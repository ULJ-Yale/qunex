#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``legacy/dicom2nii.py``

The superseded ``dicom2nii`` command.

Drives the retired ``dcm2nii`` tool only. Kept for backwards compatibility;
use ``dicom2niix`` instead.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import glob
import os
import subprocess
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.img as gi
import qx_utilities.general.log as gl
import qx_utilities.general.nifti as gn
import qx_utilities.general.qximg as qxi
from qx_utilities.dicom.dicom_archive import _unzip_dicom, _zip_dicom
from qx_utilities.dicom.dicom_info import (
    get_dicom_time,
    get_id,
    get_tr_te,
    read_dicom_base,
)


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
    except Exception:
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

    gl.print_qunex_header(file=r)
    gl.print_qunex_header(file=stxt)

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
        except Exception:
            try:
                series_description = d.ProtocolName
            except Exception:
                series_description = "None"

        try:
            time = datetime.strptime(d.ContentTime[0:6], "%H%M%S").strftime("%H:%M:%S")
        except Exception:
            try:
                time = datetime.strptime(d.StudyTime[0:6], "%H%M%S").strftime(
                    "%H:%M:%S"
                )
            except Exception:
                time = ""

        tr, TE = get_tr_te(d)

        try:
            nslices = d[0x2001, 0x1018].value
        except Exception:
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
        except Exception:
            pass

        # --- Special nii naming for Philips

        niinum = c
        try:
            if d.Manufacturer == "Philips Medical Systems":
                niinum = (d.SeriesNumber - 1) / 100
        except Exception:
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
        except Exception:
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

    _ = gc.run_external_parallel(calls, cores=parelements)

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
