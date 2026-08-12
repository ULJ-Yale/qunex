#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``core.py``

This file holds code for core support functions used by other code for
preprocessing and analysis. The functions are for internal use
and can not be called externally.
"""

import contextlib
import gzip
import inspect
import re
import os.path
import multiprocessing
import os
import os.path
import shutil
import subprocess
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

from collections import namedtuple

import qx_utilities.general.batch_io as bio
import qx_utilities.general.filelock as fl
import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl

# the batch file parser, the session selector and the filter live in batch_io,
# which imports nothing from QuNex so it can be spliced into qunex_container.
# re-exported here, as this is where the tree imports them from.
BatchError = bio.BatchError
SessionList = bio.SessionList
read_batch = bio.read_batch
read_list = bio.read_list


# ==============================================================================
#                                              SESSION AND SUBJECT LIST HANDLING

# The parsing, selection and filtering themselves live in `batch_io`, which
# imports nothing from QuNex. What is added here is the QuNex error types.


def resolve_sessions(
    batchfile=None,
    sessions=None,
    filter=None,
    sessionsfolder=None,
    command=None,
    verbose=False,
):
    """
    ``resolve_sessions(batchfile=None, sessions=None, filter=None, sessionsfolder=None, command=None, verbose=False)``

    The single entry point for "which batch file, which sessions". Returns a
    tuple of the SessionList of the selected sessions and the parameters
    specified in the batch file header.

    If batchfile is provided, it is parsed - as a `*.list` file if it has that
    extension, as a batch file otherwise - and sessions and filter select within
    it. A batch file that is absent or can not be read is always an error.

    If batchfile is not provided, sessions is a comma, space or pipe separated
    list of session ids or globs, matched against the folders in sessionsfolder
    if one is given and taken as plain ids if it is not. The returned header
    parameters are then empty.

    If the command is running as a SLURM job array, only the sessions that
    belong to this array task are returned.
    """

    try:
        slist, header = bio.resolve(
            batchfile=batchfile,
            sessions=sessions,
            filter=filter,
            sessionsfolder=sessionsfolder,
            verbose=verbose,
        )

    except bio.BatchError as e:
        raise ge.CommandFailed(
            command if command else "resolve_sessions",
            "Could not compile the list of sessions to process",
            str(e),
            "Please check your parameters!",
        )

    # are we inside a SLURM job array?
    if "SLURM_ARRAY_TASK_ID" in os.environ:
        # get ID for this job
        slurm_array_ix = int(os.environ["SLURM_ARRAY_TASK_ID"])

        # get size of job array
        slurm_array_size = int(os.environ["SLURM_ARRAY_TASK_MAX"]) + 1

        # get the chunk
        slist = slist[slurm_array_ix::slurm_array_size]

    return slist, header


# ==============================================================================
#                                                          EXECUTION AND LOGGING

def deduce_folders(args, command=None, timestamp=None):
    """
    ``deduce_folders(args)``

    Tries to deduce the location of study specific folders based on the provided
    arguments. For internal use only.
    """

    reference = args.get("reference")
    logfolder = args.get("logfolder")
    basefolder = args.get("basefolder")
    if not basefolder:
        basefolder = args.get("studyfolder")
    sessionsfolder = args.get("sessionsfolder")
    sourcefolder = args.get("sourcefolder")
    folder = args.get("folder")

    if sessionsfolder:
        sessionsfolder = os.path.abspath(sessionsfolder)

    if basefolder is None:
        if sessionsfolder:
            basefolder = os.path.dirname(sessionsfolder)
        else:
            for f in [
                os.path.abspath(e)
                for e in [logfolder, sourcefolder, folder, reference, "."]
                if e
            ]:
                # the starting folder is tested first: a command run from the
                # study root is still being run inside a study
                if f and not basefolder:
                    while f and f != "/":
                        if any(
                            os.path.exists(os.path.join(f, marker))
                            for marker in [".qunexstudy", ".mnapstudy"]
                        ):
                            basefolder = f
                            break
                        f = os.path.dirname(f)

    if logfolder is None and timestamp and command:
        if basefolder:
            logfolder = os.path.join(basefolder, "logs", f"{timestamp}_{command}")
        else:
            logfolder = os.path.join(os.path.abspath("."), f"{timestamp}_{command}")
    elif logfolder == "legacy" or (not timestamp and not command):
        if basefolder:
            logfolder = os.path.join(basefolder, "processing", "logs")
        else:
            logfolder = os.path.abspath(".")

    if logfolder is None:
        homedir = os.path.expanduser("~")
        logfolder = os.path.join(homedir, "qunex")

    return {
        "basefolder": basefolder,
        "sessionsfolder": sessionsfolder,
        "logfolder": logfolder,
    }


def run_external_parallel(calls, cores=None, _log=None):
    """
    ``run_external_parallel(calls, cores=None)``

    Runs external commands specified in 'calls' in parallel utilizing all the
    available or the number of cores specified in 'cores'.

    Parameters:
        --calls (list):
            A list of dictionaries that specifies the commands to run. It should
            consists of:

            - 'name' ... the name of the command to run
            - 'args' ... the actual command provided as a list of arguments
            - 'sout' ... the name of the log file to which to direct the
              standard output from the command ran.

        --cores (int | str, default 'all'):
            Number of elements to run in parallel for grayordinate
            decomposition. If specified as None or 'all', all available elements
            (3 max for left surface, right surface and volume files) will be
            used. One element per CPU core is processed at a time.

        --_log:
            The log to report progress into. The underscore keeps the parameter
            off the command line; it replaces the `prepend` string the callers
            used to pass, the nesting now coming from the caller's log.

    Examples:
        ::

            run_external_parallel({'name': 'List all zip files', 'args': ['ls' '-l' '*.zip'], 'sout': 'zips.log'}, \\
            cores=1)
    """
    log = gl.log_or_console(_log)

    if cores is None or cores in ["all", "All", "ALL"]:
        try:
            cores = len(os.sched_getaffinity(0))
        except Exception:
            cores = multiprocessing.cpu_count()
    else:
        try:
            cores = int(cores)
        except Exception:
            cores = 1

    running = []
    completed = []

    while True:
        # --- check if we can add a process to run
        if len(running) < cores:
            if calls:
                call = calls.pop(0)
                if call["sout"]:
                    if os.path.exists(call["sout"]):
                        sout = open(call["sout"], "a", 1)
                    else:
                        sout = open(call["sout"], "w", 1)
                else:
                    sout = open(os.devnull, "w")

                print(
                    "Starting log for %s at %s\nThe command being run: \n>> %s\n"
                    % (
                        call["name"],
                        str(datetime.now()).split(".")[0],
                        " ".join(call["args"]),
                    ),
                    file=sout,
                )

                try:
                    if "shell" in call and call["shell"]:
                        running.append(
                            {
                                "call": call,
                                "sout": sout,
                                "p": subprocess.Popen(
                                    call["args"],
                                    stdout=sout,
                                    stderr=sout,
                                    bufsize=0,
                                    shell=True,
                                ),
                            }
                        )
                    else:
                        running.append(
                            {
                                "call": call,
                                "sout": sout,
                                "p": subprocess.Popen(
                                    call["args"], stdout=sout, stderr=sout, bufsize=0
                                ),
                            }
                        )

                    if call["sout"]:
                        log.detail(
                            f'started running {call["name"]} at {str(datetime.now()).split(".")[0]}, track progress in {call["sout"]}'
                        )
                    else:
                        log.detail(
                            f'started running {call["name"]} at {str(datetime.now()).split(".")[0]}'
                        )
                except Exception:
                    log.error(
                        f'failed to start running {call["name"]}. Please check your environment!'
                    )
                    completed.append(
                        {
                            "exit": -9,
                            "name": call["name"],
                            "log": call["sout"],
                            "args": call["args"],
                        }
                    )
                continue

        # --- check if a process finished
        done = []
        for n in range(len(running)):
            running[n]["sout"].flush()

            if running[n]["p"].poll() is not None:
                running[n]["sout"].close()
                if running[n]["call"]["sout"]:
                    log.detail(
                        f'finished running {running[n]["call"]["name"]} (exit code: {running[n]["p"].poll()}), log in {running[n]["call"]["sout"]}'
                    )
                else:
                    log.detail(
                        f'finished running {running[n]["call"]["name"]} (exit code: {running[n]["p"].poll()})'
                    )
                completed.append(
                    {
                        "exit": running[n]["p"].poll(),
                        "name": running[n]["call"]["name"],
                        "log": running[n]["call"]["sout"],
                        "args": running[n]["call"]["args"],
                    }
                )
                done.append(n)
        if done:
            while done:
                running.pop(done.pop())
            continue

        # --- check if we are done:
        if not calls and not running:
            log.detail("DONE")
            break

        # --- wait a bit
        time.sleep(1)

    return completed


results = []
lock = multiprocessing.Lock()

# What one call through `run_with_log` came to. `failed` is 0, 1 or None
# ("did not report", the spelling `general.log.digest` already uses); `error`
# is the exception the call raised, or None -- never what the command
# returned, which is for its python caller (see `run_with_log`). `prepend` is
# not a field: it is an input, and `run_in_parallel` binds it into the
# callback rather than carrying it through the worker and back.
CallOutcome = namedtuple("CallOutcome", "name failed error comlog")


def record(outcome, prepend=""):
    """
    ``record(outcome, prepend="")``

    Appends the :class:`CallOutcome` of a completed function.

    For internal use only.
    """

    global results

    results.append(outcome)

    with lock:
        see = " [log: %s]." % outcome.comlog if outcome.comlog else "."

        if outcome.failed is None:
            print("%s%s did not complete%s" % (prepend, outcome.name, see))
        elif outcome.failed:
            print("%s%s failed%s" % (prepend, outcome.name, see))
        else:
            print("%s%s finished successfully%s" % (prepend, outcome.name, see))


def record_future(future, name=None, prepend=""):
    if future.exception() is not None:
        print("Unhandled exception")
        print(future.exception())
        # the worker itself died -- a BrokenProcessPool, an OOM kill, a
        # pickling failure, or a raise from the lines of `run_with_log`
        # outside its try -- so there is no outcome to take. This used to
        # print and append nothing, which dropped the call from the digest,
        # from the status record and from the failure count: a run in which a
        # session never executed reported success and exited 0.
        record(CallOutcome(name, None, future.exception(), None), prepend)
    else:
        record(future.result(), prepend)


def _drop_run_parameters(function, args):
    """
    Drop the run-level parameters the command itself does not take.

    ``--logging``, ``--logfolder``, ``--scheduler`` and the rest steer how
    qunex runs a command, not what the command does, so reaching the callable
    is a TypeError. Functions with a ``**kwargs`` catch-all keep them: for
    those the pass-through is deliberate (``run_recipe`` threads ``eargs``
    this way).

    Note that this is never reached on a scheduler run: ``run_through_scheduler``
    strips ``--scheduler`` from the call it re-issues, and the paths that use it
    return before this one.
    """
    import qx_utilities.general.commands_support as gcs

    accepted = inspect.signature(function).parameters
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in accepted.values()):
        return

    for extra in gcs.extra_parameters:
        if extra in args and extra not in accepted:
            del args[extra]


def run_with_log(
    function, args=None, run=None, name=None, prepend="", tags=None, tee=True
):
    """
    ``run_with_log(function, args=None, run=None, name=None, prepend="", tags=None, tee=True)``

    Runs a function, capturing everything it prints into a comlog and
    recording the call and its outcome in the run's runlog.

    Parameters:
        --function     The function to run.
        --args         The arguments to call it with.
        --run          The RunContext that owns this run's logs. When None the
                       function runs with its output going to the console only.
        --name         The name to report the call under [the function name].
        --prepend      The string to prepend to each line of progress report.
        --tags         The name parts of the comlog to open. When None no
                       comlog is opened and the output goes to the console.
        --tee          Whether the call's output also reaches the console.
                       False for a call submitted by `run_in_parallel`, whose
                       output would interleave with every other call's: it
                       goes to the call's own comlog only, which is announced
                       before the call starts and is line-buffered so it can
                       be followed live.

    A command that declares a ``_log`` parameter is handed a
    :class:`general.log.ReportLog` to report into. See §14.15 of the logging
    plan: the signature is the declaration, and the underscore is what keeps the
    parameter off the command line. Its report goes into the comlog live, and
    into the runlog as well when ``runlog_content`` is ``full`` or the call has
    no comlog to hold it.

    **A command fails by raising or by recording an error, never by what it
    returns.** Its return value is for a python caller -- a path, a count, a
    list of files -- and is not inspected here.

    Returns:
        a :class:`CallOutcome`. `error` is None unless the call raised, in
        which case it holds the exception; `failed` is 1 when the call raised
        or recorded an error, so a caller building a status does not have to
        infer it.

    For internal use only.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")

    if name is None:
        name = function.__name__

    comlog = run.comlog(*tags, timestamp=timestamp) if run and tags else None
    if comlog:
        comlog.open()

    if comlog and comlog.file:
        gl.print_qunex_header(timestamp=timestamp, file=comlog.file)
        comlog.write("#\n")
        with lock:
            print(
                prepend
                + "started running %s at %s, track progress in %s"
                % (name, str(datetime.now()).split(".")[0], comlog.path)
            )
    else:
        with lock:
            print(gl.print_qunex_header(timestamp=timestamp))
            print("#")
            print(
                prepend
                + "started running %s at %s" % (name, str(datetime.now()).split(".")[0])
            )

    # everything the command prints from here on goes into the comlog -- and,
    # unless the call is one of several running at once, to the console as
    # well; the streams are restored however the block exits
    with comlog.capture_stdout(tee=tee) if comlog else contextlib.nullcontext():
        with lock:
            print(
                "call: gmri %s %s\n-----------------------------------------"
                % (
                    function.__name__,
                    " ".join(['%s="%s"' % (k, v) for (k, v) in args.items()]),
                )
            )

        # the log the command reports into, built here so that it echoes into
        # the tee installed above (and never crosses a process boundary: a
        # parallel run pickles `args`, and sys.stdout does not pickle). It is
        # passed only to a callable that declares `_log`, which is how a
        # command opts in; the rest run exactly as they did before.
        log = gl.log_or_console(None)
        takes_log = "_log" in inspect.signature(function).parameters

        # the call's outcome is the exception it raised and the errors it
        # recorded -- never its return value. A command returns whatever is
        # useful to a python caller (a path, a count, a list of files, True),
        # and reading that as a status made a successful `backup_files` an
        # error and a no-op `remove_qunex_metadata` a success.
        error = None

        try:
            _drop_run_parameters(function, args)
            function(**args, **({"_log": log} if takes_log else {}))
        except ge.CommandError as e:
            with lock:
                print(ge.report_command_error(name, e))
            error = e
        except ge.CommandNull as e:
            with lock:
                print(ge.report_command_null(name, e))
            error = e
        except ge.CommandFailed as e:
            with lock:
                print(ge.report_command_failed(name, e))
            error = e
        except Exception as e:
            with lock:
                print("\n\nERROR")
                print(traceback.format_exc())
            error = e

        with lock:
            print(
                "\n-----------------------------------------\nFinished at %s"
                % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )

        # a command that took the log has a report to close; one that did not
        # recorded nothing, so there is nothing to write and nothing to derive
        # the count from. `failed` is the exception *or* a recorded error --
        # the error count is an additional source of failure, not a substitute.
        report = None
        failed = 1 if error else 0
        if log.text:
            log.finish(
                str(error) if error else "completed",
                failed=1 if error else None,
                name=name,
            )
            report = log.text
            failed = log.status[2]

        if not failed:
            print(f"\n---> Successful completion of task at {datetime.now()}")

    comlogname = comlog.close(status="error" if failed else "done") if comlog else None

    # record the call in the run's runlog -- one runlog per run, so this
    # appends to the file the RunContext opened rather than creating its own.
    # RunContext.write no-ops when the run has no runlog, which is what keeps
    # a run the settings gave no runlog from growing one here.
    if run:
        command, _, session = name.partition(": ")
        # the run's header already spelled the call; only a per-session call
        # is worth echoing again, since its arguments differ from the run's
        entry = gl.call_echo(command, args, session) + "\n" if session else name
        status = (
            "ERROR running %s" % name
            if failed
            else f"---> Successful completion of task at {datetime.now()}"
        )
        # the status line names the comlog in both modes: under `manifest` it is
        # the only pointer to what the command actually said
        if comlogname:
            status += " [log: %s]" % comlogname

        # `runlog_content` decides whether the report goes here as well as into
        # the comlog, where the same text already is -- and the setting is
        # clamped: a call with no comlog puts its report in the runlog whatever
        # the setting says, since `manifest` asks to avoid duplication and not
        # to discard the only copy.
        keep_report = report is not None and (
            comlogname is None or run.settings.runlog_content == "full"
        )
        body = "%s\n%s" % (report, status) if keep_report else status
        run.write("\n%s\n%s\n" % (entry, body))

    return CallOutcome(name, failed, error, comlogname)


def run_in_parallel(calls, cores=None, prepend="", run=None):
    """
    ``run_in_parallel(calls, cores=None, prepend="")``

    Runs functions specified in 'calls' in parallel utilizing all the available
    or the number of cores specified in 'cores'.

    INPUTS
    ======

    --calls        A list of dictionaries that specifies the commands to run.
                   It should consists of:

                   - name (the name of the command to run)
                   - function (the function to be run)
                   - args (the arguments to be passed to the function)
                   - tags (the name parts of the comlog to write the standard
                     output of the command to, or None for no comlog)

    --cores        The number of cores to utilize. If specified as None or
                   'all', all available cores will be utilized.
    --prepend      The string to prepend to each line of progress report.
    --run          The RunContext that owns this run's logs.

    EXAMPLE USE
    ===========

    ::

        run_in_parallel({'name': 'Sort dicom files', 'function': dicom.sort_dicom, 'args': {'folder': '.'}, 'tags': ['sort_dicom']}, cores=1, prepend=' ... ')
    """

    global results

    if cores is None or cores in ["all", "All", "ALL"]:
        cores = len(os.sched_getaffinity(0))
    else:
        try:
            cores = int(cores)
        except Exception:
            cores = 1

    results = []
    with ProcessPoolExecutor(max_workers=cores) as executor:
        for call in calls:
            future = executor.submit(
                run_with_log,
                call["function"],
                args=call["args"],
                run=run,
                name=call["name"],
                prepend=prepend,
                tags=call.get("tags"),
                tee=False,
            )
            # the name and `prepend` are bound here rather than returned by the
            # worker: both are inputs, and a worker that dies returns nothing
            # to take the name from
            future.add_done_callback(
                lambda f, n=call["name"], p=prepend: record_future(f, n, p)
            )

    return results


def check_files(test_folder, spec_file, fields=None, report=None):
    """
    ``check_files(test_folder, spec_file, fields=None, report=None)``

    Check the test_folder for presence of files as specified in spec_file, which
    lists files one per line with space delimited paths. Additionally an array
    of key-value pairs can be provided. If present every instance of {<key>}
    will be replaced by <value>. Where there might be two alternative options of
    results e.g. difference because of AP/PA direction, then the alternative is
    to be provided in the same line separated by a pipe '|'

    `report` is an open file handle -- the comlog of the call being checked --
    or None. It used to accept a path as well, and told the two apart with the
    Python 2 name ``types.FileType``; the only caller that ever passed one
    passed the path of a comlog it did not hold open, so the path form and its
    ``append`` companion are gone with it.
    """

    # --- the report goes to the caller's handle, when there is one

    if report:
        print(
            "\n#-----------------------------------------\n# Full file check report\n# . denotes file present\n# X denotes file absent\n",
            file=report,
        )

    # --- initial tests

    if not os.path.exists(test_folder):
        if report:
            print(
                "The folder to be tested does not exist: %s \nPlease check your settings and paths!"
                % (test_folder),
                file=report,
            )
            print(
                "\n#-----------------=== End Full File Report ===----------------------",
                file=report,
            )
        raise ge.CommandFailed(
            "check_files",
            "Folder to test does not exist",
            "The folder to be tested does not exist: %s" % (test_folder),
            "Please check your settings and paths!",
        )

    if not os.path.exists(spec_file):
        if report:
            print(
                "The specification file to test folder against does not exist: %s\nPlease check your settings and paths!"
                % (spec_file),
                file=report,
            )
            print(
                "\n#-----------------=== End Full File Report ===----------------------",
                file=report,
            )
        raise ge.CommandFailed(
            "check_files",
            "Specification file does not exist",
            "The specification file to test folder against does not exist: %s"
            % (spec_file),
            "Please check your settings and paths!",
        )

    # --- read the spec

    with open(spec_file, "r") as spec:
        files = spec.read()

    if fields:
        for key, value in fields:
            files = files.replace("{%s}" % (key), value)

    files = [
        [f.strip().split() for f in e.split("|")]
        for e in files.split("\n")
        if len(e) and not e.startswith("#")
    ]

    # --- test the files

    present = []
    missing = []
    for testfiles in files:
        file_missing = True
        for testfile in testfiles:
            test = [test_folder] + testfile
            tfile = os.path.join(*test)
            if os.path.exists(tfile):
                present.append(tfile)
                file_missing = False
                if report:
                    print(". " + tfile, file=report)
                break
        if file_missing:
            missing.append(tfile)
            if report:
                print("X " + tfile, file=report)

    if report:
        print(
            "\n#-----------------=== End Full File Report ===----------------------",
            file=report,
        )

    status = len(missing) == 0

    return status, present, missing


def print_and_log(*args, **kwargs):
    """
    ``print_and_log(*args, **kwargs)``

    Prints all that is given as nonpositional argument to the standard output.

    INPUTS
    ======

    --file         Prints to the file.
    --silent       Whether to not print to stdout.
    --end          How to end ['\n'].
    """

    silent = kwargs.get("silent", False)
    file = kwargs.get("file", None)
    end = kwargs.get("end", "\n")

    for element in args + (end,):
        if not silent:
            print(element, end=" ")
        if file:
            print(element, end=" ", file=file)


def underscore(s):
    s = s + "\n" + "".join(["=" for e in range(len(s))])
    return s


def plist(s):
    """
    plist(s)
    Processes the string, spliting it by the pipe "|" symbol, trimming
    any whitespace caracters from start or end of each resulting
    substring, and retuns an array of substrings of length more than 0.
    """
    s = s.split("|")
    s = [e.strip() for e in s]
    s = [e for e in s if len(e) > 0]
    return s


def pcslist(s):
    """
    pcslist(s)
    Processes the string, spliting it by the pipe "|", comma or space, trimming
    any whitespace caracters from start or end of each resulting substring, and
    retuns an array of substrings of length more than 0.
    """
    s = re.split(r" *, *| *\| *| +", s)
    s = [e.strip() for e in s]
    s = [e for e in s if len(e) > 0]
    return s


def link_or_copy(source, target, status=None, name=None, symlink=False, *, _log=None):
    """
    Hard-link a file, falling back to a copy, and report the outcome.

    Parameters:
        source (str): path to the file to map.
        target (str): destination path.
        _log (ReportLog | None): report log; when given, the mapping outcome is
            noted in it. Spelled with the underscore because that is the one
            name a log parameter has in this tree -- a plain `log` in a
            registered command's signature would collide with the `--log`
            comlog-retention parameter.
        status (bool | None): running status carried through (defaults True).
        name (str | None): human readable name used in the report message.
        symlink (bool): create a symbolic link instead of a hard link.

    Returns:
        bool: the running status -- False when the file could not be mapped.
    """

    log = _log

    def note(level, message):
        if log is not None:
            getattr(log, level)(message)

    if status is None:
        status = True
    if name is None:
        name = "file"
    if os.path.exists(source):
        try:
            if os.path.exists(target):
                if os.path.samefile(source, target):
                    note("detail", f"{name} already mapped")
                    return status and True
                else:
                    os.remove(target)

            # link
            if not symlink:
                os.link(source, target)
            else:
                os.symlink(source, target)

            note("detail", f"{name} mapped")
            return status and True

        except Exception:
            try:
                shutil.copy2(source, target)
                note("detail", f"{name} copied")
                return status and True
            except Exception:
                note("error", f"{name} could not be copied, check permissions!")
                return False
    else:
        note(
            "error",
            f"{name} could not be copied, source file does not exist [{source}]!",
        )
        return False


def move_link_or_copy(
    source, target, action=None, status=None, name=None, lock=False, *, _log=None
):
    """
    Map a file into place by moving, hard-linking or copying it.

    A failure is recorded in `_log`, when one is given; a success is not. The
    callers report their mapping as a count ("42 images mapped") rather than
    per file, so a line each would bury the run's report -- which is also why
    the message never came back as a string: every caller threw the successful
    one away and kept only the failure.

    Parameters:
        source (str): path to the file to map.
        target (str): destination path.
        action (str | None): one of ``"move"``, ``"link"``, ``"copy"`` or
            ``"gzip"`` (defaults ``"link"``).
        status (bool | None): running status carried through (defaults True).
        name (str | None): human readable name used in the report message
            (defaults to ``source``).
        lock (bool): serialise the mapping with a file lock to make it safe for
            concurrent callers.
        _log (ReportLog | None): report log; a failed mapping is recorded in it
            as an error, or -- for a missing source -- as a warning.

    Returns:
        bool: the status. False when the mapping failed.
    """
    if action is None:
        action = "link"
    if status is None:
        status = True
    if name is None:
        name = source

    def report(rstatus, message=None, level="error"):
        """Unlock, note a failure in the log when there is one, and return."""
        if lock:
            fl.unlock(target)
        if message is not None and _log is not None:
            getattr(_log, level)(message)
        return rstatus

    if os.path.exists(source):
        targetfolder = os.path.dirname(target)
        if not os.path.exists(targetfolder):
            io = fl.makedirs(targetfolder)
            if io:
                if io != "File exists":
                    return report(
                        False,
                        f"{name} could not be {action}ed, target folder could not "
                        "be created, check permissions!",
                    )

        if lock:
            fl.lock(target)

        if action == "link":
            io = fl.link(source, target)
            if not io:
                return report(status)
            elif io == "File exists":
                if os.path.samefile(source, target):
                    return report(status)
                else:
                    io = fl.remove(target)
                    if io and io != "No such file or directory":
                        return report(
                            False,
                            f"{name} could not be {action}ed, existing file could "
                            "not be removed, check permissions!",
                        )
                    io = fl.link(source, target)
                    if not io:
                        return report(status)
                    else:
                        action = "copy"
            else:
                action = "copy"

        if action == "copy":
            try:
                shutil.copy2(source, target)
                return report(status)
            except Exception:
                return report(
                    False, f"{name} could not be copied, check permissions!"
                )

        if action == "move":
            try:
                shutil.move(source, target)
                return report(status)
            except Exception:
                return report(
                    False, f"{name} could not be moved, check permissions!"
                )

        if action == "gzip":
            try:
                with open(source, "rb") as f_in, gzip.open(target, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                return report(status)
            except Exception:
                return report(
                    False,
                    f"{name} could not be copied and gzipped, check permissions!",
                )

    else:
        return report(
            False,
            f"{name} could not be {action}ed, source file either does not exist "
            f"or can not be accessed [{source}]!",
            level="warning",
        )


def create_session_file(command, sfolder, session, subject, overwrite, prefix=""):
    """
    ``create_session_file(command, sfolder, session, subject, overwrite, prefix)``

    Creates the generic, non pipeline specific, session file.
    """

    # open fifle
    sfile = os.path.join(sfolder, "session.txt")
    if os.path.exists(sfile):
        if overwrite == "yes" or overwrite is True:
            os.remove(sfile)
            print(prefix + "---> removed existing session.txt file")
        else:
            raise ge.CommandFailed(
                command,
                "session.txt file already present!",
                "A session.txt file alredy exists [%s]" % (sfile),
                "Please check or set parameter 'overwrite' to 'yes' to rebuild it!",
            )

    sout = open(sfile, "w")
    gl.print_qunex_header(file=sout)
    print("#", file=sout)
    print("session:", session, file=sout)
    print("subject:", subject, file=sout)

    # bids
    bfolder = os.path.join(sfolder, "bids")
    if os.path.exists(bfolder):
        print("bids:", bfolder, file=sout)

    # nii
    nfolder = os.path.join(sfolder, "nii")
    if os.path.exists(bfolder):
        print("raw_data:", nfolder, file=sout)

    # hcp
    hfolder = os.path.join(sfolder, "hcp")
    print("hcp:", hfolder, file=sout)

    # empty line
    print(file=sout)

    # return
    return sout



