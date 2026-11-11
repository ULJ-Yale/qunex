#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``general/bids.py``: where ``import_bids`` files a dataset, and how
``process_bids`` reads a fieldmap's ``IntendedFor``. ``map_nii2bids`` is
tested in ``test_nii2bids.py``.

``import_bids`` stores the files that pertain to a dataset as a whole in
``<studyfolder>/info/bids/<bidsname>``. A given ``--bidsname`` is used as it
is; without one the dataset is named after its folder or package, and a dataset
in the study's own inbox (``<sessionsfolder>/inbox/BIDS``) has no name, so its
files go straight to ``info/bids``. A subject or session folder inside that
inbox is part of the inbox dataset: it used to be named after its parent
folder, ``BIDS``, and filed under ``info/bids/BIDS``.

A fieldmap whose ``IntendedFor`` names an image the dataset does not hold
stopped ``process_bids`` with a ``KeyError``; the image is now passed over.
"""

import json
import os
from pathlib import Path

import pytest

import qx_utilities.general.bids as gb
from qx_utilities.general.log import ReportLog

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "python" / "qx_utilities" / "templates"


def _write(path, content=""):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


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
# process_bids: a fieldmap's IntendedFor


def test_process_bids_passes_over_an_intended_for_it_does_not_hold(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("NIUTemplateFolder", str(TEMPLATES))
    base = tmp_path / "sub-01" / "ses-1"
    _write(base / "func" / "sub-01_ses-1_task-rest_bold.nii.gz", "b")
    _write(base / "fmap" / "sub-01_ses-1_dir-AP_epi.nii.gz", "ap")
    _write(
        base / "fmap" / "sub-01_ses-1_dir-AP_epi.json",
        json.dumps({
            "IntendedFor": [
                "bids::sub-01/ses-1/func/sub-01_ses-1_task-rest_bold.nii.gz",
                "ses-1/func/sub-01_ses-1_task-gone_bold.nii.gz",
            ]
        }),
    )

    images = gb.process_bids(str(tmp_path))["01_1"]["images"]["info"]

    assert images["sub-01_ses-1_task-rest_bold.nii.gz"]["seq_info"] == ["se(1)"]
