#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
A ``--test`` run links and copies no file and sets no environment variable.

Three things did, whatever the flag said:

- ``pc.get_file_names`` hard-linked a legacy (NIL) 4dfp session's
  ``mprage_111_*``, ``aseg_111/333`` and ``aparc+aseg_111/333`` images to their
  QuNex names, ten links per session, for every command that resolves a 4dfp
  session's files. A dry run now notes each link it did not make, and the
  checks that read a linked name look for the legacy image instead -- without
  that a dry run would report the segmentation missing, or plan a FreeSurfer
  run the real one would not make;
- ``gmri`` set ``OMP_NUM_THREADS`` for every command;
- ``process.run`` created the ``comlogs`` folder a dry run never writes to.

The extension MATLAB path is handed to the matlab call instead of being put in
this process's environment, in a real run as well. ``hcp_icafix`` and
``hcp_apply_auto_reclean``'s ``FSL_FIX_MATLAB_MODE`` are in ``test_hcp_dryrun``.

As in ``test_fs_dryrun``, files are compared and directories are not:
``pc.get_session_folders`` creates the session skeleton, which is out of scope.
"""

import importlib.machinery
import importlib.util
import os
import subprocess
import time

import pytest
import yaml

import qx_utilities.general.commands_support as gcs
import qx_utilities.general.log as gl
import qx_utilities.general.log.context as glc
import qx_utilities.general.log.settings as gls
import qx_utilities.general.matlab as gm
import qx_utilities.processing.core as pc
import qx_utilities.processing.fs as fs
import qx_utilities.processing.workflow as wf
from tests.utils import default_options

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# the legacy image each QuNex name is linked from, and the folder both are in
LEGACY = {
    "structural": {
        "T1_brain": "mprage_111_brain",
        "T1_seg": "mprage_111_seg",
    },
    "segmentation/freesurfer/mri": {
        "aseg_t1": "aseg_111",
        "aseg_bold": "aseg_333",
        "aparc+aseg_t1": "aparc+aseg_111",
        "aparc+aseg_bold": "aparc+aseg_333",
    },
}

# every command that resolves the files with a log of its own at hand
COMMANDS = [
    (fs, "run_basic_structural_segmentation"),
    (fs, "check_for_freesurfer_data"),
    (fs, "run_freesurfer_full_segmentation"),
    (fs, "run_freesurfer_subcortical_segmentation"),
    (wf, "extract_nuisance_signal"),
    (wf, "create_bold_brain_masks"),
    (wf, "compute_bold_stats"),
]


def _tree(root):
    """
    Every file under `root`, with its size, mtime and link count: a hard link
    made to a file leaves it unchanged but for the count.
    """
    found = {}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            stat = os.stat(path)
            found[path] = (stat.st_size, stat.st_mtime_ns, stat.st_nlink)
    return found


@pytest.fixture
def legacy(tmp_path, monkeypatch):
    """
    A 4dfp session as the legacy NIL preprocessing left it, with the BOLD data
    the workflow commands look for. Every external call is fatal.
    """
    sessions = tmp_path / "sessions"
    session = sessions / "s01"
    atlas = session / "4dfp" / "atlas"
    atlas.mkdir(parents=True)
    for ext in (".4dfp.img", ".4dfp.ifh"):
        (atlas / ("s01_mpr_n1_111_t88" + ext)).write_bytes(b"x" * 300)

    images = session / "images"
    for folder, names in LEGACY.items():
        (images / folder).mkdir(parents=True)
        for name in names.values():
            for ext in (".4dfp.img", ".4dfp.ifh"):
                (images / folder / (name + ext)).write_bytes(b"x" * 300)

    functional = images / "functional"
    (functional / "movement").mkdir(parents=True)
    masks = images / "segmentation" / "boldmasks"
    masks.mkdir(parents=True)
    (functional / "bold1.nii.gz").write_bytes(b"x" * 300)
    for tail in ("_frame1.nii.gz", "_frame1_brain.nii.gz", "_frame1_brain_mask.nii.gz"):
        (masks / ("bold1" + tail)).write_bytes(b"x" * 300)

    def no_external(*args, **kwargs):
        raise AssertionError("a --test run executed an external command")

    for name in ("run", "call", "check_call", "Popen"):
        monkeypatch.setattr(subprocess, name, no_external)
    monkeypatch.setattr(time, "sleep", lambda *_: None)

    options = default_options(
        sessionsfolder=str(sessions),
        run="test",
        image_target="4dfp",
        comlogs=str(tmp_path / "comlogs"),
    )
    # `default_options` recodes "" to None, which the file-name builders
    # concatenate; the CLI supplies real empty strings for these
    for name, value in list(options.items()):
        if value is None and ("tail" in name or "variant" in name or "pref" in name):
            options[name] = ""

    sinfo = {
        "id": "s01",
        "data": str(session / "4dfp"),
        "1": {"name": "bold1", "task": "rest", "bold_number": 1},
    }
    return sinfo, options, tmp_path, images


def _links(images):
    """(legacy image, the QuNex name it is linked to), headers included."""
    for folder, names in LEGACY.items():
        for target, name in names.items():
            for ext in (".4dfp.img", ".4dfp.ifh"):
                yield (
                    str(images / folder / (name + ext)),
                    str(images / folder / (target + ext)),
                )


@pytest.mark.parametrize("module, command", COMMANDS)
def test_a_test_run_links_no_legacy_image(legacy, module, command):
    sinfo, options, root, images = legacy
    before = _tree(root)

    report = getattr(module, command)(sinfo, dict(options)).text

    assert _tree(root) == before, "a --test run linked, wrote or removed a file"
    assert "Unknown error" not in report, report
    for source, target in _links(images):
        assert "test, not linked: %s -> %s" % (source, target) in report


def test_the_links_are_noted_once_when_a_command_resolves_the_files_again(legacy):
    """The two segmentation commands resolve them in their check step and again."""
    sinfo, options, root, images = legacy

    report = fs.run_freesurfer_full_segmentation(sinfo, dict(options)).text

    source, target = next(_links(images))
    assert report.count("test, not linked: %s -> %s" % (source, target)) == 1


def test_a_freesurfer_run_the_legacy_images_complete_is_not_planned(legacy):
    """
    Without the links the dry run found no aseg_t1 and planned recon-all, which
    a real run -- linking first -- would not run.
    """
    sinfo, options, root, images = legacy

    report = fs.run_freesurfer_full_segmentation(sinfo, dict(options)).text

    assert "FreeSurfer run already completed!" in report
    assert "recon-all" not in report


def test_the_nuisance_signal_finds_the_segmentation_it_would_link(legacy):
    sinfo, options, root, images = legacy

    report = wf.extract_nuisance_signal(sinfo, dict(options)).text

    assert "freesurfer aseg present" in report
    assert "aseg missing" not in report
    assert "aseg_bold.4dfp.img" in report, "the command names the file it will read"


def test_a_real_run_still_links_the_legacy_images_and_their_headers(legacy):
    """T1_brain and T1_seg used to be linked without their .ifh header."""
    sinfo, options, root, images = legacy
    options = dict(options, run="run")

    pc.get_file_names(sinfo, options)

    for source, target in _links(images):
        assert os.path.samefile(source, target), target


def test_present_answers_for_the_link_a_dry_run_did_not_make(legacy):
    sinfo, options, root, images = legacy

    f = pc.get_file_names(sinfo, options)

    assert not os.path.exists(f["fs_aseg_bold"])
    assert pc.present(f, "fs_aseg_bold", options)
    assert not pc.present(f, "t1", options), "no legacy image stands for it"
    assert not pc.present(f, "fs_aseg_bold", dict(options, image_target="nifti"))


def test_a_real_run_reports_a_link_it_could_not_make(legacy, monkeypatch):
    """
    `present` answered for the legacy image in a real run as well, so a link
    that failed -- a read-only segmentation folder -- read as a file that was
    there: the nuisance signal went on with a segmentation that did not exist,
    and FreeSurfer was skipped as already run. The failure was not said either.
    """
    sinfo, options, root, images = legacy
    options = dict(options, run="run")
    monkeypatch.setattr(pc.gc, "link_or_copy", lambda source, target, **kwargs: False)
    log = gl.ReportLog()

    f = pc.get_file_names(sinfo, options, _log=log)

    assert not os.path.exists(f["fs_aseg_bold"])
    assert not pc.present(f, "fs_aseg_bold", options)
    assert "could not link" in log.text


# ------------------------------------------------------ the environment, gmri


@pytest.fixture
def gmri(monkeypatch, tmp_path):
    """The gmri dispatcher, with this tree's registry and no user settings."""
    monkeypatch.setenv("QUNEXPATH", REPO_ROOT)
    monkeypatch.setattr(
        gls, "USER_SETTINGS_PATHS", [str(tmp_path / "user" / "qunex_settings.yaml")]
    )
    monkeypatch.setattr(glc, "_status_written", False)
    path = os.path.join(REPO_ROOT, "python", "qx_utilities", "gmri")
    loader = importlib.machinery.SourceFileLoader("gmri_side_effects", path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_a_dispatched_dry_run_sets_no_threads_and_makes_no_comlog_folder(
    gmri, tmp_path, monkeypatch
):
    study = tmp_path / "study"
    (study / "sessions" / "S01").mkdir(parents=True)
    (study / ".qunexstudy").write_text("")
    batch = tmp_path / "batch.txt"
    batch.write_text(
        "_sessionsfolder: %s\n---\nid: S01\nsubject: S01\n01: T1w\n"
        % (study / "sessions")
    )
    monkeypatch.delenv("OMP_NUM_THREADS", raising=False)
    environment = dict(os.environ)

    with pytest.raises(gmri.ge.CommandFailed):
        # the session has no data, so the dry run reports it would fail
        gmri.runCommand(
            "hcp_pre_freesurfer", {"batchfile": str(batch), "test": True}
        )

    assert dict(os.environ) == environment
    folders = [os.path.basename(path) for path, _, _ in os.walk(tmp_path)]
    assert "comlogs" not in folders


@pytest.mark.parametrize(
    "command, args, call",
    [
        ("dwi_dtifit", {"sessions": "S01"}, "qx_utilities/dwi_dtifit.sh"),
        ("fc_compute_gbc", {"flist": "a.list"}, "fc_compute_gbc('a.list'"),
    ],
)
def test_a_bash_or_matlab_dry_run_names_its_call_and_makes_none(
    gmri, tmp_path, monkeypatch, command, args, call
):
    """
    gmri handed --test to the script or matlab function, which none of them
    reads, and ran it: `run_qc --test` rendered and copied its QC images, and
    reported the dry run as a completed one.
    """
    study = tmp_path / "study"
    (study / "sessions" / "S01").mkdir(parents=True)
    (study / ".qunexstudy").write_text("")
    status = tmp_path / "status.yaml"

    def no_call(*args, **kwargs):
        raise AssertionError("a --test run executed the command")

    for name in ("run", "call", "check_call", "Popen"):
        monkeypatch.setattr(subprocess, name, no_call)
    monkeypatch.setattr(gmri.gl, "run_and_log", no_call)
    monkeypatch.setattr(gmri.gb, "run", no_call)
    monkeypatch.setattr(gmri.gm, "run", no_call)
    monkeypatch.delenv("OMP_NUM_THREADS", raising=False)
    environment = dict(os.environ)
    before = _tree(study)

    gmri.runCommand(
        command,
        {**args, "studyfolder": str(study), "logstatus": str(status), "test": True},
    )

    assert dict(os.environ) == environment
    # the runlog is written, as for every dry run
    logs = os.path.join(str(study), "logs")
    after = {path: entry for path, entry in _tree(study).items()
             if not path.startswith(logs)}
    assert after == before, "a --test run wrote, removed or replaced a file"
    runlog = ""
    for folder, _, names in os.walk(logs):
        for name in names:
            if name.startswith("Log-"):
                with open(os.path.join(folder, name)) as file:
                    runlog += file.read()
    (line,) = [x for x in runlog.splitlines() if x.startswith("test, not run: ")]
    assert call in line
    assert "--test" not in line, "the line is the one a real run makes"
    record = yaml.safe_load(status.read_text())
    assert record["failed"] == 0
    assert record["sessions"][0]["summary"] == "test, not run"


def test_set_omp_threads_sets_nothing_in_a_dry_run(monkeypatch):
    monkeypatch.delenv("OMP_NUM_THREADS", raising=False)

    assert gcs.set_omp_threads({"run": "test", "omp_threads": "3"}) is None
    assert "OMP_NUM_THREADS" not in os.environ

    assert gcs.set_omp_threads({"run": "run", "omp_threads": "3"}) == 3
    assert os.environ["OMP_NUM_THREADS"] == "3"


# ---------------------------------------------- the extension MATLAB path


class _Command:
    """The registry record of an extension matlab command, as gm.run reads it."""

    name = "example_matlab_greet"
    args = ()
    origin = "extension:example"

    def __init__(self, root):
        self.root = root


def test_the_extension_matlab_path_is_handed_to_the_call(tmp_path, monkeypatch):
    matlab = tmp_path / "qx_example" / "matlab"
    matlab.mkdir(parents=True)
    monkeypatch.setenv("MATLABPATH", "/elsewhere")
    calls = []
    monkeypatch.setattr(gm.gl, "run_and_log", lambda com, name, run=None: calls.append(com) or 0)
    environment = dict(os.environ)

    gm.run(_Command(str(tmp_path / "qx_example")), {})

    assert dict(os.environ) == environment
    assert calls[0].startswith("MATLABPATH=%s:/elsewhere " % matlab)


def test_a_core_matlab_command_is_called_as_it_was(tmp_path, monkeypatch):
    command = _Command(str(tmp_path / "qx_example"))
    command.origin = "core"
    calls = []
    monkeypatch.setattr(gm.gl, "run_and_log", lambda com, name, run=None: calls.append(com) or 0)

    gm.run(command, {})

    assert not calls[0].startswith("MATLABPATH=")
