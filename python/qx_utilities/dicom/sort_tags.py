#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``sort_tags.py``

Metadata extraction from DICOM datasets.

Recognises image versus non image datasets and pulls the acquisition
parameters (TR and TE, SENSE and multiband factors, phase encoding
direction, pixel measures, enhanced volume maps and the derived HCP
metrics) out of flat and nested tag trees.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from qx_utilities.dicom.sort_records import (
    SequenceRecord,
    fmt,
    sequence_type,
    to_float,
    to_int,
)

# pydicom is required for real runs but imported defensively so the pure helpers
# remain importable in a bare environment
try:
    import pydicom
except Exception:  # pragma: no cover
    pydicom = None


# ---------------------------------------------------------------------------
# image vs non-image classification
# ---------------------------------------------------------------------------


def is_imaging_ds(ds: "pydicom.Dataset") -> bool:
    """Classify an instance as imaging from the Image Pixel module.

    An image instance carries frame geometry *and* ``BitsAllocated``, which is
    Type 1 (always present) in the Image Pixel module. Both are tested:

    - geometry alone is not enough. Philips ships a private per-series object
      (SOP class ``1.3.46.670589.11.0.0.12.2``) that carries Rows/Columns but no
      pixel data; dcm2niix reports it as ``Skipping non-image DICOM``. There is
      exactly one per series, so passing it through corrupts the volume tally.
    - the pixel data element itself is deliberately *not* tested, even though it
      would also separate the two. Every reader feeding this function truncates
      the header before (7FE0,0010) for speed, so a pixel-data test would reject
      every file. ``BitsAllocated`` is (0028,0100), well before that cut, so it
      is free to read.

    Non-image objects with no geometry at all (structured reports, presentation
    states, raw data) are rejected by the geometry test.
    """
    rows = to_int(getattr(ds, "Rows", None))
    cols = to_int(getattr(ds, "Columns", None))
    frames = to_int(getattr(ds, "NumberOfFrames", None))
    if not ((rows and cols) or frames):
        return False
    return to_int(getattr(ds, "BitsAllocated", None)) is not None


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


_TAG_INDEX_ATTR = "_qx_nested_tag_index"

# private/hint tags looked up through _iter_values_for_tag, indexed in one pass
_HINT_TAGS = frozenset(
    {
        (0x0019, 0x100A),  # Siemens NumberOfImagesInMosaic
        (0x0018, 0x9069),  # ParallelReductionFactorInPlane
        (0x0018, 0x9155),  # ParallelReductionFactorOutOfPlane
        (0x0018, 0x9078),  # ParallelAcquisitionTechnique
        (0x2001, 0x1033),  # Philips stack radial axis
        (0x2005, 0x107B),  # Philips scan orientation
        (0x2005, 0x1492),  # Philips echo spacing
        (0x2001, 0x1025),  # Philips echo time display
        (0x2005, 0x1033),  # Philips acquisition duration
    }
)


def _iter_values_for_tag(ds: "pydicom.Dataset", tag: Tuple[int, int]) -> List[object]:
    """Values for ``tag``, looking inside nested sequences when needed.

    Callers only ever take the first value (via ``_first_numeric`` /
    ``_first_axis``), and the returned order matches what ``iterall()`` would
    yield, so the first element is the same one the exhaustive walk would find.
    The *number* of values can be smaller: when the tag is present at the top
    level this returns just that one and does not go looking for the duplicates
    that enhanced multi-frame files repeat in their functional groups. Do not
    use this to count occurrences.

    Three shortcuts, all there because this used to dominate scan time -- it is
    called once per hint tag (eight times) per file, and a naive implementation
    walks the whole dataset every time:

    - a top-level hit is an O(1) dict lookup, which covers the common case;
    - otherwise the nested walk is done *once* and the resulting tag index is
      memoised on the dataset. Without this, a tag that is simply absent (e.g.
      the Siemens mosaic tag on Philips data) costs a full walk on every call;
    - that walk converts only what it needs (see ``_index_nested_tags``).
    """
    try:
        if tag in ds:
            return [ds[tag].value]
        index = getattr(ds, _TAG_INDEX_ATTR, None)
        if index is None:
            index = {}
            _index_nested_tags(ds, index)
            setattr(ds, _TAG_INDEX_ATTR, index)
        if tag in _HINT_TAGS:
            return index.get(tag, [])
        # tag outside the indexed set: fall back to the exhaustive walk
        return [
            elem.value
            for elem in ds.iterall()
            if (int(elem.tag.group), int(elem.tag.elem)) == tag
        ]
    except Exception:
        return []


def _index_nested_tags(ds: "pydicom.Dataset", out: dict) -> None:
    """Collect ``_HINT_TAGS`` values from ``ds`` and its nested sequences.

    Walks ``_dict`` directly rather than using ``iterall()``. ``iterall()``
    converts every raw element it yields, and only a handful are ever wanted --
    here only sequences (to recurse into) and the hint tags themselves are
    converted, which is what makes a per-file nested lookup affordable.
    """
    # sorted() to match the order iterall() yields, so the first value found
    # for a tag is the same one the exhaustive walk would have returned
    for tag in sorted(ds._dict):
        raw = ds._dict[tag]
        key = (int(tag.group), int(tag.elem))
        if key in _HINT_TAGS:
            out.setdefault(key, []).append(ds[tag].value)
        elif getattr(raw, "VR", None) == "SQ":
            for item in ds[tag].value:
                _index_nested_tags(item, out)


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
