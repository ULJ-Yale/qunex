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
the console. The inner layer, the **comlog**, holds one external pipeline
call's raw stdout/stderr and is written by ``processing.core``; while one is
attached (:meth:`ReportLog.stream_to`) it also receives everything recorded
here, so it reads as a complete record of that call.

Commands used to build the runlog by appending to a local string named ``r``
and passing it into (and back out of) every helper. The classes here hold that
text instead, so code states *what happened* and this module decides how it is
spelled:

- :class:`ReportLog` is a plain accumulator with the level vocabulary
  (``step``/``detail``/``warning``/``error``) and wrappers around the
  ``processing.core`` / ``general.core`` helpers, which are handed the log and
  write into it. Per-BOLD / per-group executors use it: they have report text
  but no session header of their own.
- :class:`SessionLog` adds the per-session header and :meth:`SessionLog.finish`,
  which closes the report and builds the ``(text, status)`` value a command
  returns to ``general.process``.

The ``processing.core`` / ``general.core`` helpers are imported lazily inside
the wrapper methods so this module stays importable from those packages.

Internally the report is a list of ``(depth, severity, message)`` records
rendered to text on demand, not a list of pre-formatted strings: severity and
nesting stay recoverable after the fact, so the report can be re-rendered (an
errors only digest, a machine readable form) without every call site changing.
Verbatim text -- :meth:`ReportLog.raw`, the framing rules -- is held as a
``RAW`` record and emitted untouched.
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


def _render(depth, severity, message):
    """Spell one record the way the runlog reads it."""
    if severity == RAW:
        return message
    return "\n" + INDENT * depth + PREFIXES[severity] + message


class ReportLog:
    """
    Accumulating report text, spelled in the QuNex runlog vocabulary.

    Holds the growing report as a list of ``(depth, severity, message)``
    records and renders it on demand. This is the piece shared by session-level
    commands and their per-BOLD / per-group executors; :class:`SessionLog`
    extends it with the header and footer.
    """

    def __init__(self, echo=None):
        """
        Parameters:
            echo: an open stream (usually ``sys.stdout``) each recorded line is
                written to as it is recorded, so a command shows its progress
                live instead of only when its report is rendered. Off by
                default: a ``SessionLog`` must not echo, since
                ``general.process`` prints its report when the session ends.
        """
        self._records = []
        self._depth = 0
        self._errors = 0
        self._comlog = None
        self._echo = echo

    # ------------------------------------------------------------------ text

    @property
    def text(self) -> str:
        """The report rendered so far."""
        return "".join(_render(*record) for record in self._records)

    def __str__(self) -> str:
        return self.text

    def _record(self, depth, severity, message) -> None:
        """
        Keep one record, and show it as it happens.

        The line goes to the attached comlog, or -- when there is none -- to
        the echo stream. The two are alternatives rather than both: a log
        echoing to a ``sys.stdout`` that ``run_with_log`` has tee'd into the
        comlog would otherwise write the line into that comlog twice.
        """
        rendered = _render(depth, severity, message)
        self._records.append((depth, severity, message))
        self.trace(rendered)
        if self._comlog is None and self._echo is not None:
            self._echo.write(rendered)
            self._echo.flush()

    # --------------------------------------------------------- the comlog

    def trace(self, text) -> None:
        """
        Write `text` verbatim to the attached comlog and nowhere else.

        The comlog's counterpart to :meth:`raw`: text that belongs in the raw
        record of one external call but not in the run's report. Dropped when
        no comlog is attached -- including when comlogs are switched off.
        """
        if self._comlog is not None:
            self._comlog.write(text)

    @contextmanager
    def stream_to(self, comlog):
        """
        Attach `comlog` for the duration of the block.

        :meth:`trace` goes to it, and everything recorded inside is echoed
        into it as it is recorded, so the comlog reads as a complete record of
        the call rather than only the tool's raw output. A ``ReportLog``
        outlives any single comlog -- one report spans one comlog per external
        call -- so the attachment is scoped rather than owned: outside a block
        :meth:`trace` drops and every other method behaves as it always has.

        Any outer attachment is restored on the way out, however the block
        exits, so nesting and exceptions are safe.
        """
        outer = self._comlog
        self._comlog = comlog
        try:
            yield self
        finally:
            self._comlog = outer

    @property
    def has_errors(self) -> bool:
        """Whether any error has been recorded on this log."""
        return self._errors > 0

    # ----------------------------------------------------------------- depth

    def indent(self, levels: int = 1) -> None:
        """Nest subsequent lines one (or ``levels``) deeper. Clamped at zero."""
        self._depth = max(0, self._depth + levels)

    def dedent(self, levels: int = 1) -> None:
        """Undo :meth:`indent`. Clamped at zero."""
        self.indent(-levels)

    @contextmanager
    def section(self, title: str):
        """
        Record a step and nest everything logged inside the block under it.

        The depth is restored even if the block raises.
        """
        self.step(title)
        self.indent()
        try:
            yield self
        finally:
            self.dedent()

    # ---------------------------------------------------------------- levels

    def _emit(self, level, message, depth=0):
        self._record(max(0, self._depth + depth), level, message)

    def step(self, message: str, *, depth: int = 0) -> None:
        """Record a processing step: ``---> <message>``."""
        self._emit("step", message, depth)

    def detail(self, message: str, *, depth: int = 0) -> None:
        """Record a sub-detail of the preceding step: ``     ... <message>``."""
        self._emit("detail", message, depth + 1)

    def warning(self, message: str, *, depth: int = 0) -> None:
        """Record a warning: ``---> WARNING: <message>``."""
        self._emit("warning", message, depth)

    def error(self, message: str, *, depth: int = 0) -> None:
        """Record an error: ``---> ERROR: <message>``."""
        self._errors += 1
        self._emit("error", message, depth)

    def info(self, message: str, *, depth: int = 0) -> None:
        """Record an unprefixed line."""
        self._emit("info", message, depth)

    def blank(self, count: int = 1) -> None:
        """Insert blank lines."""
        self.raw("\n" * count)

    def raw(self, text: str) -> None:
        """Append text verbatim, with no prefix, no indent and no added newline."""
        self._record(0, RAW, text)

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

    def run_external(self, checkfile, command, description, overwrite=False,
                     thread="0", remove=True, task=None, logfolder="",
                     logtags="", full_test=None, shell=True, verbose=True):
        """
        Run an external command, letting it write into this log.

        Calls ``processing.core.run_external_for_file`` with this log; see it
        for what the parameters mean. The signature is spelled out rather than
        forwarded as ``**kwargs`` so a mistyped argument is a ``TypeError``
        here, at the call site, and not somewhere inside the helper.

        Returns:
            ``(endlog, status, failed)`` from the underlying call.
        """
        import qx_utilities.processing.core as pc

        return pc.run_external_for_file(
            checkfile,
            command,
            description,
            self,
            overwrite=overwrite,
            thread=thread,
            remove=remove,
            task=task,
            logfolder=logfolder,
            logtags=logtags,
            full_test=full_test,
            shell=shell,
            verbose=verbose,
        )

    def check_run(self, checkfile, full_test, description, overwrite=False):
        """
        Report what a run would do, without running it (the ``--test`` path).

        Returns:
            ``(passed, report, failed)`` from ``processing.core.check_run``.
        """
        import qx_utilities.processing.core as pc

        return pc.check_run(
            checkfile, full_test, description, self, overwrite=overwrite
        )

    def check_for_file(
        self,
        checkfile,
        ok="",
        bad="",
        status=True,
        ok_level="detail",
        bad_level="detail",
    ):
        """
        Note the presence or absence of a file, recording ``ok`` or ``bad``.

        Returns:
            the running status (True while every checked file has been present).
        """
        import qx_utilities.processing.core as pc

        return pc.check_for_file(
            self, checkfile, ok, bad, status, ok_level, bad_level
        )

    def check_for_files(
        self,
        checkfiles,
        ok,
        bad,
        all=False,
        status=True,
        ok_level="detail",
        bad_level="detail",
    ):
        """
        Note the presence of one or all of ``checkfiles``.

        Returns:
            ``(status, found_file)`` from the underlying call.
        """
        import qx_utilities.processing.core as pc

        return pc.check_for_files(
            self, checkfiles, ok, bad, all, status, ok_level, bad_level
        )

    def link_or_copy(self, source, target, status=None, name=None, symlink=False):
        """
        Link or copy a file, recording the mapping outcome in the report.

        Returns:
            the running status from ``general.core.link_or_copy``.
        """
        import qx_utilities.general.core as gc

        return gc.link_or_copy(source, target, self, status, name, symlink)

    def use_or_skip_bold(self, sinfo, options):
        """
        Resolve which BOLDs to use and which to skip for this session.

        Returns:
            ``(bolds, skipped, n_skipped)`` from the underlying call.
        """
        import qx_utilities.processing.core as pc

        return pc.use_or_skip_bold(sinfo, options, self)


class SessionLog(ReportLog):
    """
    Runlog for one session (or subject) processed by one command.

    The rendered text is what the command returns to ``general.process``, so the
    output format is deliberately the one QuNex users already read.

    Typical use::

        log = SessionLog(sinfo, options, "HCP DTI Fit pipeline")
        log.step("checking for data")
        log.error("bvals file not found: %s" % path)
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
