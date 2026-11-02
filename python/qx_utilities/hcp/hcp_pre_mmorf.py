#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``hcp_pre_mmorf.py``

The first step of the HCP MMORF chain.
"""

import os
import os.path
import re
from typing import Optional

import qx_utilities.hcp.mmorf_utils as mu
from qx_utilities.general.parsing import as_bool

# the b0 limit when hcp_dwi_b0maxbval is not set, which is what hcp_diffusion uses
_DEFAULT_B0MAX = 50

# b-values further apart than this are in different shells
_SHELL_GAP = 100

_NUMBER = re.compile(r"\d+(\.\d+)?")


def hcp_pre_mmorf(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_pre_mmorf [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run the first step of the HCP MMORF chain (PreMMORFPipeline.sh).

    ..  qx_command:
        type: processing.session

    Warning:
        The MMORF chain runs after the FreeSurfer chain, hcp_diffusion and
        hcp_msmall. It adds a registration to MMORF space beside the existing
        results and does not replace the FreeSurfer chain. It requires a T2w
        image and human data, has no longitudinal path and reads the diffusion
        data from T1w/Diffusion only, so a session outside of that is rejected.

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
            Whether to overwrite existing data (yes) or not (no). A new linear
            registration invalidates the later steps, so with 'yes' the whole
            MMORFNonLinear folder and the completion file of hcp_post_mmorf are
            removed before the run. Both hcp_mmorf and hcp_post_mmorf then have
            to be run again.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_folderstructure (str, default 'hcpls'):
            The HCP folder structure of the session, 'hcpya' or 'hcpls'.

        --hcp_mmorf_t1_brain_template (str, default HCP "MMORF_T1_0.7mm_brain.nii.gz"):
            The T1w brain template for the linear registration.

        --hcp_mmorf_lowest_shell_threshold (float, default detected):
            The b-value limit of the lowest diffusion shell. Volumes with a
            lower b-value are used for the tensor fit. When not set it is
            detected from T1w/Diffusion/bvals, as the lowest shell rounded to
            100 plus 200. A value set here is used as it is, with a warning
            when it does not separate the lowest shell from the rest.

        --hcp_mmorf_gradnonlin (str, default detected):
            Whether to apply gradient nonlinearity correction to the tensor fit,
            yes or no. When not set it is 'yes' if
            T1w/Diffusion/grad_dev.nii.gz exists and 'no' otherwise.

        --hcp_dwi_b0maxbval (float, default 50):
            The highest b-value still taken as b0 when detecting the lowest
            shell. Shared with hcp_diffusion, never passed to the pipeline.

        --hcp_dwi_name (str, default 'Diffusion'):
            A session processed under another name is rejected, as the MMORF
            scripts only read T1w/Diffusion.

        --hcp_species (str, default 'Human'):
            A non-human species is rejected, as the MMORF scripts and templates
            support human data only.

        --longitudinal (flag, optional):
            Rejected if set, as the MMORF scripts have no longitudinal path.

    Output files:
        The linear registration in the MMORFNonLinear/xfms folder of the
        session's hcp folder, and the tensor fit of the lowest shell in the
        T1w/Diffusion folder (data_tensor.nii.gz and the other data_* images).
        The diffusion data itself is left as it is.

    Notes:
        hcp_pre_mmorf parameter mapping:

            ==================================== ==========================
            QuNex parameter                      HCPpipelines parameter
            ==================================== ==========================
            ``hcp_mmorf_t1_brain_template``      ``t1-brain-template``
            ``hcp_mmorf_lowest_shell_threshold`` ``lowest-shell-threshold``
            ``hcp_mmorf_gradnonlin``             ``gradnonlin``
            ==================================== ==========================

    Examples:
        Example run from the base study folder with test flag::

            qunex hcp_pre_mmorf \\
                --studyfolder="." \\
                --batchfile="processing/batch.txt" \\
                --parsessions="4" \\
                --overwrite="no" \\
                --test

        Example run with a threshold set by hand::

            qunex hcp_pre_mmorf \\
                --studyfolder="<path_to_study_folder>" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_mmorf_lowest_shell_threshold="1200" \\
                --overwrite="yes" \\
                --scheduler="SLURM,time=04:00:00,cpus-per-task=2,mem-per-cpu=8000,partition=day"
    """

    return mu.run_step(
        sinfo,
        options,
        overwrite,
        "hcp_pre_mmorf",
        "HCP PreMMORF Pipeline",
        "HCP PreMMORF",
        _plan,
    )


def _plan(sinfo: dict, options: dict, hcp: dict, _log) -> mu.MmorfStep:
    """The checks and the command line of PreMMORFPipeline.sh."""
    diffusion = mu.diffusion_folder(hcp)
    brain_template = mu.template(
        options, hcp, "hcp_mmorf_t1_brain_template", "MMORF_T1_0.7mm_brain.nii.gz"
    )

    present = mu.check_inputs(
        [(os.path.join(hcp["T1w_folder"], "T1w_acpc_dc_restore_brain.nii.gz"), "run hcp_pre_freesurfer first")]
        + [
            (os.path.join(diffusion, e), "run hcp_diffusion first")
            for e in ("data.nii.gz", "bvals", "bvecs", "nodif_brain_mask.nii.gz")
        ]
        + [(brain_template, mu.TEMPLATE_HINT)],
        _log=_log,
    )
    threshold = _lowest_shell_threshold(os.path.join(diffusion, "bvals"), options, _log)
    gradnonlin = _gradnonlin(diffusion, options, _log)

    command = mu.build_command(
        hcp,
        "PreMMORFPipeline.sh",
        mu.session_flags(sinfo, options)
        + [
            ("t1-brain-template", brain_template),
            ("lowest-shell-threshold", threshold),
            ("gradnonlin", gradnonlin),
        ],
    )

    return mu.MmorfStep(
        present and threshold is not None and gradnonlin is not None,
        command,
        os.path.join(mu.xfms_folder(hcp), "T1w_acpc_dc_restore_to_MMORFLinear.nii.gz"),
        [mu.mmorf_folder(hcp), mu.post_test_file(sinfo, options, hcp)],
    )


def _shells(bvals: list, b0max: float) -> list:
    """The non-b0 values, sorted and split into shells."""
    shells = []
    for value in sorted(v for v in bvals if v > b0max):
        if shells and value - shells[-1][-1] <= _SHELL_GAP:
            shells[-1].append(value)
        else:
            shells.append([value])
    return shells


def _separates(threshold: float, shells: list) -> bool:
    """Whether `bval < threshold`, as the pipeline selects, is the lowest shell."""
    return shells[0][-1] < threshold and (len(shells) == 1 or threshold <= shells[1][0])


def _lowest_shell_threshold(path: str, options: dict, _log) -> Optional[str]:
    """
    The value of --lowest-shell-threshold, None if there is none to pass.

    HCP's script reports only an empty selection. It keeps every volume for a
    value that is not a number and a wrong shell for a wrong number, so a value
    is checked here. One set by hand is still used if it is a number.
    """
    manual = options["hcp_mmorf_lowest_shell_threshold"]
    if manual is not None and not _NUMBER.fullmatch(str(manual)):
        _log.error(f"hcp_mmorf_lowest_shell_threshold must be a number, got {manual}!")
        return None

    # a missing file is reported along with the other inputs
    if not os.path.exists(path):
        return None if manual is None else str(manual)

    try:
        with open(path) as f:
            lines = [e for e in f.read().splitlines() if e.strip()]
        # the script counts the volumes per line, so it would select the wrong ones
        if len(lines) > 1:
            _log.error(f"{path} has {len(lines)} lines, HCP's script needs the b-values on one!")
            return None
        bvals = [float(e) for e in " ".join(lines).split()]
        shells = _shells(bvals, float(options["hcp_dwi_b0maxbval"] or _DEFAULT_B0MAX))
    except ValueError as e:
        _log.error(f"could not work out the diffusion shells from {path}: {e}!")
        return None

    if manual is not None:
        threshold = str(manual)
        source = "set by hcp_mmorf_lowest_shell_threshold"
        if not shells or not _separates(float(threshold), shells):
            _log.warning(f"hcp_mmorf_lowest_shell_threshold {threshold} does not separate the lowest shell in {path}.")
    else:
        if not shells:
            _log.error(f"no diffusion volumes above b0 in {path}, set hcp_mmorf_lowest_shell_threshold!")
            return None
        detected = int(round(shells[0][0], -2)) + 200
        if not _separates(detected, shells):
            _log.error(f"could not detect the lowest shell in {path}, set hcp_mmorf_lowest_shell_threshold!")
            return None
        threshold = str(detected)
        source = f"detected from {path}"

    kept = sum(1 for v in bvals if v < float(threshold))
    _log.step(f"Lowest shell threshold {threshold}, {source}, keeping {kept} of {len(bvals)} volumes.")
    return threshold


def _gradnonlin(diffusion: str, options: dict, _log) -> Optional[str]:
    """The value of --gradnonlin, None if the option can not be used."""
    grad_dev = os.path.join(diffusion, "grad_dev.nii.gz")
    present = os.path.exists(grad_dev)
    manual = options["hcp_mmorf_gradnonlin"]

    if manual is None:
        value = present
        source = "found" if present else "did not find"
        source = f"{source} {grad_dev}"
    else:
        value = as_bool(manual)
        source = "set by hcp_mmorf_gradnonlin"
        if value is None:
            _log.error(f"hcp_mmorf_gradnonlin must be yes or no, got {manual}!")
            return None
        if value and not present:
            _log.error(f"hcp_mmorf_gradnonlin is set but {grad_dev} not found!")
            return None
        if present and not value:
            _log.warning(f"hcp_mmorf_gradnonlin is off although {grad_dev} exists.")

    flag = "TRUE" if value else "FALSE"
    _log.step(f"Gradient nonlinearity correction {flag}, {source}.")
    return flag
