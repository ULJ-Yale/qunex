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
logging refactor guarantees: a command returns its **log**, whose ``status`` is
a three-field ``(id, summary, failed)`` triple and whose ``text`` opens with the
session header and closes with the pipeline footer. Commands that reach further
on this fixture assert a little more.
"""

import os

import pytest

import qx_utilities.general.core as gc
import qx_utilities.general.log as gl
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
from qx_utilities.hcp.hcp_roi_to_dicom import hcp_roi_to_dicom
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
from qx_utilities.hcp.hcp_utils import handle_hcp_links, write_transmit_bias_voltages
from qx_utilities.hcp.map_hcp_data import map_hcp_data

from .utils import build_hcp_session, default_options

RULE = "------------------------------------------------------------"


@pytest.fixture
def session(tmp_path, monkeypatch):
    """Build a session (and its options) ready for a dry run of one command."""
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    monkeypatch.setenv("QUNEXPATH", str(tmp_path / "qunexpath"))

    def _build(bolds=False, dwi=False, subject=False, multisession=False, **overrides):
        sinfo, sessionsfolder = build_hcp_session(str(tmp_path), bolds=bolds, dwi=dwi)
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
    log = hcp_pre_freesurfer(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "HCP PreFreeSurfer Pipeline" in report


def test_freesurfer_dry_run(session):
    sinfo, options = session()
    log = hcp_freesurfer(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "HCP FreeSurfer Pipeline" in report
    assert "PreFS" in report


def test_post_freesurfer_dry_run(session):
    sinfo, options = session()
    log = hcp_post_freesurfer(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "HCP PostFreeSurfer" in report or "HCP PostFS" in report


def test_nhp_freesurfer_dry_run(session):
    sinfo, options = session()
    log = hcp_nhp_freesurfer(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "NHP FreeSurfer" in report


def test_cortical_thickness_dry_run(session):
    sinfo, options = session()
    log = hcp_cortical_thickness(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert status[1] == "HCP CorrThick can be run"
    assert "Running HCP Pipelines command via QuNex:" in report
    assert '\n    --subject="sess-01"' in report


def test_roi_to_dicom_dry_run(session):
    sinfo, options = session(
        hcp_roidicom_input="/data/dicom/20", hcp_roidicom_cifti_roi="roi.dscalar.nii"
    )
    output = os.path.join(sinfo["hcp"], "sess-01", "T1w", "T1w_with_ROI_DICOM")
    log = hcp_roi_to_dicom(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert status[1] == "HCP ROI to DICOM can be run"
    assert status[2] == 0
    assert "ROI_to_DICOM.sh" in report
    assert '\n    --dicom-input="/data/dicom/20"' in report
    assert '\n    --cifti-roi-in="roi.dscalar.nii"' in report
    assert '\n    --surf-reg-name="MSMSulc"' in report
    assert '--dicom-output="%s"' % output in report
    assert "--vertex-in" not in report
    assert not os.path.exists(output)


def test_roi_to_dicom_rejects_bad_roi_options(session):
    sinfo, options = session(
        hcp_roidicom_cifti_roi="roi.dscalar.nii", hcp_roidicom_vertex="0"
    )
    log = hcp_roi_to_dicom(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert status[2] == 1
    assert "got hcp_roidicom_cifti_roi, hcp_roidicom_vertex" in report
    assert "requires the hcp_roidicom_vertex_structure parameter" in report
    assert "ROI_to_DICOM.sh" not in report


# ------------------------------------------------------------------- diffusion


def test_diffusion_dry_run(session):
    sinfo, options = session(dwi=True)
    log = hcp_diffusion(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "Diffusion" in report
    assert "Running HCP Pipelines command via QuNex:" in report
    # human runs must not pass any of the NHP options
    for nhp in [
        "--species",
        "--truepatientposition",
        "--scannerpatientposition",
        "--wmprojabs",
        "--resamp",
        "--usephasezero",
    ]:
        assert nhp not in report


def test_diffusion_nhp_dry_run(session):
    sinfo, options = session(
        dwi=True,
        hcp_species="Macaque",
        hcp_truepatientposition="HFP",
        hcp_scannerpatientposition="HFS",
        hcp_dwi_wmprojabs="1",
        hcp_dwi_resamp="lsr",
        hcp_dwi_usephasezero=True,
    )
    log = hcp_diffusion(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "--species=Macaque" in report
    assert "--truepatientposition=HFP" in report
    assert "--scannerpatientposition=HFS" in report
    assert "--wmprojabs=1" in report
    assert "--resamp=lsr" in report
    assert "--usephasezero=True" in report


def test_longitudinal_diffusion_dry_run_says_it_can_be_run(session, tmp_path):
    """
    A longitudinal run has no test file. `check_run` took that as a finished
    run, so the dry run reported the session as done rather than runnable.
    """
    sinfo, options = session(
        dwi=True,
        longitudinal=True,
        hcp_longitudinal_template="TPL",
        studyfolder=str(tmp_path),
    )
    log = hcp_diffusion(sinfo, options)

    assert log.status == ("sess-01", "HCP Diffusion can be run", 0)
    assert "DiffPreprocPipeline" in log.text


# ------------------------------------------------------------------ functional


def test_fmri_volume_dry_run(session):
    sinfo, options = session(bolds=True)
    log = hcp_fmri_volume(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "fMRI Volume" in report


def test_fmri_surface_dry_run(session):
    sinfo, options = session(bolds=True)
    log = hcp_fmri_surface(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "fMRI" in report


def test_fmri_stats_dry_run(session):
    sinfo, options = session(bolds=True)
    log = hcp_fmri_stats(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "fMRI Stats" in report


def test_task_fmri_analysis_dry_run(session):
    sinfo, options = session()
    log = hcp_task_fmri_analysis(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "task analysis" in report or "task fMRI" in report.lower()


# ------------------------------------------------------------------- denoising


def test_icafix_dry_run(session):
    sinfo, options = session(bolds=True)
    log = hcp_icafix(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "ICAFix" in report


def test_post_fix_dry_run(session):
    sinfo, options = session(bolds=True)
    log = hcp_post_fix(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "PostFix" in report


def test_reapply_fix_dry_run(session):
    sinfo, options = session(bolds=True)
    log = hcp_reapply_fix(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "ReApplyFix" in report


def test_msmall_dry_run(session):
    sinfo, options = session(bolds=True)
    log = hcp_msmall(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "MSMAll" in report


def test_dedrift_and_resample_dry_run(session):
    sinfo, options = session(bolds=True)
    log = hcp_dedrift_and_resample(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "DeDriftAndResample" in report


def test_apply_auto_reclean_dry_run(session):
    sinfo, options = session(bolds=True)
    log = hcp_apply_auto_reclean(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "Reclean" in report


def test_temporal_ica_dry_run(session):
    sinfo, options = session(multisession=True)
    log = hcp_temporal_ica(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "temporal ICA" in report


# ------------------------------------------------------------------------ misc


def test_asl_dry_run(session):
    sinfo, options = session()
    log = hcp_asl(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "ASL" in report


def test_transmit_bias_individual_dry_run(session):
    sinfo, options = session()
    log = hcp_transmit_bias_individual(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "Transmit Bias" in report


def test_make_average_dataset_dry_run(session):
    sinfo, options = session(multisession=True)
    log = hcp_make_average_dataset(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "average dataset" in report


def test_map_hcp_data_dry_run(session):
    sinfo, options = session(bolds=True)
    log = map_hcp_data(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "Mapping HCP data" in report


def test_map_hcp_data_reports_a_session_it_finds_no_hcp_folder_for(session):
    """
    A session given with --sessions and no batch file is a record of its id
    alone. Its report was filed under a `session` key such a record does not
    have, so the command raised a KeyError instead of saying what was wrong.
    """
    _, options = session()

    log = map_hcp_data({"id": "sess-01"}, options)

    assert log.status == (
        "sess-01",
        "Mapping sess-01 failed, check your input parameters and data!",
        1,
    )


# ---------------------------------------------------------------- longitudinal


def test_prep_long_dry_run(session):
    sinfo, options = session(subject=True)
    log = hcp_prep_long(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status, sid="subj-01")
    assert "prep long" in report


def test_long_freesurfer_dry_run(session):
    sinfo, options = session(subject=True)
    log = hcp_long_freesurfer(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status, sid="subj-01")
    assert "Longitudnal FS" in report or "Longitudinal FS" in report


def test_long_post_freesurfer_dry_run(session):
    sinfo, options = session(subject=True)
    log = hcp_long_post_freesurfer(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status, sid="subj-01")
    assert "Post FS" in report or "Post FS" in report


def test_long_msmall_dry_run(session):
    sinfo, options = session(subject=True, bolds=True)
    log = hcp_long_msmall(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status, sid="subj-01")
    assert "MSMAll" in report


def test_long_transmit_bias_dry_run(session):
    sinfo, options = session(subject=True)
    log = hcp_long_transmit_bias(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status, sid="subj-01")
    assert "Transmit Bias" in report or "FS Pipeline" in report


def test_the_subjects_folder_is_the_study_one_whatever_the_path_holds(
    tmp_path, monkeypatch
):
    """
    The subjects folder was `sessionsfolder.replace("sessions", "subjects")`,
    which rewrites every "sessions" in the path: a study kept under a folder
    named with it had its subjects put in a folder that is not the study's.
    """
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    monkeypatch.setenv("QUNEXPATH", str(tmp_path / "qunexpath"))

    study = tmp_path / "old_sessions" / "study"
    sinfo, _ = build_hcp_session(str(study))
    options = default_options(
        run="test",
        studyfolder=str(study),
        comlogs=str(tmp_path / "comlogs"),
        logfolder=str(tmp_path / "logs"),
        hcp_longitudinal_template="TPL",
    )

    log = hcp_long_freesurfer(gc.SessionList([sinfo]), options)

    assert '--path="%s"' % (study / "subjects" / "subj-01") in log.text
    assert not (tmp_path / "old_subjects").exists()


# ------------------------------------------------- transmit bias phases 1 - 4


def test_transmit_bias_individual_align_dry_run(session):
    sinfo, options = session()
    log = hcp_transmit_bias_individual_align(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "Individual Align" in report


def test_transmit_bias_group_average_fit_dry_run(session):
    sinfo, options = session(multisession=True)
    log = hcp_transmit_bias_group_average_fit(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "Group Average Fit" in report


def test_transmit_bias_individual_adjustment_dry_run(session):
    sinfo, options = session()
    log = hcp_transmit_bias_individual_adjustment(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "Individual Adjustment" in report


def test_transmit_bias_group_average_corrected_maps_dry_run(session):
    sinfo, options = session(multisession=True)
    log = hcp_transmit_bias_group_average_corrected_maps(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "Corrected Maps" in report


def test_create_transmit_bias_voltages_file_requires_hcp_voltages(session):
    """The voltages path is mandatory; without it the command must fail loudly."""
    sinfo, options = session(multisession=True)
    log = create_transmit_bias_voltages_file(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert "hcp_voltages parameter is mandatory" in report
    assert status[2] == 1


def test_create_transmit_bias_voltages_file_dry_run(session, tmp_path):
    """With --test the command reports the file it would create, and creates none."""
    target = tmp_path / "voltages.txt"
    sinfo, options = session(multisession=True, hcp_voltages=str(target))
    log = create_transmit_bias_voltages_file(sinfo, options)
    report, status = log.text, log.status
    _check_contract(report, status)
    assert str(target) in report
    assert status[2] == 0
    assert not target.exists()


def _hcp_sessions(root, ids, suffix):
    """Sessions whose hcp folders are recorded somewhere of their own."""
    sessions = []
    for sid in ids:
        hcp = os.path.join(root, "elsewhere", sid, "hcp")
        os.makedirs(os.path.join(hcp, sid + suffix, "unprocessed", "rfMRI_REST1_AP"))
        sessions.append({"id": sid, "hcp": hcp})
    return sessions


def test_transmit_bias_links_the_hcp_folder_of_each_session(tmp_path):
    """
    The links were made to `<sessionsfolder>/<id>/hcp/<id>` whatever the hcp
    suffix or the session's own hcp folder, and a missing one was not said.
    """
    sessions = _hcp_sessions(str(tmp_path), ["s1", "s2"], "_V1")
    group = str(tmp_path / "sessions" / "transmit_bias")
    options = default_options(sessionsfolder=str(tmp_path / "sessions"), hcp_suffix="_V1")

    log = gl.ReportLog()
    assert handle_hcp_links(group, sessions, options, False, _log=log)
    for session in sessions:
        link = os.path.join(group, session["id"] + "_V1")
        assert os.path.samefile(link, os.path.join(session["hcp"], session["id"] + "_V1"))
    assert "ERROR" not in log.text

    sessions[1]["hcp"] = str(tmp_path / "missing")
    log = gl.ReportLog()
    assert not handle_hcp_links(group, sessions, options, False, _log=log)
    assert "HCP folder of session s2 could not be copied" in log.text


def test_transmit_bias_voltages_are_read_from_the_hcp_folder_of_each_session(tmp_path):
    sessions = _hcp_sessions(str(tmp_path), ["s1", "s2"], "_V1")
    for value, session in zip([310, 320], sessions):
        json_file = os.path.join(
            session["hcp"], session["id"] + "_V1", "unprocessed", "rfMRI_REST1_AP",
            session["id"] + "_V1_rfMRI_REST1_AP.json",
        )
        with open(json_file, "w") as f:
            f.write('{"TxRefAmp": %d}' % value)
    voltages = tmp_path / "voltages.txt"
    options = default_options(sessionsfolder=str(tmp_path / "sessions"), hcp_suffix="_V1")

    assert write_transmit_bias_voltages(sessions, options, str(voltages), gl.ReportLog())
    assert voltages.read_text() == "310\n320\n"
