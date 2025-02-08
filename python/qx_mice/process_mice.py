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

import qx_utilities.general.core as gc
import qx_utilities.processing.core as pc

from datetime import datetime


def preprocess_mice(sinfo, options, overwrite=False, thread=0):
    """
    ``preprocess_mice [... processing options]``

    Runs the QuNex mice preprocessing command.

    Warning:
        Successful preparation of mice data for preprocessing encompasses:
            - data import,
            - setup_mice,
            - create_session_info,
            - create_batch.

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

        --bias_field_correction (str, default 'yes'):
            Whether to perform bias field correction, yes/no.

        --melodic_anatfile (str, default 'qx_library/etc/mice_pipelines/EPI_braine'):
            Path to the melodic anat file, without the extension,
            e.g. without .nii.gz.

        --fix_rdata (str, default 'qx_library/etc/mice_pipelines/zerbi_2015_neuroimage.RData'):
            Path to the RData file used by fix.

        --fix_threshold (int, default 2):
            Fix ICA treshold.

        --fix_no_motion_cleanup:
            A flag for disabling cleanup of motion confounds. Disabled by
            default.

        --fix_aggressive_cleanup:
            A flag for performing aggressive cleanup. Disabled by default.

        --mice_highpass (float, default '0.01'):
            The value of the highpass filter.

        --mice_lowpass (float, default '0.25'):
            The value of the lowpass filter.

        --mice_volumes (int, default 900):
            Number of volumes.

        --flirt_ref (str, default 'qx_library/etc/mice_pipelines/EPI_template.nii.gz'):
            Path to the template file.

    Output files:
        The results of this step will be present in the nii folder
        in the sessions's root::

            study
            └─ sessions
            ├─ session1
            |  └─ mice
            └─ session2
                └─ mice

    Examples:
        ::

            qunex preprocess_mice \\
                --sessionsfolder="/data/mice_study/sessions" \\
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
        bolds, _, _, r = pc.use_or_skip_bold(sinfo, options, r)

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
        for k in ['done', 'failed', 'ready', 'not ready']:
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


def _execute_preprocess_mice(sinfo, options, overwrite, boldinfo):
    # prepare return variables
    r = ""
    report = {'done': [], 'failed': [], 'ready': [], 'not ready': []}

    # script location
    qx_dir = os.environ['QUNEXPATH']
    preprocess_mice_script = 'bash ' + os.path.join(qx_dir, 'bash', 'qx_mice', 'preprocess_mice.sh')

    # work dir
    work_dir = os.path.join(options['sessionsfolder'], sinfo['id'], 'mice')

    # --- check for bold image
    boldimg = os.path.join(work_dir, f'{boldinfo['name']}_DS.nii.gz')
    r, boldok = pc.checkForFile2(r, boldimg, '\n     ... preprocess_mice bold image present', '\n     ... ERROR: preprocess_mice bold image missing!')

    # overwrite and file exists
    test_file = os.path.join(work_dir, f'{boldinfo['name']}_filtered_func_data_clean_BP_ABI.nii.gz')
    if (not overwrite and os.path.exists(test_file)):
        r += f' ... overwrite is disable and output [{test_file}] already exists, skipping this bold.\n'
        report['done'].append(boldinfo['name'])
    else:
        if boldok:
            # set up the command
            comm = '%(script)s \
                    --work_dir="%(work_dir)s" \
                    --bold="%(bold)s" \
                    --bias_field_correction="%(bias_field_correction)s" \
                    --fix_threshold="%(fix_threshold)s" \
                    --mice_highpass="%(mice_highpass)s" \
                    --mice_lowpass="%(mice_lowpass)s" \
                    --mice_volumes="%(mice_volumes)s"' % {
                    "script"                : preprocess_mice_script,
                    "work_dir"              : work_dir,
                    "bold"                  : boldinfo['name'],
                    "bias_field_correction" : options["bias_field_correction"],
                    "fix_threshold"         : options["fix_threshold"],
                    "mice_highpass"         : options["mice_highpass"],
                    "mice_lowpass"          : options["mice_lowpass"],
                    "mice_volumes"          : options["mice_volumes"]}

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
            r += 'Running preprocess_mice bash script through QuNex:\n\n'
            r += comm.replace('                ', '')
            r += '\n------------------------------------------------------------\n'

            # run
            if options['run'] == 'run':
                if overwrite and os.path.exists(test_file):
                    os.remove(test_file)

                # execute
                r, endlog, _, failed = pc.runExternalForFile(None, comm, 'Running preprocess_mice', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=[options['logtag']], fullTest=None, shell=True, r=r)

                if failed:
                    r += f'\n---> preprocess_mice processing for BOLD {boldinfo['name']} failed'
                    report['failed'].append(boldinfo['name'])
                else:
                    r += f'\n---> preprocess_mice processing for BOLD {boldinfo['name']} completed'
                    report['done'].append(boldinfo['name'])

            else:
                r += f'\n---> BOLD {boldinfo['name']} is ready for preprocess_mice command'
                report['ready'].append(boldinfo['name'])

        else:
            # run
            if options['run'] == 'run':
                r += f'\n---> preprocess_mice processing for BOLD {boldinfo['name']} failed'
                report['failed'].append(boldinfo['name'])
            # just checking
            else:
                r += f'\n---> BOLD {boldinfo['name']} is not ready for preprocess_mice command'
                report['not ready'].append(boldinfo['name'])

        return {'r': r, 'report': report}


def map_mice_data(sinfo, options, overwrite=False, thread=0):
    """
    ``map_mice_data [... processing options]``

    Runs the command to prepare a QuNex study for mice preprocessing.

    Warning:
        Preprocessed mica data is required.

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
            Whether to overwrite target files that already exist (yes) or not (no).

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

    Output files:
        The results of this step will be present in the functional folder
        in the sessions's root::

            study
            └─ sessions
            ├─ session1
            |  └─ functional
            └─ session2
                └─ functional


    Examples:
        ::

            qunex map_mice_data \\
              --sessionsfolder="/data/mice_study/sessions" \\
              --sessions="/data/mice_study/processsing/batch.txt"

    """

    # get session id
    session = sinfo['id']

    r = '\n------------------------------------------------------------'
    r += f'\nSession id: {sinfo["id"]} \n[started on {datetime.now().strftime("%A, %d. %B %Y %H:%M:%S")}]'
    r += f'\n{pc.action("Running", options["run"])} map_mice_data {session} ...'

    report = {'done': [], 'failed': [], 'ready': [], 'not ready': []}

    try:
        # check base settings
        pc.doOptionsCheck(options, sinfo, 'map_mice_data')

        # get bolds
        bolds, _, _, r = pc.use_or_skip_bold(sinfo, options, r)

        # dirs
        source_dir = os.path.join(options['sessionsfolder'], sinfo['id'], 'mice')
        func_dir = os.path.join(options['sessionsfolder'], sinfo['id'], 'images', 'functional')
        if not os.path.exists(func_dir):
            os.makedirs(func_dir)

        for boldinfo in bolds:


            r += f'\n---> Mapping {boldinfo['name']}'

            # files
            # original
            bold_original = boldinfo['name'] + '.nii.gz'
            source_original = os.path.join(source_dir, bold_original)
            target_original = os.path.join(func_dir, bold_original)

            # EPI
            bold_epi = boldinfo['name'] + '_filtered_func_data_clean_BP_EPI.nii.gz'
            source_epi = os.path.join(source_dir, bold_epi)
            target_epi = os.path.join(func_dir, bold_epi)

            # ABI
            bold_abi = boldinfo['name'] + '_filtered_func_data_clean_BP_ABI.nii.gz'
            source_abi = os.path.join(source_dir, bold_abi)
            target_abi = os.path.join(func_dir, bold_abi)

            # running or testing
            if options['run'] == 'run':
                # original
                r += f'\n ... mapping {bold_original}'
                if os.path.exists(source_original):
                    if os.path.exists(target_original) and not overwrite:
                        f'\n ... {bold_original} already exists and overwrite is set to no, skipping this file'
                    else:
                        gc.link_or_copy(source_original, target_original)
                    report['done'].append(bold_original)
                else:
                    r += f'\n ... ERROR: {bold_original} does not exist, rerun the preprocess_mice step'
                    report['failed'].append(bold_original)

                # EPI
                r += f'\n ... mapping {bold_epi}'
                if os.path.exists(source_epi):
                    if os.path.exists(target_epi) and not overwrite:
                        f'\n ... {bold_epi} already exists and overwrite is set to no, skipping this file'
                    else:
                        gc.link_or_copy(source_epi, target_epi)
                    report['done'].append(bold_epi)
                else:
                    r += f'\n ... ERROR: {bold_epi} does not exist, rerun the preprocess_mice step'
                    report['failed'].append(bold_epi)

                # ABI
                r += f'\n ... mapping {bold_abi}'
                if os.path.exists(source_abi):
                    if os.path.exists(target_abi) and not overwrite:
                        f'\n ... {bold_abi} already exists and overwrite is set to no, skipping this file'
                    else:
                        gc.link_or_copy(source_abi, target_abi)
                    report['done'].append(bold_abi)
                else:
                    r += f'\n ... ERROR: {bold_abi} does not exist, rerun the preprocess_mice step'
                    report['failed'].append(bold_abi)

            else:
                # original
                r += f'\n ... checking {bold_original}'
                if os.path.exists(source_original):
                    if os.path.exists(target_original) and not overwrite:
                        f'\n ... {bold_original} already exists and overwrite is set to no, this file would be skipped'
                    report['ready'].append(bold_original)
                else:
                    r += f'\n ... WARNING: {bold_original} does not exist, rerun the preprocess_mice step'
                    report['not ready'].append(bold_original)

                # EPI
                r += f'\n ... checking {bold_epi}'
                if os.path.exists(source_epi):
                    if os.path.exists(target_epi) and not overwrite:
                        f'\n ... {bold_epi} already exists and overwrite is set to no, this file would be skipped'
                    report['ready'].append(bold_epi)
                else:
                    r += f'\n ... WARNING: {bold_epi} does not exist, rerun the preprocess_mice step'
                    report['not ready'].append(bold_epi)

                # ABI
                r += f'\n ... checking {bold_abi}'
                if os.path.exists(source_abi):
                    if os.path.exists(target_abi) and not overwrite:
                        f'\n ... {bold_abi} already exists and overwrite is set to no, skipping this file'
                    report['ready'].append(bold_abi)
                else:
                    r += f'\n ... WARNING: {bold_abi} does not exist, rerun the preprocess_mice step'
                    report['not ready'].append(bold_abi)

            r += '\n'

        rep = []
        for k in ['done', 'failed', 'ready', 'not ready']:
            if len(report[k]) > 0:
                rep.append(f'{", ".join(report[k])} {k}')

        report = (sinfo['id'], 'preprocess_mice: bolds ' + '; '.join(rep), len(report['failed'] + report['not ready']))

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = f'\n --- Failed during processing of session {session} with error:\n'
        r += str(errormessage)
        report = (sinfo['id'], 'map_mice_data failed', 1)

    except:
        r += f'n --- Failed during processing of session {session} with error:\n {traceback.format_exc()}\n'
        report = (sinfo['id'], 'map_mice_data failed', 1)

    return (r, report)
