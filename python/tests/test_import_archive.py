#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``import_hcp`` and ``import_nhp`` archive a dataset folder with ``--archive=copy``.

Both commands copied the dataset with ``shutil.copy2``, which raises
``IsADirectoryError`` for a folder. The error was caught, only "copy failed!"
was logged, nothing was archived and the run still reported success. Zip and
tar packages, which are files, archived correctly. Both now go through a
``_copy_to_archive`` helper that copies a folder into the archive under its
own name, as ``--archive=move`` places it, and a file as before.
"""

import os
from pathlib import Path

import pytest

import qx_utilities.hcp.import_hcp as ih
import qx_utilities.nhp.import_nhp as inhp
from qx_utilities.general.log import ReportLog

TEMPLATES = Path(__file__).resolve().parents[1] / "qx_utilities" / "templates"


def _write(path, content="x"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _files(root):
    root = Path(root)
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())


# ---------------------------------------------------------------------------
# the helper


@pytest.mark.parametrize("module", [ih, inhp], ids=["import_hcp", "import_nhp"])
@pytest.mark.parametrize("trailing", ["", "/"], ids=["plain", "trailing_slash"])
def test_a_folder_is_archived_under_its_own_name(tmp_path, module, trailing):
    dataset = tmp_path / "inbox" / "S01_MR"
    _write(dataset / "unprocessed" / "T1w.nii.gz", "t1")
    archive = tmp_path / "archive"
    archive.mkdir()

    module._copy_to_archive(str(dataset) + trailing, str(archive))

    assert _files(archive) == ["S01_MR/unprocessed/T1w.nii.gz"]
    # a copy, the dataset stays where it was
    assert (dataset / "unprocessed" / "T1w.nii.gz").is_file()

    # and copying it again, into the archive that now holds it, does not raise
    _write(dataset / "unprocessed" / "T2w.nii.gz", "t2")
    module._copy_to_archive(str(dataset) + trailing, str(archive))
    assert _files(archive) == [
        "S01_MR/unprocessed/T1w.nii.gz",
        "S01_MR/unprocessed/T2w.nii.gz",
    ]


@pytest.mark.parametrize("module", [ih, inhp], ids=["import_hcp", "import_nhp"])
def test_a_package_file_is_archived_as_it_is(tmp_path, module):
    package = tmp_path / "inbox" / "S01_MR.zip"
    _write(package, "zip")
    archive = tmp_path / "archive"
    archive.mkdir()

    module._copy_to_archive(str(package), str(archive))
    module._copy_to_archive(str(package), str(archive))

    assert _files(archive) == ["S01_MR.zip"]
    assert package.is_file()


# ---------------------------------------------------------------------------
# the commands


@pytest.fixture
def templates(monkeypatch):
    # the mapping reads its templates from the folder the QuNex environment
    # names; a test outside that environment names it itself
    monkeypatch.setenv("NIUTemplateFolder", str(TEMPLATES))


def _hcpls_dataset(root, sid="S01_MR"):
    """An unprocessed HCPLS session with a T1w and a resting state BOLD."""
    base = Path(root) / sid / "unprocessed"
    _write(base / "T1w_MPR" / f"{sid}_T1w_MPR.nii.gz", "t1")
    _write(
        base / "T1w_MPR" / f"{sid}_T1w_MPR.json",
        '{"Manufacturer": "M", "DwellTime": 0.000002}',
    )
    _write(base / "rfMRI_REST1_AP" / f"{sid}_rfMRI_REST1_AP.nii.gz", "bold")
    _write(
        base / "rfMRI_REST1_AP" / f"{sid}_rfMRI_REST1_AP.json",
        '{"PhaseEncodingDirection": "j-", "EffectiveEchoSpacing": 0.00058}',
    )


def _nhp_dataset(root):
    for sid in ("jane", "hilary"):
        for name in ("data.nii.gz", "bvals", "bvecs"):
            _write(Path(root) / sid / "dMRI" / name)


@pytest.mark.parametrize("external", [True, False], ids=["external_inbox", "study_inbox"])
def test_import_hcp_copies_a_dataset_folder_to_the_archive(tmp_path, templates, external):
    sessions = tmp_path / "study" / "sessions"
    if external:
        # a dataset folder given as --inbox is archived as one, under its name
        inbox = tmp_path / "HCPLS"
        (sessions / "inbox" / "HCPLS").mkdir(parents=True)
        prefix = "HCPLS/HCPLS/S01_MR"
    else:
        # the study's own inbox: each session folder in it is archived
        inbox = sessions / "inbox" / "HCPLS"
        prefix = "HCPLS/S01_MR"
    _hcpls_dataset(inbox)

    log = ReportLog()
    ih.import_hcp(
        sessionsfolder=str(sessions),
        inbox=str(inbox),
        action="copy",
        archive="copy",
        overwrite="no",
        _log=log,
    )

    assert "copy failed" not in log.text
    assert f"{prefix}/unprocessed/T1w_MPR/S01_MR_T1w_MPR.nii.gz" in _files(
        sessions / "archive"
    )
    # copied, not moved
    assert (inbox / "S01_MR" / "unprocessed" / "T1w_MPR").is_dir()


@pytest.mark.parametrize("external", [True, False], ids=["external_inbox", "study_inbox"])
def test_import_nhp_copies_a_dataset_folder_to_the_archive(tmp_path, external):
    sessions = tmp_path / "study" / "sessions"
    if external:
        inbox = tmp_path / "NHP"
        sessions.mkdir(parents=True)
        prefix = "NHP/NHP/"
    else:
        inbox = sessions / "inbox" / "NHP"
        prefix = "NHP/"
    _nhp_dataset(inbox)

    log = ReportLog()
    kwargs = {"inbox": str(inbox)} if external else {}
    inhp.import_nhp(
        sessionsfolder=str(sessions), action="copy", archive="copy", _log=log, **kwargs
    )

    assert "copy failed" not in log.text
    archived = _files(sessions / "archive")
    for sid in ("jane", "hilary"):
        assert f"{prefix}{sid}/dMRI/data.nii.gz" in archived
    assert (inbox / "jane" / "dMRI" / "data.nii.gz").is_file()
    assert os.path.isdir(sessions / "jane")
