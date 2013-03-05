#!/opt/local/bin/python2.7

import dicom
import os
import glob
import datetime
import subprocess

def dicom2nii(folder='.', clean='ask', unzip='ask', gzip='ask', verbose=True):

    null = open(os.devnull, 'w')
    dmcf = os.path.join(folder, 'dicom')
    imgf = os.path.join(folder, 'nii')
    r = open(os.path.join(dmcf, "DICOM-Report.txt"), 'w')

    # check for existing .gz files

    prior = glob.glob(os.path.join(imgf,"*.nii.gz")) + glob.glob(os.path.join(dmcf,"*","*.nii.gz"))
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
            exit()

    # gzipped files

    gzipped = glob.glob(os.path.join(dmcf, "*", "*.dcm.gz"))
    if len(gzipped) > 0:
        if unzip == 'ask':
            print "\nWARNING: DICOM files have been compressed using gzip."
            unzip = raw_input("\nDo you want to unzip the existing files? [no] > ")
        if unzip == "yes":
            if verbose: print "\nUnzipping files (this might take a while)"
            for g in gzipped:
                subprocess.call("gunzip "+g, shell=True) #, stdout=null, stderr=null)
        else:
            print "\nCan not work with gzipped DICOM files, please unzip them or run with 'unzip' set to 'yes'.\nAborting processing of DICOM files!\n"
            exit()

    # get a list of folders

    folders = [e for e in os.listdir(dmcf) if os.path.isdir(os.path.join(dmcf, e))]
    folders = [int(e) for e in folders if e.isdigit()]
    folders.sort()
    folders = [os.path.join(dmcf, str(e)) for e in folders]

    if not os.path.exists(imgf):
        os.makedirs(imgf)

    first = True
    c = 0
    for folder in folders:
        d = dicom.read_file(glob.glob(os.path.join(folder, "*"))[1])
        c += 1

        if first:
            first = False
            time = datetime.datetime.strptime(str(int(float(d.StudyDate+d.StudyTime))), "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
            print >> r, "Report for %s scanned on %s\n" % (d.PatientID, time)
            if verbose: print "\n\nProcessing images from %s scanned on %s\n" % (d.PatientID, time)

        try:
            seriesDescription = d.SeriesDescription
        except:
            continue

        try:
            time = datetime.datetime.strptime(d.ContentTime[0:6], "%H%M%S").strftime("%H:%M:%S")
        except:
            time = datetime.datetime.strptime(d.StudyTime[0:6], "%H%M%S").strftime("%H:%M:%S")

        try:
            TR = d.RepetitionTime
        except:
            TR = 0

        try: 
            TE = d.EchoTime
        except:
            TE = 0


        try:
            print >> r, "%02d  %4d %40s   %3d   [TR %7.2f, TE %6.2f]   %s" % (c, d.SeriesNumber, seriesDescription, d[0x2001,0x1081].value, TR, TE, time)
            if verbose: print "---> %02d  %4d %40s   %3d   [TR %7.2f, TE %6.2f]   %s" % (c, d.SeriesNumber, seriesDescription, d[0x2001,0x1081].value, TR, TE, time)
        except:
            print >> r, "%02d  %4d %40s  [TR %7.2f, TE %6.2f]   %s" % (c, d.SeriesNumber, seriesDescription, TR, TE, time)
            if verbose: print "---> %02d  %4d %40s   [TR %7.2f, TE %6.2f]   %s" % (c, d.SeriesNumber, seriesDescription, TR, TE, time)

        call = "dcm2nii -c -v " + folder
        subprocess.call(call, shell=True, stdout=null, stderr=null)

        imgs = glob.glob(os.path.join(folder, "*.gz"))
        for img in imgs:
            if os.path.basename(img)[0:2] == 'co':
                os.rename(img, os.path.join(imgf, "%02d-co.nii.gz" % (c)))
            elif os.path.basename(img)[0:1] == 'o':
                os.rename(img, os.path.join(imgf, "%02d-o.nii.gz" % (c)))
            else:
                os.rename(img, os.path.join(imgf, "%02d.nii.gz" % (c)))

    if verbose:
        print "... done!"

    r.close()

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


def sortDicom(folder="."):
    inbox = os.path.join(folder, 'inbox')
    dcmf  = os.path.join(folder, 'dicom')

    print "============================================\n\nProcessing files from %s\n" % (inbox)

    if not os.path.exists(dcmf):
        os.makedirs(dcmf)
        print "---> Created a dicom superfolder"

    seqs  = []
    files = glob.glob(os.path.join(inbox, "*"))
    files = files + glob.glob(os.path.join(inbox, "*/*"))
    for dcm in files:
        try:
            d    = dicom.read_file(dcm)
        except:
            continue
        sqid = str(d.SeriesNumber)
        sqfl = os.path.join(dcmf, sqid)
        if sqid not in seqs:
            if not os.path.exists(sqfl):
                os.makedirs(sqfl)
                print "---> Created subfolder for sequence %s - %s" % (sqid, d.SeriesDescription)
        tgf = os.path.join(sqfl, "%s-%s-%s.dcm" % (d.AccessionNumber, sqid, d.SOPInstanceUID.split(".")[-1]))
        os.rename(dcm, tgf)

    print "\nDone!\n\n"
