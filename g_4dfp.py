#!/opt/local/bin/python2.7

import os
import g_mri
import collections
import subprocess
import g_mri.g_gimg as g
import os.path
import glob
import re
import datetime


template = '''@ economy = 5
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
'''


recode = {True: 'ok', False: 'missing'}

def runAviFolder(folder=".", pattern=None, overwrite=None):
    if pattern is None:
        pattern = "OP*"
    if overwrite is None:
        overwrite = False
    elif overwrite:
        pass
    elif overwrite == 'yes':
        overwrite = True
    else:
        overwrite = False

    subjs = glob.glob(os.path.join(folder, pattern))

    subjs = [(e, os.path.exists(os.path.join(e, 'subject.txt')), os.path.exists(os.path.join(e, 'dicom', 'DICOM-Report.txt')), os.path.exists(os.path.join(e, '4dfp', 'params'))) for e in subjs]

    do = []
    print "\n---=== Running Avi preprocessing on folder %s ===---\n" % (folder)
    print "List of subjects to process\n"
    print "%-15s%-15s%-15s%-10s" % ("subject", "subject.txt", "DICOM-Report", "params")
    for subj, stxt, sdicom, sparam in subjs:
        print "%-15s%-15s%-15s%-10s --->" % (os.path.basename(subj), recode[stxt], recode[sdicom], recode[sparam]),
        if not stxt:
            print "skipping processing"
        else:
            if not sdicom:
                print "estimating TR as 2.49836",
            if not sparam:
                print "creating param file",
            elif overwrite:
                print "overwriting existing params file",
            else:
                print "working with exisiting params file",
            do.append(subj)
        print ""

    s = raw_input("\n===> Do we process the listed subjects? [y/n]: ")
    if s is not "y":
        print "===> Aborting processing\n\n"
        return

    for s in do:
        runAvi(s, overwrite)

    print "\n---=== Done Avi preprocessing on folder %s ===---\n" % (folder)



def runAvi(folder=".", overwrite=None):
    if overwrite is None:
        overwrite = False
    elif overwrite:
        pass
    elif overwrite == 'yes':
        overwrite = True
    else:
        overwrite = False

    print "\n---> processing subject %s" % (os.path.basename(folder))

    # ---> process subject.txt

    info, pref = g_mri.g_core.readSubjectData(os.path.join(folder,'subject.txt'))

    t1, t2, bold, raw, data, sid = False, False, [], False, False, False

    if not info:
        print "===> no data in subject.txt, skipping processing!"
        return

    for k, v in info[0].iteritems():
        if k == 'raw_data':
            raw = v
        elif k == 'data':
            data = v
        elif k == 'id':
            sid = v
        elif k.isdigit():
            if "T1" in v['name']:
                t1 = k
            elif "T2" in v['name']:
                t2 = k
            elif ("BOLD" in v['name'] and not "C-BOLD" in v['name']) or ("bold" in v['name']):
                bold.append(k)
    bold.sort()

    print "...  identified images: t1: %s, t2: %s, bold:" % (t1, t2), bold


    # ---- check for 4dfp folder

    if not os.path.exists(os.path.join(folder, '4dfp')):
        print "...  creating 4dfp folder"
        os.mkdir(os.path.join(folder, '4dfp'))

    # ---- check for params

    if overwrite or (not os.path.exists(os.path.join(folder, '4dfp', 'params'))):

        # ---- check for dicom and TR

        TR = None
        if os.path.exists(os.path.join(folder, 'dicom', 'DICOM-Report.txt')):
            with open(os.path.join(folder, 'dicom', 'DICOM-Report.txt')) as f:
                for line in f:
                    if ("BOLD" in line and not "C-BOLD" in line) or ("bold" in line):
                        m = re.search('TR +([0-9.]+),', line)
                        if m:
                            TR = m.group(1)
                            TR = float(TR)/1000
                            print "...  Extracted TR info from DICOM-Report, using TR of", TR
                            break
        if TR is None or TR == 0.0:
            "...  No DICOM-Report, assuming TR of 2.49836"
            TR = 2.49836

        # ---- create params content

        print "...  creating params file"
        params = template
        params = params.replace('{{data}}', data)
        params = params.replace('{{inpath}}', raw)
        params = params.replace('{{patid}}', sid)
        params = params.replace('{{TR}}', str(TR))
        if t1:
            params = params.replace('{{t1}}', t1+"-o.nii.gz")
        if t2:
            params = params.replace('{{t2}}', t2+"-o.nii.gz")
        params = params.replace('{{boldnums}}', " ".join(["%d" % (e) for e in range(1, len(bold)+1)]))
        params = params.replace('{{bolds}}', " ".join([e+".nii.gz" for e in bold]))

        pfile = open(os.path.join(folder, '4dfp', 'params'), 'w')
        print >> pfile, params
        pfile.close()

    else:
        print "...  using existing params file"


    # ---- check for existing BOLD data

    isthere, ismissing = [],[]
    for b in range(1,len(bold)+1):
        if os.path.exists(os.path.join(folder, '4dfp', 'bold'+str(b), sid+'_b'+str(b)+'_faln_dbnd_xr3d_atl.4dfp.img')):
            isthere.append(str(b))
        else:
            ismissing.append(str(b))

    if isthere:
        if overwrite:
            print "...  Some bolds exist and will be overwritten! [%s]" % (" ".join(isthere))
            if ismissing:
                print "...  Some bolds were missing! [%s]" % (" ".join(ismissing))
        else:
            if ismissing:
                print "...  Some bolds exist [%s], however some are missing [%s]!" % (" ".join(isthere), " ".join(ismissing))
                print "...  Skipping this subject!"
                return
            else:
                print "...  BOLD files are allready processed! [%s]" % (" ".join(isthere))
                print "...  Skipping this subject!"
                return

    # ---- run avi preprocessing

    logname = 'preprocess.'+datetime.datetime.now().strftime('%Y-%m-%d.%H.%m.%S')+".log"
    print "...  running Avi preprocessing, saving log to %s " % (logname)
    logfile = open(os.path.join(folder, '4dfp', logname), 'w')

    r = subprocess.call(['preproc_avi_nifti', os.path.join(folder, '4dfp', 'params')], stdout=logfile, stderr=subprocess.STDOUT)

    logfile.close()

    if r:
        print "...  WARNING: preproc_avi_nifti finished with errors, please check log file"
    else:
        print "...  preproc_avi_nifti finished successfully"





def map2PALS(volume, metric, atlas='711-2C', method='interpolated', mapping='afm'):

    methods = {'interpolated': 'METRIC_INTERPOLATED_VOXEL', 'maximum': 'METRIC_MAXIMUM_VOXEL', 'enclosing': 'METRIC_ENCLOSING_VOXEL', 'strongest': 'METRIC_STRONGEST_VOXEL', 'gaussian': 'METRIC_GAUSSIAN'}
    if method in methods:
        method = methods[method]

    volumes = volume.split()
    mapping = ['-metric-'+e for e in mapping.split()]

    metric = metric.replace('.metric', '') + '.metric'

    for volume in volumes:
        volume = volume.replace('.img', '').replace('.ifh', '').replace('.4dfp', '') + '.4dfp.ifh'
        for structure in ['LEFT', 'RIGHT']:
            print "---> mapping %s to PALS %s [%s %s %s]" % (volume, structure, atlas, method, " ".join(mapping))
            r = subprocess.call(['caret_command', '-volume-map-to-surface-pals', metric, metric, atlas, structure, method, volume] + mapping)




