#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``dicom_utils.py``

Small shared helpers and constants used across the ``dicom`` package: the
``vdict`` defaulting dictionary, name and pattern helpers, a defensive tree
removal, the DICOM info field table and the Matlab command string.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import os
import re
import shutil

import qx_utilities.general.log as gl


if "QUNEXMCOMMAND" not in os.environ:
    mcommand = "matlab -nojvm -nodisplay -nosplash -r"
else:
    mcommand = os.environ["QUNEXMCOMMAND"]

dcm_info_list = (
    ("sessionid", str, "NA"),
    ("seriesNumber", int, 0),
    ("seriesDescription", str, "NA"),
    ("TR", float, 0.0),
    ("TE", float, 0.0),
    ("frames", int, 0),
    ("directions", int, 0),
    ("volumes", int, 0),
    ("slices", int, 0),
    ("datetime", str, ""),
    ("ImageType", str, ""),
    ("fileid", str, ""),
)


class vdict(dict):
    """
    An extension of a dictionary class. Upon initialization it creates fields
    with the names and default values as specified in the __keys__, which
    should be a list of key_name, key_func, and key_default triplets.

    Upon initialization, keys with the provided names and defaults values are
    created. When calling `validate` method, any missing keys are generated
    with the default values, and all the keys are transformed according to
    the provided functions in the key_func.
    """

    def __init__(self, *args, **kw):
        self.__keys__ = kw.pop("__keys__", ())
        super(vdict, self).__init__(*args, **kw)
        self.validate()

    def validate(self):
        for key_name, key_func, key_default in self.__keys__:
            try:
                self[key_name] = key_func(self.get(key_name, key_default))
            except ValueError as e:
                e.args += f"Validation of the dictionary failed! The value '{self[key_name]}' for {key_name} is invalid!"
                raise


def clean_name(string):
    """
    ``clean_name(string)``

    Function that makes sure that the string does not contain characters that
    should not be in a file name.
    """
    return re.sub(r"[^A-Za-z0-9]", r"", string)


def match_all(pattern, string):
    """
    ``match_all(pattern, string)``

    Function that checks if the pattern matches the whole string.
    """

    m = re.match(pattern, string)

    if m:
        return m.group() == string
    else:
        return False


def _safe_rmtree(path, _log=None):
    """
    Best-effort recursive folder removal.

    Some filesystems can leave transient files behind during cleanup, which can
    cause shutil.rmtree to raise. This helper logs and continues.
    """
    try:
        shutil.rmtree(path)
    except Exception as e:
        gl.log_or_console(_log).warning(f"unable to remove folder {path}: {e}")
