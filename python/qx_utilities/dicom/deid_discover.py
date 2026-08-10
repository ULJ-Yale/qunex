#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``deid_discover.py``

Walks a folder, archive or gzipped file tree, opens every DICOM found and
hands it to a de-identification callback, optionally renaming and saving the
result.
"""

import csv
import glob
import gzip
import os
import re
import tarfile
import tempfile
import zipfile

import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl

try:
    import pydicom.filereader as dfr
except Exception:
    import dicom.filereader as dfr


#######################

# Discovery

#######################

dicom_counter = 0


def _at_frame(tag, vr, length):
    return tag == (0x5200, 0x9230)


def read_dicom_base(filename):
    """Read a file's DICOM header, or return ``(None, None)`` if it is not one."""
    # `f` is bound before the try so the `finally` cannot raise when opening does
    f = None
    gz = False
    try:
        if '.gz' in filename:
            f = gzip.open(filename, 'rb')
            gz = True
        else:
            f = open(filename, 'rb')
        d = dfr.read_partial(f, stop_when=_at_frame)
        f.close()
        return d, gz
    except Exception:
        return None, None
    finally:
        if f is not None and not f.closed:
            f.close()


def read_dicom_full(filename):
    """Read a whole DICOM file, or return ``(None, None)`` if it is not one."""
    f = None
    gz = False
    try:
        if '.gz' in filename:
            f = gzip.open(filename, 'rb')
            gz = True
        else:
            f = open(filename, 'rb')
        # `dcmread`, not the `read_file` alias this used to call: that alias was
        # deprecated in pydicom 2 and removed in pydicom 3, so every read raised
        # an AttributeError that the `except` below turned into "not a dicom"
        d = dfr.dcmread(f)
        f.close()
        return d, gz
    except Exception:
        return None, None
    finally:
        if f is not None and not f.closed:
            f.close()


def get_dicom_name(opened_dicom, extension="dcm"):
    global dicom_counter
    dicom_counter += 1

    s_id = ""
    if "PatientID" in opened_dicom:
        s_id = opened_dicom.PatientID
    elif "StudyID" in opened_dicom:
        s_id = opened_dicom.StudyID
    else:
        s_id = "NA"

    if "SeriesNumber" in opened_dicom:
        sequence_id = str(opened_dicom.SeriesNumber)
    else:
        sequence_id = "NA"

    try:
        sop = opened_dicom.SOPInstanceUID
    except Exception:
        sop = "%010d" % dicom_counter

    filename = "{s_id}-{sequence_id}-{sop}.{extension}".format(
        s_id=s_id,
        sequence_id=sequence_id,
        sop=sop,
        extension=extension)

    return filename


def discover_dicom(folder, deid_function, output_folder=None, rename_files=False, extension="", save=False, archive_file="", _log=None):
    """
    ``discover_dicom(folder, deid_function, output_folder=None, rename_files=False, extension="", save=False, archive_file="")``

    Runs deid_function on each dicom it finds.

    INPUTS
    ======

    --folder         The folder path to search for dicoms.
    --deid_function  The function to run on each dicom file.
    --output_folder  The folder to write the dicoms to, or inplace if None.
    --rename_files   If output_folder is provided, whether to rename the files.
                     This renames the files inside zip and tar files, not the
                     zip or tar files themselves.
    --extension      If rename_files is true, the additional characters to put
                     after the extension (like abc.dcm{extension}).

    USE
    ===

    Given a folder name, looks for DICOMs in nested subfolders, zip files, gzip files
    and tar files and runs the function deid_function on each dicom it finds
    """
    log = gl.log_or_console(_log)

    if output_folder is None and rename_files:
        raise ge.CommandFailed("discover_dicom", "Output folder not specified", "Files can only be renamed if they are being saved in a different location.", "Please provide output_folder as an argument!")

    for (dirpath, dirnames, filenames) in os.walk(folder):
        for filename in filenames:
            full_filename = os.path.join(dirpath, filename)

            log.step("Inspecting %s" % (full_filename))

            opened_dicom = None

            if save:
                opened_dicom, gz = read_dicom_full(full_filename)
            else:
                opened_dicom, gz = read_dicom_base(full_filename)

            # the callback is only ever handed a DICOM. It used to be called
            # whatever the read returned, so with a `None` it still parsed its
            # specification file and reported on it while de-identifying
            # nothing -- work that looked like work and was not
            if opened_dicom is not None:
                log.detail("read as dicom")

                try:
                    modified_dicom = deid_function(opened_dicom, filename=os.path.relpath(full_filename, folder))
                    log.detail("processed")

                    if save:
                        if output_folder is None:
                            output_file = full_filename
                        else:
                            if rename_files:
                                relative_folder = os.path.dirname(os.path.relpath(full_filename, folder))
                                target_folder = os.path.join(output_folder, relative_folder)
                                if not os.path.exists(target_folder):
                                    os.makedirs(target_folder)
                                if gz:
                                    output_file = os.path.join(target_folder, get_dicom_name(modified_dicom, extension=extension + ".dcm.gz"))
                                else:
                                    output_file = os.path.join(target_folder, get_dicom_name(modified_dicom, extension=extension + ".dcm"))

                                with open(archive_file, mode='a') as af:
                                    csv.writer(af).writerow([os.path.relpath(full_filename, folder), 'filename', os.path.relpath(output_file, output_folder)])

                            else:
                                relative_folder = os.path.dirname(os.path.relpath(full_filename, folder))
                                target_folder = os.path.join(output_folder, relative_folder)
                                if not os.path.exists(target_folder):
                                    os.makedirs(target_folder)
                                relative_filepath = os.path.relpath(full_filename, folder)
                                output_file = os.path.join(output_folder, relative_filepath)

                        if gz:
                            file = tempfile.TemporaryFile()
                        else:
                            file = open(output_file, mode='wb')

                        log.detail("saving to %s" % (output_file), depth=1)
                        modified_dicom.save_as(file)

                        if gz:
                            gzfile = gzip.open(output_file, mode='wb')
                            file.seek(0)
                            gzfile.write(file.read())
                            gzfile.close()
                        file.close()

                # a file that read as a DICOM and then failed to be
                # de-identified or written is a failure of the command's whole
                # purpose, not a file to skip quietly: the `except Exception:
                # pass` this replaces is what hid the removed `read_file` API
                except Exception as e:
                    log.error("failed to process %s: %s" % (full_filename, e))

            # `is_zipfile`/`is_tarfile` answer "is this an archive?" on their
            # own, so only the test decides whether the branch is taken. The
            # work below it -- extraction, recursion, re-archiving -- is a
            # failure of the command when it fails, not a file to skip: a
            # package that was de-identified and then not written back used to
            # be reported as "not a dicom file" and exit 0
            if opened_dicom is None and zipfile.is_zipfile(full_filename):
                # the file is a zip whatever happens next, so the tar branch
                # below must not try it and it is not "not a dicom file"
                opened_dicom = True

                try:
                    with tempfile.TemporaryDirectory() as temp_directory, tempfile.TemporaryDirectory() as temp_out_directory:
                        with zipfile.ZipFile(full_filename) as file:
                            file.extractall(temp_directory)

                        log.detail("extracted as a zip file")

                        discover_dicom(temp_directory, deid_function, temp_out_directory, rename_files, extension, save=save, archive_file=archive_file, _log=log)

                        if save:
                            target_file = full_filename

                            if output_folder:
                                relative_filepath = os.path.relpath(target_file.replace('.zip', "." + extension + '.zip'), folder)
                                target_file = os.path.join(output_folder, relative_filepath)

                            log.step("zipping to %s" % (target_file))

                            with zipfile.ZipFile(target_file, mode='w') as file:
                                for (dirpath_2, dirnames_2, filenames_2) in os.walk(temp_out_directory):
                                    for filename_2 in filenames_2:
                                        full_path_2 = os.path.join(dirpath_2, filename_2)
                                        relative_filepath_2 = os.path.relpath(full_path_2, temp_out_directory)
                                        file.write(full_path_2, relative_filepath_2)

                except Exception as e:
                    log.error("failed to process zip archive %s: %s" % (full_filename, e))

            if opened_dicom is None and tarfile.is_tarfile(full_filename):
                opened_dicom = True

                try:
                    with tempfile.TemporaryDirectory() as temp_directory, tempfile.TemporaryDirectory() as temp_out_directory:
                        with tarfile.open(full_filename) as file:
                            file.extractall(temp_directory, filter="data")

                        log.detail("extracted as a tar file")

                        discover_dicom(temp_directory, deid_function, temp_out_directory, rename_files, extension, save=save, archive_file=archive_file, _log=log)

                        if save:
                            target_file = full_filename

                            # the compression has to come from the name. this
                            # used to be `"w" + file.mode[1:]` off the read
                            # handle, but `TarFile.__init__` reduces the mode
                            # to a single character, so it is "r" for every
                            # archive here and the write mode was always plain
                            # "w" -- a .tar.gz went back out as an
                            # uncompressed tar still called .tar.gz
                            if full_filename.endswith((".tar.gz", ".tgz")):
                                mode2 = "w:gz"
                            elif full_filename.endswith((".tar.bz2", ".tar.bzip2")):
                                mode2 = "w:bz2"
                            else:
                                mode2 = "w"

                            if output_folder:
                                tarext = re.search(r"\.tar$|\.tar.gz$|\.tar.bz2$|\.tarz$|\.tar.bzip2$|\.tgz$", full_filename).group(0)
                                relative_filepath = os.path.relpath(target_file.replace(tarext, "." + extension + tarext), folder)
                                target_file = os.path.join(output_folder, relative_filepath)

                            log.step("archiving to %s" % (target_file))

                            with tarfile.open(target_file, mode2) as file:
                                for item in glob.glob(os.path.join(temp_out_directory, '*')):
                                    relative_filepath = os.path.relpath(item, temp_out_directory)
                                    file.add(item, relative_filepath)

                except Exception as e:
                    log.error("failed to process tar archive %s: %s" % (full_filename, e))

            if opened_dicom is None:
                log.detail("not a dicom file ... skipping")
                # logging.warning("Unable to identify %s as a dicom file or zip archive to search.", full_filename)
                continue
