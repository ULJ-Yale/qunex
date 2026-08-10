#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Two commands that read a file and did nothing useful with what they read.

Both defects were found by a live check and both were invisible: an exception
swallowed by a bare ``except``, and a return value unpacked one level short.
The tests pin the *reading*, which is all either fix is about -- neither
command's real work (4dfp preprocessing, an approved de-identification
specification) can run in the test environment.

- ``deid_discover.read_dicom_full`` called ``pydicom.filereader.read_file``,
  removed in pydicom 3, so every DICOM came back as "not a dicom" and
  ``change_dicom_files`` de-identified nothing while exiting 0 (OI-25).
- ``fourdfp.run_nil`` read ``read_session_data``'s ``(sessions, gpref)`` pair
  into one name, so ``info[0]`` was a list and the walk over it raised on every
  session (OI-24).
- ``deid_discover.discover_dicom``'s zip and tar branches wrapped the
  extraction, the recursion *and* the re-archiving in the same
  ``except Exception: pass`` that asked "is this an archive?", so a package that
  was de-identified and then failed to be written back was reported as "not a
  dicom file" and exited 0 (OI-26).
"""

import os
import tarfile
import zipfile

import pytest

pydicom = pytest.importorskip("pydicom")

import qx_utilities.general.log as gl  # noqa: E402
from qx_utilities.dicom.deid_discover import (  # noqa: E402
    discover_dicom,
    read_dicom_base,
    read_dicom_full,
)
from qx_utilities.general.fourdfp import run_nil  # noqa: E402


def _write_dicom(path):
    """A minimal but genuinely readable DICOM file."""
    from pydicom.dataset import Dataset, FileMetaDataset
    from pydicom.uid import ExplicitVRLittleEndian, generate_uid

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.ImplementationClassUID = generate_uid()

    d = Dataset()
    d.file_meta = meta
    d.SOPClassUID = meta.MediaStorageSOPClassUID
    d.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    d.SeriesInstanceUID = generate_uid()
    d.StudyInstanceUID = generate_uid()
    d.PatientName = "TEST^SUBJECT"
    d.PatientID = "OP999"
    d.StudyDate = "20260809"
    d.Modality = "MR"
    d.SeriesNumber = 1
    d.SeriesDescription = "T1w_MPR"
    d.Rows, d.Columns = 4, 4
    d.BitsAllocated, d.BitsStored, d.HighBit = 16, 16, 15
    d.PixelRepresentation, d.SamplesPerPixel = 0, 1
    d.PhotometricInterpretation = "MONOCHROME2"
    d.PixelData = bytes(32)
    d.save_as(str(path), enforce_file_format=True)
    return path


def test_read_dicom_full_reads_a_dicom(tmp_path):
    """The de-identification path opens a DICOM, rather than reporting none."""
    path = _write_dicom(tmp_path / "one.dcm")

    dataset, gz = read_dicom_full(str(path))

    assert dataset is not None, "read_dicom_full saw a DICOM as 'not a dicom'"
    assert gz is False
    assert str(dataset.PatientName) == "TEST^SUBJECT"


def test_the_two_readers_agree_on_what_is_a_dicom(tmp_path):
    """`save=True` and `save=False` walk the same files, so they must agree."""
    dicom = _write_dicom(tmp_path / "one.dcm")
    plain = tmp_path / "readme.txt"
    plain.write_text("not a dicom")

    assert read_dicom_full(str(dicom))[0] is not None
    assert read_dicom_base(str(dicom))[0] is not None
    assert read_dicom_full(str(plain))[0] is None
    assert read_dicom_base(str(plain))[0] is None


def _zip_of_one_dicom(tmp_path, name="pkg.zip"):
    """A folder holding a single zip archive with one DICOM inside it."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    member = _write_dicom(tmp_path / "member.dcm")

    with zipfile.ZipFile(inbox / name, mode="w") as z:
        z.write(str(member), "member.dcm")

    return inbox


def _keep(dataset, filename=None):
    """A de-identification callback that changes nothing."""
    return dataset


def test_a_package_that_cannot_be_written_back_is_an_error(tmp_path):
    """
    A zip that extracted and de-identified but failed to re-archive is reported.

    The failure is forced by putting a directory where the output archive has
    to be written. Before the fix the extraction, the recursion and the
    re-archiving all sat inside the ``except Exception: pass`` that asked
    whether the file was a zip at all, so this run recorded nothing, wrote
    nothing and exited 0 (OI-26).
    """
    inbox = _zip_of_one_dicom(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    (out / "pkg.deid.zip").mkdir()  # the target the re-zip has to write

    log = gl.ReportLog()
    discover_dicom(
        str(inbox),
        _keep,
        output_folder=str(out),
        rename_files=False,
        extension="deid",
        save=True,
        archive_file=str(tmp_path / "archive.csv"),
        _log=log,
    )

    assert log.has_errors, "a package that could not be written back reported success"
    assert "failed to process zip archive" in log.text
    assert "not a dicom file" not in log.text, (
        "a zip that opened is still being reported as 'not a dicom file'"
    )


def test_a_package_that_is_written_back_is_quiet(tmp_path):
    """The same walk, succeeding: an archive out, and nothing recorded."""
    inbox = _zip_of_one_dicom(tmp_path)
    out = tmp_path / "out"
    out.mkdir()

    log = gl.ReportLog()
    discover_dicom(
        str(inbox),
        _keep,
        output_folder=str(out),
        rename_files=False,
        extension="deid",
        save=True,
        archive_file=str(tmp_path / "archive.csv"),
        _log=log,
    )

    assert not log.has_errors, log.text
    written = out / "pkg.deid.zip"
    assert written.is_file(), "the de-identified package was never written back"
    with zipfile.ZipFile(written) as z:
        assert z.namelist() == ["member.dcm"]


@pytest.mark.parametrize(
    "name, expect_compression",
    [
        ("pkg.tar", None),
        ("pkg.tar.gz", "gz"),
        ("pkg.tgz", "gz"),
        ("pkg.tar.bz2", "bz2"),
    ],
)
def test_a_tar_package_keeps_its_compression(
    tmp_path, monkeypatch, name, expect_compression
):
    """
    A compressed tar goes back out compressed, not renamed and left plain.

    The write mode used to be derived from the read handle's ``.mode``, which
    ``TarFile.__init__`` reduces to a single character -- so it was ``"r"`` for
    every archive and the write mode was always plain ``"w"``. A ``.tar.gz``
    came back out as an uncompressed POSIX tar still called ``.tar.gz``
    (OI-27).
    """
    # `tarfile.gettarinfo` resolves uid -> uname and gid -> gname for every
    # member added. where those ids are not in the local passwd/group files the
    # lookups go to a directory service and time out -- three seconds per file,
    # for names that then come back empty anyway. tarfile skips both when the
    # modules are absent, which is the same empty result without the wait
    monkeypatch.setattr(tarfile, "pwd", None)
    monkeypatch.setattr(tarfile, "grp", None)

    inbox = tmp_path / "inbox"
    inbox.mkdir()
    member = _write_dicom(tmp_path / "member.dcm")

    write_mode = {"gz": "w:gz", "bz2": "w:bz2", None: "w"}[expect_compression]
    with tarfile.open(inbox / name, write_mode) as t:
        t.add(str(member), "member.dcm")

    out = tmp_path / "out"
    out.mkdir()

    log = gl.ReportLog()
    discover_dicom(
        str(inbox),
        _keep,
        output_folder=str(out),
        rename_files=False,
        extension="deid",
        save=True,
        archive_file=str(tmp_path / "archive.csv"),
        _log=log,
    )

    assert not log.has_errors, log.text
    written = next(out.iterdir())
    assert written.name.endswith(name.replace("pkg", "pkg.deid"))

    head = written.read_bytes()[:3]
    if expect_compression == "gz":
        assert head[:2] == b"\x1f\x8b", "a gzipped tar came back out uncompressed"
    elif expect_compression == "bz2":
        assert head == b"BZh", "a bzip2 tar came back out uncompressed"
    else:
        assert head[:2] != b"\x1f\x8b"

    # and it is still a readable tar holding the member
    with tarfile.open(written) as t:
        assert t.getnames() == ["member.dcm"]


def test_a_file_that_is_no_kind_of_archive_is_still_skipped_quietly(tmp_path):
    """Narrowing the guard must not turn every stray file into an error."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "readme.txt").write_text("not a dicom, not an archive")

    log = gl.ReportLog()
    discover_dicom(str(inbox), _keep, _log=log)

    assert not log.has_errors, log.text
    assert "not a dicom file" in log.text


def test_run_nil_reads_the_session_it_is_given(tmp_path):
    """
    `run_nil` gets past the session file and writes the params from it.

    NIL preprocessing itself needs 4dfp tooling that is not in this
    environment, so the run fails at the external call -- after the params
    file, which is what this asserts. Before the fix it raised
    ``'list' object has no attribute 'items'`` and no params file was written.
    """
    session = tmp_path / "OP111"
    (session / "dicom").mkdir(parents=True)
    (session / "nii").mkdir()
    (session / "session.txt").write_text(
        "id: OP111\n"
        "subject: OP111\n"
        "raw_data: %s\n"
        "data: %s\n"
        "\n"
        "10: T1w\n"
        "20: bold1:rest\n" % (session / "nii", session / "4dfp")
    )
    (session / "dicom" / "DICOM-Report.txt").write_text(
        "  20     2   BOLD   4  [TR 2000.00, TE  30.00]\n"
    )

    try:
        run_nil(folder=str(session))
    except Exception as e:  # the external 4dfp tool is not installed here
        assert "has no attribute 'items'" not in str(e), (
            "run_nil is still unpacking read_session_data's (sessions, gpref) "
            "pair into a single name"
        )

    params = session / "4dfp" / "params"
    assert params.exists(), "run_nil never reached the params file"
    body = params.read_text()
    assert "set patid  = OP111" in body
    assert "set mprs   = ( 10-o.nii.gz )" in body  # the T1w entry
    assert "set fstd   = ( 20.nii.gz )" in body  # the bold entry
    assert "set TR_vol = 2.0" in body  # read from DICOM-Report.txt


def test_run_nil_raises_when_the_session_file_is_empty(tmp_path):
    """An unreadable session file is still a failure, not a crash in the walk."""
    session = tmp_path / "OP112"
    session.mkdir()
    (session / "session.txt").write_text("# nothing here\n")

    with pytest.raises(Exception):
        run_nil(folder=str(session))

    assert not os.path.exists(session / "4dfp" / "params")
