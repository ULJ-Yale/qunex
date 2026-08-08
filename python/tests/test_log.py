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

import qx_utilities.general.exceptions as ge
from qx_utilities.general.log import report as log_module
from qx_utilities.general.log import REPORT_RULE, ReportLog, SessionLog

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
    monkeypatch.setattr(log_module, "datetime", _FrozenDatetime)


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


def test_framed_frames_content_between_rules():
    log = _log()
    with log.framed("A title:"):
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


def test_raw_appends_verbatim():
    # the processing.core helpers write into the log rather than handing back a
    # replacement report, so everything recorded before them survives
    log = _log()
    log.step("before")
    log.raw("APPENDED")
    assert log.text.endswith("\n---> before" + "APPENDED")


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


def test_result_rejects_a_string_report_without_a_failed_count():
    # finish() derives the count (see the N4 tests below); result() is the raw
    # contract check and still demands it
    with pytest.raises(ValueError, match="failed count"):
        _log().result("HCP Thing failed")


# ------------------------------------------------------------- depth (N3)


def test_indent_nests_subsequent_lines():
    log = _log()
    log.step("outer")
    log.indent()
    log.step("inner")
    log.dedent()
    log.step("outer again")

    assert log.text.endswith(
        "\n---> outer"
        "\n     ---> inner"
        "\n---> outer again"
    )


def test_dedent_is_clamped_at_zero():
    log = _log()
    log.dedent()
    log.dedent()
    log.step("still flush left")

    assert log.text.endswith("\n---> still flush left")


def test_section_records_a_step_and_indents_its_block():
    log = _log()
    with log.section("checking %s", "data"):
        log.step("found it")
        log.detail("a detail")

    log.step("after")

    assert log.text.endswith(
        "\n---> checking data"
        "\n     ---> found it"
        "\n          ... a detail"
        "\n---> after"
    )


def test_section_restores_the_depth_when_the_block_raises():
    log = _log()
    with pytest.raises(RuntimeError):
        with log.section("doomed"):
            raise RuntimeError("boom")
    log.step("after")

    assert log.text.endswith("\n---> doomed\n---> after")


def test_per_line_depth_shifts_only_that_line():
    log = _log()
    log.step("shifted", depth=1)
    log.step("not shifted")

    assert log.text.endswith("\n     ---> shifted\n---> not shifted")


def test_detail_stays_at_its_historical_indent():
    # detail is depth 1 now, but its rendered prefix must not change
    log = _log()
    log.detail("unchanged")
    assert log.text.endswith("\n     ... unchanged")


def test_raw_ignores_depth():
    # raw text is verbatim: no prefix, no indent, no added newline
    log = ReportLog()
    log.indent(3)
    log.raw("verbatim")
    assert log.text == "verbatim"


# --------------------------------------------------- status from severity (N4)


def test_finish_derives_failed_from_recorded_errors():
    log = _log()
    log.error("could not find the data")
    _, status = log.finish("HCP Thing failed")

    assert status == ("sess-01", "HCP Thing failed", 1)


def test_finish_derives_zero_when_nothing_failed():
    _, status = _log().finish("all good")
    assert status == ("sess-01", "all good", 0)


def test_explicit_failed_count_still_wins():
    log = _log()
    log.error("one error")
    _, status = log.finish("three bolds failed", failed=3)

    assert status == ("sess-01", "three bolds failed", 3)


def test_reporting_no_failure_while_errors_exist_is_flagged():
    log = _log()
    log.error("could not find the data")
    text, status = log.finish("all good", failed=0)

    assert status == ("sess-01", "all good", 0)
    assert "---> WARNING: 1 error(s) were recorded but the command " \
           "reports no failures" in text


def test_the_flag_is_not_raised_when_the_count_agrees():
    log = _log()
    log.error("could not find the data")
    text, _ = log.finish("failed", failed=1)

    assert "reports no failures" not in text


def test_a_status_tuple_reporting_no_failure_is_flagged_too():
    log = _log()
    log.error("could not find the data")
    text, status = log.finish(("sess-01", "all good", 0))

    assert status == ("sess-01", "all good", 0)
    assert "reports no failures" in text


def test_unknown_error_counts_as_a_failure():
    log = _log()
    try:
        raise ValueError("boom")
    except ValueError:
        log.unknown_error()

    assert log.has_errors
    _, status = log.finish("HCP Thing failed")
    assert status[2] == 1


def test_command_failed_counts_as_a_failure():
    log = _log()
    log.command_failed(ge.CommandFailed("hcp_thing", "no data"))

    assert log.has_errors
    _, status = log.finish("HCP Thing failed")
    assert status[2] == 1


def test_add_carries_the_error_state_of_a_sub_log():
    bold = ReportLog()
    bold.error("bold 1 failed")

    log = _log()
    log.add(bold)
    _, status = log.finish("bold 1 failed")

    assert status[2] == 1


# ---------------------------------------------------- the second stream


class _Comlog:
    """A ComContext stand-in: all `trace` and the echo need is `write`."""

    def __init__(self):
        self.written = ""

    def write(self, text):
        self.written += text


def test_trace_is_dropped_without_an_attachment():
    log = ReportLog()
    log.trace("raw output nobody is listening for")

    assert log.text == ""


def test_trace_reaches_the_attached_comlog_and_not_the_report():
    log = ReportLog()
    comlog = _Comlog()

    with log.stream_to(comlog):
        log.trace("the tool's own output\n")

    assert comlog.written == "the tool's own output\n"
    assert log.text == ""


def test_the_report_is_echoed_into_the_attached_comlog():
    log = ReportLog()
    comlog = _Comlog()

    log.step("before the call")
    with log.stream_to(comlog):
        log.step("running the tool")
        log.detail("with a detail")
    log.step("after the call")

    # what was recorded inside the block, spelled exactly as the runlog has it
    assert comlog.written == "\n---> running the tool\n     ... with a detail"
    # and the report itself is untouched by the attachment
    assert "before the call" in log.text and "after the call" in log.text


def test_the_attachment_is_restored_even_when_the_block_raises():
    log = ReportLog()
    outer, inner = _Comlog(), _Comlog()

    with log.stream_to(outer):
        with pytest.raises(ValueError):
            with log.stream_to(inner):
                log.step("nested")
                raise ValueError("the call failed")
        log.step("back outside")

    assert inner.written == "\n---> nested"
    assert outer.written == "\n---> back outside"
    assert log._comlog is None
