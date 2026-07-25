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

import os
import shutil
import time
import traceback
from datetime import datetime

import qx_utilities.general.core as gc
import qx_utilities.general.img as gi
from qx_utilities.general.log import ReportLog
from qx_utilities.processing.core import (
    ExternalFailed,
    NoSourceFolder,
    get_file_names,
    get_session_folders,
    root4dfp,
)


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

    f = get_file_names(sinfo, options)
    log.capture("\n---------------------------------------------------------")
    log.raw(
        "\nSession id: %s \n[started on %s]"
        % (sinfo["id"], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    )
    log.raw("\nRunning basic structural segmentation ...")

    try:
        # --- copy structurals over
        copy = True
        if os.path.exists(f["t1"]):
            copy = False

        if overwrite or copy:
            if f["t1_source"] is None:
                raise NoSourceFolder(
                    "ERROR: Data source folder is not set. Please check your paths!"
                )
            log.raw("\n... copying %s" % (f["t1_source"]))
            if options["image_target"] == "4dfp":
                if gi.get_img_format(f["t1_source"]) == ".4dfp.img":
                    shutil.copy2(f["t1_source"], f["t1"])
                    shutil.copy2(
                        f["t1_source"].replace(".img", ".ifh"),
                        f["t1"].replace(".img", ".ifh"),
                    )
                else:
                    tmpfile = f["t1"].replace(
                        ".4dfp.img", gi.get_img_format(f["t1_source"])
                    )
                    shutil.copy2(f["t1_source"], tmpfile)
                    endlog, status, failed = log.run_external(
                        f["t1"],
                        "g_FlipFormat %s %s"
                        % (tmpfile, f["t1"].replace(".img", ".ifh")),
                        "... converting %s to 4dfp" % (os.path.basename(tmpfile)),
                        overwrite=overwrite,
                        thread=sinfo["id"],
                        logfolder=options["comlogs"],
                        logtags=options["logtag"],
                    )
                    os.remove(tmpfile)
            if options["image_target"] == "nifti":
                if gi.get_img_format(f["t1_source"]) == ".4dfp.img":
                    tmpimg = f["t1"] + ".4dfp.img"
                    tmpifh = f["t1"] + ".4dfp.ifh"
                    shutil.copy2(f["t1_source"], tmpimg)
                    shutil.copy2(f["t1_source"].replace(".img", ".ifh"), tmpifh)
                    endlog, status, failed = log.run_external(
                        f["t1"],
                        "g_FlipFormat %s %s"
                        % (tmpifh, f["t1"].replace(".img", ".ifh")),
                        "... converting %s to NIfTI" % (os.path.basename(tmpimg)),
                        overwrite=overwrite,
                        thread=sinfo["id"],
                        logfolder=options["comlogs"],
                        logtags=options["logtag"],
                    )
                    os.remove(tmpimg)
                    os.remove(tmpifh)
                else:
                    if gi.get_img_format(f["t1_source"]) == ".nii.gz":
                        tmpfile = f["t1"] + ".gz"
                        shutil.copy2(f["t1_source"], tmpfile)
                        endlog, status, failed = log.run_external(
                            f["t1"],
                            "gunzip -f %s" % (tmpfile),
                            "... gunzipping %s" % (os.path.basename(tmpfile)),
                            overwrite=overwrite,
                            thread=sinfo["id"],
                            logfolder=options["comlogs"],
                            logtags=options["logtag"],
                        )
                        if os.path.exists(tmpfile):
                            os.remove(tmpfile)
                    else:
                        shutil.copy2(f["t1_source"], f["t1"])

        else:
            log.raw("\n... %s file present" % (f["t1"]))

        # --- convert to NIfTI
        sfile = f["t1"]
        tfileb = f["t1_brain"].replace(gi.get_img_format(f["t1_brain"]), ".nii")
        tfiles = f["t1_seg"].replace(gi.get_img_format(f["t1_seg"]), ".nii")

        if gi.get_img_format(f["t1"]) == ".4dfp.img":
            sfile = sfile.replace(".4dfp.img", ".nii")
            endlog, status, failed = log.run_external(
                sfile,
                "g_FlipFormat %s %s" % (f["t1"].replace(".img", ".ifh"), sfile),
                "... converting %s to NIfTI" % (os.path.basename(f["t1"])),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

        # --- run BET
        if os.path.exists(tfileb):
            log.raw("\n... bet on %s already done" % (os.path.basename(sfile)))
        else:
            endlog, status, failed = log.run_external(
                tfileb + ".gz",
                "bet %s %s %s" % (sfile, tfileb, options["bet"]),
                "... running BET on %s with options %s"
                % (os.path.basename(sfile), options["bet"]),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )
            endlog, status, failed = log.run_external(
                tfileb,
                "gunzip -f %s.gz" % (tfileb),
                "gunzipping %s.gz" % (os.path.basename(tfileb)),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

        # --- run FAST
        if os.path.exists(tfiles):
            log.raw("\n... fast on %s already done" % (os.path.basename(tfiles)))
        else:
            endlog, status, failed = log.run_external(
                tfiles + ".gz",
                "fast %s -o %s %s"
                % (options["fast"], tfiles.replace("_seg.nii", ""), tfileb),
                "... running FAST on %s with options %s"
                % (os.path.basename(tfileb), options["fast"]),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )
            endlog, status, failed = log.run_external(
                tfiles,
                "gunzip -f %s.gz" % (tfiles),
                "... gunzipping %s.gz" % (os.path.basename(tfiles)),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

        # --- convert to 4dfp if needed
        if gi.get_img_format(f["t1"]) == ".4dfp.img":
            endlog, status, failed = log.run_external(
                f["t1_brain"],
                "g_FlipFormat %s %s" % (tfileb, f["t1_brain"].replace(".img", ".ifh")),
                "... converting %s to 4dfp" % (os.path.basename(tfileb)),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )
            endlog, status, failed = log.run_external(
                f["t1_seg"],
                "g_FlipFormat %s %s" % (tfiles, f["t1_seg"].replace(".img", ".ifh")),
                "... converting %s to 4dfp" % (os.path.basename(tfiles)),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

    except (ExternalFailed, NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        log.raw(
            "\nBasic structural segmentation failed on %s\n---------------------------------------------------------"
            % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        )
        print(log.text)
        return log.text
    except Exception:
        log.raw(
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        time.sleep(15)
        print(log.text)
        return log.text

    log.raw(
        "\nBasic structural segmentation completed on %s\n---------------------------------------------------------"
        % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    )

    print(log.text)
    return log.text


#
#   --- Check for existing FreeSurfer data
#
def check_for_freesurfer_data(sinfo, options, overwrite=False, thread=0, r=False):
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
    log = ReportLog()

    if not log.text:
        verbose = True
    else:
        verbose = False

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
        d = get_session_folders(sinfo, options)
        f = get_file_names(sinfo, options)

        if verbose:
            log.capture("\n---------------------------------------------------------")
            log.raw(
                "\nSession id: %s \n[started on %s]"
                % (sinfo["id"], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
            )
            log.raw("\nChecking for existing freesurfer data ...")

        # check for freesurfer folder
        if not os.path.exists(f["fs_aseg_mgz"]) or overwrite:
            if "path_freesurfer" in options:
                fspath = options["path_freesurfer"].replace("[sid]", sinfo["id"])
                log.raw("\n... looking for: %s" % (fspath))
                if os.path.exists(fspath):
                    if os.path.exists(d["s_fs"]):
                        shutil.rmtree(d["s_fs"])
                    try:
                        shutil.copytree(fspath, d["s_fs"])
                    except Exception:
                        log.raw("\n... copy reported an error, please check data!")
                    log.raw(
                        "\n... copied existing FreeSurfer data from %s to target folder"
                        % (fspath)
                    )
            else:
                log.raw("\n... no freesurfer path in options.")
        else:
            log.raw("\n... data already there.")

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
                        shutil.copy2(sf, tf)
                        if gi.get_img_format(sf) == ".4dfp.img":
                            shutil.copy2(
                                sf.replace(".img", ".ifh"), tf.replace(".img", ".ifh")
                            )
                        log.raw(
                            "\n... copied %s to target folder" % (os.path.basename(sf))
                        )
                        if tf != f[t]:
                            if options["image_target"] == "4dfp":
                                endlog, status, failed = log.run_external(
                                    f[t],
                                    "g_FlipFormat %s %s"
                                    % (tf, f[t].replace(".img", ".ifh")),
                                    "... converting %s to 4dfp"
                                    % (os.path.basename(tf)),
                                    overwrite=overwrite,
                                    thread=sinfo["id"],
                                    logfolder=options["comlogs"],
                                    logtags=options["logtag"],
                                )
                            elif gi.get_img_format(tf) == ".nii.gz":
                                endlog, status, failed = log.run_external(
                                    f[t],
                                    "gunzip -f %s" % (tf),
                                    "... gunzipping %s " % (os.path.basename(tf)),
                                    overwrite=overwrite,
                                    thread=sinfo["id"],
                                    logfolder=options["comlogs"],
                                    logtags=options["logtag"],
                                )
                            else:
                                endlog, status, failed = log.run_external(
                                    f[t],
                                    "g_FlipFormat %s %s"
                                    % (tf.replace(".img", ".ifh"), f[t]),
                                    "... converting %s to nifti"
                                    % (os.path.basename(tf)),
                                    overwrite=overwrite,
                                    thread=sinfo["id"],
                                    logfolder=options["comlogs"],
                                    logtags=options["logtag"],
                                )

    except Exception:
        log.raw(
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        time.sleep(1)
        print(log.text)
        return log.text

    if verbose:
        log.raw(
            "\nCheck completed on %s\n---------------------------------------------------------"
            % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        )
        print(log.text)

    return log.text


#
#   --- Run FreeSurfer segmentation
#
# -> @register_command(
#        description="Run full FreeSurfer segmentation on NIL preprocessed images.",
#         type="processiing.fs")
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

    try:
        log.capture("\n---------------------------------------------------------")
        log.raw(
            "\nSession id: %s \n[started on %s]"
            % (sinfo["id"], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        )
        log.raw("\nRunning Full FreeSurfer segmentation ...")

        # check if any data already exists
        log.capture(
            check_for_freesurfer_data(sinfo, options, overwrite, thread, log.text)
        )

        d = get_session_folders(sinfo, options)
        f = get_file_names(sinfo, options)

        # --- check if we need to run fsf
        if (
            os.path.exists(f["fs_aseg_nii"]) and os.path.exists(f["fs_aparc+aseg_nii"])
        ) or (os.path.exists(f["fs_aseg_t1"]) and os.path.exists(f["fs_aparc_t1"])):
            log.raw("\n... FreeSurfer run already completed!")

        else:
            # --- copy file over
            if not os.path.exists(f["t1"]):
                shutil.copy2(f["t1_source"], f["t1"])
                if gi.get_img_format(f["t1_source"]) == ".4dfp.img":
                    shutil.copy2(
                        f["t1_source"].replace(".img", ".ifh"),
                        f["t1"].replace(".img", ".ifh"),
                    )
                log.raw(
                    "\n... copied %s to target folder"
                    % (os.path.basename(f["t1_source"]))
                )

            # --- convert to NIfTI
            onifti = f["t1"]
            if gi.get_img_format(onifti) == ".4dfp.img":
                onifti = f["t1"].replace(".4dfp.img", ".nii")
                endlog, status, failed = log.run_external(
                    onifti,
                    "g_FlipFormat %s %s" % (f["t1"].replace(".img", ".ifh"), onifti),
                    "... converting %s to NIfTI" % (os.path.basename(f["t1"])),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                )

            # --- convert to MGZ
            endlog, status, failed = log.run_external(
                f["fs_morig_mgz"],
                "mri_convert --in_type nii %s %s" % (onifti, f["fs_morig_mgz"]),
                "... converting %s to MGZ" % (os.path.basename(onifti)),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

            # --- run FreeSurfer Subcortical
            endlog, status, failed = log.run_external(
                f["fs_aseg_mgz"],
                "recon-all -sd %s -subjid freesurfer -motioncor -nuintensitycor -talairach -normalization -skullstrip -subcortseg -segstats -no-isrunning"
                % (d["s_seg"]),
                "... running subcortical FreeSurfer segmentation",
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

            # --- run FreeSurfer surface registration
            endlog, status, failed = log.run_external(
                f["fs_aparc+aseg_mgz"],
                "recon-all -sd %s -subjid freesurfer -maskbfs -normalization2 -segmentation -fill -tessellate -smooth1 -inflate1 -qsphere -fix -finalsurfs -smooth2 -inflate2 -cortribbon -sphere -surfreg -contrasurfreg -avgcurv -cortparc -parcstats -cortparc2 -parcstats2 -aparc2aseg -no-isrunning"
                % (d["s_seg"]),
                "... running FreeSurfer surface processing",
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

            # --- convert segmentations to nifti
            endlog, status, failed = log.run_external(
                f["fs_aseg_nii"],
                "mri_convert -i %s -ot nii %s" % (f["fs_aseg_mgz"], f["fs_aseg_nii"]),
                "... converting %s to NIfTI" % (f["fs_aseg_mgz"]),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )
            endlog, status, failed = log.run_external(
                f["fs_aparc+aseg_nii"],
                "mri_convert -i %s -ot nii %s"
                % (f["fs_aparc+aseg_mgz"], f["fs_aparc+aseg_nii"]),
                "... converting %s to NIfTI" % (f["fs_aparc+aseg_mgz"]),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
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
                    endlog, status, failed = log.run_external(
                        f["fs_aseg_4dfp"],
                        'g_FlipFormat -c "129.000 -108.000 -142.000" %s %s'
                        % (f["fs_aseg_nii"], f["fs_aseg_4dfp"].replace(".img", ".ifh")),
                        "... converting %s to 4dfp"
                        % (os.path.basename(f["fs_aseg_nii"])),
                        overwrite=overwrite,
                        thread=sinfo["id"],
                        logfolder=options["comlogs"],
                        logtags=options["logtag"],
                        shell=True,
                    )
                endlog, status, failed = log.run_external(
                    f["fs_aseg_t1"],
                    "t4img_4dfp none %s %s -O111 -@b"
                    % (root4dfp(f["fs_aseg_4dfp"]), root4dfp(f["fs_aseg_t1"])),
                    "... converting %s to 111 space" % (f["fs_aseg_4dfp"]),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                )

            endlog, status, failed = log.run_external(
                f["fs_aseg_bold"],
                "t4img_4dfp none %s %s -O333 -n -@b"
                % (root4dfp(f["fs_aseg_t1"]), root4dfp(f["fs_aseg_bold"])),
                "... converting %s to 333 space" % (f["fs_aseg_4dfp"]),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

            # --- check for aparc
            if not os.path.exists(f["fs_aparc_t1"]):
                if not os.path.exists(f["fs_aparc+aseg_4dfp"]):
                    endlog, status, failed = log.run_external(
                        f["fs_aparc+aseg_4dfp"],
                        'g_FlipFormat -c "129.000 -108.000 -142.000" %s %s'
                        % (
                            f["fs_aparc+aseg_nii"],
                            f["fs_aparc+aseg_4dfp"].replace(".img", ".ifh"),
                        ),
                        "... converting %s to 4dfp"
                        % (os.path.basename(f["fs_aparc+aseg_nii"])),
                        overwrite=overwrite,
                        thread=sinfo["id"],
                        logfolder=options["comlogs"],
                        logtags=options["logtag"],
                        shell=True,
                    )
                endlog, status, failed = log.run_external(
                    f["fs_aparc_t1"],
                    "t4img_4dfp none %s %s -O111 -@b"
                    % (root4dfp(f["fs_aparc+aseg_4dfp"]), root4dfp(f["fs_aparc_t1"])),
                    "... converting %s to 111 space" % (f["fs_aparc+aseg_4dfp"]),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                )

            endlog, status, failed = log.run_external(
                f["fs_aparc_bold"],
                "t4img_4dfp none %s %s -O333 -n -@b"
                % (root4dfp(f["fs_aparc_t1"]), root4dfp(f["fs_aparc_bold"])),
                "... converting %s to 333 space" % (f["fs_aparc_t1"]),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

            # --- check if we need to convert to nifti
            if options["image_atlas"] == "711" and options["image_target"] == "nifti":
                # --- convert 111 4dfp to nifti
                endlog, status, failed = log.run_external(
                    f["fs_aseg_t1"],
                    "g_FlipFormat %s %s"
                    % (f["fs_aseg_111"].replace(".img", ".ifh"), f["fs_aseg_t1"]),
                    "... converting %s to nifti" % (os.path.basename(f["fs_aseg_111"])),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                )
                endlog, status, failed = log.run_external(
                    f["fs_aparc_t1"],
                    "g_FlipFormat %s %s"
                    % (
                        f["fs_aparc+aseg_111"].replace(".img", ".ifh"),
                        f["fs_aparc_t1"],
                    ),
                    "... converting %s to nifti"
                    % (os.path.basename(f["fs_aparc+aseg_111"])),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                )

                # --- convert 333 4dfp to nifti
                endlog, status, failed = log.run_external(
                    f["fs_aseg_bold"],
                    "g_FlipFormat %s %s"
                    % (f["fs_aseg_333"].replace(".img", ".ifh"), f["fs_aseg_bold"]),
                    "... converting %s to nifti" % (os.path.basename(f["fs_aseg_333"])),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                )
                endlog, status, failed = log.run_external(
                    f["fs_aparc_bold"],
                    "g_FlipFormat %s %s"
                    % (
                        f["fs_aparc+aseg_333"].replace(".img", ".ifh"),
                        f["fs_aparc_bold"],
                    ),
                    "... converting %s to nifti"
                    % (os.path.basename(f["fs_aparc+aseg_333"])),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                )

        if options["image_atlas"] != "711" and options["image_target"] == "nifti":
            if os.path.exists(f["bold_template"]):
                # --- convert t1 segmentation to bold space
                endlog, status, failed = log.run_external(
                    f["fs_aseg_bold"],
                    "3dresample -rmode NN -master %s -inset %s -prefix %s "
                    % (f["bold_template"], f["fs_aseg_t1"], f["fs_aseg_bold"]),
                    "... resampling t1 subcortical segmentation (%s) to bold space (%s)"
                    % (
                        os.path.basename(f["fs_aseg_t1"]),
                        os.path.basename(f["fs_aseg_bold"]),
                    ),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                )
                endlog, status, failed = log.run_external(
                    f["fs_aparc_bold"],
                    "3dresample -rmode NN -master %s -inset %s -prefix %s "
                    % (f["bold_template"], f["fs_aparc_t1"], f["fs_aparc_bold"]),
                    "... resampling t1 cortical segmentation (%s) to bold space (%s)"
                    % (
                        os.path.basename(f["fs_aparc_t1"]),
                        os.path.basename(f["fs_aparc_bold"]),
                    ),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                )
            else:
                log.raw(
                    "ERROR: bold template image is missing! Please run bbm (create brain masks for BOLD runs) and then rerun fsf to complete the last step!"
                )

    except (ExternalFailed, NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        log.raw(
            "\nFreeSurfer segmentation failed on %s\n---------------------------------------------------------"
            % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        )
        print(log.text)
        return log.text
    except Exception:
        log.raw(
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        time.sleep(15)
        print(log.text)
        return log.text

    log.raw(
        "\nFreeSurfer segmentation completed on %s\n---------------------------------------------------------"
        % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    )

    print(log.text)
    return log.text


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
    try:
        log.capture("\n---------------------------------------------------------")
        log.raw(
            "\nSession id: %s \n[started on %s]"
            % (sinfo["id"], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        )
        log.raw("\nRunning subcortical only FreeSurfer segmentation ...")

        # check if any data already exists
        log.capture(
            check_for_freesurfer_data(sinfo, options, overwrite, thread, log.text)
        )

        d = get_session_folders(sinfo, options)
        f = get_file_names(sinfo, options)

        # --- check if we need to run fsf
        if os.path.exists(f["fs_aseg_nii"]):
            log.raw("\n... FreeSurfer run already completed!")

        else:
            # --- copy file over
            if not os.path.exists(f["t1"]):
                shutil.copy2(f["t1_source"], f["t1"])
                if gi.get_img_format(f["t1_source"]) == ".4dfp.img":
                    shutil.copy2(
                        f["t1_source"].replace(".img", ".ifh"),
                        f["t1"].replace(".img", ".ifh"),
                    )
                log.raw(
                    "\n... copied %s to target folder"
                    % (os.path.basename(f["t1_source"]))
                )

            # --- convert to NIfTI
            onifti = f["t1"]
            if gi.get_img_format(onifti) == ".4dfp.img":
                onifti = f["t1"].replace(".4dfp.img", ".nii")
                endlog, status, failed = log.run_external(
                    onifti,
                    "g_FlipFormat %s %s" % (f["t1"].replace(".img", ".ifh"), onifti),
                    "... converting %s to NIfTI" % (os.path.basename(f["t1"])),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                )

            # --- convert to MGZ
            endlog, status, failed = log.run_external(
                f["fs_morig_mgz"],
                "mri_convert --in_type nii %s %s" % (onifti, f["fs_morig_mgz"]),
                "... converting %s to MGZ" % (os.path.basename(onifti)),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

            # --- run FreeSurfer Subcortical
            endlog, status, failed = log.run_external(
                f["fs_aseg_mgz"],
                "recon-all -sd %s -subjid freesurfer -motioncor -nuintensitycor -talairach -normalization -skullstrip -subcortseg -segstats -no-isrunning"
                % (d["s_seg"]),
                "... running subcortical FreeSurfer segmentation",
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

            # --- convert segmentations to nifti
            endlog, status, failed = log.run_external(
                f["fs_aseg_nii"],
                "mri_convert -i %s -ot nii %s" % (f["fs_aseg_mgz"], f["fs_aseg_nii"]),
                "... converting %s to NIfTI" % (f["fs_aseg_mgz"]),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

        if options["image_target"] == "nifti":
            if not os.path.exists(f["fs_aseg_t1"]):
                gc.link_or_copy(f["fs_aseg_nii"], f["fs_aseg_t1"])

        # --- 4dfp path
        if options["image_target"] == "4dfp" or options["image_atlas"] == "711":
            # --- convert to 4dfp
            endlog, status, failed = log.run_external(
                f["fs_aseg_4dfp"],
                'g_FlipFormat -c "129.000 -108.000 -142.000" %s %s'
                % (f["fs_aseg_nii"], f["fs_aseg_4dfp"].replace(".img", ".ifh")),
                "... converting %s to 4dfp" % (os.path.basename(f["fs_aseg_nii"])),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
                shell=True,
            )

            # --- convert to 111
            endlog, status, failed = log.run_external(
                f["fs_aseg_111"],
                "t4img_4dfp none %s %s -O111 -@b"
                % (root4dfp(f["fs_aseg_4dfp"]), root4dfp(f["fs_aseg_111"])),
                "... converting %s to 111 space" % (f["fs_aseg_4dfp"]),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

            # --- convert to 333
            endlog, status, failed = log.run_external(
                f["fs_aseg_333"],
                "t4img_4dfp none %s %s -O333 -n -@b"
                % (root4dfp(f["fs_aseg_4dfp"]), root4dfp(f["fs_aseg_333"])),
                "... converting %s to 333 space" % (f["fs_aseg_4dfp"]),
                overwrite=overwrite,
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=options["logtag"],
            )

            if options["image_atlas"] == "711" and options["image_target"] == "nifti":
                # --- convert 111 4dfp to nifti
                endlog, status, failed = log.run_external(
                    f["fs_aseg_t1"],
                    "g_FlipFormat %s %s"
                    % (f["fs_aseg_111"].replace(".img", ".ifh"), f["fs_aseg_t1"]),
                    "... converting %s to nifti" % (os.path.basename(f["fs_aseg_111"])),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                )

                # --- convert 333 4dfp to nifti
                endlog, status, failed = log.run_external(
                    f["fs_aseg_bold"],
                    "g_FlipFormat %s %s"
                    % (f["fs_aseg_333"].replace(".img", ".ifh"), f["fs_aseg_bold"]),
                    "... converting %s to nifti" % (os.path.basename(f["fs_aseg_333"])),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                )

        if options["image_atlas"] != "711" and options["image_target"] == "nifti":
            if os.path.exists(f["bold_template"]):
                # --- convert t1 segmentation to bold space
                endlog, status, failed = log.run_external(
                    f["fs_aseg_bold"],
                    "3dresample -rmode NN -master %s -inset %s -prefix %s "
                    % (f["bold_template"], f["fs_aseg_t1"], f["fs_aseg_bold"]),
                    "... resampling t1 subcortical segmentation (%s) to bold space (%s)"
                    % (
                        os.path.basename(f["fs_aseg_t1"]),
                        os.path.basename(f["fs_aseg_bold"]),
                    ),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                )
            else:
                log.raw(
                    "ERROR: bold template image is missing! Please run bbm (create brain masks for BOLD runs) and then rerun fsf to complete the last step!"
                )

    except (ExternalFailed, NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        log.raw(
            "\nFreeSurfer segmentation failed on %s\n---------------------------------------------------------"
            % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        )
        print(log.text)
        return log.text
    except Exception:
        log.raw(
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        time.sleep(15)
        print(log.text)
        return log.text

    log.raw(
        "\nFreeSurfer segmentation completed on %s\n---------------------------------------------------------"
        % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    )

    print(log.text)
    return log.text
