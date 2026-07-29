#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``deid_actions.py``

The de-identification actions themselves: parsing the specification file and
applying the archive, replace, delete and date removal operations to a DICOM
dataset.
"""

import csv
import functools
import random

from qx_utilities.dicom.deid_tags import get_group, get_tag, recurse_tree

try:
    import pydicom
except Exception:
    import dicom as pydicom


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

    action_order = ['archive', 'replace', 'delete']

    action_dict = {}
    replace_map = {}
    line_number  = 0

    with open(spec_file, 'r') as f:
        for line in f:
            line_number += 1
            line = line.strip()
            if len(line) > 0:
                if line[0] != "#" and ">" in line:
                    line    = line.split(">")
                    key     = line[0].strip()
                    actions = [e.strip() for e in line[1].split(",")]

                    if key not in action_dict:
                        action_dict[key] = []
                    else:
                        print("---> Warning, actions for tag %s specified more than once! [line: %d]" % (key, line_number))

                    for action in actions:
                        if "replace" in action:
                            parts = [e.strip() for e in action.split(':')]
                            if len(parts) == 2:
                                action, replacement = parts
                                replace_map[key] = replacement
                            else:
                                print("---> Warning, no replacement specified, skipping replacement! [line %d: %s]" % (line_number, action))

                        action_dict[key].append(action)

    for key in action_dict:
        action_dict[key] = [e for e in action_order if e in action_dict[key]]

    return action_dict, replace_map
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
