# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Where ``hcp_run_qc`` keeps the comlogs of its calls: with the run's other logs.

They went to a ``qclog`` folder beside the QC images, the one comlog of the
suite outside the run's log folder and out of reach of ``--comlog_folders``.
"""

import os

import pytest

import qx_utilities.general.log as gl
import qx_utilities.hcp.qc_hcp as qc_hcp
import qx_utilities.processing.core as pc

from .utils import build_hcp_session, default_options, write_script


class Inline:
    """A process pool that runs every job in this process, in order."""

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def map(self, function, jobs):
        return [function(job) for job in jobs]


@pytest.fixture(autouse=True)
def default_settings():
    """The process-wide log settings are the defaults here, and reset after."""
    gl.set_active(gl.LogSettings())
    yield
    gl.set_active(None)


@pytest.fixture
def t1w_qc(tmp_path, monkeypatch):
    """
    A session ready for T1w QC, its jobs run in this process. Returns the
    session, its sessions folder, the run's comlogs folder and a function that
    builds the options of a real run.
    """
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    monkeypatch.setattr(qc_hcp, "ProcessPoolExecutor", Inline)
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "template_t1w_qc.wb.scene").write_text("DUMMYPATH")
    sinfo, sessionsfolder = build_hcp_session(str(tmp_path))
    hcp = os.path.join(sessionsfolder, sinfo["id"], "hcp", sinfo["id"])
    open(os.path.join(hcp, "MNINonLinear", "T1w_restore.nii.gz"), "w").close()
    comlogs = str(tmp_path / "logs" / "run" / "comlogs")

    def options(**overrides):
        return default_options(
            run="run",
            sessionsfolder=sessionsfolder,
            comlogs=comlogs,
            qc_scenetemplatefolder=str(templates),
            qc_modality="T1w",
            qc_scenezip="no",
            **overrides,
        )

    return sinfo, sessionsfolder, comlogs, options


def no_qclog(folder):
    return not any("qclog" in dirs for _, dirs, _ in os.walk(folder))


@pytest.mark.parametrize(
    "comlog_folders, session_copy", [("", False), ("study,session", True)]
)
def test_the_qc_calls_log_in_the_run_s_comlogs(
    t1w_qc, monkeypatch, comlog_folders, session_copy
):
    """Every QC call is handed the run's comlogs, with the destinations it names."""
    sinfo, sessionsfolder, comlogs, options = t1w_qc
    folders = []

    def external(checkfile, run, description, **kwargs):
        folders.append(kwargs.get("logfolder"))
        return None, "done", 0

    monkeypatch.setattr(pc, "run_external_for_file", external)

    qc_hcp.hcp_run_qc(sinfo, options(comlog_folders=comlog_folders))

    expected = [comlogs] + (
        [os.path.join(sessionsfolder, sinfo["id"], "logs", "comlogs")]
        if session_copy
        else []
    )
    assert folders and all(folder == expected for folder in folders), folders
    assert no_qclog(sessionsfolder), "no qclog folder beside the QC images"


@pytest.mark.parametrize("fails", [False, True], ids=["kept", "failed"])
def test_a_qc_comlog_is_the_run_s_and_copied_where_comlog_folders_says(
    t1w_qc, tmp_path, monkeypatch, fails
):
    """
    Through the call itself, with a stand-in for Workbench: the comlog is
    written into the run's comlogs folder and copied into the session's. A
    call that completes removes its comlog unless comlogs are kept, so the
    run that completes keeps them; a call that fails keeps its comlog anyway.
    """
    sinfo, sessionsfolder, comlogs, options = t1w_qc
    (tmp_path / "bin").mkdir()
    # -show-scene <scene> 1 <png> <width> <height>
    write_script(
        tmp_path / "bin" / "wb_command",
        '#!/bin/sh\necho "wb_command $*"\n%s\n' % ("exit 1" if fails else 'touch "$4"'),
    )
    monkeypatch.setenv(
        "PATH", "%s%s%s" % (tmp_path / "bin", os.pathsep, os.environ["PATH"])
    )
    gl.set_active(gl.LogSettings(keep_comlogs=not fails))

    log = qc_hcp.hcp_run_qc(sinfo, options(comlog_folders="study,session"))

    (name,) = os.listdir(comlogs)
    status = "error_" if fails else "done_"
    assert name.startswith(status + "hcp_run_qc_show_scene"), name
    with open(os.path.join(comlogs, name)) as comlog:
        assert "wb_command -show-scene" in comlog.read()
    copy = os.path.join(sessionsfolder, sinfo["id"], "logs", "comlogs", name)
    assert os.path.exists(copy), "copied where --comlog_folders says"
    assert no_qclog(sessionsfolder), "no qclog folder beside the QC images"
    assert log.status[2] == (1 if fails else 0), log.text
