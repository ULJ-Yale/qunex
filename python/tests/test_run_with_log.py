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


def dies(sessionid=None):
    """A worker that never comes back: no outcome, only a broken pool."""
    os._exit(1)


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


@pytest.fixture
def full_run(tmp_path):
    """A run whose runlog also carries each call's report."""
    return gl.RunContext(
        "test_command",
        {},
        gl.LogSettings(runlog_content="full"),
        {"basefolder": str(tmp_path)},
        timestamp=STAMP,
    )


def comlogs(run):
    return sorted(os.listdir(run.comlogfolder))


def test_a_successful_call_leaves_a_done_comlog_holding_its_output(run):
    outcome = gc.run_with_log(
        works, args={"sessionid": "S01"}, run=run, tags=["works", "S01"]
    )

    assert outcome.name == "works"
    assert not outcome.failed and outcome.error is None
    assert os.path.basename(outcome.comlog).startswith("done_works_S01_")
    with open(outcome.comlog) as f:
        assert "worked on S01" in f.read()


def test_a_failing_call_leaves_an_error_comlog_and_says_so_in_the_runlog(run):
    run.header()
    outcome = gc.run_with_log(
        fails, args={}, run=run, name="fails: S01", tags=["fails", "S01"]
    )

    assert isinstance(outcome.error, ge.CommandFailed)
    assert outcome.failed == 1
    assert os.path.basename(outcome.comlog).startswith("error_")
    with open(run.path) as f:
        runlog = f.read()
    assert "session: S01" in runlog
    assert "ERROR running fails: S01" in runlog


def test_without_tags_no_comlog_is_opened(run, capsys):
    outcome = gc.run_with_log(works, args={}, run=run, tags=None)

    assert outcome.comlog is None
    assert "worked on None" in capsys.readouterr().out
    assert not os.path.isdir(run.comlogfolder)


def test_run_level_parameters_do_not_reach_the_command(run):
    outcome = gc.run_with_log(
        takes_only_its_own,
        args={"folder": "here", "scheduler": "SLURM", "logging": "full"},
        run=run,
        tags=["strip"],
    )

    assert not outcome.failed
    with open(outcome.comlog) as f:
        assert "folder is here" in f.read()


def test_a_catch_all_command_still_gets_them(run):
    outcome = gc.run_with_log(
        takes_everything,
        args={"folder": "here", "scheduler": "SLURM"},
        run=run,
        tags=["keep"],
    )

    assert not outcome.failed
    with open(outcome.comlog) as f:
        assert "got ['folder', 'scheduler']" in f.read()


def test_a_disabled_run_writes_no_files_at_all(tmp_path, capsys):
    run = gl.RunContext(
        "test_command", {}, gl.LogSettings(enabled=False), {"basefolder": str(tmp_path)}
    )

    outcome = gc.run_with_log(
        works, args={"sessionid": "S01"}, run=run, tags=["works", "S01"]
    )

    assert not outcome.failed
    assert outcome.comlog is None
    assert "worked on S01" in capsys.readouterr().out
    assert not list(tmp_path.rglob("*.log"))


def test_a_command_that_declares_a_log_gets_one_and_reports_into_its_comlog(run):
    run.header()
    outcome = gc.run_with_log(
        reports, args={"sessionid": "S01"}, run=run, tags=["reports", "S01"]
    )

    assert outcome.error is None and outcome.failed == 0
    with open(outcome.comlog) as f:
        comlogtext = f.read()
    # live in the comlog through the tee, and the injected parameter is not
    # spelled into the call echo
    assert "---> reporting on S01" in comlogtext
    assert "_log" not in comlogtext


def test_under_runlog_content_manifest_the_runlog_indexes_rather_than_repeats(run):
    """The default: the report is in the comlog, and the runlog says where."""
    run.header()
    outcome = gc.run_with_log(
        reports, args={"sessionid": "S01"}, run=run, tags=["reports", "S01"]
    )

    with open(run.path) as f:
        runlog = f.read()
    assert "---> reporting on S01" not in runlog
    assert "[log: %s]" % outcome.comlog in runlog


def test_under_runlog_content_full_the_runlog_carries_the_report_too(full_run):
    full_run.header()
    outcome = gc.run_with_log(
        reports, args={"sessionid": "S01"}, run=full_run, tags=["reports", "S01"]
    )

    with open(full_run.path) as f:
        runlog = f.read()
    assert "---> reporting on S01" in runlog
    assert "[log: %s]" % outcome.comlog in runlog


def test_with_no_comlog_the_report_goes_to_the_runlog_whatever_the_setting_says(
    tmp_path,
):
    """
    The clamp, and the one case that would lose the output silently.

    Under ``--logging=runlog`` there is no comlog, so the runlog is the only
    file that would hold the report: ``manifest`` asks to avoid duplication,
    not to discard the only copy.
    """
    run = gl.RunContext(
        "test_command",
        {},
        gl.LogSettings(comlog=False),
        {"basefolder": str(tmp_path)},
        timestamp=STAMP,
    )
    run.header()

    outcome = gc.run_with_log(
        reports, args={"sessionid": "S01"}, run=run, tags=["reports", "S01"]
    )

    assert outcome.comlog is None
    assert run.settings.runlog_content == "manifest"
    with open(run.path) as f:
        assert "---> reporting on S01" in f.read()


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
    outcome = gc.run_with_log(
        returns_data, args={"folder": "here"}, run=run, tags=["returns_data"]
    )

    assert outcome.error is None and outcome.failed == 0
    assert os.path.basename(outcome.comlog).startswith("done_")
    with open(run.path) as f:
        assert "Successful completion" in f.read()


def test_a_recorded_error_is_a_failure_even_when_the_command_returns_success(run):
    outcome = gc.run_with_log(
        reports_an_error, args={}, run=run, tags=["reports_an_error"]
    )

    assert outcome.error is None
    assert outcome.failed == 1


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


def test_parallel_calls_keep_their_output_in_their_own_comlog_and_off_the_console(
    run, capsys
):
    """
    N sessions' lines on one terminal are unreadable, so they do not go there.

    What the terminal keeps is the announcement of each comlog path and the
    per-call completion line, both printed in the parent.
    """
    run.header()
    calls = [
        {
            "name": "works: %s" % sid,
            "function": works,
            "args": {"sessionid": sid},
            "tags": ["works", sid],
        }
        for sid in ["S01", "S02"]
    ]

    gc.run_in_parallel(calls, cores=2, run=run)

    out = capsys.readouterr().out
    for sid in ["S01", "S02"]:
        assert "worked on %s" % sid not in out
        assert "works: %s finished successfully" % sid in out

    for name in comlogs(run):
        with open(os.path.join(run.comlogfolder, name)) as f:
            text = f.read()
        mine = "S01" if "S01" in name else "S02"
        other = "S02" if mine == "S01" else "S01"
        assert "worked on %s" % mine in text
        assert other not in text


def test_a_log_declaring_command_runs_per_session_and_writes_one_runlog(full_run):
    """
    The log is built inside ``run_with_log``, i.e. in the worker.

    A log built in the parent could not get here: futures pickle their
    arguments and ``pickle.dumps(sys.stdout)`` raises. So this pins both that
    the per-session path reports at all and that it still writes one runlog.
    """
    full_run.header()
    calls = [
        {
            "name": "reports: %s" % sid,
            "function": reports,
            "args": {"sessionid": sid},
            "tags": ["reports", sid],
        }
        for sid in ["S01", "S02"]
    ]

    results = gc.run_in_parallel(calls, cores=2, run=full_run)

    assert len(results) == 2
    assert len(list(os.listdir(full_run.logfolder))) == 2
    with open(full_run.path) as f:
        runlog = f.read()
    for sid in ["S01", "S02"]:
        assert "---> reporting on %s" % sid in runlog


def test_a_worker_that_dies_is_recorded_as_a_call_that_did_not_complete(run, capsys):
    """
    The hole nobody would find by reading: no outcome comes back at all.

    A ``BrokenProcessPool``, an OOM kill or a raise from the lines of
    ``run_with_log`` outside its try used to be printed and appended nowhere,
    so the call went missing from the digest and from the failure count -- a
    run in which a session never executed reported success and exited 0.
    """
    run.header()
    calls = [
        {
            "name": "dies: S01",
            "function": dies,
            "args": {"sessionid": "S01"},
            "tags": ["dies", "S01"],
        }
    ]

    results = gc.run_in_parallel(calls, cores=1, run=run)

    assert len(results) == 1
    # "did not complete", the spelling `digest` already has
    assert results[0].name == "dies: S01"
    assert results[0].failed is None
    assert results[0].error is not None
    assert "dies: S01 did not complete" in capsys.readouterr().out

    # and it is in the digest, in its own group, and it makes the run unsound:
    # `gmri` raises CommandFailed on `failed is None or failed`
    stati = [(o.name, str(o.error or "completed"), o.failed) for o in results]
    report = run.final_report(stati)
    assert "1 run, 0 successful, 0 failed, 1 did not complete" in report
    assert "Did not complete:" in report
    assert any(failed is None or failed for _, _, failed in stati)
