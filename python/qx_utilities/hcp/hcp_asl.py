#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_asl.py``

The HCP ASL pipeline.
"""

import glob
import os
import os.path

import qx_utilities.general.core as gc
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    check_gdc_coeff_file,
    do_hcp_options_check,
)


def hcp_asl(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_asl [... processing options]``

    Run the HCP ASL Pipeline (https://github.com/physimals/hcp-asl).

    ..  qx_command:
        type: processing.session
        aliases: hcpa

    Warning:
        The code expects the first three HCP preprocessing steps
        (hcp_pre_freesurfer, hcp_freesurfer and hcp_post_freesurfer) to have
        been run and finished successfully.

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
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_gdcoeffs (str, optional):
            Path to a file containing gradient distortion coefficients,
            alternatively a string describing multiple options (see
            below) can be provided.

        --hcp_asl_mtname (str, optional):
            Filename for empirically estimated MT-correction scaling factors.

        --hcp_asl_territories_atlas (str, optional):
            Atlas of vascular territories from Mutsaerts.

        --hcp_asl_territories_labels (str, optional):
            Labels corresponding to territories_atlas.

        --hcp_asl_cores (int, optional):
            Number of cores to use when applying motion correction and
            other potentially multi-core operations.

        --hcp_asl_use_t1 (flag, optional):
            If specified, the T1 estimates from the satrecov model fit
            will be used in perfusion estimation in oxford_asl. The
            flag is not set by default.

        --hcp_asl_interpolation (int, optional):
            Interpolation order for registrations corresponding to
            scipy's map_coordinates function.

        --hcp_asl_nobandingcorr (flag, optional):
            If this option is provided, MT and ST banding corrections
            won't be applied. The flag is not set by default.

        --hcp_asl_stages (str, optional):
            A comma separated list of stages (zero-indexed) to run.
            All prior stages are assumed to have run successfully.

        --hcp_asl_ntis (int, optional):
            Number of TIs.

        --hcp_asl_tis (str, optional):
            Comma separated list of TIs in seconds (e.g., 1.7,2.2,2.7,3.2,3.7).

        --hcp_asl_rpts (str, optional):
            Comma separated repeats for each TI (e.g., 6,6,6,10,15).

        --hcp_asl_bolus (float, optional):
            Labeling/bolus duration in seconds.

        --hcp_asl_slicedt (float, optional):
            Slice time in seconds.

        --hcp_asl_sliceband (int, optional):
            Slices per band (if omitted, derived from sidecar MB factor).

        --hcp_asl_te (float, optional):
            Echo time in milliseconds.

        --hcp_asl_tail_discard_vols (int, optional):
            Volumes immediately before calibrations to discard.

        --hcp_asl_ibf (str, optional):
            Input block format.

        --hcp_regname (str, default 'MSMSulc'):
            Input registration name.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --longitudinal:
            Set this flag if you are running the longitudinal variant of this
            command.

    Output files:
        The results of this step will be present in the ASL folder in the
        sessions's root hcp folder.

    Notes:
        Gradient coefficient file specification:
            `--hcp_gdcoeffs` parameter can be set to either "NONE", a path to a
            specific file to use, or a string that describes, which file to use
            in which case. Each option of the string has to be divided by a
            pipe "|" character and it has to specify, which information to look
            up, a possible value, and a file to use in that case, separated by
            a colon ":" character. The information too look up needs to be
            present in the description of that session. Standard options are
            e.g.::

                institution: Yale
                device: Siemens|Prisma|123456

            Where device is formatted as <manufacturer>|<model>|<serial number>.

            If specifying a string it also has to include a `default`
            option, which will be used in the information was not found. An
            example could be::

                "default:/data/gc1.conf|model:Prisma:/data/gc/Prisma.conf|model:Trio:/data/gc/Trio.conf"

            With the information present above, the file
            `/data/gc/Prisma.conf` would be used.

        Mapping of QuNex parameters onto HCP ASL pipeline parameters:
            Below is a detailed specification about how QuNex parameters are
            mapped onto the HCP ASL parameters.

            ============================== ======================
            QuNex parameter                HCP ASL parameter
            ============================== ======================
            ``hcp_gdcoeffs``               ``grads``
            ``hcp_regname``                ``regname``
            ``hcp_asl_mtname``             ``mtname``
            ``hcp_asl_territories_atlas``  ``territories_atlas``
            ``hcp_asl_territories_labels`` ``territories_labels``
            ``hcp_asl_use_t1``             ``use_t1``
            ``hcp_asl_nobandingcorr``      ``nobandingcorr``
            ``hcp_asl_interpolation``      ``interpolation``
            ``hcp_asl_cores``              ``cores```
            ``hcp_asl_stages``             ``stages``
            ``hcp_asl_ntis``               ``ntis``
            ``hcp_asl_tis``                ``tis``
            ``hcp_asl_rpts``               ``rpts``
            ``hcp_asl_bolus``              ``bolus``
            ``hcp_asl_slicedt``            ``slicedt``
            ``hcp_asl_sliceband``          ``sliceband``
            ``hcp_asl_te``                 ``te``
            ``hcp_asl_tail_discard_vols``  ``tail_discard_vols``
            ``hcp_asl_ibf``                ``ibf``
            ``longitudinal``               ``is-longitudinal``
            ``hcp_longitudinal_template``  ``longitudinal-template``
            ============================== ======================

    Examples:
        Example run::

            qunex hcp_asl \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"

        Run with scheduler, while bumping up the number of used cores::

            qunex hcp_asl \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_asl_cores="8" \\
                --scheduler="SLURM,time=24:00:00,mem-per-cpu=16000"
    """

    log = SessionLog(sinfo, options, "HCP ASL Pipeline")

    run = True
    report = "Error"

    try:
        pc.do_options_check(options, sinfo, "hcp_asl")
        do_hcp_options_check(options, "hcp_asl")
        hcp = get_hcp_paths(sinfo, options)

        if "hcp" not in sinfo:
            log.error(f"There is no hcp info for session {sinfo['id']} in batch.txt")
            run = False

        # extract ASL and SE info
        asl_info = []
        asl_se_info = []
        for k, v in sinfo.items():
            if k.isdigit():
                if v["name"] == "PCASLhr":
                    asl_se_info.append(v)
                elif v["name"] == "mbPCASLhr" or v["name"] == ["mbPCASLhr"]:
                    asl_info = v
                elif v["name"] == "ASL":
                    if "phenc" in v and "SE-FM" in v["phenc"]:
                        asl_se_info.append(v)
                    else:
                        asl_info = v

        # ASL file
        if len(asl_info) == 0:
            log.error("No ASL images found in the batch file!")
            run = False

        asl_file = ""
        if "filename" in asl_info:
            asl_file = os.path.join(
                hcp["ASL_source"], sinfo["id"] + "_" + asl_info["filename"] + ".nii.gz"
            )
        else:
            asl_files = glob.glob(os.path.join(hcp["ASL_source"], "*.nii.gz"))
            if len(asl_files) == 0:
                log.error(f"No .nii.gz files found in {hcp['ASL_source']}!")
                run = False
            else:
                asl_file = asl_files[0]

        # file exists?
        if not os.path.exists(asl_file):
            log.error(f"ASL acquistion data not found [{asl_file}]")
            run = False

        # AP and PA fieldmaps for use in distortion correction
        # asl_se_info is populated through the PCASLhr tag
        fmap_ap_file = None
        fmap_pa_file = None
        if len(asl_se_info) > 0:
            for se in asl_se_info:
                if "phenc" in se:
                    if se["phenc"] in ["AP", "SE-FM-AP"]:
                        if "filename" in se:
                            fmap_ap_file = os.path.join(
                                hcp["ASL_source"],
                                sinfo["id"] + "_" + se["filename"] + ".nii.gz",
                            )
                        else:
                            fmap_ap_file = glob.glob(
                                os.path.join(
                                    hcp["ASL_source"], "*SpinEchoFieldMap_AP*.nii.gz"
                                )
                            )
                            if len(fmap_ap_file) == 0:
                                log.error(f"SE AP file not found in [{hcp['ASL_source']}]")
                                run = False
                            else:
                                fmap_ap_file = fmap_ap_file[0]
                    elif se["phenc"] in ["PA", "SE-FM-PA"]:
                        if "filename" in se:
                            fmap_pa_file = os.path.join(
                                hcp["ASL_source"],
                                sinfo["id"] + "_" + se["filename"] + ".nii.gz",
                            )
                        else:
                            fmap_pa_file = glob.glob(
                                os.path.join(
                                    hcp["ASL_source"], "*SpinEchoFieldMap_PA*.nii.gz"
                                )
                            )
                            if len(fmap_pa_file) == 0:
                                log.error(f"SE PA file not found in [{hcp['ASL_source']}]")
                                run = False
                            else:
                                fmap_pa_file = fmap_pa_file[0]

        # else we need to get the files from se
        elif "se" in asl_info:
            senum = asl_info["se"]
            sefolder = os.path.join(
                hcp["source"], f"SpinEchoFieldMap{senum}{options['fctail']}"
            )
            fmap_ap_file = glob.glob(os.path.join(sefolder, "*AP*.nii.gz"))
            fmap_pa_file = glob.glob(os.path.join(sefolder, "*PA*.nii.gz"))
            if len(fmap_ap_file) == 0 or len(fmap_pa_file) == 0:
                log.error("SE pair not found in the batch file")
                run = False
            else:
                fmap_ap_file = fmap_ap_file[0]
                fmap_pa_file = fmap_pa_file[0]
        else:
            log.error("SE pair not found in the batch file")
            run = False

        # check
        if not fmap_ap_file or not fmap_pa_file:
            log.error("one or more fieldmaps not found, check your input data")
            run = False
        else:
            if not os.path.exists(fmap_ap_file):
                log.error(f"AP fieldmap not found [{fmap_ap_file}]")
                run = False
            if not os.path.exists(fmap_ap_file):
                log.error(f"PA fieldmap not found [{fmap_pa_file}]")
                run = False

        # get library path
        asl_library = os.path.join(os.environ["QUNEXLIBRARY"], "etc/asl")

        # build the command
        if run:
            comm = (
                "%(script)s \
                --subdir %(subdir)s \
                --subid %(subid)s \
                --mbpcasl %(mbpcasl)s \
                --fmap_ap %(fmap_ap)s \
                --fmap_pa %(fmap_pa)s \
                --regname %(regname)s"
                % {
                    "script": "process_hcp_asl",
                    "subdir": os.path.join(sinfo["hcp"], sinfo["id"]),
                    "subid": sinfo["id"] + options["hcp_suffix"],
                    "mbpcasl": asl_file,
                    "fmap_ap": fmap_ap_file,
                    "fmap_pa": fmap_pa_file,
                    "regname": options["hcp_regname"],
                }
            )

            # -- Optional parameters
            # grads
            gdcfile, run = check_gdc_coeff_file(options["hcp_gdcoeffs"], hcp, sinfo, log, run)
            if gdcfile != "NONE":
                comm += f"                --grads {gdcfile}"

            # struct
            # get struct files
            # ACPC-aligned, DC-restored structural image
            t1w_file = os.path.join(
                sinfo["hcp"], sinfo["id"], "T1w", "T1w_acpc_dc_restore.nii.gz"
            )
            if os.path.exists(t1w_file):
                comm += f"                --struct {t1w_file}"

            # sbrain
            t1w_brain_file = os.path.join(
                sinfo["hcp"], sinfo["id"], "T1w", "T1w_acpc_dc_restore_brain.nii.gz"
            )
            if os.path.exists(t1w_brain_file):
                comm += f"                --sbrain {t1w_brain_file}"

            # wmparc
            wmparc_file = os.path.join(
                sinfo["hcp"], sinfo["id"], "T1w", "wmparc.nii.gz"
            )
            if os.path.exists(wmparc_file):
                comm += f"                --wmparc {wmparc_file}"

            # ribbon
            ribbon_file = os.path.join(
                sinfo["hcp"], sinfo["id"], "T1w", "ribbon.nii.gz"
            )
            if os.path.exists(ribbon_file):
                comm += f"                --ribbon {ribbon_file}"

            # use_t1
            if options["hcp_asl_use_t1"]:
                comm += "                --use_t1"

            # mtname
            if options["hcp_asl_mtname"] is None:
                mtname = os.path.join(asl_library, "mt_scaling_factors.txt")
                if os.path.exists(mtname):
                    comm += f"                --mtname {mtname}"
            else:
                comm += f"                --mtname {options['hcp_asl_mtname']}"

            # stages
            if options["hcp_asl_stages"] is not None:
                stages = options["hcp_asl_stages"].replace(",", " ")
                comm += f"                --stages {stages}"

            # cores
            if options["hcp_asl_cores"] is not None:
                comm += f"                --cores {options['hcp_asl_cores']}"

            # interpolation
            if options["hcp_asl_interpolation"] is not None:
                comm += f"                --interpolation {options['hcp_asl_interpolation']}"

            # nobandingcorr
            if options["hcp_asl_nobandingcorr"]:
                comm += "                --nobandingcorr"

            # territories_atlas
            if options["hcp_asl_territories_atlas"] is None:
                territories_atlas = os.path.join(
                    asl_library, "vascular_territories_eroded5_atlas.nii.gz"
                )
                if os.path.exists(territories_atlas):
                    comm += f"                --territories_atlas {territories_atlas}"
            else:
                comm += f"                --territories_atlas {options['hcp_asl_territories_atlas']}"

            # territories_labels
            if options["hcp_asl_territories_labels"] is None:
                territories_labels = os.path.join(
                    asl_library, "vascular_territories_atlas.txt"
                )
                if os.path.exists(territories_labels):
                    comm += f"                --territories_labels {territories_labels}"
            else:
                comm += f"                --territories_labels {options['hcp_asl_territories_labels']}"

            # ntis
            if options["hcp_asl_ntis"] is not None:
                comm += f"                --ntis {options['hcp_asl_ntis']}"

            # tis
            if options["hcp_asl_tis"] is not None:
                hcp_asl_tis = options["hcp_asl_tis"].replace(",", " ")
                comm += f"                --tis {hcp_asl_tis}"

            # rpts
            if options["hcp_asl_rpts"] is not None:
                hcp_asl_rpts = options["hcp_asl_rpts"].replace(",", " ")
                comm += f"                --rpts {hcp_asl_rpts}"

            # bolus
            if options["hcp_asl_bolus"] is not None:
                comm += f"                --bolus {options['hcp_asl_bolus']}"

            # slicedt
            if options["hcp_asl_slicedt"] is not None:
                comm += f"                --slicedt {options['hcp_asl_slicedt']}"

            # sliceband
            if options["hcp_asl_sliceband"] is not None:
                comm += f"                --sliceband {options['hcp_asl_sliceband']}"

            # te
            if options["hcp_asl_te"] is not None:
                comm += f"                --te {options['hcp_asl_te']}"

            # tail_discard_vols
            if options["hcp_asl_tail_discard_vols"] is not None:
                comm += f"                --tail_discard_vols {options['hcp_asl_tail_discard_vols']}"

            # ibf
            if options["hcp_asl_ibf"] is not None:
                comm += f"                --ibf {options['hcp_asl_ibf']}"

            # clean/overwrite
            if overwrite:
                comm += "                --clean"

            # -- Longitudinal parameters
            if options["longitudinal"]:
                studyfolder = gc.deduce_folders(options)["basefolder"]
                if not studyfolder:
                    log.error("cannot deduce the QuNex study folder from provided parameters! Please provide the sessionsfolder or the studyfolder parameter.")
                    run = False
                # replace path
                longitudinal_study_dir = os.path.join(
                    studyfolder, "subjects", sinfo["subject"]
                )

                comm += f'                --longitudinal_template="{options["hcp_longitudinal_template"]}"'
                comm += f'                --longitudinal_study_dir="{longitudinal_study_dir}"'
                comm += "                --is_longitudinal"

            # -- Report command
            if run:
                log.raw("\n\n------------------------------------------------------------\n")
                log.raw("Running HCP Pipelines command via QuNex:\n\n")
                log.raw(comm.replace("                --", "\n    --"))
                log.raw("\n------------------------------------------------------------\n")

        # -- Run
        if run:
            if options["run"] == "run":
                if not options["longitudinal"]:
                    logtags = options["logtag"]
                else:
                    logtags = ["long", options["hcp_longitudinal_template"]]

                _, report, failed = pc.run_external_for_file(
                    None,
                    comm,
                    "Running HCP ASL",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=logtags,
                    full_test=None,
                    shell=True,
                    _log=log,
                )

            # -- just checking
            else:
                passed, report, failed = pc.check_run(
                    None, None, "HCP ASL", overwrite=overwrite, _log=log
                )
                if passed is None:
                    log.step("HCP ASL can be run")
                    report = "HCP ASL can be run"
                    failed = 0

        else:
            log.step("Session cannot be processed.")
            report = "HCP ASL cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        failed = 1
    except Exception as e:
        log.error(f"{e}")
        log.unknown_error()
        failed = 1

    log.close(pipeline="HCP ASL Preprocessing")

    return log.result(report, failed)
