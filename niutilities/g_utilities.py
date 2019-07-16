#!/usr/bin/env python2.7
# encoding: utf-8
"""
Miscellaneous utilities for file processing.

Created by Grega Repovs on 2017-09-17.
Copyright (c) Grega Repovs. All rights reserved.
"""

import os.path
import os
import shutil
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
#  This file is used to specify the default parameters used by various Qu|Nex commands for
#  HCP minimal preprocessing pipeline, additional bold preprocessing commands,
#  and other analytic functions. The content of this file should be prepended to the list
#  that contains all the sessions that is passed to the commands. It can added manually or
#  automatically when making use of the compileLists Qu|Nex command.
#
#  This template file should be edited to include the parameters relevant for
#  a given study/analysis and provide the appropriate values. For detailed description of
#  parameters and their valid values, please consult the Qu|Nex documentation
*  (e.g. Running HCP minimal preprocessing pipelines, Additional BOLD
#  preprocessing) and online help for the relevant Qu|Nex commands.
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

        markFile = os.path.join(studyfolder, '.qunexstudy')
        if os.path.exists(markFile) or os.path.exists(os.path.join(studyfolder, '.mnapstudy')):
            print " ... .qunexstudy file already exists"
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
    <studyfolder>/subjects/specs folder. Finally, it creates a .qunexstudy file in
    the <studyfolder> to identify it as a study basefolder.

    Example:

    $ qunex createStudy studyfolder=/Volumes/data/studies/WM.v4

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
    2019-05-28 Grega Repovs
             - Changes to qunex.
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
        if os.path.exists(os.path.join(testfolder, '.qunexstudy')) or os.path.exists(os.path.join(testfolder, '.mnapstudy')):
            studyfolder = testfolder
            break
        testfolder = os.path.dirname(testfolder)

    if studyfolder:
        manageStudy(studyfolder=studyfolder, action="check")

    return studyfolder  


def createBatch(subjectsfolder=".", sfile="subject_hcp.txt", tfile=None, sessions=None, sfilter=None, overwrite="no", paramfile=None):
    '''
    createBatch [subjectsfolder=.] [sfile=subject_hcp.txt] [tfile=processing/batch.txt] [sessions=None] [sfilter=None] [overwrite=no] [paramfile=<subjectsfolder>/specs/batch_parameters.txt]

    Combines all the sfile in all session folders in subjectsfolder to
    generate a joint batch file and save it as tfile. If only specific sessions
    are to be added or appended, "sessions" parameter can be used. This can be
    a pipe, comma or space separated list of session ids, another batch file or
    a list file. If a string is provided, grob patterns can be used (e.g.
    sessions="AP*|OR*") and all matching sessions will be processed.

    If no tfile is specified, it will save the file as batch.txt in a
    processing folder parallel to the subjectsfolder. If the folder does not yet
    exist, it will create it.

    If tfile already exists, depending on "overwrite" parameter it will:

    - ask:    ask interactively
    - yes:    overwrite the existing file
    - no:     abort creating the file
    - append: append sessions to the existing file

    Note that if If a batch file already exists then parameter file will not be 
    added to the header of the batch unless --overwrite is set to "yes". If 
    --overwrite is set to "append", then the parameters will not be changed, 
    however, any sessions that are not yet present in the batch file will be 
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

    Example
    =======
    
    ```
    qunex createBatch sfile="subject.txt" tfile="fcMRI/subjects_fcMRI.txt"
    ```

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
    2019-04-25 Grega Repovš
             - Changed subjects to sessions
    2019-05-02 Grega Repovš
             - Added subjectsfolder to getSubjectList call
    2019-05-12 Grega Repovš
             - Reports an error if no session is found to add to batch
    2019-05-22 Grega Repovš
             - Added full path to report
    '''

    print "Running createBatch\n==================="

    if sessions and sessions.lower() == 'none':
        sessions = None

    if sfilter and sfilter.lower() == 'none':
        sfilter = None

    subjectsfolder = os.path.abspath(subjectsfolder)

    # --- prepare target file name and folder

    if tfile is None:
        tfile = os.path.join(os.path.dirname(subjectsfolder), 'processing', 'batch.txt')

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
        print "---> Creating file %s [%s]" % (os.path.basename(tfile), tfile)
        jfile = open(tfile, 'w')
        print >> jfile, "# File generated automatically on %s" % (datetime.datetime.today())
        print >> jfile, "# Subjects folder: %s" % (subjectsfolder)
        print >> jfile, "# Source files: %s" % (sfile)
        slist   = []

    elif overwrite == 'append':
        slist, parameters = gc.getSubjectList(tfile)
        slist = [e['id'] for e in slist]
        print "---> Appending to file %s [%s]" % (os.path.basename(tfile), tfile)
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

    if sessions is not None:
        sessions, gopts = gc.getSubjectList(sessions, sfilter=sfilter, verbose=False, subjectsfolder=subjectsfolder)
        files = []
        for session in sessions:
            nfiles = glob.glob(os.path.join(subjectsfolder, session['id'], sfile))
            if nfiles:
                files += nfiles
            else:
                print "---> ERROR: no %s found for %s! Please check your data! [%s]" % (sfile, session['id'], os.path.join(subjectsfolder, session['id'], sfile))
                missing += 1
    else:
        files = glob.glob(os.path.join(subjectsfolder, '*', sfile))

    # --- loop trough session files

    files.sort()
    for file in files:
        sessionid = os.path.basename(os.path.dirname(file))
        if sessionid in slist:
            print "---> Skipping: %s" % (sessionid)
        else:
            print "---> Adding: %s" % (sessionid)
            print >> jfile, "\n---"
            with open(file) as f:
                for line in f:
                    print >> jfile, line,

    if not files:
        raise ge.CommandFailed("createBatch", "No session found", "No sessions found to add to the batch file!", "Please check your data!")

    # --- close file

    jfile.close()

    if missing:
        raise ge.CommandFailed("createBatch", "Not all sessions specified added to the batch file!", "%s was missing for %d session(s)!" % (sfile, missing), "Please check your data!")



def createList(subjectsfolder=".", sessions=None, sfilter=None, listfile=None, bolds=None, conc=None, fidl=None, glm=None, roi=None, boldname="bold", boldtail=".nii.gz", overwrite='no', check='yes'):
    """
    createList [subjectsfolder="."] [sessions=None] [sfilter=None] [listfile=None] [bolds=None] [conc=None] [fidl=None] [glm=None] [roi=None] [boldname="bold"] [boldtail=".nii.gz"] [overwrite="no"] [check="yes"]

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
    - append: append sessions to the existing file

    The sessions to list
    --------------------

    Sessions to include in the list are specified using `sessions` parameter.
    This can be a pipe, comma or space separated list of session ids, a batch
    file or another list file. If a string is provided, grob patterns can be
    used (e.g. sessions="AP*|OR*") and all matching sessions will be included.

    If a batch file is provided, sessions can be filtered using the `sfilter`
    parameter. The parameter should be provided as a string in the format:

    "<key>:<value>|<key>:<value>"

    Only the sessions for which all the specified keys match the specified values
    will be included in the list.

    If no sessions are specified, the function will inspect the `subjectsfolder`
    and include all the sessions for which an `images` folder exists as a
    subfolder in the sessions's folder.

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

    file:<subjectsfolder>/<session id>/images/functional/<boldname><boldnumber><boldtail>

    *conc files*
    To include conc files, provide a `conc` parameter. In the parameter list the
    name of the conc file to be include. Conc files will be listed as:

    conc:<subjectsfolder>/<session id>/images/functional/concs/<conc>

    *fidl files*
    To include fidl files, provide a `fidl` parameter. In the parameter list the
    name of the fidl file to include. Fidl files will be listed as:

    fidl:<subjectsfolder>/<session id>/images/functional/events/<fidl>

    *GLM files*
    To include GLM files, provide a `glm` parameter. In the parameter list the
    name of the GLM file to include. GLM files will be listed as:

    glm:<subjectsfolder>/<session id>/images/functional/<glm>

    *ROI files*
    To include ROI files, provide a `roi` parameter. In the parameter list the
    name of the ROI file to include. ROI files will be listed as:

    roi:<subjectsfolder>/<session id>/images/<roi>

    Note that for all the files the function expects the files to be present in
    the correct places within the Qu|Nex subjects folder structure. For ROI files
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
    
    ```
    qunex createList bolds="1,2,3"
    ```

    The command will create a list file in `../processing/list/subjects.txt` that
    will list for all the sessions found in the current folder BOLD files 1, 2, 3
    listed as:

      file:<current path>/<session id>/images/functional/bold[n].nii.gz

    ```
    qunex createList subjectsfolder="/studies/myStudy/subjects" sessions="batch.txt" \\
            bolds="rest" listfile="lists/rest.list" boldtail="_Atlas_g7_hpss_res-mVWMWB1d.dtseries"
    ```

    The command will create a `lists/rest.list` list file in which for all the
    sessions specified in the `batch.txt` it will list all the BOLD files tagged
    as rest runs and include them as:

      file:<subjectsfolder>/<session id>/images/functional/bold[n]_Atlas_g7_hpss_res-mVWMWB1d.dtseries

    ```
    qunex createList subjectsfolder="/studies/myStudy/subjects" sessions="batch.txt" \\
            sfilter="EC:use" listfile="lists/EC.list" \\
            conc="bold_Atlas_dtseries_EC_g7_hpss_res-mVWMWB1de.conc" \\
            fidl="EC.fidl" glm="bold_conc_EC_g7_hpss_res-mVWMWB1de_Bcoeff.nii.gz" \\
            roi="segmentation/hcp/fsaverage_LR32k/aparc.32k_fs_LR.dlabel.nii"
    ```

    The command will create a list file in `lists/EC.list" that will list for
    all the sessions in the conc file, that have the key:value pair "EC:use" the
    following files:

      conc:<subjectsfolder>/<session id>/images/functional/concs/bold_Atlas_dtseries_EC_g7_hpss_res-mVWMWB1de.conc
      fidl:<subjectsfolder>/<session id>/images/functional/events/EC.fidl
      glm:<subjectsfolder>/<session id>/images/functional/bold_conc_EC_g7_hpss_res-mVWMWB1de_Bcoeff.nii.gz
      roi:<subjectsfolder>/<session id>/images/segmentation/hcp/fsaverage_LR32k/aparc.32k_fs_LR.dlabel.nii

    ----------------
    Written by Grega Repovš 2018-06-26

    Change log
    2019-04-25 Grega Repovš
             - Changed subjects to sessions
    2019-05-02 Grega Repovš
             - Added subjectsfolder to getSubjectList call
    2019-05-12 Grega Repovš
             - Reports an error if no session is found to add to the list file
    2019-05-30 Grega Repovš
             - Fixed a None checkup bug

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

    # --- check sessions

    subjectsfolder = os.path.abspath(subjectsfolder)

    if sessions and sessions.lower() == 'none':
        sessions = None

    if sfilter and sfilter.lower() == 'none':
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
        listfile = os.path.join(os.path.dirname(subjectsfolder), 'processing', 'lists', 'subjects.list')
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

    # --- check sessions

    if sessions is None:
        print "WARNING: No sessions specified. The list will be generated for all sessions in the subjects folder!"
        sessions = glob.glob(os.path.join(subjectsfolder, '*', 'images'))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.getSubjectList(sessions, sfilter=sfilter, verbose=False, subjectsfolder=subjectsfolder)

    if not sessions:
        raise ge.CommandFailed("createList", "No session found", "No sessions found to add to the list file!", "Please check your data!")

    # --- generate list entries

    lines = []

    for session in sessions:
        lines.append("subject id: %s" % (session['id']))

        if boldnums:
            for boldnum in boldnums:
                tfile = os.path.join(subjectsfolder, session['id'], 'images', 'functional', boldname + boldnum + boldtail)
                checkFile(tfile)
                lines.append("    file:" + tfile)

        if boldtags:
            try:
                bolds = [(bsearch.match(v['name']).group(1), v['name'], v['task']) for (k, v) in session.iteritems() if k.isdigit() and bsearch.match(v['name'])]
                if "all" not in boldtags:
                    bolds = [n for n, b, t in bolds if t in boldtags]
                else:
                    bolds = [n for n, b, t in bolds]
                bolds.sort()
            except:
                pass
            for boldnum in bolds:
                tfile = os.path.join(subjectsfolder, session['id'], 'images', 'functional', boldname + boldnum + boldtail)
                checkFile(tfile)
                lines.append("    file:" + tfile)

        if roi:
            tfile = os.path.join(subjectsfolder, session['id'], 'images', roi)
            checkFile(tfile)
            lines.append("    roi:" + tfile)

        if glm:
            tfile = os.path.join(subjectsfolder, session['id'], 'images', 'functional', glm)
            checkFile(tfile)
            lines.append("    glm:" + tfile)

        if conc:
            tfile = os.path.join(subjectsfolder, session['id'], 'images', 'functional', 'concs', conc)
            checkFile(tfile)
            lines.append("    conc:" + tfile)

        if fidl:
            tfile = os.path.join(subjectsfolder, session['id'], 'images', 'functional', 'events', fidl)
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



def createConc(subjectsfolder=".", sessions=None, sfilter=None, concfolder=None, concname="", bolds=None, boldname="bold", boldtail=".nii.gz", overwrite='no', check='yes'):
    """
    createConc [subjectsfolder="."] [sessions=None] [sfilter=None] [concfolder=None] [concname=""] [bolds=None] [boldname="bold"] [boldtail=".nii.gz"] [overwrite="no"] [check="yes"]

    The function creates a set of .conc formated files that can be used as input
    to a number of processing and analysis functions. The function is fairly
    flexible, its output defined using a number of parameters.

    The location of the files
    -------------------------

    The files are created at the path specified in `concfolder` parameter. If no
    parameter is provided, the resulting files are saved in:

    <studyfolder>/<session id>/inbox/concs/

    Individual files are named using the following formula:

    <session id><concname>.conc

    If a file already exists, depending on the `overwrite` parameter the
    function will:

    - ask:    ask interactively, what to do
    - yes:    overwrite the existing file
    - no:     abort creating the file

    The sessions to list
    --------------------

    Sessions to include in the generation of conc files are specified using
    `sessions` parameter.  This can be a pipe, comma or space separated list of
    sessions ids, a batch file or another list file. If a string is provided,
    grob patterns can be used (e.g. sessions="AP*|OR*") and all matching
    sessions will be included.

    If a batch file is provided, sessions can be filtered using the `sfilter`
    parameter. The parameter should be provided as a string in the format:

    "<key>:<value>|<key>:<value>"

    The conc files will be generated only for the sessions for which all the
    specified keys match the specified values.

    If no sessions are specified, the function will inspect the `subjectsfolder`
    and generate conc files for all the sessions for which an `images` folder
    exists as a subfolder in the sessions's folder.

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

    file:<subjectsfolder>/<session id>/images/functional/<boldname><boldnumber><boldtail>

    Note that the function expects the files to be present in the correct place
    within the Qu|Nex subjects folder structure.

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
    
    ```
    qunex createConc bolds="1,2,3"
    ```

    The command will create set of conc files in `/inbox/concs`,
    each of them named <session id>.conc, one for each of the sessions found in
    the current folder. Each conc file will include BOLD files 1, 2, 3
    listed as:

      file:<current path>/<session id>/images/functional/bold[n].nii.gz
    
    ```
    qunex createConc subjectsfolder="/studies/myStudy/subjects" sessions="batch.txt" \\
            bolds="WM" concname="_WM" boldtail="_Atlas.dtseries.nii"
    ```

    The command will create for each session listed in the `batch.txt` a
    `<session id>_WM.conc` file in `subjects/inbox/concs` in which it will list
    all the BOLD files tagged as `WM` as:

      file:<subjectsfolder>/<session id>/images/functional/bold[n]_Atlas.dtseries

    ```
    qunex createConc subjectsfolder="/studies/myStudy/subjects" sessions="batch.txt" \\
            sfilter="EC:use" concfolder="analysis/EC/concs" \\
            concname="_EC_g7_hpss_res-mVWMWB1de" bolds="EC" \\
            boldtail="_g7_hpss_res-mVWMWB1deEC.dtseries.nii"
    ```

    For all the sessions in the `batch.txt` file that have the key:value pair
    "EC:use" set the command will create a conc file in `analysis/EC/concs`
    folder. The conc files will be named `<session id>_EC_g7_hpss_res-mVWMWB1de.conc`
    and will list all the bold files that are marked as `EC` runs as:

      file:<subjectsfolder>/<session id>/images/functional/bold[N]_g7_hpss_res-mVWMWB1deEC.dtseries.nii

    ----------------
    Written by Grega Repovš 2018-06-30

    Change log
    2019-04-25 Grega Repovš
             - Changed subjects to sessions
    2019-05-02 Grega Repovš
             - Added subjectsfolder to getSubjectList call
    2019-05-12 Grega Repovš
             - Reports an error if no session is found to be processed
    2019-05-30 Grega Repovš
             - Fixed a None checkup bug
    2019-06-20 Grega Repovš
             - Fixed a sessions parameter name bug 
             - Fixed sorting by bold number
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

    # --- check sessions

    if sessions and sessions.lower() == 'none':
        sessions = None

    if sfilter and sfilter.lower() == 'none':
        sfilter = None

    subjectsfolder = os.path.abspath(subjectsfolder)

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
        concfolder = os.path.join(subjectsfolder, 'inbox', 'concs')
        print "WARNING: No target conc folder specified.\n         The conc files will be created in folder: %s!" % (concfolder)

    if not os.path.exists(concfolder):
        print "---> Creating target folder %s" % (concfolder)
        os.makedirs(concfolder)

    # --- check sessions

    if sessions is None:
        print "WARNING: No sessions specified. The list will be generated for all sessions in the subjects folder!"
        sessions = glob.glob(os.path.join(subjectsfolder, '*', 'images'))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.getSubjectList(sessions, sfilter=sfilter, verbose=False, subjectsfolder=subjectsfolder)

    if not sessions:
        raise ge.CommandFailed("createConc", "No session found", "No sessions found to add to the list file!", "Please check your data!")


    # --- generate list entries

    error = False
    for session in sessions:

        print "---> Processing session %s" % (session['id'])
        files = []
        complete = True

        if boldnums:
            for boldnum in boldnums:
                tfile = os.path.join(subjectsfolder, session['id'], 'images', 'functional', boldname + boldnum + boldtail)
                complete = complete & checkFile(tfile)
                files.append("    file:" + tfile)

        if boldtags:
            try:
                bolds = [(int(bsearch.match(v['name']).group(1)), v['name'], v['task']) for (k, v) in session.iteritems() if k.isdigit() and bsearch.match(v['name'])]
                if "all" not in boldtags:
                    bolds = [n for n, b, t in bolds if t in boldtags]
                else:
                    bolds = [n for n, b, t in bolds]
                bolds.sort()
            except:
                pass
            for boldnum in bolds:
                tfile = os.path.join(subjectsfolder, session['id'], 'images', 'functional', boldname + str(boldnum) + boldtail)
                complete = complete & checkFile(tfile)
                files.append("    file:" + tfile)

        concfile = os.path.join(concfolder, session['id'] + concname + '.conc')

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
        raise ge.CommandFailed("createConc", "Incomplete execution", ".conc files for some sessions were not generated", "Please check report for details!")


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
    
    These parameters allow spreading processing of multiple sessions across 
    multiple runList invocations:

    --sessions          ... Either a string with pipe `|` or comma separated 
                            list of sessions (sessions ids) to be processed
                            (use of grep patterns is possible), e.g. 
                            "OP128,OP139,ER*", or a path to a batch.txt or
                            *list file with a list of session ids.
    --subjid            ... An optional parameter explicitly specifying, which
                            of the sessions from the list provided by the 
                            `sessions` parameter are to be processed in this
                            call. If not specified, all sessions will be 
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

    If these parameters are provided, the processing of the sessions will
    be split so that `sperlist` sessions will be processed by each separate
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
    --subjid    ... An optional parameter specifying which sessions are to be 
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
    a command to be run, where <command name> is a valid qunex command. The 
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
    sessions       : *_baseline


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
        
        sessions  : /data/testStudy/processing/batch_baseline.txt
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
        sessions : /data/testStudy/processing/batch_baseline.txt
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
        sessions  : /data/testStudy/processing/batch_baseline.txt
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
    qunex runList \
      --listfile="/data/settings/runlist.txt" \
      --runlists="dataImport,prepareHCP"
    ```
    
    ```
    qunex runList \
      --listfile="/data/settings/runlist.txt" \
      --runlists="doHCP" \
      --sessions="/data/testStudy/processing/batch_baseline.txt" \
      --sperlist=4 \
      --scheduler="SLURM,jobname=doHCP,time=04-00:00:00,ntasks=4,cpus-per-task=2,mem-per-cpu=40000,partition=pi_anticevic"
    ```

    ```
    qunex runList \
      --listfile="/data/settings/runlist.txt" \
      --runlists="prepareFCPreprocessing" \
      --sessions="/data/testStudy/processing/batch_baseline.txt" \
      --sperlist=4 \
      --scheduler="SLURM,jobname=doHCP,time=00-08:00:00,ntasks=4,cpus-per-task=2,mem-per-cpu=40000,partition=pi_anticevic"
    ```

    ```
    qunex runList
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
    processing four sessions at a time (the lower number of `sperlist` and `cores`).
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
    2019-04-25 Grega Repovš
             - Changed subjects to sessions
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
                            if k in commandParameters:
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
                    if toIgnore in commandParameters:
                        del commandParameters[toIgnore]

            # -- setup command 

            command = ["qunex"]
            command.append(commandName)
            commandr = "\n--------------------------------------------\n===> Running new command:\n---> qunex " + commandName
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


def batchTag2NameKey(filename=None, subjid=None, bolds=None, output='number', prefix="BOLD_"):
    """
    batchTag2NameKey filename=<path to batch file> subjid=<session id> bolds=<bold specification string> output=<keytype> prefix=<prefix to use>

    The function reads the batch file, extracts the data for the specified 
    session and returns the list of bold numbers or names that correspond to bolds
    specified using the `bolds` parameter.

    --filename      ... Path to batch.txt file.
    --subjid        ... Session id to look up.
    --bolds         ... Which bold images (as they are specified in the
                        batch.txt file) to process. It can be a single
                        type (e.g. 'task'), a pipe separated list (e.g.
                        'WM|Control|rest') or 'all' to process all.
    --output        ... Whether to output numbers ('number') or bold names 
                        In the latter case the name will be 'boldname', if 
                        provided in the batch file, or '<prefix>[N]' if one does
                        not exist.
    --prefix        ... The default prefix to use if a boldname is not specified
                        in the batch file.
    """

    if filename is None:
        raise ge.CommandError("batchTag2Num", "No batch file specified!")

    if subjid is None:
        raise ge.CommandError("batchTag2Num", "No session id specified!")

    if bolds is None:
        raise ge.CommandError("batchTag2Num", "No bolds specified!")

    sessions, _ = gc.getSubjectList(filename, subjid=subjid)

    if not sessions:
        raise ge.CommandFailed("batchTag2Num", "Session id not found", "Session id %s is not present in the batch file [%s]" % (subjid, filename), "Please check your data!")

    if len(sessions) > 1:
        raise ge.CommandFailed("batchTag2Num", "More than one session id found", "More than one [%s] instance of session id [%s] is present in the batch file [%s]" % (len(sessions), subjid, filename), "Please check your data!")

    session = sessions[0]

    bolds, _, _, _ = gpc.useOrSkipBOLD(session, {'bolds': bolds})

    boldlist = []
    for boldnumber, boldname, boldtask, boldinfo in bolds:
        if output == 'name':
            if 'boldname' in boldinfo:
                boldlist.append(boldinfo['boldname'])
            else:
                boldlist.append("%s%d" % (prefix, boldnumber))
        else:
            boldlist.append(str(boldnumber))

    print "BOLDS:%s" % (",".join(boldlist))


def gatherBehavior(subjectsfolder=".", sessions=None, sfilter=None, sfile="behavior.txt", tfile=None, overwrite="no", check="yes", report="yes"):
    """
    gatherBehavior [subjectsfolder="."] [sessions=None] [sfilter=None] [sfile="behavior.txt"] [tfile="<subjectsfolder>/inbox/behavior/behavior.txt"] [overwrite="no"] [check="yes"]

    The function gathers specified individual behavioral data from each 
    session's behavior folder and compiles it into a specified group behavioral
    file.

    Parameters
    ----------

    --subjectsfolder  The base study subjects folder (e.g. WM44/subjects) where
                      the inbox and individual subject folders are. If not 
                      specified, the current working folder will be taken as 
                      the location of the subjectsfolder. [.]
    
    --sessions        Either a string with pipe `|` or comma separated list of 
                      sessions (sessions ids) to be processed (use of grep 
                      patterns is possible), e.g. "AP128,OP139,ER*", or a path
                      to a batch.txt or *list file with a list of session ids.
                      [*]

    --sfilter         Optional parameter used to filter sessions to include. It
                      is specifed as a string in format:
    
                      "<key>:<value>|<key>:<value>"

                      Only the sessions for which all the specified keys match
                      the specified values will be included in the list.

    --sfile           A file or comma or pipe `|` separated list of files or
                      grep patterns that define, which subject specific files 
                      from the behavior folder to gather data from. 
                      ['behavior.txt']

    --tfile           The path to the target file, a file that will contain
                      the joined data from all the individual subject files.
                      ['<subjectsfolder>/inbox/behavior.txt']

    --overwrite       Whether to overwrite an existing group behavioral file or
                      not. ['no']

    --check           Check whether all the identified sessions have data to 
                      include in the compiled group file. The possible options
                      are:

                      * yes   ... Check and report an error if no behavioral
                                  data exists for a session
                      * warn  ... Warn and list the subjects for which the 
                                  behavioral data was not found
                      * no    ... Do not run a check, ignore sessions for which
                                  no behavioral data was found

    --report          Whether to include date when file was generated and the 
                      final report in the compiled file ('yes') or not ('no'). 
                      ['yes']

    Use
    ---
    
    The command will use the `subjectfolder`, `sessions` and `sfilter` 
    parameters to create a list of sessions to process. For each session, the
    command will use the `sfile` parameter to identify behavioral files from
    which to compile the data from. If no file is found for a session and the
    `check` parameter is set to `yes`, the command will exit with an error.

    Once the files for each session are identified, the command will read all
    the files and compile the data into a key:value dictionary for that session.
    Once all the sessions are processed, a group file will be generated for 
    all the values encountered across sessions. If any session is missing data,
    the missing data will be identified as 'NA'

    Group data will be saved to a file specified using `tfile` parameter. If no
    path is specified, the default location will be used:

    <subjectsfolder>/inbox/behavior/behavior.txt

    If a target file exists, it will be deleted and replaced, if the `overwrite`
    parameter is set to 'yes'. If the overwrite parameter is set to 'no', the 
    command will exit with an error.

    
    File format
    -----------

    Both the individual and the resulting group data is to be stored using a tab
    separated value format files. Any line that starts with a hash `#` will be
    ignored. The first valid line should hold the header, specifying the names
    of the columns. All the following lines hold the values. Individual session
    files should have a single line of data. The first column of the group file
    will hold the session id.

    In addition, if `report` is set to 'yes' (the default), the resulting file 
    will start with a comment line stating the date of creation, and at the end
    additional comment lines will list the full report of missing files and 
    errors encounterdd while gathering behavioral data from individual sessions.


    Examples
    --------

    $ qunex gatherBehavior sessions="AP*"

    The command will compile behavioral data present in `behavior.txt` files 
    present in all `<session id>/behavior` folder that match the "AP*" glob
    pattern in the current folder. 

    The resulting file will be save in the default location:

    <current folder>/inbox/behavior

    If any of the identified sessions do not include data or if errors are 
    encountered when processing the data, the command will exit with an error.
    
    ```
    qunex gatherBehavior subjectsfolder="/data/myStudy/subjects" \\
            sessions="AP*|OP*" sfile="*test*|*results*" \\
            check="warn" overwrite="yes" report="no"
    ```

    The command will find all the session folders within `/data/myStudy/subjects`
    that have a `behavior` subfolder. It will then look for presence of any 
    files that match "*test*" or "*results*" glob pattern. The compiled data 
    will be saved in the default location. If a file already exists, it will be
    overwritten. If any errors are encountered, the command will not throw an 
    error, however it also won't report a successful completion of the task.
    The resulting file will not have information on file generation or 
    processing report.

    ```
    qunex gatherBehavior subjectsfolder="/data/myStudy/subjects" \\
            sessions="/data/myStudy/processing/batch.txt" \\           
            sfilter="group:controls|behavioral:yes" \\
            sfile="*test*|*results*" \\
            tfile="/data/myStudy/analysis/n-bridge/controls.txt" \\
            check="no" overwrite="yes"
    ```

    The command will read the session information from the provided batch.txt 
    file. It will then process only those sessions that have the following
    lines in their description:

    group: control
    behavioral: yes

    For those sessions it will inspect '<session id>/behavior' folder for 
    presence of files that match either '*test*' or '*results*' glob pattern.
    The compiled data will be saved to the specified target file. If the target
    file exists, it will be overwritten. The command will print a full report 
    of the processing, however, it will exit with reported success even if 
    missing files or errors were encountered.

    ----------------
    Written by Grega Repovš 2019-05-02
    
    Change log

    2019-05-12 Grega Repovš
             - Reports an error if no session is found to process
    """

    # --- Support function

    def addData(file, sdata, keys):

        header = None
        data   = None

        with(open(file, 'r')) as f:
            for line in f:
                if line.startswith('#'):
                    continue
                elif header is None:
                    header = [e.strip() for e in line.split('\t')]
                elif data is None:
                    data = [e.strip() for e in line.split('\t')]
        
        ndata   = len(data)
        nheader = len(header)
        if ndata != nheader:
            return "Number of header [%d] and data [%d] fields do not match!" % (nheader, ndata)

        for n in range(ndata):
            if header[n] in sdata:
                if sdata[header[n]] != data[n]:
                    return "File [%s] has duplicate and nonmatching ['%s' vs '%s'] data for variable '%s'!" % (file, data[n], sdata[header[n]], header[n])
            else:
                sdata[header[n]] = data[n]
                if header[n] not in keys:
                    keys.append(header[n])


    # --- Start it up

    print "Running gatherBehavior\n======================"

    # --- check subjects folder

    subjectsfolder = os.path.abspath(subjectsfolder)

    if not os.path.exists(subjectsfolder):
        raise ge.CommandFailed("gatherBehavior", "Subjects folder does not exist", "The specified subjects folder does not exist [%s]" % (subjectsfolder), "Please check paths!")

    # --- check target file

    if tfile is None:
        tfile = os.path.join(subjectsfolder, 'inbox', 'behavior', 'behavior.txt')

    overwrite = overwrite.lower() == 'yes'

    if os.path.exists(tfile):
        if overwrite:
            try:
                os.remove(tfile)
            except:
                raise ge.CommandFailed("gatherBehavior", "Could not remove target file", "Existing object at the specified target location could not be deleted [%s]" % (tfile), "Please check your paths and authorizations!")        
        else:
            raise ge.CommandFailed("gatherBehavior", "Target file exists", "The specified target file already exists [%s]" % (tfile), "Please check your paths or set overwrite to 'yes'!")        

    # --- check sessions

    if sessions and sessions.lower() == 'none':
        sessions = None

    if sfilter and sfilter.lower() == 'none':
        sfilter = None

    report = report.lower() == 'yes'

    # --- check sfile

    sfiles = [e.strip() for e in re.split(' *, *| *\| *| +', sfile)]

    # --- check sessions

    if sessions is None:
        print "---> WARNING: No sessions specified. The list will be generated for all sessions in the subjects folder!"
        sessions = glob.glob(os.path.join(subjectsfolder, '*', 'behavior'))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.getSubjectList(sessions, sfilter=sfilter, verbose=False, subjectsfolder=subjectsfolder)

    if not sessions:
        raise ge.CommandFailed("gatherBehavior", "No session found" , "No sessions found to process behavioral data from!", "Please check your data!")

    # --- generate list entries

    processReport = {'ok': [], 'missing': [], 'error': []}
    data = {}
    keys = []

    for session in sessions:

        files = []
        for sfile in sfiles:
            files += glob.glob(os.path.join(subjectsfolder, session['id'], 'behavior', sfile))

        if not files:
            processReport['missing'].append(session['id'])
            continue

        sdata = {}
        for file in files:
            error = addData(file, sdata, keys)
            if error:
                processReport['error'].append((session['id'], error))
                break

        if error:
            continue

        processReport['ok'].append(session['id'])
        data[session['id']] = dict(sdata)


    # --- save group data

    try:
        fout = open(tfile, 'w')
    except:
        raise ge.CommandFailed("gatherBehavior", "Could not create target file", "Target file could not be created at the specified location [%s]" % (tfile), "Please check your paths and authorizations!")        

    header = ['session id'] + keys
    if report:
        print >> fout, "# Data compiled using gatherBehavior on %s" % (datetime.datetime.today())
    print >> fout, "\t".join(header)

    for sessionid in processReport['ok']:
        sdata = data[sessionid]
        line  = [sessionid]
        for key in keys:
            if key in sdata:
                line.append(sdata[key])
            else:
                line.append('NA')
        print >> fout, "\t".join(line)

    # --- print report

    reportit = [('ok', 'Successfully processed sessions:'), ('missing', 'Sessions for which no behavioral data was found'), ('error', 'Sessions for which an error was encountered')]

    if any([processReport[status] for status, message in reportit]):
        print "===> Final report"
        for status, message in reportit:
            if processReport[status]:
                print '--->', message
                if report and status != 'ok':
                    print >> fout, '#', message
                for info in processReport[status]:
                    if status == 'error':
                        print '     %s [%s]' % info
                        if report:
                            print >> fout, '# -> %s: %s' % info
                    else:
                        print '     %s' % (info)
                        if report and status != 'ok':
                            print >> fout, '# -> %s' % (info)

    fout.close()

    # --- exit

    if processReport['error'] or processReport['missing']:
        if check.lower() == 'yes':
            raise ge.CommandFailed("gatherBehavior", "Errors encountered", "Not all sessions processed successfully!", "Sessions with missing behavioral data: %d" % (len(processReport['missing'])), "Sessions with errors in processing: %d" % (len(processReport['error'])), "Please check your data!")        
        elif check.lower() == 'warn':
            raise ge.CommandNull("gatherBehavior", "Errors encountered", "Not all sessions processed successfully!", "Sessions with missing behavioral data: %d" % (len(processReport['missing'])), "Sessions with errors in processing: %d" % (len(processReport['error'])), "Please check your data!")        

    if not processReport['ok']:
        raise ge.CommandNull("gatherBehavior", "No files processed", "No valid data was found!")                




def pullSequenceNames(subjectsfolder=".", sessions=None, sfilter=None, sfile="subject.txt", tfile=None, overwrite="no", check="yes", report="yes"):
    """
    pullSequenceNames [subjectsfolder="."] [sessions=None] [sfilter=None] [sfile="subject.txt"] [tfile="<subjectsfolder>/inbox/MR/sequences.txt"] [overwrite="no"] [check="yes"]

    The function gathers a list of all the sequence names across the sessions 
    and saves it into a specified file.

    Parameters
    ----------

    --subjectsfolder  The base study subjects folder (e.g. WM44/subjects) where
                      the inbox and individual subject folders are. If not 
                      specified, the current working folder will be taken as 
                      the location of the subjectsfolder. [.]
    
    --sessions        Either a string with pipe `|` or comma separated list of 
                      sessions (sessions ids) to be processed (use of grep 
                      patterns is possible), e.g. "AP128,OP139,ER*", or a path
                      to a batch.txt or *list file with a list of session ids.
                      [*]

    --sfilter         Optional parameter used to filter sessions to include. It
                      is specifed as a string in format:
    
                      "<key>:<value>|<key>:<value>"

                      Only the sessions for which all the specified keys match
                      the specified values will be included in the list.

    --sfile           A file or comma or pipe `|` separated list of files or
                      grep patterns that define, which session description 
                      files to check. ['subject.txt']

    --tfile           The path to the target file, a file that will contain
                      the list of all the session names from all the individual
                      session information files.
                      ['<subjectsfolder>/inbox/MR/sequences.txt']

    --overwrite       Whether to overwrite an existing file or not. ['no']

    --check           Check whether all the identified sessions have the 
                      specifed information files. The possible options:
                      are:

                      * yes   ... Check and report an error if no information
                                  exists for a session
                      * warn  ... Warn and list the sessions for which the 
                                  neuroimaging information was not found
                      * no    ... Do not run a check, ignore sessions for which
                                  no imaging data was found

    --report          Whether to include date when file was generated and the 
                      final report in the compiled file ('yes') or not ('no'). 
                      ['yes']

    Use
    ---
    
    The command will use the `subjectfolder`, `sessions` and `sfilter` 
    parameters to create a list of sessions to process. For each session, the
    command will use the `sfile` parameter to identify neuroimaging information 
    files from which to genrate the list from. If no file is found for a session 
    and the `check` parameter is set to `yes`, the command will exit with an 
    error.

    Once the files for each session are identified, the command will inspect the
    files for imaging data and create a list of sequence names across all 
    sessions. The list will be saved to a file specified using `tfile` 
    parameter. If no path is specified, the default location will be used:

    <subjectsfolder>/inbox/MR/sequences.txt

    If a target file exists, it will be deleted and replaced, if the `overwrite`
    parameter is set to 'yes'. If the overwrite parameter is set to 'no', the 
    command will exit with an error.

    
    File formats
    ------------

    The command expects the neuroimaging data to be present in the standard 
    'subject.txt' files. Please se online documentation for details. 
    Specifically, it will extract the first information following the sequence
    name.

    The resulting file will be a simple text file, with one sequence name per
    line. In addition, if `report` is set to 'yes' (the default), the resulting 
    file  will start with a comment line stating the date of creation, and at 
    the end additional comment lines will list the full report of missing files 
    and errors encounterdd while gathering behavioral data from individual 
    sessions.


    Examples
    --------
    
    ```
    qunex pullSequenceNames sessions="AP*"
    ```

    The command will compile sequence names present in `subject.txt` files 
    present in all `<session id>` folders that match the "AP*" glob
    pattern in the current working directory. 

    The resulting file will be save in the default location:

    <current folder>/inbox/MR/sequences.txt

    If any of the identified sessions do not include data or if errors are 
    encountered when processing the data, the command will exit with an error.

    ```
    qunex pullSequenceNames subjectsfolder="/data/myStudy/subjects" \\
            sessions="AP*|OP*" sfile="subject.txt|session.txt" \\
            check="warn" overwrite="yes" report="no"
    ```

    The command will find all the session folders within `/data/myStudy/subjects`
    It will then look for presence of either subject.xtx or session.txt files.
    The compiled data from the found files will be saved in the default 
    location. If a file already exists, it will be overwritten. If any errors 
    are encountered, the command will not throw an error, however it also won't
    report a successful completion of the task. The resulting file will not have 
    information on file generation or processing report.
    
    ```
    qunex pullSequenceNames subjectsfolder="/data/myStudy/subjects" \\
            sessions="/data/myStudy/processing/batch.txt" \\           
            sfilter="group:controls|behavioral:yes" \\
            sfile="*.txt" \\
            tfile="/data/myStudy/subjects/specs/hcp_mapping.txt" \\
            check="no" overwrite="yes"
    ```

    The command will read the session information from the provided batch.txt 
    file. It will then process only those sessions that have the following
    lines in their description:

    group: control
    behavioral: yes

    For those sessions it will find any files that end with `.txt` and process
    them for presence of neuroimaging information. The compiled data will be 
    saved to the specified target file. If the target file exists, it will be 
    overwritten. The command will print a full report of the processing, 
    however, it will exit with reported success even if missing files or errors 
    were encountered.

    ----------------
    Written by Grega Repovš 2019-05-12
    
    """

    # --- Support function

    def addData(file, data):

        missingNames  = []
        sequenceNames = []

        try:
            f = open(file, 'r')
        except:
            return "Could not open %s for reading!" % (file)

        for line in f:
            line = line.decode('utf-8')
            if ':' in line:
                line = [e.strip() for e in line.split(':')]
                if line[0].isnumeric():
                    if len(line) > 1:
                        sequenceNames.append(line[1])
                    else:
                        misssingNames.append(line[0])
        f.close()

        if not sequenceNames:
            return "No sequence information found in file [%s]!" % (file)

        data += sequenceNames

        if missingNames:
            return "The following sequences had no names: %s!" % (", ".join(missingNames))

    # --- Start it up

    print "Running pullSequenceNames\n========================="

    # --- check subjects folder

    subjectsfolder = os.path.abspath(subjectsfolder)

    if not os.path.exists(subjectsfolder):
        raise ge.CommandFailed("pullSequenceNames", "Subjects folder does not exist", "The specified subjects folder does not exist [%s]" % (subjectsfolder), "Please check paths!")

    # --- check target file

    if tfile is None:
        tfile = os.path.join(subjectsfolder, 'inbox', 'MR', 'sequences.txt')

    overwrite = overwrite.lower() == 'yes'

    if os.path.exists(tfile):
        if overwrite:
            try:
                os.remove(tfile)
            except:
                raise ge.CommandFailed("pullSequenceNames", "Could not remove target file", "Existing object at the specified target location could not be deleted [%s]" % (tfile), "Please check your paths and authorizations!")        
        else:
            raise ge.CommandFailed("pullSequenceNames", "Target file exists", "The specified target file already exists [%s]" % (tfile), "Please check your paths or set overwrite to 'yes'!")        

    # --- check sessions

    if sessions and sessions.lower() == 'none':
        sessions = None

    if sfilter and sfilter.lower() == 'none':
        sfilter = None

    report = report.lower() == 'yes'

    # --- check sfile

    sfiles = [e.strip() for e in re.split(' *, *| *\| *| +', sfile)]

    # --- check sessions

    if sessions is None:
        print "---> WARNING: No sessions specified. The list will be generated for all sessions in the subjects folder!"
        sessions = glob.glob(os.path.join(subjectsfolder, '*', 'behavior'))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.getSubjectList(sessions, sfilter=sfilter, verbose=False, subjectsfolder=subjectsfolder)

    if not sessions:
        raise ge.CommandFailed("pullSequenceNames", "No session found" , "No sessions found to process neuroimaging data from!", "Please check your data!")

    # --- generate list entries

    processReport = {'ok': [], 'missing': [], 'error': []}
    data = []

    for session in sessions:

        files = []
        for sfile in sfiles:
            files += glob.glob(os.path.join(subjectsfolder, session['id'], sfile))

        if not files:
            processReport['missing'].append(session['id'])
            continue

        for file in files:
            error = addData(file, data)
            if error:
                processReport['error'].append((session['id'], error))
                break

        if error:
            continue

        processReport['ok'].append(session['id'])


    # --- save group data

    try:
        fout = open(tfile, 'w')
    except:
        raise ge.CommandFailed("pullSequenceNames", "Could not create target file", "Target file could not be created at the specified location [%s]" % (tfile), "Please check your paths and authorizations!")        

    if report:
        print >> fout, "# Data compiled using pullSequenceNames on %s" % (datetime.datetime.today())

    data = sorted(set(data))
    for sname in data:
        print >> fout, sname

    # --- print report

    reportit = [('ok', 'Successfully processed sessions:'), ('missing', 'Sessions for which no imaging data was found'), ('error', 'Sessions for which an error was encountered')]

    if any([processReport[status] for status, message in reportit]):
        print "===> Final report"
        for status, message in reportit:
            if processReport[status]:
                print '--->', message
                if report and status != 'ok':
                    print >> fout, '#', message
                for info in processReport[status]:
                    if status == 'error':
                        print '     %s [%s]' % info
                        if report:
                            print >> fout, '# -> %s: %s' % info
                    else:
                        print '     %s' % (info)
                        if report and status != 'ok':
                            print >> fout, '# -> %s' % (info)

    fout.close()

    # --- exit

    if processReport['error'] or processReport['missing']:
        if check.lower() == 'yes':
            raise ge.CommandFailed("pullSequenceNames", "Errors encountered", "Not all sessions processed successfully!", "Sessions with missing imaging data: %d" % (len(processReport['missing'])), "Sessions with errors in processing: %d" % (len(processReport['error'])), "Please check your data!")        
        elif check.lower() == 'warn':
            raise ge.CommandNull("pullSequenceNames", "Errors encountered", "Not all sessions processed successfully!", "Sessions with missing imaging data: %d" % (len(processReport['missing'])), "Sessions with errors in processing: %d" % (len(processReport['error'])), "Please check your data!")        

    if not processReport['ok']:
        raise ge.CommandNull("pullSequenceNames", "No files processed", "No valid data was found!")                


def mapIO(subjectsfolder=".", sessions=None, sfilter=None, subjid=None, maptype=None, mapaction="link", mapto=None, mapfrom=None, overwrite="no", mapexclude=None, verbose="no"):

    """
    mapIO [subjectsfolder="."] [sessions=None] [maptype=<desired mapping>] [sfilter=None] [subjid=None] [mapaction=<how to map>] [mapto=None|<location to map to>] [mapfrom=None|<location to map from>] [overwrite="no"] [mapexclude=None] [verbose="no"]

    The function maps data in or out of Qu|Nex data structure. What specific 
    mapping to conduct is specified by the `maptype` parameter. How to do the 
    mapping (move, copy, link) is specified by the `mapaction` parameter. The
    `overwrite` parameter specifies whether to replace any existing data at the
    target location if it already exist.

    If the function is to map out from the Qu|Nex data structure, then the target
    location has to be provided by the `mapto` parameter. If the function is to 
    map into the Qu|Nex data structure, then the source location has to be 
    provided by the `mapfrom` parameter.

    The function first prepares the mapping. Next it checks that the mapping can
    be conducted as specified by the parameters given. If the check identifies 
    any potential issues, no mapping is conducted to avoid an incomplete mapping. 
    Do note that the check only investigates the presence of source and target 
    files, it does not check, whether the user has permission on the filesystem 
    to execute the actions.


    Parameters
    ----------

    --subjectsfolder  Specifies the base study subjects folder within the Qu|Nex
                      folder structure to or from which the data are to be 
                      mapped. If not specified explicitly, the current working 
                      folder will be taken as the location of the subjectsfolder. 
                      [.]
    
    --sessions        Either a string with pipe `|` or comma separated list of 
                      sessions (sessions ids) to be mapped (use of grep patterns
                      is possible), e.g. "AP128,OP139,ER*". When mapping out of 
                      Qu|Nex it is best (or even required) to provide a path to 
                      a batch.txt file with information on the sessions. [*]

    --sfilter         And optional parameter used in combination with a 
                      batch.txt file used to filter sessions to include in the 
                      mapping. It is specified as a string in format:
    
                      "<key>:<value>|<key>:<value>"

                      The keys and values refer to information provided by the
                      batch.txt file referenced in the `sessions` parameter. 
                      Only the sessions for which all the specified keys match
                      the specified values will be mapped.
    
    --subjid          An optional parameter explicitly specifying, which of the 
                      sessions identified by the `sessions` parameter are to be 
                      mapped. If not specified, all sessions will be mapped.
 
    --maptype         The specific mapping type to be performed (see the section on
                      implemented mappings).

    --mapaction       How to map the data. The following actions are supported:
                      * 'copy'  ... the data is copied from source to target
                      * 'link'  ... if possible, hard links are created for the 
                                    files, if not, the data is copied
                      * 'move'  ... the data is moved from source to target 
                                    location
                      ['link']

    --mapfrom         The source of the mapping when mapping into Qu|Nex. 
                      This flag is optional and has to be specified when mapping 
                      into the Qu|Nex folder structure from an external location.

    --mapto           The external target of the mapping when starting with the 
                      Qu|Nex. This flag is optional and only has to be specified 
                      when mapping out of the Qu|Nex folder structure.

    --overwrite       Whether existing files at the target location should be
                      overwritten. Possible options are:
                      * yes  ... any existing files should be replaced
                      * no   ... no existing files should be replaced and the
                                 mapping should be aborted if any are found
                      * skip ... skip files that already exist, process others

    --mapexclude      A comma separated list of regular expression patterns that
                      specify, which files should be excluded from mapping. The
                      regular expression patterns are matched against the full
                      path of the source files.

    --verbose         Report details while running function



    Implemented mapping types
    -------------------------

    The following mappings are implemented, as they can be specified by the
    `maptype` parameter:

    * 'toHCPLS'         This mapping supports the the data preprocessed using
                        the HCP Pipelines following the Life Span (LS) 
                        convention. The processed derivatives from the HCP 
                        pipelines are mapped into the specified target location
                        on the file system to comply with the HCPLS output 
                        expectations. The mapping expects that HCPLS folder 
                        structure was used for the processing. The function will
                        map all the content of the session's hcp directory 
                        to a corresponding session directory in the indicated 
                        target location. If any part of the unprocessed data 
                        or the results are not to be mapped, they can be 
                        specified using the `mapexclude` parameter.


    Examples
    --------
    
    toHCPLS mapping
    
    We will assume the following:
    
    * data to be mapped is located in the folder `/data/studies/myStudy/subjects`
    * a batch file exists in the location `/data/studies/myStudy/processing/batch.txt`
    * we would like to map the data to location `/data/outbox/hcp_formatted/myStudy`
    
    given the above assumptions the following example commands can be run:
    
    ```
    qunex mapIO \\
        --subjectsfolder=/data/studies/myStudy/subjects \\
        --sessions=/data/studies/myStudy/processing/batch.txt \\
        --mapto=/data/outbox/hcp_formatted/myStudy \\
        --maptype=toHCPLS \\
        --mapexclude=unprocessed \\
        --mapaction=link \\
        --overwrite=skip
    ```

    Using the above commands the data found in the 
    `/data/studies/myStudy/subjects/<session id>/hcp/<session id>` folders, 
    excluding the `unprocessed` folder would be mapped to the 
    `/data/outbox/hcp_formatted/myStudy/<session id>` folder for all the 
    sessions listed in the batch.txt file. Specifically, folders would be 
    recreated as needed and hard-links would be created for all the files to be 
    mapped. If any target files already exist, they would be skipped, but 
    the processing of other files would take place anyway.
    
    ``` 
    qunex mapIO \\
        --subjectsfolder=/data/studies/myStudy/subjects \\
        --sessions=/data/studies/myStudy/processing/batch.txt \\
        --mapto=/data/outbox/hcp_formatted/myStudy \\
        --sfilter="group:controls|institution:Yale" \\
        --maptype="toHCPLS" \\
        --mapaction="copy" \\
        --overwrite=no
    ```

    Using the above commands, only data from the sessions that are marked in the
    batch.txt file to be from the control group and acquired at Yale would be 
    mapped. In this case, the files would be copied and if any files would 
    already exist in the target location, the mapping would be aborted 
    altogether.
    
    ```
    qunex mapIO \\
        --subjectsfolder=/data/studies/myStudy/subjects \\
        --sessions=/data/studies/myStudy/processing/batch.txt \\
        --mapto=/data/outbox/hcp_formatted/myStudy \\
        --subjid="AP*,HQ*" \\
        --maptype="toHCPLS" \\
        --mapaction="move" \\
        --overwrite=yes
    ```

    Using the above commands, only the sessions that start with either "AP" or 
    "HQ" would be mapped, the files would be moved and any existing files at the 
    target location would be overwritten.
    
    ```
    qunex mapIO \\
        --subjectsfolder=/data/studies/myStudy/subjects \\
        --sessions=/data/studies/myStudy/processing/batch.txt \\
        --mapto=/data/outbox/hcp_formatted/myStudy \\
        --maptype="toHCPLS" \\
        --mapaction="link" \\
        --mapexclude="unprocessed,MotionMatrices,MotionCorrection" \\
        --overwrite=skip
    ```
    
    Using the above commands, all the sessions specified in the batch.txt would 
    be processed, files would be linked, files that already exist would be 
    skipped, and any files for which the path include 'unprocessed', '
    MotionMatrices' or 'MotionCorrection' would be excluded from the mapping.

    ----------------
    Written by Grega Repovš 2019-05-29

    Change log
    2019-05-30 Grega Repovš
             - Modified documentation
             - Excluding 'unprocessed' is now an explicit option

    """

    verbose   = verbose.lower() == 'yes'

    # -- check input

    if os.path.exists(subjectsfolder):
        subjectsfolder = os.path.abspath(subjectsfolder)
    else:
        raise ge.CommandFailed("mapIO", "Subjects folder does not exist", "The specified subjects folder does not exist [%s]" % (subjectsfolder), "Please check paths!")

    if not maptype :
        raise ge.CommandFailed("mapIO", "No mapping specified", "A mapping has to be specified to be executed!", "Please check your command call!")

    if maptype not in ['toHCPLS']:
        raise ge.CommandFailed("mapIO", "Mapping not supported", "The specified mapping is not supported [%s]" % (maptype), "Please check your command call!")

    if maptype in ['toHCPLS']:
        direction = 'out'
        if mapto:
            mapto = os.path.abspath(mapto)
        else:
            raise ge.CommandFailed("mapIO", "Target not specified", "To execute the specified mapping (%s), a target, `mapto` parameter has to be specified!" % (maptype), "Please check your command call!")
    else:
        direction = 'in'
        if mapfrom:
            mapfrom = os.path.abspath(mapfrom)
        else:
            raise ge.CommandFailed("mapIO", "Source not specified", "To execute the specified mapping (%s), a source, using `mapfrom` parameter has to be specified!" % (maptype), "Please check your command call!")

    if mapaction not in ['link', 'copy', 'move']:
        raise ge.CommandFailed("mapIO", "Invalid action", "The action specified for the mapping is not valid [%s]!" % (maptype), "Please specify a valid mapping!")

    # -- prepare sessions to work with

    if direction == 'out':
        sessions, gopts = gc.getSubjectList(sessions, sfilter=sfilter, subjid=subjid, subjectsfolder=subjectsfolder, verbose=False)
        if not sessions:
            raise ge.CommandFailed("mapIO", "No session found" , "No sessions found to map based on the provided criteria!", "Please check your data!")

    # -- prepare exclusion

    if mapexclude:
        patterns = [e.strip() for e in re.split(', *', mapexclude)]
        mapexclude = []
        for e in patterns:
            try:
                mapexclude.append(re.compile(e))
            except:
                raise ge.CommandFailed("mapIO", "Invalid exclusion" , "Could not parse the exclusion regular expression: '%s'!" % (e), "Please check mapexclude parameter!")

    # -- open logfile

    logfilename, logfile = gc.getLogFile(folders={'subjectsfolder': subjectsfolder}, tags=['mapIO', maptype])
    
    gc.printAndLog(gc.underscore("Running mapIO: %s" % (maptype)), file=logfile)
    
    # -- prepare mapping

    gc.printAndLog("--> preparing mapping", file=logfile)

    if maptype == 'toHCPLS':
        toMap = map_toHCPLS(subjectsfolder, sessions, mapto, gopts)

    if not toMap:
        gc.printAndLog("ERROR: Found nothing to map!", file=logfile, silent=True)
        endlog = gc.closeLogFile(logfile, logfilename, status="error")
        raise ge.CommandFailed("mapIO", "Nothing to map" , "No files were found to map!", "Please check your data!")

    # -- check mapping

    missing   = []
    existing  = []
    failed    = []
    process   = []
    toexclude = []

    for sfile, tfile in toMap:
        if not os.path.exists(sfile):
            missing.append((sfile, tifile))
        elif os.path.isfile(tfile):
            existing.append((sfile, tfile))
        else:
            if mapexclude:
                if any([e.search(sfile) is not None for e in mapexclude]):
                    toexclude.append((sfile, tfile))
                    continue
            process.append((sfile, tfile))

    if missing:
        gc.printAndLog("==> ERROR: A number of source files are missing", file=logfile, silent=not verbose)
        for sfile, tfile in missing:
            gc.printAndLog("           --> " + sfile, file=logfile)
        gc.printAndLog("\nMapping Aborted!", file=logfile)
        endlog = gc.closeLogFile(logfile, logfilename, status="error")
        raise ge.CommandFailed("mapIO", "Source files missing" , "Mapping could not be run as some source files were missing!", "Please check your data and log [%s!" % (endlog))
    
    if existing:
        s = 'Some files already exist'
        if overwrite.lower() == 'yes':
            s = "==> WARNING: " + s + " and will be overwritten"
            pre = "             "
            process += existing
        if overwrite.lower() == 'skip':
            s = "==> WARNING: " + s + " and will be skipped"
            pre = "             "
        else:
            s = "==> ERROR: " + s 
            pre = "           "
        gc.printAndLog(s, file=logfile)

        for sfile, tfile in existing:
            gc.printAndLog(pre + "--> " + sfile, file=logfile, silent=not verbose)

        if overwrite.lower() == 'no':
            gc.printAndLog("==> Mapping Aborted!", file=logfile)
            endlog = gc.closeLogFile(logfile, logfilename, status="error")
            raise ge.CommandFailed("mapIO", "Target files exist" , "Mapping could not be run as some target file already exist!", "Please check your data and log [%s]!" % (endlog))

    if toexclude:
        gc.printAndLog("==> WARNING: Some files will be excluded from mapping", file=logfile)

        for sfile, tfile in toexclude:
            gc.printAndLog("             --> " + sfile, file=logfile, silent=not verbose)

    if not process:
        gc.printAndLog("==> Nothing left to map!", file=logfile, silent=True)
        endlog = gc.closeLogFile(logfile, logfilename, status="done")
        raise ge.CommandNull("mapIO", "Nothing left to map" , "After skipping and exclusion, no files were left to map!", "Please check your data!")

    # -- execute mapping

    # -> clean destination

    if overwrite.lower() == 'yes':
        for tfile in existing:
            os.remove(tfile)

    # -> map

    mapactions      = {'copy': shutil.copy2, 'move': shutil.move, 'link': gc.linkOrCopy}
    descriptions = {'copy': 'copying', 'move': 'moving', 'link': 'linking'}
    
    do   = mapactions[mapaction]
    desc = descriptions[mapaction]

    gc.printAndLog("--> Mapping files", file=logfile)

    failed = []

    for sfile, tfile in process:

        tfolder, tname = os.path.split(tfile)
        if not os.path.exists(tfolder):
            try:
                os.makedirs(tfolder)
            except:
                failed.append((sfile, tfile))
                continue
            gc.printAndLog("    --> creating folder: %s" % (tfolder), file=logfile, silent=not verbose)

        try:
            do(sfile, tfile)
        except:
            raise
            failed.append((sfile, tfile))
            continue
        gc.printAndLog("    --> %s: %s --> %s" % (desc, sfile, tfile), file=logfile, silent=not verbose)

    # -- check success
    
    if failed:
        gc.printAndLog("\n" + gc.underscore("ERROR: The following files could not be mapped"), file=logfile)
        for sfile, tfile in failed:
            gc.printAndLog("--> %s --> %s" % (sfile, tfile), file=logfile)

        endlog = gc.closeLogFile(logfile, logfilename, status="error")
        raise ge.CommandFailed("mapIO", "Some files not mapped" , "Some files could not be mapped!", "Please see log and check your data [%s]!" % (endlog))

    gc.printAndLog("--> Mapping completed", file=logfile)
    endlog = gc.closeLogFile(logfile, logfilename, status="done")



def map_toHCPLS(subjectsfolder, sessions, target, options):
    '''
    Computes mapping from Qu|Nex to HCPLS folders.
    '''
    toMap = []

    for session in sessions:
        hcpfolder = os.path.join(subjectsfolder, session['id'], 'hcp', session['id'])
        hcpfolders = glob.glob(os.path.join(hcpfolder, '*')) 
        targetfolder = os.path.join(target, session['id'])

        for datafolder in hcpfolders:
            for dirpath, dirnames, filenames in os.walk(datafolder):
                for filename in filenames:
                        toMap.append((os.path.join(datafolder, dirpath, filename), os.path.join(targetfolder, os.path.relpath(dirpath, hcpfolder), filename)))

    return toMap



