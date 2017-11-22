#!/usr/bin/env python
# encoding: utf-8
"""
Miscellaneous utilities for file processing.

Created by Grega Repovs on 2017-09-17.
Copyright (c) Grega Repovs. All rights reserved.
"""

import os.path
import os
import glob
import datetime


def createStudy(studyFolder=None):
    '''
    createStudy studyFolder=<path to study base folder>

    Creates the base folder at the provided path location and the key standard
    study subfolders. Specifically:

    <study>
    ├── analysis
    │   └── scripts
    ├── processing
    │   ├── logs
    │   ├── lists
    │   └── scripts
    ├── info
    │   ├── demographics
    │   ├── tasks
    │   └── stimuli
    └── subjects
        ├── inbox
        │   ├── MR
        │   ├── EEG
        │   ├── behavior
        │   └── events
        ├── archive
        ├── specs
        └── QC

    Do note that the command will create all the missing subfolders in which the
    specified study is to reside!

    Example:

    gmri createStudy studyFolder=/Volumes/data/studies/WM.v4
    '''

    if studyFolder is None:
        raise ValueError("ERROR: studyFolder parameter has to be provided!")

    folders = [['analysis'], ['analysis', 'scripts'], ['processing'], ['processing', 'logs'], ['processing', 'lists'], ['processing', 'scripts'],
               ['info'], ['info', 'demographics'], ['info', 'tasks'], ['info', 'stimuli'],
               ['subjects'], ['subjects', 'inbox'], ['subjects', 'inbox', 'MR'], ['subjects', 'inbox', 'EEG'], ['subjects', 'inbox', 'behavior'], ['subjects', 'inbox', 'events'], ['subjects', 'archive'], ['subjects', 'specs'], ['subjects', 'QC']]

    print "\nCreating study folder structure:"
    for folder in folders:
        tfolder = os.path.join(*[studyFolder] + folder)

        if os.path.exists(tfolder):
            print " ... folder exists:", tfolder
        else:
            print " ... creating:", tfolder
            os.makedirs(tfolder)

    print "\nDone.\n"


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

