#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_cortical_thickness.py``

Cortical thickness extraction from HCP-processed structural data.
"""

import os
import os.path

import qx_utilities.processing.core as pc
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import do_hcp_options_check


def hcp_cortical_thickness(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_cortical_thickness [... processing options]``

    Runs the curvature-corrected (folding-compensated) cortical thickness step
    of HCP Pipeline (CorrThick.sh). Computes and saves curvature-corrected
    thickness, curvatures, regression coefficients, and resampled outputs.

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

        --hcp_corrthick_regnames (str, default 'MSMSulc'):
            The desired registration name(s) separated by @, e.g.
            'RegName@RegName@RegName@...'.

        --hcp_corrthick_hemi (str, default 'B'):
            Hemisphere for regression calculation, L=Left, R=Right, or B=Both.

        --hcp_corrthick_surf (str, default 'midthickness'):
            Surface for regression calculation, white or midthickness.

        --hcp_corrthick_patch_size (str, default '6'):
            Patch kernel size in millimeters FWHM for regression.

        --hcp_corrthick_surf_smooth (str, default '2.14'):
            Surface smoothing in millimeters FWHM.

        --hcp_corrthick_metric_smooth (str, default '2.52'):
            Metric smoothing in millimeters FWHM.

        --hcp_corrthick_skip_computation (str, default 'NO'):
            Whether to skip computing the curvature-corrected thickness (YES),
            if it is already available, and just resample it to 164k and 32k,
            or to compute it (NO).

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folder inside the same session's root hcp folder.

    Notes:
        hcp_cortical_thickness parameter mapping:

            ============================================ ======================
            QuNex parameter                              HCPpipelines parameter
            ============================================ ======================
            ``hcp_corrthick_regnames``                   ``regnames``
            ``hcp_corrthick_hemi``                       ``hemi``
            ``hcp_corrthick_surf``                       ``surf``
            ``hcp_corrthick_patch_size``                 ``patch-size``
            ``hcp_corrthick_surf_smooth``                ``surf-smooth``
            ``hcp_corrthick_metric_smooth``              ``metric-smooth``
            ``hcp_corrthick_skip_computation``           ``skip-computation``
            ============================================ ======================

    Examples:
        ::

            qunex hcp_cortical_thickness \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_corrthick_hemi="B" \\
                --hcp_corrthick_surf="midthickness"
    """

    log = SessionLog(sinfo, options, "HCP CorrThick pipeline")

    run = True
    report = "HCP CorrThick"
    failed = 0

    try:
        # --- Base settings
        pc.do_options_check(options, sinfo, "hcp_cortical_thickness")
        do_hcp_options_check(options, "hcp_cortical_thickness")

        # subject
        subject = sinfo["id"] + options["hcp_suffix"]

        # --- Build the command
        comm = (
            '%(script)s \
            --subject-dir="%(subjectdir)s" \
            --subject="%(subject)s"'
            % {
                "script": os.path.join(
                    os.environ["HCPPIPEDIR"], "global", "scripts", "CorrThick.sh"
                ),
                "subjectdir": sinfo["hcp"],
                "subject": subject,
            }
        )

        # --- Optional parameters
        # hcp_corrthick_regnames
        if options["hcp_corrthick_regnames"] is not None:
            comm += '            --regnames="%s"' % options["hcp_corrthick_regnames"]

        # hcp_corrthick_hemi
        if options["hcp_corrthick_hemi"] is not None:
            comm += '            --hemi="%s"' % options["hcp_corrthick_hemi"]

        # hcp_corrthick_surf
        if options["hcp_corrthick_surf"] is not None:
            comm += '            --surf="%s"' % options["hcp_corrthick_surf"]

        # hcp_corrthick_patch_size
        if options["hcp_corrthick_patch_size"] is not None:
            comm += (
                '            --patch-size="%s"' % options["hcp_corrthick_patch_size"]
            )

        # hcp_corrthick_surf_smooth
        if options["hcp_corrthick_surf_smooth"] is not None:
            comm += (
                '            --surf-smooth="%s"' % options["hcp_corrthick_surf_smooth"]
            )

        # hcp_corrthick_metric_smooth
        if options["hcp_corrthick_metric_smooth"] is not None:
            comm += (
                '            --metric-smooth="%s"'
                % options["hcp_corrthick_metric_smooth"]
            )

        # hcp_corrthick_skip_computation
        if options["hcp_corrthick_skip_computation"] is not None:
            comm += (
                '            --skip-computation="%s"'
                % options["hcp_corrthick_skip_computation"]
            )

        # -- Report command
        if run:
            log.pipeline_command(comm, marker="            --")

        # -- Run
        if run:
            if options["run"] == "run":
                endlog, report, failed = log.run_external(
                    None,
                    comm,
                    "Running HCP CorrThick",
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
                    None, None, "HCP CorrThick", overwrite=overwrite
                )
                if passed is None:
                    log.step("HCP CorrThick can be run")
                    report = "HCP CorrThick can be run"
                    failed = 0

        else:
            log.step("Session cannot be processed.")
            report = "HCP CorrThick cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        failed = 1
    except Exception:
        log.unknown_error()
        failed = 1

    return log.finish(report, failed, pipeline="HCP CorrThick")
