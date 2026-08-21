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

    Read from two places, and both are needed. `QXEXTENSIONSPY` is what the
    environment script exports, and it names an extension that was in place when
    the environment was set up. The search roots are read here as well because
    that environment cannot always be refreshed: inside a container it is sourced
    once and every later source returns immediately, so an extension installed
    after the container started would otherwise never reach the path, and its
    commands would be listed and dispatched and then fail to import.
    """
    folders = [e.strip() for e in os.environ.get("QXEXTENSIONSPY", "").split(":") if e.strip()]

    for extension in extension_folders():
        python_folder = extension / "python"
        if python_folder.is_dir():
            folders.append(str(python_folder))

    # de-duplicate, keeping the order the folders were found in
    seen = set()
    return [f for f in folders if not (f in seen or seen.add(f))]
