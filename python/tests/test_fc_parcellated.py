# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
The fc commands on parcellated data.

A parcellated bold file (``.ptseries.nii``) has one row per parcel rather than
one per grayordinate, so the ROI used on it have to be defined over the same
rows: a parcellated label file (``.plabel.nii``) of the same parcellation,
which matches it row for row. ``.plabel.nii`` was missing from the CIFTI
extension table, so such a file was read as a plain volume, its label names
were never parsed, and a region selection through ``roiinfo`` was quietly
dropped -- the command ran and returned seedmaps for every parcel.

These drive the real commands through MATLAB/Octave and check the numbers
against a plain numpy computation, rather than against committed reference
data: the fixtures are built here from what the library already ships, so
nothing binary has to be carried for them.
"""

import os
import shutil
import subprocess

import numpy as np
import pytest

# nibabel and the qx registry are imported lazily inside the guard below, so
# that a checkout without them collects rather than errors
nib = pytest.importorskip("nibabel")
cifti2 = pytest.importorskip("nibabel.cifti2")

from qx_utilities.general import matlab as gm  # noqa: E402
from qx_registry import qx_commands  # noqa: E402


LIBRARY = os.environ.get("QUNEXLIBRARY", "")
PARCELLATION = os.path.join(
    LIBRARY, "data", "parcellations", "cole_anticevic_net_partition",
    "CortexSubcortex_ColeAnticevic_NetPartition_wSubcorGSR_parcels_LR_ReorderedByNetworks.dlabel.nii",
)
SESSIONS = ["OP242", "OP243"]
BOLD = "bold5s3_g7_hpss_res-mVWMWB1d.dtseries.nii"

# the seed used throughout: a subcortical parcel, so the volume half of the
# parcel specification is exercised as well as the surface half
SEED = "Visual1-55_L-Thalamus"
SECOND = "Visual2-05_R-Ctx"


def _session_bold(session):
    return os.path.join(LIBRARY, "matlab_tests", "subjects", session, BOLD)


def _have_matlab():
    """Whether the configured MATLAB/Octave runner is actually on PATH."""
    command = os.environ.get("QUNEXMCOMMAND", "").split()
    return bool(command) and shutil.which(command[0]) is not None


REQUIREMENTS = [
    (bool(LIBRARY) and os.path.exists(PARCELLATION), "qx_library parcellations not available"),
    (all(os.path.exists(_session_bold(s)) for s in SESSIONS), "qx_library test sessions not available"),
    (shutil.which("wb_command") is not None, "wb_command not on PATH"),
    (_have_matlab(), "no MATLAB/Octave runner on PATH"),
]
MISSING = [reason for met, reason in REQUIREMENTS if not met]

pytestmark = pytest.mark.skipif(bool(MISSING), reason="; ".join(MISSING))


@pytest.fixture(scope="module")
def parcellated(tmp_path_factory):
    """
    A parcellated study: two parcellated bolds, a file list and a .plabel.nii.

    Built with wb_command from the dense sessions and the parcellation the
    library ships, the way a user would: the bolds are parcellated with the
    dense parcellation, and the label file is a scalar of parcel indices
    imported as labels, so its parcels axis is the bolds' own and its label
    names are the parcel names.
    """
    root = tmp_path_factory.mktemp("parcellated")

    bolds = {}
    for session in SESSIONS:
        bolds[session] = os.path.join(root, "%s.ptseries.nii" % session)
        subprocess.run(
            ["wb_command", "-cifti-parcellate", _session_bold(session),
             PARCELLATION, "COLUMN", bolds[session]],
            check=True, capture_output=True,
        )

    flist = os.path.join(root, "parcellated.list")
    with open(flist, "w") as f:
        for session in SESSIONS:
            f.write("subject id:%s\n    file:%s\n" % (session, bolds[session]))

    # --- the parcellated label file, from the parcels axis of the bolds
    axis = nib.load(bolds[SESSIONS[0]]).header.get_axis(1)
    names = list(axis.name)

    index = os.path.join(root, "index.pscalar.nii")
    header = cifti2.Cifti2Header.from_axes((cifti2.ScalarAxis(["parcels"]), axis))
    data = np.arange(1, len(names) + 1, dtype=np.float32).reshape(1, -1)
    nib.Cifti2Image(data, header).to_filename(index)

    keys = os.path.join(root, "labels.txt")
    with open(keys, "w") as f:
        for key, name in enumerate(names, start=1):
            f.write("%s\n%d %d %d %d 255\n" % (name, key, key % 256, (key * 7) % 256, (key * 13) % 256))

    plabel = os.path.join(root, "parcels.plabel.nii")
    subprocess.run(
        ["wb_command", "-cifti-label-import", index, keys, plabel],
        check=True, capture_output=True,
    )

    return {"root": str(root), "flist": flist, "plabel": plabel,
            "bolds": bolds, "names": names}


def _target(tmp_path, name):
    """A target folder for a command to write into; they do not create one."""
    target = tmp_path / name
    target.mkdir(parents=True, exist_ok=True)
    return str(target)


def _run(command, args):
    """Run one fc command through the MATLAB/Octave runner, return its status."""
    return gm.run(qx_commands.get(command), dict(args))


def _timeseries(path):
    """The (frames, parcels) data of a parcellated image."""
    return np.asarray(nib.load(path).dataobj)


def _correlation(timeseries, seed_column):
    """Correlation of every column with one of them, the way fc_compute does."""
    z = (timeseries - timeseries.mean(0)) / timeseries.std(0)
    return (z * z[:, [seed_column]]).mean(0)


def test_seedmaps_computes_only_the_selected_parcel(parcellated, tmp_path):
    """The reported bug: a region selection used to be dropped silently."""
    target = _target(tmp_path, "seedmaps")
    status = _run("fc_compute_seedmaps", {
        "flist": parcellated["flist"],
        "roiinfo": "%s|rois:%s" % (parcellated["plabel"], SEED),
        "frames": "0",
        "targetf": target,
        "options": "ignore:use|fcmeasure:r|savegroup:none|saveind:r|saveindname:yes|itargetf:gfolder|verbose:false",
    })
    assert status == 0

    produced = sorted(os.listdir(target))
    assert len(produced) == len(SESSIONS), produced
    assert all(SEED in name and name.endswith(".pscalar.nii") for name in produced), produced


def test_seedmaps_match_a_plain_correlation(parcellated, tmp_path):
    target = _target(tmp_path, "seedmaps")
    assert _run("fc_compute_seedmaps", {
        "flist": parcellated["flist"],
        "roiinfo": "%s|rois:%s" % (parcellated["plabel"], SEED),
        "frames": "0",
        "targetf": target,
        "options": "ignore:use|fcmeasure:r|savegroup:none|saveind:r|saveindname:yes|itargetf:gfolder|verbose:false",
    }) == 0

    seed = parcellated["names"].index(SEED)
    for session in SESSIONS:
        produced = [f for f in os.listdir(target) if session in f]
        assert len(produced) == 1, produced

        got = _timeseries(os.path.join(target, produced[0])).reshape(-1)
        expected = _correlation(_timeseries(parcellated["bolds"][session]), seed)

        assert got.shape == expected.shape
        assert np.allclose(got, expected, atol=1e-5)
        # a seed correlates perfectly with itself, which pins the row that
        # was used down to the one that was asked for
        assert got[seed] == pytest.approx(1.0, abs=1e-5)


def test_seedmaps_reject_an_unknown_option_key(parcellated, tmp_path, capfd):
    """`parcels:` is not a key of the ROI specification; `rois:` is."""
    target = _target(tmp_path, "seedmaps")
    assert _run("fc_compute_seedmaps", {
        "flist": parcellated["flist"],
        "roiinfo": "%s|parcels:%s" % (parcellated["plabel"], SEED),
        "frames": "0",
        "targetf": target,
        "options": "ignore:use|fcmeasure:r|savegroup:none|saveind:r|saveindname:yes|itargetf:gfolder|verbose:false",
    }) != 0
    assert "unknown option(s)" in capfd.readouterr().out
    assert os.listdir(target) == []


def test_seedmaps_reject_a_region_that_is_not_there(parcellated, tmp_path, capfd):
    target = _target(tmp_path, "seedmaps")
    assert _run("fc_compute_seedmaps", {
        "flist": parcellated["flist"],
        "roiinfo": "%s|rois:NoSuchRegion" % parcellated["plabel"],
        "frames": "0",
        "targetf": target,
        "options": "ignore:use|fcmeasure:r|savegroup:none|saveind:r|saveindname:yes|itargetf:gfolder|verbose:false",
    }) != 0
    assert "could not be found" in capfd.readouterr().out
    assert os.listdir(target) == []


def test_extract_roi_timeseries_keeps_the_parcels_it_selected(parcellated, tmp_path):
    """The extracted ptseries carries the selected parcels, geometry and all."""
    target = _target(tmp_path, "timeseries")
    assert _run("fc_extract_roi_timeseries", {
        "flist": parcellated["flist"],
        "roiinfo": "%s|rois:%s,%s" % (parcellated["plabel"], SEED, SECOND),
        "frames": "0",
        "targetf": target,
        "options": "ignore:use|savegroup:none|saveind:ptseries|savesessionid:yes|itargetf:gfolder|verbose:false",
    }) == 0

    produced = [f for f in os.listdir(target) if f.endswith(".ptseries.nii") and SESSIONS[0] in f]
    assert len(produced) == 1, os.listdir(target)

    extracted = nib.load(os.path.join(target, produced[0]))
    axis = extracted.header.get_axis(1)
    assert list(axis.name) == [SEED, SECOND]

    source = _timeseries(parcellated["bolds"][SESSIONS[0]])
    rows = [parcellated["names"].index(n) for n in [SEED, SECOND]]
    assert np.allclose(np.asarray(extracted.dataobj), source[:, rows])

    # the seed is subcortical and the second parcel cortical, so between them
    # both halves of a parcel specification have to survive the extraction
    assert len(axis.voxels[0]) > 0 and not axis.vertices[0]
    assert axis.vertices[1] and (axis.voxels[1] is None or len(axis.voxels[1]) == 0)


def test_gbc_runs_on_parcellated_data(parcellated, tmp_path):
    target = _target(tmp_path, "gbc")
    assert _run("fc_compute_gbc", {
        "flist": parcellated["flist"],
        "command": "mFz:0.2",
        "sroiinfo": "%s|rois:%s,%s" % (parcellated["plabel"], SEED, SECOND),
        "troiinfo": parcellated["plabel"],
        "frames": "0",
        "targetf": target,
        "options": "ignore:use|fcmeasure:r|savegroup:none|saveind:all|saveindname:yes|itargetf:gfolder|verbose:false|debug:false",
    }) == 0

    produced = [f for f in os.listdir(target) if f.endswith(".pscalar.nii")]
    assert len(produced) == len(SESSIONS), os.listdir(target)

    gbc = nib.load(os.path.join(target, produced[0]))
    assert list(gbc.header.get_axis(1).name) == parcellated["names"]
