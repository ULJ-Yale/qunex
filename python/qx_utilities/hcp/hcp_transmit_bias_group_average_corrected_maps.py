#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_transmit_bias_group_average_corrected_maps.py``

The HCP transmit bias pipeline, phase 4: group average corrected maps.
"""

import os
import os.path
import traceback

import qx_utilities.processing.core as pc

from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    handle_hcp_links,
    do_hcp_options_check,
    write_transmit_bias_voltages,
)


def hcp_transmit_bias_group_average_corrected_maps(sessions, options, overwrite=True, thread=0):
    """
    ``hcp_transmit_bias_group_average_corrected_maps [... processing options]``

    Runs the HCP Transmit Bias Pipeline Phase 4, Group Average Corrected Maps.

    ..  qx_command:
        type: processing.study

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

        --hcp_regname (str, default 'MSMSulc'):
            Input registration name.

        --hcp_transmit_mode (str, default ''):
            What type of transmit bias correction to apply, options and required
            inputs are:

            a) AFI: actual flip angle sequence with two different echo times,
            requires the following parameters: afi-tr-one,afi-tr-two,
            afi-angle, transmit-group-name.

            b) B1Tx: b1 transmit sequence magnitude/phase pair, requires the
            following parameters: transmit-group-name.

            c) PseudoTransmit: use spin echo fieldmaps, SBRef, and a
            template transmit-corrected myelin map to derive empirical
            correction, requires the following parameters: average-myelin, group-average-name, voltages

        --hcp_transmit_group_name (str, default ''): 
            Name for the subgroup of subjects that have good AFI or B1Tx data (e.g. Partial)

        --hcp_average_myelin (str, default ''):
            CIFTI file of group average uncorrected myelin.

        --hcp_outgroupname (str, default ''):
            Output folder inside studyfolder

        --hcp_voltages (str, default ''):
            Text file of scanner calibrated transmit voltages for each subject. If the file does not exist, QuNex will attempt to create it by extracting TxrefAmp from 
            each session's JSON metadata file. 

        --hcp_afi_tr_one (str, default ''):
            TR of first AFI frame.

        --hcp_afi_tr_two (str, default ''):
            TR of second AFI frame.

        --hcp_afi_angle (str, default ''):
            Target flip angle of AFI sequence.

        --hcp_lowresmesh (int, default 32):
            Mesh resolution.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

    Notes:
        hcp_transmit_bias_group_average_corrected_maps parameter mapping:

            ================================== ============================
            QuNex parameter                    HCPpipelines parameter
            ================================== ============================
            ``sessionsfolder``                 ``study-folder``
            ``sessions`` / session list        ``subject-list``
            ``hcp_regname``                    ``reg-name``
            ``hcp_transmit_mode``              ``mode``
            ``hcp_outgroupname``               ``group-average-name``
            ``hcp_transmit_group_name``        ``transmit-group-name``
            ``hcp_voltages``                   ``voltages``
            ``hcp_afi_tr_one``                 ``afi-tr-one``
            ``hcp_afi_tr_two``                 ``afi-tr-two``
            ``hcp_afi_angle``                  ``afi-angle``
            ``hcp_average_myelin``             ``average-myelin``
            ``hcp_lowresmesh``                 ``low-res-mesh``
            ``hcp_matlab_mode``                ``matlab-run-mode``
            ================================== ============================

    Examples:
        Example run::

            qunex hcp_transmit_bias_group_average_corrected_maps \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"

    """

    sessionids = sessions.get_list_by_key("id", sep=",")
    log = SessionLog({"id": sessionids}, options, "HCP Transmit Bias Pipeline Phase 4, Group Average Corrected Maps", label="Session ids")

    run = True
    report = "Error"

    try:
        do_hcp_options_check(options, "hcp_transmit_bias_group_average_corrected_maps")
        subject_list = ""
        
        for session in sessions:
            # resolves and validates the session HCP paths
            get_hcp_paths(session, options)
            if "hcp" not in session:
                log.raw("\n---> ERROR: There is no hcp info for session %s in batch.txt"
                    % (session["id"]))
                run = False

            # subject_list
            if subject_list == "":
                subject_list = session["id"] + options["hcp_suffix"]
            else:
                subject_list = (
                    subject_list + "@" + session["id"] + options["hcp_suffix"]
                )

        outgroupname = ""
        if options["hcp_outgroupname"] is None:
            log.error("hcp_outgroupname is not provided!")
            run = False
        else:
            outgroupname = options["hcp_outgroupname"]

        if len(sessions) == 1:
            log.error("hcp_transmit_bias_group_average_corrected_maps needs to be ran across several sessions!")
            run = False

        # multi session
        else:
            # set study dir
            study_dir = os.path.join(
                options["sessionsfolder"], "transmit_bias"
            )
            handle_hcp_links(study_dir, sessions, options, False)

        if options["hcp_transmit_mode"] is None:
            log.error("the hcp_transmit_mode parameter is mandatory!")
            run = False

        
        voltages_file = ""

        if not options["hcp_voltages"]:
            log.error("the hcp_voltages parameter is mandatory!")
            run = False
        else:
            voltages_file = options["hcp_voltages"]

            if os.path.exists(voltages_file):
                log.raw(f"\n---> Using existing hcp_voltages file: {voltages_file}")
            else:
                log.raw(f"\n---> hcp_voltages file does not exist. Creating it: {voltages_file}")
                run = write_transmit_bias_voltages(
                    sessions, options, voltages_file, log
                )

        # build the command
        if run:

            matlabrunmode = None
            if options["hcp_matlab_mode"]:
                if options["hcp_matlab_mode"] == "compiled":
                    matlabrunmode = "0"
                elif options["hcp_matlab_mode"] == "interpreted":
                    matlabrunmode = "1"
                elif options["hcp_matlab_mode"] == "octave":
                    matlabrunmode = "2"
                else:
                    log.raw("\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n")
                    run = False
            else:
                matlabrunmode = "0"

            
            comm = (
                '%(script)s \
                --study-folder="%(studyfolder)s" \
                --subject-list="%(subjectlist)s" \
                --mode="%(mode)s" \
                --reg-name="%(reg_name)s" \
                --group-average-name="%(group_average_name)s" \
                --voltages="%(voltages)s" \
                --matlab-run-mode="%(matlab_run_mode)s"'
                % {
                    "script": os.path.join(
                        os.environ["HCPPIPEDIR"], "TransmitBias", "Phase4_GroupAverageCorrectedMaps.sh"
                    ),
                    "studyfolder": study_dir,
                    "subjectlist": subject_list,
                    "mode": options["hcp_transmit_mode"],
                    "reg_name": options["hcp_regname"],
                    "group_average_name": outgroupname,
                    "voltages": voltages_file,
                    "matlab_run_mode": matlabrunmode,
                }
            )

            # check and set parameters given the mode
        
            
            # AFI and B1Tx parameters
            if (options["hcp_transmit_mode"] == "AFI") or (options["hcp_transmit_mode"] == "B1Tx"):

                if options["hcp_transmit_group_name"]:
                    comm += f"                --transmit-group-name={options['hcp_transmit_group_name']}"
                else:
                    log.error("the hcp_transmit_group_name parameter is not provided!")
                    run = False

            # AFI
            if options["hcp_transmit_mode"] == "AFI":

                if options["hcp_afi_tr_one"]:
                    comm += f"                --afi-tr-one={options['hcp_afi_tr_one']}"
                else:
                    log.error("the hcp_afi_tr_one parameter is not provided!")
                    run = False

                if options["hcp_afi_tr_two"]:
                    comm += f"                --afi-tr-two={options['hcp_afi_tr_two']}"
                else:
                    log.error("the hcp_afi_tr_two parameter is not provided!")
                    run = False

                if options["hcp_afi_angle"]:
                    comm += f"                --afi-angle={options['hcp_afi_angle']}"
                else:
                    log.error("the hcp_afi_angle parameter is not provided!")
                    run = False


            # PseudoTransmit
            elif options["hcp_transmit_mode"] == "PseudoTransmit":
                if options["hcp_average_myelin"]:
                    comm += f"                --average-myelin={options['hcp_average_myelin']}"
                else:
                    log.error("the hcp_average_myelin parameter is not provided!")
                    run = False
            else:
                log.error("Unknown mode for hcp_transmit_mode, use AFI, B1Tx or PseudoTransmit!")
    

            # optional general parameters
            if options["hcp_lowresmesh"]:
                comm += f"                --low-res-mesh={options['hcp_lowresmesh']}"

    
            # -- Report command
            if run:
                log.raw("\n\n------------------------------------------------------------\n")
                log.raw("Running HCP Pipelines command via QuNex:\n\n")
                log.raw(comm.replace("                --", "\n    --"))
                log.raw("\n------------------------------------------------------------\n")

        # -- Run
        if run:
            if options["run"] == "run":
                endlog, report, failed = log.run_external(
                    None,
                    comm,
                    "Running HCP Transmit Bias Phase 4, Group Average Corrected Maps",
                    overwrite=overwrite,
                    thread=options["hcp_outgroupname"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    full_test=None,
                    shell=True,
                )

                # #Remove soft links
                # handle_hcp_links(study_dir, sessions, options, True)

            # -- just checking
            else:
                passed, report, failed = log.check_run(
                    None,
                    None,
                    "HCP Transmit Bias Phase 4, Group Average Corrected Maps",
                    overwrite=overwrite,
                )
                if passed is None:
                    log.step("HCP Transmit Bias Phase 4, Group Average Corrected Maps can be run")
                    report = "HCP Transmit Bias Phase 4, Group Average Corrected Maps can be run"
                    failed = 0

        else:
            log.step("Session cannot be processed.")
            report = "HCP Transmit Bias Phase 4, Group Average Corrected Maps cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.capture(str(errormessage))
        failed = 1
    except Exception as e:
        log.raw(f"\nERROR: {e}")
        log.raw(f"\nERROR: Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n")
        failed = 1

    #Remove soft links to prevent clutter
    #handle_hcp_links(study_dir, sessions, options, True)

    log.close(pipeline="HCP Transmit Bias Phase 4, Group Average Corrected Maps Preprocessing")

    return log.result((sessionids, report, failed))
