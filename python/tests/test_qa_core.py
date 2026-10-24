#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
`run_qa` with --sessions or --batchfile.

`QA.build_slist` takes its sessions from `gc.resolve_sessions`, which returns a
`SessionList`, and that list's `copy()` is deep. The session folder was set on
the elements of a copy, so the list that came back had none, and `qa_raw_data`
raised ``KeyError: 'QA_sessionfolder'``. A listed session without a folder was
failed before `__init__` had set `slist` and `failQA`, which raised
``AttributeError``. Running over every session (neither option given) never
went through that branch, which is why it went unnoticed.
"""

from qx_utilities.qa import core as qa
from qx_utilities.qa.run_qa import run_qa


def make_study(root, sessions=("s1",)):
    """A study with one importable session folder per id."""
    study = root / "study"
    for sid in sessions:
        session = study / "sessions" / sid
        (session / "nii").mkdir(parents=True)
        (session / "session.txt").write_text(
            f"session: {sid}\nsubject: {sid}\nraw_data: nii\n\n01: T1w\n"
        )
    (study / "processing").mkdir(parents=True, exist_ok=True)
    return study


def read_lists(study):
    """The pass and fail lists run_qa writes to the study's processing folder."""
    lists = study / "processing" / "lists"
    return (
        (lists / "QA_pass_raw_data.list").read_text(),
        (lists / "QA_fail_raw_data.list").read_text(),
    )


def test_listed_sessions_get_their_session_folder(tmp_path):
    study = make_study(tmp_path, ("s1", "s2"))
    q = qa.QA("s1", str(study / "sessions"))

    assert isinstance(q.slist, list)
    assert [s["id"] for s in q.slist] == ["s1"]
    assert q.slist[0]["QA_sessionfolder"] == str(study / "sessions" / "s1")
    assert q.failQA == []


def test_a_listed_session_without_a_folder_fails_qa(tmp_path):
    study = make_study(tmp_path, ("s1",))
    q = qa.QA("s1,s2", str(study / "sessions"))

    assert [s["id"] for s in q.slist] == ["s1"]
    assert [s["id"] for s in q.failQA] == ["s2"]
    assert "Session s2 has failed" in q.report


def test_run_qa_with_sessions(tmp_path):
    study = make_study(tmp_path, ("s1", "s2"))

    run_qa(datatype="raw_data", studyfolder=str(study), sessions="s1")

    passed, failed = read_lists(study)
    assert "session id: s1" in passed
    assert "s2" not in passed
    assert failed.strip() == ""


def test_run_qa_with_a_batch_file(tmp_path):
    study = make_study(tmp_path, ("s1", "s2"))
    batch = study / "processing" / "batch.txt"
    batch.write_text(
        "# a qunex batch file\n_hcp_brainsize: 150\n---\nsession: s1\nsubject: s1\n\n---\nsession: s3\nsubject: s3\n"
    )

    run_qa(datatype="raw_data", studyfolder=str(study), batchfile=str(batch))

    passed, failed = read_lists(study)
    assert "session id: s1" in passed
    assert "s2" not in passed
    # s3 is in the batch file but has no session folder
    assert "session id: s3" in failed
