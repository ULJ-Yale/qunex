#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``bin/qunex.sh``, the shell front end, run with stub tools.

Split from ``test_bash_scripts.py``, whose helpers it uses: ``auto_ptx``, the
one command the front end still runs itself, works in the study, on each
session's own bedpostX folder, and logs where ``gmri log_folder`` says a run
through gmri would, the output of a scheduled job included; a deprecated name
of a gmri command runs it, and a dry run sets no threads. The front end finds
itself through ``TOOLS`` and ``QUNEXREPO``, so these tests set them, and
``QUNEXPATH``, to this repository, and put ``gmri`` on the PATH.
"""

import os
import subprocess
import sys

import pytest

from tests.test_bash_scripts import BASH, REPO, write_stub

pytestmark = pytest.mark.skipif(
    BASH is None or sys.platform == "win32", reason="needs bash"
)


# bin/qunex.sh, auto_ptx


@pytest.fixture
def auto_ptx_study(tmp_path):
    """
    A study with one session, and stand-ins for the autoPtx scripts that
    record the folder they run in and what they are given, and say they are
    done, as the comlog check wants. Neither logs/ nor processing/ is made.
    """
    study = tmp_path / "study"
    (study / "sessions" / "S1").mkdir(parents=True)
    (study / ".qunexstudy").write_text("")
    calls = tmp_path / "calls.txt"
    for name in ["auto_ptx", "prepare_for_display.sh"]:
        write_stub(
            tmp_path / "autoptx",
            name,
            f'echo "$(pwd) $*" >> "{calls}"\necho "Successful completion"',
        )
    return study, calls


def bedpostx_folder(study, session="S1"):
    return study / "sessions" / session / "hcp" / session / "T1w" / "Diffusion.bedpostX"


def run_qunex_sh(tmp_path, args, cwd=None):
    """
    Run bin/qunex.sh with bash in `cwd`, by default tmp_path, which is also the
    home folder. It finds itself through TOOLS and QUNEXREPO, and gmri on PATH,
    so those are set to this repository; the stubs in tmp_path/stubs come
    first.
    """
    return subprocess.run(
        [BASH, str(REPO / "bin" / "qunex.sh"), *args],
        cwd=cwd or tmp_path,
        env={
            "PATH": os.pathsep.join(
                [
                    str(tmp_path / "stubs"),
                    str(REPO / "python" / "qx_utilities"),
                    os.environ["PATH"],
                ]
            ),
            "HOME": str(tmp_path),
            "TOOLS": str(REPO.parent),
            "QUNEXREPO": REPO.name,
            "QUNEXPATH": str(REPO),
            "AutoPtxFolder": str(tmp_path / "autoptx"),
        },
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_a_deprecated_name_of_a_gmri_command_runs_it(tmp_path):
    """
    The front end mapped a deprecated name only after it had looked for the
    gmri commands, and then refused the mapped one as no command it runs
    itself: `qunex createStudy` said it was not supported.
    """
    result = run_qunex_sh(tmp_path, ["createStudy", "--studyfolder=new"])

    assert "is now known as create_study" in result.stdout, result.stdout
    assert "not supported" not in result.stdout, result.stdout
    assert (tmp_path / "new" / ".qunexstudy").is_file(), result.stdout
    assert list((tmp_path / "new" / "logs").glob("*_create_study"))


@pytest.mark.parametrize("bedpostx", [True, False])
def test_auto_ptx_runs_each_session_in_the_study(auto_ptx_study, tmp_path, bedpostx):
    """
    auto_ptx is the one command bin/qunex.sh still runs itself. Its folders are
    taken as every command takes them, it works in the study, and it is run on
    each session's own bedpostX folder, which it looked for before the session
    was known, and refused when it was there. The scripts are given the
    session's hcp folder, the session and the bedpostX folder's name under T1w,
    as they take them; it gave them the sessions folder and the whole path. It
    logged only into a logs/ and processing/scripts/tmp the study already had.
    """
    study, calls = auto_ptx_study
    folder = bedpostx_folder(study)
    if bedpostx:
        folder.mkdir(parents=True)

    result = run_qunex_sh(
        tmp_path, ["auto_ptx", "--studyfolder=study", "--sessions=S1"]
    )

    if bedpostx:
        first = calls.read_text().splitlines()[0]
        assert first == f"{study} {study / 'sessions' / 'S1' / 'hcp'} S1 {folder.name}", result.stdout
        assert list(study.glob("logs/*_auto_ptx/batchlogs/Run_*.sh")), result.stdout
    else:
        assert "Prior BedpostX run not found" in result.stdout
        assert not calls.exists()


def test_auto_ptx_goes_on_past_a_session_without_bedpostx(auto_ptx_study, tmp_path):
    """
    A session without a bedpostX run ended the whole run, so none of the
    sessions after it was tracked. It is reported, the others are run, and the
    run still fails.
    """
    study, calls = auto_ptx_study
    (study / "sessions" / "S2").mkdir()
    folder = bedpostx_folder(study, "S2")
    folder.mkdir(parents=True)

    result = run_qunex_sh(
        tmp_path, ["auto_ptx", "--studyfolder=study", "--sessions=S1,S2"]
    )

    assert "Prior BedpostX run not found or incomplete for S1" in result.stdout
    assert calls.exists(), result.stdout + result.stderr
    first = calls.read_text().splitlines()[0]
    assert first == f"{study} {study / 'sessions' / 'S2' / 'hcp'} S2 {folder.name}"
    assert list(study.glob("logs/*_auto_ptx/comlogs/done_*_auto_ptx_S2.log"))
    assert result.returncode != 0, result.stdout


@pytest.mark.parametrize(
    "start, folders",
    [
        ("elsewhere", ["--studyfolder=~/study"]),
        (".", ["--sessionsfolder=study/sessions"]),
        (".", ["--studyfolder=study", "--sessionsfolder=sessions"]),
    ],
    ids=["home", "sessionsfolder-alone", "sessionsfolder-in-the-study"],
)
def test_auto_ptx_takes_its_folders_as_every_command_does(
    auto_ptx_study, tmp_path, start, folders
):
    """
    A ~ was kept as it was typed, as the shell does not expand it in a
    --key=value argument, and a relative sessions folder was taken from the
    current folder also when a study was named with it.
    """
    study, calls = auto_ptx_study
    folder = bedpostx_folder(study)
    folder.mkdir(parents=True)
    (tmp_path / "elsewhere").mkdir()

    result = run_qunex_sh(
        tmp_path, ["auto_ptx", *folders, "--sessions=S1"], cwd=tmp_path / start
    )

    assert calls.exists(), result.stdout + result.stderr
    first = calls.read_text().splitlines()[0]
    assert first == f"{study} {study / 'sessions' / 'S1' / 'hcp'} S1 {folder.name}", result.stdout
    assert list(study.glob("logs/*_auto_ptx/comlogs/done_*_auto_ptx_S1.log"))


@pytest.mark.parametrize(
    "logfolder, where",
    [(None, "logs/*_auto_ptx"), ("mylogs", "mylogs"), ("legacy", "processing/logs")],
    ids=["default", "relative", "legacy"],
)
def test_auto_ptx_logs_where_a_run_through_gmri_would(
    auto_ptx_study, tmp_path, logfolder, where
):
    """
    It decided its log folder itself: a relative --logfolder was taken from the
    folder it was started in, `legacy` was a folder of that name, and the run
    scripts went to processing/scripts/tmp. It did not say where it logged.
    """
    study, calls = auto_ptx_study
    bedpostx_folder(study).mkdir(parents=True)
    given = [f"--logfolder={logfolder}"] if logfolder else []
    before = set(tmp_path.iterdir())

    result = run_qunex_sh(
        tmp_path, ["auto_ptx", "--studyfolder=study", "--sessions=S1", *given]
    )

    assert result.returncode == 0, result.stdout + result.stderr
    [folder] = study.glob(where)
    # said, as every run says where it logs
    assert f"---> Logs: {folder}\n" in result.stdout, result.stdout
    [runlog] = folder.glob("Log-*_auto_ptx_S1.log")
    tag = runlog.name[len("Log-") : -len(".log")]
    assert (folder / "comlogs" / f"done_{tag}.log").is_file(), result.stdout
    assert (folder / "batchlogs" / f"Run_{tag}.sh").is_file(), result.stdout
    assert not (study / "processing" / "scripts").exists()
    # nothing in the folder it was started in, nor in the home folder
    assert set(tmp_path.iterdir()) - before == {calls}


@pytest.mark.parametrize("unset", [False, True], ids=["header", "unset"])
def test_auto_ptx_logs_where_the_batch_file_header_says(
    auto_ptx_study, tmp_path, unset
):
    """
    It asked gmri for its log folder without the batch file, so a log folder the
    header names did not place it, while a gmri run given the same batch file
    logged there. The batch file is taken from the study, as gmri takes it;
    it was read from the current folder.
    """
    study, calls = auto_ptx_study
    bedpostx_folder(study).mkdir(parents=True)
    batch = study / "processing" / "batch.txt"
    batch.parent.mkdir()
    header = tmp_path / "hdrlogs"
    batch.write_text(f"_logfolder: {header}\n---\nsession: S1\nid: S1\n")
    given = ["--unset_batch_header_parameters=logfolder"] if unset else []

    result = run_qunex_sh(
        tmp_path,
        [
            "auto_ptx",
            "--studyfolder=study",
            "--batchfile=processing/batch.txt",
            "--sessions=S1",
            *given,
        ],
    )

    assert result.returncode == 0, result.stdout + result.stderr
    where = study / "logs" if unset else header
    [folder] = where.glob("*auto_ptx*") if unset else [header]
    assert list(folder.glob("comlogs/done_*_auto_ptx_S1.log")), result.stdout
    assert header.exists() is not unset


def test_auto_ptx_takes_its_log_folder_from_the_last_line_gmri_prints(
    auto_ptx_study, tmp_path
):
    """
    gmri log_folder warns on stdout about a sessions folder that mentions a
    subject, and only then prints the folder.
    """
    study, calls = auto_ptx_study
    bedpostx_folder(study).mkdir(parents=True)
    study = study.rename(tmp_path / "subject_study")

    result = run_qunex_sh(
        tmp_path, ["auto_ptx", "--studyfolder=subject_study", "--sessions=S1"]
    )

    assert result.returncode == 0, result.stdout + result.stderr
    [folder] = (study / "logs").iterdir()
    assert list(folder.glob("comlogs/done_*_auto_ptx_S1.log")), result.stdout


def test_auto_ptx_stops_when_gmri_can_not_place_its_logs(auto_ptx_study, tmp_path):
    """An invalid logging setting stops the run before it logs or runs anything."""
    study, calls = auto_ptx_study
    bedpostx_folder(study).mkdir(parents=True)
    (tmp_path / ".qunex_settings.yaml").write_text("logging:\n  layout: bogus\n")
    before = set(tmp_path.rglob("*"))

    result = run_qunex_sh(
        tmp_path, ["auto_ptx", "--studyfolder=study", "--sessions=S1"]
    )

    assert "logging.layout must be one of" in result.stdout, result.stdout
    assert "ERROR: Could not decide where the logs of auto_ptx go." in result.stdout
    # nothing logged, run or written, in the study or anywhere else
    assert set(tmp_path.rglob("*")) == before, result.stdout


def test_a_scheduled_auto_ptx_keeps_the_job_output_in_its_log_folder(
    auto_ptx_study, tmp_path
):
    """
    The job was submitted from the log folder, which left its output there under
    the scheduler's own name, and gmri's log of the submission in a second
    folder.
    """
    study, calls = auto_ptx_study
    bedpostx_folder(study).mkdir(parents=True)
    job, where = tmp_path / "job.sh", tmp_path / "submitted_from"
    submitted = f'pwd > "{where}"\ncat > "{job}"\necho "Submitted batch job 42"'
    write_stub(tmp_path / "stubs", "sbatch", submitted)
    args = ["--studyfolder=study", "--sessions=S1", "--scheduler=SLURM,time=10"]

    result = run_qunex_sh(tmp_path, ["auto_ptx", *args])

    assert "Data successfully submitted" in result.stdout, result.stdout + result.stderr
    # from the study, where a SLURM job then starts, as a local run works there
    assert where.read_text().strip() == str(study)
    [folder] = (study / "logs").iterdir()
    tag = f"{folder.name}_S1"
    script = job.read_text()
    output = folder / "batchlogs" / f"SLURM_{tag}.log"
    assert f"#SBATCH -o {output}\n" in script, script
    assert f"#SBATCH -e {output}\n" in script, script
    assert f". {folder / 'batchlogs' / f'Run_{tag}.sh'} 2>&1" in script, script
    assert list(folder.glob("Log-schedule-*.log")), sorted(folder.iterdir())
    # submitted, not run
    assert not calls.exists()


@pytest.mark.parametrize(
    "args, threads",
    [
        (["--test"], "unset"),
        (["--run=test"], "unset"),
        (["--run=run"], "8"),
        ([], "8"),
    ],
)
def test_qunex_sets_no_threads_for_a_dry_run(tmp_path, args, threads):
    """
    bin/qunex.sh exported OMP_NUM_THREADS before it handed a dry run to gmri,
    which itself sets nothing for one: `qunex <command> --test` and
    `gmri <command> --test` reached the command with different environments.
    """
    gmri = (
        'if [ "$1" = "-available" ]; then echo hcp_icafix; exit 0; fi\n'
        'echo "OMP=${OMP_NUM_THREADS-unset}"'
    )
    write_stub(tmp_path / "stubs", "gmri", gmri)
    write_stub(tmp_path / "stubs", "nproc", "echo 64")

    result = run_qunex_sh(tmp_path, ["hcp_icafix", "--sessions=S1", *args])

    assert "OMP=%s\n" % threads in result.stdout, result.stdout + result.stderr
