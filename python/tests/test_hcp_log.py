# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for SessionLog, the per-session runlog built by the HCP commands.

These pin the rendered text, because that text is what QuNex writes to
``Log-<command>-<timestamp>.log`` and prints to the console -- it is a
user-facing surface, not an implementation detail.
"""

import pytest

from qx_utilities.hcp import hcp_log
from qx_utilities.hcp.hcp_log import REPORT_RULE, SessionLog

STAMP = "Monday, 01. January 2024 00:00:00"
SINFO = {"id": "sess-01"}
OPTIONS = {"run": "run", "hcp_processing_mode": "HCPStyleData"}


class _FrozenDatetime:
    @staticmethod
    def now():
        return _FrozenDatetime()

    def strftime(self, fmt):
        assert fmt == "%A, %d. %B %Y %H:%M:%S"
        return STAMP


@pytest.fixture(autouse=True)
def frozen_clock(monkeypatch):
    monkeypatch.setattr(hcp_log, "datetime", _FrozenDatetime)


def _log(**kwargs):
    return SessionLog(SINFO, OPTIONS, "HCP Test Pipeline", **kwargs)


def test_header_names_session_and_pipeline():
    assert _log().text == (
        "\n" + REPORT_RULE + "\nSession id: sess-01 \n[started on " + STAMP + "]"
        "\nRunning HCP Test Pipeline [HCPStyleData] ..."
    )


def test_header_without_processing_mode():
    # commands like hcp_dtifit do not report a processing mode
    assert _log(mode=False).text.endswith("\nRunning HCP Test Pipeline ...")


def test_header_label_for_subject_commands():
    log = SessionLog({"id": "subj-1"}, OPTIONS, "HCP prep long", label="Subject")
    assert "\nSubject: subj-1 \n[started on " in log.text


def test_levels_render_with_their_prefixes():
    log = _log()
    log.step("doing a thing")
    log.detail("with a detail")
    log.warning("something looks off")
    log.error("could not find %s", "a file")
    log.info("plain line")

    assert log.text.endswith(
        "\n---> doing a thing"
        "\n     ... with a detail"
        "\n---> WARNING: something looks off"
        "\n---> ERROR: could not find a file"
        "\nplain line"
    )


def test_error_without_args_does_not_interpolate():
    log = _log()
    log.error("100% of runs failed")
    assert log.text.endswith("\n---> ERROR: 100% of runs failed")


def test_section_frames_content_between_rules():
    log = _log()
    with log.section("A title:"):
        log.raw("body")

    assert log.text.endswith(
        "\n\n" + REPORT_RULE + "\nA title:\n\nbody\n" + REPORT_RULE + "\n"
    )


def test_pipeline_command_breaks_flags_onto_lines():
    log = _log()
    log.pipeline_command('cmd --alpha="1" --beta="2"')
    assert '\n    --alpha="1"' in log.text
    assert '\n    --beta="2"' in log.text
    assert "Running HCP Pipelines command via QuNex:" in log.text


def test_capture_replaces_rather_than_appends():
    # processing.core helpers hand back the whole report, not just their part
    log = _log()
    log.step("before")
    log.capture("REPLACED")
    assert log.text == "REPLACED"


def test_finish_builds_the_process_py_contract():
    log = _log()
    text, status = log.finish("all good", failed=0)

    assert status == ("sess-01", "all good", 0)
    assert text.endswith(
        "\n\nHCP Test Pipeline completed on " + STAMP + "\n" + REPORT_RULE
    )


def test_finish_accepts_a_ready_made_status_tuple():
    _, status = _log().finish(("sess-01", "bolds 1, 2 done", 3))
    assert status == ("sess-01", "bolds 1, 2 done", 3)


def test_finish_can_rename_the_closing_line():
    text, _ = _log().finish("done", 0, pipeline="HCP Test")
    assert "\n\nHCP Test completed on " in text


def test_test_mode_marks_both_ends():
    log = SessionLog(SINFO, dict(OPTIONS, run="test"), "HCP Test Pipeline")
    text, _ = log.finish("would run", 0)

    assert "Test running HCP Test Pipeline [" in text
    assert "HCP Test Pipeline test completed on " in text


def test_unknown_error_captures_the_traceback():
    log = _log()
    try:
        raise ValueError("boom")
    except ValueError:
        log.unknown_error()

    assert "ValueError: boom" in log.text
    assert "ERROR: Unknown error occured:" in log.text


def test_finish_rejects_a_two_field_status_tuple():
    # the two-field status is exactly the bug this refactor removes: it made a
    # whole run print "success status not reported for some or all tasks"
    with pytest.raises(ValueError, match="3-field"):
        _log().finish(("sess-01", "HCP Thing failed"))


def test_finish_rejects_a_string_report_without_a_failed_count():
    with pytest.raises(ValueError, match="failed count"):
        _log().finish("HCP Thing failed")
