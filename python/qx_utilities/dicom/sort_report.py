#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``sort_report.py``

Renders the DICOM integrity report produced by the single pass sort engine.

Given a ``sort_records.PackageSummary`` it produces a per session markdown
report (basic information, a sequence summary table, a detailed per
sequence section and the package verdict) plus a compact console summary
table.
"""

from __future__ import annotations

from typing import List

import qx_utilities.dicom.sort_records as gds_records
import qx_utilities.dicom.sort_tags as gds_tags
import qx_utilities.dicom.sort_validate as gds_validate


def _planned(seq) -> str:
    return str(seq.planned_volumes) if seq.planned_volumes is not None else "unknown"


def _sense(seq) -> str:
    return gds_records.fmt_summary_value(
        f"{seq.sense_factor:.2f}" if seq.sense_factor is not None else None
    )


def _mb(seq) -> str:
    return gds_records.fmt_summary_value(
        str(seq.multiband_factor) if seq.multiband_factor is not None else None
    )


def render_console_summary(pkg) -> str:
    headers = [
        "Seq ID",
        "Name",
        "TR(ms)",
        "TE(ms)",
        "SENSE",
        "MB",
        "PE Dir",
        "Volumes (exp/good)",
        "Status",
    ]
    rows = [
        [
            seq.sequence_id,
            seq.sequence_name,
            gds_records.fmt_ms(seq.tr_ms),
            gds_records.fmt_ms(seq.te_ms),
            _sense(seq),
            _mb(seq),
            seq.phase_encoding_direction,
            f"{_planned(seq)}/{seq.good_volumes}",
            seq.status,
        ]
        for seq in pkg.sequences
    ]
    return gds_validate.render_table(headers, rows)


def _basic_information(pkg) -> List[str]:
    return [
        "## Basic information",
        f"- Session id: {pkg.session_id}",
        f"- Inspection date/time: {pkg.inspection_dt.strftime('%Y-%m-%d, %H:%M:%S')}",
        f"- Participant name: {pkg.participant_name}",
        f"- Participant code: {pkg.participant_code}",
        f"- Recording date/time: {gds_records.format_study_dt(pkg.study_date, pkg.study_time)}",
        f"- Scanner manufacturer: {pkg.scanner_manufacturer}",
        f"- Scanner model: {pkg.scanner_model}",
        f"- Field strength: {pkg.scanner_field_strength}",
        f"- Location: {pkg.location}",
        f"- Number of sequences: {len(pkg.sequences)}",
        f"- Total DICOM files: {pkg.total_dicom}",
        f"- Parse/read errors: {pkg.parse_errors}",
        f"- Package verdict: {pkg.verdict}",
        "",
    ]


def _summary_table(pkg) -> List[str]:
    headers = [
        "Sequence ID",
        "Sequence name",
        "TR (ms)",
        "TE (ms)",
        "SENSE",
        "MB",
        "Phase encoding",
        "Volumes (expected/good)",
        "Status note",
    ]
    rows = []
    for seq in pkg.sequences:
        if seq.status == "SKIP":
            status_note = "NA"
        elif seq.status == "PASS":
            status_note = "OK"
        else:
            status_note = "; ".join(issue.message for issue in seq.issues[:2])
        rows.append(
            [
                seq.sequence_id,
                seq.sequence_name,
                gds_records.fmt_ms(seq.tr_ms),
                gds_records.fmt_ms(seq.te_ms),
                _sense(seq),
                _mb(seq),
                seq.phase_encoding_direction,
                f"{_planned(seq)}/{seq.good_volumes}",
                status_note,
            ]
        )
    if not rows:
        rows = [["n/a", "No MR imaging sequence detected"] + ["n/a"] * 6 + ["NOT_MR"]]
    return ["## Sequence summary overview", gds_validate.render_table(headers, rows, markdown=True), ""]


def _hcp_fields(seq, stype) -> str:
    parts: List[str] = []
    if stype in {"BOLD", "Spin-echo field map"}:
        parts.append(
            "echo spacing="
            + (f"{seq.echo_spacing_ms:.6f} ms" if seq.echo_spacing_ms is not None else "unknown")
        )
    if stype in {"T1w", "T2w"}:
        parts.append(
            "sample spacing="
            + (f"{seq.sample_spacing_ms:.6f} ms" if seq.sample_spacing_ms is not None else "unknown")
        )
        parts.append(f"unwarpdir={seq.unwarpdir}")
    if stype == "EPI field map":
        parts.append(
            "echodiff="
            + (f"{seq.echodiff_ms:.3f} ms" if seq.echodiff_ms is not None else "unknown")
        )
    return ", ".join(parts) if parts else "none"


def _render_sequence_detail(seq) -> List[str]:
    lines = [
        f"### Sequence {seq.sequence_id}: {seq.sequence_name}",
        f"- Sequence status: {seq.status}",
        f"- Time of acquisition: {gds_records.format_dt(seq.acq_start)}",
        f"- Duration of acquisition: {gds_records.format_duration(seq.acq_start, seq.acq_end)}",
    ]
    if seq.non_evaluable:
        lines.append("- Sequence details: non-evaluable sequence (ExamCard/Survey).")
        lines.append("")
        return lines

    stype = gds_records.sequence_type(seq.sequence_name)
    seq.echo_spacing_ms, seq.sample_spacing_ms, seq.echodiff_ms, seq.unwarpdir = gds_tags.compute_hcp_metrics(seq)
    geometry, resolution = gds_validate.geometry_and_resolution(seq)
    sense = f"{seq.sense_factor:.2f}" if seq.sense_factor is not None else "unknown"
    mb = str(seq.multiband_factor) if seq.multiband_factor is not None else "unknown"
    volume_issue = (
        seq.planned_volumes is not None and seq.good_volumes < seq.planned_volumes
    ) or seq.partial_volume_slices > 0
    tr_mismatch = any("TR mismatch" in issue.message for issue in seq.issues)

    lines += [
        f"- Sequence details: type={stype}, TR={gds_records.fmt_ms(seq.tr_ms)} ms, TE={gds_records.fmt_ms(seq.te_ms)} ms",
        f"- Acceleration: in-plane={sense}, multiband={mb}",
        f"- Phase encoding direction: {seq.phase_encoding_direction}",
        f"- Geometry: {geometry}",
        f"- Resolution: {resolution} mm",
        ("- **Volumes:** " if volume_issue else "- Volumes: ")
        + f"planned={_planned(seq)}, good={seq.good_volumes}, "
        + f"partial trailing volume slices={seq.partial_volume_slices}",
        f"- HCP processing fields: {_hcp_fields(seq, stype)}",
        f"- DICOM files: non-image={seq.non_imaging_dicom_count}, image={seq.imaging_dicom_count}",
        ("- **TR comparison:** " if tr_mismatch else "- TR comparison: ")
        + f"metadata={gds_records.fmt_ms(seq.tr_ms)} ms, observed={gds_records.fmt_ms(seq.observed_tr_ms)} ms",
    ]
    if seq.issues:
        lines.append("- Identified issues:")
        lines.extend(f"  - [{issue.severity}] {issue.message}" for issue in seq.issues)
    else:
        lines.append("- Identified issues: none")
    lines.append("")
    return lines


def _final_verdict(pkg) -> List[str]:
    lines = ["## Final package verdict", f"**{pkg.verdict}**"]
    if not pkg.sequences:
        lines.append("Package does not contain MR imaging sequences.")
    else:
        affected = [
            f"{s.sequence_id}:{s.sequence_name}"
            for s in pkg.sequences
            if s.status not in {"PASS", "SKIP"}
        ]
        lines.append(
            "Affected sequences: " + ", ".join(affected)
            if affected
            else "All inspected MR sequences passed core checks."
        )
    lines.append("")
    return lines


def render_report(pkg) -> str:
    """Render the full markdown integrity report for a package/session."""
    lines = [f"# MRI import inspection report: {pkg.package_name}", ""]
    lines += _basic_information(pkg)
    lines += _summary_table(pkg)
    lines.append("## Detailed sequence report")
    if not pkg.sequences:
        lines += ["No MR imaging sequences were found in this package.", ""]
    else:
        for seq in pkg.sequences:
            lines += _render_sequence_detail(seq)
    lines += _final_verdict(pkg)
    return "\n".join(lines)


def write_report(pkg, path) -> str:
    """Write the markdown report to ``path`` and return the path."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(render_report(pkg))
    return path


def _demo() -> None:
    from datetime import datetime, timedelta

    pkg = gds_records.PackageSummary(package_name="OP1174_2_EH", session_id="OP1174_2")
    pkg.participant_code = "OP1174"
    pkg.study_date, pkg.study_time = "20260413", "183254"
    pkg.scanner_manufacturer = "Philips"
    pkg.total_dicom = 9
    pkg.verdict = "WARN"

    seq = gds_records.SequenceRecord(
        key="7", sequence_id="7", sequence_name="BOLD_AP", modality="MR",
        tr_ms=2000.0, te_ms=30.0, rows=64, cols=64, pixel_spacing=(3.0, 3.0),
        spacing_between_slices=3.0, sense_factor=1.90, multiband_factor=4,
        phase_encoding_direction="AP", planned_volumes=3, good_volumes=2,
        partial_volume_slices=2, expected_slices=3, status="WARN",
    )
    seq.acq_start = datetime(2026, 4, 13, 18, 32, 54)
    seq.acq_end = seq.acq_start + timedelta(seconds=4)
    seq.issues = [gds_records.Issue("WARN", "Possible early stop: planned volumes 3, good volumes 2, partial trailing volume with 2 slices.")]
    pkg.sequences = [seq]
    pkg.incomplete_sequences = 1

    report = render_report(pkg)
    assert "# MRI import inspection report: OP1174_2_EH" in report
    assert "Recording date/time: 2026-04-13, 18:32:54" in report
    assert "| Sequence ID" in report and "Volumes (expected/good)" in report
    assert "### Sequence 7: BOLD_AP" in report
    assert "- **Volumes:**" in report            # volume issue highlighted
    assert "in-plane=1.90, multiband=4" in report
    assert "Affected sequences: 7:BOLD_AP" in report

    console = render_console_summary(pkg)
    assert "Seq ID" in console and "BOLD_AP" in console and "3/2" in console and "|" not in console

    # NOT_MR: no sequences -> summary shows the placeholder row, verdict section
    empty = gds_records.PackageSummary(package_name="EEG", session_id="EEG", verdict="NOT_MR")
    r2 = render_report(empty)
    assert "No MR imaging sequence detected" in r2 and "**NOT_MR**" in r2

    print("sort_report self-check OK")


if __name__ == "__main__":
    _demo()
