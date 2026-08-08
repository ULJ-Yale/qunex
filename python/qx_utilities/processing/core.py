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

# Created by Grega Repovs on 2016-12-17.
# Code split from dofcMRIp_core gCodeP/preprocess codebase.
# Copyright (c) Grega Repovs. All rights reserved.


import contextlib
import os
import os.path
import re
import subprocess
import glob
import multiprocessing
from datetime import datetime

import qx_utilities.general.exceptions as ge
import qx_utilities.general.core as gc
import qx_utilities.general.log as gl


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def _note(log, text):
    """
    Append verbatim text to the report log, when there is one.

    The helpers below write into the log object they are handed instead of
    taking and returning a report string. Most of them are also called from
    places that keep no log (a utility resolving bold names, a recursive
    retry), so the log stays optional and a missing one drops the text.
    """
    if log is not None:
        log.raw(text)


@contextlib.contextmanager
def _streaming(log, comlog):
    """
    Attach `comlog` to the report log for the block, when there is one.

    Everything recorded inside is echoed into the comlog as well, so the
    comlog reads as a complete record of the call rather than only the tool's
    raw output. `log` is optional here for the same reason it is in
    :func:`_note`.
    """
    if log is None:
        yield
    else:
        with log.stream_to(comlog):
            yield


def _trace(log, comlog, text):
    """Write verbatim text to the comlog, through `log` when there is one."""
    if log is not None:
        log.trace(text)
    else:
        comlog.write(text)


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


def get_extension(filetype):
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


def use_or_skip_bold(sinfo, options, log=None):
    """
    ``use_or_skip_bold(sinfo, options, log=None)``

    Internal function to determine which bolds to use and which to skip.

    The bolds that are skipped are noted in `log`, when one is given.

    OUTPUTS
    =======

    --bolds  List of bolds to process.
    --bskip  List of bolds to skip.
    --nskip  Number of bolds to skip.

    The two lists contain dictionaries with the original information and additional fields:

    - 'bold_number'  - the bold number as integer
    - 'sequence_number'  - the sequence number as integer
    """

    bsearch = re.compile(r"bold([0-9]+)")
    btargets = [e.strip() for e in re.split(r" +|\||, *", options["bolds"])]

    bolds = []
    for k, v in sinfo.items():
        if k.isdigit() and bsearch.match(v["name"]):
            v["bold_number"] = int(bsearch.match(v["name"]).group(1))
            v["sequence_number"] = k
            bolds.append(v)
    bskip = []
    nbolds = len(bolds)

    if "all" not in btargets:
        keep = []

        # check bold number
        keep += [n for n in range(nbolds) if str(bolds[n]["bold_number"]) in btargets]

        # check the listed fields if they exist and have values listed in btargets
        for field in ["name", "task", "filename", "boldname", "ext", "ima"]:
            keep += [n for n in range(nbolds) if bolds[n].get(field) in btargets]

        # check sequence number -> skipping this, as it can overlap with bold number
        # keep += [n for n in range(nbolds) if bolds[n][4] in btargets]

        # determine keep and skip
        allb = set(range(nbolds))
        keep = set(keep)
        skip = allb.difference(keep)

        # set bolds and skips

        bskip = [bolds[i] for i in skip]
        bolds = [bolds[i] for i in keep]

        # sort and report
        bskip.sort(key=lambda x: x["bold_number"])
        if len(bskip) > 0:
            _note(log, "\n\nSkipping the following BOLD images:")
            for binfo in bskip:
                if (
                    "filename" in binfo
                    and options.get("hcp_filename", "") == "userdefined"
                ):
                    _note(log, "\n...  {filename:<20} [{name:<6} {task}]".format(**binfo))
                elif (
                    "boldname" in binfo
                    and options.get("hcp_filename", "") == "userdefined"
                ):
                    _note(log, "\n...  {boldname:<20} [{name:<6} {task}]".format(**binfo))
                else:
                    _note(log, "\n...  {name:<6} [{task}]".format(**binfo))
            _note(log, "\n")

    bolds.sort(key=lambda x: x["bold_number"])

    # if bolds have boldname (legacy) and not filename, copy boldname to filename
    for b in range(len(bolds)):
        if "filename" not in bolds[b] and "boldname" in bolds[b]:
            bolds[b]["filename"] = bolds[b]["boldname"]

    return bolds, bskip, len(bskip)


def get_bold_names(boldinfo, options):
    """
    Get bold names based on the boldinfo and options.
    """

    if "filename" in boldinfo and options["hcp_filename"] == "userdefined":
        printbold = boldinfo["filename"]
        boldtarget = boldinfo["filename"]
        boldsource = boldinfo["filename"]
    else:
        printbold = str(boldinfo["bold_number"])
        boldsource = "BOLD_%d" % (boldinfo["bold_number"])
        boldtarget = "%s%s" % (options["hcp_bold_prefix"], printbold)

    return printbold, boldtarget, boldsource


def do_options_check(options, sinfo, command):
    # logs -- an empty --comlog_folders means "take the settings value"
    folders = options.get("comlog_folders") or ",".join(gl.active().comlog_folders)
    logs = [e.strip() for e in re.split(r" +|\||, *", folders)]
    study_comlogs = options["comlogs"]
    comlogs = []

    for log in logs:
        if log in ["keep", "study"]:
            comlogs.append(study_comlogs)
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


def get_exact_file(candidate):
    g = glob.glob(candidate)
    if len(g) == 1:
        return g[0]
    elif len(g) > 1:
        # print("WARNING: there are %d files matching %s" % (len(g), candidate))
        return g[0]
    else:
        # print("WARNING: there are no files matching %s" % (candidate))
        return ""


def get_file_names(sinfo, options):
    """
    Build the dictionary of QuNex file names for a session's data.

    Resolves the structural, segmentation, BOLD and derived file paths a
    processing command reads and writes, based on the session folders and the
    naming options (tails, variants, glm/conc names).

    Parameters:
        sinfo (dict): session information; ``id`` is used.
        options (dict): command options controlling naming and targets.

    Returns:
        dict: mapping of file keys to absolute paths for this session.
    """

    d = get_session_folders(sinfo, options)

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
        f["t1_source"] = get_exact_file(os.path.join(d["s_source"], options["path_t1"]))

    ext = get_extension(options["image_target"].replace("cifti", "nifti"))

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


def get_bold_file_names(sinfo, boldname, options):
    """
    Build the file names for a single BOLD run of a session.

    Parameters:
        sinfo (dict): session information; ``id`` is used.
        boldname (str): the BOLD name (e.g. ``bold1``); its trailing number
            selects the run.
        options (dict): command options controlling naming and image target.

    Returns:
        dict: mapping of file keys to absolute paths for this BOLD run.
    """
    d = get_session_folders(sinfo, options)
    f = {}

    # identify bold_tail based on the type of image
    if options["image_target"] in ["cifti", "dtseries", "ptseries"]:
        target_bold_tail = options["cifti_tail"]
    else:
        target_bold_tail = options["nifti_tail"]

    # if bold_tail is set, use that instead
    target_bold_tail = options.get("bold_tail", target_bold_tail)

    boldnumber = re.search(r"\d+$", boldname).group()

    ext = get_extension(options["image_target"])

    rgss = options["bold_nuisance"]
    rgss = rgss.translate(str.maketrans("", "", " ,;|"))

    if d["s_source"] is None:
        f["bold_source"] = None
    else:
        if "path_" + boldname in options:
            f["bold_source"] = get_exact_file(
                os.path.join(d["s_source"], options["path_" + boldname])
            )
        else:
            btarget = options["path_bold"].replace("[N]", boldnumber)
            f["bold_source"] = get_exact_file(os.path.join(d["s_source"], btarget))

        if f["bold_source"] == "" and options["image_target"] == "4dfp":
            # print("Searching in the atlas folder ...")
            f["bold_source"] = get_exact_file(
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
            f["bold_mov_o"] = get_exact_file(
                os.path.join(d["s_source"], options["path_" + movname])
            )
        else:
            mtarget = options["path_mov"].replace("[N]", boldnumber)
            f["bold_mov_o"] = get_exact_file(os.path.join(d["s_source"], mtarget))

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


def find_file(sinfo, options, fname):
    """
    Locate a session file by trying the known QuNex source locations.

    Searches the session inbox (and its ``events``/``concs`` subfolders for conc
    and fidl files) and the structural source folder, with and without the
    session-id prefix.

    Parameters:
        sinfo (dict): session information; ``id`` is used.
        options (dict): command options used to resolve the session folders.
        fname (str): the file name to look for.

    Returns:
        str | bool: the first existing path found, or False if none exist.
    """
    d = get_session_folders(sinfo, options)

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


def get_session_folders(sinfo, options):
    """
    Build the dictionary of a session's folder locations.

    Resolves the source, images, structural, segmentation, BOLD and related
    working folders from the session information and options.

    Parameters:
        sinfo (dict): session information; ``id``, ``hcp``/``data`` are used.
        options (dict): command options controlling folder naming and variants.

    Returns:
        dict: mapping of folder keys to absolute paths for this session.
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
    with folder_creation_lock:
        for key, fpath in d.items():
            if key != "s_source":
                if not os.path.exists(fpath):
                    try:
                        # Check again inside the lock to ensure no other process created the folder
                        if not os.path.exists(fpath):
                            os.makedirs(fpath)
                    except Exception:
                        print(
                            f"WARNING: Could not create folder {fpath}! Please check paths and permissions!"
                        )

    return d


def missing_report(missing, message, prefix):
    """
    Takes a list of missing files and prepares a list report.
    """

    r = message + "\n"
    for file in missing:
        r += prefix + file + "\n"

    return r


# the spellings a comlog is scanned for. Deliberately narrow: a wider net
# ("Traceback", "Segmentation fault") turns the deletion veto below into "never
# delete anything", which is what `keep_comlogs` already spells
ERROR_TOKENS = ["Error ", "Error:", "ERROR ", "ERROR:"]


def log_has_errors(path):
    """
    Whether a comlog holds any of the four error spellings.

    Read line by line rather than into memory: comlogs can be large. Used both
    to judge a call with no test file and to veto the deletion of a comlog that
    finished cleanly -- in doubt, keep.

    Parameters:
        path (str | None): the comlog's path; None or missing reads as clean.

    Returns:
        bool: whether an error line was found.
    """
    if not path or not os.path.exists(path):
        return False

    with open(path, "r", errors="replace") as written:
        return any(any(e in line for e in ERROR_TOKENS) for line in written)


def check_run(
    tfile,
    full_test=None,
    command=None,
    log=None,
    comlog=None,
    verbose=True,
    overwrite=False,
):
    """
    ``check_run(tfile, full_test=None, command=None, log=None, comlog=None, verbose=True, overwrite=False)``

    The function checks the presence of a test file.
    If specified it runs also full test.

    What was checked is noted in `log`, when one is given and `verbose` is set.
    `comlog` is the ``ComContext`` of the call being checked, when the caller
    holds one: the full file check writes its report into it, and a call with
    no test file is judged by what it left in it.

    Returns:
        tuple: ``(passed, report, failed)``, where `passed` is

        --None        test file is missing
        --incomplete  test file is present, but full test was incomplete
        --done        test file is present, and if full test was specified, all
                      files were present as well
    """

    if full_test and "specfolder" in full_test:
        if os.path.exists(os.path.join(full_test["specfolder"], full_test["tfile"])):
            full_test["tfile"] = os.path.join(full_test["specfolder"], full_test["tfile"])

    if tfile is not None and os.path.exists(tfile) and not overwrite:
        if verbose:
            _note(
                log,
                "\n---> %s test file [%s] present"
                % (command, os.path.basename(tfile)),
            )
        report = "%s finished" % (command)
        passed = "done"
        failed = 0

        if full_test:
            try:
                filestatus, filespresent, filesmissing = gc.check_files(
                    full_test["tfolder"],
                    full_test["tfile"],
                    fields=full_test["fields"],
                    report=comlog.file if comlog else None,
                )
                if filesmissing:
                    if verbose:
                        _note(
                            log,
                            missing_report(
                                filesmissing,
                                "\n---> Full file check revealed that the following files were not created:",
                                "            ",
                            ),
                        )
                    report += ", full file check incomplete"
                    passed = "incomplete"
                    failed = 1
                else:
                    _note(log, "\n---> Full file check passed")
                    report += ", full file check complete"

            except ge.CommandFailed as e:
                report += ", full file check could not be completed (%s)" % e.report[0]
                passed = "incomplete"
                failed = 1

            except Exception:
                report += ", full file check could not be completed"
                passed = "incomplete"
                failed = 1

    elif tfile is None:
        report = "%s finished" % (command)
        passed = "done"
        failed = 0

        # nothing to check against, so the comlog's contents are the evidence
        if comlog is not None and log_has_errors(comlog.path):
            report = "%s not finished" % (command)
            passed = None
            failed = 1

    else:
        if verbose and tfile is not None:
            _note(log, "\n---> %s test file missing:\n     %s" % (command, tfile))
        report = "%s not finished" % (command)
        passed = None
        failed = 1

    return passed, report, failed


def _open_comlog(logfolder, task, logtags, thread, timestamp):
    """
    Open the comlog for one external call, and say where the copies go.

    `logfolder` is one folder or the list of them ``do_options_check`` builds:
    the first is where the comlog is written, the rest are where
    :func:`close_log` maps it once it is finished.

    Whether a file is opened at all is the resolved settings' call -- with
    comlogs switched off nothing is created, :attr:`ComContext.file` stays
    None, and the child process inherits the console.

    Returns:
        tuple: ``(comlog, logfolders)`` -- the open ``ComContext`` and the
        extra folders to map it into.
    """
    if type(logfolder) in [list, set, tuple]:
        logfolders = list(logfolder)
    else:
        logfolders = [logfolder]
    folder = logfolders.pop(0) if logfolders else ""

    if isinstance(logtags, (str, bytes)) or logtags is None:
        logtags = [logtags]

    settings = gl.active()
    comlog = gl.ComContext(
        folder,
        task,
        *logtags,
        thread=thread,
        timestamp=timestamp,
        enabled=settings.enabled and settings.comlog,
    )

    try:
        comlog.open()
    except OSError:
        raise ExternalFailed(
            "\n\nERROR: Could not create folder for logfile [%s]!" % (folder)
        )

    return comlog, logfolders


def close_log(comlog, logfolders, status, remove, log=None):
    """
    Close a comlog by status and map it into the extra folders.

    The lifecycle -- the ``tmp_`` to ``done_``/``error_``/``incomplete_``
    rename -- belongs to the ``ComContext`` that owns the file. What stays here
    is the fan-out into `logfolders` and the retention rules below, because
    each destination, each failure and each removal has to be noted in the
    report log, and a ``ComContext`` deliberately knows nothing about report
    logs: the bash and matlab runners hold one with no log at all.

    Two rules guard the deletion, and both live here because this is the only
    place a comlog is deleted, so all 110 call sites get them. A removed comlog
    still leaves its completion status in the report log -- that record is the
    one artifact that has to survive the file. And a comlog holding an error is
    kept whatever was asked for, including an explicit ``--log=remove``: the
    guard exists precisely for the case where the caller's belief that the call
    succeeded is the thing in doubt. ``keep_comlogs`` short-circuits both.

    Parameters:
        comlog (ComContext): the comlog to close.
        logfolders (list): extra folders to map the finished comlog into.
        status (str): ``done``, ``error`` or ``incomplete``.
        remove (bool): whether to delete a comlog that finished cleanly.
        log (ReportLog): the report log to note the outcome in.

    Returns:
        str | None: the path of the final log file, or None when it was
        removed or no comlog was written.
    """
    tfile = comlog.close(status=status)
    if tfile is None:
        return None

    if status == "done" and remove and not gl.active().keep_comlogs:
        if log_has_errors(tfile):
            _note(log, "\n---> completed, comlog kept -- it reports errors: %s" % (tfile))
        else:
            os.remove(tfile)
            _note(log, "\n---> completed [%s], comlog removed" % (status))
            return None

    _note(log, "\n---> logfile: %s" % (tfile))

    # -- do we have multiple logfolders?
    tname = os.path.basename(tfile)
    for logfolder in logfolders:
        nfile = os.path.join(logfolder, tname)
        try:
            os.makedirs(logfolder, exist_ok=True)
            gc.link_or_copy(tfile, nfile)
            _note(log, "\n---> logfile: %s" % (nfile))
        except Exception:
            _note(log, "\n---> WARNING: could not map logfile to: %s" % (nfile))

    return tfile


def run_external_for_file(
    checkfile,
    run,
    description,
    log=None,
    overwrite=False,
    thread="0",
    remove=True,
    task=None,
    logfolder="",
    logtags="",
    full_test=None,
    shell=True,
    verbose=True,
):
    """
    ``run_external_for_file(checkfile, run, description, log=None, overwrite=False, thread="0", remove=True, task=None, logfolder="", logtags="", full_test=None, shell=True, verbose=True)``

    Runs the specified command and checks whether it was executed against a
    checkfile, and if provided a full list of files as specified in full_test.

    What was run and how it ended is noted in `log`. When the command fails an
    ``ExternalFailed`` is raised carrying *only* the error message -- everything
    that led up to it is already in the log -- so the caller's handler appends
    it and the report reads in order.

    INPUTS
    ======

    --checkfile        The file to run a check against (file path)
    --run              The specific command to run (string)
    --description      A description of the command that will be run (string)
    --log              The report log to write the report into (ReportLog)
    --overwrite        Whether to overwrite existing data (checkfile present;
                       boolean)
    --thread           Thread count if multiple are run
    --remove           Whether to remove a log file once done (boolean)
    --task             A short name of the task to run
    --logfolder        A folder or a list of folders in which to place the log
    --logtags          An array of tags used to create a log name
    --full_test         A dictionary describing how to check against a full list
                       of files:

                       - tfolder    (a target folder with the results)
                       - tfile      (a path to the file describing the files to
                         check for)
                       - fields     (list of tuple key, value pairs, describing
                         which {} keys to replace with specific values
                       - specfolder (a folder to check for tfile if tfile might
                         be relative to it)

    --shell            Whether to run the command in a shell (boolean).

    OUTPUTS
    =======

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
    print_comm = gc.print_qunex_header(timestamp=logstamp)
    print_comm += "#\n"
    # external command info
    print_comm += "------------------------------------------------------------\n"
    print_comm += "Running external command via QuNex:\n\n"

    comm = run + "\n"
    comm = re.sub(r"( +--)", r" \\\n  --", comm)
    comm = re.sub(r"( +-)(?!-)", r" \\\n  -", comm)
    comm = re.sub(r"(  +)(?!-)", r" \\\n  ", comm)

    print_comm += comm

    if checkfile is not None and checkfile != "":
        print_comm += "\nTest file: \n%s\n" % checkfile
    print_comm += "------------------------------------------------------------"

    # report for local runs
    print("Running external command: %s" % print_comm)

    # add an empty line for log purposes
    print_comm += "\n"

    if overwrite or checkfile is None or not os.path.exists(checkfile):
        _note(log, "\n\n%s" % (description))

        comlog, logfolders = _open_comlog(logfolder, task, logtags, thread, logstamp)

        # --- report
        if comlog.path:
            print("You can follow command's progress in:")
            print(comlog.path)
            print("------------------------------------------------------------")

        with _streaming(log, comlog):
            # add command call to start of the log
            _trace(log, comlog, print_comm + "\n")

            # --- run command
            try:
                if shell:
                    process = subprocess.run(
                        run,
                        shell=True,
                        stdout=comlog.file,
                        stderr=comlog.file,
                        check=False,
                    )
                else:
                    process = subprocess.run(
                        run, stdout=comlog.file, stderr=comlog.file, check=False
                    )
            except Exception:
                message = (
                    "\n\nERROR: Running external command failed! \nTry running the command directly for more detailed error information:\n"
                    + comm
                )
                close_log(comlog, logfolders, "error", remove, log)
                raise ExternalFailed(message)

            # --- check results
            if process.returncode != 0:
                message = "\n\nERROR: %s failed with error %s\n... \ncommand executed:\n%s" % (
                    description,
                    process.stderr.decode() if process.stderr else "Unknown error",
                    comm,
                )
                close_log(comlog, logfolders, "error", remove, log)
                raise ExternalFailed(message)

            status, _, failed = check_run(
                checkfile,
                full_test=full_test,
                command=task,
                log=log,
                comlog=comlog,
                verbose=verbose,
            )

            if status is None:
                _note(
                    log,
                    "\n\nTry running the command directly for more detailed error information:\n"
                    + comm,
                )

            # --- End
            if status and status == "done":
                _trace(
                    log,
                    comlog,
                    "\n\n---> Successful completion of task at %s\n\n"
                    % (datetime.now()),
                )
                endlog = close_log(comlog, logfolders, "done", remove, log)
            elif status and status == "incomplete":
                endlog = close_log(comlog, logfolders, "incomplete", remove, log)
            else:
                endlog = close_log(comlog, logfolders, "error", remove, log)

    else:
        if os.path.getsize(checkfile) < 100:
            endlog, status, failed = run_external_for_file(
                checkfile,
                run,
                description,
                log,
                overwrite=True,
                thread=thread,
                remove=remove,
                task=task,
                logfolder=logfolder,
                logtags=logtags,
                full_test=full_test,
                shell=shell,
                verbose=verbose,
            )
        else:
            status, _, failed = check_run(checkfile, full_test)
            if status in ["full", "done"]:
                _note(log, "\n%s --- already completed" % (description))
            else:
                _note(log, "\n%s --- already ran, incomplete file check" % (description))

    if task:
        task += " "
    else:
        task = ""

    if status is None:
        status = task + "failed"
    else:
        status = task + status

    return endlog, status, failed


def run_script_through_shell(
    run,
    description,
    log=None,
    thread="0",
    remove=True,
    task=None,
    logfolder="",
    logtags="",
):
    """
    Run a command through the shell, capturing its output to a comlog.

    Writes the command's stdout/stderr to a temporary comlog which is renamed to
    a ``done_`` or ``error_`` log depending on the exit status. With comlogs
    switched off no file is written and the command's output is left on the
    console.

    Parameters:
        run (str): the shell command to run.
        description (str): human readable description used in the report and log.
        log (ReportLog): the report log to note the run in.
        thread (str): identifier used in the log file name.
        remove (bool): whether to remove the done log on success.
        task (str): task name used in the log file name.
        logfolder (str | list): folder to write the comlog into, or the list of
            folders to write it into and map it to; created when missing.
        logtags (str | list): tag(s) used in the log file name.

    Returns:
        str | None: the path to the final log, when one was kept.

    Raises:
        ExternalFailed: when the script exits non-zero, carrying the error
        message alone -- the description is already in the log.
    """

    _note(log, "\n\n%s" % (description))

    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
    comlog, logfolders = _open_comlog(logfolder, task, logtags, thread, logstamp)

    with _streaming(log, comlog):
        _trace(
            log,
            comlog,
            "\n#-------------------------------\n# Running: %s\n"
            "#-------------------------------\n" % (description),
        )

        with subprocess.Popen(
            run, shell=True, stdout=comlog.file, stderr=comlog.file
        ) as process:
            ret = process.wait()

        if ret:
            close_log(comlog, logfolders, "error", remove, log)
            raise ExternalFailed("\n\nERROR: Failed with error %s\n" % (ret))

        _trace(
            log,
            comlog,
            "\n\n---> Successful completion of task at %s\n\n" % (datetime.now()),
        )
        endlog = close_log(comlog, logfolders, "done", remove, log)
        _note(log, " --- done")

    return endlog


def check_for_file(log, checkfile, ok="", bad="", status=True):
    """
    Note the presence or absence of a single file in the report.

    Notes ``ok`` in the log when ``checkfile`` exists and ``bad`` when it does
    not; a missing file also drops ``status`` to False.

    Parameters:
        log (ReportLog): the report log to note the outcome in.
        checkfile (str): path to test for.
        ok (str): text noted when the file is present.
        bad (str): text noted when the file is missing.
        status (bool): the running status, carried through and set False on a
            missing file.

    Returns:
        bool: the running status.
    """
    if os.path.exists(checkfile):
        _note(log, ok)
        return status
    else:
        _note(log, bad)
        return False


def check_for_files(log, checkfiles, ok, bad, all=False, status=True):
    """
    check_for_files - checks if any of the files in the checkfiles list exists

    If all parameter is set to True, returns True only if all files exist,
    if all parameter is False it returns the first found file.

    Returns:
        tuple: ``(status, found)`` -- the running status and the first file
        found, when searching for any one of them.
    """

    for f in checkfiles:
        if os.path.exists(f):
            if not all:
                _note(log, ok)
                return status, f
        else:
            if all:
                _note(log, bad)
                return False, ""

    if not all:
        _note(log, bad)
        return False, ""

    # if we are here all files exist and all is set
    _note(log, ok)
    return status, ""


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
