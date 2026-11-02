#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``compute_bold_fc``, ``extract_roi`` and ``dwi_bedpostx_gpu``, run with stub tools.

The FC script judged a run by a CIFTI result of the run's own name, so a volume
result and a list run, whose results carry the name of the list, were failures
or went unchecked, and the exit status of the matlab call was not read at all.
bedpostx writes three merged files per fiber, and nine were all that counted.
``extract_roi`` printed an error when it wrote nothing, and exited 0 regardless.
"""

import sys

import pytest

from tests.test_bash_scripts import BASH, run_script, write_stub

pytestmark = pytest.mark.skipif(
    BASH is None or sys.platform == "win32", reason="needs bash"
)


def matlab_stub(tmp_path, result=None, status=0):
    """A QUNEXMCOMMAND that records its call, writes `result` and exits `status`."""
    touch = f'touch "{result}"\n' if result else ""
    write_stub(
        tmp_path / "stubs",
        "matlab_stub",
        f'echo "$@" >> "{tmp_path}/matlab_calls.txt"\n{touch}exit {status}',
    )
    return str(tmp_path / "stubs" / "matlab_stub")


@pytest.fixture
def fc_study(tmp_path):
    study = tmp_path / "study"
    functional = study / "sessions" / "S1" / "images" / "functional"
    functional.mkdir(parents=True)
    (functional / "bold1.nii.gz").write_text("bold")
    return study, functional


def run_gbc(tmp_path, study, command, *args):
    return run_script(
        tmp_path,
        "compute_bold_fc",
        [
            f"--studyfolder={study}",
            "--calculation=gbc",
            "--target=[17,18]",
            "--covariance=true",
            "--mem-limit=4",
            *args,
        ],
        QUNEXMCOMMAND=command,
    )


def individual(target):
    return [
        "--runtype=individual",
        "--sessions=S1",
        "--inputfiles=bold1.nii.gz",
        "--inputpath=images/functional",
        "--outname=out",
        f"--targetf={target}",
    ]


def test_compute_bold_fc_accepts_a_volume_result(fc_study, tmp_path):
    study, _ = fc_study
    target = tmp_path / "results"

    result = run_gbc(
        tmp_path,
        study,
        matlab_stub(tmp_path, target / "out_gbc_mFz.nii.gz"),
        *individual(target),
    )

    assert result.returncode == 0, result.stdout
    assert "Connectivity calculation completed" in result.stdout


def test_compute_bold_fc_fails_when_the_calculation_fails(fc_study, tmp_path):
    """The result of an earlier run was enough to report this one complete."""
    study, _ = fc_study
    target = tmp_path / "results"
    target.mkdir()
    (target / "out_gbc_mFz.nii.gz").write_text("an earlier result")

    result = run_gbc(tmp_path, study, matlab_stub(tmp_path, status=1), *individual(target))

    assert result.returncode == 1
    assert "ERROR --- gbc calculation failed" in result.stdout


def test_compute_bold_fc_fails_without_a_result(fc_study, tmp_path):
    study, _ = fc_study

    result = run_gbc(tmp_path, study, matlab_stub(tmp_path), *individual(tmp_path / "results"))

    assert result.returncode == 1
    assert "not found" in result.stdout


@pytest.mark.parametrize("written, status", [(True, 0), (False, 1)])
def test_compute_bold_fc_checks_a_list_run_by_the_name_of_the_list(
    fc_study, tmp_path, written, status
):
    """A list run has no --outname: it was never checked, and always passed."""
    study, functional = fc_study
    target = tmp_path / "results"
    flist = tmp_path / "group.list"
    flist.write_text(f"session id: S1\nfile: {functional / 'bold1.nii.gz'}\n")

    result = run_gbc(
        tmp_path,
        study,
        matlab_stub(tmp_path, target / "group_gbc_mFz.nii.gz" if written else None),
        "--runtype=list",
        f"--flist={flist}",
        f"--targetf={target}",
    )

    assert result.returncode == status, result.stdout


@pytest.mark.parametrize("name, stem", [("group.txt", "group"), ("group.v2.list", "group.v2")])
def test_a_list_run_is_checked_by_the_name_matlab_gives_its_results(fc_study, tmp_path, name, stem):
    """matlab drops the last extension, and only `.list` was dropped here."""
    study, functional = fc_study
    target = tmp_path / "results"
    flist = tmp_path / name
    flist.write_text(f"session id: S1\nfile: {functional / 'bold1.nii.gz'}\n")

    result = run_gbc(
        tmp_path,
        study,
        matlab_stub(tmp_path, target / f"{stem}_gbc_mFz.nii.gz"),
        "--runtype=list",
        f"--flist={flist}",
        f"--targetf={target}",
    )

    assert result.returncode == 0, result.stdout


def test_a_list_run_shows_the_list_it_was_given(fc_study, tmp_path):
    study, functional = fc_study
    target = tmp_path / "results"
    flist = tmp_path / "group.list"
    flist.write_text(f"file: {functional / 'bold1.nii.gz'}\n")

    result = run_gbc(
        tmp_path,
        study,
        matlab_stub(tmp_path, target / "group_gbc_mFz.nii.gz"),
        "--runtype=list",
        f"--flist={flist}",
        f"--targetf={target}",
    )

    assert f"file: {functional / 'bold1.nii.gz'}" in result.stdout
    assert f"fc_compute_gbc3('{flist}'" in (tmp_path / "matlab_calls.txt").read_text()


# dwi_bedpostx_gpu


@pytest.mark.parametrize("fibers", [1, 2, 3])
def test_bedpostx_counts_three_merged_files_per_fiber(tmp_path, fibers):
    """Nine merged files were expected: only a run of three fibers was ever complete."""
    study = tmp_path / "study"
    bedpostx = study / "sessions" / "S1" / "hcp" / "S1" / "T1w" / "Diffusion.bedpostX"
    bedpostx.mkdir(parents=True)
    (bedpostx / "mean_d_stdsamples.nii.gz").write_text("")
    for fiber in range(1, fibers + 1):
        for name in ["th", "ph", "f"]:
            (bedpostx / f"merged_{name}{fiber}samples.nii.gz").write_text("")
    # the size that says the run is complete
    with open(bedpostx / "merged_f1samples.nii.gz", "wb") as f:
        f.truncate(3000000)

    result = run_script(
        tmp_path,
        "dwi_bedpostx_gpu",
        [
            f"--studyfolder={study}",
            "--session=S1",
            f"--fibers={fibers}",
            "--overwrite=no",
            "--model=2",
        ],
    )

    assert f"{fibers * 3} merged samples for S1 found" in result.stdout, result.stdout


# run_qc, modality DWI


@pytest.fixture
def run_qc_dwi_study(tmp_path):
    study = tmp_path / "study"
    session = study / "sessions" / "S1"
    (session / "session_hcp.txt").parent.mkdir(parents=True)
    (session / "session_hcp.txt").write_text("id: S1\n")
    t1w = session / "hcp" / "S1" / "T1w"
    for folder in ["Diffusion", "Diffusion_b3"]:
        (t1w / folder).mkdir(parents=True)
        (t1w / folder / "data.nii.gz").write_text("data")
        (t1w / folder / "nodif_brain_mask.nii.gz").write_text("mask")
    scenes = tmp_path / "scenes"
    scenes.mkdir()
    (scenes / "template_dwi_qc.wb.scene").write_text(
        "DUMMYPATH DUMMYCASE DUMMYTIMESTAMP DUMMYPNGNAME DUMMYDWIPATH\n"
    )
    for tool in ["fslsplit", "fslmaths"]:
        write_stub(tmp_path / "stubs", tool, "exit 0")
    write_stub(
        tmp_path / "stubs",
        "wb_command",
        'case "$1" in\n  -show-scene) touch "$4" ;;\n  -zip-scene-file) touch "$4" ;;\nesac\nexit 0',
    )
    return study, scenes


def run_qc_dwi(tmp_path, study, scenes, *args):
    return run_script(
        tmp_path,
        "run_qc",
        [
            f"--studyfolder={study}",
            "--sessions=S1",
            "--modality=DWI",
            "--dwidata=data",
            f"--scenetemplatefolder={scenes}",
            *args,
        ],
    )


def test_run_qc_eddyqcstats_stops_and_says_what_it_needs(run_qc_dwi_study, tmp_path):
    """Without the outputs of dwi_eddy_qc it noted that and reported success."""
    study, scenes = run_qc_dwi_study

    result = run_qc_dwi(tmp_path, study, scenes, "--eddyqcstats=yes")

    assert result.returncode != 0
    assert "EDDY QC outputs missing for S1" in result.stdout
    assert "run dwi_eddy_qc before this QC" in result.stdout


def test_run_qc_reads_eddy_and_bedpostx_of_the_dwipath_it_is_given(run_qc_dwi_study, tmp_path):
    """`Diffusion` was hard coded here, whatever --dwipath named."""
    study, scenes = run_qc_dwi_study
    hcp = study / "sessions" / "S1" / "hcp" / "S1"
    eddy = hcp / "Diffusion_b3" / "eddy" / "eddy_unwarped_images.qc"
    eddy.mkdir(parents=True)
    (eddy / "qc.pdf").write_text("pdf")
    (eddy / "qc.json").write_text('"qc_mot_abs": 1.5,\n')
    bedpostx = hcp / "T1w" / "Diffusion_b3.bedpostX"
    bedpostx.mkdir()
    for fiber in [1, 2]:
        for name in ["th", "ph", "f"]:
            (bedpostx / f"merged_{name}{fiber}samples.nii.gz").write_text("")
    with open(bedpostx / "merged_f1samples.nii.gz", "wb") as f:
        f.truncate(30000000)

    result = run_qc_dwi(
        tmp_path, study, scenes, "--dwipath=Diffusion_b3", "--eddyqcstats=yes", "--bedpostxqc=yes"
    )

    assert "EDDY QC outputs found" in result.stdout, result.stdout
    assert "FSLBedpostX outputs missing" not in result.stdout, result.stdout
    assert list((study / "sessions" / "QC" / "DWI").glob("S1.DWI.eddy.QC.pdf"))


@pytest.mark.parametrize(
    "written, status, succeeds",
    [(True, 0, True), (False, 0, False), (False, 1, False)],
    ids=["its result", "no result", "the call failed"],
)
def test_extract_roi_fails_without_its_result(tmp_path, written, status, succeeds):
    csv = tmp_path / "roi.csv"
    command = matlab_stub(tmp_path, result=csv if written else None, status=status)

    result = run_script(
        tmp_path,
        "extract_roi",
        [
            "--roifile=roi.nii.gz",
            "--inputfile=bold.nii.gz",
            f"--outpath={tmp_path}",
            "--outname=roi",
        ],
        QUNEXMCOMMAND=command,
    )

    assert (result.returncode == 0) is succeeds, result.stdout + result.stderr
    assert "try, imgf=nimage" in (tmp_path / "matlab_calls.txt").read_text()
