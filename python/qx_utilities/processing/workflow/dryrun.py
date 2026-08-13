#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``workflow/dryrun.py``

The side-effect guards the package's commands share, and the MATLAB command
they are run with.

A call site reads ``dryrun.run_external(...)``: the module is imported rather
than the names, so the qualifier says where the helper comes from and, for
``dryrun.remove`` sitting next to ``os.remove``, that this one honours
``--test``.
"""

import os
import shutil

import qx_utilities.processing.core as pc
import qx_utilities.general.core as gc


if "QUNEXMCOMMAND" not in os.environ:
    # import time, before any command and therefore any log exists: this one
    # stays a print (group C's frame, not group A's report)
    print(
        "WARNING: QUNEXMCOMMAND environment variable not set. Matlab will be run by default!"
    )
    mcommand = "matlab -nojvm -nodisplay -nosplash -r"
else:
    mcommand = os.environ["QUNEXMCOMMAND"]


# --------------------------------------------------------------- the dry run
#
# Five commands in this file -- `get_bold_data`, `create_bold_brain_masks`,
# `compute_bold_stats`, `create_stats_report` and `extract_nuisance_signal` --
# never consulted `options["run"]`, so `--test` did the work: it copied and
# linked files, invoked external tools, and deleted existing reports before
# regenerating them. `preprocess_bold` and `preprocess_conc` did guard the one
# matlab call each makes, but fell silent about it instead of naming it, and
# `preprocess_conc` copied its conc and event files in and rewrote the conc
# regardless of the flag.
#
# The four helpers below are the same guard for the side effects the commands
# repeat, spelled once instead of at 30 sites, and they follow
# `processing/fs.py`'s: a dry run reports what it *would* do rather than
# falling silent, so the report is worth reading. The one-off side effects --
# `gi.slice_image`, `os.makedirs`, `gm.meltmovfidl`, the file lock and the
# merged comlog -- are guarded where they sit.


def run_external(_log, options, checkfile, command, description, **kwargs):
    """
    Run one external command, or -- under ``--test`` -- report it and stop.

    Returns the underlying ``(endlog, status, failed)``. A dry run ran nothing
    and wrote no comlog, so it returns ``(None, None, 0)`` -- the shape the
    call sites unpack, rather than a bare None that would raise there.
    """
    if options["run"] != "run":
        _log.raw(f"\n\n{description}")
        _log.detail(f"test, not run: {command}", depth=1)
        return None, None, 0

    return pc.run_external_for_file(checkfile, command, description, **kwargs, _log=_log)


def link_or_copy(_log, options, source, target, **kwargs):
    """Link or copy a file, or -- under ``--test`` -- report it and change nothing."""
    if options["run"] != "run":
        _log.detail(f"test, not copied: {os.path.basename(source)}")
        return None

    return gc.link_or_copy(source, target, **kwargs)


def copy(_log, options, source, target):
    """Copy a file, or -- under ``--test`` -- report the copy and change nothing."""
    if options["run"] != "run":
        _log.detail(f"test, not copied: {os.path.basename(source)}")
        return

    shutil.copy2(source, target)


def remove(_log, options, path):
    """
    Delete a file, or -- under ``--test`` -- report the deletion and keep it.

    Only a file that is actually there is reported. Most of these are temporary
    files a dry run never created, and naming them would be noise; the ones
    worth naming are the existing outputs `create_stats_report` clears before
    regenerating them, which is the destructive step a dry run must not take.
    """
    if options["run"] != "run":
        if os.path.exists(path):
            _log.detail(f"test, not removed: {path}")
        return

    os.remove(path)
