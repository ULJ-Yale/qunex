#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_transmit_bias_group_average_fit.py``

The HCP transmit bias pipeline, phase 2: group average fit.
"""

import os
import os.path
import traceback

import qx_utilities.processing.core as pc

from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import do_hcp_options_check, handle_hcp_links


def hcp_transmit_bias_group_average_fit(sessions, options, overwrite=True, thread=0):
    """
    ``hcp_transmit_bias_group_average_fit [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Runs the HCP Transmit Bias Pipeline Phase 2, Group Average Fit.

    ..  qx_command:
        type: processing.study

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
            requires the following parameters: afi-tr-one, afi-tr-two,
            afi-angle, transmit-group-name.

            b) B1Tx: b1 transmit sequence magnitude/phase pair, requires the
            following parameters: transmit-group-name.

            c) PseudoTransmit: use spin echo fieldmaps, SBRef, and a
            template transmit-corrected myelin map to derive empirical
            correction, requires the following parameters: reference-value-out.

        --hcp_transmit_group_name (str, default ''):
            Name for the subgroup of subjects that have good AFI or B1Tx data (e.g. Partial)

        --hcp_outgroupname (str, default ''):
            The name of the group folder, in `<sessionsfolder>/transmit_bias`,
            that the group results are written to.

        --hcp_gmwm_template (str, default ''):
            Output file for GM+WM volume ROI. A relative path is taken to be in
            the `<sessionsfolder>/transmit_bias/<hcp_outgroupname>` folder.

        --hcp_group_uncorrected_myelin (str, default ''):
            Output cifti file for group average of uncorrected myelin. A
            relative path is taken to be in the
            `<sessionsfolder>/transmit_bias/<hcp_outgroupname>` folder.

        --hcp_all_uncorrected_myelin (str, default ''):
            Output cifti file for concatenated uncorrected myelin

        --hcp_manual_receive (str, default 'false'):
            Whether Phase1 used unprocessed scans to correct for not using PSN when acquiring scans, default false

        --hcp_afi_tr_one (str, default ''):
            TR of first AFI frame.

        --hcp_afi_tr_two (str, default ''):
            TR of second AFI frame.

        --hcp_afi_angle (str, default ''):
            Target flip angle of AFI sequence.

        --hcp_pt_reference_value_file (str, default ''):
            output text file for PseudoTransmit reference value. A relative
            path is taken to be in the
            `<sessionsfolder>/transmit_bias/<hcp_outgroupname>` folder.

        --hcp_lowresmesh (int, default 32):
            Mesh resolution.

        --hcp_grayordinatesres (int, default 2):
            The size of voxels for the subcortical and cerebellar data in
            grayordinate space in mm.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

    Notes:
        The HCP Pipelines ``study-folder`` is ``<sessionsfolder>/transmit_bias``,
        into which QuNex links the HCP folder of every session; the group
        results are written to its ``<hcp_outgroupname>`` folder.

        hcp_transmit_bias_group_average_fit parameter mapping:

            ================================== ============================
            QuNex parameter                    HCPpipelines parameter
            ================================== ============================
            ``hcp_regname``                    ``reg-name``
            ``hcp_transmit_mode``              ``mode``
            ``hcp_outgroupname``               ``group-average-name``
            ``hcp_gmwm_template``              ``gmwm-template-out``
            ``hcp_group_uncorrected_myelin``   ``average-myelin-out``
            ``hcp_all_uncorrected_myelin``     ``all-myelin-out``
            ``hcp_manual_receive``             ``manual-receive``
            ``hcp_transmit_group_name``        ``transmit-group-name``
            ``hcp_afi_tr_one``                 ``afi-tr-one``
            ``hcp_afi_tr_two``                 ``afi-tr-two``
            ``hcp_afi_angle``                  ``afi-angle``
            ``hcp_pt_reference_value_file``    ``reference-value-out``
            ``hcp_lowresmesh``                 ``low-res-mesh``
            ``hcp_grayordinatesres``           ``grayordinates-res``
            ``hcp_matlab_mode``                ``matlab-run-mode``
            ================================== ============================

    Examples:
        Example run::

            qunex hcp_transmit_bias_group_average_fit \\
                --studyfolder="<path_to_study_folder>" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"

    """

    sessionids = sessions.get_list_by_key("id", sep=",")
    log = SessionLog({"id": sessionids}, options, "HCP Transmit Bias Pipeline Phase 2, Group Average Fit", label="Session ids")

    run = True
    report = "Error"
    # the HCP study folder of the group run, into which the HCP folder of
    # every session is linked
    study_dir = os.path.join(options["sessionsfolder"], "transmit_bias")
    # only set once the multi-session path creates the links
    linked = False

    try:
        do_hcp_options_check(options, "hcp_transmit_bias_group_average_fit")
        subject_list = ""
        
        for session in sessions:
            # resolves and validates the session HCP paths
            get_hcp_paths(session, options)
            if "hcp" not in session:
                log.error(f"There is no hcp info for session {session['id']} in batch.txt")
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
            log.error("hcp_transmit_bias_group_average_fit needs to be ran across several sessions!")
            run = False

        # multi session, flagged before linking so that partial links are
        # removed as well
        elif options["run"] == "run":
            linked = True
            if not handle_hcp_links(study_dir, sessions, options, False, _log=log):
                run = False
        else:
            log.step(f"test, not linked: the HCP folder of each session into {study_dir}")

        if options["hcp_transmit_mode"] is None:
            log.error("the hcp_transmit_mode parameter is mandatory!")
            run = False

        gmwm_template = ""
        if options["hcp_gmwm_template"] is None:
            log.error("the hcp_gmwm_template parameter is mandatory!")
            run = False
        elif not os.path.isabs(options["hcp_gmwm_template"]) and options["hcp_gmwm_template"][0] != "~":
            log.warning("hcp_gmwm_template parameter is local")
            gmwm_template = os.path.join(study_dir, outgroupname, options["hcp_gmwm_template"])
            log.step(f"   hcp_gmwm_template parameter set to {gmwm_template}")
        else:
            gmwm_template = options["hcp_gmwm_template"]

        group_uncorrected_myelin = ""
        if options["hcp_group_uncorrected_myelin"] is None:
            log.error("the hcp_group_uncorrected_myelin parameter is mandatory!")
            run = False
        elif not os.path.isabs(options["hcp_group_uncorrected_myelin"]) and options["hcp_group_uncorrected_myelin"][0] != "~":
            log.warning("hcp_group_uncorrected_myelin parameter is local")
            group_uncorrected_myelin = os.path.join(study_dir, outgroupname, options["hcp_group_uncorrected_myelin"])
            log.step(f"   hcp_group_uncorrected_myelin parameter set to {group_uncorrected_myelin}")
        else:
            group_uncorrected_myelin = options["hcp_group_uncorrected_myelin"]

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
                --subject-list="%(subjectlist)s" \
                --mode="%(mode)s" \
                --reg-name="%(reg_name)s" \
                --group-average-name="%(group_average_name)s" \
                --gmwm-template-out="%(gmwm_template)s" \
                --average-myelin-out="%(average_myelin)s" \
                --matlab-run-mode="%(matlab_run_mode)s"'
                % {
                    "script": os.path.join(
                        os.environ["HCPPIPEDIR"], "TransmitBias", "Phase2_GroupAverageFit.sh"
                    ),
                    "studyfolder": study_dir,
                    "subjectlist": subject_list,
                    "mode": options["hcp_transmit_mode"],
                    "reg_name": options["hcp_regname"],
                    "group_average_name": outgroupname,
                    "gmwm_template": gmwm_template,
                    "average_myelin": group_uncorrected_myelin,
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
                if options["hcp_pt_reference_value_file"] is None:
                    log.error("the hcp_pt_reference_value_file parameter is mandatory!")
                    run = False
                elif not os.path.isabs(options["hcp_pt_reference_value_file"]) and options["hcp_pt_reference_value_file"][0] != '~':
                    log.warning("hcp_pt_reference_value_file parameter is local")
                    comm += f"                --reference-value-out={os.path.join(study_dir, outgroupname, options['hcp_pt_reference_value_file'])}"
                    log.step(f"   hcp_pt_reference_value_file parameter set to {os.path.join(study_dir, outgroupname, options['hcp_pt_reference_value_file'])}")
                else:
                    comm += f"                --reference-value-out={options['hcp_pt_reference_value_file']}"

            # B1Tx needs only the transmit group name, checked above
            elif options["hcp_transmit_mode"] != "B1Tx":
                log.error("Unknown mode for hcp_transmit_mode, use AFI, B1Tx or PseudoTransmit!")
                run = False

            # optional general parameters
            if options["hcp_manual_receive"]:
                comm += f"                --manual-receive={options['hcp_manual_receive']}"

            if options["hcp_all_uncorrected_myelin"]:
                comm += f"                --all-myelin-out={options['hcp_all_uncorrected_myelin']}"

            if options["hcp_lowresmesh"]:
                comm += f"                --low-res-mesh={options['hcp_lowresmesh']}"

            if options["hcp_grayordinatesres"]:
                comm += f"                --grayordinates-res={options['hcp_grayordinatesres']}"

    
            # -- Report command
            if run:
                log.rule(before=1, after=1)
                log.raw("Running HCP Pipelines command via QuNex:\n\n")
                log.raw(comm.replace("                --", "\n    --"))
                log.rule(after=1)

        # -- Run
        if run:
            if options["run"] == "run":
                endlog, report, failed = pc.run_external_for_file(
                    None,
                    comm,
                    "Running HCP Transmit Bias Phase 2, Group Average Fit",
                    overwrite=overwrite,
                    thread=options["hcp_outgroupname"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    full_test=None,
                    shell=True,
                    _log=log,
                )

                # #Remove soft links
                # handle_hcp_links(study_dir, sessions, options, True)

            # -- just checking: there is no file to check the run against, so
            #    a group whose inputs are all present can be run
            else:
                log.step("HCP Transmit Bias Phase 2, Group Average Fit can be run")
                report = "HCP Transmit Bias Phase 2, Group Average Fit can be run"
                failed = 0

        else:
            log.step("Session cannot be processed.")
            report = "HCP Transmit Bias Phase 2, Group Average Fit cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        failed = 1
    except Exception as e:
        log.error(f"{e}")
        log.error(f"Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n")
        failed = 1

    # remove soft links to prevent clutter, but only if they were created
    if linked:
        handle_hcp_links(study_dir, sessions, options, True)

    log.close(pipeline="HCP Transmit Bias Phase 2, Group Average Fit Preprocessing")

    return log.result((sessionids, report, failed))
