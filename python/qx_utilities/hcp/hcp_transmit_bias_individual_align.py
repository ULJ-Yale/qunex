#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_transmit_bias_individual_align.py``

The HCP transmit bias pipeline, phase 1: individual align.
"""

import os
import os.path
import traceback

import qx_utilities.processing.core as pc

from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import do_hcp_options_check


def hcp_transmit_bias_individual_align(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_transmit_bias_individual_align [... processing options]``

    Runs the HCP Transmit Bias Pipeline Phase 1, Individual Align.

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

        --hcp_regname (str, default 'MSMSulc'):
            Input registration name.

        --hcp_transmit_mode (str, default ''):
            What type of transmit bias correction to apply, options and required
            inputs are:

            a) AFI: actual flip angle sequence with two different echo times,
            requires the following parameters: afi-image, afi-tr-one,afi-tr-two, 
            and group-corrected-myelin.

            b) B1Tx: b1 transmit sequence magnitude/phase pair, requires the
            following parameters: b1tx-magnitude, b1tx-phase, group-corrected-myelin.

            c) PseudoTransmit: use spin echo fieldmaps, SBRef, and a
            template transmit-corrected myelin map to derive empirical
            correction, requires the following parameters: pt-fmri-names,
            myelin-template, group-uncorrected-myelin, reference-value.

        --hcp_group_corrected_myelin (str, default ''):
            The group-corrected myelin file from AFI or B1Tx.

        --hcp_afi_image (str, default ''):
            Two-frame AFI image.

        --hcp_afi_tr_one (str, default ''):
            TR of first AFI frame.

        --hcp_afi_tr_two (str, default ''):
            TR of second AFI frame.

        --hcp_b1tx_magnitude (str, default ''):
            B1Tx magnitude image (for alignment).

        --hcp_b1tx_phase (str, default ''):
            B1Tx phase image.

        --hcp_b1tx_phase_divisor (str, default '800'):
            What to divide the phase map by to obtain proportion of intended

        --hcp_pt_fmri_names (str, default <list of all BOLDs>):
            A comma separated list of fMRI runs to use SE/SBRef files from. Set
            to a list of all BOLDs by default.

        --hcp_pt_bbr_threshold (str, default '0.5'):
            Mincost threshold for reinitializing fMRI bbregister with flirt
            (may need to be increased for aging-related reduction of gray/white
            contrast).

        --hcp_unproc_t1w_list (str, default ''):
            A comma separated list of unprocessed T1w images, for correcting
            non-PSN data. You can set this to "auto" and QuNex will try to fill
            it automatically.

        --hcp_unproc_t2w_list (str, default ''):
            A comma separated list of unprocessed T2w images, for correcting
            non-PSN data. You can set this to "auto" and QuNex will try to fill
            it automatically.

        --hcp_receive_bias_body_coil (str, default ''):
            Image acquired with body coil receive, to be used with
            --hcp_receive_head_body_coil.

        --hcp_receive_bias_head_coil (str, default ''):
            Matched image acquired with head coil receive.

        --hcp_raw_psn_t1w (str, default ''):
            The bias-corrected version of the T1w image acquired with pre-scan
            normalize, which was used to generate the original myelin maps.
            You can set this to "auto" and QuNex will try to fill it
            automatically.

        --hcp_raw_nopsn_t1w (str, default ''):
            The uncorrected version of the --raw-psn-t1w image. You can set this
            to "auto" and QuNex will try to fill it automatically.

        --hcp_transmit_res (str, default ''):
            Resolution to use for transmit field, default equal to
            hcp_grayordinatesres.

        --hcp_myelin_mapping_fwhm (str, default '5'):
            The fwhm value to use in -myelin-style [5]

        --hcp_old_myelin_mapping (flag, not set by default):
            If myelin mapping was done using version 1.2.3 or earlier of
            wb_command, set this flag.

        --hcp_gdcoeffs (str, default ''):
            Path to a file containing gradient distortion coefficients.

        --hcp_regname (str, default 'MSMSulc'):
            The name of the registration used.

        --hcp_lowresmesh (int, default 32):
            Mesh resolution.

        --hcp_grayordinatesres (int, default 2):
            The size of voxels for the subcortical and cerebellar data in
            grayordinate space in mm.

    Notes:
        hcp_transmit_bias_individual parameter mapping:

            ================================== ============================
            QuNex parameter                    HCPpipelines parameter
            ================================== ============================
            ``hcp_regname``                    ``reg-name``
            ``hcp_transmit_mode``              ``mode``
            ``hcp_afi_image``                  ``afi-image``
            ``hcp_afi_tr_one``                 ``afi-tr-one``
            ``hcp_afi_tr_two``                 ``afi-tr-two``
            ``hcp_b1tx_magnitude``             ``b1tx-magnitude``
            ``hcp_b1tx_phase``                 ``b1tx-phase``
            ``hcp_b1tx_phase_divisor``         ``b1tx-phase-divisor``
            ``hcp_pt_fmri_names``              ``pt-fmri-names``
            ``hcp_pt_bbr_threshold``           ``pt-bbr-threshold``
            ``hcp_unproc_t1w_list``            ``unproc-t1w-list``
            ``hcp_unproc_t2w_list``            ``unproc-t2w-list``
            ``hcp_receive_bias_body_coil``     ``receive-bias-body-coil``
            ``hcp_receive_bias_head_coil``     ``receive-bias-head-coil``
            ``hcp_raw_psn_t1w``                ``raw-psn-t1w``
            ``hcp_raw_nopsn_t1w``              ``raw-nopsn-t1w``
            ``hcp_transmit_res``               ``transmit-res``
            ``hcp_myelin_mapping_fwhm``        ``myelin-mapping-fwhm``
            ``hcp_old_myelin_mapping``         ``old-myelin-mapping``
            ``hcp_gdcoeffs``                   ``scanner-grad-coeffs``
            ``hcp_regname``                    ``reg-name``
            ``hcp_lowresmesh``                 ``low-res-mesh``
            ``hcp_grayordinatesres``           ``grayordinates-res``
            ================================== ============================

    Examples:
        Example run::

            qunex hcp_transmit_bias_individual_align \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"

    """


    log = SessionLog(sinfo, options, "HCP Transmit Bias Pipeline Phase 1, Individual Align")

    run = True
    report = "Error"

    try:
        pc.do_options_check(options, sinfo, "hcp_transmit_bias_individual_align")
        do_hcp_options_check(options, "hcp_transmit_bias_individual_align")
        hcp = get_hcp_paths(sinfo, options)

        if "hcp" not in sinfo:
            log.error("There is no hcp info for session %s in batch.txt" % (
                sinfo["id"]
            ))
            run = False

        if options["hcp_transmit_mode"] is None:
            log.error("the hcp_transmit_mode parameter is mandatory!")
            run = False

        # build the command
        if run:
            comm = (
                '%(script)s \
                --study-folder="%(studyfolder)s" \
                --subject="%(subject)s" \
                --mode="%(mode)s" \
                --reg-name="%(reg_name)s"'
                % {
                    "script": os.path.join(
                        hcp["hcp_base"],
                        "TransmitBias",
                        "Phase1_IndividualAlign.sh",
                    ),
                    "studyfolder": sinfo["hcp"],
                    "subject": sinfo["id"] + options["hcp_suffix"],
                    "mode": options["hcp_transmit_mode"],
                    "reg_name": options["hcp_regname"],
                }
            )

            # check and set parameters given the mode
            # AFI
            if options["hcp_transmit_mode"] == "AFI":
                if options["hcp_afi_image"]:
                    comm += f"                --afi-image={options['hcp_afi_image']}"
                else:
                    log.step("Setting the hcp_afi_image automatically")
                    if "T1w-AFI" in hcp:
                        comm += f"                --afi-image={hcp['T1w-AFI']}"
                    else:
                        log.error("the hcp_afi_image parameter is not provided, and QuNex cannot find the T1w AFI image in the HCP unprocessed/T1w folder!")
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

            # B1Tx
            elif options["hcp_transmit_mode"] == "B1Tx":
                if options["hcp_b1tx_magnitude"]:
                    comm += f"                --b1tx-magnitude={options['hcp_b1tx_magnitude']}"
                else:
                    log.step("Setting the hcp_b1tx_magnitude automatically")
                    if "TB1TFL-Magnitude" in hcp:
                        comm += f"                --b1tx-magnitude={hcp['TB1TFL-Magnitude']}"
                    else:
                        log.error("the hcp_b1tx_magnitude parameter is not provided, and QuNex cannot find the b1tx magnitude image in the HCP unprocessed/B1 folder!")
                        run = False

                if options["hcp_b1tx_phase"]:
                    comm += f"                --b1tx-phase={options['hcp_b1tx_phase']}"
                else:
                    log.step("Setting the hcp_b1tx_phase automatically")
                    if "TB1TFL-Phase" in hcp:
                        comm += f"                --b1tx-phase={hcp['TB1TFL-Phase']}"
                    else:
                        log.error("the hcp_b1tx_phase parameter is not provided, and QuNex cannot find the b1tx phase image in the HCP unprocessed/B1 folder!")
                        run = False

                # optional B1Tx parameters
                if options["hcp_b1tx_phase_divisor"]:
                    comm += f"                --b1tx-phase-divisor={options['hcp_b1tx_phase_divisor']}"

            # PseudoTransmit
            elif options["hcp_transmit_mode"] == "PseudoTransmit":
                if options["hcp_pt_fmri_names"]:
                    pt_fmri_names = options["hcp_pt_fmri_names"].replace(",", "@")

                else:
                    log.step("Setting the hcp_pt_fmri_names automatically")
                    # --- Get sorted bold numbers and bold data
                    bolds, _, _ = log.use_or_skip_bold(sinfo, options)
                    pt_fmri_names = []
                    for boldinfo in bolds:
                        if (
                            "filename" in boldinfo
                            and options["hcp_filename"] == "userdefined"
                        ):
                            pt_fmri_names.append(boldinfo["filename"])
                        else:
                            pt_fmri_names.append(
                                f"{options['hcp_bold_prefix']}{boldinfo['bold_number']}"
                            )

                    if len(pt_fmri_names) == 0:
                        log.error("the hcp_pt_fmri_names parameter is not provided, and QuNex cannot find any BOLDs!")
                        run = False
                    else:
                        pt_fmri_names = "@".join(pt_fmri_names)

                comm += f"                --pt-fmri-names={pt_fmri_names}"

                # optional PseudoTransmit parameters
                if options["hcp_pt_bbr_threshold"]:
                    comm += f"                --pt-bbr-threshold={options['hcp_pt_bbr_threshold']}"

            else:
                log.error("Unknown mode for hcp_transmit_mode, use AFI, B1Tx or PseudoTransmit!")

            # optional general parameters
            if options["hcp_unproc_t1w_list"] is not None:
                if options["hcp_unproc_t1w_list"] == "auto":
                    log.step("Setting the hcp_unproc_t1w_list automatically")
                    comm += f"                --unproc-t1w-list={hcp['T1w']}"
                else:
                    unproc_t1w_list = options["hcp_unproc_t1w_list"].replace(",", "@")
                    comm += f"                --unproc-t1w-list={unproc_t1w_list}"

            if options["hcp_unproc_t2w_list"] is not None:
                if options["hcp_unproc_t2w_list"] == "auto":
                    log.step("Setting the hcp_unproc_t2w_list automatically")
                    comm += f"                --unproc-t2w-list={hcp['T2w']}"
                else:
                    unproc_t2w_list = options["hcp_unproc_t2w_list"].replace(",", "@")
                    comm += f"                --unproc-t2w-list={unproc_t2w_list}"

            if options["hcp_receive_bias_body_coil"]:
                comm += f"                --receive-bias-body-coil={options['hcp_receive_bias_body_coil']}"
            else:
                if "RB1COR-Body" in hcp:
                    log.step("Setting the hcp_receive_bias_body_coil automatically")
                    comm += (
                        f"                --receive-bias-body-coil={hcp['RB1COR-Body']}"
                    )

            if options["hcp_receive_bias_head_coil"]:
                comm += f"                --receive-bias-head-coil={options['hcp_receive_bias_head_coil']}"
            else:
                if "RB1COR-Head" in hcp:
                    log.step("Setting the hcp_receive_bias_head_coil automatically")
                    comm += (
                        f"                --receive-bias-head-coil={hcp['RB1COR-Head']}"
                    )

            if options["hcp_raw_psn_t1w"]:
                if options["hcp_raw_psn_t1w"] == "auto":
                    log.step("Setting the hcp_raw_psn_t1w automatically")
                    comm += f"                --raw-psn-t1w={hcp['hcp_raw_psn_t1w']}"
                else:
                    comm += (
                        f"                --raw-psn-t1w={options['hcp_raw_psn_t1w']}"
                    )

            if options["hcp_raw_nopsn_t1w"]:
                if options["hcp_raw_nopsn_t1w"] == "auto":
                    log.step("Setting the hcp_raw_nopsn_t1w automatically")
                    comm += (
                        f"                --raw-nopsn-t1w={hcp['hcp_raw_nopsn_t1w']}"
                    )
                else:
                    comm += f"                --raw-nopsn-t1w={options['hcp_raw_nopsn_t1w']}"

            if options["hcp_transmit_res"]:
                comm += f"                --transmit-res={options['hcp_transmit_res']}"

            if options["hcp_myelin_mapping_fwhm"]:
                comm += f"                --myelin-mapping-fwhm={options['hcp_myelin_mapping_fwhm']}"

            if options["hcp_old_myelin_mapping"]:
                comm += "                --old-myelin-mapping=TRUE"

            if options["hcp_gdcoeffs"]:
                # lookup gdcoeffs file
                gdcfile, run = log.check_gdc_coeff_file(options["hcp_gdcoeffs"], hcp, sinfo, run)
                if gdcfile != "NONE":
                    comm += f"                --scanner-grad-coeffs={gdcfile}"

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
                    "Running HCP Transmit Bias Phase 1, Individual Align",
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
                    "HCP Transmit Bias Phase 1, Individual Align",
                    overwrite=overwrite,
                )
                if passed is None:
                    log.step("HCP Transmit Bias Phase 1, Individual Align can be run")
                    report = "HCP Transmit Bias Phase 1, Individual Align can be run"
                    failed = 0

        else:
            log.step("Session cannot be processed.")
            report = "HCP Transmit Bias Phase 1, Individual Align cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        failed = 1
    except Exception as e:
        log.raw(f"\nERROR: {e}")
        log.raw(f"\nERROR: Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n")
        failed = 1

    log.close(pipeline="HCP Transmit Bias Phase 1, Individual Align Preprocessing")

    return log.result(report, failed)
