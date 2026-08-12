#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``utilities.py``

Miscellaneous utilities for file processing.
"""

# Created by Grega Repovs on 2017-09-17.
# Copyright (c) Grega Repovs and Jure Demsar. All rights reserved.

import errno
import getpass
import glob
import itertools
import os
import os.path
import re
import shutil
import subprocess
from datetime import datetime
import qx_utilities.general.process as gp
import qx_utilities.general.core as gc
import qx_utilities.processing.core as gpc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.filelock as fl
import qx_utilities.general.log as gl
import qx_utilities.general.parser as parser


parameter_template_header = """#  Parameters file
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
#  (... <description>) after the values for the parameters to be used.
#
"""


def manage_study(studyfolder=None, action="create", folders=None, verbose=False):
    """
    ``manage_study studyfolder=None action="create"``

    Create or check the base study folder structure.

    ..  qx_command:
        type: utility

    Parameters:
        --studyfolder (str):
            The location of the study folder.

        --action (str, default 'create'):
            Whether to create a new study folder ('create') or check an existing
            study folder ('check').

        --folders (str, default '$TOOLS/python/qx_utilities/templates/study_folders_default.txt'):
            Path to the file which defines the study folder structure.

        --verbose (bool, default False):
            Whether to print detailed output during processing.

    Notes:
        A helper function called by create_study and check_study that does the
        actual checking of the study folder and generating missing content.

    """

    # template folder
    niu_template_folder = os.environ["NIUTemplateFolder"]

    # default folders file
    if folders is None or folders == "legacy":
        folders = os.path.join(niu_template_folder, "study_folders_default.txt")
    else:
        # if not absolute path
        if not os.path.exists(folders):
            # check if in templates
            folders = os.path.join(niu_template_folder, folders)
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
            print("\n---> Creating study folder structure:")

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
            print("\n---> Preparing template files:")

        # ---> parameter template
        param_file = os.path.join(studyfolder, "sessions", "specs", "parameters.txt")
        if not os.path.exists(os.path.dirname(param_file)):
            try:
                f = os.open(param_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(f, bytes(gl.print_qunex_header(), encoding="utf8"))
                # os.write(f, bytes("# Generated by QuNex %s on %s\n" % (gc.get_qunex_version(), datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")), encoding="utf8"))
                os.write(f, bytes("#\n", encoding="utf8"))
                os.write(f, bytes((parameter_template_header + "\n"), encoding="utf8"))
                for line in gp.arglist:
                    if len(line) > 1:
                        os.write(f, bytes("# --" + line[0] + "\n", encoding="utf8"))
                    else:
                        os.write(f, bytes(line[0] + "\n", encoding="utf8"))

                os.close(f)
                if verbose:
                    print(" ... created parameters.txt file")

            except OSError as e:
                if e.errno == errno.EEXIST:
                    if verbose:
                        print(" ... parameters.txt file already exists")
                else:
                    errstr = os.strerror(e.errno)
                    raise ge.CommandFailed(
                        "manage_study",
                        "I/O error: %s" % (errstr),
                        "Parameters template file could not be created [%s]!"
                        % (param_file),
                        "Please check paths and permissions!",
                    )

        # ---> mapping example
        # get all files that match the pattern
        examples_folder = os.path.join(niu_template_folder, "templates")
        mapping_examples = glob.glob(examples_folder + "/*_mapping_example.txt")
        for src_file in mapping_examples:
            try:
                # extract filename only
                file_name = os.path.basename(src_file)
                # destination path and file
                map_file = os.path.join(studyfolder, file_name)
                dst_file = os.open(map_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                # read src
                src_content = open(src_file, "r").read()
                os.write(dst_file, bytes(src_content, encoding="utf8"))
                os.close(dst_file)
                if verbose:
                    print(" ... created %s file" % map_file)

            except OSError as e:
                if e.errno == errno.EEXIST:
                    if verbose:
                        print(" ... %s file already exists" % dst_file)
                else:
                    errstr = os.strerror(e.errno)
                    raise ge.CommandFailed(
                        "manage_study",
                        "I/O error: %s" % (errstr),
                        "Parameters template file could not be created [%s]!"
                        % (param_file),
                        "Please check paths and permissions!",
                    )

        # ---> markFile
        mark_file = os.path.join(studyfolder, ".qunexstudy")

        # ... map .mnapstudy to qunexstudy
        if os.path.exists(os.path.join(studyfolder, ".mnapstudy")):
            try:
                f = os.open(mark_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
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
                        ".qunexstudy file could not be created [%s]!" % (mark_file),
                        "Please check paths and permissions!",
                    )

            try:
                shutil.copystat(os.path.join(studyfolder, ".mnapstudy"), mark_file)
                os.unlink(os.path.join(studyfolder, ".mnapstudy"))
            except Exception:
                pass

        try:
            username = getpass.getuser()
        except Exception:
            username = "unknown user"

        try:
            f = os.open(mark_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
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
                    ".qunexstudy file could not be created [%s]!" % (mark_file),
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

    Create the base study folder structure.

    ..  qx_command:
        type: utility

    Parameters:
        --studyfolder (str):
            The path to the study folder to be generated.

        --folders (str, default None):
            Path to the file which defines the subfolder structure. Set to
            "legacy" to use the legacy folder structure. By default, QuNex will
            create a very limited set of folders.

    Notes:
        By default, QuNex will create the minimum amount of necessary folders:

            <studyfolder>
            ├── logs
            ├── processing
            |   └── scripts
            └── sessions

        Creates the base folder at the provided path location and the study folders.
        Setting the folders parameter to legacy will use
        $TOOLS/python/python/qx_utilities/templates/study_folders_default.txt
        Which gives the following structure::

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
                │   ├── MR
                │   ├── EEG
                │   ├── BIDS
                │   ├── HCPLS
                │   ├── behavior
                │   ├── concs
                │   └── events
                ├── archive
                │   ├── MR
                │   ├── EEG
                │   ├── BIDS
                │   ├── HCPLS
                │   └── behavior
                └── specs
                    └── QC

        Do note that with the legacy option, the command will create all th
        missing folders in which the specified study is to reside. The command
        also prepares template batch_example.txt and pipeline example mapping
        files in <studyfolder>/sessions/specs folder. Finally, it creates
        a .qunexstudy file in the <studyfolder> to identify it as a study
        basefolder.

    Examples:
        ::

            qunex create_study \\
                --studyfolder=/Volumes/data/studies/WM.v4
    """

    print("Running create_study\n===================")

    if studyfolder is None:
        raise ge.CommandFailed(
            "manage_study",
            "Folder structure file [%s] not found!" % folders,
            "Please check the value of the folders parameter.",
        )

    if folders is None:
        print("\n---> Creating study folder structure:")
        for subfolder in ["logs", "processing/scripts", "sessions"]:
            tfolder = os.path.join(studyfolder, subfolder)
            try:
                os.makedirs(tfolder)
                print(" ... created:", tfolder)
            except OSError as e:
                if e.errno == errno.EEXIST:
                    print(" ... folder exists:", tfolder)
                else:
                    errstr = os.strerror(e.errno)
                    raise ge.CommandFailed(
                        "create_study",
                        "I/O error: %s" % (errstr),
                        "Folder could not be created due to '%s' error!" % (errstr),
                        "Folder to create: %s" % (tfolder),
                        "Please check paths and permissions!",
                    )

        print("\n---> Preparing template files:")
        mark_file = os.path.join(studyfolder, ".qunexstudy")
        try:
            f = os.open(mark_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(f)
            print(" ... created .qunexstudy file")
        except OSError as e:
            if e.errno == errno.EEXIST:
                print(" ... .qunexstudy file already exists")
            else:
                errstr = os.strerror(e.errno)
                raise ge.CommandFailed(
                    "create_study",
                    "I/O error: %s" % (errstr),
                    ".qunexstudy file could not be created [%s]!" % (mark_file),
                    "Please check paths and permissions!",
                )
    else:
        manage_study(
            studyfolder=studyfolder, action="create", folders=folders, verbose=True
        )


def check_study(startfolder=".", folders=None):
    """
    ``check_study startfolder="." [folders=$TOOLS/python/qx_utilities/templates/study_folders_default.txt]``

    Identify and report the study base folder.

    ..  qx_command:
        type: utility

    Parameters:
        --startfolder (str, default '.'):
            The folder from which to start looking for the study folder.

        --folders (str, default '$TOOLS/python/qx_utilities/templates/study_folders_default.txt'):
            Path to the file which defines the study folder structure.

    Notes:
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


def copy_study(
    studyfolder,
    existing_study,
    sessions=None,
    subjects=None,
    batchfile=None,
    filter=None,
):
    """
    ``copy_study studyfolder=<path to study base folder> existing_study=<path to source study base folder> [sessions=None] [subjects=None] [batchfile=None] [filter=None]``

    Copy an existing QuNex study to a new location.

    ..  qx_command:
        type: utility

    Parameters:
        --studyfolder (str):
            The path to the study folder to be generated.

        --existing_study (str):
            The path of an existing QuNex study that will be copied.

        --sessions (str, default None):
            If provided, only the specified sessions from the sessions folder
            will be processed. They are to be specified as a comma separated
            list.

        --subjects (str, default None):
            If provided, only the specified subjects from the subjects folder
            will be processed along with their sessions. They are to be
            specified as a comma separated list.

        --batchfile (str, default None):
            If provided, only the sessions and subjects specified in the batch
            file will be processed.

        --filter (str, default None):
            An optional parameter given as "key:value|key:value" string. Can be
            used for filtering the session data within the provided batchfile.

    Notes:
        Can be used for backing up existing studies or when copying previous
        study to continue with the processing or an analysis in a new study
        folder. If sessions or subjects parameter is provided only a subset of
        sessions/subjects will be copied over. If batchfile is provided, only
        the sessions specified in the batch file will be copied. If filter is
        provided, it will be applied to the provided batchfile before copying
        the study.

    Examples:
        ::

            qunex copy_study \\
                --studyfolder=/Volumes/data/studies/WM.v4 \\
                --existing_study=/Volumes/data/studies/WM.v3
    """

    print("Running copy_study\n==================\n")

    # check if mandatory parameters are provided
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

    # sessions and subjects should not be provided at the same time
    if sessions is not None and subjects is not None:
        raise ge.CommandError(
            "copy_study",
            "sessions and subjects provided at the same time",
            "Please provide either sessions or subjects, not both.",
        )

    # other parameters
    print(f" ... sessions: {sessions}")
    print(f" ... subjects: {subjects}")
    print(f" ... batchfile: {batchfile}")
    print(f" ... filter: {filter}")

    # create a new study at the specified location
    print()
    create_study(studyfolder=studyfolder)

    # rsync the whole study
    print()
    print("---> Copying existing study to a new location")
    print(f" ... from: {existing_study}")
    print(f" ... to: {studyfolder}")

    # Folders to skip at top level
    if subjects is None and sessions is None and filter is None:
        skip_top = []
    else:
        skip_top = ["subjects", "sessions"]

    for entry in os.listdir(existing_study):
        src_path = os.path.join(existing_study, entry)
        if not os.path.isdir(src_path):
            continue
        if entry in skip_top:
            continue
        dest_path = os.path.join(studyfolder, entry)
        print(f" ... rsyncing {entry}: {src_path} -> {dest_path}")
        cmd = ["rsync", "-aH", f"{src_path}/", dest_path]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            print(f"ERROR: Failed to rsync {src_path}!")
            raise

    # get sessions and subjects
    if batchfile is not None:
        sessions, _ = gc.resolve_sessions(
            batchfile=batchfile, sessions=sessions, filter=filter, command="copy_study"
        )
        subjects = []
        for session in sessions:
            if "subject" not in session:
                print(
                    f"WARNING: session {session} does not have a subject field, if this is a longitudinal study subjects will not be copied correctly!"
                )
            if session["subject"] not in subjects:
                subjects.append(session["subject"])
    elif sessions is not None:
        sessions = sessions.split(",")
    elif subjects is not None:
        subjects = subjects.split(",")

    # remove all folders in existing_study/sessions that are not in keep_sessions
    if sessions is not None:
        keep_sessions = sessions + ["archive", "inbox", "QC", "specs"]
        print()
        print("---> Copying sessions")
        sessions_path = os.path.join(existing_study, "sessions")
        try:
            for entry in os.listdir(sessions_path):
                src_path = os.path.join(sessions_path, entry)
                if not os.path.isdir(src_path) or entry in keep_sessions:
                    dest_path = os.path.join(studyfolder, "sessions", entry)
                    print(f" ... rsyncing {entry}: {src_path} -> {dest_path}")
                    cmd = ["rsync", "-aH", f"{src_path}/", dest_path]
                    subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            print(f"ERROR: Failed to rsync {src_path}!")
            raise
        except OSError as e:
            print(f"Error accessing sessions directory: {e}")
            raise e

    # remove all folders in existing_study/subjects that are not in subjects
    if subjects is not None:
        print()
        print("---> Copying subjects")
        subjects_path = os.path.join(existing_study, "subjects")
        try:
            for entry in os.listdir(subjects_path):
                src_path = os.path.join(subjects_path, entry)
                folder_name = os.path.basename(src_path)
                if not os.path.isdir(src_path) or folder_name in subjects:
                    dest_path = os.path.join(studyfolder, "subjects", entry)
                    print(f" ... rsyncing {entry}: {src_path} -> {dest_path}")
                    cmd = ["rsync", "-aH", f"{src_path}/", dest_path]
                    subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            print(f"ERROR: Failed to rsync {src_path}!")
            raise
        except OSError as e:
            print(f"Error accessing sessions directory: {e}")
            raise e

    # fix paths in txt, conc and list files
    print()
    print("---> Fixing paths in relevant files")
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

    # remove unused sessions or subjects from batch files
    # assume batch files are .txt files in the processing subfolder
    if sessions or subjects:
        print()
        print(
            "---> Removing unused sessions from batch files in the processing subfolder"
        )
        processing_folder = os.path.join(studyfolder, "processing")
        for item in os.listdir(processing_folder):
            if item.endswith(".txt"):
                batchfile = os.path.join(processing_folder, item)
                print(f" ... processing {batchfile}")
                filter_batch(batchfile, sessions, subjects)

                
def filter_batch(batchfile, sessions=None, subjects=None):
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
        keep = False
        if sessions:
            for session in sessions:
                if session in item:
                    keep = True
                    break

        if not keep and subjects:
            for subject in subjects:
                if f"subject: {subject}" in item:
                    keep = True
                    break

        if keep:
            new_batch += "\n---\n" + item

    # write back
    with open(batchfile, "w") as f:
        f.write(new_batch)


def create_batch(
    sessionsfolder=".",
    sourcefiles=None,
    targetfile=None,
    batchfile=None,
    sessions=None,
    filter=None,
    overwrite="no",
    paramfile=None,
):
    """
    ``create_batch [sessionsfolder=.] [sourcefiles=session_hcp.txt] [targetfile=processing/batch.txt] [batchfile=None] [sessions=None] [filter=None] [overwrite=no] [paramfile=<sessionsfolder>/specs/parameters.txt]``

    Create a joint batch file from source files in all session folders.

    ..  qx_command:
        type: utility

    Parameters:
        --sessionsfolder (str):
            The location of the <study>/sessions folder.

        --sourcefiles (str, default 'session_hcp.txt'):
            Comma separated names of source files to take from each specified
            session folder and add to batch file.

        --targetfile (str, default '<study>/processing/batch.txt'):
            The path to the batch file to be generated. By default, it is
            created as <study>/processing/batch.txt.

        --batchfile (str, default None):
            An optional path to an existing batch file or a list file to take
            the sessions from, instead of looking through the sessions folder.

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
            provided it defaults to <sessionsfolder>/specs/parameters.txt. If
            that does not exist it will not use it.

    Notes:
        The command combines all the sourcefiles in all session folders in
        sessionsfolder to generate a joint batch file and save it as targetfile.
        If only specific sessions are to be added or appended, "sessions"
        parameter can be used. This is a pipe, comma or space separated list of
        session ids, in which grob patterns can be used (e.g.
        sessions="AP*|OR*"), and all matching sessions will be processed. To
        take the sessions from an existing batch file or a list file, use the
        "batchfile" parameter; "sessions" and "filter" then select within it.

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
                provided, for details see:
                https://qunex.readthedocs.io/en/latest/wiki/Overview-FileBatch.html.
                Batch file consists of a header section and a list of imaging
                sessions. The header section provides the possibility to specify
                the default parameter values that are to be used throughout the
                study. Specifically, the parameters are provided as
                ``_<parameter name>: <parameter value>`` pairs. An example might
                be:

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
                please see:
                https://qunex.readthedocs.io/en/latest/wiki/UsageDocs-RunningListsOfCommands.html.
                These parameters will take priority over the parameters
                specified in the header section of the study batch file.

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

                   01: Survey
                   02: T1w:             T1w 0.7mm N2 : se(1): DwellTime(0.0000459): UnwarpDir(z)
                   03: T2w:             T2w 0.7mm N2 : se(1): DwellTime(0.0000066): UnwarpDir(z)
                   04: Survey
                   05: SE-FM-AP:        C-BOLD 3mm 48 2.5s FS-P   : se(1): phenc(AP): EchoSpacing(0.0006146)
                   06: SE-FM-PA:        C-BOLD 3mm 48 2.5s FS-A   : se(1): phenc(PA): EchoSpacing(0.0006146)
                   07: bold1:rest:      BOLD 3mm 48 2.5s          : se(1): phenc(PA): EchoSpacing(0.0006029): filename(rest_PA)
                   08: bold2:task:      BOLD 3mm 48 2.5s          : se(1): phenc(PA): EchoSpacing(0.0006029): filename(task1_PA)
                   09: bold2:task:      BOLD 3mm 48 2.5s          : se(1): phenc(PA): EchoSpacing(0.0006029): filename(task2_PA)

                In the above example, ``_hcp_brainsize: 150`` is specified for
                session ``OP386_baseline`` specifically. The specified values
                would take precedence over any other value specified either in
                the header section of the batch.txt file or the command line.

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

    target_folder = os.path.dirname(targetfile)
    if not os.path.exists(target_folder):
        print("---> Creating target folder %s" % (target_folder))
        os.makedirs(target_folder)

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
            gl.print_qunex_header(file=jfile)
            print("#", file=jfile)
            print("# Sessions folder: %s" % (sessionsfolder), file=jfile)
            print("# Source files: %s" % (sfiles), file=jfile)

        elif overwrite == "append":
            slist, parameters = gc.resolve_sessions(
                batchfile=targetfile, command="create_batch"
            )
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
            if paramfile and os.path.exists(paramfile):
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

        if sessions is not None or batchfile is not None:
            sessions, gopts = gc.resolve_sessions(
                batchfile=batchfile,
                sessions=sessions,
                filter=filter,
                sessionsfolder=sessionsfolder,
                command="create_batch",
                verbose=False,
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

    except Exception:
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
    batchfile=None,
    sessions=None,
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
    ``create_list [sessionsfolder="."] [batchfile=None] [sessions=None] [filter=None] [listfile=None] [bolds=None] [conc=None] [fidl=None] [glm=None] [roi=None] [boldname="bold"] [bold_tail=".nii.gz"] [img_suffix=""] [bold_variant=""] [overwrite="no"] [check="yes"]``

    Create a .list formatted file for the specified sessions

    ..  qx_command:
        type: utility

    Description:
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
            What to do if the specified list file already exists.

            Options are:

            - 'yes' (overwrite the existing file)
            - 'no' (abort creating a file)
            - 'append' (append sessions to the existing list file).

        --check (str, default 'yes'):
            Whether to check for existence of files to be included in the list
            and what to do if they don't exist.

            Options are:

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

    def check_file(file_name):
        if check == "no":
            return True
        elif check == "present":
            if not os.path.exists(file_name):
                print("WARNING: File does not exist [%s]!" % (file_name))
                return False
            else:
                return True
        elif check == "warn":
            if not os.path.exists(file_name):
                print(
                    "WARNING: File does not exist, but will be included in the list anyway [%s]!"
                    % (file_name)
                )
            return True
        else:
            if not os.path.exists(file_name):
                raise ge.CommandFailed(
                    "create_list",
                    "File does not exist",
                    "A file to be included in the list does not exist [%s]"
                    % (file_name),
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

    if boldtags and not batchfile:
        raise ge.CommandFailed(
            "create_list",
            "Parameter error",
            "To filter bolds using tags, you need to provide the batchfile parameter!",
            "Please check your input parameters!",
        )

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

    target_folder = os.path.dirname(listfile)
    if target_folder and not os.path.exists(target_folder):
        print("---> Creating target folder %s" % (target_folder))
        os.makedirs(target_folder)

    # --- check sessions
    sessions_list = []
    if batchfile:
        sessions_list, _ = gc.resolve_sessions(
            batchfile=batchfile,
            sessions=sessions,
            filter=filter,
            sessionsfolder=sessionsfolder,
            command="create_list",
            verbose=False,
        )
    else:
        # without a batch file the pool is the session folders that have images
        pool = glob.glob(os.path.join(sessionsfolder, "*", images_folder))
        pool = "|".join([os.path.basename(os.path.dirname(e)) for e in pool])

        sessions_list, _ = gc.resolve_sessions(
            sessions=pool,
            filter=filter,
            sessionsfolder=sessionsfolder,
            command="create_list",
            verbose=False,
        )
        if sessions:
            sessions_list = sessions_list.filter_by_key("id", sessions)

    if not sessions_list:
        raise ge.CommandFailed(
            "create_list",
            "No session found",
            "No sessions found to add to the list file!",
            "Please check your data!",
        )

    # --- generate list entries
    lines = []

    for session in sessions_list:
        session_lines = []
        session_lines.append("session id: %s" % (session["id"]))
        skip_session = False

        if boldnums:
            for boldnum in boldnums:
                tfile = os.path.join(
                    sessionsfolder,
                    session["id"],
                    images_folder,
                    functional_folder,
                    boldname + boldnum + bold_tail,
                )
                include_file = check_file(tfile)
                if include_file:
                    session_lines.append("    file:" + tfile)
                else:
                    skip_session = True
                    break

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
            except Exception:
                pass
            for boldnum in bolds:
                tfile = os.path.join(
                    sessionsfolder,
                    session["id"],
                    images_folder,
                    functional_folder,
                    boldname + boldnum + bold_tail,
                )
                include_file = check_file(tfile)
                if include_file:
                    session_lines.append("    file:" + tfile)
                else:
                    skip_session = True
                    break

        if roi:
            tfile = os.path.join(sessionsfolder, session["id"], images_folder, roi)
            include_file = check_file(tfile)
            if include_file:
                session_lines.append("    roi:" + tfile)
            else:
                skip_session = True

        if glm:
            tfile = os.path.join(
                sessionsfolder, session["id"], images_folder, functional_folder, glm
            )
            include_file = check_file(tfile)
            if include_file:
                session_lines.append("    glm:" + tfile)
            else:
                skip_session = True

        if conc:
            tfile = os.path.join(
                sessionsfolder,
                session["id"],
                images_folder,
                functional_folder,
                "concs",
                conc,
            )
            include_file = check_file(tfile)
            if include_file:
                session_lines.append("    conc:" + tfile)
            else:
                skip_session = True

        if fidl:
            tfile = os.path.join(
                sessionsfolder,
                session["id"],
                images_folder,
                functional_folder,
                "events",
                fidl,
            )
            include_file = check_file(tfile)
            if include_file:
                session_lines.append("    fidl:" + tfile)
            else:
                skip_session = True

        if not skip_session:
            lines += session_lines
        else:
            print("---> Skipping session %s from the list!" % (session["id"]))

    # --- write to target file
    if overwrite == "yes" or overwrite is True:
        print("---> Creating file %s" % (os.path.basename(listfile)))
        lfile = open(listfile, "w")
        gl.print_qunex_header(file=lfile)
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
    batchfile=None,
    sessions=None,
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
    ``create_conc [sessionsfolder="."] [batchfile=None] [sessions=None] [filter=None] [concfolder=None] [concname=""] [bolds=None] [boldname="bold"] [bold_tail=".nii.gz"] [img_suffix=""] [bold_variant=""] [overwrite="no"] [check="yes"]``

    Create .conc files for the specified sessions.

    ..  qx_command:
        type: utility

    Description:
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
            What to do if the specified conc file already exists.

            Options are:

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

    def check_file(file_name):
        if check == "no":
            return True
        elif not os.path.exists(file_name):
            if check == "warn":
                print("     WARNING: File does not exist [%s]!" % (file_name))
                return True
            else:
                print("     ERROR: File does not exist [%s]!" % (file_name))
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

    if sessions is None and batchfile is None:
        print(
            "WARNING: No sessions specified. The list will be generated for all sessions in the sessions folder!"
        )
        sessions = glob.glob(os.path.join(sessionsfolder, "*", images_folder))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.resolve_sessions(
        batchfile=batchfile,
        sessions=sessions,
        filter=filter,
        sessionsfolder=sessionsfolder,
        command="create_conc",
        verbose=False,
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
                complete = complete & check_file(tfile)
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
            except Exception:
                pass
            for boldnum in bolds:
                tfile = os.path.join(
                    sessionsfolder,
                    session["id"],
                    images_folder,
                    functional_folder,
                    boldname + str(boldnum) + bold_tail,
                )
                complete = complete & check_file(tfile)
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


def batch_tag2namekey(
    filename=None, sessionid=None, bolds=None, output="number", prefix="BOLD_"
):
    """
    ``batch_tag2namekey filename=<path to batch file> sessionid=<session id> bolds=<bold specification string> [output="number"] [prefix="BOLD_"]``

    Extract the data for the specified session and return the list of bold numbers or names.

    ..  qx_command:
        type: utility

    Parameters:
        --filename (str):
            Path to batch.txt file.

        --sessionid (str):
            Session id to look up.

        --bolds (str):
            Which bold images (as they are specified in the batch.txt file) to process.
            It can be a single type (e.g. 'task'), a pipe separated list
            (e.g. 'WM|Control|rest') or 'all' to process all.

        --output (str):
            Whether to output numbers ('number') or bold names ('name').
            In the latter case the name will be extracted from the 'filename'
            specification, if provided in the batch file, or '<prefix>[N]' if
            'filename' is not specified. Default is 'number'.

        --prefix (str):
            The default prefix to use if a filename is not specified in the batch file.
            Default is ``BOLD_``.


    Notes:
        Reads the batch file, extracts the data for the specified session and
        returns the list of bold numbers or names that correspond to bolds
        specified using the `bolds` parameter.

    """

    if filename is None:
        raise ge.CommandError("batchTag2Num", "No batch file specified!")

    if sessionid is None:
        raise ge.CommandError("batchTag2Num", "No session id specified!")

    if bolds is None:
        raise ge.CommandError("batchTag2Num", "No bolds specified!")

    sessions, options = gc.resolve_sessions(
        batchfile=filename, sessions=sessionid, command="batch_tag2namekey"
    )

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

    bolds, _, _ = gpc.use_or_skip_bold(session, options)

    boldlist = []
    for boldinfo in bolds:
        if output == "name":
            if "filename" in boldinfo:
                boldlist.append(boldinfo["filename"])
            else:
                boldlist.append("%s%d" % (prefix, boldinfo["bold_number"]))
        else:
            boldlist.append(str(boldinfo["bold_number"]))

    print("BOLDS:%s" % (",".join(boldlist)))


def list_sessions(batchfile=None, sessions=None, filter=None, sessionsfolder=None):
    """
    ``list_sessions [batchfile=None] [sessions=None] [filter=None] [sessionsfolder=None]``

    Print the comma separated list of the sessions a command would run over.

    ..  qx_command:
        type: utility
        aliases: get_sessions_for_slurm_array

    Parameters:
        --batchfile (str):
            Path to a batch.txt file.

        --sessions (str):
            A string with pipe `|` or comma separated list of sessions
            (sessions ids) to be processed (use of grep patterns is possible),
            e.g. `"AP128,OP139,ER*"`, or `*list` file with a list of session ids.
            If a batchfile is provided, this parameter selects within it.

        --filter (str):
            An optional parameter given as `"<key>:<value>|<key>:<value>"`
            string. Only sessions that match all the key-value pairs will be
            returned.

        --sessionsfolder (str):
            The sessions folder to match the sessions against when no batchfile
            is provided.

    Notes:
        The three parameters are resolved exactly as they are for any other
        command, so this is what any command given the same parameters will run
        over. Inside a SLURM job array that is the subset belonging to this
        array task, which is what the `get_sessions_for_slurm_array` spelling
        of this command was for.

    """

    # get sessions
    slist, _ = gc.resolve_sessions(
        batchfile=batchfile,
        sessions=sessions,
        filter=filter,
        sessionsfolder=sessionsfolder,
        command="list_sessions",
    )

    # print
    sarray = []
    for s in slist:
        sarray.append(s["id"])

    print(",".join(sarray))


def gather_behavior(
    sessionsfolder=".",
    batchfile=None,
    sessions=None,
    filter=None,
    sourcefiles="behavior.txt",
    targetfile=None,
    overwrite="no",
    check="yes",
    report="yes",
):
    """
    ``gather_behavior [sessionsfolder="."] [batchfile=None] [sessions=None] [filter=None] [sourcefiles="behavior.txt"] [targetfile="<sessionsfolder>/inbox/behavior/behavior.txt"] [overwrite="no"] [check="yes"]``

    Gather specified individual behavioral data from each session's behavior
    folder and compile it into a specified group behavioral file.

    ..  qx_command:
        type: utility

    Parameters:
        --sessionsfolder (str, '.'):
            The base study sessions folder (e.g. WM44/sessions) where the inbox
            and individual session folders are. If not specified, the current
            working folder will be taken as the location of the sessionsfolder.

        --batchfile (str, None):
            An optional path to a batch file or a list file to take the sessions
            from. `sessions` and `filter` then select within it.

        --sessions (str, None):
            Either a string with pipe `|` or comma separated list of sessions
            (sessions ids) to be processed (use of grep patterns is possible),
            e.g. `"AP128,OP139,ER*"`, or `*list` file with a list of session ids.

        --filter (str, None):
            Optional parameter used to filter sessions to include.

            It is specifed as a string in format::

                "<key>:<value>|<key>:<value>"

            Only the sessions for which all the specified keys match the specified
            values will be included in the list.

        --sourcefiles (str, 'behavior.txt'):
            A file or comma or pipe `|` separated list of files or grep patterns
            that define, which session specific files from the behavior folder
            to gather data from.

        --targetfile (str, None):
            The path to the target file, a file that will contain the joined data
            from all the individual session files.

        --overwrite (str, 'no'):
            Whether to overwrite an existing group behavioral file or not.

        --check (str, 'yes'):
            Check whether all the identified sessions have data to include in
            the compiled group file.

            The possible options are:
            - yes  (check and report an error if no behavioral data exists for a session)
            - warn (warn and list the sessions for which the behavioral data was not found)
            - no (do not run a check, ignore sessions for which no behavioral data was found

        --report (str, 'yes'):
            Whether to include date when file was generated and the final report
            in the compiled file ('yes') or not ('no').

    Notes:

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

        File format:

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

    Examples:

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

    def add_data(file, sdata, keys):
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
            except Exception:
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

    if sessions is None and batchfile is None:
        print(
            "---> WARNING: No sessions specified. The list will be generated for all sessions in the sessions folder!"
        )
        sessions = glob.glob(os.path.join(sessionsfolder, "*", "behavior"))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.resolve_sessions(
        batchfile=batchfile,
        sessions=sessions,
        filter=filter,
        sessionsfolder=sessionsfolder,
        command="gather_behavior",
        verbose=False,
    )

    if not sessions:
        raise ge.CommandFailed(
            "gather_behavior",
            "No session found",
            "No sessions found to process behavioral data from!",
            "Please check your data!",
        )

    # --- generate list entries

    process_report = {"ok": [], "missing": [], "error": []}
    data = {}
    keys = []

    for session in sessions:
        files = []
        for sfile in sfiles:
            files += glob.glob(
                os.path.join(sessionsfolder, session["id"], "behavior", sfile)
            )

        if not files:
            process_report["missing"].append(session["id"])
            continue

        sdata = {}
        for file in files:
            error = add_data(file, sdata, keys)
            if error:
                process_report["error"].append((session["id"], error))
                break

        if error:
            continue

        process_report["ok"].append(session["id"])
        data[session["id"]] = dict(sdata)

    # --- save group data

    try:
        fout = open(targetfile, "w")
    except Exception:
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

    for sessionid in process_report["ok"]:
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

    if any([process_report[status] for status, message in reportit]):
        print("---> Final report")
        for status, message in reportit:
            if process_report[status]:
                print("--->", message)
                if report and status != "ok":
                    print("#", message, file=fout)
                for info in process_report[status]:
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

    if process_report["error"] or process_report["missing"]:
        if check.lower() == "yes":
            raise ge.CommandFailed(
                "gather_behavior",
                "Errors encountered",
                "Not all sessions processed successfully!",
                "Sessions with missing behavioral data: %d"
                % (len(process_report["missing"])),
                "Sessions with errors in processing: %d"
                % (len(process_report["error"])),
                "Please check your data!",
            )
        elif check.lower() == "warn":
            raise ge.CommandNull(
                "gather_behavior",
                "Errors encountered",
                "Not all sessions processed successfully!",
                "Sessions with missing behavioral data: %d"
                % (len(process_report["missing"])),
                "Sessions with errors in processing: %d"
                % (len(process_report["error"])),
                "Please check your data!",
            )

    if not process_report["ok"]:
        raise ge.CommandNull(
            "gather_behavior", "No files processed", "No valid data was found!"
        )


def pull_sequence_names(
    sessionsfolder=".",
    batchfile=None,
    sessions=None,
    filter=None,
    sourcefiles="session.txt",
    targetfile=None,
    overwrite="no",
    check="yes",
    report="yes",
):
    """
    ``pull_sequence_names [sessionsfolder="."] [batchfile=None] [sessions=None] [filter=None] [sourcefiles="session.txt"] [targetfile="<sessionsfolder>/inbox/MR/sequences.txt"] [overwrite="no"] [check="yes"]``

    Gather a list of all the sequence names across the sessions and save it
    into a specified file.

    ..  qx_command:
        type: utility

    Parameters:
        --sessionsfolder (str, '.'):
            The base study sessions folder (e.g. WM44/sessions) where the inbox
            and individual session folders are. If not specified, the current
            working folder will be taken as the location of the sessionsfolder.

        --batchfile (str, None):
            An optional path to a batch file or a list file to take the sessions
            from. `sessions` and `filter` then select within it.

        --sessions (str, None):
            Either a string with pipe `|` or comma separated list of sessions
            (sessions ids) to be processed (use of grep patterns is possible),
            e.g. `"AP128,OP139,ER*"`, or `*list` file with a list of session ids.

        --filter (str, None):
            Optional parameter used to filter sessions to include.

            It is specifed as a string in format::

                "<key>:<value>|<key>:<value>"

            Only the sessions for which all the specified keys match the specified
            values will be included in the list.

        --sourcefiles (str, 'session.txt'):
            A file or comma or pipe `|` separated list of files or grep patterns
            that define, which session description files to check.

        --targetfile (str, None):
            The path to the target file, a file that will contain the list of all
            the session names from all the individual session information files.

        --overwrite (str, 'no'):
            Whether to overwrite an existing file or not.

        --check (str, 'yes'):
            Check whether all the identified sessions have the specified
            information files.

            The possible options are:

            - yes   check and report an error if no information exists for a session
            - warn  warn and list the sessions for which the neuroimaging
                    information was not found
            - no    do not run a check, ignore sessions for which no imaging
                    data was found

        --report (str, 'yes'):
            Whether to include date when file was generated and the final report
            in the compiled file ('yes') or not ('no').


    Notes:
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

        File format:

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

    Examples:

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

    def add_data(file, data):
        missing_names = []
        sequence_names = []

        try:
            f = open(file, "r")
        except Exception:
            return "Could not open %s for reading!" % (file)

        for line in f:
            if ":" in line:
                line = [e.strip() for e in line.split(":")]
                if line[0].isnumeric():
                    if len(line) > 1:
                        sequence_names.append(line[1])
                    else:
                        sequence_names.append(line[0])
        f.close()

        if not sequence_names:
            return "No sequence information found in file [%s]!" % (file)

        data += sequence_names

        if missing_names:
            return "The following sequences had no names: %s!" % (
                ", ".join(missing_names)
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
            except Exception:
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

    if sessions is None and batchfile is None:
        print(
            "---> WARNING: No sessions specified. The list will be generated for all sessions in the sessions folder!"
        )
        sessions = glob.glob(os.path.join(sessionsfolder, "*", "behavior"))
        sessions = [os.path.basename(os.path.dirname(e)) for e in sessions]
        sessions = "|".join(sessions)

    sessions, gopts = gc.resolve_sessions(
        batchfile=batchfile,
        sessions=sessions,
        filter=filter,
        sessionsfolder=sessionsfolder,
        command="pull_sequence_names",
        verbose=False,
    )

    if not sessions:
        raise ge.CommandFailed(
            "pull_sequence_names",
            "No session found",
            "No sessions found to process neuroimaging data from!",
            "Please check your data!",
        )

    # --- generate list entries

    process_report = {"ok": [], "missing": [], "error": []}
    data = []

    for session in sessions:
        files = []
        for sfile in sfiles:
            files += glob.glob(os.path.join(sessionsfolder, session["id"], sfile))

        if not files:
            process_report["missing"].append(session["id"])
            continue

        for file in files:
            error = add_data(file, data)
            if error:
                process_report["error"].append((session["id"], error))
                break

        if error:
            continue

        process_report["ok"].append(session["id"])

    # --- save group data

    try:
        fout = open(targetfile, "w")
    except Exception:
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

    if any([process_report[status] for status, message in reportit]):
        print("---> Final report")
        for status, message in reportit:
            if process_report[status]:
                print("--->", message)
                if report and status != "ok":
                    print("#", message, file=fout)
                for info in process_report[status]:
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

    if process_report["error"] or process_report["missing"]:
        if check.lower() == "yes":
            raise ge.CommandFailed(
                "pull_sequence_names",
                "Errors encountered",
                "Not all sessions processed successfully!",
                "Sessions with missing imaging data: %d"
                % (len(process_report["missing"])),
                "Sessions with errors in processing: %d"
                % (len(process_report["error"])),
                "Please check your data!",
            )
        elif check.lower() == "warn":
            raise ge.CommandNull(
                "pull_sequence_names",
                "Errors encountered",
                "Not all sessions processed successfully!",
                "Sessions with missing imaging data: %d"
                % (len(process_report["missing"])),
                "Sessions with errors in processing: %d"
                % (len(process_report["error"])),
                "Please check your data!",
            )

    if not process_report["ok"]:
        raise ge.CommandNull(
            "pull_sequence_names", "No files processed", "No valid data was found!"
        )


def export_prep(command_name, sessionsfolder, mapto, mapaction, mapexclude):
    """
    Prepares variables for data export.
    """
    if os.path.exists(sessionsfolder):
        sessionsfolder = os.path.abspath(sessionsfolder)
    else:
        raise ge.CommandFailed(
            command_name,
            "Sessions folder does not exist",
            "The specified sessions folder does not exist [%s]" % (sessionsfolder),
            "Please check paths!",
        )

    if mapto:
        mapto = os.path.abspath(mapto)
    else:
        raise ge.CommandFailed(
            command_name,
            "Target not specified",
            "To execute the specified mapping `mapto` parameter has to be specified!",
            "Please check your command call!",
        )

    if mapaction not in ["link", "copy", "move"]:
        raise ge.CommandFailed(
            command_name,
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
            except Exception:
                raise ge.CommandFailed(
                    command_name,
                    "Invalid exclusion",
                    "Could not parse the exclusion regular expression: '%s'!" % (e),
                    "Please check mapexclude parameter!",
                )

    return sessionsfolder, mapto, mapexclude


def create_session_info(
    batchfile=None,
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
    ``create_session_info [batchfile=None] sessions=<sessions specification> [pipelines=hcp] [sessionsfolder=.] [sourcefile=session.txt] [targetfile=session_<pipeline>.txt] [mapping=specs/<pipeline>_mapping.txt] [filter=None] [overwrite=no]``

    Create session info files for specified sessions and pipeline.

    ..  qx_command:
        type: utility

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

            or::

                <pattern_with_*>  => <user_specified_label>

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

            Asterisk (*) patterns are supported in the original sequence names.
            Such patterns will match any sequence of characters. For example,
            the pattern `T*BOLD` will match both `T1BOLD` and `T2BOLD`. Asterisk
            can be used multiple times in a single pattern, e.g. `*BOLD*3mm*`.
            Each asterisk will match any sequence of characters, including an
            empty sequence.

            If multiple mappings are specified for fieldmap magnitude images
            only the last magnitude image will be used. To pair two fieldmap
            magnitude images with the same fieldmap phase image, `fm` tags must
            be explicitly specified in the mapping file, e.g::

                fieldmap_phase       => FM-Phase: fm(1)
                fieldmap_magnitude1  => FM-Magnitude: fm(1)
                fieldmap_magnitude2  => FM-Magnitude: fm(1)
                fieldmap_precomputed => FM-Precomputed: fm(1)

            "Or" patterns are supported using the ``||`` separator on the
            left-hand side of a mapping rule. For each image, the variants
            are tried left-to-right; the first one that matches is applied and
            the remaining variants are skipped. For example::

                T1w_HiRes || T1w_LowRes => T1w

            For an image named ``T1w_HiRes`` the first variants matches, so
            it is mapped to ``T1w``. For an image named ``T1w_LowRes`` the
            first variants does not match, but the second does, so it is also
            mapped to ``T1w``. Each variants may be an exact name or contain
            ``*`` glob patterns — they are all treated uniformly. Any number of
            variantss can be chained, e.g.::

                T1w_HiRes || T1w_MedRes || T1w_LowRes => T1w

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

                T*BOLD => bold:task

                Example lines in a source session.txt file:

                01: Scout
                02: T1w 0.7mm N1
                03: T2w 0.7mm N1
                04: RSBOLD 3mm 48 2.5s
                05: RSBOLD 3mm 48 2.5s
                06: T1BOLD 3mm 48 2.5s
                07: T2BOLD 3mm 48 2.5s

                Resulting lines in target session_<pipeline>.txt file:

                01:                  :Scout
                02: T1w              :T1w 0.7mm N1
                03: T2w              :T2w 0.7mm N1
                04: bold1:rest       :RSBOLD 3mm 48 2.5s
                05: bold2:sleep      :RSBOLD 3mm 48 2.5s
                06: bold1:task       :T1BOLD 3mm 48 2.5s
                07: bold2:task       :T2BOLD 3mm 48 2.5s

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
        sessions, _ = gc.resolve_sessions(
            batchfile=batchfile,
            sessions=sessions,
            filter=filter,
            command="create_session_info",
            verbose=False,
        )

        sfolders = []
        for session in sessions:
            new_set = glob.glob(os.path.join(sessionsfolder, session["id"]))
            if not new_set:
                print(
                    "WARNING: No folders found that match %s. Please check your data!"
                    % (os.path.join(sessionsfolder, session["id"]))
                )
            sfolders += new_set

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
                gl.print_qunex_header(file=fout)
                print("#", file=fout)

                for line in output_lines:
                    print(line, file=fout)
                report["processed"].append(sfolder)

            # session file syntax error, conflicting rules
            except ge.SpecFileSyntaxError as e:
                report["error"].append(sfolder)
                print(f"  ... ERROR: {e.error}")
            except Exception as e:
                report["error"].append(sfolder)
                print(f"  ... ERROR: {str(e)}")

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


def _simple_glob_match(text, pattern):
    """
    Simple glob matching that handles * at the beginning, end, or in between.

    Args:
        text: The text to match against
        pattern: A pattern string that may contain * wildcards

    Returns:
        True if the text matches the pattern, False otherwise
    """
    # Split pattern by * to get literal parts
    parts = pattern.split("*")

    # Check if the first part matches the beginning (if not starting with *)
    if pattern[0] != "*":
        if not text.startswith(parts[0]):
            return False
        text = text[len(parts[0]) :]
        parts = parts[1:]
    else:
        # Remove empty string from leading *
        parts = parts[1:]

    # Check if the last part matches the end (if not ending with *)
    if pattern[-1] != "*" and len(parts) > 0:
        if not text.endswith(parts[-1]):
            return False
        text = text[: -len(parts[-1])] if parts[-1] else text
        parts = parts[:-1]
    else:
        if len(parts) > 0 and parts[-1] == "":
            # Remove empty string from trailing *
            parts = parts[:-1]

    # Check middle parts
    pos = 0
    for part in parts:
        # Skip empty strings from consecutive **
        if not part:
            continue
        idx = text.find(part, pos)
        if idx == -1:
            return False
        pos = idx + len(part)

    return True


def _match_or_rule(img_name, or_rules):
    """Try to match an image name against 'or' rules (per-image).

    For each 'or' rule, variants are tried left-to-right.  The first
    variant that matches the image name wins and the associated rule
    is returned.  Each variant may be an exact name or a ``*`` glob
    pattern — they are all treated uniformly.

    For example, given ``T1w_HiRes || T1w_LowRes => T1w``:

    * An image named ``T1w_HiRes`` matches the first variant → rule
      returned.
    * An image named ``T1w_LowRes`` does not match the first variant,
      matches the second → rule returned.
    * An image named ``T1w_Other`` matches neither → ``None``.

    Args:
        img_name: The series_description of the image to match.
        or_rules: list of dicts with ``'variants'`` (list of str)
                  and ``'rule'`` (dict) keys from the parsed mapping
                  file.

    Returns:
        The matching rule dict, or ``None`` if no or-rule matches.
    """
    for or_rule in or_rules:
        for alt in or_rule["variants"]:
            if "*" in alt:
                if _simple_glob_match(img_name, alt):
                    return or_rule["rule"]
            else:
                if img_name == alt:
                    return or_rule["rule"]
    return None


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
    grp_glob_rule = mapping_rules["group_rules"]["glob"]
    grp_or_rules = mapping_rules["group_rules"].get("or", [])

    for img_num, img_info in src_session["images"].items():
        img_name = img_info["series_description"]
        rule = {"additional_tags": []}
        # rules defined using image number takes precedence
        if img_num in grp_img_num_rule:
            rule = grp_img_num_rule[img_num]
        elif img_name in grp_name_rule:
            rule = grp_name_rule[img_name]
        # Try "or" rules — variants tried left-to-right per image
        else:
            or_match = _match_or_rule(img_name, grp_or_rules)
            if or_match is not None:
                rule = or_match
            # Try glob-based matching (simple * patterns)
            else:
                matched_rules = []
                for pattern, glob_rule in grp_glob_rule.items():
                    if _simple_glob_match(img_name, pattern):
                        matched_rules.append((pattern, glob_rule))

                if len(matched_rules) > 1:
                    # Check if all matched rules map to the same target
                    first_hcp_type = matched_rules[0][1].get("hcp_image_type")
                    conflicting = False
                    for pattern, matched_rule in matched_rules[1:]:
                        if matched_rule.get("hcp_image_type") != first_hcp_type:
                            conflicting = True
                            break

                    if conflicting:
                        # Format image number properly (handle tuple case)
                        img_num_str = (
                            str(img_num[0])
                            if isinstance(img_num, tuple)
                            else str(img_num)
                        )

                        # Build detailed rule descriptions
                        rule_details = []
                        for p, matched_rule in matched_rules:
                            hcp_type = matched_rule.get("hcp_image_type")
                            if hcp_type:
                                type_str = f"{hcp_type[0]}" + (
                                    f":{hcp_type[2]}"
                                    if len(hcp_type) > 2 and hcp_type[2]
                                    else ""
                                )
                            else:
                                type_str = "no mapping"
                            rule_details.append(
                                f"  \u2022 Pattern: '{p}'  \u2192  maps to: {type_str}"
                            )

                        patterns_str = "\n".join(rule_details)
                        raise ge.SpecFileSyntaxError(
                            error=f"Image {img_num_str} ('{img_name}') matches multiple conflicting mapping rules:\n\n"
                            f"{patterns_str}\n\n"
                            f"Fix: Make your patterns more specific so only one matches, or ensure all matching patterns map to the same target."
                        )

                if matched_rules:
                    rule = matched_rules[0][1]

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
        # a tag may be defined in the source session file, in the mapping rule,
        # or in both. a conflict only exists when both define it with different
        # values; identical definitions (a common case once the source file
        # already carries auto-detected tags such as phenc) are harmless.
        if i in img_info and i in rule and img_info[i] != rule[i]:
            raise ge.SpecFileSyntaxError(
                error=f"""Conflicting definitions of tag {i} for image {img_info["raw_image_number"]}: """
                f"""source session file has {i}({img_info[i]}) but the mapping rule has {i}({rule[i]}). """
                f"""Remove the {i} tag from the source session file or the mapping file, or make them match."""
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
    grp_or_rules = mapping_rules["group_rules"].get("or", [])
    or_rule_values = [or_entry["rule"] for or_entry in grp_or_rules]
    for rule in itertools.chain(
        grp_img_num_rules.values(), grp_img_name_rules.values(), or_rule_values
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
                    # record the pair if 2 consecutive images are a matching pair
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
            "DWI",
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
