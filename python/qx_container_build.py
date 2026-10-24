# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Build-time splice of general/batch_io.py and general/folders.py into
bin/qunex_container, the same generated-and-committed arrangement
qx_registry_build.py has with qx_commands.yaml.

qunex_container runs outside the container, on a login node, in whatever python
the host provides — it can not import QuNex, so it carries a copy of the code it
shares with QuNex instead of a second implementation of it: the batch file
parser, and the study layout with the rule for where a run logs.
tests/test_container_drift.py fails if the copy and the source drift apart.

The splice writes three things into the container: the version line in its
header, taken from VERSION.md; the imports the modules need, merged into the
container's own import block so the file stays free of E402/F811; and the
modules' bodies, one after the other in one region between the generated
markers. Only that region is off limits by hand — the import block is ordinary
code that this command adds to, never prunes, so an import that stops being
needed is removed by deleting it there.

The spliced modules and the launcher's own code share one namespace. So each
module imports nothing but the standard library, neither imports the other, and
neither defines a name the other module or the launcher defines;
tests/test_container_drift.py holds them to all three.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTAINER = REPO_ROOT / "bin" / "qunex_container"
BATCH_IO = REPO_ROOT / "python" / "qx_utilities" / "general" / "batch_io.py"
FOLDERS = REPO_ROOT / "python" / "qx_utilities" / "general" / "folders.py"
VERSION_FILE = REPO_ROOT / "VERSION.md"

# the modules the container carries, in the order their bodies are spliced
MODULES = (BATCH_IO, FOLDERS)

# the container release line, as it reads in VERSION.md and the changelog
CODENAME = "QIO"

BEGIN = (
    "# --- BEGIN GENERATED from general/batch_io.py and general/folders.py "
    "— do not edit; run `qunex build_qx_container` ---"
)
END = "# --- END GENERATED ---"

NOTE = (
    "# the container runs on a login node with no QuNex on the path, so it "
    "carries a\n# copy of the code it shares with QuNex rather than importing "
    "it: the batch file\n# parser, and the study layout with the rule for "
    "where a run logs. what these\n# need is imported at the top of the file, "
    "with the container's own imports"
)

# the region, from any `BEGIN GENERATED from` line: one that names other
# modules, as an earlier build wrote it, is found and rewritten as well
_REGION_RE = re.compile(
    r"# --- BEGIN GENERATED from [^\n]*\n.*?" + re.escape(END) + r"\n", re.S
)

# the version line in the container header, stamped from VERSION.md
_VERSION_RE = re.compile(r"^# Version .*$", re.M)

# the shebang, the encoding line, the SPDX block and the module docstring — the
# container has its own, and a second docstring before the imports is E402 bait
_HEADER_RE = re.compile(r'\A(?:#[^\n]*\n|[ \t]*\n)*(?:"""(?:.|\n)*?"""\n)?')

# `from __future__` has to stay first, so the import block that is merged into
# starts on the line after it
_FUTURE_RE = re.compile(r"^from __future__ import[^\n]*\n", re.M)
_IMPORTS_RE = re.compile(
    r"^(?:import |from )[^\n]*\n(?:^(?:import |from )[^\n]*\n)*", re.M
)


def _import_sort_key(line: str) -> tuple[int, str, str]:
    """Orders an import block the way isort and ruff's I001 rule do."""

    return (0 if line.startswith("import ") else 1, line.split()[1].lower(), line)


def read_version() -> str:
    """Returns the suite version, as `VERSION.md` states it."""

    return VERSION_FILE.read_text().strip()


def stamp_version(container_text: str, version: str) -> str:
    """Returns container_text with its header version line set to version."""

    if not _VERSION_RE.search(container_text):
        raise ValueError(
            "no version line in the container header — expected a "
            "'# Version <version> [<codename>]' comment"
        )

    line = f"# Version {version} [{CODENAME}]"

    return _VERSION_RE.sub(lambda _: line, container_text, count=1)


def split_module(module_text: str) -> tuple[list[str], str]:
    """Splits a module into its import lines and the body that follows them."""

    body = _HEADER_RE.sub("", module_text).lstrip("\n")
    imports = _IMPORTS_RE.match(body)

    if imports is None:
        raise ValueError("no import block found in the module being spliced")

    return imports.group().split("\n")[:-1], body[imports.end() :].strip()


def merge_imports(container_text: str, imports: list[str]) -> str:
    """Returns container_text with imports added to its own import block."""

    future = _FUTURE_RE.search(container_text)
    block = _IMPORTS_RE.search(container_text, future.end() if future else 0)

    if block is None:
        raise ValueError("no import block found in the container")

    present = set(block.group().split("\n")[:-1])
    merged = "\n".join(sorted(present | set(imports), key=_import_sort_key)) + "\n"

    return container_text[: block.start()] + merged + container_text[block.end() :]


def render(container_text: str, module_texts: str | list[str], version: str) -> str:
    """
    Returns container_text with its version, imports and generated region
    regenerated from module_texts: the text of one module, or a list of them,
    whose bodies follow each other in the region in the order given.
    """

    if not _REGION_RE.search(container_text):
        raise ValueError(
            f"no generated region in the container — expected a {BEGIN!r} / "
            f"{END!r} pair"
        )

    if isinstance(module_texts, str):
        module_texts = [module_texts]

    imports, bodies = [], []
    for module_text in module_texts:
        module_imports, body = split_module(module_text)
        imports += module_imports
        bodies.append(body)

    # two blank lines inside each marker and between the modules, so the
    # region reads as the top level code it is rather than as a tail of the
    # function on either side of it
    region = f"{BEGIN}\n{NOTE}\n\n\n" + "\n\n\n".join(bodies) + f"\n\n\n{END}\n"

    container_text = stamp_version(container_text, version)
    container_text = merge_imports(container_text, imports)

    return _REGION_RE.sub(lambda _: region, container_text, count=1)


def spliced_modules() -> list[str]:
    """Returns the text of every module the container carries, in splice order."""

    return [module.read_text() for module in MODULES]


def build_qx_container():
    """
    ``build_qx_container()``

    Splice `general/batch_io.py` and `general/folders.py` into the generated
    region of `bin/qunex_container` and stamp the container's version line from
    `VERSION.md`. The container can not import QuNex — it runs on the login
    node, outside the container — so it carries a copy of the batch file parser
    and of the study layout, with the rule for where a run logs, and this
    command is what keeps that copy current. Commit the result, as with
    `qx_commands.yaml`.

    ..  qx_command:
        type: utility

    Returns:
        --path (str):
            The path of the container that was written.
    """

    version = read_version()

    CONTAINER.write_text(render(CONTAINER.read_text(), spliced_modules(), version))

    spliced = " and ".join(str(module) for module in MODULES)
    print(f"--> Spliced {spliced} into {CONTAINER} (version {version})")

    return str(CONTAINER)
