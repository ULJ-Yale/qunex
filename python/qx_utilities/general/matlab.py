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
from general import extensions


if "QUNEXMCOMMAND" not in os.environ:
    print("WARNING: QUNEXMCOMMAND environment variable not set. Matlab will be run by default!")
    mcommand = "matlab -nodisplay -nosplash -r"
else:
    mcommand = os.environ['QUNEXMCOMMAND']

# ==============================================================================
#                                                                      FUNCTIONS

# A dictionary of Matlab functions that can be run is provided. Each function is
# referenced with its name and provides information on arguments that are to be
# passed to it.

functions = {
    'general_parcellated2dense':       [('inimg', 'string'), ('outimg', 'string'), ('verbose', 'bool'), ('missingvalues', 'string')],
    'general_extract_glm_volumes':     [('flist', 'string'), ('outf', 'string'), ('effects', 'string'), ('frames', 'numeric'), ('saveoption', 'string'), ('values', 'string'), ('verbose', 'bool'), ('txtf', 'string')],
    'general_glm_predict':             [('flist', 'string'), ('effects', 'string'), ('targetf', 'string'), ('options', 'string')],
    'general_compute_bold_list_stats': [('flist', 'string'), ('target', 'string'), ('store', 'string'), ('scrub', 'string'), ('verbose', 'bool')],
    'general_compute_bold_stats':      [('img', 'string'), ('mask', 'string'), ('target', 'string'), ('store', 'string'), ('scrub', 'string'), ('verbose', 'bool')],
    'general_compute_group_bold_stats': [('flist', 'string'), ('tfile', 'string'), ('stats', 'string'), ('inmask', 'string'), ('ignore', 'string')],
    'general_convert_cifti':           [('fin', 'string'), ('fout', 'string'), ('output_format', 'string'), ('atlas', 'string'), ('parcel_method', 'string'), ('verbose', 'bool')],
    'general_extract_roi_glm_values':  [('flist', 'string'), ('roif', 'string'), ('outf', 'string'), ('effects', 'string'), ('frames', 'numeric'), ('values', 'string'), ('tformat', 'string'), ('verbose', 'bool')],
    'general_extract_roi_values':      [('roif', 'string'), ('mfs', 'string'), ('sefs', 'string'), ('vnames', 'string'), ('output', 'string'), ('stats', 'string'), ('verbose', 'bool')],
    'general_find_peaks':              [('fin', 'string'), ('fout', 'string'), ('mins', 'numeric'), ('maxs', 'numeric'), ('val', 'string'), ('t', 'numeric'), ('presmooth', 'string'), ('projection', 'string'), ('options', 'string'), ('verbose', 'bool')],
    'general_plot_bold_timeseries':    [('images', 'string'), ('elements', 'string'), ('masks', 'string'), ('filename', 'string'), ('skip', 'numeric'), ('sessionid', 'string'), ('verbose', 'bool')],
    'general_plot_bold_timeseries_list': [('flist', 'string'), ('elements', 'string'), ('filename', 'string'), ('skip', 'numeric'), ('fformat', 'string'), ('verbose', 'bool')],
    'general_qa_concfile':             [('file', 'string'), ('do', 'string'), ('target', 'string')],
    'general_image_conjunction':       [('imgf', 'string'), ('maskf', 'string'), ('method', 'string'), ('effect', 'string'), ('q', 'numeric'), ('data', 'string'), ('psign', 'string')],
    'general_image_overlap':           [('af', 'string'), ('bf', 'string'), ('tf', 'string'), ('v', 'numeric')],
    'fc_compute_ab_corr':              [('flist', 'string'), ('smask', 'string'), ('tmask', 'string'), ('mask', 'numeric'), ('root', 'string'), ('options', 'string'), ('verbose', 'bool')],
    'fc_compute_ab_corr_kca':          [('flist', 'string'), ('smask', 'string'), ('tmask', 'string'), ('nc', 'numeric'), ('mask', 'numeric'), ('root', 'string'), ('options', 'string'), ('dmeasure', 'string'), ('nrep', 'numeric'), ('verbose', 'bool')],
    'fc_compute_gbc3':                 [('flist', 'string'), ('command', 'string'), ('mask', 'numeric'), ('verbose', 'bool'), ('target', 'string'), ('targetf', 'string'), ('rsmooth', 'numeric'), ('rdilate', 'numeric'), ('ignore', 'string'), ('time', 'string'), ('cv', 'string'), ('vstep', 'numeric')],
    'fc_compute_gbcd':                 [('flist', 'string'), ('command', 'string'), ('roi', 'string'), ('rcodes', 'numeric'), ('nbands', 'numeric'), ('mask', 'numeric'), ('verbose', 'bool'), ('target', 'string'), ('targetf', 'string'), ('rsmooth', 'numeric'), ('rdilate', 'numeric'), ('ignore', 'string'), ('time', 'string'), ('method', 'string'), ('weights', 'string'), ('criterium', 'string')],
    'fc_extract_roi_timeseries':       [('flist', 'string'), ('roiinfo', 'string'), ('frames', 'string'), ('targetf', 'string'), ('options', 'string')],
    'fc_compute_roifc':                [('flist', 'string'), ('roiinfo', 'string'), ('frames', 'string'), ('targetf', 'string'), ('options', 'string')],
    'fc_compute_gbc':                  [('flist', 'string'), ('command', 'string'), ('sroiinfo', 'string'), ('troiinfo', 'string'), ('frames', 'string'), ('targetf', 'string'), ('options', 'string')],
    'fc_compute_seedmaps':             [('flist', 'string'), ('roiinfo', 'string'), ('frames', 'string'), ('targetf', 'string'), ('options', 'string')],
    'fc_compute_seedmaps_multiple':    [('flist', 'string'), ('roiinfo', 'string'), ('inmask', 'numeric'), ('options', 'string'), ('targetf', 'string'), ('method', 'string'), ('ignore', 'string'), ('cv', 'string')],
    'fc_extract_roi_timeseries_masked':   [('flist', 'string'), ('roiinfo', 'string'), ('inmask', 'string'), ('targetf', 'string'), ('options', 'string'), ('method', 'string'), ('ignore', 'string'), ('rcodes', 'string'), ('mcodes', 'string'), ('bmask', 'string')],
    'fc_extract_trial_timeseries_masked': [('flist', 'string'), ('roif', 'string'), ('targetf', 'string'), ('tevents', 'string'), ('frames', 'numeric'), ('scrubvar', 'string')],
    'fc_segment_mri':                  [('flist', 'string'), ('smask', 'string'), ('tmask', 'string'), ('mask', 'numeric'), ('root', 'string'), ('options', 'string'), ('verbose', 'string')],
    'fc_preprocess':                   [('sessionf', 'string'), ('bold', 'numeric'), ('omit', 'numeric'), ('do', 'string'), ('rgss', 'string'), ('task', 'string'), ('efile', 'string'), ('tr', 'numeric'), ('eventstring', 'string'), ('variant', 'string'), ('overwrite', 'string'), ('tail', 'string'), ('scrub', 'string'), ('ignores', 'string'), ('options', 'string')],
    'fc_preprocess_conc':              [('sessionf', 'string'), ('bolds', 'numeric'), ('do', 'string'), ('tr', 'numeric'), ('omit', 'string'), ('rgss', 'string'), ('task', 'string'), ('efile', 'string'), ('eventstring', 'string'), ('variant', 'string'), ('overwrite', 'string'), ('tail', 'string'), ('scrub', 'string'), ('ignores', 'string'), ('options', 'string'), ('done', 'string')],
    'stats_compute_behavioral_correlations': [('imgfile', 'string'), ('datafile', 'string'), ('target', 'string')],
    'stats_p2z':                       [('img', 'string'), ('out', 'string'), ('tail', 'string')],
    'stats_ttest_dependent':           [('filea', 'string'), ('fileb', 'string'), ('target', 'string'), ('output', 'string'), ('exclude', 'string'), ('verbose', 'bool')],
    'stats_ttest_independent':         [('filea', 'string'), ('fileb', 'string'), ('target', 'string'), ('output', 'string'), ('vartype', 'string'), ('exclude', 'string'), ('verbose', 'bool')],
    'stats_ttest_zero':                [('dfile', 'string'), ('output', 'string'), ('exclude', 'string'), ('verbose', 'bool')],
}

# -- update functions with information from extensions
functions.update(extensions.compile_dict('functions')) 

functionList = sorted(functions.keys())




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

def run(command, args):

    # -- prepare arguments

    arglist = []

    for arg, form in functions[command]:

        if arg not in args:
            args[arg] = ''

        if form == 'string':
            if len(args[arg]) > 1 and args[arg][0] in ['[', '{']:
                arglist.append("%s" % (args[arg]))
            else:
                arglist.append("'%s'" % (args[arg]))
        elif form == 'numeric':
            if args[arg] == '':
                arglist.append("[]")
            else:
                arglist.append("%s" % (args[arg]))
        elif form == 'cell':
            if args[arg] == '':
                arglist.append("{}")
            else:
                arglist.append("%s" % (args[arg]))
        elif form == 'bool':
            if args[arg] == '':
                arglist.append("[]")
            else:
                arglist.append("%s" % (args[arg]))

    # -- compose command string

    mcom = "%s(%s)" % (command, ", ".join(arglist))
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
        print("\n\nERROR: %s failed! Please check output / log!\n" % (command))
    else:
        print("\n\n---> Successful completion of task\n")
