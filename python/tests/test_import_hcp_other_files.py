# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Field maps kept in an HCPLS acquisition's OTHER_FILES subfolder are mapped."""

import json
import os

import qx_utilities.hcp.import_hcp as ih
from qx_utilities.general.log import ReportLog

SESSION = "HCA0000000_V1_MR"


def _image(folder, name, info=None):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, f"{SESSION}_{name}.nii.gz"), "w") as f:
        f.write(name)
    with open(os.path.join(folder, f"{SESSION}_{name}.json"), "w") as f:
        json.dump(info or {}, f)


def _hcpls(root):
    """An HCP Lifespan style session, with the Diffusion SE pair in OTHER_FILES."""
    hcpls = os.path.join(root, SESSION, "hcpls")

    t1w = os.path.join(hcpls, "T1w_MPR_vNav_4e_RMS")
    _image(t1w, "SpinEchoFieldMap1_AP", {"PhaseEncodingDirection": "j-"})
    _image(t1w, "SpinEchoFieldMap1_PA", {"PhaseEncodingDirection": "j"})
    _image(t1w, "T1w_MPR_vNav_4e_RMS")
    # neither a field map nor the T1w named by the folder, never mapped
    _image(os.path.join(t1w, "OTHER_FILES"), "T1w_MPR_vNav_Norm_4e_RMS")
    _image(os.path.join(t1w, "OTHER_FILES"), "SpinEchoFieldMap9_AP")

    dwi = os.path.join(hcpls, "Diffusion")
    for phenc in ("AP", "PA"):
        _image(dwi, f"dMRI_dir98_{phenc}")
        for ext in ("bval", "bvec"):
            with open(
                os.path.join(dwi, f"{SESSION}_dMRI_dir98_{phenc}.{ext}"), "w"
            ) as f:
                f.write("0\n")
        _image(dwi, f"dMRI_dir98_{phenc}_SBRef")
        _image(
            os.path.join(dwi, "OTHER_FILES"),
            f"SpinEchoFieldMap4_{phenc}",
            {"PhaseEncodingDirection": "j-" if phenc == "AP" else "j"},
        )
    return hcpls


def test_process_hcpls_takes_field_maps_from_other_files(tmp_path):
    hcpls = _hcpls(str(tmp_path))

    folders = {
        f["name"]: f for f in ih.process_hcpls(hcpls, "type_se", _log=ReportLog())
    }

    diffusion = folders["Diffusion"]
    assert diffusion["senum"] == 4
    assert [e["name"] for e in diffusion["folderFiles"]] == [
        f"{SESSION}_SpinEchoFieldMap4_AP.nii.gz",
        f"{SESSION}_SpinEchoFieldMap4_PA.nii.gz",
        f"{SESSION}_dMRI_dir98_AP.nii.gz",
        f"{SESSION}_dMRI_dir98_AP_SBRef.nii.gz",
        f"{SESSION}_dMRI_dir98_PA.nii.gz",
        f"{SESSION}_dMRI_dir98_PA_SBRef.nii.gz",
    ]
    assert all(
        os.path.basename(os.path.dirname(e["path"])) == "OTHER_FILES"
        for e in diffusion["folderFiles"][:2]
    )

    # the root holds field maps, so OTHER_FILES is not looked into
    t1w = folders["T1w_MPR_vNav_4e_RMS"]
    assert t1w["senum"] == 1
    assert [e["name"] for e in t1w["folderFiles"]] == [
        f"{SESSION}_SpinEchoFieldMap1_AP.nii.gz",
        f"{SESSION}_SpinEchoFieldMap1_PA.nii.gz",
        f"{SESSION}_T1w_MPR_vNav_4e_RMS.nii.gz",
    ]


def test_map_hcpls2nii_lists_the_other_files_field_maps(tmp_path):
    hcpls = _hcpls(str(tmp_path))

    nimg, nmapped = ih.map_hcpls2nii(os.path.dirname(hcpls), _log=ReportLog())

    assert (nimg, nmapped) == (9, 9)
    with open(os.path.join(os.path.dirname(hcpls), "session.txt")) as f:
        lines = [e for e in f.read().splitlines() if e[:2].isdigit()]
    assert [e.split(":")[1].strip() for e in lines] == [
        "SE-FM-AP",
        "SE-FM-PA",
        "T1w",
        "SE-FM-AP",
        "SE-FM-PA",
        "DWI",
        "DWIref",
        "DWI",
        "DWIref",
    ]
    assert "se(4)" in lines[3] and "se(4)" in lines[4]
