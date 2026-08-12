#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_reapply_fix.py``

The HCP ReApplyFix pipeline, its single-run / multi-run executors and the
hand reclassification step.
"""

import os
import os.path
import traceback
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog, ReportLog
from qx_utilities.hcp.hcp_utils import (
    parse_icafix_bolds,
    _build_skipped_report,
    do_hcp_options_check,
)


def hcp_reapply_fix(sinfo, options, overwrite=True, thread=0):
    """
    ``hcp_reapply_fix [... processing options]``

    Run the ReApplyFix step of HCP Pipeline
    (ReApplyFixMultiRunPipeline.sh or ReApplyFixPipeline.sh).

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

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

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
            bolds. This is a legacy option and not recommended.

        --hcp_icafix_highpass (int, default detailed below):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_icafix_domotionreg (str, default detailed below):
            Whether to regress motion parameters as part of the cleaning. The
            default value for single-run HCP ICAFix is [TRUE], while the
            default for multi-run HCP ICAFix is [FALSE].

        --hcp_icafix_deleteintermediates (str, default 'FALSE'):
            If TRUE, deletes both the concatenated high-pass filtered and
            non-filtered timeseries files that are prerequisites to FIX
            cleaning.

        --hcp_icafix_regname (str, default 'NONE'):
            Specifies surface registration name. If 'NONE' MSMSulc will be used.

        --hcp_lowresmesh (str, default '32'):
            Specifies the low res mesh number.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --longitudinal:
            Set this flag if you are running the longitudinal variant of this
            command.

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folder inside the same sessions's root hcp folder.

        The final clean ICA file can be found in::

            MNINonLinear/Results/<boldname>/<boldname>_hp<highpass>_clean.nii.gz,

        where highpass is the used value for the highpass filter. The
        default highpass value is 0 for multi-run HCP ICAFix and 2000 for
        single-run HCP ICAFix.

    Notes:
        Runs the ReApplyFix step of HCP Pipeline. This function executes two
        steps, first it applies the hand reclassifications of noise and
        signal components from FIX (ApplyHandReClassifications.sh) using the
        ReclassifyAsNoise.txt and ReclassifyAsSignal.txt input files. Next it
        executes the HCP Pipeline's ReApplyFix or ReApplyFixMulti
        (ReApplyFixMultiRunPipeline.sh or ReApplyFixPipeline.sh).

        If the hcp_icafix_bolds parameter is not provided ICAFix will bundle
        all bolds together and execute multi-run HCP ICAFix, the
        concatenated file will be named fMRI_CONCAT_ALL. WARNING: if
        session has many bolds such processing requires a lot of
        computational resources.

        hcp_reapply_fix parameter mapping:

            ================================== =======================
            QuNex parameter                    HCPpipelines parameter
            ================================== =======================
            ``hcp_icafix_highpass``            ``high-pass``
            ``hcp_icafix_regname``             ``reg-name``
            ``hcp_lowresmesh``                 ``low-res-mesh``
            ``hcp_icafix_domotionreg``         ``motion-regression``
            ``hcp_icafix_deleteintermediates`` ``delete-intermediates``
            ``hcp_matlab_mode``                ``matlabrunmode``
            ``hcp_clean_substring``            ``clean-substring``
            ``hcp_config``                     ``config``
            ``hcp_icafix_processingmode``      ``processing-mode``
            ``hcp_icafix_icadim_mode``         ``icadim-mode``
            ``hcp_longitudinal_template``      ``longitudinal-template``
            ``longitudinal``                   ``is-longitudinal``
            ================================== =======================

    Examples:
        ::

            qunex hcp_reapply_fix \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_matlab_mode="interpreted"

        ::

            qunex hcp_reapply_fix \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_icafix_bolds="GROUP_1:BOLD_1,BOLD_2|GROUP_2:BOLD_3,BOLD_4" \\
                --hcp_matlab_mode="interpreted"
    """

    log = SessionLog(sinfo, options, "HCP ReApplyFix pipeline")

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
        pc.do_options_check(options, sinfo, "hcp_reapply_fix")
        do_hcp_options_check(options, "hcp_reapply_fix")
        hcp = get_hcp_paths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report["boldskipped"] = pc.use_or_skip_bold(sinfo, options, _log=log)
        _build_skipped_report(report, bskip, options)

        # --- Parse icafix_bolds
        single_fix, icafix_bolds, icafix_groups, pars_ok = parse_icafix_bolds(options, bolds, log)
        if not pars_ok:
            raise ge.CommandFailed("hcp_reapply_fix", "... invalid input parameters!")

        # --- Multi threading
        if single_fix:
            parelements = max(1, min(options["parelements"], len(icafix_bolds)))
        else:
            parelements = max(1, min(options["parelements"], len(icafix_groups)))
        log.blank()
        log.action(
            "Processing",
            f"{parelements} ReApplyFixes in parallel",
            options["run"],
            level="info",
        )

        # --- Execute
        # single fix
        if single_fix:
            # create a multiprocessing Pool
            process_pool_executor = ProcessPoolExecutor(parelements)
            # process
            f = partial(execute_hcp_single_reapply_fix, sinfo, options, hcp, run)
            results = process_pool_executor.map(f, icafix_bolds)

            # merge r and report
            for result in results:
                log.raw(result["r"])
                temp_report = result["report"]
                report["done"] += temp_report["done"]
                report["failed"] += temp_report["failed"]
                report["incomplete"] += temp_report["incomplete"]
                report["ready"] += temp_report["ready"]
                report["not ready"] += temp_report["not ready"]
                report["skipped"] += temp_report["skipped"]

        # multi fix
        else:
            # create a multiprocessing Pool
            process_pool_executor = ProcessPoolExecutor(parelements)
            # process
            f = partial(execute_hcp_multi_reapply_fix, sinfo, options, hcp, run)
            results = process_pool_executor.map(f, icafix_groups)

            # merge r and report
            for result in results:
                log.raw(result["r"])
                temp_report = result["report"]
                report["done"] += temp_report["done"]
                report["failed"] += temp_report["failed"]
                report["incomplete"] += temp_report["incomplete"]
                report["ready"] += temp_report["ready"]
                report["not ready"] += temp_report["not ready"]
                report["skipped"] += temp_report["skipped"]

        # report
        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP ReApplyFix: bolds " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except ge.CommandFailed as e:
        log.command_failed(e)
        report = (sinfo["id"], "HCP ReApplyFix failed", 1)
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        report = (sinfo["id"], "HCP ReApplyFix failed", 1)
    except Exception:
        log.unknown_error()
        report = (sinfo["id"], "HCP ReApplyFix failed", 1)

    log.close(pipeline="HCP ReApplyFix")

    return log.result(report)


def execute_hcp_single_reapply_fix(sinfo, options, hcp, run, boldinfo):

    printbold, boldtarget, _ = pc.get_bold_names(boldinfo, options)

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
        # run HCP hand reclassification
        log.raw("\n------------------------------------------------------------")
        log.step(f"Executing HCP Hand reclassification for bold: {printbold}\n")
        result = execute_hcp_hand_reclassification(
            sinfo, options, hcp, run, True, boldtarget, printbold
        )

        # merge r
        log.raw(result["r"])

        # move on to ReApplyFix
        rc_report = result["report"]
        if (
            rc_report["incomplete"] == []
            and rc_report["failed"] == []
            and rc_report["not ready"] == []
        ):
            boldok = True

            # highpass
            highpass = (
                2000
                if options["hcp_icafix_highpass"] is None
                else options["hcp_icafix_highpass"]
            )

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

            comm = (
                '%(script)s \
                --path="%(path)s" \
                --subject="%(subject)s" \
                --fmri-name="%(boldtarget)s" \
                --high-pass="%(highpass)s" \
                --reg-name="%(regname)s" \
                --low-res-mesh="%(lowresmesh)s" \
                --matlab-run-mode="%(matlabrunmode)s" \
                --motion-regression="%(motionregression)s" \
                --delete-intermediates="%(deleteintermediates)s"'
                % {
                    "script": os.path.join(
                        hcp["hcp_base"], "ICAFIX", "ReApplyFixPipeline.sh"
                    ),
                    "path": sinfo["hcp"],
                    "subject": sinfo["id"] + options["hcp_suffix"],
                    "boldtarget": boldtarget,
                    "highpass": highpass,
                    "regname": options["hcp_icafix_regname"],
                    "lowresmesh": options["hcp_lowresmesh"],
                    "matlabrunmode": matlabrunmode,
                    "motionregression": (
                        "TRUE"
                        if options["hcp_icafix_domotionreg"] is None
                        else options["hcp_icafix_domotionreg"]
                    ),
                    "deleteintermediates": options["hcp_icafix_deleteintermediates"],
                }
            )

            if options["hcp_clean_substring"] is not None:
                comm += (
                    '             --clean-substring="%s"'
                    % options["hcp_clean_substring"]
                )

            # -- Report command
            if boldok:
                log.raw("\n------------------------------------------------------------\n")
                log.raw("Running HCP Pipelines command via QuNex:\n\n")
                log.raw(comm.replace("--", "\n    --").replace("             ", ""))
                log.raw("\n------------------------------------------------------------\n")

            # -- Test files
            # postfix
            postfix = "%s%s_hp%s_clean.dtseries.nii" % (
                boldtarget,
                "_Atlas",
                highpass,
            )
            if (
                options["hcp_icafix_regname"] != "NONE"
                and options["hcp_icafix_regname"] != ""
            ):
                postfix = "%s%s_%s_hp%s_clean.dtseries.nii" % (
                    boldtarget,
                    "_Atlas",
                    options["hcp_icafix_regname"],
                    highpass,
                )

            tfile = os.path.join(hcp["hcp_nonlin"], "Results", boldtarget, postfix)
            full_test = None

            # -- Run
            if run and boldok:
                if options["run"] == "run":
                    _, _, failed = pc.run_external_for_file(
                        tfile,
                        comm,
                        "Running single-run HCP ReApplyFix",
                        overwrite=True,
                        thread=sinfo["id"],
                        remove=options["log"] == "remove",
                        task=options["command_ran"],
                        logfolder=options["comlogs"],
                        logtags=[options["logtag"], boldtarget],
                        full_test=full_test,
                        shell=True,
                        _log=log,
                    )

                    if failed:
                        report["failed"].append(printbold)
                    else:
                        report["done"].append(printbold)

                # -- just checking
                else:
                    passed, _, failed = pc.check_run(
                        tfile, full_test, "single-run HCP ReApplyFix " + boldtarget, _log=log
                    )
                    if passed is None:
                        log.step("single-run HCP ReApplyFix can be run")
                        report["ready"].append(printbold)
                    else:
                        report["skipped"].append(printbold)

            else:
                report["not ready"].append(printbold)
                if options["run"] == "run":
                    log.error("something missing, skipping this BOLD!")
                else:
                    log.error("something missing, this BOLD would be skipped!")
                # log beautify
                log.raw("\n\n")

        else:
            log.error(f"Hand reclassification failed for bold: {printbold}!")
            report["failed"].append(printbold)
            boldok = False

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(f"\n\n\n --- Failed during processing of bold {printbold} with error:\n")
        log.raw(str(errormessage))
        report["failed"].append(printbold)
    except Exception:
        log.info(f" --- Failed during processing of bold {printbold} with error:\n {traceback.format_exc()}\n")
        report["failed"].append(printbold)

    return {"r": log.text, "report": report}


def execute_hcp_multi_reapply_fix(sinfo, options, hcp, run, group):
    # get group data
    groupname = group["name"]
    bolds = group["bolds"]

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
        log.raw("\n------------------------------------------------------------")
        log.action("Processing", f"group {groupname}", options["run"])
        groupok = True

        # --- check for bold images and prepare images parameter
        boldtargets = ""

        # check if files for all bolds exist
        for boldinfo in bolds:
            # boldok
            boldok = True

            printbold, boldtarget, _ = pc.get_bold_names(boldinfo, options)

            boldimg = os.path.join(
                hcp["hcp_nonlin"], "Results", boldtarget, "%s.nii.gz" % (boldtarget)
            )
            boldok = pc.check_for_file(boldimg,
                f"bold image {boldtarget} present",
                f"bold image [{boldimg}] missing!",
                status=boldok,
                bad_level="error",
                _log=log,
            )

            if not boldok:
                groupok = False
                break
            else:
                # add @ separator
                if boldtargets != "":
                    boldtargets = boldtargets + "@"

                # add latest image
                boldtargets = boldtargets + boldtarget

        # run HCP hand reclassification if not longitudinal
        if not options["longitudinal"]:
            log.step(f"Executing HCP Hand reclassification for group: {groupname}\n")
            result = execute_hcp_hand_reclassification(
                sinfo, options, hcp, run, False, groupname, groupname
            )

            # merge r
            log.raw(result["r"])

            # check if hand reclassification was OK
            rc_report = result["report"]
        else:
            rc_report = report

        if (
            rc_report["incomplete"] == []
            and rc_report["failed"] == []
            and rc_report["not ready"] == []
        ):
            groupok = True

            # matlab run mode, compiled=0, interpreted=1, octave=2
            matlabrunmode = None
            if options["hcp_matlab_mode"] is None:
                if "FSL_FIX_MATLAB_MODE" not in os.environ:
                    log.error("hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n")
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
                    groupok = False

            # highpass
            highpass = (
                0
                if options["hcp_icafix_highpass"] is None
                else options["hcp_icafix_highpass"]
            )

            # path
            path = sinfo["hcp"]

            # longitudinal
            if options["longitudinal"]:
                studyfolder = gc.deduce_folders(options)["basefolder"]
                if not studyfolder:
                    log.error("cannot deduce the QuNex study folder from provided parameters! Please provide the sessionsfolder or the studyfolder parameter.")
                    groupok = False
                # replace path
                path = os.path.join(studyfolder, "subjects", sinfo["subject"])

            comm = (
                '%(script)s \
                --path="%(path)s" \
                --session="%(session)s" \
                --fmri-names="%(boldtargets)s" \
                --concat-fmri-name="%(groupname)s" \
                --high-pass="%(highpass)s" \
                --reg-name="%(regname)s" \
                --low-res-mesh="%(lowresmesh)s" \
                --matlab-run-mode="%(matlabrunmode)s"'
                % {
                    "script": os.path.join(
                        hcp["hcp_base"], "ICAFIX", "ReApplyFixMultiRunPipeline.sh"
                    ),
                    "path": path,
                    "session": sinfo["id"] + options["hcp_suffix"],
                    "boldtargets": boldtargets,
                    "groupname": groupname,
                    "highpass": highpass,
                    "regname": options["hcp_icafix_regname"],
                    "lowresmesh": options["hcp_lowresmesh"],
                    "matlabrunmode": matlabrunmode,
                }
            )

            if options["hcp_icafix_domotionreg"] is not None:
                comm += (
                    '             --motionregression="%s"'
                    % options["hcp_icafix_domotionreg"]
                )

            if options["hcp_icafix_deleteintermediates"] is not None:
                comm += (
                    '             --deleteintermediates="%s"'
                    % options["hcp_icafix_deleteintermediates"]
                )

            if options["hcp_icafix_processingmode"] is not None:
                comm += (
                    '             --processing-mode="%s"'
                    % options["hcp_icafix_processingmode"]
                )

            if options["hcp_icafix_icadim_mode"] is not None:
                comm += (
                    '             --icadim-mode="%s"'
                    % options["hcp_icafix_icadim_mode"]
                )

            if options["hcp_clean_substring"] is not None:
                comm += (
                    '             --clean-substring="%s"'
                    % options["hcp_clean_substring"]
                )

            if options["hcp_config"] is not None:
                comm += '             --config="%s"' % options["hcp_config"]

            # -- Longitudinal parameters
            if options["longitudinal"]:
                comm += "                --is-longitudinal=1"
                comm += (
                    "                --longitudinal-session="
                    + f"{sinfo['id']}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"
                )

            # -- Report command
            if groupok:
                log.raw("\n------------------------------------------------------------\n")
                log.raw("Running HCP Pipelines command via QuNex:\n\n")
                log.raw(comm.replace("--", "\n    --").replace("             ", ""))
                log.raw("\n------------------------------------------------------------\n")

            # -- Test files
            # postfix
            postfix = "%s%s_hp%s_clean.dtseries.nii" % (
                groupname,
                "_Atlas",
                highpass,
            )
            if (
                options["hcp_icafix_regname"] != "NONE"
                and options["hcp_icafix_regname"] != ""
            ):
                postfix = "%s%s_%s_hp%s_clean.dtseries.nii" % (
                    groupname,
                    "_Atlas",
                    options["hcp_icafix_regname"],
                    highpass,
                )

            tfile = os.path.join(hcp["hcp_nonlin"], "Results", groupname, postfix)
            full_test = None

            # -- Run
            if run and groupok:
                if options["run"] == "run":
                    logtags = [options["logtag"], groupname]
                    if options["longitudinal"]:
                        logtags.append("long")

                    _, _, failed = pc.run_external_for_file(
                        tfile,
                        comm,
                        "Running multi-run HCP ReApplyFix",
                        overwrite=True,
                        thread=sinfo["id"],
                        remove=options["log"] == "remove",
                        task=options["command_ran"],
                        logfolder=options["comlogs"],
                        logtags=logtags,
                        full_test=full_test,
                        shell=True,
                        _log=log,
                    )

                    if failed:
                        report["failed"].append(groupname)
                    else:
                        report["done"].append(groupname)

                # -- just checking
                else:
                    passed, _, failed = pc.check_run(
                        tfile, full_test, "multi-run HCP ReApplyFix " + groupname, _log=log
                    )
                    if passed is None:
                        log.step("multi-run HCP ReApplyFix can be run")
                        report["ready"].append(groupname)
                    else:
                        report["skipped"].append(groupname)

            else:
                report["not ready"].append(groupname)
                if options["run"] == "run":
                    log.error("something missing, skipping this group!")
                else:
                    log.error("something missing, this group would be skipped!")
                # log beautify
                log.raw("\n\n")

        else:
            log.error(f"Hand reclassification failed for bold: {printbold}!")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(f"\n\n\n --- Failed during processing of group {groupname} with error:\n")
        log.raw(str(errormessage))
        report["failed"].append(groupname)
    except Exception:
        log.info(f" --- Failed during processing of group {groupname} with error:\n {traceback.format_exc()}\n")
        report["failed"].append(groupname)

    return {"r": log.text, "report": report}


def execute_hcp_hand_reclassification(
    sinfo, options, hcp, run, single_fix, boldtarget, printbold
):
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
        log.action("Processing", f"ICA {printbold}", options["run"])
        boldok = True

        # load parameters or use default values
        if single_fix:
            highpass = (
                2000
                if options["hcp_icafix_highpass"] is None
                else options["hcp_icafix_highpass"]
            )
        else:
            highpass = (
                0
                if options["hcp_icafix_highpass"] is None
                else options["hcp_icafix_highpass"]
            )

        # --- check for bold image
        icaimg = os.path.join(
            hcp["hcp_nonlin"],
            "Results",
            boldtarget,
            "%s_hp%s_clean.nii.gz" % (boldtarget, highpass),
        )
        boldok = pc.check_for_file(icaimg,
            f"ICA {boldtarget} present",
            f"ICA [{icaimg}] missing!",
            status=boldok,
            bad_level="error",
            _log=log,
        )

        comm = (
            '%(script)s \
            --study-folder="%(studyfolder)s" \
            --subject="%(subject)s" \
            --fmri-name="%(boldtarget)s" \
            --high-pass="%(highpass)s"'
            % {
                "script": os.path.join(
                    hcp["hcp_base"], "ICAFIX", "ApplyHandReClassifications.sh"
                ),
                "studyfolder": sinfo["hcp"],
                "subject": sinfo["id"] + options["hcp_suffix"],
                "boldtarget": boldtarget,
                "highpass": highpass,
            }
        )

        # -- Report command
        if boldok:
            log.pipeline_command(comm)

        # -- Test files
        tfile = os.path.join(
            hcp["hcp_nonlin"],
            "Results",
            boldtarget,
            "%s_hp%s.ica" % (boldtarget, highpass),
            "HandNoise.txt",
        )
        full_test = None

        # -- Run
        if run and boldok:
            if options["run"] == "run":
                endlog, _, failed = pc.run_external_for_file(
                    tfile,
                    comm,
                    "Running HCP HandReclassification",
                    overwrite=True,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task="hcp_HandReclassification",
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], boldtarget],
                    full_test=full_test,
                    shell=True,
                    _log=log,
                )

                if failed:
                    report["failed"].append(printbold)
                else:
                    report["done"].append(printbold)

            # -- just checking
            else:
                passed, _, failed = pc.check_run(
                    tfile,
                    full_test,
                    "HCP HandReclassification " + boldtarget,
                    overwrite=True,
                    _log=log,
                )
                if passed is None:
                    log.step("HCP HandReclassification can be run")
                    report["ready"].append(printbold)
                else:
                    report["skipped"].append(printbold)

        else:
            report["not ready"].append(printbold)
            if options["run"] == "run":
                log.error("something missing, skipping this BOLD!")
            else:
                log.error("something missing, this BOLD would be skipped!")

        # log beautify
        log.raw("\n")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(f"\n\n\n --- Failed during processing of bold {printbold} with error:\n")
        log.raw(str(errormessage))
        report["failed"].append(printbold)
    except Exception:
        log.info(f" --- Failed during processing of bold {printbold} with error:\n {traceback.format_exc()}\n")
        report["failed"].append(printbold)

    return {"r": log.text, "report": report}
