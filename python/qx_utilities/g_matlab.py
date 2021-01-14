#!/usr/bin/env python2.7
# encoding: utf-8
"""
``g_nitools.py``

This file holds the functions and settings for providing a wrapper to run
QuNex/nitools code.

None of the code is run directly from the terminal interface.
"""

"""
Created by Grega Repovs on 2017-09-16.
Copyright (c) Grega Repovs. All rights reserved.
"""

import os
import subprocess


if "QUNEXMCOMMAND" not in os.environ:
    print "WARNING: QUNEXMCOMMAND environment variable not set. Matlab will be run by default!"
    mcommand = "matlab -nodisplay -nosplash -r"
else:
    mcommand = os.environ['QUNEXMCOMMAND']

# ==============================================================================
#                                                                      FUNCTIONS

# A dictionary of Matlab functions that can be run is provided. Each function is
# referenced with its name and provides information on arguments that are to be
# passed to it.

functions = {
    'g_Parcellated2Dense':             [('inimg', 'string'), ('outimg', 'string'), ('verbose', 'bool'), ('missingvalues', 'string')],
    'g_ExtractGLMVolumes':             [('flist', 'string'), ('outf', 'string'), ('effects', 'string'), ('frames', 'numeric'), ('saveoption', 'string'), ('values', 'string'), ('verbose', 'bool')],
    'g_ComputeBOLDListStats':          [('flist', 'string'), ('target', 'string'), ('store', 'string'), ('scrub', 'string'), ('verbose', 'bool')],
    'g_ComputeBOLDStats':              [('img', 'string'), ('mask', 'string'), ('target', 'string'), ('store', 'string'), ('scrub', 'string'), ('verbose', 'bool')],
    'g_ComputeGroupBOLDStats':         [('flist', 'string'), ('tfile', 'string'), ('stats', 'string'), ('inmask', 'string'), ('ignore', 'string')],
    'g_ExtractGLMVolumes':             [('flist', 'string'), ('outf', 'string'), ('effects', 'string'), ('frames', 'numeric'), ('saveoption', 'string'), ('values', 'string'), ('verbose', 'bool'), ('txtf', 'string')],
    'g_ExtractROIGLMValues':           [('flist', 'string'), ('roif', 'string'), ('outf', 'string'), ('effects', 'string'), ('frames', 'numeric'), ('values', 'string'), ('tformat', 'string'), ('verbose', 'bool')],
    'g_ExtractROIValues':              [('roif', 'string'), ('mfs', 'string'), ('sefs', 'string'), ('vnames', 'string'), ('output', 'string'), ('stats', 'string'), ('verbose', 'bool')],
    'g_FindPeaks':                     [('fin', 'string'), ('fout', 'string'), ('mins', 'numeric'), ('maxs', 'numeric'), ('val', 'string'), ('t', 'numeric'), ('presmooth', 'string'), ('projection', 'string'), ('options', 'string'), ('verbose', 'bool')],
    'g_PlotBoldTS':                    [('images', 'string'), ('elements', 'string'), ('masks', 'string'), ('filename', 'string'), ('skip', 'numeric'), ('sessionid', 'string'), ('verbose', 'bool')],
    'g_PlotBoldTSList':                [('flist', 'string'), ('elements', 'string'), ('filename', 'string'), ('skip', 'numeric'), ('fformat', 'string'), ('verbose', 'bool')],
    'g_QAConcFile':                    [('file', 'string'), ('do', 'string'), ('target', 'string')],
    'g_ConjunctionG':                  [('imgf', 'string'), ('maskf', 'string'), ('method', 'string'), ('effect', 'string'), ('q', 'numeric'), ('data', 'string')],
    'qa_imgOverlap':                   [('af', 'string'), ('bf', 'string'), ('tf', 'string'), ('v', 'numeric')],
    'fc_ComputeABCorr':                [('flist', 'string'), ('smask', 'string'), ('tmask', 'string'), ('mask', 'numeric'), ('root', 'string'), ('options', 'string'), ('verbose', 'bool')],
    'fc_ComputeABCorrKCA':             [('flist', 'string'), ('smask', 'string'), ('tmask', 'string'), ('nc', 'numeric'), ('mask', 'numeric'), ('root', 'string'), ('options', 'string'), ('dmeasure', 'string'), ('nrep', 'numeric'), ('verbose', 'bool')],
    'fc_ComputeGBC3':                  [('flist', 'string'), ('command', 'string'), ('mask', 'numeric'), ('verbose', 'bool'), ('target', 'string'), ('targetf', 'string'), ('rsmooth', 'numeric'), ('rdilate', 'numeric'), ('ignore', 'string'), ('time', 'string'), ('cv', 'string'), ('vstep', 'numeric')],
    'fc_ComputeGBCd':                  [('flist', 'string'), ('command', 'string'), ('roi', 'string'), ('rcodes', 'numeric'), ('nbands', 'numeric'), ('mask', 'numeric'), ('verbose', 'bool'), ('target', 'string'), ('targetf', 'string'), ('rsmooth', 'numeric'), ('rdilate', 'numeric'), ('ignore', 'string'), ('time', 'string'), ('method', 'string'), ('weights', 'string'), ('criterium', 'string')],
    'fc_ComputeROIFC':                 [('bolds', 'string'), ('roiinfo', 'string'), ('frames', 'string'), ('targetf', 'string'), ('options', 'string')],
    'fc_ComputeROIFCGroup':            [('flist', 'string'), ('roiinfo', 'string'), ('frames', 'string'), ('targetf', 'string'), ('options', 'string')],
    'fc_ComputeSeedMaps':              [('bolds', 'string'), ('roiinfo', 'string'), ('frames', 'string'), ('targetf', 'string'), ('options', 'string')],
    'fc_ComputeSeedMapsGroup':         [('flist', 'string'), ('roiinfo', 'string'), ('frames', 'string'), ('targetf', 'string'), ('options', 'string')],
    'fc_ComputeSeedMapsMultiple':      [('flist', 'string'), ('roiinfo', 'string'), ('inmask', 'numeric'), ('options', 'string'), ('targetf', 'string'), ('method', 'string'), ('ignore', 'string'), ('cv', 'string')],
    'fc_ExtractROITimeseriesMasked':   [('flist', 'string'), ('roiinfo', 'string'), ('inmask', 'string'), ('targetf', 'string'), ('options', 'string'), ('method', 'string'), ('ignore', 'string'), ('rcodes', 'string'), ('mcodes', 'string'), ('bmask', 'string')],
    'fc_ExtractTrialTimeseriesMasked': [('flist', 'string'), ('roif', 'string'), ('targetf', 'string'), ('tevents', 'string'), ('frames', 'numeric'), ('scrubvar', 'string')],
    'fc_fcMRISegment':                 [('flist', 'string'), ('smask', 'string'), ('tmask', 'string'), ('mask', 'numeric'), ('root', 'string'), ('options', 'string'), ('verbose', 'string')],
    'fc_Preprocess':                   [('sessionf', 'string'), ('bold', 'numeric'), ('omit', 'numeric'), ('do', 'string'), ('rgss', 'string'), ('task', 'string'), ('efile', 'string'), ('TR', 'numeric'), ('eventstring', 'string'), ('variant', 'string'), ('overwrite', 'string'), ('tail', 'string'), ('scrub', 'string'), ('ignores', 'string'), ('options', 'string')],
    'fc_PreprocessConc':               [('sessionf', 'string'), ('bolds', 'numeric'), ('do', 'string'), ('TR', 'numeric'), ('omit', 'string'), ('rgss', 'string'), ('task', 'string'), ('efile', 'string'), ('eventstring', 'string'), ('variant', 'string'), ('overwrite', 'string'), ('tail', 'string'), ('scrub', 'string'), ('ignores', 'string'), ('options', 'string'), ('done', 'string')],
    's_ComputeBehavioralCorrelations': [('imgfile', 'string'), ('datafile', 'string'), ('target', 'string')],
    's_p2Z':                           [('img', 'string'), ('out', 'string'), ('tail', 'string')],
    's_TTestDependent':                [('filea', 'string'), ('fileb', 'string'), ('target', 'string'), ('output', 'string'), ('exclude', 'string'), ('verbose', 'bool')],
    's_TTestIndependent':              [('filea', 'string'), ('fileb', 'string'), ('target', 'string'), ('output', 'string'), ('vartype', 'string'), ('exclude', 'string'), ('verbose', 'bool')],
    's_TTestZero':                     [('dfile', 'string'), ('output', 'string'), ('exclude', 'string'), ('verbose', 'bool')],
}

functionList = functions.keys()
functionList.sort()


# ==============================================================================
#                                                                     PRINT HELP
#

def help(command):
    '''Prints help for the command using Matlab.'''

    print "\nDisplaying help for Matlab function %s\n--------------------------------------------------------------------------------\n" % (command)
    com = '%s "help %s; exit"' % (mcommand, command)
    subprocess.call(com, shell=True)
    print "\n--------------------------------------------------------------------------------\n"


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

    print "\nRunning:\n>>> %s\n" % (mcom)

    ret = subprocess.call(com, shell=True, stdout=sout, stderr=serr)

    if ret:
        print "\n\nERROR: %s failed! Please check output / log!\n" % (command)
    else:
        print "\n\n===> Successful completion of task\n"
