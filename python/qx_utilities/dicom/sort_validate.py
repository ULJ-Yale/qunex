#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``sort_validate.py``

Completeness analysis for scanned DICOM sequences.

Infers the expected slice and volume counts, estimates the repetition time,
validates a sequence against what was actually written and splits its
instances into complete and orphaned (incomplete volume) files. Also holds
the shared table renderer used by the report.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from qx_utilities.dicom.sort_records import (
    InstanceRecord,
    Issue,
    SequenceRecord,
    fmt,
    format_duration,
    sequence_type,
)
from qx_utilities.dicom.sort_tags import (
    opposite_phase_direction,
    parse_phase_token,
)


# ---------------------------------------------------------------------------
# completeness analysis
# ---------------------------------------------------------------------------


def get_slice_key(inst: InstanceRecord) -> Optional[str]:
    if inst.in_stack_position is not None:
        return f"stk:{inst.in_stack_position}"
    if inst.image_position is not None:
        x, y, z = inst.image_position
        return f"pos:{x:.2f}:{y:.2f}:{z:.2f}"
    if inst.instance_number is not None:
        return f"ins:{inst.instance_number}"
    return None


def infer_expected_slices(seq: SequenceRecord, imaging: List[InstanceRecord]) -> Optional[int]:
    if seq.enhanced_volume_to_slices:
        non_empty = [len(v) for v in seq.enhanced_volume_to_slices.values() if v]
        if non_empty:
            return max(non_empty)
    for candidate in (seq.number_of_slices, seq.images_in_acq):
        if candidate and candidate > 0:
            return candidate
    slice_keys = {get_slice_key(inst) for inst in imaging if get_slice_key(inst)}
    return len(slice_keys) if slice_keys else None


def infer_planned_volumes(seq: SequenceRecord, expected_slices: Optional[int]) -> Optional[int]:
    seq_type = sequence_type(seq.sequence_name)
    # diffusion/DKI: report directions (frames / slices) as planned volumes
    if seq_type == "DWI" and seq.number_of_frames and expected_slices and expected_slices > 0:
        return max(1, seq.number_of_frames // expected_slices)
    if seq.number_of_temporal_positions and seq.number_of_temporal_positions > 0:
        return seq.number_of_temporal_positions
    if seq.enhanced_volume_to_slices:
        return len(seq.enhanced_volume_to_slices)
    if seq.number_of_frames and seq.number_of_frames > 1 and expected_slices and expected_slices > 0:
        return max(1, seq.number_of_frames // expected_slices)
    return None


def assign_volume_index(inst: InstanceRecord, expected_slices: Optional[int]) -> int:
    if inst.temporal_position and inst.temporal_position > 0:
        return inst.temporal_position
    if inst.acquisition_number and inst.acquisition_number > 0:
        return inst.acquisition_number
    if expected_slices and expected_slices > 0 and inst.instance_number and inst.instance_number > 0:
        return ((inst.instance_number - 1) // expected_slices) + 1
    return 1


def estimate_tr_ms(vol_start_times: Dict[int, datetime]) -> Optional[float]:
    ordered = [t for _, t in sorted(vol_start_times.items())]
    if len(ordered) < 2:
        return None
    diffs_ms = [(ordered[i] - ordered[i - 1]).total_seconds() * 1000.0 for i in range(1, len(ordered))]
    try:
        return float(statistics.median(diffs_ms)) if diffs_ms else None
    except statistics.StatisticsError:
        return None


def validate_sequence(seq: SequenceRecord, tr_abs_ms: float, tr_rel_pct: float) -> None:
    """Populate completeness/timing fields and issues on ``seq`` in place.

    Scanner-aware (D1): mosaic and enhanced multi-frame acquisitions store a
    whole volume per file, so orphan-slice checks do not apply; when slice
    geometry cannot be reconstructed the sequence is reported, never pruned.
    Refined further in the write-phase step.
    """
    imaging = [inst for inst in seq.instances if inst.is_imaging]
    if not imaging:
        seq.issues.append(Issue("WARN", "No imaging DICOM instances in this sequence."))
        seq.status = "WARN"
        return

    expected_slices = infer_expected_slices(seq, imaging)
    seq.expected_slices = expected_slices
    seq.planned_volumes = infer_planned_volumes(seq, expected_slices)

    volume_to_slices: Dict[int, set] = defaultdict(set)
    volume_starts: Dict[int, datetime] = {}
    if seq.enhanced_volume_to_slices:
        for vidx, slices in seq.enhanced_volume_to_slices.items():
            volume_to_slices[vidx].update(f"stk:{sidx}" for sidx in slices)
    else:
        for inst in imaging:
            vidx = assign_volume_index(inst, expected_slices)
            skey = get_slice_key(inst)
            if skey:
                volume_to_slices[vidx].add(skey)
            if inst.dt is not None and (vidx not in volume_starts or inst.dt < volume_starts[vidx]):
                volume_starts[vidx] = inst.dt

    if volume_starts:
        seq.acq_start = min(volume_starts.values())
        seq.acq_end = max(volume_starts.values())
    else:
        dt_values = [inst.dt for inst in imaging if inst.dt is not None]
        if dt_values:
            seq.acq_start, seq.acq_end = min(dt_values), max(dt_values)

    complete = partial = missing_middle = 0
    if expected_slices and expected_slices > 0:
        last_vidx = max(volume_to_slices) if volume_to_slices else None
        for vidx in sorted(volume_to_slices):
            n = len(volume_to_slices[vidx])
            if n >= expected_slices:
                complete += 1
            elif n > 0:
                if vidx == last_vidx:
                    partial = n
                else:
                    missing_middle += 1
    else:
        complete = 1 if imaging else 0
    seq.good_volumes = complete
    seq.partial_volume_slices = partial

    if seq.acq_start is not None and seq.acq_end == seq.acq_start and seq.tr_ms and seq.good_volumes > 1:
        seq.acq_end = seq.acq_start + timedelta(milliseconds=(seq.good_volumes - 1) * seq.tr_ms)

    if seq.planned_volumes is not None and complete < seq.planned_volumes:
        if partial > 0:
            seq.issues.append(
                Issue(
                    "WARN",
                    f"Possible early stop: planned volumes {seq.planned_volumes}, "
                    f"good volumes {complete}, partial trailing volume with {partial} slices.",
                )
            )
        else:
            seq.issues.append(
                Issue(
                    "WARN",
                    f"Planned vs good volume mismatch: planned {seq.planned_volumes}, good {complete}.",
                )
            )
    if missing_middle > 0:
        seq.issues.append(
            Issue("FAIL", f"Detected {missing_middle} volume(s) with missing slices in the sequence middle.")
        )

    seq.observed_tr_ms = _observed_tr(seq, imaging, volume_starts, complete, tr_rel_pct)
    if seq.tr_ms and seq.observed_tr_ms and seq.planned_volumes and seq.planned_volumes > 1:
        abs_diff = abs(seq.observed_tr_ms - seq.tr_ms)
        rel_diff = abs_diff / max(seq.tr_ms, 1e-6) * 100.0
        if abs_diff > tr_abs_ms and rel_diff > tr_rel_pct:
            seq.issues.append(
                Issue(
                    "WARN",
                    f"TR mismatch: metadata TR={seq.tr_ms:.2f} ms, observed TR={seq.observed_tr_ms:.2f} ms "
                    f"(abs {abs_diff:.2f} ms, rel {rel_diff:.2f}%).",
                )
            )

    if not seq.issues:
        seq.status = "PASS"
    elif any(issue.severity == "FAIL" for issue in seq.issues):
        seq.status = "FAIL"
    else:
        seq.status = "WARN"


def _observed_tr(
    seq: SequenceRecord,
    imaging: List[InstanceRecord],
    volume_starts: Dict[int, datetime],
    complete: int,
    tr_rel_pct: float,
) -> Optional[float]:
    observed_tr = estimate_tr_ms(volume_starts)
    if observed_tr is None and seq.planned_volumes and seq.planned_volumes > 1 and seq.tr_ms is not None:
        observed_tr = seq.tr_ms

    # classic single-frame exports can inflate observed TR by an integer factor
    # when temporal indices cycle across slices rather than true volume ids
    if (
        observed_tr is not None
        and seq.tr_ms is not None
        and not seq.enhanced_volume_to_slices
        and (seq.number_of_frames is None or seq.number_of_frames <= 1)
    ):
        ratio = observed_tr / max(seq.tr_ms, 1e-6)
        multiplier = int(round(ratio))
        if multiplier >= 2 and abs(ratio - multiplier) <= 0.2:
            corrected = observed_tr / float(multiplier)
            rel_err = abs(corrected - seq.tr_ms) / max(seq.tr_ms, 1e-6) * 100.0
            if rel_err <= max(tr_rel_pct, 10.0):
                observed_tr = corrected

    if observed_tr is None and complete <= 1:
        frame_times = sorted(inst.dt for inst in imaging if inst.dt is not None)
        if len(frame_times) >= 2:
            observed_tr = (frame_times[-1] - frame_times[0]).total_seconds() * 1000.0
    return observed_tr


def infer_missing_phase_polarity(sequences: List[SequenceRecord]) -> None:
    """When a DWI/SE-fieldmap pair differs only in phase polarity and one side's
    polarity is known from its name, infer the opposite for its partner."""
    candidates = [s for s in sequences if s.modality.upper() == "MR" and not s.non_evaluable]
    groups: Dict[Tuple, List[SequenceRecord]] = defaultdict(list)
    for seq in candidates:
        stype = sequence_type(seq.sequence_name)
        if stype not in {"DWI", "Spin-echo field map"}:
            continue
        axis = seq.phase_encoding_direction if seq.phase_encoding_direction in {"AP", "PA", "LR", "RL"} else "unknown"
        axis_class = "AP" if axis in {"AP", "PA"} else "LR" if axis in {"LR", "RL"} else "unknown"
        key = (
            stype,
            seq.rows or -1,
            seq.cols or -1,
            round(seq.pixel_spacing[0], 4) if seq.pixel_spacing else None,
            round(seq.pixel_spacing[1], 4) if seq.pixel_spacing else None,
            axis_class,
        )
        groups[key].append(seq)

    for group in groups.values():
        if len(group) != 2:
            continue
        a, b = group
        a_token, b_token = parse_phase_token(a.sequence_name), parse_phase_token(b.sequence_name)
        if a_token and not b_token:
            _apply_opposite_polarity(a, b)
        elif b_token and not a_token:
            _apply_opposite_polarity(b, a)


def _apply_opposite_polarity(known: SequenceRecord, other: SequenceRecord) -> None:
    known_token = parse_phase_token(known.sequence_name)
    opposite = opposite_phase_direction(known_token) if known_token else None
    if not opposite or other.phase_encoding_direction not in {"AP", "PA", "LR", "RL"}:
        return
    if other.phase_encoding_direction == known.phase_encoding_direction or other.phase_encoding_direction in {"AP", "LR"}:
        other.phase_encoding_direction = opposite


def classify_sequence_files(
    seq: SequenceRecord, min_images: int = 4
) -> Tuple[Set[str], Set[str], Set[str]]:
    """
    Route a sequence's member files into (good_imaging, non_image, orphaned).

    Scanner-aware and safe by construction (decision D1): orphan-slice detection
    only runs where incomplete volumes are actually possible and robustly
    detectable. It is skipped — leaving every imaging file in the good set — for:

    - mosaic acquisitions (Siemens): one DICOM stores a whole volume, so there
      are no per-file orphan slices;
    - sequences with fewer than ``min_images`` imaging files (localizers, very
      short series), to avoid false positives;
    - sequences where the expected slice count cannot be inferred (missing
      geometry/temporal tags) — reported, never pruned.

    For enhanced multi-frame the whole sequence lives in one image DICOM, so its
    file is only orphaned if no complete volume exists at all. For classic
    single-frame data, files belonging to any volume with fewer than the
    expected number of slices are orphaned.
    """
    imaging = [inst for inst in seq.instances if inst.is_imaging]
    non_image = {inst.member_name for inst in seq.instances if not inst.is_imaging}
    orphaned: Set[str] = set()

    all_imaging = {inst.member_name for inst in imaging}
    if seq.is_mosaic or len(imaging) < min_images:
        return all_imaging, non_image, orphaned

    expected = seq.expected_slices if seq.expected_slices and seq.expected_slices > 0 else None
    if expected is None:
        expected = infer_expected_slices(seq, imaging)
    if not expected or expected <= 0:
        return all_imaging, non_image, orphaned

    if seq.enhanced_volume_to_slices:
        has_complete = any(len(s) >= expected for s in seq.enhanced_volume_to_slices.values())
        if not has_complete:
            orphaned.update(all_imaging)
    else:
        volume_members: Dict[int, List[str]] = defaultdict(list)
        volume_slices: Dict[int, Set[str]] = defaultdict(set)
        for inst in imaging:
            vidx = assign_volume_index(inst, expected)
            volume_members[vidx].append(inst.member_name)
            skey = get_slice_key(inst)
            if skey:
                volume_slices[vidx].add(skey)
        for vidx, members in volume_members.items():
            if len(volume_slices.get(vidx, set())) < expected:
                orphaned.update(members)

    return all_imaging - orphaned, non_image, orphaned


# ---------------------------------------------------------------------------
# geometry / resolution formatting
# ---------------------------------------------------------------------------


def geometry_and_resolution(seq: SequenceRecord) -> Tuple[str, str]:
    geom_z = str(seq.expected_slices) if seq.expected_slices is not None else "unknown"
    geometry = f"{fmt(seq.rows)} × {fmt(seq.cols)} × {geom_z}"

    rx = ry = None
    if seq.pixel_spacing is not None:
        rx, ry = seq.pixel_spacing
    rz = seq.spacing_between_slices if seq.spacing_between_slices is not None else seq.slice_thickness
    if rx is None or ry is None:
        return geometry, "unknown"
    rz_text = f"{rz:.2f}" if rz is not None else "unknown"
    return geometry, f"{rx:.2f} × {ry:.2f} × {rz_text}"


# ---------------------------------------------------------------------------
# table rendering (one renderer for console and markdown)
# ---------------------------------------------------------------------------


def render_table(
    headers: List[str],
    rows: List[List[str]],
    markdown: bool = False,
    header_row: Optional[List[str]] = None,
) -> str:
    """Render an aligned table. ``markdown=True`` adds pipe delimiters; an
    optional ``header_row`` provides a second header line (grouped columns)."""
    widths = [len(h) for h in headers]
    extra = list(rows) + ([header_row] if header_row is not None else [])
    for row in extra:
        for idx, cell in enumerate(row):
            if idx < len(widths):
                widths[idx] = max(widths[idx], len(cell))

    def line(cells: List[str]) -> str:
        padded = [(cells[i] if i < len(cells) else "").ljust(w) for i, w in enumerate(widths)]
        return "| " + " | ".join(padded) + " |" if markdown else "  ".join(padded).rstrip()

    if markdown:
        sep = "| " + " | ".join("-" * max(3, w) for w in widths) + " |"
    else:
        sep = line(["-" * w for w in widths])

    lines = [line(headers), sep]
    if header_row is not None:
        lines.append(line(header_row))
    lines.extend(line(row) for row in rows)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# self-check
# ---------------------------------------------------------------------------


def _demo() -> None:
    # table renderer, both flavors
    plain = render_table(["a", "bb"], [["1", "2"]])
    assert "a" in plain and "bb" in plain and "|" not in plain
    md = render_table(["a", "bb"], [["1", "2"]], markdown=True)
    assert md.startswith("| a") and md.count("|") >= 6

    # duration + sequence typing
    t0 = datetime(2026, 1, 1, 10, 0, 0)
    assert format_duration(t0, t0 + timedelta(seconds=75)) == "01:15"
    assert format_duration(t0 + timedelta(seconds=5), t0) == "unknown"
    assert sequence_type("rfMRI_BOLD_AP") == "BOLD" and sequence_type("DKI_64dir") == "DWI"

    # phase tokens
    assert parse_phase_token("SE_fieldmap_PA") == "PA"
    assert opposite_phase_direction("AP") == "PA" and opposite_phase_direction("XX") is None

    # completeness: 2 full volumes + 1 partial trailing volume -> WARN, good=2
    def inst(vol, stk):
        return InstanceRecord(
            member_name=f"v{vol}s{stk}", sop_uid=f"{vol}.{stk}", instance_number=vol * 10 + stk,
            temporal_position=vol, acquisition_number=None, in_stack_position=stk,
            image_position=None, dt=None, echo_time_ms=None, is_imaging=True,
        )
    seq = SequenceRecord(key="k", sequence_id="7", sequence_name="BOLD", modality="MR",
                         number_of_slices=3, number_of_temporal_positions=3)
    seq.instances = [inst(1, 1), inst(1, 2), inst(1, 3), inst(2, 1), inst(2, 2), inst(2, 3), inst(3, 1), inst(3, 2)]
    validate_sequence(seq, tr_abs_ms=100.0, tr_rel_pct=5.0)
    assert seq.expected_slices == 3, seq.expected_slices
    assert seq.good_volumes == 2 and seq.partial_volume_slices == 2, (seq.good_volumes, seq.partial_volume_slices)
    assert seq.status == "WARN" and any("early stop" in i.message for i in seq.issues)

    # enhanced multi-frame: planned volumes = number of frame-groups
    eseq = SequenceRecord(key="e", sequence_id="9", sequence_name="BOLD", modality="MR", number_of_frames=180)
    eseq.enhanced_volume_to_slices = {1: {1, 2, 3}, 2: {1, 2, 3}}
    assert infer_expected_slices(eseq, []) == 3 and infer_planned_volumes(eseq, 3) == 2
    # DWI reports directions (frames / slices) as planned volumes
    dseq = SequenceRecord(key="d", sequence_id="8", sequence_name="DKI_64dir", modality="MR", number_of_frames=180)
    assert infer_planned_volumes(dseq, 3) == 60

    # file classification: partial trailing volume -> its files orphaned
    seq.expected_slices = 3
    good, non_img, orph = classify_sequence_files(seq, min_images=1)
    assert orph == {"v3s1", "v3s2"} and non_img == set()
    assert good == {"v1s1", "v1s2", "v1s3", "v2s1", "v2s2", "v2s3"}
    # mosaic short-circuits orphan detection (one file per volume)
    mseq = SequenceRecord(key="m", sequence_id="5", sequence_name="BOLD", modality="MR", is_mosaic=True)
    mseq.instances = [inst(1, 1), inst(2, 1)]
    mseq.expected_slices = 40
    mgood, _, morph = classify_sequence_files(mseq, min_images=1)
    assert morph == set() and mgood == {"v1s1", "v2s1"}
    # non-image files always routed aside
    nseq = SequenceRecord(key="n", sequence_id="6", sequence_name="BOLD", modality="MR")
    img_i = inst(1, 1)
    non_i = InstanceRecord("meta", "u", None, None, None, None, None, None, None, is_imaging=False)
    nseq.instances = [img_i, non_i]
    _, nni, _ = classify_sequence_files(nseq, min_images=1)
    assert nni == {"meta"}

    print("sort_validate self-check OK")


if __name__ == "__main__":
    _demo()
