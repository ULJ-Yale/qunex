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
import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl
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


# ----------------------------------------------------- the full file check


def _full_test(tmp_path, *files):
    """A `full_test` spec listing `files`, and the folder they are checked in."""
    target = tmp_path / "results"
    target.mkdir(exist_ok=True)
    spec = tmp_path / "spec.txt"
    spec.write_text("# what a finished run leaves behind\n" + "\n".join(files) + "\n")
    return {"tfolder": str(target), "tfile": str(spec), "fields": None}, target


def test_check_files_writes_its_report_into_an_open_handle(tmp_path):
    """
    `check_files` is handed the comlog the call it is checking wrote into.

    It used to accept either a handle or a path and tell them apart with
    ``types.FileType`` -- a Python 2 name that has raised ``AttributeError``
    for every truthy `report` since the tree moved to Python 3 in 2019.
    """
    full_test, target = _full_test(tmp_path, "there.nii.gz", "missing.nii.gz")
    (target / "there.nii.gz").write_text("x")

    with open(tmp_path / "comlog.log", "w") as comlog:
        status, present, missing = gc.check_files(
            full_test["tfolder"], full_test["tfile"], report=comlog
        )

    assert (status, len(present), len(missing)) == (False, 1, 1)

    written = (tmp_path / "comlog.log").read_text()
    assert "Full file check report" in written
    assert ". " + os.path.join(str(target), "there.nii.gz") in written
    assert "X " + os.path.join(str(target), "missing.nii.gz") in written


def test_check_files_needs_no_report_at_all(tmp_path):
    """A disabled comlog hands no handle down; the check still runs."""
    full_test, target = _full_test(tmp_path, "gone.nii.gz")

    with pytest.raises(ge.CommandFailed):
        gc.check_files(str(tmp_path / "nowhere"), full_test["tfile"])


def test_check_run_completes_a_passing_full_file_check(tmp_path, log):
    """
    The opt-in full file check works -- and says so.

    Before this it raised inside `check_files`, was swallowed by `check_run`'s
    ``except Exception``, and reported ``incomplete`` with a failure for every
    user who turned it on.
    """
    tfile = tmp_path / "done.nii.gz"
    tfile.write_text("x")
    full_test, target = _full_test(tmp_path, "one.nii.gz", "two.nii.gz")
    (target / "one.nii.gz").write_text("x")
    (target / "two.nii.gz").write_text("x")

    comlog = gl.ComContext(str(tmp_path / "comlogs"), "check").open()
    passed, report, failed = pc.check_run(
        str(tfile), full_test=full_test, command="HCP Test", log=log, comlog=comlog
    )
    path = comlog.close()

    assert (passed, failed) == ("done", 0)
    assert report == "HCP Test finished, full file check complete"
    assert "Full file check passed" in log.text
    with open(path) as written:
        assert "Full file check report" in written.read()


def test_check_run_reports_an_incomplete_full_file_check(tmp_path, log):
    """A missing file is `incomplete`, and the report names it."""
    tfile = tmp_path / "done.nii.gz"
    tfile.write_text("x")
    full_test, target = _full_test(tmp_path, "one.nii.gz", "two.nii.gz")
    (target / "one.nii.gz").write_text("x")

    comlog = gl.ComContext(str(tmp_path / "comlogs"), "check").open()
    passed, report, failed = pc.check_run(
        str(tfile), full_test=full_test, command="HCP Test", log=log, comlog=comlog
    )
    path = comlog.close()

    assert (passed, failed) == ("incomplete", 1)
    assert report == "HCP Test finished, full file check incomplete"
    assert "two.nii.gz" in log.text
    with open(path) as written:
        assert "X " + os.path.join(str(target), "two.nii.gz") in written.read()


# ------------------------------------------------- the ported comlog lifecycle


@pytest.fixture
def default_settings():
    """Leave the process-wide settings as they were found."""
    yield
    gl.set_active(None)


def test_run_external_maps_the_comlog_into_the_extra_folders(tmp_path, log):
    """
    The fan-out stays in `close_log`, around the ComContext.

    Each destination is noted in the report -- and a destination that cannot be
    written is a warning, not a failure: the comlog itself is already safe.
    """
    checkfile = tmp_path / "made.txt"
    blocked = tmp_path / "blocked"
    blocked.write_text("not a folder")

    endlog, status, failed = pc.run_external_for_file(
        str(checkfile),
        "touch %s" % checkfile,
        "... making a file",
        log,
        task="touch",
        logfolder=[str(tmp_path / "comlogs"), str(tmp_path / "session"), str(blocked)],
        remove=False,
    )

    assert (status, failed) == ("touch done", 0)
    assert os.path.exists(os.path.join(str(tmp_path / "session"), os.path.basename(endlog)))
    assert "---> logfile: %s" % endlog in log.text
    assert "could not map logfile to: %s" % os.path.join(str(blocked), os.path.basename(endlog)) in log.text


def test_run_external_writes_the_report_into_the_comlog(tmp_path, log):
    """The comlog holds the call, the tool's output and the report around it."""
    checkfile = tmp_path / "made.txt"

    endlog, _, _ = pc.run_external_for_file(
        str(checkfile),
        "echo hello && touch %s" % checkfile,
        "... making a file",
        log,
        task="touch",
        logfolder=str(tmp_path / "comlogs"),
        remove=False,
    )

    with open(endlog) as written:
        comlog = written.read()

    # the call echo, the child's own output, and the report `check_run` recorded
    assert "Running external command via QuNex" in comlog
    assert "hello" in comlog
    assert "---> touch test file [made.txt] present" in comlog
    assert "Successful completion of task" in comlog


def test_comlogs_off_writes_no_file_and_leaves_the_child_on_the_console(
    tmp_path, capfd, log, default_settings
):
    """
    `logging: comlog: false` is honoured here for the first time.

    The child's output is not thrown away with it: ``--logging=runlog`` means
    "write no comlog files", so `stdout` stays inherited rather than going to
    ``DEVNULL``.
    """
    gl.set_active(gl.LogSettings(comlog=False))
    checkfile = tmp_path / "made.txt"
    comlogs = tmp_path / "comlogs"

    endlog, status, failed = pc.run_external_for_file(
        str(checkfile),
        "echo the-child-spoke && touch %s" % checkfile,
        "... making a file",
        log,
        task="touch",
        logfolder=str(comlogs),
        remove=False,
    )

    assert (endlog, status, failed) == (None, "touch done", 0)
    assert not os.path.exists(comlogs)
    assert "the-child-spoke" in capfd.readouterr().out
    assert "---> logfile: " not in log.text


def test_run_script_through_shell_takes_a_folder_list_and_creates_it(tmp_path, log):
    """
    It could take neither before the port: `os.path.join` raised on a list, and
    the folder had to exist. Its one call site never passes a list, which is
    why nobody hit it.
    """
    comlogs = tmp_path / "comlogs"

    endlog = pc.run_script_through_shell(
        "echo working", "... running a script", log,
        task="script", logfolder=[str(comlogs), str(tmp_path / "session")],
        remove=False,
    )

    assert os.path.basename(endlog).startswith("done_")
    assert os.path.exists(os.path.join(str(tmp_path / "session"), os.path.basename(endlog)))
    with open(endlog) as written:
        assert "working" in written.read()
    assert log.text.endswith(" --- done")


def test_run_script_through_shell_marks_a_failure_and_keeps_the_comlog(tmp_path, log):
    comlogs = tmp_path / "comlogs"

    with pytest.raises(pc.ExternalFailed):
        pc.run_script_through_shell(
            "exit 4", "... failing on purpose", log,
            task="script", logfolder=str(comlogs), remove=True,
        )

    assert [f for f in os.listdir(comlogs) if f.startswith("error_")]


# ---------------------------------------------------- the retention rules


def test_a_removed_comlog_still_leaves_its_status_in_the_report(tmp_path, log):
    """
    The record that the step ran and how it ended is the one artifact that has
    to survive the deletion -- it is what makes removal a reasonable default
    rather than a hole.
    """
    checkfile = tmp_path / "made.txt"
    comlogs = tmp_path / "comlogs"

    endlog, status, failed = pc.run_external_for_file(
        str(checkfile),
        "touch %s" % checkfile,
        "... making a file",
        log,
        task="touch",
        logfolder=str(comlogs),
        remove=True,
    )

    assert (endlog, status, failed) == (None, "touch done", 0)
    assert os.listdir(comlogs) == []
    assert "---> completed [done], comlog removed" in log.text


def test_an_error_in_the_comlog_vetoes_its_deletion(tmp_path, log):
    """
    The case the scan exists for: a tool that exits 0, writes its check file,
    and logs errors anyway. In doubt, keep.
    """
    checkfile = tmp_path / "made.txt"
    comlogs = tmp_path / "comlogs"

    endlog, status, failed = pc.run_external_for_file(
        str(checkfile),
        "echo 'ERROR: it went wrong' && touch %s" % checkfile,
        "... making a file",
        log,
        task="touch",
        logfolder=str(comlogs),
        remove=True,
    )

    assert endlog is not None and os.path.exists(endlog)
    assert os.path.basename(endlog).startswith("done_")
    assert "comlog kept -- it reports errors" in log.text


def test_keep_comlogs_beats_a_call_site_remove(tmp_path, log, default_settings):
    """The run-level override, which `--log=remove` cannot argue with either."""
    gl.set_active(gl.LogSettings(keep_comlogs=True))
    checkfile = tmp_path / "made.txt"
    comlogs = tmp_path / "comlogs"

    endlog, _, _ = pc.run_external_for_file(
        str(checkfile),
        "touch %s" % checkfile,
        "... making a file",
        log,
        task="touch",
        logfolder=str(comlogs),
        remove=True,
    )

    assert os.path.exists(endlog)
    assert "---> logfile: %s" % endlog in log.text


def test_the_error_scan_reads_the_four_spellings_and_nothing_else(tmp_path):
    clean = tmp_path / "clean.log"
    clean.write_text("all fine\nno errors here\nmy_error_handler ran\n")
    assert pc.log_has_errors(str(clean)) is False

    for spelling in ["Error ", "Error:", "ERROR ", "ERROR:"]:
        noisy = tmp_path / "noisy.log"
        noisy.write_text("fine\n%ssomething\n" % spelling)
        assert pc.log_has_errors(str(noisy)) is True

    assert pc.log_has_errors(None) is False
    assert pc.log_has_errors(str(tmp_path / "gone.log")) is False


def test_check_run_judges_a_call_with_no_test_file_by_the_same_scan(tmp_path, log):
    """`check_run` shares the helper, so its status and the veto cannot drift."""
    comlogs = tmp_path / "comlogs"

    endlog, status, failed = pc.run_external_for_file(
        None,
        "echo 'ERROR: it went wrong'",
        "... running a check-free command",
        log,
        task="noop",
        logfolder=str(comlogs),
        remove=True,
    )

    assert (status, failed) == ("noop failed", 1)
    assert os.path.basename(endlog).startswith("error_")


# --------------------------------------------------- comlog destinations


def test_do_options_check_falls_back_to_the_settings_comlog_folders(default_settings):
    gl.set_active(gl.LogSettings(comlog_folders=("study", "session")))
    options = {
        "comlog_folders": "",
        "comlogs": "/study/logs/comlogs",
        "sessionsfolder": "/study/sessions",
    }

    pc.do_options_check(options, {"id": "s01"}, "some_command")

    assert options["comlogs"] == [
        "/study/logs/comlogs",
        os.path.join("/study/sessions", "s01", "logs", "comlogs"),
    ]


def test_a_command_line_comlog_folders_overrides_the_settings(default_settings):
    gl.set_active(gl.LogSettings(comlog_folders=("session",)))
    options = {
        "comlog_folders": "study|/elsewhere",
        "comlogs": "/study/logs/comlogs",
        "sessionsfolder": "/study/sessions",
    }

    pc.do_options_check(options, {"id": "s01"}, "some_command")

    assert options["comlogs"] == ["/study/logs/comlogs", "/elsewhere"]
