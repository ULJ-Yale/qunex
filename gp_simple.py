#!/usr/bin/env python
# encoding: utf-8
"""
This file holds code for support functions for image preprocessing and analysis.
It consists of functions:

* createBoldList   ... creates a list with paths to each subject's BOLD files
* createConcList   ... creates a list with paths to each subject's conc files
* listSubjectInfo  ... lists subjects data stored in subjects.txt file

All the functions are part of the processing suite. They should be called
from the command line using `gmri` command. Help is available through:

`gmri ?<command>` for command specific help
`gmri -o` for a list of relevant arguments and options

Created by Grega Repovs on 2016-12-17.
Code split from dofcMRIp_core gCodeP/preprocess codebase.
Copyright (c) Grega Repovs. All rights reserved.
"""


from gp_core import *
from g_img import *
import os
import shutil
import re
import subprocess
import glob
import exceptions
import sys
import traceback
from datetime import datetime
import time


def createBoldList(sinfo, options, overwrite=False, thread=0):
    """
    createBoldList - documentation not yet available.
    """
    bfile = open(os.path.join(options['basefolder'], 'boldlist' + options['bold_prefix'] + '.list'), 'w')
    bsearch = re.compile('bold([0-9]+)')

    for subject in sinfo:
        bolds = []
        for (k, v) in subject.iteritems():
            if k.isdigit():
                bnum = bsearch.match(v['name'])
                if bnum:
                    if v['task'] in options['bppt'].split("|"):
                        bolds.append(v['name'])
        if len(bolds) > 0:
            f = getFileNames(subject, options)
            print >> bfile, "    subject id:%s" % (subject['id'])
            print >> bfile, "    roi:%s" % (os.path.abspath(f['fs_aparc_bold']))
            for bold in bolds:
                f = getBOLDFileNames(subject, boldname=bold, options=options)
                print >> bfile, "    file:%s" % (os.path.abspath(f['bold_final']))

    bfile.close()


def createConcList(sinfo, options, overwrite=False, thread=0):
    """
    createConcList - documentation not yet available.
    """

    bfile = open(os.path.join(options['basefolder'], 'conclist' + options['bold_prefix'] + '.list'), 'w')

    concs = options['bppt'].split("|")
    fidls = options['eventfile'].split("|")

    if len(concs) != len(fidls):
        print "\nWARNING: Number of conc files (%d) does not match number of event files (%d), processing aborted!" % (len(concs), len(fidls))

    else:
        for subject in sinfo:
            try:
                f = getFileNames(subject, options)
                d = getSubjectFolders(subject, options)

                print >> bfile, "subject id:%s" % (subject['id'])
                print >> bfile, "    roi:%s" % (f['fs_aparc_bold'])

                tfidl  = fidls[0].strip().replace(".fidl", "")

                f_conc = os.path.join(d['s_bold_concs'], f['conc_final'])
                f_fidl = os.path.join(d['s_bold_events'], tfidl + ".fidl")

                print >> bfile, "    fidl:%s" % (f_fidl)
                print >> bfile, "    file:%s" % (f_conc)

            except:
                print "ERROR processing subject %s!" % (subject['id'])
                raise

    bfile.close()



def listSubjectInfo(sinfo, options, overwrite=False, thread=0):
    """
    listSubjectInfo - documentation not yet available.
    """
    bfile = open(os.path.join(options['basefolder'], 'SubjectInfo.txt'), 'w')

    for subject in sinfo:
        print >> bfile, "subject: %s, group: %s" % (subject['id'], subject['group'])

    bfile.close()

