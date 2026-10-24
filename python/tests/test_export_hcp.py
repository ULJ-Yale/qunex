#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
`export_hcp --mapexclude` excludes a file whatever is at its target.

The exclusion was tested only for files whose target did not exist yet. A file
whose target existed was put on the "existing" list first, and with
``--overwrite=yes`` that list was removed and mapped again, so an excluded file
was overwritten.

The full record of a mapping is kept with the run's other logs, in the
``comlogs`` folder of the log folder ``gmri`` hands the command. It used to go
to ``<study>/processing/logs/comlogs``, a folder no other run of the study
logged in.
"""

import os

import pytest

import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl
from qx_utilities.hcp.export_hcp import export_hcp


@pytest.fixture(autouse=True)
def default_settings():
    """Whether a comlog is kept is read from the process-wide settings."""
    gl.set_active(None)
    yield
    gl.set_active(None)


def make_export(root, existing=("a.nii",)):
    """A study with one session's HCP T1w folder, and an export target that
    already holds the named files."""
    study = root / "study"
    source = study / "sessions" / "s1" / "hcp" / "s1" / "T1w"
    source.mkdir(parents=True)
    for name in ("a.nii", "b.nii", "c.nii"):
        (source / name).write_text("new")
    (study / "sessions" / "s1" / "session.txt").write_text(
        "session: s1\nsubject: s1\nhcp: hcp\n"
    )
    target = root / "out" / "s1" / "T1w"
    target.mkdir(parents=True)
    for name in existing:
        (target / name).write_text("old")
    return study, root / "out", target


@pytest.mark.parametrize("overwrite", ["yes", "no", "skip"])
def test_an_excluded_file_is_left_alone_when_its_target_exists(tmp_path, overwrite):
    study, out, target = make_export(tmp_path)

    export_hcp(
        studyfolder=str(study),
        sessions="s1",
        mapaction="copy",
        mapto=str(out),
        overwrite=overwrite,
        mapexclude="a.nii",
    )

    assert (target / "a.nii").read_text() == "old"
    assert (target / "b.nii").read_text() == "new"
    assert (target / "c.nii").read_text() == "new"


def test_overwrite_still_replaces_a_file_that_is_not_excluded(tmp_path):
    study, out, target = make_export(tmp_path, existing=("a.nii", "c.nii"))

    export_hcp(
        studyfolder=str(study),
        sessions="s1",
        mapaction="copy",
        mapto=str(out),
        overwrite="yes",
        mapexclude="a.nii",
    )

    assert (target / "a.nii").read_text() == "old"
    assert (target / "c.nii").read_text() == "new"


def test_skip_keeps_a_file_that_is_not_excluded(tmp_path):
    study, out, target = make_export(tmp_path, existing=("a.nii", "c.nii"))

    export_hcp(
        studyfolder=str(study),
        sessions="s1",
        mapaction="copy",
        mapto=str(out),
        overwrite="skip",
        mapexclude="a.nii",
    )

    assert (target / "a.nii").read_text() == "old"
    assert (target / "c.nii").read_text() == "old"
    assert (target / "b.nii").read_text() == "new"


# ------------------------------------------------------- the mapping's record


def test_the_mapping_record_is_in_the_run_s_comlogs(tmp_path):
    study, out, target = make_export(tmp_path, existing=())
    run = tmp_path / "logs" / "run"

    export_hcp(
        studyfolder=str(study),
        sessions="s1",
        mapaction="copy",
        mapto=str(out),
        logfolder=str(run),
    )

    records = os.listdir(run / "comlogs")
    assert len(records) == 1 and records[0].startswith("done_export_hcp_mapping_")
    record = (run / "comlogs" / records[0]).read_text()
    for name in ("a.nii", "b.nii", "c.nii"):
        assert str(target / name) in record, "every file, whatever --verbose says"
    assert not (study / "processing").exists(), (
        "nothing goes to the study's processing/logs any more"
    )


def test_without_a_run_folder_no_mapping_record_is_written(tmp_path, monkeypatch):
    study, out, target = make_export(tmp_path, existing=())
    monkeypatch.chdir(tmp_path)

    export_hcp(studyfolder=str(study), sessions="s1", mapaction="copy", mapto=str(out))

    assert (target / "b.nii").read_text() == "new", "the mapping still ran"
    assert sorted(os.listdir(tmp_path)) == ["out", "study"]
    assert sorted(os.listdir(study)) == ["sessions"]


def test_a_run_that_keeps_no_comlogs_keeps_no_mapping_record(tmp_path):
    study, out, _ = make_export(tmp_path, existing=())
    run = tmp_path / "logs" / "run"
    gl.set_active(gl.LogSettings(comlog=False))

    export_hcp(
        studyfolder=str(study),
        sessions="s1",
        mapaction="copy",
        mapto=str(out),
        logfolder=str(run),
    )

    assert not run.exists()


@pytest.mark.parametrize("logged", [True, False], ids=["a record", "no record"])
def test_a_failed_mapping_names_its_record_only_when_one_was_kept(tmp_path, logged):
    """With no record, the hint used to name a log called `None`."""
    study, out, _ = make_export(tmp_path)
    run = tmp_path / "logs" / "run"

    with pytest.raises(ge.CommandFailed) as failure:
        export_hcp(
            studyfolder=str(study),
            sessions="s1",
            mapaction="copy",
            mapto=str(out),
            overwrite="no",
            logfolder=str(run) if logged else None,
        )

    assert failure.value.error == "Target files exist"
    hint = failure.value.hints[-1]
    if logged:
        (record,) = os.listdir(run / "comlogs")
        assert record.startswith("error_export_hcp_mapping_")
        assert str(run / "comlogs" / record) in hint
    else:
        assert hint == "Please check your data and the log of this run!"
