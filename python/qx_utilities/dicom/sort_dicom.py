#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``sort_dicom.py``

The single pass DICOM scan and sort pipeline and the ``sort_dicom`` command.

Reads every member of a packet once, buckets instances into per sequence
records, writes the files into numbered acquisition folders and returns a
``sort_records.PackageSummary`` that ``import_dicom`` and the reporting
helpers consume.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import io
import os
import tempfile
import gzip as gz
from collections import Counter

import qx_utilities.dicom.sort_records as gds_records
import qx_utilities.dicom.sort_validate as gds_validate
from qx_utilities.dicom.dicom_archive import count_import_members, iter_import_members
from qx_utilities.dicom.dicom_info import _dicom_info_from_dataset, read_par_info
from qx_utilities.dicom.dicom_utils import clean_name

try:
    import pydicom
except Exception:
    import dicom as pydicom


# how often the scan reports progress, in DICOM files
_SCAN_PROGRESS_EVERY = 1000


    # a nonexistent source simply yields nothing


def _parse_member_dataset(data):
    """Parse in-memory bytes as a DICOM header, or return None if not DICOM."""
    try:
        d = pydicom.dcmread(
            io.BytesIO(data), stop_before_pixels=True, force=True, defer_size="1 KB"
        )
    except Exception:
        return None
    if not (
        getattr(d, "SOPInstanceUID", None)
        or getattr(d, "SeriesInstanceUID", None)
        or getattr(d, "Modality", None)
        or "SeriesNumber" in d
    ):
        return None
    return d


def _sequence_record_from_info(info, key):
    """Create a SequenceRecord from an extended read_dicom_info dictionary."""
    sid = info["seriesNumber"]
    return gds_records.SequenceRecord(
        key=key,
        sequence_id=str(sid) if sid is not None else "unknown",
        sequence_name=info["seriesDescription"],
        modality=info.get("modality", "unknown"),
        manufacturer=info.get("manufacturer", "unknown"),
        is_mosaic=info.get("is_mosaic", False),
        tr_ms=info["TR"] or None,
        te_ms=info["TE"] or None,
        rows=info.get("rows"),
        cols=info.get("cols"),
        pixel_spacing=info.get("pixel_spacing"),
        slice_thickness=info.get("slice_thickness"),
        spacing_between_slices=info.get("spacing_between_slices"),
        number_of_slices=info.get("number_of_slices"),
        images_in_acq=info.get("images_in_acq"),
        number_of_temporal_positions=info.get("number_of_temporal_positions"),
        number_of_frames=info.get("number_of_frames"),
        tags_for_hints=dict(info.get("hint_tags", {})),
        non_evaluable=gds_records.should_skip_sequence(info["seriesDescription"]),
        phase_encoding_direction=info.get("phase_encoding_direction", "unknown"),
        sense_factor=info.get("sense_factor"),
        multiband_factor=info.get("multiband_factor"),
    )


def _update_sequence_record(seq, info):
    """Fill still-unknown sequence fields from a later instance of the sequence."""
    for attr, key in (
        ("tr_ms", "TR"),
        ("te_ms", "TE"),
    ):
        if getattr(seq, attr) is None and info[key]:
            setattr(seq, attr, info[key])
    for attr in (
        "rows",
        "cols",
        "pixel_spacing",
        "slice_thickness",
        "spacing_between_slices",
        "number_of_slices",
        "images_in_acq",
        "number_of_temporal_positions",
        "sense_factor",
        "multiband_factor",
    ):
        if getattr(seq, attr) is None and info.get(attr) is not None:
            setattr(seq, attr, info.get(attr))
    frames = info.get("number_of_frames")
    if frames and (seq.number_of_frames is None or frames > seq.number_of_frames):
        seq.number_of_frames = frames
    if seq.phase_encoding_direction == "unknown":
        seq.phase_encoding_direction = info.get("phase_encoding_direction", "unknown")


def _instance_record_from_info(info, member_name):
    return gds_records.InstanceRecord(
        member_name=member_name,
        sop_uid=info["SOPInstanceUID"] or "unknown",
        instance_number=info.get("instance_number"),
        temporal_position=info.get("temporal_position"),
        acquisition_number=info.get("acquisition_number"),
        in_stack_position=info.get("in_stack_position"),
        image_position=info.get("image_position"),
        dt=info.get("acq_datetime"),
        echo_time_ms=info["TE"] or None,
        is_imaging=info.get("is_imaging", False),
        frame_count=info.get("number_of_frames") or 1,
    )


def _write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def _unique_name(base, used):
    """Return `base` (or `base` with a numeric suffix) not present in `used`."""
    name = base
    stem, ext = os.path.splitext(base)
    i = 1
    while name in used:
        i += 1
        name = f"{stem}-{i}{ext}"
    used.add(name)
    return name


def _place_par_rec(par_members, dicom_dir, session_id, verbose):
    """Sort buffered PAR/REC pairs into their sequence folders using read_par_info."""
    for base, parts in par_members.items():
        if "PAR" not in parts:
            continue
        tmp = tempfile.NamedTemporaryFile(prefix="import_par_", suffix=".PAR", delete=False)
        try:
            tmp.write(parts["PAR"])
            tmp.close()
            info = read_par_info(tmp.name)
        except Exception:
            os.remove(tmp.name)
            continue
        os.remove(tmp.name)

        if info["seriesNumber"] is None:
            continue
        sqid = str(info["seriesNumber"] * 10)
        seq_dir = os.path.join(dicom_dir, sqid)
        stem = "%s-%s-%s" % (clean_name(session_id), sqid, clean_name(base))
        _write_bytes(os.path.join(seq_dir, stem + ".PAR"), parts["PAR"])
        if "REC" in parts:
            _write_bytes(os.path.join(seq_dir, stem + ".REC"), parts["REC"])
        elif verbose:
            print("---> Warning: no REC file found for %s" % (base))


def _scan_and_sort_session(
    sources,
    dicom_dir,
    session_id,
    tr_abs_ms=100.0,
    tr_rel_pct=5.0,
    min_images=4,
    verbose=True,
):
    """
    Single read pass over ``sources`` that sorts and analyses a session's files.

    ``sources`` is one path or a list of paths (a session inbox may hold several
    packages). Each member is read once and written once: imaging DICOMs go to
    ``dicom/<seriesNumber*10>``, non-image DICOMs to ``dicom/non-image``, PAR/REC
    pairs to their sequence folders, and ``.log`` files to ``dicom/log``. Per
    sequence records are built during the pass; afterwards completeness is
    analysed (scanner-aware, decision D1) and orphaned incomplete-volume files
    are moved to ``dicom/orphans`` with a cheap rename (no re-read).

    Returns a ``sort_records.PackageSummary`` describing the session.
    """
    if isinstance(sources, (str, bytes, os.PathLike)):
        sources = [sources]

    os.makedirs(dicom_dir, exist_ok=True)
    non_image_dir = os.path.join(dicom_dir, "non-image")
    orphans_dir = os.path.join(dicom_dir, "orphans")
    log_dir = os.path.join(dicom_dir, "log")

    pkg = gds_records.PackageSummary(
        package_name=os.path.basename(str(sources[0])) if sources else session_id,
        session_id=session_id,
    )
    sequence_map = {}
    written_path = {}
    par_members = {}
    used_names = set()
    dcmn = 0

    # member total drives the progress percentage; None when it is not cheap to
    # get (a tar), in which case progress falls back to a plain running count
    total_expected = 0
    for source in sources:
        n = count_import_members(source)
        if n is None:
            total_expected = None
            break
        total_expected += n

    if verbose:
        print("---> Inspecting and sorting package content for %s" % (session_id), flush=True)
        for source in sources:
            print("     ... source: %s" % (source), flush=True)
        if total_expected:
            print("     ... %d member(s) to inspect" % (total_expected), flush=True)

    seen = 0
    step = max(1, (total_expected or 0) // 50)

    for source in sources:
        for name, data in iter_import_members(source):
            seen += 1
            if verbose:
                if total_expected:
                    if seen % step == 0:
                        print(
                            "\r     ... scanning %s"
                            % (gds_records.format_progress(seen, total_expected)),
                            end="",
                            flush=True,
                        )
                elif seen % _SCAN_PROGRESS_EVERY == 0:
                    print(
                        "     ... %d member(s) scanned, %d sequence(s) so far"
                        % (seen, len(sequence_map)),
                        flush=True,
                    )
            bn = os.path.basename(name)
            if bn[:4] in ("XX_0", "PS_0"):
                continue
            if bn.lower().endswith(".gz"):
                try:
                    data = gz.decompress(data)
                except Exception:
                    pass
                bn = bn[:-3]
            ext = bn.rsplit(".", 1)[-1].lower() if "." in bn else ""

            if ext == "log":
                _write_bytes(os.path.join(log_dir, bn), data)
                continue
            if ext in ("par", "rec"):
                par_members.setdefault(bn[:-4], {})[ext.upper()] = data
                continue

            pkg.total_members += 1
            d = _parse_member_dataset(data)
            if d is None:
                pkg.parse_errors += 1
                continue
            info = _dicom_info_from_dataset(d, os.path.splitext(bn)[0], extended=True)

            sid = info["seriesNumber"]
            if sid is None:
                if verbose:
                    print("---> Skipping file with no series number: %s" % (name))
                continue

            pkg.total_dicom += 1
            _update_package_metadata(pkg, d)

            key = str(sid)
            if key not in sequence_map:
                sequence_map[key] = _sequence_record_from_info(info, key)
            seq = sequence_map[key]
            _update_sequence_record(seq, info)

            inst = _instance_record_from_info(info, name)
            seq.instances.append(inst)
            if inst.is_imaging:
                seq.imaging_dicom_count += 1
            else:
                seq.non_imaging_dicom_count += 1
            if inst.is_imaging and (info.get("number_of_frames") or 0) > 1 and info.get("enhanced_volume_map"):
                for vidx, slices in info["enhanced_volume_map"].items():
                    seq.enhanced_volume_to_slices.setdefault(vidx, set()).update(slices)

            dcmn += 1
            sop = info["SOPInstanceUID"] or "%010d" % dcmn
            sqid = str(sid * 10)
            fname = _unique_name(
                "%s-%s-%s.dcm" % (clean_name(session_id), sqid, clean_name(sop)), used_names
            )
            dest_dir = os.path.join(dicom_dir, sqid) if inst.is_imaging else non_image_dir
            dest = os.path.join(dest_dir, fname)
            _write_bytes(dest, data)
            written_path[name] = dest

    if verbose:
        if total_expected:
            # close the in-place bar on a full line. `seen` can exceed the count
            # when the package holds nested archives, so widen the total rather
            # than render a bar past 100%
            print(
                "\r     ... scanning %s"
                % (gds_records.format_progress(seen, max(total_expected, seen))),
                flush=True,
            )
        print(
            "---> Inspected %d file(s): %d DICOM in %d sequence(s), %d unreadable"
            % (pkg.total_members, pkg.total_dicom, len(sequence_map), pkg.parse_errors),
            flush=True,
        )

    _place_par_rec(par_members, dicom_dir, session_id, verbose)

    _finalise_sequences(pkg, sequence_map, written_path, orphans_dir, tr_abs_ms, tr_rel_pct, min_images, verbose)
    return pkg


def _update_package_metadata(pkg, d):
    """Fill still-unknown package-level metadata from a DICOM dataset."""
    def pick(current, value):
        return current if current != "unknown" else gds_records.fmt(value)

    pkg.participant_name = pick(pkg.participant_name, getattr(d, "PatientName", None))
    pkg.participant_code = pick(pkg.participant_code, getattr(d, "PatientID", None))
    pkg.study_date = pick(pkg.study_date, getattr(d, "StudyDate", None))
    pkg.study_time = pick(pkg.study_time, getattr(d, "StudyTime", None))
    pkg.scanner_manufacturer = pick(pkg.scanner_manufacturer, getattr(d, "Manufacturer", None))
    pkg.scanner_model = pick(pkg.scanner_model, getattr(d, "ManufacturerModelName", None))
    pkg.scanner_field_strength = pick(pkg.scanner_field_strength, getattr(d, "MagneticFieldStrength", None))
    pkg.location = pick(
        pkg.location, getattr(d, "InstitutionName", None) or getattr(d, "StationName", None)
    )


def _finalise_sequences(pkg, sequence_map, written_path, orphans_dir, tr_abs_ms, tr_rel_pct, min_images, verbose):
    """Analyse completeness, relocate orphaned files, and tally the verdict."""
    pkg.sequences = sorted(
        sequence_map.values(),
        key=lambda s: (
            gds_records.to_int(s.sequence_id) if gds_records.to_int(s.sequence_id) is not None else float("inf"),
            s.sequence_name,
        ),
    )
    gds_validate.infer_missing_phase_polarity(pkg.sequences)

    mr_sequences = [s for s in pkg.sequences if s.modality.upper() == "MR" and s.imaging_dicom_count > 0]
    pkg.no_data_sequences = sum(
        1 for s in pkg.sequences if s.modality.upper() == "MR" and s.imaging_dicom_count == 0
    )

    for seq in mr_sequences:
        if seq.non_evaluable:
            seq.status = "SKIP"
            continue
        gds_validate.validate_sequence(seq, tr_abs_ms=tr_abs_ms, tr_rel_pct=tr_rel_pct)
        _, _, orphaned = gds_validate.classify_sequence_files(seq, min_images=min_images)
        for member_name in orphaned:
            src = written_path.get(member_name)
            if src and os.path.exists(src):
                dst = os.path.join(orphans_dir, os.path.basename(src))
                os.makedirs(orphans_dir, exist_ok=True)
                os.rename(src, dst)
        if orphaned and verbose:
            print("---> Sequence %s: moved %d orphaned file(s) to orphans/" % (seq.sequence_id, len(orphaned)))

    eval_sequences = [s for s in mr_sequences if not s.non_evaluable]
    statuses = Counter(s.status for s in eval_sequences)
    if statuses.get("FAIL", 0):
        pkg.verdict = "FAIL"
    elif statuses.get("WARN", 0):
        pkg.verdict = "WARN"
    elif not mr_sequences:
        pkg.verdict = "NOT_MR"
    else:
        pkg.verdict = "PASS"
    pkg.good_sequences = sum(1 for s in eval_sequences if s.status == "PASS")
    pkg.incomplete_sequences = sum(1 for s in eval_sequences if s.status == "WARN")
    pkg.error_sequences = sum(1 for s in eval_sequences if s.status == "FAIL")


def sort_dicom(folder=".", copy="move", outdir=None, files=None):
    """
    ``sort_dicom [folder=.] [outdir=<folder>] [files=<comma-separated list>]``

    Sorts DICOM (and PAR/REC) files into per-sequence ``dicom`` subfolders.

    ..  qx_command:
        type: utility

    Parameters:
        --folder (str, default '.'):
            The base session folder that contains the ``inbox`` subfolder with
            the unsorted DICOM files.

        --copy (str, default 'move'):
            Accepted for backward compatibility but ignored, the files are
            always copied and the ``inbox`` folder is left intact.

        --outdir (str, default detailed below):
            Optional directory in which the ``dicom`` folder is created.
            Defaults to the `folder` parameter if not set.

        --files (str, default detailed below):
            Optional comma separated list of files to sort. Defaults to the
            contents of ``<folder>/inbox``.

    Notes:
        This is a thin wrapper over the single-pass import engine. In one read
        pass it sorts imaging DICOMs into ``dicom/<seriesNumber*10>``, sets aside
        non-image DICOMs (``dicom/non-image``) and incomplete-volume/orphan
        slices (``dicom/orphans``) using scanner-aware heuristics, places PAR/REC
        pairs in their sequence folders and log files in ``dicom/log``. Unlike
        the legacy command it copies rather than moves, so the ``inbox`` is left
        intact; the ``copy`` argument is therefore accepted but ignored.

    Examples:
        ::

            qunex sort_dicom --folder=OP667
    """
    print("Running sort_dicom\n=================")
    dicom_dir = os.path.join(outdir or folder, "dicom")
    if files:
        sources = [e.strip() for e in files.split(",")]
    else:
        sources = [os.path.join(folder, "inbox")]
    session_id = os.path.basename(os.path.abspath(folder))
    pkg = _scan_and_sort_session(sources, dicom_dir, session_id, verbose=True)
    print("---> Done")
    return pkg
