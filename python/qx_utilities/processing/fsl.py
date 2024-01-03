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

All the functions are part of the processing suite. They should be called
from the command line using `qunex` command. Help is available through:

- ``qunex ?<command>`` for command specific help
There are additional support functions that are not to be used
directly.
"""

"""
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
        --feat_file (str, default ''):
            Path to the feat file. If an absolute path is provided all sessions
            will be processed using the same feat file. If a relative path
            is provided, QuNex will look for the feat file inside each
            session's folder.

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

        --log (str, default 'keep'):
            Whether to keep ("keep") or remove ("remove") the temporary logs
            once jobs are completed.
            When a comma or pipe ("|") separated list is given, the log will be
            created at the first provided location and then linked or copied to
            other locations. The valid locations are:

            - "study" (for the default:
              `<study>/processing/logs/comlogs` location)
            - "session" (for `<sessionid>/logs/comlogs`)
            - "hcp" (for `<hcp_folder>/logs/comlogs`)
            - "<path>" (for an arbitrary directory).

    Examples:
        ::

            qunex fsl_feat \\
                --feat_file="feat.fsf" \\
                --sessionsfolder="/data/qunex_study/sessions" \\
                --sessions="OP207,OP208e" \\
                --parsessions=2

            qunex fsl_feat \\
                --feat_file="/data/qunex_study/info/feat.fsf" \\
                --sessionsfolder="/data/qunex_study/sessions" \\
                --sessions="OP207,OP208e" \\
                --parsessions=2
    """

    # get session id
    session = sinfo["id"]

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s FSL feat [%s] ..." % (
        pc.action("Running", options["run"]), session)

    # status variables
    run = True

    try:
        # check base settings
        pc.doOptionsCheck(options, sinfo, "fsl_feat")

        # get feat file
        feat_file = None
        if "feat_file" not in options or options["feat_file"] is None:
            r += f"\n---> ERROR: feat_file not provided."
            report = (sinfo['id'], "Not ready for FSL feat", 1)
            run = False

        # relative path?
        if "sessionsfolder" in options and run:
            feat_path = os.path.join(options["sessionsfolder"], session,
                                     options["feat_file"])
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
            r += f"\n---> ERROR: Could not find the feat file [{options["feat_file"]}]."
            report = (sinfo['id'], "Not ready for FSL feat", 1)
            run = False

        # set up the command
        comm = "feat \
                %(feat_file)s" % {
            "feat_file": feat_file}

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
                r, _, _, failed = pc.runExternalForFile(None, comm, "Running FSL feat", overwrite=overwrite, thread=sinfo["id"], remove=options[
                                                             "log"] == "remove", task=options["command_ran"], logfolder=options["comlogs"], logtags=[options["logtag"]], fullTest=None, shell=True, r=r)
                if failed:
                    r += "\n---> FSL feat processing for session %s failed" % session
                    report = (sinfo['id'], "FSL feat failed", 1)
                else:
                    r += "\n---> FSL feat processing for session %s completed" % session
                    report = (sinfo['id'], "FSL feat completed", 0)

            # just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    None, None, "FSL feat " + session, r, overwrite=overwrite)

                if passed is None:
                    r += "\n---> FSL feat can be run"
                    report = (sinfo['id'], "FSL feat ready", 0)
                else:
                    r += "\n---> FSL feat processing for session %s would be skipped" % session
                    report = (sinfo['id'], "FSL feat would be skipped", 1)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of session %s with error:\n" % (
            session)
        r += str(errormessage)
        report = (sinfo['id'], "FSL feat failed", 1)

    except:
        r += "\n --- Failed during processing of session %s with error:\n %s\n" % (
            session, traceback.format_exc())
        report = (sinfo['id'], "FSL feat failed", 1)

    return (r, report)