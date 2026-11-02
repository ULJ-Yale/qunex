# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Dry-run tests checking that an HCP command run with ``--test`` changes nothing.

Split from ``test_hcp_dryrun.py``: ICA-FIX, PostFix, ApplyAutoReclean,
ReApplyFix, the transmit-bias group phases, run_qc and map_hcp_data are run
on a session tree that is compared before and after, with every external
call made fatal, and each still has to name what it would have run.
"""

import os
import subprocess

import nibabel as nib
import numpy as np
import pytest

import qx_utilities.general.core as gc
import qx_utilities.hcp.qc_hcp as qc_hcp
import qx_utilities.hcp.hcp_apply_auto_reclean as hcp_apply_auto_reclean_module
import qx_utilities.hcp.hcp_icafix as hcp_icafix_module
import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog
from qx_utilities.hcp.hcp_apply_auto_reclean import hcp_apply_auto_reclean
from qx_utilities.hcp.hcp_icafix import hcp_icafix
from qx_utilities.hcp.hcp_post_fix import hcp_post_fix
from qx_utilities.hcp.hcp_reapply_fix import hcp_reapply_fix
from qx_utilities.hcp.hcp_transmit_bias_group_average_fit import (
    hcp_transmit_bias_group_average_fit,
)
from qx_utilities.hcp.map_hcp_data import _bold_resolution, map_hcp_data

from .utils import build_hcp_session, default_options

@pytest.fixture
def session(tmp_path, monkeypatch):
    """Build a session (and its options) ready for a dry run of one command."""
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    monkeypatch.setenv("QUNEXPATH", str(tmp_path / "qunexpath"))

    def _build(bolds=False, dwi=False, subject=False, multisession=False, **overrides):
        sinfo, sessionsfolder = build_hcp_session(str(tmp_path), bolds=bolds, dwi=dwi)
        options = default_options(
            run="test",
            sessionsfolder=sessionsfolder,
            comlogs=str(tmp_path / "comlogs"),
            **overrides,
        )
        arg = gc.SessionList([sinfo]) if (subject or multisession) else sinfo
        return arg, options

    return _build




@pytest.fixture
def msmall_session(tmp_path, monkeypatch):
    """
    A session with two BOLDs and the ICA-FIX outputs of their group G1, at the
    default high-pass of 0, so a dry run reaches both commands.
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
        for name in ["%s_Atlas_hp0_clean.dtseries.nii", "%s_hp0_clean.nii.gz"]:
            open(os.path.join(results, bold, name % bold), "w").close()
    os.makedirs(os.path.join(results, "G1"))
    open(os.path.join(results, "G1", "G1_hp0_clean.nii.gz"), "w").close()

    def _options(**overrides):
        overrides.setdefault("hcp_icafix_bolds", "G1:BOLD_1,BOLD_2")
        return default_options(
            run="test",
            sessionsfolder=sessionsfolder,
            comlogs=str(tmp_path / "comlogs"),
            logfolder=str(tmp_path / "logs"),
            **overrides,
        )

    return sinfo, _options




# ------------------------------------------------- the dry run changes nothing


def _tree(root):
    """Every file under `root`, with its size and mtime."""
    found = {}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            stat = os.stat(path)
            found[path] = (stat.st_size, stat.st_mtime_ns)
    return found


@pytest.fixture
def no_external(monkeypatch):
    """Make every external call a dry run could reach fatal."""

    def fail(*args, **kwargs):
        raise AssertionError("a --test run executed an external command")

    monkeypatch.setattr(pc, "run_external_for_file", fail)
    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(qc_hcp, "ProcessPoolExecutor", fail)


@pytest.fixture
def fix_session(tmp_path, msmall_session, no_external):
    """
    msmall_session with the BOLD images ICA-FIX reads.
    """
    sinfo, options = msmall_session
    results = os.path.join(sinfo["hcp"], "sess-01", "MNINonLinear", "Results")
    for bold in ["BOLD_1", "BOLD_2"]:
        open(os.path.join(results, bold, bold + ".nii.gz"), "w").close()
    return sinfo, options, tmp_path


def test_icafix_dry_run_says_it_can_be_run(fix_session):
    """It was reported skipped: with no file to check, `check_run` says done."""
    sinfo, options, root = fix_session
    before = _tree(root)

    log = hcp_icafix(sinfo, options())

    assert _tree(root) == before, "a --test run wrote, removed or replaced a file"
    assert "HCP ICAFix can be run" in log.text
    assert os.path.join("ICAFIX", "hcp_fix_multi_run") in log.text
    assert log.status[1] == "HCP ICAFix: G1 (ICAFix), G1 (PostFix) ready"
    assert log.status[2] == 0


@pytest.fixture
def serial_icafix(monkeypatch):
    """
    Run the ICAFix executors in this process, so an environment variable one
    of them sets is seen by the test -- in a worker it would go unnoticed.
    """

    class Serial:
        def __init__(self, *args, **kwargs):
            pass

        def map(self, function, items):
            return [function(item) for item in items]

    monkeypatch.setattr(hcp_icafix_module, "ProcessPoolExecutor", Serial)
    monkeypatch.setattr(hcp_apply_auto_reclean_module, "ProcessPoolExecutor", Serial)


@pytest.fixture
def bare_fix_session(fix_session, serial_icafix):
    """fix_session without the ICAFix outputs: what a session has before ICAFix."""
    sinfo, options, root = fix_session
    results = os.path.join(sinfo["hcp"], "sess-01", "MNINonLinear", "Results")
    os.remove(os.path.join(results, "G1", "G1_hp0_clean.nii.gz"))
    for bold in ["BOLD_1", "BOLD_2"]:
        for name in ["%s_Atlas_hp0_clean.dtseries.nii", "%s_hp0_clean.nii.gz"]:
            os.remove(os.path.join(results, bold, name % bold))
    return sinfo, options, root


def test_an_icafix_dry_run_says_what_postfix_it_would_chain(bare_fix_session):
    """
    The real run chains PostFix after a successful ICAFix; the dry run stopped
    at ICAFix and never said so. PostFix reads the clean ICA output ICAFix
    writes, so the chained dry run cannot look for it.
    """
    sinfo, options, root = bare_fix_session
    before = _tree(root)

    log = hcp_icafix(sinfo, options())

    assert _tree(root) == before, "a --test run wrote, removed or replaced a file"
    assert log.text.count(os.path.join("ICAFIX", "PostFix.sh")) == 1
    assert log.text.count("HCP PostFix can be run after ICAFix") == 1
    assert '--fmri-name="G1"' in log.text
    assert "G1_hp0_clean.nii.gz is written by ICAFix, not checked" in log.text
    assert '--high-pass="0"' in log.text
    assert "missing" not in log.text
    assert log.status[2] == 0


def test_an_icafix_dry_run_without_postfix_chains_none(bare_fix_session):
    sinfo, options, root = bare_fix_session

    log = hcp_icafix(sinfo, options(hcp_icafix_postfix=False))

    assert "PostFix" not in log.text
    assert log.status[1] == "HCP ICAFix: G1 ready"


def test_an_icafix_that_is_not_ready_chains_no_postfix(bare_fix_session):
    """As in a real run, PostFix follows only an ICAFix that can be run."""
    sinfo, options, root = bare_fix_session
    results = os.path.join(sinfo["hcp"], "sess-01", "MNINonLinear", "Results")
    os.remove(os.path.join(results, "BOLD_2", "BOLD_2.nii.gz"))

    log = hcp_icafix(sinfo, options())

    assert os.path.join("ICAFIX", "PostFix.sh") not in log.text
    assert log.status[1] == "HCP ICAFix: G1 (ICAFix) not ready"


@pytest.mark.parametrize(
    "mode, chained",
    [(None, "1"), ("compiled", "0"), ("octave", "2")],
)
def test_an_icafix_dry_run_leaves_the_environment_alone(
    bare_fix_session, monkeypatch, mode, chained
):
    """
    --hcp_matlab_mode was put in FSL_FIX_MATLAB_MODE in this process: a dry run
    changed the environment, and the next session of the run inherited the
    value. The pipelines are handed the mode on their command lines instead.
    """
    sinfo, options, root = bare_fix_session
    environment = dict(os.environ)

    log = hcp_icafix(sinfo, options(hcp_matlab_mode=mode))

    assert dict(os.environ) == environment
    assert "FSL_FIX_MATLAB_MODE=%s " % chained in log.text
    assert '--matlab-run-mode="%s"' % chained in log.text
    assert log.status[2] == 0


def test_the_matlab_mode_of_one_session_does_not_reach_the_next(
    bare_fix_session, monkeypatch
):
    """
    A session that names a mode was followed by one that relies on the
    environment: the second ran with the first one's mode, and without an
    environment it failed only when run on its own.
    """
    sinfo, options, root = bare_fix_session
    monkeypatch.delenv("FSL_FIX_MATLAB_MODE")

    hcp_icafix(sinfo, options(hcp_matlab_mode="compiled"))
    log = hcp_icafix(sinfo, options())

    assert "FSL_FIX_MATLAB_MODE not set" in log.text
    assert log.status[2] == 1


@pytest.fixture
def reclean_session(bare_fix_session):
    """A session with the MSMAll registration hcp_apply_auto_reclean works on."""
    sinfo, options, root = bare_fix_session
    native = os.path.join(sinfo["hcp"], "sess-01", "MNINonLinear", "Native")
    os.makedirs(native, exist_ok=True)
    open(os.path.join(native, "sess-01.L.sphere.MSMAll.native.surf.gii"), "w").close()
    return sinfo, options, root


def test_apply_auto_reclean_needs_the_msmall_registration(bare_fix_session):
    """The pipeline hard codes MSMAll, and a study without it was called ready."""
    sinfo, options, root = bare_fix_session

    log = hcp_apply_auto_reclean(sinfo, options(hcp_matlab_mode="octave"))

    assert "run hcp_msmall first" in log.text
    assert "HCP ApplyAutoReclean can be run" not in log.text
    assert log.status[2] == 1


def test_apply_auto_reclean_dry_run_says_it_can_be_run(reclean_session):
    """It set FSL_FIX_MATLAB_MODE in this process and its dry run reported nothing."""
    sinfo, options, root = reclean_session
    environment = dict(os.environ)
    before = _tree(root)

    log = hcp_apply_auto_reclean(sinfo, options(hcp_matlab_mode="octave"))

    assert dict(os.environ) == environment
    assert _tree(root) == before, "a --test run wrote, removed or replaced a file"
    assert "HCP ApplyAutoReclean can be run" in log.text
    assert '--matlab-run-mode="2"' in log.text
    assert '--mrfix-concat-name="G1"' in log.text
    assert log.status[1] == "HCP ApplyAutoReclean: G1 ready"
    assert log.status[2] == 0


def test_apply_auto_reclean_hands_its_call_the_matlab_mode(reclean_session, monkeypatch):
    """The mode reaches the pipeline on its command line, the environment stays."""
    sinfo, options, root = reclean_session
    calls = []

    def run_external(checkfile, comm, description, **kwargs):
        calls.append(comm)
        return "done.log", "done", 0

    monkeypatch.setattr(pc, "run_external_for_file", run_external)
    environment = dict(os.environ)

    log = hcp_apply_auto_reclean(sinfo, dict(options(hcp_matlab_mode="compiled"), run="run"))

    assert dict(os.environ) == environment
    assert len(calls) == 1
    assert '--matlab-run-mode="0"' in calls[0]
    assert log.status[1] == "HCP ApplyAutoReclean: G1 done"
    assert log.status[2] == 0


def test_reapply_fix_hands_its_call_the_matlab_mode(msmall_session):
    sinfo, options = msmall_session

    results = os.path.join(sinfo["hcp"], "sess-01", "MNINonLinear", "Results")
    for bold in ["BOLD_1", "BOLD_2"]:
        open(os.path.join(results, bold, bold + ".nii.gz"), "w").close()

    log = hcp_reapply_fix(sinfo, options(hcp_matlab_mode="compiled"))

    assert '--matlab-run-mode="0"' in log.text
    assert '--fmri-names="BOLD_1@BOLD_2"' in log.text
    assert log.status[2] == 0


def test_reapply_fix_does_not_run_a_group_with_a_bold_missing(msmall_session):
    """The check reported the bold missing, and the group was then declared fine."""
    sinfo, options = msmall_session

    results = os.path.join(sinfo["hcp"], "sess-01", "MNINonLinear", "Results")
    open(os.path.join(results, "BOLD_1", "BOLD_1.nii.gz"), "w").close()

    log = hcp_reapply_fix(sinfo, options(hcp_matlab_mode="compiled"))

    assert "BOLD_2.nii.gz] missing" in log.text
    assert "ReApplyFixMultiRunPipeline.sh" not in log.text
    assert "Hand reclassification" not in log.text, "the group is refused before any work"
    assert log.status[1] == "HCP ReApplyFix: bolds G1 not ready"
    assert log.status[2] == 1


def test_reapply_fix_needs_a_matlab_mode(msmall_session, monkeypatch):
    """It reached the command line as `None`, after the hand reclassification had run."""
    sinfo, options = msmall_session
    monkeypatch.delenv("FSL_FIX_MATLAB_MODE")

    log = hcp_reapply_fix(sinfo, options())

    assert "FSL_FIX_MATLAB_MODE not set" in log.text
    assert "Hand reclassification" not in log.text
    assert log.status[2] == 1


def test_reapply_fix_hands_on_the_flags_the_pipeline_reads(msmall_session):
    """`--motionregression` and `--deleteintermediates` stopped the pipeline."""
    sinfo, options = msmall_session
    results = os.path.join(sinfo["hcp"], "sess-01", "MNINonLinear", "Results")
    for bold in ["BOLD_1", "BOLD_2"]:
        open(os.path.join(results, bold, bold + ".nii.gz"), "w").close()

    text = hcp_reapply_fix(
        sinfo,
        options(
            hcp_matlab_mode="compiled",
            hcp_icafix_domotionreg="TRUE",
            hcp_icafix_deleteintermediates="TRUE",
        ),
    ).text

    assert '--motion-regression="TRUE"' in text
    assert '--delete-intermediates="TRUE"' in text
    assert "--motionregression" not in text
    assert "--deleteintermediates" not in text


def test_post_fix_dry_run_says_it_can_be_run(fix_session):
    """It was reported as skipped."""
    sinfo, options, root = fix_session
    before = _tree(root)

    log = hcp_post_fix(sinfo, options())

    assert _tree(root) == before, "a --test run wrote, removed or replaced a file"
    assert "HCP PostFix can be run" in log.text
    assert os.path.join("ICAFIX", "PostFix.sh") in log.text
    assert log.status[1] == "HCP PostFix: bolds G1 ready"
    assert log.status[2] == 0


def _write_bold(path, voxel):
    """A small image with the given voxel size."""
    os.makedirs(os.path.dirname(path))
    nib.save(nib.Nifti1Image(np.zeros((2, 2, 2)), np.diag([voxel, voxel, voxel, 1])), path)


@pytest.mark.parametrize(
    "bolds, res",
    [
        ({"BOLD_1": 1.6, "BOLD_2": 2.0}, "1.6"),
        ({"BOLD_1": 2.5}, "2.5"),
        ({}, "2"),
    ],
)
def test_the_lowres_segmentation_is_resampled_to_the_resolution_of_the_bolds(tmp_path, bolds, res):
    """
    hcp_bold_res was read from map_hcp_data's own options: a run of the fMRI
    pipelines at 1.6 mm, stated for them alone, left a 2 mm segmentation that
    FC commands could not use with its BOLDs. `hcp_bold_res` answers only when
    there is no BOLD to read.
    """
    results = tmp_path / "Results"
    results.mkdir()
    for bold, voxel in bolds.items():
        _write_bold(str(results / bold / (bold + ".nii.gz")), voxel)

    assert _bold_resolution(str(results), "2", ReportLog()) == res


def test_bolds_of_different_resolutions_are_said_to_differ(tmp_path):
    results = tmp_path / "Results"
    results.mkdir()
    for bold, voxel in {"BOLD_1": 1.5, "BOLD_2": 2.0}.items():
        _write_bold(str(results / bold / (bold + ".nii.gz")), voxel)
    log = ReportLog()

    assert _bold_resolution(str(results), "2", log) == "1.5"
    assert "different resolutions (1.5, 2)" in log.text


def test_a_bold_that_can_not_be_read_says_nothing_of_the_resolution(tmp_path):
    results = tmp_path / "Results"
    (results / "BOLD_1").mkdir(parents=True)
    (results / "BOLD_1" / "BOLD_1.nii.gz").write_text("")

    assert _bold_resolution(str(results), "2", ReportLog()) == "2"


def test_transmit_bias_group_dry_run_says_it_can_be_run(tmp_path, monkeypatch, no_external):
    """It was reported as `... finished`, as if it had run."""
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    s1, sessionsfolder = build_hcp_session(str(tmp_path))
    s2, _ = build_hcp_session(str(tmp_path), session_id="sess-02")
    options = default_options(
        run="test",
        sessionsfolder=sessionsfolder,
        comlogs=str(tmp_path / "comlogs"),
        hcp_outgroupname="group",
        hcp_transmit_mode="B1Tx",
        hcp_transmit_group_name="tg",
        hcp_gmwm_template=str(tmp_path / "gmwm.dscalar.nii"),
        hcp_group_uncorrected_myelin=str(tmp_path / "myelin.dscalar.nii"),
    )
    before = _tree(str(tmp_path))

    log = hcp_transmit_bias_group_average_fit(gc.SessionList([s1, s2]), options)

    assert _tree(str(tmp_path)) == before, "a --test run wrote, removed or replaced a file"
    assert "Phase2_GroupAverageFit.sh" in log.text
    assert log.status == (
        "sess-01,sess-02",
        "HCP Transmit Bias Phase 2, Group Average Fit can be run",
        0,
    )


def test_run_qc_dry_run_runs_no_job_and_creates_no_folder(session, tmp_path, no_external):
    """
    `hcp_run_qc` read `--test` only to tag a log line: it created the QC
    folders and ran every job, each with `run: True` hard-coded.
    """
    templates = tmp_path / "templates"
    templates.mkdir()
    template = templates / "template_t1w_qc.wb.scene"
    template.write_text("DUMMYPATH DUMMYCASE")
    sinfo, options = session(qc_modality="T1w", qc_scenetemplatefolder=str(templates))
    qc = os.path.join(options["sessionsfolder"], "QC")
    before = _tree(str(tmp_path))

    log = qc_hcp.hcp_run_qc(sinfo, options)

    assert _tree(str(tmp_path)) == before, "a --test run wrote, removed or replaced a file"
    assert not os.path.exists(qc), "a --test run created the QC folder"
    assert "test, not created: %s\n" % os.path.join(qc, "T1w") in log.text
    assert "qclog" not in log.text, "the QC calls log with the run's comlogs"
    assert (
        "test, not run: T1w QC with wb_command -show-scene into %s, template %s"
        % (os.path.join(qc, "T1w"), template)
    ) in log.text
    assert log.status == ("sess-01", "HCP run QC: can be run 1 [T1w], cannot be run 0 []", 0)


def test_map_hcp_data_dry_run_changes_nothing(session, tmp_path, no_external):
    """
    `map_hcp_data` ignored `--test`: it mapped every file, removed the lowres
    segmentation and wrote the movement files.
    """
    sinfo, options = session(bolds=True, hcp_cifti_tail="_Atlas")
    for key in ["3", "4"]:
        sinfo[key]["name"] = "bold" + sinfo[key]["bold_number"]
    mni = os.path.join(sinfo["hcp"], "sess-01", "MNINonLinear")
    for name in ["T1w.nii.gz", "aparc+aseg.nii.gz", "T1w_restore.2.nii.gz"]:
        open(os.path.join(mni, name), "w").close()
    surface = os.path.join(mni, "fsaverage_LR32k")
    os.makedirs(surface)
    open(os.path.join(surface, "sess-01.L.midthickness.32k_fs_LR.surf.gii"), "w").close()
    open(os.path.join(surface, "sess-01.32k_fs_LR.wb.spec"), "w").close()
    for bold in ["BOLD_1", "BOLD_2"]:
        os.makedirs(os.path.join(mni, "Results", bold))
        for name in [bold + ".nii.gz", bold + "_Atlas.dtseries.nii", "Movement_Regressors.txt"]:
            open(os.path.join(mni, "Results", bold, name), "w").close()
    images = os.path.join(options["sessionsfolder"], "sess-01", "images")
    lowres = os.path.join(images, "segmentation", "freesurfer", "mri", "aparc+aseg_bold.nii.gz")
    os.makedirs(os.path.dirname(lowres))
    with open(lowres, "w") as f:
        f.write("an existing lowres segmentation")
    before = _tree(str(tmp_path))

    log = map_hcp_data(sinfo, options, overwrite=True)

    assert _tree(str(tmp_path)) == before, "a --test run wrote, removed or replaced a file"
    text = log.text
    t1 = os.path.join(images, "structural", "T1.nii.gz")
    assert "test, not copied: %s -> %s" % (os.path.join(mni, "T1w.nii.gz"), t1) in text
    assert "test, not removed: %s" % lowres in text
    assert "test, not run: flirt " in text
    assert "test, not copied: %s" % os.path.join(surface, "sess-01.L.midthickness") in text
    assert "test, not written: %s" % os.path.join(surface, "sess-01.32k_fs_LR.wb.spec") in text
    assert "test, not copied: %s" % os.path.join(mni, "Results", "BOLD_1", "BOLD_1.nii.gz") in text
    assert "test, not written: %s" % os.path.join(
        images, "functional", "movement", "bold1_mov.dat"
    ) in text
    assert "ERROR" not in text, text
    assert log.status[1] == (
        "T1: would be copied, aseg+aparc hires: would be copied lores: would be generated, "
        "surface: ok, bolds ok: 2, bolds failed: 0, bolds skipped: 0"
    )
    assert log.status[2] == 0
