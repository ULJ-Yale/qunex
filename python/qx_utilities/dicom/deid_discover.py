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
import shutil
import tarfile
import tempfile
import zipfile

import qx_utilities.general.exceptions as ge

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
    # try partial read
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
    # read the full dicom file
    try:
        if '.gz' in filename:
            f = gzip.open(filename, 'rb')
            gz = True
        else:
            f = open(filename, 'rb')
            gz = False
        d = dfr.read_file(f)
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


def discover_dicom(folder, deid_function, output_folder=None, rename_files=False, extension="", save=False, archive_file=""):
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
    if output_folder is None and rename_files:
        raise ge.CommandFailed("discover_dicom", "Output folder not specified", "Files can only be renamed if they are being saved in a different location.", "Please provide output_folder as an argument!")

    for (dirpath, dirnames, filenames) in os.walk(folder):
        for filename in filenames:
            full_filename = os.path.join(dirpath, filename)

            print("---> Inspecting", full_filename)

            opened_dicom = None

            try:
                # opened_dicom = pydicom.dcmread(full_filename, stop_before_pixels=True)
                if save:
                    opened_dicom, gz = read_dicom_full(full_filename)
                else:
                    opened_dicom, gz = read_dicom_base(full_filename)

                if opened_dicom:
                    print(" ... read as dicom")

                modified_dicom = deid_function(opened_dicom, filename=os.path.relpath(full_filename, folder))
                print(" ... processed")

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

                            archive_writer = csv.writer(open(archive_file, mode='a'))
                            archive_writer.writerow([os.path.relpath(full_filename, folder), 'filename', os.path.relpath(output_file, output_folder)])

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

                    print("     -> saving to", output_file)
                    modified_dicom.save_as(file)

                    if gz:
                        gzfile = gzip.open(output_file, mode='wb')
                        file.seek(0)
                        gzfile.write(file.read())
                        gzfile.close()
                    file.close()

            except Exception:
                pass  # file was not a dicom

            if opened_dicom is None:
                try:
                    file = zipfile.ZipFile(full_filename)
                    temp_directory = tempfile.mkdtemp()
                    temp_out_directory = tempfile.mkdtemp()
                    file.extractall(temp_directory)
                    file.close()

                    print(" ... extracted as a zip file")

                    discover_dicom(temp_directory, deid_function, temp_out_directory, rename_files, extension, save=save, archive_file=archive_file)

                    if save:
                        target_file = full_filename

                        if output_folder:
                            relative_filepath = os.path.relpath(target_file.replace('.zip', "." + extension + '.zip'), folder)
                            target_file = os.path.join(output_folder, relative_filepath)

                        print("---> zipping to", target_file)
                        file = zipfile.ZipFile(target_file, mode='w')

                        for (dirpath_2, dirnames_2, filenames_2) in os.walk(temp_out_directory):
                            for filename_2 in filenames_2:
                                full_path_2 = os.path.join(dirpath_2, filename_2)
                                relative_filepath_2 = os.path.relpath(full_path_2, temp_out_directory)
                                file.write(full_path_2, relative_filepath_2)

                        file.close()

                    shutil.rmtree(temp_directory)
                    shutil.rmtree(temp_out_directory)

                except Exception:
                    pass  # File was not a zip archive

            if opened_dicom is None:
                try:
                    file = tarfile.open(full_filename)
                    mode = file.mode
                    temp_directory = tempfile.mkdtemp()
                    temp_out_directory = tempfile.mkdtemp()
                    file.extractall(temp_directory)
                    file.close()

                    print(" ... extracted as a tar file")

                    opened_dicom = True

                    discover_dicom(temp_directory, deid_function, temp_out_directory, rename_files, extension, save=save, archive_file=archive_file)

                    if save:
                        target_file = full_filename
                        mode2 = 'w' + mode[1:]

                        if output_folder:
                            tarext = re.search(r"\.tar$|\.tar.gz$|\.tar.bz2$|\.tarz$|\.tar.bzip2$|\.tgz$", full_filename).group(0)
                            relative_filepath = os.path.relpath(target_file.replace(tarext, "." + extension + tarext), folder)
                            target_file = os.path.join(output_folder, relative_filepath)

                        print("---> archiving to", target_file)
                        file = tarfile.open(target_file, mode2)

                        for item in glob.glob(os.path.join(temp_out_directory, '*')):
                            relative_filepath = os.path.relpath(item, temp_out_directory)
                            file.add(item, relative_filepath)

                        file.close()

                    shutil.rmtree(temp_directory)
                    shutil.rmtree(temp_out_directory)

                except Exception:
                    pass  # File was not a tar archive

            if opened_dicom is None:
                print("... not a dicom file ... skipping")
                # logging.warning("Unable to identify %s as a dicom file or zip archive to search.", full_filename)
                continue
