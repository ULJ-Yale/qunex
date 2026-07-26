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

Note the import direction: nothing here may import ``general.core`` at module
level -- ``general.core`` is a consumer of this package. The one helper needed
from it, ``print_qunex_header``, is imported inside :meth:`RunContext.header`.
"""

import contextlib
import multiprocessing
import os
import os.path
import re
import sys
from datetime import datetime

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


def comlog_folder(folders):
    """
    The comlogs folder implied by a set of folder hints.

    For callers that open a comlog without holding a :class:`RunContext` --
    they have a sessions folder and nothing else.

    Parameters:
        folders: the hints to deduce from, e.g. ``{"sessionsfolder": ...}``.

    Returns:
        the path of the comlogs folder.
    """
    # lazily imported: `general.core` consumes this package, not the other way
    # around (see the module docstring)
    from qx_utilities.general.core import deduce_folders

    return os.path.join(deduce_folders(folders)["logfolder"], "comlogs")


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
        self.file = open(self.path, "w")
        return self

    def write(self, text):
        """Append `text` to the comlog; a no-op when it is disabled."""
        if self.file:
            self.file.write(text)
            self.file.flush()

    @contextlib.contextmanager
    def capture_stdout(self):
        """
        Tee everything printed inside the block into the comlog.

        The commands this wraps report by printing, so their output has to be
        intercepted rather than handed over. Both streams are restored when the
        block exits, however it exits.

        Yields:
            this comlog.
        """
        if not self.file:
            yield self
            return

        tee = _Tee(sys.stdout, self.file)
        with contextlib.redirect_stdout(tee), contextlib.redirect_stderr(tee):
            yield self

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
        # lazily imported: `general.core` consumes this package, not the
        # other way around (see the module docstring)
        from qx_utilities.general.core import print_qunex_header

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
        lines = ["\n\n---> Final report for command %s" % self.command]

        failed_total = 0
        for sid, report, failed in stati:
            if "Unknown" in sid:
                continue
            lines.append("... %s ---> %s" % (sid, report))
            if failed is None:
                failed_total = None
            elif failed_total is not None:
                failed_total += failed

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
