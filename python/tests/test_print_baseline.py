#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
The ratchet for the print-to-log transition.

A converted module reports through a ``general.log`` record, not through
``print()``. Nothing else in the suite notices when a new ``print()`` appears
in one of them -- a conversion cannot be proven byte-identical, so there is no
differ here -- and the drift these tests guard against is exactly how the six
competing logging implementations grew in the first place.

Two guards, and the second is the general one:

1. **A per-module budget** for the modules the sweep has converted. Most are at
   zero; the handful that are not carry a reason, and the reasons are the
   never-convert classes of the transition review (the output *is* the
   command's product, a ``_demo`` self-check, a developer's debug trace).
2. **The rule of D-improve-logging-001** -- a function that declares ``_log``
   converts its own prints -- asserted over the whole of ``qx_utilities``, with
   the decision's amendment for the prints that are console notices rather than
   records (:data:`CONSOLE_NOTICES`).

A failure here is not necessarily a bug: it is a print that has to be either
converted or added to the budget with its reason.
"""

import ast
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "qx_utilities"

# module -> stdout prints it is allowed to hold, with the reason for every
# entry that is not zero. `dicom/legacy/` is not here: it is deprecated and
# stays as it is.
BUDGET = {
    # --- dicom/, finished by N12.7
    "dicom/change_dicom_files.py": 0,
    "dicom/clean_dicom.py": 0,
    "dicom/deid_actions.py": 0,
    "dicom/deid_discover.py": 0,
    "dicom/deid_tags.py": 7,  # `recurse_tree`'s debug trace, behind a flag no caller sets
    "dicom/dicom2niix.py": 0,
    "dicom/dicom_archive.py": 0,
    "dicom/dicom_info.py": 0,
    "dicom/dicom_utils.py": 0,
    "dicom/get_dicom_fields.py": 0,
    "dicom/get_dicom_info.py": 51,  # the DICOM fields *are* the command's product
    "dicom/import_dicom.py": 0,
    "dicom/import_utils.py": 0,
    "dicom/list_dicom.py": 3,  # the listing *is* the command's product
    "dicom/sort_dicom.py": 0,
    "dicom/sort_records.py": 0,
    "dicom/sort_report.py": 1,  # `_demo` self-check
    "dicom/sort_tags.py": 0,
    "dicom/sort_validate.py": 1,  # `_demo` self-check
    "dicom/split_dicom.py": 0,
    # --- modules earlier N12 steps emptied
    "general/bruker.py": 0,
    "general/fidl.py": 0,
    "general/sessions.py": 0,
    "general/snapshots.py": 0,
    "hcp/import_hcp.py": 0,
    "nhp/import_nhp.py": 0,
}


def _stdout_prints(tree):
    """Every ``print()`` in `tree` that writes to stdout rather than to a file."""
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
        and not any(kw.arg == "file" for kw in node.keywords)
    ]


@pytest.mark.parametrize("relpath", sorted(BUDGET))
def test_converted_module_holds_no_new_print(relpath):
    path = SOURCE_ROOT / relpath
    assert path.exists(), f"{relpath} is in the budget but not in the tree"

    prints = _stdout_prints(ast.parse(path.read_text()))
    lines = ", ".join(str(node.lineno) for node in prints)
    assert len(prints) == BUDGET[relpath], (
        f"{relpath} holds {len(prints)} stdout print(s) [lines: {lines}], "
        f"budget is {BUDGET[relpath]}. Convert it to a `general.log` record, or "
        f"raise the budget here with the reason it stays a print."
    )


def test_every_dicom_module_is_budgeted():
    """A new module in ``dicom/`` joins the budget rather than escaping it."""
    present = {
        "dicom/" + p.name
        for p in (SOURCE_ROOT / "dicom").glob("*.py")
        if p.name != "__init__.py"
    }
    assert present - set(BUDGET) == set()


# functions that declare `_log` and still print. D-improve-logging-001's
# amendment is what admits them: a print is a console notice, never a record,
# and it is right only where both of these hold.
#
# 1. the fact is already recorded durably, by someone. a print never replaces a
#    record: `close_log` writes `logfile: <path>` into the report once the file
#    is final, and `_trace` writes the expanded command into the comlog, which
#    is what makes a comlog readable on its own;
# 2. the console needs it at a moment, or in a form, the log cannot serve. the
#    runlog does not stream -- a `SessionLog` does not echo, and
#    `general.process` prints the whole report only once the command has
#    returned -- so "you can follow the command's progress in: <path>",
#    recorded rather than printed, would arrive when the run it invites you to
#    watch is over, naming the `tmp_` file `ComContext.close` has since renamed.
#
# where only 1 holds, record it; where only 2 does, record it *and* echo it. a
# third entry here has to be argued in the same terms.
CONSOLE_NOTICES = {"run_external_for_file", "combined_comlog"}


def test_declaring_a_log_means_converting_its_prints():
    """D-improve-logging-001, over the whole tree."""
    offenders = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            declared = [a.arg for a in node.args.args + node.args.kwonlyargs]
            if "_log" not in declared or node.name in CONSOLE_NOTICES:
                continue
            for printed in _stdout_prints(node):
                offenders.append(
                    "%s:%d %s()" % (path.name, printed.lineno, node.name)
                )
    assert offenders == [], (
        "a function that declares `_log` converts its own prints "
        "(D-improve-logging-001): " + "; ".join(offenders)
    )
