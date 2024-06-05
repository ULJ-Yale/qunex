#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``core.py``

This file holds code for core support functions used by other code for
preprocessing and analysis. The functions are for internal use
and can not be called externally.
"""

"""
Created by Grega Repovs on 2016-12-17.
Code split from dofcMRIp_core gCodeP/preprocess codebase.
Copyright (c) Grega Repovs. All rights reserved.
"""


import os
import os.path
import shutil
import re
import subprocess
import glob
import sys
import traceback
import multiprocessing
from datetime import datetime
import general.exceptions as ge
import general.core as gc
from general.img import *
from general.meltmovfidl import *


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def print_exc_plus():
    """
    Print the usual traceback information, followed by a listing of all the
    local variables in each frame.
    """
    tb = sys.exc_info()[2]
    while 1:
        if not tb.tb_next:
            break
        tb = tb.tb_next
    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back
    stack.reverse()
    traceback.print_exc()
    print("Locals by frame, innermost last")
    for frame in stack:
        print
        print(
            "Frame %s in %s at line %s"
            % (frame.f_code.co_name, frame.f_code.co_filename, frame.f_lineno)
        )
        for key, value in frame.f_locals.items():
            print("\t%20s = " % key, end=" ")
            # We have to be careful not to cause a new error in our error
            # printer! Calling str() on an unknown object could cause an
            # error we don't want.
            try:
                print(value)
            except:
                print("<ERROR WHILE PRINTING VALUE>")


class ExternalFailed(Exception):
    def __init__(self, value="Got lost :-("):
        self.parameter = value

    def __str__(self):
        return self.parameter  # repr(self.parameter)


class NoSourceFolder(Exception):
    def __init__(self, value="Got lost :-("):
        self.parameter = value

    def __str__(self):
        return self.parameter  # repr(self.parameter)


def getExtension(filetype):
    extensions = {
        "4dfp": ".4dfp.img",
        "nifti": ".nii.gz",
        "cifti": ".dtseries.nii",
        "dtseries": ".dtseries.nii",
        "ptseries": ".ptseries.nii",
    }
    return extensions[filetype]


def root4dfp(filename):
    filename = filename.replace(".img", "")
    filename = filename.replace(".4dfp", "")
    return filename


def useOrSkipBOLD(sinfo, options, r=""):
    """
    ``useOrSkipBOLD(sinfo, options, r="")``

    Internal function to determine which bolds to use and which to skip.

    OUTPUTS
    =======

    --bolds  List of bolds to process.
    --bskip  List of bolds to skip.
    --nskip  Number of bolds to skip.
    --r      Report.

    Lists contain tuples with the following elements:

    - the bold number as integer
    - the numbered bold name (bold[N])
    - the task tag (e.g. 'rest')
    - the dictionary with all the info
    """

    bsearch = re.compile(r"bold([0-9]+)")
    btargets = [e.strip() for e in re.split(r" +|\||, *", options["bolds"])]
    bolds = [
        (int(bsearch.match(v["name"]).group(1)), v["name"], v["task"], v, k)
        for (k, v) in sinfo.items()
        if k.isdigit() and bsearch.match(v["name"])
    ]
    bskip = []
    nbolds = len(bolds)

    if "all" not in btargets:
        keep = []

        # check bold number
        keep += [n for n in range(nbolds) if str(bolds[n][0]) in btargets]

        # check bold 'bold[n]'
        keep += [n for n in range(nbolds) if bolds[n][1] in btargets]

        # check bold tags
        keep += [n for n in range(nbolds) if bolds[n][2] in btargets]

        # check bold names if present
        keep += [n for n in range(nbolds) if bolds[n][3].get("filename") in btargets]

        # check bold names if present
        keep += [n for n in range(nbolds) if bolds[n][3].get("boldname") in btargets]

        # check sequence names
        keep += [n for n in range(nbolds) if bolds[n][3].get("ext") in btargets]

        # check sequence number
        keep += [n for n in range(nbolds) if bolds[n][4] in btargets]

        # determine keep and skip
        allb = set(range(nbolds))
        keep = set(keep)
        skip = allb.difference(keep)

        # take out sequence number
        bolds = [e[:4] for e in bolds]

        # set bolds and skips

        bskip = [bolds[i] for i in skip]
        bolds = [bolds[i] for i in keep]

        # sort and report
        bskip.sort()
        if len(bskip) > 0:
            r += "\n\nSkipping the following BOLD images:"
            for n, b, t, v in bskip:
                if "filename" in v and options.get("hcp_filename", "") == "userdefined":
                    r += "\n...  %-20s [%-6s %s]" % (v["filename"], b, t)
                elif (
                    "boldname" in v and options.get("hcp_filename", "") == "userdefined"
                ):
                    r += "\n...  %-20s [%-6s %s]" % (v["boldname"], b, t)
                else:
                    r += "\n...  %-6s [%s]" % (b, t)
            r += "\n"
    else:
        # take out sequence number
        bolds = [e[:4] for e in bolds]

    bolds.sort()

    # if bolds have boldname (legacy) and not filename, copy boldname to filename
    for b in bolds:
        if "filename" not in b[3] and "boldname" in b[3]:
            b[3]["filename"] = b[3]["boldname"]

    return bolds, bskip, len(bskip), r


def _filter_bolds(bolds, bolds_filter):
    """
    An internal function for filtering a list of bolds.

    A list of bolds is filter according to the filter parameter.
    """

    # prepare filter
    filters = [e.strip() for e in re.split(r" +|\||, *", bolds_filter)]

    # used bolds storage
    used_bolds = []

    for b in bolds:
        # extract bold info
        _, _, _, boldinfo = b

        # check filters
        for f in filters:
            if f == boldinfo["ima"] or f == boldinfo["name"] or f == boldinfo["task"]:
                used_bolds.append(b)
                break

    return used_bolds


def doOptionsCheck(options, sinfo, command):
    # logs
    logs = [e.strip() for e in re.split(r" +|\||, *", options["log"])]
    studyComlogs = options["comlogs"]
    comlogs = []

    for log in logs:
        if log in ["keep", "study"]:
            comlogs.append(studyComlogs)
        elif log == "session":
            comlogs.append(
                os.path.join(options["sessionsfolder"], sinfo["id"], "logs", "comlogs")
            )
        elif log == "hcp":
            if "hcp" in sinfo:
                comlogs.append(
                    os.path.join(
                        sinfo["hcp"],
                        sinfo["id"] + options["hcp_suffix"],
                        "logs",
                        "comlogs",
                    )
                )
        else:
            comlogs.append(log)

    options["comlogs"] = comlogs


def getExactFile(candidate):
    g = glob.glob(candidate)
    if len(g) == 1:
        return g[0]
    elif len(g) > 1:
        # print("WARNING: there are %d files matching %s" % (len(g), candidate))
        return g[0]
    else:
        # print("WARNING: there are no files matching %s" % (candidate))
        return ""


def getFileNames(sinfo, options):
    """
    getFileNames - documentation not yet available.
    """

    d = getSessionFolders(sinfo, options)

    rgss = options["bold_nuisance"]
    rgss = rgss.translate(str.maketrans("", "", " ,;|")) + options["glm_name"]

    concname = "_".join(
        e
        for e in [
            options["boldname"] + options.get("bold_tail", ""),
            options["image_target"].replace("cifti", "dtseries"),
            options.get("concname", "conc"),
            options.get("fidlname", ""),
        ]
        if e
    )

    # --- structural images

    f = {}

    if d["s_source"] is None:
        f["t1_source"] = None
    else:
        f["t1_source"] = getExactFile(os.path.join(d["s_source"], options["path_t1"]))

    ext = getExtension(options["image_target"].replace("cifti", "nifti"))

    f["t1"] = os.path.join(d["s_struc"], "T1" + ext)

    f["t1_brain"] = os.path.join(d["s_struc"], "T1_brain" + ext)
    f["t1_seg"] = os.path.join(d["s_struc"], "T1_seg" + ext)
    f["bold_template"] = os.path.join(d["s_struc"], "BOLD_template" + ext)

    f["fs_aseg_t1"] = os.path.join(d["s_fs_mri"], "aseg_t1" + ext)
    f["fs_aseg_bold"] = os.path.join(d["s_fs_mri"], "aseg_bold" + ext)

    f["fs_aparc_t1"] = os.path.join(d["s_fs_mri"], "aparc+aseg_t1" + ext)
    f["fs_aparc_bold"] = os.path.join(d["s_fs_mri"], "aparc+aseg_bold" + ext)

    f["fs_lhpial"] = os.path.join(d["s_fs_surf"], "lh.pial")

    f["conc"] = os.path.join(d["s_bold_concs"], concname + ".conc")
    f["conc_final"] = os.path.join(
        d["s_bold_concs"], options["bold_prefix"] + concname + ".conc"
    )

    for ch in options["bold_actions"]:
        if ch == "s":
            f["conc_final"] = f["conc_final"].replace(".conc", "_s.conc")
        elif ch == "h":
            f["conc_final"] = f["conc_final"].replace(".conc", "_hpss.conc")
        elif ch == "r":
            f["conc_final"] = f["conc_final"].replace(".conc", "_res-" + rgss + ".conc")
        elif ch == "l":
            f["conc_final"] = f["conc_final"].replace(".conc", "_lpss.conc")

    # --- Freesurfer preprocessing "internals"

    f["fs_morig_mgz"] = os.path.join(d["s_fs_orig"], "001.mgz")
    f["fs_morig_nii"] = os.path.join(d["s_fs_orig"], "001.nii")

    # --- legacy paths and Freesurfer preprocessing "internals"

    f["m111"] = os.path.join(d["s_struc"], "mprage_111.4dfp.img")
    f["m111_nifti"] = os.path.join(d["s_struc"], "mprage_111_flip.4dfp.nii.gz")
    f["m111_brain_nifti"] = os.path.join(
        d["s_struc"], "mprage_111_brain_flip.4dfp.nii.gz"
    )
    f["m111_seg_nifti"] = os.path.join(d["s_struc"], "mprage_111_brain_flip_seg.nii.gz")
    f["m111_brain"] = os.path.join(d["s_struc"], "mprage_111_brain.4dfp.img")
    f["m111_seg"] = os.path.join(d["s_struc"], "mprage_111_seg.4dfp.img")

    f["fs_aseg_mgz"] = os.path.join(d["s_fs_mri"], "aseg.mgz")
    f["fs_aseg_nii"] = os.path.join(d["s_fs_mri"], "aseg.nii")
    f["fs_aseg_analyze"] = os.path.join(d["s_fs_mri"], "aseg.img")
    f["fs_aseg_4dfp"] = os.path.join(d["s_fs_mri"], "aseg.4dfp.img")
    f["fs_aseg_111"] = os.path.join(d["s_fs_mri"], "aseg_111.4dfp.img")
    f["fs_aseg_333"] = os.path.join(d["s_fs_mri"], "aseg_333.4dfp.img")
    f["fs_aseg_111_nii"] = os.path.join(d["s_fs_mri"], "aseg_111.nii.gz")
    f["fs_aseg_333_nii"] = os.path.join(d["s_fs_mri"], "aseg_333.nii.gz")

    f["fs_aparc+aseg_mgz"] = os.path.join(d["s_fs_mri"], "aparc+aseg.mgz")
    f["fs_aparc+aseg_nii"] = os.path.join(d["s_fs_mri"], "aparc+aseg.nii")
    f["fs_aparc+aseg_3d_nii"] = os.path.join(d["s_fs_mri"], "aparc+aseg_3d.nii")
    f["fs_aparc+aseg_analyze"] = os.path.join(d["s_fs_mri"], "aparc+aseg.img")
    f["fs_aparc+aseg_4dfp"] = os.path.join(d["s_fs_mri"], "aparc+aseg.4dfp.img")
    f["fs_aparc+aseg_111"] = os.path.join(d["s_fs_mri"], "aparc+aseg_111.4dfp.img")
    f["fs_aparc+aseg_333"] = os.path.join(d["s_fs_mri"], "aparc+aseg_333.4dfp.img")
    f["fs_aparc+aseg_111_nii"] = os.path.join(d["s_fs_mri"], "aparc+aseg_111.nii.gz")
    f["fs_aparc+aseg_333_nii"] = os.path.join(d["s_fs_mri"], "aparc+aseg_333.nii.gz")

    # --- convert legacy paths (create hard links)

    if options["image_target"] == "4dfp":
        # ---> BET & FAST

        if os.path.exists(f["m111_brain"]) and not os.path.exists(f["t1_brain"]):
            gc.link_or_copy(f["m111_brain"], f["t1_brain"])

        if os.path.exists(f["m111_seg"]) and not os.path.exists(f["t1_seg"]):
            gc.link_or_copy(f["m111_seg"], f["t1_seg"])

        # ---> FreeSurfer

        if os.path.exists(f["fs_aseg_111"]) and not os.path.exists(f["fs_aseg_t1"]):
            gc.link_or_copy(f["fs_aseg_111"], f["fs_aseg_t1"])
        if os.path.exists(
            f["fs_aseg_111"].replace(".img", ".ifh")
        ) and not os.path.exists(f["fs_aseg_t1"].replace(".img", ".ifh")):
            gc.link_or_copy(
                f["fs_aseg_111"].replace(".img", ".ifh"),
                f["fs_aseg_t1"].replace(".img", ".ifh"),
            )

        if os.path.exists(f["fs_aseg_333"]) and not os.path.exists(f["fs_aseg_bold"]):
            gc.link_or_copy(f["fs_aseg_333"], f["fs_aseg_bold"])
        if os.path.exists(
            f["fs_aseg_333"].replace(".img", ".ifh")
        ) and not os.path.exists(f["fs_aseg_bold"].replace(".img", ".ifh")):
            gc.link_or_copy(
                f["fs_aseg_333"].replace(".img", ".ifh"),
                f["fs_aseg_bold"].replace(".img", ".ifh"),
            )

        if os.path.exists(f["fs_aparc+aseg_111"]) and not os.path.exists(
            f["fs_aparc_t1"]
        ):
            gc.link_or_copy(f["fs_aparc+aseg_111"], f["fs_aparc_t1"])
        if os.path.exists(
            f["fs_aparc+aseg_111"].replace(".img", ".ifh")
        ) and not os.path.exists(f["fs_aparc_t1"].replace(".img", ".ifh")):
            gc.link_or_copy(
                f["fs_aparc+aseg_111"].replace(".img", ".ifh"),
                f["fs_aparc_t1"].replace(".img", ".ifh"),
            )

        if os.path.exists(f["fs_aparc+aseg_333"]) and not os.path.exists(
            f["fs_aparc_bold"]
        ):
            gc.link_or_copy(f["fs_aparc+aseg_333"], f["fs_aparc_bold"])
        if os.path.exists(
            f["fs_aparc+aseg_333"].replace(".img", ".ifh")
        ) and not os.path.exists(f["fs_aparc_bold"].replace(".img", ".ifh")):
            gc.link_or_copy(
                f["fs_aparc+aseg_333"].replace(".img", ".ifh"),
                f["fs_aparc_bold"].replace(".img", ".ifh"),
            )

    return f


def getBOLDFileNames(sinfo, boldname, options):
    """
    getBOLDFileNames - documentation not yet available.
    """
    d = getSessionFolders(sinfo, options)
    f = {}

    # identify bold_tail based on the type of image
    if options["image_target"] in ["cifti", "dtseries", "ptseries"]:
        target_bold_tail = options["cifti_tail"]
    else:
        target_bold_tail = options["nifti_tail"]

    # if bold_tail is set, use that instead
    target_bold_tail = options.get("bold_tail", target_bold_tail)

    boldnumber = re.search(r"\d+$", boldname).group()

    ext = getExtension(options["image_target"])

    rgss = options["bold_nuisance"]
    rgss = rgss.translate(str.maketrans("", "", " ,;|"))

    if d["s_source"] is None:
        f["bold_source"] = None
    else:
        if "path_" + boldname in options:
            f["bold_source"] = getExactFile(
                os.path.join(d["s_source"], options["path_" + boldname])
            )
        else:
            btarget = options["path_bold"].replace("[N]", boldnumber)
            f["bold_source"] = getExactFile(os.path.join(d["s_source"], btarget))

        if f["bold_source"] == "" and options["image_target"] == "4dfp":
            # print("Searching in the atlas folder ...")
            f["bold_source"] = getExactFile(
                os.path.join(
                    d["s_source"],
                    "atlas",
                    "*b" + boldnumber + "_faln_dbnd_xr3d_atl.4dfp.img",
                )
            )

    # --- bold masks
    f["bold1"] = os.path.join(
        d["s_boldmasks"],
        options["boldname"]
        + boldnumber
        + options["nifti_tail"]
        + "_frame1"
        + ".nii.gz",
    )
    f["bold1_brain"] = os.path.join(
        d["s_boldmasks"],
        options["boldname"]
        + boldnumber
        + options["nifti_tail"]
        + "_frame1_brain"
        + ".nii.gz",
    )
    f["bold1_brain_mask"] = os.path.join(
        d["s_boldmasks"],
        options["boldname"]
        + boldnumber
        + options["nifti_tail"]
        + "_frame1_brain_mask"
        + ".nii.gz",
    )

    # --- bold masks internals
    f["bold1_nifti"] = os.path.join(
        d["s_boldmasks"],
        options["boldname"]
        + boldnumber
        + options["nifti_tail"]
        + "_frame1_flip.4dfp.nii.gz",
    )
    f["bold1_brain_nifti"] = os.path.join(
        d["s_boldmasks"],
        options["boldname"]
        + boldnumber
        + options["nifti_tail"]
        + "_frame1_brain_flip.4dfp.nii.gz",
    )
    f["bold1_brain_mask_nifti"] = os.path.join(
        d["s_boldmasks"],
        options["boldname"]
        + boldnumber
        + options["nifti_tail"]
        + "_frame1_brain_flip.4dfp_mask.nii.gz",
    )

    f["bold_n_png"] = os.path.join(
        d["s_nuisance"],
        options["boldname"] + boldnumber + options["nifti_tail"] + "_nuisance.png",
    )

    # --- movement files
    movname = boldname.replace(options["boldname"], "mov")

    if d["s_source"] is None:
        f["bold_mov_o"] = None
    else:
        if "path_" + movname in options:
            f["bold_mov_o"] = getExactFile(
                os.path.join(d["s_source"], options["path_" + movname])
            )
        else:
            mtarget = options["path_mov"].replace("[N]", boldnumber)
            f["bold_mov_o"] = getExactFile(os.path.join(d["s_source"], mtarget))

    f["bold_mov"] = os.path.join(
        d["s_bold_mov"], options["boldname"] + boldnumber + "_mov.dat"
    )

    # --- event files
    if "e" in options["bold_nuisance"]:
        if d["s_source"] is None:
            f["bold_event_o"] = None
        else:
            f["bold_event_o"] = (
                os.path.join(
                    d["s_source"],
                    options["boldname"] + boldnumber + options["event_file"],
                )
                + ".fidl"
            )
        f["bold_event_a"] = (
            os.path.join(
                options["sessionsfolder"],
                "inbox",
                sinfo["id"]
                + "_"
                + options["boldname"]
                + boldnumber
                + options["event_file"],
            )
            + ".fidl"
        )
        f["bold_event"] = (
            os.path.join(
                d["s_bold_events"],
                options["boldname"] + boldnumber + options["event_file"],
            )
            + ".fidl"
        )

    # --- bold preprocessed files
    f["bold"] = os.path.join(
        d["s_bold"], options["boldname"] + boldnumber + target_bold_tail + ext
    )
    f["bold_final"] = os.path.join(
        d["s_bold"],
        options["boldname"]
        + boldnumber
        + target_bold_tail
        + options["bold_prefix"]
        + ext,
    )
    f["bold_stats"] = os.path.join(
        d["s_bold_mov"],
        options["boldname"] + boldnumber + options["nifti_tail"] + ".bstats",
    )
    f["bold_nuisance"] = os.path.join(
        d["s_bold_mov"],
        options["boldname"] + boldnumber + options["nifti_tail"] + ".nuisance",
    )
    f["bold_scrub"] = os.path.join(
        d["s_bold_mov"],
        options["boldname"] + boldnumber + options["nifti_tail"] + ".scrub",
    )

    f["bold_vol"] = os.path.join(
        d["s_bold"],
        options["boldname"] + boldnumber + options["nifti_tail"] + ".nii.gz",
    )
    f["bold_dts"] = os.path.join(
        d["s_bold"],
        options["boldname"] + boldnumber + options["cifti_tail"] + ".dtseries.nii",
    )
    f["bold_pts"] = os.path.join(
        d["s_bold"],
        options["boldname"] + boldnumber + options["cifti_tail"] + ".ptseries.nii",
    )

    f["bold_qx_vol"] = os.path.join(
        d["s_bold"],
        options["boldname"] + boldnumber + options["qx_nifti_tail"] + ".nii.gz",
    )
    f["bold_qx_dts"] = os.path.join(
        d["s_bold"],
        options["boldname"] + boldnumber + options["qx_cifti_tail"] + ".dtseries.nii",
    )
    f["bold_qx_pts"] = os.path.join(
        d["s_bold"],
        options["boldname"] + boldnumber + options["qx_cifti_tail"] + ".ptseries.nii",
    )

    for ch in options["bold_actions"]:
        if ch == "s":
            f["bold_final"] = f["bold_final"].replace(ext, "_s" + ext)
        elif ch == "h":
            f["bold_final"] = f["bold_final"].replace(ext, "_hpss" + ext)
        elif ch == "c":
            f["bold_coef"] = f["bold_final"].replace(ext, "_coeff" + ext)
        elif ch == "r":
            f["bold_final"] = f["bold_final"].replace(
                ext, "_res-" + rgss + options["glm_name"] + ext
            )
        elif ch == "l":
            f["bold_final"] = f["bold_final"].replace(ext, "_lpss" + ext)

    return f


def findFile(sinfo, options, fname):
    """
    findFile - documentation not yet available.
    """
    d = getSessionFolders(sinfo, options)

    tfile = os.path.join(d["inbox"], "%s_%s" % (sinfo["id"], fname))
    if os.path.exists(tfile):
        return tfile

    if any([e in fname for e in ["conc", "fidl"]]):
        tfile = os.path.join(d["inbox"], "events", "%s_%s" % (sinfo["id"], fname))
        if os.path.exists(tfile):
            return tfile

    if any([e in fname for e in ["conc"]]):
        tfile = os.path.join(d["inbox"], "concs", "%s_%s" % (sinfo["id"], fname))
        if os.path.exists(tfile):
            return tfile

    if d["s_source"] is not None:
        tfile = os.path.join(d["s_source"], fname)
        if os.path.exists(tfile):
            return tfile

        tfile = os.path.join(d["s_source"], "%s_%s" % (sinfo["id"], fname))
        if os.path.exists(tfile):
            return tfile

    return False


def getSessionFolders(sinfo, options):
    """
    getSessionFolders - documentation not yet available.
    """
    d = {"s_source": None}

    if options["image_source"] == "hcp" and "hcp" in sinfo:
        d["s_source"] = sinfo["hcp"]
    elif "data" in sinfo:
        d["s_source"] = sinfo["data"]

    if "hcp" in sinfo:
        d["hcp"] = os.path.join(sinfo["hcp"], sinfo["id"] + options["hcp_suffix"])

    d["s_base"] = os.path.join(options["sessionsfolder"], sinfo["id"])
    d["s_images"] = os.path.join(d["s_base"], "images" + options["img_suffix"])
    d["s_struc"] = os.path.join(d["s_images"], "structural")
    d["s_seg"] = os.path.join(d["s_images"], "segmentation")
    d["s_boldmasks"] = os.path.join(d["s_seg"], "boldmasks" + options["bold_variant"])
    d["s_bold"] = os.path.join(d["s_images"], "functional" + options["bold_variant"])
    d["s_bold_mov"] = os.path.join(d["s_bold"], "movement")
    d["s_bold_events"] = os.path.join(d["s_bold"], "events")
    d["s_bold_concs"] = os.path.join(d["s_bold"], "concs")
    d["s_bold_glm"] = os.path.join(d["s_bold"], "glm")
    d["s_roi"] = os.path.join(d["s_images"], "ROI")
    d["s_nuisance"] = os.path.join(d["s_roi"], "nuisance" + options["bold_variant"])
    d["s_fs"] = os.path.join(d["s_seg"], "freesurfer")
    d["s_hcp"] = os.path.join(d["s_seg"], "hcp")
    d["s_s32k"] = os.path.join(d["s_hcp"], "fsaverage_LR32k")
    d["s_fs_mri"] = os.path.join(d["s_fs"], "mri")
    d["s_fs_orig"] = os.path.join(d["s_fs"], "mri/orig")
    d["s_fs_surf"] = os.path.join(d["s_fs"], "surf")
    d["inbox"] = os.path.join(options["sessionsfolder"], "inbox")
    d["qc"] = os.path.join(options["sessionsfolder"], "QC")
    d["qc_mov"] = os.path.join(
        d["qc"], "movement" + options["img_suffix"] + options["bold_variant"]
    )

    folder_creation_lock = multiprocessing.Lock()

    for key, fpath in d.items():
        if key != "s_source":
            if not os.path.exists(fpath):
                try:
                    with folder_creation_lock:
                        # Check again inside the lock to ensure no other process created the folder
                        if not os.path.exists(fpath):
                            os.makedirs(fpath)
                except:
                    print(
                        f"ERROR: Could not create folder {fpath}! Please check paths and permissions!"
                    )

    return d


def missingReport(missing, message, prefix):
    """
    Takes a list of missing files and prepares a list report.
    """

    r = message + "\n"
    for file in missing:
        r += prefix + file + "\n"

    return r


def checkRun(
    tfile,
    fullTest=None,
    command=None,
    r="",
    logFile=None,
    verbose=True,
    overwrite=False,
):
    """
    ``checkRun(tfile, fullTest=None, command=None, r="", logFile=None, verbose=True, overwrite=False)``

    The function checks the presence of a test file.
    If specified it runs also full test.

    OUTPUTS
    =======

    --None        test file is missing
    --incomplete  test file is present, but full test was incomplete
    --done        test file is present, and if full test was specified, all
                  files were present as well
    """

    if fullTest and "specfolder" in fullTest:
        if os.path.exists(os.path.join(fullTest["specfolder"], fullTest["tfile"])):
            fullTest["tfile"] = os.path.join(fullTest["specfolder"], fullTest["tfile"])

    if tfile is not None and os.path.exists(tfile) and not overwrite:
        if verbose:
            r += "\n---> %s test file [%s] present" % (command, os.path.basename(tfile))
        report = "%s finished" % (command)
        passed = "done"
        failed = 0

        if fullTest:
            try:
                filestatus, filespresent, filesmissing = gc.checkFiles(
                    fullTest["tfolder"],
                    fullTest["tfile"],
                    fields=fullTest["fields"],
                    report=logFile,
                )
                if filesmissing:
                    if verbose:
                        r += missingReport(
                            filesmissing,
                            "\n---> Full file check revealed that the following files were not created:",
                            "            ",
                        )
                    report += ", full file check incomplete"
                    passed = "incomplete"
                    failed = 1
                else:
                    r += "\n---> Full file check passed"
                    report += ", full file check complete"

            except ge.CommandFailed as e:
                report += ", full file check could not be completed (%s)" % e.report[0]
                passed = "incomplete"
                failed = 1

            except:
                report += ", full file check could not be completed"
                passed = "incomplete"
                failed = 1

    elif tfile is None:
        report = "%s finished" % (command)
        passed = "done"
        failed = 0

        # check log contents for errors
        log = open(logFile, "r")
        lines = log.readlines()

        for line in lines:
            if "Error" in line or "ERROR" in line:
                report = "%s not finished" % (command)
                passed = None
                failed = 1
                break

    else:
        if verbose and tfile is not None:
            r += "\n---> %s test file missing:\n     %s" % (command, tfile)
        report = "%s not finished" % (command)
        passed = None
        failed = 1

    return passed, report, r, failed


def closeLog(logfile, logname, logfolders, status, remove, r):
    # -- close the log
    if logfile:
        logfile.close()

    # -- do we delete it
    if status == "done" and remove:
        os.remove(logname)
        return None, r

    # -- rename it
    sfolder, sname = os.path.split(logname)
    tname = re.sub("^tmp", status, sname)
    tfile = os.path.join(sfolder, tname)
    shutil.move(logname, tfile)
    r += "\n---> logfile: %s" % (tfile)

    # -- do we have multiple logfolders?
    for logfolder in logfolders:
        nfile = os.path.join(logfolder, tname)
        if not os.path.exists(logfolder):
            os.makedirs(logfolder)
        try:
            gc.link_or_copy(tfile, nfile)
            r += "\n---> logfile: %s" % (nfile)
        except:
            r += "\n---> WARNING: could not map logfile to: %s" % (nfile)

    return tfile, r


def runExternalForFile(
    checkfile,
    run,
    description,
    overwrite=False,
    thread="0",
    remove=True,
    task=None,
    logfolder="",
    logtags="",
    fullTest=None,
    shell=False,
    r="",
    verbose=True,
):
    """
    ``runExternalForFile(checkfile, run, description, overwrite=False, thread="0", remove=True, task=None, logfolder="", logtags="", fullTest=None, shell=False, r="", verbose=True)``

    Runs the specified command and checks whether it was executed against a
    checkfile, and if provided a full list of files as specified in fullTest.

    INPUTS
    ======

    --checkfile        The file to run a check against (file path)
    --run              The specific command to run (string)
    --description      A description of the command that will be run (string)
    --overwrite        Whether to overwrite existing data (checkfile present;
                       boolean)
    --thread           Thread count if multiple are run
    --remove           Whether to remove a log file once done (boolean)
    --task             A short name of the task to run
    --logfolder        A folder or a list of folders in which to place the log
    --logtags          An array of tags used to create a log name
    --fullTest         A dictionary describing how to check against a full list
                       of files:

                       - tfolder    (a target folder with the results)
                       - tfile      (a path to the file describing the files to
                         check for)
                       - fields     (list of tuple key, value pairs, describing
                         which {} keys to replace with specific values
                       - specfolder (a folder to check for tfile if tfile might
                         be relative to it)

    --shell            Whether to run the command in a shell (boolean).
    --r                A string to which to append the report.

    OUTPUTS
    =======

    --r             The report string.
    --endlog        The path to the final log file.
    --status        Description of whether the command failed, is fully done or
                    incomplete based on the test files.
    --failed        0 for ok, 1 or more for failed or incomplete runs.
    """

    endlog = None

    # timestamp
    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")

    # -- Report command
    # header
    printComm = gc.print_qunex_header(timestamp=logstamp)
    printComm += "#\n"
    # external command info
    printComm += "------------------------------------------------------------\n"
    printComm += "Running external command via QuNex:\n\n"

    comm = run + "\n"

    printComm += comm
    if checkfile is not None and checkfile != "":
        printComm += "\nTest file: \n%s\n" % checkfile
    printComm += "------------------------------------------------------------"

    # report for local runs
    print("Running external command: %s" % comm)

    # add an empty line for log purposes
    printComm += "\n"

    if overwrite or checkfile is None or not os.path.exists(checkfile):
        r += "\n\n%s" % (description)

        # --- set up parameters
        basestring = (str, bytes)
        if isinstance(logtags, basestring) or logtags is None:
            logtags = [logtags]

        logname = [task] + logtags + [thread, logstamp]
        logname = [e for e in logname if e]
        logname = "_".join(logname)

        logfolders = []
        if type(logfolder) in [list, set, tuple]:
            logfolders = list(logfolder)
            logfolder = logfolders.pop(0)

        if not os.path.exists(logfolder):
            try:
                os.makedirs(logfolder)
            except:
                r += "\n\nERROR: Could not create folder for logfile [%s]!" % (
                    logfolder
                )
                raise ExternalFailed(r)

        tmplogfile = os.path.join(logfolder, "tmp_%s.log" % (logname))
        # --- report
        print("You can follow command's progress in:")
        print(tmplogfile)
        print("------------------------------------------------------------")

        # --- run command
        try:
            # append mode
            nf = open(tmplogfile, "a")

            # --- open log file
            if not os.path.exists(tmplogfile):
                r += "\n\nERROR: Could not create a temporary log file %s!" % (
                    tmplogfile
                )
                raise ExternalFailed(r)

            # add command call to start of the log
            print(printComm, file=nf)
            nf.flush()

            if shell:
                ret = subprocess.call(run, shell=True, stdout=nf, stderr=nf)
            else:
                ret = subprocess.call(run.split(), stdout=nf, stderr=nf)

        except:
            r += "\n\nERROR: Running external command failed! \nTry running the command directly for more detailed error information:\n"
            r += comm
            endlog, r = closeLog(nf, tmplogfile, logfolders, "error", remove, r)
            raise ExternalFailed(r)

        # --- check results
        if ret:
            r += "\n\nERROR: %s failed with error %s\n... \ncommand executed:\n" % (
                description,
                ret,
            )
            r += comm
            endlog, r = closeLog(nf, tmplogfile, logfolders, "error", remove, r)
            raise ExternalFailed(r)

        status, report, r, failed = checkRun(
            checkfile,
            fullTest=fullTest,
            command=task,
            r=r,
            logFile=tmplogfile,
            verbose=verbose,
        )

        if status is None:
            r += "\n\nTry running the command directly for more detailed error information:\n"
            r += comm

        # --- End
        if status and status == "done":
            print("\n\n---> Successful completion of task\n", file=nf)
            endlog, r = closeLog(nf, tmplogfile, logfolders, "done", remove, r)
        else:
            if status and status == "incomplete":
                endlog, r = closeLog(
                    nf, tmplogfile, logfolders, "incomplete", remove, r
                )
            else:
                endlog, r = closeLog(nf, tmplogfile, logfolders, "error", remove, r)

    else:
        if os.path.getsize(checkfile) < 100:
            r, endlog, status, failed = runExternalForFile(
                checkfile,
                run,
                description,
                overwrite=True,
                thread=thread,
                task=task,
                logfolder=logfolder,
                logtags=logtags,
                fullTest=fullTest,
                shell=shell,
                r=r,
            )
        else:
            status, _, _, failed = checkRun(checkfile, fullTest)
            if status in ["full", "done"]:
                r += "\n%s --- already completed" % (description)
            else:
                r += "\n%s --- already ran, incomplete file check" % (description)

    if task:
        task += " "
    else:
        task = ""

    if status is None:
        status = task + "failed"
    else:
        status = task + status

    return r, endlog, status, failed


def runScriptThroughShell(
    run, description, thread="0", remove=True, task=None, logfolder="", logtags=""
):
    """
    runScriptThroughShell - documentation not yet available.
    """

    r = "\n\n%s" % (description)
    basestring = (str, bytes)
    if isinstance(logtags, basestring):
        logtags = [logtags]

    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
    logname = [task] + logtags + [thread, logstamp]
    logname = [e for e in logname if e]
    logname = "_".join(logname)

    tmplogfile = os.path.join(logfolder, "tmp_%s.log" % (logname))
    donelogfile = os.path.join(logfolder, "done_%s.log" % (logname))
    errlogfile = os.path.join(logfolder, "error_%s.log" % (logname))
    endlog = None

    nf = open(tmplogfile, "w")
    print(
        "\n#-------------------------------\n# Running: %s\n#-------------------------------"
        % (description),
        file=nf,
    )

    ret = subprocess.call(run, shell=True, stdout=nf, stderr=nf)
    if ret:
        r += "\n\nERROR: Failed with error %s\n" % (ret)
        nf.close()
        shutil.move(tmplogfile, errlogfile)
        endlog = errlogfile
        raise ExternalFailed(r)
    else:
        print("\n\n---> Successful completion of task\n", file=nf)
        nf.close()
        if remove:
            os.remove(tmplogfile)
        else:
            shutil.move(tmplogfile, donelogfile)
            endlog = donelogfile
        r += " --- done"

    return r, endlog


def checkForFile(r, checkfile, message, status=True):
    """
    checkForFile - documentation not yet available.
    """
    if not os.path.exists(checkfile):
        status = False
        r = r + "\n... %s" % (message)
    return r, status


def checkForFile2(r, checkfile, ok, bad, status=True):
    """
    checkForFile2 - documentation not yet available.
    """
    if os.path.exists(checkfile):
        r += ok
        return r, status
    else:
        r += bad
        return r, False


def checkForFiles(r, checkfiles, ok, bad, all=False, status=True):
    """
    checkForFiles - checks if any of the files in the checkfiles list exists

    If all parameter is set to True, returns True only if all files exist,
    if all parameter is False it returns the first found file.
    """

    for f in checkfiles:
        if os.path.exists(f):
            if not all:
                r += ok
                return r, status, f
        else:
            if all:
                r += bad
                return r, False, ""

    if not all:
        r += bad
        return r, False, ""

    # if we are here all files exist and all is set
    r += ok
    return r, status, ""


def action(action, run):
    """
    action(action, run)
    A function that prepends "test" to action name if run is set to "test".
    """
    if run == "test":
        if action.istitle():
            return "Test " + action.lower()
        else:
            return "test " + action
    else:
        return action
