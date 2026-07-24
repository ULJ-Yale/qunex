#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_nhp_freesurfer.py``

The non-human primate HCP FreeSurfer pipeline.
"""

import glob
import os
import os.path
import shutil

import qx_utilities.general.exceptions as ge
import qx_utilities.general.snapshots as gs
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    _get_postfreesurfer_snapshot_paths,
    do_hcp_options_check,
)


def hcp_nhp_freesurfer(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_nhp_freesurfer [... processing options]``

    Runs the NHP (non-human primate) variant of the FS step of the HCP
    Pipeline (FreeSurferPipelineNHP.sh).

    Warning:
        The code expects the previous step (hcp_pre_freesurfer) to have run
        successfully and checks for presence of a few key files and folders. Due
        to the number of inputs that it requires, it does not make a full check
        for all of them!

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

        --hcp_processing_mode (str, default 'HCPStyleData'):
            Controls whether the HCP acquisition and processing guidelines
            should be treated as requirements ('HCPStyleData') or if additional
            processing functionality is allowed ('LegacyStyleData'). In this case
            running processing w/o a T2w image.

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

        --hcp_species (str, default ''):
            Species type (required). Controls species-specific processing
            parameters. One of: Human, Chimp, MacaqueCyno, MacaqueRhesus,
            MacaqueSnow, NightMonkey, Marmoset.

        --hcp_scale_factor (str, default ''):
            Brain scale factor for NHP processing (required). Controls volume
            rescaling for FreeSurfer and some derived parameters. The
            recommended value is the BrainScaleFactor defined in the species'
            SetUp script.

        --hcp_runmode (str, default ''):
            Specify from which step to resume the processing instead of
            starting from the beginning. Value must be one of: Default,
            FSinit, FSbrainseg, FSsurfinit, FShires, FSFinish (default:
            Default).

        --hcp_fs_seed (str, default ''):
            Recon-all seed value. If not specified, none will be used.

        --hcp_fs_edits (str, default 'FALSE'):
            Indicates whether manual edits are to be applied to the FreeSurfer
            outputs. If set to 'TRUE', the user needs to either place the edited
            files in <sessions folder>/inbox/FS_edits and prepend '<session id>_'
            to identify them, or place them in the standard FreeSurfer location
            themselves. The 'existing_session' parameter will be set to TRUE,
            and 'extra_reconall' parameters will be set as well to only run the
            necessary steps to incorporate the edits, depending on the edits
            present and/or specified. This option can be used for edits to
            control.dat, aseg.mgz, wm.mgz, and brainmask.mgz files. Accepted
            values are 'FALSE', 'TRUE', or a comma-separated list of edits to
            apply: 'control', 'aseg', 'wm', 'brainmask'. If edits are not
            specified explicitly, they will be determined based on the files
            found in the FS_edits folder.

        --hcp_fs_existing_session (str, default 'FALSE'):
            Indicates that the command is to be run on top of an already
            existing analysis/subject. This excludes the `-i` flag from the
            invocation of recon-all. If set, the user needs to specify which
            recon-all stages to run using the --hcp_fs_extra_reconall
            parameter. Accepted values are 'TRUE' and 'FALSE'.

        --hcp_fs_extra_reconall (str, default ''):
            A string with extra parameters to pass to FreeSurfer recon-all.
            The extra parameters are to be listed in a pipe ('|') separated
            string. Parameters and their values need to be listed
            separately. E.g. to pass `-norm3diters 3` to reconall, the
            string has to be: "-norm3diters|3".

        --hcp_fs_flair (str, default 'FALSE'):
            If set to 'TRUE' indicates that recon-all is to be run with the
            -FLAIR/-FLAIRpial options (rather than the -T2/-T2pial options).
            The FLAIR input image itself should be provided as a regular T2w
            image.

        --hcp_fs_t1wdivflair (str, default 'FALSE'):
            If set to 'TRUE' indicates that recon-all is to be run with the
            -T1wDivFLAIR/-T1wDivFLAIRpial options (rather than the -T2/-T2pial
            options). The T1w/FLAIR input image itself should be provided as a
            regular T2w image. NOTE: This is experimental.

        --hcp_conf2hires (str, 'TRUE'):
            Whether to use the conf2hires flag in recon-all. If set to 'TRUE',
            the flag will be used, if set to 'FALSE' it will not be used.

        --hcp_t2 (str, default 't2'):
            'NONE' if no T2w image is available and the preprocessing should be
            run without them, anything else otherwise. 'NONE' is only
            valid if 'LegacyStyleData' processing mode was specified.

        --hcp_expert_file (str, default ''):
            Path to the read-in expert options file for FreeSurfer if one is
            prepared and should be used empty otherwise.

    Output files:
        The results of this step will be present in the above mentioned T1w
        folder as well as MNINonLinear folder in the sessions's root hcp
        folder.

    Notes:
        Runs the NHP variant of the FreeSurfer (FreeSurferPipelineNHP.sh) step
        of the HCP Pipelines. It takes the T1w and T2w images processed in the
        previous (hcp_pre_freesurfer) step, segments T1w image by brain matter
        and CSF, reconstructs the cortical surface of the brain and assigns
        structure labels for both subcortical and cortical structures, using
        species-specific templates and parameters selected via the
        ``hcp_species`` and ``hcp_scale_factor`` parameters.

        hcp_nhp_freesurfer parameter mapping:

            ============================ =======================
            QuNex parameter              HCPpipelines parameter
            ============================ =======================
            ``hcp_species``              ``species``
            ``hcp_scale_factor``         ``scale-factor``
            ``hcp_runmode``              ``runmode``
            ``hcp_fs_seed``              ``seed``
            ``hcp_processing_mode``      ``processing-mode``
            ``hcp_fs_existing_session``  ``existing-subject``
            ``hcp_fs_extra_reconall``    ``extra-reconall-arg``
            ``hcp_conf2hires``           ``conf2hires``
            ``hcp_fs_flair``             ``flair``
            ``hcp_fs_t1wdivflair``       ``t1wdivflair``
            ============================ =======================

        Running FreeSurfer again after PostFreeSurfer:

            If FreeSurfer has to be run again after PostFreeSurfer, the files
            generated during PostFreeSurfer need to be removed to prevent
            any conflicts. For this reason, when PostFreeSurfer is run, QuNex
            records the list of files generated during PostFreeSurfer and backs
            up files known to be modified by PostFreeSurfer. When FreeSurfer
            is run again, files generated by PostFreeSurfer are removed and the
            backed up files are restored.

        Running with FreeSurfer edits:

            Sometimes, after visual inspection of the FreeSurfer outputs, manual
            edits are needed to correct for misclassified regions. If such edits
            have been made, they can be applied during the FreeSurfer step as
            described for ``hcp_freesurfer``, using the ``hcp_fs_edits``,
            ``hcp_fs_existing_session`` and ``hcp_fs_extra_reconall`` parameters.

    Examples:
        Example run from the base study folder with test flag::

            qunex hcp_nhp_freesurfer \\
                --batchfile="processing/batch.txt" \\
                --sessionsfolder="sessions" \\
                --parsessions="10" \\
                --species="MacaqueRhesus" \\
                --hcp_scale_factor="1.25" \\
                --overwrite="no" \\
                --test

        Example run with absolute paths with scheduler::

            qunex hcp_nhp_freesurfer \\
                --batchfile="<path_to_study_folder>/processing/batch.hcp.txt" \\
                --sessionsfolder="<path_to_study_folder>/sessions" \\
                --parsessions="4" \\
                --species="Marmoset" \\
                --hcp_scale_factor="0.2" \\
                --overwrite="yes" \\
                --scheduler="SLURM,time=24:00:00,cpus-per-task=2,mem-per-cpu=1250,partition=day"
    """

    log = SessionLog(sinfo, options, "HCP NHP FreeSurfer Pipeline", tail="\n", lead="\n\n")

    run = True
    status = True
    report = "Error"
    failed = 0

    try:
        pc.do_options_check(options, sinfo, "hcp_nhp_freesurfer")
        do_hcp_options_check(options, "hcp_nhp_freesurfer")
        hcp = get_hcp_paths(sinfo, options)

        # --- run checks
        if "hcp" not in sinfo:
            log.raw("\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"]))
            run = False

        # -> NHP mandatory parameters
        if not options["hcp_species"]:
            log.error("hcp_species is required for hcp_nhp_freesurfer! One of: Human, Chimp, MacaqueCyno, MacaqueRhesus, MacaqueSnow, NightMonkey, Marmoset.")
            run = False

        if not options["hcp_scale_factor"]:
            log.error("hcp_scale_factor is required for hcp_nhp_freesurfer!")
            run = False

        # -> Pre FS results
        if os.path.exists(
            os.path.join(hcp["T1w_folder"], "T1w_acpc_dc_restore_brain.nii.gz")
        ):
            log.step("PreFS results present.")
        else:
            log.error("Could not find PreFS processing results.")
            run = False

        # -> T2w image
        if hcp["T2w"] in ["", "NONE"]:
            t2w = "NONE"
        else:
            t2w = os.path.join(hcp["T1w_folder"], "T2w_acpc_dc_restore.nii.gz")

        if t2w == "NONE" and options["hcp_processing_mode"] == "HCPStyleData":
            log.error("The requested HCP processing mode is 'HCPStyleData', however, no T2w image was specified!\n            Consider using LegacyStyleData processing mode.")
            run = False

        # ---> Building the command string
        comm = (
            os.path.join(hcp["hcp_base"], "FreeSurfer", "FreeSurferPipelineNHP.sh")
            + " "
        )

        # do we have edits specified?
        if options["hcp_fs_edits"] and options["hcp_fs_edits"].upper() not in [
            "",
            "FALSE",
            "NO",
            "NONE",
        ]:
            extra = [
                e.strip()
                for e in options["hcp_fs_edits"].lower().split(",")
                if e.strip() not in ["aseg", "wm", "brainmask", "yes", "true"]
            ]
            if extra:
                log.raw("\n---> ERROR: Invalid edits specified in hcp_fs_edits: '%s' ['%s']"
                    % (",".join(extra), options["hcp_fs_edits"]))
                run = False

            else:
                edited = [
                    e
                    for e in ["aseg", "wm", "brainmask"]
                    if e in options["hcp_fs_edits"].lower().split(",")
                ]
                # -- map files
                log.step("hcp_fs_edits is set to TRUE, looking for edits files ...")
                editsfolder = os.path.join(
                    options["sessionsfolder"], "inbox", "FS_edits"
                )
                editfiles = glob.glob(os.path.join(editsfolder, sinfo["id"] + "_*.mgz"))
                controlfile = os.path.join(editsfolder, sinfo["id"] + "_control.dat")
                if editfiles or os.path.exists(controlfile):
                    copyfiles = []
                    for efile in editfiles:
                        fname = os.path.basename(efile).split("_", 1)[1]
                        edited.append(fname.replace(".mgz", ""))
                        destfile = os.path.join(hcp["FS_folder"], "mri", fname)
                        copyfiles.append((efile, destfile))
                    if os.path.exists(controlfile):
                        destfile = os.path.join(hcp["FS_folder"], "tmp", "control.dat")
                        copyfiles.append((controlfile, destfile))
                        edited.append("control")
                    for efile, destfile in copyfiles:
                        if os.path.exists(destfile):
                            log.raw("\n     ... replacing: %s " % (fname))
                        else:
                            log.raw("\n     ... adding: %s " % (fname))
                        shutil.copy2(efile, destfile)
                else:
                    log.raw("\n     ... no edits files found in %s!" % (editsfolder))

                # -- set extra parameters
                options["hcp_fs_existing_session"] = True
                if "control" in edited:
                    add_extra = ["-autorecon2-cp", "-autorecon3"]
                elif "wm" in edited:
                    add_extra = ["-autorecon2-wm", "-autorecon3"]
                elif "aseg" in edited:
                    add_extra = ["-autorecon2-noaseg", "-autorecon3"]
                elif "brainmask" in edited:
                    add_extra = ["-autorecon-pial"]
                else:
                    log.error("No edits specified and no edited files found!")
                    log.raw("\n            If you are processing edits to control points, wm, aseg, or brainmask, please provide the appropriate edit files or list them explicitly in hcp_fs_edits.")
                    log.raw("\n            For other edits, please set hcp_fs_edits to FALSE, and use hcp_fs_existing_session and hcp_fs_extra_reconall parameters.")
                    run = False
                    add_extra = []

                if hcp["T2w"] not in ["", "NONE"]:
                    add_extra.append("-T2pial")

                add_extra = [
                    p for p in add_extra if p not in options["hcp_fs_extra_reconall"]
                ]
                if add_extra:
                    options["hcp_fs_extra_reconall"] = "|".join(
                        add_extra + [options["hcp_fs_extra_reconall"]]
                    )

        # -> Key elements
        elements = [
            ("session-dir", hcp["T1w_folder"]),
            ("subject", sinfo["id"] + options["hcp_suffix"]),
            ("processing-mode", options["hcp_processing_mode"]),
            ("species", options["hcp_species"]),
            ("scale-factor", options["hcp_scale_factor"]),
        ]

        # -> resume from a specific step
        if options["hcp_runmode"]:
            elements.append(("runmode", options["hcp_runmode"]))

        # -> add t1, t1brain and t2 only if options['hcp_fs_existing_session'] is FALSE
        if not options["hcp_fs_existing_session"]:
            elements.append((
                "t1",
                os.path.join(hcp["T1w_folder"], "T1w_acpc_dc_restore.nii.gz"),
            ))
            elements.append((
                "t1brain",
                os.path.join(hcp["T1w_folder"], "T1w_acpc_dc_restore_brain.nii.gz"),
            ))
            elements.append(("t2", t2w))

        # -> Additional, reconall parameters
        if options["hcp_fs_extra_reconall"]:
            for f in options["hcp_fs_extra_reconall"].split("|"):
                elements.append(("extra-reconall-arg", f))

        # -> additional QuNex passed parameters
        if options["hcp_expert_file"]:
            elements.append(("extra-reconall-arg", "-expert"))
            elements.append(("extra-reconall-arg", options["hcp_expert_file"]))

        # seed
        if options["hcp_fs_seed"]:
            elements.append(("seed", options["hcp_fs_seed"]))

        # -> conf2hires flag
        if options["hcp_conf2hires"]:
            elements.append(("conf2hires", options["hcp_conf2hires"]))

        # ---> Pull all together
        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements])

        # ---> Add flags
        for option_name, flag in [
            ("hcp_fs_flair", "--flair"),
            ("hcp_fs_t1wdivflair", "--t1wdivflair"),
            ("hcp_fs_existing_session", "--existing-subject"),
        ]:
            if options[option_name]:
                comm += " %s" % (flag)

        # check if post_fs was already completed
        post_fs_tfile = os.path.join(
            hcp["hcp_nonlin"],
            sinfo["id"]
            + options["hcp_suffix"]
            + ".corrThickness.164k_fs_LR.dscalar.nii",
        )
        postfs_snapshot_paths = _get_postfreesurfer_snapshot_paths(hcp)

        if os.path.exists(post_fs_tfile) and not (
            overwrite or options["hcp_fs_existing_session"]
        ):
            log.error("PostFreeSurfer results already present! Set overwrite to true or hcp_fs_existing_session to true to reprocess FreeSurfer!")
            run = False

        # -- Report command
        if run:
            log.pipeline_command(comm)

        # -- Run
        if run:
            if options["run"] == "run":
                # ---> clean up only if hcp_fs_existing_session is not set to True
                if overwrite and not options["hcp_fs_existing_session"]:
                    if os.path.lexists(hcp["FS_folder"]):
                        log.raw("\n---> removing preexisting FS folder [%s]"
                            % (hcp["FS_folder"]))
                        shutil.rmtree(hcp["FS_folder"], ignore_errors=True)
                    for toremove in [
                        "fsaverage",
                        "lh.EC_average",
                        "rh.EC_average",
                        os.path.join("xfms", "OrigT1w2T1w.nii.gz"),
                    ]:
                        rmtarget = os.path.join(hcp["T1w_folder"], toremove)
                        try:
                            if os.path.islink(rmtarget) or os.path.isfile(rmtarget):
                                os.remove(rmtarget)
                            elif os.path.isdir(rmtarget):
                                shutil.rmtree(rmtarget)
                        except Exception:
                            log.raw("\n---> WARNING: Could not remove preexisting file/folder: %s! Please check your data!"
                                % (rmtarget))
                            status = False

                if os.path.exists(post_fs_tfile):
                    log.warning("PostFreeSurfer results already present!")
                    # -> cleanup postfs
                    log.raw("\n     Found PostFreeSurfer results file: %s" % (
                        post_fs_tfile
                    ))
                    log.raw("\n     Cleaning up PostFreeSurfer results to allow FreeSurfer reprocessing ...")
                    have_postfs_diff = os.path.exists(postfs_snapshot_paths["diff"])
                    have_postfs_backup = os.path.exists(postfs_snapshot_paths["backup"])

                    if have_postfs_diff and have_postfs_backup:
                        gs.rollback_snapshot(
                            diff=postfs_snapshot_paths["diff"],
                            action="delete",
                            exclude=hcp["snapshots"],
                        )

                        # -> restore backup
                        log.raw("\n     Restoring FreeSurfer backup ...")
                        gs.restore_files(
                            source=postfs_snapshot_paths["backup"],
                            target=hcp["base"],
                            overwrite=True,
                        )
                    elif have_postfs_diff or have_postfs_backup:
                        raise ge.CommandFailed(
                            "hcp_nhp_freesurfer",
                            "PostFreeSurfer rollback metadata is incomplete.",
                            "Expected both postfreesurfer_diff.txt and postfreesurfer_backup in the snapshots folder.",
                            "Please repair the study state before rerunning FreeSurfer after PostFreeSurfer.",
                        )
                    else:
                        raise ge.CommandFailed(
                            "hcp_nhp_freesurfer",
                            "PostFreeSurfer results are present, but rollback metadata is missing.",
                            "Safe FreeSurfer rerun after PostFreeSurfer requires postfreesurfer_diff.txt and postfreesurfer_backup in the snapshots folder.",
                            "Re-run PostFreeSurfer once with current QuNex to seed rollback metadata, or rerun the study from PreFreeSurfer.",
                        )

                # --> record freesurfer_start_snapshot
                log.step("Recording FreeSurfer start snapshot ...")
                gs.record_snapshot(
                    targetfolder=hcp["base"],
                    outfile=os.path.join(hcp["snapshots"], "freesurfer_start.txt"),
                    exclude=hcp["snapshots"],
                )

                if status:
                    endlog, report, failed = log.run_external(
                        None,
                        comm,
                        "Running HCP NHP FS",
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
                    None, None, "HCP NHP FS", overwrite=overwrite
                )
                if passed is None:
                    log.step("HCP NHP FS can be run")
                    report = "HCP NHP FS can be run"
                    failed = 0
        else:
            log.step("Subject cannot be processed.")
            report = "FS cannot be run"
            failed = 1

    except ge.CommandFailed as e:
        log.command_failed(e, "FreeSurfer")
        report = "FS failed"
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.capture(str(errormessage))
        failed = 1
    except Exception:
        log.unknown_error()
        failed = 1

    log.close(pipeline="HCP NHP FS")

    # -- take freesurfer_end_snapshot
    if options["run"] == "run" and failed == 0:
        freesurfer_start_snapshot = os.path.join(
            hcp["snapshots"], "freesurfer_start.txt"
        )
        if os.path.exists(freesurfer_start_snapshot):
            gs.compare_snapshots(
                before=freesurfer_start_snapshot,
                after=os.path.join(hcp["base"]),
                outfile=os.path.join(hcp["snapshots"], "freesurfer_diff.txt"),
                exclude=hcp["snapshots"],
            )
        else:
            log.warning("FreeSurfer start snapshot missing, skipping diff generation.")

    return log.result(report, failed)
