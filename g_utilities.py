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
import shutil
import niutilities.g_process as gp


parameterTemplateHeader = '''#  Batch parameters file
#  =====================
#
#  This file is used to specify the default parameters used by various MNAP commands for
#  HCP minimal preprocessing pipeline, additional bold preprocessing commands,
#  and other analytic functions. The content of this file should be prepended to the list
#  that contains all the subjects that is passed to the commands. It can added manually or
#  automatically when making use of the compileLists MNAP command.
#
#  This template file should be edited to include the parameters relevant for
#  a given study/analysis and provide the appropriate values. For detailed description of
#  parameters and their valid values, please consult the MNAP documentation
*  (e.g. Running HCP minimal preprocessing pipelines, Additional BOLD
#  preprocessing) and online help for the relevant MNAP commands.
#
#
#  File format
#  -----------
#
#  Each parameter is specified in a separate line as a
#  "_<parameter_key>: <parameter_value>" pair. For example:
#
#  _hcp_brainsize:  170
#
#  Empty lines and lines that start with a hash (#) are ignored.
#
#
#  Parameters
#  ==========
#
#  The following is a list of parameters organized by the commands they relate
#  to. To specify parameters, uncomment the line (it should start with the
#  underscore before the parameter name) and provide the desired value. In some
#  cases default values are provided. Do take care to remove the descriptors
#  (... <description>) after the values for the parameters to be used.'''



def createStudy(studyFolder=None):
    '''
    createStudy studyFolder=<path to study base folder>

    Creates the base folder at the provided path location and the key standard
    study subfolders. Specifically:

    <studyFolder>
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
        │   ├── MR
        │   ├── EEG
        │   └── behavior
        ├── specs
        └── QC

    Do note that the command will create all the missing subfolders in which the
    specified study is to reside. The command also prepares template batch_parameters.txt
    and hcp_mapping.txt files in <studyFolder>/subjects/specs folder.

    Example:

    gmri createStudy studyFolder=/Volumes/data/studies/WM.v4

    ----------------
    Written by Grega Repovš

    Changelog
    2017-12-26 Grega Repovš
             - Added copying of parameters and hcpmap templates.
    '''

    if studyFolder is None:
        raise ValueError("ERROR: studyFolder parameter has to be provided!")

    folders = [['analysis'], ['analysis', 'scripts'], ['processing'], ['processing', 'logs'], ['processing', 'lists'], ['processing', 'scripts'],
               ['info'], ['info', 'demographics'], ['info', 'tasks'], ['info', 'stimuli'],
               ['subjects'], ['subjects', 'inbox'], ['subjects', 'inbox', 'MR'], ['subjects', 'inbox', 'EEG'], ['subjects', 'inbox', 'behavior'], ['subjects', 'inbox', 'events'],
               ['subjects', 'archive'], ['subjects', 'archive', 'MR'], ['subjects', 'archive', 'EEG'], ['subjects', 'archive', 'behavior'], ['subjects', 'specs'], ['subjects', 'QC']]

    print "\nCreating study folder structure:"
    for folder in folders:
        tfolder = os.path.join(*[studyFolder] + folder)

        if os.path.exists(tfolder):
            print " ... folder exists:", tfolder
        else:
            print " ... creating:", tfolder
            os.makedirs(tfolder)

    TemplateFolder = os.environ['TemplateFolder']
    print "\nPreparing template files:"

    paramFile = os.path.join(studyFolder, 'subjects', 'specs', 'batch_parameters.txt')
    if not os.path.exists(paramFile):
        print " ... parameters.txt"
        pfile = open(paramFile, 'w')
        print >> pfile, parameterTemplateHeader
        for line in gp.arglist:
            if len(line) == 4:
                print >> pfile, "# _%-24s : %-15s ... %s" % (line[0], line[1], line[3])
            elif len(line) > 0:
                print >> pfile, "#\n# " + line[0] + '\n#'
        pfile.close()
    else:
        print " ... parameters.txt file already exists"

    mapFile = os.path.join(studyFolder, 'subjects', 'specs', 'hcp_mapping.txt')
    if os.path.exists(mapFile):
        print " ... hcp_mapping.txt file already exists"
    else:
        print " ... hcp_mapping.txt"
        shutil.copyfile(os.path.join(TemplateFolder, 'templates', 'hcp_mapping.txt'), mapFile)

    print "\nDone.\n"


def compileBatch(subjectsFolder=".", sourceFiles="subject_hcp.txt", targetFile=None, overwrite="ask", paramFile=None):
    '''
    compileBatch [subjectsFolder=.] [sourceFiles=subject_hcp.txt] [targetFile=processing/batch.txt] [overwrite=ask] [paramFile=<subjectsFolder>/specs/batch_parameters.txt]

    Combines all the sourceFiles in all subject folders in subjectsFolder to
    generate a joint batch file and save it as targetFile.

    If no targetFile is specified, it will save the file as group.txt in a
    processing folder parallel to the subjectsFolder. If the folder does not yet
    exist, it will create it.

    If targetFile already exists, depending on "overwrite" parameter it will:

    - ask: ask interactively
    - yes: overwrite the existing file
    - no:  abort creating the file

    The command will also look for a parameter file. If it exists, it will
    prepend its content at the beginning of the batch.txt file. If no paramFile
    is specified and the default template does not exist, the command will print
    a warning and create an empty template with all available parameters. Do
    note that this file will need to be edited with correct parameter values for
    your study.

    Alternatively, if you don't have a parameter file prepared, you can use or
    copy and modify one of the following templates:

    legacy data template: $TemplateFolder/templates/batch_legacy_parameters.txt
    multiband data template: $TemplateFolder/templates/batch_multiband_parameters.txt

    Example:

    gmri compileBatch sourceFiles="subject.txt" targetFile="fcMRI/subjects_fcMRI.txt"

    ----------------
    Written by Grega Repovš

    Changelog
    2017-12-26 Grega Repovš
             - Renamed to compileBatch and batch.txt.
    '''

    # --- prepare target file name and folder

    if targetFile is None:
        targetFile = os.path.join(os.path.dirname(os.path.abspath(subjectsFolder)), 'processing', 'batch.txt')

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

    # --- check for param file

    if paramFile is None:
        paramFile = os.path.join(subjectsFolder, 'specs', 'batch_parameters.txt')
        if not os.path.exists(paramFile):
            print "---> WARNING: Creating empty parameter file!"
            pfile = open(paramFile, 'w')
            print >> pfile, parameterTemplateHeader
            for line in gp.arglist:
                if len(line) == 4:
                    print >> pfile, "# _%-24s : %-15s ... %s" % (line[0], line[1], line[3])
                elif len(line) > 0:
                    print >> pfile, "#\n# " + line[0] + '\n#'
            pfile.close()

    if os.path.exists(paramFile):
        print "---> appending parameter file [%s]." % (paramFile)
        print >> jfile, "# Parameter file: %s\n#" % (paramFile)
        with open(paramFile) as f:
            for line in f:
                print >> jfile, line,
    else:
        print "---> parameter files does not exist, skipping [%s]." % (paramFile)

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
