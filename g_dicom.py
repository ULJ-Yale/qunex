#!/opt/local/bin/python2.7

# import dicom
import os
import re
import glob
import shutil
import datetime
import subprocess
import g_mri.g_NIfTI
import g_mri.g_gimg as gimg
import dicom.filereader as dfr
import zipfile
import gzip
import zlib


def _at_frame(tag, VR, length):
    return tag == (0x5200, 0x9230)

def readDICOMBase(filename):
    # try partial read

    try:
        f = open(filename, "rb")
        d = dfr.read_partial(f, stop_when=_at_frame)
        f.close()
        return d
    except:
        return None
        #d = dfr.read_file(filename, stop_before_pixels=True)
        #return d

def getDicomTime(info):
    try:
        time = datetime.datetime.strptime(str(int(float(info.StudyDate+info.ContentTime))), "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    except:
        try:
            time = datetime.datetime.strptime(str(int(float(info.StudyDate+info.StudyTime))), "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
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

def dicom2nii(folder='.', clean='ask', unzip='ask', gzip='ask', verbose=True):

    base = folder
    null = open(os.devnull, 'w')
    dmcf = os.path.join(folder, 'dicom')
    imgf = os.path.join(folder, 'nii')
    r    = open(os.path.join(dmcf, "DICOM-Report.txt"), 'w')
    stxt = open(os.path.join(folder, "subject.txt"), 'w')

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
        # d = dicom.read_file(glob.glob(os.path.join(folder, "*.dcm"))[-1], stop_before_pixels=True)
        d = readDICOMBase(glob.glob(os.path.join(folder, "*.dcm"))[-1])
        c += 1

        if first:
            first = False
            time = getDicomTime(d)
            print >> r, "Report for %s scanned on %s\n" % (getID(d), time)
            if verbose: print "\n\nProcessing images from %s scanned on %s\n" % (getID(d), time)

            # --- setup subject.txt file

            print >> stxt, "id:", getID(d)
            print >> stxt, "subject:", getID(d)
            print >> stxt, "dicom:", os.path.abspath(os.path.join(base, 'dicom'))
            print >> stxt, "raw_data:", os.path.abspath(os.path.join(base, 'nii'))
            print >> stxt, "data:", os.path.abspath(os.path.join(base, '4dfp'))
            print >> stxt, "hcp:", os.path.abspath(os.path.join(base, 'hcp'))

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

        try:
            TR = d.RepetitionTime
        except:
            try:
                TR = d[0x5200,0x9229][0][0x0018,0x9112][0][0x0018,0x0080].value
            except:
                TR = 0

        try:
            TE = d.EchoTime
        except:
            try:
                TE = d[0x5200,0x9230][0][0x0018,0x9114][0][0x0018,0x9082].value
            except:
                TE = 0

        try:
            nslices = d[0x2001,0x1018].value
        except:
            nslices = 0

        recenter, dofz2zf, fz, reorder = False, False, "", False
        try:
            if d.Manufacturer == 'Philips Medical Systems' and int(d[0x2001, 0x1081].value) > 1:
                dofz2zf, fz = True, "  (switched fz)"
            if d.Manufacturer == 'Philips Medical Systems' and d.SpacingBetweenSlices in [0.7, 0.8]:
                recenter, fz = d.SpacingBetweenSlices, "  (recentered)"
            #if d.Manufacturer == 'SIEMENS' and d.InstitutionName == 'Univerisity North Carolina' and d.AcquisitionMatrix == [0, 64, 64, 0]:
            #    reorder, fz = True, " (reordered slices)"
        except:
            pass

        try:
            nframes = d[0x2001,0x1081].value;
            print >> r, "%02d  %4d %40s   %3d   [TR %7.2f, TE %6.2f]   %s   %s%s" % (c, d.SeriesNumber, seriesDescription, nframes, TR, TE, getID(d), time, fz)
            if verbose: print "---> %02d  %4d %40s   %3d   [TR %7.2f, TE %6.2f]   %s   %s%s" % (c, d.SeriesNumber, seriesDescription, nframes, TR, TE, getID(d), time, fz)
        except:
            nframes = 0
            print >> r, "%02d  %4d %40s  [TR %7.2f, TE %6.2f]   %s   %s%s" % (c, d.SeriesNumber, seriesDescription, TR, TE, getID(d), time, fz)
            if verbose: print "---> %02d  %4d %40s   [TR %7.2f, TE %6.2f]   %s   %s%s" % (c, d.SeriesNumber, seriesDescription, TR, TE, getID(d), time, fz)

        print >> stxt, "%02d: %s" % (c, seriesDescription)

        call = "dcm2nii -c -v " + folder
        subprocess.call(call, shell=True, stdout=null, stderr=null)

        tfname = False
        imgs = glob.glob(os.path.join(folder, "*.gz"))
        for img in imgs:
            if os.path.basename(img)[0:2] == 'co':
                # os.rename(img, os.path.join(imgf, "%02d-co.nii.gz" % (c)))
                os.remove(img)
            elif os.path.basename(img)[0:1] == 'o':
                if recenter:
                    tfname = os.path.join(imgf, "%02d-o.nii.gz" % (c))
                    timg = gimg.gimg(img)
                    if recenter == 0.7:
                        timg.hdrnifti.modifyHeader("srow_x:[0.7,0.0,0.0,-84.0];srow_y:[0.0,0.7,0.0,-112.0];srow_z:[0.0,0.0,0.7,-126];quatern_b:0;quatern_c:0;quatern_d:0;qoffset_x:-84.0;qoffset_y:-112.0;qoffset_z:-126.0")
                    elif recenter == 0.8:
                        timg.hdrnifti.modifyHeader("srow_x:[0.8,0.0,0.0,-94.8];srow_y:[0.0,0.8,0.0,-128.0];srow_z:[0.0,0.0,0.8,-130];quatern_b:0;quatern_c:0;quatern_d:0;qoffset_x:-94.8;qoffset_y:-128.0;qoffset_z:-130.0")
                    timg.saveimage(tfname)
                    os.remove(img)
                else:
                    tfname = os.path.join(imgf, "%02d-o.nii.gz" % (c))
                    os.rename(img, tfname)

                # -- remove original
                noob = os.path.join(folder, os.path.basename(img)[1:])
                noot = os.path.join(imgf, "%02d.nii.gz" % (c))
                if os.path.exists(noob):
                    os.remove(noot)
                elif os.path.exists(noot):
                    os.remove(noot)
            else:
                tfname = os.path.join(imgf, "%02d.nii.gz" % (c))
                os.rename(img, tfname)

            # --- check also for .bval and .bvec files

            for dwiextra in ['.bval', '.bvec']:
                dwisrc = img.replace('.nii.gz', dwiextra)
                if os.path.exists(dwisrc):
                    os.rename(dwisrc, os.path.join(imgf, "%02d%s" % (c, dwiextra)))


        # --- flip z and t dimension if needed

        if dofz2zf:
            g_mri.g_NIfTI.fz2zf(os.path.join(imgf,"%02d.nii.gz" % (c)))

        # --- reorder slices if needed

        if reorder:
            #g_mri.g_NIfTI.reorder(os.path.join(imgf,"%02d.nii.gz" % (c)))
            timgf = os.path.join(imgf,"%02d.nii.gz" % (c))
            timg  = gimg.gimg(timgf)
            timg.data = timg.data[:,::-1,...]
            timg.hdrnifti.modifyHeader("srow_x:[-3.4,0.0,0.0,-108.5];srow_y:[0.0,3.4,0.0,-102.0];srow_z:[0.0,0.0,5.0,-63.0];quatern_b:0;quatern_c:0;quatern_d:0;qoffset_x:108.5;qoffset_y:-102.0;qoffset_z:-63.0")
            timg.saveimage(timgf)

        # --- check final geometry

        if tfname:
            hdr = g_mri.g_img.niftihdr(tfname)

            if hdr.sizez > hdr.sizey:
                print >> r, "     WARNING: unusual geometry of the NIfTI file: %d %d %d %d [xyzf]" % (hdr.sizex, hdr.sizey, hdr.sizez, hdr.frames)
                if verbose: print "     WARNING: unusual geometry of the NIfTI file: %d %d %d %d [xyzf]" % (hdr.sizex, hdr.sizey, hdr.sizez, hdr.frames)

            if nframes > 1:
                if hdr.frames != nframes:
                    print >> r, "     WARNING: number of frames in nii does not match dicom information: %d vs. %d frames" % (hdr.frames, nframes)
                    if verbose: print "     WARNING: number of frames in nii does not match dicom information: %d vs. %d frames" % (hdr.frames, nframes)
                    if nslices > 0:
                        gframes = int(hdr.sizez / nslices)
                        print >> r, "     WARNING: reslicing image to %d slices and %d good frames" % (nslices, gframes)
                        if verbose: print "     WARNING: reslicing image to %d slices and %d good frames" % (nslices, gframes)
                        g_mri.g_NIfTI.reslice(tfname, nslices)
                    else:
                        print >> r, "     WARNING: no slice number information, use gmri reslice manually to correct %s" % (tfname)
                        if verbose: print "     WARNING: no slice number information, use gmri reslice manually to correct %s" % (tfname)

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
            #info = dicom.read_file(dcm, stop_before_pixels=True)
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
            #d    = dicom.read_file(dcm, stop_before_pixels=True)
            d    = readDICOMBase(dcm)
            if d == None:
                continue
        except:
            continue
        sqid = str(d.SeriesNumber)
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

        tgf = os.path.join(sqfl, "%s-%s-%s.dcm" % (sid, sqid, sop))

        should_copy = kwargs.get('copy', False)
        if should_copy:
            copy(dcm, tgf)
        else:
            os.rename(dcm, tgf)

    print "\nDone!\n\n"


def listDicom(folder=None):
    if folder == None:
        folder = os.path.join(".", 'inbox')

    print "============================================\n\nListing dicoms from %s\n" % (folder)

    files = glob.glob(os.path.join(folder, "*"))
    files = files + glob.glob(os.path.join(folder, "*/*"))
    files = [e for e in files if os.path.isfile(e)]

    for dcm in files:
        try:
            #d    = dicom.read_file(dcm, stop_before_pixels=True)
            d    = readDICOMBase(dcm)
            time = getDicomTime(d)
            try:
                print "---> %s - %-6s %6d - %-30s scanned on %s" % (dcm, getID(d), d.SeriesNumber, d.SeriesDescription, time)
            except:
                print "---> %s - %-6s %6d - %-30s scanned on %s" % (dcm, getID(d), d.SeriesNumber, d.ProtocolName, time)
        except:
            pass

def splitDicom(folder=None):
    if folder == None:
        folder = os.path.join(".", 'inbox')

    print "============================================\n\nSorting dicoms from %s\n" % (folder)

    files = glob.glob(os.path.join(folder, "*"))
    files = files + glob.glob(os.path.join(folder, "*/*"))
    files = [e for e in files if os.path.isfile(e)]

    subjects = []

    for dcm in files:
        try:
            #d    = dicom.read_file(dcm, stop_before_pixels=True)
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
    if check == 'no':
        check = False
    else:
        check = True

    if folder == None:
        folder = "."
    inbox = os.path.join(folder, 'inbox')

    if pattern == None:
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


def processInbox(folder=None, check=None, pattern=None):
    if check == 'no':
        check = False
    else:
        check = True

    if folder == None:
        folder = "."
    inbox = os.path.join(folder, 'inbox')

    if pattern == None:
        pattern = r"(.*).zip"

    igz = re.compile(r'.*\.gz')

    # ---- get file list

    print "\n---> Checking for packets in %s ... using pattern '%s'" % (inbox, pattern)

    zips = glob.glob(os.path.join(inbox, '*.zip'))
    getop = re.compile(pattern)

    okpackets  = []
    badpackets = []
    for zipf in zips:
        m = getop.search(os.path.basename(zipf))
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
                    gzname = os.path.join(dfol, str(dnum), str(fnum)+".gz")
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

        print "... moving %s to archive" % (os.path.basename(p))
        shutil.move(p, afolder)
        print "     -> done!"

        # --- run sort dicom

        print "\n\n===> running sortDicom"
        sortDicom(folder=opfolder)

        # --- run dicom to nii

        print "\n\n===> running dicom2nii"
        dicom2nii(folder=opfolder, clean='no', unzip='yes', gzip='yes', verbose=True)

    print "\n\n---=== DONE PROCESSING PACKAGES - Have a nice day! ===---\n"

    return


