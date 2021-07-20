#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``utilities.py``

Miscellaneous utilities for file processing.
"""

"""
Created by Grega Repovs on 2017-09-17.
Copyright (c) Grega Repovs and Jure Demsar. All rights reserved.
"""

import os.path
import os
import errno
import shutil
import glob
import getpass
import re
import subprocess
from datetime import datetime

import general.commands_support as gcs
import general.process as gp
import general.core as gc
import processing.core as gpc
import general.exceptions as ge
import general.filelock as fl

parameterTemplateHeader = '''#  Batch parameters file
#  =====================
#
#  This file is used to specify the default parameters used by various QuNex commands for
#  HCP minimal preprocessing pipeline, additional bold preprocessing commands,
#  and other analytic functions. The content of this file should be prepended to the list
#  that contains all the sessions that is passed to the commands. It can added manually or
#  automatically when making use of the compileLists QuNex command.
#
#  This template file should be edited to include the parameters relevant for
#  a given study/analysis and provide the appropriate values. For detailed description of
#  parameters and their valid values, please consult the QuNex documentation
*  (e.g. Running HCP minimal preprocessing pipelines, Additional BOLD
#  preprocessing) and online help for the relevant QuNex commands.
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



def manage_study(studyfolder=None, action="create", folders=None, verbose=False):
    """
    manage_study studyfolder=None action="create"

    A helper function called by create_study and checkStudy that does the
    actual checking of the study folder and generating missing content.
    
    PARAMETERS
    ==========

    --studyfolder  the location of the study folder
    --action       whether to create a new study folder (create) or check an
                   existing study folder (check)
    --folders      Path to the file which defines the study folder structure.
                   [$TOOLS/python/qx_utilities/templates/study_folders_default.txt]
    """

    # template folder
    niuTemplateFolder = os.environ["NIUTemplateFolder"]

    # default folders file
    if folders is None:
        folders = os.path.join(niuTemplateFolder, "study_folders_default.txt")
    else:
        # if not absolute path
        if not os.path.exists(folders):
            # check if in templates
            folders = os.path.join(niuTemplateFolder, folders)
            if not os.path.exists(folders):
                # fail
                raise ge.CommandFailed("manage_study", "Folder structure file [%s] not found!" % folders, "Please check the value of the folders parameter.")

    # action
    create = action == "create"

    # create folders structure from file
    folders = create_study_folders(folders)

    if create:
        if verbose:
            print("\nCreating study folder structure:")

    for folder in folders:
        tfolder = os.path.join(*[studyfolder] + folder)

        if create:
            try:
                os.makedirs(tfolder)
                if verbose:
                    print(" ... created:", tfolder)
            except OSError as e:
                if e.errno == errno.EEXIST:
                    if verbose:
                        print(" ... folder exists:", tfolder)
                else:
                    errstr = os.strerror(e.errno)
                    raise ge.CommandFailed("manage_study", "I/O error: %s" % (errstr), "Folder could not be created due to '%s' error!" % (errstr), "Folder to create: %s" % (tfolder), "Please check paths and permissions!")

        else:
            if os.path.exists(tfolder):
                if verbose:
                    print(" ... folder exists:", tfolder)
            else:  
                if verbose:
                    print(" ... folder does not exist:", tfolder)

    if create:
        if verbose:
            print("\nPreparing template files:")

        # --> parameter template
        paramFile = os.path.join(studyfolder, 'sessions', 'specs', 'batch_example.txt')
        try:
            f = os.open(paramFile, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
            os.write(f, "#  Generated by QuNex %s on %s\n" % (gc.get_qunex_version(), datetime.now().strftime("%Y-%m-%d_%H.%M.%s")))
            os.write(f, "#\n")
            os.write(f, parameterTemplateHeader + "\n")
            for line in gp.arglist:
                if len(line) == 4:
                    os.write(f, "# _%-24s : %-15s # ... %s\n" % (line[0], line[1], line[3]))
                elif len(line) > 0:
                    os.write(f, "#\n# " + line[0] + '\n#\n')
            os.close(f)
            if verbose:
                print(" ... created batch_example.txt file")

        except OSError as e:
            if e.errno == errno.EEXIST:
                if verbose:
                    print(" ... batch_example.txt file already exists")
            else:
                errstr = os.strerror(e.errno)
                raise ge.CommandFailed("manage_study", "I/O error: %s" % (errstr), "Batch parameter template file could not be created [%s]!" % (paramFile), "Please check paths and permissions!")

        # --> mapping example
        # get all files that match the pattern
        examplesFolder = os.path.join(niuTemplateFolder, 'templates')
        mappingExamples = glob.glob(examplesFolder + "/*_mapping_example.txt")
        for srcFile in mappingExamples:
            try:
                # extract filename only
                fileName = os.path.basename(srcFile)
                # destination path and file
                mapFile = os.path.join(studyfolder, fileName)
                dstFile = os.open(mapFile, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
                # read src
                srcContent = open(srcFile, 'r').read()
                os.write(dstFile, srcContent)
                os.close(dstFile)
                if verbose:
                    print(" ... created %s file" % dstFile)

            except OSError as e:
                if e.errno == errno.EEXIST:
                    if verbose:
                        print(" ... %s file already exists" % dstFile)
                else:
                    errstr = os.strerror(e.errno)
                    raise ge.CommandFailed("manage_study", "I/O error: %s" % (errstr), "Batch parameter template file could not be created [%s]!" % (paramFile), "Please check paths and permissions!")

        # --> markFile
        markFile = os.path.join(studyfolder, '.qunexstudy')

        # ... map .mnapstudy to qunexstudy
        if os.path.exists(os.path.join(studyfolder, '.mnapstudy')):
            try:
                f = os.open(markFile, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
                markcontent = open(os.path.join(studyfolder, '.mnapstudy'), 'r').read()
                os.write(f, markcontent)
                os.close(f)
                if verbose:
                    print(" ... converted .mnapstudy file to .qunexstudy")
            except OSError as e:
                if e.errno == errno.EEXIST:
                    if verbose:
                        print(" ... .qunexstudy file already exists")
                else:
                    errstr = os.strerror(e.errno)
                    raise ge.CommandFailed("manage_study", "I/O error: %s" % (errstr), ".qunexstudy file could not be created [%s]!" % (markFile), "Please check paths and permissions!")

            try:                
                shutil.copystat(os.path.join(studyfolder, '.mnapstudy'), markFile)
                os.unlink(os.path.join(studyfolder, '.mnapstudy'))
            except:
                pass

        try:
            username = getpass.getuser()
        except:
            username = "unknown user"

        try:
            f = os.open(markFile, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
            os.write(f, "%s study folder created on %s by %s." % (os.path.basename(studyfolder), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username))
            os.close(f)
            if verbose:
                print(" ... created .qunexstudy file")
        
        except OSError as e:
            if e.errno == errno.EEXIST:
                if verbose:
                    print(" ... .qunexstudy file already exists")
            else:
                errstr = os.strerror(e.errno)
                raise ge.CommandFailed("manage_study", "I/O error: %s" % (errstr), ".qunexstudy file could not be created [%s]!" % (markFile), "Please check paths and permissions!")


def create_study_folders(folders_spec):
    """
    create_study_folders folders=None

    A helper function called by manage_study for creating study folder structure
    from a .txt file with structure specification.
    
    PARAMETERS
    ==========

    --folders     Path to the file which defines the study folder structure.
                  [$TOOLS/python/qx_utilities/templates/study_folders_default.txt]
    """

    # variable for storing the structure
    folder_structure = []

    with open(folders_spec) as f:
        # track current structure
        current_structure = []
        current_indents = []

        for line in f:
            # ignore empty lines
            folder = line.strip()
            if folder != "":
                # get indent
                indent = len(line) - len(line.lstrip())

                # if indent is 0 we have a new root folder
                if indent == 0:
                    current_structure = [folder]
                    current_indents = [0]

                # if indent is not 0 find the location in structure
                else:
                    i = 0
                    while indent > current_indents[i]:
                        i = i+1
                        if i == len(current_indents):
                            break

                    # remove at the end of the list
                    current_structure = current_structure[0:i]
                    current_indents = current_indents[0:i]

                    # add new info
                    current_structure.append(folder)
                    current_indents.append(indent)

                # append to folders
                folder_structure.append(current_structure)
    
    return folder_structure


def create_study(studyfolder=None, folders=None):
    """
    ``create_study studyfolder=<path to study base folder> [folders=$TOOLS/python/python/qx_utilities/templates/study_folders_default.txt]``

    Creates the base study folder structure.

    INPUTS
    ======

    --studyfolder      The path to the study folder to be generated.
    --folders          Path to the file which defines the subfolder structure.
                       [$TOOLS/python/python/qx_utilities/templates/study_folders_default.txt]

    USE
    ===

    Creates the base folder at the provided path location and the study folders. 
    By default $TOOLS/python/python/qx_utilities/templates/study_folders_default.txt
    will be used for subfolder specification. The default structure is::

        <studyfolder>
        ├── analysis
        │   └── scripts
        ├── processing
        │   ├── logs
        │   │   ├── batchlogs
        │   │   ├── comlogs
        │   │   ├── runchecks
        │   │   └── runlogs
        │   ├── lists
        │   ├── scripts
        │   └── scenes
        │       └── QC
        │           ├── T1w
        │           ├── T2w
        │           ├── myelin
        │           ├── BOLD
        │           └── DWI
        ├── info
        │   ├── demographics
        │   ├── tasks
        │   ├── stimuli
        │   ├── bids
        │   └── hcpls
        └── sessions
            ├── inbox
            │   ├── MR
            │   ├── EEG
            │   ├── BIDS
            │   ├── HCPLS
            │   ├── behavior
            │   ├── concs
            │   └── events
            ├── archive
            │   ├── MR
            │   ├── EEG
            │   ├── BIDS
            │   ├── HCPLS
            │   └── behavior
            ├── specs
            └── QC

    Do note that the command will create all the missing folders in which the
    specified study is to reside. The command also prepares template
    batch_example.txt and pipeline example mapping files in
    <studyfolder>/sessions/specs folder. Finally, it creates a .qunexstudy file in
    the <studyfolder> to identify it as a study basefolder.

    EXAMPLE USE
    ===========

    ::

        qunex create_study studyfolder=/Volumes/data/studies/WM.v4
    """

    print("Running create_study\n===================")

    if studyfolder is None:
        raise ge.CommandError("create_study", "No studyfolder specified", "Please provide path for the new study folder using studyfolder parameter!")

    manage_study(studyfolder=studyfolder, action="create", folders=folders, verbose=True)


def checkStudy(startfolder=".", folders=None):
    """
    ``checkStudy startfolder="." [folders=$TOOLS/python/qx_utilities/templates/study_folders_default.txt]``

    The function looks for the path to the study folder in the hierarchy 
    starting from the provided startfolder. If found it checks that all the
    standard folders are present and creates any missing ones. It returns
    the path to the study folder. If the study folder can not be identified, 
    it returns None.

    ---
    Written by Grega Repovš, 2018-11-14
    """

    studyfolder = None
    testfolder  = os.path.abspath(startfolder)

    while os.path.dirname(testfolder) and os.path.dirname(testfolder) != '/':
        if os.path.exists(os.path.join(testfolder, '.qunexstudy')) or os.path.exists(os.path.join(testfolder, '.mnapstudy')):
            studyfolder = testfolder
            break
        testfolder = os.path.dirname(testfolder)

    if studyfolder:
        manage_study(studyfolder=studyfolder, action="check", folders=folders)

    return studyfolder  


def create_batch(sessionsfolder=".", sourcefiles=None, targetfile=None, sessions=None, filter=None, overwrite="no", paramfile=None):
    """
    ``create_batch [sessionsfolder=.] [sourcefiles=session_hcp.txt] [targetfile=processing/batch.txt] [sessions=None] [filter=None] [overwrite=no] [paramfile=<sessionsfolder>/specs/batch.txt]``
    
    Creates a joint batch file from source files in all session folders.

    INPUTS
    ======

    --sessionsfolder      The location of the <study>/sessions folder
    --sourcefiles         Comma separated names of source files to take from
                          each specified session folder and add to batch file.
                          [session_hcp.txt]
    --targetfile          The path to the batch file to be generated. By default
                          it is created as <study>/processing/batch.txt
    --sessions            If provided, only the specified sessions from the 
                          sessionsfolder will be processed. They are to be 
                          specified as a pipe or comma separated list, grob 
                          patterns are valid session specifiers.
    --filter              An optional parameter given as "key:value|key:value"
                          string. Only sessions with the specified key-value
                          pairs in their source files will be added to the
                          batch file.
    --overwrite           In case that the specified batch file already exists,
                          whether to interactively ask ('ask'), overwrite ('yes'),
                          abort action ('no') or append ('append') the found / 
                          specified sessions to the batch file.
    --paramfile           The path to the parameter file header to be used. If 
                          not explicitly provided it defaults to:
                          <sessionsfolder>/specs/batch.txt

    USE
    ===

    The command combines all the sourcefiles in all session folders in 
    sessionsfolder to generate a joint batch file and save it as targetfile.
    If only specific sessions are to be added or appended, "sessions" parameter
    can be used. This can be a pipe, comma or space separated list of session
    ids, another batch file or a list file. If a string is provided, grob
    patterns can be used (e.g. sessions="AP*|OR*") and all matching sessions
    will be processed.

    If no targetfile is specified, it will save the file as batch.txt in a
    processing folder parallel to the sessionsfolder. If the folder does not yet
    exist, it will create it.

    If targetfile already exists, depending on "overwrite" parameter it will:

    - ask (ask interactively, what to do)
    - yes (overwrite the existing file)
    - no (abort creating a file)
    - append (append sessions to the existing list file)

    Note that if If a batch file already exists then parameter file will not be 
    added to the header of the batch unless --overwrite is set to "yes". If 
    --overwrite is set to "append", then the parameters will not be changed, 
    however, any sessions that are not yet present in the batch file will be 
    appended at the end of the batch file.

    The command will also look for a parameter file. If it exists, it will
    prepend its content at the beginning of the batch.txt file. If no paramfile
    is specified and the default template does not exist, the command will print
    a warning and create an empty template (sessions/spec/batch.txt)
    with all the available parameters. Do note that this file will need to be
    edited with correct parameter values for your study.

    Alternatively, if you don't have a parameter file prepared, you can use or
    copy and modify one of the following templates:

    -legacy data template   
      ``qunex/python/qx_utilities/templates/batch_legacy_parameters.txt``
    -multiband data template
      ``qunex/python/qx_utilities/templates/batch_multiband_parameters.txt``

    EXAMPLE USE
    ===========
    
    ::

        qunex create_batch sourcefiles="session.txt" targetfile="fcMRI/sessions_fcMRI.txt"
    """

    print("Running create_batch\n===================")

    if sessions and sessions.lower() == 'none':
        sessions = None

    if filter and filter.lower() == 'none':
        filter = None

    sessionsfolder = os.path.abspath(sessionsfolder)

    # get sfiles from sourcefiles parameter
    if sourcefiles is None:
        sfiles = []
        sfiles.append("session_hcp.txt")
    else:
        sfiles = sourcefiles.split(",")

    # --- prepare target file name and folder
    if targetfile is None:
        targetfile = os.path.join(os.path.dirname(sessionsfolder), 'processing', 'batch.txt')

    if os.path.exists(targetfile):
        if overwrite == 'ask':
            print("WARNING: target file %s already exists!" % (os.path.abspath(targetfile)))
            s = input("         Do you want to overwrite it (o), cancel command (c), or append to the file (a)? [o/c/a]: ")
            if s == 'o':
                print("         Overwriting exisiting file.")
                overwrite = 'yes'
            elif s == 'a':
                print("         Appending to exisiting file.")
                overwrite = 'append'
            else:
                raise ge.CommandFailed("create_batch", "Target file exists", "A file with the specified path already exists [%s]" % (os.path.abspath(targetfile)), "Please use set overwrite to `yes` or `append` for apropriate action" )
        elif overwrite == 'yes':
            print("WARNING: target file %s already exists!" % (os.path.abspath(targetfile)))
            print("         Overwriting exisiting file.")
        elif overwrite == 'append':
            print("WARNING: target file %s already exists!" % (os.path.abspath(targetfile)))
            print("         Appending to exisiting file.")
        elif overwrite == 'no':
            raise ge.CommandFailed("create_batch", "Target file exists", "A file with the specified path already exists [%s]" % (os.path.abspath(targetfile)), "Please use set overwrite to `yes` or `append` for apropriate action" )
    else:
        overwrite = 'yes'

    targetFolder = os.path.dirname(targetfile)
    if not os.path.exists(targetFolder):
        print("---> Creating target folder %s" % (targetFolder))
        os.makedirs(targetFolder)

    try:
        # --- open target file
        preexist = os.path.exists(targetfile)

        # lock file
        fl.lock(targetfile)

        # --- initalize slist
        slist = []
        
        if overwrite == 'yes':
            print("---> Creating file %s [%s]" % (os.path.basename(targetfile), targetfile))
            jfile = open(targetfile, 'w')
            # header
            print >> jfile, "# Generated by QuNex %s on %s" % (gc.get_qunex_version(), datetime.now().strftime("%Y-%m-%d_%H.%M.%s"))
            print >> jfile, "#"
            print >> jfile, "# Sessions folder: %s" % (sessionsfolder)
            print >> jfile, "# Source files: %s" % (sfiles)
            
        elif overwrite == 'append':
            slist, parameters = gc.getSessionList(targetfile)
            slist = [e['id'] for e in slist]
            print("---> Appending to file %s [%s]" % (os.path.basename(targetfile), targetfile))
            if paramfile and preexist:
                print("---> WARNING: paramfile was specified, however it will not be added as we are appending to an existing file!")
            jfile = open(targetfile, 'a')

        # --- check for param file

        if overwrite == 'yes' or not preexist:
            if paramfile is None:
                paramfile = os.path.join(sessionsfolder, 'specs', 'batch.txt')
                if not os.path.exists(paramfile):
                    print("---> WARNING: Creating empty parameter file!")
                    pfile = open(paramfile, 'w')
                    print >> pfile, parameterTemplateHeader
                    for line in gp.arglist:
                        if len(line) == 4:
                            print >> pfile, "# _%-24s : %-15s ... %s" % (line[0], line[1], line[3])
                        elif len(line) > 0:
                            print >> pfile, "#\n# " + line[0] + '\n#'
                    pfile.close()

            if os.path.exists(paramfile):
                print("---> appending parameter file [%s]." % (paramfile))
                print >> jfile, "# Parameter file: %s\n#" % (paramfile)
                with open(paramfile) as f:
                    for line in f:
                        print >> jfile, line,
            else:
                print("---> parameter files does not exist, skipping [%s]." % (paramfile))

        # -- get list of sessions folders

        missing = 0

        if sessions is not None:
            sessions, gopts = gc.getSessionList(sessions, filter=filter, verbose=False, sessionsfolder=sessionsfolder)
            files = []
            for session in sessions:
                for sfile in sfiles:
                    nfiles = glob.glob(os.path.join(sessionsfolder, session['id'], sfile))
                    if nfiles:
                        files += nfiles
                    else:
                        print("---> ERROR: no %s found for %s! Please check your data! [%s]" % (sfile, session['id'], os.path.join(sessionsfolder, session['id'], sfile)))
                        missing += 1
        else:
            files = []
            for sfile in sfiles:
                globres = glob.glob(os.path.join(sessionsfolder, '*', sfile))
                for gr in globres:
                    files.append(gr)

        # --- loop trough session files
        files.sort()
        for file in files:
            sessionid = os.path.basename(os.path.dirname(file))
            if sessionid in slist:
                print("---> Skipping: %s" % (sessionid))
            else:
                print("---> Adding: %s" % (sessionid))
                print >> jfile, "\n---"
                with open(file) as f:
                    for line in f:
                        print >> jfile, line,

        # --- close file
        jfile.close()
        fl.unlock(targetfile)

    except:
        if jfile:
            jfile.close()
            fl.unlock(targetfile)
        raise

    if not files:
        raise ge.CommandFailed("create_batch", "No session found", "No sessions found to add to the batch file!", "Please check your data!")

    if missing:
        raise ge.CommandFailed("create_batch", "Not all sessions specified added to the batch file!", "%s was missing for %d session(s)!" % (sfile, missing), "Please check your data!")



def create_list(sessionsfolder=".", sessions=None, filter=None, listfile=None, bolds=None, conc=None, fidl=None, glm=None, roi=None, boldname="bold", bold_tail=".nii.gz", img_suffix="", bold_variant="", overwrite='no', check='yes'):
    """
    ``create_list [sessionsfolder="."] [sessions=None] [filter=None] [listfile=None] [bolds=None] [conc=None] [fidl=None] [glm=None] [roi=None] [boldname="bold"] [bold_tail=".nii.gz"] [img_suffix=""] [bold_variant=""] [overwrite="no"] [check="yes"]``

    Creates a .list formated file that can be used as input to a number of
    processing and analysis functions. The function is fairly flexible, its
    output defined using a number of parameters.

    INPUTS
    ======
    
    --sessionsfolder    The location of the sessions folder where the sessions
                        to create the list reside.
    --sessions          Either a comma or pipe separated string of session 
                        names to include (can be glob patterns) or a path
                        to a batch.txt file.
    --filter            If a batch.txt file is provided a string of key-value
                        pairs (`"<key>:<value>|<key>:<value>"`). Only sessions
                        that match all the key-value pairs will be added to 
                        the list.
    --listfile          The path to the generated list file. If no path is 
                        provided, the list is created as:
                        `<studyfolder>/processing/lists/sessions.list`
    --bold_variant      Specifies an optional suffix for 'functional` folder
                        when functional files are to be taken from a folder
                        that enables a parallel workflow with functional 
                        images []. 
    --bolds             If provided the specified bold files will be added to 
                        the list. The value should be a string that lists bold 
                        numbers or bold tags in a space, comma or pipe 
                        separated string.
    --boldname          The prefix to be added to the bold number specified 
                        in bolds parameter [bold]
    --bold_tail         The full tail to be added to the bold number specified
                        in bolds parameter or bold names that match the
                        tag specified in the bolds parameeter [.nii.gz].
    --img_suffix        Specifies a suffix for 'images' folder to enable
                        support for multiple parallel workflows (e.g. 
                        <session id>/images<img_suffix>). Empty if not used. []
    --conc              If provided, the specified conc file that resides in
                        `<session id>/images<img_suffix>/functional/concs/` 
                        folder will be added to the list.
    --fidl              If provided, the specified fidl file that resides in
                        `<session id>/images<img_suffix>/functional/events/` 
                        folder will be added to the list.
    --glm               If provided, the specified glm file that resides in
                        `<session id>/images<img_suffix>/functional/` folder 
                        will be added to the list.
    --roi               If provided, the specified ROI file that resides in
                        `<session id>/images<img_suffix>/<roi>` will be added 
                        to the list. Note that `<roi>` can include a path, e.g.: 
                        `segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz`    
    --overwrite         If the specified list file already exists: [no]

                        - ask (ask interactively, what to do)
                        - yes (overwrite the existing file)
                        - no (abort creating a file)
                        - append (append sessions to the existing list file)
                         
    --check             Whether to check for existence of files to be included
                        in the list and what to do if they don't exist [yes]:

                        - yes (check for presence and abort if the file to 
                          be listed is not found)
                        - no (do not check whether files are present or not)
                        - warn (check for presence and warn if the file to be 
                          listed is not found, but do not abort)
                        - present (check for presence, warn if the file to be
                          listed is not found, but do not include missing files
                          in the list)

    USE
    ===

    The location of the list file
    -----------------------------

    The file is created at the path specified in `listfile` parameter. If no
    parameter is provided, the resulting list is saved in::

        <studyfolder>/processing/lists/sessions.list

    If a file already exists, depending on the `overwrite` parameter the
    function will:

    - ask (ask interactively, what to do)
    - yes (overwrite the existing file)
    - no (abort creating a file)
    - append (append sessions to the existing list file)

    The sessions to list
    --------------------

    Sessions to include in the list are specified using `sessions` parameter.
    This can be a pipe, comma or space separated list of session ids, a batch
    file or another list file. If a string is provided, grob patterns can be
    used (e.g. sessions="AP*|OR*") and all matching sessions will be included.

    If a batch file is provided, sessions can be filtered using the `filter`
    parameter. The parameter should be provided as a string in the format::

        "<key>:<value>|<key>:<value>"

    Only the sessions for which all the specified keys match the specified values
    will be included in the list.

    If no sessions are specified, the function will inspect the `sessionsfolder`
    and include all the sessions for which an `images` folder exists as a
    subfolder in the sessions's folder.

    The location of files to include
    --------------------------------

    By default the files to incude in the list are searched for in the 
    standard location of image and functional files:: 

        <session id>/images/functional`

    The optional `img_suffix` and `bold_variant` parameters enable specifying
    alternate folders, when imaging and functional data is being processed in
    multiple parallel workflows. When these parameters are used the files are
    added to the list from the following location::

        <session id/images<img_suffix>/functional<bold_variant>

    The files to include in the list
    --------------------------------

    The function enables inclusion of bold, conc, fidl, glm and roi files.

    bold files
    ~~~~~~~~~~

    To include bold files, specify them using the `bolds` parameter. Provide a
    string that lists bold numbers or bold task names in a space, comma or pipe
    separated string. The numeric values in the string will be interpreted as
    bold numbers to include, strings will be interpreted as bold task names as
    they are provided in the batch file. All the bolds that match any of the
    tasks listed will be included. If `all` is specified, all the bolds listed
    in the batch file will be included.

    Two other parameters are crucial for generation of bold file entries in the
    list: `boldname` and `bold_tail`.

    The bolds will be listed in the list file as::

        file:<sessionsfolder>/<session id>/images<img_suffix>/functional<bold_variant>/<boldname><boldnumber><bold_tail>

    conc files
    ~~~~~~~~~~

    To include conc files, provide a `conc` parameter. In the parameter list the
    name of the conc file to be include. Conc files will be listed as::

        conc:<sessionsfolder>/<session id>/images<img_suffix>/functional<bold_variant>/concs/<conc>

    fidl files
    ~~~~~~~~~~

    To include fidl files, provide a `fidl` parameter. In the parameter list the
    name of the fidl file to include. Fidl files will be listed as::

        fidl:<sessionsfolder>/<session id>/images<img_suffix>/functional<bold_variant>/events/<fidl>

    GLM files
    ~~~~~~~~~

    To include GLM files, provide a `glm` parameter. In the parameter list the
    name of the GLM file to include. GLM files will be listed as::

        glm:<sessionsfolder>/<session id>/images<img_suffix>/functional<bold_variant>/<glm>

    ROI files
    ~~~~~~~~~

    To include ROI files, provide a `roi` parameter. In the parameter list the
    name of the ROI file to include. ROI files will be listed as::

        roi:<sessionsfolder>/<session id>/images<img_suffix>/<roi>

    Note that for all the files the function expects the files to be present in
    the correct places within the QuNex sessions folder structure. For ROI files
    provide the relative path from the `images<img_suffix>` folder.

    Checking for presence of files
    ------------------------------

    By default the function checks if the files listed indeed exist. If a file
    is missing, the function will abort and no list will be created or appended.
    The behavior is specified using the `check` parameter that can take the
    following values:

    - yes  (check for presence and abort if the file to be listed is not found)
    - no   (do not check whether files are present or not)
    - warn (check for presence and warn if the file to be listed is not found)
    - present (check for presence, warn if the file to be listed is not found,
      but do not include the file in the list)

    EXAMPLE USE
    ===========
    
    ::

        qunex create_list bolds="1,2,3"

    The command will create a list file in `../processing/list/sessions.list` that
    will list for all the sessions found in the current folder BOLD files 1, 2, 3
    listed as::

        file:<current path>/<session id>/images/functional/bold[n].nii.gz

    ::

        qunex create_list sessionsfolder="/studies/myStudy/sessions" sessions="batch.txt" \\
                bolds="rest" listfile="lists/rest.list" bold_tail="_Atlas_s_hpss_res-mVWMWB1d.dtseries"

    The command will create a `lists/rest.list` list file in which for all the
    sessions specified in the `batch.txt` it will list all the BOLD files tagged
    as rest runs and include them as::

        file:<sessionsfolder>/<session id>/images/functional/bold[n]_Atlas_s_hpss_res-mVWMWB1d.dtseries

    ::

        qunex create_list sessionsfolder="/studies/myStudy/sessions" sessions="batch.txt" \\
                filter="EC:use" listfile="lists/EC.list" \\
                conc="bold_Atlas_dtseries_EC_s_hpss_res-mVWMWB1de.conc" \\
                fidl="EC.fidl" glm="bold_conc_EC_s_hpss_res-mVWMWB1de_Bcoeff.nii.gz" \\
                roi="segmentation/hcp/fsaverage_LR32k/aparc.32k_fs_LR.dlabel.nii"

    The command will create a list file in `lists/EC.list` that will list for
    all the sessions in the conc file, that have the key:value pair "EC:use" the
    following files::

        conc:<sessionsfolder>/<session id>/images/functional/concs/bold_Atlas_dtseries_EC_s_hpss_res-mVWMWB1de.conc
        fidl:<sessionsfolder>/<session id>/images/functional/events/EC.fidl
        glm:<sessionsfolder>/<session id>/images/functional/bold_conc_EC_s_hpss_res-mVWMWB1de_Bcoeff.nii.gz
        roi:<sessionsfolder>/<session id>/images/segmentation/hcp/fsaverage_LR32k/aparc.32k_fs_LR.dlabel.nii
    """

    print("Running create_list\n==================")

    def checkFile(fileName):
        if check == 'no':
            return True
        elif check == 'present':
            if not os.path.exists(fileName):
                print("WARNING: File does not exist [%s]!" % (fileName))
                return False
            else:
                return True
        elif check == 'warn':
            if not os.path.exists(fileName):
                print("WARNING: File does not exist, but will be included in the list anyway [%s]!" % (fileName))
            return True
        else:
            if not os.path.exists(fileName):
                raise ge.CommandFailed("create_list", "File does not exist", "A file to be included in the list does not exist [%s]" % (fileName), "Please check paths or set `check` to `no` to add the missing files anyway")

        return True

    # --- check sessions

    sessionsfolder = os.path.abspath(sessionsfolder)

    if sessions and sessions.lower() == 'none':
        sessions = None

    if filter and filter.lower() == 'none':
        filter = None

    # --- prepare parameters

    boldtags, boldnums = None, None

    if bolds:        
        bolds = [e.strip() for e in re.split(' *, *| *\| *| +', bolds)]
        boldtags = [e for e in bolds if not e.isdigit()]
        boldnums = [e for e in bolds if e.isdigit()]

    bsearch  = re.compile('bold([0-9]+)')

    images_folder     = 'images' + img_suffix
    functional_folder = 'functional' + bold_variant

    # --- prepare target file name and folder

    if listfile is None:
        listfile = os.path.join(os.path.dirname(sessionsfolder), 'processing', 'lists', 'sessions.list')
        print("WARNING: No target list file name specified.\n         The list will be created as: %s!" % (listfile))

    if os.path.exists(listfile):
        print("WARNING: Target list file %s already exists!" % (os.path.abspath(listfile)))
        if overwrite == 'ask':
            s = input("         Do you want to overwrite it (o), cancel command (c), or append to the file (a)? [o/c/a]: ")
            if s == 'o':
                print("         Overwriting exisiting file.")
                overwrite = 'yes'
            elif s == 'a':
                print("         Appending to exisiting file.")
                overwrite = 'append'
            else:
                raise ge.CommandFailed("create_list", "File exists", "The specified list file already exists [%s]" % (listfile), "Please check paths or set `overwrite` to `yes` or `append` for apropriate action")
        elif overwrite == 'yes':
            print("         Overwriting the exisiting file.")
        elif overwrite == 'append':
            print("         Appending to the exisiting file.")
        elif overwrite == 'no':
            raise ge.CommandFailed("create_list", "File exists", "The specified list file already exists [%s]" % (listfile), "Please check paths or set `overwrite` to `yes` or `append` for apropriate action")
    else:
        overwrite = 'yes'

    targetFolder = os.path.dirname(listfile)
    if targetFolder and not os.path.exists(targetFolder):
        print("---> Creating target folder %s" % (targetFolder))
        os.makedirs(targetFolder)

    # --- check sessions

    if sessions is None:
        print("WARNING: No sessions specified. The list will be generated for all sessions in the sessions folder!")
        sessions = glob.glob(os.path.join(sessionsfolder, '*', images_folder))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.getSessionList(sessions, filter=filter, verbose=False, sessionsfolder=sessionsfolder)

    if not sessions:
        raise ge.CommandFailed("create_list", "No session found", "No sessions found to add to the list file!", "Please check your data!")

    # --- generate list entries

    lines = []

    for session in sessions:
        lines.append("session id: %s" % (session['id']))

        if boldnums:
            for boldnum in boldnums:
                tfile = os.path.join(sessionsfolder, session['id'], images_folder, functional_folder, boldname + boldnum + bold_tail)
                includeFile = checkFile(tfile)
                if includeFile:
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
                tfile = os.path.join(sessionsfolder, session['id'], images_folder, functional_folder, boldname + boldnum + bold_tail)
                includeFile = checkFile(tfile)
                if includeFile:
                    lines.append("    file:" + tfile)

        if roi:
            tfile = os.path.join(sessionsfolder, session['id'], images_folder, roi)
            includeFile = checkFile(tfile)
            if includeFile:
                lines.append("    roi:" + tfile)

        if glm:
            tfile = os.path.join(sessionsfolder, session['id'], images_folder, functional_folder, glm)
            includeFile = checkFile(tfile)
            if includeFile:
                lines.append("    glm:" + tfile)

        if conc:
            tfile = os.path.join(sessionsfolder, session['id'], images_folder, functional_folder, 'concs', conc)
            includeFile = checkFile(tfile)
            if includeFile:
                lines.append("    conc:" + tfile)

        if fidl:
            tfile = os.path.join(sessionsfolder, session['id'], images_folder, functional_folder, 'events', fidl)
            includeFile = checkFile(tfile)
            if includeFile:
                lines.append("    fidl:" + tfile)

    # --- write to target file

    if overwrite == 'yes':
        print("---> Creating file %s" % (os.path.basename(listfile)))
        lfile = open(listfile, 'w')
        print >> lfile, "# Generated by QuNex %s on %s" % (gc.get_qunex_version(), datetime.now().strftime("%Y-%m-%d_%H.%M.%s"))
        print >> lfile, "#"

    elif overwrite == 'append':
        print("---> Appending to file %s" % (os.path.basename(listfile)))
        lfile = open(listfile, 'a')
        print >> lfile, "# Appended to file on %s" % (datetime.today())

    for line in lines:
        print >> lfile, line

    lfile.close()



def create_conc(sessionsfolder=".", sessions=None, filter=None, concfolder=None, concname="", bolds=None, boldname="bold", bold_tail=".nii.gz", img_suffix="", bold_variant="", overwrite='no', check='yes'):
    """
    ``create_conc [sessionsfolder="."] [sessions=None] [filter=None] [concfolder=None] [concname=""] [bolds=None] [boldname="bold"] [bold_tail=".nii.gz"] [img_suffix=""] [bold_variant=""] [overwrite="no"] [check="yes"]``

    Creates a set of .conc formated files that can be used as input
    to a number of processing and analysis functions. The function is fairly
    flexible, its output defined using a number of parameters.

    INPUTS
    ======

    --sessionsfolder    The location of the sessions folder where the sessions
                        to create the list reside.
    --sessions          Either a comma or pipe separated string of session 
                        names to include (can be glob patterns) or a path
                        to a batch.txt file.
    --filter            If a batch.txt file is provided a string of key-value
                        pairs (`"<key>:<value>|<key>:<value>"`). Only
                        sessions that match all the key-value pairs will be
                        added to the list.
    --img_suffix        Specifies an optional suffix for 'images' folder when 
                        files are to be taken from a folder that enables a
                        parallel workflow [].
    --bold_variant      Specifies an optional suffix for 'functional` folder
                        when functional files are to be taken from a folder
                        that enables a parallel workflow with functional 
                        images [].
    --concfolder        The path to the folder where conc files are to be
                        generated. If not provided, the conc files will be
                        saved to the folder:
                        `<studyfolder>/<session id>/inbox/concs/`
    --concname          The name of the conc files to generate. The formula:
                        `<session id><concname>.conc` will be used. [""]
    --bolds             A space, comma or pipe separated string that lists bold 
                        numbers or bold tags to be included in the conc file.
    --boldname          The prefix to be added to the bold number specified 
                        in bolds parameter [bold]
    --bold_tail         The full tail to be added to the bold number specified
                        in bolds parameter or bold names that match the
                        tag specified in the bolds parameeter [.nii.gz].
    --overwrite         If the specified list file already exists: [no]

                        - ask    (ask interactively, what to do)
                        - yes    (overwrite the existing file)
                        - no     (abort creating a file)
                        - append (append sessions to the existing list file)
                        
    --check             Whether to check for existence of files to be included
                        in the list and what to do if they don't exist:

                        - yes (check for presence and abort if the file to 
                          be listed is not found)
                        - no (do not check whether files are present or not)
                        - warn (check for presence and warn if the file to be 
                          listed is not found, but do not abort)

    USE
    ===   

    The location of the generated conc files
    ----------------------------------------

    The files are created at the path specified in `concfolder` parameter. If no
    parameter is provided, the resulting files are saved in::

        <studyfolder>/<session id>/inbox/concs/

    Individual files are named using the following formula::

        <session id><concname>.conc

    If a file already exists, depending on the `overwrite` parameter the
    function will:

    - ask (ask interactively, what to do)
    - yes (overwrite the existing file)
    - no  (abort creating the file)

    The sessions to process
    -----------------------

    Sessions to include in the generation of conc files are specified using
    `sessions` parameter.  This can be a pipe, comma or space separated list of
    sessions ids, a batch file or another list file. If a string is provided,
    grob patterns can be used (e.g. sessions="AP*|OR*") and all matching
    sessions will be included.

    If a batch file is provided, sessions can be filtered using the `filter`
    parameter. The parameter should be provided as a string in the format::

        "<key>:<value>|<key>:<value>"

    The conc files will be generated only for the sessions for which all the
    specified keys match the specified values.

    If no sessions are specified, the function will inspect the `sessionsfolder`
    and generate conc files for all the sessions for which an `images` folder
    exists as a subfolder in the sessions's folder.

    The files to include in the conc file
    -------------------------------------

    The bold files to include in the conc file are specified using the `bolds`
    parameter. To specify the bolds to be included in the conc files, provide a
    string that lists bold numbers or bold task names in a space, comma or pipe
    separated string. The numeric values in the string will be interpreted as
    bold numbers to include, strings will be interpreted as bold task names as
    they are provided in the batch file. All the bolds that match any of the
    tasks listed will be included. If `all` is specified, all the bolds listed
    in the batch file will be included.

    Two other parameters are cruical for generation of bold file entries in the
    conc files: `boldname` and `bold_tail`.

    The bolds will be listed in the list file as::

        file:<sessionsfolder>/<session id>/images<img_suffix>/functional<bold_variant>/<boldname><boldnumber><bold_tail>

    Note that the function expects the files to be present in the correct place
    within the QuNex sessions folder structure.

    Checking for presence of files
    ------------------------------

    By default the function checks if the files listed indeed exist. If a file
    is missing, the function will abort and no list will be created or appended.
    The behavior is specified using the `check` parameter that can take the
    following values:

    - yes  (check for presence and abort if the file to be listed is not found)
    - no   (do not check whether files are present or not)
    - warn (check for presence and warn if the file to be listed is not found)

    EXAMPLE USE
    ===========
    
    ::

        qunex create_conc bolds="1,2,3"

    The command will create set of conc files in `/inbox/concs`,
    each of them named <session id>.conc, one for each of the sessions found in
    the current folder. Each conc file will include BOLD files 1, 2, 3
    listed as::

        file:<current path>/<session id>/images/functional/bold[n].nii.gz
    
    ::

        qunex create_conc sessionsfolder="/studies/myStudy/sessions" sessions="batch.txt" \\
                bolds="WM" concname="_WM" bold_tail="_Atlas.dtseries.nii"

    The command will create for each session listed in the `batch.txt` a
    `<session id>_WM.conc` file in `sessions/inbox/concs` in which it will list
    all the BOLD files tagged as `WM` as::

        file:<sessionsfolder>/<session id>/images/functional/bold[n]_Atlas.dtseries

    ::

        qunex create_conc sessionsfolder="/studies/myStudy/sessions" sessions="batch.txt" \\
                filter="EC:use" concfolder="analysis/EC/concs" \\
                concname="_EC_s_hpss_res-mVWMWB1de" bolds="EC" \\
                bold_tail="_s_hpss_res-mVWMWB1deEC.dtseries.nii"

    For all the sessions in the `batch.txt` file that have the key:value pair
    "EC:use" set the command will create a conc file in `analysis/EC/concs`
    folder. The conc files will be named `<session id>_EC_s_hpss_res-mVWMWB1de.conc`
    and will list all the bold files that are marked as `EC` runs as::

        file:<sessionsfolder>/<session id>/images/functional/bold[N]_s_hpss_res-mVWMWB1deEC.dtseries.nii
    """

    def checkFile(fileName):
        if check == 'no':
            return True
        elif not os.path.exists(fileName):
            if check == 'warn':
                print("     WARNING: File does not exist [%s]!" % (fileName))
                return True
            else:
                print("     ERROR: File does not exist [%s]!" % (fileName))
                return False
        return True

    print("Running create_conc\n==================")

    # --- check sessions

    if sessions and sessions.lower() == 'none':
        sessions = None

    if filter and filter.lower() == 'none':
        filter = None

    sessionsfolder = os.path.abspath(sessionsfolder)

    # --- prepare parameters

    boldtags, boldnums = None, None

    if bolds:
        bolds = [e.strip() for e in re.split(' *, *| *\| *| +', bolds)]
        boldtags = [e for e in bolds if not e.isdigit()]
        boldnums = [e for e in bolds if e.isdigit()]
    else:
        raise ge.CommandError("create_conc", "No bolds specified to be included in the conc files")

    bsearch  = re.compile('bold([0-9]+)')

    images_folder     = 'images' + img_suffix
    functional_folder = 'functional' + bold_variant

    # --- prepare target file name and folder

    if concfolder is None:
        concfolder = os.path.join(sessionsfolder, 'inbox', 'concs')
        print("WARNING: No target conc folder specified.\n         The conc files will be created in folder: %s!" % (concfolder))

    if not os.path.exists(concfolder):
        print("---> Creating target folder %s" % (concfolder))
        os.makedirs(concfolder)

    # --- check sessions

    if sessions is None:
        print("WARNING: No sessions specified. The list will be generated for all sessions in the sessions folder!")
        sessions = glob.glob(os.path.join(sessionsfolder, '*', images_folder))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.getSessionList(sessions, filter=filter, verbose=False, sessionsfolder=sessionsfolder)

    if not sessions:
        raise ge.CommandFailed("create_conc", "No session found", "No sessions found to add to the list file!", "Please check your data!")

    # --- generate list entries

    error = False
    for session in sessions:

        print("---> Processing session %s" % (session['id']))
        files = []
        complete = True

        if boldnums:
            for boldnum in boldnums:
                tfile = os.path.join(sessionsfolder, session['id'], images_folder, functional_folder, boldname + boldnum + bold_tail)
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
                tfile = os.path.join(sessionsfolder, session['id'], images_folder, functional_folder, boldname + str(boldnum) + bold_tail)
                complete = complete & checkFile(tfile)
                files.append("    file:" + tfile)

        concfile = os.path.join(concfolder, session['id'] + concname + '.conc')

        if not complete and check == 'yes':
            print("     WARNING: Due to missing source files conc file was not created!")
            error = True
            continue

        if os.path.exists(concfile):
            print("     WARNING: Conc file %s already exists!" % (os.path.abspath(concfile)))
            if overwrite == 'ask':
                s = input("              Do you want to overwrite it (o) or skip (s) creating this file? [o/s]: ")
                if s == 'o':
                    print("              Overwriting exisiting file.")
                    overwrite = 'yes'
                else:
                    print("              Skipping.")
                    continue
            elif overwrite == 'yes':
                print("              Overwriting the exisiting file.")
            elif overwrite == 'no':
                print("              Skipping this conc file.")
                error = True
                continue
        else:
            overwrite = 'yes'

        # --- write to target file

        if overwrite == 'yes':
            print("     ... creating %s with %d files" % (os.path.basename(concfile), len(files)))
            cfile = open(concfile, 'w')

            print >> cfile, "number_of_files: %d" % (len(files))
            for tfile in files:
                print >> cfile, tfile

            cfile.close()

    if error:
        raise ge.CommandFailed("create_conc", "Incomplete execution", ".conc files for some sessions were not generated", "Please check report for details!")


def run_list(listfile=None, runlists=None, logfolder=None, verbose="no", eargs=None):
    """
    ``run_list listfile=<path to runlist file> runlists=<name(s) of the list(s) to run> [logfolder=None] [verbose=no] [<extra arguments>]``

    Executes the commands defined in each list.

    INPUTS
    ======

    General parameters
    ------------------

    --listfile         The runlist file containing runlists and their 
                       parameters.
    --runlists         A comma, space or pipe separated list of lists specified 
                       within runlist file to run.
    --logfolder        The folder within which to save the log.
    --mapvalues        Names of values of custom variables that will be injected
                       into specifically marked fields in the runlist file.
    --verbose          Whether to record in a log a full verbose report of the 
                       output of each command that was run ('yes') or only a
                       summary success report of each command ran. ['no']

    Multiple run_list invocations
    ----------------------------
    
    These parameters allow spreading processing of multiple sessions across 
    multiple run_list invocations:

    --sessions              Either a string with pipe `|` or comma separated 
                            list of sessions (sessions ids) to be processed
                            (use of grep patterns is possible), e.g. 
                            `"OP128,OP139,ER*"`, or a path to a batch.txt or
                            `*list` file with a list of session ids.
    --sessionids            An optional parameter explicitly specifying, which
                            of the sessions from the list provided by the 
                            `sessions` parameter are to be processed in this
                            call. If not specified, all sessions will be 
                            processed.
    --sperlist              An optional parameter specifying, how many sessions
                            to run per individual run_list invocation. If not 
                            specified, all sessions will be run through the 
                            same run_list invocation. 
    --runinpar              If multiple run_list invocations are to be run, how 
                            many should be run in parallel. The default is 1.
    --scheduler             An optional scheduler settings description string. 
                            If provided, each run_list invocation will be 
                            scheduled to run on a separate cluster node. For 
                            details about the settings string specification see 
                            the inline help for the `schedule` command.

    If these parameters are provided, the processing of the sessions will
    be split so that `sperlist` sessions will be processed by each separate
    run_list invocation. If `scheduler` is specified, each run_list invocation
    will be scheduled as a separate job on a cluster. 

    When processing is spread across multiple run_list invocations, the 
    `sperlist` parameter will be passed forward as `parsessions` parameter on
    each separate invocation (see the next section). Similarly `sessionids` will
    be passed on, adjusted for the sessions to be run with the specific run_list
    invocation (see the next section).

    Please take note that if `run_list` command is ran using a scheduler, any
    scheduler specification within the `listfile` will be ignored to avoid the
    attempts to spawn new cluster jobs when `run_list` instance is already 
    running on a cluster node.

    Importantly, if `scheduler` is specified in the `run_list` file, do bear 
    in mind, that all the commands in the list will be scheduled at the same 
    time, and not in a succession, as `run_list` can not track execution of jobs
    on individual cluster nodes.


    Parameters to pass on or ignore
    -------------------------------

    Sometimes the parameters specified in the `listfile` need to be adjusted
    in a run_list invocation. If the following parameters are listed, they will
    take precedence over parameters specified within the `listfile`: 

    --parsessions    An optional parameter specifying how many sessions to run
                     in parallel. If parsessions parameter is already specified
                     within the `listfile`, then the lower value will 
                     take precedence.
    --parelements    An optional parameter specifying how many elements to run
                     in paralel within each of the jobs (e.g. how many bolds
                     when bold processing). If parelements is already specified
                     within the `listfile`, then the lower value will
                     take precedence.
    --sessionids     An optional parameter specifying which sessions are to be 
                     processed within this run_list invocation. If `sessionids`
                     is specified within the listfile, then the value passed to 
                     run_list will take precedence.

    Sometimes one would wish to ignore a parameter specified in a list when
    running a list. The parameters to ignore can be specified using:

    --ignore            An optional comma or pipe separated list of parameters
                        to ignore when running any of the specified lists.

    USE
    ===

    runlist takes a `runlist` file and a `runlists` list of lists and executes
    the commands defined in each list. The runlist file contains commands that 
    should be run and parameters that it should use.

    LOGS AND FAILURES
    =================

    The log of the commands ran will be by default stored in 
    `<study>/processing/logs/runlogs` stamped with date and time that the 
    log was started. If a study folder is not yet created, please provide a 
    valid folder to save the logs to. If the log can not be created the 
    `run_list` command will exit with a failure.

    `run_list` is checking for a successful completion of commands that it runs.
    If any of the commands fail to complete successfully, the execution of the
    commands will stop and the failure will be reported both in stdout as well
    as the log.

    Individual commands that are run can generate their own logs, the presence
    and location of those logs depend on the specific command and settings 
    specified in the runlist file.

    RUNLIST FILE
    ============

    At the top of the runlist file global settings are defined in the form
    of `<parameter>: <value>` pairs. These are the settings that will be used as 
    defaults throughout the list and individual commands defined in the rest of 
    the runlist file.

    Each list starts with a line that consists of three dashes "---" only. The
    next line should define the name of the list by specifying:
    `list: <listname>`. The list name is the one referenced in the run_list 
    command. After the definition of the list, the default parameters for the
    list can be specified as a <parameter>:<value> pairs. These values will be 
    taken as the default for the list. They have priority over the general 
    runlist file definition in that values that are defined within a specific 
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
    runlist file. For readibility purposes it is advised that the 
    <parameter>:<value> pairs are further indented for additional four spaces.

    If a specific parameter specified at a higher level is not to be used at
    this level or below, it can be listed prefixed by a dash / minus sign.

    Example runlist file
    --------------------
    
    ::

        # global settings
        sessionsfolder : /data/testStudy/sessions
        overwrite      : yes
        sessions       : *_baseline


        ---
        list: dataImport

            command: import_bids
                inbox   : /data/datalake/EMBARC/inbox/BIDS
                archive : leave

        ---
        list: prepareHCP

            command: create_session_info

            command: create_batch
                tfile: /data/testStudy/processing/batch_baseline.txt

            command: setup_hcp

        ---
        list: doHCP
            
            sessions: /data/testStudy/processing/batch_baseline.txt
            parsessions: 4

            command: hcp_pre_freesurfer

            command: hcp_freesurfer

            command: hcp_post_freesurfer

            command: hcp_fmri_volume
                parsessions : 1
                parelements : 4

            command: hcp_fmri_surface
                parsessions : 1
                parelements : 4

        ---
        list: prepareFCPreprocessing
            parsessions : 6
            sessions    : /data/testStudy/processing/batch_baseline.txt
            bolds       : all

            command: map_hcp_data
                
            command: create_bold_brain_masks

            command: compute_bold_stats
                log: remove

            command : create_stats_report
                parsessions: 1

            command: extract_nuisance_signal

        ---
        list: runFCPreprocessing
            
            parsessions : 6
            sessions    : /data/testStudy/processing/batch_baseline.txt
            scheduler   : "SLURM,jobname=doHCP,time=00-02:00:00,ntasks=6,cpus-per-task=2,mem-per-cpu=40000,partition=pi_anticevic"

            command: preprocess_bold
                bold_actions     : shrc
                glm_residuals    : save
                bold_nuisance    : m,V,WM,WB,1d
                pignore          : hipass=linear|regress=spline|lopass=linear
                overwrite        : yes
                bolds            : rest
                image_target     : cifti
                hcp_cifti_tail   : _Atlas

        ---
        list: doPreFS
            sessions    : {sessions_var}
            parsessions : 4

            command: hcp_pre_freesurfer

    EXAMPLE USE
    ===========

    ::

        qunex run_list \
          --listfile="/data/settings/runlist.txt" \
          --runlists="dataImport,prepareHCP"
    
    ::

        qunex run_list \
          --listfile="/data/settings/runlist.txt" \
          --runlists="doHCP" \
          --sessions="/data/testStudy/processing/batch_baseline.txt" \
          --sperlist=4 \
          --scheduler="SLURM,jobname=doHCP,time=04-00:00:00,ntasks=4,cpus-per-task=2,mem-per-cpu=40000,partition=pi_anticevic"

    ::

        qunex run_list \
          --listfile="/data/settings/runlist.txt" \
          --runlists="prepareFCPreprocessing" \
          --sessions="/data/testStudy/processing/batch_baseline.txt" \
          --sperlist=4 \
          --scheduler="SLURM,jobname=doHCP,time=00-08:00:00,ntasks=4,cpus-per-task=2,mem-per-cpu=40000,partition=pi_anticevic"

    ::

        qunex run_list
          --listfile="/data/settings/runlist.txt" \
          --runlists="runFCPreprocessing" 

    ::

        qunex run_list
          --listfile="/data/settings/runlist.txt" \
          --runlists="doPreFS" \
          --mapvalues="sessions_var:/data/testStudy/processing/batch_baseline.txt" 

    The first call will execute all the commands in lists `dataImport` and 
    `prepareHCP` locally.

    The second call will execute all the steps of the HCP preprocessing pipeline, 
    in sequence. Execution will be spread across the nodes with each `run_list` 
    instance processing four sessions at a time. Based on the settings in the 
    `runlist.txt` file, the first three HCP steps will be executed with four
    sessions running in parallel, whereas the last two fMRI steps the sessions 
    will be executed serially with four BOLDS from each session being processed in
    parallel. 

    The third call will again schedule multiple `run_list` invocations, each 
    processing four sessions at a time (the lower number of `sperlist`
    and `parsessions`). In this call, the initial steps will be performed
    on all BOLD images.

    The fourth call will start a single `run_list` instance locally, however,
    this will submit both listed `preprocess_bold` commands as jobs to be run with
    six sessions per node in parallel. These two commands will be run only on BOLD
    images tagged as `rest`. 

    The last, fifth call will execute hcp_pre_freesurfer, the value of the `sessions`
    parameter here is set to a placeholder variable `sessions_var`, the value is 
    then injected from the command call by using the `mapvalues` parameter.
    Alternatively the value could be injected by setting the environmental variable
    `$sessions_var`.
    """

    verbose = verbose.lower() == 'yes'

    flags = ['test']

    if listfile is None:
        raise ge.CommandError("run_list", "listfile not specified", "No runlist file specified", "Please provide path to the runlist file!")

    if runlists is None:
        raise ge.CommandError("run_list", "runlists not specified", "No runlists specified", "Please provide list of list names to run!")

    if not os.path.exists(listfile):
        raise ge.CommandFailed("run_list", "runlist file does not exist", "Runlist file not found [%s]" % (listfile), "Please check your paths!")

    # prep log
    if logfolder is None:
        logfolder = gc.deduceFolders({'reference': listfile})["logfolder"]
    runlogfolder = os.path.join(logfolder, 'runlogs')

    # create folder if it does not exist
    if not os.path.isdir(runlogfolder):
        os.makedirs(runlogfolder)

    print("===> Saving the run_list runlog to: %s" % runlogfolder)

    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%s")
    logname = os.path.join(runlogfolder, "Log-%s-%s.log") % ("runlist", logstamp)


    # -- parse runlist file

    runList = {'parameters': {},
               'lists':{}}

    parameters = runList['parameters']

    # -- prepare mapvalues
    mapvalues = {}
    if "mapvalues" in eargs:
        tempmap = eargs["mapvalues"].split("|")

        for m in tempmap:
            m = m.split(":")
            mapvalues[m[0]] = m[1]
        
        # remove
        del eargs["mapvalues"]

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
                    # is value something we should inject
                    if "{" in value and "}" in value:
                        value = value.strip("{").strip("}")
                        # is value in global parameters or environment
                        if value in mapvalues:
                            value = mapvalues[value]
                        elif value in os.environ:
                            value = os.environ[value]
                        else:
                            raise ge.CommandFailed("run_list", "Cannot parse line", "Injection value [%s] in line [%s] not provided" % (value, line), "Please provide injection values as input parameters (--mapvalues) or as environmental variables!")

                    # set
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
                raise ge.CommandFailed("run_list", "Cannot parse line", "Unable to parse line [%s]" % (line), "Please check the runlist file [%s]" % listfile)

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
        raise ge.CommandFailed("run_list", "Cannot open log", "Unable to open log [%s]" % (logname), "Please check the paths!")

    print >> log, "\n\n============================== RUNLIST LOG ==============================\n"
    print("===> Running commands from the following lists:", ", ".join(runLists))
    print >> log, "===> Running commands from the following lists:", ", ".join(runLists), "\n"

    for runListName in runLists:
        if runListName not in runList['lists']:
            raise ge.CommandFailed("run_list", "List not found", "List with name %s not found" % (runListName), "Please check the runlist file [%s]" % listfile)

        summary += "\n\n===> list: %s" % (runListName)

        print("===> Running commands from list:", runListName)
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
                        if k in ['parsessions', 'parelements']:
                            if k in commandParameters:
                                commandParameters[k] = str(min([int(e) for e in [eargs[k], commandParameters[k]]]))
                        else:
                            commandParameters[k] = eargs[k]

            # -- remove parameters that are not allowed
            import commands as gcom
            if commandName in gcom.commands:
                allowedParameters = list(gcom.commands.get(commandName)["args"])
                if any([e in allowedParameters for e in ['sourcefolder', 'folder']]):
                    allowedParameters += gcs.extra_parameters
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
                        
            print(commandr)
            print >> log, commandr

            # -- run command
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)

            # Poll process for new output until finished
            error = False
            logging = verbose

            for line in iter(process.stdout.readline, b''):
                print(line, end=" ")
                if "ERROR in completing" in line or "ERROR:" in line or "failed with error" in line:
                    error = True
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
                print("===> Successful completion of runlist command %s" % (commandName))
    summary += "\n\n----------==== END SUMMARY ====----------"
    
    print >> log, summary
    print >> log, "\n===> Successful completion of task: run_lists %s" % (", ".join(runLists))

    print("===> Successful completion of run_lists %s" % (", ".join(runLists)))
    print(summary)

    log.close()

def stripQuotes(string):
    """
    A helper function for removing leading and trailing quotes in a string. 
    """
    string = string.strip("\"")
    string = string.strip("'")
    return string


def batch_tag2namekey(filename=None, sessionid=None, bolds=None, output='number', prefix="BOLD_"):
    """
    batch_tag2namekey \\
      --filename=<path to batch file> \\
      --sessionid=<session id> \\
      --bolds=<bold specification string> \\
      [--output="number"] \\
      [--prefix="BOLD_"]

    Reads the batch file, extracts the data for the specified session and
    returns the list of bold numbers or names that correspond to bolds
    specified using the `bolds` parameter.

    INPUTS
    ======

    --filename          Path to batch.txt file.
    --sessionid         Session id to look up.
    --bolds             Which bold images (as they are specified in the
                        batch.txt file) to process. It can be a single
                        type (e.g. 'task'), a pipe separated list (e.g.
                        'WM|Control|rest') or 'all' to process all.
    --output        ... Whether to output numbers ('number') or bold names 
                        ('name'). In the latter case the name will be extracted
                        from the 'filename' specification, if provided in the 
                        batch file, or '<prefix>[N]' if 'filename' is not 
                        specified.
    --prefix        ... The default prefix to use if a filename is not specified
                        in the batch file.
    """

    if filename is None:
        raise ge.CommandError("batchTag2Num", "No batch file specified!")

    if sessionid is None:
        raise ge.CommandError("batchTag2Num", "No session id specified!")

    if bolds is None:
        raise ge.CommandError("batchTag2Num", "No bolds specified!")

    sessions, options = gc.getSessionList(filename, sessionids=sessionid)

    if not sessions:
        raise ge.CommandFailed("batchTag2Num", "Session id not found", "Session id %s is not present in the batch file [%s]" % (sessionid, filename), "Please check your data!")

    if len(sessions) > 1:
        raise ge.CommandFailed("batchTag2Num", "More than one session id found", "More than one [%s] instance of session id [%s] is present in the batch file [%s]" % (len(sessions), sessionid, filename), "Please check your data!")

    session = sessions[0]
    options['bolds'] = bolds

    bolds, _, _, _ = gpc.useOrSkipBOLD(session, options)

    boldlist = []
    for boldnumber, boldname, boldtask, boldinfo in bolds:
        if output == 'name':
            if 'filename' in boldinfo:
                boldlist.append(boldinfo['filename'])
            else:
                boldlist.append("%s%d" % (prefix, boldnumber))
        else:
            boldlist.append(str(boldnumber))

    print("BOLDS:%s" % (",".join(boldlist)))


def gather_behavior(sessionsfolder=".", sessions=None, filter=None, sourcefiles="behavior.txt", targetfile=None, overwrite="no", check="yes", report="yes"):
    """
    ``gather_behavior [sessionsfolder="."] [sessions=None] [filter=None] [sourcefiles="behavior.txt"] [targetfile="<sessionsfolder>/inbox/behavior/behavior.txt"] [overwrite="no"] [check="yes"]``

    Gathers specified individual behavioral data from each session's behavior
    folder and compiles it into a specified group behavioral file.

    INPUTS
    ======

    --sessionsfolder  The base study sessions folder (e.g. WM44/sessions) where
                      the inbox and individual session folders are. If not 
                      specified, the current working folder will be taken as 
                      the location of the sessionsfolder. [.]
    
    --sessions        Either a string with pipe `|` or comma separated list of 
                      sessions (sessions ids) to be processed (use of grep 
                      patterns is possible), e.g. `"AP128,OP139,ER*"`, or a path
                      to a `batch.txt` or `*list` file with a list of session ids.
                      [*]

    --filter          Optional parameter used to filter sessions to include. It
                      is specifed as a string in format::
    
                        "<key>:<value>|<key>:<value>"

                      Only the sessions for which all the specified keys match
                      the specified values will be included in the list.

    --sourcefiles     A file or comma or pipe `|` separated list of files or
                      grep patterns that define, which session specific files 
                      from the behavior folder to gather data from. 
                      [`'behavior.txt'`]

    --targetfile      The path to the target file, a file that will contain
                      the joined data from all the individual session files.
                      [`'<sessionsfolder>/inbox/behavior.txt'`]

    --overwrite       Whether to overwrite an existing group behavioral file or
                      not. ['no']

    --check           Check whether all the identified sessions have data to 
                      include in the compiled group file. The possible options
                      are:

                      - yes  (check and report an error if no behavioral
                        data exists for a session)
                      - warn (warn and list the sessions for which the 
                        behavioral data was not found)
                      - no (do not run a check, ignore sessions for which
                        no behavioral data was found)

    --report          Whether to include date when file was generated and the 
                      final report in the compiled file ('yes') or not ('no'). 
                      ['yes']

    USE
    ===
    
    The command will use the `sessionsfolders`, `sessions` and `filter` 
    parameters to create a list of sessions to process. For each session, the
    command will use the `sourcefiles` parameter to identify behavioral files from
    which to compile the data from. If no file is found for a session and the
    `check` parameter is set to `yes`, the command will exit with an error.

    Once the files for each session are identified, the command will read all
    the files and compile the data into a key:value dictionary for that session.
    Once all the sessions are processed, a group file will be generated for 
    all the values encountered across sessions. If any session is missing data,
    the missing data will be identified as 'NA'

    Group data will be saved to a file specified using `targetfile` parameter. If no
    path is specified, the default location will be used::

        <sessionsfolder>/inbox/behavior/behavior.txt

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

    EXAMPLE USE
    ===========

    ::

        qunex gather_behavior sessions="AP*"

    The command will compile behavioral data present in `behavior.txt` files 
    present in all `<session id>/behavior` folder that match the "AP*" glob
    pattern in the current folder.

    The resulting file will be save in the default location::

        <current folder>/inbox/behavior

    If any of the identified sessions do not include data or if errors are 
    encountered when processing the data, the command will exit with an error.
    
    ::

        qunex gather_behavior sessionsfolder="/data/myStudy/sessions" \\
                sessions="AP*|OP*" sourcefiles="*test*|*results*" \\
                check="warn" overwrite="yes" report="no"
    
    The command will find all the session folders within `/data/myStudy/sessions`
    that have a `behavior` subfolder. It will then look for presence of any 
    files that match "*test*" or "*results*" glob pattern. The compiled data 
    will be saved in the default location. If a file already exists, it will be
    overwritten. If any errors are encountered, the command will not throw an 
    error, however it also won't report a successful completion of the task.
    The resulting file will not have information on file generation or 
    processing report.

    ::

        qunex gather_behavior sessionsfolder="/data/myStudy/sessions" \\
                sessions="/data/myStudy/processing/batch.txt" \\           
                filter="group:controls|behavioral:yes" \\
                sourcefiles="*test*|*results*" \\
                targetfile="/data/myStudy/analysis/n-bridge/controls.txt" \\
                check="no" overwrite="yes"

    The command will read the session information from the provided batch.txt 
    file. It will then process only those sessions that have the following
    lines in their description::

        group: control
        behavioral: yes

    For those sessions it will inspect '<session id>/behavior' folder for 
    presence of files that match either '*test*' or '*results*' glob pattern.
    The compiled data will be saved to the specified target file. If the target
    file exists, it will be overwritten. The command will print a full report 
    of the processing, however, it will exit with reported success even if 
    missing files or errors were encountered.
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

    print("Running gather_behavior\n======================")

    # --- check subjects folder

    sessionsfolder = os.path.abspath(sessionsfolder)

    if not os.path.exists(sessionsfolder):
        raise ge.CommandFailed("gather_behavior", "Sessions folder does not exist", "The specified sessions folder does not exist [%s]" % (sessionsfolder), "Please check paths!")

    # --- check target file

    if targetfile is None:
        targetfile = os.path.join(sessionsfolder, 'inbox', 'behavior', 'behavior.txt')

    overwrite = overwrite.lower() == 'yes'

    if os.path.exists(targetfile):
        if overwrite:
            try:
                os.remove(targetfile)
            except:
                raise ge.CommandFailed("gather_behavior", "Could not remove target file", "Existing object at the specified target location could not be deleted [%s]" % (targetfile), "Please check your paths and authorizations!")        
        else:
            raise ge.CommandFailed("gather_behavior", "Target file exists", "The specified target file already exists [%s]" % (targetfile), "Please check your paths or set overwrite to 'yes'!")        

    # --- check sessions

    if sessions and sessions.lower() == 'none':
        sessions = None

    if filter and filter.lower() == 'none':
        filter = None

    report = report.lower() == 'yes'

    # --- check sourcefiles

    sfiles = [e.strip() for e in re.split(' *, *| *\| *| +', sourcefiles)]

    # --- check sessions

    if sessions is None:
        print("---> WARNING: No sessions specified. The list will be generated for all sessions in the sessions folder!")
        sessions = glob.glob(os.path.join(sessionsfolder, '*', 'behavior'))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.getSessionList(sessions, filter=filter, verbose=False, sessionsfolder=sessionsfolder)

    if not sessions:
        raise ge.CommandFailed("gather_behavior", "No session found" , "No sessions found to process behavioral data from!", "Please check your data!")

    # --- generate list entries

    processReport = {'ok': [], 'missing': [], 'error': []}
    data = {}
    keys = []

    for session in sessions:

        files = []
        for sfile in sfiles:
            files += glob.glob(os.path.join(sessionsfolder, session['id'], 'behavior', sfile))

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
        fout = open(targetfile, 'w')
    except:
        raise ge.CommandFailed("gather_behavior", "Could not create target file", "Target file could not be created at the specified location [%s]" % (targetfile), "Please check your paths and authorizations!")        

    header = ['session id'] + keys
    if report:
        print >> fout, "# Data compiled using gather_behavior on %s" % (datetime.today())
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
        print("===> Final report")
        for status, message in reportit:
            if processReport[status]:
                print('--->', message)
                if report and status != 'ok':
                    print >> fout, '#', message
                for info in processReport[status]:
                    if status == 'error':
                        print('     %s [%s]' % info)
                        if report:
                            print >> fout, '# -> %s: %s' % info
                    else:
                        print('     %s' % (info))
                        if report and status != 'ok':
                            print >> fout, '# -> %s' % (info)

    fout.close()

    # --- exit

    if processReport['error'] or processReport['missing']:
        if check.lower() == 'yes':
            raise ge.CommandFailed("gather_behavior", "Errors encountered", "Not all sessions processed successfully!", "Sessions with missing behavioral data: %d" % (len(processReport['missing'])), "Sessions with errors in processing: %d" % (len(processReport['error'])), "Please check your data!")        
        elif check.lower() == 'warn':
            raise ge.CommandNull("gather_behavior", "Errors encountered", "Not all sessions processed successfully!", "Sessions with missing behavioral data: %d" % (len(processReport['missing'])), "Sessions with errors in processing: %d" % (len(processReport['error'])), "Please check your data!")        

    if not processReport['ok']:
        raise ge.CommandNull("gather_behavior", "No files processed", "No valid data was found!")                




def pull_sequence_names(sessionsfolder=".", sessions=None, filter=None, sourcefiles="session.txt", targetfile=None, overwrite="no", check="yes", report="yes"):
    """
    ``pull_sequence_names [sessionsfolder="."] [sessions=None] [filter=None] [sourcefiles="session.txt"] [targetfile="<sessionsfolder>/inbox/MR/sequences.txt"] [overwrite="no"] [check="yes"]``

    Gathers a list of all the sequence names across the sessions and saves it
    into a specified file.

    INPUTS
    ======

    --sessionsfolder  The base study sessions folder (e.g. WM44/sessions) where
                      the inbox and individual session folders are. If not 
                      specified, the current working folder will be taken as 
                      the location of the sessionsfolder. [.]
    
    --sessions        Either a string with pipe `|` or comma separated list of 
                      sessions (sessions ids) to be processed (use of grep 
                      patterns is possible), e.g. "AP128,OP139,ER*", or a path
                      to a `batch.txt` or `*list` file with a list of session
                      ids. [*]

    --filter          Optional parameter used to filter sessions to include. It
                      is specified as a string in format::
    
                        "<key>:<value>|<key>:<value>"

                      Only the sessions for which all the specified keys match
                      the specified values will be included in the list.

    --sourcefiles     A file or comma or pipe `|` separated list of files or
                      grep patterns that define, which session description 
                      files to check. ['session.txt']

    --targetfile      The path to the target file, a file that will contain
                      the list of all the session names from all the individual
                      session information files.
                      ['<sessionsfolder>/inbox/MR/sequences.txt']

    --overwrite       Whether to overwrite an existing file or not. ['no']

    --check           Check whether all the identified sessions have the 
                      specified information files. The possible options:
                      are:

                      - yes  (check and report an error if no information
                        exists for a session)
                      - warn (warn and list the sessions for which the 
                        neuroimaging information was not found)
                      - no   (do not run a check, ignore sessions for which
                        no imaging data was found)

    --report          Whether to include date when file was generated and the 
                      final report in the compiled file ('yes') or not ('no'). 
                      ['yes']

    USE
    ===
    
    The command will use the `sessionsfolders`, `sessions` and `filter` 
    parameters to create a list of sessions to process. For each session, the
    command will use the `sourcefiles` parameter to identify neuroimaging
    information files from which to generate the list from. If no file is found
    for a session and the `check` parameter is set to `yes`, the command will
    exit with an error.

    Once the files for each session are identified, the command will inspect the
    files for imaging data and create a list of sequence names across all 
    sessions. The list will be saved to a file specified using `targetfile` 
    parameter. If no path is specified, the default location will be used::

        <sessionsfolder>/inbox/MR/sequences.txt

    If a target file exists, it will be deleted and replaced, if the `overwrite`
    parameter is set to 'yes'. If the overwrite parameter is set to 'no', the 
    command will exit with an error.

    File formats
    ------------

    The command expects the neuroimaging data to be present in the standard 
    'session.txt' files. Please see online documentation for details. 
    Specifically, it will extract the first information following the sequence
    name.

    The resulting file will be a simple text file, with one sequence name per
    line. In addition, if `report` is set to 'yes' (the default), the resulting 
    file  will start with a comment line stating the date of creation, and at 
    the end additional comment lines will list the full report of missing files 
    and errors encountered while gathering behavioral data from individual 
    sessions.

    EXAMPLE USE
    ===========
    
    ::

        qunex pull_sequence_names sessions="AP*"

    The command will compile sequence names present in `session.txt` files 
    present in all `<session id>` folders that match the "AP*" glob
    pattern in the current working directory. 

    The resulting file will be save in the default location::

        <current folder>/inbox/MR/sequences.txt

    If any of the identified sessions do not include data or if errors are 
    encountered when processing the data, the command will exit with an error.

        qunex pull_sequence_names sessionsfolder="/data/myStudy/sessions" \\
                sessions="AP*|OP*" sourcefiles="session.txt|subject.txt" \\
                check="warn" overwrite="yes" report="no"

    The command will find all the session folders within `/data/myStudy/sessions`
    It will then look for presence of either session.txt or subject.txt files.
    The compiled data from the found files will be saved in the default 
    location. If a file already exists, it will be overwritten. If any errors 
    are encountered, the command will not throw an error, however it also won't
    report a successful completion of the task. The resulting file will not have 
    information on file generation or processing report.
    
    ::

        qunex pull_sequence_names sessionsfolder="/data/myStudy/sessions" \\
                sessions="/data/myStudy/processing/batch.txt" \\           
                filter="group:controls|behavioral:yes" \\
                sourcefiles="*.txt" \\
                targetfile="/data/myStudy/sessions/specs/hcp_mapping.txt" \\
                check="no" overwrite="yes"

    The command will read the session information from the provided batch.txt 
    file. It will then process only those sessions that have the following
    lines in their description::

        group: control
        behavioral: yes

    For those sessions it will find any files that end with `.txt` and process
    them for presence of neuroimaging information. The compiled data will be 
    saved to the specified target file. If the target file exists, it will be 
    overwritten. The command will print a full report of the processing, 
    however, it will exit with reported success even if missing files or errors 
    were encountered.
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
                        sequenceNames.append(line[0])
        f.close()

        if not sequenceNames:
            return "No sequence information found in file [%s]!" % (file)

        data += sequenceNames

        if missingNames:
            return "The following sequences had no names: %s!" % (", ".join(missingNames))

    # --- Start it up

    print("Running pull_sequence_names\n=========================")

    # --- check sessions folder

    sessionsfolder = os.path.abspath(sessionsfolder)

    if not os.path.exists(sessionsfolder):
        raise ge.CommandFailed("pull_sequence_names", "Sessions folder does not exist", "The specified sessions folder does not exist [%s]" % (sessionsfolder), "Please check paths!")

    # --- check target file

    if targetfile is None:
        targetfile = os.path.join(sessionsfolder, 'inbox', 'MR', 'sequences.txt')

    overwrite = overwrite.lower() == 'yes'

    if os.path.exists(targetfile):
        if overwrite:
            try:
                os.remove(targetfile)
            except:
                raise ge.CommandFailed("pull_sequence_names", "Could not remove target file", "Existing object at the specified target location could not be deleted [%s]" % (targetfile), "Please check your paths and authorizations!")        
        else:
            raise ge.CommandFailed("pull_sequence_names", "Target file exists", "The specified target file already exists [%s]" % (targetfile), "Please check your paths or set overwrite to 'yes'!")        

    # --- check sessions

    if sessions and sessions.lower() == 'none':
        sessions = None

    if filter and filter.lower() == 'none':
        filter = None

    report = report.lower() == 'yes'

    # --- check sourcefiles

    sfiles = [e.strip() for e in re.split(' *, *| *\| *| +', sourcefiles)]

    # --- check sessions

    if sessions is None:
        print("---> WARNING: No sessions specified. The list will be generated for all sessions in the sessions folder!")
        sessions = glob.glob(os.path.join(sessionsfolder, '*', 'behavior'))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.getSessionList(sessions, filter=filter, verbose=False, sessionsfolder=sessionsfolder)

    if not sessions:
        raise ge.CommandFailed("pull_sequence_names", "No session found" , "No sessions found to process neuroimaging data from!", "Please check your data!")

    # --- generate list entries

    processReport = {'ok': [], 'missing': [], 'error': []}
    data = []

    for session in sessions:

        files = []
        for sfile in sfiles:
            files += glob.glob(os.path.join(sessionsfolder, session['id'], sfile))

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
        fout = open(targetfile, 'w')
    except:
        raise ge.CommandFailed("pull_sequence_names", "Could not create target file", "Target file could not be created at the specified location [%s]" % (targetfile), "Please check your paths and authorizations!")        

    if report:
        print >> fout, "# Data compiled using pull_sequence_names on %s" % (datetime.today())

    data = sorted(set(data))
    for sname in data:
        print >> fout, sname

    # --- print report

    reportit = [('ok', 'Successfully processed sessions:'), ('missing', 'Sessions for which no imaging data was found'), ('error', 'Sessions for which an error was encountered')]

    if any([processReport[status] for status, message in reportit]):
        print("===> Final report")
        for status, message in reportit:
            if processReport[status]:
                print('--->', message)
                if report and status != 'ok':
                    print >> fout, '#', message
                for info in processReport[status]:
                    if status == 'error':
                        print('     %s [%s]' % info)
                        if report:
                            print >> fout, '# -> %s: %s' % info
                    else:
                        print('     %s' % (info))
                        if report and status != 'ok':
                            print >> fout, '# -> %s' % (info)

    fout.close()

    # --- exit

    if processReport['error'] or processReport['missing']:
        if check.lower() == 'yes':
            raise ge.CommandFailed("pull_sequence_names", "Errors encountered", "Not all sessions processed successfully!", "Sessions with missing imaging data: %d" % (len(processReport['missing'])), "Sessions with errors in processing: %d" % (len(processReport['error'])), "Please check your data!")        
        elif check.lower() == 'warn':
            raise ge.CommandNull("pull_sequence_names", "Errors encountered", "Not all sessions processed successfully!", "Sessions with missing imaging data: %d" % (len(processReport['missing'])), "Sessions with errors in processing: %d" % (len(processReport['error'])), "Please check your data!")        

    if not processReport['ok']:
        raise ge.CommandNull("pull_sequence_names", "No files processed", "No valid data was found!")                

# prepare variables for data export
def exportPrep(commandName, sessionsfolder, mapto, mapaction, mapexclude):
    if os.path.exists(sessionsfolder):
        sessionsfolder = os.path.abspath(sessionsfolder)
    else:
        raise ge.CommandFailed(commandName, "Sessions folder does not exist", "The specified sessions folder does not exist [%s]" % (sessionsfolder), "Please check paths!")

    if mapto:
        mapto = os.path.abspath(mapto)
    else:
        raise ge.CommandFailed(commandName, "Target not specified", "To execute the specified mapping `mapto` parameter has to be specified!", "Please check your command call!")

    if mapaction not in ['link', 'copy', 'move']:
        raise ge.CommandFailed(commandName, "Invalid action", "The action specified is not valid!", "Please specify a valid action!")

    # -- prepare exclusion
    if mapexclude:
        patterns = [e.strip() for e in re.split(', *', mapexclude)]
        mapexclude = []
        for e in patterns:
            try:
                mapexclude.append(re.compile(e))
            except:
                raise ge.CommandFailed(commandName, "Invalid exclusion" , "Could not parse the exclusion regular expression: '%s'!" % (e), "Please check mapexclude parameter!")

    return sessionsfolder, mapto, mapexclude

# prepares session.txt files for specific pipeline mapping
def create_session_info(sessions=None, pipelines="hcp", sessionsfolder=".", sourcefile="session.txt", targetfile=None, mapping=None, filter=None, overwrite="no"):
    """
    ``create_session_info sessions=<sessions specification> [pipelines=hcp] [sessionsfolder=.] [sourcefile=session.txt] [targetfile=session_<pipeline>.txt] [mapping=specs/<pipeline>_mapping.txt] [filter=None] [overwrite=no]``

    Creates session.txt files that hold the information necessary for correct
    mapping to a folder structure supporting specific pipeline processing.

    INPUTS
    ======

    --sessions        Either an explicit list (space, comma or pipe separated)
                      of sessions to process or the path to a batch or list file
                      with sessions to process. If left unspecified, "*" will be
                      used and all folders within sessionsfolders will be
                      processed.
    --pipelines       Specify a comma separated list of pipelines for which the
                      session info will be be prepared. [hcp]
    --sessionsfolder  The directory that holds sessions' folders. [.]
    --sourcefile      The "source" session.txt file. [session.txt]
    --targetfile      The "target" session.txt file. [session_<pipeline>.txt]
    --mapping         The path to the text file describing the mapping.
                      [specs/<pipeline>_mapping.txt]
    --filter          An optional "key:value|key:value" string used as a filter
                      if a batch file is used. Only sessions for which all the
                      key:value pairs are true will be processed. All the
                      sessions will be processed if no filter is provided.
    --overwrite       Whether to overwrite target files that already exist (yes)
                      or not (no). [no]

    If an explicit list is provided, each element is treated as a glob pattern
    and the command will process all matching session ids.

    USE
    ===

    The command is used to prepare session.txt files so that they hold the
    information necessary for correct mapping to a folder structure supporting
    specific pipeline preprocessing.

    For all the sessions specified, the command checks for the presence of
    specified source file (sourcefile). If the source file is found, each sequence
    name is checked against the source specified in the mapping file (mapping),
    and the specified label is aded. The results are then saved to the specified
    target file (targetfile). The resulting session information files will have
    `"<pipeline>ready: true"` key-value pair added.

    Mapping specification
    ---------------------

    The mapping file specifies the mapping between original sequence names and
    the desired pipeline labels. There are no limits to the number of mappings
    specified. Each mapping is to be specified in a single line in a form::

        <original_sequence_name>  => <user_specified_label>

    or::

        <sequence number> => <user_specified_label>

    BOLD files should be given a compound label after the => separator::

        <original_sequence_name>  => bold:<user_specified_label>

    as this allows for flexible labeling of distinct BOLD runs based on their
    content. Here the 'bold' part denotes that it is a bold file and the
    <user_speficied_label> allows for flexibility in naming. create_session_info
    will automatically number bold images in a sequential order, starting with 1.

    Any empty lines, lines starting with #, and lines without the "map to" =>
    characters in the mapping file will be ignored. In the target file, images
    with names that do not match any of the specified mappings will be given
    empty labels. When both sequence number and sequence name match, sequence
    number will have priority

    Example mapping file
    --------------------

    ::

        Example lines in a mapping file:

        C-BOLD 3mm 48 2.5s FS-P => SE-FM-AP
        C-BOLD 3mm 48 2.5s FS-A => SE-FM-PA

        T1w 0.7mm N1 => T1w
        T1w 0.7mm N2 => T1w
        T2w 0.7mm N1 => T2w
        T2w 0.7mm N2 => T2w

        RSBOLD 3mm 48 2.5s  => bold:rest
        BOLD 3mm 48 2.5s    => bold:WM

        5 => bold:sleep

        Example lines in a source session.txt file:

        01: Scout
        02: T1w 0.7mm N1
        03: T2w 0.7mm N1
        04: RSBOLD 3mm 48 2.5s
        05: RSBOLD 3mm 48 2.5s

        Resulting lines in target session_<pipeline>.txt file:

        01:                  :Scout
        02: T1w              :T1w 0.7mm N1
        03: T2w              :T2w 0.7mm N1
        04: bold1:rest       :RSBOLD 3mm 48 2.5s
        05: bold2:sleep      :RSBOLD 3mm 48 2.5s

    Note, that the old sequence names are preserved.

    EXAMPLE USE
    ===========
    
    ::

        qunex create_session_info sessions="OP*|AP*" sessionsfolder=session mapping=session/hcp_mapping.txt
    
    ::

        qunex create_session_info sessions="processing/batch_new.txt" sessionsfolder=session mapping=session/hcp_mapping.txt
    """

    print("Running create_session_info\n===================")

    # get all pipelines
    pipelines = pipelines.split(",")

    # loop over them
    for pipeline in pipelines:
        if sessions is None:
            sessions = "*"

        if mapping is None:
            mapping = os.path.join(sessionsfolder, 'specs', '%s_mapping.txt' % pipeline)

        if targetfile is None:
            targetfile = "session_%s.txt" % pipeline

        # -- get mapping ready

        if not os.path.exists(mapping):
            raise ge.CommandFailed("create_session_info", "No pipeline mapping file", "The expected pipeline mapping file does not exist!", "Please check the specified path [%s]" % (mapping))

        print(" ... Reading pipeline mapping from %s" % (mapping))

        mapping = [line.strip() for line in open(mapping) if line[0] != "#"]
        mapping = [e.split('=>') for e in mapping]
        mapping = [[f.strip() for f in e] for e in mapping if len(e) == 2]
        mappingNumber = dict([[int(e[0]), e[1]] for e in mapping if e[0].isdigit()])
        mappingName   = dict([e for e in mapping if not e[0].isdigit()])

        if not mapping:
            raise ge.CommandFailed("create_session_info", "No mapping defined", "No valid mappings were found in the mapping file!", "Please check the specified file [%s]" % (mapping))

        # -- get list of session folders

        sessions, gopts = gc.getSessionList(sessions, filter=filter, verbose=False)

        sfolders = []
        for session in sessions:
            newSet = glob.glob(os.path.join(sessionsfolder, session['id']))
            if not newSet:
                print("WARNING: No folders found that match %s. Please check your data!" % (os.path.join(sessionsfolder, session['id'])))
            sfolders += newSet

        # -- check if we have any

        if not sfolders:
            raise ge.CommandFailed("create_session_info", "No sessions found to process", "No sessions were found to process!", "Please check the data and sessions parameter!")

        # -- loop through sessions folders

        report = {'missing source': [], 'pre-existing target': [], 'pre-processed source': [], 'processed': []}
        
        for sfolder in sfolders:

            ssfile = os.path.join(sfolder, sourcefile)
            stfile = os.path.join(sfolder, targetfile)

            if not os.path.exists(ssfile):
                report['missing source'].append(sfolder)
                continue
            print(" ... Processing folder %s" % (sfolder))

            if os.path.exists(stfile) and overwrite != "yes":
                print("     ... Target file already exists, skipping! [%s]" % (stfile))
                report['pre-existing target'].append(sfolder)
                continue

            lines = [line.strip() for line in open(ssfile)]

            images = False
            pipelineok = False
            bold = 0
            nlines = []
            hasref = False
            index      = 0
            se, fm     = 0, 0
            imgtrack   = {}
            setrack    = {}
            fmtrack    = {}
            p_repl     = ""
            sepattern  = re.compile(r'SE-FM-PA|SE-FM-AP|SE-FM-LR|SE-FM-RL')
            sepatt_a   = re.compile(r'SE-FM-PA|SE-FM-LR')
            sepatt_b   = re.compile(r'SE-FM-AP|SE-FM-RL')
            sa_ctn     = 0
            sb_ctn     = 0
            fmpattern  = re.compile(r'FM-Magnitude|FM-Phase')
            fmpatt_mag = re.compile(r'FM-Magnitude')
            fmpatt_pha = re.compile(r'FM-Phase')
            fmag_ctn   = 0
            fpha_ctn   = 0
            for line in lines:
                e = line.split(':')
                sestr, fmstr = "", ""
                if len(e) > 1:
                    if e[0].strip() == '%sready' % pipeline and e[1].strip() == 'true':
                        pipelineok = True
                    if e[0].strip().isdigit():
                        if not images:
                            nlines.append('%sready: true' % pipeline)
                            index += 1
                            images = True

                        onum = int(e[0].strip())
                        oimg = e[1].strip()
                        if onum in mappingNumber:
                            repl  = mappingNumber[onum]
                        elif oimg in mappingName:
                            repl  = mappingName[oimg]
                        else:
                            repl  = " "

                        if 'boldref' in repl:
                            bold += 1
                            repl = repl.replace('boldref', 'boldref%d' % (bold))
                            hasref = True
                        elif 'bold' in repl:
                            if hasref:
                                hasref = False
                            else:
                                bold += 1
                            repl = repl.replace('bold', 'bold%d' % (bold))
                        elif sepattern.search(repl):
                            if sepattern.search(p_repl) is None and (sa_ctn == sb_ctn):
                                se += 1
                                setrack.update({index: {'num': se}})
                            if sepatt_a.search(repl):
                                sa_ctn += 1
                            elif sepatt_b.search(repl):
                                sb_ctn += 1
                            repl = repl.replace(repl, '%s' % (repl))
                        elif fmpattern.search(repl):
                            if fmpattern.search(p_repl) is None and (fmag_ctn == fpha_ctn):
                                fm += 1
                                fmtrack.update({index: {'num': fm}})
                            if fmpatt_mag.search(repl):
                                fmag_ctn += 1
                            elif fmpatt_pha.search(repl):
                                fpha_ctn += 1
                            repl = repl.replace(repl, '%s' % (repl))
                        elif repl in ['FM-GE']:
                            fm += 1
                            fmtrack.update({index: {'num': fm}})
                            repl = repl.replace(repl, '%s' % (repl))

                        explDef = any([re.search(r'se\(\d{1,2}\)|fm\(\d{1,2}\)',element) for element in e])
                        if re.search(r'(DWI:)', repl) is None and explDef is False:
                            if (se > 0) and (re.search(r'(?<!SE-)(FM-)', repl) is None):
                                sestr = ": se(%d)" % (se)
                            if (fm > 0) and (re.search(r'(SE-FM)', repl) is None):
                                fmstr = ": fm(%d)" % (fm)
                            imgtrack.update({index: {'type': repl, 'se': se, 'fm': fm}})

                        p_repl = repl

                        e[1] = " %-16s:%s%s%s" % (repl, oimg, sestr, fmstr)
                        nlines.append(":".join(e))
                    else:
                        nlines.append(line)
                else:
                    nlines.append(line)
                index += 1

            if fmag_ctn != fpha_ctn:
                print("WARNING: Field map correction (Siemens/Philips) requires one or more complete pairs of scans: FM-Magnitude/FM-Phase")
            if sa_ctn != sb_ctn:
                print("WARNING: Spin-echo field map correction requires one or more complete pairs of scans: SE-FM-PA/SE-FM-AP or SE-FM-LR/SE-FM-RL")

            for item in imgtrack:
                if imgtrack[item]['fm'] == 0 and fmtrack and re.search(r'(SE-FM)', nlines[item]) is None:
                    fmdist = [abs(ln-item) for ln in fmtrack.keys()]
                    crspfm = min(fmdist)+item
                    nlines[item] = nlines[item] + ": fm(%d)" % (fmtrack[crspfm]['num'])
                if imgtrack[item]['se'] == 0 and setrack and re.search(r'(?<!SE-)(FM-)', nlines[item]) is None:
                    sedist = [abs(ln-item) for ln in setrack.keys()]
                    crspse = min(sedist)+item
                    nlines[item] = nlines[item] + ": se(%d)" % (setrack[crspse]['num'])

            if pipelineok:
                print("     ... %s already pipeline ready" % (sourcefile))
                if sourcefile != targetfile:
                    shutil.copyfile(sourcefile, targetfile)
                report['pre-processed source'].append(sfolder)
            else:
                print("     ... writing %s" % (targetfile))
                fout = open(stfile, 'w')
                for line in nlines:
                    print >> fout, line
                report['processed'].append(sfolder)

    print("\n===> Final report")

    for status in ['pre-existing target', 'pre-processed source', 'processed', 'missing source']:
        if report[status]:
            print("---> sessions with %s file:" % (status))
            for session in report[status]:
                print("     -> %s " % (os.path.basename(session)))

    if report['missing source']:
        raise ge.CommandFailed("create_session_info", "Unprocessed sessions", "Some sessions were missing source files [%s]!" % (sourcefile), "Please check the data and parameters!")

    return
