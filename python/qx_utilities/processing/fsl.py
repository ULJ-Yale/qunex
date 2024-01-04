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

- ``qunex ?<command>`` for command specific help
There are additional support functions that are not to be used
directly.

Copyright (c) Jure Demsar.
All rights reserved.
"""

import os
import traceback
import processing.core as pc
from datetime import datetime


def fsl_feat(sinfo, options, overwrite=False, thread=0):
    """
    ``fsl_feat [... processing options]``

    This command executes FSL's feat software tool for high quality model-based
    FMRI data analysis.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

        --feat_file (str, default ''):
            Path to the feat file. If an absolute path is provided all sessions
            will be processed using the same feat file. If a relative path
            is provided, QuNex will look for the feat file inside each
            session's folder.

    Examples:
        ::

            qunex fsl_feat \\
                --feat_file="feat.fsf" \\
                --sessionsfolder="/data/qunex_study/sessions" \\
                --sessions="OP207,OP208" \\
                --parsessions=2

            qunex fsl_feat \\
                --feat_file="/data/qunex_study/info/feat.fsf" \\
                --sessionsfolder="/data/qunex_study/sessions" \\
                --sessions="OP207,OP208" \\
                --parsessions=2
    """

    # get session id
    session = sinfo["id"]

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\n%s FSL feat [%s] ..." % (pc.action("Running", options["run"]), session)

    # status variables
    run = True

    try:
        # check base settings
        pc.doOptionsCheck(options, sinfo, "fsl_feat")

        # get feat file
        feat_file = None
        if "feat_file" not in options or options["feat_file"] is None:
            r += f"\n---> ERROR: feat_file not provided."
            report = (sinfo["id"], "Not ready for FSL feat", 1)
            run = False

        # relative path?
        if "sessionsfolder" in options and run:
            feat_path = os.path.join(
                options["sessionsfolder"], session, options["feat_file"]
            )
            r += "\n---> Checking for feat file at %s" % feat_path
            if os.path.exists(feat_path):
                r += "\n    ... Feat file found"
                feat_file = feat_path

        # if feat_file is still none, try absolute path
        if feat_file is None and run:
            r += f"\n---> Checking for feat file at {options['feat_file']}"
            if os.path.exists(options["feat_file"]):
                r += "\n    ... Feat file found"
                feat_file = options["feat_file"]

        if feat_file is None and run:
            r += f"\n---> ERROR: Could not find the feat file [{options['feat_file']}]."
            report = (sinfo["id"], "Not ready for FSL feat", 1)
            run = False

        # set up the command
        comm = "feat %(feat_file)s" % {"feat_file": feat_file}

        # report command
        r += "\n\n------------------------------------------------------------\n"
        r += "Running FSL feat command via QuNex:\n\n"
        r += comm.replace("                ", "")
        r += "\n------------------------------------------------------------\n"

        # run
        if run:
            # run
            if options["run"] == "run":
                # execute
                r, _, _, failed = pc.runExternalForFile(
                    None,
                    comm,
                    "Running FSL feat",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"]],
                    fullTest=None,
                    shell=True,
                    r=r,
                )
                if failed:
                    r += "\n---> FSL feat processing for session %s failed" % session
                    report = (sinfo["id"], "FSL feat failed", 1)
                else:
                    r += "\n---> FSL feat processing for session %s completed" % session
                    report = (sinfo["id"], "FSL feat completed", 0)

            # just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    None, None, "FSL feat " + session, r, overwrite=overwrite
                )

                if passed is None:
                    r += "\n---> FSL feat can be run"
                    report = (sinfo["id"], "FSL feat ready", 0)
                else:
                    r += (
                        "\n---> FSL feat processing for session %s would be skipped"
                        % session
                    )
                    report = (sinfo["id"], "FSL feat would be skipped", 1)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of session %s with error:\n" % (
            session
        )
        r += str(errormessage)
        report = (sinfo["id"], "FSL feat failed", 1)

    except:
        r += "\n --- Failed during processing of session %s with error:\n %s\n" % (
            session,
            traceback.format_exc(),
        )
        report = (sinfo["id"], "FSL feat failed", 1)

    return (r, report)


def fsl_melodic(sinfo, sessions, options, overwrite=False, thread=0):
    """
    ``fsl_melodic [... processing options]``

    This command executes FSL's melodic command line tool for ICA decomposition.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

        --input_files (str, default ''):
            A list of input files to run melodic on. These files can be
            located in the session folder, QuNex will iterate over sessions and
            use all of the listed files for all provided sessions. Can also be a
            list of absolute paths without sessions. If multiple files are
            provided, they should be separated by commas, e.g. "bold1,bold2".

        --melodic_extra_args (str, default ''):
            Additional arguments to pass to melodic. All arguments need to be
            provided as a single literal string, e.g.
            "--ICs=melodic_IC --mix=melodic_mix".

    Examples:
        ::

            qunex fsl_melodic \\
                --input_files="bold1,bold2" \\
                --sessionsfolder="/data/qunex_study/sessions" \\
                --sessions="OP207,OP208"

            qunex fsl_melodic \\
                --input_files="bold1,bold2" \\
                --sessionsfolder="/data/qunex_study/sessions" \\
                --sessions="OP207,OP208" \\
                --melodic_extra_args="--ICs=melodic_IC --mix=melodic_mix"
    """

    # list of sessions
    sessions_array = sessions.split(",")

    r = "\n------------------------------------------------------------"
    r += "\nMelodic: \n[started on %s]" % (
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S")
    )
    r += "\n%s FSL melodic ..." % (pc.action("Running", options["run"]))

    # status variables
    run = True

    try:
        # check base settings
        pc.doOptionsCheck(options, sessions, "fsl_melodic")

        # get input files
        input_files = []
        if "input_files" not in options or options["input_files"] is None:
            r += f"\n---> ERROR: input_files not provided."
            report = ("Study", "Not ready for FSL melodic", 1)
            run = False

        # input paths
        input_paths = options["input_files"].split(",")

        # sessions provided
        if len(sessions_array) > 0:
            r += "\n---> Multiple sessions provided. Will iterate over sessions."
            for session in sessions_array:
                r += f"\n---> Working on session {session}"

                for path in input_paths:
                    r += f"\n    ... checking {path}"
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
                            r += "\n        ... found at %s" % pathc
                            input_files.append(pathc)
                            file_found = True
                            break

                    if not file_found:
                        r += f"\n        ... ERROR: Could not find {path} for session {session}."
                        report = (session, "Not ready for FSL melodic", 1)
                        run = False
                        break

        # no sessions provided, we use absolute paths
        else:
            r += "\n---> No sessions provided. Will use absolute paths."
            for path in input_paths:
                r += f"\n---> Working on path {path}"
                if not os.path.exists(path):
                    r += f"\n    ... ERROR: Could not find {path}."
                    input_files.append(path)
                    report = ("Study", "Not ready for FSL melodic", 1)
                    run = False
                    break

        # set up the command
        comm = "melodic -i %(input_files)s" % {"input_files": ",".join(input_files)}

        # output
        # set from melodic_extra_args
        if options["melodic_extra_args"] is not None and (
            "-o " in options["melodic_extra_args"]
            or "--output " in options["melodic_extra_args"]
        ):
            r += "\n---> Output folder set through melodic_extra_args."
        elif options["sessionsfolder"] is not None:
            r += "\n---> Output folder set through sessionsfolder."
            comm += f" -o {os.path.join(options['sessionsfolder'], 'melodic')}"
        else:
            r += "\n---> ERROR: output (-o or --output) needs to be set through melodic_extra_args or by providing a sessionsfolder."
            report = ("Study", "Not ready for FSL melodic", 1)
            run = False

        # extra args
        if options["melodic_extra_args"] is not None:
            comm += " " + options["melodic_extra_args"]

        # report command
        r += "\n\n------------------------------------------------------------\n"
        r += "Running FSL melodic command via QuNex:\n\n"
        r += comm.replace("                ", "")
        r += "\n------------------------------------------------------------\n"

        # run
        if run:
            # run
            if options["run"] == "run":
                # execute
                r, _, _, failed = pc.runExternalForFile(
                    None,
                    comm,
                    "Running FSL melodic",
                    overwrite=overwrite,
                    thread="Study",
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"]],
                    fullTest=None,
                    shell=True,
                    r=r,
                )
                if failed:
                    r += "\n---> FSL melodic processing failed"
                    report = ("Study", "FSL melodic failed", 1)
                else:
                    r += "\n---> FSL melodic processing completed"
                    report = ("Study", "FSL melodic completed", 0)

            # just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    None, None, "FSL melodic " + sessions, r, overwrite=overwrite
                )

                if passed is None:
                    r += "\n---> FSL melodic can be run"
                    report = ("Study", "FSL melodic ready", 0)
                else:
                    r += "\n---> FSL melodic processing for would be skipped"
                    report = ("Study", "FSL melodic would be skipped", 1)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed with error:\n"
        r += str(errormessage)
        report = ("Study", "FSL melodic failed", 1)

    except:
        r += "\n --- Failed with error:\n %s\n" % (traceback.format_exc())
        report = ("Study", "FSL melodic failed", 1)

    return (r, report)
