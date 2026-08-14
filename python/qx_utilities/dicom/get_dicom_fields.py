#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``get_dicom_fields.py``

The ``get_dicom_fields`` command: inventories the DICOM fields present in a
folder of DICOM files and writes them to a csv file.
"""

import os

import qx_utilities.general.exceptions as ge
from qx_utilities.dicom.deid_discover import discover_dicom
from qx_utilities.dicom.deid_tags import dicom_scan, write_field_dict


def get_dicom_fields(folder=".", targetfile="dicom_fields.csv", limit="20", _log=None):
    """
    ``get_dicom_fields [folder=.] [targetfile=dicom_fields.csv] [limit=20]``

    Return an overview of DICOM fields across all the DICOM files in the
    specified folder.

    ..  qx_command:
        type: utility

    Parameters:
        --folder (str, default '.'):
            The base folder to search for DICOM files. The command will try to
            locate all valid DICOM files within the specified folder and its
            subfolders.

        --targetfile (str, default 'dicom_fields.csv'):
            The name (and path) of the file to store the information in.

        --limit (int, default 20):
            The maximum number of example values to provide for each of the
            DICOM fields.

    Output files:
        After running, the command will inspect all the valid DICOM files
        (including gzip compressed ones) in the specified folder and its
        subfolders. It will generate a report file that will list all the DICOM
        fields found across all the DICOM files. For each of the fields, the
        command will list example values up to the specified limit. The list
        will be saved as a comma separated values (csv) file.

        This file can be used to identify the fields that might carry personally
        identifiable information and therefore need to be processed
        appropriately.

    Examples:
        ::

            qunex get_dicom_fields

        ::

            qunex get_dicom_fields \\
                --folder=/data/studies/WM/sessions/inbox/MR

        ::

            qunex get_dicom_fields \\
                 --folder=/data/studies/WM/sessions/inbox/MR/original \\
                 --targetfile=/data/studies/WM/sessions/specs/dicom_fields.csv \\
                 --limit=10
    """

    if not os.path.exists(folder):
        raise ge.CommandFailed("get_dicom_fields", "Folder not found", "The specified folder with DICOM files to analyse was not found:", "%s" % (folder), "Please check your paths!")

    try:
        f = open(targetfile, "w")
        f.close()
    except Exception:
        raise ge.CommandFailed("get_dicom_fields", "Could not create target file", "The specifed target file could not be created:", "%s" % (targetfile), "Please check your paths and permissions!")

    _ = {}

    # the command has no report of its own -- it declares `_log` so that
    # `discover_dicom`'s does not fall back to a console stand-in, whose
    # errors cannot fail the run
    discover_dicom(folder, dicom_scan, save=False, archive_file="", _log=_log)
    write_field_dict(targetfile, limit)
