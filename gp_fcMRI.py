#!/usr/bin/env python
# encoding: utf-8
"""
Created by Grega Repovs on 2016-12-17.
Code split from dofcMRIp_core gCodeP/preprocess codebase.
Copyright (c) Grega Repovs. All rights reserved.
"""

from gp_core import *
from g_img import *
import os
import shutil
import re
import subprocess
import glob
import exceptions
import sys
import traceback
from datetime import datetime
import time


def getBOLDData(sinfo, options, overwrite=False, thread=0):
    """
    getBOLDData - documentation not yet available.
    """
    bsearch = re.compile('bold([0-9]+)')

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\nCopying imaging data ..."

    r += '\nStructural data ...'
    f = getFileNames(sinfo, options)

    copy = True
    if os.path.exists(f['t1']):
        copy = False

    try:
        if overwrite or copy:
            r += '\n... copying %s' % (f['t1_source'])
            if options['image_target'] == '4dfp':
                if getImgFormat(f['t1_source']) == '.4dfp.img':
                    linkOrCopy(f['t1_source'], f['t1'])
                    linkOrCopy(f['t1_source'].replace('.img', '.ifh'), f['t1'].replace('.img', '.ifh'))
                else:
                    tmpfile = f['t1'].replace('.4dfp.img', getImgFormat(f['t1_source']))
                    linkOrCopy(f['t1_source'], tmpfile)
                    r += runExternalForFile(f['t1'], 'g_FlipFormat %s %s' % (tmpfile, f['t1'].replace('.img', '.ifh')), '... converting %s to 4dfp' % (os.path.basename(tmpfile)), overwrite, sinfo['id'])
                    os.remove(tmpfile)
            if options['image_target'] == 'nifti':
                if getImgFormat(f['t1_source']) == '.4dfp.img':
                    tmpimg = f['t1'] + '.4dfp.img'
                    tmpifh = f['t1'] + '.4dfp.ifh'
                    linkOrCopy(f['t1_source'], tmpimg)
                    linkOrCopy(f['t1_source'].replace('.img', '.ifh'), tmpifh)
                    r += runExternalForFile(f['t1'], 'g_FlipFormat %s %s' % (tmpifh, f['t1'].replace('.img', '.ifh')), '... converting %s to NIfTI' % (os.path.basename(tmpimg)), overwrite, sinfo['id'])
                    os.remove(tmpimg)
                    os.remove(tmpifh)
                else:
                    if getImgFormat(f['t1_source']) == '.nii.gz':
                        tmpfile = f['t1'] + ".gz"
                        linkOrCopy(f['t1_source'], tmpfile)
                        r += runExternalForFile(f['t1'], 'gunzip -f %s' % (tmpfile), '... gunzipping %s' % (os.path.basename(tmpfile)), overwrite, sinfo['id'])
                        if os.path.exists(tmpfile):
                            os.remove(tmpfile)
                    else:
                        linkOrCopy(f['t1_source'], f['t1'])

        else:
            r += '\n... %s present' % (f['t1'])
    except:
        r += '\n... ERROR getting the data! Please check paths and files!'

    btargets = options['bppt'].split("|")

    for (k, v) in sinfo.iteritems():
        if k.isdigit():
            bnum = bsearch.match(v['name'])
            if bnum:
                if v['task'] in btargets:

                    boldname = v['name']

                    r += "\n\nWorking on: " + boldname + " ..."

                    try:

                        # --- filenames
                        f = getFileNames(sinfo, options)
                        f.update(getBOLDFileNames(sinfo, boldname, options))
                        d = getSubjectFolders(sinfo, options)
                        # f_conc = os.path.join(d['s_bold_concs'], tconc+".conc")
                        # f_fidl = os.path.join(d['s_bold_events'], tfidl+".fidl")

                        r, status = copyBOLDData(sinfo, options, overwrite, thread, d, f, r)

                        if status:
                            r += "\n---> Data ready!"
                        else:
                            r += "\n---> ERROR: Data missing, please check source!"

                    except (ExternalFailed, NoSourceFolder), errormessage:
                        r += str(errormessage)
                    except:
                        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
                        time.sleep(3)

    r += "\n\nImaging data copy completed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return r


def createBOLDBrainMasks(sinfo, options, overwrite=False, thread=0):
    """
    createBOLDBrainMasks [... processing options]

    createBOLDBrainMasks takes the first image of each bold file, and runs FSL
    bet to extract the brain and create a brain mask. The results are saved
    into images/segmentation/boldmasks

    The relevant processing parameters are:

    --subjects        ... The subjects.txt file with all the subject information
                          [subject.txt].
    --basefolder      ... The path to the study/subjects folder, where the
                          imaging  data is supposed to go [.].
    --cores           ... How many cores to utilize [1].
    --overwrite       ... Whether to overwrite existing data (yes) or not (no)
                          [no].
    --bold_preprocess ... Which bold images (as they are specified in the
                          subjects.txt file) to copy over. It can be a single
                          type (e.g. 'task'), a pipe separated list (e.g.
                          'WM|Control|rest') or 'all' to copy all [rest].
    --boldname        ... The default name of the bold files in the images
                          folder [bold].

    The parameters can be specified in command call or subject.txt file.

    Example use:
    gmri createBOLDBrainMasks subjects=fcMRI/subjects.hcp.txt basefolder=subjects \\
         overwrite=no hcp_cifti_tail=_Atlas bold-preprocess=all

    (c) Grega Repovš

    Changelog
    2016-12-24 - Grega Repovš - Added documentation, fixed issue with cifti
                                targets, switched to gmri functions to extract
                                the first frame and convert the image.
    """

    bsearch = re.compile('bold([0-9]+)')
    report = {'bolddone': 0, 'boldok': 0, 'boldfail': 0, 'boldmissing': 0}

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\nCreating masks for bold runs ..."

    for (k, v) in sinfo.iteritems():
        if k.isdigit():
            bnum = bsearch.match(v['name'])
            if bnum:

                if (v['task'] not in options['bppt'].split("|")) and (options['bppt'] != 'all'):
                    continue

                boldname = v['name']

                r += "\n\nWorking on: " + boldname + " ..."

                try:
                    # --- filenames

                    f = getFileNames(sinfo, options)
                    if options['image_target'] == 'cifti':
                        options['image_target'] = 'nifti'
                    f.update(getBOLDFileNames(sinfo, boldname, options))

                    # --- copy over bold data

                    # --- bold
                    r, status = checkForFile2(r, f['bold'], '\n    ... bold data present', '\n    ... bold data missing, skipping bold', status=True)
                    if not status:
                        print "Looked for:", f['bold']
                        report['boldmissing'] += 1
                        continue

                    # --- extract first bold frame

                    if not os.path.exists(f['bold1']) and not options['overwrite']:
                        sliceImage(f['bold'], f['bold1'], 1)
                        if os.path.exists(f['bold1']):
                            r += '\n    ... sliced first frame from %s' % (os.path.basename(f['bold']))
                        else:
                            r += '\n    ... WARNING: failed slicing first frame from %s' % (os.path.basename(f['bold']))
                            report['boldfail'] += 1
                            continue
                    else:
                        r += '\n    ... first %s frame already present' % (os.path.basename(f['bold']))

                    # --- convert to NIfTI

                    bsource  = f['bold1']
                    bbtarget = f['bold1_brain'].replace(getImgFormat(f['bold1_brain']), '.nii.gz')
                    bmtarget = f['bold1_brain_mask'].replace(getImgFormat(f['bold1_brain_mask']), '.nii.gz')
                    if getImgFormat(f['bold1']) == '.4dfp.img':
                        bsource = f['bold1'].replace('.4dfp.img', '.nii.gz')
                        r += runExternalForFile(bsource, 'g_FlipFormat %s %s' % (f['bold1'], bsource), '    ... converting %s to nifti' % (f['bold1']), overwrite, thread=sinfo['id'], task='FlipFormat')
                    #    r += runExternalForFile(bsource, 'caret_command -file-convert -vc %s %s' % (f['bold1'].replace('img', 'ifh'), bsource), 'converting %s to nifti' % (f['bold1']), overwrite, sinfo['id'])

                    # --- run BET

                    if os.path.exists(bbtarget):
                        r += '\n    ... bet on %s already run' % (os.path.basename(bsource))
                        report['bolddone'] += 1
                    else:
                        r += runExternalForFile(bbtarget, "bet %s %s %s" % (bsource, bbtarget, options['betboldmask']), "    ... running BET on %s with options %s" % (os.path.basename(bsource), options['betboldmask']), overwrite, sinfo['id'], task='bet')
                        report['boldok'] += 1

                    if options['image_target'] == '4dfp':
                        # --- convert nifti to 4dfp
                        r += runExternalForFile(bbtarget, 'gunzip -f %s.gz' % (bbtarget), '    ... gunzipping %s.gz' % (os.path.basename(bbtarget)), overwrite, sinfo['id'], task='gunzip')
                        r += runExternalForFile(bmtarget, 'gunzip -f %s.gz' % (bmtarget), '    ... gunzipping %s.gz' % (os.path.basename(bmtarget)), overwrite, sinfo['id'], task='gunzip')
                        r += runExternalForFile(f['bold1_brain'], 'g_FlipFormat %s %s' % (bbtarget, f['bold1_brain'].replace('.img', '.ifh')), '    ... converting %s to 4dfp' % (f['bold1_brain_nifti']), overwrite, sinfo['id'], task='FlipFormat')
                        r += runExternalForFile(f['bold1_brain_mask'], 'g_FlipFormat %s %s' % (bmtarget, f['bold1_brain_mask'].replace('.img', '.ifh')), '    ... converting %s to 4dfp' % (f['bold1_brain_mask_nifti']), overwrite, sinfo['id'], task='FlipFormat')

                    else:
                        # --- link a template
                        if not os.path.exists(f['bold_template']):
                            # r += '\n ... link %s to %s' % (f['bold1_brain'], f['bold_template'])
                            os.link(f['bold1_brain'], f['bold_template'])

                except (ExternalFailed, NoSourceFolder), errormessage:
                    r += str(errormessage)
                    report['boldfail'] += 1
                except:
                    report['boldfail'] += 1
                    r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
                    time.sleep(1)

    r += "\n\nBold mask creation completed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    rstatus = "bolds done: %(bolddone)d, bolds missing: %(boldmissing)d, bolds processed: %(boldok)d, bolds failed: %(boldfail)d" % (report)

    print r
    return (r, (sinfo['id'], rstatus))



def computeBOLDStats(sinfo, options, overwrite=False, thread=0):
    """
    computeBOLDStats - documentation not yet available.
    """

    bsearch = re.compile('bold([0-9]+)')

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\nComputing bold image statistics ..."

    btargets = options['bppt'].split("|")

    for (k, v) in sinfo.iteritems():
        if k.isdigit():
            bnum = bsearch.match(v['name'])
            if bnum:
                if v['task'] in btargets or options['bppt'] == 'all':

                    boldname = v['name']
                    boldnum = bnum.group(1)

                    r += "\n\nWorking on: " + boldname + " ..."

                    try:

                        # --- filenames
                        f = getFileNames(sinfo, options)
                        f.update(getBOLDFileNames(sinfo, boldname, options))
                        d = getSubjectFolders(sinfo, options)

                        # --- check for data availability

                        r += '... checking for data'
                        status = True

                        # --- movement
                        r, status = checkForFile2(r, f['bold_mov'], '\n    ... movement data present', '\n    ... movement data missing', status=status)

                        # --- bold
                        r, status = checkForFile2(r, f['bold'], '\n    ... bold data present', '\n    ... bold data missing', status=status)

                        # --- check
                        if not status:
                            r += '\n--> ERROR: Files missing, skipping this bold run!'
                            continue

                        # --- running the stats

                        scrub = "radius:%d|fdt:%.2f|dvarsmt:%.2f|dvarsme:%.2f|after:%d|before:%d|reject:%s" % (options['mov_radius'], options['mov_fd'], options['mov_dvars'], options['mov_dvarsme'], options['mov_after'], options['mov_before'], options['mov_bad'])
                        comm = "matlab -nojvm -nodisplay -r \"try g_ComputeBOLDStats('%s', '', '%s', 'same', '%s', true), catch fprintf('\\nMatlab error! Processing failed!\\n'), end; exit\"" % (f['bold'], d['s_bold_mov'], scrub)
                        if options['print_command'] == "yes":
                            r += '\n\nRunning\n' + comm + '\n'
                        r += runExternalForFileShell(f['bold_stats'], comm, '... running matlab g_ComputeBOLDStats on %s bold %s' % (d['s_bold'], boldnum), overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task='ComputeBOLDStats')
                        r, status = checkForFile(r, f['bold_stats'], 'ERROR: Matlab has failed preprocessing bold using command: %s' % (comm))

                    except (ExternalFailed, NoSourceFolder), errormessage:
                        r += str(errormessage)
                    except:
                        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())

    r += "\n\nBold statistics computation completed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return r



def createStatsReport(sinfo, options, overwrite=False, thread=0):
    """
    createStatsReport - documentation not yet available.
    """
    try:
        bsearch = re.compile('bold([0-9]+)')

        r = "\n---------------------------------------------------------"
        r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        r += "\nCreating BOLD Movement and statistics report ..."

        btargets = options['bppt'].split("|")
        procbolds = []
        d = getSubjectFolders(sinfo, options)

        # --- check for data

        if options['mov_plot'] != "":
            if os.path.exists(os.path.join(d['s_bold_mov'], options['mov_pref'] + options['mov_plot'] + '_cor.pdf')) and not overwrite:
                r += "\n... Movement plots already exists! Please use option --overwrite=yes to redo them!"
                plot = ""
            else:
                plot = options['mov_plot']
        else:
            plot = ""

        for (k, v) in sinfo.iteritems():
            if k.isdigit():
                bnum = bsearch.match(v['name'])
                if bnum:
                    if v['task'] in btargets or options['bppt'] == 'all':

                        boldname = v['name']
                        boldnum = bnum.group(1)

                        r += "\n\nWorking on: " + boldname + " ..."

                        try:

                            # --- filenames
                            f = getFileNames(sinfo, options)
                            f.update(getBOLDFileNames(sinfo, boldname, options))

                            # --- check for data availability

                            r += '... checking for data'
                            status = True

                            # --- movement
                            r, status = checkForFile2(r, f['bold_mov'], '\n    ... movement data present', '\n    ... movement data missing', status=status)
                            r, status = checkForFile2(r, f['bold_stats'], '\n    ... stats data present', '\n    ... stats data missing', status=status)
                            r, status = checkForFile2(r, f['bold_scrub'], '\n    ... scrub data present', '\n    ... scrub data missing', status=status)

                            # --- check
                            if status:
                                procbolds.append(boldnum)
                            else:
                                r += '\n--> ERROR: Files missing, skipping this bold run!'

                        except (ExternalFailed, NoSourceFolder), errormessage:
                            r += str(errormessage)
                        except:
                            r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())

        # run the R script

        procbolds.sort()
        report = {}

        for tf in ['mov_mreport', 'mov_sreport', 'mov_preport']:
            if options[tf] != '':
                tmpf = os.path.join(d['qc_mov'], options['boldname'] + '_' + options[tf])
                report[tf] = tmpf
                if os.path.exists(tmpf) and thread == 1:
                    os.remove(tmpf)
            else:
                report[tf] = ''

        rcomm = 'g_BoldStats --args -f=%s -mr=%s -pr=%s -sr=%s -s=%s -d=%.1f -e=%.1f -m=%.1f -rd=%.1f -tr=%.2f -fidl=%s -post=%s -plot=%s -pref=%s -rname=%s -bolds="%s" -v' % (
            d['s_bold_mov'],            # the folder to look for .dat data [.]
            report['mov_mreport'],      # the file to write movement report to [none]
            report['mov_preport'],      # the file to write movement report after scrubbing to [none]
            report['mov_sreport'],      # the file to write scrubbing report to [none]
            sinfo['id'],                # subject id to use in plots and reports [none]
            options['mov_dvars'],       # threshold to use for computing dvars rejections [3]
            options['mov_dvarsme'],     # threshold to use for computing dvarsme rejections [1.5]
            options['mov_fd'],          # threshold to use for computing frame-to-frame movement rejections [0.5]
            options['mov_radius'],      # radius (in mm) from center of head to cortex to estimate rotation size [50]
            float(options['TR']),       # TR to be used when generating .fidl files [2.5]
            options['mov_fidl'],        # whether to output and what to base fild on (fd, dvars, dvarsme, u/ume - union, i/ime - intersection, none) [none]
            options['mov_post'],        # whether to create report of scrubbing effect and what to base it on (fd, dvars, dvarsme, u/ume - union, i/ime - intersection, none) [none]
            plot,                       # root name of the plot file, none to omit plotting [mov_report]
            options['mov_pref'],        # prefix for the reports
            options['boldname'],        # root name for the bold files
            "|".join(procbolds))        # | separated list of bold indeces for which to do the stat report

        tfile = os.path.join(d['s_bold_mov'], '.r.ok')

        if options['print_command'] == "yes":
            r += '\n\nRunning\n' + rcomm + '\n'
        r += runExternalForFile(tfile, rcomm, "\nRunning g_BoldStats", overwrite, sinfo['id'], remove=options['log'] == 'remove', task='PlotBoldStats')
        os.remove(tfile)

        if options['mov_plot'] != '' and options['mov_pdf'] != "no":
            for sf in ['cor', 'dvars', 'dvarsme']:
                tfolder = os.path.join(d['qc_mov'], options['mov_pdf'], sf)
                if not os.path.exists(tfolder):
                    os.makedirs(tfolder)

                froot = "%s_%s%s_%s.pdf" % (options['boldname'], options['mov_pref'], options['mov_plot'], sf)
                if os.path.exists(os.path.join(tfolder, "%s-%s" % (sinfo['id'], froot))):
                    os.remove(os.path.join(tfolder, "%s-%s" % (sinfo['id'], froot)))
                linkOrCopy(os.path.join(d['s_bold_mov'], froot), os.path.join(tfolder, "%s-%s" % (sinfo['id'], froot)))

        if options['mov_fidl'] in ['fd', 'dvars', 'dvarsme', 'u', 'ume', 'i', 'ime'] and options['eventfile'] != "" and options['bppt'] != "":
            concf = os.path.join(d['s_bold_concs'], options['bppt'] + '.conc')
            fidlf = os.path.join(d['s_bold_events'], options['eventfile'] + '.fidl')
            ipatt = "_%s_scrub.fidl" % (options['mov_fidl'])

            if os.path.exists(concf) and os.path.exists(fidlf):
                try:
                    meltMovFidl(concf, ipatt, fidlf, fidlf.replace('.fidl', ipatt))
                except:
                    r += "\nWARNING: Failed to create a melted fidl file!"
                    print "\nWARNING: Failed to create a melted fidl file! (%s)" % (sinfo['id'])
                    raise
            else:
                r += "\nWARNING: Files missing, failed to create a melted fidl file!"

    except (ExternalFailed, NoSourceFolder), errormessage:
        r += str(errormessage)
        r += "\nBOLD statistics and movement report failed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
        print r
        return r
    except:
        r += "\nBOLD statistics and movement report failed with and unknown error: \n...................................\n%s...................................\n" % (traceback.format_exc())
        print r
        return r

    r += "\n\nBOLD statistics and movement report completed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return r



def extractNuisanceSignal(sinfo, options, overwrite=False, thread=0):
    """
    extractNuisanceSignal - documentation not yet available.
    """
    bsearch = re.compile('bold([0-9]+)')

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\nExtracting BOLD nuisance signal ..."

    btargets = options['bppt'].split("|")

    for (k, v) in sinfo.iteritems():
        if k.isdigit():
            bnum = bsearch.match(v['name'])
            if bnum:
                if v['task'] in btargets or options['bppt'] == 'all':

                    boldname = v['name']
                    boldnum = bnum.group(1)

                    r += "\n\nWorking on: " + boldname + " ..."

                    try:

                        # --- filenames
                        f = getFileNames(sinfo, options)
                        f.update(getBOLDFileNames(sinfo, boldname, options))
                        d = getSubjectFolders(sinfo, options)

                        # --- check for data availability

                        r += '... checking for data'
                        status = True

                        # --- bold mask
                        r, status = checkForFile2(r, f['bold1_brain_mask'], '\n    ... bold brain mask present', '\n    ... bold brain mask missing', status=status)

                        # --- aseg
                        r, astat = checkForFile2(r, f['fs_aseg_bold'], '\n    ... freesurfer aseg present', '\n    ... freesurfer aseg missing', status=True)
                        if not astat:
                            r, astat = checkForFile2(r, f['fs_aparc_bold'], '\n    ... freesurfer aparc present', '\n    ... freesurfer aparc missing', status=True)
                            segfile  = f['fs_aparc_bold']
                        else:
                            segfile  = f['fs_aseg_bold']

                        status = status and astat

                        # --- bold
                        r, status = checkForFile2(r, f['bold'], '\n    ... bold data present', '\n    ... bold data missing', status=status)

                        # --- check
                        if not status:
                            r += '\n--> ERROR: Files missing, skipping this bold run!'
                            continue

                        # --- running nuisance extraction


                        comm = "matlab -nojvm -nodisplay -r \"try g_ExtractNuisance('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, %s), catch fprintf('\\nMatlab error! Processing failed!\\n'), end; exit\"" % (
                            f['bold'],                  # --- bold file to process
                            segfile,                    # --- aseg or aparc file
                            f['bold1_brain_mask'],      # --- bold brain mask
                            d['s_bold_mov'],            # --- functional/movement subfolder
                            d['s_nuisance'],            # --- roi/nuisance subfolder
                            options['wbmask'],          # --- mask to exclude ROI from WB
                            options['sbjroi'],          # --- a mask used to specify subject specific WB
                            options['nroi'],            # --- additional nuisance regressors ROI
                            options['shrinknsroi'],     # --- shrink nuisance signal ROI
                            'true')                     # --- verbosity

                        if options['print_command'] == "yes":
                            r += '\n\nRunning\n' + comm + '\n'
                        r += runExternalForFileShell(f['bold_nuisance'], comm, '... running matlab g_ExtractNuisance on %s bold %s' % (d['s_bold'], boldnum), overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task='ExtractNuisance')
                        r, status = checkForFile(r, f['bold_nuisance'], 'ERROR: Matlab has failed preprocessing bold using command: %s' % (comm))

                    except (ExternalFailed, NoSourceFolder), errormessage:
                        r += str(errormessage)
                    except:
                        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())

    r += "\n\nBold nuisance signal extraction completed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return r



def preprocessBold(sinfo, options, overwrite=False, thread=0):
    """
    preprocessBold - documentation not yet available.
    """

    bsearch = re.compile('bold([0-9]+)')

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\nPreprocessing (v7) bold runs ..."
    r += "\n%s Preprocessing (v7) bold runs ..." % (action("Running", options['run']))

    report = {'done': [], 'failed': [], 'ready': [], 'not ready': []}

    btargets = options['bppt'].split("|")

    for (k, v) in sinfo.iteritems():
        if k.isdigit():
            bnum = bsearch.match(v['name'])
            if bnum:
                if v['task'] in btargets or options['bppt'] == 'all':

                    boldname = v['name']
                    boldnum = bnum.group(1)

                    r += "\n\nWorking on: " + boldname + " ..."

                    try:

                        # --- filenames
                        f = getFileNames(sinfo, options)
                        f.update(getBOLDFileNames(sinfo, boldname, options))
                        if options['image_target'] == 'cifti':
                            f['bold'] = f['bold_dts']
                            f['bold_final'] = f['bold_dts_final']

                        d = getSubjectFolders(sinfo, options)

                        # --- check for data availability

                        r += '... checking for data'
                        status = True


                        # --- movement
                        r, status = checkForFile2(r, f['bold_mov'], '\n    ... movement data present', '\n    ... movement data missing [%s]' % (f['bold_mov']), status=status)

                        # --- bold stats
                        r, status = checkForFile2(r, f['bold_stats'], '\n    ... bold statistics data present', '\n    ... bold statistics data missing [%s]' % (f['bold_stats']), status=status)

                        # --- bold scrub
                        r, status = checkForFile2(r, f['bold_scrub'], '\n    ... bold scrubbing data present', '\n    ... bold scrubbing data missing [%s]' % (f['bold_scrub']), status=status)

                        # --- check for files if doing regression

                        if 'r' in options['bppa']:

                            # --- nuisance data
                            r, status = checkForFile2(r, f['bold_nuisance'], '\n    ... bold nuisance signal data present', '\n    ... bold nuisance signal data missing [%s]' % (f['bold_nuisance']), status=status)

                            # --- event
                            if 'e' in options['bppn']:
                                r, status = checkForFile2(r, f['bold_event'], '\n    ... event data present', '\n    ... even data missing [%s]' % (f['bold_event']), status=status)

                        # --- bold
                        r, status = checkForFile2(r, f['bold'], '\n    ... bold data present', '\n    ... bold data missing [%s]' % (f['bold']), status=status)


                        # --- check
                        if not status:
                            r += '\n--> ERROR: Files missing, skipping this bold run!'
                            report['not ready'].append(boldnum)
                            continue
                        else:
                            report['ready'].append(boldnum)

                        # --- run matlab preprocessing script

                        if overwrite:
                            boldow = 'true'
                        else:
                            boldow = 'false'

                        scrub = "radius:%(mov_radius)d|fdt:%(mov_fd).2f|dvarsmt:%(mov_dvars).2f|dvarsme:%(mov_dvarsme).2f|after:%(mov_after)d|before:%(mov_before)d|reject:%(mov_bad)s" % (options)
                        opts  = "boldname=%(boldname)s|surface_smooth=%(surface_smooth)f|volume_smooth=%(volume_smooth)f|voxel_smooth=%(voxel_smooth)f|hipass_filter=%(hipass_filter)f|lopass_filter=%(lopass_filter)f|omp_threads=%(omp_threads)d|framework_path=%(framework_path)s|wb_command_path=%(wb_command_path)s|smooth_mask=%(smooth_mask)s|dilate_mask=%(dilate_mask)s|glm_matrix=%(glm_matrix)s|glm_residuals=%(glm_residuals)s|glm_name=%(glm_name)s|bold_tail=%(hcp_cifti_tail)s" % (options)

                        mcomm = 'fc_Preprocess(\'%s\', %s, %d, \'%s\', \'%s\', %s, \'%s\', %f, \'%s\', \'%s\', %s, \'%s\', \'%s\', \'%s\', \'%s\')' % (
                            d['s_base'],                        # --- subject folder
                            boldnum,                            # --- number of bold file to process
                            options['omit'],                    # --- number of frames to skip at the start of each run
                            options['bppa'],                    # --- which steps to perform (s, h, r, c, p, p)
                            options['bppn'],                    # --- what to regress (m, v, wm, wb, d, t, e, 1b)
                            '[]',                               # --- matrix of task regressors
                            options['eventfile'],               # --- fidl file to be used
                            float(options['TR']),               # --- TR of the data
                            options['eventstring'],             # --- eventstring specifying what and how of the task to regress
                            options['bold_prefix'],             # --- prefix to the bold files
                            boldow,                             # --- whether to overwrite the existing files
                            getImgFormat(f['bold_final']),      # --- what file extension to expect and use (e.g. '.nii', .'.4dfp.img')
                            scrub,                              # --- scrub parameters
                            options['pignore'],                 # --- how to deal with bad frames ('hipass:keep/linear/spline|regress:keep/ignore|lopass:keep/linear/spline')
                            opts)                               # --- additional options

                        comm = 'matlab -nojvm -nodisplay -r "try %s, catch ME; fprintf(\'\\nMatlab Error! Processing Failed!\\n%%s\\n\', ME.message), end; exit"' % (mcomm)

                        # r += '\n ... running: %s' % (comm)
                        if options['run'] == "run":
                            if options['print_command'] == "yes":
                                r += '\n\nRunning\n' + comm + '\n'
                            r += runExternalForFileShell(f['bold_final'], comm, 'running matlab Preprocess7 on %s bold %s' % (d['s_bold'], boldnum), overwrite, sinfo['id'], remove=options['log'] == 'remove', task='Preprocess7')
                            r, status = checkForFile(r, f['bold_final'], 'ERROR: Matlab has failed preprocessing bold using command: \n--> %s\n' % (mcomm))
                            if status:
                                report['done'].append(boldnum)
                            else:
                                report['failed'].append(boldnum)
                    except (ExternalFailed, NoSourceFolder), errormessage:
                        r += str(errormessage)
                        report['failed'].append(boldnum)
                    except:
                        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
                        time.sleep(5)
                        report['failed'].append(boldnum)

    r += "\n\nBold preprocessing completed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    if options['run'] == "run":
        rstatus = "bolds: %d ready [%s], %d not ready [%s], %d ran ok [%s], %d failed [%s]" % (len(report['ready']), " ".join(report['ready']), len(report['not ready']), " ".join(report['not ready']), len(report['done']), " ".join(report['done']), len(report['failed']), " ".join(report['failed']))
    else:
        rstatus = "bolds: %d ready [%s], %d not ready [%s]" % (len(report['ready']), " ".join(report['ready']), len(report['not ready']), " ".join(report['not ready']))

    print r
    return (r, (sinfo['id'], rstatus))


def preprocessConc(sinfo, options, overwrite=False, thread=0):
    """
    preprocessConc - documentation not yet available.
    """

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s Preprocessing conc bundles (v2) ..." % (action("Running", options['run']))

    concs = options['bppt'].split("|")
    fidls = options['eventfile'].split("|")

    concroot = options['boldname'] + '_' + options['image_target'] + '_'
    report = ''

    if len(concs) != len(fidls):
        r += "\nERROR: Number of conc files (%d) does not match number of event files (%d), processing aborted!" % (len(concs), len(fidls))

    else:
        for nb in range(0, len(concs)):
            tconc = concs[nb].strip().replace(".conc", "")
            tfidl = fidls[nb].strip().replace(".fidl", "")

            try:
                r += "\n\nConc bundle: %s" % (tconc)

                d = getSubjectFolders(sinfo, options)
                f = {}
                f_conc = os.path.join(d['s_bold_concs'], concroot + tconc + ".conc")
                f_fidl = os.path.join(d['s_bold_events'], tfidl + ".fidl")

                # --- find conc data

                if overwrite or not os.path.exists(f_conc):
                    tf = findFile(sinfo, options, tconc + ".conc")
                    if tf:
                        r += '\n... getting conc data from %s' % (tf)
                        if os.path.exists(f_conc):
                            os.remove(f_conc)
                        shutil.copy2(tf, f_conc)

                    else:
                        r += '\n... ERROR: Conc data file (%s) does not exist in the expected locations! Skipping this conc bundle.' % (tconc)
                        continue
                else:
                    r += '\n... conc data present'

                # --- find fidl data

                if overwrite or not os.path.exists(f_fidl):
                    tf = findFile(sinfo, options, tfidl + ".fidl")
                    if tf:
                        r += '\n... getting event data from %s' % (tf)
                        if os.path.exists(f_fidl):
                            os.remove(f_fidl)
                        shutil.copy2(tf, f_fidl)
                    else:
                        r += '\n... ERROR: Event data file (%s) does not exist in the expected locations! Skipping this conc bundle.' % (tfidl)
                        continue
                else:
                    r += '\n... event data present'


                # --- loop through bold files

                conc    = readConc(f_conc, boldname=options['boldname'])
                nconc   = []
                bolds   = []
                rstatus = True
                check   = {'ok': [], 'bad': []}


                if len(conc) == 0:
                    r += '\n... ERROR: No valid image files in conc file (%s)! Skipping this conc bundle.' % (f_conc)
                    continue

                for c in conc:
                    # print "c from conc:", c
                    boldnum  = c[1]
                    boldname = "bold" + boldnum
                    bolds.append(boldnum)

                    r += "\n\nLooking up: " + boldname + " ..."

                    # --- filenames
                    f = getFileNames(sinfo, options)
                    f.update(getBOLDFileNames(sinfo, boldname, options))

                    if options['image_target'] == 'cifti':
                        f['bold'] = f['bold_dts']
                        f['bold_final'] = f['bold_dts_final']

                    # --- check for data availability

                    r += '... checking for data'
                    status = True

                    # --- bold
                    r, status = checkForFile2(r, f['bold'], '\n    ... bold data present', '\n    ... bold data missing [%s]' % (f['bold']), status=status)
                    nconc.append((f['bold'], boldnum))

                    # --- movement
                    if 'r' in options['bppa'] and ('m' in options['bppn'] or 'm' in options['bppa']):
                        r, status = checkForFile2(r, f['bold_mov'], '\n    ... movement data present', '\n    ... movement data missing [%s]' % (f['bold_mov']), status=status)

                    # --- bold stats
                    if 'm' in options['bppa']:
                        r, status = checkForFile2(r, f['bold_stats'], '\n    ... bold statistics data present', '\n    ... bold statistics data missing [%s]' % (f['bold_stats']), status=status)

                    # --- bold scrub
                    if any([e in options['pignore'] for e in ['linear', 'spline', 'ignore']]):
                        r, status = checkForFile2(r, f['bold_scrub'], '\n    ... bold scrubbing data present', '\n    ... bold scrubbing data missing [%s]' % (f['bold_scrub']), status=status)
                        r += '\npignore: ' + options['pignore']

                    # --- check for nuisance data files if doing regression

                    if 'r' in options['bppa'] and any([e in options['bppn'] for e in ['V', 'WM', 'WB']]):
                        r, status = checkForFile2(r, f['bold_nuisance'], '\n    ... bold nuisance signal data present', '\n    ... bold nuisance signal data missing [%s]' % (f['bold_nuisance']), status=status)

                    # --- check
                    if not status:
                        r += '\n--> ERROR: Files missing!'
                        rstatus = False
                        check['bad'].append(boldnum)
                    else:
                        check['ok'].append(boldnum)

                # --- all files reviewed continuing conc processing

                report = ''
                if len(check['ok']) > 0:
                    report += "%d bolds ok [%s], " % (len(check['ok']), " ".join(check['ok']))
                else:
                    report += "0 bolds ok, "

                if len(check['bad']) > 0:
                    report += "%d bold not ok [%s], " % (len(check['bad']), " ".join(check['bad']))
                else:
                    report += "0 bolds not ok"


                if not rstatus:
                    r += '\nERROR: Due to missing data we are skipping this conc bundle!'
                    report += " => missing data"
                    continue

                writeConc(f_conc, nconc)

                # --- run matlab preprocessing script

                if overwrite:
                    boldow = 'true'
                else:
                    boldow = 'false'

                done = f['conc_final'] + ".ok"

                scrub = "radius:%(mov_radius)d|fdt:%(mov_fd).2f|dvarsmt:%(mov_dvars).2f|dvarsme:%(mov_dvarsme).2f|after:%(mov_after)d|before:%(mov_before)d|reject:%(mov_bad)s" % (options)
                opts  = "boldname=%(boldname)s|surface_smooth=%(surface_smooth)f|volume_smooth=%(volume_smooth)f|voxel_smooth=%(voxel_smooth)f|hipass_filter=%(hipass_filter)f|lopass_filter=%(lopass_filter)f|omp_threads=%(omp_threads)d|framework_path=%(framework_path)s|wb_command_path=%(wb_command_path)s|smooth_mask=%(smooth_mask)s|dilate_mask=%(dilate_mask)s|glm_matrix=%(glm_matrix)s|glm_residuals=%(glm_residuals)s|glm_name=%(glm_name)s|bold_tail=%(hcp_cifti_tail)s" % (options)

                mcomm = 'fc_PreprocessConc(\'%s\', [%s], \'%s\', %.3f,  %d, \'%s\', [], \'%s.fidl\', \'%s\', \'%s\', %s, \'%s\', \'%s\', \'%s\', \'%s\', \'%s\')' % (
                    d['s_base'],                        # --- subject folder
                    " ".join(bolds),                    # --- vector of bold runs in the order of the conc file
                    options['bppa'],                    # --- which steps to perform in what order (s, h, r0/r1/r2, c, p, l)
                    options['TR'],                      # --- TR
                    options['omit'],                    # --- the number of frames to omit at the start of each run
                    options['bppn'],                    # --- nuisance regressors (m, v, wm, wb, d, t, e)
                    tfidl,                              # --- event file to be used for task regression (w/o .fidl)
                    options['eventstring'],             # --- event string specifying what and how of task to regress
                    options['bold_prefix'],             # --- optional prefix to the resulting bolds
                    boldow,                             # --- whether to overwrite existing files
                    getImgFormat(f['bold_final']),      # --- the format of the images (.nii vs. .4dfp.img)
                    scrub,                              # --- scrub parameters string
                    options['pignore'],                 # --- how to deal with bad frames ('hipass:keep/linear/spline|regress:keep/ignore|lopass:keep/linear/spline')
                    opts,                               # --- additional options
                    done)                               # --- file to save when done

                comm = 'matlab -nojvm -nodisplay -r "try %s, catch ME; fprintf(\'\\nMatlab Error! Processing Failed!\\n%%s\\n\', ME.message), end; exit"' % (mcomm)

                r += '\n\n%s nuisance and task removal' % (action("Running", options['run']))
                if options['print_command'] == "yes":
                    r += '\n' + comm + '\n'
                if options['run'] == "run":
                    r += runExternalForFileShell(done, comm, 'running matlab conc preprocessing (v2) on bolds [%s]' % (" ".join(bolds)), overwrite, sinfo['id'], remove=options['log'] == 'remove', task='PreprocessConc2')
                    r, status = checkForFile(r, done, 'ERROR: Matlab has failed preprocessing bold using command: \n--> %s\n' % (mcomm))
                    if os.path.exists(done):
                        os.remove(done)
                    if status:
                        report += " => processed ok"
                    else:
                        report += " => processing failed"
                else:
                    if os.path.exists(done):
                        report += " => already done"
                    else:
                        report += " => ready"

            except (ExternalFailed, NoSourceFolder), errormessage:
                r += str(errormessage)
                report += " => processing failed"
            except:
                report += " => processing failed"
                r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
                time.sleep(5)

    r += "\n\nConc preprocessing (v2) completed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return (r, (sinfo['id'], report))

