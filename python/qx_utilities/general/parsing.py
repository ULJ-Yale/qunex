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



def true_or_false(s):
    """
    ``true_or_false(s)``

    First checks if string is "None", 'none', or "NONE" and returns
    None, then Checks if s is any of the possible true strings: "True", "true",
    or "TRUE" and returns a boolean result of the check.
    """
    if s in ["None", "none", "NONE"]:
        return None
    else:
        return s in ["True", "true", "TRUE", "yes", "Yes", "YES", True]


def flag(f):
    """
    ``flag(f)``

    Converts a flag (f) passed as a string to a boolean.
    """

    if type(f) == bool:
        return f
    elif f in ["True", "true", "TRUE", "yes", "Yes", "YES"]:
        return True
    else:
        return False


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