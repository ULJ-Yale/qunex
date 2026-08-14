#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``sort_records.py``

Data model for the single pass DICOM scan engine.

Holds the per instance, per sequence and per package records that
``sort_dicom`` fills in, together with the value formatting, datetime and
sequence naming helpers they depend on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

# pydicom is required for real runs but imported defensively so the pure helpers
# remain importable in a bare environment
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


def format_progress(current: int, total: int, width: int = 40) -> str:
    """Render a ``[####----] 42.0% (n/total)`` progress bar."""
    if total <= 0:
        return "[%s] 0.0%% (0/0)" % ("-" * width)
    ratio = max(0.0, min(1.0, current / total))
    done = int(width * ratio)
    return "[%s%s] %.1f%% (%d/%d)" % (
        "#" * done, "-" * (width - done), ratio * 100, current, total
    )
