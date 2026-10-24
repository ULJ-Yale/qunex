#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``general/bids.py``: where ``import_bids`` files a dataset, and what a
``map_nii2bids`` dry run leaves behind.

``import_bids`` stores the files that pertain to a dataset as a whole in
``<studyfolder>/info/bids/<bidsname>``. A given ``--bidsname`` is used as it
is; without one the dataset is named after its folder or package, and a dataset
in the study's own inbox (``<sessionsfolder>/inbox/BIDS``) has no name, so its
files go straight to ``info/bids``. A subject or session folder inside that
inbox is part of the inbox dataset: it used to be named after its parent
folder, ``BIDS``, and filed under ``info/bids/BIDS``.

``map_nii2bids`` never read ``options["run"]``, so ``--test`` created the
bids folder, wrote ``nii2bids.log``, emptied an existing bids folder under
``--overwrite=yes`` and linked every image. A dry run now changes nothing and
still names every mapping it would make.
"""

import json
import os
from pathlib import Path

import pytest

import qx_utilities.general.bids as gb
from qx_utilities.general.log import ReportLog
from tests.utils import default_options

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "python" / "qx_utilities" / "templates"
BIDS_SCHEMA = REPO / "qx_library" / "etc" / "bids" / "schema.json"


def _write(path, content=""):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _tree(root):
    """Every file under `root`, with its content."""
    found = {}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            with open(path, "rb") as f:
                found[os.path.relpath(path, root)] = f.read()
    return found


def _folders(root):
    return sorted(os.path.relpath(d, root) for d, _, _ in os.walk(root))


# ---------------------------------------------------------------------------
# import_bids: the study-level files of the dataset


def _bids_dataset(root):
    """A one-subject, one-session BIDS dataset with a T1w and a resting BOLD."""
    _write(os.path.join(root, "dataset_description.json"), json.dumps({"Name": "x"}))
    _write(os.path.join(root, "participants.tsv"), "participant_id\tage\nsub-01\t30\n")
    base = os.path.join(root, "sub-01", "ses-1")
    _write(os.path.join(base, "anat", "sub-01_ses-1_T1w.nii.gz"), "t1")
    _write(os.path.join(base, "anat", "sub-01_ses-1_T1w.json"), "{}")
    _write(os.path.join(base, "func", "sub-01_ses-1_task-rest_bold.nii.gz"), "b")
    _write(
        os.path.join(base, "func", "sub-01_ses-1_task-rest_bold.json"),
        json.dumps({"PhaseEncodingDirection": "j-"}),
    )


@pytest.fixture
def bids_study(tmp_path, monkeypatch):
    """A study, and a BIDS dataset in its default inbox and in a folder outside."""
    # import_bids reads the BIDS structure from the template folder the QuNex
    # environment names; a test outside that environment names it itself
    monkeypatch.setenv("NIUTemplateFolder", str(TEMPLATES))
    study = tmp_path / "study"
    sessions = study / "sessions"
    sessions.mkdir(parents=True)
    _bids_dataset(sessions / "inbox" / "BIDS")
    _bids_dataset(tmp_path / "ext" / "myds")
    return {
        "<study>": str(study),
        "<sessions>": str(sessions),
        "<ext>": str(tmp_path / "ext" / "myds"),
    }


def _fill(value, paths):
    for key, path in paths.items():
        value = value.replace(key, path)
    return value


@pytest.mark.parametrize(
    "inbox, bidsname, info",
    [
        # the study's own inbox has no name
        (None, None, "info/bids"),
        # a subject folder in it belongs to that dataset, not to one named BIDS
        ("<sessions>/inbox/BIDS/sub-01", None, "info/bids"),
        # a dataset elsewhere is named after its folder
        ("<ext>", None, "info/bids/myds"),
        ("<ext>/sub-01/ses-1", None, "info/bids/myds"),
        # a given name is used as it is
        (None, "swga", "info/bids/swga"),
        ("<ext>", "named", "info/bids/named"),
    ],
)
def test_import_bids_files_the_dataset_under_its_name(bids_study, inbox, bidsname, info):
    kwargs = {"studyfolder": bids_study["<study>"]}
    if inbox is not None:
        kwargs["inbox"] = _fill(inbox, bids_study)
    if bidsname is not None:
        kwargs["bidsname"] = bidsname

    gb.import_bids(**kwargs, _log=ReportLog())

    study = Path(bids_study["<study>"])
    found = sorted(
        str(p.relative_to(study)) for p in (study / "info").rglob("dataset_description.json")
    )
    assert found == [f"{info}/dataset_description.json"]
    assert (study / info / "participants.tsv").is_file()
    assert (study / "sessions" / "01_1" / "session.txt").is_file()


# ---------------------------------------------------------------------------
# map_nii2bids under --test


@pytest.fixture
def nii_session(tmp_path, monkeypatch):
    """A session with two nii images and its session_hcp.txt, and no bids folder."""
    if not BIDS_SCHEMA.is_file():
        pytest.skip("the BIDS schema needs the qx_library submodule")
    # the BIDS names are built from the schema in qx_library, which
    # _create_bids_name finds through QUNEXPATH
    monkeypatch.setenv("QUNEXPATH", str(REPO))

    study = tmp_path / "study"
    session = study / "sessions" / "01_1"
    _write(session / "nii" / "01.nii.gz", "t1")
    _write(session / "nii" / "02.nii.gz", "bold")
    _write(
        session / "session_hcp.txt",
        "session: 01_1\nsubject: 01\nraw_data: nii\nhcp: hcp\n\n"
        "01: T1w : T1w_MPR\n02: bold1:rest : rest\n",
    )
    # the record of a session imported from DICOM: it names no bids folder
    sessions = [{"id": "01_1", "session": "01_1", "subject": "01"}]
    return study, session, sessions


@pytest.mark.parametrize(
    "existing, overwrite", [(False, "no"), (False, "yes"), (True, "yes")]
)
def test_a_map_nii2bids_dry_run_changes_nothing(nii_session, existing, overwrite):
    study, session, sessions = nii_session
    if existing:
        _write(session / "bids" / "anat" / "sub-01_ses-1_T1w.nii.gz", "earlier")

    before, folders = _tree(session), _folders(session)
    options = default_options(studyfolder=str(study), run="test")
    log = gb.map_nii2bids(sessions, options, overwrite, 1)

    assert _tree(session) == before
    assert _folders(session) == folders
    assert not (session / "bids" / "nii2bids.log").exists()
    assert log.status[1:] == ("[TEST] mapping to BIDS completed", 0)

    # and every mapping is still named
    assert "test, not linked: 01.nii.gz -> anat/sub-01_ses-1_T1w.nii.gz" in log.text
    assert "test, not linked: 02.nii.gz -> func/sub-01_ses-1_task-rest_bold.nii.gz" in log.text
    if existing:
        assert "test, not removed: anat" in log.text
        # a target the run would clear first is not reported as a clash
        assert "already exists" not in log.text


def test_a_map_nii2bids_run_maps_the_same_images(nii_session):
    """The real run on the same session: the dry run above is not vacuous."""
    study, session, sessions = nii_session
    _write(session / "bids" / "anat" / "sub-01_ses-1_T1w.nii.gz", "earlier")

    options = default_options(studyfolder=str(study), run="run")
    log = gb.map_nii2bids(sessions, options, "yes", 1)

    assert log.status[1:] == ("mapping to BIDS completed", 0)
    bids = session / "bids"
    assert (bids / "anat" / "sub-01_ses-1_T1w.nii.gz").read_text() == "t1"
    assert (bids / "func" / "sub-01_ses-1_task-rest_bold.nii.gz").read_text() == "bold"
    assert (bids / "nii2bids.log").is_file()
