"""
Where `xnat_upload_download.sh` puts the XNAT project information a download
fetches: in the run's log folder, decided by the rule every QuNex run is placed
by (`gmri log_folder`), and nowhere else -- not `<study>/processing/logs/xnatlogs`
and not the download folder. curl and zip are stubbed, so nothing reaches a
server.
"""

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import os
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "bash" / "qx_utilities" / "xnat_upload_download.sh"
COMMAND = "xnat_upload_download"

# answers the stubbed XNAT site gives: a session id, the project's subjects and
# experiments, and the archive of the one session
CURL = """#!/bin/bash
for arg in "$@"; do url="$arg"; done
case "$url" in
    */data/JSESSION) echo "JSESSIONSTUB" ;;
    */data/sessions\\?*) printf 'ID,project,label\\nXS001,PRJ,SUBJ1\\n' ;;
    */data/experiments\\?*) printf 'ID,project,label\\nXE001,PRJ,SUBJ1_MR1\\n' ;;
    *format=zip) cat "%s" ;;
esac
exit 0
"""

ZIP = """#!/bin/bash
echo "test of $2 OK"
"""

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash is not available"
)


def _executable(path, text):
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


@pytest.fixture
def site(tmp_path):
    """A stubbed XNAT site, a home with a credential file, and a study."""
    archive = tmp_path / "archive.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("scan/1.dcm", "dicom")

    stubs = tmp_path / "stubs"
    stubs.mkdir()
    _executable(stubs / "curl", CURL % archive)
    _executable(stubs / "zip", ZIP)

    home = tmp_path / "home"
    home.mkdir()
    credentials = home / ".xnat"
    credentials.write_text("user:secret\n")
    credentials.chmod(0o400)

    study = tmp_path / "study"
    (study / "sessions").mkdir(parents=True)
    (study / ".qunexstudy").write_text("")

    work = tmp_path / "work"
    work.mkdir()

    env = dict(os.environ)
    env["HOME"] = str(home)
    env["PATH"] = "%s%s%s" % (stubs, os.pathsep, env.get("PATH", ""))
    return {"tmp": tmp_path, "home": home, "study": study, "work": work, "env": env}


def _run(site, *args, script=SCRIPT):
    command = [
        shutil.which("bash"),
        str(script),
        "--runtype=download",
        "--sessions=SUBJ1",
        "--xnathost=https://xnat.invalid",
        "--xnatprojectid=PRJ",
        "--xnatsessionlabel=MR1",
        *args,
    ]
    return subprocess.run(
        command,
        cwd=site["work"],
        env=site["env"],
        capture_output=True,
        text=True,
        timeout=120,
    )


def _download(site, *args):
    result = _run(site, *args)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    return output


def _record_curl(site):
    """Makes the curl stub note every call; returns the file it notes them in."""
    calls = site["tmp"] / "curl_calls"
    curl = site["tmp"] / "stubs" / "curl"
    curl.write_text(
        curl.read_text().replace(
            "#!/bin/bash\n", '#!/bin/bash\necho "$@" >> "%s"\n' % calls, 1
        )
    )
    return calls


def _system_path(site, *first):
    """A PATH of the stubs, `first`, and the system folders: no QuNex on it."""
    return os.pathsep.join(
        [str(site["tmp"] / "stubs"), *[str(f) for f in first], "/usr/bin", "/bin"]
    )


def _info(folder):
    """The XNAT project information files of one run under `folder`."""
    return sorted(glob.glob(os.path.join(folder, "XNATInfo_*", "PRJ_*.csv")))


def _everywhere(root):
    return sorted(glob.glob(os.path.join(root, "**", "PRJ_*.csv"), recursive=True))


def test_download_in_a_study_keeps_the_xnat_info_in_the_run_log_folder(site):
    study = site["study"]
    output = _download(site, "--studyfolder=%s" % study)

    runs = glob.glob(os.path.join(study, "logs", "*_%s" % COMMAND))
    assert len(runs) == 1, output
    info = _info(runs[0])
    assert [os.path.basename(f).split("_")[1] for f in info] == [
        "experiments",
        "subjects",
    ]
    # the run's folder, and no other
    assert _everywhere(site["tmp"]) == info
    assert not (study / "processing" / "logs").exists()
    assert (study / "sessions" / "inbox" / "SUBJ1.zip").is_file()
    assert "Log folder: %s" % runs[0] in output


def test_download_by_sessions_folder_logs_in_its_study(site):
    study = site["study"]
    _download(site, "--sessionsfolder=%s" % (study / "sessions"))

    runs = glob.glob(os.path.join(study, "logs", "*_%s" % COMMAND))
    assert len(runs) == 1
    assert _everywhere(site["tmp"]) == _info(runs[0])


def test_download_without_a_study_logs_where_a_run_outside_a_study_does(site):
    download = site["tmp"] / "download"
    _download(site, "--downloadpath=%s" % download)

    runs = glob.glob(os.path.join(site["home"], "qunex_logs", "*_%s" % COMMAND))
    assert len(runs) == 1
    assert _everywhere(site["tmp"]) == _info(runs[0])
    assert (download / "SUBJ1.zip").is_file()
    assert not glob.glob(os.path.join(download, "XNATInfo_*"))


def test_download_uses_the_log_folder_it_is_given(site):
    logs = site["tmp"] / "given_logs"
    _download(site, "--studyfolder=%s" % site["study"], "--logfolder=%s" % logs)

    assert _everywhere(site["tmp"]) == _info(logs)
    assert not (site["study"] / "logs").exists()


def test_a_relative_log_folder_is_taken_from_the_study(site):
    study = site["study"]
    _download(site, "--studyfolder=%s" % study, "--logfolder=xnat_runs")

    assert _everywhere(site["tmp"]) == _info(study / "xnat_runs")


def test_legacy_log_folder_is_the_study_processing_logs(site):
    study = site["study"]
    _download(site, "--studyfolder=%s" % study, "--logfolder=legacy")

    legacy = study / "processing" / "logs"
    assert _everywhere(site["tmp"]) == _info(legacy)
    assert not (legacy / "xnatlogs").exists()


def test_a_log_folder_that_can_not_be_decided_stops_the_download(site):
    (site["home"] / ".qunex_settings.yaml").write_text("logging:\n  layout: bogus\n")
    calls = _record_curl(site)

    result = _run(site, "--studyfolder=%s" % site["study"])

    assert result.returncode == 1
    assert "Could not decide where the logs" in result.stdout
    assert "Check your inputs" in result.stdout
    assert not calls.exists()
    assert not _everywhere(site["tmp"])


def test_without_gmri_the_download_stops_before_fetching(site):
    # a copy of the script outside a QuNex installation, with no gmri on PATH
    script = site["tmp"] / "xnat_upload_download.sh"
    shutil.copy(SCRIPT, script)
    site["env"]["PATH"] = _system_path(site)
    calls = _record_curl(site)

    result = _run(site, "--studyfolder=%s" % site["study"], script=script)

    assert result.returncode == 1
    assert "gmri not found" in result.stdout
    assert not calls.exists()
    assert not _everywhere(site["tmp"])


@pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0,
    reason="root writes in a read-only folder",
)
def test_a_log_folder_that_can_not_be_created_stops_the_download(site):
    locked = site["tmp"] / "locked"
    locked.mkdir()
    locked.chmod(0o555)
    calls = _record_curl(site)
    try:
        result = _run(
            site,
            "--studyfolder=%s" % site["study"],
            "--logfolder=%s" % (locked / "logs"),
        )
    finally:
        locked.chmod(0o755)

    assert result.returncode == 1
    assert "Could not create the log folder" in result.stdout
    assert not calls.exists()
    assert not _everywhere(site["tmp"])


def test_a_download_runs_where_there_is_python3_but_no_python(site):
    # gmri starts as `python`; a machine with only python3 still downloads
    if any(
        os.path.exists(os.path.join(folder, "python")) for folder in ("/usr/bin", "/bin")
    ):
        pytest.skip("the system has a python, so python3 alone can not be tested")
    python3 = site["tmp"] / "python3_only"
    python3.mkdir()
    (python3 / "python3").symlink_to(sys.executable)
    site["env"]["PATH"] = _system_path(site, python3)

    _download(site, "--studyfolder=%s" % site["study"])

    runs = glob.glob(os.path.join(site["study"], "logs", "*_%s" % COMMAND))
    assert len(runs) == 1
    assert _everywhere(site["tmp"]) == _info(runs[0])


def test_without_python_the_download_says_so_and_stops(site):
    # the system tools without any python
    tools = site["tmp"] / "no_python"
    tools.mkdir()
    for folder in ("/usr/bin", "/bin"):
        for name in os.listdir(folder):
            target = tools / name
            if name.startswith("python") or os.path.lexists(target):
                continue
            target.symlink_to(os.path.join(folder, name))
    site["env"]["PATH"] = os.pathsep.join([str(site["tmp"] / "stubs"), str(tools)])
    calls = _record_curl(site)

    result = _run(site, "--studyfolder=%s" % site["study"])

    assert result.returncode == 1
    assert "python not found" in result.stdout
    assert "Check your inputs" not in result.stdout
    assert not calls.exists()


def test_a_python_that_can_not_be_run_is_not_blamed_on_the_inputs(site):
    # a `python` that the system can not run: gmri exits 127
    broken = site["tmp"] / "broken_python"
    broken.mkdir()
    _executable(broken / "python", "#!/bin/bash\nexit 127\n")
    site["env"]["PATH"] = _system_path(site, broken)
    calls = _record_curl(site)

    result = _run(site, "--studyfolder=%s" % site["study"])

    assert result.returncode == 1
    assert "could not be run" in result.stdout
    assert "Check your inputs" not in result.stdout
    assert not calls.exists()


def test_usage_names_the_run_log_folder():
    usage = subprocess.run(
        [shutil.which("bash"), str(SCRIPT), "--help"], capture_output=True, text=True, timeout=60
    ).stdout
    assert "--logfolder" in usage
    assert "xnatlogs" not in usage
