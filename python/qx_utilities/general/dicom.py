#!/usr/bin/env python2.7
# encoding: utf-8
"""
``dicom.py``

Functions for processing dicom images and converting them to NIfTI format:

--readPARInfo           Reads image info from Philips PAR/REC files.
--readDICOMInfo         Reads image info from DICOM files.
--dicom2niiz            Converts DICOM to NIfTI images.
--sort_dicom            Sorts the DICOM files into subfolders according to images.
--list_dicom            List the information on DICOM files.
--split_dicom           Split files from different sessions.
--import_dicom          Processes incoming data.
--get_dicom_info        Prints HCP relevant information from a DICOM file.

The commands are accessible from the terminal using gmri utility.
"""

"""
Copyright (c) Grega Repovs. All rights reserved.
"""

# import dicom
import os
import os.path
import sys
import re
import glob
import shutil
import datetime
import subprocess
import nifti
import qximg as qxi
import exceptions as ge
import zipfile
import tarfile
import gzip
import csv
import json
import core
import img as gi

try:
    import pydicom.filereader as dfr
except:
    import dicom.filereader as dfr


if "QUNEXMCOMMAND" not in os.environ:
    mcommand = "matlab -nojvm -nodisplay -nosplash -r"
else:
    mcommand = os.environ['QUNEXMCOMMAND']


def cleanName(string):
    """
    ``cleanName(string)``

    Function that makes sure that the string does not contain characters that 
    should not be in a file name.
    """
    return re.sub(r'[^A-Za-z0-9]', r'', string)



def matchAll(pattern, string):
    """
    ``matchAll(pattern, string)``

    Function that checks if the pattern matches the whole string.
    """

    m = re.match(pattern, string)

    if m:
        return m.group() == string
    else:
        return False


def readPARInfo(filename):
    """
    ``readPARInfo(filename)``
    
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
        raise ValueError('PAR file %s does not exist!' % (filename))

    info = {}
    with open(filename, 'r') as f:
        for line in f:
            if len(line) > 1 and line[0] == '.':
                line = line[1:].strip()
                k, v = [e.strip() for e in line.split(':  ')]
                info[k] = v

    info['sessionid']          = info['Patient name']
    info['seriesNumber']       = int(info['Acquisition nr']) * 100 + int(info['Reconstruction nr'])
    info['seriesDescription']  = info['Protocol name'].replace("WIP ", "")
    info['TR']                 = float(info['Repetition time [msec]'])
    info['TE']                 = 0.
    info['frames']             = int(info['Max. number of dynamics'])
    info['directions']         = int(info['Max. number of gradient orients']) - 1
    info['volumes']            = max(info['frames'], info['directions'])
    info['slices']             = int(info['Max. number of slices/locations'])
    info['datetime']           = info['Examination date/time']
    info['ImageType']          = [""]
    info['fileid']             = os.path.basename(filename)[:-4].replace('.', '_').replace('-', '_')

    return info


def readDICOMInfo(filename):
    """
    ``readDICOMInfo(filename)``

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
        raise ValueError('DICOM file %s does not exist!' % (filename))

    d = readDICOMBase(filename)

    info = {}

    info['sessionid']  = getID(d)

    # --- sessionid

    info['sessionid'] = ""
    if "PatientID" in d:
        info['sessionid'] = d.PatientID
    if info['sessionid'] == "":
        if "StudyID" in d:
            info['sessionid'] = d.StudyID

    # --- seriesNumber

    try:
        info['seriesNumber'] = int(d.SeriesNumber)
    except:
        info['seriesNumber'] = None

    # --- seriesDescription -- multiple possibilities

    for keyName in ['SeriesDescription', 'ProtocolName', 'SequenceName']:
        info['seriesDescription'] = d.get(keyName, 'anonymous')
        if info['seriesDescription'].lower() != 'anonymous':
            break

    # --- TR, TE

    TR, TE = 0., 0.
    try:
        TR = d.RepetitionTime
    except:
        try:
            TR = float(d[0x2005, 0x1030].value)
        except:
            try:
                TR = d[0x2005, 0x1030].value[0]
            except:
                pass
    try:
        TE = d.EchoTime
    except:
        try:
            TE = float(d[0x2001, 0x1025].value)
        except:
            pass

    info['TR'], info['TE'] = float(TR), float(TE)

    # --- Frames

    info['volumes'] = 0
    try:
        info['volumes'] = int(d[0x2001, 0x1081].value)
    except:
        info['volumes'] = 0


    info['frames']     = info['volumes']
    info['directions'] = info['volumes']

    # --- slices

    try:
        info['slices'] = int(d[0x2001, 0x1018].value)
    except:
        try:
            info['slices'] = int(d[0x0019, 0x100a].value)
        except:
            info['slices'] = 0

    # --- datetime

    try:
        info['datetime'] = datetime.datetime.strptime(str(int(float(d.StudyDate + d.ContentTime))), "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    except:
        try:
            info['datetime'] = datetime.datetime.strptime(str(int(float(d.StudyDate + d.StudyTime))), "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        except:
            info['datetime'] = ""

    # --- SOPInstanceUID

    try:
        info['SOPInstanceUID'] = d.SOPInstanceUID
    except:
        info['SOPInstanceUID'] = None

    # --- ImageType

    try:
        info['ImageType'] = d[0x0008, 0x0008].value
    except:
        info['ImageType'] = ""

    # --- dicom header

    info['dicom'] = d

    # --- fileid

    info['fileid'], _ = os.path.splitext(os.path.basename(filename))

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

def _at_frame(tag, VR, length):
    return tag == (0x5200, 0x9230) or tag == (0x7fe0, 0x0010)


def readDICOMBase(filename):
    # try partial read
    try:
        if '.gz' in filename:
            f = gzip.open(filename, 'r')
        else:
            f = open(filename, 'r')
        d = dfr.read_partial(f, stop_when=_at_frame)
        f.close()
        return d
    except:
        # return None
        # print " ===> WARNING: Could not partial read dicom file, attempting full read! [%s]" % (filename)
        try:
            d = dfr.read_file(filename, stop_before_pixels=True)
            return d
        except:
            # print " ===> ERROR: Could not read dicom file, aborting. Please check file: %s" % (filename)
            return None


def getDicomTime(info):
    try:
        time = datetime.datetime.strptime(str(int(float(info.StudyDate + info.ContentTime))), "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    except:
        try:
            time = datetime.datetime.strptime(str(int(float(info.StudyDate + info.StudyTime))), "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        except:
            time = ""
    return time


def getID(info):
    v = ""
    if "PatientID" in info:
        v = info.PatientID
    if v == "":
        if "StudyID" in info:
            v = info.StudyID
    return v


def getTRTE(info):
    TR, TE = 0, 0
    try:
        TR = info.RepetitionTime
    except:
        try:
            TR = float(info[0x2005, 0x1030].value)
            # TR = d[0x5200,0x9229][0][0x0018,0x9112][0][0x0018,0x0080].value
        except:
            try:
                TR = info[0x2005, 0x1030].value[0]
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
    return float(TR), float(TE)


def dicom2nii(folder='.', clean='ask', unzip='ask', gzip='ask', verbose=True, parelements=1, debug=False):
    """
    ``dicom2nii [folder=.] [clean=ask] [unzip=ask] [gzip=ask] [verbose=True] [parelements=1]``

    Converts MR images from DICOM to NIfTI format.

    INPUTS
    ======

    --folder           The base session folder with the dicom subfolder that 
                       holds session numbered folders with dicom files. [.]
    --clean            Whether to remove preexisting NIfTI files (yes), leave
                       them and abort (no) or ask interactively (ask). [ask]
    --unzip            If the dicom files are gziped whether to unzip them 
                       (yes), leave them be and abort (no) or ask interactively
                       (ask). [ask]
    --gzip             After the dicom files were processed whether to gzip them 
                       (yes), leave them ungzipped (no) or ask interactively
                       (ask). [ask]
    --verbose          Whether to be report on the progress (True) or not
                       (False). [True]
    --parelements      How many parallel processes to run dcm2nii conversion 
                       with. The number is one by default, if specified as 
                       'all', all available resources are utilized.

    OUTPUTS
    =======

    After running, the command will place all the generated NIfTI files into the
    nii subfolder, named with sequential image number. It will also generate two
    additional files: a session.txt file and a DICOM-Report.txt file.

    session.txt file
    ----------------

    The session.txt will be placed in the session base folder. It will contain
    the information about the session id, subject id, location of folders and a
    list of created NIfTI images with their description.

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

    For each of the listed images there will be a corresponding NIfTI file in
    the nii subfolder (e.g. 7.nii.gz for the first BOLD sequence), if a NIfTI
    file could be generated (Survey images for instance don't convert). The
    generated session.txt files form the basis for the following HCP and other
    processing steps.

    DICOM-Report.txt file
    ---------------------

    The DICOM-Report.txt file will be created and placed in the sessions's dicom
    subfolder. The file will list the images it found, the information about
    their original sequence number and the resulting NIfTI file number, the name
    of the sequence, the number of frames, TR and TE values, subject id, time of
    acquisition, information and warnings about any additional processing it had
    to perform (e.g. recenter structural images, switch f and z dimensions,
    reslice due to premature end of recording, etc.). In some cases some of the
    information (number of frames, TE, TR) might not be reported if that
    information was not present or couldn't be found in the DICOM file.

    dcm2nii log files
    -----------------

    For each image conversion attempt a dcm2nii_[N].log file will be created
    that holds the output of the dcm2nii command that was run to convert the
    DICOM files to a NIfTI image.

    USE
    ===

    The command is used to convert MR images from DICOM to NIfTI format. It
    searches for images within the dicom subfolder within the provided
    session folder (folder). It expects to find each image within a separate
    subfolder. It then converts the images to NIfTI format and places them
    in the nii folder within the session folder. To reduce the space use it
    can then gzip the dicom files (gzip). To speed the process up, it can
    run multiple dcm2nii processes in parallel (parelements).

    Before running, the command check for presence of existing NIfTI files. The
    behavior when finding them is defined by clean parameter. If set to 'ask',
    it will ask interactively, what to do. If set to 'yes' it will remove any
    existing files and proceede. If set to 'no' it will leave them and abort.

    Before running, the command also checks whether DICOM files might be
    gzipped. If that is the case, the response depends on the setting of the
    unzip parameter. If set to 'yes' it will automatically gunzip them and
    continue. If set to 'no', it will leave them be and abort. If set to 'ask',
    it will ask interactively, what to do.

    Multiple sessions and scheduling
    --------------------------------

    The command can be run for multiple sessions by specifying `sessions` and
    optionally `sessionsfolder` and `parelements` parameters. In this case the
    command will be run for each of the specified sessions in the sessionsfolder
    (current directory by default). Optional `filter` and `sessionids`
    parameters can be used to filter sessions or limit them to just specified id
    codes. (for more information see online documentation). `sessionsfolder` 
    will be filled in automatically as each sessions's folder. Commands will run
    in parallel by utilizing the specified number of parelements (1 by default).

    If `scheduler` parameter is set, the command will be run using the specified
    scheduler settings (see `qunex ?schedule` for more information). If set in
    combination with `sessions` parameter, sessions will be processed over
    multiple nodes, `core` parameter specifying how many sessions to run per
    node. Optional `scheduler_environment`, `scheduler_workdir`,
    `scheduler_sleep`, and `nprocess` parameters can be set.

    Set optional `logfolder` parameter to specify where the processing logs
    should be stored. Otherwise the processor will make best guess, where the
    logs should go.

    EXAMPLE USE
    ===========
    
    ::

        qunex dicom2nii folder=. clean=yes unzip=yes gzip=yes parelements=3

    Multiple sessions example::

        qunex dicom2nii \\
          --sessionsfolder="/data/my_study/sessions" \\
          --sessions="OP*" \\
          --clean=yes \\
          --unzip=yes \\
          --gzip=no \\
          --parelements=3
    """

    print "Running dicom2nii\n================="

    # debug = True
    base = folder
    null = open(os.devnull, 'w')
    dmcf = os.path.join(folder, 'dicom')
    imgf = os.path.join(folder, 'nii')

    # check if dicom folder existis

    if not os.path.exists(dmcf):
        raise ge.CommandFailed("dicom2nii", "No existing dicom folder", "Dicom folder with sorted dicom files does not exist at the expected location:", "[%s]." % (dmcf), "Please check your data!", "If inbox folder with dicom files exist, you first need to use sort_dicom command!")

    # check for existing .gz files

    prior = glob.glob(os.path.join(imgf, "*.nii.gz")) + glob.glob(os.path.join(dmcf, "*", "*.nii.gz"))
    if len(prior) > 0:
        if clean == 'ask':
            print "\nWARNING: The following files already exist:"
            for p in prior:
                print p
            clean = raw_input("\nDo you want to delete the existing NIfTI files? [no] > ")
        if clean == "yes":
            print "\nDeleting files:"
            for p in prior:
                print "---> ", p
                os.remove(p)
        else:
            raise ge.CommandFailed("dicom2nii", "Existing NIfTI files", "Please remove existing NIfTI files or run the command with 'clean' set to 'yes'.", "Aborting processing of DICOM files!")

    # gzipped files

    gzipped = glob.glob(os.path.join(dmcf, "*", "*.dcm.gz"))
    if len(gzipped) > 0:
        if unzip == 'ask':
            print "\nWARNING: DICOM files have been compressed using gzip."
            unzip = raw_input("\nDo you want to unzip the existing files? [no] > ")
        if unzip == "yes":
            if verbose:
                print "\nUnzipping files (this might take a while)"
            for g in gzipped:
                subprocess.call("gunzip " + g, shell=True)  # , stdout=null, stderr=null)
        else:
            raise ge.CommandFailed("dicom2nii", "Gzipped DICOM files", "Can not work with gzipped DICOM files, please unzip them or run with 'unzip' set to 'yes'.", "Aborting processing of DICOM files!")

    # --- open report files

    r    = open(os.path.join(dmcf, "DICOM-Report.txt"), 'w')
    stxt = open(os.path.join(folder, "session.txt"), 'w')

    # get a list of folders

    folders = [e for e in os.listdir(dmcf) if os.path.isdir(os.path.join(dmcf, e))]
    folders = [int(e) for e in folders if e.isdigit()]
    folders.sort()
    folders = [os.path.join(dmcf, str(e)) for e in folders]

    if not os.path.exists(imgf):
        os.makedirs(imgf)

    first = True
    c     = 0
    calls = []
    logs  = []
    reps  = []
    files = []

    for folder in folders:
        # d = dicom.read_file(glob.glob(os.path.join(folder, "*.dcm"))[-1], stop_before_pixels=True)
        d = readDICOMBase(glob.glob(os.path.join(folder, "*.dcm"))[-1])

        if d is None:
            print >> r, "# WARNING: Could not read dicom file! Skipping folder %s" % (folder)
            print "===> WARNING: Could not read dicom file! Skipping folder %s" % (folder)
            continue

        c += 1
        if first:
            first = False
            time = getDicomTime(d)
            print >> r, "Report for %s scanned on %s\n" % (getID(d), time)
            if verbose:
                print "\n\nProcessing images from %s scanned on %s\n" % (getID(d), time)

            # --- setup session.txt file

            print >> stxt, "id:", getID(d)
            print >> stxt, "subject:", getID(d)
            print >> stxt, "dicom:", os.path.abspath(os.path.join(base, 'dicom'))
            print >> stxt, "raw_data:", os.path.abspath(os.path.join(base, 'nii'))
            print >> stxt, "data:", os.path.abspath(os.path.join(base, '4dfp'))
            print >> stxt, "hcp:", os.path.abspath(os.path.join(base, 'hcp'))
            print >> stxt, ""

        try:
            seriesDescription = d.SeriesDescription
        except:
            try:
                seriesDescription = d.ProtocolName
            except:
                seriesDescription = "None"

        try:
            time = datetime.datetime.strptime(d.ContentTime[0:6], "%H%M%S").strftime("%H:%M:%S")
        except:
            try:
                time = datetime.datetime.strptime(d.StudyTime[0:6], "%H%M%S").strftime("%H:%M:%S")
            except:
                time = ""

        TR, TE = getTRTE(d)

        try:
            nslices = d[0x2001, 0x1018].value
        except:
            nslices = 0

        recenter, dofz2zf, fz, reorder = False, False, "", False
        try:
            if d.Manufacturer == 'Philips Medical Systems' and int(d[0x2001, 0x1081].value) > 1:
                dofz2zf, fz = True, "  (switched fz)"
            if d.Manufacturer == 'Philips Medical Systems' and d.SpacingBetweenSlices in [0.7, 0.8]:
                recenter, fz = d.SpacingBetweenSlices, "  (recentered)"
            # if d.Manufacturer == 'SIEMENS' and d.InstitutionName == 'Univerisity North Carolina' and d.AcquisitionMatrix == [0, 64, 64, 0]:
            #    reorder, fz = True, " (reordered slices)"
        except:
            pass

        # --- Special nii naming for Philips

        niinum = c
        try:
            if d.Manufacturer == 'Philips Medical Systems':
                niinum = (d.SeriesNumber - 1) / 100
        except:
            pass

        try:
            nframes = d[0x2001, 0x1081].value
            logs.append("%4d  %4d %40s   %3d   [TR %7.2f, TE %6.2f]   %s   %s%s" % (niinum, d.SeriesNumber, seriesDescription, nframes, TR, TE, getID(d), time, fz))
            reps.append("---> %4d  %4d %40s   %3d   [TR %7.2f, TE %6.2f]   %s   %s%s" % (niinum, d.SeriesNumber, seriesDescription, nframes, TR, TE, getID(d), time, fz))
        except:
            nframes = 0
            logs.append("%4d  %4d %40s  [TR %7.2f, TE %6.2f]   %s   %s%s" % (niinum, d.SeriesNumber, seriesDescription, TR, TE, getID(d), time, fz))
            reps.append("---> %4d  %4d %40s   [TR %7.2f, TE %6.2f]   %s   %s%s" % (niinum, d.SeriesNumber, seriesDescription, TR, TE, getID(d), time, fz))

        if niinum > 0:
            print >> stxt, "%4d: %s" % (niinum, seriesDescription)

        niiid = str(niinum)
        calls.append({'name': 'dcm2nii: ' + niiid, 'args': ['dcm2nii', '-c', '-v', folder], 'sout': os.path.join(os.path.split(folder)[0], 'dcm2nii_' + niiid + '.log')})
        files.append([niinum, folder, dofz2zf, recenter, fz, reorder, nframes, nslices])
        # subprocess.call(call, shell=True, stdout=null, stderr=null)

    #done = core.runExternalParallel(calls, cores=parelements, prepend=' ... ')

    for niinum, folder, dofz2zf, recenter, fz, reorder, nframes, nslices in files:

        print >> r, logs.pop(0),
        if verbose:
            print reps.pop(0),
            if debug:
                print ""

        tfname = False
        imgs = glob.glob(os.path.join(folder, "*.nii*"))
        if debug:
            print "     --> found nifti files: %s" % ("\n                            ".join(imgs))
        for image in imgs:
            if not os.path.exists(image):
                continue
            if debug:
                print "     --> processing: %s [%s]" % (image, os.path.basename(image))
            if image[-3:] == 'nii':
                if debug:
                    print "     --> gzipping: %s" % (image)
                subprocess.call("gzip " + image, shell=True, stdout=null, stderr=null)
                image += '.gz'
            if os.path.basename(image)[0:2] == 'co':
                # os.rename(image, os.path.join(imgf, "%02d-co.nii.gz" % (c)))
                if debug:
                    print "         ... removing: %s" % (image)
                os.remove(image)
            elif os.path.basename(image)[0:1] == 'o':
                if recenter:
                    if debug:
                        print "         ... recentering: %s" % (image)
                    tfname = os.path.join(imgf, "%02d-o.nii.gz" % (niinum))
                    timg = qxi.qximg(image)
                    if recenter == 0.7:
                        timg.hdrnifti.modifyHeader("srow_x:[0.7,0.0,0.0,-84.0];srow_y:[0.0,0.7,0.0,-112.0];srow_z:[0.0,0.0,0.7,-126];quatern_b:0;quatern_c:0;quatern_d:0;qoffset_x:-84.0;qoffset_y:-112.0;qoffset_z:-126.0")
                    elif recenter == 0.8:
                        timg.hdrnifti.modifyHeader("srow_x:[0.8,0.0,0.0,-94.8];srow_y:[0.0,0.8,0.0,-128.0];srow_z:[0.0,0.0,0.8,-130];quatern_b:0;quatern_c:0;quatern_d:0;qoffset_x:-94.8;qoffset_y:-128.0;qoffset_z:-130.0")
                    if debug:
                        print "         saving to: %s" % (tfname)
                    timg.saveimage(tfname)
                    if debug:
                        print "         removing: %s" % (image)
                    os.remove(image)
                else:
                    tfname = os.path.join(imgf, "%02d-o.nii.gz" % (niinum))
                    if debug:
                        print "         ... moving '%s' to '%s'" % (image, tfname)
                    os.rename(image, tfname)

                # -- remove original
                noob = os.path.join(folder, os.path.basename(image)[1:])
                noot = os.path.join(imgf, "%02d.nii.gz" % (niinum))
                if os.path.exists(noob):
                    if debug:
                        print "         ... removing '%s' [noob]" % (noob)
                    os.remove(noob)
                elif os.path.exists(noot):
                    if debug:
                        print "         ... removing '%s' [noot]" % (noot)
                    os.remove(noot)
            else:
                tfname = os.path.join(imgf, "%02d.nii.gz" % (niinum))
                if debug:
                    print "         ... moving '%s' to '%s'" % (image, tfname)
                os.rename(image, tfname)

            # --- check also for .bval and .bvec files

            for dwiextra in ['.bval', '.bvec']:
                dwisrc = image.replace('.nii.gz', dwiextra)
                if os.path.exists(dwisrc):
                    os.rename(dwisrc, os.path.join(imgf, "%02d%s" % (niinum, dwiextra)))


        # --- check if resulting nifti is present

        if len(imgs) == 0:
            print >> r, " WARNING: no NIfTI file created!"
            if verbose:
                print " WARNING: no NIfTI file created!"
            continue
        else:
            print >>r, ""
            print ""


        # --- flip z and t dimension if needed

        if dofz2zf:
            nifti.fz2zf(os.path.join(imgf, "%02d.nii.gz" % (niinum)))


        # --- reorder slices if needed

        if reorder:
            # nifti.reorder(os.path.join(imgf,"%02d.nii.gz" % (niinum)))
            timgf = os.path.join(imgf, "%02d.nii.gz" % (niinum))
            timg  = qxi.qximg(timgf)
            timg.data = timg.data[:, ::-1, ...]
            timg.hdrnifti.modifyHeader("srow_x:[-3.4,0.0,0.0,-108.5];srow_y:[0.0,3.4,0.0,-102.0];srow_z:[0.0,0.0,5.0,-63.0];quatern_b:0;quatern_c:0;quatern_d:0;qoffset_x:108.5;qoffset_y:-102.0;qoffset_z:-63.0")
            timg.saveimage(timgf)

        # --- check final geometry

        if tfname:
            hdr = gi.niftihdr(tfname)

            if hdr.sizez > hdr.sizey:
                print >> r, "     WARNING: unusual geometry of the NIfTI file: %d %d %d %d [xyzf]" % (hdr.sizex, hdr.sizey, hdr.sizez, hdr.frames)
                if verbose:
                    print "     WARNING: unusual geometry of the NIfTI file: %d %d %d %d [xyzf]" % (hdr.sizex, hdr.sizey, hdr.sizez, hdr.frames)

            if nframes > 1:
                if hdr.frames != nframes:
                    print >> r, "     WARNING: number of frames in nii does not match dicom information: %d vs. %d frames" % (hdr.frames, nframes)
                    if verbose:
                        print "     WARNING: number of frames in nii does not match dicom information: %d vs. %d frames" % (hdr.frames, nframes)
                    if nslices > 0:
                        gframes = int(hdr.sizez / nslices)
                        if gframes > 1:
                            print >> r, "     WARNING: reslicing image to %d slices and %d good frames" % (nslices, gframes)
                            if verbose:
                                print "     WARNING: reslicing image to %d slices and %d good frames" % (nslices, gframes)
                            nifti.reslice(tfname, nslices)
                        else:
                            print >> r, "     WARNING: not enough slices (%d) to make a complete volume." % (hdr.sizez)
                            if verbose:
                                print "     WARNING: not enough slices (%d) to make a complete volume." % (hdr.sizez)
                    else:
                        print >> r, "     WARNING: no slice number information, use qunex reslice manually to correct %s" % (tfname)
                        if verbose:
                            print "     WARNING: no slice number information, use qunex reslice manually to correct %s" % (tfname)

    if verbose:
        print "... done!"

    r.close()
    stxt.close()

    # gzip files

    if gzip == 'ask':
        print "\nTo save space, original DICOM files can be compressed."
        gzip = raw_input("\nDo you want to gzip DICOM files? [no] > ")
    if gzip == "yes":
        if verbose:
            print "\nCompressing dicom files in folders:"
        for folder in folders:
            if verbose:
                print "--->", folder
            subprocess.call("gzip " + os.path.join(folder, "*.dcm"), shell=True, stdout=null, stderr=null)

    return


def dicom2niix(folder='.', clean='ask', unzip='ask', gzip='ask', sessionid=None, verbose=True, parelements=1, debug=False, tool='auto', options=""):
    """
    ``dicom2niix [folder=.] [clean=ask] [unzip=ask] [gzip=ask] [sessionid=None] [verbose=True] [parelements=1] [tool='auto'] [options=""]``

    Converts MR images from DICOM and PAR/REC files to NIfTI format.

    INPUTS
    ======

    --folder           The base session folder with the dicom subfolder that
                       holds session numbered folders with dicom files. [.]

    --clean            Whether to remove preexisting NIfTI files (yes), leave
                       them and abort (no) or ask interactively (ask). [ask]

    --unzip            If the dicom files are gziped whether to unzip them
                       (yes), leave them be and abort (no) or ask interactively 
                       (ask). [ask]

    --gzip             After the dicom files were processed whether to gzip them
                       (yes), leave them ungzipped (no) or ask interactively
                       (ask). [ask]

    --sessionid        The id code to use for this session. If not provided, the
                       session id is extracted from dicom files.

    --verbose          Whether to be report on the progress (True) or not
                       (False). [True]

    --parelements      How many parallel processes to run dcm2nii conversion
                       with. The number is one by defaults, if specified as
                       'all', all available resources are utilized.

    --tool             What tool to use for the conversion [auto]. It can be
                       one of:

                       - auto (determine best tool based on heuristics)
                       - dcm2niix
                       - dcm2nii
                       - dicm2nii

    --options           A pipe separated string that lists additional options as
                        a "<key1>:<value1>|<key2>:<value2>" pairs to be used
                        when processing dicom or PAR/REC files. Currently it
                        supports:

                        - addImageType (Adds image type information to the
                          sequence name (Siemens scanners). The value should 
                          specify how many of the last image type labels to add.
                          [0])
                        - addJSONInfo (What sequence information to extract from
                          JSON sidecar files and add to session.txt file.
                          Specify a comma separated list of fields or 'all'.
                          See list in session.txt file description below. [])

    OUTPUTS
    =======

    After running, the command will place all the generated NIfTI files into the
    nii subfolder, named with sequential image number. It will also generate two
    additional files: a session.txt file and a DICOM-Report.txt file.

    session.txt file
    ----------------

    The session.txt will be placed in the session base folder. It will contain
    the information about the session id, subject id, location of folders and a 
    list of created NIfTI images with their description.

    Subject id will be extracted from the session id assuming the session id
    formula: `<subject id>_<session id>`. If there is no underscore in the 
    session id, the subject id is assumed to equal session id.
    
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

    For each of the listed images there will be a corresponding NIfTI file in
    the nii subfolder (e.g. 7.nii.gz for the first BOLD sequence), if a NIfTI
    file could be generated (Survey images for instance don't convert). The
    generated session.txt files form the basis for the following HCP and other
    processing steps.

    The following information can be extracted from sidecar JSON files and added
    to the sequence information in session.txt file::
    
        :<fieldname>:       <JSON key>
        :TR:                RepetitionTime
        :PEDirection:       PhaseEncodingDirection
        :EchoSpacing:       EffectiveEchoSpacing
        :DwellTime:         DwellTime
        :ReadoutDirection:  ReadoutDirection

    DICOM-Report.txt file
    ---------------------

    The DICOM-Report.txt file will be created and placed in the session's dicom
    subfolder. The file will list the images it found, the information about
    their original sequence number and the resulting NIfTI file number, the name
    of the sequence, the number of frames, TR and TE values, session id, time of
    acquisition, information and warnings about any additional processing it had
    to perform (e.g. recenter structural images, switch f and z dimensions,
    reslice due to premature end of recording, etc.). In some cases some of the
    information (number of frames, TE, TR) might not be reported if that
    information was not present or couldn't be found in the DICOM file.

    log files
    ---------

    For each image conversion attempt a dcm2nii_[N] (or dicm2nii_[N].log) file
    will be created that holds the output of the command that was run to convert 
    the DICOM or PAR/REC files to a NIfTI image.

    USE
    ===

    The command is used to convert MR images from DICOM and PAR/REC files to
    NIfTI format. It searches for images within the a dicom subfolder within the
    provided session folder (folder). It expects to find each image within a
    separate subfolder. It then converts the found images to NIfTI format and
    places them in the nii folder within the session folder. To reduce the space
    used it can then gzip the dicom or .REC files (gzip). The tool to be used 
    for the conversion can be specified explicitly or determined automatically.
    It can be one of 'dcm2niix', 'dcm2nii', 'dicm2nii' or 'auto'. If set to 
    'auto', for dicom files the conversion is done using dcm2niix, and for 
    PAR/REC files, dicm2nii is used if QuNex is set to use Matlab, otherwise 
    also PAR/REC files are converted using dcm2niix. If set explicitly, the 
    command will try to use the tool specified. To speed the process up, the 
    command can run it can run multiple conversion processes in parallel. The 
    number of processes to run in parallel is specified using the parelements
    parameter.

    Before running, the command check for presence of existing NIfTI files. The
    behavior when finding them is defined by clean parameter. If set to 'ask',
    it will ask interactively, what to do. If set to 'yes' it will remove any
    existing files and proceede. If set to 'no' it will leave them and abort.

    Before running, the command also checks whether DICOM or .REC files might be
    gzipped. If that is the case, the response depends on the setting of the
    unzip parameter. If set to 'yes' it will automatically gunzip them and
    continue. If set to 'no', it will leave them be and abort. If set to 'ask',
    it will ask interactively, what to do.

    Multiple sessions and scheduling
    --------------------------------

    The command can be run for multiple sessions by specifying `sessions` and
    optionally `sessionsfolder` and `parelements` parameters. In this case the
    command will be run for each of the specified sessions in the sessionsfolder
    (current directory by default). Optional `filter` and `sessionids` parameters
    can be used to filter sessions or limit them to just specified id codes.
    (for more information see online documentation). `sfolder` will be filled in
    automatically as each sessions's folder. Commands will run in parallel by
    utilizing the specified number of parelements (1 by default).

    If `scheduler` parameter is set, the command will be run using the specified
    scheduler settings (see `qunex ?schedule` for more information). If set in
    combination with `sessions` parameter, sessions will be processed over
    multiple nodes, `core` parameter specifying how many sessions to run per
    node. Optional `scheduler_environment`, `scheduler_workdir`,
    `scheduler_sleep`, and `nprocess` parameters can be set.

    Set optional `logfolder` parameter to specify where the processing logs
    should be stored. Otherwise the processor will make best guess, where the
    logs should go.

    EXAMPLE USE
    ===========

    ::

        qunex dicom2nii folder=. clean=yes unzip=yes gzip=yes parelements=3
    
    
    Multiple sessions example::

        qunex dicom2niix \\
          --sessionsfolder="/data/my_study/sessions" \\
          --sessions="OP*" \\
          --clean=yes \\
          --unzip=yes \\
          --gzip=no \\
          --parelements=3
    """

    print "Running dicom2niix\n=================="

    if sessionid and sessionid.lower() == 'none':
        sessionid = None

    base = folder
    null = open(os.devnull, 'w')
    dmcf = os.path.join(folder, 'dicom')
    imgf = os.path.join(folder, 'nii')

    # check options

    optionstr = options
    options = {'addImageType': '0', 'addJSONInfo': []}

    if optionstr:
        try:
            for k, v in [e.split(':') for e in optionstr.split('|')]:
                k, v = k.strip(), v.strip()
                if k in options and type(options[k]) is list:
                    options[k] = [e.strip() for e in v.split(',')]
                else:
                    options[k] = v
        except:
            raise ge.CommandError('dicom2niix', "Misspecified options string", "The options string is not valid! [%s]" % (optionstr), "Please check command instructions!")

    try:
        options['addImageType'] = int(options['addImageType'])
    except:
        raise ge.CommandError('dicom2niix', "Misspecified addImageType option", "The addImageType option value could not be converted to integer! [%s]" % (options['addImageType']), "Please check command instructions!")

    # check tool setting

    if tool not in ['auto', 'dcm2niix', 'dcm2nii', 'dicm2nii']:
        raise ge.CommandError('dicom2niix', "Incorrect tool specified", "The tool specified for conversion to nifti (%s) is not valid!" % (tool), "Please use one of dcm2niix, dcm2nii, dicm2nii or auto!")

    # check if dicom folder existis

    if not os.path.exists(dmcf):
        raise ge.CommandFailed("dicom2niix", "No existing dicom folder", "Dicom folder with sorted dicom files does not exist at the expected location:", "[%s]." % (dmcf), "Please check your data!", "If inbox folder with dicom files exist, you first need to use sort_dicom command!")

    # check for existing .gz files

    prior = []
    for tfolder in [imgf, dmcf]:
        for ext in ['*.nii.gz', '*.bval', '*.bvec', '*.json']:
            prior += glob.glob(os.path.join(tfolder, ext))

    if len(prior) > 0:
        if clean == 'ask':
            print "\nWARNING: The following files already exist:"
            for p in prior:
                print p
            clean = raw_input("\nDo you want to delete the existing NIfTI files? [no] > ")
        if clean == "yes":
            print "\nDeleting preexisting files:"
            for p in prior:
                print "---> ", p
                os.remove(p)
            print ""
        else:
            raise ge.CommandFailed("dicom2niix", "Existing NIfTI files", "Please remove existing NIfTI files or run the command with 'clean' set to 'yes'.", "Aborting processing of DICOM files!")

    # gzipped files

    gzipped = glob.glob(os.path.join(dmcf, "*", "*.dcm.gz"))
    if len(gzipped) > 0:
        if unzip == 'ask':
            print "\nWARNING: DICOM files have been compressed using gzip."
            unzip = raw_input("\nDo you want to unzip the existing files? [no] > ")
        if unzip == "yes":
            if verbose:
                print "\nUnzipping files (this might take a while)"
            calls = []
            gpath = os.path.join(os.path.abspath(dmcf), "*", "*.dcm.gz")
            gpath = gpath.replace(" ", "\\ ")
            calls.append({'name': 'gunzip: ' + dmcf, 'args': 'gunzip %s' % (gpath), 'sout': None, 'shell': True})
            core.runExternalParallel(calls, cores=parelements, prepend="---> ")
        else:
            raise ge.CommandFailed("dicom2niix", "Gzipped DICOM files", "Can not work with gzipped DICOM files, please unzip them or run with 'unzip' set to 'yes'.", "Aborting processing of DICOM files!")

    # --- open report files

    r    = open(os.path.join(dmcf, "DICOM-Report.txt"), 'w')
    stxt = open(os.path.join(folder, "session.txt"), 'w')

    # get a list of folders

    folders = [e for e in os.listdir(dmcf) if os.path.isdir(os.path.join(dmcf, e))]
    folders = [int(e) for e in folders if e.isdigit()]
    folders.sort()
    folders = [os.path.join(dmcf, str(e)) for e in folders]

    if not os.path.exists(imgf):
        os.makedirs(imgf)

    first = True
    setdi = True
    c     = 0
    calls = []
    logs  = []
    reps  = []
    files = []

    print "---> Analyzing data"

    for folder in folders:
        par = glob.glob(os.path.join(folder, "*.PAR"))
        if par:
            par = par[0]
            info = readPARInfo(par)
        else:
            try:
                info = readDICOMInfo(glob.glob(os.path.join(folder, "*.dcm"))[-1])
                if info['volumes'] == 0:
                    da, db, ta, tb = 0, 0, 0, 0
                    try:
                        da = info['dicom'][0x0020, 0x0012].value
                    except:
                        try: 
                            db = info['dicom'][0x0020, 0x0013].value 
                        except:
                            pass
                    if da > 0:
                        ta, tb = 0x0020, 0x0012
                    elif db > 0:
                        ta, tb = 0x0020, 0x0013

                    if ta > 0:
                        for dfile in glob.glob(os.path.join(folder, "*.dcm")):
                            tinfo = readDICOMInfo(dfile)                            
                            info['volumes'] = max(tinfo['dicom'][ta, tb].value, info['volumes'])

                    info['frames']     = info['volumes']
                    info['directions'] = info['volumes']
            except:
                print >> r, "# WARNING: Could not read dicom file! Skipping folder %s" % (folder)
                print "===> WARNING: Could not read dicom file! Skipping folder %s" % (folder)
                continue

        if options['addImageType'] > 0:
            retain = min(len(info['ImageType']), options['addImageType'])
            if retain > 0:
                imageType = " ".join(info['ImageType'][-retain:])
                if len(imageType) > 0:
                    info['seriesDescription'] += ' ' + imageType

        c += 1
        if first:
            first = False
            if sessionid is None:
                sessionid = info['sessionid']

            if '_' in sessionid:
                subjectid = sessionid.split('_')[0]
            else:
                subjectid = sessionid

            print >> r, "Report for %s (%s) scanned on %s\n" % (sessionid, info['sessionid'], info['datetime'])
            if verbose:
                print "\nProcessing images from %s (%s) scanned on %s" % (sessionid, info['sessionid'], info['datetime'])

            # --- setup session.txt file

            print >> stxt, "id:", sessionid
            print >> stxt, "subject:", subjectid
            print >> stxt, "dicom:", os.path.abspath(os.path.join(base, 'dicom'))
            print >> stxt, "raw_data:", os.path.abspath(os.path.join(base, 'nii'))
            print >> stxt, "data:", os.path.abspath(os.path.join(base, '4dfp'))
            print >> stxt, "hcp:", os.path.abspath(os.path.join(base, 'hcp'))
            print >> stxt, ""

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

        if info['seriesNumber']:
            niinum = info['seriesNumber'] * 10            
        else:
            niinum = c * 10

        info['niinum'] = niinum

        logs.append("%(niinum)4d  %(seriesNumber)4d %(seriesDescription)40s   %(volumes)4d   [TR %(TR)7.2f, TE %(TE)6.2f]   %(sessionid)s   %(datetime)s" % (info))
        reps.append("---> %(niinum)4d  %(seriesNumber)4d %(seriesDescription)40s   %(volumes)4d   [TR %(TR)7.2f, TE %(TE)6.2f]   %(sessionid)s   %(datetime)s" % (info))

        niiid = str(niinum)

        if tool == 'auto':
            if par:
                utool = 'dicm2nii'
                print '---> Using dicm2nii for conversion of PAR/REC to NIfTI if Matlab is available. [%s: %s]' % (niiid, info['seriesDescription'])
            else:
                utool = 'dcm2niix'
                print '---> Using dcm2niix for conversion to NIfTI. [%s: %s]' % (niiid, info['seriesDescription'])
        else:
            utool = tool

        if utool == 'dicm2nii':            
            if 'matlab' in mcommand:
                if setdi:
                    print '---> Setting up dicm2nii settings ...'
                    subprocess.call("matlab -nodisplay -r \"setpref('dicm2nii_gui_para', 'save_patientName', true); setpref('dicm2nii_gui_para', 'save_json', true); setpref('dicm2nii_gui_para', 'use_parfor', true); setpref('dicm2nii_gui_para', 'use_seriesUID', true); setpref('dicm2nii_gui_para', 'lefthand', true); setpref('dicm2nii_gui_para', 'scale_16bit', false); exit\" ", shell=True, stdout=null, stderr=null)
                    print '     done!'
                    setdi = False
                calls.append({'name': 'dicm2nii: ' + niiid, 'args': mcommand.split(' ') + ["try dicm2nii('%s', '%s'); catch ME, general_report_crash(ME); exit(1), end; exit" % (folder, folder)], 'sout': os.path.join(os.path.split(folder)[0], 'dicm2nii_' + niiid + '.log')})                
            else:
                print '---> Using dcm2niix for conversion as Matlab is not available! [%s: %s]' % (niiid, info['seriesDescription'])
                calls.append({'name': 'dcm2niix: ' + niiid, 'args': ['dcm2niix', '-f', niiid, '-z', 'y', '-b', 'y', '-o', folder, par], 'sout': os.path.join(os.path.split(folder)[0], 'dcm2niix_' + niiid + '.log')})
        elif utool == 'dcm2nii':
            if par:
                calls.append({'name': 'dcm2nii: ' + niiid, 'args': ['dcm2nii', '-c', '-v', folder, par], 'sout': os.path.join(os.path.split(folder)[0], 'dcm2nii_' + niiid + '.log')})
            else:
                calls.append({'name': 'dcm2nii: ' + niiid, 'args': ['dcm2nii', '-c', '-v', folder], 'sout': os.path.join(os.path.split(folder)[0], 'dcm2nii_' + niiid + '.log')})
        else:
            if par:
                calls.append({'name': 'dcm2niix: ' + niiid, 'args': ['dcm2niix', '-f', niiid, '-z', 'y', '-b', 'y', '-o', folder, par], 'sout': os.path.join(os.path.split(folder)[0], 'dcm2niix_' + niiid + '.log')})
            else:
                calls.append({'name': 'dcm2niix: ' + niiid, 'args': ['dcm2niix', '-f', niiid, '-z', 'y', '-b', 'y', folder], 'sout': os.path.join(os.path.split(folder)[0], 'dcm2niix_' + niiid + '.log')})
        files.append([niinum, folder, info])

    if not calls:
        r.close()
        stxt.close()
        for cleanFile in [os.path.join(dmcf, "DICOM-Report.txt"), os.path.join(folder, "session.txt")]:
            if os.path.exists(cleanFile):
                os.remove(cleanFile)
        raise ge.CommandFailed("dicom2niix", "No source DICOM files", "No source DICOM files were found to process!", "Please check your data and paths!")

    core.runExternalParallel(calls, cores=parelements, prepend=' ... ')

    print "\nProcessed sequences:"
    for niinum, folder, info in files:

        print >> r, logs.pop(0),
        if verbose:
            print reps.pop(0),
            if debug:
                print ""

        tfname = False
        imgs = glob.glob(os.path.join(folder, "*.nii*"))
        imgs.sort()

        # --- check if resulting nifti is present

        nimg = len(imgs)
        if nimg == 0:
            print >> r, " WARNING: no NIfTI file created!"
            if verbose:
                print " WARNING: no NIfTI file created!"
            continue
        elif nimg > 9:
            print >> r, " WARNING: More than 9 images created from this sequence! Skipping. Please check conversion log!"
            if verbose:
                print " WARNING: More than 9 images created from this sequence! Skipping. Please check conversion log!"
            continue
        else:
            print >> r, ""
            print ""

            imgnum = 0

            if debug:
                print "     --> found %s nifti file(s): %s" % (nimg, "\n                            ".join(imgs))

            for image in imgs:
                if not os.path.exists(image):
                    continue                
                if debug:
                    print "     --> processing: %s [%s]" % (image, os.path.basename(image))
                if image.endswith(".nii"):
                    if debug:
                        print "     --> gzipping: %s" % (image)
                    subprocess.call("gzip " + image, shell=True, stdout=null, stderr=null)
                    image += '.gz'

                # --> compile the basename of the target file(s) for nii folder
                imgnum += 1
                imgname = os.path.basename(image)
                tbasename = "%d" % (niinum + imgnum)

                # --> extract any suffices to add to the session.txt
                suffix = ""
                if "_" in imgname:
                    suffix = " " +"_".join(imgname.replace('.nii.gz','').replace(info['fileid'], '').split('_')[1:])

                # --> generate the actual target file path and move the image
                tfname = os.path.join(imgf, "%s.nii.gz" % (tbasename))
                if debug:
                    print "         ... moving '%s' to '%s'" % (image, tfname)
                os.rename(image, tfname)

                # --> check for .bval and .bvec files
                for dwiextra in ['.bval', '.bvec']:
                    dwisrc = image.replace('.nii.gz', dwiextra)
                    if os.path.exists(dwisrc):
                        os.rename(dwisrc, os.path.join(imgf, "%s%s" % (tbasename, dwiextra)))

                # --> initialize JSON information
            
                jsoninfo = ""
                jinf = {}

                # --> check for .json files and extract info if present                

                for jsonextra in ['.json', '.JSON']:
                    jsonsrc = image.replace('.gz', '')
                    jsonsrc = jsonsrc.replace('.nii', '')
                    jsonsrc += jsonextra

                    if not os.path.exists(jsonsrc):
                        jsonfiles = glob.glob(os.path.join(folder, "*" + jsonextra))
                        if len(jsonfiles) == 1:
                            jsonsrc = jsonfiles[0]

                    if os.path.exists(jsonsrc):
                        try:
                            with open(jsonsrc, 'r') as f:                            
                                jinf = json.load(f)
                            os.rename(jsonsrc, tfname.replace('.nii.gz', '.json'))
                            jsonsrc = tfname.replace('.nii.gz', '.json')

                            if 'RepetitionTime' in jinf and ('TR' in options['addJSONInfo'] or 'all' in options['addJSONInfo']):
                                jsoninfo += ": TR(%s)" % (str(jinf['RepetitionTime']))
                            if 'PhaseEncodingDirection' in jinf and ('PEDirection' in options['addJSONInfo'] or 'all' in options['addJSONInfo']):
                                jsoninfo += ": PEDirection(%-2s)" % (jinf['PhaseEncodingDirection'])    
                            if 'EffectiveEchoSpacing' in jinf and ('EchoSpacing' in options['addJSONInfo'] or 'all' in options['addJSONInfo']):
                                jsoninfo += ": EchoSpacing(%s)" % (str(jinf['EffectiveEchoSpacing']))
                            if 'DwellTime' in jinf and ('DwellTime' in options['addJSONInfo'] or 'all' in options['addJSONInfo']):
                                jsoninfo += ": DwellTime(%s)" % (str(jinf['DwellTime']))
                            if 'ReadoutDirection' in jinf and ('ReadoutDirection' in options['addJSONInfo'] or 'all' in options['addJSONInfo']):
                                jsoninfo += ": ReadoutDirection(%-2s)" % (jinf['ReadoutDirection'])
                        except:
                            print >> r, "     WARNING: Could not parse the JSON file [%s]!" % (jsonsrc)
                            if verbose:
                                print "     WARNING: Could not parse the JSON file [%s]!" % (jsonsrc)

                # --> print the info to session.txt file

                numinfo = ""
                if nimg > 1:
                    numinfo = " [%d/%d]" % (imgnum, nimg)

                print >> stxt, "%-4s: %-25s %s" % (tbasename, info['seriesDescription'] + numinfo + suffix, jsoninfo)

                # --- check final geometry

                if tfname:
                    hdr = gi.niftihdr(tfname)

                    if hdr.sizez > hdr.sizey and hdr.sizex < 150 :
                        print >> r, "     WARNING: unusual geometry of the NIfTI file: %d %d %d %d [xyzf]" % (hdr.sizex, hdr.sizey, hdr.sizez, hdr.frames)
                        if verbose:
                            print "     WARNING: unusual geometry of the NIfTI file: %d %d %d %d [xyzf]" % (hdr.sizex, hdr.sizey, hdr.sizez, hdr.frames)

                    if info['volumes'] > 1:
                        if hdr.frames != info['volumes']:
                            print >> r, "     WARNING: number of frames in nii does not match dicom information: %d vs. %d frames" % (hdr.frames, info['volumes'])
                            if verbose:
                                print "     WARNING: number of frames in nii does not match dicom information: %d vs. %d frames" % (hdr.frames, info['volumes'])
                            if info['slices'] > 0:
                                gframes = int(hdr.sizez / info['slices'])
                                if gframes > 1:
                                    print >> r, "     WARNING: reslicing image to %d slices and %d good frames" % (info['slices'], gframes)
                                    if verbose:
                                        print "     WARNING: reslicing image to %d slices and %d good frames" % (info['slices'], gframes)
                                    nifti.reslice(tfname, info['slices'])
                                else:
                                    print >> r, "     WARNING: not enough slices (%d) to make a complete volume." % (hdr.sizez)
                                    if verbose:
                                        print "     WARNING: not enough slices (%d) to make a complete volume." % (hdr.sizez)
                            else:
                                print >> r, "     WARNING: no slice number information, use qunex reslice manually to correct %s" % (tfname)
                                if verbose:
                                    print "     WARNING: no slice number information, use qunex reslice manually to correct %s" % (tfname)

    r.close()
    stxt.close()

    # gzip files

    if gzip == 'ask':
        print "\nTo save space, original DICOM files can be compressed."
        gzip = raw_input("\nDo you want to gzip DICOM files? [no] > ")
    if gzip == "yes":
        if verbose:
            print "\nCompressing dicom files in folders:"
        calls = []
        for folder in folders:
            calls.append({'name': 'gzip: ' + folder, 'args': ['gzip'] + glob.glob(os.path.join(os.path.abspath(folder), "*.dcm")) + glob.glob(os.path.join(os.path.abspath(folder), "*.REC")), 'sout': None})
        core.runExternalParallel(calls, cores=parelements, prepend="---> ")

    return


def sort_dicom(folder=".", **kwargs):
    """
    ``sort_dicom [folder=.]``

    Sorts DICOM files.

    INPUTS
    ======

    --folder      The base session folder that contains the inbox subfolder with
                  the unsorted DICOM files.

    USE
    ===

    The command looks for the inbox subfolder in the specified session folder
    (folder) and checks for presence of DICOM or PAR/REC files in the inbox
    folder and its subfolders. It inspects the found files, creates a dicom
    folder and for each image a numbered subfolder. It then moves the found
    DICOM or PAR/REC files in the correct subfolders to prepare them for
    dicom2nii(x) processing. In the process it checks that PAR/REC extensions
    are uppercase and changes them if necessary. If log files are found, they
    are placed in a separate `log` subfolder.

    Multiple sessions and scheduling
    --------------------------------

    The command can be run for multiple sessions by specifying `sessions` and
    optionally `sessionsfolder` and `parelements` parameters. In this case the
    command will be run for each of the specified sessions in the sessionsfolder
    (current directory by default). Optional `filter` and `sessionids`
    parameters can be used to filter sessions or limit them to just specified id
    codes. (for more information see online documentation). `sfolder` will be 
    filled in automatically as each sessions's folder. Commands will run in 
    parallel by utilizing the specified number of parelements (1 by default).

    If `scheduler` parameter is set, the command will be run using the specified
    scheduler settings (see `qunex ?schedule` for more information). If set in
    combination with `sessions` parameter, sessions will be processed over
    multiple nodes, `core` parameter specifying how many sessions to run per
    node. Optional `scheduler_environment`, `scheduler_workdir`,
    `scheduler_sleep`, and `nprocess` parameters can be set.

    Set optional `logfolder` parameter to specify where the processing logs
    should be stored. Otherwise the processor will make best guess, where the
    logs should go.

    EXAMPLE USE
    ===========
    
    ::
        
        qunex sort_dicom folder=OP667

    Multiple sessions example::

        qunex sort_dicom \\
          --sessionsfolders="/data/my_study/sessions" \\
          --sessions="OP*"
    """

    # --- should we copy or move

    print "Running sort_dicom\n================="

    should_copy = kwargs.get('copy', False)
    if should_copy:
        from shutil import copy
        doFile = copy
    else:
        doFile = os.rename

    # --- establish target folder

    dcmf  = os.path.join(kwargs.get('out_dir', folder), 'dicom')

    # --- get list of files

    files = kwargs.get('files', None)
    if files is None:
        inbox = os.path.join(folder, 'inbox')
        if not os.path.exists(inbox):
            raise ge.CommandFailed("sort_dicom", "Inbox folder not found", "Please check your paths! [%s]" % (os.path.abspath(inbox)), "Aborting")
        files = glob.glob(os.path.join(inbox, "*"))
        if len(files):
            files = []
            for droot, _, dfiles in os.walk(inbox):
                for dfile in dfiles:
                    files.append(os.path.join(droot, dfile))
            print "---> Processing %d files from %s" % (len(files), inbox)
        else:
            raise ge.CommandFailed("sort_dicom", "No files found", "Please check the specified inbox folder! [%s]" % (os.path.abspath(inbox)), "Aborting")

    info = None
    for dcm in files:
        ext = dcm.split('.')[-1]
        if ext.lower() == 'par':
            info = readPARInfo(dcm)
        else:
            try:
                info = readDICOMInfo(dcm)
            except:
                pass                
        if info and info['sessionid']:
                print "---> Sorting dicoms for %s scanned on %s" % (info['sessionid'], info['datetime'])
                break

    if not os.path.exists(dcmf):
        os.makedirs(dcmf)
        print "---> Created a dicom superfolder"

    logFolder = os.path.join(dcmf, 'log')

    dcmn = 0

    for dcm in files:
        ext = dcm.split('.')[-1]

        if os.path.basename(dcm)[0:4] in ["XX_0", "PS_0"]:
            continue

        elif ext == 'log':
            if not os.path.exists(logFolder):
                os.makedirs(logFolder)
                print "---> Created log folder"
            doFile(dcm, os.path.join(logFolder, os.path.basename(dcm)))
            continue

        elif ext.lower() == 'par':
            info  = readPARInfo(dcm)

        else:
            try:
                info = readDICOMInfo(dcm)                
            except:
                continue

        if info['seriesNumber'] is None:
            print "---> Skipping file", dcm
            continue

        sqid = str(info['seriesNumber'] * 10)
        sqfl = os.path.join(dcmf, sqid)

        if not os.path.exists(sqfl):
            os.makedirs(sqfl)
            print "---> Created subfolder for sequence %s %s - %s" % (info['sessionid'], sqid, info['seriesDescription'])

        if ext.lower() == 'par':
            tgpar = os.path.join(sqfl, os.path.basename(dcm))
            tgpar = tgpar[:-3] + 'PAR'
            doFile(dcm, tgpar)

            if os.path.exists(dcm[:-3] + 'REC'):
                doFile(dcm[:-3] + 'REC', tgpar[:-3] + 'REC')
            elif os.path.exists(dcm[:-3] + 'rec'):
                doFile(dcm[:-3] + 'rec', tgpar[:-3] + 'REC')
            else:
                print "---> Warning %s does not exist!" % (dcm[:-3] + 'REC')

        else:

            # --- get info for dcm naming

            dcmn += 1
            if info['SOPInstanceUID']:
                sop = info['SOPInstanceUID']
            else:
                sop = "%010d" % (dcmn)

            # --- check if for some reason we are dealing with gzipped dicom files and add an extension when renaming

            if ext == "gz":
                dext = ".gz"
            else:
                dext = ""

            # --- do the deed

            tgf = os.path.join(sqfl, "%s-%s-%s.dcm%s" % (cleanName(info['sessionid']), sqid, sop, dext))
            doFile(dcm, tgf)

    print "---> Done"
    return 

def list_dicom(folder=None):
    """
    ``list_dicom [folder=inbox]``

    Inspects a folder for dicom files and prints a detailed reports of the
    results.

    INPUTS
    ======

    --folder      The folder to be inspected for the presence of the DICOM 
                  files. [inbox]

    USE
    ===

    The command inspects the folder (`folder`) for dicom files and prints a
    detailed report of the results. Specifically, for each dicom file it finds
    in the specified folder and its subfolders it will print:

    - location of the file
    - session id recorded in the dicom file
    - sequence number and name
    - date and time of acquisition

    Importantly, it can work with both regular and gzipped DICOM files.

    EXAMPLE USE
    ===========
    
    ::

        qunex list_dicom folder=OP269/dicom
    """

    if folder is None:
        folder = os.path.join(".", 'inbox')

    print "============================================\n\nListing dicoms from %s\n" % (folder)

    files = glob.glob(os.path.join(folder, "*"))
    files = files + glob.glob(os.path.join(folder, "*/*"))
    files = [e for e in files if os.path.isfile(e)]

    if not files:
        raise ge.CommandFailed("list_dicom", "No files found", "Please check the specified folder! [%s]" % (os.path.abspath(folder)), "Aborting")

    for dcm in files:
        try:
            d    = readDICOMBase(dcm)
            time = getDicomTime(d)
            try:
                print "---> %s - %-6s %6d - %-30s scanned on %s" % (dcm, getID(d), d.SeriesNumber, d.SeriesDescription, time)
            except:
                print "---> %s - %-6s %6d - %-30s scanned on %s" % (dcm, getID(d), d.SeriesNumber, d.ProtocolName, time)
        except:
            pass

    return


def split_dicom(folder=None):
    """
    ``split_dicom [folder=inbox]``

    Sorts out DICOM images from different sessions.

    INPUTS
    ======

    --folder      The folder that contains the DICOM files to be sorted out.

    USE
    ===

    The command is used when DICOM images from different sessions are mixed in
    the same folder and need to be sorted out. Specifically, the command
    inspects the specified folder (`folder`) and its subfolders for the presence
    of DICOM files. For each DICOM file it finds, it checks, what session id the
    file belongs to. In the specified folder it then creates a subfolder for
    each of the found sessions and moves all the DICOM files in the right
    sessions's subfolder.

    EXAMPLE USE
    ===========
    
    ::

        qunex split_dicom folder=dicommess
    """

    if folder is None:
        folder = os.path.join(".", 'inbox')

    print "============================================\n\nSorting dicoms from %s\n" % (folder)

    files = glob.glob(os.path.join(folder, "*"))
    files = files + glob.glob(os.path.join(folder, "*/*"))
    files = [e for e in files if os.path.isfile(e)]

    if not files:
        raise ge.CommandFailed("split_dicom", "No files found", "Please check the specified folder! [%s]" % (os.path.abspath(folder)), "Aborting")

    sessions = []

    for dcm in files:
        try:
            # d    = dicom.read_file(dcm, stop_before_pixels=True)
            d    = readDICOMBase(dcm)
            time = getDicomTime(d)
            sid  = getID(d)
            if sid not in sessions:
                sessions.append(sid)
                os.makedirs(os.path.join(folder, sid))
                print "===> creating subfolder for session %s" % (sid)
            print "---> %s - %-6s %6d - %-30s scanned on %s" % (dcm, sid, d.SeriesNumber, d.SeriesDescription, time)
            os.rename(dcm, os.path.join(folder, sid, os.path.basename(dcm)))
        except:
            pass

    return


def import_dicom(sessionsfolder=None, sessions=None, masterinbox=None, check="yes", pattern=None, nameformat=None, tool='auto', parelements=1, logfile=None, archive='move', options="", unzip='yes', gzip='yes', verbose='yes', overwrite='no'):
    """
    ``import_dicom [sessionsfolder=.] [sessions=""] [masterinbox=<sessionsfolder>/inbox/MR] [check=yes] [pattern="(?P<packet_name>.*?)(?:\.zip$|\.tar$|.tgz$|\.tar\..*$|$)"] [nameformat='(?P<subject_id>.*)'] [tool=auto] [parelements=1] [logfile=""] [archive=move] [options=""] [unzip="yes"] [gzip="yes"] [overwrite="no"] [verbose=yes]``

    Automatically processes packets with individual sessions's DICOM or PAR/REC
    files all the way to, and including, generation of NIfTI files.

    INPUTS
    ======

    --sessionsfolder      The base study sessions folder (e.g. WM44/sessions) 
                          where the inbox and individual session folders are. 
                          If not specified, the current working folder will be 
                          taken as the location of the sessionsfolder. [.]
    
    --sessions            A comma delimited string that lists the sessions to 
                          process. If master inbox folder is used, the parameter 
                          is optional and it can include regex patterns. In this 
                          case only those sessions identified by the pattern
                          that also match with any of the patterns in the 
                          sessions list will be processed. If `masterinbox` is 
                          set to none, the list specifies the session folders to
                          process, and it can include glob patterns. [""]
    
    --masterinbox         The master inbox folder with packages to process. By 
                          default masterinbox is in base study folder: 
                          <sessionsfolder>/inbox/MR. If the packages are
                          elsewhere the location can be specified here. If set 
                          to "none", the data is assumed to already exist in the
                          individual sessions folders.
                          [<sessionsfolder>/inbox/MR]
    
    --check               The type of check to perform when packages or session  
                          folders are identified. [yes] The possible values are:

                          - yes (ask for interactive confirmation to proceed)
                          - no (report and continue w/o additional checks)
                          - any (continue if any packages are ready to process
                            report error otherwise)

    --pattern             The regex pattern to use to find the packages and 
                          to extract the session id.
                          ["(?P<session_id>.*?)(?:\.zip$|\.tar$|\.tgz$|\.tar\..*$|$)"]

    --nameformat          The regex pattern to use to extract subject id and 
                          (optionally) the session name from the session or
                          packet name. ["(?P<subject_id>.*)"]

    --tool                What tool to use for the conversion [auto]. It can be 
                          one of:

                          - auto (determine best tool based on heuristics)
                          - dcm2niix
                          - dcm2nii
                          - dicm2nii

    --parelements         The number of parallel processes to use when running 
                          converting DICOM images to NIfTI files. If specified
                          as 'all', all avaliable resources will be utilized.
                          [1]

    --logfile             A string specifying the location of the log file and
                          the columns in which packetname, subject id and
                          session name information are stored. The string should
                          specify: ``"path:<path to the log file>|
                          packetname:<name of the packet extracted by the 
                          pattern>|subjectid:<the column with subjectid 
                          information>[|sessionid:<the column with sesion id 
                          information>]"``. [""]

    --archive             What to do with a processed package ['move']. Options 
                          are:

                          - move (move the package to the default archive 
                            folder)
                          - copy (copy the package to the default archive 
                            folder)
                          - leave (keep the package in the session or master 
                            inbox folder)
                          - delete (delete the package after it has been 
                            processed)
                      
                          In case of processing data from a sessions folder, the
                          `archive` parameter is only valid for compressed 
                          packages.
    
    --options             A pipe separated string that lists additional options 
                          as a 
                          "<key1>:<value1>|<key2>:<value2>" pairs to be used 
                          when processing dicom or PAR/REC files. Currently it 
                          supports:

                          - addImageType (Adds image type information to the 
                            sequence name (Siemens scanners). The value should 
                            specify how many of the last image type labels to 
                            add. [0])
                          - addJSONInfo (What sequence information to extract
                            from JSON sidecar files and add to session.txt file.
                            Specify a comma separated list of fields or 'all'.
                            See list in session.txt file description of 
                            dicom2niix inline help. [])

    --unzip               Whether to unzip individual DICOM files that are
                          gzipped. Valid options are 'yes', 'no', and 'ask'.
                          ['yes']

    --gzip                Whether to gzip individual DICOM files after they were
                          processed. Valid options are 'yes', 'no', 'ask'.
                          ['yes']

    --overwrite           Whether to remove existing data in the dicom and nii 
                          folders. ['no']

    --verbose             Whether to provide detailed report also of packets
                          that could not be identified and/or are not matched 
                          with log file. ['yes']

    USE
    ===

    The command is used to automatically process packets with individual
    sessions's DICOM or PAR/REC files all the way to, and including, generation
    of NIfTI files. Packet can be either a zip file, a tar archive or a folder 
    that contains DICOM or PAR/REC files.

    The command can import packets either from a dedicated masterinbox folder 
    and create the necessary session folders within `--sessionsfolder`, or it 
    can process the data already present in the session specific folders. 

    The next sections will describe the two use cases in more detail.

    Processing data from a dedicated masterinbox folder
    ---------------------------------------------------

    This is the default operation. In this case the `--masterinbox` parameter 
    has to provide a path to the folder with the incoming packets 
    (`<sessionsfolder>/inbox/MR` by default). The session id is identified by 
    the use of the `--pattern` parameter, and optionally the `--logfile` 
    parameter. The packages processed can be optionally further filtered by the 
    `--sessions` parameter, so that only the packages that match both with the 
    `--pattern` and `--sessions` list are processed.

    The command first looks into the provided master inbox folder 
    (`--masterinbox`; by default `<sessionsfolder>/inbox/MR`) and finds any 
    packets that match the specified regex pattern (`--pattern`). The 
    `--pattern` has to be prepared so that it returns a named group 'packet_name'. 
    The default pattern is::

        "(?P<packet_name>.*?)(?:\.zip$|\.tar$|\.tgz$|\.tar\..*$|$)"

    which will identify the initial part of the packet file- or foldername, (w/o 
    any extension that identifies a compressed package) as the packet name. 
    Specifically::

        OP386
        OP386.zip
        OP386.tar.gz

    will all be identified as packet names 'OP386'.

    Once all the packets have been found, if the `--sessions` parameter is 
    specified, only those packets for which the identified packet name matches 
    any of the sessions specified in the `--sessions` parameter will 
    be further processed. The entries in the `--sessions` list can be regular
    expressions, in which case all the packet names that match any of the 
    expressions will be processed.

    Next, the extracted packet name will be processed to extract subject id and 
    (optionally) session name. The extraction is specified by the 
    `--nameformat` parameter. Specifically, the parameter should be a 
    regular expression that returns a named group `subject_id` and (optionally)
    a named group `session_name`. This information will be used to identify the
    subject the data belongs to and (optionally) the specific session within 
    which the data were acquired. The default expression is::

        "(?P<subject_id>.*)"

    which will return the session id as the subject id, assuming that only a 
    single session was recorded. The following pattern::

        "(?P<subject_id>.*?)_(?P<session_name>.*)"

    Would take the section of the string before the first underscore as the
    subject id and the rest of the string as the session name. I.e.::

        OP386_MR_1

    would be parsed to::

        subject_id: OP386
        session_name: MR_1    

    The command then lists all the sessions to process along with the extracted 
    subject ids and session names. If the check parameter is set to 
    'yes', the command will ask whether to process the listed packets, if it is 
    set to 'no', it will just start processing them, if it is set to `any`, it 
    will start processing them but return an explicit error if no packets are 
    found. 

    For each packet found, the command will generate a new session folder. The
    name of the folder will take the form `<subject_id>_<session_name>`. If no
    session name is extracted then the name of the folder will be simply 
    `<subject_id>`. 

    Alternatively, a path to a log file can be provided with the information on
    which columns provide the following information:

    - packet_name (the extracted name of the packet)
    - subject_id (subject id of the packet)
    - session_name (session id of the packet)

    At least `packet_name` and `subject_id` have to be provided. If
    `session_name` is omitted, the command assumes there is only one session per
    subject. 

    The command will then copy, unzip or untar all the files in the packet 
    into an inbox folder created within the session folder. Once all the files 
    are extracted or copied, depending on the archive parameter, the packet is 
    then either moved or copied to the `study/sessions/archive/MR` folder, left
    as is, or deleted. If the archive folder does not yet exist, it is created.

    If a session folder with an inbox folder already exists, if the overwrite 
    parameter is set to yes, it will delete the contents of the dicom and nii
    folders and redo the import process. If the overwrite parameter is set to
    no, then the packet will not be processed so that existing data is not 
    changed. In this case either set the overwrite parameter to yes, or remove 
    or rename the exisiting folder(s) and rerun the command to process 
    those packet(s) as well. 

    Processing data from a session folder
    -------------------------------------

    If the `--masterinbox` parameter is set to "none", then the command assumes 
    that the incoming data has already been saved to each session folder within 
    the `--sessionsfolder`. In this case, the command will look into all folders 
    that match the list provided in the `--sessions` parameter and process the 
    data in that folder. Each entry in the list can be a glob pattern matching 
    with multitiple session folders.

    To correctly identify the subject id and session name, `--nameformat` 
    parameter will be used. Specifically, the parameter should be a regular 
    expression that returns a named group `subject_id` and (optionally)
    a named group `session_name`. This information will be used to identify the
    subject the data belongs to and (optionally) the specific session within 
    which the data were acquired. The default expression is::

        "(?P<subject_id>.*)"

    which will return the session id as the subject id, assuming that only a 
    single session was recorded. The following pattern::

        "(?P<subject_id>.*?)_(?P<session_name>.*)"

    Would take the section of the string before the first underscore as the
    subject id and the rest of the string as the session name. I.e.::

        OP386_MR_1

    would be parsed to::

        subject_id: OP386
        session_name: MR_1

    The folders found are expected to have the data stored in the inbox folder
    either as individual files or as a compressed package. If the latter is the
    case, the files will be extracted to the inbox folder. If any results—e.g.
    files in `dicom` or `nii` folders—already exists, if the overwrite parameter
    is set to no (the default) then the processing of the folder will be
    skipped. If the overwrite parmeter is set to yes, the existing data in dicom
    and nii folders will be removed and the processing will be redone.

    Further processing
    ------------------

    After the files have been copied or extracted to the inbox folder, a
    `sort_dicom` command is run on that folder and all the DICOM or PAR/REC files
    are sorted and moved to the dicom folder. After that is done, a conversion
    command is run to convert the DICOM images or PAR/REC files to the NIfTI
    format and move them to the nii folder. The specific tool to do the 
    conversion can be specified explicitly using the `--tool` parameter or left 
    for the command to decide if set to 'auto' or let to default. The DICOM or 
    PAR/REC files are preserved and gzipped to save space. To speed up the 
    conversion, the parelements parameter is passed to the `dicom2niix` command. 
    `session.txt` and `DICOM-Report.txt` files are created as well. Please, 
    check the help for `sort_dicom` and `dicom2niix` commands for the specifics.

    EXAMPLE USE
    ===========

    First the examples for processing packages from `masterinbox` folder.

    In the first example, we are assuming that the packages we want to process 
    are in the default folder (`<path_to_studyfolder>/sessions/inbox/MR`), 
    the file or folder names contain only the packet names to be used, and the 
    subject id is equal to the packet name. All packets found are to be
    processed, after the user gives a go-ahead to an interactive prompt::
    
        qunex import_dicom \
            --sessionsfolder="<path_to_studyfolder>/sessions"
    
    If the processing should continue automatically if packages to process were 
    found, then the command should be::
    
        qunex import_dicom \
            --sessionsfolder="<path_to_studyfolder>/sessions" \
            --check="any"
    
    If only package names starting with 'AP' or 'HQ' are to be processed then 
    the `sessions` parameter has to be added::
    
        qunex import_dicom \
            --sessionsfolder="<path_to_studyfolder>/sessions" \
            --sessions="AP.*,HQ.*" \
            --check="any"
    
    If the packages are named e.g. 'Yale-AP4983.zip' with the extension
    optional, then to extract the packet name and map it directly to subject id,
    the following `pattern` parameter needs to be added::
    
        qunex import_dicom \
            --sessionsfolder="<path_to_studyfolder>/sessions" \
            --pattern=".*?-(?P<packet_name>.*?)($|\..*$)" \
            --sessions="AP.*,HQ.*" \
            --check="any"
    
    If the session name can also be extracted and the files are in the format
    e.g. 'Yale-AP4876_Baseline.zip', then a `nameformat` parameter needs to be 
    added::
    
        qunex import_dicom \
            --sessionsfolder="<path_to_studyfolder>/sessions" \
            --pattern=".*?-(?P<packet_name>.*?)($|\..*$)" \
            --sessions="AP.*,HQ.*" \
            --nameformat="(?P<subject_id>.*?)_(?P<session_name>.*)" \
            --check="any"
    
    In this case, 'AP4876_Baseline' will be first extracted as a packet name and 
    then parsed into 'AP4876' subject id and 'Baseline' session name.
    
    If the files are named e.g. 'Yale-AP4983.zip' and a log file exists in which 
    the AP* or HQ* are mapped to a corresponding subject id and session names, 
    then the command is changed to::
    
        qunex import_dicom \
            --sessionsfolder="<path_to_studyfolder>/sessions" \
            --pattern=".*?-(?P<packet_name>.*?)($|\..*$)" \
            --sessions="AP.*,HQ.*" \
            --logfile="path:/studies/myStudy/info/scanning_sessions.csv|packet_name:1|subject_id:2|session_name:3" \
            --check="any"

    For the examples of processing data already present in the individual 
    session id folder, let's assume that we have the following files present, 
    with no other files in the sessions folders::
    
        /studies/myStudy/sessions/S001_baseline/inbox/AYXQ.tar.gz
        /studies/myStudy/sessions/S001_incentive/inbox/TWGS.tar.gz
        /studies/myStudy/sessions/S002_baseline/inbox/OHTZ.zip
        /studies/myStudy/sessions/S002_incentive/inbox/QRTD.zip
    
    Then these are a set of possible commands::
    
        qunex import_dicom \
            --sessionsfolder="/studies/myStudy/sessions" \
            --masterinbox="none" \
            --sessions="S*" 
    
    In the above case all the folders will be processed, the packages will be
    extracted and (by default) moved to `/studies/myStudy/sessions/archive/MR`::
    
        qunex import_dicom \
            --sessionsfolder="/studies/myStudy/sessions" \
            --masterinbox="none" \
            --sessions="*baseline" \
            --archive="delete"
    
    In the above case only the `S001_baseline` and `S002_baseline` sessions will
    be processed and the respective compressed packages will be deleted after
    the successful processing.
    """

    print "Running import_dicom\n===================="

    # check settings

    if tool not in ['auto', 'dcm2niix', 'dcm2nii', 'dicm2nii']:
        raise ge.CommandError('import_dicom', "Incorrect tool specified", "The tool specified for conversion to nifti (%s) is not valid!" % (tool), "Please use one of dcm2niix, dcm2nii, dicm2nii or auto!")

    verbose = verbose.lower() == 'yes'

    overwrite = overwrite.lower() == 'yes'

    if sessionsfolder is None:
        sessionsfolder = "."

    if masterinbox is None:
        masterinbox = os.path.join(sessionsfolder, 'inbox', 'MR')

    if masterinbox.lower() == 'none':
        masterinbox = None
        if sessions is None or sessions == "":
            raise ge.CommandError('import_dicom', "Sessions parameter not specified", "If `masterinbox` is set to 'none' the `sessions` has to list sessions to process!", "Please check your command!")

    if pattern is None:
        pattern = r"(?P<packet_name>.*?)(?:\.zip$|\.tar$|\.tgz$|\.tar\..*$|$)"

    if nameformat is None:
        nameformat = r"(?P<subject_id>.*)"

    igz = re.compile(r'.*\.gz')

    if sessions:
        sessions = re.split(', *', sessions)

    # ---- check acquisition log if present:

    sessionsInfo = None

    if logfile is not None and logfile != "":
        log = dict([[f.strip() for f in e.split(':')] for e in logfile.split('|')])

        if not all([e in log for e in ['path', 'subject_id', 'packet_name']]):
            raise ge.CommandFailed("import_dicom", "Missing information in logfile", "Please provide all information in the logfile specification! [%s]" % (logfile))

        try:
            for key in [e for e in log.keys() if e in ['packet_name', 'subject_id', 'session_name']]:
                log[key] = int(log[key]) - 1
        except:
            raise ge.CommandFailed("import_dicom", "Invalid logfile specification", "Please create a valid logfile specification! [%s]" % (logfile))

        sessionname = 'session_name' in log

        if not os.path.exists(log['path']):
            raise ge.CommandFailed("import_dicom", "Logfile does not exist", "The specified logfile does not exist:", log['path'], "Please check your paths!")

        print "---> Reading acquisition log [%s]." % (log['path'])
        sessionsInfo = {}
        with open(log['path']) as f:
            if log['path'].split('.')[-1] == 'csv':
                reader = csv.reader(f, delimiter=',')
            else:
                reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            for line in reader:
                try:
                    if sessionname:
                        sessionsInfo[line[log['packetname']]] = {'subjectid': line[log['subject_id']], 'sessionname': line[log['session_name']], 'sessionid': "%s_%s" % (line[log['subject_id']], line[log['session_name']]), 'packetname': line[log['packet_name']]}
                    else:
                        sessionsInfo[line[log['packetname']]] = {'subjectid': line[log['subject_id']], 'sessionname': None, 'sessionid': line[log['subject_id']], 'packetname': line[log['packet_name']]}
                except:
                    pass

    # ---- set up lists

    packets = {'ok': [], 'nolog': [], 'bad': [], 'exist': [], 'skip': [], 'invalid': []}
    emptysession = {'subjectid': None, 'sessionname': None, 'sessionid': None, 'packetname': None}

    # ---- get list of files / folders in masterinbox

    if masterinbox:

        reportSet = [('ok', '---> Found the following packets to process:'),
                     ('nolog', "---> These packets do not match with the log and they won't be processed"),
                     ('bad', "---> For these packets a packet name could not be identified and they won't be processed:"),
                     ('invalid', "---> For these packets the packet name could not parsed and they won't be processed:"),
                     ('exist', "---> The session and inbox folder for these packages already exist:"),
                     ('skip', "---> These packages do not match list of sessions and will be skipped:")]

        print "---> Checking for packets in %s \n     ... using regular expression '%s'\n     ... extracting subject id using regular expression '%s'" % (os.path.abspath(masterinbox), pattern, nameformat)

        files = glob.glob(os.path.join(masterinbox, '*'))
        try:
            getop = re.compile(pattern)
        except:
            raise ge.CommandFailed("import_dicom", "Invalid pattern", "Coud not parse the provided regular expression pattern: '%s'" % (pattern), "Please check and correct it!")
        try:
            getid = re.compile(nameformat)
        except:
            raise ge.CommandFailed("import_dicom", "Invalid nameformat", "Coud not parse the provided regular expression pattern: '%s'" % (nameformat), "Please check and correct it!")

        for file in files:
            m = getop.search(os.path.basename(file))
            if m:
                if 'packet_name' in m.groupdict() and m.group('packet_name'):
                    pname = m.group('packet_name')
                    session = dict(emptysession)
                    session['packetname'] = pname
                    
                    if sessionsInfo:                        
                        if pname in sessionsInfo:
                            session = dict(sessionsInfo[pname])
                        else:
                            packets['nolog'].append((file, dict(session)))
                            continue
                    else:
                        session = dict(emptysession)
                        session['packetname'] = pname

                        ms = getid.search(pname)

                        if ms and 'subject_id' in ms.groupdict() and ms.group('subject_id'):
                            sid = ms.group('subject_id')
                            if 'session_name' in ms.groupdict() and ms.group('session_name'):
                                session.update({'subjectid': ms.group('subject_id'), 'sessionname': ms.group('session_name'), 'sessionid': "%s_%s" % (ms.group('subject_id'), ms.group('session_name'))})
                            else:
                                session.update({'subjectid': ms.group('subject_id'), 'sessionname': None, 'sessionid': ms.group('subject_id')})

                        else:
                            packets['invalid'].append((file, session))
                            continue

                    sfolder = os.path.join(sessionsfolder, session['sessionid'])

                    if sessions:
                        if not any([matchAll(e, session['sessionid']) for e in sessions]):
                            packets['skip'].append((file, session))
                            continue

                    if os.path.exists(os.path.join(sfolder, 'inbox')):
                        packets['exist'].append((file, session))
                        continue

                    packets['ok'].append((file, session))

                else:
                    packets['bad'].append(file, dict(emptysession))


    # ---- get list of session folders to process

    else:

        if not sessions:
            raise ge.CommandFailed("import_dicom", "Input data not specified", "Neither masterinbox nor sessions to process were specified.", "Please check your command call!")

        reportSet = [('ok', '---> Found the following folders to process:'),
                     ('invalid', "---> For these folders the folder name could not parsed and they won't be processed:"),
                     ('exist', "---> These folders have existing results:")]

        print "---> Checking for folders to process in '%s'" % (os.path.abspath(sessionsfolder))

        getid = re.compile(nameformat)

        sfolders = []
        for sessionid in sessions:
            sfolders += glob.glob(os.path.join(sessionsfolder, sessionid))
        sfolders = list(set(sfolders))

        for sfolder in sfolders:
            session = dict(emptysession)
            pname = os.path.basename(sfolder)
            session['packetname'] = pname
            sid = pname.split('_')

            archives = []
            for tarchive in ['*.zip', '*.tar', '*.tar.*', '*.tgz']:
                archives += glob.glob(os.path.join(sfolder, 'inbox', tarchive))
            session['archives'] = list(archives)

            ms = getid.search(pname)
            if ms and 'subject_id' in ms.groupdict() and ms.group('subject_id'):
                sid = ms.group('subject_id')
                if 'session_name' in ms.groupdict() and ms.group('session_name'):
                    session.update({'subjectid': ms.group('subject_id'), 'sessionname': ms.group('session_name'), 'sessionid': pname})
                else:
                    session.update({'subjectid': ms.group('subject_id'), 'sessionname': None, 'sessionid': pname})

            else:
                packets['invalid'].append((sfolder, session))
                continue

            if glob.glob(os.path.join(sfolder, 'dicom')) or glob.glob(os.path.join(sfolder, 'nii')):
                packets['exist'].append((sfolder, session)) 
                continue                   

            packets['ok'].append((sfolder, session))



    # ---> Report

    for tag, message in reportSet:
        if packets[tag]:
            print "\n", message
            for file, session in packets[tag]:
                if session['sessionname']:
                    print "     subject: %s, session: %s ... %s <= %s <- %s" % (session['subjectid'], session['sessionname'], session['sessionid'], session['packetname'], os.path.basename(file))
                elif session['subjectid']:
                    print "     subject: %s ... %s <= %s <- %s" % (session['subjectid'], session['sessionid'], session['packetname'], os.path.basename(file))
                elif session['sessionid']:
                    print "     %s <= %s <- %s" % (session['sessionid'], session['packetname'], os.path.basename(file))
                elif session['packetname']:
                    print "     %s <= %s <- %s" % ("????", session['packetname'], os.path.basename(file))
                else:
                    print "     %s <= %s <- %s" % ("????", "????", os.path.basename(file))

            if tag == 'exist':
                #if overwrite:
                #    print "     ... The folders will be cleaned and replaced with new data"
                #else:
                #    print "     ... To process them, remove or rename the exisiting subject folders or set `overwrite` to 'yes'"
                print "     ... To process them, remove or rename the exisiting session folders"

    nToProcess = len(packets['ok'])
    if overwrite:
        nToProcess += len(packets['exist'])

    if nToProcess:
        if check.lower() == 'yes':
            s = raw_input("\n===> Should I proceeed with processing the listed packages [y/n]: ")
            if s != "y":
                print "---> Aborting operation!\n"
                return
    else:        
        if check.lower() == 'any':
            if masterinbox:
                raise ge.CommandFailed("import_dicom", "No packets found to process", "No packets were found to be processed in the master inbox [%s]!" % (os.path.abspath(masterinbox)), "Please check your data!")                
            else:
                raise ge.CommandFailed("import_dicom", "No sessions found to process", "No sessions were found to be processed in session folder [%s]!" % (os.path.abspath(sessionsfolder)), "Please check your data!")                
        else:
            if masterinbox:
                raise ge.CommandNull("import_dicom", "No packets found to process", "No packets were found to be processed in the master inbox [%s]!" % (os.path.abspath(masterinbox)))
            else:
                raise ge.CommandNull("import_dicom", "No sessions found to process", "No sessions were found to be processed in session folder [%s]!" % (os.path.abspath(sessionsfolder))) 
                

    # ---- Ok, now loop through the packets

    afolder = os.path.join(sessionsfolder, "archive", "MR")
    if not os.path.exists(afolder):
        os.makedirs(afolder)
        print "---> Created Archive folder for processed packages."

    report = {'failed': [], 'ok': []}

    # ---> clean existing data if needed

    if overwrite:
        if packets['exist']:
            print "---> Cleaning exisiting data in folders:"
            for file, session in packets['exist']:                
                sfolder = os.path.join(sessionsfolder, session['sessionid'])
                print "     ... %s" % (sfolder)
                if masterinbox:
                    ifolder = os.path.join(sfolder, 'inbox')
                    if os.path.exists(ifolder):
                        shutil.rmtree(ifolder)
                nfolder = os.path.join(sfolder, 'nii')
                dfolder = os.path.join(sfolder, 'dicom')
                for rmfolder in [nfolder, dfolder]:
                    if os.path.exists(rmfolder):
                        shutil.rmtree(rmfolder)
    
        packets['ok'] += packets['exist']

    # ---> process packets

    print "---> Starting to process %d packets ..." % (len(packets['ok']))

    for file, session in packets['ok']:
        note = []
        try:

            sfolder = os.path.join(sessionsfolder, session['sessionid'])
            ifolder = os.path.join(sfolder, 'inbox')
            dfolder = os.path.join(sfolder, 'dicom')

            # --- Big info

            print "\n\n---=== PROCESSING %s ===---\n" % (session['sessionid'])

            if masterinbox and not os.path.exists(ifolder):
                os.makedirs(ifolder)
                files = [file]
            else:
                if 'archives' in session and session['archives']:
                    files = session['archives']
                else:
                    files = [ifolder]

            for p in files:

            # --- unzip or copy the package

                if p.endswith('zip'):

                    ptype = "zip"

                    print "...  unzipping %s" % (os.path.basename(p))
                    dnum = 0
                    fnum = 0

                    try:
                        z = zipfile.ZipFile(p, 'r')
                    except:
                        e = sys.exc_info()[0]
                        raise ge.CommandFailed("import_dicom", "Zip file could not be processed", "Opening zip [%s] returned an error [%s]!" % (p, e), "Please check your data!")                

                    ilist = z.infolist()
                    for sf in ilist:
                        if sf.file_size > 0:

                            if fnum % 1000 == 0:
                                dnum += 1
                                if not os.path.exists(os.path.join(ifolder, str(dnum))):
                                    os.makedirs(os.path.join(ifolder, str(dnum)))
                            fnum += 1

                            print "...  extracting:", sf.filename, sf.file_size

                            fdata = z.read(sf)

                            # --- do we have par / rec / log

                            if sf.filename.split('.')[-1].lower() in ['par', 'rec', 'log']:
                                tfile = os.path.basename(sf.filename)
                                for ext in ['rec', 'par']:
                                    if tfile.split('.')[-1] == ext:
                                        tfile = tfile[:-3] + ext.upper()
                            else:
                                if igz.match(sf.filename):
                                    gzname = os.path.join(ifolder, str(dnum), str(fnum) + ".gz")
                                    fout = open(gzname, 'wb')
                                    fout.write(fdata)
                                    fout.close()
                                    fin = gzip.open(gzname, 'rb')
                                    fdata = fin.read()
                                    fin.close()
                                    os.remove(gzname)
                                tfile = str(fnum)
                            fout = open(os.path.join(ifolder, str(dnum), tfile), 'wb')
                            fout.write(fdata)
                            fout.close()

                    z.close()
                    print "     -> done!"

                elif re.search("\.tar$|\.tar.gz$|\.tar.bz2$|\.tarz$|\.tar.bzip2$|\.tgz$", p):

                    ptype = "tar"

                    print "...  untarring %s" % (os.path.basename(p))
                    dnum = 0
                    fnum = 0

                    tar = tarfile.open(p, 'r')
                    for tarinfo in tar:
                        if tarinfo.isfile():
                            if fnum % 1000 == 0:
                                dnum += 1
                                os.makedirs(os.path.join(ifolder, str(dnum)))
                            fnum += 1

                            print "...  extracting:", tarinfo.name, tarinfo.size

                            fdata = tar.extractfile(tarinfo)

                            # --- do we have par / rec / log

                            if tarinfo.name.split('.')[-1].lower() in ['par', 'rec', 'log']:
                                tfile = os.path.basename(tarinfo.name)
                                for ext in ['rec', 'par']:
                                    if tfile.split('.')[-1] == ext:
                                        tfile = tfile[:-3] + ext.upper()
                            else:
                                if igz.match(tarinfo.name):
                                    gzname = os.path.join(ifolder, str(dnum), str(fnum) + ".gz")
                                    fout = open(gzname, 'wb')
                                    fout.write(fdata)
                                    fout.close()
                                    fin = gzip.open(gzname, 'rb')
                                    fdata = fin.read()
                                    fin.close()
                                    os.remove(gzname)
                                tfile = str(fnum)

                            fout = open(os.path.join(ifolder, str(dnum), tfile), 'wb')
                            fout.write(fdata.read())
                            fout.close()

                    tar.close()
                    print "     -> done!"

                else:
                    ptype = "folder"
                    if masterinbox and ifolder != p:
                        if os.path.exists(ifolder):
                            shutil.rmtree(ifolder)
                        print "...  copying %s dicom files" % (os.path.basename(p))
                        shutil.copytree(p, ifolder)

            # ===> run sort dicom

            print
            sort_dicom(folder=sfolder)

            # ===> run dicom to nii

            print
            dicom2niix(folder=sfolder, clean='no', unzip=unzip, gzip=gzip, sessionid=session['sessionid'], tool=tool, parelements=parelements, options=options, verbose=True)

            # ===> archive

            if archive != 'leave':
                s = "Processing packages: " + archive
                print
                print s
                print "".join(['=' for e in range(len(s))])

            for p in files:
                if masterinbox or re.search("\.zip$|\.tar$|\.tar.gz$|\.tar.bz2$|\.tarz$|\.tar.bzip2$|\.tgz$", p):
                    archivetarget = os.path.join(afolder, os.path.basename(p))

                    # --- move package to archive
                    if archive == 'move':
                        if os.path.exists(archivetarget):
                            print "...  WARNING: %s already exists in archive and it will not be moved!" % (os.path.basename(p))
                            note.append("WARNING: %s already exists in archive and it was not moved!" % (os.path.basename(p)))
                        else:
                            print "...  moving %s to archive" % (os.path.basename(p))
                            shutil.move(p, archivetarget)
                            print "     -> done!"

                    # --- copy package to archive
                    elif archive == 'copy':
                        if os.path.exists(archivetarget):
                            print "...  WARNING: %s already exists in archive and it will not be copied!" % (os.path.basename(p))
                            note.append("WARNING: %s already exists in archive and it was not copied!" % (os.path.basename(p)))
                        else:
                            print "...  copying %s to archive" % (os.path.basename(p))
                            if ptype == 'folder':
                                shutil.copytree(p, archivetarget)
                            else:
                                shutil.copy2(p, afolder)
                            print "     -> done!"

                    # --- delete original package
                    elif archive == 'delete':
                        print "...  deleting packet [%s]" % (os.path.basename(p))
                        if ptype == 'folder':
                            shutil.rmtree(p)
                        else:
                            os.remove(p)

            report['ok'].append((file, dict(session), note))

        except ge.CommandFailed as e: 
            report['failed'].append((file, dict(session), ["%s: %s" % (e.function, e.error)]))

    print "\nFinal report\n============"

    if report["ok"]:
        print "\nSuccessfully processed:"
        for file, session, notes in report["ok"]:
            print "... %s [%s]" % (session['sessionid'], file)
            for note in notes:
                print "    %s" % (note)

    if report["failed"]:
        print "\nFailed to process:"
        for file, session, notes in report["failed"]:
            print "... %s [%s]" % (session['sessionid'], file)
            for note in notes:
                print "    %s" % (note)
        raise ge.CommandFailed("import_dicom", "Some packages failed to process", "Please check report!")

    return


def get_dicom_info(dicomfile=None, scanner='siemens'):
    """
    ``get_dicom_info dicomfile=<dicom_file> [scanner=siemens]``

    Inspects the specified DICOM file.

    INPUTS
    ======

    --dicomfile      The path to the DICOM file to be inspected.
    --scanner        The scanner on which the data was acquired, currently only
                     "siemens" and "philips" are supported. [siemens]

    USE
    ===

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

    EXAMPLE USE
    ===========

    ::

        qunex get_dicom_info dicomfile=ap308e727bxehd2.372.2342.42566.dcm
    """

    if dicomfile is None:
        raise ge.CommandError("get_dicom_info", "No path to the dicom file was provided")

    if not os.path.exists(dicomfile):
        raise ge.CommandFailed("get_dicom_info", "DICOM file does not exist", "Please check path! [%s]" % (dicomfile))

    if scanner not in ['siemens', 'philips']:
        raise ge.CommandError("get_dicom_info", "Scanner not supported", "The specified scanner is not yet supported! [%s]" % (scanner))

    d = readDICOMBase(dicomfile)
    ok = True

    print "\nHCP relevant information\n(dicom %s)\n" % (dicomfile)

    try:
        print "            Institution:", d[0x0008, 0x0080].value
    except:
        print "            Institution: undefined"

    try:
        print "                Scanner:", d[0x0008, 0x0070].value, d[0x0008, 0x1090].value
    except:
        print "                Scanner: undefined"

    try:
        print "Magnetic field strength:", d[0x0018, 0x0087].value
        tesla = float(d[0x0018, 0x0087].value)
    except:
        print "Magnetic field strength: unknown"
        tesla = None

    try:
        print "               Sequence:", d[0x0008, 0x103e].value
    except:
        print "               Sequence: undefined"

    try:
        print "             Session ID:", d[0x0010, 0x0020].value
    except:
        print "             Session ID: undefined"

    if scanner == 'siemens':
        try:
            print "         Sample spacing:", d[0x0019, 0x1018].value
        except:
            print "         Sample spacing: undefined"

        try:
            bw = d[0x0019, 0x1028].value
            print "               Bandwith:", bw
        except:
            print "               Bandwith: undefined"
            ok = False

        try:
            am = d[0x0051, 0x100b].value
            print "     Acquisition Matrix:", am
            am = float(am.split('*')[0].replace('p', ''))
        except:
            print "     Acquisition Matrix: undefined"
            ok = False

        if ok:
            dt = 1 / (bw * am)
            print "             Dwell Time:", dt
        else:
            print "             Dwell Time: Could not compute, data missing!"

        try:
            sinfo = d[0x0029, 0x1020].value
            sinfo = sinfo.split('\n')
            for l in sinfo:
                if 'sSliceArray.ucMode' in l:
                    for k, v in [('0x1', 'Sequential Ascending'), ('0x2', 'Sequential Ascending'), ('0x4', 'Interleaved')]:
                        if k in l:
                            print "Slice Acquisition Order: %s" % (v)
        except:
            print "Slice Acquisition Order: Unknown"

    # --- Philips data

    if scanner == 'philips':
        try:
            print "        Repetition Time: %.2f" % (float(d[0x0018, 0x0080].value))
        except:
            try:
                print "        Repetition Time:", d[0x2005, 0x1030].value[0]
            except:
                print "        Repetition Time: undefined"

        try:
            print "             Flip Angle:", d[0x2001, 0x1023].value
        except:
            print "             Flip Angle: undefined"

        try:
            print "       Number of Echoes:", d[0x2001, 0x1014].value
        except:
            print "       Number of Echoes: undefined"

        try:
            print "   Phase Encoding Steps:", d[0x0018, 0x0089].value
        except:
            print "   Phase Encoding Steps: undefined"

        try:
            print "      Echo Train Length:", d[0x0018, 0x0091].value
            etl = float(d[0x0018, 0x0091].value)
        except:
            print "      Echo Train Length: undefined"
            etl = None

        try:
            print "             EPI Factor:", d[0x2001, 0x1013].value
        except:
            print "             EPI Factor: undefined"

        try:
            print "        Water Fat Shift:", d[0x2001, 0x1022].value
            wfs = float(d[0x2001, 0x1022].value)
        except:
            print "        Water Fat Shift: undefined"
            wfs = None

        try:
            print "        Pixel Bandwidth:", d[0x0018, 0x0095].value
        except:
            print "        Pixel Bandwidth: undefined"

        try:
            print "   Acquisition Duration:", d[0x0018, 0x9073].value
        except:
            print "   Acquisition Duration: undefined"

        try:
            print "   Parallel Acquisition:", d[0x0018, 0x9077].value
            if d[0x0018, 0x9077].value == 'YES':
                try:
                    print "%23s: in plane: %.2f out of plane %.2f" % (d[0x0018, 0x9078].value, d[0x0018, 0x9168].value, d[0x0018, 0x9155].value)
                except:
                    print "                 Factor: undefined"
        except:
            print "   Parallel Acquisition: undefined"

        try:
            print "                 Matrix: [%d, %d, %d]" % (d[0x0028, 0x0010].value, d[0x0028, 0x0011].value, d[0x2001, 0x1018].value)
        except:
            print "                 Matrix: undefined"

        try:
            print "          Field of View: [%d, %d, %d]" % (d[0x2005, 0x1074].value, d[0x2005, 0x1076].value, d[0x2005, 0x1075].value)
        except:
            print "          Field of View: undefined"

        try:
            if tesla == 3:
                wfdiff    = 3.35
                resfreq   = 42.576
                dwelltime = 1 / ( tesla * wfdiff * resfreq / wfs * etl)
                print "   Parallel Acquisition: undefined"
                print "    Estimated dwelltime: %.8f" % (dwelltime)
        except:
            print "    Estimated dwelltime: unknown"

    # --- look for slice ordering info

    print
