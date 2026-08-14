# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for stage naming in the per-session summary.

Some commands run two pipelines over the same unit: ``hcp_icafix`` chains into
PostFix, ``hcp_msmall`` into DeDriftAndResample. Both stages report against the
same BOLD or group name, so an unqualified summary cannot say which one failed
-- a successful ICAFix followed by a failing PostFix reads exactly like a failed
ICAFix. These pin the naming, and pin that a command running a single stage
still summarizes without a stage name, which is what the standalone
``hcp_post_fix`` and ``hcp_dedrift_and_resample`` commands produce and what a
user who turns the chaining off gets back.
"""

import pytest

from qx_utilities.hcp.hcp_utils import (
    REPORT_KEYS,
    merge_report,
    new_report,
    stage_report,
)

GROUP = "fMRI_CONCAT_ALL"


def test_new_report_has_every_bucket_empty():
    assert new_report() == {key: [] for key in REPORT_KEYS}


def test_stage_report_names_every_bucket():
    report = new_report()
    report["done"].append("BOLD_1")
    report["failed"].append("BOLD_2")
    report["not ready"].append("BOLD_3")

    stage_report(report, "ICAFix")

    assert report["done"] == ["BOLD_1 (ICAFix)"]
    assert report["failed"] == ["BOLD_2 (ICAFix)"]
    assert report["not ready"] == ["BOLD_3 (ICAFix)"]


def test_stage_report_leaves_empty_buckets_alone():
    report = new_report()
    stage_report(report, "ICAFix")
    assert report == new_report()


def test_merge_report_without_a_stage_keeps_entries_verbatim():
    report = new_report()
    other = new_report()
    other["done"].append(GROUP)

    merge_report(report, other)

    assert report["done"] == [GROUP]


def test_merge_report_appends_rather_than_replaces():
    """The bug this guards: PostFix's report replacing ICAFix's entirely."""
    report = new_report()
    report["done"].append("%s (ICAFix)" % GROUP)
    other = new_report()
    other["failed"].append(GROUP)

    merge_report(report, other, stage="PostFix")

    assert report["done"] == ["%s (ICAFix)" % GROUP]
    assert report["failed"] == ["%s (PostFix)" % GROUP]


def test_merge_report_tolerates_a_partial_report():
    report = new_report()
    merge_report(report, {"done": [GROUP]}, stage="PostFix")
    assert report["done"] == ["%s (PostFix)" % GROUP]


def _summarize(report):
    """Render a report the way the commands build their summary line."""
    return "; ".join(
        "%s %s" % (", ".join(report[k]), k) for k in REPORT_KEYS if report[k]
    )


@pytest.mark.parametrize(
    "icafix_failed,postfix_failed,expected",
    [
        (False, False, "%s (ICAFix), %s (PostFix) done" % (GROUP, GROUP)),
        (False, True, "%s (ICAFix) done; %s (PostFix) failed" % (GROUP, GROUP)),
        (True, None, "%s (ICAFix) failed" % GROUP),
    ],
)
def test_chained_summary_names_the_failing_stage(icafix_failed, postfix_failed, expected):
    """A PostFix failure must not read as an ICAFix failure."""
    report = new_report()
    report["failed" if icafix_failed else "done"].append(GROUP)

    postfix_report = None
    if not icafix_failed:
        postfix_report = new_report()
        postfix_report["failed" if postfix_failed else "done"].append(GROUP)

    stage_report(report, "ICAFix")
    if postfix_report is not None:
        merge_report(report, postfix_report, stage="PostFix")

    assert _summarize(report) == expected


def test_single_stage_summary_is_unqualified():
    """With chaining off, the summary keeps the shape users already read."""
    report = new_report()
    merge_report(report, {"done": [GROUP]})
    assert _summarize(report) == "%s done" % GROUP


def test_failed_count_is_unaffected_by_naming():
    """The status count commands return must not change with stage naming."""
    report = new_report()
    report["done"].append(GROUP)
    stage_report(report, "ICAFix")
    postfix_report = new_report()
    postfix_report["failed"].append(GROUP)
    merge_report(report, postfix_report, stage="PostFix")

    failed = len(report["failed"] + report["incomplete"] + report["not ready"])
    assert failed == 1
