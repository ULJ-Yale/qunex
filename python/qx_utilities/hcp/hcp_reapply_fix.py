#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_reapply_fix.py``

The HCP ReApplyFix pipeline, its executor and the hand reclassification step.
"""

import os
import os.path
import traceback
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import qx_utilities.general.exceptions as ge
import qx_utilities.general.folders as gf
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog, ReportLog
from qx_utilities.hcp.hcp_utils import (
    parse_icafix_bolds,
    _build_skipped_report,
    do_hcp_options_check,
    matlab_run_mode,
    matlab_run_mode_ok,
)


def hcp_reapply_fix(sinfo, options, overwrite=True, thread=0):
    """
    ``hcp_reapply_fix [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run the ReApplyFix step of HCP Pipeline (ReApplyFixMultiRunPipeline.sh).

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

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_icafix_bolds (str, default ''):
            Specify how to group/concatenate the bolds for ICAFix, e.g.
            "<group1>:<boldname1>,<boldname2>|
            <group2>:<boldname3>,<boldname4>". Instead of full bold names, you
            can also use bold tags from the batch file. If this parameter is
            not provided ICAFix will bundle all bolds together, the
            concatenated file will be named fMRI_CONCAT_ALL. A tag names every
            bold that carries it, and a bold can be named once only: a bold
            named in two groups, or twice, whether by its name or by its tag,
            is an error. Every entry needs a group name: "<boldname1>,<boldname2>"
            and "<group1>:<boldname1>|<boldname2>" are errors.

        --hcp_icafix_highpass (int, default 0):
            Value for the highpass filter.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_icafix_domotionreg (str, default 'FALSE'):
            Whether to regress motion parameters as part of the cleaning.

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
        default highpass value is 0.

    Notes:
        Runs the ReApplyFix step of HCP Pipeline. This function executes two
        steps, first it applies the hand reclassifications of noise and
        signal components from FIX (ApplyHandReClassifications.sh) using the
        ReclassifyAsNoise.txt and ReclassifyAsSignal.txt input files. Next it
        executes the HCP Pipeline's ReApplyFix (ReApplyFixMultiRunPipeline.sh).

        If the hcp_icafix_bolds parameter is not provided ICAFix will bundle
        all bolds together, the
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
                --studyfolder=. \\
                --batchfile=processing/batch.txt \\
                --hcp_matlab_mode="interpreted"

        ::

            qunex hcp_reapply_fix \\
                --studyfolder=. \\
                --batchfile=processing/batch.txt \\
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
        icafix_groups, pars_ok = parse_icafix_bolds(options, bolds, log)
        if not pars_ok:
            raise ge.CommandFailed("hcp_reapply_fix", "... invalid input parameters!")

        # --- Multi threading
        parelements = max(1, min(options["parelements"], len(icafix_groups)))
        log.blank()
        log.action(
            "Processing",
            f"{parelements} ReApplyFixes in parallel",
            options["run"],
            level="info",
        )

        # --- Execute
        # create a multiprocessing Pool
        process_pool_executor = ProcessPoolExecutor(parelements)
        # process
        f = partial(execute_hcp_reapply_fix, sinfo, options, hcp, run)
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


def execute_hcp_reapply_fix(sinfo, options, hcp, run, group):
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
        log.rule()
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
                sinfo, options, hcp, run, groupname
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
            # matlab run mode, compiled=0, interpreted=1, octave=2
            matlabrunmode = matlab_run_mode(options)
            if not matlab_run_mode_ok(options, log):
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
                # replace path
                path = os.path.join(
                    gf.subjects_folder(options["studyfolder"]), sinfo["subject"]
                )
                long_session = f"{sinfo['id']}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"

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
                comm += "                --longitudinal-session=" + long_session

            # -- Report command
            if groupok:
                log.rule(after=1)
                log.raw("Running HCP Pipelines command via QuNex:\n\n")
                log.raw(comm.replace("--", "\n    --").replace("             ", ""))
                log.rule(after=1)

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
            # the longitudinal results are in the subject's longitudinal session
            if options["longitudinal"]:
                tfile = os.path.join(
                    path, long_session, "MNINonLinear", "Results", groupname, postfix
                )
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
                        "Running HCP ReApplyFix",
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
                        tfile, full_test, "HCP ReApplyFix " + groupname, _log=log
                    )
                    if passed is None:
                        log.step("HCP ReApplyFix can be run")
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
            log.error(f"Hand reclassification failed for group: {groupname}!")
            report["failed"].append(groupname)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(f"\n\n\n --- Failed during processing of group {groupname} with error:\n")
        log.raw(str(errormessage))
        report["failed"].append(groupname)
    except Exception:
        log.info(f" --- Failed during processing of group {groupname} with error:\n {traceback.format_exc()}\n")
        report["failed"].append(groupname)

    return {"r": log.text, "report": report}


def execute_hcp_hand_reclassification(sinfo, options, hcp, run, groupname):
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
        log.action("Processing", f"ICA {groupname}", options["run"])
        groupok = True

        # load parameters or use default values
        highpass = (
            0
            if options["hcp_icafix_highpass"] is None
            else options["hcp_icafix_highpass"]
        )

        # --- check for the ICA image
        icaimg = os.path.join(
            hcp["hcp_nonlin"],
            "Results",
            groupname,
            "%s_hp%s_clean.nii.gz" % (groupname, highpass),
        )
        groupok = pc.check_for_file(icaimg,
            f"ICA {groupname} present",
            f"ICA [{icaimg}] missing!",
            status=groupok,
            bad_level="error",
            _log=log,
        )

        comm = (
            '%(script)s \
            --study-folder="%(studyfolder)s" \
            --subject="%(subject)s" \
            --fmri-name="%(groupname)s" \
            --high-pass="%(highpass)s"'
            % {
                "script": os.path.join(
                    hcp["hcp_base"], "ICAFIX", "ApplyHandReClassifications.sh"
                ),
                "studyfolder": sinfo["hcp"],
                "subject": sinfo["id"] + options["hcp_suffix"],
                "groupname": groupname,
                "highpass": highpass,
            }
        )

        # -- Report command
        if groupok:
            log.pipeline_command(comm)

        # -- Test files
        tfile = os.path.join(
            hcp["hcp_nonlin"],
            "Results",
            groupname,
            "%s_hp%s.ica" % (groupname, highpass),
            "HandNoise.txt",
        )
        full_test = None

        # -- Run
        if run and groupok:
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
                    logtags=[options["logtag"], groupname],
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
                    tfile,
                    full_test,
                    "HCP HandReclassification " + groupname,
                    overwrite=True,
                    _log=log,
                )
                if passed is None:
                    log.step("HCP HandReclassification can be run")
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
        log.raw("\n")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(f"\n\n\n --- Failed during processing of group {groupname} with error:\n")
        log.raw(str(errormessage))
        report["failed"].append(groupname)
    except Exception:
        log.info(f" --- Failed during processing of group {groupname} with error:\n {traceback.format_exc()}\n")
        report["failed"].append(groupname)

    return {"r": log.text, "report": report}
