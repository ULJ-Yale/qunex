#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``dicom_sort.py``

Single-pass DICOM scan/sort/clean engine used by ``import_dicom``,
``sort_dicom`` and ``clean_dicom``. It reads each DICOM header once, buckets
instances into per-sequence records, classifies image vs non-image and complete
vs orphaned (incomplete-volume) files, and provides the analysis and reporting
helpers needed to sort files and emit an integrity report.

This module holds the data model, the metadata-extraction helpers (ported and
slimmed from the standalone ``mri_zip_report_v3.py`` tool), the completeness
analysis, and the shared table renderer. The member-source iteration, write
phase, and command wiring live with ``import_dicom`` in ``dicom.py``.
"""

from __future__ import annotations

import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

# pydicom is required for real runs but imported defensively so the pure helpers
# (and the self-check) remain importable in a bare environment
try:
    import pydicom
except Exception:  # pragma: no cover
    pydicom = None


# ---------------------------------------------------------------------------
# data model
# ---------------------------------------------------------------------------


@dataclass
class Issue:
    severity: str
    message: str


@dataclass
class InstanceRecord:
    member_name: str
    sop_uid: str
    instance_number: Optional[int]
    temporal_position: Optional[int]
    acquisition_number: Optional[int]
    in_stack_position: Optional[int]
    image_position: Optional[Tuple[float, float, float]]
    dt: Optional[datetime]
    echo_time_ms: Optional[float]
    is_imaging: bool
    frame_count: int = 1


@dataclass
class SequenceRecord:
    key: str
    sequence_id: str
    sequence_name: str
    modality: str
    manufacturer: str = "unknown"
    is_mosaic: bool = False
    tr_ms: Optional[float] = None
    te_ms: Optional[float] = None
    rows: Optional[int] = None
    cols: Optional[int] = None
    pixel_spacing: Optional[Tuple[float, float]] = None
    slice_thickness: Optional[float] = None
    spacing_between_slices: Optional[float] = None
    number_of_slices: Optional[int] = None
    images_in_acq: Optional[int] = None
    number_of_temporal_positions: Optional[int] = None
    number_of_frames: Optional[int] = None
    tags_for_hints: Dict[str, object] = field(default_factory=dict)
    instances: List[InstanceRecord] = field(default_factory=list)
    imaging_dicom_count: int = 0
    non_imaging_dicom_count: int = 0
    issues: List[Issue] = field(default_factory=list)
    status: str = "PASS"
    planned_volumes: Optional[int] = None
    good_volumes: int = 0
    partial_volume_slices: int = 0
    expected_slices: Optional[int] = None
    observed_tr_ms: Optional[float] = None
    acq_start: Optional[datetime] = None
    acq_end: Optional[datetime] = None
    enhanced_volume_to_slices: Dict[int, Set[int]] = field(default_factory=dict)
    non_evaluable: bool = False
    phase_encoding_direction: str = "unknown"
    sense_factor: Optional[float] = None
    multiband_factor: Optional[int] = None
    echo_spacing_ms: Optional[float] = None
    sample_spacing_ms: Optional[float] = None
    echodiff_ms: Optional[float] = None
    unwarpdir: str = "unknown"


@dataclass
class PackageSummary:
    package_name: str
    session_id: str = "unknown"
    inspection_dt: datetime = field(default_factory=datetime.now)
    participant_name: str = "unknown"
    participant_code: str = "unknown"
    study_date: str = "unknown"
    study_time: str = "unknown"
    scanner_manufacturer: str = "unknown"
    scanner_model: str = "unknown"
    scanner_field_strength: str = "unknown"
    location: str = "unknown"
    total_dicom: int = 0
    total_members: int = 0
    parse_errors: int = 0
    verdict: str = "PASS"
    sequences: List[SequenceRecord] = field(default_factory=list)
    good_sequences: int = 0
    incomplete_sequences: int = 0
    error_sequences: int = 0
    no_data_sequences: int = 0


# ---------------------------------------------------------------------------
# small value formatting
# ---------------------------------------------------------------------------


def fmt(value: object, default: str = "unknown") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def to_float(value: object) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: object) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def fmt_ms(value: Optional[float]) -> str:
    if value is None:
        return "unknown"
    try:
        return str(int(round(float(value))))
    except (TypeError, ValueError):
        return "unknown"


def fmt_summary_value(value: Optional[object]) -> str:
    if value is None:
        return "-"
    text = str(value).strip()
    return text if text and text.lower() != "unknown" else "-"


# ---------------------------------------------------------------------------
# datetime helpers
# ---------------------------------------------------------------------------


def parse_dt(ds: "pydicom.Dataset") -> Optional[datetime]:
    """Best available acquisition datetime from a DICOM dataset."""
    combined = fmt(getattr(ds, "AcquisitionDateTime", None), "")
    if combined:
        for pattern in ("%Y%m%d%H%M%S.%f", "%Y%m%d%H%M%S"):
            try:
                return datetime.strptime(combined, pattern)
            except ValueError:
                pass

    date_value = next(
        (
            d
            for d in (
                fmt(getattr(ds, "AcquisitionDate", None), ""),
                fmt(getattr(ds, "ContentDate", None), ""),
                fmt(getattr(ds, "SeriesDate", None), ""),
                fmt(getattr(ds, "StudyDate", None), ""),
            )
            if d
        ),
        "",
    )
    time_value = next(
        (
            t
            for t in (
                fmt(getattr(ds, "AcquisitionTime", None), ""),
                fmt(getattr(ds, "ContentTime", None), ""),
                fmt(getattr(ds, "SeriesTime", None), ""),
                fmt(getattr(ds, "StudyTime", None), ""),
            )
            if t
        ),
        "",
    )
    return parse_dt_text(date_value, time_value)


def parse_dt_text(date_value: str, time_value: str) -> Optional[datetime]:
    if not date_value or not time_value:
        return None
    time_value = time_value.replace(":", "")
    for pattern in ("%Y%m%d%H%M%S.%f", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(date_value + time_value, pattern)
        except ValueError:
            pass
    return None


def format_dt(dt: Optional[datetime]) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt is not None else "unknown"


def format_study_dt(study_date: str, study_time: str) -> str:
    if study_date == "unknown" or study_time == "unknown":
        return "unknown"
    dt = parse_dt_text(study_date, study_time)
    return dt.strftime("%Y-%m-%d, %H:%M:%S") if dt is not None else "unknown"


def format_duration(start: Optional[datetime], end: Optional[datetime]) -> str:
    """Acquisition duration as HH:MM:SS (or MM:SS), second precision."""
    if start is None or end is None or end < start:
        return "unknown"
    total_s = int(round((end - start).total_seconds()))
    hh, rem = divmod(total_s, 3600)
    mm, ss = divmod(rem, 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d}" if hh > 0 else f"{mm:02d}:{ss:02d}"


# ---------------------------------------------------------------------------
# sequence classification
# ---------------------------------------------------------------------------


def sequence_type(name: str) -> str:
    text = name.lower()
    if "dki" in text or "dwi" in text or "diff" in text:
        return "DWI"
    if "field" in text and "se" in text:
        return "Spin-echo field map"
    if "field" in text and "epi" in text:
        return "EPI field map"
    if "field" in text or "b0" in text:
        return "B0 field map"
    if "bold" in text or "fmri" in text or "epi" in text:
        return "BOLD"
    if "t1" in text or "mprage" in text:
        return "T1w"
    if "t2" in text or "flair" in text:
        return "T2w"
    return "unknown"


def should_skip_sequence(sequence_name: str) -> bool:
    text = sequence_name.strip().lower()
    if not text:
        return False
    return text in {"survey", "examcard", "exam card"} or text.startswith("survey")


# ---------------------------------------------------------------------------
# image vs non-image classification
# ---------------------------------------------------------------------------


def has_pixel_data(ds: "pydicom.Dataset") -> bool:
    return "PixelData" in ds or "FloatPixelData" in ds or "DoubleFloatPixelData" in ds


def is_imaging_ds(ds: "pydicom.Dataset") -> bool:
    if not has_pixel_data(ds):
        return False
    rows = to_int(getattr(ds, "Rows", None))
    cols = to_int(getattr(ds, "Columns", None))
    frames = to_int(getattr(ds, "NumberOfFrames", None))
    return bool((rows and cols) or frames)


def is_mosaic_ds(ds: "pydicom.Dataset") -> bool:
    """Siemens mosaic: one DICOM stores every slice of a single volume."""
    image_type = getattr(ds, "ImageType", None)
    if image_type:
        try:
            if any("MOSAIC" in str(v).upper() for v in image_type):
                return True
        except TypeError:
            if "MOSAIC" in str(image_type).upper():
                return True
    # Siemens private "NumberOfImagesInMosaic"
    return _first_numeric(_iter_values_for_tag(ds, (0x0019, 0x100A))) is not None


# ---------------------------------------------------------------------------
# private-tag / metadata extraction
# ---------------------------------------------------------------------------


def _iter_values_for_tag(ds: "pydicom.Dataset", tag: Tuple[int, int]) -> List[object]:
    out: List[object] = []
    try:
        for elem in ds.iterall():
            if (int(elem.tag.group), int(elem.tag.elem)) == tag:
                out.append(elem.value)
    except Exception:
        return out
    return out


def _first_numeric(values: List[object]) -> Optional[float]:
    for value in values:
        candidate = to_float(value[0]) if isinstance(value, (list, tuple)) and value else to_float(value)
        if candidate is not None:
            return candidate
    return None


def _first_axis(values: List[object]) -> str:
    for value in values:
        text = str(value).strip().upper()
        if text in {"AP", "PA", "LR", "RL"}:
            return text
    return "unknown"


def parse_phase_token(text: str) -> Optional[str]:
    if not text:
        return None
    for token in re.split(r"[^A-Z0-9]+", text.upper()):
        if token in {"AP", "PA", "LR", "RL"}:
            return token
    return None


def opposite_phase_direction(direction: str) -> Optional[str]:
    return {"AP": "PA", "PA": "AP", "LR": "RL", "RL": "LR"}.get(direction)


def _scalar_or_first(value: object) -> Optional[float]:
    if isinstance(value, (list, tuple)):
        return to_float(value[0]) if value else None
    return to_float(value)


def extract_tr_te(ds: "pydicom.Dataset") -> Tuple[Optional[float], Optional[float]]:
    tr = to_float(getattr(ds, "RepetitionTime", None))
    te = to_float(getattr(ds, "EchoTime", None))
    if te is None:
        te = to_float(getattr(ds, "EffectiveEchoTime", None))
    if tr is None and (0x2005, 0x1030) in ds:
        tr = _scalar_or_first(ds[(0x2005, 0x1030)].value)
    if te is None and (0x2001, 0x1025) in ds:
        te = _scalar_or_first(ds[(0x2001, 0x1025)].value)
    return tr, te


def extract_sense_factor(ds: "pydicom.Dataset") -> Optional[float]:
    factor = _first_numeric(_iter_values_for_tag(ds, (0x0018, 0x9069)))
    if factor is not None:
        return factor
    return to_float(getattr(ds, "ParallelReductionFactorInPlane", None))


def extract_mb_factor(ds: "pydicom.Dataset") -> Optional[int]:
    factor = _first_numeric(_iter_values_for_tag(ds, (0x0018, 0x9155)))
    if factor is None:
        factor = to_float(getattr(ds, "ParallelReductionFactorOutOfPlane", None))
    if factor is None:
        return None

    technique = ""
    tech_vals = _iter_values_for_tag(ds, (0x0018, 0x9078))
    if tech_vals:
        technique = str(tech_vals[0]).upper()
    elif getattr(ds, "ParallelAcquisitionTechnique", None) is not None:
        technique = str(getattr(ds, "ParallelAcquisitionTechnique")).upper()

    epi = str(getattr(ds, "EchoPlanarPulseSequence", "")).upper() == "YES"
    if factor <= 1:
        return 1 if epi else None
    return int(round(factor)) if "MB" in technique else None


def extract_phase_encoding_direction(ds: "pydicom.Dataset", sequence_name: str = "") -> str:
    token_direction: Optional[str] = None
    for source in (sequence_name, fmt(getattr(ds, "SeriesDescription", None), ""), fmt(getattr(ds, "ProtocolName", None), "")):
        token_direction = parse_phase_token(source)
        if token_direction:
            break

    axis = _first_axis(_iter_values_for_tag(ds, (0x2001, 0x1033)))
    if axis == "unknown":
        axis = _first_axis(_iter_values_for_tag(ds, (0x2005, 0x107B)))
    if axis == "unknown":
        inplane = fmt(getattr(ds, "InPlanePhaseEncodingDirection", None), "").upper()
        if inplane in {"COL", "COLUMN"}:
            axis = "AP"
        elif inplane == "ROW":
            axis = "LR"

    if token_direction is not None:
        if axis == "unknown":
            return token_direction
        if axis in {"AP", "PA"} and token_direction in {"AP", "PA"}:
            return token_direction
        if axis in {"LR", "RL"} and token_direction in {"LR", "RL"}:
            return token_direction
    return axis


def get_shared_pixel_measures(
    ds: "pydicom.Dataset",
) -> Tuple[Optional[Tuple[float, float]], Optional[float], Optional[float]]:
    """Pixel spacing, slice thickness, spacing-between-slices from top-level or
    shared/per-frame functional groups."""
    px: Optional[Tuple[float, float]] = None
    pixel_spacing = getattr(ds, "PixelSpacing", None)
    if pixel_spacing and len(pixel_spacing) >= 2:
        try:
            px = (float(pixel_spacing[0]), float(pixel_spacing[1]))
        except (TypeError, ValueError):
            px = None
    st = to_float(getattr(ds, "SliceThickness", None))
    sbs = to_float(getattr(ds, "SpacingBetweenSlices", None))

    for group_attr in ("SharedFunctionalGroupsSequence", "PerFrameFunctionalGroupsSequence"):
        if px is not None and st is not None and sbs is not None:
            break
        group = getattr(ds, group_attr, None)
        if not group or len(group) == 0:
            continue
        pm = getattr(group[0], "PixelMeasuresSequence", None)
        if not pm or len(pm) == 0:
            continue
        pms = pm[0]
        if px is None:
            pspace = getattr(pms, "PixelSpacing", None)
            if pspace and len(pspace) >= 2:
                try:
                    px = (float(pspace[0]), float(pspace[1]))
                except (TypeError, ValueError):
                    px = None
        if st is None:
            st = to_float(getattr(pms, "SliceThickness", None))
        if sbs is None:
            sbs = to_float(getattr(pms, "SpacingBetweenSlices", None))
    return px, st, sbs


def extract_enhanced_volume_map(ds: "pydicom.Dataset") -> Dict[int, Set[int]]:
    """Volume index -> set of slice indices for enhanced multi-frame DICOM."""
    per_frame = getattr(ds, "PerFrameFunctionalGroupsSequence", None)
    if not per_frame:
        return {}

    mapping: Dict[int, Set[int]] = defaultdict(set)
    for fg in per_frame:
        frame_content = getattr(fg, "FrameContentSequence", None)
        if not frame_content:
            continue
        fc = frame_content[0]
        temporal = to_int(getattr(fc, "TemporalPositionIndex", None)) or 1
        vol_idx = temporal
        slice_idx: Optional[int] = None

        dim_vals = getattr(fc, "DimensionIndexValues", None)
        if dim_vals is not None:
            try:
                ints = [int(v) for v in dim_vals]
            except (TypeError, ValueError):
                ints = []
            if len(ints) >= 3:
                slice_idx, vol_idx = ints[-2], ints[-1]
            elif len(ints) == 2:
                slice_idx = ints[-1]
            elif len(ints) == 1:
                slice_idx = ints[0]

        if slice_idx is None:
            slice_idx = to_int(getattr(fc, "InStackPositionNumber", None))
        if slice_idx is None:
            continue
        mapping[max(vol_idx, 1)].add(max(slice_idx, 1))
    return dict(mapping)


def compute_hcp_metrics(
    seq: SequenceRecord,
) -> Tuple[Optional[float], Optional[float], Optional[float], str]:
    """HCP-relevant fields by sequence type: echo spacing, sample spacing,
    echodiff, unwarp direction. Returns unknowns where not applicable."""
    stype = sequence_type(seq.sequence_name)
    hints = seq.tags_for_hints
    echo_spacing_ms = sample_spacing_ms = echodiff_ms = None
    unwarpdir = "unknown"

    ees = to_float(hints.get("EffectiveEchoSpacing"))
    if ees is not None:
        echo_spacing_ms = ees * 1000.0 if ees < 1 else ees
    if echo_spacing_ms is None:
        private_ees = to_float(hints.get("PrivateEchoSpacing"))
        if private_ees is not None:
            echo_spacing_ms = private_ees * 1000.0 if private_ees < 1 else private_ees
            etl = to_int(hints.get("EchoTrainLength"))
            if echo_spacing_ms > 5 and etl and etl > 1:
                echo_spacing_ms /= float(etl - 1)
    if echo_spacing_ms is None:
        bw_pe = to_float(hints.get("BandwidthPerPixelPhaseEncode"))
        inplane = fmt(hints.get("InPlanePhaseEncodingDirection"), "").upper()
        pe_dim = seq.cols if inplane == "COL" else seq.rows
        if bw_pe and bw_pe > 0 and pe_dim and pe_dim > 0:
            echo_spacing_ms = 1000.0 / (bw_pe * pe_dim)

    pixel_bw = to_float(hints.get("PixelBandwidth"))
    if pixel_bw and pixel_bw > 0:
        sample_spacing_ms = 1000.0 / pixel_bw

    echo_times = sorted(
        {round(inst.echo_time_ms, 6) for inst in seq.instances if inst.is_imaging and inst.echo_time_ms is not None}
    )
    if len(echo_times) >= 2:
        echodiff_ms = echo_times[-1] - echo_times[0]

    if stype in {"T1w", "T2w"}:
        unwarpdir = seq.phase_encoding_direction

    # keep only the fields meaningful for this sequence type
    if stype not in {"BOLD", "Spin-echo field map"}:
        echo_spacing_ms = None
    if stype not in {"T1w", "T2w"}:
        sample_spacing_ms = None
        unwarpdir = "unknown"
    if stype != "EPI field map":
        echodiff_ms = None
    return echo_spacing_ms, sample_spacing_ms, echodiff_ms, unwarpdir


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

    print("dicom_sort self-check OK")


if __name__ == "__main__":
    _demo()
