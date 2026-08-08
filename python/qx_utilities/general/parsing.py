#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``parsing.py``

Utility functions for parsing input strings.
"""

"""
Created by Grega Repovs on 2026-02-01.
Copyright (c) Grega Repovs and Jure Demsar. All rights reserved.
"""


# the spellings a boolean may be written as, compared case-insensitively
TRUE_VALUES = ["true", "yes", "on", "1"]
FALSE_VALUES = ["false", "no", "off", "0"]


def as_bool(value):
    """
    ``as_bool(value)``

    Reads a boolean written any of the ways QuNex accepts it, in any case.

    Returns True, False, or **None when `value` is not a boolean at all** --
    so a caller can tell "the user wrote no" from "the user wrote nonsense"
    and choose for itself whether to default or to complain. :func:`flag` and
    :func:`true_or_false` default; ``--keep_comlogs`` complains.
    """
    if isinstance(value, bool):
        return value

    key = str(value).strip().lower()
    if key in TRUE_VALUES:
        return True
    if key in FALSE_VALUES:
        return False
    return None


def true_or_false(s):
    """
    ``true_or_false(s)``

    Converts a string to a boolean, with the *string* "none" in any case
    reading as None. Anything else that is not a boolean spelling reads as
    False -- including `None` itself, which is not the string.
    """
    if isinstance(s, str) and s.strip().lower() == "none":
        return None

    return as_bool(s) is True


def flag(f):
    """
    ``flag(f)``

    Converts a flag (f) passed as a string to a boolean. Anything that is not
    a boolean spelling -- including the empty default of an unpassed flag --
    is False.
    """
    return as_bool(f) is True


def is_none(s):
    """
    ``is_none(s)``

    Check if the string is "" and returns None, otherwise
    returns the passed string.
    """

    if s in [""]:
        return None
    else:
        return s