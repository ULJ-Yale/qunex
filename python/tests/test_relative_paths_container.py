# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for where a relative path is taken from when a run goes through
`qunex_container`: the launcher works on the host and hands the command in the
container absolute paths, binds the folders it is given from where it runs,
and starts the command -- and a scheduled job -- where the launcher was run.

The rest of the hand-on cases -- links, jobs, recipe steps and tools -- are in
tests/test_relative_paths_runs.py.
"""

import os
import re
import shlex
import subprocess
import types
from pathlib import Path

import pytest

import qx_utilities.general.log as gl
import qx_utilities.general.log.context as glc
import qx_utilities.general.log.settings as gls
import qx_utilities.general.scheduler as gs
from tests import utils
from tests.test_relative_paths_runs import write_recipe

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def registry_of_this_tree(monkeypatch):
    """The commands are looked up in this tree's committed registry."""
    monkeypatch.setenv("QUNEXPATH", str(REPO_ROOT))


@pytest.fixture(autouse=True)
def no_user_settings(tmp_path, monkeypatch):
    """
    The user's own settings file must not decide what these tests see, and a
    run outside a study must not log in the home folder of whoever runs them.
    """
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setattr(
        gls, "USER_SETTINGS_PATHS", [str(tmp_path / "user" / "qunex_settings.yaml")]
    )


@pytest.fixture(autouse=True)
def default_settings():
    """`run_recipe` sets the process-wide settings; put them back after."""
    yield
    gl.set_active(None)


@pytest.fixture(autouse=True)
def one_run_per_test(monkeypatch):
    """Each test is a run of its own, which has written no status yet."""
    monkeypatch.setattr(glc, "_status_written", False)


@pytest.fixture(scope="module")
def gmri():
    return utils.load_gmri("gmri_relative_paths_container")


@pytest.fixture
def layout(tmp_path, monkeypatch):
    """
    A study with one session, and a folder beside it the runs are started
    from. Returns (study, elsewhere), the current folder being `elsewhere`.
    """
    study, elsewhere = utils.layout(tmp_path)
    monkeypatch.chdir(elsewhere)
    return study, elsewhere


@pytest.fixture
def scheduled(monkeypatch):
    """What `run_through_scheduler` hands `schedule`, kept instead of submitted."""
    calls = []
    monkeypatch.setattr(gs, "schedule", lambda **kw: calls.append(kw) or ("", "1"))
    return calls


def run_container(monkeypatch, *args):
    """
    Runs the container launcher with the container never started. Returns
    the commands it would have run, and the job script each one runs inside.
    """
    qc = utils.load_container()
    ran = []
    view = types.SimpleNamespace(**vars(subprocess))
    view.run = lambda command, **kwargs: ran.append(command)
    monkeypatch.setattr(qc, "subprocess", view)
    qc.main(list(args))
    return ran, [Path(shlex.split(command)[-1]).read_text() for command in ran]


def test_the_container_hands_the_command_absolute_paths(layout, monkeypatch):
    """
    The command in the container starts where the launcher was run, and is
    handed what the command line names absolute; the launcher's own options
    are taken from where it runs, as a scheduled job may start anywhere.
    """
    study, _ = layout
    monkeypatch.chdir(study.parent)

    ran, (script,) = run_container(
        monkeypatch,
        "hcp_pre_freesurfer",
        "--studyfolder=study",
        "--batchfile=processing/batch.txt",
        "--logfolder=logs/mine",
        "--container=x.sif",
        "--cuda_path=cuda",
    )

    command, path = ran[0].split(" bash ")
    assert str(study.parent / "x.sif") in command, "the image, from where it is run"
    assert "%s:/usr/local/cuda" % (study.parent / "cuda") in command, "bound absolute"
    assert path.startswith(str(study / "logs" / "mine" / "batchlogs") + os.sep)
    assert "\ncd %s " % study.parent in script, "the run starts where it was started"
    assert '--studyfolder="%s"' % study in script
    assert '--batchfile="%s"' % (study / "processing" / "batch.txt") in script
    assert re.findall(r'--logfolder="([^"]*)"', script) == [
        str(study / "logs" / "mine")
    ], "the run's folder, decided on the host and handed once"


def test_the_container_reads_a_relative_recipe_file_from_the_command_line_study(
    layout, monkeypatch
):
    """
    As QuNex reads it: from the study the command line names. The launcher
    read it from where it runs, and so placed the run without it.
    """
    study, _ = layout
    (study / "recipes").mkdir()
    write_recipe(
        study / "recipes" / "r.yaml", {"logfolder": "rlogs"}, ["list_sessions"]
    )
    monkeypatch.chdir(study.parent)

    _, (script,) = run_container(
        monkeypatch,
        "run_recipe",
        "--studyfolder=study",
        "--recipe_file=recipes/r.yaml",
        "--recipe=r",
        "--container=x.sif",
    )

    assert '--recipe_file="%s"' % (study / "recipes" / "r.yaml") in script
    assert re.findall(r'--logfolder="([^"]*)"', script) == [str(study / "rlogs")]
    assert not (study.parent / "rlogs").exists()


def test_the_container_finds_run_recipe_s_files_in_the_study_its_recipe_names(
    layout, monkeypatch, capsys
):
    """
    As QuNex finds them when the command line names no study: the batch file
    of the call, and the sessions its glob matches, in the study the recipe
    names. The launcher could not read the batch file at all, and matched no
    session, so a scheduled run was one job rather than one a session.
    """
    study, elsewhere = layout
    (study / "sessions" / "S02").mkdir()
    write_recipe(elsewhere / "r.yaml", {"studyfolder": "../study"}, ["list_sessions"])

    _, (script,) = run_container(
        monkeypatch,
        "run_recipe",
        "--recipe_file=r.yaml",
        "--recipe=r",
        "--batchfile=processing/batch.txt",
        "--container=x.sif",
    )

    assert '--batchfile="%s"' % (study / "processing" / "batch.txt") in script
    assert '--recipe_file="%s"' % (elsewhere / "r.yaml") in script
    assert '--sessions="S01"' in script
    (folder,) = (study / "logs").iterdir()
    assert folder.name.endswith("_run_recipe_r")

    utils.load_container().main(
        [
            "run_recipe",
            "--recipe_file=r.yaml",
            "--recipe=r",
            "--sessions=S0*",
            "--container=x.sif",
            "--parinfo",
            "--scheduler=SLURM,time=1:00:00",
        ]
    )
    out = capsys.readouterr().out
    assert "Job #1 will run sessions: S01" in out
    assert "Job #2 will run sessions: S02" in out


def test_the_container_takes_a_sessions_folder_named_alone_from_the_recipe_study(
    layout, monkeypatch
):
    """As QuNex takes it, and hands it to the container absolute."""
    study, _ = layout
    monkeypatch.chdir(study.parent)
    write_recipe(study.parent / "r.yaml", {"studyfolder": "study"}, ["list_sessions"])

    _, (script,) = run_container(
        monkeypatch,
        "run_recipe",
        "--recipe_file=r.yaml",
        "--recipe=r",
        "--sessionsfolder=sessions",
        "--sessions=S0*",
        "--container=x.sif",
    )

    assert '--sessionsfolder="%s"' % (study / "sessions") in script
    assert '--sessions="S01"' in script, "the glob, matched in the study's sessions"


def test_a_batch_file_given_as_the_sessions_is_found_as_a_batch_file_is(
    layout, monkeypatch
):
    """The legacy `--sessions=<batch file>`, taken from the command line's study."""
    study, _ = layout
    monkeypatch.chdir(study.parent)

    _, (script,) = run_container(
        monkeypatch,
        "hcp_pre_freesurfer",
        "--studyfolder=study",
        "--sessions=processing/batch.txt",
        "--container=x.sif",
    )

    assert '--batchfile="%s"' % (study / "processing" / "batch.txt") in script
    assert '--sessions="S01"' in script


def test_a_deprecated_sessions_folder_is_where_the_container_finds_the_batch_file(
    layout, monkeypatch
):
    """`--subjectsfolder` is read as `--sessionsfolder`, as QuNex reads it."""
    study, _ = layout
    monkeypatch.chdir(study.parent)

    _, (script,) = run_container(
        monkeypatch,
        "hcp_pre_freesurfer",
        "--subjectsfolder=study/sessions",
        "--batchfile=processing/batch.txt",
        "--container=x.sif",
    )

    assert '--batchfile="%s"' % (study / "processing" / "batch.txt") in script
    assert '--subjectsfolder="study/sessions"' in script, (
        "handed on as it was given: QuNex reads it from the same folder"
    )


@pytest.mark.parametrize("container", ["x.sif", "qunex/qunex_suite:1"])
def test_what_the_container_makes_absolute_is_quoted_where_a_shell_reads_it(
    tmp_path, monkeypatch, container
):
    """
    The image, the CUDA folder and the job script were written into the
    command as they were typed, relative; absolute, they carry the folder the
    launcher runs in, and a space in it split them.
    """
    start = tmp_path / "my data"
    (start / "study" / "sessions").mkdir(parents=True)
    (start / "job.sh").write_text("echo hello\n")
    monkeypatch.chdir(start)

    ran, (script,) = run_container(
        monkeypatch,
        "--script=job.sh",
        "--studyfolder=study",
        "--container=%s" % container,
        "--cuda_path=cuda",
    )

    words = shlex.split(ran[0])
    job = words[-1]
    assert job.startswith(str(start / "study" / "logs") + os.sep)
    if container == "x.sif":
        assert words[words.index("bash") - 1] == str(start / "x.sif")
        assert words[words.index("--bind") + 1].endswith(
            ",%s:/usr/local/cuda/" % (start / "cuda")
        )
        assert "\nbash %s\n" % shlex.quote(str(start / "job.sh")) in script
    else:
        assert "%s:/usr/local/cuda" % (start / "cuda") in words
        assert script.endswith("\necho hello\n"), "the script's text, run as it is"


@pytest.mark.parametrize("container", ["x.sif", "qunex/qunex_suite:1"])
def test_the_folders_the_container_binds_are_taken_from_where_it_runs(
    tmp_path, monkeypatch, container
):
    """
    As the launcher's other options are: they were handed on as typed, and a
    PBS or GridEngine job, which starts in the home folder, bound another
    folder than the one named. For Docker a bare name is a volume, not a
    folder.
    """
    start, home = tmp_path / "start", str(tmp_path / "home")
    (start / "study" / "sessions").mkdir(parents=True)
    monkeypatch.chdir(start)

    ran, _ = run_container(
        monkeypatch,
        "hcp_pre_freesurfer",
        "--studyfolder=study",
        "--container=%s" % container,
        "--bind=data:/data,./more:/more:ro,/abs:/abs,vol:/vol,~/h:/h",
    )

    words = shlex.split(ran[0])
    if container == "x.sif":
        assert words[words.index("--bind") + 1] == ",".join(
            [
                home,
                "%s/data:/data" % start,
                "%s/more:/more:ro" % start,
                "/abs:/abs",
                "%s/vol:/vol" % start,
                "%s/h:/h" % home,
            ]
        )
    else:
        assert [words[n + 1] for n, word in enumerate(words) if word == "-v"] == [
            "%s:%s" % (home, home),
            "data:/data",
            "%s/more:/more:ro" % start,
            "/abs:/abs",
            "vol:/vol",
            "%s/h:/h" % home,
        ]


@pytest.mark.parametrize(
    "name", ["my data", 'it"s $HOME'], ids=["a space", "a quote and a dollar"]
)
def test_the_command_in_the_container_starts_where_the_launcher_was_run(
    tmp_path, monkeypatch, name
):
    """
    Docker starts a command in a folder of its own, and a PBS or GridEngine
    job in the home folder. The command changes into the folder the launcher
    was run from, and says so when the container can not see it.
    """
    start, elsewhere = tmp_path / name, tmp_path / "elsewhere"
    start.mkdir()
    elsewhere.mkdir()
    monkeypatch.chdir(start)

    _, (script,) = run_container(
        monkeypatch,
        "hcp_pre_freesurfer",
        "--studyfolder=%s" % (tmp_path / "study"),
        "--container=x.sif",
    )
    (cd,) = [line for line in script.splitlines() if line.startswith("cd ")]

    def run_job():
        """The folder change as the job runs it, starting elsewhere."""
        return subprocess.run(
            ["bash", "-c", cd + "\npwd"], cwd=elsewhere, capture_output=True, text=True
        )

    job = run_job()
    assert job.stdout.strip() == str(start), job.stderr

    monkeypatch.chdir(tmp_path)
    start.rmdir()
    job = run_job()
    assert job.stdout.strip() == str(elsewhere), "the job still runs"
    assert job.stderr.strip() == (
        "WARNING: %s is not visible in the container, relative paths are taken "
        "from %s" % (start, elsewhere)
    )


@pytest.mark.parametrize("scheduler", ["PBS,walltime=1:00:00", "SLURM,time=1:00:00"])
def test_a_scheduled_container_job_starts_where_the_launcher_was_run(
    tmp_path, monkeypatch, scheduler
):
    """
    A PBS or GridEngine job starts in the home folder, and the container was
    started from there, so Apptainer bound the home folder instead of the
    launch folder and the command in it could not change into that one. gmri's
    own scheduled jobs always start where the run was started.
    """
    start = tmp_path / "start"
    start.mkdir()
    monkeypatch.chdir(start)
    qc = utils.load_container()
    submitted = []

    class Submission:
        """`sbatch` or `qsub`, keeping the job script piped to it."""

        def __init__(self, program, **kwargs):
            self.stdin, self.script = self, ""
            submitted.append(self)

        def write(self, data):
            self.script += data.decode()

        def close(self):
            pass

    view = types.SimpleNamespace(**vars(subprocess))
    view.run = lambda command, **kwargs: None
    view.Popen = Submission
    monkeypatch.setattr(qc, "subprocess", view)
    monkeypatch.setattr(qc, "time", types.SimpleNamespace(sleep=lambda s: None))
    qc.main(
        [
            "hcp_pre_freesurfer",
            "--studyfolder=%s" % (tmp_path / "study"),
            "--container=x.sif",
            "--scheduler=%s" % scheduler,
        ]
    )

    (job,) = [submission.script for submission in submitted]
    lines = job.splitlines()
    (cd,) = [n for n, line in enumerate(lines) if line.startswith("cd ")]
    (exec_,) = [n for n, line in enumerate(lines) if " exec " in line]
    assert lines[cd].startswith("cd %s " % shlex.quote(str(start))), job
    assert cd < exec_, "the container is started from the launch folder"
