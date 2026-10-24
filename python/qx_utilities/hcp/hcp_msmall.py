#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_msmall.py``

The HCP MSMAll pipeline and its single-run / multi-run executors.
"""

import os
import os.path
import traceback
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import qx_utilities.general.exceptions as ge
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog, ReportLog
from qx_utilities.hcp.hcp_utils import (
    parse_msmall_bolds,
    _build_skipped_report,
    do_hcp_options_check,
    merge_report,
)
from qx_utilities.hcp.hcp_utils import (
    execute_hcp_multi_dedrift_and_resample,
    execute_hcp_single_dedrift_and_resample,
)


def hcp_msmall(sinfo, options, overwrite=True, thread=0):
    """
    ``hcp_msmall [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run the MSMAll step of the HCP Pipeline (MSMAllPipeline.sh).

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

        --studyfolder (str):
            The path to the study folder. The sessions are in its `sessions`
            folder, unless --sessionsfolder names another one.

        --sessionsfolder (str, default '<studyfolder>/sessions'):
            The path to the folder with the sessions. Set it only when the
            sessions are not in the `sessions` folder of the study. With
            neither --studyfolder nor --sessionsfolder given, the current
            folder is used.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. msmall groups) to run in parallel.
            Every group writes the same MSMAll outputs, and the same
            dedrifted registration and resampled maps in DeDriftAndResample,
            so groups run in parallel write these files at the same time:
            keep it at 1 when hcp_icafix_bolds names two or more groups.

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
            more groups then HCP MSMAll is executed for every group, in the
            order listed, and each group replaces the outputs of the group
            before it, so the MSMAll registration that remains is the one
            computed from the last group (see the notes below).
            If not provided MSMAll will assume multi-run ICAFix was executed
            with all bolds bundled together in a single concatenation called
            fMRI_CONCAT_ALL (i.e., same default behavior as in ICAFix).

        --hcp_msmall_bolds (str, default detailed below):
            A comma separated list that defines the bolds that will be used
            in the computation of the MSMAll registration. Typically, this
            should be limited to resting-state scans. Specified bolds have
            to be a subset of bolds used from the hcp_icafix_bolds parameter
            [if not specified all bolds specified in hcp_icafix_bolds will
            be used, which is probably NOT what you want to do if
            hcp_icafix_bolds includes non-resting-state scans]. A bold can
            be given by its name, number or tag. With two or more multi-run
            ICAFix groups, every entry has to name a bold in each group, so,
            as each bold belongs in one group only, only tags that every
            group carries can be used (see the notes below).

        --hcp_icafix_highpass (int, default detailed below):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix. Should be identical to the value
            used for ICAFix.

        --hcp_msmall_outfmriname (str, default 'rfMRI_REST'):
            The name which will be given to the concatenation of scans specified
            by the hcp_msmall_bolds parameter.

        --hcp_msmall_templates (str, default <HCPPIPEDIR>/global/templates/MSMAll):
            Path to directory containing MSMAll template files.

        --hcp_msmall_outregname (str, default 'MSMAll_InitialReg'):
            Output registration name.

        --hcp_hiresmesh (int, default 164):
            High resolution mesh node count.

        --hcp_lowresmesh (str, default '32'):
            Low resolution mesh node count.

        --hcp_regname (str, default 'MSMSulc'):
            Input registration name.

        --hcp_matlab_mode (str, default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_msmall_procstring (str, default <hcp_cifti_tail>_hp<hcp_highpass>_clean):
            Identification for FIX cleaned dtseries to use.

        --hcp_msmall_resample (str, default 'TRUE'):
            Whether to automatically run HCP DeDriftAndResample if HCP MSMAll
            finishes successfully.

        --hcp_resample_regname (str, default detailed below):
            The MSMAll registration DeDriftAndResample applies. By default
            the one this MSMAll run computes, named as MSMAll names it:
            <hcp_msmall_outregname>_<number of iteration modes>_d<hcp_msmall_ica_dim>_<hcp_msmall_method>,
            where the number of iteration modes is the number of
            "_"-separated modes in hcp_msmall_iteration_modes, so
            'MSMAll_InitialReg_2_d40_WRN' with the default settings. Set it
            only to apply another registration.

        --hcp_msmall_myelin_target (str, default 'Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii'):
            Myelin map target, will use
            Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii
            by default.

        --hcp_msmall_module_name (str, default 'MSMAll.sh'):
            The name of script or code used to run registration.

        --hcp_msmall_iteration_modes (str, default 'CA_CAT'):
            Specifies what modalities:
                - C=RSN Connectivity,
                - A=Myelin Architecture,
                - T=RSN Topography.

            So, the default CA_CAT means one iteration using RSN Connectivity
            and Myelin Architecture, followed by another iteration using RSN
            Connectivity, Myelin Architecture, and RSN Topography.

        --hcp_msmall_method (str, default 'WRN'):
            Possible values: DR, DRZ, DRN, WR, WRZ, WRN.

        --hcp_msmall_use_migp (flag, not set by default):
            Whether to use MIGP (MELODIC's Incremental Group
            Component Analysis)

        --hcp_msmall_ica_dim (int, default 40):
            ICA (Independent Component Analysis) dimensions.

        --hcp_msmall_low_sica_dims (str, default '7@8@9@10@11@12@13@14@15@16@17@18@19@20@21'):
            The low sICA dimensionalities to use for determining weighting for
            individual projection.

        --hcp_msmall_vn (flag, not set by default):
            Whether to perform variance normalization.

        --hcp_msmall_reg_conf_path (str, 'MSMAllStrainFinalconf1to1_1to3'):
            Either the relative path where the registration configuration exists
            in MSMCONFIGDIR, or an absolute.

        --hcp_msmall_reg_vars (str, 'NONE'):
            The registration configure variables to override instead of using
            the configuration file. Please use quotes without space between
            parameters, e.g. 'REGNUMBER=1,REGPOWER=3'.

        --hcp_msmall_rsn_template (str, 'rfMRI_REST_Atlas_MSMAll_2_d41_WRN_DeDrift_hp2000_clean_PCA.ica_dREPLACEDIM_ROW_vn/melodic_oIC.dscalar.nii'):
            Alternate rsn template file, relative to the --msm-all-templates
            folder.

        --hcp_msmall_rsn_weights (str, 'rfMRI_REST_Atlas_MSMAll_2_d41_WRN_DeDrift_hp2000_clean_PCA.ica_dREPLACEDIM_ROW_vn/Weights.txt'):
            Alternate rsn weights file, relative to the --msm-all-templates
            folder.

        --hcp_msmall_topography_roi (str, 'Q1-Q6_RelatedParcellation210.atlas_Topographic_ROIs.32k_fs_LR.dscalar.nii'):
            Alternate topography roi file, relative to the --msm-all-templates
            folder.

        --hcp_msmall_topography_target (str, 'Q1-Q6_RelatedParcellation210.atlas_Topography.32k_fs_LR.dscalar.nii'):
            Alternate topography target, relative to the --msm-all-templates
            folder.

        --hcp_msmall_no_ind_mean (flag, not set by default):
            Whether not to use the mean of the individual myelin map as the
            group reference map's mean.

        --hcp_msmall_start_frame (int, 1):
            The starting frame to choose from each fMRI run (inclusive),
            only applied for single runs.

        --hcp_msmall_end_frame (int):
            The ending frame to choose from each fMRI run (inclusive),
            only applied for single runs.

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folder inside the same session's root hcp folder.

    Notes:
        Runs the MSMAll step of the HCP Pipeline. This function executes two
        steps, it first runs MSMAll and if it completes successfully it then
        executes the DeDriftAndResample step. To disable this automatic
        execution of DeDriftAndResample set hcp_msmall_resample to FALSE.

        The MSMAll step computes the MSMAll registration based on
        resting-state connectivity, resting-state topography, and myelin-map
        architecture. The DeDriftAndResample step applies the MSMAll
        registration to a specified set of maps and fMRI runs.

        MSMAll is intended for use with fMRI runs cleaned with hcp_icafix.
        Except for specialized/expert-user situations, the hcp_icafix_bolds
        parameter should be identical to what was used in hcp_icafix. If
        hcp_icafix_bolds is not provided MSMAll/DeDriftAndResample will
        assume multi-run ICAFix was executed with all bolds bundled
        together in a single concatenation called fMRI_CONCAT_ALL. (This is
        the default behavior if hcp_icafix_bolds parameter is not provided
        in the case of hcp_icafix).

        A key parameter in hcp_msmall is `hcp_msmall_bolds`, which controls
        the fMRI runs that enter into the computation of the MSMAll
        registration. Since MSMAll registration was designed to be computed
        from resting-state scans, this should be a list of the resting-state
        fMRI scans that you want to contribute to the computation of the
        MSMAll registration.

        However, it is perfectly fine to apply the MSMAll registration to
        task fMRI scans in the DeDriftAndResample step. The fMRI scans to
        which the MSMAll registration is applied are controlled by the
        `hcp_icafix_bolds` parameter, since typically one wants to apply the
        MSMAll registration to the same full set of fMRI scans that were
        cleaned using hcp_icafix.

        If hcp_icafix_bolds names two or more multi-run ICAFix groups,
        MSMAll is executed once for every group, in the order in which the
        groups are listed, on the bolds of the group that hcp_msmall_bolds
        selects (on all bolds of the group if hcp_msmall_bolds is not
        provided). All these runs write the same outputs, named by
        hcp_msmall_outfmriname and hcp_msmall_outregname, so each group
        replaces the outputs of the group before it, and the MSMAll
        registration that remains is the one computed from the last group.
        If MSMAll completes for every group, DeDriftAndResample is then
        executed once for every group and applies the registration named by
        hcp_resample_regname to the bolds of the group: by default the
        registration MSMAll computed, see hcp_resample_regname. With
        parelements above 1 the groups are run at the same time instead
        (see parelements).

        hcp_msmall_bolds is checked against every group, and the command
        stops with an error before anything is run if one of its entries
        does not name a bold of a group. Each bold belongs in one group
        only, so a bold given by its name or number names a bold of one
        group, and with several groups hcp_msmall_bolds can only list bold
        tags that every group carries. A bold named in two groups of
        hcp_icafix_bolds, by its name in one and by its tag in the other or
        by a tag repeated in both, stops the command with an error that
        names the bold and both groups. To compute the
        registration from the bolds of one group only, run hcp_msmall with
        hcp_icafix_bolds listing just that group, as it was given to
        hcp_icafix, and with hcp_msmall_resample set to FALSE, and then run
        hcp_dedrift_and_resample with all the groups (see the examples
        below).

        hcp_msmall parameter mapping:

            ================================ ===============================
            QuNex parameter                  HCPpipelines parameter
            ================================ ===============================
            ``hcp_msmall_outfmriname``       ``output-fmri-name``
            ``hcp_icafix_highpass``          ``high-pass``
            ``hcp_msmall_templates``         ``msm-all-templates``
            ``hcp_msmall_outregname``        ``output-registration-name``
            ``hcp_hiresmesh``                ``high-res-mesh``
            ``hcp_lowresmesh``               ``low-res-mesh``
            ``hcp_regname``                  ``input-registration-name``
            ``hcp_matlab_mode``              ``matlab-run-mode``
            ``hcp_msmall_procstring``        ``fmri-proc-string``
            ``hcp_msmall_myelin_target``     ``myelin-target-file``
            ``hcp_msmall_module_name``       ``module-name``
            ``hcp_msmall_iteration_modes``   ``iteration-modes``
            ``hcp_msmall_method``            ``method``
            ``hcp_msmall_use_migp``          ``use-migp``
            ``hcp_msmall_ica_dim``           ``ica-dim``
            ``hcp_msmall_low_sica_dims``     ``low-sica-dims``
            ``hcp_msmall_vn``                ``vn``
            ``hcp_msmall_reg_conf_path``     ``registration-configure-path``
            ``hcp_msmall_reg_vars``          ``registration-configure-override-variables``
            ``hcp_msmall_rsn_template``      ``rsn-template-file``
            ``hcp_msmall_rsn_weights``       ``rsn-weights-file``
            ``hcp_msmall_topography_roi``    ``topography-roi-file``
            ``hcp_msmall_topography_target`` ``topography-target-file``
            ``hcp_msmall_no_ind_mean``       ``use-ind-mean``
            ``hcp_msmall_start_frame``       ``start-frame``
            ``hcp_msmall_end_frame``         ``end-frame``
            ================================ ===============================

    Examples:
        HCP MSMAll after application of single-run ICAFix::

            qunex hcp_msmall \\
                --studyfolder=. \\
                --batchfile=processing/batch.txt \\
                --hcp_icafix_bolds="REST_1,REST_2,TASK_1,TASK_2" \\
                --hcp_msmall_bolds="REST_1,REST_2" \\
                --hcp_matlab_mode="interpreted"

        HCP MSMAll after application of multi-run ICAFix::

            qunex hcp_msmall \\
                --studyfolder=. \\
                --batchfile=processing/batch.txt \\
                --hcp_icafix_bolds="GROUP_1:REST_1,REST_2,TASK_1,TASK_2" \\
                --hcp_msmall_bolds="REST_1,REST_2" \\
                --hcp_matlab_mode="interpreted"

        HCP MSMAll computed from the first of two multi-run ICAFix groups,
        and applied to the bolds of both::

            qunex hcp_msmall \\
                --studyfolder=. \\
                --batchfile=processing/batch.txt \\
                --hcp_icafix_bolds="GROUP_1:REST_1,REST_2,TASK_1" \\
                --hcp_msmall_bolds="REST_1,REST_2" \\
                --hcp_msmall_resample=FALSE \\
                --hcp_matlab_mode="interpreted"

            qunex hcp_dedrift_and_resample \\
                --studyfolder=. \\
                --batchfile=processing/batch.txt \\
                --hcp_icafix_bolds="GROUP_1:REST_1,REST_2,TASK_1|GROUP_2:REST_3,TASK_2" \\
                --hcp_matlab_mode="interpreted"
    """

    log = SessionLog(sinfo, options, "HCP MSMAll pipeline")

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
        pc.do_options_check(options, sinfo, "hcp_msmall")
        do_hcp_options_check(options, "hcp_msmall")
        hcp = get_hcp_paths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report["boldskipped"] = pc.use_or_skip_bold(sinfo, options, _log=log)
        _build_skipped_report(report, bskip, options)

        # --- Parse msmall_bolds
        msmall_groups, single_run, pars_ok = parse_msmall_bolds(options, bolds, log)

        if not pars_ok:
            raise ge.CommandFailed("hcp_msmall", "... invalid input parameters!")

        # execute in parallel use parelements
        parelements = max(1, min(options["parelements"], len(msmall_groups)))

        if parelements > 1:
            log.blank()
            log.action(
                "Processing",
                f"{parelements} ICAFix groups in parallel",
                options["run"],
                level="info",
            )

        # --- Execute
        # create a multiprocessing Pool
        ppe = ProcessPoolExecutor(parelements)

        # --- Execute
        # single-run
        if single_run:
            f = partial(execute_hcp_single_msmall, sinfo, options, hcp, run)
        # multi-run
        else:
            f = partial(execute_hcp_multi_msmall, sinfo, options, hcp, run)
        results = ppe.map(f, msmall_groups)

        # with DeDriftAndResample chained on, both stages report against the same
        # units, so name the stage each entry came from
        msmall_stage = "MSMAll" if options["hcp_msmall_resample"] else None

        # merge r and report
        for result in results:
            log.raw(result["r"])
            merge_report(report, result["report"], stage=msmall_stage)

        # if all ok execute DeDriftAndResample if enabled
        if options["hcp_msmall_resample"]:
            if (
                report["incomplete"] == []
                and report["failed"] == []
                and report["not ready"] == []
            ):
                # single-run
                if single_run:
                    f = partial(
                        execute_hcp_single_dedrift_and_resample, sinfo, options, hcp, run
                    )
                # multi-run
                else:
                    f = partial(
                        execute_hcp_multi_dedrift_and_resample, sinfo, options, hcp, run
                    )
                results = ppe.map(f, msmall_groups)

                # merge r and report
                for result in results:
                    log.raw(result["r"])
                    merge_report(
                        report, result["report"], stage="DeDriftAndResample"
                    )

        # report
        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP MSMAll: bolds " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except ge.CommandFailed as e:
        log.command_failed(e)
        report = (sinfo["id"], "HCP MSMAll failed", 1)
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        report = (sinfo["id"], "HCP MSMAll failed", 1)
    except Exception:
        log.unknown_error()
        report = (sinfo["id"], "HCP MSMAll failed", 1)

    log.close(pipeline="HCP MSMAll")

    return log.result(report)


def execute_hcp_single_msmall(sinfo, options, hcp, run, group):
    # prepare return variables
    log = ReportLog()
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    # outfmriname, the name the run is reported under
    outfmriname = options["hcp_msmall_outfmriname"]

    try:
        # get data
        bolds = group["bolds"]

        # msmallBolds
        msmall_bolds = None
        if group["msmall_bolds"]:
            msmall_bolds = "@".join(group["msmall_bolds"])

        log.rule(before=1)
        log.action("Processing", f"MSMAll {outfmriname}", options["run"])
        boldsok = True

        # --- check for bold images and prepare targets parameter
        # highpass value
        highpass = (
            2000
            if options["hcp_icafix_highpass"] is None
            else options["hcp_icafix_highpass"]
        )

        # fmriprocstring
        fmriprocstring = "%s_hp%s_clean" % ("_Atlas", str(highpass))
        if options["hcp_msmall_procstring"] is not None:
            fmriprocstring = options["hcp_msmall_procstring"]

        # check if files for all bolds exist
        boldtargets = []
        for boldinfo in bolds:
            # set ok to true for now
            boldok = True

            _, boldtarget, _ = pc.get_bold_names(boldinfo, options)

            # input file check
            boldimg = os.path.join(
                hcp["hcp_nonlin"],
                "Results",
                boldtarget,
                "%s%s.dtseries.nii" % (boldtarget, fmriprocstring),
            )
            boldok = pc.check_for_file(boldimg,
                f"bold image {boldtarget} present",
                f"bold image [{boldimg}] missing!",
                status=boldok,
                bad_level="error",
                _log=log,
            )

            if not boldok:
                boldsok = False

            boldtargets.append(boldtarget)

        # if msmallBolds is not defined add all icafix bolds
        if msmall_bolds is None:
            msmall_bolds = "@".join(boldtargets)

        if options["hcp_msmall_templates"] is None:
            msmalltemplates = os.path.join(
                hcp["hcp_base"], "global", "templates", "MSMAll"
            )
        else:
            msmalltemplates = options["hcp_msmall_templates"]

        if options["hcp_msmall_myelin_target"] is None:
            myelintarget = os.path.join(
                msmalltemplates,
                "Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii",
            )
        else:
            myelintarget = options["hcp_msmall_myelin_target"]

        # matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                log.error("hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n")
                boldsok = False
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
                boldsok = False

        comm = (
            '%(script)s \
            --path="%(path)s" \
            --session="%(session)s" \
            --fmri-names-list="%(msmallBolds)s" \
            --multirun-fix-names="" \
            --multirun-fix-concat-name="" \
            --multirun-fix-names-to-use="" \
            --output-fmri-name="%(outfmriname)s" \
            --high-pass="%(highpass)s" \
            --fmri-proc-string="%(fmriprocstring)s" \
            --msm-all-templates="%(msmalltemplates)s" \
            --output-registration-name="%(outregname)s" \
            --high-res-mesh="%(highresmesh)s" \
            --low-res-mesh="%(lowresmesh)s" \
            --input-registration-name="%(inregname)s" \
            --myelin-target-file="%(myelintarget)s" \
            --matlab-run-mode="%(matlabrunmode)s"'
            % {
                "script": os.path.join(hcp["hcp_base"], "MSMAll", "MSMAllPipeline.sh"),
                "path": sinfo["hcp"],
                "session": sinfo["id"] + options["hcp_suffix"],
                "msmallBolds": msmall_bolds,
                "outfmriname": outfmriname,
                "highpass": highpass,
                "fmriprocstring": fmriprocstring,
                "msmalltemplates": msmalltemplates,
                "outregname": options["hcp_msmall_outregname"],
                "highresmesh": options["hcp_hiresmesh"],
                "lowresmesh": options["hcp_lowresmesh"],
                "inregname": options["hcp_regname"],
                "myelintarget": myelintarget,
                "matlabrunmode": matlabrunmode,
            }
        )

        # Optional parameters
        # hcp_msmall_module_name
        if options["hcp_msmall_module_name"] is not None:
            comm += "                --module-name=" + options["hcp_msmall_module_name"]

        # hcp_msmall_iteration_modes
        if options["hcp_msmall_iteration_modes"] is not None:
            comm += (
                "                --iteration-modes="
                + options["hcp_msmall_iteration_modes"]
            )

        # hcp_msmall_method
        if options["hcp_msmall_method"] is not None:
            comm += "                --method=" + options["hcp_msmall_method"]

        # hcp_msmall_use_migp
        if options["hcp_msmall_use_migp"]:
            comm += "                --use-migp=YES"

        # hcp_msmall_ica_dim
        if options["hcp_msmall_ica_dim"] is not None:
            comm += "                --ica-dim=" + options["hcp_msmall_ica_dim"]

        # hcp_msmall_low_sica_dims
        if options["hcp_msmall_low_sica_dims"] is not None:
            comm += (
                "                --low-sica-dims=" + options["hcp_msmall_low_sica_dims"]
            )

        # hcp_msmall_vn
        if options["hcp_msmall_vn"]:
            comm += "                --vn=YES"

        # hcp_msmall_reg_conf_path
        if options["hcp_msmall_reg_conf_path"] is not None:
            comm += (
                "                --registration-configure-path="
                + options["hcp_msmall_reg_conf_path"]
            )

        # hcp_msmall_reg_vars
        if options["hcp_msmall_reg_vars"] is not None:
            comm += (
                "                --registration-configure-override-variables="
                + options["hcp_msmall_reg_vars"]
            )

        # hcp_msmall_rsn_template
        if options["hcp_msmall_rsn_template"] is not None:
            comm += (
                "                --rsn-template-file="
                + options["hcp_msmall_rsn_template"]
            )

        # hcp_msmall_rsn_weights
        if options["hcp_msmall_rsn_weights"] is not None:
            comm += (
                "                --rsn-weights-file="
                + options["hcp_msmall_rsn_weights"]
            )

        # hcp_msmall_topography_roi
        if options["hcp_msmall_topography_roi"] is not None:
            comm += (
                "                --topography-roi-file="
                + options["hcp_msmall_topography_roi"]
            )

        # hcp_msmall_topography_target
        if options["hcp_msmall_topography_target"] is not None:
            comm += (
                "                --topography-target-file="
                + options["hcp_msmall_topography_target"]
            )

        # hcp_msmall_no_ind_mean
        if options["hcp_msmall_no_ind_mean"]:
            comm += "                --use-ind-mean=NO"

        # hcp_msmall_start_frame
        if options["hcp_msmall_start_frame"] is not None:
            comm += "                --start-frame=" + options["hcp_msmall_start_frame"]

        # hcp_msmall_end_frame
        if options["hcp_msmall_end_frame"] is not None:
            comm += "                --end-frame=" + options["hcp_msmall_end_frame"]

        # -- Report command
        if boldsok:
            log.pipeline_command(comm)

        # -- Run
        if run and boldsok:
            if options["run"] == "run":
                _, _, failed = pc.run_external_for_file(
                    None,
                    comm,
                    "Running HCP MSMAll",
                    overwrite=True,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], outfmriname],
                    full_test=None,
                    shell=True,
                    _log=log,
                )

                if failed:
                    report["failed"].append(outfmriname)
                else:
                    report["done"].append(outfmriname)

            # -- just checking
            else:
                # there is no file to check the run against, so one whose
                # inputs are all present can be run
                log.step("HCP MSMAll can be run")
                report["ready"].append(outfmriname)

        else:
            report["not ready"].append(outfmriname)
            if options["run"] == "run":
                log.error("something missing, skipping this BOLD!")
            else:
                log.error("something missing, this BOLD would be skipped!")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(f"\n\n\n --- Failed during processing of bolds {msmall_bolds}\n")
        log.raw(str(errormessage))
        report["failed"].append(outfmriname)
    except Exception:
        log.info(f" --- Failed during processing of bolds {msmall_bolds} with error:\n {traceback.format_exc()}\n")
        report["failed"].append(outfmriname)

    return {"r": log.text, "report": report}


def execute_hcp_multi_msmall(sinfo, options, hcp, run, group):
    # prepare return variables
    log = ReportLog()
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # get group data
        groupname = group["name"]
        bolds = group["bolds"]

        # outfmriname
        outfmriname = options["hcp_msmall_outfmriname"]

        log.rule(before=1)
        log.action("Processing", f"MSMAll {outfmriname}", options["run"])

        # --- check for bold images and prepare targets parameter
        boldtargets = ""

        # highpass
        highpass = (
            0
            if options["hcp_icafix_highpass"] is None
            else options["hcp_icafix_highpass"]
        )

        # fmriprocstring
        fmriprocstring = "%s_hp%s_clean" % ("_Atlas", str(highpass))
        if options["hcp_msmall_procstring"] is not None:
            fmriprocstring = options["hcp_msmall_procstring"]

        # check if files for all bolds exist
        for boldinfo in bolds:
            # set ok to true for now
            boldok = True

            _, boldtarget, _ = pc.get_bold_names(boldinfo, options)

            # input file check
            boldimg = os.path.join(
                hcp["hcp_nonlin"],
                "Results",
                boldtarget,
                "%s%s.dtseries.nii" % (boldtarget, fmriprocstring),
            )
            boldok = pc.check_for_file(boldimg,
                f"bold image {boldtarget} present",
                f"bold image [{boldimg}] missing!",
                status=boldok,
                bad_level="error",
                _log=log,
            )

            if not boldok:
                break
            else:
                # add @ separator
                if boldtargets != "":
                    boldtargets = boldtargets + "@"

                # add latest image
                boldtargets = boldtargets + boldtarget

        if boldok:
            # check if group file exists
            groupica = "%s_hp%s_clean.nii.gz" % (groupname, highpass)
            groupimg = os.path.join(hcp["hcp_nonlin"], "Results", groupname, groupica)
            boldok = pc.check_for_file(groupimg,
                f"ICA {groupname} present",
                f"ICA [{groupimg}] missing!",
                status=boldok,
                bad_level="error",
                _log=log,
            )

        if options["hcp_msmall_templates"] is None:
            msmalltemplates = os.path.join(
                hcp["hcp_base"], "global", "templates", "MSMAll"
            )
        else:
            msmalltemplates = options["hcp_msmall_templates"]

        if options["hcp_msmall_myelin_target"] is None:
            myelintarget = os.path.join(
                msmalltemplates,
                "Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii",
            )
        else:
            myelintarget = options["hcp_msmall_myelin_target"]

        # matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                log.error("hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n")
                boldok = False
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
                boldok = False

        # fix names to use
        fixnamestouse = "@".join(group["msmall_bolds"])

        comm = (
            '%(script)s \
            --path="%(path)s" \
            --session="%(session)s" \
            --fmri-names-list="" \
            --multirun-fix-names="%(fixnames)s" \
            --multirun-fix-concat-name="%(concatname)s" \
            --multirun-fix-names-to-use="%(fixnamestouse)s" \
            --output-fmri-name="%(outfmriname)s" \
            --high-pass="%(highpass)s" \
            --fmri-proc-string="%(fmriprocstring)s" \
            --msm-all-templates="%(msmalltemplates)s" \
            --output-registration-name="%(outregname)s" \
            --high-res-mesh="%(highresmesh)s" \
            --low-res-mesh="%(lowresmesh)s" \
            --input-registration-name="%(inregname)s" \
            --myelin-target-file="%(myelintarget)s" \
            --matlab-run-mode="%(matlabrunmode)s"'
            % {
                "script": os.path.join(hcp["hcp_base"], "MSMAll", "MSMAllPipeline.sh"),
                "path": sinfo["hcp"],
                "session": sinfo["id"] + options["hcp_suffix"],
                "fixnames": boldtargets,
                "concatname": groupname,
                "fixnamestouse": fixnamestouse,
                "outfmriname": outfmriname,
                "highpass": highpass,
                "fmriprocstring": fmriprocstring,
                "msmalltemplates": msmalltemplates,
                "outregname": options["hcp_msmall_outregname"],
                "highresmesh": options["hcp_hiresmesh"],
                "lowresmesh": options["hcp_lowresmesh"],
                "inregname": options["hcp_regname"],
                "myelintarget": myelintarget,
                "matlabrunmode": matlabrunmode,
            }
        )

        # Optional parameters
        # hcp_msmall_module_name
        if options["hcp_msmall_module_name"] is not None:
            comm += "                --module-name=" + options["hcp_msmall_module_name"]

        # hcp_msmall_iteration_modes
        if options["hcp_msmall_iteration_modes"] is not None:
            comm += (
                "                --iteration-modes="
                + options["hcp_msmall_iteration_modes"]
            )

        # hcp_msmall_method
        if options["hcp_msmall_method"] is not None:
            comm += "                --method=" + options["hcp_msmall_method"]

        # hcp_msmall_use_migp
        if options["hcp_msmall_use_migp"]:
            comm += "                --use-migp=YES"

        # hcp_msmall_ica_dim
        if options["hcp_msmall_ica_dim"] is not None:
            comm += "                --ica-dim=" + options["hcp_msmall_ica_dim"]

        # hcp_msmall_low_sica_dims
        if options["hcp_msmall_low_sica_dims"] is not None:
            comm += (
                "                --low-sica-dims=" + options["hcp_msmall_low_sica_dims"]
            )

        # hcp_msmall_vn
        if options["hcp_msmall_vn"]:
            comm += "                --vn=YES"

        # hcp_msmall_reg_conf_path
        if options["hcp_msmall_reg_conf_path"] is not None:
            comm += (
                "                --registration-configure-path="
                + options["hcp_msmall_reg_conf_path"]
            )

        # hcp_msmall_reg_vars
        if options["hcp_msmall_reg_vars"] is not None:
            comm += (
                "                --registration-configure-override-variables="
                + options["hcp_msmall_reg_vars"]
            )

        # hcp_msmall_rsn_template
        if options["hcp_msmall_rsn_template"] is not None:
            comm += (
                "                --rsn-template-file="
                + options["hcp_msmall_rsn_template"]
            )

        # hcp_msmall_rsn_weights
        if options["hcp_msmall_rsn_weights"] is not None:
            comm += (
                "                --rsn-weights-file="
                + options["hcp_msmall_rsn_weights"]
            )

        # hcp_msmall_topography_roi
        if options["hcp_msmall_topography_roi"] is not None:
            comm += (
                "                --topography-roi-file="
                + options["hcp_msmall_topography_roi"]
            )

        # hcp_msmall_topography_target
        if options["hcp_msmall_topography_target"] is not None:
            comm += (
                "                --topography-target-file="
                + options["hcp_msmall_topography_target"]
            )

        # hcp_msmall_no_ind_mean
        if options["hcp_msmall_no_ind_mean"]:
            comm += "                --use-ind-mean=NO"

        # -- Report command
        if boldok:
            log.pipeline_command(comm)

        # -- Run
        if run and boldok:
            if options["run"] == "run":
                _, _, failed = pc.run_external_for_file(
                    None,
                    comm,
                    "Running HCP MSMAll",
                    overwrite=True,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], groupname],
                    full_test=None,
                    shell=True,
                    _log=log,
                )

                if failed:
                    report["failed"].append(groupname)
                else:
                    report["done"].append(groupname)

            # -- just checking
            else:
                # there is no file to check the run against, so one whose
                # inputs are all present can be run
                log.step("HCP MSMAll can be run")
                report["ready"].append(groupname)

        else:
            report["not ready"].append(groupname)
            if options["run"] == "run":
                log.error("something missing, skipping this group!")
            else:
                log.error("something missing, this group would be skipped!")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(f"\n\n\n --- Failed during processing of group {groupname} with error:\n")
        log.raw(str(errormessage))
        report["failed"].append(groupname)
    except Exception:
        log.info(f" --- Failed during processing of group {groupname} with error:\n {traceback.format_exc()}\n")
        report["failed"].append(groupname)

    return {"r": log.text, "report": report}
