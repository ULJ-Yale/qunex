#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``hcp_mmorf.py``

The registration step of the HCP MMORF chain.
"""

import glob
import os
import os.path
import shutil

import qx_utilities.hcp.mmorf_utils as mu


def hcp_mmorf(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_mmorf [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run the registration step of the HCP MMORF chain (MMORFPipeline.sh).

    ..  qx_command:
        type: processing.session

    Warning:
        The code expects the previous step (hcp_pre_mmorf) to have run
        successfully. The chain requires a T2w image and human data, has no
        longitudinal path and reads the diffusion data from T1w/Diffusion only,
        so a session outside of that is rejected.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --studyfolder (str):
            The path to the study folder. The sessions are in its `sessions`
            folder, unless --sessionsfolder names another one.

        --sessionsfolder (str, default '<studyfolder>/sessions'):
            The path to the folder with the sessions. Set it only when the
            sessions are not in the `sessions` folder of the study. With
            neither --studyfolder nor --sessionsfolder given, the current
            folder is used.

        --parsessions (int, default 1):
            How many sessions to run in parallel. QuNex does not assign GPUs to
            sessions, so run one session per GPU.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). With 'yes' the
            mov_to_ref_mm_* files in MMORFNonLinear/xfms and the completion file
            of hcp_post_mmorf are removed before the run, and hcp_post_mmorf has
            to be run again.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_folderstructure (str, default 'hcpls'):
            The HCP folder structure of the session, 'hcpya' or 'hcpls'.

        --hcp_mmorf_t1_template (str, default HCP "MMORF_T1_0.7mm.nii.gz"):
            The T1w template. Also used by hcp_post_mmorf.

        --hcp_mmorf_t2_template (str, default HCP "MMORF_T2_0.7mm.nii.gz"):
            The T2w template.

        --hcp_mmorf_ref_mask (str, default HCP "MMORF_T1_0.7mm_brain_mask.nii.gz"):
            The reference brain mask.

        --hcp_mmorf_diffusion_ref (str, default HCP "MMORF_DTI_0.7mm_tensor.nii.gz"):
            The diffusion tensor template.

        --hcp_mmorf_dti_ref_mask (str, default HCP "MMORF_DTI_0.7mm_brain_mask.nii.gz"):
            The reference brain mask of the diffusion tensor template.

        --hcp_dwi_name (str, default 'Diffusion'):
            A session processed under another name is rejected, as the MMORF
            scripts only read T1w/Diffusion.

        --hcp_species (str, default 'Human'):
            A non-human species is rejected, as the MMORF scripts and templates
            support human data only.

        --longitudinal (flag, optional):
            Rejected if set, as the MMORF scripts have no longitudinal path.

    Output files:
        The warp, the Jacobian determinant and the bias fields
        (mov_to_ref_mm_*) in the MMORFNonLinear/xfms folder of the session's hcp
        folder.

    Notes:
        hcp_mmorf parameter mapping:

            =========================== ======================
            QuNex parameter             HCPpipelines parameter
            =========================== ======================
            ``hcp_mmorf_t1_template``   ``t1-template``
            ``hcp_mmorf_t2_template``   ``t2-template``
            ``hcp_mmorf_ref_mask``      ``ref-mask``
            ``hcp_mmorf_diffusion_ref`` ``diffusion-ref``
            ``hcp_mmorf_dti_ref_mask``  ``dti-ref-mask``
            =========================== ======================

        Apptainer (Singularity) and GPU support:
            MMORF is run on an NVIDIA GPU when it can find one, and otherwise
            falls back to its much slower CPU version without saying so. Look
            for [GPU] or [CPU] at the top of the command's comlog. To give the
            container access to the GPU, use the --cuda flag of the
            qunex_container script, or the older --nv. The MMORF settings are
            fixed in the HCP script, so neither the version nor the GPU memory
            use can be changed from QuNex, and hcp_nogpu and hcp_cuda_version
            have no effect here.

    Examples:
        Example run from the base study folder with test flag::

            qunex hcp_mmorf \\
                --studyfolder="." \\
                --batchfile="processing/batch.txt" \\
                --overwrite="no" \\
                --test

        Example run on a GPU with a scheduler::

            qunex hcp_mmorf \\
                --studyfolder="<path_to_study_folder>" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --overwrite="yes" \\
                --scheduler="SLURM,time=12:00:00,cpus-per-task=1,mem-per-cpu=32000,partition=GPU,gpus=1"
    """

    return mu.run_step(
        sinfo,
        options,
        overwrite,
        "hcp_mmorf",
        "HCP MMORF Pipeline",
        "HCP MMORF",
        _plan,
    )


def _plan(sinfo: dict, options: dict, hcp: dict, _log) -> mu.MmorfStep:
    """The checks and the command line of MMORFPipeline.sh."""
    templates = [
        ("t1-template", mu.template(options, hcp, "hcp_mmorf_t1_template", mu.T1_TEMPLATE)),
        ("t2-template", mu.template(options, hcp, "hcp_mmorf_t2_template", "MMORF_T2_0.7mm.nii.gz")),
        ("ref-mask", mu.template(options, hcp, "hcp_mmorf_ref_mask", "MMORF_T1_0.7mm_brain_mask.nii.gz")),
        ("diffusion-ref", mu.template(options, hcp, "hcp_mmorf_diffusion_ref", "MMORF_DTI_0.7mm_tensor.nii.gz")),
        ("dti-ref-mask", mu.template(options, hcp, "hcp_mmorf_dti_ref_mask", "MMORF_DTI_0.7mm_brain_mask.nii.gz")),
    ]

    present = mu.check_inputs(
        [(os.path.join(mu.diffusion_folder(hcp), "nodif_brain_mask.nii.gz"), "run hcp_diffusion first")]
        + [(path, mu.TEMPLATE_HINT) for _, path in templates],
        _log=_log,
    )
    ready = mu.check_chain_inputs(mu.pre_outputs(hcp), options, _log=_log)

    if shutil.which("nvidia-smi") is None:
        _log.warning(
            "nvidia-smi not found, MMORF will fall back to its much slower CPU version. "
            "In a container use the --cuda or --nv flag of qunex_container."
        )

    xfms = mu.xfms_folder(hcp)
    return mu.MmorfStep(
        present and ready,
        mu.build_command(hcp, "MMORFPipeline.sh", mu.session_flags(sinfo, options) + templates),
        # the warp is written first and the bias fields last, the second scalar's last of all
        os.path.join(xfms, "mov_to_ref_mm_bias_1.nii.gz"),
        glob.glob(os.path.join(xfms, "mov_to_ref_mm_*")) + [mu.post_test_file(sinfo, options, hcp)],
    )
