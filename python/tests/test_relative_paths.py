# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for where a relative path is taken from: the study folder, when the run
knows its study, and the current folder when it does not.

What a command line names is made absolute by `general/batch_io.py` before the
run knows every study it may name. `bin/qunex_container` carries a spliced copy
of that module, so the launcher on the host takes those paths the way QuNex
does, and filters a batch file header with the same unset helpers. Once the
batch file header is read, `process.merge_options` settles the study and the
sessions folder absolute, whichever tier named them.

`gmri` then places the run by the rule `general.folders.run_folders` holds and
enters the folder it takes its relative paths from (`general/placement.py`).
The commands it dispatches are stubbed where they are dispatched, and each stub
records the folder it was called in -- the folder every relative path it was
handed is read against, by the command and by every tool it starts.
"""

import os
from pathlib import Path

import pytest

import qx_utilities.general.batch_io as bio
import qx_utilities.general.commands_support as gcs
import qx_utilities.general.exceptions as ge
import qx_utilities.general.folders as gf
import qx_utilities.general.log as gl
import qx_utilities.general.log.context as glc
import qx_utilities.general.log.settings as gls
import qx_utilities.general.placement as gpl
import qx_utilities.general.process as gp
import qx_utilities.general.scheduler as gs
from qx_registry import qx_commands
from tests import utils
from tests.test_folders import run_look_only
from tests.utils import default_options

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def registry_of_this_tree(monkeypatch):
    """The commands are dispatched from this tree's committed registry."""
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
def one_run_per_test(monkeypatch):
    """Each test is a run of its own, which has written no status yet."""
    monkeypatch.setattr(glc, "_status_written", False)


@pytest.fixture(autouse=True)
def default_settings():
    """A run sets the process-wide settings; put them back after."""
    yield
    gl.set_active(None)


@pytest.fixture(scope="module")
def gmri():
    return utils.load_gmri("gmri_relative_paths")


@pytest.fixture
def layout(tmp_path, monkeypatch):
    """
    A study with one session, and a folder beside it the runs are started
    from. Returns (study, elsewhere), the current folder being `elsewhere`.
    """
    study, elsewhere = utils.layout(tmp_path)
    monkeypatch.chdir(elsewhere)
    return study, elsewhere


def recorded_utility(gmri, monkeypatch):
    """Stubs a single utility call; returns what it was called with, and where."""
    called = {}

    def record(function, args, run=None, tags=None):
        called.update(args, cwd=os.getcwd(), run=run)
        return gmri.gc.CallOutcome("call", 0, None, None)

    monkeypatch.setattr(gmri.gc, "run_with_log", record)
    return called


def recorded_processing(gmri, monkeypatch):
    """Stubs `gp.run`; returns what it was handed, and where it was called."""
    seen = {}
    monkeypatch.setattr(
        gmri.gp,
        "run",
        lambda qx_command, args, sessions, options, sources, run: seen.update(
            cwd=os.getcwd(), args=args, options=options, sessions=sessions, run=run
        ),
    )
    return seen


# ------------------------------------------------------------------ run_path


def test_a_relative_path_is_taken_from_the_base_it_is_given(tmp_path):
    assert bio.run_path("a/b.txt", str(tmp_path)) == str(tmp_path / "a" / "b.txt")


def test_a_relative_path_without_a_base_is_taken_from_the_current_folder(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    assert bio.run_path("a/../b.txt") == str(tmp_path / "b.txt")


def test_an_absolute_path_is_kept_whatever_the_base(tmp_path):
    assert bio.run_path("/x/./y", str(tmp_path)) == "/x/y"


def test_home_and_variables_are_expanded_before_anything_else(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("QX_TEST_STUDY", str(tmp_path / "s"))

    assert bio.run_path("~/x", "/base") == str(tmp_path / "home" / "x")
    assert bio.run_path("$QX_TEST_STUDY/x", "/base") == str(tmp_path / "s" / "x")


@pytest.mark.parametrize("value", ["", "  ", None, True])
def test_an_empty_or_a_flag_value_is_left_as_it_is(value):
    assert bio.run_path(value, "/base") is value


# ------------------------------------------------------- anchor_command_line


def test_the_command_line_study_is_taken_from_the_current_folder_and_the_rest_from_it(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    args, study = bio.anchor_command_line(
        {
            "studyfolder": "study",
            "sessionsfolder": "other_sessions",
            "batchfile": "processing/batch.txt",
            "sessions": "processing/lists/a.list",
            "recipe_file": "recipes/r.yaml",
            "logstatus": "status.yaml",
            "hcp_gdcoeffs": "coeffs.grad",
        }
    )

    s = tmp_path / "study"
    assert study == str(s)
    assert args["studyfolder"] == str(s)
    assert args["sessionsfolder"] == str(s / "other_sessions")
    assert args["batchfile"] == str(s / "processing" / "batch.txt")
    assert args["sessions"] == str(s / "processing" / "lists" / "a.list")
    assert args["recipe_file"] == str(s / "recipes" / "r.yaml")
    assert args["logstatus"] == str(tmp_path / "status.yaml"), "the caller's file"
    assert args["hcp_gdcoeffs"] == "coeffs.grad", "read later, from the study folder"


def test_session_ids_are_not_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args, _ = bio.anchor_command_line({"studyfolder": "s", "sessions": "S01,S0*"})
    assert args["sessions"] == "S01,S0*"


def test_a_sessions_folder_named_alone_is_left_for_the_header_to_settle(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    args, study = bio.anchor_command_line(
        {"sessionsfolder": "s/sessions", "batchfile": "processing/batch.txt"}
    )

    assert args["sessionsfolder"] == "s/sessions"
    assert study == str(tmp_path / "s"), "the study the sessions folder is in"
    assert args["batchfile"] == str(tmp_path / "s" / "processing" / "batch.txt")


def test_a_sessions_folder_named_alone_says_where_it_is(tmp_path, monkeypatch):
    """`~` and variables are expanded, the rest is left for the merge to settle."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("QX_TEST_SESSIONS", "named")
    monkeypatch.chdir(tmp_path)

    args, study = bio.anchor_command_line({"sessionsfolder": "~/study/sessions"})
    assert args["sessionsfolder"] == str(tmp_path / "home" / "study" / "sessions")
    assert study == str(tmp_path / "home" / "study")

    args, _ = bio.anchor_command_line({"sessionsfolder": "$QX_TEST_SESSIONS"})
    assert args["sessionsfolder"] == "named", "relative, for the header to settle"


def test_a_command_line_that_names_no_study_takes_files_from_the_current_folder(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    args, study = bio.anchor_command_line({"batchfile": "../processing/batch.txt"})

    assert study is None
    assert args["batchfile"] == str(tmp_path.parent / "processing" / "batch.txt")


def test_a_study_known_from_elsewhere_is_used_only_when_the_command_line_names_none(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    args, study = bio.anchor_command_line({"batchfile": "b.txt"}, study="/recipe/study")
    assert (args["batchfile"], study) == ("/recipe/study/b.txt", "/recipe/study")

    args, study = bio.anchor_command_line(
        {"studyfolder": "/cli", "batchfile": "b.txt"}, study="/recipe/study"
    )
    assert (args["batchfile"], study) == ("/cli/b.txt", "/cli")


@pytest.mark.parametrize("command", bio.CREATES_STUDY)
def test_a_command_that_creates_its_study_takes_nothing_from_it(
    tmp_path, monkeypatch, command
):
    monkeypatch.chdir(tmp_path)
    args, study = bio.anchor_command_line(
        {"studyfolder": "new", "batchfile": "old/processing/batch.txt"}, command
    )

    assert study is None
    assert args["studyfolder"] == str(tmp_path / "new")
    assert args["batchfile"] == str(tmp_path / "old" / "processing" / "batch.txt")


def test_every_command_that_creates_its_study_is_a_command(monkeypatch):
    """
    `CREATES_STUDY` names its commands by hand: one renamed without it would
    take its paths from the study it is creating. It also holds their
    deprecated names, which the container launcher is given as typed.
    """
    monkeypatch.setenv("QUNEXPATH", str(REPO_ROOT))

    for name in bio.CREATES_STUDY:
        assert qx_commands.get(gf.current_command(name)) is not None, name


# ------------------------------------------------- what the launcher carries


def test_the_batch_header_unset_helpers_are_batch_io_s():
    """
    The launcher carries `batch_io`, so these are its own as well: QuNex has
    to use the very same ones, not a second definition that can drift.
    """
    names = (
        "UNSET_BATCH_HEADER",
        "UNSET_BATCH_SESSION",
        "unset_patterns",
        "is_unset",
        "without_unset",
    )

    differ = [name for name in names if getattr(gcs, name) is not getattr(bio, name)]
    assert not differ, differ


# ------------------------------------------------------------ merge_options


@pytest.mark.parametrize("named_in", ["command line", "batch file"])
def test_a_sessions_folder_the_header_names_is_taken_from_the_study(
    tmp_path, monkeypatch, named_in
):
    monkeypatch.chdir(tmp_path)
    study = {"studyfolder": str(tmp_path / "s")}
    args, header = (study, {}) if named_in == "command line" else ({}, dict(study))
    header["sessionsfolder"] = "sessions_v2"

    options, _, stated = gp.merge_options("hcp_pre_freesurfer", args, header)

    assert options["sessionsfolder"] == str(tmp_path / "s" / "sessions_v2")
    assert stated["sessionsfolder"] == options["sessionsfolder"], (
        "a utility or a script is handed it absolute as well"
    )


@pytest.mark.parametrize("named_in", ["command line", "batch file"])
def test_a_command_line_sessions_folder_is_settled_in_the_study_any_tier_names(
    tmp_path, monkeypatch, named_in
):
    monkeypatch.chdir(tmp_path)
    args = {"sessionsfolder": "sessions_v2"}
    header = {}
    (args if named_in == "command line" else header)["studyfolder"] = "s"

    options, _, stated = gp.merge_options("hcp_pre_freesurfer", args, header)

    assert options["studyfolder"] == str(tmp_path / "s")
    assert options["sessionsfolder"] == str(tmp_path / "s" / "sessions_v2")
    assert stated["sessionsfolder"] == options["sessionsfolder"]


def test_a_study_the_header_names_is_taken_from_the_current_folder(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    options, _, stated = gp.merge_options(
        "hcp_pre_freesurfer", {}, {"studyfolder": "s"}
    )

    assert options["studyfolder"] == str(tmp_path / "s")
    assert options["sessionsfolder"] == str(tmp_path / "s" / "sessions")
    assert stated["studyfolder"] == str(tmp_path / "s")
    assert stated["sessionsfolder"] == options["sessionsfolder"], (
        "the sessions folder derived from it is handed on absolute too"
    )


def test_a_sessions_folder_named_without_a_study_is_taken_from_the_current_folder(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    options, sources, _ = gp.merge_options(
        "hcp_pre_freesurfer", {}, {"sessionsfolder": "x"}
    )

    assert options["sessionsfolder"] == str(tmp_path / "x")
    assert options["studyfolder"] == str(tmp_path)
    assert sources["sessionsfolder"] != "default", (
        "the study a named sessions folder is in is a study the run knows"
    )


def test_a_run_that_names_no_folder_has_no_folder_to_work_in(tmp_path, monkeypatch):
    study = tmp_path / "study"
    (study / "sessions").mkdir(parents=True)
    (study / ".qunexstudy").write_text("")
    monkeypatch.chdir(study / "sessions")

    options, sources, _ = gp.merge_options("hcp_pre_freesurfer", {})

    assert options["studyfolder"] == str(study), "found by its marker"
    assert sources["sessionsfolder"] == "default", (
        "a study found by its marker, or the current folder's parent, is where "
        "the logs go, not a folder the run takes paths from"
    )


@pytest.mark.parametrize("key", ["studyfolder", "sessionsfolder"])
def test_a_folder_given_without_a_value_is_said_to_be_invalid(key):
    """A bare --studyfolder used to end in a TypeError traceback."""
    with pytest.raises(ge.CommandError) as error:
        gp.merge_options("hcp_pre_freesurfer", {key: True})

    assert error.value.error == "Invalid parameter value!"
    assert "--%s=<folder>" % key in error.value.hints[-1]


@pytest.mark.parametrize("value", ["", "  "], ids=["empty", "spaces"])
def test_an_empty_folder_leaves_the_one_the_header_names(tmp_path, monkeypatch, value):
    """
    A recipe variable that expanded to nothing names no folder. It used to
    take the place of the folder the batch file header names, and one of
    spaces was taken for a study of that name in the current folder, while
    the run was placed -- and logged -- in the header's study.
    """
    monkeypatch.chdir(tmp_path)

    for key, named in (("studyfolder", "s"), ("sessionsfolder", "s/sessions")):
        options, sources, stated = gp.merge_options(
            "hcp_pre_freesurfer", {key: value}, {key: named}
        )
        assert options[key] == str(tmp_path / named), key
        assert sources[key] == "batch file", key
        assert stated[key] == options[key], key

    options, sources, _ = gp.merge_options("hcp_pre_freesurfer", {"studyfolder": value})
    assert sources["sessionsfolder"] == "default", "no study is named"
    assert options["studyfolder"] == str(tmp_path.parent), "the current one's parent"


def test_home_is_expanded_in_the_folders_a_run_names(tmp_path, monkeypatch):
    """A quoted `~` used to name a folder called `~` in the current one."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path)

    options, _, stated = gp.merge_options("hcp_pre_freesurfer", {"studyfolder": "~/s"})
    assert options["studyfolder"] == str(tmp_path / "home" / "s")
    assert stated["sessionsfolder"] == str(tmp_path / "home" / "s" / "sessions")

    options, _, _ = gp.merge_options(
        "hcp_pre_freesurfer", {}, {"sessionsfolder": "~/s/sessions"}
    )
    assert options["sessionsfolder"] == str(tmp_path / "home" / "s" / "sessions")
    assert options["studyfolder"] == str(tmp_path / "home" / "s")


@pytest.mark.parametrize(
    "named",
    [
        {"studyfolder": "s"},
        {"sessionsfolder": "x"},
        {"studyfolder": "s", "sessionsfolder": "x"},
        {"studyfolder": "s", "sessionsfolder": ""},
        {"studyfolder": "~/s", "sessionsfolder": "../x"},
        {"sessionsfolder": ""},
        {"studyfolder": "  "},
        {"studyfolder": "s", "sessionsfolder": " "},
    ],
)
def test_the_test_options_settle_relative_folders_as_a_run_does(
    tmp_path, monkeypatch, named
):
    """
    An empty folder is one nobody named. The study marked above the current
    folder is not its parent here, so a run that names neither folder tells
    the two apart.
    """
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "study" / "a" / "b").mkdir(parents=True)
    (tmp_path / "study" / ".qunexstudy").write_text("")
    monkeypatch.chdir(tmp_path / "study" / "a" / "b")

    options, _, _ = gp.merge_options("hcp_pre_freesurfer", dict(named))
    mirrored = default_options(**named)

    assert mirrored["sessionsfolder"] == options["sessionsfolder"]
    assert mirrored["studyfolder"] == options["studyfolder"]


# ------------------------------------------------ a study that is not there


def test_a_processing_run_makes_no_study_of_a_folder_its_own_logs_made(
    tmp_path, monkeypatch
):
    """
    A run writes its runlog into the study it names before the command runs,
    so a mistyped --studyfolder was there by the time the sessions folder was
    to be created in it, and the run went on in a study of its own making.
    """
    monkeypatch.chdir(tmp_path)
    typo = tmp_path / "typo"

    with pytest.raises(ge.CommandFailed) as failure:
        run_look_only(tmp_path, studyfolder=str(typo), run="run")

    assert failure.value.error == "Missing study folder"
    assert sorted(os.listdir(typo)) == ["logs"], "the runlog says what happened"


# ------------------------------------------------- the folder a run works in


def test_a_study_that_can_not_be_entered_is_said(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert gpl.enter(str(tmp_path / "missing")) is False
    assert "can not be entered" in capsys.readouterr().err
    assert os.getcwd() == str(tmp_path)


def test_entering_a_folder_says_whether_it_moved(tmp_path, monkeypatch):
    (tmp_path / "study").mkdir()
    monkeypatch.chdir(tmp_path)
    environment = dict(os.environ)

    assert gpl.enter(None) is False
    assert gpl.enter(str(tmp_path)) is False, "already there"
    assert gpl.enter(str(tmp_path / "study")) is True
    assert os.getcwd() == str(tmp_path / "study")
    assert dict(os.environ) == environment, "PWD and the rest are left as they are"


def test_what_is_only_in_the_current_folder_is_found(tmp_path):
    study = tmp_path / "study"
    study.mkdir()
    (tmp_path / "here.txt").write_text("")
    (tmp_path / "both.txt").write_text("")
    (study / "both.txt").write_text("")
    (tmp_path / "S01").mkdir()

    found = gpl.misplaced(
        {
            "a": "here.txt",
            "b": "both.txt",
            "c": str(tmp_path / "here.txt"),
            "sessions": "S01",
            "flag": True,
        },
        str(study),
        str(tmp_path),
        skip={"sessions"},
    )
    assert found == ["--a=here.txt"]


def test_a_session_id_is_not_taken_for_a_misplaced_path(
    tmp_path, monkeypatch, capsys
):
    """
    `--session` is the id of the session a script runs (`dwi_eddy_qc`,
    `parcellate_anat`), and names its folder when the run is started from
    the sessions folder: it is not a path given relative to the wrong folder.
    """
    study = tmp_path / "study"
    (study / "sessions" / "S01").mkdir(parents=True)
    (study / "sessions" / "here.txt").write_text("")
    monkeypatch.chdir(study / "sessions")
    placement = gf.Placement("parcellate_anat", str(study), True, str(study), "", None)

    gpl.work_in_study(
        "parcellate_anat",
        placement,
        {"session": "S01", "sessions": "S01", "file": "here.txt"},
        str(study / "sessions"),
    )

    err = capsys.readouterr().err
    assert "--file=here.txt" in err
    assert "--session=" not in err and "--sessions=" not in err


def test_a_placement_warning_is_in_the_runlog(gmri, layout, monkeypatch, capsys):
    """
    The warnings about where relative paths are taken from are said before the
    runlog exists, and were printed to the console alone: a runlog read later
    did not say why a value named in the current folder was not found.
    """
    study, elsewhere = layout
    (elsewhere / "params.txt").write_text("")
    recorded_utility(gmri, monkeypatch)

    gmri.runCommand(
        "create_batch", {"studyfolder": str(study), "paramfile": "params.txt"}
    )

    err = capsys.readouterr().err
    (runlog,) = (study / "logs").glob("*/**/Log-*.log")
    warning = [line for line in err.splitlines() if "--paramfile=params.txt" in line]
    assert len(warning) == 1, err
    assert warning[0] in runlog.read_text().splitlines()


# ------------------------------------------------------------- dispatch


def test_a_command_line_sessions_folder_is_taken_from_a_study_the_header_names(
    gmri, layout, monkeypatch
):
    study, elsewhere = layout
    (elsewhere / "batch.txt").write_text(
        "_studyfolder: %s\n---\nid: S01\nsubject: S01\n01: T1w\n" % study
    )
    seen = recorded_processing(gmri, monkeypatch)

    gmri.runCommand(
        "hcp_pre_freesurfer", {"sessionsfolder": "sessions", "batchfile": "batch.txt"}
    )

    assert seen["options"]["sessionsfolder"] == str(study / "sessions"), (
        "a relative sessions folder is taken from a study any tier names"
    )
    assert seen["args"]["sessionsfolder"] == str(study / "sessions")
    assert seen["cwd"] == str(study)


def test_a_utility_runs_in_the_study_and_the_caller_stays_where_it_was(
    gmri, layout, monkeypatch
):
    study, elsewhere = layout
    called = recorded_utility(gmri, monkeypatch)

    gmri.runCommand("create_batch", {"studyfolder": "../study"})

    assert called["cwd"] == str(study)
    assert called["studyfolder"] == str(study), "handed absolute, not as typed"
    assert called["sessionsfolder"] == str(study / "sessions")
    assert os.getcwd() == str(elsewhere)


def test_the_caller_gets_its_folder_back_when_the_command_fails(
    gmri, layout, monkeypatch
):
    study, elsewhere = layout

    def fail(function, args, run=None, tags=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(gmri.gc, "run_with_log", fail)

    with pytest.raises(RuntimeError):
        gmri.runCommand("create_batch", {"studyfolder": str(study)})
    assert os.getcwd() == str(elsewhere)


@pytest.mark.parametrize("language", ["bash", "matlab"])
def test_a_script_runs_in_the_study(gmri, layout, monkeypatch, language):
    study, _ = layout
    seen = []

    if language == "bash":
        monkeypatch.setattr(
            gmri.gb,
            "run",
            lambda qx_command, args, run=None, session=None: (
                seen.append((os.getcwd(), dict(args))) or 0
            ),
        )
        gmri.runCommand(
            "dwi_dtifit",
            {"studyfolder": "../study", "sessions": "S01", "mask": "m.nii"},
        )
        assert seen[0][1]["studyfolder"] == str(study)
        assert seen[0][1]["mask"] == "m.nii", "a value is handed on as typed"
    else:
        monkeypatch.setattr(
            gmri.gm,
            "run",
            lambda qx_command, args, run=None: (
                seen.append((os.getcwd(), dict(args))) or 0
            ),
        )
        gmri.runCommand(
            "fc_compute_roifc", {"studyfolder": str(study), "flist": "lists/a.list"}
        )

    assert seen[0][0] == str(study)


def test_a_processing_command_runs_in_the_study_and_reads_its_batch_file_there(
    gmri, layout, monkeypatch
):
    study, elsewhere = layout
    seen = recorded_processing(gmri, monkeypatch)

    gmri.runCommand(
        "hcp_pre_freesurfer",
        {"studyfolder": "../study", "batchfile": "processing/batch.txt"},
    )

    assert seen["cwd"] == str(study)
    assert seen["options"]["batchfile"] == str(study / "processing" / "batch.txt")
    assert seen["args"]["studyfolder"] == str(study), "replayed absolute by a scheduler"
    assert seen["run"].startfolder == str(elsewhere), "where a scheduled job starts"


def test_a_run_that_names_no_folder_stays_in_the_current_folder(
    gmri, layout, monkeypatch
):
    study, _ = layout
    monkeypatch.chdir(study / "sessions")
    seen = recorded_processing(gmri, monkeypatch)

    gmri.runCommand("hcp_pre_freesurfer", {"batchfile": "../processing/batch.txt"})

    assert seen["cwd"] == str(study / "sessions"), (
        "the legacy run from inside the sessions folder, its study found by the "
        "marker, still takes its paths from where it is"
    )
    assert seen["run"].logfolder.startswith(str(study / "logs")), (
        "while it logs in the study its marker shows"
    )


def test_a_batch_file_named_without_a_study_is_read_from_the_current_folder(
    gmri, layout, monkeypatch
):
    study, elsewhere = layout
    (elsewhere / "batch.txt").write_text(
        "_studyfolder: ../study\n---\nid: S01\nsubject: S01\n01: T1w\n"
    )
    seen = recorded_processing(gmri, monkeypatch)

    gmri.runCommand("hcp_pre_freesurfer", {"batchfile": "batch.txt"})

    assert seen["options"]["batchfile"] == str(elsewhere / "batch.txt")
    assert seen["options"]["studyfolder"] == str(study), (
        "the header's relative study is taken from the current folder"
    )
    assert seen["cwd"] == str(study), "the header named the study: the run works there"


def test_a_relative_folder_in_the_header_is_taken_from_the_study(
    gmri, layout, monkeypatch
):
    study, _ = layout
    (study / "sessions_v2" / "S01").mkdir(parents=True)
    (study / "processing" / "batch_v2.txt").write_text(
        "_sessionsfolder: sessions_v2\n---\nid: S01\nsubject: S01\nhcp: hcp\n01: T1w\n"
    )
    seen = recorded_processing(gmri, monkeypatch)

    gmri.runCommand(
        "hcp_pre_freesurfer",
        {"studyfolder": "../study", "batchfile": "processing/batch_v2.txt"},
    )

    assert seen["options"]["sessionsfolder"] == str(study / "sessions_v2")
    assert seen["sessions"][0]["hcp"] == str(study / "sessions_v2" / "S01" / "hcp")
    assert seen["run"].logfolder.startswith(str(study / "logs"))


def test_create_study_takes_its_paths_from_the_current_folder(
    gmri, layout, monkeypatch, capsys
):
    _, elsewhere = layout
    called = recorded_utility(gmri, monkeypatch)

    gmri.runCommand("create_study", {"studyfolder": "new", "folders": "mine.txt"})

    assert called["studyfolder"] == str(elsewhere / "new")
    assert called["folders"] == "mine.txt"
    assert called["cwd"] == str(elsewhere)
    assert "does not exist yet" not in capsys.readouterr().err, (
        "the study it creates is not one that is missing"
    )


def test_a_folder_that_defaults_to_the_current_one_is_the_study(
    gmri, layout, monkeypatch
):
    study, _ = layout
    called = recorded_utility(gmri, monkeypatch)

    gmri.runCommand("check_study", {"studyfolder": str(study)})

    assert "startfolder" not in called, "the default is left to the command"
    assert called["cwd"] == str(study), "where '.' is"


# ----------------------------------------------------- warnings and edges


def test_a_value_only_in_the_current_folder_is_warned_about(
    gmri, layout, monkeypatch, capsys
):
    study, elsewhere = layout
    (elsewhere / "coeffs.grad").write_text("")
    monkeypatch.setattr(gmri.gp, "run", lambda *args: None)

    gmri.runCommand(
        "hcp_pre_freesurfer",
        {"studyfolder": str(study), "sessions": "S01", "hcp_gdcoeffs": "coeffs.grad"},
    )

    err = capsys.readouterr().err
    assert "--hcp_gdcoeffs=coeffs.grad" in err
    assert str(study) in err


def test_a_batch_file_typed_from_the_current_folder_is_warned_about_before_it_is_read(
    gmri, layout, monkeypatch, capsys
):
    study, _ = layout
    monkeypatch.chdir(study.parent)

    with pytest.raises(gmri.ge.CommandFailed):
        gmri.runCommand(
            "hcp_pre_freesurfer",
            {"studyfolder": "study", "batchfile": "study/processing/batch.txt"},
        )

    assert "--batchfile=study/processing/batch.txt" in capsys.readouterr().err
    assert os.getcwd() == str(study.parent)


def test_the_banner_says_where_relative_paths_are_taken_from(
    gmri, layout, monkeypatch, capsys
):
    study, _ = layout
    seen = recorded_processing(gmri, monkeypatch)

    gmri.runCommand(
        "hcp_pre_freesurfer", {"studyfolder": str(study), "sessions": "S01"}
    )

    out = capsys.readouterr().out
    assert "relative paths are taken from the study folder: %s\n" % study in out
    assert "\n---> Logs: %s\n" % seen["run"].logfolder in out
    assert out.index("relative paths are taken") < out.index("---> Logs: ")


def test_a_run_started_in_its_study_says_nothing_about_it(
    gmri, layout, monkeypatch, capsys
):
    study, _ = layout
    link = study.parent / "link"
    link.symlink_to(study)
    monkeypatch.chdir(link)
    monkeypatch.setattr(gmri.gp, "run", lambda *args: None)

    gmri.runCommand(
        "hcp_pre_freesurfer", {"studyfolder": str(study), "sessions": "S01"}
    )

    out = capsys.readouterr()
    assert "relative paths are taken from the study folder" not in out.out
    assert "WARNING: Relative paths" not in out.err
    assert "\n---> Logs: %s" % (study / "logs") in out.out, "where it logs, still"


def test_a_study_that_does_not_exist_yet_leaves_the_run_where_it_is(
    gmri, layout, monkeypatch, capsys
):
    _, elsewhere = layout
    called = recorded_utility(gmri, monkeypatch)

    gmri.runCommand("list_dicom", {"studyfolder": "../new", "folder": "x"})

    assert called["cwd"] == str(elsewhere), (
        "an import into a new study takes what it is given from the current "
        "folder, whether or not its logging then creates the study"
    )
    err = capsys.readouterr().err
    assert "does not exist yet" in err
    assert "Each job decides again" not in err, "nothing is scheduled"


def test_a_second_run_into_a_study_its_first_run_only_logged_in_stays_where_it_was(
    gmri, layout, monkeypatch, capsys
):
    """
    The first run's logs are written into the study it names before its
    command runs. A study they alone made is not one a second run takes its
    relative paths from: it used to be, so retrying a call changed its meaning.
    """
    _, elsewhere = layout
    new = elsewhere.parent / "new"
    called = []
    monkeypatch.setattr(
        gmri.gc,
        "run_with_log",
        lambda function, args, run=None, tags=None: (
            called.append(os.getcwd()) or gmri.gc.CallOutcome("call", 0, None, None)
        ),
    )

    for _ in range(2):
        gmri.runCommand("list_dicom", {"studyfolder": "../new", "folder": "x"})
        assert sorted(os.listdir(new)) == ["logs"], "the first run logged in it"

    assert called == [str(elsewhere), str(elsewhere)]
    assert capsys.readouterr().err.count("does not exist yet") == 2


def test_a_scheduled_run_into_a_study_that_does_not_exist_yet_says_its_jobs_decide_again(
    gmri, layout, monkeypatch, capsys
):
    _, elsewhere = layout
    submitted = []
    monkeypatch.setattr(gs, "schedule", lambda **kw: submitted.append(kw) or ("", "1"))

    gmri.runCommand(
        "list_dicom",
        {"studyfolder": "../new", "folder": "x", "scheduler": "SLURM,time=1"},
    )

    err = capsys.readouterr().err
    assert "does not exist yet" in err
    assert "Each job decides again when it starts" in err
    assert submitted[0]["workdir"] == str(elsewhere), "it starts where this one did"


def test_a_relative_log_folder_is_taken_from_a_study_the_header_names(
    gmri, layout, monkeypatch
):
    study, elsewhere = layout
    (elsewhere / "batch.txt").write_text(
        "_studyfolder: %s\n---\nid: S01\nsubject: S01\n01: T1w\n" % study
    )
    seen = recorded_processing(gmri, monkeypatch)

    gmri.runCommand(
        "hcp_pre_freesurfer", {"batchfile": "batch.txt", "logfolder": "logs/mine"}
    )

    assert seen["run"].logfolder == str(study / "logs" / "mine")


def test_the_status_file_is_the_callers(gmri, layout, monkeypatch):
    study, elsewhere = layout
    recorded_utility(gmri, monkeypatch)

    gmri.runCommand(
        "create_batch", {"studyfolder": str(study), "logstatus": "status/01.yaml"}
    )

    assert (elsewhere / "status" / "01.yaml").exists()
    assert not (study / "status").exists()


def test_a_quoted_variable_names_the_study_it_holds(gmri, layout, monkeypatch):
    study, elsewhere = layout
    monkeypatch.setenv("QX_TEST_STUDY", "../study")
    seen = recorded_processing(gmri, monkeypatch)

    gmri.runCommand(
        "hcp_pre_freesurfer",
        {"studyfolder": "$QX_TEST_STUDY", "batchfile": "processing/batch.txt"},
    )

    assert seen["options"]["studyfolder"] == str(study)
    assert not (elsewhere / "$QX_TEST_STUDY").exists()


# --------------------------------------------- one study, however it is asked


@pytest.mark.parametrize(
    "args, header",
    [
        ({}, {}),
        ({"studyfolder": "study"}, {}),
        ({"studyfolder": "../elsewhere/new"}, {}),
        ({}, {"studyfolder": "study"}),
        ({"sessionsfolder": "study/sessions"}, {}),
        ({}, {"sessionsfolder": "study/sessions"}),
        ({"basefolder": "study/sessions"}, {}),
        ({}, {"subjectsfolder": "study/sessions"}),
        ({"sessionsfolder": "sessions"}, {"studyfolder": "study"}),
        ({"studyfolder": "study"}, {"studyfolder": "other"}),
        ({"studyfolder": "study"}, {"sessionsfolder": "other/sessions"}),
        ({"sessionsfolder": "other/sessions"}, {"studyfolder": "study"}),
        ({"logfolder": "study/logs/mine", "folder": "study/sessions/S01"}, {}),
        ({"studyfolder": ""}, {}),
        ({"studyfolder": ""}, {"studyfolder": "study"}),
        ({"sessionsfolder": " "}, {"sessionsfolder": "study/sessions"}),
        ({"studyfolder": "  "}, {}),
        ({}, {"studyfolder": ""}),
    ],
)
def test_the_study_a_run_takes_its_paths_from_is_the_one_the_merge_knows(
    layout, monkeypatch, args, header
):
    """
    What a command is handed and where its run is placed are settled apart:
    the folders by `process.merge_options`, the study the run knows -- the
    one it takes its relative paths from and logs in -- by `placement`. The
    two have to name one study, or a run works in one and logs in another.
    """
    study, elsewhere = layout
    monkeypatch.chdir(elsewhere.parent)
    args = gcs.check_deprecated_parameters(dict(args), "hcp_pre_freesurfer")

    options, sources, _ = gp.merge_options("hcp_pre_freesurfer", dict(args), header)
    placement = gpl.place_run(
        "hcp_pre_freesurfer", args, dict(header), "2026-10-23_10.00.00.000000"
    )

    assert placement.known == (sources["sessionsfolder"] != "default")
    if placement.known:
        assert placement.studyfolder == options["studyfolder"]
