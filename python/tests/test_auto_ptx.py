#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
auto_ptx end to end: ``qunex auto_ptx`` and the autoPtx scripts it runs.

The scripts in ``bash/qx_utilities/diffusion_tractography_dense/
auto_ptx_hcp_extended`` run as they are, on a session tree laid out as
hcp_diffusion, dwi_bedpostx_gpu and the HCP structural pipelines leave it, with
the FSL tools they call replaced by stubs (``$FSLDIR/bin`` and the PATH) that
write the images they are asked for, and with a small autoPtx library of three
structures: a plain one, one tracked both ways (``invert``) and one with two
waypoints, the three kinds of protocol the library holds.

auto_ptx had not run since 2021: the environment named a folder that had been
renamed, ``bin/qunex.sh`` called a script by its old name with the sessions
folder and the bedpostX path where the script takes the session's hcp folder
and the bedpostX folder's name, and prepared for display a results folder the
script does not write. Inside, the tractography had no probtrackx2 unless the
GPU was asked for, wrote the waypoint list of a structure into the library,
and lost its own scripts when it was started by a relative path.
"""

import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

BASH = shutil.which("bash")
REPO = Path(__file__).resolve().parents[2]
SCRIPTS = (
    REPO / "bash" / "qx_utilities" / "diffusion_tractography_dense" / "auto_ptx_hcp_extended"
)
LIBRARY = REPO / "qx_library" / "etc" / "auto_ptx"
SYSTEM_PATH = "/usr/bin:/bin"

pytestmark = pytest.mark.skipif(
    BASH is None or sys.platform == "win32" or shutil.which("bc") is None,
    reason="needs bash and bc",
)

# the three kinds of protocol: name, files, and the line of the structure list
PROTOCOLS = {
    "atr_l": (["seed", "target", "exclude", "stop"], "atr_l 1 1:00:00"),
    "fma": (["seed", "target", "exclude", "invert"], "fma 0.6 8:00:00"),
    "slf1_l": (
        ["seed", "target1", "target2", "exclude", "randfib1"],
        "slf1_l 0.1 10:00:00",
    ),
}

# every tract average_auto_ptx.sh averages
ALL_TRACTS = (
    "ar_l atr_l cgc_l cgh_l cst_l fma ifo_l ilf_l ml_l ptr_l slf_l slf1_l slf2_l "
    "slf3_l str_l unc_l ar_r atr_r cgc_r cgh_r cst_r fmi ifo_r ilf_r mcp ml_r ptr_r "
    "slf_r slf1_r slf2_r slf3_r str_r unc_r"
).split()

# the FSL tools the scripts call; each records its call, then does its part
IMAGE = """
image() { case "$1" in *.nii.gz) echo "$1" ;; *) echo "$1.nii.gz" ;; esac; }
"""
STUBS = {
    "probtrackx2": """
for arg in "$@"; do case "$arg" in --dir=*) dir=${arg#--dir=} ;; esac; done
[ -n "$FAIL_STRUCT" ] && case "$dir" in */$FAIL_STRUCT/*) exit 1 ;; esac
mkdir -p "$dir"; echo img > "$dir/density.nii.gz"; echo 1000 > "$dir/waytotal"
""",
    "imcp": IMAGE
    + """
src=$(image "$1"); dst=$(image "$2"); [ -f "$src" ] || exit 1; cp "$src" "$dst"
""",
    "immv": IMAGE
    + """
src=$(image "$1"); dst=$(image "$2"); [ -f "$src" ] || exit 1; mv "$src" "$dst"
""",
    "imrm": IMAGE + 'for i in "$@"; do rm -f "$(image "$i")"; done',
    "fslmaths": IMAGE
    + """
[ -f "$(image "$1")" ] || exit 1
out=""; skip=0
for arg in "$@"; do
    if [ $skip = 1 ]; then skip=0; continue; fi
    case "$arg" in -odt) skip=1 ;; -*) ;; *) out=$arg ;; esac
done
echo img > "$(image "$out")"
""",
    "fslval": "echo 2",
    "fslhd": "printf \"<nifti_image\\n  datatype = '16'\\n/>\\n\"",
    "fslcreatehd": "true",
    "tmpnam": 'mktemp "$TMPDIR/tmpnam.XXXXXX"',
}


def write_stub(folder, name, body, calls):
    folder.mkdir(parents=True, exist_ok=True)
    stub = folder / name
    stub.write_text(f'#!{BASH}\necho "{name} $*" >> "{calls}"\n{body}\n')
    stub.chmod(0o755)


@pytest.fixture
def fsl(tmp_path):
    """FSLDIR with the stub tools, and the file their calls are recorded in."""
    calls = tmp_path / "fsl_calls.txt"
    for name, body in STUBS.items():
        write_stub(tmp_path / "fsl" / "bin", name, body, calls)
    return tmp_path / "fsl", calls


@pytest.fixture
def library(tmp_path):
    """
    An autoPtx library of three structures, read only, as in a container. The
    two-waypoint protocol carries the target.txt the real one does, with the
    library named by a variable nothing expands.
    """
    etc = tmp_path / "library" / "etc"
    folder = etc / "auto_ptx"
    for struct, (files, _) in PROTOCOLS.items():
        protocol = folder / "protocols" / struct
        protocol.mkdir(parents=True)
        for name in files:
            target = protocol / (name if name in ("invert", "randfib1") else f"{name}.nii.gz")
            target.write_text("mask\n")
        if "target1" in files:
            (protocol / "target.txt").write_text(
                f"$QUNEXLIBRARYETC/auto_ptx/protocols/{struct}/target1.nii.gz\n"
            )
    (folder / "luts").mkdir()
    (folder / "structure_list").write_text(
        "\n".join(line for _, line in PROTOCOLS.values()) + "\n"
    )
    before = snapshot(folder)
    for path in [folder, *folder.rglob("*")]:
        path.chmod(path.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    yield etc, before
    for path in [folder, *folder.rglob("*")]:
        path.chmod(path.stat().st_mode | stat.S_IWUSR)


def snapshot(folder):
    return {p: p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def make_session(sessions, session="S1"):
    """A session's hcp folder as hcp_diffusion, bedpostX and the HCP pipelines leave it."""
    hcp = sessions / session / "hcp"
    bedpostx = hcp / session / "T1w" / "Diffusion.bedpostX"
    xfms = hcp / session / "MNINonLinear" / "xfms"
    for folder in (bedpostx, xfms):
        folder.mkdir(parents=True)
    for image in [
        bedpostx / "merged_th1samples.nii.gz",
        bedpostx / "merged_ph1samples.nii.gz",
        bedpostx / "merged_f1samples.nii.gz",
        bedpostx / "nodif_brain_mask.nii.gz",
        xfms / "standard2acpc_dc.nii.gz",
        xfms / "acpc_dc2standard.nii.gz",
    ]:
        image.write_text("img\n")
    return hcp


@pytest.fixture
def study(tmp_path):
    study = tmp_path / "study"
    study.mkdir()
    (study / ".qunexstudy").write_text("")
    make_session(study / "sessions")
    return study


def environment_auto_ptx_folder():
    """AutoPtxFolder as env/qunex_environment.sh sets it, in this repository."""
    text = (REPO / "env" / "qunex_environment.sh").read_text()
    full = re.search(r"^export HCPPIPEDIR_dMRITractFull=(\S+?);", text, re.M).group(1)
    folder = re.search(r"^export AutoPtxFolder=(\S+?);", text, re.M).group(1)
    full = full.replace("${QUNEXPATH}", str(REPO))
    return folder.replace("${HCPPIPEDIR_dMRITractFull}", full)


def base_env(tmp_path, fsl_dir, etc=None):
    env = {
        "PATH": f"{fsl_dir / 'bin'}:{SYSTEM_PATH}",
        "FSLDIR": str(fsl_dir),
        "HOME": str(tmp_path),
        "TMPDIR": str(tmp_path),
        "LC_ALL": "C",
    }
    if etc is not None:
        env["QUNEXLIBRARYETC"] = str(etc)
    return env


def run_qunex_sh(tmp_path, fsl_dir, etc, args, auto_ptx_folder, **extra):
    """
    Run bin/qunex.sh as tests/test_bash_scripts.py does: it finds itself
    through TOOLS and QUNEXREPO and needs gmri on the PATH, after the stubs.
    """
    env = base_env(tmp_path, fsl_dir, etc)
    env["PATH"] = os.pathsep.join(
        [str(fsl_dir / "bin"), str(REPO / "python" / "qx_utilities"), os.environ["PATH"]]
    )
    env.update(TOOLS=str(REPO.parent), QUNEXREPO=REPO.name, QUNEXPATH=str(REPO))
    if auto_ptx_folder is not None:
        env["AutoPtxFolder"] = auto_ptx_folder
    env.update(extra)
    return subprocess.run(
        [BASH, str(REPO / "bin" / "qunex.sh"), "auto_ptx", *args],
        cwd=tmp_path,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=300,
    )


def results(hcp, session="S1"):
    return hcp / session / "MNINonLinear" / "Results" / "autoPtx"


def test_the_environment_names_the_auto_ptx_scripts():
    """It named autoptx_hcp_extended, a folder renamed in 2021."""
    folder = Path(environment_auto_ptx_folder())
    assert folder == SCRIPTS
    assert os.access(folder / "auto_ptx", os.X_OK)


@pytest.mark.parametrize("from_environment", [True, False], ids=["env", "unset"])
def test_auto_ptx_runs_end_to_end(tmp_path, fsl, library, study, from_environment):
    """
    qunex auto_ptx tracks every structure of a session from its bedpostX
    folder, prepares the tracts for display, and completes. It also finds the
    scripts without AutoPtxFolder, which it refused to run without.
    """
    fsl_dir, calls = fsl
    etc, before = library
    folder = environment_auto_ptx_folder() if from_environment else None

    result = run_qunex_sh(
        tmp_path, fsl_dir, etc, ["--studyfolder=study", "--sessions=S1"], folder
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    [log] = study.glob("logs/*_auto_ptx")
    assert list(log.glob("comlogs/done_*_auto_ptx_S1.log")), output
    hcp = study / "sessions" / "S1" / "hcp"
    out = results(hcp)
    bedpostx = hcp / "S1" / "T1w" / "Diffusion.bedpostX"
    recorded = calls.read_text()
    for struct in PROTOCOLS:
        assert (out / struct / "tracts" / "tractsNorm.nii.gz").is_file(), output
        assert (out / f"{struct}_bin.nii.gz").is_file(), output
        assert (out / f"{struct}_thr.nii.gz").is_file(), output
    # the cpu probtrackx2, on the session's own bedpostX and warps
    assert f"probtrackx2 -s {bedpostx}/merged -m {bedpostx}/nodif_brain_mask" in recorded
    assert f"--xfm={hcp}/S1/MNINonLinear/xfms/standard2acpc_dc.nii.gz" in recorded
    # tracked both ways
    assert (out / "fma" / "tractsInv" / "fwDensity.nii.gz").is_file()
    # two waypoints, listed with the tracts
    waypoints = out / "slf1_l" / "target.txt"
    assert waypoints.read_text().split() == [
        str(out / "slf1_l" / "target1.nii.gz"),
        str(out / "slf1_l" / "target2.nii.gz"),
    ]
    assert f"--waypoints={waypoints}" in recorded
    for viewer in ("viewAll_3D_0.005", "viewAll_0.005"):
        assert (out / viewer).is_file(), output
    # nothing written into the library
    assert snapshot(etc / "auto_ptx") == before


def test_a_failed_structure_fails_the_run(tmp_path, fsl, library, study):
    """The run fails and names the structure; the others are still tracked."""
    fsl_dir, _ = fsl
    etc, _ = library

    result = run_qunex_sh(
        tmp_path,
        fsl_dir,
        etc,
        ["--studyfolder=study", "--sessions=S1"],
        environment_auto_ptx_folder(),
        FAIL_STRUCT="fma",
    )

    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    [comlog] = study.glob("logs/*_auto_ptx/comlogs/error_*_auto_ptx_S1.log")
    assert "ERROR: auto_ptx: tractography failed for: fma" in comlog.read_text()
    out = results(study / "sessions" / "S1" / "hcp")
    assert (out / "atr_l" / "tracts" / "tractsNorm.nii.gz").is_file()
    assert (out / "slf1_l" / "tracts" / "tractsNorm.nii.gz").is_file()
    assert not (out / "viewAll_0.005").exists()


def test_auto_ptx_runs_when_started_by_a_relative_path(tmp_path, fsl, library, study):
    """It changed into the bedpostX folder and looked for ./track_subject_struct there."""
    fsl_dir, _ = fsl
    etc, _ = library
    hcp = study / "sessions" / "S1" / "hcp"

    result = subprocess.run(
        [BASH, "./auto_ptx", str(hcp), "S1", "Diffusion.bedpostX"],
        cwd=SCRIPTS,
        env=base_env(tmp_path, fsl_dir, etc),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    for struct in PROTOCOLS:
        assert (results(hcp) / struct / "tracts" / "tractsNorm.nii.gz").is_file()


def test_auto_ptx_stops_without_a_bedpostx_run(tmp_path, fsl, library, study):
    """The scripts report what is missing rather than tracking nothing."""
    fsl_dir, calls = fsl
    etc, _ = library
    hcp = study / "sessions" / "S1" / "hcp"
    (hcp / "S1" / "T1w" / "Diffusion.bedpostX" / "merged_th1samples.nii.gz").unlink()

    result = subprocess.run(
        [BASH, str(SCRIPTS / "auto_ptx"), str(hcp), "S1", "Diffusion.bedpostX"],
        cwd=tmp_path,
        env=base_env(tmp_path, fsl_dir, etc),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode != 0
    assert "ERROR: auto_ptx:" in result.stdout
    assert "merged_th1samples.nii.gz not found" in result.stdout
    assert not calls.exists()


@pytest.mark.skipif(
    not (LIBRARY / "structure_list").is_file(), reason="needs the qx_library submodule"
)
def test_auto_ptx_finds_the_library_it_is_in(tmp_path, fsl, study):
    """
    Without QUNEXLIBRARYETC the scripts read the qx_library of their own
    repository, where commit 81e3b738 moved the data, and every structure of
    its list has a protocol there; nothing is written into it.
    """
    fsl_dir, _ = fsl
    hcp = study / "sessions" / "S1" / "hcp"
    before = snapshot(LIBRARY)

    result = subprocess.run(
        [BASH, str(SCRIPTS / "auto_ptx"), str(hcp), "S1", "Diffusion.bedpostX"],
        cwd=tmp_path,
        env=base_env(tmp_path, fsl_dir),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    structures = [
        line.split()[0]
        for line in (LIBRARY / "structure_list").read_text().splitlines()
        if line.strip()
    ]
    assert len(structures) == 33
    for struct in structures:
        assert (results(hcp) / struct / "tracts" / "tractsNorm.nii.gz").is_file(), struct
    assert snapshot(LIBRARY) == before


def test_average_leaves_out_an_incomplete_session(tmp_path, fsl, library):
    """
    A session without all its tracts, after a complete one, had the tracts it
    had added to the sum without being counted, so they were averaged over too
    few sessions. The average is prepared for display as a session's tracts are.
    """
    fsl_dir, calls = fsl
    etc, _ = library
    hcp = tmp_path / "hcp"
    for session, tracts in [("A", ALL_TRACTS), ("B", ALL_TRACTS[1:]), ("C", ALL_TRACTS)]:
        for struct in tracts:
            folder = results(hcp, session) / struct / "tracts"
            folder.mkdir(parents=True)
            (folder / "tractsNorm.nii.gz").write_text("img\n")
    average = tmp_path / "average"
    env = base_env(tmp_path, fsl_dir, etc)

    result = subprocess.run(
        [BASH, str(SCRIPTS / "average_auto_ptx.sh"), str(hcp), "A B C", str(average)],
        cwd=tmp_path,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "AutoPtx results from 2 sessions averaged" in result.stdout
    recorded = calls.read_text()
    assert f"{hcp}/B/" not in recorded
    assert f"fslmaths {average}/fma -div 2 {average}/fma" in recorded

    shown = subprocess.run(
        [BASH, str(SCRIPTS / "prepare_for_display.sh"), str(average), "0.005", "1"],
        cwd=tmp_path,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert shown.returncode == 0, shown.stdout + shown.stderr
    for struct in PROTOCOLS:
        assert (average / f"{struct}_bin.nii.gz").is_file()
    assert f"{etc}/auto_ptx/luts/c1.lut" in (average / "viewAll_3D_0.005").read_text()
