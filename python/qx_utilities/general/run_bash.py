#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``run_bash.py``

This file holds the functions and settings for providing a wrapper to run
QuNex/bash code.

None of the code is run directly from the terminal interface.
"""

import os

import qx_utilities.general.commands_support as gcs
import qx_utilities.general.log as gl


# ==============================================================================
#                                                              RUNNING FUNCTIONS
#

# What goes in a comlog's name besides the command and the session, so that two
# runs of one command in one log folder are told apart. This is the shell front
# end's `logtag` (`bin/qunex.sh:170-189`), and it is not cosmetic: `run_qc` is
# run once per modality into one log folder, so without the modality the four
# QC runs of a session would all be filed under `run_qc_<session>` and overwrite
# each other. The names are `run_qc_t1w`, `run_qc_bold`, `run_qc_dwi`.
COMLOG_TAGS = ("calculation", "modality")


def comlog_name(qx_command, args, session=None):
    """The name this call's comlog is filed under: the command, the parameters
    that tell two of its runs apart, and the session."""
    tags = [str(args[tag]).lower() for tag in COMLOG_TAGS if args.get(tag)]
    return "_".join([qx_command.name] + tags + ([session] if session else []))


def session_parameter(qx_command):
    """
    The name under which a bash script is handed a single session: `session`
    when it declares that, `sessions` otherwise. The two spellings are used
    interchangeably across the scripts; the registry says which one each of
    them reads.
    """
    return "session" if "session" in gcs.declared_parameters(qx_command) else "sessions"


def run(qx_command, args, run=None, session=None):
    """
    Runs a bash command, keeping its output in a comlog of its own.

    The comlog is renamed by the exit status, so a failed script is visible in
    the file listing, and the outcome is recorded in the runlog.

    Parameters:
        qx_command: the registry entry of the command to run.
        args: the parameters to call it with.
        run: the run context that owns this run's logs.
        session: the session to run it on, when the caller is running the
            script once per session. It replaces whatever session
            specification `args` carries, under the name the script reads.

    For internal use only.
    """

    # -- resolve script path

    script = os.path.join(os.environ.get('QUNEXPATH', ''), 'bash', qx_command.path)

    if not os.path.exists(script):
        print("\n\nERROR: %s failed! Script not found: %s\n" % (qx_command.name, script))
        return 1

    # -- compose command string

    declared = gcs.declared_parameters(qx_command)

    if session:
        args = {k: v for k, v in args.items() if k not in ["session", "sessions"]}
        args[session_parameter(qx_command)] = session

    arglist = []

    for key, value in args.items():
        # the run-level parameters steer how qunex runs the command, not what
        # the script does. Asked of what the command declares rather than of
        # its signature: a bash command has no signature, its parameters are
        # documented ones, so `has_arg` was False for every one of them and a
        # script was called with none of the parameters it shares with the run
        if key in gcs.extra_parameters and key not in declared:
            continue
        if value is True:
            arglist.append("--%s" % (key))
        else:
            arglist.append("--%s='%s'" % (key, value))

    com = " ".join(["bash", script] + arglist)

    # -- run command, keeping the output

    print("\nRunning:\n>>> %s\n" % (com))

    ret = gl.run_and_log(com, comlog_name(qx_command, args, session), run=run)

    if ret:
        print("\n\nERROR: %s failed! Please check output / log!\n" % (qx_command.name))
    else:
        print("\n\n---> Successful completion of task\n")

    # the caller writes the run's status record from this; printing it was all
    # that used to be done with it
    return ret
