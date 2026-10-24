# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for what ``general.scheduler`` records in a run's runlog, and for where
the jobs it submits log.

The submission record belongs in the runlog the run already opened. Until N7.2
the scheduler opened that file with ``"w"`` and so threw away the header and
everything the caller had written before submitting -- these pin the append.

Every job logs in its run's folder, and a dry run submits nothing. Nothing is
submitted here in any case: every job script is kept by
``tests.utils.Submission`` instead of being handed to a scheduler, and the
tests that look at what a job is given stub ``schedule`` itself.
"""

import os
import re
import types

import pytest

import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl
import qx_utilities.general.log.context as glc
import qx_utilities.general.scheduler as gs
from tests.utils import Submission

STAMP = "2026-07-26_12.00.00.000000"

# when a job was submitted, in the name of the file its output goes to
WHEN = r"\d{4}-\d\d-\d\d_\d\d\.\d\d\.\d\d\.\d{6}"

SESSIONS = [{"id": "S01"}, {"id": "S02"}]


@pytest.fixture(autouse=True)
def elsewhere(tmp_path, monkeypatch):
    """Nothing a run decides from the current folder or the home folder lands
    outside the test's own folder."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def submitted(monkeypatch):
    """
    The job scripts handed to sbatch or qsub, kept instead: a test that went
    wrong on a cluster's login node would otherwise submit real jobs.
    """
    return Submission.install(monkeypatch)


@pytest.fixture
def scheduled(monkeypatch):
    """What is handed to `schedule`, kept instead of submitted."""
    calls = []
    monkeypatch.setattr(
        gs,
        "schedule",
        lambda **kwargs: calls.append(kwargs) or ("Submitted batch job 1", "1"),
    )
    return calls


@pytest.fixture
def study(tmp_path):
    """A study that exists, so that a relative log folder is taken from it."""
    (tmp_path / "study" / "sessions").mkdir(parents=True)
    return tmp_path / "study"


def make_run(study, args=None, enabled=True, command="hcp_pre_freesurfer", name=None):
    """A run that names `study`, whose log folder it decides from `args`."""
    return gl.RunContext(
        command,
        dict(args or {}),
        gl.LogSettings(enabled=enabled),
        {"basefolder": str(study), "known": True},
        timestamp=STAMP,
        name=name,
    )


@pytest.fixture
def run(study):
    return make_run(study, {"sessions": "batch.txt"})


def runlog(run):
    with open(run.path) as f:
        return f.read()


def submit(run, sessions=None, given=None):
    """
    Schedule the run's command as gmri does, over `sessions` when there are
    any: a dry run, unless the arguments `given` say otherwise.
    """
    args = {"scheduler": "SLURM,time=1:00:00", "sessions": "batch.txt"}
    args.update({"run": "test"} if given is None else given)
    gs.run_through_scheduler(run.command, sessions=sessions, args=args, run=run)


def filed(output):
    """An output directive, with the moment its job was submitted taken out."""
    return re.sub(WHEN, "<WHEN>", output)


def test_the_submission_is_appended_to_the_runlog_the_run_opened(run):
    run.header()

    submit(run)

    log = runlog(run)
    assert "qunex hcp_pre_freesurfer" in log, "the header was overwritten"
    assert "Running scheduler for command hcp_pre_freesurfer" in log
    assert log.index("qunex hcp_pre_freesurfer") < log.index("Running scheduler")


@pytest.mark.parametrize("mode", ["test", "run"], ids=["dry run", "submitted"])
def test_the_call_that_is_scheduled_is_recorded(run, scheduled, mode):
    run.header()

    submit(run, given={"run": mode})

    log = runlog(run)
    said = "submitting" if mode == "run" else "test, not submitted:"
    assert "---> %s hcp_pre_freesurfer\n" % said in log
    assert "gmri hcp_pre_freesurfer" in log
    assert '--sessions="batch.txt"' in log
    assert len(scheduled) == (1 if mode == "run" else 0)


def test_how_the_sessions_were_divided_is_recorded(run):
    run.header()

    submit(run, sessions=SESSIONS)

    log = runlog(run)
    assert "run the command over 2 sessions" in log
    assert "Job #1 will run sessions: S01" in log
    assert "Job #2 will run sessions: S02" in log


@pytest.mark.parametrize(
    "sessions, settings, names",
    [
        (None, "SLURM,time=1:00:00", ["SLURM_run_recipe_r"]),
        (
            SESSIONS,
            "SLURM,time=1:00:00",
            ["SLURM_run_recipe_r_job00", "SLURM_run_recipe_r_job01"],
        ),
        (SESSIONS, "SLURM,time=1:00:00,array", ["SLURM_run_recipe_r_job%a"]),
    ],
    ids=["one job", "a job per session", "a job array"],
)
def test_job_output_goes_to_batchlogs_under_the_run_name(
    study, scheduled, sessions, settings, names
):
    """A recipe's jobs are filed under the recipe, as its folder is."""
    run = make_run(study, command="run_recipe", name="run_recipe_r")

    gs.run_through_scheduler(
        "run_recipe",
        sessions=sessions,
        args={"scheduler": settings, "run": "run"},
        run=run,
    )

    batchlogs = os.path.join(run.logfolder, "batchlogs")
    assert os.path.isdir(batchlogs)
    assert [filed(job["output"]) for job in scheduled] == [
        filed("both:%s.%s.log|return:both" % (os.path.join(batchlogs, name), STAMP))
        for name in names
    ]


@pytest.mark.parametrize(
    "given", [None, "somewhere/else", "legacy"], ids=["decided", "relative", "legacy"]
)
@pytest.mark.parametrize(
    "sessions", [None, SESSIONS], ids=["one job", "a job per session"]
)
def test_every_job_logs_in_the_run_folder(study, scheduled, sessions, given):
    """
    A job was handed the --logfolder the run was given, as it was typed, or
    none, and so decided a folder of its own: one run, as many log folders as
    it had jobs. A relative one was taken from wherever the job started.
    """
    stated = {"logfolder": given} if given else {}
    run = make_run(study, stated)

    submit(run, sessions, given={"run": "run", **stated})

    assert os.path.isabs(run.logfolder)
    assert len(scheduled) == (len(sessions) if sessions else 1)
    for job in scheduled:
        assert job["command"].count("--logfolder=") == 1
        assert '--logfolder="%s"' % run.logfolder in job["command"]


@pytest.mark.parametrize(
    "given",
    [{"run": "test"}, {"test": True}, {"run": "other"}],
    ids=["run=test", "test=True", "run=other"],
)
@pytest.mark.parametrize(
    "sessions", [None, SESSIONS], ids=["one job", "a job per session"]
)
def test_a_dry_run_submits_nothing_and_makes_no_folder(
    run, scheduled, submitted, sessions, given
):
    """
    `--test` reaches the scheduler as `test=True`, which it did not read: a
    dry run with a scheduler submitted its jobs. A `run` other than `run` is a
    dry run to the commands, and submitted nothing before either.
    """
    submit(run, sessions, given=given)

    assert scheduled == []
    assert submitted == []
    log = runlog(run)
    jobs = (
        ["hcp_pre_freesurfer"]
        if sessions is None
        else ["hcp_pre_freesurfer_#00", "hcp_pre_freesurfer_#01"]
    )
    for job in jobs:
        assert log.count("---> test, not submitted: %s\n" % job) == 1
    assert log.count("\ngmri hcp_pre_freesurfer ") == len(jobs), "and what it runs"
    assert "submitting" not in log
    assert not os.path.exists(os.path.join(run.logfolder, "batchlogs"))


def test_the_pause_between_jobs_is_read_as_seconds(run, scheduled, monkeypatch):
    """
    A `--scheduler_sleep` given on the command line arrives as text, which
    `time.sleep` refused once the first job had been submitted: the jobs
    after it never were.
    """
    slept = []
    monkeypatch.setattr(gs, "time", types.SimpleNamespace(sleep=slept.append))

    submit(run, SESSIONS, given={"run": "run", "scheduler_sleep": "0.5"})

    assert len(scheduled) == 2
    assert slept == [0.5, 0.5]


def test_schedule_keeps_the_job_output_in_the_run_folder(tmp_path, submitted):
    """
    `qunex schedule` left its job's output to the scheduler, which writes it
    in the folder the job starts in.
    """
    logfolder = tmp_path / "logs" / "run"
    mine = tmp_path / "mine.log"

    gs.schedule(command="echo", settings="SLURM,time=1", logfolder=str(logfolder))
    gs.schedule(
        command="echo",
        settings="SLURM,time=1",
        logfolder=str(logfolder),
        output="both:%s" % mine,
    )
    gs.schedule(command="echo", settings="SLURM,time=1")

    batchlogs = logfolder / "batchlogs"
    assert batchlogs.is_dir()
    script = filed(submitted[0].script)
    out = filed(os.path.join(batchlogs, "SLURM_schedule.%s.log" % STAMP))
    assert "#SBATCH -o %s\n" % out in script
    assert "#SBATCH -e %s\n" % out in script

    assert "#SBATCH -o %s\n" % mine in submitted[1].script, "the output it is given"
    assert len(os.listdir(batchlogs)) == 0, "nothing is written there by schedule"

    assert "#SBATCH -o" not in submitted[2].script, "without a run, the scheduler's"


@pytest.mark.parametrize(
    "output, written",
    [
        ("stdout:processing.log", {"o": "processing.log"}),
        (
            "stdout:processing.output.log|stderr:processing.error.log",
            {"o": "processing.output.log", "e": "processing.error.log"},
        ),
        (
            "both:processing.log|return:both",
            {"o": "processing.log", "e": "processing.log"},
        ),
    ],
    ids=["stdout", "stdout and stderr", "both"],
)
def test_the_documented_outputs_are_taken_from_the_current_folder(
    tmp_path, submitted, output, written
):
    """
    A log file named without a folder is in the current one, which the check
    for its folder took to be missing: none of the documented examples could
    be submitted. It is written into the job script absolute.
    """
    gs.schedule(command="echo", settings="SLURM,time=1", output=output)

    for flag, name in written.items():
        assert "#SBATCH -%s %s\n" % (flag, tmp_path / name) in submitted[0].script


@pytest.mark.parametrize("returned", ["both", "stdout", "stderr", "none"])
def test_what_the_submission_answers_is_returned_when_asked(submitted, returned):
    """`return:none`, as documented, ended in an UnboundLocalError."""
    answer = gs.schedule(
        command="echo", settings="SLURM,time=1", output="return:%s" % returned
    )

    assert answer == (
        ("", "NA") if returned == "none" else ("Submitted batch job 1", "1")
    )


@pytest.mark.parametrize(
    "output",
    ["both:x.log|return:true", "stdou:x.log", "both:", "x.log"],
    ids=["an unknown return", "an unknown directive", "no file", "no directive"],
)
def test_an_output_it_can_not_read_is_an_error(submitted, output):
    """
    These ended in an UnboundLocalError or a ValueError, or were dropped
    unread and the job's output left to the scheduler.
    """
    with pytest.raises(ge.CommandError):
        gs.schedule(command="echo", settings="SLURM,time=1", output=output)

    assert submitted == []


def test_a_run_without_a_runlog_still_submits(study, scheduled, capsys):
    run = make_run(study, enabled=False)

    submit(run, given={"run": "run"})

    assert len(scheduled) == 1
    assert "Running scheduler for command" in capsys.readouterr().out
    assert not list(study.rglob("*.log"))


@pytest.mark.parametrize(
    "sessions", [None, SESSIONS], ids=["one job", "a job per session"]
)
@pytest.mark.parametrize("mode", ["test", "run"], ids=["dry run", "submitted"])
def test_the_status_record_says_what_was_submitted_and_no_job_writes_it(
    study, tmp_path, scheduled, monkeypatch, sessions, mode
):
    """
    Every job was handed the run's --logstatus, so the jobs of one step wrote
    the same record and the last to finish overwrote the others, while the
    submission itself wrote none: run_recipe reported a scheduled step from
    whichever job ended last, or from nothing.
    """
    monkeypatch.setattr(glc, "_status_written", False)
    status = tmp_path / "status" / "01_hcp_pre_freesurfer.yaml"
    run = make_run(study, {"logstatus": str(status)})

    submit(run, sessions, given={"run": mode, "logstatus": str(status)})

    for job in scheduled:
        assert "--logstatus" not in job["command"], job["command"]
    record = gl.read_status(str(status))
    assert record is not None, "the submission writes the record"
    ids = [entry["id"] for entry in record["sessions"]]
    assert ids == (["hcp_pre_freesurfer"] if sessions is None else ["S01", "S02"])
    said = "submitted as job 1" if mode == "run" else "test, not submitted"
    assert all(said in entry["summary"] for entry in record["sessions"]), record
    # what the jobs did is for them to say, in their own runlogs
    assert record["failed"] == (None if mode == "run" else 0)
