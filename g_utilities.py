#!/usr/bin/env python
# encoding: utf-8
"""
Miscellaneous utilities for file processing.

Created by Grega Repovs on 2017-09-17.
Copyright (c) Grega Repovs. All rights reserved.
"""

import os.path
import glob
import datetime


def compileSubjectsTxt(subjectsFolder=".", sourceFiles="subject_hcp.txt", targetFile=None, overwrite="ask"):
    '''
    compileSubjectsTxt [subjectsFolder=.] [sourceFiles=subject_hcp.txt] [targetFile=processing/subjects.txt]

    Combines all the sourceFiles in all subject folders in subjectsFolder to
    generate a joint subjects.txt file and save it as targetFile.

    If no targetFile is specified, it will save the file as subjects.txt in a
    processing folder parallel to the subjectsFolder. If the folder does not yet
    exist, it will create it.

    If targetFile already exists, depending on "overwrite" parameter it will:

    - ask: ask interactively
    - yes: overwrite the existing file
    - no:  abort creating the file

    Example:

    gmri compileSubjectsTxt sourceFiles="subject.txt" targetFile="fcMRI/subjects_fcMRI.txt"
    '''

    # --- prepare target file name and folder

    if targetFile is None:
        targetFile = os.path.join(os.path.dirname(os.path.abspath(subjectsFolder)), 'processing', 'subjects.txt')

    if os.path.exists(targetFile):
        print "WARNING: target file %s already exists!" % (os.path.abspath(targetFile))
        if overwrite == 'ask':
            s = raw_input("         Do you want to overwrite it? [y/n]: ")
            if s == 'y':
                print "         Overwriting exisiting file."
            else:
                print "         Aborting."
                return
        elif overwrite == 'yes':
            print "         Overwriting exisiting file."
        elif overwrite == 'no':
            print "         Aborting."
            return

    targetFolder = os.path.dirname(targetFile)
    if not os.path.exists(targetFolder):
        print "---> Creating target folder %s" % (targetFolder)
        os.makedirs(targetFolder)

    # --- open target file

    print "---> Creating file %s" % (os.path.basename(targetFile))
    jfile = open(targetFile, 'w')
    print >> jfile, "# File generated automatically on %s" % (datetime.datetime.today())
    print >> jfile, "# Subjects folder: %s" % (os.path.abspath(subjectsFolder))
    print >> jfile, "# Source files: %s" % (sourceFiles)

    # --- loop trough subject files

    files = glob.glob(os.path.join(os.path.abspath(subjectsFolder), '*', sourceFiles))
    files.sort()
    for file in files:
        print "---> Adding: %s" % (os.path.basename(os.path.dirname(file)))
        print >> jfile, "\n---"
        with open(file) as f:
            for line in f:
                print >> jfile, line,

    # --- close file

    print "===> Done"
    jfile.close()

