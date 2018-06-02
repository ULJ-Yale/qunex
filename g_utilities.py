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
import niutilities.g_core as gc
import getpass


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



def createStudy(studyfolder=None):
    '''
    createStudy studyfolder=<path to study base folder>

    Creates the base folder at the provided path location and the key standard
    study subfolders. Specifically:

    <studyfolder>
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
    specified study is to reside. The command also prepares template
    batch_parameters_example.txt and hcp_mapping_example.txt files in
    <studyfolder>/subjects/specs folder. Finally, it creates a .mnapstudy file in
    the <studyfolder> to identify it as a study basefolder.

    Example:

    gmri createStudy studyfolder=/Volumes/data/studies/WM.v4

    ----------------
    Written by Grega Repovš

    Changelog
    2017-12-26 Grega Repovš
             - Added copying of parameters and hcpmap templates.
    2018-03-31 Grega Repovs
             - Added creation of .mnapstudy file.
    2018-06-02 Grega Repovs
             - Changed templates to *_example.txt.
    '''

    if studyfolder is None:
        raise ValueError("ERROR: studyfolder parameter has to be provided!")

    folders = [['analysis'], ['analysis', 'scripts'], ['processing'], ['processing', 'logs'], ['processing', 'lists'], ['processing', 'scripts'],
               ['info'], ['info', 'demographics'], ['info', 'tasks'], ['info', 'stimuli'],
               ['subjects'], ['subjects', 'inbox'], ['subjects', 'inbox', 'MR'], ['subjects', 'inbox', 'EEG'], ['subjects', 'inbox', 'behavior'], ['subjects', 'inbox', 'events'],
               ['subjects', 'archive'], ['subjects', 'archive', 'MR'], ['subjects', 'archive', 'EEG'], ['subjects', 'archive', 'behavior'], ['subjects', 'specs'], ['subjects', 'QC']]

    print "\nCreating study folder structure:"
    for folder in folders:
        tfolder = os.path.join(*[studyfolder] + folder)

        if os.path.exists(tfolder):
            print " ... folder exists:", tfolder
        else:
            print " ... creating:", tfolder
            os.makedirs(tfolder)

    TemplateFolder = os.environ['TemplateFolder']
    print "\nPreparing template files:"

    paramFile = os.path.join(studyfolder, 'subjects', 'specs', 'batch_parameters_example.txt')
    if not os.path.exists(paramFile):
        print " ... batch_parameters_example.txt"
        pfile = open(paramFile, 'w')
        print >> pfile, parameterTemplateHeader
        for line in gp.arglist:
            if len(line) == 4:
                print >> pfile, "# _%-24s : %-15s ... %s" % (line[0], line[1], line[3])
            elif len(line) > 0:
                print >> pfile, "#\n# " + line[0] + '\n#'
        pfile.close()
    else:
        print " ... batch_parameters_example.txt file already exists"

    mapFile = os.path.join(studyfolder, 'subjects', 'specs', 'hcp_mapping_example.txt')
    if os.path.exists(mapFile):
        print " ... hcp_mapping_example.txt file already exists"
    else:
        print " ... hcp_mapping_example.txt"
        shutil.copyfile(os.path.join(TemplateFolder, 'templates', 'hcp_mapping_example.txt'), mapFile)

    markFile = os.path.join(studyfolder, '.mnapstudy')
    if os.path.exists(markFile):
        print " ... .mnapstudy file already exists"
    else:
        mark = open(markFile, 'w')
        try:
            username = getpass.getuser()
        except:
            username = "unknown user"
        print >> mark, "%s study folder created on %s by %s." % (os.path.basename(studyfolder), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username)
        mark.close()

    print "\nDone.\n"


def compileBatch(subjectsfolder=".", sfile="subject_hcp.txt", tfile=None, subjects=None, sfilter=None, overwrite="ask", paramfile=None):
    '''
    compileBatch [subjectsfolder=.] [sfile=subject_hcp.txt] [tfile=processing/batch.txt] [subjects=None] [sfilter=None] [overwrite=ask] [paramfile=<subjectsfolder>/specs/batch_parameters.txt]

    Combines all the sfile in all subject folders in subjectsfolder to
    generate a joint batch file and save it as tfile. If only specific subjects
    are to be added or appended, "subjects" parameter can be used. This can be
    a pipe, comma or space separated list of subject ids, another batch file or
    a list file. If a string is provided, grob patterns can be used (e.g.
    subjects="AP*|OR*") and all matching subjects will be processed.

    If no tfile is specified, it will save the file as batch.txt in a
    processing folder parallel to the subjectsfolder. If the folder does not yet
    exist, it will create it.

    If tfile already exists, depending on "overwrite" parameter it will:

    - ask:    ask interactively
    - yes:    overwrite the existing file
    - no:     abort creating the file
    - append: append subjects to the existing file

    If overwrite is set to "append", the parameters will not be changed, however,
    any subjects that are not yet present in the batch file will be appended at
    the end of the batch file.

    The command will also look for a parameter file. If it exists, it will
    prepend its content at the beginning of the batch.txt file. If no paramfile
    is specified and the default template does not exist, the command will print
    a warning and create an empty template (subjects/spec/batch_parameters.txt)
    with all the available parameters. Do note that this file will need to be edited
    with correct parameter values for your study.

    Alternatively, if you don't have a parameter file prepared, you can use or
    copy and modify one of the following templates:

    legacy data template: $TemplateFolder/templates/batch_legacy_parameters.txt
    multiband data template: $TemplateFolder/templates/batch_multiband_parameters.txt

    Example:

    gmri compileBatch sfile="subject.txt" tfile="fcMRI/subjects_fcMRI.txt"

    ----------------
    Written by Grega Repovš

    Changelog
    2017-12-26 Grega Repovš
             - Renamed to compileBatch and batch.txt.
    2018-01-01 Grega Repovš
             - Added append option and changed parameter names.
             - Added the option to specify subjects to add explicitly.
    '''

    if subjects in ['None', 'none', 'NONE']:
        subjects = None

    if sfilter in ['None', 'none', 'NONE']:
        sfilter = None

    # --- prepare target file name and folder

    if tfile is None:
        tfile = os.path.join(os.path.dirname(os.path.abspath(subjectsfolder)), 'processing', 'batch.txt')

    if os.path.exists(tfile):
        print "WARNING: target file %s already exists!" % (os.path.abspath(tfile))
        if overwrite == 'ask':
            s = raw_input("         Do you want to overwrite it (o), cancel command (c), or append to the file (a)? [o/c/a]: ")
            if s == 'o':
                print "         Overwriting exisiting file."
                overwrite = 'yes'
            elif s == 'a':
                print "         Appending to exisiting file."
                overwrite = 'append'
            else:
                print "         Aborting."
                return
        elif overwrite == 'yes':
            print "         Overwriting exisiting file."
        elif overwrite == 'append':
            print "         Appending to exisiting file."
        elif overwrite == 'no':
            print "         Aborting."
            return
    else:
        overwrite = 'yes'

    targetFolder = os.path.dirname(tfile)
    if not os.path.exists(targetFolder):
        print "---> Creating target folder %s" % (targetFolder)
        os.makedirs(targetFolder)

    # --- open target file

    if overwrite == 'yes':
        print "---> Creating file %s" % (os.path.basename(tfile))
        jfile = open(tfile, 'w')
        print >> jfile, "# File generated automatically on %s" % (datetime.datetime.today())
        print >> jfile, "# Subjects folder: %s" % (os.path.abspath(subjectsfolder))
        print >> jfile, "# Source files: %s" % (sfile)
        slist   = []

    elif overwrite == 'append':
        slist, parameters = gc.getSubjectList(tfile)
        slist = [e['id'] for e in slist]
        print "---> Appending to file %s" % (os.path.basename(tfile))
        jfile = open(tfile, 'a')

    # --- check for param file

    if overwrite == 'yes':
        if paramfile is None:
            paramfile = os.path.join(subjectsfolder, 'specs', 'batch_parameters.txt')
            if not os.path.exists(paramfile):
                print "---> WARNING: Creating empty parameter file!"
                pfile = open(paramfile, 'w')
                print >> pfile, parameterTemplateHeader
                for line in gp.arglist:
                    if len(line) == 4:
                        print >> pfile, "# _%-24s : %-15s ... %s" % (line[0], line[1], line[3])
                    elif len(line) > 0:
                        print >> pfile, "#\n# " + line[0] + '\n#'
                pfile.close()

            if os.path.exists(paramfile):
                print "---> appending parameter file [%s]." % (paramfile)
                print >> jfile, "# Parameter file: %s\n#" % (paramfile)
                with open(paramfile) as f:
                    for line in f:
                        print >> jfile, line,
            else:
                print "---> parameter files does not exist, skipping [%s]." % (paramfile)

    # -- get list of subject folders

    if subjects is not None:
        subjects, gopts = gc.getSubjectList(subjects, sfilter=sfilter, verbose=False)
        files = []
        for subject in subjects:
            files += glob.glob(os.path.join(subjectsfolder, subject['id'], sfile))
    else:
        files = glob.glob(os.path.join(os.path.abspath(subjectsfolder), '*', sfile))

    # --- loop trough subject files

    files.sort()
    for file in files:
        subjectid = os.path.basename(os.path.dirname(file))
        if subjectid in slist:
            print "---> Skipping: %s" % (subjectid)
        else:
            print "---> Adding: %s" % (subjectid)
            print >> jfile, "\n---"
            with open(file) as f:
                for line in f:
                    print >> jfile, line,

    # --- close file

    print "===> Done"
    jfile.close()
