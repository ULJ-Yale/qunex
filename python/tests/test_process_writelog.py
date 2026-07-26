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

import qx_utilities.general.process as gp


@pytest.fixture(autouse=True)
def clean_globals(tmp_path):
    """process.py keeps the runlog in module globals; reset them per test."""
    gp.log = []
    gp.stati = []
    gp.logname = str(tmp_path / "Log-test.log")
    yield


def test_writelog_returns_the_split_it_recorded():
    r, status = gp.writelog(("report text", ("sess-01", "all good", 0)))

    assert r == "report text"
    assert status == ("sess-01", "all good", 0)


def test_one_result_yields_exactly_one_status():
    gp.writelog(("report text", ("sess-01", "all good", 0)))

    assert gp.stati == [("sess-01", "all good", 0)]
    assert gp.log == ["report text"]


def test_report_is_appended_to_the_runlog_file():
    gp.writelog(("report text", ("sess-01", "all good", 0)))
    gp.writelog(("more text", ("sess-02", "all good", 0)))

    with open(gp.logname) as f:
        assert f.read() == "report text\nmore text\n"


def test_a_plain_string_is_still_accepted_as_unknown_status():
    # unmigrated commands may return a bare report; it must not crash, but it
    # is what the "Unknown" status is for -- and why writelog must not be
    # handed a report it has already split
    r, status = gp.writelog("bare report")

    assert r == "bare report"
    assert status == ("Unknown", "Unknown", None)
