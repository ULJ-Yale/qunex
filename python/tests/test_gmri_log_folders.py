# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Where ``gmri`` puts a run's logs, whatever tier names the study or the log
folder: the command line over the recipe file over the batch file header, the
same order every other parameter follows.

The run's folder is decided once, by ``general.folders.run_folders``, and
handed to everything the run starts. ``run_recipe`` is handed it however it is
called, so that a call over sessions, or one whose sessions are not found,
still logs into one folder; so is every job a run submits.
"""

import os
import re
from pathlib import Path

import pytest

import qx_utilities.general.log as gl
import qx_utilities.general.log.context as glc
import qx_utilities.general.log.settings as gls
import qx_utilities.general.recipe as gr
import qx_utilities.general.scheduler as gs
from tests import utils

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def registry_of_this_tree(monkeypatch):
    """The commands are dispatched from this tree's committed registry."""
    monkeypatch.setenv("QUNEXPATH", str(REPO_ROOT))


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """
    A current folder and a home of their own, and no user settings file: a
    run outside a study must not log in the home folder of whoever runs them.
    """
    (tmp_path / "cwd").mkdir()
    monkeypatch.chdir(tmp_path / "cwd")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setattr(
        gls, "USER_SETTINGS_PATHS", [str(tmp_path / "user" / "qunex_settings.yaml")]
    )
    monkeypatch.setattr(glc, "_status_written", False)
    yield
    gl.set_active(None)


@pytest.fixture(scope="module")
def gmri():
    return utils.load_gmri("gmri_log_folders")


def make_study(root, header="", sessions=("S01", "S02")):
    """A marked study with the named sessions, and a batch file listing them."""
    for session in sessions:
        (root / "sessions" / session).mkdir(parents=True)
    (root / ".qunexstudy").write_text("")
    (root / "processing").mkdir()
    batch = root / "processing" / "batch.txt"
    batch.write_text(
        header + "".join("---\nid: %s\nsubject: %s\n" % (s, s) for s in sessions)
    )
    return root, batch


def recorded_utility(gmri, monkeypatch):
    """Stubs a single utility call, and returns what it was called with."""
    called = {}

    def record(function, args, run=None, tags=None):
        called.update(args, run=run)
        return gmri.gc.CallOutcome("call", 0, None, None)

    monkeypatch.setattr(gmri.gc, "run_with_log", record)
    return called


def recorded_recipe(gmri, monkeypatch):
    """
    `run_recipe` itself, replaced: what each recipe the call runs was handed.
    A call over sessions runs them through `run_in_parallel`, which is
    replaced as well, its process pool being no place for a local function.
    """
    calls = []

    def run_recipe(
        recipe_file=None,
        recipe=None,
        steps=None,
        startwith=None,
        logfolder=None,
        eargs=None,
        log_settings=None,
    ):
        calls.append({"logfolder": logfolder, "eargs": eargs})

    def run_in_parallel(parallel, cores=None, prepend="", run=None):
        for call in parallel:
            call["function"](**call["args"])
        return [gmri.gc.CallOutcome(call["name"], 0, None, None) for call in parallel]

    # the registry caches the callable it loaded, so the cache is what is
    # replaced; the module attribute for a caller that imports it
    monkeypatch.setattr(gr, "run_recipe", run_recipe)
    path = gmri.qx_commands.get("run_recipe").path
    monkeypatch.setitem(gmri.qx_commands._callable_cache, path, run_recipe)
    monkeypatch.setattr(gmri.gc, "run_in_parallel", run_in_parallel)
    return calls


def recipe_file(tmp_path, studyfolder=None, logfolder=None):
    lines = ["global_parameters:"]
    if studyfolder:
        lines.append("    studyfolder: %s" % studyfolder)
    if logfolder:
        lines.append("    logfolder: %s" % logfolder)
    lines += [
        "    overwrite: 'yes'",
        "recipes:",
        "    r:",
        "        commands:",
        "            - create_study",
    ]
    path = tmp_path / "recipe.yaml"
    path.write_text("\n".join(lines) + "\n")
    return str(path)


# ------------------------------------------------------------- the batch file


def test_a_log_folder_the_batch_file_header_names_is_where_the_logs_go(
    gmri, tmp_path, monkeypatch
):
    """The banner reported it as applied; the logs went to the study's."""
    study, batch = make_study(
        tmp_path / "study",
        "_studyfolder: %s\n_logfolder: %s\n" % (tmp_path / "study", tmp_path / "hdr"),
    )
    called = recorded_utility(gmri, monkeypatch)

    gmri.runCommand("import_dicom", {"batchfile": str(batch)})

    assert called["run"].logfolder == str(tmp_path / "hdr")


def test_a_relative_log_folder_is_in_the_study_the_header_names(
    gmri, tmp_path, monkeypatch
):
    study, batch = make_study(
        tmp_path / "study", "_studyfolder: %s\n_logfolder: hdr\n" % (tmp_path / "study")
    )
    called = recorded_utility(gmri, monkeypatch)

    gmri.runCommand("import_dicom", {"batchfile": str(batch)})

    assert called["run"].logfolder == str(study / "hdr")


def test_the_command_line_log_folder_wins_over_the_header_s(
    gmri, tmp_path, monkeypatch
):
    study, batch = make_study(
        tmp_path / "study", "_logfolder: %s\n" % (tmp_path / "hdr")
    )
    called = recorded_utility(gmri, monkeypatch)

    gmri.runCommand(
        "import_dicom", {"batchfile": str(batch), "logfolder": str(tmp_path / "cli")}
    )

    assert called["run"].logfolder == str(tmp_path / "cli")


def test_the_banner_says_where_the_logs_are(gmri, tmp_path, monkeypatch, capsys):
    study, _ = make_study(tmp_path / "study")
    called = recorded_utility(gmri, monkeypatch)

    gmri.runCommand("import_dicom", {"studyfolder": str(study)})

    line = "\n---> Logs: %s\n" % called["run"].logfolder
    assert line in capsys.readouterr().out
    assert line in Path(called["run"].path).read_text(), "and the runlog says so"


def test_a_command_that_creates_its_study_takes_a_relative_log_folder_from_here(
    gmri, tmp_path, monkeypatch
):
    """
    A relative log folder is taken from where the run takes every other
    relative path: the study a run names, once it exists -- but the current
    folder for a command that creates the study it names, even one that is
    there already.
    """
    study, _ = make_study(tmp_path / "study")
    called = recorded_utility(gmri, monkeypatch)

    gmri.runCommand("create_study", {"studyfolder": str(study), "logfolder": "mine"})
    assert called["run"].logfolder == str(tmp_path / "cwd" / "mine")

    gmri.runCommand("create_batch", {"studyfolder": str(study), "logfolder": "mine"})
    assert called["run"].logfolder == str(study / "mine")


# ------------------------------------------------------------- run_recipe


@pytest.mark.parametrize("given", ["alone", "batchfile", "sessions"])
def test_a_recipe_logs_in_the_study_it_names_however_its_sessions_are_given(
    gmri, tmp_path, monkeypatch, given
):
    """
    With --batchfile or --sessions the recipe's study used to place gmri's
    runlog in one folder and the recipes in another.
    """
    study, batch = make_study(tmp_path / "study")
    calls = recorded_recipe(gmri, monkeypatch)
    args = {"recipe_file": recipe_file(tmp_path, studyfolder=study), "recipe": "r"}
    if given == "batchfile":
        args["batchfile"] = str(batch)
    elif given == "sessions":
        args["sessions"] = "S01,S02"

    gmri.runCommand("run_recipe", args)

    assert len(calls) == (1 if given == "alone" else 2), "the sessions were found"
    folders = {call["logfolder"] for call in calls}
    assert len(folders) == 1, "every recipe of the call logs into one folder"
    folder = Path(folders.pop())
    assert folder.parent == study / "logs"
    assert folder.name.endswith("_run_recipe_r"), "named for the recipe, always"

    if given == "alone":
        assert not folder.exists(), "a recipe that runs itself writes its own runlog"
    else:
        stamp = folder.name[: -len("_run_recipe_r")]
        assert [p.name for p in folder.iterdir()] == [
            "Log-run_recipe_r-%s.log" % stamp
        ], "gmri's runlog, filed under the run's name"


def test_a_recipe_whose_sessions_are_not_found_runs_once_in_one_folder(
    gmri, tmp_path, monkeypatch
):
    """It used to leave a header only runlog in one folder and log in another."""
    study, _ = make_study(tmp_path / "study")
    calls = recorded_recipe(gmri, monkeypatch)

    gmri.runCommand(
        "run_recipe",
        {
            "recipe_file": recipe_file(tmp_path, studyfolder=study),
            "recipe": "r",
            "sessions": "NEW1,NEW2",
        },
    )

    assert len(calls) == 1
    assert Path(calls[0]["logfolder"]).parent == study / "logs"
    assert not os.path.exists(calls[0]["logfolder"]), (
        "gmri writes no runlog of its own for a recipe that runs itself"
    )


def test_the_command_line_study_wins_over_the_recipe_s(gmri, tmp_path, monkeypatch):
    a, batch = make_study(tmp_path / "a")
    b, _ = make_study(tmp_path / "b")
    calls = recorded_recipe(gmri, monkeypatch)

    gmri.runCommand(
        "run_recipe",
        {
            "recipe_file": recipe_file(tmp_path, studyfolder=b),
            "recipe": "r",
            "studyfolder": str(a),
            "batchfile": str(batch),
        },
    )

    assert {str(Path(c["logfolder"]).parent) for c in calls} == {str(a / "logs")}
    assert not (b / "logs").exists()


def test_the_recipe_s_study_wins_over_the_batch_file_header_s(
    gmri, tmp_path, monkeypatch
):
    a, batch = make_study(tmp_path / "a", "_studyfolder: %s\n" % (tmp_path / "a"))
    b, _ = make_study(tmp_path / "b")
    calls = recorded_recipe(gmri, monkeypatch)

    gmri.runCommand(
        "run_recipe",
        {
            "recipe_file": recipe_file(tmp_path, studyfolder=b),
            "recipe": "r",
            "batchfile": str(batch),
        },
    )

    assert {str(Path(c["logfolder"]).parent) for c in calls} == {str(b / "logs")}
    assert not (a / "logs").exists()


def test_a_recipe_logfolder_is_the_one_its_runs_are_handed(gmri, tmp_path, monkeypatch):
    """A relative one is taken from the study, which exists."""
    study, batch = make_study(tmp_path / "study")
    calls = recorded_recipe(gmri, monkeypatch)

    gmri.runCommand(
        "run_recipe",
        {
            "recipe_file": recipe_file(tmp_path, studyfolder=study, logfolder="rlogs"),
            "recipe": "r",
            "batchfile": str(batch),
        },
    )

    assert {c["logfolder"] for c in calls} == {str(study / "rlogs")}


def test_every_recipe_of_a_call_over_sessions_is_handed_the_run_s_folder(
    gmri, tmp_path, monkeypatch
):
    """A --logfolder the call carried reached every recipe as it was typed."""
    study, batch = make_study(tmp_path / "study")
    calls = recorded_recipe(gmri, monkeypatch)

    gmri.runCommand(
        "run_recipe",
        {
            "recipe_file": recipe_file(tmp_path, studyfolder=study),
            "recipe": "r",
            "batchfile": str(batch),
            "logfolder": "typed",
        },
    )

    assert [call["logfolder"] for call in calls] == [str(study / "typed")] * 2


# ------------------------------------------------------------- scheduled runs


@pytest.mark.parametrize(
    "command",
    ["hcp_pre_freesurfer", "run_recipe", "import_dicom"],
    ids=["a job per session", "a recipe per session", "one job"],
)
def test_a_scheduled_run_hands_every_job_its_folder(
    gmri, tmp_path, monkeypatch, command
):
    """
    Each job used to decide a folder of its own, and a --logfolder the call
    carried reached the job as it was typed.
    """
    study, batch = make_study(tmp_path / "study")
    submitted = []
    monkeypatch.setattr(gs, "schedule", lambda **kw: submitted.append(kw) or ("", "1"))
    args = {
        "studyfolder": str(study),
        "scheduler": "SLURM,time=1",
        "logfolder": "relative/elsewhere",
    }
    if command == "import_dicom":
        args["masterinbox"] = "none"
    else:
        args["batchfile"] = str(batch)
    if command == "run_recipe":
        args.update(recipe_file=recipe_file(tmp_path, studyfolder=study), recipe="r")

    gmri.runCommand(command, args)

    expected = str(study / "relative" / "elsewhere")
    assert len(submitted) == (1 if command == "import_dicom" else 2)
    for job in submitted:
        handed = re.findall(r'--logfolder="([^"]*)"', job["command"])
        assert handed == [expected], job["command"]
        assert job["output"].startswith("both:%s/batchlogs/" % expected)


@pytest.mark.parametrize("exported", [True, False], ids=["--bash", "nowhere"])
def test_a_scheduled_recipe_resolves_its_labels_with_what_bash_exports(
    gmri, tmp_path, monkeypatch, capsys, exported
):
    """
    A recipe that names its study only through a label its --bash exports
    was placed from this environment alone: the label was said to be missing
    and every job was handed ~/qunex_logs, while qunex_container, reading its
    --bash_post the same way, logged the same recipe in the study.
    """
    study, batch = make_study(tmp_path / "study")
    path = tmp_path / "recipe.yaml"
    path.write_text(
        "global_parameters:\n"
        '    studyfolder: "{{$QX_TEST_STUDY}}"\n'
        "recipes:\n    r:\n        commands:\n            - create_study\n"
    )
    monkeypatch.delenv("QX_TEST_STUDY", raising=False)
    submitted = []
    monkeypatch.setattr(gs, "schedule", lambda **kw: submitted.append(kw) or ("", "1"))
    args = {
        "recipe_file": str(path),
        "recipe": "r",
        "scheduler": "SLURM,time=1",
        "bash": "module load x; export QX_TEST_STUDY=%s" % study,
    }
    if not exported:
        args["bash"] = "module load x"

    gmri.runCommand("run_recipe", args)

    (job,) = submitted
    (handed,) = re.findall(r'--logfolder="([^"]*)"', job["command"])
    if exported:
        assert handed.startswith(str(study / "logs") + os.sep), handed
        assert "QX_TEST_STUDY" not in capsys.readouterr().err
    else:
        assert handed.startswith(str(tmp_path / "home" / "qunex_logs")), handed
        assert "export it in --bash" in capsys.readouterr().err
