#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_long_msmall.py``

The longitudinal HCP MSMAll pipeline.
"""

import concurrent.futures
import os
import os.path
import traceback
from concurrent.futures import ProcessPoolExecutor

import qx_utilities.general.exceptions as ge
import qx_utilities.general.folders as gf
import qx_utilities.processing.core as pc
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    parse_msmall_bolds,
    _build_skipped_report,
    _check_hcp_info,
    do_hcp_options_check,
)
from qx_utilities.hcp.hcp_utils import execute_hcp_multi_dedrift_and_resample


# TODO: take care of per session bold specification
def hcp_long_msmall(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_long_msmall [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run the HCP Longitudinal MSMAll Pipeline
    (MSMAllPipeline.sh with the longitudinal setup).

    ..  qx_command:
        type: processing.subject
        aliases: hcp_lmsm

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

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --hcp_icafix_bolds (str, default ''):
            List of bolds on which ICAFix was applied, with the same format
            as for ICAFix. Typically, this should be identical to the list
            used in the ICAFix run. The bolds have to be in multi-run ICAFix
            groups: a list without groups (single-run ICAFix) stops the
            command with an error. If multi-run ICAFix was run with two or
            more groups then HCP MSMAll and DeDriftAndResample are executed
            for every group, in the order listed, and each group replaces
            the MSMAll outputs of the group before it (see the notes below).
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

        --hcp_resample_regname (str, default '<hcp_msmall_outregname>_2_d40_WRN'):
            The MSMAll registration DeDriftAndResample applies. By default
            the one this MSMAll run computes, named as MSMAll names it:
            <hcp_msmall_outregname>_<number of iteration modes>_d<ica dim>_<method>.
            hcp_long_msmall runs MSMAll with its default iteration modes
            (CA_CAT), ICA dimension (40) and method (WRN), whatever
            hcp_msmall_iteration_modes, hcp_msmall_ica_dim and
            hcp_msmall_method say, so the name is
            <hcp_msmall_outregname>_2_d40_WRN. Set it only to apply another
            registration.

        --hcp_hiresmesh (int, default 164):
            High resolution mesh node count.

        --hcp_lowresmesh (str, default '32'):
            Low resolution mesh node count.

        --hcp_regname (str, default 'MSMSulc'):
            Input registration name.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_msmall_procstring (str, default <hcp_cifti_tail>_hp<hcp_highpass>_clean):
            Identification for FIX cleaned dtseries to use.

        --hcp_msmall_myelin_target (str, default 'Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii'):
            Myelin map target, will use
            Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii
            by default.

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folders of the subject's longitudinal folder,
        <studyfolder>/subjects/<subject id>: in <subject id>.long.<template>
        for the template and in <session id>.long.<template> for each
        session.

    Notes:
        Runs the longitudinal MSMAll step of the HCP Pipeline. This function
        executes two steps, it first runs longitudinal MSMAll and if it
        completes successfully it then executes the DeDriftAndResample step.

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

        If hcp_icafix_bolds names two or more multi-run ICAFix groups, the
        groups are processed one after the other, in the order in which
        they are listed. For each group, MSMAll is executed on the bolds of
        the group that hcp_msmall_bolds selects (on all bolds of the group
        if hcp_msmall_bolds is not provided) and, if it completes
        successfully, DeDriftAndResample applies the registration named by
        hcp_resample_regname, by default the resulting one, to the bolds of
        the group in every session, and to the template.
        All groups write the same MSMAll outputs, named by
        hcp_msmall_outfmriname and hcp_msmall_outregname, so each group
        replaces the outputs of the group before it: the bolds of each
        group are resampled with the registration computed from that group
        (unless hcp_resample_regname names another), while the registration
        and the maps that remain are those of the last group. As in
        hcp_msmall, every entry of hcp_msmall_bolds has to name a bold of
        every group, and each bold belongs in one group only, so with
        several groups only bold tags that every group carries can be used. To compute the registration
        from the bolds of one group only, list just that group in
        hcp_icafix_bolds, as it was given to hcp_icafix; the bolds of the
        other groups are then not resampled.

        hcp_msmall parameter mapping:

            ============================= ============================
            QuNex parameter               HCPpipelines parameter
            ============================= ============================
            ``hcp_msmall_outfmriname``    ``output-fmri-name``
            ``hcp_icafix_highpass``       ``high-pass``
            ``hcp_msmall_templates``      ``msm-all-templates``
            ``hcp_msmall_outregname``     ``output-registration-name``
            ``hcp_hiresmesh``             ``high-res-mesh``
            ``hcp_lowresmesh``            ``low-res-mesh``
            ``hcp_regname``               ``input-registration-name``
            ``hcp_matlab_mode``           ``matlab-run-mode``
            ``hcp_msmall_procstring``     ``fmri-proc-string``
            ``hcp_longitudinal_template`` ``longitudinal-template``
            ``hcp_msmall_myelin_target``  ``myelin-target-file``
            ============================= ============================

    Examples:
        ::

            qunex hcp_long_msmall \\
                --studyfolder="<path_to_study_folder>" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_icafix_bolds="GROUP_1:REST_1,REST_2,TASK_1,TASK_2" \\
                --hcp_msmall_bolds="REST_1,REST_2" \\
                --hcp_longitudinal_template="<template_id>"
    """

    subject_id = sinfo[0]["subject"]

    log = SessionLog({"id": subject_id}, options, "HCP Longitudinal MSMAll Pipeline", label="Subject")

    run = True
    report = {"done": [], "failed": [], "skipped": [], "ready": [], "not ready": []}
    failed = 0

    try:
        # checks
        pc.do_options_check(options, sinfo[0], "hcp_long_msmall")
        do_hcp_options_check(options, "hcp_long_msmall")
        hcp = _check_hcp_info(sinfo, options)

        sessions_long = []
        for session in sinfo.get_list_by_key("id", sep=None):
            sessions_long.append(f"{session}{options['hcp_suffix']}")

        # --- Get sorted bold numbers and bold data
        #
        # WARNING: Only BOLDS from the first session are identified!
        bolds, bskip, report["boldskipped"] = pc.use_or_skip_bold(sinfo[0], options, _log=log)
        _build_skipped_report(report, bskip, options)

        # --- Parse msmall_bolds
        msmall_groups, single_run, pars_ok = parse_msmall_bolds(options, bolds, log)

        # the longitudinal pipeline runs on a multi-run ICAFix concatenation
        if single_run:
            log.error(
                "hcp_long_msmall needs multi-run ICAFix bolds: name their "
                "concatenation in hcp_icafix_bolds (<group>:<bold>,<bold>), or "
                "leave it unset for fMRI_CONCAT_ALL!"
            )
            pars_ok = False

        if not pars_ok:
            raise ge.CommandFailed("hcp_long_msmall", "... invalid input parameters!")

        if run:
            for group in msmall_groups:
                # named before anything can fail, the handlers report it
                groupname = group["name"]
                try:
                    # get group data
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
                    fmriprocstring = "%s_hp%s_clean" % (
                        "_Atlas",
                        str(highpass),
                    )
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
                        groupimg = os.path.join(
                            hcp["hcp_nonlin"], "Results", groupname, groupica
                        )
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

                    # replace path
                    path = os.path.join(
                        gf.subjects_folder(options["studyfolder"]), subject_id
                    )

                    comm = (
                        '%(script)s \
                        --path="%(path)s" \
                        --session="%(subject)s" \
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
                        --matlab-run-mode="%(matlabrunmode)s" \
                        --subject-long="%(subject)s" \
                        --sessions-long="%(sessionslong)s" \
                        --template-long="%(templatelong)s" \
                        --is-longitudinal="TRUE"'
                        % {
                            "script": os.path.join(
                                hcp["hcp_base"], "MSMAll", "MSMAllPipeline.sh"
                            ),
                            "path": path,
                            "subject": subject_id,
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
                            "sessionslong": "@".join(sessions_long),
                            "templatelong": options["hcp_longitudinal_template"],
                        }
                    )

                    # -- Report command
                    if boldok:
                        log.pipeline_command(comm)

                    # -- Run
                    if run and boldok:
                        if options["run"] == "run":
                            _, _, msmall_failed = pc.run_external_for_file(
                                None,
                                comm,
                                "Running HCP MSMAll",
                                overwrite=True,
                                thread=subject_id,
                                remove=options["log"] == "remove",
                                task=options["command_ran"],
                                logfolder=options["comlogs"],
                                logtags=[options["logtag"], groupname],
                                full_test=None,
                                shell=True,
                                _log=log,
                            )

                            if msmall_failed:
                                report["failed"].append(
                                    f"msmall_{subject_id}_{groupname}"
                                )
                            else:
                                # run dedrift and resample across long timepoints
                                sinfo_long = sinfo[0].copy()
                                with ProcessPoolExecutor(
                                    options["parsessions"]
                                ) as executor:
                                    futures = {}
                                    for sl in sessions_long:
                                        sinfo_long_i = sinfo_long.copy()
                                        # fix path
                                        sinfo_long_i["hcp"] = path
                                        # fix id
                                        sinfo_long_i["id"] = (
                                            f"{sl}.long.{options['hcp_longitudinal_template']}"
                                        )
                                        # add step info
                                        sinfo_long_i["long"] = 1
                                        future = executor.submit(
                                            execute_hcp_multi_dedrift_and_resample,
                                            sinfo_long_i,
                                            options,
                                            hcp,
                                            run,
                                            group,
                                        )
                                        futures[future] = sl  # map future to sl
                                    for future in concurrent.futures.as_completed(
                                        futures
                                    ):
                                        sl = futures[
                                            future
                                        ]  # get the correct sl for this future
                                        result = future.result()
                                        log.raw(result["r"])
                                        report_dedrift = result["report"]
                                        if report_dedrift["failed"]:
                                            report["failed"].append(
                                                f"dedrift_{sl}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"
                                            )
                                        if report_dedrift["ready"]:
                                            report["ready"].append(
                                                f"dedrift_{sl}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"
                                            )
                                        if report_dedrift["not ready"]:
                                            report["not ready"].append(
                                                f"dedrift_{sl}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"
                                            )

                                # run dedrift and resample on the template
                                sinfo_template = sinfo[0].copy()
                                # fix path
                                sinfo_template["hcp"] = path
                                # fix id
                                sinfo_template["id"] = (
                                    f"{subject_id}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"
                                )
                                # add step info
                                sinfo_template["long"] = 2
                                result = execute_hcp_multi_dedrift_and_resample(
                                    sinfo_template, options, hcp, run, group
                                )
                                log.raw(result["r"])
                                report_dedrift = result["report"]
                                if report_dedrift["failed"]:
                                    report["failed"].append(
                                        f"dedrift_long_{subject_id}_{groupname}"
                                    )
                                if report_dedrift["ready"]:
                                    report["ready"].append(
                                        f"dedrift_long_{subject_id}_{groupname}"
                                    )
                                if report_dedrift["not ready"]:
                                    report["not ready"].append(
                                        f"dedrift_long_{subject_id}_{groupname}"
                                    )

                                if len(report["failed"]) == 0:
                                    report["done"].append(
                                        f"msmall_{subject_id}_{groupname}"
                                    )

                        # -- just checking
                        else:
                            _, _, check_failed = pc.check_run(
                                None,
                                None,
                                "HCP MSMAll " + f"{subject_id}_{groupname}",
                                overwrite=True,
                                _log=log,
                            )
                            if check_failed == 0:
                                log.step("HCP MSMAll can be run")
                                report["ready"].append(f"{subject_id}_{groupname}")
                            else:
                                log.step("HCP MSMAll would be skipped (check result)")
                                report["skipped"].append(f"{subject_id}_{groupname}")

                    else:
                        report["not ready"].append(f"{subject_id}_{groupname}")
                        if options["run"] == "run":
                            log.error("something missing, skipping this group!")
                        else:
                            log.error("something missing, this group would be skipped!")

                except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
                    log.raw(f"\n\n\n --- Failed during processing of group {f'{subject_id}_{groupname}'} with error:\n")
                    log.raw(str(errormessage))
                    report["failed"].append(f"{subject_id}_{groupname}")
                except Exception:
                    log.info(f" --- Failed during processing of group {f'{subject_id}_{groupname}'} with error:\n {traceback.format_exc()}\n")
                    report["failed"].append(f"{subject_id}_{groupname}")
        else:
            log.step("Subject cannot be processed.")
            report["not ready"].append(subject_id)

    except ge.CommandFailed as e:
        log.raw("\n" + ge.report_command_failed("hcp_long_msmall", e))
        report = "processing failed"
        failed = 1
    except ge.CommandError as e:
        log.raw("\n" + ge.report_command_error("hcp_long_msmall", e))
        report = "processing failed"
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        report = "Error"
        failed = 1
    except Exception:
        log.unknown_error()
        report = "Error"
        failed = 1

    log.close(pipeline="HCP Longitudinal MSMAll Preprocessing")

    # summarize the groups, unless the subject failed before reaching them
    if isinstance(report, dict):
        for check in ["failed", "not ready", "skipped"]:
            failed += len(report[check])

        report = ", ".join([
            f"{item}: {len(report[item])} [{', '.join(report[item])}]"
            for item in ["done", "ready", "skipped", "not ready", "failed"]
        ])

    return log.result((subject_id, report, failed))
