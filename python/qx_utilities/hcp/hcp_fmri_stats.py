#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_fmri_stats.py``

Extraction of HCP fMRI statistics.
"""

import os
import os.path

import qx_utilities.processing.core as pc
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    do_hcp_options_check,
)


def hcp_fmri_stats(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_fmri_stats [... processing options]``

    Runs the fMRI Statistics step of HCP Pipeline (fMRIStats.sh).
    Computes fMRI statistics including mTSNR, fCNR, and percent BOLD.

    ..  qx_command:
        type: processing.session

    Warning:
        The code expects the input images to be named and present in the QuNex
        folder structure. The function will look into folder::

            <session id>/hcp/<session id>

        for data.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no).

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --log (str, default 'keep'):
            Whether to keep ('keep') or remove ('remove') the temporary logs.

        --hcp_concat_names (str, default 'fMRI_CONCAT_ALL'):
            A comma separated list of fMRI concat names (e.g. tfMRI_ALLTASKS).
            If single-run FIX is used, this list must be exactly 1 element
            long.

        --hcp_icafix_highpass (str, default '0'):
            The high pass filter value used in ICA+FIX.

        --hcp_fmristats_regname (str, default ''):
            Surface registration name.

        --hcp_fmristats_process_volume (str, default ''):
            Whether to process volume data, TRUE or FALSE.

        --hcp_fmristats_cleanup_effects (str, default ''):
            Whether to compute cleanup effects metrics, TRUE or FALSE.

        --hcp_fmristats_procstring (str, default ''):
            Processing string suffix for cleaned data.

        --hcp_fmristats_icamode (str, default ''):
            ICA mode: 'sICA' for spatial ICA only, 'sICA+tICA' for combined
            spatial+temporal ICA.

        --hcp_fmristats_fmri_names (str, default ''):
            A comma separated list of fMRI single run names (only required if
            data was processed with single-run FIX, must be in order and
            complete).

        --hcp_fmristats_tica_component_tcs (str, default ''):
            Path to tICA timecourse CIFTI (required if tica_icamode is
            sICA+tICA).

        --hcp_fmristats_tica_component_noise (str, default ''):
            Path to tICA component noise indices text file (required if
            tica_icamode is sICA+tICA).

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folder inside the same session's root hcp folder.

    Notes:
        hcp_fmri_stats parameter mapping:

            ============================================ ========================
            QuNex parameter                              HCPpipelines parameter
            ============================================ ========================
            ``hcp_concat_names``                         ``concat-names``
            ``hcp_icafix_highpass``                      ``high-pass``
            ``hcp_fmristats_procstring``                 ``proc-string``
            ``hcp_fmristats_regname``                    ``reg-name``
            ``hcp_fmristats_process_volume``             ``process-volume``
            ``hcp_fmristats_cleanup_effects``            ``cleanup-effects``
            ``hcp_fmristats_icamode``                    ``ica-mode``
            ``hcp_fmristats_fmri_names``                 ``fmri-names``
            ``hcp_fmristats_tica_component_tcs``         ``tica-component-tcs``
            ``hcp_fmristats_tica_component_noise``       ``tica-component-noise``
            ``hcp_matlab_mode``                          ``matlab-run-mode``
            ============================================ ========================

    Examples:
        ::

            qunex hcp_fmri_stats \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_concat_names="fMRI_CONCAT_ALL" \\
                --hcp_icafix_highpass="2000" \\
                --hcp_matlab_mode="interpreted"
    """

    log = SessionLog(sinfo, options, "HCP fMRIStats pipeline")

    run = True
    report = "HCP fMRI Stats"
    failed = 0

    try:
        # --- Base settings
        pc.do_options_check(options, sinfo, "hcp_fmri_stats")
        do_hcp_options_check(options, "hcp_fmri_stats")

        # subject
        subject = sinfo["id"] + options["hcp_suffix"]

        # --- Mandatory parameters
        # hcp_concat_names
        concat_names = options["hcp_concat_names"].replace(",", "@")

        # hcp_icafix_highpass
        highpass = 0
        if options["hcp_icafix_highpass"] is not None:
            highpass = options["hcp_icafix_highpass"]

        # hcp_fmristats_procstring
        if options["hcp_fmristats_procstring"] is None:
            log.error("hcp_fmristats_procstring parameter is not set!\n")
            run = False

        # --- matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                log.error("hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n")
                run = False
            else:
                matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
        else:
            if options["hcp_matlab_mode"] == "compiled":
                matlabrunmode = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                matlabrunmode = "1"
            elif options["hcp_matlab_mode"] == "octave":
                matlabrunmode = "2"
            else:
                log.error("unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n")
                run = False

        # --- Build the command
        if run:
            comm = (
                '%(script)s \
                --study-folder="%(studyfolder)s" \
                --subject="%(subject)s" \
                --concat-names="%(concat_names)s" \
                --high-pass="%(highpass)s" \
                --proc-string="%(proc_string)s" \
                --matlab-run-mode="%(matlabrunmode)s"'
                % {
                    "script": os.path.join(
                        os.environ["HCPPIPEDIR"], "fMRIStats", "fMRIStats.sh"
                    ),
                    "studyfolder": sinfo["hcp"],
                    "subject": subject,
                    "concat_names": concat_names,
                    "highpass": highpass,
                    "proc_string": options["hcp_fmristats_procstring"],
                    "matlabrunmode": matlabrunmode,
                }
            )

            # --- Optional parameters
            # hcp_fmristats_regname
            if options["hcp_fmristats_regname"] is not None and options[
                "hcp_fmristats_regname"
            ] not in [
                "NONE",
                "none",
                "None",
            ]:
                comm += (
                    '                --reg-name="%s"' % options["hcp_fmristats_regname"]
                )

            # hcp_fmristats_process_volume
            if options["hcp_fmristats_process_volume"] is not None:
                comm += (
                    '                --process-volume="%s"'
                    % options["hcp_fmristats_process_volume"]
                )

            # hcp_fmristats_cleanup_effects
            if options["hcp_fmristats_cleanup_effects"] is not None:
                comm += (
                    '                --cleanup-effects="%s"'
                    % options["hcp_fmristats_cleanup_effects"]
                )

            # hcp_fmristats_icamode
            if options["hcp_fmristats_icamode"] is not None:
                comm += (
                    '                --ica-mode="%s"' % options["hcp_fmristats_icamode"]
                )

            # hcp_fmristats_fmri_names
            if options["hcp_fmristats_fmri_names"] is not None:
                fmri_names = options["hcp_fmristats_fmri_names"].replace(",", "@")
                comm += '                --fmri-names="%s"' % fmri_names

            # hcp_fmristats_tica_component_tcs
            if options["hcp_fmristats_tica_component_tcs"] is not None:
                comm += (
                    '                --tica-component-tcs="%s"'
                    % options["hcp_fmristats_tica_component_tcs"]
                )

            # hcp_fmristats_tica_component_noise
            if options["hcp_fmristats_tica_component_noise"] is not None:
                comm += (
                    '                --tica-component-noise="%s"'
                    % options["hcp_fmristats_tica_component_noise"]
                )

            # -- Report command
            if run:
                log.raw("\n\n------------------------------------------------------------\n")
                log.raw("Running HCP Pipelines command via QuNex:\n\n")
                log.raw(comm.replace("                --", "\n    --"))
                log.raw("\n------------------------------------------------------------\n")

        # -- Run
        if run:
            if options["run"] == "run":
                endlog, report, failed = pc.run_external_for_file(
                    None,
                    comm,
                    "Running HCP fMRI Stats",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    full_test=None,
                    shell=True,
                    _log=log,
                )

            # -- just checking
            else:
                passed, report, failed = pc.check_run(
                    None, None, "HCP fMRI Stats", overwrite=overwrite, _log=log
                )
                if passed is None:
                    log.step("HCP fMRI Stats can be run")
                    report = "HCP fMRI Stats can be run"
                    failed = 0

        else:
            log.step("Session cannot be processed.")
            report = "HCP fMRI Stats cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        failed = 1
    except Exception:
        log.unknown_error()
        failed = 1

    log.close(pipeline="HCP fMRI Stats")

    return log.result(report, failed)
