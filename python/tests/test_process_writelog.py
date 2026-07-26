# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for the runlog bookkeeping in ``general.process``.

``writelog`` splits a command's return value into the report text and the
three-field status, and the final report of a run is built from the collected
stati. Feeding it an already split report added a second, bogus "Unknown"
status per session, so these pin that one item in equals one status out.
"""

import pytest

import qx_utilities.general.log as gl
import qx_utilities.general.process as gp


@pytest.fixture
def run(tmp_path):
    """The run that owns the runlog writelog appends to."""
    return gl.RunContext(
        "test_command",
        {},
        gl.LogSettings(),
        {"basefolder": str(tmp_path)},
        timestamp="2026-07-26_12.00.00.000000",
    )


@pytest.fixture
def stati():
    return []


def test_writelog_returns_the_split_it_recorded(run, stati):
    r, status = gp.writelog(("report text", ("sess-01", "all good", 0)), run, stati)

    assert r == "report text"
    assert status == ("sess-01", "all good", 0)


def test_one_result_yields_exactly_one_status(run, stati):
    gp.writelog(("report text", ("sess-01", "all good", 0)), run, stati)

    assert stati == [("sess-01", "all good", 0)]


def test_report_is_appended_to_the_runlog_file(run, stati):
    gp.writelog(("report text", ("sess-01", "all good", 0)), run, stati)
    gp.writelog(("more text", ("sess-02", "all good", 0)), run, stati)

    with open(run.path) as f:
        assert f.read() == "report text\nmore text\n"


def test_a_plain_string_is_still_accepted_as_unknown_status(run, stati):
    # unmigrated commands may return a bare report; it must not crash, but it
    # is what the "Unknown" status is for -- and why writelog must not be
    # handed a report it has already split
    r, status = gp.writelog("bare report", run, stati)

    assert r == "bare report"
    assert status == ("Unknown", "Unknown", None)


def test_a_disabled_run_records_stati_but_writes_nothing(tmp_path, stati):
    run = gl.RunContext(
        "test_command",
        {},
        gl.LogSettings(enabled=False),
        {"basefolder": str(tmp_path)},
    )

    gp.writelog(("report text", ("sess-01", "all good", 0)), run, stati)

    assert stati == [("sess-01", "all good", 0)]
    assert run.path is None
    assert not list(tmp_path.rglob("Log-*.log"))
