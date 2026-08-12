#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``general.log.context``

Where a run's logs live, and who owns the files.

QuNex writes two kinds of log file:

- one **runlog** per invocation -- ``Log-<command>-<timestamp>.log`` in the log
  folder -- holding the call that was made and the report each session
  produced. :class:`RunContext` owns it: it is created once, before any
  dispatch, and shared by every worker the run spawns.
- one **comlog** per external call -- ``<tags>_<timestamp>.log`` in
  ``<logfolder>/comlogs`` -- holding that call's raw output.
  :class:`ComContext` owns one of those. It opens as ``tmp_…`` and is renamed
  to ``done_…``, ``error_…`` or ``incomplete_…`` on close, so an interrupted
  run is visible in the file listing.

Both no-op when the resolved :class:`~qx_utilities.general.log.LogSettings`
turn them off, so callers never have to ask whether logging is on.

There is a third file, written only when it is asked for: the **status
record**. A parent process that runs QuNex as a subprocess -- ``run_recipe``
-- passes ``--logstatus=<path>``, and :meth:`RunContext.write_status` puts the
run's report there as data. It is how a report crosses a process boundary
without anyone grepping stdout.

Note the import direction: nothing here may import ``general.core`` or
``processing.core`` at all -- both are consumers of this package. What this
module needs from them it is given: :func:`comlog_folder` takes the log folder
rather than deducing it, and the banner it heads a comlog with is the log
package's own :func:`~general.log.report.print_qunex_header`.
"""

import contextlib
import multiprocessing
import os
import os.path
import re
import subprocess
import sys
from datetime import datetime

import yaml

from qx_utilities.general.log.report import print_qunex_header

# the timestamp both file names and headers are stamped with
TIMESTAMP = "%Y-%m-%d_%H.%M.%S.%f"

# comlog name parts are joined with this, and the joined stem is capped: a long
# command plus a long session id must not produce a name the file system
# rejects
NAME_SEP = "_"
MAX_STEM = 150

# the status prefixes a comlog name may carry
STATUS_PREFIX = re.compile("^(tmp_|done_|error_|incomplete_)")

# the runlog is appended to from parallel workers, which are forked from the
# process that builds the RunContext -- so the lock is inherited rather than
# pickled, the same arrangement `general.core` uses for its progress prints
_lock = multiprocessing.Lock()

# frames the call echo at the top of a runlog
RULE = "================================================================="

# whether this process has already written its status record. A run writes one
# -- the digest it built, or, when it died before building one, the failure
# `write_failure_status` records at the exit boundary. The flag is what keeps
# the second from overwriting the first: `process.run` writes its per-session
# digest and *then* raises for the sessions that failed, and the digest is the
# better record of the two. A file check cannot tell this run's record from one
# an earlier run left at the same path, which is why this is a flag and not an
# `os.path.exists`.
_status_written = False


def digest(stati):
    """
    Split the collected statuses into what gets reported and the failure count.

    Triples whose id is ``Unknown`` -- the commands that do not report a status
    yet -- have nothing to say, so they are left out.

    Parameters:
        stati: the ``(session_id, report, failed)`` triples of a run.

    Returns:
        the ``(reported, failed)`` pair, where `failed` is the total number of
        failures, or None when any reported session did not say.
    """
    reported = [
        (sid, report, failed) for sid, report, failed in stati if "Unknown" not in sid
    ]

    if any(failed is None for _, _, failed in reported):
        return reported, None

    return reported, sum(failed for _, _, failed in reported)


def comlog_name(*parts):
    """
    Build a comlog file name out of its parts.

    Parts that are empty or None are dropped, the rest are joined with an
    underscore and capped at :data:`MAX_STEM` characters.

    Returns:
        the file name, without any status prefix and with the ``.log``
        extension.
    """
    stem = NAME_SEP.join(str(part) for part in parts if part)
    if len(stem) > MAX_STEM:
        stem = stem[:MAX_STEM] + "(...)"
    return stem + ".log"


def call_echo(command, args, session=None):
    """
    Spell the call that was made, the way it would be typed.

    Parameters:
        command: the command name.
        args: the arguments it was called with.
        session: the session it was called for, when it was called per session.

    Returns:
        the ``qunex <command> \\`` echo, one argument per line.
    """
    lines = ["session: %s" % session] if session else []
    items = [(k, v) for k, v in (args or {}).items()]
    lines.append("qunex %s%s" % (command, " \\" if items else ""))
    for i, (k, v) in enumerate(items):
        lines.append('  --%s="%s"%s' % (k, v, " \\" if i < len(items) - 1 else ""))
    return "\n".join(lines)


def log_folder(command, args, settings, folders, timestamp):
    """
    Decide where this run's logs go.

    An explicit ``--logfolder`` wins. Inside a study the logs go to
    ``<study>/logs/<timestamp>_<command>``, or to ``<study>/processing/logs``
    under the ``legacy`` layout. Outside a study the ``outside_study`` setting
    decides: ``home`` (the default, ``~/qunex_logs``), ``cwd``, or a path.

    Parameters:
        command: the command name.
        args: the parsed arguments; ``logfolder`` is read from them.
        settings: the resolved :class:`LogSettings`.
        folders: the folders deduced by ``general.core.deduce_folders``;
            ``basefolder`` is read from them.
        timestamp: the run's timestamp.

    Returns:
        the absolute path of the log folder.
    """
    explicit = (args or {}).get("logfolder")
    if explicit and explicit != "legacy":
        return os.path.abspath(explicit)

    basefolder = (folders or {}).get("basefolder")

    if explicit == "legacy" or settings.layout == "legacy":
        if basefolder:
            return os.path.join(basefolder, "processing", "logs")
        return os.path.abspath(".")

    runfolder = "%s_%s" % (timestamp, command)

    if basefolder:
        return os.path.join(basefolder, "logs", runfolder)

    if settings.outside_study == "cwd":
        root = os.path.abspath(".")
    elif settings.outside_study == "home":
        root = os.path.join(os.path.expanduser("~"), "qunex_logs")
    else:
        root = os.path.abspath(os.path.expanduser(settings.outside_study))

    return os.path.join(root, runfolder)


def comlog_folder(logfolder):
    """
    Where the comlogs go, under a run's log folder.

    For callers that open a comlog without holding a :class:`RunContext`. The
    caller resolves the log folder -- with ``general.core.deduce_folders``
    when all it has is a sessions folder -- because deducing a study's layout
    is not this package's business.

    Parameters:
        logfolder: the run's log folder.

    Returns:
        the path of the comlogs folder.
    """
    return os.path.join(logfolder, "comlogs")


class _Tee:
    """Writes to the console and to a log file at the same time."""

    def __init__(self, terminal, logfile):
        self.terminal = terminal
        self.log = logfile

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()


class ComContext:
    """
    One comlog: the raw output of a single call, and its status.

    The file is opened as ``tmp_<name>`` and renamed to ``done_``, ``error_``
    or ``incomplete_`` on close, so a run interrupted halfway leaves the
    evidence of it in the file name. Used as a context manager the rename
    follows the exception state::

        with run.comlog("hcp_fmri_volume", session_id) as comlog:
            subprocess.run(call, stdout=comlog.file, stderr=comlog.file)

    A disabled comlog is the same object with :attr:`file` and :attr:`path`
    left at None and every write dropped, so callers never branch on whether
    logging is on.

    Attributes:
        path: the file's current path -- ``tmp_…`` while open, the final path
            after :meth:`close`, and None when the comlog is disabled.
        file: the open file handle, suitable as ``stdout=``/``stderr=`` for
            ``subprocess``; None when disabled or not yet opened.
    """

    def __init__(
        self, folder, *tags, thread=None, name=None, timestamp=None, enabled=True
    ):
        """
        Parameters:
            folder: the comlogs folder to write into.
            tags: the name parts, in order (command, session, ...).
            thread: the parallel thread number, when there is one.
            name: a complete name stem, used instead of `tags`.
            timestamp: the stamp appended to the name; defaults to now.
            enabled: when False nothing is opened and nothing is written.
        """
        parts = [name] if name else list(tags)
        parts.append(thread)
        parts.append(timestamp or datetime.now().strftime(TIMESTAMP))

        self.folder = folder
        self.name = comlog_name(*parts)
        self.enabled = bool(enabled and folder)
        self.path = None
        self.file = None
        self._closed = False

    def open(self):
        """Create the ``tmp_`` file and open it. A second call is a no-op."""
        if not self.enabled or self.file or self._closed:
            return self

        os.makedirs(self.folder, exist_ok=True)
        self.path = os.path.join(self.folder, "tmp_" + self.name)
        # line-buffered: for a call whose output does not reach the terminal
        # (`capture_stdout(tee=False)`) this file is the only live view of it,
        # so `tail -f` has to see lines as they are written rather than a block
        # at a time
        self.file = open(self.path, "w", buffering=1)
        return self

    def write(self, text):
        """Append `text` to the comlog; a no-op when it is disabled."""
        if self.file:
            self.file.write(text)
            self.file.flush()

    @contextlib.contextmanager
    def capture_stdout(self, tee=True):
        """
        Send everything printed inside the block into the comlog.

        The commands this wraps report by printing, so their output has to be
        intercepted rather than handed over. Both streams are restored when the
        block exits, however it exits.

        Parameters:
            tee: when True the output goes to the console *and* the comlog;
                when False it goes to the comlog only. Several calls running
                at once interleave unreadably on one terminal, so a parallel
                run redirects instead of teeing and the comlog -- opened
                line-buffered -- is the live view.

        Yields:
            this comlog.
        """
        if not self.file:
            yield self
            return

        target = _Tee(sys.stdout, self.file) if tee else self.file
        with contextlib.redirect_stdout(target), contextlib.redirect_stderr(target):
            yield self

    def tee(self, command, shell=True):
        """
        Run `command`, writing its output to the console and the comlog at once.

        A subprocess writes to the inherited descriptor, which
        :meth:`capture_stdout` cannot see, and handing it :attr:`file` directly
        would leave the user watching nothing. So the output is read line by
        line and written to both.

        Parameters:
            command: the command to run, as a string or an argument list.
            shell: whether to run it through a shell.

        Returns:
            the command's exit code.
        """
        process = subprocess.Popen(
            command,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            self.write(line)

        process.stdout.close()
        return process.wait()

    def close(self, status="done", remove=False):
        """
        Close the comlog and rename it to reflect how the call ended.

        Parameters:
            status: ``done``, ``error`` or ``incomplete``.
            remove: delete the file instead of renaming it.

        Returns:
            the final path, or None when the comlog was disabled or removed.
        """
        if self.file:
            self.file.close()
            self.file = None

        if self._closed or self.path is None:
            return self.path

        self._closed = True

        if remove:
            os.remove(self.path)
            self.path = None
            return None

        folder, name = os.path.split(self.path)
        self.path = os.path.join(folder, status + "_" + STATUS_PREFIX.sub("", name))
        os.rename(os.path.join(folder, name), self.path)
        return self.path

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc, tb):
        self.close(status="done" if exc_type is None else "error")
        return False


def run_and_log(command, name, run=None, shell=True):
    """
    Run an external command, keeping its output and recording its outcome.

    The output goes to the console and to a comlog of this run, which is
    renamed ``done_`` or ``error_`` by the exit status; the runlog gets the
    one-line record. This is the matlab and bash equivalent of what
    ``general.core.run_with_log`` does for a python command.

    Parameters:
        command: the command to run, as a string or an argument list.
        name: what to call it in the logs.
        run: the :class:`RunContext` that owns this run's logs, when there is
            one; without it the command runs with no comlog and no record.
        shell: whether to run it through a shell.

    Returns:
        the command's exit code.
    """
    comlog = (run.comlog(name) if run else ComContext(None, name)).open()
    code = comlog.tee(command, shell=shell)
    path = comlog.close(status="error" if code else "done")

    if run:
        status = (
            "ERROR running %s" % name
            if code
            else "---> Successful completion of task at %s" % (datetime.now())
        )
        run.write("\n%s%s\n%s\n" % (name, " [log: %s]" % path if path else "", status))

    return code


class RunContext:
    """
    One QuNex invocation's logging: the runlog it writes and the comlogs it
    opens.

    Created once, before the command is dispatched, and passed down --
    including into parallel workers, which is why it holds no open file handle:
    the runlog is appended to under a lock and closed again on every write.

    When logging is disabled, or the runlog is switched off, :attr:`path` is
    None and every write is dropped.

    Attributes:
        logfolder: where this run's logs go.
        comlogfolder: the ``comlogs`` subfolder of it.
        path: the runlog, or None when no runlog is written.
    """

    def __init__(self, command, args, settings, folders, timestamp=None, tag=None):
        """
        Parameters:
            command: the command name as invoked.
            args: the arguments it was called with, for the call echo.
            settings: the resolved :class:`LogSettings`.
            folders: the folders deduced by ``general.core.deduce_folders``.
            timestamp: the run's timestamp; defaults to now.
            tag: an extra marker for the runlog file name, e.g. ``long``.
        """
        self.command = command
        self.args = dict(args or {})
        self.settings = settings
        self.timestamp = timestamp or datetime.now().strftime(TIMESTAMP)

        self.logfolder = log_folder(
            command, self.args, settings, folders, self.timestamp
        )
        self.comlogfolder = os.path.join(self.logfolder, "comlogs")

        self.path = None
        if settings.enabled and settings.runlog:
            self.path = os.path.join(
                self.logfolder,
                "Log-%s%s-%s.log"
                % (command, "-" + tag if tag else "", self.timestamp),
            )

    def write(self, text):
        """Append `text` to the runlog; a no-op when there is no runlog."""
        if not self.path:
            return

        os.makedirs(self.logfolder, exist_ok=True)
        with _lock:
            with open(self.path, "a") as runlog:
                runlog.write(text)

    def header(self, session=None):
        """
        Write the runlog header -- provenance and the call that was made.

        Written first, before any report, so a run killed halfway still says
        what it was.

        Parameters:
            session: the session, when the call was made per session.

        Returns:
            the header text, so the caller can print it as well.
        """
        text = "%s\n#\n%s\n%s\n%s" % (
            print_qunex_header(timestamp=self.timestamp),
            RULE,
            call_echo(self.command, self.args, session),
            RULE,
        )
        self.write(text + "\n")
        return text

    def comlog(self, *tags, thread=None, name=None, timestamp=None):
        """
        Open a comlog for one call of this run.

        Parameters:
            tags: the name parts, in order (command, session, ...).
            thread: the parallel thread number, when there is one.
            name: a complete name stem, used instead of `tags`.
            timestamp: the stamp appended to the name; defaults to now.

        Returns:
            a :class:`ComContext`, disabled when comlogs are switched off.
        """
        return ComContext(
            self.comlogfolder,
            *tags,
            thread=thread,
            name=name,
            timestamp=timestamp,
            enabled=self.settings.enabled and self.settings.comlog,
        )

    def final_report(self, stati):
        """
        Print and record the run's closing digest.

        Parameters:
            stati: the ``(session_id, report, failed)`` triples collected from
                the sessions that ran. Triples whose id is "Unknown" -- the
                commands that do not report a status yet -- are left out of the
                digest but still make the overall status unknown.

        Returns:
            the report text.
        """
        reported, failed_total = digest(stati)

        # the manifest: the counts first, then the calls grouped by how they
        # ended, each entry keeping the `[log: …]` its summary carries. A run
        # of a hundred sessions is read from the top, and the question asked of
        # it is "what failed and where do I look".
        groups = [
            ("Successful", [s for s in reported if s[2] == 0]),
            ("Failed", [s for s in reported if s[2]]),
            ("Did not complete", [s for s in reported if s[2] is None]),
        ]

        lines = ["\n\n---> Final report for command %s" % self.command]
        lines.append(
            "     %d run, %d successful, %d failed, %d did not complete"
            % (len(reported), *(len(group) for _, group in groups))
        )
        for title, group in groups:
            if not group:
                continue
            lines.append("     %s:" % title)
            for sid, report, _ in group:
                lines.append("     ... %s ---> %s" % (sid, report))

        if failed_total is None:
            lines.append("---> Success status not reported for some or all tasks")
        elif failed_total > 0:
            lines.append("---> Not all tasks completed fully!")
        else:
            lines.append(
                "---> Successful completion of all tasks at %s" % (datetime.now())
            )

        text = "\n".join(lines)
        print(text)
        self.write(text + "\n")
        return text

    def write_status(self, stati):
        """
        Write the run's status record, when the caller asked for one.

        ``--logstatus=<path>`` is how a parent process -- ``run_recipe``
        today, a batch driver or CI tomorrow -- asks this run to say what it
        did somewhere the parent can read it. The record carries the same
        ``finish()`` triples :meth:`final_report` renders, so the contract
        that holds inside the process is the one that crosses out of it, and
        the parent has no reason to parse stdout.

        Parameters:
            stati: the ``(session_id, report, failed)`` triples of this run.

        Returns:
            the path written, or None when no status path was asked for.
        """
        path = self.args.get("logstatus")
        if not path:
            return None

        reported, failed_total = digest(stati)

        record = {
            "command": self.command,
            "timestamp": self.timestamp,
            "runlog": self.path,
            "failed": failed_total,
            "sessions": [
                {"id": sid, "summary": report, "failed": failed}
                for sid, report, failed in reported
            ],
        }

        return _write_record(path, record)


def _write_record(path, record):
    """Write `record` to `path`, and note that this run has written one."""
    global _status_written

    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w") as status:
        yaml.safe_dump(record, status, sort_keys=False, default_flow_style=False)

    _status_written = True
    return path


def write_failure_status(args, command, error, failed=1, timestamp=None):
    """
    Write the status record for a run that ended before it could build one.

    A run reports what it did through :meth:`RunContext.write_status`, from
    the digest it collected. A run that dies first -- a command that raises
    before its loop, a worker that never comes back, a command name that is
    not one -- collects nothing, and used to leave the parent that asked for a
    record with nothing to read. That parent is ``run_recipe``, and what it
    reported for such a step was "no status reported", however loudly the step
    had failed.

    So this is the same record, from what is known at the exit boundary rather
    than from a digest: the run has no session level detail to give, and the
    one thing it does have -- that it failed, and with what -- is the thing
    worth having. There is no :class:`RunContext` here on purpose: the boundary
    is reached from paths that never built one, and the only thing needed is
    the path the parent named, which is in the arguments it passed.

    A run that already wrote its record keeps it: see :data:`_status_written`.

    Parameters:
        args: the arguments the run was called with, holding ``logstatus``.
        command: the command as invoked.
        error: what went wrong, spelled into the summary.
        failed: the failure count; 0 for an outcome that is not a failure.
        timestamp: the run's stamp; defaults to now.

    Returns:
        the path written, or None when no record was asked for or one was
        already written.
    """
    path = (args or {}).get("logstatus")
    if not path or _status_written:
        return None

    return _write_record(
        path,
        {
            "command": command,
            "timestamp": timestamp or datetime.now().strftime(TIMESTAMP),
            "runlog": None,
            "failed": failed,
            "sessions": [{"id": command, "summary": str(error), "failed": failed}],
        },
    )


def read_status(path):
    """
    Read a status record written by :meth:`RunContext.write_status`.

    Parameters:
        path: the file the record was asked for at.

    Returns:
        the record as a dict, or None when the run wrote none -- a command
        that reports no status, or one that died before it could.
    """
    try:
        with open(path) as status:
            return yaml.safe_load(status)
    except (OSError, yaml.YAMLError):
        return None
