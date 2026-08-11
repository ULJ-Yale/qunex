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
  which closes the report and records the summary and failure count.

A processing command returns the log itself. ``general.process`` writes it with
:meth:`ReportLog.write_to` and asks it for :attr:`ReportLog.status` -- the
``(session_id, summary, failed)`` triple, derived on read rather than assembled
by hand at the call site.

The ``processing.core`` / ``general.core`` helpers are imported lazily inside
the wrapper methods so this module stays importable from those packages.

Internally the report is a list of ``(depth, severity, message)`` records
rendered to text on demand, not a list of pre-formatted strings: severity and
nesting stay recoverable after the fact, so the report can be re-rendered (an
errors only digest, a machine readable form) without every call site changing.
Verbatim text -- :meth:`ReportLog.raw`, the framing rules -- is held as a
``RAW`` record and emitted untouched.
"""

import sys
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


def action(word, run):
    """
    Spell an action word for the run mode: "Running" or "Test running".

    Under ``--test`` a command reports what it *would* do, and every line
    saying so is spelled the same way. Use :meth:`ReportLog.action` to record
    such a line; this function is for the places that need the word as a
    **value** -- a command's summary string, or a word reused across lines.

    Parameters:
        word: the action, e.g. ``"Running"`` or ``"completed"``.
        run: ``options["run"]``.
    """
    if run == "test":
        if word.istitle():
            return "Test " + word.lower()
        return "test " + word
    return word


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

        Attributes:
            sid: what the report is filed under -- the session, the subject, or
                (filled in by :meth:`write_to`) the command. A
                :class:`SessionLog` sets it from ``sinfo["id"]``.
            report: the one-line summary of what the command did.
            failed: the number of failures, or None to have it derived from the
                errors recorded here.

        The three are plain attributes so a command can state them where it
        knows them::

            log.step("Subject cannot be processed.")
            log.report = "FS cannot be run"
            log.failed = 1

        rather than assembling a positional tuple at the return. Nothing is
        frozen at assignment: :attr:`status` derives on read.
        """
        self._records = []
        self._depth = 0
        self._errors = 0
        self._comlog = None
        self._echo = echo
        self._external_calls = 0

        self.sid = None
        self.report = None
        self.failed = None
        self._warned_failed = False

    def __getstate__(self):
        """
        The state that crosses a process boundary: everything but the streams.

        A command's log is returned to ``general.process``, which for a
        parallel run means being pickled out of a ``ProcessPoolExecutor``
        worker. ``_echo`` and ``_comlog`` are the only unpicklable things a log
        can hold, and neither has anything left to do once the command returns:
        both are side channels for records *as they happen*.

        They are dropped, never closed. ``_echo`` is ``sys.stdout``, and
        ``_comlog`` is a ``ComContext`` whose ``tmp_`` to ``done_`` rename
        belongs to ``processing.core.close_log``. Dropping them here rather
        than checking for them at ``finish()`` makes a log picklable by
        construction -- including the commands that ``return log`` without
        calling ``finish()`` at all.
        """
        state = self.__dict__.copy()
        state["_echo"] = None
        state["_comlog"] = None
        return state

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
        echoing to a ``sys.stdout`` that ``run_with_log`` has pointed at the
        comlog -- tee'd into it, or redirected into it for a parallel call --
        would otherwise write the line into that comlog twice.
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

    @contextmanager
    def combined_comlog(self, options, command, thread=None):
        """
        One comlog for the whole command, instead of one per external call.

        A command that makes forty external calls used to leave forty comlogs,
        each a fragment of one run and each named after the tool rather than
        after the command. This opens a single comlog named for `command`,
        attaches it for the length of the block, and closes it once by how the
        block ended.

        Attachment is what does the work: :meth:`run_external` hands the
        attached comlog to ``processing.core.run_external_for_file``, which then
        writes into it instead of opening and disposing of its own. Everything
        recorded on this log inside the block goes in too, so the file reads as
        the run rather than as one tool's stdout. The traffic is one way -- the
        report reaches the comlog, and no external output can reach the runlog,
        because :meth:`trace` writes to the comlog and never to
        :attr:`_records`.

        Nothing is opened under ``--test``: a dry run makes no external calls,
        so there is no output to keep and no file to leave behind.

        Retention is decided here rather than at each call site, which is what
        makes ``--log`` reach these commands at all::

            with log.combined_comlog(options, "run_freesurfer_full_segmentation",
                                     thread=sinfo["id"]):
                ...

        Parameters:
            options: the command's options; ``comlogs``, ``logtag``, ``run``
                and ``log`` are read.
            command: the command's name, which names the comlog.
            thread: the parallel thread, or the session being processed.

        Yields:
            this log.
        """
        import qx_utilities.processing.core as pc

        if options["run"] != "run":
            yield self
            return

        comlog, logfolders = pc.open_comlog(
            options["comlogs"], command, options["logtag"], thread, None
        )
        if comlog.path:
            print("You can follow the command's progress in:")
            print(comlog.path)
            print(REPORT_RULE)

        started = self._external_calls
        completed = False
        try:
            with self.stream_to(comlog):
                yield self
            completed = True
        finally:
            # written to the comlog directly: the block has ended, so the
            # attachment is gone, and this line belongs to the file rather than
            # to the report
            comlog.write(
                "\n\n---> %s at %s\n\n"
                % (
                    "Successful completion" if completed else
                    "An external command failed",
                    datetime.now(),
                )
            )
            ran = self._external_calls - started
            self.step("ran %d external command%s%s" % (
                ran,
                "" if ran == 1 else "s",
                "" if completed else " before failing",
            ))
            pc.close_log(
                comlog,
                logfolders,
                "done" if completed else "error",
                options["log"] == "remove",
                self,
            )

    def external_call(self) -> None:
        """
        Count one external command actually run under the combined comlog.

        Counted where the call is made rather than where it is asked for: a
        call whose check file is already there returns without running
        anything, and a summary line saying otherwise would be a lie.
        """
        self._external_calls += 1

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

    def action(self, word: str, message: str, run: str, *, level: str = "step") -> None:
        """
        Record what the command is doing, or -- under ``--test`` -- would do.

        ``log.action("Running", "FSL feat ...", options["run"])`` records
        ``---> Running FSL feat ...``, or ``---> Test running FSL feat ...``
        when ``run`` is ``"test"``. The action word is a logging operation
        rather than a string spliced into the message.

        Parameters:
            word: the action, e.g. ``"Running"`` or ``"Processing"``.
            message: what is being acted on.
            run: ``options["run"]``.
            level: the level method to record at.
        """
        getattr(self, level)("%s %s" % (action(word, run), message))

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

        An attached comlog is handed on as the one to write into, so a call
        inside a :meth:`combined_comlog` block joins that file instead of
        opening its own -- and `thread`, `remove`, `task`, `logfolder` and
        `logtags`, which only describe a comlog being opened, are then inert.

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
            comlog=self._comlog,
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

    # ---------------------------------------------------------------- finish

    def _derive_failed(self, report, failed):
        """
        The failure count to report, derived from the log when not given.

        A command that recorded an error reports a failure. An explicit
        ``failed=`` (or the count inside a status tuple) always wins, but a
        caller reporting no failures while errors were recorded gets a warning
        line in the report -- the two disagreeing is a bug in the command, not
        something to hide or to raise on mid-run.

        Reached from :attr:`status` as well as from :meth:`finish`, so the
        warning is recorded at most once however often the status is read.
        """
        reported = report[2] if isinstance(report, tuple) and len(report) == 3 else failed
        if reported is None:
            failed = reported = 1 if self.has_errors else 0
        if self.has_errors and not reported and not self._warned_failed:
            self._warned_failed = True
            self.warning(
                "%d error(s) were recorded but the command reports no failures"
                % self._errors
            )
        return failed

    @property
    def status(self):
        """
        The ``(session_id, summary, failed)`` triple ``general.process`` files.

        Derived on read rather than stored: whatever a command assigned to
        :attr:`failed` wins, an unset count comes from the errors recorded
        here, and a command claiming no failures while errors were recorded
        still gets its warning line. There is no tuple to build, so there is no
        wrong order to build it in and no two-field status to reject.
        """
        return (self.sid, self.report, self._derive_failed(self.report, self.failed))

    def write_to(self, run):
        """
        Append this report to the run's runlog and show it.

        What ``general.process.writelog`` and the ``print(r)`` beside it used
        to do, in the one place that knows the report is complete. The runlog
        is written first: it is the durable record, and a broken console must
        not cost it.

        A log with no id of its own -- a study level command's plain
        :class:`ReportLog` -- is filed under the run's command name, which is
        what the final report then lists it as. The command does not have to
        repeat its own name to say so.
        """
        if self.sid is None:
            self.sid = run.command

        text = self.text
        run.write(text + "\n")
        print(text)

    def finish(self, summary, failed=None, name=None):
        """
        Close the report and record what the command is reporting.

        The status contract processing commands already use, for a log that has
        no session of its own: ``general.core.run_with_log`` calls this on the
        log it gave a utility command, writes the report text into the runlog
        and hands the count on. :class:`SessionLog` overrides it to append its
        footer first.

        The count is derived here as well as on :attr:`status`, so a derived
        warning reads inside the report -- before a session log's closing rule
        -- rather than after it.

        Parameters:
            summary: the one-line summary, or a ready three-field
                ``(name, summary, failed)`` status tuple.
            failed: number of failures; derived from recorded errors when
                omitted, ignored when ``summary`` is a tuple.
            name: what the report is filed under -- the command, or
                ``command: session``.

        Returns:
            ``self``, which is what a processing command returns.
        """
        return self.result(summary, self._derive_failed(summary, failed), name)

    def result(self, report, failed=None, name=None):
        """
        Record the summary and failure count, and hand the log back.

        Enforces the three-field status contract (see :meth:`finish`). Unlike
        :meth:`finish` it does not derive ``failed`` -- a direct caller states
        the count.

        Returns:
            ``self``, which is what a processing command returns.
        """
        if isinstance(report, tuple):
            if len(report) != 3:
                raise ValueError(
                    "command status must be a 3-field "
                    "(session_id, summary, failed) tuple, got %d fields: %r"
                    % (len(report), report)
                )
            self.sid, self.report, self.failed = report
        else:
            if failed is None:
                raise ValueError(
                    "finish() needs a failed count when report is a "
                    "summary string (got failed=None for %r)" % (report,)
                )
            if name is not None:
                self.sid = name
            self.report = report
            self.failed = failed

        return self


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
        super().__init__()
        self._options = options
        self._pipeline = pipeline
        self.sid = sinfo["id"]

        self.raw("\n%s\n%s: %s \n[started on %s]" % (
            REPORT_RULE,
            label,
            self.sid,
            datetime.now().strftime(REPORT_TIME),
        ))

        running = action("Running", options["run"])
        if mode:
            self.raw("%s%s %s [%s] ...%s" % (
                lead, running, pipeline, options["hcp_processing_mode"], tail,
            ))
        else:
            self.raw("%s%s %s ...%s" % (lead, running, pipeline, tail))

    # ---------------------------------------------------------------- finish

    def finish(self, report, failed=None, pipeline=None, lead="\n\n"):
        """
        Close the report and record what the command is reporting.

        Every command returns its log, and ``general.process`` reads
        :attr:`ReportLog.status` off it as ``(sid, report, failed)``. This
        method records exactly that, so a command can never report the
        malformed two-field status that made a whole run print "success status
        not reported".

        The failure count is derived from the log when the caller does not give
        one, exactly as :meth:`ReportLog.finish` derives it; the footer goes in
        after the derivation, so a derived warning still reads inside the
        report rather than after its closing rule.

        Parameters:
            report: the per-session summary string, or a ready three-field
                ``(session_id, summary, failed)`` status tuple.
            failed: number of failed units; derived from recorded errors when
                omitted, ignored when ``report`` is a tuple.
            pipeline: name for the closing line; defaults to the opening one.
            lead: newlines separating the footer from the preceding text.

        Returns:
            ``self``, which is what the command returns.
        """
        failed = self._derive_failed(report, failed)
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
        self.raw("%s%s %s on %s\n%s" % (
            lead,
            name,
            action("completed", self._options["run"]),
            datetime.now().strftime(REPORT_TIME),
            REPORT_RULE,
        ))

    def result(self, report, failed=None, name=None):
        """
        Record the summary and failure count, and hand the log back.

        As :meth:`ReportLog.result`, with the session id as the name -- a
        session log knows what it is reporting on and callers do not pass it.
        """
        return super().result(report, failed, name or self.sid)


def log_or_console(_log):
    """
    The log to report into: the caller's, or one that echoes to the console.

    For a function that reports but is called from both a place that holds a
    log and a place that does not -- a helper shared by the pipelines and by
    tests or scripts, a utility command reached directly rather than through
    ``qunex``. It keeps the body reading as ``log.step(...)``, where guarding
    every call would put ``if log is not None`` between each line and its
    meaning.

    **The stand-in echoes to ``sys.stdout``**, which is what a caller with no
    log had before there was one to give: the line appears as it happens, and
    under :func:`general.core.run_with_log` -- which points ``sys.stdout`` at
    the comlog for the length of the call -- it reaches that file too. For one
    call that is a tee and the line is live on the terminal as well; for a call
    submitted by :func:`general.core.run_in_parallel` it is a redirect and the
    comlog is the only live view, since N calls' lines on one terminal are
    unreadable. ``sys.stdout`` is read here rather than at import, so whichever
    is in place at call time is the one written to.

    This is the one place the console decision is made, for both branches:
    ``run_with_log`` builds the log it hands a registered command through here
    too, so a switch for the terminal is one line in this function rather than
    one per command. It is no longer what stops a registered command being
    silent -- ``run_with_log`` supplies an echoing log -- but the fallback for
    the paths it never reaches: logging off, ``run_recipe`` without sessions,
    and a call from another python function.

    :func:`processing.core._say` is the other shape of the same problem and is
    the better one when there are only a few messages: it takes the level as an
    argument, so the guard lives in one place rather than in a stand-in object.
    Reach for this when the guard would otherwise be repeated, and for the
    nesting -- ``with log.section(...)`` has no ``_say`` equivalent.

    Parameters:
        _log (ReportLog | None): the caller's log, or None. Spelled with the
            underscore because that is the one name a log parameter has in this
            tree -- see the note on `link_or_copy`.

    Returns:
        ReportLog: `_log` when there is one, an echoing stand-in otherwise.
    """
    return _log if _log is not None else ReportLog(echo=sys.stdout)
