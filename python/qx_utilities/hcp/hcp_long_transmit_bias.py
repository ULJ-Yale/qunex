#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_long_transmit_bias.py``

The longitudinal HCP transmit bias field correction pipeline.
"""

import os
import os.path
import shutil
from datetime import datetime

import qx_utilities.general.exceptions as ge
import qx_utilities.processing.core as pc
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    _append_sorted_logdir_to_log,
    _check_hcp_info,
    do_hcp_options_check,
)


def hcp_long_transmit_bias(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_long_transmit_bias [... processing options]``

    Run the HCP Longitudinal Transmit Bias Pipeline.

    ..  qx_command:
        type: processing.subject

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsubjects (int, default 1):
            How many subjects to run in parallel.

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

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --hcp_parallel_mode (str, default "BUILTIN"):
            Parallelization execution mode, one of FSLSUB, BUILTIN, NONE.

        --hcp_filename (str, default 'automated'):
            How to name the BOLD files once mapped into the hcp input folder
            structure. The default ('automated') will automatically name each
            file by their number (e.g. BOLD_1). The alternative ('userdefined')
            is to use the file names, which can be defined by the user prior to
            mapping (e.g. rfMRI_REST1_AP).

        --hcp_gmwm_template (str, default ''):
            Location of the GMWMtemplate, the file containing GM+WM volume ROI.

        --hcp_regname (str, default 'MSMSulc'):
            Input registration name.

        --hcp_transmit_mode (str, default ''):
            What type of transmit bias correction to apply, options and required
            inputs are:

            a) AFI: actual flip angle sequence with two different echo times,
            requires the following parameters: afi-image, afi-tr-one,afi-tr-two,
            afi-angle, group-corrected-myelin.

            b) B1Tx: b1 transmit sequence magnitude/phase pair, requires the
            following parameters: b1tx-magnitude, b1tx-phase, group-corrected-myelin.

            c) PseudoTransmit: use spin echo fieldmaps, SBRef, and a
            template transmit-corrected myelin map to derive empirical
            correction, requires the following parameters: pt-fmri-names,
            myelin-template, group-uncorrected-myelin, reference-value.

        --hcp_group_corrected_myelin (str, default ''):
            The group-corrected myelin file from AFI or B1Tx.

        --hcp_afi_tr_one (str, default ''):
            TR of first AFI frame.

        --hcp_afi_tr_two (str, default ''):
            TR of second AFI frame.

        --hcp_afi_angle (str, default ''):
            Target flip angle of AFI sequence.

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

        --hcp_myelin_mapping_fwhm (str, default '5'):
            The fwhm value to use in -myelin-style [5]

        --hcp_old_myelin_mapping (flag, not set by default):
            If myelin mapping was done using version 1.2.3 or earlier of
            wb_command, set this flag.

        --hcp_regname (str, default 'MSMSulc'):
            The name of the registration used.

        --hcp_lowresmesh (str, default '32'):
            Mesh resolution.

        --hcp_grayordinatesres (str, default '2'):
            The size of voxels for the subcortical and cerebellar data in
            grayordinate space in mm.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

    Notes:
        hcp_transmit_bias_individual parameter mapping:

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
            ``hcp_b1tx_phase_divisor``         ``b1tx-phase-divisor``
            ``hcp_pt_fmri_names``              ``pt-fmri-names``
            ``hcp_pt_bbr_threshold``           ``pt-bbr-threshold``
            ``hcp_myelin_template``            ``myelin-template``
            ``hcp_group_uncorrected_myelin``   ``group-uncorrected-myelin``
            ``hcp_pt_reference_value_file``    ``pt-reference-value-file``
            ``hcp_transmit_res``               ``transmit-res``
            ``hcp_myelin_mapping_fwhm``        ``myelin-mapping-fwhm``
            ``hcp_old_myelin_mapping``         ``old-myelin-mapping``
            ``hcp_regname``                    ``reg-name``
            ``hcp_lowresmesh``                 ``low-res-mesh``
            ``hcp_grayordinatesres``           ``grayordinates-res``
            ``hcp_matlab_mode``                ``matlab-run-mode``
            ``hcp_longitudinal_template``      ``longitudinal-template``
            ================================== ============================

    Examples:
        Example run::

            qunex hcp_long_transmit_bias \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"

    """

    subject_id = sinfo[0]["subject"]

    log = SessionLog({"id": subject_id}, options, "HCP Longitudnal FS Pipeline", label="Subject")

    run = True
    report = ""
    failed = 0

    try:
        # checks
        pc.do_options_check(options, sinfo[0], "hcp_long_transmit_bias")
        do_hcp_options_check(options, "hcp_long_transmit_bias")
        hcp = _check_hcp_info(sinfo, options)

        # sort out the folder structure
        sessionsfolder = options["sessionsfolder"]
        subjectsfolder = sessionsfolder.replace("sessions", "subjects")
        if not os.path.exists(subjectsfolder):
            os.makedirs(subjectsfolder)
        study_folder = os.path.join(subjectsfolder, subject_id)
        if not os.path.exists(study_folder):
            os.makedirs(study_folder)

        # logdir
        logdir = os.path.join(
            options["logfolder"],
            "comlogs",
            f"extra_logs_hcp_long_transmit_bias_{subject_id}",
        )
        if os.path.exists(logdir):
            shutil.rmtree(logdir)
        os.makedirs(logdir)

        if options["hcp_transmit_mode"] is None:
            log.error("the hcp_transmit_mode parameter is mandatory!")
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
                    log.raw("\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n")
                    run = False
            else:
                matlabrunmode = "0"

            comm = (
                '%(script)s \
                --study-folder="%(studyfolder)s" \
                --subject="%(subject)s" \
                --sessions="%(sessions)s" \
                --longitudinal-template="%(longitudinal_template)s" \
                --mode="%(mode)s" \
                --gmwm-template="%(gmwm_template)s" \
                --reg-name="%(reg_name)s" \
                --parallel-mode="%(parallel_mode)s" \
                --logdir="%(logdir)s" \
                --matlab-run-mode="%(matlab_run_mode)s"'
                % {
                    "script": os.path.join(
                        hcp["hcp_base"],
                        "TransmitBias",
                        "TransmitBiasLong.sh",
                    ),
                    "studyfolder": study_folder,
                    "subject": subject_id,
                    "sessions": sinfo.get_list_by_key("id", sep="@"),
                    "longitudinal_template": options["hcp_longitudinal_template"],
                    "mode": options["hcp_transmit_mode"],
                    "gmwm_template": options["hcp_gmwm_template"],
                    "reg_name": options["hcp_regname"],
                    "parallel_mode": options["hcp_parallel_mode"],
                    "logdir": logdir,
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
                    # WARNING: sinfo[0] used here –- it assumes all the sessions have the same BOLDS as the first one
                    bolds, _, _ = log.use_or_skip_bold(sinfo[0], options)
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
                if options["hcp_pt_bbr_threshold"]:
                    comm += f"                --pt-bbr-threshold={options['hcp_pt_bbr_threshold']}"

                if options["hcp_myelin_template"]:
                    comm += f"                --myelin-template={options['hcp_myelin_template']}"

                if options["hcp_group_uncorrected_myelin"]:
                    comm += f"                --group-uncorrected-myelin={options['hcp_group_uncorrected_myelin']}"

            else:
                log.error("Unknown mode for hcp_transmit_mode, use AFI, B1Tx or PseudoTransmit!")

            # optional general parameters
            if options["hcp_transmit_res"]:
                comm += f"                --transmit-res={options['hcp_transmit_res']}"

            if options["hcp_myelin_mapping_fwhm"]:
                comm += f"                --myelin-mapping-fwhm={options['hcp_myelin_mapping_fwhm']}"

            if options["hcp_old_myelin_mapping"]:
                comm += "                --old-myelin-mapping=TRUE"

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

            # -- Test file
            if options["run"] == "run":
                endlog, _, failed = log.run_external(
                    None,
                    comm,
                    "Running HCP Longitudinal Transmit Bias",
                    overwrite=overwrite,
                    thread=subject_id,
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    full_test=None,
                    shell=True,
                )

                if failed == 0:
                    report = "processing completed"
                else:
                    report = "processing failed"

                # read and print all files in logdir
                with open(endlog, "a", encoding="utf-8") as log_file:
                    _append_sorted_logdir_to_log(log_file, logdir)
                    # print succesful completion
                    print(
                        f"\n---> Successful completion of task at {datetime.now()}",
                        file=log_file,
                    )

                # remove the directory and its contents
                shutil.rmtree(logdir)

            # -- just checking
            else:
                passed, _, _ = log.check_run(
                    None, None, "HCP Longitudinal Transmit Bias", overwrite=overwrite
                )
                if passed is None:
                    log.step("HCP Longitudinal Transmit Bias can be run")
                    report = "ready"
                else:
                    log.step("HCP Longitudinal Transmit Bias cannot be run")
                    report = "not ready"

        else:
            log.step("Subject cannot be processed.")
            report = "not ready"

    except ge.CommandFailed as e:
        log.raw("\n" + ge.report_command_failed("hcp_long_transmit_bias", e))
        report = "processing failed"
        failed += 1
    except ge.CommandError as e:
        log.raw("\n" + ge.report_command_error("hcp_long_transmit_bias", e))
        report = "processing failed"
        failed += 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        report = "Error"
        failed = 1
    except Exception:
        log.unknown_error()
        report = "Error"
        failed = 1

    log.close(pipeline="HCP Longitudinal Transmit Bias Preprocessing")

    return log.result((subject_id, report, failed))
