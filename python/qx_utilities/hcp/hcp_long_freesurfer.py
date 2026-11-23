#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_long_freesurfer.py``

The longitudinal HCP FreeSurfer pipeline.
"""

import os
import os.path
import shutil

import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.folders as gf
import qx_utilities.processing.core as pc
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    _check_hcp_info,
    do_hcp_options_check,
    run_longitudinal_pipeline,
)


def hcp_long_freesurfer(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_long_freesurfer [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run the HCP Longitudinal FreeSurfer Pipeline (LongitudinalFreeSurferPipeline.sh).

    ..  qx_command:
        type: processing.subject
        aliases: hcp_lfs

    Warning:
        The code expects the first three HCP preprocessing steps
        (hcp_pre_freesurfer, hcp_freesurfer and hcp_post_freesurfer) to have
        been run and finished successfully.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --studyfolder (str):
            The path to the study folder. The sessions are in its `sessions`
            folder, unless --sessionsfolder names another one.

        --sessionsfolder (str, default '<studyfolder>/sessions'):
            The path to the folder with the sessions. Set it only when the
            sessions are not in the `sessions` folder of the study. With
            neither --studyfolder nor --sessionsfolder given, the current
            folder is used.

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

        --hcp_no_t2w (flag, optional):
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
        The sessions' hcp folders are linked into the subject's longitudinal
        folder, <studyfolder>/subjects/<subject id>, and the results of this
        step will be present there: the template in
        <subject id>.long.<template> and each session in
        <session id>.long.<template>.

    Notes:
        hcp_long_freesurfer parameter mapping:

            =================================== ===========================
            QuNex parameter                     HCPpipelines parameter
            =================================== ===========================
            ``hcp_longitudinal_template``       ``longitudinal-template``
            ``hcp_no_t2w``                      ``use-T2w``
            ``hcp_seed``                        ``seed``
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
                --studyfolder="<path_to_study_folder>" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_longitudinal_template="<template_id>"
    """

    subject_id = sinfo[0]["subject"]

    log = SessionLog({"id": subject_id}, options, "HCP Longitudinal FS Pipeline", label="Subject")

    run = True
    report = ""
    failed = 0

    try:
        # checks
        pc.do_options_check(options, sinfo[0], "hcp_long_freesurfer")
        do_hcp_options_check(options, "hcp_long_freesurfer")
        hcp = _check_hcp_info(sinfo, options)

        # sort out the folder structure
        study_folder = os.path.join(
            gf.subjects_folder(options["studyfolder"]), subject_id
        )
        if not os.path.exists(study_folder):
            if options["run"] == "run":
                os.makedirs(study_folder)
            else:
                log.detail(f"test, not created: {study_folder}")

        longitudinal_template = options["hcp_longitudinal_template"]
        long_dir = os.path.join(
            study_folder, f"{subject_id}.long.{longitudinal_template}"
        )

        # exit if overwrite is not set, else the earlier results are removed
        # just before the run
        long_dir_exists = os.path.lexists(long_dir)
        if not overwrite and long_dir_exists:
            log.error(f"{long_dir} already exists and overwrite is set to no!")
            run = False

        # symlink sessions
        for session in sinfo:
            source_dir = os.path.join(session["hcp"], session["id"])
            target_dir = os.path.join(study_folder, session["id"])
            # check that source exists
            if not os.path.exists(source_dir):
                log.error(f"{source_dir} does not exist, cannot map into the longitudinal folder structure!")
                run = False
            elif options["run"] == "run":
                # a link left dangling, e.g. by a study that was moved, is
                # replaced
                if os.path.islink(target_dir) and not os.path.exists(target_dir):
                    os.unlink(target_dir)
                if not gc.link_or_copy(
                    source_dir,
                    target_dir,
                    name=f"session {session['id']}",
                    symlink=True,
                    _log=log,
                ):
                    run = False
            elif not os.path.exists(target_dir):
                log.detail(f"test, not linked: {target_dir}")

        # logdir, created just before the run
        logdir = os.path.join(
            options["logfolder"],
            "comlogs",
            f"extra_logs_hcp_long_freesurfer_{subject_id}",
        )

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
                        hcp["hcp_base"],
                        "FreeSurfer",
                        "LongitudinalFreeSurferPipeline.sh",
                    ),
                    "studyfolder": study_folder,
                    "subject": subject_id,
                    "sessions": "@".join([session["id"] for session in sinfo]),
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
                log.rule(before=1, after=1)
                log.raw("Running HCP Pipelines command via QuNex:\n\n")
                log.raw(comm.replace("                --", "\n    --"))
                log.rule(after=1)

            # -- Remove the results of an earlier run, just before the run
            if long_dir_exists:
                if options["run"] == "run":
                    if os.path.islink(long_dir):
                        long_dir_target = os.path.realpath(long_dir)
                        os.unlink(long_dir)
                        if os.path.isdir(long_dir_target):
                            shutil.rmtree(long_dir_target)
                    else:
                        shutil.rmtree(long_dir)
                else:
                    log.detail(f"test, not removed: {long_dir}")

            # -- Run, judged by the exit code: the results' location depends
            # on the pipeline version and the session naming
            report, failed = run_longitudinal_pipeline(
                comm, "HCP Longitudinal FS", options, overwrite, subject_id, logdir, log
            )

        else:
            log.step("Subject cannot be processed.")
            report = "not ready"
            failed = 1

    except ge.CommandFailed as e:
        log.raw("\n" + ge.report_command_failed("hcp_long_freesurfer", e))
        report = "processing failed"
        failed += 1
    except ge.CommandError as e:
        log.raw("\n" + ge.report_command_error("hcp_long_freesurfer", e))
        report = "processing failed"
        failed += 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        report = "Error"
        failed = 1
    except Exception:
        log.unknown_error()
        report = "Error"
        failed = 1

    log.close(pipeline="HCP Longitudinal FS Preprocessing")

    return log.result((subject_id, report, failed))
