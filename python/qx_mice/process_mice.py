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
        - preprocess_mice,
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
    --bolds             Which bold images to process. You can select bolds
                        through their number, name or task (e.g. rest), you
                        can chain multiple conditions together by providing a
                        comma separated list.
    --parsessions       How many sessions to run in parallel. [1]
    --parelements       How many elements (e.g bolds) to run in parallel. [1]
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

    --melodic_anatfile          Path to the melodic anat file, without the
                                extension, e.g. without .nii.gz.
                                [qx_library/etc/mice_pipelines/EPI_braine]
    --fix_rdata                 Path to the RData file used by fix.
                                [qx_library/etc/mice_pipelines/zerbi_2015_neuroimage.RData]
    --fix_threshold             Fix ICA treshold. [2].
    --fix_no_motion_cleanup     A flag for disabling cleanup of motion confounds.
                                [Disabled by default]
    --fix_aggressive_cleanup    A flag for performing aggressive cleanup.
                                [Disabled by default]
    --mice_highpass             The value of the highpass filter. [0.01]
    --mice_lowpass              The value of the lowpass filter. [0.25]
    --flirt_ref                 Path to the template file.
                                [qx_library/etc/mice_pipelines/EPI_template.nii.gz]

    OUTPUTS
    =======

    The results of this step will be present in the nii folder
    in the sessions's root::

        study
        └─ sessions
           ├─ session1
           |  └─ nii
           └─ session2
           |  └─ nii

    EXAMPLE USE
    ===========

    ::

        qunex preprocess_mice \
          --sessionsfolder="/data/mice_study/sessions" \
          --sessions="/data/mice_study/processsing/batch.txt"

    """

    # get session id
    session = sinfo['id']

    r = '\n------------------------------------------------------------'
    r += f'\nSession id: {sinfo["id"]} \n[started on {datetime.now().strftime("%A, %d. %B %Y %H:%M:%S")}]'
    r += f'\n{pc.action("Running", options["run"])} preprocess_mice {session} ...'

    report = {'done': [], 'failed': [], 'ready': [], 'not ready': []}  

    try:
        # check base settings
        pc.doOptionsCheck(options, sinfo, 'preprocess_mice')
        
        # get bolds
        bolds, _, _, r = pc.useOrSkipBOLD(sinfo, options, r)

        # filter bolds
        if (options['bolds'] != 'all'):
            bolds = pc._filter_bolds(bolds, options['bolds'])

        # report
        parelements = max(1, min(options['parelements'], len(bolds)))
        r += f'\n{pc.action("Running", options["run"])} {parelements} BOLD images in parallel'

        if parelements == 1: # serial execution
            for b in bolds:
                # process
                result = _execute_preprocess_mice(sinfo, options, overwrite, b)

                # merge r
                r += result['r']

                # merge report
                tempReport            = result['report']
                report['done']       += tempReport['done']
                report['failed']     += tempReport['failed']
                report['ready']      += tempReport['ready']
                report['not ready']  += tempReport['not ready']

        else: # parallel execution
            # create a multiprocessing Pool
            processPoolExecutor = ProcessPoolExecutor(parelements)
            # process
            f = partial(_execute_preprocess_mice, sinfo, options, overwrite)
            results = processPoolExecutor.map(f, bolds)

            # merge r and report
            for result in results:
                r                    += result['r']
                tempReport            = result['report']
                report['done']       += tempReport['done']
                report['failed']     += tempReport['failed']
                report['ready']      += tempReport['ready']
                report['not ready']  += tempReport['not ready']

        rep = []
        for k in ['done', 'failed', 'ready', 'not ready', ]:
            if len(report[k]) > 0:
                rep.append(f'{", ".join(report[k])} {k}')

        report = (sinfo['id'], 'preprocess_mice: bolds ' + '; '.join(rep), len(report['failed'] + report['not ready']))

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = f'\n --- Failed during processing of session {session} with error:\n'
        r += str(errormessage)
        report = (sinfo['id'], 'preprocess_mice failed', 1)

    except:
        r += f'n --- Failed during processing of session {session} with error:\n {traceback.format_exc()}\n'
        report = (sinfo['id'], 'preprocess_mice failed', 1)

    return (r, report)


def _execute_preprocess_mice(sinfo, options, overwrite, bold_data):
    # prepare return variables
    r = ""
    report = {'done': [], 'failed': [], 'ready': [], 'not ready': []}

    # script location
    qx_dir = os.environ['QUNEXPATH']
    preprocess_mice_script = 'bash ' + os.path.join(qx_dir, 'bash', 'qx_mice', 'preprocess_mice.sh')

    # work dir
    work_dir = os.path.join(options['sessionsfolder'], sinfo['id'], 'nii')

    # extract bold filename
    _, _, _, boldinfo = bold_data
    boldname  = boldinfo['ima'] + '_ds'

    # --- check for bold image
    boldimg = os.path.join(work_dir, f'{boldname}.nii.gz')
    r, boldok = pc.checkForFile2(r, boldimg, '\n     ... preprocess_mice bold image present', '\n     ... ERROR: preprocess_mice bold image missing!')

    if boldok:
        # set up the command
        comm = '%(script)s \
                --work_dir="%(work_dir)s" \
                --bold="%(bold)s" \
                --fix_threshold="%(fix_threshold)s" \
                --mice_highpass="%(mice_highpass)s" \
                --mice_lowpass="%(mice_lowpass)s"' % {
                "script"   : preprocess_mice_script,
                "work_dir" : work_dir,
                "bold"     : boldname,
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
        r += '\n\n------------------------------------------------------------\n'
        r += 'Running preprocess_mice command via QuNex:\n\n'
        r += comm.replace('                ', '')
        r += '\n------------------------------------------------------------\n'

        # run
        if options['run'] == 'run':
            # execute
            r, endlog, _, failed = pc.runExternalForFile(None, comm, 'Running preprocess_mice', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=[options['logtag']], fullTest=None, shell=True, r=r)

            if failed:
                r += f'\n---> preprocess_mice processing for BOLD {boldname} failed'
                report['failed'].append(boldname)
            else:
                r += f'\n---> preprocess_mice processing for BOLD {boldname} completed'
                report['done'].append(boldname)

        else:
            r += f'\n---> BOLD {boldname} is ready for preprocess_mice command'
            report['ready'].append(boldname)

    else:
        # run
        if options['run'] == 'run':
            r += f'\n---> preprocess_mice processing for BOLD {boldname} failed'
            report['failed'].append(boldname)
        # just checking
        else:
            r += f'\n---> BOLD {boldname} is not ready for preprocess_mice command'
            report['not ready'].append(boldname)

    return {'r': r, 'report': report}
