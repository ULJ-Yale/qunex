#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``processing/fs.py``'s four commands honour ``--test``.

Every other processing command guards its work with
``if options["run"] == "run"``. This file had no such guard anywhere, so
``--test`` ran the commands for real: it copied structurals, invoked
``recon-all``, ``bet`` and ``fast``, and deleted an existing FreeSurfer folder
before replacing it. A dry run is supposed to resolve inputs and report what it
*would* do.

The tests assert the two halves of that: nothing is executed and nothing on
disk changes, and the report still names every external command in full, so a
dry run is worth reading.
"""

import os
import subprocess

import pytest

import qx_utilities.processing.fs as fs
from qx_utilities.general.log import ReportLog
from tests.utils import default_options

COMMANDS = [
    "run_basic_structural_segmentation",
    "check_for_freesurfer_data",
    "run_freesurfer_full_segmentation",
    "run_freesurfer_subcortical_segmentation",
]


def _tree(root):
    """Every file under `root`, with its size and mtime."""
    found = {}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            stat = os.stat(path)
            found[path] = (stat.st_size, stat.st_mtime_ns)
    return found


@pytest.fixture
def session(tmp_path, monkeypatch):
    """A session with a 4dfp structural, and every external call made fatal."""
    sessions = tmp_path / "sessions"
    atlas = sessions / "s01" / "4dfp" / "atlas"
    atlas.mkdir(parents=True)
    (atlas / "s01_mpr_n1_111_t88.4dfp.img").write_bytes(b"x" * 300)
    (atlas / "s01_mpr_n1_111_t88.4dfp.ifh").write_bytes(b"x" * 300)

    # an existing FreeSurfer folder, so the one destructive path in the file --
    # `shutil.rmtree` before `copytree` -- is reachable in the walk
    existing = tmp_path / "freesurfer_elsewhere"
    (existing / "mri").mkdir(parents=True)
    (existing / "mri" / "aseg.mgz").write_bytes(b"x" * 300)

    def no_external(*args, **kwargs):
        raise AssertionError("a --test run executed an external command")

    monkeypatch.setattr(subprocess, "run", no_external)
    # the catch-all handler naps 15s before returning; a test that trips it
    # should fail fast rather than sleep
    monkeypatch.setattr(fs.time, "sleep", lambda *_: None)

    options = default_options(
        sessionsfolder=str(sessions),
        run="test",
        comlogs=str(tmp_path / "comlogs"),
        path_freesurfer=str(existing),
    )
    return {"id": "s01", "data": str(sessions / "s01" / "4dfp")}, options, tmp_path


@pytest.mark.parametrize("command", COMMANDS)
def test_a_test_run_changes_nothing_on_disk(session, command):
    sinfo, options, root = session
    before = _tree(root)

    report = getattr(fs, command)(sinfo, dict(options)).text

    assert _tree(root) == before, "a --test run wrote, removed or replaced a file"
    assert "Unknown error occured" not in report, report


@pytest.mark.parametrize("command", COMMANDS)
def test_a_test_run_says_it_is_a_test(session, command):
    sinfo, options, root = session

    report = getattr(fs, command)(sinfo, dict(options)).text

    assert "test" in report.lower()
    assert "Unknown error occured" not in report, report


def test_the_dry_run_reports_the_commands_it_would_have_run(session):
    """The point of a dry run: the fully expanded call, not just a step name."""
    sinfo, options, root = session

    report = fs.run_basic_structural_segmentation(sinfo, dict(options)).text

    for tool in ("g_FlipFormat", "bet ", "fast ", "gunzip -f"):
        assert "test, not run: %s" % tool in report or (
            "test, not run: " in report and tool in report
        ), "the dry run does not name %r" % tool
    assert "test, not copied: s01_mpr_n1_111_t88.4dfp.img" in report


def test_the_freesurfer_folder_is_not_replaced_in_a_test_run(session):
    """`check_for_freesurfer_data` rmtree's the target before copying into it."""
    sinfo, options, root = session
    target = os.path.join(
        str(root), "sessions", "s01", "images", "segmentation", "freesurfer"
    )
    os.makedirs(target)
    keep = os.path.join(target, "do_not_delete.txt")
    with open(keep, "w") as f:
        f.write("existing FreeSurfer output")

    fs.check_for_freesurfer_data(sinfo, dict(options), overwrite=True)

    assert os.path.exists(keep), "a --test run deleted an existing FreeSurfer folder"


def test_a_real_run_leaves_the_comlog_to_the_block():
    """
    `_run_external` says what to run, and nothing about where it is logged.

    All 41 call sites used to spell `thread`, `logfolder` and `logtags`
    themselves, and each of them opened a comlog. The comlog is now the
    command's, opened once by `combined_comlog`, so the helper forwards only
    what the call is -- passing the three again would describe a file this call
    never opens.
    """
    calls = []

    def fake(*args, **kwargs):
        calls.append((args, kwargs))

    log = ReportLog()
    options = {
        "run": "run",
        "comlogs": ["/study/logs/comlogs"],
        "logtag": "tag",
    }
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(fs.pc, "run_external_for_file", fake)
        fs._run_external(log, options, True, "/check.nii.gz", "bet a b", "... bet")

    (args, kwargs) = calls[0]
    assert args == ("/check.nii.gz", "bet a b", "... bet")
    assert kwargs == {"overwrite": True, "_log": log}


# --------------------------------------- the return contract inside the file


@pytest.mark.parametrize("command", COMMANDS)
def test_every_command_returns_a_log_with_a_status(session, command):
    """OI-1: these four returned bare report text and no status at all."""
    sinfo, options, _ = session

    log = getattr(fs, command)(sinfo, dict(options))

    sid, summary, failed = log.status
    assert sid == "s01"
    assert isinstance(summary, str) and summary
    assert failed == 0


def test_the_nested_check_lands_in_the_callers_report(session):
    """
    `check_for_freesurfer_data` is both a command and a step of two others.

    Its two internal callers hand it their own log as `_log`, which is what
    tells it the call is nested: it reports into that log rather than building
    a second one to be copied across, so the session header is not repeated and
    its external calls reach the comlog the outer command opened.
    """
    sinfo, options, _ = session

    nested = fs.run_freesurfer_full_segmentation(sinfo, dict(options)).text
    alone = fs.check_for_freesurfer_data(sinfo, dict(options)).text

    assert "looking for: " in nested, "the nested check's report is missing"
    assert "Session id: s01" in alone
    assert nested.count("Session id: s01") == 1
