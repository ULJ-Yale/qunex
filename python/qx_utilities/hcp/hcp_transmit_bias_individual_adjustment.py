#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_transmit_bias_individual_adjustment.py``

The HCP transmit bias pipeline, phase 3: individual adjustment.
"""

import os
import os.path
import traceback

import qx_utilities.processing.core as pc

from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import do_hcp_options_check


def hcp_transmit_bias_individual_adjustment(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_transmit_bias_individual_adjustment([... processing options])``

    Runs the HCP Transmit Bias Pipeline Phase 3, Individual Adjustment.
    
    ..  qx_command:
        type: processing.session

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

        --hcp_gmwm_template (str, default ''):
            Location of the GMWMtemplate, the file containing GM+WM volume ROI.

        --hcp_regname (str, default 'MSMSulc'):
            Input registration name.

        --hcp_transmit_mode (str, default ''):
            What type of transmit bias correction to apply, options and required
            inputs are:

            a) AFI: actual flip angle sequence with two different echo times,
            requires the following parameters: afi-tr-one,afi-tr-two,afi-angle, group-corrected-myelin.

            b) B1Tx: b1 transmit sequence magnitude/phase pair, requires the
            following parameters: group-corrected-myelin.

            c) PseudoTransmit: use spin echo fieldmaps, SBRef, and a
            template transmit-corrected myelin map to derive empirical
            correction, requires the following parameters: myelin-template, group-uncorrected-myelin, reference-value.

        --hcp_group_corrected_myelin (str, default ''):
            The group-corrected myelin file from AFI or B1Tx.

        --hcp_afi_tr_one (str, default ''):
            TR of first AFI frame.

        --hcp_afi_tr_two (str, default ''):
            TR of second AFI frame.

        --hcp_afi_angle (str, default ''):
            Target flip angle of AFI sequence.


        --hcp_myelin_template (str, default ''):
            Expected transmit-corrected group-average myelin pattern (for testing
            correction parameters).

        --hcp_group_uncorrected_myelin (str, default ''):
            The group-average uncorrected myelin file (to set the appropriate
            scaling of the myelin template).

        --hcp_pt_reference_value_file (str, default ''):
            Text file containing the value in the pseudotransmit map where the
            flip angle best matches the intended angle, from the Phase2 group
            script.

        --hcp_transmit_res (str, default ''):
            Resolution to use for transmit field, default equal to
            hcp_grayordinatesres.

        --hcp_regname (str, default 'MSMSulc'):
            The name of the registration used.

        --hcp_lowresmesh (int, default 32):
            Mesh resolution.

        --hcp_grayordinatesres (int, default 2):
            The size of voxels for the subcortical and cerebellar data in
            grayordinate space in mm.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_manual_receive (str, default ''):
            Whether Phase1 used unprocessed scans to correct for not using PSN when acquiring scans.

    Notes:
        hcp_transmit_bias_individual_adjustment parameter mapping:

            ================================== ============================
            QuNex parameter                    HCPpipelines parameter
            ================================== ============================
            ``hcp_gmwm_template``              ``gmwm-template``
            ``hcp_regname``                    ``reg-name``
            ``hcp_transmit_mode``              ``mode``
            ``hcp_group_corrected_myelin``     ``group-corrected-myelin``
            ``hcp_afi_tr_one``                 ``afi-tr-one``
            ``hcp_afi_tr_two``                 ``afi-tr-two``
            ``hcp_afi_angle``                  ``afi-angle``
            ``hcp_myelin_template``            ``myelin-template``
            ``hcp_group_uncorrected_myelin``   ``group-uncorrected-myelin``
            ``hcp_pt_reference_value_file``    ``pt-reference-value-file``
            ``hcp_transmit_res``               ``transmit-res``
            ``hcp_regname``                    ``reg-name``
            ``hcp_lowresmesh``                 ``low-res-mesh``
            ``hcp_grayordinatesres``           ``grayordinates-res``
            ``hcp_matlab_mode``                ``matlab-run-mode``
            ``hcp_manual_receive``             ``manual-receive``
            ================================== ============================

    Examples:
        Example run::

            qunex hcp_transmit_bias_individual_adjustment \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"

    """

    log = SessionLog(sinfo, options, "HCP Transmit Bias Phase 3, Individual Adjustment")

    run = True
    report = "Error"

    try:
        pc.do_options_check(options, sinfo, "hcp_transmit_bias_individual_adjustment")
        do_hcp_options_check(options, "hcp_transmit_bias_individual_adjustment")
        hcp = get_hcp_paths(sinfo, options)

        if "hcp" not in sinfo:
            log.error(f"There is no hcp info for session {sinfo['id']} in batch.txt")
            run = False

        if options["hcp_transmit_mode"] is None:
            log.error("the hcp_transmit_mode parameter is mandatory!")
            run = False

        if options["hcp_gmwm_template"] is None:
            log.error("the hcp_gmwm_template parameter is mandatory!")
            run = False

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
                    log.error("unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n")
                    run = False
            else:
                matlabrunmode = "0"

            comm = (
                '%(script)s \
                --study-folder="%(studyfolder)s" \
                --subject="%(subject)s" \
                --mode="%(mode)s" \
                --gmwm-template="%(gmwm_template)s" \
                --reg-name="%(reg_name)s" \
                --matlab-run-mode="%(matlab_run_mode)s"'
                % {
                    "script": os.path.join(
                        hcp["hcp_base"],
                        "TransmitBias",
                        "Phase3_IndividualAdjustment.sh",
                    ),
                    "studyfolder": sinfo["hcp"],
                    "subject": sinfo["id"] + options["hcp_suffix"],
                    "mode": options["hcp_transmit_mode"],
                    "gmwm_template": options["hcp_gmwm_template"],
                    "reg_name": options["hcp_regname"],
                    "matlab_run_mode": matlabrunmode,
                }
            )
            

            # check and set parameters given the mode
            # AFI
            if options["hcp_transmit_mode"] == "AFI":

                if not options["hcp_afi_tr_two"]:
                    log.error("the hcp_afi_tr_two parameter is not provided!")
                    run = False
                if not options["hcp_afi_angle"]:
                    log.error("the hcp_afi_angle parameter is not provided!")
                    run = False
                if not options["hcp_group_corrected_myelin"]:
                    log.error("the hcp_group_corrected_myelin parameter is not provided!")
                    run = False

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

                if options["hcp_group_corrected_myelin"]:
                    comm += f"                --group-corrected-myelin={options['hcp_group_corrected_myelin']}"
                else:
                    log.error("the hcp_group_corrected_myelin parameter is not provided!")
                    run = False

            # B1Tx
            elif options["hcp_transmit_mode"] == "B1Tx":
                if options["hcp_group_corrected_myelin"]:
                    comm += f"                --group-corrected-myelin={options['hcp_group_corrected_myelin']}"
                else:
                    log.error("the hcp_group_corrected_myelin parameter is not provided!")
                    run = False

        

            # PseudoTransmit
            elif options["hcp_transmit_mode"] == "PseudoTransmit":

                if not options["hcp_myelin_template"]:
                    log.error("the hcp_myelin_template parameter is not provided!")
                    run = False
                if not options["hcp_group_uncorrected_myelin"]:
                    log.error("the hcp_group_uncorrected_myelin parameter is not provided!")
                    run = False
                if not options["hcp_pt_reference_value_file"]:
                    log.error("the hcp_pt_reference_value_file parameter is not provided!")
                    run = False
                else:
                    comm += f"                --pt-reference-value-file={options['hcp_pt_reference_value_file']}"

                # optional PseudoTransmit parameters
                if options["hcp_myelin_template"]:
                    comm += f"                --myelin-template={options['hcp_myelin_template']}"

                if options["hcp_group_uncorrected_myelin"]:
                    comm += f"                --group-uncorrected-myelin={options['hcp_group_uncorrected_myelin']}"

            else:
                log.error("Unknown mode for hcp_transmit_mode, use AFI, B1Tx or PseudoTransmit!")

            # optional general parameters
            if options["hcp_manual_receive"]:
                comm += f"                --manual-receive={options['hcp_manual_receive']}" 
            if options["hcp_transmit_res"]:
                comm += f"                --transmit-res={options['hcp_transmit_res']}"
            if options["hcp_lowresmesh"]:
                comm += f"                --low-res-mesh={options['hcp_lowresmesh']}"
            if options["hcp_grayordinatesres"]:
                comm += f"                --grayordinates-res={options['hcp_grayordinatesres']}"
            

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
                    "Running HCP Transmit Bias Phase 3,Individual Adjustment",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    full_test=None,
                    shell=True,
                )

            # -- just checking
            else:
                passed, report, failed = log.check_run(
                    None,
                    None,
                    "HCP Transmit Bias Phase 3,Individual Adjustment",
                    overwrite=overwrite,
                )
                if passed is None:
                    log.step("HCP Transmit Bias Phase 3,Individual Adjustment can be run")
                    report = "HCP Transmit Bias Phase 3,Individual Adjustment can be run"
                    failed = 0

        else:
            log.step("Session cannot be processed.")
            report = "HCP Transmit Bias Phase 3,Individual Adjustment cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        failed = 1
    except Exception as e:
        log.error(f"{e}")
        log.error(f"Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n")
        failed = 1

    log.close(pipeline="HCP Transmit Bias Phase 3,Individual Adjustment Preprocessing")

    return log.result(report, failed)
