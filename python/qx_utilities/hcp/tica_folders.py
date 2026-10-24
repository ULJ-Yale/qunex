# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``tica_folders.py``

The folders of an hcp_temporal_ica run: the study dir tICAPipeline.sh runs in,
the sessions linked into it, and the group folder, which is the average
dataset the run reads and the folder its group results are written into.
Which steps of tICAPipeline.sh a run goes through decides what the group
folder has to hold.
"""

import os
import os.path

import qx_utilities.general.core as gc
from qx_utilities.general.log import SessionLog


def average_wmparc(folder: str, group: str) -> str:
    """
    The file of an average dataset tICA reads: ComputeTICAFeatures
    (brain_masks.sh) reads <group folder>/MNINonLinear/<group>_Averagewmparc.nii.gz,
    which MakeAverageDataset.sh writes whatever its registration and meshes.
    """
    return os.path.join(folder, "MNINonLinear", f"{group}_Averagewmparc.nii.gz")


# the steps of tICAPipeline.sh, in the order it runs them
TICA_STEPS = (
    "MIGP",
    "GroupSICA",
    "indProjSICA",
    "ConcatGroupSICA",
    "ComputeGroupTICA",
    "indProjTICA",
    "ComputeTICAFeatures",
    "ClassifyTICA",
    "CleanData",
)


def tica_mode(options: dict) -> str:
    """The --ica-mode of the run: NEW by default, REUSE_TICA when longitudinal."""
    if options["hcp_tica_icamode"]:
        return options["hcp_tica_icamode"]
    return "REUSE_TICA" if options["longitudinal"] else "NEW"


def tica_steps(options: dict) -> tuple[str, ...]:
    """
    The steps the run goes through, from --hcp_tica_starting_step to
    --hcp_tica_stop_after_step, with the defaults of tICAPipeline.sh. All of
    them when either is not a step, which the script refuses.
    """
    start = options["hcp_tica_starting_step"] or TICA_STEPS[0]
    stop = options["hcp_tica_stop_after_step"] or TICA_STEPS[-1]
    if start not in TICA_STEPS or stop not in TICA_STEPS:
        return TICA_STEPS
    return TICA_STEPS[TICA_STEPS.index(start) : TICA_STEPS.index(stop) + 1]


def reads_average_wmparc(options: dict) -> bool:
    """
    Whether the run reads the average dataset, see `average_wmparc`: only
    ComputeTICAFeatures does, which REUSE_TICA skips.
    """
    return tica_mode(options) != "REUSE_TICA" and "ComputeTICAFeatures" in tica_steps(options)


def writes_group_folder(options: dict) -> bool:
    """
    Whether a step of the run writes into the group folder: indProjSICA (the
    volume template), ConcatGroupSICA and ComputeGroupTICA in every mode,
    MIGP and GroupSICA when the sICA is estimated (NEW), and
    ComputeTICAFeatures unless REUSE_TICA skips it. indProjTICA and CleanData
    write into the sessions.
    """
    mode = tica_mode(options)
    writes = {"indProjSICA", "ConcatGroupSICA", "ComputeGroupTICA"}
    if mode == "NEW":
        writes |= {"MIGP", "GroupSICA"}
    if mode != "REUSE_TICA":
        writes.add("ComputeTICAFeatures")
    return bool(writes.intersection(tica_steps(options)))


def is_average_dataset(_log: SessionLog, options: dict, folder: str, group: str) -> bool:
    """
    Check that a named average dataset holds the file of the group that the
    run reads. A folder that does not exist is not checked: a run reports it
    when it links it in, a dry run passes over it.

    Returns:
        bool: False when the run would read a file the dataset does not hold.
    """
    if not os.path.exists(folder) or not reads_average_wmparc(options):
        return True
    wmparc = average_wmparc(folder, group)
    if os.path.exists(wmparc):
        return True
    _log.error(
        f"{wmparc} does not exist: --hcp_tica_average_dataset is the folder "
        f"that holds MNINonLinear, made with --hcp_outgroupname={group}!"
    )
    inner = os.path.join(folder, group)
    if os.path.exists(average_wmparc(inner, group)):
        _log.error(f"{inner} holds it, it is probably the folder meant!")
    return False


def make_group_folder(
    _log: SessionLog,
    options: dict,
    study_dir: str,
    group: str,
    average_dataset: str | None,
    earlier: list[str] | None = None,
) -> bool:
    """
    Make the group folder of a run that has one of its own, with the
    MNINonLinear a REUSE mode writes into without making it, unless an average
    dataset is linked in its place. A link at the group folder that dangles,
    or that points to one of the `earlier` folders, is replaced by the folder.

    Returns:
        bool: False when the link could not be removed.
    """
    if not group or average_dataset is not None:
        return True
    group_dir = os.path.join(study_dir, group)
    mni = os.path.join(group_dir, "MNINonLinear")
    if os.path.islink(group_dir):
        target = os.readlink(group_dir)
        replaced = not os.path.exists(group_dir) or any(
            os.path.exists(folder) and os.path.samefile(group_dir, folder)
            for folder in earlier or []
        )
        if replaced and options["run"] != "run":
            _log.detail(f"test, not removed: {group_dir} -> {target}")
            _log.detail(f"test, not created: {mni}")
            return True
        if replaced:
            try:
                os.unlink(group_dir)
            except OSError as e:
                _log.error(f"{group_dir} could not be removed: {e}")
                return False
            _log.detail(f"removed link: {group_dir} -> {target}, the group folder is made in its place")
    make_folder(_log, options, mni)
    return True


def make_folder(_log: SessionLog, options: dict, folder: str) -> None:
    """Create a folder of the tICA study dir, or under --test say it would be."""
    if os.path.exists(folder):
        return
    if options["run"] == "run":
        os.makedirs(folder)
    else:
        _log.detail(f"test, not created: {folder}")


def link_folder(_log: SessionLog, options: dict, source: str, target: str) -> bool:
    """
    Symlink a folder into the tICA study dir, or under --test say it would be.
    The source is linked by its absolute path. A link left dangling at the
    target is replaced, and so is a folder that holds no files, such as the
    empty <group>/MNINonLinear earlier versions made where the average dataset
    is linked now; any other folder at the target is an error. Under --test a
    link already in place and a source that does not exist are not reported;
    a run reports the missing source as an error and leaves the target as it
    is.

    Returns:
        bool: False when the link could not be made.
    """
    source = os.path.abspath(source)
    if os.path.isdir(target) and not os.path.islink(target):
        if os.path.exists(source) and os.path.samefile(source, target):
            return True
        if not _holds_nothing(target):
            _log.error(f"{target} is a folder, cannot link {source} in its place! Move it out of the way.")
            return False
        if os.path.exists(source):
            if options["run"] != "run":
                _log.detail(f"test, not removed: {target}")
            elif not _remove_empty_folder(_log, target):
                return False

    if options["run"] != "run":
        if os.path.exists(source) and not (
            os.path.exists(target) and os.path.samefile(source, target)
        ):
            _log.detail(f"test, not linked: {target} -> {source}")
        return True

    if os.path.islink(target) and not os.path.exists(target):
        os.unlink(target)
    return gc.link_or_copy(source, target, name=target, symlink=True, _log=_log)


def _holds_nothing(folder: str) -> bool:
    """
    True when a folder holds nothing but empty folders: no files, no links,
    and no folder that could not be read.
    """
    unreadable = []
    for root, dirs, files in os.walk(folder, onerror=unreadable.append):
        if files or any(os.path.islink(os.path.join(root, d)) for d in dirs):
            return False
    return not unreadable


def _remove_empty_folder(_log: SessionLog, folder: str) -> bool:
    """
    Remove a folder that holds nothing but empty folders, see `_holds_nothing`.

    Returns:
        bool: False when it could not be removed.
    """
    try:
        for subfolder, _, _ in os.walk(folder, topdown=False):
            os.rmdir(subfolder)
    except OSError as e:
        _log.error(f"{folder} could not be removed: {e}")
        return False
    _log.detail(f"removed empty folder: {folder}")
    return True
