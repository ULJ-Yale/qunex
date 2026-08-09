#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``list_dicom.py``

The ``list_dicom`` command: prints session, sequence and acquisition
information for the DICOM files found in a folder.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import glob
import os

import qx_utilities.general.exceptions as ge
from qx_utilities.dicom.dicom_info import get_dicom_time, get_id, read_dicom_base


def list_dicom(folder=None):
    """
    ``list_dicom [folder=inbox]``

    Identify all DICOM files in a folder and print a detailed report.

    ..  qx_command:
        type: utility

    Parameters:
        --folder (str, default 'inbox'):
            The folder to be inspected for the presence of the DICOM files.

    Notes:
        The command inspects the folder (`folder`) for dicom files and prints a
        detailed report of the results. Specifically, for each dicom file it
        finds in the specified folder and its subfolders it will print:

        - location of the file
        - session id recorded in the dicom file
        - sequence number and name
        - date and time of acquisition.

        Importantly, it can work with both regular and gzipped DICOM files.

    Examples:
        ::

            qunex list_dicom \\
                --folder=OP269/dicom
    """

    if folder is None:
        folder = os.path.join(".", "inbox")

    print(
        "============================================\n\nListing dicoms from %s\n"
        % (folder)
    )

    files = glob.glob(os.path.join(folder, "*"))
    files = files + glob.glob(os.path.join(folder, "*/*"))
    files = [e for e in files if os.path.isfile(e)]

    if not files:
        raise ge.CommandFailed(
            "list_dicom",
            "No files found",
            "Please check the specified folder! [%s]" % (os.path.abspath(folder)),
            "Aborting",
        )

    for dcm in files:
        try:
            d = read_dicom_base(dcm)
            time = get_dicom_time(d)
            try:
                print(
                    "---> %s - %-6s %6d - %-30s scanned on %s"
                    % (dcm, get_id(d), d.SeriesNumber, d.SeriesDescription, time)
                )
            except Exception:
                print(
                    "---> %s - %-6s %6d - %-30s scanned on %s"
                    % (dcm, get_id(d), d.SeriesNumber, d.ProtocolName, time)
                )
        except Exception:
            pass

    return
