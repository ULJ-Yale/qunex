#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``hcp_post_mmorf.py``

The last step of the HCP MMORF chain.
"""

import os
import os.path
import re

import qx_utilities.hcp.mmorf_utils as mu

_POST_FS_HINT = "run hcp_post_freesurfer first"


def hcp_post_mmorf(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_post_mmorf [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run the last step of the HCP MMORF chain (PostMMORFPipeline.sh).

    ..  qx_command:
        type: processing.session

    Warning:
        The code expects the previous steps (hcp_pre_mmorf and hcp_mmorf) to
        have run successfully. By default it also needs the MSMAll registration,
        from hcp_msmall with resampling or from hcp_dedrift_and_resample. The
        chain requires a T2w image and human data, has no longitudinal path and
        reads the diffusion data from T1w/Diffusion only, so a session outside
        of that is rejected.

        The HCP script (PostMMORF_generateSurfaceFiles.sh) stops on any file it
        expects and does not find.

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
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). With 'yes' the
            command's completion file is removed before the run, and the
            pipeline writes its results over the existing ones. With 'no', a
            completion file older than the warp of hcp_mmorf stops the command
            instead of being taken as finished.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_folderstructure (str, default 'hcpls'):
            The HCP folder structure of the session, 'hcpya' or 'hcpls'.

        --hcp_mmorf_t1_template (str, default HCP "MMORF_T1_0.7mm.nii.gz"):
            The T1w template. Also used by hcp_mmorf.

        --hcp_hiresmesh (int, default 164):
            The high resolution mesh, which hcp_post_freesurfer must have built.
            Passed only if it is not 164, which is HCP's default.

        --hcp_lowresmesh (str, default '32'):
            The low resolution meshes, separated by commas, which
            hcp_post_freesurfer must have built. Passed only if it is not 32,
            which is HCP's default.

        --hcp_mmorf_diffusionmesh (int, default HCP 79):
            The diffusion mesh, which this command creates. It can not be a mesh
            of hcp_post_freesurfer, whose files it would overwrite. Passed only
            if set.

        --hcp_mmorf_regname (str, default HCP MSMAll):
            The surface registration to use, which must be in
            MNINonLinear/Native. Passed only if set.

        --hcp_mmorf_regnameorig (str, default HCP MSMSulc):
            The registration the first one started from, which must be in
            MNINonLinear/Native. After hcp_post_freesurfer with hcp_regname=FS
            the sphere is called reg.reg_LR. Passed only if set.

        --hcp_inflatescale (float, default HCP 1):
            Additional inflation scaling, for a low resolution mesh above 32k.
            Passed only if set.

        --hcp_dwi_name (str, default 'Diffusion'):
            A session processed under another name is rejected, as the MMORF
            scripts only read T1w/Diffusion.

        --hcp_species (str, default 'Human'):
            A non-human species is rejected, as the MMORF scripts and templates
            support human data only.

        --longitudinal (flag, optional):
            Rejected if set, as the MMORF scripts have no longitudinal path.

    Output files:
        The T1w, T2w and tensor images, the warps and the surfaces in MMORF space
        in the MMORFNonLinear folder of the session's hcp folder, and the
        session's maps on the diffusion mesh in MNINonLinear/fsaverage_LR79k.

    Notes:
        QuNex leaves the optional flags of PostMMORFPipeline.sh to HCP, so a flag
        is passed only when its parameter asks for something other than HCP's
        default. hcp_hiresmesh, hcp_lowresmesh and hcp_inflatescale are shared
        with hcp_post_freesurfer, as this command reads the meshes it built.
        hcp_regname is not read here: it names the registration
        hcp_post_freesurfer used, while the MMORF chain defaults to MSMAll.

        hcp_post_mmorf parameter mapping:

            =========================== ======================
            QuNex parameter             HCPpipelines parameter
            =========================== ======================
            ``hcp_mmorf_t1_template``   ``t1-template``
            ``hcp_hiresmesh``           ``hiresmesh``
            ``hcp_lowresmesh``          ``lowresmesh``
            ``hcp_mmorf_diffusionmesh`` ``diffusionmesh``
            ``hcp_mmorf_regname``       ``regname``
            ``hcp_mmorf_regnameorig``   ``regnameorig``
            ``hcp_inflatescale``        ``inflatescale``
            =========================== ======================

    Examples:
        Example run from the base study folder with test flag::

            qunex hcp_post_mmorf \\
                --studyfolder="." \\
                --batchfile="processing/batch.txt" \\
                --parsessions="4" \\
                --overwrite="no" \\
                --test

        Example run with two low resolution meshes::

            qunex hcp_post_mmorf \\
                --studyfolder="<path_to_study_folder>" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_lowresmesh="32,59" \\
                --overwrite="yes" \\
                --scheduler="SLURM,time=08:00:00,cpus-per-task=2,mem-per-cpu=8000,partition=day"
    """

    return mu.run_step(
        sinfo,
        options,
        overwrite,
        "hcp_post_mmorf",
        "HCP PostMMORF Pipeline",
        "HCP PostMMORF",
        _plan,
    )


def _plan(sinfo: dict, options: dict, hcp: dict, _log) -> mu.MmorfStep:
    """The checks and the command line of PostMMORFPipeline.sh."""
    t1_template = mu.template(options, hcp, "hcp_mmorf_t1_template", mu.T1_TEMPLATE)
    session = mu.session_name(sinfo, options)

    inputs = [
        (os.path.join(hcp["T1w_folder"], f"{image}.nii.gz"), _POST_FS_HINT)
        for image in (
            "T1w_acpc_dc", "T1w_acpc_dc_restore_brain", "T2w_acpc_dc", "T2w_acpc_dc_restore_brain",
        )
    ]
    inputs += _surface_inputs(session, options, hcp)
    inputs += [
        (t1_template, mu.TEMPLATE_HINT),
        (os.path.join(hcp["hcp_Templates"], "MMORF_T1_1mm.nii.gz"), mu.TEMPLATE_HINT),
    ]
    present = mu.check_inputs(inputs, _log=_log)
    mesh_ok = _check_diffusion_mesh(session, options, hcp, _log)
    warp = os.path.join(mu.xfms_folder(hcp), "mov_to_ref_mm_warp.nii.gz")
    ready = mu.check_chain_inputs(mu.pre_outputs(hcp) + [(warp, "hcp_mmorf")], options, _log=_log)

    test_file = mu.post_test_file(sinfo, options, hcp)
    return mu.MmorfStep(
        present and mesh_ok and ready,
        mu.build_command(
            hcp,
            "PostMMORFPipeline.sh",
            mu.session_flags(sinfo, options) + [("t1-template", t1_template)] + _optional_flags(options),
        ),
        test_file,
        [test_file],
        warp,
    )


def _optional_flags(options: dict) -> list:
    """
    The optional flags, as set: build_command leaves out those that are not.

    hcp_hiresmesh and hcp_lowresmesh always hold a value, as other pipelines
    need them, so here they count as set only when it is not HCP's default.
    """
    hires = mu.effective(options, "hcp_hiresmesh")
    lowres = "@".join(_low_meshes(options))
    return [
        ("hiresmesh", None if hires == mu.UPSTREAM_POST_DEFAULTS["hcp_hiresmesh"] else hires),
        ("lowresmesh", None if lowres == mu.UPSTREAM_POST_DEFAULTS["hcp_lowresmesh"] else lowres),
        ("diffusionmesh", options["hcp_mmorf_diffusionmesh"]),
        ("regname", options["hcp_mmorf_regname"]),
        ("regnameorig", options["hcp_mmorf_regnameorig"]),
        ("inflatescale", options["hcp_inflatescale"]),
    ]


def _low_meshes(options: dict) -> list:
    """The low resolution meshes in effect, split on what both forms use."""
    return [e for e in re.split(r"[,@]", mu.effective(options, "hcp_lowresmesh")) if e]


def _surface_inputs(session: str, options: dict, hcp: dict) -> list:
    """The surfaces PostMMORF_generateSurfaceFiles.sh stops without, with their hints."""
    regname = mu.effective(options, "hcp_mmorf_regname")
    regnameorig = mu.effective(options, "hcp_mmorf_regnameorig")
    hires = mu.effective(options, "hcp_hiresmesh")
    nonlin = hcp["hcp_nonlin"]
    t1w_native = os.path.join(hcp["T1w_folder"], "Native")
    native = os.path.join(nonlin, "Native")

    inputs = [(os.path.join(native, f"{session}.thickness.native.dscalar.nii"), _POST_FS_HINT)]
    for h in ("L", "R"):
        inputs += [
            (os.path.join(t1w_native, f"{session}.{h}.{surface}.native.surf.gii"), _POST_FS_HINT)
            for surface in ("white", "pial")
        ]
        inputs += [
            (
                os.path.join(native, f"{session}.{h}.sphere.{regname}.native.surf.gii"),
                "run hcp_msmall with resampling or hcp_dedrift_and_resample first, or set hcp_mmorf_regname",
            ),
            (
                os.path.join(native, f"{session}.{h}.sphere.{regnameorig}.native.surf.gii"),
                "set hcp_mmorf_regnameorig, which is reg.reg_LR after hcp_regname=FS",
            ),
        ]
        for kind in ("sphere", "flat"):
            inputs.append((
                os.path.join(nonlin, f"{session}.{h}.{kind}.{hires}k_fs_LR.surf.gii"),
                "set hcp_hiresmesh to a mesh hcp_post_freesurfer built",
            ))
            inputs += [
                (
                    os.path.join(nonlin, f"fsaverage_LR{m}k", f"{session}.{h}.{kind}.{m}k_fs_LR.surf.gii"),
                    "set hcp_lowresmesh to meshes hcp_post_freesurfer built",
                )
                for m in _low_meshes(options)
            ]
    return inputs


def _check_diffusion_mesh(session: str, options: dict, hcp: dict, _log) -> bool:
    """
    A diffusion mesh must be new and have HCP's atlas files.

    The script copies and resamples into its folder without looking, so one that
    hcp_post_freesurfer built would have that command's files overwritten. The
    midthickness surface tells them apart: the script writes its own under
    MMORFNonLinear, so its rerun on the same mesh is not rejected.
    """
    mesh = mu.effective(options, "hcp_mmorf_diffusionmesh")
    if not mesh.isdigit():
        _log.error(f"hcp_mmorf_diffusionmesh must be a number, got {mesh}!")
        return False

    built = os.path.join(
        hcp["hcp_nonlin"], f"fsaverage_LR{mesh}k", f"{session}.L.midthickness.{mesh}k_fs_LR.surf.gii"
    )
    if mesh == mu.effective(options, "hcp_hiresmesh") or mesh in _low_meshes(options) or os.path.exists(built):
        _log.error(f"hcp_mmorf_diffusionmesh {mesh} is also a mesh hcp_post_freesurfer built, hcp_post_mmorf would overwrite its files!")
        return False

    atlases = os.path.join(hcp["hcp_Templates"], "standard_mesh_atlases")
    hint = "HCP Pipelines have no atlas for this hcp_mmorf_diffusionmesh"
    inputs = [
        (os.path.join(hcp["hcp_Templates"], "surface-only_cifti", f"CortexOnly.{mesh}k_fs_LR.dscalar.nii"), hint)
    ]
    for h in ("L", "R"):
        inputs += [
            (os.path.join(atlases, name), hint)
            for name in (
                f"{h}.sphere.{mesh}k_fs_LR.surf.gii",
                f"{h}.atlasroi.{mesh}k_fs_LR.shape.gii",
                f"colin.cerebral.{h}.flat.{mesh}k_fs_LR.surf.gii",
            )
        ]
    return mu.check_inputs(inputs, _log=_log)
