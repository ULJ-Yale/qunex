#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``nii2bids.py``

Maps the sessions' nii images to BIDS: the ``map_nii2bids`` command.

The images, their BIDS entities and the fieldmaps each of them is corrected
with come from the session record: the batch file's, when it holds the
session's mapped images, else the session's ``session_hcp.txt``. Their names
are built by ``bids_names.py``.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import glob
import json
import os
import re
import shutil
import sys
from datetime import datetime

import yaml

import qx_utilities.general.bids_names as bn
import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.folders as gf
import qx_utilities.general.log as gl


def map_nii2bids(
    sinfo,
    options,
    overwrite=False,
    thread=0,
    action="hardlink",
    session_mapping_file=None,
):
    """
    ``map_nii2bids [batchfile=''] [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [sessions=''] [overwrite='no'] [action='hardlink'] [session_mapping_file=None]``

    Maps images from the sessions's nii folder to BIDS structure.

    ..  qx_command:
        type: processing.study

    Description:
        Maps data from the `nii` folder to the `bids` folder. The images and
        their BIDS entities are read from the session record: from the batch
        file, when it was made from `session_hcp.txt` files, else from each
        session's `session_hcp.txt`. Entities (key-value) pairs should be
        specified by the user in `hcp_mapping.txt` file and `session_hcp.txt`
        should be created using the `create_session_info` function. Suffix is
        inferred from data, but can be specified manually in case of ambiguity
        (e.g. for fieldmaps).

        Images that would get the same BIDS name, such as repeated T1w images
        or several spin echo fieldmap pairs, are told apart by the `run`
        entity. The images of a fieldmap set are numbered by its `se()` or
        `fm()` number, so that the images of a set keep matching, a boldref
        takes the run of its bold, and other images are numbered in the order
        of the session file. An image whose `run` is specified keeps it.

        The label of a DWI image, `<label>_<direction>` (e.g. `DWI:dir98_AP`),
        gives its `acq` and `dir` entities (`acq-dir98_dir-AP`).

        A fieldmap's `IntendedFor` is filled in from the session record when
        its sidecar has none: a spin echo fieldmap is intended for the images
        that name its `se()`, a gradient echo fieldmap for those that name its
        `fm()`. The images are given as BIDS URIs
        (`bids::sub-<subject>/ses-<session>/func/<image>.nii.gz`). A bold
        image's `TaskName`, which BIDS requires, is filled in from its task in
        the same way. A sidecar that gains a field is written to the `bids`
        folder as a new file, so the one in the `nii` folder stays as it is.

        In case session name contains non-alphanumeric characters, these characters
        will be replaced with 'x' in the BIDS session name.

        See examples below for details.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --studyfolder (str):
            The path to the study folder. The sessions are in its `sessions`
            folder, unless --sessionsfolder names another one.

        --sessionsfolder (str, default '<studyfolder>/sessions'):
            The path to the folder with the sessions. Set it only when the
            sessions are not in the `sessions` folder of the study. With
            neither --studyfolder nor --sessionsfolder given, the current
            folder is used.

        --sessions (str, default ''):
            The comma separated list of sessions to process. If not specified,
            all sessions will be processed.

        --overwrite (str, default 'no'):
            Parameter that specifies what should be done in cases where there
            are existing data stored in `bids` folder.
            The options are:

            - 'no'  ... do not overwrite the data, report an error and stop
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

            qunex map_nii2bids \\
              --studyfolder="/data/studies/fMRI/import_bids_test" \\
              --batchfile="/data/studies/fMRI/import_bids_test/processing/batch.txt" \\
              --sessions="01_1" \\
              --overwrite='yes'

        In this example, the following mappings are performed:

        - 7.nii.gz --> `sub-01_ses-1_run-2_magnitude2.nii.gz`

        Note that the suffix has been explicitly defined as `magnitude2`,
        otherwise it would implicitly be set to `magnitude`.

        - `11.nii.gz` --> `sub-01_ses-1_task-rest_acq-fullbrain_run-2_bold.nii.gz`

        In this case suffix was inferred from the image type. Key-value pairs
        not defined in BIDS are ignored (e.g. `fm` in the above case)

        Note that optional BIDS entities (e.g. acq) should be specified
        manually as key-value pairs in hcp_mapping.txt; `run` is added where
        the names would otherwise clash.

        With two spin echo fieldmap pairs::

            71  :SE-FM-AP        :SpinEchoFieldMap_AP: se(1)
            81  :SE-FM-PA        :SpinEchoFieldMap_PA: se(1)
            101 :bold1:rest      :rfMRI_REST_AP: se(1): phenc(AP)
            271 :SE-FM-AP        :SpinEchoFieldMap_AP: se(2)
            281 :SE-FM-PA        :SpinEchoFieldMap_PA: se(2)
            301 :DWI:dir98_AP    :dMRI_dir98_AP: se(2)

        the mappings are:

        - `71.nii.gz` --> `sub-01_ses-1_dir-AP_run-1_epi.nii.gz`, intended
          for `bids::sub-01/ses-1/func/sub-01_ses-1_task-rest_dir-AP_bold.nii.gz`
        - `271.nii.gz` --> `sub-01_ses-1_dir-AP_run-2_epi.nii.gz`, intended
          for `bids::sub-01/ses-1/dwi/sub-01_ses-1_acq-dir98_dir-AP_dwi.nii.gz`
        - `301.nii.gz` --> `sub-01_ses-1_acq-dir98_dir-AP_dwi.nii.gz`

        and the PA images in the same way.

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

    # a processing command builds its own log and returns its text; `gp.run`
    # puts that in the session log. `nii2bids.log` and its `file=bout` writes
    # are a data artifact and stay exactly as they are.
    log = gl.ReportLog()

    if "action" in options:
        action = options["action"]
    if action not in ["hardlink", "copy"]:
        raise ge.CommandError(
            "map_nii2bids",
            "Invalid option for action specified",
            "%s is not a valid option for the action parameter!" % (action),
            "Please specify one of: hardlink, copy!",
        )

    if "session_mapping_file" in options:
        session_mapping_file = options["session_mapping_file"]

    if session_mapping_file is not None:
        with open(session_mapping_file) as mapping_file:
            remaps = yaml.safe_load(mapping_file)
        log.step(f"Session mapping file {session_mapping_file} loaded")
    else:
        remaps = {}

    test = options.get("run") == "test"

    for session_info in sinfo:
        # the session's folder is the one named after it in the sessions
        # folder. Its folders are the ones the batch file names, else the
        # ones session_hcp.txt names, else the standard ones in it: a session
        # imported from DICOM has no `bids` entry
        sourcefolder = os.path.join(options["sessionsfolder"], session_info["id"])
        record, source = _session_record(session_info, sourcefolder)
        bidsfolder = (
            session_info.get("bids")
            or record.get("bids")
            or os.path.join(sourcefolder, "bids")
        )
        niifolder = (
            session_info.get("raw_data")
            or record.get("raw_data")
            or os.path.join(sourcefolder, "nii")
        )

        # --- open nii2bids log file
        if overwrite in ["yes", True, "True"]:
            mode = "w"
        else:
            mode = "a"

        # the log is kept in the bids folder, so the folder has to exist first;
        # a dry run creates neither
        if test:
            logfile = os.devnull
        else:
            if not os.path.exists(bidsfolder):
                os.makedirs(bidsfolder)
            logfile = os.path.join(bidsfolder, "nii2bids.log")

        with open(logfile, mode) as bout:
            print(
                "nii to BIDS mapping report, executed on %s"
                % (datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
                file=bout,
            )
            _map_session_nii2bids(
                record,
                source,
                bidsfolder,
                niifolder,
                overwrite,
                action,
                remaps,
                test,
                bout,
                _log=log,
            )

    return log.finish(gl.action("mapping to BIDS completed", options.get("run")))


def _map_session_nii2bids(
    record,
    source,
    bidsfolder,
    niifolder,
    overwrite,
    action,
    remaps,
    test,
    bout,
    *,
    _log,
):
    """
    Map one session's nii images to its bids folder, for map_nii2bids.

    `record` is the session record the images are read from, and `source`
    says where it was read. The mapping report goes to `bout`, the session's
    open `nii2bids.log`, and its warnings to the runlog as well. Under --test
    nothing is created, removed, linked, copied or written: the names are
    built as in a real run and every image that would be mapped is named in
    the log.
    """
    session = record.get("session") or record["id"]
    subject = record.get("subject")
    if not subject:
        raise ge.CommandFailed(
            "map_nii2bids",
            "Missing subject",
            f"The session record of session {session} names no subject!",
            "Please add 'subject: <subject id>' to its session_hcp.txt or batch file!",
        )

    print("", file=sys.stdout)
    _report(f"mapping subject {subject}, session {session}", bout)
    _log.step(f"mapping subject {subject}, session {session}")
    _log.detail(f"reading the session's images from {source}")
    skip, sessionid = _bids_session_id(subject, session, remaps, bout)
    if skip:
        return

    # --- check for presence of nifti files
    cleared = _clear_bids_folder(bidsfolder, overwrite, test, _log=_log)

    # --- name the images, then map them
    images = _session_images(record, niifolder, bout, _log=_log)
    bn.assign_runs(images, subject, sessionid)
    errors = _name_images(images, subject, sessionid, bout, _log=_log)
    intended = _intended_for(images, subject, sessionid)

    # what this run has mapped and created: a dry run writes neither, and a
    # target in a bids folder it would have cleared would be gone
    mapped = set()
    created = set()

    for image in images:
        if image["stem"] is None:
            continue

        # create func, anat, fmap folders if needed
        targetfolder = os.path.join(bidsfolder, image["folder"])
        if not os.path.exists(targetfolder) and targetfolder not in created:
            created.add(targetfolder)
            if test:
                _log.detail(f"test, not created: {targetfolder}")
            else:
                _log.detail(f"creating folder {targetfolder}")
                os.makedirs(targetfolder)

        for file_to_map in image["files"]:
            extension = file_to_map.split(".", 1)[1]
            if not bn.extension_allowed(image["type"], extension):
                _report(
                    f"ERROR: extension {extension} not allowed for {image['type']}, "
                    f"{file_to_map} not mapped",
                    bout,
                )
                errors += 1
                continue

            bids_name = f"{image['stem']}.{extension}"
            target_file = os.path.join(targetfolder, bids_name)
            if target_file in mapped or (
                os.path.exists(target_file) and not (test and cleared)
            ):
                _warn(
                    f"tried to map {file_to_map} to file {bids_name}, but this target already exists in {targetfolder}, check if mapping is unique",
                    bout,
                    _log,
                )
                continue
            mapped.add(target_file)

            source_file = os.path.join(niifolder, file_to_map)
            sidecar = None
            if extension == "json":
                sidecar = _sidecar(image, intended, source_file, bout, _log=_log)
            _place(source_file, target_file, sidecar, action, test, bout, _log=_log)

    if errors > 0:
        if test:
            where = "the output above"
        else:
            where = f"log file {os.path.join(bidsfolder, 'nii2bids.log')}"
        raise ge.CommandFailed(
            "map_nii2bids",
            "Errors during mapping",
            f"Errors occured during mapping, please check {where} for details",
        )


def _report(message, bout):
    """Print a mapping message to the terminal and to `nii2bids.log`."""
    for output in (sys.stdout, bout):
        print(f"... {message}", file=output)


def _warn(message, bout, _log):
    """Report a mapping warning, in the runlog as well."""
    _report(f"WARNING: {message}", bout)
    _log.warning(message)


def _session_record(session_info, sourcefolder):
    """
    The session record the images are mapped from, and where it was read.

    A batch file record made from session_hcp.txt files (marked `hcpready`)
    holds the session's images with their mapping and is used as it is;
    otherwise the session's own session_hcp.txt is read, and the folders it
    names are resolved against the session's folder.
    """
    if session_info.get("hcpready") == "true" and any(
        key.isdigit() for key in session_info
    ):
        return session_info, "the batch file"

    session_file = os.path.join(sourcefolder, "session_hcp.txt")
    if not os.path.exists(session_file):
        raise ge.CommandFailed(
            "map_nii2bids",
            "session_hcp.txt is missing!",
            "Please prepare hcp_mapping.txt file and run create_session_info to prepare 'session_hcp.txt' files",
        )
    record = gc.read_batch(session_file)[0][0]
    return gf.resolve_session_folders(record, sourcefolder), "session_hcp.txt"


def _session_images(record, niifolder, bout, *, _log):
    """
    The session's images that map to BIDS, in the order of the session record.

    Each is a dict: its `id`, `name` and BIDS `type`, the BIDS `folder` and
    `suffix`, `info`, its key-value pairs read as BIDS entities, and `files`,
    its files in the nii folder. `key` and `stem` are filled in later.
    """
    if not os.path.isdir(niifolder):
        raise ge.CommandFailed(
            "map_nii2bids",
            "nii folder is missing!",
            f"The nii folder {niifolder} does not exist!",
            "Please check the session's raw_data folder!",
        )
    available = sorted(os.listdir(niifolder))

    images = []
    for image_id in (key for key in record if key.isdigit()):
        image_info = record[image_id]
        image_type = bn.bids_type(image_info["name"])
        if not image_type:
            _report(f"image {image_id} has no image type, not mapped", bout)
            continue
        if image_type not in bn.bids_mri_types:
            _warn(
                f"image type {image_type} of image {image_id} has no BIDS mapping, skipping",
                bout,
                _log,
            )
            continue

        files = [name for name in available if name.startswith(f"{image_id}.")]
        if not files:
            _warn(f"no files found for id: {image_id}, skipping", bout, _log)
            continue

        kind = bn.bids_mri_types[image_type]
        images.append({
            "id": image_id,
            "name": image_info["name"],
            "type": image_type,
            "folder": kind["folder"],
            "suffix": image_info.get("suffix", kind["suffix"]),
            "info": bn.entity_info(image_info, image_type),
            "files": files,
            "key": None,
            "stem": None,
        })

    return images


def _name_images(images, subject, sessionid, bout, *, _log):
    """
    Build the BIDS name of every image, into its `stem`.

    Reports what could not be named and returns the number of errors.
    """
    errors = 0
    for image in images:
        image["stem"], problems = bn.bids_stem(
            subject, image["info"], image["type"], image["suffix"], sessionid
        )
        for level, message in problems:
            if level == "warning":
                _warn(message, bout, _log)
            else:
                _report(f"ERROR: {message}", bout)
                errors += 1

        if image["stem"] is None:
            _report(
                f"ERROR: could not create BIDS name for image {image['id']}, skipping",
                bout,
            )
            errors += 1

    return errors


def _intended_for(images, subject, sessionid):
    """
    The images each fieldmap is intended for, from the session record.

    A spin echo fieldmap is intended for the images that name its se(), any
    other fieldmap for the images that name its fm(). Returns, by fieldmap id,
    a pair: the images' BIDS URIs in the order of the session record, and why
    there are none, for when there are none.
    """
    root = f"bids::sub-{subject}/" + (f"ses-{sessionid}/" if sessionid else "")
    intended = {}
    for fieldmap in images:
        if fieldmap["folder"] != "fmap" or fieldmap["stem"] is None:
            continue

        tag = bn.fieldmap_tag(fieldmap)
        number = bn.fieldmap_number(fieldmap)
        if number is None:
            intended[fieldmap["id"]] = (
                [],
                f"the session file gives image {fieldmap['id']} no {tag}() number",
            )
            continue

        targets = [
            f"{root}{image['folder']}/{image['stem']}.{extension}"
            for image in images
            if image["folder"] != "fmap"
            and image["stem"] is not None
            and str(image["info"].get(tag)) == number
            for extension in (name.split(".", 1)[1] for name in image["files"])
            if extension in ("nii", "nii.gz")
        ]
        intended[fieldmap["id"]] = (
            targets,
            f"no image in the session file names {tag}({number})",
        )

    return intended


def _sidecar(image, intended, source_file, bout, *, _log):
    """
    The BIDS sidecar of an image, when it needs what its nii sidecar lacks.

    A fieldmap's IntendedFor and a bold's TaskName are filled in from the
    session record when the nii sidecar has none; a magnitude image needs no
    IntendedFor. Returns `(sidecar, added)`, the sidecar to write and what was
    added to it, or None when the nii sidecar is mapped as it is.
    """
    wants_intended = image["folder"] == "fmap" and not image["suffix"].startswith(
        "magnitude"
    )
    task = image["info"].get("task")
    wants_task = image["suffix"] == "bold" and bool(task)
    if not (wants_intended or wants_task):
        return None

    try:
        with open(source_file, encoding="utf-8") as json_file:
            sidecar = json.load(json_file)
    except ValueError as error:
        _warn(
            f"could not read {os.path.basename(source_file)} [{error}], mapped as it is",
            bout,
            _log,
        )
        return None

    added = []
    if wants_intended and "IntendedFor" not in sidecar:
        targets, reason = intended.get(image["id"], ([], "it can not be named"))
        if targets:
            sidecar["IntendedFor"] = targets
            shown = ", ".join("/".join(target.split("/")[-2:]) for target in targets)
            added.append(f"IntendedFor {shown}")
        else:
            _warn(
                f"IntendedFor of {image['stem']} not set, {reason}", bout, _log
            )
    if wants_task and "TaskName" not in sidecar:
        sidecar["TaskName"] = task
        added.append(f"TaskName {task}")

    return (sidecar, added) if added else None


def _place(source_file, target_file, sidecar, action, test, bout, *, _log):
    """
    Link or copy one file into the bids folder, or write its sidecar.

    A sidecar with additions is written as a new file, never through a link,
    so the nii folder's stays as it is.
    """
    name = os.path.basename(source_file)
    shown = "/".join(target_file.split(os.sep)[-2:])

    if sidecar is not None:
        content, added = sidecar
        if test:
            _log.detail(f"test, not written: {name} -> {shown}, adding {'; '.join(added)}")
            return
        _report(f"writing {name} to {shown}, adding {'; '.join(added)}", bout)
        with open(target_file, "w", encoding="utf-8") as json_file:
            json.dump(content, json_file, indent="\t", ensure_ascii=False)
            json_file.write("\n")
        return

    if test:
        verb = "linked" if action == "hardlink" else "copied"
        _log.detail(f"test, not {verb}: {name} -> {shown}")
        return

    verb = "linking" if action == "hardlink" else "copying"
    _report(f"{verb} {name} to {shown}", bout)
    if action == "hardlink":
        os.link(source_file, target_file)
    else:
        shutil.copy(source_file, target_file)


def _bids_session_id(subject, session, remaps, bout):
    """
    The BIDS session label of a session, for map_nii2bids.

    Returns `(skip, sessionid)`. `skip` is True when the session mapping file
    remaps the session to a label that is not alphanumeric, and `sessionid` is
    None when the session is named after its subject.
    """
    if subject in remaps.keys():
        if session in remaps[subject].keys():
            sessionid = remaps[subject][session]
            if not sessionid.isalnum():
                _report(
                    "WARNING: session name contains non-alphanumeric characters, skipping",
                    bout,
                )
                return True, None
            _report(f"remapping session {session} to {sessionid}", bout)
        else:
            sessionid = session
    elif session == subject:
        sessionid = None
    else:
        replacement = "x"
        sessionid = (session.split("_"))[1:]
        sessionid = replacement.join(sessionid)
        if not sessionid.isalnum():
            _report(
                f"WARNING: session name contains non-alphanumeric characters, replacing them with {replacement}",
                bout,
            )
            sessionid = re.sub(r"[^a-zA-Z0-9]", replacement, sessionid)

    return False, sessionid


def _clear_bids_folder(bidsfolder, overwrite, test, *, _log):
    """
    Empty a bids folder that already holds images, for map_nii2bids.

    With `overwrite` set, removes everything but `nii2bids.log`, which the run
    is already writing to; without it, raises CommandFailed. Under --test
    nothing is removed and every entry that would be is named instead.

    Returns True when the folder held images, so that a dry run knows its
    existing targets would have been removed.
    """
    if not glob.glob(os.path.join(bidsfolder, "*/*.nii*")):
        return False

    if overwrite not in ["yes", True, "True"]:
        raise ge.CommandFailed(
            "map_nii2bids",
            "Existing files present!",
            "There are existing files in the bids folder [%s]" % (bidsfolder),
            "Please check or set parameter 'overwrite' to yes!",
        )

    if test:
        _log.step(f"existing files in the bids folder {bidsfolder} would be removed")

    # everything but the log this run is already writing to
    for entry in sorted(os.listdir(bidsfolder)):
        if entry == "nii2bids.log":
            continue
        path = os.path.join(bidsfolder, entry)
        if test:
            _log.detail(f"test, not removed: {entry}")
        elif os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

    if not test:
        _log.step("cleaned bids folder, removed existing files")
    return True
