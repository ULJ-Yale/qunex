# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for how ``hcp_roi_to_dicom`` finds the T1w DICOM series on its own.

Without ``hcp_roidicom_input`` the command has to pick the T1w image
hcp_pre_freesurfer used first -- told by its data, as the order the images
were handed over in followed the directory listing -- read its series number
from the JSON sidecar and find that series in the session's ``dicom`` folder,
extracting it when import_dicom archived it.
"""

import io
import json
import os
import tarfile

import nibabel as nib
import numpy as np
import pytest

import qx_utilities.processing.core as pc
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp import hcp_roi_to_dicom as rd
from qx_utilities.hcp.hcp_paths import _glob_sorted, get_hcp_paths

from .utils import build_hcp_session, default_options


def _save(data, path, affine=None):
    nib.save(nib.Nifti1Image(data, np.eye(4) if affine is None else affine), path)


@pytest.fixture
def session(tmp_path, monkeypatch):
    """
    A session with two T1w images whose second one (series 20) was the first
    hcp_pre_freesurfer used, and series 20 archived the way import_dicom does.
    """
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    sinfo, sessionsfolder = build_hcp_session(str(tmp_path))
    base = os.path.join(sinfo["hcp"], "sess-01")
    rng = np.random.default_rng(0)

    images = {}
    for n, series in [(1, 19), (2, 20)]:
        images[n] = rng.random((12, 14, 16)).astype(np.float32)
        stem = os.path.join(base, "unprocessed", "T1w", f"sess-01_T1w_MPR{n}")
        _save(images[n], stem + ".nii.gz")
        with open(stem + ".json", "w") as f:
            json.dump({"SeriesNumber": series}, f)

    # hcp_pre_freesurfer stores its first image reoriented, here flipped along x
    flip = np.diag([-1.0, 1.0, 1.0, 1.0])
    flip[0, 3] = 11
    _save(images[2][::-1], os.path.join(base, "T1w", "T1w1_gdc.nii.gz"), flip)

    dicom = os.path.join(sessionsfolder, "sess-01", "dicom")
    os.makedirs(os.path.join(dicom, "190"))
    with tarfile.open(os.path.join(dicom, "200.tar.gz"), "w:gz") as tar:
        for name in ["200/a.dcm", "200/b.dcm"]:
            info = tarfile.TarInfo(name)
            info.size = 4
            tar.addfile(info, io.BytesIO(b"DICM"))

    options = default_options(
        run="test",
        sessionsfolder=sessionsfolder,
        comlogs=str(tmp_path / "comlogs"),
        hcp_roidicom_vertex="0",
        hcp_roidicom_vertex_structure="CORTEX_LEFT",
    )
    return sinfo, options, base


def test_first_t1w_is_told_by_data(session):
    sinfo, options, base = session
    hcp = get_hcp_paths(sinfo, options)
    assert hcp["T1w"].split("@")[0].endswith("MPR1.nii.gz")

    first = rd._first_t1w(hcp, SessionLog(sinfo, options, "test"))
    assert first.endswith("sess-01_T1w_MPR2.nii.gz")


def test_dry_run_finds_archived_series(session):
    sinfo, options, base = session
    log = rd.hcp_roi_to_dicom(sinfo, options)
    report, status = log.text, log.status

    assert status[2] == 0, report
    assert "T1w DICOM series 20 of sess-01_T1w_MPR2.nii.gz" in report
    assert "test, not extracted:" in report and "200.tar.gz" in report
    assert "ROI_to_DICOM_XXXXXX/dicom" in report
    assert not [e for e in os.listdir(os.path.join(base, "T1w")) if e.startswith("ROI_to_DICOM_")]


def test_run_extracts_series_and_removes_it(session, monkeypatch):
    sinfo, options, base = session
    options["run"] = "run"
    seen = {}

    def fake_run(checkfile, comm, *args, **kwargs):
        dicom = comm.split('--dicom-input="')[1].split('"')[0]
        seen["dicom"], seen["files"] = dicom, sorted(os.listdir(dicom))
        return None, "HCP ROI to DICOM done", 0

    monkeypatch.setattr(pc, "run_external_for_file", fake_run)
    log = rd.hcp_roi_to_dicom(sinfo, options)

    assert log.status[2] == 0, log.text
    assert seen["files"] == ["a.dcm", "b.dcm"]
    assert seen["dicom"].startswith(os.path.join(base, "T1w", "ROI_to_DICOM_"))
    assert not os.path.exists(seen["dicom"])


def test_missing_series_is_reported(session):
    sinfo, options, base = session
    os.remove(os.path.join(options["sessionsfolder"], "sess-01", "dicom", "200.tar.gz"))
    log = rd.hcp_roi_to_dicom(sinfo, options)

    assert log.status[2] == 1
    assert "DICOM series 20 of sess-01_T1w_MPR2.nii.gz not found" in log.text
    assert "ROI_to_DICOM.sh" not in log.text


def test_glob_sorted_follows_numbers(tmp_path):
    for n in [10, 2, 1]:
        open(tmp_path / f"s_T1w_MPR{n}.nii.gz", "w").close()
    found = [os.path.basename(e) for e in _glob_sorted(str(tmp_path / "*.nii.gz"))]
    assert found == ["s_T1w_MPR1.nii.gz", "s_T1w_MPR2.nii.gz", "s_T1w_MPR10.nii.gz"]
