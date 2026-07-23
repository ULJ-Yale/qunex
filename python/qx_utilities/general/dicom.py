#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``dicom.py``

Functions for processing dicom images and converting them to NIfTI format:

--read_par_info           Reads image info from Philips PAR/REC files.
--read_dicom_info         Reads image info from DICOM files.
--dicom2niiz            Converts DICOM to NIfTI images.
--sort_dicom            Sorts the DICOM files into subfolders according to images.
--clean_dicom           Removes non-image and incomplete volume DICOM files.
--list_dicom            List the information on DICOM files.
--split_dicom           Split files from different sessions.
--import_dicom          Processes incoming data.
--get_dicom_info        Prints HCP relevant information from a DICOM file.

The commands are accessible from the terminal using gmri utility.
"""

"""
Copyright (c) Grega Repovs. All rights reserved.
"""


import os
import io
import os.path
import sys
import re
import glob
import shutil
import subprocess
import traceback
import zipfile
import tarfile
import gzip as gz
import csv
import json
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
import qx_utilities.general.core as gc
import qx_utilities.general.img as gi
import qx_utilities.general.nifti as gn
import qx_utilities.general.qximg as qxi
import qx_utilities.general.exceptions as ge
from qx_utilities.general.parsing import true_or_false

from datetime import datetime

if "QUNEXMCOMMAND" not in os.environ:
    mcommand = "matlab -nojvm -nodisplay -nosplash -r"
else:
    mcommand = os.environ["QUNEXMCOMMAND"]

try:
    import pydicom.filereader as dfr
    import pydicom
except:
    import dicom.filereader as dfr
    import dicom as pydicom

import numpy as np
from collections import defaultdict, Counter

dcm_info_list = (
    ("sessionid", str, "NA"),
    ("seriesNumber", int, 0),
    ("seriesDescription", str, "NA"),
    ("TR", float, 0.0),
    ("TE", float, 0.0),
    ("frames", int, 0),
    ("directions", int, 0),
    ("volumes", int, 0),
    ("slices", int, 0),
    ("datetime", str, ""),
    ("ImageType", str, ""),
    ("fileid", str, ""),
)

if "QUNEXMCOMMAND" not in os.environ:
    mcommand = "matlab -nojvm -nodisplay -nosplash -r"
else:
    mcommand = os.environ["QUNEXMCOMMAND"]

dcm_info_list = (
    ("sessionid", str, "NA"),
    ("seriesNumber", int, 0),
    ("seriesDescription", str, "NA"),
    ("TR", float, 0.0),
    ("TE", float, 0.0),
    ("frames", int, 0),
    ("directions", int, 0),
    ("volumes", int, 0),
    ("slices", int, 0),
    ("datetime", str, ""),
    ("ImageType", str, ""),
    ("fileid", str, ""),
)


class vdict(dict):
    """
    An extension of a dictionary class. Upon initialization it creates fields
    with the names and default values as specified in the __keys__, which
    should be a list of key_name, key_func, and key_default triplets.

    Upon initialization, keys with the provided names and defaults values are
    created. When calling `validate` method, any missing keys are generated
    with the default values, and all the keys are transformed according to
    the provided functions in the key_func.
    """

    def __init__(self, *args, **kw):
        self.__keys__ = kw.pop("__keys__", ())
        super(vdict, self).__init__(*args, **kw)
        self.validate()

    def validate(self):
        for key_name, key_func, key_default in self.__keys__:
            try:
                self[key_name] = key_func(self.get(key_name, key_default))
            except ValueError as e:
                e.args += f"Validation of the dictionary failed! The value '{self[key_name]}' for {key_name} is invalid!"
                raise


def clean_name(string):
    """
    ``clean_name(string)``

    Function that makes sure that the string does not contain characters that
    should not be in a file name.
    """
    return re.sub(r"[^A-Za-z0-9]", r"", string)


def match_all(pattern, string):
    """
    ``match_all(pattern, string)``

    Function that checks if the pattern matches the whole string.
    """

    m = re.match(pattern, string)

    if m:
        return m.group() == string
    else:
        return False


def _safe_rmtree(path):
    """
    Best-effort recursive folder removal.

    Some filesystems can leave transient files behind during cleanup, which can
    cause shutil.rmtree to raise. This helper logs and continues.
    """
    try:
        shutil.rmtree(path)
    except Exception as e:
        print(f"WARNING unable to remove folder {path}: {e}")


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


def read_dicom_info(filename):
    """
    ``read_dicom_info(filename)``

    Reads basic information from DICOM files.

    INPUT
    =====

    --filename      The name of the `DICOM` file.

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
    """

    if not os.path.exists(filename):
        raise ValueError("DICOM file %s does not exist!" % (filename))

    d = read_dicom_base(filename)

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
    except:
        info["seriesNumber"] = None

    # --- seriesDescription -- multiple possibilities

    for key_name in ["SeriesDescription", "ProtocolName", "SequenceName"]:
        info["seriesDescription"] = d.get(key_name, "anonymous")
        if info["seriesDescription"].lower() != "anonymous":
            break

    # --- TR, TE

    tr, TE = 0.0, 0.0
    try:
        tr = d.RepetitionTime
    except:
        try:
            tr = float(d[0x2005, 0x1030].value)
        except:
            try:
                tr = d[0x2005, 0x1030].value[0]
            except:
                pass
    try:
        TE = d.EchoTime
    except:
        try:
            TE = float(d[0x2001, 0x1025].value)
        except:
            pass

    info["TR"], info["TE"] = float(tr), float(TE)

    # --- Frames

    info["volumes"] = 0
    try:
        info["volumes"] = int(d[0x2001, 0x1081].value)
    except:
        info["volumes"] = 0

    info["frames"] = info["volumes"]
    info["directions"] = info["volumes"]

    # --- slices

    try:
        info["slices"] = int(d[0x2001, 0x1018].value)
    except:
        try:
            info["slices"] = int(d[0x0019, 0x100A].value)
        except:
            info["slices"] = 0

    # --- datetime

    try:
        info["datetime"] = datetime.strptime(
            str(int(float(d.StudyDate + d.ContentTime))), "%Y%m%d%H%M%S"
        ).strftime("%Y-%m-%d %H:%M:%S")
    except:
        try:
            info["datetime"] = datetime.strptime(
                str(int(float(d.StudyDate + d.StudyTime))), "%Y%m%d%H%M%S"
            ).strftime("%Y-%m-%d %H:%M:%S")
        except:
            info["datetime"] = ""

    # --- SOPInstanceUID

    try:
        info["SOPInstanceUID"] = d.SOPInstanceUID
    except:
        info["SOPInstanceUID"] = None

    # --- ImageType

    try:
        info["ImageType"] = d[0x0008, 0x0008].value
    except:
        info["ImageType"] = ""

    # --- dicom header

    info["dicom"] = d

    # --- fileid

    info["fileid"], _ = os.path.splitext(os.path.basename(filename))

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

    return info


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
    except:
        # return None
        # print(" ---> WARNING: Could not partial read dicom file, attempting full read! [%s]" % (filename))
        try:
            d = dfr.read_file(filename, stop_before_pixels=True)
            return d
        except:
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
    except:
        try:
            time = datetime.strptime(
                str(int(float(info.StudyDate + info.StudyTime))), "%Y%m%d%H%M%S"
            ).strftime("%Y-%m-%d %H:%M:%S")
        except:
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
    tr, TE = 0, 0
    try:
        tr = info.RepetitionTime
    except:
        try:
            tr = float(info[0x2005, 0x1030].value)
            # TR = d[0x5200,0x9229][0][0x0018,0x9112][0][0x0018,0x0080].value
        except:
            try:
                tr = info[0x2005, 0x1030].value[0]
            except:
                pass
    try:
        TE = info.EchoTime
    except:
        try:
            TE = float(info[0x2001, 0x1025].value)
            # TE = d[0x5200,0x9230][0][0x0018,0x9114][0][0x0018,0x9082].value
        except:
            pass
    return float(tr), float(TE)


def dicom2nii(
    folder=".",
    clean="no",
    unzip="yes",
    gzip="folder",
    verbose=True,
    parelements=1,
    debug=False,
):
    """
    ``dicom2nii [folder=.] [clean=no] [unzip=ask] [gzip=folder] [verbose=True] [parelements=1]``

    Process sessions's DICOM or PAR/REC files and generate NIfTI files using dcm2niix.

    ..  qx_command:
        type: utility

    Parameters:
        --folder (str, default '.'):
            The base session folder with the dicom subfolder that holds session
            numbered folders with dicom files.

        --clean (str, default 'no'):
            Whether to remove preexisting NIfTI files ('yes'), leave them and
            abort ('no').

        --unzip (str, default 'yes'):
            If the dicom files are gziped whether to unzip them ('yes'), leave
            them be and abort ('no').

        --gzip (str, default 'folder'):
            Whether to gzip individual DICOM files after they were processed
            ('file'), gzip a DICOM sequence or acquisition as an tar.gz archive
            ('folder'), or leave them ungzipped ('no'). Valid options are
            'folder', 'file', 'no'.

        --verbose (bool, default True):
            Whether to report on the progress (True) or not (False).

        --parelements (int | str, default 1):
            How many parallel processes to run dcm2nii conversion with. The
            number is 1 by default, if specified as 'all', all available
            resources are utilized.

    Output files:
        After running, the command will place all the generated NIfTI files
        into the nii subfolder, named with sequential image number. It will
        also generate two additional files: a session.txt file and a
        DICOM-Report.txt file.

        session.txt file:
            The session.txt will be placed in the session base folder. It
            will contain the information about the session id, subject id,
            location of folders and a list of created NIfTI images with
            their description.

            An example session.txt file would be::

                id: OP169
                subject: OP169
                dicom: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/sessions/OP169/dicom
                raw_data: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/sessions/OP169/nii
                data: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/sessions/OP169/4dfp
                hcp: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/sessions/OP169/hcp
                01: Survey
                02: T1w 0.7mm N1
                03: T2w 0.7mm N1
                04: Survey
                05: C-BOLD 3mm 48 2.5s FS-P
                06: C-BOLD 3mm 48 2.5s FS-A
                07: BOLD 3mm 48 2.5s
                08: BOLD 3mm 48 2.5s
                09: BOLD 3mm 48 2.5s
                10: BOLD 3mm 48 2.5s
                11: BOLD 3mm 48 2.5s
                12: BOLD 3mm 48 2.5s
                13: RSBOLD 3mm 48 2.5s
                14: RSBOLD 3mm 48 2.5s

            For each of the listed images there will be a corresponding
            NIfTI file in the nii subfolder (e.g. 7.nii.gz for the first
            BOLD sequence), if a NIfTI file could be generated (Survey
            images for instance don't convert). The generated session.txt
            files form the basis for the following HCP and other processing
            steps.

        DICOM-Report.txt file:
            The DICOM-Report.txt file will be created and placed in the
            sessions' dicom subfolder. The file will list the images it
            found, the information about their original sequence number and
            the resulting NIfTI file number, the name of the sequence, the
            number of frames, TR and TE values, subject id, time of
            acquisition, information and warnings about any additional
            processing it had to perform (e.g. recenter structural images,
            switch f and z dimensions, reslice due to premature end of
            recording, etc.). In some cases some of the information (number
            of frames, TE, TR) might not be reported if that information was
            not present or couldn't be found in the DICOM file.

        dcm2nii log files:
            For each image conversion attempt a dcm2nii_[N].log file will be
            created that holds the output of the dcm2nii command that was
            run to convert the DICOM files to a NIfTI image.

    Notes:
        The command is used to convert MR images from DICOM to NIfTI format.
        It searches for images within the dicom subfolder within the
        provided session folder (folder). It expects to find each image
        within a separate subfolder. It then converts the images to NIfTI
        format and places them in the nii folder within the session folder.
        To reduce the space use it can then gzip the dicom files (gzip). To
        speed the process up, it can run multiple dcm2nii processes in
        parallel (parelements).

        Before running, the command check for presence of existing NIfTI
        files. The behavior when finding them is defined by clean parameter.
        If set to 'yes' it will remove any existing files and proceed. If set to
        'no' it will leave them and abort.

        Before running, the command also checks whether DICOM files might be
        gzipped. If that is the case, the response depends on the setting of
        the unzip parameter. If set to 'yes' it will automatically gunzip
        them and continue. If set to 'no', it will leave them be and abort.

        Multiple sessions and scheduling:
            The command can be run for multiple sessions by specifying
            `sessions` and optionally `sessionsfolder` and `parelements`
            parameters. In this case the command will be run for each of the
            specified sessions in the sessionsfolder (current directory by
            default). Optional `filter` and `sessionids` parameters can be
            used to filter sessions or limit them to just specified id
            codes. (for more information see online documentation).
            `sessionsfolder` will be filled in automatically as each
            sessions's folder. Commands will run in parallel by utilizing
            the specified number of parelements (1 by default).

            If `scheduler` parameter is set, the command will be run using
            the specified scheduler settings (see `qunex ?schedule` for more
            information). If set in combination with `sessions` parameter,
            sessions will be processed over multiple nodes, `core` parameter
            specifying how many sessions to run per node. Optional
            `scheduler_environment`, `scheduler_workdir`, `scheduler_sleep`,
            and `nprocess` parameters can be set.

            Set optional `logfolder` parameter to specify where the
            processing logs should be stored. Otherwise the processor will
            make best guess, where the logs should go.

    Examples:
        ::

            qunex dicom2nii \\
                --folder=. \\
                --clean=yes \\
                --unzip=yes \\
                --gzip=folder \\
                --parelements=3

        Multiple sessions example::

            qunex dicom2nii \\
                --sessionsfolder="/data/my_study/sessions" \\
                --sessions="OP*" \\
                --clean=yes \\
                --unzip=yes \\
                --gzip=no \\
                --parelements=3
    """

    print("Running dicom2nii\n=================")

    # debug = True
    base = folder
    null = open(os.devnull, "w")
    dmcf = os.path.join(folder, "dicom")
    imgf = os.path.join(folder, "nii")

    # parse parelements
    try:
        parelements = int(parelements)
    except:
        parelements = 1

    # check if dicom folder existis

    if not os.path.exists(dmcf):
        raise ge.CommandFailed(
            "dicom2nii",
            "No existing dicom folder",
            "Dicom folder with sorted dicom files does not exist at the expected location:",
            "[%s]." % (dmcf),
            "Please check your data!",
            "If inbox folder with dicom files exist, you first need to use sort_dicom command!",
        )

    # check for existing .gz files

    prior = glob.glob(os.path.join(imgf, "*.nii.gz")) + glob.glob(
        os.path.join(dmcf, "*", "*.nii.gz")
    )
    if len(prior) > 0:
        if clean == "yes":
            print("\nDeleting files:")
            for p in prior:
                print("---> ", p)
                os.remove(p)
        else:
            raise ge.CommandFailed(
                "dicom2nii",
                "Existing NIfTI files",
                "Please remove existing NIfTI files or run the command with 'clean' set to 'yes'.",
                "Aborting processing of DICOM files!",
            )

    # gzipped files

    zipped_file = glob.glob(os.path.join(dmcf, "*", "*.dcm.gz"))
    zipped_folder = glob.glob(os.path.join(dmcf, "*.tar.gz"))
    if len(zipped_file) > 0 or len(zipped_folder) > 0:
        if unzip == "yes":
            if verbose:
                print("\nUnzipping files (this might take a while)")
            _unzip_dicom(dmcf, parelements)
        else:
            raise ge.CommandFailed(
                "dicom2nii",
                "Gzipped DICOM files",
                "Can not work with gzipped DICOM files, please unzip them or run with 'unzip' set to 'yes'.",
                "Aborting processing of DICOM files!",
            )

    # --- open report files

    r = open(os.path.join(dmcf, "DICOM-Report.txt"), "w")
    stxt = open(os.path.join(folder, "session.txt"), "w")

    # --- Print header

    gc.print_qunex_header(file=r)
    gc.print_qunex_header(file=stxt)

    # get a list of folders

    folders = [e for e in os.listdir(dmcf) if os.path.isdir(os.path.join(dmcf, e))]
    folders = [int(e) for e in folders if e.isdigit()]
    folders.sort()
    folders = [os.path.join(dmcf, str(e)) for e in folders]

    if not os.path.exists(imgf):
        os.makedirs(imgf)

    first = True
    c = 0
    calls = []
    logs = []
    reps = []
    files = []

    for folder in folders:
        # d = dicom.read_file(glob.glob(os.path.join(folder, "*.dcm"))[-1], stop_before_pixels=True)
        d = read_dicom_base(glob.glob(os.path.join(folder, "*.dcm"))[-1])

        if d is None:
            print(
                "# WARNING: Could not read dicom file! Skipping folder %s" % (folder),
                file=r,
            )
            print(
                "---> WARNING: Could not read dicom file! Skipping folder %s" % (folder)
            )
            continue

        c += 1
        if first:
            first = False
            time = get_dicom_time(d)
            print("Report for %s scanned on %s\n" % (get_id(d), time), file=r)

            if verbose:
                print(
                    "\n\nProcessing images from %s scanned on %s\n" % (get_id(d), time)
                )

            # --- setup session.txt file

            print("id:", get_id(d), file=stxt)
            print("subject:", get_id(d), file=stxt)
            print("dicom:", os.path.abspath(os.path.join(base, "dicom")), file=stxt)
            print("raw_data:", os.path.abspath(os.path.join(base, "nii")), file=stxt)
            print("data:", os.path.abspath(os.path.join(base, "4dfp")), file=stxt)
            print("hcp:", os.path.abspath(os.path.join(base, "hcp")), file=stxt)
            print("", file=stxt)

            # ---> institution name
            if [0x0008, 0x0080] in d:
                print(f"Scanned at: {d[0x0008, 0x0080].value}", file=r)
                print(f"institution: {d[0x0008, 0x0080].value}", file=stxt)

            # ---> manufacturer and model
            MR = []
            for e in [[0x0008, 0x0070], [0x0008, 0x1090], [0x0008, 0x1010]]:
                if e in d:
                    print(f"{e}: {d[e].value}", file=r)
                    MR.append(d[e].value)
            if MR:
                print(f"device: {'|'.join(MR)}", file=stxt)

        try:
            series_description = d.SeriesDescription
        except:
            try:
                series_description = d.ProtocolName
            except:
                series_description = "None"

        try:
            time = datetime.strptime(d.ContentTime[0:6], "%H%M%S").strftime("%H:%M:%S")
        except:
            try:
                time = datetime.strptime(d.StudyTime[0:6], "%H%M%S").strftime(
                    "%H:%M:%S"
                )
            except:
                time = ""

        tr, TE = get_tr_te(d)

        try:
            nslices = d[0x2001, 0x1018].value
        except:
            nslices = 0

        recenter, dofz2zf, fz, reorder = False, False, "", False
        try:
            if (
                d.Manufacturer == "Philips Medical Systems"
                and int(d[0x2001, 0x1081].value) > 1
            ):
                dofz2zf, fz = True, "  (switched fz)"
            if (
                d.Manufacturer == "Philips Medical Systems"
                and d.SpacingBetweenSlices in [0.7, 0.8]
            ):
                recenter, fz = d.SpacingBetweenSlices, "  (recentered)"
            # if d.Manufacturer == 'SIEMENS' and d.InstitutionName == 'Univerisity North Carolina' and d.AcquisitionMatrix == [0, 64, 64, 0]:
            #    reorder, fz = True, " (reordered slices)"
        except:
            pass

        # --- Special nii naming for Philips

        niinum = c
        try:
            if d.Manufacturer == "Philips Medical Systems":
                niinum = (d.SeriesNumber - 1) / 100
        except:
            pass

        try:
            nframes = d[0x2001, 0x1081].value
            logs.append(
                "%4d  %4d %40s   %3d   [TR %7.2f, TE %6.2f]   %s   %s%s"
                % (
                    niinum,
                    d.SeriesNumber,
                    series_description,
                    nframes,
                    tr,
                    TE,
                    get_id(d),
                    time,
                    fz,
                )
            )
            reps.append(
                "---> %4d  %4d %40s   %3d   [TR %7.2f, TE %6.2f]   %s   %s%s"
                % (
                    niinum,
                    d.SeriesNumber,
                    series_description,
                    nframes,
                    tr,
                    TE,
                    get_id(d),
                    time,
                    fz,
                )
            )
        except:
            nframes = 0
            logs.append(
                "%4d  %4d %40s  [TR %7.2f, TE %6.2f]   %s   %s%s"
                % (
                    niinum,
                    d.SeriesNumber,
                    series_description,
                    tr,
                    TE,
                    get_id(d),
                    time,
                    fz,
                )
            )
            reps.append(
                "---> %4d  %4d %40s   [TR %7.2f, TE %6.2f]   %s   %s%s"
                % (
                    niinum,
                    d.SeriesNumber,
                    series_description,
                    tr,
                    TE,
                    get_id(d),
                    time,
                    fz,
                )
            )

        if niinum > 0:
            print("%4d: %s" % (niinum, series_description))

        niiid = str(niinum)
        calls.append(
            {
                "name": "dcm2nii: " + niiid,
                "args": ["dcm2nii", "-c", "-v", folder],
                "sout": os.path.join(
                    os.path.split(folder)[0], "dcm2nii_" + niiid + ".log"
                ),
            }
        )
        files.append([niinum, folder, dofz2zf, recenter, fz, reorder, nframes, nslices])

    done = gc.run_external_parallel(calls, cores=parelements, prepend=" ... ")

    for niinum, folder, dofz2zf, recenter, fz, reorder, nframes, nslices in files:
        print(logs.pop(0), file=r)
        if verbose:
            print(reps.pop(0), end=" ")
            if debug:
                print("")

        tfname = False
        imgs = glob.glob(os.path.join(folder, "*.nii*"))
        if debug:
            print(
                "     ---> found nifti files: %s"
                % ("\n                            ".join(imgs))
            )
        for image in imgs:
            if not os.path.exists(image):
                continue
            if debug:
                print(
                    "     ---> processing: %s [%s]" % (image, os.path.basename(image))
                )
            if image[-3:] == "nii":
                if debug:
                    print("     ---> gzipping: %s" % (image))
                subprocess.call("gzip " + image, shell=True, stdout=null, stderr=null)
                image += ".gz"
            if os.path.basename(image)[0:2] == "co":
                # os.rename(image, os.path.join(imgf, "%02d-co.nii.gz" % (c)))
                if debug:
                    print("         ... removing: %s" % (image))
                os.remove(image)
            elif os.path.basename(image)[0:1] == "o":
                if recenter:
                    if debug:
                        print("         ... recentering: %s" % (image))
                    tfname = os.path.join(imgf, "%02d-o.nii.gz" % (niinum))
                    timg = qxi.qximg(image)
                    if recenter == 0.7:
                        timg.hdrnifti.modify_header(
                            "srow_x:[0.7,0.0,0.0,-84.0];srow_y:[0.0,0.7,0.0,-112.0];srow_z:[0.0,0.0,0.7,-126];quatern_b:0;quatern_c:0;quatern_d:0;qoffset_x:-84.0;qoffset_y:-112.0;qoffset_z:-126.0"
                        )
                    elif recenter == 0.8:
                        timg.hdrnifti.modify_header(
                            "srow_x:[0.8,0.0,0.0,-94.8];srow_y:[0.0,0.8,0.0,-128.0];srow_z:[0.0,0.0,0.8,-130];quatern_b:0;quatern_c:0;quatern_d:0;qoffset_x:-94.8;qoffset_y:-128.0;qoffset_z:-130.0"
                        )
                    if debug:
                        print("         saving to: %s" % (tfname))
                    timg.saveimage(tfname)
                    if debug:
                        print("         removing: %s" % (image))
                    os.remove(image)
                else:
                    tfname = os.path.join(imgf, "%02d-o.nii.gz" % (niinum))
                    if debug:
                        print("         ... moving '%s' to '%s'" % (image, tfname))
                    os.rename(image, tfname)

                # -- remove original
                noob = os.path.join(folder, os.path.basename(image)[1:])
                noot = os.path.join(imgf, "%02d.nii.gz" % (niinum))
                if os.path.exists(noob):
                    if debug:
                        print("         ... removing '%s' [noob]" % (noob))
                    os.remove(noob)
                elif os.path.exists(noot):
                    if debug:
                        print("         ... removing '%s' [noot]" % (noot))
                    os.remove(noot)
            else:
                tfname = os.path.join(imgf, "%02d.nii.gz" % (niinum))
                if debug:
                    print("         ... moving '%s' to '%s'" % (image, tfname))
                os.rename(image, tfname)

            # --- check also for .bval and .bvec files

            for dwiextra in [".bval", ".bvec"]:
                dwisrc = image.replace(".nii.gz", dwiextra)
                if os.path.exists(dwisrc):
                    os.rename(dwisrc, os.path.join(imgf, "%02d%s" % (niinum, dwiextra)))

        # --- check if resulting nifti is present

        if len(imgs) == 0:
            print(" WARNING: no NIfTI file created!", file=r)
            if verbose:
                print(" WARNING: no NIfTI file created!")
            continue
        else:
            print("", file=r)
            print("")

        # --- flip z and t dimension if needed

        if dofz2zf:
            gn.fz2zf(os.path.join(imgf, "%02d.nii.gz" % (niinum)))

        # --- reorder slices if needed

        if reorder:
            # nifti.reorder(os.path.join(imgf,"%02d.nii.gz" % (niinum)))
            timgf = os.path.join(imgf, "%02d.nii.gz" % (niinum))
            timg = qxi.qximg(timgf)
            timg.data = timg.data[:, ::-1, ...]
            timg.hdrnifti.modify_header(
                "srow_x:[-3.4,0.0,0.0,-108.5];srow_y:[0.0,3.4,0.0,-102.0];srow_z:[0.0,0.0,5.0,-63.0];quatern_b:0;quatern_c:0;quatern_d:0;qoffset_x:108.5;qoffset_y:-102.0;qoffset_z:-63.0"
            )
            timg.saveimage(timgf)

        # --- check final geometry

        if tfname:
            hdr = gi.niftihdr(tfname)

            if hdr.sizez > hdr.sizey:
                print(
                    "     WARNING: unusual geometry of the NIfTI file: %d %d %d %d [xyzf]"
                    % (hdr.sizex, hdr.sizey, hdr.sizez, hdr.frames),
                    file=r,
                )
                if verbose:
                    print(
                        "     WARNING: unusual geometry of the NIfTI file: %d %d %d %d [xyzf]"
                        % (hdr.sizex, hdr.sizey, hdr.sizez, hdr.frames)
                    )

            if nframes > 1:
                if hdr.frames != nframes:
                    print(
                        "     WARNING: number of frames in nii does not match dicom information: %d vs. %d frames"
                        % (hdr.frames, nframes),
                        file=r,
                    )
                    if verbose:
                        print(
                            "     WARNING: number of frames in nii does not match dicom information: %d vs. %d frames"
                            % (hdr.frames, nframes)
                        )
                    if nslices > 0:
                        gframes = int(hdr.sizez / nslices)
                        if gframes > 1:
                            print(
                                "     WARNING: reslicing image to %d slices and %d good frames"
                                % (nslices, gframes),
                                file=r,
                            )
                            if verbose:
                                print(
                                    "     WARNING: reslicing image to %d slices and %d good frames"
                                    % (nslices, gframes)
                                )
                            gn.reslice(tfname, nslices)
                        elif hdr.sizez < nslices:
                            print(
                                "     WARNING: not enough slices (%d) to make a complete volume."
                                % (hdr.sizez),
                                file=r,
                            )
                            if verbose:
                                print(
                                    "     WARNING: not enough slices (%d) to make a complete volume."
                                    % (hdr.sizez)
                                )
                    else:
                        print(
                            "     WARNING: no slice number information, use qunex reslice manually to correct %s"
                            % (tfname),
                            file=r,
                        )
                        if verbose:
                            print(
                                "     WARNING: no slice number information, use qunex reslice manually to correct %s"
                                % (tfname)
                            )

    if verbose:
        print("... done!")

    r.close()
    stxt.close()

    # gzip files
    if gzip == "file" or gzip == "folder":
        if verbose:
            print("\nCompressing dicom with option {}:".format(gzip))

        with ProcessPoolExecutor(parelements) as executor:
            pending_futures = []
            for folder in folders:
                future = executor.submit(_zip_dicom, gzip, folder)
                print("submit archive dicom: {}".format(folder))
                pending_futures.append(future)

            exceptions = []
            for future in as_completed(pending_futures):
                if future.exception() is not None:
                    # Unhandled
                    e = future.exception()
                    print("Unhandled exception")
                    print(traceback.format_exc())
                    exceptions.append(e)
                    continue
                r = future.result()
                if r["status"] == "ok":
                    print("archived {}".format(r["args"]["dicom_folder"]))
                else:
                    print("archive failed {}".format(r["args"]["dicom_folder"]))
                    print(r["traceback"])
                    exceptions.append(r["exception"])
            if len(exceptions) > 0:
                raise ge.CommandError(
                    "dicom2nii", "Unable to archive one or more acquisitions"
                )


def dicom2niix(
    folder=".",
    clean="no",
    unzip="yes",
    gzip="folder",
    sessionid=None,
    verbose=True,
    parelements=1,
    debug=False,
    tool="auto",
    add_image_type=0,
    add_json_info="",
):
    """
    ``dicom2niix [folder=.] [clean=no] [unzip=yes] [gzip=folder] [sessionid=None] [verbose=True] [parelements=1] [tool='auto'] [add_image_type=0] [add_json_info=""]``

    Process sessions's DICOM or PAR/REC files and generate NIfTI files using dcm2niix.

    ..  qx_command:
        type: utility

    Parameters:
        --folder (str, default '.'):
            The base session folder with the dicom subfolder that holds session
            numbered folders with dicom files.

        --clean (str, default 'no'):
            Whether to remove preexisting NIfTI files ('yes'), leave them and
            abort ('no').

        --unzip (str, default 'yes'):
            If the dicom files are gziped whether to unzip them ('yes'), leave
            them be and abort ('no').

        --gzip (str, default 'folder'):
            Whether to gzip individual DICOM files after they were processed
            ('file'), gzip a DICOM sequence or acquisition as an tar.gz archive
            ('folder'), or leave them ungzipped ('no'). Valid options are
            'folder', 'file', 'no'.

        --sessionid (str, default ''):
            The id code to use for this session. If not provided, the session id
            is extracted from dicom files.

        --verbose (bool, default True):
            Whether to report on the progress (True) or not (False).

        --parelements (str, default '1'):
            How many parallel processes to run dcm2nii conversion with. The
            number is one by defaults, if specified as 'all', all available
            resources are utilized.

        --tool (str, default 'auto'):
            What tool to use for the conversion. It can be one of:

            - 'auto' (determine best tool based on heuristics)
            - 'dcm2niix'
            - 'dcm2nii'
            - 'dicm2nii'.

        --add_image_type (int, default 0):
            Adds image type information to the sequence name (Siemens scanners).
            The value should specify how many of image type labels from the end
            of the image type list to add.

        --add_json_info (str, default 'all'):
            What sequence information to extract from JSON sidecar files and add
            to session.txt file. Specify a comma separated list of fields or
            'all'. See list in session.txt file description below.

    Output files:
        After running, the command will place all the generated NIfTI files
        into the nii subfolder, named with sequential image number. It will
        also generate two additional files: a session.txt file and a
        DICOM-Report.txt file.

        session.txt file:
            The session.txt will be placed in the session base folder. It
            will contain the information about the session id, subject id,
            location of folders and a list of created NIfTI images with
            their description.

            Subject id will be extracted from the session id assuming the
            session id formula: `<subject id>_<session id>`. If there is no
            underscore in the session id, the subject id is assumed to
            equal session id.

            An example session.txt file would be::

                id: OP169_baseline
                subject: OP169
                dicom: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/sessions/OP169/dicom
                raw_data: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/sessions/OP169/nii
                data: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/sessions/OP169/4dfp
                hcp: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/sessions/OP169/hcp
                01: Survey
                02: T1w 0.7mm N1
                03: T2w 0.7mm N1
                04: Survey
                05: C-BOLD 3mm 48 2.5s FS-P
                06: C-BOLD 3mm 48 2.5s FS-A
                07: BOLD 3mm 48 2.5s
                08: BOLD 3mm 48 2.5s
                09: BOLD 3mm 48 2.5s
                10: BOLD 3mm 48 2.5s
                11: BOLD 3mm 48 2.5s
                12: BOLD 3mm 48 2.5s
                13: RSBOLD 3mm 48 2.5s
                14: RSBOLD 3mm 48 2.5s

            For each of the listed images there will be a corresponding
            NIfTI file in the nii subfolder (e.g. 7.nii.gz for the first
            BOLD sequence), if a NIfTI file could be generated (Survey
            images for instance don't convert). The generated session.txt
            files form the basis for the following HCP and other processing
            steps.

            The following information can be extracted from sidecar JSON
            files and added to the sequence information in session.txt
            file::

                :<fieldname>:       <JSON key>
                :TR:                RepetitionTime
                :PEDirection:       PhaseEncodingDirection
                :EchoSpacing:       EffectiveEchoSpacing
                :DwellTime:         DwellTime
                :ReadoutDirection:  ReadoutDirection

        DICOM-Report.txt file:
            The DICOM-Report.txt file will be created and placed in the
            session's dicom subfolder. The file will list the images it
            found, the information about their original sequence number and
            the resulting NIfTI file number, the name of the sequence, the
            number of frames, TR and TE values, session id, time of
            acquisition, information and warnings about any additional
            processing it had to perform (e.g. recenter structural images,
            switch f and z dimensions, reslice due to premature end of
            recording, etc.). In some cases some of the information (number
            of frames, TE, TR) might not be reported if that information
            was not present or couldn't be found in the DICOM file.

        log files:
            For each image conversion attempt a dcm2nii_[N] (or
            dicm2nii_[N].log) file will be created that holds the output of
            the command that was run to convert the DICOM or PAR/REC files
            to a NIfTI image.

    Notes:
        The command is used to convert MR images from DICOM and PAR/REC
        files to NIfTI format. It searches for images within the a dicom
        subfolder within the provided session folder (folder). It expects
        to find each image within a separate subfolder. It then converts
        the found images to NIfTI format and places them in the nii folder
        within the session folder. To reduce the space used it can then
        gzip the dicom or .REC files (gzip). The tool to be used for the
        conversion can be specified explicitly or determined automatically.
        It can be one of 'dcm2niix', 'dcm2nii', 'dicm2nii' or 'auto'. If
        set to 'auto', for dicom files the conversion is done using
        dcm2niix, and for PAR/REC files, dicm2nii is used if QuNex is set
        to use Matlab, otherwise also PAR/REC files are converted using
        dcm2niix. If set explicitly, the command will try to use the tool
        specified. To speed the process up, the command can run it can run
        multiple conversion processes in parallel. The number of processes
        to run in parallel is specified using the parelements parameter.

        Before running, the command check for presence of existing NIfTI
        files. The behavior when finding them is defined by clean
        parameter. If set to 'yes' it will remove any existing files and
        proceede. If set to 'no' it will leave them and abort.

        Before running, the command also checks whether DICOM or .REC files
        might be gzipped. If that is the case, the response depends on the
        setting of the unzip parameter. If set to 'yes' it will
        automatically gunzip them and continue. If set to 'no', it will
        leave them be and abort.

        Multiple sessions and scheduling:
            The command can be run for multiple sessions by specifying
            `sessions` and optionally `sessionsfolder` and `parelements`
            parameters. In this case the command will be run for each of
            the specified sessions in the sessionsfolder (current directory
            by default). Optional `filter` and `sessionids` parameters can
            be used to filter sessions or limit them to just specified id
            codes. (for more information see online documentation).
            `sfolder` will be filled in automatically as each sessions's
            folder. Commands will run in parallel by utilizing the
            specified number of parelements (1 by default).

            If `scheduler` parameter is set, the command will be run using
            the specified scheduler settings (see `qunex ?schedule` for
            more information). If set in combination with `sessions`
            parameter, sessions will be processed over multiple nodes,
            `core` parameter specifying how many sessions to run per node.
            Optional `scheduler_environment`, `scheduler_workdir`,
            `scheduler_sleep`, and `nprocess` parameters can be set.

            Set optional `logfolder` parameter to specify where the
            processing logs should be stored. Otherwise the processor will
            make best guess, where the logs should go.

    Examples:
        ::

            qunex dicom2niix \\
                --folder=. \\
                --clean=yes \\
                --unzip=yes \\
                --gzip=folder \\
                --parelements=3

        Multiple sessions example::

            qunex dicom2niix \\
                --sessionsfolder="/data/my_study/sessions" \\
                --sessions="OP*" \\
                --clean=yes \\
                --unzip=yes \\
                --gzip=no \\
                --parelements=3
    """

    print("Running dicom2niix\n==================")

    if sessionid and sessionid.lower() == "none":
        sessionid = None

    base = folder
    null = open(os.devnull, "w")
    dmcf = os.path.join(folder, "dicom")
    imgf = os.path.join(folder, "nii")

    try:
        if add_image_type == None or add_image_type == "":
            add_image_type = 0
        else:
            add_image_type = int(add_image_type)
    except:
        raise ge.CommandError(
            "dicom2niix",
            "Misspecified add_image_type",
            "The add_image_type argument value could not be converted to integer! [%s]"
            % (add_image_type),
            "Please check command instructions!",
        )
    # parse parelements
    try:
        parelements = int(parelements)
    except:
        parelements = 1

    if "," in add_json_info:
        add_json_info = [field.strip() for field in add_json_info.split(",")]

    # check tool setting

    if tool not in ["auto", "dcm2niix", "dcm2nii", "dicm2nii"]:
        raise ge.CommandError(
            "dicom2niix",
            "Incorrect tool specified",
            "The tool specified for conversion to nifti (%s) is not valid!" % (tool),
            "Please use one of dcm2niix, dcm2nii, dicm2nii or auto!",
        )

    # check if dicom folder existis

    if not os.path.exists(dmcf):
        raise ge.CommandFailed(
            "dicom2niix",
            "No existing dicom folder",
            "Dicom folder with sorted dicom files does not exist at the expected location:",
            "[%s]." % (dmcf),
            "Please check your data!",
            "If inbox folder with dicom files exist, you first need to use sort_dicom command!",
        )

    # check for existing .gz files

    prior = []
    for tfolder in [imgf, dmcf]:
        for ext in ["*.nii.gz", "*.bval", "*.bvec", "*.json"]:
            prior += glob.glob(os.path.join(tfolder, ext))

    if len(prior) > 0:
        if clean == "yes":
            print("\nDeleting preexisting files:")
            for p in prior:
                print("---> ", p)
                os.remove(p)
            print("")
        else:
            raise ge.CommandFailed(
                "dicom2niix",
                "Existing NIfTI files",
                "Please remove existing NIfTI files or run the command with 'clean' set to 'yes'.",
                "Aborting processing of DICOM files!",
            )

    # gzipped files

    zipped_file = glob.glob(os.path.join(dmcf, "*", "*.dcm.gz"))
    zipped_folder = glob.glob(os.path.join(dmcf, "*.tar.gz"))
    if len(zipped_file) > 0 or len(zipped_folder) > 0:
        if unzip == "yes":
            if verbose:
                print("\nUnzipping files (this might take a while)")
            _unzip_dicom(dmcf, parelements)
        else:
            raise ge.CommandFailed(
                "dicom2niix",
                "Gzipped DICOM files",
                "Can not work with gzipped DICOM files, please unzip them or run with 'unzip' set to 'yes'.",
                "Aborting processing of DICOM files!",
            )

    # --- open report files

    r = open(os.path.join(dmcf, "DICOM-Report.txt"), "w")
    stxt = open(os.path.join(folder, "session.txt"), "w")

    # --- Print header

    gc.print_qunex_header(file=r)
    gc.print_qunex_header(file=stxt)

    # get a list of folders

    folders = [e for e in os.listdir(dmcf) if os.path.isdir(os.path.join(dmcf, e))]
    folders = [int(e) for e in folders if e.isdigit()]
    folders.sort()
    folders = [os.path.join(dmcf, str(e)) for e in folders]

    if not os.path.exists(imgf):
        os.makedirs(imgf)

    first = True
    setdi = True
    c = 0
    calls = []
    logs = []
    reps = []
    files = []

    print("---> Analyzing data")

    for folder in folders:
        par = glob.glob(os.path.join(folder, "*.PAR"))
        if par:
            par = par[0]
            info = read_par_info(par)
        else:
            try:
                info = read_dicom_info(glob.glob(os.path.join(folder, "*.dcm"))[-1])
                if info["volumes"] == 0:
                    da, db, ta, tb = 0, 0, 0, 0
                    try:
                        da = info["dicom"][0x0020, 0x0012].value
                    except:
                        try:
                            db = info["dicom"][0x0020, 0x0013].value
                        except:
                            pass
                    if da > 0:
                        ta, tb = 0x0020, 0x0012
                    elif db > 0:
                        ta, tb = 0x0020, 0x0013

                    if ta > 0:
                        for dfile in glob.glob(os.path.join(folder, "*.dcm")):
                            tinfo = read_dicom_info(dfile)
                            info["volumes"] = max(
                                tinfo["dicom"][ta, tb].value, info["volumes"]
                            )

                    info["frames"] = info["volumes"]
                    info["directions"] = info["volumes"]
            except:
                print(
                    "# WARNING: Could not read dicom file! Skipping folder %s"
                    % (folder),
                    file=r,
                )
                print(
                    "---> WARNING: Could not read dicom file! Skipping folder %s"
                    % (folder)
                )
                continue

        if add_image_type > 0:
            retain = min(len(info["ImageType"]), add_image_type)
            if retain > 0:
                image_type = " ".join(info["ImageType"][-retain:])
                if len(image_type) > 0:
                    info["seriesDescription"] += " " + image_type

        c += 1
        if first:
            first = False
            if sessionid is None:
                sessionid = info["sessionid"]

            if "_" in sessionid:
                subjectid = sessionid.split("_")[0]
            else:
                subjectid = sessionid

            print(
                "Report for %s (%s) scanned on %s\n"
                % (sessionid, info["sessionid"], info["datetime"]),
                file=r,
            )
            if verbose:
                print(
                    "\nProcessing images from %s (%s) scanned on %s"
                    % (sessionid, info["sessionid"], info["datetime"])
                )

            # --- setup session.txt file

            print("id:", sessionid, file=stxt)
            print("subject:", subjectid, file=stxt)
            print("dicom:", os.path.abspath(os.path.join(base, "dicom")), file=stxt)
            print("raw_data:", os.path.abspath(os.path.join(base, "nii")), file=stxt)
            print("data:", os.path.abspath(os.path.join(base, "4dfp")), file=stxt)
            print("hcp:", os.path.abspath(os.path.join(base, "hcp")), file=stxt)
            print("", file=stxt)

            if "institution" in info:
                print(f"Scanned at: {info['institution']}", file=r)
                print(f"institution: {info['institution']}", file=stxt)

            if "device" in info:
                print(f"MR device: {info['device']}", file=r)
                print(f"device: {info['device']}", file=stxt)

            if "institution" in info or "device" in info:
                print("", file=r)
                print("", file=stxt)

        # recenter, dofz2zf, fz, reorder = False, False, "", False
        # try:
        #     if d.Manufacturer == 'Philips Medical Systems' and int(d[0x2001, 0x1081].value) > 1:
        #         dofz2zf, fz = True, "  (switched fz)"
        #     if d.Manufacturer == 'Philips Medical Systems' and d.SpacingBetweenSlices in [0.7, 0.8]:
        #         recenter, fz = d.SpacingBetweenSlices, "  (recentered)"
        #     # if d.Manufacturer == 'SIEMENS' and d.InstitutionName == 'Univerisity North Carolina' and d.AcquisitionMatrix == [0, 64, 64, 0]:
        #     #    reorder, fz = True, " (reordered slices)"
        # except:
        #     pass

        if info["seriesNumber"]:
            niinum = info["seriesNumber"] * 10
        else:
            niinum = c * 10

        info["niinum"] = niinum

        logs.append(
            "%(niinum)4d  %(seriesNumber)4d %(seriesDescription)40s   %(volumes)4d   [TR %(TR)7.2f, TE %(TE)6.2f]   %(sessionid)s   %(datetime)s"
            % (info)
        )
        reps.append(
            "---> %(niinum)4d  %(seriesNumber)4d %(seriesDescription)40s   %(volumes)4d   [TR %(TR)7.2f, TE %(TE)6.2f]   %(sessionid)s   %(datetime)s"
            % (info)
        )

        niiid = str(niinum)

        if tool == "auto":
            if par:
                utool = "dicm2nii"
                print(
                    "---> Using dicm2nii for conversion of PAR/REC to NIfTI if Matlab is available. [%s: %s]"
                    % (niiid, info["seriesDescription"])
                )
            else:
                utool = "dcm2niix"
                print(
                    "---> Using dcm2niix for conversion to NIfTI. [%s: %s]"
                    % (niiid, info["seriesDescription"])
                )
        else:
            utool = tool

        if utool == "dicm2nii":
            if "matlab" in mcommand:
                if setdi:
                    print("---> Setting up dicm2nii settings ...")
                    subprocess.call(
                        "matlab -nodisplay -r \"setpref('dicm2nii_gui_para', 'save_patientName', true); setpref('dicm2nii_gui_para', 'save_json', true); setpref('dicm2nii_gui_para', 'use_parfor', true); setpref('dicm2nii_gui_para', 'use_seriesUID', true); setpref('dicm2nii_gui_para', 'lefthand', true); setpref('dicm2nii_gui_para', 'scale_16bit', false); exit\" ",
                        shell=True,
                        stdout=null,
                        stderr=null,
                    )
                    print("     done!")
                    setdi = False
                calls.append(
                    {
                        "name": "dicm2nii: " + niiid,
                        "args": mcommand.split(" ")
                        + [
                            "try dicm2nii('%s', '%s'); catch ME, general_report_crash(ME); exit(1), end; exit"
                            % (folder, folder)
                        ],
                        "sout": os.path.join(
                            os.path.split(folder)[0], "dicm2nii_" + niiid + ".log"
                        ),
                    }
                )
            else:
                print(
                    "---> Using dcm2niix for conversion as Matlab is not available! [%s: %s]"
                    % (niiid, info["seriesDescription"])
                )
                if par:
                    calls.append(
                        {
                            "name": "dcm2niix: " + niiid,
                            "args": [
                                "dcm2niix",
                                "-f",
                                niiid,
                                "-z",
                                "y",
                                "-b",
                                "y",
                                "-o",
                                folder,
                                par,
                            ],
                            "sout": os.path.join(
                                os.path.split(folder)[0], "dcm2niix_" + niiid + ".log"
                            ),
                        }
                    )
                else:
                    calls.append(
                        {
                            "name": "dcm2niix: " + niiid,
                            "args": [
                                "dcm2niix",
                                "-f",
                                niiid,
                                "-z",
                                "y",
                                "-b",
                                "y",
                                "-o",
                                folder,
                            ],
                            "sout": os.path.join(
                                os.path.split(folder)[0], "dcm2niix_" + niiid + ".log"
                            ),
                        }
                    )

        elif utool == "dcm2nii":
            if par:
                calls.append(
                    {
                        "name": "dcm2nii: " + niiid,
                        "args": ["dcm2nii", "-c", "-v", folder, par],
                        "sout": os.path.join(
                            os.path.split(folder)[0], "dcm2nii_" + niiid + ".log"
                        ),
                    }
                )
            else:
                calls.append(
                    {
                        "name": "dcm2nii: " + niiid,
                        "args": ["dcm2nii", "-c", "-v", folder],
                        "sout": os.path.join(
                            os.path.split(folder)[0], "dcm2nii_" + niiid + ".log"
                        ),
                    }
                )
        else:
            if par:
                calls.append(
                    {
                        "name": "dcm2niix: " + niiid,
                        "args": [
                            "dcm2niix",
                            "-f",
                            niiid,
                            "-z",
                            "y",
                            "-b",
                            "y",
                            "-o",
                            folder,
                            par,
                        ],
                        "sout": os.path.join(
                            os.path.split(folder)[0], "dcm2niix_" + niiid + ".log"
                        ),
                    }
                )
            else:
                calls.append(
                    {
                        "name": "dcm2niix: " + niiid,
                        "args": ["dcm2niix", "-f", niiid, "-z", "y", "-b", "y", folder],
                        "sout": os.path.join(
                            os.path.split(folder)[0], "dcm2niix_" + niiid + ".log"
                        ),
                    }
                )
        files.append([niinum, folder, info])

    if not calls:
        r.close()
        stxt.close()
        for clean_file in [
            os.path.join(dmcf, "DICOM-Report.txt"),
            os.path.join(folder, "session.txt"),
        ]:
            if os.path.exists(clean_file):
                os.remove(clean_file)
        raise ge.CommandFailed(
            "dicom2niix",
            "No source DICOM files",
            "No source DICOM files were found to process!",
            "Please check your data and paths!",
        )

    gc.run_external_parallel(calls, cores=parelements, prepend=" ... ")

    print("\nProcessed sequences:")
    for niinum, folder, info in files:
        print(logs.pop(0), end=" ", file=r)
        if verbose:
            print(reps.pop(0), end=" ")
            if debug:
                print("")

        tfname = False
        imgs = glob.glob(os.path.join(folder, "*.nii*"))
        imgs.sort()

        # --- check if resulting nifti is present

        nimg = len(imgs)
        if nimg == 0:
            print(" WARNING: no NIfTI file created!", file=r)
            if verbose:
                print(" WARNING: no NIfTI file created!")
            continue
        elif nimg > 9:
            print(
                " WARNING: More than 9 images created from this sequence! Skipping. Please check conversion log!",
                file=r,
            )
            if verbose:
                print(
                    " WARNING: More than 9 images created from this sequence! Skipping. Please check conversion log!"
                )
            continue
        else:
            print("", file=r)
            print("")

            imgnum = 0

            if debug:
                print(
                    "     ---> found %s nifti file(s): %s"
                    % (nimg, "\n                            ".join(imgs))
                )

            for image in imgs:
                if not os.path.exists(image):
                    continue
                if debug:
                    print(
                        "     ---> processing: %s [%s]"
                        % (image, os.path.basename(image))
                    )
                if image.endswith(".nii"):
                    if debug:
                        print("     ---> gzipping: %s" % (image))
                    subprocess.call(
                        "gzip " + image, shell=True, stdout=null, stderr=null
                    )
                    image += ".gz"

                # ---> compile the basename of the target file(s) for nii folder
                imgnum += 1
                imgname = os.path.basename(image)
                tbasename = "%d" % (niinum + imgnum)

                # ---> extract any suffices to add to the session.txt
                suffix = ""
                if "_" in imgname:
                    suffix = " " + "_".join(
                        imgname.replace(".nii.gz", "")
                        .replace(info["fileid"], "")
                        .split("_")[1:]
                    )

                # ---> generate the actual target file path and move the image
                tfname = os.path.join(imgf, "%s.nii.gz" % (tbasename))
                if debug:
                    print("         ... moving '%s' to '%s'" % (image, tfname))
                os.rename(image, tfname)

                # ---> check for .bval and .bvec files
                for dwiextra in [".bval", ".bvec"]:
                    dwisrc = image.replace(".nii.gz", dwiextra)
                    if os.path.exists(dwisrc):
                        os.rename(
                            dwisrc, os.path.join(imgf, "%s%s" % (tbasename, dwiextra))
                        )

                # ---> initialize JSON information

                jsoninfo = ""
                jinf = {}

                # ---> check for .json files and extract info if present

                for jsonextra in [".json", ".JSON"]:
                    jsonsrc = image.replace(".gz", "")
                    jsonsrc = jsonsrc.replace(".nii", "")
                    jsonsrc += jsonextra

                    if not os.path.exists(jsonsrc):
                        jsonfiles = glob.glob(os.path.join(folder, "*" + jsonextra))
                        if len(jsonfiles) == 1:
                            jsonsrc = jsonfiles[0]

                    if os.path.exists(jsonsrc):
                        try:
                            with open(jsonsrc, "r") as f:
                                jinf = json.load(f)
                            os.rename(jsonsrc, tfname.replace(".nii.gz", ".json"))
                            jsonsrc = tfname.replace(".nii.gz", ".json")

                            if "RepetitionTime" in jinf and (
                                "TR" in add_json_info or "all" in add_json_info
                            ):
                                jsoninfo += ": TR(%s)" % (str(jinf["RepetitionTime"]))
                            if "PhaseEncodingDirection" in jinf and (
                                "PEDirection" in add_json_info or "all" in add_json_info
                            ):
                                jsoninfo += ": PEDirection(%s)" % (
                                    jinf["PhaseEncodingDirection"].strip()
                                )
                            if "EffectiveEchoSpacing" in jinf and (
                                "EchoSpacing" in add_json_info or "all" in add_json_info
                            ):
                                jsoninfo += ": EchoSpacing(%s)" % (
                                    str(jinf["EffectiveEchoSpacing"])
                                )
                            if "DwellTime" in jinf and (
                                "DwellTime" in add_json_info or "all" in add_json_info
                            ):
                                jsoninfo += ": DwellTime(%s)" % (str(jinf["DwellTime"]))
                            if "ReadoutDirection" in jinf and (
                                "ReadoutDirection" in add_json_info
                                or "all" in add_json_info
                            ):
                                jsoninfo += ": ReadoutDirection(%s)" % (
                                    jinf["ReadoutDirection"].strip()
                                )
                        except:
                            print(
                                "     WARNING: Could not parse the JSON file [%s]!"
                                % (jsonsrc),
                                file=r,
                            )
                            if verbose:
                                print(
                                    "     WARNING: Could not parse the JSON file [%s]!"
                                    % (jsonsrc)
                                )

                # ---> print the info to session.txt file

                numinfo = ""
                if nimg > 1:
                    numinfo = " [%d/%d]" % (imgnum, nimg)

                print(
                    "%-4s: %-25s %s"
                    % (
                        tbasename,
                        info["seriesDescription"] + numinfo + suffix,
                        jsoninfo,
                    ),
                    file=stxt,
                )

                # --- check final geometry

                if tfname:
                    hdr = gi.niftihdr(tfname)

                    if hdr.sizez > hdr.sizey and hdr.sizex < 150:
                        print(
                            "     WARNING: unusual geometry of the NIfTI file: %d %d %d %d [xyzf]"
                            % (hdr.sizex, hdr.sizey, hdr.sizez, hdr.frames),
                            file=r,
                        )
                        if verbose:
                            print(
                                "     WARNING: unusual geometry of the NIfTI file: %d %d %d %d [xyzf]"
                                % (hdr.sizex, hdr.sizey, hdr.sizez, hdr.frames)
                            )

                    if info["volumes"] > 1:
                        if hdr.frames != info["volumes"]:
                            print(
                                "     WARNING: number of frames in nii does not match dicom information: %d vs. %d frames"
                                % (hdr.frames, info["volumes"]),
                                file=r,
                            )
                            if verbose:
                                print(
                                    "     WARNING: number of frames in nii does not match dicom information: %d vs. %d frames"
                                    % (hdr.frames, info["volumes"])
                                )
                            if info["slices"] > 0:
                                gframes = int(hdr.sizez / info["slices"])
                                if gframes > 1:
                                    print(
                                        "     WARNING: reslicing image to %d slices and %d good frames"
                                        % (info["slices"], gframes),
                                        file=r,
                                    )
                                    if verbose:
                                        print(
                                            "     WARNING: reslicing image to %d slices and %d good frames"
                                            % (info["slices"], gframes)
                                        )
                                    gn.reslice(tfname, info["slices"])
                                elif hdr.sizez < info["slices"]:
                                    print(
                                        "     WARNING: not enough slices (%d) to make a complete volume."
                                        % (hdr.sizez),
                                        file=r,
                                    )
                                    if verbose:
                                        print(
                                            "     WARNING: not enough slices (%d) to make a complete volume."
                                            % (hdr.sizez)
                                        )
                            else:
                                print(
                                    "     WARNING: no slice number information, use qunex reslice manually to correct %s"
                                    % (tfname),
                                    file=r,
                                )
                                if verbose:
                                    print(
                                        "     WARNING: no slice number information, use qunex reslice manually to correct %s"
                                        % (tfname)
                                    )

    r.close()
    stxt.close()

    # gzip files
    if gzip == "file" or gzip == "folder":
        if verbose:
            print("\nCompressing dicom with option {}:".format(gzip))

        with ProcessPoolExecutor(parelements) as executor:
            pending_futures = []
            for folder in folders:
                future = executor.submit(_zip_dicom, gzip, folder)
                print("submit archive dicom: {}".format(folder))
                pending_futures.append(future)

            exceptions = []
            for future in as_completed(pending_futures):
                if future.exception() is not None:
                    # Unhandled
                    e = future.exception()
                    print("Unhandled exception")
                    print(traceback.format_exc())
                    exceptions.append(e)
                    continue
                r = future.result()
                if r["status"] == "ok":
                    print("archived {}".format(r["args"]["dicom_folder"]))
                else:
                    print("archive failed {}".format(r["args"]["dicom_folder"]))
                    print(r["traceback"])
                    exceptions.append(r["exception"])
            if len(exceptions) > 0:
                raise ge.CommandError(
                    "dicom2nii", "Unable to archive one or more acquisitions"
                )


def _zip_dicom(gzip, dicom_folder):
    """
    Compress or archive a dicom acquisition folder or file

    This function archives the dicom acquisition folder a single tar.gz file
    when gzip=folder. A hidden temporary tar.gz file will be created and will
    be renamed after the dicom acquisition folder is completely archived. If
    gzip=file is set, gzip will compress individual files in the dicom
    acquisition folder.

    This function can be called through ProcessPoolExecutor.
    """
    r = {"args": {"gzip": gzip, "dicom_folder": dicom_folder}}
    try:
        if not os.path.exists(dicom_folder):
            raise ge.CommandFailed(
                "_zip_dicom", "Unable to find acquisition folder %s" % (dicom_folder)
            )
        if not os.path.isdir(dicom_folder):
            raise ge.CommandFailed("_zip_dicom", "%s is not a folder" % (dicom_folder))

        dicom_dir, dicom_num = os.path.split(dicom_folder)
        if gzip == "folder":
            dicom_folder_zip = os.path.join(dicom_dir, "{}.tar.gz".format(dicom_num))
            dicom_folder_zip_tmp = os.path.join(
                dicom_dir, ".{}.tar.gz".format(dicom_num)
            )

            if os.path.exists(dicom_folder_zip):
                os.remove(dicom_folder_zip)
            if os.path.exists(dicom_folder_zip_tmp):
                os.remove(dicom_folder_zip_tmp)

            p = subprocess.run(
                [
                    "tar",
                    "czf",
                    os.path.abspath(dicom_folder_zip_tmp),
                    os.path.basename(dicom_folder),
                ],
                cwd=os.path.dirname(dicom_folder),
            )

            if p.returncode != 0:
                raise ge.CommandFailed(
                    "_zip_dicom",
                    "Unable to archive: tar exit code: %d" % (p.returncode),
                )

            os.rename(dicom_folder_zip_tmp, dicom_folder_zip)
            _safe_rmtree(dicom_folder)

        elif gzip == "file":
            p = subprocess.run(["gzip", "-r", dicom_folder])

            if p.returncode != 0:
                raise ge.CommandFailed(
                    "_zip_dicom",
                    "Unable to archive: gzip exit code: %d" % (p.returncode),
                )
        r["status"] = "ok"
    except Exception as e:
        r["status"] = "error"
        r["exception"] = e
        r["traceback"] = traceback.format_exc()
    return r


def _get_zip_file_content_iterator(packet_name):
    """
    Return an iterator over all the files in an zip or tar archive.

    The iterator yields the file name and a file object opened in binary mode
    """

    def zip_gen():
        try:
            z = zipfile.ZipFile(packet_name, "r")
            fobj = None
            for f in z.infolist():
                if f.is_dir():
                    continue
                fobj = z.open(f, "rb")
                yield f.filename, fobj
                fobj.close()
        except:
            e = sys.exc_info()[0]
            raise ge.CommandFailed(
                "_get_zip_file_content_iterator",
                "Zip file could not be processed",
                "Opening zip [%s] returned an error [%s]!" % (packet_name, e),
                "Please check your data!",
            )
        finally:
            if fobj is not None:
                fobj.close()
            if z is not None:
                z.close()

    def tar_gen():
        try:
            tar = tarfile.open(packet_name, "r")
            fobj = None
            for tarinfo in tar:
                if tarinfo.isfile():
                    fobj = tar.extractfile(tarinfo)
                    yield tarinfo.name, fobj
                    fobj.close()
        except:
            pass
        finally:
            if fobj is not None:
                fobj.close()
            if tar is not None:
                tar.close()

    if not os.path.exists(packet_name):
        raise ge.CommandFailed(
            "_get_zip_file_content_iterator",
            "Packet does not exist {}".format(packet_name),
        )

    if packet_name.endswith("zip"):
        return zip_gen()
    elif re.search(
        r"\.tar$|\.tar\.gz$|\.tar\.bz2$|\.tarz$|\.tar\.bzip2$|\.tgz$", packet_name
    ):
        return tar_gen()
    else:
        raise ge.CommandFailed("_get_zip_file_content_iterator", "Unknown packet type")


def _unzip_dicom_folder(dicom_packet, dicom_folder):
    """
    Extract archived dicom acquisition.

    The zip/tar dicom packet (dicom_packet) will be extracted into the dicom
    acquisition folder (dicom_folder).If the input packet contains gzipped
    dicom files, they will also be decompressed on-the-fly to minimize I/O
    operations.

    Archived dicom_packets generated by dicom2niix/dicom2nii will not compress
    individual dicom files as gzip in gzip=folder mode. This would allow user
    to manually archive dicom acquisition folders previously processed in
    gzip=file mode.

    This function can be called through ProcessPoolExecutor.
    """
    r = {"args": {"dicom_packet": dicom_packet, "dicom_folder": dicom_folder}}
    try:
        if not os.path.exists(dicom_folder):
            os.mkdir(dicom_folder)

        for fpath, fobj in _get_zip_file_content_iterator(dicom_packet):
            extract_path = os.path.join(dicom_folder, os.path.basename(fpath))
            if fpath.endswith(".gz"):
                extract_path, _ = extract_path.rsplit(".", 1)
            with open(extract_path, "wb") as f:
                if fpath.endswith(".gz"):
                    with gz.GzipFile(fileobj=fobj) as gzobj:
                        shutil.copyfileobj(gzobj, f)
                else:
                    shutil.copyfileobj(fobj, f)

        r["status"] = "ok"
    except Exception as e:
        r["status"] = "error"
        r["exception"] = e
        r["traceback"] = traceback.format_exc()
    return r


def _unzip_dicom_file(dicom_folder):
    """
    Decompress gzip files in a dicom acquisition folder

    This function can be called through ProcessPoolExecutor.
    """
    r = {"args": {"dicom_folder": dicom_folder}}
    try:
        p = subprocess.run(["gunzip", "-r", dicom_folder])
        if p.returncode != 0:
            raise ge.CommandError(
                "_unzip_dicom_file",
                "Unable to unzip dicom files: gunzip exit code: %d" % p.returncode,
            )
        r["status"] = "ok"
    except Exception as e:
        r["status"] = "error"
        r["exception"] = e
        r["traceback"] = traceback.format_exc()
    return r


def _unzip_dicom(dicom_root_folder, parelements):
    """
    Find and unzip archived dicom folders and files.

    This function finds archived dicom folders created by previous import dicom
    runs
    """
    with ProcessPoolExecutor(parelements) as executor:
        pending_futures = []
        for i in os.listdir(dicom_root_folder):
            fullpath = os.path.join(dicom_root_folder, i)
            if os.path.isfile(fullpath):
                match_result = re.match(
                    r"^(?P<dcm_name>\d+)(\.zip|\.tar|\.tar\.gz|\.tar\.bz2|\.tar\.xz|\.tarz|\.tar\.bzip2|\.tgz)$",
                    i,
                )
                if match_result:
                    dcm_name = match_result.group("dcm_name")
                    print("submit unzip dicom folder: {}".format(dcm_name))
                    if not dcm_name.isdigit():
                        continue
                    future = executor.submit(
                        _unzip_dicom_folder,
                        fullpath,
                        os.path.join(dicom_root_folder, dcm_name),
                    )
                    pending_futures.append(future)
        exceptions = []
        for future in as_completed(pending_futures):
            if future.exception() is not None:
                # Unhandled
                e = future.exception()
                print("Unhandled exception")
                print(traceback.format_exc())
                exceptions.append(e)
                continue
            r = future.result()
            if r["status"] == "ok":
                print(
                    "unzipped {} -> {}".format(
                        r["args"]["dicom_packet"], r["args"]["dicom_folder"]
                    )
                )
            else:
                print(
                    "unzip failed {} -> {}".format(
                        r["args"]["dicom_packet"], r["args"]["dicom_folder"]
                    )
                )
                print(r["traceback"])
                exceptions.append(r["exception"])
        # raise exception after the status of all child processes are collected
        if len(exceptions) > 0:
            raise ge.CommandError(
                "_unzip_dicom", "Unable to unzip one or more acquisition folders"
            )

        pending_futures.clear()
        for i in os.listdir(dicom_root_folder):
            fullpath = os.path.join(dicom_root_folder, i)
            if os.path.isdir(fullpath):
                glob_iter = glob.iglob(os.path.join(fullpath, "*.gz"))
                if next(glob_iter, None):
                    future = executor.submit(_unzip_dicom_file, fullpath)
                    pending_futures.append(future)

        exceptions.clear()
        for future in as_completed(pending_futures):
            if future.exception() is not None:
                # Unhandled
                e = future.exception()
                print("Unhandled exception")
                print(traceback.format_exc())
                exceptions.append(e)
                continue
            r = future.result()
            if r["status"] == "ok":
                print("extract gzipped dicoms {}".format(r["args"]["dicom_folder"]))
            else:
                print(
                    "extract gzipped dicoms failed {}".format(r["args"]["dicom_folder"])
                )
                print(r["traceback"])
                exceptions.append(r["exception"])
        # raise exception after the status of all child processes are collected
        if len(exceptions) > 0:
            raise ge.CommandError("_unzip_dicom", "Unable to unzip one or more files")


def sort_dicom(folder=".", copy='move', outdir=None, files=None):
    """
    ``sort_dicom [folder=.]``

    Sort DICOM files from the specified folder.

    ..  qx_command:
        type: utility

    Parameters:
        --folder (str, default '.'):
            The base session folder that contains the inbox subfolder with the
            unsorted DICOM files.

        --copy (str, default 'move'):
            Should we 'copy' or 'move'.

        --outdir (str, default detailed below):
            Optional directory where the sorted files are to be saved. Defaults
            to `folder` parameter if not set.

        --files (str, default detailed below):
            Comma separated list of files to sort. Defaults to files in `folder`.

    Notes:
        The command looks for the inbox subfolder in the specified session
        folder (folder) and checks for presence of DICOM or PAR/REC files in
        the inbox folder and its subfolders. It inspects the found files,
        creates a dicom folder and for each image a numbered subfolder. It then
        moves the found DICOM or PAR/REC files in the correct subfolders to
        prepare them for dicom2nii(x) processing. In the process it checks that
        PAR/REC extensions are uppercase and changes them if necessary. If log
        files are found, they are placed in a separate `log` subfolder.

        Multiple sessions and scheduling:
            The command can be run for multiple sessions by specifying
            `sessions` and optionally `sessionsfolder` and `parelements`
            parameters. In this case the command will be run for each of the
            specified sessions in the sessionsfolder (current directory by
            default). Optional `filter` and `sessionids` parameters can be used
            to filter sessions or limit them to just specified id codes. (for
            more information see online documentation). `sfolder` will be
            filled in automatically as each session's folder. Commands will
            run in parallel by utilizing the specified number of parelements (1
            by default).

            If `scheduler` parameter is set, the command will be run using the
            specified scheduler settings (see `qunex ?schedule` for more
            information). If set in combination with `sessions` parameter,
            sessions will be processed over multiple nodes, `core` parameter
            specifying how many sessions to run per node. Optional
            `scheduler_environment`, `scheduler_workdir`, `scheduler_sleep`,
            and `nprocess` parameters can be set.

            Set optional ``logfolder`` parameter to specify where the processing
            logs should be stored. Otherwise, the processor will make best
            guess, where the logs should go.

    Examples:
        Single sessions example::

            qunex sort_dicom \\
                --folder=OP667

        Multiple sessions example::

            qunex sort_dicom \\
                  --sessionsfolders="/data/my_study/sessions" \\
                  --sessions="OP*"
    """

    # --- should we copy or move

    print("Running sort_dicom\n=================")

    if copy is None:
        copy = 'move'

    if copy == 'copy':
        from shutil import copy
        do_file = copy
    else:
        do_file = os.rename

    # --- establish target folder

    if outdir is None:
        dcmf = os.path.join(folder, "dicom")
    else:
        dcmf = os.path.join(outdir, "dicom")

    # --- get list of files

    if files is None:
        inbox = os.path.join(folder, "inbox")
        if not os.path.exists(inbox):
            raise ge.CommandFailed(
                "sort_dicom",
                "Inbox folder not found",
                "Please check your paths! [%s]" % (os.path.abspath(inbox)),
                "Aborting",
            )
        files_iter = glob.iglob(os.path.join(inbox, "**", "*"), recursive=True)

        # if len(files):
        #     files = []
        #     for droot, _, dfiles in os.walk(inbox):
        #         for dfile in dfiles:
        #             files.append(os.path.join(droot, dfile))
        #     print("---> Processing %d files from %s" % (len(files), inbox))
        # else:
        #     raise ge.CommandFailed("sort_dicom", "No files found", "Please check the specified inbox folder! [%s]" % (os.path.abspath(inbox)), "Aborting")
    else:
        files_iter = [e.strip() for e in files.split(",")]

    info = None

    if not os.path.exists(dcmf):
        os.makedirs(dcmf)
        print("---> Created a dicom superfolder")

    log_folder = os.path.join(dcmf, "log")

    dcmn = 0

    show_session_info = True

    for dcm in files_iter:
        if os.path.isdir(dcm):
            continue

        ext = dcm.split(".")[-1]

        if os.path.basename(dcm)[0:4] in ["XX_0", "PS_0"]:
            continue

        elif ext == "log":
            if not os.path.exists(log_folder):
                os.makedirs(log_folder)
                print("---> Created log folder")
            do_file(dcm, os.path.join(log_folder, os.path.basename(dcm)))
            continue

        elif ext.lower() == "par":
            info = read_par_info(dcm)

        else:
            try:
                info = read_dicom_info(dcm)
            except:
                continue

        if show_session_info:
            if info and info["sessionid"]:
                print(
                    "---> Sorting dicoms for %s scanned on %s"
                    % (info["sessionid"], info["datetime"])
                )
                show_session_info = False

        if info["seriesNumber"] is None:
            print("---> Skipping file", dcm)
            continue

        sqid = str(info["seriesNumber"] * 10)
        sqfl = os.path.join(dcmf, sqid)

        if not os.path.exists(sqfl):
            os.makedirs(sqfl)
            print(
                "---> Created subfolder for sequence %s %s - %s"
                % (info["sessionid"], sqid, info["seriesDescription"])
            )

        if ext.lower() == "par":
            tgpar = os.path.join(sqfl, os.path.basename(dcm))
            tgpar = tgpar[:-3] + "PAR"
            do_file(dcm, tgpar)

            if os.path.exists(dcm[:-3] + "REC"):
                do_file(dcm[:-3] + "REC", tgpar[:-3] + "REC")
            elif os.path.exists(dcm[:-3] + "rec"):
                do_file(dcm[:-3] + "rec", tgpar[:-3] + "REC")
            else:
                print("---> Warning %s does not exist!" % (dcm[:-3] + "REC"))

        else:
            # --- get info for dcm naming

            dcmn += 1
            if info["SOPInstanceUID"]:
                sop = info["SOPInstanceUID"]
            else:
                sop = "%010d" % (dcmn)

            # --- check if for some reason we are dealing with gzipped dicom files and add an extension when renaming

            if ext == "gz":
                dext = ".gz"
            else:
                dext = ""

            # --- do the deed

            tgf = os.path.join(
                sqfl, "%s-%s-%s.dcm%s" % (clean_name(info["sessionid"]), sqid, sop, dext)
            )
            do_file(dcm, tgf)

    print("---> Processed %d dicom files from %s" % (dcmn, inbox))

    print("---> Done")
    return


def clean_dicom(
    folder=".",
    tol_mm=0.2,
    min_files=10,
    verbose="yes",
    move_non_image=True,
    move_incomplete=True,
):
    r"""
    ``clean_dicom [folder=.] [tol_mm=0.2] [min_files=10] [verbose=yes] [move_non_image=True] [move_incomplete=True]``

    Inspects DICOM files within sequence subfolders and identifies DICOM files
    that do not hold imaging data or that contain slice data that does not
    complete a full volume (e.g., from interrupted scans). These files are
    moved to designated removal folders to prevent processing errors during
    DICOM to NIfTI conversion.

    Parameters:
        --folder (str, default '.'):
            The base session folder that contains the 'dicom' subfolder with
            sorted DICOM files organized in numbered sequence subfolders. This
            parameter is typically the session folder path when called from
            import_dicom.

        --tol_mm (float, default 0.2):
            Tolerance in millimeters for clustering slice positions into Z
            indices. This parameter controls how strictly slice positions must
            match to be considered part of the same spatial location. Increase
            this value for acquisitions with slight positional variations;
            decrease it for more stringent matching. Default: 0.2 mm.

        --min_files (int, default 10):
            Minimum number of image files required for a sequence to be
            processed. Sequences with fewer image files than this threshold
            will be skipped and reported. This helps avoid false positives from
            localizer scans or other short sequences. Default: 10.

        --verbose (str, default 'yes'):
            Controls the verbosity of output messages. Set to 'yes' for detailed
            reporting of each sequence processed, including statistics on
            detected volumes and incomplete timepoints. Set to 'no' for minimal
            output showing only critical information and summary statistics.

        --move_non_image (bool, default True):
            Whether to move DICOM files that do not contain imaging data (e.g.,
            files with only metadata, presentation states, or other non-image
            DICOM objects) to the 'dicom/non-image' folder. When True, such
            files are moved; when False, they are left in place.

        --move_incomplete (bool, default True):
            Whether to move DICOM files that are part of incomplete volumes
            (volumes missing slices) to the 'dicom/_REMOVED' folder. When True,
            files from timepoints that do not contain all expected slices are
            moved; when False, they are left in place. This is the primary
            mechanism for handling interrupted scans.

    Notes:
        The command processes sorted DICOM files to identify and remove
        problematic files before conversion to NIfTI format. It is designed to
        handle the common scenario of interrupted fMRI acquisitions where some
        timepoints may be incomplete due to scanner interruption, subject
        motion, or other acquisition issues.

        The cleaning process consists of several steps:

        Sequence folder identification:
            The command scans the 'dicom' folder within the specified session
            folder for sequence subfolders. Sequence subfolders are identified
            by integer names (e.g., '1', '2', '3'). Special folders like
            '_REMOVED' and 'non-image' are excluded from processing. Each
            identified sequence folder is processed independently.

        DICOM header inspection:
            For each file in a sequence folder, the DICOM header is read using
            pydicom with stop_before_pixels=True for efficiency. Files are
            classified as either:

            - Image DICOMs: Files with valid Rows and Columns attributes,
              indicating they contain actual imaging data.
            - Non-image DICOMs: Files without imaging data (e.g., presentation
              states, reports, or metadata-only objects).
            - Unreadable files: Files that cannot be parsed as valid DICOM.

        Slice position clustering:
            For image DICOMs, the command computes a robust slice coordinate by:

            1. Extracting ImagePositionPatient (IPP) and ImageOrientationPatient
               (IOP) from the DICOM header.
            2. Computing the plane normal as: normal = row_direction × col_direction
            3. Calculating the slice coordinate as: coord = dot(normal, IPP)

            This approach works correctly for both standard acquisitions and
            oblique slices. The computed slice coordinates are then clustered
            using the specified tolerance (tol_mm) to identify unique slice
            positions. The number of clusters determines the expected number of
            slices per volume.

        Timepoint grouping:
            Files are grouped into volumetric timepoints using temporal
            information from DICOM headers. The command uses a prioritized
            hierarchy of temporal tags:

            1. TemporalPositionIdentifier (most reliable for fMRI)
            2. AcquisitionNumber
            3. TriggerTime (common in Philips fMRI data)
            4. AcquisitionTime (converted to milliseconds)
            5. InstanceNumber (least reliable, used as last resort)

            This ensures robust timepoint identification across different
            scanner manufacturers and sequence types.

        Volume completeness detection:
            Each timepoint is examined to determine if it contains all expected
            slices. The expected number of slices is computed as the mode of
            slice counts across all timepoints, which is more robust than using
            the total number of unique slice positions (which may include stray
            slices from partial volumes).

            A timepoint is considered incomplete if:

            - It contains fewer unique slice positions than expected.
            - Its slices cannot be mapped to the identified slice position
              clusters (due to invalid or missing IPP/IOP data).

        File removal:
            Based on the move_non_image and move_incomplete parameters:

            - Non-image DICOM files are moved to: dicom/non-image/
            - Files from incomplete volumes are moved to: dicom/_REMOVED/

            Files are renamed during the move to avoid collisions, with duplicate
            filenames receiving a numeric suffix (e.g., file__dup1.dcm,
            file__dup2.dcm).

        Edge cases and considerations:
            - If slice coordinates cannot be computed (missing IPP/IOP), the
              sequence is skipped with a warning.
            - Multi-echo or multi-phase sequences may require manual inspection
              if they share acquisition numbers but represent complete volumes.
            - Very short sequences (< min_files) are skipped to avoid false
              positives.
            - The command preserves the original DICOM folder structure except
              for moved files.

    Examples:
        Clean DICOM files in a single session (called from import_dicom)::

            clean_dicom(folder="/data/study/sessions/subj001")

        Clean DICOM files with custom parameters::

            clean_dicom(
                folder="/data/study/sessions/subj001",
                tol_mm=0.5,
                min_files=20,
                verbose="yes"
            )

        Clean DICOM files but only move non-image files::

            clean_dicom(
                folder="/data/study/sessions/subj001",
                move_non_image=True,
                move_incomplete=False
            )
    """

    def _is_image_dicom(ds):
        """Check if DICOM dataset contains imaging data."""
        return ds is not None and hasattr(ds, "Rows") and hasattr(ds, "Columns")

    def _safe_float(x, default=None):
        """Safely convert value to float."""
        try:
            return float(x)
        except Exception:
            return default

    def _read_header(path):
        """Read DICOM header without pixel data for efficiency."""
        try:
            # Only read specific tags we need for volume detection
            # This provides ~2-3x speedup vs reading all tags
            specific_tags = [
                (0x0020, 0x0032),  # ImagePositionPatient
                (0x0020, 0x0037),  # ImageOrientationPatient
                (0x0020, 0x1041),  # SliceLocation
                (0x0020, 0x0100),  # TemporalPositionIdentifier
                (0x0020, 0x0012),  # AcquisitionNumber
                (0x0028, 0x0010),  # Rows
                (0x0028, 0x0011),  # Columns
                (0x0020, 0x000E),  # SeriesInstanceUID
                (0x0008, 0x0018),  # SOPInstanceUID
                (0x0020, 0x0013),  # InstanceNumber
                (0x0008, 0x0032),  # AcquisitionTime
                (0x0018, 0x1060),  # TriggerTime
            ]
            ds = pydicom.filereader.dcmread(
                path,
                stop_before_pixels=True,
                specific_tags=specific_tags,
                force=False,  # Don't force reading invalid DICOM files
            )
            return ds
        except Exception:
            return None

    def _slice_coordinate(ds):
        """
        Compute robust slice coordinate using plane normal.
        coord = dot(normal, IPP) where normal = row_cosines × col_cosines
        Works across oblique acquisitions.
        """
        ipp = getattr(ds, "ImagePositionPatient", None)
        iop = getattr(ds, "ImageOrientationPatient", None)
        if ipp is None or iop is None:
            return None

        ipp = np.array([_safe_float(v) for v in ipp], dtype=float)
        if np.any(np.isnan(ipp)):
            return None

        iop = [_safe_float(v) for v in iop]
        if any(v is None for v in iop) or len(iop) != 6:
            return None

        row = np.array(iop[0:3], dtype=float)
        col = np.array(iop[3:6], dtype=float)
        normal = np.cross(row, col)
        nrm = np.linalg.norm(normal)
        if nrm == 0:
            return None
        normal = normal / nrm

        return float(np.dot(normal, ipp))

    def _cluster_values(values, tol):
        """
        Cluster numeric values into bins with tolerance.
        Returns cluster centers sorted, plus mapping function.
        """
        vals = sorted(v for v in values if v is not None)
        if not vals:
            return [], (lambda x: None)

        clusters = []
        current = [vals[0]]
        for v in vals[1:]:
            if abs(v - np.mean(current)) <= tol:
                current.append(v)
            else:
                clusters.append(float(np.mean(current)))
                current = [v]
        clusters.append(float(np.mean(current)))

        def assign(v):
            if v is None:
                return None
            idx = int(np.argmin([abs(v - c) for c in clusters]))
            if abs(v - clusters[idx]) <= tol:
                return clusters[idx]
            return None

        return clusters, assign

    def _choose_time_key(ds):
        """
        Choose temporal key for grouping slices into volumes.
        Priority: TemporalPositionIdentifier > AcquisitionNumber >
                  TriggerTime > AcquisitionTime > InstanceNumber
        """
        if hasattr(ds, "TemporalPositionIdentifier"):
            v = getattr(ds, "TemporalPositionIdentifier", None)
            if v is not None:
                return ("TPI", int(v))

        if hasattr(ds, "AcquisitionNumber"):
            v = getattr(ds, "AcquisitionNumber", None)
            if v is not None:
                return ("ACQ", int(v))

        if hasattr(ds, "TriggerTime"):
            v = _safe_float(getattr(ds, "TriggerTime", None))
            if v is not None:
                return ("TRIG", int(round(v)))

        at = getattr(ds, "AcquisitionTime", None)
        if at:
            try:
                s = str(at)
                hh = int(s[0:2])
                mm = int(s[2:4])
                ss = float(s[4:])
                sec = hh * 3600 + mm * 60 + ss
                return ("AT", int(round(sec * 1000)))
            except Exception:
                pass

        inst = getattr(ds, "InstanceNumber", None)
        if inst is not None:
            return ("INST", int(inst))

        return ("UNK", 0)

    def _process_sequence_folder(seq_folder, seq_name, removed_dir, non_image_dir):
        """Process a single sequence folder for incomplete volumes."""

        # Collect all files in sequence folder (use scandir for speed)
        # Pre-filter by extension to avoid reading non-DICOM files
        all_paths = []
        try:
            with os.scandir(seq_folder) as entries:
                for entry in entries:
                    if entry.is_file():
                        # Only process files that look like DICOMs
                        name_lower = entry.name.lower()
                        if (
                            name_lower.endswith(".dcm")
                            or name_lower.endswith(".dcm.gz")
                            or "."
                            not in entry.name  # DICOM files often have no extension
                            or name_lower.endswith(".ima")
                        ):
                            all_paths.append(entry.path)
        except Exception:
            # Fallback to os.walk if scandir fails
            for root, _, files in os.walk(seq_folder):
                for fn in files:
                    all_paths.append(os.path.join(root, fn))

        if not all_paths:
            return

        # Print early progress indication
        if verbose:
            print(
                f"---> Inspecting sequence {seq_name} (evaluating {len(all_paths)} files):"
            )

        # Batch read files into memory first (one sequential pass - faster on spinning disk)
        # Read first 64KB of each file (DICOM headers typically <16KB, 64KB provides safety margin)
        from io import BytesIO

        file_data = {}
        for p in all_paths:
            try:
                with open(p, "rb") as f:
                    file_data[p] = f.read(65536)  # 64KB
            except Exception:
                pass

        # Read headers and classify files (parsing from memory is faster)
        items = []
        non_images = []
        unreadable = 0

        specific_tags = [
            (0x0020, 0x0032),
            (0x0020, 0x0037),
            (0x0020, 0x1041),
            (0x0020, 0x0100),
            (0x0020, 0x0012),
            (0x0028, 0x0010),
            (0x0028, 0x0011),
            (0x0020, 0x000E),
            (0x0008, 0x0018),
            (0x0020, 0x0013),
            (0x0008, 0x0032),
            (0x0018, 0x1060),
        ]

        for p, data in file_data.items():
            try:
                ds = pydicom.filereader.dcmread(
                    BytesIO(data),
                    stop_before_pixels=True,
                    specific_tags=specific_tags,
                    force=False,
                )
            except Exception:
                unreadable += 1
                continue

            if not _is_image_dicom(ds):
                non_images.append(p)
                continue

            ser = getattr(ds, "SeriesInstanceUID", "NO_SERIES_UID")
            sop = getattr(ds, "SOPInstanceUID", os.path.basename(p))
            sc = _slice_coordinate(ds)
            tk = _choose_time_key(ds)

            items.append(
                {
                    "path": p,
                    "series": ser,
                    "sop": sop,
                    "slice_coord": sc,
                    "time_key": tk,
                }
            )

        # Skip if too few image files
        if len(items) < min_files:
            if verbose:
                print(
                    f"     Sequence {seq_name}: only {len(items)} image files, skipping (< {min_files})"
                )
                print()
            return

        # Group by series (should typically be one series per folder)
        by_series = defaultdict(list)
        for it in items:
            by_series[it["series"]].append(it)

        to_remove = []

        for series_uid, series_items in by_series.items():
            # Cluster slice coords into Z positions
            coords = [it["slice_coord"] for it in series_items]
            centers, assign_z = _cluster_values(coords, tol_mm)

            if not centers:
                if verbose:
                    print(
                        f"     Sequence {seq_name}: cannot cluster slice positions (missing/invalid IPP/IOP), skipping"
                    )
                    print()
                continue

            expected_z = len(centers)

            # Assign each file to a Z cluster
            valid = []
            unmapped = []
            for it in series_items:
                zc = assign_z(it["slice_coord"])
                if zc is None:
                    unmapped.append(it)
                else:
                    it2 = dict(it)
                    it2["z_center"] = zc
                    valid.append(it2)

            # Group by timepoint
            vols = defaultdict(list)
            for it in valid:
                vols[it["time_key"]].append(it)

            # Determine mode of z-count across volumes (more robust)
            z_counts = [
                len(set(it["z_center"] for it in vitems)) for vitems in vols.values()
            ]
            if z_counts:
                mode_z = Counter(z_counts).most_common(1)[0][0]
            else:
                mode_z = expected_z

            # Flag incomplete volumes
            flagged = []
            for tk, vitems in vols.items():
                zset = set(it["z_center"] for it in vitems)
                if len(zset) != mode_z:
                    flagged.extend(vitems)

            # Re-check unmapped files - they might be non-image DICOMs
            # that passed the initial Rows/Columns check
            unmapped_non_image = []
            unmapped_incomplete = []
            for it in unmapped:
                # Re-read the full header to check more thoroughly
                ds = _read_header(it["path"])
                # Check if this is truly an image by looking for additional image attributes
                if ds and (
                    not hasattr(ds, "ImagePositionPatient")
                    or not hasattr(ds, "ImageOrientationPatient")
                    or not hasattr(ds, "SliceLocation")
                ):
                    # Missing critical image geometry - likely non-image
                    unmapped_non_image.append(it["path"])
                else:
                    # Has some geometry but couldn't be clustered - incomplete
                    unmapped_incomplete.append(it["path"])

            # Add unmapped non-images to the non_images list
            non_images.extend(unmapped_non_image)

            # Report if verbose
            if verbose:
                bad_tks = sorted(set(it["time_key"] for it in flagged))
                print(
                    f"     Files (image): {len(series_items)} (valid: {len(valid)}, unmapped: {len(unmapped)})"
                )
                print(
                    f"     Slice clusters: {expected_z} (mode across volumes: {mode_z})"
                )
                print(f"     Timepoints detected: {len(vols)}")
                print(f"     Incomplete timepoints flagged: {len(bad_tks)}")
                if unmapped_non_image:
                    print(
                        f"     Unmapped files reclassified as non-image: {len(unmapped_non_image)}"
                    )

            # Add only truly incomplete unmapped files to removal list
            for p in unmapped_incomplete:
                to_remove.append(p)
            for it in flagged:
                to_remove.append(it["path"])

        # Move non-image files if requested
        if move_non_image and non_images:
            os.makedirs(non_image_dir, exist_ok=True)
            for p in non_images:
                if os.path.exists(p):
                    dst = os.path.join(non_image_dir, os.path.basename(p))
                    # Avoid collisions
                    if os.path.exists(dst):
                        base, ext = os.path.splitext(os.path.basename(p))
                        i = 1
                        while os.path.exists(dst):
                            dst = os.path.join(non_image_dir, f"{base}__dup{i}{ext}")
                            i += 1
                    os.rename(p, dst)
            if verbose:
                print(f"     Moved {len(non_images)} non-image files to non-image/")

        # Move incomplete volume files if requested
        if move_incomplete and to_remove:
            os.makedirs(removed_dir, exist_ok=True)
            moved = 0
            for p in set(to_remove):  # Deduplicate
                if os.path.exists(p):
                    dst = os.path.join(removed_dir, os.path.basename(p))
                    # Avoid collisions
                    if os.path.exists(dst):
                        base, ext = os.path.splitext(os.path.basename(p))
                        i = 1
                        while os.path.exists(dst):
                            dst = os.path.join(removed_dir, f"{base}__dup{i}{ext}")
                            i += 1
                    os.rename(p, dst)
                    moved += 1
            if verbose:
                print(f"     Moved {moved} files from incomplete volumes to _REMOVED/")

        # Add blank line at end of sequence report
        if verbose:
            print()

    # Main execution
    print("Running clean_dicom\n==================")

    verbose = true_or_false(verbose)

    dicom_folder = os.path.join(folder, "dicom")

    if not os.path.exists(dicom_folder):
        print(f"---> DICOM folder not found: {dicom_folder}")
        print("---> Skipping clean_dicom")
        return

    # Create removal directories
    removed_dir = os.path.join(dicom_folder, "_REMOVED")
    non_image_dir = os.path.join(dicom_folder, "non-image")

    # Find sequence folders (integer-named directories)
    sequence_folders = []
    for item in os.listdir(dicom_folder):
        item_path = os.path.join(dicom_folder, item)
        if os.path.isdir(item_path) and item.isdigit():
            sequence_folders.append((item, item_path))

    if not sequence_folders:
        print("---> No sequence folders found in dicom/")
        print("---> Skipping clean_dicom")
        return

    sequence_folders.sort(key=lambda x: int(x[0]))

    if verbose:
        print(f"---> Found {len(sequence_folders)} sequence folder(s) to process")

    # Process each sequence folder
    for seq_name, seq_path in sequence_folders:
        _process_sequence_folder(seq_path, seq_name, removed_dir, non_image_dir)

    print("---> Done")
    return


def list_dicom(folder=None):
    """
    ``list_dicom [folder=inbox]``

    Identify all DICOM files in a folder and print a detailed report.

    ..  qx_command:
        type: utility

    Parameters:
        --folder (str, default 'inbox'):
            The folder to be inspected for the presence of the DICOM files.

    Notes:
        The command inspects the folder (`folder`) for dicom files and prints a
        detailed report of the results. Specifically, for each dicom file it
        finds in the specified folder and its subfolders it will print:

        - location of the file
        - session id recorded in the dicom file
        - sequence number and name
        - date and time of acquisition.

        Importantly, it can work with both regular and gzipped DICOM files.

    Examples:
        ::

            qunex list_dicom \\
                --folder=OP269/dicom
    """

    if folder is None:
        folder = os.path.join(".", "inbox")

    print(
        "============================================\n\nListing dicoms from %s\n"
        % (folder)
    )

    files = glob.glob(os.path.join(folder, "*"))
    files = files + glob.glob(os.path.join(folder, "*/*"))
    files = [e for e in files if os.path.isfile(e)]

    if not files:
        raise ge.CommandFailed(
            "list_dicom",
            "No files found",
            "Please check the specified folder! [%s]" % (os.path.abspath(folder)),
            "Aborting",
        )

    for dcm in files:
        try:
            d = read_dicom_base(dcm)
            time = get_dicom_time(d)
            try:
                print(
                    "---> %s - %-6s %6d - %-30s scanned on %s"
                    % (dcm, get_id(d), d.SeriesNumber, d.SeriesDescription, time)
                )
            except:
                print(
                    "---> %s - %-6s %6d - %-30s scanned on %s"
                    % (dcm, get_id(d), d.SeriesNumber, d.ProtocolName, time)
                )
        except:
            pass

    return


def split_dicom(folder=None):
    """
    ``split_dicom [folder=inbox]``

    Sort out DICOM images from different sessions.

    ..  qx_command:
        type: utility

    Parameters:
        --folder (str, default 'inbox'):
            The folder that contains the DICOM files to be sorted out.

    Notes:
        The command is used when DICOM images from different sessions are mixed
        in the same folder and need to be sorted out. Specifically, the command
        inspects the specified folder (`folder`) and its subfolders for the
        presence of DICOM files. For each DICOM file it finds, it checks, what
        session id the file belongs to. In the specified folder it then creates
        a subfolder for each of the found sessions and moves all the DICOM
        files in the right sessions' subfolder.

    Examples:
        ::

            qunex split_dicom \\
                --folder=dicommess
    """

    if folder is None:
        folder = os.path.join(".", "inbox")

    print(
        "============================================\n\nSorting dicoms from %s\n"
        % (folder)
    )

    files = glob.glob(os.path.join(folder, "*"))
    files = files + glob.glob(os.path.join(folder, "*/*"))
    files = [e for e in files if os.path.isfile(e)]

    if not files:
        raise ge.CommandFailed(
            "split_dicom",
            "No files found",
            "Please check the specified folder! [%s]" % (os.path.abspath(folder)),
            "Aborting",
        )

    sessions = []

    for dcm in files:
        try:
            # d    = dicom.read_file(dcm, stop_before_pixels=True)
            d = read_dicom_base(dcm)
            time = get_dicom_time(d)
            sid = get_id(d)
            if sid not in sessions:
                sessions.append(sid)
                os.makedirs(os.path.join(folder, sid))
                print("---> creating subfolder for session %s" % (sid))
            print(
                "---> %s - %-6s %6d - %-30s scanned on %s"
                % (dcm, sid, d.SeriesNumber, d.SeriesDescription, time)
            )
            os.rename(dcm, os.path.join(folder, sid, os.path.basename(dcm)))
        except:
            pass

    return


def import_dicom(
    sessionsfolder=None,
    sessions=None,
    masterinbox=None,
    check="any",
    pattern=None,
    nameformat=None,
    tool="auto",
    parelements=1,
    logfile=None,
    archive="leave",
    add_image_type=0,
    add_json_info="all",
    unzip="yes",
    gzip="folder",
    verbose="yes",
    overwrite="no",
    existing_structure=False,
    clean_dicom_folders=False,
    test=False,
):
    r"""
    ``import_dicom [sessionsfolder=.] [sessions=""] [masterinbox=<sessionsfolder>/inbox/MR] [check=any] [pattern="(?P<packet_name>.*?)(?:\.zip$|\.tar$|.tgz$|\.tar\..*$|$)"] [nameformat='(?P<subject_id>.*)'] [tool=auto] [parelements=1] [logfile=""] [archive=leave] [add_image_type=0] [add_json_info=""] [unzip="yes"] [gzip="folder"] [verbose=yes] [overwrite="no"] [existing_structure=False] [clean_dicom_folders=False]``

    Process sessions's DICOM or PAR/REC files and generate NIfTI files.

    ..  qx_command:
        type: utility

    Parameters:
        --sessionsfolder (str, default '.'):
            The base study sessions folder (e.g. WM44/sessions) where the inbox
            and individual session folders are. If not specified, the current
            working folder will be taken as the location of the sessionsfolder.

        --sessions (str, default ''):
            A comma delimited string that lists the sessions to process. If
            master inbox folder is used, the parameter is optional and it can
            include regex patterns. In this case only those sessions identified
            by the pattern that also match with any of the patterns in the
            sessions list will be processed. If `masterinbox` is set to none,
            the list specifies the session folders to process, and it can
            include glob patterns.

        --masterinbox (str, default '<sessionsfolder>/inbox/MR'):
            The master inbox folder with packages to process. By default
            masterinbox is in sessions folder: <sessionsfolder>/inbox/MR. If
            the packages are elsewhere, the location can be specified here. If
            set to "none", the data is assumed to already exist in the
            individual sessions' inbox folder:
            <studyfolder>/<sessionsfolder>/<session id>/inbox.

        --check (str, default 'any'):
            The type of check to perform when packages or session folders are
            identified.

            The possible values are:
            - 'no'  ... report and continue w/o additional checks
            - 'any' ... continue if any packages are ready to process report error otherwise.

        --pattern (str, default '(?P<session_id>.*?)(?:\\.zip$|\\.tar$|\\.tgz$|\\.tar\\..*$|$)'):
            The regex pattern to use to find the packages and to extract the
            session id.

        --nameformat (str, default '(?P<subject_id>.*)'):
            The regex pattern to use to extract subject id and (optionally) the
            session name from the session or packet name.

        --tool (str, default 'auto'):
            What tool to use for the conversion.

            It can be one of:
            - 'auto' (determine best tool based on heuristics)
            - 'dcm2niix'
            - 'dcm2nii'
            - 'dicm2nii'.

        --parelements (int, default 1):
            The number of parallel processes to use when running converting
            DICOM images to NIfTI files. If specified as 'all', all avaliable
            resources will be utilized.

        --logfile (str, default ''):
            A string specifying the location of the log file and the columns in
            which packetname, subject id and session name information are
            stored. The string should specify: ``"path:<path to the log file>|
            packetname:<name of the packet extracted by the
            pattern>|subjectid:<the column with subjectid
            information>[|sessionid:<the column with sesion id
            information>]"``.

        --archive (str, default 'leave'):
            What to do with a processed package.

            Options are:

            - 'move'   ... move the package to the default archive folder
            - 'copy'   ... copy the package to the default archive folder
            - 'leave'  ... keep the package in the session or master inbox
              folder
            - 'delete' ... delete the package after it has been processed.

            In case of processing data from a sessions folder, the
            `archive` parameter is only valid for compressed
            packages.

        --add_image_type (int, default 0):
            Adds image type information to the sequence name (Siemens scanners).
            The value should specify how many of image type labels from the end
            of the image type list to add.

        --add_json_info (str, default 'all'):
            What sequence information to extract from JSON sidecar files and add
            to session.txt file. Specify a comma separated list of fields or
            'all'. See list in session.txt file description below.

        --unzip (str, default 'yes'):
            Whether to unzip individual DICOM files that are gzipped. Valid
            options are 'yes', 'no'.

        --gzip (str, default 'folder'):
            Whether to gzip individual DICOM files after they were processed
            ('file'), gzip a DICOM sequence or acquisition as an tar.gz archive
            ('folder'), or leave them ungzipped ('no'). Valid options are
            'folder', 'file', 'no'.

        --verbose (str, default 'yes'):
            Whether to provide detailed report also of packets that could not be
            identified and/or are not matched with log file.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --existing_structure (bool, default False):
            If the images are preorganized in folders, set this to True so QuNex
            will not try to reorganize them.

        --clean_dicom (bool, default False):
            If set to True, after sorting dicom files into sequence folders, the
            dicom files will be inspected and any dicom files that do not
            contain image data, or that do not constitute a full volume (e.g.,
            in the case of interrupted scans) will be set aside before
            conversion to NIfTI.

    Notes:
        The command is used to automatically process packets with individual
        session's DICOM or PAR/REC files all the way to, and including,
        generation of NIfTI files. Packet can be either a zip file, a tar
        archive or a folder that contains DICOM or PAR/REC files.

        The command can import packets either from a dedicated masterinbox
        folder and create the necessary session folders within
        `--sessionsfolder`, or it can process the data already present in
        the session specific folders.

        The next sections will describe the two use cases in more detail.

        Processing data from a dedicated inbox folder:
            This is the default operation. In this mode of operation:

            - The candidate packages are identified by a `pattern` parameter,
              which also specifies, how to extract a packet name.
            - The packets found are optionally filtered using the `sessions`
              parameter.
            - Subject id and (optionally) session name are either extracted
              from the packet name using the `nameformat` parameter or looked
              up in a log file.
            - A report of packets identified is generated.
            - Session folders are created and packet data is moved or copied to
              the session's `inbox` folder.
            - Dicom data is sorted into folders holding information from a
              single scan
            - Images are converted to nifti format
            - `session.txt` files are generated
            - Original packets are archived as specified by the `archive`
              parameter.

            In this mode of operation the `masterinbox` parameter passed to
            `import_dicom` has to provide a path to the folder with the
            incoming packets. The default location is
            `<study>/<sessionsfolder>/inbox/MR`, which is used automatically if
            `masterinbox` is not specified. Data from each session has to be
            present in the `masterinbox` directory either as a separate folder
            with the raw DICOM files or as a compressed package with that
            session's data. `import_dicom` supports the following packages:
            `.zip`, `.tar`, `.tar.gz`, `.tar.bz2`, `.tarz` and `.tar.bzip2`.

            The `pattern` parameter is used to specify, which files and/or
            folders are to be identified as potential packets to be processed.
            Specifically, the `pattern` parameter is a string that specifies a
            `regular expression <http://www.rexegg.com/regex-quickstart.html>`_
            against which the files and folders in the `masterinbox` are
            matched. In addition, the regular expression has to return a named
            group, 'packet_name' that is used in further processing.

            The default `pattern` parameter is
            `"(?P<packet_name>.*?)(?:\\.zip$|\\.tar$|\\.tar\\..*$|$)"`. This
            pattern will identify the initial part of the packet file- or
            foldername, (without any extension that identifies a compressed
            package) as the packet name.

            Specifically:

            - OP386
            - OP386.zip
            - OP386.tar.gz

            will all be identified as packet names 'OP386'.

            Next the packet name has to be processed to identify the subject id
            and (optionally) the session name. This can be done in one of two
            ways. If the necessary information is present in the packet name
            itself, it can be extracted as specified in by the `nameformat`
            parameter. If not, it can be specified using a `logfile` parameter.

            Extracting subject id from packet name:
                To extract subject id from a packet name, the `nameformat`
                parameter has to specify a `regular
                expression <http://www.rexegg.com/regex-quickstart.html>`_ that
                will extract the subject id and (optionally) the session name
                from the packet name as named groups, `subject_id` and
                `session_name`, respectively. The default `nameformat`
                parameter is `"(?P<subject_id>.*)"`. It assumes that the packet
                name is equal to the subject id and only a single session was
                recorded. Here are a few additional examples of how subject id
                and session names can be extracted using the `nameformat`
                parameter:

                +-----------------------+--------------------------------------------------+------------+--------------+---------------+
                | packet name           | `nameformat` parameter                           | subject id | session name | session id    |
                +=======================+==================================================+============+==============+===============+
                | AP346_MR_1            | `"(?P<subject_id>.*?)_(?P<session_name>.*)"`     | AP346      | MR_1         | AP346_MR_1    |
                +-----------------------+--------------------------------------------------+------------+--------------+---------------+
                | Siemens_Baseline-S002 | `".*?_(?P<session_name>.*?)-(?P<subject_id>.*)"` | S002       | Baseline     | S002_Baseline |
                +-----------------------+--------------------------------------------------+------------+--------------+---------------+
                | Yale-EQ469-Placebo    | `".*?-(?P<subject_id>.*?)-(?P<session_name>.*)"` | EQ469      | Placebo      | EQ469_Placebo |
                +-----------------------+--------------------------------------------------+------------+--------------+---------------+
                | Oxford.MR492.T3-Trio  | `".*?\\.(?P<subject_id>.*?)\\..*"`               | MR492      | -            | MR492         |
                +-----------------------+--------------------------------------------------+------------+--------------+---------------+


                Shown are the extracted packet name, the `nameformat` regular
                expression, the resulting extracted subject id and session name
                (when present), and the final generated session id.

            Looking up subject id in a log file:
                If subject id and (optionally) session name is not present or
                cannot be robustly extracted from the package name, it is
                possible to make use of a file that provides the mapping
                between package names, subject ids and session names. A log
                file has to be either a comma separated value (`.csv`) file or
                a tab separated text file in which each row provides
                information about a single scanning session. An example log
                file (e.g. `scanning_sessions.csv`) can be::

                    scanning code,subject,session,date of scan, ...
                    AP1789,S001,baseline,2019-03-21, ...
                    AP1790,S001,incentive,2019-03-21, ...
                    WID1832,S002,baselime,2019-04-12, ...
                    WID1913,S002,incentive,2019-04-12, ...

                To use a log file, a `logfile` parameter has to be provided.
                The content of the `logfile` has to be a string of the
                following format::

                    path:<path to the log file>|packet_name:<the column number with the packet name>|subject_id:<a column number with the subject id>|session_name:<a column number with the session name>

                In case of the above information, the `logfile` parameter would be::

                    --logfile="path:/studies/myStudy/info/scanning_sessions.csv|packet_name:1|subject_id:2|session_name:3"

                And the resulting mapping would be:

                +-------------+------------+--------------+----------------+
                | packet name | subject id | session name | session id     |
                +=============+============+==============+================+
                | AP1789      | S001       | baseline     | S001_baseline  |
                +-------------+------------+--------------+----------------+
                | AP1790      | S001       | incentive    | S001_incentive |
                +-------------+------------+--------------+----------------+
                | WID1832     | S002       | baseline     | S002_baseline  |
                +-------------+------------+--------------+----------------+
                | WID1913     | S002       | incentive    | S002_incentive |
                +-------------+------------+--------------+----------------+

                Shown are the extracted packet name, the extracted subject id
                and session name, and the final generated session id.

                Do note that at least `packet_name` and `subject_id` have to be
                provided in the `logfile` parameter and in the log file itself.
                If `session_name` is not provided, it is assumed that only a
                single session was recorded for each subject and session id
                equals subject id.

            Further processing:
                As can be seen from the examples, after the subject id and
                (optionally) the session name are extracted, the session id is
                generated using the formula `<subject_id>[_<session_name>]`,
                where `_<session_name>` is appended only if extracted from
                either the packet name or the log file. The generated session
                id would then be used to name the sessions' folders in the
                `/studies/myStudy/sessions`.

                The progress of processing now depends on the `check` parameter.
                If the `check` parameter is set to `any` it will proceed if any
                packets to process were found, and it will report an error
                otherwise. If `check` is set to `no`, no additional check will
                be performed. If any packets were found to be processed, they
                will be processed. If none were found, the command will exit
                without reporting an error.

                If packets were found to process and a go ahead was given,
                import_dicom will then copy, unzip or untar all the files in
                each packet into an inbox folder created within the session
                folder. Once all the files are extracted or copied, depending
                on the `archive` parameter, the packet is then either moved
                ('move') or copied ('copy') to the
                `<study>/sessions/archive/MR` folder, left as is ('leave'), or
                deleted ('delete'). If the archive folder does not yet exist,
                it is created. The default `archive` setting is 'move'.

                If a session folder and an inbox folder within it already
                exists, then the related packet will not be processed so that
                the existing data is not changed. In this case the user has to
                either remove or rename the existing folder(s) and rerun the
                command to process those packet(s) as well.

            Filtering sessions:
                If not all packets in the `masterinbox` folder are to be
                processed, it is possible to explicitly define which packets
                can be processed by specifying the `sessions` parameter. The
                parameter is a comma separated string of packet names that can
                be processed. Each entry in the list can be a regular extension
                pattern, in which case all the packet names that match any of
                the patterns will be processed. Following the last example
                above, specifying::

                    --sessions=".*_baseline"

                Would only process the baseline sessions and prepare data in
                these session-specific folders:

                - /studies/myStudy/sessions/S001_baseline
                - /studies/myStudy/sessions/S002_baseline

        Processing data from a session folder:
            If the raw DICOM files or compressed packages with the raw DICOM
            files are already present in the respective
            `<study>/sessions/<session id>/inbox` folders, then the
            `masterinbox` parameter has to be explicitly set to 'none', and the
            session folders to be processed have to be listed in the `sessions`
            parameter. In this case the `session` parameter is a comma
            separated string, where each entry in the list can be a glob
            pattern matching with multiple session folders.

            Please note that the `sessions` parameter is only used to identify
            possible folders. If a session folder is not present, even though
            explicitly listed, `import_dicom` won't report an error.

            In this mode of operation the session id is taken to be the folder
            name. However, if subject id is not equal to the session id, the
            `nameformat` parameter has to be specified to correctly extract the
            subject id from the session name. Specifically, `nameformat`
            parameter has to specify a `regular
            expression <http://www.rexegg.com/regex-quickstart.html>`_ string
            that returns a 'subject_id' named group. By default, the
            `nameformat` parameter is `"(?P<subject_id>.*)"`, which identifies
            the whole session name as the subject id. Here are a few examples
            of how to change the `nameformat` parameter to extract the subject
            id correctly:

            +------------------+----------------------------+-------------+
            | session id       | `nameformat` string        | subject id  |
            +==================+============================+=============+
            | P1102_000_01     | `"(?P<subject_id>.*?)_.*"` | P1102       |
            +------------------+----------------------------+-------------+
            | S5238_Placebo    | `"(?P<subject_id>.*?)_.*"` | S5238       |
            +------------------+----------------------------+-------------+
            | NDAR_INV2CTC8934 | `".*?_(?P<subject_id>.*)"` | INV2CTC8934 |
            +------------------+----------------------------+-------------+

            After the sessions are identified and subject id extracted,
            depending on the `check` parameter, the user is prompted to confirm
            processing (`check="yes"`), the processing continues, but an error
            is reported if no sessions are identified (`check="any"`), or the
            processing continues and no error is reported even if no sessions
            to be processed are found (`check="no"`).

            The folders found are expected to have the data stored in the inbox
            folder either as individual raw DICOM files—that can be nested in
            additional subfolders—or as a compressed package(s). If the latter
            is the case, the files will be extracted to the inbox folder, and
            the package(s) will submit to the setting in the `archive`
            parameter.

            If any results—e.g. files in `dicom` or `nii` folders—already
            exists, the processing of the folder will be skipped.

            For similar use cases refer to the Examples section.

        Processing steps:
            `import_dicom` will first extract and organize the data as described above. As a next step, it will call `sort_dicom` command to organize the raw DICOM files into separate folders for each images. Next it will call `dicom2niix` command that will convert the DICOM files to NIfTI format, store them in `nii` folder and create a `session.txt` file with details of the session.

    Examples:
        Data from a dedicated inbox folder:
            First the examples for processing packages from `masterinbox` folder.

            In the first example, we are assuming that the packages we want to
            process are in the default folder
            (`<path_to_studyfolder>/sessions/inbox/MR`), the file or folder names
            contain only the packet names to be used, and the subject id is equal
            to the packet name. All packets found are to be processed, after the
            user gives a go-ahead to an interactive prompt:

            ::

                qunex import_dicom \\
                    --sessionsfolder="<path_to_studyfolder>/sessions"

            If the processing should continue automatically if packages to process
            were found, then the command should be:

            ::

                qunex import_dicom \\
                    --sessionsfolder="<path_to_studyfolder>/sessions" \\
                    --check="any"

            If only package names starting with 'AP' or 'HQ' are to be processed
            then the `sessions` parameter has to be added:

            ::

                qunex import_dicom \\
                    --sessionsfolder="<path_to_studyfolder>/sessions" \\
                    --sessions="AP.*,HQ.*" \\
                    --check="any"

            If the packages are named e.g. 'Yale-AP4983.zip' with the extension
            optional, then to extract the packet name and map it directly to
            subject id, the following `pattern` parameter needs to be added:

            ::

                qunex import_dicom \\
                    --sessionsfolder="<path_to_studyfolder>/sessions" \\
                    --pattern=".*?-(?P<packet_name>.*?)($|\\..*$)" \\
                    --sessions="AP.*,HQ.*" \\
                    --check="any"

            If the session name can also be extracted and the files are in the
            format e.g. 'Yale-AP4876_Baseline.zip', then a `nameformat` parameter
            needs to be added:

            ::

                qunex import_dicom \\
                    --sessionsfolder="<path_to_studyfolder>/sessions" \\
                    --pattern=".*?-(?P<packet_name>.*?)($|\\..*$)" \\
                    --sessions="AP.*,HQ.*" \\
                    --nameformat="(?P<subject_id>.*?)_(?P<session_name>.*)" \\
                    --check="any"

            In this case, 'AP4876_Baseline' will be first extracted as a packet name
            and then parsed into 'AP4876' subject id and 'Baseline' session name.

            If the files are named e.g. 'Yale-AP4983.zip' and a log file exists in
            which the AP* or HQ* are mapped to a corresponding subject id and
            session names, then the command is changed to:

            ::

                qunex import_dicom \\
                    --sessionsfolder="<path_to_studyfolder>/sessions" \\
                    --pattern=".*?-(?P<packet_name>.*?)($|\\..*$)" \\
                    --sessions="AP.*,HQ.*" \\
                    --logfile="path:/studies/myStudy/info/scanning_sessions.csv|packet_name:1|subject_id:2|session_name:3" \\
                    --check="any"

        Data already present:
            For the examples of processing data already present in the individual
            session id folder, let's assume that we have the following files
            present, with no other files in the sessions folders:

            - /studies/myStudy/sessions/S001_baseline/inbox/AYXQ.tar.gz
            - /studies/myStudy/sessions/S001_incentive/inbox/TWGS.tar.gz
            - /studies/myStudy/sessions/S002_baseline/inbox/OHTZ.zip
            - /studies/myStudy/sessions/S002_incentive/inbox/QRTD.zip

            Then these are a set of possible commands:

            ::

                qunex import_dicom \\
                    --sessionsfolder="/studies/myStudy/sessions" \\
                    --masterinbox="none" \\
                    --sessions="S*"

            In the above case all the folders will be processed, the packages will
            be extracted and (by default) moved to
            `/studies/myStudy/sessions/archive/MR`::

                qunex import_dicom \\
                    --sessionsfolder="/studies/myStudy/sessions" \\
                    --masterinbox="none" \\
                    --sessions="*baseline" \\
                    --archive="delete"

            In the above case only the `S001_baseline` and `S002_baseline` sessions
            will be processed and the respective compressed packages will be
            deleted after the successful processing.
    """

    clean_dicom_folders = true_or_false(clean_dicom_folders)
    existing_structure = true_or_false(existing_structure)

    isgz = re.compile(r"(^.*)\.gz$")
    iszip = re.compile(r"(^.*)\.zip$")
    istar = re.compile(
        r"(^.*)(\.tar$|\.tar.gz$|\.tar.bz2$|\.tarz$|\.tar.bzip2$|\.tgz$)"
    )

    def _process_file(fobj, fname, fnum, dnum, target):
        if not isinstance(fobj, io.IOBase):
            if os.path.isfile(fobj):
                fobj = open(fobj, "rb")
            else:
                return (fnum, dnum)

        if isgz.match(fname):
            fobj = gz.GzipFile(fileobj=fobj)
            fname = isgz.match(fname).group(1)
        elif istar.match(fname):
            return _extract_tar(fobj, fname, fnum, dnum, target)
        elif iszip.match(fname):
            return _extract_zip(fobj, fname, fnum, dnum, target)

        if fnum % 1000 == 0:
            dnum += 1
            if not os.path.exists(os.path.join(target, str(dnum))):
                os.makedirs(os.path.join(target, str(dnum)))
        fnum += 1

        tfile = f"{dnum}-{os.path.basename(fname)}"

        # --- check if par/rec/log
        if tfile.split(".")[-1].lower() in ["par", "rec", "log"]:
            for ext in ["rec", "par"]:
                if tfile.split(".")[-1] == ext:
                    tfile = tfile[:-3] + ext.upper()

        with open(os.path.join(target, str(dnum), tfile), "wb") as fout:
            shutil.copyfileobj(fobj, fout)

        fobj.close()
        return (fnum, dnum)

    def _extract_zip(packet, packetname, fnum=0, dnum=0, target=None):
        # -- open packet
        try:
            z = zipfile.ZipFile(packet, "r")
        except:
            e = sys.exc_info()[0]
            raise ge.CommandFailed(
                "import_dicom",
                "Zip file could not be processed",
                "Opening zip [%s] returned an error [%s]!" % (packetname, e),
                "Please check your data!",
            )

        # -- get list of files in packet
        file_list = z.infolist()

        # -- process list
        for source_file in file_list:
            if source_file.file_size > 0:
                print("...  extracting:", source_file.filename, source_file.file_size)
                fnum, dnum = _process_file(
                    z.open(source_file), source_file.filename, fnum, dnum, target
                )

        # -- close and return with latest numbers
        print("     -> done!")
        z.close()
        return (fnum, dnum)

    def _extract_tar(packet, packetname, fnum=0, dnum=0, target=None):
        # -- open packet
        try:
            if isinstance(packet, io.IOBase):
                tar = tarfile.open(fileobj=packet, mode="r")
            else:
                tar = tarfile.open(packet, "r")
        except:
            e = sys.exc_info()[0]
            raise ge.CommandFailed(
                "import_dicom",
                "Tar file could not be processed",
                "Opening tar [%s] returned an error [%s]!" % (packetname, e),
                "Please check your data!",
            )

        # -- process files
        for tarinfo in tar:
            if tarinfo.isfile():
                print("...  extracting:", tarinfo.name, tarinfo.size)
                fnum, dnum = _process_file(
                    tar.extractfile(tarinfo), tarinfo.name, fnum, dnum, target
                )

        # -- close and return with latest numbers
        print("     -> done!")
        tar.close()
        return (fnum, dnum)

    def _process_folder(folder, fnum=0, dnum=0, target=None):
        # -- get list of files
        files_iter = glob.iglob(os.path.join(folder, "**", "*"), recursive=True)
        for source_file in files_iter:
            fnum, dnum = _process_file(
                source_file, os.path.basename(source_file), fnum, dnum, target
            )

        return (fnum, dnum)

    print("Running import_dicom\n====================")

    # check settings
    if tool not in ["auto", "dcm2niix", "dcm2nii", "dicm2nii"]:
        raise ge.CommandError(
            "import_dicom",
            "Incorrect tool specified",
            "The tool specified for conversion to nifti (%s) is not valid!" % (tool),
            "Please use one of dcm2niix, dcm2nii, dicm2nii or auto!",
        )

    verbose = verbose.lower() == "yes"

    overwrite = overwrite if isinstance(overwrite, bool) else overwrite.lower() == "yes"

    if sessionsfolder is None:
        sessionsfolder = "."

    if masterinbox is None:
        masterinbox = os.path.join(sessionsfolder, "inbox", "MR")

    if masterinbox.lower() == "none":
        masterinbox = None
        if sessions is None or sessions == "":
            raise ge.CommandError(
                "import_dicom",
                "Sessions parameter not specified",
                "If `masterinbox` is set to 'none' the `sessions` has to list sessions to process!",
                "Please check your command!",
            )

    if pattern is None:
        pattern = r"(?P<packet_name>.*?)(?:\.zip$|\.tar$|\.tgz$|\.tar\..*$|$)"

    if nameformat is None:
        nameformat = r"(?P<subject_id>.*)"

    try:
        if add_image_type == None or add_image_type == "":
            add_image_type = 0
        else:
            add_image_type = int(add_image_type)
    except:
        raise ge.CommandError(
            "import_dicom",
            "Misspecified add_image_type",
            "The add_image_type argument value could not be converted to integer! [%s]"
            % (add_image_type),
            "Please check command instructions!",
        )

    if sessions:
        sessions = re.split(r", *", sessions)

    # ---- check acquisition log if present:
    sessions_info = None

    if logfile is not None and logfile != "":
        log = dict([[f.strip() for f in e.split(":")] for e in logfile.split("|")])

        if not all([e in log for e in ["path", "subject_id", "packet_name"]]):
            raise ge.CommandFailed(
                "import_dicom",
                "Missing information in logfile",
                "Please provide all information in the logfile specification! [%s]"
                % (logfile),
            )

        try:
            for key in [
                e
                for e in log.keys()
                if e in ["packet_name", "subject_id", "session_name"]
            ]:
                log[key] = int(log[key]) - 1
        except:
            raise ge.CommandFailed(
                "import_dicom",
                "Invalid logfile specification",
                "Please create a valid logfile specification! [%s]" % (logfile),
            )

        sessionname = "session_name" in log

        if not os.path.exists(log["path"]):
            raise ge.CommandFailed(
                "import_dicom",
                "Logfile does not exist",
                "The specified logfile does not exist:",
                log["path"],
                "Please check your paths!",
            )

        print("---> Reading acquisition log [%s]." % (log["path"]))
        sessions_info = {}
        with open(log["path"]) as f:
            if log["path"].split(".")[-1] == "csv":
                reader = csv.reader(f, delimiter=",")
            else:
                reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
            for line in reader:
                try:
                    if sessionname:
                        sessions_info[line[log["packetname"]]] = {
                            "subjectid": line[log["subject_id"]],
                            "sessionname": line[log["session_name"]],
                            "sessionid": "%s_%s"
                            % (line[log["subject_id"]], line[log["session_name"]]),
                            "packetname": line[log["packet_name"]],
                        }
                    else:
                        sessions_info[line[log["packetname"]]] = {
                            "subjectid": line[log["subject_id"]],
                            "sessionname": None,
                            "sessionid": line[log["subject_id"]],
                            "packetname": line[log["packet_name"]],
                        }
                except:
                    pass

    # ---- set up lists
    packets = {"ok": [], "nolog": [], "bad": [], "exist": [], "skip": [], "invalid": []}
    emptysession = {
        "subjectid": None,
        "sessionname": None,
        "sessionid": None,
        "packetname": None,
    }

    # ---- get list of files / folders in masterinbox
    if masterinbox:
        report_set = [
            ("ok", "---> Found the following packets to process:"),
            (
                "nolog",
                "---> These packets do not match with the log and they won't be processed",
            ),
            (
                "bad",
                "---> For these packets a packet name could not be identified and they won't be processed:",
            ),
            (
                "invalid",
                "---> For these packets the packet name could not parsed and they won't be processed:",
            ),
            (
                "exist",
                "---> The session and inbox folder for these packages already exist:",
            ),
            (
                "skip",
                "---> These packages do not match list of sessions and will be skipped:",
            ),
        ]

        if not os.path.exists(masterinbox):
            raise ge.CommandFailed(
                "import_dicom",
                "Master inbox does not exist",
                f"A folder {masterinbox} does not exist.",
                "Please check your path!",
            )

        if not os.path.isdir(masterinbox):
            raise ge.CommandFailed(
                "import_dicom",
                "Master inbox is not a folder",
                f"{masterinbox} is not a folder.",
                "Please check your path!",
            )

        print(
            "---> Checking for packets in %s \n     ... using regular expression '%s'\n     ... extracting subject id using regular expression '%s'"
            % (os.path.abspath(masterinbox), pattern, nameformat)
        )

        files = glob.glob(os.path.join(masterinbox, "*"))
        try:
            getop = re.compile(pattern)
        except:
            raise ge.CommandFailed(
                "import_dicom",
                "Invalid pattern",
                "Coud not parse the provided regular expression pattern: '%s'"
                % (pattern),
                "Please check and correct it!",
            )
        try:
            getid = re.compile(nameformat)
        except:
            raise ge.CommandFailed(
                "import_dicom",
                "Invalid nameformat",
                "Coud not parse the provided regular expression pattern: '%s'"
                % (nameformat),
                "Please check and correct it!",
            )

        for afile in files:
            m = getop.search(os.path.basename(afile))
            if m:
                if "packet_name" in m.groupdict() and m.group("packet_name"):
                    pname = m.group("packet_name")
                    session = dict(emptysession)
                    session["packetname"] = pname

                    if sessions_info:
                        if pname in sessions_info:
                            session = dict(sessions_info[pname])
                        else:
                            packets["nolog"].append((afile, dict(session)))
                            continue
                    else:
                        session = dict(emptysession)
                        session["packetname"] = pname

                        ms = getid.search(pname)

                        if (
                            ms
                            and "subject_id" in ms.groupdict()
                            and ms.group("subject_id")
                        ):
                            sid = ms.group("subject_id")
                            if "session_name" in ms.groupdict() and ms.group(
                                "session_name"
                            ):
                                session.update(
                                    {
                                        "subjectid": ms.group("subject_id"),
                                        "sessionname": ms.group("session_name"),
                                        "sessionid": "%s_%s"
                                        % (
                                            ms.group("subject_id"),
                                            ms.group("session_name"),
                                        ),
                                    }
                                )
                            else:
                                session.update(
                                    {
                                        "subjectid": ms.group("subject_id"),
                                        "sessionname": None,
                                        "sessionid": ms.group("subject_id"),
                                    }
                                )

                        else:
                            packets["invalid"].append((afile, session))
                            continue

                    sfolder = os.path.join(sessionsfolder, session["sessionid"])

                    if sessions:
                        if not any(
                            [match_all(e, session["sessionid"]) for e in sessions]
                        ):
                            packets["skip"].append((afile, session))
                            continue

                    if os.path.exists(os.path.join(sfolder, "inbox")):
                        packets["exist"].append((afile, session))
                        continue

                    packets["ok"].append((afile, session))

                else:
                    packets["bad"].append(afile, dict(emptysession))

    # ---- get list of session folders to process
    else:
        if not sessions:
            raise ge.CommandFailed(
                "import_dicom",
                "Input data not specified",
                "Neither masterinbox nor sessions to process were specified.",
                "Please check your command call!",
            )

        report_set = [
            ("ok", "---> Found the following folders to process:"),
            (
                "invalid",
                "---> For these folders the folder name could not parsed and they won't be processed:",
            ),
            ("exist", "---> These folders have existing results:"),
        ]

        print(
            "---> Checking for folders to process in '%s'"
            % (os.path.abspath(sessionsfolder))
        )

        getid = re.compile(nameformat)

        sfolders = []
        for sessionid in sessions:
            sfolders += glob.glob(os.path.join(sessionsfolder, sessionid))
        sfolders = list(set(sfolders))

        for sfolder in sfolders:
            session = dict(emptysession)
            pname = os.path.basename(sfolder)
            session["packetname"] = pname
            sid = pname.split("_")

            archives = []
            for tarchive in ["*.zip", "*.tar", "*.tar.*", "*.tgz"]:
                archives += glob.glob(os.path.join(sfolder, "inbox", tarchive))
            session["archives"] = list(archives)

            ms = getid.search(pname)
            if ms and "subject_id" in ms.groupdict() and ms.group("subject_id"):
                sid = ms.group("subject_id")
                if "session_name" in ms.groupdict() and ms.group("session_name"):
                    session.update(
                        {
                            "subjectid": ms.group("subject_id"),
                            "sessionname": ms.group("session_name"),
                            "sessionid": pname,
                        }
                    )
                else:
                    session.update(
                        {
                            "subjectid": ms.group("subject_id"),
                            "sessionname": None,
                            "sessionid": pname,
                        }
                    )

            else:
                packets["invalid"].append((sfolder, session))
                continue

            if glob.glob(os.path.join(sfolder, "dicom")) or glob.glob(
                os.path.join(sfolder, "nii")
            ):
                packets["exist"].append((sfolder, session))
                continue

            packets["ok"].append((sfolder, session))

    # ---> Report
    for tag, message in report_set:
        if packets[tag]:
            print(f"\n{message}")
            for afile, session in packets[tag]:
                if session["sessionname"]:
                    print(
                        "     subject: %s, session: %s ... %s <= %s <- %s"
                        % (
                            session["subjectid"],
                            session["sessionname"],
                            session["sessionid"],
                            session["packetname"],
                            os.path.basename(afile),
                        )
                    )
                elif session["subjectid"]:
                    print(
                        "     subject: %s ... %s <= %s <- %s"
                        % (
                            session["subjectid"],
                            session["sessionid"],
                            session["packetname"],
                            os.path.basename(afile),
                        )
                    )
                elif session["sessionid"]:
                    print(
                        "     %s <= %s <- %s"
                        % (
                            session["sessionid"],
                            session["packetname"],
                            os.path.basename(afile),
                        )
                    )
                elif session["packetname"]:
                    print(
                        "     %s <= %s <- %s"
                        % ("????", session["packetname"], os.path.basename(afile))
                    )
                else:
                    print(
                        "     %s <= %s <- %s"
                        % ("????", "????", os.path.basename(afile))
                    )

            if tag == "exist":
                if overwrite:
                    print(
                        " ... Since overwrite is set the folders will be removed and replaced"
                    )
                else:
                    print(
                        " ... To process them, remove or rename the existing subject folders or set `overwrite` to 'yes'"
                    )

    n_to_process = len(packets["ok"])
    if overwrite:
        n_to_process += len(packets["exist"])

    # just testing
    if n_to_process and test:
        print("\n---> To process them, remove the --test option!")
        return
    elif not n_to_process:
        if check.lower() == "any":
            if masterinbox:
                raise ge.CommandFailed(
                    "import_dicom",
                    "No packets found to process",
                    "No packets were found to be processed in the master inbox [%s]!"
                    % (os.path.abspath(masterinbox)),
                    "Please check your data!",
                )
            else:
                raise ge.CommandFailed(
                    "import_dicom",
                    "No sessions found to process",
                    "No sessions were found to be processed in session folder [%s]!"
                    % (os.path.abspath(sessionsfolder)),
                    "Please check your data!",
                )
        else:
            if masterinbox:
                raise ge.CommandNull(
                    "import_dicom",
                    "No packets found to process",
                    "No packets were found to be processed in the master inbox [%s]!"
                    % (os.path.abspath(masterinbox)),
                )
            else:
                raise ge.CommandNull(
                    "import_dicom",
                    "No sessions found to process",
                    "No sessions were found to be processed in session folder [%s]!"
                    % (os.path.abspath(sessionsfolder)),
                )

    # ---- Ok, now loop through the packets
    afolder = os.path.join(sessionsfolder, "archive", "MR")
    if not os.path.exists(afolder):
        os.makedirs(afolder)
        print("---> Created Archive folder for processed packages.")

    report = {"failed": [], "ok": []}

    # ---> clean existing data if needed
    if overwrite:
        if packets["exist"]:
            print("---> Cleaning existing data in folders:")
            for afile, session in packets["exist"]:
                sfolder = os.path.join(sessionsfolder, session["sessionid"])
                print(" ... %s" % (sfolder))
                if masterinbox:
                    ifolder = os.path.join(sfolder, "inbox")
                    if os.path.exists(ifolder):
                        _safe_rmtree(ifolder)
                nfolder = os.path.join(sfolder, "nii")
                dfolder = os.path.join(sfolder, "dicom")
                for rmfolder in [nfolder, dfolder]:
                    if os.path.exists(rmfolder):
                        _safe_rmtree(rmfolder)

        packets["ok"] += packets["exist"]

    # ---> process packets
    print("---> Starting to process %d packets ..." % (len(packets["ok"])))

    for afile, session in packets["ok"]:
        note = []
        try:
            sfolder = os.path.join(sessionsfolder, session["sessionid"])
            ifolder = os.path.join(sfolder, "inbox")
            dfolder = os.path.join(sfolder, "dicom")

            # --- Big info
            print("\n\n---=== PROCESSING %s ===---\n" % (session["sessionid"]))

            if masterinbox and not os.path.exists(ifolder):
                os.makedirs(ifolder)
                files = [afile]
            else:
                if "archives" in session and session["archives"]:
                    files = session["archives"]
                else:
                    files = [ifolder]

            if not existing_structure:
                dnum = 0
                fnum = 0

                for p in files:
                    # --- unzip or copy the package
                    if iszip.match(p):
                        ptype = "zip"
                        fnum, dnum = _extract_zip(
                            p, os.path.basename(p), fnum, dnum, ifolder
                        )

                    elif istar.match(p):
                        ptype = "tar"
                        fnum, dnum = _extract_tar(
                            p, os.path.basename(p), fnum, dnum, ifolder
                        )

                    else:
                        ptype = "folder"
                        if masterinbox and ifolder != p:
                            fnum, dnum = _process_folder(p, fnum, dnum, ifolder)

                            # if os.path.exists(ifolder):
                            #     shutil.rmtree(ifolder)
                            # print("...  copying %s dicom files" % (os.path.basename(p)))
                            # shutil.copytree(p, ifolder)
            else:
                source_folder = afile
                # --- unpack zip first
                if iszip.match(afile):
                    print(f"---> found a zip archive at {afile}")
                    temp_dir = tempfile.mkdtemp(prefix="import_dicom_")
                    with zipfile.ZipFile(afile, "r") as z:
                        z.extractall(temp_dir)
                    source_folder = temp_dir

                elif istar.match(afile):
                    temp_dir = tempfile.mkdtemp(prefix="import_dicom_")
                    print(f"---> found a tar archive at {afile}")
                    with tarfile.open(afile, "r:*") as t:
                        t.extractall(temp_dir)
                    source_folder = temp_dir

                # first‐level subfolders only
                fnum = 0
                for root, dirs, files in os.walk(source_folder):
                    for sub in dirs:
                        subpath = os.path.join(root, sub)
                        if not os.path.isdir(subpath):
                            continue
                        # find any .dcm files
                        dcms = glob.glob(os.path.join(subpath, "*.dcm"))
                        if not dcms:
                            continue
                        # one group found → bump fnum, make dest, copy & rename
                        fnum += 1
                        dest = os.path.join(ifolder, str(fnum))
                        os.makedirs(dest, exist_ok=True)
                        print(f"---> found {len(dcms)} dicom files in {subpath}")
                        print(f"     ... copying to {dest}")
                        for dcm in dcms:
                            name = os.path.basename(dcm)
                            shutil.copy2(dcm, os.path.join(dest, f"{fnum}-{name}"))

            # ---> run sort dicom
            print()
            sort_dicom(folder=sfolder)

            # ---> run clean dicom
            if clean_dicom_folders:
                print()
                clean_dicom(folder=sfolder, verbose=verbose)

            # ---> run dicom to nii
            print()
            dicom2niix(
                folder=sfolder,
                clean="no",
                unzip=unzip,
                gzip=gzip,
                sessionid=session["sessionid"],
                tool=tool,
                parelements=parelements,
                add_image_type=add_image_type,
                add_json_info=add_json_info,
                verbose=True,
            )

            # ---> archive
            if archive != "leave":
                s = "Processing packages: " + archive
                print()
                print(s)
                print("".join(["=" for e in range(len(s))]))

            for p in files:
                if masterinbox or re.search(
                    r"\.zip$|\.tar$|\.tar.gz$|\.tar.bz2$|\.tarz$|\.tar.bzip2$|\.tgz$", p
                ):
                    archivetarget = os.path.join(afolder, os.path.basename(p))

                    # --- move package to archive
                    if archive == "move":
                        if os.path.exists(archivetarget):
                            print(
                                "...  WARNING: %s already exists in archive and it will not be moved!"
                                % (os.path.basename(p))
                            )
                            note.append(
                                "WARNING: %s already exists in archive and it was not moved!"
                                % (os.path.basename(p))
                            )
                        else:
                            print("...  moving %s to archive" % (os.path.basename(p)))
                            shutil.move(p, archivetarget)
                            print("     -> done!")

                    # --- copy package to archive
                    elif archive == "copy":
                        if os.path.exists(archivetarget):
                            print(
                                "...  WARNING: %s already exists in archive and it will not be copied!"
                                % (os.path.basename(p))
                            )
                            note.append(
                                "WARNING: %s already exists in archive and it was not copied!"
                                % (os.path.basename(p))
                            )
                        else:
                            print("...  copying %s to archive" % (os.path.basename(p)))
                            if ptype == "folder":
                                shutil.copytree(p, archivetarget)
                            else:
                                shutil.copy2(p, afolder)
                            print("     -> done!")

                    # --- delete original package
                    elif archive == "delete":
                        print("...  deleting packet [%s]" % (os.path.basename(p)))
                        if ptype == "folder":
                            _safe_rmtree(p)
                        else:
                            os.remove(p)

            report["ok"].append((afile, dict(session), note))

        except ge.CommandFailed as e:
            report["failed"].append(
                (afile, dict(session), ["%s: %s" % (e.function, e.error)])
            )

    print("\nFinal report\n============")

    if report["ok"]:
        print("\nSuccessfully processed:")
        for afile, session, notes in report["ok"]:
            print("... %s [%s]" % (session["sessionid"], afile))
            for note in notes:
                print("    %s" % (note))

    if report["failed"]:
        print("\nFailed to process:")
        for afile, session, notes in report["failed"]:
            print("... %s [%s]" % (session["sessionid"], afile))
            for note in notes:
                print("    %s" % (note))
        raise ge.CommandFailed(
            "import_dicom", "Some packages failed to process", "Please check report!"
        )

    return


def get_dicom_info(dicomfile=None, scanner="siemens"):
    """
    ``get_dicom_info dicomfile=<dicom_file> [scanner=siemens]``

    Inspect the specified DICOM file.

    ..  qx_command:
        type: utility

    Parameters:
        --dicomfile (str, ''):
            The path to the DICOM file to be inspected.

        --scanner (str, 'siemens'):
            The scanner on which the data was acquired, currently only
            "siemens" and "philips" are supported.

    Notes:
        The command inspects the specified DICOM file (dicomfile) for information
        that is relevant for HCP preprocessing and prints out the report.
        Specifically it looks for and reports the following information:

        - Institution
        - Scanner
        - Sequence
        - Session ID
        - Sample spacing
        - Bandwidth
        - Acquisition Matrix
        - Dwell Time
        - Slice Acquisition Order

        If the information can not be found or computed it is listed as 'undefined'.

        Currently only DICOM files generated by Siemens and Philips scanners are
        supported.

    Examples:
        ::

            qunex get_dicom_info dicomfile=ap308e727bxehd2.372.2342.42566.dcm
    """

    if dicomfile is None:
        raise ge.CommandError(
            "get_dicom_info", "No path to the dicom file was provided"
        )

    if not os.path.exists(dicomfile):
        raise ge.CommandFailed(
            "get_dicom_info",
            "DICOM file does not exist",
            "Please check path! [%s]" % (dicomfile),
        )

    if scanner not in ["siemens", "philips"]:
        raise ge.CommandError(
            "get_dicom_info",
            "Scanner not supported",
            "The specified scanner is not yet supported! [%s]" % (scanner),
        )

    d = read_dicom_base(dicomfile)
    ok = True

    print("\nHCP relevant information\n(dicom %s)\n" % (dicomfile))

    try:
        print("            Institution:", d[0x0008, 0x0080].value)
    except:
        print("            Institution: undefined")

    try:
        print(
            "                Scanner:", d[0x0008, 0x0070].value, d[0x0008, 0x1090].value
        )
    except:
        print("                Scanner: undefined")

    try:
        print("Magnetic field strength:", d[0x0018, 0x0087].value)
        tesla = float(d[0x0018, 0x0087].value)
    except:
        print("Magnetic field strength: unknown")
        tesla = None

    try:
        print("               Sequence:", d[0x0008, 0x103E].value)
    except:
        print("               Sequence: undefined")

    try:
        print("             Session ID:", d[0x0010, 0x0020].value)
    except:
        print("             Session ID: undefined")

    if scanner == "siemens":
        try:
            print("         Sample spacing:", d[0x0019, 0x1018].value)
        except:
            print("         Sample spacing: undefined")

        try:
            bw = d[0x0019, 0x1028].value
            print("               Bandwith:", bw)
        except:
            print("               Bandwith: undefined")
            ok = False

        try:
            am = d[0x0051, 0x100B].value
            print("     Acquisition Matrix:", am)
            am = float(am.split("*")[0].replace("p", ""))
        except:
            print("     Acquisition Matrix: undefined")
            ok = False

        if ok:
            dt = 1 / (bw * am)
            print("             Dwell Time:", dt)
        else:
            print("             Dwell Time: Could not compute, data missing!")

        try:
            sinfo = d[0x0029, 0x1020].value
            sinfo = sinfo.split("\n")
            for l in sinfo:
                if "sSliceArray.ucMode" in l:
                    for k, v in [
                        ("0x1", "Sequential Ascending"),
                        ("0x2", "Sequential Ascending"),
                        ("0x4", "Interleaved"),
                    ]:
                        if k in l:
                            print("Slice Acquisition Order: %s" % (v))
        except:
            print("Slice Acquisition Order: Unknown")

    # --- Philips data

    if scanner == "philips":
        try:
            print("        Repetition Time: %.2f" % (float(d[0x0018, 0x0080].value)))
        except:
            try:
                print("        Repetition Time:", d[0x2005, 0x1030].value[0])
            except:
                print("        Repetition Time: undefined")

        try:
            print("             Flip Angle:", d[0x2001, 0x1023].value)
        except:
            print("             Flip Angle: undefined")

        try:
            print("       Number of Echoes:", d[0x2001, 0x1014].value)
        except:
            print("       Number of Echoes: undefined")

        try:
            print("   Phase Encoding Steps:", d[0x0018, 0x0089].value)
        except:
            print("   Phase Encoding Steps: undefined")

        try:
            print("      Echo Train Length:", d[0x0018, 0x0091].value)
            etl = float(d[0x0018, 0x0091].value)
        except:
            print("      Echo Train Length: undefined")
            etl = None

        try:
            print("             EPI Factor:", d[0x2001, 0x1013].value)
        except:
            print("             EPI Factor: undefined")

        try:
            print("        Water Fat Shift:", d[0x2001, 0x1022].value)
            wfs = float(d[0x2001, 0x1022].value)
        except:
            print("        Water Fat Shift: undefined")
            wfs = None

        try:
            print("        Pixel Bandwidth:", d[0x0018, 0x0095].value)
        except:
            print("        Pixel Bandwidth: undefined")

        try:
            print("   Acquisition Duration:", d[0x0018, 0x9073].value)
        except:
            print("   Acquisition Duration: undefined")

        try:
            print("   Parallel Acquisition:", d[0x0018, 0x9077].value)
            if d[0x0018, 0x9077].value == "YES":
                try:
                    print(
                        "%23s: in plane: %.2f out of plane %.2f"
                        % (
                            d[0x0018, 0x9078].value,
                            d[0x0018, 0x9168].value,
                            d[0x0018, 0x9155].value,
                        )
                    )
                except:
                    print("                 Factor: undefined")
        except:
            print("   Parallel Acquisition: undefined")

        try:
            print(
                "                 Matrix: [%d, %d, %d]"
                % (
                    d[0x0028, 0x0010].value,
                    d[0x0028, 0x0011].value,
                    d[0x2001, 0x1018].value,
                )
            )
        except:
            print("                 Matrix: undefined")

        try:
            print(
                "          Field of View: [%d, %d, %d]"
                % (
                    d[0x2005, 0x1074].value,
                    d[0x2005, 0x1076].value,
                    d[0x2005, 0x1075].value,
                )
            )
        except:
            print("          Field of View: undefined")

        try:
            if tesla == 3:
                wfdiff = 3.35
                resfreq = 42.576
                dwelltime = 1 / (tesla * wfdiff * resfreq / wfs * etl)
                print("   Parallel Acquisition: undefined")
                print("    Estimated dwelltime: %.8f" % (dwelltime))
        except:
            print("    Estimated dwelltime: unknown")

    # --- look for slice ordering info

    print
