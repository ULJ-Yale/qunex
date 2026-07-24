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
--dwi_noddi     Runs CUDIMOT NODDI microstructure modelling.

All the functions are part of the processing suite. They should be called
from the command line using `qunex` command. Help is available through:

- ``qunex ?<command>`` for command specific help
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


def dwi_f99(sinfo, options, overwrite=False, thread=0):
    """
    ``dwi_f99 [... processing options]``

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

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --diffusion_folder (str, default '<sessions_folder>/<session>/NHP/dMRI'):
            The path to the diffusion folder holding the dtifit results.

    Output files:
        The results of this step will be present in the dMRI/NHP/F99reg
        folder in the sessions's root::

            study
            └─ sessions
               ├─ session1
               |  └─ dMRI
               |    └─ NHP
               |      └─ F99reg
               └─ session2
                  └─ dMRI
                    └─ NHP
                      └─ F99reg

    Examples:
        ::

            qunex dwi_f99 \\
                --sessionsfolder="/data/macaque_study/sessions" \\
                --sessions="hilary,jane" \\
                --overwrite=no \\
                --parsessions=2
    """
    log = ReportLog()

    # get session id
    session = sinfo["id"]

    log.capture("\n------------------------------------------------------------")
    log.raw("\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    ))
    log.raw("\n%s FSL F99 registration [%s] ..." % (
        pc.action("Running", options["run"]),
        session,
    ))

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
        if not os.path.exists(f99reg_dir):
            os.makedirs(f99reg_dir)
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
        log.raw("\n\n------------------------------------------------------------\n")
        log.raw("Running FSL F99 command via QuNex:\n\n")
        log.raw(comm.replace("                ", ""))
        log.raw("\n------------------------------------------------------------\n")

        # check for existing F99 results
        target_file = os.path.join(f99reg_dir, "F99_anat_to_F99.nii.gz")
        full_test = None

        # run
        if run:
            # run
            if options["run"] == "run":
                # remove previous file
                if overwrite and os.path.exists(target_file):
                    os.remove(target_file)

                # go to F99 folder before starting workd
                comm_pre = "CDIR=`pwd`;cd " + f99reg_dir + ";"

                # go back to current dir after work is done
                comm_post = ";cd $CDIR"

                # add pre and post to command
                comm = comm_pre + comm + comm_post

                # execute
                endlog, _, failed = log.run_external(
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
                )

                if failed:
                    log.raw("\n---> FSL F99 processing for session %s failed" % session)
                    report = (sinfo["id"], "FSL F99 failed", 1)
                else:
                    log.raw("\n---> FSL F99 processing for session %s completed" % session)
                    report = (sinfo["id"], "FSL F99 completed", 0)

            # just checking
            else:
                passed, _, failed = log.check_run(
                    target_file, None, "FSL F99 " + session, overwrite=overwrite
                )

                if passed is None:
                    log.step("FSL F99 can be run")
                    report = (sinfo["id"], "FSL F99 ready", 0)
                else:
                    log.raw("\n---> FSL F99 processing for session %s would be skipped"
                        % session)
                    report = (sinfo["id"], "FSL F99 would be skipped", 1)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.capture("\n\n\n --- Failed during processing of session %s with error:\n" % (
            session
        ))
        log.raw(str(errormessage))
        report = (sinfo["id"], "FSL F99 failed", 1)

    except Exception:
        log.raw("\n --- Failed during processing of session %s with error:\n %s\n" % (
            session,
            traceback.format_exc(),
        ))
        report = (sinfo["id"], "FSL F99 failed", 1)

    return (log.text, report)


def dwi_xtract(sinfo, options, overwrite=False, thread=0):
    """
    ``dwi_xtract [... processing options]``

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

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

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
            is set to dMRI for macaques and T1w/Diffusion for humans. If
            --xtract_bpx is provided, it takes precedence over this parameter.

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
            '$TOOLS/python/qx_utilities/templates/nhp/ptx_options'.

        --xtract_mni (flag, optional):
            Run tractography in MNI (diffusion) and not native space. This flag is not set by default.

        --xtract_ref (str, default ''):
            Reference image ("<refimage> <diff2ref> <ref2diff>") for running
            tractography in reference space, Diff2Reference and Reference2Diff
            transforms.

        --xtract_out (str, default detailed below):
            Output folder for XTRACT results. By default it is set to
            dMRI/NHP/xtract for macaques and hcp/session/T1w/xtract for humans.

        --xtract_bpx (str, default detailed below):
            Bedpostx folder. By default it is set to dMRI.bedpostX for macaques
            and T1w/Diffusion.bedpostX for humans.

    Output files:
        The results of this step will be present in the dMRI/NHP/xtract folder
        in the sessions's root::

            study
            └─ sessions
               ├─ session1
               |  └─ dMRI
               |    └─ NHP
               |      └─ xtract
               └─ session2
                  └─ dMRI
                    └─ NHP
                      └─ xtract

    Examples:
        ::

            qunex dwi_xtract \\
                --sessionsfolder="/data/macaque_study/sessions" \\
                --batchfile="/data/example_study/processing/batch.txt" \\
                --species="human" \\
                --overwrite=yes

        ::

            qunex dwi_xtract \\
                --sessionsfolder="/data/macaque_study/sessions" \\
                --batchfile="hilary,jane" \\
                --species="macaque" \\
                --overwrite=no \\
                --parsessions=2

    """
    log = ReportLog()

    # get session id
    session = sinfo["id"]

    log.capture("\n------------------------------------------------------------")
    log.raw("\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    ))
    log.raw("\n%s FSL XTRACT [%s] ..." % (pc.action("Running", options["run"]), session))

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
            hcp_dir = os.path.join(options["sessionsfolder"], session, "hcp")
            # if sessions is a folder
            if os.path.isfile(options["sessions"]):
                hcp_dir = os.path.join(
                    sinfo["hcp"], sinfo["id"] + options["hcp_suffix"]
                )
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

        # create output dir if it does not exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

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
            log.step("f results present.")
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
        log.raw("\n\n------------------------------------------------------------\n")
        log.raw("Running FSL F99 command via QuNex:\n\n")
        log.raw(comm.replace("                ", ""))
        log.raw("\n------------------------------------------------------------\n")

        # check for existing XTRACT results
        target_file = os.path.join(output_dir, "tracts", "vof_r", "density.nii.gz")
        full_test = None

        # run
        if run:
            # run
            if options["run"] == "run":
                # remove previous file
                if overwrite and os.path.exists(target_file):
                    os.remove(target_file)

                # execute
                _, _, failed = log.run_external(
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
                )

                log.raw("\n---> Processing details can be found in %s" % (
                    os.path.join(output_dir, "logs")
                ))

                if failed:
                    log.raw("\n---> FSL XTRACT processing for session %s failed" % session)
                    report = (sinfo["id"], "FSL XTRACT failed", 1)
                else:
                    log.raw("\n---> FSL XTRACT processing for session %s completed"
                        % session)
                    report = (sinfo["id"], "FSL XTRACT completed", 0)

            # just checking
            else:
                passed, _, failed = log.check_run(
                    target_file, None, "FSL XTRACT " + session, overwrite=overwrite
                )

                if passed is None:
                    log.step("FSL XTRACT can be run")
                    report = (sinfo["id"], "FSL XTRACT ready", 0)
                else:
                    log.raw("\n---> FSL XTRACT processing for session %s would be skipped"
                        % session)
                    report = (sinfo["id"], "FSL XTRACT would be skipped", 1)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.capture("\n\n\n --- Failed during processing of session %s with error:\n" % (
            session
        ))
        log.raw(str(errormessage))
        report = (sinfo["id"], "FSL XTRACT failed", 1)

    except Exception:
        log.raw("\n --- Failed during processing of session %s with error:\n %s\n" % (
            session,
            traceback.format_exc(),
        ))
        report = (sinfo["id"], "FSL XTRACT failed", 1)

    return (log.text, report)


# -> @register_command(
#        description="Run CUDIMOT's NODDI microstructure modelling using GPU acceleration.",
#         type="processing.session.dwi")
def dwi_noddi_gpu(sinfo, options, overwrite=False, thread=0):
    """
    ``dwi_noddi_gpu [... processing options]``

    Run CUDIMOT NODDI microstructure modelling using GPU acceleration.

    ..  qx_command:
        type: processing.session
        aliases: noddi

    Description:
        This command runs CUDIMOT's NODDI microstructure modelling. It uses
        precompiled CUDA (GPU) binaries and therefore requires a CUDA capable GPU to
        run. Currently supported CUDA version are 10.2, 11.3 and 12. The command can
        use two different models: Watson and Bingham. The Watson model is used by
        default.

    Warning:
        To use this command, successful completion of hcp_diffusion or
        dwi_legacy_gpu is required.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessions (str, default ''):
            A list of sessions to process.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

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

        --cuda_version (str, default '11.3'):
            Which CUDA version to use. Supports 10.2, 11.3 and 12.

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
        results will be stored in the same root folder as the input diffusion
        data, in a subfolder named Diffusion.NODDI_<model>.

    Examples:
        ::

            qunex dwi_noddi_gpu \\
                --sessionsfolder="/data/qx_study/sessions" \\
                --batchfile="/data/qx_study/processing/batch.txt"

            qunex dwi_noddi_gpu \\
                --sessionsfolder="/data/qx_study/sessions" \\
                --batchfile="/data/qx_study/processing/batch.txt" \\
                --noddi_model="Bingham" \\
                --cuda_version="12" \\
                --overwrite=no \\
                --parsessions=2
    """
    log = ReportLog()

    # get session id
    session = sinfo["id"]

    log.capture("\n------------------------------------------------------------")
    log.raw("\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    ))
    log.raw("\n%s CUDIMOT NODDI modelling [%s] ..." % (
        pc.action("Running", options["run"]),
        session,
    ))

    # status variables
    run = True

    try:
        # check base settings
        pc.do_options_check(options, sinfo, "dwi_noddi_gpu")

        # script location
        cudimot_dir = ""
        if "cuda_version" in options:
            if "QUNEXLIBRARY" not in os.environ:
                log.error("Variable QUNEXLIBRARY not found in environment, check your QuNex setup.")
                report = (sinfo["id"], "Not ready for CUDIMOT NODDI", 1)
                run = False
            else:
                cudimot_dir = os.path.join(
                    os.environ["QUNEXLIBRARY"],
                    "etc",
                    "cudimot",
                    f"cuda_{options['cuda_version']}",
                )
                os.environ["CUDIMOT"] = cudimot_dir
        else:
            cudimot_dir = os.environ["CUDIMOT"]

        # model
        if "noddi_model" not in options:
            options["noddi_model"] = "Watson"

        # check validity
        if options["noddi_model"] not in ["Watson", "Bingham"]:
            log.raw(f"\n---> ERROR: Invalid NODDI model [{options['noddi_model']}], needs to be Watson or Bingham.")
            report = (sinfo["id"], "Not ready for CUDIMOT NODDI", 1)
            run = False

        cudimot_script = os.path.join(
            cudimot_dir, "bin", f"Pipeline_NODDI_{options['noddi_model']}.sh"
        )

        # session's diffusion dir
        root_dir = os.path.join(
            options["sessionsfolder"], session, "hcp", session, "T1w"
        )
        diffusion_dir = os.path.join(root_dir, "Diffusion")

        # if diffusion folder specified, use that instead
        if options["diffusion_folder"]:
            diffusion_dir = options["diffusion_folder"]
            root_dir = os.path.dirname(diffusion_dir)

        # check that diffusion_dir exists
        if not os.path.exists(diffusion_dir):
            log.raw(f"\n---> ERROR: Could not find diffusion folder at {diffusion_dir}.")
            report = (sinfo["id"], "Not ready for CUDIMOT NODDI", 1)
            run = False

        # set up the command
        comm = (
            "%(script)s \
                %(diffusion_dir)s"
            % {"script": cudimot_script, "diffusion_dir": diffusion_dir}
        )

        # report command
        log.raw("\n\n------------------------------------------------------------\n")
        log.raw("Running CUDIMOT NODDI modelling via QuNex:\n\n")
        log.raw(comm.replace("                ", ""))
        log.raw("\n------------------------------------------------------------\n")

        # run
        if run:
            # run
            if options["run"] == "run":
                # remove previous results if overwrite
                results_folder = os.path.join(
                    root_dir, "Diffusion.NODDI_" + options["noddi_model"]
                )

                if overwrite:
                    if os.path.exists(results_folder):
                        shutil.rmtree(results_folder)

                if os.path.exists(results_folder):
                    log.raw(f"\n---> Results already exits and overwrite not set, skipping session {session}.")
                    report = (sinfo["id"], "CUDIMOT NODDI results already exist", 0)
                else:
                    # execute
                    _, _, failed = log.run_external(
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
                    )

                    if failed:
                        log.raw("\n---> CUDIMOT NODDI processing for session %s failed"
                            % session)
                        report = (sinfo["id"], "CUDIMOT NODDI failed", 1)
                    else:
                        log.raw("\n---> CUDIMOT NODDI processing for session %s completed"
                            % session)
                        report = (sinfo["id"], "CUDIMOT NODDI completed", 0)

            # just checking
            else:
                passed, _, failed = log.check_run(
                    None, None, "CUDIMOT NODDI " + session, overwrite=overwrite
                )

                if passed is None:
                    log.step("CUDIMOT NODDI can be run")
                    report = (sinfo["id"], "CUDIMOT NODDI ready", 0)
                else:
                    log.raw(f"\n---> CUDIMOT NODDI processing for session {session} would be skipped")
                    report = (sinfo["id"], "CUDIMOT NODDI would be skipped", 1)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.capture(f"\n\n\n --- Failed during processing of session {session} with error:\n")
        log.raw(str(errormessage))
        report = (sinfo["id"], "CUDIMOT NODDI failed", 1)

    except Exception:
        log.raw(f"\n --- Failed during processing of session {session} with error:\n {traceback.format_exc()}\n")
        report = (sinfo["id"], "CUDIMOT NODDI failed", 1)

    return (log.text, report)
