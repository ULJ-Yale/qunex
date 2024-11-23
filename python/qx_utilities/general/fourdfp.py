#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``4dfp.py``

This file holds code for running 4dfp NIL preprocessing commands and volume to
surface mapping. It implements the following commands:

--run_nil           Runs NIL preprocessing of a session.
--run_nil_folder    Runs NIL preprocessing of sessins in a folder.
--map2pals          Maps volume image to PALS Atlas caret image.
--map2hcp           Maps volume image to CIFTI dense scalar image.

Use gmri to run the commands from the terminal.
"""

import os
import subprocess
import os.path
import glob
import re

import general.core as gc
import general.exceptions as ge

from datetime import datetime

template = """@ economy = 5
@ go = 1
set tgdir  = {{data}}
set scrdir =
set inpath = {{inpath}}
set patid  = {{patid}}
set mprs   = ( {{t1}} )
set t1w    = ()
set tse    = ( {{t2}} )
set irun   = ( {{boldnums}} )
set fstd   = ( {{bolds}} )
set target = /Applications/NIL/atlas/TRIO_Y_NDC
@ nx = 80
@ ny = 80
set TR_vol = {{TR}}
set TR_slc = 0.
set imaflip = 0
set seq = ""
@ epidir = 0
@ skip = 2
@ epi2atl = 1
@ normode = 0
"""

recode = {True: "ok", False: "missing"}


def run_nil_folder(folder=".", pattern=None, overwrite=None, sourcefile=None):
    """
    ``run_nil_folder [folder=.] [pattern=OP*] [overwrite=no] [sourcefile=session.txt]``

    Goes through the folder and runs run_nil on all the subfolders that match the
    pattern. Setting overwrite to overwrite.

    INPUTS
    ======

    --folder          the base study sessions folder (e.g. WM44/sessions) where
                       OP folders and the inbox folder with the new packages
                       from the scanner reside.
    --pattern         which sessionsfolders to match (default OP*).
    --overwrite       whether to overwrite existing (params and BOLD) files.
    --sourcefile      the name of the session file.

    EXAMPLE USE
    ===========

    ::

        qunex run_nil_folder folder=. pattern=OP* overwrite=no sourcefile=session.txt
    """

    if pattern is None:
        pattern = "OP*"
    if sourcefile is None:
        sourcefile = "session.txt"
    if overwrite is None:
        overwrite = False
    elif overwrite:
        pass
    elif overwrite == "yes" or overwrite is True:
        overwrite = True
    else:
        overwrite = False

    subjs = glob.glob(os.path.join(folder, pattern))

    subjs = [
        (
            e,
            os.path.exists(os.path.join(e, "session.txt")),
            os.path.exists(os.path.join(e, "dicom", "DICOM-Report.txt")),
            os.path.exists(os.path.join(e, "4dfp", "params")),
        )
        for e in subjs
    ]

    do = []
    print("\n---=== Running NIL preprocessing on folder %s ===---\n" % folder)
    print("List of sessions to process\n")
    print("%-15s%-15s%-15s%-10s" % ("session", "session.txt", "DICOM-Report", "params"))
    for subj, stxt, sdicom, sparam in subjs:
        print(
            "%-15s%-15s%-15s%-10s --->"
            % (os.path.basename(subj), recode[stxt], recode[sdicom], recode[sparam]),
            end=" ",
        )
        if not stxt:
            print("skipping processing")
        else:
            if not sdicom:
                print("estimating TR as 2.49836", end=" ")
            if not sparam:
                print("creating param file", end=" ")
            elif overwrite:
                print("overwriting existing params file", end=" ")
            else:
                print("working with existing params file", end=" ")
            do.append(subj)
        print("")

    for s in do:
        try:
            run_nil(s, overwrite, sourcefile)
        except:
            print("---> Failed running NIL preprocessing on", s)

    print("\n---=== Done NIL preprocessing on folder %s ===---\n" % (folder))


def run_nil(folder=".", overwrite=None, sourcefile=None):
    """
    ``run_nil [folder=.] [overwrite=no] [sourcefile=session.txt]``

    Runs NIL preprocessing script on the session data in specified folder.

    INPUTS
    ======

    --folder          session's folder with nii and dicom folders and
                      session.txt file.
    --overwrite       whether to overwrite existing parameters file or existing
                      BOLD data.
    --sourcefile      the name of the session file.

    USE
    ===

    Runs NIL preprocessing script on the session data in specified folder.
    Uses session.txt to identify structural and BOLD runs and DICOM-report.txt
    to get TR value. The processing is saved to a datestamped log in the 4dfp
    folder.
    """

    if overwrite is None:
        overwrite = False
    elif overwrite:
        pass
    elif overwrite == "yes" or overwrite is True:
        overwrite = True
    else:
        overwrite = False
    if sourcefile is None:
        sourcefile = "session.txt"

    print("\n---> processing session %s" % (os.path.basename(folder)))

    # ---> process session.txt

    rbold = re.compile(r"bold([0-9]+)")

    info = gc.read_session_data(os.path.join(folder, sourcefile))

    t1, t2, bold, raw, data, sid = False, False, [], False, False, False

    if not info:
        raise ValueError("ERROR: No data in session.txt! [%s]!" % (sourcefile))

    for k, v in info[0].items():
        if k == "raw_data":
            raw = v
        elif k == "data":
            data = v
        elif k == "id":
            sid = v
        elif k.isdigit():
            rb = rbold.match(v["name"])
            if v["name"] == "T1w":
                t1 = k
            elif v["name"] == "T2w":
                t2 = k
            elif rb:
                bold.append((k, rb.group(1)))
    bold.sort(key=lambda e: e[1])

    print(
        "...  identified images: t1: %s, t2: %s, bold:" % (t1, t2), [k for k, b in bold]
    )

    # ---- check for 4dfp folder

    if not os.path.exists(os.path.join(folder, "4dfp")):
        print("...  creating 4dfp folder")
        os.mkdir(os.path.join(folder, "4dfp"))

    # ---- check for params

    if overwrite or (not os.path.exists(os.path.join(folder, "4dfp", "params"))):

        # ---- check for dicom and TR

        TR = None
        if os.path.exists(os.path.join(folder, "dicom", "DICOM-Report.txt")):
            with open(os.path.join(folder, "dicom", "DICOM-Report.txt")) as f:
                for line in f:
                    if ("BOLD" in line and not "C-BOLD" in line) or ("bold" in line):
                        m = re.search(r"TR +([0-9.]+),", line)
                        if m:
                            TR = m.group(1)
                            TR = float(TR) / 1000
                            print(
                                "...  Extracted TR info from DICOM-Report, using TR of",
                                TR,
                            )
                            break
        if TR is None or TR == 0.0:
            "...  No DICOM-Report, assuming TR of 2.49836"
            TR = 2.49836

        # ---- create params content

        print("...  creating params file")
        params = template
        params = params.replace("{{data}}", data)
        params = params.replace("{{inpath}}", raw)
        params = params.replace("{{patid}}", sid)
        params = params.replace("{{TR}}", str(TR))
        if t1:
            params = params.replace("{{t1}}", t1 + "-o.nii.gz")
        if t2:
            params = params.replace("{{t2}}", t2 + "-o.nii.gz")
        params = params.replace("{{boldnums}}", " ".join(["%s" % (b) for k, b in bold]))
        params = params.replace("{{bolds}}", " ".join([k + ".nii.gz" for k, b in bold]))

        pfile = open(os.path.join(folder, "4dfp", "params"), "w")
        print(params, file=pfile)
        pfile.close()

    else:
        print("...  using existing params file")

    # ---- check for existing BOLD data

    isthere, ismissing = [], []
    for b in range(1, len(bold) + 1):
        if os.path.exists(
            os.path.join(
                folder,
                "4dfp",
                "bold" + str(b),
                sid + "_b" + str(b) + "_faln_dbnd_xr3d_atl.4dfp.img",
            )
        ):
            isthere.append(str(b))
        else:
            ismissing.append(str(b))

    if isthere:
        if overwrite:
            print(
                "...  Some bolds exist and will be overwritten! [%s]"
                % (" ".join(isthere))
            )
            if ismissing:
                print("...  Some bolds were missing! [%s]" % (" ".join(ismissing)))
        else:
            if ismissing:
                print(
                    "...  Some bolds exist [%s], however some are missing [%s]!"
                    % (" ".join(isthere), " ".join(ismissing))
                )
                print("...  Skipping this session!")
                return
            else:
                print(
                    "...  BOLD files are allready processed! [%s]" % (" ".join(isthere))
                )
                print("...  Skipping this session!")
                return

    # ---- run avi preprocessing

    logname = "preprocess." + datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f") + ".log"
    print("...  running NIL preprocessing, saving log to %s " % (logname))
    logfile = open(os.path.join(folder, "4dfp", logname), "w")

    r = subprocess.call(
        ["preproc_avi_nifti", os.path.join(folder, "4dfp", "params")],
        stdout=logfile,
        stderr=subprocess.STDOUT,
    )

    logfile.close()

    if r:
        print(
            "...  WARNING: preproc_NIL_nifti finished with errors, please check log file"
        )
    else:
        print("...  preproc_NIL_nifti finished successfully")


def map2pals(volume, metric, atlas="711-2C", method="interpolated", mapping="afm"):
    """
    ``map2pals volume=<volume file> metric=<metric file> [atlas=711-2C] [method=interpolated] [mapping=afm]``

    Maps volume files to metric surface files using PALS12 surface atlas.

    INPUTS
    ======

    --volume       a volume file or a space separated list of volume files - put
                   in quotes
    --metric       the name of the metric file that stores the mapping
    --atlas        volume atlas from which to map (711-2C by default or 711-2B,
                   AFNI, FLIRT, FNIRT, SPM2, SPM5, SPM95, SPM96, SPM99,
                   MRITOTAL)
    --method       interpolated, maximum, enclosing, strongest, Gaussian
                   (for other options see caret_command)
    --mapping      a single mapping option or a space separated list in quotes.
                   [afm] The options are:

                   - afm (average fiducial mapping)
                   - mfm (average of mapping to all PALS cases (multifiducial
                     mapping))
                   - min (minimum of mapping to all PALS cases)
                   - max (maximum of mapping to all PALS cases)
                   - std-dev (sample standard deviation of mapping to all PALS
                     cases)
                   - std-error (standard error of mapping to all PALS cases)
                   - all-cases (mapping to each of the PALS12 cases)
    """

    methods = {
        "interpolated": "METRIC_INTERPOLATED_VOXEL",
        "maximum": "METRIC_MAXIMUM_VOXEL",
        "enclosing": "METRIC_ENCLOSING_VOXEL",
        "strongest": "METRIC_STRONGEST_VOXEL",
        "gaussian": "METRIC_GAUSSIAN",
    }
    if method in methods:
        method = methods[method]

    volumes = volume.split()
    mapping = ["-metric-" + e for e in mapping.split()]

    metric = metric.replace(".metric", "") + ".metric"

    for volume in volumes:
        volume = (
            volume.replace(".img", "").replace(".ifh", "").replace(".4dfp", "")
            + ".4dfp.ifh"
        )
        for structure in ["LEFT", "RIGHT"]:
            print(
                "---> mapping %s to PALS %s [%s %s %s]"
                % (volume, structure, atlas, method, " ".join(mapping))
            )
            subprocess.call(
                [
                    "caret_command",
                    "-volume-map-to-surface-pals",
                    metric,
                    metric,
                    atlas,
                    structure,
                    method,
                    volume,
                ]
                + mapping
            )


def map2hcp(volume, method="trilinear"):
    """
    ``map2hcp volume=<volume file> [method=trilinear]``

    Maps volume files to dense scalar files using HCP templates.

    INPUTS
    ======

    --volume      a volume file or a space separated list of volume files - put
                  in quotes
    --method      one of: trilinear, enclosing, cubic, ribbon constrained

    USE
    ===

    Maps volume files to dense scalar files using HCP templates. It expects
    "HCPATLAS" environment variable to be set, to be able to find the right
    templates.
    """

    if not "HCPATLAS" in os.environ:
        raise ge.CommandError(
            "map2hcp",
            "HCPATLAS environment variable not set.",
            "Can not find HCP Template files!",
            "Please check your environment settings!",
        )

    apath = os.environ["HCPATLAS"]
    tpath = os.path.join(apath, "91282_Greyordinates")

    if method not in ["trilinear", "enclosing", "cubic", "ribbon-constrained"]:
        raise ge.CommandError("map2hcp", "Unrecognised mapping method [%s]!" % (method))
    method = "-" + method

    volumes = volume.split()
    for volume in volumes:
        target = volume.replace(".nii", "").replace(".gz", "") + ".dscalar.nii"
        print("---> mapping %s to %s using %s" % (volume, target, method))
        for structure in ["L", "R"]:
            subprocess.call(
                [
                    "wb_command",
                    "-volume-to-surface-mapping",
                    volume,
                    os.path.join(
                        apath,
                        "Q1-Q6_R440.%s.midthickness.32k_fs_LR.surf.gii" % (structure),
                    ),
                    "tmp.%s.func.gii" % (structure),
                    method,
                ]
            )
        subprocess.call(
            [
                "wb_command",
                "-cifti-create-dense-scalar",
                target,
                "-volume",
                volume,
                os.path.join(tpath, "Atlas_ROIs.2.nii.gz"),
                "-left-metric",
                "tmp.L.func.gii",
                "-roi-left",
                os.path.join(tpath, "L.atlasroi.32k_fs_LR.shape.gii"),
                "-right-metric",
                "tmp.R.func.gii",
                "-roi-right",
                os.path.join(tpath, "R.atlasroi.32k_fs_LR.shape.gii"),
            ]
        )
        os.remove("tmp.L.func.gii")
        os.remove("tmp.R.func.gii")
