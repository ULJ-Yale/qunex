# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later


"""
Build-time splice of general/batch_io.py into bin/qunex_container, the same
generated-and-committed arrangement qx_registry_build.py has with
qx_commands.yaml.

qunex_container runs outside the container, on a login node, in whatever python
the host provides — it can not import QuNex, so it carries a copy of the parser
instead of a second implementation of it. tests/test_container_drift.py fails if
the copy and the source drift apart.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTAINER = REPO_ROOT / "bin" / "qunex_container"
BATCH_IO = REPO_ROOT / "python" / "qx_utilities" / "general" / "batch_io.py"

BEGIN = (
    "# --- BEGIN GENERATED from general/batch_io.py "
    "— do not edit; run `qunex build_qx_container` ---"
)
END = "# --- END GENERATED ---"

NOTE = (
    "# the container runs on a login node with no QuNex on the path, so it "
    "carries a\n# copy of the one parser rather than importing it"
)

_REGION_RE = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n", re.S)

# the shebang, the encoding line, the SPDX block and the module docstring — the
# container has its own, and a second docstring before the imports is E402 bait
_HEADER_RE = re.compile(r'\A(?:#[^\n]*\n|[ \t]*\n)*(?:"""(?:.|\n)*?"""\n)?')


def render(container_text: str, module_text: str) -> str:
    """Returns container_text with its generated region filled from module_text."""

    if not _REGION_RE.search(container_text):
        raise ValueError(
            f"no generated region in the container — expected a {BEGIN!r} / "
            f"{END!r} pair"
        )

    region = "%s\n%s\n\n%s\n%s\n" % (
        BEGIN,
        NOTE,
        _HEADER_RE.sub("", module_text).strip(),
        END,
    )

    return _REGION_RE.sub(lambda _: region, container_text, count=1)


def build_qx_container():
    """
    ``build_qx_container()``

    Splice `general/batch_io.py` into the generated region of
    `bin/qunex_container`. The container can not import QuNex — it runs on the
    login node, outside the container — so it carries a copy of the batch file
    parser, and this command is what keeps that copy current. Commit the result,
    as with `qx_commands.yaml`.

    ..  qx_command:
        type: utility

    Returns:
        --path (str):
            The path of the container that was written.
    """

    CONTAINER.write_text(render(CONTAINER.read_text(), BATCH_IO.read_text()))

    print(f"--> Spliced {BATCH_IO} into {CONTAINER}")

    return str(CONTAINER)
