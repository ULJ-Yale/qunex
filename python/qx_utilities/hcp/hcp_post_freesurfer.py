#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_post_freesurfer.py``

The HCP PostFreeSurfer pipeline.
"""

import os
import os.path

import qx_utilities.general.exceptions as ge
import qx_utilities.general.snapshots as gs
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    _prepare_postfreesurfer_snapshot_state,
    do_hcp_options_check,
)
from qx_utilities.hcp.hcp_utils import _nhp_postfs_paths


def hcp_post_freesurfer(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_post_freesurfer [... processing options]``

    Run the PostFS step of the HCP Pipeline (PostFreeSurferPipeline.sh).

    ..  qx_command:
        type: processing.session

    Warning:
        The code expects the previous step (hcp_freesurfer) to have run
        successfully and checks for presence of the last file that should have
        been generated. Due to the number of files that it requires, it does not
        make a full check for all of them!

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging  data is
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
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_processing_mode (str, default 'HCPStyleData'):
            Controls whether the HCP acquisition and processing guidelines
            should be treated as requirements ('HCPStyleData') or if additional
            processing functionality is allowed ('LegacyStyleData'). In this
            case running processing w/o a T2w image.

        --hcp_folderstructure (str, default 'hcpls'):
            If set to 'hcpya' the folder structure used in the initial HCP
            Young Adults study is used. Specifically, the source files are
            stored in individual folders within the main 'hcp' folder in
            parallel with the working folders and the 'MNINonLinear' folder
            with results. If set to 'hcpls' the folder structure used in the
            HCP Life Span study is used. Specifically, the source files are
            all stored within their individual subfolders located in the joint
            'unprocessed' folder in the main 'hcp' folder, parallel to the
            working folders and the 'MNINonLinear' folder.

        --hcp_filename (str, default 'automated'):
            How to name the BOLD files once mapped intothe hcp input folder
            structure. The default ('automated') will automatically name each
            file by their number (e.g. BOLD_1). The alternative ('userdefined')
            is to use the file names, which can be defined by the user prior to
            mapping (e.g. rfMRI_REST1_AP).

        --hcp_t2 (str, default 't2'):
            'NONE' if no T2w image is available and the preprocessing should
            be run without them, anything else otherwise. 'NONE' is
            only valid if 'LegacyStyleData' processing mode was specified.

        --hcp_surfatlasdir (str, HCP "standard_mesh_atlases"):
            Surface atlas directory. For non-human species (hcp_species other
            than 'Human') the default is the species-specific surface atlas
            folder inside HCP's NHP_NNP templates folder.

        --hcp_grayordinatesres (str, default '2'):
            The resolution of the volume part of the grayordinate representation
            in mm.

        --hcp_grayordinatesdir (str, default HCP "91282_Greyordinates"):
            Grayordinates space directory. For non-human species (hcp_species
            other than 'Human') the default is the species-specific surface
            atlas folder inside HCP's NHP_NNP templates folder, which also holds
            the grayordinates data.

        --hcp_subcortgraylabels (str, default HCP "FreeSurferSubcorticalLabelTableLut.txt"):
            The location of FreeSurferSubcorticalLabelTableLut.txt.

        --hcp_refmyelinmaps (str, default HCP "Conte69.MyelinMap_BC.164k_fs_LR.dscalar.nii"):
            Group myelin map to use for bias correction. For non-human species
            (hcp_species other than 'Human') the default is the species-specific
            group myelin map inside HCP's NHP_NNP templates folder.

        --hcp_hiresmesh (int, default 164):
            The number of vertices for the high resolution mesh of each
            hemisphere (in thousands).

        --hcp_lowresmesh (str, default '32'):
            The number of vertices for the low resolution mesh of each
            hemisphere (in thousands). Provide a comma separated list of numbers
            to generate multiple low resolution meshes, for example: 32,10.

        --hcp_regname (str, default 'MSMSulc'):
            The registration used, FS or MSMSulc.

        --hcp_mcsigma (str, default 'sqrt(200)'):
            Correction sigma used for metric smoothing.

        --hcp_inflatescale (int, default 1):
            Inflate extra scale parameter.

        --hcp_fs_ind_mean (str, default 'YES'):
            Whether to use the mean of the subject's myelin map as reference
            map's myelin map mean, YES or NO, defaults to YES.

        --hcp_freesurfer_labels (str, default '${HCPPIPEDIR}/global/config/FreeSurferAllLut.txt'):
            Path to the location of the FreeSurfer look up table file.

        --hcp_thickness_regression (str, default 'BOTH'):
            Wwhether to use the updated curvature-thickness regression, set to
            'OLD', 'NEW' or 'BOTH', defaults to 'BOTH'.

        --hcp_species (str, default 'Human'):
            Target species for processing. When set to anything other than
            'Human' (case-insensitive), the non-human primate (NHP) variant of
            PostFreeSurfer processing is engaged and the species-specific
            parameters below are passed to the pipeline.

        --hcp_myelin_volume_fwhm (float, default detected):
            Myelin mapping volume smoothing FWHM. Only relevant for non-human
            species (when hcp_species is not 'Human'). When unset the HCP
            pipeline default is used.

        --hcp_myelin_surface_fwhm (float, default detected):
            Myelin mapping surface smoothing FWHM. Only relevant for non-human
            species (when hcp_species is not 'Human'). When unset the HCP
            pipeline default is used.

        --hcp_msmsulc_conf (str, default detected):
            MSMSulc configuration. Only relevant for non-human species (when
            hcp_species is not 'Human'). When unset the HCP pipeline default
            is used.

        --hcp_flatmap_root_name (str, default detected):
            Flat map root name. Only relevant for non-human species (when
            hcp_species is not 'Human'). When unset the HCP pipeline default
            is used.

    Output files:
        The results of this step will be present in the MNINonLinear folder
        in the sessions's root hcp folder.

    Notes:
        Runs the PostFreeSurfer step (PostFreeSurferPipeline.sh) of the HCP
        Pipelines. It creates Workbench compatible files based on the Freesurfer
        segmentation and surface registration. It uses the adjusted version of
        the HCP code that enables the preprocessing to run also if no T2w image
        is present.

        hcp_post_freesurfer parameter mapping:

            ============================ ========================
            QuNex parameter              HCPpipelines parameter
            ============================ ========================
            ``hcp_freesurfer_labels``    ``freesurferlabels``
            ``hcp_surfatlasdir``         ``surfatlasdir``
            ``hcp_grayordinatesdir``     ``grayordinatesdir``
            ``hcp_grayordinatesres``     ``grayordinatesres``
            ``hcp_subcortgraylabels``    ``subcortgraylabels``
            ``hcp_refmyelinmaps``        ``refmyelinmaps``
            ``hcp_hiresmesh``            ``hiresmesh``
            ``hcp_lowresmesh``           ``lowresmesh``
            ``hcp_mcsigma``              ``mcsigma``
            ``hcp_regname``              ``regname``
            ``hcp_inflatescale``         ``inflatescale``
            ``hcp_fs_ind_mean``          ``use-ind-mean``
            ``hcp_processing_mode``      ``processing-mode``
            ``hcp_thickness_regression`` ``thickness-regression``
            ``hcp_species``              ``species``
            ``hcp_myelin_volume_fwhm``   ``myelin-volume-fwhm``
            ``hcp_myelin_surface_fwhm``  ``myelin-surface-fwhm``
            ``hcp_msmsulc_conf``         ``msmsulc-conf``
            ``hcp_flatmap_root_name``    ``flatmap-root-name``
            ============================ ========================

        The ``hcp_species`` parameter and the four species-specific parameters
        below it are only passed to PostFreeSurferPipeline.sh when
        ``hcp_species`` is set to a non-human species (case-insensitive).

    Examples:
        Example run from the base study folder with test flag::

            qunex hcp_post_freesurfer \\
                --batchfile="processing/batch.txt" \\
                --sessionsfolder="sessions" \\
                --parsessions="10" \\
                --overwrite="no" \\
                --test

        Example run with absolute paths with scheduler::

            qunex hcp_post_freesurfer \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --parsessions="4" \\
                --hcp_t2="NONE" \\
                --overwrite="yes" \\
                --scheduler="SLURM,time=24:00:00,cpus-per-task=2,mem-per-cpu=1250,partition=day"

        Additional examples::

            qunex hcp_post_freesurfer \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10

        ::

            qunex hcp_post_freesurfer \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --hcp_t2=NONE

        Example run for a non-human primate (NHP) species::

            qunex hcp_post_freesurfer \\
                --batchfile="processing/batch.txt" \\
                --sessionsfolder="sessions" \\
                --parsessions="4" \\
                --hcp_species="MacaqueRhesus" \\
                --overwrite="yes"
    """

    log = SessionLog(sinfo, options, "HCP PostFreeSurfer Pipeline", tail="\n")

    run = True
    report = "Error"

    try:
        pc.do_options_check(options, sinfo, "hcp_post_freesurfer")
        do_hcp_options_check(options, "hcp_post_freesurfer")
        hcp = get_hcp_paths(sinfo, options)

        species = options["hcp_species"]
        is_human = not species or species.lower() == "human"

        # --- run checks
        if "hcp" not in sinfo:
            log.raw("\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"]))
            run = False

        # -> FS results, check only for human
        if is_human:
            if os.path.exists(os.path.join(hcp["FS_folder"], "mri", "aparc+aseg.mgz")):
                log.step("FS results present.")
            else:
                log.error("Could not find Freesurfer processing results.")
                run = False

        # -> T2w image
        if (
            hcp["T2w"] in ["", "NONE"]
            and options["hcp_processing_mode"] == "HCPStyleData"
        ):
            log.error("The requested HCP processing mode is 'HCPStyleData', however, no T2w image was specified!")
            run = False

        # hcp_freesurfer_labels
        freesurferlabels = ""
        if options["hcp_freesurfer_labels"] is None:
            freesurferlabels = os.path.join(hcp["hcp_Config"], "FreeSurferAllLut.txt")
        else:
            freesurferlabels = options["hcp_freesurfer_labels"]

        # default surface atlas, grayordinates and reference myelin map paths
        # human ones live directly in the HCP templates folder, non-human ones
        # in the species-specific NHP_NNP folder
        if is_human:
            tpl = {
                "surfatlasdir": os.path.join(
                    hcp["hcp_Templates"], "standard_mesh_atlases"
                ),
                "grayordinatesdir": os.path.join(
                    hcp["hcp_Templates"], "91282_Greyordinates"
                ),
                "refmyelinmaps": os.path.join(
                    hcp["hcp_Templates"],
                    "standard_mesh_atlases",
                    "Conte69.MyelinMap_BC.164k_fs_LR.dscalar.nii",
                ),
            }
        else:
            tpl = _nhp_postfs_paths(hcp["hcp_Templates"], species)
            if tpl is None:
                tpl = {}
                log.raw("\n---> NOTE: species '%s' is not in QuNex's built-in NHP template map; "
                    "the surface atlas, grayordinates and reference myelin map paths have to "
                    "be provided explicitly via hcp_surfatlasdir, hcp_grayordinatesdir and "
                    "hcp_refmyelinmaps." % (species))

        # hcp_surfatlasdir
        if options["hcp_surfatlasdir"] is None:
            surfatlasdir = tpl.get("surfatlasdir")
        else:
            surfatlasdir = options["hcp_surfatlasdir"]

        # hcp_grayordinatesdir
        if options["hcp_grayordinatesdir"] is None:
            grayordinatesdir = tpl.get("grayordinatesdir")
        else:
            grayordinatesdir = options["hcp_grayordinatesdir"]

        # hcp_subcortgraylabels
        subcortgraylabels = ""
        if options["hcp_subcortgraylabels"] is None:
            subcortgraylabels = os.path.join(
                hcp["hcp_Config"], "FreeSurferSubcorticalLabelTableLut.txt"
            )
        else:
            subcortgraylabels = options["hcp_subcortgraylabels"]

        # hcp_refmyelinmaps
        if options["hcp_refmyelinmaps"] is None:
            refmyelinmaps = tpl.get("refmyelinmaps")
        else:
            refmyelinmaps = options["hcp_refmyelinmaps"]

        # compile the command
        comm = (
            os.path.join(hcp["hcp_base"], "PostFreeSurfer", "PostFreeSurferPipeline.sh")
            + " "
        )

        elements = [
            ("path", sinfo["hcp"]),
            ("subject", sinfo["id"] + options["hcp_suffix"]),
            ("surfatlasdir", surfatlasdir),
            ("grayordinatesdir", grayordinatesdir),
            ("grayordinatesres", options["hcp_grayordinatesres"]),
            ("hiresmesh", options["hcp_hiresmesh"]),
            ("lowresmesh", options["hcp_lowresmesh"].replace(",", "@")),
            ("subcortgraylabels", subcortgraylabels),
            ("freesurferlabels", freesurferlabels),
            ("refmyelinmaps", refmyelinmaps),
            ("mcsigma", options["hcp_mcsigma"]),
            ("regname", options["hcp_regname"]),
            ("inflatescale", options["hcp_inflatescale"]),
            ("processing-mode", options["hcp_processing_mode"]),
        ]

        # optional parameters
        if options["hcp_fs_ind_mean"] != "YES":
            elements.append(("use-ind-mean", options["hcp_fs_ind_mean"]))

        if options["hcp_thickness_regression"] is not None:
            elements.append((
                "thickness-regression",
                options["hcp_thickness_regression"],
            ))

        # species-specific (NHP) parameters, only relevant for non-human species
        # the four tuning parameters are optional; when unset they are not
        # passed and the HCP pipeline applies its own defaults
        if not is_human:
            elements.append(("species", species))
            optional_species_params = [
                ("myelin-volume-fwhm", options["hcp_myelin_volume_fwhm"]),
                ("myelin-surface-fwhm", options["hcp_myelin_surface_fwhm"]),
                ("msmsulc-conf", options["hcp_msmsulc_conf"]),
                ("flatmap-root-name", options["hcp_flatmap_root_name"]),
            ]
            for k, v in optional_species_params:
                if v is not None:
                    elements.append((k, v))

        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])

        # -- Report command
        if run:
            log.pipeline_command(comm)

        # -- Test files
        tfolder = hcp["hcp_nonlin"]
        tfile = os.path.join(
            tfolder,
            sinfo["id"]
            + options["hcp_suffix"]
            + ".corrThickness.164k_fs_LR.dscalar.nii",
        )

        if hcp["hcp_postfs_check"]:
            full_test = {
                "tfolder": hcp["base"],
                "tfile": hcp["hcp_postfs_check"],
                "fields": [("sessionid", sinfo["id"] + options["hcp_suffix"])],
                "specfolder": options["specfolder"],
            }
        else:
            full_test = None

        # -- run
        if run:
            if options["run"] == "run":
                if overwrite or not os.path.exists(tfile):
                    log.step("Recording pre-PostFreeSurfer snapshot ...")
                    _prepare_postfreesurfer_snapshot_state(hcp)

                # ---> clean up test file if overwrite
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                _, report, failed = log.run_external(
                    tfile,
                    comm,
                    "Running HCP PostFS",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    full_test=full_test,
                    shell=True,
                )

            # -- just checking
            else:
                passed, report, failed = log.check_run(
                    tfile, full_test, "HCP PostFS", overwrite=overwrite
                )
                if passed is None:
                    log.step("HCP PostFS can be run")
                    report = "HCP PostFS can be run"
                    failed = 0
        else:
            log.step("Session cannot be processed.")
            report = "HCP PostFS cannot be run"
            failed = 1

    except ge.CommandFailed as e:
        log.command_failed(e, "PostFreeSurfer")
        report = "PostFS failed"
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.capture(str(errormessage))
        failed = 1
    except Exception:
        log.unknown_error()
        failed = 1

    log.close(pipeline="HCP PostFS")

    # -- take freesurfer_end_snapshot
    if options["run"] == "run" and failed == 0:
        postfs_start_snapshot = os.path.join(
            hcp["snapshots"], "postfreesurfer_start.txt"
        )
        if os.path.exists(postfs_start_snapshot):
            gs.compare_snapshots(
                before=postfs_start_snapshot,
                after=os.path.join(hcp["base"]),
                outfile=os.path.join(hcp["snapshots"], "postfreesurfer_diff.txt"),
                exclude=hcp["snapshots"],
            )
        else:
            log.warning("PostFreeSurfer start snapshot missing, skipping diff generation.")

    return log.result(report, failed)
