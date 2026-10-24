# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Regression tests for the HCP longitudinal session steps.

They cover the session links ``hcp_prep_long`` and ``hcp_make_average_dataset``
make (a link left dangling by a moved study is replaced, a link that can not be
made fails its session instead of being reported done), and the failures
``hcp_long_transmit_bias`` and ``hcp_long_msmall`` used to report as success.
``hcp_temporal_ica`` is covered in ``test_hcp_long_dryrun.py``.

Nothing external runs: a dry run builds the command only, and a real run gets
a stub in place of ``pc.run_external_for_file``.
"""

import concurrent.futures
import os
import re

import pytest

import qx_utilities.general.core as gc
import qx_utilities.hcp.hcp_long_msmall as hcp_long_msmall_module
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_long_transmit_bias import hcp_long_transmit_bias
from qx_utilities.hcp.hcp_make_average_dataset import hcp_make_average_dataset
from qx_utilities.hcp.hcp_prep_long import hcp_prep_long

from .test_hcp_long_dryrun import GROUP, session_hcp, tree
from .utils import build_hcp_session, default_options


@pytest.fixture
def study(tmp_path, monkeypatch):
    """
    A study with sessions s1 and s2 of subject subj-01, the options to run a
    command on it, and a stub in place of the external call that records the
    scripts it was asked to run.
    """
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    monkeypatch.setenv("QUNEXPATH", str(tmp_path / "qunexpath"))

    root = tmp_path / "study"
    sinfos = []
    for sid in ("s1", "s2"):
        sinfo, sessionsfolder = build_hcp_session(str(root), session_id=sid)
        sinfos.append(sinfo)

    calls = []
    outcome = {"failed": 0}

    def fake_run_external_for_file(tfile, comm, *args, **kwargs):
        calls.append(os.path.basename(comm.split()[0]))
        return None, "done", outcome["failed"]

    monkeypatch.setattr(pc, "run_external_for_file", fake_run_external_for_file)

    def options(run, **overrides):
        return default_options(
            run=run,
            studyfolder=str(root),
            comlogs=str(tmp_path / "comlogs"),
            logfolder=str(tmp_path / "logs"),
            **overrides,
        )

    class Study:
        pass

    s = Study()
    s.root = root
    s.sessionsfolder = sessionsfolder
    s.sessions = gc.SessionList(sinfos)
    s.options = options
    s.calls = calls
    s.outcome = outcome
    return s


# --------------------------------------------------------------- hcp_prep_long


def subject_folder(study):
    folder = study.root / "subjects" / "subj-01"
    folder.mkdir(parents=True)
    return folder


def test_prep_long_replaces_a_dangling_session_link(study):
    """
    A link left dangling, e.g. by a study that was moved, made link_or_copy
    fail without a word, and the session was still reported done.
    """
    subject = subject_folder(study)
    os.symlink("/nonexistent/old_study/sessions/s1/hcp/s1", subject / "s1")

    log = hcp_prep_long(study.sessions, study.options("run"))

    assert log.status == (
        "subj-01",
        "sessions: 2 done [s1, s2], 0 failed [] => processing completed",
        0,
    )
    for sid in ("s1", "s2"):
        assert os.path.islink(subject / sid)
        assert os.readlink(subject / sid) == session_hcp(study, sid)


def test_prep_long_fails_a_session_it_cannot_link(study):
    """A folder in the link's place fails the session; it is not 'done'."""
    subject = subject_folder(study)
    (subject / "s1").mkdir()
    (subject / "s1" / "keep.txt").write_text("mine")

    log = hcp_prep_long(study.sessions, study.options("run"))

    assert log.status == (
        "subj-01",
        "sessions: 1 done [s2], 1 failed [s1] => processing completed",
        1,
    )
    assert "could not be copied" in log.text
    assert not os.path.islink(subject / "s1")
    assert (subject / "s1" / "keep.txt").read_text() == "mine"
    assert os.readlink(subject / "s2") == session_hcp(study, "s2")


def test_prep_long_dry_run_leaves_a_dangling_link_alone(study):
    subject = subject_folder(study)
    os.symlink("/nonexistent/old_study/sessions/s1/hcp/s1", subject / "s1")
    before = tree(study.root)

    log = hcp_prep_long(study.sessions, study.options("test"))

    assert log.status == (
        "subj-01",
        "sessions: 2 ready [s1, s2], 0 failed [] => processing completed",
        0,
    )
    for sid in ("s1", "s2"):
        target = subject / sid
        assert f"test, not linked: {target} -> {session_hcp(study, sid)}" in log.text
    assert tree(study.root) == before


# ---------------------------------------------------- hcp_make_average_dataset


def average_folder(study):
    folder = os.path.join(study.sessionsfolder, "average_dataset", GROUP)
    os.makedirs(folder)
    return folder


def test_make_average_dataset_dry_run_reports_a_dangling_link(study):
    """
    The dry run checked the link with lexists, so a dangling one passed as
    linked; it is reported as a link still to be made, and left in place.
    """
    folder = average_folder(study)
    dangling = os.path.join(folder, "s1")
    os.symlink("/nonexistent/old_study/sessions/s1/hcp/s1", dangling)
    before = tree(study.root)

    log = hcp_make_average_dataset(
        study.sessions, study.options("test", hcp_outgroupname=GROUP)
    )

    assert log.status == ("s1,s2", "HCP make average dataset can be run", 0)
    assert f"test, not linked: {dangling}" in log.text
    assert f"test, not linked: {os.path.join(folder, 's2')}" in log.text
    assert study.calls == []
    assert tree(study.root) == before


def test_make_average_dataset_replaces_a_dangling_link(study):
    folder = average_folder(study)
    os.symlink("/nonexistent/old_study/sessions/s1/hcp/s1", os.path.join(folder, "s1"))

    log = hcp_make_average_dataset(
        study.sessions, study.options("run", hcp_outgroupname=GROUP)
    )

    assert log.status[2] == 0
    assert study.calls == ["MakeAverageDataset.sh"]
    for sid in ("s1", "s2"):
        assert os.readlink(os.path.join(folder, sid)) == session_hcp(study, sid)


def test_make_average_dataset_fails_a_session_it_cannot_link(study):
    """A failed link used to be ignored and the pipeline started anyway."""
    folder = average_folder(study)
    os.makedirs(os.path.join(folder, "s1"))

    log = hcp_make_average_dataset(
        study.sessions, study.options("run", hcp_outgroupname=GROUP)
    )

    assert log.status == ("s1,s2", "HCP make average dataset cannot be run", 1)
    assert "Session cannot be processed" in log.text
    assert "could not be copied" in log.text
    assert study.calls == []


# ------------------------------------------------------ hcp_long_transmit_bias


def test_long_transmit_bias_with_missing_afi_parameters_fails(study, tmp_path):
    """
    A real run whose AFI parameters are incomplete is not started, and is
    reported as failed: it was 'not ready' with failed=0, which gmri takes for
    success.
    """
    options = study.options("run", hcp_transmit_mode="AFI", hcp_afi_tr_one="1")

    log = hcp_long_transmit_bias(study.sessions, options)

    assert log.status == ("subj-01", "not ready", 1)
    assert study.calls == []
    assert not (tmp_path / "logs" / "comlogs").exists()


# ------------------------------------------------------------ hcp_long_msmall


DEDRIFT_CALLS = []


def fake_dedrift(sinfo, options, hcp, run, group):
    DEDRIFT_CALLS.append(sinfo["id"])
    return {
        "r": "",
        "report": {"failed": [], "ready": [], "not ready": [], "done": []},
    }


@pytest.fixture
def msmall_study(study, monkeypatch):
    """
    The study's s1 alone, with two BOLDs and the multi-run ICA-FIX outputs
    hcp_long_msmall checks for, and dedrift and resample stubbed in this
    process.
    """
    sinfo = study.sessions[0]
    for key, number in (("3", "1"), ("4", "2")):
        sinfo[key] = {"name": "bold" + number, "task": "rest",
                      "boldname": "BOLD_" + number, "bold_number": number,
                      "filename": "BOLD_" + number}
    results = os.path.join(session_hcp(study, "s1"), "MNINonLinear", "Results")
    for bold in ("BOLD_1", "BOLD_2"):
        os.makedirs(os.path.join(results, bold))
        open(os.path.join(results, bold, f"{bold}_Atlas_hp0_clean.dtseries.nii"), "w").close()
    os.makedirs(os.path.join(results, "fMRI_CONCAT_ALL"))
    open(os.path.join(results, "fMRI_CONCAT_ALL", "fMRI_CONCAT_ALL_hp0_clean.nii.gz"), "w").close()

    DEDRIFT_CALLS.clear()
    monkeypatch.setattr(
        hcp_long_msmall_module, "execute_hcp_multi_dedrift_and_resample", fake_dedrift
    )
    monkeypatch.setattr(
        hcp_long_msmall_module, "ProcessPoolExecutor", concurrent.futures.ThreadPoolExecutor
    )
    study.sessions = gc.SessionList([sinfo])
    return study


def msmall_options(study):
    return study.options(
        "run",
        hcp_icafix_bolds="fMRI_CONCAT_ALL:BOLD_1,BOLD_2",
        hcp_msmall_bolds="BOLD_1",
        hcp_icafix_highpass="0",
        hcp_matlab_mode="interpreted",
    )


def test_long_msmall_reports_a_failed_msmall_call(msmall_study):
    """
    `failed = False` right after the MSMAll call threw its result away: a
    failed call was reported done and dedrift and resample started.
    """
    msmall_study.outcome["failed"] = 1

    log = hcp_long_msmall_module.hcp_long_msmall(
        msmall_study.sessions, msmall_options(msmall_study)
    )

    assert msmall_study.calls == ["MSMAllPipeline.sh"]
    assert log.status == (
        "subj-01",
        "done: 0 [], ready: 0 [], skipped: 0 [], not ready: 0 [], "
        "failed: 1 [msmall_subj-01_fMRI_CONCAT_ALL]",
        1,
    )
    assert DEDRIFT_CALLS == []


def test_long_msmall_goes_on_to_dedrift_after_a_good_msmall_call(msmall_study):
    log = hcp_long_msmall_module.hcp_long_msmall(
        msmall_study.sessions, msmall_options(msmall_study)
    )

    assert msmall_study.calls == ["MSMAllPipeline.sh"]
    assert log.status == (
        "subj-01",
        "done: 1 [msmall_subj-01_fMRI_CONCAT_ALL], ready: 0 [], skipped: 0 [], "
        "not ready: 0 [], failed: 0 []",
        0,
    )
    assert sorted(DEDRIFT_CALLS) == ["s1.long.base", "subj-01.long.base"]


def test_long_msmall_refuses_bolds_that_are_not_a_concatenation(msmall_study):
    """
    Ungrouped (single-run) ICAFix bolds have no concatenation for the
    longitudinal pipeline to run on: the run ended in a KeyError on the group
    name, and an UnboundLocalError in the handler that was to report it.
    """
    options = msmall_options(msmall_study)
    options["hcp_icafix_bolds"] = "BOLD_1,BOLD_2"

    log = hcp_long_msmall_module.hcp_long_msmall(msmall_study.sessions, options)

    assert msmall_study.calls == []
    assert log.status[2] == 1
    assert "needs multi-run ICAFix bolds" in log.text
    assert "Traceback" not in log.text


def test_long_msmall_dedrifts_the_registration_msmall_named(msmall_study, monkeypatch):
    """
    DeDriftAndResample applies the registration under the name MSMAll gives
    it. hcp_long_msmall runs MSMAll with its default iteration modes, ICA
    dimension and method, so these name the registration whatever a batch
    file sets for hcp_msmall, unless hcp_resample_regname names another.
    """
    import qx_utilities.hcp.hcp_utils as hcp_utils

    monkeypatch.setattr(
        hcp_long_msmall_module,
        "execute_hcp_multi_dedrift_and_resample",
        hcp_utils.execute_hcp_multi_dedrift_and_resample,
    )
    results = os.path.join(session_hcp(msmall_study, "s1"), "MNINonLinear", "Results")
    for bold in ("BOLD_1", "BOLD_2"):
        open(os.path.join(results, bold, f"{bold}_hp0_clean.nii.gz"), "w").close()
    commands = []

    def fake_run_external_for_file(tfile, comm, *args, **kwargs):
        commands.append(comm)
        return None, "done", 0

    monkeypatch.setattr(pc, "run_external_for_file", fake_run_external_for_file)

    for overrides, regname in [
        ({}, "MSMAll_InitialReg_2_d40_WRN"),
        (
            {
                "hcp_msmall_iteration_modes": "C_A_CAT",
                "hcp_msmall_ica_dim": "25",
                "hcp_msmall_method": "DR",
            },
            "MSMAll_InitialReg_2_d40_WRN",
        ),
        ({"hcp_resample_regname": "MyReg"}, "MyReg"),
    ]:
        commands.clear()
        options = msmall_options(msmall_study)
        options.update(overrides)

        log = hcp_long_msmall_module.hcp_long_msmall(msmall_study.sessions, options)

        dedrift = [c for c in commands if "DeDriftAndResamplePipeline.sh" in c]
        assert len(dedrift) == 2, log.text
        for comm in dedrift:
            assert re.search(r'--registration-name="%s"' % regname, comm), comm
