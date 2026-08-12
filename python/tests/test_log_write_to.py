# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for ``ReportLog.write_to``, the runlog half of the return contract.

A processing command returns its log; ``general.process`` writes it with
``write_to`` and collects ``status``. These pin what ``writelog`` and the
``print(r)`` beside it used to do -- one report appended to the runlog per
session, printed as the session completes so a long run can be followed by
tailing the file -- plus the one thing that is new: a log with no id of its own
is filed under the run's command name, where ``proc_response`` said "Unknown".
"""

import pytest

import qx_utilities.general.log as gl
from qx_utilities.general.log import ReportLog


@pytest.fixture
def run(tmp_path):
    """The run that owns the runlog a report is appended to."""
    return gl.RunContext(
        "test_command",
        {},
        gl.LogSettings(),
        {"basefolder": str(tmp_path)},
        timestamp="2026-07-26_12.00.00.000000",
    )


def _log(text, sid="sess-01", summary="all good", failed=0):
    log = ReportLog()
    log.raw(text)
    return log.result(summary, failed, sid)


def test_the_report_is_appended_to_the_runlog(run):
    _log("report text").write_to(run)
    _log("more text", sid="sess-02").write_to(run)

    with open(run.path) as f:
        assert f.read() == "report text\nmore text\n"


def test_the_report_is_printed_as_well(run, capsys):
    _log("report text").write_to(run)

    assert capsys.readouterr().out == "report text\n"


def test_one_log_yields_exactly_one_status(run):
    log = _log("report text")
    log.write_to(run)

    assert log.status == ("sess-01", "all good", 0)


def test_a_log_with_no_id_is_filed_under_the_command(run):
    # a study level command builds a plain ReportLog and never names itself;
    # the run knows the command name, so it supplies it
    log = ReportLog()
    log.finish("study command ran")
    log.write_to(run)

    assert log.status == ("test_command", "study command ran", 0)


def test_an_id_the_command_gave_is_not_overwritten(run):
    log = _log("report text", sid="sess-01")
    log.write_to(run)

    assert log.status[0] == "sess-01"


def test_a_disabled_run_still_reports_but_writes_nothing(tmp_path, capsys):
    run = gl.RunContext(
        "test_command",
        {},
        gl.LogSettings(enabled=False),
        {"basefolder": str(tmp_path)},
    )

    log = _log("report text")
    log.write_to(run)

    assert log.status == ("sess-01", "all good", 0)
    assert capsys.readouterr().out == "report text\n"
    assert run.path is None
    assert not list(tmp_path.rglob("Log-*.log"))
