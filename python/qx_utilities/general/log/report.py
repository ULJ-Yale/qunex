#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``general.log.report``

The per-session report built by QuNex processing commands.

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
  (``step``/``detail``/``warning``/``error``) and wrappers around the
  ``processing.core`` / ``general.core`` helpers that used to thread the report
  string. Per-BOLD / per-group executors use it: they have report text but no
  session header of their own.
- :class:`SessionLog` adds the per-session header and :meth:`SessionLog.finish`,
  which closes the report and builds the ``(text, status)`` value a command
  returns to ``general.process``.

The ``processing.core`` / ``general.core`` helpers are imported lazily inside
the wrapper methods so this module stays importable from those packages.

Internally the report is a list of ``(depth, severity, message)`` records
rendered to text on demand, not a list of pre-formatted strings: severity and
nesting stay recoverable after the fact, so the report can be re-rendered (an
errors only digest, a machine readable form) without every call site changing.
Verbatim text -- :meth:`ReportLog.raw`, :meth:`ReportLog.capture`, the framing
rules -- is held as a ``RAW`` record and emitted untouched.
"""

import traceback
from contextlib import contextmanager
from datetime import datetime

import qx_utilities.general.exceptions as ge

# separator used to frame the per-session reports
REPORT_RULE = "------------------------------------------------------------"

# timestamp format used in the per-session reports
REPORT_TIME = "%A, %d. %B %Y %H:%M:%S"

# how each severity is spelled in the runlog, after the depth indent
PREFIXES = {
    "step": "---> ",
    "detail": "... ",
    "warning": "---> WARNING: ",
    "error": "---> ERROR: ",
    "info": "",
}

# severity of a record holding verbatim text: no newline, no prefix, no indent
RAW = "raw"

# what one level of nesting costs; `detail` sits at depth 1, which is what
# spells its historical "     ... " prefix
INDENT = "     "


class ReportLog:
    """
    Accumulating report text, spelled in the QuNex runlog vocabulary.

    Holds the growing report as a list of ``(depth, severity, message)``
    records and renders it on demand. This is the piece shared by session-level
    commands and their per-BOLD / per-group executors; :class:`SessionLog`
    extends it with the header and footer.
    """

    def __init__(self):
        self._records = []
        self._depth = 0
        self._errors = 0

    # ------------------------------------------------------------------ text

    @property
    def text(self) -> str:
        """The report rendered so far."""
        return "".join(
            message if severity == RAW
            else "\n" + INDENT * depth + PREFIXES[severity] + message
            for depth, severity, message in self._records
        )

    def __str__(self) -> str:
        return self.text

    @property
    def has_errors(self) -> bool:
        """Whether any error has been recorded on this log."""
        return self._errors > 0

    def capture(self, text: str) -> None:
        """
        Adopt a report string returned by a ``processing.core`` helper.

        Those helpers take the report so far and hand back the report with their
        own output appended, so the returned string replaces the buffer rather
        than extending it.

        Deprecated: this flattens every record recorded so far into one verbatim
        block, losing severity and depth. It disappears once the helpers write
        into the log object instead of round-tripping its text.
        """
        self._records = [(0, RAW, text)]

    def add(self, other) -> None:
        """Append the text of another report log (e.g. an executor's result)."""
        if isinstance(other, ReportLog):
            self._records += other._records
            self._errors += other._errors
        else:
            self.raw(other)

    # ----------------------------------------------------------------- depth

    def indent(self, levels: int = 1) -> None:
        """Nest subsequent lines one (or ``levels``) deeper. Clamped at zero."""
        self._depth = max(0, self._depth + levels)

    def dedent(self, levels: int = 1) -> None:
        """Undo :meth:`indent`. Clamped at zero."""
        self.indent(-levels)

    @contextmanager
    def section(self, title: str, *args):
        """
        Record a step and nest everything logged inside the block under it.

        The depth is restored even if the block raises.
        """
        self.step(title, *args)
        self.indent()
        try:
            yield self
        finally:
            self.dedent()

    # ---------------------------------------------------------------- levels

    def _emit(self, level, message, args, depth=0):
        if args:
            message = message % args
        self._records.append((max(0, self._depth + depth), level, message))

    def step(self, message: str, *args, depth: int = 0) -> None:
        """Record a processing step: ``---> <message>``."""
        self._emit("step", message, args, depth)

    def detail(self, message: str, *args, depth: int = 0) -> None:
        """Record a sub-detail of the preceding step: ``     ... <message>``."""
        self._emit("detail", message, args, depth + 1)

    def warning(self, message: str, *args, depth: int = 0) -> None:
        """Record a warning: ``---> WARNING: <message>``."""
        self._emit("warning", message, args, depth)

    def error(self, message: str, *args, depth: int = 0) -> None:
        """Record an error: ``---> ERROR: <message>``."""
        self._errors += 1
        self._emit("error", message, args, depth)

    def info(self, message: str, *args, depth: int = 0) -> None:
        """Record an unprefixed line."""
        self._emit("info", message, args, depth)

    def blank(self, count: int = 1) -> None:
        """Insert blank lines."""
        self.raw("\n" * count)

    def raw(self, text: str) -> None:
        """Append text verbatim, with no prefix, no indent and no added newline."""
        self._records.append((0, RAW, text))

    @contextmanager
    def framed(self, title: str):
        """Frame a block of output between report rules."""
        self.raw("\n\n%s\n%s\n\n" % (REPORT_RULE, title))
        try:
            yield self
        finally:
            self.raw("\n%s\n" % REPORT_RULE)

    def pipeline_command(self, command: str, marker: str = "--",
                         title: str = "Running HCP Pipelines command via QuNex:"):
        """
        Show the pipeline command QuNex is about to run, one flag per line.

        Parameters:
            command: the assembled command line.
            marker: the flag separator as it appears in ``command``. Commands
                that pad their flags for readability pass that padding along
                with the dashes.
            title: the section title placed above the command.
        """
        body = command.replace(marker, "\n    --")
        if marker == "--":
            # commands assembled with line continuations carry alignment padding
            body = body.replace("             ", "")
        with self.framed(title):
            self.raw(body)

    # ---------------------------------------------------------------- errors

    def command_failed(self, e: ge.CommandFailed, step: str = None) -> None:
        """Record a ``ge.CommandFailed`` raised inside the command."""
        self._errors += 1
        details = "\n     ".join(e.report)
        if step is None:
            self.raw(
                "\n\nERROR in completing %s:\n     %s\n" % (e.function, details)
            )
        else:
            self.raw(
                "\n\nERROR in completing %s at %s:\n     %s\n"
                % (step, e.function, details)
            )

    def unknown_error(self) -> None:
        """Record an unexpected exception, including the current traceback."""
        self._errors += 1
        dots = "." * 35
        self.raw(
            "\nERROR: Unknown error occured: \n%s\n%s%s\n"
            % (dots, traceback.format_exc(), dots)
        )

    # ------------------------------------------------------- external calls

    def run_external(self, checkfile, command, description, **kwargs):
        """
        Run an external command, threading the runlog through it.

        Wraps ``processing.core.run_external_for_file`` so the caller neither
        passes nor reassigns the report text.

        Returns:
            ``(endlog, report, failed)`` from the underlying call.
        """
        import qx_utilities.processing.core as pc

        text, endlog, report, failed = pc.run_external_for_file(
            checkfile, command, description, r=self.text, **kwargs
        )
        self.capture(text)
        return endlog, report, failed

    def check_run(self, checkfile, full_test, description, overwrite=False):
        """
        Report what a run would do, without running it (the ``--test`` path).

        Wraps ``processing.core.check_run`` so the caller neither passes nor
        reassigns the report text.

        Returns:
            ``(passed, report, failed)`` from the underlying call.
        """
        import qx_utilities.processing.core as pc

        passed, report, text, failed = pc.check_run(
            checkfile, full_test, description, self.text, overwrite=overwrite
        )
        self.capture(text)
        return passed, report, failed

    def check_for_file(self, checkfile, ok="", bad="", status=True):
        """
        Note the presence or absence of a file, appending ``ok`` or ``bad``.

        Wraps ``processing.core.check_for_file`` so the caller neither passes nor
        reassigns the report text.

        Returns:
            the running status (True while every checked file has been present).
        """
        import qx_utilities.processing.core as pc

        text, status = pc.check_for_file(self.text, checkfile, ok, bad, status)
        self.capture(text)
        return status

    def check_for_files(self, checkfiles, ok, bad, all=False, status=True):
        """
        Note the presence of one or all of ``checkfiles``.

        Wraps ``processing.core.check_for_files`` so the caller neither passes
        nor reassigns the report text.

        Returns:
            ``(status, found_file)`` from the underlying call.
        """
        import qx_utilities.processing.core as pc

        text, status, found = pc.check_for_files(
            self.text, checkfiles, ok, bad, all, status
        )
        self.capture(text)
        return status, found

    def link_or_copy(self, source, target, status=None, name=None,
                     prefix=None, symlink=False):
        """
        Link or copy a file, appending the mapping outcome to the report.

        Wraps ``general.core.link_or_copy`` so the caller neither passes nor
        reassigns the report text.

        Returns:
            the running status from the underlying call.
        """
        import qx_utilities.general.core as gc

        status, text = gc.link_or_copy(
            source, target, self.text, status, name, prefix, symlink
        )
        self.capture(text)
        return status

    def use_or_skip_bold(self, sinfo, options):
        """
        Resolve which BOLDs to use and which to skip for this session.

        Wraps ``processing.core.use_or_skip_bold`` so the caller neither passes
        nor reassigns the report text.

        Returns:
            ``(bolds, skipped, n_skipped)`` from the underlying call.
        """
        import qx_utilities.processing.core as pc

        bolds, skipped, n_skipped, text = pc.use_or_skip_bold(
            sinfo, options, self.text
        )
        self.capture(text)
        return bolds, skipped, n_skipped


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
        import qx_utilities.processing.core as pc

        super().__init__()
        self._options = options
        self._pipeline = pipeline
        self._sid = sinfo["id"]

        self.raw("\n%s\n%s: %s \n[started on %s]" % (
            REPORT_RULE,
            label,
            self._sid,
            datetime.now().strftime(REPORT_TIME),
        ))

        action = pc.action("Running", options["run"])
        if mode:
            self.raw("%s%s %s [%s] ...%s" % (
                lead, action, pipeline, options["hcp_processing_mode"], tail,
            ))
        else:
            self.raw("%s%s %s ...%s" % (lead, action, pipeline, tail))

    # ---------------------------------------------------------------- finish

    def finish(self, report, failed=None, pipeline=None, lead="\n\n"):
        """
        Close the report and build the value the command returns.

        Every command returns ``(report_text, (session_id, summary, failed))`` --
        a three-field status ``general.process`` unpacks as
        ``(sid, report, failed)``. This method builds exactly that, so a command
        can never return the malformed two-field status that made a whole run
        print "success status not reported".

        The failure count is derived from the log when the caller does not give
        one: a command that recorded an error reports a failure. An explicit
        ``failed=`` (or the count inside a status tuple) always wins, but a
        caller reporting no failures while errors were recorded gets a warning
        line in the report -- the two disagreeing is a bug in the command, not
        something to hide or to raise on mid-run.

        Parameters:
            report: the per-session summary string, or a ready three-field
                ``(session_id, summary, failed)`` status tuple.
            failed: number of failed units; derived from recorded errors when
                omitted, ignored when ``report`` is a tuple.
            pipeline: name for the closing line; defaults to the opening one.
            lead: newlines separating the footer from the preceding text.

        Returns:
            ``(report_text, (session_id, summary, failed))``.
        """
        reported = report[2] if isinstance(report, tuple) and len(report) == 3 else failed
        if reported is None:
            failed = reported = 1 if self.has_errors else 0
        if self.has_errors and not reported:
            self.warning(
                "%d error(s) were recorded but the command reports no failures"
                % self._errors
            )

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
        import qx_utilities.processing.core as pc

        name = pipeline if pipeline is not None else self._pipeline
        self.raw("%s%s %s on %s\n%s" % (
            lead,
            name,
            pc.action("completed", self._options["run"]),
            datetime.now().strftime(REPORT_TIME),
            REPORT_RULE,
        ))

    def result(self, report, failed=None):
        """
        Build the ``(report_text, status)`` value the command returns.

        Enforces the three-field status contract (see :meth:`finish`). Unlike
        :meth:`finish` it does not derive ``failed`` -- a direct caller states
        the count.
        """
        if isinstance(report, tuple):
            if len(report) != 3:
                raise ValueError(
                    "command status must be a 3-field "
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
