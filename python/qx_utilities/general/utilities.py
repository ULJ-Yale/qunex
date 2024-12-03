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
import traceback
import itertools
import yaml
import general.commands_support as gcs
import general.process as gp
import general.core as gc
import processing.core as gpc
import general.exceptions as ge
import general.filelock as fl
import general.parser as parser
import general.all_commands as gac


parameterTemplateHeader = """#  Parameters file
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
#  (... <description>) after the values for the parameters to be used."""


def manage_study(studyfolder=None, action="create", folders=None, verbose=False):
    """
    manage_study studyfolder=None action="create"

    A helper function called by create_study and check_study that does the
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
                raise ge.CommandFailed(
                    "manage_study",
                    "Folder structure file [%s] not found!" % folders,
                    "Please check the value of the folders parameter.",
                )

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
                    raise ge.CommandFailed(
                        "manage_study",
                        "I/O error: %s" % (errstr),
                        "Folder could not be created due to '%s' error!" % (errstr),
                        "Folder to create: %s" % (tfolder),
                        "Please check paths and permissions!",
                    )

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

        # ---> parameter template
        paramFile = os.path.join(
            studyfolder, "sessions", "specs", "parameters_example.txt"
        )
        try:
            f = os.open(paramFile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(f, bytes(gc.print_qunex_header(), encoding="utf8"))
            # os.write(f, bytes("# Generated by QuNex %s on %s\n" % (gc.get_qunex_version(), datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")), encoding="utf8"))
            os.write(f, bytes("#\n", encoding="utf8"))
            os.write(f, bytes((parameterTemplateHeader + "\n"), encoding="utf8"))
            for line in gp.arglist:
                if len(line) == 4:
                    os.write(
                        f,
                        bytes(
                            "# _%-24s : %-15s # ... %s\n" % (line[0], line[1], line[3]),
                            encoding="utf8",
                        ),
                    )
                elif len(line) > 0:
                    os.write(f, bytes("#\n# " + line[0] + "\n#\n", encoding="utf8"))
            os.close(f)
            if verbose:
                print(" ... created parameters_example.txt file")

        except OSError as e:
            if e.errno == errno.EEXIST:
                if verbose:
                    print(" ... parameters_example.txt file already exists")
            else:
                errstr = os.strerror(e.errno)
                raise ge.CommandFailed(
                    "manage_study",
                    "I/O error: %s" % (errstr),
                    "Parameters template file could not be created [%s]!" % (paramFile),
                    "Please check paths and permissions!",
                )

        # ---> mapping example
        # get all files that match the pattern
        examplesFolder = os.path.join(niuTemplateFolder, "templates")
        mappingExamples = glob.glob(examplesFolder + "/*_mapping_example.txt")
        for srcFile in mappingExamples:
            try:
                # extract filename only
                fileName = os.path.basename(srcFile)
                # destination path and file
                mapFile = os.path.join(studyfolder, fileName)
                dstFile = os.open(mapFile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                # read src
                srcContent = open(srcFile, "r").read()
                os.write(dstFile, bytes(srcContent, encoding="utf8"))
                os.close(dstFile)
                if verbose:
                    print(" ... created %s file" % dstFile)

            except OSError as e:
                if e.errno == errno.EEXIST:
                    if verbose:
                        print(" ... %s file already exists" % dstFile)
                else:
                    errstr = os.strerror(e.errno)
                    raise ge.CommandFailed(
                        "manage_study",
                        "I/O error: %s" % (errstr),
                        "Parameters template file could not be created [%s]!"
                        % (paramFile),
                        "Please check paths and permissions!",
                    )

        # ---> markFile
        markFile = os.path.join(studyfolder, ".qunexstudy")

        # ... map .mnapstudy to qunexstudy
        if os.path.exists(os.path.join(studyfolder, ".mnapstudy")):
            try:
                f = os.open(markFile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                markcontent = open(os.path.join(studyfolder, ".mnapstudy"), "r").read()
                os.write(f, bytes(markcontent, encoding="utf8"))
                os.close(f)
                if verbose:
                    print(" ... converted .mnapstudy file to .qunexstudy")
            except OSError as e:
                if e.errno == errno.EEXIST:
                    if verbose:
                        print(" ... .qunexstudy file already exists")
                else:
                    errstr = os.strerror(e.errno)
                    raise ge.CommandFailed(
                        "manage_study",
                        "I/O error: %s" % (errstr),
                        ".qunexstudy file could not be created [%s]!" % (markFile),
                        "Please check paths and permissions!",
                    )

            try:
                shutil.copystat(os.path.join(studyfolder, ".mnapstudy"), markFile)
                os.unlink(os.path.join(studyfolder, ".mnapstudy"))
            except:
                pass

        try:
            username = getpass.getuser()
        except:
            username = "unknown user"

        try:
            f = os.open(markFile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(
                f,
                bytes(
                    "%s study folder created on %s by %s."
                    % (
                        os.path.basename(studyfolder),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        username,
                    ),
                    encoding="utf8",
                ),
            )
            os.close(f)
            if verbose:
                print(" ... created .qunexstudy file")

        except OSError as e:
            if e.errno == errno.EEXIST:
                if verbose:
                    print(" ... .qunexstudy file already exists")
            else:
                errstr = os.strerror(e.errno)
                raise ge.CommandFailed(
                    "manage_study",
                    "I/O error: %s" % (errstr),
                    ".qunexstudy file could not be created [%s]!" % (markFile),
                    "Please check paths and permissions!",
                )


def create_study_folders(folders_spec):
    """
    create_study_folders folders=None

    A helper function called by manage_study for creating study folder structure
    from a .txt file with structure specification.

    Parameters:
        --folders (str, default '$TOOLS/python/qx_utilities/templates/study_folders_default.txt'):
            Path to the file which defines the study folder structure.
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
                        i = i + 1
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

    Parameters:
        --studyfolder (str):
            The path to the study folder to be generated.

        --folders (str, default $TOOLS/python/python/qx_utilities/templates/study_folders_default.txt):
            Path to the file which defines the subfolder structure.

    Notes:
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
            ├── sessions
            |   ├── inbox
            |   │   ├── MR
            |   │   ├── EEG
            |   │   ├── BIDS
            |   │   ├── HCPLS
            |   │   ├── behavior
            |   │   ├── concs
            |   │   └── events
            |   ├── archive
            |   │   ├── MR
            |   │   ├── EEG
            |   │   ├── BIDS
            |   │   ├── HCPLS
            |   │   └── behavior
            |   ├── specs
            |   └── QC
            └── subjects

        Do note that the command will create all the missing folders in which
        the specified study is to reside. The command also prepares template
        batch_example.txt and pipeline example mapping files in
        <studyfolder>/sessions/specs folder. Finally, it creates a .qunexstudy
        file in the <studyfolder> to identify it as a study basefolder.

    Examples:
        ::

            qunex create_study \\
                --studyfolder=/Volumes/data/studies/WM.v4
    """

    print("Running create_study\n===================")

    if studyfolder is None:
        raise ge.CommandError(
            "create_study",
            "No studyfolder specified",
            "Please provide path for the new study folder using studyfolder parameter!",
        )

    manage_study(
        studyfolder=studyfolder, action="create", folders=folders, verbose=True
    )


def copy_study(
    studyfolder, existing_study, step=None, sessions=None, batchfile=None, filter=None
):
    """
    ``copy_study studyfolder=<path to study base folder> existing_study=<path to source study base folder> [step=None] [sessions=None] [batchfile=None] [filter=None]``

    Copies an existing QuNex study onto a new location.

    Parameters:
        --studyfolder (str):
            The path to the study folder to be generated.

        --existing_study (str):
            The path of an existing QuNex study that will be copied.

        --step (str, default None):
            The step which will be executed next, if provided only a subset of
            data will be copied in some cases.

        --sessions (str, default None):
            If provided, only the specified sessions from the sessions folder
            will be processed. They are to be specified as a comma separated
            list.

        --batchfile (str, default None):
            If provided, only the sessions specified in the batch file will be
            processed.

        --filter (str, default None):
            An optional parameter given as "key:value|key:value" string. Can be
            used for filtering the session data within the provided batchfile.

    Notes:
        Can be used for backing up existing studies or when copying previous
        study to continue with the processing or an analysis in a new study
        folder. If sessions parameter is provided only a subset of sessions will
        be copied over. If batchfile is provided, only the sessions specified
        in the batch file will be copied. If filter is provided, it will be
        applied to the provided batchfile before copying the study.

    Examples:
        ::

            qunex copy_study \\
                --studyfolder=/Volumes/data/studies/WM.v4 \\
                --existing_study=/Volumes/data/studies/WM.v3
    """

    print("Running copy_study\n==================\n")

    # check if mandatory parameters are provided
    print()
    print("---> Checking input parameters")
    if studyfolder is None:
        raise ge.CommandError(
            "copy_study",
            "No studyfolder specified",
            "Please provide path for the new study folder using the studyfolder parameter!",
        )
    print(f" ... studyfolder: {studyfolder}")

    if existing_study is None:
        raise ge.CommandError(
            "copy_study",
            "No existing_study specified",
            "Please provide path of an existing QuNex study by using the existing_study parameter!",
        )
    print(f" ... existing_study: {existing_study}")

    # check if the source folder is a QuNex study
    if not os.path.exists(os.path.join(existing_study, ".qunexstudy")):
        raise ge.CommandError(
            "copy_study",
            "Existing study is not a QuNex study",
            "The existing study folder does not contain a .qunexstudy file. Please provide a valid QuNex study folder.",
        )

    # if filter is provided, we need the batchfile as well
    if filter is not None and batchfile is None:
        raise ge.CommandError(
            "copy_study",
            "Filter provided, but no batchfile specified",
            "Please provide the path to the batch file using the batchfile parameter.",
        )

    # other parameters
    print(f" ... step: {step}")
    print(f" ... sessions: {sessions}")
    print(f" ... batchfile: {batchfile}")
    print(f" ... filter: {filter}")

    # create a new study at the specified location
    create_study(studyfolder=studyfolder)

    # copy analysis, processing, info folders as they are
    print()
    print("Copying top-level folders")
    for folder in ["analysis", "processing", "info"]:
        src = os.path.join(existing_study, folder)
        dst = os.path.join(studyfolder, folder)
        print(f" ... copying {src}")
        shutil.copytree(src, dst, dirs_exist_ok=True, ignore_dangling_symlinks=True)

    # copy inbox, archive, specs and QC folders inside sessions
    session_supplementary = ["inbox", "archive", "specs", "QC"]
    for folder in session_supplementary:
        src = os.path.join(existing_study, "sessions", folder)
        dst = os.path.join(studyfolder, "sessions", folder)
        print(f" ... copying {src}")
        shutil.copytree(src, dst, dirs_exist_ok=True, ignore_dangling_symlinks=True)

    # get sessions
    if batchfile is not None:
        sessions, _ = gc.get_sessions_list(
            batchfile, filter=filter, sessionids=sessions
        )
    elif sessions is not None:
        sessions = sessions.split(",")

    # copy sessions
    if sessions is None:
        sessions = os.listdir(os.path.join(existing_study, "sessions"))
        # remove archive, inbox, QC, specs
        sessions = [
            session for session in sessions if session not in session_supplementary
        ]

    print()
    print("Copying sessions")
    for session in sessions:
        src = os.path.join(existing_study, "sessions", session)
        dst = os.path.join(studyfolder, "sessions", session)
        print(f" ... copying {session}")

        # copy all files and folder from src to dst, with the exception of the hcp folder
        for item in os.listdir(src):
            if os.path.isfile(os.path.join(src, item)):
                os.makedirs(dst, exist_ok=True)
                shutil.copy2(os.path.join(src, item), os.path.join(dst, item))
            elif item != "hcp":
                shutil.copytree(
                    os.path.join(src, item),
                    os.path.join(dst, item),
                    dirs_exist_ok=True,
                    ignore_dangling_symlinks=True,
                )

        # only copy hcp folder if "hcp_" in steps but not if steps is hcp_pre_freesurfer
        if step is None or ("hcp_" in step and step != "hcp_pre_freesurfer"):
            src = os.path.join(existing_study, "sessions", session, "hcp")
            dst = os.path.join(studyfolder, "sessions", session)
            shutil.copytree(src, dst, dirs_exist_ok=True, ignore_dangling_symlinks=True)

    # fix paths in txt, conc and list files
    print()
    print("Fixing paths in relevant files")
    for root, _, files in os.walk(studyfolder):
        for file in files:
            if (
                file.endswith(".txt")
                or file.endswith(".conc")
                or file.endswith(".list")
            ):
                with open(os.path.join(root, file), "r") as f:
                    lines = f.readlines()
                with open(os.path.join(root, file), "w") as f:
                    for line in lines:
                        f.write(line.replace(existing_study, studyfolder))

    # remove unused sessions from batch files
    # assume batch files are .txt files in the processing subfolder
    if sessions:
        print()
        print("Removing unused sessions from batch files in the processing subfolder")
        processing_folder = os.path.join(studyfolder, "processing")
        for item in os.listdir(processing_folder):
            if item.endswith(".txt"):
                batchfile = os.path.join(processing_folder, item)
                print(f" ... processing {batchfile}")
                filter_batch(batchfile, sessions)


def filter_batch(batchfile, sessions=None):
    """
    A helper function that removes all unused sessions from a batch file.
    """
    batch_content = ""

    with open(batchfile, "r") as f:
        for line in f:
            batch_content += line

    # split on ---
    batch_list = batch_content.split("\n---\n")

    # new batch
    new_batch = batch_list[0]

    # iterate over other items
    for item in batch_list[1:]:
        for session in sessions:
            if session in item:
                new_batch += "\n---\n" + item

    # write back
    with open(batchfile, "w") as f:
        f.write(new_batch)


def check_study(startfolder=".", folders=None):
    """
    ``check_study startfolder="." [folders=$TOOLS/python/qx_utilities/templates/study_folders_default.txt]``

    The function looks for the path to the study folder in the hierarchy
    starting from the provided startfolder. If found it checks that all the
    standard folders are present and creates any missing ones. It returns
    the path to the study folder. If the study folder can not be identified,
    it returns None.

    ---
    Written by Grega Repovš, 2018-11-14
    """

    studyfolder = None
    testfolder = os.path.abspath(startfolder)

    while os.path.dirname(testfolder) and os.path.dirname(testfolder) != "/":
        if os.path.exists(os.path.join(testfolder, ".qunexstudy")) or os.path.exists(
            os.path.join(testfolder, ".mnapstudy")
        ):
            studyfolder = testfolder
            break
        testfolder = os.path.dirname(testfolder)

    if studyfolder:
        manage_study(studyfolder=studyfolder, action="check", folders=folders)

    return studyfolder


def create_batch(
    sessionsfolder=".",
    sourcefiles=None,
    targetfile=None,
    sessions=None,
    filter=None,
    overwrite="no",
    paramfile=None,
):
    """
    ``create_batch [sessionsfolder=.] [sourcefiles=session_hcp.txt] [targetfile=processing/batch.txt] [sessions=None] [filter=None] [overwrite=no] [paramfile=<sessionsfolder>/specs/parameters.txt]``

    Creates a joint batch file from source files in all session folders.

    Parameters:
        --sessionsfolder (str):
            The location of the <study>/sessions folder.

        --sourcefiles (str, default 'session_hcp.txt'):
            Comma separated names of source files to take from each specified
            session folder and add to batch file.

        --targetfile (str, default <study>/processing/batch.txt):
            The path to the batch file to be generated. By default, it is
            created as <study>/processing/batch.txt.

        --sessions (str, default None):
            If provided, only the specified sessions from the sessions folder
            will be processed. They are to be specified as a pipe or comma
            separated list, grob patterns are valid session specifiers.

        --filter (str, default None):
            An optional parameter given as "key:value|key:value" string. Only
            sessions with the specified key-value pairs in their source files
            will be added to the batch file.

        --overwrite (str, default 'yes'):
            In case that the specified batch file already exists, whether to
            overwrite ('yes'), abort action ('no') or append ('append') the
            found / specified sessions to the batch file. Note that
            previous data is deleted before the run, so in the case of the "yes"
            option and a failed command run, previous results will be lost.

        --paramfile (str, default <sessionsfolder>/specs/parameters.txt):
            The path to the parameter file header to be used. If not explicitly
            provided it defaults to <sessionsfolder>/specs/parameters.txt.

    Notes:
        The command combines all the sourcefiles in all session folders in
        sessionsfolder to generate a joint batch file and save it as targetfile.
        If only specific sessions are to be added or appended, "sessions"
        parameter can be used. This can be a pipe, comma or space separated list
        of session ids, another batch file or a list file. If a string is
        provided, grob patterns can be used (e.g. sessions="AP*|OR*") and all
        matching sessions will be processed.

        If no targetfile is specified, it will save the file as batch.txt in a
        processing folder parallel to the sessionsfolder. If the folder does not
        yet exist, it will create it.

        If targetfile already exists, depending on "overwrite" parameter it will:

        - 'ask' (ask interactively, what to do)
        - 'yes' (overwrite the existing file)
        - 'no' (abort creating a file)
        - 'append' (append sessions to the existing list file)

        Note that if If a batch file already exists then parameter file will not
        be added to the header of the batch unless --overwrite is set to "yes".
        If --overwrite is set to "append", then the parameters will not be
        changed, however, any sessions that are not yet present in the batch
        file will be appended at the end of the batch file.

        The command will also look for a parameter file. If it exists, it will
        prepend its content at the beginning of the batch.txt file. If no
        paramfile is specified and the default template does not exist, the
        command will print a warning and create an empty template
        (sessions/spec/batch.txt) with all the available parameters. Do note
        that this file will need to be edited with correct parameter values for
        your study.

        Alternatively, if you don't have a parameter file prepared, you can use
        or copy and modify one of the following templates:

        - legacy data template
            ``qunex/python/qx_utilities/templates/batch_legacy_parameters.txt``

        - multiband data template
            ``qunex/python/qx_utilities/templates/batch_multiband_parameters.txt``

        The command also prepends the specific batch header parameters, if they
        are saved in a specified parameters file (the default location of the
        batch header files is ``sessions/specs/``). By default the code looks
        for a header file ``sessions/specs/batch_parameters.txt``. If
        ``batch_parameters.txt`` does not exist, it will be created
        automatically, placing all the possible parameters into the header,
        their default values and explanations to allow easy editing. The command
        also supports appending new sessions to an existing batch file. The
        final batch file with the appended session information is saved in
        ``<path_to_study_folder>/processing/<name_of_batch_file>.txt``

        Details on specification of batch file processing parameters:
            The following section details how QuNex handles parameter
            specification and how to set them up in the batch file.

            Both HCP Pipelines as well as additional functional processing of
            images make use of a number of parameters. For a full and current
            list of parameters, run ``qunex -o``. These parameters can be
            specified at multiple levels.

            In order of priority, from lower to highest, they can be specified:

            -  in the header section of the study batch file
            -  in the recipe file
            -  as a command line parameter
            -  in the session section of the study batch file
            -  in the image specification of the session section of the study
               batch file

            Header section of the study batch file:
                To run most of the processing steps, a batch file needs to be
                provided (see `batch file specification
                <../../wiki/Overview/file_batch_txt.html>`__). Batch file consists of a
                header section and a list of imaging sessions. The header
                section provides the possibility to specify the default
                parameter values that are to be used throughout the study.
                Specifically, the parameters are provided as ``_<parameter
                name>: <parameter value>`` pairs. An example might be:

                ::

                   --hcp_brainsize          : 150
                   --hcp_t1samplespacing    : 0.0000021000
                   --hcp_t2samplespacing    : 0.0000021000
                   --hcp_unwarpdir          : z

                If these parameters are not specified anywhere else, the above
                values will be used.

            recipe file:
                When ``run_recipe`` utility is used, parameters can be specified
                at the global run list level, at a specific list level, and at
                an individual command level. The parameters specified will then
                be passed to the command as command line parameters. For
                details on the ``run_recipe`` command itself and how to specify
                parameters at different levels within the recipe.yaml file,
                please see `Running a list of QuNex commands
                <../../wiki/UsageDocs/RunningListsOfCommands.html>`__. These
                parameters will take priority over the parameters specified in
                the header section of the study batch file.

            Command line parameters:
                Parameters can be specified when running the command on the
                command line. Any parameter specified on the command line takes
                precedence over the parameters specified in the header section
                of the study batch file.

            Batch file individual session section:
                The second part of the study batch file consists of information
                for each individual session. Within the individual session
                sections the parameters can be specified in the ``_<parameter
                name>: <parameter value>`` format. Any parameter value
                specified in such a way will override the parameter values
                specified either in the header section of the study batch file
                or as command line parameters.

            Batch file image details section:
                Each image can have a number of parameters associated with it.
                They are listed as ``<key>(<value>)`` pairs separated by colons
                in the relevant sequence line. The keys currently in use are:

                - ``phenc`` – Phase Encoding direction (used for BOLD, SE and
                  DWI images, overriding the ``hcp_bold_unwarpdir``,
                  ``hcp_seunwarpdir`` and ``hcp_dwi_PEdir`` parameters,
                  respectively)
                - ``UnwarpDir`` – Unwarp direction (used for T1w and T2w
                  images, overriding the ``hcp_unwarpdir`` parameter)
                - ``EchoSpacing`` - Echo Spacing (used for BOLD, SE, and DWI
                  images, overriding the ``hcp_bold_echospacing``,
                  ``hcp_dwelltime``, and ``hcp_dwi_dwelltime`` parameters,
                  respectively; note that the value has to be provided in ms
                  for DWI images and in seconds for BOLD and Spin-Echo images)
                - ``DwellTime`` – Dwell Time in seconds, overriding
                  ``hcp_t1samplespacing`` and ``hcp_t2samplespacing`` parameters
                - ``se`` - the spin echo pair to use for distortion correction
                  (integer)
                - ``filename`` – the exact (unique) name of the image file

                This information is extracted from JSON sidecar files by default
                when onboarding HCPLS datasets (if the information exists),
                when onboarding DICOM datasets, this information is extracted
                from JSON sidecar files only if explicitly requested. See
                `import_dicom --addJSONInfo <import_dicom.html>`__
                optional parameter for details.

            Batch file example:
                An example of batch.txt individual session section.

                ::

                   ---
                   session: OP386_baseline
                   subject: OP386
                   dicom: /data/my_study/sessions/OP386_baseline/dicom
                   raw_data: /data/my_study/sessions/OP386_baseline/nii
                   hpc: /data/my_study/sessions/OP386_baseline/hpc

                   age: 21
                   handedness: right
                   gender: male
                   group: control

                   institution: MR Imaging Center New Amsterdam
                   device: Siemens|Prisma_fit|123456

                   --hcp_brainsize: 150
                   --hcp_fs_no_conf2hires: TRUE

                   01: Survey
                   02: T1w:             T1w 0.7mm N2 : se(1): DwellTime(0.0000459): UnwarpDir(z)
                   03: T2w:             T2w 0.7mm N2 : se(1): DwellTime(0.0000066): UnwarpDir(z)
                   04: Survey
                   05: SE-FM-AP:        C-BOLD 3mm 48 2.5s FS-P   : se(1): phenc(AP): EchoSpacing(0.0006146)
                   06: SE-FM-PA:        C-BOLD 3mm 48 2.5s FS-A   : se(1): phenc(PA): EchoSpacing(0.0006146)
                   07: bold1:rest:      BOLD 3mm 48 2.5s          : se(1): phenc(PA): EchoSpacing(0.0006029): filename(rest_PA)
                   08: bold2:task:      BOLD 3mm 48 2.5s          : se(1): phenc(PA): EchoSpacing(0.0006029): filename(task1_PA)
                   09: bold2:task:      BOLD 3mm 48 2.5s          : se(1): phenc(PA): EchoSpacing(0.0006029): filename(task2_PA)

                In the above example, ``_hcp_brainsize: 150`` and
                ``_hcp_fs_no_conf2hires: TRUE`` are specified for session
                ``OP386_baseline`` specifically. The specified values would
                take precedence over any other value specified either in the
                header section of the batch.txt file or the command line.

                Additionally, the sequence specific

                - ``DwellTime`` specifications would take precedence over
                  ``hcp_t1samplespacing`` and ``hcp_t2samplespacing`` provided
                  in batch.txt file or command call.
                - ``EchoSpacing`` specifications would take precedence over
                  ``hcp_seechospacing`` for the SE image pair provided in
                  batch.txt file or command call.
                - ``UnwarpDir`` specification would take precedence over
                  ``hcp_unwarpdir`` provided in batch.txt file or command call.
                - ``filename`` specification would define how to name the image
                  files during HCP processing if ``hcp_filename`` was set to
                  ``userdefined``.

    Examples:
        This section shows a couple of examples for compiling a group batch
        file and adding session-specific information.

        ::

            qunex create_batch \\
                --sourcefiles="session.txt" \\
                --targetfile="fcMRI/sessions_fcMRI.txt"

        The following examples prepares a batch file using defaults::

            qunex create_batch

        Prepare a batch file specifying details::

            qunex create_batch \\
                --sessionsfolder="<path_to_study_folder>/sessions/<session_id>" \\
                --sourcefiles="session_hcp.txt" \\
                --targetfile="<path_to_study_folder>/processing/batch_hcp.txt" \\
                --paramfile="<path_to_parameter_file>" \\
                --overwrite="yes"

        Append to an existing batch file using a glob pattern::

            qunex create_batch \\
                --sessionsfolder="<path_to_study_folder/sessions/<session_id>" \\
                --sourcefiles="session_hcp.txt" \\
                --targetfile="<path_to_study_folder>/processing/batch_hcp.txt" \\
                --sessions="AP*|OP*" \\
                --overwrite="append"
    """

    print("Running create_batch\n====================")

    if sessions and sessions.lower() == "none":
        sessions = None

    if filter and filter.lower() == "none":
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
        targetfile = os.path.join(
            os.path.dirname(sessionsfolder), "processing", "batch.txt"
        )

    if os.path.exists(targetfile):
        if overwrite == "yes" or overwrite is True:
            print(
                "WARNING: target file %s already exists!"
                % (os.path.abspath(targetfile))
            )
            print("         Overwriting existing file.")
        elif overwrite == "append":
            print(
                "WARNING: target file %s already exists!"
                % (os.path.abspath(targetfile))
            )
            print("         Appending to an existing file.")
        elif overwrite == "no" or overwrite is False:
            raise ge.CommandFailed(
                "create_batch",
                "Target file exists",
                "A file with the specified path already exists [%s]"
                % (os.path.abspath(targetfile)),
                "Please use set overwrite to `yes` or `append` for apropriate action",
            )
    else:
        overwrite = "yes"

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

        if overwrite == "yes" or overwrite is True:
            print(
                "---> Creating file %s [%s]"
                % (os.path.basename(targetfile), targetfile)
            )
            jfile = open(targetfile, "w")
            # header
            gc.print_qunex_header(file=jfile)
            print("#", file=jfile)
            print("# Sessions folder: %s" % (sessionsfolder), file=jfile)
            print("# Source files: %s" % (sfiles), file=jfile)

        elif overwrite == "append":
            slist, parameters = gc.get_sessions_list(targetfile)
            slist = [e["id"] for e in slist]
            print(
                "---> Appending to file %s [%s]"
                % (os.path.basename(targetfile), targetfile)
            )
            if paramfile and preexist:
                print(
                    "---> WARNING: paramfile was specified, however it will not be added as we are appending to an existing file!"
                )

            # open the file
            jfile = open(targetfile, "a")

        # --- check for param file
        if overwrite == "yes" or overwrite is True or not preexist:
            if paramfile is None:
                paramfile = os.path.join(sessionsfolder, "specs", "parameters.txt")
                if not os.path.exists(paramfile):
                    print("---> WARNING: Creating empty parameter file!")
                    pfile = open(paramfile, "w")
                    print(parameterTemplateHeader, file=pfile)
                    for line in gp.arglist:
                        if len(line) == 4:
                            print(
                                "# _%-24s : %-15s ... %s" % (line[0], line[1], line[3]),
                                file=pfile,
                            )
                        elif len(line) > 0:
                            print("#\n# " + line[0] + "\n#", file=pfile)
                    pfile.close()

            if os.path.exists(paramfile):
                print("---> appending parameter file [%s]." % (paramfile))
                print("# Parameter file: %s\n#" % (paramfile), file=jfile)
                with open(paramfile) as f:
                    for line in f:
                        jfile.write(line)
            else:
                print(
                    "---> parameter files does not exist, skipping [%s]." % (paramfile)
                )
            jfile.write("\n")

        # -- get list of sessions folders
        missing = 0

        if sessions is not None:
            sessions, gopts = gc.get_sessions_list(
                sessions, filter=filter, verbose=False, sessionsfolder=sessionsfolder
            )
            files = []
            for session in sessions:
                for sfile in sfiles:
                    nfiles = glob.glob(
                        os.path.join(sessionsfolder, session["id"], sfile)
                    )
                    if nfiles:
                        files += nfiles
                    else:
                        print(
                            "---> ERROR: no %s found for %s! Please check your data! [%s]"
                            % (
                                sfile,
                                session["id"],
                                os.path.join(sessionsfolder, session["id"], sfile),
                            )
                        )
                        missing += 1
        else:
            files = []
            for sfile in sfiles:
                globres = glob.glob(os.path.join(sessionsfolder, "*", sfile))
                for gr in globres:
                    files.append(gr)

        # --- loop trough session files
        files.sort()

        for file in files:
            sessionid = os.path.basename(os.path.dirname(file))
            if overwrite != "append" and sessionid in slist:
                print("---> Skipping: %s" % (sessionid))
            else:
                # if we are appending remove the session block
                if overwrite == "append":
                    remove_session_block(targetfile, sessionid)

                print("---> Adding: %s" % (sessionid))
                print("\n---", file=jfile)
                with open(file) as f:
                    for line in f:
                        jfile.write(line)

        # --- close file
        jfile.close()
        fl.unlock(targetfile)

    except:
        if jfile:
            jfile.close()
            fl.unlock(targetfile)
        raise

    if not files:
        raise ge.CommandFailed(
            "create_batch",
            "No session found",
            "No sessions found to add to the batch file!",
            "Please check your data!",
        )

    if missing:
        raise ge.CommandFailed(
            "create_batch",
            "Not all sessions specified added to the batch file!",
            "%s was missing for %d session(s)!" % (sfile, missing),
            "Please check your data!",
        )


def remove_session_block(file_path, session_id):
    """
    Removes session with session_id from the batch file.
    """
    # read the contents of the file
    with open(file_path, "r", encoding="UTF-8") as file:
        content = file.read()

    # split the contents into blocks using "---" separator
    blocks = content.split("---")

    # find and remove blocks containing the specified session_ids
    updated_blocks = blocks.copy()
    for block in blocks:
        if f"session: {session_id}" in block:
            updated_blocks.remove(block)

    # join the remaining blocks back together
    updated_content = "---".join(updated_blocks)

    # write the updated contents back to the file
    with open(file_path, "w", encoding="UTF-8") as file:
        file.write(updated_content)


def create_list(
    sessionsfolder=".",
    sessions=None,
    sessionids=None,
    filter=None,
    listfile=None,
    bolds=None,
    conc=None,
    fidl=None,
    glm=None,
    roi=None,
    boldname="bold",
    bold_tail=".nii.gz",
    img_suffix="",
    bold_variant="",
    overwrite="no",
    check="yes",
):
    """
    ``create_list [sessionsfolder="."] [sessions=None] [sessionids=None] [filter=None] [listfile=None] [bolds=None] [conc=None] [fidl=None] [glm=None] [roi=None] [boldname="bold"] [bold_tail=".nii.gz"] [img_suffix=""] [bold_variant=""] [overwrite="no"] [check="yes"]``

    Creates a .list formatted file that can be used as input to a number of
    processing and analysis functions. The function is fairly flexible, its
    output defined using a number of parameters.

    Parameters:
        --sessionsfolder (str, default '.'):
            The location of the sessions folder where the sessions to create the
            list reside.

        --batchfile (str, default None):
            A path to a batch.txt file.

        --sessions (str, default None):
            A comma or pipe separated string of session names to include
            (can be glob patterns).

        --filter (str, default None):
            If a batch.txt file is provided a string of key-value pairs
            (`"<key>:<value>|<key>:<value>"`). Only sessions that match all the
            key-value pairs will be added to the list.

        --listfile (str, default None):
            The path to the generated list file. If no path is provided, the
            list is created as: `<studyfolder>/processing/lists/sessions.list`

        --bold_variant (str, default ''):
            Specifies an optional suffix for 'functional` folder when functional
            files are to be taken from a folder that enables a parallel workflow
            with functional images.

        --bolds (str, default None):
            If provided the specified bold files will be added to the list. The
            value should be a string that lists bold numbers or bold tags in a
            space, comma or pipe separated string.

        --boldname (str, default 'bold'):
            The prefix to be added to the bold number specified in bolds
            parameter.

        --bold_tail (str, default '.nii.gz'):
            The full tail to be added to the bold number specified in bolds
            parameter or bold names that match the tag specified in the bolds
            parameter.

        --img_suffix (str, default ''):
            Specifies a suffix for 'images' folder to enable support for
            multiple parallel workflows (e.g. <session id>/images<img_suffix>).
            Empty if not used.

        --conc (str, default None):
            If provided, the specified conc file that resides in
            `<session id>/images<img_suffix>/functional/concs/` folder will be
            added to the list.

        --fidl (str, default None):
            If provided, the specified fidl file that resides in
            `<session id>/images<img_suffix>/functional/events/` folder will be
            added to the list.

        --glm (str, default None):
            If provided, the specified glm file that resides in
            `<session id>/images<img_suffix>/functional/` folder will be added
            to the list.

        --roi (str, default None):
            If provided, the specified ROI file that resides in
            `<session id>/images<img_suffix>/<roi>` will be added to the list.
            Note that `<roi>` can include a path, e.g.:
            `segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz`.

        --overwrite (str, default 'no'):
            If the specified list file already exists:

            - 'yes' (overwrite the existing file)
            - 'no' (abort creating a file)
            - 'append' (append sessions to the existing list file).

        --check (str, default 'yes'):
            Whether to check for existence of files to be included in the list
            and what to do if they don't exist:

            - 'yes' (check for presence and abort if the file to be listed is not
              found)
            - 'no' (do not check whether files are present or not)
            - 'warn' (check for presence and warn if the file to be listed is not
              found, but do not abort)
            - 'present' (check for presence, warn if the file to be listed is not
              found, but do not include missing files in the list).

    Notes:
        The location of the list file:
            The file is created at the path specified in `listfile` parameter.
            If no parameter is provided, the resulting list is saved in::

                <studyfolder>/processing/lists/sessions.list

            If a file already exists, depending on the `overwrite` parameter the
            function will:

            - 'yes' (overwrite the existing file)
            - 'no' (abort creating a file)
            - 'append' (append sessions to the existing list file)

        The sessions to list:
            Sessions to include in the list are specified using `sessions`
            parameter. This can be a pipe, comma or space separated list of
            session ids, a batch file or another list file. If a string is
            provided, grob patterns can be used (e.g. sessions="AP*|OR*") and
            all matching sessions will be included.

            If a batch file is provided, sessions can be filtered using the
            `filter` parameter. The parameter should be provided as a string in
            the format::

                "<key>:<value>|<key>:<value>"

            Only the sessions for which all the specified keys match the
            specified values will be included in the list.

            If no sessions are specified, the function will inspect the
            `sessionsfolder` and include all the sessions for which an `images`
            folder exists as a subfolder in the sessions's folder.

        The location of files to include:
            By default the files to incude in the list are searched for in the
            standard location of image and functional files::

                <session id>/images/functional`

            The optional `img_suffix` and `bold_variant` parameters enable
            specifying alternate folders, when imaging and functional data is
            being processed in multiple parallel workflows. When these
            parameters are used the files are added to the list from the
            following location::

                <session id/images<img_suffix>/functional<bold_variant>

            The files to include in the list
            The function enables inclusion of bold, conc, fidl, glm and roi
            files.

            bold files:
                To include bold files, specify them using the `bolds` parameter.
                Provide a string that lists bold numbers or bold task names in a
                space, comma or pipe separated string. The numeric values in the
                string will be interpreted as bold numbers to include, strings
                will be interpreted as bold task names as they are provided in
                the batch file. All the bolds that match any of the tasks listed
                will be included. If `all` is specified, all the bolds listed in
                the batch file will be included.

                Two other parameters are crucial for generation of bold file
                entries in the list: `boldname` and `bold_tail`.

                The bolds will be listed in the list file as::

                    file:<sessionsfolder>/<session id>/images<img_suffix>/functional<bold_variant>/<boldname><boldnumber><bold_tail>

            conc files:
                To include conc files, provide a `conc` parameter. In the
                parameter list the name of the conc file to be include. Conc
                files will be listed as::

                    conc:<sessionsfolder>/<session id>/images<img_suffix>/functional<bold_variant>/concs/<conc>

            fidl files:
                To include fidl files, provide a `fidl` parameter. In the
                parameter list the name of the fidl file to include. Fidl files
                will be listed as::

                    fidl:<sessionsfolder>/<session id>/images<img_suffix>/functional<bold_variant>/events/<fidl>

            GLM files:
                To include GLM files, provide a `glm` parameter. In the
                parameter list the name of the GLM file to include. GLM files
                will be listed as::

                    glm:<sessionsfolder>/<session id>/images<img_suffix>/functional<bold_variant>/<glm>

            ROI files:
                To include ROI files, provide a `roi` parameter. In the
                parameter list the name of the ROI file to include. ROI files
                will be listed as::

                    roi:<sessionsfolder>/<session id>/images<img_suffix>/<roi>

                Note that for all the files the function expects the files to be
                present in the correct places within the QuNex sessions folder
                structure. For ROI files provide the relative path from the
                `images<img_suffix>` folder.

        Checking for presence of files:
            By default the function checks if the files listed indeed exist. If
            a file is missing, the function will abort and no list will be
            created or appended. The behavior is specified using the `check`
            parameter that can take the following values:

            - 'yes'  (check for presence and abort if the file to be listed is not found)
            - 'no'   (do not check whether files are present or not)
            - 'warn' (check for presence and warn if the file to be listed is not found)
            - 'present' (check for presence, warn if the file to be listed is not found,
              but do not include the file in the list).

    Examples:
        The command::

            qunex create_list \\
                --bolds="1,2,3"

        will create a list file in `../processing/list/sessions.list` that will
        list for all the sessions found in the current folder BOLD files 1, 2, 3
        listed as::

            file:<current path>/<session id>/images/functional/bold[n].nii.gz

        The command::

            qunex create_list \\
                --sessionsfolder="/studies/myStudy/sessions" \\
                --batchfile="batch.txt" \\
                --bolds="rest" \\
                --listfile="lists/rest.list" \\
                --bold_tail="_Atlas_s_hpss_res-mVWMWB1d.dtseries"

        will create a `lists/rest.list` list file in which for all the sessions
        specified in the `batch.txt` it will list all the BOLD files tagged as
        rest runs and include them as::

            file:<sessionsfolder>/<session id>/images/functional/bold[n]_Atlas_s_hpss_res-mVWMWB1d.dtseries

        The command::

            qunex create_list \\
                --sessionsfolder="/studies/myStudy/sessions" \\
                --batchfile="batch.txt" \\
                --filter="EC:use" \\
                --listfile="lists/EC.list" \\
                --conc="bold_Atlas_dtseries_EC_s_hpss_res-mVWMWB1de.conc" \\
                --fidl="EC.fidl" \\
                --glm="bold_conc_EC_s_hpss_res-mVWMWB1de_Bcoeff.nii.gz" \\
                --roi="segmentation/hcp/fsaverage_LR32k/aparc.32k_fs_LR.dlabel.nii"

        will create a list file in `lists/EC.list` that will list for all the
        sessions in the conc file, that have the key:value pair "EC:use" the
        following files::

            conc:<sessionsfolder>/<session id>/images/functional/concs/bold_Atlas_dtseries_EC_s_hpss_res-mVWMWB1de.conc
            fidl:<sessionsfolder>/<session id>/images/functional/events/EC.fidl
            glm:<sessionsfolder>/<session id>/images/functional/bold_conc_EC_s_hpss_res-mVWMWB1de_Bcoeff.nii.gz
            roi:<sessionsfolder>/<session id>/images/segmentation/hcp/fsaverage_LR32k/aparc.32k_fs_LR.dlabel.nii
    """

    print("Running create_list\n==================")

    def checkFile(fileName):
        if check == "no":
            return True
        elif check == "present":
            if not os.path.exists(fileName):
                print("WARNING: File does not exist [%s]!" % (fileName))
                return False
            else:
                return True
        elif check == "warn":
            if not os.path.exists(fileName):
                print(
                    "WARNING: File does not exist, but will be included in the list anyway [%s]!"
                    % (fileName)
                )
            return True
        else:
            if not os.path.exists(fileName):
                raise ge.CommandFailed(
                    "create_list",
                    "File does not exist",
                    "A file to be included in the list does not exist [%s]"
                    % (fileName),
                    "Please check paths or set `check` to `no` to add the missing files anyway",
                )

        return True

    # --- check sessions

    sessionsfolder = os.path.abspath(sessionsfolder)

    if sessions and sessions.lower() == "none":
        sessions = None

    if filter and filter.lower() == "none":
        filter = None

    # --- prepare parameters

    boldtags, boldnums = None, None

    if bolds:
        bolds = [e.strip() for e in re.split(r" *, *| *\| *| +", bolds)]
        boldtags = [e for e in bolds if not e.isdigit()]
        boldnums = [e for e in bolds if e.isdigit()]

    bsearch = re.compile(r"bold([0-9]+)")

    images_folder = "images" + img_suffix
    functional_folder = "functional" + bold_variant

    # --- prepare target file name and folder

    if listfile is None:
        listfile = os.path.join(
            os.path.dirname(sessionsfolder), "processing", "lists", "sessions.list"
        )
        print(
            "WARNING: No target list file name specified.\n         The list will be created as: %s!"
            % (listfile)
        )

    if os.path.exists(listfile):
        print(
            "WARNING: Target list file %s already exists!" % (os.path.abspath(listfile))
        )
        if overwrite == "yes" or overwrite is True:
            print("         Overwriting the existing file.")
        elif overwrite == "append":
            print("         Appending to the existing file.")
        elif overwrite == "no" or overwrite is False:
            raise ge.CommandFailed(
                "create_list",
                "File exists",
                "The specified list file already exists [%s]" % (listfile),
                "Please check paths or set `overwrite` to `yes` or `append` for apropriate action",
            )
    else:
        overwrite = "yes"

    targetFolder = os.path.dirname(listfile)
    if targetFolder and not os.path.exists(targetFolder):
        print("---> Creating target folder %s" % (targetFolder))
        os.makedirs(targetFolder)

    # --- check sessions

    if sessions is None:
        print(
            "WARNING: No sessions specified. The list will be generated for all sessions in the sessions folder!"
        )
        sessions = glob.glob(os.path.join(sessionsfolder, "*", images_folder))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.get_sessions_list(
        sessions, filter=filter, verbose=False, sessionsfolder=sessionsfolder
    )

    if not sessions:
        raise ge.CommandFailed(
            "create_list",
            "No session found",
            "No sessions found to add to the list file!",
            "Please check your data!",
        )

    # --- generate list entries

    lines = []

    for session in sessions:
        lines.append("session id: %s" % (session["id"]))

        if boldnums:
            for boldnum in boldnums:
                tfile = os.path.join(
                    sessionsfolder,
                    session["id"],
                    images_folder,
                    functional_folder,
                    boldname + boldnum + bold_tail,
                )
                includeFile = checkFile(tfile)
                if includeFile:
                    lines.append("    file:" + tfile)

        if boldtags:
            try:
                bolds = [
                    (bsearch.match(v["name"]).group(1), v["name"], v["task"])
                    for (k, v) in session.items()
                    if k.isdigit() and bsearch.match(v["name"])
                ]
                if "all" not in boldtags:
                    bolds = [n for n, b, t in bolds if t in boldtags]
                else:
                    bolds = [n for n, b, t in bolds]
                bolds.sort()
            except:
                pass
            for boldnum in bolds:
                tfile = os.path.join(
                    sessionsfolder,
                    session["id"],
                    images_folder,
                    functional_folder,
                    boldname + boldnum + bold_tail,
                )
                includeFile = checkFile(tfile)
                if includeFile:
                    lines.append("    file:" + tfile)

        if roi:
            tfile = os.path.join(sessionsfolder, session["id"], images_folder, roi)
            includeFile = checkFile(tfile)
            if includeFile:
                lines.append("    roi:" + tfile)

        if glm:
            tfile = os.path.join(
                sessionsfolder, session["id"], images_folder, functional_folder, glm
            )
            includeFile = checkFile(tfile)
            if includeFile:
                lines.append("    glm:" + tfile)

        if conc:
            tfile = os.path.join(
                sessionsfolder,
                session["id"],
                images_folder,
                functional_folder,
                "concs",
                conc,
            )
            includeFile = checkFile(tfile)
            if includeFile:
                lines.append("    conc:" + tfile)

        if fidl:
            tfile = os.path.join(
                sessionsfolder,
                session["id"],
                images_folder,
                functional_folder,
                "events",
                fidl,
            )
            includeFile = checkFile(tfile)
            if includeFile:
                lines.append("    fidl:" + tfile)

    # --- write to target file

    if overwrite == "yes" or overwrite is True:
        print("---> Creating file %s" % (os.path.basename(listfile)))
        lfile = open(listfile, "w")
        gc.print_qunex_header(file=lfile)
        print("#", file=lfile)

    elif overwrite == "append":
        print("---> Appending to file %s" % (os.path.basename(listfile)))
        lfile = open(listfile, "a")
        print("# Appended to file on %s" % (datetime.today()), file=lfile)

    for line in lines:
        print(line, file=lfile)

    lfile.close()


def create_conc(
    sessionsfolder=".",
    sessions=None,
    sessionids=None,
    filter=None,
    concfolder=None,
    concname="",
    bolds=None,
    boldname="bold",
    bold_tail=".nii.gz",
    img_suffix="",
    bold_variant="",
    overwrite="no",
    check="yes",
):
    """
    ``create_conc [sessionsfolder="."] [sessions=None] [sessionids=None] [filter=None] [concfolder=None] [concname=""] [bolds=None] [boldname="bold"] [bold_tail=".nii.gz"] [img_suffix=""] [bold_variant=""] [overwrite="no"] [check="yes"]``

    Creates a set of .conc formated files that can be used as input
    to a number of processing and analysis functions. The function is fairly
    flexible, its output defined using a number of parameters.

    Parameters:
        --sessionsfolder (str):
            The location of the sessions folder where the sessions to create the
            list reside.

        --batchfile (str, default None):
            A path to a batch.txt file.

        --sessions (str, default None):
            A comma or pipe separated string of session names to include
            (can be glob patterns).

        --filter (str):
            If a batch.txt file is provided a string of key-value pairs
            (`"<key>:<value>|<key>:<value>"`). Only sessions that match all the
            key-value pairs will be added to the list.

        --img_suffix (str, default ''):
            Specifies an optional suffix for 'images' folder when files are to
            be taken from a folder that enables a parallel workflow.

        --bold_variant (str, default ''):
            Specifies an optional suffix for 'functional` folder when functional
            files are to be taken from a folder that enables a parallel workflow
            with functional images.

        --concfolder (str, default <studyfolder>/<session id>/inbox/concs/):
            The path to the folder where conc files are to be generated. If not
            provided, the conc files will be saved to the folder:
            `<studyfolder>/<session id>/inbox/concs/`

        --concname (str, default ''):
            The name of the conc files to generate. The formula:
            `<session id><concname>.conc` will be used.

        --bolds (str, default 'all'):
            A space, comma or pipe separated string that lists bold numbers or
            bold tags to be included in the conc file.

        --boldname (str, 'bold'):
            The prefix to be added to the bold number specified in bolds
            parameter.

        --bold_tail (str, default '.nii.gz'):
            The full tail to be added to the bold number specified in bolds
            parameter or bold names that match the tag specified in the bolds
            parameter.

        --overwrite (str, default 'no'):
            If the specified list file already exists:

            - yes    (overwrite the existing file)
            - no     (abort creating a file)
            - append (append sessions to the existing list file).

    Notes:
        The location of the generated conc files:
            The files are created at the path specified in `concfolder`
            parameter. If no parameter is provided, the resulting files are
            saved in::

                <studyfolder>/<session id>/inbox/concs/

            Individual files are named using the following formula::

                <session id><concname>.conc

            If a file already exists, depending on the `overwrite` parameter the
            function will:

            - ask (ask interactively, what to do)
            - yes (overwrite the existing file)
            - no  (abort creating the file)

        The sessions to process:
            Sessions to include in the generation of conc files are specified
            using `sessions` parameter. This can be a pipe, comma or space
            separated list of sessions ids, a batch file or another list file.
            If a string is provided, grob patterns can be used (e.g.
            sessions="AP*|OR*") and all matching sessions will be included.

            If a batch file is provided, sessions can be filtered using the
            `filter` parameter. The parameter should be provided as a string in
            the format::

                "<key>:<value>|<key>:<value>"

            The conc files will be generated only for the sessions for which all
            the specified keys match the specified values.

            If no sessions are specified, the function will inspect the
            `sessionsfolder` and generate conc files for all the sessions for
            which an `images` folder exists as a subfolder in the sessions's
            folder.

        The files to include in the conc file:
            The bold files to include in the conc file are specified using the
            `bolds` parameter. To specify the bolds to be included in the conc
            files, provide a string that lists bold numbers or bold task names
            in a space, comma or pipe separated string. The numeric values in
            the string will be interpreted as bold numbers to include, strings
            will be interpreted as bold task names as they are provided in the
            batch file. All the bolds that match any of the tasks listed will be
            included. If `all` is specified, all the bolds listed in the batch
            file will be included.

            Two other parameters are cruical for generation of bold file entries
            in the conc files: `boldname` and `bold_tail`.

            The bolds will be listed in the list file as::

                file:<sessionsfolder>/<session id>/images<img_suffix>/functional<bold_variant>/<boldname><boldnumber><bold_tail>

            Note that the function expects the files to be present in the
            correct place within the QuNex sessions folder structure.

        Checking for presence of files:
            By default the function checks if the files listed indeed exist. If
            a file is missing, the function will abort and no list will be
            created or appended. The behavior is specified using the `check`
            parameter that can take the following values:

            - yes  (check for presence and abort if the file to be listed is not
              found)
            - no   (do not check whether files are present or not)
            - warn (check for presence and warn if the file to be listed is not
              found).

    Examples:
        The command below will create set of conc files in `/inbox/concs`,
        each of them named <session id>.conc, one for each of the sessions found
        in the current folder::

            qunex create_conc \\
                --bolds="1,2,3"

        Each conc file will include BOLD files 1, 2, 3
        listed as::

            file:<current path>/<session id>/images/functional/bold[n].nii.gz

        The command below will create for each session listed in the `batch.txt`
        a `<session id>_WM.conc` file in `sessions/inbox/concs`::

            qunex create_conc \\
                --sessionsfolder="/studies/myStudy/sessions" \\
                --batchfile="batch.txt" \\
                --bolds="WM" \\
                --concname="_WM" \\
                --bold_tail="_Atlas.dtseries.nii"

        In it it will list all the BOLD files tagged as `WM` as::

            file:<sessionsfolder>/<session id>/images/functional/bold[n]_Atlas.dtseries

        For all the sessions in the `batch.txt` file that have the key:value
        pair "EC:use" set the command below will create a conc file in
        `analysis/EC/concs` folder::

            qunex create_conc \\
                --sessionsfolder="/studies/myStudy/sessions" \\
                --batchfile="batch.txt" \\
                --filter="EC:use" \\
                --concfolder="analysis/EC/concs" \\
                --concname="_EC_s_hpss_res-mVWMWB1de" \\
                --bolds="EC" \\
                --bold_tail="_s_hpss_res-mVWMWB1deEC.dtseries.nii"

        The conc files will be named `<session id>_EC_s_hpss_res-mVWMWB1de.conc`
        and will list all the bold files that are marked as `EC` runs as::

            file:<sessionsfolder>/<session id>/images/functional/bold[N]_s_hpss_res-mVWMWB1deEC.dtseries.nii
    """

    def checkFile(fileName):
        if check == "no":
            return True
        elif not os.path.exists(fileName):
            if check == "warn":
                print("     WARNING: File does not exist [%s]!" % (fileName))
                return True
            else:
                print("     ERROR: File does not exist [%s]!" % (fileName))
                return False
        return True

    print("Running create_conc\n==================")

    # --- check sessions

    if sessions and sessions.lower() == "none":
        sessions = None

    if filter and filter.lower() == "none":
        filter = None

    sessionsfolder = os.path.abspath(sessionsfolder)

    # --- prepare parameters

    boldtags, boldnums = None, None

    if bolds:
        bolds = [e.strip() for e in re.split(r" *, *| *\| *| +", bolds)]
        boldtags = [e for e in bolds if not e.isdigit()]
        boldnums = [e for e in bolds if e.isdigit()]
    else:
        raise ge.CommandError(
            "create_conc", "No bolds specified to be included in the conc files"
        )

    bsearch = re.compile(r"bold([0-9]+)")

    images_folder = "images" + img_suffix
    functional_folder = "functional" + bold_variant

    # --- prepare target file name and folder

    if concfolder is None:
        concfolder = os.path.join(sessionsfolder, "inbox", "concs")
        print(
            "WARNING: No target conc folder specified.\n         The conc files will be created in folder: %s!"
            % (concfolder)
        )

    if not os.path.exists(concfolder):
        print("---> Creating target folder %s" % (concfolder))
        os.makedirs(concfolder)

    # --- check sessions

    if sessions is None:
        print(
            "WARNING: No sessions specified. The list will be generated for all sessions in the sessions folder!"
        )
        sessions = glob.glob(os.path.join(sessionsfolder, "*", images_folder))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.get_sessions_list(
        sessions, filter=filter, verbose=False, sessionsfolder=sessionsfolder
    )

    if not sessions:
        raise ge.CommandFailed(
            "create_conc",
            "No session found",
            "No sessions found to add to the list file!",
            "Please check your data!",
        )

    # --- generate list entries

    error = False
    for session in sessions:
        print("---> Processing session %s" % (session["id"]))
        files = []
        complete = True

        if boldnums:
            for boldnum in boldnums:
                tfile = os.path.join(
                    sessionsfolder,
                    session["id"],
                    images_folder,
                    functional_folder,
                    boldname + boldnum + bold_tail,
                )
                complete = complete & checkFile(tfile)
                files.append("    file:" + tfile)

        if boldtags:
            try:
                bolds = [
                    (int(bsearch.match(v["name"]).group(1)), v["name"], v["task"])
                    for (k, v) in session.items()
                    if k.isdigit() and bsearch.match(v["name"])
                ]
                if "all" not in boldtags:
                    bolds = [n for n, b, t in bolds if t in boldtags]
                else:
                    bolds = [n for n, b, t in bolds]
                bolds.sort()
            except:
                pass
            for boldnum in bolds:
                tfile = os.path.join(
                    sessionsfolder,
                    session["id"],
                    images_folder,
                    functional_folder,
                    boldname + str(boldnum) + bold_tail,
                )
                complete = complete & checkFile(tfile)
                files.append("    file:" + tfile)

        concfile = os.path.join(concfolder, session["id"] + concname + ".conc")

        if not complete and check == "yes":
            print(
                "     WARNING: Due to missing source files conc file was not created!"
            )
            error = True
            continue

        if os.path.exists(concfile):
            print(
                "     WARNING: Conc file %s already exists!"
                % (os.path.abspath(concfile))
            )
            if overwrite == "yes" or overwrite is True:
                print("              Overwriting the existing file.")
            elif overwrite == "no" or overwrite is False:
                print("              Skipping this conc file.")
                error = True
                continue
        else:
            overwrite = "yes"

        # --- write to target file

        if overwrite == "yes" or overwrite is True:
            print(
                "     ... creating %s with %d files"
                % (os.path.basename(concfile), len(files))
            )
            cfile = open(concfile, "w")

            print("number_of_files: %d" % (len(files)), file=cfile)
            for tfile in files:
                print(tfile, file=cfile)

            cfile.close()

    if error:
        raise ge.CommandFailed(
            "create_conc",
            "Incomplete execution",
            ".conc files for some sessions were not generated",
            "Please check report for details!",
        )


def _is_qunex_command(command):
    """
    Check if the command is a QuNex command.

    Parameters:
        command (str): The command to check.
    """
    for full_name, _, _ in gac.all_qunex_commands:
        full_name = full_name.split(".")[-1]
        if full_name == command:
            return True

    return False


def run_recipe(recipe_file=None, recipe=None, steps=None, logfolder=None, eargs=None):
    """
    ``run_recipe [recipe_file=None] [recipe=None] [steps=None] [logfolder=None] [<extra arguments>]``

    Executes the commands defined in each recipe.

    INPUTS
    ======

    General parameters
    ------------------

    --recipe_file   path to a YAML file that contains recipe definitions.
    --recipe        Name of the recipe in the recipe_file to run.
    --steps         A comma separated list of steps (QuNex commands) to run.
                    This is an alternative to specifying the recipe file and
                    a recipe name.
    --logfolder     The folder within which to save the log.

    Multiple run_recipe invocations
    ----------------------------

    These parameters allow spreading processing of multiple sessions across
    multiple run_recipe invocations:

    --batchfile             A path to a batch.txt file.
    --sessions              Either a string with comma separated list of
                            sessions (sessions ids) to be processed (use of grep
                            patterns is possible), e.g.  `"OP128,OP139,ER*"` or
                            `*list` file with a list of session ids.
    --scheduler             An optional scheduler settings description string.
                            If provided, each run_recipe invocation will be
                            scheduled to run on a separate cluster node. For
                            details about the settings string specification see
                            the inline help for the `schedule` command.

    Please take note that if `run_recipe` command is ran using a scheduler, any
    scheduler specification within the `recipe_file` will be ignored to avoid
    the attempts to spawn new cluster jobs when `run_recipe` instance is
    already running on a cluster node.

    Importantly, if `scheduler` is specified in the `run_recipe` file, do bear
    in mind, that all the commands in the recipe will be scheduled at the same
    time, and not in a succession, as `run_recipe` can not track execution of
    jobs on individual cluster nodes.

    Parallel processing
    -------------------

    To setup run_recipe parallelism, you can use the traditional parsessions and
    parelements parameters.

    --parsessions    An optional parameter specifying how many sessions to run
                     in parallel.
    --parelements    An optional parameter specifying how many elements to run
                     in parallel within each of the jobs (e.g. how many bolds
                     when bold processing).

    The parsessions parameter defines the number of sessions that will be ran in
    parallel within a single run_recipe invocation. The default is 1, which
    means that each session will be ran in parallel within a separate job. If
    parsessions is set to the number of sessions, then all the sessions will
    be executed in sequence within a single run_recipe invocation.

    USE
    ===

    run_recipe takes a `recipe_file` and a `recipe` name and executes
    the commands defined in the recipe. The `recipe_file` contains commands that
    should be run and parameters that it should use. Alternatively, you can
    provide a comma separated list of commands with the `steps` parameter.

    LOGS AND FAILURES
    =================

    The log of the commands ran will be by default stored in
    `<study>/processing/logs/runlogs` stamped with date and time that the
    log was started. If a study folder is not yet created, please provide a
    valid folder to save the logs to. If the log can not be created the
    `run_recipe` command will exit with a failure.

    `run_recipe` is checking for a successful completion of commands that it runs.
    If any of the commands fail to complete successfully, the execution of the
    commands will stop and the failure will be reported both in stdout as well
    as the log.

    Individual commands that are run can generate their own logs, the presence
    and location of those logs depend on the specific command and settings
    specified in the recipe file.

    THE RECIPE FILE
    ===============

    Recipe files use YAML markup language. At the top of the recipe file is the
    global_parameters section, where the global settings are defined in the form
    of `<parameter>: <value>` pairs. These are the settings that will be used as
    defaults throughout all recipes and individual commands defined in the rest
    of the recipe file.

    Recpies are defined in the recipes portion of the file where each recipe is
    defined by its unique name. Each recipe has two sections, the parameters and
    the commands. The parameters section defines the parameters and the values
    that are specific to that recipe. The commands section defines the commands
    that are specific to that recipe along with command specific parameters. All
    parameters are provided in the form of <parameter>:<value> pairs. Recipe
    level parameters have a higher priority than global parameters, while
    command level parameters have a higher priority than recipe level
    parameters. Parameters provided through the command line interface call have
    the highest priority, meaning that their valus will override any values in
    recipe files.

    Example recipe file
    -------------------

    ::

        global_parameters:
            sessionsfolder    : /data/qx_study/sessions
            sessions          : OP101,OP102
            overwrite         : "yes"
            batchfile         : /data/qx_study/processing/batch.txt

        recipes:
            onboard_dicom:
                commands:
                    - create_study:
                        studyfolder: /data/qx_study
                    - import_dicom:
                        masterinbox: /data/qx_data
                        archive: leave
                    - create_session_info
                        mapping: /data/qx_specs/hcp_mapping.txt
                    - create_batch:
                        targetfile: /data/qx_study/processing/batch.txt
                        paramfile : /data/qx_specs/hcp_parameters.txt
                    - setup_hcp

            hcp_preprocess:
                parsessions: 2

                commands:
                    - hcp_pre_freesurfer
                    - hcp_freesurfer
                    - hcp_post_freesurfer
                    - hcp_fmri_volume
                    - hcp_fmri_surface

            hcp_denoise:
                commands:
                    - hcp_icafix:
                        hcp_matlab_mode: "{{$MATLAB_MODE}}"
                    - hcp_msmall
                        hcp_matlab_mode: "{{$MATLAB_MODE}}"

    EXAMPLE USE
    ===========

    ::

        qunex run_recipe \\
          --recipe_file="/data/settings/recipe.yaml" \\
          --recipe="onboard_dicom"

    ::

        qunex run_recipe \\
          --recipe_file="/data/settings/recipe.yaml" \\
          --recipe="hcp_preprocess" \\
          --batchfile="/data/testStudy/processing/batch_baseline.txt" \\
          --scheduler="SLURM,jobname=doHCP,time=04-00:00:00,cpus-per-task=2,mem-per-cpu=40000,partition=week"

    ::

        export MATLAB_MODE="interpreted"
        qunex run_recipe \\
          --recipe_file="/data/settings/recipe.yaml" \\
          --recipe="hcp_denoise"

    ::

        qunex run_recipe \\
          --sessionsfolder="/data/qx_study/sessions" \\
          --batchfile="/data/qx_study/processing/batch.txt" \\
          --steps="hcp_pre_freesurfer,hcp_freesurfer,hcp_post_freesurfer"

    The first call will execute all the commands in recipe `onboard_dicom`.

    The second call will execute all the steps of the HCP preprocessing pipeline
    via a scheduler. It will execute two sessions in parallel within the run.
    in sequence.

    The third call will execute the hcp_denoise list where the  hcp_matlab_mode
    parameter will be set to "interpreted" this value will be read from the
    system environment variable $MATLAB_MODE. This is an example of how you can
    inject custom values into specially marked slots (marked with "{{<label>}}")
    in the recipe file. Note that the labels need to be provided in the form of
    a string, so they need to be encapsulated with double quotes.

    The forth example shows how to use the steps parameter to run a set of
    commands sequentially.
    """

    flags = ["test"]

    if recipe_file is not None and steps is not None:
        raise ge.CommandError(
            "run_recipe",
            "both recipe_file and steps are specified",
            "BOth recipe file and steps specified",
            "Please set only one parameter!",
        )

    if recipe_file is None and steps is None:
        raise ge.CommandError(
            "run_recipe",
            "both recipe_file and steps are not specified",
            "No recipe file or steps specified",
            "Please provide path to the recipe file or a comma separated list of steps to run!",
        )

    if recipe_file is not None and recipe is None:
        raise ge.CommandError(
            "run_recipe",
            "recipe not specified",
            "No recipe specified",
            "Please provide the recipe name!",
        )

    if recipe_file is not None and not os.path.exists(recipe_file):
        raise ge.CommandFailed(
            "run_recipe",
            "recipe file file does not exist",
            "Recipe file file not found [%s]" % (recipe_file),
            "Please check your paths!",
        )

    # parse the recipe file
    parameters = {}
    commands = []

    # open the recipe file
    if not steps:
        with open(recipe_file, "r", encoding="UTF-8") as file:
            try:
                recipe_data = yaml.load(file, Loader=yaml.FullLoader)
            except Exception as e:
                raise ge.CommandFailed("run_recipe", "Cannot parse the recipe file")

        # get the recipe
        if "recipes" not in recipe_data:
            raise ge.CommandFailed("run_recipe", "Recipes not found in the recipe file")

        recipes = recipe_data["recipes"]

        if recipe not in recipes:
            raise ge.CommandFailed(
                "run_recipe", f"Recipe {recipe} not found in the recipe file"
            )

        recipe_dict = recipes[recipe]

        # global parameters
        if "global_parameters" in recipe_data:
            for parameter, value in recipe_data["global_parameters"].items():
                parameters[parameter] = value

        # recipe parameters
        if "parameters" in recipe_dict:
            for parameter, value in recipe_dict["parameters"].items():
                parameters[parameter] = value
    else:
        # define recipe name
        recipe = "steps parameter"

        # create the commands dict
        recipe_dict = {}
        recipe_dict["commands"] = steps.split(",")

    # log location
    if logfolder is None:
        if "studyfolder" in parameters:
            logfolder = os.path.join(parameters["studyfolder"], "processing", "logs")
        elif "studyfolder" in eargs:
            logfolder = os.path.join(eargs["studyfolder"], "processing", "logs")
        elif "sessionsfolder" in parameters:
            logfolder = gc.deduceFolders(
                {"sessionsfolder": parameters["sessionsfolder"]}
            )["logfolder"]
        elif "sessionsfolder" in eargs:
            logfolder = gc.deduceFolders({"sessionsfolder": eargs["sessionsfolder"]})[
                "logfolder"
            ]

    # mustache injections to logfolder?
    if "{{" in logfolder and "}}" in logfolder:
        labels = _find_enclosed_substrings(logfolder)
        for label in labels:
            cleaned_label = label.replace("{", "").replace("}", "")
            os_label = cleaned_label[1:]
            if cleaned_label[0] == "$" and os_label in os.environ:
                logfolder = logfolder.replace(label, os.environ[os_label])
            else:
                raise ge.CommandFailed(
                    "run_recipe",
                    f"Cannot inject values marked with double curly braces in the recipe. Label [{label}] not found in system environment variables.",
                )

    runlogfolder = os.path.join(logfolder, "runlogs")
    comlogfolder = os.path.join(logfolder, "comlogs")

    # create folder if it does not exist
    if not os.path.isdir(runlogfolder):
        os.makedirs(runlogfolder)

    print(f"\n---> Saving the run_recipe runlog to: {runlogfolder}")

    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
    logname = os.path.join(runlogfolder, f"Log-run_recipe-{logstamp}.log")

    # run
    summary = "\n----==== RECIPE EXECUTION SUMMARY ====----"

    try:
        log = open(logname, "w", encoding="utf-8")
    except:
        raise ge.CommandFailed(
            "run_recipe",
            "Cannot open log",
            f"Unable to open log [{logname}]",
            "Please check the paths!",
        )

    print(
        "\n\n============================== RUN_RECIPE LOG ==============================\n",
        file=log,
    )

    summary += f"\n\nRecipe: {recipe}"

    print(f"---> Running commands from recipe: {recipe}")
    print(f"---> Running commands from recipe: {recipe}\n", file=log)

    # commands
    if "commands" not in recipe_dict:
        raise ge.CommandFailed(
            "run_recipe", f"Recipe {recipe} missing commands specification"
        )

    commands = recipe_dict["commands"]

    # XNAT initial setup
    # If running on XNAT, try and load checkpoint if supplied
    if os.environ.get("XNAT", "") == "yes":
        checkpoint_str = os.environ.get("XNAT_CHECKPOINT", "")
        print("Checkpoint Supplied: " + checkpoint_str, file=log)
        print("Checkpoint Supplied: " + checkpoint_str)

        if checkpoint_str == "":
            print("XNAT Checkpoint empty, skipping...", file=log)
            print("XNAT Checkpoint empty, skipping...")
        else:
            file_path, find_summary = xnat_find_checkpoint(checkpoint_str)
            print(find_summary, file=log)
            load_summary = xnat_load_checkpoint(file_path)
            print(load_summary, file=log)

    for com in commands:
        if isinstance(com, dict):
            command_name = list(com.keys())[0]
            command_parameters = list(com.values())[0]
        else:
            command_name = com
            command_parameters = {}

        # executing a custom script
        if command_name == "script":
            if "path" in command_parameters:
                script_path = command_parameters["path"]
                del command_parameters["path"]
            else:
                raise ge.CommandFailed(
                    "run_recipe",
                    "Script path not provided",
                    f"Script path not provided [{command_parameters}]",
                    "Please provide the path to the script!",
                )
            print(
                f"\n--------------------------------------------\n---> Running script: {script_path}"
            )
            print(
                f"\n--------------------------------------------\n---> Running script: {script_path}",
                file=log,
            )
            if not os.path.exists(script_path):
                raise ge.CommandFailed(
                    "run_recipe",
                    "Script not found",
                    f"Script not found [{script_path}]",
                    "Please check the script path!",
                )

            # log
            script_name = os.path.basename(script_path)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
            log_path = os.path.join(
                comlogfolder,
                f"tmp_{script_name}_{command_name}_{timestamp}.log",
            )

            # prep command
            if script_path.endswith(".sh"):
                command = ["bash", script_path]
            elif script_path.endswith(".py"):
                command = ["python", script_path]
            else:
                raise ge.CommandFailed(
                    "run_recipe",
                    "Script type not supported",
                    f"Script type not supported [{script_path}]",
                    "Please use .sh or .py scripts!",
                )

            # add parameters to the command
            for param, value in command_parameters.items():
                command.append(f"--{param}={value}")

            # create comlogfolder folder if needed
            if not os.path.isdir(comlogfolder):
                print(f"    ... creating log folder [{comlogfolder}]")
                print(f"    ... creating log folder [{comlogfolder}]", file=log)
                os.makedirs(comlogfolder)

            # run the command with subprocess Popen
            with open(log_path, "w", encoding="UTF-8") as log_file:
                process = subprocess.Popen(
                    command, stdout=log_file, stderr=subprocess.STDOUT
                )
                process.communicate()

            # Get the exit code
            exit_code = process.returncode

            if exit_code != 0:
                summary += f"\n - script {script_path} ... FAILED"
                error_log = log_path.replace("tmp_", "error_")
                print(f"    ... failed [{script_path}], see [{error_log}]")
                print(f"    ... failed [{script_path}], see [{error_log}]", file=log)
                os.rename(log_path, error_log)
                raise ge.CommandFailed(
                    "run_recipe",
                    "Script failed",
                    f"Script failed [{script_path}]",
                    "Please check the log for details!",
                )
            else:
                summary += f"\n - script {script_path} ... OK"
                done_log = log_path.replace("tmp_", "done_")
                print(f"    ... done [{script_path}], see [{done_log}]")
                print(f"    ... done [{script_path}], see [{done_log}]", file=log)
                os.rename(log_path, done_log)

        elif _is_qunex_command(command_name):
            # override params with those from eargs (passed because of parallelization on a higher level)
            if eargs is not None:
                # do not add parameter if it is flagged as removed
                for k in eargs:
                    if k in ["parsessions", "parelements"]:
                        if k in command_parameters:
                            command_parameters[k] = str(
                                min([int(e) for e in [eargs[k], command_parameters[k]]])
                            )
                    else:
                        command_parameters[k] = eargs[k]

            # append global and recipe parameters
            for parameter, value in parameters.items():
                if parameter not in command_parameters:
                    command_parameters[parameter] = value

            # remove parameters that are not allowed
            import general.commands as gcom

            if command_name in gcom.commands:
                allowed_parameters = list(gcom.commands.get(command_name)["args"])
                if any([e in allowed_parameters for e in ["sourcefolder", "folder"]]):
                    allowed_parameters += gcs.extra_parameters

                new_parameters = command_parameters.copy()
                for param in command_parameters.keys():
                    if param not in allowed_parameters:
                        del new_parameters[param]
                command_parameters = new_parameters

            # XNAT individual command prep, creates _in checkpoint
            if os.environ.get("XNAT", "") == "yes":
                print("Attemping XNAT specific setup...", file=log)
                possibles = globals().copy()
                possibles.update(locals())
                # XNAT helper functions for individual commands must be in format xnat_ + command_name
                xnat_command = possibles.get("xnat_" + command_name)
                if not xnat_command:
                    print("\n------------------------", file=log)
                    print(
                        "\nNo XNAT setup method detected for: "
                        + command_name
                        + ", continuing...",
                        file=log,
                    )
                    print("\n------------------------", file=log)
                else:
                    print(xnat_command(prep=True), file=log)
                print("Making checkpoint IN...", file=log)
                print("Making checkpoint IN...")
                xnat_make_checkpoint(
                    command_name + "_in",
                    tag=os.environ.get("XNAT_CHECKPOINT_TAG", "timestamp"),
                )

            # setup command
            command = ["qunex"]
            command.append(command_name)
            commandr = (
                "\n--------------------------------------------\n---> Running command:\n\n     qunex "
                + command_name
            )

            for param, value in command_parameters.items():
                # inject mustache marked values
                if (
                    isinstance(value, str)
                    and len(value) > 0
                    and "{{" in value
                    and "}}" in value
                ):
                    labels = _find_enclosed_substrings(value)
                    for label in labels:
                        cleaned_label = label.replace("{", "").replace("}", "")
                        os_label = cleaned_label[1:]
                        if cleaned_label[0] == "$" and os_label in os.environ:
                            value = value.replace(label, os.environ[os_label])
                        else:
                            raise ge.CommandFailed(
                                "run_recipe",
                                f"Cannot inject values marked with double curly braces in the recipe. Label [{label}] not found in system environment variables.",
                            )

                if param in flags:
                    command.append(f"--{param}")
                    commandr += f" \\\n          --{param}" % (param)
                else:
                    command.append(f"--{param}={value}")
                    commandr += f" \\\n          --{param}='{value}'"

            # warn if scheduler was used in the recipe file
            if "scheduler" in command_parameters:
                print(
                    f"\nWARNING: the scheduler parameter defined in the recipe file will be ignored. Scheduling needs to be defined at the command call level."
                )

            print(commandr)
            print(commandr, file=log)

            # run command
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0
            )

            # Poll process for new output until finished
            error = False
            logging = False

            for line in iter(process.stdout.readline, b""):
                line = line.decode("utf-8")
                print(line)
                if (
                    "ERROR in completing" in line
                    or "ERROR:" in line
                    or "failed with error" in line
                ):
                    print("", file=log)
                    error = True

                if "Final report" in line:
                    print("", file=log)
                    logging = True

                # print
                if logging or error:
                    print(line, end=" ", file=log)
                    log.flush()

            if error:
                summary += f"\n - command {command_name} ... FAILED"
                summary += "\n\n----------==== END SUMMARY ====----------"
                print(summary, file=log)
                print(
                    f"\n---> run_recipe not completed successfully: failed running command {command_name}",
                    file=log,
                )
                log.close()
                raise ge.CommandFailed(
                    "run_recipe",
                    "run_recipe command failed",
                    f"Command {command_name} inside recipe {recipe} failed",
                    "See error logs in the study folder for details",
                )
            else:
                summary += f"\n - command {command_name} ... OK"
                print(
                    f"---> Successful completion of the run_recipe command {command_name}\n"
                )

            # XNAT individual command cleanup, creates _out checkpoint
            if os.environ.get("XNAT", "") == "yes":
                print("Attempting Xnat specific cleanup...", file=log)
                if not xnat_command:
                    print("\n------------------------")
                    print(
                        "\nNo Xnat cleanup method detected for: "
                        + command_name
                        + ", continuing...",
                        file=log,
                    )
                    print("\n------------------------")
                else:
                    print(xnat_command(prep=False), file=log)
                print("Making checkpoint OUT...", file=log)
                print("Making checkpoint OUT...")
                xnat_make_checkpoint(
                    command_name + "_out",
                    tag=os.environ.get("XNAT_CHECKPOINT_TAG", "timestamp"),
                )

        else:
            print(f"\n---> ERROR: run_recipe failed, {command_name} is not known!")
            raise ge.CommandFailed(
                "run_recipe",
                "Unknown command",
                f"Unknown command [{command_name}]",
                "This is not a QuNex command or a custom script!",
            )

    summary += "\n\n----------==== END SUMMARY ====----------"

    print(summary, file=log)
    print("\n---> Successful completion of task: run_recipe", file=log)

    print("\n------------------------")
    print("---> Successful completion of run_recipe")
    print(summary)

    log.close()

    # hack copy the log from runlogs to comlogs as well
    comlog = logname.replace("runlogs", "comlogs")
    if not error:
        comlog = comlog.replace("Log-", "done_")
    else:
        comlog = comlog.replace("Log-", "error_")

    # copy logname to comlog
    shutil.copyfile(logname, comlog)


def _find_enclosed_substrings(input_string, start_delimiter="{{", end_delimiter="}}"):
    """
    Find all substrings enclosed by start and end delimiters in a string.
    """
    substrings = []
    start_index = 0

    while True:
        start_pos = input_string.find(start_delimiter, start_index)
        if start_pos == -1:
            break

        end_pos = input_string.find(end_delimiter, start_pos + len(start_delimiter))
        if end_pos == -1:
            break

        substrings.append(input_string[start_pos : (end_pos + len(end_delimiter))])
        start_index = end_pos + len(end_delimiter)

    return substrings


def strip_quotes(string):
    """
    A helper function for removing leading and trailing quotes in a string.
    """
    string = string.strip('"')
    string = string.strip("'")
    return string


def batch_tag2namekey(
    filename=None, sessionid=None, bolds=None, output="number", prefix="BOLD_"
):
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
    --output     ... Whether to output numbers ('number') or bold names
                        ('name'). In the latter case the name will be extracted
                        from the 'filename' specification, if provided in the
                        batch file, or '<prefix>[N]' if 'filename' is not
                        specified.
    --prefix     ... The default prefix to use if a filename is not specified
                        in the batch file.
    """

    if filename is None:
        raise ge.CommandError("batchTag2Num", "No batch file specified!")

    if sessionid is None:
        raise ge.CommandError("batchTag2Num", "No session id specified!")

    if bolds is None:
        raise ge.CommandError("batchTag2Num", "No bolds specified!")

    sessions, options = gc.get_sessions_list(filename, sessionids=sessionid)

    if not sessions:
        raise ge.CommandFailed(
            "batchTag2Num",
            "Session id not found",
            "Session id %s is not present in the batch file [%s]"
            % (sessionid, filename),
            "Please check your data!",
        )

    if len(sessions) > 1:
        raise ge.CommandFailed(
            "batchTag2Num",
            "More than one session id found",
            "More than one [%s] instance of session id [%s] is present in the batch file [%s]"
            % (len(sessions), sessionid, filename),
            "Please check your data!",
        )

    session = sessions[0]
    options["bolds"] = bolds

    bolds, _, _, _ = gpc.useOrSkipBOLD(session, options)

    boldlist = []
    for boldnumber, boldname, boldtask, boldinfo in bolds:
        if output == "name":
            if "filename" in boldinfo:
                boldlist.append(boldinfo["filename"])
            else:
                boldlist.append("%s%d" % (prefix, boldnumber))
        else:
            boldlist.append(str(boldnumber))

    print("BOLDS:%s" % (",".join(boldlist)))


def get_sessions_for_slurm_array(sessions, sessionids):
    """
    get_sessions_for_slurm_array \\
      --sessions=<a list of sessions, or path to the batch file)

    Returns the subset of sessions that will be processed

    INPUTS
    ======

    --sessions      A list of sessions or path to the batch file.
    --sessionids    A subset of sessions to filter out.
    """

    # get sessions
    slist, _ = gc.get_sessions_list(sessions, sessionids=sessionids)

    # print
    sarray = []
    for s in slist:
        sarray.append(s["id"])

    print(",".join(sarray))


def gather_behavior(
    sessionsfolder=".",
    sessions=None,
    filter=None,
    sourcefiles="behavior.txt",
    targetfile=None,
    overwrite="no",
    check="yes",
    report="yes",
):
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

    --batchfile       A path to a `batch.txt` file.

    --sessions        Either a string with pipe `|` or comma separated list of
                      sessions (sessions ids) to be processed (use of grep
                      patterns is possible), e.g. `"AP128,OP139,ER*"`, or
                      `*list` file with a list of session ids. [*]

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
        data = None

        with open(file, "r") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                elif header is None:
                    header = [e.strip() for e in line.split("\t")]
                elif data is None:
                    data = [e.strip() for e in line.split("\t")]

        ndata = len(data)
        nheader = len(header)
        if ndata != nheader:
            return "Number of header [%d] and data [%d] fields do not match!" % (
                nheader,
                ndata,
            )

        for n in range(ndata):
            if header[n] in sdata:
                if sdata[header[n]] != data[n]:
                    return (
                        "File [%s] has duplicate and nonmatching ['%s' vs '%s'] data for variable '%s'!"
                        % (file, data[n], sdata[header[n]], header[n])
                    )
            else:
                sdata[header[n]] = data[n]
                if header[n] not in keys:
                    keys.append(header[n])

    # --- Start it up

    print("Running gather_behavior\n======================")

    # --- check subjects folder

    sessionsfolder = os.path.abspath(sessionsfolder)

    if not os.path.exists(sessionsfolder):
        raise ge.CommandFailed(
            "gather_behavior",
            "Sessions folder does not exist",
            "The specified sessions folder does not exist [%s]" % (sessionsfolder),
            "Please check paths!",
        )

    # --- check target file

    if targetfile is None:
        targetfile = os.path.join(sessionsfolder, "inbox", "behavior", "behavior.txt")

    overwrite = overwrite.lower() == "yes"

    if os.path.exists(targetfile):
        if overwrite:
            try:
                os.remove(targetfile)
            except:
                raise ge.CommandFailed(
                    "gather_behavior",
                    "Could not remove target file",
                    "Existing object at the specified target location could not be deleted [%s]"
                    % (targetfile),
                    "Please check your paths and authorizations!",
                )
        else:
            raise ge.CommandFailed(
                "gather_behavior",
                "Target file exists",
                "The specified target file already exists [%s]" % (targetfile),
                "Please check your paths or set overwrite to 'yes'!",
            )

    # --- check sessions

    if sessions and sessions.lower() == "none":
        sessions = None

    if filter and filter.lower() == "none":
        filter = None

    report = report.lower() == "yes"

    # --- check sourcefiles

    sfiles = [e.strip() for e in re.split(r" *, *| *\| *| +", sourcefiles)]

    # --- check sessions

    if sessions is None:
        print(
            "---> WARNING: No sessions specified. The list will be generated for all sessions in the sessions folder!"
        )
        sessions = glob.glob(os.path.join(sessionsfolder, "*", "behavior"))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.get_sessions_list(
        sessions, filter=filter, verbose=False, sessionsfolder=sessionsfolder
    )

    if not sessions:
        raise ge.CommandFailed(
            "gather_behavior",
            "No session found",
            "No sessions found to process behavioral data from!",
            "Please check your data!",
        )

    # --- generate list entries

    processReport = {"ok": [], "missing": [], "error": []}
    data = {}
    keys = []

    for session in sessions:
        files = []
        for sfile in sfiles:
            files += glob.glob(
                os.path.join(sessionsfolder, session["id"], "behavior", sfile)
            )

        if not files:
            processReport["missing"].append(session["id"])
            continue

        sdata = {}
        for file in files:
            error = addData(file, sdata, keys)
            if error:
                processReport["error"].append((session["id"], error))
                break

        if error:
            continue

        processReport["ok"].append(session["id"])
        data[session["id"]] = dict(sdata)

    # --- save group data

    try:
        fout = open(targetfile, "w")
    except:
        raise ge.CommandFailed(
            "gather_behavior",
            "Could not create target file",
            "Target file could not be created at the specified location [%s]"
            % (targetfile),
            "Please check your paths and authorizations!",
        )

    header = ["session id"] + keys
    if report:
        print(
            "# Data compiled using gather_behavior on %s" % (datetime.today()),
            file=fout,
        )
    print("\t".join(header), file=fout)

    for sessionid in processReport["ok"]:
        sdata = data[sessionid]
        line = [sessionid]
        for key in keys:
            if key in sdata:
                line.append(sdata[key])
            else:
                line.append("NA")
        print("\t".join(line), file=fout)

    # --- print report

    reportit = [
        ("ok", "Successfully processed sessions:"),
        ("missing", "Sessions for which no behavioral data was found"),
        ("error", "Sessions for which an error was encountered"),
    ]

    if any([processReport[status] for status, message in reportit]):
        print("---> Final report")
        for status, message in reportit:
            if processReport[status]:
                print("--->", message)
                if report and status != "ok":
                    print("#", message, file=fout)
                for info in processReport[status]:
                    if status == "error":
                        print("     %s [%s]" % info)
                        if report:
                            print("# -> %s: %s" % info, file=fout)
                    else:
                        print("     %s" % (info))
                        if report and status != "ok":
                            print("# -> %s" % (info), file=fout)

    fout.close()

    # --- exit

    if processReport["error"] or processReport["missing"]:
        if check.lower() == "yes":
            raise ge.CommandFailed(
                "gather_behavior",
                "Errors encountered",
                "Not all sessions processed successfully!",
                "Sessions with missing behavioral data: %d"
                % (len(processReport["missing"])),
                "Sessions with errors in processing: %d"
                % (len(processReport["error"])),
                "Please check your data!",
            )
        elif check.lower() == "warn":
            raise ge.CommandNull(
                "gather_behavior",
                "Errors encountered",
                "Not all sessions processed successfully!",
                "Sessions with missing behavioral data: %d"
                % (len(processReport["missing"])),
                "Sessions with errors in processing: %d"
                % (len(processReport["error"])),
                "Please check your data!",
            )

    if not processReport["ok"]:
        raise ge.CommandNull(
            "gather_behavior", "No files processed", "No valid data was found!"
        )


def pull_sequence_names(
    sessionsfolder=".",
    sessions=None,
    filter=None,
    sourcefiles="session.txt",
    targetfile=None,
    overwrite="no",
    check="yes",
    report="yes",
):
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

    --batchfile       A path to a `batch.txt` file.

    --sessions        Either a string with pipe `|` or comma separated list of
                      sessions (sessions ids) to be processed (use of grep
                      patterns is possible), e.g. "AP128,OP139,ER*", or
                      `*list` file with a list of session ids. [*]

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
        missingNames = []
        sequenceNames = []

        try:
            f = open(file, "r")
        except:
            return "Could not open %s for reading!" % (file)

        for line in f:
            if ":" in line:
                line = [e.strip() for e in line.split(":")]
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
            return "The following sequences had no names: %s!" % (
                ", ".join(missingNames)
            )

    # --- Start it up

    print("Running pull_sequence_names\n=========================")

    # --- check sessions folder

    sessionsfolder = os.path.abspath(sessionsfolder)

    if not os.path.exists(sessionsfolder):
        raise ge.CommandFailed(
            "pull_sequence_names",
            "Sessions folder does not exist",
            "The specified sessions folder does not exist [%s]" % (sessionsfolder),
            "Please check paths!",
        )

    # --- check target file

    if targetfile is None:
        targetfile = os.path.join(sessionsfolder, "inbox", "MR", "sequences.txt")

    overwrite = overwrite.lower() == "yes"

    if os.path.exists(targetfile):
        if overwrite:
            try:
                os.remove(targetfile)
            except:
                raise ge.CommandFailed(
                    "pull_sequence_names",
                    "Could not remove target file",
                    "Existing object at the specified target location could not be deleted [%s]"
                    % (targetfile),
                    "Please check your paths and authorizations!",
                )
        else:
            raise ge.CommandFailed(
                "pull_sequence_names",
                "Target file exists",
                "The specified target file already exists [%s]" % (targetfile),
                "Please check your paths or set overwrite to 'yes'!",
            )

    # --- check sessions

    if sessions and sessions.lower() == "none":
        sessions = None

    if filter and filter.lower() == "none":
        filter = None

    report = report.lower() == "yes"

    # --- check sourcefiles

    sfiles = [e.strip() for e in re.split(r" *, *| *\| *| +", sourcefiles)]

    # --- check sessions

    if sessions is None:
        print(
            "---> WARNING: No sessions specified. The list will be generated for all sessions in the sessions folder!"
        )
        sessions = glob.glob(os.path.join(sessionsfolder, "*", "behavior"))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.get_sessions_list(
        sessions, filter=filter, verbose=False, sessionsfolder=sessionsfolder
    )

    if not sessions:
        raise ge.CommandFailed(
            "pull_sequence_names",
            "No session found",
            "No sessions found to process neuroimaging data from!",
            "Please check your data!",
        )

    # --- generate list entries

    processReport = {"ok": [], "missing": [], "error": []}
    data = []

    for session in sessions:
        files = []
        for sfile in sfiles:
            files += glob.glob(os.path.join(sessionsfolder, session["id"], sfile))

        if not files:
            processReport["missing"].append(session["id"])
            continue

        for file in files:
            error = addData(file, data)
            if error:
                processReport["error"].append((session["id"], error))
                break

        if error:
            continue

        processReport["ok"].append(session["id"])

    # --- save group data

    try:
        fout = open(targetfile, "w")
    except:
        raise ge.CommandFailed(
            "pull_sequence_names",
            "Could not create target file",
            "Target file could not be created at the specified location [%s]"
            % (targetfile),
            "Please check your paths and authorizations!",
        )

    if report:
        print(
            "# Data compiled using pull_sequence_names on %s" % (datetime.today()),
            file=fout,
        )

    data = sorted(set(data))
    for sname in data:
        print(sname, file=fout)

    # --- print report

    reportit = [
        ("ok", "Successfully processed sessions:"),
        ("missing", "Sessions for which no imaging data was found"),
        ("error", "Sessions for which an error was encountered"),
    ]

    if any([processReport[status] for status, message in reportit]):
        print("---> Final report")
        for status, message in reportit:
            if processReport[status]:
                print("--->", message)
                if report and status != "ok":
                    print("#", message, file=fout)
                for info in processReport[status]:
                    if status == "error":
                        print("     %s [%s]" % info)
                        if report:
                            print("# -> %s: %s" % info, file=fout)
                    else:
                        print("     %s" % (info))
                        if report and status != "ok":
                            print("# -> %s" % (info), file=fout)

    fout.close()

    # --- exit

    if processReport["error"] or processReport["missing"]:
        if check.lower() == "yes":
            raise ge.CommandFailed(
                "pull_sequence_names",
                "Errors encountered",
                "Not all sessions processed successfully!",
                "Sessions with missing imaging data: %d"
                % (len(processReport["missing"])),
                "Sessions with errors in processing: %d"
                % (len(processReport["error"])),
                "Please check your data!",
            )
        elif check.lower() == "warn":
            raise ge.CommandNull(
                "pull_sequence_names",
                "Errors encountered",
                "Not all sessions processed successfully!",
                "Sessions with missing imaging data: %d"
                % (len(processReport["missing"])),
                "Sessions with errors in processing: %d"
                % (len(processReport["error"])),
                "Please check your data!",
            )

    if not processReport["ok"]:
        raise ge.CommandNull(
            "pull_sequence_names", "No files processed", "No valid data was found!"
        )


def exportPrep(commandName, sessionsfolder, mapto, mapaction, mapexclude):
    """
    Prepares variables for data export.
    """
    if os.path.exists(sessionsfolder):
        sessionsfolder = os.path.abspath(sessionsfolder)
    else:
        raise ge.CommandFailed(
            commandName,
            "Sessions folder does not exist",
            "The specified sessions folder does not exist [%s]" % (sessionsfolder),
            "Please check paths!",
        )

    if mapto:
        mapto = os.path.abspath(mapto)
    else:
        raise ge.CommandFailed(
            commandName,
            "Target not specified",
            "To execute the specified mapping `mapto` parameter has to be specified!",
            "Please check your command call!",
        )

    if mapaction not in ["link", "copy", "move"]:
        raise ge.CommandFailed(
            commandName,
            "Invalid action",
            "The action specified is not valid!",
            "Please specify a valid action!",
        )

    # -- prepare exclusion
    if mapexclude:
        patterns = [e.strip() for e in re.split(r", *", mapexclude)]
        mapexclude = []
        for e in patterns:
            try:
                mapexclude.append(re.compile(e))
            except:
                raise ge.CommandFailed(
                    commandName,
                    "Invalid exclusion",
                    "Could not parse the exclusion regular expression: '%s'!" % (e),
                    "Please check mapexclude parameter!",
                )

    return sessionsfolder, mapto, mapexclude


def create_session_info(
    sessions=None,
    pipelines="hcp",
    sessionsfolder=".",
    sourcefile="session.txt",
    targetfile=None,
    mapping=None,
    filter=None,
    overwrite="no",
):
    """
    ``create_session_info sessions=<sessions specification> [pipelines=hcp] [sessionsfolder=.] [sourcefile=session.txt] [targetfile=session_<pipeline>.txt] [mapping=specs/<pipeline>_mapping.txt] [filter=None] [overwrite=no]``

    Creates session.txt files that hold the information necessary for correct
    mapping to a folder structure supporting specific pipeline processing.

    Parameters:
        --batchfile (str, default ''):
            Path to a batch file.

        --sessions (str, default '*'):
            Either an explicit list (space, comma or pipe separated) of sessions
            to process or the path to a list file with sessions to process. If
            left unspecified, '*' will be used and all folders within sessions'
            folders will be processed.

        --pipelines (str, default 'hcp'):
            Specify a comma separated list of pipelines for which the session
            info will be prepared.

        --sessionsfolder (str, default '.'):
            The directory that holds sessions' folders.

        --sourcefile (str, default 'session.txt'):
            The "source" session.txt file.

        --targetfile (str, default session_<pipeline>.txt):
            The "target" session.txt file.

        --mapping (str, default specs/<pipeline>_mapping.txt):
            The path to the text file describing the mapping.

        --filter (str, default None):
            An optional "key:value|key:value" string used as a filter if a batch
            file is used. Only sessions for which all the key:value pairs are
            true will be processed. All the sessions will be processed if no
            filter is provided.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

    Notes:
        If an explicit list of parameters is provided, each element is treated
        as a glob pattern and the command will process all matching session ids.

        The create_session_info command is used to prepare session.txt files so
        that they hold the information necessary for correct mapping to a folder
        structure supporting specific pipeline preprocessing.

        For all the sessions specified, the command checks for the presence of
        specified source file (sourcefile). If the source file is found, each
        sequence name is checked against the source specified in the mapping
        file (mapping), and the specified label is aded. The results are then
        saved to the specified target file (targetfile). The resulting session
        information files will have `"<pipeline>ready: true"` key-value pair
        added.

        Mapping specification:
            The mapping file specifies the mapping between original sequence
            names and the desired pipeline labels. There are no limits to the
            number of mappings specified. Each mapping is to be specified in a
            single line in a form::

                <original_sequence_name>  => <user_specified_label>

            or::

                <sequence number> => <user_specified_label>

            BOLD files should be given a compound label after the => separator::

                <original_sequence_name>  => bold:<user_specified_label>

            as this allows for flexible labeling of distinct BOLD runs based on
            their content. Here the 'bold' part denotes that it is a bold file
            and the <user_speficied_label> allows for flexibility in naming.
            create_session_info will automatically number bold images in a
            sequential order, starting with 1.

            Any empty lines, lines starting with #, and lines without the
            "map to" => characters in the mapping file will be ignored. In the
            target file, images with names that do not match any of the
            specified mappings will be given empty labels. When both sequence
            number and sequence name match, sequence number will have priority.

            If multiple mappings are specified for fieldmap magnitude images
            only the last one will be used. To use two fieldmap magnitude images
            fm tags must be explicitly specified in the mapping file, e.g::

                fieldmap_magnitude1  => FM-Magnitude: fm(1)
                fieldmap_magnitude2  => FM-Magnitude: fm(1)

        Example mapping file:
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

    Examples:
        Specify the session folder for a given study to automatically loop over
        the entire folder::

            qunex create_session_info \\
                --sessions="*" \\
                --sessionsfolder=<study_folder>/sessions

        Define source and target session parameter files and mapping file. In
        this example the --sourcefile flag points to the original session
        information file, --targetfile points to the session information file to
        generate, and --mapping points to a generic mapping file::

            qunex create_session_info \\
                --sessionsfolder=/<study_folder>/sessions \\
                --sourcefile=<original_session_information_file> \\
                --targetfile=<hcp_session_information_file> \\
                --mapping=<generic_mapping_file>

        Two additional examples::

            qunex create_session_info \\
                --sessions="OP*|AP*" \\
                --sessionsfolder=session \\
                --mapping=session/hcp_mapping.txt

        ::

            qunex create_session_info \\
                --sessions="processing/batch_new.txt" \\
                --sessionsfolder=session \\
                --mapping=session/hcp_mapping.txt

    """

    print("Running create_session_info\n===================")

    # get all pipelines
    pipelines = pipelines.split(",")

    # loop over them
    for pipeline in pipelines:
        if pipeline not in ["hcp", "mice"]:
            raise ge.CommandFailed(
                "create_session_info",
                "Invalid pipeline type!",
                "Only hcp and mice mapping are currently supported",
            )

        if sessions is None:
            sessions = "*"

        if mapping is None:
            mapping = os.path.join(sessionsfolder, "specs", "%s_mapping.txt" % pipeline)

        if targetfile is None:
            targetfile = "session_%s.txt" % pipeline

        # -- get mapping ready
        if not os.path.exists(mapping):
            raise ge.CommandFailed(
                "create_session_info",
                "No pipeline mapping file",
                "The expected pipeline mapping file does not exist!",
                "Please check the specified path [%s]" % (mapping),
            )

        print(" ... Reading pipeline mapping from %s" % (mapping))

        try:
            mapping_rules = parser.read_mapping_file(mapping)
        except ge.SpecFileSyntaxError as e:
            raise ge.CommandFailed(
                "create_session_info",
                "Invalid mapping file.",
                "Please check the specified file [{}].".format(mapping),
                "Syntax error: {}".format(e.error),
            )

        # -- get list of session folders
        sessions, _ = gc.get_sessions_list(sessions, filter=filter, verbose=False)

        sfolders = []
        for session in sessions:
            newSet = glob.glob(os.path.join(sessionsfolder, session["id"]))
            if not newSet:
                print(
                    "WARNING: No folders found that match %s. Please check your data!"
                    % (os.path.join(sessionsfolder, session["id"]))
                )
            sfolders += newSet

        # -- check if we have any
        if not sfolders:
            raise ge.CommandFailed(
                "create_session_info",
                "No sessions found to process",
                "No sessions were found to process!",
                "Please check the data and sessions parameter!",
            )

        # -- loop through sessions folders
        report = {
            "missing source": [],
            "pre-existing target": [],
            "pre-processed source": [],
            "processed": [],
            "error": [],
        }

        for sfolder in sfolders:
            ssfile = os.path.join(sfolder, sourcefile)
            stfile = os.path.join(sfolder, targetfile)

            if not os.path.exists(ssfile):
                if os.path.basename(sfolder) not in ["archive", "specs", "QC", "inbox"]:
                    report["missing source"].append(sfolder)
                continue
            print(" ... Processing folder %s" % (sfolder))

            if os.path.exists(stfile) and overwrite != "yes":
                print("  ... Target file already exists, skipping! [%s]" % (stfile))
                report["pre-existing target"].append(sfolder)
                continue

            try:
                src_session = parser.read_generic_session_file(ssfile)

                if "hcp" in src_session["pipeline_ready"]:
                    print("  ... %s already pipeline ready" % (sourcefile))
                    if sourcefile != targetfile:
                        shutil.copyfile(sourcefile, targetfile)
                    report["pre-processed source"].append(sfolder)

                tgt_session = _process_pipeline_hcp_mapping(src_session, mapping_rules)

                output_lines = _serialize_session(tgt_session)

                print(" ... writing %s" % (targetfile))
                fout = open(stfile, "w")

                # qunex header
                gc.print_qunex_header(file=fout)
                print("#", file=fout)

                for line in output_lines:
                    print(line, file=fout)
                report["processed"].append(sfolder)

            except e:  # session file syntax error, conflicting rules
                report["error"].append(sfolder)
                print(traceback.format_exc())

    print("\n---> Final report")

    for status in [
        "pre-existing target",
        "pre-processed source",
        "processed",
        "missing source",
        "error",
    ]:
        if report[status]:
            print("---> sessions with %s file:" % (status))
            for session in report[status]:
                print("     -> %s " % (os.path.basename(session)))

    if report["missing source"] or report["error"]:
        raise ge.CommandFailed(
            "create_session_info",
            "Error",
            "Some sessions were missing source files {}!".format(
                report["missing source"]
            ),
            "Some sessions encountered errors {}!".format(report["error"]),
            "Please check the data and parameters!",
        )

    return


def _process_pipeline_hcp_mapping(src_session, mapping_rules):
    """Apply mapping rule and assign spin-echo and field-map pairs

    The algorithm for assign field-map requires two passes. It need to find
    correct se / fm pairs with a finite-state machine.
    """

    # construct mapped session object by making a shallow copy of the image
    # in the input session, and add the appropriate rule
    tgt_session = _apply_rules(src_session, mapping_rules)

    reserved_bold_numbers = _reserved_bold_numbers(mapping_rules)

    # assign numbers for bold and boldref images
    _assign_bold_number(tgt_session, reserved_bold_numbers)

    # find user defined se/fm in session or mapping file
    user_defined_field_map_fm = _find_user_defined_field_maps(tgt_session, "fm")
    user_defined_field_map_se = _find_user_defined_field_maps(tgt_session, "se")

    # skip this step when there are user defined entries.
    # execute FSM to identify proper se/fm pairs
    if len(user_defined_field_map_fm) > 0 or len(user_defined_field_map_se) > 0:
        field_map_fm = user_defined_field_map_fm
        field_map_se = user_defined_field_map_se
    else:
        field_map_fm = _find_field_maps(tgt_session, "fm")
        field_map_se = _find_field_maps(tgt_session, "se")

    # assign se/fm number only proper SE/FM pairs will be assigned with proper
    # HCP image type tag
    if len(field_map_fm) != 0:
        _assign_field_maps(tgt_session, field_map_fm, "fm")

    if len(field_map_se) != 0:
        _assign_field_maps(tgt_session, field_map_se, "se")

    # All remaining hcp image type tags can be assigned now
    # every thing except bold/boldref/se/fm
    _assign_remaining_image_type(tgt_session)

    tgt_session["pipeline_ready"].append("hcp")

    return tgt_session


def _apply_rules(src_session, mapping_rules):
    """Apply mapping rules for each image

    A mapping rule will be attached to images if exists
    A mapping rule identified by image numbers always takes precedence

    Note:
    src_session object should not be used after this function
    """
    tgt_session = {
        "session": src_session["session"],
        "subject": src_session["subject"],
        "paths": src_session["paths"],
        "pipeline_ready": src_session["pipeline_ready"],
        "images": {},
        "custom_tags": src_session["custom_tags"],
    }

    grp_img_num_rule = mapping_rules["group_rules"]["image_number"]
    grp_name_rule = mapping_rules["group_rules"]["name"]

    for img_num, img_info in src_session["images"].items():
        # evaluate session specific rules
        # evaluate group specific rules
        img_name = img_info["series_description"]
        rule = {"additional_tags": []}
        # rules defined using image number takes precedence
        if img_num in grp_img_num_rule:
            rule = grp_img_num_rule[img_num]
        elif img_name in grp_name_rule:
            rule = grp_name_rule[img_name]

        tgt_session["images"][img_num] = _apply_image_rule(img_info, rule)

    return tgt_session


def _apply_image_rule(img_info, rule):
    """Construct new_image_info based on rule"""

    # special tags that are parsed but not handled by special handlers
    pass_through_tags = ["phenc", "bold_num"]

    new_img_info = {
        "image_number": img_info["image_number"],
        "raw_image_number": img_info["raw_image_number"],
        "applied_rule": rule,
        "additional_tags": [img_info["series_description"]]
        + img_info["additional_tags"]
        + rule["additional_tags"],
    }
    if "se" in img_info:
        new_img_info["se"] = img_info["se"]
    if "fm" in img_info:
        new_img_info["fm"] = img_info["fm"]
    for i in pass_through_tags:
        if i in img_info and i in rule:
            raise ge.SpecFileSyntaxError(
                error=f"""Multiple definitions of tag {i} for image {img_info["image_number"]}"""
            )

        if i in img_info:
            new_img_info[i] = img_info[i]

        if i in rule:
            new_img_info[i] = rule[i]

    return new_img_info


def _reserved_bold_numbers(mapping_rules):
    """Returns the set of all bold numbers used by bold_num tag"""
    bold_nums = set()
    grp_img_num_rules = mapping_rules["group_rules"]["image_number"]
    grp_img_name_rules = mapping_rules["group_rules"]["name"]
    for rule in itertools.chain(
        grp_img_num_rules.values(), grp_img_name_rules.values()
    ):
        image_type = rule.get("hcp_image_type")
        if image_type is None:
            continue
        if image_type[0] == "bold":
            bold_num = rule.get("bold_num")
            if bold_num is not None:
                bold_nums.add(bold_num)
    return bold_nums


def _assign_bold_number(tgt_session, reserved_bold_numbers):
    """
    bold numbers are assigned sequentially, consecutively by default
    Currently, this function does not respect the bold_num hint in the mapping file
    """
    images = tgt_session["images"]
    image_numbers = list(sorted(images.keys()))
    bold_pairs = []
    IDLE_STATE = 0
    FOUND_BOLD_REF = 1
    state = IDLE_STATE
    prev_boldref_image_number = None
    for i in image_numbers:
        image = images[i]
        hcp_image_type = image["applied_rule"].get("hcp_image_type")
        if hcp_image_type is None:
            continue

        # when a ref image is found save it and wait to pair it with a bold img
        if hcp_image_type[0] == "boldref":
            # if it has manual numbering do not link it to any other bold image
            bold_num = image.get("bold_num")
            if bold_num is not None:
                bold_pairs.append((i,))
                continue
            if state == IDLE_STATE:
                prev_boldref_image_number = i
                state = FOUND_BOLD_REF
            elif state == FOUND_BOLD_REF:
                bold_pairs.append((prev_boldref_image_number,))
                prev_boldref_image_number = i
                # keep state - state = FOUND_BOLD_REF
        elif hcp_image_type[0] == "bold":
            if state == IDLE_STATE:
                bold_pairs.append((i,))
                # keep state - state = IDLE_STATE
            elif state == FOUND_BOLD_REF:
                bold_pairs.append((prev_boldref_image_number, i))
                prev_boldref_image_number = None
                state = IDLE_STATE
        else:
            continue

    if state == FOUND_BOLD_REF:
        bold_pairs.append((prev_boldref_image_number,))
        prev_boldref_image_number = None

    used_bold_num = set()
    used_boldref_num = set()
    remaining_pairs = []

    for pair in bold_pairs:
        custom_bold_num = None
        custom_boldref_num = None
        for e in pair:
            image = images[e]
            hcp_image_type = image["applied_rule"].get("hcp_image_type")
            if hcp_image_type[0] == "bold":
                bn = image.get("bold_num")
                if bn is not None:
                    custom_bold_num = bn

            if hcp_image_type[0] == "boldref":
                bn = image.get("bold_num")
                if bn is not None:
                    custom_boldref_num = bn

        if custom_bold_num is not None:
            if custom_bold_num in used_bold_num:
                raise ge.CommandError(
                    "create_session_info",
                    "Custom bold number conflict",
                    "cannot apply the same bold number to multiple bold images",
                )
            used_bold_num.add(custom_bold_num)
            for e in pair:
                image = images[e]
                hcp_image_type = image["applied_rule"].get("hcp_image_type")
                image["hcp_image_type"] = (
                    hcp_image_type[0],
                    custom_bold_num,
                    hcp_image_type[2],
                )

        if custom_boldref_num is not None:
            if custom_boldref_num in used_boldref_num:
                raise ge.CommandError(
                    "create_session_info",
                    "Custom bold number conflict",
                    "cannot apply the same bold number to multiple boldref images",
                )
            used_boldref_num.add(custom_boldref_num)
            for e in pair:
                image = images[e]
                hcp_image_type = image["applied_rule"].get("hcp_image_type")
                image["hcp_image_type"] = (
                    hcp_image_type[0],
                    custom_boldref_num,
                    hcp_image_type[2],
                )

        if custom_bold_num is None and custom_boldref_num is None:
            remaining_pairs.append(pair)

    # exclude bold numbers previously used and reserved globally
    used_bold_num = used_bold_num | reserved_bold_numbers
    bold_num = 1
    for pair in remaining_pairs:
        while bold_num in used_bold_num:
            bold_num += 1
        used_bold_num.add(bold_num)
        for e in pair:
            image = images[e]
            hcp_image_type = image["applied_rule"].get("hcp_image_type")
            image["hcp_image_type"] = (hcp_image_type[0], bold_num, hcp_image_type[2])


def _find_user_defined_field_maps(tgt_session, field_map_type):
    """
    Find user-defined spin-echo / field map numbers.

    User could define se/fm in mapping or session file. Here we only record
    se/fm numbers defined on actual field map images. The output of this function
    is used to decide whether we will run the auto-assign FSM.
    """

    user_defined = {}

    for img_num, img_info in tgt_session["images"].items():
        rule = img_info["applied_rule"]
        hcp_image_type = rule.get("hcp_image_type")

        fm_num = img_info.get(field_map_type, rule.get(field_map_type))

        if fm_num is None or hcp_image_type is None:
            continue

        if (field_map_type == "fm" and hcp_image_type[0] in ("FM", "FM-GE")) or (
            field_map_type == "se" and hcp_image_type[0] == "SE-FM"
        ):
            fm_images = user_defined.get(fm_num, list())
            fm_images.append(img_num)

            user_defined[fm_num] = fm_images

    return user_defined


def _find_field_maps(tgt_session, field_map_type):
    """Using a finite state machine to identify field map pairs

    The FSM iterates over the list of images in reverse order, to preferentially
    identify the second and third image as a pair in this case AP (PA AP).

    Returns: A dictionary where the key is the field map number and the value is a tuple
             containing the image number of one or two images.
    """
    IDLE_STATE = 0
    LOOKING_FOR_PAIR_STATE = 1
    PHASE_MAGNITUDE_OPPOSITE_LUT = {"Phase": "Magnitude", "Magnitude": "Phase"}
    SPIN_ECHO_OPPOSITE_LUT = {"AP": "PA", "PA": "AP", "LR": "RL", "RL": "LR"}

    def get_fm_info(hcp_image_type):
        """
        Returns:
            is_field_map: depending on field_map_type
            current_dir: direction/type of the current image, None if FM-GE
            opposite_dir: opposite direction/type of the current image, None if FM-GE
        """
        if hcp_image_type is None:
            return False, None, None

        if field_map_type == "fm":
            if hcp_image_type[0] == "FM":
                cur = hcp_image_type[1]
                opp = PHASE_MAGNITUDE_OPPOSITE_LUT[cur]
                return True, cur, opp
            elif hcp_image_type[0] == "FM-GE":
                return True, None, None

        if field_map_type == "se" and hcp_image_type[0] == "SE-FM":
            cur = hcp_image_type[1]
            opp = SPIN_ECHO_OPPOSITE_LUT[cur]
            return True, cur, opp

        return False, None, None

    images = tgt_session["images"]
    image_numbers = list(sorted(images.keys(), reverse=True))
    found_fm = []
    state = IDLE_STATE
    pending_image = None
    looking_for_dir = None
    for inum in image_numbers:
        image = images[inum]
        rule = image.get("applied_rule")
        hcp_type = None
        if rule is not None:
            hcp_type = rule.get("hcp_image_type")
        is_field_map, current_dir, opposite_dir = get_fm_info(hcp_type)

        if state == IDLE_STATE:
            if is_field_map:
                if opposite_dir:
                    state = LOOKING_FOR_PAIR_STATE
                    pending_image = inum
                    looking_for_dir = opposite_dir
                else:
                    # FM-GE
                    found_fm.append((inum,))
                    state = IDLE_STATE
                    pending_image = None
                    looking_for_dir = None
            else:
                state = IDLE_STATE
                pending_image = None
                looking_for_dir = None
        elif state == LOOKING_FOR_PAIR_STATE:
            if is_field_map:
                if looking_for_dir == current_dir:
                    # record the pair iff the 2 consecutive images are a matching pair
                    found_fm.append((inum, pending_image))
                    state = IDLE_STATE
                    pending_image = None
                    looking_for_dir = None
                else:
                    print("WARNING: Incomplete pair detected")
                    if opposite_dir:
                        state = LOOKING_FOR_PAIR_STATE
                        pending_image = inum
                        looking_for_dir = opposite_dir
                    else:
                        # Found FM-GE
                        found_fm.append((inum,))
                        state = IDLE_STATE
                        pending_image = None
                        looking_for_dir = None
            else:
                # keep looking unless it is the end or the same direction of the pair
                if inum == image_numbers[-1] or opposite_dir:
                    print("WARNING: Incomplete pair detected")
                    state = IDLE_STATE
                    pending_image = None
                    looking_for_dir = None

    res = {}
    for idx, fm in enumerate(reversed(found_fm)):
        res[idx + 1] = fm
    return res


def _assign_field_maps(tgt_session, field_maps, field_map_type):
    """
    field_maps shall not be empty

    This function assigns field map hint to identified images and
    hcp image type for field maps.
    """
    if len(field_maps) == 0:
        return

    images = tgt_session["images"]
    image_numbers = list(sorted(images.keys()))
    fm_range = []  # starting index for each fm pair
    fm_number = []

    img_idx = 0
    # we iterate over field maps in the same order as they appear based on the first image
    for fm_hint, fm in sorted(field_maps.items(), key=lambda kv: min(kv[1])):
        for fm_img_num in fm:
            image = images[fm_img_num]
            rule = image["applied_rule"]
            hcp_image_type = rule.get("hcp_image_type")

            image["hcp_image_type"] = hcp_image_type
            image[field_map_type] = fm_hint

        while img_idx < len(image_numbers) and image_numbers[img_idx] < fm[0]:
            img_idx += 1

        fm_range.append(img_idx)
        fm_number.append(fm_hint)

    fm_range.append(len(image_numbers))
    # everything before the first field map will be assigned with the first fm
    fm_range[0] = 0

    for fm_idx, (st, ed) in enumerate(zip(fm_range[:-1], fm_range[1:])):
        fm_hint = fm_number[fm_idx]
        for i in range(st, ed):
            image = images[image_numbers[i]]
            rule = image["applied_rule"]
            hcp_image_type = rule.get("hcp_image_type")

            if hcp_image_type is None:
                continue
            elif (
                image.get(field_map_type) is not None
                or rule.get(field_map_type) is not None
            ):
                user_defined_sefm = image.get(field_map_type, rule.get(field_map_type))
                if user_defined_sefm not in fm_number:
                    raise ge.CommandError(
                        "create_session_info",
                        f"User specified spin-echo or field map number {field_map_type}({user_defined_sefm}) does not exist",
                    )
                image[field_map_type] = user_defined_sefm
            elif hcp_image_type[0] in ["T1w", "T2w", "DWI", "ASL", "bold", "boldref"]:
                image[field_map_type] = fm_hint


def _assign_remaining_image_type(tgt_session):
    """This function assigns hcp image tag for T1,T2w,DWI,ASL images

    bold/boldref should be assigned in `_assign_bold_number`
    se/fm that are used are assigned in `_assign_field_map`
    unused se/fm will be not be identified
    """
    images = tgt_session["images"]

    for _, image in images.items():
        rule = image["applied_rule"]
        hcp_image_type = rule.get("hcp_image_type")
        if hcp_image_type is not None and hcp_image_type[0] in [
            "T1w",
            "T2w",
            "FM-GE",
            "ASL",
            "mbPCASLhr",
            "PCASLhr",
            "TB1DAM",
            "TB1EPI",
            "TB1AFI",
            "TB1TFL",
            "TB1RFM",
            "TB1SRGE",
            "TB1map",
            "RB1COR",
            "RB1map",
        ]:
            image["hcp_image_type"] = hcp_image_type


def _serialize_session(tgt_session):
    """Encode mapped session as a list of strings"""
    lines = []

    if tgt_session.get("session") is None:
        raise ge.SpecFileSyntaxError(error="session id cannot be empty")
    lines.append("session: {}".format(tgt_session["session"]))

    if tgt_session.get("subject") is None:
        raise ge.SpecFileSyntaxError(error="subject id cannot be empty")
    lines.append("subject: {}".format(tgt_session["subject"]))

    lines.append("")

    for path_name, path in tgt_session["paths"].items():
        lines.append("{}: {}".format(path_name, path))

    lines.append("")

    for tag_key, tag_value in tgt_session["custom_tags"].items():
        lines.append("{}: {}".format(tag_key, tag_value))

    lines.append("")

    for pipeline in tgt_session["pipeline_ready"]:
        lines.append("{}ready: true".format(pipeline))

    lines.append("")

    for img_num in sorted(tgt_session["images"].keys()):
        image = tgt_session["images"][img_num]
        image_num_str = tgt_session["images"][img_num]["raw_image_number"]
        hcp_image_type = image.get("hcp_image_type")

        tags = []

        if hcp_image_type is None:
            tags.append("")
        elif hcp_image_type[0] in ["bold", "boldref"]:
            tags.append("{}{}:{}".format(*hcp_image_type))
        elif hcp_image_type[0] in ["SE-FM", "FM"]:
            tags.append("{}-{}".format(*hcp_image_type))
        elif hcp_image_type[0] == "DWI":
            tags.append("{}:{}".format(*hcp_image_type))
        elif hcp_image_type[0] == "RB1COR":
            tags.append("{}-{}".format(*hcp_image_type))
        elif hcp_image_type[0] == "TB1TFL":
            tags.append("{}-{}".format(*hcp_image_type))
        else:
            tags.append(hcp_image_type[0])

        # add additional tags
        tags.extend(image["additional_tags"])

        # add se, fm, bold_num at the end
        for k in ["se", "fm", "bold_num", "phenc"]:
            if k in image and image[k] is not None:
                tags.append("{}({})".format(k, image[k]))

        remaining_tags = ""
        if len(tags) > 1:
            # tag: str | (str, str)
            serialized_tags = []
            for t in tags[1:]:
                if type(t) is str:
                    serialized_tags.append(t)
                elif type(t) is tuple and len(t) == 2:
                    serialized_tags.append(f"{t[0]}({t[1]})")
                else:
                    # invalid tag format
                    raise Exception()
            remaining_tags = ":" + ": ".join(serialized_tags)

        lines.append("{:<4}:{:<16}{}".format(image_num_str, tags[0], remaining_tags))
    return lines


def xnat_run_cmd(cmd):
    """
    xnat_run_cmd

    A helper function called by xnat_ functions to run bash commands on XNAT

    Parameters:
        --cmd (str list):
            Bash command to run split into a list of strings.

    Returns:
        --summary (str):
            stdout of the run bash command plus other details to print to a log
    """
    cmdS = " ".join(cmd)
    summary = "\nRunning: " + cmdS
    cmdP = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0
    )
    summary += "\n          --- stdout start --- \n"
    for line in iter(cmdP.stdout.readline, b""):
        line = line.decode("utf-8")
        summary += "\n"
        summary += line
    summary += "\n          ---  stdout end  --- \n"
    print(summary)
    return summary


def xnat_make_checkpoint(step, tag="timestamp"):
    """
    xnat_make_checkpoint

    Creates a 'checkpoint' of the current build directory, called by run_recipe if running on XNAT

    Parameters:
        --step (str):
            Prefix of the checkpoint, usually the step plus either _in or _out. (eg. import_dicom_in). See Notes
        --tag (str):
            Suffix of the checkpoint, if 'timestamp' or 'xnat_id' then the current timestamp or XNAT_WORKFLOW_ID
            will be used. Otherwise, the supplied string will be used. Default: 'timestamp'

    Notes:
        The output file is in format step:tag.txt, to be input into xnat_load_checkpoint.

        A checkpoint is a .txt containing a new-line seperated list of filepaths. This is designed with
        XNAT in mind and makes use of environmental variables. This checkpoint is created in a
        directory called 'checkpoints' inside the sessions folder.

        There is also a special checkpoint type called 'all', which lists the archive instead of the build
        directory. When run at the start of run_recipe, it allows users to copy the entire archive into build.
    """
    if step == "all":
        files = glob.glob("/input/RESOURCES/qunex_study/**", recursive=True)
        for i in range(len(files)):
            files[i] = files[i].replace(
                "/input/RESOURCES/qunex_study/", os.environ["STUDY_FOLDER"]
            )
    else:
        files = glob.glob(os.environ["STUDY_FOLDER"] + "/**", recursive=True)

    if tag == "timestamp":
        suffix = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    elif tag == "xnat_id":
        suffix = os.environ.get("XNAT_WORKFLOW_ID", "XNAT")
    else:
        suffix = tag

    outPath = (
        os.environ["SESSIONS_FOLDER"] + "/checkpoints/" + step + ":" + suffix + ".txt"
    )
    with open(outPath, "w") as fp:
        fp.write("\n".join(files))
    return


def xnat_find_checkpoint(checkpoint_str):
    """
    xnat_find_checkpoint

    Determines if a valid checkpoint exists for the input and finds it if it exists

    Parameters:
        --checkpoint_str (str):
            The checkpoint to load, valid input being checkpoint 'tag', 'step:tag', or 'all'. See Notes.

    Returns:
        --checkpoint_path (str):
            The full path to the appropriate checkpoint if found, otherwise raises an error.
        --summary (str):
            Info used for logging plus bash stdout

    Notes:
        Only the tag needs to be supplied, the step is optional for more specificity. The tag can either be the
        exact tag used by a checkpoint, the String 'latest'

        If the step is not supplied and there are multiple checkpoints with the same tag, it will provide the
        latest checkpoint.

        If 'latest' is supplied without a step, it will provide the path to the most recently generated
        checkpoint. When combined with a step, it will locate the most recently generated checkpoint for that
        step.

        If 'all' is supplied without a step or tag, then it will create a new checkpoint of the archive/input
        directory and provide the path to this new file. This can effectively be used to load the entire archive,
        though it is still subject to the filters supplied in xnat_load_checkpoint
    """
    summary = "Starting xnat_find_checkpoint..."

    c_path = "/input/RESOURCES/qunex_study/sessions/checkpoints/"

    # split into step and tag
    checkpoint = checkpoint_str.split(":")
    if len(checkpoint) == 1:
        if checkpoint[0].lower() == "all":
            xnat_make_checkpoint("all")
            step = "all"
            tag = "latest"
            c_path = os.environ["SESSIONS_FOLDER"] + "/checkpoints/"
        elif checkpoint[0].lower() == "latest":
            step = ""
            tag = "latest"
        else:
            step = "*" + checkpoint[0]
            tag = "latest"

    elif len(checkpoint) == 2:
        step = checkpoint[0]
        tag = checkpoint[1]

    else:
        summary += "\nXNAT Checkpoint invalid, please supply one of ['', 'command':'timestamp', 'command':latest, latest]"
        print(
            "XNAT Checkpoint invalid, please supply one of ['', 'command':'timestamp', 'command':latest, latest]"
        )
        raise ge.CommandFailed(
            "run_recipe",
            "Cannot open checkpoint",
            f"Invalid Checkpoint supplied [{checkpoint_str}]",
            "Checkpoint must be one of ['', 'command'_'in/out':'timestamp', 'command'_'in/out':latest, latest]",
        )

    checkpoints = glob.glob(c_path + step + "*.txt")

    if len(checkpoints) == 0:
        summary += (
            "\nXNAT Checkpoint supplied, but no checkpoints found in: "
            + c_path
            + " for step: "
            + step
        )
        print(
            "XNAT Checkpoint supplied, but no checkpoints found in: "
            + c_path
            + " for step: "
            + step
        )
        raise ge.CommandFailed(
            "run_recipe",
            "No checkpoint found",
            f"Invalid Checkpoint supplied [{checkpoint_str}]",
            "Checkpoint not found",
        )

    if tag == "latest":
        print("Getting latest XNAT Checkpoint for step: " + step)
        summary += "Getting latest XNAT Checkpoint for step: " + step
        file_name = max(checkpoints, key=os.path.getctime)
    else:
        file_name = c_path + step + ":" + tag
        print("\nSearching for checkpoint: " + file_name)
        summary += "\nSearching for checkpoint: " + file_name
        if file_name not in checkpoints:
            summary += (
                "\nERROR: XNAT Checkpoint tag supplied but not found! Check your paths!"
            )
            summary += "\nFound the following checkpoints for step: " + step
            print(
                "ERROR: XNAT Checkpoint tag supplied but not found! Check your paths!"
            )
            print("Found the following checkpoints for step: " + step)
            summary += "\n".join(checkpoints)
            print("\n".join(checkpoints))
            raise ge.CommandFailed(
                "run_recipe",
                "Cannot open checkpoint",
                f"Unable to find checkpoint [{file_name}]",
                "Please check your paths!",
            )
        else:
            summary += "\nXNAT Checkpoint found!"
            print("XNAT Checkpoint found!")

    summary += "\nPrepared Checkpoint: " + file_name
    print("Prepared Checkpoint: " + file_name)
    return file_name, summary


def xnat_load_checkpoint(file_path):
    """
    xnat_load_checkpoint

    Loads a valid checkpoint and sets the build directory to that state via rsync

    Parameters:
        --file_path (str):
            Exact path to the checkpoint to load

    Returns:
        --summary (str):
            Info used for logging plus bash stdout from rsync

    Notes:
        For XNAT, there are a number of environmental variables that can be set to control what gets copied. Logs
        are always filtered out.

        With XNAT_DEFAULT_FILTERS=yes (default 'yes), the default filters will be applied for certain steps to
        avoid copying unneccesary files. At the moment, this affects the raw nifti files (/nii/), and hcp files
        (/hcp/). Set to 'no' to disable these filters.

        With XNAT_CUSTOM_FILTERS={filters} (default 'no'), users can provide custom filters to prevent files
        they deem unneccesary from copying into build, {filters} being comma seperated substrings. If a filepath
        contains one of these substrings, it will not  be copied. If 'no' is provided, this will be ignored.

        With XNAT_CUSTOM_RSYNC={filepaths} (default 'no'), users can provide files they want copied from archive
        that may not be present in the checkpoint, {filepaths} being comma seperated substrings. These
        substrings are the relative paths to the files from the Study Folder (where Sessions is located). This
        is used directly by the rsync command so wildcards like '*' and '**' are accepted. The same limitations
        that affect rsync also affect this command, however.
    """

    summary = "Starting xnat_load_checkpoint..."

    cmd = [
        "rsync",
        "-avzh",
        "/input/RESOURCES/qunex_study/",
        os.environ["STUDY_FOLDER"],
    ]
    try:
        files = [line.rstrip() for line in open(file_path)]
    except:
        raise ge.CommandFailed(
            "run_recipe",
            "Cannot open checkpoint",
            f"Unable to open checkpoint [{file_path}]",
            "Please check your paths!",
        )

    # Filters out logs
    # Dicoms are deleted Xnat, so /dicom/ only contains logs
    files = list(filter(lambda n: "/dicom/" not in n, files))
    files = list(filter(lambda n: "/checkpoints/" not in n, files))
    files = list(filter(lambda n: "/processing/logs" not in n, files))

    use_filter = os.environ.get("XNAT_DEFAULT_FILTERS", "")

    if use_filter == "":
        use_filter = "yes"
        print("WARNING: XNAT_DEFAULT_FILTERS empty, setting to default: " + use_filter)
        summary += (
            "\nWARNING: XNAT_DEFAULT_FILTERS empty, setting to default: " + use_filter
        )

    if use_filter.lower() == "no":
        print("XNAT_DEFAULT_FILTERS set as 'no', skipping default filters...")
        summary += "\nXNAT_DEFAULT_FILTERS set as 'no', skipping default filters..."

    elif use_filter.lower() == "yes":
        print("XNAT_DEFAULT_FILTERS set as 'yes', filtering files now...")
        summary += "\nXNAT_DEFAULT_FILTERS set as 'yes', filtering files now..."

        if (
            "create_session_info" in file_path
            or "setup_hcp_in" in file_path
            or "export_hcp" in file_path
            or "run_qc_in" in file_path
        ):
            pass
        else:
            print("Filtering '/nii/' ...")
            summary += "\nFiltering '/nii/' ..."
            files = list(filter(lambda n: "/nii/" not in n, files))

        if (
            "hcp" in file_path or "run_qc" in file_path or "dwi" in file_path
        ) and "map_hcp_data_out" not in file_path:
            pass
        else:
            print("Filtering '/hcp/' ...")
            summary += "\nFiltering '/hcp/' ..."
            files = list(filter(lambda n: "/hcp/" not in n, files))

    else:
        print("XNAT_DEFAULT_FILTERS value: '" + use_filter + "' unrecognized!")
        print("XNAT_DEFAULT_FILTERS must be one of: ['yes', 'no', '']")
        summary += "\nXNAT_DEFAULT_FILTERS value: '" + use_filter + "' unrecognized!"
        summary += "\nXNAT_DEFAULT_FILTERS must be one of: ['yes', 'no', '']"

        raise ge.CommandFailed(
            "run_recipe",
            "Invalid XNAT_DEFAULT_FILTERS value",
            f"Invalid filter supplied '{use_filter}'",
            "XNAT_DEFAULT_FILTERS must be one of: ['yes', 'no', '']",
        )

    custom_filter = os.environ.get("XNAT_CUSTOM_FILTERS", "")

    if custom_filter != "" and custom_filter.lower() != "no":
        print(
            "Custom Filter detected! File paths containing these strings will not be loaded from the checkpoint"
        )
        print("XNAT_CUSTOM_FILTERS value: '" + custom_filter + "'")
        summary += "\nCustom Filter detected!"
        summary += "\nXNAT_CUSTOM_FILTERS value: '" + custom_filter + "'"
        filter_list = custom_filter.split(",")
        for to_filter in filter_list:
            print(f"Filtering '{to_filter}' ...")
            summary += f"\nFiltering '{to_filter}' ..."
            files = list(filter(lambda n: to_filter not in n, files))

    custom_rsync = os.environ.get("XNAT_CUSTOM_RSYNC", "")

    if custom_rsync != "" and custom_rsync.lower() != "no":
        print(
            "Custom Rsync detected! This will be loaded in addition to the checkpoint"
        )
        print("XNAT_CUSTOM_RSYNC value: '" + custom_rsync + "'")
        summary += (
            "Custom Rsync detected! This will be loaded in addition to the checkpoint"
        )
        summary += "XNAT_CUSTOM_RSYNC value: '" + custom_rsync + "'"
        rsync_list = custom_rsync.split(",")
        for to_rsync in rsync_list:
            print(f"Adding '{to_rsync}' ...")
            summary += f"\nAdding'{to_rsync}' ..."
            cmd.append("--include=" + to_rsync)

    for file in files:
        cmd.append("--include=" + file.replace(os.environ["STUDY_FOLDER"], ""))

    cmd.append("--exclude=*")

    summary += xnat_run_cmd(cmd)
    return summary


def xnat_import_dicom(prep=True):
    """
    xnat_import_dicom

    A helper function called by run_recipe to run import_dicom on XNAT

    Parameters:
        --prep (boolean):
            Whether to run prep or cleanup related code. Default: True

    Returns:
        --summary (str):
            stdout of the run bash commands plus other details to print to a log

    Notes:
        When run with prep=True, replaces map_raw_data from the old run_recipe, copying scans to the inbox
        folder (qunex hierarchy). Also copies the initial batch parameters from the project level.

        When run with prep=False, replaces the cleanup function from run_turnkey, removing unneeded dicoms and
        the inbox folder.
    """

    summary = "\n\n----==== XNAT IMPORT_DICOM EXECUTION SUMMARY ====----\n\n"
    summary += "\n Running with prep:" + str(prep)
    if prep:
        summary += "\nimport_dicom set up finished"

        summary += "\nCopying SCANS..."

        inPath = "/input/SCANS"
        outPath = os.path.join(
            os.environ["SESSIONS_FOLDER"], os.path.join(os.environ["LABEL"], "inbox")
        )
        cmd = ["rsync", "-avzh", inPath, outPath]
        summary += xnat_run_cmd(cmd)

    else:
        summary += "\n Removing dicoms..."
        # dicoms currently all gunzipped, update if that changes
        files = glob.glob(
            os.environ["SESSIONS_FOLDER"] + "/" + os.environ["LABEL"] + "/dicom/*.gz"
        )  #
        cmd = ["rm", "-f"] + files
        summary += xnat_run_cmd(cmd)

        summary += "\n Removing inbox folders..."
        inPath = os.environ["SESSIONS_FOLDER"] + "/" + os.environ["LABEL"] + "/inbox"
        cmd = ["rm", "-rf", inPath]
        summary += xnat_run_cmd(cmd)

    summary += "\n\n----==== XNAT IMPORT_DICOM EXECUTION END ====----\n\n"
    print(summary)
    return summary


def xnat_create_session_info(prep=True):
    """
    xnat_create_session_info

    A helper function called by run_recipe to run create_session_info on XNAT

    Parameters:
        --prep (boolean):
            Whether to run prep or cleanup related code. Default: True

    Returns:
        --summary (str):
            stdout of the run bash commands plus other details to print to a log

    Notes:
        When run with prep=True, it copies over the mapping from the project level

        When run with prep=False, does nothing
    """
    summary = "\n\n----==== XNAT CREATE_SESSION_INFO EXECUTION SUMMARY ====----\n\n"
    summary += "\n Running with prep:" + str(prep)
    if prep:
        summary += "\nGetting Mapping file from project..."

        inPath = (
            os.environ["XNAT_HOST"]
            + "/data/projects/"
            + os.environ["XNAT_PROJECT"]
            + "/resources/QUNEX_PROC/files/"
            + os.environ["SCAN_MAPPING_FILENAME"]
        )
        outPath = os.environ["MAPPING"]
        cmd = [
            "curl",
            "-k",
            "-u",
            os.environ["XNAT_USER"] + ":" + os.environ["XNAT_PASS"],
            "-X",
            "GET",
            inPath,
            "-o",
            outPath,
        ]
        summary += xnat_run_cmd(cmd)

    summary += "\n\n----==== XNAT CREATE_SESSION_INFO EXECUTION END ====----\n\n"
    print(summary)
    return summary


def xnat_create_batch(prep=True):
    """
    xnat_create_batch

    A helper function called by run_recipe to run create_batch on XNAT, in this case copying the batch parameters file

    Parameters:
        --prep (boolean):
            Whether to run prep or cleanup related code. Default: True

    Returns:
        --summary (str):
            stdout of the run bash commands plus other details to print to a log

    Notes:
        When run with prep=True, it copies over the mapping from the project level

        When run with prep=False, does nothing
    """
    summary = "\n\n----==== XNAT CREATE_BATCH EXECUTION SUMMARY ====----\n\n"
    summary += "\n Running with prep:" + str(prep)
    if prep:
        summary += "\nGetting Parameter file from project..."

        inPath = (
            os.environ["XNAT_HOST"]
            + "/data/projects/"
            + os.environ["XNAT_PROJECT"]
            + "/resources/QUNEX_PROC/files/"
            + os.environ["BATCH_PARAMETERS_FILENAME"]
        )
        outPath = os.environ["INITIAL_PARAMETERS"]
        cmd = [
            "curl",
            "-k",
            "-u",
            os.environ["XNAT_USER"] + ":" + os.environ["XNAT_PASS"],
            "-X",
            "GET",
            inPath,
            "-o",
            outPath,
        ]
        summary += xnat_run_cmd(cmd)

    summary += "\n\n----==== XNAT CREATE_BATCH EXECUTION END ====----\n\n"
    print(summary)
    return summary
