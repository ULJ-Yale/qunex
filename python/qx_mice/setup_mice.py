#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2022 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``setup_mice.py``

This file holds code for preparing a study for QuNex mice pipelines. It
consists of functions:

- setup_mice    Runs the command to prepare a study for QuNex mice pipelines.

All the functions are part of the processing suite. They should be called
from the command line using `qunex` command. Help is available through:

- ``qunex ?<command>`` for command specific help
- ``qunex -o`` for a list of relevant arguments and options

There are additional support functions that are not to be used
directly.
"""

'''
Copyright (c) Jure Demsar, Jie Lisa Ji and Valerio Zerbi
All rights reserved.
'''

import os

import qx_utilities.general.core as gc
import qx_utilities.processing.core as pc

from datetime import datetime

from concurrent.futures import ProcessPoolExecutor
from functools import partial

def setup_mice(sinfo, options, overwrite=False, thread=0):
    """
    ``setup_mice [... processing options]``

    Runs the command to prepare a QuNex study for mice preprocessing.

    Warning:
        Succesfull import of mice data is required to run this command.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --bolds (str, default ''):
            Which bold images to process. You can select bolds through their
            number, name or task (e.g. rest), you can chain multiple conditions
            together by providing a comma separated list.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

        --tr (float, default 2.5):
            TR of the bold data.

        --voxel_increase (int):
            The factor by which to increase voxel size. If not provided QuNex
            will not increase the voxel size.

        --orienatation (str, default 'x -y z'):
            A string depicting how to fix the orientation. Set to "" to leave
            orientation as is.

    Output files:
        The results of this step will be present in the mice folder
        in the sessions's root::

            study
            └─ sessions
            ├─ session1
            |  └─ mice
            └─ session2
                └─ mice

    Examples:
        ::

            qunex setup_mice \\
                --sessionsfolder='/data/mice_study/sessions' \\
                --sessions='/data/mice_study/processsing/batch.txt'

        ::

            qunex setup_mice \\
                --sessionsfolder='/data/mice_study/sessions' \\
                --sessions='/data/mice_study/processsing/batch.txt' \\
                --sessionids='joe01' \\
                --bolds='bold1' \\
                --tr='1'

    """

    # get session id
    session = sinfo['id']

    r = '\n------------------------------------------------------------'
    r += f'\nSession id: {sinfo["id"]} \n[started on {datetime.now().strftime("%A, %d. %B %Y %H:%M:%S")}]'
    r += f'\n{pc.action("Running", options["run"])} setup_mice {session} ...'

    report = {'done': [], 'failed': [], 'ready': [], 'not ready': []}

    try:
        # check base settings
        pc.doOptionsCheck(options, sinfo, 'setup_mice')

        # get bolds
        bolds, _, _, r = pc.use_or_skip_bold(sinfo, options, r)

        # report
        parelements = max(1, min(options['parelements'], len(bolds)))
        r += f'\n{pc.action("Running", options["run"])} {parelements} BOLD images in parallel'

        if parelements == 1: # serial execution
            for b in bolds:
                # process
                result = _execute_setup_mice(sinfo, options, overwrite, b)

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
            f = partial(_execute_setup_mice, sinfo, options, overwrite)
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
        for k in ['done', 'failed', 'ready', 'not ready']:
            if len(report[k]) > 0:
                rep.append(f'{", ".join(report[k])} {k}')

        report = (sinfo['id'], 'setup_mice: bolds ' + '; '.join(rep), len(report['failed'] + report['not ready']))

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = f'\n --- Failed during processing of session {session} with error:\n'
        r += str(errormessage)
        report = (sinfo['id'], 'setup_mice failed', 1)

    except:
        r += f'n --- Failed during processing of session {session} with error:\n {traceback.format_exc()}\n'
        report = (sinfo['id'], 'setup_mice failed', 1)

    return (r, report)


def _execute_setup_mice(sinfo, options, overwrite, boldinfo):
    # prepare return variables
    r = ''
    report = {'done': [], 'failed': [], 'ready': [], 'not ready': []}

    # script location
    qx_dir = os.environ['QUNEXPATH']
    setup_mice_script = 'bash ' + os.path.join(qx_dir, 'bash', 'qx_mice', 'setup_mice.sh')

    # work dir
    nifti_dir = os.path.join(options['sessionsfolder'], sinfo['id'], 'nii')
    work_dir = os.path.join(options['sessionsfolder'], sinfo['id'], 'mice')

    # create mice dir if it does not exist
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)


    # --- check for bold image
    source_bold = os.path.join(nifti_dir, f'{boldinfo["ima"]}.nii.gz')
    r, boldok = pc.checkForFile2(r, source_bold, '\n     ... setup_mice bold image present', '\n     ... ERROR: setup_mice bold image missing!')

    # map the image
    target_bold = os.path.join(work_dir, f'{boldinfo["name"]}.nii.gz')
    r += f'\n---> mapping the bold image to session\'s mice pipelines (mice) folder\n'

    # overwrite and file exists
    if (not overwrite and os.path.exists(target_bold)):
        r += f' ... overwrite is disable and target bold [{target_bold}] already exists, skipping this bold.\n'
        report['done'].append(boldinfo['name'])
    else:
        # map
        r += f' ... mapping {source_bold} => {target_bold}.\n'
        gc.link_or_copy(source_bold, target_bold)

        if boldok:
            # set up the command
            comm = '%(script)s \
                    --work_dir="%(work_dir)s" \
                    --bold="%(bold)s" \
                    --tr="%(tr)s" \
                    --orientation="%(orientation)s"' % {
                    "script"     : setup_mice_script,
                    "work_dir"   : work_dir,
                    "bold"       : boldinfo['name'],
                    "tr"         : options["tr"],
                    "orientation": options["orientation"].replace(" ", "|")}

            # optional parameters
            # voxel_increase
            if options['voxel_increase']:
                comm += '                --voxel_increase=' + options['voxel_increase']

            # report command
            r += '\n\n------------------------------------------------------------\n'
            r += 'Running setup_mice bash script through QuNex:\n\n'
            r += comm.replace('                ', '')
            r += '\n------------------------------------------------------------\n'

            # run
            if options['run'] == 'run':
                test_file = os.path.join(work_dir, f'{boldinfo["name"]}_DS.nii.gz')
                if overwrite and os.path.exists(test_file):
                    os.remove(test_file)

                # execute
                r, endlog, _, failed = pc.runExternalForFile(test_file, comm, 'Running setup_mice', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=[options['logtag']], fullTest=None, shell=True, r=r)

                if failed:
                    r += f'\n---> setup_mice processing for BOLD {boldinfo["name"]} failed'
                    report['failed'].append(boldinfo['name'])
                else:
                    r += f'\n---> setup_mice processing for BOLD {boldinfo["name"]} completed'
                    report['done'].append(boldinfo['name'])

            else:
                r += f'\n---> BOLD {boldinfo["name"]} is ready for setup_mice command'
                report['ready'].append(boldinfo['name'])

        else:
            # run
            if options['run'] == 'run':
                r += f'\n---> setup_mice processing for BOLD {boldinfo["name"]} failed'
                report['failed'].append(boldinfo['name'])
            # just checking
            else:
                r += f'\n---> BOLD {boldinfo["name"]} is not ready for setup_mice command'
                report['not ready'].append(boldinfo['name'])

    return {'r': r, 'report': report}
