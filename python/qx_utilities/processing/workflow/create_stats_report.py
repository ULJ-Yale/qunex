#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``workflow/create_stats_report.py``

Creates a report of movement and image statistics across sessions.
"""

# Created by Grega Repovs on 2016-12-17.
# Code split from dofcMRIp_core gCodeP/preprocess codebase.
# Copyright (c) Grega Repovs. All rights reserved.

import os
import traceback
from datetime import datetime

import qx_utilities.processing.core as pc
import qx_utilities.processing.mov_stats as ms
import qx_utilities.general.meltmovfidl as gm
from qx_utilities.general.log import ReportLog
from qx_utilities.processing.workflow import dryrun


# --------------------------------------------------------- the command preamble
#
# What the command does, shown once at the head of every session report, and
# the parameters it quotes back. A dedented block rather than lines carrying
# their own `\n    `: this is prose, it is read as prose, and it should be
# reviewable as prose. The parameter list is a list rather than a format string
# with one interpolation each, so it cannot drift from `options`.
STATS_REPORT_PURPOSE = """\
Movement correction parameters and computed BOLD statistics are used to create
per session plots, fidl snippets and group reports. Only the images named by
--bolds are processed; see the documentation for the other parameters."""

STATS_REPORT_PARAMETERS = [
    "mov_dvars",
    "mov_dvarsme",
    "mov_fd",
    "mov_radius",
    "mov_fidl",
    "mov_post",
    "mov_pref",
]


def create_stats_report(sinfo, options, overwrite=False, thread=0):
    """
    ``create_stats_report [... processing options]``

    Process movement correction parameters and computed BOLD statistics to
    create per session plots and fidl snippets and group reports.

    ..  qx_command:
        type: processing.session

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the session information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --bolds (str, default 'rest'):
            Which bold images (as they are specified in the batch.txt file) to
            copy over. It can be a single type (e.g. 'task'), a pipe separated
            list (e.g. 'WM|Control|rest') or 'all' to copy all.

        --boldname (str, default 'bold'):
            The default name of the bold files in the images folder.

        --nifti_tail (str, default ''):
            The tail of NIfTI volume images to use.

        --bold_variant (str, default ''):
            Optional variant of bold preprocessing. If specified, the BOLD
            images in `images/functional<bold_variant>` will be processed.

        --img_suffix (str, default ''):
            Specifies a suffix for 'images' folder to enable support for
            multiple parallel workflows. Empty if not used.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --mov_radius (int, default 50):
            Estimated head radius (in mm) for computing frame displacement
            statistics.

        --mov_fd (float, default 0.5):
            Frame displacement threshold (in mm) to use for identifying bad
            frames.

        --mov_dvars (float, default 3.0):
            The (mean normalized) dvars threshold to use for identifying bad
            frames. Later referred to as dvarsmt.

        --mov_dvarsme (float, default 1.5):
            The (median normalized) dvarsm threshold to use for identifying bad
            frames. Later referred to as dvarsmet.

        --mov_after (int, default 0):
            How many frames after each frame identified as bad to also exclude
            from further processing and analysis.

        --mov_before (int, default 0):
            How many frames before each frame identified as bad to also exclude
            from further processing and analysis.

        --tr (float, default 2.5):
            TR of the BOLD files.

        --mov_pref (str, default ''):
            The prefix to be used for the figure plot files.

        --mov_plot (str, default 'mov_report'):
            The base name of the plot files. If set to empty no plots are
            generated.

        --mov_mreport (str, default 'movement_report.txt'):
            The name of the group movement report file. If set to an empty
            string, no file is generated.

        --mov_sreport (str, default 'movement_scrubbing_report.txt'):
            The name of the group scrubbing report file. If set to an empty
            string, no file is generated.

        --mov_preport (str, default 'movement_report_post.txt'):
            The name of group report file with stats computed with frames
            identified as bad exluded from analysis. If set to an empty
            string, no file is generated.

        --mov_post (str, default 'udvarsme'):
            The criterium for identification of bad frames that is used when
            generating a post scrubbing statistics group report. The value names
            a column of the `.scrub` file that `compute_bold_stats` wrote:

            - 'mov'       ... Frame displacement threshold (fdt) is exceeded.
            - 'dvars'     ... Image intensity normalized root mean squared error
              (RMSE) threshold (dvarsmt) is exceeded.
            - 'dvarsme'   ... Median normalised RMSE threshold (dvarsmet) is
              exceeded.
            - 'idvars'    ... Both fdt and dvarsmt are exceeded (i for
              intersection).
            - 'idvarsme'  ... Both fdt and dvarsmet are exceeded.
            - 'udvars'    ... Either fdt or dvarsmt are exceeded (u for union).
            - 'udvarsme'  ... Either fdt or udvarsmet are exceeded (default).
            - 'none'.

            For more detailed description please see wiki entry on Movement
            scrubbing.

        --mov_fidl (str, default 'udvarsme'):
            Whether to create fidl file snippets with listed bad frames, and
            what criterium to use for the definition of bad frames. The value
            names a column of the `.scrub` file that `compute_bold_stats` wrote:

            - 'mov'       ... Frame displacement threshold (fdt) is exceeded.
            - 'dvars'     ... Image intensity normalized root mean squared error
              (RMSE) threshold (dvarsmt) is exceeded.
            - 'dvarsme'   ... Median normalised RMSE threshold  (dvarsmet) is
              exceeded.
            - 'idvars'    ... Both fdt and dvarsmt are exceeded (i for
              intersection).
            - 'idvarsme'  ... Both fdt and dvarsmet are exceeded.
            - 'udvars'    ... Either fdt or dvarsmt are exceeded (u for union).
            - 'udvarsme'  ... Either fdt or udvarsmet are exceeded (default).
            - 'none'      ... Set to 'none' to not generate them.

            For more detailed description please see wiki entry on Movement
            scrubbing.

        --mov_pdf (str, default 'movement_plots'):
            The name of the folder in sessions/QC/movement in which to copy
            the individuals' movement plots.

    Notes:
        Use:
            create_stats_report processes movement correction parameters and
            computed BOLD statistics to create per session plots and fidl
            snippets and group reports.

            For each session it saves into images/functional/movement:

            --`bold<nifti_tail>_<mov_plot>_cor.pdf`
                A plot of movement correction parameters for each of the BOLD
                files.
            --`bold<nifti_tail>_<mov_plot>_dvars.pdf`
                A plot of frame displacement and dvarsm statistics with frames
                that are identified as bad marked in blue.
            --`bold<nifti_tail>_<mov_plot>_dvarsme.pdf`
                A plot of frame displacement and dvarsme statistics with frames
                that are identified as bad marked in blue.
            --`bold[N]<nifti_tail>_scrub.fidl`
                A fidl filesnippet that lists, which frames are to be excluded
                from the analysis.

            For the group level it creates three report files that are stored in
            the <sessionsfolder>/QC/movement folder. These files are:

            - ``<mov_mreport>`` (bold<nifti_tail>_movement_report.txt by default)
                This file lists for each session and bold file mean, sd, range,
                max, min, median, and squared mean divided by max statistics for
                each of the 6 movement correction parameters. It also prints
                mean, median, maximum, and standard deviation of frame
                displacement statistics. The purpose of this file is to enable
                easy session and group level analysis of movement in the scanner.

            - ``<mov_preport>`` (bold<nifti_tail>_movement_report_post.txt by default)
                This file has the same structure and information as the above,
                with frames marked as bad excluded from the statistics
                computation. This enables session and group level assessment of
                the effects of scrubbing.

            - ``<mov_sreport>`` (bold<nifti_tail>_movement_scrubbing_report.txt by default)
                This file lists for each BOLD of each session the number and the
                percentage of frames that would be marked as bad and excluded
                from the analyses when a specific exclusion criteria would be
                used. Again, the file supports session and group level analysis
                of movement scrubbing.

            Extra notes and dependencies:
                The statistics are computed and the plots drawn in Python. The
                command requires that movement correction parameters files and
                bold statistics data files (results of the compute_bold_stats
                command) are present in the expected locations.

                Session statistics are appended to the group level report files
                as they are being computed. To avoid messy group level files, it
                is recommended to run the command with parsessions set to 1
                (example 1), to enforce sequential processing and adding of
                information to group level statistics files. Another option is
                to run the processing in two steps. The first step with multiple
                parsessions to speed up generation of session level maps
                (example 2), and then the second step with a single core,
                omitting the slow generation of session specific plots.

    Examples:
        ::

            qunex create_stats_report \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --bolds=all \\
                --parsessions=1

        ::

            qunex create_stats_report \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --bolds=all \\
                --parsessions=10

        ::

            qunex create_stats_report \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --bolds=all \\
                --nifti_tail=_hp2000_clean \\
                --parsessions=1 \\
                --mov_plot=""
    """
    log = ReportLog()

    preport = {
        "plotdone": "done",
        "boldok": 0,
        "procok": "ok",
        "boldmissing": 0,
        "boldskipped": 0,
    }

    try:
        log.rule()
        log.info(f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]")
        log.action("Creating", "BOLD movement and statistics report ...", options["run"], level="info")
        log.blank()
        log.info(STATS_REPORT_PURPOSE)

        pc.do_options_check(options, sinfo, "create_stats_report")
        d = pc.get_session_folders(sinfo, options)

        if overwrite:
            ostatus = "will"
        else:
            ostatus = "will not"

        log.step("Using parameters")
        for name in STATS_REPORT_PARAMETERS:
            log.detail(f"--{name}: {options[name]}")

        log.step(f"Working on BOLD information in {d['s_bold_mov']}")
        log.detail(f"images{options['img_suffix']}/functional{options['bold_variant']} will be processed")
        log.detail("the resulting plots will be saved there")
        log.detail(f"{', '.join(options['bolds'].split('|'))} BOLD files will be processed (see --bolds)")
        log.detail(f"existing results {ostatus} be overwritten (see --overwrite)")

        procbolds = []
        d = pc.get_session_folders(sinfo, options)

        # --- check for data

        if options["mov_plot"] != "":
            if (
                os.path.exists(
                    os.path.join(
                        d["s_bold_mov"],
                        options["mov_pref"] + options["mov_plot"] + "_cor.pdf",
                    )
                )
                and not overwrite
            ):
                log.detail("Movement plots already exists! Please use option --overwrite=yes to redo them!")
                preport["plotdone"] = "old"
                plot = ""
            else:
                plot = options["mov_plot"]
                preport["plotdone"] = "new"
        else:
            plot = ""
            preport["plotdone"] = "none"

        log.step(f"Checking for data in {d['s_bold_mov']}")

        bolds, bskip, preport["boldskipped"] = pc.use_or_skip_bold(sinfo, options, _log=log)

        for boldinfo in bolds:
            log.step("Working on " + boldinfo["name"] + " ...")

            try:
                # --- filenames
                f = pc.get_file_names(sinfo, options)
                f.update(pc.get_bold_file_names(sinfo, boldinfo["name"], options))

                # --- check for data availability

                status = True

                if os.path.exists(d["s_bold_mov"]):
                    # --- movement
                    status = pc.check_for_file(f["bold_mov"],
                        f"movement data present [{os.path.basename(f['bold_mov'])}]",
                        f"movement data missing [{os.path.basename(f['bold_mov'])}]",
                        status=status,
                        _log=log,
                    )
                    status = pc.check_for_file(f["bold_stats"],
                        f"stats data present [{os.path.basename(f['bold_stats'])}]",
                        f"stats data missing [{os.path.basename(f['bold_stats'])}]",
                        status=status,
                        _log=log,
                    )
                    status = pc.check_for_file(f["bold_scrub"],
                        f"scrub data present [{os.path.basename(f['bold_scrub'])}]",
                        f"scrub data missing [{os.path.basename(f['bold_scrub'])}]",
                        status=status,
                        _log=log,
                    )
                else:
                    log.detail("folder does not exist!")
                    status = False

                # --- check
                if status:
                    procbolds.append(boldinfo["bold_number"])
                    preport["boldok"] += 1
                else:
                    log.error("Files missing, skipping this bold run!")
                    preport["boldmissing"] += 1

            except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
                log.raw(str(errormessage))
            except Exception:
                log.error(f"Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n")

        # build the reports

        procbolds.sort()
        procbolds = [str(e) for e in procbolds]

        report = {}

        for tf in ["mov_mreport", "mov_sreport", "mov_preport"]:
            if options[tf] != "":
                tmpf = os.path.join(
                    d["qc_mov"],
                    options["boldname"] + options["nifti_tail"] + "_" + options[tf],
                )
                report[tf] = tmpf
                if os.path.exists(tmpf) and thread == 1:
                    dryrun.remove(log, options, tmpf)
            else:
                report[tf] = ""

        # a session can arrive here with nothing to report: no BOLD run named in
        # the batch file, or every one of them missing its movement files. That is
        # information, not a failure -- but running the report over an empty list
        # writes nothing, copies figures that were never drawn, and claims success
        # for it, so the session says what it has instead
        if not procbolds:
            log.warning(
                "no BOLD run has the movement and statistics files this report is "
                "built from, so there is nothing to report for this session"
            )
            preport["procok"] = "no data"
        else:
            runs = [options["boldname"] + e + options["nifti_tail"] for e in procbolds]

            # one line for both arms: `action` is what tags it "[TEST] Running ..."
            # under `--test`, so the run mode is the log's business and not a branch
            log.action(
                "Running",
                f"movement and statistics reporting for {', '.join(runs)}",
                options["run"],
            )

            if options["run"] != "run":
                for tf in ["mov_mreport", "mov_sreport", "mov_preport"]:
                    if report[tf] != "":
                        log.detail(f"test, not written: {report[tf]}")
                if options["mov_fidl"] != "none":
                    for run in runs:
                        log.detail(f"test, not written: {os.path.join(d['s_bold_mov'], run + '_scrub.fidl')}")
                preport["procok"] = "test"
            else:
                # failure arrives as an exception now, caught by the handlers below
                ms.report_movement_statistics(
                    d["s_bold_mov"], procbolds, sinfo["id"], report, options, plot, _log=log
                )
                preport["procok"] = "ok"

            if options["mov_plot"] != "" and options["mov_pdf"] != "no":
                for sf in ["cor", "dvars", "dvarsme"]:
                    tfolder = os.path.join(d["qc_mov"], options["mov_pdf"], sf)
                    if not os.path.exists(tfolder):
                        if options["run"] != "run":
                            log.detail(f"test, not created: {tfolder}")
                        else:
                            os.makedirs(tfolder)

                    froot = "%s%s_%s%s_%s.pdf" % (
                        options["boldname"],
                        options["nifti_tail"],
                        options["mov_pref"],
                        options["mov_plot"],
                        sf,
                    )
                    if os.path.exists(
                        os.path.join(tfolder, "%s-%s" % (sinfo["id"], froot))
                    ):
                        dryrun.remove(
                            log,
                            options,
                            os.path.join(tfolder, "%s-%s" % (sinfo["id"], froot)),
                        )
                    dryrun.link_or_copy(
                        log,
                        options,
                        os.path.join(d["s_bold_mov"], froot),
                        os.path.join(tfolder, "%s-%s" % (sinfo["id"], froot)),
                    )
                    if options["run"] == "run":
                        log.detail(f"copying {os.path.join(d['s_bold_mov'], froot)} to {os.path.join(tfolder, '%s-%s' % (sinfo['id'], froot))}")

            if (
                options["mov_fidl"] in ms.CRITERIA
                and options["event_file"] != ""
                and options["bolds"] != ""
            ):
                concf = os.path.join(d["s_bold_concs"], options["bolds"] + ".conc")
                fidlf = os.path.join(d["s_bold_events"], options["event_file"] + ".fidl")
                ipatt = "_%s_scrub.fidl" % (options["mov_fidl"])

                if options["run"] != "run":
                    log.detail(
                        f'test, not written: {fidlf.replace(".fidl", ipatt)}'
                    )
                elif os.path.exists(concf) and os.path.exists(fidlf):
                    try:
                        gm.meltmovfidl(concf, ipatt, fidlf, fidlf.replace(".fidl", ipatt))
                    except Exception:
                        log.warning(
                            f"Failed to create a melted fidl file! ({sinfo['id']})"
                        )
                        raise
                else:
                    log.warning("Files missing, failed to create a melted fidl file!")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        log.info(f"BOLD statistics and movement report failed on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}")
        log.rule()
        preport["procok"] = "failed"
    except Exception:
        log.info(f"BOLD statistics and movement report failed with and unknown error: \n...................................\n{traceback.format_exc()}...................................\n")
        preport["procok"] = "failed"

    if preport["procok"] == "ok":
        log.blank()
        log.info(f"BOLD statistics and movement report completed on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}")
        log.rule()

    rstatus = (
        "BOLDs ok: %(boldok)2d, missing data: %(boldmissing)2d, processing: %(procok)s, skipped: %(boldskipped)s"
        % (preport)
    )
    if preport["procok"] == "ok":
        rstatus += ", plots: %(plotdone)s" % (preport)

    return log.result(
        rstatus,
        preport["boldmissing"] + (preport["procok"] == "failed"),
        sinfo["id"],
    )
