#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
The comlog chain end to end: ``process.run`` to the file on disk.

Where a comlog goes, and whether it is deleted, is decided in three places that
never meet in any other test: ``process.run`` builds the options and the run
context, ``do_options_check`` turns ``--comlog_folders`` into a list of real
folders, and ``run_external_for_file`` writes and ``close_log`` disposes of the
file. Every command that exercises all three is an HCP pipeline, and those need
imaging data to reach their first external call -- which is why the destination
and retention rules could be checked by hand at the unit level but never end to
end.

:func:`external_step` closes that gap. It is a real session-processing command
by every contract ``process.run`` applies -- it takes ``(sinfo, options,
overwrite, thread)``, calls ``do_options_check``, runs something external
against a check file and **returns its log** -- whose external tool happens to
be one line of shell. Nothing here is mocked: the options come from
``arglist``, the sessions from a batch file, the runlog and comlogs from the
run context, and the comlog is written by the same helper the 110 real call
sites use.

That makes it the one harness in the suite that exercises the *return* chain as
well: the log a command hands back, ``write_to`` putting its report in the
runlog, ``status`` reaching the final report -- and, with ``parsessions``
raised, the log surviving the pickle out of a real ``ProcessPoolExecutor``.
"""

import os

import pytest

import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl
import qx_utilities.general.process as gp
import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog


# defined at module level so a ProcessPoolExecutor could pickle it, the same
# constraint every real processing command is under
def external_step(sinfo, options, overwrite=False, thread=0):
    """A processing command whose external tool is one line of shell."""
    log = ReportLog()
    pc.do_options_check(options, sinfo, "external_step")

    checkfile = os.path.join(options["sessionsfolder"], sinfo["id"], "ran.txt")
    failed = 0

    try:
        pc.run_external_for_file(
            checkfile,
            options["shell_command"] % {"checkfile": checkfile},
            "... running the external step",
            log,
            overwrite=overwrite,
            task="step",
            logfolder=options["comlogs"],
            logtags=sinfo["id"],
            remove=options["log"] == "remove",
        )
    except pc.ExternalFailed as e:
        log.raw(str(e))
        failed = 1

    log.step("external step done for %s" % sinfo["id"])
    return log.result("external step ran", failed, sinfo["id"])


# the study level twin: no session id of its own, so `write_to` files it under
# the command name -- the case `proc_response` used to call "Unknown"
def study_step(sinfo, options, overwrite=False, thread=0):
    """A study-processing command that reports without naming a session."""
    log = ReportLog()
    pc.do_options_check(options, sinfo, "study_step")

    log.step("looked at %d sessions" % len(list(sinfo)))
    return log.finish("study step ran")


class Command:
    """Stand-in for the registry entry `process.run` is handed."""

    name = "external_step"
    type = "processing/session"
    logging = None

    def load_callable(self):
        return external_step


class StudyCommand(Command):
    name = "study_step"
    type = "processing/study"

    def load_callable(self):
        return study_step


@pytest.fixture
def study(tmp_path):
    """A study with one session and a batch file naming it."""
    sessions = tmp_path / "sessions"
    (sessions / "S01").mkdir(parents=True)
    (tmp_path / ".qunexstudy").write_text("")

    batch = tmp_path / "batch.txt"
    batch.write_text(
        "id: S01\nsubject: S01\nhcp: %s\n\n01: T1w\n" % (sessions / "S01" / "hcp")
    )
    return tmp_path


@pytest.fixture(autouse=True)
def default_settings():
    """`process.run` sets the process-wide settings; put them back after."""
    yield
    gl.set_active(None)


def run_step(study, settings=None, shell="touch %(checkfile)s", command=None, **args):
    """Drive the real `process.run` over the one session, and say what it left."""
    args = {
        "sessions": str(study / "batch.txt"),
        "sessionsfolder": str(study / "sessions"),
        "shell_command": shell,
        **args,
    }
    gp.run(command or Command(), args, settings or gl.LogSettings())

    logfolder = next((study / "logs").iterdir())
    runlog = next(f for f in logfolder.iterdir() if f.name.startswith("Log-"))
    return logfolder, runlog.read_text()


def comlogs_in(folder):
    return sorted(os.listdir(folder)) if os.path.isdir(folder) else []


# ------------------------------------------------------- where a comlog goes


def test_the_comlog_lands_in_the_run_folder_by_default(study):
    logfolder, runlog = run_step(study)

    written = comlogs_in(logfolder / "comlogs")
    assert len(written) == 1 and written[0].startswith("done_step_S01_")
    assert "---> logfile: " in runlog


def test_comlog_folders_fans_the_comlog_out_to_all_three_destinations(study):
    """
    The rule that could not be checked without imaging data.

    `--comlog_folders=study,session,hcp` writes the comlog to the first and maps
    it into the other two, and each destination is named in the runlog.
    """
    logfolder, runlog = run_step(study, comlog_folders="study,session,hcp")

    name = comlogs_in(logfolder / "comlogs")[0]
    session_copy = study / "sessions" / "S01" / "logs" / "comlogs" / name
    hcp_copy = study / "sessions" / "S01" / "hcp" / "S01" / "logs" / "comlogs" / name

    assert session_copy.exists() and hcp_copy.exists()
    assert str(session_copy) in runlog and str(hcp_copy) in runlog
    # all three hold the same call, not three different runs
    assert "Running external command via QuNex" in session_copy.read_text()


def test_the_settings_supply_the_destinations_when_the_command_line_does_not(study):
    """`--comlog_folders` empty means "take the policy", through the real chain."""
    logfolder, _ = run_step(
        study, settings=gl.LogSettings(comlog_folders=("study", "session"))
    )

    name = comlogs_in(logfolder / "comlogs")[0]
    assert (study / "sessions" / "S01" / "logs" / "comlogs" / name).exists()


def test_a_command_line_comlog_folders_beats_the_settings(study):
    logfolder, _ = run_step(
        study,
        settings=gl.LogSettings(comlog_folders=("study", "session")),
        comlog_folders="study",
    )

    assert not (study / "sessions" / "S01" / "logs").exists()
    assert len(comlogs_in(logfolder / "comlogs")) == 1


def test_a_deprecated_log_destination_still_reaches_do_options_check(study, capsys):
    """The remap has to survive `process.run`'s option handling, not just gmri's."""
    from qx_utilities.general import commands_support as gcs

    args = gcs.check_deprecated_parameters({"log": "study|session"}, "external_step")
    logfolder, _ = run_step(study, **args)

    name = comlogs_in(logfolder / "comlogs")[0]
    assert (study / "sessions" / "S01" / "logs" / "comlogs" / name).exists()
    assert "--comlog_folders" in capsys.readouterr().out


# --------------------------------------------------- whether it is deleted


def test_log_remove_deletes_the_comlog_and_records_it_in_the_runlog(study):
    """
    The record has to reach the *runlog*, not just the session's report.

    That is the whole point of the rule -- the comlog is gone, so the runlog is
    the only place left that says the step ran and how it ended.
    """
    logfolder, runlog = run_step(study, log="remove")

    assert comlogs_in(logfolder / "comlogs") == []
    assert "---> completed [done], comlog removed" in runlog
    assert "---> logfile: " not in runlog


def test_an_error_in_the_comlog_vetoes_an_explicit_log_remove(study):
    """
    A tool that exits 0, writes its check file, and logs errors anyway.

    The session still passes -- the check file is there -- so nothing else in
    the run would have kept this comlog.
    """
    logfolder, runlog = run_step(
        study,
        log="remove",
        shell="echo 'ERROR: it went wrong' && touch %(checkfile)s",
    )

    kept = comlogs_in(logfolder / "comlogs")
    assert len(kept) == 1 and kept[0].startswith("done_")
    assert "comlog kept -- it reports errors" in runlog
    assert "ERROR: it went wrong" in (logfolder / "comlogs" / kept[0]).read_text()


def test_keep_comlogs_beats_log_remove(study):
    logfolder, runlog = run_step(
        study, settings=gl.LogSettings(keep_comlogs=True), log="remove"
    )

    assert len(comlogs_in(logfolder / "comlogs")) == 1
    assert "comlog removed" not in runlog


def test_a_removed_comlog_is_still_removed_from_every_destination(study):
    """Removal wins over the fan-out: nothing is mapped out before it happens."""
    logfolder, _ = run_step(study, log="remove", comlog_folders="study,session")

    assert comlogs_in(logfolder / "comlogs") == []
    assert comlogs_in(study / "sessions" / "S01" / "logs" / "comlogs") == []


# ------------------------------------------------------------ the run around it


def test_a_failing_tool_keeps_an_error_comlog_and_fails_the_command(study):
    with pytest.raises(ge.CommandFailed):
        run_step(study, log="remove", shell="exit 3")

    logfolder = next((study / "logs").iterdir())
    kept = comlogs_in(logfolder / "comlogs")
    assert len(kept) == 1 and kept[0].startswith("error_")


def test_comlogs_off_writes_no_comlog_through_the_whole_chain(study):
    logfolder, runlog = run_step(study, settings=gl.LogSettings(comlog=False))

    assert comlogs_in(logfolder / "comlogs") == []
    assert "---> logfile: " not in runlog
    # the runlog itself is still written, and the session still passed
    assert "external step ran" in runlog


# ------------------------------------------------- the return chain (OI-1)


def test_the_returned_log_reaches_both_the_runlog_and_the_final_report(study):
    """
    The whole of what a command hands back, end to end.

    Its report text is appended to the runlog by `write_to`, and its `status`
    is what the run's closing digest is built from -- with the session id it
    carries, not one reconstructed at the call site.
    """
    _, runlog = run_step(study)

    assert "---> external step done for S01" in runlog
    assert "     ... S01 ---> external step ran" in runlog
    assert "1 run, 1 successful, 0 failed, 0 did not complete" in runlog


def test_a_study_command_is_filed_under_the_command_name(study):
    """
    A plain `ReportLog` has no id; the run supplies one.

    `proc_response` used to call this "Unknown" and leave it out of the digest
    altogether.
    """
    _, runlog = run_step(study, command=StudyCommand())

    assert "     ... study_step ---> study step ran" in runlog
    assert "Unknown" not in runlog


def test_a_failing_command_reports_its_failure_through_its_log(study):
    with pytest.raises(ge.CommandFailed):
        run_step(study, shell="exit 3")

    logfolder = next((study / "logs").iterdir())
    runlog = next(f for f in logfolder.iterdir() if f.name.startswith("Log-"))
    text = runlog.read_text()

    assert "     ... S01 ---> external step ran" in text
    assert "0 successful, 1 failed" in text


def test_the_log_survives_the_process_pool(study):
    """
    The one new failure class the return contract creates, closed end to end.

    With `parsessions` above one the log is pickled out of a real
    `ProcessPoolExecutor` worker, which a `(str, tuple)` never had to survive.
    """
    _, runlog = run_step(study, parsessions=2)

    assert "---> external step done for S01" in runlog
    assert "     ... S01 ---> external step ran" in runlog
