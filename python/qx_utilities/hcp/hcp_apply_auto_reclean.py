#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_apply_auto_reclean.py``

The HCP ApplyAutoReclean pipeline and its executor.
"""

import os
import os.path
import traceback
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import qx_utilities.general.exceptions as ge
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog, ReportLog
from qx_utilities.hcp.hcp_utils import (
    parse_icafix_bolds,
    _build_skipped_report,
    do_hcp_options_check,
)


def hcp_apply_auto_reclean(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_apply_auto_reclean [... processing options]``

    Run the ApplyAutoRecleanPipeline step of HCP Pipeline
    (ApplyAutoRecleanPipeline.sh).

    ..  qx_command:
        type: processing.session

    Warning:
        The code expects the input images to be named and present in the QuNex
        folder structure. The function will look into folder::

            <session id>/hcp/<session id>

        for files::

            MNINonLinear/Results/<boldname>/<boldname>.nii.gz

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_icafix_bolds (str, default ''):
            Specify a list of bolds for ICAFix. You should specify how to
            group/concatenate bolds together along with bolds, e.g.
            "<group1>:<boldname1>,<boldname2>|
            <group2>:<boldname3>,<boldname4>", in this case multi-run HCP
            ICAFix will be executed, which is the default. Instead of full bold
            names, you can also  use bold tags from the batch file. If this
            parameter is not provided ICAFix will bundle all bolds together and
            execute multi-run HCP ICAFix, the concatenated file will be named
            fMRI_CONCAT_ALL. Alternatively, you can specify a comma separated
            list of bolds without groups, e.g. "<boldname1>,<boldname2>", in
            this case single-run HCP ICAFix will be executed over specified
            bolds. This is a legacy option and not recommended.

        --hcp_icafix_highpass (int, default 0):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix.

        --hcp_bold_res (str, default '2'):
            Resolution of data.

        --hcp_lowresmesh (str, default '32'):
            Mesh resolution.

        --hcp_grayordinatesres (str, default '2'):
            The size of voxels for the subcortical and cerebellar data in
            grayordinate space in mm.

        --hcp_bold_smoothFWHM (str, default '2'):
            Smoothing FWHM that matches what was used in the fMRISurface
            pipeline.

        --hcp_autoreclean_model_folder (str, default '<$HCPPIPEDIR/ICAFIX/rclean_models>'):
            The folder path of the trained models. Will use the HCP's model
            folder by default.

        --hcp_autoreclean_model_to_use (str, default 'MLP,RandomForest'):
            A comma separeted list of models to use. HCP available models are:
            MLP, RandomForest, Xgboost and XgboostEnsemble. Will use MLP and
            RandomForest by default.

        --hcp_autoreclean_vote_threshold (int):
            A decision threshold for determing reclassifications,
            should be less than to equal to the number of models to use.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

    Output files:
        The results of this step will be generated and populated in the
        MNINonLinear folder inside the same sessions's root hcp folder.

    Notes:
        hcp_apply_auto_reclean parameter mapping:

            ================================== =======================
            QuNex parameter                    HCPpipelines parameter
            ================================== =======================
            ``hcp_icafix_bolds``               ``fmri-names``
            ``hcp_icafix_bolds``               ``mrfix-concat-name``
            ``hcp_icafix_highpass``            ``bandpass``
            ``hcp_bold_res``                   ``fmri-resolution``
            ``hcp_lowresmesh``                 ``low-res-mesh``
            ``hcp_grayordinatesres``           ``grayordinatesres``
            ``hcp_bold_smoothFWHM``            ``smoothingFWHM``
            ``hcp_autoreclean_model_folder``   ``model-folder``
            ``hcp_autoreclean_model_to_use``   ``model-to-use``
            ``hcp_autoreclean_vote_threshold`` ``vote-threshold``
            ``hcp_matlab_mode``                ``matlabrunmode``
            ================================== =======================

    Examples:
        ::

            qunex hcp_apply_auto_reclean \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions

        ::

            qunex hcp_apply_auto_reclean \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --hcp_icafix_bolds="GROUP_1:BOLD_1,BOLD_2|GROUP_2:BOLD_3,BOLD_4" \\
                --hcp_matlab_mode="interpreted"
    """

    log = SessionLog(sinfo, options, "HCP ApplyAutoRecleanPipeline pipeline")

    run = True
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # --- Base settings
        pc.do_options_check(options, sinfo, "hcp_apply_auto_reclean")
        do_hcp_options_check(options, "hcp_apply_auto_reclean")
        hcp = get_hcp_paths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report["boldskipped"] = log.use_or_skip_bold(sinfo, options)
        _build_skipped_report(report, bskip, options)

        # --- Parse icafix_bolds
        single_fix, icafix_bolds, icafix_groups, pars_ok = parse_icafix_bolds(options, bolds, log)

        # --- Multi threading
        if single_fix:
            parelements = max(1, min(options["parelements"], len(icafix_bolds)))
            reclean_elements = icafix_bolds
        else:
            parelements = max(1, min(options["parelements"], len(icafix_groups)))
            reclean_elements = icafix_groups

        log.raw("\n\n%s %d ApplyAutoReclean elements in parallel" % (
            pc.action("Processing", options["run"]),
            parelements,
        ))

        # matlab run mode, compiled=0, interpreted=1, octave=2
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                log.raw("\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n")
                pars_ok = False
        else:
            if options["hcp_matlab_mode"] == "compiled":
                os.environ["FSL_FIX_MATLAB_MODE"] = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                os.environ["FSL_FIX_MATLAB_MODE"] = "1"
            elif options["hcp_matlab_mode"] == "octave":
                os.environ["FSL_FIX_MATLAB_MODE"] = "2"
            else:
                log.raw("\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n")
                pars_ok = False

        if not pars_ok:
            raise ge.CommandFailed(
                "hcp_apply_auto_reclean", "... invalid input parameters!"
            )

        # --- Execute
        # create a multiprocessing Pool
        ppe = ProcessPoolExecutor(parelements)
        # process
        f = partial(
            execute_hcp_apply_auto_reclean,
            sinfo,
            options,
            overwrite,
            hcp,
            run,
            single_fix,
        )
        results = ppe.map(f, reclean_elements)

        # merge r and report
        for result in results:
            log.raw(result["r"])
            temp_report = result["report"]
            report["done"] += temp_report["done"]
            report["failed"] += temp_report["failed"]
            report["incomplete"] += temp_report["incomplete"]
            report["ready"] += temp_report["ready"]
            report["not ready"] += temp_report["not ready"]
            report["skipped"] += temp_report["skipped"]

        # report
        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP ApplyAytoReclean: " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except ge.CommandFailed as e:
        log.command_failed(e)
        report = (sinfo["id"], "HCP ApplyAytoReclean failed", 1)
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        report = (sinfo["id"], "HCP ApplyAytoReclean failed", 1)
    except Exception:
        log.unknown_error()
        report = (sinfo["id"], "HCP ApplyAytoReclean failed", 1)

    log.close(pipeline="HCP ApplyAytoReclean")

    return log.result(report)


def execute_hcp_apply_auto_reclean(sinfo, options, overwrite, hcp, run, single_fix, re):
    """Execute HCP Apply Auto Reclean"""
    if single_fix:
        groupname = None
        bolds = [re]
    else:
        # get group data
        groupname = re["name"]
        bolds = re["bolds"]

    # prepare return variables
    log = ReportLog()
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        log.raw("\n\n------------------------------------------------------------")
        log.raw("\n---> %s group %s" % (pc.action("Processing", options["run"]), groupname))
        groupok = True

        # --- check for bold images and prepare images parameter
        boldimgs = ""

        # check if files for all bolds exist
        for boldinfo in bolds:
            # set ok to true for now
            boldok = True

            _, boldtarget, _ = pc.get_bold_names(boldinfo, options)
            boldimg = os.path.join(
                hcp["hcp_nonlin"], "Results", boldtarget, "%s" % (boldtarget)
            )
            boldok = log.check_for_file("%s.nii.gz" % boldimg,
                "\n     ... bold image %s present" % boldtarget,
                "\n     ... ERROR: bold image [%s.nii.gz] missing!" % boldimg,
                status=boldok,
            )

            if not boldok:
                run = False
                break
            else:
                # add @ separator
                if boldimgs != "":
                    boldimgs = boldimgs + "@"

                boldimgs = boldimgs + boldtarget

        # subject/session
        subject = sinfo["id"] + options["hcp_suffix"]

        # highpass
        if single_fix:
            highpass = (
                2000
                if options["hcp_icafix_highpass"] is None
                else options["hcp_icafix_highpass"]
            )
        else:
            highpass = (
                0
                if options["hcp_icafix_highpass"] is None
                else options["hcp_icafix_highpass"]
            )

        # matlab run mode, compiled=0, interpreted=1, octave=2
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                log.raw("\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n")
                run = False
        else:
            if options["hcp_matlab_mode"] == "compiled":
                os.environ["FSL_FIX_MATLAB_MODE"] = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                os.environ["FSL_FIX_MATLAB_MODE"] = "1"
            elif options["hcp_matlab_mode"] == "octave":
                os.environ["FSL_FIX_MATLAB_MODE"] = "2"
            else:
                log.raw("\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n")
                run = False

        matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]

        comm = (
            '%(script)s \
            --study-folder="%(studyfolder)s" \
            --subject="%(subject)s" \
            --fmri-names="%(boldimgs)s" \
            --fix-high-pass="%(highpass)s" \
            --fmrires="%(fmrires)s" \
            --low-res="%(low_res)s" \
            --grayordinatesres="%(grayordinatesres)s" \
            --smoothingFWHM="%(smoothingFWHM)s" \
            --matlab-run-mode="%(matlabrunmode)s"'
            % {
                "script": os.path.join(
                    hcp["hcp_base"], "ICAFIX", "ApplyAutoRecleanPipeline.sh"
                ),
                "studyfolder": sinfo["hcp"],
                "subject": subject,
                "boldimgs": boldimgs,
                "highpass": highpass,
                "fmrires": options["hcp_bold_res"],
                "low_res": options["hcp_lowresmesh"],
                "grayordinatesres": options["hcp_grayordinatesres"],
                "smoothingFWHM": options["hcp_bold_smoothFWHM"],
                "matlabrunmode": matlabrunmode,
            }
        )

        # optional parameters
        if groupname is not None:
            comm += '             --mrfix-concat-name="%s"' % groupname

        if options["hcp_autoreclean_model_folder"] is not None:
            comm += (
                '             --model-folder="%s"'
                % options["hcp_autoreclean_model_folder"]
            )

        if options["hcp_autoreclean_model_to_use"] is not None:
            comm += '             --model-to-use="%s"' % options[
                "hcp_autoreclean_model_to_use"
            ].replace(",", "@")

        if options["hcp_autoreclean_vote_threshold"] is not None:
            comm += (
                '             --vote-threshold="%s"'
                % options["hcp_autoreclean_vote_threshold"]
            )

        # -- Report command
        if boldok:
            log.pipeline_command(comm)

        # -- Run
        if run and groupok:
            if options["run"] == "run":
                endlog, _, failed = log.run_external(
                    None,
                    comm,
                    "Running ApplyAutoRecleanPipeline",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], groupname],
                    full_test=None,
                    shell=True,
                )

                if failed:
                    report["failed"].append(groupname)
                else:
                    report["done"].append(groupname)

        else:
            report["not ready"].append(groupname)
            if options["run"] == "run":
                log.error("something missing, skipping this group!")
            else:
                log.error("something missing, this group would be skipped!")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw("\n\n\n --- Failed during processing of group %s with error:\n" % (
            groupname
        ))
        log.raw(str(errormessage))
        report["failed"].append(groupname)
    except Exception:
        log.raw("\n --- Failed during processing of group %s with error:\n %s\n" % (
            groupname,
            traceback.format_exc(),
        ))
        report["failed"].append(groupname)

    return {"r": log.text, "report": report}
