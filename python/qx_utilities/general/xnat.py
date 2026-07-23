#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``recipe.py``

Run recipe framework.
"""

"""
Copyright (c) Grega Repovs and Jure Demsar. All rights reserved.
"""

import os.path
import os
import glob
import subprocess
from datetime import datetime
import qx_utilities.general.exceptions as ge


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
    cmd_s = " ".join(cmd)
    summary = "\nRunning: " + cmd_s
    cmd_p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0
    )
    summary += "\n          --- stdout start --- \n"
    for line in iter(cmd_p.stdout.readline, b""):
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

    out_path = (
        os.environ["SESSIONS_FOLDER"] + "/checkpoints/" + step + ":" + suffix + ".txt"
    )
    with open(out_path, "w") as fp:
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
    # Dicoms are deleted XNAT, so /dicom/ only contains logs
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

        in_path = "/input/SCANS"
        out_path = os.path.join(
            os.environ["SESSIONS_FOLDER"], os.path.join(os.environ["LABEL"], "inbox")
        )
        cmd = ["rsync", "-avzh", in_path, out_path]
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
        in_path = os.environ["SESSIONS_FOLDER"] + "/" + os.environ["LABEL"] + "/inbox"
        cmd = ["rm", "-rf", in_path]
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

        in_path = (
            os.environ["XNAT_HOST"]
            + "/data/projects/"
            + os.environ["XNAT_PROJECT"]
            + "/resources/QUNEX_PROC/files/"
            + os.environ["SCAN_MAPPING_FILENAME"]
        )
        out_path = os.environ["MAPPING"]
        cmd = [
            "curl",
            "-k",
            "-u",
            os.environ["XNAT_USER"] + ":" + os.environ["XNAT_PASS"],
            "-X",
            "GET",
            in_path,
            "-o",
            out_path,
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

        in_path = (
            os.environ["XNAT_HOST"]
            + "/data/projects/"
            + os.environ["XNAT_PROJECT"]
            + "/resources/QUNEX_PROC/files/"
            + os.environ["BATCH_PARAMETERS_FILENAME"]
        )
        out_path = os.environ["INITIAL_PARAMETERS"]
        cmd = [
            "curl",
            "-k",
            "-u",
            os.environ["XNAT_USER"] + ":" + os.environ["XNAT_PASS"],
            "-X",
            "GET",
            in_path,
            "-o",
            out_path,
        ]
        summary += xnat_run_cmd(cmd)

    summary += "\n\n----==== XNAT CREATE_BATCH EXECUTION END ====----\n\n"
    print(summary)
    return summary
