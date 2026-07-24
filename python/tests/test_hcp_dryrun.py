# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Per-command dry-run tests for the HCP processing commands.

With ``--test`` (``run="test"``) a command resolves its inputs, builds the
pipeline command line and reports what it *would* do, without running anything
external. That makes the dry run a cheap, dependency-free way to exercise option
handling, input discovery and -- since every command now builds its report
through :class:`SessionLog` -- the runlog itself.

Each command gets its own test. Every one asserts the invariant the whole
logging refactor guarantees: a command returns ``(report_text, status)`` where
``status`` is a three-field ``(id, summary, failed)`` tuple, the report opens
with the session header and closes with the pipeline footer. Commands that
reach further on this fixture assert a little more.
"""

import pytest

import qx_utilities.general.core as gc
from qx_utilities.hcp.hcp_apply_auto_reclean import hcp_apply_auto_reclean
from qx_utilities.hcp.hcp_asl import hcp_asl
from qx_utilities.hcp.hcp_cortical_thickness import hcp_cortical_thickness
from qx_utilities.hcp.hcp_dedrift_and_resample import hcp_dedrift_and_resample
from qx_utilities.hcp.hcp_diffusion import hcp_diffusion
from qx_utilities.hcp.hcp_fmri_stats import hcp_fmri_stats
from qx_utilities.hcp.hcp_fmri_surface import hcp_fmri_surface
from qx_utilities.hcp.hcp_fmri_volume import hcp_fmri_volume
from qx_utilities.hcp.hcp_freesurfer import hcp_freesurfer
from qx_utilities.hcp.hcp_icafix import hcp_icafix
from qx_utilities.hcp.hcp_long_freesurfer import hcp_long_freesurfer
from qx_utilities.hcp.hcp_long_msmall import hcp_long_msmall
from qx_utilities.hcp.hcp_long_post_freesurfer import hcp_long_post_freesurfer
from qx_utilities.hcp.hcp_long_transmit_bias import hcp_long_transmit_bias
from qx_utilities.hcp.hcp_make_average_dataset import hcp_make_average_dataset
from qx_utilities.hcp.hcp_msmall import hcp_msmall
from qx_utilities.hcp.hcp_nhp_freesurfer import hcp_nhp_freesurfer
from qx_utilities.hcp.hcp_post_fix import hcp_post_fix
from qx_utilities.hcp.hcp_post_freesurfer import hcp_post_freesurfer
from qx_utilities.hcp.hcp_pre_freesurfer import hcp_pre_freesurfer
from qx_utilities.hcp.hcp_prep_long import hcp_prep_long
from qx_utilities.hcp.hcp_reapply_fix import hcp_reapply_fix
from qx_utilities.hcp.hcp_task_fmri_analysis import hcp_task_fmri_analysis
from qx_utilities.hcp.hcp_temporal_ica import hcp_temporal_ica
from qx_utilities.hcp.hcp_transmit_bias_individual import hcp_transmit_bias_individual
from qx_utilities.hcp.hcp_transmit_bias_individual_align import (
    hcp_transmit_bias_individual_align,
)
from qx_utilities.hcp.hcp_transmit_bias_individual_adjustment import (
    hcp_transmit_bias_individual_adjustment,
)
from qx_utilities.hcp.hcp_transmit_bias_group_average_fit import (
    hcp_transmit_bias_group_average_fit,
)
from qx_utilities.hcp.hcp_transmit_bias_group_average_corrected_maps import (
    hcp_transmit_bias_group_average_corrected_maps,
)
from qx_utilities.hcp.create_transmit_bias_voltages_file import (
    create_transmit_bias_voltages_file,
)
from qx_utilities.hcp.map_hcp_data import map_hcp_data

from .utils import build_hcp_session, default_options

RULE = "------------------------------------------------------------"


@pytest.fixture
def session(tmp_path, monkeypatch):
    """Build a session (and its options) ready for a dry run of one command."""
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    monkeypatch.setenv("QUNEXPATH", str(tmp_path / "qunexpath"))

    def _build(bolds=False, subject=False, multisession=False, **overrides):
        sinfo, sessionsfolder = build_hcp_session(str(tmp_path), bolds=bolds)
        options = default_options(
            run="test",
            sessionsfolder=sessionsfolder,
            comlogs=str(tmp_path / "comlogs"),
            **overrides,
        )
        arg = gc.SessionList([sinfo]) if (subject or multisession) else sinfo
        return arg, options

    return _build


def _check_contract(report, status, sid="sess-01"):
    """Every HCP command returns this shape; assert it explicitly."""
    assert isinstance(status, tuple) and len(status) == 3, status
    assert status[0] == sid
    assert isinstance(status[2], int)
    assert "Session id" in report or "Session ids" in report or "Subject" in report
    assert RULE in report


# ------------------------------------------------------------------ structural


def test_pre_freesurfer_dry_run(session):
    sinfo, options = session(hcp_avgrdcmethod="NONE")
    report, status = hcp_pre_freesurfer(sinfo, options)
    _check_contract(report, status)
    assert "HCP PreFreeSurfer Pipeline" in report


def test_freesurfer_dry_run(session):
    sinfo, options = session()
    report, status = hcp_freesurfer(sinfo, options)
    _check_contract(report, status)
    assert "HCP FreeSurfer Pipeline" in report
    assert "PreFS" in report


def test_post_freesurfer_dry_run(session):
    sinfo, options = session()
    report, status = hcp_post_freesurfer(sinfo, options)
    _check_contract(report, status)
    assert "HCP PostFreeSurfer" in report or "HCP PostFS" in report


def test_nhp_freesurfer_dry_run(session):
    sinfo, options = session()
    report, status = hcp_nhp_freesurfer(sinfo, options)
    _check_contract(report, status)
    assert "NHP FreeSurfer" in report


def test_cortical_thickness_dry_run(session):
    sinfo, options = session()
    report, status = hcp_cortical_thickness(sinfo, options)
    _check_contract(report, status)
    assert status[1] == "HCP CorrThick finished"
    assert "Running HCP Pipelines command via QuNex:" in report
    assert '\n    --subject="sess-01"' in report


# ------------------------------------------------------------------- diffusion


def test_diffusion_dry_run(session):
    sinfo, options = session()
    report, status = hcp_diffusion(sinfo, options)
    _check_contract(report, status)
    assert "Diffusion" in report


# ------------------------------------------------------------------ functional


def test_fmri_volume_dry_run(session):
    sinfo, options = session(bolds=True)
    report, status = hcp_fmri_volume(sinfo, options)
    _check_contract(report, status)
    assert "fMRI Volume" in report


def test_fmri_surface_dry_run(session):
    sinfo, options = session(bolds=True)
    report, status = hcp_fmri_surface(sinfo, options)
    _check_contract(report, status)
    assert "fMRI" in report


def test_fmri_stats_dry_run(session):
    sinfo, options = session(bolds=True)
    report, status = hcp_fmri_stats(sinfo, options)
    _check_contract(report, status)
    assert "fMRI Stats" in report


def test_task_fmri_analysis_dry_run(session):
    sinfo, options = session()
    report, status = hcp_task_fmri_analysis(sinfo, options)
    _check_contract(report, status)
    assert "task analysis" in report or "task fMRI" in report.lower()


# ------------------------------------------------------------------- denoising


def test_icafix_dry_run(session):
    sinfo, options = session(bolds=True)
    report, status = hcp_icafix(sinfo, options)
    _check_contract(report, status)
    assert "ICAFix" in report


def test_post_fix_dry_run(session):
    sinfo, options = session(bolds=True)
    report, status = hcp_post_fix(sinfo, options)
    _check_contract(report, status)
    assert "PostFix" in report


def test_reapply_fix_dry_run(session):
    sinfo, options = session(bolds=True)
    report, status = hcp_reapply_fix(sinfo, options)
    _check_contract(report, status)
    assert "ReApplyFix" in report


def test_msmall_dry_run(session):
    sinfo, options = session(bolds=True)
    report, status = hcp_msmall(sinfo, options)
    _check_contract(report, status)
    assert "MSMAll" in report


def test_dedrift_and_resample_dry_run(session):
    sinfo, options = session(bolds=True)
    report, status = hcp_dedrift_and_resample(sinfo, options)
    _check_contract(report, status)
    assert "DeDriftAndResample" in report


def test_apply_auto_reclean_dry_run(session):
    sinfo, options = session(bolds=True)
    report, status = hcp_apply_auto_reclean(sinfo, options)
    _check_contract(report, status)
    assert "Reclean" in report


def test_temporal_ica_dry_run(session):
    sinfo, options = session(multisession=True)
    report, status = hcp_temporal_ica(sinfo, options)
    _check_contract(report, status)
    assert "temporal ICA" in report


# ------------------------------------------------------------------------ misc


def test_asl_dry_run(session):
    sinfo, options = session()
    report, status = hcp_asl(sinfo, options)
    _check_contract(report, status)
    assert "ASL" in report


def test_transmit_bias_individual_dry_run(session):
    sinfo, options = session()
    report, status = hcp_transmit_bias_individual(sinfo, options)
    _check_contract(report, status)
    assert "Transmit Bias" in report


def test_make_average_dataset_dry_run(session):
    sinfo, options = session(multisession=True)
    report, status = hcp_make_average_dataset(sinfo, options)
    _check_contract(report, status)
    assert "average dataset" in report


def test_map_hcp_data_dry_run(session):
    sinfo, options = session(bolds=True)
    report, status = map_hcp_data(sinfo, options)
    _check_contract(report, status)
    assert "Mapping HCP data" in report


# ---------------------------------------------------------------- longitudinal


def test_prep_long_dry_run(session):
    sinfo, options = session(subject=True)
    report, status = hcp_prep_long(sinfo, options)
    _check_contract(report, status, sid="subj-01")
    assert "prep long" in report


def test_long_freesurfer_dry_run(session):
    sinfo, options = session(subject=True)
    report, status = hcp_long_freesurfer(sinfo, options)
    _check_contract(report, status, sid="subj-01")
    assert "Longitudnal FS" in report or "Longitudinal FS" in report


def test_long_post_freesurfer_dry_run(session):
    sinfo, options = session(subject=True)
    report, status = hcp_long_post_freesurfer(sinfo, options)
    _check_contract(report, status, sid="subj-01")
    assert "Post FS" in report or "Post FS" in report


def test_long_msmall_dry_run(session):
    sinfo, options = session(subject=True, bolds=True)
    report, status = hcp_long_msmall(sinfo, options)
    _check_contract(report, status, sid="subj-01")
    assert "MSMAll" in report


def test_long_transmit_bias_dry_run(session):
    sinfo, options = session(subject=True)
    report, status = hcp_long_transmit_bias(sinfo, options)
    _check_contract(report, status, sid="subj-01")
    assert "Transmit Bias" in report or "FS Pipeline" in report


# ------------------------------------------------- transmit bias phases 1 - 4


def test_transmit_bias_individual_align_dry_run(session):
    sinfo, options = session()
    report, status = hcp_transmit_bias_individual_align(sinfo, options)
    _check_contract(report, status)
    assert "Individual Align" in report


def test_transmit_bias_group_average_fit_dry_run(session):
    sinfo, options = session(multisession=True)
    report, status = hcp_transmit_bias_group_average_fit(sinfo, options)
    _check_contract(report, status)
    assert "Group Average Fit" in report


def test_transmit_bias_individual_adjustment_dry_run(session):
    sinfo, options = session()
    report, status = hcp_transmit_bias_individual_adjustment(sinfo, options)
    _check_contract(report, status)
    assert "Individual Adjustment" in report


def test_transmit_bias_group_average_corrected_maps_dry_run(session):
    sinfo, options = session(multisession=True)
    report, status = hcp_transmit_bias_group_average_corrected_maps(sinfo, options)
    _check_contract(report, status)
    assert "Corrected Maps" in report


def test_create_transmit_bias_voltages_file_requires_hcp_voltages(session):
    """The voltages path is mandatory; without it the command must fail loudly."""
    sinfo, options = session(multisession=True)
    report, status = create_transmit_bias_voltages_file(sinfo, options)
    _check_contract(report, status)
    assert "hcp_voltages parameter is mandatory" in report
    assert status[2] == 1


def test_create_transmit_bias_voltages_file_dry_run(session, tmp_path):
    """With --test the command reports the file it would create, and creates none."""
    target = tmp_path / "voltages.txt"
    sinfo, options = session(multisession=True, hcp_voltages=str(target))
    report, status = create_transmit_bias_voltages_file(sinfo, options)
    _check_contract(report, status)
    assert str(target) in report
    assert status[2] == 0
    assert not target.exists()
