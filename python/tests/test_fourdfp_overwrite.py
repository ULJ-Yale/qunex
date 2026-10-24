#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
`run_nil` and `run_nil_folder` read `--overwrite=no` as no.

Both parsed the option with ``elif overwrite: pass``, which kept any non-empty
string as it was, so the command line's ``"no"`` counted as yes: the existing
params file was rewritten and the processed BOLDs were run again. The NIL
tooling is not installed here, so the external call is replaced with a stub
that records whether it was made.
"""

import pytest

import qx_utilities.general.fourdfp as f4


def make_session(root, name="OP1"):
    """A session with an existing params file and processed BOLD output."""
    session = root / name
    (session / "4dfp" / "bold1").mkdir(parents=True)
    (session / "nii").mkdir()
    (session / "session.txt").write_text(
        f"session: {name}\nsubject: {name}\nraw_data: nii\ndata: 4dfp\n\n"
        "01: T1w\n02: bold1\n"
    )
    (session / "4dfp" / "params").write_text("OLD")
    (session / "4dfp" / "bold1" / f"{name}_b1_faln_dbnd_xr3d_atl.4dfp.img").write_text(
        "x"
    )
    return session


@pytest.fixture
def calls(monkeypatch):
    """Record the external calls run_nil makes instead of making them."""
    made = []

    def call(args, **kwargs):
        made.append(args)
        return 0

    monkeypatch.setattr(f4.subprocess, "call", call)
    return made


@pytest.mark.parametrize("overwrite", ["no", "NO", None, False])
def test_run_nil_without_overwrite_keeps_the_existing_output(tmp_path, calls, overwrite):
    session = make_session(tmp_path)

    f4.run_nil(str(session), overwrite=overwrite)

    assert (session / "4dfp" / "params").read_text() == "OLD"
    assert calls == []


@pytest.mark.parametrize("overwrite", ["yes", True])
def test_run_nil_with_overwrite_redoes_the_session(tmp_path, calls, overwrite):
    session = make_session(tmp_path)

    f4.run_nil(str(session), overwrite=overwrite)

    params = (session / "4dfp" / "params").read_text()
    assert params != "OLD"
    assert "set patid  = OP1" in params
    assert [c[0] for c in calls] == ["preproc_avi_nifti"]


def test_run_nil_folder_without_overwrite_keeps_the_existing_output(tmp_path, calls):
    sessions = [make_session(tmp_path, "OP1"), make_session(tmp_path, "OP2")]

    f4.run_nil_folder(folder=str(tmp_path), pattern="OP*", overwrite="no")

    for session in sessions:
        assert (session / "4dfp" / "params").read_text() == "OLD"
    assert calls == []


def test_run_nil_folder_with_overwrite_redoes_every_session(tmp_path, calls):
    sessions = [make_session(tmp_path, "OP1"), make_session(tmp_path, "OP2")]

    f4.run_nil_folder(folder=str(tmp_path), pattern="OP*", overwrite="yes")

    for session in sessions:
        assert (session / "4dfp" / "params").read_text() != "OLD"
    assert len(calls) == 2
