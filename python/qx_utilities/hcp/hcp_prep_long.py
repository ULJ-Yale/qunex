#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_prep_long.py``

Preparation of sessions for the longitudinal HCP pipelines.
"""

import os
import os.path

import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.processing.core as pc
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    _check_hcp_info,
    do_hcp_options_check,
)


def hcp_prep_long(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_prep_long [... processing options]``

    Prepare the data for longitudinal processing with HCP longitudinal
    pipelines. Not needed if the starting point is hcp_long_freesurfer as that
    command does the prep work automatically.

    For each subject in the batch file, QuNex will get their sessions and
    prepare a suitable subject folder by symlinking relevant folders into it. It
    will symlink both regular session folders and longitudinal sessions folders
    (defined by hcp_longitudinal_template) if they are present.

    ..  qx_command:
        type: processing.subject

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

    Output files:
        The results of this step will be present in the
        <study_folder>/subjects.

    Examples:
        ::

            qunex hcp_prep_long \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_longitudinal_template="base"
    """

    subject_id = sinfo[0]["subject"]

    log = SessionLog({"id": subject_id}, options, "HCP prep long", label="Subject")

    status = "=> processing completed"
    result = {"done": [], "failed": [], "ready": [], "not ready": []}
    failed = 0

    try:
        # checks
        pc.do_options_check(options, sinfo[0], "hcp_prep_long")
        do_hcp_options_check(options, "hcp_prep_long")
        # raises if any session in the batch is missing its hcp info
        _check_hcp_info(sinfo, options)

        # sort out the folder structure
        sessionsfolder = options["sessionsfolder"]
        subjectsfolder = sessionsfolder.replace("sessions", "subjects")
        if not os.path.exists(subjectsfolder):
            os.makedirs(subjectsfolder)
        study_folder = os.path.join(subjectsfolder, subject_id)
        if not os.path.exists(study_folder):
            os.makedirs(study_folder)

        # symlink sessions
        for session in sinfo:
            source_dir = os.path.join(session["hcp"], session["id"])
            if not os.path.exists(source_dir):
                log.raw(f"\n---> ERROR: {source_dir} does not exists, cannot map into longutidinal folder structure!")
                result["failed"] = session["id"]

            target_dir = os.path.join(study_folder, session["id"])
            gc.link_or_copy(source_dir, target_dir, symlink=True)
            result["done"] = session["id"]

    except ge.CommandFailed as e:
        log.raw("\n" + ge.report_command_failed("hcp_prep_long", e))
        status = "processing failed"
        failed += 1
    except ge.CommandError as e:
        log.raw("\n" + ge.report_command_error("hcp_prep_long", e))
        status = "processing failed"
        failed += 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        status = "Error"
        failed = 1
    except Exception:
        log.unknown_error()
        status = "Error"
        failed = 1

    log.close(pipeline="HCP prep long")

    report = f"sessions: {len(result['done'])} done [{result['done']}], {len(result['failed'])} failed [{result['failed']}] => {status}"
    failed = len(result["failed"]) if len(result["failed"]) > 0 else failed
    return log.result((subject_id, report, failed))
