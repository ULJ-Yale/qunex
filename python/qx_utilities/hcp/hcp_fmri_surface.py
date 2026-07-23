#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_fmri_surface.py``

The HCP fMRISurface pipeline and its per-BOLD executor.
"""

import os
import os.path
import traceback
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import qx_utilities.general.core as gc
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.hcp.hcp_log import SessionLog, ReportLog
from qx_utilities.hcp.hcp_utils import (
    _build_skipped_report,
    do_hcp_options_check,
)


def hcp_fmri_surface(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_fmri_surface [... processing options]``

    Run the fMRI Surface (GenericfMRISurfaceProcessingPipeline.sh) step of the
    HCP Pipeline .

    ..  qx_command:
        type: processing.session

    Warning:
        The code expects all the previous HCP preprocessing steps
        (hcp_pre_freesurfer, hcp_freesurfer, hcp_post_freesurfer,
        hcp_fmri_volume) to have been run and finished successfully. The
        command will test for presence of key files but do note that it won't
        run a thorough check for all the required files.

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

        --bolds (str, default 'all'):
            Which bold images (as they are specified in the batch.txt file) to
            process. It can be a single type (e.g. 'task'), a pipe separated
            list (e.g. 'WM|Control|rest') or 'all' to process all.

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

        --hcp_folderstructure (str, default 'hcpls'):
            If set to 'hcpya' the folder structure used in the initial HCP Young
            Adults study is used. Specifically, the source files are stored in
            individual folders within the main 'hcp' folder in parallel with the
            working folders and the 'MNINonLinear' folder with results. If set
            to'hcpls' the folder structure used in the HCP Life Span study is
            used. Specifically, the source files are all stored within their
            individual subfolders located in the joint 'unprocessed' folder in
            the main 'hcp' folder, parallel to the working folders and the
            'MNINonLinear' folder.

        --hcp_filename (str, default 'automated'):
            How to name the BOLD files once mapped into the hcp input folder
            structure. The default ('automated') will automatically name each
            file by their number (e.g. BOLD_1). The alternative ('userdefined')
            is to use the file names, which can be defined by the user prior to
            mapping (e.g. rfMRI_REST1_AP).

        --hcp_bold_prefix (str, default 'BOLD'):
            The prefix to use when generating BOLD names (see 'hcp_filename')
            for BOLD working folders and results.

        --hcp_lowresmesh (str, default '32'):
            The number of vertices to be used in the low-resolution grayordinate
            mesh (in thousands).

        --hcp_bold_res (str, default '2'):
            The resolution of the BOLD volume data in mm.

        --hcp_grayordinatesres (str, default '2'):
            The size of voxels for the subcortical and cerebellar data in
            grayordinate space in mm.

        --hcp_bold_smoothFWHM (str, default '2'):
            The size of the smoothing kernel (in mm).

        --hcp_regname (str, default 'MSMSulc'):
            The name of the registration used.

        --hcp_species (str, default ''):
            Species label (Human, Macaque, Marmoset, etc.). When unset the HCP
            pipeline default (Human) is used. Only relevant for non-human
            species.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --longitudinal:
            Set this flag if you are running the longitudinal variant of this
            command.

    Output files:
        The results of this step will be present in the MNINonLinear folder
        in the sessions's root hcp folder::

            study
            └─ sessions
               └─ session1_session1
                  └─ hcp
                     └─ subject1_session1
                       └─ MNINonlinear
                          └─ Results
                             └─ BOLD_1

    Notes:
        Runs the fMRI Surface (GenericfMRISurfaceProcessingPipeline.sh) step of
        the HCP Pipeline. It uses the FreeSurfer segmentation and surface
        reconstruction to map BOLD timeseries to grayordinate representation
        and generates .dtseries.nii files.

        hcp_fmri_surface parameter mapping:

            ============================= =======================
            QuNex parameter               HCPpipelines parameter
            ============================= =======================
            ``hcp_lowresmesh``            ``lowresmesh``
            ``hcp_bold_res``              ``fmrires``
            ``hcp_bold_smoothFWHM``       ``smoothingFWHM``
            ``hcp_grayordinatesres``      ``grayordinatesres``
            ``hcp_regname``               ``regname``
            ``hcp_species``               ``species``
            ``hcp_printcom``              ``printcom``
            ``hcp_longitudinal_template`` ``longitudinal-template``
            ``longitudinal``              ``is-longitudinal``
            ============================= =======================

    Examples:
        Example run from the base study folder with ``--test`` flag. Here
        ``--parsessions`` specifies how many sessions to run concurrently and
        ``--parelements`` specifies how many elements (e.g. bold images) to
        process concurrently::

            qunex hcp_fmri_surface  \\
                --batchfile="processing/batch.txt"  \\
                --sessionsfolder="sessions"  \\
                --parsessions="10"  \\
                --parelements="4"  \\
                --overwrite="no"  \\
                --test

        Run using absolute paths with scheduler::

            qunex hcp_fmri_surface  \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"  \\
                --sessionsfolder="<path_to_study_folder>/sessions"  \\
                --parsessions="4"  \\
                --parelements="4"  \\
                --overwrite="yes"  \\
                --scheduler="SLURM,time=24:00:00,cpus-per-task=2,mem-per-cpu=1300,partition=day"

        Extra example::

            qunex hcp_fmri_surface \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10
    """

    log = SessionLog(sinfo, options, "HCP fMRI Surface pipeline")

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
        pc.do_options_check(options, sinfo, "hcp_fmri_surface")
        do_hcp_options_check(options, "hcp_fmri_surface")
        hcp = get_hcp_paths(sinfo, options)

        # --- bold filtering not yet supported!
        # btargets = options['bolds'].split("|")

        # --- run checks
        if "hcp" not in sinfo:
            log.raw("\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"]))
            run = False

        # -> PostFS results
        tfile = os.path.join(
            hcp["hcp_nonlin"],
            "fsaverage_LR32k",
            sinfo["id"] + options["hcp_suffix"] + ".32k_fs_LR.wb.spec",
        )

        if os.path.exists(tfile):
            log.step("PostFS results present.")
        else:
            log.error("Could not find PostFS processing results.")
            run = False

        # --- Get sorted bold numbers
        bolds, bskip, report["boldskipped"] = log.use_or_skip_bold(sinfo, options)
        if len(bolds) == 0:
            log.raw("\n---> ERROR: No BOLD images found for session %s! Check your data or the contents of the batch file."
                % (sinfo["id"]))
            run = False

        _build_skipped_report(report, bskip, options)

        parelements = max(1, min(options["parelements"], len(bolds)))
        log.raw("\n%s %d BOLD images in parallel" % (
            pc.action("Running", options["run"]),
            parelements,
        ))

        # create a multiprocessing Pool
        process_pool_executor = ProcessPoolExecutor(parelements)
        # process
        f = partial(execute_hcp_fmri_surface, sinfo, options, overwrite, hcp, run)
        results = process_pool_executor.map(f, bolds)

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

        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP fMRI Surface: bolds " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.capture(str(errormessage))
        report = (sinfo["id"], "HCP fMRI Surface failed", 1)
    except Exception:
        log.unknown_error()
        report = (sinfo["id"], "HCP fMRI Surface failed", 1)

    log.close(pipeline="HCP fMRISurface")

    return log.result(report)


def execute_hcp_fmri_surface(sinfo, options, overwrite, hcp, run, boldinfo):

    printbold, boldtarget, _ = pc.get_bold_names(boldinfo, options)

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
        log.raw("\n\n---> %s BOLD image %s" % (
            pc.action("Processing", options["run"]),
            printbold,
        ))
        boldok = True

        # --- check for bold image
        if "longitudinal" not in options or not options["longitudinal"]:
            boldimg = os.path.join(
                hcp["hcp_nonlin"], "Results", boldtarget, "%s.nii.gz" % (boldtarget)
            )
            boldok = log.check_for_file(boldimg,
                "\n     ... fMRIVolume preprocessed bold image present",
                f"\n     ... ERROR: fMRIVolume preprocessed bold image missing {boldimg}!",
                status=boldok,
            )

        # --- Set up the command
        comm = (
            os.path.join(
                hcp["hcp_base"],
                "fMRISurface",
                "GenericfMRISurfaceProcessingPipeline.sh",
            )
            + " "
        )

        # path and session
        path = sinfo["hcp"]
        session = sinfo["id"] + options["hcp_suffix"]

        # longitudinal
        if options["longitudinal"]:
            studyfolder = gc.deduce_folders(options)["basefolder"]
            if not studyfolder:
                log.raw("\nERROR: cannot deduce the QuNex study folder from provided parameters! Please provide the sessionsfolder or the studyfolder parameter.")
                boldok = False
            # replace path
            path = os.path.join(studyfolder, "subjects", sinfo["subject"])
            session = f"{sinfo['id']}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"

        elements = [
            ("path", path),
            ("session", session),
            ("fmriname", boldtarget),
            ("lowresmesh", options["hcp_lowresmesh"]),
            ("fmrires", options["hcp_bold_res"]),
            ("smoothingFWHM", options["hcp_bold_smoothFWHM"]),
            ("grayordinatesres", options["hcp_grayordinatesres"]),
            ("regname", options["hcp_regname"]),
            ("printcom", options["hcp_printcom"]),
        ]

        # optional species / NHP parameter, only relevant for non-human
        # species, when unset the HCP pipeline default (Human) is used
        if options["hcp_species"]:
            elements.append(("species", options["hcp_species"]))

        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])

        # -- Report command
        if boldok:
            log.pipeline_command(comm)

        # -- Test files
        tfile = None
        full_test = None
        if not options["longitudinal"]:
            tfile = os.path.join(
                hcp["hcp_nonlin"],
                "Results",
                boldtarget,
                "%s%s.dtseries.nii" % (boldtarget, "_Atlas"),
            )

            if hcp["hcp_bold_surf_check"]:
                full_test = {
                    "tfolder": hcp["base"],
                    "tfile": hcp["hcp_bold_surf_check"],
                    "fields": [
                        ("sessionid", sinfo["id"] + options["hcp_suffix"]),
                        ("scan", boldtarget),
                    ],
                    "specfolder": options["specfolder"],
                }

        # -- Run
        if run and boldok:
            if options["run"] == "run":
                if not options["longitudinal"] and (
                    overwrite and os.path.exists(tfile)
                ):
                    os.remove(tfile)

                logtags = [options["logtag"], boldtarget]
                if options["longitudinal"]:
                    logtags.append("long")

                _, _, failed = log.run_external(
                    tfile,
                    comm,
                    "Running HCP fMRISurface",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=logtags,
                    full_test=full_test,
                    shell=True,
                )

                if failed:
                    report["failed"].append(printbold)
                else:
                    report["done"].append(printbold)

            # -- just checking
            else:
                passed, _, failed = log.check_run(
                    tfile,
                    full_test,
                    "HCP fMRISurface " + boldtarget,
                    overwrite=overwrite,
                )
                if passed is None:
                    log.step("HCP fMRISurface can be run")
                    report["ready"].append(printbold)
                else:
                    report["skipped"].append(printbold)

        else:
            report["not ready"].append(printbold)
            if options["run"] == "run":
                log.error("something missing, skipping this BOLD!")
            else:
                log.error("something missing, this BOLD would be skipped!")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.capture("\n\n\n --- Failed during processing of bold %s with error:\n" % (printbold))
        log.raw(str(errormessage))
        report["failed"].append(printbold)
    except Exception:
        log.raw("\n --- Failed during processing of bold %s with error:\n %s\n" % (
            printbold,
            traceback.format_exc(),
        ))
        report["failed"].append(printbold)

    return {"r": log.text, "report": report}
