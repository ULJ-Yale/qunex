#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Option parsing and exit codes of the bash commands, run with stub tools.

Each test runs a script from ``bash/qx_utilities`` with ``bash`` in a scratch
study, with the neuroimaging tools it calls replaced by small stubs on a PATH
that holds nothing else but the system folders, and with an environment built
from scratch: none of ``TOOLS``, ``QUNEXPATH`` or ``QUNEXREPO`` is set, as in
the CI workflow.

- ``dwi_dtifit``: a flag is set only by its own name (``--kurtdir`` is not
  ``--kurt``), and ``--flag=no`` does not set it.
- ``parcellate_anat``: ``--extractdata`` given bare, its documented form before,
  still asks for the CSV file.
- ``dwi_legacy_gpu``: ``--nogpu`` given bare is accepted, and ``--nogpu=true``
  asks for the cpu as well.
- ``run_qc``: a failed QC makes the script exit non-zero, which is all gmri
  judges a bash command by, also when a later session succeeds.
- ``run_qc``: the other modalities still render their custom scenes.
- ``run_qc``: a relative ``--outpath`` is taken from the folder the script
  runs in, and made absolute: the QC scripts change into the output folder.

``run_qc`` with ``--modality=BOLD`` is covered in
``test_bash_scripts_run_qc_bold.py``, and ``bin/qunex.sh`` in
``test_bash_scripts_qunex_sh.py``; both import their helpers from here.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BASH = shutil.which("bash")
SCRIPTS = Path(__file__).resolve().parents[2] / "bash" / "qx_utilities"
REPO = SCRIPTS.parents[1]
SYSTEM_PATH = "/usr/bin:/bin"

pytestmark = pytest.mark.skipif(
    BASH is None or sys.platform == "win32", reason="needs bash"
)


def write_stub(folder, name, body):
    """Write an executable stub tool `name` into `folder`."""
    folder.mkdir(parents=True, exist_ok=True)
    stub = folder / name
    stub.write_text(f"#!{BASH}\n{body}\n")
    stub.chmod(0o755)
    return stub


def run_script(tmp_path, script, args, **extra_env):
    """Run `script` with bash, the stubs in tmp_path/stubs first on PATH."""
    env = {
        "PATH": f"{tmp_path / 'stubs'}:{SYSTEM_PATH}",
        "HOME": str(tmp_path),
        "TMPDIR": str(tmp_path),
        "LC_ALL": "C",
    }
    env.update(extra_env)
    return subprocess.run(
        [BASH, str(SCRIPTS / f"{script}.sh"), *args],
        cwd=tmp_path,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
    )


def reported(result):
    """The stripped lines of the script's output."""
    return [line.strip() for line in result.stdout.splitlines()]


# dwi_dtifit


DTIFIT_FLAGS = {"--sse", "--wls", "--kurt", "--kurtdir", "--littlebit", "--save_tensor"}


@pytest.fixture
def dtifit_study(tmp_path):
    study = tmp_path / "study"
    (study / "sessions" / "S1" / "hcp" / "S1" / "T1w" / "Diffusion").mkdir(parents=True)
    args_log = tmp_path / "dtifit.args"
    # the stub records its arguments one per line and writes an FA image large
    # enough for the script's completion check
    write_stub(
        tmp_path / "stubs",
        "dtifit",
        f'printf "%s\\n" "$@" > "{args_log}"\n'
        'for a in "$@"; do case "$a" in --out=*) out="${a#--out=}" ;; esac; done\n'
        'head -c 200000 /dev/zero > "${out}_FA.nii.gz"',
    )
    return study, args_log


@pytest.mark.parametrize(
    "flags, expected",
    [
        # --kurtdir used to set --kurt too, and --wls=no used to set --wls
        (["--kurtdir", "--wls=no"], {"--kurtdir"}),
        (["--sse=YES", "--save_tensor=true"], {"--sse", "--save_tensor"}),
        (["--kurt", "--littlebit=yes", "--sse=no"], {"--kurt", "--littlebit"}),
        ([], set()),
    ],
)
def test_dtifit_sets_a_flag_only_by_its_own_name(dtifit_study, tmp_path, flags, expected):
    study, args_log = dtifit_study

    result = run_script(
        tmp_path, "dwi_dtifit", [f"--studyfolder={study}", "--sessions=S1", *flags]
    )

    passed = {a for a in args_log.read_text().splitlines() if a in DTIFIT_FLAGS}
    assert passed == expected, result.stdout
    lines = reported(result)
    for flag in DTIFIT_FLAGS:
        line = f"{flag[2:]}: yes"
        assert (line in lines) == (flag in expected), (line, result.stdout)
    if shutil.which("bc", path=SYSTEM_PATH):
        # the completion check compares sizes with bc
        assert result.returncode == 0, result.stdout + result.stderr


# parcellate_anat


@pytest.fixture
def parcellate_anat_study(tmp_path):
    study = tmp_path / "study"
    fsaverage = study / "sessions" / "S1" / "hcp" / "S1" / "MNINonLinear" / "fsaverage_LR32k"
    fsaverage.mkdir(parents=True)
    (fsaverage / "S1.MyelinMap.32k_fs_LR.dscalar.nii").write_text("dense")
    (tmp_path / "p.dlabel.nii").write_text("labels")
    write_stub(
        tmp_path / "stubs",
        "wb_command",
        'case "$1" in\n'
        '  -cifti-parcellate) echo parcellated > "$5" ;;\n'
        '  -nifti-information) echo "1,2,3" ;;\n'
        "esac\n"
        "exit 0",
    )
    return study, fsaverage


@pytest.mark.parametrize(
    "extractdata, csv_written",
    [(["--extractdata"], True), (["--extractdata=yes"], True), (["--extractdata=no"], False)],
)
def test_parcellate_anat_takes_extractdata_bare_or_with_a_value(
    parcellate_anat_study, tmp_path, extractdata, csv_written
):
    study, fsaverage = parcellate_anat_study

    result = run_script(
        tmp_path,
        "parcellate_anat",
        [
            f"--studyfolder={study}",
            "--session=S1",
            "--inputdatatype=MyelinMap",
            f"--parcellationfile={tmp_path / 'p.dlabel.nii'}",
            "--outname=x",
            *extractdata,
        ],
    )

    assert "Unrecognized Option" not in result.stdout
    assert result.returncode == 0, result.stdout + result.stderr
    assert ("ExtractData: yes" in reported(result)) == csv_written
    assert (fsaverage / "S1.MyelinMap.32k_fs_LR_x.pscalar.nii").is_file()
    csv = fsaverage / "S1.MyelinMap.32k_fs_LR_x.csv"
    assert csv.is_file() == csv_written
    if csv_written:
        assert csv.read_text().strip() == "1,2,3"


# dwi_legacy_gpu


@pytest.mark.parametrize(
    "nogpu, expected",
    [
        (["--nogpu"], "yes"),
        (["--nogpu=true"], "yes"),
        (["--nogpu=YES"], "yes"),
        (["--nogpu=no"], "no"),
        ([], ""),
    ],
)
def test_dwi_legacy_gpu_takes_nogpu_bare_or_with_a_value(tmp_path, nogpu, expected):
    study = tmp_path / "study"
    (study / "sessions" / "S1").mkdir(parents=True)
    # the script sources two HCP Pipelines libraries before it parses anything
    hcppipedir = tmp_path / "HCPpipelines"
    (hcppipedir / "global" / "scripts").mkdir(parents=True)
    for library in ["log.shlib", "version.shlib"]:
        (hcppipedir / "global" / "scripts" / library).write_text("")

    # without the spin echo images the script stops right after reporting its
    # options, before any FSL tool is called
    result = run_script(
        tmp_path,
        "dwi_legacy_gpu",
        [
            f"--studyfolder={study}",
            "--sessions=S1",
            "--pedir=1",
            "--echospacing=0.5",
            "--unwarpdir=y",
            "--usesefieldmap=yes",
            "--diffdatasuffix=DWI",
            *nogpu,
        ],
        HCPPIPEDIR=str(hcppipedir),
    )

    assert "Unrecognized Option" not in result.stdout
    assert f"No GPU: {expected}".strip() in reported(result), result.stdout
    assert "Spin Echo field map images not found" in result.stdout


# run_qc


@pytest.fixture
def run_qc_study(tmp_path):
    study = tmp_path / "study"
    for session in ["S1", "S2"]:
        folder = study / "sessions" / session
        (folder / "hcp" / session / "MNINonLinear").mkdir(parents=True)
        (folder / "hcp" / session / "MNINonLinear" / "T1w_restore.nii.gz").write_text("t1w")
        (folder / "session_hcp.txt").write_text(f"id: {session}\n")
    # a template with the placeholders run_qc fills; the default templates are
    # in the qx_library submodule, which the CI workflow does not check out
    scenes = tmp_path / "scenes"
    scenes.mkdir()
    (scenes / "template_t1w_qc.wb.scene").write_text(
        "DUMMYPATH DUMMYCASE DUMMYTIMESTAMP DUMMYPNGNAME\n"
    )
    return study, scenes


def wb_command_stub(tmp_path, failing=()):
    """A wb_command that writes its outputs, or fails for the given sessions."""
    fail = "".join(f"    *{session}.T1w*) exit 1 ;;\n" for session in failing)
    write_stub(
        tmp_path / "stubs",
        "wb_command",
        'case "$1" in\n'
        "  -show-scene)\n"
        '    case "$2" in\n'
        f"{fail}"
        "    esac\n"
        '    touch "$4" ;;\n'
        '  -zip-scene-file) touch "$4" ;;\n'
        "esac\n"
        "exit 0",
    )


def run_qc(tmp_path, study, scenes):
    return run_script(
        tmp_path,
        "run_qc",
        [
            f"--studyfolder={study}",
            "--sessions=S1,S2",
            "--modality=T1w",
            f"--scenetemplatefolder={scenes}",
        ],
    )


def qc_png(study, session):
    qc = study / "sessions" / "QC" / "T1w"
    return list(qc.glob(f"{session}.T1w.QC.wb.scene.*.png"))


def test_run_qc_exits_zero_when_the_qc_is_made(run_qc_study, tmp_path):
    study, scenes = run_qc_study
    wb_command_stub(tmp_path)

    result = run_qc(tmp_path, study, scenes)

    assert result.returncode == 0, result.stdout + result.stderr
    assert qc_png(study, "S1") and qc_png(study, "S2")
    assert "QC generation did not complete correctly" not in result.stdout


def test_run_qc_exits_non_zero_when_the_qc_fails(run_qc_study, tmp_path):
    study, scenes = run_qc_study
    wb_command_stub(tmp_path, failing=["S1", "S2"])

    result = run_qc(tmp_path, study, scenes)

    assert result.returncode != 0, result.stdout
    assert "QC generation did not complete correctly" in result.stdout
    assert not qc_png(study, "S1") and not qc_png(study, "S2")


def test_run_qc_remembers_a_failed_session_a_later_one_does_not_clear(
    run_qc_study, tmp_path
):
    study, scenes = run_qc_study
    wb_command_stub(tmp_path, failing=["S1"])

    result = run_qc(tmp_path, study, scenes)

    assert result.returncode != 0, result.stdout
    assert "QC generation did not complete correctly" in result.stdout
    assert not qc_png(study, "S1")
    assert qc_png(study, "S2")


@pytest.mark.skipif(
    shutil.which("rsync", path=SYSTEM_PATH) is None, reason="custom scenes are copied with rsync"
)
def test_run_qc_renders_custom_scenes_beside_the_default_for_other_modalities(
    run_qc_study, tmp_path
):
    study, scenes = run_qc_study
    custom = study / "processing" / "scenes" / "QC" / "T1w"
    custom.mkdir(parents=True)
    (custom / "mine.scene").write_text("DUMMYPATH DUMMYCASE DUMMYTIMESTAMP DUMMYPNGNAME\n")
    wb_command_stub(tmp_path)

    result = run_script(
        tmp_path,
        "run_qc",
        [
            f"--studyfolder={study}",
            "--sessions=S1",
            "--modality=T1w",
            f"--scenetemplatefolder={scenes}",
            "--processcustom=yes",
        ],
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "not available" not in result.stdout
    qc = study / "sessions" / "QC" / "T1w"
    assert qc_png(study, "S1")
    assert list(qc.glob("S1.T1w.mine.scene.*.png")), result.stdout
    # the scene check tested an unquoted grep, which passed by accident
    assert "too many arguments" not in result.stderr, result.stderr


def test_run_qc_takes_a_relative_outpath_from_the_folder_it_runs_in(
    run_qc_study, tmp_path
):
    """
    The QC scripts change into the output folder and then name files in it by
    the same path, so a relative --outpath left the scene zip uncopied.
    """
    study, scenes = run_qc_study
    wb_command_stub(tmp_path)

    result = run_script(
        tmp_path,
        "run_qc",
        [
            f"--studyfolder={study}",
            "--sessions=S1",
            "--modality=T1w",
            f"--scenetemplatefolder={scenes}",
            "--outpath=QC/T1w",
        ],
    )

    assert "cannot stat" not in result.stdout + result.stderr
    assert result.returncode == 0, result.stdout + result.stderr
    qc = tmp_path / "QC" / "T1w"
    assert list(qc.glob("S1.T1w.QC.wb.scene.*.png")), result.stdout
    assert list((study / "sessions" / "S1" / "hcp" / "S1" / "qc").glob("*.zip"))
