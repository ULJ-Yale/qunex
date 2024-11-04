#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``bids.py``

Functions for importing and exporting BIDS data to QuNex file structure.

--import_bids         Maps BIDS data to QuNex structure.
--BIDSExport          Exports QuNex data to BIDS structured folder.

The commands are accessible from the terminal using qunex command.
"""

"""
Copyright (c) Grega Repovs. All rights reserved.
"""

import os
import os.path
import re
import shutil
import zipfile
import tarfile
import glob
import gzip
import ast
import json
import yaml
import sys

import general.exceptions as ge
import general.core as gc
import general.filelock as fl
import processing.core as pc

from datetime import datetime

unwarp = {
    None: "Unknown",
    "i": "x",
    "j": "y",
    "k": "z",
    "i-": "x-",
    "j-": "y-",
    "k-": "z-",
}
PEDirMap = {
    "AP": "j-",
    "j-": "AP",
    "PA": "j",
    "j": "PA",
    "RL": "i",
    "i": "RL",
    "LR": "i-",
    "i-": "LR",
}
json_all = ["phenc", "DwellTime", "EchoSpacing", "UnwarpDir"]
json_mapping = {
    "phenc": ["PhaseEncodingDirection", lambda x: PEDirMap.get(x, "NA")],
    "UnwarpDir": ["PhaseEncodingDirection", lambda x: unwarp.get(x, "NA")],
    "EchoSpacing": ["EffectiveEchoSpacing", lambda x: x],
}
bids_mri_types = {
        'T1w': {'folder': 'anat', 'subtype': 'nonparametric', 'suffix': 'T1w'},
        'T2w': {'folder': 'anat', 'subtype': 'nonparametric', 'suffix': 'T2w'},
        'FM-GE': {'folder': 'fmap', 'subtype': 'fieldmaps', 'suffix': 'fieldmap'},
        'FM-Magnitude': {'folder': 'fmap', 'subtype': 'fieldmaps', 'suffix': 'magnitude'},
        'FM-Phase': {'folder': 'fmap', 'subtype': 'fieldmaps', 'suffix': 'phasediff'},
        'SE-FM-AP': {'folder': 'fmap', 'subtype': 'pepolar', 'suffix': 'epi'},
        'SE-FM-PA': {'folder': 'fmap', 'subtype': 'pepolar', 'suffix': 'epi'},
        'SE-FM-LR': {'folder': 'fmap', 'subtype': 'pepolar', 'suffix': 'epi'},
        'SE-FM-RL': {'folder': 'fmap', 'subtype': 'pepolar', 'suffix': 'epi'},
        'boldref': {'folder': 'func', 'subtype': 'func', 'suffix': 'sbref'},
        'bold': {'folder': 'func', 'subtype': 'func', 'suffix': 'bold'},
        'DWI': {'folder': 'dwi', 'subtype': 'dwi', 'suffix': 'dwi'}
        }




def mapToQUNEXBids(
    file, sessionsfolder, bidsfolder, sessionsList, overwrite, prefix, select=False
):
    """
    Identifies and returns the intended location of the file based on its name.
    """
    try:
        if sessionsfolder[-1] == "/":
            sessionsfolder = sessionsfolder[:-1]
    except:
        pass

    folder = bidsfolder
    subject = ""
    session = ""
    optional = ""
    modality = ""
    isoptional = False

    # --- load BIDS structure
    # template folder
    niuTemplateFolder = os.environ["NIUTemplateFolder"]
    bidsStructure = os.path.join(niuTemplateFolder, "import_bids.txt")

    if not os.path.exists(bidsStructure):
        raise ge.CommandFailed(
            "mapToQUNEXBids",
            "No BIDS structure file present!",
            "There is no BIDS structure file %s" % (bidsStructure),
            "Please check your QuNex installation",
        )

    bids_file = open(bidsStructure)
    content = bids_file.read()
    bids = ast.literal_eval(content)

    # -> extract file meta information
    bids_path = file.replace(sessionsfolder, "")
    for part in re.split(r"_|/|\.", bids_path):
        if part.startswith("sub-"):
            subject = part.split("-")[1]
        elif part.startswith("ses-"):
            session = part.split("-")[1]
        elif part in bids["optional"]:
            optional = part
            isoptional = True
        elif part in bids["modalities"]:
            modality = part
        else:
            for targetModality in bids["modalities"]:
                if part in bids[targetModality]["label"]:
                    modality = targetModality

    # -> check whether we have a session specific or study general file

    session = "_".join([e for e in [subject, session] if e])
    if session:
        folder = os.path.join(sessionsfolder, session, "bids")
        if select:
            if session not in select:
                sessionsList["skip"].append(session)
    else:
        session = "bids"

    # ---> session marked to skip
    if session in sessionsList["skip"]:
        return False, False

    # ---> processing a new session
    elif session not in sessionsList["list"]:

        sessionsList["list"].append(session)

        # ---> processing study level data
        if session == "bids":
            io = fl.makedirs(bidsfolder)
            if io and io != "File exists":
                raise ge.CommandFailed(
                    "import_bids",
                    "I/O error: %s" % (io),
                    "Could not create BIDS info folder [%s]!" % (bidsfolder),
                    "Please check paths and permissions!",
                )

            io = fl.open_status(
                os.path.join(bidsfolder, "bids_info_status"),
                "Processing started on %s.\n"
                % (datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            )

            # ---> status created
            if io is None:
                print(prefix + "---> processing BIDS info folder")
                sessionsList["bids"] = "open"

            # ---> status exists
            elif io == "File exists" and not (overwrite == "yes" or overwrite is True):
                print(prefix + "---> skipping processing of BIDS info folder")
                sessionsList["skip"].append("bids")
                sessionsList["bids"] = "locked"
                return False, False

            # ---> an error
            elif io != "File exists":
                raise ge.CommandFailed(
                    "import_bids",
                    "I/O error: %s" % (io),
                    "Could not create BIDS info status file [%s]!"
                    % (os.path.join(bidsfolder, "bids_info_status")),
                    "Please check paths and permissions!",
                )

        # ---> session folder exists
        elif os.path.exists(folder):
            if overwrite == "yes" or overwrite is True:
                print(
                    prefix
                    + "---> bids for session %s already exists: cleaning session"
                    % (session)
                )
                shutil.rmtree(folder)
                sessionsList["clean"].append(session)
            elif not os.path.exists(os.path.join(folder, "bids2nii.log")):
                print(
                    prefix
                    + "---> incomplete bids for session %s already exists: cleaning session"
                    % (session)
                )
                shutil.rmtree(folder)
                sessionsList["clean"].append(session)
            else:
                sessionsList["skip"].append(session)
                print(
                    prefix
                    + "---> bids for session %s already exists: skipping session"
                    % (session)
                )
                print(prefix + "    files previously mapped:")
                with open(os.path.join(folder, "bids2nii.log")) as bidsLog:
                    for logline in bidsLog:
                        if "BIDS to nii mapping report" in logline:
                            continue
                        elif "=>" in logline:
                            mappedFile = logline.split("=>")[0].strip()
                            print(
                                prefix + "    ... %s" % (os.path.basename(mappedFile))
                            )
                return False, False

        # ---> session folder does not exist and is not 'bids'
        else:
            print(prefix + "---> creating bids session %s" % (session))
            sessionsList["map"].append(session)

    # ---> compile target filename
    if isoptional:
        oparts = file.split(os.sep)
        fparts = [folder] + oparts[oparts.index(optional) :]
        tfile = os.path.join(*fparts)
    else:
        tfile = os.path.join(folder, optional, modality, os.path.basename(file))

    # ---> check folder
    io = fl.makedirs(os.path.dirname(tfile))

    if io and io != "File exists":
        raise ge.CommandFailed(
            "import_bids",
            "I/O error: %s" % (io),
            "Could not create folder for file [%s]!" % (tfile),
            "Please check paths and permissions!",
        )

    # ---> return file and locking info
    return tfile, session == "bids"


def import_bids(
    sessionsfolder=None,
    inbox=None,
    sessions=None,
    action="link",
    overwrite="no",
    archive="move",
    bidsname=None,
    fileinfo=None,
    add_json_info="all",
):
    """
    ``import_bids [sessionsfolder=.] [inbox=<sessionsfolder>/inbox/BIDS] [sessions="*"] [action=link] [overwrite=no] [archive=move] [bidsname=<inbox folder name>] [fileinfo=short] [add_json_info='all']``
    
    Maps a BIDS dataset to the QuNex Suite file structure.

    Parameters:
        --sessionsfolder (str, default '.'):
            The sessions folder where all the sessions are to be mapped to. It
            should be a folder within the <study folder>.

        --inbox (str, default <sessionsfolder>/inbox/BIDS):
            The location of the BIDS dataset. It can be any of the following:
            the BIDS dataset top folder, a folder that contains the BIDS
            dataset, a path to the compressed `.zip` or `.tar.gz` package that
            can contain a single session or a multi-session dataset, or a
            folder that contains a compressed package. For instance the user
            can specify "<path>/<bids_file>.zip" or "<path>" to a folder that
            contains multiple packages. The default location where the command
            will look for a BIDS dataset is.

        --sessions (str, optional):
            An optional parameter that specifies a comma or pipe separated list
            of sessions from the inbox folder to be processed. Glob patterns
            can be used. If provided, only packets or folders within the inbox
            that match the list of sessions will be processed. If `inbox` is a
            file `sessions` has to be a list of session specifications, only
            those sessions that match the list will be processed. If `inbox` is
            a valid bids datastructure folder or archive, then the sessions can
            be specified either in `<subject id>[_<session name>]` format or as
            explicit `sub-<subject id>[/ses-<session name>]` names.

        --action (str, default 'link'):
            How to map the files to QuNex structure.
            These are the options:

            - 'link' ... the files will be mapped by creating hard
              links if possible, otherwise they will be copied
            - 'copy' ... the files will be copied
            - 'move' ... the files will be moved.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --archive (str, default 'move'):
            What to do with the files after they were mapped.
            Options are:

            - 'leave'  ... leave the specified archive where it is
            - 'move'   ... move the specified archive to
              `<sessionsfolder>/archive/BIDS`
            - 'copy'   ... copy the specified archive to
              `<sessionsfolder>/archive/BIDS`
            - 'delete' ... delete the archive after processing if no
              errors were identified.

            Please note that there can be an interaction with the `action`
            parameter. If files are moved during action, they will be missing
            if `archive` is set to 'move' or 'copy'.

        --bidsname (str, default detailed below):
            The optional name of the BIDS dataset. If not provided it will be
            set to the name of the inbox folder or the name of the compressed
            package.

        --fileinfo (str, default 'short'):
            What file information to include in the session.txt file. Options
            are:

            - 'short' ... only provide the short description based on
              the identified BIDS tags
            - 'full' ... list the full file name excluding the
              participant id, session name and extension.

        --add_json_info (str, default 'all'):
            A comma or space separated string, listing which info present in 
            `.json` sidecar files to include in the sequence information. 
            Options are:

            - phenc ... phase encoding direction
            - DwellTime
            - UnwarpDir ... unwarp direction
            - EchoSpacing
            - 'all' ... all of the above listed information, if present in 
              the `.json` sidecar file.

    Output files:
        After running the `import_bids` command the BIDS dataset will be
        mapped to the QuNex folder structure and image files will be
        prepared for further processing along with required metadata.

        Files pertaining to the study and not specific subject / session are
        stored in::

            <study folder>/info/bids/<bids bame>

        The original BIDS session-level data is stored in::

            <sessionsfolder>/<session>/bids

        Image files mapped to new names for QuNex are stored in::

            <sessionsfolder>/<session>/nii

        The full description of the mapped files is in::

            <sessionsfolder>/<session>/session.txt

        The output log of BIDS mapping is in::

            <sessionsfolder>/<session>/bids/bids2nii.log

        The study-level BIDS files are in::

            <study_folder>/<info>/bids/<bidsname>

    Notes:
        The import_bids command consists of two steps:

        Step 1 - Mapping BIDS dataset to QuNex Suite folder structure:
            The `inbox` parameter specifies the location of the BIDS
            dataset. This path is inspected for a BIDS compliant dataset.
            The path can point to a folder with extracted BIDS dataset, a
            `.zip` or `.tar.gz` archive or a folder containing one or more
            `.zip` or `.tar.gz` archives. In the initial step, each file
            found will be assigned either to a specific session or the
            overall study.

            The BIDS files assigned to the study will be saved in the
            following location::

                <study_folder>/info/bids/<bids_dataset_name>

            <bids_dataset_name> can be provided as a `bidsname` parameter to
            the command call. If `bidsname` is not provided, the name will
            be set to the name of the parent folder or the name of the
            compressed archive.

            The files identified as belonging to a specific session will be
            mapped to folder::

                <sessions_folder>/<subject>_<session>/bids

            The `<subject>_<session>` string will be used as the identifier
            for the session in all the following steps. If no session is
            specified in BIDS, `session` will be the same as `subject`. If
            the folder for the `session` does not exist, it will be
            created.

            When the files are mapped, their filenames will be preserved and
            the correct folder structure will be reconstructed if it was
            previously flattened.

            Behavioral data:
                Upon import of the BIDS dataset, the behavioral and participant
                specific data present in the `<bids_study>/participants.tsv`
                and `<bids_study>/phenotype/*.tsv` files, is parsed and split
                so that data belonging to a specific participant is mapped to
                that participant's sessions `behavior` folder (e.g. `<QuNex
                study folder>/sessions/s14_01/behavior/masq01.tsv`). In this
                way the session folder contains all the behavioral data
                relevant for that participant.

        Step 2 - Mapping image files to QuNex Suite `nii` folder:
            For each session separately, images from the `bids` folder are
            mapped to the `nii` folder and appropriate `session.txt` file
            is created per standard QuNex specification.

            The second step is achieved by running `map_bids2nii` on each
            session folder. This step is run automatically, but can be
            invoked indepdendently if mapping of bids dataset to QuNex
            Suite folder structure was already completed. For detailed
            information about this step, please review `map_bids2nii`
            inline help.

        Extra notes:
            Please see `map_bids2nii` inline documentation!

    Examples:
        ::

            qunex import_bids \\
                --sessionsfolder="<absolute path to study folder>/sessions" \\
                --inbox="<absolute path to folder with bids dataset>" \\
                --archive=move \\
                --overwrite=yes

        The above command would map the entire BIDS dataset located at the
        specified location into the relevant sessions' folders—creating them
        when needed—, organize the MR image files in the sessions' `nii` folder
        and prepare `session.txt` file for further processing. Any preexisting
        data for the sessions present in the BIDS dataset would be removed and
        replaced. By default, the BIDS files would be hard-linked to the new
        location.

        ::

            qunex import_bids \\
                --sessionsfolder="<absolute path to study folder>/sessions" \\
                --inbox="<absolute path to folder with bids dataset>" \\
                --action='copy' \\
                --archive='leave' \\
                --overwrite=no

        The above command would map the entire BIDS dataset located at the
        specified location into the relevant sessions' folders—creating them
        when needed—, organize the MR image files in the sessions' `nii` folder
        and prepare `session.txt` file for further processing. If for any of
        the sessions bids mapped data already exist, that session will be
        skipped when processing. The files would be mapped to their
        destinations by creating a copy rather than hard-linking them.

        ::

            qunex import_bids \\
                --sessionsfolder="<absolute path to study folder>/sessions" \\
                --inbox="<absolute path to folder with bids dataset>" \\
                --action='copy' \\
                --archive='leave' \\
                --overwrite=no \\
                --fileinfo=full


        In the example above, by specifying the `--fileinfo` parameter as "full"
        the whole file name (with the exception of the participant id, the
        session name and the extension) will be printed for each image file in
        the `session.txt` file. Use this parameter if file names are not
        matching the BIDS standard completely and hold important information
        for later correct file handling.

        ::

            qunex import_bids \\
                --sessionsfolder=myStudy \\
                --overwrite=yes \\
                --bidsname=swga
    """

    print("Running import_bids\n==================")

    if action not in ["link", "copy", "move"]:
        raise ge.CommandError(
            "import_bids",
            "Invalid action specified",
            "%s is not a valid action!" % (action),
            "Please specify one of: copy, link, move!",
        )

    if overwrite not in ["yes", "no"]:
        raise ge.CommandError(
            "import_bids",
            "Invalid option for overwrite",
            "%s is not a valid option for overwrite parameter!" % (overwrite),
            "Please specify one of: yes, no!",
        )

    if archive not in ["leave", "move", "copy", "delete"]:
        raise ge.CommandError(
            "import_bids",
            "Invalid dataset archive option",
            "%s is not a valid option for dataset archive option!" % (archive),
            "Please specify one of: move, copy, delete!",
        )

    if fileinfo not in ["short", "full", None]:
        raise ge.CommandError(
            "import_bids",
            "Invalid fileinfo option",
            "%s is not a valid option for fileinfo parameer!" % (fileinfo),
            "Please specify one of: short, full!",
        )

    if sessionsfolder is None:
        sessionsfolder = os.path.abspath(".")

    qxfolders = gc.deduceFolders({"sessionsfolder": sessionsfolder})

    if inbox is None:
        inbox = os.path.join(sessionsfolder, "inbox", "BIDS")

    sessionsList = {
        "list": [],
        "clean": [],
        "skip": [],
        "map": [],
        "append": [],
        "bids": False,
    }
    allOk = True
    errors = ""

    inbox = os.path.abspath(inbox)

    # ---> Check for folders
    bidsinbox = os.path.join(sessionsfolder, "inbox", "BIDS")
    if not os.path.exists(bidsinbox):
        io = fl.makedirs(bidsinbox)
        if not io:
            print("---> created inbox BIDS folder")
        elif io != "File exists":
            raise ge.CommandFailed(
                "import_bids",
                "I/O error: %s" % (io),
                "Could not create BIDS inbox [%s]!" % (bidsinbox),
                "Please check paths and permissions!",
            )

    bidsarchive = os.path.join(sessionsfolder, "archive", "BIDS")
    if not os.path.exists(bidsarchive):
        io = fl.makedirs(bidsarchive)
        if not io:
            print("---> created BIDS archive folder")
        elif io != "File exists":
            raise ge.CommandFailed(
                "import_bids",
                "I/O error: %s" % (io),
                "Could not create BIDS archive [%s]!" % (bidsarchive),
                "Please check paths and permissions!",
            )

    # --- load BIDS structure
    # template folder
    niuTemplateFolder = os.environ["NIUTemplateFolder"]
    bidsStructure = os.path.join(niuTemplateFolder, "import_bids.txt")

    if not os.path.exists(bidsStructure):
        raise ge.CommandFailed(
            "import_bids",
            "No BIDS structure file present!",
            "There is no BIDS structure file %s" % (bidsStructure),
            "Please check your QuNex installation",
        )

    bids_file = open(bidsStructure)
    content = bids_file.read()
    bids = ast.literal_eval(content)

    # ---> identification of files
    print("---> identifying files in %s" % (inbox))

    sourceFiles = []
    processAll = True
    select = None

    if os.path.exists(inbox):
        if os.path.isfile(inbox):
            sourceFiles = [inbox]
            folderType = "file"
            if sessions:
                select = [
                    e.strip().replace("sub-", "").replace("ses-", "").replace("/", "_")
                    for e in re.split(r" +|\| *|, *", sessions)
                ]

        elif os.path.isdir(inbox):
            # -- figure out, where we are
            basename = os.path.basename(inbox)
            if "sub-" in basename:
                folderType = "subject"
            elif "ses-" in basename:
                folderType = "session"
            elif glob.glob(os.path.join(inbox, "sub-*")):
                folderType = "bids_study"
            else:
                folderType = "inbox"

            print("---> Inbox type:", folderType)

            # -- process sessions
            globfor = {
                "subject": "*",
                "session": "*",
                "bids_study": "sub-*",
                "inbox": "*",
            }

            if sessions:
                processAll = False
                sessions = [e.strip() for e in re.split(r" +|\| *|, *", sessions)]
                if folderType == "bids_study":
                    nsessions = []
                    for session in sessions:
                        if "sub-" in session:
                            nsessions.append(session.replace("_", "/"))
                        elif "_" in session:
                            nsessions.append(
                                "sub-%s/ses-%s" % tuple(session.split("_"))
                            )
                        else:
                            nsessions.append("sub-" + session)
                    sessions = nsessions
                elif folderType == "subject":
                    nsessions = []
                    for session in sessions:
                        if "ses-" in session:
                            nsessions.append(session)
                        elif "_" in session:
                            nsessions.append("ses-%s" % (session.split("_")[1]))
                        else:
                            nsessions.append("ses-" + session)
                    sessions = nsessions
            else:
                sessions = [globfor[folderType]]

            # --- check for metadata
            studyat = {"subject": -1, "session": -2}
            metadata = [
                "dataset_description.json",
                "README",
                "CHANGES",
                "participants.*",
            ]
            metadata += ["%s/*" % (e) for e in bids["optional"]]

            if folderType in studyat:
                metadataPath = os.path.join(
                    "/", *inbox.split(os.path.sep)[: studyat[folderType]]
                )
            else:
                metadataPath = inbox

            mcandidates = []
            for m in metadata:
                mcandidates += glob.glob(os.path.join(metadataPath, m))

            for mcandidate in mcandidates:
                if os.path.isfile(mcandidate):
                    sourceFiles.append(mcandidate)
                elif os.path.isdir(mcandidate):
                    for path, dirs, files in os.walk(mcandidate):
                        for file in files:
                            sourceFiles.append(os.path.join(path, file))

            # --- compile candidates
            candidates = []
            for e in sessions:
                candidates += glob.glob(os.path.join(inbox, e) + "*")
            for candidate in candidates:
                if os.path.isfile(candidate):
                    sourceFiles.append(candidate)
                elif os.path.isdir(candidate):
                    for path, dirs, files in os.walk(candidate):
                        for file in files:
                            sourceFiles.append(os.path.join(path, file))
        else:
            raise ge.CommandFailed(
                "import_bids",
                "Invalid inbox",
                "%s is neither a file or a folder!" % (inbox),
                "Please check your path!",
            )
    else:
        raise ge.CommandFailed(
            "import_bids",
            "Inbox does not exist",
            "The specified inbox [%s] does not exist!" % (inbox),
            "Please check your path!",
        )

    if not sourceFiles:
        raise ge.CommandFailed(
            "import_bids",
            "No files found",
            "No files were found to be processed at the specified inbox [%s]!"
            % (inbox),
            "Please check your path!",
        )

    # ---> definition of paths
    if bidsname is None:
        if os.path.samefile(inbox, os.path.join(sessionsfolder, "inbox", "BIDS")):
            bidsname = ""
    else:
        if folderType == "file":
            bidsname = os.path.basename(inbox)
            bidsname = re.sub(".zip$|.gz$|.tgz$", "", bidsname)
            bidsname = re.sub(".tar$", "", bidsname)
        elif folderType in ["inbox", "bids_study"]:
            bidsname = os.path.basename(inbox)
        elif folderType in ["subject", "session"]:
            bidsname = inbox.split(os.path.sep)[studyat[folderType] - 1]

    if not bidsname:
        bidsinfo = os.path.join(qxfolders["basefolder"], "info", "bids")
    else:
        bidsinfo = os.path.join(qxfolders["basefolder"], "info", "bids", bidsname)

    print("---> Paths:")
    print("    bidsinfo    ->", bidsinfo)
    print("    bidsinbox   ->", bidsinbox)
    print("    bidsarchive ->", bidsarchive)

    # ---> mapping data to sessions' folders
    print("---> mapping files to QuNex bids folders")
    for file in sourceFiles:
        if file.endswith(".zip"):
            print("    ---> processing zip package [%s]" % (file))

            try:
                z = zipfile.ZipFile(file, "r")
                for sf in z.infolist():
                    if sf.filename[-1] != "/":
                        tfile, lock = mapToQUNEXBids(
                            sf.filename,
                            sessionsfolder,
                            bidsinfo,
                            sessionsList,
                            overwrite,
                            "        ",
                            select,
                        )
                        if tfile:
                            if lock:
                                fl.lock(tfile)
                            fdata = z.read(sf)
                            if tfile.endswith(".nii"):
                                tfile += ".gz"
                                fout = gzip.open(tfile, "wb")
                            else:
                                fout = open(tfile, "wb")
                            fout.write(fdata)
                            fout.close()
                            if lock:
                                fl.unlock(tfile)
                z.close()
                print("        -> done!")
            except:
                print(
                    "        => Error: Processing of zip package failed. Please check the package!"
                )
                errors += "\n    .. Processing of package %s failed!" % (file)
                raise

        elif ".tar" in file or ".tgz" in file:
            print("   ---> processing tar package [%s]" % (file))

            try:
                tar = tarfile.open(file)
                for member in tar.getmembers():
                    if member.isfile():
                        tfile, lock = mapToQUNEXBids(
                            member.name,
                            sessionsfolder,
                            bidsinfo,
                            sessionsList,
                            overwrite,
                            "        ",
                            select,
                        )
                        if tfile:
                            if lock:
                                fl.lock(tfile)
                            fobj = tar.extractfile(member)
                            fdata = fobj.read()
                            fobj.close()
                            if tfile.endswith(".nii"):
                                tfile += ".gz"
                                fout = gzip.open(tfile, "wb")
                            else:
                                fout = open(tfile, "wb")
                            fout.write(fdata)
                            fout.close()
                            if lock:
                                fl.unlock(tfile)
                tar.close()
                print("        -> done!")
            except:
                print(
                    "        => Error: Processing of tar package failed. Please check the package!"
                )
                errors += "\n    .. Processing of package %s failed!" % (file)

        else:
            tfile, lock = mapToQUNEXBids(
                file, sessionsfolder, bidsinfo, sessionsList, overwrite, "    "
            )
            if tfile:
                if tfile.endswith(".nii"):
                    tfile += ".gz"
                    status, msg = gc.moveLinkOrCopy(
                        file, tfile, "gzip", r="", prefix="    .. ", lock=lock
                    )
                else:
                    feedback = gc.moveLinkOrCopy(
                        file, tfile, action, r="", prefix="    .. ", lock=lock
                    )
                    status, msg = feedback

                allOk = allOk and status
                if not status:
                    errors += msg

    # ---> close status file
    if sessionsList["bids"] == "open":
        fl.write_status(
            os.path.join(bidsinfo, "bids_info_status"),
            "Processing done on %s."
            % (datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            "a",
        )

    # ---> archiving the dataset
    if errors:
        print("   ---> The following errors were encountered when mapping the files:")
        print(errors)
    else:
        archiveList = []

        # ---> review what to archive
        # -> we're archiving a file
        if os.path.isfile(inbox):
            archiveList = [inbox]
            folderType = "file"

        # -> we're archiving fully processed inbox folder
        elif processAll:

            # -> from bidsinbox
            if os.path.samefile(inbox, bidsinbox):
                archiveList = glob.glob(os.path.join(inbox, "*"))

            # -> from external inbox location
            else:
                archiveList = [inbox]

        # -> we're archiving partially processed inbox folder
        else:
            archiveList = candidates

        # ---> archive
        if archive in ["move", "copy", "delete"]:
            print("---> Archiving: %sing items" % (archive.replace("y", "yy")[:-1]))

        # -> prepare target folder
        if archive in ["move", "copy"]:
            if folderType == "file":
                archiveFolder = bidsarchive
            elif folderType in ["inbox", "bids_study"]:
                if os.path.samefile(inbox, bidsinbox):
                    archiveFolder = bidsarchive
                else:
                    archiveFolder = os.path.join(bidsarchive, os.path.basename(inbox))
            else:
                if os.path.samefile(inbox, bidsinbox):
                    archiveFolder = os.path.join(
                        bidsarchive, *inbox.split(os.path.sep)[studyat[folderType] :]
                    )
                else:
                    archiveFolder = os.path.join(
                        bidsarchive,
                        *inbox.split(os.path.sep)[studyat[folderType] - 1 :],
                    )

        # -> loop through items
        for archiveItem in archiveList:

            # -> delete items
            if archive == "delete":
                if os.path.isfile(archiveItem):
                    io = fl.remove(archiveItem)
                else:
                    io = fl.rmtree(archiveItem)
                if io and io != "No such file or directory":
                    print(
                        "    WARNING: Could not remove %s. Please check permissions!"
                        % (archiveItem)
                    )

            # -> move or copy items
            if archive in ["move", "copy"]:
                targetItem = archiveItem.replace(inbox, "")
                targetItem = re.sub(r"^%s+" % (os.path.sep), "", targetItem)
                archiveTarget = os.path.join(archiveFolder, targetItem)
                archiveTargetFolder = os.path.dirname(archiveTarget)

                # print("---> Archive folder:", archiveFolder)
                # print("---> Archive item:", targetItem)
                # print("---> Archive target:", archiveTarget)

                io = fl.makedirs(archiveTargetFolder)
                if io and io != "File exists":
                    print(
                        "    WARNING: Could not create archive folder %s. Skipping archiving. Please check permissions!"
                        % (archiveTargetFolder)
                    )
                    archiveTargetFolder = None

                fl.lock(archiveTarget)
                try:
                    if archive == "move":
                        shutil.move(archiveItem, archiveTargetFolder)
                    else:
                        if os.path.isfile(archiveItem):
                            shutil.copy2(archiveItem, archiveTargetFolder)
                        else:
                            if os.path.exists(archiveTarget):
                                shutil.rmtree(archiveTarget)
                            shutil.copytree(archiveItem, archiveTarget)
                except:
                    print(
                        "    WARNING: Could not %s %s. Please check permissions!"
                        % (archive, archiveItem)
                    )
                fl.unlock(archiveTarget)

    # ---> mapping data to QuNex nii and behavioral folder
    # -> check study level data
    if sessionsList["bids"] == "locked":
        BIDSInfoStatus = fl.wait_status(
            os.path.join(bidsinfo, "bids_info_status"), "done"
        )
        if BIDSInfoStatus != "done":
            print(
                "---> WARNING: Status of behavioral files is unknown! Please check the data!"
            )

    # ---> get a list of behavioral data:
    behavior = []
    behavior += glob.glob(os.path.join(bidsinfo, "participants.tsv"))
    behavior += glob.glob(os.path.join(bidsinfo, "phenotype/*.tsv"))

    # ---> run the mapping
    report = []
    for execute in ["map", "clean"]:
        for session in sessionsList[execute]:
            if session != "bids":

                subject = session.split("_")[0]
                sessionid = (session.split("_") + [""])[1]
                info = "subject " + subject
                if sessionid:
                    info += ", session " + sessionid

                print

                # -- do image mapping
                try:
                    map_bids2nii(
                        os.path.join(sessionsfolder, session),
                        overwrite=overwrite,
                        fileinfo=fileinfo,
                        add_json_info=add_json_info
                    )
                    nmapping = True
                except ge.CommandFailed as e:
                    print("---> WARNING:\n     %s\n" % ("\n     ".join(e.report)))
                    nmapping = False

                # -- do behavioral mapping
                try:
                    bmapping = mapBIDS2behavior(
                        os.path.join(sessionsfolder, session), behavior, overwrite
                    )
                except ge.CommandFailed as e:
                    print("---> WARNING:\n     %s\n" % ("\n     ".join(e.report)))
                    bmapping = False

                # -- compile report
                if nmapping:
                    minfo = info + " image mapping completed"
                else:
                    minfo = info + " image mapping failed"
                    allOk = False

                if bmapping:
                    minfo += ", behavioral files: "
                    binfo = []
                    if bmapping["mapped"]:
                        binfo.append("%d files mapped" % (len(bmapping["mapped"])))
                    else:
                        binfo.append("no files mapped")

                    if bmapping["invalid"]:
                        binfo.append("%d files invalid" % (len(bmapping["invalid"])))
                        # allOk = False
                    minfo += ", ".join(binfo)
                else:
                    minfo += ", behavior file mapping failed"
                    # allOk = False

                report.append(minfo)

    print("\nFinal report\n============")

    for line in report:
        print(line)

    if not allOk:
        raise ge.CommandFailed(
            "import_bids", "Some actions failed", "Please check report!"
        )

    if not report:
        raise ge.CommandNull(
            "import_bids", "No sessions were mapped in this call. Please check report!"
        )


def processBIDS(bfolder):
    """ """

    bidsData = {}
    sourceFiles = []

    if os.path.exists(bfolder):
        for path, dirs, files in os.walk(bfolder):
            for file in files:
                sourceFiles.append(os.path.join(path, file))
    else:
        raise ge.CommandFailed(
            "processBIDS",
            "No bids folder present!",
            "There is no bids data in session folder %s" % (bfolder),
            "Please import BIDS data first!",
        )

    # --- load BIDS structure
    # template folder
    niuTemplateFolder = os.environ["NIUTemplateFolder"]
    bidsStructure = os.path.join(niuTemplateFolder, "import_bids.txt")

    if not os.path.exists(bidsStructure):
        raise ge.CommandFailed(
            "processBIDS",
            "No BIDS structure file present!",
            "There is no BIDS structure file %s" % (bidsStructure),
            "Please check your QuNex installation",
        )

    bids_file = open(bidsStructure)
    content = bids_file.read()
    bids = ast.literal_eval(content)

    # -> map all the files
    for sfile in sourceFiles:
        parts = re.split(r"_|/|\.", sfile)

        # ---> is it optional content
        optional = [e for e in parts if e in bids["optional"]]
        if optional:
            optional = optional[0]

        # ---> get session ID
        subject = [e.split("-")[1] for e in parts if e.startswith("sub-")] + [""]
        session = [e.split("-")[1] for e in parts if e.startswith("ses-")] + [""]
        session = "_".join([e for e in [subject[0], session[0]] if e])
        if not session:
            session = "study"

        if session not in bidsData:
            bidsData[session] = {}

        # ---> get and process .json file
        sidecar, sideinfo = None, None
        filename = os.path.basename(sfile)
        filedir = os.path.dirname(sfile)
        fileroot = filename.split(".")[0]
        for ext in [".json", ".JSON"]:
            if os.path.exists(os.path.join(filedir, fileroot + ext)):
                sidecar = os.path.join(filedir, fileroot + ext)
                with open(sidecar) as json_file:
                    sideinfo = json.load(json_file)

        # ---> get modality
        modality = [e for e in parts if e in bids["modalities"]]
        if modality:
            modality = modality[0]
            if modality not in bidsData[session]:
                bidsData[session][modality] = []

            info = dict(
                zip(
                    bids[modality]["info"],
                    [None for e in range(len(bids[modality]["info"]))],
                )
            )
            info.update(
                dict(
                    [
                        (i, part.split("-")[1])
                        for part in parts
                        for i in bids[modality]["info"]
                        if "-" in part and i == part.split("-")[0]
                    ]
                )
            )
            info["filepath"] = sfile
            info["filename"] = filename
            info["label"] = (
                [None] + [part for part in parts if part in bids[modality]["label"]]
            )[-1]
            info["json_file"] = sidecar
            info["json_info"] = sideinfo

            bidsData[session][modality].append(info)
        else:
            bidsData[session]["files"] = {
                "filepath": sfile,
                "filename": filename,
                "json_file": sidecar,
                "json_info": sideinfo,
            }

    # ---> sort within modalities
    _sort_bids_images(bidsData, bids)

    # ---> prepare and sort images
    for session in bidsData:
        bidsData[session]["images"] = {"list": [], "info": {}}
        imgn = 0
        for modality in ["anat", "fmap", "func", "dwi", "asl"]:
            if modality in bidsData[session]:
                for element in bidsData[session][modality]:
                    if ".nii" in element["filename"]:
                        imgn += 1
                        bidsData[session]["images"]["list"].append(element["filename"])
                        element["tag"] = " ".join(
                            [
                                "%s-%s" % (e, element[e])
                                for e in bids[modality]["tag"]
                                if element[e]
                            ]
                        )
                        element["tag"] = element["tag"].replace("label-", "")
                        element["tag"] = element["tag"].replace("task-", "")
                        element["imgn"] = imgn
                        bidsData[session]["images"]["info"][
                            element["filename"]
                        ] = element

    # ---> process fieldmap matching
    for session in bidsData:
        for element in bidsData[session].get("fmap", []):
            if ".nii" in element["filename"]:

                # ---> is fieldmap a spin-echo type or a "regular" fieldmap?
                if element["label"] == "epi":
                    fmtype = "se"
                else:
                    fmtype = "fm"

                # ---> is there a run information or is there just a single fieldmap
                if element["run"] is None:
                    fmindex = 1
                else:
                    fmindex = element["run"]

                tag = f"{fmtype}({fmindex})"

                # ---> add a tag to the fieldmap image
                bidsData[session]["images"]["info"][element["filename"]]["seq_info"] = (
                    bidsData[session]["images"]["info"][element["filename"]].get(
                        "seq_info", []
                    )
                    + [tag]
                )
                if (
                    "json_info" in element
                    and element["json_info"]
                    and "IntendedFor" in element["json_info"]
                ):
                    if isinstance(element["json_info"]["IntendedFor"], str):
                        target_files = [element["json_info"]["IntendedFor"]]
                    else:
                        target_files = element["json_info"]["IntendedFor"]
                    for target_file in target_files:
                        target_file = os.path.basename(target_file)
                        bidsData[session]["images"]["info"][target_file]["seq_info"] = (
                            bidsData[session]["images"]["info"][target_file].get(
                                "seq_info", []
                            )
                            + [tag]
                        )

    return bidsData


def _label_order(label_list, value):
    """
    Returns the index of `value` in the `label_list`

    If value is `None`, the function will return -1.
    Caller should guarantee that if value is not `None`
    it exists in the label_list.
    """
    if value is None:
        return -1
    else:
        return label_list.index(value)


def _sort_bids_images(bidsData, bids):
    """
    Sort bids images as defined in the bids template

    Labels are sorted in the order they appear in the template instead of alphabetical order.
    """
    for session in bidsData:
        for modality in bids["modalities"]:
            if modality in bidsData[session]:
                for key in bids[modality]["sort"]:
                    if key == "label":
                        bidsData[session][modality].sort(
                            key=lambda x: _label_order(bids[modality]["label"], x[key])
                        )
                    else:
                        bidsData[session][modality].sort(key=lambda x: x[key] or "")


def map_bids2nii(sourcefolder='.', overwrite='no', fileinfo=None, add_json_info='all'):
    """
    ``map_bids2nii [sourcefolder='.'] [overwrite='no'] [fileinfo='short'] [add_json_info='all']``

    Maps data organized according to BIDS specification to `nii` folder 
    structure as expected by QuNex commands.

    Warning:
        File order:
            The files are ordered according to best guess sorted primarily by
            modality. This can be problematic for further HCP processing when
            different fieldmap files are used for different BOLD and structural
            files. In the future version the files will be organized so that
            fieldmaps will precede the files to which they correspond,
            according to HCP processing expectations.

        .bvec and .bval files:
            `.bvec` and `.bval` files are expected to be present along with dwi
            files in each session folder. If they are only present in the main
            folder, they are currently not mapped to the `.nii` folder.

        Image format:
            The function assumes that all the images are saved as `.nii.gz`
            files!

    Parameters:
        --sourcefolder (str, default '.'):
            The base session folder in which bids folder with data and files for
            the session is present.

        --overwrite (str, default 'no'):
            Parameter that specifies what should be done in cases where there
            are existing data stored in `nii` folder.
            The options are:

            - 'no'  ... do not overwrite the data, skip session
            - 'yes' ... remove existing files in `nii` folder and redo the
              mapping.

        --fileinfo (str, default 'short'):
            What file information to include in the session.txt file. Options
            are:

            - 'short' ... only provide the short description based on the
              identified BIDS tags
            - 'full' ... list the full file name excluding the
              participant id, session name and extension.

        --add_json_info (str, default 'all'):
            A comma or space separated string, listing which info present in 
            `.json` sidecar files to include in the sequence information. 
            Options are:

            - phenc ... phase encoding direction
            - DwellTime
            - UnwarpDir ... unwarp direction
            - EchoSpacing
            - 'all' ... all of the above listed information, if present in 
              the `.json` sidecar file.

    Output files:
        After running the mapped nifti files will be in the `nii` subfolder,
        named with sequential image number. `session.txt` will be in the
        base session folder and `bids2nii.log` will be in the `bids`
        folder.

        session.txt file:
            The session.txt will be placed in the session base folder. It
            will contain the information about the session id, subject id
            location of folders and a list of created NIfTI images with
            their description.

            An example session.txt file would be::

                id: 06_retest
                subject: 06
                bids: /Volumes/tigr/MBLab/fMRI/bidsTest/sessions/06_retest/bids
                raw_data: /Volumes/tigr/MBLab/fMRI/bidsTest/sessions/06_retest/nii
                hcp: /Volumes/tigr/MBLab/fMRI/bidsTest/sessions/06_retest/hcp

                01: T1w
                02: bold covertverbgeneration
                03: bold fingerfootlips
                04: bold linebisection
                05: bold overtverbgeneration
                06: bold overtwordrepetition
                07: dwi

            For each of the listed images there will be a corresponding
            NIfTI file in the nii subfolder (e.g. 04.nii.gz for the line
            bisection BOLD sequence). The generated session.txt files form
            the basis for the following HCP and other processing steps.
            `id` field will be set to the full session name, `subject` will
            be set to the text preceeding the underscore (`_`) character.

        bids2nii.log file:
            The `bids2nii.log` provides the information about the date and
            time the files were mapped and the exact information about
            which specific file from the `bids` folder was mapped to which
            file in the `nii` folder.

    Notes:
        The command is used to map data organized according to BIDS
        specification, residing in `bids` session subfolder to `nii` folder
        as expected by QuNex functions. The command checks the imaging data
        and compiles a list in the following order:

        - anatomical images
        - fieldmap images
        - functional images
        - diffusion weighted images.

        Once the list is compiled, the files are mapped to `nii` folder to
        files named by ordinal number of the image in the list. To save
        space, files are not copied but rather hard links are created. Only
        image, bvec and bval files are mapped from the `bids` to `nii`
        folder. The exact mapping is noted in file `bids2nii.log` that is
        saved to the `bids` folder. The information on images is also
        compiled in `session.txt` file that is generated in the main
        session folder. For every image all the information present in the
        bids filename is listed.

        Multiple sessions and scheduling:
            The command can be run for multiple sessions by specifying
            `sessions` and optionally `sessionsfolder` and `parsessions`
            parameters. In this case the command will be run for each of
            the specified sessions in the sessionsfolder (current directory
            by default). Optional `filter` and `sessionids` parameters can
            be used to filter sessions or limit them to just specified id
            codes. (for more information see online documentation).
            `sourcefolder` will be filled in automatically as each
            session's folder. Commands will run in parallel where the
            degree of parallelism is determined by `parsessions` (1 by
            default).

            If `scheduler` parameter is set, the command will be run using
            the specified scheduler settings (see `qunex ?schedule` for
            more information). If set in combination with `sessions`
            parameter, sessions will be processed over multiple nodes,
            `core` parameter specifying how many sessions to run per node.
            Optional `scheduler_environment`, `scheduler_workdir`,
            `scheduler_sleep`, and `nprocess` parameters can be set.

            Set optional `logfolder` parameter to specify where the
            processing logs should be stored. Otherwise the processor will
            make best guess, where the logs should go.

            Do note that as this command only performs file mapping and no
            image or file processing, the best performance might be
            achieved by running on a single node and a single core.

    Examples:
        ::

            qunex map_bids2nii \\
                --folder=. \\
                --overwrite=yes
    """

    if fileinfo is None:
        fileinfo = "short"

    if fileinfo not in ["short", "full"]:
        raise ge.CommandError(
            "map_bids2nii",
            "Invalid fileinfo option",
            "%s is not a valid option for fileinfo parameer!" % (fileinfo),
            "Please specify one of: short, full!",
        )

    sfolder = os.path.abspath(sourcefolder)
    bfolder = os.path.join(sfolder, "bids")
    nfolder = os.path.join(sfolder, "nii")

    session = os.path.basename(sfolder)
    subject = session.split("_")[0]
    sessionid = (session.split("_") + [""])[1]

    add_json_info = [e.strip() for e in add_json_info.replace(",", " ").split()]
    add_json_info = [e for e in add_json_info if len(e) > 0]
    if "all" in add_json_info:
        add_json_info = list(set(add_json_info + json_all))

    info = "subject " + subject
    if sessionid:
        info += ", session " + sessionid

    splash = "Running map_bids2nii for %s" % (info)
    print(splash)
    print("".join(["=" for e in range(len(splash))]))

    if overwrite not in ["yes", "no"]:
        raise ge.CommandError(
            "map_bids2nii",
            "Invalid option for overwrite specified",
            "%s is not a valid option for the overwrite parameter!" % (overwrite),
            "Please specify one of: yes, no!",
        )

    # --- process bids folder

    bidsData = processBIDS(bfolder)

    if session not in bidsData:
        raise ge.CommandFailed(
            "map_bids2nii",
            "Unrecognized session!",
            "This folder [%s] does not have a valid matching BIDS session!" % (sfolder),
            "Please check your data!",
        )

    bidsData = bidsData[session]

    if not bidsData["images"]["list"]:
        raise ge.CommandFailed(
            "map_bids2nii",
            "No image files in bids folder!",
            "There are no image files in the bids folder [%s]" % (bfolder),
            "Please check your data!",
        )

    # --- check for presence of nifti files

    if os.path.exists(nfolder):
        nfiles = len(glob.glob(os.path.join(nfolder, "*.nii*")))
        if nfiles > 0:
            if overwrite == "no" or overwrite is False:
                raise ge.CommandFailed(
                    "map_bids2nii",
                    "Existing files present!",
                    "There are existing files in the nii folder [%s]" % (nfolder),
                    "Please check or set parameter 'overwrite' to yes!",
                )
            else:
                shutil.rmtree(nfolder)
                os.makedirs(nfolder)
                print("---> cleaned nii folder, removed existing files")
    else:
        os.makedirs(nfolder)

    # --- create session.txt file
    sout = gc.createSessionFile("map_bids2nii", sfolder, session, subject, overwrite)

    # --- open bids2nii log file
    if overwrite == "yes" or overwrite is True:
        mode = "w"
    else:
        mode = "a"

    bout = open(os.path.join(bfolder, "bids2nii.log"), mode)
    print(
        "BIDS to nii mapping report, executed on %s"
        % (datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
        file=bout,
    )

    # --- map files

    allOk = True

    for image in bidsData["images"]["list"]:

        imgn = bidsData["images"]["info"][image]["imgn"]
        tfile = os.path.join(nfolder, "%d.nii.gz" % (imgn))

        status = gc.moveLinkOrCopy(
            bidsData["images"]["info"][image]["filepath"], tfile, action="link"
        )
        if bidsData["images"]["info"][image]["json_file"]:
            status = status & gc.moveLinkOrCopy(
                bidsData["images"]["info"][image]["json_file"],
                os.path.join(nfolder, "%d.json" % (imgn)),
                action="link",
            )
        if status:
            print(
                "---> linked %d.nii.gz <-- %s"
                % (imgn, bidsData["images"]["info"][image]["filename"])
            )

            # ---> check if there is sequence info present
            seq_info = ":".join(bidsData["images"]["info"][image].get("seq_info", []))
            if seq_info:
                seq_info = ":" + seq_info

            # ---> check if there is json info present
            json_info = []
            json_data = bidsData["images"]["info"][image].get("json_info", None)
            if json_data and add_json_info:
                for ji in add_json_info:
                    if ji in json_mapping:
                        if json_mapping[ji][0] in json_data:
                            json_info.append(
                                f"{ji}({json_mapping[ji][1](json_data[json_mapping[ji][0]])})"
                            )
                    elif ji in json_data:
                        json_info.append(f"{ji}({json_data[ji]})")
            if json_info:
                json_info = ":" + ":".join(json_info)
            else:
                json_info = ""

            # ---> compile file information
            if fileinfo == "short":
                file_info = bidsData["images"]["info"][image]["tag"]
            elif fileinfo == "full":
                file_info = (
                    bidsData["images"]["info"][image]["filename"]
                    .replace(".nii.gz", "")
                    .replace("sub-%s_" % (subject), "")
                    .replace("ses-%s_" % (sessionid), "")
                )

            # ---> print info to session.txt
            print(f"{imgn}: {file_info} {seq_info} {json_info}", file=sout)

            print(
                "%s => %s" % (bidsData["images"]["info"][image]["filepath"], tfile),
                file=bout,
            )
        else:
            allOk = False
            print(
                "---> ERROR: Linking failed: %d.nii.gz <-- %s"
                % (imgn, bidsData["images"]["info"][image]["filename"])
            )
            print(
                "FAILED: %s => %s"
                % (bidsData["images"]["info"][image]["filepath"], tfile),
                file=bout,
            )

        status = True
        if bidsData["images"]["info"][image]["label"] == "dwi":
            sbvec = bidsData["images"]["info"][image]["filepath"].replace(
                ".nii.gz", ".bvec"
            )
            tbvec = tfile.replace(".nii.gz", ".bvec")
            if gc.moveLinkOrCopy(sbvec, tbvec, action="link"):
                print("%s => %s" % (sbvec, tbvec), file=bout)
            else:
                status = False

            sbval = bidsData["images"]["info"][image]["filepath"].replace(
                ".nii.gz", ".bval"
            )
            tbval = tfile.replace(".nii.gz", ".bval")
            if gc.moveLinkOrCopy(sbval, tbval, action="link", status=status):
                print("%s => %s" % (sbval, tbval), file=bout)
            else:
                status = False

            if not status:
                print(
                    "---> WARNING: bval/bvec files were not found and were not mapped for %d.nii.gz [%s]!"
                    % (
                        imgn,
                        bidsData["images"]["info"][image]["filename"].replace(
                            ".nii.gz", ".bval/.bvec"
                        ),
                    ),
                    file=bout,
                )
                print(
                    "---> ERROR: bval/bvec files were not found and were not mapped: %d.bval/.bvec <-- %s"
                    % (
                        imgn,
                        bidsData["images"]["info"][image]["filename"].replace(
                            ".nii.gz", ".bval/.bvec"
                        ),
                    )
                )
                allOk = False

    sout.close()
    bout.close()

    if not allOk:
        raise ge.CommandFailed(
            "map_bids2nii",
            "Not all actions completed successfully!",
            "Some files for session %s were not mapped successfully!" % (session),
            "Please check logs and data!",
        )


def map_nii2bids(sinfo, options, overwrite=False, action='hardlink', session_mapping_file=None):
    """
    ``map_nii2bids [batchfile=''] [sessionsfolder='.'] [sessions=''] [overwrite='no'] [action='hardlink'] [session_mapping_file=None]``

    Maps data from the `nii` folder to the `bids` folder. Requires
    `session_hcp.txt` files. Entities (key-value) pairs should be specified by
    the user in `hcp_mapping.txt` file and `session_hcp.txt` should be created
    using the `create_session_info` function. Suffix is inferred from data, but
    can be specified manually in case of ambiguity (e.g. for fieldmaps).

    In case session name contains non-alphanumeric characters, these characters
    will be replaced with 'x' in the BIDS session name.

    See examples below for details.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --sessions (str, ''):
            The comma separated list of sessions to process. If not specified,
            all sessions will be processed.

        --overwrite (str, default 'no'):
            Parameter that specifies what should be done in cases where there
            are existing data stored in `nii` folder.
            The options are:

            - 'no'  ... do not overwrite the data, skip session
            - 'yes' ... remove existing files in `bids` folder and redo the
              mapping.

        --action (str, default 'hardlink'):
            The type of link that should be used for linking the files from
            `nii` to `bids` folder. The options are:

            - 'hardlink' ... use hard links to link the files
            - 'copy'     ... copy the files to the `bids` folder

        --session_mapping_file (str, default None):
            The path to the session mapping file in yaml format. Can be used for
            cases where original session name is not BIDS compliant, see example
            below. If not specified, the mapping will be done based on the
            session name.

    Examples:

        We have session_hcp.txt with following content::

            session: 01_1
            subject: 01
            ...
            7   :FM-Magnitude    :FM magnitude2: run(2): fm(2): suffix(magnitude2)
            ...
            11  :bold3:rest      : acq(fullbrain): run(2): fm(2)

        We run the following command::

            qunex map_nii2bids \
              --sourcefolder="/data/studies/fMRI/import_bids_test/sessions/01_1" \
              --overwrite='yes'

        In this example, the following mappings are performed:

        - 7.nii.gz --> `sub-01_ses-1_run-2_magnitude2.nii.gz`

        Note that the suffix has been explicitly defined as `magnitude2`,
        otherwise it would implicitly be set to `magnitude`.

        - `11.nii.gz` --> `sub-01_ses-1_task-rest_acq-fullbrain_run-1_bold.nii.gz`

        In this case suffix was inferred from the image type. Key-value pairs
        not defined in BIDS are ignored (e.g. `fm` in the above case)

        Note that optional BIDS entities (e.g. acq and run) should be specified
        manually as key-value pairs in hcp_mapping.txt.

        If the session name contains non-alphanumeric characters, they will be
        replaced with 'x' in the BIDS session name. However, if the session
        name is specified in the session_mapping_file, the session name will be
        remapped according to the mapping file.

        Session mapping file example::

            '01':
              '01_1': 'first'
              '01_2': 'second'

        In this case, subject name is '01' and session name is '01_1'. The session
        name will be remapped to 'first' according to the session_mapping_file,
        and the BIDS session name will be 'sub-01_ses-first'.

    """
    
    if 'action' in options:
        action = options['action']
    if action not in ['hardlink', 'copy']:
        raise ge.CommandError("map_nii2bids", "Invalid option for action specified",
                              "%s is not a valid option for the action parameter!" % (action),
                              "Please specify one of: hardlink, copy!")

    if 'session_mapping_file' in options:
        session_mapping_file = options['session_mapping_file']

    if session_mapping_file is not None:
        remaps = yaml.safe_load(open(session_mapping_file))
        print(f"Session mapping file {session_mapping_file} loaded")
    else:
        remaps = {}

    for session_info in sinfo:
        bidsfolder = session_info['bids']
        sourcefolder = bidsfolder[:-5]
        niifolder = session_info['raw_data']

        # --- open nii2bids log file
        if overwrite in ['yes', True, 'True']:
            mode = 'w'
        else:
            mode = 'a'

        bout = open(os.path.join(bidsfolder, 'nii2bids.log'), mode)
        print("nii to BIDS mapping report, executed on %s" % (datetime.now().strftime("%Y-%m-%dT%H:%M:%S")), file=bout)

        session = session_info['session']
        subject = session_info['subject']
        print('', file=sys.stdout)
        [print(f'... mapping subject {subject}, session {session}', file=output) for output in [sys.stdout, bout]]
        if subject in remaps.keys():
            if session in remaps[subject].keys():
                sessionid = remaps[subject][session]
                if not sessionid.isalnum():
                    [print(f'... WARNING: session name contains non-alphanumeric characters, skipping', file=output) for output in [sys.stdout, bout]]
                    continue
                [print(f'... remapping session {session} to {sessionid}', file=output) for output in [sys.stdout, bout]]
            else:
                sessionid = session
        elif session == subject:
            sessionid = None
        else:
            replacement = 'x'
            sessionid = (session.split('_'))[1:]
            sessionid = replacement.join(sessionid)
            if not sessionid.isalnum():
                [print(f'... WARNING: session name contains non-alphanumeric characters, replacing them with {replacement}', file=output) for output in [sys.stdout, bout]]
                sessionid = re.sub(r'[^a-zA-Z0-9]', replacement, sessionid)

        # --- check for presence of nifti files
        if os.path.exists(bidsfolder):
            bidsfiles = len(glob.glob(os.path.join(bidsfolder, '*/*.nii*')))
            if bidsfiles > 0:
                if overwrite in ['yes', True, 'True']:
                    shutil.rmtree(bidsfolder)
                    os.makedirs(bidsfolder)
                    print("--> cleaned bids folder, removed existing files")
                else:
                    raise ge.CommandFailed("map_nii2bids", "Existing files present!", "There are existing files in the bids folder [%s]" % (bidsfolder), "Please check or set parameter 'overwrite' to yes!")
        else:
            os.makedirs(bidsfolder)

        # --- read session_hcp.txt file
        if os.path.exists(os.path.join(sourcefolder, 'session_hcp.txt')):
            print("... session_hcp.txt found, reading session info")
            session_info = gc.read_session_data(os.path.join(sourcefolder, 'session_hcp.txt'))[0][0]
        else:
            raise ge.CommandFailed("map_nii2bids", "session_hcp.txt is missing!", "Please prepare hcp_mapping.txt file and run create_session_info to prepare 'session_hcp.txt' files")


        # --- map files to BIDS
        images_ids = [i for i in session_info.keys() if i.isdigit()]

        dwi_count = len([i for i in images_ids if session_info[i]['name'] in ['dwi', 'DWI']])
        if dwi_count > 1:
            [print(f'... WARNING: Multiple DWI images found, set entity run or other relevant entities to ensure that file names are unique.', file=output) for output in [sys.stdout, bout]]

        errors = 0
        for image_id in images_ids:
            image_info = session_info[image_id]
            image_type = image_info['name']
            if image_type[:7] == 'boldref':
                image_type = 'boldref'
            elif image_type[:4] == 'bold':
                image_type = 'bold'
            elif image_type == '':
                [print(f'... ERROR: image type is empty for image {image_id}, skipping', file=output) for output in [sys.stdout, bout]]
                continue
            elif image_type not in bids_mri_types.keys():
                [print(f'... ERROR: image type {image_type} does not exists, skipping', file=output) for output in [sys.stdout, bout]]
                continue

            # create func, anat, fmap folders if needed
            targetfolder = os.path.join(bidsfolder, bids_mri_types[image_type]['folder'])
            if not os.path.exists(targetfolder):
                print(f'... creating folder {targetfolder}')
                os.makedirs(targetfolder)

            files_to_map = [filename for filename in os.listdir(niifolder) if filename.startswith(f'{image_id}.')]
            if len(files_to_map) == 0:
                [print(f'... WARNING: no files found for id: {image_id}, skipping', file=output) for output in [sys.stdout, bout]]
                continue

            if 'suffix' in image_info.keys():
                suffix = image_info['suffix']
            else:
                suffix = bids_mri_types[image_type]['suffix']

            for file_to_map in files_to_map:
                extension = '.'.join(file_to_map.split('.')[1::])
                bids_name, errors_ = _create_bids_name(subject, image_info, image_type, suffix, extension, sessionid, bout)
                errors += errors_

                if bids_name is None:
                    [print(f'... ERROR: could not create BIDS name for {file_to_map}, skipping', file=output) for output in [sys.stdout, bout]]
                    errors += 1
                    continue

                source_file = os.path.join(niifolder, file_to_map)
                target_file = os.path.join(targetfolder, bids_name)
                if os.path.exists(target_file):
                    [print(f'... WARNING: tried to map {file_to_map} to file {bids_name}, but this target already exists in {targetfolder}, check if mapping is unique', file=output) for output in [sys.stdout, bout]]
                    continue

                [print(f'... linking {file_to_map} to {os.path.basename(targetfolder)}/{bids_name}', file=output) for output in [sys.stdout, bout]]
                if action == 'hardlink':
                    os.link(source_file, target_file)
                elif action == 'copy':
                    shutil.copy(source_file, target_file)

        if errors > 0:
            raise ge.CommandFailed("map_nii2bids", "Errors during mapping", f"Errors occured during mapping, please check log file {os.path.join(bidsfolder, 'nii2bids.log')} for details")

        bout.close()


def _create_bids_name(subject, image_info, image_type, suffix, extension, sessionid=None, report=None):

    # prepare entities and rules
    bids_spec_path = os.path.join(os.environ['QUNEXPATH'], 'qx_library/etc/bids/')
    bids_schema = json.load(open(bids_spec_path + 'schema.json'))

    raw_rules = bids_schema['rules']['files']['raw'][bids_mri_types[image_type]['folder']]

    entities_order = bids_schema['rules']['entities']
    entities_description = bids_schema['objects']['entities']
    entities_short_names = {key: value['name'] for key, value in entities_description.items()}
    entities_format = {key: value['format'] for key, value in entities_description.items()}

    bids_name = f'sub-{subject}'
    if sessionid is not None:
        bids_name += f'_ses-{sessionid}'

    errors = 0

    if image_type in ['dwi', 'DWI'] and 'dir' not in image_info:
        image_info['dir'] = image_info.pop('task')[-2:]

    # check if extension is valid for this image type
    allowed_extensions = raw_rules[bids_mri_types[image_type]['subtype']]['extensions']
    allowed_extensions = [i[1:] for i in allowed_extensions if i[0] == '.'] # remove dot from extensions
    if extension not in allowed_extensions:
        [print(f'    ... ERROR: extension {extension} not allowed for {image_type}, skipping', file=output) for output in [sys.stdout, report]]
        errors += 1
        return (None, errors)

    # check if suffix is valid for this image type
    allowed_suffixes = raw_rules[bids_mri_types[image_type]['subtype']]['suffixes']
    if suffix not in allowed_suffixes:
        [print(f'    ... ERROR: suffix {suffix} not allowed for {image_type}, skipping', file=output) for output in [sys.stdout, report]]
        errors += 1
        return (None, errors)

    # rename 'phenc' to 'dir' for BIDS compatibility
    if 'phenc' in image_info:
        image_info['dir'] = image_info.pop('phenc')

    allowed_entities = raw_rules[bids_mri_types[image_type]['subtype']]['entities']
    for entity in entities_order:
        if entity in image_info:
            entity_value = image_info[entity]
        elif entities_short_names[entity] in image_info:
            entity_value = image_info[entities_short_names[entity]]
        elif image_type in ['SE-FM-PA', 'SE-FM-AP', 'SE-FM-RL', 'SE-FM-LR'] and entity == 'direction':
            entity_value = image_type.split('-')[-1]
        else:
            continue

        entity_key = entities_short_names[entity]
        if entity not in allowed_entities.keys():
            [print(f'    ... WARNING: entity {entity} not allowed for {image_type}', file=output) for output in [sys.stdout, report]]
            continue

        # check allowed characters in entity value
        entity_format = entities_format[entity]
        if entity_format == 'label' and not entity_value.isalnum():
            [print(f'    ... ERROR: value {entity_value} for entity {entity} is not alphanumeric for {image_type}, skipping', file=output) for output in [sys.stdout, report]]
            errors += 1
            continue
        if entity_format == 'index' and not entity_value.isdigit():
            [print(f'    ... ERROR: value {entity_value} for entity {entity} is not an integer for {image_type}, skipping', file=output) for output in [sys.stdout, report]]
            errors += 1
            continue

        bids_name += f'_{entity_key}-{entity_value}'

    # check if all required entities are present
    required_entities = [i for i in allowed_entities if allowed_entities[i] == 'required']
    for required_entity in required_entities:
        entity_key = entities_short_names[required_entity]
        if entity_key not in bids_name:
            [print(f'    ... ERROR: required entity {required_entity} not found for {image_type}, skipping', file=output) for output in [sys.stdout, report]]
            errors += 1
            return (None, errors)

    bids_name = f'{bids_name}_{suffix}.{extension}'

    return (bids_name, errors)


def mapBIDS2behavior(sfolder='.', behavior=[], overwrite='no'):
    """
    """

    # -- set up variables

    sfolder = os.path.abspath(sfolder)
    bfolder = os.path.join(sfolder, "behavior")

    session = os.path.basename(sfolder)
    subject = session.split("_")[0]
    sessionid = (session.split("_") + [""])[1]

    # -- print splash

    info = "subject " + subject
    if sessionid:
        info += ", session " + sessionid

    print
    splash = "Running mapBIDS2behavior for %s" % (info)
    print(splash)
    print("".join(["=" for e in range(len(splash))]))

    # -- map data

    report = {"mapped": [], "invalid": []}

    subjectid = "sub-" + subject
    if not os.path.exists(bfolder):
        print("---> created behavior subfolder")
        os.makedirs(bfolder)

    for bfile in behavior:
        outlines = []
        error = "Data for %s not found in file." % (subjectid)
        with open(bfile, "r") as f:
            first = True
            for line in f:
                line = line.strip()
                if first:
                    first = False
                    fields = line.split("\t")
                    if "participant_id" in fields:
                        sidcol = fields.index("participant_id")
                        outlines.append(line)
                    else:
                        error = "No 'participant_id' field in file."
                        break
                else:
                    values = line.split("\t")
                    if values[sidcol] == subjectid:
                        outlines.append(line)

        bfilename = os.path.basename(bfile)
        if len(outlines) >= 2:
            with open(os.path.join(bfolder, bfilename), "w") as ofile:
                for oline in outlines:
                    print(oline, file=ofile)
            print("---> mapped:", bfilename)
            report["mapped"].append(bfilename)
        elif len(outlines) < 2:
            print(
                "---> WARNING: Could not map %s! %s Please inspect file for validity!"
                % (bfilename, error)
            )
            report["invalid"].append(bfilename)
        else:
            print(
                "---> WARNING: Could not map %s! More than one line matching %s! Please inspect file for validity!"
                % (bfilename, subjectid)
            )
            report["invalid"].append(bfilename)

    return report
