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

import os
import site
import subprocess
import sys
import zipfile

import pytest

import qx_extension_dependencies as qd
import qx_extension_paths
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
    _wheel(wheels, "qxdep_qunex", "1.0")
    _wheel(wheels, "qxdep_qunex", "2.0")
    _wheel(wheels, "qxdep_needs_old", "1.0", ["qxdep_qunex<2"])
    _wheel(wheels, "qxdep_user", "1.0", ["qxdep_qunex>=2"])
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
    stamp = (_folder(extension) / ".qunex_environment").read_text().strip()
    assert stamp == qx_extension_paths.environment_fingerprint()
    assert (_folder(extension) / "qxdep_a.py").is_file()
    assert (_folder(extension) / "qxdep_b.py").is_file()
    # pytest is required too, and QuNex has it
    assert not list(_folder(extension).glob("pytest*"))


def test_an_unresolvable_dependency_fails_and_keeps_the_old_folder(index):
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


# ==============================================================================
#                      a version QuNex has, replaced for the extension's commands


@pytest.fixture
def qunex_has(index, monkeypatch, tmp_path):
    """
    Make packages part of "QuNex's environment" by installing them into a user
    site of this test's own, which pip counts as installed.
    """
    if not site.ENABLE_USER_SITE:
        pytest.skip("user site packages are disabled for this interpreter")
    monkeypatch.setenv("PYTHONUSERBASE", str(tmp_path / "userbase"))

    def install(*packages):
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "--user", *packages],
            env=env, check=True,
        )

    return install


def test_a_conflicting_version_is_installed_and_reported(index, qunex_has, capsys):
    qunex_has("qxdep_qunex==2.0")
    extension = _extension(index, ["qxdep_needs_old"])

    installed = qd.install_qx_extension_dependencies(extensions="example")

    assert installed == {"qx_example": ["qxdep_needs_old==1.0", "qxdep_qunex==1.0"]}
    assert (_folder(extension) / "qxdep_qunex.py").read_text() == "VALUE = '1.0'\n"
    assert "qxdep_qunex 2.0 -> 1.0" in capsys.readouterr().out


def test_a_replacement_that_breaks_a_qunex_package_fails(index, qunex_has):
    qunex_has("qxdep_qunex==2.0", "qxdep_user==1.0")
    extension = _extension(index, ["qxdep_needs_old"])
    _folder(extension).mkdir(parents=True)
    (_folder(extension) / "kept.txt").write_text("", encoding="utf-8")

    with pytest.raises(ge.CommandFailed) as failed:
        qd.install_qx_extension_dependencies(extensions="example")

    assert "qxdep-user 1.0 has requirement qxdep_qunex>=2" in " ".join(failed.value.report)
    assert (_folder(extension) / "kept.txt").is_file()
    assert not _folder(extension).with_name(_folder(extension).name + ".new").exists()


# ==============================================================================
#                                                           check_qx_extensions


@pytest.fixture
def no_declarations(monkeypatch):
    """No `qx_modules` loaded, whatever the test run imported before."""
    from qx_utilities.general import extensions as qx_extensions

    monkeypatch.setattr(qx_extensions, "module_names", [])
    monkeypatch.setattr(qx_extensions, "modules", {})
    return qx_extensions


def _registered(root, name="qx_example", dependencies=None):
    extension = root / name
    extension.mkdir()
    (extension / "qx_commands.yaml").write_text("version: 1\n", encoding="utf-8")
    if dependencies is not None:
        listed = ", ".join(f'"{d}"' for d in dependencies)
        (extension / "pyproject.toml").write_text(
            f'[project]\nname = "{name}"\ndependencies = [{listed}]\n', encoding="utf-8"
        )
    return extension


def test_a_sound_extension_has_nothing_to_report(index, no_declarations):
    _registered(index, dependencies=["pytest"])

    findings = qd.check_qx_extensions()

    assert findings["qx_example"] == []
    assert findings["across"] == []


def test_a_missing_registry_is_reported(index, no_declarations):
    (index / "qx_example").mkdir()

    findings = qd.check_qx_extensions()["qx_example"]

    assert any("qunex build_qx_extensions --extensions=example" in f for f in findings)


def test_unmet_dependencies_are_reported(index, no_declarations):
    _registered(index, dependencies=["qxdep_absent", "pytest<1"])

    findings = qd.check_qx_extensions()["qx_example"]

    assert any(f.startswith("qxdep_absent is not installed") for f in findings)
    assert any(f.startswith("pytest ") and "'<1'" in f for f in findings)
    assert all("install_qx_extension_dependencies --extensions=example" in f for f in findings)


def test_a_dependency_in_the_package_folder_is_met(index, no_declarations):
    extension = _registered(index, dependencies=["qxdep_b>=2"])
    (_folder(extension) / "qxdep_b-2.0.dist-info").mkdir(parents=True)

    assert qd.check_qx_extensions()["qx_example"] == []


def test_a_folder_for_other_packages_is_reported(index, no_declarations):
    extension = _registered(index)
    _folder(extension).mkdir(parents=True)
    (_folder(extension) / ".qunex_environment").write_text("elsewhere\n", encoding="utf-8")

    findings = qd.check_qx_extensions()["qx_example"]

    assert any("different set of QuNex's packages" in f for f in findings)


def test_clashes_across_extensions_are_reported(index, no_declarations, monkeypatch):
    for name in ("qx_one", "qx_two"):
        extension = _registered(index, name)
        (extension / "python" / "shared").mkdir(parents=True)
        (_folder(extension) / f"qxdep_b-{'1.0' if name == 'qx_one' else '2.0'}.dist-info").mkdir(parents=True)
    for module_name in ("one_parameters", "two_parameters"):
        module = type(sys)(module_name)
        module.arglist = [["same_parameter", "", str, ""]]
        no_declarations.module_names.append(module_name)
        no_declarations.modules[module_name] = module

    across = qd.check_qx_extensions()["across"]

    assert any(f.startswith("'shared' is in qx_one, qx_two") for f in across)
    assert any("'same_parameter' in arglist" in f for f in across)
    assert any(f.startswith("qxdep-b differs") for f in across)
