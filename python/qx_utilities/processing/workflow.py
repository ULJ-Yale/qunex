#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``workflow.py``

This file holds code for running functional connectivity preprocessing and
GLM computation workflow. It consists of functions:

--get_bold_data             Maps NIL preprocessed data to images folder.
--create_bold_brain_masks   Extracts the first frame of each BOLD file.
--compute_bold_stats        Computes per volume image statistics for scrubbing.
--create_stats_report       Creates a report of movement and image statistics.
--extract_nuisance_signal   Extracts the nuisance signal for regressions.
--preprocess_bold           Processes a single BOLD file.
--preprocess_conc           Processes concatenated BOLD files.

All the functions are part of the processing suite. They should be called
from the command line using `qunex` command. Help is available through:

- `qunex ?<command>` for command specific help
"""

"""
Created by Grega Repovs on 2016-12-17.
Code split from dofcMRIp_core gCodeP/preprocess codebase.
Copyright (c) Grega Repovs. All rights reserved.
"""

import os
import shutil
import re
import traceback
import time
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import processing.core as pc
import general.exceptions as ge
import general.filelock as fl
import general.meltmovfidl as gm
import general.img as gi
import general.core as gc

if "QUNEXMCOMMAND" not in os.environ:
    print(
        "WARNING: QUNEXMCOMMAND environment variable not set. Matlab will be run by default!"
    )
    mcommand = "matlab -nojvm -nodisplay -nosplash -r"
else:
    mcommand = os.environ["QUNEXMCOMMAND"]


def get_bold_data(sinfo, options, overwrite=False, thread=0):
    """
    get_bold_data - documentation not yet available.
    """
    bsearch = re.compile(r"bold([0-9]+)")

    r = "\n---------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\nCopying imaging data ..."

    r += "\nStructural data ..."
    pc.doOptionsCheck(options, sinfo, "get_bold_data")
    f = pc.getFileNames(sinfo, options)

    copy = True
    if os.path.exists(f["t1"]):
        copy = False

    try:
        if overwrite or copy:
            if f["t1_source"] is None:
                raise pc.NoSourceFolder(
                    "ERROR: Data source folder is not set. Please check your paths!"
                )
            r += "\n... copying %s" % (f["t1_source"])
            if options["image_target"] == "4dfp":
                if gi.getImgFormat(f["t1_source"]) == ".4dfp.img":
                    gc.link_or_copy(f["t1_source"], f["t1"])
                    gc.link_or_copy(
                        f["t1_source"].replace(".img", ".ifh"),
                        f["t1"].replace(".img", ".ifh"),
                    )
                else:
                    tmpfile = f["t1"].replace(
                        ".4dfp.img", gi.getImgFormat(f["t1_source"])
                    )
                    gc.link_or_copy(f["t1_source"], tmpfile)
                    r, endlog, status, failed = pc.runExternalForFile(
                        f["t1"],
                        "g_FlipFormat %s %s"
                        % (tmpfile, f["t1"].replace(".img", ".ifh")),
                        "... converting %s to 4dfp" % (os.path.basename(tmpfile)),
                        overwrite=overwrite,
                        thread=sinfo["id"],
                        logfolder=options["comlogs"],
                        logtags=[options["bold_variant"], options["logtag"]],
                        r=r,
                    )
                    os.remove(tmpfile)
            if options["image_target"] == "nifti":
                if gi.getImgFormat(f["t1_source"]) == ".4dfp.img":
                    tmpimg = f["t1"] + ".4dfp.img"
                    tmpifh = f["t1"] + ".4dfp.ifh"
                    gc.link_or_copy(f["t1_source"], tmpimg)
                    gc.link_or_copy(f["t1_source"].replace(".img", ".ifh"), tmpifh)
                    r, endlog, status, failed = pc.runExternalForFile(
                        f["t1"],
                        "g_FlipFormat %s %s"
                        % (tmpifh, f["t1"].replace(".img", ".ifh")),
                        "... converting %s to NIfTI" % (os.path.basename(tmpimg)),
                        overwrite=overwrite,
                        thread=sinfo["id"],
                        logfolder=options["comlogs"],
                        logtags=[options["bold_variant"], options["logtag"]],
                        r=r,
                    )
                    os.remove(tmpimg)
                    os.remove(tmpifh)
                else:
                    if gi.getImgFormat(f["t1_source"]) == ".nii.gz":
                        tmpfile = f["t1"] + ".gz"
                        gc.link_or_copy(f["t1_source"], tmpfile)
                        r, endlog, status, failed = pc.runExternalForFile(
                            f["t1"],
                            "gunzip -f %s" % (tmpfile),
                            "... gunzipping %s" % (os.path.basename(tmpfile)),
                            overwrite=overwrite,
                            thread=sinfo["id"],
                            logfolder=options["comlogs"],
                            logtags=[options["bold_variant"], options["logtag"]],
                            r=r,
                        )
                        if os.path.exists(tmpfile):
                            os.remove(tmpfile)
                    else:
                        gc.link_or_copy(f["t1_source"], f["t1"])

        else:
            r += "\n... %s present" % (f["t1"])
    except:
        r += "\n... ERROR getting the data! Please check paths and files!"

    btargets = options["bolds"].split("|")

    for k, v in sinfo.items():
        if k.isdigit():
            bnum = bsearch.match(v["name"])
            if bnum:
                if v["task"] in btargets:
                    boldname = v["name"]

                    r += "\n\nWorking on: " + boldname + " ..."

                    try:
                        # --- filenames
                        f = pc.getFileNames(sinfo, options)
                        f.update(pc.getBOLDFileNames(sinfo, boldname, options))
                        d = pc.getSessionFolders(sinfo, options)

                        if status:
                            r += "\n---> Data ready!"
                        else:
                            r += "\n---> ERROR: Data missing, please check source!"

                    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
                        r += str(errormessage)
                    except:
                        r += (
                            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
                            % (traceback.format_exc())
                        )
                        time.sleep(3)

    r += (
        "\n\nImaging data copy completed on %s\n---------------------------------------------------------"
        % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    )

    # print r
    return r


def create_bold_brain_masks(sinfo, options, overwrite=False, thread=0):
    """
    ``create_bold_brain_masks [... processing options]``

    Extracts the brain and creates a brain mask for each BOLD image.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions' information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --overwrite (str, 'no'):
            Whether to overwrite existing data (yes) or not (no).

        --bolds (str, default 'rest'):
            Which bold images (as they are specified in the batch.txt file) to
            copy over. It can be a single type (e.g. 'task'), a pipe separated
            list (e.g. 'WM|Control|rest') or 'all' to copy all.

        --boldname (str, default 'bold'):
            The default name of the bold files in the images folder.

        --nifti_tail (str, default detailed below):
            The tail of NIfTI volume images to use. Default to the value of
            qx_nifti_tail.

        --bold_variant (str, default ''):
            Optional variant of bold preprocessing. If specified, the BOLD
            images in `images/functional<bold_variant>` will be processed.

        --img_suffix (str, default ''):
            Specifies a suffix for 'images' folder to enable support for
            multiple parallel workflows. Empty if not used.

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

    Notes:
        The parameters can be specified in command call or session.txt file.

        create_bold_brain_masks takes the first image of each bold file, and
        runs FSL bet to extract the brain and create a brain mask. The resulting
        files are saved into images/segmentation/boldmasks in the source image
        format:

        - bold[N]<nifti_tail>_frame1.*
        - bold[N]<nifti_tail>_frame1_brain.*
        - bold[N]<nifti_tail>_frame1_brain_mask.*

    Examples:
        ::

            qunex create_bold_brain_masks \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --nifti_tail=_hp2000_clean \\
                --bolds=all \\
                --parelements=8
    """

    report = {
        "bolddone": 0,
        "boldok": 0,
        "boldfail": 0,
        "boldmissing": 0,
        "boldskipped": 0,
    }

    r = "\n---------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\nCreating masks for bold runs ... \n"
    r += "\n\n   Files in 'images%s/functional%s will be processed." % (
        options["img_suffix"],
        options["bold_variant"],
    )
    r += "\n   Masks will be saved in 'images%s/boldmasks.%s." % (
        options["img_suffix"],
        options["bold_variant"],
    )
    r += "\n   The command will create a mask identifying actual coverage of the brain for\n   each of the specified BOLD files based on its first frame.\n\n   Please note: when mapping the BOLD data, the following parameter is key: \n\n   --bolds parameter defines which BOLD files are processed based on their\n     specification in batch.txt file. Please see documentation for formatting. \n     If the parameter is not specified the default value is 'all' and all BOLD\n     files will be processed."
    r += "\n\n........................................................"

    pc.doOptionsCheck(options, sinfo, "create_bold_brain_masks")
    d = pc.getSessionFolders(sinfo, options)

    if overwrite:
        ostatus = "will"
    else:
        ostatus = "will not"

    r += "\n\nWorking on BOLD images in: " + d["s_images"]
    r += "\nResulting masks will be in: " + d["s_boldmasks"]
    r += "\n\nBased on the settings, %s BOLD files will be processed (see --bolds)." % (
        ", ".join(options["bolds"].split("|"))
    )
    r += (
        "\nIf already present, existing masks %s be overwritten (see --overwrite).\n"
        % (ostatus)
    )

    bolds, bskip, report["boldskipped"], r = pc.useOrSkipBOLD(sinfo, options, r)

    parelements = options["parelements"]
    r += "\nProcessing %d BOLDs in parallel" % (parelements)

    if parelements == 1:  # serial execution
        for b in bolds:
            # process
            result = executeCreateBOLDBrainMasks(sinfo, options, overwrite, b)

            # merge r
            r += result["r"]

            # merge report
            tempReport = result["report"]
            report["bolddone"] += tempReport["bolddone"]
            report["boldok"] += tempReport["boldok"]
            report["boldfail"] += tempReport["boldfail"]
            report["boldmissing"] += tempReport["boldmissing"]
    else:  # parallel execution
        # create a multiprocessing Pool
        processPoolExecutor = ProcessPoolExecutor(parelements)
        # process
        f = partial(executeCreateBOLDBrainMasks, sinfo, options, overwrite)
        results = processPoolExecutor.map(f, bolds)

        # merge r and report
        for result in results:
            r += result["r"]
            tempReport = result["report"]
            report["bolddone"] += tempReport["bolddone"]
            report["boldok"] += tempReport["boldok"]
            report["boldfail"] += tempReport["boldfail"]
            report["boldmissing"] += tempReport["boldmissing"]

    r += (
        "\n\nBold mask creation completed on %s\n---------------------------------------------------------"
        % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    )
    rstatus = (
        "BOLDS done: %(bolddone)2d, missing data: %(boldmissing)2d, failed: %(boldfail)2d, processed: %(boldok)2d, skipped: %(boldskipped)2d"
        % (report)
    )

    return (r, (sinfo["id"], rstatus, report["boldmissing"] + report["boldfail"]))


def executeCreateBOLDBrainMasks(sinfo, options, overwrite, boldData):
    # extract data
    boldnum = boldData[0]
    boldname = boldData[1]

    # prepare return variables
    r = ""
    report = {"bolddone": 0, "boldok": 0, "boldfail": 0, "boldmissing": 0}

    r += "\n\nWorking on: " + boldname

    try:
        # --- filenames
        f = pc.getFileNames(sinfo, options)
        f.update(pc.getBOLDFileNames(sinfo, boldname, options))

        # template file
        templatefile = f["bold_template"]

        # --- copy over bold data
        # --- bold
        r, status = pc.checkForFile2(
            r,
            f["bold_vol"],
            "\n    ... bold data present",
            "\n    ... bold data missing, skipping bold",
            status=True,
        )
        if not status:
            r += "\nLooked for:" + f["bold_vol"]
            report["boldmissing"] += 1
            return {"r": r, "report": report}

        # --- extract first bold frame
        if not os.path.exists(f["bold1"]) or overwrite:
            gi.slice_image(f["bold_vol"], f["bold1"], 1)
            if os.path.exists(f["bold1"]):
                r += "\n    ... sliced first frame from %s" % (
                    os.path.basename(f["bold_vol"])
                )
            else:
                r += "\n    ... WARNING: failed slicing first frame from %s" % (
                    os.path.basename(f["bold_vol"])
                )
                report["boldfail"] += 1
                return {"r": r, "report": report}
        else:
            r += "\n    ... first %s frame already present" % (
                os.path.basename(f["bold_vol"])
            )

        # --- logs storage
        endlogs = []

        # --- convert to NIfTI
        bsource = f["bold1"]
        bbtarget = f["bold1_brain"].replace(
            gi.getImgFormat(f["bold1_brain"]), ".nii.gz"
        )
        bmtarget = f["bold1_brain_mask"].replace(
            gi.getImgFormat(f["bold1_brain_mask"]), ".nii.gz"
        )
        if gi.getImgFormat(f["bold1"]) == ".4dfp.img":
            bsource = f["bold1"].replace(".4dfp.img", ".nii.gz")

            # run g_FlipFormat
            r, endlog, status, failed = pc.runExternalForFile(
                bsource,
                "g_FlipFormat %s %s" % (f["bold1"], bsource),
                "    ... converting %s to nifti" % (f["bold1"]),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                task="FlipFormat" % (boldnum),
                logfolder=options["comlogs"],
                logtags=[options["bold_variant"], options["logtag"], "B%d" % boldnum],
                r=r,
                verbose=False,
            )

            # append to endlogs
            endlogs.append(endlog)

            # run caret_command
            r, endlog, status, failed = pc.runExternalForFile(
                bsource,
                "caret_command -file-convert -vc %s %s"
                % (f["bold1"].replace("img", "ifh"), bsource),
                "converting %s to nifti" % (f["bold1"]),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=[options["bold_variant"], options["logtag"], "B%d" % boldnum],
                r=r,
                verbose=False,
            )

            # append to endlogs
            endlogs.append(endlog)

        # --- run BET
        if os.path.exists(bbtarget) and not overwrite:
            r += "\n    ... bet on %s already run" % (os.path.basename(bsource))
            report["bolddone"] += 1
        else:
            # run BET
            r, endlog, status, failed = pc.runExternalForFile(
                bbtarget,
                "bet %s %s %s" % (bsource, bbtarget, options["betboldmask"]),
                "    ... running BET on %s with options %s"
                % (os.path.basename(bsource), options["betboldmask"]),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                task="bet",
                logfolder=options["comlogs"],
                logtags=[options["bold_variant"], options["logtag"], "B%d" % boldnum],
                r=r,
                verbose=False,
            )
            report["boldok"] += 1

            # append to endlogs
            endlogs.append(endlog)

        if options["image_target"] == "4dfp":
            # --- convert nifti to 4dfp
            # run gunzip
            r, endlog, status, failed = pc.runExternalForFile(
                bbtarget,
                "gunzip -f %s.gz" % (bbtarget),
                "    ... gunzipping %s.gz" % (os.path.basename(bbtarget)),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                task="gunzip",
                logfolder=options["comlogs"],
                logtags=[options["bold_variant"], options["logtag"], "B%d" % boldnum],
                r=r,
                verbose=False,
            )

            # append to endlogs
            endlogs.append(endlog)

            # run gunzip
            r, endlog, status, failed = pc.runExternalForFile(
                bmtarget,
                "gunzip -f %s.gz" % (bmtarget),
                "    ... gunzipping %s.gz" % (os.path.basename(bmtarget)),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                task="gunzip",
                logfolder=options["comlogs"],
                logtags=[options["bold_variant"], options["logtag"], "B%d" % boldnum],
                r=r,
                verbose=False,
            )

            # append to endlogs
            endlogs.append(endlog)

            # run g_FlipFormat
            r, endlog, status, failed = pc.runExternalForFile(
                f["bold1_brain"],
                "g_FlipFormat %s %s"
                % (bbtarget, f["bold1_brain"].replace(".img", ".ifh")),
                "    ... converting %s to 4dfp" % (f["bold1_brain_nifti"]),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                task="FlipFormat",
                logfolder=options["comlogs"],
                logtags=[options["bold_variant"], options["logtag"], "B%d" % boldnum],
                r=r,
                verbose=False,
            )

            # append to endlogs
            endlogs.append(endlog)

            # run g_FlipFormat
            r, endlog, status, failed = pc.runExternalForFile(
                f["bold1_brain_mask"],
                "g_FlipFormat %s %s"
                % (bmtarget, f["bold1_brain_mask"].replace(".img", ".ifh")),
                "    ... converting %s to 4dfp" % (f["bold1_brain_mask_nifti"]),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                task="FlipFormat",
                logfolder=options["comlogs"],
                logtags=[options["bold_variant"], options["logtag"], "B%d" % boldnum],
                r=r,
                verbose=False,
            )

            # append to endlogs
            endlogs.append(endlog)

        else:
            # --- link a template
            # lock
            fl.lock(templatefile)

            # create link
            if not os.path.exists(templatefile):
                # r += '\n ... link %s to %s' % (f['bold1_brain'], f['bold_template'])
                gc.link_or_copy(f["bold1_brain"], f["bold_template"])

            # unlock
            fl.unlock(templatefile)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r += str(errormessage)

        # unlock tempalte file if it crashed there
        fl.unlock(templatefile)

        report["boldfail"] += 1
    except Exception as e:
        # unlock template file if it crashed there
        if templatefile is not None and os.path.exists(templatefile):
            fl.unlock(templatefile)

        report["boldfail"] += 1
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s\n%s...................................\n"
            % (e, traceback.format_exc())
        )
        time.sleep(1)

    # merge into final comlog
    log_prefix = "done"

    # final_ log storage
    final_log = ""

    # if remove option is set do nothinng
    remove = options["log"] == "remove"
    if not remove and endlogs:
        for el in endlogs:
            if os.path.exists(el):
                # did the command error out?
                el_log = os.path.basename(el)
                if "error" in el_log:
                    log_prefix = "error"

                # read log
                with open(el, "r") as f:
                    log_content = f.read()

                # concatenate
                final_log = final_log + log_content + "\n\n"

                # delete the partial log
                os.remove(el)

    # fails?
    if report["boldfail"] > 0:
        log_prefix = "error"
    elif not overwrite and final_log == "":
        final_log = "Previous results present, overwrite set to no.\n\n"
        final_log = final_log + "---> Successful completion of task"

    # print to log file
    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
    logname = "%s_create_bold_brain_masks_B%s_%s_%s.log" % (
        log_prefix,
        boldnum,
        sinfo["id"],
        logstamp,
    )

    # setup log folder
    logfolder = options["comlogs"]
    logfolders = []
    if type(logfolder) in [list, set, tuple]:
        logfolders = list(logfolder)
        logfolder = logfolders.pop(0)

    if not os.path.exists(logfolder):
        try:
            os.makedirs(logfolder)
        except:
            r += "\n\nERROR: Could not create folder for logfile [%s]!" % (logfolder)
            raise pc.ExternalFailed(r)

    # print to file and close
    logfile = os.path.join(logfolder, logname)
    lf = open(logfile, "a")
    lf.write(final_log)
    lf.close()

    return {"r": r, "report": report}


def compute_bold_stats(sinfo, options, overwrite=False, thread=0):
    """
    ``compute_bold_stats [... processing options]``

    Processes specified BOLD files and saves images/function/movement files.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the session information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no).

        --bolds (str, default 'rest'):
            Which bold images (as they are specified in the batch.txt file) to
            copy over. It can be a single type (e.g. 'task'), a pipe separated
            list (e.g. 'WM|Control|rest') or 'all' to copy all.

        --boldname (str, default 'bold'):
            The default name of the bold files in the images folder.

        --nifti_tail (str, default ''):
            The tail of NIfTI volume images to use.

        --bold_variant (str, default ''):
            Optional variant of bold preprocessing. If specified, the BOLD
            images in `images/functional<bold_variant>` will be processed.

        --img_suffix (str, default ''):
            Specifies a suffix for 'images' folder to enable support for
            multiple parallel workflows. Empty if not used.

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

        --mov_radius (int, default 50):
            Estimated head radius (in mm) for computing frame displacement
            statistics.

        --mov_fd (float, default 0.5):
            Frame displacement threshold (in mm) to use for identifying bad
            frames.

        --mov_dvars (float, default 3.0):
            The (mean normalized) dvars threshold to use for identifying bad
            frames.

        --mov_dvarsme (float, default 1.5):
            The (median normalized) dvarsm threshold to use for identifying bad
            frames.

        --mov_after (int, default 0):
            How many frames after each frame identified as bad to also exclude
            from further processing and analysis.

        --mov_before (int, default 0):
            How many frames before each frame identified as bad to also exclude
            from further processing and analysis.

        --mov_bad (str, default 'udvarsme'):
            Which criteria to use for identification of bad frames (mov, dvars,
            dvarsme, idvars, uvars, idvarsme, udvarsme). See movement scrubbing
            documentation for further information.
            Criteria for identification of bad frames can be one out of:

            - 'mov'      ... Frame displacement threshold (fdt) is exceeded.
            - 'dvars'    ... Image intensity normalized root mean squared error
              (RMSE) threshold (dvarsmt) is exceeded.
            - 'dvarsme'  ... Median normalised RMSE (dvarsmet) threshold is
              exceeded.
            - 'idvars'   ... Both fdt and dvarsmt are exceeded (i for
              intersection).
            - 'uvars'    ... Either fdt or dvarsmt are exceeded (u for union).
            - 'idvarsme' ... Both fdt and dvarsmet are exceeded.
            - 'udvarsme' ... Either fdt or udvarsmet are exceeded.

            For more detailed description please see wiki entry on Movement
            scrubbing.

    Notes:
        The parameters listed in `Other parameters` can be specified in command
        call or session.txt file.

        The compute_bold_stats function processes each of the specified BOLD
        files and saves three files in the images/functional/movement folder:

        bold[N].bstats:
            bold[N]<nifti_tail>.bstats includes for each frame of the BOLD image
            the following computed statistics:

            - n
                Number of brain voxels.
            - m
                Mean signal intensity across all brain voxels.
            - var
                Signal variance across all brain voxels.
            - sd
                Signal standard variation across all brain voxels.
            - dvars
                RMDS measure of signal intensity difference between this and the
                preceeding frame.
            - dvarsm
                Mean normalized dvars measure.
            - dvarsme
                Median normalized dvarsm measure.
            - fd
                Frame displacement.

            There are three additional lines at the end of the file listing
            maximum, mean and standard deviation of values across all timepoints
            / volumes.

        bold[N].scrub:
            bold[N]<nifti_tail>.scrub includes for each frame the information on
            whether the frame should be excluded (1) or not (0) based on the
            following criteria (note below the relevant settings that specify
            thresholds etc.):

            - mov
                Is frame displacement higher from the specified threshold?
            - dvars
                Is mean normalized dvars (dvarsm) higher than the specified
                threshold?
            - dvarsme
                Is the median normalized dvarsm higher than the specified
                threshold?
            - idvars
                Are both frame displacement as well as dvarsm measures above
                threshold (intersection of fd and dvarsm).
            - idvarsme
                Are both frame displacement as well as dvarsme measures above
                threshold (intersection of fd and dvarsme).
            - udvars
                Are either frame displacement or dvarsm measures above threshold
                (union of fs and dvarsm).
            - udvarsme
                Are either frame displacement or dvarsme measures above
                threshold (union of fs and dvarsme).

            The last column of the file is a 'use' column, which specifies,
            based on the criteria provided, whether the frame should be used in
            further preprocessing and analysis or not.

            There is an additional #sum line at the end of the file, listing how
            many frames are marked as bad using each criteria.

        bold[N].use:
            bold[N]<nifti_tail>.use file lists for each frame of the relevant
            BOLD image, whether it is to be used (1) or not (0).

        When 'cifti' is the specified image target, the related nifti volume
        files will be processed as only they provide all the information for
        computing the relevant parameters.

        Dependencies:
            The command runs the general_compute_bold_stats.m Matlab function
            for computation of parameters. It also expects that both bold images
            and the related movement correction parameter files are present in
            the expected locations.

    Examples:
        Using the defaults::

            qunex compute_bold_stats \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --bolds=all

        Specifying additional parameters for identification of bad frames::

            qunex compute_bold_stats \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --bolds=all \\
                --mov_fd=0.9 \\
                --mov_dvarsme=1.6 \\
                --mov_before=1 \\
                --mov_after=2
    """

    report = {
        "bolddone": 0,
        "boldok": 0,
        "boldfail": 0,
        "boldmissing": 0,
        "boldskipped": 0,
    }

    r = "\n---------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n\nComputing BOLD image statistics ..."
    r += "\n\n    Files in 'images%s/functional%s will be processed." % (
        options["img_suffix"],
        options["bold_variant"],
    )
    r += "\n\n    The command will compute per frame statistics for each of the specified BOLD\n    files based on its movement correction parameter file and BOLD image analysis.\n    The results will be saved as *.bstat and *.bscrub files in the images/movement\n    subfolder. Only images specified using --bolds parameter will be\n    processed (see documentation). Do also note that even if cifti is specifed as\n    target format, nifti volume image will be used to compute statistics."
    r += (
        "\n\n    Using parameters:\n\n    --mov_radius: %(mov_radius)s\n    --mov_fd: %(mov_fd)s\n    --mov_dvars: %(mov_dvars)s\n    --mov_dvarsme: %(mov_dvarsme)s\n    --mov_after: %(mov_after)s\n    --mov_before: %(mov_before)s\n    --mov_bad: %(mov_bad)s"
        % (options)
    )
    r += "\n\n    for computing scrubbing information."
    r += "\n\n........................................................"

    pc.doOptionsCheck(options, sinfo, "compute_bold_stats")
    d = pc.getSessionFolders(sinfo, options)

    if overwrite:
        ostatus = "will"
    else:
        ostatus = "will not"

    r += "\n\nWorking on BOLD images in: " + d["s_bold"]
    r += "\nResulting files will be in: " + d["s_bold_mov"]
    r += "\n\nBased on the settings, %s BOLD files will be processed (see --bolds)." % (
        ", ".join(options["bolds"].split("|"))
    )
    r += (
        "\nIf already present, existing statistics %s be overwritten (see --overwrite)."
        % (ostatus)
    )

    bolds, bskip, report["boldskipped"], r = pc.useOrSkipBOLD(sinfo, options, r)

    parelements = options["parelements"]
    r += "\nProcessing %d BOLDs in parallel" % (parelements)

    if parelements == 1:  # serial execution
        for b in bolds:
            # process
            result = executeComputeBOLDStats(sinfo, options, overwrite, b)

            # merge r
            r += result["r"]

            # merge report
            tempReport = result["report"]
            report["bolddone"] += tempReport["bolddone"]
            report["boldok"] += tempReport["boldok"]
            report["boldfail"] += tempReport["boldfail"]
            report["boldmissing"] += tempReport["boldmissing"]
    else:  # parallel execution
        # create a multiprocessing Pool
        processPoolExecutor = ProcessPoolExecutor(parelements)
        # process
        f = partial(executeComputeBOLDStats, sinfo, options, overwrite)
        results = processPoolExecutor.map(f, bolds)

        # merge r and report
        for result in results:
            r += result["r"]
            tempReport = result["report"]
            report["bolddone"] += tempReport["bolddone"]
            report["boldok"] += tempReport["boldok"]
            report["boldfail"] += tempReport["boldfail"]
            report["boldmissing"] += tempReport["boldmissing"]

    r += (
        "\n\nBold statistics computation completed on %s\n---------------------------------------------------------"
        % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    )
    rstatus = (
        "BOLDS done: %(bolddone)2d, missing data: %(boldmissing)2d, failed: %(boldfail)2d, processed: %(boldok)2d, skipped: %(boldskipped)2d"
        % (report)
    )

    # print r
    return (r, (sinfo["id"], rstatus, report["boldmissing"] + report["boldfail"]))


def executeComputeBOLDStats(sinfo, options, overwrite, boldData):
    # extract data
    boldnum = boldData[0]
    boldname = boldData[1]

    # prepare return variables
    r = ""
    report = {"bolddone": 0, "boldok": 0, "boldfail": 0, "boldmissing": 0}

    r += "\n\nWorking on: " + boldname + " ..."

    try:
        # --- filenames

        f = pc.getFileNames(sinfo, options)
        f.update(pc.getBOLDFileNames(sinfo, boldname, options))
        d = pc.getSessionFolders(sinfo, options)

        # --- check for data availability

        r += "\n... checking for data"
        status = True

        # --- movement
        r, status = pc.checkForFile2(
            r,
            f["bold_mov"],
            "\n    ... movement data present [%s]" % (os.path.basename(f["bold_mov"])),
            "\n    ... movement data missing [%s]" % (os.path.basename(f["bold_mov"])),
            status=status,
        )

        # --- bold
        r, status = pc.checkForFile2(
            r,
            f["bold_vol"],
            "\n    ... bold data present [%s]" % (os.path.basename(f["bold_vol"])),
            "\n    ... bold data missing [%s]" % (os.path.basename(f["bold_vol"])),
            status=status,
        )

        # --- check
        if not status:
            r += "\n---> ERROR: Files missing, skipping this bold run!"
            report["boldmissing"] += 1
            return {"r": r, "report": report}

        # --- running the stats

        scrub = (
            "radius:%d|fdt:%.2f|dvarsmt:%.2f|dvarsmet:%.2f|after:%d|before:%d|reject:%s"
            % (
                options["mov_radius"],
                options["mov_fd"],
                options["mov_dvars"],
                options["mov_dvarsme"],
                options["mov_after"],
                options["mov_before"],
                options["mov_bad"],
            )
        )
        comm = (
            "%s \"try general_compute_bold_stats('%s', '', '%s', 'same', '%s', true); catch ME, general_report_crash(ME); exit(1), end; exit\""
            % (mcommand, f["bold_vol"], d["s_bold_mov"], scrub)
        )
        if options["print_command"] == "yes":
            r += "\n\nRunning\n" + comm + "\n"
        runit = True
        if os.path.exists(f["bold_stats"]) and not overwrite:
            report["bolddone"] += 1
            runit = False
        r, endlog, status, failed = pc.runExternalForFile(
            f["bold_stats"],
            comm,
            "... running matlab general_compute_bold_stats on %s" % (f["bold_vol"]),
            overwrite,
            thread=sinfo["id"],
            remove=options["log"] == "remove",
            task=options["command_ran"],
            logfolder=options["comlogs"],
            logtags=[options["bold_variant"], options["logtag"], "B%d" % boldnum],
            r=r,
            shell=True,
        )
        r, status = pc.checkForFile(
            r,
            f["bold_stats"],
            "ERROR: Matlab/Octave has failed preprocessing BOLD using command: %s"
            % (comm),
        )

        if status and runit:
            report["boldok"] += 1
        elif runit:
            report["boldfail"] += 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r += str(errormessage)
        report["boldfail"] += 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report["boldfail"] += 1

    return {"r": r, "report": report}


def create_stats_report(sinfo, options, overwrite=False, thread=0):
    """
    ``create_stats_report(sinfo, options, overwrite=False, thread=0)``

    Processes movement correction parameters and computed BOLD statistics to
    create per session plots and fidl snippets and group reports.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the session information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no).

        --bolds (str, default 'rest'):
            Which bold images (as they are specified in the batch.txt file) to
            copy over. It can be a single type (e.g. 'task'), a pipe separated
            list (e.g. 'WM|Control|rest') or 'all' to copy all.

        --boldname (str, default 'bold'):
            The default name of the bold files in the images folder.

        --nifti_tail (str, default ''):
            The tail of NIfTI volume images to use.

        --bold_variant (str, default ''):
            Optional variant of bold preprocessing. If specified, the BOLD
            images in `images/functional<bold_variant>` will be processed.

        --img_suffix (str, default ''):
            Specifies a suffix for 'images' folder to enable support for
            multiple parallel workflows. Empty if not used.

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

        --mov_radius (int, default 50):
            Estimated head radius (in mm) for computing frame displacement
            statistics.

        --mov_fd (float, default 0.5):
            Frame displacement threshold (in mm) to use for identifying bad
            frames.

        --mov_dvars (float, default 3.0):
            The (mean normalized) dvars threshold to use for identifying bad
            frames.

        --mov_dvarsme (float, default 1.5):
            The (median normalized) dvarsm threshold to use for identifying bad
            frames.

        --mov_after (int, default 0):
            How many frames after each frame identified as bad to also exclude
            from further processing and analysis.

        --mov_before (int, default 0):
            How many frames before each frame identified as bad to also exclude
            from further processing and analysis.

        --mov_bad (str, default 'udvarsme'):
            Which criteria to use for identification of bad frames (mov, dvars,
            dvarsme, idvars, uvars, idvarsme, udvarsme). See movement scrubbing
            documentation for further information.
            Criteria for identification of bad frames can be one out of:

            - 'mov'      ... Frame displacement threshold (fdt) is exceeded.
            - 'dvars'    ... Image intensity normalized root mean squared error
              (RMSE) threshold (dvarsmt) is exceeded.
            - 'dvarsme'  ... Median normalised RMSE (dvarsmet) threshold is
              exceeded.
            - 'idvars'   ... Both fdt and dvarsmt are exceeded (i for
              intersection).
            - 'uvars'    ... Either fdt or dvarsmt are exceeded (u for union).
            - 'idvarsme' ... Both fdt and dvarsmet are exceeded.
            - 'udvarsme' ... Either fdt or udvarsmet are exceeded.

            For more detailed description please see wiki entry on Movement
            scrubbing.

        --tr (float, default 2.5):
            TR of the BOLD files.

        --mov_pref (str, default ''):
            The prefix to be used for the figure plot files.

        --mov_plot (str, default 'mov_report'):
            The base name of the plot files. If set to empty no plots are
            generated.

        --mov_mreport (str, default 'movement_report.txt'):
            The name of the group movement report file. If set to an empty
            string, no file is generated.

        --mov_sreport (str, default 'movement_scrubbing_report.txt'):
            The name of the group scrubbing report file. If set to an empty
            string, no file is generated.

        --mov_preport (str, default 'movement_report_post.txt'):
            The name of group report file with stats computed with frames
            identified as bad exluded from analysis. If set to an empty
            string, no file is generated.

        --mov_post (str, default 'udvarsme'):
            The criterium for identification of bad frames that is used when
            generating a post scrubbing statistics group report:

            - 'fd'
            - 'dvars'
            - 'dvars'
            - 'dvarsme'
            - 'idvars'
            - 'idvarsme'
            - 'udvars'
            - 'udvarsme' ... default
            - 'none'.

        --mov_fidl (str, default 'udvarsme'):
            Whether to create fidl file snippets with listed bad frames, and
            what criterium to use for the definition of bad frames:

            - 'fd'
            - 'dvars'
            - 'dvars'
            - 'dvarsme'
            - 'idvars'
            - 'idvarsme'
            - 'udvars'
            - 'udvarsme' ... default
            - 'none'     ... Set to 'none' to not generate them.

        --mov_pdf (str, default 'movement_plots'):
            The name of the folder in sessions/QC/movement in which to copy
            the individuals' movement plots.

    Notes:
        Use:
            create_stats_report processes movement correction parameters and
            computed BOLD statistics to create per session plots and fidl
            snippets and group reports.

            For each session it saves into images/functional/movement:

            --`bold<nifti_tail>_<mov_plot>_cor.pdf`
                A plot of movement correction parameters for each of the BOLD
                files.
            --`bold<nifti_tail>_<mov_plot>_dvars.pdf`
                A plot of frame displacement and dvarsm statistics with frames
                that are identified as bad marked in blue.
            --`bold<nifti_tail>_<mov_plot>_dvarsme.pdf`
                A plot of frame displacement and dvarsme statistics with frames
                that are identified as bad marked in blue.
            --`bold[N]<nifti_tail>_scrub.fidl`
                A fidl filesnippet that lists, which frames are to be excluded
                from the analysis.

            For the group level it creates three report files that are stored in
            the <sessionsfolder>/QC/movement folder. These files are:

            - ``<mov_mreport>`` (bold<nifti_tail>_movement_report.txt by default)
                This file lists for each session and bold file mean, sd, range,
                max, min, median, and squared mean divided by max statistics for
                each of the 6 movement correction parameters. It also prints
                mean, median, maximum, and standard deviation of frame
                displacement statistics. The purpose of this file is to enable
                easy session and group level analysis of movement in the scanner.

            - ``<mov_preport>`` (bold<nifti_tail>_movement_report_post.txt by default)
                This file has the same structure and information as the above,
                with frames marked as bad excluded from the statistics
                computation. This enables session and group level assessment of
                the effects of scrubbing.

            - ``<mov_sreport>`` (bold<nifti_tail>_movement_scrubbing_report.txt by default)
                This file lists for each BOLD of each session the number and the
                percentage of frames that would be marked as bad and excluded
                from the analyses when a specific exclusion criteria would be
                used. Again, the file supports session and group level analysis
                of movement scrubbing.

            Extra notes and dependencies:
                The command runs the bold_stats.R R script that computes the
                statistics and plots the data. The function requires that
                movement correction parameters files and bold statistics data
                files (results of the compute_bold_stats command) are present in
                the expected locations.

                Session statistics are appended to the group level report files
                as they are being computed. To avoid messy group level files, it
                is recommended to run the command with parsessions set to 1
                (example 1), to enforce sequential processing and adding of
                information to group level statistics files. Another option is
                to run the processing in two steps. The first step with multiple
                parsessions to speed up generation of session level maps
                (example 2), and then the second step with a single core,
                omitting the slow generation of session specific plots.

    Examples:
        ::

            qunex create_stats_report \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --bolds=all \\
                --parsessions=1

        ::

            qunex create_stats_report \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --bolds=all \\
                --parsessions=10

        ::

            qunex create_stats_report \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --bolds=all \\
                --nifti_tail=_hp2000_clean \\
                --parsessions=1 \\
                --mov_plot=""
    """

    preport = {
        "plotdone": "done",
        "boldok": 0,
        "procok": "ok",
        "boldmissing": 0,
        "boldskipped": 0,
    }

    try:
        r = "\n---------------------------------------------------------"
        r += "\nSession id: %s \n[started on %s]" % (
            sinfo["id"],
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
        r += "\n\nCreating BOLD Movement and statistics report ..."
        r += "\n\n    Files in 'images%s/functional%s will be processed." % (
            options["img_suffix"],
            options["bold_variant"],
        )
        r += "\n\n    The command will use movement correction parameters and computed BOLD\n    statistics to create per session plots, fidl snippets and group reports. Only\n    images specified using --bolds parameter will be processed. Please\n    see documentation for use of other relevant parameters!"
        r += (
            "\n\n    Using parameters:\n\n    --mov_dvars: %(mov_dvars)s\n    --mov_dvarsme: %(mov_dvarsme)s\n    --mov_fd: %(mov_fd)s\n    --mov_radius: %(mov_radius)s\n    --mov_fidl: %(mov_fidl)s\n    --mov_post: %(mov_post)s\n    --mov_pref: %(mov_pref)s"
            % (options)
        )
        r += "\n\n........................................................"

        pc.doOptionsCheck(options, sinfo, "create_stats_report")
        d = pc.getSessionFolders(sinfo, options)

        if overwrite:
            ostatus = "will"
        else:
            ostatus = "will not"

        r += "\n\nWorking on BOLD information images in: " + d["s_bold_mov"]
        r += "\nResulting plots will be saved in: " + d["s_bold_mov"]

        r += (
            "\n\nBased on the settings, %s BOLD files will be processed (see --bolds)."
            % (", ".join(options["bolds"].split("|")))
        )
        r += (
            "\nIf already present, existing results %s be overwritten (see --overwrite)."
            % (ostatus)
        )

        procbolds = []
        d = pc.getSessionFolders(sinfo, options)

        # --- check for data

        if options["mov_plot"] != "":
            if (
                os.path.exists(
                    os.path.join(
                        d["s_bold_mov"],
                        options["mov_pref"] + options["mov_plot"] + "_cor.pdf",
                    )
                )
                and not overwrite
            ):
                r += "\n... Movement plots already exists! Please use option --overwrite=yes to redo them!"
                preport["plotdone"] = "old"
                plot = ""
            else:
                plot = options["mov_plot"]
                preport["plotdone"] = "new"
        else:
            plot = ""
            preport["plotdone"] = "none"

        r += "\n\nChecking for data in %s." % (d["s_bold_mov"])

        bolds, bskip, preport["boldskipped"], r = pc.useOrSkipBOLD(sinfo, options, r)

        for boldnum, boldname, boldtask, boldinfo in bolds:
            r += "\n\nWorking on: " + boldname + " ..."

            try:
                # --- filenames
                f = pc.getFileNames(sinfo, options)
                f.update(pc.getBOLDFileNames(sinfo, boldname, options))

                # --- check for data availability

                status = True

                if os.path.exists(d["s_bold_mov"]):
                    # --- movement
                    r, status = pc.checkForFile2(
                        r,
                        f["bold_mov"],
                        "\n    ... movement data present [%s]"
                        % (os.path.basename(f["bold_mov"])),
                        "\n    ... movement data missing [%s]"
                        % (os.path.basename(f["bold_mov"])),
                        status=status,
                    )
                    r, status = pc.checkForFile2(
                        r,
                        f["bold_stats"],
                        "\n    ... stats data present [%s]"
                        % (os.path.basename(f["bold_stats"])),
                        "\n    ... stats data missing [%s]"
                        % (os.path.basename(f["bold_stats"])),
                        status=status,
                    )
                    r, status = pc.checkForFile2(
                        r,
                        f["bold_scrub"],
                        "\n    ... scrub data present [%s]"
                        % (os.path.basename(f["bold_scrub"])),
                        "\n    ... scrub data missing [%s]"
                        % (os.path.basename(f["bold_scrub"])),
                        status=status,
                    )
                else:
                    r += "\n    ... folder does not exist!"
                    status = False

                # --- check
                if status:
                    procbolds.append(boldnum)
                    preport["boldok"] += 1
                else:
                    r += "\n---> ERROR: Files missing, skipping this bold run!"
                    preport["boldmissing"] += 1

            except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
                r += str(errormessage)
            except:
                r += (
                    "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
                    % (traceback.format_exc())
                )

        # run the R script

        procbolds.sort()
        procbolds = [str(e) for e in procbolds]

        report = {}

        for tf in ["mov_mreport", "mov_sreport", "mov_preport"]:
            if options[tf] != "":
                tmpf = os.path.join(
                    d["qc_mov"],
                    options["boldname"] + options["nifti_tail"] + "_" + options[tf],
                )
                report[tf] = tmpf
                if os.path.exists(tmpf) and thread == 1:
                    os.remove(tmpf)
            else:
                report[tf] = ""

        rcomm = (
            '%s --args -f=%s -mr=%s -pr=%s -sr=%s -s=%s -d=%.1f -e=%.1f -m=%.1f -rd=%.1f -tr=%.2f -fidl=%s -post=%s -plot=%s -pref=%s -rname=%s -bold_tail=%s -bolds="%s" -v'
            % (
                os.path.join(
                    os.environ["QUNEXPATH"], "r/qx_utilities", "bold_stats.R"
                ),  # script location
                d["s_bold_mov"],  # the folder to look for .dat data [.]
                report["mov_mreport"],  # the file to write movement report to [none]
                report[
                    "mov_preport"
                ],  # the file to write movement report after scrubbing to [none]
                report["mov_sreport"],  # the file to write scrubbing report to [none]
                sinfo["id"],  # session id to use in plots and reports [none]
                options[
                    "mov_dvars"
                ],  # threshold to use for computing dvars rejections [3]
                options[
                    "mov_dvarsme"
                ],  # threshold to use for computing dvarsme rejections [1.5]
                options[
                    "mov_fd"
                ],  # threshold to use for computing frame-to-frame movement rejections [0.5]
                options[
                    "mov_radius"
                ],  # radius (in mm) from center of head to cortex to estimate rotation size [50]
                options["tr"],  # TR to be used when generating .fidl files [2.5]
                options[
                    "mov_fidl"
                ],  # whether to output and what to base fild on (fd, dvars, dvarsme, u/ume - union, i/ime - intersection, none) [none]
                options[
                    "mov_post"
                ],  # whether to create report of scrubbing effect and what to base it on (fd, dvars, dvarsme, u/ume - union, i/ime - intersection, none) [none]
                plot,  # root name of the plot file, none to omit plotting [mov_report]
                options["mov_pref"],  # prefix for the reports
                options["boldname"],  # root name for the bold files
                options["nifti_tail"],  # tail for the volume bold files
                "|".join(procbolds),
            )
        )  # | separated list of bold indeces for which to do the stat report

        tfile = os.path.join(d["s_bold_mov"], ".r.ok")

        if options["print_command"] == "yes":
            r += "\n\nRunning\n" + rcomm + "\n"
        r, endlog, status, failed = pc.runExternalForFile(
            tfile,
            rcomm,
            "\nRunning bold_stats",
            overwrite=overwrite,
            thread=sinfo["id"],
            remove=options["log"] == "remove",
            task=options["command_ran"],
            logfolder=options["comlogs"],
            logtags=[options["bold_variant"], options["logtag"]],
            r=r,
        )
        if os.path.exists(tfile):
            preport["procok"] = "ok"
            os.remove(tfile)
        else:
            preport["procok"] = "failed"

        if options["mov_plot"] != "" and options["mov_pdf"] != "no":
            for sf in ["cor", "dvars", "dvarsme"]:
                tfolder = os.path.join(d["qc_mov"], options["mov_pdf"], sf)
                if not os.path.exists(tfolder):
                    os.makedirs(tfolder)

                froot = "%s%s_%s%s_%s.pdf" % (
                    options["boldname"],
                    options["nifti_tail"],
                    options["mov_pref"],
                    options["mov_plot"],
                    sf,
                )
                if os.path.exists(
                    os.path.join(tfolder, "%s-%s" % (sinfo["id"], froot))
                ):
                    os.remove(os.path.join(tfolder, "%s-%s" % (sinfo["id"], froot)))
                gc.link_or_copy(
                    os.path.join(d["s_bold_mov"], froot),
                    os.path.join(tfolder, "%s-%s" % (sinfo["id"], froot)),
                )
                r += "\n... copying %s to %s" % (
                    os.path.join(d["s_bold_mov"], froot),
                    os.path.join(tfolder, "%s-%s" % (sinfo["id"], froot)),
                )

        if (
            options["mov_fidl"]
            in ["fd", "dvars", "dvarsme", "udvars", "udvarsme", "idvars", "idvarsme"]
            and options["event_file"] != ""
            and options["bolds"] != ""
        ):
            concf = os.path.join(d["s_bold_concs"], options["bolds"] + ".conc")
            fidlf = os.path.join(d["s_bold_events"], options["event_file"] + ".fidl")
            ipatt = "_%s_scrub.fidl" % (options["mov_fidl"])

            if os.path.exists(concf) and os.path.exists(fidlf):
                try:
                    gm.meltmovfidl(concf, ipatt, fidlf, fidlf.replace(".fidl", ipatt))
                except:
                    r += "\nWARNING: Failed to create a melted fidl file!"
                    print(
                        "\nWARNING: Failed to create a melted fidl file! (%s)"
                        % (sinfo["id"])
                    )
                    raise
            else:
                r += "\nWARNING: Files missing, failed to create a melted fidl file!"

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r += str(errormessage)
        r += (
            "\nBOLD statistics and movement report failed on %s\n---------------------------------------------------------"
            % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        )
        preport["procok"] = "failed"
    except:
        r += (
            "\nBOLD statistics and movement report failed with and unknown error: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        preport["procok"] = "failed"

    if preport["procok"] == "ok":
        r += (
            "\n\nBOLD statistics and movement report completed on %s\n---------------------------------------------------------"
            % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        )

    rstatus = (
        "BOLDs ok: %(boldok)2d, missing data: %(boldmissing)2d, processing: %(procok)s, skipped: %(boldskipped)s"
        % (preport)
    )
    if preport["procok"] == "ok":
        rstatus += ", plots: %(plotdone)s" % (preport)

    # print r
    return (
        r,
        (
            sinfo["id"],
            rstatus,
            preport["boldmissing"] + (preport["procok"] == "failed"),
        ),
    )


def extract_nuisance_signal(sinfo, options, overwrite=False, thread=0):
    """
    ``extract_nuisance_signal [... processing options]``

    Extracts nuisance signal from volume BOLD files.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the session information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no).

        --bolds (str, default 'rest'):
            Which bold images (as they are specified in the batch.txt file) to
            copy over. It can be a single type (e.g. 'task'), a pipe separated
            list (e.g. 'WM|Control|rest') or 'all' to copy all.

        --boldname (str, default 'bold'):
            The default name of the bold files in the images folder.

        --nifti_tail (str, default ''):
            The tail of NIfTI volume images to use.

        --bold_variant (str, default ''):
            Optional variant of bold preprocessing. If specified, the BOLD
            images in `images/functional<bold_variant>` will be processed.

        --img_suffix (str, default ''):
            Specifies a suffix for 'images' folder to enable support for
            multiple parallel workflows. Empty if not used.

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

        --wbmask (str, default ''):
            A path to an optional file that specifies which regions are to be
            excluded from the whole-brain mask. It can be used in the case of
            ROI analyses for which one does not want to include the ROI specific
            signals in the global signal regression.

        --nroi (str, default ''):
            The path to additional nuisance regressors file. It can be either a
            binary mask or a '.names' file that specifies the ROI to be used.
            Based on other options, the ROI can be further masked by session
            specific files or not masked at all (see Use section below).

        --sessionroi (str, default ''):
            A string specifying which session specific mask to use for further
            masking the additional roi. The two options are 'wb' or 'aseg' for
            whole brain mask or FreeSurfer aseg+aparc mask, respectively.

        --shrinknsroi (str, default 'true'):
            A string specifying whether to shrink ('true') the whole
            brain and white matter masks or not ('false').

    Output files:
        The command generates the following files:

        - `bold[N]<nifti_tail>.nuisance`
              A text file that lists for each volume frame the information
              on mean intensity across the ventricle, white matter and whole
              brain voxels, and any additional nuisance ROI specified using
              parameters. The file is stored in the
              `images<img_suffix>/functional<bold_variant>/movement` folder.

        - `bold[N]<nifti_tail>_nuisance.png`
            A PNG image of axial slices of the first BOLD frame over which
            the identified nuisance regions are overlayed. Ventricles in
            green, white matter in red and the rest of the brain in blue.
            The ventricle and white matter regions are defined based on
            FreeSurfer segmentation. Each region is "trimmed" before use, so
            that there is at least one voxel buffer between each nuisance
            region mask. The image is stored in
            images<img_suffix>/ROI/nuisance<bold_variant>`.

        - `bold[N]<nifti_tail>_nuisance.<image format>`
            An image file of the relevant image format that holds the same
            information as the above PNG. It is a file of five volumes, the
            first volume holds the first BOLD frame, the second the whole
            brain mask, the third the ventricles mask and the fourth the
            white matter mask. The fifth volume stores all three masks coded
            as 1 (whole brain), 2 (ventricles), or 3 (white matter). The
            image is stored in `images<img_suffix>/ROI/nuisance<bold_variant>`
            folder.

    Notes:
        extract_nuisance_signal is used to extract nuisance signal from volume
        BOLD files to be used in the latter steps of preprocessing,
        specifically for regression of nuisance signals. By default, it
        extracts nuisance signals from ventricles, white matter and whole
        brain. Whole brain is defined as those parts of the brain that are not
        ventricles or white matter, which results in whole brain to mostly
        overlap with gray matter.

        Using parameters listed below, it is also possible to specify
        additional ROIs for which nuisance signal is to be extracted and/or ROI
        that are to be excluded from the whole brain mask.

        To exclude specific ROI from the whole brain mask, use the '--wbmask'
        option. This should be a path to a file that specifies, which ROI are
        to be excluded from the whole-brain mask. The reason for exclusion
        might be when one does not want the signals from specific ROI to be
        included in the global signal regression, thereby resolving some issues
        taken as arguments against using global signal regression. The file can
        be either a binary mask, or a '.names' file. In the latter case, it is
        possible to additional mask the ROI to be excluded based on session
        specific aseg+aparc image (see description of .names file format).

        Another option is to include additional independent nuisance regions
        that might or might not overlap with the existing masks. Two parameters
        are used to specify this. The first is the '--nroi' parameter. This,
        again, is a path to either a binary image or a '.names' file. In the
        latter case, it is again possible to mask the additional ROI either by
        the binary whole brain mask or the individuals aseg+aparc file. To
        achieve this, set the additional '--sessionroi' parameter to 'wb' or
        'aseg', respectively. If some additional ROI are to be excluded, even
        though they fall outside the brain, then these are to be listed as
        comma separated list of ROI names (that match the ROI names in the
        .names file), separated from the path by a pipe ('|') symbol. For
        instance if one also would like to include eyes and scull as two
        additional nuiscance regions, one has to create a volume mask + a
        .names file pair, and pass it as the '--nroi' parameter, e.g.::

            --nroi="<path to ROI>/nroi.names|eyes,scull"

        Extra notes and dependencies:
            When 'cifti' is the specified image target, the related nifti volume
            files will be processed as only they provide all the information for
            computing the relevant parameters

            The command runs the general_extract_nuisance.m Matlab function for
            actual nuisance signal extraction. It expects that bold images,
            whole brain masks, and aseg+aparc imags to be present in the
            expected locations.

    Examples:
        ::

            qunex extract_nuisance_signal \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --bolds=all \\
                --parsessions=10
    """

    report = {
        "bolddone": 0,
        "boldok": 0,
        "boldfail": 0,
        "boldmissing": 0,
        "boldskipped": 0,
    }

    r = "\n---------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n\nExtracting BOLD nuisance signal ..."
    r += "\n\n    Files in 'images%s/functional%s will be processed." % (
        options["img_suffix"],
        options["bold_variant"],
    )
    r += (
        "\n\n    The command will extract nuisance signal from each of the specified BOLD files.\n    The results will be saved as %s[N]%s.nuisance files in the images%s/movement\n    subfolder. Only images specified using --bolds parameter will be\n    processed (see documentation). Do also note that even if cifti is specifed as\n    the target format, nifti volume image will be used to extract nuisance signal."
        % (options["boldname"], options["nifti_tail"], options["img_suffix"])
    )
    r += (
        "\n\n    Using parameters:\n\n    --wbmask: %(wbmask)s\n    --sessionroi: %(sessionroi)s\n    --nroi: %(nroi)s\n    --shrinknsroi: %(shrinknsroi)s"
        % (options)
    )
    r += "\n\n    when extracting nuisance signal."
    r += "\n\n........................................................"

    pc.doOptionsCheck(options, sinfo, "extract_nuisance_signal")
    d = pc.getSessionFolders(sinfo, options)

    if overwrite:
        ostatus = "will"
    else:
        ostatus = "will not"

    r += "\n\nWorking on BOLD images in: " + d["s_bold"]
    r += "\nResulting files will be in: " + d["s_bold_mov"]
    r += "\n\nBased on the settings, %s BOLD files will be processed (see --bolds)." % (
        ", ".join(options["bolds"].split("|"))
    )
    r += (
        "\nIf already present, existing nuisance files %s be overwritten (see --overwrite)."
        % (ostatus)
    )

    bolds, bskip, report["boldskipped"], r = pc.useOrSkipBOLD(sinfo, options, r)

    parelements = options["parelements"]
    r += "\nProcessing %d BOLDs in parallel" % (parelements)

    if parelements == 1:  # serial execution
        for b in bolds:
            # process
            result = executeExtractNuisanceSignal(sinfo, options, overwrite, b)

            # merge r
            r += result["r"]

            # merge report
            tempReport = result["report"]
            report["bolddone"] += tempReport["bolddone"]
            report["boldok"] += tempReport["boldok"]
            report["boldfail"] += tempReport["boldfail"]
            report["boldmissing"] += tempReport["boldmissing"]
    else:  # parallel execution
        # create a multiprocessing Pool
        processPoolExecutor = ProcessPoolExecutor(parelements)
        # process
        f = partial(executeExtractNuisanceSignal, sinfo, options, overwrite)
        results = processPoolExecutor.map(f, bolds)

        # merge r and report
        for result in results:
            r += result["r"]
            tempReport = result["report"]
            report["bolddone"] += tempReport["bolddone"]
            report["boldok"] += tempReport["boldok"]
            report["boldfail"] += tempReport["boldfail"]
            report["boldmissing"] += tempReport["boldmissing"]

    r += (
        "\n\nBold nuisance signal extraction completed on %s\n---------------------------------------------------------"
        % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    )
    rstatus = (
        "BOLDS done: %(bolddone)2d, missing data: %(boldmissing)2d, failed: %(boldfail)2d, skipped: %(boldskipped)2d, processed: %(boldok)2d"
        % (report)
    )

    print(r)
    return (r, (sinfo["id"], rstatus, report["boldmissing"] + report["boldfail"]))


def executeExtractNuisanceSignal(sinfo, options, overwrite, boldData):
    # extract data
    boldnum = boldData[0]
    boldname = boldData[1]

    # prepare return variables
    r = ""
    report = {"bolddone": 0, "boldok": 0, "boldfail": 0, "boldmissing": 0}

    r += "\n\nWorking on: " + boldname + " ..."

    try:
        # --- filenames
        f = pc.getFileNames(sinfo, options)
        f.update(pc.getBOLDFileNames(sinfo, boldname, options))
        d = pc.getSessionFolders(sinfo, options)

        # --- check for data availability

        r += "\n... checking for data"
        status = True

        # --- bold mask
        r, status = pc.checkForFile2(
            r,
            f["bold1_brain_mask"],
            "\n    ... bold brain mask present",
            "\n    ... bold brain mask missing [%s]" % (f["bold1_brain_mask"]),
            status=status,
        )

        # --- aseg
        r, astat = pc.checkForFile2(
            r,
            f["fs_aseg_bold"],
            "\n    ... freesurfer aseg present",
            "\n    ... freesurfer aseg missing [%s]" % (f["fs_aseg_bold"]),
            status=True,
        )
        if not astat:
            r, astat = pc.checkForFile2(
                r,
                f["fs_aparc_bold"],
                "\n    ... freesurfer aparc present",
                "\n    ... freesurfer aparc missing [%s]" % (f["fs_aparc_bold"]),
                status=True,
            )
            segfile = f["fs_aparc_bold"]
        else:
            segfile = f["fs_aseg_bold"]

        status = status and astat

        # --- bold
        r, status = pc.checkForFile2(
            r,
            f["bold_vol"],
            "\n    ... bold data present",
            "\n    ... bold data missing [%s]" % (f["bold_vol"]),
            status=status,
        )

        # --- check
        if not status:
            r += "\n---> ERROR: Files missing, skipping this bold run!"
            report["boldmissing"] += 1
            return {"r": r, "report": report}

        # --- running nuisance extraction

        comm = (
            "%s \"try general_extract_nuisance('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, %s); catch ME, general_report_crash(ME); exit(1), end; exit\""
            % (
                mcommand,  # --- matlab command to run
                f["bold_vol"],  # --- bold volume file to process
                segfile,  # --- aseg or aparc file
                f["bold1_brain_mask"],  # --- bold brain mask
                d["s_bold_mov"],  # --- functional/movement subfolder
                d["s_nuisance"],  # --- roi/nuisance subfolder
                options["wbmask"],  # --- mask to exclude ROI from WB
                options["sessionroi"],  # --- a mask used to specify session specific WB
                options["nroi"],  # --- additional nuisance regressors ROI
                options["shrinknsroi"],  # --- shrink nuisance signal ROI
                "true",
            )
        )  # --- verbosity

        if options["print_command"] == "yes":
            r += "\n\nRunning\n" + comm + "\n"

        runit = True
        if os.path.exists(f["bold_nuisance"]):
            report["bolddone"] += 1
            runit = False
        r, endlog, status, failed = pc.runExternalForFile(
            f["bold_nuisance"],
            comm,
            "... running matlab general_extract_nuisance on %s" % (f["bold_vol"]),
            overwrite,
            thread=sinfo["id"],
            remove=options["log"] == "remove",
            task=options["command_ran"],
            logfolder=options["comlogs"],
            logtags=[options["bold_variant"], options["logtag"], "B%d" % boldnum],
            r=r,
            shell=True,
        )
        r, status = pc.checkForFile(
            r,
            f["bold_nuisance"],
            "ERROR: Matlab/Octave has failed preprocessing BOLD using command: %s"
            % (comm),
        )

        if runit and status:
            report["boldok"] += 1
        elif runit:
            report["boldfail"] += 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r += str(errormessage)
        report["boldfail"] += 1
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        report["boldfail"] += 1

    return {"r": r, "report": report}


def preprocess_bold(sinfo, options, overwrite=False, thread=0):
    """
    ``preprocess_bold [... processing options]``

    Prepares BOLD files for further functional connectivity analysis.

    Notes:
        List of bold files specify, which types of bold files are to be
        processed, as they are specified in the batch.txt file. An example of a
        list of bolds in batch.txt would be::

            07: bold1:blink       :BOLD blink 3mm 48 2.5s
            08: bold2:flanker     :BOLD flanker 3mm 48 2.5s
            09: bold3:EC          :BOLD EC 3mm 48 2.5s
            10: bold4:mirror      :BOLD mirror 3mm 48 2.5s
            11: bold5:rest        :RSBOLD 3mm 48 2.5s

        With --bolds set to "blink|EC|rest", bold1, 3, and 5 would be processed.
        If it were set to "all", all would be processed. As each bold gets
        processed independently and only one fidl file can be specified, you
        are advised to use preprocess_conc when regressing task structure, and
        only use preprocess_bold for resting state data. If you would still use
        like to regress out events specified in a fidl file. They would neet to
        be named as [<session id>_]<boldname>_<image_target>_<fidl name>.fidl.
        In the case of cifti files, image_target is composed of
        <cifti_tail>_cifti. If the files are not present in the relevant
        individual sessions's folders, they are searched for in the
        <sessionsfolder>/inbox/events folder. In that case the "<session id>_"
        is not optional but required.

        The --bold_actions parameter specifies the actions, denoted by a single 
        letter, that will be executed in the sequence listed:

        --m
            Motion scrubbing.
        --s
            Spatial smoothing.
        --h
            High-pass filtering.
        --r
            Regression (nuisance and/or task) with an optional number 0, 1, or 2
            specifying the type of regression to use (see REGRESSION below).
        --l
            Low-pass filtering.
        --c
            Save beta coefficients as well.

        So the default 's,h,r,c,l' bold_actions parameter would lead to the
        files first being smoothed, then high-pass filtered. Next a regression
        step would follow in which nuisance signal and/or task related signal
        would be estimated and regressed out, then the related beta estimates
        would be saved. Lastly the BOLDs would be also low-pass filtered.

        Use:
            preprocess_bold is a complex command initially used to prepare BOLD
            files for further functional connectivity analysis. The function
            enables the following actions:

            - spatial smoothing (3D or 2D for cifti files)
            - temporal filtering (high-pass, low-pass)
            - removal of nuisance signal and task structure

            The function makes use of a number of files and accepts a long list
            of arguments that make it very powerful and flexible but also
            require care in its use. What follows is a detailed documentation
            of its actions and parameters organized by actions in the order
            they would be most commonly done. Use and parameter description
            will be intertwined.

        Scrubbing:
            The command either makes use of scrubbing information or performs
            scrubbing comuputation on its own (when 'm' is part of the
            command). In the latter case, all the scrubbing parameters need to
            be specified:

            --mov_radius (int, default 50):
                Estimated head radius (in mm) for computing frame displacement
                statistics.
            --mov_fd (float, default 0.5):
                Frame displacement threshold (in mm) to use for identifying bad
                frames.
            --mov_dvars (float, default 3.0):
                The (mean normalized) dvars threshold to use for identifying bad
                frames.
            --mov_dvarsme (float, default 1.5):
                The (median normalized) dvarsm threshold to use for identifying
                bad frames.
            --mov_after (int, default 0):
                How many frames after each frame identified as bad to also
                exclude from further processing and analysis.
            --mov_before (int, default 0):
                How many frames before each frame identified as bad to also
                exclude from further processing and analysis.
            --mov_bad (str, default 'udvarsme'):
                Which criteria to use for identification of bad frames.

            Criteria for identification of bad frames can be one out of:

            --mov
                Frame displacement threshold (fdt) is exceeded.
            --dvars
                Image intensity normalized root mean squared error (RMSE)
                threshold (dvarsmt) is exceeded.
            --dvarsme
                Median normalised RMSE (dvarsmet) threshold is exceeded.
            --idvars
                Both fdt and dvarsmt are exceeded (i for intersection).
            --uvars
                Either fdt or dvarsmt are exceeded (u for union).
            --idvarsme
                Both fdt and dvarsmet are exceeded.
            --udvarsme
                Either fdt or udvarsmet are exceeded.

            For more detailed description please see wiki entry on Movement
            scrubbing.

            In any case, if scrubbing was done beforehand or as a part of this
            command, one has to specify, how the scrubbing information is used:

            --pignore
                String describing how to deal with bad frames.

            The string has the following format::

                'hipass:<filtering opt.>|regress:<regression opt.>|lopass:<filtering opt.>'

            Filtering options are:

            --keep
                Keep all the bad frames unchanged.
            --linear
                Replace bad frames with linear interpolated values based on
                neighboring good frames.
            --spline
                Replace bad frames with spline interpolated values based on
                neighboring good frames.

            To prevent artifacts present in bad frames to be temporarily spread,
            use either 'linear' or 'spline' options.

            Regression options are:

            --keep
                Keep the bad frames and use them in the regression.
            --ignore
                Exclude bad frames from regression.
            --mark
                Exclude bad frames from regression and mark the bad frames as
                NaN.
            --linear
                Replace bad frames with linear interpolated values based on
                neighboring good frames.
            --spline
                Replace bad frames with spline interpolated values based on
                neighboring good frames.

            Please note that when the bad frames are not kept, the original
            values will be retained in the residual signal. In this case they
            have to be excluded or ignored also in all following analyses,
            otherwise they can be a significant source of artifacts.

        Spatial smoothing:
            Volume smoothing:
                For volume formats the images will be smoothed using the
                img_smooth_3d nimage method. For cifti format the smooting will
                be done by calling the relevant wb_command command. The
                smoothing parameters are:

                --voxel_smooth (int, default 1):
                    Gaussian smoothing FWHM in voxels.
                --smooth_mask (str, default false):
                    Whether to smooth only within a mask, and what mask to use
                    (nonzero|brainsignal|brainmask|<filename>|false).
                --dilate_mask (str, default false):
                    Whether to dilate the image after masked smoothing and what
                    mask to use
                    (nonzero|brainsignal|brainmask|same|<filename>|false).

                If a smoothing mask is set, only the signal within the specified
                mask will be used in the smoothing. If a dilation mask is set,
                after smoothing within a mask, the resulting signal will be
                constrained / dilated to the specified dilation mask.

                For both parameters the possible options are:

                --nonzero
                    Mask will consist of all the nonzero voxels of the first
                    BOLD frame.
                --brainsignal
                    Mask will consist of all the voxels that are of value 300 or
                    higher in the first BOLD frame (this gave a good coarse
                    brain mask for images intensity normalized to mode 1000 in
                    the NIL preprocessing stream).
                --brainmask
                    Mask will be the actual bet extracted brain mask based on
                    the first BOLD frame (generated using in the
                    creatBOLDBrainMasks command).
                --filename
                    All the non-zero voxels in a specified volume file will be
                    used as a mask.
                --false
                    No mask will be used.
                --same
                    Only for dilate_mask, the mask used will be the same as
                    smoothing mask.

            Cifti smoothing:
                For cifti format images, smoothing will be run using wb_command.
                The following parameters can be set:

                --surface_smooth (float, default 2.0):
                    FWHM for Gaussian surface smoothing in mm.
                --volume_smooth (float, default 2.0):
                    FWHM for Gaussian volume smoothing in mm.
                --framework_path (str, default ''):
                    The path to framework libraries on the Mac system. No need
                    to use it currently if installed correctly.
                --wb_command_path (str, default ''):
                    The path to the wb_command executive. No need to use it
                    currently if installed correctly.

                Results:
                    The resulting smoothed files are saved with '_s' added to
                    the BOLD root filename.

        Temporal filtering:
            Temporal filtering is accomplished using img_filter nimage method.
            The code is adopted from the FSL C++ code enabling appropriate
            handling of bad frames (as described above - see SCRUBBING). The
            parameters are:

            --hipass_filter (float, default 0.008):
                The frequency for high-pass filtering in Hz.
            --lopass_filter (float, default 0.09):
                The frequency for low-pass filtering in Hz.

            Please note that the values finally passed to img_filter method are
            the respective sigma values computed from the specified frequencies
            and TR.

            Filtering of nuisance signal, movement, task, and events
            Besides data, nuisance signal, motion parameters, and event 
            regressors can be filtered as well. What to filter beside data can
            be specified by a comma separated list using the following 
            parameters:
            
            --hipass_do (str, default 'nuisance')
                What to high-pass filter besides data – options are: nuisance, 
                movement, events, task. Default is 'nuisance'.
 
            --lopass_do (str, default 'nuisance,movement,task,events')
                What to lo-pass filter besides data – options are: nuisance, 
                movement, events, task. Default is 'nuisance, movement, task, 
                events'.
            
            Note that 'events' refers to regressors created based on events 
            as specified in the fidl file, whereas 'task' refers to a task
            matrix that is passed directy in the matlab function call.

            Results:
                The resulting filtered files are saved with '_hpss' or '_bpss'
                added to the BOLD root filename for high-pass and low-pass
                filtering, respectively.

        Regression:
            Regression is a complex step in which GLM is used to estimate the
            beta weights for the specified nuisance regressors and events. The
            resulting beta weights are then stored in a GLM file (a regular
            file with additional information on the design used) and residuals
            are stored in a separate file. This step can therefore be used for
            two purposes: (1) to remove nuisance signal and event structure
            from BOLD files, removing unwanted potential sources of correlation
            for further functional connectivity analyses, and (2) to get task
            beta estimates for further activation analyses. The following
            parameters are used in this step:

            --bold_nuisance (str, default 'm,m1d,mSq,m1dSq,V,WM,WB,1d'):
                A comma separated list of regressors to include in GLM.
                Possible values are:

                - 'm'     ... motion parameters
                - 'm1d'   ... first derivative of motion parameters
                - 'mSq'   ... squared motion parameters
                - 'm1dSq' ... squared first derivative of motion parameters
                - 'V'     ... ventricles signal
                - 'WM'    ... white matter signal
                - 'WB'    ... whole brain signal
                - '1d'    ... first derivative of above nuisance signals
                - 'e'     ... events listed in the provided fidl files.

            --event_string (str, default ''):
                A string describing, how to model the events listed in the
                provided fidl files.
            --glm_matrix (str, default 'none'):
                Whether to save the GLM matrix as a text file ('text'), a png
                image file ('image'), both ('both') or not ('none').
            --glm_results (str, default 'c,r')
                A string  which of the GLM analysis results are saved.
                Possible values are:

                - 'c'   ... Saving of resulting beta coefficients.
                - 'z'   ... Saving of resulting z-scores of beta coefficients.
                - 'p'   ... Saving of session-level coefficient p-values.
                - 'se'  ... Saving of standard errors of beta coefficients.
                - 'r'   ... Saving of resulting residuals of the GLM.
                - 'all' ... Saving all of the results above.

            --glm_name (str, default ''):
                An additional name to add to the residuals and GLM files to
                distinguish between different possible models used.

        GLM modeling:
            There are two important variables that affect the exact GLM
            model used to estimate nuisance and task beta coefficients and
            regress them from the signal. The first is the optional number
            following the 'r' command in the --bold_actions parameter.
            There are three options:

            - '0' ... Estimate nuisance regressors for each bold file
                separately, however, model events across all bold files (the
                default if no number is) specified.
            - '1' ... Estimate both nuisance regressors and task regressors
                for each bold run separately.
            - '2' ... Estimate both nuisance regressors as well as task
                regressors across all bold runs.

            The second key variable is the event string provided by the
            event_string parameter. The event string is a pipe ('|')
            separated list of regressor specifications. The possibilities
            are discussed below:

            Unassumed Modeling:
                ::

                    <fidl code>:<length in frames>

                Where <fidl code> is the code for the event used in the fidl
                file, and <length in frames> specifies, for how many frames
                of the bold run (since the onset of the event) the event
                should be modeled.

            Assumed Modeling:
                ::

                    <fidl code>:<hrf>[-run|-uni][:<length>]

                Where <fidl code> is the same as above, <hrf> is the type of
                the hemodynamic response function to use, '-run' and '-uni'
                specify how the regressor should be normalized, and
                <length> is an optional parameter, with its value dependent
                on the model used. The allowed <hrf> are:

                - 'boynton' ... uses the Boynton HRF
                - 'SPM'     ... uses the SPM double gaussian HRF
                - 'u'       ... unassumed (see above)
                - 'block'   ... block response.

                For the first two, the <length> parameter is optional and
                would override the event duration information provided in
                the fidl file. For 'u' the length is the same as in
                previous section: the number of frames to model. For
                'block' length should be two numbers separated by a colon
                (e.g. 2:9) that specify the start and end offset (from the
                event onset) to model as a block.

                Assumed HRF regressors normalization:
                    hrf_types `boynton` and `SPM` can be marked with an
                    additional flag denoting how to normalize the
                    regressor.

                    In case of `<hrf function>-uni`, e.g. 'boynton-uni' or
                    'SPM-uni', the HRF function will be normalized to have
                    the area under the curve equal to 1. This ensures
                    uniform and universal, scaling of the resulting
                    regressor across all event lengths. In addition, the
                    scaling is not impacted by weights (e.g. behavioral
                    coregressors), which in turn ensures that the weights
                    are not scaled.

                    In case of `<hrf function>-run`, e.g. `boynton-run` or
                    `SPM-run`, the resulting regressor is normalized to
                    amplitude of 1 within each bold run separately. This
                    can result in different scaling of regressors with
                    different durations, and of the same regressor across
                    different runs. Scaling in this case is performed after
                    the signal is weighted, so in effect the scaling of
                    weights (e.g. behavioral regressors), can differ across
                    bold runs.

                    The flag can be abbreviated to '-r' and '-u'. If not
                    specified, '-run' will be assumed (the default might
                    change).

        Naming And Behavioral Regressors:
            Each of the above (unassumed and assumed modeling
            specification) can be followed by a ">" (greater-than
            character), which signifies additional information in the
            form::

                <name>[:<column>[:<normalization_span>[:<normalization_method>]]]

            --name
                The name of the resulting regressor.
            --column
                The number of the additional behavioral regressors
                column in the fidl file (1-based) to use as a weight
                for the regressors.
            --normalization_span
                Whether to normalize the behavioral weight within a
                specific event type ('within') or across all events
                ('across'). [within]
            --normalization_method
                The method to use for normalization. Options are:

                - 'z'    (compute Z-score)
                - '01'   (normalize to fixed range 0 to 1)
                - '-11'  (normalize to fixed range -1 to 1)
                - 'none' (use weights as provided in fidl file)

                Example string::

                    'block:boynton|target:9|target:9>target_rt:1:within:z'

                This would result in three sets of task regressors: one
                assumed task regressor for the sustained activity across
                the block, one unassumed task regressor set spanning 9
                frames that would model the presentation of the target, and
                one behaviorally weighted unassumed regressor that would
                for each frame estimate the variability in response as
                explained by the reaction time to the target.

        Results:
            This step results in the following files (if requested):

            - residual image (``<root>_res-<regressors>.<ext>``)
            - GLM coefficient image (``<root>_res-<regressors>_coeff.<ext>``)

            If you want more specific GLM results and information, please use
            preprocess_conc command.

    Examples:
        ::

            qunex preprocess_bold \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --bolds=rest \\
                --bold_actions="s,h,r,c,l" \\
                --bold_nuisance="m,V,WM,WB,1d" \\
                --mov_bad=udvarsme \\
                --pignore="hipass=linear|regress=ignore|lopass=linear"
    """

    pc.doOptionsCheck(options, sinfo, "preprocess_bold")

    r = "\n---------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\nPreprocessing %s BOLD files as specified in --bolds." % (
        ", ".join(options["bolds"].split("|"))
    )
    r += "\nFiles in 'images%s/functional%s will be processed." % (
        options["img_suffix"],
        options["bold_variant"],
    )
    r += "\n%s Preprocessing bold runs ..." % (pc.action("Running", options["run"]))

    report = {
        "done": [],
        "processed": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    bolds, bskip, report["boldskipped"], r = pc.useOrSkipBOLD(sinfo, options, r)
    report["skipped"] = [str(n) for n, b, t, v in bskip]

    parelements = options["parelements"]
    r += "\nProcessing %d BOLDs in parallel" % (parelements)

    if parelements == 1:  # serial execution
        for b in bolds:
            # process
            result = executePreprocessBold(sinfo, options, overwrite, b)

            # merge r
            r += result["r"]

            # merge report
            tempReport = result["report"]
            report["done"] += tempReport["done"]
            report["processed"] += tempReport["processed"]
            report["failed"] += tempReport["failed"]
            report["ready"] += tempReport["ready"]
            report["not ready"] += tempReport["not ready"]
    else:  # parallel execution
        # create a multiprocessing Pool
        processPoolExecutor = ProcessPoolExecutor(parelements)
        # process
        f = partial(executePreprocessBold, sinfo, options, overwrite)
        results = processPoolExecutor.map(f, bolds)

        # merge r and report
        for result in results:
            r += result["r"]
            tempReport = result["report"]
            report["done"] += tempReport["done"]
            report["processed"] += tempReport["processed"]
            report["failed"] += tempReport["failed"]
            report["ready"] += tempReport["ready"]
            report["not ready"] += tempReport["not ready"]

    r += (
        "\n\nBold preprocessing completed on %s\n---------------------------------------------------------"
        % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    )
    if options["run"] == "run":
        rstatus = (
            "bolds: %d ready [%s], %d not ready [%s], %d already processed [%s], %d ran ok [%s], %d failed [%s], %d skipped [%s]"
            % (
                len(report["ready"]),
                " ".join(report["ready"]),
                len(report["not ready"]),
                " ".join(report["not ready"]),
                len(report["done"]),
                " ".join(report["done"]),
                len(report["processed"]),
                " ".join(report["processed"]),
                len(report["failed"]),
                " ".join(report["failed"]),
                len(report["skipped"]),
                " ".join(report["skipped"]),
            )
        )
    else:
        rstatus = (
            "bolds: %d ready [%s], %d not ready [%s], %d already processed [%s], %d skipped [%s]"
            % (
                len(report["ready"]),
                " ".join(report["ready"]),
                len(report["not ready"]),
                " ".join(report["not ready"]),
                len(report["done"]),
                " ".join(report["done"]),
                len(report["skipped"]),
                " ".join(report["skipped"]),
            )
        )

    # print r
    return (r, (sinfo["id"], rstatus, len(report["not ready"]) + len(report["failed"])))


def executePreprocessBold(sinfo, options, overwrite, boldData):
    # extract data
    boldnum = boldData[0]
    boldname = boldData[1]

    # prepare return variables
    r = ""
    report = {"done": [], "processed": [], "failed": [], "ready": [], "not ready": []}

    boldnum = str(boldnum)

    r += "\n\nWorking on: " + boldname + " ..."

    try:
        # --- define the tail

        options["bold_tail"] = options["nifti_tail"]
        if options["image_target"] in ["cifti", "dtseries", "ptseries"]:
            options["bold_tail"] = options["cifti_tail"]

        # --- filenames and folders

        f = pc.getFileNames(sinfo, options)
        f.update(pc.getBOLDFileNames(sinfo, boldname, options))
        d = pc.getSessionFolders(sinfo, options)

        # --- check for data availability

        r += "\n... checking for data"
        status = True

        # --- movement
        if "r" in options["bold_actions"] and (
            "m" in options["bold_nuisance"] or "m" in options["bold_actions"]
        ):
            r, status = pc.checkForFile2(
                r,
                f["bold_mov"],
                "\n    ... movement data present",
                "\n    ... movement data missing [%s]" % (f["bold_mov"]),
                status=status,
            )

        # --- bold stats
        if "m" in options["bold_actions"]:
            r, status = pc.checkForFile2(
                r,
                f["bold_stats"],
                "\n    ... bold statistics data present",
                "\n    ... bold statistics data missing [%s]" % (f["bold_stats"]),
                status=status,
            )

        # --- bold scrub
        if any([e in options["pignore"] for e in ["linear", "spline", "ignore"]]):
            r, status = pc.checkForFile2(
                r,
                f["bold_scrub"],
                "\n    ... bold scrubbing data present",
                "\n    ... bold scrubbing data missing [%s]" % (f["bold_scrub"]),
                status=status,
            )

        # --- check for files if doing regression

        if "r" in options["bold_actions"]:
            # --- nuisance data
            if any([e in options["bold_nuisance"] for e in ["V", "WM", "WB"]]):
                r, status = pc.checkForFile2(
                    r,
                    f["bold_nuisance"],
                    "\n    ... bold nuisance signal data present",
                    "\n    ... bold nuisance signal data missing [%s]"
                    % (f["bold_nuisance"]),
                    status=status,
                )

            # --- event
            if "e" in options["bold_nuisance"]:
                r, status = pc.checkForFile2(
                    r,
                    f["bold_event"],
                    "\n    ... event data present",
                    "\n    ... even data missing [%s]" % (f["bold_event"]),
                    status=status,
                )

        # --- bold
        r, status = pc.checkForFile2(
            r,
            f["bold"],
            "\n    ... bold data present",
            "\n    ... bold data missing [%s]" % (f["bold"]),
            status=status,
        )

        # --- results
        r, alreadyDone = pc.checkForFile2(
            r, f["bold_final"], "\n    ... result present", ""
        )

        # --- check
        if not status:
            r += "\n---> ERROR: Files missing, skipping this bold run!"
            report["not ready"].append(boldnum)
            return {"r": r, "report": report}
        else:
            report["ready"].append(boldnum)

        if alreadyDone:
            report["done"].append(boldnum)

        # --- run matlab preprocessing script

        if overwrite:
            boldow = "true"
        else:
            boldow = "false"

        scrub = (
            "radius:%(mov_radius)d|fdt:%(mov_fd).2f|dvarsmt:%(mov_dvars).2f|dvarsmet:%(mov_dvarsme).2f|after:%(mov_after)d|before:%(mov_before)d|reject:%(mov_bad)s"
            % (options)
        )
        opts = (
            "boldname=%(boldname)s|surface_smooth=%(surface_smooth)f|volume_smooth=%(volume_smooth)f|voxel_smooth=%(voxel_smooth)f|hipass_filter=%(hipass_filter)f|lopass_filter=%(lopass_filter)f|framework_path=%(framework_path)s|wb_command_path=%(wb_command_path)s|smooth_mask=%(smooth_mask)s|dilate_mask=%(dilate_mask)s|glm_matrix=%(glm_matrix)s|glm_residuals=%(glm_residuals)s|glm_results=%(glm_results)s|glm_name=%(glm_name)s|bold_tail=%(bold_tail)s|ref_bold_tail=%(nifti_tail)s|bold_variant=%(bold_variant)s|img_suffix=%(img_suffix)s"
            % (options)
        )

        mcomm = (
            "fc_preprocess('%s', %s, %d, '%s', '%s', %s, '%s', %f, '%s', '%s', %s, '%s', '%s', '%s', '%s')"
            % (
                d["s_base"],  # --- sessions folder
                boldnum,  # --- number of bold file to process
                options[
                    "omit"
                ],  # --- number of frames to skip at the start of each run
                options[
                    "bold_actions"
                ],  # --- which steps to perform (s, h, r, c, p, p, z)
                options[
                    "bold_nuisance"
                ],  # --- what to regress (m, m1d, mSq, m1dSq, V, WM, WB, d, t, e, 1d)
                "[]",  # --- matrix of task regressors
                options["event_file"],  # --- fidl file to be used
                options["tr"],  # --- TR of the data
                options[
                    "event_string"
                ],  # --- event string specifying what and how of the task to regress
                options["bold_prefix"],  # --- prefix to the bold files
                boldow,  # --- whether to overwrite the existing files
                gi.getImgFormat(
                    f["bold_final"]
                ),  # --- what file extension to expect and use (e.g. '.nii', .'.4dfp.img')
                scrub,  # --- scrub parameters
                options[
                    "pignore"
                ],  # --- how to deal with bad frames ('hipass:keep/linear/spline|regress:keep/ignore|lopass:keep/linear/spline')
                opts,
            )
        )  # --- additional options

        comm = '%s "try %s; catch ME, general_report_crash(ME); exit(1), end; exit"' % (
            mcommand,
            mcomm,
        )

        # r += '\n ... running: %s' % (comm)
        if options["run"] == "run":
            if alreadyDone and not overwrite:
                r += "\n\nProcessing already completed! Set overwrite to yes to redo processing!\n"
            else:
                if options["print_command"] == "yes":
                    r += "\n\nRunning\n" + comm + "\n"
                r, endlog, status, failed = pc.runExternalForFile(
                    f["bold_final"],
                    comm,
                    "running matlab/octave fc_preprocess on %s bold %s"
                    % (d["s_bold"], boldnum),
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[
                        options["bold_variant"],
                        options["glm_name"],
                        options["logtag"],
                        "B%s" % (boldnum),
                    ],
                    r=r,
                    shell=True,
                )
                r, status = pc.checkForFile(
                    r,
                    f["bold_final"],
                    "ERROR: Matlab/Octave has failed preprocessing BOLD using command: \n---> %s\n"
                    % (mcomm),
                )
                if status:
                    report["processed"].append(boldnum)
                else:
                    report["failed"].append(boldnum)
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r += str(errormessage)
        report["failed"].append(boldnum)
    except:
        r += (
            "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
            % (traceback.format_exc())
        )
        time.sleep(5)
        report["failed"].append(boldnum)

    return {"r": r, "report": report}


def preprocess_conc(sinfo, options, overwrite=False, thread=0):
    r"""
    ``preprocess_conc [... processing options]``

    Performs spatial smoothing, temporal filtering, removal of nuisance signals
    and complex modeling of events.

    preprocess_conc is a complex general purpose command implementing spatial
    and temporal filtering, and multiple regression (GLM) to enable both
    preprocessing and denoising of BOLD files for further analysis, as well as
    complex activation modeling that creates GLM files for second-level
    analyses. The function enables the following actions:

    - spatial smoothing (3D or 2D for cifti files)
    - temporal filtering (high-pass, low-pass)
    - removal of nuisance signal
    - complex modeling of events.

    The function makes use of a number of files and accepts a long list of
    arguments that make it very powerful and flexible but also require care in
    its use. What follows is a detailed documentation of its actions and
    parameters organized by actions in the order they would be most commonly
    done. Use and parameter description will be intertwined.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the session information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging  data is
            supposed to go.

        --parsessions (str, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data ('yes') or not ('no').

        --boldname (str, default 'bold'):
            The default name of the bold files in the images folder.

        --image_target (str, default 'nifti'):
            The target format to work with, one of '4dfp', 'nifti', 'dtseries'
            or 'ptseries'.

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

        --log (str, default 'study'):
            Whether to keep ('keep') or remove ('remove') the temporary logs
            once jobs are completed. When a comma or pipe ('|') separated list
            is given, the log will be created at the first provided location
            and then linked or copied to other locations. The valid locations
            are:

            - 'study'   (for the default:
              ``<study>/processing/logs/comlogs`` location)
            - 'session' (for ``<sessionid>/logs/comlogs``)
            - 'hcp'     (for ``<hcp_folder>/logs/comlogs``)
            - <path>  (for an arbitrary directory).

        --bolds (str, default 'all'):
            A pipe ('|') separated list of conc names to process.

        --event_file (str, default ''):
            A pipe ('|') separated list of fidl names to use, that
            matches the conc list.

        --bold_actions (str, default 's,h,r,c,l'):
            A string specifying which actions, and in what sequence
            to perform.

        --nifti_tail (str, default ''):
            The tail of NIfTI volume images to use.

        --cifti_tail (str, default ''):
            The tail of CIFTI images to use.

        --bold_prefix (str, default ''):
            An optional prefix to place in front of processing name extensions
            in the resulting files, e.g. bold3<bold_prefix>_s_hpss.nii.gz.

        --bold_variant (str, default detailed below):
            Optional variant of HCP BOLD preprocessing. If specified, the BOLD
            images in `images/functional<bold_variant>` will be processed.

        --img_suffix (str, default ''):
            Specifies a suffix for 'images' folder to enable support for
            multiple parallel workflows. Empty if not used.

    Output files:
        This step results in the following files (if requested):

        - residual image::

            <root>_res-<regressors><glm name>.<ext>

        - GLM image::

            <bold name><bold tail>_conc_<event root>_res-<regressors><glm name>_Bcoeff.<ext>

        - text GLM regressor matrix::

            glm/<bold name><bold tail>_GLM-X_<event root>_res-<regressors><glm name>.txt

        - image of a regressor matrix::

            ``glm/<bold name><bold tail>_GLM-X_<event root>_res-<regressors><glm name>.png``

    Notes:
        The --bolds and --event_file parameters provide names based on which the
        the appropriate .conc and .fidl files are searched for. Both are first
        searched for in `images<img_suffix>/functional<bold_variant>/concs` and
        images<img_suffix>/functional<bold_variant>/events folders
        respectively. There they would be named as `[<session
        id>_]<boldname>_<image_target>_<conc name>.conc` and `[<session
        id>_]<boldname>_<image_target>_<fidl name>.fidl`. If the files are not
        present in the relevant individual session's folders, they are searched
        for in the `<sessionsfolder>/inbox/events` and
        `<sessionsfolder>/inbox/concs` folder. In that case the "<session id>_"
        in the \*.fidl and \*.conc file name is not optional but required.

        The --bold_actions parameter specifies the actions, denoted by a single 
        letter, that will be executed in the sequence listed:

        --m     Motion scrubbing.
        --s     Spatial smoothing.
        --h     High-pass filtering.
        --r     Regression (nuisance and/or task) with an optional number 0, 1,
                or 2 specifying the type of regression to use (see REGRESSION
                below).
        --l     Low-pass filtering.

        So the default 's,h,r,c,l' --bold_actions parameter would lead to the
        files first being smoothed, then high-pass filtered. Next a regression
        step would follow in which nuisance signal and/or task related signal
        would be estimated and regressed out, then the related beta estimates
        would be saved. Lastly the BOLDs would be also low-pass filtered.

        Relative vs. absolute use of conc files:
            If `conc_use` is set to relative (the default), then the only
            information taken from the conc files will be the bold numbers. The
            actual location of the bold files will be constructed from the
            information on the location of the session's sesion folder present
            in the batch file, and the `bold_variant` setting, whereas the
            specific bold file name and file format (e.g. .nii.gz vs.
            .dtseries.nii) to use will depend on `boldname`, `image_target`,
            `nifti_tail` and `cifti_tail` settings. This allows for flexible
            use of conc files. That is, the same conc files can be used for
            NIfTI and CIFTI versions of bold files, across bold variants, and
            even when the actual study location changes, e.g. when moving the
            study from one server, volume or folder to another. In most cases
            this use will be prefered.

            If the information in the conc file is to be used literally, e.g. in
            cases when you want to work with a specific preprocessed version of
            the BOLD files, then `conc_use` should be set to `absolute`. In
            this case both the specific location as well as the specific
            filename specified in the conc file will be used exactly as
            specified. In this case, do check and make sure that the
            information in the conc file is valid and it matches with
            `boldname` and `image_target` parameters, and that the `nifti_tail`
            is specified correctly, as it will be used to obtain bold
            statistics and nuisance information!

        Scrubbing:
            The command either makes use of scrubbing information or performs
            scrubbing comuputation on its own (when 'm' is part of the
            command). In the latter case, all the scrubbing parameters need to
            be specified:

            --mov_radius (int, default 50):
                Estimated head radius (in mm) for computing frame displacement
                statistics.
            --mov_fd (float, default 0.5):
                Frame displacement threshold (in mm) to use for identifying bad
                frames.
            --mov_dvars (float, default 3.0):
                The (mean normalized) dvars threshold to use for identifying bad
                frames.
            --mov_dvarsme (float, default 1.5):
                The (median normalized) dvarsm threshold to use for identifying
                bad frames.
            --mov_after (int, default 0):
                How many frames after each frame identified as bad to also
                exclude from further processing and analysis.
            --mov_before (int, default 0):
                How many frames before each frame identified as bad to also
                exclude from further processing and analysis.
            --mov_bad (str, default 'udvarsme'):
                Which criteria to use for identification of bad frames.

            Criteria for identification of bad frames can be one out of:

            --mov
                Frame displacement threshold (fdt) is exceeded.
            --dvars
                Image intensity normalized root mean squared error (RMSE)
                threshold (dvarsmt) is exceeded.
            --dvarsme
                Median normalised RMSE (dvarsmet) threshold is exceeded.
            --idvars
                Both fdt and dvarsmt are exceeded (i for intersection).
            --uvars
                Either fdt or dvarsmt are exceeded (u for union).
            --idvarsme
                Both fdt and dvarsmet are exceeded.
            --udvarsme
                Either fdt or udvarsmet are exceeded.

            For more detailed description please see wiki entry on Movement
            scrubbing.

            In any case, if scrubbing was done beforehand or as a part of this
            command, one has to specify, how the scrubbing information is used:

            --pignore
                String describing how to deal with bad frames.

            The string has the following format::

                'hipass:<filtering opt.>|regress:<regression opt.>|lopass:<filtering opt.>'

            Filtering options are:

            --keep
                Keep all the bad frames unchanged.
            --linear
                Replace bad frames with linear interpolated values based on
                neighboring good frames.
            --spline
                Replace bad frames with spline interpolated values based on
                neighboring good frames.

            To prevent artifacts present in bad frames to be temporarily spread,
            use either 'linear' or 'spline' options.

            Regression options are:

            --keep
                Keep the bad frames and use them in the regression.
            --ignore
                Exclude bad frames from regression.
            --mark
                Exclude bad frames from regression and mark the bad frames as
                NaN.
            --linear
                Replace bad frames with linear interpolated values based on
                neighboring good frames.
            --spline
                Replace bad frames with spline interpolated values based on
                neighboring good frames.

            Please note that when the bad frames are not kept, the original
            values will be retained in the residual signal. In this case they
            have to be excluded or ignored also in all following analyses,
            otherwise they can be a significant source of artifacts.

        Spatial smoothing:
            Volume smoothing:
                For volume formats the images will be smoothed using the
                img_smooth_3d nimage method. For cifti format the smooting will
                be done by calling the relevant wb_command command. The
                smoothing parameters are:

                --voxel_smooth (int, default 1):
                    Gaussian smoothing FWHM in voxels.
                --smooth_mask (str, default false):
                    Whether to smooth only within a mask, and what mask to use
                    (nonzero|brainsignal|brainmask|<filename>|false).
                --dilate_mask (str, default false):
                    Whether to dilate the image after masked smoothing and what
                    mask to use
                    (nonzero|brainsignal|brainmask|same|<filename>|false).

                If a smoothing mask is set, only the signal within the specified
                mask will be used in the smoothing. If a dilation mask is set,
                after smoothing within a mask, the resulting signal will be
                constrained / dilated to the specified dilation mask.

                For both parameters the possible options are:

                --nonzero
                    Mask will consist of all the nonzero voxels of the first
                    BOLD frame.
                --brainsignal
                    Mask will consist of all the voxels that are of value 300 or
                    higher in the first BOLD frame (this gave a good coarse
                    brain mask for images intensity normalized to mode 1000 in
                    the NIL preprocessing stream).
                --brainmask
                    Mask will be the actual bet extracted brain mask based on
                    the first BOLD frame (generated using in the
                    creatBOLDBrainMasks command).
                --filename
                    All the non-zero voxels in a specified volume file will be
                    used as a mask.
                --false
                    No mask will be used.
                --same
                    Only for dilate_mask, the mask used will be the same as
                    smoothing mask.

            Cifti smoothing:
                For cifti format images, smoothing will be run using wb_command.
                The following parameters can be set:

                --surface_smooth (float, default 2.0):
                    FWHM for Gaussian surface smoothing in mm.
                --volume_smooth (float, default 2.0):
                    FWHM for Gaussian volume smoothing in mm.
                --framework_path (str, default ''):
                    The path to framework libraries on the Mac system. No need
                    to use it currently if installed correctly.
                --wb_command_path (str, default ''):
                    The path to the wb_command executive. No need to use it
                    currently if installed correctly.

                Results:
                    The resulting smoothed files are saved with '_s' added to
                    the BOLD root filename.


        Temporal filtering:
            Temporal filtering is accomplished using img_filter nimage method.
            The code is adopted from the FSL C++ code enabling appropriate
            handling of bad frames (as described above - see SCRUBBING). The
            parameters are:

            --hipass_filter (float, default 0.008):
                The frequency for high-pass filtering in Hz.
            --lopass_filter (float, default 0.09):
                The frequency for low-pass filtering in Hz.

            Please note that the values finally passed to img_filter method are
            the respective sigma values computed from the specified frequencies
            and TR.

            Filtering of nuisance signal, movement, task, and events
            Besides data, nuisance signal, motion parameters, and event 
            regressors can be filtered as well. What to filter beside data can
            be specified by a comma separated list using the following 
            parameters:
            
            --hipass_do (str, default 'nuisance')
                What to high-pass filter besides data – options are: nuisance, 
                movement, events, task. Default is 'nuisance'.
 
            --lopass_do (str, default 'nuisance,movement,task,events')
                What to lo-pass filter besides data – options are: nuisance, 
                movement, events, task. Default is 'nuisance, movement, task, 
                events'.
            
            Note that 'events' refers to regressors created based on events 
            as specified in the fidl file, whereas 'task' refers to a task
            matrix that is passed directy in the matlab function call.

            Results:
                The resulting filtered files are saved with '_hpss' or '_bpss'
                added to the BOLD root filename for high-pass and low-pass
                filtering, respectively.

        Regression:
            Regression is a complex step in which GLM is used to estimate the
            beta weights for the specified nuisance regressors and events. The
            resulting beta weights are then stored in a GLM file (a regular
            file with additional information on the design used) and residuals
            are stored in a separate file. This step can therefore be used for
            two purposes: (1) to remove nuisance signal and event structure
            from BOLD files, removing unwanted potential sources of correlation
            for further functional connectivity analyses, and (2) to get task
            beta estimates for further activation analyses. The following
            parameters are used in this step:

            --bold_nuisance (str, default 'm,m1d,mSq,m1dSq,V,WM,WB,1d'):
                A comma separated list of regressors to include in GLM.
                Possible values are:

                - 'm'     ... motion parameters
                - 'm1d'   ... first derivative of motion parameters
                - 'mSq'   ... squared motion parameters
                - 'm1dSq' ... squared first derivative of motion parameters
                - 'V'     ... ventricles signal
                - 'WM'    ... white matter signal
                - 'WB'    ... whole brain signal
                - '1d'    ... first derivative of above nuisance signals
                - 'e'     ... events listed in the provided fidl files.

            --event_string (str, default ''):
                A string describing, how to model the events listed in the
                provided fidl files.
            --glm_matrix (str, default 'none'):
                Whether to save the GLM matrix as a text file ('text'), a png
                image file ('image'), both ('both') or not ('none').
            --glm_results (str, default 'c,r')
                A string  which of the GLM analysis results are saved.
                Possible values are:

                - 'c'   ... Saving of resulting beta coefficients.
                - 'z'   ... Saving of resulting z-scores of beta coefficients.
                - 'p'   ... Saving of session-level coefficient p-values.
                - 'se'  ... Saving of standard errors of beta coefficients.
                - 'r'   ... Saving of resulting residuals of the GLM.
                - 'all' ... Saving all of the results above.

            --glm_name (str, default ''):
                An additional name to add to the residuals and GLM files to
                distinguish between different possible models used.

            GLM modeling:
                There are two important variables that affect the exact GLM
                model used to estimate nuisance and task beta coefficients and
                regress them from the signal. The first is the optional number
                following the 'r' command in the --bold_actions parameter.
                There are three options:

                - '0' ... Estimate nuisance regressors for each bold file
                  separately, however, model events across all bold files (the
                  default if no number is) specified.
                - '1' ... Estimate both nuisance regressors and task regressors
                  for each bold run separately.
                - '2' ... Estimate both nuisance regressors as well as task
                  regressors across all bold runs.

                The second key variable is the event string provided by the
                --event_string parameter. The event string is a pipe ('|')
                separated list of regressor specifications. The possibilities
                are discussed below:

                Unassumed Modeling:
                    ::

                        <fidl code>:<length in frames>

                    Where <fidl code> is the code for the event used in the fidl
                    file, and <length in frames> specifies, for how many frames
                    of the bold run (since the onset of the event) the event
                    should be modeled.

                Assumed Modeling:
                    ::

                        <fidl code>:<hrf>[-run|-uni][:<length>]

                    Where <fidl code> is the same as above, <hrf> is the type of
                    the hemodynamic response function to use, '-run' and '-uni'
                    specify how the regressor should be normalized, and
                    <length> is an optional parameter, with its value dependent
                    on the model used. The allowed <hrf> are:

                    - 'boynton' ... uses the Boynton HRF
                    - 'SPM'     ... uses the SPM double gaussian HRF
                    - 'u'       ... unassumed (see above)
                    - 'block'   ... block response.

                    For the first two, the <length> parameter is optional and
                    would override the event duration information provided in
                    the fidl file. For 'u' the length is the same as in
                    previous section: the number of frames to model. For
                    'block' length should be two numbers separated by a colon
                    (e.g. 2:9) that specify the start and end offset (from the
                    event onset) to model as a block.

                    Assumed HRF regressors normalization:
                        hrf_types `boynton` and `SPM` can be marked with an
                        additional flag denoting how to normalize the
                        regressor.

                        In case of `<hrf function>-uni`, e.g. 'boynton-uni' or
                        'SPM-uni', the HRF function will be normalized to have
                        the area under the curve equal to 1. This ensures
                        uniform and universal, scaling of the resulting
                        regressor across all event lengths. In addition, the
                        scaling is not impacted by weights (e.g. behavioral
                        coregressors), which in turn ensures that the weights
                        are not scaled.

                        In case of `<hrf function>-run`, e.g. `boynton-run` or
                        `SPM-run`, the resulting regressor is normalized to
                        amplitude of 1 within each bold run separately. This
                        can result in different scaling of regressors with
                        different durations, and of the same regressor across
                        different runs. Scaling in this case is performed after
                        the signal is weighted, so in effect the scaling of
                        weights (e.g. behavioral regressors), can differ across
                        bold runs.

                        The flag can be abbreviated to '-r' and '-u'. If not
                        specified, '-run' will be assumed (the default might
                        change).

                Naming And Behavioral Regressors:
                    Each of the above (unassumed and assumed modeling
                    specification) can be followed by a ">" (greater-than
                    character), which signifies additional information in the
                    form::

                        <name>[:<column>[:<normalization_span>[:<normalization_method>]]]

                    --name
                        The name of the resulting regressor.
                    --column
                        The number of the additional behavioral regressors
                        column in the fidl file (1-based) to use as a weight
                        for the regressors.
                    --normalization_span
                        Whether to normalize the behavioral weight within a
                        specific event type ('within') or across all events
                        ('across'). [within]
                    --normalization_method
                        The method to use for normalization. Options are:

                        - 'z'    (compute Z-score)
                        - '01'   (normalize to fixed range 0 to 1)
                        - '-11'  (normalize to fixed range -1 to 1)
                        - 'none' (use weights as provided in fidl file)

                    Example string::

                        'block:boynton|target:9|target:9>target_rt:1:within:z'

                    This would result in three sets of task regressors: one
                    assumed task regressor for the sustained activity across
                    the block, one unassumed task regressor set spanning 9
                    frames that would model the presentation of the target, and
                    one behaviorally weighted unassumed regressor that would
                    for each frame estimate the variability in response as
                    explained by the reaction time to the target.

    Examples:
        Activation analysis::

            qunex preprocess_conc \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --bolds=SRT \\
                --event_file=SRT \\
                --glm_name=-M1 \\
                --bold_actions="s,r,c" \\
                --bold_nuisance=e \\
                --mov_bad=none \\
                --event_string="block:boynton|target:9|target:9>target_rt:1:within:z" \\
                --glm_matrix=both \\
                --glm_residuals=none \\
                --pignore="hipass=keep|regress=keep|lopass=keep"

        Functional connectivity preprocessing::

            qunex preprocess_conc \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --bolds=SRT \\
                --event_file=SRT \\
                --glm_name=-FC \\
                --bold_actions="s,h,r,c,l" \\
                --bold_nuisance="m,V,WM,WB,1d,e" \\
                --mov_bad=udvarsme \\
                --event_string="block:boynton|target:9" \\
                --glm_matrix=none \\
                --glm_residuals=save \\
                --pignore="hipass=linear|regress=ignore|lopass=linear"
    """

    pc.doOptionsCheck(options, sinfo, "preprocess_conc")

    r = "\n---------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s Preprocessing conc bundles ..." % (pc.action("Running", options["run"]))
    r += "\nFiles in 'images%s/functional%s will be processed." % (
        options["img_suffix"],
        options["bold_variant"],
    )

    # --- extract conc and fidl names
    concs = [e.strip().replace(".conc", "") for e in options["bolds"].split("|")]
    fidls = [e.strip().replace(".fidl", "") for e in options["event_file"].split("|")]

    # --- define the tail
    options["bold_tail"] = options["nifti_tail"]
    if options["image_target"] in ["cifti", "dtseries", "ptseries"]:
        options["bold_tail"] = options["cifti_tail"]

    concroot = "_".join(
        e
        for e in [
            options["boldname"] + options["bold_tail"],
            options["image_target"].replace("cifti", "dtseries"),
        ]
        if e
    )
    report = ""

    failed = 0
    if len(concs) != len(fidls):
        r += (
            "\nERROR: Number of conc files (%d) does not match number of event files (%d), processing aborted!"
            % (len(concs), len(fidls))
        )

    else:
        for nb in range(0, len(concs)):
            tconc = concs[nb]
            tfidl = fidls[nb]
            options["concname"] = tconc
            if tfidl:
                options["fidlname"] = tfidl
            else:
                options["fidlname"] = ""

            try:
                r += "\n\nConc bundle: %s" % (tconc)

                d = pc.getSessionFolders(sinfo, options)
                f = {}
                f_conc = os.path.join(
                    d["s_bold_concs"], concroot + "_" + tconc + ".conc"
                )
                f_fidl = os.path.join(d["s_bold_events"], tfidl + ".fidl")

                # --- find conc data

                if overwrite or not os.path.exists(f_conc):
                    tf = pc.findFile(sinfo, options, tconc + ".conc")
                    if tf:
                        r += "\n... getting conc data from %s" % (tf)
                        if os.path.exists(f_conc):
                            os.remove(f_conc)
                        shutil.copy2(tf, f_conc)

                    else:
                        r += (
                            "\n... ERROR: Conc data file (%s) does not exist in the expected locations! Skipping this conc bundle."
                            % (tconc)
                        )
                        failed += 1
                        continue
                else:
                    r += "\n... conc data present"

                # --- find fidl data

                if "e" in [e.strip() for e in options["bold_nuisance"].split(",")]:
                    if overwrite or not os.path.exists(f_fidl):
                        tf = pc.findFile(sinfo, options, tfidl + ".fidl")
                        if tf:
                            r += "\n... getting event data from %s" % (tf)
                            if os.path.exists(f_fidl):
                                os.remove(f_fidl)
                            shutil.copy2(tf, f_fidl)
                        else:
                            r += (
                                "\n... ERROR: Event data file (%s) does not exist in the expected locations! Skipping this conc bundle."
                                % (tfidl)
                            )
                            failed += 1
                            continue
                    else:
                        r += "\n... event data present"
                else:
                    r += (
                        "\n... event data not needed (e not specified in --bold_nuisance) %s"
                        % (options["bold_nuisance"])
                    )

                # --- loop through bold files

                conc = gi.readConc(f_conc, boldname=options["boldname"])
                nconc = []
                bolds = []
                rstatus = True
                check = {"ok": [], "bad": []}

                if len(conc) == 0:
                    r += (
                        "\n... ERROR: No valid image files in conc file (%s)! Skipping this conc bundle."
                        % (f_conc)
                    )
                    failed += 1
                    continue

                for c in conc:
                    # print("c from conc:", c)
                    boldnum = c[1]
                    boldname = options["boldname"] + boldnum
                    bolds.append(boldnum)

                    # if absolute path flag use session folder from conc file
                    if options["conc_use"] == "absolute":
                        # extract session folder from conc file
                        options["sessionsfolder"] = (c[0].split(sinfo["id"]))[0]
                        d["s_base"] = options["sessionsfolder"] + sinfo["id"]
                        options["bold_tail"] = (c[0].split(boldname))[1].replace(
                            pc.getExtension(options["image_target"]), ""
                        )

                    r += "\n\nLooking up: " + boldname + " ..."

                    # --- filenames
                    f = pc.getFileNames(sinfo, options)
                    f.update(pc.getBOLDFileNames(sinfo, boldname, options))

                    # if absolute path flag use also exact filename (extension)
                    if options["conc_use"] == "absolute":
                        f["bold"] = c[0]

                    # --- check for data availability

                    # r += '\n    ... checking for data'
                    status = True

                    # --- bold
                    r, status = pc.checkForFile2(
                        r,
                        f["bold"],
                        "\n    ... bold data present",
                        "\n    ... bold data missing [%s]" % (f["bold"]),
                        status=status,
                    )
                    nconc.append((f["bold"], boldnum))

                    # --- movement
                    if "r" in options["bold_actions"] and (
                        "m" in options["bold_nuisance"]
                        or "m" in options["bold_actions"]
                    ):
                        r, status = pc.checkForFile2(
                            r,
                            f["bold_mov"],
                            "\n    ... movement data present",
                            "\n    ... movement data missing [%s]" % (f["bold_mov"]),
                            status=status,
                        )

                    # --- bold stats
                    if "m" in options["bold_actions"]:
                        r, status = pc.checkForFile2(
                            r,
                            f["bold_stats"],
                            "\n    ... bold statistics data present",
                            "\n    ... bold statistics data missing [%s]"
                            % (f["bold_stats"]),
                            status=status,
                        )

                    # --- bold scrub
                    if any(
                        [
                            e in options["pignore"]
                            for e in ["linear", "spline", "ignore"]
                        ]
                    ):
                        r, status = pc.checkForFile2(
                            r,
                            f["bold_scrub"],
                            "\n    ... bold scrubbing data present",
                            "\n    ... bold scrubbing data missing [%s]"
                            % (f["bold_scrub"]),
                            status=status,
                        )

                    # --- check for nuisance data files if doing regression

                    if "r" in options["bold_actions"] and any(
                        [e in options["bold_nuisance"] for e in ["V", "WM", "WB"]]
                    ):
                        r, status = pc.checkForFile2(
                            r,
                            f["bold_nuisance"],
                            "\n    ... bold nuisance signal data present",
                            "\n    ... bold nuisance signal data missing [%s]"
                            % (f["bold_nuisance"]),
                            status=status,
                        )

                    # --- check
                    if not status:
                        r += "\n---> ERROR: Files missing!"
                        rstatus = False
                        check["bad"].append(boldnum)
                    else:
                        check["ok"].append(boldnum)

                # --- all files reviewed continuing conc processing

                report = ""
                if len(check["ok"]) > 0:
                    report += "%d bolds ok [%s], " % (
                        len(check["ok"]),
                        " ".join(check["ok"]),
                    )
                else:
                    report += "0 bolds ok, "

                if len(check["bad"]) > 0:
                    report += "%d bold not ok [%s], " % (
                        len(check["bad"]),
                        " ".join(check["bad"]),
                    )
                else:
                    report += "0 bolds not ok"

                if not rstatus:
                    r += (
                        "\nERROR: Due to missing data we are skipping this conc bundle!"
                    )
                    report += " => missing data"
                    failed += 1
                    continue

                gi.writeConc(f_conc, nconc)

                # --- run matlab preprocessing script

                if overwrite:
                    boldow = "true"
                else:
                    boldow = "false"

                done = f["conc_final"] + ".ok"

                scrub = (
                    "radius:%(mov_radius)d|fdt:%(mov_fd).2f|dvarsmt:%(mov_dvars).2f|dvarsmet:%(mov_dvarsme).2f|after:%(mov_after)d|before:%(mov_before)d|reject:%(mov_bad)s"
                    % (options)
                )
                opts = (
                    "boldname=%(boldname)s|fidlname=%(fidlname)s|concname=%(concname)s|surface_smooth=%(surface_smooth)f|volume_smooth=%(volume_smooth)f|voxel_smooth=%(voxel_smooth)f|hipass_filter=%(hipass_filter)f|lopass_filter=%(lopass_filter)f|framework_path=%(framework_path)s|wb_command_path=%(wb_command_path)s|smooth_mask=%(smooth_mask)s|dilate_mask=%(dilate_mask)s|glm_matrix=%(glm_matrix)s|glm_residuals=%(glm_residuals)s|glm_results=%(glm_results)s|glm_name=%(glm_name)s|bold_tail=%(bold_tail)s|ref_bold_tail=%(nifti_tail)s|bold_variant=%(bold_variant)s|img_suffix=%(img_suffix)s"
                    % (options)
                )

                mcomm = (
                    "fc_preprocess_conc('%s', [%s], '%s', %.3f,  %d, '%s', [], '%s.fidl', '%s', '%s', %s, '%s', '%s', '%s', '%s', '%s')"
                    % (
                        d["s_base"],  # --- session folder
                        " ".join(
                            bolds
                        ),  # --- vector of bold runs in the order of the conc file
                        options[
                            "bold_actions"
                        ],  # --- which steps to perform in what order (s, h, r0/r1/r2, c, p, l)
                        options["tr"],  # --- TR
                        options[
                            "omit"
                        ],  # --- the number of frames to omit at the start of each run
                        options[
                            "bold_nuisance"
                        ],  # --- nuisance regressors (m, v, wm, wb, d, t, e)
                        tfidl,  # --- event file to be used for task regression (w/o .fidl)
                        options[
                            "event_string"
                        ],  # --- event string specifying what and how of task to regress
                        options[
                            "bold_prefix"
                        ],  # --- optional prefix to the resulting bolds
                        boldow,  # --- whether to overwrite existing files
                        gi.getImgFormat(
                            f["bold_final"]
                        ),  # --- the format of the images (.nii vs. .4dfp.img)
                        scrub,  # --- scrub parameters string
                        options[
                            "pignore"
                        ],  # --- how to deal with bad frames ('hipass:keep/linear/spline|regress:keep/ignore|lopass:keep/linear/spline')
                        opts,  # --- additional options
                        done,
                    )
                )  # --- file to save when done

                comm = (
                    '%s "try %s; catch ME, general_report_crash(ME); exit(1), end; exit;"'
                    % (mcommand, mcomm)
                )

                r += "\n\n%s nuisance and task removal" % (
                    pc.action("Running", options["run"])
                )
                if options["print_command"] == "yes":
                    r += "\n" + comm + "\n"
                if options["run"] == "run":
                    r, endlog, status, failed = pc.runExternalForFile(
                        done,
                        comm,
                        "running matlab/octave fc_preprocess_conc on bolds [%s]"
                        % (" ".join(bolds)),
                        overwrite=overwrite,
                        thread=sinfo["id"],
                        remove=options["log"] == "remove",
                        task=options["command_ran"],
                        logfolder=options["comlogs"],
                        logtags=[
                            options["bold_variant"],
                            options["bolds"],
                            options["glm_name"],
                            options["logtag"],
                        ],
                        r=r,
                        shell=True,
                    )
                    r, status = pc.checkForFile(
                        r,
                        done,
                        "ERROR: Matlab/Octave has failed preprocessing BOLD using command: \n---> %s\n"
                        % (mcomm),
                    )
                    if os.path.exists(done):
                        os.remove(done)
                    if status:
                        report += " => processed ok"
                    else:
                        report += " => processing failed"
                        failed += 1
                else:
                    if os.path.exists(done):
                        report += " => already done"
                    else:
                        report += " => ready"
                        failed += 1

            except ge.CommandFailed as e:
                r += "\n" + ge.reportCommandFailed("preprocess_conc", e)
                report += " => processing failed"
                failed += 1
            except ge.CommandError as e:
                r += "\n" + ge.reportCommandError("preprocess_conc", e)
                report += " => processing failed"
                failed += 1
            except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
                r += str(errormessage)
                report += " => processing failed"
                failed += 1
            except:
                report += " => processing failed"
                r += (
                    "\nERROR: Unknown error occured: \n...................................\n%s...................................\n"
                    % (traceback.format_exc())
                )
                time.sleep(5)
                failed += 1

    r += (
        "\n\nConc preprocessing (v2) completed on %s\n---------------------------------------------------------"
        % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    )

    # print r
    return (r, (sinfo["id"], report, failed))
