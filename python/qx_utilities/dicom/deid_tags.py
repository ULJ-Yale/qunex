#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``deid_tags.py``

DICOM tag helpers for de-identification: recursive traversal of a dataset,
tag id conversion, and the field inventory that ``get_dicom_fields``
collects and writes out.
"""

import csv
import struct

try:
    import pydicom
except Exception:
    import dicom as pydicom


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
