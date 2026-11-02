#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
The unprocessed folders of the `hcpya` structure, and the XTRACT tract list.

Under `hcpya` setup_hcp names a field map folder `FieldMap<n>_strc` and its files
`<id>_FieldMap_*`; the commands looked in folders with the wrong tail and for
files with the tail in their name, so a field map was never found. Diffusion is
`Diffusion_unproc` there, or HCP's PreEddy deletes what it reads from.
"""

import os

import pytest

from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.hcp.hcp_utils import do_hcp_options_check
from qx_utilities.processing.dwi import dwi_xtract

from .utils import build_hcp_session, default_options


@pytest.fixture(autouse=True)
def hcppipedir(tmp_path, monkeypatch):
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))


@pytest.mark.parametrize(
    "structure, folder, tail",
    [("hcpya", "Diffusion_unproc", "_strc"), ("hcpls", "Diffusion", "")],
)
def test_the_paths_follow_what_setup_hcp_writes(tmp_path, structure, folder, tail):
    sinfo, sessionsfolder = build_hcp_session(str(tmp_path))
    base = os.path.join(sinfo["hcp"], "sess-01")
    source = base if structure == "hcpya" else os.path.join(base, "unprocessed")
    fieldmap = os.path.join(source, "FieldMap1" + tail)
    os.makedirs(fieldmap)
    magnitude = os.path.join(fieldmap, "sess-01_FieldMap_Magnitude.nii.gz")
    phase = os.path.join(fieldmap, "sess-01_FieldMap_Phase.nii.gz")
    for image in [magnitude, phase]:
        open(image, "w").close()

    options = default_options(
        sessionsfolder=sessionsfolder,
        hcp_folderstructure=structure,
        hcp_avgrdcmethod="SiemensFieldMap",
    )
    do_hcp_options_check(options, "hcp_pre_freesurfer")
    sinfo["3"] = {"name": "FM-Magnitude", "task": "FM-Magnitude", "fmnum": "1"}
    sinfo["4"] = {"name": "FM-Phase", "task": "FM-Phase", "fmnum": "1"}

    hcp = get_hcp_paths(sinfo, options)

    assert hcp["DWI_source"] == os.path.join(source, folder)
    assert hcp["DWI_folder"] == os.path.join(base, "Diffusion")
    assert hcp["fieldmap"][1]["magnitude"] == magnitude
    assert hcp["fieldmap"][1]["phase"] == phase


def test_xtract_hands_on_its_tract_list_with_the_flag_xtract_reads(tmp_path):
    """`-list` is not an option of xtract, it wants `-tract_list`."""
    sinfo, sessionsfolder = build_hcp_session(str(tmp_path))
    options = default_options(
        run="test",
        sessionsfolder=sessionsfolder,
        comlogs=str(tmp_path / "comlogs"),
        xtract_list="vof_r,vof_l",
    )

    log = dwi_xtract(sinfo, options)

    assert " -tract_list vof_r,vof_l" in log.text
    assert " -list " not in log.text
