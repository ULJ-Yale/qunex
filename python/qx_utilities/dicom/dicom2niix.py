#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``dicom2niix.py``

The ``dicom2niix`` command: converts a session's sorted DICOM or PAR/REC
files to NIfTI using dcm2niix, dcm2nii or the Matlab based dicm2nii, and
writes the session and DICOM report files.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import glob
import json
import os
import subprocess
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed

import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.img as gi
import qx_utilities.general.log as gl
import qx_utilities.general.nifti as gn
from qx_utilities.dicom.dicom_archive import _unzip_dicom, _zip_dicom
from qx_utilities.dicom.dicom_info import read_dicom_info, read_par_info
from qx_utilities.dicom.dicom_utils import mcommand


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
    _log=None,
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

    log = gl.log_or_console(_log)

    log.info("Running dicom2niix\n==================")

    if sessionid and sessionid.lower() == "none":
        sessionid = None

    base = folder
    null = open(os.devnull, "w")
    dmcf = os.path.join(folder, "dicom")
    imgf = os.path.join(folder, "nii")

    try:
        if add_image_type is None or add_image_type == "":
            add_image_type = 0
        else:
            add_image_type = int(add_image_type)
    except Exception:
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
    except Exception:
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
            with log.section("Deleting preexisting files:"):
                for p in prior:
                    log.detail(p)
                    os.remove(p)
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
                log.step("Unzipping files (this might take a while)")
            _unzip_dicom(dmcf, parelements, _log=log)
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
    files = []

    log.step("Analyzing data")

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
                    except Exception:
                        try:
                            db = info["dicom"][0x0020, 0x0013].value
                        except Exception:
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
            except Exception:
                print(
                    "# WARNING: Could not read dicom file! Skipping folder %s"
                    % (folder),
                    file=r,
                )
                log.warning(
                    "Could not read dicom file! Skipping folder %s" % (folder)
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
                log.step(
                    "Processing images from %s (%s) scanned on %s"
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

        niiid = str(niinum)

        if tool == "auto":
            if par:
                utool = "dicm2nii"
                log.step(
                    "Using dicm2nii for conversion of PAR/REC to NIfTI if Matlab is available. [%s: %s]"
                    % (niiid, info["seriesDescription"])
                )
            else:
                utool = "dcm2niix"
                log.step(
                    "Using dcm2niix for conversion to NIfTI. [%s: %s]"
                    % (niiid, info["seriesDescription"])
                )
        else:
            utool = tool

        if utool == "dicm2nii":
            if "matlab" in mcommand:
                if setdi:
                    log.step("Setting up dicm2nii settings ...")
                    subprocess.call(
                        "matlab -nodisplay -r \"setpref('dicm2nii_gui_para', 'save_patientName', true); setpref('dicm2nii_gui_para', 'save_json', true); setpref('dicm2nii_gui_para', 'use_parfor', true); setpref('dicm2nii_gui_para', 'use_seriesUID', true); setpref('dicm2nii_gui_para', 'lefthand', true); setpref('dicm2nii_gui_para', 'scale_16bit', false); exit\" ",
                        shell=True,
                        stdout=null,
                        stderr=null,
                    )
                    log.detail("done!")
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
                log.step(
                    "Using dcm2niix for conversion as Matlab is not available! [%s: %s]"
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

    gc.run_external_parallel(calls, cores=parelements, _log=log)

    log.step("Processed sequences:")
    for niinum, folder, info in files:
        # the row is one record rather than a line assembled with `end=" "`
        # across the branches below: a record is a whole line, and the notes
        # that used to be appended to it are records of their own
        row = logs.pop(0)
        print(row, end=" ", file=r)
        if verbose:
            log.detail(row)

        tfname = False
        imgs = glob.glob(os.path.join(folder, "*.nii*"))
        imgs.sort()

        # --- check if resulting nifti is present

        nimg = len(imgs)
        if nimg == 0:
            print(" WARNING: no NIfTI file created!", file=r)
            if verbose:
                log.warning("no NIfTI file created!")
            continue
        elif nimg > 9:
            print(
                " WARNING: More than 9 images created from this sequence! Skipping. Please check conversion log!",
                file=r,
            )
            if verbose:
                log.warning(
                    "More than 9 images created from this sequence! Skipping. Please check conversion log!"
                )
            continue
        else:
            print("", file=r)

            imgnum = 0

            if debug:
                log.detail(
                    "found %s nifti file(s): %s"
                    % (nimg, "\n                            ".join(imgs))
                )

            for image in imgs:
                if not os.path.exists(image):
                    continue
                if debug:
                    log.detail(
                        "processing: %s [%s]" % (image, os.path.basename(image))
                    )
                if image.endswith(".nii"):
                    if debug:
                        log.detail("gzipping: %s" % (image))
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
                    log.detail("moving '%s' to '%s'" % (image, tfname), depth=1)
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
                        except Exception:
                            print(
                                "     WARNING: Could not parse the JSON file [%s]!"
                                % (jsonsrc),
                                file=r,
                            )
                            if verbose:
                                log.warning(
                                    "Could not parse the JSON file [%s]!" % (jsonsrc)
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
                            log.warning(
                                "unusual geometry of the NIfTI file: %d %d %d %d [xyzf]"
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
                                log.warning(
                                    "number of frames in nii does not match dicom information: %d vs. %d frames"
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
                                        log.warning(
                                            "reslicing image to %d slices and %d good frames"
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
                                        log.warning(
                                            "not enough slices (%d) to make a complete volume."
                                            % (hdr.sizez)
                                        )
                            else:
                                print(
                                    "     WARNING: no slice number information, use qunex reslice manually to correct %s"
                                    % (tfname),
                                    file=r,
                                )
                                if verbose:
                                    log.warning(
                                        "no slice number information, use qunex reslice manually to correct %s"
                                        % (tfname)
                                    )

    r.close()
    stxt.close()

    # gzip files
    if gzip == "file" or gzip == "folder":
        if verbose:
            log.step("Compressing dicom with option {}:".format(gzip))

        with ProcessPoolExecutor(parelements) as executor:
            pending_futures = []
            for folder in folders:
                future = executor.submit(_zip_dicom, gzip, folder)
                log.detail("submit archive dicom: {}".format(folder))
                pending_futures.append(future)

            exceptions = []
            for future in as_completed(pending_futures):
                if future.exception() is not None:
                    # Unhandled
                    e = future.exception()
                    log.error("unhandled exception")
                    log.raw("\n" + traceback.format_exc())
                    exceptions.append(e)
                    continue
                r = future.result()
                if r["status"] == "ok":
                    log.detail("archived {}".format(r["args"]["dicom_folder"]))
                else:
                    log.error("archive failed {}".format(r["args"]["dicom_folder"]))
                    log.raw("\n" + r["traceback"])
                    exceptions.append(r["exception"])
            if len(exceptions) > 0:
                raise ge.CommandError(
                    "dicom2nii", "Unable to archive one or more acquisitions"
                )
