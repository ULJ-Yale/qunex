# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for the ICAFix -> PostFix chain on the ``run="run"`` path.

The dry-run tests only reach ``log.check_run``, so the ``run="run"`` branch of
``execute_hcp_post_fix`` -- the one ``hcp_icafix`` chains into after a
successful ICAFix -- goes unexercised by them. That branch raised a
``TypeError`` for calling ``log.run_external`` with the pre-refactor argument
name, and because the executor catches every exception the failure surfaced as
"``<group>`` failed" on a run whose comlog said ``done``. These drive the branch
with the external call stubbed out, so the chain is checked without needing the
HCP pipelines, and assert that the summary says which of the two stages failed.
"""

import os

import pytest

import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_icafix import execute_hcp_multi_icafix
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.hcp.hcp_utils import execute_hcp_post_fix

from .utils import build_hcp_session, default_options

GROUP = "fMRI_CONCAT_ALL"


@pytest.fixture
def postfix_session(tmp_path):
    """A session whose group ICA output is present, ready for PostFix."""
    sinfo, sessionsfolder = build_hcp_session(tmp_path, bolds=True)
    options = default_options(
        sessionsfolder=sessionsfolder,
        sourcefolder=sessionsfolder,
        run="run",
        hcp_matlab_mode="compiled",
        comlogs=str(tmp_path / "comlogs"),
        logtag="",
    )
    hcp = get_hcp_paths(sinfo, options)

    results = os.path.join(hcp["hcp_nonlin"], "Results", GROUP)
    os.makedirs(results, exist_ok=True)
    open(os.path.join(results, "%s_hp0_clean.nii.gz" % GROUP), "w").close()
    return sinfo, options, hcp


@pytest.fixture
def stub_external(monkeypatch):
    """Replace the external runner, recording how the wrapper called it."""
    calls = []

    def fake(checkfile, run, description, log=None, **kwargs):
        calls.append({"checkfile": checkfile, "run": run,
                      "description": description, **kwargs})
        if log is not None:
            log.raw("\n---> %s ran" % description)
        return "done.log", "done", 0

    monkeypatch.setattr(pc, "run_external_for_file", fake)
    return calls


def test_post_fix_runs_and_reports_done(postfix_session, stub_external):
    sinfo, options, hcp = postfix_session

    result = execute_hcp_post_fix(sinfo, options, hcp, True, False, GROUP)

    assert result["report"]["done"] == [GROUP]
    assert result["report"]["failed"] == []
    assert "Traceback" not in result["r"]


def test_post_fix_forwards_the_pipeline_command(postfix_session, stub_external):
    """The assembled PostFix command must reach the runner as its command."""
    sinfo, options, hcp = postfix_session

    execute_hcp_post_fix(sinfo, options, hcp, True, False, GROUP)

    assert len(stub_external) == 1
    call = stub_external[0]
    assert "PostFix.sh" in call["run"]
    assert '--fmri-name="%s"' % GROUP in call["run"]
    assert call["checkfile"] is None
    assert call["task"] == "hcp_post_fix"


def test_post_fix_reports_failure_when_the_run_fails(postfix_session, monkeypatch):
    def fake(checkfile, run, description, r="", **kwargs):
        return r, "error.log", None, 1

    monkeypatch.setattr(pc, "run_external_for_file", fake)
    sinfo, options, hcp = postfix_session

    result = execute_hcp_post_fix(sinfo, options, hcp, True, False, GROUP)

    assert result["report"]["failed"] == [GROUP]
    assert result["report"]["done"] == []


def _icafix_group(hcp, bolds=("BOLD_1", "BOLD_2")):
    """Lay out the concatenated-group inputs the multi-run executor checks for."""
    for name in bolds:
        results = os.path.join(hcp["hcp_nonlin"], "Results", name)
        os.makedirs(results, exist_ok=True)
        open(os.path.join(results, "%s.nii.gz" % name), "w").close()
    return {
        "name": GROUP,
        "bolds": [{"filename": name, "bold_number": i + 1}
                  for i, name in enumerate(bolds)],
    }


def test_chain_names_the_stage_that_failed(postfix_session, monkeypatch):
    """ICAFix succeeding and PostFix failing must not read as an ICAFix failure."""
    sinfo, options, hcp = postfix_session
    options["hcp_icafix_postfix"] = True
    group = _icafix_group(hcp)

    def fake(checkfile, run, description, log=None, **kwargs):
        failed = 1 if "PostFix" in run else 0
        return "log", None if failed else "done", failed

    monkeypatch.setattr(pc, "run_external_for_file", fake)

    report = execute_hcp_multi_icafix(sinfo, options, False, hcp, True, group)["report"]

    assert report["done"] == ["%s (ICAFix)" % GROUP]
    assert report["failed"] == ["%s (PostFix)" % GROUP]


def test_chain_names_both_stages_when_both_pass(postfix_session, stub_external):
    sinfo, options, hcp = postfix_session
    options["hcp_icafix_postfix"] = True
    group = _icafix_group(hcp)

    report = execute_hcp_multi_icafix(sinfo, options, False, hcp, True, group)["report"]

    assert report["done"] == ["%s (ICAFix)" % GROUP, "%s (PostFix)" % GROUP]
    assert report["failed"] == []


def test_chain_names_icafix_when_icafix_itself_fails(postfix_session, monkeypatch):
    sinfo, options, hcp = postfix_session
    options["hcp_icafix_postfix"] = True
    group = _icafix_group(hcp)

    calls = []

    def fake(checkfile, run, description, r="", **kwargs):
        calls.append(run)
        return r, "log", None, 1

    monkeypatch.setattr(pc, "run_external_for_file", fake)

    report = execute_hcp_multi_icafix(sinfo, options, False, hcp, True, group)["report"]

    assert report["failed"] == ["%s (ICAFix)" % GROUP]
    # a failed ICAFix must not go on to run PostFix
    assert not any("PostFix" in c for c in calls)


def test_summary_is_unqualified_when_postfix_is_disabled(postfix_session, stub_external):
    """Turning the chaining off keeps the summary users already read."""
    sinfo, options, hcp = postfix_session
    options["hcp_icafix_postfix"] = False
    group = _icafix_group(hcp)

    report = execute_hcp_multi_icafix(sinfo, options, False, hcp, True, group)["report"]

    assert report["done"] == [GROUP]
    assert len(stub_external) == 1


def test_post_fix_is_not_ready_without_the_ica_image(tmp_path, stub_external):
    sinfo, sessionsfolder = build_hcp_session(tmp_path, bolds=True)
    options = default_options(
        sessionsfolder=sessionsfolder,
        sourcefolder=sessionsfolder,
        run="run",
        hcp_matlab_mode="compiled",
        comlogs=str(tmp_path / "comlogs"),
        logtag="",
    )
    hcp = get_hcp_paths(sinfo, options)

    result = execute_hcp_post_fix(sinfo, options, hcp, True, False, GROUP)

    assert result["report"]["not ready"] == [GROUP]
    assert stub_external == []
