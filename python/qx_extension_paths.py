# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Where QuNex looks for extensions.

A leaf: it imports nothing from QuNex, and both halves that need the answer
import it. `qx_registry` asks so that it can find each extension's registry;
`general/extensions.py` asks so that it can put each extension's python folder
on `sys.path`. The second of those runs while `qx_registry` is still being
imported -- `general/__init__.py` loads the extensions as it is read -- so the
two cannot ask each other, and neither should hold its own copy of the answer:
one variable spelled two ways is the defect this file exists to prevent.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, List


# The variable naming the folders QuNex searches for extensions. It was spelled
# with the second S in the shell and without it in python, so a root named in
# only one of them was half integrated -- it got PATH, MATLABPATH and
# QXEXTENSIONSPY but no registry, or a registry whose commands could not import.
# The shell's spelling is canonical; the other is still read, with a notice, for
# installations that set it.
EXTENSION_FOLDERS_ENV = "QUNEXEXTENSIONSFOLDERS"
EXTENSION_FOLDERS_ENV_DEPRECATED = "QUNEXEXTENSIONFOLDERS"

_warned: set = set()


def _warn(message: str) -> None:
    """
    One warning line, once per process, on stderr.

    Never on stdout: `bin/qunex.sh` reads `gmri -available` as its routing table,
    so anything printed there is taken for a command name.
    """
    if message not in _warned:
        _warned.add(message)
        print(f"WARNING: {message}", file=sys.stderr)


def _split_env_path_list(value: str) -> List[str]:
    value = (value or "").strip()
    if not value:
        return []
    value = value.replace(";", ":")
    return [p.strip() for p in value.split(":") if p.strip()]


def extension_search_roots() -> List[Path]:
    roots: List[Path] = []

    qunexpath = os.environ.get("QUNEXPATH", "").strip()
    if qunexpath:
        roots.append(Path(qunexpath) / "qx_extensions")

    tools = os.environ.get("TOOLS", "").strip()
    if tools:
        roots.append(Path(tools) / "qx_extensions")

    named = _split_env_path_list(os.environ.get(EXTENSION_FOLDERS_ENV, ""))
    deprecated = _split_env_path_list(os.environ.get(EXTENSION_FOLDERS_ENV_DEPRECATED, ""))

    if deprecated:
        _warn(
            f"{EXTENSION_FOLDERS_ENV_DEPRECATED} is deprecated and will be removed in a "
            f"future release. Please name the extension folders in "
            f"{EXTENSION_FOLDERS_ENV} instead."
        )

    # a folder somebody named and QuNex cannot use is worth a line: the two fixed
    # roots above are absent on most installations and are passed over in silence
    for folder in named + deprecated:
        path = Path(folder).expanduser()
        if not path.is_dir():
            _warn(f"extensions folder '{folder}' does not exist or is not a folder, skipping it.")
            continue
        roots.append(path)

    # de-dup preserving order
    seen = set()
    uniq: List[Path] = []
    for r in roots:
        rr = r.expanduser()
        try:
            rr = rr.resolve()
        except Exception:
            pass
        s = str(rr)
        if s not in seen:
            seen.add(s)
            uniq.append(rr)
    return uniq


def extension_folders() -> List[Path]:
    """
    Every extension QuNex can see, as its own `qx_<name>` folder.

    An extension found under more than one root is taken from the last of them,
    which is how the registry resolves it too -- so the code that runs and the
    folders set up for it are always the same copy.
    """
    found: Dict[str, Path] = {}

    for root in extension_search_roots():
        if not root.is_dir():
            continue
        for extension in sorted(root.iterdir()):
            if extension.is_dir() and extension.name.startswith("qx_"):
                found[extension.name] = extension

    return [found[name] for name in sorted(found)]


def extension_python_folders() -> List[str]:
    """
    The python folder of every extension QuNex can see.

    Taken from `extension_folders()` alone, so the folder on `sys.path` belongs
    to the copy the registry was read from. The environment script's
    `QXEXTENSIONSPY` is not read: it lists the copies found when the
    environment was sourced, and with a root named since then it put the
    overridden copy ahead of the winning one, so a command was listed from one
    copy and imported from another. The search roots are read on every run and
    cover what it did, including an extension installed after a container
    started.
    """
    return [
        str(extension / "python")
        for extension in extension_folders()
        if (extension / "python").is_dir()
    ]


def extension_package_folder(extension: Path) -> Path:
    """
    Where an extension's own python dependencies are installed, for the
    interpreter running this process.

    Named after the interpreter's version, because a compiled package built
    for another one does not load, and after where the interpreter is
    installed, because the same extension is often used by more than one
    installation of QuNex -- on the host and in a container, both on python
    3.12 -- each with packages of its own: `lib/python3.12-1a2b3c4d`. Each
    gets its own folder, and an extension bound into a container finds the
    container's folder, or none, and says so, rather than the host's.
    """
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    where = hashlib.sha256(os.path.realpath(sys.prefix).encode()).hexdigest()[:8]
    return Path(extension) / "lib" / f"python{version}-{where}"


# written into a package folder by the install, to be compared at dispatch
ENVIRONMENT_STAMP = ".qunex_environment"


def environment_fingerprint() -> str:
    """
    A hash of the python packages this process can see, with their versions.

    Taken from the names of the `.dist-info` and `.egg-info` folders on
    `sys.path`, which carry the version, so that it only lists folders: it is
    computed every time an extension command is dispatched. A package folder
    resolved against one set of packages and used with another -- installed on
    the host and bound into a container, or kept across an upgrade of QuNex --
    is recognised by its stamp no longer matching.
    """
    names = []
    for entry in sys.path:
        try:
            names += [n for n in os.listdir(entry or ".") if n.endswith((".dist-info", ".egg-info"))]
        except OSError:
            pass
    return hashlib.sha256("\n".join(sorted(names)).encode()).hexdigest()
