#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Reading a boolean written the way a user actually writes it.

``flag`` is the type converter for 21 ``arglist`` entries and ``true_or_false``
is called on user-supplied strings in ``dicom.py`` and ``snapshots.py``, so
what these accept is a command line contract. Both now defer to ``as_bool``,
whose one addition is that it can say **"that is not a boolean"** -- which is
what lets ``--keep_comlogs=sometimes`` raise instead of silently reading as no.
"""

import pytest

from qx_utilities.general.parsing import as_bool, flag, is_none, true_or_false


@pytest.mark.parametrize("value", ["true", "TRUE", "True", "yes", "YES", "on", "1", " Yes "])
def test_the_true_spellings(value):
    assert as_bool(value) is True
    assert flag(value) is True
    assert true_or_false(value) is True


@pytest.mark.parametrize("value", ["false", "FALSE", "no", "NO", "off", "0", " no "])
def test_the_false_spellings(value):
    assert as_bool(value) is False
    assert flag(value) is False
    assert true_or_false(value) is False


@pytest.mark.parametrize("value", ["", None, "sometimes", "maybe", "2"])
def test_anything_else_is_not_a_boolean(value):
    """The distinction `flag` could not make: unrecognised, not "no"."""
    assert as_bool(value) is None
    # the two defaulting callers still fall back to False, as they always did
    assert flag(value) is False
    assert true_or_false(value) is False


def test_a_real_bool_passes_through():
    assert (as_bool(True), as_bool(False)) == (True, False)
    assert (flag(True), flag(False)) == (True, False)


def test_true_or_false_keeps_its_none():
    """Its one difference from `flag`, and the reason both exist."""
    for spelling in ["None", "none", "NONE"]:
        assert true_or_false(spelling) is None
        assert flag(spelling) is False


def test_is_none_maps_only_the_empty_string():
    assert is_none("") is None
    assert is_none("0") == "0"
