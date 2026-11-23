# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Longitudinal HCP runs are judged by the pipeline's exit code.

Where a longitudinal pipeline writes its results depends on the pipeline
version and the session naming, and test files that did not match marked
successful runs as failed (``error_`` comlogs for a clean exit). The
longitudinal commands now check no test file, and do not read a successful
pipeline's error-looking output lines as a failure either.
"""

import os

import pytest

import qx_utilities.general.core as gc
import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog
from qx_utilities.hcp.hcp_long_freesurfer import hcp_long_freesurfer
from qx_utilities.hcp.hcp_long_post_freesurfer import hcp_long_post_freesurfer
from qx_utilities.hcp.hcp_long_transmit_bias import hcp_long_transmit_bias
from qx_utilities.hcp.hcp_utils import run_longitudinal_pipeline

from .utils import build_hcp_session, default_options


def _files(root):
    """Every file and link under root, so a dry run can be shown to write nothing."""
    found = []
    for d, dirs, files in os.walk(root):
        found += [os.path.join(d, f) for f in files + dirs]
    return sorted(found)


@pytest.fixture
def pipeline(tmp_path):
    """Options and a pipeline log folder for `run_longitudinal_pipeline`."""

    def _build(**overrides):
        logdir = tmp_path / "extra_logs"
        logdir.mkdir()
        options = default_options(
            comlogs=str(tmp_path / "comlogs"), command_ran="hcp_long_test", **overrides
        )
        return options, logdir

    return _build


def test_pipeline_success_with_error_lines_is_done(pipeline, tmp_path):
    options, logdir = pipeline(run="run", log="keep")
    comm = f"echo 'ERROR: harmless'; echo 'own log' > {logdir}/Pipeline.sh.1.o.log"
    log = ReportLog()

    report, failed = run_longitudinal_pipeline(
        comm, "HCP Longitudinal Test", options, False, "subj-01", str(logdir), log
    )

    assert (report, failed) == ("processing completed", 0)
    comlogs = os.listdir(tmp_path / "comlogs")
    assert len(comlogs) == 1 and comlogs[0].startswith("done_")
    text = (tmp_path / "comlogs" / comlogs[0]).read_text()
    assert "Contents of Pipeline.sh.1.o.log" in text
    assert text.rstrip().splitlines()[-1].startswith("---> Successful completion")
    assert not logdir.exists()


def test_pipeline_failure_keeps_its_own_logs(pipeline):
    options, logdir = pipeline(run="run", log="keep")
    log = ReportLog()

    with pytest.raises(pc.ExternalFailed):
        run_longitudinal_pipeline(
            "exit 1", "HCP Longitudinal Test", options, False, "subj-01", str(logdir), log
        )

    assert logdir.exists()
    assert str(logdir) in log.text


def test_pipeline_success_with_removed_comlog(pipeline, tmp_path):
    """--log=remove deletes a clean comlog; appending to it used to crash."""
    options, logdir = pipeline(run="run", log="remove")
    log = ReportLog()

    report, failed = run_longitudinal_pipeline(
        "true", "HCP Longitudinal Test", options, False, "subj-01", str(logdir), log
    )

    assert (report, failed) == ("processing completed", 0)
    assert not logdir.exists()


def test_pipeline_dry_run_runs_nothing(pipeline, tmp_path):
    options, logdir = pipeline(run="test")
    marker = tmp_path / "ran"
    log = ReportLog()

    report, failed = run_longitudinal_pipeline(
        f"touch {marker}", "HCP Longitudinal Test", options, False, "subj-01",
        str(logdir), log,
    )

    assert (report, failed) == ("ready", 0)
    assert "HCP Longitudinal Test can be run" in log.text
    assert not marker.exists()


@pytest.fixture
def subject(tmp_path, monkeypatch):
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    sinfo, sessionsfolder = build_hcp_session(str(tmp_path))
    options = default_options(
        run="test",
        sessionsfolder=sessionsfolder,
        comlogs=str(tmp_path / "comlogs"),
        logfolder=str(tmp_path / "logs"),
    )
    return gc.SessionList([sinfo]), options


def test_long_freesurfer_dry_run_changes_nothing(subject, tmp_path):
    sinfo, options = subject
    long_dir = tmp_path / "subjects" / "subj-01" / "subj-01.long.base"
    long_dir.mkdir(parents=True)
    (long_dir / "keep.txt").write_text("existing results")
    before = _files(tmp_path)

    log = hcp_long_freesurfer(sinfo, options, overwrite=True)

    assert "test, not removed" in log.text
    assert "test, not linked" in log.text
    assert "HCP Longitudinal FS can be run" in log.text
    assert log.status[1:] == ("ready", 0)
    assert _files(tmp_path) == before


@pytest.mark.parametrize(
    "command, name, settings",
    [
        (hcp_long_post_freesurfer, "HCP Longitudinal Post FS", {"hcp_prefs_template_res": "0.8"}),
        (
            hcp_long_transmit_bias,
            "HCP Longitudinal Transmit Bias",
            {
                "hcp_transmit_mode": "AFI",
                "hcp_afi_tr_one": "20",
                "hcp_afi_tr_two": "100",
                "hcp_afi_angle": "50",
                "hcp_group_corrected_myelin": "group_corrected_myelin.dscalar.nii",
            },
        ),
    ],
)
def test_long_dry_runs_are_ready_and_write_nothing(subject, tmp_path, command, name, settings):
    sinfo, options = subject
    options.update(settings)
    before = _files(tmp_path)

    log = command(sinfo, options)

    assert f"{name} can be run" in log.text, log.text
    assert log.status[1:] == ("ready", 0)
    assert _files(tmp_path) == before
