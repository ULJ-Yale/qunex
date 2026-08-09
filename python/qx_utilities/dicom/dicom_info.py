#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``dicom_info.py``

Reading image metadata from DICOM and Philips PAR/REC files.

Provides the low level header readers (``read_dicom_base``, ``_read_deep``)
and the higher level extractors (``read_dicom_info``, ``read_par_info``)
that return a ``vdict`` with the fields the sort, conversion and import
commands rely on.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import os
import gzip as gz

from datetime import datetime

import qx_utilities.dicom.sort_records as gds_records
import qx_utilities.dicom.sort_tags as gds_tags
from qx_utilities.dicom.dicom_utils import dcm_info_list, vdict

try:
    import pydicom.filereader as dfr
except Exception:
    import dicom.filereader as dfr


def read_par_info(filename):
    """
    ``read_par_info(filename)``

    Reads `.PAR` files.

    INPUT
    =====

    --filename      The name of the `.PAR` file.

    OUTPUT
    ======

    The function returns the PAR fields as well as a
    set of standard information as a dictionary. Including:

    - sessionid
    - seriesNumber
    - seriesDescription
    - TR
    - TE
    - frames
    - directions
    - volumes
    - slices
    - datetime
    """

    if not os.path.exists(filename):
        raise ValueError("PAR file %s does not exist!" % (filename))

    # -- set up info
    info = vdict(__keys__=dcm_info_list)

    with open(filename, "r") as f:
        for line in f:
            if len(line) > 1 and line[0] == ".":
                line = line[1:].strip()
                k, v = [e.strip() for e in line.split(":  ")]
                info[k] = v

    info["sessionid"] = info.get("Patient name", info["sessionid"])
    info["seriesNumber"] = int(info.get("Acquisition nr", 0)) * 100 + int(
        info.get("Reconstruction nr", 0)
    )
    info["seriesDescription"] = info.get(
        "Protocol name", info["seriesDescription"]
    ).replace("WIP ", "")
    info["TR"] = float(info.get("Repetition time [msec]", info["TR"]))
    info["TR"] = float(info.get("Repetition time [ms]", info["TR"]))
    info["TE"] = 0.0
    info["frames"] = int(info.get("Max. number of dynamics", info["frames"]))
    info["directions"] = int(info.get("Max. number of gradient orients", 1)) - 1
    info["volumes"] = max(info["frames"], info["directions"])
    info["slices"] = int(info.get("Max. number of slices/locations", info["slices"]))
    info["datetime"] = info.get("Examination date/time", info["datetime"])
    info["ImageType"] = [""]
    info["fileid"] = os.path.basename(filename)[:-4].replace(".", "_").replace("-", "_")

    info.validate()

    return info


def read_dicom_info(filename, extended=False):
    """
    ``read_dicom_info(filename, extended=False)``

    Reads basic information from DICOM files.

    INPUT
    =====

    --filename      The name of the `DICOM` file.
    --extended      If True, also read per-frame functional groups and populate
                    the extended geometry/temporal/acceleration/HCP keys used by
                    the single-pass sort engine (see below). Default: False, in
                    which case the fast partial read and the original key set are
                    used, unchanged.

    OUTPUT
    ======

    Extracted information is returned in a dictionary along with a DICOM objects
    stored as `dicom`. It tries to extract
    the following standard information:

    - sessionid
    - seriesNumber
    - seriesDescription
    - TR
    - TE
    - frames
    - directions
    - volumes
    - slices
    - datetime

    When ``extended`` is True the dictionary additionally carries per-instance
    and per-sequence fields consumed by ``sort_dicom`` (SeriesInstanceUID,
    manufacturer/model, is_imaging, is_mosaic, rows/cols, number_of_frames/
    slices/temporal_positions, images_in_acq, pixel_spacing, slice_thickness,
    spacing_between_slices, instance_number, temporal_position,
    acquisition_number, in_stack_position, image_position, acq_datetime,
    sense_factor, multiband_factor, phase_encoding_direction,
    enhanced_volume_map, hint_tags).
    """

    if not os.path.exists(filename):
        raise ValueError("DICOM file %s does not exist!" % (filename))

    d = _read_deep(filename) if extended else read_dicom_base(filename)
    fileid, _ = os.path.splitext(os.path.basename(filename))
    return _dicom_info_from_dataset(d, fileid, extended)


def _dicom_info_from_dataset(d, fileid, extended=False):
    """
    Build the ``read_dicom_info`` dictionary from an already-read pydicom dataset.

    Shared by ``read_dicom_info`` (file path) and the single-pass sort engine
    (in-memory bytes), so both parse identically without staging files to disk.
    """
    info = vdict(__keys__=dcm_info_list)

    info["sessionid"] = get_id(d)

    # --- sessionid

    info["sessionid"] = ""
    if "PatientID" in d:
        info["sessionid"] = d.PatientID
    if info["sessionid"] == "":
        if "StudyID" in d:
            info["sessionid"] = d.StudyID

    # --- seriesNumber

    try:
        info["seriesNumber"] = int(d.SeriesNumber)
    except Exception:
        info["seriesNumber"] = None

    # --- seriesDescription -- multiple possibilities

    for key_name in ["SeriesDescription", "ProtocolName", "SequenceName"]:
        info["seriesDescription"] = d.get(key_name, "anonymous")
        if info["seriesDescription"].lower() != "anonymous":
            break

    # --- TR, TE (robust extraction shared with the sort engine)

    tr, te = gds_tags.extract_tr_te(d)
    info["TR"], info["TE"] = float(tr or 0.0), float(te or 0.0)

    # --- Frames

    info["volumes"] = 0
    try:
        info["volumes"] = int(d[0x2001, 0x1081].value)
    except Exception:
        info["volumes"] = 0

    info["frames"] = info["volumes"]
    info["directions"] = info["volumes"]

    # --- slices

    try:
        info["slices"] = int(d[0x2001, 0x1018].value)
    except Exception:
        try:
            info["slices"] = int(d[0x0019, 0x100A].value)
        except Exception:
            info["slices"] = 0

    # --- datetime

    try:
        info["datetime"] = datetime.strptime(
            str(int(float(d.StudyDate + d.ContentTime))), "%Y%m%d%H%M%S"
        ).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            info["datetime"] = datetime.strptime(
                str(int(float(d.StudyDate + d.StudyTime))), "%Y%m%d%H%M%S"
            ).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            info["datetime"] = ""

    # --- SOPInstanceUID

    try:
        info["SOPInstanceUID"] = d.SOPInstanceUID
    except Exception:
        info["SOPInstanceUID"] = None

    # --- ImageType

    try:
        info["ImageType"] = d[0x0008, 0x0008].value
    except Exception:
        info["ImageType"] = ""

    # --- dicom header

    info["dicom"] = d

    # --- fileid

    info["fileid"] = fileid

    # ---> institution name
    if [0x0008, 0x0080] in d:
        info["institution"] = d[0x0008, 0x0080].value

    # ---> manufacturer and model
    MR = []
    for e in [[0x0008, 0x0070], [0x0008, 0x1090], [0x0008, 0x1010]]:
        if e in d:
            MR.append(str(d[e].value))
    if MR:
        info["device"] = "|".join(MR)

    if extended:
        _augment_extended(info, d)

    return info


def _read_deep(filename):
    """
    Read a DICOM header including per-frame functional groups, stopping before
    pixel data. Needed for enhanced multi-frame files where the volume/slice
    layout lives in the per-frame groups (which the fast partial read in
    ``read_dicom_base`` deliberately skips). Handles gzipped files.
    """

    def stop(tag, VR, length):
        return tag == (0x7FE0, 0x0010)

    f = None
    try:
        f = gz.open(filename, "rb") if ".gz" in filename else open(filename, "rb")
        return dfr.read_partial(f, stop_when=stop)
    except Exception:
        try:
            return dfr.read_file(filename, stop_before_pixels=True)
        except Exception:
            return None
    finally:
        if f is not None and not f.closed:
            f.close()


def _augment_extended(info, d):
    """
    Populate the extended keys consumed by the single-pass sort engine. Called
    only when ``read_dicom_info(extended=True)``; the original keys are untouched.
    """
    if d is None:
        return

    info["SeriesInstanceUID"] = str(getattr(d, "SeriesInstanceUID", "") or "")
    info["modality"] = gds_records.fmt(getattr(d, "Modality", None))
    info["manufacturer"] = gds_records.fmt(getattr(d, "Manufacturer", None))
    info["model"] = gds_records.fmt(getattr(d, "ManufacturerModelName", None))

    info["is_imaging"] = gds_tags.is_imaging_ds(d)
    info["is_mosaic"] = gds_tags.is_mosaic_ds(d)

    info["rows"] = gds_records.to_int(getattr(d, "Rows", None))
    info["cols"] = gds_records.to_int(getattr(d, "Columns", None))
    info["number_of_frames"] = gds_records.to_int(getattr(d, "NumberOfFrames", None))
    info["number_of_slices"] = gds_records.to_int(getattr(d, "NumberOfSlices", None))
    info["images_in_acq"] = gds_records.to_int(getattr(d, "ImagesInAcquisition", None))
    info["number_of_temporal_positions"] = gds_records.to_int(
        getattr(d, "NumberOfTemporalPositions", None)
    )

    px, st, sbs = gds_tags.get_shared_pixel_measures(d)
    info["pixel_spacing"] = px
    info["slice_thickness"] = st
    info["spacing_between_slices"] = sbs

    info["instance_number"] = gds_records.to_int(getattr(d, "InstanceNumber", None))
    info["temporal_position"] = gds_records.to_int(getattr(d, "TemporalPositionIdentifier", None))
    info["acquisition_number"] = gds_records.to_int(getattr(d, "AcquisitionNumber", None))
    info["in_stack_position"] = gds_records.to_int(getattr(d, "InStackPositionNumber", None))

    ipp = getattr(d, "ImagePositionPatient", None)
    info["image_position"] = None
    if ipp is not None and len(ipp) >= 3:
        try:
            info["image_position"] = (float(ipp[0]), float(ipp[1]), float(ipp[2]))
        except (TypeError, ValueError):
            info["image_position"] = None

    info["acq_datetime"] = gds_records.parse_dt(d)
    info["sense_factor"] = gds_tags.extract_sense_factor(d)
    info["multiband_factor"] = gds_tags.extract_mb_factor(d)
    info["phase_encoding_direction"] = gds_tags.extract_phase_encoding_direction(
        d, info["seriesDescription"]
    )

    frames = info["number_of_frames"] or 0
    info["enhanced_volume_map"] = (
        gds_tags.extract_enhanced_volume_map(d) if frames > 1 else {}
    )

    info["hint_tags"] = {
        "EffectiveEchoSpacing": getattr(d, "EffectiveEchoSpacing", None),
        "BandwidthPerPixelPhaseEncode": getattr(d, "BandwidthPerPixelPhaseEncode", None),
        "PixelBandwidth": getattr(d, "PixelBandwidth", None),
        "EchoTrainLength": getattr(d, "EchoTrainLength", None),
        "InPlanePhaseEncodingDirection": getattr(d, "InPlanePhaseEncodingDirection", None),
        "PrivateEchoSpacing": gds_tags._first_numeric(
            gds_tags._iter_values_for_tag(d, (0x2005, 0x1492))
        ),
        "PrivateAcqDurationSec": gds_tags._first_numeric(
            gds_tags._iter_values_for_tag(d, (0x2005, 0x1033))
        ),
        "StackRadialAxis": gds_tags._first_axis(
            gds_tags._iter_values_for_tag(d, (0x2001, 0x1033))
        ),
    }


# fcount = 0
#
# def _at_frame(tag, VR, length):
#     global fcount
#     test = tag == (0x5200, 0x9230)
#     if test and fcount == 1:
#         fcount = 0
#         return true
#     elif test:
#         fcount = 1


def _at_frame(tag, vr, length):
    return tag == (0x5200, 0x9230) or tag == (0x7FE0, 0x0010)


def read_dicom_base(filename):
    # try partial read
    try:
        if ".gz" in filename:
            f = gz.open(filename, "rb")
        else:
            f = open(filename, "rb")
        d = dfr.read_partial(f, stop_when=_at_frame)
        f.close()
        return d
    except Exception:
        # return None
        # print(" ---> WARNING: Could not partial read dicom file, attempting full read! [%s]" % (filename))
        try:
            d = dfr.read_file(filename, stop_before_pixels=True)
            return d
        except Exception:
            # print(" ---> ERROR: Could not read dicom file, aborting. Please check file: %s" % (filename))
            return None
    finally:
        if f is not None and not f.closed:
            f.close()


def get_dicom_time(info):
    try:
        time = datetime.strptime(
            str(int(float(info.StudyDate + info.ContentTime))), "%Y%m%d%H%M%S"
        ).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            time = datetime.strptime(
                str(int(float(info.StudyDate + info.StudyTime))), "%Y%m%d%H%M%S"
            ).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            time = ""
    return time


def get_id(info):
    v = ""
    if "PatientID" in info:
        v = info.PatientID
    if v == "":
        if "StudyID" in info:
            v = info.StudyID
    return v


def get_tr_te(info):
    # delegates to the shared robust extractor; info is a pydicom dataset
    tr, te = gds_tags.extract_tr_te(info)
    return float(tr or 0.0), float(te or 0.0)
