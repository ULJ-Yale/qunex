#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``workflow/compute_bold_stats.py``

Computes per volume image statistics used for scrubbing.
"""

# Created by Grega Repovs on 2016-12-17.
# Code split from dofcMRIp_core gCodeP/preprocess codebase.
# Copyright (c) Grega Repovs. All rights reserved.

import os
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from functools import partial

import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog
from qx_utilities.processing.workflow import dryrun
from qx_utilities.processing.workflow.dryrun import mcommand


# --------------------------------------------------------- the command preamble
#
# What the command does, shown once at the head of every session report, and
# the parameters it quotes back. A dedented block rather than lines carrying
# their own `\n    `: this is prose, it is read as prose, and it should be
# reviewable as prose. The parameter list is a list rather than a format string
# with one interpolation each, so it cannot drift from `options`.
BOLD_STATS_PURPOSE = """\
Per frame statistics are computed for each of the specified BOLD files, from
its movement correction parameter file and an analysis of the image. The
results are saved as *.bstat and *.bscrub files in the images/movement
subfolder. Only the images named by --bolds are processed. Note that the NIfTI
volume image is used even when the target format is CIFTI."""

BOLD_STATS_PARAMETERS = [
    "mov_radius",
    "mov_fd",
    "mov_dvars",
    "mov_dvarsme",
    "mov_after",
    "mov_before",
    "mov_bad",
]


def compute_bold_stats(sinfo, options, overwrite=False, thread=0):
    """
    ``compute_bold_stats [... processing options]``

    Process specified BOLD files and save images/function/movement files.

    ..  qx_command:
        type: processing.session

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
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

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
            The path to the folder where logs are to be stored,
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
            dvarsme, idvars, idvarsme, udvars, udvarsme). See movement scrubbing
            documentation for further information.
            Criteria for identification of bad frames can be one out of:

            - 'mov'      ... Frame displacement threshold (fdt) is exceeded.
            - 'dvars'    ... Image intensity normalized root mean squared error
              (RMSE) threshold (dvarsmt) is exceeded.
            - 'dvarsme'  ... Median normalised RMSE (dvarsmet) threshold is
              exceeded.
            - 'idvars'   ... Both fdt and dvarsmt are exceeded (i for
              intersection).
            - 'udvars'   ... Either fdt or dvarsmt are exceeded (u for union).
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
    log.action("Computing", "BOLD image statistics ...", options["run"], level="info")
    log.blank()
    log.info(BOLD_STATS_PURPOSE)

    pc.do_options_check(options, sinfo, "compute_bold_stats")
    d = pc.get_session_folders(sinfo, options)

    if overwrite:
        ostatus = "will"
    else:
        ostatus = "will not"

    log.step("Using parameters for computing scrubbing information")
    for name in BOLD_STATS_PARAMETERS:
        log.detail(f"--{name}: {options[name]}")

    log.step(f"Working on BOLD images in {d['s_bold']}")
    log.detail(f"images{options['img_suffix']}/functional{options['bold_variant']} will be processed")
    log.detail(f"the resulting files will be in {d['s_bold_mov']}")
    log.detail(f"{', '.join(options['bolds'].split('|'))} BOLD files will be processed (see --bolds)")
    log.detail(f"existing statistics {ostatus} be overwritten (see --overwrite)")

    bolds, bskip, report["boldskipped"] = pc.use_or_skip_bold(sinfo, options, _log=log)

    parelements = options["parelements"]
    log.info(f"Processing {parelements} BOLDs in parallel")

    if parelements == 1:  # serial execution
        for b in bolds:
            # process
            result = execute_compute_bold_stats(sinfo, options, overwrite, b)

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
        f = partial(execute_compute_bold_stats, sinfo, options, overwrite)
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
    log.info(f"Bold statistics computation completed on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}")
    log.rule()
    rstatus = (
        "BOLDS done: %(bolddone)2d, missing data: %(boldmissing)2d, failed: %(boldfail)2d, processed: %(boldok)2d, skipped: %(boldskipped)2d"
        % (report)
    )

    # print r
    return log.result(rstatus, report["boldmissing"] + report["boldfail"], sinfo["id"])


def execute_compute_bold_stats(sinfo, options, overwrite, boldinfo):

    # prepare return variables
    log = ReportLog()
    report = {"bolddone": 0, "boldok": 0, "boldfail": 0, "boldmissing": 0}

    log.step("Working on " + boldinfo["name"] + " ...")

    try:
        # --- filenames

        f = pc.get_file_names(sinfo, options)
        f.update(pc.get_bold_file_names(sinfo, boldinfo["name"], options))
        d = pc.get_session_folders(sinfo, options)

        # --- check for data availability

        log.detail("checking for data")
        status = True

        # --- movement
        status = pc.check_for_file(f["bold_mov"],
            f"movement data present [{os.path.basename(f['bold_mov'])}]",
            f"movement data missing [{os.path.basename(f['bold_mov'])}]",
            status=status,
            _log=log,
        )

        # --- bold
        status = pc.check_for_file(f["bold_vol"],
            f"bold data present [{os.path.basename(f['bold_vol'])}]",
            f"bold data missing [{os.path.basename(f['bold_vol'])}]",
            status=status,
            _log=log,
        )

        # --- check
        if not status:
            log.error("Files missing, skipping this bold run!")
            report["boldmissing"] += 1
            return {"r": log.text, "report": report}

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
            log.pipeline_command(comm, title="Running:")
        runit = True
        if os.path.exists(f["bold_stats"]) and not overwrite:
            report["bolddone"] += 1
            runit = False
        endlog, status, failed = dryrun.run_external(
            log,
            options,
            f["bold_stats"],
            comm,
            "... running matlab general_compute_bold_stats on %s" % (f["bold_vol"]),
            overwrite=overwrite,
            thread=sinfo["id"],
            remove=options["log"] == "remove",
            task=options["command_ran"],
            logfolder=options["comlogs"],
            logtags=[
                options["bold_variant"],
                options["logtag"],
                "B%d" % boldinfo["bold_number"],
            ],
            shell=True,
        )
        status = pc.check_for_file(
            f["bold_stats"],
            bad=f"Matlab/Octave has failed preprocessing BOLD using command: {comm}",
            bad_level="error",
            _log=log,
        )

        if status and runit:
            report["boldok"] += 1
        elif runit:
            report["boldfail"] += 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        report["boldfail"] += 1
    except Exception:
        log.error(f"Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n")
        report["boldfail"] += 1

    return {"r": log.text, "report": report}
