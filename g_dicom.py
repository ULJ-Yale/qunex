#!/usr/bin/env python
# encoding: utf-8
"""
g_dicom.py

Functions for processing dicom images and converting them to NIfTI format:

* setupHCP        ... maps the data to a hcp folder
* setupHCPFolder  ... runs setupHCP for all subject folders
* getHCPReady     ... prepares subject.txt files for HCP mapping

The commands are accessible from the terminal using gmri utility.

Copyright (c) Grega Repovs. All rights reserved.
"""

# import dicom
import os
import re
import glob
import shutil
import datetime
import subprocess
import niutilities.g_NIfTI
import niutilities.g_gimg as gimg
import niutilities
import dicom.filereader as dfr
import zipfile
import gzip
import zlib


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
    return tag == (0x5200, 0x9230)


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


def dicom2nii(folder='.', clean='ask', unzip='ask', gzip='ask', verbose=True, cores=1, debug=False):
    '''
    dicom2nii [folder=.] [clean=ask] [unzip=ask] [gzip=ask] [verbose=True] [cores=1]

    USE
    ===

    The command is used to converts MR images from DICOM to NIfTI format. It
    searches for images within the a dicom subfolder within the provided
    subject folder (folder). It expects to find each image within a separate
    subfolder. It then converts the images to NIfTI format and places them
    in the nii folder within the subject folder. To reduce the space use it
    can then gzip the dicom files (gzip). To speed the process up, it can
    run multiple dcm2nii processes in parallel (cores).

    Before running, the command check for presence of existing NIfTI files. The
    behavior when finding them is defined by clean parameter. If set to 'ask',
    it will ask interactively, what to do. If set to 'yes' it will remove any
    existing files and proceede. If set to 'no' it will leave them and abort.

    Before running, the command also checks whether DICOM files might be
    gzipped. If that is the case, the response depends on the setting of the
    unzip parameter. If set to 'yes' it will automatically gunzip them and
    continue. If set to 'no', it will leave them be and abort. If set to 'ask',
    it will ask interactively, what to do.

    PARAMETERS
    ==========

    --folder    The base subject folder with the dicom subfolder that holds
                session numbered folders with dicom files. [.]
    --clean     Whether to remove preexisting NIfTI files (yes), leave them and
                abort (no) or ask interactively (ask). [ask]
    --unzip     If the dicom files are gziped whether to unzip them (yes), leave
                them be and abort (no) or ask interactively (ask). [ask]
    --gzip      After the dicom files were processed whether to gzip them (yes),
                leave them ungzipped (no) or ask interactively (ask). [ask]
    --verbose   Whether to be report on the progress (True) or not (False). [True]
    --cores     How many parallel processes to run dcm2nii conversion with. The
                number is one by defaults, if specified as 'all', the number of
                available cores is utilized.

    RESULTS
    =======

    After running, the command will place all the generated NIfTI files into the
    nii subfolder, named with sequential image number. It will also generate two
    additional files: a subject.txt file and a DICOM-Report.txt file.

    subject.txt file
    ----------------

    The subject.txt will be placed in the subject base folder. It will contain
    the information about the subject id, location of folders and a list of
    created NIfTI images with their description.

    An example subject.txt file would be:

    id: OP169
    subject: OP169
    dicom: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/subjects/OP169/dicom
    raw_data: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/subjects/OP169/nii
    data: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/subjects/OP169/4dfp
    hcp: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/subjects/OP169/hcp
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
    generated subject.txt files form the basis for the following HCP and other
    processing steps.

    DICOM-Report.txt file
    ---------------------

    The DICOM-Report.txt file will be created and placed in the subject's dicom
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

    EXAMPLE USE
    ===========

    gmri dicom2nii folder=. clean=yes unzip=yes gzip=yes cores=3

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-08 Grega Repovš
             - Updated documentation
    '''

    # debug = True
    base = folder
    null = open(os.devnull, 'w')
    dmcf = os.path.join(folder, 'dicom')
    imgf = os.path.join(folder, 'nii')

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
            print "\nPlease remove existing NIfTI files or run the command with 'clean' set to 'yes'. \nAborting processing of DICOM files!\n"
            return
            # exit()

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
            print "\nCan not work with gzipped DICOM files, please unzip them or run with 'unzip' set to 'yes'.\nAborting processing of DICOM files!\n"
            return
            # exit()

    # --- open report files

    r    = open(os.path.join(dmcf, "DICOM-Report.txt"), 'w')
    stxt = open(os.path.join(folder, "subject.txt"), 'w')

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

            # --- setup subject.txt file

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
            logs.append("%02d  %4d %40s   %3d   [TR %7.2f, TE %6.2f]   %s   %s%s" % (niinum, d.SeriesNumber, seriesDescription, nframes, TR, TE, getID(d), time, fz))
            reps.append("---> %02d  %4d %40s   %3d   [TR %7.2f, TE %6.2f]   %s   %s%s" % (niinum, d.SeriesNumber, seriesDescription, nframes, TR, TE, getID(d), time, fz))
        except:
            nframes = 0
            logs.append("%02d  %4d %40s  [TR %7.2f, TE %6.2f]   %s   %s%s" % (niinum, d.SeriesNumber, seriesDescription, TR, TE, getID(d), time, fz))
            reps.append("---> %02d  %4d %40s   [TR %7.2f, TE %6.2f]   %s   %s%s" % (niinum, d.SeriesNumber, seriesDescription, TR, TE, getID(d), time, fz))

        if niinum > 0:
            print >> stxt, "%02d: %s" % (niinum, seriesDescription)

        niiid = str(niinum)
        calls.append({'name': 'dcm2nii: ' + niiid, 'args': ['dcm2nii', '-c', '-v', folder], 'sout': os.path.join(os.path.split(folder)[0], 'dcm2nii_' + niiid + '.log')})
        files.append([niinum, folder, dofz2zf, recenter, fz, reorder, nframes, nslices])
        # subprocess.call(call, shell=True, stdout=null, stderr=null)

    done = niutilities.g_core.runExternalParallel(calls, cores=cores, prepend=' ... ')

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
        for img in imgs:
            if not os.path.exists(img):
                continue
            if debug:
                print "     --> processing: %s [%s]" % (img, os.path.basename(img))
            if img[-3:] == 'nii':
                if debug:
                    print "     --> gzipping: %s" % (img)
                subprocess.call("gzip " + img, shell=True, stdout=null, stderr=null)
                img += '.gz'
            if os.path.basename(img)[0:2] == 'co':
                # os.rename(img, os.path.join(imgf, "%02d-co.nii.gz" % (c)))
                if debug:
                    print "         ... removing: %s" % (img)
                os.remove(img)
            elif os.path.basename(img)[0:1] == 'o':
                if recenter:
                    if debug:
                        print "         ... recentering: %s" % (img)
                    tfname = os.path.join(imgf, "%02d-o.nii.gz" % (niinum))
                    timg = gimg.gimg(img)
                    if recenter == 0.7:
                        timg.hdrnifti.modifyHeader("srow_x:[0.7,0.0,0.0,-84.0];srow_y:[0.0,0.7,0.0,-112.0];srow_z:[0.0,0.0,0.7,-126];quatern_b:0;quatern_c:0;quatern_d:0;qoffset_x:-84.0;qoffset_y:-112.0;qoffset_z:-126.0")
                    elif recenter == 0.8:
                        timg.hdrnifti.modifyHeader("srow_x:[0.8,0.0,0.0,-94.8];srow_y:[0.0,0.8,0.0,-128.0];srow_z:[0.0,0.0,0.8,-130];quatern_b:0;quatern_c:0;quatern_d:0;qoffset_x:-94.8;qoffset_y:-128.0;qoffset_z:-130.0")
                    if debug:
                        print "         saving to: %s" % (tfname)
                    timg.saveimage(tfname)
                    if debug:
                        print "         removing: %s" % (img)
                    os.remove(img)
                else:
                    tfname = os.path.join(imgf, "%02d-o.nii.gz" % (niinum))
                    if debug:
                        print "         ... moving '%s' to '%s'" % (img, tfname)
                    os.rename(img, tfname)

                # -- remove original
                noob = os.path.join(folder, os.path.basename(img)[1:])
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
                    print "         ... moving '%s' to '%s'" % (img, tfname)
                os.rename(img, tfname)

            # --- check also for .bval and .bvec files

            for dwiextra in ['.bval', '.bvec']:
                dwisrc = img.replace('.nii.gz', dwiextra)
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
            niutilities.g_NIfTI.fz2zf(os.path.join(imgf, "%02d.nii.gz" % (niinum)))


        # --- reorder slices if needed

        if reorder:
            # niutilities.g_NIfTI.reorder(os.path.join(imgf,"%02d.nii.gz" % (niinum)))
            timgf = os.path.join(imgf, "%02d.nii.gz" % (niinum))
            timg  = gimg.gimg(timgf)
            timg.data = timg.data[:, ::-1, ...]
            timg.hdrnifti.modifyHeader("srow_x:[-3.4,0.0,0.0,-108.5];srow_y:[0.0,3.4,0.0,-102.0];srow_z:[0.0,0.0,5.0,-63.0];quatern_b:0;quatern_c:0;quatern_d:0;qoffset_x:108.5;qoffset_y:-102.0;qoffset_z:-63.0")
            timg.saveimage(timgf)

        # --- check final geometry

        if tfname:
            hdr = niutilities.g_img.niftihdr(tfname)

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
                            niutilities.g_NIfTI.reslice(tfname, nslices)
                        else:
                            print >> r, "     WARNING: not enough slices (%d) to make a complete volume." % (hdr.sizez)
                            if verbose:
                                print "     WARNING: not enough slices (%d) to make a complete volume." % (hdr.sizez)
                    else:
                        print >> r, "     WARNING: no slice number information, use gmri reslice manually to correct %s" % (tfname)
                        if verbose:
                            print "     WARNING: no slice number information, use gmri reslice manually to correct %s" % (tfname)

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

    if verbose:
        print "Finished!\n"


def dicom2niix(folder='.', clean='ask', unzip='ask', gzip='ask', verbose=True, cores=1, debug=False):
    '''
    dicom2niix [folder=.] [clean=ask] [unzip=ask] [gzip=ask] [verbose=True] [cores=1]

    USE
    ===

    The command is used to convert MR images from DICOM to NIfTI format. It
    searches for images within the a dicom subfolder within the provided
    subject folder (folder). It expects to find each image within a separate
    subfolder. It then converts the images to NIfTI format and places them
    in the nii folder within the subject folder. To reduce the space use it
    can then gzip the dicom files (gzip). To speed the process up, it can
    run multiple dcm2niix processes in parallel (cores).

    This version of the command uses dcm2niix.

    Before running, the command check for presence of existing NIfTI files. The
    behavior when finding them is defined by clean parameter. If set to 'ask',
    it will ask interactively, what to do. If set to 'yes' it will remove any
    existing files and proceede. If set to 'no' it will leave them and abort.

    Before running, the command also checks whether DICOM files might be
    gzipped. If that is the case, the response depends on the setting of the
    unzip parameter. If set to 'yes' it will automatically gunzip them and
    continue. If set to 'no', it will leave them be and abort. If set to 'ask',
    it will ask interactively, what to do.

    PARAMETERS
    ==========

    --folder    The base subject folder with the dicom subfolder that holds
                session numbered folders with dicom files. [.]
    --clean     Whether to remove preexisting NIfTI files (yes), leave them and
                abort (no) or ask interactively (ask). [ask]
    --unzip     If the dicom files are gziped whether to unzip them (yes), leave
                them be and abort (no) or ask interactively (ask). [ask]
    --gzip      After the dicom files were processed whether to gzip them (yes),
                leave them ungzipped (no) or ask interactively (ask). [ask]
    --verbose   Whether to be report on the progress (True) or not (False). [True]
    --cores     How many parallel processes to run dcm2nii conversion with. The
                number is one by defaults, if specified as 'all', the number of
                available cores is utilized.

    RESULTS
    =======

    After running, the command will place all the generated NIfTI files into the
    nii subfolder, named with sequential image number. It will also generate two
    additional files: a subject.txt file and a DICOM-Report.txt file.

    subject.txt file
    ----------------

    The subject.txt will be placed in the subject base folder. It will contain
    the information about the subject id, location of folders and a list of
    created NIfTI images with their description.

    An example subject.txt file would be:

    id: OP169
    subject: OP169
    dicom: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/subjects/OP169/dicom
    raw_data: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/subjects/OP169/nii
    data: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/subjects/OP169/4dfp
    hcp: /Volumes/pooh/MBLab/fMRI/SWM-D-v1/subjects/OP169/hcp
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
    generated subject.txt files form the basis for the following HCP and other
    processing steps.

    DICOM-Report.txt file
    ---------------------

    The DICOM-Report.txt file will be created and placed in the subject's dicom
    subfolder. The file will list the images it found, the information about
    their original sequence number and the resulting NIfTI file number, the name
    of the sequence, the number of frames, TR and TE values, subject id, time of
    acquisition, information and warnings about any additional processing it had
    to perform (e.g. recenter structural images, switch f and z dimensions,
    reslice due to premature end of recording, etc.). In some cases some of the
    information (number of frames, TE, TR) might not be reported if that
    information was not present or couldn't be found in the DICOM file.

    dcm2niix log files
    ------------------

    For each image conversion attempt a dcm2nii_[N].log file will be created
    that holds the output of the dcm2nii command that was run to convert the
    DICOM files to a NIfTI image.

    EXAMPLE USE
    ===========

    gmri dicom2nii folder=. clean=yes unzip=yes gzip=yes cores=3

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-08 Grega Repovš
             - Updated documentation
    2017-07-07 Grega Repovš
             - Modified from dicom2nii to use dcm2niix
    '''

    # debug = True
    base = folder
    null = open(os.devnull, 'w')
    dmcf = os.path.join(folder, 'dicom')
    imgf = os.path.join(folder, 'nii')

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
            print "\nPlease remove existing NIfTI files or run the command with 'clean' set to 'yes'. \nAborting processing of DICOM files!\n"
            return
            # exit()

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
            print "\nCan not work with gzipped DICOM files, please unzip them or run with 'unzip' set to 'yes'.\nAborting processing of DICOM files!\n"
            return
            # exit()

    # --- open report files

    r    = open(os.path.join(dmcf, "DICOM-Report.txt"), 'w')
    stxt = open(os.path.join(folder, "subject.txt"), 'w')

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

            # --- setup subject.txt file

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

        # --- Special nii naming for Philips

        niinum = c
        try:
            if d.Manufacturer == 'Philips Medical Systems':
                # niinum = (d.SeriesNumber - 1) / 100
                niinum = d.SeriesNumber
        except:
            pass

        try:
            nframes = d[0x2001, 0x1081].value
            logs.append("%02d  %4d %40s   %3d   [TR %7.2f, TE %6.2f]   %s   %s" % (niinum, d.SeriesNumber, seriesDescription, nframes, TR, TE, getID(d), time))
            reps.append("---> %02d  %4d %40s   %3d   [TR %7.2f, TE %6.2f]   %s   %s" % (niinum, d.SeriesNumber, seriesDescription, nframes, TR, TE, getID(d), time))
        except:
            nframes = 0
            logs.append("%02d  %4d %40s  [TR %7.2f, TE %6.2f]   %s   %s" % (niinum, d.SeriesNumber, seriesDescription, TR, TE, getID(d), time))
            reps.append("---> %02d  %4d %40s   [TR %7.2f, TE %6.2f]   %s   %s" % (niinum, d.SeriesNumber, seriesDescription, TR, TE, getID(d), time))

        if niinum > 0:
            print >> stxt, "%02d: %s" % (niinum, seriesDescription)

        niiid = str(niinum)
        calls.append({'name': 'dcm2niix: ' + niiid, 'args': ['dcm2niix', '-f', niiid, '-z', 'y', folder], 'sout': os.path.join(os.path.split(folder)[0], 'dcm2niix_' + niiid + '.log')})
        files.append([niinum, folder, nframes, nslices])
        # subprocess.call(call, shell=True, stdout=null, stderr=null)

    done = niutilities.g_core.runExternalParallel(calls, cores=cores, prepend=' ... ')

    for niinum, folder, nframes, nslices in files:

        print >> r, logs.pop(0),
        if verbose:
            print reps.pop(0),
            if debug:
                print ""

        tfname = False
        imgs = glob.glob(os.path.join(folder, "*.nii*"))
        if debug:
            print "     --> found nifti files: %s" % ("\n                            ".join(imgs))
        for img in imgs:
            if not os.path.exists(img):
                continue
            if debug:
                print "     --> processing: %s [%s]" % (img, os.path.basename(img))
            if img[-3:] == 'nii':
                if debug:
                    print "     --> gzipping: %s" % (img)
                subprocess.call("gzip " + img, shell=True, stdout=null, stderr=null)
                img += '.gz'

            tfname = os.path.join(imgf, "%02d.nii.gz" % (niinum))
            if debug:
                print "         ... moving '%s' to '%s'" % (img, tfname)
            os.rename(img, tfname)

            # --- check also for .bval and .bvec files

            for dwiextra in ['.bval', '.bvec']:
                dwisrc = img.replace('.nii.gz', dwiextra)
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

        # --- check final geometry

        if tfname:
            hdr = niutilities.g_img.niftihdr(tfname)

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
                            niutilities.g_NIfTI.reslice(tfname, nslices)
                        else:
                            print >> r, "     WARNING: not enough slices (%d) to make a complete volume." % (hdr.sizez)
                            if verbose:
                                print "     WARNING: not enough slices (%d) to make a complete volume." % (hdr.sizez)
                    else:
                        print >> r, "     WARNING: no slice number information, use gmri reslice manually to correct %s" % (tfname)
                        if verbose:
                            print "     WARNING: no slice number information, use gmri reslice manually to correct %s" % (tfname)

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

    if verbose:
        print "Finished!\n"



def sortDicom(folder=".", **kwargs):
    '''
    sortDicom [folder=.]

    USE
    ===

    The command looks for the inbox subfolder in the specified subject folder
    (folder) and checks for presence of DICOM files in the inbox folder and its
    subfolders. It inspects the found files, creates a dicom folder and for each
    image a numbered subfolder. It then moves the found DICOM files in the
    correct subfolders to prepare them for dicom2nii processing.

    PARAMETERS
    ==========

    --folder: The base subject folder that contains the inbox subfolder with
              the unsorted DICOM files.

    EXAMPLE USE
    ===========

    gmri sortDicom folder=OP667

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-08 Grega Repovš
             - Updated documentation
    '''

    from shutil import copy
    dcmf  = os.path.join(kwargs.get('out_dir', folder), 'dicom')
    files = kwargs.get('files', None)
    if files is None:
        inbox = os.path.join(folder, 'inbox')
        print "============================================\n\nProcessing files from %s\n" % (inbox)
        files = glob.glob(os.path.join(inbox, "*"))
        files = files + glob.glob(os.path.join(inbox, "*/*"))
        files = files + glob.glob(os.path.join(inbox, "*/*/*"))
        files = [e for e in files if os.path.isfile(e)]

    seqs  = []
    for dcm in files:
        try:
            # info = dicom.read_file(dcm, stop_before_pixels=True)
            info = readDICOMBase(dcm)
            sid  = getID(info)
            time = getDicomTime(info)
            print "===> Sorting dicoms for %s scanned on %s\n" % (sid, time)
            break
        except:
            # raise
            pass

    if not os.path.exists(dcmf):
        os.makedirs(dcmf)
        print "---> Created a dicom superfolder"

    dcmn = 0

    for dcm in files:
        if os.path.basename(dcm)[0:2] in ["XX", "PS"]:
            continue
        try:
            # d    = dicom.read_file(dcm, stop_before_pixels=True)
            d    = readDICOMBase(dcm)
            if d is None:
                continue
            sqid = str(d.SeriesNumber)

        except:
            continue
        sqfl = os.path.join(dcmf, sqid)
        sid  = getID(d)
        if sqid not in seqs:
            if not os.path.exists(sqfl):
                os.makedirs(sqfl)
                try:
                    print "---> Created subfolder for sequence %s %s - %s" % (sid, sqid, d.SeriesDescription)
                except:
                    print "---> Created subfolder for sequence %s %s - %s " % (sid, sqid, d.ProtocolName)

        dcmn += 1

        try:
            sop = d.SOPInstanceUID
        except:
            sop = "%010d" % (dcmn)

        # --- check if for some reason we are dealing with gzipped dicom files and add an extension when renaming

        ext = dcm.split('.')[-1]
        if ext == "gz":
            ext = ".gz"
        else:
            ext = ""

        tgf = os.path.join(sqfl, "%s-%s-%s.dcm%s" % (sid, sqid, sop, ext))

        should_copy = kwargs.get('copy', False)
        if should_copy:
            copy(dcm, tgf)
        else:
            os.rename(dcm, tgf)

    print "\nDone!\n\n"


def listDicom(folder=None):
    '''
    listDicom [folder=inbox]

    USE
    ===

    The command inspects the folder (folder) for dicom files and prints a
    detailed report of the results. Specifically, for each dicom file it finds
    in the specified folder and its subfolders it will print:

    * location of the file
    * subject id recorded in the dicom file
    * sequence number and name
    * date and time of acquisition

    Importantly, it can work with both regular and gzipped DICOM files.

    PARAMETERS
    ==========

    --folder: The folder to be inspected for the presence of the DICOM files.
              [inbox]

    EXAMPLE USE
    ===========

    gmri listDicom folder=OP269/dicom

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-08 Grega Repovš
             - Updated documentation
    '''

    if folder is None:
        folder = os.path.join(".", 'inbox')

    print "============================================\n\nListing dicoms from %s\n" % (folder)

    files = glob.glob(os.path.join(folder, "*"))
    files = files + glob.glob(os.path.join(folder, "*/*"))
    files = [e for e in files if os.path.isfile(e)]

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


def splitDicom(folder=None):
    '''
    splitDicom [folder=inbox]

    USE
    ===

    The command is used when DICOM images from different subjects are mixed in
    the same folder and need to be sorted out. Specifically, the command
    inspects the specified folder (folder) and its subfolders for the presence
    of DICOM files. For each DICOM file it finds, it checks, what subject id the
    file belongs to. In the specified folder it then creates a subfolder for
    each of the found subjects and moves all the DICOM files in the right
    subject's subfolder.

    PARAMETERS
    ==========

    --folder: The folder that contains the DICOM files to be sorted out.

    EXAMPLE USE
    ===========

    gmri splitDicom folder=dicommess

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-08 Grega Repovš
             - Updated documentation
    '''

    if folder is None:
        folder = os.path.join(".", 'inbox')

    print "============================================\n\nSorting dicoms from %s\n" % (folder)

    files = glob.glob(os.path.join(folder, "*"))
    files = files + glob.glob(os.path.join(folder, "*/*"))
    files = [e for e in files if os.path.isfile(e)]

    subjects = []

    for dcm in files:
        try:
            # d    = dicom.read_file(dcm, stop_before_pixels=True)
            d    = readDICOMBase(dcm)
            time = getDicomTime(d)
            sid  = getID(d)
            if sid not in subjects:
                subjects.append(sid)
                os.makedirs(os.path.join(folder, sid))
                print "===> creating subfolder for subject %s" % (sid)
            print "---> %s - %-6s %6d - %-30s scanned on %s" % (dcm, sid, d.SeriesNumber, d.SeriesDescription, time)
            os.rename(dcm, os.path.join(folder, sid, os.path.basename(dcm)))
        except:
            pass


def processPhilips(folder=None, check=None, pattern=None):
    '''
    processPhilips [folder=.] [check=yes] [pattern=OP]

    The "original" processInbox function written specifically for data coming off the Ljubljana Philips scanner,
    it has been adapted for more flexible use in the form of the processInbox function, which should be used instead.
    '''

    if check == 'no':
        check = False
    else:
        check = True

    if folder is None:
        folder = "."
    inbox = os.path.join(folder, 'inbox')

    if pattern is None:
        pattern = r"(OP[0-9.-]+)"
    else:
        pattern = r"(%s[0-9.-]+)" % (pattern)

    # ---- get file list

    print "\n---> Checking for packets in %s ..." % (inbox)

    zips = glob.glob(os.path.join(inbox, '*.zip'))
    getop = re.compile(pattern)

    okpackets  = []
    badpackets = []
    for zipf in zips:
        m = getop.search(zipf)
        if m.groups():
            okpackets.append((zipf, m.group(0)))
        else:
            badpackets.append(zipf)

    print "---> Found the following packets to process:"
    for p, o in okpackets:
        print "     %s: %s" % (o, os.path.basename(p))

    if len(badpackets):
        print "---> For these packets no OP code was found and won't be processed:"
        for p in badpackets:
            print "     %s" % (os.path.basename(p))

    if check:
        s = raw_input("\n===> Should I proceeed with processing the listed packages [y/n]: ")
        if s != "y":
            print "---> Aborting operation!\n"
            return

    print "---> Starting to process %d packets ..." % (len(okpackets))


    # ---- Ok, now loop through the packets

    afolder = os.path.join(folder, "Archive")
    if not os.path.exists(afolder):
        os.makedirs(afolder)
        print "---> Created Archive folder for processed packages."

    for p, o in okpackets:

        # --- Big info

        print "\n\n---=== PROCESSING %s ===---\n" % (o)

        # --- create a new OP folder
        opfolder = os.path.join(folder, o)

        if os.path.exists(opfolder):
            print "---> WARNING: %s folder exists, skipping package %s" % (o, os.path.basename(p))
            continue

        os.makedirs(opfolder)

        # --- unzip the file

        print "...  unzipping %s" % (os.path.basename(p))
        with zipfile.ZipFile(p, 'r') as z:
            z.extractall(opfolder)
        print "     -> done!"

        # --- move package to archive

        print "... moving %s to archive" % (os.path.basename(p))
        shutil.move(p, afolder)
        print "     -> done!"

        # --- move dicom files to inbox

        print "... moving dicoms to inbox"
        shutil.move(os.path.join(opfolder, "Dicom", "DICOM"), os.path.join(opfolder, "inbox"))
        shutil.rmtree(os.path.join(opfolder, "Dicom"))
        print "     -> done!"

        # --- run sort dicom

        print "\n\n===> running sortDicom"
        sortDicom(folder=opfolder)

        # --- run dicom to nii

        print "\n\n===> running dicom2nii"
        dicom2nii(folder=opfolder, clean='no', unzip='yes', gzip='yes', verbose=True)

    print "\n\n---=== DONE PROCESSING PACKAGES - Have a nice day! ===---\n"

    return


def processInbox(folder=None, check=None, pattern=None, cores=1):
    '''
    processInbox [folder=.] [check=yes] [pattern=".*?(OP[0-9.-]+).*\.zip"] [cores=1]

    USE
    ===

    The command is used to automagically process zipped packets with individual
    subject's DICOM files all the way to, and including, generation of NIfTI
    files.

    The command first looks into provided inbox folder (folder; by default
    `inbox/MR`) and finds any zip files that match the specified regex pattern
    (pattern). The pattern has to be prepared to return as the first group
    found the subject id. Once all the zip files have been found, it lists them
    along with the extracted subject ids. If the check parameter is set to
    'yes', the command will ask whether to process the listed packages, if it is
    set to 'no', it will just start processing them.

    For each found package, the command will generate a new subject folder, its
    name set to the subject id extracted. It will then uzip all the files in the
    packet into an inbox folder created within the subject folder. Once all the
    files are extracted, the packet is then moved to the `study/subjects/archive/MR`
    folder. If the archive folder does not yet exist, it is created.

    After the files have been extracted to the inbox folder, a sortDicom command
    is run on that folder and all the DICOM files are sorted and moved to the
    dicom folder. After that is done, a dicom2nii command is run to convert the
    DICOM images to the NIfTI format and move them to the nii folder. The DICOM
    files are preserved and gzipped to save space. To speed up the conversion
    the cores parameter is passed to the dicom2nii command. subject.txt and
    DICOM-Report.txt files are created as well. Please, check the help for
    sortDicom and dicom2nii commands for the specifics.

    PARAMETERS
    ==========

    --folder   The base study subjects folder (e.g. WM44/subjects) where the
               inbox and individual subject folders are. [.]
    --check    Whether to ask for confirmation to proceed once zip packages in
               inbox are identified and listed. [yes]
    --pattern  The pattern to use to extract subject codes.
               [".*?(OP[0-9.-]+).*\.zip"]
    --cores    The number of parallel processes to use when running dcm2nii
               command. If specified as 'all', all the avaliable cores will
               be utilized. [1]

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-08 Grega Repovš
             - Updated documentation
    '''

    if check == 'no':
        check = False
    else:
        check = True

    if folder is None:
        folder = "."
    inbox = os.path.join(folder, 'inbox', 'MR')

    if pattern is None:
        pattern = r".*?(OP[0-9.-]+).*\.zip"

    igz = re.compile(r'.*\.gz')

    # ---- get file list

    print "\n---> Checking for packets in %s ... using pattern '%s'" % (inbox, pattern)

    zips = glob.glob(os.path.join(inbox, '*.zip'))
    getop = re.compile(pattern)

    okpackets  = []
    badpackets = []
    for zipf in zips:
        m = getop.search(os.path.basename(zipf))
        if m:
            if m.groups():
                okpackets.append((zipf, m.group(1)))
            else:
                badpackets.append(zipf)

    print "---> Found the following packets to process:"
    for p, o in okpackets:
        print "     %s: %s" % (o, os.path.basename(p))

    if len(badpackets):
        print "---> For these packets subject id could not be identified and they won't be processed:"
        for p in badpackets:
            print "     %s" % (os.path.basename(p))

    if check:
        s = raw_input("\n===> Should I proceeed with processing the listed packages [y/n]: ")
        if s != "y":
            print "---> Aborting operation!\n"
            return

    print "---> Starting to process %d packets ..." % (len(okpackets))


    # ---- Ok, now loop through the packets

    afolder = os.path.join(folder, "archive", "MR")
    if not os.path.exists(afolder):
        os.makedirs(afolder)
        print "---> Created Archive folder for processed packages."

    for p, o in okpackets:

        # --- Big info

        print "\n\n---=== PROCESSING %s ===---\n" % (o)

        # --- create a new OP folder
        opfolder = os.path.join(folder, o)

        if os.path.exists(opfolder):
            print "---> WARNING: %s folder exists, skipping package %s" % (o, os.path.basename(p))
            continue

        os.makedirs(opfolder)

        # --- create the inbox folder for dicoms

        dfol = os.path.join(opfolder, 'inbox')
        os.makedirs(dfol)

        # --- unzip the file

        print "...  unzipping %s" % (os.path.basename(p))
        dnum = 0
        fnum = 0

        z = zipfile.ZipFile(p, 'r')
        ilist = z.infolist()
        for sf in ilist:
            if sf.file_size > 0:

                if fnum % 1000 == 0:
                    dnum += 1
                    os.makedirs(os.path.join(dfol, str(dnum)))
                fnum += 1

                print "...  extracting:", sf.filename, sf.file_size
                fdata = z.read(sf)
                if igz.match(sf.filename):
                    gzname = os.path.join(dfol, str(dnum), str(fnum) + ".gz")
                    fout = open(gzname, 'wb')
                    fout.write(fdata)
                    fout.close()
                    fin = gzip.open(gzname, 'rb')
                    fdata = fin.read()
                    fin.close()
                    os.remove(gzname)
                fout = open(os.path.join(dfol, str(dnum), str(fnum)), 'wb')
                fout.write(fdata)
                fout.close()

        z.close()
        print "     -> done!"

        # --- move package to archive

        if os.path.exists(os.path.join(afolder, os.path.basename(p))):
            print "... WARNING: %s already exists in archive and it will not be moved!" % (os.path.basename(p))
        else:
            print "... moving %s to archive" % (os.path.basename(p))
            shutil.move(p, afolder)
            print "     -> done!"

        # --- run sort dicom

        print "\n\n===> running sortDicom"
        sortDicom(folder=opfolder)

        # --- run dicom to nii

        print "\n\n===> running dicom2nii"
        dicom2niix(folder=opfolder, clean='no', unzip='yes', gzip='yes', cores=cores, verbose=True)

    print "\n\n---=== DONE PROCESSING PACKAGES - Have a nice day! ===---\n"

    return


def getDICOMInfo(dfile=None, scanner='siemens'):
    '''
    getDICOMInfo dfile=<dicom_file> [scanner=siemens]

    USE
    ===

    The command inspects the specified DICOM file (dfile) for information that
    is relevant for HCP preprocessing and prints out the report. Specifically
    it looks for and reports the following information:

    * Institution
    * Scanner
    * Sequence
    * Subject ID
    * Sample spacing
    * Bandwidth
    * Acquisition Matrix
    * Dwell Time
    * Slice Acquisition Order

    If the information can not be found or computed it is listed as 'undefined'.

    Currently only DICOM files generated by Siemens scanners are fully
    supported.

    PARAMETERS
    ==========

    --dfile:   The path to the DICOM file to be inspected.
    --scanner: The scanner on which the data was acquired, currently only
               "siemens" is supported. [siemens]

    EXAMPLE USE
    ===========

    gmri getDICOMInfo dfile=ap308e727bxehd2.372.2342.42566.dcm

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-08 Grega Repovš
             - Updated documentation
    '''

    if dfile is None:
        print "\nERROR: No path to the dicom file is provided!"
        return

    if not os.path.exists(dfile):
        print "\nERROR: Could not find the requested dicom file! [%s]" % (dfile)
        return

    if scanner not in ['siemens']:
        print "\nERROR: The provided scanner is not supported! [%s]" % (scanner)
        return

    d = readDICOMBase(dfile)
    ok = True

    print "\nHCP relevant information\n(dicom %s)\n" % (dfile)

    try:
        print "            Institution:", d[0x0008, 0x0080].value
    except:
        print "            Institution: undefined"

    try:
        print "                Scanner:", d[0x0008, 0x0070].value, d[0x0008, 0x1090].value
    except:
        print "                Scanner: undefined"

    try:
        print "               Sequence:", d[0x0008, 0x103e].value
    except:
        print "               Sequence: undefined"

    try:
        print "             Subject ID:", d[0x0010, 0x0020].value
    except:
        print "             Subject ID: undefined"

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

    # --- look for slice ordering info

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

    print



