#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``simple.py``

This file holds code for support functions for image preprocessing and analysis.
It consists of functions:

--create_bold_list  ... Creates a list with paths to each session's BOLD files.
--create_conc_list  ... Creates a list with paths to each session's conc files.
--list_session_info ... Lists session data stored in batch.txt file.

All the functions are part of the processing suite. They should be called from
the command line using `qunex` command. Help is available through:

- `qunex ?<command>` for command specific help
"""

# Created by Grega Repovs on 2016-12-17.
# Code split from dofcMRIp_core gCodeP/preprocess codebase.
# Copyright (c) Grega Repovs. All rights reserved.

import os
import re
from datetime import datetime

import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog


def create_bold_list(sinfo, options, overwrite=False, thread=0):
    """
    ``create_bold_list [... processing options]``

    Create a list with paths to each session's processed BOLD files.

    ..  qx_command:
        type: processing.study

    Parameters:
        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder.

        --bold_prefix (str, default ''):
            An optional prefix added to the output filename.

        --bolds (str, default ''):
            Pipe-separated list of task names to include (e.g. "rest|task").
    """
    bfile = open(os.path.join(options['sessionsfolder'], 'boldlist' + options['bold_prefix'] + '.list'), 'w')
    bsearch = re.compile(r'bold([0-9]+)')

    for session in sinfo:
        bolds = []
        for (k, v) in session.items():
            if k.isdigit():
                bnum = bsearch.match(v['name'])
                if bnum:
                    if v['task'] in options['bolds'].split("|"):
                        bolds.append(v['name'])
        if len(bolds) > 0:
            f = pc.get_file_names(session, options)
            print("    session id:%s" % (session['id']), file=bfile)
            print("    roi:%s" % (os.path.abspath(f['fs_aparc_bold'])), file=bfile)
            for bold in bolds:
                f = pc.get_bold_file_names(session, boldname=bold, options=options)
                print("    file:%s" % (os.path.abspath(f['bold_final'])), file=bfile)

    bfile.close()


def create_conc_list(sinfo, options, overwrite=False, thread=0):
    """
    ``create_conc_list [... processing options]``

    Create a list with paths to each session's conc files.

    ..  qx_command:
        type: processing.study

    Parameters:
        --sessionsfolder (str):
            The path to study sessions folder.

        --bold_prefix (str):
            An optional prefix to place in front of processing name extensions
            in the resulting files.

        --bolds (str):
            Which bolds to process (can be multiple joind with '|' ).

        --event_file (str):
            The root name of the fidl event file for task regression.

    """
    bfile = open(os.path.join(options['sessionsfolder'], 'conclist' + options['bold_prefix'] + '.list'), 'w')

    concs = options['bolds'].split("|")
    fidls = options['event_file'].split("|")

    if len(concs) != len(fidls):
        print("\nWARNING: Number of conc files (%d) does not match number of event files (%d), processing aborted!" % (len(concs), len(fidls)))

    else:
        for session in sinfo:
            try:
                f = pc.get_file_names(session, options)
                d = pc.get_session_folders(session, options)

                print("session id:%s" % (session['id']), file=bfile)
                print("    roi:%s" % (f['fs_aparc_bold']), file=bfile)

                tfidl  = fidls[0].strip().replace(".fidl", "")

                f_conc = os.path.join(d['s_bold_concs'], f['conc_final'])
                f_fidl = os.path.join(d['s_bold_events'], tfidl + ".fidl")

                print("    fidl:%s" % (f_fidl), file=bfile)
                print("    file:%s" % (f_conc), file=bfile)

            except Exception:
                print("ERROR processing session %s!" % (session['id']))
                raise

    bfile.close()


def list_session_info(sinfo, options, overwrite=False, thread=0):
    """
    ``list_session_info [... processing options]``

    List session id and group from the batch file selection.

    ..  qx_command:
        type: processing.study

    Parameters:
        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder.
    """
    bfile = open(os.path.join(options['sessionsfolder'], 'session_info.txt'), 'w')

    for session in sinfo:
        print("session: %s, group: %s" % (session['id'], session['group']), file=bfile)

    bfile.close()


def run_shell_script(sinfo, options, overwrite=False, thread=0):
    """
    ``run_shell_script [... processing options]``

    Run the specified script on every selected session from batch.txt file.

    ..  qx_command:
        type: processing.session

    Parameters:
        --script (str):
            The path to the script to be executed.

        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing outputs (yes) or not (no).

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.


    Notes:
        run_shell_script runs the specified script on every selected session from
        batch.txt file. It places the specified session specific information
        before running the script. The information to be added is to be referenced
        in the script using double curly braces: {{<key>}}. Specifically, the
        function loops through all the session specific information as well as all
        the processing parameters and places them into the script. If the
        information is not provided, the {{<key>}} will remain as is.

        Example:

        If batch.txt contains among others::

            ---
            id: OP578
            subject: OP578
            dicom: /data/qx_study/sessions/OP578/dicom
            raw_data: /data/qx_study/sessions/OP578/nii
            hcp: /data/qx_study/sessions/OP578/hcp
            group: control

        If script.sh contains among others::

            ls -l {{hcp}}/{{id}}/MNINonLinear
            if [ "{{group}}" = "control" ]; then
                mkdir /data/tmp/{{id}}
                cp {{raw_data}}/*.nii.gz /data/tmp/{{id}}
            fi
            echo "{{nothing}}"

        Before running the function will change that part of the script to::

            ls -l /data/qx_study/sessions/OP578/hcp/OP578/MNINonLinear
            if [ "control" = "control" ]; then
                mkdir /data/tmp/OP578
                cp /data/qx_study/sessions/OP578/nii/*.nii.gz /data/tmp/OP578
            fi
            echo "{{nothing}}"

    Examples:

        ::

            qunex run_shell_script sessions=fcMRI/session_hcp.txt sessionsfolder=sessions \\
                  overwrite=no script=fcMRI/processdata.sh
    """
    log = ReportLog()

    log.capture("\n---------------------------------------------------------")
    log.raw("\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S")))
    log.raw("\nRunning script %s" % (options['script']))
    log.raw("\n........................................................\n")

    try:
        assert (options['script'] is not None), "ERROR: No script was referenced!"
        assert (os.path.exists(options['script'])), "ERROR: The referenced script does not exist in the path provided!"

        file = open(options['script'], 'r')
        script = file.read()

        # --- place session specific data

        for key, value in sinfo.items():
            if not key.isdigit():
                script = script.replace("{{%s}}" % (key), str(value))

        # --- place options

        for key, value in options.items():
            if not key.isdigit():
                script = script.replace("{{%s}}" % (key), str(value))

        # --- check for nonplaced

        nonplaced = re.findall("{{.*?}}", script)

        if nonplaced:
            log.raw("\nWARNING: the following tags were not filled:")
            for n in nonplaced:
                log.raw("\n ... " + n)

        # --- execute script

        description = "run_shell_script: %s" % (options['script'])
        task = "run_shell_script-%s" % (options['script'])

        log.raw(pc.run_script_through_shell(script, description, thread=sinfo['id'], remove=options['log'] == 'remove', task=task, logfolder=options['comlogs']))

    except AssertionError as message:
        log.raw(str(message) + "\n---------------------------------------------------------")
        print(log.text)
        return (log.text, (sinfo['id'], message, 1))

    except pc.ExternalFailed as errormessage:
        log.raw(str(errormessage) + "\n---------------------------------------------------------")
        print(log.text)
        return (log.text, (sinfo['id'], "Failed: " + str(errormessage), 1))

    except Exception:
        message = 'ERROR: Error in parsing or executing script %s' % (options['script'])
        log.raw("\n" + message + "\n---------------------------------------------------------")
        print(log.text)
        raise
        return (log.text, (sinfo['id'], message, 1))

    log.raw("\n\nrun_shell_script %s completed on %s\n---------------------------------------------------------" % (options['script'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S")))
    print(log.text)
    return (log.text, (sinfo['id'], "Ran %s without errors" % (options['script']), 0))
