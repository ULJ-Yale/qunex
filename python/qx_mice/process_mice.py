#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``process_mice.py``

This file holds code for processing mice MRI data with QuNex mice pipelines. It
consists of functions:

- preprocess_mice   Runs the QuNex mice preprocessing pipeline.

All the functions are part of the processing suite. They should be called
from the command line using `qunex` command. Help is available through:

- ``qunex ?<command>`` for command specific help
- ``qunex -o`` for a list of relevant arguments and options

There are additional support functions that are not to be used
directly.
"""

"""
Copyright (c) Jure Demsar, Jie Lisa Ji and Valerio Zerbi
All rights reserved.
"""
import os

import qx_utilities as qxu
import qx_utilities.processing.core as pc

from datetime import datetime

def preprocess_mice(sinfo, options, overwrite=False, thread=0):
    """
    ``preprocess_mice [... processing options]``
    ``premice [... processing options]``

    Runs the command to prepare a QuNex study for mice preprocessing.

    REQUIREMENTS
    ============

    Succesfull preparation of mice data for preprocessing:
        - data import,
        - setup_mice,
        - create_session_info,
        - create_batch.

    INPUTS
    ======

    General parameters
    ------------------

    When running the command, the following *general* processing parameters are
    taken into account:

    --sessions          The batch.txt file with all the sessions information.
                        [batch.txt]
    --sessionsfolder    The path to the study/sessions folder, where the
                        imaging data is supposed to go. [.]
    --parsessions       How many sessions to run in parallel. [1]
    --logfolder         The path to the folder where runlogs and comlogs
                        are to be stored, if other than default. []
    --log               Whether to keep ("keep") or remove ("remove") the
                        temporary logs once jobs are completed. ["keep"]
                        When a comma or pipe ("|") separated list is given, 
                        the log will be created at the first provided 
                        location and then linked or copied to other 
                        locations. The valid locations are:
                        
                        - "study" (for the default: 
                          `<study>/processing/logs/comlogs` location)
                        - "session" (for `<sessionid>/logs/comlogs`)
                        - "hcp" (for `<hcp_folder>/logs/comlogs`)
                        - "<path>" (for an arbitrary directory)

    Specific parameters
    -------------------

    --tr                            TR of the bold data. [2.5]
    --increase_voxel_size           The factor by which to increase voxel size.
    --no_orienatation_correction    Whether to disable orientation correction.
    --no_despike                    Whether to disable despiking.

    OUTPUTS
    =======

    TODO

    The results of this step will be present in the dMRI/NHP/F99reg folder
    in the sessions's root::

        study
        └─ sessions
           ├─ session1
           |  └─ dMRI
           |    └─ NHP
           |      └─ F99reg
           └─ session2
              └─ dMRI
                └─ NHP
                  └─ F99reg

    EXAMPLE USE
    ===========

    ::

        qunex preprocess_mice \
          --sessionsfolder="/data/mice_study/sessions" \
          --sessions="/data/mice_study/processsing/batch.txt" \
          --parsessions=2

    """

    # get session id
    session = sinfo["id"]

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo["id"], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s preprocess_mice [%s] ..." % (pc.action("Running", options["run"]), session)

    # status variables
    run = True

    try:
        # check base settings
        pc.doOptionsCheck(options, sinfo, "preprocess_mice")
        
        # script location
        qx_dir = os.environ["QUNEXPATH"]
        preprocess_mice_script = "bash " + os.path.join(qx_dir, "bash", "qx_mice", "preprocess_mice.sh")

        # work dir
        # TODO FIX
        work_dir = os.path.join(options["sessionsfolder"], sinfo["id"])

        # set up the command
        comm = '%(script)s \
                --work_dir="%(work_dir)s" \
                --session="%(session)s" \
                --fix_threshold="%(fix_threshold)s" \
                --mice_highpass="%(mice_highpass)s" \
                --mice_lowpass="%(mice_lowpass)s"' % {
                "script"   : preprocess_mice_script,
                "work_dir" : work_dir,
                "fix_threshold" : options["fix_threshold"],
                "mice_highpass" : options["mice_highpass"],
                "mice_lowpass"  : options["mice_lowpass"]}

        # optional parameters
        if options["melodic_anatfile"]:
            comm += "                --melodic_anatfile=" + options["melodic_anatfile"]
        
        if options["fix_rdata"]:
            comm += "                --fix_rdata=" + options["fix_rdata"]

        if options["flirt_ref"]:
            comm += "                --flirt_ref=" + options["flirt_ref"]

        if options['fix_no_motion_cleanup']:
            comm += "                --fix_no_motion_cleanup"

        if options['fix_aggressive_cleanup']:
            comm += "                --fix_aggressive_cleanup"

        # report command
        r += "\n\n------------------------------------------------------------\n"
        r += "Running preprocess_mice command via QuNex:\n\n"
        r += comm.replace("                ", "")
        r += "\n------------------------------------------------------------\n"

        # run
        if run:
            # run
            if options["run"] == "run":

                # execute
                r, endlog, _, failed = pc.runExternalForFile(None, comm, "Running preprocess_mice", overwrite=overwrite, thread=sinfo["id"], remove=options["log"] == "remove", task=options["command_ran"], logfolder=options["comlogs"], logtags=[options["logtag"]], fullTest=None, shell=True, r=r)

                if failed:
                    r += "\n---> preprocess_mice processing for session %s failed" % session
                    report = (sinfo['id'], "preprocess_mice failed", 1)
                else:
                    r += "\n---> preprocess_mice processing for session %s completed" % session
                    report = (sinfo['id'], "preprocess_mice completed", 0)

            # just checking
            else:
                passed, _, r, failed = pc.checkRun(target_file, None, "preprocess_mice " + session, r, overwrite=overwrite)

                if passed is None:
                    r += "\n---> preprocess_mice can be run"
                    report = (sinfo['id'], "preprocess_mice ready", 0)
                else:
                    r += "\n---> preprocess_mice processing for session %s would be skipped" % session
                    report = (sinfo['id'], "preprocess_mice would be skipped", 1)


    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of session %s with error:\n" % (session)
        r += str(errormessage)
        report = (sinfo['id'], "preprocess_mice failed", 1)

    except:
        r += "\n --- Failed during processing of session %s with error:\n %s\n" % (session, traceback.format_exc())
        report = (sinfo['id'], "preprocess_mice failed", 1)

    return (r, report)
