#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Where a registry is about to be written, checked before it is.

Two conditions, and they are not the same. A location that cannot be written is
an error, and happens inside a container whose image is read only just as much
as outside one on an installation somebody has no write access to. A location
that can be written but sits on the container image is a warning: the registry
is there until the container exits and no longer.

The container is not available to the suite, so the two lookups take their input
explicitly and the tests hand them fixtures.
"""

import os
from pathlib import Path

import pytest

import qx_registry_build as qb
from qx_utilities.general import exceptions as ge


# `/proc/self/mountinfo` as a container gives it: the image at `/`, a folder
# bound in from the host, and scratch. Taken from qunex_suite-latest.sif.
MOUNTINFO = """\
1637 1259 0:76 / / rw,nodev,relatime unbindable - overlay overlay ro,lowerdir=/var/lib/apptainer/mnt/session/overlay-lowerdir
1688 1637 252:1 /opt/software/qunexfeatures/88-extensions-cleanup /opt/qunex rw,nosuid,nodev,relatime master:1151 - ext4 /dev/mapper/ubuntu--vg-ubuntu--lv rw
1699 1637 0:77 / /tmp rw,nosuid,nodev,relatime - tmpfs tmpfs rw,size=8192000k
"""


def _obj():
    """The smallest thing `write_registry_file` will serialise."""
    return {"version": 1, "generated_at": "2026-01-01T00:00:00Z",
            "source": {"id": "core"}, "commands": []}


# ==============================================================================
#                                                          reading the mounts


def test_the_image_root_does_not_persist():
    assert not qb.writes_persist(Path("/opt/qunex_other/qx_commands.yaml"), MOUNTINFO)


def test_a_bound_folder_persists():
    assert qb.writes_persist(Path("/opt/qunex/qx_commands.yaml"), MOUNTINFO)


def test_tmp_does_not_persist():
    """
    The reason the filesystem type is read rather than just the mount point.
    `/tmp` is writable and is its own mount, so a check that stopped at the
    mount point would call it persistent -- and it is where somebody trying an
    extension inside a container puts it.
    """
    assert not qb.writes_persist(Path("/tmp/extroot/qx_one/qx_commands.yaml"), MOUNTINFO)


def test_the_deepest_mount_decides():
    """`/opt/qunex` is under `/`, and it is the longer match that answers."""
    assert qb.writes_persist(Path("/opt/qunex/deeply/nested/qx_commands.yaml"), MOUNTINFO)


def test_no_mount_table_does_not_warn():
    """Nothing established is not the same as something wrong."""
    assert qb.writes_persist(Path("/anywhere/qx_commands.yaml"), "")


def test_a_mount_table_that_makes_no_sense_is_ignored():
    assert qb.writes_persist(Path("/opt/qunex/qx_commands.yaml"), "nonsense\nlines\n")


# ==============================================================================
#                                                       knowing it is a container


def test_the_marker_file_says_so(tmp_path):
    marker = tmp_path / ".container"
    marker.write_text("")

    assert qb.in_container(marker)


def test_without_a_marker_the_apptainer_variable_still_says_so(tmp_path, monkeypatch):
    monkeypatch.setenv("APPTAINER_CONTAINER", "/path/to/qunex_suite.sif")

    assert qb.in_container(tmp_path / "absent")


def test_neither_is_not_a_container(tmp_path, monkeypatch):
    for name in ("APPTAINER_CONTAINER", "SINGULARITY_CONTAINER"):
        monkeypatch.delenv(name, raising=False)

    assert not qb.in_container(tmp_path / "absent")


# ==============================================================================
#                                                            writing, or not


@pytest.fixture
def not_a_container(monkeypatch):
    monkeypatch.setattr(qb, "in_container", lambda *a, **kw: False)


def test_a_writable_location_is_written(not_a_container, tmp_path):
    out = tmp_path / "qx_commands.yaml"

    qb.write_registry_file(out, _obj())

    assert out.exists()


def test_an_unwritable_folder_names_the_path_and_the_way_out(not_a_container, tmp_path):
    folder = tmp_path / "install"
    folder.mkdir()
    os.chmod(folder, 0o555)
    try:
        with pytest.raises(ge.CommandFailed) as raised:
            qb.write_registry_file(folder / "qx_commands.yaml", _obj(), source_id="core")
    finally:
        os.chmod(folder, 0o755)

    reported = "\n".join(raised.value.report)
    assert str(folder) in reported
    # the whole point: the user is told what to run instead
    assert "build_qx_extensions" in reported


def test_an_extension_is_told_it_has_to_live_somewhere_writable(not_a_container, tmp_path):
    folder = tmp_path / "qx_one"
    folder.mkdir()
    os.chmod(folder, 0o555)
    try:
        with pytest.raises(ge.CommandFailed) as raised:
            qb.write_registry_file(
                folder / "qx_commands.yaml", _obj(), source_id="extension:one"
            )
    finally:
        os.chmod(folder, 0o755)

    reported = "\n".join(raised.value.report)
    assert "build_qx_extensions" not in reported, "that is the core registry's advice"
    assert "bind" in reported.lower()


def test_an_unwritable_location_with_nothing_to_write_is_not_an_error(
    not_a_container, tmp_path
):
    """
    The case that must stay silent. An extension shipped inside a container
    image with its registry already built rebuilds cleanly, because there is
    nothing to write -- and rebuilding to see what happens is the first thing
    anybody does. A check hoisted above the comparison would fail it.
    """
    folder = tmp_path / "install"
    folder.mkdir()
    out = folder / "qx_commands.yaml"
    qb.write_registry_file(out, _obj())
    before = out.read_text()

    os.chmod(folder, 0o555)
    os.chmod(out, 0o444)
    try:
        qb.write_registry_file(out, _obj())
    finally:
        os.chmod(folder, 0o755)
        os.chmod(out, 0o644)

    assert out.read_text() == before


def test_only_the_timestamp_moving_still_counts_as_nothing_to_write(
    not_a_container, tmp_path
):
    """`generated_at` differs on every build and is not a reason to write."""
    folder = tmp_path / "install"
    folder.mkdir()
    out = folder / "qx_commands.yaml"
    qb.write_registry_file(out, _obj())

    later = _obj()
    later["generated_at"] = "2026-09-05T18:00:00Z"

    os.chmod(folder, 0o555)
    os.chmod(out, 0o444)
    try:
        qb.write_registry_file(out, later)
    finally:
        os.chmod(folder, 0o755)
        os.chmod(out, 0o644)

    assert "2026-01-01" in out.read_text(), "the committed file was left as it stands"


# ==============================================================================
#                                                     and the warning with it


def test_a_write_onto_the_container_image_warns_and_still_writes(tmp_path, monkeypatch):
    out = tmp_path / "qx_commands.yaml"
    monkeypatch.setattr(qb, "in_container", lambda *a, **kw: True)
    monkeypatch.setattr(qb, "writes_persist", lambda *a, **kw: False)
    qb._WARNINGS.clear()

    qb.write_registry_file(out, _obj())

    assert out.exists(), "a warning is not a refusal"
    assert any("gone when the container exits" in w for w in qb._WARNINGS)


def test_a_write_onto_a_bound_folder_does_not_warn(tmp_path, monkeypatch):
    out = tmp_path / "qx_commands.yaml"
    monkeypatch.setattr(qb, "in_container", lambda *a, **kw: True)
    monkeypatch.setattr(qb, "writes_persist", lambda *a, **kw: True)
    qb._WARNINGS.clear()

    qb.write_registry_file(out, _obj())

    assert qb._WARNINGS == []


def test_outside_a_container_the_mounts_do_not_matter(tmp_path, monkeypatch):
    """A laptop's `/tmp` is not a container's, and is nobody's problem here."""
    out = tmp_path / "qx_commands.yaml"
    monkeypatch.setattr(qb, "in_container", lambda *a, **kw: False)
    monkeypatch.setattr(qb, "writes_persist", lambda *a, **kw: False)
    qb._WARNINGS.clear()

    qb.write_registry_file(out, _obj())

    assert qb._WARNINGS == []
