#!/usr/bin/env python
# encoding: utf-8

import os
import gzip
import logging
import tempfile
import zipfile
import tarfile
import csv
import hashlib
import json
import random
import string
import functools
import base64
import struct
import shutil

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
    try:
        if '.gz' in filename:
            f = gzip.open(filename, 'r')
        else:
            f = open(filename, 'r')
        d = dfr.read_partial(f, stop_when=_at_frame)
        f.close()
        return d
    except:
        # return None
        # print " ===> WARNING: Could not partial read dicom file, attempting full read! [%s]" % (filename)
        try:
            d = dfr.read_file(filename, stop_before_pixels=True)
            return d
        except:
            # print " ===> ERROR: Could not read dicom file, aborting. Please check file: %s" % (filename)
            return None


def get_dicom_name(opened_dicom, extension="dcm"):
    global dicom_counter
    dicom_counter += 1

    s_id = ""
    if "PatientID" in opened_dicom:
        s_id = opened_dicom.PatientID
    elif "StudyID" in opened_dicom:
        s_id = opened_dicom.StudyID

    sequence_id = str(opened_dicom.SeriesNumber)
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


def discoverDICOM(folder, deid_function, output_folder=None, rename_files=False, extension=""):
    """
    Given a folder name, looks for DICOMs in nested subfolders, zip files, gzip files
    and tar files and runs the function deid_function on each dicom it finds

    :param folder: the folder path to search for dicoms
    :param deid_function: the function to run on each dicom file
    :param output_folder: the folder to write the dicoms to, or inplace if None
    :param rename_files: if output_folder is provided, whether to rename the files. This renames
        the files inside zip and tar files, not the zip or tar files themselves.
    :param extension: if rename_files is true, the additional characters to put after the extension
        (like abc.dcm{extension})
    :return: None
    """
    if output_folder is None and rename_files:
        raise RuntimeError("Files can only be renamed if they are being saved"
                           " in a different location.  Please provide output_folder"
                           " as an argument.")

    for (dirpath, dirnames, filenames) in os.walk(folder):
        for filename in filenames:
            full_filename = os.path.join(dirpath, filename)

            print "---> Inspecting", full_filename

            opened_dicom = None

            try:
                # opened_dicom = pydicom.dcmread(full_filename, stop_before_pixels=True)
                opened_dicom = readDICOMBase(full_filename)

                if opened_dicom:
                    print "     ... read as dicom"

                modified_dicom = deid_function(opened_dicom)

                

                if output_folder is None:
                    output_file = full_filename
                else:
                    if rename_files:
                        output_file = os.path.join(output_folder, get_dicom_name(modified_dicom), "dcm"+extension)
                    else:
                        relative_filepath = os.path.relpath(full_filename, folder)
                        output_file = os.path.join(output_folder, relative_filepath)

                modified_dicom.save_as(output_file)
            except Exception as e:
                pass  # file was not a dicom

            if opened_dicom is None:
                try:
                    file = gzip.open(full_filename, mode='rb')
                    opened_dicom = pydicom.dcmread(file, stop_before_pixels=True)
                    modified_dicom = deid_function(opened_dicom)
                    file.close()

                    if opened_dicom:
                        print "     ... read as gzipped dicom"

                    if output_folder is None:
                        file = gzip.open(full_filename, mode='wb')
                    else:
                        if rename_files:
                            new_filepath = os.path.join(dirpath, get_dicom_name(modified_dicom), "dcm.gz"+extension)
                        else:
                            relative_filepath = os.path.relpath(full_filename, folder)
                            new_filepath = os.path.join(output_folder, relative_filepath)
                        file = gzip.open(new_filepath, mode='wb')

                    modified_dicom.save_as(file)

                except Exception as e:
                    pass  # file was not a gzipped DICOM

            if opened_dicom is None:
                try:
                    file = zipfile.ZipFile(full_filename)
                    temp_directory = tempfile.mkdtemp("_".join(full_filename.split("/")))
                    file.extractall(temp_directory)
                    file.close()

                    if opened_dicom:
                        print "     ... extracted as a zip file"

                    opened_dicom = True

                    discoverDICOM(temp_directory, deid_function, output_folder, rename_files, extension)

                    if output_folder is None:
                        file = zipfile.ZipFile(full_filename, mode='w')
                    else:
                        relative_filepath = os.path.relpath(full_filename, folder)
                        new_filepath = os.path.join(output_folder, relative_filepath)
                        file = zipfile.ZipFile(new_filepath, mode='w')

                    for (dirpath_2, dirnames_2, filenames_2) in os.walk(temp_directory):
                        for filename_2 in filenames_2:
                            full_path_2 = os.path.join(dirpath_2, filename_2)
                            relative_filepath_2 = os.path.relpath(full_path_2, temp_directory)
                            file.write(full_path_2, relative_filepath_2)

                    shutil.rmtree(temp_directory)

                except:
                    pass  # File was not a zip archive

            if opened_dicom is None:
                try:
                    file = tarfile.open(full_filename)
                    mode = file.mode
                    temp_directory = tempfile.mkdtemp("_".join(full_filename.split("/")))
                    file.extractall(temp_directory)
                    file.close()

                    if opened_dicom:
                        print "     ... extracted as a tar file"

                    opened_dicom = True

                    discoverDICOM(temp_directory, deid_function, output_folder, rename_files, extension)

                    mode2 = 'w' + mode[1:]

                    if output_folder is None:
                        file = tarfile.open(full_filename, mode=mode2)
                    else:
                        relative_filepath = os.path.relpath(full_filename, folder)
                        new_filepath = os.path.join(output_folder, relative_filepath)
                        file = tarfile.open(new_filepath, mode2)

                    for (dirpath_2, dirnames_2, filenames_2) in os.walk(temp_directory):
                        for filename_2 in filenames_2:
                            full_path_2 = os.path.join(dirpath_2, filename_2)
                            relative_filepath_2 = os.path.relpath(full_path_2, temp_directory)
                            file.write(full_path_2, relative_filepath_2)

                    shutil.rmtree(temp_directory)

                except:
                    pass  # File was not a tar archive

            if opened_dicom is None:
                logging.warning("Unable to identify %s as a dicom file or zip archive to search.", full_filename)
                continue


#######################

# Scanning

#######################


field_dict = {}


def field_dict_modifier(node_id, node_path, node):
    """Add the node_id node_element pair to field_dict with the provided DataElement

    :param node_id: the id (like 0x0194db21/0x238983d92) of the DataElement
    :type node_id: str
    :param node_path: the path (like fieldname/innerfield) of the DataElement
    :type node_path: str
    :param node: the DataElement whose value is being recorded
    :type node: pydicom.DataElement
    :return: None
    :rtype: None
    """
    value_list = field_dict.get((node_id, node_path), set())
    if isinstance(node.value, bytearray):
        if node.tag == 0x20001:
            value_list.add(str(node.value))
        else:
            value_list.add("POTENTIAL PHI; REMOVE: binary data")
    else:
        value_list.add(str(node.value))
    print "          >", value_list
    field_dict[(node_id, node_path)] = value_list


def recurse_tree(dataset, node_func, parent_id=None, parent_path=None):
    """Recursively step through the levels of the dicom dataset, calling node_func on each DataElement found with its
    id and path

    :param dataset: The current level of the dicom
    :type dataset: pydicom.Dataset
    :param node_func: The function to call on each node, which takes the node_id, node_path and dataElement as arguments
    :type node_func: Callable[[str, str, pydicom.DataElement], None]
    :param parent_id: the id (like 0x0194db21/0x238983d92) of the parent or None if this is the whole dicom
    :type parent_id: str
    :param parent_path: the path (like fieldname/innerfield) of the parent or None if this is the whole dicom
    :type parent_path: str
    :return: None
    :rtype: None
    """
    # order the dicom tags

    print "     ... recursing tree"

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

        print "         > node id:", node_id, "node path:", node_path
        print "         > checking element type"

        if isinstance(data_element.value, pydicom.Sequence):   # a sequence
            print "          > a sequence"
            for dataset in data_element.value:
                recurse_tree(dataset, node_func, node_id, node_path)
        elif isinstance(data_element.value, pydicom.Dataset):
            print "          > a dataset"
            recurse_tree(data_element.value, node_func, node_id, node_path)
        else:
            print "          > processing"
            node_func(node_id, node_path, data_element)

    print "     ... end recursing"


def dicom_scan(opened_dicom):
    recurse_tree(opened_dicom, field_dict_modifier)
    recurse_tree(opened_dicom.file_meta, field_dict_modifier)
    return opened_dicom


def write_field_dict(output_file, limit):
    with open(output_file, "w") as f:
        writer = csv.writer(f)
        for key, items in field_dict.items():
            row = [key[0], key[1]]
            row.extend(list(items)[:limit])
            writer.writerow(row)


def run_scanning(folder_to_scan, output_file, limit=None):
    discoverDICOM(folder_to_scan, dicom_scan)
    write_field_dict(output_file, limit)


#######################

# Reprocessing

#######################


DEFAULT_SALT = ''.join(random.choice(string.ascii_uppercase) for i in range(12))


def run_deid(folder_to_scan, param_file, archive_file, output_folder=None, rename_files=False, extension="",
             replacement_date=None):
    if output_folder is not None:
        try:
            shutil.rmtree(output_folder)
        except:
            pass
        os.mkdir(output_folder)
    manipulate_file = functools.partial(deid_and_date_removal, param_file=param_file, archive_file=archive_file,
                                        replacement_date=replacement_date)
    discoverDICOM(folder_to_scan, manipulate_file, output_folder, rename_files, extension)


def deid_and_date_removal(opened_dicom, param_file="", archive_file="", replacement_date=None):
    deid(opened_dicom, param_file, archive_file)
    strip_dates(opened_dicom, replacement_date)
    return opened_dicom


def from_tag(tag_value):
    """Get the tag string from its value

    :param tag_value: the integer tag value
    :type tag_value: int
    :return: the tag hex string (like 0xd73829b1)
    :rtype: str
    """
    hex_tag = hex(tag_value)
    if hex_tag[-1] != "L":
        raise RuntimeError(
            "Something went horribly wrong. Hex conversion does not end in 'L'")
    return hex_tag[:-1]


def get_tag(tag_string):
    """Get the individual tag from the string representation

    :param tag_string: the tag hex string (like 0xd73829b1)
    :type tag_string: str
    :return: the integer tag value
    :rtype: int
    """
    removed = tag_string.lstrip("0x")
    if len(removed) < 8:
        removed = "0"*(8-len(removed)) + removed
    decoded = removed.decode('hex')
    return struct.unpack(">I", decoded)[0]


def get_group(full_id):
    """Get the group from the full id of a DataElement

    :param full_id: the id (like 0x0194db21/0x238983d92) of the element
    :type full_id: str
    :return: the group id as a number
    :rtype: int
    """
    try:
        return struct.pack(">I", get_tag(full_id.split("/")[0]))
    except TypeError as e:
        raise e


def deid(opened_dicom, param_file="", archive_file=""):
    action_dict, replace_map, hasher_map = read_spec_file(param_file)

    archive_writer = csv.writer(open(archive_file, mode='a'))

    for key in action_dict:
        for action in action_dict[key]:
            if action == 'archive':
                apply_func = functools.partial(archive, archive_csv_writer=archive_writer)
            elif action == 'hash':
                apply_func = functools.partial(hash, hasher_map=hasher_map)
            elif action == 'replace':
                apply_func = functools.partial(replace, replace_map=replace_map)
            elif action == 'delete':
                apply_func = delete
            else:
                raise RuntimeError("SHOULD NEVER HAPPEN")

            group = get_group(key)
            if group == 0x02:
                apply_action_from_field_id(opened_dicom.file_meta, key, apply_func)
            else:
                apply_action_from_field_id(opened_dicom, key, apply_func)

    return opened_dicom


def read_spec_file(spec_file):
    """Reads the spec file, which specifies what actions to take with specific tags.

    Example spec file:

    0x80005 > archive, delete
    fieldname3 > hash: sdh2083uddoqew
    fieldname5 > archive, hash:random
    fieldname7 > hash: sdh2083uddoqew

    0x80005  > delete
    0x100010 > delete
    0x80012  > delete, archive
    0x82112  > hash, archive
    0x180022 > hash:qrklejwrlke, archive
    0x180032 > replace:20070101

    Operations are applied in this order: archive, hash, replace, delete

    Lines that start with '#' or do not specify a mapping (i.e. lack '>') are ignored.

    :param spec_file: the path to the spec file
    :return: (action_dict, replace_map, hasher_map), action_dict is a mapping of keys to a set of actions,
    replace_map is a mapping of keys to the value to replace their value with, hasher map is a map of keys
    to the salt to use for the hash function
    """

    actionOrder = ['archive', 'hash', 'replace', 'delete']

    action_dict = {}
    replace_map = {}
    hasher_map  = {}
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
                        print("===> Warning, actions for tag %s specified more than once! [line: %d]" % (key, lineNumber))

                    for action in actions:
                        if "hash" in action:
                            parts = [e.strip() for e in action.split(':')]
                            if len(parts) == 2:
                                action, salt = parts
                            else:
                                action = "hash"
                                salt   = ""
                            hasher_map[key] = salt

                        if "replace" in action:
                            parts = [e.strip() for e in action.split(':')]
                            if len(parts) == 2:
                                action, replacement = parts
                                replace_map[key] = replacement
                            else:
                                print("===> Warning, no replacement specified, skipping replacement! [line %d: %s]" % (lineNumber, action))

                        action_dict[key].append(action)

    for key in action_dict:
        action_dict[key] = [e for e in actionOrder if e in action_dict[key]]

    return action_dict, replace_map, hasher_map

def read_param_file(param_file):
    """Reads the parameter file which specifies the actions to take

    Example param file:
    {
      "0x80005": "delete",
      "0x100010": [ "delete" ],
      "0x80012": [
        "delete",
        "archive"
      ],
      "0x82112/0x81150": [
        "hash",
        "archive"
      ],
      "0x180022": [
        "hash:qrklejwrlke",
        "archive"
      ],
      "0x180022": "replace:20070101",
    }

    Single operations may be in a list or not.  Operations are applied in this order:
    archive, hash, replace, delete

    :param param_file: the path to the param file
    :return: (action_dict, replace_map, hasher_map), action_dict is a mapping of keys to a set of actions,
    replace_map is a mapping of keys to the value to replace their value with, hasher map is a map of keys
    to the salt to use for the hash function
    """
    file_dict = json.load(open(param_file))

    action_dict = {}
    replace_map = {}
    hasher_map = {}

    for key, value in file_dict.items():
        if isinstance(value, str):
            action_resolver(key, value, action_dict, replace_map, hasher_map)
        elif isinstance(value, list):
            for elt in value:
                action_resolver(key, elt, action_dict, replace_map, hasher_map)
        else:
            raise RuntimeError(param_file + " is improperly structured.")

    return action_dict, replace_map, hasher_map


def action_resolver(key, action, action_dict, replace_map, hasher_map):
    action_set = action_dict.get(key, set())

    if action == "archive":
        action_set.add(action)
    elif action == "delete":
        action_set.add(action)
    elif action.startswith("replace:"):
        action_set.add("replace")
        replace_value = ":".join(action.split(":")[1:])
        replace_map[key] = replace_value
    elif action.startswith("hash"):
        action_set.add("hash")
        if action.startswith("hash:"):
            salt = ":".join(action.split(":")[1:])
        else:
            if action != "hash":
                raise RuntimeError(action + " is not a valid action.")
            salt = DEFAULT_SALT

        hasher_map[key] = salt
    else:
        raise RuntimeError(action + " is not a valid action.")

    action_dict[key] = action_set


def replace(target_dicom, tag, field_id, filename, replace_map):
    """

    :param target_dicom: The dicom dataset one level above the element to apply this action to
    :type target_dicom: pydicom.Dataset
    :param tag: the tag to the data element is located at in target_dicom
    :type tag: int
    :param field_id: the full id (like /0x0194db21/0x238983d92) of the element to archive
    :type field_id: str
    :param filename: the filename for this dicom
    :type filename: str
    :param replace_map: the map of field ids to the values to replace them with
    :type replace_map: dict[str, str]
    :return: None
    :rtype: None
    """
    replace_result_string = replace_map[field_id]

    if isinstance(target_dicom, pydicom.Sequence):
        for elt in target_dicom:
            if isinstance(elt, pydicom.Dataset) and tag in elt:
                elt[tag].value = replace_result_string
    else:
        if isinstance(target_dicom, pydicom.Dataset) and tag in target_dicom:
            target_dicom[tag].value = replace_result_string


def hash_one_value(value, salt):
    """Apply the hash function to one value

    :param value: the value to hash
    :type value: str
    :param salt: the salt to use for the hash
    :type salt: str
    :return: the hashed value converted to remove special characters
    :rtype: str
    """
    hashed = hashlib.pbkdf2_hmac('sha256', bytearray(value), bytearray(salt), 100000)
    return base64.b64encode(hashed)


def hash(target_dicom, tag, field_id, filename, hasher_map):
    """Hash the value in the field in this dicom

    :param target_dicom: The dicom dataset one level above the element to apply this action to
    :type target_dicom: pydicom.Dataset
    :param tag: the tag to the data element is located at in target_dicom
    :type tag: int
    :param field_id: the full id (like /0x0194db21/0x238983d92) of the element to archive
    :type field_id: str
    :param filename: the filename for this dicom
    :type filename: str
    :param hasher_map: the map from field ids to the salt to use for their hash
    :type hasher_map: dict[str, str]
    :return: None
    :rtype: None
    """
    salt = hasher_map[field_id]

    if isinstance(target_dicom, pydicom.Sequence):
        for elt in target_dicom:
            if isinstance(elt, pydicom.Dataset) and elt in target_dicom:
                elt[tag].value = hash_one_value(str(elt[tag].value), salt)
    else:
        if isinstance(target_dicom, pydicom.Dataset) and tag in target_dicom:
            target_dicom[tag].value = hash_one_value(str(target_dicom[tag].value), salt)


def delete(target_dicom, tag, field_id, filename):
    """Delete the field from the dicom

    :param target_dicom: The dicom dataset one level above the element to apply this action to
    :type target_dicom: pydicom.Dataset
    :param tag: the tag to the data element is located at in target_dicom
    :type tag: int
    :param field_id: the full id (like /0x0194db21/0x238983d92) of the element
    :type field_id: str
    :param filename: the filename for this dicom
    :type filename: str
    :return: None
    :rtype: None
    """
    if isinstance(target_dicom, pydicom.Dataset):
        target_dicom.pop(tag, None)


def archive(target_dicom, tag, field_id, filename, archive_csv_writer):
    """Archive the field from the dicom

    :param target_dicom: The dicom dataset one level above the element to apply this action to
    :type target_dicom: pydicom.Dataset
    :param tag: the tag to the data element is located at in target_dicom
    :type tag: int
    :param field_id: the full id (like /0x0194db21/0x238983d92) of the element
    :type field_id: str
    :param filename: the filename for this dicom
    :type filename: str
    :param archive_csv_writer: the csv.Writer object to write the archive to
    :type archive_csv_writer: csv.Writer
    :return: None
    :rtype: None
    """
    if isinstance(target_dicom, pydicom.Dataset):
        value = str(target_dicom.get(tag))
        archive_csv_writer.writerow([filename, field_id, value])


def apply_action_from_field_id(opened_dicom, field_id, apply_func):
    """Apply the apply_func to the data element/s at the field id specified in the dicom provided

    :param opened_dicom: the opened dicom file
    :type opened_dicom: pydicom.Dataset
    :param field_id: the id (like /0x0194db21/0x238983d92) to apply the function to
    :type field_id: str
    :param apply_func: the function to apply
    :type apply_func: Callable[[pydicom.Dataset, int, str, str], None]
    :return: None
    :rtype: None
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
        apply_func(target, field_path_int[-1], field_id, opened_dicom.filename)


def strip_dates(dicom_file, replacement_date=None):
    """
    :param dicom_file: the opened dicom file to strip dates from
    :type dicom_file: pydicom.FileDataset
    :param replacement_date: the date string to replace stripped dates with
    :type replacement_date: str
    :return: None
    :rtype: None
    """
    target_date = dicom_file.StudyDate

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


def date_removal_func(node_id, node_path, node, target_date, replace_date):
    """
    :param node_id: the id (like /0x0194db21/0x238983d92) of the data element
    :type node_id: str
    :param node_path: the path (like /field1name/innername) of the data element
    :type node_path: str
    :param node: the data element in the dicom
    :type node: pydicom.DataElement
    :param target_date: the date string to replace
    :type target_date: str
    :param replace_date: the date string to replace the above string with
    :type replace_date: str
    :return: None
    :rtype: None
    """
    if isinstance(node.value, str):
        node.value = node.value.replace(target_date, replace_date)


"""

if __name__ == "__main__":
    run_scanning("/Users/antonijakolobaric/Desktop/0702/dicoms",
                 "/Users/antonijakolobaric/Desktop/0702/dicoms/Output.csv",
                 20)


if __name__ == "__main__":
    run_deid("/Users/antonijakolobaric/Desktop/0702/dicoms",
             "/Users/antonijakolobaric/Desktop/0702/dicoms/test_config",
             "/Users/antonijakolobaric/Desktop/0702/dicoms/archive.csv",
             "/Users/antonijakolobaric/Desktop/0702/dicoms_output")

"""