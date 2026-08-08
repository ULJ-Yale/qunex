# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for ``log_render_diff``, the harness the ``raw()`` retirement leans on.

The pass rewrites ~400 call sites on the claim that a ``raw()`` whose leading
literal already spells a prefix renders exactly what the semantic method would.
These pin that claim, so if it is ever false the harness says so instead of
quietly agreeing with a broken codemod.
"""

import pytest

from .log_render_diff import diff_sources, records

# the codemod's whole premise: each pair renders byte-identically, so the
# differ must not be able to tell them apart
EQUIVALENT = [
    ('log.raw("\\n---> ERROR: %s missing" % path)', 'log.error("%s missing" % path)'),
    ('log.raw("\\n---> WARNING: odd")', 'log.warning("odd")'),
    ('log.raw("\\n---> running %s" % tool)', 'log.step("running %s" % tool)'),
    ('log.raw("\\n     ... found %s" % n)', 'log.detail("found %s" % n)'),
    # N9.5's class B5: a bare newline and prose is exactly info()
    ('log.raw("\\nplain line")', 'log.info("plain line")'),
]


@pytest.mark.parametrize("before, after", EQUIVALENT)
def test_prefixed_raw_equals_the_semantic_call(before, after):
    assert records(before) == records(after)
    assert diff_sources(before, after) == []


def test_a_dropped_interpolation_is_caught():
    # same rendered template, one fewer hole -- only the slots catch this
    before = 'log.raw("\\n---> ERROR: %s in %s" % (what, where))'
    after = 'log.error("%s in %s" % (what,))'
    assert diff_sources(before, after) != []


def test_a_reordered_interpolation_is_caught():
    before = 'log.error("%s in %s" % (what, where))'
    after = 'log.error("%s in %s" % (where, what))'
    assert diff_sources(before, after) != []


def test_the_interpolation_style_does_not_matter():
    # so the differ stays usable across N9.6's f-string restyle
    assert diff_sources('log.step("at %s" % path)', 'log.step(f"at {path}")') == []


def test_a_class_c_indent_change_is_reported():
    # four spaces normalising to detail()'s five is a real change and must show
    before = 'log.raw("\\n    ... checking")'
    after = 'log.detail("checking")'
    assert diff_sources(before, after) != []


def test_a_class_c_arrow_addition_is_reported():
    before = 'log.raw("\\nERROR: no such file")'
    after = 'log.error("no such file")'
    assert diff_sources(before, after) != []


def test_depth_is_tracked_through_indent_and_dedent():
    flush = 'def f():\n    log.step("x")\n'
    nested = 'def f():\n    log.indent()\n    log.step("x")\n'
    assert diff_sources(flush, nested) != []
    assert diff_sources(nested, nested + "    log.dedent()\n") == []


def test_a_section_nests_the_block_it_wraps():
    plain = 'def f():\n    log.step("checking")\n    log.step("inner")\n'
    sectioned = 'def f():\n    with log.section("checking"):\n        log.step("inner")\n'
    # the section's own step is identical; the block below it is not
    assert records(plain)["f"][0] == records(sectioned)["f"][0]
    assert records(plain)["f"][1] != records(sectioned)["f"][1]


def test_depth_does_not_leak_between_functions():
    source = (
        'def f():\n    log.indent()\n    log.step("x")\n'
        'def g():\n    log.step("x")\n'
    )
    assert records(source)["f"] != records(source)["g"]


def test_records_are_grouped_by_function():
    source = 'def f():\n    log.step("a")\ndef g():\n    log.step("b")\n'
    assert list(records(source)) == ["f", "g"]
