# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for ``general.scheduler.run_through_scheduler``'s use of the runlog.

The submission record belongs in the runlog the run already opened. Until N7.2
the scheduler opened that file with ``"w"`` and so threw away the header and
everything the caller had written before submitting -- these pin the append.

Nothing is submitted: ``--run=test`` stops before ``schedule()``, which is as
far as a scheduler can be exercised without one.
"""

import os

import pytest

import qx_utilities.general.log as gl
import qx_utilities.general.scheduler as gs

STAMP = "2026-07-26_12.00.00.000000"


@pytest.fixture
def run(tmp_path):
    return gl.RunContext(
        "hcp_pre_freesurfer",
        {"sessions": "batch.txt"},
        gl.LogSettings(),
        {"basefolder": str(tmp_path)},
        timestamp=STAMP,
    )


def runlog(run):
    with open(run.path) as f:
        return f.read()


def submit(run, sessions=None):
    gs.run_through_scheduler(
        run.command,
        sessions=sessions,
        args={"scheduler": "SLURM,time=1:00:00", "run": "test", "sessions": "batch.txt"},
        run=run,
    )


def test_the_submission_is_appended_to_the_runlog_the_run_opened(run):
    run.header()

    submit(run)

    log = runlog(run)
    assert "qunex hcp_pre_freesurfer" in log, "the header was overwritten"
    assert "Running scheduler for command hcp_pre_freesurfer" in log
    assert log.index("qunex hcp_pre_freesurfer") < log.index("Running scheduler")


def test_the_call_that_is_scheduled_is_recorded(run):
    run.header()

    submit(run)

    log = runlog(run)
    assert "submitting hcp_pre_freesurfer" in log
    assert 'gmri hcp_pre_freesurfer' in log
    assert '--sessions="batch.txt"' in log


def test_how_the_sessions_were_divided_is_recorded(run):
    run.header()

    submit(run, sessions=[{"id": "S01"}, {"id": "S02"}])

    log = runlog(run)
    assert "run the command over 2 sessions" in log
    assert "Job #1 will run sessions: S01" in log
    assert "Job #2 will run sessions: S02" in log


def test_job_output_goes_to_batchlogs_under_the_run_folder(run):
    submit(run)

    assert os.path.isdir(os.path.join(run.logfolder, "batchlogs"))


def test_a_run_without_a_runlog_still_submits(tmp_path, capsys):
    run = gl.RunContext(
        "hcp_pre_freesurfer",
        {},
        gl.LogSettings(enabled=False),
        {"basefolder": str(tmp_path)},
        timestamp=STAMP,
    )

    submit(run)

    assert "Running scheduler for command" in capsys.readouterr().out
    assert not list(tmp_path.rglob("*.log"))
