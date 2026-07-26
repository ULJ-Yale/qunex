#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_task_fmri_analysis.py``

The HCP task fMRI analysis pipeline.
"""

import os
import os.path

import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    do_hcp_options_check,
)


def hcp_task_fmri_analysis(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_task_fmri_analysis [... processing options]``

    Run the Task fMRI analysis step of the HCP Pipeline (TaskfMRIAnalysis.sh).

    ..  qx_command:
        type: processing.session

    Warning:
        The requirement for this command is a successful completion of the
        minimal HCP preprocessing pipeline.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the session's information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_task_lvl1tasks (str, default ''):
            List of task fMRI scan names, which are the prefixes of the time
            series filename for the TaskName task. Multiple task fMRI scan
            names should be provided as a comma separated list.

        --hcp_task_lvl1fsfs (str, default ''):
            List of design names, which are the prefixes of the fsf filenames
            for each scan run. Should contain same number of design files as
            time series images in --hcp_task_lvl1tasks option (N-th design will
            be used for N-th time series image). Provide a comma separated list
            of design names. If no value is passed to --hcp_task_lvl1fsfs, the
            value will be set to --hcp_task_lvl1tasks.

        --hcp_task_lvl2task (str, default NONE):
            Name of Level2 subdirectory in which all Level2 feat directories are
            written for TaskName.

        --hcp_task_lvl2fsf (str, default ''):
            Prefix of design.fsf filename for the Level2 analysis for TaskName.
            If no value is passed to --hcp_task_lvl2fsf, the value will be set
            to the same list passed to --hcp_task_lvl2task.

        --hcp_task_summaryname (str, default 'NONE'):
            Naming convention for single-subject summary directory. Mandatory
            when running Level1 analysis only, and should match naming of
            Level2 summary directories. Default when running Level2 analysis is
            derived from --hcp_task_lvl2task and --hcp_task_lvl2fsf options
            'tfMRI_TaskName/DesignName_TaskName'.

        --hcp_task_confound (str, default 'NONE'):
            Confound matrix text filename (e.g., output of fsl_motion_outliers).
            Assumes file is in <SubjectID>/MNINonLinear/Results/<ScanName>.

        --hcp_bold_smoothFWHM (str, default '2'):
            Smoothing FWHM that matches what was used in the fMRISurface
            pipeline.

        --hcp_bold_final_smoothFWHM (int, default 2):
            Value (in mm FWHM) of total desired smoothing, reached by
            calculating the additional smoothing required and applying that
            additional amount to data previously smoothed in fMRISurface.
            Default=2, which is no additional smoothing above HCP minimal
            preprocessing pipelines outputs.

        --hcp_task_highpass (int, default 200):
            Apply additional highpass filter (in seconds) to time series and
            task design. This is above and beyond temporal filter applied
            during preprocessing. To apply no additional filtering, set to
            'NONE'.

        --hcp_task_lowpass (str, default 'NONE'):
            Apply additional lowpass filter (in seconds) to time series and task
            design. This is above and beyond temporal filter applied during
            preprocessing. Low pass filter is generally not advised for Task
            fMRI analyses.

        --hcp_task_procstring (str, default 'NONE'):
            String value in filename of time series image, specifying the
            additional processing that was previously applied (e.g.,
            FIX-cleaned data with 'hp2000_clean' in filename).

        --hcp_regname (str, default 'MSMSulc'):
            Name of surface registration technique.

        --hcp_grayordinatesres (str, default '2'):
            Value (in mm) that matches value in 'Atlas_ROIs' filename.

        --hcp_lowresmesh (str, default '32'):
            Value (in mm) that matches surface resolution for fMRI data.

        --hcp_task_vba (flag, optional):
            A flag for using VBA. Only use this flag if you want unconstrained
            volumetric blurring of your data, otherwise set to NO for faster,
            less biased, and more senstive processing (grayordinates results do
            not use unconstrained volumetric blurring and are always produced).
            This flag is not set by defult.

        --hcp_task_parcellation (str, default 'NONE'):
            Name of parcellation scheme to conduct parcellated analysis. Default
            setting is NONE, which will perform dense analysis instead.
            Non-greyordinates parcellations are not supported because they are
            not valid for cerebral cortex. Parcellation supersedes smoothing
            (i.e. no smoothing is done).

        --hcp_task_parcellation_file (str, default 'NONE'):
            Absolute path to the parcellation dlabel file.

    Output files:
        The results of this step will be populated in the MNINonLinear
        folder inside the same sessions's root hcp folder.

    Notes:
        Mapping of QuNex parameters onto HCP Pipelines parameters:
            Below is a detailed specification about how QuNex parameters are
            mapped onto the HCP Pipelines parameters.

            ============================== ======================
            QuNex parameter                HCPpipelines parameter
            ============================== ======================
            ``hcp_task_lvl1task``          ``lvl1tasks``
            ``hcp_task_lvl1fsfs``          ``lvl1fsfs``
            ``hcp_task_lvl2task``          ``lvl2task``
            ``hcp_task_lvl2fsf``           ``lvl2fsf``
            ``hcp_task_confound``          ``confound``
            ``hcp_bold_smoothFWHM``        ``origsmoothingFWHM``
            ``hcp_bold_final_smoothFWHM``  ``finalsmoothingFWHM``
            ``hcp_task_highpass``          ``highpassfilter``
            ``hcp_task_lowpass``           ``lowpassfilter``
            ``hcp_task_procstring``        ``procstring``
            ``hcp_regname``                ``regname``
            ``hcp_grayordinatesres``       ``grayordinatesres``
            ``hcp_lowresmesh``             ``lowresmesh``
            ``hcp_task_vba``               ``vba``
            ``hcp_task_parcellation``      ``parcellation``
            ``hcp_task_parcellation_file`` ``parcellationfile``
            ============================== ======================

    Examples:
        First level HCP TaskfMRIanalysis::

            qunex hcp_task_fmri_analysis \\
                --sessionsfolder="<study_path>/sessions" \\
                --batchfile="<study_path>/processing/batch.txt" \\
                --hcp_task_lvl1tasks="tfMRI_GUESSING_PA" \\
                --hcp_task_summaryname="tfMRI_GUESSING/tfMRI_GUESSING"

        Second level HCP TaskfMRIanalysis::

            qunex hcp_task_fmri_analysis \\
                --sessionsfolder="<study_path>/sessions" \\
                --batchfile="<study_path>/processing/batch.txt" \\
                --hcp_task_lvl1tasks="tfMRI_GUESSING_AP@tfMRI_GUESSING_PA" \\
                --hcp_task_lvl2task="tfMRI_GUESSING"
    """

    log = SessionLog(sinfo, options, "HCP fMRI task analysis pipeline")

    run = True
    report = "Error"

    try:
        pc.do_options_check(options, sinfo, "hcp_task_fmri_analysis")
        do_hcp_options_check(options, "hcp_task_fmri_analysis")
        hcp = get_hcp_paths(sinfo, options)

        if "hcp" not in sinfo:
            log.raw("\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"]))
            run = False

        # parse input parameters
        # hcp_task_lvl1tasks
        lvl1tasks = ""
        if options["hcp_task_lvl1tasks"] is not None:
            lvl1tasks = options["hcp_task_lvl1tasks"].replace(",", "@")
        else:
            log.error("hcp_task_lvl1tasks parameter is not provided")
            run = False

        # --- build the command
        if run:
            comm = (
                '%(script)s \
                --study-folder="%(studyfolder)s" \
                --subject="%(subject)s" \
                --lvl1tasks="%(lvl1tasks)s" '
                % {
                    "script": os.path.join(
                        hcp["hcp_base"], "TaskfMRIAnalysis", "TaskfMRIAnalysis.sh"
                    ),
                    "studyfolder": sinfo["hcp"],
                    "subject": sinfo["id"] + options["hcp_suffix"],
                    "lvl1tasks": lvl1tasks,
                }
            )

            # optional parameters
            # hcp_task_lvl1fsfs
            if options["hcp_task_lvl1fsfs"] is not None:
                lvl1fsfs = options["hcp_task_lvl1fsfs"].replace(",", "@")
                if len(lvl1fsfs.split(",")) != len(lvl1tasks.split(",")):
                    log.error("mismatch in the length of hcp_task_lvl1tasks and hcp_task_lvl1fsfs")
                    run = False

                comm += '                --lvl1fsfs="%s"' % lvl1fsfs

            # hcp_task_lvl2task
            if options["hcp_task_lvl2task"] is not None:
                comm += '                --lvl2task="%s"' % options["hcp_task_lvl2task"]

                # hcp_task_lvl2fsf
                if options["hcp_task_lvl2fsf"] is not None:
                    comm += (
                        '                --lvl2fsf="%s"' % options["hcp_task_lvl2fsf"]
                    )

            # summary name
            # mandatory for Level1
            if (
                options["hcp_task_lvl2task"] is None
                and options["hcp_task_summaryname"] is None
            ):
                log.error("hcp_task_summaryname is mandatory when running Level1 analysis!")
                run = False

            if options["hcp_task_summaryname"] is not None:
                comm += (
                    '                --summaryname="%s"'
                    % options["hcp_task_summaryname"]
                )

            # confound
            if options["hcp_task_confound"] is not None:
                comm += '                --confound="%s"' % options["hcp_task_confound"]

            # origsmoothingFWHM
            if options["hcp_bold_smoothFWHM"] != "2":
                comm += (
                    '                --origsmoothingFWHM="%s"'
                    % options["hcp_bold_smoothFWHM"]
                )

            # finalsmoothingFWHM
            if options["hcp_bold_final_smoothFWHM"] is not None:
                comm += (
                    '                --finalsmoothingFWHM="%s"'
                    % options["hcp_bold_final_smoothFWHM"]
                )

            # highpassfilter
            if options["hcp_task_highpass"] is not None:
                comm += (
                    '                --highpassfilter="%s"'
                    % options["hcp_task_highpass"]
                )

            # lowpassfilter
            if options["hcp_task_lowpass"] is not None:
                comm += (
                    '                --lowpassfilter="%s"' % options["hcp_task_lowpass"]
                )

            # procstring
            if options["hcp_task_procstring"] is not None:
                comm += (
                    '                --procstring="%s"' % options["hcp_task_procstring"]
                )

            # regname
            if options["hcp_regname"] is not None and options["hcp_regname"] not in [
                "MSMSulc",
                "NONE",
                "none",
                "None",
            ]:
                comm += '                --regname="%s"' % options["hcp_regname"]

            # grayordinatesres
            if (
                options["hcp_grayordinatesres"] is not None
                and options["hcp_grayordinatesres"] != "2"
            ):
                comm += (
                    '                --grayordinatesres="%s"'
                    % options["hcp_grayordinatesres"]
                )

            # lowresmesh
            if (
                options["hcp_lowresmesh"] is not None
                and options["hcp_lowresmesh"] != "32"
            ):
                comm += '                --lowresmesh="%s"' % options["hcp_lowresmesh"]

            # parcellation
            if options["hcp_task_parcellation"] is not None:
                comm += (
                    '                --parcellation="%s"'
                    % options["hcp_task_parcellation"]
                )

            # parcellationfile
            if options["hcp_task_parcellation_file"] is not None:
                comm += (
                    '                --parcellationfile="%s"'
                    % options["hcp_task_parcellation_file"]
                )

            # hcp_task_vba flag
            if options["hcp_task_vba"]:
                comm += '                --vba="YES"'

            # -- Report command
            if run:
                log.raw("\n\n------------------------------------------------------------\n")
                log.raw("Running HCP Pipelines command via QuNex:\n\n")
                log.raw(comm.replace("                --", "\n    --"))
                log.raw("\n------------------------------------------------------------\n")

        # -- Run
        if run:
            if options["run"] == "run":
                endlog, report, failed = log.run_external(
                    None,
                    comm,
                    "Running HCP fMRI task analysis",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    full_test=None,
                    shell=True,
                )

            # -- just checking
            else:
                passed, report, failed = log.check_run(
                    None, None, "HCP Diffusion", overwrite=overwrite
                )
                if passed is None:
                    log.step("HCP fMRI task analysis can be run")
                    report = "HCP fMRI task analysis can be run"
                    failed = 0

        else:
            log.step("Session cannot be processed.")
            report = "HCP fMRI task analysis cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        failed = 1
    except Exception:
        log.unknown_error()
        failed = 1

    log.close(pipeline="HCP fMRI task analysis Preprocessing")

    return log.result(report, failed)
