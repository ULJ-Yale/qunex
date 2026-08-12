#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_long_post_freesurfer.py``

The longitudinal HCP PostFreeSurfer pipeline.
"""

import os
import os.path
import shutil
from datetime import datetime

import qx_utilities.general.exceptions as ge
import qx_utilities.processing.core as pc
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    _append_sorted_logdir_to_log,
    _check_hcp_info,
    _set_hcp_prefs_template_res,
    do_hcp_options_check,
)


def hcp_long_post_freesurfer(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_long_post_freesurfer [... processing options]``

    Run the HCP Longitudinal FreeSurfer Pipeline (LongitudinalFreeSurferPipeline.sh).

    ..  qx_command:
        type: processing.subject
        aliases: hcp_lpfs

    Warning:
        The code expects the first three HCP preprocessing steps
        (hcp_pre_freesurfer, hcp_freesurfer and hcp_post_freesurfer) to have
        been run and finished successfully.

    Parameters:
        --batchfile (str, default ""):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default "."):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsubjects (int, default 1):
            How many subjects to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ""):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ""):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_longitudinal_template (str, default "base"):
            Name of the longitudinal template.

        --hcp_t2 (str, default 't2'):
            'NONE' if no T2w image is available and the preprocessing should be
            run without them, anything else otherwise. 'NONE' is only valid if
            'LegacyStyleData' processing mode was specified.

        --hcp_prefs_template_res (float, default set from imaging data):
            The resolution (in mm) of the structural images templates to use in
            the preFS step. Note: it should match the resolution of the
            acquired structural images. If no value is provided, QuNex will try
            to use the imaging data to set a sensible default value. It will
            notify you about which setting it used, you should pay attention to
            this piece of information and manually overwrite the default if
            something is off.

        --hcp_prefs_t1template (str, default ""):
            Path to the T1 template to be used by PreFreeSurfer. By default the
            used template is determined through the resolution provided by the
            hcp_prefs_template_res parameter.

        --hcp_prefs_t1templatebrain (str, default ""):
            Path to the T1 brain template to be used by PreFreeSurfer. By
            default the used template is determined through the resolution
            provided by the hcp_prefs_template_res parameter.

        --hcp_prefs_t1template2mm (str, default ""):
            Path to the T1 2mm template to be used by PreFreeSurfer. By default
            the used template is HCP's MNI152_T1_2mm.nii.gz.

        --hcp_prefs_t2template (str, default ""):
            Path to the T2 template to be used by PreFreeSurfer. By default the
            used template is determined through the resolution provided by the
            hcp_prefs_template_res parameter.

        --hcp_prefs_t2templatebrain (str, default ""):
            Path to the T2 brain template to be used by PreFreeSurfer. By
            default the used template is determined through the resolution
            provided by the hcp_prefs_template_res parameter.

        --hcp_prefs_t2template2mm (str, default ""):
            Path to the T2 2mm template to be used by PreFreeSurfer. By default
            the used template is HCP's MNI152_T2_2mm.nii.gz.

        --hcp_prefs_templatemask (str, default ""):
            Path to the template mask to be used by PreFreeSurfer. By default
            the used template mask is determined through the resolution provided
            by the hcp_prefs_template_res parameter.

        --hcp_prefs_template2mmmask (str, default ""):
            Path to the template mask to be used by PreFreeSurfer. By default
            the used 2mm template mask is HCP's
            MNI152_T1_2mm_brain_mask_dil.nii.gz.

        --hcp_prefs_fnirtconfig (str, default ""):
            Path to the used FNIRT config. Set to the HCP's T1_2_MNI152_2mm.cnf
            by default.

        --hcp_freesurfer_labels (str, default "${HCPPIPEDIR}/global/config/FreeSurferAllLut.txt"):
            Path to the location of the FreeSurfer look up table file.

        --hcp_surfatlasdir (str, HCP "standard_mesh_atlases"):
            Surface atlas directory.

        --hcp_grayordinatesres (str, default '2'):
            The resolution of the volume part of the grayordinate representation
            in mm.

        --hcp_grayordinatesdir (str, default HCP "91282_Greyordinates"):
            Grayordinates space directory.

        --hcp_subcortgraylabels (str, default HCP "FreeSurferSubcorticalLabelTableLut.txt"):
            The location of FreeSurferSubcorticalLabelTableLut.txt.

        --hcp_refmyelinmaps (str, default HCP "Conte69.MyelinMap_BC.164k_fs_LR.dscalar.nii"):
            Group myelin map to use for bias correction.

        --hcp_hiresmesh (int, default 164):
            The number of vertices for the high resolution mesh of each
            hemisphere (in thousands).

        --hcp_lowresmesh (str, default '32'):
            The number of vertices for the low resolution mesh of each
            hemisphere (in thousands). Provide a comma separated list of numbers
            to generate multiple low resolution meshes, for example: 32,10.

        --hcp_regname (str, default "MSMSulc"):
            The registration used, FS or MSMSulc.

        --hcp_parallel_mode (str, default "BUILTIN"):
            Parallelization execution mode, one of FSLSUB, BUILTIN, NONE.

        --hcp_fslsub_queue (str, default ""):
            FSLSUB queue name.

        --hcp_max_jobs (int, default -1):
            Maximum number of concurrent processes in BUILTIN mode. Set to -1 to
            auto-detect.

        --hcp_start_stage (str, default "PREP-T"):
            One of:
                - PREP-T (PostFSPrepLong build template, skip timepoint
                         processing),
                - POSTFS-TP1 (PostFreeSurfer timepoint stage 1),
                - POSTFS-T (PostFreesurfer template),
                - POSTFS-TP2 (PostFreesurfer timepoint stage 2).

        --hcp_end_stage (str, default "POSTFS-TP2"):
            One of:
                - PREP-T (PostFSPrepLong build template, skip timepoint
                         processing),
                - POSTFS-TP1 (PostFreeSurfer timepoint stage 1),
                - POSTFS-T (PostFreesurfer template),
                - POSTFS-TP2 (PostFreesurfer timepoint stage 2).

    Output files:
        The results of this step will be present in the
        <study_folder>/<sessions_folder>/<subject_id>.

    Notes:
        hcp_long_post_freesurfer parameter mapping:

            =================================== ===========================
            QuNex parameter                     HCPpipelines parameter
            =================================== ===========================
            ``hcp_longitudinal_template``       ``longitudinal_template``
            ``hcp_prefs_t1template``            ``t1template``
            ``hcp_prefs_t1templatebrain``       ``t1templatebrain``
            ``hcp_prefs_t1template2mm``         ``t1template2mm``
            ``hcp_prefs_t2template``            ``t2template``
            ``hcp_prefs_t2templatebrain``       ``t2templatebrain``
            ``hcp_prefs_t2template2mm``         ``t2template2mm``
            ``hcp_prefs_templatemask``          ``templatemask``
            ``hcp_prefs_template2mmmask``       ``template2mmmask``
            ``hcp_prefs_fnirtconfig``           ``fnirtconfig``
            ``hcp_freesurfer_labels``           ``freesurferlabels``
            ``hcp_surfatlasdir``                ``surfatlasdir``
            ``hcp_grayordinatesres``            ``grayordinatesres``
            ``hcp_grayordinatesdir``            ``grayordinatesdir``
            ``hcp_subcortgraylabels``           ``subcortgraylabels``
            ``hcp_refmyelinmaps``                ``refmyelinmaps``
            ``hcp_hiresmesh``                   ``hiresmesh``
            ``hcp_lowresmesh``                  ``lowresmesh``
            ``hcp_regname``                     ``regname``
            ``hcp_parallel_mode``               ``parallel-mode``
            ``hcp_fslsub_queue``                ``fslsub-queue``
            ``hcp_max_jobs``                    ``max-jobs``
            ``hcp_start_stage``                 ``start-stage``
            ``hcp_end_stage``                   ``end-stage``
            =================================== ===========================

    Examples:
        ::

            qunex hcp_long_post_freesurfer \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"
    """

    subject_id = sinfo[0]["subject"]

    log = SessionLog({"id": subject_id}, options, "HCP Longitudnal Post FS Pipeline", label="Subject")

    run = True
    report = {"done": [], "failed": [], "ready": [], "not ready": []}
    failed = 0

    try:
        # checks
        pc.do_options_check(options, sinfo[0], "hcp_long_post_freesurfer")
        do_hcp_options_check(options, "hcp_long_post_freesurfer")
        hcp = _check_hcp_info(sinfo, options)

        # -- Prepare templates
        # try to set hcp_prefs_template_res automatically if not set yet
        if not options["hcp_prefs_template_res"]:
            log.step("Trying to set the hcp_prefs_template_res parameter automatically.")
            t1w = hcp["T1w"].split("@")[0]
            resolution, res_report = _set_hcp_prefs_template_res(t1w)
            log.raw(res_report)
            if resolution == 0:
                run = False
                log.error("unable to set hcp_prefs_template_res automatically, please set it manually!", depth=1)
            else:
                options["hcp_prefs_template_res"] = resolution

        # if hcp_prefs_template_res cannot be converted to a number something went wrong
        try:
            float(options["hcp_prefs_template_res"])
        except Exception:
            log.error(f"hcp_prefs_template_res  [{options['hcp_prefs_template_res']}] is not a number! It could be that automatic setup did not work, set it manually.")
            run = False

        # hcp_prefs_t1template
        if options["hcp_prefs_t1template"] is None:
            t1template = os.path.join(
                hcp["hcp_Templates"],
                "MNI152_T1_%smm.nii.gz" % (options["hcp_prefs_template_res"]),
            )
        else:
            t1template = options["hcp_prefs_t1template"]

        # hcp_prefs_t1templatebrain
        if options["hcp_prefs_t1templatebrain"] is None:
            t1templatebrain = os.path.join(
                hcp["hcp_Templates"],
                "MNI152_T1_%smm_brain.nii.gz" % (options["hcp_prefs_template_res"]),
            )
        else:
            t1templatebrain = options["hcp_prefs_t1templatebrain"]

        # hcp_prefs_t1template2mm
        if options["hcp_prefs_t1template2mm"] is None:
            t1template2mm = os.path.join(hcp["hcp_Templates"], "MNI152_T1_2mm.nii.gz")
        else:
            t1template2mm = options["hcp_prefs_t1template2mm"]

        # hcp_prefs_t2template
        if options["hcp_t2"] == "NONE":
            t2template = ""
        elif options["hcp_prefs_t2template"] is None:
            t2template = os.path.join(
                hcp["hcp_Templates"],
                "MNI152_T2_%smm.nii.gz" % (options["hcp_prefs_template_res"]),
            )
        else:
            t2template = options["hcp_prefs_t2template"]

        # hcp_prefs_t2templatebrain
        if options["hcp_t2"] == "NONE":
            t2templatebrain = ""
        elif options["hcp_prefs_t2templatebrain"] is None:
            t2templatebrain = os.path.join(
                hcp["hcp_Templates"],
                "MNI152_T2_%smm_brain.nii.gz" % (options["hcp_prefs_template_res"]),
            )
        else:
            t2templatebrain = options["hcp_prefs_t2templatebrain"]

        # hcp_prefs_t2template2mm
        if options["hcp_t2"] == "NONE":
            t2template2mm = ""
        elif options["hcp_prefs_t2template2mm"] is None:
            t2template2mm = os.path.join(hcp["hcp_Templates"], "MNI152_T2_2mm.nii.gz")
        else:
            t2template2mm = options["hcp_prefs_t2template2mm"]

        # hcp_prefs_templatemask
        if options["hcp_prefs_templatemask"] is None:
            templatemask = os.path.join(
                hcp["hcp_Templates"],
                "MNI152_T1_%smm_brain_mask.nii.gz"
                % (options["hcp_prefs_template_res"]),
            )
        else:
            templatemask = options["hcp_prefs_templatemask"]

        # hcp_prefs_template2mmmask
        if options["hcp_prefs_template2mmmask"] is None:
            template2mmmask = os.path.join(
                hcp["hcp_Templates"], "MNI152_T1_2mm_brain_mask_dil.nii.gz"
            )
        else:
            template2mmmask = options["hcp_prefs_template2mmmask"]

        # hcp_prefs_fnirtconfig
        if options["hcp_prefs_fnirtconfig"] is None:
            fnirtconfig = os.path.join(hcp["hcp_Config"], "T1_2_MNI152_2mm.cnf")
        else:
            fnirtconfig = options["hcp_prefs_fnirtconfig"]

        # hcp_freesurfer_labels
        freesurferlabels = ""
        if options["hcp_freesurfer_labels"] is None:
            freesurferlabels = os.path.join(hcp["hcp_Config"], "FreeSurferAllLut.txt")
        else:
            freesurferlabels = options["hcp_freesurfer_labels"]

        # hcp_surfatlasdir
        surfatlasdir = ""
        if options["hcp_surfatlasdir"] is None:
            surfatlasdir = os.path.join(hcp["hcp_Templates"], "standard_mesh_atlases")
        else:
            surfatlasdir = options["hcp_surfatlasdir"]

        # hcp_grayordinatesdir
        grayordinatesdir = ""
        if options["hcp_grayordinatesdir"] is None:
            grayordinatesdir = os.path.join(hcp["hcp_Templates"], "91282_Greyordinates")
        else:
            grayordinatesdir = options["hcp_grayordinatesdir"]

        # hcp_subcortgraylabels
        subcortgraylabels = ""
        if options["hcp_subcortgraylabels"] is None:
            subcortgraylabels = os.path.join(
                hcp["hcp_Config"], "FreeSurferSubcorticalLabelTableLut.txt"
            )
        else:
            subcortgraylabels = options["hcp_subcortgraylabels"]

        # hcp_refmyelinmaps
        refmyelinmaps = ""
        if options["hcp_refmyelinmaps"] is None:
            refmyelinmaps = os.path.join(
                hcp["hcp_Templates"],
                "standard_mesh_atlases",
                "Conte69.MyelinMap_BC.164k_fs_LR.dscalar.nii",
            )
        else:
            refmyelinmaps = options["hcp_refmyelinmaps"]

        # logdir
        logdir = os.path.join(
            options["logfolder"],
            "comlogs",
            f"extra_logs_hcp_long_post_freesurfer_{subject_id}",
        )
        if os.path.exists(logdir):
            shutil.rmtree(logdir)
        os.makedirs(logdir)

        # subject folder
        studyfolder = os.path.join(
            options["sessionsfolder"].replace("sessions", "subjects"), subject_id
        )

        # build the command
        if run:
            comm = (
                '%(script)s \
                --study-folder="%(studyfolder)s" \
                --subject="%(subject)s" \
                --sessions="%(sessions)s" \
                --longitudinal-template="%(longitudinal_template)s" \
                --t1template="%(t1template)s" \
                --t1templatebrain="%(t1templatebrain)s" \
                --t1template2mm="%(t1template2mm)s" \
                --t2template="%(t2template)s" \
                --t2templatebrain="%(t2templatebrain)s" \
                --t2template2mm="%(t2template2mm)s" \
                --templatemask="%(templatemask)s" \
                --template2mmmask="%(template2mmmask)s" \
                --fnirtconfig="%(fnirtconfig)s" \
                --freesurferlabels="%(freesurferlabels)s" \
                --surfatlasdir="%(surfatlasdir)s" \
                --grayordinatesres="%(grayordinatesres)s" \
                --grayordinatesdir="%(grayordinatesdir)s" \
                --hiresmesh="%(hiresmesh)s" \
                --lowresmesh="%(lowresmesh)s" \
                --subcortgraylabels="%(subcortgraylabels)s" \
                --refmyelinmaps="%(refmyelinmaps)s" \
                --regname="%(regname)s" \
                --parallel-mode="%(parallel_mode)s" \
                --logdir="%(logdir)s"'
                % {
                    "script": os.path.join(
                        hcp["hcp_base"],
                        "PostFreeSurfer",
                        "PostFreeSurferPipelineLongLauncher.sh",
                    ),
                    "studyfolder": studyfolder,
                    "subject": subject_id,
                    "sessions": "@".join([session["id"] for session in sinfo]),
                    "longitudinal_template": options["hcp_longitudinal_template"],
                    "t1template": t1template,
                    "t1templatebrain": t1templatebrain,
                    "t1template2mm": t1template2mm,
                    "t2template": t2template,
                    "t2templatebrain": t2templatebrain,
                    "t2template2mm": t2template2mm,
                    "templatemask": templatemask,
                    "template2mmmask": template2mmmask,
                    "fnirtconfig": fnirtconfig,
                    "freesurferlabels": freesurferlabels,
                    "surfatlasdir": surfatlasdir,
                    "grayordinatesres": options["hcp_grayordinatesres"],
                    "grayordinatesdir": grayordinatesdir,
                    "hiresmesh": options["hcp_hiresmesh"],
                    "lowresmesh": options["hcp_lowresmesh"].replace(",", "@"),
                    "subcortgraylabels": subcortgraylabels,
                    "refmyelinmaps": refmyelinmaps,
                    "regname": options["hcp_regname"],
                    "parallel_mode": options["hcp_parallel_mode"],
                    "logdir": logdir,
                }
            )

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

            # -- Test file
            tfile = None

            if options["run"] == "run":
                endlog, _, failed = pc.run_external_for_file(
                    tfile,
                    comm,
                    "Running HCP Longitudinal Post FS",
                    overwrite=overwrite,
                    thread=subject_id,
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    full_test=None,
                    shell=True,
                    _log=log,
                )

                if failed == 0:
                    report = "processing completed"
                else:
                    report = "processing failed"

                # read and print all files in logdir
                with open(endlog, "a", encoding="utf-8") as log_file:
                    _append_sorted_logdir_to_log(log_file, logdir)
                    # print succesful completion
                    print(
                        f"\n---> Successful completion of task at {datetime.now()}",
                        file=log_file,
                    )

                # remove the directory and its contents
                shutil.rmtree(logdir)

        else:
            log.step("Subject cannot be processed.")
            report = "not ready"

    except ge.CommandFailed as e:
        log.raw("\n" + ge.report_command_failed("hcp_long_post_freesurfer", e))
        report = "processing failed"
        failed += 1
    except ge.CommandError as e:
        log.raw("\n" + ge.report_command_error("hcp_long_post_freesurfer", e))
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

    log.close(pipeline="HCP Longitudinal Post FS Preprocessing")

    return log.result((subject_id, report, failed))
