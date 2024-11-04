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

RE_IMAGE_TYPE_SE_PATTERN = re.compile(r"^SE-FM-PA|SE-FM-AP|SE-FM-LR|SE-FM-RL$")
RE_IMAGE_TYPE_FM_PATTERN = re.compile(r"^FM-Magnitude|FM-Phase$")
RE_IMAGE_TYPE_BOLD_PATTERN = re.compile(r"^(bold|boldref)(\d*)$")


def read_generic_session_file(session_file_path):
    """Parse and return the content of a session file

    Args:
        session_file_path: session file path as a string

    Returns:
        A dict mapping with the following schema
        {
            "session": str, # session id
            "subject": str, # subject id
            "paths": Dict[str, str] # key: path_type, value: path string,
            "pipeline_ready": List[str] # ["hcp"]
            "images": {
                <image_number> : <image_info_schema>
            }
        }
        <image_number>: Tuple[int] # one or more int separated by decimal points
        <image_info_schema>: {
            "image_number": <image_number>,
            "raw_image_number": str,
            "series_description": str,
            "fm": int | None, # field map hint
            "se": int | None, # spin-echo hint
            "phenc": str | None, # phase encoding direction
            "bold_num": int | None, # bold number hint
            "additional_tags": List[str | Tuple[str, str]], #additional tag string
        }

    """
    return _read_session_file(session_file_path, "generic")


def read_hcp_session_file(session_file_path):
    """Return the content of an HCP session file

    Args:
        session_file_name: session file name as a string

    Returns:
        A dict mapping with the following schema
        {
            "session": str, # session id
            "subject": str, # subject id
            "paths": Dict[str, str] # key: path_type, value: path string,
            "pipeline_ready": List[str] # ["hcp"]
            "images": {
                <image_number> : <image_info_schema>
            }
        }
        <image_number>: Tuple[int] # one or more int separated by decimal points
        <image_info_schema>: {
            "image_number": <image_number>,
            "raw_image_number": str
            "hcp_image_type": (
                1 tuple -> "T1w", "T2w", "FM-GE"
                2 tuple -> ("FM", Phase/Magnitude), ("SE-FM", RL/LR/AP/PA), ("DWI", label)
                3 tuple -> ("boldref", num, label), ("bold", num, label),
                ),
            "fm": int | None, # field map hint
            "se": int | None, # spin-echo hint
            "phenc": str | None, # phase encoding direction
            "bold_num": int | None, # bold number hint
            "additional_tags": List[str | Tuple[str, str]], #additional tag string
        }

    """
    return _read_session_file(session_file_path, "pipeline:hcp")


def read_mapping_file(mapping_file_path):
    """Return the content of a mapping file

    Args:
        mapping_file_path: session file path as a string

    Returns:
        A dict mapping with the following schema
        schema
        {
            "group_rules": {
                "image_number" => {<rule_schema>}
                "name" => {<rule_schema>}
            }
            "session_rules": { # reserved for session specific mapping rules
                <session id>: {
                    ...
                }
            }
        }

        <image_info_schema>: {
            "hcp_image_type": (
                1 tuple -> "T1w", "T2w", "FM-GE",
                2 tuple -> ("FM", Phase/Magnitude), ("SE-FM", RL/LR/AP/PA), ("DWI", label)
                3 tuple -> ("boldref", None, label), ("bold", None, label),
                ),
            "fm": int | None, # field map hint
            "se": int | None, # spin-echo hint
            "phenc": str | None, # phase encoding direction
            "bold_num": int | None, # bold number hint
            "additional_tags": List[str | Tuple[str, str]], #additional tag string
        }
    """
    with open(mapping_file_path) as f:
        lines = f.readlines()
        # remove comments
        lines = [l.split("#")[0] for l in lines]
        lines = [l.strip() for l in lines]

    # convert to a proper data structure
    try:
        return _parse_mapping_file_lines(lines)
    except ge.SpecFileSyntaxError as e:
        e.filename = mapping_file_path
        raise e
    except StopIteration:
        raise ge.SpecFileSyntaxError(
            filename=mapping_file_path, error="unexpected number of tokens"
        )


def _read_session_file(session_file_path, session_file_type):
    """Return the content of a session file"""
    with open(session_file_path) as f:
        lines = f.readlines()
        # remove comments
        lines = [l.split("#")[0] for l in lines]
        lines = [l.strip() for l in lines]

    # convert to a proper data structure
    try:
        return _parse_session_file_lines(lines, session_file_type)
    except ge.SpecFileSyntaxError as e:
        e.filename = session_file_path
        raise e


def _parse_session_file_lines(lines, session_file_type):
    """Parse the content of a session file

    session_file_type: "generic" / "pipeline:hcp"

    """
    session = {
        "session": None,
        "subject": None,
        "paths": dict(),
        "pipeline_ready": [],
        "images": {},
        "custom_tags": {},
    }
    for l in lines:
        tokens = [e.strip() for e in l.split(":")]
        if len(tokens) == 1 and tokens[0] == "":
            continue

        if tokens[0] == "id" or tokens[0] == "session":
            if len(tokens) != 2 or tokens[1] == "":
                raise ge.SpecFileSyntaxError(error="unexpected number of tokens")
            session["session"] = tokens[1]

        elif tokens[0] == "subject":
            if len(tokens) != 2 or tokens[1] == "":
                raise ge.SpecFileSyntaxError(error="unexpected number of tokens")
            session["subject"] = tokens[1]

        elif tokens[0] in ["dicom", "raw_data", "data", "hcp", "bids", "hcpls"]:
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

        else:
            session["custom_tags"][tokens[0]] = l.split(":", 1)[1].strip()

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


def _parse_session_image_line(tokens, session_file_type):
    """Parse one line of session file describing an image

    Args:
        tokens: tokenized line, tokens[0] must be a valid image number
        session_file_type: "generic" / "pipeline:hcp"
    """
    image_number = _parse_image_number(tokens[0])

    image_info = _parse_image_line_tags(tokens[1:], session_file_type)
    image_info["image_number"] = image_number
    image_info["raw_image_number"] = tokens[0]
    return image_info


def _parse_image_number(token):
    """Parse image number

    Image number could be one or more integer number separated
    by '.' Allow forward compatibility.

    Args:
        token: str
    Returns:
        A tuple of integers
    Exceptions:
        ValueError: parse int error
    """
    return tuple(int(i) for i in token.split("."))


def _parse_image_line_tags(tokens, line_type):
    """Parse tags of a image or a mapping rule

    The first (and second for bold) tag will be treated differently
    based on line_type (generic / pipeline:hcp / mapping:hcp)

    Exceptions:
        SpecFileSyntaxError
        StopIteration: when bold, boldref, DWI doesn't have user defined label

    """
    # use enum?
    GENERIC = "generic"
    SESSION_HCP = "pipeline:hcp"
    MAPPING_HCP = "mapping:hcp"

    img_info = {"additional_tags": []}

    token_iter = iter(tokens)

    if line_type == GENERIC:
        img_info["series_description"] = next(token_iter)
    elif line_type == SESSION_HCP or line_type == MAPPING_HCP:
        hcp_image_type = next(token_iter)
        if hcp_image_type == "":
            # image type not specified
            pass
        elif hcp_image_type in ["T1w", "T2w", "FM-GE", "ASL", "mbPCASLhr", "PCASLhr", "TB1DAM", "TB1EPI", "TB1AFI", "TB1TFL", "TB1RFM", "TB1SRGE", "RB1COR"]:
            img_info["hcp_image_type"] = (hcp_image_type,)

        elif RE_IMAGE_TYPE_FM_PATTERN.match(hcp_image_type):
            img_info["hcp_image_type"] = ("FM", hcp_image_type.rsplit("-")[-1])

        elif RE_IMAGE_TYPE_SE_PATTERN.match(hcp_image_type):
            img_info["hcp_image_type"] = ("SE-FM", hcp_image_type.rsplit("-")[-1])

        elif RE_IMAGE_TYPE_BOLD_PATTERN.match(hcp_image_type):
            match = RE_IMAGE_TYPE_BOLD_PATTERN.match(hcp_image_type)
            bold_type = match.group(1)

            bold_num = match.group(2)
            if line_type == SESSION_HCP:
                bold_num = int(bold_num)
            elif line_type == MAPPING_HCP:
                if bold_num != "":
                    raise ge.SpecFileSyntaxError(
                        error="bold number should be specified as hint tag in mapping file"
                    )
                bold_num = None

            bold_label = next(token_iter)
            img_info["hcp_image_type"] = (bold_type, bold_num, bold_label)

        elif hcp_image_type == "DWI":
            img_info["hcp_image_type"] = (hcp_image_type, next(token_iter))

        else:
            raise ge.SpecFileSyntaxError(
                error="unknown hcp image type {}".format(hcp_image_type)
            )

    else:
        raise ge.SpecFileSyntaxError(error="unexpected session file type")

    for token in token_iter:
        if token == "":
            continue

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
