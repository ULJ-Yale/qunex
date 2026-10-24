#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``dwi.py``

This file holds code for running DWI commands. It
consists of functions:

--dwi_f99       Runs FSL F99 command.
--dwi_xtract    Runs FSL XTRACT command.
--dwi_noddi_gpu Runs CUDIMOT NODDI microstructure modelling.

All the functions are part of the processing suite. They should be called
from the command line using `qunex` command. Help is available through:

- ``qunex <command> --help`` for command specific help
There are additional support functions that are not to be used
directly.
"""

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

import os
import shutil
import traceback
from datetime import datetime

import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog


def _hcp_session_folder(sinfo: dict, options: dict) -> str:
    """
    The session's HCP folder, ``<hcp>/<session id><hcp_suffix>``.

    ``<hcp>`` is the folder the session record names, else the ``hcp`` folder
    in the session's own folder -- a session given by its id alone, without a
    batch file, has no record of it.
    """
    hcp = sinfo.get("hcp") or os.path.join(
        options["sessionsfolder"], sinfo["id"], "hcp"
    )
    return os.path.join(hcp, sinfo["id"] + options["hcp_suffix"])


def dwi_f99(sinfo, options, overwrite=False, thread=0):
    """
    ``dwi_f99 [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run FSL's F99 registration for macaque diffusion/structural data.

    ..  qx_command:
        type: processing.session
        aliases: f99

    Description:
        This command runs FSL's F99 script for registering your own diffusion
        or structural data to the F99 atlas. This atlas is used when processing
        macaque data.

    Warning:
        To use this command, successful completion of FSL's dtifit processing
        (dwi_dtifit command in QuNex) is required.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

        --studyfolder (str):
            The path to the study folder. The sessions are in its `sessions`
            folder, unless --sessionsfolder names another one.

        --sessionsfolder (str, default '<studyfolder>/sessions'):
            The path to the folder with the sessions. Set it only when the
            sessions are not in the `sessions` folder of the study. With
            neither --studyfolder nor --sessionsfolder given, the current
            folder is used.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --diffusion_folder (str, default '<sessionsfolder>/<session>/NHP/dMRI'):
            The path to the diffusion folder holding the dtifit results.

    Output files:
        The results of this step will be present in the NHP/F99reg folder of
        each session::

            study
            └─ sessions
               ├─ session1
               |  └─ NHP
               |    └─ F99reg
               └─ session2
                  └─ NHP
                    └─ F99reg

    Examples:
        ::

            qunex dwi_f99 \\
                --studyfolder="/data/macaque_study" \\
                --sessions="hilary,jane" \\
                --overwrite=no \\
                --parsessions=2
    """
    log = ReportLog()

    # get session id
    session = sinfo["id"]

    log.rule()
    log.info(f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]")
    log.action(
        "Running", f"FSL F99 registration [{session}] ...", options["run"], level="info"
    )

    # status variables
    run = True

    try:
        # check base settings
        pc.do_options_check(options, sinfo, "dwi_f99")

        # construct dirs
        dwi_f99_dir = os.path.join(
            os.environ["FSLDIR"], "data/xtract_data/standard/F99"
        )
        nhp_dir = os.path.join(options["sessionsfolder"], session, "NHP")
        f99reg_dir = os.path.join(nhp_dir, "F99reg")
        dtifit_dir = os.path.join(nhp_dir, "dMRI")

        # if diffusion folder specified, use that instead
        if options["diffusion_folder"]:
            dtifit_dir = options["diffusion_folder"]

        # check dtifit results
        dti_file = os.path.join(dtifit_dir, "dti_FA.nii.gz")
        if os.path.exists(dti_file):
            log.step("dtifit results present.")
        else:
            log.error("Could not find dtifit results.")
            report = (sinfo["id"], "Not ready for FSL F99", 1)
            run = False

        # script location
        niu_template_dir = os.environ["NIUTemplateFolder"]
        f99_script = "bash " + os.path.join(niu_template_dir, "nhp", "do_reg_F99.sh")

        # set up the command
        comm = (
            "%(script)s \
                %(input)s \
                %(output)s \
                %(f99dir)s"
            % {
                "script": f99_script,
                "input": dti_file,
                "output": f99reg_dir + "/F99",
                "f99dir": dwi_f99_dir,
            }
        )

        # report command
        log.rule(before=1, after=1)
        log.raw("Running FSL F99 command via QuNex:\n\n")
        log.raw(comm.replace("                ", ""))
        log.rule(after=1)

        # check for existing F99 results
        target_file = os.path.join(f99reg_dir, "F99_anat_to_F99.nii.gz")
        full_test = None

        # run
        if run:
            # run
            if options["run"] == "run":
                # the F99 folder is where the script is run, created here
                # rather than above so that a dry run leaves nothing behind
                os.makedirs(f99reg_dir, exist_ok=True)

                # remove previous file
                if overwrite and os.path.exists(target_file):
                    os.remove(target_file)

                # go to F99 folder before starting work
                comm_pre = "CDIR=`pwd`;cd " + f99reg_dir + ";"

                # go back to current dir after work is done
                comm_post = ";cd $CDIR"

                # add pre and post to command
                comm = comm_pre + comm + comm_post

                # execute
                endlog, _, failed = pc.run_external_for_file(
                    target_file,
                    comm,
                    "Running FSL F99",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"]],
                    full_test=full_test,
                    shell=True,
                    _log=log,
                )

                if failed:
                    log.step(f"FSL F99 processing for session {session} failed")
                    report = (sinfo["id"], "FSL F99 failed", 1)
                else:
                    log.step(f"FSL F99 processing for session {session} completed")
                    report = (sinfo["id"], "FSL F99 completed", 0)

            # just checking
            else:
                passed, _, failed = pc.check_run(
                    target_file, None, "FSL F99 " + session, overwrite=overwrite, _log=log
                )

                if passed is None:
                    log.step("FSL F99 can be run")
                    report = (sinfo["id"], "FSL F99 ready", 0)
                else:
                    log.step(f"FSL F99 processing for session {session} would be skipped")
                    report = (sinfo["id"], "FSL F99 would be skipped", 0)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(f"\n\n\n --- Failed during processing of session {session} with error:\n")
        log.raw(str(errormessage))
        report = (sinfo["id"], "FSL F99 failed", 1)

    except Exception:
        log.info(f" --- Failed during processing of session {session} with error:\n {traceback.format_exc()}\n")
        report = (sinfo["id"], "FSL F99 failed", 1)

    return log.result(report)


def dwi_xtract(sinfo, options, overwrite=False, thread=0):
    """
    ``dwi_xtract [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run FSL's XTRACT (cross-species tractography) command.

    ..  qx_command:
        type: processing.session
        aliases: fslx

    Description:
        The command can be used to automatically extract a set of carefully dissected tracts
        in humans and macaques. It can also be used to define one's own tractography
        protocols where all the user needs to do is to define a set of masks in
        standard space (e.g. MNI152).

    Warning:
        Successful completion of FSL's bedpostx processing (dwi_bedpostx_gpu
        command in QuNex) is required. For macaques FSL F99 registration is also
        required (dwi_f99 command in QuNex).

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

        --studyfolder (str):
            The path to the study folder. The sessions are in its `sessions`
            folder, unless --sessionsfolder names another one.

        --sessionsfolder (str, default '<studyfolder>/sessions'):
            The path to the folder with the sessions. Set it only when the
            sessions are not in the `sessions` folder of the study. With
            neither --studyfolder nor --sessionsfolder given, the current
            folder is used.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --diffusion_folder (str, default detailed below):
            The path to the diffusion folder. The bedpostx folder is derived
            from it by appending '.bedpostX'. By default the diffusion folder
            is set to NHP/dMRI in the session's folder for macaques and to
            hcp/<session>/T1w/Diffusion for humans. If --xtract_bpx is
            provided, it takes precedence over this parameter.

        --species (str, default 'human'):
            Species: human or macaque.

        --nogpu (flag, optional):
            Do not use the GPU version, this flag is not set by default.

        --xtract_list (str, default ''):
            Comma separated list of tract names.

        --xtract_structures (str, default ''):
            Path to structures file (format: <tractName> per line OR format:
            <tractName> [samples=1], 1 means 1000, '#' to skip lines).

        --xtract_protocols (str, default $FSLDIR/data/xtract_data/<species>):
            Protocols folder (all masks in same standard space).

        --xtract_stdwarp (str, default detailed below):
            Standard2diff and Diff2standard transforms. Default for humans is
            set to session's:
            [acpc_dc2standard.nii.gz and standard2acpc_dc.nii.gz],
            for macaques warp fields from F99 registration command (dwi_f99) are
            used by default.

        --xtract_resolution (int, default detailed below):
            Output resolution in mm. Default is the same as in the protocols
            folder unless --native is used.

        --xtract_ptx_options (str, default detailed below):
            Pass extra probtrackx2 options as a text file to override defaults
            (e.g. --steplength=0.2).
            For humans it defaults to '', for macaques it defaults to
            '$QUNEXPATH/python/qx_utilities/templates/nhp/ptx_options'.

        --xtract_mni (flag, optional):
            Run tractography in MNI (diffusion) and not native space. This flag is not set by default.

        --xtract_ref (str, default ''):
            Reference image ("<refimage> <diff2ref> <ref2diff>") for running
            tractography in reference space, Diff2Reference and Reference2Diff
            transforms.

        --xtract_out (str, default detailed below):
            Output folder for XTRACT results. By default it is set to
            NHP/xtract in the session's folder for macaques and to
            hcp/<session>/T1w/Results/Tractography/xtract for humans
            (MNINonLinear instead of T1w with --xtract_mni).

        --xtract_bpx (str, default detailed below):
            Bedpostx folder. By default it is set to NHP/dMRI.bedpostX in the
            session's folder for macaques and to
            hcp/<session>/T1w/Diffusion.bedpostX for humans.

    Output files:
        For macaques, the results of this step will be present in the
        NHP/xtract folder of each session::

            study
            └─ sessions
               ├─ session1
               |  └─ NHP
               |    └─ xtract
               └─ session2
                  └─ NHP
                    └─ xtract

        For humans, they are in the session's
        hcp/<session>/T1w/Results/Tractography/xtract folder
        (MNINonLinear/Results/Tractography/xtract with --xtract_mni).

    Examples:
        ::

            qunex dwi_xtract \\
                --studyfolder="/data/example_study" \\
                --batchfile="/data/example_study/processing/batch.txt" \\
                --species="human" \\
                --overwrite=yes

        ::

            qunex dwi_xtract \\
                --studyfolder="/data/macaque_study" \\
                --sessions="hilary,jane" \\
                --species="macaque" \\
                --overwrite=no \\
                --parsessions=2

    """
    log = ReportLog()

    # get session id
    session = sinfo["id"]

    log.rule()
    log.info(f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]")
    log.action("Running", f"FSL XTRACT [{session}] ...", options["run"], level="info")

    # status variables
    run = True

    try:
        # check base settings
        pc.do_options_check(options, sinfo, "dwi_xtract")

        # get species
        species = "HUMAN"
        if "species" in options and options["species"].upper() == "MACAQUE":
            species = "MACAQUE"

        # set dirs
        if species == "MACAQUE":
            ptx_options = os.path.join(
                os.environ["NIUTemplateFolder"], "nhp", "ptx_options"
            )
            nhp_dir = os.path.join(options["sessionsfolder"], session, "NHP")
            f99reg_dir = os.path.join(nhp_dir, "F99reg")
            bedpostx_dir = os.path.join(nhp_dir, "dMRI.bedpostX")
            output_dir = os.path.join(nhp_dir, "xtract")
        else:
            hcp_dir = _hcp_session_folder(sinfo, options)
            xfms_dir = os.path.join(hcp_dir, "MNINonLinear", "xfms")
            bedpostx_dir = os.path.join(hcp_dir, "T1w", "Diffusion.bedpostX")

            if "xtract_mni" in options:
                output_dir = os.path.join(
                    hcp_dir, "MNINonLinear", "Results", "Tractography", "xtract"
                )
            else:
                output_dir = os.path.join(
                    hcp_dir, "T1w", "Results", "Tractography", "xtract"
                )

        # custom out dir
        if "xtract_out" in options:
            output_dir = options["xtract_out"]

        # if diffusion folder specified, derive bedpostx dir from it
        if options["diffusion_folder"]:
            bedpostx_dir = options["diffusion_folder"] + ".bedpostX"

        # custom bedpostx dir
        if "xtract_bpx" in options:
            bedpostx_dir = options["xtract_bpx"]

        # check bedpostx results
        if species == "MACAQUE":
            bedpostx_file = os.path.join(bedpostx_dir, "mean_fsumsamples.nii.gz")
        else:
            bedpostx_file = os.path.join(bedpostx_dir, "mean_fsumsamples.nii.gz")

        if os.path.exists(bedpostx_file):
            log.step("bedpostx results present.")
        else:
            log.error("Could not find bedpostx results.")
            report = (sinfo["id"], "Not ready for XTRACT", 1)
            run = False

        # script location
        xtract_script = os.path.join(os.environ["FSLDIR"], "bin/xtract")

        # set up the core command
        comm = (
            "%(script)s \
                -bpx %(bedpostx_dir)s \
                -out %(output_dir)s \
                -species %(species)s"
            % {
                "script": xtract_script,
                "bedpostx_dir": bedpostx_dir,
                "output_dir": output_dir,
                "species": species,
            }
        )

        # native?
        if "xtract_mni" not in options:
            comm = comm + " -native"

        # optional parameters
        # nogpu
        if "nogpu" not in options:
            comm = comm + " -gpu"

        # xtract_list
        if "xtract_list" in options:
            comm = comm + " -list %s" % options["xtract_list"]

        # xtract_structures
        if "xtract_structures" in options:
            comm = comm + " -str %s" % options["xtract_structures"]

        # xtract_protocols
        if "xtract_protocols" in options:
            comm = comm + " -p %s" % options["xtract_protocols"]

        # xtract_stdwarp
        if "xtract_stdwarp" in options:
            comm = comm + " -stdwarp %s" % options["xtract_stdwarp"]
        elif species == "MACAQUE":
            std2diff = os.path.join(f99reg_dir, "F99_F99_to_anat_warp.nii.gz")
            diff2std = os.path.join(f99reg_dir, "F99_anat_to_F99_warp.nii.gz")
            comm = comm + " -stdwarp %s %s" % (std2diff, diff2std)
        else:
            std2diff = os.path.join(xfms_dir, "standard2acpc_dc.nii.gz")
            diff2std = os.path.join(xfms_dir, "acpc_dc2standard.nii.gz")
            comm = comm + " -stdwarp %s %s" % (std2diff, diff2std)

        # xtract_resolution
        if "xtract_resolution" in options:
            comm = comm + " -res %s" % options["xtract_resolution"]

        # xtract_ptx_options
        if "xtract_ptx_options" in options:
            comm = comm + " -ptx_options %s" % options["xtract_ptx_options"]
        elif species == "MACAQUE":
            comm = comm + " -ptx_options %s" % ptx_options

        # xtract_resolution
        if "xtract_ref" in options:
            comm = comm + " -ref %s" % options["xtract_ref"]

        # report command
        log.rule(before=1, after=1)
        log.raw("Running FSL XTRACT command via QuNex:\n\n")
        log.raw(comm.replace("                ", ""))
        log.rule(after=1)

        # check for existing XTRACT results
        target_file = os.path.join(output_dir, "tracts", "vof_r", "density.nii.gz")
        full_test = None

        # run
        if run:
            # run
            if options["run"] == "run":
                # create output dir if it does not exist, here rather than
                # above so that a dry run leaves nothing behind
                os.makedirs(output_dir, exist_ok=True)

                # remove previous file
                if overwrite and os.path.exists(target_file):
                    os.remove(target_file)

                # execute
                _, _, failed = pc.run_external_for_file(
                    target_file,
                    comm,
                    "Running FSL XTRACT",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"]],
                    full_test=full_test,
                    shell=True,
                    _log=log,
                )

                log.step(f"Processing details can be found in {os.path.join(output_dir, 'logs')}")

                if failed:
                    log.step(f"FSL XTRACT processing for session {session} failed")
                    report = (sinfo["id"], "FSL XTRACT failed", 1)
                else:
                    log.step(f"FSL XTRACT processing for session {session} completed")
                    report = (sinfo["id"], "FSL XTRACT completed", 0)

            # just checking
            else:
                passed, _, failed = pc.check_run(
                    target_file, None, "FSL XTRACT " + session, overwrite=overwrite, _log=log
                )

                if passed is None:
                    log.step("FSL XTRACT can be run")
                    report = (sinfo["id"], "FSL XTRACT ready", 0)
                else:
                    log.step(f"FSL XTRACT processing for session {session} would be skipped")
                    report = (sinfo["id"], "FSL XTRACT would be skipped", 0)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(f"\n\n\n --- Failed during processing of session {session} with error:\n")
        log.raw(str(errormessage))
        report = (sinfo["id"], "FSL XTRACT failed", 1)

    except Exception:
        log.info(f" --- Failed during processing of session {session} with error:\n {traceback.format_exc()}\n")
        report = (sinfo["id"], "FSL XTRACT failed", 1)

    return log.result(report)


def dwi_noddi_gpu(sinfo, options, overwrite=False, thread=0):
    """
    ``dwi_noddi_gpu [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run CUDIMOT NODDI microstructure modelling using GPU acceleration.

    ..  qx_command:
        type: processing.session
        aliases: noddi

    Description:
        This command runs CUDIMOT's NODDI microstructure modelling. It uses
        precompiled CUDA (GPU) binaries and therefore requires a CUDA capable GPU to
        run. The command can use two different models: Watson and Bingham. The
        Watson model is used by default.

    Warning:
        To use this command, successful completion of hcp_diffusion or
        dwi_legacy_gpu is required.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

        --studyfolder (str):
            The path to the study folder. The sessions are in its `sessions`
            folder, unless --sessionsfolder names another one.

        --sessionsfolder (str, default '<studyfolder>/sessions'):
            The path to the folder with the sessions. Set it only when the
            sessions are not in the `sessions` folder of the study. With
            neither --studyfolder nor --sessionsfolder given, the current
            folder is used.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --noddi_model (str, default 'Watson'):
            Whether to use the Watson or the Bingham NODDI model.

        --diffusion_folder (str, default '<hcp_folder>/T1w/Diffusion'):
            The path to the diffusion folder.

    Output files:
        By default, the results of this step will be present in the HCP Diffusion folder::

            study
            └─ sessions
               ├─ session1
               |  └─ hcp
               |    └─ session1
               |      └─ T1w
               |        └─ Diffusion.NODDI_<model>
               └─ session2
                  └─ hcp
                    └─ session2
                      └─ T1w
                        └─ Diffusion.NODDI_<model>

        If a custom diffusion folder is specified with --diffusion_folder, the
        results will be stored next to it, in a folder named after it:
        <diffusion_folder>.NODDI_<model>.

    Examples:
        ::

            qunex dwi_noddi_gpu \\
                --studyfolder="/data/qx_study" \\
                --batchfile="/data/qx_study/processing/batch.txt"

            qunex dwi_noddi_gpu \\
                --studyfolder="/data/qx_study" \\
                --batchfile="/data/qx_study/processing/batch.txt" \\
                --noddi_model="Bingham" \\
                --overwrite=no \\
                --parsessions=2
    """
    log = ReportLog()

    # get session id
    session = sinfo["id"]

    log.rule()
    log.info(f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]")
    log.action(
        "Running", f"CUDIMOT NODDI modelling [{session}] ...", options["run"], level="info"
    )

    # status variables
    run = True

    try:
        # check base settings
        pc.do_options_check(options, sinfo, "dwi_noddi_gpu")

        # script location
        cudimot_dir = os.environ["CUDIMOT"]

        # model
        if "noddi_model" not in options:
            options["noddi_model"] = "Watson"

        # check validity
        if options["noddi_model"] not in ["Watson", "Bingham"]:
            log.error(f"Invalid NODDI model [{options['noddi_model']}], needs to be Watson or Bingham.")
            report = (sinfo["id"], "Not ready for CUDIMOT NODDI", 1)
            run = False

        cudimot_script = os.path.join(
            cudimot_dir, "bin", f"Pipeline_NODDI_{options['noddi_model']}.sh"
        )

        # session's diffusion dir
        diffusion_dir = os.path.join(_hcp_session_folder(sinfo, options), "T1w", "Diffusion")

        # if diffusion folder specified, use that instead
        if options["diffusion_folder"]:
            diffusion_dir = options["diffusion_folder"]

        # the results, next to the diffusion folder and named after it, as
        # cudimot writes them to <diffusion folder>.NODDI_<model>
        results_folder = diffusion_dir.rstrip("/") + ".NODDI_" + options["noddi_model"]

        # check that diffusion_dir exists
        if not os.path.exists(diffusion_dir):
            log.error(f"Could not find diffusion folder at {diffusion_dir}.")
            report = (sinfo["id"], "Not ready for CUDIMOT NODDI", 1)
            run = False

        # set up the command
        comm = (
            "%(script)s \
                %(diffusion_dir)s"
            % {"script": cudimot_script, "diffusion_dir": diffusion_dir}
        )

        # report command
        log.rule(before=1, after=1)
        log.raw("Running CUDIMOT NODDI modelling via QuNex:\n\n")
        log.raw(comm.replace("                ", ""))
        log.rule(after=1)

        # run
        if run:
            # run
            if options["run"] == "run":
                # remove previous results if overwrite
                if overwrite:
                    if os.path.exists(results_folder):
                        shutil.rmtree(results_folder)

                if os.path.exists(results_folder):
                    log.step(f"Results already exits and overwrite not set, skipping session {session}.")
                    report = (sinfo["id"], "CUDIMOT NODDI results already exist", 0)
                else:
                    # execute
                    _, _, failed = pc.run_external_for_file(
                        None,
                        comm,
                        "Running CUDIMOT NODDI modelling",
                        overwrite=overwrite,
                        thread=sinfo["id"],
                        remove=options["log"] == "remove",
                        task=options["command_ran"],
                        logfolder=options["comlogs"],
                        logtags=[options["logtag"]],
                        full_test=None,
                        shell=True,
                        _log=log,
                    )

                    if failed:
                        log.step(f"CUDIMOT NODDI processing for session {session} failed")
                        report = (sinfo["id"], "CUDIMOT NODDI failed", 1)
                    else:
                        log.step(f"CUDIMOT NODDI processing for session {session} completed")
                        report = (sinfo["id"], "CUDIMOT NODDI completed", 0)

            # just checking, against the results the run would leave
            else:
                passed, _, failed = pc.check_run(
                    results_folder,
                    None,
                    "CUDIMOT NODDI " + session,
                    overwrite=overwrite,
                    _log=log,
                )

                if passed is None:
                    log.step("CUDIMOT NODDI can be run")
                    report = (sinfo["id"], "CUDIMOT NODDI ready", 0)
                else:
                    log.step(f"CUDIMOT NODDI processing for session {session} would be skipped")
                    report = (sinfo["id"], "CUDIMOT NODDI would be skipped", 0)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(f"\n\n\n --- Failed during processing of session {session} with error:\n")
        log.raw(str(errormessage))
        report = (sinfo["id"], "CUDIMOT NODDI failed", 1)

    except Exception:
        log.info(f" --- Failed during processing of session {session} with error:\n {traceback.format_exc()}\n")
        report = (sinfo["id"], "CUDIMOT NODDI failed", 1)

    return log.result(report)
