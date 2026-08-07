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

def run(qx_command, args, run=None):
    """
    Runs a bash command, keeping its output in a comlog of its own.

    The comlog is renamed by the exit status, so a failed script is visible in
    the file listing, and the outcome is recorded in the runlog.

    For internal use only.
    """

    # -- resolve script path

    script = os.path.join(os.environ.get('QUNEXPATH', ''), 'bash', qx_command.path)

    if not os.path.exists(script):
        print("\n\nERROR: %s failed! Script not found: %s\n" % (qx_command.name, script))
        return

    # -- compose command string

    arglist = []

    for key, value in args.items():
        # the run-level parameters steer how qunex runs the command, not what
        # the script does; none of the registered scripts reads them
        if key in gcs.extra_parameters and not qx_command.has_arg(key):
            continue
        if value is True:
            arglist.append("--%s" % (key))
        else:
            arglist.append("--%s='%s'" % (key, value))

    com = " ".join(["bash", script] + arglist)

    # -- run command, keeping the output

    print("\nRunning:\n>>> %s\n" % (com))

    ret = gl.run_and_log(com, qx_command.name, run=run)

    if ret:
        print("\n\nERROR: %s failed! Please check output / log!\n" % (qx_command.name))
    else:
        print("\n\n---> Successful completion of task\n")
