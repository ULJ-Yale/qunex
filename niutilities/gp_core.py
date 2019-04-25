#!/usr/bin/env python2.7
# encoding: utf-8
"""
This file holds code for core support functions used by other code for
preprocessing and analysis. The functions are for internal use
and can not be called externaly.

Created by Grega Repovs on 2016-12-17.
Code split from dofcMRIp_core gCodeP/preprocess codebase.
Copyright (c) Grega Repovs. All rights reserved.
"""

import os
import os.path
import shutil
import re
import subprocess
import glob
import exceptions
import sys
import traceback
from datetime import datetime
import time
from g_img import *
from g_MeltMovFidl import *


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def print_exc_plus():
    """
    Print the usual traceback information, followed by a listing of all the
    local variables in each frame.
    """
    tb = sys.exc_info()[2]
    while 1:
        if not tb.tb_next:
            break
        tb = tb.tb_next
    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back
    stack.reverse()
    traceback.print_exc()
    print "Locals by frame, innermost last"
    for frame in stack:
        print
        print "Frame %s in %s at line %s" % (frame.f_code.co_name,
                                             frame.f_code.co_filename,
                                             frame.f_lineno)
        for key, value in frame.f_locals.items():
            print "\t%20s = " % key,
            # We have to be careful not to cause a new error in our error
            # printer! Calling str() on an unknown object could cause an
            # error we don't want.
            try:
                print value
            except:
                print "<ERROR WHILE PRINTING VALUE>"


class ExternalFailed(exceptions.Exception):
    def __init__(self, value="Got lost :-("):
        self.parameter = value

    def __str__(self):
        return self.parameter  # repr(self.parameter)


class NoSourceFolder(exceptions.Exception):
    def __init__(self, value="Got lost :-("):
        self.parameter = value

    def __str__(self):
        return self.parameter   # repr(self.parameter)


def getExtension(filetype):
    extensions = {'4dfp': '.4dfp.img', 'nifti': '.nii.gz', 'cifti': '.dtseries.nii', 'dtseries': '.dtseries.nii', 'ptseries': '.ptseries.nii'}
    return extensions[filetype]


def root4dfp(filename):
    filename = filename.replace('.img', '')
    filename = filename.replace('.4dfp', '')
    return filename


def useOrSkipBOLD(sinfo, options, r=None):
    """
    useOrSkipBOLD
    Internal function to determine which bolds to use and which to skip.
    """
    bsearch  = re.compile('bold([0-9]+)')
    btargets = [e.strip() for e in re.split(" +|\||, *", options['bolds'])]
    bolds    = [(int(bsearch.match(v['name']).group(1)), v['name'], v['task'], v) for (k, v) in sinfo.iteritems() if k.isdigit() and bsearch.match(v['name'])]
    bskip    = []
    if "all" not in btargets:
        bskip = [(n, b, t, v) for n, b, t, v in bolds if t not in btargets and str(n) not in btargets]
        bolds = [(n, b, t, v) for n, b, t, v in bolds if t in btargets or str(n) in btargets]
        bskip.sort()
        if r is not None:
            if len(bskip) > 0:
                r += "\n\nSkipping the following BOLD images:"
                for n, b, t, v in bskip:
                    r += "\n...  %-6s [%s]" % (b, t)
                r += "\n"
    bolds.sort()

    return bolds, bskip, len(bskip), r



def getExactFile(candidate):
    g = glob.glob(candidate)
    if len(g) == 1:
        return g[0]
    elif len(g) > 1:
        return g[0]
        print "WARNING: there are %d files matching %s" % (len(g), candidate)
    else:
        # print "WARNING: there are no files matching %s" % (candidate)
        return ''


def getFileNames(sinfo, options):
    """
    getFileNames - documentation not yet available.
    """

    d = getSubjectFolders(sinfo, options)

    rgss = options['bold_nuisance']
    rgss = rgss.translate(None, ' ,;|')

    concroot = options['boldname'] + '_'
    fformat  = options['image_target'] + '_'

    # --- structural images

    f = {}

    f['t1_source']          = getExactFile(os.path.join(d['s_source'], options['path_t1']))

    ext = getExtension(options['image_target'].replace('cifti', 'nifti'))

    f['t1']                 = os.path.join(d['s_struc'], 'T1' + ext)

    f['t1_brain']           = os.path.join(d['s_struc'], 'T1_brain' + ext)
    f['t1_seg']             = os.path.join(d['s_struc'], 'T1_seg' + ext)
    f['bold_template']      = os.path.join(d['s_struc'], 'BOLD_template' + ext)

    f['fs_aseg_t1']         = os.path.join(d['s_fs_mri'], 'aseg_t1' + ext)
    f['fs_aseg_bold']       = os.path.join(d['s_fs_mri'], 'aseg_bold' + ext)

    f['fs_aparc_t1']        = os.path.join(d['s_fs_mri'], 'aparc+aseg_t1' + ext)
    f['fs_aparc_bold']      = os.path.join(d['s_fs_mri'], 'aparc+aseg_bold' + ext)

    f['fs_lhpial']          = os.path.join(d['s_fs_surf'], 'lh.pial')

    f['conc']               = os.path.join(d['s_bold_concs'], concroot + fformat + options['event_file'] + '.conc')
    f['conc_final']         = os.path.join(d['s_bold_concs'], concroot + fformat + options['event_file'] + options['bold_prefix'] + '.conc')

    for ch in options['bold_actions']:
        if ch == 's':
            f['conc_final'] = f['conc_final'].replace('.conc', '_g7.conc')
        elif ch == 'h':
            f['conc_final'] = f['conc_final'].replace('.conc', '_hpss.conc')
        elif ch == 'r':
            f['conc_final'] = f['conc_final'].replace('.conc', '_res-' + rgss + '.conc')
        elif ch == 'l':
            f['conc_final'] = f['conc_final'].replace('.conc', '_lpss.conc')

    # --- Freesurfer preprocessing "internals"

    f['fs_morig_mgz']       = os.path.join(d['s_fs_orig'], '001.mgz')
    f['fs_morig_nii']       = os.path.join(d['s_fs_orig'], '001.nii')

    # --- legacy paths and Freesurfer preprocessing "internals"

    f['m111']               = os.path.join(d['s_struc'], 'mprage_111.4dfp.img')
    f['m111_nifti']         = os.path.join(d['s_struc'], 'mprage_111_flip.4dfp.nii.gz')
    f['m111_brain_nifti']   = os.path.join(d['s_struc'], 'mprage_111_brain_flip.4dfp.nii.gz')
    f['m111_seg_nifti']     = os.path.join(d['s_struc'], 'mprage_111_brain_flip_seg.nii.gz')
    f['m111_brain']         = os.path.join(d['s_struc'], 'mprage_111_brain.4dfp.img')
    f['m111_seg']           = os.path.join(d['s_struc'], 'mprage_111_seg.4dfp.img')

    f['fs_aseg_mgz']        = os.path.join(d['s_fs_mri'], 'aseg.mgz')
    f['fs_aseg_nii']        = os.path.join(d['s_fs_mri'], 'aseg.nii')
    f['fs_aseg_analyze']    = os.path.join(d['s_fs_mri'], 'aseg.img')
    f['fs_aseg_4dfp']       = os.path.join(d['s_fs_mri'], 'aseg.4dfp.img')
    f['fs_aseg_111']        = os.path.join(d['s_fs_mri'], 'aseg_111.4dfp.img')
    f['fs_aseg_333']        = os.path.join(d['s_fs_mri'], 'aseg_333.4dfp.img')
    f['fs_aseg_111_nii']    = os.path.join(d['s_fs_mri'], 'aseg_111.nii.gz')
    f['fs_aseg_333_nii']    = os.path.join(d['s_fs_mri'], 'aseg_333.nii.gz')

    f['fs_aparc+aseg_mgz']        = os.path.join(d['s_fs_mri'], 'aparc+aseg.mgz')
    f['fs_aparc+aseg_nii']        = os.path.join(d['s_fs_mri'], 'aparc+aseg.nii')
    f['fs_aparc+aseg_3d_nii']     = os.path.join(d['s_fs_mri'], 'aparc+aseg_3d.nii')
    f['fs_aparc+aseg_analyze']    = os.path.join(d['s_fs_mri'], 'aparc+aseg.img')
    f['fs_aparc+aseg_4dfp']       = os.path.join(d['s_fs_mri'], 'aparc+aseg.4dfp.img')
    f['fs_aparc+aseg_111']        = os.path.join(d['s_fs_mri'], 'aparc+aseg_111.4dfp.img')
    f['fs_aparc+aseg_333']        = os.path.join(d['s_fs_mri'], 'aparc+aseg_333.4dfp.img')
    f['fs_aparc+aseg_111_nii']    = os.path.join(d['s_fs_mri'], 'aparc+aseg_111.nii.gz')
    f['fs_aparc+aseg_333_nii']    = os.path.join(d['s_fs_mri'], 'aparc+aseg_333.nii.gz')

    # --- convert legacy paths (create hard links)

    if options['image_target'] == '4dfp':

        # ---> BET & FAST

        if os.path.exists(f['m111_brain']) and not os.path.exists(f['t1_brain']):
            os.link(f['m111_brain'], f['t1_brain'])

        if os.path.exists(f['m111_seg']) and not os.path.exists(f['t1_seg']):
            os.link(f['m111_seg'], f['t1_seg'])

        # ---> FreeSurfer

        if os.path.exists(f['fs_aseg_111']) and not os.path.exists(f['fs_aseg_t1']):
            os.link(f['fs_aseg_111'], f['fs_aseg_t1'])
        if os.path.exists(f['fs_aseg_111'].replace('.img', '.ifh')) and not os.path.exists(f['fs_aseg_t1'].replace('.img', '.ifh')):
            os.link(f['fs_aseg_111'].replace('.img', '.ifh'), f['fs_aseg_t1'].replace('.img', '.ifh'))

        if os.path.exists(f['fs_aseg_333']) and not os.path.exists(f['fs_aseg_bold']):
            os.link(f['fs_aseg_333'], f['fs_aseg_bold'])
        if os.path.exists(f['fs_aseg_333'].replace('.img', '.ifh')) and not os.path.exists(f['fs_aseg_bold'].replace('.img', '.ifh')):
            os.link(f['fs_aseg_333'].replace('.img', '.ifh'), f['fs_aseg_bold'].replace('.img', '.ifh'))

        if os.path.exists(f['fs_aparc+aseg_111']) and not os.path.exists(f['fs_aparc_t1']):
            os.link(f['fs_aparc+aseg_111'], f['fs_aparc_t1'])
        if os.path.exists(f['fs_aparc+aseg_111'].replace('.img', '.ifh')) and not os.path.exists(f['fs_aparc_t1'].replace('.img', '.ifh')):
            os.link(f['fs_aparc+aseg_111'].replace('.img', '.ifh'), f['fs_aparc_t1'].replace('.img', '.ifh'))

        if os.path.exists(f['fs_aparc+aseg_333']) and not os.path.exists(f['fs_aparc_bold']):
            os.link(f['fs_aparc+aseg_333'], f['fs_aparc_bold'])
        if os.path.exists(f['fs_aparc+aseg_333'].replace('.img', '.ifh')) and not os.path.exists(f['fs_aparc_bold'].replace('.img', '.ifh')):
            os.link(f['fs_aparc+aseg_333'].replace('.img', '.ifh'), f['fs_aparc_bold'].replace('.img', '.ifh'))

    return f


def getBOLDFileNames(sinfo, boldname, options):
    """
    getBOLDFileNames - documentation not yet available.
    """
    d = getSubjectFolders(sinfo, options)
    f = {}

    if 'bold_tail' not in options:
        options['bold_tail'] = ""

    boldnumber = boldname.replace(options['boldname'], '')
    ext = getExtension(options['image_target'])

    # print "root", root, "--- options boldname", options['boldname'], '--- boldname', boldname, '--- ext', ext

    rgss = options['bold_nuisance']
    rgss = rgss.translate(None, ' ,;|')

    if 'path_' + boldname in options:
        f['bold_source']        = getExactFile(os.path.join(d['s_source'], options['path_' + boldname]))
    else:
        btarget                 = options['path_bold'].replace('[N]', boldnumber)
        f['bold_source']        = getExactFile(os.path.join(d['s_source'], btarget))

    # --- alternative check for 4dfp preprocessing

    if f['bold_source'] == '' and options['image_target'] == '4dfp':
        # print "Searching in the atlas folder ..."
        f['bold_source']        = getExactFile(os.path.join(d['s_source'], 'atlas', '*b' + boldnumber + '_faln_dbnd_xr3d_atl.4dfp.img'))

    # --- bold masks

    f['bold1']                  = os.path.join(d['s_boldmasks'], boldname + '_frame1' + ext)
    f['bold1_brain']            = os.path.join(d['s_boldmasks'], boldname + '_frame1_brain' + ext)
    f['bold1_brain_mask']       = os.path.join(d['s_boldmasks'], boldname + '_frame1_brain_mask' + ext)

    # --- bold masks internals

    f['bold1_nifti']            = os.path.join(d['s_boldmasks'], boldname + '_frame1_flip.4dfp.nii.gz')
    f['bold1_brain_nifti']      = os.path.join(d['s_boldmasks'], boldname + '_frame1_brain_flip.4dfp.nii.gz')
    f['bold1_brain_mask_nifti'] = os.path.join(d['s_boldmasks'], boldname + '_frame1_brain_flip.4dfp_mask.nii.gz')

    f['bold_n_png']             = os.path.join(d['s_nuisance'], boldname + '_nuisance.png')

    # --- movement files

    movname = boldname.replace(options['boldname'], 'mov')
    if 'path_' + movname in options:
        f['bold_mov_o']        = getExactFile(os.path.join(d['s_source'], options['path_' + movname]))
    else:
        mtarget                = options['path_mov'].replace('[N]', boldnumber)
        f['bold_mov_o']        = getExactFile(os.path.join(d['s_source'], mtarget))

    f['bold_mov']              = os.path.join(d['s_bold_mov'], boldname + '_mov.dat')

    # --- event files

    if 'e' in options['bold_nuisance']:
        f['bold_event_o']       = os.path.join(d['s_source'], boldname + options['event_file'])
        f['bold_event_a']       = os.path.join(options['subjectsfolder'], 'inbox', sinfo['id'] + "_" + boldname + options['event_file'])
        f['bold_event']         = os.path.join(d['s_bold_events'], boldname + options['event_file'])

    # --- bold preprocessed files

    f['bold']                   = os.path.join(d['s_bold'], boldname + options['bold_tail'] + ext)
    f['bold_final']             = os.path.join(d['s_bold'], boldname + options['bold_prefix'] + options['bold_tail'] + ext)
    f['bold_stats']             = os.path.join(d['s_bold_mov'], boldname + '.bstats')
    f['bold_nuisance']          = os.path.join(d['s_bold_mov'], boldname + '.nuisance')
    f['bold_scrub']             = os.path.join(d['s_bold_mov'], boldname + '.scrub')

    f['bold_vol']               = os.path.join(d['s_bold'], boldname + '.nii.gz')
    f['bold_dts']               = os.path.join(d['s_bold'], boldname + options['hcp_cifti_tail'] + '.dtseries.nii')
    f['bold_pts']               = os.path.join(d['s_bold'], boldname + options['hcp_cifti_tail'] + '.ptseries.nii')

    for ch in options['bold_actions']:
        if ch == 's':
            f['bold_final'] = f['bold_final'].replace(ext, '_g7' + ext)
        elif ch == 'h':
            f['bold_final'] = f['bold_final'].replace(ext, '_hpss' + ext)
        elif ch == 'c':
            f['bold_coef']  = f['bold_final'].replace(ext, '_coeff' + ext)
        elif ch == 'r':
            f['bold_final'] = f['bold_final'].replace(ext, '_res-' + rgss + options['glm_name'] + ext)
        elif ch == 'l':
            f['bold_final'] = f['bold_final'].replace(ext, '_lpss' + ext)

    return f


def findFile(sinfo, options, fname):
    """
    findFile - documentation not yet available.
    """
    d = getSubjectFolders(sinfo, options)

    tfile = os.path.join(d['inbox'], "%s_%s" % (sinfo['id'], fname))
    if os.path.exists(tfile):
        return tfile

    if any([e in fname for e in ['conc', 'fidl']]):
        tfile = os.path.join(d['inbox'], 'events', "%s_%s" % (sinfo['id'], fname))
        if os.path.exists(tfile):
            return tfile

    if any([e in fname for e in ['conc']]):
        tfile = os.path.join(d['inbox'], 'concs', "%s_%s" % (sinfo['id'], fname))
        if os.path.exists(tfile):
            return tfile

    tfile = os.path.join(d['s_source'], fname)
    if os.path.exists(tfile):
        return tfile

    tfile = os.path.join(d['s_source'], "%s_%s" % (sinfo['id'], fname))
    if os.path.exists(tfile):
        return tfile

    return False


def getSubjectFolders(sinfo, options):
    """
    getSubjectFolders - documentation not yet available.
    """
    d = {}

    if options['image_source'] == 'hcp':
        d['s_source'] = sinfo['hcp']
    else:
        d['s_source'] = sinfo['data']

    if options['hcp_bold_variant'] == "":
        bvar = ''
    else:
        bvar = '.' + options['hcp_bold_variant']

    if "hcp" in sinfo:
        d['hcp'] = os.path.join(sinfo['hcp'], sinfo['id'])

    d['s_base']             = os.path.join(options['subjectsfolder'], sinfo['id'])
    d['s_images']           = os.path.join(d['s_base'], 'images')
    d['s_struc']            = os.path.join(d['s_images'], 'structural')
    d['s_seg']              = os.path.join(d['s_images'], 'segmentation')
    d['s_boldmasks']        = os.path.join(d['s_seg'], 'boldmasks' + bvar)
    d['s_bold']             = os.path.join(d['s_images'], 'functional' + bvar)
    d['s_bold_mov']         = os.path.join(d['s_bold'], 'movement')
    d['s_bold_events']      = os.path.join(d['s_bold'], 'events')
    d['s_bold_concs']       = os.path.join(d['s_bold'], 'concs')
    d['s_bold_glm']         = os.path.join(d['s_bold'], 'glm')
    d['s_roi']              = os.path.join(d['s_images'], 'ROI')
    d['s_nuisance']         = os.path.join(d['s_roi'], 'nuisance' + bvar)
    d['s_fs']               = os.path.join(d['s_seg'], 'freesurfer')
    d['s_hcp']              = os.path.join(d['s_seg'], 'hcp')
    d['s_s32k']             = os.path.join(d['s_hcp'], 'fsaverage_LR32k')
    d['s_fs_mri']           = os.path.join(d['s_fs'], 'mri')
    d['s_fs_orig']          = os.path.join(d['s_fs'], 'mri/orig')
    d['s_fs_surf']          = os.path.join(d['s_fs'], 'surf')
    d['inbox']              = os.path.join(options['subjectsfolder'], 'inbox')

    d['qc']                 = os.path.join(options['subjectsfolder'], 'QC')
    d['qc_mov']             = os.path.join(d['qc'], 'movement' + bvar)

    if not os.path.exists(d['s_source']) and options['source_folder']:
        print "WARNING: Source folder not found, waiting 15s to give it a chance to come online!"
        time.sleep(15)
        if not os.path.exists(d['s_source']):
            print "WARNING: Source folder still not found, if data has not been copied over the processing will fail!"
            # errormessage = "\n... ERROR: Source folder does not exist or is not reachable [%s]" % (d['s_source'])
            # raise NoSourceFolder(errormessage)

    for (key, fpath) in d.iteritems():
        if key != 's_source':
            if not os.path.exists(fpath):
                try:
                    os.makedirs(fpath)
                except:
                    print "ERROR: Could not create folder %s! Please check paths and permissions!" % (fpath)
                    raise

    return d


def readSubjectData(filename):
    """
    readSubjectData - documentation not yet available.
    """

    if not os.path.exists(filename):
        print "\n\n=====================================================\nERROR: Batch file does not exist [%s]" % (filename)
        raise ValueError("ERROR: Batch file not found: %s" % (filename))

    s = file(filename).read()
    s = s.replace("\r", "\n")
    s = s.replace("\n\n", "\n")
    s = re.sub("^#.*?\n", "", s)

    s = s.split("\n---")
    s = [e for e in s if len(e) > 10]

    nsearch = re.compile('(.*?)\((.*)\)')
    csearch = re.compile('c([0-9]+)$')

    slist = []
    gpref = {}

    c = 0
    try:
        for sub in s:
            sub = sub.split('\n')
            sub = [e.strip() for e in sub]
            sub = [e for e in sub if len(e) > 0]
            sub = [e for e in sub if e[0] != "#"]

            dic = {}
            image = {}
            for line in sub:
                c += 1
                line = line.split(':')
                line = [e.strip() for e in line]

                # --- read global preferences / settings

                if len(line[0]) > 0:
                    if line[0][0] == "_":
                        gpref[line[0][1:]] = line[1]
                        continue

                # --- read ima data

                if line[0].isdigit():
                    image = {}
                    image['ima'] = line[0]
                    for e in line:
                        m = nsearch.match(e)
                        if m:
                            image[m.group(1)] = m.group(2)
                            line.remove(e)

                    ni = len(line)
                    if ni > 1:
                        image['name'] = line[1]
                    if ni > 2:
                        image['task'] = line[2]
                    if ni > 3:
                        for n in range(3, ni):
                            if '>' in line[n]:
                                kv = line[n].split('>')
                                image[kv[0].strip()] = kv[1].strip()
                    dic[line[0]] = image


                # --- read conc data

                elif csearch.match(line[0]):
                    conc = {}
                    conc['cnum'] = line[0]
                    for e in line:
                        m = nsearch.match(e)
                        if m:
                            conc[m.group(1)] = m.group(2)
                            line.remove(e)

                    ni = len(line)
                    if ni < 3:
                        print "Missing data for conc entry!"
                        raise AssertionError('Not enough values in conc definition line!')

                    conc['label'] = line[1]
                    conc['conc']  = line[2]
                    conc['fidl']  = line[3]
                    dic[line[0]]  = conc

                # --- read rest of the data

                else:
                    dic[line[0]] = line[1]

            if len(dic) > 0:
                if "id" not in dic:
                    print "WARNING: There is a record missing an id field and is being omitted from processing.", dic
                elif "data" not in dic and "hcp" not in dic:
                    print "WARNING: Session %s is missing a data field and is being omitted from processing." % (dic['id'])
                else:
                    slist.append(dic)

    except:
        print "\n\n=====================================================\nERROR: There was an error with the batch.txt file in line %d:\n---> %s\n\n--------\nError raised:\n" % (c, line)
        raise

    return slist, gpref


def linkOrCopy(source, target, r=None, status=None, name=None, prefix=None):
    """
    linkOrCopy - documentation not yet available.
    """
    if status is None:
        status = True
    if name is None:
        name = "file"
    if prefix is None:
        prefix = "\n ... "
    if os.path.exists(source):
        try:
            if os.path.exists(target):
                if os.path.samefile(source, target):
                    if r is None:
                        return status and True
                    else:
                        return (status and True, "%s%s%s already mapped" % (r, prefix, name))
                else:
                    os.remove(target)
            os.link(source, target)
            if r is None:
                return status and True
            else:
                return (status and True, "%s%s%s mapped" % (r, prefix, name))
        except:
            try:
                shutil.copy2(source, target)
                if r is None:
                    return status and True
                else:
                    return (status and True, "%s%s%s copied" % (r, prefix, name))
            except:
                if r is None:
                    return False
                else:
                    return (False, "%s%sERROR: %s could not be copied, check permissions! " % (r, prefix, name))
        return True
    else:
        if r is None:
            return False
        else:
            return (False, "%s%sERROR: %s could not be copied, source file does not exist [%s]! " % (r, prefix, name, source))


def runExternalForFile(checkfile, run, description, overwrite=False, thread="0", remove="true", task=None, logfolder="", logtags=""):
    """
    runExternalForFile - documentation not yet available.
    """
    if overwrite or not os.path.exists(checkfile):

        r = '\n%s' % (description)

        if isinstance(logtags, basestring):
            logtags = [logtags]

        logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%s")
        logname  = [task] + logtags + [thread, logstamp]
        logname  = [e for e in logname if e]
        logname  = "_".join(logname)

        tmplogfile  = os.path.join(logfolder, "tmp_%s.log" % (logname))
        donelogfile = os.path.join(logfolder, "done_%s.log" % (logname))
        errlogfile  = os.path.join(logfolder, "error_%s.log" % (logname))

        nf = open(tmplogfile, 'w')
        print >> nf, "\n#-------------------------------\n# Running: %s\n# Command: %s\n# Test file: %s\n#-------------------------------" % (run, description, checkfile)

        if not os.path.exists(tmplogfile):
            r = "\n\nERROR: could not create a temporary log file %s!" % (tmplogfile)
            raise ExternalFailed(r)

        try:
            ret = subprocess.call(run.split(), stdout=nf, stderr=nf)
        except:
            nf.close()
            shutil.move(tmplogfile, errlogfile)
            r = "\n\nERROR: Running external command failed! \nTry running the command directly for more detailed error information: \n%s\n" % (run)
            raise ExternalFailed(r)

        if ret or not os.path.exists(checkfile):
            r = "\n\nERROR: %s failed with error %s\n... \ncommand executed:\n %s\n" % (r, ret, run)
            nf.close()
            shutil.move(tmplogfile, errlogfile)
            raise ExternalFailed(r)

        print >> nf, "\n\n===> Successful completion of task\n"
        nf.close()
        if remove:
            os.remove(tmplogfile)
        else:
            shutil.move(tmplogfile, donelogfile)
        r += ' --- done'

    else:
        # if os.path.getsize(checkfile) < 50000:
        #     r = runExternalForFile(checkfile, run, description, overwrite=True, thread=thread)
        # else:
        r = '\n%s --- already completed' % (description)

    return r


def runExternalForFileShell(checkfile, run, description, overwrite=False, thread="0", remove=True, task=None, logfolder="", logtags=""):
    """
    runExternalForFileShell - documentation not yet available.
    """
    if overwrite or not os.path.exists(checkfile):
        r = '\n\n%s' % (description)

        if isinstance(logtags, basestring) or logtags is None:
            logtags = [logtags]

        logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%s")
        logname  = [task] + logtags + [thread, logstamp]
        logname  = [e for e in logname if e]
        logname  = "_".join(logname)

        tmplogfile  = os.path.join(logfolder, "tmp_%s.log" % (logname))
        donelogfile = os.path.join(logfolder, "done_%s.log" % (logname))
        errlogfile  = os.path.join(logfolder, "error_%s.log" % (logname))

        nf = open(tmplogfile, 'w')
        print >> nf, "\n#-------------------------------\n# Running: %s\n# Command: %s\n# Test file: %s\n#-------------------------------" % (run, description, checkfile)

        ret = subprocess.call(run, shell=True, stdout=nf, stderr=nf, executable='/bin/csh')
        if ret:
            r = "\n\nERROR: %s failed with error %s\n... \ncommand executed:\n %s\n" % (r, ret, run)
            nf.close()
            shutil.move(tmplogfile, errlogfile)
            raise ExternalFailed(r)
        elif not os.path.exists(checkfile):
            r += "\n\nWARNING: Expected file [%s] not present after running the external command!\nTry running the command directly for more detailed error information:\n--> %s\n" % (checkfile, run)
            nf.close()
            shutil.move(tmplogfile, errlogfile)
        else:
            print >> nf, "\n\n===> Successful completion of task\n"
            nf.close()
            if remove:
                os.remove(tmplogfile)
            else:
                shutil.move(tmplogfile, donelogfile)
            r += ' --- done'
    else:
        if os.path.getsize(checkfile) < 100:
            r = runExternalForFileShell(checkfile, run, description, overwrite=True, thread=thread, task=task, logfolder=logfolder, logtags=logtags)
        else:
            r = '\n%s --- already completed' % (description)

    return r


def runScriptThroughShell(run, description, thread="0", remove=True, task=None, logfolder="", logtags=""):
    """
    runScriptThroughShell - documentation not yet available.
    """
    
    r = '\n\n%s' % (description)

    if isinstance(logtags, basestring):
        logtags = [logtags]

    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%s")
    logname  = [task] + logtags + [thread, logstamp]
    logname  = [e for e in logname if e]
    logname  = "_".join(logname)

    tmplogfile  = os.path.join(logfolder, "tmp_%s.log" % (logname))
    donelogfile = os.path.join(logfolder, "done_%s.log" % (logname))
    errlogfile  = os.path.join(logfolder, "error_%s.log" % (logname))

    nf = open(tmplogfile, 'w')
    print >> nf, "\n#-------------------------------\n# Running: %s\n#-------------------------------" % (description)

    ret = subprocess.call(run, shell=True, stdout=nf, stderr=nf)
    if ret:
        r += "\n\nERROR: Failed with error %s\n" % (ret)
        nf.close()
        shutil.move(tmplogfile, errlogfile)
        raise ExternalFailed(r)
    else:
        print >> nf, "\n\n===> Successful completion of task\n"
        nf.close()
        if remove:
            os.remove(tmplogfile)
        else:
            shutil.move(tmplogfile, donelogfile)
        r += ' --- done'

    return r



def checkForFile(r, checkfile, message, status=True):
    """
    checkForFile - documentation not yet available.
    """
    if not os.path.exists(checkfile):
        status = False
        r = r + '\n... %s' % (message)
    return r, status


def checkForFile2(r, checkfile, ok, bad, status=True):
    """
    checkForFile2 - documentation not yet available.
    """
    if os.path.exists(checkfile):
        r += ok
        return r, status
    else:
        r += bad
        return r, False


def action(action, run):
    '''
    action(action, run)
    A function that prepends "test" to action name if run is set to "test".
    '''
    if run == "test":
        if action.istitle():
            return "Test " + action.lower()
        else:
            return "test " + action
    else:
        return action