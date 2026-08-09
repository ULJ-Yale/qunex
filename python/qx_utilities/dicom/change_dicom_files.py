#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``change_dicom_files.py``

The ``change_dicom_files`` command: applies a de-identification
specification to every DICOM file found in a folder.
"""

import functools
import os
import random
import string

import qx_utilities.general.exceptions as ge
from qx_utilities.dicom.deid_actions import deid_and_date_removal
from qx_utilities.dicom.deid_discover import discover_dicom


#######################

# Reprocessing

#######################

DEFAULT_SALT = ''.join(random.choice(string.ascii_uppercase) for i in range(12))


def change_dicom_files(folder=".", paramfile="deidparam.txt", archivefile="archive.csv", outputfolder=None, extension="", replacementdate=None):
    """
    ``change_dicom_files [folder=.] [paramfile=deidparam.txt] [archivefile=archive.csv] [outputfolder=None] [extension=""] [replacementdate=]``

    Change all the dicom files in the specified folder according the `paramfile`.

    ..  qx_command:
        type: utility

    Description:
        Changes all the dicom files in the specified folder according to the
        directions provided in the `paramfile`. The command is used to change all
        the dicom files in the specified folder according to directions provided in
        the `paramfile`. The values to be archived are saved (appended) to
        `archivefile` as a comma separated values formatted file. The dicom files
        can be either changed in place or saved to the specified `outputfolder` and
        optionally renamed by adding the specified `extension`.

    Parameters:
        --folder (str, default '.'):
            The base folder to search for DICOM files. The command will try to
            locate all valid DICOM files within the specified folder and its
            subfolders.

        --paramfile (str, default 'deidparam.txt'):
            The path to the parameter file that specifies what actions to
            perform on the dicom fields.

        --archivefile (str, default 'archive.csv'):
            The path to the file in which values to be archived are to be stored.

        --outputfolder (str):
            The optional path to the folder to which the modified dicom files
            are to be saved. If not specified, the dicom files are changed in
            place (overwritten).

        --extension (str):
            An optional extension to be added to each modified dicom file name.
            The extension can be applied only when files are copied to the
            outputfolder.

        --replacementdate (str):
            The date to replace all instances of StudyDate in the file. Looks at
            all DICOM fields with string values, and replaces the substring
            matching StudyDate with either a provided date, or a randomly
            generated date.

    Notes:
        Parameter file:
            Parameter file is a text file that specifies the operations that are
            to be performed on the fields in the dicom files. The default name
            for the parameter file is `deidparam.txt`, however any other name
            can be used. The operations to be performed are specifed one dicom
            field per line in the format:

            ::

                <dicom field>  > <action>[:<parameter>], <action>[:<parameter>]

            Dicom field is the hexdecimal code of the field, which can be found
            in the first column of the readDICOMfields output csv. The list of
            actions is a comma separated list of commands and their optional
            parameters. The possible actions are:

            - archive (archive the original value in the archive file)
            - replace (replace the original value with the specified value)
            - delete (delete the field from the dicom file)

            If multiple actions are specified, they are carried out in the above
            order (archive,replace, delete). Lines in the parameter file that
            start with '#' or do not specify a mapping (i.e. lack '>') are
            ignored. An example of the spec file would be:

            ::

                0x80005  > delete
                0x100010 > delete
                0x80012  > delete, archive
                0x180032 > replace:20070101

        Parameter file:
            Date replacement:
                The date the dicom was recorded is taken from the StudyDate or
                SeriesDate field. The date found is then replaced either by a
                randomly generated date or the date specified by the
                `replacementdate` parameter. Any occurrence ofthe date in any of
                the other fields in dicom is also replaced by the same randomly
                generated or specified date. Please note that any other dates
                (e.g. participant's birth date) are not automatically replaced.
                These need to be either deleted or replaced explicitly.

        Deidentification effectiveness:
            Please note the following:
            1. Only the fields explicitly set to be removed or replaced will
            be changed. It is the responsibility of the user to make sure that
            no dicom fields with identifiable information are left unchanged.
            2. Only valid dicom fields can be accessed and changed using this
            tool. Any vendor specific metadata that is not stored in regular
            dicom fields will not be changed. Please make sure that no such
            information is present in your dicom files.
            3. Only metadata stored in dicom fields can be processed using this
            tool. If any information is "burnt in" into the image data itself,
            it can not be identified and changed using this tool. Please make
            sure that no such information is present in your dicom files.

    Examples:
        ::

            qunex change_dicom_files \\
                --folder=.

        ::

            qunex change_dicom_files \\
                --folder=/data/studies/WM/sessions/inbox/MR \\
                --paramfile=/data/studies/WM/sessions/specs/deid.txt

        ::

            qunex change_dicom_files \\
                --folder=/data/studies/WM/sessions/inbox/MR/original \\
                --paramfile=/data/studies/WM/sessions/specs/deidv1.txt \\
                --outputfolder=/data/studies/WM/sessions/MR/deid \\
                --extension="v1"
    """

    if extension:
        renamefiles = True
    else:
        renamefiles = False

    if not os.path.exists(folder):
        raise ge.CommandFailed("change_dicom_files", "Folder not found", "The specified folder with DICOM files to change was not found:", "%s" % (folder), "Please check your paths!")

    if not paramfile:
        raise ge.CommandError("change_dicom_files", "No parameter file specified", "No parameter file information was provided.", "Please provide a parameter file that describes the changes to be made!")

    if not os.path.exists(paramfile):
        raise ge.CommandFailed("change_dicom_files", "Parameter file not found", "The specified parameter file was not found:", "%s" % (folder), "Please check your paths!")

    try:
        f = open(archivefile, "a")
        f.close()
    except Exception:
        raise ge.CommandFailed("change_dicom_files", "Could not create archive file", "The specifed archive file could not be created:", "%s" % (archivefile), "Please check your paths and permissions!")

    if outputfolder is not None and not os.path.exists(outputfolder):
            os.mkdir(outputfolder)

    manipulate_file = functools.partial(deid_and_date_removal, param_file=paramfile, archive_file=archivefile, replacement_date=replacementdate)
    discover_dicom(folder, manipulate_file, outputfolder, renamefiles, extension, save=True, archive_file=archivefile)
