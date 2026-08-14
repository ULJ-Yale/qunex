#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2022 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later


"""
``bruker.py``

This file holds code for converting and onboarding bruker data into QuNex. It
consists of functions:

- bruker_to_dicom Converts bruker data into DICOM.

All the functions are part of the processing suite. They should be called
from the command line using `qunex` command. Help is available through:

- ``qunex <command> --help`` for command specific help
- ``qunex -o`` for a list of relevant arguments and options

There are additional support functions that are not to be used
directly.
"""

# Copyright (c) Jure Demsar, Jie Lisa Ji and Valerio Zerbi
# All rights reserved.

# general imports
import os
import re
import shutil

# qx imports
import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl


def bruker_to_dicom(sessionsfolder=None, inbox=None, sessions=None, archive='leave', parelements=1, _log=None):
    """
    ``bruker_to_dicom [... processing options]``

    Convert bruker data into DICOM format for QuNex import.

    ..  qx_command:
        type: utility

    Parameters:
        --sessionsfolder (str, default '.'):
            The sessions folder where all the sessions are to be mapped to. It
            should be a folder within the <study folder>.

        --inbox (str, default '<sessionsfolder>/inbox/bruker'):
            The location of the folder with bruker datasets.

        --sessions (str, default ''):
            An optional parameter that specifies a comma or pipe separated list
            of sessions from the inbox folder to be processed. Regular
            expression patterns can be used. If provided, only folders within
            the inbox that match the list of sessions will be processed.
            Note: the session will match if the string is found within the
            folder name. So 'S01' with match any folder that contains the string
            'S01'!

        --archive (str, default 'leave'):
            What to do with bruker data once it is converted. Options are:

            - move (move the package to the study's archive folder)
            - copy (copy the package to the study's archive folder)
            - leave (keep the package where it was)
            - delete (delete the package).

        --parelements (int, default 1):
            How many parallel processes to run the conversion with.

    Examples:
        ::

            qunex bruker_to_dicom \\
                --sessionsfolder='/data/mice_study/sessions' \\
                --sourcefolder='/data/raw/bruker' \\
                --sessions='S01,S02'

    """

    log = gl.log_or_console(_log)

    # `raw` because a title over its own rule is not a record shape; no
    # trailing newline, since every record that follows opens with one
    log.raw('\nRunning bruker_to_dicom\n=======================')

    # check inputs
    if archive not in ['leave', 'move', 'copy', 'delete']:
        raise ge.CommandError('bruker_to_dicom', 'Invalid dataset archive option', '%s is not a valid option for dataset archive option!' % (archive), 'Please specify one of: leave, move, copy, delete!')

    if sessionsfolder is None:
        sessionsfolder = os.path.abspath('.')

    if inbox is None:
        inbox = os.path.join(sessionsfolder, 'inbox', 'bruker')

    # verify inbox
    if not os.path.exists(inbox) or not os.path.isdir(inbox):
        raise ge.CommandError('bruker_to_dicom', 'Inbox does not exist or is not a folder!', f'{inbox} is not a valid option for the inbox parameter!')

    # check for folders
    if not os.path.exists(os.path.join(sessionsfolder, 'inbox', 'bruker')):
        os.makedirs(os.path.join(sessionsfolder, 'inbox', 'bruker'))
        log.step('creating inbox bruker folder')

    # archive
    archive_dir = os.path.join(sessionsfolder, 'archive', 'bruker')
    if not os.path.exists(os.path.join(sessionsfolder, 'archive', 'bruker')):
        os.makedirs(archive_dir)
        log.step('creating archive bruker folder')

    # identification of files
    if sessions:
        sessions = [e.strip() for e in re.split(r' +|\| *|, *', sessions)]

    log.step(f"identifying files in {inbox}")

    # prepare calls
    calls = []
    dirs = []

    # iterate over subfolders in inbox
    for d in os.listdir(inbox):
        source_path = os.path.join(inbox, d)
        # is it a directory
        if os.path.isdir(source_path):
            onboard = False

            # we onboard all or those that match the session regex
            if sessions is None:
                onboard = True
            else:
                for s in sessions:
                    if re.search(s, d):
                        onboard = True
                        break

            # onboard
            if onboard:
                log.blank()
                with log.section(f'importing {d}'):
                    # target path
                    target_path = os.path.join(sessionsfolder, 'inbox', 'MR', d)
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)

                    log_path = os.path.join(target_path, 'bruker_to_dicom.log')

                    if os.path.exists(log_path):
                        os.remove(log_path)

                    log.detail(f'importing to {target_path}')
                    log.detail(f'import log can be found at {log_path}')

                # dicomifier
                calls.append({'name': 'bruker_to_dicom: ' + d, 'args': ['dicomifier', 'to-dicom', source_path, target_path], 'sout': log_path})

                # add to list of imported dirs
                dir_dict = {
                    'session': d,
                    'source': source_path,
                }
                dirs.append(dir_dict)

    # execute
    log.blank()
    log.step('running conversions')
    done = gc.run_external_parallel(calls, cores=parelements, _log=log)

    # archive
    failed = []
    i = 0
    for call in done:
        session = dirs[i]['session']

        if call['exit'] != 0:
            # a session whose conversion exited non-zero used to get this line
            # and nothing else, so the command reported the failure and still
            # exited 0
            failed.append(session)
            log.error(f'failed import for {session}, inspect {call["log"]}')
        elif archive != 'leave':
            source_path =  dirs[i]['source']

            with log.section(f'archiving {session}'):
                if archive == 'move':
                    log.detail('moving dataset to archive')
                    shutil.move(source_path, archive_dir)
                elif archive == 'copy':
                    log.detail('copying dataset to archive')
                    shutil.copy2(source_path, archive_dir)
                elif archive == 'delete':
                    log.detail('deleting dataset')
                    shutil.rmtree(source_path)

        # index increase
        i += 1

    # raised after the loop, so one failing session does not abort its siblings
    if failed:
        raise ge.CommandFailed(
            'bruker_to_dicom',
            'Conversion failed',
            'Conversion to DICOM failed for %d of %d sessions: %s'
            % (len(failed), len(done), ', '.join(failed)),
            'Please check the report!',
        )
