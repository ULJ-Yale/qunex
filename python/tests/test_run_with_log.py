# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for ``general.core.run_with_log`` on a :class:`RunContext`.

This is the path a parallel session run takes, and the one that cannot be
checked by reading: the RunContext is pickled into every worker process, the
comlog is opened there, and all of them append to one runlog. So these run the
real ``run_in_parallel``.
"""

import os

import pytest

import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl

STAMP = "2026-07-26_12.00.00.000000"


def works(sessionid=None):
    print("worked on %s" % sessionid)
    return False


def fails(sessionid=None):
    raise ge.CommandFailed("fails", "No", "It did not work")


def takes_only_its_own(folder=None):
    print("folder is %s" % folder)
    return False


def takes_everything(**kwargs):
    print("got %s" % sorted(kwargs))
    return False


def returns_data(folder=None):
    print("did the work")
    return ["a.txt", "b.txt"]


def reports(sessionid=None, _log=None):
    log = gl.log_or_console(_log)
    log.step("reporting on %s" % sessionid)
    return False


def reports_an_error(_log=None):
    log = gl.log_or_console(_log)
    log.error("could not do it")
    return False


@pytest.fixture
def run(tmp_path):
    return gl.RunContext(
        "test_command",
        {},
        gl.LogSettings(),
        {"basefolder": str(tmp_path)},
        timestamp=STAMP,
    )


def comlogs(run):
    return sorted(os.listdir(run.comlogfolder))


def test_a_successful_call_leaves_a_done_comlog_holding_its_output(run):
    name, result, comlog, *_ = gc.run_with_log(
        works, args={"sessionid": "S01"}, run=run, tags=["works", "S01"]
    )

    assert name == "works"
    assert not result
    assert os.path.basename(comlog).startswith("done_works_S01_")
    with open(comlog) as f:
        assert "worked on S01" in f.read()


def test_a_failing_call_leaves_an_error_comlog_and_says_so_in_the_runlog(run):
    run.header()
    _, result, comlog, *_ = gc.run_with_log(
        fails, args={}, run=run, name="fails: S01", tags=["fails", "S01"]
    )

    assert isinstance(result, ge.CommandFailed)
    assert os.path.basename(comlog).startswith("error_")
    with open(run.path) as f:
        runlog = f.read()
    assert "session: S01" in runlog
    assert "ERROR running fails: S01" in runlog


def test_without_tags_no_comlog_is_opened(run, capsys):
    _, _, comlog, *_ = gc.run_with_log(works, args={}, run=run, tags=None)

    assert comlog is None
    assert "worked on None" in capsys.readouterr().out
    assert not os.path.isdir(run.comlogfolder)


def test_run_level_parameters_do_not_reach_the_command(run):
    _, result, comlog, *_ = gc.run_with_log(
        takes_only_its_own,
        args={"folder": "here", "scheduler": "SLURM", "logging": "full"},
        run=run,
        tags=["strip"],
    )

    assert not result
    with open(comlog) as f:
        assert "folder is here" in f.read()


def test_a_catch_all_command_still_gets_them(run):
    _, result, comlog, *_ = gc.run_with_log(
        takes_everything,
        args={"folder": "here", "scheduler": "SLURM"},
        run=run,
        tags=["keep"],
    )

    assert not result
    with open(comlog) as f:
        assert "got ['folder', 'scheduler']" in f.read()


def test_a_disabled_run_writes_no_files_at_all(tmp_path, capsys):
    run = gl.RunContext(
        "test_command", {}, gl.LogSettings(enabled=False), {"basefolder": str(tmp_path)}
    )

    _, result, comlog, *_ = gc.run_with_log(
        works, args={"sessionid": "S01"}, run=run, tags=["works", "S01"]
    )

    assert not result
    assert comlog is None
    assert "worked on S01" in capsys.readouterr().out
    assert not list(tmp_path.rglob("*.log"))


def test_a_command_that_declares_a_log_gets_one_and_its_report_reaches_the_runlog(run):
    run.header()
    _, result, comlog, _, failed = gc.run_with_log(
        reports, args={"sessionid": "S01"}, run=run, tags=["reports", "S01"]
    )

    assert not result and failed == 0
    with open(run.path) as f:
        runlog = f.read()
    # the report, not the two-line stub
    assert "---> reporting on S01" in runlog
    with open(comlog) as f:
        comlogtext = f.read()
    # live in the comlog through the tee, and the injected parameter is not
    # spelled into the call echo
    assert "---> reporting on S01" in comlogtext
    assert "_log" not in comlogtext


def test_a_command_that_does_not_declare_one_keeps_the_two_line_stub(run):
    run.header()
    gc.run_with_log(works, args={"sessionid": "S01"}, run=run, tags=["works", "S01"])

    with open(run.path) as f:
        runlog = f.read()
    # the command's output is in its comlog; the runlog gets the call and the
    # status and no empty report
    assert "worked on S01" not in runlog
    assert "Successful completion" in runlog


def test_a_command_that_returns_data_is_not_a_failure(run):
    """
    A command fails by raising or by recording an error, never by returning.

    ``backup_files`` returns the list of files it copied, ``check_study`` the
    study folder, ``remove_qunex_metadata`` True when it removed something --
    reading the return value as a status made every one of those a failed run.
    """
    run.header()
    _, result, comlog, _, failed = gc.run_with_log(
        returns_data, args={"folder": "here"}, run=run, tags=["returns_data"]
    )

    assert result is None and failed == 0
    assert os.path.basename(comlog).startswith("done_")
    with open(run.path) as f:
        assert "Successful completion" in f.read()


def test_a_recorded_error_is_a_failure_even_when_the_command_returns_success(run):
    _, result, _, _, failed = gc.run_with_log(
        reports_an_error, args={}, run=run, tags=["reports_an_error"]
    )

    assert not result
    assert failed == 1


def test_parallel_calls_share_one_runlog_and_get_one_comlog_each(run):
    run.header()
    calls = [
        {
            "name": "works: %s" % sid,
            "function": works,
            "args": {"sessionid": sid},
            "tags": ["works", sid],
        }
        for sid in ["S01", "S02", "S03"]
    ]

    results = gc.run_in_parallel(calls, cores=2, run=run)

    assert len(results) == 3
    # one runlog for the whole run, one comlog per call
    assert len(list(os.listdir(run.logfolder))) == 2
    assert len(comlogs(run)) == 3

    with open(run.path) as f:
        runlog = f.read()
    for sid in ["S01", "S02", "S03"]:
        assert "session: %s" % sid in runlog
    assert runlog.count("Successful completion") == 3


def test_a_log_declaring_command_runs_per_session_and_writes_one_runlog(run):
    """
    The log is built inside ``run_with_log``, i.e. in the worker.

    A log built in the parent could not get here: futures pickle their
    arguments and ``pickle.dumps(sys.stdout)`` raises. So this pins both that
    the per-session path reports at all and that it still writes one runlog.
    """
    run.header()
    calls = [
        {
            "name": "reports: %s" % sid,
            "function": reports,
            "args": {"sessionid": sid},
            "tags": ["reports", sid],
        }
        for sid in ["S01", "S02"]
    ]

    results = gc.run_in_parallel(calls, cores=2, run=run)

    assert len(results) == 2
    assert len(list(os.listdir(run.logfolder))) == 2
    with open(run.path) as f:
        runlog = f.read()
    for sid in ["S01", "S02"]:
        assert "---> reporting on %s" % sid in runlog
