#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
`bruker_to_dicom --archive` with a stub `dicomifier` on PATH.

- ``--archive=copy`` called `shutil.copy2` on a dataset, which is a folder, so
  it could never copy one.
- A dataset already in the archive raised out of the archive loop (a
  `FileExistsError` for copy, a `shutil.Error` for move): the datasets after it
  were not archived, and the failed conversions were never reported. Each
  archive failure is now logged and one `CommandFailed` after the loop names the
  failed conversions and the failed archiving together.
- The conversions come back in the order they finish, and were matched to
  their datasets by position, so with ``parelements`` above 1 a dataset whose
  conversion failed could be archived or deleted.
"""

import os
import stat

import pytest

import qx_utilities.general.bruker as br
import qx_utilities.general.exceptions as ge

# fails the datasets named c_*
DICOMIFIER = """#!/bin/sh
case "$3" in
    */c_*) exit 1 ;;
esac
exit 0
"""


@pytest.fixture
def dicomifier(tmp_path, monkeypatch):
    """Put a stub dicomifier first on PATH."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    stub = bindir / "dicomifier"
    stub.write_text(DICOMIFIER)
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    return stub


def make_study(root, datasets=("a_ok", "b_ok", "c_fail"), archived=()):
    """A study with bruker datasets in its inbox, some already archived."""
    sessions = root / "study" / "sessions"
    for name in datasets:
        folder = sessions / "inbox" / "bruker" / name
        folder.mkdir(parents=True)
        (folder / "f").write_text("x")
    for name in archived:
        (sessions / "archive" / "bruker" / name).mkdir(parents=True)
    return root / "study", sessions


def run(study, archive, parelements=3):
    with pytest.raises(ge.CommandFailed) as raised:
        br.bruker_to_dicom(
            studyfolder=str(study), archive=archive, parelements=parelements
        )
    return " ".join(str(e) for e in raised.value.report)


def test_copy_archives_each_dataset_folder(tmp_path, dicomifier):
    study, sessions = make_study(tmp_path, datasets=("a_ok", "b_ok"))

    br.bruker_to_dicom(studyfolder=str(study), archive="copy")

    for name in ("a_ok", "b_ok"):
        assert (sessions / "archive" / "bruker" / name / "f").read_text() == "x"
        assert (sessions / "inbox" / "bruker" / name / "f").exists()


def test_copy_into_an_existing_archive_is_reported(tmp_path, dicomifier):
    study, sessions = make_study(tmp_path, archived=("a_ok",))

    report = run(study, "copy")

    # one failure for the conversion and one for the archiving, both named
    assert "c_fail" in report
    assert "a_ok" in report
    assert "b_ok" not in report
    archive = sessions / "archive" / "bruker"
    # the dataset after the one that could not be archived still is
    assert (archive / "b_ok" / "f").exists()
    # and a failed conversion is never archived
    assert not (archive / "c_fail").exists()


def test_move_into_an_existing_archive_is_reported(tmp_path, dicomifier):
    study, sessions = make_study(tmp_path, archived=("a_ok",))

    report = run(study, "move")

    assert "c_fail" in report
    assert "a_ok" in report
    assert "b_ok" not in report
    inbox = sessions / "inbox" / "bruker"
    archive = sessions / "archive" / "bruker"
    assert (archive / "b_ok" / "f").exists()
    assert not (inbox / "b_ok").exists()
    # the one that could not be moved, and the failed conversion, stay
    assert (inbox / "a_ok" / "f").exists()
    assert (inbox / "c_fail" / "f").exists()
    assert not (archive / "c_fail").exists()


def test_a_failed_conversion_is_not_deleted(tmp_path, monkeypatch):
    """The results are matched to the datasets by name, not by position."""
    study, sessions = make_study(tmp_path, datasets=("a_ok", "c_fail"))

    def finished_in_reverse(calls, cores=None, _log=None):
        # the conversions come back in the opposite order to the one they
        # were started in, as they can with parelements above 1
        return [
            {
                "name": call["name"],
                "exit": 1 if call["name"].endswith("c_fail") else 0,
                "log": call["sout"],
                "args": call["args"],
            }
            for call in reversed(calls)
        ]

    monkeypatch.setattr(br.gc, "run_external_parallel", finished_in_reverse)

    report = run(study, "delete", parelements=2)

    assert "c_fail" in report
    assert "a_ok" not in report
    inbox = sessions / "inbox" / "bruker"
    assert (inbox / "c_fail" / "f").exists()
    assert not (inbox / "a_ok").exists()
