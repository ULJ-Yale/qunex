#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``workflow/qc_summary_report.py``

The interactive report ``run_qc_summary`` builds from the tables it compiled.

The page itself -- markup, style and the JavaScript behind its four tabs --
is not here: it is ``template_qc_summary_report.html`` in ``qx_library``,
beside the workbench scene templates the visual QC commands use. This module
prepares the data the page reads and substitutes it into the template, which
is the whole of the coupling between the two: the template carries one
``/*DATA*/`` placeholder for the payload and one ``/*PLOTLY*/`` placeholder for
the plotting library.

Plotly is inlined from a copy vendored beside the template rather than fetched
from a CDN. A QC report is normally read on the cluster the study was processed
on, which commonly has no route out, and a report that renders as a blank page
there is worse than a large one.

The rows arrive as lists of dictionaries, in memory, straight from the command
that assembled them -- there is no round trip through the tables on disk, and
no pandas: the per metric statistics are a few numpy lines over a column.
"""

import json
import os

import numpy as np

import qx_utilities.general.exceptions as ge
from qx_utilities.general.log import log_or_console


TEMPLATE_NAME = "template_qc_summary_report.html"
PLOTLY_NAME = "plotly.min.js"

# the metrics the tables can carry, in the order the report offers them, each
# with the direction a reader should be worried about and the name it is shown
# under. Transcribed from the metric reference; `up` means a higher value is
# the better one, `down` that a lower one is, and `mid` that neither end is
# good in itself and the sample is what a value is read against.
#
# The direction is data because it decides how a metric contributes to the
# z-scores, to the composite deviation ranking and to the "orient so higher =
# more concerning" view. Deriving it from the spelling of the name -- which is
# what this report used to do -- silently inverts a metric the day one is added
# whose name reads the other way round.
METRICS = {
    # ---- registration and the PreFreeSurfer warp
    "reg_group_ncc": ("up", "MNI registration similarity (vs group)"),
    "reg_template_ncc": ("up", "MNI registration similarity (vs template)"),
    "mni_brain_volume_ml": ("mid", "Brain volume in MNI (ml)"),
    "t1t2_ratio_median": ("mid", "T1w/T2w ratio (median)"),
    "warp_jac_min": ("mid", "Warp Jacobian (min)"),
    "warp_jac_max": ("mid", "Warp Jacobian (max)"),
    "warp_jac_pct_folded": ("down", "Warp folding (%)"),
    # ---- the FreeSurfer recon, in native space
    "fs_etiv_ml": ("mid", "Intracranial volume (ml)"),
    "fs_brainseg_ml": ("mid", "Brain-seg volume (ml)"),
    "fs_surface_holes": ("down", "Surface holes (total)"),
    "fs_mean_thickness": ("mid", "Mean thickness (native)"),
    "t1_wg_cnr": ("up", "WM/GM contrast-to-noise"),
    "t1_wg_contrast": ("up", "WM/GM contrast (%)"),
    # ---- the fs_LR surfaces and myelin maps
    "myelin_mean_L": ("mid", "Myelin mean (L)"),
    "myelin_mean_R": ("mid", "Myelin mean (R)"),
    "myelin_asym": ("down", "Myelin L-R asymmetry"),
    "myelin_cv": ("down", "Myelin variability (CV)"),
    "areal_distortion_p95": ("down", "Surface areal distortion (p95)"),
    "edge_distortion_mean": ("down", "Surface edge distortion (mean)"),
    "thickness_mean": ("mid", "Mean thickness (fs_LR)"),
    "thickness_sd": ("mid", "Thickness SD (fs_LR)"),
    "n_vertices_L": ("mid", "Cortical vertices (L)"),
    "n_vertices_R": ("mid", "Cortical vertices (R)"),
    # ---- BOLD, rolled up to the session by its worst run
    "bold_n": ("mid", "BOLD runs (n)"),
    "bold_worst_run": ("mid", "Worst BOLD run"),
    "bold_worstFD": ("down", "BOLD worst FD"),
    "bold_worst_pct_bad": ("down", "BOLD worst-run % flagged"),
    "bold_tsnr_min": ("up", "BOLD tSNR (worst run)"),
    "bold_coverage_min": ("up", "BOLD coverage (worst run, %)"),
    # ---- diffusion, from the eddy QC report
    "dwi_motion_abs": ("down", "DWI motion (absolute)"),
    "dwi_motion_rel": ("down", "DWI motion (relative)"),
    "dwi_outliers_pct": ("down", "DWI outlier slices (%)"),
    "dwi_cnr_mean": ("up", "DWI CNR (mean)"),
    # ---- what the session as a whole came to
    "likely_failure_step": ("mid", "Likely failure step"),
    "diagnosis_evidence": ("mid", "Diagnosis evidence"),
    "completeness": ("mid", "Completeness"),
    "stages_missing": ("mid", "Missing stages"),
    # ---- the per run BOLD table
    "run": ("mid", "Run"),
    "n_frames": ("mid", "Total frames (n)"),
    "fd_mean": ("down", "FD mean (mm)"),
    "fd_max": ("down", "Peak FD (mm)"),
    "fd_pct_over": ("down", "Frames over FD threshold (%)"),
    "dvarsme_mean": ("down", "DVARSme mean"),
    "dvarsme_max": ("down", "DVARSme max"),
    "dvarsme_pct_over": ("down", "Frames over DVARSme threshold (%)"),
    "dvars_mean": ("down", "DVARS mean (raw)"),
    "n_bad": ("down", "Flagged frames (n)"),
    "pct_bad": ("down", "Flagged frames (%)"),
    "n_both": ("down", "Frames over both measures (n)"),
    "pct_both": ("down", "Frames over both measures (%)"),
    "frames_retained": ("up", "Frames retained (n)"),
    "tsnr_median": ("up", "Temporal SNR (median)"),
    "coverage_pct": ("up", "Cortical coverage (%)"),
    "criterion": ("mid", "Scrubbing criterion"),
    "flags": ("mid", "Flags"),
    "fdt": ("mid", "FD threshold used (mm)"),
    "dvarsmet": ("mid", "DVARSme threshold used"),
}

# columns that identify a row rather than measure it
IDENTIFIERS = ("session", "subject", "run", "criterion", "flags")


def scenes_folder():
    """
    The ``qx_library`` folder the template and the plotting library live in.

    Located off ``QUNEXPATH`` the way the visual QC commands locate their scene
    templates. The variable is read here rather than at import so that the
    module can be imported -- and the rest of the command tested -- in an
    environment that has no QuNex on it.

    Returns:
        str: the path to ``qx_library/data/scenes/qc``.

    Raises:
        CommandError: when ``QUNEXPATH`` is not set.
    """
    if "QUNEXPATH" not in os.environ:
        raise ge.CommandError(
            "run_qc_summary",
            "QUNEXPATH is not set, so the QC report template cannot be found. "
            "Source the QuNex environment, or run with --qc_summary_report=no "
            "to write the tables alone.",
        )
    return os.path.join(os.environ["QUNEXPATH"], "qx_library", "data", "scenes", "qc")


def _asset(folder, name):
    """One of the report's data files, or an error naming the file and why."""
    path = os.path.join(folder, name)
    if not os.path.isfile(path):
        raise ge.CommandError(
            "run_qc_summary",
            "the QC report needs %s, and there is no such file. Is the "
            "qx_library submodule checked out and up to date?" % path,
        )
    with open(path, encoding="utf-8") as asset:
        return asset.read()


# --------------------------------------------------------------- the numbers


def _number(value):
    """A cell as a float, or None when it holds no number."""
    if isinstance(value, bool) or not isinstance(value, (int, float, np.number)):
        return None
    value = float(value)
    return value if np.isfinite(value) else None


def _round(value):
    """A number rounded for the payload, with anything unusable as null."""
    return None if value is None or not np.isfinite(value) else round(float(value), 6)


def _is_measure(values):
    """
    Whether a column holds measurements, and so can be plotted.

    A column qualifies when no row holds anything but a number or a blank, and
    at least one row holds a numeric value. The value may be the
    not-a-number a stage that produced nothing leaves behind: a metric no
    session in the study has is still a metric, and the report says so rather
    than passing over it in silence.
    """
    numeric = False
    for value in values:
        if isinstance(value, bool):
            return False
        if isinstance(value, (int, float, np.number)):
            numeric = True
        elif value is not None and value != "":
            return False
    return numeric


def _measures(rows):
    """The measured columns of a table, in the order the report offers them."""
    names = {name for row in rows for name in row}
    ordered = [name for name in METRICS if name in names]
    ordered += sorted(names - set(METRICS) - set(IDENTIFIERS))
    return [name for name in ordered
            if name not in IDENTIFIERS
            and _is_measure([row[name] for row in rows if name in row])]


def _column(rows, name):
    """One measured column as a float array, with the blanks as nan."""
    values = [_number(row.get(name)) for row in rows]
    return np.array([np.nan if value is None else value for value in values], dtype=float)


def _describe(values):
    """
    The reference statistics the report draws its cutoffs and overlays from.

    Computed over the finite values alone rather than with ``nanmean`` and
    friends, so that a metric no session produced is an empty description
    rather than a warning from numpy.
    """
    empty = dict.fromkeys(("mean", "sd", "median", "q1", "q3", "p2_5", "p97_5"))
    good = values[np.isfinite(values)]
    if not good.size:
        return empty

    q1, q3, p2_5, p97_5 = np.percentile(good, [25, 75, 2.5, 97.5])
    return {
        "mean": _round(good.mean()),
        "sd": _round(good.std(ddof=1)) if good.size > 1 else None,
        "median": _round(np.median(good)),
        "q1": _round(q1), "q3": _round(q3),
        "p2_5": _round(p2_5), "p97_5": _round(p97_5),
    }


def _direction(name, *, log):
    """The direction a metric is read in, or `mid` and a warning when unknown."""
    if name in METRICS:
        return METRICS[name][0]
    log.warning(f"the report has no direction recorded for '{name}', so it is "
                "read as a metric with no good end. Add it to METRICS in "
                "processing/workflow/qc_summary_report.py")
    return "mid"


def _label(name):
    """The name a metric is shown under."""
    return METRICS[name][1] if name in METRICS else name.replace("_", " ")


# --------------------------------------------------------------- the payload


def _session_payload(rows, options, *, log):
    """
    The session level half of the payload: values, z scores and statistics.

    A metric every session agrees on -- one that is constant, or that no
    session produced -- carries no information to plot, so it is moved to the
    list the Diagnosis tab notes at the bottom rather than offered as a
    parameter to look at.
    """
    sessions = [str(row.get("session", "")) for row in rows]
    measures = _measures(rows)

    raw, scores, statistics, constant, plotted = {}, {}, {}, [], []
    for name in measures:
        values = _column(rows, name)
        described = _describe(values)
        statistics[name] = described
        raw[name] = [_round(value) for value in values]

        mean, sd = described["mean"], described["sd"]
        scores[name] = ([_round(value) for value in (values - mean) / sd]
                        if sd else [None] * len(values))

        good = values[np.isfinite(values)]
        if np.unique(good).size <= 1:
            constant.append({
                "name": name, "label": _label(name),
                "value": _round(good[0]) if good.size else None,
                "reason": "all missing" if not good.size else "constant across sample",
            })
        else:
            plotted.append(name)

    return {
        "subjects": sessions,
        "metrics": plotted,
        "labels": {name: _label(name) for name in measures},
        "raw": raw,
        "z": scores,
        "stats": statistics,
        "higher_is_better": [name for name in measures
                             if _direction(name, log=log) == "up"],
        "paths": {session: os.path.join(options["sessionsfolder"], session)
                  for session in sessions},
        "constant_metrics": constant,
        "diagnosis": [{"subject": str(row.get("session", "")),
                       "step": str(row.get("likely_failure_step") or ""),
                       "evidence": str(row.get("diagnosis_evidence") or "")}
                      for row in rows if row.get("likely_failure_step")],
    }


def _run_payload(runs, traces):
    """
    The per run half of the payload: one record per BOLD run, plus the traces.

    The rows are handed over as they are, save for the session column, which
    the report reads as ``subject``, and the blanks, which become nulls so that
    the page can tell "not measured" from zero.
    """
    records = []
    for run in runs:
        record = {}
        for name, value in run.items():
            name = "subject" if name == "session" else name
            number = _number(value)
            if number is not None:
                record[name] = _round(number)
            else:
                record[name] = None if isinstance(value, (float, np.floating)) else value
        records.append(record)

    return {
        "bold_runs": records,
        "bold_traces": traces,
        "bold_labels": {name: _label(name) for name in _measures(runs)},
    }


def build_report(session_rows, run_rows, traces, options, *, _log=None):
    """
    Build the study's QC report as one self-contained HTML page.

    Everything the page needs travels inside it -- the data, the styling and
    the plotting library -- so that it can be opened from a file, over a share
    or on a machine with no network at all.

    Parameters:
        session_rows (list): one row per session, as written to the session
            table, with the diagnosis and completeness already recorded.
        run_rows (list): one row per BOLD run.
        traces (dict): the per frame traces, keyed ``<session>/<run>``.
        options (dict): the command's options.
        _log: the log to report into.

    Returns:
        str: the report, ready to be written out.

    Raises:
        CommandError: when the template or the plotting library cannot be
            found. Building the report is something the command was asked to
            do, so failing to do it is a failure of the command, unlike a
            session that has no data to report on.
    """
    log = log_or_console(_log)

    folder = scenes_folder()
    template = _asset(folder, TEMPLATE_NAME)
    plotly = _asset(folder, PLOTLY_NAME)

    payload = _session_payload(session_rows, options, log=log)
    payload.update(_run_payload(run_rows, traces))

    log.detail(f"{len(payload['subjects'])} sessions, "
               f"{len(payload['metrics'])} metrics to plot, "
               f"{len(payload['constant_metrics'])} constant or missing, "
               f"{len(payload['bold_runs'])} BOLD runs")

    # the payload first: it is the smaller substitution, and doing it after
    # inlining several megabytes of JavaScript would mean scanning all of it
    return (template
            .replace("/*DATA*/", json.dumps(payload, default=float))
            .replace("/*PLOTLY*/", plotly))
