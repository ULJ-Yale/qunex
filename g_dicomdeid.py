#!/usr/bin/env python
# encoding: utf-8

import re
import os
import gzip
import glob
import logging
import tempfile
import zipfile
import tarfile
import csv
import hashlib
import random
import string
import functools
import base64
import struct
import shutil
import collections
import niutilities.g_exceptions as ge

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
            f = gzip.open(filename, 'r')
            gz = True
        else:
            f = open(filename, 'r')
        d = dfr.read_partial(f, stop_when=_at_frame)
        f.close()
        if not d:
            raise ValueError
        return d, gz
    except:
        try:
            if '.gz' in filename:
                f = gzip.open(filename, 'r')
                gz = True
            else:
                f = open(filename, 'r')
            d = dfr.read_file(f, stop_before_pixels=True)
            return d, gz
        except:
            return None, None


def readDICOMFull(filename):
    # read the full dicom file
    try:
        if '.gz' in filename:
            f = gzip.open(filename, 'r')
            gz = True
        else:
            f = open(filename, 'r')
            gz = False
        d = dfr.read_file(f)
        f.close()
        return d, gz
    except:
        return None


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


def discoverDICOM(folder, deid_function, output_folder=None, rename_files=False, extension="", save=False, archive_file=""):
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
        raise ge.CommandFailed("discoverDICOM", "Output folder not specified", "Files can only be renamed if they are being saved in a different location.", "Please provide output_folder as an argument!")

    for (dirpath, dirnames, filenames) in os.walk(folder):
        for filename in filenames:
            full_filename = os.path.join(dirpath, filename)

            print "---> Inspecting", full_filename

            opened_dicom = None

            try:
                # opened_dicom = pydicom.dcmread(full_filename, stop_before_pixels=True)
                if save:
                    opened_dicom, gz = readDICOMFull(full_filename)
                else:    
                    opened_dicom, gz = readDICOMBase(full_filename)

                if opened_dicom:
                    print "     ... read as dicom"

                modified_dicom = deid_function(opened_dicom, filename=os.path.relpath(full_filename, folder))
                print "     ... processed"

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

                    print "     -> saving to", output_file
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

                    print " ... extracted as a zip file"

                    discoverDICOM(temp_directory, deid_function, temp_out_directory, rename_files, extension, save=save, archive_file=archive_file)

                    if save:
                        target_file = full_filename

                        if output_folder:
                            relative_filepath = os.path.relpath(target_file.replace('.zip', "." + extension + '.zip'), folder)
                            target_file = os.path.join(output_folder, relative_filepath)
                        
                        print "===> zipping to", target_file
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

                    print " ... extracted as a tar file"                    

                    opened_dicom = True

                    discoverDICOM(temp_directory, deid_function, temp_out_directory, rename_files, extension, save=save, archive_file=archive_file)

                    if save:
                        target_file = full_filename
                        mode2 = 'w' + mode[1:]

                        if output_folder:
                            tarext = re.search("\.tar$|\.tar.gz$|\.tar.bz2$|\.tarz$|\.tar.bzip2$", full_filename).group(0)
                            relative_filepath = os.path.relpath(target_file.replace(tarext, "." + extension + tarext), folder)
                            target_file = os.path.join(output_folder, relative_filepath)

                        print "====> archiving to", target_file
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
                print "... not a dicom file ... skipping"
                # logging.warning("Unable to identify %s as a dicom file or zip archive to search.", full_filename)
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
    field_dict[(node_id, node_path)] = value_list


def recurse_tree(dataset, node_func, parent_id=None, parent_path=None, debug=False):
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

    if debug:
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

        if debug:
            print "         > node id:", node_id, "node path:", node_path, 
            print "> checking element type", 

        if isinstance(data_element.value, pydicom.Sequence):   # a sequence
            if debug:
                print "> a sequence"
            for dataset in data_element.value:
                recurse_tree(dataset, node_func, node_id, node_path)
        elif isinstance(data_element.value, pydicom.Dataset):
            if debug:
                print "> a dataset"
            recurse_tree(data_element.value, node_func, node_id, node_path)
        else:
            if debug:
                print "> an element"
            node_func(node_id, node_path, data_element)

    if debug:
        print "     ... end recursing"


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
            writer.writerow(row)


def getDICOMFields(folder=".", tfile="dicomFields.csv", limit="20"):
    '''
    getDICOMFields [folder=.] [tfile=dicomFields.csv] [limit=20]

    USE
    ===

    The command is used to get an overview of DICOM fields across all the DICOM
    files in the study with example values, with the goal of identifying
    those fields that might carry personally identifiable information.

    PARAMETERS
    ==========

    --folder    The base folder to search for DICOM files. 
                The command will try to locate all valid DICOM files
                within the specified folder and its subfolders. [.]
    --tfile     The name (and path) of the file to store the information
                in. [dicomFields.csv]
    --limit     The maximum number of example values to provide for each of the
                DICOM fields. [20]

    RESULTS
    =======

    After running, the command will inspect all the valid DICOM files (including
    gzip compressed ones) in the specified folder and its subfolders. It will 
    generate a report file that will list all the DICOM fields found across all 
    the DICOM files. For each of the fields, the command will list example values
    up to the specified limit. The list will be saved as a comma separated values
    (csv) file.

    This file can be used to identify the fields that might carry personally
    identifiable information and therefore need to be processed appropriately. 

    EXAMPLE USE
    ===========

    gmri getDICOMFields

    gmri getDICOMFields \
         --folder=/data/studies/WM/subjects/inbox/MR 

    gmri getDICOMFields \
         --folder=/data/studies/WM/subjects/inbox/MR/original \
         --tfile=/data/studies/WM/subjects/specs/dicomFields.csv \
         --limit=10

    ----------------
    Written by Antonija Kolobarić

    Changelog
    2018-10-24 Grega Repovš
             - Updated documentation
             – Changed parameter names to match the convention and use elsewhere
             - Added input parameter checks
    2018-11-11 Grega Repovš
             - The command does not change/save the files anymore
             - More robust checking of parameters             
    '''

    if not os.path.exists(folder):
        raise ge.CommandFailed("getDICOMFields", "Folder not found", "The specified folder with DICOM files to analyse was not found:", "%s" % (folder), "Please check your paths!")

    try:
        f = open(tfile, "w")
        f.close()
    except:
        raise ge.CommandFailed("getDICOMFields", "Could not create target file", "The specifed target file could not be created:", "%s" % (tfile), "Please check your paths and permissions!")


    field_dict = {}

    discoverDICOM(folder, dicom_scan, save=False, archive_file="")
    write_field_dict(tfile, limit)


#######################

# Reprocessing

#######################


DEFAULT_SALT = ''.join(random.choice(string.ascii_uppercase) for i in range(12))

def changeDICOMFiles(folder=".", paramfile="deidparam.txt", archivefile="archive.csv", outputfolder=None, extension="", replacementdate=None):
    '''
    changeDICOMFiles [folder=.] [paramfile=deidparam.txt] [archivefile=archive.csv] [outputfolder=None] [extension=""] [replacementdate=]

    USE
    ===

    The command is used to change all the dicom files in the specified folder
    according to directions provided in the `paramfile`. The values to be 
    archived are saved (appended) to `archivefile` as a comma separated values 
    formatted file. The dicom files can be either changed in place or saved to 
    the specified `outputfolder` and optionally renamed by adding the specified
    `extension`. 


    PARAMETERS
    ==========

    --folder            The base folder from which the search for DICOM files 
                        should start. The command will try to locate all valid 
                        DICOM files within the specified folder and its 
                        subfolders. [.]
    --paramfile         The path to the parameter file that specifies what 
                        actions to perform on the dicom fields. [deidparam.txt]
    --archivefile       The path to the file in which values to be archived are 
                        to be stored. [archive.csv]
    --outputfolder      The optional path to the folder to which the modified 
                        dicom files are to be saved. If not specified, the dicom 
                        files are changed in place (overwriten). []
    --extension         An optional extension to be added to each modified dicom 
                        file name. The extension can be applied only when files 
                        are copied to the `outputfolder`. []
    --replacementdate   The date to replace all instances of StudyDate in the
                        file. []


    PARAMETER FILE
    ==============

    Parameter file is a text file that specifies the operations that are to be 
    performed on the fields in the dicom files. The default name for the 
    parameter file is `deidparam.txt`, however any other name can be used. The
    operations to be performed are specifed one dicom field per line in the
    format:

    <dicom field>  > <action>[:<parameter>], <action>[:<parameter>]

    Dicom field is the hexdecimal code of the field, which can be found in
    the first column of the readDICOMfields output csv. The list of actions
    is a comma separated list of commands and their optional parameters. 
    The possible actions are:

    archive  ... Archive the original value in the archive file.
    hash     ... Replace the original value with the hashed value. An optional
                 salt can be specified.
    replace  ... Replace the original value with the specified value.
    delete   ... Delete the field from the dicom file.
    
    If multiple actions are specified, they are carried out in the above order
    (archive, hash, replace, delete). When hashing, to prevent the possibility
    of reconstructing the original value by hashing candidate values, a salt 
    is used. By default a random salt is generated each time changeDICOMFiles 
    is run, however, a specific salt can be provided as the optional parameter
    to the `hash` command. A random salt can also be explictly specified by 
    setting the optinal parameter to 'random'.

    Lines in the parmeter file that start with '#' or do not specify a mapping 
    (i.e. lack '>') are ignored.

    Example spec file:
    ------------------

    0x80005  > delete
    0x100010 > delete
    0x80012  > delete, archive
    0x82112  > hash, archive
    0x180022 > hash:qrklejwrlke, archive
    0x180032 > replace:20070101


    DATE REPLACEMENT
    ================

    The date the dicom was recorded is taken from the StudyDate or SeriesDate
    field. The date found is then replaced either by a randomly generated date 
    or the date specified by the `replacementdate` parameter. Any occurence of 
    the date in any of the other fields in dicom is also replaced by the same
    randomly generated or specified date. Please note that any other dates 
    (e.g. participant's birth date) are not automatically replaced. These need
    to be either deleted, replaced or hashed explicitly.


    DEIDENTIFICATION EFFECTIVENESS
    ==============================

    Please note the folowing:

    1/ Only the fields explicitly set to be removed, replaced or hashed will
       be changed. It is the resposibility of the user to make sure that no
       dicom fields with identifiable information are left unchanged.
    2/ Only valid dicom fields can be accessed and changed using this tool. Any 
       vendor specific metadata that is not stored in regular dicom fields will
       not be changed. Please make sure that no such information is present in 
       your dicom files.
    3/ Only metadata stored in dicom fields can be processed using this tool.
       If any information is "burnt in" into the image data itself, it can not
       be identified and changed using this tool. Please make sure that no
       such information is present in your dicom files.


    EXAMPLE USE
    ===========

    gmri changeDICOMFiles \
         --folder=. 

    gmri changeDICOMFiles \
         --folder=/data/studies/WM/subjects/inbox/MR \
         --paramfile=/data/studies/WM/subjects/specs/deid.txt

    gmri changeDICOMFiles \
         --folder=/data/studies/WM/subjects/inbox/MR/original \
         --paramfile=/data/studies/WM/subjects/specs/deidv1.txt \
         --outputfolder=/data/studies/WM/subjects/MR/deid \
         --extension="v1"

    ----------------
    Written by Antonija Kolobarić & Grega Repovš

    Changelog
    2018-11-10 Grega Repovš
             - Updated documentation
             – Changed parameter names to match the convention and use elsewhere
             - Added input parameter checks
    
    2018-11-11 Grega Repovš
             - Stores the correct renamed and processed files in the zip package
             - urlsafe hash encoding
             - More robust field checking

    2018-11-13 Grega Repovš
             - Fixed in place processing of tar and zip archives
             - Fixed saving of gzipped dicom files
             - Expanded documentation
    '''

    if extension:
        renamefiles = True
    else:
        renamefiles = False

    if not os.path.exists(folder):
        raise ge.CommandFailed("changeDICOMFiles", "Folder not found", "The specified folder with DICOM files to change was not found:", "%s" % (folder), "Please check your paths!")

    if not paramfile:
        raise ge.CommandError("changeDICOMFiles", "No parameter file specified", "No parameter file information was provided.", "Please provide a parameter file that describes the changes to be made!")

    if not os.path.exists(paramfile):
        raise ge.CommandFailed("changeDICOMFiles", "Parameter file not found", "The specified parameter file was not found:", "%s" % (folder), "Please check your paths!")

    try:
        f = open(archivefile, "a")
        f.close()
    except:
        raise ge.CommandFailed("changeDICOMFiles", "Could not create archive file", "The specifed archive file could not be created:", "%s" % (tfile), "Please check your paths and permissions!")

    if outputfolder is not None:
        try:
            shutil.rmtree(outputfolder)
        except:
            pass
        os.mkdir(outputfolder)

    manipulate_file = functools.partial(deid_and_date_removal, param_file=paramfile, archive_file=archivefile, replacement_date=replacementdate)
    discoverDICOM(folder, manipulate_file, outputfolder, renamefiles, extension, save=True, archive_file=archivefile)


def deid_and_date_removal(opened_dicom, param_file="", archive_file="", replacement_date=None, filename=""):
    deid(opened_dicom, param_file, archive_file, filename)
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


def deid(opened_dicom, param_file="", archive_file="", filename=""):
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
                apply_action_from_field_id(opened_dicom.file_meta, key, apply_func, filename)
            else:
                apply_action_from_field_id(opened_dicom, key, apply_func, filename)

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
    return base64.urlsafe_b64encode(hashed)[:-1]


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


def apply_action_from_field_id(opened_dicom, field_id, apply_func, filename):
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
        apply_func(target, field_path_int[-1], field_id, filename)


def strip_dates(dicom_file, replacement_date=None):
    """
    :param dicom_file: the opened dicom file to strip dates from
    :type dicom_file: pydicom.FileDataset
    :param replacement_date: the date string to replace stripped dates with
    :type replacement_date: str
    :return: None
    :rtype: None
    """

    if "StudyDate" in dicom_file:
        target_date = dicom_file.StudyDate
    elif "SeriesDate" in dicom_file:
        target_date = dicom_file.SeriesDate
    else:
        print "     -> WARNING: No StudyDate field present"
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