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
--run_shell_script  ... Runs a script on every selected session.

All the functions are part of the processing suite. They should be called from
the command line using `qunex` command. Help is available through:

- `qunex <command> --help` for command specific help
"""

# Created by Grega Repovs on 2016-12-17.
# Code split from dofcMRIp_core gCodeP/preprocess codebase.
# Copyright (c) Grega Repovs. All rights reserved.

import os
import re
from datetime import datetime

import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog, action


def _write_list(_log, options, path, lines):
    """
    Write a list file, or -- under ``--test`` -- report it and write nothing.

    The list is built in full before it is written, so neither a dry run nor
    a command that stops partway leaves an existing list emptied or half
    written. Returns whether the file was written.
    """
    if options["run"] != "run":
        _log.detail(f"test, not written: {path}")
        return False

    with open(path, "w") as listfile:
        for line in lines:
            print(line, file=listfile)

    return True


def create_bold_list(sinfo, options, overwrite=False, thread=0):
    """
    ``create_bold_list [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Create a list with paths to each session's processed BOLD files.

    ..  qx_command:
        type: processing.study

    Parameters:
        --studyfolder (str):
            The path to the study folder. The sessions are in its `sessions`
            folder, unless --sessionsfolder names another one.

        --sessionsfolder (str, default '<studyfolder>/sessions'):
            The path to the folder with the sessions. Set it only when the
            sessions are not in the `sessions` folder of the study. With
            neither --studyfolder nor --sessionsfolder given, the current
            folder is used. The list is written into it, as
            `boldlist<bold_prefix>.list`.

        --bold_prefix (str, default ''):
            An optional prefix added to the output filename.

        --bolds (str, default ''):
            Pipe-separated list of task names to include (e.g. "rest|task").

    Examples:
        ::

            qunex create_bold_list \\
                --studyfolder="/data/qunex_study" \\
                --batchfile="/data/qunex_study/processing/batch.txt" \\
                --bolds="rest"
    """
    log = ReportLog()

    listfile = os.path.join(options['sessionsfolder'], 'boldlist' + options['bold_prefix'] + '.list')
    lines = []
    bsearch = re.compile(r'bold([0-9]+)')

    nsessions = 0
    nbolds = 0

    for session in sinfo:
        nsessions += 1
        bolds = []
        for (k, v) in session.items():
            if k.isdigit():
                bnum = bsearch.match(v['name'])
                if bnum:
                    if v['task'] in options['bolds'].split("|"):
                        bolds.append(v['name'])
        if len(bolds) > 0:
            f = pc.get_file_names(session, options, _log=log)
            lines.append("    session id:%s" % (session['id']))
            lines.append("    roi:%s" % (os.path.abspath(f['fs_aparc_bold'])))
            for bold in bolds:
                f = pc.get_bold_file_names(session, boldname=bold, options=options)
                lines.append("    file:%s" % (os.path.abspath(f['bold_final'])))
            nbolds += len(bolds)

    # the list itself is the command's product; the report says what went into
    # it, not what it says
    log.step(f"processed {nsessions} sessions")
    if _write_list(log, options, listfile, lines):
        log.step(f"wrote {listfile} with {nbolds} bolds in total")

    return log.finish(action("wrote a bold list with %d bolds from %d sessions" % (nbolds, nsessions), options['run']))


def create_conc_list(sinfo, options, overwrite=False, thread=0):
    """
    ``create_conc_list [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Create a list with paths to each session's conc files.

    ..  qx_command:
        type: processing.study

    Parameters:
        --studyfolder (str):
            The path to the study folder. The sessions are in its `sessions`
            folder, unless --sessionsfolder names another one.

        --sessionsfolder (str, default '<studyfolder>/sessions'):
            The path to the folder with the sessions. Set it only when the
            sessions are not in the `sessions` folder of the study. With
            neither --studyfolder nor --sessionsfolder given, the current
            folder is used. The list is written into it, as
            `conclist<bold_prefix>.list`.

        --bold_prefix (str):
            An optional prefix to place in front of processing name extensions
            in the resulting files.

        --bolds (str):
            Which bolds to process (can be multiple joined with '|' ).

        --event_file (str):
            The root name of the fidl event file for task regression.

    """
    log = ReportLog()

    listfile = os.path.join(options['sessionsfolder'], 'conclist' + options['bold_prefix'] + '.list')
    lines = []

    concs = options['bolds'].split("|")
    fidls = options['event_file'].split("|")

    nsessions = 0

    if len(concs) != len(fidls):
        log.warning(f"Number of conc files ({len(concs)}) does not match number of event files ({len(fidls)}), processing aborted!")
        return log.result("aborted: %d conc files but %d event files" % (len(concs), len(fidls)), 1)

    else:
        for session in sinfo:
            nsessions += 1
            try:
                f = pc.get_file_names(session, options, _log=log)
                d = pc.get_session_folders(session, options)

                lines.append("session id:%s" % (session['id']))
                lines.append("    roi:%s" % (f['fs_aparc_bold']))

                tfidl  = fidls[0].strip().replace(".fidl", "")

                f_conc = os.path.join(d['s_bold_concs'], f['conc_final'])
                f_fidl = os.path.join(d['s_bold_events'], tfidl + ".fidl")

                lines.append("    fidl:%s" % (f_fidl))
                lines.append("    file:%s" % (f_conc))

            except Exception:
                log.error(f"processing session {session['id']}!")
                # the report is lost when the command aborts by exception --
                # showing it is the only thing that survives the raise
                print(log.text)
                raise

    _write_list(log, options, listfile, lines)

    return log.finish(action("wrote a conc list for %d sessions" % (nsessions), options['run']))


def list_session_info(sinfo, options, overwrite=False, thread=0):
    """
    ``list_session_info [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    List session id and group from the batch file selection.

    ..  qx_command:
        type: processing.study

    Parameters:
        --studyfolder (str):
            The path to the study folder. The sessions are in its `sessions`
            folder, unless --sessionsfolder names another one.

        --sessionsfolder (str, default '<studyfolder>/sessions'):
            The path to the folder with the sessions. Set it only when the
            sessions are not in the `sessions` folder of the study. With
            neither --studyfolder nor --sessionsfolder given, the current
            folder is used. The list is written into it, as
            `session_info.txt`.

    Examples:
        ::

            qunex list_session_info \\
                --studyfolder="/data/qunex_study" \\
                --batchfile="/data/qunex_study/processing/batch.txt"
    """
    log = ReportLog()

    listfile = os.path.join(options['sessionsfolder'], 'session_info.txt')
    lines = []

    nsessions = 0
    for session in sinfo:
        # a session's group is optional in a batch file
        lines.append("session: %s, group: %s" % (session['id'], session.get('group', '')))
        nsessions += 1

    # the listing itself is the command's product; the report says what went
    # into it, not what it says
    log.step(f"listed {nsessions} sessions")
    if _write_list(log, options, listfile, lines):
        log.step(f"wrote {listfile}")

    return log.finish("listed %d sessions" % (nsessions))


def run_shell_script(sinfo, options, overwrite=False, thread=0):
    """
    ``run_shell_script [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

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
        the processing parameters (among them {{studyfolder}} and
        {{sessionsfolder}}) and places them into the script. If the
        information is not provided, the {{<key>}} will remain as is.

        A session's folders (dicom, raw_data, data, hcp, ...) are placed as
        absolute paths. A batch file records them relative to the session's
        own folder (`<sessionsfolder>/<session id>`), and they are resolved
        against it before they are placed.

        With --test, the script is not run. The runlog shows it as it would
        be run, with the information placed.

        Example:

        If batch.txt of the study in /data/qx_study contains among others::

            ---
            id: OP578
            subject: OP578
            dicom: dicom
            raw_data: nii
            hcp: hcp
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

            qunex run_shell_script \\
                --studyfolder=. \\
                --batchfile=processing/batch.txt \\
                --overwrite=no \\
                --script=processing/scripts/processdata.sh
    """
    log = ReportLog()

    log.rule()
    log.info(f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]")
    log.info(f"Running script {options['script']}")
    log.raw("\n........................................................\n")

    try:
        assert (options['script'] is not None), "ERROR: No script was referenced!"
        assert (os.path.exists(options['script'])), "ERROR: The referenced script does not exist in the path provided!"

        with open(options['script'], 'r') as file:
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
            log.warning("the following tags were not filled:")
            for n in nonplaced:
                log.detail(n)

        # --- execute script

        # the comlog is named after the script's file name: a folder in its
        # name would point the comlog into folders that do not exist
        description = "run_shell_script: %s" % (options['script'])
        task = "run_shell_script-%s" % (os.path.basename(options['script']))

        if options['run'] != 'run':
            # a dry run shows the script as it would have been run
            log.raw("\n\n%s" % (description))
            log.detail("test, not run: %s" % (options['script']), depth=1)
            log.raw("\n%s" % (script.rstrip("\n")))
        else:
            # the run's comlogs folder and the --comlog_folders destinations,
            # resolved into the list the comlog is written to and copied into.
            # Only after the script is filled in, so that {{comlogs}} is still
            # the run's comlogs folder rather than that list
            pc.do_options_check(options, sinfo, "run_shell_script")
            pc.run_script_through_shell(script, description, log, thread=sinfo['id'], remove=options['log'] == 'remove', task=task, logfolder=options['comlogs'])

    except AssertionError as message:
        log.raw(str(message))
        log.rule()
        return log.result(str(message), 1, sinfo['id'])

    except pc.ExternalFailed as errormessage:
        log.raw(str(errormessage))
        log.rule()
        return log.result("Failed: " + str(errormessage), 1, sinfo['id'])

    except Exception:
        message = 'ERROR: Error in parsing or executing script %s' % (options['script'])
        log.raw("\n" + message)
        log.rule()
        # the report is lost when the command aborts by exception -- showing it
        # is the only thing that survives the raise
        print(log.text)
        raise

    log.blank()
    completed = action("run_shell_script %s completed" % (options['script']), options['run'])
    log.info(f"{completed} on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}")
    log.rule()
    return log.result(action("Ran %s without errors" % (options['script']), options['run']), 0, sinfo['id'])
