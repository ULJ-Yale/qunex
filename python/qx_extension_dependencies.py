# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Installs the python packages an extension needs and QuNex does not have, and
checks what the extensions QuNex can see have installed.

An extension's python commands run in the QuNex process, so they can import
what QuNex's environment has and, once one of them is dispatched, what is in
the extension's own package folder (`qx_extension_paths.extension_package_folder`),
which goes in front of QuNex's packages for that command. This fills that
folder, from the dependencies the extension declares in the `pyproject.toml`
at its root.
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
from typing import Dict, List, Optional, Tuple

try:
    from qx_utilities.general import exceptions as ge
except ModuleNotFoundError:
    from general import exceptions as ge
from qx_extension_paths import (
    ENVIRONMENT_STAMP,
    environment_fingerprint,
    extension_folders,
    extension_package_folder,
)
from qx_registry_build import _select_extensions


def install_qx_extension_dependencies(*, extensions: Optional[str] = None) -> Dict[str, List[str]]:
    """
    ``install_qx_extension_dependencies(extensions=None)``

    Install the python packages one or more extensions depend on, into each
    extension's own folder, for the python QuNex runs with.

    An extension declares its dependencies in the ``[project]`` table of a
    ``pyproject.toml`` at its root, as any python project does. They are
    resolved against QuNex's own environment, keeping every package QuNex has
    at the version it has where that works, and the packages QuNex lacks are
    installed into ``<extension>/lib/python<major>.<minor>-<id>``: one folder
    for each QuNex installation that uses the extension, the ``<id>`` standing
    for where its python is installed, so that the host's and a container's
    packages do not overwrite each other.

    Where the extension needs a different version of a package QuNex has -- a
    container's environment is built without knowing the extensions that will
    run in it -- that version is installed into the folder as well, and the
    report lists every such replacement. QuNex puts the folder on the python
    path ahead of its own packages, but only when one of that extension's
    commands runs, each in a process of its own: QuNex's own commands always
    run with QuNex's versions. A replacement that would break a package QuNex
    has, by that package's own requirements, fails the install.

    The packages are installed for the interpreter running this command. Run
    it with each QuNex installation that will run the extension -- inside the
    container too, if the extension is used there. It needs access to the package index pip is configured to use,
    and leaves the previous folder in place if anything fails. Running it again
    replaces the folder.

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
        missing, replaced = _resolve(extension, dependencies, Path(work))

    if not missing:
        print("    QuNex provides every dependency, nothing to install.")
        if folder.exists():
            shutil.rmtree(folder)
            print(f"    Removed the package folder no longer needed: {folder}")
        return []

    _install(extension, missing, folder, check=bool(replaced))
    print(f"    Installed into {folder}, for {sys.executable}:")
    for package in missing:
        print(f"      {package}")
    if replaced:
        print(f"    These replace QuNex's own version, for the commands of {extension.name} only:")
        for package in replaced:
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


def _resolve(extension: Path, dependencies: List[str], work: Path) -> Tuple[List[str], List[str]]:
    """
    The packages to install, as 'name==version', resolved against QuNex, and
    the ones among them that replace a version QuNex has.

    `pip install --target` ignores what is installed and would copy all of
    QuNex's numerical stack into the folder, so the resolution is a dry run in
    QuNex's own environment instead: what it plans to install is exactly what
    QuNex lacks. Pinning every installed package as a constraint makes pip pick
    versions of the new packages that work with QuNex's. Only when that is
    impossible is it run again unpinned, and pip then upgrades just what it
    has to.
    """
    have = {_normalise(p["name"]): p["version"] for p in json.loads(_pip(["list", "--format=json"]))}
    constraints = work / "qunex_constraints.txt"
    constraints.write_text("".join(f"{name}=={version}\n" for name, version in have.items()))
    report = work / "report.json"

    dry_run = ["install", "--dry-run", "--report", str(report)]
    try:
        _pip([*dry_run, "-c", str(constraints), *dependencies])
    except ge.CommandFailed:
        _pip(
            [*dry_run, *dependencies],
            failure=f"The dependencies of {extension.name} can not be resolved",
        )

    # pinned by name and version, so a dependency given as a direct URL would
    # be looked up on the index instead; pass the report's url if one is needed
    planned = [i["metadata"] for i in json.loads(report.read_text())["install"]]
    replaced = [f"{m['name']} {have[_normalise(m['name'])]} -> {m['version']}"
                for m in planned if _normalise(m["name"]) in have]
    return [f"{m['name']}=={m['version']}" for m in planned], replaced


def _install(extension: Path, packages: List[str], folder: Path, *, check: bool) -> None:
    """
    Install into a fresh folder beside the old one, and swap only on success.

    With `check`, the folder replaces some of QuNex's packages, and is kept
    only if QuNex's packages still meet each other's requirements with it in
    front: `pip check` run both ways, so that a problem QuNex's environment
    already has is not blamed on the extension.
    """
    staging = folder.with_name(folder.name + ".new")
    if staging.exists():
        shutil.rmtree(staging)
    try:
        _pip(
            ["install", "--target", str(staging), "--no-deps", *packages],
            failure=f"Installing the dependencies of {extension.name} failed",
        )
        broken = _new_problems(staging) if check else []
        if broken:
            raise ge.CommandFailed(
                'install_qx_extension_dependencies',
                f"The versions {extension.name} needs would break packages QuNex has",
                *broken,
            )
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    # what it was resolved against, for the dispatch to compare with
    (staging / ENVIRONMENT_STAMP).write_text(environment_fingerprint() + "\n")
    if folder.exists():
        shutil.rmtree(folder)
    staging.rename(folder)


def _new_problems(staging: Path) -> List[str]:
    """What `pip check` finds with `staging` in front of QuNex's packages and not without."""
    before = set(_pip(["check"], check=False).splitlines())
    after = _pip(["check"], check=False, pythonpath=staging).splitlines()
    return [line for line in after if line not in before]


def _pip(
    arguments: List[str], *, failure: str = "pip failed", check: bool = True,
    pythonpath: Optional[Path] = None,
) -> str:
    """
    Run pip with this interpreter, seeing QuNex's environment and nothing else.

    `PYTHONPATH` is dropped so that the run sees the installed packages only
    (or set to `pythonpath`, to see a package folder in front of them); the
    rest of the environment is kept, so pip's own configuration -- an index
    mirror, a proxy -- applies.
    """
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    if pythonpath is not None:
        env["PYTHONPATH"] = str(pythonpath)
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    run = subprocess.run(
        [sys.executable, "-m", "pip", *arguments], env=env, capture_output=True, text=True
    )
    if check and run.returncode != 0:
        lines = (run.stdout + run.stderr).strip().splitlines()
        raise ge.CommandFailed('install_qx_extension_dependencies', failure, *lines[-20:])
    return run.stdout


def _normalise(name: str) -> str:
    """A distribution name as pip compares it (PEP 503)."""
    return re.sub(r"[-_.]+", "-", name).lower()


# ==============================================================================
#                                                       checking what is installed

# what an extension may declare in its `qx_modules`, by name: dictionaries whose
# keys, and lists whose entries' first element, must not be claimed twice
_DECLARED_DICTS = ("deprecated_commands", "deprecated_parameters", "deprecated_values", "towarn_parameters")
_DECLARED_LISTS = ("arglist", "flaglist")


def check_qx_extensions(*, extensions: Optional[str] = None) -> Dict[str, List[str]]:
    """
    ``check_qx_extensions(extensions=None)``

    Check the extensions QuNex can see, and report what is wrong or at odds
    with something else, with what to do about each.

    Nothing here is checked when QuNex runs a command, so that a clash costs
    nothing until somebody asks; run this after installing or updating an
    extension, or when an extension's command fails in a way that does not
    explain itself. It reports:

    - problems ``pip check`` finds among QuNex's own python packages;
    - for each extension: a missing command registry; a declared dependency
      that is missing or at a version it does not accept; a package folder
      installed for a different set of QuNex's packages than the ones here;
      the QuNex packages it replaces for its own commands, and whether that
      replacement breaks another of QuNex's packages;
    - across extensions: a python module or package of the same name in more
      than one extension, of which only one can be imported; a parameter or
      deprecation declared by more than one extension; the same package at
      different versions in two extensions' package folders.

    It changes nothing, and completes whatever it finds.

    ..  qx_command:
        type: utility

    Parameters:
        --extensions (str, default ''):
            Which extensions to check, as a comma separated list of names given
            with or without the ``qx_`` prefix. 'all' checks every extension
            found, and so does leaving it out.

    Returns:
        --findings (dict):
            The problems found, as lists of messages under 'qunex', under each
            extension's folder name, and under 'across'. Empty lists when there
            is nothing to report.
    """
    folders = _select_extensions(extensions, extension_folders(), 'check_qx_extensions')
    findings = {}

    print("\n--> QuNex's python packages")
    findings["qunex"] = _print_findings(_pip(["check"], check=False).splitlines())

    for extension in folders:
        print(f"\n--> {extension.name}: {extension}")
        findings[extension.name] = _print_findings(_check_extension(extension))

    print("\n--> Across extensions")
    findings["across"] = _print_findings(_check_across(folders))
    return findings


def _print_findings(findings: List[str]) -> List[str]:
    for finding in findings or ["nothing to report"]:
        print(f"    {finding}")
    return findings


def _check_extension(extension: Path) -> List[str]:
    name = extension.name[len("qx_"):]
    install = f"run: qunex install_qx_extension_dependencies --extensions={name}"
    findings = []

    if not (extension / "qx_commands.yaml").is_file():
        findings.append(f"no command registry; run: qunex build_qx_extensions --extensions={name}")

    folder = extension_package_folder(extension)
    in_folder = _folder_versions(folder)
    for requirement in _declared_dependencies(extension):
        problem = _unmet(requirement, in_folder)
        if problem:
            findings.append(f"{problem}; {install}")

    others = sorted(d.name for d in (extension / "lib").glob("python*")
                    if d.is_dir() and d != folder and not d.name.endswith(".new"))
    if others:
        print(f"    also holds packages for other python installations: {', '.join(others)}")

    stamp = folder / ENVIRONMENT_STAMP
    if stamp.is_file() and stamp.read_text().strip() != environment_fingerprint():
        findings.append(f"its packages were installed for a different set of QuNex's packages; {install}")

    replaced = [f"{package} {_installed_version(package)} -> {version}"
                for package, version in in_folder.items() if _installed_version(package)]
    if replaced:
        print(f"    replaces, for its own commands: {', '.join(replaced)}")
        findings += [f"with its packages in front: {p}; {install}" for p in _new_problems(folder)]
    return findings


def _check_across(folders: List[Path]) -> List[str]:
    findings = []

    owners: Dict[str, List[str]] = {}
    for extension in folders:
        python = extension / "python"
        for entry in sorted(python.iterdir()) if python.is_dir() else []:
            importable = entry.is_dir() or entry.suffix == ".py"
            if importable and not entry.name.startswith(("_", ".")):
                owners.setdefault(entry.stem, []).append(extension.name)
    findings += [f"'{module}' is in {', '.join(names)}; only one of them can be imported, rename the others"
                 for module, names in owners.items() if len(names) > 1]

    findings += _declaration_clashes()

    versions: Dict[str, Dict[str, str]] = {}
    for extension in folders:
        for package, version in _folder_versions(extension_package_folder(extension)).items():
            versions.setdefault(package, {})[extension.name] = version
    findings += [f"{package} differs between extensions ({', '.join(f'{e} {v}' for e, v in by.items())}); "
                 f"a process running commands of both imports only one"
                 for package, by in versions.items() if len(set(by.values())) > 1]
    return findings


def _declaration_clashes() -> List[str]:
    """Keys of `_DECLARED_DICTS` and names in `_DECLARED_LISTS` claimed by more than one module."""
    from qx_utilities.general import extensions as qx_extensions

    claims: Dict[tuple, List[str]] = {}
    for module_name in qx_extensions.module_names:
        module = qx_extensions.modules[module_name]
        keys = set()
        for declared in _DECLARED_DICTS:
            keys |= {(declared, key) for key in getattr(module, declared, None) or {}}
        for declared in _DECLARED_LISTS:
            keys |= {(declared, entry[0]) for entry in getattr(module, declared, None) or [] if entry}
        for key in keys:
            claims.setdefault(key, []).append(module_name)
    return [f"'{key}' in {declared} is declared by {', '.join(modules)}; only one declaration is used"
            for (declared, key), modules in sorted(claims.items(), key=str) if len(modules) > 1]


def _unmet(requirement: str, in_folder: Dict[str, str]) -> Optional[str]:
    """Why a declared requirement is not met here, or None when it is."""
    from packaging.requirements import InvalidRequirement, Requirement

    try:
        parsed = Requirement(requirement)
    except InvalidRequirement:
        return f"'{requirement}' in pyproject.toml can not be read"
    if parsed.marker is not None and not parsed.marker.evaluate():
        return None
    version = in_folder.get(_normalise(parsed.name)) or _installed_version(parsed.name)
    if version is None:
        return f"{parsed.name} is not installed"
    if not parsed.specifier.contains(version, prereleases=True):
        return f"{parsed.name} {version} does not meet '{parsed.specifier}'"
    return None


def _folder_versions(folder: Path) -> Dict[str, str]:
    """The packages in a package folder, by normalised name, from their `.dist-info` folders."""
    versions = {}
    for dist_info in folder.glob("*.dist-info") if folder.is_dir() else []:
        name, version = dist_info.name[: -len(".dist-info")].rsplit("-", 1)
        versions[_normalise(name)] = version
    return versions


def _installed_version(package: str) -> Optional[str]:
    """The version of a package QuNex has, or None. Seen from a core command, so no extension's folder is in it."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version(package)
    except PackageNotFoundError:
        return None
