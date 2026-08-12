#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``general/log`` imports nothing from the tree but leaf utilities.

The log package owns how a report reads; everything else imports it. That only
holds while the arrow points one way, and it did not: thirteen imports inside
the package reached up into ``general/core`` and ``processing/core``, every one
of them written inside a function body because an import at module level would
have been a circular ``ImportError`` -- ``general/core`` imports the log package
too. The lazy import was never a design, it was the cycle not being an error
yet.

Without this test that regresses the first time someone needs one helper, which
is exactly how the thirteen accumulated. So the assertion covers imports
**anywhere** in the module, function bodies included, and it is a whole-package
rule rather than a per-module one: a new file under ``general/log/`` is bound by
it without being added anywhere.

The same shape as ``test_print_baseline.py`` and ``test_registry_drift.py``,
which this branch already relies on.
"""

import ast
from pathlib import Path

LOG_PACKAGE = Path(__file__).resolve().parents[1] / "qx_utilities" / "general" / "log"

# what the log package may import from the tree: leaf utilities that import
# nothing from it, or from anything else in `qx_utilities`
ALLOWED = {
    "qx_utilities.general.exceptions",
    "qx_utilities.general.parsing",
    # its own modules
    "qx_utilities.general.log",
    "qx_utilities.general.log.context",
    "qx_utilities.general.log.report",
    "qx_utilities.general.log.settings",
}


def _imported(tree):
    """Every ``qx_utilities.*`` module this tree imports, at any depth."""
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
    return {name for name in found if name.startswith("qx_utilities")}


def test_the_log_package_imports_only_leaf_utilities():
    offenders = {}
    for path in sorted(LOG_PACKAGE.glob("*.py")):
        reaching = _imported(ast.parse(path.read_text())) - ALLOWED
        if reaching:
            offenders[path.name] = sorted(reaching)

    assert offenders == {}, (
        "`general/log` reaches back into the tree: %s. The log package owns how "
        "a report reads and imports nothing else -- give it what it needs as a "
        "parameter, or move the formatting into the package." % offenders
    )


def test_the_allowed_imports_are_themselves_leaves():
    """The allowance is only sound while `exceptions` and `parsing` import nothing."""
    root = LOG_PACKAGE.parents[1]
    for module in ("general/exceptions.py", "general/parsing.py"):
        reaching = _imported(ast.parse((root / module).read_text()))
        assert reaching == set(), "%s is no longer a leaf: %s" % (module, reaching)
