# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for `gmri log_folder`, which prints the folder a run would log in,
decided by the rule tests/test_log_placement.py pins.
"""

import re

import pytest

import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl
import qx_utilities.general.log.settings as ls
import qx_utilities.general.placement as gpl
from tests import utils
from tests.test_log_placement import REPO_ROOT, TS, study


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """A home and a current folder of their own, and no user settings file."""
    home = tmp_path / "home"
    home.mkdir()
    (tmp_path / "cwd").mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(tmp_path / "cwd")
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(home / ".qunex_settings.yaml")])
    yield
    gl.set_active(None)


def test_gmri_log_folder_prints_the_folder_a_run_would_log_in(
    tmp_path, monkeypatch, capsys
):
    """
    `bin/qunex.sh` runs one command itself, and asks `gmri log_folder` where
    it logs: the answer is the one a run started there gets from `gmri`.
    """
    s = study(tmp_path / "s")

    def printed(**args):
        gpl.print_log_folder({"command": "auto_ptx", **args})
        return capsys.readouterr().out.splitlines()[-1]

    assert printed(timestamp=TS, studyfolder=str(s)) == str(
        s / "logs" / (TS + "_auto_ptx")
    )
    assert printed(timestamp=TS, studyfolder=str(s), logfolder="legacy") == str(
        s / "processing" / "logs"
    )
    assert re.fullmatch(
        re.escape(str(s / "logs"))
        + r"/\d{4}-\d\d-\d\d_\d\d\.\d\d\.\d\d\.\d{6}_auto_ptx",
        printed(studyfolder=str(s)),
    ), "stamped now when no stamp is given"

    # a relative batch file is taken from the study the command line names,
    # and its header is taken as gmri takes it, less what the call unsets
    (s / "processing" / "logs_batch.txt").write_text(
        "_logfolder: hdrlogs\n---\nsession: S1\n"
    )
    monkeypatch.chdir(tmp_path)
    named = {
        "timestamp": TS,
        "studyfolder": "s",
        "batchfile": "processing/logs_batch.txt",
    }

    assert printed(**named) == str(s / "hdrlogs")
    assert printed(**named, unset_batch_header_parameters="logfolder") == str(
        s / "logs" / (TS + "_auto_ptx")
    )

    with pytest.raises(ge.CommandError):
        gpl.print_log_folder({"timestamp": TS, "studyfolder": str(s)})


def test_gmri_log_folder_is_answered_from_the_command_line(
    tmp_path, monkeypatch, capsys
):
    """As `bin/qunex.sh` calls it: the folder is the last line printed."""
    monkeypatch.setenv("QUNEXPATH", str(REPO_ROOT))
    s = study(tmp_path / "s")
    gmri = utils.load_gmri("gmri_log_placement")

    with pytest.raises(SystemExit) as exited:
        gmri.main(
            [
                "log_folder",
                "--command=auto_ptx",
                "--timestamp=%s" % TS,
                "--studyfolder=%s" % s,
            ]
        )
    assert exited.value.code == 0
    assert capsys.readouterr().out.splitlines()[-1] == str(
        s / "logs" / (TS + "_auto_ptx")
    )

    with pytest.raises(SystemExit) as exited:
        gmri.main(["log_folder", "--studyfolder=%s" % s])
    assert exited.value.code == 1, "without --command"


def test_gmri_log_folder_help_is_its_usage(monkeypatch, capsys):
    """
    `gmri log_folder --help` is not a registered command's help: it prints
    the usage of what answers it, rather than that it is not supported.
    """
    monkeypatch.setenv("QUNEXPATH", str(REPO_ROOT))
    gmri = utils.load_gmri("gmri_log_placement")

    gmri.main(["log_folder", "--help"])
    out = capsys.readouterr().out
    assert "gmri log_folder --command=<command>" in out
    assert "not supported" not in out
