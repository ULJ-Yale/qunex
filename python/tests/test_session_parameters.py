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
    # the legacy pair, as user scripts and recipes still spell it
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


def test_a_deprecated_name_for_one_session_means_what_it_means_elsewhere(capsys):
    """
    The per-session tier applied `_TR:` as written, so it set an option
    nothing reads, while the same name in the header or on the command line
    is remapped to `tr`.
    """
    options = {"tr": 2.5, "command_ran": "preprocess_bold"}

    soptions, ssources = gcs.update_options(
        {"id": "S01", "_TR": "2.0", "--hcp_brainsize": "170"}, options, {}
    )

    assert soptions["tr"] == "2.0"
    assert "TR" not in soptions
    assert ssources["tr"] == gcs.PER_SESSION
    assert soptions["hcp_brainsize"] == "170"


@pytest.mark.parametrize("spelling", ["TR", "tr"])
def test_a_deprecated_name_for_one_session_is_unset_in_either_spelling(spelling):
    options = {
        "tr": 2.5,
        "command_ran": "preprocess_bold",
        gcs.UNSET_BATCH_SESSION: spelling,
    }

    soptions, _ = gcs.update_options({"id": "S01", "_TR": "2.0"}, options, {})

    assert soptions["tr"] == 2.5


@pytest.mark.parametrize("name", ["hcp_bold_sequencetype", "hcp_biascorrect_t1w"])
def test_a_parameter_no_longer_used_is_dropped_and_never_stored_under_none(
    name, capsys
):
    """
    The table maps a name that is no longer used to None. Only an empty value
    was taken to mean that, so a stated one was stored under the key None.
    """
    options = gcs.check_deprecated_parameters(
        {name: "interleaved", "hcp_brainsize": "170"}, "hcp_fmri_volume"
    )

    assert options == {"hcp_brainsize": "170"}
    assert None not in options
    out = capsys.readouterr().out
    assert "no longer used" in out and "... %s" % name in out


def test_a_parameter_no_longer_used_for_one_session_does_not_break_its_report(
    capsys,
):
    """
    A batch file entry `_hcp_bold_sequencetype: interleaved` reached the
    per-session tier as the key None, and the session's parameter report,
    which sorts the names that tier states, failed on comparing None with a
    string: every processing run over such a batch file crashed.
    """
    options = {"command_ran": "hcp_fmri_volume", "hcp_brainsize": 150}
    session = {
        "id": "S01",
        "_hcp_bold_sequencetype": "interleaved",
        "_hcp_brainsize": "170",
    }

    soptions, ssources = gcs.update_options(
        session, options, {"hcp_brainsize": "default"}
    )

    assert None not in soptions and None not in ssources
    assert "hcp_bold_sequencetype" not in soptions
    assert soptions["hcp_brainsize"] == "170"
    assert ssources["hcp_brainsize"] == gcs.PER_SESSION

    class Command:
        name = "hcp_fmri_volume"

    report = gcs.report_parameters(Command(), soptions, ssources, session=session)
    assert "on session S01" in report
    assert "hcp_brainsize" in report and "hcp_bold_sequencetype" not in report
