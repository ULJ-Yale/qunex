#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``process_hcp.py``

This file holds code for running HCP preprocessing pipelines.
"""

"""
Copyright (c) Grega Repovs and Jure Demsar.
All rights reserved.
"""

import concurrent.futures
import glob
import json
import os
import os.path
import pprint
import re
import shutil
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from functools import partial

import general.core as gc
import general.exceptions as ge
import general.snapshots as gs
import nibabel as nib
import processing.core as pc

unwarp = {
    None: "Unknown",
    "i": "x",
    "j": "y",
    "k": "z",
    "i-": "x-",
    "j-": "y-",
    "k-": "z-",
}
PEDirMap = {
    "AP": "j-",
    "j-": "AP",
    "PA": "j",
    "j": "PA",
    "RL": "i",
    "i": "RL",
    "LR": "i-",
    "i-": "LR",
}
SEDirMap = {"AP": "y", "PA": "y", "LR": "x", "RL": "x"}

# ------------------------------------------------------------------------------
#                                                              Support functions


def _build_skipped_report(report, skipped, options):
    """
    Function builds the skipped report based on the skipped list and the
    hcp_filename option setting.
    """
    if report["boldskipped"]:
        if options["hcp_filename"] == "userdefined":
            report["skipped"] = [
                binfo.get("filename", str(binfo["bold_number"])) for binfo in skipped
            ]
        else:
            report["skipped"] = [str(binfo["bold_number"]) for binfo in skipped]


def _append_sorted_logdir_to_log(log_file, logdir):
    """Append the contents of all files in a log directory into a single log.

    Files are listed in a consistent order:
    - first by increasing integer N in filenames matching '*.N.{e,o}.log'
    - then with '.e.log' preceding '.o.log' for the same N
    - any non-matching files are appended last in lexicographic order

    Parameters:
        log_file: open file handle to write to.
        logdir (str): directory with log files to append.
    """

    def _log_sort_key(filename):
        match = re.match(
            r"^(?P<prefix>.*)\.(?P<n>\d+)\.(?P<stream>[eo])\.log$", filename
        )
        if not match:
            return (float("inf"), 2, filename)

        n = int(match.group("n"))
        stream = match.group("stream")
        stream_order = 0 if stream == "e" else 1
        return (n, stream_order, filename)

    try:
        filenames = [entry.name for entry in os.scandir(logdir) if entry.is_file()]
    except FileNotFoundError:
        print(f"\n---> WARNING: log directory not found: {logdir}", file=log_file)
        return

    for filename in sorted(filenames, key=_log_sort_key):
        file_path = os.path.join(logdir, filename)
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                content = file.read()
        except OSError as err:
            content = f"[Could not read {file_path}: {err}]"

        print(file=log_file)
        print("----------------------------------------", file=log_file)
        print(f"Contents of {filename}:", file=log_file)
        print("----------------------------------------", file=log_file)
        print(content, file=log_file)


# -------------------------------------------------------------------
#
#                       HCP Pipeline Scripts
#


def getHCPPaths(sinfo, options):
    """
    getHCPPaths - documentation not yet available.
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
        T1w = [v for (k, v) in sinfo.items() if k.isdigit() and v["name"] == "T1w"][0]
        filename = T1w.get("filename", None)
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
    except:
        d["T1w"] = "NONE"

    # --- T2w related paths
    if options["hcp_t2"] == "NONE":
        d["T2w"] = "NONE"
    else:
        try:
            T2w = [v for (k, v) in sinfo.items() if k.isdigit() and v["name"] == "T2w"][
                0
            ]
            filename = T2w.get("filename", None)
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
        except:
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


def doHCPOptionsCheck(options, command):
    if options["hcp_folderstructure"] not in ["hcpya", "hcpls"]:
        raise ge.CommandFailed(
            command,
            "Unknown HCP folder structure version",
            "The specified HCP folder structure version is unknown: %s"
            % (options["hcp_folderstructure"]),
            "Please check the 'hcp_folderstructure' parameter!",
        )

    if options["hcp_folderstructure"] == "hcpya":
        options["fctail"] = "_fncb"
        options["fmtail"] = "_strc"
    else:
        options["fctail"] = ""
        options["fmtail"] = ""


def checkInlineParameterUse(modality, parameter, options):
    return any(
        [
            e in options["use_sequence_info"]
            for e in [
                "all",
                parameter,
                "%s:all" % (modality),
                "%s:%s" % (modality, parameter),
            ]
        ]
    )


def check_gdc_coeff_file(gdcstring, hcp, sinfo, r="", run=True):
    """
    Function that extract the information on the correct gdc file to be used and tests for its presence;
    """

    if gdcstring not in ["", "NONE"]:
        if any([e in gdcstring for e in ["|", "default"]]):
            try:
                try:
                    device = {}
                    dmanufacturer, dmodel, dserial = [
                        e.strip() for e in sinfo.get("device", "NA|NA|NA").split("|")
                    ]
                    device["manufacturer"] = dmanufacturer
                    device["model"] = dmodel
                    device["serial"] = dserial
                except:
                    r += (
                        "\n---> WARNING: device information for this session is malformed: %s"
                        % (sinfo.get("device", "---"))
                    )
                    raise

                gdcoptions = [
                    [ee.strip() for ee in e.strip().split(":")]
                    for e in gdcstring.split("|")
                ]
                gdcfile = [e[1] for e in gdcoptions if e[0] == "default"][0]
                gdcfileused = "default"

                for ginfo, gwhat, gfile in [e for e in gdcoptions if e[0] != "default"]:
                    if ginfo in device:
                        if device[ginfo] == gwhat:
                            gdcfile = gfile
                            gdcfileused = "%s: %s" % (ginfo, gwhat)
                            break
                    if ginfo in sinfo:
                        if sinfo[ginfo] == gwhat:
                            gdcfile = gfile
                            gdcfileused = "%s: %s" % (ginfo, gwhat)
                            break
            except:
                r += "\n---> ERROR: malformed specification of gdcoeffs: %s!" % (
                    gdcstring
                )
                run = False
                raise

            if gdcfile in ["", "NONE"]:
                r += "\n---> WARNING: Specific gradient distortion coefficients file could not be identified! None will be used."
                gdcfile = "NONE"
            else:
                r += (
                    "\n---> Specific gradient distortion coefficients file identified (%s):\n     %s"
                    % (gdcfileused, gdcfile)
                )

        else:
            gdcfile = gdcstring

        if gdcfile not in ["", "NONE"]:
            if not os.path.exists(gdcfile):
                gdcoeffs = os.path.join(hcp["hcp_Config"], gdcfile)
                if not os.path.exists(gdcoeffs):
                    r += (
                        "\n---> ERROR: Could not find gradient distortion coefficients file: %s."
                        % (gdcfile)
                    )
                    run = False
                else:
                    r += "\n---> Gradient distortion coefficients file present."
            else:
                r += "\n---> Gradient distortion coefficients file present."
    else:
        gdcfile = "NONE"

    return gdcfile, r, run


def hcp_pre_freesurfer(sinfo, options, overwrite=False, thread=0):
    r"""
    ``hcp_pre_freesurfer [... processing options]``

    Runs the pre-FS step of the HCP Pipeline (PreFreeSurferPipeline.sh).

    Warning:
        The code expects the input images to be named and present in the
        specific folder structure. Specifically it will look within the
        folder::

            <session id>/hcp/<session id>

        for folders and files::

            T1w/\*T1w_MPR[N]\*
            T2w/\*T2w_MPR[N]\*

        There has to be at least one T1w image present. If there are more than
        one T1w or T2w images, they will all be used and averaged together.

        Depending on the type of distortion correction method specified by the
        `--hcp_avgrdcmethod` argument (see below), it will also expect the
        presence of the following files:

        **TOPUP**::

            SpinEchoFieldMap[N]\*/\*_<hcp_sephasepos>_\*
            SpinEchoFieldMap[N]\*/\*_<hcp_sephaseneg>_\*

        **SiemensFieldMap, GEHealthCareFieldMap or PhilipsFieldMap**::

            FieldMap/<session id>_FieldMap_Magnitude.nii.gz
            FieldMap/<session id>_FieldMap_Phase.nii.gz

        **GEHealthCareLegacyFieldMap**::

            FieldMap/<session id>_FieldMap_GE.nii.gz

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_processing_mode (str, default 'HCPStyleData'):
            Controls whether the HCP acquisition and processing guidelines
            should be treated as requirements ('HCPStyleData') or if additional
            processing functionality is allowed ('LegacyStyleData'). In this
            case running processing w/o a T2w image.

        --hcp_folderstructure (str, default 'hcpls'):
            If set to 'hcpya' the folder structure used in the initial HCP
            Young Adults study is used. Specifically, the source files are
            stored in individual folders within the main 'hcp' folder in
            parallel with the working folders and the 'MNINonLinear' folder
            with results. If set to 'hcpls' the folder structure used in the
            HCP Life Span study is used. Specifically, the source files are
            all stored within their individual subfolders located in the joint
            'unprocessed' folder in the main 'hcp' folder, parallel to the
            working folders and the 'MNINonLinear' folder.

        --hcp_filename (str, default 'automated'):
            How to name the BOLD files once mapped into the hcp input folder
            structure. The default ('automated') will automatically name each
            file by their number (e.g. BOLD_1). The alternative ('userdefined')
            is to use the file names, which can be defined by the user prior to
            mapping (e.g. rfMRI_REST1_AP).

        --hcp_t2 (str, default 't2'):
            'NONE' if no T2w image is available and the preprocessing should be
            run without them, anything else otherwise [t2]. 'NONE' is only valid
            if 'LegacyStyleData' processing mode was specified.

        --hcp_brainsize (int, default 150):
             Specifies the size of the brain in mm. 170 is FSL default and seems
             to be a good choice, HCP uses 150, which can lead to problems with
             larger heads.

        --hcp_t1samplespacing (str, default 'NONE'):
            T1 image sample spacing, 'NONE' if not used.

        --hcp_t2samplespacing (str, default 'NONE'):
            T2 image sample spacing, 'NONE' if not used.

        --hcp_gdcoeffs (str, default 'NONE):
            Path to a file containing gradient distortion coefficients,
            alternatively a string describing multiple options (see below), or
            "NONE", if not used.

        --hcp_bfsigma (str, default ''):
            Bias Field Smoothing Sigma (optional).

        --hcp_avgrdcmethod (str):
            Averaging and readout distortion correction method.
            Can take the following values:

            - 'NONE' (average any repeats with no readout correction)
            - 'FIELDMAP' (average any repeats and use Siemens field map for
              readout correction)
            - 'SiemensFieldMap' (average any repeats and use Siemens field map
              for readout correction)
            - 'GEHealthCareFieldMap' (average any repeats and use GE field
              map for readout correction)
            - 'GEHealthCareLegacyFieldMap' (average any repeats and use GE field
              map for readout correction, for legacy, combined GE field maps)
            - 'PhilipsFieldMap' (average any repeats and use Philips field map
              for readout correction)
            - 'TOPUP' (average any repeats and use spin echo field map for
              readout correction).

        --hcp_unwarpdir (str, default 'z'):
            Readout direction of the T1w and T2w images (x, y, z or NONE); used
            with either a regular field map or a spin echo field map.

        --hcp_echodiff (str):
            Difference in TE times if a fieldmap image is used, set to NONE if
            not used.

        --hcp_seechospacing (str, default ''):
            Echo Spacing or of Spin Echo Field Maps in seconds or "NONE" if not
            used.

        --hcp_sephasepos (str, default ''):
            Label for the positive image of the Spin Echo Field Map pair.

        --hcp_sephaseneg (str, default ''):
            Label for the negative image of the Spin Echo Field Map pair.

        --hcp_senum (str, default ''):
            Number of the Spin Echo Field Map pair to use, will be set
            automatically based on the batch/session file. If set, QuNex will
            use the files in the SpinEchoFieldMap[N] folder from the HCP
            unprocessed folder.

        --hcp_seunwarpdir (str, default ''):
            Phase encoding direction of the Spin Echo Field Map (x, y or NONE).

        --hcp_topupconfig (str, default 'NONE'):
            Path to a configuration file for TOPUP method or "NONE" if not used.

        --hcp_prefs_custombrain (str, default 'NONE'):
            Whether to only run the final registration using either a custom
            prepared brain mask (MASK) or custom prepared brain images
            (CUSTOM), or to run the full set of processing steps (NONE).
            If a mask is to be used (MASK) then a
            `"custom_acpc_dc_restore_mask.nii.gz"` image needs to be placed in
            the `<session>/T1w` folder. If a custom brain is to be used
            (BRAIN), then the following images in `<session>/T1w` folder need
            to be adjusted:

            - `T1w_acpc_dc_restore_brain.nii.gz`
            - `T1w_acpc_dc_restore.nii.gz`
            - `T2w_acpc_dc_restore_brain.nii.gz`
            - `T2w_acpc_dc_restore.nii.gz`.

        --hcp_prefs_template_res (float, default set from imaging data):
            The resolution (in mm) of the structural images templates to use in
            the preFS step. Note: it should match the resolution of the
            acquired structural images. If no value is provided, QuNex will try
            to use the imaging data to set a sensible default value. It will
            notify you about which setting it used, you should pay attention to
            this piece of information and manually overwrite the default if
            something is off.

        --hcp_prefs_t1template (str):
            Path to the T1 template to be used by PreFreeSurfer. By default the
            used template is determined through the resolution provided by the
            hcp_prefs_template_res parameter.

        --hcp_prefs_t1templatebrain (str):
            Path to the T1 brain template to be used by PreFreeSurfer. By
            default the used template is determined through the resolution
            provided by the hcp_prefs_template_res parameter.

        --hcp_prefs_t1template2mm (str):
            Path to the T1 2mm template to be used by PreFreeSurfer. By default
            the used template is HCP's MNI152_T1_2mm.nii.gz.

        --hcp_prefs_t2template (str):
            Path to the T2 template to be used by PreFreeSurfer. By default the
            used template is determined through the resolution provided by the
            hcp_prefs_template_res parameter.

        --hcp_prefs_t2templatebrain (str):
            Path to the T2 brain template to be used by PreFreeSurfer. By
            default the used template is determined through the resolution
            provided by the hcp_prefs_template_res parameter.

        --hcp_prefs_t2template2mm (str):
            Path to the T2 2mm template to be used by PreFreeSurfer. By default
            the used template is HCP's MNI152_T2_2mm.nii.gz.

        --hcp_prefs_templatemask (str):
            Path to the template mask to be used by PreFreeSurfer. By default
            the used template mask is determined through the resolution provided
            by the hcp_prefs_template_res parameter.

        --hcp_prefs_template2mmmask (str):
            Path to the template mask to be used by PreFreeSurfer. By default
            the used 2mm template mask is HCP's
            MNI152_T1_2mm_brain_mask_dil.nii.gz.

        --hcp_prefs_fnirtconfig (str):
            Path to the used FNIRT config. Set to the HCP's T1_2_MNI152_2mm.cnf
            by default.

        --use_sequence_info (str, default 'all'):
            A pipe, comma or space separated list of inline sequence information
            to use in preprocessing of specific image modalities.

            Example specifications:

            - `all`: use all present inline information for all modalities,
            - 'DwellTime': use DwellTime information for all modalities,
            - `T1w:all`: use all present inline information for T1w modality,
            - `SE:EchoSpacing`: use EchoSpacing information for Spin-Echo
              fieldmap images.
            - `none`: do not use inline information

            Modalities: T1w, T2w, SE, BOLD, dMRi Inline information: TR,
            PEDirection, EchoSpacing DwellTime, ReadoutDirection.

            If information is not specified it will not be used. More general
            specification (e.g. `all`) implies all more specific cases (e.g.
            `T1w:all`).

        --hcp_sephasepos2 (str, default ''):
            Label for the positive image of the second Spin Echo Field Map pair.

        --hcp_sephaseneg2 (str, default ''):
            Label for the negative image of the second Spin Echo Field Map pair.

        --hcp_senum2 (str, default ''):
            Number of the second Spin Echo Field Map pair to use. QuNex will
            use the files in the SpinEchoFieldMap[N] folder from the HCP
            unprocessed folder.

        --hcp_species (str, default ''):
            Species (default: Human).

        --hcp_runmode (str, default ''):
            Specify from which step to resume the processing instead of
            starting from the beginning. Value must be one of: Default,
            ACPCAlignment, BrainExtraction, T2wToT1wRegAndBiasCorrection,
            AtlasRegistration (default: Default).

        --hcp_truepatientposition (str, default ''):
            True patient position (default: HFS).

        --hcp_scannerpatientposition (str, default ''):
            Scanner patient position (default: HFS).

        --hcp_betcenter (str, default ''):
            Center coordinates for BET (default: 45,55,39).

        --hcp_betradius (str, default ''):
            Radius for BET (default: 75).

        --hcp_betfraction (str, default ''):
            Fraction for BET (default: 0.3).

        --hcp_bettop2center (str, default ''):
            Distance from top to center for BET (default: 86).

        --hcp_brainextract (str, default ''):
            Brain extraction method (default: INVIVO).

        --hcp_use_t2w_phase_zero (str, default ''):
            Indicates whether to add T2-weighted image as a phase zero volume,
            for bright-CSF T2w contrast acquisition types (e.g., not FLAIR).
            Accepted values are 'TRUE' and 'FALSE'.

        --hcp_bias_field_sigma_no_t2w (str, default ''):
            Bias Field Smoothing Sigma for Bias Field Correction using T1w
            image only (only for NHP, default: 20).

        --hcp_betbiasfieldcor (str, default ''):
            Indicates whether to correct bias field for BET (default: FALSE).
            Accepted values are 'TRUE' and 'FALSE'.

    Output files:
        The results of this step will be present in the above mentioned T1w
        and T2w folders as well as MNINonLinear folder generated and
        populated in the same sessions's root hcp folder.

    Notes:
        Gradient coefficient file specification:
            ``--hcp_gdcoeffs`` parameter can be set to either 'NONE', a path to
            a specific file to use, or a string that describes, which file to
            use in which case. Each option of the string has to be divided by a
            pipe '|' character and it has to specify, which information to look
            up, a possible value, and a file to use in that case, separated by
            a colon ':' character. The information too look up needs to be
            present in the description of that session. Standard options are
            e.g.::

                institution: Yale
                device: Siemens|Prisma|123456

            Where device is formatted as <manufacturer>|<model>|<serial number>.

            If specifying a string it also has to include a `default` option,
            which will be used in the information was not found. An example
            could be::

                "default:/data/gc1.conf|model:Prisma:/data/gc/Prisma.conf|model:Trio:/data/gc/Trio.conf"

            With the information present above, the file `/data/gc/Prisma.conf`
            would be used.

        hcp_pre_freesurfer parameter mapping:

            =============================== ===========================
            QuNex parameter                 HCPpipelines parameter
            =============================== ===========================
            ``hcp_prefs_t1template``        ``t1template``
            ``hcp_prefs_t1templatebrain``   ``t1templatebrain``
            ``hcp_prefs_t1template2mm``     ``t1template2mm``
            ``hcp_prefs_t2template``        ``t2template``
            ``hcp_prefs_t2templatebrain``   ``t2templatebrain``
            ``hcp_prefs_t2template2mm``     ``t2template2mm``
            ``hcp_prefs_templatemask``      ``templatemask``
            ``hcp_prefs_template2mmmask``   ``template2mmmask``
            ``hcp_brainsize``               ``brainsize``
            ``hcp_prefs_fnirtconfig``       ``fnirtconfig``
            ``hcp_sephaseneg``              ``SEPhaseNeg``
            ``hcp_sephasepos``              ``SEPhasePos``
            ``hcp_seechospacing``           ``seechospacing``
            ``hcp_seunwarpdir``             ``seunwarpdir``
            ``hcp_t1samplespacing``         ``t1samplespacing``
            ``hcp_t2samplespacing``         ``t2samplespacing``
            ``hcp_gdcoeffs``                ``gdcoeffs``
            ``hcp_avgrdcmethod``            ``avgrdcmethod``
            ``hcp_topupconfig``             ``topupconfig``
            ``hcp_bfsigma``                 ``bfsigma``
            ``hcp_prefs_custombrain``       ``custombrain``
            ``hcp_processing_mode``         ``processing-mode``
            ``hcp_sephaseneg2``             ``SEPhaseNeg2``
            ``hcp_sephasepos2``             ``SEPhasePos2``
            ``hcp_species``                 ``species``
            ``hcp_runmode``                 ``runmode``
            ``hcp_truepatientposition``     ``truepatientposition``
            ``hcp_scannerpatientposition``  ``scannerpatientposition``
            ``hcp_betcenter``               ``betcenter``
            ``hcp_betradius``               ``betradius``
            ``hcp_betfraction``             ``betfraction``
            ``hcp_bettop2center``           ``bettop2center``
            ``hcp_brainextract``            ``brainextract``
            ``hcp_use_t2w_phase_zero``      ``use-t2w-phase-zero``
            ``hcp_bias_field_sigma_no_t2w`` ``bias-field-sigma-no-T2w``
            ``hcp_betbiasfieldcor``         ``betbiasfieldcor``
            =============================== ===========================

        Use:
            Runs the PreFreeSurfer step of the HCP Pipeline. It looks for T1w
            and T2w images in sessions's T1w and T2w folder, averages them (if
            multiple present) and linearly and nonlinearly aligns them to the
            MNI atlas. It uses the adjusted version of the HCP that enables the
            preprocessing to run with of without T2w image(s).

    Examples:
        ::

            qunex hcp_pre_freesurfer \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --hcp_brainsize=170

        ::

            qunex hcp_pre_freesurfer \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --hcp_t2=NONE
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP PreFreeSurfer Pipeline [%s] ...\n" % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = "Error"

    try:
        # mandatory check
        if not options["hcp_avgrdcmethod"]:
            raise ge.CommandFailed(
                "hcp_pre_freesurfer",
                "... the hcp_avgrdcmethod parameter needs to be set manually! Since QuNex cannot robustly extract the information needed to set this from the data, you need to set this parameter by yourself.",
            )

        # --- Base settings
        pc.doOptionsCheck(options, sinfo, "hcp_pre_freesurfer")
        doHCPOptionsCheck(options, "hcp_pre_freesurfer")
        hcp = getHCPPaths(sinfo, options)

        # --- run checks
        if "hcp" not in sinfo:
            r += (
                "\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"])
            )
            run = False

        # --- check for T1w and T2w images
        for tfile in hcp["T1w"].split("@"):
            if os.path.exists(tfile):
                r += "\n---> T1w image file present."
                T1w = [
                    v for (k, v) in sinfo.items() if k.isdigit() and v["name"] == "T1w"
                ][0]

                if "DwellTime" in T1w and checkInlineParameterUse(
                    "T1w", "DwellTime", options
                ):
                    options["hcp_t1samplespacing"] = f"{float(T1w['DwellTime']):.10f}"
                    r += (
                        "\n---> T1w image specific EchoSpacing: %s s"
                        % (options["hcp_t1samplespacing"])
                    )
                elif "EchoSpacing" in T1w and checkInlineParameterUse(
                    "T1w", "EchoSpacing", options
                ):
                    options["hcp_t1samplespacing"] = f"{float(T1w['EchoSpacing']):.10f}"
                    r += (
                        "\n---> T1w image specific EchoSpacing: %s s"
                        % (options["hcp_t1samplespacing"])
                    )
                if "UnwarpDir" in T1w and checkInlineParameterUse(
                    "T1w", "UnwarpDir", options
                ):
                    options["hcp_unwarpdir"] = T1w["UnwarpDir"]
                    r += (
                        "\n---> T1w image specific unwarp direction: %s"
                        % (options["hcp_unwarpdir"])
                    )

                # try to set hcp_t1samplespacing from the JSON sidecar if not yet set
                if options["hcp_t1samplespacing"] == "NONE":
                    json_sidecar = tfile.replace("nii.gz", "json")
                    if os.path.exists(json_sidecar):
                        r += "\n---> Trying to set hcp_t1samplespacing from the JSON sidecar."
                        with open(json_sidecar, "r") as file:
                            sidecar_data = json.load(file)
                            if "DwellTime" in sidecar_data:
                                options["hcp_t1samplespacing"] = (
                                    f"{float(sidecar_data['DwellTime']):.10f}"
                                )
                                r += f"\n       - hcp_t1samplespacing set to {options['hcp_t1samplespacing']}"

        if hcp["T2w"] in ["", "NONE"]:
            if options["hcp_processing_mode"] == "HCPStyleData":
                r += "\n---> ERROR: The requested HCP processing mode is 'HCPStyleData', however, no T2w image was specified!\n            Consider using LegacyStyleData processing mode."
                run = False
            else:
                r += "\n---> Not using T2w image."
        else:
            for tfile in hcp["T2w"].split("@"):
                if os.path.exists(tfile):
                    r += "\n---> T2w image file present."
                    T2w = [
                        v
                        for (k, v) in sinfo.items()
                        if k.isdigit() and v["name"] == "T2w"
                    ][0]
                    if "DwellTime" in T2w and checkInlineParameterUse(
                        "T2w", "DwellTime", options
                    ):
                        options["hcp_t2samplespacing"] = (
                            f"{float(T2w['DwellTime']):.10f}"
                        )
                        r += (
                            "\n---> T2w image specific EchoSpacing: %s s"
                            % (options["hcp_t2samplespacing"])
                        )
                    elif "EchoSpacing" in T2w and checkInlineParameterUse(
                        "T2w", "EchoSpacing", options
                    ):
                        options["hcp_t2samplespacing"] = (
                            f"{float(T2w['EchoSpacing']):.10f}"
                        )
                        r += (
                            "\n---> T2w image specific EchoSpacing: %s s"
                            % (options["hcp_t2samplespacing"])
                        )

                    # try to set hcp_t2samplespacing from the JSON sidecar if not yet set
                    if options["hcp_t2samplespacing"] == "NONE":
                        json_sidecar = tfile.replace("nii.gz", "json")
                        if os.path.exists(json_sidecar):
                            r += "\n---> Trying to set hcp_t2samplespacing from the JSON sidecar."
                            with open(json_sidecar, "r") as file:
                                sidecar_data = json.load(file)
                                if "DwellTime" in sidecar_data:
                                    options["hcp_t2samplespacing"] = (
                                        f"{float(sidecar_data['DwellTime']):.10f}"
                                    )
                                    r += f"\n       - hcp_t2samplespacing set to {options['hcp_t2samplespacing']}"

                else:
                    r += "\n---> ERROR: Could not find T2w image file. [%s]" % (tfile)
                    run = False

        # --- do we need spinecho images
        sepos = ""
        seneg = ""
        topupconfig = ""
        senum = None
        tufolder = None
        fmmag = ""
        fmphase = ""
        fmcombined = ""
        echodiff = "NONE"
        if options["hcp_avgrdcmethod"].lower() == "topup":
            try:
                # -- spin echo settings
                T1w = [
                    v for (k, v) in sinfo.items() if k.isdigit() and v["name"] == "T1w"
                ][0]
                senum = T1w.get("se", None)
                # overwrite senum if set
                if options["hcp_senum"]:
                    senum = options["hcp_senum"]
                    r += (
                        "\n---> Overwriting automatically extracted Spin-Echo pair number with a user specified value: %s"
                        % (options["hcp_senum"])
                    )
                if senum:
                    try:
                        senum = int(senum)
                        if senum > 0:
                            tufolder = os.path.join(
                                hcp["source"],
                                "SpinEchoFieldMap%d%s" % (senum, options["fctail"]),
                            )
                            r += (
                                "\n---> TOPUP Correction, Spin-Echo pair %d specified"
                                % (senum)
                            )
                        else:
                            r += (
                                "\n---> ERROR: No Spin-Echo image pair specified for T1w image! [%d]"
                                % (senum)
                            )
                            run = False
                    except:
                        r += (
                            "\n---> ERROR: Could not process the specified Spin-Echo information [%s]! "
                            % (str(senum))
                        )
                        run = False

            except:
                pass

            if senum is None:
                try:
                    tufolder = glob.glob(
                        os.path.join(hcp["source"], "SpinEchoFieldMap*")
                    )[0]
                    senum = int(
                        os.path.basename(tufolder)
                        .replace("SpinEchoFieldMap", "")
                        .replace("_fncb", "")
                    )
                    r += (
                        "\n---> TOPUP Correction, no Spin-Echo pair explicitly specified, using pair %d"
                        % (senum)
                    )
                except:
                    r += (
                        "\n---> ERROR: Could not find folder with files for TOPUP processing of session %s."
                        % (sinfo["id"])
                    )
                    run = False
                    raise

            # try to set hcp_seechospacing from the JSON sidecar if not yet set
            if options["hcp_seechospacing"] is None and tufolder:
                fmap_json = glob.glob(os.path.join(tufolder, "*AP*.json"))
                if len(fmap_json) == 0:
                    fmap_json = glob.glob(os.path.join(tufolder, "*LR*.json"))

                if len(fmap_json) != 0:
                    fmap_json = fmap_json[0]
                    json_sidecar = os.path.join(tufolder, fmap_json)

                    if os.path.exists(json_sidecar):
                        r += "\n---> Trying to set hcp_seechospacing from the JSON sidecar."
                        with open(json_sidecar, "r") as file:
                            sidecar_data = json.load(file)
                            if "EffectiveEchoSpacing" in sidecar_data:
                                options["hcp_seechospacing"] = (
                                    f"{float(sidecar_data['EffectiveEchoSpacing']):.10f}"
                                )
                                r += f"\n       - hcp_seechospacing set to {options['hcp_seechospacing']}"

            # -- spin echo settings
            sesettings = True
            for p in [
                "hcp_sephaseneg",
                "hcp_sephasepos",
            ]:
                if not options[p]:
                    r += f"\nERROR: {p} parameter not set! It needs to be set manually as QuNex cannot infer it from the data in a robust manner."
                    run = False
                    sesettings = False

            try:
                # se phase pos and neg
                # full paths
                if sesettings:
                    if os.path.exists(options["hcp_sephasepos"]) and os.path.exists(
                        options["hcp_sephaseneg"]
                    ):
                        sepos = options["hcp_sephasepos"]
                        seneg = options["hcp_sephaseneg"]
                        r += "\n---> Spin-Echo pair of images present. [%s, %s]" % (
                            os.path.basename(sepos),
                            os.path.basename(seneg),
                        )
                    # labels
                    elif tufolder:
                        sepos = glob.glob(
                            os.path.join(
                                tufolder, "*_" + options["hcp_sephasepos"] + "*.nii.gz"
                            )
                        )[0]
                        seneg = glob.glob(
                            os.path.join(
                                tufolder, "*_" + options["hcp_sephaseneg"] + "*.nii.gz"
                            )
                        )[0]

                        if all([sepos, seneg]):
                            r += "\n---> Spin-Echo pair of images present. [%s]" % (
                                os.path.basename(tufolder)
                            )
                        else:
                            r += (
                                "\n---> ERROR: Could not find the relevant Spin-Echo files! [%s]"
                                % (tufolder)
                            )
                            run = False

                # get SE info from session info
                try:
                    seInfo = [
                        v
                        for (k, v) in sinfo.items()
                        if k.isdigit()
                        and "SE-FM" in v["name"]
                        and "se" in v
                        and v["se"] == str(senum)
                    ][0]
                except:
                    seInfo = None

                if options["hcp_seechospacing"] is None:
                    if (
                        seInfo
                        and "EchoSpacing" in seInfo
                        and checkInlineParameterUse("SE", "EchoSpacing", options)
                    ):
                        options["hcp_seechospacing"] = seInfo["EchoSpacing"]
                        r += (
                            "\n---> Spin-Echo images specific EchoSpacing: %s s"
                            % (options["hcp_seechospacing"])
                        )

                if options["hcp_seunwarpdir"] is None:
                    if seInfo and "phenc" in seInfo:
                        options["hcp_seunwarpdir"] = SEDirMap[seInfo["phenc"]]
                        r += (
                            "\n---> Spin-Echo unwarp direction: %s"
                            % (options["hcp_seunwarpdir"])
                        )
                    elif (
                        seInfo
                        and "PEDirection" in seInfo
                        and checkInlineParameterUse("SE", "PEDirection", options)
                    ):
                        options["hcp_seunwarpdir"] = seInfo["PEDirection"]
                        r += (
                            "\n---> Spin-Echo unwarp direction: %s"
                            % (options["hcp_seunwarpdir"])
                        )

                if options["hcp_topupconfig"] != "NONE" and options["hcp_topupconfig"]:
                    topupconfig = options["hcp_topupconfig"]
                    if not os.path.exists(options["hcp_topupconfig"]):
                        topupconfig = os.path.join(
                            hcp["hcp_Config"], options["hcp_topupconfig"]
                        )
                        if not os.path.exists(topupconfig):
                            r += (
                                "\n---> ERROR: Could not find TOPUP configuration file: %s."
                                % (topupconfig)
                            )
                            run = False
                        else:
                            r += "\n---> TOPUP configuration file present."
                    else:
                        r += "\n---> TOPUP configuration file present."

                for p in [
                    "hcp_seechospacing",
                    "hcp_seunwarpdir",
                ]:
                    if p in options and not options[p]:
                        r += f"\nERROR: {p} parameter not set manually and QuNex was unable to set it automatically."
                        run = False

            except:
                r += (
                    "\n---> ERROR: Could not find files for TOPUP processing of session %s."
                    % (sinfo["id"])
                )
                run = False
                raise

        elif options["hcp_avgrdcmethod"].lower() == "gehealthcarelegacyfieldmap":
            fmnum = T1w.get("fm", None)

            if fmnum is None:
                r += "\n---> ERROR: No fieldmap number specified for the T1w image!"
                run = False
            else:
                for i, v in hcp["fieldmap"].items():
                    if os.path.exists(hcp["fieldmap"][i]["GE"]):
                        r += "\n---> Gradient Echo Field Map %d file present." % (i)
                    else:
                        r += (
                            "\n---> ERROR: Could not find Gradient Echo Field Map %d file for session %s.\n            Expected location: %s"
                            % (i, sinfo["id"], hcp["fmapge"])
                        )
                        run = False

                fmmag = None
                fmphase = None
                fmcombined = hcp["fieldmap"][int(fmnum)]["GE"]

        elif options["hcp_avgrdcmethod"].lower() in [
            "fieldmap",
            "siemensfieldmap",
            "philipsfieldmap",
            "gehealthcarefieldmap",
        ]:
            fmnum = T1w.get("fm", None)

            if fmnum is None:
                r += "\n---> ERROR: No fieldmap number specified for the T1w image!"
                run = False
            else:
                for i, v in hcp["fieldmap"].items():
                    if isinstance(hcp["fieldmap"][i]["magnitude"], list):
                        if all(
                            os.path.exists(mag)
                            for mag in hcp["fieldmap"][i]["magnitude"]
                        ):
                            r += "\n---> Magnitude Field Map %d files present." % (i)
                        else:
                            r += (
                                "\n---> ERROR: Could not find all Magnitude Field Map %d files for session %s.\n            Expected locations: %s"
                                % (i, sinfo["id"], hcp["fieldmap"][i]["magnitude"])
                            )
                            run = False
                    else:
                        if os.path.exists(hcp["fieldmap"][i]["magnitude"]):
                            r += "\n---> Magnitude Field Map %d file present." % (i)
                        else:
                            r += (
                                "\n---> ERROR: Could not find Magnitude Field Map %d file for session %s.\n            Expected location: %s"
                                % (i, sinfo["id"], hcp["fieldmap"][i]["magnitude"])
                            )
                            run = False
                    if os.path.exists(hcp["fieldmap"][i]["phase"]):
                        r += "\n---> Phase Field Map %d file present." % (i)
                    else:
                        r += (
                            "\n---> ERROR: Could not find Phase Field Map %d file for session %s.\n            Expected location: %s"
                            % (i, sinfo["id"], hcp["fmapphase"])
                        )
                        run = False

                fmmag = hcp["fieldmap"][int(fmnum)]["magnitude"]
                if isinstance(fmmag, list):
                    fmmag = "@".join(fmmag)
                fmphase = hcp["fieldmap"][int(fmnum)]["phase"]
                fmcombined = None

                # try to set hcp_echodiff from the JSON sidecar if not yet set
                if not options["hcp_echodiff"]:
                    fmfolder = os.path.join(
                        hcp["source"],
                        "FieldMap%s%s" % (fmnum, options["fctail"]),
                    )

                    fmap_json = glob.glob(os.path.join(fmfolder, "*Phase.json"))

                    if len(fmap_json) != 0:
                        fmap_json = fmap_json[0]
                        json_sidecar = os.path.join(fmfolder, fmap_json)

                        if os.path.exists(json_sidecar):
                            r += "\n---> Trying to set hcp_echodiff from the JSON sidecar."
                            with open(json_sidecar, "r") as file:
                                sidecar_data = json.load(file)
                                if (
                                    "EchoTime1" in sidecar_data
                                    and "EchoTime2" in sidecar_data
                                ):
                                    et2 = float(sidecar_data["EchoTime2"])
                                    et1 = float(sidecar_data["EchoTime1"])
                                    echodiff = (et2 - et1) * 1000
                                    echodiff = f"{echodiff:.10f}"
                                    r += f"\n       - hcp_echodiff set to {echodiff}"
                        else:
                            r += "\n---> hcp_echodiff not provided and not found in the JSON sidecar, setting it to 'NONE'."
                            echodiff = "NONE"
                            if options["hcp_avgrdcmethod"].lower() == "fieldmap":
                                r += "\n---> ERROR: hcp_echodiff is not set and cannot be deducted from the JSON sidecar."
                                run = False
                    else:
                        r += "\n---> JSON sidecar not found, setting hcp_echodiff to 'NONE'."
                        echodiff = "NONE"
                        if options["hcp_avgrdcmethod"].lower() == "fieldmap":
                            r += "\n---> ERROR: hcp_echodiff is not set and cannot be deducted from the JSON sidecar."
                            run = False
                else:
                    echodiff = options["hcp_echodiff"]

        else:
            r += "\n---> WARNING: No distortion correction method specified."

        # --- lookup gdcoeffs file if needed
        gdcfile, r, run = check_gdc_coeff_file(
            options["hcp_gdcoeffs"], hcp=hcp, sinfo=sinfo, r=r, run=run
        )

        # --- see if we have set up to use custom mask
        if options["hcp_prefs_custombrain"] == "MASK":
            tfile = os.path.join(hcp["T1w_folder"], "T1w_acpc_dc_restore_brain.nii.gz")
            mfile = os.path.join(
                hcp["T1w_folder"], "custom_acpc_dc_restore_mask.nii.gz"
            )
            r += "\n---> Set to run only final atlas registration with a custom mask."

            if os.path.exists(tfile):
                r += "\n     ... Previous results present."
                if os.path.exists(mfile):
                    r += "\n     ... Custom mask present."
                else:
                    r += "\n     ... ERROR: Custom mask missing! [%s]!." % (mfile)
                    run = False
            else:
                run = False
                r += "\n     ... ERROR: No previous results found! Please run PreFS without hcp_prefs_custombrain set to MASK first!"
                if os.path.exists(mfile):
                    r += "\n     ... Custom mask present."
                else:
                    r += "\n     ... ERROR: Custom mask missing as well! [%s]!." % (
                        mfile
                    )

        # --- check if we are using a custom brain
        if options["hcp_prefs_custombrain"] == "CUSTOM":
            t1files = ["T1w_acpc_dc_restore_brain.nii.gz", "T1w_acpc_dc_restore.nii.gz"]
            t2files = ["T2w_acpc_dc_restore_brain.nii.gz", "T2w_acpc_dc_restore.nii.gz"]
            if hcp["T2w"] in ["", "NONE"]:
                tfiles = t1files
            else:
                tfiles = t1files + t2files

            r += "\n---> Set to run only final atlas registration with custom brain images."

            missingfiles = []
            for tfile in tfiles:
                if not os.path.exists(os.path.join(hcp["T1w_folder"], tfile)):
                    missingfiles.append(tfile)

            if missingfiles:
                run = False
                r += (
                    "\n     ... ERROR: The following brain files are missing in %s:"
                    % (hcp["T1w_folder"])
                )
                for tfile in missingfiles:
                    r += "\n                %s" % tfile

        # -- Prepare templates
        # try to set hcp_prefs_template_res automatically if not set yet
        if not options["hcp_prefs_template_res"]:
            r += "\n---> Trying to set the hcp_prefs_template_res parameter automatically."
            t1w = hcp["T1w"].split("@")[0]
            resolution, res_report = _set_hcp_prefs_template_res(t1w)
            r += res_report
            if resolution == 0:
                run = False
                r += "\n     ... ERROR: unable to set hcp_prefs_template_res automatically, please set it manually!"
            else:
                options["hcp_prefs_template_res"] = resolution

        # if hcp_prefs_template_res cannot be converted to a number something went wrong
        try:
            float(options["hcp_prefs_template_res"])
        except:
            r += (
                "\n---> ERROR: hcp_prefs_template_res  [%s] is not a number! It could be that automatic setup did not work, set it manually."
                % (options["hcp_prefs_template_res"])
            )
            run = False

        # hcp_prefs_t1template
        if options["hcp_prefs_t1template"] is None:
            t1template = os.path.join(
                hcp["hcp_Templates"],
                "MNI152_T1_%smm.nii.gz" % (options["hcp_prefs_template_res"]),
            )
        else:
            t1template = options["hcp_prefs_t1template"]

        # hcp_prefs_t1templatebrain
        if options["hcp_prefs_t1templatebrain"] is None:
            t1templatebrain = os.path.join(
                hcp["hcp_Templates"],
                "MNI152_T1_%smm_brain.nii.gz" % (options["hcp_prefs_template_res"]),
            )
        else:
            t1templatebrain = options["hcp_prefs_t1templatebrain"]

        # hcp_prefs_t1template2mm
        if options["hcp_prefs_t1template2mm"] is None:
            t1template2mm = os.path.join(hcp["hcp_Templates"], "MNI152_T1_2mm.nii.gz")
        else:
            t1template2mm = options["hcp_prefs_t1template2mm"]

        # hcp_prefs_t2template
        if options["hcp_t2"] == "NONE":
            t2template = "NONE"
        elif options["hcp_prefs_t2template"] is None:
            t2template = os.path.join(
                hcp["hcp_Templates"],
                "MNI152_T2_%smm.nii.gz" % (options["hcp_prefs_template_res"]),
            )
        else:
            t2template = options["hcp_prefs_t2template"]

        # hcp_prefs_t2templatebrain
        if options["hcp_t2"] == "NONE":
            t2templatebrain = "NONE"
        elif options["hcp_prefs_t2templatebrain"] is None:
            t2templatebrain = os.path.join(
                hcp["hcp_Templates"],
                "MNI152_T2_%smm_brain.nii.gz" % (options["hcp_prefs_template_res"]),
            )
        else:
            t2templatebrain = options["hcp_prefs_t2templatebrain"]

        # hcp_prefs_t2template2mm
        if options["hcp_t2"] == "NONE":
            t2template2mm = "NONE"
        elif options["hcp_prefs_t2template2mm"] is None:
            t2template2mm = os.path.join(hcp["hcp_Templates"], "MNI152_T2_2mm.nii.gz")
        else:
            t2template2mm = options["hcp_prefs_t2template2mm"]

        # hcp_prefs_templatemask
        if options["hcp_prefs_templatemask"] is None:
            templatemask = os.path.join(
                hcp["hcp_Templates"],
                "MNI152_T1_%smm_brain_mask.nii.gz"
                % (options["hcp_prefs_template_res"]),
            )
        else:
            templatemask = options["hcp_prefs_templatemask"]

        # hcp_prefs_template2mmmask
        if options["hcp_prefs_template2mmmask"] is None:
            template2mmmask = os.path.join(
                hcp["hcp_Templates"], "MNI152_T1_2mm_brain_mask_dil.nii.gz"
            )
        else:
            template2mmmask = options["hcp_prefs_template2mmmask"]

        # hcp_prefs_fnirtconfig
        if options["hcp_prefs_fnirtconfig"] is None:
            fnirtconfig = os.path.join(hcp["hcp_Config"], "T1_2_MNI152_2mm.cnf")
        else:
            fnirtconfig = options["hcp_prefs_fnirtconfig"]

        # --- Set up the command
        comm = (
            os.path.join(hcp["hcp_base"], "PreFreeSurfer", "PreFreeSurferPipeline.sh")
            + " "
        )

        # if hcp_seechospacing and hcp_seunwarpdir are None at this point, set to "NONE"
        if options["hcp_seechospacing"] is None:
            options["hcp_seechospacing"] = "NONE"
        if options["hcp_seunwarpdir"] is None:
            options["hcp_seunwarpdir"] = "NONE"

        elements = [
            ("path", sinfo["hcp"]),
            ("subject", sinfo["id"] + options["hcp_suffix"]),
            ("t1", hcp["T1w"]),
            ("t2", hcp["T2w"]),
            ("t1template", t1template),
            ("t1templatebrain", t1templatebrain),
            ("t1template2mm", t1template2mm),
            ("t2template", t2template),
            ("t2templatebrain", t2templatebrain),
            ("t2template2mm", t2template2mm),
            ("templatemask", templatemask),
            ("template2mmmask", template2mmmask),
            ("brainsize", options["hcp_brainsize"]),
            ("fnirtconfig", fnirtconfig),
            ("fmapmag", fmmag),
            ("fmapphase", fmphase),
            ("fmapcombined", fmcombined),
            ("echodiff", echodiff),
            ("SEPhaseNeg", seneg),
            ("SEPhasePos", sepos),
            ("seechospacing", options["hcp_seechospacing"]),
            ("seunwarpdir", options["hcp_seunwarpdir"]),
            ("t1samplespacing", options["hcp_t1samplespacing"]),
            ("t2samplespacing", options["hcp_t2samplespacing"]),
            ("unwarpdir", options["hcp_unwarpdir"]),
            ("gdcoeffs", gdcfile),
            ("avgrdcmethod", options["hcp_avgrdcmethod"]),
            ("topupconfig", topupconfig),
            ("bfsigma", options["hcp_bfsigma"]),
            ("printcom", options["hcp_printcom"]),
            ("custombrain", options["hcp_prefs_custombrain"]),
            ("processing-mode", options["hcp_processing_mode"]),
        ]

        # optional parameters
        # hcp_sephasepos2, hcp_sephaseneg2, hcp_senum2 for a second SE pair for TOPUP
        if options["hcp_sephasepos2"] and options["hcp_sephaseneg2"]:
            if os.path.exists(options["hcp_sephasepos2"]) and os.path.exists(
                options["hcp_sephaseneg2"]
            ):
                sepos2 = options["hcp_sephasepos2"]
                seneg2 = options["hcp_sephaseneg2"]
                r += "\n---> Second Spin-Echo pair of images present. [%s, %s]" % (
                    os.path.basename(sepos2),
                    os.path.basename(seneg2),
                )
            # labels
            elif options["hcp_senum2"]:
                try:
                    tufolder2 = os.path.join(
                        hcp["source"],
                        "SpinEchoFieldMap%s%s"
                        % (options["hcp_senum2"], options["fctail"]),
                    )
                    sepos2 = glob.glob(
                        os.path.join(
                            tufolder2, "*_" + options["hcp_sephasepos2"] + "*.nii.gz"
                        )
                    )[0]
                    seneg2 = glob.glob(
                        os.path.join(
                            tufolder2, "*_" + options["hcp_sephaseneg2"] + "*.nii.gz"
                        )
                    )[0]

                    if all([sepos2, seneg2]):
                        r += "\n---> Spin-Echo pair of images present. [%s]" % (
                            os.path.basename(tufolder)
                        )
                    else:
                        r += (
                            "\n---> ERROR: Could not find the relevant second Spin-Echo files! [%s]"
                            % (tufolder2)
                        )
                        run = False
                except:
                    r += (
                        "\n---> ERROR: Could not find the relevant second Spin-Echo files! [%s]"
                        % (tufolder2)
                    )
                    run = False
            else:
                r += "\n---> ERROR: Could not find the relevant second Spin-Echo files!"
                run = False

            elements += [
                ("SEPhasePos2", sepos2),
                ("SEPhaseNeg2", seneg2),
            ]

        # optional parameters: species, runmode, patient positions, BET settings, brain extraction
        if options["hcp_species"]:
            elements.append(("species", options["hcp_species"]))

        if options["hcp_runmode"]:
            elements.append(("runmode", options["hcp_runmode"]))

        if options["hcp_truepatientposition"]:
            elements.append(("truepatientposition", options["hcp_truepatientposition"]))

        if options["hcp_scannerpatientposition"]:
            elements.append(
                ("scannerpatientposition", options["hcp_scannerpatientposition"])
            )

        if options["hcp_betcenter"]:
            elements.append(("betcenter", options["hcp_betcenter"]))

        if options["hcp_betradius"]:
            elements.append(("betradius", options["hcp_betradius"]))

        if options["hcp_betfraction"]:
            elements.append(("betfraction", options["hcp_betfraction"]))

        if options["hcp_bettop2center"]:
            elements.append(("bettop2center", options["hcp_bettop2center"]))

        if options["hcp_brainextract"]:
            elements.append(("brainextract", options["hcp_brainextract"]))

        if options["hcp_use_t2w_phase_zero"]:
            elements.append(("use-t2w-phase-zero", options["hcp_use_t2w_phase_zero"]))

        if options["hcp_bias_field_sigma_no_t2w"]:
            elements.append(
                (
                    "bias-field-sigma-no-T2w",
                    options["hcp_bias_field_sigma_no_t2w"],
                )
            )

        if options["hcp_betbiasfieldcor"]:
            elements.append(("betbiasfieldcor", options["hcp_betbiasfieldcor"]))

        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])

        # -- Report command
        if run:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test files
        tfile = os.path.join(hcp["hcp_nonlin"], "T1w_restore_brain.nii.gz")
        if hcp["hcp_prefs_check"]:
            fullTest = {
                "tfolder": hcp["base"],
                "tfile": hcp["hcp_prefs_check"],
                "fields": [("sessionid", sinfo["id"] + options["hcp_suffix"])],
                "specfolder": options["specfolder"],
            }
        else:
            fullTest = None

        # -- Run
        if run:
            if options["run"] == "run":
                if overwrite:
                    if os.path.exists(tfile):
                        os.remove(tfile)

                    # additional cleanup for stability and compatibility purposes
                    image = os.path.join(
                        hcp["T1w_folder"], "T1w_acpc_dc_restore.nii.gz"
                    )
                    if os.path.exists(image):
                        os.remove(image)

                    brain = os.path.join(
                        hcp["T1w_folder"], "T1w_acpc_dc_restore_brain.nii.gz"
                    )
                    if os.path.exists(brain):
                        os.remove(brain)

                    bias = os.path.join(hcp["T1w_folder"], "BiasField_acpc_dc.nii.gz")
                    if os.path.exists(bias):
                        os.remove(bias)

                r, _, report, failed = pc.runExternalForFile(
                    tfile,
                    comm,
                    "Running HCP PreFS",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    fullTest=fullTest,
                    shell=True,
                    r=r,
                )

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(
                    tfile, fullTest, "HCP PreFS", r, overwrite=overwrite
                )
                if passed is None:
                    r += "\n---> HCP PreFS can be run"
                    report = "HCP Pre FS can be run"
                    failed = 0
        else:
            r += "\n---> Due to missing files session cannot be processed."
            report = "Files missing, PreFS cannot be run"
            failed = 1

    except ge.CommandFailed as e:
        r += "\n\nERROR in completing %s at %s:\n     %s\n" % (
            "PreFreeSurfer",
            e.function,
            "\n     ".join(e.report),
        )
        report = "PreFS failed"
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = "PreFS failed"
        failed = 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = "PreFS failed"
        failed = 1

    r += (
        "\nHCP PreFS %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, (sinfo["id"], report, failed))


def _set_hcp_prefs_template_res(image):
    """
    Set the template resolution based on the pixdim of the T1w image.

    Parameters:
        image: image to use for pixel setting.
    """

    img = nib.load(image)
    pixdim1, pixdim2, pixdim3 = img.header["pixdim"][1:4]

    # do they match
    epsilon = 0.05
    r = ""
    if abs(pixdim1 - pixdim2) > epsilon or abs(pixdim1 - pixdim3) > epsilon:
        r = f"\n     ... ERROR: T1w pixdim mismatch [{pixdim1, pixdim2, pixdim3}], please set hcp_prefs_template_res manually!"
        return (0, r)
    else:
        # upscale slightly and use the closest that matches
        pixdim = pixdim1 * 1.05

        if pixdim > 2:
            r = f"\n     ... ERROR: weird T1w pixdim found [{pixdim1, pixdim2, pixdim3}], please set the associated parameters manually!"
            return (0, r)
        elif pixdim > 1:
            r = f"\n     ... Based on T1w pixdim [{pixdim1, pixdim2, pixdim3}] the hcp_prefs_template_res parameter was set to 1.0!"
            return (1, r)
        elif pixdim > 0.8:
            r = f"\n     ... Based on T1w pixdim [{pixdim1, pixdim2, pixdim3}] the hcp_prefs_template_res parameter was set to 0.8!"
            return (0.8, r)
        elif pixdim > 0.65:
            r = f"\n     ... Based on T1w pixdim [{pixdim1, pixdim2, pixdim3}] the hcp_prefs_template_res parameter was set to to 0.7!"
            return (0.7, r)
        else:
            r = f"\n     ... ERROR: weird T1w pixdim found [{pixdim1, pixdim2, pixdim3}], please set the associated parameters manually!"
            return (0, r)


def hcp_freesurfer(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_freesurfer [... processing options]``

    Runs the FS step of the HCP Pipeline (FreeSurferPipeline.sh).

    Warning:
        The code expects the previous step (hcp_pre_freesurfer) to have run
        successfully and checks for presence of a few key files and folders. Due
        to the number of inputs that it requires, it does not make a full check
        for all of them!

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_processing_mode (str, default 'HCPStyleData'):
            Controls whether the HCP acquisition and processing guidelines
            should be treated as requirements ('HCPStyleData') or if additional
            processing functionality is allowed ('LegacyStyleData'). In this case
            running processing w/o a T2w image.

        --hcp_folderstructure (str, default 'hcpls'):
            If set to 'hcpya' the folder structure used in the initial HCP
            Young Adults study is used. Specifically, the source files are
            stored in individual folders within the main 'hcp' folder in
            parallel with the working folders and the 'MNINonLinear' folder
            with results. If set to 'hcpls' the folder structure used in the
            HCP Life Span study is used. Specifically, the source files are
            all stored within their individual subfolders located in the joint
            'unprocessed' folder in the main 'hcp' folder, parallel to the
            working folders and the 'MNINonLinear' folder.

        --hcp_filename (str, default 'automated'):
            How to name the BOLD files once mapped intothe hcp input folder
            structure. The default ('automated') will automatically name each
            file by their number (e.g. BOLD_1). The alternative ('userdefined')
            is to use the file names, which can be defined by the user prior to
            mapping (e.g. rfMRI_REST1_AP).

        --hcp_fs_seed (str, default ''):
            Recon-all seed value. If not specified, none will be used.
            (Please note that it will only be used when HCP Pipelines are
            used. It is not implemented in hcpmodified!)

        --hcp_fs_edits (str, default 'FALSE'):
            Indicates whether manual edits are to be applied to the FreeSurfer
            outputs. If set to 'TRUE', the user needs to either place the edited
            files in <sessions folder>/inbox/FS_edits and prepend '<session id>_'
            to identify them, or place them in the standard FreeSurfer location
            themselves. The 'existing_session' parameter will be set to TRUE,
            and 'extra_reconall' parameters will be set as well to only run the
            necessary steps to incorporate the edits, depending on the edits
            present and/or specified. This option can be used for edits to
            control.dat, aseg.mgz, wm.mgz, and brainmask.mgz files. Accepted
            values are 'FALSE', 'TRUE', or a comma-separated list of edits to
            apply: 'control', 'aseg', 'wm', 'brainmask'. If edits are not
            specified explicitly, they will be determined based on the files
            found in the FS_edits folder.

        --hcp_fs_existing_session (str, default 'FALSE'):
            Indicates that the command is to be run on top of an already
            existing analysis/subject. This excludes the `-i` flag from the
            invocation of recon-all. If set, the user needs to specify which
            recon-all stages to run using the --hcp_fs_extra_reconall
            parameter. Accepted values are 'TRUE' and 'FALSE'.
            (Please note that it will only be used when HCP Pipelines are
            used. It is not implemented in hcpmodified!)

        --hcp_fs_extra_reconall (str, default ''):
            A string with extra parameters to pass to FreeSurfer recon-all.
            The extra parameters are to be listed in a pipe ('|') separated
            string. Parameters and their values need to be listed
            separately. E.g. to pass `-norm3diters 3` to reconall, the
            string has to be: "-norm3diters|3".
            (Please note that it will only be used when HCP Pipelines are
            used. It is not implemented in hcpmodified!)

        --hcp_fs_flair (str, default 'FALSE'):
            If set to 'TRUE' indicates that recon-all is to be run with the
            -FLAIR/-FLAIRpial options (rather than the -T2/-T2pial options).
            The FLAIR input image itself should be provided as a regular T2w
            image.
            (Please note that it will only be used when HCP Pipelines are
            used. It is not implemented in hcpmodified!)

        --hcp_conf2hires (str, 'TRUE'):
            Whether to use the conf2hires flag in recon-all. If set to 'TRUE',
            the flag will be used, if set to 'FALSE' it will not be used.

        --hcp_hires (str, 'FALSE'):
            Whether to use the hires flag in recon-all. If set to 'TRUE',
            the flag will be used, if set to 'FALSE' it will not be used.

        --hcp_t2 (str, default 't2'):
            'NONE' if no T2w image is available and the preprocessing should be
            run without them, anything else otherwise. 'NONE' is only
            valid if 'LegacyStyleData' processing mode was specified.
            (Please note, that this setting will only be used when
            LegacyStyleData processing mode is specified!)

        --hcp_expert_file (str, default ''):
            Path to the read-in expert options file for FreeSurfer if one is
            prepared and should be used empty otherwise.
            (Please note, that this setting will only be used when
            LegacyStyleData processing mode is specified!)

        --hcp_high_myelin (float):
            The high myelin threshold for the FreeSurfer recon-all command. Set automatically by default.

    Output files:
        The results of this step will be present in the above mentioned T1w
        folder as well as MNINonLinear folder in the sessions's root hcp
        folder.

    Notes:
        Runs the FreeSurfer (FreeSurfer.sh) step of the HCP Pipelines. It takes
        the T1w and T2w images processed in the previous (hcp_pre_freesurfer)
        step, segments T1w image by brain matter and CSF, reconstructs the
        cortical surface of the brain and assigns structure labels for both
        subcortical and cortical structures. It completes the listed in
        multiple steps of increased precision and (if present) uses
        T2w image to refine the surface reconstruction. It uses the adjusted
        version of the HCP code that enables the preprocessing to run also
        if no T2w image is present.

        hcp_freesurfer parameter mapping:

            ============================ =======================
            QuNex parameter              HCPpipelines parameter
            ============================ =======================
            ``hcp_fs_seed``              ``seed``
            ``hcp_processing_mode``      ``processing-mode``
            ``hcp_fs_existing_session``  ``existing-subject``
            ``hcp_fs_extra_reconall``    ``extra-reconall-arg``
            ``hcp_conf2hires``           ``conf2hires``
            ``hcp_hires``                ``hires``
            ``hcp_fs_flair``             ``flair``
            ============================ =======================

        Running FreeSurfer again after PostFreeSurfer:

            If FreeSurfer has to be run again after PostFreeSurfer, the files
            generated during PostFreeSurfer need to be removed to prevent
            any conflicts. For this reason, when PostFreeSurfer is run, QuNex
            records the list of files generated during PostFreeSurfer and backs
            up files known to be modified by PostFreeSurfer. When FreeSurfer
            is run again, files generated by PostFreeSurfer are removed and the
            backed up files are restored.

        Running with FreeSurfer edits:

            Sometimes, after visual inspection of the FreeSurfer outputs, manual
            edits are needed to correct for misclassified regions. If such edits
            have been made, they can be applied during the FreeSurfer step in
            two ways. The first option is to place the edited files in the
            FreeSurfer standard location within the subject's FS folder, set the
            ``hcp_fs_existing_session`` parameter to 'TRUE' and specify the
            recon-all stages to run using the ``hcp_fs_extra_reconall`` parameter.
            This way, the command will run on top of an already existing analysis/
            subject and will incorporate the edits.

            The second option, if only wm.mgz, brainmask.mgz, and/or aseg.mgz
            files have been edited, is to place the edited files in the
            ``<sessions folder>/inbox/FS_edits`` folder and prepend
            ``<session id>_`` to identify them. In this case, the
            ``hcp_fs_edits`` parameter should be set to 'TRUE'. QuNex will
            detect which edits are present and will set the ``hcp_fs_existing_session``
            and ``hcp_fs_extra_reconall`` parameters accordingly to incorporate
            the edits.

            The third option is to place the edited files in the standard location
            within the subject's FS folder, and specify which edits to apply
            using the ``hcp_fs_edits`` parameter as a comma-separated list of
            edits to apply: 'aseg', 'wm', 'brainmask'. In this case, the
            ``hcp_fs_existing_session`` parameter will be set to 'TRUE', and
            ``hcp_fs_extra_reconall`` parameter will be set accordingly to
            incorporate the specified edits.

    Examples:
        Example run from the base study folder with test flag::

            qunex hcp_freesurfer \\
                --batchfile="processing/batch.txt" \\
                --sessionsfolder="sessions" \\
                --parsessions="10" \\
                --overwrite="no" \\
                --test

        Example run with absolute paths with scheduler and no T2w image is available::

            qunex hcp_freesurfer \\
                --batchfile="<path_to_study_folder>/processing/batch.hcp.txt" \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --parsessions="4" \\
                --hcp_t2="NONE" \\
                --overwrite="yes" \\
                --scheduler="SLURM,time=24:00:00,cpus-per-task=2,mem-per-cpu=1250,partition=day"

        Run from the study folder with FreeSurfer specific details and scheduler::

            qunex hcp_freesurfer \\
                --batchfile="processing/batch.txt" \\
                --sessionsfolder="sessions" \\
                --parsessions="10" \\
                --overwrite="no" \\
                --scheduler="SLURM,time=03-24:00:00,cpus-per-task=2,mem-per-cpu=1250,partition=week"

        Run with FreeSurfer edits applied and present in inbox/FS-edits::

            qunex hcp_freesurfer \\
                --batchfile="processing/batch.txt" \\
                --sessionsfolder="sessions" \\
                --sessions="s01,sub-07,sub-12" \\
                --parsessions="3" \\
                --overwrite="yes" \\
                --hcp_fs_edits="TRUE"

        Run with FreeSurfer edits prepared within FS folder and specified explicitly::

            qunex hcp_freesurfer \\
                --batchfile="processing/batch.txt" \\
                --sessionsfolder="sessions" \\
                --sessions="s01,sub-07,sub-12" \\
                --parsessions="3" \\
                --overwrite="yes" \\
                --hcp_fs_edits="wm,brainmask"

        Additional examples::

            qunex hcp_freesurfer \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10

        ::

            qunex hcp_freesurfer \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --hcp_t2=NONE

        ::

            qunex hcp_freesurfer \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --hcp_t2=NONE
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n\n%s HCP FreeSurfer Pipeline [%s] ...\n" % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    status = True
    report = "Error"
    failed = 0

    try:
        pc.doOptionsCheck(options, sinfo, "hcp_freesurfer")
        doHCPOptionsCheck(options, "hcp_freesurfer")
        hcp = getHCPPaths(sinfo, options)

        # --- run checks
        if "hcp" not in sinfo:
            r += (
                "\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"])
            )
            run = False

        # -> Pre FS results
        if os.path.exists(
            os.path.join(hcp["T1w_folder"], "T1w_acpc_dc_restore_brain.nii.gz")
        ):
            r += "\n---> PreFS results present."
        else:
            r += "\n---> ERROR: Could not find PreFS processing results."
            run = False

        # -> T2w image
        if hcp["T2w"] in ["", "NONE"]:
            t2w = "NONE"
        else:
            t2w = os.path.join(hcp["T1w_folder"], "T2w_acpc_dc_restore.nii.gz")

        if t2w == "NONE" and options["hcp_processing_mode"] == "HCPStyleData":
            r += "\n---> ERROR: The requested HCP processing mode is 'HCPStyleData', however, no T2w image was specified!\n            Consider using LegacyStyleData processing mode."
            run = False

        # test file
        tfile = os.path.join(hcp["FS_folder"], "label", "BA_exvivo.thresh.ctab")

        # ---> Building the command string
        comm = (
            os.path.join(hcp["hcp_base"], "FreeSurfer", "FreeSurferPipeline.sh") + " "
        )

        # do we have edits specified?
        if options["hcp_fs_edits"] and options["hcp_fs_edits"].upper() not in [
            "",
            "FALSE",
            "NO",
            "NONE",
        ]:
            extra = [
                e.strip()
                for e in options["hcp_fs_edits"].lower().split(",")
                if e.strip() not in ["aseg", "wm", "brainmask", "yes", "true"]
            ]
            if extra:
                r += (
                    "\n---> ERROR: Invalid edits specified in hcp_fs_edits: '%s' ['%s']"
                    % (",".join(extra), options["hcp_fs_edits"])
                )
                run = False

            else:
                edited = [
                    e
                    for e in ["aseg", "wm", "brainmask"]
                    if e in options["hcp_fs_edits"].lower().split(",")
                ]
                # -- map files
                r += "\n---> hcp_fs_edits is set to TRUE, looking for edits files ..."
                editsfolder = os.path.join(
                    options["sessionsfolder"], "inbox", "FS_edits"
                )
                editfiles = glob.glob(os.path.join(editsfolder, sinfo["id"] + "_*.mgz"))
                controlfile = os.path.join(editsfolder, sinfo["id"] + "_control.dat")
                if editfiles or os.path.exists(controlfile):
                    copyfiles = []
                    for efile in editfiles:
                        fname = os.path.basename(efile).split("_", 1)[1]
                        edited.append(fname.replace(".mgz", ""))
                        destfile = os.path.join(hcp["FS_folder"], "mri", fname)
                        copyfiles.append((efile, destfile))
                    if os.path.exists(controlfile):
                        destfile = os.path.join(hcp["FS_folder"], "tmp", "control.dat")
                        copyfiles.append((controlfile, destfile))
                        edited.append("control")
                    for efile, destfile in copyfiles:
                        if os.path.exists(destfile):
                            r += "\n     ... replacing: %s " % (fname)
                        else:
                            r += "\n     ... adding: %s " % (fname)
                        shutil.copy2(efile, destfile)
                else:
                    r += "\n     ... no edits files found in %s!" % (editsfolder)

                # -- set extra parameters
                options["hcp_fs_existing_session"] = True
                if "control" in edited:
                    add_extra = ["-autorecon2-cp", "-autorecon3"]
                elif "wm" in edited:
                    add_extra = ["-autorecon2-wm", "-autorecon3"]
                elif "aseg" in edited:
                    add_extra = ["-autorecon2-noaseg", "-autorecon3"]
                elif "brainmask" in edited:
                    add_extra = ["-autorecon-pial"]
                else:
                    r += "\n---> ERROR: No edits specified and no edited files found!"
                    r += "\n            If you are processing edits to control points, wm, aseg, or brainmask, please provide the appropriate edit files or list them explicitly in hcp_fs_edits."
                    r += "\n            For other edits, please set hcp_fs_edits to FALSE, and use hcp_fs_existing_session and hcp_fs_extra_reconall parameters."
                    run = False
                    add_extra = []

                if hcp["T2w"] not in ["", "NONE"]:
                    add_extra.append("-T2pial")

                add_extra = [
                    p for p in add_extra if p not in options["hcp_fs_extra_reconall"]
                ]
                if add_extra:
                    options["hcp_fs_extra_reconall"] = "|".join(
                        add_extra + [options["hcp_fs_extra_reconall"]]
                    )

        # -> Key elements
        elements = [
            ("session-dir", hcp["T1w_folder"]),
            ("session", sinfo["id"] + options["hcp_suffix"]),
            ("seed", options["hcp_fs_seed"]),
            ("processing-mode", options["hcp_processing_mode"]),
        ]

        # -> add t1, t1brain and t2 only if options['hcp_fs_existing_session'] is FALSE
        if not options["hcp_fs_existing_session"]:
            elements.append(
                ("t1", os.path.join(hcp["T1w_folder"], "T1w_acpc_dc_restore.nii.gz"))
            )
            elements.append(
                (
                    "t1brain",
                    os.path.join(hcp["T1w_folder"], "T1w_acpc_dc_restore_brain.nii.gz"),
                )
            )
            elements.append(("t2", t2w))

        # -> Additional, reconall parameters
        if options["hcp_fs_extra_reconall"]:
            for f in options["hcp_fs_extra_reconall"].split("|"):
                elements.append(("extra-reconall-arg", f))

        # -> additional QuNex passed parameters
        if options["hcp_expert_file"]:
            elements.append(("extra-reconall-arg", "-expert"))
            elements.append(("extra-reconall-arg", options["hcp_expert_file"]))

        # high myelin
        if options["hcp_high_myelin"] is None:
            options["hcp_high_myelin"] = ""
        if options["hcp_high_myelin"].lower() != "auto":
            elements.append(("high-myelin", options["hcp_high_myelin"]))

        # -> conf2hires and hires flags
        if options["hcp_conf2hires"]:
            elements.append(("conf2hires", options["hcp_conf2hires"]))
        if options["hcp_hires"]:
            elements.append(("hires", options["hcp_hires"]))

        # ---> Pull all together
        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])

        # ---> Add flags
        for optionName, flag in [
            ("hcp_fs_flair", "--flair"),
            ("hcp_fs_existing_session", "--existing-subject"),
        ]:
            if options[optionName]:
                comm += " %s" % (flag)

        # check if post_fs was already completed
        post_fs_tfile = os.path.join(
            hcp["hcp_nonlin"],
            sinfo["id"]
            + options["hcp_suffix"]
            + ".corrThickness.164k_fs_LR.dscalar.nii",
        )

        if os.path.exists(post_fs_tfile) and not (
            overwrite or options["hcp_fs_existing_session"]
        ):
            r += "\n---> ERROR: PostFreeSurfer results already present! Set overwrite to true or hcp_fs_existing_session to true to reprocess FreeSurfer!"
            run = False

        # -- Report command
        if run:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test files
        if hcp["hcp_fs_check"]:
            fullTest = {
                "tfolder": hcp["base"],
                "tfile": hcp["hcp_fs_check"],
                "fields": [("sessionid", sinfo["id"] + options["hcp_suffix"])],
                "specfolder": options["specfolder"],
            }
        else:
            fullTest = None

        # -- Run
        if run:
            if options["run"] == "run":
                # ---> clean up test file if overwrite and hcp_fs_existing_session not set to True
                if (
                    overwrite
                    and os.path.lexists(tfile)
                    and not options["hcp_fs_existing_session"]
                ):
                    os.remove(tfile)

                # ---> clean up only if hcp_fs_existing_session is not set to True
                if (overwrite or not os.path.exists(tfile)) and not options[
                    "hcp_fs_existing_session"
                ]:
                    if os.path.lexists(hcp["FS_folder"]):
                        r += (
                            "\n---> removing preexisting FS folder [%s]"
                            % (hcp["FS_folder"])
                        )
                        shutil.rmtree(hcp["FS_folder"], ignore_errors=True)
                    for toremove in [
                        "fsaverage",
                        "lh.EC_average",
                        "rh.EC_average",
                        os.path.join("xfms", "OrigT1w2T1w.nii.gz"),
                    ]:
                        rmtarget = os.path.join(hcp["T1w_folder"], toremove)
                        try:
                            if os.path.islink(rmtarget) or os.path.isfile(rmtarget):
                                os.remove(rmtarget)
                            elif os.path.isdir(rmtarget):
                                shutil.rmtree(rmtarget)
                        except:
                            r += (
                                "\n---> WARNING: Could not remove preexisting file/folder: %s! Please check your data!"
                                % (rmtarget)
                            )
                            status = False

                if os.path.exists(post_fs_tfile):
                    r += "\n---> WARNING: PostFreeSurfer results already present!"
                    # -> cleanup postfs
                    r += "\n     Found PostFreeSurfer results file: %s" % (
                        post_fs_tfile
                    )
                    r += "\n     Cleaning up PostFreeSurfer results to allow FreeSurfer reprocessing ..."
                    gs.rollback_snapshot(
                        diff=os.path.join(hcp["snapshots"], "postfreesurfer_diff.txt"),
                        action="delete",
                        exclude=hcp["snapshots"],
                    )

                    # -> restore backup
                    r += "\n     Restoring FreeSurfer backup ..."
                    gs.restore_files(
                        source=os.path.join(hcp["snapshots"], "postfreesurfer_backup"),
                        target=hcp["base"],
                        overwrite=True,
                    )

                # --> record freesurfer_start_snapshot
                r += "\n---> Recording FreeSurfer start snapshot ..."
                gs.record_snapshot(
                    targetfolder=hcp["base"],
                    outfile=os.path.join(hcp["snapshots"], "freesurfer_start.txt"),
                    exclude=hcp["snapshots"],
                )

                if status:
                    r, endlog, report, failed = pc.runExternalForFile(
                        tfile,
                        comm,
                        "Running HCP FS",
                        overwrite=overwrite,
                        thread=sinfo["id"],
                        remove=options["log"] == "remove",
                        task=options["command_ran"],
                        logfolder=options["comlogs"],
                        logtags=options["logtag"],
                        fullTest=fullTest,
                        shell=True,
                        r=r,
                    )

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(
                    tfile, fullTest, "HCP FS", r, overwrite=overwrite
                )
                if passed is None:
                    r += "\n---> HCP FS can be run"
                    report = "HCP FS can be run"
                    failed = 0
        else:
            r += "\n---> Subject cannot be processed."
            report = "FS cannot be run"
            failed = 1

    except ge.CommandFailed as e:
        r += "\n\nERROR in completing %s at %s:\n     %s\n" % (
            "FreeSurfer",
            e.function,
            "\n     ".join(e.report),
        )
        report = "FS failed"
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        failed = 1

    r += (
        "\n\nHCP FS %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # -- take freesurfer_end_snapshot
    if options["run"] == "run" and failed == 0:
        gs.compare_snapshots(
            before=os.path.join(hcp["snapshots"], "freesurfer_start.txt"),
            after=os.path.join(hcp["base"]),
            outfile=os.path.join(hcp["snapshots"], "freesurfer_diff.txt"),
            exclude=hcp["snapshots"],
        )

    # print r
    return (r, (sinfo["id"], report, failed))


def hcp_post_freesurfer(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_post_freesurfer [... processing options]``

    Runs the PostFS step of the HCP Pipeline (PostFreeSurferPipeline.sh).

    Warning:
        The code expects the previous step (hcp_freesurfer) to have run
        successfully and checks for presence of the last file that should have
        been generated. Due to the number of files that it requires, it does not
        make a full check for all of them!

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging  data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_processing_mode (str, default 'HCPStyleData'):
            Controls whether the HCP acquisition and processing guidelines
            should be treated as requirements ('HCPStyleData') or if additional
            processing functionality is allowed ('LegacyStyleData'). In this
            case running processing w/o a T2w image.

        --hcp_folderstructure (str, default 'hcpls'):
            If set to 'hcpya' the folder structure used in the initial HCP
            Young Adults study is used. Specifically, the source files are
            stored in individual folders within the main 'hcp' folder in
            parallel with the working folders and the 'MNINonLinear' folder
            with results. If set to 'hcpls' the folder structure used in the
            HCP Life Span study is used. Specifically, the source files are
            all stored within their individual subfolders located in the joint
            'unprocessed' folder in the main 'hcp' folder, parallel to the
            working folders and the 'MNINonLinear' folder.

        --hcp_filename (str, default 'automated'):
            How to name the BOLD files once mapped intothe hcp input folder
            structure. The default ('automated') will automatically name each
            file by their number (e.g. BOLD_1). The alternative ('userdefined')
            is to use the file names, which can be defined by the user prior to
            mapping (e.g. rfMRI_REST1_AP).

        --hcp_t2 (str, default 't2'):
            'NONE' if no T2w image is available and the preprocessing should
            be run without them, anything else otherwise. 'NONE' is
            only valid if 'LegacyStyleData' processing mode was specified.

        --hcp_surfatlasdir (str, HCP "standard_mesh_atlases"):
            Surface atlas directory.

        --hcp_grayordinatesres (int, default 2):
            The resolution of the volume part of the grayordinate representation
            in mm.

        --hcp_grayordinatesdir (str, default HCP "91282_Greyordinates"):
            Grayordinates space directory.

        --hcp_subcortgraylabels (str, default HCP "FreeSurferSubcorticalLabelTableLut.txt"):
            The location of FreeSurferSubcorticalLabelTableLut.txt.

        --hcp_refmyelinmaps (str, default HCP "Conte69.MyelinMap_BC.164k_fs_LR.dscalar.nii"):
            Group myelin map to use for bias correction.

        --hcp_hiresmesh (int, default 164):
            The number of vertices for the high resolution mesh of each
            hemisphere (in thousands).

        --hcp_lowresmesh (int, default 32):
            The number of vertices for the low resolution mesh of each
            hemisphere (in thousands).

        --hcp_regname (str, default 'MSMSulc'):
            The registration used, FS or MSMSulc.

        --hcp_mcsigma (str, default 'sqrt(200)'):
            Correction sigma used for metric smoothing.

        --hcp_inflatescale (int, default 1):
            Inflate extra scale parameter.

        --hcp_fs_ind_mean (str, default 'YES'):
            Whether to use the mean of the subject's myelin map as reference
            map's myelin map mean, YES or NO, defaults to YES.

        --hcp_freesurfer_labels (str, default '${HCPPIPEDIR}/global/config/FreeSurferAllLut.txt'):
            Path to the location of the FreeSurfer look up table file.

        --hcp_thickness_regression (str, default 'BOTH'):
            Wwhether to use the updated curvature-thickness regression, set to
            'OLD', 'NEW' or 'BOTH', defaults to 'BOTH'.

    Output files:
        The results of this step will be present in the MNINonLinear folder
        in the sessions's root hcp folder.

    Notes:
        Runs the PostFreeSurfer step (PostFreeSurferPipeline.sh) of the HCP
        Pipelines. It creates Workbench compatible files based on the Freesurfer
        segmentation and surface registration. It uses the adjusted version of
        the HCP code that enables the preprocessing to run also if no T2w image
        is present.

        hcp_post_freesurfer parameter mapping:

            ============================ ========================
            QuNex parameter              HCPpipelines parameter
            ============================ ========================
            ``hcp_freesurfer_labels``    ``freesurferlabels``
            ``hcp_surfatlasdir``         ``surfatlasdir``
            ``hcp_grayordinatesdir``     ``grayordinatesdir``
            ``hcp_grayordinatesres``     ``grayordinatesres``
            ``hcp_subcortgraylabels``    ``subcortgraylabels``
            ``hcp_refmyelinmaps``        ``refmyelinmaps``
            ``hcp_hiresmesh``            ``hiresmesh``
            ``hcp_lowresmesh``           ``lowresmesh``
            ``hcp_mcsigma``              ``mcsigma``
            ``hcp_regname``              ``regname``
            ``hcp_inflatescale``         ``inflatescale``
            ``hcp_fs_ind_mean``          ``use-ind-mean``
            ``hcp_processing_mode``      ``processing-mode``
            ``hcp_thickness_regression`` ``thickness-regression``
            ============================ ========================

    Examples:
        Example run from the base study folder with test flag::

            qunex hcp_post_freesurfer \\
                --batchfile="processing/batch.txt" \\
                --sessionsfolder="sessions" \\
                --parsessions="10" \\
                --overwrite="no" \\
                --test

        Example run with absolute paths with scheduler::

            qunex hcp_post_freesurfer \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --parsessions="4" \\
                --hcp_t2="NONE" \\
                --overwrite="yes" \\
                --scheduler="SLURM,time=24:00:00,cpus-per-task=2,mem-per-cpu=1250,partition=day"

        Additional examples::

            qunex hcp_post_freesurfer \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10

        ::

            qunex hcp_post_freesurfer \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --hcp_t2=NONE
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP PostFreeSurfer Pipeline [%s] ...\n" % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = "Error"

    try:
        pc.doOptionsCheck(options, sinfo, "hcp_post_freesurfer")
        doHCPOptionsCheck(options, "hcp_post_freesurfer")
        hcp = getHCPPaths(sinfo, options)

        # --- run checks
        if "hcp" not in sinfo:
            r += (
                "\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"])
            )
            run = False

        # -> FS results
        if os.path.exists(os.path.join(hcp["FS_folder"], "mri", "aparc+aseg.mgz")):
            r += "\n---> FS results present."
        else:
            r += "\n---> ERROR: Could not find Freesurfer processing results."
            run = False

        # -> T2w image
        if (
            hcp["T2w"] in ["", "NONE"]
            and options["hcp_processing_mode"] == "HCPStyleData"
        ):
            r += "\n---> ERROR: The requested HCP processing mode is 'HCPStyleData', however, no T2w image was specified!"
            run = False

        # hcp_freesurfer_labels
        freesurferlabels = ""
        if options["hcp_freesurfer_labels"] is None:
            freesurferlabels = os.path.join(hcp["hcp_Config"], "FreeSurferAllLut.txt")
        else:
            freesurferlabels = options["hcp_freesurfer_labels"]

        # hcp_surfatlasdir
        surfatlasdir = ""
        if options["hcp_surfatlasdir"] is None:
            surfatlasdir = os.path.join(hcp["hcp_Templates"], "standard_mesh_atlases")
        else:
            surfatlasdir = options["hcp_surfatlasdir"]

        # hcp_grayordinatesdir
        grayordinatesdir = ""
        if options["hcp_grayordinatesdir"] is None:
            grayordinatesdir = os.path.join(hcp["hcp_Templates"], "91282_Greyordinates")
        else:
            grayordinatesdir = options["hcp_grayordinatesdir"]

        # hcp_subcortgraylabels
        subcortgraylabels = ""
        if options["hcp_subcortgraylabels"] is None:
            subcortgraylabels = os.path.join(
                hcp["hcp_Config"], "FreeSurferSubcorticalLabelTableLut.txt"
            )
        else:
            subcortgraylabels = options["hcp_subcortgraylabels"]

        # hcp_refmyelinmaps
        refmyelinmaps = ""
        if options["hcp_refmyelinmaps"] is None:
            refmyelinmaps = os.path.join(
                hcp["hcp_Templates"],
                "standard_mesh_atlases",
                "Conte69.MyelinMap_BC.164k_fs_LR.dscalar.nii",
            )
        else:
            refmyelinmaps = options["hcp_refmyelinmaps"]

        # compile the command
        comm = (
            os.path.join(hcp["hcp_base"], "PostFreeSurfer", "PostFreeSurferPipeline.sh")
            + " "
        )

        elements = [
            ("path", sinfo["hcp"]),
            ("subject", sinfo["id"] + options["hcp_suffix"]),
            ("surfatlasdir", surfatlasdir),
            ("grayordinatesdir", grayordinatesdir),
            ("grayordinatesres", options["hcp_grayordinatesres"]),
            ("hiresmesh", options["hcp_hiresmesh"]),
            ("lowresmesh", options["hcp_lowresmesh"]),
            ("subcortgraylabels", subcortgraylabels),
            ("freesurferlabels", freesurferlabels),
            ("refmyelinmaps", refmyelinmaps),
            ("mcsigma", options["hcp_mcsigma"]),
            ("regname", options["hcp_regname"]),
            ("inflatescale", options["hcp_inflatescale"]),
            ("processing-mode", options["hcp_processing_mode"]),
        ]

        # optional parameters
        if options["hcp_fs_ind_mean"] != "YES":
            elements.append(("use-ind-mean", options["hcp_fs_ind_mean"]))

        if options["hcp_thickness_regression"] is not None:
            elements.append(
                ("thickness-regression", options["hcp_thickness_regression"])
            )

        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])

        # -- Report command
        if run:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test files
        tfolder = hcp["hcp_nonlin"]
        tfile = os.path.join(
            tfolder,
            sinfo["id"]
            + options["hcp_suffix"]
            + ".corrThickness.164k_fs_LR.dscalar.nii",
        )

        if hcp["hcp_postfs_check"]:
            fullTest = {
                "tfolder": hcp["base"],
                "tfile": hcp["hcp_postfs_check"],
                "fields": [("sessionid", sinfo["id"] + options["hcp_suffix"])],
                "specfolder": options["specfolder"],
            }
        else:
            fullTest = None

        # -- run
        if run:
            if options["run"] == "run":
                if not os.path.exists(tfile):
                    # ---> record pre freesurfer snapshot
                    gs.record_snapshot(
                        targetfolder=hcp["base"],
                        outfile=os.path.join(
                            hcp["snapshots"], "postfreesurfer_start.txt"
                        ),
                        exclude=hcp["snapshots"],
                    )

                    # ---> prepare freesurfer backup
                    gs.backup_files(
                        source=hcp["base"],
                        target=os.path.join(hcp["snapshots"], "postfreesurfer_backup"),
                        filelist=[
                            "MNINonLinear/T1w.nii.gz",
                            "MNINonLinear/T1w_restore.nii.gz",
                            "MNINonLinear/T1w_restore_brain.nii.gz",
                            "MNINonLinear/T2w.nii.gz",
                            "MNINonLinear/T2w_restore.nii.gz",
                            "MNINonLinear/T2w_restore_brain.nii.gz",
                            "MNINonLinear/xfms/NonlinearRegJacobians.nii.gz",
                            "T1w/T1w_acpc_dc.nii.gz",
                            "T1w/T1w_acpc_dc_restore.nii.gz",
                            "T1w/T1w_acpc_dc_restore_brain.nii.gz",
                            "T1w/T2w_acpc_dc.nii.gz",
                            "T1w/T2w_acpc_dc_restore.nii.gz",
                            "T1w/T2w_acpc_dc_restore_brain.nii.gz",
                        ],
                        overwrite=overwrite,
                    )

                # ---> clean up test file if overwrite
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, _, report, failed = pc.runExternalForFile(
                    tfile,
                    comm,
                    "Running HCP PostFS",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    fullTest=fullTest,
                    shell=True,
                    r=r,
                )

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(
                    tfile, fullTest, "HCP PostFS", r, overwrite=overwrite
                )
                if passed is None:
                    r += "\n---> HCP PostFS can be run"
                    report = "HCP PostFS can be run"
                    failed = 0
        else:
            r += "\n---> Session cannot be processed."
            report = "HCP PostFS cannot be run"
            failed = 1

    except ge.CommandFailed as e:
        r += "\n\nERROR in completing %s at %s:\n     %s\n" % (
            "PostFreeSurfer",
            e.function,
            "\n     ".join(e.report),
        )
        report = "PostFS failed"
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        failed = 1

    r += (
        "\n\nHCP PostFS %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # -- take freesurfer_end_snapshot
    if options["run"] == "run" and failed == 0:
        gs.compare_snapshots(
            before=os.path.join(hcp["snapshots"], "postfreesurfer_start.txt"),
            after=os.path.join(hcp["base"]),
            outfile=os.path.join(hcp["snapshots"], "postfreesurfer_diff.txt"),
            exclude=hcp["snapshots"],
        )

    # print r
    return (r, (sinfo["id"], report, failed))


def _get_subjects_from_batch(sinfo, hcp, run):
    """
    Get a list of subjects and their sessions from the batch file.
    """
    subjects_dict = {}
    for session in sinfo:
        if "hcp" not in session:
            r += (
                "\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (session["id"])
            )
            run = False

        if hcp["T1w"] != "NONE":
            subject = session["subject"]
            if subject not in subjects_dict:
                subject_info = {}
                subject_info["id"] = subject
                subject_info["hcp"] = [session["hcp"]]
                subject_info["sessions"] = [session["id"]]
                subjects_dict[subject] = subject_info
            else:
                subjects_dict[subject]["sessions"].append(session["id"])
                subjects_dict[subject]["hcp"].append(session["hcp"])

    # dict to list
    subjects_list = []
    for subject in subjects_dict:
        subjects_list.append(subjects_dict[subject])

    return run, subjects_list


def hcp_prep_long(sinfo, subjectids, options, overwrite=False, thread=0):
    """
    ``hcp_prep_long [... processing options]``

    Prepares the data for longitudinal processing with HCP longitudinal
    pipelines. Not needed if the starting point is hcp_long_freesurfer as that
    command does the prep work automatically.

    For each subject in the batch file, QuNex will get their sessions and
    prepare a suitable subject folder by symlinking relevant folders into it. It
    will symlink both regular session folders and longitudinal sessions folders
    (defined by hcp_longitudinal_template) if they are present.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

    Output files:
        The results of this step will be present in the
        <study_folder>/subjects.

    Examples:
        ::

            qunex hcp_prep_long \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_longitudinal_template="base"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSubjects: %s \n[started on %s]" % (
        subjectids,
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP prep long [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = {"done": [], "failed": [], "ready": [], "not ready": []}
    failed = 0

    try:
        # checks
        pc.doOptionsCheck(options, sinfo[0], "hcp_prep_long")
        doHCPOptionsCheck(options, "hcp_prep_long")
        hcp = getHCPPaths(sinfo[0], options)

        # get subjects and their sessions from the batch file
        run, subjects_list = _get_subjects_from_batch(sinfo, hcp, run)

        # launch
        parsubjects = options["parsubjects"]

        # create a multiprocessing Pool
        processPoolExecutor = ProcessPoolExecutor(parsubjects)
        # process
        f = partial(
            _execute_hcp_prep_long,
            options,
        )
        results = processPoolExecutor.map(f, subjects_list)

        # merge r and report
        for result in results:
            r += result["r"]
            run_report = result["report"]
            if run_report["done"]:
                report["done"].append(run_report["done"])
            if run_report["failed"]:
                report["failed"].append(run_report["failed"])
            if run_report["ready"]:
                report["ready"].append(run_report["ready"])
            if run_report["not ready"]:
                report["not ready"].append(run_report["not ready"])

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = "Error"
        failed = 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = "Error"
        failed = 1

    r += (
        "\n\nHCP prep long %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, (subjectids, report, failed))


def _execute_hcp_prep_long(options, subject):
    # prepare return variables
    r = ""
    report = {"done": [], "failed": [], "ready": [], "not ready": []}

    # get subject data
    subject_id = subject["id"]
    hcp_list = subject["hcp"]
    sessions_list = subject["sessions"]

    # sort out the folder structure
    sessionsfolder = options["sessionsfolder"]
    subjectsfolder = sessionsfolder.replace("sessions", "subjects")
    if not os.path.exists(subjectsfolder):
        os.makedirs(subjectsfolder)
    study_folder = os.path.join(subjectsfolder, subject_id)
    if not os.path.exists(study_folder):
        os.makedirs(study_folder)

    # symlink sessions
    for i, _ in enumerate(sessions_list):
        session = sessions_list[i]
        hcp = hcp_list[i]
        source_dir = os.path.join(hcp, session)
        # check that source exists
        if not os.path.exists(source_dir):
            r += f"\n---> ERROR: {source_dir} does not exists, cannot map into the longitudinal folder structure!"
            report["failed"] = subject_id

        target_dir = os.path.join(study_folder, session)
        gc.link_or_copy(source_dir, target_dir, symlink=True)

        # symlink long sessions back
        session_long = f"{session}.long.{options['hcp_longitudinal_template']}"
        source_long_dir = os.path.join(hcp, session_long)
        target_long_dir = os.path.join(study_folder, session_long)
        # create root long dir if needed
        if not os.path.exists(source_long_dir):
            os.makedirs(source_long_dir)
        gc.link_or_copy(source_long_dir, target_long_dir, symlink=True)

    if len(report["failed"]) == 0:
        report["done"] = subject_id

    return {"r": r, "report": report}


def hcp_long_freesurfer(sinfo, subjectids, options, overwrite=False, thread=0):
    """
    ``hcp_long_freesurfer [... processing options]``

    ``hcp_lfs [... processing options]``

    Runs the HCP Longitudinal FreeSurfer Pipeline
    (LongitudinalFreeSurferPipeline.sh).

    Warning:
        The code expects the first three HCP preprocessing steps
        (hcp_pre_freesurfer, hcp_freesurfer and hcp_post_freesurfer) to have
        been run and finished successfully.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsubjects (int, default 1):
            How many subjects to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --hcp_no_t2w:
            Set this flag to process without T2w. Disabled by default.

        --hcp_seed (int):
            The recon-all seed value.

        --hcp_high_myelin (float):
            The high myelin threshold for the FreeSurfer recon-all command. Set automatically by default.

        --hcp_parallel_mode (str, default "BUILTIN"):
            Parallelization execution mode, one of FSLSUB, BUILTIN, NONE.

        --hcp_fslsub_queue (str, default ""):
            FSLSUB queue name.

        --hcp_max_jobs (int, default -1):
            Maximum number of concurrent processes in BUILTIN mode. Set to -1 to
            auto-detect.

        --hcp_start_stage (str, default "TEMPLATE"):
            One of:
                - TEMPLATE,
                - TIMEPOINTS.

        --hcp_end_stage (str, default "TIMEPOINTS"):
            One of:
                - TEMPLATE,
                - TIMEPOINTS.

    Output files:
        The results of this step will be present in the
        <study_folder>/<sessions_folder>/<subject_id>.

    Notes:
        hcp_long_freesurfer parameter mapping:

            =================================== ===========================
            QuNex parameter                     HCPpipelines parameter
            =================================== ===========================
            ``hcp_longitudinal_template``       ``longitudinal-template``
            ``hcp_no_t2w``                      ``use-T2w``
            ``hcp_fs_seed``                     ``seed``
            ``hcp_high_myelin``                 ``high-myelin``
            ``hcp_parallel_mode``               ``parallel-mode``
            ``hcp_fslsub_queue``                ``fslsub-queue``
            ``hcp_max_jobs``                    ``max-jobs``
            ``hcp_start_stage``                 ``start-stage``
            ``hcp_end_stage``                   ``end-stage``
            =================================== ===========================

    Examples:
        ::

            qunex hcp_long_freesurfer \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_longitudinal_template="<template_id>"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSubjects: %s \n[started on %s]" % (
        subjectids,
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP Longitudnal FS Pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = {"done": [], "failed": [], "ready": [], "not ready": []}
    failed = 0

    try:
        # checks
        pc.doOptionsCheck(options, sinfo[0], "hcp_long_freesurfer")
        doHCPOptionsCheck(options, "hcp_long_freesurfer")
        hcp = getHCPPaths(sinfo[0], options)

        # get subjects and their sessions from the batch file
        run, subjects_list = _get_subjects_from_batch(sinfo, hcp, run)

        # launch
        parsubjects = options["parsubjects"]

        # create a multiprocessing Pool
        processPoolExecutor = ProcessPoolExecutor(parsubjects)
        # process
        f = partial(
            _execute_hcp_long_freesurfer,
            options,
            overwrite,
            run,
            hcp["hcp_base"],
        )
        results = processPoolExecutor.map(f, subjects_list)

        # merge r and report
        for result in results:
            r += result["r"]
            run_report = result["report"]
            if run_report["done"]:
                report["done"].append(run_report["done"])
            if run_report["failed"]:
                report["failed"].append(run_report["failed"])
            if run_report["ready"]:
                report["ready"].append(run_report["ready"])
            if run_report["not ready"]:
                report["not ready"].append(run_report["not ready"])

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = "Error"
        failed = 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = "Error"
        failed = 1

    r += (
        "\n\nHCP Longitudinal FS Preprocessing %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, (subjectids, report, failed))


def _execute_hcp_long_freesurfer(options, overwrite, run, hcp_dir, subject):
    prep_result = _execute_hcp_prep_long(options, subject)
    r = prep_result["r"]
    report = prep_result["report"]

    # get subject data
    subject_id = subject["id"]
    sessions_list = subject["sessions"]

    # studyfolder
    subjectsfolder = options["sessionsfolder"].replace("sessions", "subjects")
    study_folder = os.path.join(subjectsfolder, subject_id)

    # main long folder
    longitudinal_template = options["hcp_longitudinal_template"]
    long_dir = os.path.join(study_folder, f"{subject_id}.long.{longitudinal_template}")
    long_dir_exists = os.path.lexists(long_dir)
    # exit if overwrite is not set, else cleanup
    if not overwrite and long_dir_exists:
        r += f"\n---> ERROR: {long_dir} already exists and overwrite is set to no!"
        run = False
    else:
        if long_dir_exists:
            if os.path.islink(long_dir):
                # Remove symlink first, then clean up the directory it points to.
                long_dir_target = os.path.realpath(long_dir)
                os.unlink(long_dir)
                if os.path.isdir(long_dir_target):
                    shutil.rmtree(long_dir_target)
            else:
                shutil.rmtree(long_dir)

    # logdir
    logdir = os.path.join(
        options["logfolder"],
        "comlogs",
        f"extra_logs_hcp_long_freesurfer_{subject['id']}",
    )
    if os.path.exists(logdir):
        shutil.rmtree(logdir)
    os.makedirs(logdir)

    # build the command
    if run:
        comm = (
            '%(script)s \
            --subject="%(subject)s" \
            --path="%(studyfolder)s" \
            --sessions="%(sessions)s" \
            --longitudinal-template="%(longitudinal_template)s" \
            --parallel-mode="%(parallel_mode)s" \
            --logdir="%(logdir)s"'
            % {
                "script": os.path.join(
                    hcp_dir, "FreeSurfer", "LongitudinalFreeSurferPipeline.sh"
                ),
                "studyfolder": study_folder,
                "subject": subject_id,
                "sessions": "@".join(sessions_list),
                "longitudinal_template": longitudinal_template,
                "parallel_mode": options["hcp_parallel_mode"],
                "logdir": logdir,
            }
        )

        # -- Optional parameters
        if options["hcp_no_t2w"]:
            comm += "                --use-T2w=0"

        if options["hcp_seed"]:
            comm += f"                --seed={options['hcp_seed']}"

        if options["hcp_high_myelin"] is None:
            options["hcp_high_myelin"] = ""
        if options["hcp_high_myelin"].lower() != "auto":
            comm += f"                --high-myelin={options['hcp_high_myelin']}"

        if options["hcp_fslsub_queue"]:
            comm += f"                --fslsub-queue={options['hcp_fslsub_queue']}"

        if options["hcp_max_jobs"]:
            comm += f"                --max-jobs={options['hcp_max_jobs']}"

        if options["hcp_start_stage"]:
            comm += f"                --start-stage={options['hcp_start_stage']}"

        if options["hcp_end_stage"]:
            comm += f"                --end-stage={options['hcp_end_stage']}"

        # -- Report command
        if run:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("                --", "\n    --")
            r += "\n------------------------------------------------------------\n"

        if options["run"] == "run":
            r, endlog, _, failed = pc.runExternalForFile(
                None,
                comm,
                "Running HCP Longitudinal FS",
                overwrite=overwrite,
                thread=subject_id,
                remove=options["log"] == "remove",
                task=options["command_ran"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
                fullTest=None,
                shell=True,
                r=r,
            )

            if failed == 0:
                report["done"] = subject_id
            else:
                report["failed"] = subject_id

            with open(endlog, "a", encoding="utf-8") as log_file:
                _append_sorted_logdir_to_log(log_file, logdir)

                # print succesful completion
                print("\n---> Successful completion of task", file=log_file)

            # remove the directory and its contents
            shutil.rmtree(logdir)

        # -- just checking
        else:
            passed, _, r, _ = pc.checkRun(
                tfile, None, "HCP Longitudinal FS", r, overwrite=overwrite
            )
            if passed is None:
                r += "\n---> HCP Longitudinal FS can be run"
                report["ready"] = subject_id
            else:
                r += "\n---> HCP Longitudinal FS cannot be run"
                report["not ready"] = subject_id

    else:
        r += "\n---> Subject cannot be processed."
        report["not ready"] = subject_id

    return {"r": r, "report": report}


def hcp_long_post_freesurfer(sinfo, subjectids, options, overwrite=False, thread=0):
    """
    ``hcp_long_post_freesurfer [... processing options]``

    ``hcp_lpfs [... processing options]``

    Runs the HCP Longitudinal FreeSurfer Pipeline
    (LongitudinalFreeSurferPipeline.sh).

    Warning:
        The code expects the first three HCP preprocessing steps
        (hcp_pre_freesurfer, hcp_freesurfer and hcp_post_freesurfer) to have
        been run and finished successfully.

    Parameters:
        --batchfile (str, default ""):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default "."):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsubjects (int, default 1):
            How many subjects to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ""):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ""):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_longitudinal_template (str, default "base"):
            Name of the longitudinal template.

        --hcp_prefs_template_res (float, default set from imaging data):
            The resolution (in mm) of the structural images templates to use in
            the preFS step. Note: it should match the resolution of the
            acquired structural images. If no value is provided, QuNex will try
            to use the imaging data to set a sensible default value. It will
            notify you about which setting it used, you should pay attention to
            this piece of information and manually overwrite the default if
            something is off.

        --hcp_prefs_t1template (str, default ""):
            Path to the T1 template to be used by PreFreeSurfer. By default the
            used template is determined through the resolution provided by the
            hcp_prefs_template_res parameter.

        --hcp_prefs_t1templatebrain (str, default ""):
            Path to the T1 brain template to be used by PreFreeSurfer. By
            default the used template is determined through the resolution
            provided by the hcp_prefs_template_res parameter.

        --hcp_prefs_t1template2mm (str, default ""):
            Path to the T1 2mm template to be used by PreFreeSurfer. By default
            the used template is HCP's MNI152_T1_2mm.nii.gz.

        --hcp_prefs_t2template (str, default ""):
            Path to the T2 template to be used by PreFreeSurfer. By default the
            used template is determined through the resolution provided by the
            hcp_prefs_template_res parameter.

        --hcp_prefs_t2templatebrain (str, default ""):
            Path to the T2 brain template to be used by PreFreeSurfer. By
            default the used template is determined through the resolution
            provided by the hcp_prefs_template_res parameter.

        --hcp_prefs_t2template2mm (str, default ""):
            Path to the T2 2mm template to be used by PreFreeSurfer. By default
            the used template is HCP's MNI152_T2_2mm.nii.gz.

        --hcp_prefs_templatemask (str, default ""):
            Path to the template mask to be used by PreFreeSurfer. By default
            the used template mask is determined through the resolution provided
            by the hcp_prefs_template_res parameter.

        --hcp_prefs_template2mmmask (str, default ""):
            Path to the template mask to be used by PreFreeSurfer. By default
            the used 2mm template mask is HCP's
            MNI152_T1_2mm_brain_mask_dil.nii.gz.

        --hcp_prefs_fnirtconfig (str, default ""):
            Path to the used FNIRT config. Set to the HCP's T1_2_MNI152_2mm.cnf
            by default.

        --hcp_freesurfer_labels (str, default "${HCPPIPEDIR}/global/config/FreeSurferAllLut.txt"):
            Path to the location of the FreeSurfer look up table file.

        --hcp_surfatlasdir (str, HCP "standard_mesh_atlases"):
            Surface atlas directory.

        --hcp_grayordinatesres (int, default 2):
            The resolution of the volume part of the grayordinate representation
            in mm.

        --hcp_grayordinatesdir (str, default HCP "91282_Greyordinates"):
            Grayordinates space directory.

        --hcp_subcortgraylabels (str, default HCP "FreeSurferSubcorticalLabelTableLut.txt"):
            The location of FreeSurferSubcorticalLabelTableLut.txt.

        --hcp_refmyelinmaps (str, default HCP "Conte69.MyelinMap_BC.164k_fs_LR.dscalar.nii"):
            Group myelin map to use for bias correction.

        --hcp_hiresmesh (int, default 164):
            The number of vertices for the high resolution mesh of each
            hemisphere (in thousands).

        --hcp_lowresmesh (int, default 32):
            The number of vertices for the low resolution mesh of each
            hemisphere (in thousands).

        --hcp_regname (str, default "MSMSulc"):
            The registration used, FS or MSMSulc.

        --hcp_parallel_mode (str, default "BUILTIN"):
            Parallelization execution mode, one of FSLSUB, BUILTIN, NONE.

        --hcp_fslsub_queue (str, default ""):
            FSLSUB queue name.

        --hcp_max_jobs (int, default -1):
            Maximum number of concurrent processes in BUILTIN mode. Set to -1 to
            auto-detect.

        --hcp_start_stage (str, default "PREP-T"):
            One of:
                - PREP-T (PostFSPrepLong build template, skip timepoint
                         processing),
                - POSTFS-TP1 (PostFreeSurfer timepoint stage 1),
                - POSTFS-T (PostFreesurfer template),
                - POSTFS-TP2 (PostFreesurfer timepoint stage 2).

        --hcp_end_stage (str, default "POSTFS-TP2"):
            One of:
                - PREP-T (PostFSPrepLong build template, skip timepoint
                         processing),
                - POSTFS-TP1 (PostFreeSurfer timepoint stage 1),
                - POSTFS-T (PostFreesurfer template),
                - POSTFS-TP2 (PostFreesurfer timepoint stage 2).

    Output files:
        The results of this step will be present in the
        <study_folder>/<sessions_folder>/<subject_id>.

    Notes:
        hcp_long_post_freesurfer parameter mapping:

            =================================== ===========================
            QuNex parameter                     HCPpipelines parameter
            =================================== ===========================
            ``hcp_longitudinal_template``       ``longitudinal_template``
            ``hcp_prefs_t1template``            ``t1template``
            ``hcp_prefs_t1templatebrain``       ``t1templatebrain``
            ``hcp_prefs_t1template2mm``         ``t1template2mm``
            ``hcp_prefs_t2template``            ``t2template``
            ``hcp_prefs_t2templatebrain``       ``t2templatebrain``
            ``hcp_prefs_t2template2mm``         ``t2template2mm``
            ``hcp_prefs_templatemask``          ``templatemask``
            ``hcp_prefs_template2mmmask``       ``template2mmmask``
            ``hcp_prefs_fnirtconfig``           ``fnirtconfig``
            ``hcp_freesurfer_labels``           ``freesurferlabels``
            ``hcp_surfatlasdir``                ``surfatlasdir``
            ``hcp_grayordinatesres``            ``grayordinatesres``
            ``hcp_grayordinatesdir``            ``grayordinatesdir``
            ``hcp_subcortgraylabels``           ``subcortgraylabels``
            ``hcp_refmyelinmaps``                ``refmyelinmaps``
            ``hcp_hiresmesh``                   ``hiresmesh``
            ``hcp_lowresmesh``                  ``lowresmesh``
            ``hcp_regname``                     ``regname``
            ``hcp_parallel_mode``               ``parallel-mode``
            ``hcp_fslsub_queue``                ``fslsub-queue``
            ``hcp_max_jobs``                    ``max-jobs``
            ``hcp_start_stage``                 ``start-stage``
            ``hcp_end_stage``                   ``end-stage``
            =================================== ===========================

    Examples:
        ::

            qunex hcp_long_post_freesurfer \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSubjects: %s \n[started on %s]" % (
        subjectids,
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP Longitudnal Post FS Pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = {"done": [], "failed": [], "ready": [], "not ready": []}
    failed = 0

    try:
        # checks
        pc.doOptionsCheck(options, sinfo[0], "hcp_long_post_freesurfer")
        doHCPOptionsCheck(options, "hcp_long_post_freesurfer")
        hcp = getHCPPaths(sinfo[0], options)

        # get subjects and their sesssions from the batch file
        run, subjects_list = _get_subjects_from_batch(sinfo, hcp, run)

        # launch
        parsubjects = options["parsubjects"]

        # create a multiprocessing Pool
        processPoolExecutor = ProcessPoolExecutor(parsubjects)
        # process
        f = partial(_execute_hcp_long_post_freesurfer, options, overwrite, run, hcp)
        results = processPoolExecutor.map(f, subjects_list)

        # merge
        for result in results:
            r += result["r"]
            run_report = result["report"]
            if run_report["done"]:
                report["done"].append(run_report["done"])
            if run_report["failed"]:
                report["failed"].append(run_report["failed"])
            if run_report["ready"]:
                report["ready"].append(run_report["ready"])
            if run_report["not ready"]:
                report["not ready"].append(run_report["not ready"])

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = "Error"
        failed = 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = "Error"
        failed = 1

    r += (
        "\n\nHCP Longitudinal Post FS Preprocessing %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, (subjectids, report, failed))


def _execute_hcp_long_post_freesurfer(options, overwrite, run, hcp, subject):
    # prepare return variables
    r = ""
    report = {"done": [], "failed": [], "ready": [], "not ready": []}

    # subject id
    subject_id = subject["id"]

    # -- Prepare templates
    # try to set hcp_prefs_template_res automatically if not set yet
    if not options["hcp_prefs_template_res"]:
        r += "\n---> Trying to set the hcp_prefs_template_res parameter automatically."
        t1w = hcp["T1w"].split("@")[0]
        resolution, res_report = _set_hcp_prefs_template_res(t1w)
        r += res_report
        if resolution == 0:
            run = False
            r += "\n     ... ERROR: unable to set hcp_prefs_template_res automatically, please set it manually!"
        else:
            options["hcp_prefs_template_res"] = resolution

    # if hcp_prefs_template_res cannot be converted to a number something went wrong
    try:
        float(options["hcp_prefs_template_res"])
    except:
        r += (
            "\n---> ERROR: hcp_prefs_template_res  [%s] is not a number! It could be that automatic setup did not work, set it manually."
            % (options["hcp_prefs_template_res"])
        )
        run = False

    # hcp_prefs_t1template
    if options["hcp_prefs_t1template"] is None:
        t1template = os.path.join(
            hcp["hcp_Templates"],
            "MNI152_T1_%smm.nii.gz" % (options["hcp_prefs_template_res"]),
        )
    else:
        t1template = options["hcp_prefs_t1template"]

    # hcp_prefs_t1templatebrain
    if options["hcp_prefs_t1templatebrain"] is None:
        t1templatebrain = os.path.join(
            hcp["hcp_Templates"],
            "MNI152_T1_%smm_brain.nii.gz" % (options["hcp_prefs_template_res"]),
        )
    else:
        t1templatebrain = options["hcp_prefs_t1templatebrain"]

    # hcp_prefs_t1template2mm
    if options["hcp_prefs_t1template2mm"] is None:
        t1template2mm = os.path.join(hcp["hcp_Templates"], "MNI152_T1_2mm.nii.gz")
    else:
        t1template2mm = options["hcp_prefs_t1template2mm"]

    # hcp_prefs_t2template
    if options["hcp_t2"] == "NONE":
        t2template = ""
    elif options["hcp_prefs_t2template"] is None:
        t2template = os.path.join(
            hcp["hcp_Templates"],
            "MNI152_T2_%smm.nii.gz" % (options["hcp_prefs_template_res"]),
        )
    else:
        t2template = options["hcp_prefs_t2template"]

    # hcp_prefs_t2templatebrain
    if options["hcp_t2"] == "NONE":
        t2templatebrain = ""
    elif options["hcp_prefs_t2templatebrain"] is None:
        t2templatebrain = os.path.join(
            hcp["hcp_Templates"],
            "MNI152_T2_%smm_brain.nii.gz" % (options["hcp_prefs_template_res"]),
        )
    else:
        t2templatebrain = options["hcp_prefs_t2templatebrain"]

    # hcp_prefs_t2template2mm
    if options["hcp_t2"] == "NONE":
        t2template2mm = ""
    elif options["hcp_prefs_t2template2mm"] is None:
        t2template2mm = os.path.join(hcp["hcp_Templates"], "MNI152_T2_2mm.nii.gz")
    else:
        t2template2mm = options["hcp_prefs_t2template2mm"]

    # hcp_prefs_templatemask
    if options["hcp_prefs_templatemask"] is None:
        templatemask = os.path.join(
            hcp["hcp_Templates"],
            "MNI152_T1_%smm_brain_mask.nii.gz" % (options["hcp_prefs_template_res"]),
        )
    else:
        templatemask = options["hcp_prefs_templatemask"]

    # hcp_prefs_template2mmmask
    if options["hcp_prefs_template2mmmask"] is None:
        template2mmmask = os.path.join(
            hcp["hcp_Templates"], "MNI152_T1_2mm_brain_mask_dil.nii.gz"
        )
    else:
        template2mmmask = options["hcp_prefs_template2mmmask"]

    # hcp_prefs_fnirtconfig
    if options["hcp_prefs_fnirtconfig"] is None:
        fnirtconfig = os.path.join(hcp["hcp_Config"], "T1_2_MNI152_2mm.cnf")
    else:
        fnirtconfig = options["hcp_prefs_fnirtconfig"]

    # hcp_freesurfer_labels
    freesurferlabels = ""
    if options["hcp_freesurfer_labels"] is None:
        freesurferlabels = os.path.join(hcp["hcp_Config"], "FreeSurferAllLut.txt")
    else:
        freesurferlabels = options["hcp_freesurfer_labels"]

    # hcp_surfatlasdir
    surfatlasdir = ""
    if options["hcp_surfatlasdir"] is None:
        surfatlasdir = os.path.join(hcp["hcp_Templates"], "standard_mesh_atlases")
    else:
        surfatlasdir = options["hcp_surfatlasdir"]

    # hcp_grayordinatesdir
    grayordinatesdir = ""
    if options["hcp_grayordinatesdir"] is None:
        grayordinatesdir = os.path.join(hcp["hcp_Templates"], "91282_Greyordinates")
    else:
        grayordinatesdir = options["hcp_grayordinatesdir"]

    # hcp_subcortgraylabels
    subcortgraylabels = ""
    if options["hcp_subcortgraylabels"] is None:
        subcortgraylabels = os.path.join(
            hcp["hcp_Config"], "FreeSurferSubcorticalLabelTableLut.txt"
        )
    else:
        subcortgraylabels = options["hcp_subcortgraylabels"]

    # hcp_refmyelinmaps
    refmyelinmaps = ""
    if options["hcp_refmyelinmaps"] is None:
        refmyelinmaps = os.path.join(
            hcp["hcp_Templates"],
            "standard_mesh_atlases",
            "Conte69.MyelinMap_BC.164k_fs_LR.dscalar.nii",
        )
    else:
        refmyelinmaps = options["hcp_refmyelinmaps"]

    # logdir
    logdir = os.path.join(
        options["logfolder"],
        "comlogs",
        f"extra_logs_hcp_long_post_freesurfer_{subject['id']}",
    )
    if os.path.exists(logdir):
        shutil.rmtree(logdir)
    os.makedirs(logdir)

    # subject folder
    studyfolder = os.path.join(
        options["sessionsfolder"].replace("sessions", "subjects"), subject["id"]
    )

    # build the command
    if run:
        comm = (
            '%(script)s \
            --study-folder="%(studyfolder)s" \
            --subject="%(subject)s" \
            --sessions="%(sessions)s" \
            --longitudinal-template="%(longitudinal_template)s" \
            --t1template="%(t1template)s" \
            --t1templatebrain="%(t1templatebrain)s" \
            --t1template2mm="%(t1template2mm)s" \
            --t2template="%(t2template)s" \
            --t2templatebrain="%(t2templatebrain)s" \
            --t2template2mm="%(t2template2mm)s" \
            --templatemask="%(templatemask)s" \
            --template2mmmask="%(template2mmmask)s" \
            --fnirtconfig="%(fnirtconfig)s" \
            --freesurferlabels="%(freesurferlabels)s" \
            --surfatlasdir="%(surfatlasdir)s" \
            --grayordinatesres="%(grayordinatesres)s" \
            --grayordinatesdir="%(grayordinatesdir)s" \
            --hiresmesh="%(hiresmesh)s" \
            --lowresmesh="%(lowresmesh)s" \
            --subcortgraylabels="%(subcortgraylabels)s" \
            --refmyelinmaps="%(refmyelinmaps)s" \
            --regname="%(regname)s" \
            --parallel-mode="%(parallel_mode)s" \
            --logdir="%(logdir)s"'
            % {
                "script": os.path.join(
                    hcp["hcp_base"],
                    "PostFreeSurfer",
                    "PostFreeSurferPipelineLongLauncher.sh",
                ),
                "studyfolder": studyfolder,
                "subject": subject["id"],
                "sessions": "@".join(subject["sessions"]),
                "longitudinal_template": options["hcp_longitudinal_template"],
                "t1template": t1template,
                "t1templatebrain": t1templatebrain,
                "t1template2mm": t1template2mm,
                "t2template": t2template,
                "t2templatebrain": t2templatebrain,
                "t2template2mm": t2template2mm,
                "templatemask": templatemask,
                "template2mmmask": template2mmmask,
                "fnirtconfig": fnirtconfig,
                "freesurferlabels": freesurferlabels,
                "surfatlasdir": surfatlasdir,
                "grayordinatesres": options["hcp_grayordinatesres"],
                "grayordinatesdir": grayordinatesdir,
                "hiresmesh": options["hcp_hiresmesh"],
                "lowresmesh": options["hcp_lowresmesh"],
                "subcortgraylabels": subcortgraylabels,
                "refmyelinmaps": refmyelinmaps,
                "regname": options["hcp_regname"],
                "parallel_mode": options["hcp_parallel_mode"],
                "logdir": logdir,
            }
        )

        if options["hcp_fslsub_queue"]:
            comm += f"                --fslsub-queue={options['hcp_fslsub_queue']}"

        if options["hcp_max_jobs"]:
            comm += f"                --max-jobs={options['hcp_max_jobs']}"

        if options["hcp_start_stage"]:
            comm += f"                --start-stage={options['hcp_start_stage']}"

        if options["hcp_end_stage"]:
            comm += f"                --end-stage={options['hcp_end_stage']}"

        # -- Report command
        if run:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("                --", "\n    --")
            r += "\n------------------------------------------------------------\n"

        # -- Test file
        tfile = None

        if options["run"] == "run":
            r, endlog, _, failed = pc.runExternalForFile(
                tfile,
                comm,
                "Running HCP Longitudinal Post FS",
                overwrite=overwrite,
                thread=subject_id,
                remove=options["log"] == "remove",
                task=options["command_ran"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
                fullTest=None,
                shell=True,
                r=r,
            )

            if failed == 0:
                report["done"] = subject_id
            else:
                report["failed"] = subject_id

            with open(endlog, "a", encoding="utf-8") as log_file:
                _append_sorted_logdir_to_log(log_file, logdir)

                # print succesful completion
                print("\n---> Successful completion of task", file=log_file)

            # remove the directory and its contents
            shutil.rmtree(logdir)

    else:
        r += "\n---> Subject cannot be processed."
        report["not ready"] = subject_id

    return {"r": r, "report": report}


def hcp_diffusion(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_diffusion [... processing options]``

    Runs the Diffusion step of HCP Pipeline (DiffPreprocPipeline.sh). This
    command uses GPUs by default so CUDA Libraries are required for this to
    work. Use the hcp_nogpu flag to run without a GPU if needed, note that this
    results in much slower processing speed.

    Warning:
        The code expects the first HCP preprocessing step (hcp_pre_freesurfer)
        to have been run and finished successfully. It expects the DWI data to
        have been acquired in phase encoding reversed pairs, which should be
        present in the Diffusion folder in the sessions's root hcp folder.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_dwi_echospacing (str, default detailed below):
            Echo Spacing of DWI images in s. By default, QuNex will try to get
            this value from the imaging data.

        --use_sequence_info (str, default 'all'):
            A pipe, comma or space separated list of inline sequence
            information to use in preprocessing of specific image
            modalities.

            Example specifications:

            - `all`
                Use all present inline information for all modalities.
            - `DwellTime`
                Use DwellTime information for all modalities.
            - `T1w:all`
                Use all present inline information for T1w modality.
            - `SE:EchoSpacing`
                Use EchoSpacing information for Spin-Echo fieldmap images.
            - `none`
                Do not use inline information.

            Modalities: 'T1w', 'T2w', 'SE', 'BOLD', 'dMRi'.
            Inline information: 'TR', 'PEDirection', 'EchoSpacing' 'DwellTime',
            'ReadoutDirection'.

            If information is not specified it will not be used. More
            general specification (e.g. `all`) implies all more specific
            cases (e.g. `T1w:all`).

        --hcp_dwi_phasepos (str, default 'PA'):
            The direction of unwarping for positive phase. Can be AP,
            PA, LR, or RL. Negative phase is set automatically based on
            this setting.

        --hcp_dwi_gdcoeffs (str, default 'NONE'):
            A path to a file containing gradient distortion
            coefficients, alternatively a string describing multiple
            options (see below), or "NONE", if not used.

        --hcp_dwi_topupconfig (str, default $HCPPIPEDIR/global/config/b02b0.cnf):
            A full path to the topup configuration file to use.

        --hcp_dwi_dof (int, default 6):
            Degrees of Freedom for post eddy registration to structural images.

        --hcp_dwi_b0maxbval (int, default 50):
            Volumes with a bvalue smaller than this value will be
            considered as b0s.

        --hcp_dwi_combinedata (int, default 1):
            If JAC resampling has been used in eddy, this value determines what
            to do with the output file:

            - 2 ... include in the output all volumes uncombined (i.e. output
              file of eddy)
            - 1 ... include in the output and combine only volumes where
              both LR/RL (or AP/PA) pairs have been acquired
            - 0 ... As 1, but also include uncombined single volumes.

        --hcp_dwi_selectbestb0 (flag, optional):
            If set selects the best b0 for each phase encoding direction
            to pass on to topup rather than the default behaviour of
            using equally spaced b0's throughout the scan. The best b0
            is identified as the least distorted (i.e., most similar to
            the average b0 after registration). The flag is not set by
            default.

        --hcp_dwi_extraeddyarg (str, default ''):
            A string specifying additional arguments to pass to the
            DiffPreprocPipeline_Eddy.sh script and subsequently to the
            run_eddy.sh script and finally to the command that actually
            invokes the eddy binary. The string is to be written as a
            contiguous set of arguments to be added. Each argument
            needs to be provided together with dashes if it needs them.
            To provide multiple arguments divide them with the pipe (|)
            character, e.g.
            --hcp_dwi_extraeddyarg="--niter=8|--nvoxhp=2000".

        --hcp_dwi_name (str, default 'Diffusion'):
            Name to give DWI output directories.

        --hcp_nogpu (flag, optional):
            If specified, use the non-GPU-enabled version of eddy. The
            flag is not set by default.

        --hcp_dwi_even_slices (flag, optional):
            If set will ensure the input images to FSL's topup and eddy
            have an even number of slices by removing one slice if
            necessary. This behaviour used to be the default, but is
            now optional, because discarding a slice is incompatible
            with using slice-to-volume correction in FSL's eddy. The
            flag is not set by default.

        --hcp_dwi_posdata (str, default ''):
            Overrides the automatic QuNex's setup for the posData HCP pipelines'
            parameter. Provide a comma separated list of images with pos data.

        --hcp_dwi_negdata (str, default ''):
            Overrides the automatic QuNex's setup for the negData HCP pipelines'
            parameter. Provide a comma separated list of images with neg data.

        --hcp_dwi_dummy_bval_bvec (flag, optional):
            QuNex will create dummy bval and bvec files if they do not yet
            exist. Mainly useful when using distortion maps as part of the
            input data.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --longitudinal:
            Set this flag if you are running the longitudinal variant of this
            command.

    Output files:
        The results of this command will be present in the Diffusion folder
        in the sessions's root hcp folder.

    Notes:
        Gradient Coefficient File Specification:
            --hcp_dwi_gdcoeffs parameter can be set to either "NONE", a path to
            a specific file to use, or a string that describes, which file to
            use in which case. Each option of the string has to be divided by a
            pipe "|" character and it has to specify, which information to look
            up, a possible value, and a file to use in that case, separated by
            a colon ":" character. The information too look up needs to be
            present in the description of that session. Standard options are
            e.g.::

                institution: Yale
                device: Siemens|Prisma|123456

            Where device is formatted as "<manufacturer>|<model>|<serial number>".

            If specifying a string it also has to include a "default" option,
            which will be used in the information was not found. An example
            could be::

                "default:/data/gc1.conf|model:Prisma:/data/gc/Prisma.conf|model:Trio:/data/gc/Trio.conf"

            With the information present above, the file "/data/gc/Prisma.conf"
            would be used.

        Apptainer (Singularity) and GPU support:
            If nogpu is not provided, this command will facilitate GPUs to speed
            up processing. Since the command uses CUDA binaries, an NVIDIA GPU
            is required. To give access to CUDA drivers to the system inside the
            Apptainer (Singularity) container, you need to use the --nv flag
            of the qunex_container script.

        Mapping of QuNex parameters onto HCP Pipelines parameters:
            Below is a detailed specification about how QuNex parameters are
            mapped onto the HCP Pipelines parameters.

            ============================= ======================================
            QuNex parameter               HCPpipelines parameter
            ============================= ======================================
            ``hcp_dwi_phasepos``          ``posData``, ``negData`` and ``PEdir``
            ``hcp_dwi_echospacing``       ``echospacing``
            ``hcp_dwi_gdcoeffs``          ``gdcoeffs``
            ``hcp_dwi_dof``               ``dof``
            ``hcp_dwi_b0maxbval``         ``b0maxbval``
            ``hcp_dwi_combinedata``       ``combine-data-flag``
            ``hcp_printcom``              ``printcom``
            ``hcp_dwi_extraeddyarg``      ``extra-eddy-arg``
            ``hcp_dwi_name``              ``dwiname``
            ``hcp_dwi_selectbestb0``      ``select-best-b0``
            ``hcp_dwi_topupconfig``       ``topup-config-file``
            ``hcp_dwi_even_slices``       ``ensure-even-slices``
            ``hcp_dwi_posdata``           ``posData``
            ``hcp_dwi_negdata``           ``negData``
            ``hcp_nogpu``                 ``gpu``
            ``hcp_longitudinal_template`` ``longitudinal-template``
            ``longitudinal``              ``is-longitudinal``
            ============================= ======================================

        Use:
            Runs the Diffusion step of HCP Pipeline. It preprocesses diffusion
            weighted images (DWI). Specifically, after b0 intensity
            normalization, the b0 images of both phase encoding directions are
            used to calculate the susceptibility-induced B0 field deviations.
            The full timeseries from both phase encoding directions is used in
            the “eddy” tool for modeling of eddy current distortions and subject
            motion. Gradient distortion is corrected and the b0 image is
            registered to the T1w image using BBR. The diffusion data output
            from eddy are then resampled into 1.25mm native structural space and
            masked. Diffusion directions and the gradient deviation estimates
            are also appropriately rotated and registered into structural space.
            The function enables the use of a number of parameters to customize
            the specific preprocessing steps.

    Examples:
        Example run from the base study folder with test flag::

            qunex hcp_diffusion \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --overwrite="no" \\
                --test

        Run with scheduler, the compute node also loads the required CUDA module::

            qunex hcp_diffusion \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --overwrite="yes" \\
                --bash="module load CUDA/11.3.1" \\
                --scheduler="SLURM,time=24:00:00,cpus-per-task=1,mem-per-cpu=16000,partition=GPU,gpus=1"

        Run without a scheduler and without GPU support::

            qunex hcp_diffusion \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --overwrite="yes" \\
                --hcp_nogpu
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP DiffusionPreprocessing Pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = "Error"

    try:
        pc.doOptionsCheck(options, sinfo, "hcp_diffusion")
        doHCPOptionsCheck(options, "hcp_diffusion")
        hcp = getHCPPaths(sinfo, options)

        if "hcp" not in sinfo:
            r += (
                "\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"])
            )
            run = False

        # --- using a legacy parameter?
        if "hcp_dwi_pedir" in options:
            r += "\n---> WARNING: you are still providing the hcp_dwi_pedir parameter which has been replaced with hcp_dwi_phasepos! Please consult the documentation to see how to use it."
            r += (
                "\n---> hcp_dwi_phasepos is currently set to %s."
                % options["hcp_dwi_phasepos"]
            )

        # --- set up data
        direction = None
        pe_dir = None
        if options["hcp_dwi_phasepos"] == "PA":
            direction = {"pos": "PA", "neg": "AP"}
            pe_dir = 2
        elif options["hcp_dwi_phasepos"] == "AP":
            direction = {"pos": "AP", "neg": "PA"}
            pe_dir = 2
        elif options["hcp_dwi_phasepos"] == "LR":
            direction = {"pos": "LR", "neg": "RL"}
            pe_dir = 1
        elif options["hcp_dwi_phasepos"] == "RL":
            direction = {"pos": "RL", "neg": "LR"}
            pe_dir = 1
        else:
            r += (
                "\n---> ERROR: Invalid value of the hcp_dwi_phasepos parameter [%s]"
                % options["hcp_dwi_phasepos"]
            )
            run = False

        if run:
            # get subject's DWIs
            dwis = dict()
            for k, v in sinfo.items():
                if k.isdigit() and v["name"] == "DWI":
                    dwis[int(k)] = v["task"]

            # QuNex's automatic posData and negData setup
            has_pair = False
            if (
                options["hcp_dwi_posdata"] is None
                and options["hcp_dwi_negdata"] is None
            ):
                # get dwi files
                dwi_data = dict()
                # sort by temporal order as specified in batch
                for dwi in sorted(dwis):
                    for ddir, dext in direction.items():
                        dwi_files = glob.glob(
                            os.path.join(hcp["DWI_source"], "*_%s.nii.gz" % (dext))
                        )

                        for dwi_file in dwi_files:
                            if dwis[dwi] in dwi_file:
                                dwi_dict = {"dir": ddir, "ext": dext, "file": dwi_file}
                                dwi_data[dwis[dwi]] = dwi_dict

                                # add matching pair if it does not exist
                                opposite_dir = "pos"
                                if ddir == "pos":
                                    opposite_dir = "neg"
                                opposite_exp = direction[opposite_dir]

                                dwi_matching = dwis[dwi].replace(dext, opposite_exp)

                                if dwi_matching not in dwi_data:
                                    dwi_dict = {
                                        "dir": opposite_dir,
                                        "ext": opposite_exp,
                                        "file": "EMPTY",
                                    }
                                    dwi_data[dwi_matching] = dwi_dict
                                else:
                                    has_pair = True

                # prepare pos and neg files
                dwi_files = dict()
                for _, dwi in dwi_data.items():
                    if not has_pair and dwi["file"] == "EMPTY":
                        continue

                    if dwi["dir"] in dwi_files:
                        dwi_files[dwi["dir"]] = (
                            dwi_files[dwi["dir"]] + "@" + dwi["file"]
                        )
                    else:
                        dwi_files[dwi["dir"]] = dwi["file"]

                for ddir in ["pos", "neg"]:
                    if ddir not in dwi_files:
                        break

                    dfiles = dwi_files[ddir].split("@")

                    if dfiles and dfiles != [""] and dfiles != "EMPTY":
                        r += "\n---> The following %s direction files were found:" % (
                            ddir
                        )
                        for dfile in dfiles:
                            r += "\n     %s" % (os.path.basename(dfile))
                    else:
                        r += (
                            "\n---> ERROR: No %s direction files were found! Both images with pos and neg directions are required for hcp_diffusion. If you have data with only one direction, you can use dwi_legacy_gpu."
                            % ddir
                        )
                        run = False
                        break

                # if both dirs are missing
                if "pos" not in dwi_files and "neg" not in dwi_files:
                    r += "\n---> ERROR: No DWI data found, check your batchfile and command parameters!"
                    run = False
                elif "pos" not in dwi_files:
                    pos_data = "EMPTY"
                    neg_data = dwi_files["neg"]
                elif "neg" not in dwi_files:
                    pos_data = dwi_files["pos"]
                    neg_data = "EMPTY"
                else:
                    pos_data = dwi_files["pos"]
                    neg_data = dwi_files["neg"]

            # if both are None something is wrong
            elif (
                options["hcp_dwi_posdata"] is not None
                and options["hcp_dwi_negdata"] is None
            ) or (
                options["hcp_dwi_posdata"] is None
                and options["hcp_dwi_negdata"] is not None
            ):
                r += "\n---> ERROR: When manually overriding posData and negData, you need to set both hcp_dwi_posdata and hcp_dwi_negdata parameters. Set to EMPTY if you do not have data for one of the directions. If there are no pos/neg pairs, also set the --hcp_dwi_combinedata flag."
                run = False
            else:
                # pos
                pos_list = options["hcp_dwi_posdata"].split(",")
                pos_paths = []
                for image in pos_list:
                    if image != "EMPTY":
                        pos_paths.append(hcp["DWI_source"] + "/" + image)
                    else:
                        pos_paths.append(image)
                pos_data = "@".join(pos_paths)
                # neg
                neg_list = options["hcp_dwi_negdata"].split(",")
                neg_paths = []
                for image in neg_list:
                    if image != "EMPTY":
                        neg_paths.append(hcp["DWI_source"] + "/" + image)
                    else:
                        neg_paths.append(image)
                neg_data = "@".join(neg_paths)

        # --- lookup gdcoeffs file if needed
        gdcfile, r, run = check_gdc_coeff_file(
            options["hcp_dwi_gdcoeffs"], hcp=hcp, sinfo=sinfo, r=r, run=run
        )

        # -- check for DWI data
        dwi_found = False
        for k, v in sinfo.items():
            if k.isdigit() and v["name"] == "DWI":
                dwi_found = True

        if not dwi_found:
            r += "\n---> ERROR: No DWI files found in the batch file for one of the sessions!"
            run = False
        else:
            # -- set echospacing
            dwiinfo = [
                v for (k, v) in sinfo.items() if k.isdigit() and v["name"] == "DWI"
            ][0]

            echospacing = None
            if "EchoSpacing" in dwiinfo and checkInlineParameterUse(
                "dMRI", "EchoSpacing", options
            ):
                # echospacing read from image data
                echospacing = dwiinfo["EchoSpacing"]
                r += f"\n---> Using image specific EchoSpacing: {echospacing} s"

                # check validity
                echospacing, message = _check_dwi_echospacing(echospacing)
                r += message

            # if echospacing is none, set from parameter
            if not echospacing and "hcp_dwi_echospacing" in options:
                echospacing = options["hcp_dwi_echospacing"]
                r += f"\n---> Using study general EchoSpacing: {echospacing} s"

                # check validity
                echospacing, message = _check_dwi_echospacing(echospacing)
                r += message

            # -- check echospacing
            if not echospacing:
                r += "\n---> ERROR: QuNex was unable to acquire echospacing from the data and the parameter is not set!"
                run = False

        # path
        path = sinfo["hcp"]

        # longitudinal mode
        if options["longitudinal"]:
            studyfolder = gc.deduce_folders(options)["basefolder"]
            if not studyfolder:
                r += "\nERROR: cannot deduce the QuNex study folder from provided parameters! Please provide the sessionsfolder or the studyfolder parameter."
                run = False
            # replace path
            path = os.path.join(studyfolder, "subjects", sinfo["subject"])

        # --- build the command
        if run:
            comm = (
                '%(script)s \
                --path="%(path)s" \
                --session="%(session)s" \
                --PEdir=%(pe_dir)s \
                --posData="%(pos_data)s" \
                --negData="%(neg_data)s" \
                --echospacing-seconds="%(echospacing)s" \
                --gdcoeffs="%(gdcoeffs)s" \
                --printcom="%(printcom)s"'
                % {
                    "script": os.path.join(
                        hcp["hcp_base"],
                        "DiffusionPreprocessing",
                        "DiffPreprocPipeline.sh",
                    ),
                    "pos_data": pos_data,
                    "neg_data": neg_data,
                    "path": path,
                    "session": sinfo["id"] + options["hcp_suffix"],
                    "echospacing": echospacing,
                    "pe_dir": pe_dir,
                    "gdcoeffs": gdcfile,
                    "printcom": options["hcp_printcom"],
                }
            )

            # -- Longitudinal parameters
            if options["longitudinal"]:
                comm += "                --is-longitudinal=1"
                comm += (
                    "                --longitudinal-session="
                    + f"{sinfo['id']}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"
                )

            # -- Optional parameters
            # if there are no pairs combine-data-flag default is 2
            if options["hcp_dwi_combinedata"] is not None:
                comm += (
                    "                --combine-data-flag="
                    + options["hcp_dwi_combinedata"]
                )
            elif not has_pair:
                comm += "                --combine-data-flag=2"

            if options["hcp_dwi_b0maxbval"] is not None:
                comm += "                --b0maxbval=" + options["hcp_dwi_b0maxbval"]

            if options["hcp_dwi_dof"] is not None:
                comm += "                --dof=" + options["hcp_dwi_dof"]

            if options["hcp_dwi_extraeddyarg"] is not None:
                eddyoptions = options["hcp_dwi_extraeddyarg"].split("|")

                if eddyoptions != [""]:
                    for eddyoption in eddyoptions:
                        comm += "                --extra-eddy-arg=" + eddyoption

            if options["hcp_dwi_name"] is not None:
                comm += "                --dwiname=" + options["hcp_dwi_name"]

            if options["hcp_dwi_selectbestb0"]:
                comm += "                --select-best-b0"

            if options["hcp_dwi_topupconfig"] is not None:
                comm += (
                    "                --topup-config-file="
                    + options["hcp_dwi_topupconfig"]
                )

            if options["hcp_dwi_even_slices"]:
                comm += "                --ensure-even-slices"

            if options["hcp_nogpu"]:
                comm += "                --gpu=False"
            else:
                comm += "                --gpu=True"
                comm += "                --cuda-version=11.0"

            # create dummy bvals and bvecs if demanded
            if options["hcp_dwi_dummy_bval_bvec"]:
                # iterate over pos_data
                pos_array = pos_data.split("@")
                for pos in pos_array:
                    # bval
                    bval = pos.replace(".nii.gz", ".bval")
                    if not os.path.isfile(bval):
                        r += f"\n---> Creating dummy bval file for [{pos}]."
                        with open(bval, "w") as f:
                            f.write("0\n")

                    # bvec
                    bvec = pos.replace(".nii.gz", ".bvec")
                    if not os.path.isfile(bvec):
                        r += f"\n---> Creating dummy bvec file for [{pos}]."
                        with open(bvec, "w") as f:
                            f.write("0\n0\n0\n")

                # iterate over neg_data
                neg_array = neg_data.split("@")
                for neg in neg_array:
                    # bval
                    bval = neg.replace(".nii.gz", ".bval")
                    if not os.path.isfile(bval):
                        r += f"\n---> Creating dummy bval file for [{pos}]."
                        with open(bval, "w") as f:
                            f.write("0\n")

                    # bvec
                    bvec = neg.replace(".nii.gz", ".bvec")
                    if not os.path.isfile(bvec):
                        r += f"\n---> Creating dummy bvec file for [{pos}]."
                        with open(bvec, "w") as f:
                            f.write("0\n0\n0\n")

            # -- Report command
            if run:
                r += (
                    "\n\n------------------------------------------------------------\n"
                )
                r += "Running HCP Pipelines command via QuNex:\n\n"
                r += comm.replace("                --", "\n    --")
                r += "\n------------------------------------------------------------\n"

            # -- Test files
            tfile = None
            full_test = None
            if not options["longitudinal"]:
                tfile = os.path.join(hcp["T1w_folder"], "Diffusion", "data.nii.gz")

                if hcp["hcp_dwi_check"]:
                    full_test = {
                        "tfolder": hcp["base"],
                        "tfile": hcp["hcp_dwi_check"],
                        "fields": [("sessionid", sinfo["id"])],
                        "specfolder": options["specfolder"],
                    }

        # -- Run
        if run:
            if options["run"] == "run":
                if not options["longitudinal"] and overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                logtags = [options["logtag"]]
                if options["longitudinal"]:
                    logtags.append("long")

                r, _, report, failed = pc.runExternalForFile(
                    tfile,
                    comm,
                    "Running HCP Diffusion Preprocessing",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=logtags,
                    fullTest=full_test,
                    shell=True,
                    r=r,
                )

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(
                    tfile, full_test, "HCP Diffusion", r, overwrite=overwrite
                )
                if passed is None:
                    r += "\n---> HCP Diffusion can be run"
                    report = "HCP Diffusion can be run"
                    failed = 0

        else:
            r += "\n---> Session cannot be processed."
            report = "HCP Diffusion cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        failed = 1

    r += (
        "\n\nHCP Diffusion Preprocessing %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, (sinfo["id"], report, failed))


def _check_dwi_echospacing(echospacing):
    """
    Checks the echospacing parameter for the hcp_diffusion command.
    """
    echospacing = float(echospacing)

    # convert to milis
    echospacing_mili = float(echospacing) * 1000

    # all good
    if echospacing_mili > 0.1 and echospacing_mili < 1:
        return (echospacing, "")

    # maybe it was provided in miliseconds already
    if echospacing > 0.1 and echospacing < 1:
        echospacing = echospacing / 1000
        return (
            echospacing,
            f"\nWARNING: the provided value of echospacing seems to be in ms, converted to s [{echospacing}]!",
        )

    # maybe OK?
    if echospacing_mili > 0.01 and echospacing_mili < 10:
        return (
            echospacing,
            f"\nWARNING: the value of echospacing in seconds [{echospacing}] is out of the expected range, please check!",
        )

    # maybe OK in ms?
    if echospacing > 0.01 and echospacing < 10:
        echospacing = echospacing / 1000
        message = f"\nWARNING: the provided value of echospacing seems to be in ms, converted to s [{echospacing}]!"
        message += f"\nWARNING: the value of echospacing in seconds [{echospacing}] is out of the expected range, please check!"
        return (echospacing, message)

    # not OK
    return (
        None,
        f"\n---> ERROR: the value of echospacing in seconds [{echospacing}] is way out of the expected range!",
    )


def hcp_fmri_volume(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_fmri_volume [... processing options]``

    Runs the fMRI Volume (GenericfMRIVolumeProcessingPipeline.sh) step of HCP
    Pipeline. It preprocesses BOLD images and linearly and nonlinearly
    registers them to the MNI atlas. It makes use of the PreFS and FS steps of
    the pipeline. It enables the use of a number of parameters to customize the
    specific preprocessing steps.

    Warning:
        The code expects the first two HCP preprocessing steps
        (hcp_pre_freesurfer and hcp_freesurfer) to have been run and finished
        successfully. It also tests for the presence of fieldmap or spin-echo
        images if they were specified. It does not make a thorough check for
        PreFS and FS steps due to the large number of files.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --bolds (str, default 'all'):
            Which bold images (as they are specified in the batch.txt file) to
            process. It can be a single type (e.g. 'task'), a pipe separated
            list (e.g. 'WM|Control|rest') or 'all' to process all.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_processing_mode (str, default 'HCPStyleData'):
            Controls whether the HCP acquisition and processing guidelines
            should be treated as requirements ('HCPStyleData') or if additional
            processing functionality is allowed ('LegacyStyleData'). In this
            case running processing with slice timing correction, external BOLD
            reference, or without a distortion correction method.

        --hcp_folderstructure (str, default 'hcpls'):
            If set to 'hcpya' the folder structure used in the initial HCP Young
            Adults study is used. Specifically, the source files are stored in
            individual folders within the main 'hcp' folder in parallel with the
            working folders and the 'MNINonLinear' folder with results. If set
            to 'hcpls' the folder structure used in the HCP Life Span study is
            used. Specifically, the source files are all stored within their
            individual subfolders located in the joint 'unprocessed' folder in
            the main 'hcp' folder, parallel to the working folders and the
            'MNINonLinear' folder.

        --hcp_filename (str, default 'automated'):
            How to name the BOLD files once mapped into the hcp input folder
            structure. The default ('automated') will automatically name each
            file by their number (e.g. `BOLD_1`). The alternative
            ('userdefined') is to use the file names, which can be defined by
            the user prior to mapping (e.g. `rfMRI_REST1_AP`).

        --hcp_bold_biascorrection (str, default 'NONE'):
            Whether to perform bias correction for BOLD images. NONE, LEGACY
            or SEBASED. With SEBASED must also use hcp_bold_dcmethod.

        --hcp_bold_usejacobian (str, default 'FALSE'):
            Whether to apply the jacobian of the distortion correction to fMRI
            data.

        --hcp_bold_prefix (str, default 'BOLD'):
            The prefix to use when generating BOLD names (see --hcp_filename)
            for BOLD working folders and results.

        --hcp_bold_echospacing (float):
            Echo Spacing of BOLD images in seconds.

        --hcp_bold_sbref (str, default 'NONE'):
            Whether BOLD Reference images should be used - NONE or USE.

        --use_sequence_info (str, default 'all'):
            A pipe, comma or space separated list of inline sequence information
            to use in preprocessing of specific image modalities.

            Example specifications:

            - `all`: use all present inline information for all
              modalities,
            - 'DwellTime': use DwellTime information for all modalities,
            - `T1w:all`: use all present inline information for T1w
              modality,
            - `SE:EchoSpacing`: use EchoSpacing information for
              Spin-Echo fieldmap images.
            - `none`: do not use inline information.

            Modalities: T1w, T2w, SE, BOLD, dMRi Inline information: TR,
            PEDirection, EchoSpacing, DwellTime, ReadoutDirection.

            If information is not specified it will not be used. More general
            specification (e.g. `all`) implies all more specific cases (e.g.
            `T1w:all`).

        --hcp_bold_dcmethod (str):
            BOLD image deformation correction that should be used: TOPUP,
            TOPUP_MISMATCHED, FIELDMAP / SiemensFieldMap, GEHealthCareFieldMap,
            GEHealthCareLegacyFieldMap, PhilipsFieldMap,
            PRECOMPUTED_FIELDMAP, OnScanner or NONE.

        --hcp_bold_precomputedfmap (str, default ''):
            Path to the precomputed fieldmap image, QuNex tries to
            automatically set this if left empty and PRECOMPUTED_FIELDMAP
            is selected. This parameter is used when hcp_bold_dcmethod is set to
            PRECOMPUTED_FIELDMAP. Usually this is set automatically based
            on the FM-Real image specified in the batch file.

        --hcp_bold_precomputedfmapmag (str, default ''):
            Path to the magnitude image in the same space as
            --hcp_bold_precomputedfmap (e.g., a b=0 volume from the diffusion
            acquisition). Used for fieldmap-to-T1w registration. This parameter
            is used when hcp_bold_dcmethod is set to PRECOMPUTED_FIELDMAP.
            Usually this is set automatically based on the FM-Magnitude image
            specified in the batch file.

        --hcp_bold_echodiff (str):
            Delta TE for BOLD fieldmap images or NONE if not used.

        --hcp_bold_sephasepos (str, default ''):
            Label for the positive image of the Spin Echo Field Map pair.

        --hcp_bold_sephaseneg (str, default ''):
            Label for the negative image of the Spin Echo Field Map pair.

        --hcp_bold_unwarpdir (str, default 'y'):
            The direction of unwarping. Can be specified separately for
            LR/RL : `'LR=x|RL=-x|x'` or separately for PA/AP :
            `'PA=y|AP=y-|y-'`.

        --hcp_bold_res (str, default '2'):
            Target image resolution. 2mm recommended.

        --hcp_bold_gdcoeffs (str, default 'NONE'):
            Gradient distortion correction coefficients or NONE.

        --hcp_bold_topupconfig (str, default detailed below):
            A full path to the topup configuration file to use. Do not set if
            the default is to be used or if TOPUP distortion correction is not
            used.

        --hcp_bold_doslicetime (str, default 'FALSE'):
            Whether to do slice timing correction 'TRUE' or 'FALSE'.

        --hcp_bold_slicetimingfile (str, default 'FALSE'):
            Whether to use custom slice timing file 'TRUE' or 'FALSE'.
            You can prepare these files manually or you can use the
            functinality witin the setup_hcp command. The file will be then used
            for the --tcustom parameter of FSL slicetimer. The file should be
            located in the BOLD folder, using the same name, but with the
            `_slicetimer.txt` suffix.

        --hcp_bold_slicetimerparams (str, default ''):
            A comma or pipe separated string of parameters for FSL slicetimer.

        --hcp_bold_stcorrdir (str, default 'up'):
            The direction of slice acquisition ('up' or 'down').
            This parameter is deprecated. If specified, it will be added to
            --hcp_bold_slicetimerparams.

        --hcp_bold_stcorrint (str, default 'odd'):
            Whether slices were acquired in an interleaved fashion ('odd') or
            not ('empty').
            This parameter is deprecated. If specified, it will be added to
            --hcp_bold_slicetimerparams.

        --hcp_bold_preregistertool (str, default 'epi_reg'):
            What tool to use to preregister BOLDs before FSL BBR is 'run',
            'epi_reg' (default) or 'flirt'.

        --hcp_bold_movreg (str, default 'MCFLIRT'):
            Whether to use 'FLIRT' (usually for multiband images) or 'MCFLIRT'
            (default) for motion correction.

        --hcp_bold_movref (str, default 'independent'):
            What reference to use for movement correction ('independent',
            'first').
            This parameter is only valid when running HCPpipelines using the
            LegacyStyleData processing mode!

        --hcp_bold_seimg (str, default 'independent'):
            What image to use for spin-echo distortion correction
            ('independent' | 'first').
            This parameter is only valid when running HCPpipelines
            using the LegacyStyleData processing mode!

        --hcp_bold_refreg (str, default 'linear'):
            Whether to use only 'linear' (default) or also 'nonlinear'
            registration of motion corrected bold to reference.
            This parameter is only valid when running HCPpipelines
            using the LegacyStyleData processing mode!

        --hcp_bold_mask (str, default 'T1_fMRI_FOV'):
            Specifies what mask to use for the final bold:

            - `T1_fMRI_FOV`           ... combined T1w brain mask and
              fMRI FOV masks (the default and HCPStyleData compliant)
            - `T1_DILATED_fMRI_FOV`   ... a once dilated T1w brain based
              mask combined with fMRI FOV
            - `T1_DILATED2x_fMRI_FOV` ... a twice dilated T1w brain
              based mask combined with fMRI FOV
            - `fMRI_FOV`              ... a fMRI FOV mask.

            This parameter is only valid when running HCPpipelines
            using the LegacyStyleData processing mode!

        --hcp_wb_resample:
            Set this flag to use wb command to do volume resampling instead of
            applywarp.

        --hcp_echo_te (str, default ''):
            Comma delimited list of numbers which represent TE for each echo
            (unused for single echo).

        --hcp_bold_seechospacing (str, default ''):
            Echo Spacing or of Spin Echo Field Maps in seconds or "NONE" if not
            used. Used when hcp_bold_dcmethod is set to TOPUP_MISMATCHED.

        --hcp_bold_seunwarpdir (str, default ''):
            Phase encoding direction of the Spin Echo Field Map (x, y or NONE).
            Used when hcp_bold_dcmethod is set to TOPUP_MISMATCHED.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --longitudinal:
            Set this flag if you are running the longitudinal variant of this
            command.

        --hcp_longitudinal_subject (str, default ''):
            The subject id of the longitudinal subject. Mandatory for
            longitudinal processing.

        --hcp_longitudinal_sessions (str, default ''):
            A comma separated list of sessions for a given subject. Mandatory
            for longitudinal processing.

        --hcp_longitudinal_extract_all:
            Set this flag to extract all runs specified in hcp_tica_bolds, with
            output name matching the one from hcp_tica_mrfix_concat_name. Not
            set by default.

    Output files:
        The results of this step will be present in the MNINonLinear folder
        in the sessions's root hcp folder::

            study
            └─ sessions
               └─ subject1_session1
                  └─ hcp
                     └─ subject1_session1
                       └─ MNINonlinear
                          └─ Results
                             └─ BOLD_1

    Notes:
        These last parameters enable fine-tuning of preprocessing and deserve
        additional information. In general the defaults should be appropriate
        for multiband images, single-band can profit from specific adjustments.
        Whereas FLIRT is best used for motion registration of high-resolution
        BOLD images, lower resolution single-band images might be better motion
        aligned using MCFLIRT (--hcp_bold_movreg).

        As a movement correction target, either each BOLD can be independently
        registered to T1 image, or all BOLD images can be motion correction
        aligned to the first BOLD in the series and only that image is
        registered to the T1 structural image (--hcp_bold_moveref). Do note
        that in this case also distortion correction will be computed for the
        first BOLD image in the series only and applied to all subsequent BOLD
        images after they were motion-correction aligned to the first BOLD.

        Similarly, for distortion correction, either the last preceding
        spin-echo image pair can be used (independent) or only the first
        spin-echo pair is used for all BOLD images (first; --hcp_bold_seimg).
        Do note that this also affects the previous motion correction target
        setting. If independent spin-echo pairs are used, then the first BOLD
        image after a new spin-echo pair serves as a new starting
        motion-correction reference.

        If there is no spin-echo image pair and TOPUP correction was requested,
        an error will be reported and processing aborted. If there is no
        preceding spin-echo pair, but there is at least one following the BOLD
        image in question, the first following spin-echo pair will be used and
        no error will be reported. The spin-echo pair used is reported in the
        log.

        When BOLD images are registered to the first BOLD in the series, due to
        larger movement between BOLD images it might be advantageous to use
        also nonlinear alignment to the first bold reference image
        (--hcp_bold_refreg).

        Lastly, for lower resolution BOLD images it might be better not to use
        subject specific T1 image based brain mask, but rather a mask generated
        on the BOLD image itself or based on the dilated standard MNI brain
        mask.

        Gradient coefficient file specification:
            `--hcp_bold_gdcoeffs` parameter can be set to either 'NONE', a path
            to a specific file to use, or a string that describes, which file
            to use in which case. Each option of the string has to be divided
            by a pipe '|' character and it has to specify, which information to
            look up, a possible value, and a file to use in that case,
            separated by a colon ':' character. The information too look up
            needs to be present in the description of that session. Standard
            options are e.g.::

                institution: Yale
                device: Siemens|Prisma|123456

            Where device is formatted as ``<manufacturer>|<model>|<serial number>``.

            If specifying a string it also has to include a `default` option,
            which will be used in the information was not found. An example
            could be::

                "default:/data/gc1.conf|model:Prisma:/data/gc/Prisma.conf|model:Trio:/data/gc/Trio.conf"

            With the information present above, the file
            `/data/gc/Prisma.conf` would be used.

        Slice timing correction:
            Slice timing correction is performed using FSL slicetimer. For the
            correction to be done correctly, the data needs to be carefully
            inspected and the ``hcp_bold_slicetimerparams`` parameter has to be
            prepared with the valid information. For complex slice timing
            acquisition (e.g., multiband acquisition) it is best to prepare a
            slice timing file. The slice timing file has to be saved in the
            same folder as the respective BOLD file. It has to be named the
            same as the BOLD file with ``_slicetimer.txt`` tail and extension.
            The slice timing file can be prepared automatically using the
            ```setup_hcp`` <../../api/gmri/setup_hcp.rst>`__ command, if JSON
            sidecar files for BOLD images exist and have the correct slice
            timing information. Alternatively ``prepare_slice_timing`` command
            can be used. See the respective inline help for more information.

        Movement and spin-echo references:
            Whereas most of the options should be clear, the ones specifying
            movement and spin-echo reference present the most significant
            change from the original way fMRIVolume is run and should be
            explained more in detail. Originally, each fMRI image is processed
            independently and registered to the individual's T1w image. Whereas
            this works well for high-resolution multiband fMRI images, in our
            experience the results are not optimal for legacy (non-multiband)
            fMRI images of lower resolution. Due to slight changes in the
            optimal registration to T1w image, fMRI images would not be
            optimally spatially aligned to one another, which would lead to
            increased within-subject noise across fMRI images. Using the
            ``hcp_bold_movref`` parameter it is possible to instead align the
            first fMRI image to the T1w image and then align all the following
            fMRI images to the first fMRI rather than registering each of them
            separately and independently to T1w image.

            The original registration procedure (the steps in brackets are
            based on previously completed steps):

            ::

               bold1 -> T1w [-> MNI atlas]
               bold2 -> T1w [-> MNI atlas]
               bold3 -> T1w [-> MNI atlas]

            can be changed to:

            ::

               bold1 -> T1w [-> MNI atlas]
               bold2 -> bold1 [-> T1w -> MNI atlas]
               bold3 -> bold1 [-> T1w -> MNI atlas]

            To use the original procedure and align each BOLD independently to
            T1w image, the ``hcp_bold_movref`` parameter has to be set to
            ``independent``. To use the modified procedure set the parameter to
            ``first``. To remove additional mismatches that can arise due to
            changes in distortion because of larger head movements between
            acquisition of individual BOLD images, linear registration of
            references between BOLD images can be enhanced with additional
            nonlinear registration. To make use of the latter, set the
            ``hcp_bold_refreg`` parameter to ``nonlinear`` instead of
            ``linear``. Note that using the non-linear registration is not
            compliant with the ``HCPStyleData`` processing mode.

            The additional advantage of registration to the first BOLD image is
            reduction in processing as the previously computed distortion
            correction can be re-used. This can lead to noticeable reduction in
            processing time.

            When recording is interrupted for any reason (e.g. subject had to go
            to a toilet, or the recording was completed in two sessions), a
            novel spin-echo image might be acquired to account for movement and
            allow better registration with BOLD images. In such a case, if
            ``hcp_bold_seimg`` parameter is set to ``independent``, the
            modified HCP pipeline will use for each BOLD image the last
            spin-echo recorded before the BOLD image in question. In this case,
            if BOLD registration target is set to the first BOLD image (using
            ``hcp_bold_movref``), the BOLD image registration target will be
            also changed to the fist BOLD image after the new spin-echo pair.
            Specifically with ``independent`` ``hcp_bold_seimg`` an example
            sequence might be::

               se-pair1
               bold1 -> se-pair1 -> T1w [-> MNI atlas]
               bold2 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold3 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               se-pair2
               bold4 -> se-pair2 -> T1w [-> MNI atlas]
               bold5 -> bold4 [se-pair2 -> T1w -> MNI atlas]
               bold6 -> bold4 [se-pair2 -> T1w -> MNI atlas]

            If the ``hcp_bold_seimg`` parameter is set to ``first``, only the
            first spin-echo pair of images will be considered and all others
            will be ignored. The above sequence would then be changed to::

               se-pair1
               bold1 -> se-pair1 -> T1w [-> MNI atlas]
               bold2 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold3 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               se-pair2
               bold4 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold5 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold6 -> bold1 [se-pair1 -> T1w -> MNI atlas]

            In the rare cases, where a spin-echo pair of images would be
            recorded after the first BOLD image, the first spin-echo image
            found after the BOLD image would be used for distortion correction.
            An example of such a situation might be the following sequence::

               bold1 -> se-pair1 -> T1w [-> MNI atlas]
               bold2 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold3 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               se-pair1
               bold4 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold5 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold6 -> bold1 [se-pair1 -> T1w -> MNI atlas]

            In our testing, using the following combination of settings resulted
            in smallest differences between registered BOLD legacy
            (non-multiband) images::

               # batch.txt settings
               --hcp_bold_movreg    : MCFLIRT
               --hcp_bold_movref    : first
               --hcp_bold_seimg     : first
               --hcp_bold_refreg    : nonlinear
               --hcp_bold_mask      : T1_DILATED2x_fMRI_FOV

            Do note that the best performing settings are study dependent and need
            to be evaluated on a study by study basis.

        hcp_fmri_volume parameter mapping:

            =============================== =======================
            QuNex parameter                 HCPpipelines parameter
            =============================== =======================
            ``hcp_bold_res``                ``fmrires``
            ``hcp_bold_biascorrection``     ``biascorrection``
            ``hcp_bold_echodiff``           ``echodiff``
            ``hcp_gdcoeffs``                ``gdcoeffs``
            ``hcp_bold_dcmethod``           ``dcmethod``
            ``hcp_bold_echospacing``        ``echospacing``
            ``hcp_bold_unwarpdir``          ``unwarpdir``
            ``hcp_bold_topupconfig``        ``topupconfig``
            ``hcp_bold_dof``                ``dof``
            ``hcp_printcom``                ``printcom``
            ``hcp_bold_usejacobian``        ``usejacobian``
            ``hcp_bold_movreg``             ``mctype``
            ``hcp_bold_preregistertool``    ``preregistertool``
            ``hcp_processing_mode``         ``processing-mode``
            ``hcp_bold_doslicetime``        ``slicetimerparams``
            ``hcp_bold_slicetimerparams``   ``slicetimerparams``
            ``hcp_bold_slicetimingfile``    ``slicetimerparams``
            ``hcp_bold_stcorrdir``          ``slicetimerparams``
            ``hcp_bold_stcorrint``          ``slicetimerparams``
            ``hcp_bold_refreg``             ``fmrirefreg``
            ``hcp_bold_mask``               ``fmrimask``
            ``hcp_bold_seunwarpdir``        ``seunwarpdir``
            ``hcp_bold_seechospacing``      ``seechospacing``
            ``hcp_bold_precomputedfmap``    ``precomputedfmap``
            ``hcp_bold_precomputedfmapmag`` ``precomputedfmapmag``
            ``wb-resample``                 ``hcp_wb_resample``
            ``echoTE``                      ``hcp_echo_te``
            ``matlab-run-mode``             ``hcp_matlab_mode``
            ``hcp_longitudinal_template``   ``longitudinal-template``
            ``longitudinal``                ``is-longitudinal``
            =============================== =======================

    Examples:
        Example run from the base study folder with test flag::

            qunex hcp_fmri_volume  \\
                --batchfile="processing/batch.txt"  \\
                --sessionsfolder="sessions"  \\
                --parsessions="10"  \\
                --parelements="4"  \\
                --overwrite="no"  \\
                --test

        Run using absolute paths with additional options and scheduler::

            qunex hcp_fmri_volume  \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"
                --sessionsfolder="<path_to_study_folder>/sessions"  \\
                --parsessions="4"  \\
                --parelements="2"  \\
                --hcp_bold_doslicetime="TRUE"  \\
                --hcp_bold_movereg="MCFLIRT"  \\
                --hcp_bold_moveref="first"  \\
                --hcp_bold_mask="T1_DILATED2x_fMRI_FOV"  \\
                --overwrite="yes"  \\
                --scheduler="SLURM,time=24:00:00,cpus-per-task=2,mem-per-cpu=1250,partition=day"

        Additional examples::

            qunex hcp_fmri_volume \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10

        ::

            qunex hcp_fmri_volume \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --hcp_bold_movref=first \\
                --hcp_bold_seimg=first \\
                --hcp_bold_refreg=nonlinear \\
                --hcp_bold_mask=DILATED

    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP fMRI Volume pipeline [%s] ... " % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # mandatory check
        if not options["hcp_bold_dcmethod"]:
            raise ge.CommandFailed(
                "hcp_fmri_volume",
                "... the hcp_bold_dcmethod parameter needs to be set manually! Since QuNex cannot robustly extract the information needed to set this from the data, you need to set this parameter by yourself.",
            )

        # --- Base settings
        pc.doOptionsCheck(options, sinfo, "hcp_fmri_volume")
        doHCPOptionsCheck(options, "hcp_fmri_volume")
        hcp = getHCPPaths(sinfo, options)

        # --- bold filtering not yet supported!
        # btargets = options['bolds'].split("|")

        # --- run checks
        if "hcp" not in sinfo:
            r += (
                "\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"])
            )
            run = False

        # -> Pre FS results
        if os.path.exists(
            os.path.join(hcp["T1w_folder"], "T1w_acpc_dc_restore_brain.nii.gz")
        ):
            r += "\n---> PreFS results present."
        else:
            r += "\n---> ERROR: Could not find PreFS processing results."
            run = False

        # -> FS results
        tfolder = hcp["FS_folder"]

        if os.path.exists(os.path.join(tfolder, "mri", "aparc+aseg.mgz")):
            r += "\n---> FS results present."
        else:
            r += "\n---> ERROR: Could not find Freesurfer processing results."
            run = False

        # -> PostFS results
        tfile = os.path.join(
            hcp["hcp_nonlin"],
            "fsaverage_LR32k",
            sinfo["id"] + options["hcp_suffix"] + ".32k_fs_LR.wb.spec",
        )

        if os.path.exists(tfile):
            r += "\n---> PostFS results present."
        else:
            r += "\n---> ERROR: Could not find PostFS processing results."
            run = False

        # -> lookup gdcoeffs file if needed
        gdcfile, r, run = check_gdc_coeff_file(
            options["hcp_bold_gdcoeffs"], hcp=hcp, sinfo=sinfo, r=r, run=run
        )

        # -> default parameter values
        spinP = 0
        spinN = 0
        spinNeg = ""  # AP or LR
        spinPos = ""  # PA or RL
        refimg = "NONE"
        futureref = "NONE"
        topupconfig = ""
        orient = ""
        fmmag = "NONE"
        fmphase = "NONE"
        fmcombined = "NONE"
        fmprecomputed = "NONE"
        fmprecomputedmag = "NONE"

        # -> Check for SE images
        sepresent = []
        sepairs = {}
        sesettings = False

        # check parameters values
        if options["hcp_bold_biascorrection"] not in ["LEGACY", "SEBASED", "NONE"]:
            r += f"\n---> ERROR: invalid value for the hcp_bold_biascorrection parameter {options['hcp_bold_biascorrection']}!"
            run = False

        if options["hcp_bold_dcmethod"].lower() not in [
            "topup",
            "topup_mismatched",
            "fieldmap",
            "siemensfieldmap",
            "philipsfieldmap",
            "gehealthcarefieldmap",
            "gehealthcarelegacyfieldmap",
            "precomputed_fieldmap",
            "onscanner",
            "none",
        ]:
            r += f"\n---> ERROR: invalid value for the hcp_bold_dcmethod parameter {options['hcp_bold_dcmethod']}!"
            run = False

        if options["hcp_bold_dcmethod"].lower() in ["topup", "topup_mismatched"]:
            # -- spin echo settings
            sesettings = True
            for p in [
                "hcp_bold_sephaseneg",
                "hcp_bold_sephasepos",
            ]:
                if not options[p]:
                    r += f"\nERROR: {p} parameter not set! It needs to be set manually as QuNex cannot infer it from the data in a robust manner."
                    boldok = False
                    sesettings = False
                    run = False

            if sesettings:
                r += "\n---> Looking for spin echo fieldmap set images [%s/%s]." % (
                    options["hcp_bold_sephasepos"],
                    options["hcp_bold_sephaseneg"],
                )

                for senum in range(50):
                    spinok = False

                    # check if folder exists
                    sepath = glob.glob(
                        os.path.join(hcp["source"], "SpinEchoFieldMap%d*" % (senum))
                    )
                    if sepath:
                        sepath = sepath[0]
                        r += "\n     ... identified folder %s" % (
                            os.path.basename(sepath)
                        )
                        # get all *.nii.gz files in that folder
                        images = glob.glob(os.path.join(sepath, "*.nii.gz"))

                        # variable for checking se status
                        spinok = True
                        spinPos, spinNeg = None, None

                        # search in images
                        for i in images:
                            # look for phase positive
                            if "_" + options["hcp_bold_sephasepos"] in os.path.basename(
                                i
                            ):
                                spinPos = i
                                r, spinok = pc.checkForFile2(
                                    r,
                                    spinPos,
                                    "\n     ... phase positive %s spin echo fieldmap image present"
                                    % (options["hcp_bold_sephasepos"]),
                                    "\n         ERROR: %s spin echo fieldmap image missing!"
                                    % (options["hcp_bold_sephasepos"]),
                                    status=spinok,
                                )
                            # look for phase negative
                            elif "_" + options[
                                "hcp_bold_sephaseneg"
                            ] in os.path.basename(i):
                                spinNeg = i
                                r, spinok = pc.checkForFile2(
                                    r,
                                    spinNeg,
                                    "\n     ... phase negative %s spin echo fieldmap image present"
                                    % (options["hcp_bold_sephaseneg"]),
                                    "\n         ERROR: %s spin echo fieldmap image missing!"
                                    % (options["hcp_bold_sephaseneg"]),
                                    status=spinok,
                                )

                        if not all([spinPos, spinNeg]):
                            r += (
                                "\n---> ERROR: Either one of both pairs of SpinEcho images are missing in the %s folder! Please check your data or settings!"
                                % (os.path.basename(sepath))
                            )
                            spinok = False

                    if spinok:
                        sepresent.append(senum)
                        sepairs[senum] = {"spinPos": spinPos, "spinNeg": spinNeg}

            # ---> check for topupconfig
            if (
                options["hcp_bold_topupconfig"]
                and options["hcp_bold_topupconfig"] != ""
            ):
                topupconfig = options["hcp_bold_topupconfig"]
                if not os.path.exists(options["hcp_bold_topupconfig"]):
                    topupconfig = os.path.join(
                        hcp["hcp_Config"], options["hcp_bold_topupconfig"]
                    )
                    if not os.path.exists(topupconfig):
                        r += (
                            "\n---> ERROR: Could not find TOPUP configuration file: %s."
                            % (options["hcp_bold_topupconfig"])
                        )
                        run = False
                    else:
                        r += "\n     ... TOPUP configuration file present"
                else:
                    r += "\n     ... TOPUP configuration file present"
            else:
                topupconfig = ""

        # --- Process unwarp direction
        if options["hcp_bold_dcmethod"].lower() in [
            "topup",
            "topup_mismatched",
            "fieldmap",
            "siemensfieldmap",
            "philipsfieldmap",
            "gehealthcarefieldmap",
            "gehealthcarelegacyfieldmap",
            "precomputed_fieldmap",
        ]:
            unwarpdirs = [
                [f.strip() for f in e.strip().split("=")]
                for e in options["hcp_bold_unwarpdir"].split("|")
            ]
            unwarpdirs = [["default", e[0]] if len(e) == 1 else e for e in unwarpdirs]
            unwarpdirs = dict(unwarpdirs)
        else:
            unwarpdirs = {"default": ""}

        # --- Get sorted bold numbers
        bolds, bskip, report["boldskipped"], r = pc.use_or_skip_bold(sinfo, options, r)
        if len(bolds) == 0:
            r += (
                "\n---> ERROR: No BOLD images found for session %s! Check your data or the contents of the batch file."
                % (sinfo["id"])
            )
            run = False

        _build_skipped_report(report, bskip, options)

        # --- Preprocess
        boldsData = []

        firstSE = None
        if bolds:
            firstSE = bolds[0].get("se", None)

        for boldinfo in bolds:
            printbold, boldtarget, boldsource = pc.get_bold_names(boldinfo, options)

            r += "\n\n---> %s BOLD %s" % (
                pc.action(
                    "Preprocessing settings (unwarpdir, refimage, moveref, seimage) for",
                    options["run"],
                ),
                printbold,
            )
            boldok = True

            # ---> Check for and prepare distortion correction parameters
            echospacing = ""
            unwarpdir = ""

            dcset = options["hcp_bold_dcmethod"].lower() in [
                "topup",
                "topup_mismatched",
                "fieldmap",
                "siemensfieldmap",
                "philipsfieldmap",
                "gehealthcarefieldmap",
                "gehealthcarelegacyfieldmap",
                "precomputed_fieldmap",
            ]

            # --- set unwarpdir and orient
            if "o" in boldinfo:
                orient = "_" + boldinfo["o"]
                if dcset:
                    unwarpdir = unwarpdirs.get(boldinfo["o"])
                    if unwarpdir is None:
                        r += (
                            "\n     ... ERROR: No unwarpdir is defined for %s! Please check hcp_bold_unwarpdir parameter!"
                            % (boldinfo["o"])
                        )
                        boldok = False
            elif "phenc" in boldinfo:
                orient = "_" + boldinfo["phenc"]
                if dcset:
                    unwarpdir = unwarpdirs.get(boldinfo["phenc"])
                    if unwarpdir is None:
                        r += (
                            "\n     ... ERROR: No unwarpdir is defined for %s! Please check hcp_bold_unwarpdir parameter!"
                            % (boldinfo["phenc"])
                        )
                        boldok = False
            elif "PEDirection" in boldinfo and checkInlineParameterUse(
                "BOLD", "PEDirection", options
            ):
                if boldinfo["PEDirection"] in PEDirMap:
                    orient = "_" + PEDirMap[boldinfo["PEDirection"]]
                    if dcset:
                        unwarpdir = boldinfo["PEDirection"]
                else:
                    r += (
                        "\n     ... ERROR: Invalid PEDirection specified [%s]! Please check sequence specific PEDirection value!"
                        % (boldinfo["PEDirection"])
                    )
                    boldok = False
            else:
                orient = ""
                if dcset:
                    unwarpdir = unwarpdirs.get("default")
                    if unwarpdir is None:
                        r += "\n     ... ERROR: No default unwarpdir is set! Please check hcp_bold_unwarpdir parameter!"
                        boldok = False

            if orient:
                r += "\n     ... phase encoding direction: %s" % (orient[1:])
            else:
                r += "\n     ... phase encoding direction not specified"

            if dcset:
                r += "\n     ... unwarp direction: %s" % (unwarpdir)

            # --- check for bold image
            if "filename" in boldinfo and options["hcp_filename"] == "userdefined":
                boldroot = boldinfo["filename"]
            else:
                boldroot = boldsource + orient

            boldimgs = []
            boldimgs.append(
                os.path.join(
                    hcp["source"],
                    "%s%s" % (boldroot, options["fctail"]),
                    "%s_%s.nii.gz" % (sinfo["id"], boldroot),
                )
            )

            # -- set echospacing
            if dcset:
                if "EchoSpacing" in boldinfo and checkInlineParameterUse(
                    "BOLD", "EchoSpacing", options
                ):
                    echospacing = boldinfo["EchoSpacing"]
                    r += "\n     ... using image specific EchoSpacing: %s s" % (
                        echospacing
                    )
                elif options["hcp_bold_echospacing"]:
                    echospacing = options["hcp_bold_echospacing"]
                    r += "\n     ... using study general EchoSpacing: %s s" % (
                        echospacing
                    )
                else:
                    # try to set from the JSON sidecar
                    json_sidecar = boldimgs[0].replace(".nii.gz", ".json")
                    if os.path.exists(json_sidecar):
                        r += "\n     ... trying to set hcp_bold_echospacing from the JSON sidecar"
                        with open(json_sidecar, "r") as file:
                            sidecar_data = json.load(file)
                            if "EffectiveEchoSpacing" in sidecar_data:
                                echospacing = sidecar_data["EffectiveEchoSpacing"]
                                r += f"\n     ... hcp_bold_echospacing set to {echospacing}"

                    if not options["hcp_bold_echospacing"]:
                        echospacing = ""
                        r += "\n---> ERROR: EchoSpacing is not set! Please review parameter file."
                        boldok = False

            # --- check for spin-echo-fieldmap image
            if (
                options["hcp_bold_dcmethod"].lower() in ["topup", "topup_mismatched"]
                and sesettings
            ):
                if not sepresent:
                    r += "\n     ... ERROR: No spin echo fieldmap set images present!"
                    boldok = False

                elif options["hcp_bold_seimg"] == "first":
                    if firstSE is None:
                        spinN = int(sepresent[0])
                        r += (
                            "\n     ... using the first recorded spin echo fieldmap set %d"
                            % (spinN)
                        )
                    else:
                        spinN = int(firstSE)
                        r += (
                            "\n     ... using the spin echo fieldmap set for the first bold run, %d"
                            % (spinN)
                        )
                    spinNeg = sepairs[spinN]["spinNeg"]
                    spinPos = sepairs[spinN]["spinPos"]

                else:
                    spinN = False
                    if "se" in boldinfo:
                        spinN = int(boldinfo["se"])
                    else:
                        for sen in sepresent:
                            if sen <= boldinfo["bold_number"]:
                                spinN = sen
                            elif not spinN:
                                spinN = sen

                    spinNeg = sepairs[spinN]["spinNeg"]
                    spinPos = sepairs[spinN]["spinPos"]
                    r += "\n     ... using spin echo fieldmap set %d" % (spinN)
                    r += "\n         -> SE Positive image : %s" % (
                        os.path.basename(spinPos)
                    )
                    r += "\n         -> SE Negative image : %s" % (
                        os.path.basename(spinNeg)
                    )

                # -- are we using a new SE image?
                if spinN != spinP:
                    spinP = spinN
                    futureref = "NONE"

            # --- check for Siemens double TE-fieldmap image
            elif options["hcp_bold_biascorrection"].lower() != "sebased" and options[
                "hcp_bold_dcmethod"
            ].lower() in [
                "fieldmap",
                "siemensfieldmap",
            ]:
                fmnum = boldinfo.get("fm", None)
                if fmnum is None:
                    r += (
                        "\n---> ERROR: No fieldmap number specified for the BOLD image!"
                    )
                    run = False
                else:
                    fieldok = True
                    for i, v in hcp["fieldmap"].items():
                        if isinstance(hcp["fieldmap"][i]["magnitude"], list):
                            r, fieldok = pc.checkForFile2(
                                r,
                                hcp["fieldmap"][i]["magnitude"][0],
                                "\n     ... Siemens fieldmap magnitude image %d present "
                                % (i),
                                "\n     ... ERROR: Siemens fieldmap magnitude image %d missing!"
                                % (i),
                                status=fieldok,
                            )
                            r, fieldok = pc.checkForFile2(
                                r,
                                hcp["fieldmap"][i]["magnitude"][1],
                                "\n     ... Siemens fieldmap magnitude image %d present "
                                % (i),
                                "\n     ... ERROR: Siemens fieldmap magnitude image %d missing!"
                                % (i),
                                status=fieldok,
                            )
                        else:
                            r, fieldok = pc.checkForFile2(
                                r,
                                hcp["fieldmap"][i]["magnitude"],
                                "\n     ... Siemens fieldmap magnitude image %d present "
                                % (i),
                                "\n     ... ERROR: Siemens fieldmap magnitude image %d missing!"
                                % (i),
                                status=fieldok,
                            )

                        r, fieldok = pc.checkForFile2(
                            r,
                            hcp["fieldmap"][i]["phase"],
                            "\n     ... Siemens fieldmap phase image %d present " % (i),
                            "\n     ... ERROR: Siemens fieldmap phase image %d missing!"
                            % (i),
                            status=fieldok,
                        )
                        boldok = boldok and fieldok
                    if not pc.is_number(echospacing):
                        fieldok = False
                        r += (
                            '\n     ... ERROR: hcp_bold_echospacing not defined correctly: "%s"!'
                            % (options["hcp_bold_echospacing"])
                        )

                    # try to set hcp_bold_echodiff from the JSON sidecar if not yet set
                    if (
                        not options["hcp_bold_echodiff"]
                        or options["hcp_bold_echodiff"] == "NONE"
                    ):
                        fmfolder = os.path.join(
                            hcp["source"],
                            "FieldMap%s%s" % (fmnum, options["fctail"]),
                        )

                        fmap_json = glob.glob(os.path.join(fmfolder, "*Phase.json"))

                        if len(fmap_json) != 0:
                            fmap_json = fmap_json[0]
                            json_sidecar = os.path.join(fmfolder, fmap_json)

                            if os.path.exists(json_sidecar):
                                r += "\n     ... Trying to set hcp_echodiff from the JSON sidecar."
                                with open(json_sidecar, "r") as file:
                                    sidecar_data = json.load(file)
                                    if (
                                        "EchoTime1" in sidecar_data
                                        and "EchoTime2" in sidecar_data
                                    ):
                                        echodiff = (
                                            sidecar_data["EchoTime2"]
                                            - sidecar_data["EchoTime1"]
                                        )
                                        # from s to ms
                                        echodiff = echodiff * 1000
                                        options["hcp_bold_echodiff"] = (
                                            f"{echodiff:.10f}"
                                        )
                                        r += f"\n     ... hcp_bold_echodiff set to {options['hcp_bold_echodiff']}"
                            else:
                                r += "\n---> hcp_bold_echodiff not provided and not found in the JSON sidecar, setting it to NONE."
                                options["hcp_bold_echodiff"] = None
                        else:
                            r += "\n---> JSON sidecar not found, setting hcp_bold_echodiff to NONE."
                            options["hcp_bold_echodiff"] = None

                    if not pc.is_number(options["hcp_bold_echodiff"]):
                        fieldok = False
                        r += (
                            '\n     ... ERROR: hcp_bold_echodiff not defined correctly: "%s"!'
                            % (options["hcp_bold_echodiff"])
                        )
                    boldok = boldok and fieldok
                    fmmag = hcp["fieldmap"][int(fmnum)]["magnitude"]
                    if isinstance(fmmag, list):
                        fmmag = "@".join(fmmag)
                    fmphase = hcp["fieldmap"][int(fmnum)]["phase"]
                    fmcombined = None

            # --- check for GE legacy fieldmap image
            elif (
                options["hcp_bold_biascorrection"].lower() != "sebased"
                and options["hcp_bold_dcmethod"].lower() == "gehealthcarelegacyfieldmap"
            ):
                fmnum = boldinfo.get("fm", None)
                if fmnum is None:
                    r += (
                        "\n---> ERROR: No fieldmap number specified for the BOLD image!"
                    )
                    run = False
                else:
                    fieldok = True
                    for i, v in hcp["fieldmap"].items():
                        r, fieldok = pc.checkForFile2(
                            r,
                            hcp["fieldmap"][i]["GE"],
                            "\n     ... GeneralElectric legacy fieldmap image %d present "
                            % (i),
                            "\n     ... ERROR: GeneralElectric legacy fieldmap image %d missing!"
                            % (i),
                            status=fieldok,
                        )
                        boldok = boldok and fieldok
                    fmmag = None
                    fmphase = None
                    fmcombined = hcp["fieldmap"][int(fmnum)]["GE"]

            # --- check for GE double TE-fieldmap image
            elif (
                options["hcp_bold_biascorrection"].lower() != "sebased"
                and options["hcp_bold_dcmethod"].lower() == "gehealthcarefieldmap"
            ):
                fmnum = boldinfo.get("fm", None)
                if fmnum is None:
                    r += (
                        "\n---> ERROR: No fieldmap number specified for the BOLD image!"
                    )
                    run = False
                else:
                    fieldok = True
                    for i, v in hcp["fieldmap"].items():
                        r, fieldok = pc.checkForFile2(
                            r,
                            hcp["fieldmap"][i]["magnitude"],
                            "\n     ... GE fieldmap magnitude image %d present " % (i),
                            "\n     ... ERROR: GE fieldmap magnitude image %d missing!"
                            % (i),
                            status=fieldok,
                        )
                        r, fieldok = pc.checkForFile2(
                            r,
                            hcp["fieldmap"][i]["phase"],
                            "\n     ... GE fieldmap phase image %d present " % (i),
                            "\n     ... ERROR: GE fieldmap phase image %d missing!"
                            % (i),
                            status=fieldok,
                        )
                        boldok = boldok and fieldok
                    if not pc.is_number(echospacing):
                        fieldok = False
                        r += (
                            '\n     ... ERROR: hcp_bold_echospacing not defined correctly: "%s"!'
                            % (options["hcp_bold_echospacing"])
                        )
                    boldok = boldok and fieldok
                    fmmag = hcp["fieldmap"][int(fmnum)]["magnitude"]
                    fmphase = hcp["fieldmap"][int(fmnum)]["phase"]
                    fmcombined = None

            # --- check for Philips double TE-fieldmap image
            elif (
                options["hcp_bold_biascorrection"].lower() != "sebased"
                and options["hcp_bold_dcmethod"].lower() == "philipsfieldmap"
            ):
                fmnum = boldinfo.get("fm", None)
                if fmnum is None:
                    r += (
                        "\n---> ERROR: No fieldmap number specified for the BOLD image!"
                    )
                    run = False
                else:
                    fieldok = True
                    for i, v in hcp["fieldmap"].items():
                        r, fieldok = pc.checkForFile2(
                            r,
                            hcp["fieldmap"][i]["magnitude"],
                            "\n     ... Philips fieldmap magnitude image %d present "
                            % (i),
                            "\n     ... ERROR: Philips fieldmap magnitude image %d missing!"
                            % (i),
                            status=fieldok,
                        )
                        r, fieldok = pc.checkForFile2(
                            r,
                            hcp["fieldmap"][i]["phase"],
                            "\n     ... Philips fieldmap phase image %d present " % (i),
                            "\n     ... ERROR: Philips fieldmap phase image %d missing!"
                            % (i),
                            status=fieldok,
                        )
                        boldok = boldok and fieldok
                    if not pc.is_number(echospacing):
                        fieldok = False
                        r += (
                            '\n     ... ERROR: hcp_bold_echospacing not defined correctly: "%s"!'
                            % (options["hcp_bold_echospacing"])
                        )
                    boldok = boldok and fieldok
                    fmmag = hcp["fieldmap"][int(fmnum)]["magnitude"]
                    fmphase = hcp["fieldmap"][int(fmnum)]["phase"]
                    fmcombined = None

            # --- check for real fieldmap image
            elif (
                options["hcp_bold_biascorrection"].lower() != "sebased"
                and options["hcp_bold_dcmethod"].lower() == "precomputed_fieldmap"
            ):
                if options["hcp_bold_precomputedfmap"] is not None:
                    if not os.path.exists(options["hcp_bold_precomputedfmap"]):
                        r += (
                            "\n---> ERROR: Could not find precomputed fieldmap image specified in hcp_bold_precomputedfmap parameter: %s."
                            % (options["hcp_bold_precomputedfmap"])
                        )
                        fieldok = False
                    else:
                        r += "\n     ... real fieldmap image present"
                        fieldok = True
                    boldok = boldok and fieldok
                    fmprecomputed = options["hcp_bold_precomputedfmap"]
                    fmmag = None
                    fmphase = None
                    fmcombined = None
                else:
                    fmnum = boldinfo.get("fm", None)
                    if fmnum is None:
                        r += "\n---> ERROR: No fieldmap number specified for the BOLD image!"
                        run = False
                    else:
                        fieldok = True
                        for i, v in hcp["fieldmap"].items():
                            r, fieldok = pc.checkForFile2(
                                r,
                                hcp["fieldmap"][i]["Real"],
                                "\n     ... Real fieldmap image %d present " % (i),
                                "\n     ... ERROR: Real fieldmap image %d missing!"
                                % (i),
                                status=fieldok,
                            )
                            boldok = boldok and fieldok
                        if not pc.is_number(echospacing):
                            fieldok = False
                            r += (
                                '\n     ... ERROR: hcp_bold_echospacing not defined correctly: "%s"!'
                                % (options["hcp_bold_echospacing"])
                            )
                        boldok = boldok and fieldok
                        fmprecomputed = hcp["fieldmap"][int(fmnum)]["Real"]
                        fmmag = None
                        fmphase = None
                        fmcombined = None

                # --- check for precomputedfmapmag
                if options["hcp_bold_precomputedfmapmag"] is not None:
                    # --- user provided a path to a magnitude image
                    if os.path.exists(options["hcp_bold_precomputedfmapmag"]):
                        fmprecomputedmag = options["hcp_bold_precomputedfmapmag"]
                        r += (
                            "\n     ... precomputed fieldmap magnitude image present: %s"
                            % (fmprecomputedmag)
                        )
                    else:
                        r += (
                            "\n---> ERROR: Could not find precomputed fieldmap magnitude image specified in the hcp_bold_precomputedfmapmag parameter: %s."
                            % (options["hcp_bold_precomputedfmapmag"])
                        )
                        boldok = False
                else:
                    # --- try to auto-detect from fieldmap dict using fm number from bold info
                    fmnum_mag = boldinfo.get("fm", None)
                    if (
                        fmnum_mag is not None
                        and int(fmnum_mag) in hcp["fieldmap"]
                        and "Magnitude" in hcp["fieldmap"][int(fmnum_mag)]
                    ):
                        auto_precomputedfmapmag = hcp["fieldmap"][int(fmnum_mag)][
                            "Magnitude"
                        ]
                        r, boldok = pc.checkForFile2(
                            r,
                            auto_precomputedfmapmag,
                            "\n     ... precomputed fieldmap magnitude image auto-detected and present: %s"
                            % (auto_precomputedfmapmag),
                            "\n---> ERROR: Could not find auto-detected precomputed fieldmap magnitude image: %s."
                            % (auto_precomputedfmapmag),
                            status=boldok,
                        )
                        if os.path.exists(auto_precomputedfmapmag):
                            fmprecomputedmag = auto_precomputedfmapmag
                    else:
                        r += "\n---> WARNING: hcp_bold_precomputedfmapmag is not set and could not be auto-detected. The HCP pipelines require this for PRECOMPUTED_FIELDMAP."

            # --- NO DC used
            elif options["hcp_bold_dcmethod"].lower() == "none":
                r += "\n     ... No distortion correction used "
                if options["hcp_processing_mode"] == "HCPStyleData":
                    r += "\n---> ERROR: The requested HCP processing mode is 'HCPStyleData', however, no distortion correction method was specified!\n            Consider using LegacyStyleData processing mode."
                    run = False

            # --- SEBASED
            elif options["hcp_bold_biascorrection"].lower() == "sebased":
                r += "\n     ... SEBASED bias correction used"
                if options["hcp_bold_dcmethod"].lower() not in [
                    "topup",
                    "topup_mismatched",
                ]:
                    r += "\n---> ERROR: SEBASED hcp_bold_biascorrection requires hcp_bold_dcmethod TOPUP or TOPUP_MISMATCHED!"
                    run = False

            # --- OnScanner
            elif options["hcp_bold_dcmethod"].lower() == "onscanner":
                r += "\n     ... OnScanner distortion correction used "

            # --- ERROR
            else:
                r += "\n     ... ERROR: Issues detected with distortion correction setup! Please check related parameters!"
                boldok = False

            # --- set reference
            # Need to make sure the right reference is used in relation to LR/RL AP/PA bolds
            # - have to keep track of whether an old topup in the same direction exists
            if options["hcp_folderstructure"] == "hcpya":
                boldimgs.append(
                    os.path.join(
                        hcp["source"],
                        "%s%s" % (boldroot, options["fctail"]),
                        "%s%s_%s.nii.gz" % (sinfo["id"], options["fctail"], boldroot),
                    )
                )

            r, boldok, boldimg = pc.checkForFiles(
                r,
                boldimgs,
                "\n     ... bold image present",
                "\n     ... ERROR: bold image missing, searched for %s!" % (boldimgs),
                status=boldok,
            )

            # --- check for ref image
            if options["hcp_bold_sbref"].lower() == "use":
                refimg = os.path.join(
                    hcp["source"],
                    "%s_SBRef%s" % (boldroot, options["fctail"]),
                    "%s_%s_SBRef.nii.gz" % (sinfo["id"], boldroot),
                )
                r, boldok = pc.checkForFile2(
                    r,
                    refimg,
                    "\n     ... reference image present",
                    "\n     ... ERROR: bold reference image missing!",
                    status=boldok,
                )
            else:
                r += "\n     ... reference image not used"

            # --- check the mask used
            if options["hcp_bold_mask"]:
                if (
                    options["hcp_bold_mask"] != "T1_fMRI_FOV"
                    and options["hcp_processing_mode"] == "HCPStyleData"
                ):
                    r += "\n---> ERROR: The requested HCP processing mode is 'HCPStyleData', however, %s was specified as bold mask to use!\n            Consider either using 'T1_fMRI_FOV' for the bold mask or LegacyStyleData processing mode."
                    run = False
                else:
                    r += "\n     ... using %s as BOLD mask" % (options["hcp_bold_mask"])
            else:
                r += "\n     ... using the HCPpipelines default BOLD mask"

            # --- set movement reference image
            fmriref = futureref
            if options["hcp_bold_movref"] == "first":
                if futureref == "NONE":
                    futureref = boldtarget

            # --- are we using previous reference
            if fmriref != "NONE":
                r += "\n     ... using %s as movement correction reference" % (fmriref)
                refimg = "NONE"
                if (
                    options["hcp_processing_mode"] == "HCPStyleData"
                    and options["hcp_bold_refreg"] == "nonlinear"
                ):
                    r += "\n---> ERROR: The requested HCP processing mode is 'HCPStyleData', however, a nonlinear registration to an external BOLD was specified!\n            Consider using LegacyStyleData processing mode."
                    run = False

            # --- Check for slice timing file
            if options["hcp_bold_doslicetime"] and options["hcp_bold_slicetimingfile"]:
                stfile = os.path.join(
                    hcp["source"],
                    "%s%s" % (boldroot, options["fctail"]),
                    "%s_%s_slicetimer.txt" % (sinfo["id"], boldroot),
                )
                r, boldok = pc.checkForFile2(
                    r,
                    stfile,
                    "\n     ... slice timing file present",
                    "\n     ... ERROR: slice timing file missing!",
                    status=boldok,
                )
            else:
                stfile = None

            # store required data
            b = {
                "boldsource": boldsource,
                "boldtarget": boldtarget,
                "printbold": printbold,
                "run": run,
                "boldok": boldok,
                "boldimg": boldimg,
                "refimg": refimg,
                "stfile": stfile,
                "gdcfile": gdcfile,
                "unwarpdir": unwarpdir,
                "echospacing": echospacing,
                "spinNeg": spinNeg,
                "spinPos": spinPos,
                "topupconfig": topupconfig,
                "fmmag": fmmag,
                "fmphase": fmphase,
                "fmcombined": fmcombined,
                "fmprecomputed": fmprecomputed,
                "fmprecomputedmag": fmprecomputedmag,
                "fmriref": fmriref,
            }
            boldsData.append(b)

        # --- Process
        r += "\n"

        # if moveref equals first and seimage equals independent (complex scenario)
        if (
            not options["longitudinal"]
            and options["hcp_bold_movref"] == "first"
            and options["hcp_bold_seimg"] == "independent"
        ):
            # loop over bolds to prepare processing pools
            boldsPool = []
            for b in boldsData:
                fmriref = b["fmriref"]
                # if fmriref is "NONE" then process the previous pool followed by this one as single
                if fmriref == "NONE":
                    if len(boldsPool) > 0:
                        r, report = executeMultipleHCPfMRIVolume(
                            sinfo, options, overwrite, hcp, boldsPool, r, report
                        )
                    boldsPool = []
                    r, report = executeSingleHCPfMRIVolume(
                        sinfo, options, overwrite, hcp, b, r, report
                    )
                else:  # else add to pool
                    boldsPool.append(b)

            # execute remaining pool
            r, report = executeMultipleHCPfMRIVolume(
                sinfo, options, overwrite, hcp, boldsPool, r, report
            )

        else:
            # if moveref equals first then process first one in serial
            if not options["longitudinal"] and options["hcp_bold_movref"] == "first":
                # process first one
                b = boldsData[0]
                r, report = executeSingleHCPfMRIVolume(
                    sinfo, options, overwrite, hcp, b, r, report
                )

                # remove first one from array then process others in parallel
                boldsData.pop(0)

            # process the rest in parallel
            r, report = executeMultipleHCPfMRIVolume(
                sinfo, options, overwrite, hcp, boldsData, r, report
            )

        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP fMRI Volume: bolds " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = (sinfo["id"], "HCP fMRI Volume failed", 1)
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = (sinfo["id"], "HCP fMRI Volume failed", 1)

    r += (
        "\n\nHCP fMRIVolume %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, report)


def executeSingleHCPfMRIVolume(sinfo, options, overwrite, hcp, b, r, report):
    # process
    result = executeHCPfMRIVolume(sinfo, options, overwrite, hcp, b)

    # merge r
    r += result["r"]

    # merge report
    tempReport = result["report"]
    report["done"] += tempReport["done"]
    report["incomplete"] += tempReport["incomplete"]
    report["failed"] += tempReport["failed"]
    report["ready"] += tempReport["ready"]
    report["not ready"] += tempReport["not ready"]
    report["skipped"] += tempReport["skipped"]

    return r, report


def executeMultipleHCPfMRIVolume(sinfo, options, overwrite, hcp, boldsData, r, report):
    # parelements
    parelements = max(1, min(options["parelements"], len(boldsData)))

    # create a multiprocessing Pool
    processPoolExecutor = ProcessPoolExecutor(parelements)

    # partial function
    f = partial(executeHCPfMRIVolume, sinfo, options, overwrite, hcp)
    results = processPoolExecutor.map(f, boldsData)

    # merge r and report
    for result in results:
        r += result["r"]
        tempReport = result["report"]
        report["done"] += tempReport["done"]
        report["incomplete"] += tempReport["incomplete"]
        report["failed"] += tempReport["failed"]
        report["ready"] += tempReport["ready"]
        report["not ready"] += tempReport["not ready"]
        report["skipped"] += tempReport["skipped"]

    return r, report


def executeHCPfMRIVolume(sinfo, options, overwrite, hcp, b):
    # extract data
    boldtarget = b["boldtarget"]
    printbold = b["printbold"]
    gdcfile = b["gdcfile"]
    run = b["run"]
    boldok = b["boldok"]
    boldimg = b["boldimg"]
    refimg = b["refimg"]
    stfile = b["stfile"]
    unwarpdir = b["unwarpdir"]
    echospacing = b["echospacing"]
    spinNeg = b["spinNeg"]
    spinPos = b["spinPos"]
    topupconfig = b["topupconfig"]
    fmmag = b["fmmag"]
    fmphase = b["fmphase"]
    fmcombined = b["fmcombined"]
    fmprecomputed = b["fmprecomputed"]
    fmprecomputedmag = b["fmprecomputedmag"]
    fmriref = b["fmriref"]

    # prepare return variables
    r = ""
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # --- process additional parameters
        doslicetime = "FALSE"
        slicetimerparams = ""

        if options["hcp_bold_doslicetime"]:
            doslicetime = "TRUE"

            slicetimerparams = re.split(
                r" +|,|\|", options["hcp_bold_slicetimerparams"]
            )

            slicetimerparams = [e for e in slicetimerparams if e]

            if (
                options["hcp_bold_stcorrdir"] != ""
                and options["hcp_bold_stcorrdir"] not in slicetimerparams
            ):
                slicetimerparams.append(options["hcp_bold_stcorrdir"])
            if (
                options["hcp_bold_stcorrint"] != ""
                and options["hcp_bold_stcorrint"] not in slicetimerparams
            ):
                slicetimerparams.append(options["hcp_bold_stcorrint"])
            if options["hcp_bold_slicetimingfile"]:
                slicetimingfile = f"--tcustom={stfile}"
                if slicetimingfile not in slicetimerparams:
                    slicetimerparams.append(slicetimingfile)

            # iterate over slicetimerparams
            for i in range(len(slicetimerparams)):
                if not slicetimerparams[i].startswith("--"):
                    slicetimerparams[i] = f"--{slicetimerparams[i]}"

            slicetimerparams = "@".join(slicetimerparams)

        # --- Set up the command
        if fmriref == "NONE":
            fmrirefparam = ""
        else:
            fmrirefparam = fmriref

        comm = (
            os.path.join(
                hcp["hcp_base"], "fMRIVolume", "GenericfMRIVolumeProcessingPipeline.sh"
            )
            + " "
        )

        print(
            "======================================================================================================================================="
        )
        elements = [
            ("path", sinfo["hcp"]),
            ("session", sinfo["id"] + options["hcp_suffix"]),
            ("fmriname", boldtarget),
            ("fmritcs", boldimg),
            ("fmriscout", refimg),
            ("SEPhaseNeg", spinNeg),
            ("SEPhasePos", spinPos),
            ("fmapmag", fmmag),
            ("fmapphase", fmphase),
            ("fmapcombined", fmcombined),
            ("precomputedfmap", fmprecomputed),
            ("precomputedfmapmag", fmprecomputedmag),
            ("echospacing", echospacing),
            ("echodiff", options["hcp_bold_echodiff"]),
            ("unwarpdir", unwarpdir),
            ("fmrires", options["hcp_bold_res"]),
            ("dcmethod", options["hcp_bold_dcmethod"]),
            ("biascorrection", options["hcp_bold_biascorrection"]),
            ("gdcoeffs", gdcfile),
            ("topupconfig", topupconfig),
            ("dof", options["hcp_bold_dof"]),
            ("printcom", options["hcp_printcom"]),
            ("usejacobian", options["hcp_bold_usejacobian"]),
            ("mctype", options["hcp_bold_movreg"].upper()),
            ("preregistertool", options["hcp_bold_preregistertool"]),
            ("processing-mode", options["hcp_processing_mode"]),
            ("doslicetime", doslicetime),
            ("slicetimerparams", slicetimerparams),
            ("fmriref", fmrirefparam),
            ("fmrirefreg", options["hcp_bold_refreg"]),
            ("fmrimask", options["hcp_bold_mask"]),
        ]

        # optional parameters
        if options["hcp_wb_resample"]:
            elements.append(("wb-resample", "1"))

        if options["hcp_echo_te"]:
            echo_te = ("echoTE", options["hcp_echo_te"].replace(",", "@"))
            elements.append(echo_te)

        # matlab run mode, compiled=0, interpreted=1, octave=2
        if options["hcp_matlab_mode"]:
            if options["hcp_matlab_mode"] == "compiled":
                elements.append(("matlab-run-mode", "0"))
            elif options["hcp_matlab_mode"] == "interpreted":
                elements.append(("matlab-run-mode", "1"))
            elif options["hcp_matlab_mode"] == "octave":
                elements.append(("matlab-run-mode", "2"))
            else:
                r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                run = False

        if options["hcp_bold_seechospacing"]:
            elements.append(("seechospacing", options["hcp_bold_seechospacing"]))

        if options["hcp_bold_seunwarpdir"]:
            elements.append(("seunwarpdir", options["hcp_bold_seunwarpdir"]))

        # longitudinal mode
        if options["longitudinal"]:
            studyfolder = gc.deduce_folders(options)["basefolder"]
            if not studyfolder:
                r += "\nERROR: cannot deduce the QuNex study folder from provided parameters! Please provide the sessionsfolder or the studyfolder parameter."
                run = False
            # replace path (elements[0])
            elements[0] = (
                "path",
                os.path.join(studyfolder, "subjects", sinfo["subject"]),
            )
            elements.append(("is-longitudinal", "1"))
            elements.append(
                (
                    "longitudinal-session",
                    f"{sinfo['id']}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}",
                )
            )

        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])

        # -- Report command
        if boldok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test files
        tfile = None
        fullTest = None
        if not options["longitudinal"]:
            tfile = os.path.join(
                hcp["hcp_nonlin"], "Results", boldtarget, "%s.nii.gz" % (boldtarget)
            )

            if hcp["hcp_bold_vol_check"]:
                fullTest = {
                    "tfolder": hcp["base"],
                    "tfile": hcp["hcp_bold_vol_check"],
                    "fields": [
                        ("sessionid", sinfo["id"] + options["hcp_suffix"]),
                        ("scan", boldtarget),
                    ],
                    "specfolder": options["specfolder"],
                }

        # -- Run
        if run and boldok:
            if options["run"] == "run":
                if not options["longitudinal"] and (
                    overwrite or not os.path.exists(tfile)
                ):
                    # ---> Clean up existing data
                    # -> bold working folder
                    bold_folder = os.path.join(hcp["base"], boldtarget)
                    if os.path.exists(bold_folder):
                        r += (
                            "\n     ... removing preexisting working bold folder [%s]"
                            % (bold_folder)
                        )
                        shutil.rmtree(bold_folder)

                    # -> bold MNINonLinear results folder
                    bold_folder = os.path.join(hcp["hcp_nonlin"], "Results", boldtarget)
                    if os.path.exists(bold_folder):
                        r += (
                            "\n     ... removing preexisting MNINonLinar results bold folder [%s]"
                            % (bold_folder)
                        )
                        shutil.rmtree(bold_folder)

                    # -> bold T1w results folder
                    bold_folder = os.path.join(hcp["T1w_folder"], "Results", boldtarget)
                    if os.path.exists(bold_folder):
                        r += (
                            "\n     ... removing preexisting T1w results bold folder [%s]"
                            % (bold_folder)
                        )
                        shutil.rmtree(bold_folder)

                    # -> xfms in T1w folder
                    xfms_file = os.path.join(
                        hcp["T1w_folder"], "xfms", "%s2str.nii.gz" % (boldtarget)
                    )
                    if os.path.exists(xfms_file):
                        r += "\n     ... removing preexisting xfms file [%s]" % (
                            xfms_file
                        )
                        os.remove(xfms_file)

                    # -> xfms in MNINonLinear folder
                    xfms_file = os.path.join(
                        hcp["hcp_nonlin"], "xfms", "%s2str.nii.gz" % (boldtarget)
                    )
                    if os.path.exists(xfms_file):
                        r += "\n     ... removing preexisting xfms file [%s]" % (
                            xfms_file
                        )
                        os.remove(xfms_file)

                    # -> xfms in MNINonLinear folder
                    xfms_file = os.path.join(
                        hcp["hcp_nonlin"], "xfms", "standard2%s.nii.gz" % (boldtarget)
                    )
                    if os.path.exists(xfms_file):
                        r += "\n     ... removing preexisting xfms file [%s]" % (
                            xfms_file
                        )
                        os.remove(xfms_file)

                logtags = [options["logtag"], boldtarget]
                if options["longitudinal"]:
                    logtags.append("long")

                r, _, _, failed = pc.runExternalForFile(
                    tfile,
                    comm,
                    "Running HCP fMRIVolume",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=logtags,
                    fullTest=fullTest,
                    shell=True,
                    r=r,
                )

                if failed:
                    report["failed"].append(printbold)
                else:
                    report["done"].append(printbold)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    tfile,
                    fullTest,
                    "HCP fMRIVolume " + boldtarget,
                    r,
                    overwrite=overwrite,
                )
                if passed is None:
                    r += "\n---> HCP fMRIVolume can be run"
                    report["ready"].append(printbold)
                else:
                    report["skipped"].append(printbold)

        else:
            report["not ready"].append(printbold)
            if options["run"] == "run":
                r += "\n---> ERROR: something missing, skipping this BOLD!"
            else:
                r += "\n---> ERROR: something missing, this BOLD would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of bold %s with error:\n" % (printbold)
        r += str(errormessage)
        report["failed"].append(printbold)
    except:
        r += "\n --- Failed during processing of bold %s with error:\n %s\n" % (
            printbold,
            traceback.format_exc(),
        )
        report["failed"].append(printbold)

    return {"r": r, "report": report}


def hcp_fmri_surface(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_fmri_surface [... processing options]``

    Runs the fMRI Surface (GenericfMRISurfaceProcessingPipeline.sh) step of the
    HCP Pipeline .

    Warning:
        The code expects all the previous HCP preprocessing steps
        (hcp_pre_freesurfer, hcp_freesurfer, hcp_post_freesurfer,
        hcp_fmri_volume) to have been run and finished successfully. The
        command will test for presence of key files but do note that it won't
        run a thorough check for all the required files.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --bolds (str, default 'all'):
            Which bold images (as they are specified in the batch.txt file) to
            process. It can be a single type (e.g. 'task'), a pipe separated
            list (e.g. 'WM|Control|rest') or 'all' to process all.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_folderstructure (str, default 'hcpls'):
            If set to 'hcpya' the folder structure used in the initial HCP Young
            Adults study is used. Specifically, the source files are stored in
            individual folders within the main 'hcp' folder in parallel with the
            working folders and the 'MNINonLinear' folder with results. If set
            to'hcpls' the folder structure used in the HCP Life Span study is
            used. Specifically, the source files are all stored within their
            individual subfolders located in the joint 'unprocessed' folder in
            the main 'hcp' folder, parallel to the working folders and the
            'MNINonLinear' folder.

        --hcp_filename (str, default 'automated'):
            How to name the BOLD files once mapped into the hcp input folder
            structure. The default ('automated') will automatically name each
            file by their number (e.g. BOLD_1). The alternative ('userdefined')
            is to use the file names, which can be defined by the user prior to
            mapping (e.g. rfMRI_REST1_AP).

        --hcp_bold_prefix (str, default 'BOLD'):
            The prefix to use when generating BOLD names (see 'hcp_filename')
            for BOLD working folders and results.

        --hcp_lowresmesh (int, default 32):
            The number of vertices to be used in the low-resolution grayordinate
            mesh (in thousands).

        --hcp_bold_res (str, default '2'):
            The resolution of the BOLD volume data in mm.

        --hcp_grayordinatesres (int, default 2):
            The size of voxels for the subcortical and cerebellar data in
            grayordinate space in mm.

        --hcp_bold_smoothFWHM (int, default 2):
            The size of the smoothing kernel (in mm).

        --hcp_regname (str, default 'MSMSulc'):
            The name of the registration used.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --longitudinal:
            Set this flag if you are running the longitudinal variant of this
            command.

    Output files:
        The results of this step will be present in the MNINonLinear folder
        in the sessions's root hcp folder::

            study
            └─ sessions
               └─ session1_session1
                  └─ hcp
                     └─ subject1_session1
                       └─ MNINonlinear
                          └─ Results
                             └─ BOLD_1

    Notes:
        Runs the fMRI Surface (GenericfMRISurfaceProcessingPipeline.sh) step of
        the HCP Pipeline. It uses the FreeSurfer segmentation and surface
        reconstruction to map BOLD timeseries to grayordinate representation
        and generates .dtseries.nii files.

        hcp_fmri_surface parameter mapping:

            ============================= =======================
            QuNex parameter               HCPpipelines parameter
            ============================= =======================
            ``hcp_lowresmesh``            ``lowresmesh``
            ``hcp_bold_res``              ``fmrires``
            ``hcp_bold_smoothFWHM``       ``smoothingFWHM``
            ``hcp_grayordinatesres``      ``grayordinatesres``
            ``hcp_regname``               ``regname``
            ``hcp_printcom``              ``printcom``
            ``hcp_longitudinal_template`` ``longitudinal-template``
            ``longitudinal``              ``is-longitudinal``
            ============================= =======================

    Examples:
        Example run from the base study folder with ``--test`` flag. Here
        ``--parsessions`` specifies how many sessions to run concurrently and
        ``--parelements`` specifies how many elements (e.g. bold images) to
        process concurrently::

            qunex hcp_fmri_surface  \\
                --batchfile="processing/batch.txt"  \\
                --sessionsfolder="sessions"  \\
                --parsessions="10"  \\
                --parelements="4"  \\
                --overwrite="no"  \\
                --test

        Run using absolute paths with scheduler::

            qunex hcp_fmri_surface  \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"  \\
                --sessionsfolder="<path_to_study_folder>/sessions"  \\
                --parsessions="4"  \\
                --parelements="4"  \\
                --overwrite="yes"  \\
                --scheduler="SLURM,time=24:00:00,cpus-per-task=2,mem-per-cpu=1300,partition=day"

        Extra example::

            qunex hcp_fmri_surface \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP fMRI Surface pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, "hcp_fmri_surface")
        doHCPOptionsCheck(options, "hcp_fmri_surface")
        hcp = getHCPPaths(sinfo, options)

        # --- bold filtering not yet supported!
        # btargets = options['bolds'].split("|")

        # --- run checks
        if "hcp" not in sinfo:
            r += (
                "\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"])
            )
            run = False

        # -> PostFS results
        tfile = os.path.join(
            hcp["hcp_nonlin"],
            "fsaverage_LR32k",
            sinfo["id"] + options["hcp_suffix"] + ".32k_fs_LR.wb.spec",
        )

        if os.path.exists(tfile):
            r += "\n---> PostFS results present."
        else:
            r += "\n---> ERROR: Could not find PostFS processing results."
            run = False

        # --- Get sorted bold numbers
        bolds, bskip, report["boldskipped"], r = pc.use_or_skip_bold(sinfo, options, r)
        if len(bolds) == 0:
            r += (
                "\n---> ERROR: No BOLD images found for session %s! Check your data or the contents of the batch file."
                % (sinfo["id"])
            )
            run = False

        _build_skipped_report(report, bskip, options)

        parelements = max(1, min(options["parelements"], len(bolds)))
        r += "\n%s %d BOLD images in parallel" % (
            pc.action("Running", options["run"]),
            parelements,
        )

        # create a multiprocessing Pool
        processPoolExecutor = ProcessPoolExecutor(parelements)
        # process
        f = partial(executeHCPfMRISurface, sinfo, options, overwrite, hcp, run)
        results = processPoolExecutor.map(f, bolds)

        # merge r and report
        for result in results:
            r += result["r"]
            tempReport = result["report"]
            report["done"] += tempReport["done"]
            report["failed"] += tempReport["failed"]
            report["incomplete"] += tempReport["incomplete"]
            report["ready"] += tempReport["ready"]
            report["not ready"] += tempReport["not ready"]
            report["skipped"] += tempReport["skipped"]

        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP fMRI Surface: bolds " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = (sinfo["id"], "HCP fMRI Surface failed")
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = (sinfo["id"], "HCP fMRI Surface failed")

    r += (
        "\n\nHCP fMRISurface %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, report)


def executeHCPfMRISurface(sinfo, options, overwrite, hcp, run, boldinfo):

    printbold, boldtarget, _ = pc.get_bold_names(boldinfo, options)

    # prepare return variables
    r = ""
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        r += "\n\n---> %s BOLD image %s" % (
            pc.action("Processing", options["run"]),
            printbold,
        )
        boldok = True

        # --- check for bold image
        if "longitudinal" not in options or not options["longitudinal"]:
            boldimg = os.path.join(
                hcp["hcp_nonlin"], "Results", boldtarget, "%s.nii.gz" % (boldtarget)
            )
            r, boldok = pc.checkForFile2(
                r,
                boldimg,
                "\n     ... fMRIVolume preprocessed bold image present",
                f"\n     ... ERROR: fMRIVolume preprocessed bold image missing {boldimg}!",
                status=boldok,
            )

        # --- Set up the command
        comm = (
            os.path.join(
                hcp["hcp_base"],
                "fMRISurface",
                "GenericfMRISurfaceProcessingPipeline.sh",
            )
            + " "
        )

        # path and session
        path = sinfo["hcp"]
        session = sinfo["id"] + options["hcp_suffix"]

        # longitudinal
        if options["longitudinal"]:
            studyfolder = gc.deduce_folders(options)["basefolder"]
            if not studyfolder:
                r += "\nERROR: cannot deduce the QuNex study folder from provided parameters! Please provide the sessionsfolder or the studyfolder parameter."
                boldok = False
            # replace path
            path = os.path.join(studyfolder, "subjects", sinfo["subject"])
            session = f"{sinfo['id']}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"

        elements = [
            ("path", path),
            ("session", session),
            ("fmriname", boldtarget),
            ("lowresmesh", options["hcp_lowresmesh"]),
            ("fmrires", options["hcp_bold_res"]),
            ("smoothingFWHM", options["hcp_bold_smoothFWHM"]),
            ("grayordinatesres", options["hcp_grayordinatesres"]),
            ("regname", options["hcp_regname"]),
            ("printcom", options["hcp_printcom"]),
        ]

        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])

        # -- Report command
        if boldok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test files
        tfile = None
        fullTest = None
        if not options["longitudinal"]:
            tfile = os.path.join(
                hcp["hcp_nonlin"],
                "Results",
                boldtarget,
                "%s%s.dtseries.nii" % (boldtarget, "_Atlas"),
            )

            if hcp["hcp_bold_surf_check"]:
                fullTest = {
                    "tfolder": hcp["base"],
                    "tfile": hcp["hcp_bold_surf_check"],
                    "fields": [
                        ("sessionid", sinfo["id"] + options["hcp_suffix"]),
                        ("scan", boldtarget),
                    ],
                    "specfolder": options["specfolder"],
                }

        # -- Run
        if run and boldok:
            if options["run"] == "run":
                if not options["longitudinal"] and (
                    overwrite and os.path.exists(tfile)
                ):
                    os.remove(tfile)

                logtags = [options["logtag"], boldtarget]
                if options["longitudinal"]:
                    logtags.append("long")

                r, _, _, failed = pc.runExternalForFile(
                    tfile,
                    comm,
                    "Running HCP fMRISurface",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=logtags,
                    fullTest=fullTest,
                    shell=True,
                    r=r,
                )

                if failed:
                    report["failed"].append(printbold)
                else:
                    report["done"].append(printbold)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    tfile,
                    fullTest,
                    "HCP fMRISurface " + boldtarget,
                    r,
                    overwrite=overwrite,
                )
                if passed is None:
                    r += "\n---> HCP fMRISurface can be run"
                    report["ready"].append(printbold)
                else:
                    report["skipped"].append(printbold)

        else:
            report["not ready"].append(printbold)
            if options["run"] == "run":
                r += "\n---> ERROR: something missing, skipping this BOLD!"
            else:
                r += "\n---> ERROR: something missing, this BOLD would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of bold %s with error:\n" % (printbold)
        r += str(errormessage)
        report["failed"].append(printbold)
    except:
        r += "\n --- Failed during processing of bold %s with error:\n %s\n" % (
            printbold,
            traceback.format_exc(),
        )
        report["failed"].append(printbold)

    return {"r": r, "report": report}


def parse_icafix_bolds(options, bolds, r, msmall=False):
    # --- Use hcp_icafix parameter to determine if a single fix or a multi fix should be used
    singleFix = True

    # variable for storing groups and their bolds
    hcpGroups = {}

    # variable for storing erroneously specified bolds
    boldError = []

    # flag that all is OK
    boldsOK = True

    # get all bold targets and tags
    boldtargets = []
    boldtags = []

    for boldinfo in bolds:
        _, boldtarget, _ = pc.get_bold_names(boldinfo, options)
        boldtag = boldinfo["task"]

        boldtargets.append(boldtarget)
        boldtags.append(boldtag)

    hcpBolds = None
    if options["hcp_icafix_bolds"] is not None:
        hcpBolds = options["hcp_icafix_bolds"]

    if hcpBolds:
        # if hcpBolds includes : then we have groups and we need multi fix
        if ":" in hcpBolds:
            # run multi fix
            singleFix = False

            # get all groups
            groups = str.split(hcpBolds, "|")

            # store all bolds in hcpBolds
            hcpBolds = []

            for g in groups:
                # get group name
                split = str.split(g, ":")

                # create group and add to dictionary
                if split[0] not in hcpGroups:
                    specifiedBolds = str.split(split[1], ",")
                    groupBolds = []

                    # iterate over all and add to bolds or inject instead of tags
                    for sb in specifiedBolds:
                        if sb not in boldtargets and sb not in boldtags:
                            boldError.append(sb)
                        else:
                            # counter
                            i = 0

                            for b in boldtargets:
                                if sb == boldtargets[i] or sb == boldtags[i]:
                                    if sb in hcpBolds:
                                        boldsOK = False
                                        r += (
                                            "\n\nERROR: the bold [%s] is specified twice!"
                                            % b
                                        )
                                    else:
                                        groupBolds.append(b)
                                        hcpBolds.append(b)

                                # increase counter
                                i = i + 1

                    hcpGroups[split[0]] = groupBolds
                else:
                    boldsOK = False
                    r += (
                        "\n\nERROR: multiple concatenations with the same name [%s]!"
                        % split[0]
                    )

        # else we extract bolds and use single fix
        else:
            # specified bolds
            specifiedBolds = str.split(hcpBolds, ",")

            # variable for storing bolds
            hcpBolds = []

            # iterate over all and add to bolds or inject instead of tags
            for sb in specifiedBolds:
                if sb not in boldtargets and sb not in boldtags:
                    boldError.append(sb)
                else:
                    # counter
                    i = 0

                    for b in boldtargets:
                        if sb == boldtargets[i] or sb == boldtags[i]:
                            if sb in hcpBolds:
                                boldsOK = False
                                r += "\n\nERROR: the bold [%s] is specified twice!" % b
                            else:
                                hcpBolds.append(b)

                        # increase counter
                        i = i + 1

    # if hcp_icafix is empty then bundle all bolds
    else:
        # run multi fix
        singleFix = False
        hcpBolds = bolds
        hcpGroups = []
        hcpGroups.append({"name": "fMRI_CONCAT_ALL", "bolds": hcpBolds})

        # create specified bolds
        specifiedBolds = boldtargets

        r += "\nConcatenating all bolds\n"

    # --- Get hcp_icafix data from bolds
    # variable for storing skipped bolds
    boldSkip = []

    if hcpBolds is not bolds:
        # compare
        r += "\n\nComparing bolds with those specifed via parameters\n"

        # single fix
        if singleFix:
            # variable for storing bold data
            boldData = []

            # add data to list
            for b in hcpBolds:
                # get index
                i = boldtargets.index(b)

                # store data
                if b in boldtargets:
                    boldData.append(bolds[i])

            # skipped bolds
            for b in boldtargets:
                if b not in hcpBolds:
                    boldSkip.append(b)

            # store data into the hcpBolds variable
            hcpBolds = boldData

        # multi fix
        else:
            # variable for storing group data
            groupData = {}

            # variable for storing skipped bolds
            boldSkipDict = {}
            for b in boldtargets:
                boldSkipDict[b] = True

            # go over all groups
            for g in hcpGroups:
                # create empty dict entry for group
                groupData[g] = []

                # go over group bolds
                groupBolds = hcpGroups[g]

                # add data to list
                for b in groupBolds:
                    # get index
                    i = boldtargets.index(b)

                    # store data
                    if b in boldtargets:
                        groupData[g].append(bolds[i])

                # find skipped bolds
                for i in range(len(boldtargets)):
                    # bold is defined
                    if boldtargets[i] in groupBolds:
                        # append

                        boldSkipDict[boldtargets[i]] = False

            # cast boldSkip from dictionary to array
            for b in boldtargets:
                if boldSkipDict[b]:
                    boldSkip.append(b)

            # cast group data to array of dictionaries (needed for parallel)
            hcpGroups = []
            for g in groupData:
                hcpGroups.append({"name": g, "bolds": groupData[g]})

    # report that some hcp_icafix_bolds not found in bolds
    if len(boldSkip) > 0 or len(boldError) > 0:
        for b in boldSkip:
            r += "     ... skipping %s: it is not specified in hcp_icafix_bolds\n" % b
        for b in boldError:
            r += (
                "     ... ERROR: %s specified in hcp_icafix_bolds but not found in bolds\n"
                % b
            )
    else:
        r += "     ... all bolds specified via hcp_icafix_bolds are present\n"

    if len(boldError) > 0:
        boldsOK = False

    # --- Report single fix or multi fix
    if singleFix:
        r += "\nSingle-run HCP ICAFix on %d bolds" % len(hcpBolds)
    else:
        r += "\nMulti-run HCP ICAFix on %d groups" % len(hcpGroups)

    # different output for msmall and singlefix
    if msmall and singleFix:
        # single group
        hcpGroups = []
        icafixGroup = {}
        icafixGroup["bolds"] = hcpBolds
        hcpGroups.append(icafixGroup)

        # bolds
        hcpBolds = specifiedBolds
    elif options["hcp_icafix_bolds"] is None:
        # bolds
        hcpBolds = specifiedBolds

    return (singleFix, hcpBolds, hcpGroups, boldsOK, r)


def hcp_icafix(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_icafix [... processing options]``

    Runs the ICAFix step of HCP Pipeline (hcp_fix_multi_run or hcp_fix).

    Warning:
        The code expects the input images to be named and present in the QuNex
        folder structure. The function will look into folder::

            <session id>/hcp/<session id>

        for files::

            MNINonLinear/Results/<boldname>/<boldname>.nii.gz

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging  data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_icafix_bolds (str, default ''):
            Specify a list of bolds for ICAFix. You should specify how to
            group/concatenate bolds together along with bolds, e.g.
            "<group1>:<boldname1>,<boldname2>|
            <group2>:<boldname3>,<boldname4>", in this case multi-run HCP
            ICAFix will be executed, which is the default. Instead of full bold
            names, you can also  use bold tags from the batch file. If this
            parameter is not provided ICAFix will bundle all bolds together and
            execute multi-run HCP ICAFix, the concatenated file will be named
            fMRI_CONCAT_ALL. Alternatively, you can specify a comma separated
            list of bolds without groups, e.g. "<boldname1>,<boldname2>", in
            this case single-run HCP ICAFix will be executed over specified
            bolds. This is a legacy option and not recommended.

        --hcp_icafix_highpass (int, default detailed below):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default. For single-run HCP ICAFix the default
            is 'octave'.

        --hcp_icafix_domotionreg (str, default detailed below):
            Whether to regress motion parameters as part of the cleaning. The
            default value for single-run HCP ICAFix is [TRUE], while the
            default for multi-run HCP ICAFix is [FALSE].

        --hcp_icafix_model (str, default detailed below):
            Which model to use for classification. Can be one of the pre-trained
            models shpipped with FSL or a custom model as `somefile.RData`,
            `somefile.pyfix_model`, or a pyfix built-in model without extension.
            You can provide a full path to a file or just a filename if the file
            is in the FSL training_files folder. [HCP_hp<high-pass>.RData] for
            single-run HCP ICAFix and [HCP_Style_Single_Multirun_Dedrift.RData]
            for multi-run HCP ICAFix.

        --hcp_icafix_threshold (int, default 10):
            ICAFix threshold that controls the sensitivity/specificity tradeoff.

        --hcp_icafix_deleteintermediates (str, default 'FALSE'):
            If True, deletes both the concatenated high-pass filtered and
            non-filtered timeseries files that are prerequisites to FIX
            cleaning.

        --hcp_icafix_fallbackthreshold (int, default 0):
            If greater than zero, reruns icadim on any run with a VN mean more
            than this amount greater than the minimum VN mean.

        --hcp_config (str, default ''):
            Path to the HCP config file where additional parameters can be
            specified. For hcp_icafix, these parametersa are: volwisharts,
            ciftiwisharts and icadimmode.

        --hcp_icafix_postfix (str, default 'TRUE'):
            Whether to automatically run HCP PostFix if HCP ICAFix finishes
            successfully.

        --hcp_icafix_processingmode (str, default ''):
            HCPStyleData (default) or LegacyStyleData, controls whether
            --hcp_icadim_mode=fewtimepoints is allowed.

        --hcp_icafix_icadim_mode (str, default 'default'):
            Choose how to run icaDim: "default" - start with a VN dimensionality
            of 1 and rerun until convergence "fewtimepoints" - start with a VN
            dimensionality of half the timepoints, do not iterate.

        --hcp_icafix_parallel_limit (int, default -1):
            How many melodic commands to run in parallel (local, not
            cluster-distributed) during individual projection and cleanup,
            defaults to all detected physical cores.

        --hcp_icafix_concatenate_only (flag, not set by default):
            When set, the script stops after the concatination step,
            e.g., for use in experimental alternative multi-run denoising.

        --hcp_reuse_existing_ica (str, default 'FALSE'):
            Whether to execute only the FIX step of the pipeline and reuse the
            previous ICA results.

        --hcp_fix_backup (str, default ''):
            If provided, the previous FIX solution is backed up to the specified
            folder, in case hcp_reuse_existing_ica is used.

        --hcp_t1wtemplatebrain (str, default ''):
            Path to the T1w template brain used by pyfix. Not set by default,
            you can either set a path or set to "auto" to set as
            <HCPPIPEDIR>/global/templates/MNI152_T1_<RES>mm_brain.nii.gz.

        --hcp_ica_method (str, default 'MELODIC'):
            MELODIC or ICASSO. Use single-pass MELODIC (default) or multi-pass
            ICASSO consensus method for ICA.

        --hcp_legacy_fix (flag, not set by default):
            Whether to use the legacy MATLAB fix instead of the new pyfix.

        --hcp_vol_wisharts (int, default '2'):
            Number of wisharts to fit to volume data in icaDim.

        --hcp_cifti_wisharts (int, default '3'):
            Number of wisharts to fit to CIFTI data in icaDim.

        --hcp_icadim_mode (str, default 'default'):
            Choose how to run icaDim: "default" - start with a VN dimensionality
            of 1 and rerun until convergence "fewtimepoints" - start with a VN
            dimensionality of half the timepoints, do not iterate.

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folder inside the same sessions's root hcp folder.

        The final clean ICA file can be found in::

            MNINonLinear/Results/<boldname>/<boldname>_hp<highpass>_clean.nii.gz,

        where highpass is the used value for the highpass filter. The
        default highpass value is 0 for multi-run HCP ICAFix and 2000 for
        single-run HCP ICAFix.

    Notes:
        Runs the ICAFix step of HCP Pipeline (hcp_fix_multi_run or hcp_fix).
        This step attempts to auto-classify ICA components into good and bad
        components, so that the bad components can be then removed from the 4D
        FMRI data. If ICAFix step finishes successfully PostFix (PostFix.sh)
        step will execute  automatically, to disable this set the
        hcp_icafix_postfix to FALSE.

        If the hcp_icafix_bolds parameter is not provided ICAFix will bundle
        all bolds together and execute multi-run HCP ICAFix, the
        concatenated file will be named fMRI_CONCAT_ALL. WARNING: if
        session has many bolds such processing requires a lot of
        computational resources.

        hcp_icafix parameter mapping:

            ================================== =======================
            QuNex parameter                    HCPpipelines parameter
            ================================== =======================
            ``hcp_icafix_highpass``            ``high-pass``
            ``hcp_icafix_domotionreg``         ``motion-regression``
            ``hcp_icafix_model``               ``training-file``
            ``hcp_icafix_threshold``           ``fix-threshold``
            ``hcp_icafix_deleteintermediates`` ``delete-intermediates``
            ``hcp_icafix_fallbackthreshold``   ``fallback-threshold``
            ``hcp_icafix_parallel_limit``      ``parallel-limit``
            ``hcp_config``                     ``config``
            ``hcp_icafix_processingmode``      ``processing-mode``
            ``hcp_icafix_icadim_mode``         ``icadim-mode``
            ``hcp_reuse_existing_ica``         ``reuse-existing-ica``
            ``hcp_fix_backup``                 ``fix-backup``
            ``hcp_matlab_mode``                ``matlabrunmode``
            ``hcp_t1wtemplatebrain``           ``T1wTemplateBrain``
            ``hcp_ica_method``                 ``ica-method``
            ``hcp_legacy_fix``                 ``enable-legacy-fix``
            ``hcp_icafix_concatenate_only``    ``concatenate-only``
            ``hcp_vol_wisharts``               ``vol-wisharts``
            ``hcp_cifti_wisharts``             ``cifti-wisharts``
            ``hcp_icadim_mode``                ``icadim-mode``
            ================================== =======================

    Examples:
        ::

            qunex hcp_icafix \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions

        ::

            qunex hcp_icafix \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_icafix_bolds="GROUP_1:BOLD_1,BOLD_2|GROUP_2:BOLD_3,BOLD_4"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP ICAFix pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, "hcp_icafix")
        doHCPOptionsCheck(options, "hcp_icafix")
        hcp = getHCPPaths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report["boldskipped"], r = pc.use_or_skip_bold(sinfo, options, r)
        _build_skipped_report(report, bskip, options)

        # --- Parse icafix_bolds
        singleFix, icafixBolds, icafixGroups, pars_ok, r = parse_icafix_bolds(
            options, bolds, r
        )

        # --- Multi threading
        if singleFix:
            parelements = max(1, min(options["parelements"], len(icafixBolds)))
        else:
            parelements = max(1, min(options["parelements"], len(icafixGroups)))
        r += "\n\n%s %d ICAFix elements in parallel" % (
            pc.action("Processing", options["run"]),
            parelements,
        )

        # matlab run mode, compiled=0, interpreted=1, octave=2
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
                pars_ok = False
        else:
            if options["hcp_matlab_mode"] == "compiled":
                os.environ["FSL_FIX_MATLAB_MODE"] = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                os.environ["FSL_FIX_MATLAB_MODE"] = "1"
            elif options["hcp_matlab_mode"] == "octave":
                os.environ["FSL_FIX_MATLAB_MODE"] = "2"
            else:
                r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                pars_ok = False

        if not pars_ok:
            raise ge.CommandFailed("hcp_icafix", "... invalid input parameters!")

        # --- Execute
        # single fix
        if singleFix:
            # create a multiprocessing Pool
            processPoolExecutor = ProcessPoolExecutor(parelements)
            # process
            f = partial(executeHCPSingleICAFix, sinfo, options, overwrite, hcp, run)
            results = processPoolExecutor.map(f, icafixBolds)

            # merge r and report
            for result in results:
                r += result["r"]
                tempReport = result["report"]
                report["done"] += tempReport["done"]
                report["failed"] += tempReport["failed"]
                report["incomplete"] += tempReport["incomplete"]
                report["ready"] += tempReport["ready"]
                report["not ready"] += tempReport["not ready"]
                report["skipped"] += tempReport["skipped"]

        # multi fix
        else:
            # create a multiprocessing Pool
            processPoolExecutor = ProcessPoolExecutor(parelements)
            # process
            f = partial(executeHCPMultiICAFix, sinfo, options, overwrite, hcp, run)
            results = processPoolExecutor.map(f, icafixGroups)

            # merge r and report
            for result in results:
                r += result["r"]
                tempReport = result["report"]
                report["done"] += tempReport["done"]
                report["failed"] += tempReport["failed"]
                report["incomplete"] += tempReport["incomplete"]
                report["ready"] += tempReport["ready"]
                report["not ready"] += tempReport["not ready"]
                report["skipped"] += tempReport["skipped"]

        # report
        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP ICAFix: " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except ge.CommandFailed as e:
        r += "\n\nERROR in completing %s:\n     %s\n" % (
            e.function,
            "\n     ".join(e.report),
        )
        report = (sinfo["id"], "HCP ICAFix failed")
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = (sinfo["id"], "HCP ICAFix failed")
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = (sinfo["id"], "HCP ICAFix failed")

    r += (
        "\n\nHCP ICAFix %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, report)


def executeHCPSingleICAFix(sinfo, options, overwrite, hcp, run, boldinfo):
    printbold, boldtarget, _ = pc.get_bold_names(boldinfo, options)

    # prepare return variables
    r = ""
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        r += "\n\n------------------------------------------------------------"
        r += "\n---> %s BOLD image %s" % (
            pc.action("Processing", options["run"]),
            printbold,
        )
        boldok = True

        # --- check for bold image
        boldimg = os.path.join(
            hcp["hcp_nonlin"], "Results", boldtarget, "%s.nii.gz" % (boldtarget)
        )
        r, boldok = pc.checkForFile2(
            r,
            boldimg,
            "\n     ... bold image %s present" % boldtarget,
            "\n     ... ERROR: bold image [%s] missing!" % boldimg,
            status=boldok,
        )

        # bold in input format
        inputfile = os.path.join(
            hcp["hcp_nonlin"], "Results", boldtarget, "%s" % (boldtarget)
        )

        # bandpass value
        if options["hcp_icafix_highpass"] is None:
            bandpass = 2000
        else:
            bandpass = options["hcp_icafix_highpass"]

        # delete intermediates
        icafix_threshold = 10
        if options["hcp_icafix_threshold"] is not None:
            icafix_threshold = options["hcp_icafix_threshold"]

        # delete intermediates
        delete_intermediates = "FALSE"
        if options["hcp_icafix_deleteintermediates"] is not None:
            delete_intermediates = options["hcp_icafix_deleteintermediates"]

        # the default for single fix is octave
        if options["hcp_matlab_mode"] is None:
            os.environ["FSL_FIX_MATLAB_MODE"] = "2"

        comm = (
            '%(script)s \
                "%(inputfile)s" \
                %(bandpass)s \
                "%(domot)s" \
                "%(trainingdata)s" \
                %(fixthreshold)s \
                "%(deleteintermediates)s"'
            % {
                "script": os.path.join(hcp["hcp_base"], "ICAFIX", "hcp_fix"),
                "inputfile": inputfile,
                "bandpass": bandpass,
                "domot": (
                    "TRUE"
                    if options["hcp_icafix_domotionreg"] is None
                    else options["hcp_icafix_domotionreg"]
                ),
                "trainingdata": (
                    f"HCP_hp{bandpass}.RData"
                    if options["hcp_icafix_model"] is None
                    else options["hcp_icafix_model"]
                ),
                "fixthreshold": icafix_threshold,
                "deleteintermediates": delete_intermediates,
            }
        )

        # -- Report command
        if boldok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test file
        tfile = None
        fullTest = None

        # -- Run
        if run and boldok:
            if options["run"] == "run":
                r, _, _, failed = pc.runExternalForFile(
                    tfile,
                    comm,
                    "Running single-run HCP ICAFix",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], boldtarget],
                    fullTest=fullTest,
                    shell=True,
                    r=r,
                )

                if failed:
                    report["failed"].append(printbold)
                else:
                    report["done"].append(printbold)

                # if all ok execute PostFix if enabled
                if options["hcp_icafix_postfix"]:
                    if (
                        report["incomplete"] == []
                        and report["failed"] == []
                        and report["not ready"] == []
                    ):
                        result = executeHCPPostFix(
                            sinfo, options, hcp, run, True, boldinfo
                        )
                        r += result["r"]
                        report = result["report"]

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    tfile,
                    fullTest,
                    "single-run HCP ICAFix " + boldtarget,
                    r,
                    overwrite=overwrite,
                )
                if passed is None:
                    r += "\n---> single-run HCP ICAFix can be run"
                    report["ready"].append(printbold)
                else:
                    report["skipped"].append(printbold)

        else:
            report["not ready"].append(printbold)
            if options["run"] == "run":
                r += "\n---> ERROR: something missing, skipping this BOLD!"
            else:
                r += "\n---> ERROR: something missing, this BOLD would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of bold %s\n" % (printbold)
        r += str(errormessage)
        report["failed"].append(printbold)
    except:
        r += "\n --- Failed during processing of bold %s with error:\n %s\n" % (
            printbold,
            traceback.format_exc(),
        )
        report["failed"].append(printbold)

    return {"r": r, "report": report}


def executeHCPMultiICAFix(sinfo, options, overwrite, hcp, run, group):
    # get group data
    groupname = group["name"]
    bolds = group["bolds"]

    # prepare return variables
    r = ""
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        r += "\n\n------------------------------------------------------------"
        r += "\n---> %s group %s" % (pc.action("Processing", options["run"]), groupname)
        groupok = True

        # --- check for bold images and prepare images parameter
        boldimgs = ""

        # check if files for all bolds exist
        for boldinfo in bolds:
            # set ok to true for now
            boldok = True

            _, boldtarget, _ = pc.get_bold_names(boldinfo, options)

            boldimg = os.path.join(
                hcp["hcp_nonlin"], "Results", boldtarget, "%s" % (boldtarget)
            )
            r, boldok = pc.checkForFile2(
                r,
                "%s.nii.gz" % boldimg,
                "\n     ... bold image %s present" % boldtarget,
                "\n     ... ERROR: bold image [%s.nii.gz] missing!" % boldimg,
                status=boldok,
            )

            if not boldok:
                groupok = False
                break
            else:
                # add @ separator
                if boldimgs != "":
                    boldimgs = boldimgs + "@"

                # add latest image
                boldimgs = boldimgs + boldimg

        # construct concat file name
        concatfilename = os.path.join(
            hcp["hcp_nonlin"], "Results", groupname, groupname
        )

        # bandpass
        bandpass = (
            0
            if options["hcp_icafix_highpass"] is None
            else options["hcp_icafix_highpass"]
        )

        # matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
                groupok = False
            else:
                matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
        else:
            if options["hcp_matlab_mode"] == "compiled":
                matlabrunmode = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                matlabrunmode = "1"
            elif options["hcp_matlab_mode"] == "octave":
                matlabrunmode = "2"
            else:
                r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                groupok = False

        comm = (
            '%(script)s \
                --fmri-names="%(fmrinames)s" \
                --high-pass=%(bandpass)s \
                --concat-fmri-name="%(concatfilename)s" \
                --matlab-run-mode=%(matlabrunmode)s'
            % {
                "script": os.path.join(hcp["hcp_base"], "ICAFIX", "hcp_fix_multi_run"),
                "fmrinames": boldimgs,
                "bandpass": bandpass,
                "concatfilename": concatfilename,
                "matlabrunmode": matlabrunmode,
            }
        )

        # optional parameters
        if options["hcp_icafix_domotionreg"] is not None:
            comm += (
                '             --motion-regression="%s"'
                % options["hcp_icafix_domotionreg"]
            )

        if options["hcp_icafix_model"] is not None:
            comm += '             --training-file="%s"' % options["hcp_icafix_model"]

        if options["hcp_icafix_threshold"] is not None:
            comm += (
                '             --fix-threshold="%s"' % options["hcp_icafix_threshold"]
            )

        if options["hcp_icafix_deleteintermediates"] is not None:
            comm += (
                '             --delete-intermediates="%s"'
                % options["hcp_icafix_deleteintermediates"]
            )

        if options["hcp_icafix_fallbackthreshold"] is not None:
            comm += (
                '             --fallback-threshold="%s"'
                % options["hcp_icafix_fallbackthreshold"]
            )

        if options["hcp_icafix_parallel_limit"] is not None:
            comm += (
                '             --parallel-limit="%s"'
                % options["hcp_icafix_parallel_limit"]
            )

        if options["hcp_config"] is not None:
            comm += '             --config="%s"' % options["hcp_config"]

        if options["hcp_icafix_processingmode"] is not None:
            comm += (
                '             --processing-mode="%s"'
                % options["hcp_icafix_processingmode"]
            )

        if options["hcp_icafix_icadim_mode"] is not None:
            comm += (
                '             --icadim-mode="%s"' % options["hcp_icafix_icadim_mode"]
            )

        if options["hcp_reuse_existing_ica"] is not None:
            comm += (
                '             --reuse-existing-ica="%s"'
                % options["hcp_reuse_existing_ica"]
            )

        if options["hcp_fix_backup"] is not None:
            comm += '             --fix-backup="%s"' % options["hcp_fix_backup"]

        if (
            not options["hcp_legacy_fix"]
            and options["hcp_t1wtemplatebrain"] is not None
        ):
            if options["hcp_t1wtemplatebrain"] == "auto":
                if hcp["T1w"] is not None:
                    # try to set get the resolution automatically if not set yet
                    r += "\n---> Trying to set the hcp_t1wtemplatebrain parameter automatically."

                    # place holder
                    resolution = None

                    # read nii header of hcp["T1w"]
                    t1w = hcp["T1w"].split("@")[0]
                    img = nib.load(t1w)
                    pixdim1, pixdim2, pixdim3 = img.header["pixdim"][1:4]

                    # do they match
                    epsilon = 0.05
                    if (
                        abs(pixdim1 - pixdim2) > epsilon
                        or abs(pixdim1 - pixdim3) > epsilon
                    ):
                        run = False
                        r += f"\n     ... ERROR: T1w pixdim mismatch [{pixdim1, pixdim2, pixdim3}], please set hcp_t1wtemplatebrain manually!"
                    else:
                        # upscale slightly and use the closest that matches
                        pixdim = pixdim1 * 1.05

                        if pixdim > 2:
                            run = False
                            r += f"\n     ... ERROR: weird T1w pixdim found [{pixdim1, pixdim2, pixdim3}], please set the hcp_t1wtemplatebrain parameter manually!"
                        elif pixdim > 1:
                            r += f"\n     ... Based on T1w pixdim [{pixdim1, pixdim2, pixdim3}] the hcp_t1wtemplatebrain parameter was set to 1.0!"
                            resolution = 1.0
                        elif pixdim > 0.8:
                            r += f"\n     ... Based on T1w pixdim [{pixdim1, pixdim2, pixdim3}] the hcp_t1wtemplatebrain parameter was set to 0.8!"
                            resolution = 0.8
                        elif pixdim > 0.65:
                            r += f"\n     ... Based on T1w pixdim [{pixdim1, pixdim2, pixdim3}] the hcp_t1wtemplatebrain parameter was set to to 0.7!"
                            resolution = 0.7
                        else:
                            run = False
                            r += f"\n     ... ERROR: weird T1w pixdim found [{pixdim1, pixdim2, pixdim3}], please set the hcp_t1wtemplatebrain parameter manually!"

                    if resolution is not None:
                        t1wtemplatebrain = os.path.join(
                            hcp["hcp_base"],
                            "global",
                            "templates",
                            f"MNI152_T1_{resolution}mm_brain.nii.gz",
                        )
                        comm += (
                            '             --T1wTemplateBrain="%s"' % t1wtemplatebrain
                        )
            else:
                comm += (
                    '             --T1wTemplateBrain="%s"'
                    % options["hcp_t1wtemplatebrain"]
                )

        if options["hcp_ica_method"] is not None:
            comm += '             --ica-method="%s"' % options["hcp_ica_method"]

        if options["hcp_vol_wisharts"] is not None:
            comm += '             --vol-wisharts="%s"' % options["hcp_vol_wisharts"]

        if options["hcp_cifti_wisharts"] is not None:
            comm += '             --cifti-wisharts="%s"' % options["hcp_cifti_wisharts"]

        if options["hcp_icadim_mode"] is not None:
            comm += '             --icadim-mode="%s"' % options["hcp_icadim_mode"]

        if not options["hcp_legacy_fix"]:
            comm += '             --enable-legacy-fix="FALSE"'

        if options["hcp_icafix_concatenate_only"]:
            comm += '             --concatenate-only="TRUE"'

        # -- Report command
        if groupok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test file
        tfile = None
        fullTest = None

        # -- Run
        if run and groupok:
            if options["run"] == "run":
                r, _, _, failed = pc.runExternalForFile(
                    tfile,
                    comm,
                    "Running multi-run HCP ICAFix",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], groupname],
                    fullTest=fullTest,
                    shell=True,
                    r=r,
                )

                if failed:
                    report["failed"].append(groupname)
                else:
                    report["done"].append(groupname)

                # if all ok execute PostFix if enabled
                if options["hcp_icafix_postfix"]:
                    if (
                        report["incomplete"] == []
                        and report["failed"] == []
                        and report["not ready"] == []
                    ):
                        result = executeHCPPostFix(
                            sinfo, options, hcp, run, False, groupname
                        )
                        r += result["r"]
                        report = result["report"]

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    tfile,
                    fullTest,
                    "multi-run HCP ICAFix " + groupname,
                    r,
                    overwrite=overwrite,
                )
                if passed == "done":
                    r += "\n---> multi-run HCP ICAFix can be run"
                    report["ready"].append(groupname)
                else:
                    report["skipped"].append(groupname)

        else:
            report["not ready"].append(groupname)
            if options["run"] == "run":
                r += "\n---> ERROR: images missing, skipping this group!"
            else:
                r += "\n---> ERROR: images missing, this group would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of group %s with error:\n" % (
            groupname
        )
        r += str(errormessage)
        report["failed"].append(groupname)
    except:
        r += "\n --- Failed during processing of group %s with error:\n %s\n" % (
            groupname,
            traceback.format_exc(),
        )
        report["failed"].append(groupname)

    return {"r": r, "report": report}


def hcp_post_fix(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_post_fix [... processing options]``

    Runs the PostFix step of HCP Pipeline (PostFix.sh).

    Warning:
        The code expects the input images to be named and present in the QuNex
        folder structure. The function will look into folder::

            <session id>/hcp/<session id>

        for files::

            MNINonLinear/Results/<boldname>/<boldname>_hp<highpass>_clean.nii.gz

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging  data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_icafix_bolds (str, default ''):
            Specify a list of bolds for ICAFix. You should specify how to
            group/concatenate bolds together along with bolds, e.g.
            "<group1>:<boldname1>,<boldname2>|
            <group2>:<boldname3>,<boldname4>", in this case multi-run HCP
            ICAFix will be executed, which is the default. Instead of full bold
            names, you can also  use bold tags from the batch file. If this
            parameter is not provided ICAFix will bundle all bolds together and
            execute multi-run HCP ICAFix, the concatenated file will be named
            fMRI_CONCAT_ALL. Alternatively, you can specify a comma separated
            list of bolds without groups, e.g. "<boldname1>,<boldname2>", in
            this case single-run HCP ICAFix will be executed over specified
            bolds. This is a legacy option and not recommended.

        --hcp_icafix_highpass (int, default detailed below):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_postfix_dualscene (str, default ''):
            Path to an alternative template scene, if empty HCP default dual
            scene will be used.

        --hcp_postfix_singlescene (str, default ''):
            Path to an alternative template scene, if empty HCP default single
            scene will be used.

        --hcp_postfix_reusehighpass (bool, default True):
            Whether to reuse highpass.

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folder inside the same sessions's root hcp folder.

        The final output files are::

            MNINonLinear/Results/<boldname>/
            <session id>_<boldname>_hp<highpass>_ICA_Classification_singlescreen.scene

        where highpass is the used value for the highpass filter. The
        default highpass value is 0 for multi-run HCP ICAFix and 2000 for
        single-run HCP ICAFix.

    Notes:
        Runs the PostFix step of HCP Pipeline (PostFix.sh). This step creates
        Workbench scene files that can be used to visually review the signal vs.
        noise classification generated by ICAFix.

        If the hcp_icafix_bolds parameter is not provided ICAFix will bundle
        all bolds together and execute multi-run HCP ICAFix, the
        concatenated file will be named fMRI_CONCAT_ALL. WARNING: if
        session has many bolds such processing requires a lot of
        computational resources.

        hcp_post_fix parameter mapping:

            ================================== ================================
            QuNex parameter                    HCPpipelines parameter
            ================================== ================================
            ``hcp_icafix_highpass``            ``high-pass``
            ``hcp_postfix_singlescene``        ``template-scene-single-screen``
            ``hcp_postfix_dualscene``          ``template-scene-dual-screen``
            ``hcp_postfix_reusehighpass``      ``reuse-high-pass``
            ``hcp_matlab_mode``                ``matlabrunmode``
            ================================== ================================

    Examples:
        ::

            qunex hcp_post_fix \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_matlab_mode="interpreted"

        ::

            qunex hcp_post_fix \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_icafix_bolds="GROUP_1:BOLD_1,BOLD_2|GROUP_2:BOLD_3,BOLD_4" \\
                --hcp_matlab_mode="interpreted"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP PostFix pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, "hcp_post_fix")
        doHCPOptionsCheck(options, "hcp_post_fix")
        hcp = getHCPPaths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report["boldskipped"], r = pc.use_or_skip_bold(sinfo, options, r)
        _build_skipped_report(report, bskip, options)

        # --- Parse icafix_bolds
        singleFix, icafixBolds, icafixGroups, pars_ok, r = parse_icafix_bolds(
            options, bolds, r
        )
        if not pars_ok:
            raise ge.CommandFailed("hcp_post_fix", "... invalid input parameters!")

        # --- Multi threading
        if singleFix:
            parelements = max(1, min(options["parelements"], len(icafixBolds)))
        else:
            parelements = max(1, min(options["parelements"], len(icafixGroups)))
        r += "\n\n%s %d PostFixes in parallel" % (
            pc.action("Processing", options["run"]),
            parelements,
        )

        # --- Execute
        # single fix
        if not singleFix:
            # put all group bolds together
            icafixBolds = []
            for g in icafixGroups:
                groupBolds = g["name"]
                icafixBolds.append(groupBolds)

        # create a multiprocessing Pool
        processPoolExecutor = ProcessPoolExecutor(parelements)
        # process
        f = partial(executeHCPPostFix, sinfo, options, hcp, run, singleFix)
        results = processPoolExecutor.map(f, icafixBolds)

        # merge r and report
        for result in results:
            r += result["r"]
            tempReport = result["report"]
            report["done"] += tempReport["done"]
            report["failed"] += tempReport["failed"]
            report["incomplete"] += tempReport["incomplete"]
            report["ready"] += tempReport["ready"]
            report["not ready"] += tempReport["not ready"]
            report["skipped"] += tempReport["skipped"]

        # report
        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP PostFix: bolds " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except ge.CommandFailed as e:
        r += "\n\nERROR in completing %s:\n     %s\n" % (
            e.function,
            "\n     ".join(e.report),
        )
        report = (sinfo["id"], "HCP PostFix failed")
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = (sinfo["id"], "HCP PostFix failed")
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = (sinfo["id"], "HCP PostFix failed")

    r += (
        "\n\nHCP PostFix %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, report)


def executeHCPPostFix(sinfo, options, hcp, run, singleFix, boldinfo):
    # prepare return variables
    r = ""
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    # extract data
    r += "\n\n------------------------------------------------------------"

    if singleFix:
        # highpass
        highpass = (
            2000
            if options["hcp_icafix_highpass"] is None
            else options["hcp_icafix_highpass"]
        )

        printbold, boldtarget, _ = pc.get_bold_names(boldinfo, options)

        printica = "%s_hp%s_clean.nii.gz" % (boldtarget, highpass)
        icaimg = os.path.join(hcp["hcp_nonlin"], "Results", boldtarget, printica)
        r += "\n---> %s bold ICA %s" % (
            pc.action("Processing", options["run"]),
            printica,
        )

    else:
        # highpass
        highpass = (
            0
            if options["hcp_icafix_highpass"] is None
            else options["hcp_icafix_highpass"]
        )

        printbold = boldinfo
        boldtarget = boldinfo

        printica = "%s_hp%s_clean.nii.gz" % (boldtarget, highpass)
        icaimg = os.path.join(hcp["hcp_nonlin"], "Results", boldtarget, printica)
        r += "\n---> %s group ICA %s" % (
            pc.action("Processing", options["run"]),
            printica,
        )

    try:
        boldok = True

        # --- check for ICA image
        r, boldok = pc.checkForFile2(
            r,
            icaimg,
            "\n     ... ICA %s present" % boldtarget,
            "\n     ... ERROR: ICA [%s] missing!" % icaimg,
            status=boldok,
        )

        # hcp_postfix_reusehighpass
        if options["hcp_postfix_reusehighpass"]:
            reusehighpass = "YES"
        else:
            reusehighpass = "NO"

        singlescene = os.path.join(
            hcp["hcp_base"],
            "ICAFIX/PostFixScenes/",
            "ICA_Classification_SingleScreenTemplate.scene",
        )
        if options["hcp_postfix_singlescene"] is not None:
            singlescene = options["hcp_postfix_singlescene"]

        dualscene = os.path.join(
            hcp["hcp_base"],
            "ICAFIX/PostFixScenes/",
            "ICA_Classification_DualScreenTemplate.scene",
        )
        if options["hcp_postfix_dualscene"] is not None:
            dualscene = options["hcp_postfix_dualscene"]

        # matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
                boldok = False
            else:
                matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
        else:
            if options["hcp_matlab_mode"] == "compiled":
                matlabrunmode = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                matlabrunmode = "1"
            elif options["hcp_matlab_mode"] == "octave":
                matlabrunmode = "2"
            else:
                r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                boldok = False

        # subject/session
        subject = sinfo["id"] + options["hcp_suffix"]

        comm = (
            '%(script)s \
            --study-folder="%(studyfolder)s" \
            --subject="%(subject)s" \
            --fmri-name="%(boldtarget)s" \
            --high-pass="%(highpass)s" \
            --template-scene-dual-screen="%(dualscene)s" \
            --template-scene-single-screen="%(singlescene)s" \
            --reuse-high-pass="%(reusehighpass)s" \
            --matlab-run-mode="%(matlabrunmode)s"'
            % {
                "script": os.path.join(hcp["hcp_base"], "ICAFIX", "PostFix.sh"),
                "studyfolder": sinfo["hcp"],
                "subject": subject,
                "boldtarget": boldtarget,
                "highpass": highpass,
                "dualscene": dualscene,
                "singlescene": singlescene,
                "reusehighpass": reusehighpass,
                "matlabrunmode": matlabrunmode,
            }
        )

        # -- Report command
        if boldok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Run
        if run and boldok:
            if options["run"] == "run":
                r, endlog, _, failed = pc.runExternalForFile(
                    checkfile=None,
                    run=comm,
                    description="Running HCP PostFix",
                    overwrite=False,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task="hcp_post_fix",
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], boldtarget],
                    fullTest=None,
                    shell=True,
                    r=r,
                )

                if failed:
                    report["failed"].append(printbold)
                else:
                    report["done"].append(printbold)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    None, None, "HCP PostFix " + boldtarget, r, overwrite=False
                )
                if passed is None:
                    r += "\n---> HCP PostFix can be run"
                    report["ready"].append(printbold)
                else:
                    report["skipped"].append(printbold)

        else:
            report["not ready"].append(printbold)
            if options["run"] == "run":
                r += "\n---> ERROR: something missing, skipping this BOLD!"
            else:
                r += "\n---> ERROR: something missing, this BOLD would be skipped!"

        # log beautify
        r += "\n\n"

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of bold %s with error:\n" % (printbold)
        r += str(errormessage)
        report["failed"].append(printbold)
    except:
        r += "\n --- Failed during processing of bold %s with error:\n %s\n" % (
            printbold,
            traceback.format_exc(),
        )
        report["failed"].append(printbold)

    return {"r": r, "report": report}


def hcp_reapply_fix(sinfo, options, overwrite=True, thread=0):
    """
    ``hcp_reapply_fix [... processing options]``

    Runs the ReApplyFix step of HCP Pipeline
    (ReApplyFixMultiRunPipeline.sh or ReApplyFixPipeline.sh).

    Warning:
        The code expects the input images to be named and present in the QuNex
        folder structure. The function will look into folder::

            <session id>/hcp/<session id>

        for files::

            MNINonLinear/Results/<boldname>/<boldname>.nii.gz

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_icafix_bolds (str, default ''):
            Specify a list of bolds for ICAFix. You should specify how to
            group/concatenate bolds together along with bolds, e.g.
            "<group1>:<boldname1>,<boldname2>|
            <group2>:<boldname3>,<boldname4>", in this case multi-run HCP
            ICAFix will be executed, which is the default. Instead of full bold
            names, you can also  use bold tags from the batch file. If this
            parameter is not provided ICAFix will bundle all bolds together and
            execute multi-run HCP ICAFix, the concatenated file will be named
            fMRI_CONCAT_ALL. Alternatively, you can specify a comma separated
            list of bolds without groups, e.g. "<boldname1>,<boldname2>", in
            this case single-run HCP ICAFix will be executed over specified
            bolds. This is a legacy option and not recommended.

        --hcp_icafix_highpass (int, default detailed below):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_icafix_domotionreg (str, default detailed below):
            Whether to regress motion parameters as part of the cleaning. The
            default value for single-run HCP ICAFix is [TRUE], while the
            default for multi-run HCP ICAFix is [FALSE].

        --hcp_icafix_deleteintermediates (str, default 'FALSE'):
            If TRUE, deletes both the concatenated high-pass filtered and
            non-filtered timeseries files that are prerequisites to FIX
            cleaning.

        --hcp_icafix_regname (str, default 'NONE'):
            Specifies surface registration name. If 'NONE' MSMSulc will be used.

        --hcp_lowresmesh (int, default 32):
            Specifies the low res mesh number.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --longitudinal:
            Set this flag if you are running the longitudinal variant of this
            command.

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folder inside the same sessions's root hcp folder.

        The final clean ICA file can be found in::

            MNINonLinear/Results/<boldname>/<boldname>_hp<highpass>_clean.nii.gz,

        where highpass is the used value for the highpass filter. The
        default highpass value is 0 for multi-run HCP ICAFix and 2000 for
        single-run HCP ICAFix.

    Notes:
        Runs the ReApplyFix step of HCP Pipeline. This function executes two
        steps, first it applies the hand reclassifications of noise and
        signal components from FIX (ApplyHandReClassifications.sh) using the
        ReclassifyAsNoise.txt and ReclassifyAsSignal.txt input files. Next it
        executes the HCP Pipeline's ReApplyFix or ReApplyFixMulti
        (ReApplyFixMultiRunPipeline.sh or ReApplyFixPipeline.sh).

        If the hcp_icafix_bolds parameter is not provided ICAFix will bundle
        all bolds together and execute multi-run HCP ICAFix, the
        concatenated file will be named fMRI_CONCAT_ALL. WARNING: if
        session has many bolds such processing requires a lot of
        computational resources.

        hcp_reapply_fix parameter mapping:

            ================================== =======================
            QuNex parameter                    HCPpipelines parameter
            ================================== =======================
            ``hcp_icafix_highpass``            ``high-pass``
            ``hcp_icafix_regname``             ``reg-name``
            ``hcp_lowresmesh``                 ``low-res-mesh``
            ``hcp_icafix_domotionreg``         ``motion-regression``
            ``hcp_icafix_deleteintermediates`` ``delete-intermediates``
            ``hcp_matlab_mode``                ``matlabrunmode``
            ``hcp_clean_substring``            ``clean-substring``
            ``hcp_config``                     ``config``
            ``hcp_icafix_processingmode``      ``processing-mode``
            ``hcp_icafix_icadim_mode``         ``icadim-mode``
            ``hcp_longitudinal_template``      ``longitudinal-template``
            ``longitudinal``                   ``is-longitudinal``
            ================================== =======================

    Examples:
        ::

            qunex hcp_reapply_fix \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_matlab_mode="interpreted"

        ::

            qunex hcp_reapply_fix \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_icafix_bolds="GROUP_1:BOLD_1,BOLD_2|GROUP_2:BOLD_3,BOLD_4" \\
                --hcp_matlab_mode="interpreted"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP ReApplyFix pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, "hcp_reapply_fix")
        doHCPOptionsCheck(options, "hcp_reapply_fix")
        hcp = getHCPPaths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report["boldskipped"], r = pc.use_or_skip_bold(sinfo, options, r)
        _build_skipped_report(report, bskip, options)

        # --- Parse icafix_bolds
        singleFix, icafixBolds, icafixGroups, pars_ok, r = parse_icafix_bolds(
            options, bolds, r
        )
        if not pars_ok:
            raise ge.CommandFailed("hcp_reapply_fix", "... invalid input parameters!")

        # --- Multi threading
        if singleFix:
            parelements = max(1, min(options["parelements"], len(icafixBolds)))
        else:
            parelements = max(1, min(options["parelements"], len(icafixGroups)))
        r += "\n\n%s %d ReApplyFixes in parallel" % (
            pc.action("Processing", options["run"]),
            parelements,
        )

        # --- Execute
        # single fix
        if singleFix:
            # create a multiprocessing Pool
            processPoolExecutor = ProcessPoolExecutor(parelements)
            # process
            f = partial(executeHCPSingleReApplyFix, sinfo, options, hcp, run)
            results = processPoolExecutor.map(f, icafixBolds)

            # merge r and report
            for result in results:
                r += result["r"]
                tempReport = result["report"]
                report["done"] += tempReport["done"]
                report["failed"] += tempReport["failed"]
                report["incomplete"] += tempReport["incomplete"]
                report["ready"] += tempReport["ready"]
                report["not ready"] += tempReport["not ready"]
                report["skipped"] += tempReport["skipped"]

        # multi fix
        else:
            # create a multiprocessing Pool
            processPoolExecutor = ProcessPoolExecutor(parelements)
            # process
            f = partial(executeHCPMultiReApplyFix, sinfo, options, hcp, run)
            results = processPoolExecutor.map(f, icafixGroups)

            # merge r and report
            for result in results:
                r += result["r"]
                tempReport = result["report"]
                report["done"] += tempReport["done"]
                report["failed"] += tempReport["failed"]
                report["incomplete"] += tempReport["incomplete"]
                report["ready"] += tempReport["ready"]
                report["not ready"] += tempReport["not ready"]
                report["skipped"] += tempReport["skipped"]

        # report
        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP ReApplyFix: bolds " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except ge.CommandFailed as e:
        r += "\n\nERROR in completing %s:\n     %s\n" % (
            e.function,
            "\n     ".join(e.report),
        )
        report = (sinfo["id"], "HCP ReApplyFix failed")
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = (sinfo["id"], "HCP ReApplyFix failed")
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = (sinfo["id"], "HCP ReApplyFix failed")

    r += (
        "\n\nHCP ReApplyFix %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, report)


def executeHCPSingleReApplyFix(sinfo, options, hcp, run, boldinfo):

    printbold, boldtarget, _ = pc.get_bold_names(boldinfo, options)

    # prepare return variables
    r = ""
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # run HCP hand reclassification
        r += "\n------------------------------------------------------------"
        r += "\n---> Executing HCP Hand reclassification for bold: %s\n" % printbold
        result = executeHCPHandReclassification(
            sinfo, options, hcp, run, True, boldtarget, printbold
        )

        # merge r
        r += result["r"]

        # move on to ReApplyFix
        rcReport = result["report"]
        if (
            rcReport["incomplete"] == []
            and rcReport["failed"] == []
            and rcReport["not ready"] == []
        ):
            boldok = True

            # highpass
            highpass = (
                2000
                if options["hcp_icafix_highpass"] is None
                else options["hcp_icafix_highpass"]
            )

            # matlab run mode, compiled=0, interpreted=1, octave=2
            matlabrunmode = None
            if options["hcp_matlab_mode"] is None:
                if "FSL_FIX_MATLAB_MODE" not in os.environ:
                    r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
                    boldok = False
                else:
                    matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
            else:
                if options["hcp_matlab_mode"] == "compiled":
                    matlabrunmode = "0"
                elif options["hcp_matlab_mode"] == "interpreted":
                    matlabrunmode = "1"
                elif options["hcp_matlab_mode"] == "octave":
                    matlabrunmode = "2"
                else:
                    r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                    boldok = False

            comm = (
                '%(script)s \
                --path="%(path)s" \
                --subject="%(subject)s" \
                --fmri-name="%(boldtarget)s" \
                --high-pass="%(highpass)s" \
                --reg-name="%(regname)s" \
                --low-res-mesh="%(lowresmesh)s" \
                --matlab-run-mode="%(matlabrunmode)s" \
                --motion-regression="%(motionregression)s" \
                --delete-intermediates="%(deleteintermediates)s"'
                % {
                    "script": os.path.join(
                        hcp["hcp_base"], "ICAFIX", "ReApplyFixPipeline.sh"
                    ),
                    "path": sinfo["hcp"],
                    "subject": sinfo["id"] + options["hcp_suffix"],
                    "boldtarget": boldtarget,
                    "highpass": highpass,
                    "regname": options["hcp_icafix_regname"],
                    "lowresmesh": options["hcp_lowresmesh"],
                    "matlabrunmode": matlabrunmode,
                    "motionregression": (
                        "TRUE"
                        if options["hcp_icafix_domotionreg"] is None
                        else options["hcp_icafix_domotionreg"]
                    ),
                    "deleteintermediates": options["hcp_icafix_deleteintermediates"],
                }
            )

            if options["hcp_clean_substring"] is not None:
                comm += (
                    '             --clean-substring="%s"'
                    % options["hcp_clean_substring"]
                )

            # -- Report command
            if boldok:
                r += "\n------------------------------------------------------------\n"
                r += "Running HCP Pipelines command via QuNex:\n\n"
                r += comm.replace("--", "\n    --").replace("             ", "")
                r += "\n------------------------------------------------------------\n"

            # -- Test files
            # postfix
            postfix = "%s%s_hp%s_clean.dtseries.nii" % (
                boldtarget,
                "_Atlas",
                highpass,
            )
            if (
                options["hcp_icafix_regname"] != "NONE"
                and options["hcp_icafix_regname"] != ""
            ):
                postfix = "%s%s_%s_hp%s_clean.dtseries.nii" % (
                    boldtarget,
                    "_Atlas",
                    options["hcp_icafix_regname"],
                    highpass,
                )

            tfile = os.path.join(hcp["hcp_nonlin"], "Results", boldtarget, postfix)
            fullTest = None

            # -- Run
            if run and boldok:
                if options["run"] == "run":
                    r, _, _, failed = pc.runExternalForFile(
                        tfile,
                        comm,
                        "Running single-run HCP ReApplyFix",
                        overwrite=True,
                        thread=sinfo["id"],
                        remove=options["log"] == "remove",
                        task=options["command_ran"],
                        logfolder=options["comlogs"],
                        logtags=[options["logtag"], boldtarget],
                        fullTest=fullTest,
                        shell=True,
                        r=r,
                    )

                    if failed:
                        report["failed"].append(printbold)
                    else:
                        report["done"].append(printbold)

                # -- just checking
                else:
                    passed, _, r, failed = pc.checkRun(
                        tfile, fullTest, "single-run HCP ReApplyFix " + boldtarget, r
                    )
                    if passed is None:
                        r += "\n---> single-run HCP ReApplyFix can be run"
                        report["ready"].append(printbold)
                    else:
                        report["skipped"].append(printbold)

            else:
                report["not ready"].append(printbold)
                if options["run"] == "run":
                    r += "\n---> ERROR: something missing, skipping this BOLD!"
                else:
                    r += "\n---> ERROR: something missing, this BOLD would be skipped!"
                # log beautify
                r += "\n\n"

        else:
            r += "\n---> ERROR: Hand reclassification failed for bold: %s!" % printbold
            report["failed"].append(printbold)
            boldok = False

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of bold %s with error:\n" % (printbold)
        r += str(errormessage)
        report["failed"].append(printbold)
    except:
        r += "\n --- Failed during processing of bold %s with error:\n %s\n" % (
            printbold,
            traceback.format_exc(),
        )
        report["failed"].append(printbold)

    return {"r": r, "report": report}


def executeHCPMultiReApplyFix(sinfo, options, hcp, run, group):
    # get group data
    groupname = group["name"]
    bolds = group["bolds"]

    # prepare return variables
    r = ""
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        r += "\n------------------------------------------------------------"
        r += "\n---> %s group %s" % (pc.action("Processing", options["run"]), groupname)
        groupok = True

        # --- check for bold images and prepare images parameter
        boldtargets = ""

        # check if files for all bolds exist
        for boldinfo in bolds:
            # boldok
            boldok = True

            printbold, boldtarget, _ = pc.get_bold_names(boldinfo, options)

            boldimg = os.path.join(
                hcp["hcp_nonlin"], "Results", boldtarget, "%s.nii.gz" % (boldtarget)
            )
            r, boldok = pc.checkForFile2(
                r,
                boldimg,
                "\n     ... bold image %s present" % boldtarget,
                "\n     ... ERROR: bold image [%s] missing!" % boldimg,
                status=boldok,
            )

            if not boldok:
                groupok = False
                break
            else:
                # add @ separator
                if boldtargets != "":
                    boldtargets = boldtargets + "@"

                # add latest image
                boldtargets = boldtargets + boldtarget

        # run HCP hand reclassification if not longitudinal
        if not options["longitudinal"]:
            r += (
                "\n---> Executing HCP Hand reclassification for group: %s\n" % groupname
            )
            result = executeHCPHandReclassification(
                sinfo, options, hcp, run, False, groupname, groupname
            )

            # merge r
            r += result["r"]

            # check if hand reclassification was OK
            rcReport = result["report"]
        else:
            rcReport = report

        if (
            rcReport["incomplete"] == []
            and rcReport["failed"] == []
            and rcReport["not ready"] == []
        ):
            groupok = True

            # matlab run mode, compiled=0, interpreted=1, octave=2
            matlabrunmode = None
            if options["hcp_matlab_mode"] is None:
                if "FSL_FIX_MATLAB_MODE" not in os.environ:
                    r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
                else:
                    matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
            else:
                if options["hcp_matlab_mode"] == "compiled":
                    matlabrunmode = "0"
                elif options["hcp_matlab_mode"] == "interpreted":
                    matlabrunmode = "1"
                elif options["hcp_matlab_mode"] == "octave":
                    matlabrunmode = "2"
                else:
                    r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                    groupok = False

            # highpass
            highpass = (
                0
                if options["hcp_icafix_highpass"] is None
                else options["hcp_icafix_highpass"]
            )

            # path
            path = sinfo["hcp"]

            # longitudinal
            if options["longitudinal"]:
                studyfolder = gc.deduce_folders(options)["basefolder"]
                if not studyfolder:
                    r += "\nERROR: cannot deduce the QuNex study folder from provided parameters! Please provide the sessionsfolder or the studyfolder parameter."
                    groupok = False
                # replace path
                path = os.path.join(studyfolder, "subjects", sinfo["subject"])

            comm = (
                '%(script)s \
                --path="%(path)s" \
                --session="%(session)s" \
                --fmri-names="%(boldtargets)s" \
                --concat-fmri-name="%(groupname)s" \
                --high-pass="%(highpass)s" \
                --reg-name="%(regname)s" \
                --low-res-mesh="%(lowresmesh)s" \
                --matlab-run-mode="%(matlabrunmode)s"'
                % {
                    "script": os.path.join(
                        hcp["hcp_base"], "ICAFIX", "ReApplyFixMultiRunPipeline.sh"
                    ),
                    "path": path,
                    "session": sinfo["id"] + options["hcp_suffix"],
                    "boldtargets": boldtargets,
                    "groupname": groupname,
                    "highpass": highpass,
                    "regname": options["hcp_icafix_regname"],
                    "lowresmesh": options["hcp_lowresmesh"],
                    "matlabrunmode": matlabrunmode,
                }
            )

            if options["hcp_icafix_domotionreg"] is not None:
                comm += (
                    '             --motionregression="%s"'
                    % options["hcp_icafix_domotionreg"]
                )

            if options["hcp_icafix_deleteintermediates"] is not None:
                comm += (
                    '             --deleteintermediates="%s"'
                    % options["hcp_icafix_deleteintermediates"]
                )

            if options["hcp_icafix_processingmode"] is not None:
                comm += (
                    '             --processing-mode="%s"'
                    % options["hcp_icafix_processingmode"]
                )

            if options["hcp_icafix_icadim_mode"] is not None:
                comm += (
                    '             --icadim-mode="%s"'
                    % options["hcp_icafix_icadim_mode"]
                )

            if options["hcp_clean_substring"] is not None:
                comm += (
                    '             --clean-substring="%s"'
                    % options["hcp_clean_substring"]
                )

            if options["hcp_config"] is not None:
                comm += '             --config="%s"' % options["hcp_config"]

            # -- Longitudinal parameters
            if options["longitudinal"]:
                comm += "                --is-longitudinal=1"
                comm += (
                    "                --longitudinal-session="
                    + f"{sinfo['id']}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"
                )

            # -- Report command
            if groupok:
                r += "\n------------------------------------------------------------\n"
                r += "Running HCP Pipelines command via QuNex:\n\n"
                r += comm.replace("--", "\n    --").replace("             ", "")
                r += "\n------------------------------------------------------------\n"

            # -- Test files
            # postfix
            postfix = "%s%s_hp%s_clean.dtseries.nii" % (
                groupname,
                "_Atlas",
                highpass,
            )
            if (
                options["hcp_icafix_regname"] != "NONE"
                and options["hcp_icafix_regname"] != ""
            ):
                postfix = "%s%s_%s_hp%s_clean.dtseries.nii" % (
                    groupname,
                    "_Atlas",
                    options["hcp_icafix_regname"],
                    highpass,
                )

            tfile = os.path.join(hcp["hcp_nonlin"], "Results", groupname, postfix)
            fullTest = None

            # -- Run
            if run and groupok:
                if options["run"] == "run":
                    logtags = [options["logtag"], groupname]
                    if options["longitudinal"]:
                        logtags.append("long")

                    r, _, _, failed = pc.runExternalForFile(
                        tfile,
                        comm,
                        "Running multi-run HCP ReApplyFix",
                        overwrite=True,
                        thread=sinfo["id"],
                        remove=options["log"] == "remove",
                        task=options["command_ran"],
                        logfolder=options["comlogs"],
                        logtags=logtags,
                        fullTest=fullTest,
                        shell=True,
                        r=r,
                    )

                    if failed:
                        report["failed"].append(groupname)
                    else:
                        report["done"].append(groupname)

                # -- just checking
                else:
                    passed, _, r, failed = pc.checkRun(
                        tfile, fullTest, "multi-run HCP ReApplyFix " + groupname, r
                    )
                    if passed is None:
                        r += "\n---> multi-run HCP ReApplyFix can be run"
                        report["ready"].append(groupname)
                    else:
                        report["skipped"].append(groupname)

            else:
                report["not ready"].append(groupname)
                if options["run"] == "run":
                    r += "\n---> ERROR: something missing, skipping this group!"
                else:
                    r += "\n---> ERROR: something missing, this group would be skipped!"
                # log beautify
                r += "\n\n"

        else:
            r += "\n---> ERROR: Hand reclassification failed for bold: %s!" % printbold

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of group %s with error:\n" % (
            groupname
        )
        r += str(errormessage)
        report["failed"].append(groupname)
    except:
        r += "\n --- Failed during processing of group %s with error:\n %s\n" % (
            groupname,
            traceback.format_exc(),
        )
        report["failed"].append(groupname)

    return {"r": r, "report": report}


def executeHCPHandReclassification(
    sinfo, options, hcp, run, singleFix, boldtarget, printbold
):
    # prepare return variables
    r = ""
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        r += "\n---> %s ICA %s" % (pc.action("Processing", options["run"]), printbold)
        boldok = True

        # load parameters or use default values
        if singleFix:
            highpass = (
                2000
                if options["hcp_icafix_highpass"] is None
                else options["hcp_icafix_highpass"]
            )
        else:
            highpass = (
                0
                if options["hcp_icafix_highpass"] is None
                else options["hcp_icafix_highpass"]
            )

        # --- check for bold image
        icaimg = os.path.join(
            hcp["hcp_nonlin"],
            "Results",
            boldtarget,
            "%s_hp%s_clean.nii.gz" % (boldtarget, highpass),
        )
        r, boldok = pc.checkForFile2(
            r,
            icaimg,
            "\n     ... ICA %s present" % boldtarget,
            "\n     ... ERROR: ICA [%s] missing!" % icaimg,
            status=boldok,
        )

        comm = (
            '%(script)s \
            --study-folder="%(studyfolder)s" \
            --subject="%(subject)s" \
            --fmri-name="%(boldtarget)s" \
            --high-pass="%(highpass)s"'
            % {
                "script": os.path.join(
                    hcp["hcp_base"], "ICAFIX", "ApplyHandReClassifications.sh"
                ),
                "studyfolder": sinfo["hcp"],
                "subject": sinfo["id"] + options["hcp_suffix"],
                "boldtarget": boldtarget,
                "highpass": highpass,
            }
        )

        # -- Report command
        if boldok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test files
        tfile = os.path.join(
            hcp["hcp_nonlin"],
            "Results",
            boldtarget,
            "%s_hp%s.ica" % (boldtarget, highpass),
            "HandNoise.txt",
        )
        fullTest = None

        # -- Run
        if run and boldok:
            if options["run"] == "run":
                r, endlog, _, failed = pc.runExternalForFile(
                    tfile,
                    comm,
                    "Running HCP HandReclassification",
                    overwrite=True,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task="hcp_HandReclassification",
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], boldtarget],
                    fullTest=fullTest,
                    shell=True,
                    r=r,
                )

                if failed:
                    report["failed"].append(printbold)
                else:
                    report["done"].append(printbold)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    tfile,
                    fullTest,
                    "HCP HandReclassification " + boldtarget,
                    r,
                    overwrite=True,
                )
                if passed is None:
                    r += "\n---> HCP HandReclassification can be run"
                    report["ready"].append(printbold)
                else:
                    report["skipped"].append(printbold)

        else:
            report["not ready"].append(printbold)
            if options["run"] == "run":
                r += "\n---> ERROR: something missing, skipping this BOLD!"
            else:
                r += "\n---> ERROR: something missing, this BOLD would be skipped!"

        # log beautify
        r += "\n"

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of bold %s with error:\n" % (printbold)
        r = str(errormessage)
        report["failed"].append(printbold)
    except:
        r += "\n --- Failed during processing of bold %s with error:\n %s\n" % (
            printbold,
            traceback.format_exc(),
        )
        report["failed"].append(printbold)

    return {"r": r, "report": report}


def parse_msmall_bolds(options, bolds, r):
    # parse the same way as with icafix first
    single_run, _, icafix_groups, pars_ok, r = parse_icafix_bolds(
        options, bolds, r, True
    )

    msmall_groups = []

    for icafix_group in icafix_groups:
        # validate that msmall bolds is a subset of icafixGroups
        if options["hcp_msmall_bolds"] is not None:
            msmall_bolds = options["hcp_msmall_bolds"].split(",")
            hcp_msmall_bolds = []

            for mb in msmall_bolds:
                hmb = None
                for b in bolds:
                    # does the name match?
                    if (
                        "filename" in b
                        and mb == b["filename"]
                        and options["hcp_filename"] == "userdefined"
                    ):
                        hmb = b["filename"]
                        break
                    # does the number match?
                    if "bold_number" in b and mb == b["bold_number"]:
                        hmb = f"{options['hcp_bold_prefix']}{b}"
                        break
                    # does the tag match?
                    if "task" in b and mb == b["task"]:
                        if "filename" in b and options["hcp_filename"] == "userdefined":
                            hmb = b["filename"]
                            break
                        else:
                            hmb = f"{options['hcp_bold_prefix']}{b[0]}"
                            break

                if hmb is None:
                    r += f"\n---> ERROR: bold {mb} used in hcp_msmall_bolds but not found in hcp_icafix_bolds!"
                    pars_ok = False
                    break
                else:
                    if hmb not in hcp_msmall_bolds:
                        hcp_msmall_bolds.append(hmb)

            icafix_group["msmall_bolds"] = hcp_msmall_bolds
        else:
            msmall_bolds = []
            for bold in icafix_group["bolds"]:
                if "filename" in bold and options["hcp_filename"] == "userdefined":
                    msmall_bolds.append(bold["filename"])
                else:
                    msmall_bolds.append(
                        f"{options['hcp_bold_prefix']}{bold['bold_number']}"
                    )

            icafix_group["msmall_bolds"] = msmall_bolds

        msmall_groups.append(icafix_group)

    return (msmall_groups, single_run, pars_ok, r)


def hcp_msmall(sinfo, options, overwrite=True, thread=0):
    """
    ``hcp_msmall [... processing options]``

    Runs the MSMAll step of the HCP Pipeline (MSMAllPipeline.sh).

    Warning:
        The code expects the input images to be named and present in the QuNex
        folder structure. The function will look into folder::

            <session id>/hcp/<session id>

        for files::

            MNINonLinear/Results/<boldname>/
            <boldname>_<hcp_cifti_tail>_hp<hcp_highpass>_clean.dtseries.nii

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. msmall groups) to run in parallel.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_icafix_bolds (str, default ''):
            List of bolds on which ICAFix was applied, with the same format
            as for ICAFix. Typically, this should be identical to the list
            used in the ICAFix run. If multi-run ICAFix was run with two or
            more groups then HCP MSMAll will be executed over the first
            specified group (and the scans listed for hcp_msmall_bolds must
            be limited to scans in the first concatenation group as well).
            If not provided MSMAll will assume multi-run ICAFix was executed
            with all bolds bundled together in a single concatenation called
            fMRI_CONCAT_ALL (i.e., same default behavior as in ICAFix).

        --hcp_msmall_bolds (str, default detailed below):
            A comma separated list that defines the bolds that will be used
            in the computation of the MSMAll registration. Typically, this
            should be limited to resting-state scans. Specified bolds have
            to be a subset of bolds used from the hcp_icafix_bolds parameter
            [if not specified all bolds specified in hcp_icafix_bolds will
            be used, which is probably NOT what you want to do if
            hcp_icafix_bolds includes non-resting-state scans].

        --hcp_icafix_highpass (int, default detailed below):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix. Should be identical to the value
            used for ICAFix.

        --hcp_msmall_outfmriname (str, default 'rfMRI_REST'):
            The name which will be given to the concatenation of scans specified
            by the hcp_msmall_bold parameter.

        --hcp_msmall_templates (str, default <HCPPIPEDIR>/global/templates/MSMAll):
            Path to directory containing MSMAll template files.

        --hcp_msmall_outregname (str, default 'MSMAll_InitialReg'):
            Output registration name.

        --hcp_hiresmesh (int, default 164):
            High resolution mesh node count.

        --hcp_lowresmesh (int, default 32):
            Low resolution mesh node count.

        --hcp_regname (str, default 'MSMSulc'):
            Input registration name.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_msmall_procstring (str, default <hcp_cifti_tail>_hp<hcp_highpass>_clean):
            Identification for FIX cleaned dtseries to use.

        --hcp_msmall_resample (str, default 'TRUE'):
            Whether to automatically run HCP DeDriftAndResample if HCP MSMAll
            finishes successfully.

        --hcp_msmall_myelin_target (str, default 'Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii'):
            Myelin map target, will use
            Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii
            by default.

        --hcp_msmall_module_name (str, default 'MSMAll.sh'):
            The name of script or code used to run registration.

        --hcp_msmall_iteration_modes (str, default 'CA_CAT'):
            Specifies what modalities:
                - C=RSN Connectivity,
                - A=Myelin Architecture,
                - T=RSN Topography.

            So, the default CA_CAT means one iteration using RSN Connectivity
            and Myelin Architecture, followed by another iteration using RSN
            Connectivity, Myelin Architecture, and RSN Topography.

        --hcp_msmall_method (str, default 'WRN'):
            Possible values: DR, DRZ, DRN, WR, WRZ, WRN.

        --hcp_msmall_use_migp (flag, not set by default):
            Whether to use MIGP (MELODIC's Incremental Group
            Component Analysis)

        --hcp_msmall_ica_dim (int, default 40):
            ICA (Independent Component Analysis) dimensions.

        --hcp_msmall_low_sica_dims (str, default '7@8@9@10@11@12@13@14@15@16@17@18@19@20@21'):
            The low sICA dimensionalities to use for determining weighting for
            individual projection.

        --hcp_msmall_vn (flag, not set by default):
            Whether to perform variance normalization.

        --hcp_msmall_reg_conf_path (str, 'MSMAllStrainFinalconf1to1_1to3'):
            Either the relative path where the registration configuration exists
            in MSMCONFIGDIR, or an absolute.

        --hcp_msmall_reg_vars (str, 'NONE'):
            The registration configure variables to override instead of using
            the configuration file. Please use quotes without space between
            parameters, e.g. 'REGNUMBER=1,REGPOWER=3'.

        --hcp_msmall_rsn_template (str, 'rfMRI_REST_Atlas_MSMAll_2_d41_WRN_DeDrift_hp2000_clean_PCA.ica_dREPLACEDIM_ROW_vn/melodic_oIC.dscalar.nii'):
            Alternate rsn template file, relative to the --msm-all-templates
            folder.

        --hcp_msmall_rsn_weights (str, 'rfMRI_REST_Atlas_MSMAll_2_d41_WRN_DeDrift_hp2000_clean_PCA.ica_dREPLACEDIM_ROW_vn/Weights.txt'):
            Alternate rsn weights file, relative to the --msm-all-templates
            folder.

        --hcp_msmall_topography_roi (str, 'Q1-Q6_RelatedParcellation210.atlas_Topographic_ROIs.32k_fs_LR.dscalar.nii'):
            Alternate topography roi file, relative to the --msm-all-templates
            folder.

        --hcp_msmall_topography_target (str, 'Q1-Q6_RelatedParcellation210.atlas_Topography.32k_fs_LR.dscalar.nii'):
            Alternate topography target, relative to the --msm-all-templates
            folder.

        --hcp_msmall_no_ind_mean (flag, not set by default):
            Whether not to use the mean of the individual myelin map as the
            group reference map's mean.

        --hcp_msmall_start_frame (int, 1):
            The starting frame to choose from each fMRI run (inclusive),
            only applied for single runs.

        --hcp_msmall_end_frame (int):
            The ending frame to choose from each fMRI run (inclusive),
            only applied for single runs.

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folder inside the same sessions's root hcp folder.

    Notes:
        Runs the MSMAll step of the HCP Pipeline. This function executes two
        steps, it first runs MSMAll and if it completes successfully it then
        executes the DeDriftAndResample step. To disable this automatic
        execution of DeDriftAndResample set hcp_msmall_resample to FALSE.

        The MSMAll step computes the MSMAll registration based on
        resting-state connectivity, resting-state topography, and myelin-map
        architecture. The DeDriftAndResample step applies the MSMAll
        registration to a specified set of maps and fMRI runs.

        MSMAll is intended for use with fMRI runs cleaned with hcp_icafix.
        Except for specialized/expert-user situations, the hcp_icafix_bolds
        parameter should be identical to what was used in hcp_icafix. If
        hcp_icafix_bolds is not provided MSMAll/DeDriftAndResample will
        assume multi-run ICAFix was executed with all bolds bundled
        together in a single concatenation called fMRI_CONCAT_ALL. (This is
        the default behavior if hcp_icafix_bolds parameter is not provided
        in the case of hcp_icafix).

        A key parameter in hcp_msmall is `hcp_msmall_bolds`, which controls
        the fMRI runs that enter into the computation of the MSMAll
        registration. Since MSMAll registration was designed to be computed
        from resting-state scans, this should be a list of the resting-state
        fMRI scans that you want to contribute to the computation of the
        MSMAll registration.

        However, it is perfectly fine to apply the MSMAll registration to
        task fMRI scans in the DeDriftAndResample step. The fMRI scans to
        which the MSMAll registration is applied are controlled by the
        `hcp_icafix_bolds` parameter, since typically one wants to apply the
        MSMAll registration to the same full set of fMRI scans that were
        cleaned using hcp_icafix.

        hcp_msmall parameter mapping:

            ================================ ===============================
            QuNex parameter                  HCPpipelines parameter
            ================================ ===============================
            ``hcp_msmall_outfmriname``       ``output-fmri-name``
            ``hcp_icafix_highpass``          ``high-pass``
            ``hcp_msmall_templates``         ``msm-all-templates``
            ``hcp_msmall_outregname``        ``output-registration-name``
            ``hcp_hiresmesh``                ``high-res-mesh``
            ``hcp_lowresmesh``               ``low-res-mesh``
            ``hcp_regname``                  ``input-registration-name``
            ``hcp_matlab_mode``              ``matlab-run-mode``
            ``hcp_msmall_procstring``        ``fmri-proc-string``
            ``hcp_msmall_myelin_target``     ``myelin-target-file``
            ``hcp_msmall_module_name``       ``module-name``
            ``hcp_msmall_iteration_modes``   ``iteration-modes``
            ``hcp_msmall_method``            ``method``
            ``hcp_msmall_use_migp``          ``use-migp``
            ``hcp_msmall_ica_dim``           ``ica-dim``
            ``hcp_msmall_low_sica_dims``     ``low-sica-dims``
            ``hcp_msmall_vn``                ``vn``
            ``hcp_msmall_reg_conf_path``     ``registration-configure-path``
            ``hcp_msmall_reg_vars``          ``registration-configure-override-variables``
            ``hcp_msmall_rsn_template``      ``rsn-template-file``
            ``hcp_msmall_rsn_weights``       ``rsn-weights-file``
            ``hcp_msmall_topography_roi``    ``topography-roi-file``
            ``hcp_msmall_topography_target`` ``topography-target-file``
            ``hcp_msmall_no_ind_mean``       ``use-ind-mean``
            ``hcp_msmall_start_frame``       ``start-frame``
            ``hcp_msmall_end_frame``         ``end-frame``
            ================================ ===============================

    Examples:
        HCP MSMAll after application of single-run ICAFix::

            qunex hcp_msmall \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_icafix_bolds="REST_1,REST_2,TASK_1,TASK_2" \\
                --hcp_msmall_bolds="REST_1,REST_2" \\
                --hcp_matlab_mode="interpreted"

        HCP MSMAll after application of multi-run ICAFix::

            qunex hcp_msmall \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_icafix_bolds="GROUP_1:REST_1,REST_2,TASK_1|GROUP_2:REST_3,TASK_2" \\
                --hcp_msmall_bolds="REST_1,REST_2" \\
                --hcp_matlab_mode="interpreted"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP MSMAll pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, "hcp_msmall")
        doHCPOptionsCheck(options, "hcp_msmall")
        hcp = getHCPPaths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report["boldskipped"], r = pc.use_or_skip_bold(sinfo, options, r)
        _build_skipped_report(report, bskip, options)

        # --- Parse msmall_bolds
        msmall_groups, single_run, pars_ok, r = parse_msmall_bolds(options, bolds, r)

        if not pars_ok:
            raise ge.CommandFailed("hcp_msmall", "... invalid input parameters!")

        # execute in parallel use parelements
        parelements = max(1, min(options["parelements"], len(msmall_groups)))

        if parelements > 1:
            r += "\n\n%s %d ICAFix groups in parallel" % (
                pc.action("Processing", options["run"]),
                parelements,
            )

        # --- Execute
        # create a multiprocessing Pool
        ppe = ProcessPoolExecutor(parelements)

        # --- Execute
        # single-run
        if single_run:
            f = partial(executeHCPSingleMSMAll, sinfo, options, hcp, run)
        # multi-run
        else:
            f = partial(executeHCPMultiMSMAll, sinfo, options, hcp, run)
        results = ppe.map(f, msmall_groups)

        # merge r and report
        for result in results:
            r += result["r"]
            temp_report = result["report"]
            report["done"] += temp_report["done"]
            report["failed"] += temp_report["failed"]
            report["incomplete"] += temp_report["incomplete"]
            report["ready"] += temp_report["ready"]
            report["not ready"] += temp_report["not ready"]
            report["skipped"] += temp_report["skipped"]

        # if all ok execute DeDriftAndResample if enabled
        if options["hcp_msmall_resample"]:
            if (
                report["incomplete"] == []
                and report["failed"] == []
                and report["not ready"] == []
            ):
                # single-run
                if single_run:
                    f = partial(
                        executeHCPSingleDeDriftAndResample, sinfo, options, hcp, run
                    )
                # multi-run
                else:
                    f = partial(
                        executeHCPMultiDeDriftAndResample, sinfo, options, hcp, run
                    )
                results = ppe.map(f, msmall_groups)

                # merge r and report
                for result in results:
                    r += result["r"]
                    temp_report = result["report"]
                    report["done"] += temp_report["done"]
                    report["failed"] += temp_report["failed"]
                    report["incomplete"] += temp_report["incomplete"]
                    report["ready"] += temp_report["ready"]
                    report["not ready"] += temp_report["not ready"]
                    report["skipped"] += temp_report["skipped"]

        # report
        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP MSMAll: bolds " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except ge.CommandFailed as e:
        r += "\n\nERROR in completing %s:\n     %s\n" % (
            e.function,
            "\n     ".join(e.report),
        )
        report = (sinfo["id"], "HCP MSMAll failed")
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = (sinfo["id"], "HCP MSMAll failed")
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = (sinfo["id"], "HCP MSMAll failed")

    r += (
        "\n\nHCP MSMAll %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, report)


def executeHCPSingleMSMAll(sinfo, options, hcp, run, group):
    # prepare return variables
    r = ""
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # get data
        bolds = group["bolds"]

        # msmallBolds
        msmallBolds = None
        if group["msmall_bolds"]:
            msmallBolds = "@".join(group["msmall_bolds"])

        # outfmriname
        outfmriname = options["hcp_msmall_outfmriname"]

        r += "\n\n------------------------------------------------------------"
        r += "\n---> %s MSMAll %s" % (
            pc.action("Processing", options["run"]),
            outfmriname,
        )
        boldsok = True

        # --- check for bold images and prepare targets parameter
        # highpass value
        highpass = (
            2000
            if options["hcp_icafix_highpass"] is None
            else options["hcp_icafix_highpass"]
        )

        # fmriprocstring
        fmriprocstring = "%s_hp%s_clean" % ("_Atlas", str(highpass))
        if options["hcp_msmall_procstring"] is not None:
            fmriprocstring = options["hcp_msmall_procstring"]

        # check if files for all bolds exist
        for boldinfo in bolds:
            # set ok to true for now
            boldok = True

            printbold, boldtarget, _ = pc.get_bold_names(boldinfo, options)

            # input file check
            boldimg = os.path.join(
                hcp["hcp_nonlin"],
                "Results",
                boldtarget,
                "%s%s.dtseries.nii" % (boldtarget, fmriprocstring),
            )
            r, boldok = pc.checkForFile2(
                r,
                boldimg,
                "\n     ... bold image %s present" % boldtarget,
                "\n     ... ERROR: bold image [%s] missing!" % boldimg,
                status=boldok,
            )

            if not boldok:
                boldsok = False

            # if msmallBolds is not defined add all icafix bolds
            if msmallBolds is None:
                # add @ separator
                if msmallBolds != "":
                    msmallBolds = msmallBolds + "@"

                # add latest image
                msmallBolds = msmallBolds + boldtarget

        if options["hcp_msmall_templates"] is None:
            msmalltemplates = os.path.join(
                hcp["hcp_base"], "global", "templates", "MSMAll"
            )
        else:
            msmalltemplates = options["hcp_msmall_templates"]

        if options["hcp_msmall_myelin_target"] is None:
            myelintarget = os.path.join(
                msmalltemplates,
                "Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii",
            )
        else:
            myelintarget = options["hcp_msmall_myelin_target"]

        # matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
                boldsok = False
            else:
                matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
        else:
            if options["hcp_matlab_mode"] == "compiled":
                matlabrunmode = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                matlabrunmode = "1"
            elif options["hcp_matlab_mode"] == "octave":
                matlabrunmode = "2"
            else:
                r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                boldsok = False

        comm = (
            '%(script)s \
            --path="%(path)s" \
            --session="%(session)s" \
            --fmri-names-list="%(msmallBolds)s" \
            --multirun-fix-names="" \
            --multirun-fix-concat-name="" \
            --multirun-fix-names-to-use="" \
            --output-fmri-name="%(outfmriname)s" \
            --high-pass="%(highpass)s" \
            --fmri-proc-string="%(fmriprocstring)s" \
            --msm-all-templates="%(msmalltemplates)s" \
            --output-registration-name="%(outregname)s" \
            --high-res-mesh="%(highresmesh)s" \
            --low-res-mesh="%(lowresmesh)s" \
            --input-registration-name="%(inregname)s" \
            --myelin-target-file="%(myelintarget)s" \
            --matlab-run-mode="%(matlabrunmode)s"'
            % {
                "script": os.path.join(hcp["hcp_base"], "MSMAll", "MSMAllPipeline.sh"),
                "path": sinfo["hcp"],
                "session": sinfo["id"],
                "msmallBolds": msmallBolds,
                "outfmriname": outfmriname,
                "highpass": highpass,
                "fmriprocstring": fmriprocstring,
                "msmalltemplates": msmalltemplates,
                "outregname": options["hcp_msmall_outregname"],
                "highresmesh": options["hcp_hiresmesh"],
                "lowresmesh": options["hcp_lowresmesh"],
                "inregname": options["hcp_regname"],
                "myelintarget": myelintarget,
                "matlabrunmode": matlabrunmode,
            }
        )

        # Optional parameters
        # hcp_msmall_module_name
        if options["hcp_msmall_module_name"] is not None:
            comm += "                --module-name=" + options["hcp_msmall_module_name"]

        # hcp_msmall_iteration_modes
        if options["hcp_msmall_iteration_modes"] is not None:
            comm += (
                "                --iteration-modes="
                + options["hcp_msmall_iteration_modes"]
            )

        # hcp_msmall_method
        if options["hcp_msmall_method"] is not None:
            comm += "                --method=" + options["hcp_msmall_method"]

        # hcp_msmall_use_migp
        if options["hcp_msmall_use_migp"]:
            comm += "                --use-migp=YES"

        # hcp_msmall_ica_dim
        if options["hcp_msmall_ica_dim"] is not None:
            comm += "                --ica-dim=" + options["hcp_msmall_ica_dim"]

        # hcp_msmall_low_sica_dims
        if options["hcp_msmall_low_sica_dims"] is not None:
            comm += (
                "                --low-sica-dims=" + options["hcp_msmall_low_sica_dims"]
            )

        # hcp_msmall_vn
        if options["hcp_msmall_vn"] is not None:
            comm += "                --vn=YES"

        # hcp_msmall_reg_conf_path
        if options["hcp_msmall_reg_conf_path"] is not None:
            comm += (
                "                --registration-configure-path="
                + options["hcp_msmall_reg_conf_path"]
            )

        # hcp_msmall_reg_vars
        if options["hcp_msmall_reg_vars"] is not None:
            comm += (
                "                --registration-configure-override-variables="
                + options["hcp_msmall_reg_vars"]
            )

        # hcp_msmall_rsn_template
        if options["hcp_msmall_rsn_template"] is not None:
            comm += (
                "                --rsn-template-file="
                + options["hcp_msmall_rsn_template"]
            )

        # hcp_msmall_rsn_weights
        if options["hcp_msmall_rsn_weights"] is not None:
            comm += (
                "                --rsn-weights-file="
                + options["hcp_msmall_rsn_weights"]
            )

        # hcp_msmall_topography_roi
        if options["hcp_msmall_topography_roi"] is not None:
            comm += (
                "                --topography-roi-file="
                + options["hcp_msmall_topography_roi"]
            )

        # hcp_msmall_topography_target
        if options["hcp_msmall_topography_target"] is not None:
            comm += (
                "                --topography-target-file="
                + options["hcp_msmall_topography_target"]
            )

        # hcp_msmall_no_ind_mean
        if options["hcp_msmall_no_ind_mean"] is not None:
            comm += "                --use-ind-mean=NO"

        # hcp_msmall_start_frame
        if options["hcp_msmall_start_frame"] is not None:
            comm += "                --start-frame=" + options["hcp_msmall_start_frame"]

        # hcp_msmall_end_frame
        if options["hcp_msmall_end_frame"] is not None:
            comm += "                --end-frame=" + options["hcp_msmall_end_frame"]

        # -- Report command
        if boldsok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Run
        if run and boldsok:
            if options["run"] == "run":
                r, _, _, failed = pc.runExternalForFile(
                    None,
                    comm,
                    "Running HCP MSMAll",
                    overwrite=True,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], outfmriname],
                    fullTest=None,
                    shell=True,
                    r=r,
                )

                if failed:
                    report["failed"].append(printbold)
                else:
                    report["done"].append(printbold)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    None, None, "HCP MSMAll " + outfmriname, r, overwrite=True
                )
                if passed is None:
                    r += "\n---> HCP MSMAll can be run"
                    report["ready"].append(printbold)
                else:
                    report["skipped"].append(printbold)

        else:
            report["not ready"].append(printbold)
            if options["run"] == "run":
                r += "\n---> ERROR: something missing, skipping this BOLD!"
            else:
                r += "\n---> ERROR: something missing, this BOLD would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of bolds %s\n" % (msmallBolds)
        r += str(errormessage)
        report["failed"].append(msmallBolds)
    except:
        r += "\n --- Failed during processing of bolds %s with error:\n %s\n" % (
            msmallBolds,
            traceback.format_exc(),
        )
        report["failed"].append(msmallBolds)

    return {"r": r, "report": report}


def executeHCPMultiMSMAll(sinfo, options, hcp, run, group):
    # prepare return variables
    r = ""
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # get group data
        groupname = group["name"]
        bolds = group["bolds"]

        # outfmriname
        outfmriname = options["hcp_msmall_outfmriname"]

        r += "\n\n------------------------------------------------------------"
        r += "\n---> %s MSMAll %s" % (
            pc.action("Processing", options["run"]),
            outfmriname,
        )

        # --- check for bold images and prepare targets parameter
        boldtargets = ""

        # highpass
        highpass = (
            0
            if options["hcp_icafix_highpass"] is None
            else options["hcp_icafix_highpass"]
        )

        # fmriprocstring
        fmriprocstring = "%s_hp%s_clean" % ("_Atlas", str(highpass))
        if options["hcp_msmall_procstring"] is not None:
            fmriprocstring = options["hcp_msmall_procstring"]

        # check if files for all bolds exist
        for boldinfo in bolds:
            # set ok to true for now
            boldok = True

            _, boldtarget, _ = pc.get_bold_names(boldinfo, options)

            # input file check
            boldimg = os.path.join(
                hcp["hcp_nonlin"],
                "Results",
                boldtarget,
                "%s%s.dtseries.nii" % (boldtarget, fmriprocstring),
            )
            r, boldok = pc.checkForFile2(
                r,
                boldimg,
                "\n     ... bold image %s present" % boldtarget,
                "\n     ... ERROR: bold image [%s] missing!" % boldimg,
                status=boldok,
            )

            if not boldok:
                break
            else:
                # add @ separator
                if boldtargets != "":
                    boldtargets = boldtargets + "@"

                # add latest image
                boldtargets = boldtargets + boldtarget

        if boldok:
            # check if group file exists
            groupica = "%s_hp%s_clean.nii.gz" % (groupname, highpass)
            groupimg = os.path.join(hcp["hcp_nonlin"], "Results", groupname, groupica)
            r, boldok = pc.checkForFile2(
                r,
                groupimg,
                "\n     ... ICA %s present" % groupname,
                "\n     ... ERROR: ICA [%s] missing!" % groupimg,
                status=boldok,
            )

        if options["hcp_msmall_templates"] is None:
            msmalltemplates = os.path.join(
                hcp["hcp_base"], "global", "templates", "MSMAll"
            )
        else:
            msmalltemplates = options["hcp_msmall_templates"]

        if options["hcp_msmall_myelin_target"] is None:
            myelintarget = os.path.join(
                msmalltemplates,
                "Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii",
            )
        else:
            myelintarget = options["hcp_msmall_myelin_target"]

        # matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
                boldok = False
            else:
                matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
        else:
            if options["hcp_matlab_mode"] == "compiled":
                matlabrunmode = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                matlabrunmode = "1"
            elif options["hcp_matlab_mode"] == "octave":
                matlabrunmode = "2"
            else:
                r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                boldok = False

        # fix names to use
        fixnamestouse = "@".join(group["msmall_bolds"])

        comm = (
            '%(script)s \
            --path="%(path)s" \
            --session="%(session)s" \
            --fmri-names-list="" \
            --multirun-fix-names="%(fixnames)s" \
            --multirun-fix-concat-name="%(concatname)s" \
            --multirun-fix-names-to-use="%(fixnamestouse)s" \
            --output-fmri-name="%(outfmriname)s" \
            --high-pass="%(highpass)s" \
            --fmri-proc-string="%(fmriprocstring)s" \
            --msm-all-templates="%(msmalltemplates)s" \
            --output-registration-name="%(outregname)s" \
            --high-res-mesh="%(highresmesh)s" \
            --low-res-mesh="%(lowresmesh)s" \
            --input-registration-name="%(inregname)s" \
            --myelin-target-file="%(myelintarget)s" \
            --matlab-run-mode="%(matlabrunmode)s"'
            % {
                "script": os.path.join(hcp["hcp_base"], "MSMAll", "MSMAllPipeline.sh"),
                "path": sinfo["hcp"],
                "session": sinfo["id"] + options["hcp_suffix"],
                "fixnames": boldtargets,
                "concatname": groupname,
                "fixnamestouse": fixnamestouse,
                "outfmriname": outfmriname,
                "highpass": highpass,
                "fmriprocstring": fmriprocstring,
                "msmalltemplates": msmalltemplates,
                "outregname": options["hcp_msmall_outregname"],
                "highresmesh": options["hcp_hiresmesh"],
                "lowresmesh": options["hcp_lowresmesh"],
                "inregname": options["hcp_regname"],
                "myelintarget": myelintarget,
                "matlabrunmode": matlabrunmode,
            }
        )

        # Optional parameters
        # hcp_msmall_module_name
        if options["hcp_msmall_module_name"] is not None:
            comm += "                --module-name=" + options["hcp_msmall_module_name"]

        # hcp_msmall_iteration_modes
        if options["hcp_msmall_iteration_modes"] is not None:
            comm += (
                "                --iteration-modes="
                + options["hcp_msmall_iteration_modes"]
            )

        # hcp_msmall_method
        if options["hcp_msmall_method"] is not None:
            comm += "                --method=" + options["hcp_msmall_method"]

        # hcp_msmall_use_migp
        if options["hcp_msmall_use_migp"]:
            comm += "                --use-migp=YES"

        # hcp_msmall_ica_dim
        if options["hcp_msmall_ica_dim"] is not None:
            comm += "                --ica-dim=" + options["hcp_msmall_ica_dim"]

        # hcp_msmall_low_sica_dims
        if options["hcp_msmall_low_sica_dims"] is not None:
            comm += (
                "                --low-sica-dims=" + options["hcp_msmall_low_sica_dims"]
            )

        # hcp_msmall_vn
        if options["hcp_msmall_vn"] is not None:
            comm += "                --vn=YES"

        # hcp_msmall_reg_conf_path
        if options["hcp_msmall_reg_conf_path"] is not None:
            comm += (
                "                --registration-configure-path="
                + options["hcp_msmall_reg_conf_path"]
            )

        # hcp_msmall_reg_vars
        if options["hcp_msmall_reg_vars"] is not None:
            comm += (
                "                --registration-configure-override-variables="
                + options["hcp_msmall_reg_vars"]
            )

        # hcp_msmall_rsn_template
        if options["hcp_msmall_rsn_template"] is not None:
            comm += (
                "                --rsn-template-file="
                + options["hcp_msmall_rsn_template"]
            )

        # hcp_msmall_rsn_weights
        if options["hcp_msmall_rsn_weights"] is not None:
            comm += (
                "                --rsn-weights-file="
                + options["hcp_msmall_rsn_weights"]
            )

        # hcp_msmall_topography_roi
        if options["hcp_msmall_topography_roi"] is not None:
            comm += (
                "                --topography-roi-file="
                + options["hcp_msmall_topography_roi"]
            )

        # hcp_msmall_topography_target
        if options["hcp_msmall_topography_target"] is not None:
            comm += (
                "                --topography-target-file="
                + options["hcp_msmall_topography_target"]
            )

        # hcp_msmall_no_ind_mean
        if options["hcp_msmall_no_ind_mean"] is not None:
            comm += "                --use-ind-mean=NO"

        # -- Report command
        if boldok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Run
        if run and boldok:
            if options["run"] == "run":
                r, _, _, failed = pc.runExternalForFile(
                    None,
                    comm,
                    "Running HCP MSMAll",
                    overwrite=True,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], groupname],
                    fullTest=None,
                    shell=True,
                    r=r,
                )

                if failed:
                    report["failed"].append(groupname)
                else:
                    report["done"].append(groupname)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    None, None, "HCP MSMAll " + groupname, r, overwrite=True
                )
                if passed is None:
                    r += "\n---> HCP MSMAll can be run"
                    report["ready"].append(groupname)
                else:
                    report["skipped"].append(groupname)

        else:
            report["not ready"].append(groupname)
            if options["run"] == "run":
                r += "\n---> ERROR: something missing, skipping this group!"
            else:
                r += "\n---> ERROR: something missing, this group would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of group %s with error:\n" % (
            groupname
        )
        r += str(errormessage)
        report["failed"].append(groupname)
    except:
        r += "\n --- Failed during processing of group %s with error:\n %s\n" % (
            groupname,
            traceback.format_exc(),
        )
        report["failed"].append(groupname)

    return {"r": r, "report": report}


def hcp_long_msmall(sinfo, subjectids, options, overwrite=False, thread=0):
    """
    ``hcp_long_msmall [... processing options]``

    ``hcp_lmsm [... processing options]``

    Runs the HCP Longitudinal MSMAll Pipeline
    (MSMAllPipeline.sh with the longitudinal setup).

    Warning:
        The code expects the input images to be named and present in the QuNex
        folder structure. The function will look into folder::

            <session id>/hcp/<session id>

        for files::

            MNINonLinear/Results/<boldname>/
            <boldname>_<hcp_cifti_tail>_hp<hcp_highpass>_clean.dtseries.nii

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_icafix_bolds (str, default ''):
            List of bolds on which ICAFix was applied, with the same format
            as for ICAFix. Typically, this should be identical to the list
            used in the ICAFix run. If multi-run ICAFix was run with two or
            more groups then HCP MSMAll will be executed over the first
            specified group (and the scans listed for hcp_msmall_bolds must
            be limited to scans in the first concatenation group as well).
            If not provided MSMAll will assume multi-run ICAFix was executed
            with all bolds bundled together in a single concatenation called
            fMRI_CONCAT_ALL (i.e., same default behavior as in ICAFix).

        --hcp_msmall_bolds (str, default detailed below):
            A comma separated list that defines the bolds that will be used
            in the computation of the MSMAll registration. Typically, this
            should be limited to resting-state scans. Specified bolds have
            to be a subset of bolds used from the hcp_icafix_bolds parameter
            [if not specified all bolds specified in hcp_icafix_bolds will
            be used, which is probably NOT what you want to do if
            hcp_icafix_bolds includes non-resting-state scans].

        --hcp_icafix_highpass (int, default detailed below):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix. Should be identical to the value
            used for ICAFix.

        --hcp_msmall_outfmriname (str, default 'rfMRI_REST'):
            The name which will be given to the concatenation of scans specified
            by the hcp_msmall_bold parameter.

        --hcp_msmall_templates (str, default <HCPPIPEDIR>/global/templates/MSMAll):
            Path to directory containing MSMAll template files.

        --hcp_msmall_outregname (str, default 'MSMAll_InitialReg'):
            Output registration name.

        --hcp_hiresmesh (int, default 164):
            High resolution mesh node count.

        --hcp_lowresmesh (int, default 32):
            Low resolution mesh node count.

        --hcp_regname (str, default 'MSMSulc'):
            Input registration name.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_msmall_procstring (str, default <hcp_cifti_tail>_hp<hcp_highpass>_clean):
            Identification for FIX cleaned dtseries to use.

        --hcp_msmall_myelin_target (str, default 'Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii'):
            Myelin map target, will use
            Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii
            by default.

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folder inside the same sessions's root hcp folder.

    Notes:
        Runs the longitudinal MSMAll step of the HCP Pipeline. This function
        executes two steps, it first runs longitudinal MSMAll and if it
        completes successfully it then executes the DeDriftAndResample step.

        The MSMAll step computes the MSMAll registration based on
        resting-state connectivity, resting-state topography, and myelin-map
        architecture. The DeDriftAndResample step applies the MSMAll
        registration to a specified set of maps and fMRI runs.

        MSMAll is intended for use with fMRI runs cleaned with hcp_icafix.
        Except for specialized/expert-user situations, the hcp_icafix_bolds
        parameter should be identical to what was used in hcp_icafix. If
        hcp_icafix_bolds is not provided MSMAll/DeDriftAndResample will
        assume multi-run ICAFix was executed with all bolds bundled
        together in a single concatenation called fMRI_CONCAT_ALL. (This is
        the default behavior if hcp_icafix_bolds parameter is not provided
        in the case of hcp_icafix).

        A key parameter in hcp_msmall is `hcp_msmall_bolds`, which controls
        the fMRI runs that enter into the computation of the MSMAll
        registration. Since MSMAll registration was designed to be computed
        from resting-state scans, this should be a list of the resting-state
        fMRI scans that you want to contribute to the computation of the
        MSMAll registration.

        However, it is perfectly fine to apply the MSMAll registration to
        task fMRI scans in the DeDriftAndResample step. The fMRI scans to
        which the MSMAll registration is applied are controlled by the
        `hcp_icafix_bolds` parameter, since typically one wants to apply the
        MSMAll registration to the same full set of fMRI scans that were
        cleaned using hcp_icafix.

        hcp_msmall parameter mapping:

            ============================= ============================
            QuNex parameter               HCPpipelines parameter
            ============================= ============================
            ``hcp_msmall_outfmriname``    ``output-fmri-name``
            ``hcp_icafix_highpass``       ``high-pass``
            ``hcp_msmall_templates``      ``msm-all-templates``
            ``hcp_msmall_outregname``     ``output-registration-name``
            ``hcp_hiresmesh``             ``high-res-mesh``
            ``hcp_lowresmesh``            ``low-res-mesh``
            ``hcp_regname``               ``input-registration-name``
            ``hcp_matlab_mode``           ``matlab-run-mode``
            ``hcp_msmall_procstring``     ``fmri-proc-string``
            ``hcp_longitudinal_template`` ``longitudinal-template``
            ``hcp_msmall_myelin_target``  ``myelin-target-file``
            ============================= ============================

    Examples:
            qunex hcp_long_msmall \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_icafix_bolds="GROUP_1:REST_1,REST_2,TASK_1|GROUP_2:REST_3,TASK_2" \\
                --hcp_msmall_bolds="REST_1,REST_2" \\
                --hcp_longitudinal_template="<template_id>"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSubjects: %s \n[started on %s]" % (
        subjectids,
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP Longitudnal MSMAll Pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = {"done": [], "failed": [], "ready": [], "not ready": []}
    failed = 0

    try:
        # checks
        pc.doOptionsCheck(options, sinfo[0], "hcp_long_msmall")
        doHCPOptionsCheck(options, "hcp_long_msmall")
        hcp = getHCPPaths(sinfo[0], options)

        # get subjects and their sesssions from the batch file
        run, subjects_list = _get_subjects_from_batch(sinfo, hcp, run)

        # launch
        parsubjects = options["parsubjects"]

        # create a multiprocessing Pool
        processPoolExecutor = ProcessPoolExecutor(parsubjects)
        # process
        f = partial(
            _execute_hcp_long_msmall,
            sinfo,
            options,
            run,
            hcp,
        )
        results = processPoolExecutor.map(f, subjects_list)

        # merge r and report
        for result in results:
            r += result["r"]
            run_report = result["report"]
            if run_report["done"]:
                report["done"].append(run_report["done"])
            if run_report["failed"]:
                report["failed"].append(run_report["failed"])
                failed = 1
            if run_report["ready"]:
                report["ready"].append(run_report["ready"])
            if run_report["not ready"]:
                report["not ready"].append(run_report["not ready"])

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = "Error"
        failed = 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = "Error"
        failed = 1

    r += (
        "\n\nHCP Longitudinal MSMAll Preprocessing %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, (subjectids, report, failed))


def _execute_hcp_long_msmall(sinfos, options, run, hcp, subject):
    # prepare return variables
    r = ""
    report = {"done": [], "failed": [], "ready": [], "not ready": []}

    # get subject data
    subject_id = subject["id"]
    sessions_list = subject["sessions"]
    sessions_long = []
    for session in sessions_list:
        sessions_long.append(f"{session}{options['hcp_suffix']}")

    # --- Get sorted bold numbers and bold data
    sinfo = None
    for si in sinfos:
        if si["subject"] == subject_id:
            sinfo = si
            break
    if not sinfo:
        raise ge.CommandFailed(
            "hcp_long_msmall", f"Subject {subject} not found in the batch file!"
        )
    bolds, bskip, report["boldskipped"], r = pc.use_or_skip_bold(sinfo, options, r)
    _build_skipped_report(report, bskip, options)

    # --- Parse msmall_bolds
    msmall_groups, _, pars_ok, r = parse_msmall_bolds(options, bolds, r)

    if not pars_ok:
        raise ge.CommandFailed("hcp_msmall", "... invalid input parameters!")

    if run:
        for group in msmall_groups:
            try:
                # get group data
                groupname = group["name"]
                bolds = group["bolds"]

                # outfmriname
                outfmriname = options["hcp_msmall_outfmriname"]

                r += "\n\n------------------------------------------------------------"
                r += "\n---> %s MSMAll %s" % (
                    pc.action("Processing", options["run"]),
                    outfmriname,
                )

                # --- check for bold images and prepare targets parameter
                boldtargets = ""

                # highpass
                highpass = (
                    0
                    if options["hcp_icafix_highpass"] is None
                    else options["hcp_icafix_highpass"]
                )

                # fmriprocstring
                fmriprocstring = "%s_hp%s_clean" % (
                    "_Atlas",
                    str(highpass),
                )
                if options["hcp_msmall_procstring"] is not None:
                    fmriprocstring = options["hcp_msmall_procstring"]

                # check if files for all bolds exist
                for boldinfo in bolds:
                    # set ok to true for now
                    boldok = True

                    _, boldtarget, _ = pc.get_bold_names(boldinfo, options)

                    # input file check
                    boldimg = os.path.join(
                        hcp["hcp_nonlin"],
                        "Results",
                        boldtarget,
                        "%s%s.dtseries.nii" % (boldtarget, fmriprocstring),
                    )
                    r, boldok = pc.checkForFile2(
                        r,
                        boldimg,
                        "\n     ... bold image %s present" % boldtarget,
                        "\n     ... ERROR: bold image [%s] missing!" % boldimg,
                        status=boldok,
                    )

                    if not boldok:
                        break
                    else:
                        # add @ separator
                        if boldtargets != "":
                            boldtargets = boldtargets + "@"

                        # add latest image
                        boldtargets = boldtargets + boldtarget

                if boldok:
                    # check if group file exists
                    groupica = "%s_hp%s_clean.nii.gz" % (groupname, highpass)
                    groupimg = os.path.join(
                        hcp["hcp_nonlin"], "Results", groupname, groupica
                    )
                    r, boldok = pc.checkForFile2(
                        r,
                        groupimg,
                        "\n     ... ICA %s present" % groupname,
                        "\n     ... ERROR: ICA [%s] missing!" % groupimg,
                        status=boldok,
                    )

                if options["hcp_msmall_templates"] is None:
                    msmalltemplates = os.path.join(
                        hcp["hcp_base"], "global", "templates", "MSMAll"
                    )
                else:
                    msmalltemplates = options["hcp_msmall_templates"]

                if options["hcp_msmall_myelin_target"] is None:
                    myelintarget = os.path.join(
                        msmalltemplates,
                        "Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii",
                    )
                else:
                    myelintarget = options["hcp_msmall_myelin_target"]

                # matlab run mode, compiled=0, interpreted=1, octave=2
                matlabrunmode = None
                if options["hcp_matlab_mode"] is None:
                    if "FSL_FIX_MATLAB_MODE" not in os.environ:
                        r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
                        boldok = False
                    else:
                        matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
                else:
                    if options["hcp_matlab_mode"] == "compiled":
                        matlabrunmode = "0"
                    elif options["hcp_matlab_mode"] == "interpreted":
                        matlabrunmode = "1"
                    elif options["hcp_matlab_mode"] == "octave":
                        matlabrunmode = "2"
                    else:
                        r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                        boldok = False

                # fix names to use
                fixnamestouse = "@".join(group["msmall_bolds"])

                studyfolder = gc.deduce_folders(options)["basefolder"]
                if not studyfolder:
                    r += "\nERROR: cannot deduce the QuNex study folder from provided parameters! Please provide the sessionsfolder or the studyfolder parameter."
                    boldok = False
                # replace path
                path = os.path.join(studyfolder, "subjects", sinfo["subject"])

                comm = (
                    '%(script)s \
                    --path="%(path)s" \
                    --session="%(subject)s" \
                    --fmri-names-list="" \
                    --multirun-fix-names="%(fixnames)s" \
                    --multirun-fix-concat-name="%(concatname)s" \
                    --multirun-fix-names-to-use="%(fixnamestouse)s" \
                    --output-fmri-name="%(outfmriname)s" \
                    --high-pass="%(highpass)s" \
                    --fmri-proc-string="%(fmriprocstring)s" \
                    --msm-all-templates="%(msmalltemplates)s" \
                    --output-registration-name="%(outregname)s" \
                    --high-res-mesh="%(highresmesh)s" \
                    --low-res-mesh="%(lowresmesh)s" \
                    --input-registration-name="%(inregname)s" \
                    --myelin-target-file="%(myelintarget)s" \
                    --matlab-run-mode="%(matlabrunmode)s" \
                    --subject-long="%(subject)s" \
                    --sessions-long="%(sessionslong)s" \
                    --template-long="%(templatelong)s" \
                    --is-longitudinal="TRUE"'
                    % {
                        "script": os.path.join(
                            hcp["hcp_base"], "MSMAll", "MSMAllPipeline.sh"
                        ),
                        "path": path,
                        "subject": subject_id,
                        "fixnames": boldtargets,
                        "concatname": groupname,
                        "fixnamestouse": fixnamestouse,
                        "outfmriname": outfmriname,
                        "highpass": highpass,
                        "fmriprocstring": fmriprocstring,
                        "msmalltemplates": msmalltemplates,
                        "outregname": options["hcp_msmall_outregname"],
                        "highresmesh": options["hcp_hiresmesh"],
                        "lowresmesh": options["hcp_lowresmesh"],
                        "inregname": options["hcp_regname"],
                        "myelintarget": myelintarget,
                        "matlabrunmode": matlabrunmode,
                        "sessionslong": "@".join(sessions_long),
                        "templatelong": options["hcp_longitudinal_template"],
                    }
                )

                # -- Report command
                if boldok:
                    r += "\n\n------------------------------------------------------------\n"
                    r += "Running HCP Pipelines command via QuNex:\n\n"
                    r += comm.replace("--", "\n    --").replace("             ", "")
                    r += "\n------------------------------------------------------------\n"

                # -- Run
                if run and boldok:
                    if options["run"] == "run":
                        r, _, _, failed = pc.runExternalForFile(
                            None,
                            comm,
                            "Running HCP MSMAll",
                            overwrite=True,
                            thread=subject_id,
                            remove=options["log"] == "remove",
                            task=options["command_ran"],
                            logfolder=options["comlogs"],
                            logtags=[options["logtag"], groupname],
                            fullTest=None,
                            shell=True,
                            r=r,
                        )
                        failed = False

                        if failed:
                            report["failed"].append(f"msmall_{subject_id}_{groupname}")
                        else:
                            # run dedrift and resample across long timepoints
                            sinfo_long = sinfo.copy()
                            with ProcessPoolExecutor(
                                options["parsessions"]
                            ) as executor:
                                futures = {}
                                for sl in sessions_long:
                                    sinfo_long_i = sinfo_long.copy()
                                    # fix path
                                    sinfo_long_i["hcp"] = path
                                    # fix id
                                    sinfo_long_i["id"] = (
                                        f"{sl}.long.{options['hcp_longitudinal_template']}"
                                    )
                                    # add step info
                                    sinfo_long_i["long"] = 1
                                    future = executor.submit(
                                        executeHCPMultiDeDriftAndResample,
                                        sinfo_long_i,
                                        options,
                                        hcp,
                                        run,
                                        group,
                                    )
                                    futures[future] = sl  # map future to sl
                                for future in concurrent.futures.as_completed(futures):
                                    sl = futures[
                                        future
                                    ]  # get the correct sl for this future
                                    result = future.result()
                                    r += result["r"]
                                    report_dedrift = result["report"]
                                    if report_dedrift["failed"]:
                                        report["failed"].append(
                                            f"dedrift_{sl}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"
                                        )
                                    if report_dedrift["ready"]:
                                        report["ready"].append(
                                            f"dedrift_{sl}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"
                                        )
                                    if report_dedrift["not ready"]:
                                        report["not ready"].append(
                                            f"dedrift_{sl}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"
                                        )

                            # run dedrift and resample on the template
                            sinfo_template = sinfo.copy()
                            # fix path
                            sinfo_template["hcp"] = path
                            # fix id
                            sinfo_template["id"] = (
                                f"{subject_id}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"
                            )
                            # add step info
                            sinfo_template["long"] = 2
                            result = executeHCPMultiDeDriftAndResample(
                                sinfo_template, options, hcp, run, group
                            )
                            r += result["r"]
                            report_dedrift = result["report"]
                            if report_dedrift["failed"]:
                                report["failed"].append(
                                    f"dedrift_long_{subject_id}_{groupname}"
                                )
                            if report_dedrift["ready"]:
                                report["ready"].append(
                                    f"dedrift_long_{subject_id}_{groupname}"
                                )
                            if report_dedrift["not ready"]:
                                report["not ready"].append(
                                    f"dedrift_long_{subject_id}_{groupname}"
                                )

                            if len(report["failed"]) == 0:
                                report["done"].append(
                                    f"msmall_{subject_id}_{groupname}"
                                )

                    # -- just checking
                    else:
                        passed, _, r, failed = pc.checkRun(
                            None,
                            None,
                            "HCP MSMAll " + f"{subject_id}_{groupname}",
                            r,
                            overwrite=True,
                        )
                        if passed is None:
                            r += "\n---> HCP MSMAll can be run"
                            report["ready"].append(f"{subject_id}_{groupname}")
                        else:
                            report["skipped"].append(f"{subject_id}_{groupname}")

                else:
                    report["not ready"].append(f"{subject_id}_{groupname}")
                    if options["run"] == "run":
                        r += "\n---> ERROR: something missing, skipping this group!"
                    else:
                        r += "\n---> ERROR: something missing, this group would be skipped!"

            except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
                r = "\n\n\n --- Failed during processing of group %s with error:\n" % (
                    f"{subject_id}_{groupname}"
                )
                r += str(errormessage)
                report["failed"].append(f"{subject_id}_{groupname}")
            except:
                r += (
                    "\n --- Failed during processing of group %s with error:\n %s\n"
                    % (
                        f"{subject_id}_{groupname}",
                        traceback.format_exc(),
                    )
                )
                report["failed"].append(f"{subject_id}_{groupname}")
    else:
        r += "\n---> Subject cannot be processed."
        report["not ready"] = subject_id

    return {"r": r, "report": report}


def hcp_dedrift_and_resample(sinfo, options, overwrite=True, thread=0):
    """
    ``hcp_dedrift_and_resample [... processing options]``

    Runs the DeDriftAndResample step of the HCP Pipeline.

    Warning:
        The code expects the input images to be named and present in the QuNex
        folder structure. The function will look into folder::

            <session id>/hcp/<session id>

        for files::

            MNINonLinear/Results/<boldname>/
            <boldname>_<hcp_cifti_tail>_hp<hcp_highpass>_clean.dtseries.nii

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging  data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_icafix_bolds (str, default ''):
            List of bolds on which ICAFix was applied, with the same format
            as for ICAFix. Typically, this should be identical to the list
            used in the ICAFix run. If multi-run ICAFix was run with two or
            more groups then HCP MSMAll will be executed over the first
            specified group (and the scans listed for hcp_msmall_bolds must
            be limited to scans in the first concatenation group as well).
            If not provided MSMAll will assume multi-run ICAFix was executed
            with all bolds bundled together in a single concatenation called
            fMRI_CONCAT_ALL (i.e., same default behavior as in ICAFix).

        --hcp_resample_concatregname (str, default 'MSMAll'):
            Output name of the dedrifted registration.

        --hcp_resample_regname (str, default '<hcp_msmall_outregname>_2_d40_WRN'):
            Registration sphere name.

        --hcp_icafix_highpass (int, default detailed below):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix. Should be identical to the value
            used for ICAFix.

        --hcp_hiresmesh (int, default 164):
            High resolution mesh node count.

        --hcp_lowresmeshes (str, default 32):
            Low resolution meshes node count. To provide more values separate
            them with commas.

        --hcp_resample_reg_files (str, default detailed below):
            Comma separated paths to the spheres output from the
            MSMRemoveGroupDrift pipeline [<HCPPIPEDIR>/global/templates/MSMAll/<file1>,
            <HCPPIPEDIR>/global/templates/MSMAll/<file2>].
            Where <file1> is equal to:
            DeDriftingGroup.L.sphere.DeDriftMSMAll.
            164k_fs_LR.surf.gii and <file2> is equal
            to DeDriftingGroup.R.sphere.DeDriftMSMAll.
            164k_fs_LR.surf.gii

        --hcp_resample_maps (str, default 'sulc,curvature,corrThickness,thickness'):
            Comma separated paths to maps that will have the MSMAll registration
            applied that are not myelin maps.

        --hcp_resample_myelinmaps (str, default 'MyelinMap,SmoothedMyelinMap'):
            Comma separated paths to myelin maps.

        --hcp_bold_smoothFWHM (int, default 2):
            Smoothing FWHM that matches what was used in the fMRISurface
            pipeline.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_icafix_domotionreg (bool, default detailed below):
            Whether to regress motion parameters as part of the cleaning. The
            default value after a single-run HCP ICAFix is [TRUE], while the
            default after a multi-run HCP ICAFix is [FALSE].

        --hcp_resample_dontfixnames (str, default 'NONE'):
            A list of comma separated bolds that will not have HCP ICAFix
            reapplied to them. Only applicable if single-run ICAFix was used.
            Generally not recommended.

        --hcp_resample_inregname (str, default 'NONE'):
            A string to enable multiple fMRI resolutions (e.g._1.6mm).

        --hcp_resample_use_ind_mean (str, default 'YES'):
            Whether to use the mean of the individual myelin map as the group
            reference map's mean.

        --hcp_resample_extractnames (str, default 'NONE'):
            List of bolds and concat names provided in the same format as the
            hcp_icafix_bolds parameter. Defines which bolds to extract. Exists
            to enable extraction of a subset of the runs in a multi-run HCP
            ICAFix group into a new concatenated series.

        --hcp_resample_extractextraregnames (str, default 'NONE'):
            Extract multi-run HCP ICAFix runs for additional surface
            registrations, often MSMSulc

        --hcp_resample_extractvolume (str, default 'NONE'):
            Whether to also extract the specified multi-run HCP ICAFix from the
            volume data, requires hcp_resample_extractnames to work.

        --hcp_msmall_templates (str, default <HCPPIPEDIR>/global/templates/MSMAll):
            Path to directory containing MSMAll template files.

        --hcp_msmall_myelin_target (str, default 'Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii'):
            Myelin map target, will use
            Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii
            by default.

    Output files:
        The results of this step will be populated in the MNINonLinear
        folder inside the same session's root hcp folder.

    Notes:
        Mapping of QuNex parameters onto HCP Pipelines parameters:
            Below is a detailed specification about how QuNex parameters are
            mapped onto the HCP Pipelines parameters.

        hcp_dedrift_and_resample parameter mapping:

            ===================================== =======================================
            QuNex parameter                       HCPpipelines parameter
            ===================================== =======================================
            ``hcp_resample_concatregname``        ``concat-reg-name``
            ``hcp_resample_regname``              ``registration-name``
            ``hcp_icafix_highpass``               ``high-pass``
            ``hcp_hiresmesh``                     ``high-res-mesh``
            ``hcp_lowresmeshes``                  ``low-res-meshes``
            ``hcp_resample_reg_files``            ``dedrift-reg-files``
            ``hcp_resample_maps``                 ``maps``
            ``hcp_resample_myelinmaps``           ``myelin-maps``
            ``hcp_bold_smoothFWHM``               ``smoothing-fwhm``
            ``hcp_matlab_mode``                   ``matlab-run-mode``
            ``hcp_icafix_domotionreg``            ``motion-regression``
            ``hcp_msmall_myelin_target``          ``myelin-target-file``
            ``hcp_resample_dontfixnames``         ``dont-fix-names``
            ``hcp_resample_inregname``            ``input-reg-name``
            ``hcp_resample_extractnames``         ``multirun-fix-extract-names``
            ``hcp_resample_extractnames``         ``multirun-fix-extract-concat-names``
            ``hcp_resample_extractextraregnames`` ``multirun-fix-extract-extra-regnames``
            ``hcp_resample_extractvolume``        ``multirun-fix-extract-volume``
            ``hcp_resample_use_ind_mean``         ``use-ind-mean``
            ===================================== =======================================

    Examples:
        HCP DeDriftAndResample after application of single-run ICAFix::

            qunex hcp_dedrift_and_resample \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_icafix_bolds="REST_1,REST_2,TASK_1,TASK_2" \\
                --hcp_matlab_mode="interpreted"

        HCP DeDriftAndResample after application of multi-run ICAFix::

            qunex hcp_dedrift_and_resample \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_icafix_bolds="GROUP_1:REST_1,REST_2,TASK_1|GROUP_2:REST_3,TASK_2" \\
                --hcp_matlab_mode="interpreted"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP DeDriftAndResample pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, "hcp_dedrift_and_resample")
        doHCPOptionsCheck(options, "hcp_dedrift_and_resample")
        hcp = getHCPPaths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report["boldskipped"], r = pc.use_or_skip_bold(sinfo, options, r)
        _build_skipped_report(report, bskip, options)

        # --- Parse msmall_bolds
        single_run, _, dedrift_groups, pars_ok, r = parse_icafix_bolds(
            options, bolds, r, True
        )

        if not pars_ok:
            raise ge.CommandFailed(
                "hcp_dedrift_and_resample", "... invalid input parameters!"
            )

        # --- Execute
        parelements = max(1, min(options["parelements"], len(dedrift_groups)))
        ppe = ProcessPoolExecutor(parelements)
        # single-run
        if single_run:
            f = partial(executeHCPSingleDeDriftAndResample, sinfo, options, hcp, run)
        # multi-run
        else:
            f = partial(executeHCPMultiDeDriftAndResample, sinfo, options, hcp, run)
        results = ppe.map(f, dedrift_groups)

        # merge r and report
        for result in results:
            r += result["r"]
            temp_report = result["report"]
            report["done"] += temp_report["done"]
            report["failed"] += temp_report["failed"]
            report["incomplete"] += temp_report["incomplete"]
            report["ready"] += temp_report["ready"]
            report["not ready"] += temp_report["not ready"]
            report["skipped"] += temp_report["skipped"]

        # report
        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP DeDriftAndResample: " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except ge.CommandFailed as e:
        r += "\n\nERROR in completing %s:\n     %s\n" % (
            e.function,
            "\n     ".join(e.report),
        )
        report = (sinfo["id"], "HCP DeDriftAndResample failed")
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = (sinfo["id"], "HCP DeDriftAndResample failed")
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = (sinfo["id"], "HCP DeDriftAndResample failed")

    r += (
        "\n\nHCP DeDriftAndResample %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, report)


def executeHCPSingleDeDriftAndResample(sinfo, options, hcp, run, group):
    # prepare return variables
    r = ""
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # get group data
        bolds = group["bolds"]

        r += "\n\n------------------------------------------------------------"
        r += "\n---> %s DeDriftAndResample" % (pc.action("Processing", options["run"]))
        boldsok = True

        # --- check for bold images and prepare targets parameter
        boldtargets = ""

        # highpass
        highpass = (
            2000
            if options["hcp_icafix_highpass"] is not None
            else options["hcp_icafix_highpass"]
        )

        # check if files for all bolds exist
        for boldinfo in bolds:
            # set ok to true for now
            boldok = True

            _, boldtarget, _ = pc.get_bold_names(boldinfo, options)

            # input file check
            boldimg = os.path.join(
                hcp["hcp_nonlin"],
                "Results",
                boldtarget,
                "%s_hp%s_clean.nii.gz" % (boldtarget, highpass),
            )
            r, boldok = pc.checkForFile2(
                r,
                boldimg,
                "\n     ... bold image %s present" % boldtarget,
                "\n     ... ERROR: bold image [%s] missing!" % boldimg,
                status=boldok,
            )

            if not boldok:
                boldsok = False

            # add @ separator
            if boldtargets != "":
                boldtargets = boldtargets + "@"

            # add latest image
            boldtargets = boldtargets + boldtarget

        # regname
        regname = "%s_2_d40_WRN" % options["hcp_msmall_outregname"]
        if options["hcp_resample_regname"] is not None:
            regname = options["hcp_resample_regname"]

        # dedrift reg files
        regfiles = (
            hcp["hcp_base"]
            + "/global/templates/MSMAll/DeDriftingGroup.L.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii"
            + "@"
            + hcp["hcp_base"]
            + "/global/templates/MSMAll/DeDriftingGroup.R.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii"
        )
        if options["hcp_resample_reg_files"] is not None:
            regfiles = options["hcp_resample_reg_files"].replace(",", "@")

        if options["hcp_msmall_templates"] is None:
            msmalltemplates = os.path.join(
                hcp["hcp_base"], "global", "templates", "MSMAll"
            )
        else:
            msmalltemplates = options["hcp_msmall_templates"]

        if options["hcp_msmall_myelin_target"] is None:
            myelintarget = os.path.join(
                msmalltemplates,
                "Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii",
            )
        else:
            myelintarget = options["hcp_msmall_myelin_target"]

        # matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
            else:
                matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
        else:
            if options["hcp_matlab_mode"] == "compiled":
                matlabrunmode = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                matlabrunmode = "1"
            elif options["hcp_matlab_mode"] == "octave":
                matlabrunmode = "2"
            else:
                r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                boldsok = False

        comm = (
            '%(script)s \
            --path="%(path)s" \
            --subject="%(subject)s" \
            --fix-names="%(fixnames)s" \
            --high-res-mesh="%(highresmesh)s" \
            --low-res-meshes="%(lowresmeshes)s" \
            --registration-name="%(regname)s" \
            --maps="%(maps)s" \
            --smoothing-fwhm="%(smoothingfwhm)s" \
            --high-pass="%(highpass)s" \
            --motion-regression="%(motionregression)s" \
            --dedrift-reg-files="%(regfiles)s" \
            --concat-reg-name="%(concatregname)s" \
            --myelin-maps="%(myelinmaps)s" \
            --myelin-target-file="%(myelintarget)s" \
            --matlab-run-mode="%(matlabrunmode)s"'
            % {
                "script": os.path.join(
                    hcp["hcp_base"],
                    "DeDriftAndResample",
                    "DeDriftAndResamplePipeline.sh",
                ),
                "path": sinfo["hcp"],
                "subject": sinfo["id"] + options["hcp_suffix"],
                "fixnames": boldtargets,
                "highresmesh": options["hcp_hiresmesh"],
                "lowresmeshes": options["hcp_lowresmeshes"].replace(",", "@"),
                "regname": regname,
                "maps": options["hcp_resample_maps"].replace(",", "@"),
                "smoothingfwhm": options["hcp_bold_smoothFWHM"],
                "highpass": highpass,
                "motionregression": (
                    "TRUE"
                    if options["hcp_icafix_domotionreg"] is None
                    else options["hcp_icafix_domotionreg"]
                ),
                "regfiles": regfiles,
                "concatregname": options["hcp_resample_concatregname"],
                "myelinmaps": options["hcp_resample_myelinmaps"].replace(",", "@"),
                "myelintarget": myelintarget,
                "matlabrunmode": matlabrunmode,
            }
        )

        # optional parameters
        if options["hcp_resample_dontfixnames"] is not None:
            comm += "                --dont-fix-names=" + options[
                "hcp_resample_dontfixnames"
            ].replace(",", "@")

        if options["hcp_msmall_myelin_target"] is not None:
            comm += (
                "                --myelin-target-file="
                + options["hcp_msmall_myelin_target"]
            )

        if options["hcp_resample_inregname"] is not None:
            comm += (
                "                --input-reg-name=" + options["hcp_resample_inregname"]
            )

        if options["hcp_resample_use_ind_mean"] is not None:
            comm += (
                "                --use-ind-mean=" + options["hcp_resample_use_ind_mean"]
            )

        # -- Report command
        if boldsok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Run
        if run and boldsok:
            if options["run"] == "run":
                r, endlog, _, failed = pc.runExternalForFile(
                    None,
                    comm,
                    "Running HCP DeDriftAndResample",
                    overwrite=True,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task="hcp_dedrift_and_resample",
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], regname],
                    fullTest=None,
                    shell=True,
                    r=r,
                )

                if failed:
                    report["failed"].append(regname)
                else:
                    report["done"].append(regname)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    None, None, "HCP DeDriftAndResample", r, overwrite=True
                )
                if passed is None:
                    r += "\n---> HCP DeDriftAndResample can be run"
                    report["ready"].append(regname)
                else:
                    report["skipped"].append(regname)

        else:
            report["not ready"].append(regname)
            if options["run"] == "run":
                r += "\n---> ERROR: something missing, skipping this group!"
            else:
                r += "\n---> ERROR: something missing, this group would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of group %s with error:\n" % (
            "DeDriftAndResample"
        )
        r += str(errormessage)
        report["failed"].append(regname)
    except:
        r += "\n --- Failed during processing of group %s with error:\n %s\n" % (
            "DeDriftAndResample",
            traceback.format_exc(),
        )
        report["failed"].append(regname)

    return {"r": r, "report": report}


def executeHCPMultiDeDriftAndResample(sinfo, options, hcp, run, group):
    # prepare return variables
    r = ""
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        r += "\n\n------------------------------------------------------------"
        r += "\n---> %s DeDriftAndResample" % (pc.action("Processing", options["run"]))

        # --- check for bold images and prepare targets parameter
        groupList = []
        grouptargets = ""
        boldList = []
        boldtargets = ""

        # highpass
        highpass = (
            0
            if options["hcp_icafix_highpass"] is None
            else options["hcp_icafix_highpass"]
        )

        # runok
        runok = True

        # check if files for all bolds exist
        # get group data
        groupname = group["name"]
        bolds = group["bolds"]

        # for storing bolds
        groupbolds = ""

        for boldinfo in bolds:
            _, boldtarget, _ = pc.get_bold_names(boldinfo, options)

            # input file check
            boldimg = os.path.join(
                hcp["hcp_nonlin"],
                "Results",
                boldtarget,
                "%s_hp%s_clean.nii.gz" % (boldtarget, highpass),
            )
            r, boldok = pc.checkForFile2(
                r,
                boldimg,
                "\n     ... bold image %s present" % boldtarget,
                "\n     ... ERROR: bold image [%s] missing!" % boldimg,
            )

            if not boldok:
                runok = False

            # add @ separator
            if groupbolds != "":
                groupbolds = groupbolds + "@"

            # add latest image
            boldList.append(boldtarget)
            groupbolds = groupbolds + boldtarget

        # check if group file exists
        groupica = "%s_hp%s_clean.nii.gz" % (groupname, highpass)
        groupimg = os.path.join(hcp["hcp_nonlin"], "Results", groupname, groupica)
        r, groupok = pc.checkForFile2(
            r,
            groupimg,
            "\n     ... ICA %s present" % groupname,
            "\n     ... ERROR: ICA [%s] missing!" % groupimg,
        )

        if not groupok:
            runok = False

        # add @ or % separator
        if grouptargets != "":
            grouptargets = grouptargets + "@"
            boldtargets = boldtargets + "%"

        # add latest group
        groupList.append(groupname)
        grouptargets = grouptargets + groupname
        boldtargets = boldtargets + groupbolds

        # regname
        regname = "%s_2_d40_WRN" % options["hcp_msmall_outregname"]
        if options["hcp_resample_regname"] is not None:
            regname = options["hcp_resample_regname"]

        # dedrift reg files
        regfiles = (
            hcp["hcp_base"]
            + "/global/templates/MSMAll/DeDriftingGroup.L.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii"
            + "@"
            + hcp["hcp_base"]
            + "/global/templates/MSMAll/DeDriftingGroup.R.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii"
        )
        if options["hcp_resample_reg_files"] is not None:
            regfiles = options["hcp_resample_reg_files"].replace(",", "@")

        if options["hcp_msmall_templates"] is None:
            msmalltemplates = os.path.join(
                hcp["hcp_base"], "global", "templates", "MSMAll"
            )
        else:
            msmalltemplates = options["hcp_msmall_templates"]

        if options["hcp_msmall_myelin_target"] is None:
            myelintarget = os.path.join(
                msmalltemplates,
                "Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii",
            )
        else:
            myelintarget = options["hcp_msmall_myelin_target"]

        # matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
                runok = False
            else:
                matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
        else:
            if options["hcp_matlab_mode"] == "compiled":
                matlabrunmode = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                matlabrunmode = "1"
            elif options["hcp_matlab_mode"] == "octave":
                matlabrunmode = "2"
            else:
                r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                runok = False

        comm = (
            '%(script)s \
            --path="%(path)s" \
            --subject="%(subject)s" \
            --high-res-mesh="%(highresmesh)s" \
            --low-res-meshes="%(lowresmeshes)s" \
            --registration-name="%(regname)s" \
            --maps="%(maps)s" \
            --smoothing-fwhm="%(smoothingfwhm)s" \
            --high-pass="%(highpass)s" \
            --motion-regression="%(motionregression)s" \
            --dedrift-reg-files="%(regfiles)s" \
            --concat-reg-name="%(concatregname)s" \
            --myelin-maps="%(myelinmaps)s" \
            --myelin-target-file="%(myelintarget)s" \
            --matlab-run-mode="%(matlabrunmode)s"'
            % {
                "script": os.path.join(
                    hcp["hcp_base"],
                    "DeDriftAndResample",
                    "DeDriftAndResamplePipeline.sh",
                ),
                "path": sinfo["hcp"],
                "subject": sinfo["id"] + options["hcp_suffix"],
                "highresmesh": options["hcp_hiresmesh"],
                "lowresmeshes": options["hcp_lowresmeshes"].replace(",", "@"),
                "regname": regname,
                "maps": options["hcp_resample_maps"].replace(",", "@"),
                "smoothingfwhm": options["hcp_bold_smoothFWHM"],
                "highpass": highpass,
                "motionregression": (
                    "FALSE"
                    if options["hcp_icafix_domotionreg"] is None
                    else options["hcp_icafix_domotionreg"]
                ),
                "regfiles": regfiles,
                "concatregname": options["hcp_resample_concatregname"],
                "myelinmaps": options["hcp_resample_myelinmaps"].replace(",", "@"),
                "myelintarget": myelintarget,
                "matlabrunmode": matlabrunmode,
            }
        )

        # do not set --multirun-fix-names and --multirun-fix-concat-names for the second step of longitudinal processing
        if "long" not in sinfo or sinfo["long"] == 1:
            comm += "                --multirun-fix-names=" + boldtargets
            comm += "                --multirun-fix-concat-names=" + grouptargets

        # optional parameters
        if options["hcp_resample_dontfixnames"] is not None:
            comm += "                --dont-fix-names=" + options[
                "hcp_resample_dontfixnames"
            ].replace(",", "@")

        if options["hcp_msmall_myelin_target"] is not None:
            comm += (
                "                --myelin-target-file="
                + options["hcp_msmall_myelin_target"]
            )

        if options["hcp_resample_inregname"] is not None:
            comm += (
                "                --input-reg-name=" + options["hcp_resample_inregname"]
            )

        if options["hcp_resample_use_ind_mean"] is not None:
            comm += (
                "                --use-ind-mean=" + options["hcp_resample_use_ind_mean"]
            )

        # -- hcp_resample_extractnames
        if options["hcp_resample_extractnames"] is not None:
            # variables for storing
            boldnames = ""
            extractnames = ""
            extractconcatnames = ""

            # split to groups
            ens = options["hcp_resample_extractnames"].split("|")
            # iterate
            for en in ens:
                en_split = en.split(":")
                concatname = en_split[0]

                # if none all is good
                if concatname.upper() == "NONE":
                    concatname = concatname.upper()
                    boldnames = "NONE"
                # wrong input
                elif len(en_split) == 0:
                    runok = False
                    r += "\n---> ERROR: invalid input, check the hcp_resample_extractnames parameter!"
                # else check if concatname is in groups
                else:
                    # extract fix names ok?
                    fixnames = en_split[1].split(",")
                    for fn in fixnames:
                        # extract fixname name ok?
                        if fn not in boldList:
                            runok = False
                            r += (
                                "\n---> ERROR: extract fix name [%s], not found in provided fix names!"
                                % fn
                            )

                    if len(en_split) > 0:
                        boldnames = en_split[1].replace(",", "@")

                # add @ or % separator
                if extractnames != "":
                    extractconcatnames = extractconcatnames + "@"
                    extractnames = extractnames + "%"

                # add latest group
                extractconcatnames = extractconcatnames + concatname
                extractnames = extractnames + boldnames

            # append to command
            comm += '             --multirun-fix-extract-names="%s"' % extractnames
            comm += (
                '             --multirun-fix-extract-concat-names="%s"'
                % extractconcatnames
            )

        # -- hcp_resample_extractextraregnames
        if options["hcp_resample_extractextraregnames"] is not None:
            comm += (
                '             --multirun-fix-extract-extra-regnames="%s"'
                % options["hcp_resample_extractextraregnames"]
            )

        # -- hcp_resample_extractvolume
        if options["hcp_resample_extractvolume"] is not None:
            extractvolume = options["hcp_resample_extractvolume"].upper()

            # check value
            if extractvolume != "TRUE" and extractvolume != "FALSE":
                runok = False
                r += (
                    "\n---> ERROR: invalid extractvolume parameter [%s], expecting TRUE or FALSE!"
                    % extractvolume
                )

            # append to command
            comm += '             --multirun-fix-extract-volume="%s"' % extractvolume

        # -- Report command
        if runok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Run
        if run and runok:
            if options["run"] == "run":
                r, _, _, failed = pc.runExternalForFile(
                    None,
                    comm,
                    "Running HCP DeDriftAndResample",
                    overwrite=True,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task="hcp_dedrift_and_resample",
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], groupname],
                    fullTest=None,
                    shell=True,
                    r=r,
                )

                if failed:
                    report["failed"].append(grouptargets)
                else:
                    report["done"].append(grouptargets)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    None, None, "HCP DeDriftAndResample", r, overwrite=True
                )
                if passed is None:
                    r += "\n---> HCP DeDriftAndResample can be run"
                    report["ready"].append(grouptargets)
                else:
                    report["skipped"].append(grouptargets)

        else:
            report["not ready"].append(grouptargets)
            if options["run"] == "run":
                r += "\n---> ERROR: something missing, skipping this group!"
            else:
                r += "\n---> ERROR: something missing, this group would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of group %s with error:\n" % (
            "DeDriftAndResample"
        )
        r += str(errormessage)
        report["failed"].append(grouptargets)
    except:
        r += "\n --- Failed during processing of group %s with error:\n %s\n" % (
            "DeDriftAndResample",
            traceback.format_exc(),
        )
        report["failed"].append(grouptargets)

    return {"r": r, "report": report}


def hcp_asl(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_asl [... processing options]``

    ``hcpa [... processing options]``

    Runs the HCP ASL Pipeline (https://github.com/physimals/hcp-asl).

    Warning:
        The code expects the first three HCP preprocessing steps
        (hcp_pre_freesurfer, hcp_freesurfer and hcp_post_freesurfer) to have
        been run and finished successfully.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_gdcoeffs (str, optional):
            Path to a file containing gradient distortion coefficients,
            alternatively a string describing multiple options (see
            below) can be provided.

        --hcp_asl_mtname (str, optional):
            Filename for empirically estimated MT-correction scaling factors.

        --hcp_asl_territories_atlas (str, optional):
            Atlas of vascular territories from Mutsaerts.

        --hcp_asl_territories_labels (str, optional):
            Labels corresponding to territories_atlas.

        --hcp_asl_cores (int, optional)
            Number of cores to use when applying motion correction and
            other potentially multi-core operations.

        --hcp_asl_use_t1 (flag, optional):
            If specified, the T1 estimates from the satrecov model fit
            will be used in perfusion estimation in oxford_asl. The
            flag is not set by default.

        --hcp_asl_interpolation (int, optional):
            Interpolation order for registrations corresponding to
            scipy's map_coordinates function.

        --hcp_asl_nobandingcorr (flag, optional):
            If this option is provided, MT and ST banding corrections
            won't be applied. The flag is not set by default.

        --hcp_asl_stages (str, optional)
            A comma separated list of stages (zero-indexed) to run.
            All prior stages are assumed to have run successfully.

        --hcp_asl_ntis (int, optional)
            Number of TIs.

        --hcp_asl_tis (str, optional)
            Comma separated list of TIs in seconds (e.g., 1.7,2.2,2.7,3.2,3.7).

        --hcp_asl_rpts (str, optional)
            Comma separated repeats for each TI (e.g., 6,6,6,10,15).

        --hcp_asl_bolus (float, optional)
            Labeling/bolus duration in seconds.

        --hcp_asl_slicedt (float, optional)
            Slice time in seconds.

        --hcp_asl_sliceband (int, optional)
            Slices per band (if omitted, derived from sidecar MB factor).

        --hcp_asl_te (float, optional)
            Echo time in milliseconds.

        --hcp_asl_tail_discard_vols (int, optional)
            Volumes immediately before calibrations to discard.

        --hcp_asl_ibf (str, optional)
            Input block format.

        --hcp_regname (str, default 'MSMSulc'):
            Input registration name.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --longitudinal:
            Set this flag if you are running the longitudinal variant of this
            command.

    Output files:
        The results of this step will be present in the ASL folder in the
        sessions's root hcp folder.

    Notes:
        Gradient coefficient file specification:
            `--hcp_gdcoeffs` parameter can be set to either "NONE", a path to a
            specific file to use, or a string that describes, which file to use
            in which case. Each option of the string has to be divided by a
            pipe "|" character and it has to specify, which information to look
            up, a possible value, and a file to use in that case, separated by
            a colon ":" character. The information too look up needs to be
            present in the description of that session. Standard options are
            e.g.::

                institution: Yale
                device: Siemens|Prisma|123456

            Where device is formatted as <manufacturer>|<model>|<serial number>.

            If specifying a string it also has to include a `default`
            option, which will be used in the information was not found. An
            example could be::

                "default:/data/gc1.conf|model:Prisma:/data/gc/Prisma.conf|model:Trio:/data/gc/Trio.conf"

            With the information present above, the file
            `/data/gc/Prisma.conf` would be used.

        Mapping of QuNex parameters onto HCP ASL pipeline parameters:
            Below is a detailed specification about how QuNex parameters are
            mapped onto the HCP ASL parameters.

            ============================== ======================
            QuNex parameter                HCP ASL parameter
            ============================== ======================
            ``hcp_gdcoeffs``               ``grads``
            ``hcp_regname``                ``regname``
            ``hcp_asl_mtname``             ``mtname``
            ``hcp_asl_territories_atlas``  ``territories_atlas``
            ``hcp_asl_territories_labels`` ``territories_labels``
            ``hcp_asl_use_t1``             ``use_t1``
            ``hcp_asl_nobandingcorr``      ``nobandingcorr``
            ``hcp_asl_interpolation``      ``interpolation``
            ``hcp_asl_cores``              ``cores```
            ``hcp_asl_stages``             ``stages``
            ``hcp_asl_ntis``               ``ntis``
            ``hcp_asl_tis``                ``tis``
            ``hcp_asl_rpts``               ``rpts``
            ``hcp_asl_bolus``              ``bolus``
            ``hcp_asl_slicedt``            ``slicedt``
            ``hcp_asl_sliceband``          ``sliceband``
            ``hcp_asl_te``                 ``te``
            ``hcp_asl_tail_discard_vols``  ``tail_discard_vols``
            ``hcp_asl_ibf``                ``ibf``
            ``longitudinal``               ``is-longitudinal``
            ``hcp_longitudinal_template``  ``longitudinal-template``
            ============================== ======================

    Examples:
        Example run::

            qunex hcp_asl \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"

        Run with scheduler, while bumping up the number of used cores::

            qunex hcp_asl \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_asl_cores="8" \\
                --scheduler="SLURM,time=24:00:00,mem-per-cpu=16000"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP ASL Pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = "Error"

    try:
        pc.doOptionsCheck(options, sinfo, "hcp_asl")
        doHCPOptionsCheck(options, "hcp_asl")
        hcp = getHCPPaths(sinfo, options)

        if "hcp" not in sinfo:
            r += (
                "\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"])
            )
            run = False

        # extract ASL and SE info
        asl_info = []
        asl_se_info = []
        for k, v in sinfo.items():
            if k.isdigit():
                if v["name"] == "PCASLhr":
                    asl_se_info.append(v)
                elif v["name"] == "mbPCASLhr" or v["name"] == ["mbPCASLhr"]:
                    asl_info = v
                elif v["name"] == "ASL":
                    if "phenc" in v and "SE-FM" in v["phenc"]:
                        asl_se_info.append(v)
                    else:
                        asl_info = v

        # ASL file
        if len(asl_info) == 0:
            r += "\n---> ERROR: No ASL images found in the batch file!"
            run = False

        asl_file = ""
        if "filename" in asl_info:
            asl_file = os.path.join(
                hcp["ASL_source"], sinfo["id"] + "_" + asl_info["filename"] + ".nii.gz"
            )
        else:
            asl_files = glob.glob(os.path.join(hcp["ASL_source"], "*.nii.gz"))
            if len(asl_files) == 0:
                r += f"\n---> ERROR: No .nii.gz files found in {hcp['ASL_source']}!"
                run = False
            else:
                asl_file = asl_files[0]

        # file exists?
        if not os.path.exists(asl_file):
            r += "\n---> ERROR: ASL acquistion data not found [%s]" % asl_file
            run = False

        # AP and PA fieldmaps for use in distortion correction
        # asl_se_info is populated through the PCASLhr tag
        fmap_ap_file = None
        fmap_pa_file = None
        if len(asl_se_info) > 0:
            for se in asl_se_info:
                if "phenc" in se:
                    if se["phenc"] in ["AP", "SE-FM-AP"]:
                        if "filename" in se:
                            fmap_ap_file = os.path.join(
                                hcp["ASL_source"],
                                sinfo["id"] + "_" + se["filename"] + ".nii.gz",
                            )
                        else:
                            fmap_ap_file = glob.glob(
                                os.path.join(
                                    hcp["ASL_source"], "*SpinEchoFieldMap_AP*.nii.gz"
                                )
                            )
                            if len(fmap_ap_file) == 0:
                                r += (
                                    "\n---> ERROR: SE AP file not found in [%s]"
                                    % hcp["ASL_source"]
                                )
                                run = False
                            else:
                                fmap_ap_file = fmap_ap_file[0]
                    elif se["phenc"] in ["PA", "SE-FM-PA"]:
                        if "filename" in se:
                            fmap_pa_file = os.path.join(
                                hcp["ASL_source"],
                                sinfo["id"] + "_" + se["filename"] + ".nii.gz",
                            )
                        else:
                            fmap_pa_file = glob.glob(
                                os.path.join(
                                    hcp["ASL_source"], "*SpinEchoFieldMap_PA*.nii.gz"
                                )
                            )
                            if len(fmap_pa_file) == 0:
                                r += (
                                    "\n---> ERROR: SE PA file not found in [%s]"
                                    % hcp["ASL_source"]
                                )
                                run = False
                            else:
                                fmap_pa_file = fmap_pa_file[0]

        # else we need to get the files from se
        elif "se" in asl_info:
            senum = asl_info["se"]
            sefolder = os.path.join(
                hcp["source"], f"SpinEchoFieldMap{senum}{options['fctail']}"
            )
            fmap_ap_file = glob.glob(os.path.join(sefolder, "*AP*.nii.gz"))
            fmap_pa_file = glob.glob(os.path.join(sefolder, "*PA*.nii.gz"))
            if len(fmap_ap_file) == 0 or len(fmap_pa_file) == 0:
                r += "\n---> ERROR: SE pair not found in the batch file"
                run = False
            else:
                fmap_ap_file = fmap_ap_file[0]
                fmap_pa_file = fmap_pa_file[0]
        else:
            r += "\n---> ERROR: SE pair not found in the batch file"
            run = False

        # check
        if not fmap_ap_file or not fmap_pa_file:
            r += "\n---> ERROR: one or more fieldmaps not found, check your input data"
            run = False
        else:
            if not os.path.exists(fmap_ap_file):
                r += "\n---> ERROR: AP fieldmap not found [%s]" % fmap_ap_file
                run = False
            if not os.path.exists(fmap_ap_file):
                r += "\n---> ERROR: PA fieldmap not found [%s]" % fmap_pa_file
                run = False

        # get library path
        asl_library = os.path.join(os.environ["QUNEXLIBRARY"], "etc/asl")

        # build the command
        if run:
            comm = (
                "%(script)s \
                --subdir %(subdir)s \
                --subid %(subid)s \
                --mbpcasl %(mbpcasl)s \
                --fmap_ap %(fmap_ap)s \
                --fmap_pa %(fmap_pa)s \
                --regname %(regname)s"
                % {
                    "script": "process_hcp_asl",
                    "subdir": os.path.join(sinfo["hcp"], sinfo["id"]),
                    "subid": sinfo["id"] + options["hcp_suffix"],
                    "mbpcasl": asl_file,
                    "fmap_ap": fmap_ap_file,
                    "fmap_pa": fmap_pa_file,
                    "regname": options["hcp_regname"],
                }
            )

            # -- Optional parameters
            # grads
            gdcfile, r, run = check_gdc_coeff_file(
                options["hcp_gdcoeffs"], hcp=hcp, sinfo=sinfo, r=r, run=run
            )
            if gdcfile != "NONE":
                comm += f"                --grads {gdcfile}"

            # struct
            # get struct files
            # ACPC-aligned, DC-restored structural image
            t1w_file = os.path.join(
                sinfo["hcp"], sinfo["id"], "T1w", "T1w_acpc_dc_restore.nii.gz"
            )
            if os.path.exists(t1w_file):
                comm += f"                --struct {t1w_file}"

            # sbrain
            t1w_brain_file = os.path.join(
                sinfo["hcp"], sinfo["id"], "T1w", "T1w_acpc_dc_restore_brain.nii.gz"
            )
            if os.path.exists(t1w_brain_file):
                comm += f"                --sbrain {t1w_brain_file}"

            # wmparc
            wmparc_file = os.path.join(
                sinfo["hcp"], sinfo["id"], "T1w", "wmparc.nii.gz"
            )
            if os.path.exists(wmparc_file):
                comm += f"                --wmparc {wmparc_file}"

            # ribbon
            ribbon_file = os.path.join(
                sinfo["hcp"], sinfo["id"], "T1w", "ribbon.nii.gz"
            )
            if os.path.exists(ribbon_file):
                comm += f"                --ribbon {ribbon_file}"

            # use_t1
            if options["hcp_asl_use_t1"]:
                comm += "                --use_t1"

            # mtname
            if options["hcp_asl_mtname"] is None:
                mtname = os.path.join(asl_library, "mt_scaling_factors.txt")
                if os.path.exists(mtname):
                    comm += f"                --mtname {mtname}"
            else:
                comm += f"                --mtname {options['hcp_asl_mtname']}"

            # stages
            if options["hcp_asl_stages"] is not None:
                stages = options["hcp_asl_stages"].replace(",", " ")
                comm += f"                --stages {stages}"

            # cores
            if options["hcp_asl_cores"] is not None:
                comm += f"                --cores {options['hcp_asl_cores']}"

            # interpolation
            if options["hcp_asl_interpolation"] is not None:
                comm += f"                --interpolation {options['hcp_asl_interpolation']}"

            # nobandingcorr
            if options["hcp_asl_nobandingcorr"]:
                comm += "                --nobandingcorr"

            # territories_atlas
            if options["hcp_asl_territories_atlas"] is None:
                territories_atlas = os.path.join(
                    asl_library, "vascular_territories_eroded5_atlas.nii.gz"
                )
                if os.path.exists(territories_atlas):
                    comm += f"                --territories_atlas {territories_atlas}"
            else:
                comm += f"                --territories_atlas {options['hcp_asl_territories_atlas']}"

            # territories_labels
            if options["hcp_asl_territories_labels"] is None:
                territories_labels = os.path.join(
                    asl_library, "vascular_territories_atlas.txt"
                )
                if os.path.exists(territories_labels):
                    comm += f"                --territories_labels {territories_labels}"
            else:
                comm += f"                --territories_labels {options['hcp_asl_territories_labels']}"

            # ntis
            if options["hcp_asl_ntis"] is not None:
                comm += f"                --ntis {options['hcp_asl_ntis']}"

            # tis
            if options["hcp_asl_tis"] is not None:
                hcp_asl_tis = options["hcp_asl_tis"].replace(",", " ")
                comm += f"                --tis {hcp_asl_tis}"

            # rpts
            if options["hcp_asl_rpts"] is not None:
                hcp_asl_rpts = options["hcp_asl_rpts"].replace(",", " ")
                comm += f"                --rpts {hcp_asl_rpts}"

            # bolus
            if options["hcp_asl_bolus"] is not None:
                comm += f"                --bolus {options['hcp_asl_bolus']}"

            # slicedt
            if options["hcp_asl_slicedt"] is not None:
                comm += f"                --slicedt {options['hcp_asl_slicedt']}"

            # sliceband
            if options["hcp_asl_sliceband"] is not None:
                comm += f"                --sliceband {options['hcp_asl_sliceband']}"

            # te
            if options["hcp_asl_te"] is not None:
                comm += f"                --te {options['hcp_asl_te']}"

            # tail_discard_vols
            if options["hcp_asl_tail_discard_vols"] is not None:
                comm += f"                --tail_discard_vols {options['hcp_asl_tail_discard_vols']}"

            # ibf
            if options["hcp_asl_ibf"] is not None:
                comm += f"                --ibf {options['hcp_asl_ibf']}"

            # clean/overwrite
            if overwrite:
                comm += "                --clean"

            # -- Longitudinal parameters
            if options["longitudinal"]:
                studyfolder = gc.deduce_folders(options)["basefolder"]
                if not studyfolder:
                    r += "\nERROR: cannot deduce the QuNex study folder from provided parameters! Please provide the sessionsfolder or the studyfolder parameter."
                    run = False
                # replace path
                longitudinal_study_dir = os.path.join(
                    studyfolder, "subjects", sinfo["subject"]
                )

                comm += f'                --longitudinal_template="{options["hcp_longitudinal_template"]}"'
                comm += f'                --longitudinal_study_dir="{longitudinal_study_dir}"'
                comm += "                --is_longitudinal"

            # -- Report command
            if run:
                r += (
                    "\n\n------------------------------------------------------------\n"
                )
                r += "Running HCP Pipelines command via QuNex:\n\n"
                r += comm.replace("                --", "\n    --")
                r += "\n------------------------------------------------------------\n"

        # -- Run
        if run:
            if options["run"] == "run":
                if not options["longitudinal"]:
                    logtags = options["logtag"]
                else:
                    logtags = ["long", options["hcp_longitudinal_template"]]

                r, _, report, failed = pc.runExternalForFile(
                    None,
                    comm,
                    "Running HCP ASL",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=logtags,
                    fullTest=None,
                    shell=True,
                    r=r,
                )

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(
                    None, None, "HCP ASL", r, overwrite=overwrite
                )
                if passed is None:
                    r += "\n---> HCP ASL can be run"
                    report = "HCP ASL can be run"
                    failed = 0

        else:
            r += "\n---> Session cannot be processed."
            report = "HCP ASL cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        failed = 1
    except Exception as e:
        r += f"\nERROR: {e}"
        r += f"\nERROR: Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n"
        failed = 1

    r += (
        "\n\nHCP ASL Preprocessing %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, (sinfo["id"], report, failed))


def hcp_transmit_bias_individual(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_transmit_bias_individual [... processing options]``

    Runs the HCP Transmit Bias Individual Only Pipeline.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_gmwm_template (str, default ''):
            Location of the GMWMtemplate, the file containing GM+WM volume ROI.

        --hcp_regname (str, default 'MSMSulc'):
            Input registration name.

        --hcp_transmit_mode (str, default ''):
            What type of transmit bias correction to apply, options and required
            inputs are:

            a) AFI: actual flip angle sequence with two different echo times,
            requires the following parameters: afi-image, afi-tr-one,afi-tr-two,
            afi-angle, group-corrected-myelin.

            b) B1Tx: b1 transmit sequence magnitude/phase pair, requires the
            following parameters: b1tx-magnitude, b1tx-phase, group-corrected-myelin.

            c) PseudoTransmit: use spin echo fieldmaps, SBRef, and a
            template transmit-corrected myelin map to derive empirical
            correction, requires the following parameters: pt-fmri-names,
            myelin-template, group-uncorrected-myelin, reference-value.

        --hcp_group_corrected_myelin (str, default ''):
            The group-corrected myelin file from AFI or B1Tx.

        --hcp_afi_image (str, default ''):
            Two-frame AFI image.

        --hcp_afi_tr_one (str, default ''):
            TR of first AFI frame.

        --hcp_afi_tr_two (str, default ''):
            TR of second AFI frame.

        --hcp_afi_angle (str, default ''):
            Target flip angle of AFI sequence.

        --hcp_b1tx_magnitude (str, default ''):
            B1Tx magnitude image (for alignment).

        --hcp_b1tx_phase (str, default ''):
            B1Tx phase image.

        --hcp_b1tx_phase_divisor (str, default '800'):
            What to divide the phase map by to obtain proportion of intended

        --hcp_pt_fmri_names (str, default <list of all BOLDs>):
            A comma separated list of fMRI runs to use SE/SBRef files from. Set
            to a list of all BOLDs by default.

        --hcp_pt_bbr_threshold (str, default '0.5'):
            Mincost threshold for reinitializing fMRI bbregister with flirt
            (may need to be increased for aging-related reduction of gray/white
            contrast).

        --hcp_myelin_template (str, default ''):
            Expected transmit-corrected group-average myelin pattern (for testing
            correction parameters).

        --hcp_group_uncorrected_myelin (str, default ''):
            The group-average uncorrected myelin file (to set the appropriate
            scaling of the myelin template).

        --hcp_pt_reference_value_file (str, default ''):
            Text file containing the value in the pseudotransmit map where the
            flip angle best matches the intended angle, from the Phase2 group
            script.

        --hcp_unproc_t1w_list (str, default ''):
            A comma separated list of unprocessed T1w images, for correcting
            non-PSN data. You can set this to "auto" and QuNex will try to fill
            it automatically.

        --hcp_unproc_t2w_list (str, default ''):
            A comma separated list of unprocessed T2w images, for correcting
            non-PSN data. You can set this to "auto" and QuNex will try to fill
            it automatically.

        --hcp_receive_bias_body_coil (str, default ''):
            Image acquired with body coil receive, to be used with
            --hcp_receive_head_body_coil.

        --hcp_receive_bias_head_coil (str, default ''):
            Matched image acquired with head coil receive.

        --hcp_raw_psn_t1w (str, default ''):
            The bias-corrected version of the T1w image acquired with pre-scan
            normalize, which was used to generate the original myelin maps.
            You can set this to "auto" and QuNex will try to fill it
            automatically.

        --hcp_raw_nopsn_t1w (str, default ''):
            The uncorrected version of the --raw-psn-t1w image. You can set this
            to "auto" and QuNex will try to fill it automatically.

        --hcp_transmit_res (str, default ''):
            Resolution to use for transmit field, default equal to
            hcp_grayordinatesres.

        --hcp_myelin_mapping_fwhm (str, default '5'):
            The fwhm value to use in -myelin-style [5]

        --hcp_old_myelin_mapping (flag, not set by default):
            If myelin mapping was done using version 1.2.3 or earlier of
            wb_command, set this flag.

        --hcp_gdcoeffs (str, default ''):
            Path to a file containing gradient distortion coefficients.

        --hcp_regname (str, default 'MSMSulc'):
            The name of the registration used.

        --hcp_lowresmesh (int, default 32):
            Mesh resolution.

        --hcp_grayordinatesres (int, default 2):
            The size of voxels for the subcortical and cerebellar data in
            grayordinate space in mm.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

    Notes:
        hcp_transmit_bias_individual parameter mapping:

            ================================== ============================
            QuNex parameter                    HCPpipelines parameter
            ================================== ============================
            ``hcp_gmwm_template``              ``gmwm-template``
            ``hcp_regname``                    ``reg-name``
            ``hcp_transmit_mode``              ``mode``
            ``hcp_group_corrected_myelin``     ``group-corrected-myelin``
            ``hcp_afi_image``                  ``afi-image``
            ``hcp_afi_tr_one``                 ``afi-tr-one``
            ``hcp_afi_tr_two``                 ``afi-tr-two``
            ``hcp_afi_angle``                  ``afi-angle``
            ``hcp_b1tx_magnitude``              ``b1tx-magnitude``
            ``hcp_b1tx_phase``                 ``b1tx-phase``
            ``hcp_b1tx_phase_divisor``         ``b1tx-phase-divisor``
            ``hcp_pt_fmri_names``              ``pt-fmri-names``
            ``hcp_pt_bbr_threshold``           ``pt-bbr-threshold``
            ``hcp_myelin_template``            ``myelin-template``
            ``hcp_group_uncorrected_myelin``   ``group-uncorrected-myelin``
            ``hcp_pt_reference_value_file``    ``pt-reference-value-file``
            ``hcp_unproc_t1w_list``            ``unproc-t1w-list``
            ``hcp_unproc_t2w_list``            ``unproc-t2w-list``
            ``hcp_receive_bias_body_coil``     ``receive-bias-body-coil``
            ``hcp_receive_bias_head_coil``     ``receive-bias-head-coil``
            ``hcp_raw_psn_t1w``                ``raw-psn-t1w``
            ``hcp_raw_nopsn_t1w``              ``raw-nopsn-t1w``
            ``hcp_transmit_res``               ``transmit-res``
            ``hcp_myelin_mapping_fwhm``        ``myelin-mapping-fwhm``
            ``hcp_old_myelin_mapping``         ``old-myelin-mapping``
            ``hcp_gdcoeffs``                   ``scanner-grad-coeffs``
            ``hcp_regname``                    ``reg-name``
            ``hcp_lowresmesh``                 ``low-res-mesh``
            ``hcp_grayordinatesres``           ``grayordinates-res``
            ``hcp_matlab_mode``                ``matlab-run-mode``
            ================================== ============================

    Examples:
        Example run::

            qunex hcp_transmit_bias_individual \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"

    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP Transmit Bias Individual Only Pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = "Error"

    try:
        pc.doOptionsCheck(options, sinfo, "hcp_transmit_bias_individual")
        doHCPOptionsCheck(options, "hcp_transmit_bias_individual")
        hcp = getHCPPaths(sinfo, options)

        if "hcp" not in sinfo:
            r += (
                "\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"])
            )
            run = False

        if options["hcp_transmit_mode"] is None:
            r += "\n---> ERROR: the hcp_transmit_mode parameter is mandatory!"
            run = False

        # build the command
        if run:
            matlabrunmode = None
            if options["hcp_matlab_mode"]:
                if options["hcp_matlab_mode"] == "compiled":
                    matlabrunmode = "0"
                elif options["hcp_matlab_mode"] == "interpreted":
                    matlabrunmode = "1"
                elif options["hcp_matlab_mode"] == "octave":
                    matlabrunmode = "2"
                else:
                    r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                    run = False
            else:
                matlabrunmode = "0"

            comm = (
                '%(script)s \
                --study-folder="%(studyfolder)s" \
                --subject="%(subject)s" \
                --mode="%(mode)s" \
                --gmwm-template="%(gmwm_template)s" \
                --reg-name="%(reg_name)s" \
                --matlab-run-mode="%(matlab_run_mode)s"'
                % {
                    "script": os.path.join(
                        hcp["hcp_base"],
                        "TransmitBias",
                        "RunIndividualOnly.sh",
                    ),
                    "studyfolder": sinfo["hcp"],
                    "subject": sinfo["id"] + options["hcp_suffix"],
                    "mode": options["hcp_transmit_mode"],
                    "gmwm_template": options["hcp_gmwm_template"],
                    "reg_name": options["hcp_regname"],
                    "matlab_run_mode": matlabrunmode,
                }
            )

            # check and set parameters given the mode
            # AFI
            if options["hcp_transmit_mode"] == "AFI":
                if options["hcp_afi_image"]:
                    comm += f"                --afi-image={options['hcp_afi_image']}"
                else:
                    r += "\n---> Setting the hcp_afi_image automatically"
                    if "T1w-AFI" in hcp:
                        comm += f"                --afi-image={hcp['T1w-AFI']}"
                    else:
                        r += "\n---> ERROR: the hcp_afi_image parameter is not provided, and QuNex cannot find the T1w AFI image in the HCP unprocessed/T1w folder!"
                        run = False

                if not options["hcp_afi_tr_two"]:
                    r += "\n---> ERROR: the hcp_afi_tr_two parameter is not provided!"
                    run = False
                if not options["hcp_afi_angle"]:
                    r += "\n---> ERROR: the hcp_afi_angle parameter is not provided!"
                    run = False
                if not options["hcp_group_corrected_myelin"]:
                    r += "\n---> ERROR: the hcp_group_corrected_myelin parameter is not provided!"
                    run = False

                if options["hcp_afi_tr_one"]:
                    comm += f"                --afi-tr-one={options['hcp_afi_tr_one']}"
                else:
                    r += "\n---> ERROR: the hcp_afi_tr_one parameter is not provided!"
                    run = False

                if options["hcp_afi_tr_two"]:
                    comm += f"                --afi-tr-two={options['hcp_afi_tr_two']}"
                else:
                    r += "\n---> ERROR: the hcp_afi_tr_two parameter is not provided!"
                    run = False

                if options["hcp_afi_angle"]:
                    comm += f"                --afi-angle={options['hcp_afi_angle']}"
                else:
                    r += "\n---> ERROR: the hcp_afi_angle parameter is not provided!"
                    run = False

                if options["hcp_group_corrected_myelin"]:
                    comm += f"                --group-corrected-myelin={options['hcp_group_corrected_myelin']}"
                else:
                    r += "\n---> ERROR: the hcp_group_corrected_myelin parameter is not provided!"
                    run = False

            # B1Tx
            elif options["hcp_transmit_mode"] == "B1Tx":
                if options["hcp_b1tx_magnitude"]:
                    comm += f"                --b1tx-magnitude={options['hcp_b1tx_magnitude']}"
                else:
                    r += "\n---> Setting the hcp_b1tx_magnitude automatically"
                    if "TB1TFL-Magnitude" in hcp:
                        comm += f"                --b1tx-magnitude={hcp['TB1TFL-Magnitude']}"
                    else:
                        r += "\n---> ERROR: the hcp_b1tx_magnitude parameter is not provided, and QuNex cannot find the b1tx magnitude image in the HCP unprocessed/B1 folder!"
                        run = False

                if options["hcp_b1tx_phase"]:
                    comm += f"                --b1tx-phase={options['hcp_b1tx_phase']}"
                else:
                    r += "\n---> Setting the hcp_b1tx_phase automatically"
                    if "TB1TFL-Phase" in hcp:
                        comm += f"                --b1tx-phase={hcp['TB1TFL-Phase']}"
                    else:
                        r += "\n---> ERROR: the hcp_b1tx_phase parameter is not provided, and QuNex cannot find the b1tx phase image in the HCP unprocessed/B1 folder!"
                        run = False

                if options["hcp_group_corrected_myelin"]:
                    comm += f"                --group-corrected-myelin={options['hcp_group_corrected_myelin']}"
                else:
                    r += "\n---> ERROR: the hcp_group_corrected_myelin parameter is not provided!"
                    run = False

                # optional B1Tx parameters
                if options["hcp_b1tx_phase_divisor"]:
                    comm += f"                --b1tx-phase-divisor={options['hcp_b1tx_phase_divisor']}"

            # PseudoTransmit
            elif options["hcp_transmit_mode"] == "PseudoTransmit":
                if options["hcp_pt_fmri_names"]:
                    pt_fmri_names = options["hcp_pt_fmri_names"].replace(",", "@")

                else:
                    r += "\n---> Setting the hcp_pt_fmri_names automatically"
                    # --- Get sorted bold numbers and bold data
                    bolds, _, _, r = pc.use_or_skip_bold(sinfo, options, r)
                    pt_fmri_names = []
                    for boldinfo in bolds:
                        if (
                            "filename" in boldinfo
                            and options["hcp_filename"] == "userdefined"
                        ):
                            pt_fmri_names.append(boldinfo["filename"])
                        else:
                            pt_fmri_names.append(
                                f"{options['hcp_bold_prefix']}{boldinfo['bold_number']}"
                            )

                    if len(pt_fmri_names) == 0:
                        r += "\n---> ERROR: the hcp_pt_fmri_names parameter is not provided, and QuNex cannot find any BOLDs!"
                        run = False
                    else:
                        pt_fmri_names = "@".join(pt_fmri_names)

                comm += f"                --pt-fmri-names={pt_fmri_names}"

                if not options["hcp_myelin_template"]:
                    r += "\n---> ERROR: the hcp_myelin_template parameter is not provided!"
                    run = False
                if not options["hcp_group_uncorrected_myelin"]:
                    r += "\n---> ERROR: the hcp_group_uncorrected_myelin parameter is not provided!"
                    run = False
                if not options["hcp_pt_reference_value_file"]:
                    r += "\n---> ERROR: the hcp_pt_reference_value_file parameter is not provided!"
                    run = False
                else:
                    comm += f"                --pt-reference-value-file={options['hcp_pt_reference_value_file']}"

                # optional PseudoTransmit parameters
                if options["hcp_pt_bbr_threshold"]:
                    comm += f"                --pt-bbr-threshold={options['hcp_pt_bbr_threshold']}"

                if options["hcp_myelin_template"]:
                    comm += f"                --myelin-template={options['hcp_myelin_template']}"

                if options["hcp_group_uncorrected_myelin"]:
                    comm += f"                --group-uncorrected-myelin={options['hcp_group_uncorrected_myelin']}"

            else:
                r += "\n---> ERROR: Unknown mode for hcp_transmit_mode, use AFI, B1Tx or PseudoTransmit!"

            # optional general parameters
            if options["hcp_unproc_t1w_list"] is not None:
                if options["hcp_unproc_t1w_list"] == "auto":
                    r += "\n---> Setting the hcp_unproc_t1w_list automatically"
                    comm += f"                --unproc-t1w-list={hcp['T1w']}"
                else:
                    unproc_t1w_list = options["hcp_unproc_t1w_list"].replace(",", "@")
                    comm += f"                --unproc-t1w-list={unproc_t1w_list}"

            if options["hcp_unproc_t2w_list"] is not None:
                if options["hcp_unproc_t2w_list"] == "auto":
                    r += "\n---> Setting the hcp_unproc_t2w_list automatically"
                    comm += f"                --unproc-t2w-list={hcp['T2w']}"
                else:
                    unproc_t2w_list = options["hcp_unproc_t2w_list"].replace(",", "@")
                    comm += f"                --unproc-t2w-list={unproc_t2w_list}"

            if options["hcp_receive_bias_body_coil"]:
                comm += f"                --receive-bias-body-coil={options['hcp_receive_bias_body_coil']}"
            else:
                if "RB1COR-Body" in hcp:
                    r += "\n---> Setting the hcp_receive_bias_body_coil automatically"
                    comm += (
                        f"                --receive-bias-body-coil={hcp['RB1COR-Body']}"
                    )

            if options["hcp_receive_bias_head_coil"]:
                comm += f"                --receive-bias-head-coil={options['hcp_receive_bias_head_coil']}"
            else:
                if "RB1COR-Head" in hcp:
                    r += "\n---> Setting the hcp_receive_bias_head_coil automatically"
                    comm += (
                        f"                --receive-bias-head-coil={hcp['RB1COR-Head']}"
                    )

            if options["hcp_raw_psn_t1w"]:
                if options["hcp_raw_psn_t1w"] == "auto":
                    r += "\n---> Setting the hcp_raw_psn_t1w automatically"
                    comm += f"                --raw-psn-t1w={hcp['hcp_raw_psn_t1w']}"
                else:
                    comm += (
                        f"                --raw-psn-t1w={options['hcp_raw_psn_t1w']}"
                    )

            if options["hcp_raw_nopsn_t1w"]:
                if options["hcp_raw_nopsn_t1w"] == "auto":
                    r += "\n---> Setting the hcp_raw_nopsn_t1w automatically"
                    comm += (
                        f"                --raw-nopsn-t1w={hcp['hcp_raw_nopsn_t1w']}"
                    )
                else:
                    comm += f"                --raw-nopsn-t1w={options['hcp_raw_nopsn_t1w']}"

            if options["hcp_transmit_res"]:
                comm += f"                --transmit-res={options['hcp_transmit_res']}"

            if options["hcp_myelin_mapping_fwhm"]:
                comm += f"                --myelin-mapping-fwhm={options['hcp_myelin_mapping_fwhm']}"

            if options["hcp_old_myelin_mapping"]:
                comm += "                --old-myelin-mapping=TRUE"

            if options["hcp_gdcoeffs"]:
                # lookup gdcoeffs file
                gdcfile, r, run = check_gdc_coeff_file(
                    options["hcp_gdcoeffs"], hcp=hcp, sinfo=sinfo, r=r, run=run
                )
                if gdcfile != "NONE":
                    comm += f"                --scanner-grad-coeffs={gdcfile}"

            if options["hcp_lowresmesh"]:
                comm += f"                --low-res-mesh={options['hcp_lowresmesh']}"

            if options["hcp_grayordinatesres"]:
                comm += f"                --grayordinates-res={options['hcp_grayordinatesres']}"

            # -- Report command
            if run:
                r += (
                    "\n\n------------------------------------------------------------\n"
                )
                r += "Running HCP Pipelines command via QuNex:\n\n"
                r += comm.replace("                --", "\n    --")
                r += "\n------------------------------------------------------------\n"

        # -- Run
        if run:
            if options["run"] == "run":
                r, endlog, report, failed = pc.runExternalForFile(
                    None,
                    comm,
                    "Running HCP Transmit Bias Individual Only",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    fullTest=None,
                    shell=True,
                    r=r,
                )

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(
                    None,
                    None,
                    "HCP Transmit Bias Individual Only",
                    r,
                    overwrite=overwrite,
                )
                if passed is None:
                    r += "\n---> HCP Transmit Bias Individual Only can be run"
                    report = "HCP Transmit Bias Individual Only can be run"
                    failed = 0

        else:
            r += "\n---> Session cannot be processed."
            report = "HCP Transmit Bias Individual Only cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        failed = 1
    except Exception as e:
        r += f"\nERROR: {e}"
        r += f"\nERROR: Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n"
        failed = 1

    r += (
        "\n\nHCP Transmit Bias Individual Only Preprocessing %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, (sinfo["id"], report, failed))


def hcp_long_transmit_bias(sinfo, subjectids, options, overwrite=False, thread=0):
    """
    ``hcp_long_transmit_bias [... processing options]``

    Runs the HCP Longitudinal Transmit Bias Pipeline.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsubjects (int, default 1):
            How many subjects to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --hcp_gmwm_template (str, default ''):
            Location of the GMWMtemplate, the file containing GM+WM volume ROI.

        --hcp_regname (str, default 'MSMSulc'):
            Input registration name.

        --hcp_transmit_mode (str, default ''):
            What type of transmit bias correction to apply, options and required
            inputs are:

            a) AFI: actual flip angle sequence with two different echo times,
            requires the following parameters: afi-image, afi-tr-one,afi-tr-two,
            afi-angle, group-corrected-myelin.

            b) B1Tx: b1 transmit sequence magnitude/phase pair, requires the
            following parameters: b1tx-magnitude, b1tx-phase, group-corrected-myelin.

            c) PseudoTransmit: use spin echo fieldmaps, SBRef, and a
            template transmit-corrected myelin map to derive empirical
            correction, requires the following parameters: pt-fmri-names,
            myelin-template, group-uncorrected-myelin, reference-value.

        --hcp_group_corrected_myelin (str, default ''):
            The group-corrected myelin file from AFI or B1Tx.

        --hcp_afi_tr_one (str, default ''):
            TR of first AFI frame.

        --hcp_afi_tr_two (str, default ''):
            TR of second AFI frame.

        --hcp_afi_angle (str, default ''):
            Target flip angle of AFI sequence.

        --hcp_b1tx_magnitude (str, default ''):
            B1Tx magnitude image (for alignment).

        --hcp_b1tx_phase (str, default ''):
            B1Tx phase image.

        --hcp_b1tx_phase_divisor (str, default '800'):
            What to divide the phase map by to obtain proportion of intended

        --hcp_pt_fmri_names (str, default <list of all BOLDs>):
            A comma separated list of fMRI runs to use SE/SBRef files from. Set
            to a list of all BOLDs by default.

        --hcp_pt_bbr_threshold (str, default '0.5'):
            Mincost threshold for reinitializing fMRI bbregister with flirt
            (may need to be increased for aging-related reduction of gray/white
            contrast).

        --hcp_myelin_template (str, default ''):
            Expected transmit-corrected group-average myelin pattern (for testing
            correction parameters).

        --hcp_group_uncorrected_myelin (str, default ''):
            The group-average uncorrected myelin file (to set the appropriate
            scaling of the myelin template).

        --hcp_pt_reference_value_file (str, default ''):
            Text file containing the value in the pseudotransmit map where the
            flip angle best matches the intended angle, from the Phase2 group
            script.

        --hcp_transmit_res (str, default ''):
            Resolution to use for transmit field, default equal to
            hcp_grayordinatesres.

        --hcp_myelin_mapping_fwhm (str, default '5'):
            The fwhm value to use in -myelin-style [5]

        --hcp_old_myelin_mapping (flag, not set by default):
            If myelin mapping was done using version 1.2.3 or earlier of
            wb_command, set this flag.

        --hcp_regname (str, default 'MSMSulc'):
            The name of the registration used.

        --hcp_lowresmesh (int, default 32):
            Mesh resolution.

        --hcp_grayordinatesres (int, default 2):
            The size of voxels for the subcortical and cerebellar data in
            grayordinate space in mm.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

    Notes:
        hcp_transmit_bias_individual parameter mapping:

            ================================== ============================
            QuNex parameter                    HCPpipelines parameter
            ================================== ============================
            ``hcp_gmwm_template``              ``gmwm-template``
            ``hcp_regname``                    ``reg-name``
            ``hcp_transmit_mode``              ``mode``
            ``hcp_group_corrected_myelin``     ``group-corrected-myelin``
            ``hcp_afi_tr_one``                 ``afi-tr-one``
            ``hcp_afi_tr_two``                 ``afi-tr-two``
            ``hcp_afi_angle``                  ``afi-angle``
            ``hcp_b1tx_phase_divisor``         ``b1tx-phase-divisor``
            ``hcp_pt_fmri_names``              ``pt-fmri-names``
            ``hcp_pt_bbr_threshold``           ``pt-bbr-threshold``
            ``hcp_myelin_template``            ``myelin-template``
            ``hcp_group_uncorrected_myelin``   ``group-uncorrected-myelin``
            ``hcp_pt_reference_value_file``    ``pt-reference-value-file``
            ``hcp_transmit_res``               ``transmit-res``
            ``hcp_myelin_mapping_fwhm``        ``myelin-mapping-fwhm``
            ``hcp_old_myelin_mapping``         ``old-myelin-mapping``
            ``hcp_regname``                    ``reg-name``
            ``hcp_lowresmesh``                 ``low-res-mesh``
            ``hcp_grayordinatesres``           ``grayordinates-res``
            ``hcp_matlab_mode``                ``matlab-run-mode``
            ``hcp_longitudinal_template``      ``longitudinal-template``
            ================================== ============================

    Examples:
        Example run::

            qunex hcp_long_transmit_bias \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"

    """

    r = "\n------------------------------------------------------------"
    r += "\nSubjects: %s \n[started on %s]" % (
        subjectids,
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP Longitudnal FS Pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = {"done": [], "failed": [], "ready": [], "not ready": []}
    failed = 0

    try:
        # checks
        pc.doOptionsCheck(options, sinfo[0], "hcp_long_transmit_bias")
        doHCPOptionsCheck(options, "hcp_long_transmit_bias")
        hcp = getHCPPaths(sinfo[0], options)

        run = True
        report = {"done": [], "failed": [], "ready": [], "not ready": []}
        failed = 0

        # get subjects and their sessions from the batch file
        run, subjects_list = _get_subjects_from_batch(sinfo, hcp, run)

        # launch
        parsubjects = options["parsubjects"]

        # create a multiprocessing Pool
        processPoolExecutor = ProcessPoolExecutor(parsubjects)
        # process
        f = partial(
            _execute_hcp_long_transmit_bias,
            sinfo,
            options,
            overwrite,
            run,
            hcp["hcp_base"],
        )
        results = processPoolExecutor.map(f, subjects_list)

        # merge r and report
        for result in results:
            r += result["r"]
            run_report = result["report"]
            if run_report["done"]:
                report["done"].append(run_report["done"])
            if run_report["failed"]:
                report["failed"].append(run_report["failed"])
            if run_report["ready"]:
                report["ready"].append(run_report["ready"])
            if run_report["not ready"]:
                report["not ready"].append(run_report["not ready"])

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = "Error"
        failed = 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = "Error"
        failed = 1

    r += (
        "\n\nHCP Longitudinal Transmit Bias Preprocessing %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, (subjectids, report, failed))


def _execute_hcp_long_transmit_bias(sinfo, options, overwrite, run, hcp_base, subject):
    # prepare return variables
    r = ""
    report = {"done": [], "failed": [], "ready": [], "not ready": []}

    # get subject data
    subject_id = subject["id"]
    sessions_list = subject["sessions"]

    # logdir
    logdir = os.path.join(
        options["logfolder"],
        "comlogs",
        f"extra_logs_hcp_long_transmit_bias_{subject['id']}",
    )
    if os.path.exists(logdir):
        shutil.rmtree(logdir)
    os.makedirs(logdir)

    if options["hcp_transmit_mode"] is None:
        r += "\n---> ERROR: the hcp_transmit_mode parameter is mandatory!"
        run = False

    # build the command
    if run:
        matlabrunmode = None
        if options["hcp_matlab_mode"]:
            if options["hcp_matlab_mode"] == "compiled":
                matlabrunmode = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                matlabrunmode = "1"
            elif options["hcp_matlab_mode"] == "octave":
                matlabrunmode = "2"
            else:
                r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                run = False
        else:
            matlabrunmode = "0"

        comm = (
            '%(script)s \
            --study-folder="%(studyfolder)s" \
            --subject="%(subject)s" \
            --sessions="%(sessions)s" \
            --longitudinal-template="%(longitudinal_template)s" \
            --mode="%(mode)s" \
            --gmwm-template="%(gmwm_template)s" \
            --reg-name="%(reg_name)s" \
            --parallel-mode="%(parallel_mode)s" \
            --logdir="%(logdir)s" \
            --matlab-run-mode="%(matlab_run_mode)s"'
            % {
                "script": os.path.join(
                    hcp_base,
                    "TransmitBias",
                    "TransmitBiasLong.sh",
                ),
                "studyfolder": study_folder,
                "subject": subject_id,
                "sessions": "@".join(sessions_list),
                "longitudinal_template": options["hcp_longitudinal_template"],
                "mode": options["hcp_transmit_mode"],
                "gmwm_template": options["hcp_gmwm_template"],
                "reg_name": options["hcp_regname"],
                "parallel_mode": options["hcp_parallel_mode"],
                "logdir": logdir,
                "matlab_run_mode": matlabrunmode,
            }
        )

        # check and set parameters given the mode
        # AFI
        if options["hcp_transmit_mode"] == "AFI":
            if not options["hcp_afi_tr_two"]:
                r += "\n---> ERROR: the hcp_afi_tr_two parameter is not provided!"
                run = False
            if not options["hcp_afi_angle"]:
                r += "\n---> ERROR: the hcp_afi_angle parameter is not provided!"
                run = False
            if not options["hcp_group_corrected_myelin"]:
                r += "\n---> ERROR: the hcp_group_corrected_myelin parameter is not provided!"
                run = False

            if options["hcp_afi_tr_one"]:
                comm += f"                --afi-tr-one={options['hcp_afi_tr_one']}"
            else:
                r += "\n---> ERROR: the hcp_afi_tr_one parameter is not provided!"
                run = False

            if options["hcp_afi_tr_two"]:
                comm += f"                --afi-tr-two={options['hcp_afi_tr_two']}"
            else:
                r += "\n---> ERROR: the hcp_afi_tr_two parameter is not provided!"
                run = False

            if options["hcp_afi_angle"]:
                comm += f"                --afi-angle={options['hcp_afi_angle']}"
            else:
                r += "\n---> ERROR: the hcp_afi_angle parameter is not provided!"
                run = False

            if options["hcp_group_corrected_myelin"]:
                comm += f"                --group-corrected-myelin={options['hcp_group_corrected_myelin']}"
            else:
                r += "\n---> ERROR: the hcp_group_corrected_myelin parameter is not provided!"
                run = False

        # B1Tx
        elif options["hcp_transmit_mode"] == "B1Tx":
            if options["hcp_group_corrected_myelin"]:
                comm += f"                --group-corrected-myelin={options['hcp_group_corrected_myelin']}"
            else:
                r += "\n---> ERROR: the hcp_group_corrected_myelin parameter is not provided!"
                run = False

            # optional B1Tx parameters
            if options["hcp_b1tx_phase_divisor"]:
                comm += f"                --b1tx-phase-divisor={options['hcp_b1tx_phase_divisor']}"

        # PseudoTransmit
        elif options["hcp_transmit_mode"] == "PseudoTransmit":
            if options["hcp_pt_fmri_names"]:
                pt_fmri_names = options["hcp_pt_fmri_names"].replace(",", "@")

            else:
                r += "\n---> Setting the hcp_pt_fmri_names automatically"
                # --- Get sorted bold numbers and bold data
                bolds, _, _, r = pc.use_or_skip_bold(sinfo, options, r)
                pt_fmri_names = []
                for boldinfo in bolds:
                    if (
                        "filename" in boldinfo
                        and options["hcp_filename"] == "userdefined"
                    ):
                        pt_fmri_names.append(boldinfo["filename"])
                    else:
                        pt_fmri_names.append(
                            f"{options['hcp_bold_prefix']}{boldinfo['bold_number']}"
                        )

                if len(pt_fmri_names) == 0:
                    r += "\n---> ERROR: the hcp_pt_fmri_names parameter is not provided, and QuNex cannot find any BOLDs!"
                    run = False
                else:
                    pt_fmri_names = "@".join(pt_fmri_names)

            comm += f"                --pt-fmri-names={pt_fmri_names}"

            if not options["hcp_myelin_template"]:
                r += "\n---> ERROR: the hcp_myelin_template parameter is not provided!"
                run = False
            if not options["hcp_group_uncorrected_myelin"]:
                r += "\n---> ERROR: the hcp_group_uncorrected_myelin parameter is not provided!"
                run = False
            if not options["hcp_pt_reference_value_file"]:
                r += "\n---> ERROR: the hcp_pt_reference_value_file parameter is not provided!"
                run = False
            else:
                comm += f"                --pt-reference-value-file={options['hcp_pt_reference_value_file']}"

            # optional PseudoTransmit parameters
            if options["hcp_pt_bbr_threshold"]:
                comm += f"                --pt-bbr-threshold={options['hcp_pt_bbr_threshold']}"

            if options["hcp_myelin_template"]:
                comm += f"                --myelin-template={options['hcp_myelin_template']}"

            if options["hcp_group_uncorrected_myelin"]:
                comm += f"                --group-uncorrected-myelin={options['hcp_group_uncorrected_myelin']}"

        else:
            r += "\n---> ERROR: Unknown mode for hcp_transmit_mode, use AFI, B1Tx or PseudoTransmit!"

        # optional general parameters
        if options["hcp_transmit_res"]:
            comm += f"                --transmit-res={options['hcp_transmit_res']}"

        if options["hcp_myelin_mapping_fwhm"]:
            comm += f"                --myelin-mapping-fwhm={options['hcp_myelin_mapping_fwhm']}"

        if options["hcp_old_myelin_mapping"]:
            comm += "                --old-myelin-mapping=TRUE"

        if options["hcp_lowresmesh"]:
            comm += f"                --low-res-mesh={options['hcp_lowresmesh']}"

        if options["hcp_grayordinatesres"]:
            comm += (
                f"                --grayordinates-res={options['hcp_grayordinatesres']}"
            )

        # -- Report command
        if run:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("                --", "\n    --")
            r += "\n------------------------------------------------------------\n"

        # -- Test file
        if options["run"] == "run":
            r, endlog, _, failed = pc.runExternalForFile(
                None,
                comm,
                "Running HCP Longitudinal Transmit Bias",
                overwrite=overwrite,
                thread=subject_id,
                remove=options["log"] == "remove",
                task=options["command_ran"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
                fullTest=None,
                shell=True,
                r=r,
            )

            if failed == 0:
                report["done"] = subject_id
            else:
                report["failed"] = subject_id

            with open(endlog, "a", encoding="utf-8") as log_file:
                _append_sorted_logdir_to_log(log_file, logdir)

                # print succesful completion
                print("\n---> Successful completion of task", file=log_file)

            # remove the directory and its contents
            shutil.rmtree(logdir)

        # -- just checking
        else:
            passed, _, r, _ = pc.checkRun(
                None, None, "HCP Longitudinal Transmit Bias", r, overwrite=overwrite
            )
            if passed is None:
                r += "\n---> HCP Longitudinal Transmit Bias can be run"
                report["ready"] = subject_id
            else:
                r += "\n---> HCP Longitudinal Transmit Bias cannot be run"
                report["not ready"] = subject_id

    else:
        r += "\n---> Subject cannot be processed."
        report["not ready"] = subject_id

    return {"r": r, "report": report}


def hcp_temporal_ica(sessions, sessionids, options, overwrite=True, thread=0):
    """
    ``hcp_temporal_ica [... processing options]``

    ``hcp_tica [... processing options]``

    Runs the HCP temporal ICA pipeline (tICAPipeline.sh).

    Warning:
        The code expects the HCP minimal preprocessing pipeline, HCP ICAFix,
        HCP MSMAll and HCP make average dataset to be executed.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_tica_studyfolder (str, default ''):
            Overwrite the automatic QuNex's setup of the study folder, mainly
            useful for REUSE mode and advanced users.

        --hcp_tica_bolds (str, default ''):
            A comma separated list of fmri run names. Set to all session BOLDs
            by default.

        --hcp_tica_outfmriname (str, default 'rfMRI_REST'):
            Name to use for tICA pipeline outputs.

        --hcp_tica_surfregname (str, default ''):
            The registration string corresponding to the input files.

        --hcp_icafix_highpass (str, default detailed below):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix.

        --hcp_tica_procstring (str, default '<hcp_cifti_tail>_<hcp_tica_surfregname>_hp<hcp_icafix_highpass>_clean'):
            File name component representing the preprocessing already done,
            e.g. '_Atlas_MSMAll_hp0_clean'.

        --hcp_outgroupname (str, default ''):
            Name to use for the group output folder.

        --hcp_bold_res (str, default '2'):
            Resolution of data.

        --hcp_tica_timepoints (str, default ''):
            Output spectra size for sICA individual projection,
            RunsXNumTimePoints, like '4800'.

        --hcp_tica_num_wishart (str, default ''):
            How many wisharts to use in icaDim.

        --hcp_lowresmesh (int, default 32):
            Mesh resolution.

        --hcp_tica_mrfix_concat_name (str, default ''):
            If multi-run FIX was used, you must specify the concat name
            with this option.

        --hcp_tica_icamode (str, default 'NEW'):
            Whether to use parts of a previous tICA run (for instance, if this
            group has too few subjects to simply estimate a new tICA). Defaults
            to NEW, all other modes require specifying the
            `hcp_tica_precomputed_*` parameters. Value must be one of:

            - 'NEW'             ... estimate a new sICA and a new tICA,
            - 'REUSE_SICA_ONLY' ... reuse an existing sICA and estimate a new
              tICA,
            - 'INITIALIZE_TICA' ... reuse an existing sICA and use an
              existing tICA to start the estimation,
            - 'REUSE_TICA'      ... reuse an existing sICA and an existing tICA.

        --hcp_tica_precomputed_clean_folder (str, default ''):
            Group folder containing an existing tICA cleanup to make use
            of for REUSE or INITIALIZE modes.

        --hcp_tica_precomputed_fmri_name (str, default ''):
            The output fMRI name used in the previously computed tICA.

        --hcp_tica_precomputed_group_name (str, default ''):
            The group name used during the previously computed tICA.

        --hcp_tica_extra_output_suffix (str, default ''):
            Add something extra to most output filenames, for collision
            avoidance.

        --hcp_tica_pca_out_dim (str, default ''):
            Override number of PCA components to use for group sICA.

        --hcp_tica_pca_internal_dim (str, default ''):
            Override internal MIGP dimensionality.

        --hcp_tica_migp_resume (str, default 'YES'):
            Resume from a previous interrupted MIGP run, if present.

        --hcp_tica_sicadim_iters (int, default 100):
            Number of iterations or mode for estimating sICA dimensionality.

        --hcp_tica_sicadim_override (str, default ''):
            Use this dimensionality instead of icaDim's estimate.

        --hcp_low_sica_dims (str, default '7@8@9@10@11@12@13@14@15@16@17@18@19@20@21'):
            The low sICA dimensionalities to use for determining weighting for
            individual projection.

        --hcp_tica_reclean_mode (str, default ''):
            Whether the data should use ReCleanSignal.txt for DVARS.

        --hcp_tica_starting_step (str, default ''):
            What step to start processing at, one of:

            - 'MIGP',
            - 'GroupSICA',
            - 'indProjSICA',
            - 'ConcatGroupSICA',
            - 'ComputeGroupTICA',
            - 'indProjTICA',
            - 'ComputeTICAFeatures',
            - 'ClassifyTICA',
            - 'CleanData'.

        --hcp_tica_stop_after_step (str, default 'ComputeTICAFeatures'):
            What step to stop processing after, same valid values as for
            hcp_tica_starting_step.

        --hcp_tica_remove_manual_components (str, default ''):
            Text file containing the component numbers to be removed by
            cleanup, separated by spaces, requires either:
            --hcp_tica_icamode=REUSE_TICA or
            --hcp_tica_starting_step=CleanData.

        --hcp_tica_fix_legacy_bias (str, default 'YES'):
            Whether the input data used the legacy bias correction, YES or NO.

        --hcp_parallel_limit (str, default ''):
            How many subjects to do in parallel (local, not
            cluster-distributed) during individual projection.

        --hcp_tica_config_out (flag, optional):
            A flag that determines whether to generate config file for rerunning
            with similar settings, or for reusing these results for future
            cleaning. Not set by default.

        --hcp_tica_average_dataset (str, default ''):
            Location of the average dataset, the output from
            hcp_make_average_dataset command. Set this if using the average set
            from another study, this is usually used in combination with
            REUSE_TICA mode.

        --hcp_tica_extract_fmri_name_list (str, default ''):
            A comma separated list of list of fMRI run names to concatenate into
            the --hcp_tica_extract_fmri_out output after tICA cleanup.

        --hcp_tica_extract_fmri_out (str, default ''):
            fMRI name for concatenated extracted runs, requires
            --hcp_tica_extract_fmri_name_list.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --longitudinal:
            Set this flag if you are running the longitudinal variant of this
            command.

        --hcp_tica_longitudinal_extract_all (str, default ''):
            Extract all runs specified in hcp_tica_bolds, with output name
            matching the one from hcp_tica_mrfix_concat_name.

    Output files:
        If ran on a single session the results of this step can be found in
        the same sessions's root hcp folder. If ran on multiple sessions
        then a group folder is created inside the QuNex's session folder.

    Notes:
        the HCP Temporal ICA Pipeline needs to be executed in two steps, the
        first step runs the following steps:

        -  ``MIGP``,
        -  ``GroupSICA``,
        -  ``indProjSICA``,
        -  ``ConcatGroupSICA``,
        -  ``ComputeGroupTICA``,
        -  ``indProjTICA``,
        -  ``ComputeTICAFeatures``.

        Since automatic classification is not yet supported. Users need to
        classify the components manually and then rerun temporal ICA from
        CleanData step onwards. This is the reason that the
        ``hcp_tica_stop_after_step`` is by default set to
        ``ComputeTICAFeatures``. After the manual classification both
        ``hcp_tica_starting_step`` and ``hcp_tica_stop_after_step`` need to be
        set to ``CleanData``.

        In practice this means that after the HCP Temporal ICA Pipeline
        requirements have been satisified (you need to run the HCP Minimnal
        Preprocessing Pipeline,
        ```hcp_icafix`` <../../api/gmri/hcp_icafix.rst>`__,
        ```hcp_msmall`` <../../api/gmri/hcp_msmall.rst>`__ and
        ```hcp_make_average_dataset`` <../../api/gmri/hcp_make_average_dataset.rst>`__)
        you can run the first processing part, for example:

        .. code:: bash

           qunex hcp_temporal_ica \\
               --sessionsfolder="<path_to_study_folder>/sessions" \\
               --batchfile="<path_to_study_folder>/processing/batch.txt" \\
               --hcp_tica_bolds="fMRI_CONCAT_ALL" \\
               --hcp_tica_outfmriname="fMRI_CONCAT_ALL" \\
               --hcp_tica_mrfix_concat_name="fMRI_CONCAT_ALL" \\
               --hcp_tica_surfregname="MSMAll" \\
               --hcp_icafix_highpass="0" \\
               --hcp_outgroupname="hcp_group" \\
               --hcp_tica_timepoints=<read from post_fix logs> \\
               --hcp_tica_num_wishart="6" \\
               --hcp_parallel_limit="4"

        The ``hcp_tica_timepoints`` parameter value can be found inside the
        ``hcp post_fix`` logs under the label ``NumTimePoints``. If your study
        has many sessions you also need to set the ``hcp_parallel_limit`` to
        prevent too many sessions from processing and parallel. If you do not
        limit this, your system will most likely run out of memory. Once this
        part is done (note that this can take a couple of days with larger
        studies), the command will store the components in
        ``<sessionfolderpath>/hcp_group/hcp_group/MNINonLinear/Results/fMRI_CONCAT_ALL/tICA_d<N>``
        where ``<N>`` denotes the number of temporal ICA components. To inspect
        the components you can create a ``wb_command`` scene file:

        .. code:: bash

           GroupAverageName='hcp_group'
           tICADim=<N>
           TemplateFolder="/gpfs/gibbs/pi/n3/software/HCP/HCPpipelines/global/templates/tICA"
           ResultsFolder="<path_to_study_folder>/sessions/hcp_group/hcp_group/MNINonLinear/Results/fMRI_CONCAT_ALL/tICA_d<N>"
           TemplateComponentScene="${TemplateFolder}/tICA.scene"
           ResultComponentSceneFile="${ResultsFolder}/tICA_hcp_group.scene"
           ResultComponentSceneFileFinal="${ResultsFolder}/tICA_hcp_group_final.scene"
           cp ${TemplateComponentScene} ${ResultComponentSceneFile}
           cat "${TemplateComponentScene}" | sed s/ExampleGroupAverageName/${GroupAverageName}/g | sed s/ExampleDim/${tICADim}/g >| "${ResultComponentSceneFile}"

        Your scene file called tICA_hcp_group.scene will be created in
        ``<path_to_study_folder>/sessions/hcp_group/hcp_group/MNINonLinear/Results/fMRI_CONCAT_ALL/tICA_d<N>``.
        You can then zip the scene file in order to download it and explore it
        with Workbench on your computer:

        .. code:: bash

           cd ${ResultsFolder}
           wb_command -zip-scene-file \\
               tICA_hcp_group.scene \\
               tICA_hcp_group_fMRI_CONCAT_ALL \\
               -skip-missing \\
               tICA_hcp_group_fMRI_CONCAT_ALL.zip

        MATLAB large variable error:
            If receiving an error in MATLAB saying that a variable was not saved
            because it is larger than 2GB, you need to set the default saving format
            in MATLAB, to do this run MATLAB and execute:

            .. code:: matlab

               s = settings();
               s.matlab.general.matfile.SaveFormat.PersonalValue = 'v7.3';

        Mapping of QuNex parameters onto HCP temporal ICA parameters:
            Below is a detailed specification about how QuNex parameters are
            mapped onto the HCP temporal ICA parameters.

            ===================================== ===============================
            QuNex parameter                       HCP temporal ICA parameter
            ===================================== ===============================
            ``hcp_tica_bolds``                    ``fmri-names``
            ``hcp_tica_outfmriname``              ``output-fmri-name``
            ``hcp_tica_surfregname``              ``surf-reg-name``
            ``hcp_tica_procstring``               ``proc-string``
            ``hcp_outgroupname``                  ``out-group-name``
            ``hcp_bold_res``                      ``fmri-resolution``
            ``hcp_tica_timepoints``               ``session-expected-timepoints``
            ``hcp_tica_num_wishart``              ``num-wishart``
            ``hcp_lowresmesh``                    ``low-res``
            ``hcp_tica_mrfix_concat_name``        ``mrfix-concat-name``
            ``hcp_tica_icamode``                  ``ica-mode``
            ``hcp_tica_precomputed_clean_folder`` ``precomputed-clean-folder``
            ``hcp_tica_precomputed_fmri_name``    ``precomputed-clean-fmri-name``
            ``hcp_tica_precomputed_group_name``   ``precomputed-group-name``
            ``hcp_tica_extra_output_suffix``      ``extra-output-suffix``
            ``hcp_tica_pca_out_dim``              ``pca-out-dim``
            ``hcp_tica_pca_internal_dim``         ``pca-internal-dim``
            ``hcp_tica_migp_resume``              ``migp-resume``
            ``hcp_tica_sicadim_iters``            ``sicadim-iters``
            ``hcp_tica_sicadim_override``         ``sicadim-override``
            ``hcp_low_sica_dims``                 ``low-sica-dims``
            ``hcp_tica_reclean_mode``             ``reclean-mode``
            ``hcp_tica_starting_step``            ``starting-step``
            ``hcp_tica_stop_after_step``          ``stop-after-step``
            ``hcp_tica_remove_manual_components`` ``manual-components-to-remove``
            ``hcp_tica_fix_legacy_bias``          ``fix-legacy-bias``
            ``hcp_parallel_limit``                ``parallel-limit``
            ``hcp_tica_config_out``               ``config-out``
            ``hcp_tica_extract_fmri_name_list``   ``extract-fmri-name-list``
            ``hcp_tica_extract_fmri_out``         ``extract-fmri-out``
            ``hcp_matlab_mode``                   ``matlab-run-mode``
            ``longitudinal``                      ``is-longitudinal``
            ``hcp_longitudinal_template``         ``longitudinal-template``
            ``hcp_tica_longitudinal_extract_all`` ``longitudinal-extract-all``
            ===================================== ===============================


    Examples:
        Example run::

            qunex hcp_temporal_ica \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_tica_bolds="fMRI_CONCAT_ALL" \\
                --hcp_tica_outfmriname="fMRI_CONCAT_ALL" \\
                --hcp_tica_mrfix_concat_name="fMRI_CONCAT_ALL" \\
                --hcp_tica_surfregname="MSMAll" \\
                --hcp_icafix_highpass="0" \\
                --hcp_outgroupname="hcp_group" \\
                --hcp_tica_timepoints="<value can be found in hcp_post_fix logs>" \\
                --hcp_tica_num_wishart="6" \\
                --hcp_matlab_mode="interpreted"

    """

    r = "\n------------------------------------------------------------"
    r += "\nSession ids: %s \n[started on %s]" % (
        sessionids,
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP temporal ICA Pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = "Error"

    try:
        # if longitudinal is set, session list needs to be provided
        if options["longitudinal"]:
            if not options["hcp_longitudinal_sessions"]:
                r += "\n---> ERROR: hcp_longitudinal_sessions is not provided!"
                run = False
            session_list = options["hcp_longitudinal_sessions"].replace(",", "@")

        # if sessions is not a batch file skip batch file validity checks
        elif ("sessions" in options and os.path.exists(options["sessions"])) or (
            "batchfile" in options and os.path.exists(options["batchfile"])
        ):
            doHCPOptionsCheck(options, "hcp_temporal_ica")

            # session_list
            session_list = ""

            # check sessions
            for session in sessions:
                if "hcp" not in session:
                    r += (
                        "\n---> ERROR: There is no hcp info for session %s in batch.txt"
                        % (session["id"])
                    )
                    run = False

                # session_list
                if session_list == "":
                    session_list = session["id"] + options["hcp_suffix"]
                else:
                    session_list = (
                        session_list + "@" + session["id"] + options["hcp_suffix"]
                    )
        else:
            # session_list
            session_list = ""

            for session in sessions:
                # session_list
                if session_list == "":
                    session_list = session["id"] + options["hcp_suffix"]
                else:
                    session_list = (
                        session_list + "@" + session["id"] + options["hcp_suffix"]
                    )

        # mandatory parameters
        # hcp_tica_bolds
        fmri_names = ""
        if options["hcp_tica_bolds"] is None:
            r += "\n---> ERROR: hcp_tica_bolds is not provided!"
            run = False
        else:
            # defined bolds
            fmri_names = options["hcp_tica_bolds"].replace(",", "@")

        # hcp_tica_outfmriname
        out_fmri_name = ""
        if options["hcp_tica_outfmriname"] is None:
            r += "\n---> ERROR: hcp_tica_outfmriname is not provided!"
            run = False
        else:
            out_fmri_name = options["hcp_tica_outfmriname"]

        # hcp_tica_surfregname
        surfregname = ""
        if options["hcp_tica_surfregname"] is None:
            r += "\n---> ERROR: hcp_tica_surfregname is not provided!"
            run = False
        else:
            surfregname = options["hcp_tica_surfregname"]

        # hcp_icafix_highpass
        icafix_highpass = ""
        if options["hcp_icafix_highpass"] is None:
            r += "\n---> ERROR: hcp_icafix_highpass is not provided!"
            run = False
        else:
            icafix_highpass = options["hcp_icafix_highpass"]

        # hcp_tica_procstring
        if options["hcp_tica_procstring"] is None:
            proc_string = ""
            if "hcp_cifti_tail" in options:
                proc_string = "%s_" % "_Atlas"

            proc_string = "%s%s_hp%s_clean" % (
                proc_string,
                surfregname,
                icafix_highpass,
            )
        else:
            proc_string = options["hcp_tica_procstring"]

        # hcp_outgroupname
        outgroupname = ""
        if options["hcp_outgroupname"] is None:
            r += "\n---> ERROR: hcp_outgroupname is not provided!"
            run = False
        else:
            outgroupname = options["hcp_outgroupname"]

        # hcp_tica_timepoints
        timepoints = ""
        if options["hcp_tica_timepoints"] is None:
            r += "\n---> ERROR: hcp_tica_timepoints is not provided!"
            run = False
        else:
            timepoints = options["hcp_tica_timepoints"]

        # hcp_tica_timepoints
        num_wishart = ""
        if options["hcp_tica_num_wishart"] is None:
            r += "\n---> ERROR: hcp_tica_num_wishart is not provided!"
            run = False
        else:
            num_wishart = options["hcp_tica_num_wishart"]

        # if using a manual study_dir bypass all validity checks and preparation
        if options["hcp_tica_studyfolder"]:
            study_dir = options["hcp_tica_studyfolder"]
        else:
            study_dir = ""

            # longitudinal
            if options["longitudinal"]:
                studyfolder = gc.deduce_folders(options)["basefolder"]
                if not studyfolder:
                    r += "\nERROR: cannot deduce the QuNex study folder from provided parameters! Please provide the sessionsfolder or the studyfolder parameter."
                    run = False

                if not options["hcp_longitudinal_subject"]:
                    r += "\nERROR: hcp_longitudinal_subject is a mandatory parameter for the longitudinal mode of temporal ICA!"
                    run = False

                # set study dir
                study_dir = os.path.join(
                    studyfolder, "subjects", options["hcp_longitudinal_subject"]
                )

                # create folder
                if not os.path.exists(study_dir):
                    os.makedirs(study_dir)

            # single session
            elif len(sessions) == 1:
                # get session info
                study_dir = sessions[0]["hcp"]

            # multi session
            else:
                # set study dir
                study_dir = os.path.join(options["sessionsfolder"], outgroupname)

                # create folder
                if not os.path.exists(study_dir):
                    os.makedirs(study_dir)

                # link sessions
                for session in sessions:
                    # prepare folders
                    session_name = session["id"] + options["hcp_suffix"]
                    source_dir = os.path.join(session["hcp"], session_name)
                    target_dir = os.path.join(study_dir, session_name)

                    # link
                    gc.link_or_copy(source_dir, target_dir, symlink=True)

                # check for make average dataset outputs
                mad_file = os.path.join(
                    options["sessionsfolder"],
                    "average_dataset",
                    outgroupname,
                    "MNINonLinear",
                    "fsaverage_LR32k",
                    outgroupname + ".midthickness_MSMAll_va.32k_fs_LR.dscalar.nii",
                )
                if not os.path.exists(mad_file):
                    r += "\n---> ERROR: %s does not exist!" % mad_file
                    r += "\n---> ERROR: You need to run hcp_make_average_dataset before running hcp_temporal_ica!"
                    run = False

                # create folder if it does not exist
                out_dir = os.path.join(study_dir, outgroupname, "MNINonLinear")
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)

        # if hcp_tica_average_dataset is provided copy or link it into the outgroupname
        mad_dir = os.path.join(study_dir, outgroupname)
        if options["hcp_tica_average_dataset"] is not None:
            gc.link_or_copy(options["hcp_tica_average_dataset"], mad_dir, symlink=True)
        elif options["longitudinal"]:
            # if longitudinal, check if we have to copy from sessions to subjects
            studyfolder = gc.deduce_folders(options)["basefolder"]
            if not studyfolder:
                r += "\nERROR: cannot deduce the QuNex study folder from provided parameters! Please provide the sessionsfolder or the studyfolder parameter."
                run = False
            sessions_mad_dir = os.path.join(
                studyfolder, "sessions", "average_dataset", outgroupname
            )
            if os.path.exists(sessions_mad_dir):
                gc.link_or_copy(sessions_mad_dir, mad_dir, symlink=True)

        # matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
                run = False
            else:
                matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
        else:
            if options["hcp_matlab_mode"] == "compiled":
                matlabrunmode = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                matlabrunmode = "1"
            elif options["hcp_matlab_mode"] == "octave":
                matlabrunmode = "2"
            else:
                r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                run = False

        # build the command
        if run:
            comm = (
                '%(script)s \
                --study-folder="%(study_dir)s" \
                --session-list="%(session_list)s" \
                --fmri-names="%(fmri_names)s" \
                --output-fmri-name="%(output_fmri_name)s" \
                --surf-reg-name="%(surf_reg_name)s" \
                --fix-high-pass="%(icafix_highpass)s" \
                --proc-string="%(proc_string)s" \
                --out-group-name="%(outgroupname)s" \
                --fmri-resolution="%(fmri_resolution)s" \
                --session-expected-timepoints="%(timepoints)s" \
                --num-wishart="%(num_wishart)s" \
                --low-res="%(low_res)s" \
                --matlab-run-mode="%(matlabrunmode)s" \
                --stop-after-step="%(stopafterstep)s"'
                % {
                    "script": os.path.join(
                        os.environ["HCPPIPEDIR"], "tICA", "tICAPipeline.sh"
                    ),
                    "study_dir": study_dir,
                    "session_list": session_list,
                    "fmri_names": fmri_names,
                    "output_fmri_name": out_fmri_name,
                    "surf_reg_name": surfregname,
                    "icafix_highpass": icafix_highpass,
                    "proc_string": proc_string,
                    "outgroupname": outgroupname,
                    "fmri_resolution": options["hcp_bold_res"],
                    "timepoints": timepoints,
                    "num_wishart": num_wishart,
                    "low_res": options["hcp_lowresmesh"],
                    "matlabrunmode": matlabrunmode,
                    "stopafterstep": options["hcp_tica_stop_after_step"],
                }
            )

            # -- Optional parameters
            # hcp_tica_mrfix_concat_name
            if options["hcp_tica_mrfix_concat_name"] is not None:
                comm += (
                    '                    --mrfix-concat-name="%s"'
                    % options["hcp_tica_mrfix_concat_name"]
                )

            # hcp_tica_icamode
            if options["hcp_tica_icamode"] is not None:
                comm += (
                    '                    --ica-mode="%s"' % options["hcp_tica_icamode"]
                )

            # hcp_tica_precomputed_clean_folder
            if options["hcp_tica_precomputed_clean_folder"] is not None:
                comm += (
                    '                    --precomputed-clean-folder="%s"'
                    % options["hcp_tica_precomputed_clean_folder"]
                )

            # hcp_tica_precomputed_fmri_name
            if options["hcp_tica_precomputed_fmri_name"] is not None:
                comm += (
                    '                    --precomputed-clean-fmri-name="%s"'
                    % options["hcp_tica_precomputed_fmri_name"]
                )

            # hcp_tica_precomputed_group_name
            if options["hcp_tica_precomputed_group_name"] is not None:
                comm += (
                    '                    --precomputed-group-name="%s"'
                    % options["hcp_tica_precomputed_group_name"]
                )

            # hcp_tica_extra_output_suffix
            if options["hcp_tica_extra_output_suffix"] is not None:
                comm += (
                    '                    --extra-output-suffix="%s"'
                    % options["hcp_tica_extra_output_suffix"]
                )

            # hcp_tica_pca_out_dim
            if options["hcp_tica_pca_out_dim"] is not None:
                comm += (
                    '                    --pca-out-dim="%s"'
                    % options["hcp_tica_pca_out_dim"]
                )

            # hcp_tica_pca_internal_dim
            if options["hcp_tica_pca_internal_dim"] is not None:
                comm += (
                    '                    --pca-internal-dim="%s"'
                    % options["hcp_tica_pca_internal_dim"]
                )

            # hcp_tica_migp_resume
            if options["hcp_tica_migp_resume"] is not None:
                comm += (
                    '                    --migp-resume="%s"'
                    % options["hcp_tica_migp_resume"]
                )

            # hcp_tica_sicadim_iters
            if options["hcp_tica_sicadim_iters"] is not None:
                comm += (
                    '                    --sicadim-iters="%s"'
                    % options["hcp_tica_sicadim_iters"]
                )

            # hcp_tica_sicadim_override
            if options["hcp_tica_sicadim_override"] is not None:
                comm += (
                    '                    --sicadim-override="%s"'
                    % options["hcp_tica_sicadim_override"]
                )

            # hcp_low_sica_dims
            if options["hcp_low_sica_dims"] is not None:
                comm += (
                    '                    --low-sica-dims="%s"'
                    % options["hcp_low_sica_dims"]
                )

            # hcp_tica_reclean_mode
            if options["hcp_tica_reclean_mode"] is not None:
                comm += (
                    '                    --reclean-mode="%s"'
                    % options["hcp_tica_reclean_mode"]
                )

            # hcp_tica_starting_step
            if options["hcp_tica_starting_step"] is not None:
                comm += (
                    '                    --starting-step="%s"'
                    % options["hcp_tica_starting_step"]
                )

            # hcp_tica_remove_manual_components
            if options["hcp_tica_remove_manual_components"] is not None:
                comm += (
                    '                    --manual-components-to-remove="%s"'
                    % options["hcp_tica_remove_manual_components"]
                )

            # hcp_tica_fix_legacy_bias
            if options["hcp_tica_fix_legacy_bias"] is not None:
                comm += (
                    '                    --fix-legacy-bias="%s"'
                    % options["hcp_tica_fix_legacy_bias"]
                )

            # hcp_parallel_limit
            if options["hcp_parallel_limit"] is not None:
                comm += (
                    '                    --parallel-limit="%s"'
                    % options["hcp_parallel_limit"]
                )

            # hcp_tica_config_out
            if options["hcp_tica_config_out"]:
                comm += "                    --config-out"

            # hcp_tica_extract_fmri_name_list
            if options["hcp_tica_extract_fmri_name_list"]:
                comm += f'                    --extract-fmri-name-list="{options["hcp_tica_extract_fmri_name_list"].replace(",", "@")}"'

            # hcp_tica_extract_fmri_out
            if options["hcp_tica_extract_fmri_out"]:
                comm += f'                    --extract-fmri-out="{options["hcp_tica_extract_fmri_out"]}"'

            # longitudinal
            if options["longitudinal"]:
                comm += '                --is-longitudinal="TRUE"'
                comm += (
                    '                --longitudinal-template="'
                    + options["hcp_longitudinal_template"]
                    + '"'
                )
                comm += (
                    '                --longitudinal-subject="'
                    + options["hcp_longitudinal_subject"]
                    + '"'
                )
                if options["hcp_tica_longitudinal_extract_all"]:
                    comm += '                --longitudinal-extract-all="TRUE"'

                if not options["hcp_tica_icamode"]:
                    comm += '                    --ica-mode="REUSE_TICA"'
                elif options["hcp_tica_icamode"] != "REUSE_TICA":
                    r += "\n---> ERROR: Longitudinal processing is set, but hcp_tica_icamode is not set to REUSE_TICA, this will not work!"
                    run = False

            # -- Report command
            if run:
                r += (
                    "\n\n------------------------------------------------------------\n"
                )
                r += "Running HCP Pipelines command via QuNex:\n\n"
                r += comm.replace("                --", "\n    --")
                r += "\n------------------------------------------------------------\n"

        # -- Run
        if run:
            if options["run"] == "run":
                logtags = [options["logtag"]]
                if options["longitudinal"]:
                    logtags.append("long")

                r, _, report, failed = pc.runExternalForFile(
                    None,
                    comm,
                    "Running HCP temporal ICA",
                    overwrite=True,
                    thread=outgroupname,
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=logtags,
                    fullTest=None,
                    shell=True,
                    r=r,
                )

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(
                    None, None, "HCP temporal ICA", r, overwrite=True
                )
                if passed is None:
                    r += "\n---> HCP temporal ICA can be run"
                    report = "HCP temporal ICA can be run"
                    failed = 0

        else:
            r += "\n---> Session cannot be processed."
            report = "HCP temporal ICA cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        failed = 1

    r += (
        "\n\nHCP temporal ICA Preprocessing %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, (sessionids, report, failed))


def hcp_make_average_dataset(sessions, sessionids, options, overwrite=True, thread=0):
    """
    ``hcp_make_average_dataset [... processing options]``

    ``hcp_mad [... processing options]``

    Runs the HCP make average dataset pipeline (MakeAverageDataset.sh).

    Warning:
        The code expects the HCP minimal preprocessing pipeline to be executed.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions' information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_surface_atlas_dir (str, default '${HCPPIPEDIR}/global/templates/standard_mesh_atlases'):
            Path to the location of the standard surfaces.

        --hcp_grayordinates_dir (str, default '${HCPPIPEDIR}/global/templates/91282_Greyordinates'):
            Path to the location of the standard grayorinates space.

        --hcp_hiresmesh (int, default 164):
            High resolution mesh node count.

        --hcp_lowresmeshes (int, default 32):
            Low resolution meshes node count. To provide more values
            separate them with commas.

        --hcp_freesurfer_labels (str, default '${HCPPIPEDIR}/global/config/FreeSurferAllLut.txt'):
            Path to the location of the FreeSurfer look up table file.

        --hcp_pregradient_smoothing (int, default 1):
            Sigma of the pregradient smoothing.

        --hcp_mad_regname (str, default 'MSMALL'):
            Name of the registration.

        --hcp_mad_videen_maps (str, default 'corrThickness,thickness,MyelinMap_BC,SmoothedMyelinMap_BC'):
            Maps you want to use for the videen palette.

        --hcp_mad_greyscale_maps (str, default 'sulc,curvature'):
            Maps you want to use for the greyscale palette.

        --hcp_mad_distortion_maps (str, default 'SphericalDistortion,ArealDistortion,EdgeDistortion'):
            Distortion maps.

        --hcp_mad_gradient_maps (str, default 'MyelinMap_BC,SmoothedMyelinMap_BC,corrThickness'):
            Maps you want to compute the gradient on.

        --hcp_mad_std_maps (str, default 'sulc@curvature,corrThickness,thickness,MyelinMap_BC'):
            Maps you want to compute the standard deviation on.

        --hcp_mad_multi_maps (str, default 'NONE'):
            Maps with more than one map (column) that cannot be merged and must
            be averaged.

    Output files:
        A group folder with outputs is created inside the average_dataset foledr in
        QuNex's sessions folder.

    Notes:
        Mapping of QuNex parameters onto HCP make average dataset parameters:
            Below is a detailed specification about how QuNex parameters are
            mapped onto the HCP make average dataset parameters.

            ================================== =====================================
            QuNex parameter                    HCP make average dataset parameter
            ================================== =====================================
            ``hcp_outgroupname``               ``group-average-name``
            ``hcp_surface_atlas_dir``          ``surface-atlas-dir``
            ``hcp_grayordinates_dir``          ``grayordinates-space-dir``
            ``hcp_hiresmesh``                  ``high-res-mesh``
            ``hcp_lowresmeshes``               ``low-res-meshes``
            ``hcp_freesurfer_labels``          ``freesurfer-labels``
            ``hcp_pregradient_smoothing``      ``sigma``
            ``hcp_mad_regname``                ``reg-name``
            ``hcp_mad_videen_maps``            ``videen-maps``
            ``hcp_mad_greyscale_maps``         ``greyscale-maps``
            ``hcp_mad_distortion_maps``        ``distortion-maps``
            ``hcp_mad_gradient_maps``          ``gradient-maps``
            ``hcp_mad_std_maps``               ``std-maps``
            ``hcp_mad_multi_maps``             ``multi-maps``
            ================================== =====================================

    Examples:
        A run with the default set of parameters::

            qunex hcp_make_average_dataset \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_outgroupname="hcp_group"

    """

    r = "\n------------------------------------------------------------"
    r += "\nSession ids: %s \n[started on %s]" % (
        sessionids,
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP make average dataset pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = "Error"

    try:
        doHCPOptionsCheck(options, "hcp_make_average_dataset")

        # subject_list
        subject_list = ""

        # check sessions
        for session in sessions:
            hcp = getHCPPaths(session, options)

            if "hcp" not in session:
                r += (
                    "\n---> ERROR: There is no hcp info for session %s in batch.txt"
                    % (session["id"])
                )
                run = False

            # subject_list
            if subject_list == "":
                subject_list = session["id"] + options["hcp_suffix"]
            else:
                subject_list = (
                    subject_list + "@" + session["id"] + options["hcp_suffix"]
                )

        # mandatory parameters
        # hcp_outgroupname
        outgroupname = ""
        if options["hcp_outgroupname"] is None:
            r += "\n---> ERROR: hcp_outgroupname is not provided!"
            run = False
        else:
            outgroupname = options["hcp_outgroupname"]

        # study_dir prep
        study_dir = ""

        # single session
        if len(sessions) == 1:
            r += "\n---> ERROR: hcp_make_average_dataset needs to be ran across several sessions!"
            run = False

        # multi session
        else:
            # set study dir
            study_dir = os.path.join(
                options["sessionsfolder"], "average_dataset", outgroupname
            )

            # create folder
            if not os.path.exists(study_dir):
                os.makedirs(study_dir)

            # link sessions
            for session in sessions:
                # prepare folders
                session_name = session["id"] + options["hcp_suffix"]
                source_dir = os.path.join(session["hcp"], session_name)
                target_dir = os.path.join(study_dir, session_name)

                # link
                gc.link_or_copy(source_dir, target_dir, symlink=True)

        # hcp_surface_atlas_dir
        surface_atlas = ""
        if options["hcp_surface_atlas_dir"] is None:
            surface_atlas = os.path.join(hcp["hcp_Templates"], "standard_mesh_atlases")
        else:
            surface_atlas = options["hcp_surface_atlas_dir"]

        # hcp_grayordinates_dir
        grayordinates = ""
        if options["hcp_grayordinates_dir"] is None:
            grayordinates = os.path.join(hcp["hcp_Templates"], "91282_Greyordinates")
        else:
            grayordinates = options["hcp_grayordinates_dir"]

        # hcp_freesurfer_labels
        freesurferlabels = ""
        if options["hcp_freesurfer_labels"] is None:
            freesurferlabels = os.path.join(hcp["hcp_Config"], "FreeSurferAllLut.txt")
        else:
            freesurferlabels = options["hcp_freesurfer_labels"]

        # build the command
        if run:
            comm = (
                '%(script)s \
                --study-folder="%(study_dir)s" \
                --subject-list="%(subject_list)s" \
                --group-average-name="%(group_average_name)s" \
                --surface-atlas-dir="%(surface_atlas)s" \
                --grayordinates-space-dir="%(grayordinates)s" \
                --high-res-mesh="%(highresmesh)s" \
                --low-res-meshes="%(lowresmeshes)s" \
                --freesurfer-labels="%(freesurferlabels)s" \
                --sigma="%(sigma)s" \
                --reg-name="%(regname)s" \
                --videen-maps="%(videenmaps)s" \
                --greyscale-maps="%(greyscalemaps)s" \
                --distortion-maps="%(distortionmaps)s" \
                --gradient-maps="%(gradientmaps)s" \
                --std-maps="%(stdmaps)s" \
                --multi-maps="%(multimaps)s"'
                % {
                    "script": os.path.join(
                        hcp["hcp_base"],
                        "Supplemental",
                        "MakeAverageDataset",
                        "MakeAverageDataset.sh",
                    ),
                    "study_dir": study_dir,
                    "subject_list": subject_list,
                    "group_average_name": outgroupname,
                    "surface_atlas": surface_atlas,
                    "grayordinates": grayordinates,
                    "highresmesh": options["hcp_hiresmesh"],
                    "lowresmeshes": options["hcp_lowresmeshes"].replace(",", "@"),
                    "freesurferlabels": freesurferlabels,
                    "sigma": options["hcp_pregradient_smoothing"],
                    "regname": options["hcp_mad_regname"],
                    "videenmaps": options["hcp_mad_videen_maps"].replace(",", "@"),
                    "greyscalemaps": options["hcp_mad_greyscale_maps"].replace(
                        ",", "@"
                    ),
                    "distortionmaps": options["hcp_mad_distortion_maps"].replace(
                        ",", "@"
                    ),
                    "gradientmaps": options["hcp_mad_gradient_maps"].replace(",", "@"),
                    "stdmaps": options["hcp_mad_std_maps"].replace(",", "@"),
                    "multimaps": options["hcp_mad_multi_maps"].replace(",", "@"),
                }
            )

            # -- Report command
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("                --", "\n    --")
            r += "\n------------------------------------------------------------\n"

            # -- Run
            if options["run"] == "run":
                r, endlog, report, failed = pc.runExternalForFile(
                    None,
                    comm,
                    "Running HCP make average dataset",
                    overwrite=True,
                    thread=outgroupname,
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    fullTest=None,
                    shell=True,
                    r=r,
                )

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(
                    None, None, "HCP make average dataset", r, overwrite=True
                )
                if passed is None:
                    r += "\n---> HCP make average dataset can be run"
                    report = "HCP make average dataset can be run"
                    failed = 0

        else:
            r += "\n---> Session cannot be processed."
            report = "HCP make average dataset cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        failed = 1

    r += (
        "\n\nHCP make average dataset preprocessing %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, (sessionids, report, failed))


def hcp_fmri_stats(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_fmri_stats [... processing options]``

    Runs the fMRI Statistics step of HCP Pipeline (fMRIStats.sh).
    Computes fMRI statistics including mTSNR, fCNR, and percent BOLD.

    Warning:
        The code expects the input images to be named and present in the QuNex
        folder structure. The function will look into folder::

            <session id>/hcp/<session id>

        for data.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no).

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --log (str, default 'keep'):
            Whether to keep ('keep') or remove ('remove') the temporary logs.

        --hcp_concat_names (str, default 'fMRI_CONCAT_ALL'):
            A comma separated list of fMRI concat names (e.g. tfMRI_ALLTASKS).
            If single-run FIX is used, this list must be exactly 1 element
            long.

        --hcp_icafix_highpass (str, default '0'):
            The high pass filter value used in ICA+FIX.

        --hcp_fmristats_regname (str, default ''):
            Surface registration name.

        --hcp_fmristats_process_volume (str, default ''):
            Whether to process volume data, TRUE or FALSE.

        --hcp_fmristats_cleanup_effects (str, default ''):
            Whether to compute cleanup effects metrics, TRUE or FALSE.

        --hcp_fmristats_procstring (str, default ''):
            Processing string suffix for cleaned data.

        --hcp_fmristats_icamode (str, default ''):
            ICA mode: 'sICA' for spatial ICA only, 'sICA+tICA' for combined
            spatial+temporal ICA.

        --hcp_fmristats_fmri_names (str, default ''):
            A comma separated list of fMRI single run names (only required if
            data was processed with single-run FIX, must be in order and
            complete).

        --hcp_fmristats_tica_component_tcs (str, default ''):
            Path to tICA timecourse CIFTI (required if tica_icamode is
            sICA+tICA).

        --hcp_fmristats_tica_component_noise (str, default ''):
            Path to tICA component noise indices text file (required if
            tica_icamode is sICA+tICA).

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folder inside the same session's root hcp folder.

    Notes:
        hcp_fmri_stats parameter mapping:

            ============================================ ============================
            QuNex parameter                              HCPpipelines parameter
            ============================================ ============================
            ``hcp_concat_names``                         ``concat-names``
            ``hcp_icafix_highpass``                      ``high-pass``
            ``hcp_fmristats_procstring``                 ``proc-string``
            ``hcp_fmristats_regname``                    ``reg-name``
            ``hcp_fmristats_process_volume``             ``process-volume``
            ``hcp_fmristats_cleanup_effects``            ``cleanup-effects``
            ``hcp_fmristats_icamode``                    ``ica-mode``
            ``hcp_fmristats_fmri_names``                 ``fmri-names``
            ``hcp_fmristats_tica_component_tcs``         ``tica-component-tcs``
            ``hcp_fmristats_tica_component_noise``       ``tica-component-noise``
            ``hcp_matlab_mode``                          ``matlab-run-mode``
            ============================================ ============================

    Examples:
        ::

            qunex hcp_fmri_stats \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_concat_names="fMRI_CONCAT_ALL" \\
                --hcp_icafix_highpass="2000" \\
                --hcp_matlab_mode="interpreted"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP fMRIStats pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = "HCP fMRI Stats"
    failed = 0

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, "hcp_fmri_stats")
        doHCPOptionsCheck(options, "hcp_fmri_stats")

        # subject
        subject = sinfo["id"] + options["hcp_suffix"]

        # --- Mandatory parameters
        # hcp_concat_names
        concat_names = options["hcp_concat_names"].replace(",", "@")

        # hcp_icafix_highpass
        highpass = 0
        if options["hcp_icafix_highpass"] is not None:
            highpass = options["hcp_icafix_highpass"]

        # hcp_fmristats_procstring
        if options["hcp_fmristats_procstring"] is None:
            r += "\\nERROR: hcp_fmristats_procstring parameter is not set!\n"
            run = False

        # --- matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
                run = False
            else:
                matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
        else:
            if options["hcp_matlab_mode"] == "compiled":
                matlabrunmode = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                matlabrunmode = "1"
            elif options["hcp_matlab_mode"] == "octave":
                matlabrunmode = "2"
            else:
                r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                run = False

        # --- Build the command
        if run:
            comm = (
                '%(script)s \
                --study-folder="%(studyfolder)s" \
                --subject="%(subject)s" \
                --concat-names="%(concat_names)s" \
                --high-pass="%(highpass)s" \
                --proc-string="%(proc_string)s" \
                --matlab-run-mode="%(matlabrunmode)s"'
                % {
                    "script": os.path.join(
                        os.environ["HCPPIPEDIR"], "fMRIStats", "fMRIStats.sh"
                    ),
                    "studyfolder": sinfo["hcp"],
                    "subject": subject,
                    "concat_names": concat_names,
                    "highpass": highpass,
                    "proc_string": options["hcp_fmristats_procstring"],
                    "matlabrunmode": matlabrunmode,
                }
            )

            # --- Optional parameters
            # hcp_fmristats_regname
            if options["hcp_fmristats_regname"] is not None and options[
                "hcp_fmristats_regname"
            ] not in [
                "NONE",
                "none",
                "None",
            ]:
                comm += (
                    '                --reg-name="%s"' % options["hcp_fmristats_regname"]
                )

            # hcp_fmristats_process_volume
            if options["hcp_fmristats_process_volume"] is not None:
                comm += (
                    '                --process-volume="%s"'
                    % options["hcp_fmristats_process_volume"]
                )

            # hcp_fmristats_cleanup_effects
            if options["hcp_fmristats_cleanup_effects"] is not None:
                comm += (
                    '                --cleanup-effects="%s"'
                    % options["hcp_fmristats_cleanup_effects"]
                )

            # hcp_fmristats_icamode
            if options["hcp_fmristats_icamode"] is not None:
                comm += (
                    '                --ica-mode="%s"' % options["hcp_fmristats_icamode"]
                )

            # hcp_fmristats_fmri_names
            if options["hcp_fmristats_fmri_names"] is not None:
                fmri_names = options["hcp_fmristats_fmri_names"].replace(",", "@")
                comm += '                --fmri-names="%s"' % fmri_names

            # hcp_fmristats_tica_component_tcs
            if options["hcp_fmristats_tica_component_tcs"] is not None:
                comm += (
                    '                --tica-component-tcs="%s"'
                    % options["hcp_fmristats_tica_component_tcs"]
                )

            # hcp_fmristats_tica_component_noise
            if options["hcp_fmristats_tica_component_noise"] is not None:
                comm += (
                    '                --tica-component-noise="%s"'
                    % options["hcp_fmristats_tica_component_noise"]
                )

            # -- Report command
            if run:
                r += (
                    "\n\n------------------------------------------------------------\n"
                )
                r += "Running HCP Pipelines command via QuNex:\n\n"
                r += comm.replace("                --", "\n    --")
                r += "\n------------------------------------------------------------\n"

        # -- Run
        if run:
            if options["run"] == "run":
                r, endlog, report, failed = pc.runExternalForFile(
                    None,
                    comm,
                    "Running HCP fMRI Stats",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    fullTest=None,
                    shell=True,
                    r=r,
                )

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(
                    None, None, "HCP fMRI Stats", r, overwrite=overwrite
                )
                if passed is None:
                    r += "\n---> HCP fMRI Stats can be run"
                    report = "HCP fMRI Stats can be run"
                    failed = 0

        else:
            r += "\n---> Session cannot be processed."
            report = "HCP fMRI Stats cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        failed = 1

    r += (
        "\n\nHCP fMRI Stats %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, (sinfo["id"], report, failed))


def hcp_apply_auto_reclean(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_apply_auto_reclean [... processing options]``

    Runs the ApplyAutoRecleanPipeline step of HCP Pipeline
    (ApplyAutoRecleanPipeline.sh).

    Warning:
        The code expects the input images to be named and present in the QuNex
        folder structure. The function will look into folder::

            <session id>/hcp/<session id>

        for files::

            MNINonLinear/Results/<boldname>/<boldname>.nii.gz

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_icafix_bolds (str, default ''):
            Specify a list of bolds for ICAFix. You should specify how to
            group/concatenate bolds together along with bolds, e.g.
            "<group1>:<boldname1>,<boldname2>|
            <group2>:<boldname3>,<boldname4>", in this case multi-run HCP
            ICAFix will be executed, which is the default. Instead of full bold
            names, you can also  use bold tags from the batch file. If this
            parameter is not provided ICAFix will bundle all bolds together and
            execute multi-run HCP ICAFix, the concatenated file will be named
            fMRI_CONCAT_ALL. Alternatively, you can specify a comma separated
            list of bolds without groups, e.g. "<boldname1>,<boldname2>", in
            this case single-run HCP ICAFix will be executed over specified
            bolds. This is a legacy option and not recommended.

        --hcp_icafix_highpass (int, default 0):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix.

        --hcp_bold_res (str, default '2'):
            Resolution of data.

        --hcp_lowresmesh (int, default 32):
            Mesh resolution.

        --hcp_grayordinatesres (int, default 2):
            The size of voxels for the subcortical and cerebellar data in
            grayordinate space in mm.

        --hcp_bold_smoothFWHM (int, default 2):
            Smoothing FWHM that matches what was used in the fMRISurface
            pipeline.

        --hcp_autoreclean_model_folder (str, default '<$HCPPIPEDIR/ICAFIX/rclean_models>'):
            The folder path of the trained models. Will use the HCP's model
            folder by default.

        --hcp_autoreclean_model_to_use (str, default 'MLP,RandomForest'):
            A comma separeted list of models to use. HCP available models are:
            MLP, RandomForest, Xgboost and XgboostEnsemble. Will use MLP and
            RandomForest by default.

        --hcp_autoreclean_vote_threshold (int):
            A decision threshold for determing reclassifications,
            should be less than to equal to the number of models to use.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folder inside the same sessions's root hcp folder.

    Notes:
        hcp_apply_auto_reclean parameter mapping:

            ================================== =======================
            QuNex parameter                    HCPpipelines parameter
            ================================== =======================
            ``hcp_icafix_bolds``               ``fmri-names``
            ``hcp_icafix_bolds``               ``mrfix-concat-name``
            ``hcp_icafix_highpass``            ``bandpass``
            ``hcp_bold_res``                   ``fmri-resolution``
            ``hcp_lowresmesh``                 ``low-res-mesh``
            ``hcp_grayordinatesres``           ``grayordinatesres``
            ``hcp_bold_smoothFWHM``            ``smoothingFWHM``
            ``hcp_autoreclean_model_folder``   ``model-folder``
            ``hcp_autoreclean_model_to_use``   ``model-to-use``
            ``hcp_autoreclean_vote_threshold`` ``vote-threshold``
            ``hcp_matlab_mode``                ``matlabrunmode``
            ================================== =======================

    Examples:
        ::

            qunex hcp_apply_auto_reclean \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions

        ::

            qunex hcp_apply_auto_reclean \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_icafix_bolds="GROUP_1:BOLD_1,BOLD_2|GROUP_2:BOLD_3,BOLD_4" \\
                --hcp_matlab_mode="interpreted"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP ApplyAutoRecleanPipeline pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, "hcp_apply_auto_reclean")
        doHCPOptionsCheck(options, "hcp_apply_auto_reclean")
        hcp = getHCPPaths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report["boldskipped"], r = pc.use_or_skip_bold(sinfo, options, r)
        _build_skipped_report(report, bskip, options)

        # --- Parse icafix_bolds
        single_fix, icafix_bolds, icafix_groups, pars_ok, r = parse_icafix_bolds(
            options, bolds, r
        )

        # --- Multi threading
        if single_fix:
            parelements = max(1, min(options["parelements"], len(icafix_bolds)))
            reclean_elements = icafix_bolds
        else:
            parelements = max(1, min(options["parelements"], len(icafix_groups)))
            reclean_elements = icafix_groups

        r += "\n\n%s %d ApplyAutoReclean elements in parallel" % (
            pc.action("Processing", options["run"]),
            parelements,
        )

        # matlab run mode, compiled=0, interpreted=1, octave=2
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
                pars_ok = False
        else:
            if options["hcp_matlab_mode"] == "compiled":
                os.environ["FSL_FIX_MATLAB_MODE"] = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                os.environ["FSL_FIX_MATLAB_MODE"] = "1"
            elif options["hcp_matlab_mode"] == "octave":
                os.environ["FSL_FIX_MATLAB_MODE"] = "2"
            else:
                r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                pars_ok = False

        if not pars_ok:
            raise ge.CommandFailed(
                "hcp_apply_auto_reclean", "... invalid input parameters!"
            )

        # --- Execute
        # create a multiprocessing Pool
        ppe = ProcessPoolExecutor(parelements)
        # process
        f = partial(
            execute_hcp_apply_auto_reclean,
            sinfo,
            options,
            overwrite,
            hcp,
            run,
            single_fix,
        )
        results = ppe.map(f, reclean_elements)

        # merge r and report
        for result in results:
            r += result["r"]
            temp_report = result["report"]
            report["done"] += temp_report["done"]
            report["failed"] += temp_report["failed"]
            report["incomplete"] += temp_report["incomplete"]
            report["ready"] += temp_report["ready"]
            report["not ready"] += temp_report["not ready"]
            report["skipped"] += temp_report["skipped"]

        # report
        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP ApplyAytoReclean: " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except ge.CommandFailed as e:
        r += "\n\nERROR in completing %s:\n     %s\n" % (
            e.function,
            "\n     ".join(e.report),
        )
        report = (sinfo["id"], "HCP ApplyAytoReclean failed")
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        report = (sinfo["id"], "HCP ApplyAytoReclean failed")
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report = (sinfo["id"], "HCP ApplyAytoReclean failed")

    r += (
        "\n\nHCP ApplyAytoReclean %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, report)


def execute_hcp_apply_auto_reclean(sinfo, options, overwrite, hcp, run, single_fix, re):
    """Execute HCP Apply Auto Reclean"""
    if single_fix:
        groupname = None
        bolds = [re]
    else:
        # get group data
        groupname = re["name"]
        bolds = re["bolds"]

    # prepare return variables
    r = ""
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        r += "\n\n------------------------------------------------------------"
        r += "\n---> %s group %s" % (pc.action("Processing", options["run"]), groupname)
        groupok = True

        # --- check for bold images and prepare images parameter
        boldimgs = ""

        # check if files for all bolds exist
        for boldinfo in bolds:
            # set ok to true for now
            boldok = True

            _, boldtarget, _ = pc.get_bold_names(boldinfo, options)
            boldimg = os.path.join(
                hcp["hcp_nonlin"], "Results", boldtarget, "%s" % (boldtarget)
            )
            r, boldok = pc.checkForFile2(
                r,
                "%s.nii.gz" % boldimg,
                "\n     ... bold image %s present" % boldtarget,
                "\n     ... ERROR: bold image [%s.nii.gz] missing!" % boldimg,
                status=boldok,
            )

            if not boldok:
                run = False
                break
            else:
                # add @ separator
                if boldimgs != "":
                    boldimgs = boldimgs + "@"

                boldimgs = boldimgs + boldtarget

        # subject/session
        subject = sinfo["id"] + options["hcp_suffix"]

        # highpass
        if single_fix:
            highpass = (
                2000
                if options["hcp_icafix_highpass"] is None
                else options["hcp_icafix_highpass"]
            )
        else:
            highpass = (
                0
                if options["hcp_icafix_highpass"] is None
                else options["hcp_icafix_highpass"]
            )

        # matlab run mode, compiled=0, interpreted=1, octave=2
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                r += "\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n"
                run = False
        else:
            if options["hcp_matlab_mode"] == "compiled":
                os.environ["FSL_FIX_MATLAB_MODE"] = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                os.environ["FSL_FIX_MATLAB_MODE"] = "1"
            elif options["hcp_matlab_mode"] == "octave":
                os.environ["FSL_FIX_MATLAB_MODE"] = "2"
            else:
                r += "\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n"
                run = False

        matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]

        comm = (
            '%(script)s \
            --study-folder="%(studyfolder)s" \
            --subject="%(subject)s" \
            --fmri-names="%(boldimgs)s" \
            --fix-high-pass="%(highpass)s" \
            --fmrires="%(fmrires)s" \
            --low-res="%(low_res)s" \
            --grayordinatesres="%(grayordinatesres)s" \
            --smoothingFWHM="%(smoothingFWHM)s" \
            --matlab-run-mode="%(matlabrunmode)s"'
            % {
                "script": os.path.join(
                    hcp["hcp_base"], "ICAFIX", "ApplyAutoRecleanPipeline.sh"
                ),
                "studyfolder": sinfo["hcp"],
                "subject": subject,
                "boldimgs": boldimgs,
                "highpass": highpass,
                "fmrires": options["hcp_bold_res"],
                "low_res": options["hcp_lowresmesh"],
                "grayordinatesres": options["hcp_grayordinatesres"],
                "smoothingFWHM": options["hcp_bold_smoothFWHM"],
                "matlabrunmode": matlabrunmode,
            }
        )

        # optional parameters
        if groupname is not None:
            comm += '             --mrfix-concat-name="%s"' % groupname

        if options["hcp_autoreclean_model_folder"] is not None:
            comm += (
                '             --model-folder="%s"'
                % options["hcp_autoreclean_model_folder"]
            )

        if options["hcp_autoreclean_model_to_use"] is not None:
            comm += '             --model-to-use="%s"' % options[
                "hcp_autoreclean_model_to_use"
            ].replace(",", "@")

        if options["hcp_autoreclean_vote_threshold"] is not None:
            comm += (
                '             --vote-threshold="%s"'
                % options["hcp_autoreclean_vote_threshold"]
            )

        # -- Report command
        if boldok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Run
        if run and groupok:
            if options["run"] == "run":
                r, endlog, _, failed = pc.runExternalForFile(
                    None,
                    comm,
                    "Running ApplyAutoRecleanPipeline",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], groupname],
                    fullTest=None,
                    shell=True,
                    r=r,
                )

                if failed:
                    report["failed"].append(groupname)
                else:
                    report["done"].append(groupname)

        else:
            report["not ready"].append(groupname)
            if options["run"] == "run":
                r += "\n---> ERROR: something missing, skipping this group!"
            else:
                r += "\n---> ERROR: something missing, this group would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of group %s with error:\n" % (
            groupname
        )
        r += str(errormessage)
        report["failed"].append(groupname)
    except:
        r += "\n --- Failed during processing of group %s with error:\n %s\n" % (
            groupname,
            traceback.format_exc(),
        )
        report["failed"].append(groupname)

    return {"r": r, "report": report}


def map_hcp_data(sinfo, options, overwrite=False, thread=0):
    """
    ``map_hcp_data [... processing options]``

    Maps the results of the HCP preprocessing:

    * T1w.nii.gz
        └-> images/structural/T1w.nii.gz

    * aparc+aseg.nii.gz
        └-> images/segmentation/freesurfer/mri/aparc+aseg_t1.nii.gz

        └-> images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz
        (2mm iso downsampled version)

    * fsaverage_LR32k/*
        └-> images/segmentation/hcp/fsaverage_LR32k

    * BOLD_[N][hcp_nifti_tail].nii.gz
        └-> images/functional/[boldname][N][qx_nifti_tail].nii.gz

    * BOLD_[N][hcp_cifti_tail].dtseries.nii
        └-> images/functional/[boldname][N][qx_cifti_tail].dtseries.nii

    * Movement_Regressors.txt
        └-> images/functional/movement/[boldname][N]_mov.dat

    See Use section for details.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --hcp_bold_variant (str, default ''):
            Optional variant of HCP BOLD preprocessing. If specified, the
            results will be copied/linked from `Results<hcp_bold_variant>`.

        --hcp_nifti_tail (str, default ''):
            The tail to use for the volume files to map from the HCP file
            structure.

        --hcp_cifti_tail (str, default ''):
            The tail to use for the surface files to map from the HCP file
            structure.

        --bolds (str, default 'all'):
            Which bold images (as they are specified in the batch.txt file) to
            copy over. It can be a single type (e.g. 'task'), a pipe separated
            list (e.g. 'WM|Control|rest') or 'all' to copy all.

        --boldname (str, default 'bold'):
            The prefix for the fMRI files in the images folder.

        --img_suffix (str, default ''):
            Specifies a suffix for 'images' folder to enable support for
            multiple parallel workflows. Empty if not used.

        --qx_nifti_tail (str, default detailed below):
            The tail to use for the mapped volume files in the QuNex file
            structure. If not specified or if set to 'None', the value of
            hcp_nifti_tail will be used.

        --qx_cifti_tail (str, default detailed below):
            The tail to use for the mapped cifti files in the QuNex file
            structure. If not specified or if set to 'None', the value of
            hcp_cifti_tail will be used.

        --bold_variant (str, default ''):
            Optional variant for functional images. If specified, functional
            images will be mapped into `functional<bold_variant>` folder.

        --additional_bolds (str, default ''):
            A comma separated list of additional bolds to map. Use this
            parameter to map HCP results/derivatives that are not part of the
            session.txt file (for example concatenated rest denoised BOLDs
            after runnning hcp_msmall).

    Notes:
        The parameters can be specified in command call or session.txt file. If
        possible, the files are not copied but rather hard links are created to
        save space. If hard links cannot be created, the files are copied.

        Specific attention needs to be paid to the use of `hcp_nifti_tail`,
        `hcp_cifti_tail`, `hcp_suffix`, and `hcp_bold_variant` that relate to
        file location and naming within the HCP folder structure and
        `qx_nifti_tail`, `qx_cifti_tail`, `img_suffix`, and `bold_variant` that
        relate to file and folder naming within the QuNex folder structure.

        `hcp_suffix` parameter enables the use of a parallel HCP minimal
        processing stream. To enable the same separation in the QuNex folder
        structure, `img_suffix` parameter has to be set. In this case HCP data
        will be mapped to `<sessionsfolder>/<session id>/images<img_suffix>`
        folder instead of the default `<sessionsfolder>/<session id>/images`
        folder.

        Similarly, if separate variants of bold image processing were run, and
        the results were stored in `MNINonLinear/Results<hcp_bold_variant>`,
        the `hcp_bold_variant` parameter needs to be set to map the data from
        the correct location. `bold_variant` parameter on the other hand
        enables continued parallel processing of bold data in the QuNex folder
        structure by mapping bold data to `functional<bold_variant>` folder
        instead of the default `functional` folder.

        Based on HCP minimal preprocessing choices, both CIFTI and NIfTI volume
        files can be marked using different tails. E.g. CIFT files are marked
        with an `_Atlas` tail, NIfTI files are marked with `_hp2000_clean` tail
        after employing ICAFix procedure. When mapping the data, it is
        important that the correct files are mapped. The correct tails for
        NIfTI volume, and CIFTI files are specified using the `hcp_nifti_tail`
        and `hcp_cifti_tail` parameters. When the data is mapped into QuNex
        folder structure the tails to be used for NIfTI and CIFTI data are
        specified with `qx_nifti_tail` and `qx_cifti_tail` parameters,
        respectively. If the `qx_*_tail` parameters are not provided
        explicitly, the values specified in the `hcp_*_tail` parameters will be
        used.

        Use:
            map_hcp_data maps the results of the HCP preprocessing (in
            MNINonLinear) to the `<sessionsfolder>/<session
            id>/images<img_suffix>` folder structure. Specifically, it copies
            the files and folders:

            * T1w.nii.gz
                └-> images/structural/T1w.nii.gz

            * aparc+aseg.nii.gz
                └-> images/segmentation/freesurfer/mri/aparc+aseg_t1.nii.gz

                └-> images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz
                (2mm iso downsampled version)

            * fsaverage_LR32k/*
                └-> images/segmentation/hcp/fsaverage_LR32k

            * BOLD_[N][hcp_nifti_tail].nii.gz
                └-> images/functional/[boldname][N][qx_nifti_tail].nii.gz

            * BOLD_[N][hcp_cifti_tail].dtseries.nii
                └-> images/functional/[boldname][N][qx_cifti_tail].dtseries.nii

            * Movement_Regressors.txt
                └-> images/functional/movement/[boldname][N]_mov.dat

    Examples:

        A basic mapping example::

            qunex map_hcp_data \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --hcp_cifti_tail=_Atlas \\
                --bolds=all

        Also map concatenated bolds and rest bolds from hcp_msmall::

            qunex map_hcp_data \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --hcp_cifti_tail=_Atlas \\
                --additional_bolds=fMRI_CONCAT_ALL

        Run using absolute paths with scheduler::

            qunex map_hcp_data \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --parsessions="4" \\
                --hcp_cifti_tail="_Atlas" \\
                --overwrite="yes" \\
                --scheduler="SLURM,time=24:00:00,cpus-per-task=2,mem-per-cpu=1250,partition=day"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\nMapping HCP data ... \n"
    r += (
        "\n   The command will map the results of the HCP preprocessing from sessions's hcp\n   to sessions's images folder. It will map the T1 structural image, aparc+aseg \n   segmentation in both high resolution as well as one downsampled to the \n   resolution of BOLD images. It will map the 32k surface mapping data, BOLD \n   data in volume and cifti representation, and movement correction parameters. \n\n   Please note: when mapping the BOLD data, two parameters are key: \n\n   --bolds parameter defines which BOLD files are mapped based on their\n     specification in batch.txt file. Please see documentation for formatting. \n        If the parameter is not specified the default value is 'all' and all BOLD\n        files will be mapped. \n\n   --hcp_nifti_tail and --hcp_cifti_tail specifiy which kind of the nifti and cifti files will be copied over. \n     The tail is added after the boldname[N] start. If the parameters are not specified \n     explicitly the default is ''.\n\n   Based on settings:\n\n    * %s BOLD files will be copied\n    * '%s' nifti tail will be used\n    * '%s' cifti tail will be used."
        % (
            ", ".join(options["bolds"].split("|")),
            options["hcp_nifti_tail"],
            options["hcp_cifti_tail"],
        )
    )
    if any([options["hcp_suffix"], options["img_suffix"]]):
        r += (
            "\n   Based on --hcp_suffix and --img_suffix parameters, the files will be mapped from hcp/%s%s/MNINonLinear to 'images%s' folder!"
            % (sinfo["id"], options["hcp_suffix"], options["img_suffix"])
        )
    if any([options["hcp_bold_variant"], options["bold_variant"]]):
        r += (
            "\n   Based on --hcp_bold_variant and --bold_variant parameters, the files will be mapped from MNINonLinear/Results%s to 'images%s/functional%s folder!"
            % (
                options["hcp_bold_variant"],
                options["img_suffix"],
                options["bold_variant"],
            )
        )
    r += "\n\n........................................................"

    # --- sanity checks
    if "sessionsfolder" not in options:
        r += "\nERROR: sessionsfolder not specified in options, cannot map HCP data!"
        rstatus = f"Mapping {sinfo['id']} failed, check your input parameters!"
        failed = 1
        return (r, (sinfo["id"], rstatus, failed))

    session_path = os.path.join(options["sessionsfolder"], sinfo["id"])
    if not os.path.exists(session_path):
        r += f"\nERROR: session {sinfo['id']} does not exists at {session_path}!"
        rstatus = f"Mapping {sinfo['id']} failed, check your input parameters and study folder structure!"
        failed = 1
        return (r, (sinfo["session"], rstatus, failed))

    # --- file/dir structure
    f = pc.getFileNames(sinfo, options)
    d = pc.getSessionFolders(sinfo, options)

    if "hcp" not in d:
        r += f"\nERROR: something went wrong, mapping was unable to get the HCP folder for session {sinfo['id']}!"
        rstatus = f"Mapping {sinfo['id']} failed, check your input parameters and data!"
        failed = 1

        r += "\n\nsession information:\n"
        r += pprint.pformat(sinfo)

        r += "\n\ndirectory structure:\n"
        r += pprint.pformat(d)

        return (r, (sinfo["session"], rstatus, failed))

    if not os.path.exists(d["hcp"]):
        r += f"\nERROR: HCP folder for session {sinfo['id']} does not exists at {d['hcp']}!"
        rstatus = f"Mapping {sinfo['id']} failed, check your input parameters and study folder structure!"
        failed = 1
        return (r, (sinfo["session"], rstatus, failed))

    #    MNINonLinear/Results/<boldname>/<boldname>.nii.gz -- volume
    #    MNINonLinear/Results/<boldname>/<boldname>_Atlas.dtseries.nii -- cifti
    #    MNINonLinear/Results/<boldname>/Movement_Regressors.txt -- movement
    #    MNINonLinear/T1w.nii.gz -- atlas T1 hires
    #    MNINonLinear/aparc+aseg.nii.gz -- FS hires segmentation

    # ------------------------------------------------------------------------------------------------------------
    #                                                                                      map T1 and segmentation
    report = {}
    failed = 0

    if "hcp" not in d or "s_images" not in d:
        r += f"\nERROR: found issues with session {sinfo['id']}\n...................................\n{traceback.format_exc()}...................................\n"
        failed += 1
        rstatus = f"Mapping {sinfo['id']} failed, check your batch file and session processing!"
    else:
        r += "\n\nSource folder: " + d["hcp"]
        r += "\nTarget folder: " + d["s_images"]

        r += "\n\nStructural data: ..."
        status = True

        if os.path.exists(f["t1"]) and not overwrite:
            r += "\n ... T1 ready"
            report["T1"] = "present"
        else:
            status, r = gc.link_or_copy(
                os.path.join(d["hcp"], "MNINonLinear", "T1w.nii.gz"),
                f["t1"],
                r,
                status,
                "T1",
            )
            report["T1"] = "copied"

        if os.path.exists(f["fs_aparc_t1"]) and not overwrite:
            r += "\n ... highres aseg+aparc ready"
            report["hires aseg+aparc"] = "present"
        else:
            status, r = gc.link_or_copy(
                os.path.join(d["hcp"], "MNINonLinear", "aparc+aseg.nii.gz"),
                f["fs_aparc_t1"],
                r,
                status,
                "highres aseg+aparc",
            )
            report["hires aseg+aparc"] = "copied"

        if os.path.exists(f["fs_aparc_bold"]) and not overwrite:
            r += "\n ... lowres aseg+aparc ready"
            report["lores aseg+aparc"] = "present"
        else:
            if os.path.exists(f["fs_aparc_bold"]):
                os.remove(f["fs_aparc_bold"])
            if os.path.exists(
                os.path.join(d["hcp"], "MNINonLinear", "T1w_restore.2.nii.gz")
            ) and os.path.exists(f["fs_aparc_t1"]):
                # prepare logtags
                if options["logtag"] != "":
                    options["logtag"] += "_"
                logtags = options["logtag"] + "%s-flirt_%s" % (
                    options["command_ran"],
                    sinfo["id"],
                )

                _, endlog, _, failedcom = pc.runExternalForFile(
                    f["fs_aparc_bold"],
                    f"flirt -interp nearestneighbour -ref {os.path.join(d['hcp'], 'MNINonLinear', 'T1w_restore.2.nii.gz')} -in {f['fs_aparc_t1']} -out {f['fs_aparc_bold']} -applyisoxfm {options['hcp_bold_res']}",
                    " ... resampling t1 cortical segmentation (%s) to bold space (%s)"
                    % (
                        os.path.basename(f["fs_aparc_t1"]),
                        os.path.basename(f["fs_aparc_bold"]),
                    ),
                    overwrite=overwrite,
                    remove=options["log"] == "remove",
                    logfolder=options["comlogs"],
                    logtags=logtags,
                    shell=True,
                )
                if failedcom:
                    report["lores aseg+aparc"] = "failed"
                    failed += 1
                else:
                    report["lores aseg+aparc"] = "generated"
            else:
                r += "\n ... ERROR: could not generate downsampled aseg+aparc, files missing!"
                report["lores aseg+aparc"] = "failed"
                status = False
                failed += 1

        report["surface"] = "ok"
        if os.path.exists(os.path.join(d["hcp"], "MNINonLinear", "fsaverage_LR32k")):
            r += "\n ... processing surface files"
            sfiles = glob.glob(
                os.path.join(d["hcp"], "MNINonLinear", "fsaverage_LR32k", "*.*")
            )
            npre, ncp = 0, 0
            sid = ""
            if len(sfiles):
                sid = os.path.basename(sfiles[0]).split(".")[0]
            for sfile in sfiles:
                tfile = os.path.join(
                    d["s_s32k"], ".".join(os.path.basename(sfile).split(".")[1:])
                )
                if os.path.exists(tfile) and not overwrite:
                    npre += 1
                else:
                    if ".spec" in tfile:
                        file = open(sfile, "r")
                        s = file.read()
                        s = s.replace(sid + ".", "")
                        tf = open(tfile, "w")
                        print(s, file=tf)
                        tf.close()
                        r += "\n     -> updated .spec file [%s]" % (sid)
                        ncp += 1
                        continue
                    if gc.link_or_copy(sfile, tfile):
                        ncp += 1
                    else:
                        r += "\n     -> ERROR: could not map or copy %s" % (sfile)
                        report["surface"] = "error"
                        failed += 1
            if npre:
                r += "\n     -> %d files already copied" % (npre)
            if ncp:
                r += "\n     -> copied %d surface files" % (ncp)
        else:
            r += "\n ... ERROR: missing folder: %s!" % (
                os.path.join(d["hcp"], "MNINonLinear", "fsaverage_LR32k")
            )
            status = False
            report["surface"] = "error"
            failed += 1

        # ------------------------------------------------------------------------------------------------------------
        #                                                                                          map functional data
        r += (
            "\n\nFunctional data: \n ... mapping %s BOLD files\n ... mapping '%s' hcp nifti tail to '%s' qx nifti tail\n ... mapping '%s' hcp cifti tail to '%s' qx cifti tail\n"
            % (
                ", ".join(options["bolds"].split("|")),
                options["hcp_nifti_tail"],
                options["qx_nifti_tail"],
                options["hcp_cifti_tail"],
                options["qx_cifti_tail"],
            )
        )

        report["boldok"] = 0
        report["boldfail"] = 0
        report["boldskipped"] = 0

        bolds, skipped, report["boldskipped"], r = pc.use_or_skip_bold(
            sinfo, options, r
        )

        # add additional BOLDS
        if options["additional_bolds"] is not None:
            r += f"\n\nAdditional BOLD images to map: {options['additional_bolds']}\n"
            additional_bolds = options["additional_bolds"].split(",")
            boldnum = len(bolds) + 1
            for ab in additional_bolds:
                bolds.append(
                    {
                        "bold": ab,
                        "filename": ab,
                        "bold_number": boldnum,
                        "name": ab,
                        "task": "additional_bold",
                    }
                )
                boldnum += 1

        for boldinfo in bolds:
            r += "\n ... " + boldinfo["name"]

            # --- filenames
            if boldinfo["task"] != "additional_bold":
                f.update(pc.getBOLDFileNames(sinfo, boldinfo["name"], options))
            else:
                d = pc.getSessionFolders(sinfo, options)

                f["bold_qx_vol"] = os.path.join(
                    d["s_bold"],
                    boldinfo["name"] + options["qx_nifti_tail"] + ".nii.gz",
                )
                f["bold_qx_dts"] = os.path.join(
                    d["s_bold"],
                    boldinfo["name"] + options["qx_cifti_tail"] + ".dtseries.nii",
                )
                f["bold_mov"] = os.path.join(
                    d["s_bold_mov"], boldinfo["name"] + "_mov.dat"
                )

            status = True
            hcp_bold_name = ""

            try:
                # -- get source bold name
                if "filename" in boldinfo and options["hcp_filename"] == "userdefined":
                    hcp_bold_name = boldinfo["filename"]
                elif "bold" in boldinfo:
                    hcp_bold_name = boldinfo["bold"]
                else:
                    hcp_bold_name = "%s%d" % (
                        options["hcp_bold_prefix"],
                        boldinfo["bold_number"],
                    )

                # -- check if present and map
                hcp_bold_path = os.path.join(
                    d["hcp"],
                    "MNINonLinear",
                    "Results" + options["hcp_bold_variant"],
                    hcp_bold_name,
                )

                if not os.path.exists(hcp_bold_path):
                    r += "\n     ... ERROR: source folder does not exist [%s]!" % (
                        hcp_bold_path
                    )
                    status = False

                else:
                    if os.path.exists(f["bold_qx_vol"]) and not overwrite:
                        r += "\n     ... volume image ready"
                    elif boldinfo["task"] == "additional_bold" and not os.path.exists(
                        hcp_bold_path
                    ):
                        r += f"\n     ... WARNING: additional bold source does not exist: {f['bold_vol']}"
                    else:
                        status, r = gc.link_or_copy(
                            os.path.join(
                                hcp_bold_path,
                                hcp_bold_name + options["hcp_nifti_tail"] + ".nii.gz",
                            ),
                            f["bold_qx_vol"],
                            r,
                            status,
                            "volume image",
                            "\n     ... ",
                        )

                    if os.path.exists(f["bold_qx_dts"]) and not overwrite:
                        r += "\n     ... grayordinate image ready"
                    else:
                        status, r = gc.link_or_copy(
                            os.path.join(
                                hcp_bold_path,
                                hcp_bold_name
                                + options["hcp_cifti_tail"]
                                + ".dtseries.nii",
                            ),
                            f["bold_qx_dts"],
                            r,
                            status,
                            "grayordinate image",
                            "\n     ... ",
                        )

                    if os.path.exists(f["bold_mov"]) and not overwrite:
                        r += "\n     ... movement data ready"
                    else:
                        movement_regressors_icafix = f"Movement_Regressors{options['hcp_nifti_tail'].replace('_Atlas', '')}.txt"
                        movement_regressors = None
                        if os.path.exists(
                            os.path.join(hcp_bold_path, movement_regressors_icafix)
                        ):
                            movement_regressors = movement_regressors_icafix
                        else:
                            movement_regressors_volume = "Movement_Regressors.txt"
                            if os.path.exists(
                                os.path.join(hcp_bold_path, movement_regressors_volume)
                            ):
                                movement_regressors = movement_regressors_volume
                                r += "\n     ... WARNING: using movement regressors from jcp_fmri_volume, hcp_icafix movement regressors not found"
                        if movement_regressors:
                            mdata = [
                                line.strip().split()
                                for line in open(
                                    os.path.join(hcp_bold_path, movement_regressors)
                                )
                            ]
                            mfile = open(f["bold_mov"], "w")
                            gc.print_qunex_header(file=mfile)
                            print("#", file=mfile)
                            print(
                                "#frame     dx(mm)     dy(mm)     dz(mm)     X(deg)     Y(deg)     Z(deg)",
                                file=mfile,
                            )
                            c = 0
                            for mline in mdata:
                                if len(mline) >= 6:
                                    c += 1
                                    mline = "%6d   %s" % (c, "   ".join(mline[0:6]))
                                    print(mline.replace(" -", "-"), file=mfile)
                            mfile.close()
                            r += "\n     ... movement data prepared"
                        elif boldinfo["task"] == "additional_bold":
                            r += (
                                "\n     ... WARNING: could not prepare movement data for the additional bold, source does not exist: [%s or %s]"
                                % (
                                    os.path.join(
                                        hcp_bold_path, movement_regressors_icafix
                                    ),
                                    os.path.join(
                                        hcp_bold_path, movement_regressors_volume
                                    ),
                                )
                            )
                        else:
                            r += (
                                "\n     ... ERROR: could not prepare movement data, source does not exist: [%s or %s]"
                                % (
                                    os.path.join(
                                        hcp_bold_path, movement_regressors_icafix
                                    ),
                                    os.path.join(
                                        hcp_bold_path, movement_regressors_volume
                                    ),
                                )
                            )
                            failed += 1
                            status = False

                if status:
                    r += "\n     ---> Data ready!\n"
                    report["boldok"] += 1
                else:
                    r += "\n     ---> ERROR: Data missing, please check source!\n"
                    report["boldfail"] += 1
                    failed += 1

            except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
                r = str(errormessage)
                report["boldfail"] += 1
                failed += 1
            except:
                r += (
                    "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
                    % (traceback.format_exc())
                )
                time.sleep(3)
                failed += 1

        if len(skipped) > 0:
            r += (
                "\nThe following BOLD images were not mapped as they were not specified in\n'--bolds=\"%s\"':\n"
                % (options["bolds"])
            )
            for boldinfo in skipped:
                if "filename" in boldinfo and options["hcp_filename"] == "userdefined":
                    r += "\n ... %s [task: '%s']" % (
                        boldinfo["filename"],
                        boldinfo["task"],
                    )
                else:
                    r += "\n ... %s [task: '%s']" % (boldinfo["name"], boldinfo["task"])

        r += (
            "\n\nHCP data mapping completed on %s\n------------------------------------------------------------\n"
            % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        )
        rstatus = (
            "T1: %(T1)s, aseg+aparc hires: %(hires aseg+aparc)s lores: %(lores aseg+aparc)s, surface: %(surface)s, bolds ok: %(boldok)d, bolds failed: %(boldfail)d, bolds skipped: %(boldskipped)d"
            % (report)
        )

    # print r
    return (r, (sinfo["id"], rstatus, failed))


def hcp_task_fmri_analysis(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_task_fmri_analysis [... processing options]``

    Runs the Diffusion step of HCP Pipeline (TaskfMRIAnalysis.sh).

    Warning:
        The requirement for this command is a successful completion of the
        minimal HCP preprocessing pipeline.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the session's information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_task_lvl1tasks (str, default ''):
            List of task fMRI scan names, which are the prefixes of the time
            series filename for the TaskName task. Multiple task fMRI scan
            names should be provided as a comma separated list.

        --hcp_task_lvl1fsfs (str, default ''):
            List of design names, which are the prefixes of the fsf filenames
            for each scan run. Should contain same number of design files as
            time series images in --hcp_task_lvl1tasks option (N-th design will
            be used for N-th time series image). Provide a comma separated list
            of design names. If no value is passed to --hcp_task_lvl1fsfs, the
            value will be set to --hcp_task_lvl1tasks.

        --hcp_task_lvl2task (str, default NONE):
            Name of Level2 subdirectory in which all Level2 feat directories are
            written for TaskName.

        --hcp_task_lvl2fsf (str, default ''):
            Prefix of design.fsf filename for the Level2 analysis for TaskName.
            If no value is passed to --hcp_task_lvl2fsf, the value will be set
            to the same list passed to --hcp_task_lvl2task.

        --hcp_task_summaryname (str, default 'NONE'):
            Naming convention for single-subject summary directory. Mandatory
            when running Level1 analysis only, and should match naming of
            Level2 summary directories. Default when running Level2 analysis is
            derived from --hcp_task_lvl2task and --hcp_task_lvl2fsf options
            'tfMRI_TaskName/DesignName_TaskName'.

        --hcp_task_confound (str, default 'NONE'):
            Confound matrix text filename (e.g., output of fsl_motion_outliers).
            Assumes file is in <SubjectID>/MNINonLinear/Results/<ScanName>.

        --hcp_bold_smoothFWHM (int, default 2):
            Smoothing FWHM that matches what was used in the fMRISurface
            pipeline.

        --hcp_bold_final_smoothFWHM (int, default 2):
            Value (in mm FWHM) of total desired smoothing, reached by
            calculating the additional smoothing required and applying that
            additional amount to data previously smoothed in fMRISurface.
            Default=2, which is no additional smoothing above HCP minimal
            preprocessing pipelines outputs.

        --hcp_task_highpass (int, default 200):
            Apply additional highpass filter (in seconds) to time series and
            task design. This is above and beyond temporal filter applied
            during preprocessing. To apply no additional filtering, set to
            'NONE'.

        --hcp_task_lowpass (str, default 'NONE'):
            Apply additional lowpass filter (in seconds) to time series and task
            design. This is above and beyond temporal filter applied during
            preprocessing. Low pass filter is generally not advised for Task
            fMRI analyses.

        --hcp_task_procstring (str, default 'NONE'):
            String value in filename of time series image, specifying the
            additional processing that was previously applied (e.g.,
            FIX-cleaned data with 'hp2000_clean' in filename).

        --hcp_regname (str, default 'MSMSulc'):
            Name of surface registration technique.

        --hcp_grayordinatesres (int, default 2):
            Value (in mm) that matches value in 'Atlas_ROIs' filename.

        --hcp_lowresmesh (int, default 32):
            Value (in mm) that matches surface resolution for fMRI data.

        --hcp_task_vba (flag, optional):
            A flag for using VBA. Only use this flag if you want unconstrained
            volumetric blurring of your data, otherwise set to NO for faster,
            less biased, and more senstive processing (grayordinates results do
            not use unconstrained volumetric blurring and are always produced).
            This flag is not set by defult.

        --hcp_task_parcellation (str, default 'NONE'):
            Name of parcellation scheme to conduct parcellated analysis. Default
            setting is NONE, which will perform dense analysis instead.
            Non-greyordinates parcellations are not supported because they are
            not valid for cerebral cortex. Parcellation supersedes smoothing
            (i.e. no smoothing is done).

        --hcp_task_parcellation_file (str, default 'NONE'):
            Absolute path to the parcellation dlabel file.

    Output files:
        The results of this step will be populated in the MNINonLinear
        folder inside the same sessions's root hcp folder.

    Notes:
        Mapping of QuNex parameters onto HCP Pipelines parameters:
            Below is a detailed specification about how QuNex parameters are
            mapped onto the HCP Pipelines parameters.

            ============================== ======================
            QuNex parameter                HCPpipelines parameter
            ============================== ======================
            ``hcp_task_lvl1task``          ``lvl1tasks``
            ``hcp_task_lvl1fsfs``          ``lvl1fsfs``
            ``hcp_task_lvl2task``          ``lvl2task``
            ``hcp_task_lvl2fsf``           ``lvl2fsf``
            ``hcp_task_confound``          ``confound``
            ``hcp_bold_smoothFWHM``        ``origsmoothingFWHM``
            ``hcp_bold_final_smoothFWHM``  ``finalsmoothingFWHM``
            ``hcp_task_highpass``          ``highpassfilter``
            ``hcp_task_lowpass``           ``lowpassfilter``
            ``hcp_task_procstring``        ``procstring``
            ``hcp_regname``                ``regname``
            ``hcp_grayordinatesres``       ``grayordinatesres``
            ``hcp_lowresmesh``             ``lowresmesh``
            ``hcp_task_vba``               ``vba``
            ``hcp_task_parcellation``      ``parcellation``
            ``hcp_task_parcellation_file`` ``parcellationfile``
            ============================== ======================

    Examples:
        First level HCP TaskfMRIanalysis::

            qunex hcp_task_fmri_analysis \\
                --sessionsfolder="<study_path>/sessions" \\
                --batchfile="<study_path>/processing/batch.txt" \\
                --hcp_task_lvl1tasks="tfMRI_GUESSING_PA" \\
                --hcp_task_summaryname="tfMRI_GUESSING/tfMRI_GUESSING"

        Second level HCP TaskfMRIanalysis::

            qunex hcp_task_fmri_analysis \\
                --sessionsfolder="<study_path>/sessions" \\
                --batchfile="<study_path>/processing/batch.txt" \\
                --hcp_task_lvl1tasks="tfMRI_GUESSING_AP@tfMRI_GUESSING_PA" \\
                --hcp_task_lvl2task="tfMRI_GUESSING"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s HCP fMRI task analysis pipeline [%s] ..." % (
        pc.action("Running", options["run"]),
        options["hcp_processing_mode"],
    )

    run = True
    report = "Error"

    try:
        pc.doOptionsCheck(options, sinfo, "hcp_task_fmri_analysis")
        doHCPOptionsCheck(options, "hcp_task_fmri_analysis")
        hcp = getHCPPaths(sinfo, options)

        if "hcp" not in sinfo:
            r += (
                "\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"])
            )
            run = False

        # parse input parameters
        # hcp_task_lvl1tasks
        lvl1tasks = ""
        if options["hcp_task_lvl1tasks"] is not None:
            lvl1tasks = options["hcp_task_lvl1tasks"].replace(",", "@")
        else:
            r += "\n---> ERROR: hcp_task_lvl1tasks parameter is not provided"
            run = False

        # --- build the command
        if run:
            comm = (
                '%(script)s \
                --study-folder="%(studyfolder)s" \
                --subject="%(subject)s" \
                --lvl1tasks="%(lvl1tasks)s" '
                % {
                    "script": os.path.join(
                        hcp["hcp_base"], "TaskfMRIAnalysis", "TaskfMRIAnalysis.sh"
                    ),
                    "studyfolder": sinfo["hcp"],
                    "subject": sinfo["id"] + options["hcp_suffix"],
                    "lvl1tasks": lvl1tasks,
                }
            )

            # optional parameters
            # hcp_task_lvl1fsfs
            if options["hcp_task_lvl1fsfs"] is not None:
                lvl1fsfs = options["hcp_task_lvl1fsfs"].replace(",", "@")
                if len(lvl1fsfs.split(",")) != len(lvl1tasks.split(",")):
                    r += "\n---> ERROR: mismatch in the length of hcp_task_lvl1tasks and hcp_task_lvl1fsfs"
                    run = False

                comm += '                --lvl1fsfs="%s"' % lvl1fsfs

            # hcp_task_lvl2task
            if options["hcp_task_lvl2task"] is not None:
                comm += '                --lvl2task="%s"' % options["hcp_task_lvl2task"]

                # hcp_task_lvl2fsf
                if options["hcp_task_lvl2fsf"] is not None:
                    comm += (
                        '                --lvl2fsf="%s"' % options["hcp_task_lvl2fsf"]
                    )

            # summary name
            # mandatory for Level1
            if (
                options["hcp_task_lvl2task"] is None
                and options["hcp_task_summaryname"] is None
            ):
                r += "\n---> ERROR: hcp_task_summaryname is mandatory when running Level1 analysis!"
                run = False

            if options["hcp_task_summaryname"] is not None:
                comm += (
                    '                --summaryname="%s"'
                    % options["hcp_task_summaryname"]
                )

            # confound
            if options["hcp_task_confound"] is not None:
                comm += '                --confound="%s"' % options["hcp_task_confound"]

            # origsmoothingFWHM
            if options["hcp_bold_smoothFWHM"] != "2":
                comm += (
                    '                --origsmoothingFWHM="%s"'
                    % options["hcp_bold_smoothFWHM"]
                )

            # finalsmoothingFWHM
            if options["hcp_bold_final_smoothFWHM"] is not None:
                comm += (
                    '                --finalsmoothingFWHM="%s"'
                    % options["hcp_bold_final_smoothFWHM"]
                )

            # highpassfilter
            if options["hcp_task_highpass"] is not None:
                comm += (
                    '                --highpassfilter="%s"'
                    % options["hcp_task_highpass"]
                )

            # lowpassfilter
            if options["hcp_task_lowpass"] is not None:
                comm += (
                    '                --lowpassfilter="%s"' % options["hcp_task_lowpass"]
                )

            # procstring
            if options["hcp_task_procstring"] is not None:
                comm += (
                    '                --procstring="%s"' % options["hcp_task_procstring"]
                )

            # regname
            if options["hcp_regname"] is not None and options["hcp_regname"] not in [
                "MSMSulc",
                "NONE",
                "none",
                "None",
            ]:
                comm += '                --regname="%s"' % options["hcp_regname"]

            # grayordinatesres
            if (
                options["hcp_grayordinatesres"] is not None
                and options["hcp_grayordinatesres"] != 2
            ):
                comm += (
                    '                --grayordinatesres="%d"'
                    % options["hcp_grayordinatesres"]
                )

            # lowresmesh
            if (
                options["hcp_lowresmesh"] is not None
                and options["hcp_lowresmesh"] != "32"
            ):
                comm += '                --lowresmesh="%s"' % options["hcp_lowresmesh"]

            # parcellation
            if options["hcp_task_parcellation"] is not None:
                comm += (
                    '                --parcellation="%s"'
                    % options["hcp_task_parcellation"]
                )

            # parcellationfile
            if options["hcp_task_parcellation_file"] is not None:
                comm += (
                    '                --parcellationfile="%s"'
                    % options["hcp_task_parcellation_file"]
                )

            # hcp_task_vba flag
            if options["hcp_task_vba"]:
                comm += '                --vba="YES"'

            # -- Report command
            if run:
                r += (
                    "\n\n------------------------------------------------------------\n"
                )
                r += "Running HCP Pipelines command via QuNex:\n\n"
                r += comm.replace("                --", "\n    --")
                r += "\n------------------------------------------------------------\n"

        # -- Run
        if run:
            if options["run"] == "run":
                r, endlog, report, failed = pc.runExternalForFile(
                    None,
                    comm,
                    "Running HCP fMRI task analysis",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    fullTest=None,
                    shell=True,
                    r=r,
                )

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(
                    None, None, "HCP Diffusion", r, overwrite=overwrite
                )
                if passed is None:
                    r += "\n---> HCP fMRI task analysis can be run"
                    report = "HCP fMRI task analysis can be run"
                    failed = 0

        else:
            r += "\n---> Session cannot be processed."
            report = "HCP fMRI task analysis cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        failed = 1

    r += (
        "\n\nHCP fMRI task analysis Preprocessing %s on %s\n------------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    # print r
    return (r, (sinfo["id"], report, failed))
