# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for where a relative path is taken from once a run hands it on: to a
link it makes, a job it submits, a recipe step or a tool it starts, or the
command `qunex_container` runs in a container. Each of them reads a relative
path from a folder of its own, so the run has to make the path absolute before
it hands it on.

Only entering the study changes the current folder: `gmri` enters it, through
`general/placement.py`, and returns to where it was started however the run
ends. Anything else that changed folder would move every relative path of the
run under it.
"""

import ast
import os
import re
import shlex
import subprocess
from pathlib import Path

import pytest
import yaml

import qx_utilities.general.core as gc
import qx_utilities.general.log as gl
import qx_utilities.general.log.context as glc
import qx_utilities.general.log.settings as gls
import qx_utilities.general.recipe as gr
import qx_utilities.general.scheduler as gs
from tests import utils
from tests.utils import Submission, write_script

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
    return utils.load_gmri("gmri_relative_paths_runs")


@pytest.fixture
def layout(tmp_path, monkeypatch):
    """
    A study with one session, and a folder beside it the runs are started
    from. Returns (study, elsewhere), the current folder being `elsewhere`.
    """
    study, elsewhere = utils.layout(tmp_path)
    monkeypatch.chdir(elsewhere)
    return study, elsewhere


# ----------------------------------------------------------- link_or_copy


def test_a_relative_source_is_linked_where_it_was_found(tmp_path, monkeypatch):
    (tmp_path / "src" / "avg").mkdir(parents=True)
    (tmp_path / "study" / "grp").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    assert gc.link_or_copy("src/avg", "study/grp/avg", symlink=True)
    assert os.path.exists("study/grp/avg"), "the link resolves"
    assert os.path.samefile("study/grp/avg", "src/avg")
    assert os.path.isabs(os.readlink("study/grp/avg")), (
        "a relative link is read from its own folder"
    )


@pytest.mark.parametrize("symlink", [False, True], ids=["hard link", "symbolic link"])
def test_a_link_left_dangling_at_the_target_is_replaced(tmp_path, monkeypatch, symlink):
    """
    Earlier versions left a link to a relative source dangling. Taken for no
    target at all, it could not be linked over, and was then copied onto --
    through the link, to wherever it pointed.
    """
    (tmp_path / "elsewhere").mkdir()
    (tmp_path / "source.txt").write_text("source\n")
    os.symlink("elsewhere/stray.txt", tmp_path / "target.txt")
    monkeypatch.chdir(tmp_path)

    assert gc.link_or_copy("source.txt", "target.txt", symlink=symlink)
    assert os.path.samefile("target.txt", "source.txt")
    assert not (tmp_path / "elsewhere" / "stray.txt").exists(), (
        "nothing written through the stale link"
    )


# --------------------------------------------------------------- scheduler


@pytest.fixture
def scheduled(monkeypatch):
    """What `run_through_scheduler` hands `schedule`, kept instead of submitted."""
    calls = []
    monkeypatch.setattr(gs, "schedule", lambda **kw: calls.append(kw) or ("", "1"))
    return calls


def test_a_job_starts_in_the_folder_its_run_was_started_from(
    tmp_path, monkeypatch, scheduled
):
    """
    Not in the folder it is submitted from, which is the study once the run
    has entered it: the job settles its study from where the run did.
    """
    started, study = tmp_path / "started", tmp_path / "study"
    started.mkdir()
    (study / "sessions").mkdir(parents=True)
    monkeypatch.chdir(study)
    run = gl.RunContext(
        "hcp_pre_freesurfer",
        {},
        gl.LogSettings(),
        {"basefolder": str(study), "known": True},
        startfolder=str(started),
    )

    for workdir in (None, "work"):
        args = {"scheduler": "PBS,walltime=1:00:00"}
        if workdir:
            args["scheduler_workdir"] = workdir
        gs.run_through_scheduler("hcp_pre_freesurfer", args=args, run=run)

    assert scheduled[0]["workdir"] == str(started)
    assert scheduled[1]["workdir"] == "work", "the folder it is told to start in"


def test_a_scheduled_job_starts_where_the_run_was_started(gmri, layout, monkeypatch):
    """
    Through `gmri`, which has entered the study the batch file header names by
    the time it submits the job. The job reads the header's relative study
    from where this run read it, and is handed every folder absolute.
    """
    study, elsewhere = layout
    (elsewhere / "batch.txt").write_text(
        "_studyfolder: ../study\n---\nid: S01\nsubject: S01\n01: T1w\n"
    )
    submitted = Submission.install(monkeypatch)

    gmri.runCommand(
        "hcp_pre_freesurfer",
        {"batchfile": "batch.txt", "scheduler": "PBS,walltime=1:00:00"},
    )

    (logfolder,) = (study / "logs").iterdir()
    script = submitted[0].script
    assert "\ncd %s ||" % shlex.quote(str(elsewhere)) in script, (
        "PBS starts a job in the home folder; the job has to read the header's "
        "relative study from where this run read it"
    )
    assert '--batchfile="%s"' % (elsewhere / "batch.txt") in script
    assert '--studyfolder="%s"' % study in script
    assert '--sessionsfolder="%s"' % (study / "sessions") in script
    assert re.findall(r'--logfolder="([^"]*)"', script) == [str(logfolder)], (
        "the run's folder, handed once"
    )
    assert os.getcwd() == str(elsewhere)


@pytest.mark.parametrize(
    "command, extra",
    [
        ("hcp_pre_freesurfer", {}),
        ("run_shell_script", {"script": "s.sh"}),
    ],
    ids=["processing", "utility"],
)
def test_a_job_started_elsewhere_works_in_the_study_the_header_names(
    gmri, layout, monkeypatch, command, extra
):
    """
    A job started in `--scheduler_workdir` reads the batch file header again
    there, and would take its relative study from that folder: it is handed
    the study and the sessions folder the run settled, absolute.
    """
    study, elsewhere = layout
    (study / "work").mkdir()
    (elsewhere / "batch.txt").write_text(
        "_studyfolder: ../study\n---\nid: S01\nsubject: S01\n01: T1w\n"
    )
    submitted = Submission.install(monkeypatch)

    gmri.runCommand(
        command,
        {
            "batchfile": "batch.txt",
            "scheduler": "SLURM,time=1",
            "scheduler_workdir": "work",
            **extra,
        },
    )

    (script,) = [job.script for job in submitted]
    assert "\ncd %s ||" % shlex.quote(str(study / "work")) in script
    assert '--studyfolder="%s"' % study in script
    assert '--sessionsfolder="%s"' % (study / "sessions") in script


def test_a_job_of_a_run_that_names_no_study_is_handed_none(
    gmri, layout, monkeypatch
):
    """
    A run that names neither folder works in the current folder, as each of
    its jobs does: the study found from the marker is not handed on.
    """
    study, _ = layout
    monkeypatch.chdir(study / "sessions")
    submitted = Submission.install(monkeypatch)

    gmri.runCommand(
        "hcp_pre_freesurfer",
        {"batchfile": "../processing/batch.txt", "scheduler": "SLURM,time=1"},
    )

    (script,) = [job.script for job in submitted]
    assert "--studyfolder" not in script
    assert "--sessionsfolder" not in script


def test_a_job_submitted_without_a_run_starts_where_it_is_submitted(
    tmp_path, monkeypatch, scheduled
):
    monkeypatch.chdir(tmp_path)

    gs.run_through_scheduler(
        "hcp_pre_freesurfer", args={"scheduler": "PBS,walltime=1:00:00"}, run=None
    )

    assert scheduled[0]["workdir"] == str(tmp_path)


def test_a_relative_working_folder_is_made_absolute_when_the_job_is_submitted(
    tmp_path, monkeypatch
):
    """PBS and GridEngine start a job in the home folder, not where it was
    submitted from."""
    submitted = Submission.install(monkeypatch)
    (tmp_path / "work").mkdir()
    monkeypatch.chdir(tmp_path)

    gs.schedule(command="echo", settings="SLURM,time=1", workdir="work")

    assert "\ncd %s ||" % shlex.quote(str(tmp_path / "work")) in submitted[0].script


@pytest.mark.parametrize(
    "name", ["my work", 'it"s $HOME'], ids=["a space", "a quote and a dollar"]
)
def test_a_working_folder_with_a_space_is_quoted_in_the_job_script(
    tmp_path, monkeypatch, name
):
    """
    The folder was written into the job script as it was: a space split it,
    and the job did not start in it. The warning a job gives when it can not
    change into the folder names it too, so it is quoted there as well: a
    lone `"` in the name would have left the whole script unreadable.
    """
    submitted = Submission.install(monkeypatch)
    work, elsewhere = tmp_path / name, tmp_path / "elsewhere"
    work.mkdir()
    elsewhere.mkdir()

    gs.schedule(command="pwd", settings="SLURM,time=1", workdir=str(work))

    def run_job():
        """Run the job script as the node would, starting elsewhere."""
        return subprocess.run(
            ["bash", "-c", submitted[0].script],
            cwd=elsewhere,
            capture_output=True,
            text=True,
        )

    job = run_job()
    assert job.stdout.strip() == str(work), job.stderr

    work.rmdir()
    job = run_job()
    assert job.stdout.strip() == str(elsewhere), "the job still runs"
    assert (
        "WARNING: could not change into %s, relative paths are taken from %s"
        % (work, elsewhere)
        in job.stderr.splitlines()
    )


# ------------------------------------------------------------------ recipe


def write_recipe(path, global_parameters, commands, parameters=None):
    """A recipe file holding the one recipe, `r`."""
    recipe = {"commands": commands}
    if parameters is not None:
        recipe["parameters"] = parameters
    path.write_text(
        yaml.safe_dump(
            {"global_parameters": global_parameters, "recipes": {"r": recipe}}
        )
    )
    return str(path)


def test_an_external_step_is_found_in_and_run_from_the_recipe_study(
    tmp_path, monkeypatch
):
    study = tmp_path / "study"
    (study / "sessions").mkdir(parents=True)
    (study / "scripts").mkdir()
    (study / ".qunexstudy").write_text("")
    write_script(study / "scripts" / "where.sh", "#!/bin/bash\npwd > where.txt\n")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    recipe = write_recipe(
        tmp_path / "recipe.yaml",
        {"studyfolder": "../study"},
        [{"external": {"path": "scripts/where.sh"}}],
    )

    gr.run_recipe(recipe_file=recipe, recipe="r")

    assert (study / "where.txt").read_text().strip() == str(study)
    assert not (elsewhere / "where.txt").exists()
    assert os.getcwd() == str(elsewhere), "run_recipe itself does not move"


@pytest.mark.parametrize(
    "logfolder", [True, False], ids=["logs outside it", "logs in the study to be"]
)
def test_an_external_step_whose_study_is_not_there_yet_runs_where_the_recipe_runs(
    tmp_path, monkeypatch, capsys, logfolder
):
    """
    A step that runs before the study exists is found and run where the recipe
    was started. Without a `logfolder` of its own the recipe logs in that
    study, and makes its log folder before the first step: a folder holding
    nothing but those logs is still a study that does not exist yet.
    """
    elsewhere = tmp_path / "elsewhere"
    (elsewhere / "scripts").mkdir(parents=True)
    write_script(elsewhere / "scripts" / "where.sh", "#!/bin/bash\npwd > where.txt\n")
    monkeypatch.chdir(elsewhere)

    stated = {"studyfolder": "../new"}
    if logfolder:
        stated["logfolder"] = str(tmp_path / "logs")
    recipe = write_recipe(
        tmp_path / "recipe.yaml", stated, [{"external": {"path": "scripts/where.sh"}}]
    )

    gr.run_recipe(recipe_file=recipe, recipe="r")

    assert (elsewhere / "where.txt").read_text().strip() == str(elsewhere), (
        "a step before the study exists is found and run where the recipe runs"
    )
    if not logfolder:
        assert os.listdir(tmp_path / "new") == ["logs"], "the recipe's logs were in it"
    out = capsys.readouterr().out
    assert "does not exist yet" in out
    assert "external scripts/where.sh ... OK" in out, "reported as written"


def test_an_external_step_after_the_one_that_makes_the_study_runs_in_it(
    tmp_path, monkeypatch, capsys
):
    """Where a step runs is asked when the step is reached."""
    elsewhere = tmp_path / "elsewhere"
    (elsewhere / "scripts").mkdir(parents=True)
    write_script(
        elsewhere / "scripts" / "make.sh",
        "#!/bin/bash\nmkdir -p ../new/sessions ../new/scripts\n"
        "cp scripts/where.sh ../new/scripts/\n",
    )
    write_script(elsewhere / "scripts" / "where.sh", "#!/bin/bash\npwd > where.txt\n")
    monkeypatch.chdir(elsewhere)

    recipe = write_recipe(
        tmp_path / "recipe.yaml",
        {"studyfolder": "../new"},
        [
            {"external": {"path": "scripts/make.sh"}},
            {"external": {"path": "scripts/where.sh"}},
        ],
    )

    gr.run_recipe(recipe_file=recipe, recipe="r")

    assert (tmp_path / "new" / "where.txt").read_text().strip() == str(tmp_path / "new")
    assert not (elsewhere / "where.txt").exists()
    assert capsys.readouterr().out.count("does not exist yet") == 1, (
        "the first step only"
    )


def test_an_external_step_is_typed_by_its_own_extension(tmp_path, monkeypatch):
    """A dot in a folder name made a script without an extension unsupported."""
    study = tmp_path / "my.study"
    (study / "scripts").mkdir(parents=True)
    write_script(study / "scripts" / "where", "#!/bin/bash\npwd > where.txt\n")
    monkeypatch.chdir(tmp_path)

    recipe = write_recipe(
        tmp_path / "recipe.yaml",
        {"studyfolder": "my.study"},
        [{"external": {"path": "scripts/where"}}],
    )

    gr.run_recipe(recipe_file=recipe, recipe="r")

    assert (study / "where.txt").read_text().strip() == str(study)


@pytest.mark.parametrize("absolute", [False, True], ids=["as written", "absolute"])
def test_a_step_takes_its_paths_from_the_study_it_is_handed(
    tmp_path, monkeypatch, absolute
):
    """
    The batch file a recipe states for every step is relative, and the one
    its `create_batch` step writes is written as the recipe's, or absolute in
    the study. Either way they are the same file, the relative one being taken
    from the study, as each step takes it.
    """
    study = tmp_path / "study"
    (study / "sessions").mkdir(parents=True)
    (study / ".qunexstudy").write_text("")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    calls = tmp_path / "calls.txt"
    bin_folder = tmp_path / "bin"
    bin_folder.mkdir()
    write_script(bin_folder / "gmri", '#!/bin/bash\necho "$(pwd) $@" >> %s\n' % calls)
    monkeypatch.setenv("PATH", "%s:%s" % (bin_folder, os.environ["PATH"]))

    target = (
        str(study / "processing" / "batch.txt") if absolute else "processing/batch.txt"
    )
    recipe = write_recipe(
        tmp_path / "recipe.yaml",
        {"studyfolder": "../study", "batchfile": "processing/batch.txt"},
        [{"create_batch": {"targetfile": target}}, "list_sessions"],
    )

    gr.run_recipe(recipe_file=recipe, recipe="r")

    lines = calls.read_text().splitlines()
    assert lines[0].startswith(str(elsewhere) + " "), (
        "a step starts where the recipe runs"
    )
    assert "--studyfolder=../study" in lines[0], "and settles its study from there"
    assert "--batchfile" not in lines[0], (
        "the batch file the first step writes is recognised as the run's own, "
        "both taken from the study"
    )
    assert "--batchfile=processing/batch.txt" in lines[1]


def test_run_recipe_finds_its_sessions_in_the_study_the_recipe_names(
    gmri, layout, monkeypatch, capsys
):
    """
    Through `gmri`, which reads the recipe file once, from the current folder
    when the command line names no study, and matches the call's sessions in
    the sessions folder of the study the recipe names. A recipe file read
    from the current folder is where it should be, and is not warned about.
    """
    study, elsewhere = layout
    (study / "sessions" / "S02").mkdir()
    write_recipe(elsewhere / "r.yaml", {"studyfolder": "../study"}, ["list_sessions"])
    issued, where = [], []

    def run_in_parallel(calls, cores=None, prepend="", run=None):
        issued.extend(calls)
        where.append(os.getcwd())
        return [gmri.gc.CallOutcome(call["name"], 0, None, None) for call in calls]

    monkeypatch.setattr(gmri.gc, "run_in_parallel", run_in_parallel)

    gmri.runCommand(
        "run_recipe", {"recipe_file": "r.yaml", "recipe": "r", "sessions": "S0*"}
    )

    assert [call["args"]["eargs"]["sessions"] for call in issued] == ["S01", "S02"], (
        "the glob is matched in the sessions folder of the study the recipe names"
    )
    assert issued[0]["args"]["recipe_file"] == str(elsewhere / "r.yaml")
    (logfolder,) = (study / "logs").iterdir()
    assert logfolder.name.endswith("_run_recipe_r")
    assert {call["args"]["logfolder"] for call in issued} == {str(logfolder)}
    assert where == [str(elsewhere)], "run_recipe works where it is started"
    assert os.getcwd() == str(elsewhere)
    assert "WARNING: Relative paths" not in capsys.readouterr().err


def test_a_relative_batch_file_is_found_in_the_study_the_recipe_names(
    gmri, layout, monkeypatch, capsys
):
    """
    The recipe file is read first -- from the current folder, the command
    line naming no study -- and the batch file of the call is then taken from
    the study the recipe names, as its steps take it.
    """
    study, elsewhere = layout
    write_recipe(elsewhere / "r.yaml", {"studyfolder": "../study"}, ["list_sessions"])
    issued = []

    def run_in_parallel(calls, cores=None, prepend="", run=None):
        issued.extend(calls)
        return [gmri.gc.CallOutcome(call["name"], 0, None, None) for call in calls]

    monkeypatch.setattr(gmri.gc, "run_in_parallel", run_in_parallel)

    gmri.runCommand(
        "run_recipe",
        {"recipe_file": "r.yaml", "recipe": "r", "batchfile": "processing/batch.txt"},
    )

    assert [call["args"]["eargs"]["sessions"] for call in issued] == ["S01"]
    assert issued[0]["args"]["eargs"]["batchfile"] == str(
        study / "processing" / "batch.txt"
    )
    assert "WARNING: Relative paths" not in capsys.readouterr().err


def test_an_empty_study_on_the_command_line_leaves_the_one_the_recipe_names(
    gmri, layout, monkeypatch
):
    """
    A variable that expanded to nothing names no study: the call's sessions
    are matched in the sessions folder of the study the recipe names, as its
    batch file and its log folder are found there.
    """
    study, elsewhere = layout
    (study / "sessions" / "S02").mkdir()
    write_recipe(elsewhere / "r.yaml", {"studyfolder": "../study"}, ["list_sessions"])
    issued = []

    def run_in_parallel(calls, cores=None, prepend="", run=None):
        issued.extend(calls)
        return [gmri.gc.CallOutcome(call["name"], 0, None, None) for call in calls]

    monkeypatch.setattr(gmri.gc, "run_in_parallel", run_in_parallel)

    gmri.runCommand(
        "run_recipe",
        {"recipe_file": "r.yaml", "recipe": "r", "studyfolder": "", "sessions": "S0*"},
    )

    assert [call["args"]["eargs"]["sessions"] for call in issued] == ["S01", "S02"]
    (logfolder,) = (study / "logs").iterdir()
    assert {call["args"]["logfolder"] for call in issued} == {str(logfolder)}


def test_a_sessions_folder_named_alone_is_taken_from_the_study_the_recipe_names(
    gmri, layout, monkeypatch
):
    """
    A sessions folder named on the command line together with a study the
    recipe names is taken from that study, as one named together with a study
    in a batch file header is: the step works on the sessions of the study it
    works in, and no sessions folder is made beside the study.
    """
    study, _ = layout
    (study / "sessions" / "S02").mkdir()
    monkeypatch.chdir(study.parent)
    write_recipe(study.parent / "r.yaml", {"studyfolder": "study"}, ["list_sessions"])
    issued = []

    def run_in_parallel(calls, cores=None, prepend="", run=None):
        issued.extend(calls)
        return [gmri.gc.CallOutcome(call["name"], 0, None, None) for call in calls]

    monkeypatch.setattr(gmri.gc, "run_in_parallel", run_in_parallel)

    gmri.runCommand(
        "run_recipe",
        {
            "recipe_file": "r.yaml",
            "recipe": "r",
            "sessionsfolder": "sessions",
            "sessions": "S0*",
        },
    )

    assert [call["args"]["eargs"]["sessions"] for call in issued] == ["S01", "S02"], (
        "the glob is matched in the sessions folder of the study the recipe names"
    )
    assert {call["args"]["eargs"]["sessionsfolder"] for call in issued} == {
        str(study / "sessions")
    }
    assert not (study.parent / "sessions").exists()


def test_a_recipe_that_unsets_its_study_names_none(tmp_path):
    recipe = write_recipe(
        tmp_path / "r.yaml",
        {"studyfolder": "/s"},
        [],
        parameters={"-studyfolder": None},
    )

    assert gr.recipe_folders(recipe, "r") == {}


def test_the_study_a_step_works_in_follows_the_step_precedence():
    step = {"create_batch": {"studyfolder": "/t", "targetfile": "b.txt"}}

    assert gr._produced_path(step, "targetfile", {}, {}, {"studyfolder": "/s"}) == (
        "/t/b.txt"
    ), "the step's own study over the recipe's"
    assert (
        gr._produced_path(
            step, "targetfile", {}, {}, {"studyfolder": "/s"}, {"studyfolder": "/c"}
        )
        == "/c/b.txt"
    ), "the command line's over the step's own"

    plain = {"create_batch": {"targetfile": "processing/batch.txt"}}
    assert gr._produced_path(plain, "targetfile", {}, {}, {"studyfolder": "/s"}) == (
        "/s/processing/batch.txt"
    )

    renamed = {"create_batch": {"subjectsfolder": "/u/sessions", "targetfile": "b.txt"}}
    assert gr._produced_path(renamed, "targetfile", {}, {}, {"studyfolder": "/s"}) == (
        "/s/b.txt"
    ), "a study named anywhere wins over the folder a sessions folder is in"
    assert gr._produced_path(renamed, "targetfile", {}, {}, {}) == "/u/b.txt", (
        "a deprecated name counts as the one it has now, as the step's gmri reads it"
    )


# ------------------------------------------------------------------- tools


def test_the_gradient_coefficients_found_are_handed_on_absolute(tmp_path, monkeypatch):
    """
    The HCP scripts take a relative coefficients file from the folder they
    run in, which is not the HCP configuration folder a bare name may have
    been found in.
    """
    import qx_utilities.hcp.hcp_utils as hu

    config = tmp_path / "config"
    config.mkdir()
    (config / "coeffs.grad").write_text("")
    (tmp_path / "local.grad").write_text("")
    monkeypatch.chdir(tmp_path)
    log = gl.ReportLog()

    found, run = hu.check_gdc_coeff_file(
        "coeffs.grad", {"hcp_Config": str(config)}, {}, log
    )
    assert (found, run) == (str(config / "coeffs.grad"), True)

    found, _ = hu.check_gdc_coeff_file("coeffs.grad", {"hcp_Config": "config"}, {}, log)
    assert found == str(config / "coeffs.grad"), "whatever the folder it was found in"

    found, run = hu.check_gdc_coeff_file(
        "local.grad", {"hcp_Config": str(config)}, {}, log
    )
    assert (found, run) == (str(tmp_path / "local.grad"), True)

    picked = "default:coeffs.grad|institution:Yale:local.grad"
    found, _ = hu.check_gdc_coeff_file(
        picked, {"hcp_Config": str(config)}, {"institution": "Yale"}, log
    )
    assert found == str(tmp_path / "local.grad"), "and so is one picked for the session"

    found, run = hu.check_gdc_coeff_file("NONE", {"hcp_Config": str(config)}, {}, log)
    assert (found, run) == ("NONE", True)


def test_the_fc_path_written_into_a_qc_scene_is_absolute(tmp_path, monkeypatch):
    """Workbench reads a relative path in a scene from the scene's own folder."""
    from concurrent.futures import ThreadPoolExecutor

    import qx_utilities.hcp.qc_hcp as qc_hcp
    import qx_utilities.processing.core as pc

    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "template_scalar_bold_qc.wb.scene").write_text(
        "DUMMYIMAGEPATH/DUMMYIMAGEFILE\n"
    )
    sinfo, sessionsfolder = utils.build_hcp_session(str(tmp_path), bolds=True)
    for key in ["3", "4"]:
        sinfo[key]["name"] = "bold" + sinfo[key]["bold_number"]
    (tmp_path / "fc").mkdir()
    for number in ["1", "2"]:
        (tmp_path / "fc" / ("bold%s_fc.pscalar.nii" % number)).write_text("")
    # the jobs run in this process, and Workbench is not run at all
    monkeypatch.setattr(qc_hcp, "ProcessPoolExecutor", ThreadPoolExecutor)
    monkeypatch.setattr(
        pc, "run_external_for_file", lambda *args, **kwargs: (None, "done", 0)
    )
    monkeypatch.chdir(tmp_path)

    log = qc_hcp.hcp_run_qc(
        sinfo,
        utils.default_options(
            run="run",
            sessionsfolder=sessionsfolder,
            comlogs=str(tmp_path / "comlogs"),
            qc_scenetemplatefolder=str(templates),
            qc_modality="BOLD_FC",
            qc_boldfc="pscalar",
            qc_boldfcinput="fc.pscalar.nii",
            qc_boldfcpath="fc",
            qc_scenezip="no",
        ),
    )

    assert log.status[2] == 0, log.text
    scenes = sorted(Path(sessionsfolder, "QC", "BOLD_FC").glob("*.wb.scene"))
    assert [scene.read_text() for scene in scenes] == [
        "%s\n" % (tmp_path / "fc" / ("bold%s_fc.pscalar.nii" % number))
        for number in ["1", "2"]
    ]


# ------------------------------------------------------------------ guards


def test_only_entering_the_study_changes_the_current_folder():
    """
    A run that knows its study works in it because `gmri` enters it, through
    `placement.enter`, and leaves it on the way out, in `runCommand`. A second
    place that changed folder would move every relative path of the run, and
    of every run in the same process, under it. The launcher on the host never
    changes folder.
    """
    python = REPO_ROOT / "python"
    files = [
        *python.glob("qx_utilities/**/*.py"),
        *python.glob("qx_mice/**/*.py"),
        *python.glob("*.py"),
        python / "qx_utilities" / "gmri",
        REPO_ROOT / "bin" / "qunex_container",
    ]
    allowed = {"placement.py": {"enter"}, "gmri": {"runCommand"}}

    def changes_folder(node):
        function = node.func if isinstance(node, ast.Call) else None
        return (isinstance(function, ast.Attribute) and function.attr == "chdir") or (
            isinstance(function, ast.Name) and function.id == "chdir"
        )

    found = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        functions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        for function in functions:
            # a function's own statements, not those of a function inside it
            inner = {
                id(node)
                for nested in ast.walk(function)
                if nested is not function
                and isinstance(nested, (ast.FunctionDef, ast.AsyncFunctionDef))
                for node in ast.walk(nested)
            }
            for node in ast.walk(function):
                if id(node) not in inner and changes_folder(node):
                    if function.name not in allowed.get(path.name, set()):
                        found.append(
                            "%s: %s" % (path.relative_to(REPO_ROOT), function.name)
                        )

        outside = {id(node) for function in functions for node in ast.walk(function)}
        for node in ast.walk(tree):
            if id(node) not in outside and changes_folder(node):
                found.append("%s: <module>" % path.relative_to(REPO_ROOT))

    assert not found, found
