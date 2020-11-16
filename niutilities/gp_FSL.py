#!/usr/bin/env python2.7
# encoding: utf-8
"""
``gp_HCP.py``

This file holds code for running FSL commands. It
consists of functions:

--fsl_f99       Runs FSL F99 command.

All the functions are part of the processing suite. They should be called
from the command line using `qunex` command. Help is available through:

- ``qunex ?<command>`` for command specific help
- ``qunex -o`` for a list of relevant arguments and options

There are additional support functions that are not to be used
directly.
"""

"""
Copyright (c) Grega Repovs and Jure Demsar.
All rights reserved.
"""
import os

from niutilities.gp_core import *

def fsl_f99(sinfo, options, overwrite=False, thread=0):
    """
    ``fsl_f99 [... processing options]``

    This command executes FSL"s F99 script for registering your own diffusion
    or structural data to the F99 atlas. This atlas is used when processing
    macaque data.

    REQUIREMENTS
    ============

    A completed 

    INPUTS
    ======

    General parameters
    ------------------

    When running the command, the following *general* processing parameters are
    taken into account:

    --sessions              The batch.txt file with all the sessions information.
                            [batch.txt]
    --sessionsfolder        The path to the study/sessions folder, where the
                            imaging data is supposed to go. [.]
    --parsessions           How many sessions to run in parallel. [1]
    --overwrite             Whether to overwrite existing data (yes) or not (no).
                            [no]
    --logfolder             The path to the folder where runlogs and comlogs
                            are to be stored, if other than default. []
    --log                   Whether to keep ("keep") or remove ("remove") the
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

    OUTPUTS
    =======

    The results of this step will be present in the MNINonLinear folder in the
    sessions"s root hcp folder. In case a longitudinal FS template is used, the
    results will be stored in a `MNINonlinear_<FS longitudinal template name>`
    folder::

        study
        └─ sessions
           ├─ session1
           |  └─ dmri
           |    └─ NHP
           |      └─ F99reg
           └─ session2
              └─ dmri
                └─ NHP
                  └─ F99reg

    EXAMPLE USE
    ===========

    ::

        qunex fsl_f99 \
          --sessionsfolder="/data/macaque_study/sessions" \
          --sessions="hilary,jane" \
          --overwrite=no \
          --parsessions=2

    """

    """
    ~~~~~~~~~~~~~~~~~~

    Change log

    2020-11-16 Grega Repovš
               Initial version
    """

    # get session id
    session = sinfo["id"]

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo["id"], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s FSL F99 registration [%s] ..." % (action("Running", options["run"]), session)

    # status variables
    run = True

    try:
        # check base settings
        doOptionsCheck(options, sinfo, "fsl_f99")
        
        # construct dirs
        fsl_dir = os.environ["FSLDIR"]
        nhp_dir = os.path.join(options["sessionsfolder"], session, "NHP")
        f99_dir = os.path.join(nhp_dir, "F99ref")
        if not os.path.exists(f99_dir):
            os.makedirs(f99_dir)
        dtifit_dir = os.path.join(nhp_dir, "dMRI")

        # check dtifit results
        dti_file = os.path.join(dtifit_dir, "dti_FA.nii.gz")
        if os.path.exists(dti_file):
            r += "\n---> dtifit results present."
        else:
            r += "\n---> ERROR: Could not find dtifit results."
            report = ("not ready for FSL F99", 1)
            run = False

        # --- check for existing F99 results
        # TODO target_file = ....
        target_file = "todo.txt"
        fullTest = None

        # set up the command
        comm = "%(script)s \
                %(input)s \
                %(output)s" % {
                "script"  : os.path.join(fsl_dir, "data/xtract_data/standard/F99", "do_reg_F99.sh"),
                "input"   : dti_file,
                "output"  : str(f99_dir) + "/F99"}

        # -- Report command
        r += "\n\n------------------------------------------------------------\n"
        r += "Running FSL F99 command via Qu|Nex:\n\n"
        r += comm.replace("                ", "")
        r += "\n------------------------------------------------------------\n"

        # run
        if run:
            # run
            if options["run"] == "run":
                # remove previous file
                #if overwrite and os.path.exists(target_file):
                #    os.remove(target_file)

                # execute
                r, endlog, _, failed = runExternalForFile(target_file, comm, "Running FSL F99", overwrite=overwrite, thread=sinfo["id"], remove=options["log"] == "remove", task=options["command_ran"], logfolder=options["comlogs"], logtags=[options["logtag"]], fullTest=fullTest, shell=True, r=r)

                if failed:
                    r += "\n---> FSL F99 processing for session %s failed" % session
                    report = ("FSL F99 failed", 1)
                    report["failed"].append(session)
                else:
                    r += "\n---> FSL F99 processing for session %s completed" % session
                    report = ("FSL F99 completed", 0)
                    report["done"].append(session)

            # just checking
            else:
                passed, _, r, failed = checkRun(target_file, None, "FSL F99 " + session, r, overwrite=overwrite)

                if passed is None:
                    r += "\n---> FSL F99 can be run"
                    report = ("FSL F99 ready", 0)
                else:
                    r += "\n---> FSL F99 processing for session %s would be skipped" % session
                    report = ("FSL F99 would be skipped", 1)

        # prepare final report
        report = (sinfo['id'], report[0], report[1])

    except (ExternalFailed, NoSourceFolder), errormessage:
        r = "\n\n\n --- Failed during processing of session %s with error:\n" % (session)
        r += str(errormessage)
        report = (sinfo['id'], "FSL F99 failed", 1)

    except:
        r += "\n --- Failed during processing of session %s with error:\n %s\n" % (session, traceback.format_exc())
        report = (sinfo['id'], "FSL F99 failed", 1)

    print("!!!! report: ", report)

    return (r, report)
