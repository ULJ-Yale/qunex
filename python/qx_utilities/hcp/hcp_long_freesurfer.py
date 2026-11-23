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
import qx_utilities.processing.core as pc
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    _check_hcp_info,
    do_hcp_options_check,
    run_longitudinal_pipeline,
)


def hcp_long_freesurfer(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_long_freesurfer [... processing options]``

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
        sessionsfolder = options["sessionsfolder"]
        subjectsfolder = sessionsfolder.replace("sessions", "subjects")
        study_folder = os.path.join(subjectsfolder, subject_id)
        dry = options["run"] != "run"
        if not dry:
            os.makedirs(study_folder, exist_ok=True)

        longitudinal_template = options["hcp_longitudinal_template"]
        long_dir = os.path.join(
            study_folder, f"{subject_id}.long.{longitudinal_template}"
        )

        # exit if overwrite is not set, else cleanup
        long_dir_exists = os.path.lexists(long_dir)
        if not overwrite and long_dir_exists:
            log.error(f"{long_dir} already exists and overwrite is set to no!")
            run = False
        elif long_dir_exists and dry:
            log.step(f"test, not removed: {long_dir}")
        else:
            if long_dir_exists:
                if os.path.islink(long_dir):
                    long_dir_target = os.path.realpath(long_dir)
                    os.unlink(long_dir)
                    if os.path.isdir(long_dir_target):
                        shutil.rmtree(long_dir_target)
                else:
                    shutil.rmtree(long_dir)

        # symlink sessions
        for session in sinfo:
            source_dir = os.path.join(session["hcp"], session["id"])
            # check that source exists
            if not os.path.exists(source_dir):
                log.error(f"{source_dir} does not exists, cannot map into longitudinal folder structure!")
                run = False
                continue

            target_dir = os.path.join(study_folder, session["id"])
            if dry:
                log.step(f"test, not linked: {source_dir} -> {target_dir}")
            elif not gc.link_or_copy(
                source_dir, target_dir, name=session["id"], symlink=True, _log=log
            ):
                run = False

        # logdir
        logdir = os.path.join(
            options["logfolder"],
            "comlogs",
            f"extra_logs_hcp_long_freesurfer_{subject_id}",
        )
        if not dry:
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
