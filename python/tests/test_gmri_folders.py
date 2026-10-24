# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for the folders ``gmri`` runs a command in: the study folder, the
sessions folder derived from it or named instead, and the sessions' own
folders, which session and batch files record relative to each session.

``gmri`` is a script without a ``.py`` extension, so it is loaded by path.
"""

import importlib.machinery
import importlib.util
import os
from pathlib import Path

import pytest

import qx_utilities.general.log.context as glc
import qx_utilities.general.log.settings as gls

from .test_gmri_dispatch import reported_as

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


@pytest.fixture(scope="module")
def gmri():
    path = os.path.join(os.path.dirname(__file__), "..", "qx_utilities", "gmri")
    loader = importlib.machinery.SourceFileLoader("gmri_folders_under_test", path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def relative_study(tmp_path, header, sessions=("S01",)):
    """
    A study, and a batch file outside it whose sessions record their folders
    relative to their session folders, as session files are written now.
    """
    study = tmp_path / "study"
    for session in sessions:
        (study / "sessions" / session).mkdir(parents=True)
    (study / ".qunexstudy").write_text("")

    batch = tmp_path / "batch.txt"
    batch.write_text(
        header
        + "".join(
            "---\nid: %s\nsubject: %s\nhcp: hcp\nraw_data: nii\n01: T1w\n"
            % (session, session)
            for session in sessions
        )
    )
    return study, batch


def recorded_call(gmri, monkeypatch):
    """Stubs a single utility call, and returns what it was called with."""
    called = {}

    def record(function, args, run=None, tags=None):
        called.update(args, run=run)
        return gmri.gc.CallOutcome("call", 0, None, None)

    monkeypatch.setattr(gmri.gc, "run_with_log", record)
    return called


def test_a_utility_works_in_the_sessions_folder_of_the_study_it_is_given(
    gmri, tmp_path, monkeypatch, capsys
):
    study, _ = relative_study(tmp_path, "_hcp_brainsize: 170\n")
    called = recorded_call(gmri, monkeypatch)

    gmri.runCommand("import_dicom", {"studyfolder": str(study)})

    assert called["sessionsfolder"] == str(study / "sessions")
    assert called["run"].logfolder.startswith(str(study / "logs"))
    assert reported_as(capsys.readouterr().out, "sessionsfolder").startswith(
        "studyfolder"
    ), "the banner says the folder was derived from the study folder"


@pytest.mark.parametrize("where", ["command line", "batch file"])
def test_a_named_sessions_folder_wins_over_the_study_folder(
    gmri, tmp_path, monkeypatch, where
):
    mine = tmp_path / "mine"
    mine.mkdir()
    header = "_sessionsfolder: %s\n" % mine if where == "batch file" else "_x: 1\n"
    study, batch = relative_study(tmp_path, header)

    args = {"studyfolder": str(study), "batchfile": str(batch)}
    if where == "command line":
        args["sessionsfolder"] = str(mine)

    called = recorded_call(gmri, monkeypatch)
    gmri.runCommand("import_dicom", args)

    assert called["sessionsfolder"] == str(mine), (
        "a sessions folder named anywhere beats one derived from the study"
    )


def test_a_batch_file_that_names_its_study_names_its_sessions_folder(
    gmri, tmp_path, monkeypatch
):
    study, batch = relative_study(tmp_path, "_studyfolder: %s\n" % (tmp_path / "study"))
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    called = recorded_call(gmri, monkeypatch)
    gmri.runCommand("import_dicom", {"batchfile": str(batch)})

    assert called["sessionsfolder"] == str(study / "sessions")


def test_a_bash_command_is_given_the_sessions_folder_of_the_study(
    gmri, tmp_path, monkeypatch
):
    study, _ = relative_study(tmp_path, "_x: 1\n", sessions=("S01", "S02"))
    calls = []
    monkeypatch.setattr(
        gmri.gb,
        "run",
        lambda qx_command, args, run=None, session=None: calls.append(
            (dict(args), session)
        )
        or 0,
    )

    gmri.runCommand("dwi_dtifit", {"studyfolder": str(study), "sessions": "S0*"})

    assert [session for _, session in calls] == ["S01", "S02"], (
        "the ids are globbed in the study's sessions folder"
    )
    assert calls[0][0]["sessionsfolder"] == str(study / "sessions")


@pytest.mark.parametrize("named", ["by the batch file", "on the command line"])
def test_the_sessions_folders_are_resolved_where_the_run_works(
    gmri, tmp_path, monkeypatch, named
):
    """
    A session's folders are read back against the sessions folder the run
    works on, which the batch file's header can name: they are resolved only
    once the header has been read.
    """
    if named == "by the batch file":
        header = "_sessionsfolder: %s\n" % (tmp_path / "study" / "sessions")
        study, batch = relative_study(tmp_path, header)
        args = {"batchfile": str(batch)}
    else:
        study, batch = relative_study(tmp_path, "_x: 1\n")
        args = {"batchfile": str(batch), "studyfolder": str(study)}

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    seen = {}
    monkeypatch.setattr(
        gmri.gp,
        "run",
        lambda qx_command, args, sessions, options, sources, run: seen.update(
            sessions=sessions, options=options
        ),
    )
    gmri.runCommand("hcp_pre_freesurfer", args)

    session = seen["sessions"][0]
    assert session["hcp"] == str(study / "sessions" / "S01" / "hcp")
    assert session["raw_data"] == str(study / "sessions" / "S01" / "nii")
    assert seen["options"]["studyfolder"] == str(study)


def test_a_session_by_session_utility_runs_where_it_is_told(
    gmri, tmp_path, monkeypatch
):
    """
    A batch file with a header and no folder named anywhere used to fail with a
    TypeError: the folders were deduced again from the header, which dropped
    the current folder the run had fallen back on.
    """
    study, batch = relative_study(tmp_path, "_hcp_brainsize: 170\n")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    calls = []

    def run_in_parallel(issued, cores=None, prepend="", run=None):
        calls.extend(issued)
        return [gmri.gc.CallOutcome(call["name"], 0, None, None) for call in issued]

    monkeypatch.setattr(gmri.gc, "run_in_parallel", run_in_parallel)

    gmri.runCommand("setup_hcp", {"batchfile": str(batch)})
    assert calls[0]["args"]["sourcefolder"] == str(elsewhere / "S01")

    calls.clear()
    gmri.runCommand("setup_hcp", {"batchfile": str(batch), "studyfolder": str(study)})
    assert calls[0]["args"]["sourcefolder"] == str(study / "sessions" / "S01")


def test_a_processing_run_that_names_no_folder_says_where_it_works(
    gmri, tmp_path, monkeypatch, capsys
):
    study, batch = relative_study(tmp_path, "_hcp_brainsize: 170\n")
    monkeypatch.chdir(study / "sessions")
    monkeypatch.setattr(gmri.gp, "run", lambda *args: None)

    gmri.runCommand("hcp_pre_freesurfer", {"batchfile": str(batch)})
    assert "Neither --studyfolder nor --sessionsfolder" in capsys.readouterr().err

    gmri.runCommand(
        "hcp_pre_freesurfer", {"batchfile": str(batch), "studyfolder": str(study)}
    )
    assert "Neither" not in capsys.readouterr().err


def test_the_study_folder_reaches_only_a_command_that_takes_it(gmri):
    def command(sessionsfolder=None):
        pass

    args = {"studyfolder": "/s", "sessionsfolder": "/s/sessions"}
    gmri.gc._drop_run_parameters(command, args)

    assert args == {"sessionsfolder": "/s/sessions"}


def test_a_group_run_over_a_batch_file_hands_the_script_its_sessions(
    gmri, tmp_path, monkeypatch
):
    """
    A script run once over all the sessions was given the batch file they came
    from, which it is not passed, and no sessions: `compute_bold_fc` group runs
    named by a batch file stopped on a missing --sessions.
    """
    study, batch = relative_study(tmp_path, "_x: 1\n", sessions=("S01", "S02"))
    calls = []
    monkeypatch.setattr(
        gmri.gb,
        "run",
        lambda qx_command, args, run=None, session=None: calls.append(
            (dict(args), session)
        )
        or 0,
    )

    gmri.runCommand(
        "compute_bold_fc",
        {"batchfile": str(batch), "studyfolder": str(study), "runtype": "group"},
    )

    assert len(calls) == 1 and calls[0][1] is None, "one call for the group"
    assert calls[0][0]["sessions"] == "S01,S02"
