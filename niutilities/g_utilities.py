#!/usr/bin/env python2.7
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
import niutilities.gp_core as gpc
import niutilities.g_exceptions as ge
import niutilities
import getpass
import re
import subprocess
import sys

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



def manageStudy(studyfolder=None, action="create"):
    '''
    manageStudy studyfolder=None action="create"

    A helper function called by createStudy and checkStudy that does the
    actual checking of the study folder and generating missing content.

    studyfolder  : the location of the study folder
    action       : whether to create a new study folder (create) or check
                   an existing study folder (check)
    '''

    create = action == "create"

    folders = [['analysis'], ['analysis', 'scripts'], 
               ['processing'], 
               ['processing', 'logs'], ['processing', 'logs', 'comlogs'], ['processing', 'logs', 'runlogs'], ['processing', 'logs', 'runchecks'], 
               ['processing', 'lists'], 
               ['processing', 'scripts'],
               ['processing', 'scenes'], ['processing', 'scenes', 'QC'], ['processing', 'scenes', 'QC', 'T1w'], ['processing', 'scenes', 'QC', 'T2w'], ['processing', 'scenes', 'QC', 'myelin'], ['processing', 'scenes', 'QC', 'BOLD'], ['processing', 'scenes', 'QC', 'DWI'],
               ['info'], ['info', 'demographics'], ['info', 'tasks'], ['info', 'stimuli'], ['info', 'bids'], ['info', 'hcpls'],
               ['subjects'], 
               ['subjects', 'inbox'], ['subjects', 'inbox', 'MR'], ['subjects', 'inbox', 'EEG'], ['subjects', 'inbox', 'BIDS'], ['subjects', 'inbox', 'HCPLS'], ['subjects', 'inbox', 'behavior'], ['subjects', 'inbox', 'concs'], ['subjects', 'inbox', 'events'],
               ['subjects', 'archive'], ['subjects', 'archive', 'MR'], ['subjects', 'archive', 'EEG'], ['subjects', 'archive', 'BIDS'], ['subjects', 'archive', 'HCPLS'], ['subjects', 'archive', 'behavior'], 
               ['subjects', 'specs'], 
               ['subjects', 'QC']]

    if create:
        print "\nCreating study folder structure:"

    for folder in folders:
        tfolder = os.path.join(*[studyfolder] + folder)

        if os.path.exists(tfolder):                
            if create:
                print " ... folder exists:", tfolder
        else:
            if create:
                print " ... creating:", tfolder
            os.makedirs(tfolder)

    if create:
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
    │   │   ├── comlogs
    │   │   ├── runchecks
    │   │   └── runlogs
    │   ├── lists
    │   ├── scenes
    │   │   └── QC
    │   │       ├── T1w
    │   │       ├── T2w
    │   │       ├── myelin
    │   │       ├── BOLD
    │   │       └── DWI
    │   └── scripts
    ├── info
    │   ├── bids
    │   ├── demographics
    │   ├── hcpls
    │   ├── tasks
    │   └── stimuli
    └── subjects
        ├── inbox
        │   ├── MR
        │   ├── EEG
        │   ├── BIDS
        │   ├── behavior
        │   ├── concs
        │   ├── events
        │   └── HCPLS
        ├── archive
        │   ├── MR
        │   ├── EEG
        │   ├── BIDS
        │   ├── behavior
        │   └── HCPLS
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
    2018-07-24 Grega Repovs
             - Expanded folders to include QC scenes
    2018-09-17 Grega Repovs
             - Added BIDS folders
    2018-11-14 Grega Repovs
             - Moved the processing to manageStudy function
    2018-11-14 Grega Repovs
             - Added HCPLS folders
    '''

    print "Running createStudy\n==================="

    if studyfolder is None:
        raise ge.CommandError("createStudy", "No studyfolder specified", "Please provide path for the new study folder using studyfolder parameter!")

    manageStudy(studyfolder=studyfolder, action="create")


def checkStudy(startfolder="."):
    '''
    checkStudy startfolder="."

    The function looks for the path to the study folder in the hierarchy 
    starting from the provided startfolder. If found it checks that all the
    standard folders are present and creates any missing ones. It returns
    the path to the study folder. If the study folder can not be identified, 
    it returns None.

    ---
    Written by Grega Repovš, 2018-11-14
    '''

    studyfolder = None
    testfolder  = os.path.abspath(startfolder)

    while os.path.dirname(testfolder) and os.path.dirname(testfolder) != '/':
        if os.path.exists(os.path.join(testfolder, '.mnapstudy')):
            studyfolder = testfolder
            break
        testfolder = os.path.dirname(testfolder)

    if studyfolder:
        manageStudy(studyfolder=studyfolder, action="check")

    return studyfolder  


def createBatch(subjectsfolder=".", sfile="subject_hcp.txt", tfile=None, subjects=None, sfilter=None, overwrite="no", paramfile=None):
    '''
    createBatch [subjectsfolder=.] [sfile=subject_hcp.txt] [tfile=processing/batch.txt] [subjects=None] [sfilter=None] [overwrite=no] [paramfile=<subjectsfolder>/specs/batch_parameters.txt]

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

    Note that if If a batch file already exists then parameter file will not be 
    added to the header of the batch unless --overwrite is set to "yes". If 
    --overwrite is set to "append", then the parameters will not be changed, 
    however, any subjects that are not yet present in the batch file will be 
    appended at the end of the batch file.

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

    gmri createBatch sfile="subject.txt" tfile="fcMRI/subjects_fcMRI.txt"

    ----------------
    Written by Grega Repovš

    Changelog
    2017-12-26 Grega Repovš
             - Renamed to createBatch and batch.txt.
    2018-01-01 Grega Repovš
             - Added append option and changed parameter names.
             - Added the option to specify subjects to add explicitly.
    2018-07-16 Grega Repovš
             - Renamed to createBatch from compileBatch
    2018-07-20 Grega Repovš
             - Fixed adding paramfile and updated documentation
    '''

    print "Running createBatch\n==================="

    if subjects in ['None', 'none', 'NONE']:
        subjects = None

    if sfilter in ['None', 'none', 'NONE']:
        sfilter = None

    # --- prepare target file name and folder

    if tfile is None:
        tfile = os.path.join(os.path.dirname(os.path.abspath(subjectsfolder)), 'processing', 'batch.txt')

    if os.path.exists(tfile):
        if overwrite == 'ask':
            print "WARNING: target file %s already exists!" % (os.path.abspath(tfile))
            s = raw_input("         Do you want to overwrite it (o), cancel command (c), or append to the file (a)? [o/c/a]: ")
            if s == 'o':
                print "         Overwriting exisiting file."
                overwrite = 'yes'
            elif s == 'a':
                print "         Appending to exisiting file."
                overwrite = 'append'
            else:
                raise ge.CommandFailed("createBatch", "Target file exists", "A file with the specified path already exists [%s]" % (os.path.abspath(tfile)), "Please use set overwrite to `yes` or `append` for apropriate action" )
        elif overwrite == 'yes':
            print "WARNING: target file %s already exists!" % (os.path.abspath(tfile))
            print "         Overwriting exisiting file."
        elif overwrite == 'append':
            print "WARNING: target file %s already exists!" % (os.path.abspath(tfile))
            print "         Appending to exisiting file."
        elif overwrite == 'no':
            raise ge.CommandFailed("createBatch", "Target file exists", "A file with the specified path already exists [%s]" % (os.path.abspath(tfile)), "Please use set overwrite to `yes` or `append` for apropriate action" )
    else:
        overwrite = 'yes'

    targetFolder = os.path.dirname(tfile)
    if not os.path.exists(targetFolder):
        print "---> Creating target folder %s" % (targetFolder)
        os.makedirs(targetFolder)

    # --- open target file

    preexist = os.path.exists(tfile)

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
        if paramfile and preexist:
            print "---> WARNING: paramfile was specified, however it will not be added as we are appending to an existing file!"
        jfile = open(tfile, 'a')

    # --- check for param file

    if overwrite == 'yes' or not preexist:
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

    missing = 0

    if subjects is not None:
        subjects, gopts = gc.getSubjectList(subjects, sfilter=sfilter, verbose=False)
        files = []
        for subject in subjects:
            nfiles = glob.glob(os.path.join(subjectsfolder, subject['id'], sfile))
            if nfiles:
                files += nfiles
            else:
                print "---> ERROR: no %s found for %s! Please check your data! [%s]" % (sfile, subject['id'], os.path.join(subjectsfolder, subject['id'], sfile))
                missing += 1
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

    jfile.close()

    if missing:
        raise ge.CommandFailed("createBatch", "Not all subjects specified added to the batch file!", "%s was missing for %d subject(s)!" % (sfile, missing), "Please check your data!")



def createList(subjectsfolder=".", subjects=None, sfilter=None, listfile=None, bolds=None, conc=None, fidl=None, glm=None, roi=None, boldname="bold", boldtail=".nii.gz", overwrite='no', check='yes'):
    """
    createList [subjectsfolder="."] [subjects=None] [sfilter=None] [listfile=None] [bolds=None] [conc=None] [fidl=None] [glm=None] [roi=None] [boldname="bold"] [boldtail=".nii.gz"] [overwrite="no"] [check="yes"]

    The function creates a .list formated file that can be used as input to a
    number of processing and analysis functions. The function is fairly flexible,
    its output defined using a number of parameters.

    The location of the file
    ------------------------

    The file is created at the path specified in `listfile` parameter. If no
    parameter is provided, the resulting list is saved in:

    <studyfolder>/processing/lists/subjects.list

    If a file already exists, depending on the `overwrite` parameter the
    function will:

    - ask:    ask interactively, what to do
    - yes:    overwrite the existing file
    - no:     abort creating the file
    - append: append subjects to the existing file

    The subjects to list
    --------------------

    Subjects to include in the list are specified using `subjects` parameter.
    This can be a pipe, comma or space separated list of subject ids, a batch
    file or another list file. If a string is provided, grob patterns can be
    used (e.g. subjects="AP*|OR*") and all matching subjects will be included.

    If a batch file is provided, subjects can be filtered using the `sfilter`
    parameter. The parameter should be provided as a string in the format:

    "<key>:<value>|<key>:<value>"

    Only the subjects for which all the specified keys match the specified values
    will be included in the list.

    If no subjects are specified, the function will inspect the `subjectsfolder`
    and include all the subjects for which an `images` folder exists as a
    subfolder in the subject's folder.

    The files to include
    --------------------

    The function enables inclusion of bold, conc, fidl, glm and roi files.

    *bold files*
    To include bold files, specify them using the `bolds` parameter. Provide a
    string that lists bold numbers or bold task names in a space, comma or pipe
    separated string. The numeric values in the string will be interpreted as
    bold numbers to include, strings will be interpreted as bold task names as
    they are provided in the batch file. All the bolds that match any of the
    tasks listed will be included. If `all` is specified, all the bolds listed
    in the batch file will be included.

    Two other parameters are cruical for generation of bold file entries in the
    list: `boldname` and `boldtail`.

    The bolds will be listed in the list file as:

    file:<subjectsfolder>/<subject>/images/functional/<boldname><boldnumber><boldtail>

    *conc files*
    To include conc files, provide a `conc` parameter. In the parameter list the
    name of the conc file to be include. Conc files will be listed as:

    conc:<subjectsfolder>/<subject>/images/functional/concs/<conc>

    *fidl files*
    To include fidl files, provide a `fidl` parameter. In the parameter list the
    name of the fidl file to include. Fidl files will be listed as:

    fidl:<subjectsfolder>/<subject>/images/functional/events/<fidl>

    *GLM files*
    To include GLM files, provide a `glm` parameter. In the parameter list the
    name of the GLM file to include. GLM files will be listed as:

    glm:<subjectsfolder>/<subject>/images/functional/<glm>

    *ROI files*
    To include ROI files, provide a `roi` parameter. In the parameter list the
    name of the ROI file to include. ROI files will be listed as:

    roi:<subjectsfolder>/<subject>/images/<roi>

    Note that for all the files the function expects the files to be present in
    the correct places within the MNAP subjects folder structure. For ROI files
    provide the relative path from the `images` folder.

    Checking for presence of files
    ------------------------------

    By default the function checks if the files listed indeed exist. If a file
    is missing, the function will abort and no list will be created or appended.
    The behavior is specified using the `check` parameter that can take the
    following values:

    - yes  ... check for presence and abort if the file to be listed is not found
    - no   ... do not check whether files are present or not
    - warn ... check for presence and warn if the file to be listed is not found

    Examples
    --------

    > gmri createList bolds="1,2,3"

    The command will create a list file in `../processing/list/subjects.txt` that
    will list for all the subjects found in the current folder BOLD files 1, 2, 3
    listed as:

      file:<current path>/<subject>/images/functional/bold[n].nii.gz

    > gmri createList subjectsfolder="/studies/myStudy/subjects" subjects="batch.txt" \\
           bolds="rest" listfile="lists/rest.list" boldtail="_Atlas_g7_hpss_res-mVWMWB1d.dtseries"

    The command will create a `lists/rest.list` list file in which for all the
    subjects specified in the `batch.txt` it will list all the BOLD files tagged
    as rest runs and include them as:

      file:<subjectsfolder>/<subject>/images/functional/bold[n]_Atlas_g7_hpss_res-mVWMWB1d.dtseries

    > gmri createList subjectsfolder="/studies/myStudy/subjects" subjects="batch.txt" \\
           sfilter="EC:use" listfile="lists/EC.list" \\
           conc="bold_Atlas_dtseries_EC_g7_hpss_res-mVWMWB1de.conc" \\
           fidl="EC.fidl" glm="bold_conc_EC_g7_hpss_res-mVWMWB1de_Bcoeff.nii.gz" \\
           roi="segmentation/hcp/fsaverage_LR32k/aparc.32k_fs_LR.dlabel.nii"

    The command will create a list file in `lists/EC.list" that will list for
    all the subject in the conc file, that have the key:value pair "EC:use" the
    following files:

      conc:<subjectsfolder>/<subject>/images/functional/concs/bold_Atlas_dtseries_EC_g7_hpss_res-mVWMWB1de.conc
      fidl:<subjectsfolder>/<subject>/images/functional/events/EC.fidl
      glm:<subjectsfolder>/<subject>/images/functional/bold_conc_EC_g7_hpss_res-mVWMWB1de_Bcoeff.nii.gz
      roi:<subjectsfolder>/<subject>/images/segmentation/hcp/fsaverage_LR32k/aparc.32k_fs_LR.dlabel.nii

    ----------------
    Written by Grega Repovš 2018-06-26

    """

    print "Running createList\n=================="

    def checkFile(fileName):
        if check == 'no':
            pass
        elif not os.path.exists(fileName):
            if check == 'warn':
                print "WARNING: File does not exist [%s]!" % (fileName)
            else:
                raise ge.CommandFailed("createList", "File does not exist", "A file to be included in the list does not exist [%s]" % (fileName), "Please check paths or set `check` to `no` to add the missing files anyway")

    # --- check subjects

    if subjects in ['None', 'none', 'NONE']:
        subjects = None

    if sfilter in ['None', 'none', 'NONE']:
        sfilter = None

    # --- prepare parameters

    boldtags, boldnums = None, None

    if bolds:
        bolds = [e.strip() for e in re.split(' *, *| *\| *| +', bolds)]
        boldtags = [e for e in bolds if not e.isdigit()]
        boldnums = [e for e in bolds if e.isdigit()]

    bsearch  = re.compile('bold([0-9]+)')

    # --- prepare target file name and folder

    if listfile is None:
        listfile = os.path.join(os.path.dirname(os.path.abspath(subjectsfolder)), 'processing', 'lists', 'subjects.list')
        print "WARNING: No target list file name specified.\n         The list will be created as: %s!" % (listfile)

    if os.path.exists(listfile):
        print "WARNING: Target list file %s already exists!" % (os.path.abspath(listfile))
        if overwrite == 'ask':
            s = raw_input("         Do you want to overwrite it (o), cancel command (c), or append to the file (a)? [o/c/a]: ")
            if s == 'o':
                print "         Overwriting exisiting file."
                overwrite = 'yes'
            elif s == 'a':
                print "         Appending to exisiting file."
                overwrite = 'append'
            else:
                raise ge.CommandFailed("createList", "File exists", "The specified list file already exists [%s]" % (listfile), "Please check paths or set `overwrite` to `yes` or `append` for apropriate action")
        elif overwrite == 'yes':
            print "         Overwriting the exisiting file."
        elif overwrite == 'append':
            print "         Appending to the exisiting file."
        elif overwrite == 'no':
            raise ge.CommandFailed("createList", "File exists", "The specified list file already exists [%s]" % (listfile), "Please check paths or set `overwrite` to `yes` or `append` for apropriate action")
    else:
        overwrite = 'yes'

    targetFolder = os.path.dirname(listfile)
    if not os.path.exists(targetFolder):
        print "---> Creating target folder %s" % (targetFolder)
        os.makedirs(targetFolder)

    # --- check subjects

    if subjects is None:
        print "WARNING: No subjects specified. The list will be generated for all subjects in the subjects folder!"
        subjects = glob.glob(os.path.join(subjectsfolder, '*', 'images'))
        subjects = [os.path.basename(os.path.dirname(e)) for e in subjects]
        subjects = "|".join(subjects)

    subjects, gopts = gc.getSubjectList(subjects, sfilter=sfilter, verbose=False)

    # --- generate list entries

    lines = []

    for subject in subjects:
        lines.append("subject id: %s" % (subject['id']))

        if boldnums:
            for boldnum in boldnums:
                tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', 'functional', boldname + boldnum + boldtail)
                checkFile(tfile)
                lines.append("    file:" + tfile)

        if boldtags:
            try:
                bolds = [(bsearch.match(v['name']).group(1), v['name'], v['task']) for (k, v) in subject.iteritems() if k.isdigit() and bsearch.match(v['name'])]
                if "all" not in boldtags:
                    bolds = [n for n, b, t in bolds if t in boldtags]
                else:
                    bolds = [n for n, b, t in bolds]
                bolds.sort()
            except:
                pass
            for boldnum in bolds:
                tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', 'functional', boldname + boldnum + boldtail)
                checkFile(tfile)
                lines.append("    file:" + tfile)

        if roi:
            tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', roi)
            checkFile(tfile)
            lines.append("    roi:" + tfile)

        if glm:
            tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', 'functional', glm)
            checkFile(tfile)
            lines.append("    glm:" + tfile)

        if conc:
            tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', 'functional', 'concs', conc)
            checkFile(tfile)
            lines.append("    conc:" + tfile)

        if fidl:
            tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', 'functional', 'events', fidl)
            checkFile(tfile)
            lines.append("    fidl:" + tfile)

    # --- write to target file

    if overwrite == 'yes':
        print "---> Creating file %s" % (os.path.basename(listfile))
        lfile = open(listfile, 'w')
        print >> lfile, "# File generated automatically on %s" % (datetime.datetime.today())

    elif overwrite == 'append':
        print "---> Appending to file %s" % (os.path.basename(listfile))
        lfile = open(listfile, 'a')
        print >> lfile, "# Appended to file on %s" % (datetime.datetime.today())

    for line in lines:
        print >> lfile, line

    lfile.close()


def createConc(subjectsfolder=".", subjects=None, sfilter=None, concfolder=None, concname="", bolds=None, boldname="bold", boldtail=".nii.gz", overwrite='no', check='yes'):
    """
    createConc [subjectsfolder="."] [subjects=None] [sfilter=None] [concfolder=None] [concname=""] [bolds=None] [boldname="bold"] [boldtail=".nii.gz"] [overwrite="no"] [check="yes"]

    The function creates a set of .conc formated files that can be used as input
    to a number of processing and analysis functions. The function is fairly
    flexible, its output defined using a number of parameters.

    The location of the files
    -------------------------

    The files are created at the path specified in `concfolder` parameter. If no
    parameter is provided, the resulting files are saved in:

    <studyfolder>/<subjects>/inbox/concs/

    Individual files are named using the following formula:

    <subjectid><concname>.conc

    If a file already exists, depending on the `overwrite` parameter the
    function will:

    - ask:    ask interactively, what to do
    - yes:    overwrite the existing file
    - no:     abort creating the file

    The subjects to list
    --------------------

    Subjects to include in the generation of conc files are specified using
    `subjects` parameter.  This can be a pipe, comma or space separated list of
    subject ids, a batch file or another list file. If a string is provided,
    grob patterns can be used (e.g. subjects="AP*|OR*") and all matching
    subjects will be included.

    If a batch file is provided, subjects can be filtered using the `sfilter`
    parameter. The parameter should be provided as a string in the format:

    "<key>:<value>|<key>:<value>"

    The conc files will be generated only for the subjects for which all the
    specified keys match the specified values.

    If no subjects are specified, the function will inspect the `subjectsfolder`
    and generate conc files for all the subjects for which an `images` folder
    exists as a subfolder in the subject's folder.

    The files to include
    --------------------

    The bold files to incude in the conc file are specified using the `bolds`
    parameter. To specify the bolds to be included in the conc files, provide a
    string that lists bold numbers or bold task names in a space, comma or pipe
    separated string. The numeric values in the string will be interpreted as
    bold numbers to include, strings will be interpreted as bold task names as
    they are provided in the batch file. All the bolds that match any of the
    tasks listed will be included. If `all` is specified, all the bolds listed
    in the batch file will be included.

    Two other parameters are cruical for generation of bold file entries in the
    conc files: `boldname` and `boldtail`.

    The bolds will be listed in the list file as:

    file:<subjectsfolder>/<subject>/images/functional/<boldname><boldnumber><boldtail>

    Note that the function expects the files to be present in the correct place
    within the MNAP subjects folder structure.

    Checking for presence of files
    ------------------------------

    By default the function checks if the files listed indeed exist. If a file
    is missing, the function will abort and no list will be created or appended.
    The behavior is specified using the `check` parameter that can take the
    following values:

    - yes  ... check for presence and abort if the file to be listed is not found
    - no   ... do not check whether files are present or not
    - warn ... check for presence and warn if the file to be listed is not found

    Examples
    --------

    > gmri createConc bolds="1,2,3"

    The command will create set of conc files in `/inbox/concs`,
    each of them named <subject id>.conc, one for each of the subjects found in
    the current folder. Each conc file will include BOLD files 1, 2, 3
    listed as:

      file:<current path>/<subject>/images/functional/bold[n].nii.gz

    > gmri createConc subjectsfolder="/studies/myStudy/subjects" subjects="batch.txt" \\
           bolds="WM" concname="_WM" boldtail="_Atlas.dtseries.nii"

    The command will create for each subject listed in the `batch.txt` a
    `<subjectid>_WM.conc` file in `subjects/inbox/concs` in which it will list
    all the BOLD files tagged as `WM` as:

      file:<subjectsfolder>/<subject>/images/functional/bold[n]_Atlas.dtseries

    > gmri createConc subjectsfolder="/studies/myStudy/subjects" subjects="batch.txt" \\
           sfilter="EC:use" concfolder="analysis/EC/concs" \\
           concname="_EC_g7_hpss_res-mVWMWB1de" bolds="EC" \\
           boldtail="_g7_hpss_res-mVWMWB1deEC.dtseries.nii"

    For all the subjects in the `batch.txt` file that have the key:value pair
    "EC:use" set the command will create a conc file in `analysis/EC/concs`
    folder. The conc files will be named `<subject id>_EC_g7_hpss_res-mVWMWB1de.conc`
    and will list all the bold files that are marked as `EC` runs as:

      file:<subjectsfolder>/<subject>/images/functional/bold[N]_g7_hpss_res-mVWMWB1deEC.dtseries.nii

    ----------------
    Written by Grega Repovš 2018-06-30

    """

    def checkFile(fileName):
        if check == 'no':
            return True
        elif not os.path.exists(fileName):
            if check == 'warn':
                print "     WARNING: File does not exist [%s]!" % (fileName)
                return True
            else:
                print "     ERROR: File does not exist [%s]!" % (fileName)
                return False
        return True

    print "Running createConc\n=================="

    # --- check subjects

    if subjects in ['None', 'none', 'NONE']:
        subjects = None

    if sfilter in ['None', 'none', 'NONE']:
        sfilter = None

    # --- prepare parameters

    boldtags, boldnums = None, None

    if bolds:
        bolds = [e.strip() for e in re.split(' *, *| *\| *| +', bolds)]
        boldtags = [e for e in bolds if not e.isdigit()]
        boldnums = [e for e in bolds if e.isdigit()]
    else:
        raise ge.CommandError("createConc", "No bolds specified to be included in the conc files")

    bsearch  = re.compile('bold([0-9]+)')

    # --- prepare target file name and folder

    if concfolder is None:
        concfolder = os.path.join(os.path.abspath(subjectsfolder), 'inbox', 'concs')
        print "WARNING: No target conc folder specified.\n         The conc files will be created in folder: %s!" % (concfolder)

    if not os.path.exists(concfolder):
        print "---> Creating target folder %s" % (concfolder)
        os.makedirs(concfolder)

    # --- check subjects

    if subjects is None:
        print "WARNING: No subjects specified. The list will be generated for all subjects in the subjects folder!"
        subjects = glob.glob(os.path.join(subjectsfolder, '*', 'images'))
        subjects = [os.path.basename(os.path.dirname(e)) for e in subjects]
        subjects = "|".join(subjects)

    subjects, gopts = gc.getSubjectList(subjects, sfilter=sfilter, verbose=False)

    # --- generate list entries

    error = False
    for subject in subjects:

        print "---> Processing subject %s" % (subject['id'])
        files = []
        complete = True

        if boldnums:
            for boldnum in boldnums:
                tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', 'functional', boldname + boldnum + boldtail)
                complete = complete & checkFile(tfile)
                files.append("    file:" + tfile)

        if boldtags:
            try:
                bolds = [(bsearch.match(v['name']).group(1), v['name'], v['task']) for (k, v) in subject.iteritems() if k.isdigit() and bsearch.match(v['name'])]
                if "all" not in boldtags:
                    bolds = [n for n, b, t in bolds if t in boldtags]
                else:
                    bolds = [n for n, b, t in bolds]
                bolds.sort()
            except:
                pass
            for boldnum in bolds:
                tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', 'functional', boldname + boldnum + boldtail)
                complete = complete & checkFile(tfile)
                files.append("    file:" + tfile)

        concfile = os.path.join(concfolder, subject['id'] + concname + '.conc')

        if not complete and check == 'yes':
            print "     WARNING: Due to missing source files conc file was not created!"
            error = True
            continue

        if os.path.exists(concfile):
            print "     WARNING: Conc file %s already exists!" % (os.path.abspath(concfile))
            if overwrite == 'ask':
                s = raw_input("              Do you want to overwrite it (o) or skip (s) creating this file? [o/s]: ")
                if s == 'o':
                    print "              Overwriting exisiting file."
                    overwrite = 'yes'
                else:
                    print "              Skipping."
                    continue
            elif overwrite == 'yes':
                print "              Overwriting the exisiting file."
            elif overwrite == 'no':
                print "              Skipping this conc file."
                error = True
                continue
        else:
            overwrite = 'yes'

        # --- write to target file

        if overwrite == 'yes':
            print "     ... creating %s with %d files" % (os.path.basename(concfile), len(files))
            cfile = open(concfile, 'w')

            print >> cfile, "number_of_files: %d" % (len(files))
            for tfile in files:
                print >> cfile, tfile

            cfile.close()

    if error:
        raise ge.CommandFailed("createConc", "Incomplete execution", ".conc files for some subjects were not generated", "Please check report for details!")


def runList(listfile=None, runlists=None, logfolder=None, verbose="no", eargs=None):
    """
    runList listfile=<path to runlist file> runlists=<name(s) of the list(s) to run> [logfolder=None] [verbose=no] [<extra arguments>]


    USE AND RESULTS
    ===============

    runlist takes a `runlist` file and a `runlists` list of lists and executes
    the commands defined in each list. The runlist file contains commands that 
    should be run and parameters that it should use.


    CORE PARAMETERS
    ===============

    --listfile     ... The runlist.txt file containing runlists and their 
                       parameters.
    --runlists     ... A comma, space or pipe separated list of lists specified 
                       within runlist.txt to run.
    --logfolder    ... The folder within which to save the log.
    --verbose      ... Whether to record in a log a full verbose report of the 
                       output of each command that was run ('yes') or only a
                       summary success report of each command ran. ['no']


    EXTRA PARAMETERS
    ================

    Multiple runList invocations
    ----------------------------
    
    These parameters allow spreading processing of multiple subjects across 
    multiple runList invocations:

    --subjects          ... Either a string with pipe `|` or comma separated 
                            list of subjects (sessions ids) to be processed
                            (use of grep patterns is possible), e.g. 
                            "OP128,OP139,ER*", or a path to a batch.txt or
                            *list file with a list of session ids.
    --subjid            ... An optional parameter explicitly specifying, which
                            of the subjects from the list provided by the 
                            `subjects` parameter are to be processed in this
                            call. If not specified, all subjects will be 
                            processed.
    --sperlist          ... An optional parameter specifying, how many sessions
                            to run per individual runList invocation. If not 
                            specified, all sessions will be run through the 
                            same runList invocation. 
    --runinpar          ... If multiple runList invocations are to be run, how 
                            many should be run in parallel. The default is 1.
    --scheduler         ... An optional scheduler settings description string. 
                            If provided, each runList invocation will be 
                            scheduled to run on a separate cluster node. For 
                            details about the settings string specification see 
                            the inline help for the `schedule` command.

    If these parameters are provided, the processing of the subjects will
    be split so that `sperlist` subjects will be processed by each separate
    runList invocation. If `scheduler` is specified, each runList invocation
    will be scheduled as a separate job on a cluster. 

    When processing is spread across multiple runList invocations, the 
    `sperlist` parameter will be passed forward as `cores` parameter on each
    separate invocation (see the next section). Similarly `subjid` will be
    passed on, adjusted for the sessions to be run with the specific runList
    invocation (see the next section).

    Please take note that if `runList` command is ran using a scheduler, any
    scheduler specification within the `listfile` will be ignored to avoid the
    attempts to spawn new cluster jobs when `runList` instance is already 
    running on a cluster node.

    Importantly, if `scheduler` is specified in the `runlist.txt` file, do bear 
    in mind, that all the commands in the list will be scheduled at the same 
    time, and not in a succession, as `runList` can not track execution of jobs
    on individual cluster nodes.


    Parameters to pass on or ignore
    -------------------------------

    Sometimes the parameters specified in the `listfile` need to be adjusted
    in a runList invocation. If the following parameters are listed, they will
    take precedence over parameters specified within the `listfile`: 

    --cores     ... An optional parameter specifying how many cores to utilize 
                    within a runList invocation. If cores parameter is already 
                    specified within the `listfile`, then the lower value will 
                    take precedence.
    --threads   ... An optional parameter specifying how many threads to utilize
                    within each of parallel jobs (their number) defined by 
                    `cores` parameter in a runList invocation. If threads 
                    parameter is already specified within the `listfile`, then 
                    the lower value will take precedence.
    --subjid    ... An optional parameter specifying which subjects are to be 
                    processed within this runList invocation. If `subjid` is 
                    specified within the listfile, then the value passed to 
                    runList will take precedence.

    Sometimes one would wish to ignore a parameter specified in a list when
    running a list. The parameters to ignore can be specified using:

    --ignore    ... An optional comma or pipe separated list of parameters to 
                    ignore when running any of the specified lists.


    LOGS AND FAILURES
    =================

    The log of the commands ran will be by default stored in 
    `<study>/processing/logs/runlogs` stamped with date and time that the 
    log was started. If a study folder is not yet created, please provide a 
    valid folder to save the logs to. If the log can not be created the 
    `runList` command will exit with a failure.

    `runList` is checking for a successfull completion of commands that it runs.
    If any of the commands fail to complete successfully, the execution of the
    commands will stop and the failure will be reported both in stdout as well
    as the log.

    Individual commands that are run can generate their own logs, the presence
    and location of those logs depend on the specific command and settings 
    specified in the runlist file.


    RUNLIST FILE
    ============

    At the top of the runlist.txt file global settings are defined in the form
    of `<parameter>: <value>` pairs. These are the settings that will be used as 
    defaults throughout the list and individual commands defined in the rest of 
    the runlist.txt file.

    Each list starts with a line that consists of three dashes "---" only. The
    next line should define the name of the list by specifying:
    `list: <listname>`. The list name is the one referenced in the runList 
    command. After the definition of the list, the default parameters for the
    list can be specified as a <parameter>:<value> pairs. These values will be 
    taken as the default for the list. They have priority over the general 
    runlist.txt definition in that values that are defined within a specific 
    list will be used rather than values defined at the higher level. It is 
    recommended for readibility purposes for the content of the list to be 
    indented by four spaces.

    Each list then consists of commands. Commands are defined by the:
    `command: <command name>` lines. Each `command: <command name>` specifies
    a command to be run, where <command name> is a valid mnap command. The 
    command within a list will be executed in the order they are listed. 

    Each command can then list additional parameters to be provided to the
    command in the form of `<parameter>:<value>` pairs. The values provided
    here will take priority over the values specified at the beginning of the
    list as well as over the default values provided at the beginning of the
    runlist.txt file. For readibility puposes it is advised that the 
    <parameter>:<value> pairs are further indented for additional four spaces.

    If a specific parameter specified at a higher level is not to be used at
    this level or below, it can be listed prefixed by a dash / minus sign.

    EXAMPLE RUNLIST FILE
    ====================

    ```
    # global settings
    subjectsfolder : /data/testStudy/subjects
    overwrite      : yes
    subjects       : *_baseline


    ---
    list: dataImport

        command: BIDSImport
            inbox   : /data/datalake/EMBARC/inbox/BIDS
            archive : leave

    ---
    list: prepareHCP

        command: getHCPReady

        command: createBatch
            tfile : /data/testStudy/processing/batch_baseline.txt

        command: setupHCP

    ---
    list: doHCP
        
        subjects  : /data/testStudy/processing/batch_baseline.txt
        cores     : 4

        command: hcp1

        command: hcp2

        command: hcp3

        command: hcp4
            cores     : 1
            threads   : 4

        command: hcp5
            cores     : 1
            threads   : 4

    ---
    list: prepareFCPreprocessing
        cores    : 6
        subjects : /data/testStudy/processing/batch_baseline.txt
        bolds    : all

        command: mapHCPData
            
        command: createBOLDBrainMasks

        command: computeBOLDStats
            log : remove

        command : createStatsReport
            cores : 1

        command: extractNuisanceSignal

    ---
    list: runFCPreprocessing
        
        cores     : 6
        subjects  : /data/testStudy/processing/batch_baseline.txt
        scheduler : "SLURM,jobname=doHCP,time=00-02:00:00,ntasks=6,cpus-per-task=2,mem-per-cpu=40000,partition=pi_anticevic"

        command: preprocessBold
            bold_actions     : shrc
            glm_residuals    : save
            bold_nuisance    : m,V,WM,WB,1d
            pignore          : hipass=linear|regress=spline|lopass=linear
            overwrite        : yes
            bolds            : rest
            image_target     : nifti
            hcp_cifti_tail   : 

        command: preprocessBold
            bold_actions     : shrc
            glm_residuals    : save
            bold_nuisance    : m,V,WM,WB,1d
            pignore          : hipass=linear|regress=spline|lopass=linear
            overwrite        : yes
            bolds            : rest
            image_target     : cifti
            hcp_cifti_tail   : _Atlas
    ```

    EXAMPLE USE
    ===========

    ```
    mnap runList \
      --listfile="/data/settings/runlist.txt" \
      --runlists="dataImport,prepareHCP"

    mnap runList \
      --listfile="/data/settings/runlist.txt" \
      --runlists="doHCP" \
      --subjects="/data/testStudy/processing/batch_baseline.txt" \
      --sperlist=4 \
      --scheduler="SLURM,jobname=doHCP,time=04-00:00:00,ntasks=4,cpus-per-task=2,mem-per-cpu=40000,partition=pi_anticevic"

    mnap runList \
      --listfile="/data/settings/runlist.txt" \
      --runlists="prepareFCPreprocessing" \
      --subjects="/data/testStudy/processing/batch_baseline.txt" \
      --sperlist=4 \
      --scheduler="SLURM,jobname=doHCP,time=00-08:00:00,ntasks=4,cpus-per-task=2,mem-per-cpu=40000,partition=pi_anticevic"

    mnap runList
      --listfile="/data/settings/runlist.txt" \
      --runlists="runFCPreprocessing"
    ```  

    The first call will execute all the commands in lists `dataImport` and 
    `prepareHCP` localy.

    The second call will execute all the steps of the HCP preprocessing pipeline, 
    in sequence. Execution will be spread across the nodes with each `runList` 
    instance processing four sessions at a time. Based on the settings in the 
    `runlist.txt` file, the first three HCP steps will be executed with four
    sessions running in parallel, whereas the last two fMRI steps the sessions 
    will be executed serially with four BOLDS from each session being processed in
    parallel. 

    The third call will again schedule muultiple `runList` invocations, each 
    processing four subjects at a time (the lower number of `sperlist` and `cores`).
    In this call, the initial steps will be performed on all BOLD images.

    The last, fourth call will start a single `runList` instance localy, however,
    this will submit both listed `preprocessBold` commands as jobs to be run with
    six sessions per node in parallel. These two commands will be run only on BOLD
    images tagged as `rest`. 

    ---
    Written by Jure Demšar 2019-02-11.

    Change log
    2019-03-29 Grega Repovš
             - Updated documentation, implemented running multiple lists
    2019-04-12 Jure Demšar
             - Expanded parameter handling and parameter injection
    2019-04-13 Grega Repovš
             - Updated documentation
             - Edited multiple runList invocation
             - Added option to ignore parameters
    """

    verbose = verbose.lower() == 'yes'

    flags = ['test']

    if listfile is None:
        raise ge.CommandError("runList", "listfile not specified", "No runlist file specified", "Please provide path to the runlist file!")

    if runlists is None:
        raise ge.CommandError("runList", "runlists not specified ", "No runlists specified", "Please provide list of list names to run!")

    if not os.path.exists(listfile):
        raise ge.CommandFailed("runList", "Funlist file does not exist", "Runlist file not found [%s]" % (listfile), "Please check your paths!")

    # prep log
    if logfolder is None:
        logfolder = gc.deduceFolders({'reference': listfile})["logfolder"]
    runlogfolder = os.path.join(logfolder, 'runlogs')
    logstamp = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%s")
    logname = os.path.join(runlogfolder, "Log-%s-%s.log") % ("runlist", logstamp)


    # -- parse runlist file

    runList = {'parameters': {},
               'lists':{}}

    parameters = runList['parameters']

    with open(listfile, 'r') as file:
        for line in file:
            try:
                line = line.strip()
                if line.startswith('#') or line.startswith('---') or line.strip() == "":
                    continue
                elif line.startswith('list'):
                    listName = stripQuotes(line.split(':')[1].strip())
                    runList['lists'][listName] = {'parameters': runList['parameters'].copy(), 'commands': [], 'removed_parameters': []}
                    parameters = runList['lists'][listName]['parameters']
                    removedParameters = runList['lists'][listName]['removed_parameters']
                elif line.startswith('command'):
                    commandName = stripQuotes(line.split(':')[1].strip())
                    parameters = runList['lists'][listName]['parameters'].copy()
                    removedParameters = list(runList['lists'][listName]['removed_parameters'])
                    runList['lists'][listName]['commands'].append({'name': commandName, 'parameters': parameters, 'removed_parameters': removedParameters})
                elif ':' in line:
                    parameter, value = [stripQuotes(e.strip()) for e in line.split(":", 1)]
                    parameters[parameter] = value
                elif line.strip() in flags:
                    parameters[line.strip()] = "flag"
                elif line.strip().startswith('-'):
                    keyToRemove = line.strip()[1:]
                    if keyToRemove in parameters:
                        # mark parameter as removed
                        removedParameters.append(keyToRemove)
                        del parameters[keyToRemove]
                    # also remove arguments that come from eargs
                    elif eargs is not None and keyToRemove in eargs:
                        # mark parameter as removed
                        removedParameters.append(keyToRemove)

            except:
                raise ge.CommandFailed("runList", "Cannot parse line", "Unable to parse line [%s]" % (line), "Please check the runlist file [%s]" % listfile)

    # -- are there parameters to ignore

    if 'ignore' in eargs:
        ignore = [e.strip() for e in re.split(' ?, ?| ?\| ?| +|', eargs['ignore'])]
    else:
        ignore = None

    # -- run through lists

    runLists = re.split(' ?, ?| ?\| ?| +|', runlists)
    summary = "\n----==== LISTS EXECUTION SUMMARY ====----"

    try:
        log = open(logname, "w", buffering=0)
    except:
        raise ge.CommandFailed("runList", "Cannot open log", "Unable to open log [%s]" % (logname), "Please check the paths!")

    print >> log, "\n\n============================== RUNLIST LOG ==============================\n"
    print "===> Running commands from the following lists:", ", ".join(runLists)
    print >> log, "===> Running commands from the following lists:", ", ".join(runLists), "\n"

    for runListName in runLists:
        if runListName not in runList['lists']:
            raise ge.CommandFailed("runList", "List not found", "List with name %s not found" % (runListName), "Please check the runlist file [%s]" % listfile)

        summary += "\n\n===> list: %s" % (runListName)

        print "===> Running commands from list:", runListName
        print >> log, "\n----------==================== LIST ====================---------\n"
        print >> log, "===> Running commands from list:", runListName, "\n"

        commandsToRun = list(runList['lists'][runListName]['commands'])
        
        for runCommand in commandsToRun:
            commandName = runCommand['name']
            commandParameters = runCommand['parameters']

            # -- override params with those from eargs (passed because of parallelization on a higher level)

            if eargs is not None:
                # do not add parameter if it is flagged as removed
                removedParameters = runCommand['removed_parameters']
                for k in eargs:
                    if k not in removedParameters:
                        if k in ['cores', 'threads']:
                            commandParameters[k] = str(min([int(e) for e in [eargs[k], commandParameters[k]]]))
                        else:
                            commandParameters[k] = eargs[k]

            # -- remove parameters that are not allowed

            if commandName in niutilities.g_commands.commands:
                allowedParameters = list(niutilities.g_commands.commands.get(commandName)["args"]) 
                if any([e in allowedParameters for e in ['sfolder', 'folder']]):
                    allowedParameters += niutilities.g_commands.extraParameters
                for param in commandParameters.keys():
                    if param not in allowedParameters:
                        del commandParameters[param]

            # -- remove parameters set to ignore

            if ignore:
                for toIgnore in ignore:
                    del commandParameters[toIgnore]

            # -- setup command 

            command = ["mnap"]
            command.append(commandName)
            commandr = "\n--------------------------------------------\n===> Running new command:\n---> mnap " + commandName
            for param, value in commandParameters.iteritems():
                if param in flags:
                    command.append('--%s' % (param))
                    commandr += " \\\n          --%s" % (param)
                else:
                    command.append('--%s=%s' % (param, value))
                    commandr += ' \\\n          --%s="%s"' % (param, value)
                        
            print commandr
            print >> log, commandr

            # -- run command
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)

            # Poll process for new output until finished
            error = True
            logging = verbose

            for line in iter(process.stdout.readline, b''):
                print line,
                if "Successful completion" in line:
                    error = False
                if "Final report" in line:
                    if not verbose:
                        print >> log, ""
                    logging = True

                # print
                if logging:
                    print >> log, line,
                    log.flush()

            if error:
                summary += "\n---> command %-20s FAILED" % (commandName)
                summary += "\n\n----------==== END SUMMARY ====----------"
                print >> log, summary
                print >> log, "\n---> Running lists not completed successfully: failed running command '%s' in list '%s'" % (commandName, runListName)
                log.close()
                raise ge.CommandFailed("runlist", "Runlist command failed", "Command '%s' inside list '%s' failed" % (commandName, runListName), "See errors above for details")
            else:
                summary += "\n---> command %-20s OK" % (commandName)                
                print "===> Successful completion of runlist command %s" % (commandName)
    summary += "\n\n----------==== END SUMMARY ====----------"
    
    print >> log, summary
    print >> log, "\n===> Successful completion of task: runLists %s" % (", ".join(runLists))

    print "===> Successful completion of runLists %s" % (", ".join(runLists))
    print summary

    log.close()

def stripQuotes(string):
    """
    A helper function for removing leading and trailing quotes in a string. 
    """
    string = string.strip("\"")
    string = string.strip("'")
    return string

def batchTag2Num(filename=None, subjid=None, bolds=None):
    """
    batchTag2Num filename=<path to batch file> subjid=<session id> bolds=<bold specification string>

    The function reads the batch file, extracts the data for the specified 
    session and returns the list of bold numbers that correspond to bolds
    specified using the `bolds` parameter.

    --filename      ... Path to batch.txt file.
    --subjid        ... Subject id to look up.
    --bolds         ... Which bold images (as they are specified in the
                        batch.txt file) to process. It can be a single
                        type (e.g. 'task'), a pipe separated list (e.g.
                        'WM|Control|rest') or 'all' to process all.
    """

    if filename is None:
        raise ge.CommandError("batchTag2Num", "No batch file specified!")

    if subjid is None:
        raise ge.CommandError("batchTag2Num", "No session id specified!")

    if bolds is None:
        raise ge.CommandError("batchTag2Num", "No bolds specified!")

    subjects, _ = gc.getSubjectList(filename, subjid=subjid)

    if not subjects:
        raise ge.CommandFailed("batchTag2Num", "Session id not found", "Session id %s is not present in the batch file [%s]" % (subjid, filename), "Please check your data!")

    if len(subjects) > 1:
        raise ge.CommandFailed("batchTag2Num", "More than one session id found", "More than one [%s] instance of session id [%s] is present in the batch file [%s]" % (len(subjects), subjid, filename), "Please check your data!")

    subject = subjects[0]

    bolds, _, _, _ = gpc.useOrSkipBOLD(subject, {'bolds': bolds})
    
    bolds = [str(e[0]) for e in bolds]

    print "BOLDS:%s" % (",".join(bolds))
