#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_icafix.py``

The HCP ICAFix pipeline and its single-run / multi-run executors.
"""

import os
import os.path
import traceback
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import nibabel as nib

import qx_utilities.general.exceptions as ge
import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog, SessionLog
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.hcp.hcp_utils import (
    _build_skipped_report,
    do_hcp_options_check,
    MATLAB_RUN_MODES,
    execute_hcp_post_fix,
    matlab_run_mode,
    matlab_run_mode_ok,
    merge_report,
    new_report,
    parse_icafix_bolds,
    stage_report,
)


def hcp_icafix(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_icafix [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run the ICAFix step of HCP Pipeline (hcp_fix_multi_run or hcp_fix).

    ..  qx_command:
        type: processing.session

    Warning:
        The code expects the input images to be named and present in the QuNex
        folder structure. The function will look into folder::

            <session id>/hcp/<session id>

        for files::

            MNINonLinear/Results/<boldname>/<boldname>.nii.gz

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
            How many elements (e.g. bolds) to run in parallel.

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

        --hcp_icafix_bolds (str, default ''):
            Specify a list of bolds for ICAFix. You should specify how to
            group/concatenate bolds together along with bolds, e.g.
            "<group1>:<boldname1>,<boldname2>|
            <group2>:<boldname3>,<boldname4>", in this case multi-run HCP
            ICAFix will be executed, which is the default. Instead of full bold
            names, you can also  use bold tags from the batch file. If this
            parameter is not provided ICAFix will bundle all bolds together and
            execute multi-run HCP ICAFix, the concatenated file will be named
            fMRI_CONCAT_ALL. Alternatively, you can specify a comma separated
            list of bolds without groups, e.g. "<boldname1>,<boldname2>", in
            this case single-run HCP ICAFix will be executed over specified
            bolds. This is a legacy option and not recommended. A tag names
            every bold that carries it, and a bold can be named once only:
            a bold named in two groups, or twice, whether by its name or by
            its tag, is an error. With groups, every entry needs a group
            name: "<group1>:<boldname1>|<boldname2>" is an error.

        --hcp_icafix_highpass (int, default detailed below):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default. For single-run HCP ICAFix the default
            is 'octave'.

        --hcp_icafix_domotionreg (str, default detailed below):
            Whether to regress motion parameters as part of the cleaning. The
            default value for single-run HCP ICAFix is [TRUE], while the
            default for multi-run HCP ICAFix is [FALSE].

        --hcp_icafix_model (str, default detailed below):
            Which model to use for classification. Can be one of the pre-trained
            models shipped with FSL or a custom model as `somefile.RData`,
            `somefile.pyfix_model`, or a pyfix built-in model without extension.
            You can provide a path to a file, a relative one taken from the
            study folder, or just a filename if the file is in the FSL
            training_files folder. [HCP_hp<high-pass>.RData] for
            single-run HCP ICAFix and [HCP_Style_Single_Multirun_Dedrift.RData]
            for multi-run HCP ICAFix.

        --hcp_icafix_threshold (int, default 10):
            ICAFix threshold that controls the sensitivity/specificity tradeoff.

        --hcp_icafix_deleteintermediates (str, default 'FALSE'):
            If True, deletes both the concatenated high-pass filtered and
            non-filtered timeseries files that are prerequisites to FIX
            cleaning.

        --hcp_icafix_fallbackthreshold (int, default 0):
            If greater than zero, reruns icadim on any run with a VN mean more
            than this amount greater than the minimum VN mean.

        --hcp_config (str, default ''):
            Path to the HCP config file where additional parameters can be
            specified. For hcp_icafix, these parameters are: volwisharts,
            ciftiwisharts and icadimmode.

        --hcp_icafix_postfix (str, default 'TRUE'):
            Whether to automatically run HCP PostFix if HCP ICAFix finishes
            successfully.

        --hcp_icafix_processingmode (str, default ''):
            HCPStyleData (default) or LegacyStyleData, controls whether
            --hcp_icadim_mode=fewtimepoints is allowed.

        --hcp_icafix_icadim_mode (str, default 'default'):
            Choose how to run icaDim: "default" - start with a VN dimensionality
            of 1 and rerun until convergence "fewtimepoints" - start with a VN
            dimensionality of half the timepoints, do not iterate.

        --hcp_icafix_parallel_limit (int, default -1):
            How many melodic commands to run in parallel (local, not
            cluster-distributed) during individual projection and cleanup,
            defaults to all detected physical cores.

        --hcp_icafix_concatenate_only (flag, not set by default):
            When set, the script stops after the concatenation step,
            e.g., for use in experimental alternative multi-run denoising.
            PostFix is then not run, as there is no ICA output for it.

        --hcp_reuse_existing_ica (str, default 'FALSE'):
            Whether to execute only the FIX step of the pipeline and reuse the
            previous ICA results.

        --hcp_fix_backup (str, default ''):
            If provided, the previous FIX solution is backed up to the specified
            folder, in case hcp_reuse_existing_ica is used.

        --hcp_t1wtemplatebrain (str, default ''):
            Path to the T1w template brain used by pyfix. Not set by default,
            you can either set a path or set to "auto" to set as
            <HCPPIPEDIR>/global/templates/MNI152_T1_<RES>mm_brain.nii.gz.

        --hcp_ica_method (str, default 'MELODIC'):
            MELODIC or ICASSO. Use single-pass MELODIC (default) or multi-pass
            ICASSO consensus method for ICA.

        --hcp_legacy_fix (flag, not set by default):
            Whether to use the legacy MATLAB fix instead of the new pyfix.

        --hcp_vol_wisharts (int, default '2'):
            Number of wisharts to fit to volume data in icaDim.

        --hcp_cifti_wisharts (int, default '3'):
            Number of wisharts to fit to CIFTI data in icaDim.

        --hcp_icadim_mode (str, default 'default'):
            Choose how to run icaDim: "default" - start with a VN dimensionality
            of 1 and rerun until convergence "fewtimepoints" - start with a VN
            dimensionality of half the timepoints, do not iterate.

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folder inside the same session's root hcp folder.

        The final clean ICA file can be found in::

            MNINonLinear/Results/<boldname>/<boldname>_hp<highpass>_clean.nii.gz,

        where highpass is the used value for the highpass filter. The
        default highpass value is 0 for multi-run HCP ICAFix and 2000 for
        single-run HCP ICAFix.

    Notes:
        Runs the ICAFix step of HCP Pipeline (hcp_fix_multi_run or hcp_fix).
        This step attempts to auto-classify ICA components into good and bad
        components, so that the bad components can be then removed from the 4D
        FMRI data. If ICAFix step finishes successfully PostFix (PostFix.sh)
        step will execute  automatically, to disable this set the
        hcp_icafix_postfix to FALSE. A dry run (--test) reports the PostFix
        it would run after ICAFix as well.

        If the hcp_icafix_bolds parameter is not provided ICAFix will bundle
        all bolds together and execute multi-run HCP ICAFix, the
        concatenated file will be named fMRI_CONCAT_ALL. WARNING: if
        session has many bolds such processing requires a lot of
        computational resources.

        hcp_icafix parameter mapping:

            ================================== =======================
            QuNex parameter                    HCPpipelines parameter
            ================================== =======================
            ``hcp_icafix_highpass``            ``high-pass``
            ``hcp_icafix_domotionreg``         ``motion-regression``
            ``hcp_icafix_model``               ``training-file``
            ``hcp_icafix_threshold``           ``fix-threshold``
            ``hcp_icafix_deleteintermediates`` ``delete-intermediates``
            ``hcp_icafix_fallbackthreshold``   ``fallback-threshold``
            ``hcp_icafix_parallel_limit``      ``parallel-limit``
            ``hcp_config``                     ``config``
            ``hcp_icafix_processingmode``      ``processing-mode``
            ``hcp_icafix_icadim_mode``         ``icadim-mode``
            ``hcp_reuse_existing_ica``         ``reuse-existing-ica``
            ``hcp_fix_backup``                 ``fix-backup``
            ``hcp_matlab_mode``                ``matlabrunmode``
            ``hcp_t1wtemplatebrain``           ``T1wTemplateBrain``
            ``hcp_ica_method``                 ``ica-method``
            ``hcp_legacy_fix``                 ``enable-legacy-fix``
            ``hcp_icafix_concatenate_only``    ``concatenate-only``
            ``hcp_vol_wisharts``               ``vol-wisharts``
            ``hcp_cifti_wisharts``             ``cifti-wisharts``
            ``hcp_icadim_mode``                ``icadim-mode``
            ================================== =======================

    Examples:
        ::

            qunex hcp_icafix \\
                --batchfile=processing/batch.txt \\
                --studyfolder=.

        ::

            qunex hcp_icafix \\
                --batchfile=processing/batch.txt \\
                --studyfolder=. \\
                --hcp_icafix_bolds="GROUP_1:BOLD_1,BOLD_2|GROUP_2:BOLD_3,BOLD_4"
    """

    log = SessionLog(sinfo, options, "HCP ICAFix pipeline")

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
        pc.do_options_check(options, sinfo, "hcp_icafix")
        do_hcp_options_check(options, "hcp_icafix")
        hcp = get_hcp_paths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report["boldskipped"] = pc.use_or_skip_bold(sinfo, options, _log=log)
        _build_skipped_report(report, bskip, options)

        # --- Parse icafix_bolds
        single_fix, icafix_bolds, icafix_groups, pars_ok = parse_icafix_bolds(
            options, bolds, log
        )

        # --- Multi threading
        if single_fix:
            parelements = max(1, min(options["parelements"], len(icafix_bolds)))
        else:
            parelements = max(1, min(options["parelements"], len(icafix_groups)))
        log.blank()
        log.action(
            "Processing",
            f"{parelements} ICAFix elements in parallel",
            options["run"],
            level="info",
        )

        # matlab run mode, compiled=0, interpreted=1, octave=2. The executors
        # hand it to the pipelines on their command lines and never set it in
        # this process, where a session would pass it on to the next one.
        # Single-run HCP ICAFix defaults to octave
        if not matlab_run_mode_ok(
            options, log, default=MATLAB_RUN_MODES["octave"] if single_fix else None
        ):
            pars_ok = False

        if not pars_ok:
            raise ge.CommandFailed("hcp_icafix", "... invalid input parameters!")

        # --- Execute
        # single fix
        if single_fix:
            # create a multiprocessing Pool
            process_pool_executor = ProcessPoolExecutor(parelements)
            # process
            f = partial(execute_hcp_single_icafix, sinfo, options, overwrite, hcp, run)
            results = process_pool_executor.map(f, icafix_bolds)

            # merge r and report, the executor has already named the stages
            for result in results:
                log.raw(result["r"])
                merge_report(report, result["report"])

        # multi fix
        else:
            # create a multiprocessing Pool
            process_pool_executor = ProcessPoolExecutor(parelements)
            # process
            f = partial(execute_hcp_multi_icafix, sinfo, options, overwrite, hcp, run)
            results = process_pool_executor.map(f, icafix_groups)

            # merge r and report, the executor has already named the stages
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
            "HCP ICAFix: " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except ge.CommandFailed as e:
        log.command_failed(e)
        report = (sinfo["id"], "HCP ICAFix failed", 1)
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        report = (sinfo["id"], "HCP ICAFix failed", 1)
    except Exception:
        log.unknown_error()
        report = (sinfo["id"], "HCP ICAFix failed", 1)

    log.close(pipeline="HCP ICAFix")

    return log.result(report)


def _chain_post_fix(
    sinfo, options, hcp, run, single_fix, unit, matlabrunmode, report, _log
):
    """
    Run the PostFix chained to an ICAFix that succeeded, or -- in a dry run --
    that can be run, and say what it would run. Returns its report, or None
    when it is not chained (hcp_icafix_postfix off, ICAFix not through, or a
    multi-run ICAFix that only concatenates).

    The PostFix is handed the matlab run mode its ICAFix ran with.
    """
    if not options["hcp_icafix_postfix"]:
        return None
    if report["incomplete"] or report["failed"] or report["not ready"]:
        return None
    if not single_fix and options["hcp_icafix_concatenate_only"]:
        # hcp_fix_multi_run stops after the concatenation, before the ICA
        # PostFix reads, so a PostFix chained on could only report it missing
        _log.detail("PostFix not chained: --hcp_icafix_concatenate_only runs no ICA")
        return None

    result = execute_hcp_post_fix(
        sinfo, options, hcp, run, single_fix, unit,
        matlabrunmode=matlabrunmode, after_icafix=True,
    )
    _log.raw(result["r"])
    return result["report"]


def _single_run_model(model: str | None, bandpass) -> str:
    """
    The training data handed to single-run ``hcp_fix``: ``HCP_hp<bandpass>``
    by default, and a model that names a file from the current folder, the
    study, made absolute -- ``hcp_fix`` changes into the BOLD's folder before
    it looks for it, appending ``.RData`` when it is not there, and then in
    FIX's ``training_files``. A bare name of one of those is left as it is.
    The multi-run script makes it absolute itself.
    """
    if model is None:
        return f"HCP_hp{bandpass}.RData"
    if os.path.isabs(model):
        return model
    if os.path.isfile(model) or os.path.isfile(model + ".RData"):
        return os.path.abspath(model)
    return model


def execute_hcp_single_icafix(sinfo, options, overwrite, hcp, run, boldinfo):
    printbold, boldtarget, _ = pc.get_bold_names(boldinfo, options)

    # prepare return variables
    log = ReportLog()
    report = new_report()

    # PostFix is reported separately so the two stages can be told apart
    postfix_report = None

    try:
        log.rule(before=1)
        log.action("Processing", f"BOLD image {printbold}", options["run"])
        boldok = True

        # --- check for bold image
        boldimg = os.path.join(
            hcp["hcp_nonlin"], "Results", boldtarget, "%s.nii.gz" % (boldtarget)
        )
        boldok = pc.check_for_file(
            boldimg,
            f"bold image {boldtarget} present",
            f"bold image [{boldimg}] missing!",
            status=boldok,
            bad_level="error",
            _log=log,
        )

        # bold in input format
        inputfile = os.path.join(
            hcp["hcp_nonlin"], "Results", boldtarget, "%s" % (boldtarget)
        )

        # bandpass value
        if options["hcp_icafix_highpass"] is None:
            bandpass = 2000
        else:
            bandpass = options["hcp_icafix_highpass"]

        # delete intermediates
        icafix_threshold = 10
        if options["hcp_icafix_threshold"] is not None:
            icafix_threshold = options["hcp_icafix_threshold"]

        # delete intermediates
        delete_intermediates = "FALSE"
        if options["hcp_icafix_deleteintermediates"] is not None:
            delete_intermediates = options["hcp_icafix_deleteintermediates"]

        # the default for single fix is octave. hcp_fix takes no matlab
        # argument, it reads FSL_FIX_MATLAB_MODE through FIX's settings.sh, so
        # the mode is set for its call alone
        matlabrunmode = matlab_run_mode(options, default=MATLAB_RUN_MODES["octave"])

        comm = (
            'FSL_FIX_MATLAB_MODE=%(matlabrunmode)s %(script)s \
                "%(inputfile)s" \
                %(bandpass)s \
                "%(domot)s" \
                "%(trainingdata)s" \
                %(fixthreshold)s \
                "%(deleteintermediates)s"'
            % {
                "matlabrunmode": matlabrunmode,
                "script": os.path.join(hcp["hcp_base"], "ICAFIX", "hcp_fix"),
                "inputfile": inputfile,
                "bandpass": bandpass,
                "domot": (
                    "TRUE"
                    if options["hcp_icafix_domotionreg"] is None
                    else options["hcp_icafix_domotionreg"]
                ),
                "trainingdata": _single_run_model(
                    options["hcp_icafix_model"], bandpass
                ),
                "fixthreshold": icafix_threshold,
                "deleteintermediates": delete_intermediates,
            }
        )

        # -- Report command
        if boldok:
            log.pipeline_command(comm)

        # -- Run
        if run and boldok:
            if options["run"] == "run":
                _, _, failed = pc.run_external_for_file(
                    None,
                    comm,
                    "Running single-run HCP ICAFix",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], boldtarget],
                    full_test=None,
                    shell=True,
                    _log=log,
                )

                if failed:
                    report["failed"].append(printbold)
                else:
                    report["done"].append(printbold)

            # -- just checking: there is no file to check the run against, so
            #    a bold whose inputs are all present can be run
            else:
                log.step("single-run HCP ICAFix can be run")
                report["ready"].append(printbold)

            postfix_report = _chain_post_fix(
                sinfo, options, hcp, run, True, boldinfo, matlabrunmode, report, log
            )

        else:
            report["not ready"].append(printbold)
            if options["run"] == "run":
                log.error("something missing, skipping this BOLD!")
            else:
                log.error("something missing, this BOLD would be skipped!")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(f"\n\n\n --- Failed during processing of bold {printbold}\n")
        log.raw(str(errormessage))
        report["failed"].append(printbold)
    except Exception:
        log.info(
            f" --- Failed during processing of bold {printbold} with error:\n {traceback.format_exc()}\n"
        )
        report["failed"].append(printbold)

    # with PostFix chained on, both stages report against the same bold, so name
    # the stage each entry came from
    if options["hcp_icafix_postfix"]:
        stage_report(report, "ICAFix")
        if postfix_report is not None:
            merge_report(report, postfix_report, stage="PostFix")

    return {"r": log.text, "report": report}


def execute_hcp_multi_icafix(sinfo, options, overwrite, hcp, run, group):
    # get group data
    groupname = group["name"]
    bolds = group["bolds"]

    # prepare return variables
    log = ReportLog()
    report = new_report()

    # PostFix is reported separately so the two stages can be told apart
    postfix_report = None

    try:
        log.rule(before=1)
        log.action("Processing", f"group {groupname}", options["run"])
        groupok = True

        # --- check for bold images and prepare images parameter
        boldimgs = ""

        # check if files for all bolds exist
        for boldinfo in bolds:
            # set ok to true for now
            boldok = True

            _, boldtarget, _ = pc.get_bold_names(boldinfo, options)

            boldimg = os.path.join(
                hcp["hcp_nonlin"], "Results", boldtarget, "%s" % (boldtarget)
            )
            boldok = pc.check_for_file(
                f"{boldimg}.nii.gz",
                f"bold image {boldtarget} present",
                f"bold image [{boldimg}.nii.gz] missing!",
                status=boldok,
                bad_level="error",
                _log=log,
            )

            if not boldok:
                groupok = False
                break
            else:
                # add @ separator
                if boldimgs != "":
                    boldimgs = boldimgs + "@"

                # add latest image
                boldimgs = boldimgs + boldimg

        # construct concat file name
        concatfilename = os.path.join(
            hcp["hcp_nonlin"], "Results", groupname, groupname
        )

        # bandpass
        bandpass = (
            0
            if options["hcp_icafix_highpass"] is None
            else options["hcp_icafix_highpass"]
        )

        # matlab run mode, compiled=0, interpreted=1, octave=2: the one
        # hcp_matlab_mode names, else the environment's. Legacy FIX reads it
        # through FIX's settings.sh as well, so it is also set for the call
        matlabrunmode = matlab_run_mode(options)
        if not matlab_run_mode_ok(options, log):
            groupok = False

        comm = (
            'FSL_FIX_MATLAB_MODE=%(matlabrunmode)s %(script)s \
                --fmri-names="%(fmrinames)s" \
                --high-pass=%(bandpass)s \
                --concat-fmri-name="%(concatfilename)s" \
                --matlab-run-mode=%(matlabrunmode)s'
            % {
                "script": os.path.join(hcp["hcp_base"], "ICAFIX", "hcp_fix_multi_run"),
                "fmrinames": boldimgs,
                "bandpass": bandpass,
                "concatfilename": concatfilename,
                "matlabrunmode": matlabrunmode,
            }
        )

        # optional parameters
        if options["hcp_icafix_domotionreg"] is not None:
            comm += (
                '             --motion-regression="%s"'
                % options["hcp_icafix_domotionreg"]
            )

        if options["hcp_icafix_model"] is not None:
            comm += '             --training-file="%s"' % options["hcp_icafix_model"]

        if options["hcp_icafix_threshold"] is not None:
            comm += (
                '             --fix-threshold="%s"' % options["hcp_icafix_threshold"]
            )

        if options["hcp_icafix_deleteintermediates"] is not None:
            comm += (
                '             --delete-intermediates="%s"'
                % options["hcp_icafix_deleteintermediates"]
            )

        if options["hcp_icafix_fallbackthreshold"] is not None:
            comm += (
                '             --fallback-threshold="%s"'
                % options["hcp_icafix_fallbackthreshold"]
            )

        if options["hcp_icafix_parallel_limit"] is not None:
            comm += (
                '             --parallel-limit="%s"'
                % options["hcp_icafix_parallel_limit"]
            )

        if options["hcp_config"] is not None:
            comm += '             --config="%s"' % options["hcp_config"]

        if options["hcp_icafix_processingmode"] is not None:
            comm += (
                '             --processing-mode="%s"'
                % options["hcp_icafix_processingmode"]
            )

        if options["hcp_icafix_icadim_mode"] is not None:
            comm += (
                '             --icadim-mode="%s"' % options["hcp_icafix_icadim_mode"]
            )

        if options["hcp_reuse_existing_ica"] is not None:
            comm += (
                '             --reuse-existing-ica="%s"'
                % options["hcp_reuse_existing_ica"]
            )

        if options["hcp_fix_backup"] is not None:
            comm += '             --fix-backup="%s"' % options["hcp_fix_backup"]

        if (
            not options["hcp_legacy_fix"]
            and options["hcp_t1wtemplatebrain"] is not None
        ):
            if options["hcp_t1wtemplatebrain"] == "auto":
                if hcp["T1w"] is not None:
                    # try to set get the resolution automatically if not set yet
                    log.step(
                        "Trying to set the hcp_t1wtemplatebrain parameter automatically."
                    )

                    # place holder
                    resolution = None

                    # read nii header of hcp["T1w"]
                    t1w = hcp["T1w"].split("@")[0]
                    img = nib.load(t1w)
                    pixdim1, pixdim2, pixdim3 = img.header["pixdim"][1:4]

                    # do they match
                    epsilon = 0.05
                    if (
                        abs(pixdim1 - pixdim2) > epsilon
                        or abs(pixdim1 - pixdim3) > epsilon
                    ):
                        run = False
                        log.error(
                            f"T1w pixdim mismatch [{pixdim1, pixdim2, pixdim3}], please set hcp_t1wtemplatebrain manually!"
                        , depth=1)
                    else:
                        # upscale slightly and use the closest that matches
                        pixdim = pixdim1 * 1.05

                        if pixdim > 2:
                            run = False
                            log.error(
                                f"weird T1w pixdim found [{pixdim1, pixdim2, pixdim3}], please set the hcp_t1wtemplatebrain parameter manually!"
                            , depth=1)
                        elif pixdim > 1:
                            log.detail(
                                f"Based on T1w pixdim [{pixdim1, pixdim2, pixdim3}] the hcp_t1wtemplatebrain parameter was set to 1.0!"
                            )
                            resolution = 1.0
                        elif pixdim > 0.8:
                            log.detail(
                                f"Based on T1w pixdim [{pixdim1, pixdim2, pixdim3}] the hcp_t1wtemplatebrain parameter was set to 0.8!"
                            )
                            resolution = 0.8
                        elif pixdim > 0.65:
                            log.detail(
                                f"Based on T1w pixdim [{pixdim1, pixdim2, pixdim3}] the hcp_t1wtemplatebrain parameter was set to to 0.7!"
                            )
                            resolution = 0.7
                        else:
                            run = False
                            log.error(
                                f"weird T1w pixdim found [{pixdim1, pixdim2, pixdim3}], please set the hcp_t1wtemplatebrain parameter manually!"
                            , depth=1)

                    if resolution is not None:
                        t1wtemplatebrain = os.path.join(
                            hcp["hcp_base"],
                            "global",
                            "templates",
                            f"MNI152_T1_{resolution}mm_brain.nii.gz",
                        )
                        comm += (
                            '             --T1wTemplateBrain="%s"' % t1wtemplatebrain
                        )
            else:
                comm += (
                    '             --T1wTemplateBrain="%s"'
                    % options["hcp_t1wtemplatebrain"]
                )

        if options["hcp_ica_method"] is not None:
            comm += '             --ica-method="%s"' % options["hcp_ica_method"]

        if options["hcp_vol_wisharts"] is not None:
            comm += '             --vol-wisharts="%s"' % options["hcp_vol_wisharts"]

        if options["hcp_cifti_wisharts"] is not None:
            comm += '             --cifti-wisharts="%s"' % options["hcp_cifti_wisharts"]

        if options["hcp_icadim_mode"] is not None:
            comm += '             --icadim-mode="%s"' % options["hcp_icadim_mode"]

        if not options["hcp_legacy_fix"]:
            comm += '             --enable-legacy-fix="FALSE"'

        if options["hcp_icafix_concatenate_only"]:
            comm += '             --concatenate-only="TRUE"'

        # -- Report command
        if groupok:
            log.pipeline_command(comm)

        # -- Run
        if run and groupok:
            if options["run"] == "run":
                _, _, failed = pc.run_external_for_file(
                    None,
                    comm,
                    "Running multi-run HCP ICAFix",
                    overwrite=overwrite,
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

            # -- just checking: there is no file to check the run against, so
            #    a group whose inputs are all present can be run
            else:
                log.step("multi-run HCP ICAFix can be run")
                report["ready"].append(groupname)

            postfix_report = _chain_post_fix(
                sinfo, options, hcp, run, False, groupname, matlabrunmode, report, log
            )

        else:
            report["not ready"].append(groupname)
            if options["run"] == "run":
                log.error("images missing, skipping this group!")
            else:
                log.error("images missing, this group would be skipped!")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(
            f"\n\n\n --- Failed during processing of group {groupname} with error:\n"
        )
        log.raw(str(errormessage))
        report["failed"].append(groupname)
    except Exception:
        log.info(
            f" --- Failed during processing of group {groupname} with error:\n {traceback.format_exc()}\n"
        )
        report["failed"].append(groupname)

    # with PostFix chained on, both stages report against the same group, so name
    # the stage each entry came from
    if options["hcp_icafix_postfix"]:
        stage_report(report, "ICAFix")
        if postfix_report is not None:
            merge_report(report, postfix_report, stage="PostFix")

    return {"r": log.text, "report": report}
