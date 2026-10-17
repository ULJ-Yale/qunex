#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Installing an extension's own python dependencies.

Offline: the packages are wheels built here, served to pip from a folder, and
the package QuNex "already has" is pytest, which every test run has.
"""

import sys
import zipfile

import pytest

import qx_extension_dependencies as qd
from qx_utilities.general import exceptions as ge

pytest.importorskip("pip")


def _wheel(folder, name, version, requires=()):
    """A minimal pure-python wheel: one module, `VALUE = <version>`."""
    dist = f"{name}-{version}.dist-info"
    files = {
        f"{name}.py": f"VALUE = {version!r}\n",
        f"{dist}/METADATA": f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
        + "".join(f"Requires-Dist: {r}\n" for r in requires),
        f"{dist}/WHEEL": "Wheel-Version: 1.0\nGenerator: qunex-tests\n"
        "Root-Is-Purelib: true\nTag: py3-none-any\n",
    }
    files[f"{dist}/RECORD"] = "".join(f"{f},,\n" for f in files) + f"{dist}/RECORD,,\n"
    with zipfile.ZipFile(folder / f"{name}-{version}-py3-none-any.whl", "w") as z:
        for path, content in files.items():
            z.writestr(path, content)


@pytest.fixture
def index(monkeypatch, tmp_path):
    """A package index pip reads from a folder, and an extensions root."""
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    _wheel(wheels, "qxdep_a", "1.0", ["qxdep_b", "pytest"])
    _wheel(wheels, "qxdep_b", "2.0")
    _wheel(wheels, "qxdep_conflict", "1.0", ["pytest<1"])
    monkeypatch.setenv("PIP_NO_INDEX", "1")
    monkeypatch.setenv("PIP_FIND_LINKS", str(wheels))
    monkeypatch.setenv("PIP_NO_CACHE_DIR", "1")

    root = tmp_path / "extroot"
    root.mkdir()
    for name in ("QUNEXPATH", "TOOLS", "QUNEXEXTENSIONFOLDERS"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("QUNEXEXTENSIONSFOLDERS", str(root))
    return root


def _extension(root, dependencies=None):
    extension = root / "qx_example"
    extension.mkdir()
    if dependencies is not None:
        listed = ", ".join(f'"{d}"' for d in dependencies)
        (extension / "pyproject.toml").write_text(
            f'[project]\nname = "example"\ndependencies = [{listed}]\n', encoding="utf-8"
        )
    return extension


def _folder(extension):
    return extension / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"


def test_only_what_qunex_lacks_is_installed(index):
    extension = _extension(index, ["qxdep_a"])

    installed = qd.install_qx_extension_dependencies(extensions="example")

    assert installed == {"qx_example": ["qxdep_a==1.0", "qxdep_b==2.0"]}
    assert (_folder(extension) / "qxdep_a.py").is_file()
    assert (_folder(extension) / "qxdep_b.py").is_file()
    # pytest is required too, and QuNex has it
    assert not list(_folder(extension).glob("pytest*"))


def test_a_conflict_with_qunex_fails_and_keeps_the_old_folder(index):
    extension = _extension(index, ["qxdep_conflict"])
    _folder(extension).mkdir(parents=True)
    (_folder(extension) / "kept.txt").write_text("", encoding="utf-8")

    with pytest.raises(ge.CommandFailed) as failed:
        qd.install_qx_extension_dependencies(extensions="example")

    assert "pytest<1" in " ".join(failed.value.report)
    assert (_folder(extension) / "kept.txt").is_file()


@pytest.mark.parametrize("dependencies", [None, []])
def test_nothing_declared_touches_nothing(index, dependencies):
    extension = _extension(index, dependencies)

    assert qd.install_qx_extension_dependencies(extensions="all") == {"qx_example": []}
    assert not (extension / "lib").exists()


def test_a_second_run_replaces_the_folder(index):
    extension = _extension(index, ["qxdep_b"])
    qd.install_qx_extension_dependencies(extensions="qx_example")
    (_folder(extension) / "stale.txt").write_text("", encoding="utf-8")

    qd.install_qx_extension_dependencies(extensions="qx_example")

    assert (_folder(extension) / "qxdep_b.py").is_file()
    assert not (_folder(extension) / "stale.txt").exists()
    assert not _folder(extension).with_name(_folder(extension).name + ".new").exists()


def test_a_folder_qunex_makes_redundant_is_removed(index):
    extension = _extension(index, ["pytest"])
    _folder(extension).mkdir(parents=True)

    assert qd.install_qx_extension_dependencies(extensions="example") == {"qx_example": []}
    assert not _folder(extension).exists()


def test_an_extension_has_to_be_named(index):
    with pytest.raises(ge.CommandFailed):
        qd.install_qx_extension_dependencies()


def test_an_unknown_extension_is_reported_by_this_command(index):
    _extension(index, ["qxdep_b"])

    with pytest.raises(ge.CommandFailed) as failed:
        qd.install_qx_extension_dependencies(extensions="nosuch")

    assert failed.value.function == "install_qx_extension_dependencies"
