#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_dedrift_and_resample.py``

The HCP DeDriftAndResample pipeline.
"""

from concurrent.futures import ProcessPoolExecutor
from functools import partial

import qx_utilities.general.exceptions as ge
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    parse_icafix_bolds,
    _build_skipped_report,
    do_hcp_options_check,
    merge_report,
)
from qx_utilities.hcp.hcp_utils import (
    execute_hcp_multi_dedrift_and_resample,
    execute_hcp_single_dedrift_and_resample,
)


def hcp_dedrift_and_resample(sinfo, options, overwrite=True, thread=0):
    """
    ``hcp_dedrift_and_resample [... processing options]``

    Run the DeDriftAndResample step of the HCP Pipeline.

    ..  qx_command:
        type: processing.session

    Warning:
        The code expects the input images to be named and present in the QuNex
        folder structure. The function will look into folder::

            <session id>/hcp/<session id>

        for files::

            MNINonLinear/Results/<boldname>/
            <boldname>_<hcp_cifti_tail>_hp<hcp_highpass>_clean.dtseries.nii

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging  data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_icafix_bolds (str, default ''):
            List of bolds on which ICAFix was applied, with the same format
            as for ICAFix. Typically, this should be identical to the list
            used in the ICAFix run. If multi-run ICAFix was run with two or
            more groups then HCP MSMAll will be executed over the first
            specified group (and the scans listed for hcp_msmall_bolds must
            be limited to scans in the first concatenation group as well).
            If not provided MSMAll will assume multi-run ICAFix was executed
            with all bolds bundled together in a single concatenation called
            fMRI_CONCAT_ALL (i.e., same default behavior as in ICAFix).

        --hcp_resample_concatregname (str, default 'MSMAll'):
            Output name of the dedrifted registration.

        --hcp_resample_regname (str, default '<hcp_msmall_outregname>_2_d40_WRN'):
            Registration sphere name.

        --hcp_icafix_highpass (int, default detailed below):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix. Should be identical to the value
            used for ICAFix.

        --hcp_hiresmesh (int, default 164):
            High resolution mesh node count.

        --hcp_lowresmeshes (str, default 32):
            Low resolution meshes node count. To provide more values separate
            them with commas.

        --hcp_resample_reg_files (str, default detailed below):
            Comma separated paths to the spheres output from the
            MSMRemoveGroupDrift pipeline [<HCPPIPEDIR>/global/templates/MSMAll/<file1>,
            <HCPPIPEDIR>/global/templates/MSMAll/<file2>].
            Where <file1> is equal to:
            DeDriftingGroup.L.sphere.DeDriftMSMAll.
            164k_fs_LR.surf.gii and <file2> is equal
            to DeDriftingGroup.R.sphere.DeDriftMSMAll.
            164k_fs_LR.surf.gii

        --hcp_resample_maps (str, default 'sulc,curvature,corrThickness,thickness'):
            Comma separated paths to maps that will have the MSMAll registration
            applied that are not myelin maps.

        --hcp_resample_myelinmaps (str, default 'MyelinMap,SmoothedMyelinMap'):
            Comma separated paths to myelin maps.

        --hcp_bold_smoothFWHM (str, default '2'):
            Smoothing FWHM that matches what was used in the fMRISurface
            pipeline.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_icafix_domotionreg (bool, default detailed below):
            Whether to regress motion parameters as part of the cleaning. The
            default value after a single-run HCP ICAFix is [TRUE], while the
            default after a multi-run HCP ICAFix is [FALSE].

        --hcp_resample_dontfixnames (str, default 'NONE'):
            A list of comma separated bolds that will not have HCP ICAFix
            reapplied to them. Only applicable if single-run ICAFix was used.
            Generally not recommended.

        --hcp_resample_inregname (str, default 'NONE'):
            A string to enable multiple fMRI resolutions (e.g._1.6mm).

        --hcp_resample_use_ind_mean (str, default 'YES'):
            Whether to use the mean of the individual myelin map as the group
            reference map's mean.

        --hcp_resample_extractnames (str, default 'NONE'):
            List of bolds and concat names provided in the same format as the
            hcp_icafix_bolds parameter. Defines which bolds to extract. Exists
            to enable extraction of a subset of the runs in a multi-run HCP
            ICAFix group into a new concatenated series.

        --hcp_resample_extractextraregnames (str, default 'NONE'):
            Extract multi-run HCP ICAFix runs for additional surface
            registrations, often MSMSulc

        --hcp_resample_extractvolume (str, default 'NONE'):
            Whether to also extract the specified multi-run HCP ICAFix from the
            volume data, requires hcp_resample_extractnames to work.

        --hcp_msmall_templates (str, default <HCPPIPEDIR>/global/templates/MSMAll):
            Path to directory containing MSMAll template files.

        --hcp_msmall_myelin_target (str, default 'Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii'):
            Myelin map target, will use
            Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii
            by default.

    Output files:
        The results of this step will be populated in the MNINonLinear
        folder inside the same session's root hcp folder.

    Notes:
        Mapping of QuNex parameters onto HCP Pipelines parameters:
            Below is a detailed specification about how QuNex parameters are
            mapped onto the HCP Pipelines parameters.

        hcp_dedrift_and_resample parameter mapping:

            ===================================== =======================================
            QuNex parameter                       HCPpipelines parameter
            ===================================== =======================================
            ``hcp_resample_concatregname``        ``concat-reg-name``
            ``hcp_resample_regname``              ``registration-name``
            ``hcp_icafix_highpass``               ``high-pass``
            ``hcp_hiresmesh``                     ``high-res-mesh``
            ``hcp_lowresmeshes``                  ``low-res-meshes``
            ``hcp_resample_reg_files``            ``dedrift-reg-files``
            ``hcp_resample_maps``                 ``maps``
            ``hcp_resample_myelinmaps``           ``myelin-maps``
            ``hcp_bold_smoothFWHM``               ``smoothing-fwhm``
            ``hcp_matlab_mode``                   ``matlab-run-mode``
            ``hcp_icafix_domotionreg``            ``motion-regression``
            ``hcp_msmall_myelin_target``          ``myelin-target-file``
            ``hcp_resample_dontfixnames``         ``dont-fix-names``
            ``hcp_resample_inregname``            ``input-reg-name``
            ``hcp_resample_extractnames``         ``multirun-fix-extract-names``
            ``hcp_resample_extractnames``         ``multirun-fix-extract-concat-names``
            ``hcp_resample_extractextraregnames`` ``multirun-fix-extract-extra-regnames``
            ``hcp_resample_extractvolume``        ``multirun-fix-extract-volume``
            ``hcp_resample_use_ind_mean``         ``use-ind-mean``
            ===================================== =======================================

    Examples:
        HCP DeDriftAndResample after application of single-run ICAFix::

            qunex hcp_dedrift_and_resample \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_icafix_bolds="REST_1,REST_2,TASK_1,TASK_2" \\
                --hcp_matlab_mode="interpreted"

        HCP DeDriftAndResample after application of multi-run ICAFix::

            qunex hcp_dedrift_and_resample \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_icafix_bolds="GROUP_1:REST_1,REST_2,TASK_1|GROUP_2:REST_3,TASK_2" \\
                --hcp_matlab_mode="interpreted"
    """

    log = SessionLog(sinfo, options, "HCP DeDriftAndResample pipeline")

    run = True
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # --- Base settings
        pc.do_options_check(options, sinfo, "hcp_dedrift_and_resample")
        do_hcp_options_check(options, "hcp_dedrift_and_resample")
        hcp = get_hcp_paths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report["boldskipped"] = log.use_or_skip_bold(sinfo, options)
        _build_skipped_report(report, bskip, options)

        # --- Parse msmall_bolds
        single_run, _, dedrift_groups, pars_ok = parse_icafix_bolds(options, bolds, log, True)

        if not pars_ok:
            raise ge.CommandFailed(
                "hcp_dedrift_and_resample", "... invalid input parameters!"
            )

        # --- Execute
        parelements = max(1, min(options["parelements"], len(dedrift_groups)))
        ppe = ProcessPoolExecutor(parelements)
        # single-run
        if single_run:
            f = partial(execute_hcp_single_dedrift_and_resample, sinfo, options, hcp, run)
        # multi-run
        else:
            f = partial(execute_hcp_multi_dedrift_and_resample, sinfo, options, hcp, run)
        results = ppe.map(f, dedrift_groups)

        # merge r and report, this command runs DeDriftAndResample as its only
        # stage, so the entries need no stage name
        for result in results:
            log.raw(result["r"])
            merge_report(report, result["report"])

        # report
        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP DeDriftAndResample: " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except ge.CommandFailed as e:
        log.command_failed(e)
        report = (sinfo["id"], "HCP DeDriftAndResample failed", 1)
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.capture(str(errormessage))
        report = (sinfo["id"], "HCP DeDriftAndResample failed", 1)
    except Exception:
        log.unknown_error()
        report = (sinfo["id"], "HCP DeDriftAndResample failed", 1)

    log.close(pipeline="HCP DeDriftAndResample")

    return log.result(report)
