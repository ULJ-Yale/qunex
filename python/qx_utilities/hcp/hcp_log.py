#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``hcp_log.py``

The report text built by every HCP processing command.

QuNex keeps two layers of logs. This module owns the outer one, the **runlog**:
the human readable summary of what a command did to one session, which
``general.process`` writes to ``Log-<command>-<timestamp>.log`` and prints to
the console. The inner layer, the **comlog**, is the raw stdout/stderr of each
external pipeline call and is written separately by ``processing.core``.

Commands used to build the runlog by appending to a local string named ``r``
and passing it into (and back out of) every helper. The classes here hold that
text instead, so code states *what happened* and this module decides how it is
spelled:

- :class:`ReportLog` is a plain accumulator with the level vocabulary
  (``step``/``detail``/``warning``/``error``) and the external-call wrappers.
  Per-BOLD / per-group executors use it: they have report text but no
  session header of their own.
- :class:`SessionLog` adds the per-session header and :meth:`SessionLog.finish`,
  which closes the report and builds the ``(text, status)`` value a command
  returns to ``general.process``.
"""

import traceback
from contextlib import contextmanager
from datetime import datetime

import qx_utilities.general.exceptions as ge
import qx_utilities.processing.core as pc

# separator used to frame the per-session reports
REPORT_RULE = "------------------------------------------------------------"

# timestamp format used in the per-session reports
REPORT_TIME = "%A, %d. %B %Y %H:%M:%S"

# how each severity is spelled in the runlog
PREFIXES = {
    "step": "---> ",
    "detail": "     ... ",
    "warning": "---> WARNING: ",
    "error": "---> ERROR: ",
    "info": "",
}


class ReportLog:
    """
    Accumulating report text, spelled in the QuNex runlog vocabulary.

    Holds the growing report as a list of parts and renders it on demand. This
    is the piece shared by session-level commands and their per-BOLD / per-group
    executors; :class:`SessionLog` extends it with the header and footer.
    """

    def __init__(self):
        self._parts = []

    # ------------------------------------------------------------------ text

    @property
    def text(self) -> str:
        """The report rendered so far."""
        return "".join(self._parts)

    def __str__(self) -> str:
        return self.text

    def capture(self, text: str) -> None:
        """
        Adopt a report string returned by a ``processing.core`` helper.

        Those helpers take the report so far and hand back the report with their
        own output appended, so the returned string replaces the buffer rather
        than extending it.
        """
        self._parts = [text]

    def add(self, other) -> None:
        """Append the text of another report log (e.g. an executor's result)."""
        self._parts.append(other.text if isinstance(other, ReportLog) else other)

    # ---------------------------------------------------------------- levels

    def _emit(self, level, message, args):
        if args:
            message = message % args
        self._parts.append("\n" + PREFIXES[level] + message)

    def step(self, message: str, *args) -> None:
        """Record a processing step: ``---> <message>``."""
        self._emit("step", message, args)

    def detail(self, message: str, *args) -> None:
        """Record a sub-detail of the preceding step: ``     ... <message>``."""
        self._emit("detail", message, args)

    def warning(self, message: str, *args) -> None:
        """Record a warning: ``---> WARNING: <message>``."""
        self._emit("warning", message, args)

    def error(self, message: str, *args) -> None:
        """Record an error: ``---> ERROR: <message>``."""
        self._emit("error", message, args)

    def info(self, message: str, *args) -> None:
        """Record an unprefixed line."""
        self._emit("info", message, args)

    def blank(self, count: int = 1) -> None:
        """Insert blank lines."""
        self._parts.append("\n" * count)

    def raw(self, text: str) -> None:
        """Append text verbatim, with no prefix and no added newline."""
        self._parts.append(text)

    @contextmanager
    def section(self, title: str):
        """Frame a block of output between report rules."""
        self._parts.append("\n\n%s\n%s\n\n" % (REPORT_RULE, title))
        try:
            yield self
        finally:
            self._parts.append("\n%s\n" % REPORT_RULE)

    def pipeline_command(self, command: str, marker: str = "--") -> None:
        """
        Show the HCP pipeline command QuNex is about to run, one flag per line.

        Parameters:
            command: the assembled command line.
            marker: the flag separator as it appears in ``command``. Commands
                that pad their flags for readability pass that padding along
                with the dashes.
        """
        body = command.replace(marker, "\n    --")
        if marker == "--":
            # commands assembled with line continuations carry alignment padding
            body = body.replace("             ", "")
        with self.section("Running HCP Pipelines command via QuNex:"):
            self.raw(body)

    # ---------------------------------------------------------------- errors

    def command_failed(self, e: ge.CommandFailed, step: str = None) -> None:
        """Record a ``ge.CommandFailed`` raised inside the command."""
        details = "\n     ".join(e.report)
        if step is None:
            self._parts.append(
                "\n\nERROR in completing %s:\n     %s\n" % (e.function, details)
            )
        else:
            self._parts.append(
                "\n\nERROR in completing %s at %s:\n     %s\n"
                % (step, e.function, details)
            )

    def unknown_error(self) -> None:
        """Record an unexpected exception, including the current traceback."""
        dots = "." * 35
        self._parts.append(
            "\nERROR: Unknown error occured: \n%s\n%s%s\n"
            % (dots, traceback.format_exc(), dots)
        )

    # ------------------------------------------------------- external calls

    def run_external(self, checkfile, command, description, **kwargs):
        """
        Run an external pipeline command, threading the runlog through it.

        Wraps ``pc.run_external_for_file`` so the caller neither passes nor
        reassigns the report text.

        Returns:
            ``(endlog, report, failed)`` from the underlying call.
        """
        text, endlog, report, failed = pc.run_external_for_file(
            checkfile, command, description, r=self.text, **kwargs
        )
        self.capture(text)
        return endlog, report, failed

    def check_gdc_coeff_file(self, gdcstring, hcp, sinfo, run=True):
        """
        Resolve the gradient distortion coefficient file for this session.

        Wraps ``hcp_utils.check_gdc_coeff_file`` so the caller neither passes nor
        reassigns the report text.

        Returns:
            ``(gdcfile, run)`` from the underlying call.
        """
        from qx_utilities.hcp import hcp_utils

        gdcfile, text, run = hcp_utils.check_gdc_coeff_file(
            gdcstring, hcp, sinfo, self.text, run
        )
        self.capture(text)
        return gdcfile, run

    def parse_icafix_bolds(self, options, bolds, msmall=False):
        """
        Group BOLDs for ICAFix, threading the report through the parser.

        Returns:
            ``(single_fix, icafix_bolds, icafix_groups, bolds_ok)``.
        """
        from qx_utilities.hcp import hcp_utils

        single_fix, icafix_bolds, icafix_groups, bolds_ok, text = (
            hcp_utils.parse_icafix_bolds(options, bolds, self.text, msmall)
        )
        self.capture(text)
        return single_fix, icafix_bolds, icafix_groups, bolds_ok

    def parse_msmall_bolds(self, options, bolds):
        """
        Group BOLDs for MSMAll, threading the report through the parser.

        Returns:
            ``(msmall_groups, single_run, pars_ok)``.
        """
        from qx_utilities.hcp import hcp_utils

        msmall_groups, single_run, pars_ok, text = hcp_utils.parse_msmall_bolds(
            options, bolds, self.text
        )
        self.capture(text)
        return msmall_groups, single_run, pars_ok

    def check_for_file(self, checkfile, ok, bad, status=True):
        """
        Note the presence or absence of a file, appending ``ok`` or ``bad``.

        Wraps ``pc.check_for_file2`` so the caller neither passes nor reassigns
        the report text.

        Returns:
            the running status (True while every checked file has been present).
        """
        text, status = pc.check_for_file2(self.text, checkfile, ok, bad, status)
        self.capture(text)
        return status

    def check_for_files(self, checkfiles, ok, bad, all=False, status=True):
        """
        Note the presence of one or all of ``checkfiles``.

        Wraps ``pc.check_for_files`` so the caller neither passes nor reassigns
        the report text.

        Returns:
            ``(status, found_file)`` from the underlying call.
        """
        text, status, found = pc.check_for_files(
            self.text, checkfiles, ok, bad, all, status
        )
        self.capture(text)
        return status, found

    def link_or_copy(self, source, target, status=None, name=None,
                     prefix=None, symlink=False):
        """
        Link or copy a file, appending the mapping outcome to the report.

        Wraps ``gc.link_or_copy`` so the caller neither passes nor reassigns the
        report text.

        Returns:
            the running status from the underlying call.
        """
        from qx_utilities.general import core as gc

        status, text = gc.link_or_copy(
            source, target, self.text, status, name, prefix, symlink
        )
        self.capture(text)
        return status

    def use_or_skip_bold(self, sinfo, options):
        """
        Resolve which BOLDs to use and which to skip for this session.

        Wraps ``pc.use_or_skip_bold`` so the caller neither passes nor reassigns
        the report text.

        Returns:
            ``(bolds, skipped, n_skipped)`` from the underlying call.
        """
        bolds, skipped, n_skipped, text = pc.use_or_skip_bold(
            sinfo, options, self.text
        )
        self.capture(text)
        return bolds, skipped, n_skipped

    def check_run(self, checkfile, full_test, description, overwrite=False):
        """
        Report what a run would do, without running it (the ``--test`` path).

        Wraps ``pc.check_run`` so the caller neither passes nor reassigns the
        report text.

        Returns:
            ``(passed, report, failed)`` from the underlying call.
        """
        passed, report, text, failed = pc.check_run(
            checkfile, full_test, description, self.text, overwrite=overwrite
        )
        self.capture(text)
        return passed, report, failed


class SessionLog(ReportLog):
    """
    Runlog for one session (or subject) processed by one command.

    The rendered text is what the command returns to ``general.process``, so the
    output format is deliberately the one QuNex users already read.

    Typical use::

        log = SessionLog(sinfo, options, "HCP DTI Fit pipeline")
        log.step("checking for data")
        log.error("bvals file not found: %s", path)
        return log.finish("HCP DTIFit failed", failed=1)
    """

    def __init__(
        self,
        sinfo,
        options,
        pipeline,
        mode=True,
        tail="",
        lead="\n",
        label="Session id",
    ):
        """
        Parameters:
            sinfo: session information dictionary; ``id`` names the session.
            options: command options; ``run`` and ``hcp_processing_mode`` are used.
            pipeline: human readable pipeline name, e.g. ``HCP DTI Fit pipeline``.
            mode: whether to show ``[hcp_processing_mode]`` in the opening line.
            tail: text appended after the opening line's trailing ``...``.
            lead: newlines between the session id block and the opening line.
            label: how the processed unit is named; subject level commands
                pass ``"Subject"``.
        """
        super().__init__()
        self._options = options
        self._pipeline = pipeline
        self._sid = sinfo["id"]

        self._parts.append("\n%s\n%s: %s \n[started on %s]" % (
            REPORT_RULE,
            label,
            self._sid,
            datetime.now().strftime(REPORT_TIME),
        ))

        action = pc.action("Running", options["run"])
        if mode:
            self._parts.append("%s%s %s [%s] ...%s" % (
                lead, action, pipeline, options["hcp_processing_mode"], tail,
            ))
        else:
            self._parts.append("%s%s %s ...%s" % (lead, action, pipeline, tail))

    # ---------------------------------------------------------------- finish

    def finish(self, report, failed=None, pipeline=None, lead="\n\n"):
        """
        Close the report and build the value the command returns.

        Every HCP command returns ``(report_text, (session_id, summary, failed))``
        -- a three-field status ``general.process`` unpacks as
        ``(sid, report, failed)``. This method builds exactly that, so a command
        can never return the malformed two-field status that made a whole run
        print "success status not reported".

        Parameters:
            report: the per-session summary string, or a ready three-field
                ``(session_id, summary, failed)`` status tuple.
            failed: number of failed units; required when ``report`` is a string,
                ignored when it is a tuple.
            pipeline: name for the closing line; defaults to the opening one.
            lead: newlines separating the footer from the preceding text.

        Returns:
            ``(report_text, (session_id, summary, failed))``.
        """
        self.close(pipeline=pipeline, lead=lead)
        return self.result(report, failed)

    def close(self, pipeline=None, lead="\n\n"):
        """
        Append the closing footer line.

        Usually reached through :meth:`finish`; call it directly only when a
        command appends more report text *after* the footer (e.g. a post-run
        snapshot diff) before building its status.

        Parameters:
            pipeline: name for the closing line; defaults to the opening one.
            lead: newlines separating the footer from the preceding text.
        """
        name = pipeline if pipeline is not None else self._pipeline
        self._parts.append("%s%s %s on %s\n%s" % (
            lead,
            name,
            pc.action("completed", self._options["run"]),
            datetime.now().strftime(REPORT_TIME),
            REPORT_RULE,
        ))

    def result(self, report, failed=None):
        """
        Build the ``(report_text, status)`` value the command returns.

        Enforces the three-field status contract (see :meth:`finish`).
        """
        if isinstance(report, tuple):
            if len(report) != 3:
                raise ValueError(
                    "HCP command status must be a 3-field "
                    "(session_id, summary, failed) tuple, got %d fields: %r"
                    % (len(report), report)
                )
            status = report
        else:
            if failed is None:
                raise ValueError(
                    "SessionLog.finish needs a failed count when report is a "
                    "summary string (got failed=None for %r)" % (report,)
                )
            status = (self._sid, report, failed)

        return (self.text, status)
