# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
MSMAll and DeDriftAndResample dry-run tests for the HCP processing commands.

Split from ``test_hcp_dryrun.py``: with ``--test`` the MSMAll and
DeDriftAndResample commands are checked for the options they hand on, the
BOLDs they select, the names they report under and the ICA-FIX group rules.
"""

import os

import pytest

from qx_utilities.hcp.hcp_dedrift_and_resample import hcp_dedrift_and_resample
from qx_utilities.hcp.hcp_icafix import hcp_icafix
from qx_utilities.hcp.hcp_msmall import hcp_msmall

from .utils import build_hcp_session, default_options

# ------------------------------------------- MSMAll, and DeDriftAndResample


@pytest.fixture
def msmall_session(tmp_path, monkeypatch):
    """
    A session with two BOLDs and their single-run ICA-FIX outputs, at the
    default high-pass of 2000, so a dry run reaches both commands.
    """
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    monkeypatch.setenv("QUNEXPATH", str(tmp_path / "qunexpath"))
    monkeypatch.setenv("FSL_FIX_MATLAB_MODE", "1")

    sinfo, sessionsfolder = build_hcp_session(str(tmp_path), bolds=True)
    for key in ["3", "4"]:
        sinfo[key]["name"] = "bold" + sinfo[key]["bold_number"]

    results = os.path.join(sessionsfolder, "sess-01", "hcp", "sess-01", "MNINonLinear", "Results")
    for bold in ["BOLD_1", "BOLD_2"]:
        os.makedirs(os.path.join(results, bold))
        for name in ["%s_Atlas_hp2000_clean.dtseries.nii", "%s_hp2000_clean.nii.gz"]:
            open(os.path.join(results, bold, name % bold), "w").close()

    def _options(**overrides):
        overrides.setdefault("hcp_icafix_bolds", "BOLD_1,BOLD_2")
        return default_options(
            run="test",
            sessionsfolder=sessionsfolder,
            comlogs=str(tmp_path / "comlogs"),
            logfolder=str(tmp_path / "logs"),
            **overrides,
        )

    return sinfo, _options


def test_msmall_passes_vn_and_ind_mean_only_when_asked(msmall_session):
    """
    Both are flags, False when not given, and were tested with `is not None`:
    every run passed --vn=YES and --use-ind-mean=NO, never the HCP defaults.
    """
    sinfo, options = msmall_session

    text = hcp_msmall(sinfo, options()).text
    assert "--vn=YES" not in text
    assert "--use-ind-mean=NO" not in text

    text = hcp_msmall(
        sinfo, options(hcp_msmall_vn=True, hcp_msmall_no_ind_mean=True)
    ).text
    assert "--vn=YES" in text
    assert "--use-ind-mean=NO" in text


@pytest.mark.parametrize("named", ["BOLD_1,BOLD_2", "1,2", "rest"])
def test_msmall_bolds_are_named_by_name_number_or_tag(msmall_session, named):
    """
    A BOLD given by its number became `BOLD_{...the whole record...}`, and one
    given by its tag raised a KeyError; a name was only recognized as a user
    defined file name. A tag names every BOLD that carries it, as it does in
    hcp_icafix_bolds.
    """
    sinfo, options = msmall_session

    log = hcp_msmall(sinfo, options(hcp_msmall_bolds=named))

    assert '--fmri-names-list="BOLD_1@BOLD_2"' in log.text
    assert "ERROR" not in log.text


@pytest.mark.parametrize(
    "icafix, where",
    [
        ("BOLD_1", "hcp_icafix_bolds"),
        ("G1:BOLD_1|G2:BOLD_2", "the hcp_icafix_bolds group G1"),
    ],
)
def test_msmall_bolds_have_to_be_in_hcp_icafix_bolds(msmall_session, icafix, where):
    """
    The BOLDs were looked up in the whole session, so one ICA-FIX was not run
    on was accepted, and a multi-run group was handed a BOLD of another
    group's concatenation.
    """
    sinfo, options = msmall_session

    log = hcp_msmall(
        sinfo, options(hcp_icafix_bolds=icafix, hcp_msmall_bolds="BOLD_2")
    )

    assert "bold BOLD_2 used in hcp_msmall_bolds but not found in %s!" % where in log.text
    assert "--fmri-names-list" not in log.text
    assert log.status[2] == 1


def test_msmall_names_the_session_with_its_hcp_suffix(msmall_session):
    """
    Single-run MSMAll looked for its inputs in `<id><suffix>` and was then
    pointed at `<id>`, unlike DeDriftAndResample chained on after it.
    """
    sinfo, options = msmall_session
    os.rename(
        os.path.join(sinfo["hcp"], "sess-01"), os.path.join(sinfo["hcp"], "sess-01_V1")
    )

    log = hcp_msmall(sinfo, options(hcp_suffix="_V1"))

    assert '--session="sess-01_V1"' in log.text
    assert '--subject="sess-01_V1"' in log.text
    assert log.status[2] == 0


def test_msmall_is_reported_under_its_output_name(msmall_session):
    """It was reported under the number of the last BOLD it checked."""
    sinfo, options = msmall_session

    log = hcp_msmall(sinfo, options(hcp_msmall_resample=False))

    assert log.status[1] == "HCP MSMAll: bolds rfMRI_REST ready"


def test_single_run_dedrift_checks_its_input_at_the_default_highpass(msmall_session):
    """
    The condition was inverted: with the high-pass left at its default, the
    input it checked for was `<bold>_hpNone_clean.nii.gz`, so single-run
    DeDriftAndResample never ran; one that was set was replaced by 2000.
    """
    sinfo, options = msmall_session

    log = hcp_msmall(sinfo, options())

    assert "hpNone" not in log.text
    assert "HCP DeDriftAndResample can be run" in log.text
    assert "HCP MSMAll can be run" in log.text, "a dry run is not reported skipped"
    assert log.status[2] == 0


def test_dedrift_and_resample_on_its_own_finds_its_input(msmall_session):
    sinfo, options = msmall_session

    log = hcp_dedrift_and_resample(sinfo, options())

    assert "hpNone" not in log.text
    assert "HCP DeDriftAndResample can be run" in log.text
    assert log.status[2] == 0


def test_single_run_dedrift_needs_a_matlab_mode(msmall_session, monkeypatch):
    """
    Without hcp_matlab_mode or FSL_FIX_MATLAB_MODE it reported the error and
    then passed --matlab-run-mode="None" to a run it called ready.
    """
    sinfo, options = msmall_session
    monkeypatch.delenv("FSL_FIX_MATLAB_MODE")

    log = hcp_dedrift_and_resample(sinfo, options())

    assert "FSL_FIX_MATLAB_MODE not set" in log.text
    assert '--matlab-run-mode="None"' not in log.text
    assert "HCP DeDriftAndResample can be run" not in log.text
    assert log.status[2] == 1


MSMALL_SETTINGS = {
    "hcp_msmall_iteration_modes": "C_A_CAT",
    "hcp_msmall_ica_dim": "25",
    "hcp_msmall_method": "DR",
}


@pytest.mark.parametrize("command", [hcp_msmall, hcp_dedrift_and_resample])
@pytest.mark.parametrize(
    "icafix",
    [
        {},
        {"hcp_icafix_bolds": "G1:BOLD_1,BOLD_2", "hcp_icafix_highpass": "2000"},
    ],
    ids=["single-run", "multi-run"],
)
@pytest.mark.parametrize(
    "settings, regname",
    [
        ({}, "MSMAll_InitialReg_2_d40_WRN"),
        (MSMALL_SETTINGS, "MSMAll_InitialReg_3_d25_DR"),
        (dict(MSMALL_SETTINGS, hcp_resample_regname="MyReg"), "MyReg"),
        ({"hcp_msmall_outregname": "Mine"}, "Mine_2_d40_WRN"),
    ],
)
def test_dedrift_applies_the_registration_msmall_named(
    msmall_session, command, icafix, settings, regname
):
    """
    The registration was always `<hcp_msmall_outregname>_2_d40_WRN`, the name
    MSMAll gives it with its default settings only: with other iteration
    modes, ICA dimension or method DeDriftAndResample looked for a
    registration that was never made, unless hcp_resample_regname was set
    by hand.
    """
    sinfo, options = msmall_session
    if icafix:
        # the concatenation multi-run ICA-FIX made of the group
        concat = os.path.join(sinfo["hcp"], "sess-01", "MNINonLinear", "Results", "G1")
        os.makedirs(concat)
        open(os.path.join(concat, "G1_hp2000_clean.nii.gz"), "w").close()

    log = command(sinfo, options(**icafix, **settings))

    assert "HCP DeDriftAndResample can be run" in log.text
    assert '--registration-name="%s"' % regname in log.text
    assert log.status[2] == 0


@pytest.mark.parametrize("command", [hcp_icafix, hcp_msmall, hcp_dedrift_and_resample])
@pytest.mark.parametrize(
    "icafix, error",
    [
        (
            "G1:BOLD_1|G2:rest",
            "the bold [BOLD_1] is specified in the hcp_icafix_bolds groups G1 and G2",
        ),
        (
            "G1:rest|G2:rest",
            "the bold [BOLD_1] is specified in the hcp_icafix_bolds groups G1 and G2",
        ),
        (
            "G1:BOLD_2,rest",
            "the bold [BOLD_2] is specified twice in the hcp_icafix_bolds group G1",
        ),
        ("BOLD_1,rest", "the bold [BOLD_1] is specified twice"),
    ],
)
def test_a_bold_belongs_to_one_icafix_group_only(
    msmall_session, command, icafix, error
):
    """
    An entry was compared as written with the bolds already collected, so a
    bold named by its name in one group and by its tag in another, or a tag
    repeated, put the bold in two groups (or twice in one) without an error.
    """
    sinfo, options = msmall_session

    log = command(sinfo, options(hcp_icafix_bolds=icafix))

    assert error in log.text
    assert "invalid input parameters" in log.text
    assert "Pipeline.sh" not in log.text
    assert log.status[2] == 1


@pytest.mark.parametrize("command", [hcp_icafix, hcp_msmall, hcp_dedrift_and_resample])
@pytest.mark.parametrize(
    "icafix, entry",
    [("G1:BOLD_1|BOLD_2", "BOLD_2"), ("G1:BOLD_1|:BOLD_2", ":BOLD_2")],
)
def test_every_icafix_group_entry_needs_a_group_name(
    msmall_session, command, icafix, entry
):
    """
    With groups, an entry without a group name ('G1:BOLD_1|BOLD_2') raised an
    IndexError, reported as an unknown error with a traceback.
    """
    sinfo, options = msmall_session

    log = command(sinfo, options(hcp_icafix_bolds=icafix))

    assert f"the hcp_icafix_bolds entry [{entry}] is not <group name>:<bolds>" in log.text
    assert "invalid input parameters" in log.text
    assert "Traceback" not in log.text
    assert "Pipeline.sh" not in log.text
    assert log.status[2] == 1
