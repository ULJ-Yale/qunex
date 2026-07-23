#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``paths_hcp.py``

Resolution of the HCP folder structure and per-session file paths
shared by all HCP processing commands.
"""

import glob
import os
import os.path
import re

import qx_utilities.general.exceptions as ge


unwarp = {
    None: "Unknown",
    "i": "x",
    "j": "y",
    "k": "z",
    "i-": "x-",
    "j-": "y-",
    "k-": "z-",
}


pe_dir_map = {
    "AP": "j-",
    "j-": "AP",
    "PA": "j",
    "j": "PA",
    "RL": "i",
    "i": "RL",
    "LR": "i-",
    "i-": "LR",
}


se_dir_map = {"AP": "y", "PA": "y", "LR": "x", "RL": "x"}


def get_hcp_paths(sinfo, options):
    """
    Build the dictionary of HCP folder and file paths for a session.

    Resolves the HCP Pipelines locations, the session's hcp working folders and
    the expected structural / functional file names from ``sinfo`` and the given
    ``options``.

    Parameters:
        sinfo (dict): session information; ``id`` and ``hcp`` are used.
        options (dict): command options controlling the folder structure and
            file naming.

    Returns:
        dict: mapping of path keys (e.g. ``base``, ``T1w_folder``,
        ``hcp_nonlin``) to absolute paths for this session.
    """
    d = {}

    # ---- HCP Pipeline folders

    # set location of HCP Pipelines
    options["hcp_pipeline"] = os.environ["HCPPIPEDIR"]

    base = options["hcp_pipeline"]

    d["hcp_base"] = base

    d["hcp_Templates"] = os.path.join(base, "global", "templates")
    d["hcp_Bin"] = os.path.join(base, "global", "binaries")
    d["hcp_Config"] = os.path.join(base, "global", "config")

    d["hcp_PreFS"] = os.path.join(base, "PreFreeSurfer", "scripts")
    d["hcp_FS"] = os.path.join(base, "FreeSurfer", "scripts")
    d["hcp_PostFS"] = os.path.join(base, "PostFreeSurfer", "scripts")
    d["hcp_fMRISurf"] = os.path.join(base, "fMRISurface", "scripts")
    d["hcp_fMRIVol"] = os.path.join(base, "fMRIVolume", "scripts")
    d["hcp_tfMRI"] = os.path.join(base, "tfMRI", "scripts")
    d["hcp_dMRI"] = os.path.join(base, "DiffusionPreprocessing", "scripts")
    d["hcp_Global"] = os.path.join(base, "global", "scripts")
    d["hcp_tfMRIANalysis"] = os.path.join(base, "TaskfMRIAnalysis", "scripts")

    d["hcp_caret7dir"] = os.path.join(
        base, "global", "binaries", "caret7", "bin_rh_linux64"
    )

    # ---- Key folder in the hcp folder structure
    if "hcp" in sinfo:
        hcpbase = os.path.join(sinfo["hcp"], sinfo["id"] + options["hcp_suffix"])
    else:
        print(
            "ERROR: HCP path does not exists, check your parameters and the batch file!"
        )
        raise ge.CommandFailed(
            options["command_ran"],
            "No sufficient input data, perhaps you did not provide the batch file?",
        )

    d["base"] = hcpbase
    if options["hcp_folderstructure"] == "hcpya":
        d["source"] = d["base"]
    else:
        d["source"] = os.path.join(d["base"], "unprocessed")

    d["snapshots"] = os.path.join(hcpbase, "snapshots")
    d["hcp_nonlin"] = os.path.join(hcpbase, "MNINonLinear")
    d["T1w_source"] = os.path.join(d["source"], "T1w")
    d["T2w_source"] = os.path.join(d["source"], "T2w")
    d["DWI_source"] = os.path.join(d["source"], "Diffusion")
    d["ASL_source"] = os.path.join(d["source"], "ASL")

    d["T1w_folder"] = os.path.join(hcpbase, "T1w")
    d["DWI_folder"] = os.path.join(hcpbase, "Diffusion")
    d["FS_folder"] = os.path.join(hcpbase, "T1w", sinfo["id"] + options["hcp_suffix"])

    # T1w file
    try:
        t1w = [v for (k, v) in sinfo.items() if k.isdigit() and v["name"] == "T1w"][0]
        filename = t1w.get("filename", None)
        if filename and options["hcp_filename"] == "userdefined":
            d["T1w"] = "@".join(
                glob.glob(
                    os.path.join(
                        d["T1w_source"], sinfo["id"] + "*" + filename + "*.nii.gz"
                    )
                )
            )
        else:
            d["T1w"] = "@".join(
                glob.glob(
                    os.path.join(d["T1w_source"], sinfo["id"] + "*T1w_MPR*.nii.gz")
                )
            )

        # raw_psn_t1w and # raw_nopsn_t1w
        if filename:
            d["hcp_raw_psn_t1w"] = os.path.join(
                d["source"],
                filename,
                "OTHER_FILES",
                f"{sinfo['id']}_T1w_MPR_vNav_Norm_4e_RMS.nii.gz",
            )
            d["hcp_raw_nopsn_t1w"] = os.path.join(
                d["source"],
                filename,
                "T1w_MPR_vNav_4e_e1e2_mean",
                f"{sinfo['id']}_T1w_MPR_vNav_4e_e1e2_mean.nii.gz",
            )
        else:
            d["hcp_raw_psn_t1w"] = os.path.join(
                d["source"],
                "T1w",
                "OTHER_FILES",
                f"{sinfo['id']}_T1w_MPR_vNav_Norm_4e_RMS.nii.gz",
            )
            d["hcp_raw_nopsn_t1w"] = os.path.join(
                d["source"],
                "T1w",
                "T1w_MPR_vNav_4e_e1e2_mean",
                f"{sinfo['id']}_T1w_MPR_vNav_4e_e1e2_mean.nii.gz",
            )
    except Exception:
        d["T1w"] = "NONE"

    # --- T2w related paths
    if options["hcp_t2"] == "NONE":
        d["T2w"] = "NONE"
    else:
        try:
            t2w = [v for (k, v) in sinfo.items() if k.isdigit() and v["name"] == "T2w"][
                0
            ]
            filename = t2w.get("filename", None)
            if filename and options["hcp_filename"] == "userdefined":
                d["T2w"] = "@".join(
                    glob.glob(
                        os.path.join(
                            d["source"],
                            "T2w",
                            sinfo["id"] + "*" + filename + "*.nii.gz",
                        )
                    )
                )
            else:
                d["T2w"] = "@".join(
                    glob.glob(
                        os.path.join(d["T2w_source"], sinfo["id"] + "_T2w_SPC*.nii.gz")
                    )
                )
        except Exception:
            d["T2w"] = "NONE"

    # --- Fieldmap related paths
    d["fieldmap"] = {}
    dc = False
    legacy_dc = False
    if options["hcp_avgrdcmethod"] is not None:
        if options["hcp_avgrdcmethod"].lower() in [
            "fieldmap",
            "siemensfieldmap",
            "philipsfieldmap",
            "gehealthcarefieldmap",
        ]:
            dc = True
        elif options["hcp_avgrdcmethod"].lower() == "gehealthcarelegacyfieldmap":
            legacy_dc = True
    real_dc = False
    if options["hcp_bold_dcmethod"] is not None:
        if options["hcp_bold_dcmethod"].lower() in [
            "fieldmap",
            "siemensfieldmap",
            "philipsfieldmap",
        ]:
            dc = True
        elif options["hcp_bold_dcmethod"].lower() == "gehealthcarelegacyfieldmap":
            legacy_dc = True
        elif options["hcp_bold_dcmethod"].lower() in [
            "precomputed_fieldmap",
        ]:
            real_dc = True

    if dc:
        fmapmag = glob.glob(
            os.path.join(
                d["source"],
                "FieldMap*" + options["fmtail"],
                sinfo["id"] + options["fmtail"] + "*_FieldMap_Magnitude*.nii.gz",
            )
        )
        for fmap in fmapmag:
            fmnum = re.search(r"(?<=FieldMap)[0-9]{1,2}", fmap)
            if fmnum:
                fmnum = int(fmnum.group())
                if fmnum not in d["fieldmap"]:
                    d["fieldmap"].update({fmnum: {"magnitude": fmap}})
                else:
                    existing = d["fieldmap"][fmnum]["magnitude"]
                    d["fieldmap"].update({fmnum: {"magnitude": [fmap, existing]}})

                    # check if too many magnitudes
                    if len(d["fieldmap"][fmnum]["magnitude"]) > 2:
                        print("ERROR: Found more than two FM-Magnitude files!")
                        raise ge.CommandFailed(
                            options["command_ran"],
                            "Too many FM-Magnitude files found!",
                        )

        fmapphase = glob.glob(
            os.path.join(
                d["source"],
                "FieldMap*" + options["fmtail"],
                sinfo["id"] + options["fmtail"] + "*_FieldMap_Phase.nii.gz",
            )
        )
        for imagepath in fmapphase:
            fmnum = re.search(r"(?<=FieldMap)[0-9]{1,2}", imagepath)
            if fmnum:
                fmnum = int(fmnum.group())
                if fmnum in d["fieldmap"]:
                    d["fieldmap"][fmnum].update({"phase": imagepath})

    elif legacy_dc:
        fmapge = glob.glob(
            os.path.join(
                d["source"],
                "FieldMap*" + options["fmtail"],
                sinfo["id"] + options["fmtail"] + "*_FieldMap_GE.nii.gz",
            )
        )
        for imagepath in fmapge:
            fmnum = re.search(r"(?<=FieldMap)[0-9]{1,2}", imagepath)
            if fmnum:
                fmnum = int(fmnum.group())
                d["fieldmap"].update({fmnum: {"GE": imagepath}})

    if real_dc:
        fmapreal = glob.glob(
            os.path.join(
                d["source"],
                "FieldMap*" + options["fmtail"],
                sinfo["id"] + options["fmtail"] + "*_FieldMap_Real.nii.gz",
            )
        )
        for imagepath in fmapreal:
            fmnum = re.search(r"(?<=FieldMap)[0-9]{1,2}", imagepath)
            if fmnum:
                fmnum = int(fmnum.group())
                if fmnum not in d["fieldmap"]:
                    d["fieldmap"].update({fmnum: {"Real": imagepath}})
                else:
                    d["fieldmap"][fmnum].update({"Real": imagepath})

        fmapmag_real = glob.glob(
            os.path.join(
                d["source"],
                "FieldMap*" + options["fmtail"],
                sinfo["id"] + options["fmtail"] + "*_FieldMap_Magnitude*.nii.gz",
            )
        )
        for imagepath in fmapmag_real:
            fmnum = re.search(r"(?<=FieldMap)[0-9]{1,2}", imagepath)
            if fmnum:
                fmnum = int(fmnum.group())
                if fmnum not in d["fieldmap"]:
                    d["fieldmap"].update({fmnum: {"Magnitude": imagepath}})
                else:
                    d["fieldmap"][fmnum].update({"Magnitude": imagepath})

    # B1tx/TB1TFL phase and mag
    tb1tlf_magnitude = glob.glob(
        os.path.join(d["source"], "B1", sinfo["id"] + "*_TB1TFL-Magnitude.nii.gz")
    )
    if len(tb1tlf_magnitude) != 0:
        d["TB1TFL-Magnitude"] = tb1tlf_magnitude[0]
    else:
        tb1tlf_magnitude = glob.glob(
            os.path.join(d["T1w_source"], sinfo["id"] + "*_TB1TFL-Magnitude.nii.gz")
        )
        if len(tb1tlf_magnitude) != 0:
            d["TB1TFL-Magnitude"] = tb1tlf_magnitude[0]

    tb1tlf_phase = glob.glob(
        os.path.join(d["source"], "B1", sinfo["id"] + "*_TB1TFL-Phase.nii.gz")
    )
    if len(tb1tlf_phase) != 0:
        d["TB1TFL-Phase"] = tb1tlf_phase[0]
    else:
        tb1tlf_phase = glob.glob(
            os.path.join(d["T1w_source"], sinfo["id"] + "*_TB1TFL-Phase.nii.gz")
        )
        if len(tb1tlf_phase) != 0:
            d["TB1TFL-Phase"] = tb1tlf_phase[0]

    # AFI
    t1w_afi = glob.glob(os.path.join(d["source"], "B1", sinfo["id"] + "*AFI.nii.gz"))
    if len(t1w_afi) != 0:
        d["T1w-AFI"] = t1w_afi[0]
    else:
        t1w_afi = glob.glob(os.path.join(d["T1w_source"], sinfo["id"] + "*AFI.nii.gz"))
        if len(t1w_afi) != 0:
            d["T1w-AFI"] = t1w_afi[0]

    rb1cor_32ch = glob.glob(
        os.path.join(d["source"], "B1", sinfo["id"] + "*_*CH.nii.gz")
    )
    rb1cor_head = glob.glob(
        os.path.join(d["source"], "B1", sinfo["id"] + "*-Head.nii.gz")
    )
    if len(rb1cor_32ch) != 0:
        d["RB1COR-Head"] = rb1cor_32ch[0]
    elif len(rb1cor_head) != 0:
        d["RB1COR-Head"] = rb1cor_head[0]
    else:
        rb1cor_32ch = glob.glob(
            os.path.join(d["T1w_source"], sinfo["id"] + "*_*CH.nii.gz")
        )
        if len(rb1cor_32ch) != 0:
            d["RB1COR-Head"] = rb1cor_32ch[0]
        else:
            rb1cor_head = glob.glob(
                os.path.join(d["T1w_source"], sinfo["id"] + "*-Head.nii.gz")
            )
            if len(rb1cor_head) != 0:
                d["RB1COR-Head"] = rb1cor_head[0]

    rb1cor_bc = glob.glob(os.path.join(d["source"], "B1", sinfo["id"] + "*_BC.nii.gz"))
    rb1cor_body = glob.glob(
        os.path.join(d["source"], "B1", sinfo["id"] + "*-Body.nii.gz")
    )
    if len(rb1cor_bc) != 0:
        d["RB1COR-Body"] = rb1cor_bc[0]
    elif len(rb1cor_body) != 0:
        d["RB1COR-Body"] = rb1cor_body[0]
    else:
        rb1cor_bc = glob.glob(
            os.path.join(d["T1w_source"], sinfo["id"] + "*_BC.nii.gz")
        )
        if len(rb1cor_bc) != 0:
            d["RB1COR-Body"] = rb1cor_bc[0]
        else:
            rb1cor_body = glob.glob(
                os.path.join(d["T1w_source"], sinfo["id"] + "*-Body.nii.gz")
            )
            if len(rb1cor_body) != 0:
                d["RB1COR-Body"] = rb1cor_body[0]

    # --- default check files
    for pipe, default in [
        ("hcp_prefs_check", "check_PreFreeSurfer.txt"),
        ("hcp_fs_check", "check_FreeSurfer.txt"),
        ("hcp_postfs_check", "check_PostFreeSurfer.txt"),
        ("hcp_bold_vol_check", "check_fMRIVolume.txt"),
        ("hcp_bold_surf_check", "check_fMRISurface.txt"),
        ("hcp_dwi_check", "check_Diffusion.txt"),
    ]:
        if options[pipe] == "all":
            d[pipe] = os.path.join(options["sessionsfolder"], "specs", default)
        elif options[pipe] == "last":
            d[pipe] = False
        else:
            d[pipe] = options[pipe]

    return d
