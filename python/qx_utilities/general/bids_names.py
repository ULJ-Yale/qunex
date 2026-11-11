#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``bids_names.py``

The BIDS names of a session's images, for ``map_nii2bids``.

An image is read from the session record as a BIDS type, a suffix and its
key-value pairs as BIDS entities (``entity_info``); images whose names would
clash are told apart by ``run`` (``assign_runs``); and the name is built and
checked against the BIDS schema in the ``qx_library`` submodule
(``bids_stem``). Nothing here reads or writes the session's files.

The images are the dicts ``nii2bids._session_images`` makes: ``id``,
``name``, ``type``, ``folder``, ``suffix``, ``info``, ``files``, and the
``key`` and ``stem`` filled in here and by the caller.
"""

import functools
import itertools
import json
import os
import re

import qx_utilities.general.exceptions as ge

bids_mri_types = {
    "T1w": {"folder": "anat", "subtype": "nonparametric", "suffix": "T1w"},
    "T2w": {"folder": "anat", "subtype": "nonparametric", "suffix": "T2w"},
    "FM-GE": {"folder": "fmap", "subtype": "fieldmaps", "suffix": "fieldmap"},
    "FM-Magnitude": {"folder": "fmap", "subtype": "fieldmaps", "suffix": "magnitude"},
    "FM-Phase": {"folder": "fmap", "subtype": "fieldmaps", "suffix": "phasediff"},
    "FM-Precomputed": {"folder": "fmap", "subtype": "fieldmaps", "suffix": "fmap"},
    "SE-FM-AP": {"folder": "fmap", "subtype": "pepolar", "suffix": "epi"},
    "SE-FM-PA": {"folder": "fmap", "subtype": "pepolar", "suffix": "epi"},
    "SE-FM-LR": {"folder": "fmap", "subtype": "pepolar", "suffix": "epi"},
    "SE-FM-RL": {"folder": "fmap", "subtype": "pepolar", "suffix": "epi"},
    "boldref": {"folder": "func", "subtype": "func", "suffix": "sbref"},
    "bold": {"folder": "func", "subtype": "func", "suffix": "bold"},
    "DWI": {"folder": "dwi", "subtype": "dwi", "suffix": "dwi"},
}

# what a DWI label (`DWI:dir98_AP`) ends in
PE_DIRECTIONS = ("AP", "PA", "LR", "RL")

# the schema the names are built from: in the qx_library submodule at the root
# of the source tree this module belongs to, three levels up from
# `<root>/python/qx_utilities/general/bids_names.py`
BIDS_SCHEMA = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        *[os.pardir] * 3,
        "qx_library",
        "etc",
        "bids",
        "schema.json",
    )
)


def bids_type(name: str) -> str:
    """The BIDS type of an image named `name` in the session file."""
    if name.startswith("boldref"):
        return "boldref"
    if name.startswith("bold"):
        return "bold"
    return name


def entity_info(image_info: dict, image_type: str) -> dict:
    """
    The image's key-value pairs, read as BIDS entities.

    `phenc` is the direction. The label of a DWI image (`DWI:dir98_AP`) is its
    direction and its acquisition: `dir-AP`, `acq-dir98`. A copy is returned,
    so the session record stays as it is.
    """
    info = dict(image_info)

    if image_type == "DWI" and "task" in info:
        parts = info.pop("task").split("_")
        if parts[-1] in PE_DIRECTIONS:
            info.setdefault("dir", parts.pop())
        label = re.sub(r"[^a-zA-Z0-9]", "", "".join(parts))
        if label and "acq" not in info and "acquisition" not in info:
            info["acq"] = label

    if "phenc" in info:
        info["dir"] = info.pop("phenc")

    return info


def assign_runs(images: list, subject: str, sessionid: str | None) -> None:
    """
    Number the runs of the images whose BIDS names would otherwise clash.

    The images are grouped by their name read without a run. A fieldmap set,
    both directions of a spin echo pair or the magnitude and the phase of a
    gradient echo fieldmap, is grouped as a whole, as process_bids pairs them
    on import, and numbered by its se() or fm() number. A boldref with no run
    of its own takes the run of its bold, so the two keep matching. Sets each
    image's `key` and, where it needs one, the `run` in its `info`.
    """
    for image in images:
        info = {key: value for key, value in image["info"].items() if key != "run"}
        stem, _ = bids_stem(subject, info, image["type"], image["suffix"], sessionid)
        image["key"] = None if stem is None else (image["folder"], stem)

    bolds = {
        image["name"][4:]: image
        for image in images
        if image["type"] == "bold" and image["name"][4:]
    }
    followers = [
        image
        for image in images
        if image["type"] == "boldref"
        and "run" not in image["info"]
        and image["name"][7:] in bolds
    ]
    following = {image["id"] for image in followers}

    families = {}
    for image in images:
        if image["key"] is not None and image["id"] not in following:
            families.setdefault(_family(image["key"]), []).append(image)

    for members in families.values():
        keys = [member["key"] for member in members]
        if len(set(keys)) < len(keys):
            _number_runs(members)

    for image in followers:
        run = bolds[image["name"][7:]]["info"].get("run")
        if run is not None:
            image["info"]["run"] = run


def _family(key):
    """
    The group an image is numbered in, from its `(folder, name)` key.

    A fieldmap set reads the same with the direction and the suffix taken off
    its name; any other image is grouped by its name.
    """
    folder, stem = key
    if folder != "fmap":
        return key
    return folder, re.sub(r"_dir-[a-zA-Z0-9]+", "", stem.rsplit("_", 1)[0])


def _number_runs(members):
    """
    Give a run to every member of a clashing group that has none.

    A specified run is kept, a fieldmap takes its se() or fm() number, and the
    rest take the lowest numbers free among the images of the same name, in
    the order of the session record. Two images of one fieldmap set that read
    the same, such as two magnitude images given no suffix(), keep clashing:
    they are not repeats, and the clash is reported for the suffix to be set.
    """
    taken = {}
    for member in members:
        if "run" in member["info"]:
            taken.setdefault(member["key"], set()).add(str(member["info"]["run"]))

    pending = []
    for member in members:
        if "run" in member["info"]:
            continue
        number = fieldmap_number(member)
        if number is not None:
            member["info"]["run"] = number
            taken.setdefault(member["key"], set()).add(number)
        else:
            pending.append(member)

    for member in pending:
        used = taken.setdefault(member["key"], set())
        run = next(str(n) for n in itertools.count(1) if str(n) not in used)
        member["info"]["run"] = run
        used.add(run)


def fieldmap_tag(image: dict) -> str:
    """The session file tag that ties images to this fieldmap: se or fm."""
    return "se" if image["type"].startswith("SE-FM-") else "fm"


def fieldmap_number(image: dict) -> str | None:
    """The se() or fm() number of a fieldmap, or None for any other image."""
    if image["folder"] != "fmap":
        return None
    number = image["info"].get(fieldmap_tag(image))
    return None if number is None else str(number)


def extension_allowed(image_type: str, extension: str) -> bool:
    """Whether BIDS allows a file with this extension for the image type."""
    return f".{extension}" in _file_rules(image_type)["extensions"]


def bids_stem(
    subject: str,
    image_info: dict,
    image_type: str,
    suffix: str,
    sessionid: str | None = None,
) -> tuple[str | None, list]:
    """
    The BIDS name of an image, without its extension.

    Returns `(stem, problems)`. `stem` is None when the image can not be named,
    and `problems` lists what was found building it, as `(level, message)`
    pairs, `level` being "warning" or "error". An entity with a value BIDS
    does not allow is left out of the name and reported as an error.
    """
    schema = _bids_schema()
    rules = _file_rules(image_type)
    entities = schema["objects"]["entities"]

    if suffix not in rules["suffixes"]:
        return None, [("error", f"suffix {suffix} not allowed for {image_type}, skipping")]

    problems = []
    stem = f"sub-{subject}"
    present = {"subject"}
    if sessionid is not None:
        stem += f"_ses-{sessionid}"
        present.add("session")

    for entity in schema["rules"]["entities"]:
        short = entities[entity]["name"]
        if entity in image_info:
            value = image_info[entity]
        elif short in image_info:
            value = image_info[short]
        elif entity == "direction" and image_type.startswith("SE-FM-"):
            value = image_type.split("-")[-1]
        else:
            continue

        if entity not in rules["entities"]:
            problems.append(("warning", f"entity {entity} not allowed for {image_type}"))
            continue

        value = str(value)
        entity_format = entities[entity]["format"]
        if entity_format == "label" and not value.isalnum():
            problems.append((
                "error",
                f"value {value} for entity {entity} is not alphanumeric for {image_type}, skipping",
            ))
            continue
        if entity_format == "index" and not value.isdigit():
            problems.append((
                "error",
                f"value {value} for entity {entity} is not an integer for {image_type}, skipping",
            ))
            continue

        stem += f"_{short}-{value}"
        present.add(entity)

    for entity, level in rules["entities"].items():
        if isinstance(level, dict):
            level = level.get("level")
        if level == "required" and entity not in present:
            problems.append((
                "error",
                f"required entity {entity} not found for {image_type}, skipping",
            ))
            return None, problems

    return f"{stem}_{suffix}", problems


@functools.lru_cache(maxsize=None)
def _bids_schema():
    """
    The BIDS schema, read once.

    From the source tree this module belongs to, else from `$QUNEXPATH`, for
    an installation that places the python package somewhere else.
    """
    candidates = [BIDS_SCHEMA]
    if os.environ.get("QUNEXPATH"):
        candidates.append(
            os.path.join(
                os.environ["QUNEXPATH"], "qx_library", "etc", "bids", "schema.json"
            )
        )

    for candidate in candidates:
        if os.path.isfile(candidate):
            with open(candidate) as schema_file:
                return json.load(schema_file)

    raise ge.CommandFailed(
        "map_nii2bids",
        "BIDS schema not found",
        "The BIDS schema is not in %s" % " or ".join(candidates),
        "Please check that the qx_library submodule is present!",
    )


def _file_rules(image_type):
    """The BIDS schema's rules for the files of an image type."""
    kind = bids_mri_types[image_type]
    return _bids_schema()["rules"]["files"]["raw"][kind["folder"]][kind["subtype"]]
