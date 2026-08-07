#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``matlab.py``

This file holds the functions and settings for providing a wrapper to run
QuNex/matlab code.

None of the code is run directly from the terminal interface.
"""

# Created by Grega Repovs on 2017-09-16.
# Copyright (c) Grega Repovs. All rights reserved.

import os
import subprocess

import qx_utilities.general.log as gl


if "QUNEXMCOMMAND" not in os.environ:
    print("WARNING: QUNEXMCOMMAND environment variable not set. Matlab will be run by default!")
    mcommand = "matlab -nodisplay -nosplash -r"
else:
    mcommand = os.environ['QUNEXMCOMMAND']

# ==============================================================================
#                                                                     PRINT HELP
#


def help(command):
    """
    Prints help for the command using Matlab.
    """

    print("\nDisplaying help for Matlab function %s\n--------------------------------------------------------------------------------\n" % (command))
    com = '%s "help %s; exit"' % (mcommand, command)
    subprocess.call(com, shell=True)
    print("\n--------------------------------------------------------------------------------\n")


# ==============================================================================
#                                                              RUNNING FUNCTIONS
#

def run(qx_command, args, run=None):
    """
    Runs a matlab command, keeping its output in a comlog of its own.

    The comlog is renamed by the exit status, so a failed matlab call is
    visible in the file listing, and the outcome is recorded in the runlog.

    For internal use only.
    """

    # -- prepare arguments

    arglist = []

    for arg in qx_command.args:

        if arg.name not in args:
            args[arg.name] = ''

        # matlab args are positional, so every arg must append exactly one token,
        # else all following args shift; type may be None if not documented
        argtype = arg.type or ''
        value = args[arg.name]

        if argtype.startswith(('string', 'str')):
            if len(value) > 1 and value[0] in ['[', '{']:
                arglist.append("%s" % (value))
            else:
                arglist.append("'%s'" % (value))

        elif argtype.startswith(('int', 'integer', 'float', 'numeric', 'vector', 'matrix')):
            arglist.append("[]" if value == '' else "%s" % (value))

        elif argtype.startswith('cell'):
            arglist.append("{}" if value == '' else "%s" % (value))

        elif argtype.startswith('bool'):
            arglist.append("[]" if value == '' else "%s" % (value))

        else:
            # unknown or undocumented type: pass through (empty -> []), never drop the arg
            if not argtype:
                print(f"    ... WARNING: argument '{arg.name}' of {qx_command.name} has no documented type; passing value as-is")
            arglist.append("[]" if value == '' else "%s" % (value))

    # -- compose command string

    mcom = "%s(%s)" % (qx_command.name, ", ".join(arglist))
    com = '%s "try %s; catch ME; fprintf(\'\\nMatlab Error! Processing Failed!\\n%%s\\n\', ME.message); exit(1), end; exit"' % (mcommand, mcom)

    # --- run command, keeping the output

    print("\nRunning:\n>>> %s\n" % (mcom))

    ret = gl.run_and_log(com, qx_command.name, run=run)

    if ret:
        print("\n\nERROR: %s failed! Please check output / log!\n" % (qx_command.name))
    else:
        print("\n\n---> Successful completion of task\n")
