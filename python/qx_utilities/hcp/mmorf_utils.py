#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``mmorf_utils.py``

What the HCP MMORF commands (hcp_pre_mmorf, hcp_mmorf, hcp_post_mmorf) share:
the checks every step makes, the paths more than one step needs, and the one
run and dry run flow, so the --test contract is kept in a single place.
"""

import os
import os.path
import shutil
from typing import Callable, NamedTuple, Optional

import qx_utilities.general.exceptions as ge
import qx_utilities.processing.core as pc
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.hcp.hcp_utils import do_hcp_options_check

MMORF_FOLDER = "MMORFNonLinear"

T1_TEMPLATE = "MMORF_T1_0.7mm.nii.gz"

TEMPLATE_HINT = "set its option or use HCP Pipelines that include the MMORF templates"

# the defaults of PostMMORFPipeline.sh for the flags QuNex leaves to it. These
# are never passed: an unset option stays off the command line, as does a mesh
# that is the default, so HCP's own default applies. They only tell the checks
# and the completion file which value will be in effect. tests/test_hcp_mmorf.py holds them to the script wherever
# HCP Pipelines with the chain are installed, which the CI workflow does not have
UPSTREAM_POST_DEFAULTS = {
    "hcp_hiresmesh": "164",
    "hcp_lowresmesh": "32",
    "hcp_mmorf_diffusionmesh": "79",
    "hcp_mmorf_regname": "MSMAll",
    "hcp_mmorf_regnameorig": "MSMSulc",
}


class MmorfStep(NamedTuple):
    """What a command's plan function hands to :func:`run_step`."""

    run: bool
    command: str
    test_file: str
    stale: list
    # a test_file older than this is not taken as finished without an overwrite
    newer_than: Optional[str] = None


def effective(options: dict, option: str) -> str:
    """The value in effect for a post flag: the option's, else HCP's default."""
    value = options[option]
    return UPSTREAM_POST_DEFAULTS[option] if value in (None, "") else str(value)


def session_name(sinfo: dict, options: dict) -> str:
    """The session as the HCP scripts name it."""
    return sinfo["id"] + options["hcp_suffix"]


def session_flags(sinfo: dict, options: dict) -> list:
    """The two flags every MMORF script takes."""
    return [("study-folder", sinfo["hcp"]), ("session", session_name(sinfo, options))]


def mmorf_folder(hcp: dict) -> str:
    return os.path.join(hcp["base"], MMORF_FOLDER)


def xfms_folder(hcp: dict) -> str:
    return os.path.join(mmorf_folder(hcp), "xfms")


def diffusion_folder(hcp: dict) -> str:
    return os.path.join(hcp["T1w_folder"], "Diffusion")


def template(options: dict, hcp: dict, option: str, filename: str) -> str:
    """The image an option names, else the HCP template of that name."""
    return options[option] or os.path.join(hcp["hcp_Templates"], filename)


def build_command(hcp: dict, script: str, elements: list) -> str:
    """The pipeline's command line. A value of None or a blank one stays off it."""
    flags = " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])
    return "%s %s" % (os.path.join(hcp["hcp_base"], "MMORF", script), flags)


def pre_outputs(hcp: dict) -> list:
    """What hcp_pre_mmorf writes and the later steps read, for check_chain_inputs."""
    return [
        (os.path.join(diffusion_folder(hcp), "data_tensor.nii.gz"), "hcp_pre_mmorf"),
        (os.path.join(xfms_folder(hcp), "acpc2MMORFLinear.mat"), "hcp_pre_mmorf"),
    ]


def post_test_file(sinfo: dict, options: dict, hcp: dict) -> str:
    """
    The last file hcp_post_mmorf writes.

    The final loop of PostMMORF_generateSurfaceFiles.sh ends with `thickness`,
    then `MRcorrThickness`, which it skips when the native file is missing. It
    sits outside MMORFNonLinear, so all three commands remove it on overwrite:
    otherwise a rerun of an earlier step would leave hcp_post_mmorf finished.
    It is named from the options of the command running, so hcp_post_mmorf
    also compares its age with the warp, for one an earlier step missed.
    """
    session = session_name(sinfo, options)
    regname = effective(options, "hcp_mmorf_regname")
    mesh = effective(options, "hcp_mmorf_diffusionmesh")
    native = os.path.join(
        hcp["hcp_nonlin"], "Native", f"{session}.MRcorrThickness.native.dscalar.nii"
    )
    stem = "MRcorrThickness" if os.path.exists(native) else "thickness"
    return os.path.join(
        hcp["hcp_nonlin"],
        f"fsaverage_LR{mesh}k",
        f"{session}.{stem}_{regname}.{mesh}k_fs_LR.dscalar.nii",
    )


def check_inputs(inputs: list, *, _log) -> bool:
    """
    Report every missing input of `(path, hint)`, rather than only the first.

    For files that come from outside the chain, which a dry run needs as much
    as a real one.
    """
    ok = True
    for path, hint in inputs:
        ok = pc.check_for_file(
            path, bad=f"{path} not found, {hint}!", status=ok, bad_level="error", _log=_log
        )
    return ok


def check_chain_inputs(inputs: list, options: dict, *, _log) -> bool:
    """
    Check the `(path, step)` files an earlier MMORF step writes.

    A dry run of that step wrote nothing, so a dry run here reports the file and
    carries on to name its tool. A real run can not do without the file.
    """
    ok = True
    for path, step in inputs:
        if os.path.exists(path):
            continue
        if options["run"] == "run":
            _log.error(f"{path} not found, run {step} first!")
            ok = False
        else:
            _log.warning(f"{path} not found, {step} would write it.")
    return ok


def _check_chain(options: dict, hcp: dict, _log) -> bool:
    """The checks of every MMORF step: all of it is hardcoded in the HCP scripts."""
    ok = True

    species = options["hcp_species"]
    if species and species.lower() != "human":
        _log.error(f"hcp_species is {species}, the MMORF scripts and templates support human data only!")
        ok = False

    if options["longitudinal"]:
        _log.error("longitudinal is set, the MMORF scripts only read the cross-sectional T1w folder!")
        ok = False

    if options["hcp_dwi_name"] not in (None, "Diffusion"):
        _log.error(f"hcp_dwi_name is {options['hcp_dwi_name']}, the MMORF scripts only read T1w/Diffusion!")
        ok = False

    t1w = hcp["T1w_folder"]
    return check_inputs(
        [
            (os.path.join(t1w, "T1w_acpc_dc_restore.nii.gz"), "run hcp_pre_freesurfer first"),
            (os.path.join(t1w, "T2w_acpc_dc_restore.nii.gz"), "MMORF requires a T2w image"),
        ],
        _log=_log,
    ) and ok


def _remove_stale(paths: list, options: dict, *, _log) -> None:
    """Remove what an overwrite invalidates, or under --test say what would go."""
    for path in paths:
        if not os.path.lexists(path):
            continue
        if options["run"] != "run":
            _log.detail(f"test, not removed: {path}")
            continue
        _log.step(f"removing preexisting {path}")
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def _is_current(step: MmorfStep, *, _log) -> bool:
    """Whether a finished step still holds: what it read has not been rewritten."""
    if step.newer_than is None or not os.path.exists(step.test_file) or not os.path.exists(step.newer_than):
        return True
    if os.path.getmtime(step.test_file) >= os.path.getmtime(step.newer_than):
        return True
    _log.error(f"{step.test_file} is older than {step.newer_than}, an earlier step has run since, use --overwrite=yes!")
    return False


def run_step(
    sinfo: dict,
    options: dict,
    overwrite: bool,
    command: str,
    title: str,
    name: str,
    plan: Callable,
) -> SessionLog:
    """
    Run one step of the chain, or under --test report what it would do.

    Nothing is removed unless every check has passed.

    Parameters:
        sinfo: the session information.
        options: the command's options.
        overwrite: whether to overwrite existing results.
        command: the QuNex command.
        title: the name in the opening line of the report.
        name: the name in the summary and the closing line.
        plan: `plan(sinfo, options, hcp, _log)` makes the command's own checks
            and returns its :class:`MmorfStep`.

    Returns:
        The session's log.
    """
    log = SessionLog(sinfo, options, title)
    report = f"{name} failed"
    failed = 1

    try:
        pc.do_options_check(options, sinfo, command)
        do_hcp_options_check(options, command)
        hcp = get_hcp_paths(sinfo, options)

        # both run in full, so one report names every problem
        ready = _check_chain(options, hcp, log)
        step = plan(sinfo, options, hcp, log)
        current = overwrite or _is_current(step, _log=log)

        if ready and step.run and current:
            log.pipeline_command(step.command)

            if overwrite:
                _remove_stale(step.stale, options, _log=log)

            if options["run"] == "run":
                _, report, failed = pc.run_external_for_file(
                    step.test_file,
                    step.command,
                    f"Running {name}",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    full_test=None,
                    shell=True,
                    _log=log,
                )

            # just checking
            else:
                passed, report, failed = pc.check_run(
                    step.test_file, None, name, overwrite=overwrite, _log=log
                )
                if passed is None:
                    log.step(f"{name} can be run")
                    report = f"{name} can be run"
                    failed = 0

        else:
            log.step("Session cannot be processed.")
            report = f"{name} cannot be run"
            failed = 1

    except ge.CommandFailed as e:
        log.command_failed(e, name)
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        failed = 1
    except Exception:
        log.unknown_error()
        failed = 1

    return log.finish(report, failed, pipeline=name)
