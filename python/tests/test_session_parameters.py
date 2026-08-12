#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
The encoding front door — `general/commands_support.normalize_session_parameters`.

QuNex accepted three encodings of "which batch file, which sessions": the legacy
`sessions=<path>` plus `sessionids=<ids>`, the modern `batchfile=<path>` plus
`sessions=<ids>`, and a bare `sessions=<ids>`. They all arrive here and leave as
one form, so that `resolve_sessions` is handed a batch file and a session
specification as two separate parameters.
"""

import os

import pytest

import qx_utilities.general.commands_support as gcs
from qx_utilities.general.exceptions import CommandError

BATCH = os.path.join("study", "processing", "batch.txt")


def normalize(**options):
    return gcs.normalize_session_parameters(dict(options), "test_command")


# ==============================================================================
#                                                     is this a path or is it not


@pytest.mark.parametrize(
    "value",
    [
        BATCH,
        "/absolute/batch.txt",
        "batch.txt",
        "processing/batch",
        "batch.yaml",
    ],
)
def test_batchfile_paths_are_recognised(value):
    assert gcs.is_batchfile_path(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        "",
        "   ",
        "S01",
        "S01,S02",
        "S01|S02",
        "S01 S02",
        "AP*",
        "sessions.list",
        "/study/sessions/sessions.list",
        "/study/one.txt,/study/two.txt",
    ],
)
def test_session_specifications_are_not_paths(value):
    assert not gcs.is_batchfile_path(value)


# ==============================================================================
#                                                        the three encodings in


def test_legacy_encoding_is_remapped(capsys):
    options = normalize(sessions=BATCH, sessionids="S01,S02")

    assert options == {"batchfile": BATCH, "sessions": "S01,S02"}
    warnings = capsys.readouterr().out
    assert "sessions parameter is deprecated" in warnings
    assert "sessionids parameter is deprecated" in warnings


def test_modern_encoding_is_left_alone(capsys):
    options = normalize(batchfile=BATCH, sessions="S01,S02", filter="group:control")

    assert options == {
        "batchfile": BATCH,
        "sessions": "S01,S02",
        "filter": "group:control",
    }
    assert capsys.readouterr().out == ""


def test_sessions_alone_are_left_alone(capsys):
    assert normalize(sessions="S01,S02") == {"sessions": "S01,S02"}
    assert capsys.readouterr().out == ""


def test_batchfile_alone_is_left_alone(capsys):
    assert normalize(batchfile=BATCH) == {"batchfile": BATCH}
    assert capsys.readouterr().out == ""


def test_sessionids_alone_becomes_sessions(capsys):
    assert normalize(sessionids="S01,S02") == {"sessions": "S01,S02"}
    assert "sessionids parameter is deprecated" in capsys.readouterr().out


def test_a_list_file_stays_a_session_specification(capsys):
    options = normalize(sessions="/study/sessions.list")

    assert options == {"sessions": "/study/sessions.list"}
    assert capsys.readouterr().out == ""


# ==============================================================================
#                                                              the ambiguous ones


def test_batch_file_through_both_parameters_is_an_error():
    with pytest.raises(CommandError):
        normalize(batchfile=BATCH, sessions="other.txt")


def test_two_different_session_specifications_are_an_error():
    with pytest.raises(CommandError):
        normalize(sessions="S01", sessionids="S02")


def test_the_same_session_specification_twice_is_not(capsys):
    # qunex.sh sets both from the same value on its way to the SLURM array check
    assert normalize(sessions="S01,S02", sessionids="S01,S02") == {
        "sessions": "S01,S02"
    }


@pytest.mark.parametrize("empty", ["", "   "])
def test_an_empty_sessionids_is_no_sessionids(empty, capsys):
    # qunex.sh passes every parameter it knows of, set or not
    assert normalize(sessions="S01", sessionids=empty) == {"sessions": "S01"}
    assert capsys.readouterr().out == ""


def test_an_empty_sessionids_next_to_a_batch_file(capsys):
    options = normalize(sessions=BATCH, sessionids="")

    assert options == {"batchfile": BATCH}
    assert "sessionids" not in capsys.readouterr().out


def test_promotion_to_an_error_is_one_constant(monkeypatch):
    monkeypatch.setattr(gcs, "SESSIONS_AS_BATCHFILE_IS_ERROR", True)

    with pytest.raises(CommandError):
        normalize(sessions=BATCH, sessionids="S01")


# ==============================================================================
#                                                   through check_deprecated_parameters


def test_the_front_door_runs_it(capsys):
    # run_turnkey's internal calls, verbatim
    options = gcs.check_deprecated_parameters(
        {"sessions": BATCH, "sessionids": "S01", "sessionsfolder": "/study/sessions"},
        "hcp_pre_freesurfer",
    )

    assert options == {
        "batchfile": BATCH,
        "sessions": "S01",
        "sessionsfolder": "/study/sessions",
    }


def test_subjid_maps_to_sessions_for_export_hcp():
    assert gcs.check_deprecated_parameters({"subjid": "S01"}, "export_hcp") == {
        "sessions": "S01"
    }


def test_subjid_maps_to_sessionid_everywhere_else():
    assert gcs.check_deprecated_parameters({"subjid": "S01"}, "import_dicom") == {
        "sessionid": "S01"
    }
