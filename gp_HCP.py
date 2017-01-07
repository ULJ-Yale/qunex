#!/usr/bin/env python
# encoding: utf-8
"""
This file holds code for running HCP preprocessing and image mapping. It
consists of functions:

* hcpPreFS        ... runs HCP PreFS preprocessing
* hcpFS           ... runs HCP FS preprocessing
* hcpPostFS       ... runs HCP PostFS preprocessing
* hcpDiffusion    ... runs HCP Diffusion weighted image preprocessing
* hcpfMRIVolume   ... runs HCP BOLD Volume preprocessing
* hcpfMRISurface  ... runs HCP BOLD Surface preprocessing
* hcpDTIFit       ... runs DTI Fit
* hcpBedpostx     ... runs Bedpost X
* mapHCPData      ... maps results of HCP preprocessing into `images`
                      folder

All the functions are part of the processing suite. They should be called
from the command line using `gmri` command. Help is available through:

`gmri ?<command>` for command specific help
`gmri -o` for a list of relevant arguments and options

There are additional support functions that are not to be used
directly.

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


# -------------------------------------------------------------------
#
#                       HCP Pipeline Scripts
#

def getHCPPaths(sinfo, options):
    """
    getHCPPaths - documentation not yet available.
    """
    d = {}

    # ---- HCP Pipeline folders

    base                    = options['hcp_Pipeline']

    d['hcp_base']           = base

    d['hcp_Templates']      = os.path.join(base, 'global', 'templates')
    d['hcp_Bin']            = os.path.join(base, 'global', 'binaries')
    d['hcp_Config']         = os.path.join(base, 'global', 'config')

    d['hcp_PreFS']          = os.path.join(base, 'PreFreeSurfer', 'scripts')
    d['hcp_FS']             = os.path.join(base, 'FreeSurfer', 'scripts')
    d['hcp_PostFS']         = os.path.join(base, 'PostFreeSurfer', 'scripts')
    d['hcp_fMRISurf']       = os.path.join(base, 'fMRISurface', 'scripts')
    d['hcp_fMRIVol']        = os.path.join(base, 'fMRIVolume', 'scripts')
    d['hcp_tfMRI']          = os.path.join(base, 'tfMRI', 'scripts')
    d['hcp_dMRI']           = os.path.join(base, 'DiffusionPreprocessing', 'scripts')
    d['hcp_Global']         = os.path.join(base, 'global', 'scripts')
    d['hcp_tfMRIANalysis']  = os.path.join(base, 'TaskfMRIAnalysis', 'scripts')

    d['hcp_caret7dir']      = os.path.join(base, 'global', 'binaries', 'caret7', 'bin_rh_linux64')

    # ----

    hcpbase                 = os.path.join(sinfo['hcp'], sinfo['id'] + options['hcp_suffix'])

    d['base']               = hcpbase
    d['hcp_nonlin']         = os.path.join(hcpbase, 'MNINonLinear')
    d['T1w_folder']         = os.path.join(hcpbase, 'T1w')
    # d['T1w']                = os.path.join(hcpbase, 'T1w', sinfo['id'] + '_strc_T1w_MPR1.nii.gz')
    d['T1w']                = "@".join(glob.glob(os.path.join(d['T1w_folder'], '*T1w_MPR*')))
    d['DWI_folder']         = os.path.join(hcpbase, 'Diffusion')
    d['FS_folder']          = os.path.join(hcpbase, 'T1w', sinfo['id'] + options['hcp_suffix'])

    if options['hcp_t2'] == 'NONE':
        d['T2w'] = 'NONE'
    else:
        # d['T2w'] = os.path.join(hcpbase, 'T2w', sinfo['id'] + '_strc_T2w_SPC1.nii.gz')
        d['T2w']                = "@".join(glob.glob(os.path.join(hcpbase, 'T2w', sinfo['id'] + '_strc_T2w_SPC*.nii.gz')))


    d['fmapmag']   = 'NONE'
    d['fmapphase'] = 'NONE'
    d['fmapge']    = 'NONE'
    if options['hcp_avgrdcmethod'] == 'SiemensFieldMap' or options['hcp_bold_correct'] == 'SiemensFieldMap':
        d['fmapmag']   = os.path.join(hcpbase, 'FieldMap_strc', sinfo['id'] + '_strc_FieldMap_Magnitude.nii.gz')
        d['fmapphase'] = os.path.join(hcpbase, 'FieldMap_strc', sinfo['id'] + '_strc_FieldMap_Phase.nii.gz')
        d['fmapge']    = "NONE"
    elif options['hcp_avgrdcmethod'] == 'GeneralElectricFieldMap' or options['hcp_bold_correct'] == 'GeneralElectricFieldMap':
        d['fmapmag']   = "NONE"
        d['fmapphase'] = "NONE"
        d['fmapge']    = os.path.join(hcpbase, 'FieldMap_strc', sinfo['id'] + '_strc_FieldMap_GE.nii.gz')

    return d


def action(action, run):
    """
    action - documentation not yet available.
    """
    if run == "test":
        if action.istitle():
            return "Test " + action.lower()
        else:
            return "test " + action
    else:
        return action



def hcpPreFS(sinfo, options, overwrite=False, thread=0):
    '''hcp_PreFS command (hcp1)

    Runs the pre-FS step of HCP Pipeline. It looks for T1w and T2w images in subject's T1w and T2w folder, averages them (if multiple present) and linearly and nonlinearly aligns them to the MNI atlas.

    It makes use of the following options:

    - hcp_suffix           ... Specifies a suffix to the subject id if multiple variants are run, empty otherwise.
    - hcp_biascorrect_t1w      ... Whether to run T1w image bias correction.
    - hcp_t2               ... NONE if no T2w image is available, anything else otherwise.
    - hcp_brainsize        ... Specifies the size of the brain in mm (170 is FSL default and seems to be a good choice, HCP uses 150).
    - hcp_echodiff         ... Difference in TE times if a fieldmap image is used, set to NONE if not used.
    - hcp_dwelltime        ... Echo Spacing or Dwelltime of Spin Echo Field Map or "NONE" if not used.
    - hcp_seunwarpdir      ... Phase encoding direction of the spin echo field map (x, y or NONE).
    - hcp_t1samplespacing  ... T1 image sample spacing, "NONE" if not used.
    - hcp_t2samplespacing  ... T2 image sample spacing, "NONE" if not used
    - hcp_unwarpdir        ... Readout direction of the T1w and T2w images (x, y, z; Used with either a regular field map or a spin echo field map)
    - hcp_gdcoeffs         ... File containing gradient distortion coefficients, Set to "NONE" to turn off.
    - hcp_avgrdcmethod     ... Averaging and readout distortion correction method.
                                 "NONE"                    = average any repeats with no readout correction
                                 "FIELDMAP"                = average any repeats and use Siemens field map for readout correction
                                 "SiemensFieldMap"         = average any repeats and use Siemens field map for readout correction
                                 "GeneralElectricFieldMap" = average any repeats and use GE field map for readout correction
                                 "TOPUP"                   = average any repeats and use spin echo field map for readout correction
    - hcp_topupconfig      ... Configuration file for topup or "NONE" if not used
    - hcp_bfsigma          ... Bias Field Smoothing Sigma (optional).
    '''

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP PreFreeSurfer Pipeline ...\n" % (action("Running", options['run']))

    # print "---> Setting up hcp"

    hcp = getHCPPaths(sinfo, options)

    # print "---> Setting up command"

    run    = True
    report = "Error"

    try:

        # --- checks

        if 'hcp' not in sinfo:
            r += "\n---> ERROR: There is no hcp info for subject %s in subjects.txt" % (sinfo['id'])
            run = False

        # --- check for T1w and T2w images

        for tfile in hcp['T1w'].split("@"):
            if os.path.exists(tfile):
                r += "\n---> T1w image file present."
            else:
                r += "\n---> ERROR: Could not find T1w image file. [%s]" % (tfile)
                run = False

        if hcp['T2w'] == 'NONE':
            r += "\n---> Not using T2w image."
        else:
            for tfile in hcp['T2w'].split("@"):
                if os.path.exists(tfile):
                    r += "\n---> T2w image file present."
                else:
                    r += "\n---> ERROR: Could not find T2w image file. [%s]" % (tfile)
                    run = False


        # --- do we need spinecho images

        sepos       = 'NONE'
        seneg       = 'NONE'
        topupconfig = 'NONE'

        if options['hcp_avgrdcmethod'] == 'TOPUP':
            try:
                tufolder = glob.glob(os.path.join(hcp['base'], 'SpinEchoFieldMap*'))
                tufolder = tufolder[0]
                sepos    = glob.glob(os.path.join(tufolder, "*_" + options['hcp_sephasepos'] + "_*"))[0]
                seneg    = glob.glob(os.path.join(tufolder, "*_" + options['hcp_sephaseneg'] + "_*"))[0]

                if options['hcp_topupconfig'] != 'NONE':
                    if not os.path.exists(options['hcp_topupconfig']):
                        topupconfig = os.path.join(hcp['hcp_Config'], options['hcp_topupconfig'])
                        if not os.path.exists(topupconfig):
                            r += "\n---> ERROR: Could not find TOPUP configuration file: %s." % (options['hcp_topupconfig'])
                            # raise AssertionError('Could not find TOPUP configuration file!')
                            run = False
                        else:
                            r += "\n---> TOPUP configuration file present."
                    else:
                        r += "\n---> TOPUP configuration file present."
            except:
                r += "\n---> ERROR: Could not find files for TOPUP processing of subject %s." % (sinfo['id'])
                # raise
                run = False

        # --- lookup gdcoeffs file if needed

        if options['hcp_gdcoeffs'] != 'NONE':
            if not os.path.exists(options['hcp_gdcoeffs']):
                gdcoeffs = os.path.join(hcp['hcp_Config'], options['hcp_gdcoeffs'])
                if not os.path.exists(gdcoeffs):
                    r += "\n---> ERROR: Could not find gradient distorsion coefficients file: %s." % (options['hcp_gdcoeffs'])
                    # raise AssertionError('Could not find gradient distorsion coefficients file!')
                    run = False
                else:
                    r += "\n---> Gradient distorsion coefficients file present."
            else:
                r += "\n---> Gradient distorsion coefficients file present."
        else:
            gdcoeffs = 'NONE'



        # --- Set up the command

        comm = '%(script)s \
            --path="%(path)s" \
            --subject="%(subject)s" \
            --t1="%(t1)s" \
            --t2="%(t2)s" \
            --t1template="%(t1template)s" \
            --t1templatebrain="%(t1templatebrain)s" \
            --t1template2mm="%(t1template2mm)s" \
            --t2template="%(t2template)s" \
            --t2templatebrain="%(t2templatebrain)s" \
            --t2template2mm="%(t2template2mm)s" \
            --templatemask="%(templatemask)s" \
            --template2mmmask="%(template2mmmask)s" \
            --brainsize="%(brainsize)d" \
            --fnirtconfig="%(fnirtconfig)s" \
            --fmapmag="%(fmapmag)s" \
            --fmapphase="%(fmapphase)s" \
            --fmapgeneralelectric="%(fmapge)s" \
            --echodiff="%(echodiff)s" \
            --SEPhaseNeg="%(SEPhaseNeg)s" \
            --SEPhasePos="%(SEPhasePos)s" \
            --echospacing="%(echospacing)s" \
            --seunwarpdir="%(seunwarpdir)s" \
            --t1samplespacing="%(t1samplespacing)s" \
            --t2samplespacing="%(t2samplespacing)s" \
            --unwarpdir="%(unwarpdir)s" \
            --gdcoeffs="%(gdcoeffs)s" \
            --avgrdcmethod="%(avgrdcmethod)s" \
            --topupconfig="%(topupconfig)s" \
            --bfsigma="%(bfsigma)s" \
            --t1biascorrect="%(biascorrect)s" ' % {
                'script'            : os.path.join(hcp['hcp_base'], 'PreFreeSurfer', 'PreFreeSurferPipeline.sh'),
                'path'              : sinfo['hcp'],
                'subject'           : sinfo['id'] + options['hcp_suffix'],
                't1'                : hcp['T1w'],
                't2'                : hcp['T2w'],
                't1template'        : os.path.join(hcp['hcp_Templates'], 'MNI152_T1_0.7mm.nii.gz'),
                't1templatebrain'   : os.path.join(hcp['hcp_Templates'], 'MNI152_T1_0.7mm_brain.nii.gz'),
                't1template2mm'     : os.path.join(hcp['hcp_Templates'], 'MNI152_T1_2mm.nii.gz'),
                't2template'        : os.path.join(hcp['hcp_Templates'], 'MNI152_T2_0.7mm.nii.gz'),
                't2templatebrain'   : os.path.join(hcp['hcp_Templates'], 'MNI152_T2_0.7mm_brain.nii.gz'),
                't2template2mm'     : os.path.join(hcp['hcp_Templates'], 'MNI152_T2_2mm.nii.gz'),
                'templatemask'      : os.path.join(hcp['hcp_Templates'], 'MNI152_T1_0.7mm_brain_mask.nii.gz'),
                'template2mmmask'   : os.path.join(hcp['hcp_Templates'], 'MNI152_T1_2mm_brain_mask_dil.nii.gz'),
                'brainsize'         : options['hcp_brainsize'],
                'fnirtconfig'       : os.path.join(hcp['hcp_Config'], 'T1_2_MNI152_2mm.cnf'),
                'fmapmag'           : hcp['fmapmag'],
                'fmapphase'         : hcp['fmapphase'],
                'fmapge'            : hcp['fmapge'],
                'echodiff'          : options['hcp_echodiff'],
                'SEPhaseNeg'        : seneg,
                'SEPhasePos'        : sepos,
                'echospacing'       : options['hcp_dwelltime'],
                'seunwarpdir'       : options['hcp_seunwarpdir'],
                't1samplespacing'   : options['hcp_t1samplespacing'],
                't2samplespacing'   : options['hcp_t2samplespacing'],
                'unwarpdir'         : options['hcp_unwarpdir'],
                'gdcoeffs'          : gdcoeffs,
                'avgrdcmethod'      : options['hcp_avgrdcmethod'],
                'topupconfig'       : topupconfig,
                'bfsigma'           : options['hcp_bfsigma'],
                'biascorrect'       : options['hcp_biascorrect_t1w']}

        tfile = os.path.join(hcp['T1w_folder'], 'T1w_acpc_dc_restore_brain.nii.gz')
        # tfile = os.path.join(hcp['T1w_folder'], '_PreFS.done')

        if run:
            if options['run'] == "run":
                # print "---> Running HCP Pre FS"
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)
                r += runExternalForFileShell(tfile, comm, '... running HCP PreFS', overwrite, sinfo['id'], remove=options['log'] == 'remove', task='hcpPreFS')
                r, status = checkForFile(r, tfile, 'ERROR: HCP PreFS failed running command: %s' % (comm))
                # print "---> Done with Pre FS"
                report = "Pre FS Done" if status else "Pre FS Failed"
            else:
                if os.path.exists(tfile):
                    r += "\n---> HCP PreFS completed"
                    # print "---> HCP PreFS completed"
                    report = "Pre FS done"
                else:
                    r += "\n---> HCP PreFS can be run"
                    # print "---> HCP PreFS can be run"
                    report = "Pre FS can be run"
        else:
            r += "\n---> Due to missing files subject can not be processed."
            # print "---> Due to missing files subject can not be processed."
            report = "Files missing, PreFS can not be run"

    except (ExternalFailed, NoSourceFolder), errormessage:
        # print "---> External failed"
        r += str(errormessage)
        report = "PreFS failed"
    except:
        # print "---> Unknown error"
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        report = "PreFS failed"

    # print "---> Completed %s HCP Pre FS" % (action("running", options['run']))
    r += "\n\nHCP PreFS %s on %s\n---------------------------------------------------------" % (action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return (r, (sinfo['id'], report))


def hcpFS(sinfo, options, overwrite=False, thread=0):
    '''hcp_FS command (hcp2)

    Runs the FS step of HCP Pipeline. It makes use of the linearly and nonlinearly registered T1w and T2w images from the PreFS step to run Freesurfer segmentation, surface reconstruction and optimization.

    It makes use of the following options:

    - hcp_suffix           ... Specifies a suffix to the subject id if multiple variants are run, empty otherwise.
    - hcp_t2               ... NONE if no T2w image is available, anything else otherwise.
    '''

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n\n%s HCP FreeSurfer Pipeline ...\n" % (action("Running", options['run']))

    run    = True
    report = "Error"

    try:
        hcp = getHCPPaths(sinfo, options)

        # --- run checks

        if 'hcp' not in sinfo:
            r += "\n---> ERROR: There is no hcp info for subject %s in subjects.txt" % (sinfo['id'])
            run = False

        # --- check for T1w and T2w images

        for tfile in hcp['T1w'].split("@"):
            if os.path.exists(tfile):
                r += "\n---> T1w image file present."
            else:
                r += "\n---> ERROR: Could not find T1w image file."
                run = False

        if hcp['T2w'] == 'NONE':
            r += "\n---> Not using T2w image."
        else:
            for tfile in hcp['T2w'].split("@"):
                if os.path.exists(tfile):
                    r += "\n---> T2w image file present."
                else:
                    r += "\n---> ERROR: Could not find T2w image file."
                    run = False

        # -> Pre FS results

        if os.path.exists(os.path.join(hcp['T1w_folder'], 'T1w_acpc_dc_restore_brain.nii.gz')):
            r += "\n---> PreFS results present."
        else:
            r += "\n---> ERROR: Could not find PreFS processing results."
            run = False

        # --- set up T2 NONE if needed

        if hcp['T2w'] == 'NONE':
            t2w = 'NONE'
        else:
            t2w = os.path.join(hcp['T1w_folder'], 'T2w_acpc_dc_restore.nii.gz')


        comm = '%(script)s \
            --subject="%(subject)s" \
            --subjectDIR="%(subjectDIR)s" \
            --ExpertFile="%(ExpertFile)s" \
            --t1="%(t1)s" \
            --t1brain="%(t1brain)s" \
            --t2="%(t2)s"' % {
                'script'            : os.path.join(hcp['hcp_base'], 'FreeSurfer', 'FreeSurferPipeline.sh'),
                'subject'           : sinfo['id'] + options['hcp_suffix'],
                'subjectDIR'        : hcp['T1w_folder'],
                'ExpertFile'        : options['hcp_expert_file'],
                't1'                : os.path.join(hcp['T1w_folder'], 'T1w_acpc_dc_restore.nii.gz'),
                't1brain'           : os.path.join(hcp['T1w_folder'], 'T1w_acpc_dc_restore_brain.nii.gz'),
                't2'                : t2w}

        if run:
            # tfile = os.path.join(hcp['T1w_folder'], sinfo['id'] + options['hcp_suffix'], 'mri', 'aparc+aseg.mgz')
            # tfile = os.path.join(hcp['T1w_folder'], '_FS.done')
            tfile = os.path.join(hcp['T1w_folder'], sinfo['id'] + options['hcp_suffix'], 'label', 'rh.entorhinal_exvivo.label')
            if options['run'] == "run":
                if overwrite and os.path.lexists(tfile):
                    os.remove(tfile)
                if overwrite or not os.path.exists(tfile):
                    if os.path.lexists(hcp['FS_folder']):
                        r += "\n---> removing preexisting FS folder [%s]" % (hcp['FS_folder'])
                        shutil.rmtree(hcp['FS_folder'])
                    for toremove in ['fsaverage', 'lh.EC_average', 'rh.EC_average']:
                        if os.path.lexists(os.path.join(hcp['T1w_folder'], toremove)):
                            os.remove(os.path.join(hcp['T1w_folder'], toremove))
                r += runExternalForFileShell(tfile, comm, '... running HCP FS', overwrite, sinfo['id'], remove=options['log'] == 'remove', task='hcpFS')
                r, status = checkForFile(r, tfile, 'ERROR: HCP FS failed running command: %s' % (comm))
                report = "FS Done" if status else "FS Failed"
            else:
                if os.path.exists(tfile):
                    r += "\n---> HCP FS completed"
                    report = "FS done"
                else:
                    r += "\n---> HCP FS can be run"
                    report = "FS can be run"
        else:
            r += "\n---> Subject can not be processed."
            report = "FS can not be run"

    except (ExternalFailed, NoSourceFolder), errormessage:
        r += str(errormessage)
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())

    r += "\n\nHCP FS %s on %s\n---------------------------------------------------------" % (action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return (r, (sinfo['id'], report))


def hcpPostFS(sinfo, options, overwrite=False, thread=0):
    '''hcp_PostFS command (hcp3)

    Runs the Post FS step of HCP Pipeline. It creates Workbench compatible files based on the Freesurfer segmentation and surface registration. It follows PreFS and FS steps.

    It makes use of the following options:

    - hcp_suffix           ... Specifies a suffix to the subject id if multiple variants are run, empty otherwise.
    - hcp_t2               ... NONE if no T2w image is available, anything else otherwise.
    - hcp_grayordinatesres ... The resolution of the grayordinate voxels (usually 2mm).
    - hcp_hiresmesh        ... Number of verteces in high-resolution mesh (164).
    - hcp_lowresmesh       ... Number of verteces in low-resolution mesh (32).
    - hcp_regname          ... Name of the registration to use (currently only FS).

    '''

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP PostFreeSurfer Pipeline ...\n" % (action("Running", options['run']))

    run    = True
    report = "Error"

    try:
        hcp = getHCPPaths(sinfo, options)

        # --- run checks

        if 'hcp' not in sinfo:
            r += "\n---> ERROR: There is no hcp info for subject %s in subjects.txt" % (sinfo['id'])
            run = False

        # --- check for T1w and T2w images

        for tfile in hcp['T1w'].split("@"):
            if os.path.exists(tfile):
                r += "\n---> T1w image file present."
            else:
                r += "\n---> ERROR: Could not find T1w image file."
                run = False

        if hcp['T2w'] == 'NONE':
            r += "\n---> Not using T2w image."
        else:
            for tfile in hcp['T2w'].split("@"):
                if os.path.exists(tfile):
                    r += "\n---> T2w image file present."
                else:
                    r += "\n---> ERROR: Could not find T2w image file."
                    run = False

        # -> Pre FS results

        if os.path.exists(os.path.join(hcp['T1w_folder'], 'T1w_acpc_dc_restore_brain.nii.gz')):
            r += "\n---> PreFS results present."
        else:
            r += "\n---> ERROR: Could not find PreFS processing results."
            run = False

        # -> FS results

        if os.path.exists(os.path.join(hcp['T1w_folder'], sinfo['id'] + options['hcp_suffix'], 'mri', 'aparc+aseg.mgz')):
            r += "\n---> FS results present."
        else:
            r += "\n---> ERROR: Could not find Freesurfer processing results."
            run = False

        comm = '%(script)s \
            --path="%(path)s" \
            --subject="%(subject)s" \
            --surfatlasdir="%(surfatlasdir)s" \
            --grayordinatesdir="%(grayordinatesdir)s" \
            --grayordinatesres="%(grayordinatesres)d" \
            --hiresmesh="%(hiresmesh)d" \
            --lowresmesh="%(lowresmesh)d" \
            --subcortgraylabels="%(subcortgraylabels)s" \
            --freesurferlabels="%(freesurferlabels)s" \
            --refmyelinmaps="%(refmyelinmaps)s" \
            --regname"%(regname)s"' % {
                'script'            : os.path.join(hcp['hcp_base'], 'PostFreeSurfer', 'PostFreeSurferPipeline.sh'),
                'path'              : sinfo['hcp'],
                'subject'           : sinfo['id'] + options['hcp_suffix'],
                'surfatlasdir'      : os.path.join(hcp['hcp_Templates'], 'standard_mesh_atlases'),
                'grayordinatesdir'  : os.path.join(hcp['hcp_Templates'], '91282_Greyordinates'),
                'grayordinatesres'  : options['hcp_grayordinatesres'],
                'hiresmesh'         : options['hcp_hiresmesh'],
                'lowresmesh'        : options['hcp_lowresmesh'],
                'subcortgraylabels' : os.path.join(hcp['hcp_Config'], 'FreeSurferSubcorticalLabelTableLut.txt'),
                'freesurferlabels'  : os.path.join(hcp['hcp_Config'], 'FreeSurferAllLut.txt'),
                'refmyelinmaps'     : os.path.join(hcp['hcp_Templates'], 'standard_mesh_atlases', 'Conte69.MyelinMap_BC.164k_fs_LR.dscalar.nii'),
                'regname'           : options['hcp_regname']}

        if run:
            # tfile = os.path.join(hcp['hcp_nonlin'], 'fsaverage_LR32k', sinfo['id'] + options['hcp_suffix'] + '.32k_fs_LR.wb.spec')
            # tfile = os.path.join(hcp['T1w_folder'], '_PostFS.done')
            tfile = os.path.join(hcp['T1w_folder'], 'ribbon.nii.gz')
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)
                r += runExternalForFileShell(tfile, comm, '... running HCP PostFS', overwrite, sinfo['id'], remove=options['log'] == 'remove', task='hcpPostFS')
                r, status = checkForFile(r, tfile, 'ERROR: HCP PostFS failed running command: %s' % (comm))
                if not status:
                    r += "\nEpected file %s not found!\n" % (tfile)
                report = "Post FS Done" if status else "Post FS Failed"
            else:
                if os.path.exists(tfile):
                    r += "\n---> HCP Post FS completed"
                    report = "Post FS done"
                else:
                    r += "\n---> HCP Post FS can be run"
                    report = "Post FS can be run"
        else:
            r += "\n---> Subject can not be processed."
            report = "Post FS can not be run"

    except (ExternalFailed, NoSourceFolder), errormessage:
        r += str(errormessage)
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())

    r += "\n\nHCP PostFS %s on %s\n---------------------------------------------------------" % (action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return (r, (sinfo['id'], report))


def hcpDiffusion(sinfo, options, overwrite=False, thread=0):
    """
    hcpDiffusion - documentation not yet available.
    """

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP DiffusionPreprocessing Pipeline ..." % (action("Running", options['run']))

    run    = True
    report = "Error"

    try:
        hcp = getHCPPaths(sinfo, options)

        if 'hcp' not in sinfo:
            r += "---> ERROR: There is no hcp info for subject %s in subjects.txt" % (sinfo['id'])
            run = False

        # --- set up data

        if options['hcp_dwi_PEdir'] == "1":
            direction = [('pos', 'RL'), ('neg', 'LR')]
        else:
            direction = [('pos', 'AP'), ('neg', 'PA')]

        dwiData = dict()
        for ddir, dext in direction:
            dwiData[ddir] = "@".join(glob.glob(os.path.join(hcp['DWI_folder'], "*_%s.nii.gz" % (dext))))

        # --- lookup gdcoeffs file if needed

        if options['hcp_dwi_gdcoeffs'] != 'NONE':
            if not os.path.exists(options['hcp_dwi_gdcoeffs']):
                gdcoeffs = os.path.join(hcp['hcp_Config'], options['hcp_dwi_gdcoeffs'])
                if not os.path.exists(gdcoeffs):
                    r += "---> ERROR: Could not find gradient distorsion coefficients file: %s." % (options['hcp_dwi_gdcoeffs'])
                    # raise AssertionError('Could not find gradient distorsion coefficients file!')
                    run = False
                else:
                    r += "---> Gradient distorsion coefficients file found."
            else:
                r += "---> Gradient distorsion coefficients file found."
        else:
            gdcoeffs = 'NONE'

        comm = '%(script)s \
            --posData="%(posData)s" \
            --negData="%(negData)s" \
            --path="%(path)s" \
            --subject="%(subject)s" \
            --echospacing="%(echospacing)s" \
            --PEdir=%(PEdir)s \
            --gdcoeffs="%(gdcoeffs)s" \
            --printcom="%(printcom)s"' % {
                'script'            : os.path.join(hcp['hcp_base'], 'DiffusionPreprocessing', 'DiffPreprocPipeline.sh'),
                'posData'           : dwiData['pos'],
                'negData'           : dwiData['neg'],
                'path'              : sinfo['hcp'],
                'subject'           : sinfo['id'] + options['hcp_suffix'],
                'echospacing'       : options['hcp_dwi_dwelltime'],
                'PEdir'             : options['hcp_dwi_PEdir'],
                'gdcoeffs'          : gdcoeffs,
                'printcom'          : options['hcp_printcom']}

        if run:
            tfile = os.path.join(hcp['T1w_folder'], 'Diffusion', 'data.nii.gz')
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)
                r += runExternalForFileShell(tfile, comm, '... running HCP Diffusion Preprocessing', overwrite, sinfo['id'], remove=options['log'] == 'remove', task='hcpDWI')
                r, status = checkForFile(r, tfile, 'ERROR: HCP Diffusion Preprocessing failed running command: %s' % (comm))
                if not status:
                    r += "\nEpected file %s not found!\n" % (tfile)
                report = "Diffusion done" if status else "Diffusion failed"
            else:
                if os.path.exists(tfile):
                    r += "---> HCP Diffusion completed"
                    report = "HCP Diffusion done"
                else:
                    r += "---> HCP Diffusion can be run"
                    report = "HCP Diffusion can be run"
        else:
            r += "---> Subject can not be processed."
            report = "HCP Diffusion can not be run"

    except (ExternalFailed, NoSourceFolder), errormessage:
        r += str(errormessage)
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())

    r += "\n\nHCP Diffusion Preprocessing %s on %s\n---------------------------------------------------------" % (action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return (r, (sinfo['id'], report))



def hcpfMRIVolume(sinfo, options, overwrite=False, thread=0):
    '''hcp_fMRIVolume command (hcp4)

    Runs the fMRI Volume step of HCP Pipeline. It preprocesses BOLD images and linearly and nonlinearly registers them to the MNI atlas. It makes use of the PreFS and FS steps of the pipeline.

    It makes use of the following options:

    - hcp_suffix             ... Specifies a suffix to the subject id if multiple variants are run, empty otherwise. []
    - hcp_bold_sequencetype  ... The type of the sequence used: multi(band) vs single(band). [multi]
    - hcp_bold_prefix        ... To be specified if multiple variants of BOLD processing are run. The prefix is prepended to the bold name. []
    - hcp_bold_echospacing   ... Echo Spacing or Dwelltime of BOLD images. [0.00035]
    - hcp_bold_ref           ... Whether BOLD image Reference images should be recorded - NONE or USE. [NONE]

    - hcp_bold_correct       ... BOLD image deformation correction: TOPUP, FIELDMAP / SiemensFieldMap, GeneralElectricFieldMap or NONE. [TOPUP]
    - hcp_bold_echodiff      ... Delta TE for BOLD fieldmap images or NONE if not used. [NONE]
    - hcp_bold_unwarpdir     ... The direction of unwarping, can be specified separately for LR/RL : 'LR=x|RL=-x|x'. [y]
    - hcp_bold_res           ... Target image resolution 2mm recommended. [2].
    - hcp_bold_gdcoeffs      ... Gradient distorsion correction coefficients or NONE. [NONE]

    - hcp_bold_stcorr        ... Whether to do slice timing correction TRUE or NONE". [TRUE]
    - hcp_bold_stcorrdir     ... The direction of slice acquisition. [up]
    - hcp_bold_stcorrint     ... Whether slices were acquired in an interleaved fashion (odd or even) or not (empty). [odd]

    - hcp_bold_preregister   ... What code to use to preregister BOLDs before FSL BBR epi_reg (default) or flirt. [epi_reg]
    - hcp_bold_movreg        ... Whether to use FLIRT (default and best for multiband images) or McFLIRT for motion correction. [FLIRT]

    - hcp_bold_movref        ... What reference to use for movement correction (independent, first). [independent]
    - hcp_bold_seimg         ... What image to use for spin-echo distorsion correction (independent, first). [independent]
    - hcp_bold_usemask       ... What mask to use for the bold images (T1: default, BOLD: mask based on bet of the scout, DILATED: dilated MNI brain mask, NONE: do not use a mask). [T1]
    - hcp_bold_refreg        ... Whether to use only linaer (default) or also nonlinear registration of motion corrected bold to reference. [linear]

    '''

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP fMRI Volume registration" % (action("Running", options['run']))

    run    = True
    report = {'done': [], 'failed': [], 'ready': [], 'not ready': []}

    try:

        # --- Base settings

        hcp = getHCPPaths(sinfo, options)

        # --- bold filtering not yet supported!
        # btargets = options['bppt'].split("|")

        # --- run checks

        if 'hcp' not in sinfo:
            r += "\n---> ERROR: There is no hcp info for subject %s in subjects.txt" % (sinfo['id'])
            run = False

        # --- check for T1w and T2w images

        for tfile in hcp['T1w'].split("@"):
            if os.path.exists(tfile):
                r += "\n---> T1w image file present."
            else:
                r += "\n---> ERROR: Could not find T1w image file."
                run = False

        if hcp['T2w'] == 'NONE':
            r += "\n---> Not using T2w image."
        else:
            for tfile in hcp['T2w'].split("@"):
                if os.path.exists(tfile):
                    r += "\n---> T2w image file present."
                else:
                    r += "\n---> ERROR: Could not find T2w image file."
                    run = False

        # -> Pre FS results

        if os.path.exists(os.path.join(hcp['T1w_folder'], 'T1w_acpc_dc_restore_brain.nii.gz')):
            r += "\n---> PreFS results present."
        else:
            r += "\n---> ERROR: Could not find PreFS processing results."
            run = False

        # -> FS results

        if os.path.exists(os.path.join(hcp['T1w_folder'], sinfo['id'] + options['hcp_suffix'], 'mri', 'aparc+aseg.mgz')):
            r += "\n---> FS results present."
        else:
            r += "\n---> ERROR: Could not find Freesurfer processing results."
            run = False

        # -> PostFS results

        if os.path.exists(os.path.join(hcp['hcp_nonlin'], 'fsaverage_LR32k', sinfo['id'] + options['hcp_suffix'] + '.32k_fs_LR.wb.spec')):
            r += "\n---> PostFS results present."
        else:
            r += "\n---> ERROR: Could not find PostFS processing results."
            run = False

        # --- Process unwarp direction

        unwarpdirs = [[f.strip() for f in e.strip().split("=")] for e in options['hcp_bold_unwarpdir'].split("|")]
        unwarpdirs = [['default', e[0]] if len(e) == 1 else e for e in unwarpdirs]
        unwarpdirs = dict(unwarpdirs)

        # --- Get sorted bold numbers

        bolds = [v for (k, v) in sinfo.iteritems() if k.isdigit()]
        bolds = [(int(e['name'].lower().replace('bold', '')), e) for e in bolds if 'bold' in e['name'].lower() and 'boldref' not in e['name'].lower()]
        bolds.sort()

        # --- Loop through bolds

        spinN     = 0
        spinOne   = "NONE"  # AP or LR
        spinTwo   = "NONE"  # PA or RL
        refimg    = "NONE"
        futureref = "NONE"

        for bold, boldinfo in bolds:

            try:

                # --- set unwarpdir

                if "o" in boldinfo:
                    orient    = "_" + boldinfo['o']
                    unwarpdir = unwarpdirs[boldinfo['o']]
                else:
                    orient = ""
                    unwarpdir = unwarpdirs['default']

                # --- set reference
                #
                # !!!! Need to make sure the right reference is used in relation to LR/RL AP/PA bolds
                # - have to keep track of whether an old topup in the same direction exists
                #


                r += "\n---> %s BOLD %d" % (action("Processing", options['run']), bold)
                boldok = True

                fmriref = futureref
                if options['hcp_bold_movref'] == 'first':
                    if futureref == "NONE":
                        futureref = "%s%d" % (options['hcp_bold_prefix'], bold)

                # --- check for bold image

                boldimg = os.path.join(hcp['base'], "BOLD_%d%s_fncb" % (bold, orient), "%s_fncb_BOLD_%d%s.nii.gz" % (sinfo['id'], bold, orient))
                r, boldok = checkForFile2(r, boldimg, '\n     ... bold image present', '\n     ... ERROR: bold image missing!', status=boldok)

                # --- check for ref image

                if options['hcp_bold_ref'].lower() == 'use':
                    refimg = os.path.join(hcp['base'], "BOLD_%d%s_SBRef_fncb" % (bold, orient), "%s_fncb_BOLD_%d%s_SBRef.nii.gz" % (sinfo['id'], bold, orient))
                    r, boldok = checkForFile2(r, refimg, '\n     ... reference image present', '\n     ... ERROR: bold reference image missing!', status=boldok)

                # --- are we using previous reference

                if fmriref is not "NONE":
                    r += '\n     ... using %s as movement correction reference' % (fmriref)


                # --- check for spin-echo-fieldmap image

                if options['hcp_bold_correct'].lower() == 'topup':
                    if spinN > 0 and (not os.path.exists(os.path.join(hcp['base'], "SpinEchoFieldMap%d_fncb" % (bold))) or options['hcp_bold_seimg'] == 'first'):
                        r += "\n     ... using spin echo fieldmap set %d" % (spinN)
                    else:
                        if spinN > 0:
                            r += '\n     ... found new spin echo fieldmap set [%d]' % (bold)

                        fmriref = "NONE"
                        # need to turn this off for multiband LR/RL
                        if options['hcp_bold_movref'] == 'first':
                            futureref = "%s%d" % (options['hcp_bold_prefix'], bold)

                        if os.path.exists(os.path.join(hcp['base'], "SpinEchoFieldMap%d_fncb" % (bold), "%s_fncb_BOLD_AP_SB_SE.nii.gz" % (sinfo['id']))):
                            spinOne = os.path.join(hcp['base'], "SpinEchoFieldMap%d_fncb" % (bold), "%s_fncb_BOLD_AP_SB_SE.nii.gz" % (sinfo['id']))
                            spinTwo = os.path.join(hcp['base'], "SpinEchoFieldMap%d_fncb" % (bold), "%s_fncb_BOLD_PA_SB_SE.nii.gz" % (sinfo['id']))
                        elif os.path.exists(os.path.join(hcp['base'], "SpinEchoFieldMap%d_fncb" % (bold), "%s_fncb_BOLD_LR_SB_SE.nii.gz" % (sinfo['id']))):
                            spinOne = os.path.join(hcp['base'], "SpinEchoFieldMap%d_fncb" % (bold), "%s_fncb_BOLD_LR_SB_SE.nii.gz" % (sinfo['id']))
                            spinTwo = os.path.join(hcp['base'], "SpinEchoFieldMap%d_fncb" % (bold), "%s_fncb_BOLD_RL_SB_SE.nii.gz" % (sinfo['id']))

                        spinok = True
                        r, spinok = checkForFile2(r, spinOne, '\n     ... spin echo fildmap AP/LR image present', '\n     ... ERROR: spin echo fildmap AP/LR image missing!', status=spinok)
                        r, spinok = checkForFile2(r, spinTwo, '\n     ... spin echo fildmap PA/RL image present', '\n     ... ERROR: spin echo fildmap PA/RL image missing!', status=spinok)
                        if spinok:
                            spinN = bold
                        boldok = boldok and spinok

                # --- check for Siemens double TE-fieldmap image

                elif options['hcp_bold_correct'].lower() in ['fieldmap', 'siemensfieldmap']:
                    fieldok = True
                    r, fieldok = checkForFile2(r, hcp['fmapmag'], '\n     ... Siemens fieldmap magnitude image present ', '\n     ... ERROR: Siemens fieldmap magnitude image missing!', status=fieldok)
                    r, fieldok = checkForFile2(r, hcp['fmapphase'], '\n     ... Siemens fieldmap phase image present ', '\n     ... ERROR: Siemens fieldmap phase image missing!', status=fieldok)
                    if not is_number(options['hcp_bold_echospacing']):
                        fieldok = False
                        r += '\n     ... ERROR: hcp_bold_echospacing not defined correctly: "%s"!' % (options['hcp_bold_echospacing'])
                    if not is_number(options['hcp_bold_echodiff']):
                        fieldok = False
                        r += '\n     ... ERROR: hcp_bold_echodiff not defined correctly: "%s"!' % (options['hcp_bold_echodiff'])
                    boldok = boldok and fieldok

                # --- check for GE fieldmap image

                elif options['hcp_bold_correct'].lower() in ['generalelectricfieldmap']:
                    fieldok = True
                    r, fieldok = checkForFile2(r, hcp['fmapge'], '\n     ... GeneralElectric fieldmap image present ', '\n     ... ERROR: GeneralElectric fieldmap image missing!', status=fieldok)
                    boldok = boldok and fieldok

                # --- NO DC used

                elif options['hcp_bold_correct'].lower() in ['none']:
                    r += '\n     ... No distortion correction used '

                # --- ERROR

                else:
                    r += '\n     ... ERROR: Unknown distortion correction method: %s! Please check your settings!' % (options['hcp_bold_correct'])
                    boldok = False


                # --- process additional parameters

                hcp_bold_stcorrdir = ''
                hcp_bold_stcorrint = ''

                if options['hcp_bold_stcorr'].lower() == 'true':
                    if options['hcp_bold_stcorrdir'] == 'down':
                        hcp_bold_stcorrdir = '--down'
                    if options['hcp_bold_stcorrint'] == 'odd':
                        hcp_bold_stcorrint = "--odd"
                    elif options['hcp_bold_stcorrint'] == 'even':
                        hcp_bold_stcorrint = "--even"

                comm = '%(script)s \
                    --path="%(path)s" \
                    --subject="%(subject)s" \
                    --fmriname="%(prefix)s%(boldn)d" \
                    --fmritcs="%(boldimg)s" \
                    --fmriscout="%(refimg)s" \
                    --SEPhaseNeg="%(spinOne)s" \
                    --SEPhasePos="%(spinTwo)s" \
                    --fmapmag="%(fmapmag)s" \
                    --fmapphase="%(fmapphase)s" \
                    --fmapgeneralelectric="%(fmapge)s" \
                    --echospacing="%(echospacing)s" \
                    --echodiff="%(echodiff)s" \
                    --unwarpdir="%(unwarpdir)s" \
                    --fmrires="%(fmrires)s" \
                    --dcmethod="%(dcmethod)s" \
                    --gdcoeffs="%(gdcoeffs)s" \
                    --topupconfig="%(topupconfig)s" \
                    --printcom="%(printcom)s" \
                    --doslicetime="%(doslicetime)s" \
                    --slicetimedir="%(slicetimedir)s" \
                    --slicetimeodd="%(slicetimeodd)s" \
                    --sequencetype="%(sequencetype)s" \
                    --fmriref="%(fmriref)s" \
                    --usemask="%(usemask)s" \
                    --preregister="%(preregister)s" \
                    --refreg="%(refreg)s" \
                    --movreg="%(movreg)s" \
                    --tr="%(tr)f"' % {
                        'script'            : os.path.join(hcp['hcp_base'], 'fMRIVolume', 'GenericfMRIVolumeProcessingPipeline.sh'),
                        'path'              : sinfo['hcp'],
                        'subject'           : sinfo['id'] + options['hcp_suffix'],
                        'prefix'            : options['hcp_bold_prefix'],
                        'boldn'             : bold,
                        'boldimg'           : boldimg,
                        'refimg'            : refimg,
                        'spinOne'           : spinOne,
                        'spinTwo'           : spinTwo,
                        'fmapmag'           : hcp['fmapmag'],
                        'fmapphase'         : hcp['fmapphase'],
                        'fmapge'            : hcp['fmapge'],
                        'echospacing'       : options['hcp_bold_echospacing'],
                        'echodiff'          : options['hcp_bold_echodiff'],
                        'unwarpdir'         : unwarpdir,
                        'fmrires'           : options['hcp_bold_res'],
                        'dcmethod'          : options['hcp_bold_correct'],
                        'gdcoeffs'          : options['hcp_bold_gdcoeffs'],
                        'topupconfig'       : os.path.join(hcp['hcp_Config'], 'b02b0.cnf'),
                        'printcom'          : options['hcp_printcom'],
                        'doslicetime'       : options['hcp_bold_stcorr'].upper(),
                        'slicetimedir'      : hcp_bold_stcorrdir,
                        'slicetimeodd'      : hcp_bold_stcorrint,
                        'tr'                : options['TR'],
                        'sequencetype'      : options['hcp_bold_sequencetype'],
                        'preregister'       : options['hcp_bold_preregister'],
                        'refreg'            : options['hcp_bold_refreg'],
                        'movreg'            : options['hcp_bold_movreg'],
                        'fmriref'           : fmriref,
                        'usemask'           : options['hcp_bold_usemask']}

                if run and boldok:
                    tfile = os.path.join(hcp['hcp_nonlin'], 'Results', "%s%d" % (options['hcp_bold_prefix'], bold), "%s%d.nii.gz" % (options['hcp_bold_prefix'], bold))
                    if options['run'] == "run":
                        if overwrite and os.path.exists(tfile):
                            os.remove(tfile)
                        r += runExternalForFileShell(tfile, comm, '     ... running HCP fMRIVolume', overwrite, sinfo['id'], remove=options['log'] == 'remove', task='hcpfMRIVolume_B%d' % (bold))
                        r, status = checkForFile(r, tfile, '     ... ERROR: HCP fMRIVolume failed running command: %s' % (comm))
                        if status:
                            report['done'].append(str(bold))
                        else:
                            report['failed'].append(str(bold))
                    else:
                        if os.path.exists(tfile):
                            r += "\n     ... HCP fMRIVolume done"
                            report['done'].append(str(bold))
                        else:
                            r += "\n     ... HCP fMRIVolume can be run"
                            report['ready'].append(str(bold))
                elif run:
                    report['not ready'].append(str(bold))
                    if options['run'] == "run":
                        r += "\n     ... ERROR: images or data parameters missing, skipping this BOLD!"
                    else:
                        r += "\n     ... ERROR: images or data parameters missing, this bold would be skipped BOLD!"
                else:
                    report['not ready'].append(str(bold))
                    if options['run'] == "run":
                        r += "\n     ... ERROR: No hcp info for subject, skipping this BOLD!"
                    else:
                        r += "\n     ... ERROR: No hcp info for subject, this bold would be skipped BOLD!"

            except (ExternalFailed, NoSourceFolder), errormessage:
                r += "\n ---  Failed during processing of bold %d with error:\n" % (bold)
                r += str(errormessage)
                report['failed'].append(str(bold))
            except:
                r += "\n ---  Failed during processing of bold %d with error:\n %s\n" % (bold, traceback.format_exc())
                report['failed'].append(str(bold))

            r += "\n     ... DONE!"

        rep = []
        for k in ['done', 'failed', 'ready', 'not ready']:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))
        report = (sinfo['id'], "HCP fMRI Volume: bolds " + "; ".join(rep))

    except (ExternalFailed, NoSourceFolder), errormessage:
        r += str(errormessage)
        report = (sinfo['id'], 'HCP fMRI Volume failed')
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        report = (sinfo['id'], 'HCP fMRI Volume failed')

    r += "\n\nHCP fMRIVolume %s on %s\n---------------------------------------------------------" % (action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return (r, report)


def hcpfMRISurface(sinfo, options, overwrite=False, thread=0):
    '''hcp_fMRISurface command (hcp5)

    Runs the fMRI Surface step of HCP Pipeline. It maps BOLD data prepared in the prvious step to surface and creates a grayordinate representation of the data.

    It makes use of the following options:

    - hcp_suffix           ... Specifies a suffix to the subject id if multiple variants are run, empty otherwise. []
    - hcp_bold_prefix      ... To be specified if multiple variants of BOLD processing are run. The prefix is prepended to the bold name. []
    - hcp_lowresmesh       ... The number of vertices used in the low-resolution grayordinate mesh. [32]
    - hcp_bold_res         ... The resolution of the BOLD volume data in mm. [2]
    - hcp_grayordinatesres ... The size of voxels for the subcortical and cerebellar data in grayordinate space in mm. [2]
    - hcp_bold_smoothFWHM  ... The size of the smoothing kernel. [2]
    - hcp_regname          ... The name of the registration used. [FS]

    '''

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP fMRI Surface registration" % (action("Running", options['run']))

    run    = True
    report = {'done': [], 'failed': [], 'ready': [], 'not ready': []}

    try:

        # --- Base settings

        hcp = getHCPPaths(sinfo, options)

        # --- bold filtering not yet supported!
        # btargets = options['bppt'].split("|")

        # --- run checks

        if 'hcp' not in sinfo:
            r += "\n---> ERROR: There is no hcp info for subject %s in subjects.txt" % (sinfo['id'])
            run = False

        # --- check for T1w and T2w images

        for tfile in hcp['T1w'].split("@"):
            if os.path.exists(tfile):
                r += "\n---> T1w image file present."
            else:
                r += "\n---> ERROR: Could not find T1w image file."
                run = False

        if hcp['T2w'] == 'NONE':
            r += "\n---> Not using T2w image."
        else:
            for tfile in hcp['T2w'].split("@"):
                if os.path.exists(tfile):
                    r += "\n---> T2w image file present."
                else:
                    r += "\n---> ERROR: Could not find T2w image file."
                    run = False

        # -> Pre FS results

        if os.path.exists(os.path.join(hcp['T1w_folder'], 'T1w_acpc_dc_restore_brain.nii.gz')):
            r += "\n---> PreFS results present."
        else:
            r += "\n---> ERROR: Could not find PreFS processing results."
            run = False

        # -> FS results

        if os.path.exists(os.path.join(hcp['T1w_folder'], sinfo['id'] + options['hcp_suffix'], 'mri', 'aparc+aseg.mgz')):
            r += "\n---> FS results present."
        else:
            r += "\n---> ERROR: Could not find Freesurfer processing results."
            run = False

        # -> PostFS results

        if os.path.exists(os.path.join(hcp['hcp_nonlin'], 'fsaverage_LR32k', sinfo['id'] + options['hcp_suffix'] + '.32k_fs_LR.wb.spec')):
            r += "\n---> PostFS results present."
        else:
            r += "\n---> ERROR: Could not find PostFS processing results."
            run = False

        # --- Get sorted bold numbers

        bolds = [v for (k, v) in sinfo.iteritems() if k.isdigit()]
        bolds = [int(e['name'].lower().replace('bold', '')) for e in bolds if 'bold' in e['name'].lower() and 'boldref' not in e['name'].lower()]
        bolds.sort()

        # --- Loop through bolds

        for bold in bolds:

            try:
                r += "\n---> Processing BOLD %d" % (bold)
                boldok = True

                # --- check for bold image

                boldimg = os.path.join(hcp['hcp_nonlin'], 'Results', "%s%d" % (options['hcp_bold_prefix'], bold), "%s%d.nii.gz" % (options['hcp_bold_prefix'], bold))
                r, boldok = checkForFile2(r, boldimg, '\n     ... preprocessed bold image present', '\n     ... ERROR: preprocessed bold image missing!', status=boldok)

                comm = '%(script)s \
                    --path="%(path)s" \
                    --subject="%(subject)s" \
                    --fmriname="%(prefix)s%(boldn)d" \
                    --lowresmesh="%(lowresmesh)s" \
                    --fmrires="%(fmrires)s" \
                    --smoothingFWHM="%(smoothingFWHM)s" \
                    --grayordinatesres="%(grayordinatesres)d" \
                    --regname"%(regname)s"' % {
                        'script'            : os.path.join(hcp['hcp_base'], 'fMRISurface', 'GenericfMRISurfaceProcessingPipeline.sh'),
                        'path'              : sinfo['hcp'],
                        'subject'           : sinfo['id'] + options['hcp_suffix'],
                        'prefix'            : options['hcp_bold_prefix'],
                        'boldn'             : bold,
                        'lowresmesh'        : options['hcp_lowresmesh'],
                        'fmrires'           : options['hcp_bold_res'],
                        'smoothingFWHM'     : options['hcp_bold_smoothFWHM'],
                        'grayordinatesres'  : options['hcp_grayordinatesres'],
                        'regname'           : options['hcp_regname']}


                if run and boldok:
                    tfile = os.path.join(hcp['hcp_nonlin'], 'Results', "%s%d" % (options['hcp_bold_prefix'], bold), "%s%d_Atlas.dtseries.nii" % (options['hcp_bold_prefix'], bold))
                    if options['run'] == "run":
                        if overwrite and os.path.exists(tfile):
                            os.remove(tfile)
                        r += runExternalForFileShell(tfile, comm, '     ... running HCP fMRISurface', overwrite, sinfo['id'], remove=options['log'] == 'remove', task='hcpfMRISurface_B%d' % (bold))
                        r, status = checkForFile(r, tfile, '     ... ERROR: HCP fMRISurface failed running command: %s' % (comm))
                        if status:
                            report['done'].append(str(bold))
                        else:
                            report['failed'].append(str(bold))
                    else:
                        if os.path.exists(tfile):
                            r += "\n     ... HCP fMRISurface done"
                            report['done'].append(str(bold))
                        else:
                            r += "\n     ... HCP fMRISurface can be run"
                            report['ready'].append(str(bold))
                elif run:
                    report['not ready'].append(str(bold))
                    if options['run'] == "run":
                        r += "\n     ... ERROR: images missing, skipping this BOLD!"
                    else:
                        r += "\n     ... ERROR: images missing, this bold would be skipped BOLD!"
                else:
                    report['not ready'].append(str(bold))
                    if options['run'] == "run":
                        r += "\n     ... ERROR: No hcp info for subject, skipping this BOLD!"
                    else:
                        r += "\n     ... ERROR: No hcp info for subject, this bold would be skipped BOLD!"

            except (ExternalFailed, NoSourceFolder), errormessage:
                r += "\n ---  Failed during processing of bold %d with error:\n" % (bold)
                r += str(errormessage)
                report['failed'].append(str(bold))
            except:
                r += "\n ---  Failed during processing of bold %d with error:\n %s\n" % (bold, traceback.format_exc())
                report['failed'].append(str(bold))

            r += "\n     ... DONE!"

        rep = []
        for k in ['done', 'failed', 'ready', 'not ready']:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))
        report = (sinfo['id'], "HCP fMRI Surface: bolds " + "; ".join(rep))

    except (ExternalFailed, NoSourceFolder), errormessage:
        r += str(errormessage)
        report = (sinfo['id'], 'HCP fMRI Surface failed')
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        report = (sinfo['id'], 'HCP fMRI Surface failed')

    r += "\n\nHCP fMRISurface %s on %s\n---------------------------------------------------------" % (action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return (r, report)


def hcpDTIFit(sinfo, options, overwrite=False, thread=0):
    """
    hcpDTIFit - documentation not yet available.
    """

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP DTI Fix ..." % (action("Running", options['run']))

    run    = True
    report = "Error"

    try:
        hcp = getHCPPaths(sinfo, options)

        if 'hcp' not in sinfo:
            r += "---> ERROR: There is no hcp info for subject %s in subjects.txt" % (sinfo['id'])
            run = False

        for tfile in ['bvals', 'bvecs', 'data.nii.gz', 'nodif_brain_mask.nii.gz']:
            if not os.path.exists(os.path.join(hcp['T1w_folder'], 'Diffusion', tfile)):
                r += "---> ERROR: Could not find %s file!" % (tfile)
                run = False
            else:
                r += "---> %s found!" % (tfile)

        comm = 'dtifit \
            --data="%(data)s" \
            --out="%(out)s" \
            --mask="%(mask)s" \
            --bvecs="%(bvecs)s" \
            --bvals="%(bvals)s"' % {
                'data'              : os.path.join(hcp['T1w_folder'], 'Diffusion', 'data'),
                'out'               : os.path.join(hcp['T1w_folder'], 'Diffusion', 'dti'),
                'mask'              : os.path.join(hcp['T1w_folder'], 'Diffusion', 'nodif_brain_mask'),
                'bvecs'             : os.path.join(hcp['T1w_folder'], 'Diffusion', 'bvecs'),
                'bvals'             : os.path.join(hcp['T1w_folder'], 'Diffusion', 'bvals')}

        if run:
            tfile = os.path.join(hcp['T1w_folder'], 'Diffusion', 'dti_FA.nii.gz')
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)
                r += runExternalForFileShell(tfile, comm, '... running HCP DTI Fit', overwrite, sinfo['id'], remove=options['log'] == 'remove', task='hcpDTIFix')
                r, status = checkForFile(r, tfile, 'ERROR: DTI Fit failed running command: %s' % (comm))
                if not status:
                    r += "\nEpected file %s not found!\n" % (tfile)
                report = "DTI Fit done" if status else "DTI Fit failed"
            else:
                if os.path.exists(tfile):
                    r += "---> HCP DTI Fit completed"
                    report = "HCP DTI Fit done"
                else:
                    r += "---> HCP DTI Fit can be run"
                    report = "HCP DTI Fit can be run"
        else:
            r += "---> Subject can not be processed."
            report = "HCP DTI Fit can not be run"

    except (ExternalFailed, NoSourceFolder), errormessage:
        r += str(errormessage)
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())

    r += "\n\nHCP Diffusion Preprocessing %s on %s\n---------------------------------------------------------" % (action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return (r, (sinfo['id'], report))


def hcpBedpostx(sinfo, options, overwrite=False, thread=0):
    """
    hcpBedpostx - documentation not yet available.
    """

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP Bedpostx GPU ..." % (action("Running", options['run']))

    run    = True
    report = "Error"

    try:
        hcp = getHCPPaths(sinfo, options)

        if 'hcp' not in sinfo:
            r += "---> ERROR: There is no hcp info for subject %s in subjects.txt" % (sinfo['id'])
            run = False

        for tfile in ['bvals', 'bvecs', 'data.nii.gz', 'nodif_brain_mask.nii.gz']:
            if not os.path.exists(os.path.join(hcp['T1w_folder'], 'Diffusion', tfile)):
                r += "---> ERROR: Could not find %s file!" % (tfile)
                run = False

        for tfile in ['FA', 'L1', 'L2', 'L3', 'MD', 'MO', 'S0', 'V1', 'V2', 'V3']:
            if not os.path.exists(os.path.join(hcp['T1w_folder'], 'Diffusion', 'dti_' + tfile + '.nii.gz')):
                r += "---> ERROR: Could not find %s file!" % (tfile)
                run = False
        if not run:
            r += "---> all necessary files found!"

        comm = 'fslbedpostx_gpu \
            %(data)s \
            --nf=%(nf)s \
            --rician \
            --model="%(model)s"' % {
                'data'              : os.path.join(hcp['T1w_folder'], 'Diffusion', '.'),
                'nf'                : "3",
                'model'             : "2"}

        if run:
            tfile = os.path.join(hcp['T1w_folder'], 'Diffusion.bedpostX', 'mean_fsumsamples.nii.gz')
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)
                r += runExternalForFileShell(tfile, comm, '... running HCP BedpostX', overwrite, sinfo['id'], remove=options['log'] == 'remove', task='hcpBedpostx')
                r, status = checkForFile(r, tfile, 'ERROR: HCP BedpostX failed running command: %s' % (comm))
                if not status:
                    r += "\nEpected file %s not found!\n" % (tfile)
                report = "BedpostX done" if status else "BedpostX failed"
            else:
                if os.path.exists(tfile):
                    r += "---> HCP BedpostX completed"
                    report = "HCP BedpostX done"
                else:
                    r += "---> HCP BedpostX can be run"
                    report = "HCP BedpostX can be run"
        else:
            r += "---> Subject can not be processed."
            report = "HCP BedpostX can not be run"

    except (ExternalFailed, NoSourceFolder), errormessage:
        r += str(errormessage)
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())

    r += "\n\nHCP Diffusion Preprocessing %s on %s\n---------------------------------------------------------" % (action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return (r, (sinfo['id'], report))


def mapHCPData(sinfo, options, overwrite=False, thread=0):
    """
    mapHCPData [... processing options]

    mapHCPData maps the results of the HCP preprocessing (in MNINonLinear) to
    the <basefolder>/<subject id>/images folder structure. Specifically, it
    copies the files and folders:

    * T1w.nii.gz                  -> images/structural/T1w.nii.gz
    * aparc+aseg.nii.gz           -> images/segmentation/freesurfer/mri/aparc+aseg_t1.nii.gz
                                  -> images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz
                                     (2mm iso downsampled version)
    * fsaverage_LR32k/*           -> images/segmentation/hcp/fsaverage_LR32k
    * BOLD_[N].nii.gz             -> images/functional/[boldname][N].nii.gz
    * BOLD_[N][tail].dtseries.nii -> images/functional/[boldname][N][tail].dtseries.nii
    * Movement_Regressors.txt     -> images/functional/movement/[boldname][N]_mov.dat

    The relevant processing parameters are:

    --subjects        ... The subjects.txt file with all the subject information
                          [subject.txt].
    --basefolder      ... The path to the study/subjects folder, where the
                          imaging  data is supposed to go [.].
    --cores           ... How many cores to utilize [1].
    --overwrite       ... Whether to overwrite existing data (yes) or not (no)
                          [no].
    --hcp_cifti_tail  ... The tail (see above) that specifies, which version of
                          the cifti files to copy over [].
    --bold_preprocess ... Which bold images (as they are specified in the
                          subjects.txt file) to copy over. It can be a single
                          type (e.g. 'task'), a pipe separated list (e.g.
                          'WM|Control|rest') or 'all' to copy all [rest].
    --boldname        ... The default name of the bold files in the images
                          folder [bold].

    The parameters can be specified in command call or subject.txt file.
    If possible, the files are not copied but rather hard links are created to
    save space. If hard links can not be created, the files are copied.

    Example use:
    gmri mapHCPdata subjects=fcMRI/subjects.hcp.txt basefolder=subjects \\
         overwrite=no hcp_cifti_tail=_Atlas bold-preprocess=all

    (c) Grega Repovš

    Changelog
    2016-12-24 - Grega Repovš - Added documentation, fixed copy of volume images.
    """

    bsearch = re.compile('bold([0-9]+)')

    r = "\n---------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\nMapping HCP data ..."

    # --- file/dir structure


    f = getFileNames(sinfo, options)
    d = getSubjectFolders(sinfo, options)

    #    MNINonLinear/Results/<boldname>/<boldname>.nii.gz -- volume
    #    MNINonLinear/Results/<boldname>/<boldname>_Atlas.dtseries.nii -- cifti
    #    MNINonLinear/Results/<boldname>/Movement_Regressors.txt -- movement
    #    MNINonLinear/T1w.nii.gz -- atlas T1 hires
    #    MNINonLinear/aparc+aseg.nii.gz -- FS hires segmentation

    # ------------------------------------------------------------------------------------------------------------
    #                                                                                      map T1 and segmentation

    report = {}

    r += "\n\nStructural data: ..."
    status = True

    if os.path.exists(f['t1']) and not overwrite:
        r += "\n ... T1 ready"
        report['T1'] = 'present'
    else:
        status, r = linkOrCopy(os.path.join(d['hcp'], 'MNINonLinear', 'T1w.nii.gz'), f['t1'], r, status, "T1")
        report['T1'] = 'copied'

    if os.path.exists(f['fs_aparc_t1']) and not overwrite:
        r += "\n ... highres aseg+aparc ready"
        report['hires aseg+aparc'] = 'present'
    else:
        status, r = linkOrCopy(os.path.join(d['hcp'], 'MNINonLinear', 'aparc+aseg.nii.gz'), f['fs_aparc_t1'], r, status, "highres aseg+aparc")
        report['hires aseg+aparc'] = 'copied'

    if os.path.exists(f['fs_aparc_bold']) and not overwrite:
        r += "\n ... lowres aseg+aparc ready"
        report['lores aseg+aparc'] = 'present'
    else:
        if os.path.exists(f['fs_aparc_bold']):
            os.remove(f['fs_aparc_bold'])
        if os.path.exists(os.path.join(d['hcp'], 'MNINonLinear', 'T1w_restore.2.nii.gz')) and os.path.exists(f['fs_aparc_t1']):
            r += runExternalForFile(f['fs_aparc_bold'], '3dresample -rmode NN -master %s -inset %s -prefix %s ' % (os.path.join(d['hcp'], 'MNINonLinear', 'T1w_restore.2.nii.gz'), f['fs_aparc_t1'], f['fs_aparc_bold']), ' ... resampling t1 cortical segmentation (%s) to bold space (%s)' % (os.path.basename(f['fs_aparc_t1']), os.path.basename(f['fs_aparc_bold'])), overwrite, sinfo['id'])
            report['lores aseg+aparc'] = 'generated'
        else:
            r += "\n ... ERROR: could not generate downsampled aseg+aparc, files missing!"
            report['lores aseg+aparc'] = 'failed'
            status = False

    report['surface'] = 'ok'
    if os.path.exists(os.path.join(d['hcp'], 'MNINonLinear', 'fsaverage_LR32k')):
        r += "\n ... processing surface files"
        sfiles = glob.glob(os.path.join(d['hcp'], 'MNINonLinear', 'fsaverage_LR32k', '*.*'))
        npre, ncp = 0, 0
        if len(sfiles):
            sid = os.path.basename(sfiles[0]).split(".")[0]
        for sfile in sfiles:
            tfile = os.path.join(d['s_s32k'], ".".join(os.path.basename(sfile).split(".")[1:]))
            if os.path.exists(tfile) and not overwrite:
                npre += 1
            else:
                if ".spec" in tfile:
                    s = file(sfile).read()
                    s = s.replace(sid + ".", "")
                    tf = open(tfile, 'w')
                    print >> tf, s
                    tf.close()
                    r += "\n     -> updated .spec file [%s]" % (sid)
                    ncp += 1
                    continue
                if linkOrCopy(sfile, tfile):
                    ncp += 1
                else:
                    r += "\n     -> ERROR: could not map or copy %s" % (sfile)
                    report['surface'] = 'error'
        if npre:
            r += "\n     -> %d files already copied" % (npre)
        if ncp:
            r += "\n     -> copied %d surface files" % (ncp)
    else:
        r += "\n ... ERROR: missing folder: %s!" % (os.path.join(d['hcp'], 'MNINonLinear', 'fsaverage_LR32k'))
        status = False
        report['surface'] = 'error'

    # ------------------------------------------------------------------------------------------------------------
    #                                                                                          map functional data

    r += "\n\nFunctional data: ... [%s]" % (options['hcp_cifti_tail'])

    btargets = options['bppt'].split("|")

    report['boldok'] = 0
    report['boldfail'] = 0

    for (k, v) in sinfo.iteritems():
        if k.isdigit():
            bnum = bsearch.match(v['name'])
            if bnum:
                if v['task'] in btargets or options['bppt'] == 'all':

                    boldname = v['name']
                    r += "\n ... " + boldname
                    bnum = bnum.group(1)

                    # --- filenames
                    options['image_target'] = 'nifti'        # -- needs to be set to correctly copy volume files
                    f.update(getBOLDFileNames(sinfo, boldname, options))

                    status = True
                    bname  = ""

                    try:
                        if 'bold' in v:
                            bname = v['bold']
                        else:
                            for posb in ["%s", "bold%s", "BOLD%s", "BOLD_%s"]:
                                if os.path.exists(os.path.join(d['hcp'], 'MNINonLinear', 'Results', posb % (bnum))):
                                    bname = posb % (bnum)
                                    break
                            if bname == "":
                                r += "\n     ... ERROR: could not identify HCP boldname for %s!" % (boldname)
                                status = False
                                raise NoSourceFolder(r)
                        boldpath = os.path.join(d['hcp'], 'MNINonLinear', 'Results', bname)

                        if os.path.exists(f['bold']) and not overwrite:
                            r += "\n     ... volume image ready"
                        else:
                            status, r = linkOrCopy(os.path.join(boldpath, bname + '.nii.gz'), f['bold'], r, status, "volume image", "\n     ... ")

                        if os.path.exists(f['bold_dts']) and not overwrite:
                            r += "\n     ... grayordinate image ready"
                        else:
                            r += "\n     ... linking %s to %s" % (os.path.join(boldpath, bname + options['hcp_cifti_tail'] + '.dtseries.nii'), f['bold_dts'])
                            status, r = linkOrCopy(os.path.join(boldpath, bname + options['hcp_cifti_tail'] + '.dtseries.nii'), f['bold_dts'], r, status, "grayordinate image", "\n     ... ")

                        if os.path.exists(f['bold_mov']) and not overwrite:
                            r += "\n     ... movement data ready"
                        else:
                            if os.path.exists(os.path.join(boldpath, 'Movement_Regressors.txt')):
                                mdata = [line.strip().split() for line in open(os.path.join(boldpath, 'Movement_Regressors.txt'))]
                                mfile = open(f['bold_mov'], 'w')
                                print >> mfile, "#frame     dx(mm)     dy(mm)     dz(mm)     X(deg)     Y(deg)     Z(deg)"
                                c = 0
                                for mline in mdata:
                                    c += 1
                                    mline = "%6d   %s" % (c, "   ".join(mline[0:6]))
                                    print >> mfile, mline.replace(' -', '-')
                                mfile.close()
                                r += "\n     ... movement data prepared"
                            else:
                                r += "\n     ... ERROR: could not prepare movement data, source does not exist: %s" % os.path.join(boldpath, 'Movement_Regressors.txt')
                                status = False

                        if status:
                            r += "\n     ---> Data ready!\n"
                            report['boldok'] += 1
                        else:
                            r += "\n     ---> ERROR: Data missing, please check source!\n"
                            report['boldfail'] += 1

                    except (ExternalFailed, NoSourceFolder), errormessage:
                        r += str(errormessage)
                    except:
                        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
                        time.sleep(3)

    r += "\nHCP data mapping completed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    rstatus = "T1: %(T1)s, aseg+aparc hires: %(hires aseg+aparc)s lores: %(lores aseg+aparc)s, surface: %(surface)s, bolds ok: %(boldok)d, bolds failed: %(boldfail)d" % (report)

    print r
    return (r, (sinfo['id'], rstatus))
