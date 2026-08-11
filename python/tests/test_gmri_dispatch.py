# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for what ``gmri`` does around a command, rather than for the command.

``gmri`` is a script without a ``.py`` extension, so it is loaded by path.
What is pinned here is the run level bookkeeping: a run writes the status
record a parent process asked it for. `run_recipe` is that parent today, and
it reads the record to report what each of its steps did.
"""

import importlib.machinery
import importlib.util
import os

import pytest
import yaml

import qx_utilities.general.log as gl
import qx_utilities.general.log.context as glc
import qx_utilities.general.log.settings as gls


@pytest.fixture(autouse=True)
def no_user_settings(tmp_path, monkeypatch):
    """The user's own settings file must not decide what these tests see."""
    monkeypatch.setattr(
        gls, "USER_SETTINGS_PATHS", [str(tmp_path / "user" / "qunex_settings.yaml")]
    )


@pytest.fixture(autouse=True)
def one_run_per_test(monkeypatch):
    """
    `_status_written` is per process, which is per run everywhere but here:
    the suite runs many in one process, so each test starts having written
    nothing.
    """
    monkeypatch.setattr(glc, "_status_written", False)


@pytest.fixture(scope="module")
def gmri():
    path = os.path.join(os.path.dirname(__file__), "..", "qx_utilities", "gmri")
    loader = importlib.machinery.SourceFileLoader("gmri_under_test", path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_a_single_utility_call_writes_the_status_record_it_was_asked_for(
    gmri, tmp_path
):
    """
    The sessions loop and `process.run` both wrote one; a utility command run
    as a single call wrote none, so every utility step of a recipe was
    reported as "no status reported" however well it went.
    """
    status = tmp_path / "status.yaml"

    gmri.runCommand(
        "create_study",
        {"studyfolder": str(tmp_path / "study"), "logstatus": str(status)},
    )

    record = yaml.safe_load(status.read_text())
    assert record["command"] == "create_study"
    assert record["failed"] == 0
    assert record["sessions"][0]["summary"].startswith("completed")
    assert (tmp_path / "study" / "sessions").is_dir(), "the command still ran"


def test_a_bash_command_reports_what_its_exit_code_said(gmri, tmp_path, monkeypatch):
    """
    The matlab and bash paths had the exit code and did nothing with it but
    print it, so such a step of a recipe had no status at all. The runner is
    stubbed: what is pinned is the record, not the pipeline behind it.
    """
    monkeypatch.setattr(gmri.gb, "run", lambda qx_command, args, run=None: 3)
    status = tmp_path / "status.yaml"

    gmri.runCommand(
        "dwi_dtifit",
        {"studyfolder": str(tmp_path / "study"), "logstatus": str(status)},
    )

    record = yaml.safe_load(status.read_text())
    assert record["failed"] == 1
    assert record["sessions"][0]["summary"] == "failed with exit code 3"


def test_a_run_that_dies_still_reports_that_it_failed(gmri, tmp_path):
    """
    The record is written at the exit boundary for the runs that never build
    one. Without it the step that failed hardest was the one `run_recipe`
    could say least about.
    """
    status = tmp_path / "status.yaml"

    with pytest.raises(OSError):
        gmri.main(
            [
                "create_study",
                "--studyfolder=/dev/null/study",
                "--logstatus=%s" % status,
            ]
        )

    record = yaml.safe_load(status.read_text())
    assert record["failed"] == 1
    assert record["runlog"] is None, "there was no runlog to name"
    assert "Not a directory" in record["sessions"][0]["summary"]


def test_a_command_that_is_not_one_reports_that_it_failed(gmri, tmp_path):
    """A typo in a recipe exits rather than raises, and still has to report."""
    status = tmp_path / "status.yaml"

    with pytest.raises(SystemExit):
        gmri.main(["no_such_command", "--logstatus=%s" % status, "--x=1"])

    assert yaml.safe_load(status.read_text())["failed"] == 1


def test_the_record_a_run_wrote_itself_is_not_overwritten_at_the_boundary(tmp_path):
    """
    `process.run` writes its per-session digest and *then* raises for the
    sessions that failed. The digest is the better record of the two.
    """
    status = tmp_path / "status.yaml"
    args = {"logstatus": str(status)}

    settings = gl.LogSettings()
    run = gl.RunContext("hcp_pre_freesurfer", args, settings, {"logfolder": str(tmp_path)})
    run.write_status([("S01", "PreFS failed", 1)])

    assert gl.write_failure_status(args, "hcp_pre_freesurfer", "died") is None
    assert yaml.safe_load(status.read_text())["sessions"][0]["id"] == "S01"
