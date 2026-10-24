# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for the study utilities that pick sessions out of a sessions folder
themselves: which sessions `copy_study` copies, and which folders
`gather_behavior` takes for sessions when it is given none.

Both read the folder as it is laid out, and a sessions folder holds more than
sessions: `inbox`, `archive`, `specs` and `QC` are never sessions, whatever
they hold.
"""

import os
import shutil

import pytest

import qx_utilities.general.core as gc
import qx_utilities.general.utilities as gu


def make_study(root, sessions=("OP1", "OP2", "OP10"), legacy=True):
    """
    A study with session folders whose session files name a subject each, a
    batch file over all of them, and -- in the legacy layout -- the folders
    of the sessions folder that are not sessions.
    """
    study = root / "study"
    (study / "processing").mkdir(parents=True)
    (study / ".qunexstudy").write_text("")
    if legacy:
        for folder in ["inbox/MR", "inbox/behavior", "archive/behavior", "specs", "QC"]:
            (study / "sessions" / folder).mkdir(parents=True)

    batch = "# header\n_hcp_brainsize: 170\n"
    for session in sessions:
        folder = study / "sessions" / session
        folder.mkdir(parents=True)
        (folder / "session.txt").write_text(
            "session: %s\nsubject: %s\nhcp: hcp\n" % (session, session)
        )
        batch += "\n---\nsession: %s\nsubject: %s\nhcp: hcp\n" % (session, session)
    (study / "processing" / "batch.txt").write_text(batch)
    return study


# ------------------------------------------------------------------------------
#                                                     what copy_study selects


@pytest.mark.parametrize(
    "sessions", ["OP1|OP2", "OP1 OP2", "OP1, OP2", "OP1,OP2"]
)
def test_copy_study_reads_the_sessions_the_way_every_command_does(tmp_path, sessions):
    """
    Without a batch file `--sessions` was split on commas alone: `OP1|OP2`
    named one session that did not exist, so nothing was copied, and every
    session block was then removed from the batch files of the new study.
    """
    study = make_study(tmp_path)

    selected, subjects, batch_subjects = gu._copy_study_selection(
        str(study), sessions, None, None, None
    )

    assert selected == ["OP1", "OP2"]
    assert subjects is None and batch_subjects is None


def test_copy_study_expands_a_glob_over_the_session_folders(tmp_path):
    study = make_study(tmp_path)

    selected, _, _ = gu._copy_study_selection(str(study), "OP*", None, None, None)

    assert selected == ["OP1", "OP10", "OP2"]


def test_copy_study_never_takes_a_folder_that_holds_no_session(tmp_path):
    study = make_study(tmp_path)

    selected, _, _ = gu._copy_study_selection(str(study), "*", None, None, None)

    assert selected == ["OP1", "OP10", "OP2"], "not inbox, archive, specs or QC"
    assert gu._select_session_folders(
        str(study / "sessions"), ["inbox", "archive", "specs", "QC"]
    ) == []


def test_copy_study_names_a_session_it_can_not_find(tmp_path, capsys):
    study = make_study(tmp_path)

    selected, _, _ = gu._copy_study_selection(
        str(study), "OP1,OP3,OP1", None, None, None
    )

    assert selected == ["OP1"], "nothing for OP3, and OP1 once"
    out = capsys.readouterr().out
    assert "WARNING: no session in %s matches OP3" % (study / "sessions") in out
    assert "matches OP1" not in out


def test_copy_study_of_a_missing_sessions_folder_selects_nothing(tmp_path, capsys):
    assert gu._select_session_folders(str(tmp_path / "none"), ["OP1"]) == []
    assert "matches OP1" in capsys.readouterr().out


@pytest.mark.skipif(shutil.which("rsync") is None, reason="copy_study needs rsync")
def test_copy_study_copies_the_sessions_named_with_pipes(tmp_path):
    study = make_study(tmp_path)
    new = tmp_path / "new"

    gu.copy_study(studyfolder=str(new), existing_study=str(study), sessions="OP1|OP2")

    copied = sorted(os.listdir(new / "sessions"))
    assert "OP1" in copied and "OP2" in copied
    assert "OP10" not in copied
    assert {"inbox", "archive", "specs", "QC"} <= set(copied), (
        "the folders that are not sessions go with the selected sessions"
    )

    sessions, header = gc.read_batch(str(new / "processing" / "batch.txt"))
    assert [s["id"] for s in sessions] == ["OP1", "OP2"], "OP10's block is removed"
    assert header == {"hcp_brainsize": "170"}


# ------------------------------------------------------------------------------
#                                          the sessions gather_behavior finds


def test_gather_behavior_finds_only_sessions_in_a_legacy_study(tmp_path, capsys):
    """
    With no sessions given, gather_behavior took every folder holding a
    `behavior` folder for a session, and in the legacy layout that is `inbox`
    and `archive` as well: the default check then failed the call on them, and
    files waiting in the inbox became a row of the group file.
    """
    study = make_study(tmp_path, sessions=("OP1", "OP2"))
    sessionsfolder = study / "sessions"
    for session in ["OP1", "OP2"]:
        (sessionsfolder / session / "behavior").mkdir()
        (sessionsfolder / session / "behavior" / "x_behavior.txt").write_text(
            "a\tb\n1\t2\n"
        )
    (sessionsfolder / "inbox" / "behavior" / "raw_behavior.txt").write_text(
        "a\tb\n9\t9\n"
    )
    (sessionsfolder / "archive" / "behavior" / "old_behavior.txt").write_text(
        "a\tb\n8\t8\n"
    )

    # check="yes" is the default, and failed the call on inbox and archive
    gu.gather_behavior(studyfolder=str(study), sourcefiles="*_behavior.txt")

    target = sessionsfolder / "inbox" / "behavior" / "behavior.txt"
    rows = [
        line.split("\t")[0]
        for line in target.read_text().split("\n")
        if line and not line.startswith("#")
    ]
    assert rows == ["session id", "OP1", "OP2"]

    out = capsys.readouterr().out
    assert "archive" not in out and "\n     inbox" not in out


def test_the_sessions_with_an_entry_leave_out_what_is_not_a_session(tmp_path):
    study = make_study(tmp_path, sessions=("OP1", "OP2"))
    for folder in ["OP1", "inbox", "archive", "specs", "QC"]:
        (study / "sessions" / folder / "behavior").mkdir(exist_ok=True)

    assert gu._sessions_with(str(study / "sessions"), ["behavior"]) == "OP1"
    assert gu._sessions_with(str(study / "sessions"), ["session.txt"]) == "OP1|OP2"


# ------------------------------------------------------------------------------
#                                                                  check_study


def test_check_study_finds_the_study_and_creates_nothing(tmp_path):
    """
    Its notes said it created the standard folders it found missing; it never
    did, and says now that it only finds the study.
    """
    study = make_study(tmp_path, sessions=("OP1",), legacy=False)
    before = sorted(str(p) for p in study.rglob("*"))

    found = gu.check_study(startfolder=str(study / "sessions" / "OP1"))

    assert found == str(study)
    assert sorted(str(p) for p in study.rglob("*")) == before
    assert gu.check_study(startfolder=str(tmp_path)) is None
