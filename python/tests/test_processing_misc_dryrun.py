#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Dry runs of ``rapidtide``, ``dwi_noddi_gpu`` and ``fsl_melodic``.

- ``rapidtide`` falls back to the ``--bolds`` values as HCP bold folder names
  when nothing in the batch file matches them. The fallback assumed the default
  was ``rest`` while ``process.arglist`` defaults ``bolds`` to ``all``, so a
  session with no BOLDs got the target ``all`` (and, in a run, a
  ``rapidtide/all`` folder), and it split on ``,`` only, so ``rest|task`` was
  one target. It now splits as ``use_or_skip_bold`` does and never falls back
  to ``all`` or ``rest``.
- ``dwi_noddi_gpu`` took CUDIMOT's results to be
  ``<dirname(diffusion folder)>/Diffusion.NODDI_<model>``. CUDIMOT writes
  ``<diffusion folder>.NODDI_<model>``, so with a ``--diffusion_folder`` not
  named ``Diffusion`` the skip check, the dry run and the overwrite removal all
  looked at the wrong folder.
- ``fsl_melodic`` runs one melodic over all the sessions. A missing input
  filed the study's one result under the session that missed it and went on
  searching the remaining sessions; it is now reported once, for the study.

Nothing external is run: ``subprocess`` is made fatal in every test.
"""

import os
import subprocess

import pytest

import qx_utilities.processing.dwi as dwi
import qx_utilities.processing.fsl as fsl
import qx_utilities.processing.rapidtide as rapidtide
from tests.utils import build_hcp_session, default_options


def _files(root):
    """Every file under `root`, with its size and mtime."""
    found = {}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            stat = os.stat(path)
            found[path] = (stat.st_size, stat.st_mtime_ns)
    return found


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def fatal(*args, **kwargs):
        raise AssertionError("a dry run executed an external command")

    for name in ("run", "call", "Popen", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, fatal)


def _options(tmp_path, sessionsfolder, **overrides):
    return default_options(
        sessionsfolder=sessionsfolder,
        studyfolder=str(tmp_path),
        comlogs=str(tmp_path / "comlogs"),
        **overrides,
    )


# ---------------------------------------------------------------------------
# rapidtide


@pytest.fixture
def rapidtide_session(tmp_path, monkeypatch):
    # the flirt step names FSL's identity matrix
    monkeypatch.setenv("FSLDIR", str(tmp_path / "fsl"))
    # and the HCP paths every bold is resolved through start at the pipelines
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    return build_hcp_session(str(tmp_path))


@pytest.mark.parametrize("run", ["test", "run"])
@pytest.mark.parametrize("bolds", ["all", "rest"])
def test_rapidtide_without_bolds_is_not_ready(tmp_path, rapidtide_session, run, bolds):
    """`all` and `rest` select bolds; neither is a bold folder name."""
    sinfo, sessionsfolder = rapidtide_session
    options = _options(tmp_path, sessionsfolder, run=run, bolds=bolds)

    log = rapidtide.rapidtide(sinfo, options)

    assert log.status == ("sess-01", "rapidtide not ready: no bolds found", 1)
    assert "No BOLD images found" in log.text
    assert "- all" not in log.text
    assert not os.path.exists(os.path.join(sessionsfolder, "sess-01", "rapidtide"))


@pytest.mark.parametrize(
    "bolds", ["BOLD_X|BOLD_Y", "BOLD_X BOLD_Y", "BOLD_X,BOLD_Y", "BOLD_X, BOLD_Y"]
)
def test_rapidtide_falls_back_to_each_bold_named(tmp_path, rapidtide_session, bolds):
    """Bolds the batch file does not have are used as folder names, one each."""
    sinfo, sessionsfolder = rapidtide_session
    options = _options(tmp_path, sessionsfolder, run="test", bolds=bolds)
    before = _files(tmp_path)

    log = rapidtide.rapidtide(sinfo, options)

    assert "Found 2 bolds:" in log.text
    lines = [line.strip() for line in log.text.splitlines()]
    assert "- BOLD_X" in lines and "- BOLD_Y" in lines
    assert "Working on bold BOLD_X" in log.text
    assert "Working on bold BOLD_Y" in log.text
    # the inputs are missing, so each is reported failed on its own
    assert log.status == ("sess-01", "rapidtide failed: BOLD_X,BOLD_Y", 2)
    # and a dry run leaves nothing behind
    assert _files(tmp_path) == before
    assert not os.path.exists(os.path.join(sessionsfolder, "sess-01", "rapidtide"))


# ---------------------------------------------------------------------------
# dwi_noddi_gpu


@pytest.fixture
def noddi_session(tmp_path, monkeypatch):
    monkeypatch.setenv("CUDIMOT", str(tmp_path / "cudimot"))
    sinfo, sessionsfolder = build_hcp_session(str(tmp_path))
    dmri = tmp_path / "NHP" / "dMRI"
    dmri.mkdir(parents=True)
    # where the results were looked for before: the sibling named after the
    # standard HCP diffusion folder, not after the folder given
    (tmp_path / "NHP" / "Diffusion.NODDI_Watson").mkdir()
    return sinfo, sessionsfolder, dmri


@pytest.mark.parametrize("trailing", ["", "/"], ids=["plain", "trailing_slash"])
def test_noddi_results_are_named_after_the_diffusion_folder(tmp_path, noddi_session, trailing):
    sinfo, sessionsfolder, dmri = noddi_session
    options = _options(
        tmp_path, sessionsfolder, run="test", diffusion_folder=str(dmri) + trailing
    )
    before = _files(tmp_path)

    log = dwi.dwi_noddi_gpu(sinfo, options)
    assert log.status == ("sess-01", "CUDIMOT NODDI ready", 0)
    assert "Pipeline_NODDI_Watson.sh" in log.text

    # once <diffusion folder>.NODDI_Watson is there, a run would skip it
    (tmp_path / "NHP" / "dMRI.NODDI_Watson").mkdir()
    log = dwi.dwi_noddi_gpu(sinfo, options)
    assert log.status == ("sess-01", "CUDIMOT NODDI would be skipped", 0)

    assert _files(tmp_path) == before


def test_noddi_results_of_the_hcp_diffusion_folder(tmp_path, noddi_session):
    """Without --diffusion_folder the results are next to T1w/Diffusion."""
    sinfo, sessionsfolder, _ = noddi_session
    options = _options(tmp_path, sessionsfolder, run="test")

    log = dwi.dwi_noddi_gpu(sinfo, options)
    assert log.status == ("sess-01", "CUDIMOT NODDI ready", 0)

    t1w = os.path.join(sinfo["hcp"], "sess-01", "T1w")
    os.makedirs(os.path.join(t1w, "Diffusion.NODDI_Watson"))
    log = dwi.dwi_noddi_gpu(sinfo, options)
    assert log.status == ("sess-01", "CUDIMOT NODDI would be skipped", 0)


# ---------------------------------------------------------------------------
# fsl_melodic


@pytest.fixture
def melodic_sessions(tmp_path):
    sessionsfolder = tmp_path / "sessions"
    for session in ("A", "B"):
        (sessionsfolder / session / "images" / "functional").mkdir(parents=True)
    return [{"id": "A"}, {"id": "B"}], sessionsfolder


def _bold(sessionsfolder, session):
    path = sessionsfolder / session / "images" / "functional" / "bold1.nii.gz"
    path.write_text("bold")
    return str(path)


@pytest.mark.parametrize("present, missing", [((), "A"), (("A",), "B")])
def test_melodic_reports_a_missing_input_once_for_the_study(
    tmp_path, melodic_sessions, present, missing
):
    sessions, sessionsfolder = melodic_sessions
    for session in present:
        _bold(sessionsfolder, session)
    options = _options(tmp_path, str(sessionsfolder), run="test", input_files="bold1")

    log = fsl.fsl_melodic(sessions, options)

    assert log.status == (
        "Study",
        f"Not ready for FSL melodic: bold1 missing for {missing}",
        1,
    )
    if missing == "A":
        # the run is doomed already, the remaining sessions are not searched
        assert "Working on session B" not in log.text


def test_melodic_is_one_command_over_every_session(tmp_path, melodic_sessions):
    sessions, sessionsfolder = melodic_sessions
    inputs = [_bold(sessionsfolder, session) for session in ("A", "B")]
    options = _options(tmp_path, str(sessionsfolder), run="test", input_files="bold1")
    before = _files(tmp_path)

    log = fsl.fsl_melodic(sessions, options)

    assert log.status == ("Study", "FSL melodic ready", 0)
    melodic = os.path.join(str(sessionsfolder), "melodic")
    assert f"melodic -i {','.join(inputs)} -o {melodic}" in log.text
    assert _files(tmp_path) == before
    assert not os.path.exists(melodic)
