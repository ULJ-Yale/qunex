#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``workflow/run_qc_summary.py``

Compiles the QC information a study already holds into study level tables and
an interactive report.
"""

import csv
import json
import os
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from functools import partial

import qx_utilities.processing.core as pc
import qx_utilities.processing.workflow.qc_summary as qcs
import qx_utilities.processing.workflow.qc_summary_bold as qcb
import qx_utilities.processing.workflow.qc_summary_report as qcr
from qx_utilities.general.log import ReportLog


# --------------------------------------------------------- the command preamble
#
# What the command does, shown once at the head of the report, and the
# parameters it quotes back. A dedented block rather than lines carrying their
# own `\n    `: this is prose, it is read as prose, and it should be reviewable
# as prose. The parameter list is a list rather than a format string with one
# interpolation each, so it cannot drift from `options`.
QC_SUMMARY_PURPOSE = """\
QuNex writes quality control information at every stage of processing and in
many places in the file hierarchy. This command reads what is already there --
the registration and myelin maps, the FreeSurfer statistics, the BOLD movement
and scrubbing files, the diffusion eddy report -- and compiles it into one set
of study level tables and, optionally, an interactive report. It computes
nothing new and changes nothing it reads. A session that has not reached a
processing stage yet contributes blanks for that stage: that is information the
report presents, not a failure."""

QC_SUMMARY_PARAMETERS = [
    "qc_summary_modules",
    "qc_summary_report",
    "qc_summary_tsnr",
    "qc_summary_warp_jac",
    "qc_summary_mni_template",
    "qc_summary_diag_k",
    "hcp_suffix",
    "bolds",
    "mov_bad",
    "mov_fd",
    "mov_dvars",
    "mov_dvarsme",
]


def run_qc_summary(sinfo, options, overwrite=False, thread=0):
    """
    ``run_qc_summary [... processing options]``

    Compile the study's quality control information into tables and a report.

    ..  qx_command:
        type: processing.study

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the session information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parelements (int, default 1):
            How many sessions to read in parallel. The command is run once for
            the whole study, so this -- and not `parsessions` -- is the knob
            that speeds it up.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Each run
            writes into a folder of its own, named after the time it started,
            so there is normally nothing to overwrite.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --bolds (str, default 'all'):
            Which bold images (as they are specified in the batch.txt file) to
            report on. It can be a single type (e.g. 'task'), a pipe separated
            list (e.g. 'WM|Control|rest') or 'all' to report on all.

        --boldname (str, default 'bold'):
            The default name of the bold files in the images folder.

        --nifti_tail (str, default ''):
            The tail of NIfTI volume images to use. It selects the `.bstats`
            and `.scrub` files the BOLD statistics are read from.

        --cifti_tail (str, default ''):
            The tail of CIFTI images to use. It selects the dense timeseries
            the temporal SNR and cortical coverage are read from.

        --bold_variant (str, default ''):
            Optional variant of bold preprocessing. If specified, the BOLD
            images in `images/functional<bold_variant>` will be reported on.

        --img_suffix (str, default ''):
            Specifies a suffix for 'images' folder to enable support for
            multiple parallel workflows. Empty if not used.

        --hcp_suffix (str, default ''):
            Specifies a suffix for the session's folder in the HCP folder, if
            the data is processed in multiple ways.

        --mov_bad (str, default 'udvarsme'):
            Which criterion to report bad frames by. The value names a column
            of the `.scrub` file that `compute_bold_stats` wrote, so the frames
            reported here are the frames preprocessing itself excluded:

            - 'mov'       ... Frame displacement threshold (fdt) is exceeded.
            - 'dvars'     ... Image intensity normalized root mean squared error
              (RMSE) threshold (dvarsmt) is exceeded.
            - 'dvarsme'   ... Median normalised RMSE threshold (dvarsmet) is
              exceeded.
            - 'idvars'    ... Both fdt and dvarsmt are exceeded (i for
              intersection).
            - 'idvarsme'  ... Both fdt and dvarsmet are exceeded.
            - 'udvars'    ... Either fdt or dvarsmt are exceeded (u for union).
            - 'udvarsme'  ... Either fdt or dvarsmet are exceeded (default).

            For more detailed description please see wiki entry on Movement
            scrubbing.

        --mov_fd (float, default 0.5):
            Frame displacement threshold (in mm) to report bad frames by. Given
            explicitly, it overrides the threshold `compute_bold_stats` used and
            the frame counts are recomputed and marked as exploratory.

        --mov_dvars (float, default 3.0):
            The (mean normalized) dvars threshold to report bad frames by. As
            with --mov_fd, giving it explicitly recomputes the counts.

        --mov_dvarsme (float, default 1.5):
            The (median normalized) dvarsm threshold to report bad frames by. As
            with --mov_fd, giving it explicitly recomputes the counts.

        --mov_before (int, default 0):
            How many frames before each frame identified as bad to also count as
            bad, when the counts are recomputed.

        --mov_after (int, default 0):
            How many frames after each frame identified as bad to also count as
            bad, when the counts are recomputed.

        --qc_summary_modules (str, default 'prefs fs postfs bold dwi'):
            Which processing stages to compile information for. A space, comma
            or pipe separated list of:

            - 'prefs'   ... Registration to MNI, from the PreFreeSurfer warp.
            - 'fs'      ... The FreeSurfer recon, in native space.
            - 'postfs'  ... The fs_LR surface registration and myelin maps.
            - 'bold'    ... BOLD movement, scrubbing, temporal SNR and coverage.
            - 'dwi'     ... Diffusion, from the FSL eddy QC report.

        --qc_summary_report (str, default 'yes'):
            Whether to build the interactive HTML report (yes) or to write the
            tables alone (no).

        --qc_summary_tsnr (str, default 'yes'):
            Whether to compute BOLD temporal SNR and cortical coverage (yes) or
            not (no). This reads every dense timeseries and is the slowest part
            of the command.

        --qc_summary_warp_jac (str, default 'yes'):
            Whether to compute the Jacobian determinant of the PreFreeSurfer
            warp (yes) or not (no). Requires FSL; without it the columns are
            left blank.

        --qc_summary_mni_template (str, default ''):
            The path to an MNI template to compute registration similarity
            against. Without it, similarity is computed against the study's own
            group mean alone.

        --qc_summary_diag_k (float, default 3.0):
            The robust standard deviation threshold at which a session's value
            is called atypical for the study when localising the likely failure
            step. Lower is more sensitive.

    Returns:
        --log (ReportLog):
            The command's log object, carrying its report and its status.

    Notes:
        Use:
            run_qc_summary reads the quality control information the processing
            pipelines have already written for every session of the study, and
            compiles it into one place. It is a reporting command: it computes
            no new imaging results and modifies nothing it reads.

            Each run writes a folder of its own, named after the time it
            started, into the study's QC folder::

                <sessionsfolder>/QC/qc_summary_<YYYY-MM-DD_HH.MM.SS>/

            Because the folder is named after the run, results of several runs
            sit side by side and nothing is ever overwritten. Two runs started
            within the same second would name the same folder, so the second
            of them takes a `_2` suffix, the third a `_3`, and so on.

        Missing data:
            A session that has not reached a processing stage, or whose files
            cannot be read, contributes blank columns for that stage and a
            warning in the log. It is never dropped from the tables and it never
            fails the command: which sessions are missing what is one of the
            things the summary is for.

    Examples:
        Using the defaults::

            qunex run_qc_summary \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions

        Reading eight sessions at a time, without the slow temporal SNR pass::

            qunex run_qc_summary \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --parelements=8 \\
                --qc_summary_tsnr=no

        The structural stages alone, tables only::

            qunex run_qc_summary \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --qc_summary_modules="prefs fs postfs" \\
                --qc_summary_report=no
    """
    log = ReportLog()

    log.rule()
    log.info(f"Study QC summary \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]")
    log.action("Compiling", "study QC summary ...", options["run"], level="info")
    log.blank()
    log.info(QC_SUMMARY_PURPOSE)

    log.step("Using parameters")
    for name in QC_SUMMARY_PARAMETERS:
        log.detail(f"--{name}: {options[name]}")

    qcfolder = run_folder(options["sessionsfolder"], options["run"], _log=log)

    modules = options["qc_summary_modules"]

    # sessions are read independently, so they can be read at once -- but not
    # under `--test`, where there is nothing to read and a serial report is the
    # readable one
    parelements = options["parelements"] if options["run"] == "run" else 1
    log.step(f"Compiling information for sessions, {parelements} at a time")

    read = partial(session_metrics, options=options, modules=modules)
    if parelements == 1:
        results = [read(session) for session in sinfo]
    else:
        with ProcessPoolExecutor(parelements) as pool:
            results = list(pool.map(read, sinfo))

    rows, runs, traces, bases = [], [], {}, {}
    for result in results:
        log.raw(result["r"])
        rows.append(result["row"])
        runs.extend(result["runs"])
        traces.update(result["traces"])
        if result["base"]:
            bases[result["row"]["session"]] = result["base"]

    if "prefs" in modules:
        log.step("Comparing each session's registration against the study")
        group, template = qcs.group_registration(
            bases,
            qcfolder,
            options["qc_summary_mni_template"],
            options["run"],
            _log=log,
        )
        for row in rows:
            if row["session"] in group:
                row["reg_group_ncc"] = group[row["session"]]
            if row["session"] in template:
                row["reg_template_ncc"] = template[row["session"]]

    qcs.diagnose(rows, options["qc_summary_diag_k"])
    qcs.note_completeness(rows, modules)

    written = write_tables(qcfolder, rows, runs, traces, options, _log=log)
    if options["qc_summary_report"]:
        written += write_report(qcfolder, rows, runs, traces, options, _log=log)

    missing = sum(1 for row in rows if not row["stages_missing"] == "")
    flagged = sum(1 for row in rows if row["likely_failure_step"] != "OK")

    return log.finish(
        f"compiled QC information for {len(rows)} sessions and {len(runs)} BOLD runs, "
        f"{missing} sessions missing a stage, {flagged} flagged for review, "
        f"{written} files written"
    )


# the order the session table's columns are written in. A column no session has
# a value for is left out of the file entirely rather than written empty
SESSION_COLUMNS = [
    "session",
    "reg_group_ncc", "reg_template_ncc", "mni_brain_volume_ml", "t1t2_ratio_median",
    "warp_jac_min", "warp_jac_max", "warp_jac_pct_folded",
    "fs_etiv_ml", "fs_brainseg_ml", "fs_surface_holes", "fs_mean_thickness",
    "t1_wg_cnr", "t1_wg_contrast",
    "myelin_mean_L", "myelin_mean_R", "myelin_asym", "myelin_cv",
    "areal_distortion_p95", "edge_distortion_mean", "thickness_mean", "thickness_sd",
    "n_vertices_L", "n_vertices_R",
    "bold_n", "bold_worst_run", "bold_worstFD", "bold_worst_pct_bad",
    "bold_tsnr_min", "bold_coverage_min",
    "dwi_motion_abs", "dwi_motion_rel", "dwi_outliers_pct", "dwi_cnr_mean",
    "likely_failure_step", "diagnosis_evidence", "completeness", "stages_missing",
]


def write_tables(qcfolder, rows, runs, traces, options, *, _log):
    """
    Write the tables and the per frame traces into the run's folder.

    Tab separated, because the values include the diagnosis evidence and that
    reads as prose with commas in it. Nothing is ever overwritten: the folder
    is named after the moment the run started, so a second run sits beside the
    first rather than on top of it.

    Parameters:
        qcfolder (str): the run's own folder.
        rows (list): one row per session.
        runs (list): one row per BOLD run.
        traces (dict): the per frame traces, keyed ``<session>/<run>``.
        options (dict): the command's options.
        _log: the log to report into.

    Returns:
        int: how many files were written.
    """
    written = 0

    columns = [name for name in SESSION_COLUMNS if any(name in row for row in rows)]
    columns += sorted({name for row in rows for name in row} - set(columns))

    tables = [(os.path.join(qcfolder, "qc_summary.tsv"), columns, rows)]
    if runs:
        tables.append(
            (os.path.join(qcfolder, "qc_summary_bold.tsv"), qcb.RUN_COLUMNS, runs))

    for path, header, table in tables:
        if options["run"] != "run":
            _log.detail(f"test, not written: {path}")
            continue
        with open(path, "w", newline="") as tsv:
            writer = csv.DictWriter(tsv, fieldnames=header, delimiter="\t",
                                    extrasaction="ignore")
            writer.writeheader()
            for row in table:
                writer.writerow({name: row.get(name, "") for name in header})
        _log.detail(f"wrote {os.path.basename(path)} ({len(table)} rows)")
        written += 1

    if traces:
        path = os.path.join(qcfolder, "qc_summary_bold_traces.json")
        if options["run"] != "run":
            _log.detail(f"test, not written: {path}")
        else:
            with open(path, "w") as tracefile:
                json.dump(traces, tracefile)
            _log.detail(f"wrote {os.path.basename(path)} ({len(traces)} runs)")
            written += 1

    return written


def run_folder(sessionsfolder, run, *, _log):
    """
    Resolve the run's own folder, and create it unless this is a dry run.

    The folder is named after the moment the run started, so the results of
    several runs sit side by side and nothing is ever overwritten. The name is
    only good to the second, though, and two runs started inside the same
    second would otherwise share it -- so a name already taken takes a ``_2``,
    then a ``_3``. The folder is created without ``exist_ok``, which is what
    settles it: two processes that resolved the same free name cannot both
    take it, since the loser is told the directory exists and tries the next
    name.

    Parameters:
        sessionsfolder (str): the study's sessions folder.
        run (str): ``options["run"]`` -- nothing is created unless it is
            ``"run"``.
        _log: the log to report into.

    Returns:
        str: the folder the run writes into.
    """
    base = os.path.join(
        sessionsfolder,
        "QC",
        "qc_summary_" + datetime.now().strftime("%Y-%m-%d_%H.%M.%S"),
    )

    folder, index = base, 1
    while True:
        if run != "run":
            if not os.path.exists(folder):
                break
        else:
            try:
                os.makedirs(folder)
                break
            except FileExistsError:
                pass
        index += 1
        folder = f"{base}_{index}"

    _log.step(f"Writing results to {folder}")
    if run != "run":
        _log.detail(f"test, not created: {folder}")
    return folder


def write_report(qcfolder, rows, runs, traces, options, *, _log):
    """
    Build the interactive report and write it beside the tables.

    Two kinds of trouble meet here and they are not the same failure. A session
    with nothing to report is reported as such and the report is what carries
    that to the reader. Being unable to build the report at all -- no template,
    no QuNex environment, nowhere to write -- is the command failing to do what
    it was asked to do, so it is an error and it is counted as one. The tables
    already written are untouched by it and stay where they are.

    Parameters:
        qcfolder (str): the run's own folder.
        rows (list): one row per session.
        runs (list): one row per BOLD run.
        traces (dict): the per frame traces, keyed ``<session>/<run>``.
        options (dict): the command's options.
        _log: the log to report into.

    Returns:
        int: how many files were written.
    """
    path = os.path.join(qcfolder, "qc_summary_report.html")
    if options["run"] != "run":
        _log.detail(f"test, not written: {path}")
        return 0

    try:
        report = qcr.build_report(rows, runs, traces, options, _log=_log)
        with open(path, "w", encoding="utf-8") as html:
            html.write(report)
    except Exception as error:
        _log.error(f"the QC report could not be built: {error}\n"
                   f"the tables in {qcfolder} were written and are unaffected")
        return 0

    _log.detail(f"wrote {os.path.basename(path)} "
                f"({len(report) / (1024 * 1024):.1f} MB)")
    return 1


def session_metrics(session, options, modules):
    """
    Compile one session's measures, reporting rather than raising on failure.

    Every stage is read independently and every one of them is allowed to come
    back empty. The guard around the lot is what keeps one unreadable session
    -- a truncated statistics file, an image written while the disk filled --
    from ending a study's run.

    Reports into a log of its own and hands back its text rather than writing
    into the caller's, which is what lets the sessions be read in parallel: a
    worker in another process cannot append to the parent's log.

    Parameters:
        session (dict): the session information from the batch file.
        options (dict): the command's options.
        modules (list): the processing stages to read.

    Returns:
        dict: ``{"r": report text, "row": {...}, "runs": [...],
        "traces": {...}, "base": HCP folder or None}``.
    """
    _log = ReportLog()
    _log.step(f"Working on {session['id']} ...")

    row = {"session": session["id"]}
    runs, traces = [], {}
    base = None

    try:
        folders = pc.get_session_folders(session, options)
        base = folders.get("hcp")
        if not base or not os.path.isdir(base):
            _log.warning(f"no HCP folder for {session['id']}, "
                         "only the BOLD measures can be read")
            base = None
        else:
            name = session["id"] + options["hcp_suffix"]
            if "prefs" in modules:
                row.update(qcs.prefs_metrics(base, _log=_log))
                if options["qc_summary_warp_jac"]:
                    row.update(qcs.warp_jacobian(base, options["run"], _log=_log))
            if "fs" in modules:
                row.update(qcs.fs_metrics(base, name, _log=_log))
                row.update(qcs.contrast_metrics(base, name, _log=_log))
            if "postfs" in modules:
                row.update(qcs.postfs_metrics(base, name, _log=_log))
            if "dwi" in modules:
                row.update(qcs.dwi_metrics(base, _log=_log))

        # the BOLD measures are read from the images folder, so they are there
        # to be read whether or not the session has been through the HCP
        # pipelines
        if "bold" in modules:
            runs, traces, rollup = qcb.bold_metrics(session, options, _log=_log)
            row.update(rollup)

        _log.detail(f"{len(row) - 1} measures read, "
                    f"{len(runs)} BOLD run{'' if len(runs) == 1 else 's'}")
    except Exception:
        _log.error(f"could not compile QC information for {session['id']}, "
                   f"the session is reported with no data: \n{traceback.format_exc()}")

    return {"r": _log.text, "row": row, "runs": runs, "traces": traces, "base": base}
