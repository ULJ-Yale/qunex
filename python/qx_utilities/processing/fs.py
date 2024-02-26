#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``fs.py``

This file holds code for running legacy FreeSurfer preprocessing on NIL
preprocessed images. The specific functions are:

--runBasicStructuralSegmentation
--checkForFreeSurferData
--runFreeSurferFullSegmentation
--runFreeSurferSubcorticalSegmentation

All the functions are part of the processing suite. They should be called
from the command line using `gmri` command. Help is available through:

- `gmri ?<command>` for command specific help
- `gmri -o` for a list of relevant arguments and options
"""

"""
Created by Grega Repovs on 2016-12-17.
Code split from dofcMRIp_core gCodeP/preprocess codebase.
Copyright (c) Grega Repovs. All rights reserved.
"""

import os
import shutil
import traceback
import time
from datetime import datetime

import general.img as gi
import general.core as gc
from processing.core import *

def runBasicStructuralSegmentation(sinfo, options, overwrite=False, thread=0):
    """
    runBasicStructuralSegmentation - documentation not yet available.
    """

    f = getFileNames(sinfo, options)
    r = "\n---------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\nRunning basic structural segmentation ..."

    try:
        # --- copy structurals over

        copy = True
        if os.path.exists(f['t1']):
            copy = False

        if overwrite or copy:
            if f['t1_source'] is None:
                raise NoSourceFolder("ERROR: Data source folder is not set. Please check your paths!")
            r += '\n... copying %s' % (f['t1_source'])
            if options['image_target'] == '4dfp':
                if gi.getImgFormat(f['t1_source']) == '.4dfp.img':
                    shutil.copy2(f['t1_source'], f['t1'])
                    shutil.copy2(f['t1_source'].replace('.img', '.ifh'), f['t1'].replace('.img', '.ifh'))
                else:
                    tmpfile = f['t1'].replace('.4dfp.img', gi.getImgFormat(f['t1_source']))
                    shutil.copy2(f['t1_source'], tmpfile)
                    r, endlog, status, failed = runExternalForFile(f['t1'], 'g_FlipFormat %s %s' % (tmpfile, f['t1'].replace('.img', '.ifh')), '... converting %s to 4dfp' % (os.path.basename(tmpfile)), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
                    os.remove(tmpfile)
            if options['image_target'] == 'nifti':
                if gi.getImgFormat(f['t1_source']) == '.4dfp.img':
                    tmpimg = f['t1'] + '.4dfp.img'
                    tmpifh = f['t1'] + '.4dfp.ifh'
                    shutil.copy2(f['t1_source'], tmpimg)
                    shutil.copy2(f['t1_source'].replace('.img', '.ifh'), tmpifh)
                    r, endlog, status, failed = runExternalForFile(f['t1'], 'g_FlipFormat %s %s' % (tmpifh, f['t1'].replace('.img', '.ifh')), '... converting %s to NIfTI' % (os.path.basename(tmpimg)), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
                    os.remove(tmpimg)
                    os.remove(tmpifh)
                else:
                    if gi.getImgFormat(f['t1_source']) == '.nii.gz':
                        tmpfile = f['t1'] + ".gz"
                        shutil.copy2(f['t1_source'], tmpfile)
                        r, endlog, status, failed = runExternalForFile(f['t1'], 'gunzip -f %s' % (tmpfile), '... gunzipping %s' % (os.path.basename(tmpfile)), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
                        if os.path.exists(tmpfile):
                            os.remove(tmpfile)
                    else:
                        shutil.copy2(f['t1_source'], f['t1'])

        else:
            r += '\n... %s file present' % (f['t1'])

        # --- convert to NIfTI

        sfile = f['t1']
        tfileb = f['t1_brain'].replace(gi.getImgFormat(f['t1_brain']), '.nii')
        tfiles = f['t1_seg'].replace(gi.getImgFormat(f['t1_seg']), '.nii')

        if gi.getImgFormat(f['t1']) == '.4dfp.img':
            sfile = sfile.replace('.4dfp.img', '.nii')
            r, endlog, status, failed = runExternalForFile(sfile, 'g_FlipFormat %s %s' % (f['t1'].replace('.img', '.ifh'), sfile), '... converting %s to NIfTI' % (os.path.basename(f['t1'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

        # --- run BET

        if os.path.exists(tfileb):
            r += "\n... bet on %s already done" % (os.path.basename(sfile))
        else:
            r, endlog, status, failed = runExternalForFile(tfileb + '.gz', 'bet %s %s %s' % (sfile, tfileb, options['bet']), '... running BET on %s with options %s' % (os.path.basename(sfile), options['bet']), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
            r, endlog, status, failed = runExternalForFile(tfileb, 'gunzip -f %s.gz' % (tfileb), 'gunzipping %s.gz' % (os.path.basename(tfileb)), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

        # --- run FAST

        if os.path.exists(tfiles):
            r += "\n... fast on %s already done" % (os.path.basename(tfiles))
        else:
            r, endlog, status, failed = runExternalForFile(tfiles + '.gz', 'fast %s -o %s %s' % (options['fast'], tfiles.replace('_seg.nii', ''), tfileb), '... running FAST on %s with options %s' % (os.path.basename(tfileb), options['fast']), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
            r, endlog, status, failed = runExternalForFile(tfiles, 'gunzip -f %s.gz' % (tfiles), '... gunzipping %s.gz' % (os.path.basename(tfiles)), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

        # --- convert to 4dfp if needed

        if gi.getImgFormat(f['t1']) == '.4dfp.img':
            r, endlog, status, failed = runExternalForFile(f['t1_brain'], 'g_FlipFormat %s %s' % (tfileb, f['t1_brain'].replace('.img', '.ifh')), '... converting %s to 4dfp' % (os.path.basename(tfileb)), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
            r, endlog, status, failed = runExternalForFile(f['t1_seg'], 'g_FlipFormat %s %s' % (tfiles, f['t1_seg'].replace('.img', '.ifh')), '... converting %s to 4dfp' % (os.path.basename(tfiles)), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)


    except (ExternalFailed, NoSourceFolder) as errormessage:
        r += str(errormessage)
        r += "\nBasic structural segmentation failed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        print(r)
        return r
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        time.sleep(15)
        print(r)
        return r

    r += "\nBasic structural segmentation completed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print(r)
    return r


#
#   --- Check for existing FreeSurfer data
#

def checkForFreeSurferData(sinfo, options, overwrite=False, thread=0, r=False):
    """
    checkForFreeSurferData - documentation not yet available.
    """

    if not r:
        verbose = True
    else:
        verbose = False

    def checkPath(p, sid):
        p = p.replace("[sid]", sid)
        if os.path.exists(p):
            return p
        else:
            if d['s_source'] is not None:
                tp = os.path.join(d['s_source'], p)
                if os.path.exists(tp):
                    return tp
            elif "path_freesurfer" in options:
                tf = options['path_freesurfer'].replace("[sid]", sid)
                tp = os.path.join(tf, p)
                if os.path.exists(tp):
                    return tp
        return False

    try:
        d = getSessionFolders(sinfo, options)
        f = getFileNames(sinfo, options)

        if verbose:
            r = "\n---------------------------------------------------------"
            r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
            r += "\nChecking for existing freesurfer data ..."

        # check for freesurfer folder

        if not os.path.exists(f['fs_aseg_mgz']) or overwrite:
            if "path_freesurfer" in options:
                fspath = options["path_freesurfer"].replace("[sid]", sinfo['id'])
                r += "\n... looking for: %s" % (fspath)
                if os.path.exists(fspath):
                    if os.path.exists(d['s_fs']):
                        shutil.rmtree(d['s_fs'])
                    try:
                        shutil.copytree(fspath, d['s_fs'])
                    except:
                        r += "\n... copy reported an error, please check data!"
                    r += "\n... copied existing FreeSurfer data from %s to target folder" % (fspath)
            else:
                r += "\n... no freesurfer path in options."
        else:
            r += "\n... data already there."
        # check for specific freesurfer file options

        fsfiles = [("path_aseg_t1", "fs_aseg_t1"), ("path_aseg_bold", "fs_aseg_bold"), ("path_aparc_t1", "fs_aparc_t1"), ("path_aparc_bold", "fs_aparc_bold")]
        for s, t in fsfiles:
            if not os.path.exists(f[t]) or overwrite:
                if s in options:
                    sf = checkPath(options[s], sinfo['id'])
                    if sf:
                        tf = f[t].replace(gi.getImgFormat(f[t]), gi.getImgFormat(sf))
                        shutil.copy2(sf, tf)
                        if gi.getImgFormat(sf) == '.4dfp.img':
                            shutil.copy2(sf.replace('.img', '.ifh'), tf.replace('.img', '.ifh'))
                        r += "\n... copied %s to target folder" % (os.path.basename(sf))
                        if tf != f[t]:
                            if options['image_target'] == '4dfp':
                                r, endlog, status, failed = runExternalForFile(f[t], 'g_FlipFormat %s %s' % (tf, f[t].replace('.img', '.ifh')), '... converting %s to 4dfp' % (os.path.basename(tf)), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
                            elif gi.getImgFormat(tf) == '.nii.gz':
                                r, endlog, status, failed = runExternalForFile(f[t], 'gunzip -f %s' % (tf), '... gunzipping %s ' % (os.path.basename(tf)), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
                            else:
                                r, endlog, status, failed = runExternalForFile(f[t], 'g_FlipFormat %s %s' % (tf.replace('.img', '.ifh'), f[t]), '... converting %s to nifti' % (os.path.basename(tf)), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        time.sleep(1)
        print(r)
        return r

    if verbose:
        r += "\nCheck completed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        print(r)

    return r


#
#   --- Run FreeSurfer segmentation
#

def runFreeSurferFullSegmentation(sinfo, options, overwrite=False, thread=0):
    """
    runFreeSurferFullSegmentation - documentation not yet available.
    """

    try:

        r = "\n---------------------------------------------------------"
        r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        r += "\nRunning Full FreeSurfer segmentation ..."

        # check if any data already exists

        r = checkForFreeSurferData(sinfo, options, overwrite, thread, r)

        d = getSessionFolders(sinfo, options)
        f = getFileNames(sinfo, options)

        # --- check if we need to run fsf

        if (os.path.exists(f['fs_aseg_nii']) and os.path.exists(f['fs_aparc+aseg_nii'])) or (os.path.exists(f['fs_aseg_t1']) and os.path.exists(f['fs_aparc_t1'])):

            r += "\n... FreeSurfer run already completed!"

        else:

            # --- copy file over

            if not os.path.exists(f['t1']):
                shutil.copy2(f['t1_source'], f['t1'])
                if gi.getImgFormat(f['t1_source']) == '.4dfp.img':
                    shutil.copy2(f['t1_source'].replace('.img', '.ifh'), f['t1'].replace('.img', '.ifh'))
                r += "\n... copied %s to target folder" % (os.path.basename(f['t1_source']))


            # --- convert to NIfTI

            onifti = f['t1']
            if gi.getImgFormat(onifti) == '.4dfp.img':
                onifti = f['t1'].replace('.4dfp.img', '.nii')
                r, endlog, status, failed = runExternalForFile(onifti, 'g_FlipFormat %s %s' % (f['t1'].replace('.img', '.ifh'), onifti), '... converting %s to NIfTI' % (os.path.basename(f['t1'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

            # --- convert to MGZ

            r, endlog, status, failed = runExternalForFile(f['fs_morig_mgz'], 'mri_convert --in_type nii %s %s' % (onifti, f['fs_morig_mgz']), '... converting %s to MGZ' % (os.path.basename(onifti)), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

            # --- run FreeSurfer Subcortical

            r, endlog, status, failed = runExternalForFile(f['fs_aseg_mgz'], 'recon-all -sd %s -subjid freesurfer -motioncor -nuintensitycor -talairach -normalization -skullstrip -subcortseg -segstats -no-isrunning' % (d['s_seg']), '... running subcortical FreeSurfer segmentation', overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

            # --- run FreeSurfer surface registration

            r, endlog, status, failed = runExternalForFile(f['fs_aparc+aseg_mgz'], 'recon-all -sd %s -subjid freesurfer -maskbfs -normalization2 -segmentation -fill -tessellate -smooth1 -inflate1 -qsphere -fix -finalsurfs -smooth2 -inflate2 -cortribbon -sphere -surfreg -contrasurfreg -avgcurv -cortparc -parcstats -cortparc2 -parcstats2 -aparc2aseg -no-isrunning' % (d['s_seg']), '... running FreeSurfer surface processing', overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

            # --- convert segmentations to nifti

            r, endlog, status, failed = runExternalForFile(f['fs_aseg_nii'], 'mri_convert -i %s -ot nii %s' % (f['fs_aseg_mgz'], f['fs_aseg_nii']), '... converting %s to NIfTI' % (f['fs_aseg_mgz']), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
            r, endlog, status, failed = runExternalForFile(f['fs_aparc+aseg_nii'], 'mri_convert -i %s -ot nii %s' % (f['fs_aparc+aseg_mgz'], f['fs_aparc+aseg_nii']), '... converting %s to NIfTI' % (f['fs_aparc+aseg_mgz']), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)


        if options['image_target'] == 'nifti':
            if not os.path.exists(f['fs_aseg_t1']):
                gc.link_or_copy(f['fs_aseg_nii'], f['fs_aseg_t1'])
            if not os.path.exists(f['fs_aparc_t1']):
                gc.link_or_copy(f['fs_aparc+aseg_nii'], f['fs_aparc_t1'])

        # --- 4dfp path

        if options['image_target'] == '4dfp' or options['image_atlas'] == '711':

            # --- check for aseg

            if not os.path.exists(f['fs_aseg_t1']):
                if not os.path.exists(f['fs_aseg_4dfp']):
                    r, endlog, status, failed = runExternalForFile(f['fs_aseg_4dfp'], 'g_FlipFormat -c "129.000 -108.000 -142.000" %s %s' % (f['fs_aseg_nii'], f['fs_aseg_4dfp'].replace('.img', '.ifh')), '... converting %s to 4dfp' % (os.path.basename(f['fs_aseg_nii'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r, shell=True)
                r, endlog, status, failed = runExternalForFile(f['fs_aseg_t1'], 't4img_4dfp none %s %s -O111 -@b' % (root4dfp(f['fs_aseg_4dfp']), root4dfp(f['fs_aseg_t1'])), '... converting %s to 111 space' % (f['fs_aseg_4dfp']), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

            r, endlog, status, failed = runExternalForFile(f['fs_aseg_bold'], 't4img_4dfp none %s %s -O333 -n -@b' % (root4dfp(f['fs_aseg_t1']), root4dfp(f['fs_aseg_bold'])), '... converting %s to 333 space' % (f['fs_aseg_4dfp']), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

            # --- check for aparc

            if not os.path.exists(f['fs_aparc_t1']):
                if not os.path.exists(f['fs_aparc+aseg_4dfp']):
                    r, endlog, status, failed = runExternalForFile(f['fs_aparc+aseg_4dfp'], 'g_FlipFormat -c "129.000 -108.000 -142.000" %s %s' % (f['fs_aparc+aseg_nii'], f['fs_aparc+aseg_4dfp'].replace('.img', '.ifh')), '... converting %s to 4dfp' % (os.path.basename(f['fs_aparc+aseg_nii'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r, shell=True)
                r, endlog, status, failed = runExternalForFile(f['fs_aparc_t1'], 't4img_4dfp none %s %s -O111 -@b' % (root4dfp(f['fs_aparc+aseg_4dfp']), root4dfp(f['fs_aparc_t1'])), '... converting %s to 111 space' % (f['fs_aparc+aseg_4dfp']), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

            r, endlog, status, failed = runExternalForFile(f['fs_aparc_bold'], 't4img_4dfp none %s %s -O333 -n -@b' % (root4dfp(f['fs_aparc_t1']), root4dfp(f['fs_aparc_bold'])), '... converting %s to 333 space' % (f['fs_aparc_t1']), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

            # --- check if we need to convert to nifti

            if options['image_atlas'] == '711' and options['image_target'] == 'nifti':

                # --- convert 111 4dfp to nifti
                r, endlog, status, failed = runExternalForFile(f['fs_aseg_t1'], 'g_FlipFormat %s %s' % (f['fs_aseg_111'].replace('.img', '.ifh'), f['fs_aseg_t1']), '... converting %s to nifti' % (os.path.basename(f['fs_aseg_111'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
                r, endlog, status, failed = runExternalForFile(f['fs_aparc_t1'], 'g_FlipFormat %s %s' % (f['fs_aparc+aseg_111'].replace('.img', '.ifh'), f['fs_aparc_t1']), '... converting %s to nifti' % (os.path.basename(f['fs_aparc+aseg_111'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

                # --- convert 333 4dfp to nifti
                r, endlog, status, failed = runExternalForFile(f['fs_aseg_bold'], 'g_FlipFormat %s %s' % (f['fs_aseg_333'].replace('.img', '.ifh'), f['fs_aseg_bold']), '... converting %s to nifti' % (os.path.basename(f['fs_aseg_333'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
                r, endlog, status, failed = runExternalForFile(f['fs_aparc_bold'], 'g_FlipFormat %s %s' % (f['fs_aparc+aseg_333'].replace('.img', '.ifh'), f['fs_aparc_bold']), '... converting %s to nifti' % (os.path.basename(f['fs_aparc+aseg_333'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

        if options['image_atlas'] != '711' and options['image_target'] == 'nifti':

            if os.path.exists(f['bold_template']):
                # --- convert t1 segmentation to bold space
                r, endlog, status, failed = runExternalForFile(f['fs_aseg_bold'], '3dresample -rmode NN -master %s -inset %s -prefix %s ' % (f['bold_template'], f['fs_aseg_t1'], f['fs_aseg_bold']), '... resampling t1 subcortical segmentation (%s) to bold space (%s)' % (os.path.basename(f['fs_aseg_t1']), os.path.basename(f['fs_aseg_bold'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
                r, endlog, status, failed = runExternalForFile(f['fs_aparc_bold'], '3dresample -rmode NN -master %s -inset %s -prefix %s ' % (f['bold_template'], f['fs_aparc_t1'], f['fs_aparc_bold']), '... resampling t1 cortical segmentation (%s) to bold space (%s)' % (os.path.basename(f['fs_aparc_t1']), os.path.basename(f['fs_aparc_bold'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
            else:
                r += "ERROR: bold template image is missing! Please run bbm (create brain masks for BOLD runs) and then rerun fsf to complete the last step!"


    except (ExternalFailed, NoSourceFolder) as errormessage:
        r += str(errormessage)
        r += "\nFreeSurfer segmentation failed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        print(r)
        return r
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        time.sleep(15)
        print(r)
        return r

    r += "\nFreeSurfer segmentation completed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print(r)
    return r


def runFreeSurferSubcorticalSegmentation(sinfo, options, overwrite=False, thread=0):
    """
    runFreeSurferFullSegmentation - documentation not yet available.
    """
    try:

        r = "\n---------------------------------------------------------"
        r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        r += "\nRunning subcortical only FreeSurfer segmentation ..."

        # check if any data already exists

        r = checkForFreeSurferData(sinfo, options, overwrite, thread, r)

        d = getSessionFolders(sinfo, options)
        f = getFileNames(sinfo, options)

        # --- check if we need to run fsf

        if os.path.exists(f['fs_aseg_nii']):

            r += "\n... FreeSurfer run already completed!"

        else:

            # --- copy file over

            if not os.path.exists(f['t1']):
                shutil.copy2(f['t1_source'], f['t1'])
                if gi.getImgFormat(f['t1_source']) == '.4dfp.img':
                    shutil.copy2(f['t1_source'].replace('.img', '.ifh'), f['t1'].replace('.img', '.ifh'))
                r += "\n... copied %s to target folder" % (os.path.basename(f['t1_source']))


            # --- convert to NIfTI

            onifti = f['t1']
            if gi.getImgFormat(onifti) == '.4dfp.img':
                onifti = f['t1'].replace('.4dfp.img', '.nii')
                r, endlog, status, failed = runExternalForFile(onifti, 'g_FlipFormat %s %s' % (f['t1'].replace('.img', '.ifh'), onifti), '... converting %s to NIfTI' % (os.path.basename(f['t1'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

            # --- convert to MGZ

            r, endlog, status, failed = runExternalForFile(f['fs_morig_mgz'], 'mri_convert --in_type nii %s %s' % (onifti, f['fs_morig_mgz']), '... converting %s to MGZ' % (os.path.basename(onifti)), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

            # --- run FreeSurfer Subcortical

            r, endlog, status, failed = runExternalForFile(f['fs_aseg_mgz'], 'recon-all -sd %s -subjid freesurfer -motioncor -nuintensitycor -talairach -normalization -skullstrip -subcortseg -segstats -no-isrunning' % (d['s_seg']), '... running subcortical FreeSurfer segmentation', overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

            # --- convert segmentations to nifti

            r, endlog, status, failed = runExternalForFile(f['fs_aseg_nii'], 'mri_convert -i %s -ot nii %s' % (f['fs_aseg_mgz'], f['fs_aseg_nii']), '... converting %s to NIfTI' % (f['fs_aseg_mgz']), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

        if options['image_target'] == 'nifti':
            if not os.path.exists(f['fs_aseg_t1']):
                gc.link_or_copy(f['fs_aseg_nii'], f['fs_aseg_t1'])

        # --- 4dfp path

        if options['image_target'] == '4dfp' or options['image_atlas'] == '711':

            # --- convert to 4dfp
            r, endlog, status, failed = runExternalForFile(f['fs_aseg_4dfp'], 'g_FlipFormat -c "129.000 -108.000 -142.000" %s %s' % (f['fs_aseg_nii'], f['fs_aseg_4dfp'].replace('.img', '.ifh')), '... converting %s to 4dfp' % (os.path.basename(f['fs_aseg_nii'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r, shell=True)

            # --- convert to 111
            r, endlog, status, failed = runExternalForFile(f['fs_aseg_111'], 't4img_4dfp none %s %s -O111 -@b' % (root4dfp(f['fs_aseg_4dfp']), root4dfp(f['fs_aseg_111'])), '... converting %s to 111 space' % (f['fs_aseg_4dfp']), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

            # --- convert to 333
            r, endlog, status, failed = runExternalForFile(f['fs_aseg_333'], 't4img_4dfp none %s %s -O333 -n -@b' % (root4dfp(f['fs_aseg_4dfp']), root4dfp(f['fs_aseg_333'])), '... converting %s to 333 space' % (f['fs_aseg_4dfp']), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

            if options['image_atlas'] == '711' and options['image_target'] == 'nifti':

                # --- convert 111 4dfp to nifti
                r, endlog, status, failed = runExternalForFile(f['fs_aseg_t1'], 'g_FlipFormat %s %s' % (f['fs_aseg_111'].replace('.img', '.ifh'), f['fs_aseg_t1']), '... converting %s to nifti' % (os.path.basename(f['fs_aseg_111'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

                # --- convert 333 4dfp to nifti
                r, endlog, status, failed = runExternalForFile(f['fs_aseg_bold'], 'g_FlipFormat %s %s' % (f['fs_aseg_333'].replace('.img', '.ifh'), f['fs_aseg_bold']), '... converting %s to nifti' % (os.path.basename(f['fs_aseg_333'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)

        if options['image_atlas'] != '711' and options['image_target'] == 'nifti':

            if os.path.exists(f['bold_template']):
                # --- convert t1 segmentation to bold space
                r, endlog, status, failed = runExternalForFile(f['fs_aseg_bold'], '3dresample -rmode NN -master %s -inset %s -prefix %s ' % (f['bold_template'], f['fs_aseg_t1'], f['fs_aseg_bold']), '... resampling t1 subcortical segmentation (%s) to bold space (%s)' % (os.path.basename(f['fs_aseg_t1']), os.path.basename(f['fs_aseg_bold'])), overwrite=overwrite, thread=sinfo['id'], logfolder=options['comlogs'], logtags=options['logtag'], r=r)
            else:
                r += "ERROR: bold template image is missing! Please run bbm (create brain masks for BOLD runs) and then rerun fsf to complete the last step!"


    except (ExternalFailed, NoSourceFolder) as errormessage:
        r += str(errormessage)
        r += "\nFreeSurfer segmentation failed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        print(r)
        return r
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        time.sleep(15)
        print(r)
        return r

    r += "\nFreeSurfer segmentation completed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print(r)
    return r
