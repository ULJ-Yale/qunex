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
import subprocess


# ==============================================================================
#                                                              RUNNING FUNCTIONS
#

def run(qx_command, args):

    # -- resolve script path

    script = os.path.join(os.environ.get('QUNEXPATH', ''), 'bash', qx_command.path)

    if not os.path.exists(script):
        print("\n\nERROR: %s failed! Script not found: %s\n" % (qx_command.name, script))
        return

    # -- compose command string

    arglist = []

    for key, value in args.items():
        if value is True:
            arglist.append("--%s" % (key))
        else:
            arglist.append("--%s='%s'" % (key, value))

    com = " ".join(["bash", script] + arglist)

    # -- run command

    print("\nRunning:\n>>> %s\n" % (com))

    ret = subprocess.call(com, shell=True)

    if ret:
        print("\n\nERROR: %s failed! Please check output / log!\n" % (qx_command.name))
    else:
        print("\n\n---> Successful completion of task\n")
