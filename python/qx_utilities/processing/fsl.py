#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``fsl.py``

This file holds code for running FSL commands. It
consists of functions:

--fsl_feat      Runs FSL feat command.
--fsl_melodic   Runs FSL melodic command.

All the functions are part of the processing suite. They should be called
from the command line using `qunex` command. Help is available through:

- ``qunex <command> --help`` for command specific help
There are additional support functions that are not to be used
directly.

Copyright (c) Jure Demsar.
All rights reserved.
"""

import os
import re
import traceback
from datetime import datetime

import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog


def fsl_feat(sinfo, options, overwrite=False, thread=0):
    """
    ``fsl_feat [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Execute FSL's feat software tool for high quality model-based
    FMRI data analysis.

    ..  qx_command:
        type: processing.session

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

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

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --feat_file (str, default ''):
            Path to the feat file. If an absolute path is provided all sessions
            will be processed using the same feat file. If a relative path
            is provided, QuNex will look for the feat file inside each
            session's folder.

    Examples:
        ::

            qunex fsl_feat \\
                --studyfolder="/data/qunex_study" \\
                --feat_file="feat.fsf" \\
                --sessions="OP207,OP208" \\
                --parsessions=2

            qunex fsl_feat \\
                --studyfolder="/data/qunex_study" \\
                --feat_file="/data/qunex_study/info/feat.fsf" \\
                --sessions="OP207,OP208" \\
                --parsessions=2
    """
    log = ReportLog()

    # get session id
    session = sinfo["id"]

    log.rule()
    log.info(f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]")
    log.action("Running", f"FSL feat [{session}] ...", options["run"], level="info")

    # status variables
    run = True

    try:
        # check base settings
        pc.do_options_check(options, sinfo, "fsl_feat")

        # get feat file
        feat_file = None
        if "feat_file" not in options or options["feat_file"] is None:
            log.error("feat_file not provided.")
            report = (sinfo["id"], "Not ready for FSL feat", 1)
            run = False

        # relative path?
        if "sessionsfolder" in options and run:
            feat_path = os.path.join(
                options["sessionsfolder"], session, options["feat_file"]
            )
            log.step(f"Checking for feat file at {feat_path}")
            if os.path.exists(feat_path):
                log.detail("Feat file found")
                feat_file = feat_path

        # if feat_file is still none, try absolute path
        if feat_file is None and run:
            log.step(f"Checking for feat file at {options['feat_file']}")
            if os.path.exists(options["feat_file"]):
                log.detail("Feat file found")
                feat_file = options["feat_file"]

        if feat_file is None and run:
            log.error(f"Could not find the feat file [{options['feat_file']}].")
            report = (sinfo["id"], "Not ready for FSL feat", 1)
            run = False

        # set up the command
        comm = "feat %(feat_file)s" % {"feat_file": feat_file}

        # report command
        log.rule(before=1, after=1)
        log.raw("Running FSL feat command via QuNex:\n\n")
        log.raw(comm.replace("                ", ""))
        log.rule(after=1)

        # run
        if run:
            # run
            if options["run"] == "run":
                # execute
                _, _, failed = pc.run_external_for_file(
                    None,
                    comm,
                    "Running FSL feat",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"]],
                    full_test=None,
                    shell=True,
                    _log=log,
                )
                if failed:
                    log.step(f"FSL feat processing for session {session} failed")
                    report = (sinfo["id"], "FSL feat failed", 1)
                else:
                    log.step(f"FSL feat processing for session {session} completed")
                    report = (sinfo["id"], "FSL feat completed", 0)

            # just checking. feat names its outputs in the feat file, so
            # there is nothing here to check them against
            else:
                log.step("FSL feat can be run")
                report = (sinfo["id"], "FSL feat ready", 0)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(f"\n\n\n --- Failed during processing of session {session} with error:\n")
        log.raw(str(errormessage))
        report = (sinfo["id"], "FSL feat failed", 1)

    except Exception:
        log.info(f" --- Failed during processing of session {session} with error:\n {traceback.format_exc()}\n")
        report = (sinfo["id"], "FSL feat failed", 1)

    return log.result(report)


def fsl_melodic(sessions, options, overwrite=False, thread=0):
    """
    ``fsl_melodic [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Execute FSL's melodic command line tool for ICA decomposition.

    ..  qx_command:
        type: processing.study

    Description:
        The command runs a single melodic over the input files of all the
        given sessions.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

        --studyfolder (str):
            The path to the study folder. The sessions are in its `sessions`
            folder, unless --sessionsfolder names another one.

        --sessionsfolder (str, default '<studyfolder>/sessions'):
            The path to the folder with the sessions. Set it only when the
            sessions are not in the `sessions` folder of the study. With
            neither --studyfolder nor --sessionsfolder given, the current
            folder is used. The melodic results are written to its `melodic`
            folder, unless --melodic_extra_args sets the output folder.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --input_files (str, default ''):
            A list of input files to run melodic on. These files can be
            located in the session folder, QuNex will iterate over sessions and
            use all of the listed files for all provided sessions. Can also be a
            list of absolute paths. If multiple files are provided, they should
            be separated by commas, e.g. "bold1,bold2".

        --melodic_extra_args (str, default ''):
            Additional arguments to pass to melodic. All arguments need to be
            provided as a single literal string, e.g.
            "--ICs=melodic_IC --mix=melodic_mix". The output folder can be
            set here with -o or --outdir.

    Examples:
        ::

            qunex fsl_melodic \\
                --studyfolder="/data/qunex_study" \\
                --input_files="bold1,bold2" \\
                --sessions="OP207,OP208"

            qunex fsl_melodic \\
                --studyfolder="/data/qunex_study" \\
                --input_files="bold1,bold2" \\
                --sessions="OP207,OP208" \\
                --melodic_extra_args="--ICs=melodic_IC --mix=melodic_mix"
    """
    log = ReportLog()

    # the sessions melodic is run over
    sessions_array = [session["id"] for session in sessions]

    log.rule()
    log.info(f"Melodic: \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]")
    log.action("Running", "FSL melodic ...", options["run"], level="info")

    # status variables
    run = True

    try:
        # check base settings. a run over many sessions has no session of its
        # own, so a `session` or `hcp` --comlog_folders is taken to be the first's
        pc.do_options_check(options, sessions[0], "fsl_melodic")

        # get input files
        input_files = []
        if "input_files" not in options or options["input_files"] is None:
            log.error("input_files not provided.")
            report = ("Study", "Not ready for FSL melodic", 1)
            run = False

        # input paths
        input_paths = options["input_files"].split(",") if run else []

        # sessions provided
        if len(sessions_array) > 0:
            log.step("Multiple sessions provided. Will iterate over sessions.")
            for session in sessions_array:
                log.step(f"Working on session {session}")

                for path in input_paths:
                    log.detail(f"checking {path}")
                    path_candidates = []
                    # check for input file in images functional
                    input_path = os.path.join(
                        options["sessionsfolder"], session, "images", "functional", path
                    )
                    path_candidates.append(input_path)

                    # with .nii.gz
                    input_path = os.path.join(
                        options["sessionsfolder"],
                        session,
                        "images",
                        "functional",
                        path + ".nii.gz",
                    )
                    path_candidates.append(input_path)

                    # as full relative path
                    input_path = os.path.join(options["sessionsfolder"], session, path)
                    path_candidates.append(input_path)

                    # with .nii.gz
                    input_path = os.path.join(
                        options["sessionsfolder"], session, path + ".nii.gz"
                    )
                    path_candidates.append(input_path)

                    file_found = False
                    for pathc in path_candidates:
                        if os.path.exists(pathc):
                            log.detail(f"found at {pathc}")
                            input_files.append(pathc)
                            file_found = True
                            break

                    if not file_found:
                        log.error(f"Could not find {path} for session {session}.", depth=1)
                        report = (
                            "Study",
                            f"Not ready for FSL melodic: {path} missing for {session}",
                            1,
                        )
                        run = False
                        break

                # one missing input is enough, melodic is run over all of them
                if not run:
                    break

        # no sessions provided, we use absolute paths
        else:
            log.step("No sessions provided. Will use absolute paths.")
            for path in input_paths:
                log.step(f"Working on path {path}")
                if not os.path.exists(path):
                    log.error(f"Could not find {path}.", depth=1)
                    report = ("Study", f"Not ready for FSL melodic: {path} missing", 1)
                    run = False
                    break
                input_files.append(path)

        # an absolute path is found once for every session, but is one input
        input_files = list(dict.fromkeys(input_files))

        # set up the command
        comm = "melodic -i %(input_files)s" % {"input_files": ",".join(input_files)}

        # output, set from melodic_extra_args (melodic's -o/--outdir) or else
        # the `melodic` folder in the sessions folder
        if options["melodic_extra_args"] is not None and re.search(
            r"(^|\s)(-o|--outdir|--output)(=|\s|$)", options["melodic_extra_args"]
        ):
            log.step("Output folder set through melodic_extra_args.")
        else:
            log.step("Output folder set through sessionsfolder.")
            comm += f" -o {os.path.join(options['sessionsfolder'], 'melodic')}"

        # extra args
        if options["melodic_extra_args"] is not None:
            comm += " " + options["melodic_extra_args"]

        # report command
        log.rule(before=1, after=1)
        log.raw("Running FSL melodic command via QuNex:\n\n")
        log.raw(comm.replace("                ", ""))
        log.rule(after=1)

        # run
        if run:
            # run
            if options["run"] == "run":
                # execute
                _, _, failed = pc.run_external_for_file(
                    None,
                    comm,
                    "Running FSL melodic",
                    overwrite=overwrite,
                    thread="Study",
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"]],
                    full_test=None,
                    shell=True,
                    _log=log,
                )
                if failed:
                    log.step("FSL melodic processing failed")
                    report = ("Study", "FSL melodic failed", 1)
                else:
                    log.step("FSL melodic processing completed")
                    report = ("Study", "FSL melodic completed", 0)

            # just checking. a run does not check for earlier results, so
            # there is nothing here to check them against
            else:
                log.step("FSL melodic can be run")
                report = ("Study", "FSL melodic ready", 0)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw("\n\n\n --- Failed with error:\n")
        log.raw(str(errormessage))
        report = ("Study", "FSL melodic failed", 1)

    except Exception:
        log.info(f" --- Failed with error:\n {traceback.format_exc()}\n")
        report = ("Study", "FSL melodic failed", 1)

    return log.result(report)
