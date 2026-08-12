#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``processing/workflow.py``'s five unguarded commands honour ``--test``.

Measured by AST: five of the file's seven registered processing commands --
``get_bold_data``, ``create_bold_brain_masks``, ``compute_bold_stats``,
``create_stats_report`` and ``extract_nuisance_signal`` -- never consulted
``options["run"]`` anywhere in their bodies. Only ``preprocess_bold`` and
``preprocess_conc`` did. A ``--test`` run of any of the five therefore copied
and linked files, invoked FSL and MATLAB (and, at the time, R), and -- in
``create_stats_report`` -- deleted the existing movement reports before
regenerating them, all while the report said the command was being tested.

``create_stats_report`` no longer runs anything external: its work is now
``processing/mov_stats.py``, called in process. The dry run still has to guard
it, since it appends to the group reports and writes the fidl snippets.

This is the same defect ``processing/fs.py`` had, and these tests are that
file's ``test_fs_dryrun.py`` applied here: nothing is executed, nothing on disk
changes, and the report still names the external command in full so a dry run
is worth reading.

**Directories are deliberately not compared.** ``pc.get_session_folders``
creates the session skeleton whenever it resolves paths, for every processing
command in the tree including the four in ``fs.py``; that is shared behaviour
older than this fix and out of its scope. What must not happen is a *file*
being written, changed or removed, which is what :func:`_tree` records.
"""

import os
import subprocess

import pytest

import qx_utilities.processing.workflow as wf
from tests.utils import default_options

COMMANDS = [
    "get_bold_data",
    "create_bold_brain_masks",
    "compute_bold_stats",
    "create_stats_report",
    "extract_nuisance_signal",
]

# `create_bold_brain_masks` skips BET when the masks are already there, and the
# fixture has to provide them for `extract_nuisance_signal` to get past its own
# check -- so this one command is driven with overwrite on, which is what takes
# it through the slice and the seven external calls
OVERWRITE = {"create_bold_brain_masks": True}

# the tool each command reaches with this fixture, and must name in its report
TOOLS = {
    "get_bold_data": "g_FlipFormat",
    "create_bold_brain_masks": "bet ",
    "compute_bold_stats": "matlab",
    # the only one of the five that no longer shells out at all: it names the
    # work rather than a tool, which is the point of dropping the subprocess
    "create_stats_report": "movement and statistics reporting",
    "extract_nuisance_signal": "matlab",
}


def _tree(root):
    """Every file under `root`, with its size and mtime. Directories excluded."""
    found = {}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            stat = os.stat(path)
            found[path] = (stat.st_size, stat.st_mtime_ns)
    return found


@pytest.fixture
def session(tmp_path, monkeypatch):
    """
    A session complete enough for all five commands, every external call fatal.

    `executed` is the belt to the raised exception's braces: three of these
    commands catch ``Exception`` and record it as an unknown error, so a test
    that only relied on the raise would pass while the command had in fact run
    something.
    """
    sessions = tmp_path / "sessions"
    atlas = sessions / "s01" / "4dfp" / "atlas"
    atlas.mkdir(parents=True)
    for name in ("s01_mpr_n1_111_t88.4dfp.img", "s01_mpr_n1_111_t88.4dfp.ifh"):
        (atlas / name).write_bytes(b"x" * 300)

    functional = sessions / "s01" / "images" / "functional"
    (functional / "movement").mkdir(parents=True)
    masks = sessions / "s01" / "images" / "segmentation" / "boldmasks"
    masks.mkdir(parents=True)
    freesurfer = sessions / "s01" / "images" / "segmentation" / "freesurfer" / "mri"
    freesurfer.mkdir(parents=True)
    (sessions / "QC" / "movement").mkdir(parents=True)

    for bold in ("bold1", "bold2"):
        (functional / (bold + ".nii.gz")).write_bytes(b"x" * 300)
        (functional / "movement" / (bold + "_mov.dat")).write_text("1 0 0 0 0 0\n")
        (functional / "movement" / (bold + ".bstats")).write_text("1\n")
        (functional / "movement" / (bold + ".scrub")).write_text("1\n")
        for tail in (
            "_frame1.nii.gz",
            "_frame1_brain.nii.gz",
            "_frame1_brain_mask.nii.gz",
        ):
            (masks / (bold + tail)).write_bytes(b"x" * 300)
    for name in ("aseg_bold.nii.gz", "aparc+aseg_bold.nii.gz"):
        (freesurfer / name).write_bytes(b"x" * 300)

    # the existing movement report `create_stats_report` clears before
    # regenerating it: the destructive step a dry run must not take. It lives in
    # the study's QC folder, which is where `--mov_mreport` is resolved to
    (sessions / "QC" / "movement" / "bold_mov_report.txt").write_text("keep me")

    executed = []

    def no_external(*args, **kwargs):
        executed.append(args[:1])
        raise AssertionError("a --test run executed an external command")

    for name in ("run", "call", "check_call", "Popen"):
        monkeypatch.setattr(subprocess, name, no_external)
    # the catch-all handlers nap before returning; a test that trips one should
    # fail fast rather than sleep
    monkeypatch.setattr(wf.time, "sleep", lambda *_: None)

    options = default_options(
        sessionsfolder=str(sessions),
        run="test",
        comlogs=str(tmp_path / "comlogs"),
        mov_mreport="mov_report.txt",
    )
    # `default_options` recodes "" to None, which the file-name builders
    # concatenate; the CLI supplies real empty strings for these
    for name, value in list(options.items()):
        if value is None and ("tail" in name or "variant" in name or "pref" in name):
            options[name] = ""

    sinfo = {
        "id": "s01",
        "data": str(sessions / "s01" / "4dfp"),
        "1": {"name": "bold1", "task": "rest", "bold_number": 1},
        "2": {"name": "bold2", "task": "rest", "bold_number": 2},
    }
    return sinfo, options, tmp_path, executed


# `create_stats_report` clears the existing reports only on the first thread,
# so a dry run driven with the default thread=0 never reaches its one
# destructive step
THREAD = {"create_stats_report": 1}


def _drive(session, command):
    sinfo, options, root, executed = session
    log = getattr(wf, command)(
        sinfo,
        dict(options),
        overwrite=OVERWRITE.get(command, False),
        thread=THREAD.get(command, 0),
    )
    return log.text, executed


@pytest.mark.parametrize("command", COMMANDS)
def test_a_test_run_changes_nothing_on_disk(session, command):
    _, _, root, _ = session
    before = _tree(root)

    report, _ = _drive(session, command)

    assert _tree(root) == before, "a --test run wrote, removed or replaced a file"
    assert "Unknown error occured" not in report, report


@pytest.mark.parametrize("command", COMMANDS)
def test_a_test_run_executes_no_external_command(session, command):
    report, executed = _drive(session, command)

    assert executed == [], "a --test run reached subprocess: %r" % (executed,)
    assert "Unknown error occured" not in report, report


@pytest.mark.parametrize("command", COMMANDS)
def test_a_test_run_names_the_command_it_would_have_run(session, command):
    """A dry run that guards its work but reports nothing is not worth running."""
    report, _ = _drive(session, command)

    assert "test, not " in report, report
    assert TOOLS[command] in report, "the dry run does not name %r" % TOOLS[command]


def test_an_existing_movement_report_survives_a_test_run(session):
    """
    The destructive step, pinned on its own.

    `create_stats_report` deletes the movement reports before regenerating
    them. Under `--test` nothing regenerates them, so deleting them would leave
    the session worse off than before the dry run.
    """
    _, _, root, _ = session
    keep = root / "sessions" / "QC" / "movement" / "bold_mov_report.txt"

    report, _ = _drive(session, "create_stats_report")

    assert keep.exists(), "a --test run deleted an existing movement report"
    assert keep.read_text() == "keep me"
    assert "test, not removed: %s" % keep in report


def test_the_bold_readiness_check_reads_the_bold_and_not_a_stale_status(session):
    """
    `get_bold_data`'s per-bold check used to read the last conversion's status.

    That name is unbound whenever no conversion ran -- every run where the T1 is
    already in place, and every dry run -- so the `except Exception` below it
    reported an unknown error once per bold instead of saying anything about
    the data. The bolds are present in this fixture, so the answer is "ready".
    """
    report, _ = _drive(session, "get_bold_data")

    assert report.count("Data ready!") == 2
    assert "Data missing" not in report


def test_bolds_all_processes_every_bold(session):
    """
    The default `--bolds=all` used to process nothing at all.

    `get_bold_data` was the only command in the file with a hand-rolled bold
    selection: it compared each bold's `task` against `options["bolds"]` split
    on "|", so the default "all" matched no task and the loop body never ran.
    It now uses `use_or_skip_bold`, the same helper its five siblings use.
    """
    sinfo, options, _, _ = session
    assert options["bolds"] == "all", "the fixture must exercise the default"

    report = wf.get_bold_data(sinfo, dict(options)).text

    assert "Working on: bold1" in report
    assert "Working on: bold2" in report
    assert report.count("Data ready!") == 2


def test_bolds_can_still_name_a_subset(session):
    """Naming one bold selects it and reports the other as skipped."""
    sinfo, options, _, _ = session
    options["bolds"] = "bold2"

    report = wf.get_bold_data(sinfo, dict(options)).text

    assert "Working on: bold2" in report
    assert "Working on: bold1" not in report
    assert "Skipping the following BOLD images" in report
