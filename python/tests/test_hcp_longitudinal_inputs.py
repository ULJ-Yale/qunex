# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Longitudinal HCP runs need nothing from a session's unprocessed folder.

The longitudinal variants of hcp_fmri_volume and hcp_diffusion reuse the
cross-sectional outputs: fMRIVolume links the cross-sectional
``<bold>/<bold>_orig.nii.gz`` and reuses its motion and distortion correction,
DiffPreprocPipeline copies the cross-sectional Pre-Eddy and Eddy outputs and
runs only Post-Eddy. These dry runs delete ``unprocessed/`` and check that the
commands are still built, and that a missing cross-sectional output is what
gets reported instead.
"""

import os
import shutil

import pytest

import qx_utilities.general.core as gc
from qx_utilities.hcp.hcp_diffusion import hcp_diffusion
from qx_utilities.hcp.hcp_fmri_volume import hcp_fmri_volume
from qx_utilities.hcp.hcp_prep_long import hcp_prep_long

from .utils import build_hcp_session, default_options

BOLDS = ["BOLD_1", "BOLD_2"]

TOPUP = dict(
    hcp_bold_dcmethod="TOPUP",
    hcp_bold_sephasepos="PA",
    hcp_bold_sephaseneg="AP",
    hcp_bold_unwarpdir="y",
    hcp_bold_sbref="USE",
    hcp_bold_movref="first",
    hcp_bold_doslicetime=True,
    hcp_bold_slicetimingfile=True,
)


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()


def _files(root):
    """Every file under root, so a dry run can be shown to write nothing."""
    return sorted(
        os.path.join(d, f) for d, _, files in os.walk(root) for f in files
    )


@pytest.fixture
def longitudinal(tmp_path, monkeypatch):
    """A session with its structural results in place and no unprocessed folder."""
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))

    def _build(bolds=False, dwi=False, cross=True, **overrides):
        sinfo, sessionsfolder = build_hcp_session(str(tmp_path), bolds=bolds, dwi=dwi)
        base = os.path.join(sinfo["hcp"], sinfo["id"])
        if bolds:
            # use_or_skip_bold only takes bold<N> names
            sinfo["3"]["name"] = "bold1"
            sinfo["4"]["name"] = "bold2"
        _touch(os.path.join(base, "T1w", "T1w_acpc_dc_restore_brain.nii.gz"))
        _touch(os.path.join(base, "T1w", sinfo["id"], "mri", "aparc+aseg.mgz"))
        _touch(os.path.join(
            base, "MNINonLinear", "fsaverage_LR32k", sinfo["id"] + ".32k_fs_LR.wb.spec"
        ))
        shutil.rmtree(os.path.join(base, "unprocessed"))
        if cross:
            for bold in BOLDS:
                _touch(os.path.join(base, bold, f"{bold}_orig.nii.gz"))
            os.makedirs(os.path.join(base, "Diffusion"))

        options = default_options(
            run="test",
            sessionsfolder=sessionsfolder,
            comlogs=str(tmp_path / "comlogs"),
            hcp_filename="userdefined",
            longitudinal=True,
            **overrides,
        )
        return sinfo, options, base

    return _build


def test_fmri_volume_longitudinal_needs_no_unprocessed_data(longitudinal, tmp_path):
    sinfo, options, base = longitudinal(bolds=True, **TOPUP)
    before = _files(tmp_path)

    log = hcp_fmri_volume(sinfo, options)
    report = log.text

    assert "ERROR" not in report, report
    # judged by the exit code, there is no test file that could mark it done
    assert log.status[1:] == ("HCP fMRI Volume: bolds BOLD_1, BOLD_2 ready", 0)
    assert "unprocessed" not in report
    for bold in BOLDS:
        orig = os.path.join(base, bold, f"{bold}_orig.nii.gz")
        assert f'--fmritcs="{orig}"' in report
    # the pipeline still requires the spin echo arguments for TOPUP
    assert '--SEPhaseNeg="NONE"' in report
    assert '--SEPhasePos="NONE"' in report
    assert '--fmriscout="NONE"' in report
    assert '--is-longitudinal="1"' in report
    # the movement reference and slice timing are cross-sectional only
    assert "--fmriref" not in report
    assert "--tcustom" not in report
    assert _files(tmp_path) == before


def test_fmri_volume_longitudinal_fieldmap_placeholders(longitudinal):
    sinfo, options, _ = longitudinal(
        bolds=True, hcp_bold_dcmethod="SiemensFieldMap", hcp_bold_unwarpdir="y"
    )
    log = hcp_fmri_volume(sinfo, options)
    report = log.text

    assert "ERROR" not in report, report
    # set but unused in longitudinal mode, the pipeline only checks they are set
    assert '--echodiff="NONE"' in report
    assert '--echospacing="NONE"' in report
    assert '--fmapmag="NONE"' in report


def test_fmri_volume_longitudinal_reports_missing_cross_sectional_run(longitudinal):
    sinfo, options, base = longitudinal(bolds=True, cross=False, **TOPUP)
    log = hcp_fmri_volume(sinfo, options)
    report = log.text

    assert "cross-sectional fMRIVolume results missing" in report
    assert os.path.join(base, "BOLD_1", "BOLD_1_orig.nii.gz") in report
    assert log.status[2] == 2


def test_fmri_volume_without_bolds_fails(longitudinal):
    sinfo, options, _ = longitudinal(hcp_bold_dcmethod="NONE")
    log = hcp_fmri_volume(sinfo, options)

    assert "No BOLD images found" in log.text
    assert log.status[2] == 1


def test_diffusion_longitudinal_needs_no_unprocessed_data(longitudinal, tmp_path):
    sinfo, options, base = longitudinal(dwi=True, hcp_dwi_dummy_bval_bvec=True)
    for k in sinfo:
        if k.isdigit() and sinfo[k]["name"] == "DWI":
            sinfo[k].pop("EchoSpacing")
    before = _files(tmp_path)

    log = hcp_diffusion(sinfo, options)
    report = log.text

    assert "ERROR" not in report, report
    assert log.status[1:] == ("HCP Diffusion can be run", 0)
    assert "unprocessed" not in report
    for arg in ["--PEdir", "--posData", "--negData", "--echospacing-seconds"]:
        assert arg not in report
    assert "--is-longitudinal=1" in report
    # the batch file declares an AP/PA pair, so the HCP default combine flag holds
    assert "--combine-data-flag" not in report
    assert _files(tmp_path) == before


def test_diffusion_longitudinal_unpaired_combine_flag(longitudinal):
    sinfo, options, _ = longitudinal(dwi=True)
    for k in [k for k in sinfo if k.isdigit()]:
        if sinfo[k]["name"] == "DWI" and sinfo[k]["task"].endswith("_AP"):
            del sinfo[k]

    log = hcp_diffusion(sinfo, options)
    assert "--combine-data-flag=2" in log.text


def test_diffusion_longitudinal_reports_missing_cross_sectional_run(longitudinal):
    sinfo, options, base = longitudinal(dwi=True, cross=False)
    log = hcp_diffusion(sinfo, options)

    assert "Cross-sectional hcp_diffusion results missing" in log.text
    assert os.path.join(base, "Diffusion") in log.text
    assert log.status[2] == 1


def test_diffusion_missing_echospacing_is_reported(tmp_path, monkeypatch):
    """No EchoSpacing anywhere is an error to report, not a crash."""
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    sinfo, sessionsfolder = build_hcp_session(str(tmp_path), dwi=True)
    for k in sinfo:
        if k.isdigit() and sinfo[k]["name"] == "DWI":
            sinfo[k].pop("EchoSpacing")
    options = default_options(
        run="test", sessionsfolder=sessionsfolder, comlogs=str(tmp_path / "comlogs")
    )

    log = hcp_diffusion(sinfo, options)
    assert "unable to acquire echospacing" in log.text
    assert "Unknown error" not in log.text
    assert log.status[2] == 1


def test_diffusion_dummy_bval_bvec_dry_run_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    sinfo, sessionsfolder = build_hcp_session(str(tmp_path), dwi=True)
    options = default_options(
        run="test",
        sessionsfolder=sessionsfolder,
        comlogs=str(tmp_path / "comlogs"),
        hcp_dwi_dummy_bval_bvec=True,
    )
    before = _files(tmp_path)

    log = hcp_diffusion(sinfo, options)
    assert "test, not created: dummy bval file for" in log.text
    assert "DWI_dir99_AP.nii.gz" in log.text
    assert _files(tmp_path) == before


def test_prep_long_dry_run_links_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    sinfo, sessionsfolder = build_hcp_session(str(tmp_path))
    options = default_options(
        run="test", sessionsfolder=sessionsfolder, comlogs=str(tmp_path / "comlogs")
    )

    log = hcp_prep_long(gc.SessionList([sinfo]), options)
    assert "test, not linked" in log.text
    # a session that would be linked is ready, not done
    assert "1 ready [sess-01], 0 failed" in log.status[1]
    assert not os.path.exists(tmp_path / "subjects")
