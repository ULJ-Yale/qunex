#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``parser.py``

A collection of parses for qunex file formats
"""

"""
Created by Lining Pan on 2022-05-19.
"""

from logging import raiseExceptions
import re
import general.exceptions as ge

# compile once but might slow down start up time
# RE_IMAGE_NUM = re.compile(r"^\d+$")
RE_IMAGE_NUM = re.compile(r"^\d+(\.\d+)*$")
RE_READY = re.compile(r"^(\w+)ready$")

RE_TAG_NO_VALUE = re.compile(r"^[^:]*$")
RE_TAG_SE = re.compile(r"^se\((\w+)\)$")
RE_TAG_FM = re.compile(r"^fm\((\w+)\)$")
RE_TAG_PHENC = re.compile(r"^phenc\((\w+)\)$")
RE_TAG_BOLD_NUM = re.compile(r"^bold_num\((\w+)\)$")
RE_TAG_WITH_VALUE = re.compile(r"^(\w+)\((\w+)\)$")

RE_IMAGE_TYPE_SE_PATTERN  = re.compile(r'^SE-FM-PA|SE-FM-AP|SE-FM-LR|SE-FM-RL$')
RE_IMAGE_TYPE_FM_PATTERN  = re.compile(r'^FM-Magnitude|FM-Phase$')
RE_IMAGE_TYPE_BOLD_PATTERN = re.compile(r"^(bold|boldref)(\d*)$")


def read_generic_session_file(session_file_name):
    """Return the content of a session file 

    schema:
    {
        "id": <session id>,
        "subject": <subject id>
        "paths": { <path_type>: <path string> },
        "pipeline_ready": ["hcp"],
        "images": {
            <image_number> : {
                "image_number": <image_number> (int,)
                "series_description": "",
                "fm": <fm hint / None>,
                "se": <se hint / None>,
                "phenc": <phenc direction / None>,
                "bold_num": <boldnum hint / None>,
                "additional_tags": [<tag str>, or tuple(tag key, tag val)],
            }
        }
    }
    """
    return _read_session_file(session_file_name, "generic")

def read_hcp_session_file(session_file_name):
    """Return the content of an HCP session file 
    
    schema:
    {
        "id": <session id>,
        "subject": <subject id>
        "paths": { <path_type>: <path string> },
        "pipeline_ready": ["hcp"],
        "images": {
            <image_number> : {
                "image_number": <image_number> (int,)
                "hcp_image_type": (
                    1 tuple -> "T1w", "T2w", "FM-GE", "DWI"
                    2 tuple -> ("FM", Phase/Magnitude), ("SE-FM", RL/LR/AP/PA),
                    3 tuple -> ("BoldRef", num, label), ("Bold", num, label), 
                    ),
                "fm": <fm hint / None>,
                "se": <se hint / None>,
                "phenc": <phenc direction / None>,
                "bold_num": <boldnum hint / None>,
                "additional_tags": [<tag str>, or tuple(tag key, tag val)],
            }
        }
    }
    """
    return _read_session_file(session_file_name, "pipeline:hcp")


def read_mapping_file(mapping_file_name):
    """Return the content of a mapping file

    schema
    {
        "group_rules": {
            "image_number" => {<rule_schema>}
            "name" => {<rule_schema>}
        }
        "session_rules": { // reserved for session specific mapping rules
            <session id>: {

            }
        }
    }

    rule_schema
    {
        "hcp_image_type": (
            1 tuple -> "T1w", "T2w", "FM-GE", "DWI"
            2 tuple -> ("FM", Phase/Magnitude), ("SE-FM", RL/LR/AP/PA),
            3 tuple -> ("BoldRef", num, label), ("Bold", num, label), 
            ),
        "fm": <fm hint / None>,
        "se": <se hint / None>,
        "phenc": <phenc direction / None>,
        "bold_num": <boldnum hint / None>,
        "additional_tags": [<tag str>, or tuple(tag key, tag val)],
    }
    """
    with open(mapping_file_name) as f:
        lines = f.readlines()
        # remove comments
        lines = [l.split("#")[0] for l in lines]
        lines = [l.strip() for l in lines]
    
    # convert to a proper data structure
    try:
        return _parse_mapping_file_lines(lines)
    except ge.SpecFileSyntaxError as e:
        e.filename = mapping_file_name
        raise e
    except StopIteration:
        raise ge.SpecFileSyntaxError(filename=mapping_file_name, error="unexpected number of tokens")
    

def _read_session_file(session_file_name, session_file_type):
    """Return the content of a session file
    
    """
    with open(session_file_name) as f:
        lines = f.readlines()
        # remove comments
        lines = [l.split("#")[0] for l in lines]
        lines = [l.strip() for l in lines]
    
    # convert to a proper data structure
    try:
        return _parse_session_file_lines(lines, session_file_type)
    except ge.SpecFileSyntaxError as e:
        e.filename = session_file_name
        raise e


def _parse_session_file_lines(lines, session_file_type):
    """ Parse the content of a session file
    
    session_file_type: "generic" / "pipeline:hcp"

    """
    session = {"id": None, "subject": None, "paths": dict(), "pipeline_ready": [], "images": {}}
    for l in lines:
        tokens = [e.strip() for e in l.split(":")]
        if len(tokens) == 1 and tokens[0] == "":
            continue
        
        if tokens[0] == "id":
            if len(tokens) != 2 or tokens[1] == "":
                raise ge.SpecFileSyntaxError(error="unexpected number of tokens")
            session["id"] = tokens[1]

        elif tokens[0] == "subject":
            if len(tokens) != 2 or tokens[1] == "":
                raise ge.SpecFileSyntaxError(error="unexpected number of tokens")
            session["subject"] = tokens[1]

        elif tokens[0] in ["dicom", "raw_data", "data", "hcp", "bids"]:
            if len(tokens) != 2 or tokens[1] == "":
                raise ge.SpecFileSyntaxError(error="unexpected number of tokens")
            session["paths"][tokens[0]] = tokens[1]

        elif RE_READY.match(tokens[0]):
            pipeline_type = RE_READY.match(tokens[0]).group(1)
            if len(tokens) != 2 or tokens[1] == "":
                raise ge.SpecFileSyntaxError(error="unexpected number of tokens")
            if tokens[1] == "true":
                session["pipeline_ready"].append(pipeline_type)

        elif RE_IMAGE_NUM.match(tokens[0]):
            img = _parse_session_image_line(tokens, session_file_type)
            session["images"][img["image_number"]] = img
        
    # TODO: validate completeness
    return session


def _parse_mapping_file_lines(lines):    
    """
    {
        "group_rules": {
            "image_number" => {}
            "name" => {}
        }
        "session_rules": { // reserved for session specific mapping rules
            <session id>: {

            }
        }
    }
    """

    result = {"group_rules": {"image_number": {}, "name": {}}}
    for l in lines:
        if l == "":
            continue
        tokens = [e.strip() for e in l.split("=>")]
        if len(tokens) != 2:
            raise ge.SpecFileSyntaxError(error="invalid mapping rule")
        
        tag_tokens = [e.strip() for e in tokens[1].split(":")]
        rule = _parse_image_line_tags(tag_tokens, "mapping:hcp")
        
        if RE_IMAGE_NUM.match(tokens[0]):
            rule_key = _parse_image_number(tokens[0])
            rule_set = result["group_rules"]["image_number"]
        else:
            rule_key = tokens[0]
            rule_set = result["group_rules"]["name"]
        
        if rule_key in rule_set:
            raise ge.SpecFileSyntaxError(error="duplicated rules")
        else:
            rule_set[rule_key] = rule
        
    return result


def _parse_session_image_line(line, session_file_type):
    """ 
    line[0] must be a valid image number
    """
    image_number = _parse_image_number(line[0])

    image_info = _parse_image_line_tags(line[1:], session_file_type)
    image_info["image_number"] = image_number
    return image_info


def _parse_image_number(token):
    # image_number = tuple(int(line[0]))
    return tuple(int(i) for i in token.split('.'))


def _parse_image_line_tags(line, line_type):
    """ Parse tags of a image or a mapping rule
    
    The first (and second for bold) tag will be treated differently
    based on line_type (generic / pipeline:hcp / mapping:hcp)
    """
    GENERIC = "generic"
    SESSION_HCP = "pipeline:hcp"
    MAPPING_HCP = "mapping:hcp"

    img_info = {"additional_tags": []}

    line_iter = iter(line)

    if line_type == GENERIC:
        img_info["series_description"] = next(line_iter)
    elif line_type == SESSION_HCP or line_type == MAPPING_HCP:
        hcp_image_type = next(line_iter)
        if hcp_image_type == "":
            # image type not specified
            pass
        elif hcp_image_type in ["T1w", "T2w", "FM-GE", "DWI"]:
            img_info["hcp_image_type"] = (hcp_image_type,)
        
        elif RE_IMAGE_TYPE_FM_PATTERN.match(hcp_image_type):
            img_info["hcp_image_type"] = ("FM", hcp_image_type.rsplit('-')[-1])
        
        elif RE_IMAGE_TYPE_SE_PATTERN.match(hcp_image_type):
            img_info["hcp_image_type"] = ("SE-FM", hcp_image_type.rsplit('-')[-1])
        
        elif RE_IMAGE_TYPE_BOLD_PATTERN.match(hcp_image_type):
            match = RE_IMAGE_TYPE_BOLD_PATTERN.match(hcp_image_type)
            bold_type = match.group(1)
            
            bold_num = match.group(2)
            if line_type == SESSION_HCP:
                bold_num = int(bold_num)
            elif line_type == MAPPING_HCP:
                if bold_num != "":
                    raise ge.SpecFileSyntaxError(
                        error="bold number should be specified as hint tag in mapping file")
                bold_num = None
            
            bold_label = next(line_iter)
            img_info["hcp_image_type"] = (bold_type, bold_num, bold_label)

        else:
            raise ge.SpecFileSyntaxError(error="unknown hcp image type {}".format(hcp_image_type))

    else:
        raise ge.SpecFileSyntaxError(error="unexpected session file type")
    
    for token in line_iter:
        # TODO: python 3.8 https://docs.python.org/3/whatsnew/3.8.html#assignment-expressions
        # assignment expressions will make the code much more readable and less error prone
        se_match = RE_TAG_SE.match(token)
        if se_match:
            img_info["se"] = int(se_match.group(1))
            continue
        
        fm_match = RE_TAG_FM.match(token)
        if fm_match:
            img_info["fm"] = int(fm_match.group(1))
            continue
    
        phenc_match = RE_TAG_PHENC.match(token)
        if phenc_match:
            # TODO: should validate
            img_info["phenc"] = phenc_match.group(1)
            continue

        bold_num_match = RE_TAG_BOLD_NUM.match(token)
        if bold_num_match:
            img_info["bold_num"] = int(bold_num_match.group(1))
            continue
    
        tag_with_value_match = RE_TAG_WITH_VALUE.match(token)
        if tag_with_value_match:
            t = (tag_with_value_match.group(1), tag_with_value_match.group(2))
            img_info["additional_tags"].append(t)
            continue
        
        if RE_TAG_NO_VALUE.match(token):
            img_info["additional_tags"].append(token)
            continue

        raise ge.SpecFileSyntaxError(error="invalid image tag: {}".format(token))
    
    return img_info