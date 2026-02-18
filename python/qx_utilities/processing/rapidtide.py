#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2025 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``fsl.py``

This file holds code for running FSL commands. It
consists of functions:

--rapidtide      Runs rapidtide (https://rapidtide.readthedocs.io/).

All the functions are part of the processing suite. They should be called
from the command line using `qunex` command. Help is available through:

- ``qunex ?<command>`` for command specific help
There are additional support functions that are not to be used
directly.

Copyright (c) Jure Demsar.
All rights reserved.
"""

import os
import shutil
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from functools import partial

import hcp.process_hcp as hcp
import processing.core as pc


def rapidtide(sinfo, options, overwrite=False, thread=0):
    """
    ``rapidtide [... processing options]``

    This command executes rapidtide, it calculates a similarity function between
    a signal and every voxel of a BOLD fMRI dataset. It then determines the peak
    value, time delay, and width of the similarity function to determine when
    and how strongly that probe signal appears in each voxel.

    See (https://rapidtide.readthedocs.io/en/latest/usage_rapidtide.html) for
    additional details.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

        --sessionsfolder (str):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --bolds (str, default 'rest'):
            Which bold images to process. You can select bolds through their
            number, name or task (e.g. rest), you can chain multiple conditions
            together by providing a comma separated list. By default, rest bolds
            will be used.

        --nifti_tail (str, ''):
            The tail of BOLD NIfTI images to use. For example, if bold is
            rfMRI_REST1_AP and tail is _hp0_clean_rclean_tclean, then the
            HCP processed BOLD image that will be used is
            rfMRI_REST1_AP_hp0_clean_rclean_tclean.nii.gz.

        --despecklepasses (int, 4):
            Detect and refit suspect correlations to disambiguate peak location
            in PASSES passes. Set to 0 to
            disable.

        --filterband (str, 'lfo'):
            Filter data and regressors to specific band. Use None to disable
            filtering. Ranges and options are: vlf: 0.0-0.009Hz,
            lfo: 0.01-0.15Hz, cardiac: 0.66-3.0Hz, hrv_ulf: 0.0-0.0033Hz,
            hrv_vlf: 0.0033-0.04Hz, hrv_lf: 0.04-0.15Hz, hrv_hf: 0.15-0.4Hz,
            hrv_vhf: 0.4-0.5Hz, lfo_legacy: 0.01-0.15Hz, lfo_tight: 0.01-0.1Hz,
            resp.

        --searchrange (str, '-30.0 30.0'):
            Space separated limits for a range of lags.

        --nprocs (int, 1):
            Number of worker processes for multiprocessing. Setting to less than
            1 sets the number of worker processes to number of CPUs.

        --nofitfilt (flag):
            Do not zero out peak fit values if fit fails.

        --similaritymetric (str, 'correlation'):
            Similarity metric for finding delay values. Choices are correlation,
            mutualinfo, and hybrid.

        --ampthresh (str, '-1.0'):
            For refinement, exclude voxels with correlation coefficients less
            than the set value. Note htat ampthresh will automatically be set to
            the p<0.05 significance level determined by the --numnull option if
            --nomnull is set greater than 0 and this is not manually specified.

        --outputlevel (str, 'normal'):
            The level of file output produced. "min" produces only absolutely
            essential files, "less" adds in the sLFO filtered data (rather than
            just filter efficacy metrics), "normal" saves what you would
            typically want around for interactive data exploration, "more" adds
            files that are sometimes useful, and "max" outputs anything you
            might possibly want. Selecting "max" will produce ~3x your input
            datafile size as output.

        --spatialfilt (str, '-1.0'):
            Spatially filter fMRI data prior to analysis using the set value in
            mm. Set negative to have rapidtide set it to half the mean voxel
            dimension (a rule of thumb for a good value). Set to 0 to disable.

        --simcalcrange (str, '-1 -1'):
            2 space separated values that limit correlation calculation to
            data between them in the fmri file. If the end value is set to -1,
            analysis will go to the last time-point. Negative start values wil
            be set to 0. Default is to use all time-points.

        --brainmask (str):
            This specifies the valid brain voxels. No voxels outside of this
            will be used for global mean calculation, correlation, refinement,
            offset calculation, or denoising. Will be set to BOLD's
            brainmask_fs.2.nii.gz from HCP pipelines by default if it file
            exists. Set to "None" to disable brain mask.

        --graymattermask (str):
            This specifies a gray matter mask registered to the input functional
            data. If not set flirt will be used to automatically calculate 2 mm
            aparc+aseg. Set to "None" to disable gray matter mask.

        --whitemattermask (str):
            This specifies a white matter mask registered to the input
            functional data. If not set flirt will be used to automatically
            calculate 2 mm aparc+aseg. Set to "None" to disable white matter
            mask.

        --refineexclude (str):
            Do not use voxels in the provided file for regressor refinement. By
            default BOLD's dropouts from HCP pipelines will be used if they
            exist. Set to "None" to disable refinement exclusion.

        --nodenoise (flag):
            Turn off regression filtering to remove delayed regressor from each
            voxel (disables output of fitNorm). Does not perform denoising, only
            calculates the maps.

        --rapidtide_extra_args (str, ''):
            Additional arguments to pass to rapidtide. This is useful for
            passing any additional arguments that are not yet exposed through
            QuNex command line options. The string will be passed to rapidtide
            as is.

    Examples:
        ::

            qunex rapidtide \\
                --sessionsfolder="/data/qunex_study/sessions" \\
                --batchfile="/data/qunex_study/processing/batch.txt"

            qunex rapidtide \
                --sessionsfolder="/data/jdemsar/studies/hca_alzheimer/sessions" \
                --bolds="rfMRI_REST1_AP,rfMRI_REST1_PA,rfMRI_REST2_AP,rfMRI_REST2_PA" \
                --despecklepasses="4" \
                --filterband="lfo" \
                --searchrange="-7.5 15.0" \
                --nprocs="4" \
                --nofitfilt \
                --similaritymetric="hybrid" \
                --ampthresh="0.15" \
                --outputlevel="normal" \
                --spatialfilt="3" \
                --simcalcrange="100 -1"

        The first command uses rapidtide defaults across all sessions and their
        rest bolds in the batch file. The second one uses a sensible setup for
        HCP style acquisition data.
    """

    # get session id
    session = sinfo["id"]

    r = "\n------------------------------------------------------------"
    timestamp = datetime.now().strftime("%A, %d. %B %Y %H:%M:%S")
    r += f"\nSession id: {sinfo['id']} \n[started on {timestamp}]"
    action = pc.action("Running", options["run"])
    r += f"\n{action} rapidtide [{session}] ..."

    # status variables
    run = True

    try:
        # check base settings
        pc.doOptionsCheck(options, sinfo, "rapidtide")

        # check if we have the session
        session_folder = os.path.join(options["sessionsfolder"], session)
        if not os.path.exists(session_folder):
            r += f"\n\n---> Session folder {session_folder} does not exist, cannot run rapidtide."
            run = False

        # hcp paths
        hcp_folders = hcp.getHCPPaths(sinfo, options)
        rapidtide_folder = os.path.join(session_folder, "rapidtide")
        os.makedirs(rapidtide_folder, exist_ok=True)

        # --- run checks
        if "hcp" not in sinfo:
            r += f"\n---> ERROR: There is no hcp info for session {sinfo['id']} in batch.txt"
            run = False

        # get bolds
        if not options["bolds"]:
            options["bolds"] = "rest"
        bolds, _, _, r = pc.use_or_skip_bold(sinfo, options, r)

        if len(bolds) == 0:
            # default was used
            if options["bolds"] == "rest":
                r += f"\n---> ERROR: No BOLD images found for session {sinfo['id']}! Check your data or the contents of the batch file."
                run = False
            else:
                r += "\n---> Automatic BOLD identification did not find any bolds using the --bolds parameter as is."
                boldtargets = options["bolds"].split(",")

        boldtargets = []
        for boldinfo in bolds:
            _, boldtarget, _ = pc.get_bold_names(boldinfo, options)
            boldtargets.append(boldtarget)

        # bolds loop
        report = {
            "done": [],
            "failed": [],
            "skipped": [],
            "ready": [],
        }

        if len(boldtargets) == 0:
            r += f"\n---> ERROR: No BOLD images found for session {sinfo['id']}! Check your data or the contents of the batch file."
            report["failed"].append("no bolds found")
            run = False
        else:
            r += f"\n---> Found {len(boldtargets)} bolds:"
            for boldtarget in boldtargets:
                r += f"\n  - {boldtarget}"

        # run in parallel
        if run:
            parelements = max(1, min(options["parelements"], len(boldtargets)))
            ppe = ProcessPoolExecutor(parelements)
            # process
            f = partial(
                _execute_rapidtide,
                options,
                sinfo,
                overwrite,
                run,
                hcp_folders,
                rapidtide_folder,
            )
            results = ppe.map(f, boldtargets)

            # merge r and report
            for result in results:
                r += result["r"]
                run_report = result["report"]
                if run_report["done"]:
                    report["done"].extend(run_report["done"])
                if run_report["failed"]:
                    report["failed"].extend(run_report["failed"])
                if run_report["skipped"]:
                    report["ready"].extend(run_report["ready"])
                if run_report["ready"]:
                    report["ready"].extend(run_report["not ready"])

            # parse report
            if report["failed"]:
                report = (
                    sinfo["id"],
                    f"rapidtide failed: {','.join(report['failed'])}",
                    len(report["failed"]),
                )
            else:
                message = "rapidtide: "
                sep = ""
                if report["done"]:
                    message += f"done: {','.join(report['done'])}"
                    sep = " | "
                if report["skipped"]:
                    message += f"{sep}skipped: {','.join(report['skipped'])}"

                report = (
                    sinfo["id"],
                    message,
                    0,
                )

        # rapidtide ------------------------------------------------------------
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = f"\n\n\n --- Failed during processing of session {session} with error:\n"
        r += str(errormessage)
        report = (sinfo["id"], "rapidtide failed", 1)

    except:
        r += f"\n --- Failed during processing of session {session} with error:\n {traceback.format_exc()}\n"
        report = (sinfo["id"], "rapidtide failed", 1)

    return (r, report)


def _execute_rapidtide(
    options, sinfo, overwrite, run, hcp_folders, rapidtide_folder, boldtarget
):
    # prepare return variables
    r = f"\n\n\n---> Working on bold {boldtarget}"
    report = {
        "done": [],
        "failed": [],
        "skipped": [],
        "ready": [],
    }

    # get session id
    session = sinfo["id"]

    # main outputs folder
    rapidtide_out = os.path.join(rapidtide_folder, boldtarget)
    if os.path.exists(rapidtide_out):
        if not overwrite:
            r += f"\n---> Skipping rapidtide for {boldtarget}, output folder already exists, and overwrite is not set: {rapidtide_out}"
            report["skipped"].append(boldtarget)
            return {"r": r, "report": report}
        else:
            r += f"\n---> Removing existing results in {rapidtide_out}"
            shutil.rmtree(rapidtide_out, ignore_errors=True)
    os.makedirs(rapidtide_out)

    # flirt ------------------------------------------------------------
    # run flirt to create masks if parameters are not provided
    if options["graymattermask"] is None and options["whitemattermask"] is None:
        r += f"\n\n---> Running FSL flirt to create gray or white matter masks for {boldtarget}"
        # in
        in_path = os.path.join(hcp_folders["hcp_nonlin"], "aparc+aseg.nii.gz")
        if not os.path.exists(in_path):
            r += f"\n---> ERROR: Cannot find aparc+aseg.nii.gz at {in_path}"

        # ref
        ref_path = os.path.join(
            hcp_folders["hcp_nonlin"], "Results", boldtarget, "brainmask_fs.2.nii.gz"
        )
        if not os.path.exists(ref_path):
            r += f"\n---> ERROR: Cannot find brainmask_fs.2.nii.gz at {ref_path}"
            run = False

        # init
        init_path = os.path.join(
            os.environ["FSLDIR"], "data", "atlases", "bin", "eye.mat"
        )

        # out
        out_path = os.path.join(rapidtide_out, "aparc+aseg_res-2.nii.gz")

        flirt_comm = (
            "flirt \
            -in %(in)s \
            -ref %(ref)s \
            -applyxfm \
            -init %(init)s \
            -interp nearestneighbour \
            -out %(out)s"
            % {
                "in": in_path,
                "ref": ref_path,
                "init": init_path,
                "out": out_path,
            }
        )

        # report command
        r += "\n\n------------------------------------------------------------\n"
        r += "Running FSL flirt command via QuNex:\n\n"
        r += flirt_comm.replace("                ", "")
        r += "\n------------------------------------------------------------\n"

        # run
        if run:
            # run
            if options["run"] == "run":
                # execute
                r, _, _, failed = pc.runExternalForFile(
                    out_path,
                    flirt_comm,
                    "Running FSL flirt",
                    overwrite=overwrite,
                    thread=f"{sinfo['id']}_{boldtarget}",
                    remove=options["log"] == "remove",
                    task="rapidtide_flirt",
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"]],
                    fullTest=None,
                    shell=True,
                    r=r,
                )
                if failed:
                    r += f"\n---> FSL flirt processing for session {session} failed"
                    report["failed"].append(boldtarget)
                else:
                    r += f"\n---> FSL flirt processing for session {session} completed"
                    report["done"].append(boldtarget)

            # just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    out_path, None, "FSL flirt " + session, r, overwrite=overwrite
                )

                if passed is None:
                    r += "\n---> FSL flirt can be run"
                    report["ready"].append(boldtarget)
                else:
                    r += f"\n---> FSL flirt processing for bold {boldtarget} would be skipped"
                    report["skipped"].append(boldtarget)

    # rapidtide --------------------------------------------------------
    r += f"\n\n---> Running rapidtide for {boldtarget}"
    boldname = f"{boldtarget}{options['nifti_tail']}.nii.gz"
    bold = os.path.join(hcp_folders["hcp_nonlin"], "Results", boldtarget, boldname)
    if not os.path.exists(bold):
        r += f"\n---> ERROR: Cannot find BOLD image {bold} for session {session}"
        report["failed"].append(boldtarget)
        run = False

    rapidtide_comm = (
        "rapidtide \
        %(bold)s \
        %(out)s \
        --noprogressbar"
        % {
            "bold": bold,
            "out": f"{rapidtide_out}/{boldtarget}{options['nifti_tail']}",
        }
    )

    # optional parameters
    if options["despecklepasses"] is not None:
        rapidtide_comm += (
            f"                --despecklepasses {options['despecklepasses']}"
        )
    if options["filterband"] is not None:
        rapidtide_comm += f"                --filterband {options['filterband']}"
    if options["searchrange"] is not None:
        rapidtide_comm += f"                --searchrange {options['searchrange']}"
    if options["nprocs"] is not None:
        rapidtide_comm += f"                --nprocs {options['nprocs']}"
    if options["nofitfilt"]:
        rapidtide_comm += "                --nofitfilt"
    if options["similaritymetric"] is not None:
        rapidtide_comm += (
            f"                --similaritymetric {options['similaritymetric']}"
        )
    if options["ampthresh"] is not None:
        rapidtide_comm += f"                --ampthresh {options['ampthresh']}"
    if options["outputlevel"] is not None:
        rapidtide_comm += f"                --outputlevel {options['outputlevel']}"
    if options["spatialfilt"] is not None:
        rapidtide_comm += f"                --spatialfilt {options['spatialfilt']}"
    if options["simcalcrange"] is not None:
        rapidtide_comm += f"                --simcalcrange {options['simcalcrange']}"
    if options["nodenoise"]:
        rapidtide_comm += "                --nodenoise"
    if options["rapidtide_extra_args"] is not None:
        rapidtide_comm += f" {options['rapidtide_extra_args']}"

    # run
    if run:
        # run
        if options["run"] == "run":
            # do more complex parameter setup here
            if options["brainmask"] is not None and options["brainmask"] != "None":
                rapidtide_comm += f"                --brainmask {options['brainmask']}"
            elif options["brainmask"] is None:
                brainmask = os.path.join(
                    hcp_folders["hcp_nonlin"],
                    "Results",
                    boldtarget,
                    "brainmask_fs.2.nii.gz",
                )
                if not os.path.exists(brainmask):
                    r += f"\n---> ERROR: Cannot find the default --brainmask: brainmask_fs.2.nii.gz at {brainmask}"
                    run = False
                else:
                    rapidtide_comm += f"                --brainmask {brainmask}"

            default_mask = os.path.join(rapidtide_out, "aparc+aseg_res-2.nii.gz")
            if (
                options["graymattermask"] is not None
                and options["graymattermask"] != "None"
            ):
                rapidtide_comm += (
                    f"                --graymattermask {options['graymattermask']}"
                )
            elif options["graymattermask"] is None:
                if not os.path.exists(default_mask):
                    r += "\n---> ERROR: Cannot find the default --graymattermask: aparc+aseg_res-2.nii.gz at {default_mask}"
                    run = False
                else:
                    rapidtide_comm += (
                        f"                --graymattermask {default_mask}:APARC_GRAY"
                    )

            if (
                options["whitemattermask"] is not None
                and options["whitemattermask"] != "None"
            ):
                rapidtide_comm += (
                    f"                --whitemattermask {options['whitemattermask']}"
                )
            elif options["whitemattermask"] is None:
                if not os.path.exists(default_mask):
                    r += "\n---> ERROR: Cannot find the default --whitemattermask: aparc+aseg_res-2.nii.gz at {default_mask}"
                    run = False
                else:
                    rapidtide_comm += (
                        f"                --whitemattermask {default_mask}:APARC_WHITE"
                    )

            if (
                options["refineexclude"] is not None
                and options["refineexclude"] != "None"
            ):
                rapidtide_comm += (
                    f"                --refineexclude {options['refineexclude']}"
                )
            elif options["refineexclude"] is None:
                refineexclude = os.path.join(
                    hcp_folders["hcp_nonlin"],
                    "Results",
                    boldtarget,
                    f"{boldtarget}_dropouts.nii.gz",
                )
                if not os.path.exists(refineexclude):
                    r += f"\n---> ERROR: Cannot find the default --refineexclude: {refineexclude}"
                    run = False
                else:
                    rapidtide_comm += f"                --refineexclude {refineexclude}"

            # execute
            r, _, _, failed = pc.runExternalForFile(
                None,
                rapidtide_comm,
                "Running rapidtide",
                overwrite=overwrite,
                thread=f"{sinfo['id']}_{boldtarget}",
                remove=options["log"] == "remove",
                task="rapidtide",
                logfolder=options["comlogs"],
                logtags=[options["logtag"]],
                fullTest=None,
                shell=True,
                r=r,
            )
            if failed:
                r += f"\n---> rapidtide processing for bold {boldtarget} failed"
                report["failed"].append(boldtarget)
            else:
                r += f"\n---> rapidtide processing for session {boldtarget} completed"

        # just checking
        else:
            passed, _, r, failed = pc.checkRun(
                None, None, "rapidtide " + session, r, overwrite=overwrite
            )
            if passed == "done":
                r += "\n---> rapidtide can be run"
                report["ready"].append(boldtarget)
            else:
                r += f"\n---> rapidtide processing for bold {boldtarget} would be skipped"
                report["skipped"].append(boldtarget)

    return {"r": r, "report": report}
