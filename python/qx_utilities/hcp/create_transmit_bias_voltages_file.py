#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``create_transmit_bias_voltages_file.py``

Creation of the transmit bias voltages file used by the HCP transmit bias
group average corrected maps (phase 4) pipeline.
"""


import qx_utilities.processing.core as pc
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import write_transmit_bias_voltages


def create_transmit_bias_voltages_file(sessions, options, overwrite=True, thread=0):
    """
    ``create_transmit_bias_voltages_file [... processing options]``

    Create the transmit bias voltages file for a group of sessions.

    Reads the ``TxRefAmp`` value from each session's unprocessed rfMRI_REST1_AP
    JSON sidecar and writes one value per line, in session order, to the file
    given by ``--hcp_voltages``. The HCP transmit bias phase 4 pipeline
    (hcp_transmit_bias_group_average_corrected_maps) consumes this file, and
    creates it itself when it is missing -- this command lets you generate and
    inspect it up front.

    ..  qx_command:
        type: processing.study

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --hcp_voltages (str, default ''):
            Path of the voltages file to create. Mandatory.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

    Output files:
        The voltages file at the path given by ``--hcp_voltages``, holding one
        TxRefAmp value per line in session order.

    Examples:
        ::

            qunex create_transmit_bias_voltages_file \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_voltages="<path_to_study_folder>/processing/voltages.txt"
    """

    sessionids = sessions.get_list_by_key("id", sep=",")
    log = SessionLog(
        {"id": sessionids}, options, "Create transmit bias voltages file",
        mode=False, label="Session ids",
    )

    report = "Error"
    failed = 0

    try:
        if not options["hcp_voltages"]:
            log.error("the hcp_voltages parameter is mandatory!")
            report = "voltages file not created"
            failed = 1
        else:
            voltages_file = options["hcp_voltages"]
            if options["run"] == "run":
                if write_transmit_bias_voltages(sessions, options, voltages_file, log):
                    report = "voltages file created"
                else:
                    report = "voltages file not created"
                    failed = 1
            else:
                log.step("voltages file would be created: %s", voltages_file)
                report = "voltages file can be created"

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        report = "voltages file not created"
        failed = 1
    except Exception:
        log.unknown_error()
        report = "voltages file not created"
        failed = 1

    return log.finish(report, failed, pipeline="Create transmit bias voltages file")
