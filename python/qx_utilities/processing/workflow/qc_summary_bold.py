#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``workflow/qc_summary_bold.py``

The BOLD half of what ``run_qc_summary`` compiles: movement, scrubbing,
temporal SNR and cortical coverage, per run and rolled up per session.

Split from ``qc_summary.py``, which holds the structural and diffusion measures
and the image reading the two share.
"""

import os
import re

import numpy as np

import qx_utilities.processing.core as pc
import qx_utilities.processing.mov_stats as ms
from qx_utilities.general.log import log_or_console
from qx_utilities.processing.workflow.qc_summary import timeseries_stats


#
# The per frame statistics and the scrubbing flags are read from the `.bstats`
# and `.scrub` files `compute_bold_stats` wrote, through `mov_stats.read_named`
# -- the same reader `create_stats_report` uses, so the two commands cannot
# come to different conclusions about the same run.
#
# The flags in particular are *read*, not recomputed. The `.scrub` file already
# holds one column per criterion, with the study's own thresholds and its
# --mov_before / --mov_after padding applied, so the frames reported here are
# the frames preprocessing actually excluded. Asking for a different threshold
# is still possible and is the one case the flags are recomputed from the
# traces -- and the row then says so, because it is no longer the pipeline's
# answer.

# what the `.scrub` header records about the run it describes
SCRUB_PARAMETERS = ["radius", "fdt", "dvarsmt", "dvarsmet", "after", "before"]

# the command's parameters, against the `.scrub` parameter each one would change
THRESHOLD_PARAMETERS = {
    "mov_fd": "fdt",
    "mov_dvars": "dvarsmt",
    "mov_dvarsme": "dvarsmet",
    "mov_before": "before",
    "mov_after": "after",
}

RUN_COLUMNS = [
    "session", "run", "n_frames", "fd_mean", "fd_max", "fd_pct_over",
    "dvarsme_mean", "dvarsme_max", "dvarsme_pct_over", "dvars_mean",
    "n_bad", "pct_bad", "n_both", "pct_both", "frames_retained",
    "tsnr_median", "coverage_pct", "criterion", "flags", "fdt", "dvarsmet",
]


def _scrub_parameters(path):
    """
    The parameters recorded in a ``.scrub`` file's header, as ``{name: value}``.

    ``general_compute_bold_stats`` writes them as ``# <name>:  <value>`` lines
    ahead of the table. Only the numeric ones are read; ``reject`` names the
    criterion the ``use`` column was built with and is not needed here.
    """
    parameters = {}
    if not path or not os.path.isfile(path):
        return parameters

    entry = re.compile(r"#\s*([a-zA-Z_]+):\s*([-\d.]+)")
    with open(path) as scrub:
        for line in scrub:
            if not line.startswith("#"):
                break
            found = entry.search(line)
            if found and found.group(1).lower() in SCRUB_PARAMETERS:
                try:
                    parameters[found.group(1).lower()] = float(found.group(2))
                except ValueError:
                    pass

    return parameters


def _requested_thresholds(options, parameters):
    """
    The thresholds asked for, and whether they differ from the ones on record.

    A run's ``.scrub`` file records the thresholds it was built with, so
    "the command was asked for something else" is simply the two disagreeing --
    no need to know which parameters were typed on the command line and which
    came from a default.

    Returns ``(thresholds, differs)``.
    """
    thresholds = {}
    differs = False
    for parameter, recorded in THRESHOLD_PARAMETERS.items():
        asked = options[parameter]
        thresholds[recorded] = asked
        if recorded in parameters and float(parameters[recorded]) != float(asked):
            differs = True

    return thresholds, differs


def _recompute_flags(traces, criterion, thresholds):
    """
    Rebuild the bad frame flags from the per frame traces, for a threshold the
    run was not processed with.

    The frames padded around a flagged one are included, as
    ``compute_bold_stats`` includes them. A measure the ``.bstats`` file does
    not carry flags nothing, rather than everything.
    """
    frames = len(next(iter(traces.values())))

    def over(measure, threshold):
        values = traces.get(measure)
        if values is None:
            return np.zeros(frames, bool)
        return np.asarray(values) > threshold

    fd = over("fd", thresholds["fdt"])
    dvars = over("dvarsm", thresholds["dvarsmt"])
    dvarsme = over("dvarsme", thresholds["dvarsmet"])

    bad = {
        "mov": fd, "dvars": dvars, "dvarsme": dvarsme,
        "udvars": fd | dvars, "idvars": fd & dvars,
        "udvarsme": fd | dvarsme, "idvarsme": fd & dvarsme,
    }.get(criterion, fd | dvarsme)

    before, after = int(thresholds["before"]), int(thresholds["after"])
    if before or after:
        padded = bad.copy()
        for frame in np.flatnonzero(bad):
            padded[max(0, frame - before):min(frames, frame + after + 1)] = True
        bad = padded

    return bad


def _mean(values):
    return round(float(np.nanmean(values)), 5) if values is not None and len(values) else np.nan


def _max(values):
    return round(float(np.nanmax(values)), 5) if values is not None and len(values) else np.nan


def _percent_over(values, threshold):
    if values is None or not len(values):
        return np.nan
    return round(100.0 * float(np.mean(np.asarray(values) > threshold)), 3)


def _trace(values):
    """A per frame measure as a JSON-safe list, with the gaps as null."""
    if values is None:
        return []
    return [None if not np.isfinite(value) else round(float(value), 5) for value in values]


def bold_metrics(session, options, *, _log=None):
    """
    Movement, scrubbing, temporal SNR and coverage for a session's BOLD runs.

    Which runs are read is what ``--bolds`` selects from the batch file, and
    their files are the ones QuNex names for them, so ``--boldname``,
    ``--nifti_tail``, ``--cifti_tail`` and ``--bold_variant`` all apply.

    Parameters:
        session (dict): the session information from the batch file.
        options (dict): the command's options.
        _log: the log to report into.

    Returns:
        tuple: ``(runs, traces, rollup)`` -- a row per run, the per frame
        traces keyed ``<session>/<run>``, and the worst run summary that goes
        on the session's own row.
    """
    log = log_or_console(_log)
    criterion = options["mov_bad"]

    bolds, _, _ = pc.use_or_skip_bold(session, options, _log=None)
    if not bolds:
        log.detail("no BOLD runs selected, skipping the BOLD measures")
        return [], {}, {}

    runs, traces = [], {}
    for boldinfo in bolds:
        f = pc.get_bold_file_names(session, boldinfo["name"], options)
        run = os.path.basename(f["bold_stats"])[: -len(".bstats")]

        if not os.path.isfile(f["bold_stats"]):
            log.detail(f"no statistics for {run}, the run is not reported")
            continue

        try:
            row, trace = _run_metrics(session, run, f, options, criterion, _log=log)
        except Exception as error:
            log.warning(f"could not read the statistics for {run}: {error}")
            continue

        runs.append(row)
        traces[f"{session['id']}/{run}"] = trace

    return runs, traces, _worst_run(runs)


def _run_metrics(session, run, f, options, criterion, *, _log):
    """One BOLD run's row and its per frame traces."""
    log = log_or_console(_log)

    stats = ms.read_named(f["bold_stats"])
    frames = len(next(iter(stats.values())))

    parameters = _scrub_parameters(f["bold_scrub"])
    thresholds, differs = _requested_thresholds(options, parameters)

    flags = None
    if os.path.isfile(f["bold_scrub"]) and not differs:
        scrub = ms.read_named(f["bold_scrub"])
        if criterion in scrub:
            flags = np.asarray(scrub[criterion]) > 0
            both = np.asarray(scrub.get("idvarsme", np.zeros(frames))) > 0
            source = "pipeline"
        else:
            log.warning(f"{run}: the scrub file has no '{criterion}' column, "
                        "the flags are computed from the statistics instead")

    if flags is None:
        flags = _recompute_flags(stats, criterion, thresholds)
        both = _recompute_flags(stats, "idvarsme", thresholds)
        source = "recomputed" if differs else "computed"

    nbad = int(flags.sum())
    nboth = int(both.sum())

    tsnr, coverage = np.nan, np.nan
    if options["qc_summary_tsnr"]:
        if os.path.isfile(f["bold_dts"]):
            try:
                tsnr, coverage = timeseries_stats(f["bold_dts"])
            except Exception as error:
                log.warning(f"{run}: could not read the dense timeseries: {error}")
        else:
            log.detail(f"no dense timeseries for {run}, "
                       "no temporal SNR or coverage for it")

    fd, dvars = stats.get("fd"), stats.get("dvars")
    dvarsm, dvarsme = stats.get("dvarsm"), stats.get("dvarsme")

    row = {
        "session": session["id"], "run": run, "n_frames": frames,
        "fd_mean": _mean(fd), "fd_max": _max(fd),
        "fd_pct_over": _percent_over(fd, thresholds["fdt"]),
        "dvarsme_mean": _mean(dvarsme), "dvarsme_max": _max(dvarsme),
        "dvarsme_pct_over": _percent_over(dvarsme, thresholds["dvarsmet"]),
        "dvars_mean": _mean(dvars),
        "n_bad": nbad, "pct_bad": round(100.0 * nbad / frames, 3) if frames else np.nan,
        "n_both": nboth, "pct_both": round(100.0 * nboth / frames, 3) if frames else np.nan,
        "frames_retained": frames - nbad,
        "tsnr_median": tsnr, "coverage_pct": coverage,
        "criterion": criterion, "flags": source,
        "fdt": thresholds["fdt"], "dvarsmet": thresholds["dvarsmet"],
    }
    trace = {
        "fd": _trace(fd), "dvars": _trace(dvars),
        "dvarsm": _trace(dvarsm), "dvarsme": _trace(dvarsme),
        "bad": flags.astype(int).tolist(),
        "fdt": thresholds["fdt"], "dvarst": thresholds["dvarsmt"],
        "dvarsmet": thresholds["dvarsmet"],
        "criterion": criterion, "flags": source,
    }

    return row, trace


def _worst_run(runs):
    """
    The session level summary of its BOLD runs.

    Every column but the counts describes one run -- the worst of them, by the
    percentage of frames flagged and then by peak displacement -- so that they
    can be read together rather than as statistics of different runs.
    """
    if not runs:
        return {}

    def badness(run):
        flagged = run["pct_bad"] if np.isfinite(run["pct_bad"]) else -1
        peak = run["fd_max"] if np.isfinite(run["fd_max"]) else -1
        return flagged, peak

    worst = max(runs, key=badness)
    tsnrs = [run["tsnr_median"] for run in runs if np.isfinite(run["tsnr_median"])]
    coverages = [run["coverage_pct"] for run in runs if np.isfinite(run["coverage_pct"])]

    return {
        "bold_n": len(runs),
        "bold_worst_run": worst["run"],
        "bold_worstFD": worst["fd_max"],
        "bold_worst_pct_bad": worst["pct_bad"],
        "bold_tsnr_min": round(min(tsnrs), 3) if tsnrs else np.nan,
        "bold_coverage_min": round(min(coverages), 3) if coverages else np.nan,
    }
