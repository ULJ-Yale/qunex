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

"""
Copyright (c) Grega Repovs and Jure Demsar.
All rights reserved.
"""

import os
import shutil
import traceback
import processing.core as pc
from datetime import datetime

def dwi_f99(sinfo, options, overwrite=False, thread=0):
    """
    ``dwi_f99 [... processing options]``

    ``f99 [... processing options]``

    This command executes FSL's F99 script for registering your own diffusion
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
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

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

    # get session id
    session = sinfo["id"]

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s FSL F99 registration [%s] ..." % (
        pc.action("Running", options["run"]), session)

    # status variables
    run = True

    try:
        # check base settings
        pc.doOptionsCheck(options, sinfo, "dwi_f99")

        # construct dirs
        dwi_f99_dir = os.path.join(
            os.environ["FSLDIR"], "data/xtract_data/standard/F99")
        nhp_dir = os.path.join(options["sessionsfolder"], session, "NHP")
        f99reg_dir = os.path.join(nhp_dir, "F99reg")
        if not os.path.exists(f99reg_dir):
            os.makedirs(f99reg_dir)
        dtifit_dir = os.path.join(nhp_dir, "dMRI")

        # check dtifit results
        dti_file = os.path.join(dtifit_dir, "dti_FA.nii.gz")
        if os.path.exists(dti_file):
            r += "\n---> dtifit results present."
        else:
            r += "\n---> ERROR: Could not find dtifit results."
            report = (sinfo['id'], "Not ready for FSL F99", 1)
            run = False

        # script location
        niu_template_dir = os.environ["NIUTemplateFolder"]
        f99_script = "bash " + \
            os.path.join(niu_template_dir, "nhp", "do_reg_F99.sh")

        # set up the command
        comm = "%(script)s \
                %(input)s \
                %(output)s \
                %(f99dir)s" % {
            "script": f99_script,
            "input": dti_file,
            "output": f99reg_dir + "/F99",
            "f99dir": dwi_f99_dir}

        # report command
        r += "\n\n------------------------------------------------------------\n"
        r += "Running FSL F99 command via QuNex:\n\n"
        r += comm.replace("                ", "")
        r += "\n------------------------------------------------------------\n"

        # check for existing F99 results
        target_file = os.path.join(f99reg_dir, "F99_anat_to_F99.nii.gz")
        fullTest = None

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
                r, endlog, _, failed = pc.runExternalForFile(target_file, comm, "Running FSL F99", overwrite=overwrite, thread=sinfo["id"], remove=options[
                                                             "log"] == "remove", task=options["command_ran"], logfolder=options["comlogs"], logtags=[options["logtag"]], fullTest=fullTest, shell=True, r=r)

                if failed:
                    r += "\n---> FSL F99 processing for session %s failed" % session
                    report = (sinfo['id'], "FSL F99 failed", 1)
                else:
                    r += "\n---> FSL F99 processing for session %s completed" % session
                    report = (sinfo['id'], "FSL F99 completed", 0)

            # just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    target_file, None, "FSL F99 " + session, r, overwrite=overwrite)

                if passed is None:
                    r += "\n---> FSL F99 can be run"
                    report = (sinfo['id'], "FSL F99 ready", 0)
                else:
                    r += "\n---> FSL F99 processing for session %s would be skipped" % session
                    report = (sinfo['id'], "FSL F99 would be skipped", 1)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of session %s with error:\n" % (
            session)
        r += str(errormessage)
        report = (sinfo['id'], "FSL F99 failed", 1)

    except:
        r += "\n --- Failed during processing of session %s with error:\n %s\n" % (
            session, traceback.format_exc())
        report = (sinfo['id'], "FSL F99 failed", 1)

    return (r, report)


def dwi_xtract(sinfo, options, overwrite=False, thread=0):
    """
    ``dwi_xtract [... processing options]``

    ``fslx [... processing options]``

    This command executes FSL's XTRACT (cross-species tractography) command.
    It can be used to automatically extract a set of carefully dissected tracts
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
            The path to the folder where runlogs and comlogs
            are to be stored, if other than default.

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

        --xtract_native (flag, optional):
            Run tractography in native (diffusion) space. This flag is not set
            by default.

        --xtract_ref (str, default ''):
            Reference image ("<refimage> <diff2ref> <ref2diff>") for running
            tractography in reference space, Diff2Reference and Reference2Diff
            transforms.

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

    # get session id
    session = sinfo["id"]

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s FSL XTRACT [%s] ..." % (pc.action("Running",
                                       options["run"]), session)

    # status variables
    run = True

    try:
        # check base settings
        pc.doOptionsCheck(options, sinfo, "dwi_xtract")

        # get species
        species = "HUMAN"
        if "species" in options and options["species"].upper() == "MACAQUE":
            species = "MACAQUE"

        # set dirs
        if species == "MACAQUE":
            ptx_options = os.path.join(
                os.environ["NIUTemplateFolder"], "nhp", "ptx_options")
            nhp_dir = os.path.join(options["sessionsfolder"], session, "NHP")
            f99reg_dir = os.path.join(nhp_dir, "F99reg")
            bedpostx_dir = os.path.join(nhp_dir, "dMRI.bedpostX")
            output_dir = os.path.join(nhp_dir, "xtract")
        else:
            hcp_dir = os.path.join(options["sessionsfolder"], session, "hcp")
            # if sessions is a folder
            if os.path.isfile(options["sessions"]):
                hcp_dir = os.path.join(
                    sinfo["hcp"], sinfo["id"] + options["hcp_suffix"])
            xfms_dir = os.path.join(hcp_dir, "MNINonLinear", "xfms")
            t1w_dir = os.path.join(hcp_dir, "T1w")
            bedpostx_dir = os.path.join(t1w_dir, "Diffusion.bedpostX")
            output_dir = os.path.join(t1w_dir, "xtract")

        # check bedpostx results
        if species == "MACAQUE":
            bedpostx_file = os.path.join(
                bedpostx_dir, "mean_fsumsamples.nii.gz")
        else:
            bedpostx_file = os.path.join(
                bedpostx_dir, "mean_fsumsamples.nii.gz")

        if os.path.exists(bedpostx_file):
            r += "\n---> f results present."
        else:
            r += "\n---> ERROR: Could not find bedpostx results."
            report = (sinfo['id'], "Not ready for XTRACT", 1)
            run = False

        # script location
        xtract_script = os.path.join(os.environ["FSLDIR"], "bin/xtract")

        # set up the core command
        comm = "%(script)s \
                -bpx %(bedpostx_dir)s \
                -out %(output_dir)s \
                -species %(species)s" % {
            "script": xtract_script,
            "bedpostx_dir": bedpostx_dir,
            "output_dir": output_dir,
            "species": species}

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

        # xtract_native
        if "xtract_native" in options:
            comm = comm + " -native"

        # xtract_resolution
        if "xtract_ref" in options:
            comm = comm + " -ref %s" % options["xtract_ref"]

        # report command
        r += "\n\n------------------------------------------------------------\n"
        r += "Running FSL F99 command via QuNex:\n\n"
        r += comm.replace("                ", "")
        r += "\n------------------------------------------------------------\n"

        # check for existing XTRACT results
        target_file = os.path.join(
            output_dir, "tracts", "vof_r", "density.nii.gz")
        fullTest = None

        # run
        if run:
            # run
            if options["run"] == "run":
                # remove previous file
                if overwrite and os.path.exists(target_file):
                    os.remove(target_file)

                # execute
                r, endlog, _, failed = pc.runExternalForFile(target_file, comm, "Running FSL XTRACT", overwrite=overwrite, thread=sinfo["id"], remove=options[
                                                             "log"] == "remove", task=options["command_ran"], logfolder=options["comlogs"], logtags=[options["logtag"]], fullTest=fullTest, shell=True, r=r)

                r += "\n---> Processing details can be found in %s" % (
                    os.path.join(output_dir, "logs"))

                if failed:
                    r += "\n---> FSL XTRACT processing for session %s failed" % session
                    report = (sinfo['id'], "FSL XTRACT failed", 1)
                else:
                    r += "\n---> FSL XTRACT processing for session %s completed" % session
                    report = (sinfo['id'], "FSL XTRACT completed", 0)

            # just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    target_file, None, "FSL XTRACT " + session, r, overwrite=overwrite)

                if passed is None:
                    r += "\n---> FSL XTRACT can be run"
                    report = (sinfo['id'], "FSL XTRACT ready", 0)
                else:
                    r += "\n---> FSL XTRACT processing for session %s would be skipped" % session
                    report = (sinfo['id'], "FSL XTRACT would be skipped", 1)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = "\n\n\n --- Failed during processing of session %s with error:\n" % (
            session)
        r += str(errormessage)
        report = (sinfo['id'], "FSL XTRACT failed", 1)

    except:
        r += "\n --- Failed during processing of session %s with error:\n %s\n" % (
            session, traceback.format_exc())
        report = (sinfo['id'], "FSL XTRACT failed", 1)

    return (r, report)


def dwi_noddi_gpu(sinfo, options, overwrite=False, thread=0):
    """
    ``dwi_noddi_gpu [... processing options]``

    ``noddi [... processing options]``

    This command executes CUDIMOT's NODDI microstructure modelling. It uses
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
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.

        --noddi_model (str, default 'Watson'):
            Whether to use the Watson or the Bingham NODDI model.

        --cuda_version (str, default '10.2'):
            Which CUDA version to use. Supports 10.2, 11.3 and 12.

    Output files:
        The results of this step will be present in the HCP Diffusion folder::

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

    # get session id
    session = sinfo["id"]

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s CUDIMOT NODDI modelling [%s] ..." % (
        pc.action("Running", options["run"]), session)

    # status variables
    run = True

    try:
        # check base settings
        pc.doOptionsCheck(options, sinfo, "dwi_noddi_gpu")

        # script location
        cudimot_dir = ""
        if "cuda_version" in options:
            if "QUNEXLIBRARY" not in os.environ:
                r += "\n---> ERROR: Variable QUNEXLIBRARY not found in environment, check your QuNex setup."
                report = (sinfo['id'], "Not ready for CUDIMOT NODDI", 1)
                run = False
            else:
                cudimot_dir = os.path.join(
                    os.environ["QUNEXLIBRARY"], "etc", "cudimot", f"cuda_{options['cuda_version']}")
                os.environ["CUDIMOT"] = cudimot_dir
        else:
            cudimot_dir = os.environ["CUDIMOT"]

        # model
        if "noddi_model" not in options:
            options["noddi_model"] = "Watson"

        # check validity
        if options["noddi_model"] not in ["Watson", "Bingham"]:
            r += f"\n---> ERROR: Invalid NODDI model [{options['noddi_model']}], needs to be Watson or Bingham."
            report = (sinfo['id'], "Not ready for CUDIMOT NODDI", 1)
            run = False

        cudimot_script = os.path.join(
            cudimot_dir, "bin", f"Pipeline_NODDI_{options['noddi_model']}.sh")

        # session's diffusion dir
        t1w_dir = os.path.join(
            options["sessionsfolder"], session, "hcp", session, "T1w")
        diffusion_dir = os.path.join(t1w_dir, "Diffusion")

        # set up the command
        comm = "%(script)s \
                %(diffusion_dir)s" % {
            "script": cudimot_script,
            "diffusion_dir": diffusion_dir}

        # report command
        r += "\n\n------------------------------------------------------------\n"
        r += "Running CUDIMOT NODDI modelling via QuNex:\n\n"
        r += comm.replace("                ", "")
        r += "\n------------------------------------------------------------\n"

        # run
        if run:
            # run
            if options["run"] == "run":
                # remove previous results if overwrite
                results_folder = os.path.join(
                    t1w_dir, "Diffusion.NODDI_" + options["noddi_model"])

                if overwrite:
                    if os.path.exists(results_folder):
                        shutil.rmtree(results_folder)

                if os.path.exists(results_folder):
                    r += f"\n---> Results already exits and overwrite not set, skipping session {session}."
                    report = (
                        sinfo['id'], "CUDIMOT NODDI results already exist", 0)
                else:
                    # execute
                    r, _, _, failed = pc.runExternalForFile(None, comm, "Running CUDIMOT NODDI modelling", overwrite=overwrite, thread=sinfo["id"], remove=options[
                        "log"] == "remove", task=options["command_ran"], logfolder=options["comlogs"], logtags=[options["logtag"]], fullTest=None, shell=True, r=r)

                    if failed:
                        r += "\n---> CUDIMOT NODDI processing for session %s failed" % session
                        report = (sinfo['id'], "CUDIMOT NODDI failed", 1)
                    else:
                        r += "\n---> CUDIMOT NODDI processing for session %s completed" % session
                        report = (sinfo['id'], "CUDIMOT NODDI completed", 0)

            # just checking
            else:
                passed, _, r, failed = pc.checkRun(
                    None, None, "CUDIMOT NODDI " + session, r, overwrite=overwrite)

                if passed is None:
                    r += "\n---> CUDIMOT NODDI can be run"
                    report = (sinfo['id'], "CUDIMOT NODDI ready", 0)
                else:
                    r += f"\n---> CUDIMOT NODDI processing for session {session} would be skipped"
                    report = (sinfo['id'], "CUDIMOT NODDI would be skipped", 1)

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        r = f"\n\n\n --- Failed during processing of session {session} with error:\n"
        r += str(errormessage)
        report = (sinfo["id"], "CUDIMOT NODDI failed", 1)

    except:
        r += f"\n --- Failed during processing of session {session} with error:\n {traceback.format_exc()}\n"
        report = (sinfo["id"], "CUDIMOT NODDI failed", 1)

    return (r, report)
