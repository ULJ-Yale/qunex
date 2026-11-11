#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``general/nii2bids.py``: ``map_nii2bids``.

``map_nii2bids`` never read ``options["run"]``, so ``--test`` created the
bids folder, wrote ``nii2bids.log``, emptied an existing bids folder under
``--overwrite=yes`` and linked every image. A dry run now changes nothing and
still names every mapping it would make.

A repeated image -- a second T1w, a second spin echo pair, a second DWI of the
same direction -- was given the name of the first and dropped, with a warning
only in ``nii2bids.log``, and no fieldmap carried ``IntendedFor``. Images are
now told apart by ``run`` (a fieldmap set by its ``se()``/``fm()`` number, a
boldref by its bold), a DWI label gives ``acq`` and ``dir``, and a fieldmap's
``IntendedFor`` and a bold's ``TaskName`` are filled in from the session
record. Those sidecars are written as new files, so a hard linked nii sidecar
stays as it is. The images come from the batch file record when it holds them,
and a session named without a batch file is read from its ``session_hcp.txt``
instead of failing on a missing ``session`` key.
"""

import json
import os
from pathlib import Path

import pytest

import qx_utilities.general.core as gc
import qx_utilities.general.nii2bids as nb
from tests.utils import default_options

REPO = Path(__file__).resolve().parents[2]
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


@pytest.fixture(autouse=True)
def bids_schema(monkeypatch):
    """The schema is found in the source tree, without the QuNex environment."""
    if not BIDS_SCHEMA.is_file():
        pytest.skip("the BIDS schema needs the qx_library submodule")
    monkeypatch.delenv("QUNEXPATH", raising=False)


# ---------------------------------------------------------------------------
# map_nii2bids under --test


@pytest.fixture
def nii_session(tmp_path):
    """A session with two nii images and its session_hcp.txt, and no bids folder."""
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
    log = nb.map_nii2bids(sessions, options, overwrite, 1)

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
    log = nb.map_nii2bids(sessions, options, "yes", 1)

    assert log.status[1:] == ("mapping to BIDS completed", 0)
    bids = session / "bids"
    assert (bids / "anat" / "sub-01_ses-1_T1w.nii.gz").read_text() == "t1"
    assert (bids / "func" / "sub-01_ses-1_task-rest_bold.nii.gz").read_text() == "bold"
    assert (bids / "nii2bids.log").is_file()


# ---------------------------------------------------------------------------
# repeated images, IntendedFor and TaskName


SESSION_HCP = """session: 01_1
subject: 01
raw_data: nii
hcp: hcp

hcpready: true

10: : Localizer
11: SE-FM-AP : SpinEchoFieldMap_AP : se(1)
12: SE-FM-PA : SpinEchoFieldMap_PA : se(1)
13: boldref1:rest : rfMRI_REST_AP_SBRef : se(1): phenc(AP)
14: bold1:rest : rfMRI_REST_AP : se(1): phenc(AP)
15: bold2:rest : rfMRI_REST_AP : se(1): phenc(AP)
16: T1w : T1w_MPR : se(1)
17: T1w : T1w_MPR : se(1)
21: SE-FM-AP : SpinEchoFieldMap_AP : se(2)
22: SE-FM-PA : SpinEchoFieldMap_PA : se(2)
23: DWI:dir98_AP : dMRI_dir98_AP : se(2)
24: DWI:dir99_AP : dMRI_dir99_AP : se(2)
"""

FMAP_SIDECAR = {"PhaseEncodingDirection": "j-", "TotalReadoutTime": 0.05}

SES = "sub-01_ses-1"
URI = "bids::sub-01/ses-1"

# what every image of SESSION_HCP is mapped to
MAPPED = {
    "fmap": [
        f"{SES}_dir-AP_run-1_epi",
        f"{SES}_dir-PA_run-1_epi",
        f"{SES}_dir-AP_run-2_epi",
        f"{SES}_dir-PA_run-2_epi",
    ],
    # bold1 and bold2 clash, and boldref1 takes the run of its bold
    "func": [
        f"{SES}_task-rest_dir-AP_run-1_sbref",
        f"{SES}_task-rest_dir-AP_run-1_bold",
        f"{SES}_task-rest_dir-AP_run-2_bold",
    ],
    "anat": [f"{SES}_run-1_T1w", f"{SES}_run-2_T1w"],
    # the DWI label is its acquisition and direction
    "dwi": [f"{SES}_acq-dir98_dir-AP_dwi", f"{SES}_acq-dir99_dir-AP_dwi"],
}


@pytest.fixture
def repeated_session(tmp_path):
    """A session with two spin echo pairs, and two bolds, T1w images and DWIs."""
    study = tmp_path / "study"
    session = study / "sessions" / "01_1"
    nii = session / "nii"
    for image in ["10", "11", "12", "13", "14", "15", "16", "17", "21", "22", "23", "24"]:
        _write(nii / f"{image}.nii.gz", f"image {image}")
    for image in ["11", "12", "21", "22"]:
        _write(nii / f"{image}.json", json.dumps(FMAP_SIDECAR))
    for image in ["13", "14", "15", "16"]:
        _write(nii / f"{image}.json", json.dumps({"RepetitionTime": 0.8}))
    for image in ["23", "24"]:
        _write(nii / f"{image}.bval", "0 1000")
        _write(nii / f"{image}.bvec", "0 1\n0 0\n0 0")
    _write(session / "session_hcp.txt", SESSION_HCP)
    sessions = [{"id": "01_1", "session": "01_1", "subject": "01"}]
    return study, session, sessions


def _map(study, sessions, run="run", **options):
    options = default_options(studyfolder=str(study), run=run, **options)
    return nb.map_nii2bids(sessions, options, "yes", 1)


def _sidecar(session, folder, stem):
    return json.loads((session / "bids" / folder / f"{stem}.json").read_text())


def test_repeated_images_are_all_mapped_under_their_own_name(repeated_session):
    study, session, sessions = repeated_session
    log = _map(study, sessions)

    assert log.status[1:] == ("mapping to BIDS completed", 0)
    expected = {
        f"{folder}/{stem}.nii.gz" for folder, stems in MAPPED.items() for stem in stems
    }
    found = {
        name
        for name in _tree(session / "bids")
        if name.endswith(".nii.gz")
    }
    assert found == expected
    assert (session / "bids" / "dwi" / f"{SES}_acq-dir99_dir-AP_dwi.bval").is_file()
    assert "already exists" not in log.text


def test_a_fieldmap_is_intended_for_the_images_that_name_its_set(repeated_session):
    study, session, sessions = repeated_session
    _map(study, sessions)

    first = [
        f"{URI}/func/{SES}_task-rest_dir-AP_run-1_sbref.nii.gz",
        f"{URI}/func/{SES}_task-rest_dir-AP_run-1_bold.nii.gz",
        f"{URI}/func/{SES}_task-rest_dir-AP_run-2_bold.nii.gz",
        f"{URI}/anat/{SES}_run-1_T1w.nii.gz",
        f"{URI}/anat/{SES}_run-2_T1w.nii.gz",
    ]
    second = [
        f"{URI}/dwi/{SES}_acq-dir98_dir-AP_dwi.nii.gz",
        f"{URI}/dwi/{SES}_acq-dir99_dir-AP_dwi.nii.gz",
    ]
    for direction in ["AP", "PA"]:
        one = _sidecar(session, "fmap", f"{SES}_dir-{direction}_run-1_epi")
        two = _sidecar(session, "fmap", f"{SES}_dir-{direction}_run-2_epi")
        assert one == {**FMAP_SIDECAR, "IntendedFor": first}
        assert two == {**FMAP_SIDECAR, "IntendedFor": second}

    # the bold's TaskName is filled in, an sbref needs none
    bold = _sidecar(session, "func", f"{SES}_task-rest_dir-AP_run-1_bold")
    assert bold == {"RepetitionTime": 0.8, "TaskName": "rest"}
    sbref = _sidecar(session, "func", f"{SES}_task-rest_dir-AP_run-1_sbref")
    assert sbref == {"RepetitionTime": 0.8}


@pytest.mark.parametrize("action", ["hardlink", "copy"])
def test_the_nii_sidecars_stay_as_they_are(repeated_session, action):
    study, session, sessions = repeated_session
    nii = session / "nii"
    before = _tree(nii)

    _map(study, sessions, action=action)

    assert _tree(nii) == before
    bids = session / "bids"
    written = bids / "fmap" / f"{SES}_dir-AP_run-1_epi.json"
    assert not os.path.samefile(written, nii / "11.json")
    kept = bids / "anat" / f"{SES}_run-1_T1w.json"
    assert os.path.samefile(kept, nii / "16.json") == (action == "hardlink")


def test_an_intended_for_of_the_nii_sidecar_is_kept(repeated_session):
    study, session, sessions = repeated_session
    stated = {**FMAP_SIDECAR, "IntendedFor": ["bids::sub-01/ses-1/func/x_bold.nii.gz"]}
    _write(session / "nii" / "21.json", json.dumps(stated))

    _map(study, sessions)

    assert _sidecar(session, "fmap", f"{SES}_dir-AP_run-2_epi") == stated


def test_the_images_come_from_the_batch_file_record(repeated_session):
    """A batch file made from session_hcp.txt files holds the images itself."""
    study, session, sessions = repeated_session
    batch = study / "processing" / "batch.txt"
    _write(batch, SESSION_HCP)
    os.remove(session / "session_hcp.txt")
    # read as gmri reads it: the folders a record names are resolved against
    # the session's folder
    records, _ = gc.resolve_sessions(
        batchfile=str(batch), sessionsfolder=str(study / "sessions")
    )

    log = _map(study, records)

    assert "reading the session's images from the batch file" in log.text
    assert _sidecar(session, "fmap", f"{SES}_dir-AP_run-2_epi")["IntendedFor"]


def test_a_session_named_without_a_batch_file(repeated_session):
    """Its record is its id alone; session and subject are in session_hcp.txt."""
    study, session, sessions = repeated_session
    log = _map(study, [{"id": "01_1"}])

    assert "reading the session's images from session_hcp.txt" in log.text
    assert (session / "bids" / "anat" / f"{SES}_run-2_T1w.nii.gz").is_file()


def test_a_dry_run_names_the_sidecars_it_would_write(repeated_session):
    study, session, sessions = repeated_session
    before = _tree(session)

    log = _map(study, sessions, run="test")

    assert _tree(session) == before
    assert (
        f"test, not written: 11.json -> fmap/{SES}_dir-AP_run-1_epi.json, "
        f"adding IntendedFor func/{SES}_task-rest_dir-AP_run-1_sbref.nii.gz"
    ) in log.text
    assert (
        f"test, not written: 14.json -> func/{SES}_task-rest_dir-AP_run-1_bold.json, "
        "adding TaskName rest"
    ) in log.text


def test_an_intended_for_that_can_not_be_deduced_is_reported(tmp_path):
    study = tmp_path / "study"
    session = study / "sessions" / "01_1"
    _write(session / "nii" / "1.nii.gz", "ap")
    _write(session / "nii" / "1.json", json.dumps(FMAP_SIDECAR))
    _write(session / "nii" / "2.nii.gz", "bold")
    _write(
        session / "session_hcp.txt",
        "session: 01_1\nsubject: 01\n\n"
        "1: SE-FM-AP : SpinEchoFieldMap_AP\n2: bold1:rest : rest : phenc(AP)\n",
    )

    log = _map(study, [{"id": "01_1"}])

    # the runlog says so, not only nii2bids.log
    assert (
        f"WARNING: IntendedFor of {SES}_dir-AP_epi not set, "
        "the session file gives image 1 no se() number"
    ) in log.text
    assert _sidecar(session, "fmap", f"{SES}_dir-AP_epi") == FMAP_SIDECAR


def test_a_clash_a_specified_run_makes_is_reported_in_the_runlog(tmp_path):
    study = tmp_path / "study"
    session = study / "sessions" / "01_1"
    _write(session / "nii" / "1.nii.gz", "first")
    _write(session / "nii" / "2.nii.gz", "second")
    _write(
        session / "session_hcp.txt",
        "session: 01_1\nsubject: 01\n\n"
        "1: T1w : T1w_MPR : run(1)\n2: T1w : T1w_MPR : run(1)\n",
    )

    log = _map(study, [{"id": "01_1"}])

    assert "WARNING: tried to map 2.nii.gz" in log.text
    t1w = session / "bids" / "anat" / f"{SES}_run-1_T1w.nii.gz"
    assert t1w.read_text() == "first"


def _session(tmp_path, images, files, sidecars=()):
    """A session with a session_hcp.txt of `images`, and `files` in its nii folder."""
    study = tmp_path / "study"
    session = study / "sessions" / "01_1"
    for name in files:
        _write(session / "nii" / name, name)
    for name in sidecars:
        _write(session / "nii" / name, "{}")
    _write(session / "session_hcp.txt", "session: 01_1\nsubject: 01\n\n" + images)
    return study, session


def test_gradient_echo_fieldmap_sets_are_numbered_by_their_fm(tmp_path):
    study, session = _session(
        tmp_path,
        "1: FM-Magnitude : mag : fm(1): suffix(magnitude1)\n"
        "2: FM-Phase : phase : fm(1)\n"
        "3: bold1:rest : rest : fm(1)\n"
        "4: FM-Magnitude : mag : fm(2): suffix(magnitude1)\n"
        "5: FM-Phase : phase : fm(2)\n"
        "6: bold2:rest : rest : fm(2)\n",
        [f"{n}.nii.gz" for n in range(1, 7)],
        ["1.json", "2.json", "4.json", "5.json"],
    )

    _map(study, [{"id": "01_1"}])

    for run in ["1", "2"]:
        phasediff = _sidecar(session, "fmap", f"{SES}_run-{run}_phasediff")
        bold = f"{URI}/func/{SES}_task-rest_run-{run}_bold.nii.gz"
        assert phasediff == {"IntendedFor": [bold]}
        # a magnitude image needs none
        assert _sidecar(session, "fmap", f"{SES}_run-{run}_magnitude1") == {}


def test_two_images_of_one_fieldmap_set_that_read_the_same_are_reported(tmp_path):
    """Not repeats: the second magnitude image needs its suffix() set."""
    study, session = _session(
        tmp_path,
        "1: FM-Magnitude : mag : fm(1)\n"
        "2: FM-Magnitude : mag : fm(1)\n"
        "3: FM-Phase : phase : fm(1)\n"
        "4: FM-Magnitude : mag : fm(2)\n"
        "5: FM-Phase : phase : fm(2)\n",
        [f"{n}.nii.gz" for n in range(1, 6)],
    )

    log = _map(study, [{"id": "01_1"}])

    assert (
        f"WARNING: tried to map 2.nii.gz to file {SES}_run-1_magnitude.nii.gz" in log.text
    )
    fmap = session / "bids" / "fmap"
    assert (fmap / f"{SES}_run-1_magnitude.nii.gz").read_text() == "1.nii.gz"
    assert (fmap / f"{SES}_run-2_magnitude.nii.gz").read_text() == "4.nii.gz"


def test_the_nii_folder_session_hcp_txt_names_is_used(tmp_path):
    """Without a batch file, a folder named in session_hcp.txt is the session's."""
    study = tmp_path / "study"
    session = study / "sessions" / "01_1"
    _write(session / "raw" / "1.nii.gz", "t1")
    _write(
        session / "session_hcp.txt",
        "session: 01_1\nsubject: 01\nraw_data: raw\n\n1: T1w : T1w_MPR\n",
    )

    _map(study, [{"id": "01_1"}])

    assert (session / "bids" / "anat" / f"{SES}_T1w.nii.gz").read_text() == "t1"
