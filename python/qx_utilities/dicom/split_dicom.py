#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``split_dicom.py``

The ``split_dicom`` command: splits a folder holding DICOM files from
several sessions into one subfolder per session.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import glob
import os

import qx_utilities.general.exceptions as ge
from qx_utilities.dicom.dicom_info import get_dicom_time, get_id, read_dicom_base


def split_dicom(folder=None):
    """
    ``split_dicom [folder=inbox]``

    Sort out DICOM images from different sessions.

    ..  qx_command:
        type: utility

    Parameters:
        --folder (str, default 'inbox'):
            The folder that contains the DICOM files to be sorted out.

    Notes:
        The command is used when DICOM images from different sessions are mixed
        in the same folder and need to be sorted out. Specifically, the command
        inspects the specified folder (`folder`) and its subfolders for the
        presence of DICOM files. For each DICOM file it finds, it checks, what
        session id the file belongs to. In the specified folder it then creates
        a subfolder for each of the found sessions and moves all the DICOM
        files in the right sessions' subfolder.

    Examples:
        ::

            qunex split_dicom \\
                --folder=dicommess
    """

    if folder is None:
        folder = os.path.join(".", "inbox")

    print(
        "============================================\n\nSorting dicoms from %s\n"
        % (folder)
    )

    files = glob.glob(os.path.join(folder, "*"))
    files = files + glob.glob(os.path.join(folder, "*/*"))
    files = [e for e in files if os.path.isfile(e)]

    if not files:
        raise ge.CommandFailed(
            "split_dicom",
            "No files found",
            "Please check the specified folder! [%s]" % (os.path.abspath(folder)),
            "Aborting",
        )

    sessions = []

    for dcm in files:
        try:
            # d    = dicom.read_file(dcm, stop_before_pixels=True)
            d = read_dicom_base(dcm)
            time = get_dicom_time(d)
            sid = get_id(d)
            if sid not in sessions:
                sessions.append(sid)
                os.makedirs(os.path.join(folder, sid))
                print("---> creating subfolder for session %s" % (sid))
            print(
                "---> %s - %-6s %6d - %-30s scanned on %s"
                % (dcm, sid, d.SeriesNumber, d.SeriesDescription, time)
            )
            os.rename(dcm, os.path.join(folder, sid, os.path.basename(dcm)))
        except Exception:
            pass

    return
