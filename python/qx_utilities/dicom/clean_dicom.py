#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``clean_dicom.py``

The ``clean_dicom`` command: re-checks an already sorted session folder and
moves non-image and incomplete-volume DICOM files out of the acquisition
folders.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import os

import qx_utilities.dicom.sort_validate as gds_validate
import qx_utilities.general.log as gl
from qx_utilities.dicom.dicom_info import read_dicom_info
from qx_utilities.dicom.sort_dicom import (
    _instance_record_from_info,
    _sequence_record_from_info,
    _update_sequence_record,
)
from qx_utilities.general.parsing import true_or_false


def _move_files(paths, dest_dir):
    """Move ``paths`` into ``dest_dir``, adding a suffix on filename collisions."""
    if not paths:
        return 0
    os.makedirs(dest_dir, exist_ok=True)
    moved = 0
    for p in paths:
        if not os.path.exists(p):
            continue
        dst = os.path.join(dest_dir, os.path.basename(p))
        if os.path.exists(dst):
            base, ext = os.path.splitext(os.path.basename(p))
            i = 1
            while os.path.exists(dst):
                dst = os.path.join(dest_dir, f"{base}__dup{i}{ext}")
                i += 1
        os.rename(p, dst)
        moved += 1
    return moved


def _clean_sorted_dicom(folder, min_images, move_non_image, move_incomplete, verbose, _log=None):
    """Inspect already-sorted ``dicom/<seq>`` folders and set aside non-image and
    orphaned incomplete-volume files, reusing the shared classifier."""
    log = gl.log_or_console(_log)

    dicom_dir = os.path.join(folder, "dicom")
    if not os.path.isdir(dicom_dir):
        log.warning(f"DICOM folder not found: {dicom_dir}")
        log.step("Skipping clean_dicom")
        return

    non_image_dir = os.path.join(dicom_dir, "non-image")
    orphans_dir = os.path.join(dicom_dir, "orphans")
    seq_ids = sorted(
        (d for d in os.listdir(dicom_dir) if d.isdigit() and os.path.isdir(os.path.join(dicom_dir, d))),
        key=int,
    )
    for sqid in seq_ids:
        seq_dir = os.path.join(dicom_dir, sqid)
        seq = None
        for fn in sorted(os.listdir(seq_dir)):
            fp = os.path.join(seq_dir, fn)
            if not os.path.isfile(fp):
                continue
            try:
                info = read_dicom_info(fp, extended=True)
            except Exception:
                continue
            if info["seriesNumber"] is None:
                continue
            if seq is None:
                seq = _sequence_record_from_info(info, sqid)
            _update_sequence_record(seq, info)
            inst = _instance_record_from_info(info, fp)
            seq.instances.append(inst)
            if inst.is_imaging:
                seq.imaging_dicom_count += 1
            else:
                seq.non_imaging_dicom_count += 1
            if inst.is_imaging and (info.get("number_of_frames") or 0) > 1 and info.get("enhanced_volume_map"):
                for vidx, slices in info["enhanced_volume_map"].items():
                    seq.enhanced_volume_to_slices.setdefault(vidx, set()).update(slices)
        if seq is None:
            continue
        gds_validate.validate_sequence(seq, tr_abs_ms=100.0, tr_rel_pct=5.0)
        _, non_image, orphaned = gds_validate.classify_sequence_files(seq, min_images=min_images)
        n_ni = _move_files(non_image, non_image_dir) if move_non_image else 0
        n_or = _move_files(orphaned, orphans_dir) if move_incomplete else 0
        if verbose:
            log.step(
                f"Sequence {sqid}: {seq.imaging_dicom_count} image, moved {n_ni} non-image, {n_or} orphaned"
            )


def clean_dicom(
    folder=".",
    tol_mm=0.2,
    min_files=10,
    verbose="yes",
    move_non_image=True,
    move_incomplete=True,
    _log=None,
):
    r"""
    ``clean_dicom [folder=.] [min_files=10] [verbose=yes] [move_non_image=True] [move_incomplete=True]``

    Inspects already-sorted ``dicom/<seq>`` folders and sets aside DICOM files
    that hold no imaging data (to ``dicom/non-image``) or that belong to an
    incomplete volume (to ``dicom/orphans``), preventing conversion errors.

    ..  qx_command:
        type: utility

    Parameters:
        --folder (str, default '.'):
            The base session folder containing the ``dicom`` subfolder with
            sorted, numbered sequence subfolders.

        --min_files (int, default 10):
            Minimum number of imaging files a sequence must have for
            orphan-slice detection to run (shorter sequences are left intact).

        --verbose (str, default 'yes'):
            Whether to report per-sequence statistics.

        --move_non_image (bool, default True):
            Whether to move non-image DICOM files to ``dicom/non-image``.

        --move_incomplete (bool, default True):
            Whether to move incomplete-volume/orphan files to ``dicom/orphans``.

    Notes:
        This is a thin, robust re-implementation over the shared single-pass
        classifier. Detection is scanner-aware (decision D1): mosaic
        acquisitions and sequences whose slice geometry cannot be inferred are
        reported but never pruned. The ``tol_mm`` argument from the previous
        implementation is accepted for backward compatibility but no longer
        used (slice membership is derived from per-slice geometry keys, not mm
        clustering). Orphan files now go to ``dicom/orphans`` (previously
        ``dicom/_REMOVED``).
    """
    log = gl.log_or_console(_log)

    log.info("Running clean_dicom\n==================")
    verbose_b = true_or_false(verbose)
    try:
        min_images = int(min_files)
    except (TypeError, ValueError):
        min_images = 10
    _clean_sorted_dicom(
        folder,
        min_images,
        true_or_false(move_non_image),
        true_or_false(move_incomplete),
        verbose_b,
        _log=log,
    )
    log.step("Done")
