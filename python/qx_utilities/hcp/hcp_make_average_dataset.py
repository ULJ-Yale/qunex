#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_make_average_dataset.py``

Creation of an HCP average dataset across sessions.
"""

import os
import os.path

import qx_utilities.general.core as gc
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    do_hcp_options_check,
)


def hcp_make_average_dataset(sessions, options, overwrite=True, thread=0):
    """
    ``hcp_make_average_dataset [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run the HCP make average dataset pipeline (MakeAverageDataset.sh).

    ..  qx_command:
        type: processing.study
        aliases: hcp_mad

    Warning:
        The code expects the HCP minimal preprocessing pipeline to be executed.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions' information.

        --studyfolder (str):
            The path to the study folder. The sessions are in its `sessions`
            folder, unless --sessionsfolder names another one.

        --sessionsfolder (str, default '<studyfolder>/sessions'):
            The path to the folder with the sessions. Set it only when the
            sessions are not in the `sessions` folder of the study. With
            neither --studyfolder nor --sessionsfolder given, the current
            folder is used. The average dataset is made in its
            `average_dataset` folder.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_outgroupname (str):
            Name to use for the group output folder. Mandatory.

        --hcp_surface_atlas_dir (str, default '${HCPPIPEDIR}/global/templates/standard_mesh_atlases'):
            Path to the location of the standard surfaces.

        --hcp_grayordinates_dir (str, default '${HCPPIPEDIR}/global/templates/91282_Greyordinates'):
            Path to the location of the standard grayorinates space.

        --hcp_hiresmesh (int, default 164):
            High resolution mesh node count.

        --hcp_lowresmeshes (int, default 32):
            Low resolution meshes node count. To provide more values
            separate them with commas.

        --hcp_freesurfer_labels (str, default '${HCPPIPEDIR}/global/config/FreeSurferAllLut.txt'):
            Path to the location of the FreeSurfer look up table file.

        --hcp_pregradient_smoothing (int, default 1):
            Sigma of the pregradient smoothing.

        --hcp_mad_regname (str, default 'MSMAll'):
            Name of the registration.

        --hcp_mad_videen_maps (str, default 'corrThickness,thickness,MyelinMap_BC,SmoothedMyelinMap_BC'):
            Maps you want to use for the videen palette.

        --hcp_mad_greyscale_maps (str, default 'sulc,curvature'):
            Maps you want to use for the greyscale palette.

        --hcp_mad_distortion_maps (str, default 'SphericalDistortion,ArealDistortion,EdgeDistortion'):
            Distortion maps.

        --hcp_mad_gradient_maps (str, default 'MyelinMap_BC,SmoothedMyelinMap_BC,corrThickness'):
            Maps you want to compute the gradient on.

        --hcp_mad_std_maps (str, default 'sulc@curvature,corrThickness,thickness,MyelinMap_BC'):
            Maps you want to compute the standard deviation on.

        --hcp_mad_multi_maps (str, default 'NONE'):
            Maps with more than one map (column) that cannot be merged and must
            be averaged.

    Output files:
        The sessions' hcp folders are linked into
        <sessionsfolder>/average_dataset/<hcp_outgroupname>, the study folder
        MakeAverageDataset.sh runs in, and the script writes the average
        dataset into its <hcp_outgroupname> folder,
        <sessionsfolder>/average_dataset/<hcp_outgroupname>/<hcp_outgroupname>.
        hcp_temporal_ica links it in as the group folder of a multi-session
        run with the same --hcp_outgroupname, unless that group folder
        already holds an average dataset: a link an earlier run made to a
        dataset named with --hcp_tica_average_dataset, or a folder from an
        older QuNex layout, is used as it is (see hcp_temporal_ica).

    Notes:
        Mapping of QuNex parameters onto HCP make average dataset parameters:
            Below is a detailed specification about how QuNex parameters are
            mapped onto the HCP make average dataset parameters.

            ================================== =====================================
            QuNex parameter                    HCP make average dataset parameter
            ================================== =====================================
            ``hcp_outgroupname``               ``group-average-name``
            ``hcp_surface_atlas_dir``          ``surface-atlas-dir``
            ``hcp_grayordinates_dir``          ``grayordinates-space-dir``
            ``hcp_hiresmesh``                  ``high-res-mesh``
            ``hcp_lowresmeshes``               ``low-res-meshes``
            ``hcp_freesurfer_labels``          ``freesurfer-labels``
            ``hcp_pregradient_smoothing``      ``sigma``
            ``hcp_mad_regname``                ``reg-name``
            ``hcp_mad_videen_maps``            ``videen-maps``
            ``hcp_mad_greyscale_maps``         ``greyscale-maps``
            ``hcp_mad_distortion_maps``        ``distortion-maps``
            ``hcp_mad_gradient_maps``          ``gradient-maps``
            ``hcp_mad_std_maps``               ``std-maps``
            ``hcp_mad_multi_maps``             ``multi-maps``
            ================================== =====================================

    Examples:
        A run with the default set of parameters::

            qunex hcp_make_average_dataset \\
                --studyfolder="<path_to_study_folder>" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_outgroupname="hcp_group"

    """
    sessionid_list = sessions.get_list_by_key("id", sep=",")
    log = SessionLog({"id": sessionid_list}, options, "HCP make average dataset pipeline", label="Session ids")

    run = True
    report = "Error"

    try:
        do_hcp_options_check(options, "hcp_make_average_dataset")

        # subject_list
        subject_list = ""

        # check sessions
        for session in sessions:
            if "hcp" in session:
                hcp = get_hcp_paths(session, options)
            else:
                log.error(f"There is no hcp info for session {session['id']} in batch.txt")
                run = False

            # subject_list
            if subject_list == "":
                subject_list = session["id"] + options["hcp_suffix"]
            else:
                subject_list = (
                    subject_list + "@" + session["id"] + options["hcp_suffix"]
                )

        # mandatory parameters
        # hcp_outgroupname
        outgroupname = ""
        if options["hcp_outgroupname"] is None:
            log.error("hcp_outgroupname is not provided!")
            run = False
        else:
            outgroupname = options["hcp_outgroupname"]

        # study_dir prep
        study_dir = ""

        # single session
        if len(sessions) == 1:
            log.error("hcp_make_average_dataset needs to be ran across several sessions!")
            run = False

        # multi session, set up only when the sessions and the group name are
        # all there
        elif run:
            # set study dir
            study_dir = average_dataset_study(options["sessionsfolder"], outgroupname)

            # create folder
            if not os.path.exists(study_dir):
                if options["run"] == "run":
                    os.makedirs(study_dir)
                else:
                    log.detail(f"test, not created: {study_dir}")

            # link sessions
            for session in sessions:
                # prepare folders
                session_name = session["id"] + options["hcp_suffix"]
                source_dir = os.path.join(session["hcp"], session_name)
                target_dir = os.path.join(study_dir, session_name)

                # link
                if options["run"] == "run":
                    # a link left dangling, e.g. by a study that was moved, is
                    # replaced
                    if os.path.islink(target_dir) and not os.path.exists(target_dir):
                        os.unlink(target_dir)
                    if not gc.link_or_copy(
                        source_dir,
                        target_dir,
                        name=f"session {session['id']}",
                        symlink=True,
                        _log=log,
                    ):
                        run = False
                elif not os.path.exists(target_dir):
                    log.detail(f"test, not linked: {target_dir}")

        # build the command
        if run:
            # hcp_surface_atlas_dir
            surface_atlas = ""
            if options["hcp_surface_atlas_dir"] is None:
                surface_atlas = os.path.join(hcp["hcp_Templates"], "standard_mesh_atlases")
            else:
                surface_atlas = options["hcp_surface_atlas_dir"]

            # hcp_grayordinates_dir
            grayordinates = ""
            if options["hcp_grayordinates_dir"] is None:
                grayordinates = os.path.join(hcp["hcp_Templates"], "91282_Greyordinates")
            else:
                grayordinates = options["hcp_grayordinates_dir"]

            # hcp_freesurfer_labels
            freesurferlabels = ""
            if options["hcp_freesurfer_labels"] is None:
                freesurferlabels = os.path.join(hcp["hcp_Config"], "FreeSurferAllLut.txt")
            else:
                freesurferlabels = options["hcp_freesurfer_labels"]

            comm = (
                '%(script)s \
                --study-folder="%(study_dir)s" \
                --subject-list="%(subject_list)s" \
                --group-average-name="%(group_average_name)s" \
                --surface-atlas-dir="%(surface_atlas)s" \
                --grayordinates-space-dir="%(grayordinates)s" \
                --high-res-mesh="%(highresmesh)s" \
                --low-res-meshes="%(lowresmeshes)s" \
                --freesurfer-labels="%(freesurferlabels)s" \
                --sigma="%(sigma)s" \
                --reg-name="%(regname)s" \
                --videen-maps="%(videenmaps)s" \
                --greyscale-maps="%(greyscalemaps)s" \
                --distortion-maps="%(distortionmaps)s" \
                --gradient-maps="%(gradientmaps)s" \
                --std-maps="%(stdmaps)s" \
                --multi-maps="%(multimaps)s"'
                % {
                    "script": os.path.join(
                        hcp["hcp_base"],
                        "Supplemental",
                        "MakeAverageDataset",
                        "MakeAverageDataset.sh",
                    ),
                    "study_dir": study_dir,
                    "subject_list": subject_list,
                    "group_average_name": outgroupname,
                    "surface_atlas": surface_atlas,
                    "grayordinates": grayordinates,
                    "highresmesh": options["hcp_hiresmesh"],
                    "lowresmeshes": options["hcp_lowresmeshes"].replace(",", "@"),
                    "freesurferlabels": freesurferlabels,
                    "sigma": options["hcp_pregradient_smoothing"],
                    "regname": options["hcp_mad_regname"],
                    "videenmaps": options["hcp_mad_videen_maps"].replace(",", "@"),
                    "greyscalemaps": options["hcp_mad_greyscale_maps"].replace(
                        ",", "@"
                    ),
                    "distortionmaps": options["hcp_mad_distortion_maps"].replace(
                        ",", "@"
                    ),
                    "gradientmaps": options["hcp_mad_gradient_maps"].replace(",", "@"),
                    "stdmaps": options["hcp_mad_std_maps"].replace(",", "@"),
                    "multimaps": options["hcp_mad_multi_maps"].replace(",", "@"),
                }
            )

            # -- Report command
            log.pipeline_command(comm, marker="                --")

            # -- Run
            if options["run"] == "run":
                endlog, report, failed = pc.run_external_for_file(
                    None,
                    comm,
                    "Running HCP make average dataset",
                    overwrite=True,
                    thread=outgroupname,
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    full_test=None,
                    shell=True,
                    _log=log,
                )

            # just checking, there is no test file to check against
            else:
                log.step("HCP make average dataset can be run")
                report = "HCP make average dataset can be run"
                failed = 0

        else:
            log.step("Session cannot be processed.")
            report = "HCP make average dataset cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        failed = 1
    except Exception:
        log.unknown_error()
        failed = 1

    log.close(pipeline="HCP make average dataset preprocessing")

    return log.result((sessionid_list, report, failed))


def average_dataset_study(sessionsfolder: str, group: str) -> str:
    """
    The study folder hcp_make_average_dataset runs MakeAverageDataset.sh in,
    its --study-folder, with the group's sessions linked into it:
    <sessionsfolder>/average_dataset/<group>.

    The script writes the average dataset into the <group> folder of this one,
    see `average_dataset_folder`.
    """
    return os.path.join(sessionsfolder, "average_dataset", group)


def average_dataset_folder(sessionsfolder: str, group: str) -> str:
    """
    The average dataset hcp_make_average_dataset makes of a group, the folder
    that holds its MNINonLinear:
    <sessionsfolder>/average_dataset/<group>/<group>.
    """
    return os.path.join(average_dataset_study(sessionsfolder, group), group)
