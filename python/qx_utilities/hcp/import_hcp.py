#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``import_hcp.py``

Functions for importing HCP style data into QuNex:

--import_hcp      Maps HCP style data to QuNex structure.

The commands are accessible from the terminal using the gmri utility.
"""

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.


import ast
import glob
import json
import os
import os.path
import re
import shutil
import qx_utilities.general.exceptions as ge
import qx_utilities.general.core as gc
import qx_utilities.general.log as gl
import zipfile
import tarfile
from datetime import datetime
import yaml

unwarp = {
    None: "Unknown",
    "i": "x",
    "j": "y",
    "k": "z",
    "i-": "x-",
    "j-": "y-",
    "k-": "z-",
}
pe_dir_map = {
    "AP": "j-",
    "j-": "AP",
    "PA": "j",
    "j": "PA",
    "RL": "i",
    "i": "RL",
    "LR": "i-",
    "i-": "LR",
}


def map_to_qunex_cpls(
    file, sessionsfolder, hcplsname, sessions, overwrite, nameformat, _log=None
):
    """
    Identifies and returns the intended location of the file based on its name.

    A file whose name cannot be parsed records an error rather than printing
    one: `False` is also what this returns for a legitimate skip, so the
    caller's `if tfile:` cannot tell the two apart and the failure was
    invisible to the run's status.

    The `prefix` parameter this took is gone: `import_hcp` opens a
    `log.section` per package and the log spells the nesting.
    """
    log = gl.log_or_console(_log)

    try:
        if sessionsfolder[-1] == "/":
            sessionsfolder = sessionsfolder[:-1]
    except Exception:
        pass

    if "\\" in file:
        pathsep = "\\"
    else:
        pathsep = "/"

    # -- extract file info
    m = re.search(nameformat, file)

    try:
        subjid = m.group("subject_id")
        session = m.group("session_name")
        data = m.group("data").split(pathsep)
    except Exception:
        log.error("Could not parse file: %s" % (file))
        return False

    if any([e[0] == "." for e in [subjid, session] + data]):
        return False

    sessionid = subjid + "_" + session

    tfolder = os.path.join(sessionsfolder, sessionid, "hcpls")

    tfile = os.path.join(tfolder, os.sep.join(data))

    if sessionid in sessions["skip"]:
        return False
    elif sessionid not in sessions["list"]:
        sessions["list"].append(sessionid)
        if os.path.exists(tfolder):
            if overwrite == "yes" or overwrite is True:
                log.step(
                    "hcpls for session %s already exists: cleaning session"
                    % (sessionid)
                )
                shutil.rmtree(tfolder)
                sessions["clean"].append(sessionid)
            elif not os.path.exists(os.path.join(tfolder, "hcpfs2nii.log")):
                log.step(
                    "incomplete hcpls for session %s already exists: cleaning session"
                    % (session)
                )
                shutil.rmtree(tfolder)
                sessions["clean"].append(session)
            else:
                sessions["skip"].append(session)
                with log.section(
                    "hcpls for session %s already exists: skipping session" % (session)
                ):
                    log.step("files previously mapped:")
                    with open(os.path.join(tfolder, "hcpfs2nii.log")) as hcpls_log:
                        for logline in hcpls_log:
                            if "HCPFS to nii mapping report" in logline:
                                continue
                            elif "=>" in logline:
                                mapped_file = logline.split("=>")[0].strip()
                                log.detail(os.path.basename(mapped_file))
        else:
            log.step("creating hcpl session %s" % (sessionid))
            sessions["map"].append(sessionid)

    if os.path.exists(tfile):
        if sessionid in sessions["skip"]:
            return False
        else:
            os.remove(tfile)
    elif not os.path.exists(os.path.dirname(tfile)):
        os.makedirs(os.path.dirname(tfile))

    if session in sessions["skip"]:
        return False

    return tfile


def import_hcp(
    sessionsfolder=None,
    inbox=None,
    sessions=None,
    action="link",
    overwrite="no",
    archive="leave",
    hcplsname=None,
    nameformat=None,
    filesort=None,
    processed_data=None,
    hcp_dataset=None,
    _log=None,
):
    """
    ``import_hcp [sessionsfolder=.] [inbox=<sessionsfolder>/inbox/HCPLS] [sessions=""] [action=link] [overwrite=no] [archive=leave] [hcplsname=<inbox folder name>] [nameformat='(?P<subject_id>[^/]+?)_(?P<session_name>[^/]+?)/unprocessed/(?P<data>.*)'] [filesort=<file sorting option>] [processed_data=<path to hcp processed data>] [hcp_dataset=<HCP dataset name>]``

    Map HCPLS data to the QuNex Suite file structure.

    ..  qx_command:
        type: utility

    Parameters:
        --sessionsfolder (str, default '.'):
            The sessions folder where all the sessions are to be mapped to. It
            should be a folder within the <study folder>.

        --inbox (str, default <sessionsfolder>/inbox/HCPLS):
            The location of the HCPLS dataset. It can be any of the following:
            the HCPLS dataset top folder, a folder that contains the HCPLS
            dataset, a path to the compressed `.zip` or `.tar.gz` package that
            can contain a single session or a multi-session dataset, or a
            folder that contains a compressed package. For instance the user
            can specify "<path>/<hcpfs_file>.zip" or "<path>" to a folder that
            contains multiple packages. The default location where the command
            will look for a HCPLS dataset is "<sessionsfolder>/inbox/HCPLS". Set
            to "NONE" if onboarding preprocessed data only.

        --sessions (str, default detailed below):
            An optional parameter that specifies a comma or pipe separated list
            of sessions from the inbox folder to be processed. Regular
            expression patterns can be used. If provided, only packets or
            folders within the inbox that match the list of sessions will be
            processed. If `inbox` is a file `sessions` will not be applied. If
            `inbox` is a valid HCPLS datastructure folder, then the sessions
            will be matched against the `<subject id>[_<session name>]`. Note:
            the session will match if the string is found within the package
            name or the session id. So 'HCPA' with match any zip file that
            contains string 'HCPA' or any session id that contains 'HCPA'!

        --action (str, default 'link'):
            How to map the files to QuNex structure.

            The following actions are supported:

            - 'link' ... files will be mapped by creating hard links if
              possible, otherwise they will be copied
            - 'copy' ... files will be copied
            - 'move' ... files will be moved.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --archive (str, default 'move'):
            What to do with the files after they were mapped.

            Options are:

            - 'leave' ... leave the specified archive where it is
            - 'move'  ... move the specified archive to
              `<sessionsfolder>/archive/HCPLS`)
            - 'copy'  ... copy the specified archive to
              `<sessionsfolder>/archive/HCPLS`)
            - 'delete' ... delete the archive after processing if no errors were
              identified.

            Please note that there can be an interaction with the `action`
            parameter. If files are moved during action, they will be missing
            if `archive` is set to 'move' or 'copy'.

        --hcplsname (str, default detailed below):
            The optional name of the HCPLS dataset. If not provided it will be
            set to the name of the inbox folder or the name of the compressed
            package.

        --nameformat (str, default '(?P<subject_id>[^/]+?)_(?P<session_name>[^/]+?)/unprocessed/(?P<data>.*)'):
            An optional parameter that contains a regular expression pattern
            with named fields used to extract the subject and session
            information based on the file paths and names.

            The pattern has to return the groups named:

            - 'subject_id'   ... the id of the subject
            - 'session_name' ... the name of the session
            - 'data'         ... the rest of the path with the sequence related
              files.

        --filesort (str, default 'name_type_se'):
            An optional parameter that specifies how the files should be sorted
            before mapping to `nii` folder and inclusion in `session_hcp.txt`.
            The sorting is specified by a string of sort keys separated by '_'.

            The available sort keys are:

            - 'name' ... sort by the name of the file
            - 'type' ... sort by the type of the file (T1w, T2w, rfMRI, tfMRI,
              Diffusion)
            - 'se'   ... sort by the number of the related pair of the SE
              fieldmap images.

            The files will be sorted in the order of the listed keys.

            NOTE:

            1. SE field map pair will always come before the first
               image in the sorted list that references it.
            2. Diffusion images will always be listed jointly in a
               fixed order.

        --processed_data (str):
            Path to the folder with processed data. If provided, the command
            will copy that data along with unprocessed data. If onboarding
            multiple sessions then define the portion of the path to be replaced
            with session id with <session_id>, e.g.:
            --processed_data=/archive/fMRI/hca/<session_id>. If the inbox
            parameter is set to NONE, then only processed data will be
            onboarded. When onboarding preprocessed data, processed HCP folder
            structure needs to reside inside the root of the session folder or
            immediately inside the zip archive.

        --hcp_dataset (str):
            When onboarding a preprocessed HCP dataset, this parameter is
            mandatory. Set to HCA, HCD or HCYA depending on the dataset you are
            onboarding.

    Output files:
        After running the `import_hcp` command the HCPLS dataset will be
        mapped to the QuNex folder structure and image files will be
        prepared for further processing along with required metadata. When
        onboarding preprocessed data, only HCP folders with preprocessed data
        will be created.

        - The original HCPL session-level data is stored in::

            <sessionsfolder>/<session>/hcpls

        - Image files mapped to new names for QuNex are stored in::

            <sessionsfolder>/<session>/nii

        - The full description of the mapped files is in::

            <sessionsfolder>/<session>/session.txt

        - The output log of HCPLS mapping is in::

            <sessionsfolder>/<session>/hcpls/hcpls2nii.log

    Notes:
        When onboarding only preprocessed data only that data will be copied
        into the QuNex study. Otherwise, the import_hcp command consists of two
        steps:

        1. Mapping HCPLS dataset to QuNex Suite folder structure:
            The `inbox` parameter specifies the location of the HCPLS
            dataset. This path is inspected for a HCPLS compliant dataset.
            The path can point to a folder with extracted HCPLS dataset, a
            `.zip` or `.tar.gz` archive or a folder containing one or more
            `.zip` or `.tar.gz` archives. In the initial step, each file
            found will be assigned either to a specific session.

            <hcpls_dataset_name> can be provided as a `hcplsname` parameter
            to the command call. If `hcplsname` is not provided, the name
            will be set to the name of the parent folder or the name of the
            compressed archive.

            The files identified as belonging to a specific session will be
            mapped to folder::

                <sessions_folder>/<subject>_<session>/hcpls

            The `<subject>_<session>` string will be used as the identifier
            for the session in all the following steps. If the folder for
            the `session` does not exist, it will be created.

            When the files are mapped, their filenames will be preserved.

        2. Mapping image files to QuNex Suite `nii` folder:
            For each session separately, images from the `hcpls` folder are
            mapped to the `nii` folder and appropriate `session.txt` file
            is created per standard QuNex specification.

            The second step is achieved by running `map_hcpls2nii` on each
            session folder. This step is run automatically, but can be
            invoked independently if mapping of HCPLS dataset to QuNex
            Suite folder structure was already completed. For detailed
            information about this step, please review `map_hcpls2nii`
            inline help.

        Please see `map_hcpls2nii` inline documentation!

        Importing only specific sessions:
            If only specific sessions are to be imported, then the `--sessions`
            parameter can be used. Specifically, `--sessions` is an optional
            parameter that should specify a comma or pipe separated list of
            sessions from the inbox folder to be processed. Regular expression
            patterns can be used. If provided, only packets or folders within
            the inbox folder that match the list of sessions will be processed.
            If `inbox` is a file, `sessions` will not be applied. If `inbox` is
            a valid HCPLS datastructure folder, then the sessions will be
            matched against the `<subject id>[_<session name>]`.

            **Note**: the session will match if the string is found within the
            package name or the session id. So 'HCPA' with match any zip file
            that contains string 'HCPA' or any session id that contains 'HCPA'!

    Examples:
        ::

           qunex import_hcp \\
              --sessionsfolder="<absolute path to study folder>/sessions" \\
              --inbox="<absolute path to folder with HCP dataset>" \\
              --archive=move \\
              --overwrite=yes

        The above command would map the entire HCP dataset located at the
        specified location into the relevant sessions' folders—creating them
        when needed—, organize the MR image files in the sessions' ``nii``
        folder and prepare ``session_hcp.txt`` file for further processing. Any
        preexisting data for the sessions present in the HCP dataset would be
        removed and replaced. By default the HCP files would be hard-linked to
        the new location.

        ::

           qunex import_hcp \\
              --sessionsfolder="<absolute path to study folder>/sessions" \\
              --inbox="<absolute path to folder with HCP dataset>" \\
              --action='copy' \\
              --archive='leave' \\
              --overwrite=no

        The above command would map the entire HCP dataset located at the
        specified location into the relevant session folders—creating them when
        needed—, organize the MR image files in the sessions' ``nii`` folder and
        prepare ``session_hcp.txt`` file for further processing. If for any of
        the sessions HCP mapped data already exist, that session will be skipped
        when processing. The files would be mapped to their destinations by
        creating a copy rather than hard-linking them.

        ::

           qunex import_hcp \\
              --sessionsfolder="<absolute path to study folder>/sessions" \\
              --sessions="HCA6086369_V1_MR,HCA6166973_V1_MR,HCD00" \\
              --inbox="<absolute path to folder with HCP dataset>" \\
              --action='copy' \\
              --archive='leave' \\
              --overwrite=no

        The above example additionally specifies, that only sessions
        HCA6086369_V1_MR and HCA6166973_V1_MR, and any session that starts
        with HCD00 should be imported.

        ::

            qunex import_hcp \\
                --sessionsfolder=myStudy/sessions \\
                --inbox=HCPLS \\
                --overwrite=yes \\
                --hcplsname=hcpls
    """

    log = gl.log_or_console(_log)

    # `raw` because a title over its own rule is not a record shape; no
    # trailing newline, since every record that follows opens with one
    log.raw("\nRunning import_hcp\n==================")

    if action not in ["link", "copy", "move"]:
        raise ge.CommandError(
            "import_hcp",
            "Invalid action specified",
            "%s is not a valid action!" % (action),
            "Please specify one of: copy, link, move!",
        )

    if archive not in ["leave", "move", "copy", "delete"]:
        raise ge.CommandError(
            "import_hcp",
            "Invalid dataset archive option",
            "%s is not a valid option for dataset archive option!" % (archive),
            "Please specify one of: move, copy, delete!",
        )

    if not filesort:
        filesort = "name_type_se"

    if any([e not in ["name", "type", "se"] for e in filesort.split("_")]):
        raise ge.CommandError(
            "import_hcp",
            "invalid filesort option",
            "%s is not a valid option for filesort parameter!" % (filesort),
            "Please only use keys: name, type, se!",
        )

    if hcp_dataset:
        hcp_dataset = hcp_dataset.lower()
        if hcp_dataset not in ["hca", "hcd", "hcya"]:
            raise ge.CommandError(
                "import_hcp",
                "invalid hcp_dataset option",
                "%s is not a valid option for hcp_dataset parameter!" % (hcp_dataset),
                "Please use one of: HCA, HCD, HCYA!",
            )

    if sessionsfolder is None:
        sessionsfolder = os.path.abspath(".")

    if inbox is None:
        inbox = os.path.join(sessionsfolder, "inbox", "HCPLS")
        hcplsname = ""
    else:
        hcplsname = os.path.basename(inbox)
        hcplsname = re.sub(".zip$|.gz$|.tgz$", "", hcplsname)
        hcplsname = re.sub(".tar$", "", hcplsname)

    if not nameformat:
        nameformat = (
            r"(?P<subject_id>[^/]+?)_(?P<session_name>[^/]+?)/unprocessed/(?P<data>.*)"
        )

    sessions_list = {"list": [], "clean": [], "skip": [], "map": []}
    all_ok = True
    errors = ""

    # ---> Check for folders
    # if not os.path.exists(os.path.join(sessionsfolder, "inbox", "HCPLS")):
    #     os.makedirs(os.path.join(sessionsfolder, "inbox", "HCPLS"))
    #     print("---> creating inbox HCPLS folder")

    if archive in ["move", "copy"]:
        if not os.path.exists(os.path.join(sessionsfolder, "archive", "HCPLS")):
            os.makedirs(os.path.join(sessionsfolder, "archive", "HCPLS"))
            log.step("creating archive HCPLS folder")

    # ---> identification of files
    if sessions:
        sessions = [e.strip() for e in re.split(r" +|\| *|, *", sessions)]

    # traditional onboarding with unprocessed data
    report = []
    if inbox != "NONE":
        log.step("identifying files in %s" % (inbox))

        source_files = _get_source_files(inbox, sessions, nameformat)

        # ---> mapping data to sessions' folders
        log.step("mapping files to QuNex hcpls folders")

        for file in source_files:
            if file.endswith(".zip"):
                with log.section("processing zip package [%s]" % (file)):
                    try:
                        z = zipfile.ZipFile(file, "r")
                        for sf in z.infolist():
                            if sf.filename[-1] != "/":
                                tfile = map_to_qunex_cpls(
                                    sf.filename,
                                    sessionsfolder,
                                    hcplsname,
                                    sessions_list,
                                    overwrite,
                                    nameformat,
                                    _log=log,
                                )
                                if tfile:
                                    fdata = z.read(sf)
                                    fout = open(tfile, "wb")
                                    fout.write(fdata)
                                    fout.close()
                        z.close()

                        log.step("done!")
                    except Exception:
                        log.error(
                            "Processing of zip package failed. Please check the package!"
                        )
                        errors += "\n    .. Processing of package %s failed!" % (file)
                        all_ok = False
                        raise

            elif ".tar" in file or ".tgz" in file:
                with log.section("processing tar package [%s]" % (file)):
                    try:
                        tar = tarfile.open(file)
                        for member in tar.getmembers():
                            if member.isfile():
                                tfile = map_to_qunex_cpls(
                                    member.name,
                                    sessionsfolder,
                                    hcplsname,
                                    sessions_list,
                                    overwrite,
                                    nameformat,
                                    _log=log,
                                )
                                if tfile:
                                    fobj = tar.extractfile(member)
                                    fdata = fobj.read()
                                    fobj.close()
                                    fout = open(tfile, "wb")
                                    fout.write(fdata)
                                    fout.close()
                        tar.close()

                        log.step("done!")
                    except Exception:
                        log.error(
                            "Processing of tar package failed. Please check the package!"
                        )
                        errors += "\n    .. Processing of package %s failed!" % (file)
                        all_ok = False

            else:
                tfile = map_to_qunex_cpls(
                    file,
                    sessionsfolder,
                    hcplsname,
                    sessions_list,
                    overwrite,
                    nameformat,
                    _log=log,
                )
                if tfile:
                    status, msg = gc.move_link_or_copy(
                        file, tfile, action, r="", prefix="    .. "
                    )
                    all_ok = all_ok and status
                    if not status:
                        errors += msg

        # ---> archiving the dataset
        if errors:
            log.error("The following errors were encountered when mapping the files:")
            log.raw(errors)
        else:
            if os.path.isfile(inbox) or (
                os.path.exists(os.path.join(sessionsfolder, "inbox", "HCPLS"))
                and not os.path.samefile(
                    inbox, os.path.join(sessionsfolder, "inbox", "HCPLS")
                )
            ):
                try:
                    if archive == "move":
                        log.step("moving dataset to archive")
                        shutil.move(
                            inbox, os.path.join(sessionsfolder, "archive", "HCPLS")
                        )
                    elif archive == "copy":
                        log.step("copying dataset to archive")
                        shutil.copy2(
                            inbox, os.path.join(sessionsfolder, "archive", "HCPLS")
                        )
                    elif archive == "delete":
                        log.step("deleting dataset")
                        if os.path.isfile(inbox):
                            os.remove(inbox)
                        else:
                            shutil.rmtree(inbox)
                except Exception:
                    log.warning("%s failed!" % (archive))
            else:
                files = glob.glob(os.path.join(inbox, "*"))
                for file in files:
                    try:
                        if archive == "move":
                            log.step("moving dataset to archive")
                            shutil.move(
                                file, os.path.join(sessionsfolder, "archive", "HCPLS")
                            )
                        elif archive == "copy":
                            log.step("copying dataset to archive")
                            shutil.copy2(
                                file, os.path.join(sessionsfolder, "archive", "HCPLS")
                            )
                        elif archive == "delete":
                            log.step("deleting dataset")
                            if os.path.isfile(file):
                                os.remove(file)
                            else:
                                shutil.rmtree(file)
                    except Exception:
                        log.warning("%s of %s failed!" % (archive, file))

        # ---> check status
        if not all_ok:
            log.raw("\n\nFinal report\n============")
            raise ge.CommandFailed(
                "import_hcp",
                "Processing of some packages failed",
                "Mapping of image files aborted.",
                "Please check report!",
            )

        # ---> mapping data to QuNex nii folder
        for execute in ["map", "clean"]:
            for session in sessions_list[execute]:
                if session != "hcpls":
                    sparts = session.split("_")
                    subjectid = sparts.pop(0)
                    sessionid = "_".join([e for e in sparts + [""] if e])
                    info = "subject " + subjectid
                    if sessionid:
                        info += ", session " + sessionid

                    try:
                        nimg, nmapped = map_hcpls2nii(
                            os.path.join(sessionsfolder, session),
                            overwrite,
                            filesort=filesort,
                            _log=log,
                        )
                        if nimg == 0:
                            report.append(
                                "%s had no images found to be mapped" % (info)
                            )
                            all_ok = False
                        elif nimg == nmapped:
                            report.append(
                                "%s completed ok. %d images mapped" % (info, nmapped)
                            )
                        else:
                            report.append(
                                "%s mapped incompletely [%d images, %d mapped]"
                                % (info, nimg, nmapped)
                            )
                            all_ok = False
                    except ge.CommandFailed as e:
                        log.warning(e.report[0])
                        for hint in e.report[1:]:
                            log.detail(hint)
                        report.append("%s failed" % (info))
                        all_ok = False

                # ---> also copy over processed data
                if processed_data:
                    log.step("copying processed data")
                    # path to the session's processed data
                    session_path = processed_data.replace("<session_id>", sessionid)
                    if not os.path.exists(session_path):
                        session_path = processed_data.replace("<session_id>", subjectid)
                    if not os.path.exists(session_path):
                        session_path = processed_data.replace("<session_id>", session)
                    if not os.path.exists(session_path):
                        session_path = processed_data

                    # target folder
                    tfolder = os.path.join(sessionsfolder, session, "hcp", session)
                    if not os.path.exists(tfolder):
                        os.makedirs(tfolder)

                    modalities = ["T1w", "T2w", "Diffusion", "MNINonLinear"]
                    for m in modalities:
                        modality_path = os.path.join(session_path, m)
                        if os.path.exists(modality_path):
                            log.detail(
                                f"copying processed {m} data to QuNex session folder"
                            )
                            shutil.copytree(modality_path, os.path.join(tfolder, m))

    # processed data only
    else:
        log.step("onboarding preprocessed data only")
        # load the yaml file
        template_folder = os.environ["NIUTemplateFolder"]
        hcp_onboarding = os.path.join(template_folder, "hcp_onboarding.yaml")
        with open(hcp_onboarding, "r", encoding="UTF-8") as f:
            hcp_onboarding_data = yaml.safe_load(f)
        dataset_info = hcp_onboarding_data[hcp_dataset]
        anat_info = dataset_info["anat"]
        dwi_info = dataset_info["dwi"]
        func_info = hcp_onboarding_data["func"]

        # look for files and folders in the processed_data folder
        source_files = _get_source_files(processed_data, sessions, nameformat, True)

        for sf in source_files:
            # session id
            session = os.path.basename(sf)
            log.step(f"onboarding {session}")
            subject = session.split("_")[0]

            session_folder = os.path.join(sessionsfolder, session)
            hcp_folder_no_session = os.path.join(sessionsfolder, session, "hcp")
            hcp_folder = os.path.join(hcp_folder_no_session, session)
            mni_folder = os.path.join(hcp_folder, "MNINonLinear")
            t1w_folder = os.path.join(hcp_folder, "T1w")
            if not os.path.exists(hcp_folder):
                os.makedirs(hcp_folder)

            # if .zip unzip into hcp_folder
            is_file = True
            if sf.endswith(".zip"):
                log.detail(f"unzipping {sf} to {hcp_folder}")

                with zipfile.ZipFile(sf, "r") as zf:
                    zf.extractall(hcp_folder)
            else:
                is_file = False
                log.detail(f"copying {sf} to {hcp_folder}")
                shutil.copytree(sf, hcp_folder, dirs_exist_ok=True)

            # archive
            if archive == "move":
                log.detail(
                    f"archiving {sf} to {os.path.join(sessionsfolder, 'archive', 'HCPLS')}"
                )
                shutil.move(sf, os.path.join(sessionsfolder, "archive", "HCPLS"))
            elif archive == "copy":
                log.detail(
                    f"copying {sf} to {os.path.join(sessionsfolder, 'archive', 'HCPLS')}"
                )
                if is_file:
                    shutil.copy2(sf, os.path.join(sessionsfolder, "archive", "HCPLS"))
                else:
                    # if it is a folder, copy the whole folder
                    if not os.path.exists(
                        os.path.join(sessionsfolder, "archive", "HCPLS")
                    ):
                        os.makedirs(os.path.join(sessionsfolder, "archive", "HCPLS"))
                    if os.path.isdir(sf):
                        shutil.copytree(
                            sf, os.path.join(sessionsfolder, "archive", "HCPLS")
                        )
            elif archive == "delete":
                log.detail(f"deleting {sf}")
                shutil.rmtree(sf)

            # create session_hcp.txt
            session_hcp_file = os.path.join(session_folder, "session_hcp.txt")
            log.detail(f"creating {session_hcp_file}")

            with open(session_hcp_file, "w", encoding="UTF-8") as f:
                gl.print_qunex_header(timestamp=None, file=f)
                f.write("#\n")
                f.write(f"session: {session}\n")
                f.write(f"subject: {subject}\n")
                f.write(f"hcp: {hcp_folder_no_session}\n")
                f.write("hcpready: true\n\n")

                # anat
                ix = 1
                if os.path.exists(os.path.join(mni_folder, "T1w_restore.nii.gz")):
                    f.write(f"{ix:02d}: T1w : {anat_info['T1w']}\n")
                    ix += 1
                elif os.path.exists(
                    os.path.join(t1w_folder, "T1w_acpc_dc_restore.nii.gz")
                ):
                    f.write(f"{ix:02d}: T1w : {anat_info['T1w']}\n")
                    ix += 1
                if os.path.exists(os.path.join(mni_folder, "T2w_restore.nii.gz")):
                    f.write(f"{ix:02d}: T2w : {anat_info['T2w']}\n")
                    ix += 1
                elif os.path.exists(
                    os.path.join(t1w_folder, "T2w_acpc_dc_restore.nii.gz")
                ):
                    f.write(f"{ix:02d}: T2w : {anat_info['T2w']}\n")
                    ix += 1

                # dwi
                if os.path.exists(os.path.join(t1w_folder, "Diffusion")):
                    for dwi_tag in dwi_info:
                        for direction in dataset_info["direction"]:
                            f.write(
                                f"{ix:02d}: DWI: {dwi_tag}_{direction} : DWI_{dwi_tag}_{direction}\n"
                            )
                            ix += 1

                # func
                bold_ix = 1
                for bold_info in func_info:
                    bold_tag = bold_info[0]
                    for direction in dataset_info["direction"]:
                        bold = f"{bold_info[1]}_{direction}"
                        if os.path.exists(os.path.join(mni_folder, "Results", bold)):
                            f.write(
                                f"{ix:02d}: bold{bold_ix} : {bold_tag}: {bold}: filename({bold})\n"
                            )
                            bold_ix += 1
                            ix += 1

            session_file = os.path.join(session_folder, "session.txt")
            shutil.copyfile(session_hcp_file, session_file)

            report.append(f"{session} onboarded successfully with {ix - 1} images.")

    log.raw("\n\nFinal report\n============")
    for line in report:
        log.info(line)

    if not all_ok:
        raise ge.CommandFailed(
            "import_hcp", "Some actions failed", "Please check report!"
        )


def _get_source_files(archive_folder, sessions, nameformat, processed=False):
    """
    Get source files given a folder, sessions and the name format.
    """
    source_files = []
    if os.path.exists(archive_folder):
        if os.path.isfile(archive_folder):
            source_files = [archive_folder]
        elif os.path.isdir(archive_folder):
            if not processed:
                for path, _, files in os.walk(archive_folder):
                    for file in files:
                        filepath = os.path.join(path, file)
                        if sessions:
                            if any(
                                [
                                    file.endswith(e)
                                    for e in [
                                        ".zip",
                                        ".tar",
                                        ".tar.gz",
                                        ".tar.bz",
                                        ".tarz",
                                        ".tar.bzip2",
                                        ".tgz",
                                    ]
                                ]
                            ):
                                for session in sessions:
                                    if re.search(session, file):
                                        source_files.append(filepath)
                                        break
                            else:
                                m = re.search(nameformat, filepath)
                                try:
                                    file_subjid = m.group("subject_id")
                                    file_session = m.group("session_name")
                                    file_sessionid = "%s_%s" % (
                                        file_subjid,
                                        file_session,
                                    )
                                    for session in sessions:
                                        if re.search(session, file_sessionid):
                                            source_files.append(filepath)
                                            break
                                except Exception:
                                    pass
                        else:
                            source_files.append(filepath)
            else:
                # add only root if it matches the
                for file in os.listdir(archive_folder):
                    filepath = os.path.join(archive_folder, file)
                    if os.path.isfile(filepath):
                        source_files.append(filepath)
                    elif os.path.isdir(filepath):
                        if sessions:
                            for session in sessions:
                                if re.search(session, file):
                                    source_files.append(filepath)
                                    break
                        else:
                            source_files.append(filepath)
    else:
        raise ge.CommandFailed(
            "import_hcp",
            "Inbox does not exist",
            "The specified inbox [%s] does not exist!" % (archive_folder),
            "Please check your path!",
        )

    if not source_files:
        raise ge.CommandFailed(
            "import_hcp",
            "No files found",
            "No files were found to be processed at the specified inbox [%s]!"
            % (archive_folder),
            "Please check your path!",
        )

    return source_files


def process_hcpls(sessionfolder, filesort, _log=None):
    """ """

    if not os.path.exists(sessionfolder):
        raise ge.CommandFailed(
            "process_hcpls",
            "No hcpls folder present!",
            "There is no hcpls data in session folder %s" % (sessionfolder),
            "Please import HCPLS data first!",
        )

    session = os.path.basename(os.path.dirname(sessionfolder))
    # sparts    = session.split('_')
    # subjectid = sparts.pop(0)
    # sessionid = "_".join([e for e in sparts + [""] if e])

    # --- load HCPLS structure
    # template folder
    niu_template_folder = os.environ["NIUTemplateFolder"]
    hcpls_structure = os.path.join(niu_template_folder, "import_hcp.txt")

    if not os.path.exists(hcpls_structure):
        raise ge.CommandFailed(
            "process_hcpls",
            "No HCPLS structure file present!",
            "There is no HCPLS structure file %s" % (hcpls_structure),
            "Please check your QuNex installation",
        )

    hcpls_file = open(hcpls_structure)
    content = hcpls_file.read()
    hcpls = ast.literal_eval(content)

    # --- get a list of folders and process them
    dfolders = glob.glob(os.path.join(sessionfolder, "*"))

    # -- data: SE number, label, fodlerInfo, folderFiles, status
    checked_folders = []

    for dfolder in dfolders:
        folder_info = {}
        folder_files = []
        senum = 0
        fmnum = 0
        missing_files = []

        # --- get folder information
        folder_name = os.path.basename(dfolder)
        folder_tags = folder_name.split("_")
        folder_label = folder_tags.pop(0)
        if folder_label not in hcpls["folders"]:
            continue

        for info in hcpls["folders"][folder_label]["info"]:
            if folder_tags:
                folder_info[info] = folder_tags.pop(0)

        # --- Get files list
        files = sorted(glob.glob(os.path.join(dfolder, "*")))
        files = [e for e in files if e.endswith(".nii.gz")]

        # --- Exclude files
        to_exclude = ["InitialFrames"]
        for exclude in to_exclude:
            files = [e for e in files if exclude not in e]

        # --- Proces spin echo files
        sefile = [e for e in files if ("SpinEchoFieldMap" in e or "DistortionMap" in e)]
        if sefile:
            senum = (
                [
                    e
                    for e in sefile[0].split("_")
                    if ("SpinEchoFieldMap" in e or "DistortionMap" in e)
                ][0]
                .replace("SpinEchoFieldMap", "")
                .replace("DistortionMap", "")
            )
            if senum:
                senum = int(senum)
            else:
                senum = 1

        # --- Proces fieldmap files
        fmfile = [e for e in files if "FieldMap_Magnitude" in e]
        if fmfile:
            fmnum = (
                [e for e in fmfile[0].split("_") if "Magnitude" in e][0]
                .replace("Magnitude", "")
                .replace(".nii.gz", "")
            )
            if fmnum:
                fmnum = int(fmnum)
            else:
                fmnum = 1

        for file in files:
            file_name = os.path.basename(file)
            file_parts = (
                file_name.replace(session + "_", "").replace(".nii.gz", "").split("_")
            )
            file_parts = [
                (
                    "SpinEchoFieldMap"
                    if "SpinEchoFieldMap" in e
                    else "DistortionMap"
                    if "DistortionMap" in e
                    else e
                )
                for e in file_parts
            ]
            folder_files.append(
                {
                    "rank": 0,
                    "path": file,
                    "name": file_name,
                    "parts": file_parts,
                    "json": None,
                }
            )

        # --- Check files
        check = list(hcpls["folders"][folder_label]["check"])
        rank = 0
        # diffusion
        if folder_label == "Diffusion":
            # sort folderfiles by dir
            folder_files.sort(
                key=lambda x: (
                    (
                        int(x["parts"][1].replace("dir", ""))
                        if "dir" in x["parts"][1]
                        else float("inf")
                    ),
                    x["parts"][2] if len(x["parts"]) > 2 else "z",
                )
            )
            for file in folder_files:
                match = False
                for fcheck in check:
                    if "dir" in file["parts"][1] or (
                        "b0" in file["parts"] and len(file["parts"]) == 3
                    ):
                        if (
                            file["parts"][0] == fcheck[0]
                            and file["parts"][1].startswith(fcheck[1])
                            and file["parts"][2] == fcheck[2]
                        ):
                            match = True
                            break
                    elif "b0" in file["parts"]:
                        if (
                            file["parts"][0] == fcheck[0]
                            and file["parts"][1].startswith(fcheck[1])
                            and file["parts"][3] == fcheck[2]
                        ):
                            match = True
                            break
                if match:
                    rank += 1
                    file["rank"] = rank

        else:
            for fcheck in check:
                found = False
                for file in folder_files:
                    match = True
                    for citem in fcheck:
                        if citem[0] == "-":
                            if citem[1:] in file["parts"]:
                                match = False
                        else:
                            if citem not in file["parts"]:
                                match = False
                    if match:
                        rank += 1
                        file["rank"] = rank
                        found = True
                        break
                if not found:
                    missing_files.append([dfolder, fcheck])

        # --- Order files
        folder_files.sort(key=lambda x: x["rank"])
        extra_files = [e for e in folder_files if e["rank"] == 0]
        folder_files = [e for e in folder_files if e["rank"] > 0]

        # --- Get json info
        for file in folder_files:
            jfile = file["path"].replace(".nii.gz", ".json")
            if not os.path.exists(jfile):
                missing_files.append([dfolder, os.path.basename(jfile)])
                file["json"] = {}
            else:
                with open(jfile, "r") as f:
                    jinf = json.load(f)
                file["json"] = jinf

        # --- finish up folder
        checked_folders.append(
            {
                "senum": senum,
                "fmnum": fmnum,
                "name": folder_name,
                "label": folder_label,
                "folderInfo": folder_info,
                "folderFiles": folder_files,
                "extraFiles": extra_files,
                "missingFiles": missing_files,
            }
        )

    # sort folders
    log = gl.log_or_console(_log)
    log.step("filesort: %s" % (filesort))
    for sortkey in filesort.split("_"):
        if sortkey == "name":
            checked_folders.sort(key=lambda x: x["name"])

        if sortkey == "type":
            checked_folders.sort(key=lambda x: hcpls["folders"]["order"][x["label"]])

        if sortkey == "se":
            checked_folders.sort(key=lambda x: x["senum"])

    return checked_folders


def map_hcpls2nii(
    sourcefolder=".", overwrite="no", report=None, filesort=None, _log=None
):
    """
    ``map_hcpls2nii [sourcefolder='.'] [overwrite='no'] [report=<study>/info/hcpls/parameters.txt] [filesort=<file sorting option>]``

    Map HCPLS organized data to `nii` folder structure.

    ..  qx_command:
        type: utility

    Warning:
        .bvec and .bval files:
            `.bvec` and `.bval` files are expected to be present along with dMRI
            files in each session folder. If they are present in another
            folder, they are currently not mapped to the `.nii` folder.

        Image format:
            The function assumes that all the images are saved as `.nii.gz`
            files!

    Parameters:
        --sourcefolder (str, default '.'):
            The base session folder in which bids folder with data and files for
            the session are present.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --report (str, default None):
            The path to the file that will hold the information about the images
            that are relevant for HCP Pipelines. Will not write it by default.

        --filesort (str, default 'name_type_se'):
            An optional parameter that specifies how the files should
            be sorted before mapping to `nii` folder and inclusion in
            `session_hcp.txt`. The sorting is specified by a string of
            sort keys separated by '_'.

            The available sort keys are:

            - 'name' ... sort by the name of the file
            - 'type' ... sort by the type of the file (T1w, T2w, rfMRI, tfMRI,
              Diffusion
            - 'se'   ... sort by the number of the related pair of the SE fieldmap
              images.

            The files will be sorted in the order of the listed keys.

            NOTE:

            - SE field map pair will always come before the first image in the
              sorted list that references it.
            - Diffusion images will always be listed jointly in a fixed order.

    Output files:
        After running the mapped nifti files will be in the `nii` subfolder,
        named with sequential image number. `session.txt` will be in the
        base session folder and `hcpls2nii.log` will be in the `hcpls`
        folder.

        session.txt file:
            The session.txt will be placed in the session base folder. It
            will contain the information about the session id, subject id
            location of folders and a list of created NIfTI images with
            their description.

            An example session.txt file would be::

                id: 06_retest
                subject: 06
                hcpls: /Volumes/tigr/MBLab/fMRI/bidsTest/sessions/06_retest/hcpls
                raw_data: /Volumes/tigr/MBLab/fMRI/bidsTest/sessions/06_retest/nii
                hcp: /Volumes/tigr/MBLab/fMRI/bidsTest/sessions/06_retest/hcp

                01: T1w
                02: bold1:rest1
                03: bold2:rest1
                04: bold3:rest2
                05: bold4:rest2
                06: bold5:CARIT
                07: bold6:FACENAME
                08: bold7:VISMOTOR
                09: dwi

            For each of the listed images there will be a corresponding
            NIfTI file in the nii subfolder (e.g. 04.nii.gz for resting
            state 2 PA). The generated session.txt files form the basis for
            the following HCP and other processing steps. `id` field will
            be set to the full session name, `subject` will be set to the
            text preceeding the first underscore (`_`) character.

        hcpls2nii.log file:
            The `hcpls2nii.log` provides the information about the date and
            time the files were mapped and the exact information about
            which specific file from the `hcpls` folder was mapped to which
            file in the `nii` folder.

    Notes:
        The command is used to map data organized according to HCPLS
        specification, residing in `hcpls` session subfolder to `nii`
        folder as expected by QuNex functions. The command checks the
        imaging data and compiles a list in the following order:

        - anatomical images
        - fieldmap images
        - functional images
        - diffusion weighted images.

        Once the list is compiled, the files are mapped to `nii` folder to
        files named by ordinal number of the image in the list. To save
        space, files are not copied but rather hard links are created. Only
        image, bvec and bval files are mapped from the `hcpls` to `nii`
        folder. The exact mapping is noted in file `hcpls2nii.log` that is
        saved to the `hcpls` folder. The information on images is also
        compiled in `session.txt` file that is generated in the main
        session folder. For every image all the information present in the
        hcpls filename is listed.

        Multiple sessions and scheduling:
            The command can be run for multiple sessions by specifying
            `sessions` and optionally `sessionsfolder` and `parsessions`
            parameters. In this case the command will be run for each of
            the specified sessions in the sessionsfolder (current directory
            by default). Optional `filter` and `sessionids` parameters can
            be used to filter sessions or limit them to just specified id
            codes. (for more information see online documentation).
            `sourcefolder` will be filled in automatically as each
            sessions's folder. Commands will run in parallel, where the
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

            qunex map_hcpls2nii \\
                --folder=. \\
                --overwrite=yes

        ::

            qunex map_hcpls2nii \\
                --sessionsfolder="/data/my_study/sessions" \\
                --sessions="AP*" \\
                --overwrite=yes
    """

    log = gl.log_or_console(_log)

    if not filesort:
        filesort = "name_type_se"

    if any([e not in ["name", "type", "se"] for e in filesort.split("_")]):
        raise ge.CommandError(
            "import_hcp",
            "invalid filesort option",
            "%s is not a valid option for filesort parameter!" % (filesort),
            "Please only use keys: name, type, se!",
        )

    sfolder = os.path.abspath(sourcefolder)
    hfolder = os.path.join(sourcefolder, "hcpls")
    nfolder = os.path.join(sourcefolder, "nii")

    # --- report file
    if report is None:
        rout = open(os.devnull, "w")
    else:
        rout = open(report, "a")

    # --- session info
    session = os.path.basename(sfolder)
    sparts = session.split("_")
    subjectid = sparts.pop(0)
    sessionid = "_".join([e for e in sparts + [""] if e])

    info = "subject " + subjectid
    if sessionid:
        info += ", session " + sessionid

    log.detail("info: %s" % (info))

    splash = "Running map_hcpls2nii for %s" % (info)
    # `raw` because a title over its own rule is not a record shape
    log.raw("\n%s\n%s" % (splash, "".join(["=" for e in range(len(splash))])))

    splash = "\n\nParameters for " + info
    print(splash, file=rout)
    print("".join(["=" for e in range(len(splash))]), file=rout)

    # --- process hcpls folder
    hcpls_data = process_hcpls(hfolder, filesort, _log=log)
    if not hcpls_data:
        raise ge.CommandFailed(
            "map_hcpls2nii",
            "No image files in hcpls folder!",
            "There are no image files in the hcpls folder [%s]" % (hfolder),
            "Please check your data!",
        )

    # --- check for presence of nifti files
    if os.path.exists(nfolder):
        nfiles = len(glob.glob(os.path.join(nfolder, "*.nii*")))
        if nfiles > 0:
            if overwrite == "no" or overwrite is False:
                raise ge.CommandFailed(
                    "map_hcpls2nii",
                    "Existing files present!",
                    "There are existing files in the nii folder [%s]" % (nfolder),
                    "Please check or set parameter 'overwrite' to yes!",
                )
            else:
                shutil.rmtree(nfolder)
                os.makedirs(nfolder)
                log.step("cleaned nii folder, removed existing files")
    else:
        os.makedirs(nfolder)

    # --- create session.txt file
    # seam: `create_session_file` still prints, and a record renders as
    # "\n<line>" where a print emits "<line>\n" -- without this newline the
    # two run together. Goes when that helper takes a log.
    log.raw("\n")
    sout = gc.create_session_file("map_hcpls2nii", sfolder, session, subjectid, overwrite)

    # --- create session_hcp.txt file
    sfile = os.path.join(sfolder, "session_hcp.txt")
    if os.path.exists(sfile):
        if overwrite == "yes" or overwrite is True:
            os.remove(sfile)
            log.step("removed existing session_hcp.txt file")
        else:
            raise ge.CommandFailed(
                "map_hcpls2nii",
                "session_hcp.txt file already present!",
                "A session_hcp.txt file alredy exists [%s]" % (sfile),
                "Please check or set parameter 'overwrite' to 'yes' to rebuild it!",
            )

    sout_hcp = open(sfile, "w")
    gl.print_qunex_header(file=sout_hcp)
    print("#", file=sout_hcp)
    print("session:", session, file=sout_hcp)
    print("subject:", subjectid, file=sout_hcp)
    print("hcpfs:", hfolder, file=sout_hcp)
    print("raw_data:", nfolder, file=sout_hcp)
    print("hcp:", os.path.join(sfolder, "hcp"), file=sout_hcp)
    print(file=sout_hcp)
    print("hcpready: true", file=sout_hcp)

    # --- open hcpfs2nii log file
    if overwrite == "yes" or overwrite is True:
        mode = "w"
    else:
        mode = "a"

    bout = open(os.path.join(hfolder, "hcpls2nii.log"), mode)
    print(
        "HCPLS to nii mapping report, executed on %s"
        % (datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
        file=bout,
    )

    # --- map files
    all_ok = True

    # hcplsData   = [{'senum':senum, 'label': folderLabel, 'folderInfo': folderInfo, 'folderFiles': folderFiles, 'extraFiles': extraFiles, 'missingFiles': missingFiles}]
    # folderFiles = [{'rank': 0, 'path': file, 'name': file_name, 'parts': fileParts, 'json': None}]

    mapped = []
    imgn = 0
    boldn = 0
    nmapped = 0
    first_image = True

    for folder in hcpls_data:
        if folder["label"] in ["rfMRI", "tfMRI"]:
            boldn += 1

        for file_info in folder["folderFiles"]:
            if file_info["name"] in mapped:
                continue

            mapped.append(file_info["name"])

            imgn += 1
            tfile = os.path.join(nfolder, "%02d.nii.gz" % (imgn))
            status = gc.move_link_or_copy(file_info["path"], tfile, action="link")

            if status:
                nmapped += 1
                log.step("linked %02d.nii.gz <-- %s" % (imgn, file_info["name"]))

                # -- Institution and device information
                if first_image:
                    device_info = "%s|%s|%s" % (
                        file_info["json"].get("Manufacturer", "NA"),
                        file_info["json"].get("ManufacturersModelName", "NA"),
                        file_info["json"].get("DeviceSerialNumber", "NA"),
                    )
                    institution = file_info["json"].get("InstitutionName", "NA")
                    out = "\ninstitution: %s\ndevice: %s\n" % (institution, device_info)
                    print(out, file=sout)
                    print(out, file=sout_hcp)
                    first_image = False

                # --T1w and T2w
                if file_info["parts"][0] in ["T1w", "T2w"]:
                    # -29s for alignment purposes (output generation is slightly different with T1w and T2w)
                    out = "%02d: %-20s: %-29s" % (
                        imgn,
                        file_info["parts"][0],
                        "_".join(file_info["parts"]),
                    )
                    print(out, end=" ", file=sout)
                    print(out, end=" ", file=sout_hcp)
                    if folder["senum"]:
                        out = ": se(%d)" % (folder["senum"])
                        print(out, end=" ", file=sout)
                        print(out, end=" ", file=sout_hcp)
                    if folder["fmnum"]:
                        out = ": fm(%d)" % (folder["fmnum"])
                        print(out, end=" ", file=sout)
                        print(out, end=" ", file=sout_hcp)
                    echospacing = 0
                    if file_info["json"].get("DwellTime", None):
                        echospacing = file_info["json"].get("DwellTime")
                        out = ": DwellTime(%.10f)" % (echospacing)
                        print(out, end=" ", file=sout)
                        print(out, end=" ", file=sout_hcp)
                    elif file_info["json"].get("EchoSpacing", None):
                        echospacing = file_info["json"].get("EchoSpacing")
                        out = ": EchoSpacing(%.10f)" % (echospacing)
                        print(out, end=" ", file=sout)
                        print(out, end=" ", file=sout_hcp)
                    if file_info["json"].get("ReadoutDirection", None):
                        out = (
                            ": UnwarpDir(%s)"
                            % (unwarp[file_info["json"].get("ReadoutDirection")])
                        )
                        print(out, end=" ", file=sout)
                        print(out, end=" ", file=sout_hcp)

                    # add filename
                    out = ": filename(%s)" % "_".join(file_info["parts"])
                    print(out, file=sout)
                    print(out, file=sout_hcp)

                    print("\n" + file_info["parts"][0], file=rout)
                    print(
                        "".join(["-" for e in range(len(file_info["parts"][0]))]),
                        file=rout,
                    )
                    print(
                        "%-25s : %.8f"
                        % (
                            "_hcp_%ssamplespacing" % (file_info["parts"][0][:2]),
                            echospacing,
                        ),
                        file=rout,
                    )
                    print(
                        "%-25s : %s"
                        % (
                            "_hcp_unwarpdir",
                            unwarp[file_info["json"].get("ReadoutDirection", None)],
                        ),
                        file=rout,
                    )

                # -- BOLDS
                elif file_info["parts"][0] in ["tfMRI", "rfMRI"]:
                    phenc = file_info["json"].get("PhaseEncodingDirection", None)
                    if phenc:
                        phenc = pe_dir_map.get(phenc, "NA")
                    else:
                        phenc = file_info["parts"][2]

                    fmstr = ""
                    if folder["fmnum"]:
                        fmstr += ": fm(%d)" % (folder["fmnum"])
                    if folder["senum"]:
                        fmstr += ": se(%d)" % (folder["senum"])

                    if "SBRef" in file_info["parts"]:
                        out = "%02d: %-20s: %-30s%s : phenc(%s)" % (
                            imgn,
                            "boldref%d:%s" % (boldn, file_info["parts"][1]),
                            "_".join(file_info["parts"]),
                            fmstr,
                            phenc,
                        )
                        print(out, end=" ", file=sout)
                        print(out, end=" ", file=sout_hcp)
                    else:
                        out = "%02d: %-20s: %-30s%s : phenc(%s)" % (
                            imgn,
                            "bold%d:%s" % (boldn, file_info["parts"][1]),
                            "_".join(file_info["parts"]),
                            fmstr,
                            phenc,
                        )
                        print(out, end=" ", file=sout)
                        print(out, end=" ", file=sout_hcp)

                    if file_info["json"].get("EffectiveEchoSpacing", None):
                        out = ": EchoSpacing(%.10f)" % (
                            file_info["json"].get("EffectiveEchoSpacing")
                        )
                        print(out, end=" ", file=sout)
                        print(out, end=" ", file=sout_hcp)

                    # add filename
                    out = ": filename(%s)" % "_".join(file_info["parts"])
                    print(out, file=sout)
                    print(out, file=sout_hcp)

                    print("\n" + "_".join(file_info["parts"]), file=rout)
                    print(
                        "".join(["-" for e in range(len("_".join(file_info["parts"])))]),
                        file=rout,
                    )
                    print(
                        "%-25s : %.8f"
                        % (
                            "_hcp_bold_echospacing",
                            file_info["json"].get("EffectiveEchoSpacing", -9.0),
                        ),
                        file=rout,
                    )
                    print(
                        "%-25s : '%s=%s'"
                        % (
                            "_hcp_bold_unwarpdir",
                            phenc,
                            unwarp[
                                file_info["json"].get("PhaseEncodingDirection", None)
                            ],
                        ),
                        file=rout,
                    )

                # -- SE
                elif file_info["parts"][0] in ["SpinEchoFieldMap", "DistortionMap"]:
                    phenc = file_info["json"].get("PhaseEncodingDirection", None)
                    if phenc:
                        phenc = pe_dir_map.get(phenc, "NA")
                    else:
                        phenc = [
                            e
                            for e in ["LR", "RL", "AP", "PA"]
                            if e in file_info["parts"]
                        ] + ["NA"]
                        phenc = phenc[0]

                    if phenc == "NA":
                        log.warning(
                            "Could not identify phase encoding direction for %d.nii.gz [%s]!"
                            % (imgn, file_info["name"])
                        )
                        phencstr = ""
                    else:
                        phencstr = ": phenc(%s) " % (phenc)

                    if file_info["json"].get("EffectiveEchoSpacing", None):
                        echospstr = ": EchoSpacing(%.10f) " % (
                            file_info["json"].get("EffectiveEchoSpacing")
                        )
                    else:
                        echospstr = ""

                    out = "%02d: %-20s: %-30s: se(%d) %s%s: filename(%s)" % (
                        imgn,
                        "SE-FM-%s" % (file_info["parts"][1]),
                        "_".join(file_info["parts"]),
                        folder["senum"],
                        phencstr,
                        echospstr,
                        "_".join(file_info["parts"]),
                    )
                    print(out, file=sout)
                    print(out, file=sout_hcp)

                    print("\n" + "_".join(file_info["parts"]), file=rout)
                    print(
                        "".join(["-" for e in range(len("_".join(file_info["parts"])))]),
                        file=rout,
                    )
                    print(
                        "%-25s : %.8f"
                        % (
                            "_hcp_seechospacing",
                            file_info["json"].get("EffectiveEchoSpacing", -9.0),
                        ),
                        file=rout,
                    )
                    print(
                        "%-25s : '%s=%s'"
                        % (
                            "_hcp_seunwarpdir",
                            phenc,
                            unwarp[
                                file_info["json"].get("PhaseEncodingDirection", None)
                            ],
                        ),
                        file=rout,
                    )

                # -- Siemens fieldmap
                elif file_info["parts"][0] == "FieldMap":
                    out = "%02d: %-20s: %-30s: fm(%d) : filename(%s)" % (
                        imgn,
                        "FM-%s" % (file_info["parts"][1]),
                        "_".join(file_info["parts"]),
                        folder["fmnum"],
                        "_".join(file_info["parts"]),
                    )
                    print(out, file=sout)
                    print(out, file=sout_hcp)

                    print("\n" + "_".join(file_info["parts"]), file=rout)
                    print(
                        "".join(["-" for e in range(len("_".join(file_info["parts"])))]),
                        file=rout,
                    )

                # -- dMRI
                elif file_info["parts"][0] in ["dMRI", "DWI"]:
                    phenc = file_info["json"].get("PhaseEncodingDirection", None)
                    if phenc:
                        phenc = pe_dir_map.get(phenc, "NA")
                    else:
                        phenc = [
                            e
                            for e in ["LR", "RL", "AP", "PA"]
                            if e in file_info["parts"]
                        ] + ["NA"]
                        phenc = phenc[0]

                    if phenc == "NA":
                        log.warning(
                            "Could not identify phase encoding direction for %d.nii.gz [%s]!"
                            % (imgn, file_info["name"])
                        )
                        phencstr = ""
                    else:
                        phencstr = ": phenc(%s)" % (phenc)

                    if "SBRef" in file_info["parts"]:
                        if len(file_info["parts"]) == 4:
                            out = "%02d: %-20s: %-30s%s" % (
                                imgn,
                                "DWIref:%s_%s" % (file_info["parts"][1], phenc),
                                "_".join(file_info["parts"]),
                                phencstr,
                            )
                        elif len(file_info["parts"]) == 5:
                            out = "%02d: %-20s: %-30s: phenc(%s)" % (
                                imgn,
                                "DWIref:%s_%s_%s"
                                % (file_info["parts"][1], file_info["parts"][2], phenc),
                                "_".join(file_info["parts"]),
                                phenc,
                            )

                        print(out, end=" ", file=sout)
                        print(out, end=" ", file=sout_hcp)
                        if file_info["json"].get("EffectiveEchoSpacing", None):
                            print(
                                ": EchoSpacing(%.10f)"
                                % (
                                    file_info["json"].get("EffectiveEchoSpacing", -0.009)
                                ),
                                end=" ",
                                file=sout,
                            )
                            print(
                                ": EchoSpacing(%.10f)"
                                % (
                                    file_info["json"].get("EffectiveEchoSpacing", -0.009)
                                ),
                                end=" ",
                                file=sout_hcp,
                            )

                    else:
                        if len(file_info["parts"]) == 3:
                            out = "%02d: %-20s: %-30s: phenc(%s)" % (
                                imgn,
                                "DWI:%s_%s" % (file_info["parts"][1], phenc),
                                "_".join(file_info["parts"]),
                                phenc,
                            )
                        elif len(file_info["parts"]) == 4:
                            out = "%02d: %-20s: %-30s: phenc(%s)" % (
                                imgn,
                                "DWI:%s_%s_%s"
                                % (file_info["parts"][1], file_info["parts"][2], phenc),
                                "_".join(file_info["parts"]),
                                phenc,
                            )
                        print(out, end=" ", file=sout)
                        print(out, end=" ", file=sout_hcp)
                        if file_info["json"].get("EffectiveEchoSpacing", None):
                            out = ": EchoSpacing(%.10f)" % (
                                file_info["json"].get("EffectiveEchoSpacing", -0.009)
                            )
                            print(out, end=" ", file=sout)
                            print(out, end=" ", file=sout_hcp)

                        print("\n" + "_".join(file_info["parts"]), file=rout)
                        print(
                            "".join(
                                ["-" for e in range(len("_".join(file_info["parts"])))]
                            ),
                            file=rout,
                        )
                        print(
                            "%-25s : %.8f"
                            % (
                                "_hcp_dwi_echospacing",
                                file_info["json"].get("EffectiveEchoSpacing", -0.009),
                            ),
                            file=rout,
                        )

                    # add filename
                    out = ": filename(%s)" % "_".join(file_info["parts"])
                    print(out, file=sout)
                    print(out, file=sout_hcp)

                # -- ASL
                elif file_info["parts"][0] in ["mbPCASLhr", "PCASLhr", "ASL"]:
                    # phenc
                    phenc = file_info["json"].get("PhaseEncodingDirection", None)
                    if phenc:
                        phenc = pe_dir_map.get(phenc, "NA")
                    else:
                        phenc = file_info["parts"][2]

                    if file_info["parts"][1] in ["SpinEchoFieldMap", "DistortionMap"]:
                        phenc = "SE-FM-" + phenc

                    out = "%02d: %-20s: %-30s: phenc(%s)" % (
                        imgn,
                        "ASL",
                        "_".join(file_info["parts"]),
                        phenc,
                    )

                    print(out, end=" ", file=sout)
                    print(out, end=" ", file=sout_hcp)

                    # add filename
                    out = ": filename(%s)" % "_".join(file_info["parts"])
                    print(out, file=sout)
                    print(out, file=sout_hcp)

                    print("\n" + file_info["parts"][0], file=rout)
                    print(
                        "".join(["-" for e in range(len(file_info["parts"][0]))]),
                        file=rout,
                    )
                    print(
                        "%-25s : %.8f"
                        % (
                            "_hcp_%ssamplespacing" % (file_info["parts"][0][:2]),
                            file_info["json"].get("EffectiveEchoSpacing", -0.009),
                        ),
                        file=rout,
                    )
                    print(
                        "%-25s : %s"
                        % (
                            "_hcp_unwarpdir",
                            unwarp[file_info["json"].get("ReadoutDirection", None)],
                        ),
                        file=rout,
                    )

                elif file_info["parts"][0] in ["AFI"]:
                    phenc = file_info["json"].get("PhaseEncodingDirection", None)
                    out = "%02d: %-20s: %-30s" % (
                        imgn,
                        "TB1" + file_info["parts"][0],
                        "_".join(file_info["parts"]),
                    )
                    if phenc:
                        out += ": phenc(%s)" % (phenc)

                    print(out, end=" ", file=sout)
                    print(out, end=" ", file=sout_hcp)

                    # add filename
                    out = ": filename(%s)" % "_".join(file_info["parts"])
                    print(out, file=sout)
                    print(out, file=sout_hcp)

                    print("\n" + "TB1" + file_info["parts"][0], file=rout)
                    print(
                        "".join(["-" for e in range(len(file_info["parts"][0]))]),
                        file=rout,
                    )

                elif file_info["parts"][0] in ["BIAS"]:
                    phenc = file_info["json"].get("PhaseEncodingDirection", None)
                    if re.match(r"^\d+CH$", file_info["parts"][1]):
                        tag = "RB1COR-Head"
                    elif file_info["parts"][1] == "BC":
                        tag = "RB1COR-Body"
                    out = "%02d: %-20s: %-30s" % (
                        imgn,
                        tag,
                        "_".join(file_info["parts"]),
                    )
                    if phenc:
                        out += ": phenc(%s)" % (phenc)

                    print(out, end=" ", file=sout)
                    print(out, end=" ", file=sout_hcp)

                    # add filename
                    out = ": filename(%s)" % "_".join(file_info["parts"])
                    print(out, file=sout)
                    print(out, file=sout_hcp)

                    print("\n" + tag, file=rout)
                    print(
                        "".join(["-" for e in range(len(file_info["parts"][0]))]),
                        file=rout,
                    )

                elif file_info["parts"][0] in ["B1"]:
                    phenc = file_info["json"].get("PhaseEncodingDirection", None)
                    out = "%02d: %-20s: %-30s" % (
                        imgn,
                        file_info["parts"][1],
                        "_".join(file_info["parts"]),
                    )
                    if phenc:
                        out += ": phenc(%s)" % (phenc)

                    print(out, end=" ", file=sout)
                    print(out, end=" ", file=sout_hcp)

                    # add filename
                    out = ": filename(%s)" % "_".join(file_info["parts"])
                    print(out, file=sout)
                    print(out, file=sout_hcp)

                    print("\n" + file_info["parts"][0], file=rout)
                    print(
                        "".join(["-" for e in range(len(file_info["parts"][0]))]),
                        file=rout,
                    )

                print("%s => %s" % (file_info["path"], tfile), file=bout)
            else:
                all_ok = False
                log.error(
                    "Linking failed: %02d.nii.gz <-- %s" % (imgn, file_info["name"])
                )
                print("FAILED: %s => %s" % (file_info["path"], tfile), file=bout)

            status = True
            if (
                "dMRI" in file_info["parts"] or "DWI" in file_info["parts"]
            ) and "SBRef" not in file_info["parts"]:
                status_a = gc.move_link_or_copy(
                    file_info["path"].replace(".nii.gz", ".bvec"),
                    tfile.replace(".nii.gz", ".bvec"),
                    action="link",
                )
                if status_a:
                    print(
                        "%s => %s"
                        % (
                            file_info["path"].replace(".nii.gz", ".bvec"),
                            tfile.replace(".nii.gz", ".bvec"),
                        ),
                        file=bout,
                    )

                status_b = gc.move_link_or_copy(
                    file_info["path"].replace(".nii.gz", ".bval"),
                    tfile.replace(".nii.gz", ".bval"),
                    action="link",
                )
                if status_b:
                    print(
                        "%s => %s"
                        % (
                            file_info["path"].replace(".nii.gz", ".bval"),
                            tfile.replace(".nii.gz", ".bval"),
                        ),
                        file=bout,
                    )

                if not all([status_a, status_b]):
                    log.error(
                        "bval/bvec files were not found and were not mapped: %02d.bval/.bvec <-- %s"
                        % (imgn, file_info["name"].replace(".nii.gz", ".bval/.bvec"))
                    )
                    all_ok = False

    sout.close()
    sout_hcp.close()
    bout.close()

    if not all_ok:
        raise ge.CommandFailed(
            "map_hcpls2nii",
            "Not all actions completed successfully!",
            "Some files for session %s were not mapped successfully!" % (session),
            "Please check logs and data!",
        )

    return imgn, nmapped
