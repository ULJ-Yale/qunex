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


def _note(_log, text):
    """
    Append verbatim text to the report log, when there is one.

    The helpers below write into the log object they are handed instead of
    taking and returning a report string. Most of them are also called from
    places that keep no log (a utility resolving bold names, a recursive
    retry), so the log stays optional and a missing one drops the text.
    """
    if _log is not None:
        _log.raw(text)


def _say(_log, level, message, depth=0):
    """
    Record `message` at `level` on the report log, when there is one.

    :func:`_note`'s counterpart for text the helpers here state themselves:
    the level method spells the marker and the indent, so the message never
    carries them. `log` is optional for the same reason it is in :func:`_note`.
    An empty message is dropped rather than rendered as a bare marker --
    :func:`check_for_file`'s `ok` and `bad` both default to `""`.
    """
    if _log is not None and message:
        getattr(_log, level)(message, depth=depth)


@contextlib.contextmanager
def _streaming(_log, comlog):
    """
    Attach `comlog` to the report log for the block, when there is one.

    Everything recorded inside is echoed into the comlog as well, so the
    comlog reads as a complete record of the call rather than only the tool's
    raw output. `log` is optional here for the same reason it is in
    :func:`_note`.
    """
    if _log is None:
        yield
    else:
        with _log.stream_to(comlog):
            yield


def _trace(_log, comlog, text):
    """Write verbatim text to the comlog, through `log` when there is one."""
    if _log is not None:
        _log.trace(text)
    else:
        comlog.write(text)


class ExternalFailed(Exception):
    def __init__(self, value="Got lost :-("):
        super().__init__(value)


class NoSourceFolder(Exception):
    def __init__(self, value="Got lost :-("):
        super().__init__(value)


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


def use_or_skip_bold(sinfo, options, *, _log=None):
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
            _note(_log, "\n\nSkipping the following BOLD images:")
            for binfo in bskip:
                if (
                    "filename" in binfo
                    and options.get("hcp_filename", "") == "userdefined"
                ):
                    _note(_log, "\n...  {filename:<20} [{name:<6} {task}]".format(**binfo))
                elif (
                    "boldname" in binfo
                    and options.get("hcp_filename", "") == "userdefined"
                ):
                    _note(_log, "\n...  {boldname:<20} [{name:<6} {task}]".format(**binfo))
                else:
                    _note(_log, "\n...  {name:<6} [{task}]".format(**binfo))
            _note(_log, "\n")

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
    # the function turns `comlogs` from the single study folder `process.py`
    # set into the resolved list, so a list is the record that it has already
    # run for this options dict. calling it twice would take that list as the
    # study folder and nest it, and a command that calls another command as a
    # helper passes the same dict to both -- `fs.py`'s two FreeSurfer
    # segmentation commands call `check_for_freesurfer_data`, which is also a
    # command in its own right. guarding here rather than at each call site
    # keeps the callers from having to know which of them is the outer one
    if isinstance(options["comlogs"], list):
        return

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


def missing_report(_log, missing, message):
    """
    Note `message` and the files that are missing, one line each.
    """

    _say(_log, "step", message)
    for file in missing:
        _say(_log, "detail", file)


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
    comlog=None,
    verbose=True,
    overwrite=False,
    *,
    _log=None,
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
            _say(
                _log,
                "step",
                f"{command} test file [{os.path.basename(tfile)}] present",
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
                        missing_report(
                            _log,
                            filesmissing,
                            "Full file check revealed that the following files "
                            "were not created:",
                        )
                    report += ", full file check incomplete"
                    passed = "incomplete"
                    failed = 1
                else:
                    _say(_log, "step", "Full file check passed")
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

        # nothing to check against, so the comlog's contents are the evidence.
        # a comlog shared by a whole command (`combined_comlog`) holds
        # the calls before this one too, so an earlier error would fail this
        # call as well -- no caller combines the two today, and one that wants
        # to would have to scan from where its own call started
        if comlog is not None and log_has_errors(comlog.path):
            report = "%s not finished" % (command)
            passed = None
            failed = 1

    else:
        if verbose and tfile is not None:
            _say(_log, "step", f"{command} test file missing:")
            _say(_log, "info", tfile, depth=1)
        report = "%s not finished" % (command)
        passed = None
        failed = 1

    return passed, report, failed


def open_comlog(logfolder, task, logtags, thread, timestamp):
    """
    Open the comlog for one external call, and say where the copies go.

    `logfolder` is one folder or the list of them ``do_options_check`` builds:
    the first is where the comlog is written, the rest are where
    :func:`close_log` maps it once it is finished.

    Public because :func:`combined_comlog` opens one for a
    whole command rather than for one call, and the naming, the folder list and
    the settings check are the same job there.

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


def close_log(comlog, logfolders, status, remove, _log=None):
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
            _say(_log, "step", f"completed, comlog kept -- it reports errors: {tfile}")
        else:
            os.remove(tfile)
            _say(_log, "step", f"completed [{status}], comlog removed")
            return None

    _say(_log, "step", f"logfile: {tfile}")

    # -- do we have multiple logfolders?
    tname = os.path.basename(tfile)
    for logfolder in logfolders:
        nfile = os.path.join(logfolder, tname)
        try:
            os.makedirs(logfolder, exist_ok=True)
            gc.link_or_copy(tfile, nfile)
            _say(_log, "step", f"logfile: {nfile}")
        except Exception:
            _say(_log, "warning", f"could not map logfile to: {nfile}")

    return tfile


@contextlib.contextmanager
def combined_comlog(_log, options, command, thread=None):
    """
    One comlog for the whole command, instead of one per external call.

    A command that makes forty external calls used to leave forty comlogs,
    each a fragment of one run and each named after the tool rather than after
    the command. This opens a single comlog named for `command`, attaches it to
    `log` for the length of the block, and closes it once by how the block
    ended.

    Attachment is what does the work: :func:`run_external_for_file` takes the
    comlog attached to the log it is given and writes into it instead of
    opening and disposing of its own. Everything recorded on the log inside the
    block goes in too, so the file reads as the run rather than as one tool's
    stdout. The traffic is one way -- the report reaches the comlog, and no
    external output can reach the runlog, because
    ``general.log.ReportLog.trace`` writes to the comlog and never to the
    log's records.

    Nothing is opened under ``--test``: a dry run makes no external calls, so
    there is no output to keep and no file to leave behind.

    Retention is decided here rather than at each call site, which is what
    makes ``--log`` reach these commands at all::

        with pc.combined_comlog(log, options, "run_freesurfer_full_segmentation",
                                thread=sinfo["id"]):
            ...

    It lives here rather than on the log because opening a file, fanning it out
    to the study, session and hcp folders and applying a retention policy are
    things a run *does*; the log is a parameter to them, and `close_log`'s
    fan-out needs `general.core.link_or_copy`, which the log package must not
    reach for.

    Parameters:
        log: the command's report log, which the comlog is attached to.
        options: the command's options; ``comlogs``, ``logtag``, ``run`` and
            ``log`` are read.
        command: the command's name, which names the comlog.
        thread: the parallel thread, or the session being processed.

    Yields:
        the log it was given.
    """
    if options["run"] != "run":
        yield _log
        return

    comlog, logfolders = open_comlog(
        options["comlogs"], command, options["logtag"], thread, None
    )
    if comlog.path:
        print("You can follow the command's progress in:")
        print(comlog.path)
        print(gl.REPORT_RULE)

    started = _log.external_calls
    completed = False
    try:
        with _log.stream_to(comlog):
            yield _log
        completed = True
    finally:
        # written to the comlog directly: the block has ended, so the
        # attachment is gone, and this line belongs to the file rather than to
        # the report
        comlog.write(
            "\n\n---> %s at %s\n\n"
            % (
                "Successful completion" if completed else
                "An external command failed",
                datetime.now(),
            )
        )
        ran = _log.external_calls - started
        _log.step(f'ran {ran} external command{"" if ran == 1 else "s"}{"" if completed else " before failing"}')
        close_log(
            comlog,
            logfolders,
            "done" if completed else "error",
            options["log"] == "remove",
            _log,
        )

def run_external_for_file(
    checkfile,
    run,
    description,
    overwrite=False,
    thread="0",
    remove=True,
    task=None,
    logfolder="",
    logtags="",
    full_test=None,
    shell=True,
    verbose=True,
    comlog=None,
    *,
    _log=None,
):
    """
    ``run_external_for_file(checkfile, run, description, log=None, overwrite=False, thread="0", remove=True, task=None, logfolder="", logtags="", full_test=None, shell=True, verbose=True, comlog=None)``

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
    --comlog           An already open comlog to write into (ComContext).
                       Defaults to whatever is attached to `log`, which is what
                       a call inside a `combined_comlog` block picks up. When
                       given, the call joins that comlog instead of
                       opening one of its own, and neither opens nor closes a
                       file: `thread`, `remove`, `task`, `logfolder` and
                       `logtags` describe a comlog being opened and are then
                       unused, and `endlog` comes back as None because the file
                       is not finished here. Attached by `combined_comlog`,
                       which owns the comlog for the whole command.

    OUTPUTS
    =======

    --endlog        The path to the final log file.
    --status        Description of whether the command failed, is fully done or
                    incomplete based on the test files.
    --failed        0 for ok, 1 or more for failed or incomplete runs.
    """

    endlog = None

    # a log inside a `combined_comlog` block already holds the comlog this call
    # belongs in; the caller does not have to hand it over as well
    if comlog is None and _log is not None:
        comlog = _log.comlog

    # timestamp
    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")

    # -- Report command
    # header
    print_comm = gl.print_qunex_header(timestamp=logstamp)
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
        _note(_log, "\n\n%s" % (description))

        # a comlog handed in belongs to the caller: it is neither opened nor
        # closed here, and `endlog` stays None because the file is not finished
        shared = comlog is not None
        if shared:
            logfolders = []
            if _log is not None:
                _log.external_call()
        else:
            comlog, logfolders = open_comlog(logfolder, task, logtags, thread, logstamp)

            # --- report
            if comlog.path:
                print("You can follow command's progress in:")
                print(comlog.path)
                print("------------------------------------------------------------")

        def finish_comlog(status):
            """Close the comlog by `status`, unless the caller owns it."""
            if shared:
                return None
            return close_log(comlog, logfolders, status, remove, _log)

        with _streaming(_log, comlog):
            # add command call to start of the log
            _trace(_log, comlog, print_comm + "\n")

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
                finish_comlog("error")
                raise ExternalFailed(message)

            # --- check results
            if process.returncode != 0:
                message = "\n\nERROR: %s failed with error %s\n... \ncommand executed:\n%s" % (
                    description,
                    process.stderr.decode() if process.stderr else "Unknown error",
                    comm,
                )
                finish_comlog("error")
                raise ExternalFailed(message)

            status, _, failed = check_run(
                checkfile,
                full_test=full_test,
                command=task,
                _log=_log,
                comlog=comlog,
                verbose=verbose,
            )

            if status is None:
                _note(
                    _log,
                    "\n\nTry running the command directly for more detailed error information:\n"
                    + comm,
                )

            # --- End
            if status and status == "done":
                _trace(
                    _log,
                    comlog,
                    "\n\n---> Successful completion of task at %s\n\n"
                    % (datetime.now()),
                )
                endlog = finish_comlog("done")
            elif status and status == "incomplete":
                endlog = finish_comlog("incomplete")
            else:
                endlog = finish_comlog("error")

    else:
        if os.path.getsize(checkfile) < 100:
            endlog, status, failed = run_external_for_file(
                checkfile,
                run,
                description,
                overwrite=True,
                thread=thread,
                remove=remove,
                task=task,
                logfolder=logfolder,
                logtags=logtags,
                full_test=full_test,
                shell=shell,
                verbose=verbose,
                comlog=comlog,
                _log=_log,
            )
        else:
            status, _, failed = check_run(checkfile, full_test)
            if status in ["full", "done"]:
                _note(_log, "\n%s --- already completed" % (description))
            else:
                _note(_log, "\n%s --- already ran, incomplete file check" % (description))

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
    _log=None,
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

    _note(_log, "\n\n%s" % (description))

    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
    comlog, logfolders = open_comlog(logfolder, task, logtags, thread, logstamp)

    with _streaming(_log, comlog):
        _trace(
            _log,
            comlog,
            "\n#-------------------------------\n# Running: %s\n"
            "#-------------------------------\n" % (description),
        )

        with subprocess.Popen(
            run, shell=True, stdout=comlog.file, stderr=comlog.file
        ) as process:
            ret = process.wait()

        if ret:
            close_log(comlog, logfolders, "error", remove, _log)
            raise ExternalFailed("\n\nERROR: Failed with error %s\n" % (ret))

        _trace(
            _log,
            comlog,
            "\n\n---> Successful completion of task at %s\n\n" % (datetime.now()),
        )
        endlog = close_log(comlog, logfolders, "done", remove, _log)
        _note(_log, " --- done")

    return endlog


def check_for_file(
    checkfile, ok="", bad="", status=True, ok_level="detail", bad_level="detail",
    *, _log=None,
):
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
        ok_level (str): the level ``ok`` is recorded at.
        bad_level (str): the level ``bad`` is recorded at.

    Returns:
        bool: the running status.
    """
    if os.path.exists(checkfile):
        _say(_log, ok_level, ok)
        return status
    else:
        _say(_log, bad_level, bad)
        return False


def check_for_files(
    checkfiles, ok, bad, all=False, status=True, ok_level="detail",
    bad_level="detail", *, _log=None,
):
    """
    check_for_files - checks if any of the files in the checkfiles list exists

    If all parameter is set to True, returns True only if all files exist,
    if all parameter is False it returns the first found file.

    ``ok_level`` and ``bad_level`` name the level each message is recorded at,
    as in :func:`check_for_file`.

    Returns:
        tuple: ``(status, found)`` -- the running status and the first file
        found, when searching for any one of them.
    """

    for f in checkfiles:
        if os.path.exists(f):
            if not all:
                _say(_log, ok_level, ok)
                return status, f
        else:
            if all:
                _say(_log, bad_level, bad)
                return False, ""

    if not all:
        _say(_log, bad_level, bad)
        return False, ""

    # if we are here all files exist and all is set
    _say(_log, ok_level, ok)
    return status, ""
