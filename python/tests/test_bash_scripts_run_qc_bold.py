#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``run_qc`` with ``--modality=BOLD``, run with stub tools.

Split from ``test_bash_scripts.py``, whose helpers it uses: custom and user
scenes are reported and ignored, the default scene is read from
``--scenetemplatefolder``, a failed render fails the run and a rerun renders it
again rather than finding it done; ``--skipframes`` takes a number of frames
and leaves out that many, and the chart's axis ends at the duration, or charts
a run it would leave empty whole; nothing is written into the folder the script
is run from; BOLD FC reads the scalar template and the input of each session
and BOLD, a relative ``--boldfcpath`` is written into the scene absolute,
and an unknown FC type is an error. A BOLD template the template
folder lacks is taken from the library, or stops the run when the library has
none either; ``--overwrite`` removes only the QC a run renders again.
"""

import shutil
import sys

import pytest

from tests.test_bash_scripts import BASH, run_script, write_stub

pytestmark = pytest.mark.skipif(
    BASH is None or sys.platform == "win32", reason="needs bash"
)


# run_qc, BOLD


BOLD_TOKENS = (
    "DUMMYPATH DUMMYCASE DUMMYBOLDDATA _DUMMYBOLDSUFFIX DUMMYTIMESTAMP DUMMYBOLDANNOT "
    "DUMMYPNGNAMEGSMAP DUMMYPNGNAMEGSTIME DUMMYXAXISMAX DUMMYYAXISMAX DUMMYYAXISMIN"
)
FC_TOKENS = "DUMMYPATH DUMMYCASE DUMMYTIMESTAMP DUMMYIMAGEPATH DUMMYIMAGEFILE DUMMYPNGNAME"


def bold_wb_command_stub(tmp_path, failing=False):
    """A wb_command for the BOLD QC: ten frames, and the arguments it was given."""
    show = "exit 1" if failing else 'touch "$4"'
    write_stub(
        tmp_path / "stubs",
        "wb_command",
        f'echo "$*" >> "{tmp_path / "stubs" / "wb_command.calls"}"\n'
        'case "$1" in\n'
        '  -cifti-reduce) touch "$4" ;;\n'
        "  -cifti-stats)\n"
        '    case "$2" in\n'
        "      *_GS.dtseries.nii) seq 1 10 ;;\n"
        "      *) echo 1 ;;\n"
        "    esac ;;\n"
        '  -cifti-create-scalar-series) touch "$3" ;;\n'
        f"  -show-scene) {show} ;;\n"
        '  -zip-scene-file) touch "$4" ;;\n'
        "esac\n"
        "exit 0",
    )


@pytest.fixture
def run_qc_bold_study(tmp_path):
    study = tmp_path / "study"
    session = study / "sessions" / "S1"
    for bold in ["1", "2"]:
        results = session / "hcp" / "S1" / "MNINonLinear" / "Results" / bold
        results.mkdir(parents=True)
        (results / f"{bold}_Atlas.dtseries.nii").write_text("dtseries")
        (results / f"{bold}.nii.gz").write_text("bold")
    (session / "session_hcp.txt").write_text("id: S1\n")
    functional = session / "images" / "functional"
    functional.mkdir(parents=True)
    for bold in ["1", "2"]:
        (functional / f"bold{bold}_fc.pscalar.nii").write_text("fc")
    # a custom scene, which a BOLD run does not render, as a custom or a user scene
    custom = study / "processing" / "scenes" / "QC" / "BOLD"
    custom.mkdir(parents=True)
    (custom / "custom_bold.scene").write_text(BOLD_TOKENS + "\n")
    # the templates, given with --scenetemplatefolder: the CI workflow has no
    # qx_library, and no TOOLS or QUNEXREPO to find it with
    scenes = tmp_path / "scenes"
    scenes.mkdir()
    (scenes / "template_bold_qc.wb.scene").write_text("default " + BOLD_TOKENS + "\n")
    (scenes / "template_scalar_bold_qc.wb.scene").write_text("scalar " + FC_TOKENS + "\n")
    # fslval prints its value with a space after it
    write_stub(
        tmp_path / "stubs",
        "fslval",
        'case "$2" in pixdim4) echo "0.720000 " ;; dim4) echo "10 " ;; esac',
    )
    return study, scenes


def run_qc_bold(tmp_path, study, scenes, *args, **extra_env):
    return run_script(
        tmp_path,
        "run_qc",
        [
            f"--studyfolder={study}",
            "--sessions=S1",
            "--modality=BOLD",
            "--bolddata=1",
            "--boldsuffix=Atlas",
            f"--scenetemplatefolder={scenes}",
            *args,
        ],
        **extra_env,
    )


def bold_qc(study, pattern):
    return list((study / "sessions" / "QC" / "BOLD").glob(pattern))


def bold_results(study, bold="1"):
    return study / "sessions" / "S1" / "hcp" / "S1" / "MNINonLinear" / "Results" / bold


def test_run_qc_renders_the_default_bold_scene_and_writes_nothing_where_it_is_run(
    run_qc_bold_study, tmp_path
):
    """
    The BOLD scene came from the library whatever --scenetemplatefolder said,
    and `[ ${SkipFrames} > 0 ]` wrote a file named `0` into the folder the
    script was run from.
    """
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)
    before = set(tmp_path.iterdir())

    result = run_qc_bold(tmp_path, study, scenes)

    assert result.returncode == 0, result.stdout + result.stderr
    assert bold_qc(study, "S1.BOLD.1.QC.wb.scene.*.GStimeseries.QC.wb.png"), result.stdout
    scene = (study / "sessions" / "QC" / "BOLD" / "S1.BOLD.1.QC.wb.scene").read_text()
    assert scene.startswith("default ")
    assert set(tmp_path.iterdir()) == before
    # the global signal is a TR apart, and its chart ends at the duration: ten
    # frames of 0.72 s. It was a frame count apart, on an axis of ten
    calls = (tmp_path / "stubs" / "wb_command.calls").read_text()
    assert "-series SECOND 0 0.720000" in calls, calls
    assert " 7.20 " in scene, scene


@pytest.mark.parametrize(
    "given, ignored",
    [
        (["--processcustom=yes"], "--processcustom"),
        (["--customqc=yes"], "--processcustom"),
        (["--userscenefile=CUSTOM"], "--userscenefile"),
        # a user scene that is not there stopped the run
        (["--processcustom=yes", "--userscenefile=missing.scene"],
         "--processcustom and --userscenefile"),
        # a user scene folder alone made the run read the library templates
        (["--userscenepath=CUSTOM_FOLDER"], "--userscenepath"),
    ],
)
def test_run_qc_ignores_custom_and_user_scenes_for_bold(
    run_qc_bold_study, tmp_path, given, ignored
):
    """They replaced the default scene, and nothing checked what they made."""
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)
    custom = study / "processing" / "scenes" / "QC" / "BOLD" / "custom_bold.scene"
    given = [
        arg.replace("CUSTOM_FOLDER", str(custom.parent)).replace("CUSTOM", str(custom))
        for arg in given
    ]

    result = run_qc_bold(tmp_path, study, scenes, *given)

    assert result.returncode == 0, result.stdout + result.stderr
    warning = f"WARNING: Custom and user scenes are not available for BOLD, ignoring {ignored}."
    assert warning in result.stdout
    assert bold_qc(study, "S1.BOLD.1.QC.wb.scene.*.GStimeseries.QC.wb.png"), result.stdout
    scene = (study / "sessions" / "QC" / "BOLD" / "S1.BOLD.1.QC.wb.scene").read_text()
    assert scene.startswith("default "), scene
    assert not bold_qc(study, "*custom_bold*")
    assert "Running QC completion checks" in result.stdout


def test_run_qc_bold_with_processcustom_fails_when_the_render_fails(
    run_qc_bold_study, tmp_path
):
    """The custom BOLD scenes were never checked: a failed render exited 0."""
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path, failing=True)

    result = run_qc_bold(tmp_path, study, scenes, "--processcustom=yes")

    assert result.returncode != 0, result.stdout
    assert "QC generation did not complete correctly" in result.stdout


def test_run_qc_bold_reruns_a_failed_render(run_qc_bold_study, tmp_path):
    """
    The scene zip is made also when the render fails, and a rerun looked for
    the zip alone: it reported the failed QC as done by a previous run.
    """
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path, failing=True)
    failed = run_qc_bold(tmp_path, study, scenes)
    assert failed.returncode != 0, failed.stdout
    assert bold_qc(study, "S1.BOLD.1.QC.wb.scene.*.zip")
    bold_wb_command_stub(tmp_path)

    rerun = run_qc_bold(tmp_path, study, scenes)

    assert rerun.returncode == 0, rerun.stdout + rerun.stderr
    assert "Found files from a previous run" not in rerun.stdout
    assert bold_qc(study, "S1.BOLD.1.QC.wb.scene.*.GStimeseries.QC.wb.png"), rerun.stdout
    # with the png made, a later run still finds the QC done
    assert "Found files from a previous run" in run_qc_bold(tmp_path, study, scenes).stdout


@pytest.mark.parametrize("snronly", ["no", "yes"])
def test_run_qc_bold_with_omitdefaults_says_it_renders_nothing(
    run_qc_bold_study, tmp_path, snronly
):
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)

    result = run_qc_bold(tmp_path, study, scenes, "--omitdefaults=yes", f"--snronly={snronly}")

    assert result.returncode == 0, result.stdout + result.stderr
    assert ("no BOLD QC is rendered" in result.stdout) == (snronly == "no")
    assert not bold_qc(study, "*.png")
    assert bool(bold_qc(study, "S1_1_TSNR_Report_*.txt")) == (snronly == "yes")


@pytest.mark.parametrize("omitdefaults", ["YES", "true"])
def test_run_qc_bold_says_it_renders_nothing_for_any_omitdefaults_but_no(
    run_qc_bold_study, tmp_path, omitdefaults
):
    """A value other than yes or no omitted the default scene without a word."""
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)

    result = run_qc_bold(tmp_path, study, scenes, f"--omitdefaults={omitdefaults}")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "no BOLD QC is rendered" in result.stdout
    assert not bold_qc(study, "*.png")


def test_run_qc_bold_overwrite_keeps_the_qc_a_run_does_not_render(run_qc_bold_study, tmp_path):
    """
    --overwrite removed the BOLD QC of the session, and with --omitdefaults
    nothing took its place; a BOLD FC run removed the default BOLD QC too.
    """
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)
    assert run_qc_bold(tmp_path, study, scenes).returncode == 0
    made = set(bold_qc(study, "S1.BOLD.1.*"))
    assert len(made) == 4, made

    omitted = run_qc_bold(tmp_path, study, scenes, "--omitdefaults=yes", "--overwrite=yes")
    fc = run_qc_bold(
        tmp_path,
        study,
        scenes,
        "--boldfc=pscalar",
        "--boldfcinput=fc.pscalar.nii",
        "--overwrite=yes",
    )

    assert omitted.returncode == 0, omitted.stdout + omitted.stderr
    assert fc.returncode == 0, fc.stdout + fc.stderr
    assert set(bold_qc(study, "S1.BOLD.1.*")) == made
    assert bold_qc(study, "S1.pscalar.BOLD.1.QC.wb.scene.*.png"), fc.stdout


def test_run_qc_bold_overwrite_replaces_the_qc_it_renders(run_qc_bold_study, tmp_path):
    """The earlier QC of the BOLD a run renders again is removed, its FC QC too."""
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)
    qc = study / "sessions" / "QC" / "BOLD"
    qc.mkdir(parents=True)
    earlier = [
        qc / "S1.BOLD.1.QC.wb.scene.2020-01-01_00.00.00.000000.GSmap.QC.wb.png",
        qc / "S1.pscalar.BOLD.1.QC.wb.scene.2020-01-01_00.00.00.000000.png",
    ]
    for png in earlier:
        png.write_text("an earlier png\n")

    default = run_qc_bold(tmp_path, study, scenes, "--overwrite=yes")
    fc = run_qc_bold(
        tmp_path,
        study,
        scenes,
        "--boldfc=pscalar",
        "--boldfcinput=fc.pscalar.nii",
        "--overwrite=yes",
    )

    assert default.returncode == 0, default.stdout + default.stderr
    assert fc.returncode == 0, fc.stdout + fc.stderr
    assert not any(png.exists() for png in earlier)
    assert len(bold_qc(study, "S1.BOLD.1.QC.wb.scene.*.GSmap.QC.wb.png")) == 1
    assert len(bold_qc(study, "S1.pscalar.BOLD.1.QC.wb.scene.*.png")) == 1


def library_templates(tmp_path, *names):
    """A QuNex library under TOOLS/QUNEXREPO that holds the named BOLD templates."""
    library = tmp_path / "tools" / "repo" / "qx_library" / "data" / "scenes" / "qc"
    library.mkdir(parents=True)
    for name in names:
        tokens = BOLD_TOKENS if name == "template_bold_qc.wb.scene" else FC_TOKENS
        (library / name).write_text(f"library {tokens}\n")
    return {"TOOLS": str(tmp_path / "tools"), "QUNEXREPO": "repo"}


BOLD_TEMPLATE_RUNS = [
    # a folder with the default BOLD template alone, run for BOLD FC
    (
        "template_scalar_bold_qc.wb.scene",
        ["--boldfc=pscalar", "--boldfcinput=fc.pscalar.nii"],
        "S1.pscalar.BOLD.1",
    ),
    # a folder with the BOLD FC template alone, run for the default scene
    ("template_bold_qc.wb.scene", [], "S1.BOLD.1"),
]


@pytest.mark.parametrize("missing, given, scene", BOLD_TEMPLATE_RUNS)
def test_run_qc_bold_takes_a_template_its_folder_lacks_from_the_library(
    run_qc_bold_study, tmp_path, missing, given, scene
):
    """
    The folder was checked for any BOLD scene, and a run that needed another
    one failed late, after reporting the template copied.
    """
    study, scenes = run_qc_bold_study
    (scenes / missing).unlink()
    bold_wb_command_stub(tmp_path)
    library = library_templates(tmp_path, missing)

    result = run_qc_bold(tmp_path, study, scenes, *given, **library)

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"holds no {missing}" in result.stdout
    text = (study / "sessions" / "QC" / "BOLD" / f"{scene}.QC.wb.scene").read_text()
    assert text.startswith("library "), text


@pytest.mark.parametrize("missing, given, scene", BOLD_TEMPLATE_RUNS)
def test_run_qc_bold_stops_when_no_folder_holds_its_template(
    run_qc_bold_study, tmp_path, missing, given, scene
):
    study, scenes = run_qc_bold_study
    (scenes / missing).unlink()
    bold_wb_command_stub(tmp_path)

    result = run_qc_bold(tmp_path, study, scenes, *given)

    assert result.returncode != 0, result.stdout
    error = f"ERROR: BOLD QC template not found: {scenes}/{missing}"
    assert error in result.stdout
    assert "can't read" not in result.stdout + result.stderr
    assert not bold_qc(study, "*")


@pytest.mark.parametrize("skipframes, skipped", [("2", 2), ("08", 8)])
def test_run_qc_skipframes_omits_that_many_frames(
    run_qc_bold_study, tmp_path, skipframes, skipped
):
    """It kept the frame it was to start after, and plotted a frame count apart."""
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)

    result = run_qc_bold(tmp_path, study, scenes, f"--skipframes={skipframes}")

    assert result.returncode == 0, result.stdout + result.stderr
    series = bold_results(study) / f"1_Atlas_GS_omit_initial_{skipped}_TRs.txt"
    assert series.read_text().split() == [str(frame) for frame in range(skipped + 1, 11)]
    calls = (tmp_path / "stubs" / "wb_command.calls").read_text()
    assert "-series SECOND 0 0.720000" in calls, calls
    # the frames left, 0.72 s apart
    scene = (study / "sessions" / "QC" / "BOLD" / "S1.BOLD.1.QC.wb.scene").read_text()
    assert " %.2f " % (0.72 * (10 - skipped)) in scene, scene


@pytest.mark.parametrize("skipframes", ["10", "12"])
def test_run_qc_charts_a_run_skipframes_would_leave_empty_whole(
    run_qc_bold_study, tmp_path, skipframes
):
    """It charted an empty series, on an axis that ended at 0."""
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)

    result = run_qc_bold(tmp_path, study, scenes, f"--skipframes={skipframes}")

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"WARNING: --skipframes={skipframes} leaves none of the 10 frames" in result.stdout
    assert not list(bold_results(study).glob("*_omit_initial_*"))
    scene = (study / "sessions" / "QC" / "BOLD" / "S1.BOLD.1.QC.wb.scene").read_text()
    assert " 7.20 " in scene, scene


@pytest.mark.parametrize("skipframes", ["two", "-1"])
def test_run_qc_rejects_skipframes_that_are_not_a_number_of_frames(
    run_qc_bold_study, tmp_path, skipframes
):
    """Such a value was taken for a number of frames, or ignored without a word."""
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)

    result = run_qc_bold(tmp_path, study, scenes, f"--skipframes={skipframes}")

    assert result.returncode != 0, result.stdout
    assert f"ERROR: --skipframes={skipframes} is not a number of frames." in result.stdout
    assert not bold_qc(study, "*")


def test_run_qc_bold_writes_the_global_signal_afresh(run_qc_bold_study, tmp_path):
    """It was appended to the series an earlier run left, and plotted twice."""
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)
    series = bold_results(study) / "1_Atlas_GS.txt"
    series.write_text("99\n99\n")

    result = run_qc_bold(tmp_path, study, scenes)

    assert result.returncode == 0, result.stdout + result.stderr
    assert series.read_text().split() == [str(frame) for frame in range(1, 11)]


def test_run_qc_bold_overwrite_removes_the_earlier_tsnr_reports(run_qc_bold_study, tmp_path):
    """They were removed by a name with an unset variable in it, so none was."""
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)
    qc = study / "sessions" / "QC" / "BOLD"
    qc.mkdir(parents=True)
    earlier = qc / "S1_1_TSNR_Report_2020-01-01_00.00.00.000000.txt"
    earlier.write_text("an earlier report\n")

    result = run_qc_bold(tmp_path, study, scenes, "--overwrite=yes")

    assert result.returncode == 0, result.stdout + result.stderr
    assert not earlier.exists()
    assert len(bold_qc(study, "S1_1_TSNR_Report_*.txt")) == 1


def test_run_qc_bold_fc_reads_the_scalar_template_and_the_input_of_each_session_and_bold(
    run_qc_bold_study, tmp_path
):
    """
    pscalar asked for a template qx_library does not ship, the second BOLD read
    `bold2_bold1_<input>`, and the second session the first one's folder.
    """
    study, scenes = run_qc_bold_study
    s2 = study / "sessions" / "S2"
    shutil.copytree(study / "sessions" / "S1", s2)
    (s2 / "hcp" / "S1").rename(s2 / "hcp" / "S2")
    (s2 / "session_hcp.txt").write_text("id: S2\n")
    bold_wb_command_stub(tmp_path)

    result = run_script(
        tmp_path,
        "run_qc",
        [
            f"--studyfolder={study}",
            "--sessions=S1,S2",
            "--modality=BOLD",
            "--bolddata=1,2",
            "--boldfc=pscalar",
            "--boldfcinput=fc.pscalar.nii",
            f"--scenetemplatefolder={scenes}",
        ],
    )

    assert result.returncode == 0, result.stdout + result.stderr
    for session in ["S1", "S2"]:
        functional = study / "sessions" / session / "images" / "functional"
        for bold in ["1", "2"]:
            scene = study / "sessions" / "QC" / "BOLD" / f"{session}.pscalar.BOLD.{bold}.QC.wb.scene"
            text = scene.read_text()
            assert text.startswith("scalar ")
            assert f" {functional} bold{bold}_fc.pscalar.nii " in text, text


def test_run_qc_bold_fc_ignores_custom_scenes_and_omitdefaults(run_qc_bold_study, tmp_path):
    """BOLD FC renders its scene whatever --omitdefaults says, so it does not warn."""
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)

    result = run_qc_bold(
        tmp_path,
        study,
        scenes,
        "--boldfc=pscalar",
        "--boldfcinput=fc.pscalar.nii",
        "--processcustom=yes",
        "--omitdefaults=yes",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "not available for BOLD, ignoring --processcustom." in result.stdout
    assert "no BOLD QC is rendered" not in result.stdout
    assert bold_qc(study, "S1.pscalar.BOLD.1.QC.wb.scene.*.png"), result.stdout


def test_run_qc_writes_a_relative_bold_fc_path_into_the_scene_absolute(
    run_qc_bold_study, tmp_path
):
    """
    Workbench reads a relative path in a scene from the scene's own folder, so
    the FC path, taken from the folder run_qc runs in, is written in absolute.
    """
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)
    functional = study / "sessions" / "S1" / "images" / "functional"

    result = run_qc_bold(
        tmp_path,
        study,
        scenes,
        "--boldfc=pscalar",
        "--boldfcinput=fc.pscalar.nii",
        f"--boldfcpath={functional.relative_to(tmp_path)}",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    scene = study / "sessions" / "QC" / "BOLD" / "S1.pscalar.BOLD.1.QC.wb.scene"
    text = scene.read_text()
    assert f" {functional} bold1_fc.pscalar.nii " in text, text


def test_run_qc_rejects_an_unknown_bold_fc_type(run_qc_bold_study, tmp_path):
    """It rendered the default BOLD scene with the FC input, and called it done."""
    study, scenes = run_qc_bold_study
    bold_wb_command_stub(tmp_path)

    result = run_qc_bold(
        tmp_path, study, scenes, "--boldfc=pscalr", "--boldfcinput=fc.pscalar.nii"
    )

    assert result.returncode != 0, result.stdout
    assert "ERROR: --boldfc=pscalr is not supported, use pscalar or pconn." in result.stdout
    assert not bold_qc(study, "*")
