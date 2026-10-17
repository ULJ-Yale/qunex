# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Installs the python packages an extension needs and QuNex does not have.

An extension's python commands run in the QuNex process, so they can import
what QuNex's environment has and, once one of them is dispatched, what is in
the extension's own package folder (`qx_extension_paths.extension_package_folder`).
This fills that folder, from the dependencies the extension declares in the
`pyproject.toml` at its root.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Dict, List, Optional

try:
    from qx_utilities.general import exceptions as ge
except ModuleNotFoundError:
    from general import exceptions as ge
from qx_extension_paths import extension_folders, extension_package_folder
from qx_registry_build import _select_extensions


def install_qx_extension_dependencies(*, extensions: Optional[str] = None) -> Dict[str, List[str]]:
    """
    ``install_qx_extension_dependencies(extensions=None)``

    Install the python packages one or more extensions depend on, into each
    extension's own folder, for the python QuNex runs with.

    An extension declares its dependencies in the ``[project]`` table of a
    ``pyproject.toml`` at its root, as any python project does. They are
    resolved against QuNex's own environment, with every package QuNex has
    held at the version it has, and only the packages QuNex does not have are
    installed, into ``<extension>/lib/python<major>.<minor>``. QuNex puts that
    folder on the python path, after its own packages, when one of the
    extension's commands runs.

    So an extension can add packages but never replace one QuNex depends on. A
    dependency that needs a different version of a package QuNex has fails
    here, with pip's account of the conflict, rather than at run time.

    The packages are installed for the interpreter running this command, and
    the folder is named after its version. Run it with the QuNex installation
    that will run the extension -- inside the container, if the extension is
    used there and the container's python differs from the host's. It needs
    access to the package index pip is configured to use, and leaves the
    previous folder in place if anything fails. Running it again replaces the
    folder.

    ..  qx_command:
        type: utility

    Parameters:
        --extensions (str, default ''):
            Which extensions to install the dependencies of, as a comma
            separated list of names given with or without the ``qx_`` prefix.
            'all' covers every extension found.

    Returns:
        --installed (dict):
            For each extension covered, the packages installed into its folder,
            as 'name==version' strings. Empty when it declares no dependencies
            or QuNex has them all.
    """
    if not (extensions or "").strip():
        raise ge.CommandFailed(
            'install_qx_extension_dependencies',
            "No extensions named",
            "Name one or more with --extensions=<name>, or --extensions=all for all of them.",
        )

    installed = {}
    for extension in _select_extensions(
        extensions, extension_folders(), 'install_qx_extension_dependencies'
    ):
        installed[extension.name] = _install_for(extension)
    return installed


def _install_for(extension: Path) -> List[str]:
    print(f"\n--> {extension.name}: {extension}")

    dependencies = _declared_dependencies(extension)
    if not dependencies:
        print("    No dependencies declared in pyproject.toml, nothing to install.")
        return []

    folder = extension_package_folder(extension)
    with tempfile.TemporaryDirectory() as work:
        missing = _resolve(extension, dependencies, Path(work))

    if not missing:
        print("    QuNex provides every dependency, nothing to install.")
        if folder.exists():
            shutil.rmtree(folder)
            print(f"    Removed the package folder no longer needed: {folder}")
        return []

    _install(extension, missing, folder)
    print(f"    Installed into {folder}:")
    for package in missing:
        print(f"      {package}")
    return missing


def _declared_dependencies(extension: Path) -> List[str]:
    """`[project].dependencies` of the extension's `pyproject.toml`, if it has one."""
    pyproject = extension / "pyproject.toml"
    if not pyproject.is_file():
        return []
    try:
        with open(pyproject, "rb") as f:
            project = tomllib.load(f).get("project", {})
    except tomllib.TOMLDecodeError as e:
        raise ge.CommandFailed(
            'install_qx_extension_dependencies', f"Could not read {pyproject}", str(e)
        ) from e
    return list(project.get("dependencies", []))


def _resolve(extension: Path, dependencies: List[str], work: Path) -> List[str]:
    """
    The packages to install, as 'name==version', resolved against QuNex.

    `pip install --target` ignores what is installed and would copy all of
    QuNex's numerical stack into the folder, so the resolution is a dry run in
    QuNex's own environment instead: what it plans to install is exactly what
    QuNex lacks. Pinning every installed package as a constraint makes pip pick
    versions of the new packages that work with QuNex's, rather than plan an
    upgrade of one of QuNex's.
    """
    have = {_normalise(p["name"]): p["version"] for p in json.loads(_pip(["list", "--format=json"]))}
    constraints = work / "qunex_constraints.txt"
    constraints.write_text("".join(f"{name}=={version}\n" for name, version in have.items()))
    report = work / "report.json"

    _pip(
        ["install", "--dry-run", "--report", str(report), "-c", str(constraints), *dependencies],
        failure=f"The dependencies of {extension.name} can not be installed alongside QuNex's packages",
    )

    # pinned by name and version, so a dependency given as a direct URL would
    # be looked up on the index instead; pass the report's url if one is needed
    planned = [i["metadata"] for i in json.loads(report.read_text())["install"]]
    replaced = [f"{m['name']} {have[_normalise(m['name'])]} -> {m['version']}"
                for m in planned if _normalise(m["name"]) in have]
    if replaced:
        raise ge.CommandFailed(
            'install_qx_extension_dependencies',
            f"The dependencies of {extension.name} would replace packages QuNex depends on",
            *replaced,
        )
    return [f"{m['name']}=={m['version']}" for m in planned]


def _install(extension: Path, packages: List[str], folder: Path) -> None:
    """Install into a fresh folder beside the old one, and swap only on success."""
    staging = folder.with_name(folder.name + ".new")
    if staging.exists():
        shutil.rmtree(staging)
    try:
        _pip(
            ["install", "--target", str(staging), "--no-deps", *packages],
            failure=f"Installing the dependencies of {extension.name} failed",
        )
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    if folder.exists():
        shutil.rmtree(folder)
    staging.rename(folder)


def _pip(arguments: List[str], *, failure: str = "pip failed") -> str:
    """
    Run pip with this interpreter, seeing QuNex's environment and nothing else.

    `PYTHONPATH` is dropped so that the run sees the installed packages only;
    the rest of the environment is kept, so pip's own configuration -- an index
    mirror, a proxy -- applies.
    """
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    run = subprocess.run(
        [sys.executable, "-m", "pip", *arguments], env=env, capture_output=True, text=True
    )
    if run.returncode != 0:
        lines = (run.stdout + run.stderr).strip().splitlines()
        raise ge.CommandFailed('install_qx_extension_dependencies', failure, *lines[-20:])
    return run.stdout


def _normalise(name: str) -> str:
    """A distribution name as pip compares it (PEP 503)."""
    return re.sub(r"[-_.]+", "-", name).lower()
