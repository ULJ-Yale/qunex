#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``dicomdeid.py``
"""

import re
import os
import gzip
import glob
import tempfile
import zipfile
import tarfile
import csv
import random
import string
import functools
import struct
import shutil

import general.exceptions as ge

try:
    import pydicom
except:
    import dicom as pydicom

try:
    import pydicom.filereader as dfr
except:
    import dicom.filereader as dfr
    
#######################

# Discovery

#######################

dicom_counter = 0

def _at_frame(tag, VR, length):
    return tag == (0x5200, 0x9230)

def readDICOMBase(filename):
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
    except:
        return None, None
    finally:
        if f is not None and not f.closed:
            f.close()

def readDICOMFull(filename):
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
    except:
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
    except:
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
                    opened_dicom, gz = readDICOMFull(full_filename)
                else:    
                    opened_dicom, gz = readDICOMBase(full_filename)

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

            except Exception as e:
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

                except:
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

                except:
                    pass  # File was not a tar archive

            if opened_dicom is None:
                print("... not a dicom file ... skipping")
                # logging.warning("Unable to identify %s as a dicom file or zip archive to search.", full_filename)
                continue


#######################

# Scanning

#######################

field_dict = {}

def field_dict_modifier(node_id, node_path, node):
    """
    ``field_dict_modifier(node_id, node_path, node)``

    Adds the node_id node_element pair to field_dict with the provided 
    DataElement.

    INPUTS
    ======

    --node_id    The id (like 0x0194db21/0x238983d92) of the DataElement.
    --node_path  The path (like fieldname/innerfield) of the DataElement.
    --node       The DataElement whose value is being recorded.
    """
    value_list = field_dict.get((node_id, node_path), set())
    if isinstance(node.value, bytearray):
        if node.tag == 0x20001:
            value_list.add(str(node.value))
        else:
            value_list.add("POTENTIAL PHI; REMOVE: binary data")
    else:
        value_list.add(str(node.value))
    field_dict[(node_id, node_path)] = value_list

def recurse_tree(dataset, node_func, parent_id=None, parent_path=None, debug=False):
    """
    ``recurse_tree(dataset, node_func, parent_id=None, parent_path=None, debug=False)``

    Recursively steps through the levels of the dicom dataset, calling node_func
    on each DataElement found with its id and path.

    --dataset      The current level of the dicom.
    --node_func    The function to call on each node, which takes the node_id, 
                   node_path and dataElement as arguments.
    --parent_id    The id (like 0x0194db21/0x238983d92) of the parent or None if
                   this is the whole dicom.
    --parent_path  The path (like fieldname/innerfield) of the parent or None if
                   this is the whole dicom.
    """
    # order the dicom tags

    if debug:
        print(" ... recursing tree")

    for data_element in dataset:
        if data_element.name == "Pixel Data":
            continue

        if parent_id is None:
            node_id = from_tag(data_element.tag)
            data_element_name = data_element.name
            if data_element.name is None:
                data_element_name = from_tag(data_element.tag)
            node_path = data_element_name
        else:
            node_id = parent_id + "/" + from_tag(data_element.tag)
            data_element_name = data_element.name
            if data_element.name is None:
                data_element_name = from_tag(data_element.tag)
            node_path = parent_path + "/" + data_element_name

        if debug:
            print("         > node id:", node_id, "node path:", node_path, end=" ")
            print("> checking element type", end=" ")

        if isinstance(data_element.value, pydicom.Sequence):   # a sequence
            if debug:
                print("> a sequence")
            for dataset in data_element.value:
                recurse_tree(dataset, node_func, node_id, node_path)
        elif isinstance(data_element.value, pydicom.Dataset):
            if debug:
                print("> a dataset")
            recurse_tree(data_element.value, node_func, node_id, node_path)
        else:
            if debug:
                print("> an element")
            node_func(node_id, node_path, data_element)

    if debug:
        print(" ... end recursing")

def dicom_scan(opened_dicom, filename=""):
    recurse_tree(opened_dicom, field_dict_modifier)
    recurse_tree(opened_dicom.file_meta, field_dict_modifier)
    return opened_dicom

def write_field_dict(output_file, limit):
    with open(output_file, "w") as f:
        writer = csv.writer(f)
        for key, items in field_dict.items():
            row = [key[0], key[1]]
            row.extend(list(items)[:int(limit)])
            # limit length of printouts
            if (len(row[2]) <  128):
                writer.writerow(row)


def get_dicom_fields(folder=".", targetfile="dicom_fields.csv", limit="20"):
    """
    ``get_dicom_fields [folder=.] [targetfile=dicom_fields.csv] [limit=20]``

    Returns an overview of DICOM fields across all the DICOM files.

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
    except:
        raise ge.CommandFailed("get_dicom_fields", "Could not create target file", "The specifed target file could not be created:", "%s" % (targetfile), "Please check your paths and permissions!")


    field_dict = {}

    discover_dicom(folder, dicom_scan, save=False, archive_file="")
    write_field_dict(targetfile, limit)


#######################

# Reprocessing

#######################

DEFAULT_SALT = ''.join(random.choice(string.ascii_uppercase) for i in range(12))


def change_dicom_files(folder=".", paramfile="deidparam.txt", archivefile="archive.csv", outputfolder=None, extension="", replacementdate=None):
    """
    ``change_dicom_files [folder=.] [paramfile=deidparam.txt] [archivefile=archive.csv] [outputfolder=None] [extension=""] [replacementdate=]``

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
    except:
        raise ge.CommandFailed("change_dicom_files", "Could not create archive file", "The specifed archive file could not be created:", "%s" % (archivefile), "Please check your paths and permissions!")

    if outputfolder is not None and not os.path.exists(outputfolder):
            os.mkdir(outputfolder)

    manipulate_file = functools.partial(deid_and_date_removal, param_file=paramfile, archive_file=archivefile, replacement_date=replacementdate)
    discover_dicom(folder, manipulate_file, outputfolder, renamefiles, extension, save=True, archive_file=archivefile)

def date_removal_func(node_id, node_path, node, target_date, replace_date):
    """
    ``date_removal_func(node_id, node_path, node, target_date, replace_date)``

    INPUTS
    ======

    --node_id       The id (like /0x0194db21/0x238983d92) of the data element.
    --node_path     The path (like /field1name/innername) of the data element.
    --node          The data element in the dicom.
    --target_date   The date string to replace.
    --replace_date  The date string to replace the above string with.
    """
    if isinstance(node.value, str):
        node.value = node.value.replace(target_date, replace_date)

def strip_dates(dicom_file, replacement_date=None):
    """
    ``strip_dates(dicom_file, replacement_date=None)``

    INPUTS
    ======

    --dicom_file        The opened dicom file to strip dates from.
    --replacement_date  The date string to replace stripped dates with.
    """

    if "StudyDate" in dicom_file:
        target_date = dicom_file.StudyDate
    elif "SeriesDate" in dicom_file:
        target_date = dicom_file.SeriesDate
    else:
        print("     -> WARNING: No StudyDate field present")
        return

    if replacement_date is None:
        year = random.randint(1970, 2015)
        month = random.randint(1, 12)
        day = random.randint(1, 28)

        month_str = str(month)
        if len(month_str) == 1:
            month_str = "0" + month_str

        day_str = str(day)
        if len(day_str) == 1:
            day_str = "0" + day_str

        replacement_date = str(year) + month_str + day_str

    modified_removal_func = functools.partial(date_removal_func, target_date=target_date, replace_date=replacement_date)

    recurse_tree(dicom_file, modified_removal_func)
    recurse_tree(dicom_file.file_meta, modified_removal_func)

def read_spec_file(spec_file):
    """
    ``read_spec_file(spec_file)``
    
    Reads the spec file that specifies what actions to take with specific tags.

    INPUT
    =====

    --spec_file  the path to the spec file
    
    OUTPUT
    ======

    --action_dict  Action_dict is a mapping of keys to a set of actions.
    --replace_map  Replace_map is a mapping of keys to the value to replace 
                   their value with.

    USE
    ===

    Reads the spec file that specifies what actions to take with specific tags.

    Example spec file::

        0x80005  > delete
        0x100010 > delete
        0x80012  > archive,delete
        0x180032 > replace:20070101

    Operations are applied in this order:

    1. archive
    2. replace
    4. delete

    Lines that start with '#' or do not specify a mapping (i.e. lack '>') are
    ignored.
    """

    actionOrder = ['archive', 'replace', 'delete']

    action_dict = {}
    replace_map = {}
    lineNumber  = 0

    with open(spec_file, 'r') as f:
        for line in f:
            lineNumber += 1
            line = line.strip()
            if len(line) > 0:
                if line[0] != "#" and ">" in line:
                    line    = line.split(">")
                    key     = line[0].strip()
                    actions = [e.strip() for e in line[1].split(",")]

                    if key not in action_dict:
                        action_dict[key] = []
                    else:
                        print("---> Warning, actions for tag %s specified more than once! [line: %d]" % (key, lineNumber))

                    for action in actions:
                        if "replace" in action:
                            parts = [e.strip() for e in action.split(':')]
                            if len(parts) == 2:
                                action, replacement = parts
                                replace_map[key] = replacement
                            else:
                                print("---> Warning, no replacement specified, skipping replacement! [line %d: %s]" % (lineNumber, action))

                        action_dict[key].append(action)

    for key in action_dict:
        action_dict[key] = [e for e in actionOrder if e in action_dict[key]]

    return action_dict, replace_map

def action_resolver(key, action, action_dict, replace_map):
    action_set = action_dict.get(key, set())

    if action == "archive":
        action_set.add(action)
    elif action == "delete":
        action_set.add(action)
    elif action.startswith("replace:"):
        action_set.add("replace")
        replace_value = ":".join(action.split(":")[1:])
        replace_map[key] = replace_value
    else:
        raise RuntimeError(action + " is not a valid action.")

    action_dict[key] = action_set

def archive(target_dicom, tag, field_id, filename, archive_csv_writer):
    """
    ``archive(target_dicom, tag, field_id, filename, archive_csv_writer)``

    Archive the field from the dicom.

    INPUTS
    ======

    --target_dicom        The dicom dataset one level above the element to apply
                          this action to.
    --tag                 The tag to the data element is located at in
                          target_dicom.
    --field_id            The full id (like /0x0194db21/0x238983d92) of the
                          element.
    --filename            The filename for this dicom.
    --archive_csv_writer  The csv.Writer object to write the archive to.
    """
    if isinstance(target_dicom, pydicom.Dataset):
        value = str(target_dicom.get(tag))
        archive_csv_writer.writerow([filename, field_id, value])

def replace(target_dicom, tag, field_id, filename, replace_map):
    """
    ``replace(target_dicom, tag, field_id, filename, replace_map)``

    INPUTS
    ======

    --target_dicom   The dicom dataset one level above the element to apply this
                     action to.
    --tag            The tag to the data element is located at in target_dicom.
    --field_id       The full id (like /0x0194db21/0x238983d92) of the element
                     to archive.
    --filename       The filename for this dicom.
    --replace_map    The map of field ids to the values to replace them with.
    """
    replace_result_string = replace_map[field_id]

    if isinstance(target_dicom, pydicom.Sequence):
        for elt in target_dicom:
            if isinstance(elt, pydicom.Dataset) and tag in elt:
                elt[tag].value = replace_result_string
    else:
        if isinstance(target_dicom, pydicom.Dataset) and tag in target_dicom:
            target_dicom[tag].value = replace_result_string

def delete(target_dicom, tag, field_id, filename):
    """
    ``delete(target_dicom, tag, field_id, filename)``

    Delete the field from the dicom.

    INPUTS
    ======

    --target_dicom  The dicom dataset one level above the element to apply this 
                    action to.
    --tag           The tag to the data element is located at in target_dicom.
    --field_id      The full id (like /0x0194db21/0x238983d92) of the element.
    --filename      The filename for this dicom.
    """
    if isinstance(target_dicom, pydicom.Dataset):
        target_dicom.pop(tag, None)

def get_group(full_id):
    """
    ``get_group(full_id)``

    Gets the group from the full id of a DataElement.
    
    INPUT
    =====

    --full_id  The id (like 0x0194db21/0x238983d92) of the element.

    OUTPUT
    ======

    Returns the group id as a number.
    """

    try:
        tag = get_tag(full_id.split("/")[0])
        return tag
    except TypeError as e:
        raise e

def apply_action_from_field_id(opened_dicom, field_id, apply_func, filename):
    """
    ``apply_action_from_field_id(opened_dicom, field_id, apply_func, filename)``

    Apply the apply_func to the data element/s at the field id specified in the 
    dicom provided.

    INPUTS
    ======
    
    --opened_dicom  The opened dicom file.
    --field_id      The id (like /0x0194db21/0x238983d92) to apply the function 
                    to.
    --apply_func    The function to apply.
    """
    field_path = field_id.split('/')
    field_path_int = [get_tag(x) for x in field_path]

    group = get_group(field_id)

    if group == 0x02:
        targets = [opened_dicom.file_meta]
    else:
        targets = [opened_dicom]

    for tag in field_path_int[:-1]:
        new_targets = []
        for target in targets:
            new_target = target.get(tag)
            if isinstance(new_target, pydicom.Sequence):
                for elt in new_target:
                    new_targets.append(elt)
            else:
                new_targets.append(new_target)

        targets = new_targets

    for target in targets:
        apply_func(target, field_path_int[-1], field_id, filename)

def deid(opened_dicom, param_file="", archive_file="", filename=""):
    action_dict, replace_map = read_spec_file(param_file)

    archive_writer = csv.writer(open(archive_file, mode='a'))
    for key in action_dict:
        for action in action_dict[key]:
            if action == 'archive':
                apply_func = functools.partial(archive, archive_csv_writer=archive_writer)
            elif action == 'replace':
                apply_func = functools.partial(replace, replace_map=replace_map)
            elif action == 'delete':
                apply_func = delete
            else:
                raise RuntimeError("SHOULD NEVER HAPPEN")

            group = get_group(key)
            if group == "0x02":
                apply_action_from_field_id(opened_dicom.file_meta, key, apply_func, filename)
            else:
                apply_action_from_field_id(opened_dicom, key, apply_func, filename)
    return opened_dicom

def deid_and_date_removal(opened_dicom, param_file="", archive_file="", replacement_date=None, filename=""):
    deid(opened_dicom, param_file, archive_file, filename)
    strip_dates(opened_dicom, replacement_date)
    return opened_dicom

def from_tag(tag_value):
    """
    ``from_tag(tag_value)``

    Gets the tag string from its value.

    INPUT
    =====
    
    --tag_value  The integer tag value.
    
    OUTPUT
    ======

    Returns the tag hex string (like 0xd73829b1).
    """
    return hex(tag_value)

def get_tag(tag_string):
    """
    ``get_tag(tag_string)``

    Gets the individual tag from the string representation.

    INPUT
    =====

    --tag_string  The tag hex string (like 0xd73829b1).

    OUTPUT
    ======

    Returns the integer tag value.
    """
    removed = tag_string.lstrip("0x")
    if len(removed) < 8:
        removed = "0"*(8-len(removed)) + removed
    hex = bytes.fromhex(removed)
    decoded = struct.unpack(">I", hex)[0]
    return decoded
