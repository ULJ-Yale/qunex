# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Defaults the command registry reads from a docstring's parameter line."""

import inspect

import pytest

import qx_registry_build
from qx_utilities.general import utilities


@pytest.mark.parametrize(
    "spec, expected",
    [
        ("str, default 'abc'", ("str", "abc")),
        ('str, default "abc"', ("str", "abc")),
        ("int, default 20", ("int", "20")),
        ("str, default ``BOLD_``", ("str", "BOLD_")),
    ],
)
def test_parse_type_default_strips_quotes_and_literals(spec, expected):
    """A quoted value and an rst literal both give the bare default."""
    assert qx_registry_build._parse_type_default(spec) == expected


def test_batch_tag2namekey_prefix_default_is_valid_rst():
    """A default ending in "_" is not read by docutils as a link reference."""
    docutils_core = pytest.importorskip("docutils.core")

    doc = inspect.getdoc(utilities.batch_tag2namekey)
    line = next(ln for ln in doc.splitlines() if ln.strip().startswith("--prefix"))
    spec = line.split("(", 1)[1].rsplit(")", 1)[0]
    assert qx_registry_build._parse_type_default(spec) == ("str", "BOLD_")

    doctree = docutils_core.publish_doctree(
        line.strip() + "\n    x\n",
        settings_overrides={"report_level": 1, "warning_stream": False},
    )
    problems = [
        n.astext()
        for n in doctree.findall()
        if n.tagname in ("problematic", "system_message")
    ]
    assert problems == []
