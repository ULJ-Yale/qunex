#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``workflow/create_bold_brain_masks.py``

Extracts the first frame of each BOLD file and generates its brain mask.
"""

# Created by Grega Repovs on 2016-12-17.
# Code split from dofcMRIp_core gCodeP/preprocess codebase.
# Copyright (c) Grega Repovs. All rights reserved.

import os
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from functools import partial

import qx_utilities.processing.core as pc
import qx_utilities.general.filelock as fl
import qx_utilities.general.img as gi
import qx_utilities.general.core as gc
from qx_utilities.general.log import ReportLog
from qx_utilities.processing.workflow import dryrun


# --------------------------------------------------------- the command preamble
#
# What the command does, shown once at the head of every session report, and
# the parameters it quotes back. A dedented block rather than lines carrying
# their own `\n    `: this is prose, it is read as prose, and it should be
# reviewable as prose. The parameter list is a list rather than a format string
# with one interpolation each, so it cannot drift from `options`.
BRAIN_MASKS_PURPOSE = """\
A mask identifying the actual coverage of the brain is created for each of the
specified BOLD files, from its first frame. Only the images named by --bolds
are processed; the default is all of them."""


def create_bold_brain_masks(sinfo, options, overwrite=False, thread=0):
    """
    ``create_bold_brain_masks [... processing options]``

    Extract the brain and create a brain mask for each BOLD image.

    ..  qx_command:
        type: processing.session

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

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

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
            The path to the folder where logs are to be stored,
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
    log = ReportLog()

    report = {
        "bolddone": 0,
        "boldok": 0,
        "boldfail": 0,
        "boldmissing": 0,
        "boldskipped": 0,
    }

    log.rule()
    log.info(f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]")
    log.action("Creating", "masks for bold runs ...", options["run"], level="info")
    log.blank()
    log.info(BRAIN_MASKS_PURPOSE)

    pc.do_options_check(options, sinfo, "create_bold_brain_masks")
    d = pc.get_session_folders(sinfo, options)

    if overwrite:
        ostatus = "will"
    else:
        ostatus = "will not"

    log.step(f"Working on BOLD images in {d['s_images']}")
    log.detail(f"images{options['img_suffix']}/functional{options['bold_variant']} will be processed")
    log.detail(f"the resulting masks will be in {d['s_boldmasks']}")
    log.detail(f"{', '.join(options['bolds'].split('|'))} BOLD files will be processed (see --bolds)")
    log.detail(f"existing masks {ostatus} be overwritten (see --overwrite)")

    bolds, bskip, report["boldskipped"] = pc.use_or_skip_bold(sinfo, options, _log=log)

    parelements = options["parelements"]
    log.info(f"Processing {parelements} BOLDs in parallel")

    if parelements == 1:  # serial execution
        for b in bolds:
            # process
            result = execute_create_bold_brain_masks(sinfo, options, overwrite, b)

            # merge r
            log.raw(result["r"])

            # merge report
            temp_report = result["report"]
            report["bolddone"] += temp_report["bolddone"]
            report["boldok"] += temp_report["boldok"]
            report["boldfail"] += temp_report["boldfail"]
            report["boldmissing"] += temp_report["boldmissing"]
    else:  # parallel execution
        # create a multiprocessing Pool
        process_pool_executor = ProcessPoolExecutor(parelements)
        # process
        f = partial(execute_create_bold_brain_masks, sinfo, options, overwrite)
        results = process_pool_executor.map(f, bolds)

        # merge r and report
        for result in results:
            log.raw(result["r"])
            temp_report = result["report"]
            report["bolddone"] += temp_report["bolddone"]
            report["boldok"] += temp_report["boldok"]
            report["boldfail"] += temp_report["boldfail"]
            report["boldmissing"] += temp_report["boldmissing"]

    log.blank()
    log.info(f"Bold mask creation completed on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}")
    log.rule()
    rstatus = (
        "BOLDS done: %(bolddone)2d, missing data: %(boldmissing)2d, failed: %(boldfail)2d, processed: %(boldok)2d, skipped: %(boldskipped)2d"
        % (report)
    )

    return log.result(rstatus, report["boldmissing"] + report["boldfail"], sinfo["id"])


def execute_create_bold_brain_masks(sinfo, options, overwrite, boldinfo):

    # prepare return variables
    log = ReportLog()
    report = {"bolddone": 0, "boldok": 0, "boldfail": 0, "boldmissing": 0}

    log.step("Working on " + boldinfo["name"])

    try:
        # --- filenames
        f = pc.get_file_names(sinfo, options)
        f.update(pc.get_bold_file_names(sinfo, boldinfo["name"], options))

        # template file
        templatefile = f["bold_template"]

        # --- copy over bold data
        # --- bold
        status = pc.check_for_file(f["bold_vol"],
            "bold data present",
            "bold data missing, skipping bold",
            status=True,
            _log=log,
        )
        if not status:
            log.info("Looked for:" + f["bold_vol"])
            report["boldmissing"] += 1
            return {"r": log.text, "report": report}

        # --- extract first bold frame
        if not os.path.exists(f["bold1"]) or overwrite:
            if options["run"] != "run":
                # the check below reads the file the slice would have written,
                # so a dry run has to skip it rather than report a failure and
                # return before naming the tools it would have run
                log.detail(f"test, not sliced: first frame of {os.path.basename(f['bold_vol'])}")
            else:
                gi.slice_image(f["bold_vol"], f["bold1"], 1)
                if os.path.exists(f["bold1"]):
                    log.detail(f"sliced first frame from {os.path.basename(f['bold_vol'])}")
                else:
                    log.warning(f"failed slicing first frame from {os.path.basename(f['bold_vol'])}", depth=1)
                    report["boldfail"] += 1
                    return {"r": log.text, "report": report}
        else:
            log.detail(f"first {os.path.basename(f['bold_vol'])} frame already present")

        # --- logs storage
        endlogs = []

        # --- convert to NIfTI
        bsource = f["bold1"]
        bbtarget = f["bold1_brain"].replace(
            gi.get_img_format(f["bold1_brain"]), ".nii.gz"
        )
        bmtarget = f["bold1_brain_mask"].replace(
            gi.get_img_format(f["bold1_brain_mask"]), ".nii.gz"
        )
        if gi.get_img_format(f["bold1"]) == ".4dfp.img":
            bsource = f["bold1"].replace(".4dfp.img", ".nii.gz")

            # run g_FlipFormat
            endlog, status, failed = dryrun.run_external(
                log,
                options,
                bsource,
                "g_FlipFormat %s %s" % (f["bold1"], bsource),
                "    ... converting %s to nifti" % (f["bold1"]),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                task="FlipFormat",
                logfolder=options["comlogs"],
                logtags=[
                    options["bold_variant"],
                    options["logtag"],
                    "B%d" % boldinfo["bold_number"],
                ],
                verbose=False,
            )

            # append to endlogs
            endlogs.append(endlog)

            # run caret_command
            endlog, status, failed = dryrun.run_external(
                log,
                options,
                bsource,
                "caret_command -file-convert -vc %s %s"
                % (f["bold1"].replace("img", "ifh"), bsource),
                "converting %s to nifti" % (f["bold1"]),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                logfolder=options["comlogs"],
                logtags=[
                    options["bold_variant"],
                    options["logtag"],
                    "B%d" % boldinfo["bold_number"],
                ],
                verbose=False,
            )

            # append to endlogs
            endlogs.append(endlog)

        # --- run BET
        if os.path.exists(bbtarget) and not overwrite:
            log.detail(f"bet on {os.path.basename(bsource)} already run")
            report["bolddone"] += 1
        else:
            # run BET
            endlog, status, failed = dryrun.run_external(
                log,
                options,
                bbtarget,
                "bet %s %s %s" % (bsource, bbtarget, options["betboldmask"]),
                "    ... running BET on %s with options %s"
                % (os.path.basename(bsource), options["betboldmask"]),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                task="bet",
                logfolder=options["comlogs"],
                logtags=[
                    options["bold_variant"],
                    options["logtag"],
                    "B%d" % boldinfo["bold_number"],
                ],
                verbose=False,
            )
            report["boldok"] += 1

            # append to endlogs
            endlogs.append(endlog)

        if options["image_target"] == "4dfp":
            # --- convert nifti to 4dfp
            # run gunzip
            endlog, status, failed = dryrun.run_external(
                log,
                options,
                bbtarget,
                "gunzip -f %s.gz" % (bbtarget),
                "    ... gunzipping %s.gz" % (os.path.basename(bbtarget)),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                task="gunzip",
                logfolder=options["comlogs"],
                logtags=[
                    options["bold_variant"],
                    options["logtag"],
                    "B%d" % boldinfo["bold_number"],
                ],
                verbose=False,
            )

            # append to endlogs
            endlogs.append(endlog)

            # run gunzip
            endlog, status, failed = dryrun.run_external(
                log,
                options,
                bmtarget,
                "gunzip -f %s.gz" % (bmtarget),
                "    ... gunzipping %s.gz" % (os.path.basename(bmtarget)),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                task="gunzip",
                logfolder=options["comlogs"],
                logtags=[
                    options["bold_variant"],
                    options["logtag"],
                    "B%d" % boldinfo["bold_number"],
                ],
                verbose=False,
            )

            # append to endlogs
            endlogs.append(endlog)

            # run g_FlipFormat
            endlog, status, failed = dryrun.run_external(
                log,
                options,
                f["bold1_brain"],
                "g_FlipFormat %s %s"
                % (bbtarget, f["bold1_brain"].replace(".img", ".ifh")),
                "    ... converting %s to 4dfp" % (f["bold1_brain_nifti"]),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                task="FlipFormat",
                logfolder=options["comlogs"],
                logtags=[
                    options["bold_variant"],
                    options["logtag"],
                    "B%d" % boldinfo["bold_number"],
                ],
                verbose=False,
            )

            # append to endlogs
            endlogs.append(endlog)

            # run g_FlipFormat
            endlog, status, failed = dryrun.run_external(
                log,
                options,
                f["bold1_brain_mask"],
                "g_FlipFormat %s %s"
                % (bmtarget, f["bold1_brain_mask"].replace(".img", ".ifh")),
                "    ... converting %s to 4dfp" % (f["bold1_brain_mask_nifti"]),
                overwrite=overwrite,
                remove=options["log"] == "remove",
                thread=sinfo["id"],
                task="FlipFormat",
                logfolder=options["comlogs"],
                logtags=[
                    options["bold_variant"],
                    options["logtag"],
                    "B%d" % boldinfo["bold_number"],
                ],
                verbose=False,
            )

            # append to endlogs
            endlogs.append(endlog)

        else:
            # --- link a template
            if options["run"] != "run":
                # `fl.lock` writes a .lock file beside the template, so a dry
                # run cannot take the lock, let alone make the link it guards
                log.detail(f"test, not linked: {os.path.basename(f['bold1_brain'])} as the bold template")
            else:
                # lock
                fl.lock(templatefile)

                # create link
                if not os.path.exists(templatefile):
                    # r += '\n ... link %s to %s' % (f['bold1_brain'], f['bold_template'])
                    gc.link_or_copy(f["bold1_brain"], f["bold_template"])

                # unlock
                fl.unlock(templatefile)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))

        # unlock tempalte file if it crashed there
        fl.unlock(templatefile)

        report["boldfail"] += 1
    except Exception as e:
        # unlock template file if it crashed there
        if templatefile is not None and os.path.exists(templatefile):
            fl.unlock(templatefile)

        report["boldfail"] += 1
        log.error(f"Unknown error occured: \n...................................\n{e}\n{traceback.format_exc()}...................................\n")
        time.sleep(1)

    # merge into final comlog
    log_prefix = "done"

    # final_ log storage
    final_log = ""

    # if remove option is set do nothinng
    remove = options["log"] == "remove"
    if not remove and endlogs:
        for el in endlogs:
            # a dry run ran nothing, so every entry is the None `_run_external`
            # returns in place of a comlog path
            if el is not None and os.path.exists(el):
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
                dryrun.remove(log, options, el)

    # fails?
    if report["boldfail"] > 0:
        log_prefix = "error"
    elif not overwrite and final_log == "":
        final_log = "Previous results present, overwrite set to no.\n\n"
        final_log = final_log + f"---> Successful completion of task at {datetime.now()}"

    # a dry run ran nothing, so there is no output to merge and no comlog to
    # leave behind -- the same rule `pc.combined_comlog` follows
    if options["run"] != "run":
        return {"r": log.text, "report": report}

    # print to log file
    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
    logname = "%s_create_bold_brain_masks_B%s_%s_%s.log" % (
        log_prefix,
        boldinfo["bold_number"],
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
        except Exception:
            raise pc.ExternalFailed(
                "\n\nERROR: Could not create folder for logfile [%s]!" % (logfolder)
            )

    # print to file and close
    logfile = os.path.join(logfolder, logname)
    lf = open(logfile, "a")
    lf.write(final_log)
    lf.close()

    return {"r": log.text, "report": report}
