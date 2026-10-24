# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for the BOLD QC of ``hcp_run_qc``.

Custom and user scenes are not available for BOLD and BOLD_FC: a run that asks
for them warns and runs the default BOLD QC, while the other modalities keep
theirs, and a legacy study has no folder for custom BOLD scenes.
``--qc_omitdefaults`` leaves a BOLD run nothing to render but the TSNR report,
and says so. ``--qc_bold_skipframes`` takes a number of frames, and the global
signal chart of the BOLD QC ends at the duration of the run.

Nothing external runs: a dry run prepares the QC jobs only, and the BOLD job
run on its own gets stubs in place of ``pc.run_external_for_file`` and of the
tools it reads values from.
"""

import os
import subprocess

import pytest

import qx_utilities.general.exceptions as ge
import qx_utilities.general.utilities as gu
import qx_utilities.hcp.qc_hcp as qc_hcp
import qx_utilities.processing.core as pc

from .utils import build_hcp_session, default_options


@pytest.fixture
def no_external(monkeypatch):
    """Make every external call a dry run could reach fatal."""

    def fail(*args, **kwargs):
        raise AssertionError("a --test run executed an external command")

    monkeypatch.setattr(pc, "run_external_for_file", fail)
    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(qc_hcp, "ProcessPoolExecutor", fail)


@pytest.fixture
def bold_session(tmp_path, monkeypatch, no_external):
    """
    A session with two BOLD runs, the scene templates in a folder of their own,
    and a function that builds the options of a dry run on them.
    """
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    templates = tmp_path / "templates"
    templates.mkdir()
    for name in ["bold", "scalar_bold", "t1w"]:
        (templates / f"template_{name}_qc.wb.scene").write_text("DUMMYPATH")
    sinfo, sessionsfolder = build_hcp_session(str(tmp_path), bolds=True)
    # use_or_skip_bold selects the runs named bold<N>
    for key in ["3", "4"]:
        sinfo[key]["name"] = "bold" + sinfo[key]["bold_number"]

    def options(**overrides):
        return default_options(
            run="test",
            sessionsfolder=sessionsfolder,
            comlogs=str(tmp_path / "comlogs"),
            qc_scenetemplatefolder=str(templates),
            **overrides,
        )

    return sinfo, options, templates


@pytest.mark.parametrize(
    "given, scene",
    [
        ({"qc_processcustom": "yes"}, "custom.scene"),
        ({"processcustom": "yes"}, "custom.scene"),
        ({"qc_userscenefile": "user.scene"}, "user.scene"),
    ],
)
def test_run_qc_renders_no_custom_or_user_bold_scene(bold_session, tmp_path, given, scene):
    """
    A custom or user BOLD scene was rendered as a BOLD QC job of its own. The
    run now warns and runs the default BOLD QC, and T1w keeps its scene.
    """
    sinfo, options, templates = bold_session
    for modality in ["BOLD", "T1w"]:
        custom = tmp_path / "processing" / "scenes" / "QC" / modality
        custom.mkdir(parents=True)
        (custom / "custom.scene").write_text("DUMMYPATH")
    (templates / "user.scene").write_text("DUMMYPATH")

    log = qc_hcp.hcp_run_qc(sinfo, options(qc_modality="BOLD,T1w", **given))

    assert "WARNING: custom and user scenes are not available for BOLD, ignoring" in log.text
    assert log.status == (
        "sess-01",
        "HCP run QC: can be run 4 [BOLD bold1, BOLD bold2, T1w, T1w %s], cannot be run 0 []"
        % scene,
        0,
    )


def test_run_qc_bold_fc_says_it_renders_no_custom_scene(bold_session):
    """BOLD_FC ignored a custom scene without a word."""
    sinfo, options, _ = bold_session

    log = qc_hcp.hcp_run_qc(
        sinfo,
        options(
            qc_modality="BOLD_FC",
            qc_boldfc="pscalar",
            qc_boldfcinput="fc.pscalar.nii",
            qc_processcustom="yes",
        ),
    )

    assert (
        "WARNING: custom and user scenes are not available for BOLD_FC, "
        "ignoring --qc_processcustom there"
    ) in log.text
    assert log.status == (
        "sess-01",
        "HCP run QC: can be run 2 [BOLD_FC pscalar bold1, BOLD_FC pscalar bold2], "
        "cannot be run 0 []",
        0,
    )


def test_a_legacy_study_has_no_folder_for_custom_bold_scenes(tmp_path, monkeypatch):
    """
    Custom scenes are read from processing/scenes/QC/<modality>, and BOLD has
    none: create_study --folders=legacy made a folder for them all the same.
    """
    monkeypatch.delenv("NIUTemplateFolder", raising=False)
    study = tmp_path / "study"

    gu.create_study(str(study), folders="legacy")

    custom = study / "processing" / "scenes" / "QC"
    assert sorted(folder.name for folder in custom.iterdir()) == ["DWI", "T1w", "T2w", "myelin"]


@pytest.mark.parametrize(
    "snronly, ready",
    [("no", "0 []"), ("yes", "2 [BOLD bold1, BOLD bold2]")],
)
def test_run_qc_bold_with_omitdefaults_says_it_renders_nothing(bold_session, snronly, ready):
    """
    A TSNR-only BOLD job renders no scene, so --qc_omitdefaults keeps it. It
    dropped every BOLD job, and said nothing about it.
    """
    sinfo, options, _ = bold_session
    given = options(qc_modality="BOLD", qc_omitdefaults="yes", qc_bold_snronly=snronly)

    log = qc_hcp.hcp_run_qc(sinfo, given)

    assert ("WARNING: --qc_omitdefaults=yes" in log.text) == (snronly == "no")
    assert log.status[1] == "HCP run QC: can be run %s, cannot be run 0 []" % ready
    # the dry run named a scene for the TSNR-only jobs too
    assert "-show-scene" not in log.text
    if snronly == "yes":
        qc = os.path.join(given["sessionsfolder"], "QC", "BOLD")
        for bold in ["bold1", "bold2"]:
            assert (
                "test, not run: BOLD %s TSNR report with wb_command -cifti-reduce into %s"
                % (bold, qc)
            ) in log.text


@pytest.mark.parametrize("skipframes", ["two", "2.5", "-1"])
def test_run_qc_rejects_skipframes_that_are_not_a_number_of_frames(bold_session, skipframes):
    """
    A negative number was ignored without a word, and a value that is not a
    whole number stopped the command with a traceback.
    """
    sinfo, options, _ = bold_session

    with pytest.raises(ge.CommandError) as error:
        qc_hcp.hcp_run_qc(sinfo, options(qc_modality="BOLD", qc_bold_skipframes=skipframes))

    assert error.value.error == f"--qc_bold_skipframes={skipframes} is not a number of frames."


@pytest.mark.parametrize("skipframes, ymin", [(0, "1.0"), (2, "3.0")])
def test_bold_qc_chart_ends_at_the_duration_of_the_run(
    tmp_path, monkeypatch, skipframes, ymin
):
    """
    The chart plots each frame at its time, a TR apart, and its axis ended at
    the number of frames less the skipped ones: it cut the series off at a TR
    over a second and left it short of the end at one under. The skipped frames
    set the y range only.
    """
    nonlin = tmp_path / "hcp" / "sess-01" / "MNINonLinear"
    results = nonlin / "Results" / "1"
    results.mkdir(parents=True)
    for name in ["1_Atlas.dtseries.nii", "1.nii.gz"]:
        (results / name).write_text("")
    template = tmp_path / "template.scene"
    template.write_text("XMAX=DUMMYXAXISMAX YMIN=DUMMYYAXISMIN YMAX=DUMMYYAXISMAX\n")
    outpath = tmp_path / "QC"
    (outpath / "qclog").mkdir(parents=True)

    def external(checkfile, command, *args, **kwargs):
        # the global signal of ten frames, and an empty file for the other outputs
        with open(checkfile, "w") as f:
            if "-reduce MEAN >" in command:
                f.write("\n".join(str(frame) for frame in range(1, 11)) + "\n")
        return None, "done", 0

    def capture(command, **kwargs):
        # fslval prints its value with a space after it
        if "pixdim4" in command:
            return "0.720000 "
        if "dim4" in command:
            return "10 "
        return "1.5"

    monkeypatch.setattr(pc, "run_external_for_file", external)
    monkeypatch.setattr(subprocess, "check_output", capture)

    result = qc_hcp._run_qc_bold(
        {"id": "sess-01"},
        {"hcp_suffix": "", "hcp_filename": "automated"},
        True,
        {"hcp_nonlin": str(nonlin), "base": str(nonlin.parent)},
        {
            "run": True,
            "template_scene": str(template),
            "outpath": str(outpath),
            "qclog": str(outpath / "qclog"),
            "timestamp": "ts",
            "boldinfo": {"bold_number": "1", "name": "bold1"},
            "hcp_cifti_tail": "_Atlas",
            "scenezip": "no",
            "snronly": "no",
            "skipframes": skipframes,
        },
    )

    assert result["report"] == {"done": ["BOLD1"], "failed": []}, result["r"]
    # ten frames of 0.72 s
    scene = (outpath / "sess-01.BOLD.1.QC.wb.scene").read_text()
    assert scene == "XMAX=7.2 YMIN=%s YMAX=10.0\n" % ymin


def test_run_qc_renders_the_custom_myelin_scenes_from_their_documented_folder(
    bold_session, tmp_path
):
    """
    Custom myelin scenes were looked for in processing/scenes/QC/Myelin, the
    modality's name in the code, and create_study, run_qc and the docs all name
    the folder myelin: on a case-sensitive file system none was rendered.
    """
    sinfo, options, templates = bold_session
    (templates / "template_myelin_qc.wb.scene").write_text("DUMMYPATH")
    custom = tmp_path / "processing" / "scenes" / "QC" / "myelin"
    custom.mkdir(parents=True)
    (custom / "custom.scene").write_text("DUMMYPATH")

    log = qc_hcp.hcp_run_qc(sinfo, options(qc_modality="myelin", qc_processcustom="yes"))

    assert "custom.scene" in log.status[1], log.status
    assert log.status[2] == 0, log.text
