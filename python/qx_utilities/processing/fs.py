#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``fs.py``

This file holds code for running legacy FreeSurfer preprocessing on NIL
preprocessed images. The specific functions are:

--run_basic_structural_segmentation
--check_for_freesurfer_data
--run_freesurfer_full_segmentation
--run_freesurfer_subcortical_segmentation

All the functions are part of the processing suite. They should be called
from the command line using `gmri` command. Help is available through:

- `gmri ?<command>` for command specific help
- `gmri -o` for a list of relevant arguments and options
"""

# Created by Grega Repovs on 2016-12-17.
# Code split from dofcMRIp_core gCodeP/preprocess codebase.
# Copyright (c) Grega Repovs. All rights reserved.

import contextlib
import os
import shutil
import time
import traceback
from datetime import datetime

import qx_utilities.general.core as gc
import qx_utilities.general.img as gi
import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog, action
from qx_utilities.processing.core import (
    ExternalFailed,
    NoSourceFolder,
    combined_comlog,
    do_options_check,
    get_file_names,
    get_session_folders,
    root4dfp,
)


def _run_external(_log, options, overwrite, checkfile, command, description):
    """
    Run one external command, or -- under ``--test`` -- report it and stop.

    All 41 external calls in this file write into the one comlog the command
    opened for itself (:func:`processing.core.combined_comlog`), so
    nothing here has to say where the comlog goes or whether to keep it: the
    ``with`` block at the top of each command decided both, once.

    The underlying call's ``(endlog, status, failed)`` is dropped, because no
    caller in this file has ever read it -- a failure arrives as
    ``ExternalFailed``, which the commands catch.
    """
    if options["run"] != "run":
        _log.raw(f"\n\n{description}")
        _log.detail(f"test, not run: {command}", depth=1)
        return

    pc.run_external_for_file(checkfile, command, description, overwrite=overwrite, _log=_log)


def _copy(_log, options, source, target, ifh=False):
    """
    Copy a file, or -- under ``--test`` -- report the copy and change nothing.

    `ifh` also copies the 4dfp header that sits beside the image, which is what
    every 4dfp copy in this file does.
    """
    if options["run"] != "run":
        _log.detail(f"test, not copied: {os.path.basename(source)}")
        return

    shutil.copy2(source, target)
    if ifh:
        shutil.copy2(source.replace(".img", ".ifh"), target.replace(".img", ".ifh"))


def run_basic_structural_segmentation(sinfo, options, overwrite=False, thread=0):
    """
    ``run_basic_structural_segmentation [... processing options]``

    Run basic structural segmentation (BET + FAST) on NIL preprocessed images.

    ..  qx_command:
        type: processing.session
        aliases: runBasicStructuralSegmentation

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder.

        --overwrite (str, default 'no'):
            Whether to overwrite existing outputs (yes) or not (no).

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

        --bet (str, default ''):
            Options passed to FSL BET.

        --fast (str, default ''):
            Options passed to FSL FAST.
    """
    log = ReportLog()
    do_options_check(options, sinfo, "run_basic_structural_segmentation")

    f = get_file_names(sinfo, options)
    log.rule()
    log.info(
        f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]"
    )
    log.action("Running", "basic structural segmentation ...", options["run"], level="info")

    try:
        with combined_comlog(
            log, options, "run_basic_structural_segmentation", thread=sinfo["id"]
        ):
            # --- copy structurals over
            copy = True
            if os.path.exists(f["t1"]):
                copy = False

            if overwrite or copy:
                if f["t1_source"] is None:
                    raise NoSourceFolder(
                        "ERROR: Data source folder is not set. Please check your paths!"
                    )
                log.detail(f"copying {f['t1_source']}")
                if options["image_target"] == "4dfp":
                    if gi.get_img_format(f["t1_source"]) == ".4dfp.img":
                        _copy(log, options, f["t1_source"], f["t1"], ifh=True)
                    else:
                        tmpfile = f["t1"].replace(
                            ".4dfp.img", gi.get_img_format(f["t1_source"])
                        )
                        _copy(log, options, f["t1_source"], tmpfile)
                        _run_external(
                            log, options, overwrite,
                            f["t1"],
                            "g_FlipFormat %s %s"
                            % (tmpfile, f["t1"].replace(".img", ".ifh")),
                            "... converting %s to 4dfp" % (os.path.basename(tmpfile)),
                        )
                        if options["run"] == "run":
                            os.remove(tmpfile)
                if options["image_target"] == "nifti":
                    if gi.get_img_format(f["t1_source"]) == ".4dfp.img":
                        tmpimg = f["t1"] + ".4dfp.img"
                        tmpifh = f["t1"] + ".4dfp.ifh"
                        _copy(log, options, f["t1_source"], tmpimg, ifh=True)
                        _run_external(
                            log, options, overwrite,
                            f["t1"],
                            "g_FlipFormat %s %s"
                            % (tmpifh, f["t1"].replace(".img", ".ifh")),
                            "... converting %s to NIfTI" % (os.path.basename(tmpimg)),
                        )
                        if options["run"] == "run":
                            os.remove(tmpimg)
                            os.remove(tmpifh)
                    else:
                        if gi.get_img_format(f["t1_source"]) == ".nii.gz":
                            tmpfile = f["t1"] + ".gz"
                            _copy(log, options, f["t1_source"], tmpfile)
                            _run_external(
                                log, options, overwrite,
                                f["t1"],
                                "gunzip -f %s" % (tmpfile),
                                "... gunzipping %s" % (os.path.basename(tmpfile)),
                            )
                            if os.path.exists(tmpfile):
                                os.remove(tmpfile)
                        else:
                            _copy(log, options, f["t1_source"], f["t1"])

            else:
                log.detail(f"{f['t1']} file present")

            # --- convert to NIfTI
            sfile = f["t1"]
            tfileb = f["t1_brain"].replace(gi.get_img_format(f["t1_brain"]), ".nii")
            tfiles = f["t1_seg"].replace(gi.get_img_format(f["t1_seg"]), ".nii")

            if gi.get_img_format(f["t1"]) == ".4dfp.img":
                sfile = sfile.replace(".4dfp.img", ".nii")
                _run_external(
                    log, options, overwrite,
                    sfile,
                    "g_FlipFormat %s %s" % (f["t1"].replace(".img", ".ifh"), sfile),
                    "... converting %s to NIfTI" % (os.path.basename(f["t1"])),
                )

            # --- run BET
            if os.path.exists(tfileb):
                log.detail(f"bet on {os.path.basename(sfile)} already done")
            else:
                _run_external(
                    log, options, overwrite,
                    tfileb + ".gz",
                    "bet %s %s %s" % (sfile, tfileb, options["bet"]),
                    "... running BET on %s with options %s"
                    % (os.path.basename(sfile), options["bet"]),
                )
                _run_external(
                    log, options, overwrite,
                    tfileb,
                    "gunzip -f %s.gz" % (tfileb),
                    "gunzipping %s.gz" % (os.path.basename(tfileb)),
                )

            # --- run FAST
            if os.path.exists(tfiles):
                log.detail(f"fast on {os.path.basename(tfiles)} already done")
            else:
                _run_external(
                    log, options, overwrite,
                    tfiles + ".gz",
                    "fast %s -o %s %s"
                    % (options["fast"], tfiles.replace("_seg.nii", ""), tfileb),
                    "... running FAST on %s with options %s"
                    % (os.path.basename(tfileb), options["fast"]),
                )
                _run_external(
                    log, options, overwrite,
                    tfiles,
                    "gunzip -f %s.gz" % (tfiles),
                    "... gunzipping %s.gz" % (os.path.basename(tfiles)),
                )

            # --- convert to 4dfp if needed
            if gi.get_img_format(f["t1"]) == ".4dfp.img":
                _run_external(
                    log, options, overwrite,
                    f["t1_brain"],
                    "g_FlipFormat %s %s" % (tfileb, f["t1_brain"].replace(".img", ".ifh")),
                    "... converting %s to 4dfp" % (os.path.basename(tfileb)),
                )
                _run_external(
                    log, options, overwrite,
                    f["t1_seg"],
                    "g_FlipFormat %s %s" % (tfiles, f["t1_seg"].replace(".img", ".ifh")),
                    "... converting %s to 4dfp" % (os.path.basename(tfiles)),
                )

    except (ExternalFailed, NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        log.info(
            f"Basic structural segmentation failed on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}\n---------------------------------------------------------"
        )
        return log.result("Basic structural segmentation failed", 1, sinfo["id"])
    except Exception:
        log.error(
            f"Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n"
        )
        time.sleep(15)
        return log.finish("Basic structural segmentation failed", name=sinfo["id"])

    log.info(
        f"{action('Basic structural segmentation completed', options['run'])} on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}\n---------------------------------------------------------"
    )

    return log.finish(
        action("Basic structural segmentation completed", options["run"]),
        name=sinfo["id"],
    )


#
#   --- Check for existing FreeSurfer data
#
def check_for_freesurfer_data(sinfo, options, overwrite=False, thread=0, _log=None):
    """
    ``check_for_freesurfer_data [... processing options]``

    Check for (and optionally copy) existing FreeSurfer outputs into the
    session folder.

    ..  qx_command:
        type: processing.session
        aliases: checkForFreeSurferData

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder.

        --overwrite (str, default 'no'):
            Whether to overwrite existing outputs (yes) or not (no).

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

        --path_freesurfer (str, default ''):
            Path template to a precomputed FreeSurfer directory (supports
            replacing "[sid]" with session id).

        --path_aseg_t1 (str, default ''):
            Path template to an aseg segmentation in T1 space.

        --path_aparc_t1 (str, default ''):
            Path template to an aparc+aseg segmentation in T1 space.
    """
    # `_log` is the log of the command this is a step of, when it is one: the
    # two FreeSurfer segmentation commands call it before doing their own work.
    # A step reports into that command's log rather than into one of its own --
    # so it needs no header, and its external calls go to the comlog that
    # command already opened, leaving one comlog for the run rather than two
    log = _log if _log is not None else ReportLog()
    verbose = _log is None
    do_options_check(options, sinfo, "check_for_freesurfer_data")

    comlog = (
        combined_comlog(log, options, "check_for_freesurfer_data", thread=sinfo["id"])
        if verbose
        else contextlib.nullcontext()
    )

    def check_path(p, sid):
        p = p.replace("[sid]", sid)
        if os.path.exists(p):
            return p
        else:
            if d["s_source"] is not None:
                tp = os.path.join(d["s_source"], p)
                if os.path.exists(tp):
                    return tp
            elif "path_freesurfer" in options:
                tf = options["path_freesurfer"].replace("[sid]", sid)
                tp = os.path.join(tf, p)
                if os.path.exists(tp):
                    return tp
        return False

    try:
        with comlog:
            d = get_session_folders(sinfo, options)
            f = get_file_names(sinfo, options)

            if verbose:
                log.rule()
                log.info(
                    f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]"
                )
                log.action(
                    "Checking",
                    "for existing freesurfer data ...",
                    options["run"],
                    level="info",
                )

            # check for freesurfer folder
            if not os.path.exists(f["fs_aseg_mgz"]) or overwrite:
                if "path_freesurfer" in options:
                    fspath = options["path_freesurfer"].replace("[sid]", sinfo["id"])
                    log.detail(f"looking for: {fspath}")
                    if os.path.exists(fspath):
                        if options["run"] != "run":
                            # the only destructive step in this file: it removes an
                            # existing FreeSurfer folder before replacing it, so a
                            # test run must not reach it
                            log.detail(
                                f"test, not copied: existing FreeSurfer data from {fspath}"
                            )
                        else:
                            if os.path.exists(d["s_fs"]):
                                shutil.rmtree(d["s_fs"])
                            try:
                                shutil.copytree(fspath, d["s_fs"])
                            except Exception:
                                log.detail("copy reported an error, please check data!")
                            log.detail(
                                f"copied existing FreeSurfer data from {fspath} to target folder"
                            )
                else:
                    log.detail("no freesurfer path in options.")
            else:
                log.detail("data already there.")

            # check for specific freesurfer file options
            fsfiles = [
                ("path_aseg_t1", "fs_aseg_t1"),
                ("path_aseg_bold", "fs_aseg_bold"),
                ("path_aparc_t1", "fs_aparc_t1"),
                ("path_aparc_bold", "fs_aparc_bold"),
            ]
            for s, t in fsfiles:
                if not os.path.exists(f[t]) or overwrite:
                    if s in options:
                        sf = check_path(options[s], sinfo["id"])
                        if sf:
                            tf = f[t].replace(
                                gi.get_img_format(f[t]), gi.get_img_format(sf)
                            )
                            _copy(
                                log,
                                options,
                                sf,
                                tf,
                                ifh=gi.get_img_format(sf) == ".4dfp.img",
                            )
                            log.detail(
                                f"copied {os.path.basename(sf)} to target folder"
                            )
                            if tf != f[t]:
                                if options["image_target"] == "4dfp":
                                    _run_external(
                                        log, options, overwrite,
                                        f[t],
                                        "g_FlipFormat %s %s"
                                        % (tf, f[t].replace(".img", ".ifh")),
                                        "... converting %s to 4dfp"
                                        % (os.path.basename(tf)),
                                    )
                                elif gi.get_img_format(tf) == ".nii.gz":
                                    _run_external(
                                        log, options, overwrite,
                                        f[t],
                                        "gunzip -f %s" % (tf),
                                        "... gunzipping %s " % (os.path.basename(tf)),
                                    )
                                else:
                                    _run_external(
                                        log, options, overwrite,
                                        f[t],
                                        "g_FlipFormat %s %s"
                                        % (tf.replace(".img", ".ifh"), f[t]),
                                        "... converting %s to nifti"
                                        % (os.path.basename(tf)),
                                    )

    except Exception:
        log.error(
            f"Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n"
        )
        time.sleep(1)
        return log.finish("Check for FreeSurfer data failed", name=sinfo["id"])

    if not verbose:
        # a step of another command: that command states the outcome, and
        # summarising over its log here would only be overwritten
        return log

    log.info(
        f"{action('Check completed', options['run'])} on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}\n---------------------------------------------------------"
    )

    return log.finish(
        action("Check for FreeSurfer data completed", options["run"]),
        name=sinfo["id"],
    )


#
#   --- Run FreeSurfer segmentation
#
def run_freesurfer_full_segmentation(sinfo, options, overwrite=False, thread=0):
    """
    ``run_freesurfer_full_segmentation [... processing options]``

    Run full FreeSurfer segmentation on NIL preprocessed images.

    ..  qx_command:
        type: processing.session
        aliases: runFreeSurferFullSegmentation

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder.

        --overwrite (str, default 'no'):
            Whether to overwrite existing outputs (yes) or not (no).

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.
    """
    log = ReportLog()
    do_options_check(options, sinfo, "run_freesurfer_full_segmentation")

    try:
        with combined_comlog(
            log, options, "run_freesurfer_full_segmentation", thread=sinfo["id"]
        ):
            log.rule()
            log.info(
                f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]"
            )
            log.action(
                "Running", "Full FreeSurfer segmentation ...", options["run"], level="info"
            )

            # check if any data already exists
            check_for_freesurfer_data(sinfo, options, overwrite, thread, log)

            d = get_session_folders(sinfo, options)
            f = get_file_names(sinfo, options)

            # --- check if we need to run fsf
            if (
                os.path.exists(f["fs_aseg_nii"]) and os.path.exists(f["fs_aparc+aseg_nii"])
            ) or (os.path.exists(f["fs_aseg_t1"]) and os.path.exists(f["fs_aparc_t1"])):
                log.detail("FreeSurfer run already completed!")

            else:
                # --- copy file over
                if not os.path.exists(f["t1"]):
                    _copy(
                        log,
                        options,
                        f["t1_source"],
                        f["t1"],
                        ifh=gi.get_img_format(f["t1_source"]) == ".4dfp.img",
                    )
                    log.detail(
                        f"copied {os.path.basename(f['t1_source'])} to target folder"
                    )

                # --- convert to NIfTI
                onifti = f["t1"]
                if gi.get_img_format(onifti) == ".4dfp.img":
                    onifti = f["t1"].replace(".4dfp.img", ".nii")
                    _run_external(
                        log, options, overwrite,
                        onifti,
                        "g_FlipFormat %s %s" % (f["t1"].replace(".img", ".ifh"), onifti),
                        "... converting %s to NIfTI" % (os.path.basename(f["t1"])),
                    )

                # --- convert to MGZ
                _run_external(
                    log, options, overwrite,
                    f["fs_morig_mgz"],
                    "mri_convert --in_type nii %s %s" % (onifti, f["fs_morig_mgz"]),
                    "... converting %s to MGZ" % (os.path.basename(onifti)),
                )

                # --- run FreeSurfer Subcortical
                _run_external(
                    log, options, overwrite,
                    f["fs_aseg_mgz"],
                    "recon-all -sd %s -subjid freesurfer -motioncor -nuintensitycor -talairach -normalization -skullstrip -subcortseg -segstats -no-isrunning"
                    % (d["s_seg"]),
                    "... running subcortical FreeSurfer segmentation",
                )

                # --- run FreeSurfer surface registration
                _run_external(
                    log, options, overwrite,
                    f["fs_aparc+aseg_mgz"],
                    "recon-all -sd %s -subjid freesurfer -maskbfs -normalization2 -segmentation -fill -tessellate -smooth1 -inflate1 -qsphere -fix -finalsurfs -smooth2 -inflate2 -cortribbon -sphere -surfreg -contrasurfreg -avgcurv -cortparc -parcstats -cortparc2 -parcstats2 -aparc2aseg -no-isrunning"
                    % (d["s_seg"]),
                    "... running FreeSurfer surface processing",
                )

                # --- convert segmentations to nifti
                _run_external(
                    log, options, overwrite,
                    f["fs_aseg_nii"],
                    "mri_convert -i %s -ot nii %s" % (f["fs_aseg_mgz"], f["fs_aseg_nii"]),
                    "... converting %s to NIfTI" % (f["fs_aseg_mgz"]),
                )
                _run_external(
                    log, options, overwrite,
                    f["fs_aparc+aseg_nii"],
                    "mri_convert -i %s -ot nii %s"
                    % (f["fs_aparc+aseg_mgz"], f["fs_aparc+aseg_nii"]),
                    "... converting %s to NIfTI" % (f["fs_aparc+aseg_mgz"]),
                )

            if options["image_target"] == "nifti":
                if not os.path.exists(f["fs_aseg_t1"]):
                    gc.link_or_copy(f["fs_aseg_nii"], f["fs_aseg_t1"])
                if not os.path.exists(f["fs_aparc_t1"]):
                    gc.link_or_copy(f["fs_aparc+aseg_nii"], f["fs_aparc_t1"])

            # --- 4dfp path
            if options["image_target"] == "4dfp" or options["image_atlas"] == "711":
                # --- check for aseg
                if not os.path.exists(f["fs_aseg_t1"]):
                    if not os.path.exists(f["fs_aseg_4dfp"]):
                        _run_external(
                            log, options, overwrite,
                            f["fs_aseg_4dfp"],
                            'g_FlipFormat -c "129.000 -108.000 -142.000" %s %s'
                            % (f["fs_aseg_nii"], f["fs_aseg_4dfp"].replace(".img", ".ifh")),
                            "... converting %s to 4dfp"
                            % (os.path.basename(f["fs_aseg_nii"])),
                        )
                    _run_external(
                        log, options, overwrite,
                        f["fs_aseg_t1"],
                        "t4img_4dfp none %s %s -O111 -@b"
                        % (root4dfp(f["fs_aseg_4dfp"]), root4dfp(f["fs_aseg_t1"])),
                        "... converting %s to 111 space" % (f["fs_aseg_4dfp"]),
                    )

                _run_external(
                    log, options, overwrite,
                    f["fs_aseg_bold"],
                    "t4img_4dfp none %s %s -O333 -n -@b"
                    % (root4dfp(f["fs_aseg_t1"]), root4dfp(f["fs_aseg_bold"])),
                    "... converting %s to 333 space" % (f["fs_aseg_4dfp"]),
                )

                # --- check for aparc
                if not os.path.exists(f["fs_aparc_t1"]):
                    if not os.path.exists(f["fs_aparc+aseg_4dfp"]):
                        _run_external(
                            log, options, overwrite,
                            f["fs_aparc+aseg_4dfp"],
                            'g_FlipFormat -c "129.000 -108.000 -142.000" %s %s'
                            % (
                                f["fs_aparc+aseg_nii"],
                                f["fs_aparc+aseg_4dfp"].replace(".img", ".ifh"),
                            ),
                            "... converting %s to 4dfp"
                            % (os.path.basename(f["fs_aparc+aseg_nii"])),
                        )
                    _run_external(
                        log, options, overwrite,
                        f["fs_aparc_t1"],
                        "t4img_4dfp none %s %s -O111 -@b"
                        % (root4dfp(f["fs_aparc+aseg_4dfp"]), root4dfp(f["fs_aparc_t1"])),
                        "... converting %s to 111 space" % (f["fs_aparc+aseg_4dfp"]),
                    )

                _run_external(
                    log, options, overwrite,
                    f["fs_aparc_bold"],
                    "t4img_4dfp none %s %s -O333 -n -@b"
                    % (root4dfp(f["fs_aparc_t1"]), root4dfp(f["fs_aparc_bold"])),
                    "... converting %s to 333 space" % (f["fs_aparc_t1"]),
                )

                # --- check if we need to convert to nifti
                if options["image_atlas"] == "711" and options["image_target"] == "nifti":
                    # --- convert 111 4dfp to nifti
                    _run_external(
                        log, options, overwrite,
                        f["fs_aseg_t1"],
                        "g_FlipFormat %s %s"
                        % (f["fs_aseg_111"].replace(".img", ".ifh"), f["fs_aseg_t1"]),
                        "... converting %s to nifti" % (os.path.basename(f["fs_aseg_111"])),
                    )
                    _run_external(
                        log, options, overwrite,
                        f["fs_aparc_t1"],
                        "g_FlipFormat %s %s"
                        % (
                            f["fs_aparc+aseg_111"].replace(".img", ".ifh"),
                            f["fs_aparc_t1"],
                        ),
                        "... converting %s to nifti"
                        % (os.path.basename(f["fs_aparc+aseg_111"])),
                    )

                    # --- convert 333 4dfp to nifti
                    _run_external(
                        log, options, overwrite,
                        f["fs_aseg_bold"],
                        "g_FlipFormat %s %s"
                        % (f["fs_aseg_333"].replace(".img", ".ifh"), f["fs_aseg_bold"]),
                        "... converting %s to nifti" % (os.path.basename(f["fs_aseg_333"])),
                    )
                    _run_external(
                        log, options, overwrite,
                        f["fs_aparc_bold"],
                        "g_FlipFormat %s %s"
                        % (
                            f["fs_aparc+aseg_333"].replace(".img", ".ifh"),
                            f["fs_aparc_bold"],
                        ),
                        "... converting %s to nifti"
                        % (os.path.basename(f["fs_aparc+aseg_333"])),
                    )

            if options["image_atlas"] != "711" and options["image_target"] == "nifti":
                if os.path.exists(f["bold_template"]):
                    # --- convert t1 segmentation to bold space
                    _run_external(
                        log, options, overwrite,
                        f["fs_aseg_bold"],
                        "3dresample -rmode NN -master %s -inset %s -prefix %s "
                        % (f["bold_template"], f["fs_aseg_t1"], f["fs_aseg_bold"]),
                        "... resampling t1 subcortical segmentation (%s) to bold space (%s)"
                        % (
                            os.path.basename(f["fs_aseg_t1"]),
                            os.path.basename(f["fs_aseg_bold"]),
                        ),
                    )
                    _run_external(
                        log, options, overwrite,
                        f["fs_aparc_bold"],
                        "3dresample -rmode NN -master %s -inset %s -prefix %s "
                        % (f["bold_template"], f["fs_aparc_t1"], f["fs_aparc_bold"]),
                        "... resampling t1 cortical segmentation (%s) to bold space (%s)"
                        % (
                            os.path.basename(f["fs_aparc_t1"]),
                            os.path.basename(f["fs_aparc_bold"]),
                        ),
                    )
                else:
                    log.raw(
                        "ERROR: bold template image is missing! Please run bbm (create brain masks for BOLD runs) and then rerun fsf to complete the last step!"
                    )

    except (ExternalFailed, NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        log.info(
            f"FreeSurfer segmentation failed on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}\n---------------------------------------------------------"
        )
        return log.result("FreeSurfer segmentation failed", 1, sinfo["id"])
    except Exception:
        log.error(
            f"Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n"
        )
        time.sleep(15)
        return log.finish("FreeSurfer segmentation failed", name=sinfo["id"])

    log.info(
        f"{action('FreeSurfer segmentation completed', options['run'])} on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}\n---------------------------------------------------------"
    )

    return log.finish(
        action("FreeSurfer segmentation completed", options["run"]),
        name=sinfo["id"],
    )


def run_freesurfer_subcortical_segmentation(sinfo, options, overwrite=False, thread=0):
    """
    ``run_freesurfer_subcortical_segmentation [... processing options]``

    Run subcortical-only FreeSurfer segmentation on NIL preprocessed images.

    ..  qx_command:
        type: processing.session
        aliases: runFreeSurferSubcorticalSegmentation

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder.

        --overwrite (str, default 'no'):
            Whether to overwrite existing outputs (yes) or not (no).

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.
    """
    log = ReportLog()
    do_options_check(options, sinfo, "run_freesurfer_subcortical_segmentation")
    try:
        with combined_comlog(
            log, options, "run_freesurfer_subcortical_segmentation", thread=sinfo["id"]
        ):
            log.rule()
            log.info(
                f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]"
            )
            log.action(
                "Running",
                "subcortical only FreeSurfer segmentation ...",
                options["run"],
                level="info",
            )

            # check if any data already exists
            check_for_freesurfer_data(sinfo, options, overwrite, thread, log)

            d = get_session_folders(sinfo, options)
            f = get_file_names(sinfo, options)

            # --- check if we need to run fsf
            if os.path.exists(f["fs_aseg_nii"]):
                log.detail("FreeSurfer run already completed!")

            else:
                # --- copy file over
                if not os.path.exists(f["t1"]):
                    _copy(
                        log,
                        options,
                        f["t1_source"],
                        f["t1"],
                        ifh=gi.get_img_format(f["t1_source"]) == ".4dfp.img",
                    )
                    log.detail(
                        f"copied {os.path.basename(f['t1_source'])} to target folder"
                    )

                # --- convert to NIfTI
                onifti = f["t1"]
                if gi.get_img_format(onifti) == ".4dfp.img":
                    onifti = f["t1"].replace(".4dfp.img", ".nii")
                    _run_external(
                        log, options, overwrite,
                        onifti,
                        "g_FlipFormat %s %s" % (f["t1"].replace(".img", ".ifh"), onifti),
                        "... converting %s to NIfTI" % (os.path.basename(f["t1"])),
                    )

                # --- convert to MGZ
                _run_external(
                    log, options, overwrite,
                    f["fs_morig_mgz"],
                    "mri_convert --in_type nii %s %s" % (onifti, f["fs_morig_mgz"]),
                    "... converting %s to MGZ" % (os.path.basename(onifti)),
                )

                # --- run FreeSurfer Subcortical
                _run_external(
                    log, options, overwrite,
                    f["fs_aseg_mgz"],
                    "recon-all -sd %s -subjid freesurfer -motioncor -nuintensitycor -talairach -normalization -skullstrip -subcortseg -segstats -no-isrunning"
                    % (d["s_seg"]),
                    "... running subcortical FreeSurfer segmentation",
                )

                # --- convert segmentations to nifti
                _run_external(
                    log, options, overwrite,
                    f["fs_aseg_nii"],
                    "mri_convert -i %s -ot nii %s" % (f["fs_aseg_mgz"], f["fs_aseg_nii"]),
                    "... converting %s to NIfTI" % (f["fs_aseg_mgz"]),
                )

            if options["image_target"] == "nifti":
                if not os.path.exists(f["fs_aseg_t1"]):
                    gc.link_or_copy(f["fs_aseg_nii"], f["fs_aseg_t1"])

            # --- 4dfp path
            if options["image_target"] == "4dfp" or options["image_atlas"] == "711":
                # --- convert to 4dfp
                _run_external(
                    log, options, overwrite,
                    f["fs_aseg_4dfp"],
                    'g_FlipFormat -c "129.000 -108.000 -142.000" %s %s'
                    % (f["fs_aseg_nii"], f["fs_aseg_4dfp"].replace(".img", ".ifh")),
                    "... converting %s to 4dfp" % (os.path.basename(f["fs_aseg_nii"])),
                )

                # --- convert to 111
                _run_external(
                    log, options, overwrite,
                    f["fs_aseg_111"],
                    "t4img_4dfp none %s %s -O111 -@b"
                    % (root4dfp(f["fs_aseg_4dfp"]), root4dfp(f["fs_aseg_111"])),
                    "... converting %s to 111 space" % (f["fs_aseg_4dfp"]),
                )

                # --- convert to 333
                _run_external(
                    log, options, overwrite,
                    f["fs_aseg_333"],
                    "t4img_4dfp none %s %s -O333 -n -@b"
                    % (root4dfp(f["fs_aseg_4dfp"]), root4dfp(f["fs_aseg_333"])),
                    "... converting %s to 333 space" % (f["fs_aseg_4dfp"]),
                )

                if options["image_atlas"] == "711" and options["image_target"] == "nifti":
                    # --- convert 111 4dfp to nifti
                    _run_external(
                        log, options, overwrite,
                        f["fs_aseg_t1"],
                        "g_FlipFormat %s %s"
                        % (f["fs_aseg_111"].replace(".img", ".ifh"), f["fs_aseg_t1"]),
                        "... converting %s to nifti" % (os.path.basename(f["fs_aseg_111"])),
                    )

                    # --- convert 333 4dfp to nifti
                    _run_external(
                        log, options, overwrite,
                        f["fs_aseg_bold"],
                        "g_FlipFormat %s %s"
                        % (f["fs_aseg_333"].replace(".img", ".ifh"), f["fs_aseg_bold"]),
                        "... converting %s to nifti" % (os.path.basename(f["fs_aseg_333"])),
                    )

            if options["image_atlas"] != "711" and options["image_target"] == "nifti":
                if os.path.exists(f["bold_template"]):
                    # --- convert t1 segmentation to bold space
                    _run_external(
                        log, options, overwrite,
                        f["fs_aseg_bold"],
                        "3dresample -rmode NN -master %s -inset %s -prefix %s "
                        % (f["bold_template"], f["fs_aseg_t1"], f["fs_aseg_bold"]),
                        "... resampling t1 subcortical segmentation (%s) to bold space (%s)"
                        % (
                            os.path.basename(f["fs_aseg_t1"]),
                            os.path.basename(f["fs_aseg_bold"]),
                        ),
                    )
                else:
                    log.raw(
                        "ERROR: bold template image is missing! Please run bbm (create brain masks for BOLD runs) and then rerun fsf to complete the last step!"
                    )

    except (ExternalFailed, NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        log.info(
            f"FreeSurfer segmentation failed on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}\n---------------------------------------------------------"
        )
        return log.result("FreeSurfer segmentation failed", 1, sinfo["id"])
    except Exception:
        log.error(
            f"Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n"
        )
        time.sleep(15)
        return log.finish("FreeSurfer segmentation failed", name=sinfo["id"])

    log.info(
        f"{action('FreeSurfer segmentation completed', options['run'])} on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}\n---------------------------------------------------------"
    )

    return log.finish(
        action("FreeSurfer segmentation completed", options["run"]),
        name=sinfo["id"],
    )
