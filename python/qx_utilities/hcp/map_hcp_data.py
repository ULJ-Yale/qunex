#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``map_hcp_data.py``

Mapping of HCP pipeline results into the QuNex file structure.
"""

import glob
import os
import os.path
import pprint
import time
import traceback
from datetime import datetime

import qx_utilities.general.core as gc
import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog
from qx_utilities.hcp.hcp_utils import session_report_header


def map_hcp_data(sinfo, options, overwrite=False, thread=0):
    """
    ``map_hcp_data [... processing options]``

    Map the results of the HCP preprocessing to the QuNex folder structure.

    ..  qx_command:
        type: processing.session


    Description:
        This function maps the results of the HCP preprocessing into the QuNex
        folder structure. The following files are mapped:

        * T1w.nii.gz
            └-> images/structural/T1w.nii.gz

        * aparc+aseg.nii.gz
            └-> images/segmentation/freesurfer/mri/aparc+aseg_t1.nii.gz

            └-> images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz
            (2mm iso downsampled version)

        * fsaverage_LR32k/*
            └-> images/segmentation/hcp/fsaverage_LR32k

        * BOLD_[N][hcp_nifti_tail].nii.gz
            └-> images/functional/[boldname][N][qx_nifti_tail].nii.gz

        * BOLD_[N][hcp_cifti_tail].dtseries.nii
            └-> images/functional/[boldname][N][qx_cifti_tail].dtseries.nii

        * Movement_Regressors.txt
            └-> images/functional/movement/[boldname][N]_mov.dat

        See Use section for details.

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

        --hcp_bold_variant (str, default ''):
            Optional variant of HCP BOLD preprocessing. If specified, the
            results will be copied/linked from `Results<hcp_bold_variant>`.

        --hcp_nifti_tail (str, default ''):
            The tail to use for the volume files to map from the HCP file
            structure.

        --hcp_cifti_tail (str, default ''):
            The tail to use for the surface files to map from the HCP file
            structure.

        --bolds (str, default 'all'):
            Which bold images (as they are specified in the batch.txt file) to
            copy over. It can be a single type (e.g. 'task'), a pipe separated
            list (e.g. 'WM|Control|rest') or 'all' to copy all.

        --boldname (str, default 'bold'):
            The prefix for the fMRI files in the images folder.

        --img_suffix (str, default ''):
            Specifies a suffix for 'images' folder to enable support for
            multiple parallel workflows. Empty if not used.

        --qx_nifti_tail (str, default detailed below):
            The tail to use for the mapped volume files in the QuNex file
            structure. If not specified or if set to 'None', the value of
            hcp_nifti_tail will be used.

        --qx_cifti_tail (str, default detailed below):
            The tail to use for the mapped cifti files in the QuNex file
            structure. If not specified or if set to 'None', the value of
            hcp_cifti_tail will be used.

        --bold_variant (str, default ''):
            Optional variant for functional images. If specified, functional
            images will be mapped into `functional<bold_variant>` folder.

        --additional_bolds (str, default ''):
            A comma separated list of additional bolds to map. Use this
            parameter to map HCP results/derivatives that are not part of the
            session.txt file (for example concatenated rest denoised BOLDs
            after runnning hcp_msmall).

    Notes:
        The parameters can be specified in command call or session.txt file. If
        possible, the files are not copied but rather hard links are created to
        save space. If hard links cannot be created, the files are copied.

        Specific attention needs to be paid to the use of `hcp_nifti_tail`,
        `hcp_cifti_tail`, `hcp_suffix`, and `hcp_bold_variant` that relate to
        file location and naming within the HCP folder structure and
        `qx_nifti_tail`, `qx_cifti_tail`, `img_suffix`, and `bold_variant` that
        relate to file and folder naming within the QuNex folder structure.

        `hcp_suffix` parameter enables the use of a parallel HCP minimal
        processing stream. To enable the same separation in the QuNex folder
        structure, `img_suffix` parameter has to be set. In this case HCP data
        will be mapped to `<sessionsfolder>/<session id>/images<img_suffix>`
        folder instead of the default `<sessionsfolder>/<session id>/images`
        folder.

        Similarly, if separate variants of bold image processing were run, and
        the results were stored in `MNINonLinear/Results<hcp_bold_variant>`,
        the `hcp_bold_variant` parameter needs to be set to map the data from
        the correct location. `bold_variant` parameter on the other hand
        enables continued parallel processing of bold data in the QuNex folder
        structure by mapping bold data to `functional<bold_variant>` folder
        instead of the default `functional` folder.

        Based on HCP minimal preprocessing choices, both CIFTI and NIfTI volume
        files can be marked using different tails. E.g. CIFT files are marked
        with an `_Atlas` tail, NIfTI files are marked with `_hp2000_clean` tail
        after employing ICAFix procedure. When mapping the data, it is
        important that the correct files are mapped. The correct tails for
        NIfTI volume, and CIFTI files are specified using the `hcp_nifti_tail`
        and `hcp_cifti_tail` parameters. When the data is mapped into QuNex
        folder structure the tails to be used for NIfTI and CIFTI data are
        specified with `qx_nifti_tail` and `qx_cifti_tail` parameters,
        respectively. If the `qx_*_tail` parameters are not provided
        explicitly, the values specified in the `hcp_*_tail` parameters will be
        used.

        Use:
            map_hcp_data maps the results of the HCP preprocessing (in
            MNINonLinear) to the `<sessionsfolder>/<session
            id>/images<img_suffix>` folder structure. Specifically, it copies
            the files and folders:

            * T1w.nii.gz
                └-> images/structural/T1w.nii.gz

            * aparc+aseg.nii.gz
                └-> images/segmentation/freesurfer/mri/aparc+aseg_t1.nii.gz

                └-> images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz
                (2mm iso downsampled version)

            * fsaverage_LR32k/*
                └-> images/segmentation/hcp/fsaverage_LR32k

            * BOLD_[N][hcp_nifti_tail].nii.gz
                └-> images/functional/[boldname][N][qx_nifti_tail].nii.gz

            * BOLD_[N][hcp_cifti_tail].dtseries.nii
                └-> images/functional/[boldname][N][qx_cifti_tail].dtseries.nii

            * Movement_Regressors.txt
                └-> images/functional/movement/[boldname][N]_mov.dat

    Examples:

        A basic mapping example::

            qunex map_hcp_data \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --hcp_cifti_tail=_Atlas \\
                --bolds=all

        Also map concatenated bolds and rest bolds from hcp_msmall::

            qunex map_hcp_data \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --hcp_cifti_tail=_Atlas \\
                --additional_bolds=fMRI_CONCAT_ALL

        Run using absolute paths with scheduler::

            qunex map_hcp_data \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --parsessions="4" \\
                --hcp_cifti_tail="_Atlas" \\
                --overwrite="yes" \\
                --scheduler="SLURM,time=24:00:00,cpus-per-task=2,mem-per-cpu=1250,partition=day"
    """

    log = ReportLog()
    log.raw(session_report_header(sinfo))
    log.info("Mapping HCP data ... \n")
    log.info(f"   The command will map the results of the HCP preprocessing from sessions's hcp\n   to sessions's images folder. It will map the T1 structural image, aparc+aseg \n   segmentation in both high resolution as well as one downsampled to the \n   resolution of BOLD images. It will map the 32k surface mapping data, BOLD \n   data in volume and cifti representation, and movement correction parameters. \n\n   Please note: when mapping the BOLD data, two parameters are key: \n\n   --bolds parameter defines which BOLD files are mapped based on their\n     specification in batch.txt file. Please see documentation for formatting. \n        If the parameter is not specified the default value is 'all' and all BOLD\n        files will be mapped. \n\n   --hcp_nifti_tail and --hcp_cifti_tail specifiy which kind of the nifti and cifti files will be copied over. \n     The tail is added after the boldname[N] start. If the parameters are not specified \n     explicitly the default is ''.\n\n   Based on settings:\n\n    * {', '.join(options['bolds'].split('|'))} BOLD files will be copied\n    * '{options['hcp_nifti_tail']}' nifti tail will be used\n    * '{options['hcp_cifti_tail']}' cifti tail will be used.")
    if any([options["hcp_suffix"], options["img_suffix"]]):
        log.info(f"   Based on --hcp_suffix and --img_suffix parameters, the files will be mapped from hcp/{sinfo['id']}{options['hcp_suffix']}/MNINonLinear to 'images{options['img_suffix']}' folder!")
    if any([options["hcp_bold_variant"], options["bold_variant"]]):
        log.info(f"   Based on --hcp_bold_variant and --bold_variant parameters, the files will be mapped from MNINonLinear/Results{options['hcp_bold_variant']} to 'images{options['img_suffix']}/functional{options['bold_variant']} folder!")
    log.raw("\n\n........................................................")

    # --- sanity checks
    if "sessionsfolder" not in options:
        log.error("sessionsfolder not specified in options, cannot map HCP data!")
        rstatus = f"Mapping {sinfo['id']} failed, check your input parameters!"
        failed = 1
        return log.result(rstatus, failed, sinfo["id"])

    session_path = os.path.join(options["sessionsfolder"], sinfo["id"])
    if not os.path.exists(session_path):
        log.error(f"session {sinfo['id']} does not exists at {session_path}!")
        rstatus = f"Mapping {sinfo['id']} failed, check your input parameters and study folder structure!"
        failed = 1
        return log.result(rstatus, failed, sinfo["session"])

    # --- file/dir structure
    f = pc.get_file_names(sinfo, options)
    d = pc.get_session_folders(sinfo, options)

    if "hcp" not in d:
        log.error(f"something went wrong, mapping was unable to get the HCP folder for session {sinfo['id']}!")
        rstatus = f"Mapping {sinfo['id']} failed, check your input parameters and data!"
        failed = 1

        log.raw("\n\nsession information:\n")
        log.raw(pprint.pformat(sinfo))

        log.raw("\n\ndirectory structure:\n")
        log.raw(pprint.pformat(d))

        return log.result(rstatus, failed, sinfo["session"])

    if not os.path.exists(d["hcp"]):
        log.error(f"HCP folder for session {sinfo['id']} does not exists at {d['hcp']}!")
        rstatus = f"Mapping {sinfo['id']} failed, check your input parameters and study folder structure!"
        failed = 1
        return log.result(rstatus, failed, sinfo["session"])

    #    MNINonLinear/Results/<boldname>/<boldname>.nii.gz -- volume
    #    MNINonLinear/Results/<boldname>/<boldname>_Atlas.dtseries.nii -- cifti
    #    MNINonLinear/Results/<boldname>/Movement_Regressors.txt -- movement
    #    MNINonLinear/T1w.nii.gz -- atlas T1 hires
    #    MNINonLinear/aparc+aseg.nii.gz -- FS hires segmentation

    # ------------------------------------------------------------------------------------------------------------
    #                                                                                      map T1 and segmentation
    report = {}
    failed = 0

    if "hcp" not in d or "s_images" not in d:
        log.error(f"found issues with session {sinfo['id']}\n...................................\n{traceback.format_exc()}...................................\n")
        failed += 1
        rstatus = f"Mapping {sinfo['id']} failed, check your batch file and session processing!"
    else:
        log.raw("\n\nSource folder: " + d["hcp"])
        log.info("Target folder: " + d["s_images"])

        log.raw("\n\nStructural data: ...")
        status = True

        if os.path.exists(f["t1"]) and not overwrite:
            log.detail("T1 ready")
            report["T1"] = "present"
        else:
            status = log.link_or_copy(
                os.path.join(d["hcp"], "MNINonLinear", "T1w.nii.gz"),
                f["t1"],
                status,
                "T1")
            report["T1"] = "copied"

        if os.path.exists(f["fs_aparc_t1"]) and not overwrite:
            log.detail("highres aseg+aparc ready")
            report["hires aseg+aparc"] = "present"
        else:
            status = log.link_or_copy(
                os.path.join(d["hcp"], "MNINonLinear", "aparc+aseg.nii.gz"),
                f["fs_aparc_t1"],
                status,
                "highres aseg+aparc")
            report["hires aseg+aparc"] = "copied"

        if os.path.exists(f["fs_aparc_bold"]) and not overwrite:
            log.detail("lowres aseg+aparc ready")
            report["lores aseg+aparc"] = "present"
        else:
            if os.path.exists(f["fs_aparc_bold"]):
                os.remove(f["fs_aparc_bold"])
            if os.path.exists(
                os.path.join(d["hcp"], "MNINonLinear", "T1w_restore.2.nii.gz")
            ) and os.path.exists(f["fs_aparc_t1"]):
                # prepare logtags
                if options["logtag"] != "":
                    options["logtag"] += "_"
                logtags = options["logtag"] + "%s-flirt_%s" % (
                    options["command_ran"],
                    sinfo["id"],
                )

                endlog, _, failedcom = pc.run_external_for_file(
                    f["fs_aparc_bold"],
                    f"flirt -interp nearestneighbour -ref {os.path.join(d['hcp'], 'MNINonLinear', 'T1w_restore.2.nii.gz')} -in {f['fs_aparc_t1']} -out {f['fs_aparc_bold']} -applyisoxfm {options['hcp_bold_res']}",
                    " ... resampling t1 cortical segmentation (%s) to bold space (%s)"
                    % (
                        os.path.basename(f["fs_aparc_t1"]),
                        os.path.basename(f["fs_aparc_bold"]),
                    ),
                    log,
                    overwrite=overwrite,
                    remove=options["log"] == "remove",
                    logfolder=options["comlogs"],
                    logtags=logtags,
                    shell=True,
                )
                if failedcom:
                    report["lores aseg+aparc"] = "failed"
                    failed += 1
                else:
                    report["lores aseg+aparc"] = "generated"
            else:
                log.error("could not generate downsampled aseg+aparc, files missing!", depth=1)
                report["lores aseg+aparc"] = "failed"
                status = False
                failed += 1

        report["surface"] = "ok"
        if os.path.exists(os.path.join(d["hcp"], "MNINonLinear", "fsaverage_LR32k")):
            log.detail("processing surface files")
            sfiles = glob.glob(
                os.path.join(d["hcp"], "MNINonLinear", "fsaverage_LR32k", "*.*")
            )
            npre, ncp = 0, 0
            sid = ""
            if len(sfiles):
                sid = os.path.basename(sfiles[0]).split(".")[0]
            for sfile in sfiles:
                tfile = os.path.join(
                    d["s_s32k"], ".".join(os.path.basename(sfile).split(".")[1:])
                )
                if os.path.exists(tfile) and not overwrite:
                    npre += 1
                else:
                    if ".spec" in tfile:
                        file = open(sfile, "r")
                        s = file.read()
                        s = s.replace(sid + ".", "")
                        tf = open(tfile, "w")
                        print(s, file=tf)
                        tf.close()
                        log.info(f"     -> updated .spec file [{sid}]")
                        ncp += 1
                        continue
                    if gc.link_or_copy(sfile, tfile):
                        ncp += 1
                    else:
                        log.info(f"     -> ERROR: could not map or copy {sfile}")
                        report["surface"] = "error"
                        failed += 1
            if npre:
                log.info(f"     -> {npre} files already copied")
            if ncp:
                log.info(f"     -> copied {ncp} surface files")
        else:
            log.error(f"missing folder: {os.path.join(d['hcp'], 'MNINonLinear', 'fsaverage_LR32k')}!", depth=1)
            status = False
            report["surface"] = "error"
            failed += 1

        # ------------------------------------------------------------------------------------------------------------
        #                                                                                          map functional data
        log.raw(f"\n\nFunctional data: \n ... mapping {', '.join(options['bolds'].split('|'))} BOLD files\n ... mapping '{options['hcp_nifti_tail']}' hcp nifti tail to '{options['qx_nifti_tail']}' qx nifti tail\n ... mapping '{options['hcp_cifti_tail']}' hcp cifti tail to '{options['qx_cifti_tail']}' qx cifti tail\n")

        report["boldok"] = 0
        report["boldfail"] = 0
        report["boldskipped"] = 0

        bolds, skipped, report["boldskipped"] = log.use_or_skip_bold(sinfo, options)

        # add additional BOLDS
        if options["additional_bolds"] is not None:
            log.raw(f"\n\nAdditional BOLD images to map: {options['additional_bolds']}\n")
            additional_bolds = options["additional_bolds"].split(",")
            boldnum = len(bolds) + 1
            for ab in additional_bolds:
                bolds.append({
                    "bold": ab,
                    "filename": ab,
                    "bold_number": boldnum,
                    "name": ab,
                    "task": "additional_bold",
                })
                boldnum += 1

        for boldinfo in bolds:
            log.detail(boldinfo["name"])

            # --- filenames
            if boldinfo["task"] != "additional_bold":
                f.update(pc.get_bold_file_names(sinfo, boldinfo["name"], options))
            else:
                d = pc.get_session_folders(sinfo, options)

                f["bold_qx_vol"] = os.path.join(
                    d["s_bold"],
                    boldinfo["name"] + options["qx_nifti_tail"] + ".nii.gz",
                )
                f["bold_qx_dts"] = os.path.join(
                    d["s_bold"],
                    boldinfo["name"] + options["qx_cifti_tail"] + ".dtseries.nii",
                )
                f["bold_mov"] = os.path.join(
                    d["s_bold_mov"], boldinfo["name"] + "_mov.dat"
                )

            status = True
            hcp_bold_name = ""

            try:
                # -- get source bold name
                if "filename" in boldinfo and options["hcp_filename"] == "userdefined":
                    hcp_bold_name = boldinfo["filename"]
                elif "bold" in boldinfo:
                    hcp_bold_name = boldinfo["bold"]
                else:
                    hcp_bold_name = "%s%d" % (
                        options["hcp_bold_prefix"],
                        boldinfo["bold_number"],
                    )

                # -- check if present and map
                hcp_bold_path = os.path.join(
                    d["hcp"],
                    "MNINonLinear",
                    "Results" + options["hcp_bold_variant"],
                    hcp_bold_name,
                )

                if not os.path.exists(hcp_bold_path):
                    log.error(f"source folder does not exist [{hcp_bold_path}]!", depth=1)
                    status = False

                else:
                    if os.path.exists(f["bold_qx_vol"]) and not overwrite:
                        log.detail("volume image ready")
                    elif boldinfo["task"] == "additional_bold" and not os.path.exists(
                        hcp_bold_path
                    ):
                        log.warning(f"additional bold source does not exist: {f['bold_vol']}", depth=1)
                    else:
                        status = log.link_or_copy(
                            os.path.join(
                                hcp_bold_path,
                                hcp_bold_name + options["hcp_nifti_tail"] + ".nii.gz",
                            ),
                            f["bold_qx_vol"],
                            status,
                            "volume image")

                    if os.path.exists(f["bold_qx_dts"]) and not overwrite:
                        log.detail("grayordinate image ready")
                    else:
                        status = log.link_or_copy(
                            os.path.join(
                                hcp_bold_path,
                                hcp_bold_name
                                + options["hcp_cifti_tail"]
                                + ".dtseries.nii",
                            ),
                            f["bold_qx_dts"],
                            status,
                            "grayordinate image")

                    if os.path.exists(f["bold_mov"]) and not overwrite:
                        log.detail("movement data ready")
                    else:
                        movement_regressors_icafix = f"Movement_Regressors{options['hcp_nifti_tail'].replace('_Atlas', '')}.txt"
                        movement_regressors = None
                        if os.path.exists(
                            os.path.join(hcp_bold_path, movement_regressors_icafix)
                        ):
                            movement_regressors = movement_regressors_icafix
                        else:
                            movement_regressors_volume = "Movement_Regressors.txt"
                            if os.path.exists(
                                os.path.join(hcp_bold_path, movement_regressors_volume)
                            ):
                                movement_regressors = movement_regressors_volume
                                log.warning("using movement regressors from jcp_fmri_volume, hcp_icafix movement regressors not found", depth=1)
                        if movement_regressors:
                            mdata = [
                                line.strip().split()
                                for line in open(
                                    os.path.join(hcp_bold_path, movement_regressors)
                                )
                            ]
                            mfile = open(f["bold_mov"], "w")
                            gc.print_qunex_header(file=mfile)
                            print("#", file=mfile)
                            print(
                                "#frame     dx(mm)     dy(mm)     dz(mm)     X(deg)     Y(deg)     Z(deg)",
                                file=mfile,
                            )
                            c = 0
                            for mline in mdata:
                                if len(mline) >= 6:
                                    c += 1
                                    mline = "%6d   %s" % (c, "   ".join(mline[0:6]))
                                    print(mline.replace(" -", "-"), file=mfile)
                            mfile.close()
                            log.detail("movement data prepared")
                        elif boldinfo["task"] == "additional_bold":
                            log.warning(f"could not prepare movement data for the additional bold, source does not exist: [{os.path.join(hcp_bold_path, movement_regressors_icafix)} or {os.path.join(hcp_bold_path, movement_regressors_volume)}]", depth=1)
                        else:
                            log.error(f"could not prepare movement data, source does not exist: [{os.path.join(hcp_bold_path, movement_regressors_icafix)} or {os.path.join(hcp_bold_path, movement_regressors_volume)}]", depth=1)
                            failed += 1
                            status = False

                if status:
                    log.step("Data ready!\n", depth=1)
                    report["boldok"] += 1
                else:
                    log.error("Data missing, please check source!\n", depth=1)
                    report["boldfail"] += 1
                    failed += 1

            except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
                log.raw(str(errormessage))
                report["boldfail"] += 1
                failed += 1
            except Exception:
                log.unknown_error()
                time.sleep(3)
                failed += 1

        if len(skipped) > 0:
            log.info(f"The following BOLD images were not mapped as they were not specified in\n'--bolds=\"{options['bolds']}\"':\n")
            for boldinfo in skipped:
                if "filename" in boldinfo and options["hcp_filename"] == "userdefined":
                    log.detail(f"{boldinfo['filename']} [task: '{boldinfo['task']}']")
                else:
                    log.detail(f"{boldinfo['name']} [task: '{boldinfo['task']}']")

        log.raw(f"\n\nHCP data mapping completed on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}\n------------------------------------------------------------\n")
        rstatus = (
            "T1: %(T1)s, aseg+aparc hires: %(hires aseg+aparc)s lores: %(lores aseg+aparc)s, surface: %(surface)s, bolds ok: %(boldok)d, bolds failed: %(boldfail)d, bolds skipped: %(boldskipped)d"
            % (report)
        )

    # print r
    return log.result(rstatus, failed, sinfo["id"])
