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

"""
Created by Grega Repovs on 2017-09-16.
Copyright (c) Grega Repovs. All rights reserved.
"""

import os
import subprocess
from qx_registry import qx_commands


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

def run(qx_command, args):

    # -- prepare arguments

    arglist = []

    for arg in qx_command.args:

        if arg.name not in args:
            args[arg.name] = ''

        if any([arg.type.startswith(s) for s in ['string', 'str']]):
            if len(args[arg.name]) > 1 and args[arg.name][0] in ['[', '{']:
                arglist.append("%s" % (args[arg.name]))
            else:
                arglist.append("'%s'" % (args[arg.name]))
        
        elif any([arg.type.startswith(s) for s in ['int', 'integer', 'float', 'numeric', 'vector', 'matrix']]):
            if args[arg.name] == '':
                arglist.append("[]")
            else:
                arglist.append("%s" % (args[arg.name]))

        elif arg.type.startswith('cell'):
            if args[arg.name] == '':
                arglist.append("{}")
            else:
                arglist.append("%s" % (args[arg.name]))
        
        elif arg.type.startswith('bool'):
            if args[arg.name] == '':
                arglist.append("[]")
            else:
                arglist.append("%s" % (args[arg.name]))

    # -- compose command string

    mcom = "%s(%s)" % (qx_command.name, ", ".join(arglist))
    com = '%s "try %s; catch ME; fprintf(\'\\nMatlab Error! Processing Failed!\\n%%s\\n\', ME.message); exit(1), end; exit"' % (mcommand, mcom)


    # --- parse output options

    sout = None
    serr = None

    if "saveOutput" in args:
        output = args['saveOutput']
        if 'return' in output:
            serr = subprocess.STDOUT
            sout = subprocess.PIPE
        elif 'both' in output:
            serr = subprocess.STDOUT
            sout = open(output.split(':')[1].strip(), 'a')
        else:
            for k, v in [[f.strip() for f in e.split(":")] for e in output.split("|")]:
                if k == 'stdout':
                    sout = open(v, 'a')
                elif k == 'stderr':
                    serr = open(v, 'a')

    # --- run command

    print("\nRunning:\n>>> %s\n" % (mcom))

    ret = subprocess.call(com, shell=True, stdout=sout, stderr=serr)

    if ret:
        print("\n\nERROR: %s failed! Please check output / log!\n" % (qx_command.name))
    else:
        print("\n\n---> Successful completion of task\n")
