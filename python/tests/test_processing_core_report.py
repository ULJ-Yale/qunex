# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
The ``processing.core`` / ``general.core`` helpers write into the report log.

They used to take the report so far as ``r=`` and hand the whole thing back,
which meant the log had to adopt the returned string wholesale (``capture()``)
and so lost every record it had. They now take the log and append to it, and
return only what the caller actually branches on -- a status, a count, a path.

The one shape worth pinning beyond that is the failure path: when an external
command fails, everything that led up to the failure is already in the log, and
``ExternalFailed`` carries the error message *alone*. A caller's handler appends
it, so the report reads in order and nothing is duplicated.
"""

import os

import pytest

import qx_utilities.general.core as gc
import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog


@pytest.fixture
def log():
    return ReportLog()


# ------------------------------------------------------------- file checks


def test_check_for_file_notes_and_returns_the_status(tmp_path, log):
    present = tmp_path / "there.nii.gz"
    present.write_text("x")

    assert pc.check_for_file(log, str(present), "\n ... present", "\n ... missing")
    assert log.text == "\n ... present"

    assert pc.check_for_file(log, str(tmp_path / "gone"), "\n ... ok", "\n ... bad") is False
    assert log.text.endswith("\n ... bad")


def test_check_for_files_returns_the_first_match(tmp_path, log):
    second = tmp_path / "b.nii.gz"
    second.write_text("x")

    status, found = pc.check_for_files(
        log, [str(tmp_path / "a.nii.gz"), str(second)], "\n ... ok", "\n ... bad"
    )

    assert (status, found) == (True, str(second))
    assert log.text == "\n ... ok"


def test_link_or_copy_notes_the_mapping_and_returns_a_bool(tmp_path, log):
    source = tmp_path / "source.nii.gz"
    source.write_text("x")

    assert gc.link_or_copy(source, tmp_path / "target.nii.gz", log, name="T1") is True
    assert log.text == "\n ... T1 mapped"

    assert gc.link_or_copy(tmp_path / "nope", tmp_path / "t2", log, name="T2") is False
    assert "ERROR: T2 could not be copied" in log.text


def test_link_or_copy_without_a_log_still_reports_by_return_value(tmp_path):
    source = tmp_path / "source.nii.gz"
    source.write_text("x")

    assert gc.link_or_copy(source, tmp_path / "target.nii.gz") is True


# ------------------------------------------------------------------ bolds


def test_use_or_skip_bold_notes_what_it_skips(log):
    sinfo = {
        "id": "sess-01",
        "1": {"name": "bold1", "task": "rest"},
        "2": {"name": "bold2", "task": "task"},
    }

    bolds, skipped, nskipped = pc.use_or_skip_bold(sinfo, {"bolds": "1"}, log)

    assert [b["bold_number"] for b in bolds] == [1]
    assert (len(skipped), nskipped) == (1, 1)
    assert "Skipping the following BOLD images:" in log.text
    assert "bold2" in log.text


def test_use_or_skip_bold_works_without_a_log():
    sinfo = {"id": "sess-01", "1": {"name": "bold1", "task": "rest"}}

    bolds, _, nskipped = pc.use_or_skip_bold(sinfo, {"bolds": "all"})

    assert (len(bolds), nskipped) == (1, 0)


# -------------------------------------------------------------- check_run


def test_check_run_notes_a_present_test_file(tmp_path, log):
    tfile = tmp_path / "done.nii.gz"
    tfile.write_text("x")

    passed, report, failed = pc.check_run(str(tfile), command="HCP Test", log=log)

    assert (passed, failed) == ("done", 0)
    assert report == "HCP Test finished"
    assert "test file [done.nii.gz] present" in log.text


def test_check_run_notes_a_missing_test_file(tmp_path, log):
    passed, report, failed = pc.check_run(
        str(tmp_path / "gone.nii.gz"), command="HCP Test", log=log
    )

    assert (passed, failed) == (None, 1)
    assert report == "HCP Test not finished"
    assert "test file missing" in log.text


# --------------------------------------------------------- external calls


def test_run_external_writes_the_report_into_the_log(tmp_path, log):
    checkfile = tmp_path / "made.txt"
    comlogs = tmp_path / "comlogs"

    endlog, status, failed = pc.run_external_for_file(
        str(checkfile),
        "touch %s" % checkfile,
        "... making a file",
        log,
        task="touch",
        logfolder=str(comlogs),
        remove=False,
    )

    assert (status, failed) == ("touch done", 0)
    assert os.path.basename(endlog).startswith("done_")
    assert "... making a file" in log.text
    assert "---> logfile: %s" % endlog in log.text


def test_run_external_raises_the_error_alone(tmp_path, log):
    log.step("earlier work")
    comlogs = tmp_path / "comlogs"

    with pytest.raises(pc.ExternalFailed) as failure:
        pc.run_external_for_file(
            str(tmp_path / "never.txt"),
            "exit 3",
            "... failing on purpose",
            log,
            task="boom",
            logfolder=str(comlogs),
            remove=False,
        )

    message = str(failure.value)
    # the exception carries the error, not a copy of the report -- so a handler
    # that appends it cannot duplicate what is already recorded
    assert "failed with error" in message
    assert "earlier work" not in message

    # ... and what led up to it is in the log, with the comlog marked error_
    assert "---> earlier work" in log.text
    assert "... failing on purpose" in log.text
    assert "---> logfile: " in log.text
    assert [f for f in os.listdir(comlogs) if f.startswith("error_")]


def test_run_external_skips_a_completed_check_file(tmp_path, log):
    checkfile = tmp_path / "already.txt"
    checkfile.write_text("x" * 200)

    endlog, status, failed = pc.run_external_for_file(
        str(checkfile), "exit 1", "... would run", log, task="skip",
        logfolder=str(tmp_path / "comlogs"),
    )

    assert (endlog, status, failed) == (None, "skip done", 0)
    assert log.text.endswith("\n... would run --- already completed")
