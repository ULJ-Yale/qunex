#!/usr/bin/env python2.7
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``process_hcp.py``

This file holds code for running HCP preprocessing pipeline. It
consists of functions:

--hcp_pre_preesurfer        Runs HCP PreFS preprocessing.
--hcp_freesurfer            Runs HCP FS preprocessing.
--hcp_post_freesurfer       Runs HCP PostFS preprocessing.
--hcp_diffusion             Runs HCP Diffusion weighted image preprocessing.
--hcp_fmri_volume           Runs HCP BOLD Volume preprocessing.
--hcp_fmri_surface          Runs HCP BOLD Surface preprocessing.
--hcp_icafix                Runs HCP ICAFix.
--hcp_post_fix              Runs HCP PostFix.
--hcp_reapply_fix           Runs HCP ReApplyFix.
--hcp_msmall                Runs HCP MSMAll.
--hcp_dedrift_and_resample  Runs HCP DeDriftAndResample.
--hcp_dtifit                Runs DTI Fit.
--hcp_bedpostx              Runs Bedpost X.
--hcp_task_fmri_analysis    Runs HCP TaskfMRIanalysis.
--map_hcp_data              Maps results of HCP preprocessing into `images` folder.

All the functions are part of the processing suite. They should be called
from the command line using `qunex` command. Help is available through:

- ``qunex ?<command>`` for command specific help
- ``qunex -o`` for a list of relevant arguments and options

There are additional support functions that are not to be used
directly.

Code split from dofcMRIp_core gCodeP/preprocess codebase.
"""

"""
Copyright (c) Grega Repovs and Jure Demsar.
All rights reserved.
"""

import os
import re
import os.path
import shutil
import glob
import sys
import traceback
import time
import general.core as gc
import processing.core as pc
import general.img as gi
import general.exceptions as ge
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from functools import partial


# ---- some definitions
unwarp = {None: "Unknown", 'i': 'x', 'j': 'y', 'k': 'z', 'i-': 'x-', 'j-': 'y-', 'k-': 'z-'}
PEDir  = {None: "Unknown", "LR": 1, "RL": 1, "AP": 2, "PA": 2}
PEDirMap  = {'AP': 'j-', 'j-': 'AP', 'PA': 'j', 'j': 'PA', 'RL': 'i', 'i': 'RL', 'LR': 'i-', 'i-': 'LR'}
SEDirMap  = {'AP': 'y', 'PA': 'y', 'LR': 'x', 'RL': 'x'}

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

    # ---- Key folder in the hcp folder structure

    hcpbase                 = os.path.join(sinfo['hcp'], sinfo['id'] + options['hcp_suffix'])

    d['base']               = hcpbase
    if options['hcp_folderstructure'] == 'initial':
        d['source'] = d['base']
    else:
        d['source'] = os.path.join(d['base'], 'unprocessed')

    d['hcp_nonlin']         = os.path.join(hcpbase, 'MNINonLinear')
    d['T1w_source']         = os.path.join(d['source'], 'T1w')
    d['DWI_source']         = os.path.join(d['source'], 'Diffusion')

    d['T1w_folder']         = os.path.join(hcpbase, 'T1w')
    d['DWI_folder']         = os.path.join(hcpbase, 'Diffusion')
    d['FS_folder']          = os.path.join(hcpbase, 'T1w', sinfo['id'] + options['hcp_suffix'])

    # T1w file
    try:
        T1w = [v for (k, v) in sinfo.iteritems() if k.isdigit() and v['name'] == 'T1w'][0]
        filename = T1w.get('filename', None)
        if filename and options['hcp_filename'] == "original":
            d['T1w'] = "@".join(glob.glob(os.path.join(d['source'], 'T1w', sinfo['id'] + '*' + filename + '*.nii.gz')))
        else:
            d['T1w'] = "@".join(glob.glob(os.path.join(d['source'], 'T1w', sinfo['id'] + '*T1w_MPR*.nii.gz')))
    except:
        d['T1w'] = 'NONE'

    # --- longitudinal FS related paths

    if options['hcp_fs_longitudinal']:
        d['FS_long_template'] = os.path.join(hcpbase, 'T1w', options['hcp_fs_longitudinal'])
        d['FS_long_results']  = os.path.join(hcpbase, 'T1w', "%s.long.%s" % (sinfo['id'] + options['hcp_suffix'], options['hcp_fs_longitudinal']))
        d['FS_long_subject_template'] = os.path.join(options['sessionsfolder'], 'FSTemplates', sinfo['subject'], options['hcp_fs_longitudinal'])
        d['hcp_long_nonlin']          = os.path.join(hcpbase, 'MNINonLinear_' + options['hcp_fs_longitudinal'])
    else:
        d['FS_long_template']         = ""
        d['FS_long_results']          = ""
        d['FS_long_subject_template'] = ""
        d['hcp_long_nonlin']          = ""


    # --- T2w related paths

    if options['hcp_t2'] == 'NONE':
        d['T2w'] = 'NONE'
    else:
        try:
            T2w = [v for (k, v) in sinfo.iteritems() if k.isdigit() and v['name'] == 'T2w'][0]
            filename = T2w.get('filename', None)
            if filename and options['hcp_filename'] == "original":
                d['T2w'] = "@".join(glob.glob(os.path.join(d['source'], 'T2w', sinfo['id'] + '*' + filename + '*.nii.gz')))
            else:
                d['T2w'] = "@".join(glob.glob(os.path.join(d['source'], 'T2w', sinfo['id'] + '_T2w_SPC*.nii.gz')))
        except:
            d['T2w'] = 'NONE'

    # --- Fieldmap related paths
    d['fieldmap'] = {}
    if options['hcp_avgrdcmethod'] in ['SiemensFieldMap', 'PhilipsFieldMap'] or options['hcp_bold_dcmethod'] in ['SiemensFieldMap', 'PhilipsFieldMap']:
        fmapmag = glob.glob(os.path.join(d['source'], 'FieldMap*' + options['fmtail'], sinfo['id'] + options['fmtail'] + '*_FieldMap_Magnitude.nii.gz'))
        for imagepath in fmapmag:
            fmnum = re.search(r'(?<=FieldMap)[0-9]{1,2}',imagepath)
            if fmnum:
                fmnum = int(fmnum.group())
                d['fieldmap'].update({fmnum: {'magnitude': imagepath}})

        fmapphase = glob.glob(os.path.join(d['source'], 'FieldMap*' + options['fmtail'], sinfo['id'] + options['fmtail'] + '*_FieldMap_Phase.nii.gz'))
        for imagepath in fmapphase:
            fmnum = re.search(r'(?<=FieldMap)[0-9]{1,2}',imagepath)
            if fmnum:
                fmnum = int(fmnum.group())
                if fmnum in d['fieldmap']:
                    d['fieldmap'][fmnum].update({'phase': imagepath})
    elif options['hcp_avgrdcmethod'] == 'GeneralElectricFieldMap' or options['hcp_bold_dcmethod'] == 'GeneralElectricFieldMap':
        fmapge = glob.glob(os.path.join(d['source'], 'FieldMap*' + options['fmtail'], sinfo['id'] + options['fmtail'] + '*_FieldMap_GE.nii.gz'))
        for imagepath in fmapge:
            fmnum = re.search(r'(?<=FieldMap)[0-9]{1,2}',imagepath)
            if fmnum:
                fmnum = int(fmnum.group())
                d['fieldmap'].update({fmnum: {'GE': imagepath}})

    # --- default check files

    for pipe, default in [('hcp_prefs_check',     'check_PreFreeSurfer.txt'),
                          ('hcp_fs_check',        'check_FreeSurfer.txt'),
                          ('hcp_fslong_check',    'check_FreeSurferLongitudinal.txt'),
                          ('hcp_postfs_check',    'check_PostFreeSurfer.txt'),
                          ('hcp_bold_vol_check',  'check_fMRIVolume.txt'),
                          ('hcp_bold_surf_check', 'check_fMRISurface.txt'),
                          ('hcp_dwi_check',       'check_Diffusion.txt')]:
        if options[pipe] == 'all':
            d[pipe] = os.path.join(options['sessionsfolder'], 'specs', default)
        elif options[pipe] == 'last':
            d[pipe] = False
        else:
            d[pipe] = options[pipe]

    return d


def doHCPOptionsCheck(options, sinfo, command):
    if options['hcp_folderstructure'] not in ['initial', 'hcpls']:
        raise ge.CommandFailed(command, "Unknown HCP folder structure version", "The specified HCP folder structure version is unknown: %s" % (options['hcp_folderstructure']), "Please check the 'hcp_folderstructure' parameter!")

    if options['hcp_folderstructure'] == 'initial':
        options['fctail'] = '_fncb'
        options['fmtail'] = '_strc'
    else:
        options['fctail'] = ""
        options['fmtail'] = ""


def checkInlineParameterUse(modality, parameter, options):
    return any([e in options['use_sequence_info'] for e in ['all', parameter, '%s:all' % (modality), '%s:%s' % (modality, parameter)]])


def checkGDCoeffFile(gdcstring, hcp, sinfo, r="", run=True):
    """
    Function that extract the information on the correct gdc file to be used and tests for its presence;
    """

    if gdcstring not in ['', 'NONE']:

        if any([e in gdcstring for e in ['|', 'default']]):
            try:
                try:
                    device = {}
                    dmanufacturer, dmodel, dserial = [e.strip() for e in sinfo.get('device', 'NA|NA|NA').split('|')]
                    device['manufacturer'] = dmanufacturer
                    device['model'] = dmodel
                    device['serial'] = dserial
                except:
                    r += "\n---> WARNING: device information for this session is malformed: %s" % (sinfo.get('device', '---'))
                    raise

                gdcoptions = [[ee.strip() for ee in e.strip().split(':')] for e in gdcstring.split('|')]
                gdcfile = [e[1] for e in gdcoptions if e[0] == 'default'][0]
                gdcfileused = 'default'

                for ginfo, gwhat, gfile in [e for e in gdcoptions if e[0] != 'default']:
                    if ginfo in device:
                        if device[ginfo] == gwhat:
                            gdcfile = gfile
                            gdcfileused = '%s: %s' % (ginfo, gwhat)
                            break
                    if ginfo in sinfo:
                        if sinfo[ginfo] == gwhat:
                            gdcfile = gfile
                            gdcfileused = '%s: %s' % (ginfo, gwhat)
                            break
            except:
                r += "\n---> ERROR: malformed specification of gdcoeffs: %s!" % (gdcstring)
                run = False
                raise

            if gdcfile in ['', 'NONE']:
                r += "\n---> WARNING: Specific gradient distortion coefficients file could not be identified! None will be used."
                gdcfile = "NONE"
            else:
                r += "\n---> Specific gradient distortion coefficients file identified (%s):\n     %s" % (gdcfileused, gdcfile)

        else:
            gdcfile = gdcstring

        if gdcfile not in ['', 'NONE']:
            if not os.path.exists(gdcfile):
                gdcoeffs = os.path.join(hcp['hcp_Config'], gdcfile)
                if not os.path.exists(gdcoeffs):
                    r += "\n---> ERROR: Could not find gradient distortion coefficients file: %s." % (gdcfile)
                    run = False
                else:
                    r += "\n---> Gradient distortion coefficients file present."
            else:
                r += "\n---> Gradient distortion coefficients file present."
    else:
        gdcfile = "NONE"

    return gdcfile, r, run




def hcp_pre_freesurfer(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_pre_freesurfer [... processing options]``

    Runs the pre-FS step of the HCP Pipeline.

    REQUIREMENTS
    ============

    The code expects the input images to be named and present in the specific
    folder structure. Specifically it will look within the folder::

        <session id>/hcp/<session id>

    for folders and files::

        T1w/*T1w_MPR[N]*
        T2w/*T2w_MPR[N]*

    There has to be at least one T1w image present. If there are more than one
    T1w or T2w images, they will all be used and averaged together.

    Depending on the type of distortion correction method specified by the
    `--hcp_avgrdcmethod` argument (see below), it will also expect the presence
    of the following files:

    __TOPUP__::

        SpinEchoFieldMap[N]*/*_<hcp_sephasepos>_*
        SpinEchoFieldMap[N]*/*_<hcp_sephaseneg>_*

    __SiemensFieldMap__::

        FieldMap/<session id>_FieldMap_Magnitude.nii.gz
        FieldMap/<session id>_FieldMap_Phase.nii.gz

    __GeneralElectricFieldMap__::

        FieldMap/<session id>_FieldMap_GE.nii.gz

    __PhilipsFieldMap__::

        FieldMap/<session id>_FieldMap_Magnitude.nii.gz
        FieldMap/<session id>_FieldMap_Phase.nii.gz

    INPUTS
    ======

    General parameters
    ------------------

    When running the command, the following *general* processing parameters are
    taken into account:

    --sessions                  The batch.txt file with all the sessions
                                information. [batch.txt]
    --sessionsfolder            The path to the study/sessions folder, where the
                                imaging  data is supposed to go. [.]
    --parsessions               How many sessions to run in parallel. [1]
    --overwrite                 Whether to overwrite existing data (yes) or not
                                (no). [no]
    --hcp_suffix                Specifies a suffix to the session id if multiple
                                variants are run, empty otherwise. []
    --logfolder                 The path to the folder where runlogs and comlogs
                                are to be stored, if other than default. []
    --log                       Whether to keep ('keep') or remove ('remove')
                                the temporary logs once jobs are completed
                                ['keep']. When a comma or pipe ('|') separated
                                list is given, the log will be created at the
                                first provided location and then linked or
                                copied to other locations. The valid locations
                                are:
                                - 'study' (for the default:
                                  `<study>/processing/logs/comlogs` location)
                                - 'session' (for `<sessionid>/logs/comlogs`)
                                - 'hcp' (for `<hcp_folder>/logs/comlogs`)
                                - '<path>' (for an arbitrary directory)

    --hcp_processing_mode       Controls whether the HCP acquisition and
                                processing guidelines should be treated as
                                requirements (HCPStyleData) or if additional
                                processing functionality is allowed
                                (LegacyStyleData). In this case running
                                processing w/o a T2w image.
    --hcp_folderstructure       Specifies the version of the folder structure to
                                use, 'initial' and 'hcpls' are supported.
                                ['hcpls']
    --hcp_filename              Specifies whether the standard ('standard')
                                filenames or the specified original names
                                ('original') are to be used. ['standard']

    Specific parameters
    -------------------

    In addition the following *specific* parameters will be used to guide the
    processing in this step:

    --hcp_t2                    NONE if no T2w image is available and the
                                preprocessing should be run without them,
                                anything else otherwise. NONE is only valid if
                                'LegacyStyleData' processing mode was
                                specified. [t2]
    --hcp_brainsize             Specifies the size of the brain in mm. 170 is
                                FSL default and seems to be a good choice, HCP
                                uses 150, which can lead to problems with
                                larger heads. [150]
    --hcp_t1samplespacing       T1 image sample spacing, NONE if not used.
                                [NONE]
    --hcp_t2samplespacing       T2 image sample spacing, NONE if not used.
                                [NONE]
    --hcp_gdcoeffs              Path to a file containing gradient distortion
                                coefficients, alternatively a string describing
                                multiple options (see below), or "NONE", if not
                                used. [NONE]
    --hcp_bfsigma               Bias Field Smoothing Sigma (optional). []
    --hcp_avgrdcmethod          Averaging and readout distortion correction
                                method. [NONE]
                                Can take the following values:
                                - NONE (average any repeats with no readout
                                  correction)
                                - FIELDMAP (average any repeats and use
                                  Siemens field map for readout correction)
                                - SiemensFieldMap (average any repeats and use
                                  Siemens field map for readout correction)
                                - GeneralElectricFieldMap (average any repeats
                                  and use GE field map for readout correction)
                                - PhilipsFieldMap (average any repeats and use
                                  Philips field map for readout correction)
                                - TOPUP (average any repeats and use spin echo
                                  field map for readout correction)
    --hcp_unwarpdir             Readout direction of the T1w and T2w images
                                (x, y, z or NONE); used with either a regular
                                field map or a spin echo field map. [NONE]
    --hcp_echodiff              Difference in TE times if a fieldmap image is
                                used, set to NONE if not used. [NONE]
    --hcp_seechospacing         Echo Spacing or Dwelltime of Spin Echo Field
                                Map or "NONE" if not used. [NONE]
    --hcp_sephasepos            Label for the positive image of the Spin Echo
                                Field Map pair. [""]
    --hcp_sephaseneg            Label for the negative image of the Spin Echo
                                Field Map pair. [""]
    --hcp_seunwarpdir           Phase encoding direction of the Spin Echo
                                Field Map (x, y or NONE). [NONE]
    --hcp_topupconfig           Path to a configuration file for TOPUP method
                                or "NONE" if not used. [NONE]
    --hcp_prefs_custombrain     Whether to only run the final registration
                                using either a custom prepared brain mask
                                (MASK) or custom prepared brain images
                                (CUSTOM), or to run the full set of processing
                                steps (NONE). [NONE] If a mask is to be used
                                (MASK) then a
                                `"custom_acpc_dc_restore_mask.nii.gz"` image
                                needs to be placed in the `<session>/T1w`
                                folder. If a custom brain is to be used
                                (BRAIN), then the following images in
                                `<session>/T1w` folder need to be adjusted:

                                - `T1w_acpc_dc_restore_brain.nii.gz`
                                - `T1w_acpc_dc_restore.nii.gz`
                                - `T2w_acpc_dc_restore_brain.nii.gz`
                                - `T2w_acpc_dc_restore.nii.gz`
    --hcp_prefs_template_res    The resolution (in mm) of the structural
                                images templates to use in the preFS step.
                                Note: it should match the resolution of the
                                acquired structural images.
    --use_sequence_info         A pipe, comma or space separated list of inline
                                sequence information to use in preprocessing of
                                specific image modalities.

                                Example specifications:

                                - `all`: use all present inline information for
                                  all modalities,
                                - 'DwellTime': use DwellTime information for all
                                  modalities,
                                - `T1w:all': use all present inline information
                                  for T1w modality,
                                - `SE:EchoSpacing': use EchoSpacing information
                                  for Spin-Echo fieldmap images.
                                - 'none': do not use inline information

                                Modalities: T1w, T2w, SE, BOLD, dMRi
                                Inline information: TR, PEDirection, EchoSpacing
                                  DwellTime, ReadoutDirection

                                If information is not specified it will not be
                                used. More general specification (e.g. `all`)
                                implies all more specific cases (e.g. `T1w:all`).
                                ['all']

    Gradient coefficient file specification:
    ----------------------------------------

    `--hcp_gdcoeffs` parameter can be set to either 'NONE', a path to a specific
    file to use, or a string that describes, which file to use in which case.
    Each option of the string has to be divided by a pipe '|' character and it
    has to specify, which information to look up, a possible value, and a file
    to use in that case, separated by a colon ':' character. The information
    too look up needs to be present in the description of that session.
    Standard options are e.g.::

        institution: Yale
        device: Siemens|Prisma|123456

    Where device is formatted as <manufacturer>|<model>|<serial number>.

    If specifying a string it also has to include a `default` option, which
    will be used in the information was not found. An example could be::

        "default:/data/gc1.conf|model:Prisma:/data/gc/Prisma.conf|model:Trio:/data/gc/Trio.conf"

    With the information present above, the file `/data/gc/Prisma.conf` would
    be used.

    OUTPUTS
    =======

    The results of this step will be present in the above mentioned T1w and T2w
    folders as well as MNINonLinear folder generated and populated in the same
    sessions's root hcp folder.

    USE
    ===

    Runs the PreFreeSurfer step of the HCP Pipeline. It looks for T1w and T2w images in
    sessions's T1w and T2w folder, averages them (if multiple present) and
    linearly and nonlinearly aligns them to the MNI atlas. It uses the adjusted
    version of the HCP that enables the preprocessing to run with of without T2w
    image(s).

    EXAMPLE USE
    ===========

    ::

        qunex hcp_pre_freesurfer sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
            overwrite=no parsessions=10 hcp_brainsize=170

    ::

        qunex hcp_pre_freesurfer sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
            overwrite=no parsessions=10 hcp_t2=NONE
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP PreFreeSurfer Pipeline [%s] ...\n" % (pc.action("Running", options['run']), options['hcp_processing_mode'])

    run    = True
    report = "Error"

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, 'hcp_pre_freesurfer')
        doHCPOptionsCheck(options, sinfo, 'hcp_pre_freesurfer')
        hcp = getHCPPaths(sinfo, options)

        # --- run checks

        if 'hcp' not in sinfo:
            r += "\n---> ERROR: There is no hcp info for session %s in batch.txt" % (sinfo['id'])
            run = False

        # --- check for T1w and T2w images
        for tfile in hcp['T1w'].split("@"):
            if os.path.exists(tfile):
                r += "\n---> T1w image file present."
                T1w = [v for (k, v) in sinfo.iteritems() if k.isdigit() and v['name'] == 'T1w'][0]
                if 'DwellTime' in T1w and checkInlineParameterUse('T1w', 'DwellTime', options):
                    options['hcp_t1samplespacing'] = T1w['DwellTime']
                    r += "\n---> T1w image specific EchoSpacing: %s s" % (options['hcp_t1samplespacing'])
                elif 'EchoSpacing' in T1w  and checkInlineParameterUse('T1w', 'EchoSpacing', options):
                    options['hcp_t1samplespacing'] = T1w['EchoSpacing']
                    r += "\n---> T1w image specific EchoSpacing: %s s" % (options['hcp_t1samplespacing'])
                if 'UnwarpDir' in T1w and checkInlineParameterUse('T1w', 'UnwarpDir', options):
                    options['hcp_unwarpdir'] = T1w['UnwarpDir']
                    r += "\n---> T1w image specific unwarp direction: %s" % (options['hcp_unwarpdir'])
            else:
                r += "\n---> ERROR: Could not find T1w image file. [%s]" % (tfile)
                run = False

        if hcp['T2w'] in ['', 'NONE']:
            if options['hcp_processing_mode'] == 'HCPStyleData':
                r += "\n---> ERROR: The requested HCP processing mode is 'HCPStyleData', however, no T2w image was specified!\n            Consider using LegacyStyleData processing mode."
                run = False
            else:
                r += "\n---> Not using T2w image."
        else:
            for tfile in hcp['T2w'].split("@"):
                if os.path.exists(tfile):
                    r += "\n---> T2w image file present."
                    T2w = [v for (k, v) in sinfo.iteritems() if k.isdigit() and v['name'] == 'T2w'][0]
                    if 'DwellTime' in T2w and checkInlineParameterUse('T2w', 'DwellTime', options):
                        options['hcp_t2samplespacing'] = T2w['DwellTime']
                        r += "\n---> T2w image specific EchoSpacing: %s s" % (options['hcp_t2samplespacing'])
                    elif 'EchoSpacing' in T2w and checkInlineParameterUse('T2w', 'EchoSpacing', options):
                        options['hcp_t2samplespacing'] = T2w['EchoSpacing']
                        r += "\n---> T2w image specific EchoSpacing: %s s" % (options['hcp_t2samplespacing'])
                else:
                    r += "\n---> ERROR: Could not find T2w image file. [%s]" % (tfile)
                    run = False

        # --- do we need spinecho images

        sepos       = ''
        seneg       = ''
        topupconfig = ''
        senum       = None
        tufolder    = None
        fmmag = ''
        fmphase = ''
        fmge = ''

        if options['hcp_avgrdcmethod'].lower() == 'topup':
            # -- spin echo settings
            sesettings = True
            for p in ['hcp_sephaseneg', 'hcp_sephasepos', 'hcp_seunwarpdir']:
                if not options[p]:
                    r += '\n---> ERROR: %s parameter is not set! Please review parameter file!' % (p)
                    run = False
                    sesettings = False

            try:
                T1w = [v for (k, v) in sinfo.iteritems() if k.isdigit() and v['name'] == 'T1w'][0]
                senum = T1w.get('se', None)
                if senum:
                    try:
                        senum = int(senum)
                        if senum > 0:
                            tufolder = os.path.join(hcp['source'], 'SpinEchoFieldMap%d%s' % (senum, options['fctail']))
                            r += "\n---> TOPUP Correction, Spin-Echo pair %d specified" % (senum)
                        else:
                            r += "\n---> ERROR: No Spin-Echo image pair specified for T1w image! [%d]" % (senum)
                            run = False
                    except:
                        r += "\n---> ERROR: Could not process the specified Spin-Echo information [%s]! " % (str(senum))
                        run = False

            except:
                pass

            if senum is None:
                try:
                    tufolder = glob.glob(os.path.join(hcp['source'], 'SpinEchoFieldMap*'))[0]
                    senum = int(os.path.basename(tufolder).replace('SpinEchoFieldMap', '').replace('_fncb', ''))
                    r += "\n---> TOPUP Correction, no Spin-Echo pair explicitly specified, using pair %d" % (senum)
                except:
                    r += "\n---> ERROR: Could not find folder with files for TOPUP processing of session %s." % (sinfo['id'])
                    run = False
                    raise

            if tufolder and sesettings:
                try:
                    sepos = glob.glob(os.path.join(tufolder, "*_" + options['hcp_sephasepos'] + "*"))[0]
                    seneg = glob.glob(os.path.join(tufolder, "*_" + options['hcp_sephaseneg'] + "*"))[0]

                    if all([sepos, seneg]):
                        r += "\n---> Spin-Echo pair of images present. [%s]" % (os.path.basename(tufolder))
                    else:
                        r += "\n---> ERROR: Could not find the relevant Spin-Echo files! [%s]" % (tufolder)
                        run = False


                    # get SE info from session info
                    try:
                        seInfo = [v for (k, v) in sinfo.iteritems() if k.isdigit() and 'SE-FM' in v['name'] and 'se' in v and v['se'] == str(senum)][0]
                    except:
                        seInfo = None

                    if seInfo and 'EchoSpacing' in seInfo and checkInlineParameterUse('SE', 'EchoSpacing', options):
                        options['hcp_seechospacing'] = seInfo['EchoSpacing']
                        r += "\n---> Spin-Echo images specific EchoSpacing: %s s" % (options['hcp_seechospacing'])
                    if seInfo and 'phenc' in seInfo:
                        options['hcp_seunwarpdir'] = SEDirMap[seInfo['phenc']]
                        r += "\n---> Spin-Echo unwarp direction: %s" % (options['hcp_seunwarpdir'])
                    elif seInfo and 'PEDirection' in seInfo and checkInlineParameterUse('SE', 'PEDirection', options):
                        options['hcp_seunwarpdir'] = seInfo['PEDirection']
                        r += "\n---> Spin-Echo unwarp direction: %s" % (options['hcp_seunwarpdir'])

                    if options['hcp_topupconfig'] != 'NONE' and options['hcp_topupconfig']:
                        topupconfig = options['hcp_topupconfig']
                        if not os.path.exists(options['hcp_topupconfig']):
                            topupconfig = os.path.join(hcp['hcp_Config'], options['hcp_topupconfig'])
                            if not os.path.exists(topupconfig):
                                r += "\n---> ERROR: Could not find TOPUP configuration file: %s." % (topupconfig)
                                run = False
                            else:
                                r += "\n---> TOPUP configuration file present."
                        else:
                            r += "\n---> TOPUP configuration file present."
                except:
                    r += "\n---> ERROR: Could not find files for TOPUP processing of session %s." % (sinfo['id'])
                    run = False
                    raise

        elif options['hcp_avgrdcmethod'] == 'GeneralElectricFieldMap':
            fmnum = T1w.get('fm', None)
            ## include => if fmnum is None, same as for senum

            for i, v in hcp['fieldmap'].iteritems():
                if os.path.exists(hcp['fieldmap'][i]['GE']):
                    r += "\n---> Gradient Echo Field Map %d file present." % (i)
                else:
                    r += "\n---> ERROR: Could not find Gradient Echo Field Map %d file for session %s.\n            Expected location: %s" % (i, sinfo['id'], hcp['fmapge'])
                    run = False

            fmmag = None
            fmphase = None
            fmge = hcp['fieldmap'][int(fmnum)]['GE']

        elif options['hcp_avgrdcmethod'] in ['FIELDMAP', 'SiemensFieldMap', 'PhilipsFieldMap']:
            fmnum = T1w.get('fm', None)

            for i, v in hcp['fieldmap'].iteritems():
                if os.path.exists(hcp['fieldmap'][i]['magnitude']):
                    r += "\n---> Magnitude Field Map %d file present." % (i)
                else:
                    r += "\n---> ERROR: Could not find Magnitude Field Map %d file for session %s.\n            Expected location: %s" % (i, sinfo['id'], hcp['fmapmag'])
                    run = False
                if os.path.exists(hcp['fieldmap'][i]['phase']):
                    r += "\n---> Phase Field Map %d file present." % (i)
                else:
                    r += "\n---> ERROR: Could not find Phase Field Map %d file for session %s.\n            Expected location: %s" % (i, sinfo['id'], hcp['fmapphase'])
                    run = False

            fmmag = hcp['fieldmap'][int(fmnum)]['magnitude']
            fmphase = hcp['fieldmap'][int(fmnum)]['phase']
            fmge = None

        else:
            r += "\n---> WARNING: No distortion correction method specified."

        # --- lookup gdcoeffs file if needed

        gdcfile, r, run = checkGDCoeffFile(options['hcp_gdcoeffs'], hcp=hcp, sinfo=sinfo, r=r, run=run)

        # --- see if we have set up to use custom mask

        if options['hcp_prefs_custombrain'] == 'MASK':
            tfile = os.path.join(hcp['T1w_folder'], 'T1w_acpc_dc_restore_brain.nii.gz')
            mfile = os.path.join(hcp['T1w_folder'], 'custom_acpc_dc_restore_mask.nii.gz')
            r += "\n---> Set to run only final atlas registration with a custom mask."

            if os.path.exists(tfile):
                r += "\n     ... Previous results present."
                if os.path.exists(mfile):
                    r += "\n     ... Custom mask present."
                else:
                    r += "\n     ... ERROR: Custom mask missing! [%s]!." % (mfile)
                    run = False
            else:
                run = False
                r += "\n     ... ERROR: No previous results found! Please run PreFS without hcp_prefs_custombrain set to MASK first!"
                if os.path.exists(mfile):
                    r += "\n     ... Custom mask present."
                else:
                    r += "\n     ... ERROR: Custom mask missing as well! [%s]!." % (mfile)

        # --- check if we are using a custom brain

        if options['hcp_prefs_custombrain'] == 'CUSTOM':
            t1files = ['T1w_acpc_dc_restore_brain.nii.gz', 'T1w_acpc_dc_restore.nii.gz']
            t2files = ['T2w_acpc_dc_restore_brain.nii.gz', 'T2w_acpc_dc_restore.nii.gz']
            if hcp['T2w'] in ['', 'NONE']:
                tfiles = t1files
            else:
                tfiles = t1files + t2files

            r += "\n---> Set to run only final atlas registration with custom brain images."

            missingfiles = []
            for tfile in tfiles:
                if not os.path.exists(os.path.join(hcp['T1w_folder'], tfile)):
                    missingfiles.append(tfile)

            if missingfiles:
                run = False
                r += "\n     ... ERROR: The following brain files are missing in %s:" % (hcp['T1w_folder'])
                for tfile in missingfiles:
                    r += "\n                %s" % tfile


        # --- Set up the command

        comm = os.path.join(hcp['hcp_base'], 'PreFreeSurfer', 'PreFreeSurferPipeline.sh') + " "

        elements = [("path", sinfo['hcp']),
                    ('subject', sinfo['id'] + options['hcp_suffix']),
                    ('t1', hcp['T1w']),
                    ('t2', hcp['T2w']),
                    ('t1template', os.path.join(hcp['hcp_Templates'], 'MNI152_T1_%smm.nii.gz' % (options['hcp_prefs_template_res']))),
                    ('t1templatebrain', os.path.join(hcp['hcp_Templates'], 'MNI152_T1_%smm_brain.nii.gz' % (options['hcp_prefs_template_res']))),
                    ('t1template2mm', os.path.join(hcp['hcp_Templates'], 'MNI152_T1_2mm.nii.gz')),
                    ('t2template', os.path.join(hcp['hcp_Templates'], 'MNI152_T2_%smm.nii.gz' % (options['hcp_prefs_template_res']))),
                    ('t2templatebrain', os.path.join(hcp['hcp_Templates'], 'MNI152_T2_%smm_brain.nii.gz' % (options['hcp_prefs_template_res']))),
                    ('t2template2mm', os.path.join(hcp['hcp_Templates'], 'MNI152_T2_2mm.nii.gz')),
                    ('templatemask', os.path.join(hcp['hcp_Templates'], 'MNI152_T1_%smm_brain_mask.nii.gz' % (options['hcp_prefs_template_res']))),
                    ('template2mmmask', os.path.join(hcp['hcp_Templates'], 'MNI152_T1_2mm_brain_mask_dil.nii.gz')),
                    ('brainsize', options['hcp_brainsize']),
                    ('fnirtconfig', os.path.join(hcp['hcp_Config'], 'T1_2_MNI152_2mm.cnf')),
                    ('fmapmag', fmmag),
                    ('fmapphase',fmphase),
                    ('fmapgeneralelectric', fmge),
                    ('echodiff', options['hcp_echodiff']),
                    ('SEPhaseNeg', seneg),
                    ('SEPhasePos', sepos),
                    ('seechospacing', options['hcp_seechospacing']),
                    ('seunwarpdir', options['hcp_seunwarpdir']),
                    ('t1samplespacing', options['hcp_t1samplespacing']),
                    ('t2samplespacing', options['hcp_t2samplespacing']),
                    ('unwarpdir', options['hcp_unwarpdir']),
                    ('gdcoeffs', gdcfile),
                    ('avgrdcmethod', options['hcp_avgrdcmethod']),
                    ('topupconfig', topupconfig),
                    ('bfsigma', options['hcp_bfsigma']),
                    ('printcom', options['hcp_printcom']),
                    ('custombrain', options['hcp_prefs_custombrain']),
                    ('processing-mode', options['hcp_processing_mode'])]

        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])

        # -- Report command
        if run:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test files

        tfile = os.path.join(hcp['hcp_nonlin'], 'T1w_restore_brain.nii.gz')
        if hcp['hcp_prefs_check']:
            fullTest = {'tfolder': hcp['base'], 'tfile': hcp['hcp_prefs_check'], 'fields': [('sessionid', sinfo['id'] + options['hcp_suffix'])], 'specfolder': options['specfolder']}
        else:
            fullTest = None

        # -- Run

        if run:
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, endlog, report, failed = pc.runExternalForFile(tfile, comm, 'Running HCP PreFS', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=options['logtag'], fullTest=fullTest, shell=True, r=r)

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(tfile, fullTest, 'HCP PreFS', r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP PreFS can be run"
                    report = "HCP Pre FS can be run"
                    failed = 0
        else:
            r += "\n---> Due to missing files session can not be processed."
            report = "Files missing, PreFS can not be run"
            failed = 1

    except ge.CommandFailed as e:
        r +=  "\n\nERROR in completing %s at %s:\n     %s\n" % ('PreFreeSurfer', e.function, "\n     ".join(e.report))
        report = "PreFS failed"
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        report = "PreFS failed"
        failed = 1
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        report = "PreFS failed"
        failed = 1

    r += "\nHCP PreFS %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, (sinfo['id'], report, failed))


def hcp_freesurfer(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_freesurfer [... processing options]``

    Runs the FS step of the HCP Pipeline.

    REQUIREMENTS
    ============

    The code expects the previous step (hcp_pre_freesurfer) to have run successfully and
    checks for presence of a few key files and folders. Due to the number of
    inputs that it requires, it does not make a full check for all of them!

    INPUTS
    ======

    General parameters
    ------------------

    When running the command, the following *general* processing parameters are
    taken into account:

    --sessions                  The batch.txt file with all the sessions
                                information. [batch.txt]
    --sessionsfolder            The path to the study/sessions folder, where the
                                imaging  data is supposed to go. [.]
    --parsessions               How many sessions to run in parallel. [1]
    --overwrite                 Whether to overwrite existing data (yes) or not
                                (no). [no]
    --hcp_suffix                Specifies a suffix to the session id if multiple
                                variants are run, empty otherwise. []
    --logfolder                 The path to the folder where runlogs and comlogs
                                are to be stored, if other than default. []
    --log                       Whether to keep ('keep') or remove ('remove')
                                the temporary logs once jobs are completed
                                ['keep']. When a comma or pipe ('|') separated
                                list is given, the log will be created at the
                                first provided location and then linked or
                                copied to other locations. The valid locations
                                are:

                                - 'study' (for the default:
                                  `<study>/processing/logs/comlogs` location)
                                - 'session' (for `<sessionid>/logs/comlogs`)
                                - 'hcp' (for `<hcp_folder>/logs/comlogs`)
                                - '<path>' (for an arbitrary directory)

    --hcp_processing_mode       Controls whether the HCP acquisition and
                                processing guidelines should be treated as
                                requirements (HCPStyleData) or if additional
                                processing functionality is allowed
                                (LegacyStyleData). In this case running
                                processing w/o a T2w image.
    --hcp_folderstructure       Specifies the version of the folder structure to
                                use, 'initial' and 'hcpls' are supported.
                                ['hcpls']
    --hcp_filename              Specifies whether the standard ('standard')
                                filenames or the specified original names
                                ('original') are to be used. ['standard']


    Specific parameters
    -------------------

    These are optional parameters. Please note that they will only be used
    when HCP Pipelines are used. They are not implemented in hcpmodified!

    --hcp_fs_seed                  Recon-all seed value. If not specified, none
                                   will be used. []
    --hcp_fs_existing_session      Indicates that the command is to be run on
                                   top of an already existing analysis/subject.
                                   This excludes the `-i` flag from the
                                   invocation of recon-all. If set, the
                                   user needs to specify which recon-all stages
                                   to run using the --hcp_fs_extra_reconall
                                   parameter. Accepted values are TRUE and
                                   FALSE. [FALSE]
    --hcp_fs_extra_reconall        A string with extra parameters to pass to
                                   FreeSurfer recon-all. The extra parameters
                                   are to be listed in a pipe ('|') separated
                                   string. Parameters and their values need to
                                   be listed separately. E.g. to pass
                                   `-norm3diters 3` to reconall, the string has
                                   to be: "-norm3diters|3". []
    --hcp_fs_flair                 If set to TRUE indicates that recon-all is to
                                   be run with the -FLAIR/-FLAIRpial options
                                   (rather than the -T2/-T2pial options).
                                   The FLAIR input image itself should be
                                   provided as a regular T2w image.
    --hcp_fs_no_conf2hires         Indicates that (most commonly due to low
                                   resolution—1mm or less—of structural image(s),
                                   high-resolution steps of recon-all should be
                                   excluded. Accepted values are TRUE or FALSE
                                   [FALSE].


    HCP LegacyStyleData processing mode parameters:
    -----------------------------------------------

    Please note, that these settings will only be used when LegacyStyleData
    processing mode is specified!

    --hcp_t2                    NONE if no T2w image is available and the
                                preprocessing should be run without them,
                                anything else otherwise [t2]. NONE is only valid
                                if 'LegacyStyleData' processing mode was
                                specified.
    --hcp_expert_file           Path to the read-in expert options file for
                                FreeSurfer if one is prepared and should be used
                                empty otherwise. []
    --hcp_control_points        Specify YES to use manual control points or
                                empty otherwise. [] (currently not available)
    --hcp_wm_edits              Specify YES to use manually edited WM mask or
                                empty otherwise. [] (currently not available)
    --hcp_fs_brainmask          Specify 'original' to keep the masked original
                                brain image; 'manual' to use the manually edited
                                brainmask file; default 'fs' uses the brainmask
                                generated by mri_watershed. [fs] (currently not
                                available)
    --hcp_autotopofix_off       Specify YES to turn off the automatic topologic
                                fix step in FS and compute WM surface
                                deterministically from manual WM mask, or empty
                                otherwise. [] (currently not available)
    --hcp_freesurfer_home       Path for FreeSurfer home folder can be manually
                                specified to override default environment
                                variable to ensure backwards compatiblity and
                                hcp_freesurfer customization.

    OUTPUTS
    =======

    The results of this step will be present in the above mentioned T1w folder
    as well as MNINonLinear folder in the sessions's root hcp folder.

    USE
    ===

    Runs the FreeSurfer step of the HCP Pipeline. It takes the T1w and T2w images
    processed in the previous (hcp_pre_freesurfer) step, segments T1w image by brain
    matter and CSF, reconstructs the cortical surface of the brain and assigns
    structure labels for both subcortical and cortical structures. It completes
    the listed in multiple steps of increased precision and (if present) uses
    T2w image to refine the surface reconstruction. It uses the adjusted
    version of the HCP code that enables the preprocessing to run also if no T2w
    image is present. 

    EXAMPLE USE
    ===========

    ::

        qunex hcp_freesurfer sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no parsessions=10

    ::

        qunex hcp_freesurfer sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no parsessions=10 hcp_fs_longitudinal=TemplateA

    ::

        qunex hcp_freesurfer sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no parsessions=10 hcp_t2=NONE

    ::

        qunex hcp_freesurfer sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no parsessions=10 hcp_t2=NONE \\
              hcp_freesurfer_home=<absolute_path_to_freesurfer_binary> \\
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n\n%s HCP FreeSurfer Pipeline [%s] ...\n" % (pc.action("Running", options['run']), options['hcp_processing_mode'])

    run    = True
    status = True
    report = "Error"

    try:
        pc.doOptionsCheck(options, sinfo, 'hcp_freesurfer')
        doHCPOptionsCheck(options, sinfo, 'hcp_freesurfer')
        hcp = getHCPPaths(sinfo, options)

        # --- run checks

        if 'hcp' not in sinfo:
            r += "\n---> ERROR: There is no hcp info for session %s in batch.txt" % (sinfo['id'])
            run = False

        # -> Pre FS results

        if os.path.exists(os.path.join(hcp['T1w_folder'], 'T1w_acpc_dc_restore_brain.nii.gz')):
            r += "\n---> PreFS results present."
        else:
            r += "\n---> ERROR: Could not find PreFS processing results."
            run = False

        # -> T2w image

        if hcp['T2w'] in ['', 'NONE']:
            t2w = 'NONE'
        else:
            t2w = os.path.join(hcp['T1w_folder'], 'T2w_acpc_dc_restore.nii.gz')

        if t2w == 'NONE' and options['hcp_processing_mode'] == 'HCPStyleData':
            r += "\n---> ERROR: The requested HCP processing mode is 'HCPStyleData', however, not T2w image was specified!\n            Consider using LegacyStyleData processing mode."
            run = False

        # -> check version of FS against previous version of FS

        # ------------------------------------------------------------------
        # - Alan added integrated code for FreeSurfer 6.0 completion check
        # -----------------------------------------------------------------

        freesurferhome = options['hcp_freesurfer_home']

        # - Set FREESURFER_HOME based on --hcp_freesurfer_home flag to ensure backward compatibility
        if freesurferhome:
            sys.path.append(freesurferhome)
            os.environ['FREESURFER_HOME'] = str(freesurferhome)
            r +=  "\n---> FREESURFER_HOME set to: " + str(freesurferhome)
            versionfile = os.path.join(os.environ['FREESURFER_HOME'], 'build-stamp.txt')
        else:
            fshome = os.environ["FREESURFER_HOME"]
            r += "\n---> FREESURFER_HOME set to: " + str(fshome)
            versionfile = os.path.join(os.environ['FREESURFER_HOME'], 'build-stamp.txt')

        fsbuildstamp = open(versionfile).read()

        for fstest, fsversion in [('stable-pub-v6.0.0', '6.0'), ('stable-pub-v5.3.0-HCP', '5.3-HCP'), ('unknown', 'unknown')]:
            if fstest in fsbuildstamp:
                break

        # - Check if recon-all.log exists to set the FS version
        reconallfile = os.path.join(hcp['T1w_folder'], sinfo['id'] + options['hcp_suffix'], 'scripts', 'recon-all.log')

        if os.path.exists(reconallfile):
            r +=  "\n---> Existing FreeSurfer recon-all.log was found!"

            reconallfiletxt = open(reconallfile).read()
            for fstest, efsversion in [('stable-pub-v6.0.0', '6.0'), ('stable-pub-v5.3.0-HCP', '5.3-HCP'), ('unknown', 'unknown')]:
                if fstest in reconallfiletxt:
                    break

            if overwrite and options['run'] == "run" and not options['hcp_fs_existing_session']:
                r += "\n     ... removing previous files"
            else:
                if fsversion == efsversion:
                    r += "\n     ... current FREESURFER_HOME settings match previous version of recon-all.log [%s]." % (fsversion)
                    r += "\n         Proceeding ..."
                else:
                    r += "\n     ... ERROR: current FREESURFER_HOME settings [%s] do not match previous version of recon-all.log [%s]!" % (fsversion, efsversion)
                    r += "\n         Please check your FS version or set overwrite to yes"
                    run = False

        # --- set target file

        # --- Deprecated versions of tfile variable based on prior FS runs ---------------------------------------------
        # tfile = os.path.join(hcp['T1w_folder'], sinfo['id'] + options['hcp_suffix'], 'mri', 'aparc+aseg.mgz')
        # tfile = os.path.join(hcp['T1w_folder'], '_FS.done')
        # tfile = os.path.join(hcp['T1w_folder'], sinfo['id'] + options['hcp_suffix'], 'label', 'BA_exvivo.thresh.ctab')
        # --------------------------------------------------------------------------------------------------------------

        tfiles = {'6.0':     os.path.join(hcp['FS_folder'], 'label', 'BA_exvivo.thresh.ctab'),
                  '5.3-HCP': os.path.join(hcp['FS_folder'], 'label', 'rh.entorhinal_exvivo.label')}
        tfile = tfiles[fsversion]


        # --> longitudinal run currently not supported
        #
        # identify template if longitudinal run
        #
        # fslongitudinal = ""
        #
        # if options['hcp_fs_longitudinal']:
        #     if 'subject' not in sinfo:
        #         r += "\n     ... 'subject' field not defined in batch file, can not run longitudinal FS"
        #         run = False
        #     elif sinfo['subject'] == sinfo['id']:
        #         r += "\n     ... 'subject' field is equal to session 'id' field, can not run longitudinal FS"
        #         run = False
        #     else:
        #         lresults = os.path.join(hcp['FS_long_template'], 'label', 'rh.entorhinal_exvivo.label')
        #         if not os.path.exists(lresults):
        #             r += "\n     ... ERROR: Longitudinal template not present! [%s]" % (lresults)
        #             r += "\n                Please chesk the results of longitudinal_freesurfer command!"
        #             r += "\n                Please check your data and settings!" % (lresults)
        #             run = False
        #         else:
        #             r += "\n     ... longitudinal template present"
        #             fslongitudinal = "run"
        #             tfiles = {'6.0':     os.path.join(hcp['FS_long_results'], 'label', 'BA_exvivo.thresh.ctab'),
        #                       '5.3-HCP': os.path.join(hcp['FS_long_results'], 'label', 'rh.entorhinal_exvivo.label')}
        #             tfile = tfiles[fsversion]

        # --> Building the command string

        comm = os.path.join(hcp['hcp_base'], 'FreeSurfer', 'FreeSurferPipeline.sh') + " "

        # -> Key elements

        elements = [("subjectDIR",       hcp['T1w_folder']),
                    ('subject',          sinfo['id'] + options['hcp_suffix']),
                    ('seed',             options['hcp_fs_seed']),
                    ('no-conf2hires',    options['hcp_fs_no_conf2hires']),
                    ('processing-mode',  options['hcp_processing_mode'])]

        # -> add t1, t1brain and t2 only if options['hcp_fs_existing_session'] is FALSE
        if (not options['hcp_fs_existing_session']):
            elements.append(('t1', os.path.join(hcp['T1w_folder'], 'T1w_acpc_dc_restore.nii.gz')))
            elements.append(('t1brain', os.path.join(hcp['T1w_folder'], 'T1w_acpc_dc_restore_brain.nii.gz')))
            elements.append(('t2', t2w))

        # -> Additional, reconall parameters

        if options['hcp_fs_extra_reconall']:
            for f in options['hcp_fs_extra_reconall'].split('|'):
                elements.append(('extra-reconall-arg', f))

        # -> additional QuNex passed parameters

        if options['hcp_expert_file']:
            elements.append(('extra-reconall-arg', '-expert'))
            elements.append(('extra-reconall-arg', options['hcp_expert_file']))

        # --> Pull all together

        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])
        # --> Add flags

        for optionName, flag in [('hcp_fs_flair', '--flair'), ('hcp_fs_existing_session', '--existing-subject')]:
            if options[optionName]:
                comm += " %s" % (flag)

        # -- Report command
        if run:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test files

        if hcp['hcp_fs_check']:
            fullTest = {'tfolder': hcp['base'], 'tfile': hcp['hcp_fs_check'], 'fields': [('sessionid', sinfo['id'] + options['hcp_suffix'])], 'specfolder': options['specfolder']}
        else:
            fullTest = None

        # -- Run

        if run:
            if options['run'] == "run":

                # --> clean up test file if overwrite and hcp_fs_existing_session not set to True
                if (overwrite and os.path.lexists(tfile)and not options['hcp_fs_existing_session']):
                    os.remove(tfile)

                # --> clean up only if hcp_fs_existing_session is not set to True
                if (overwrite or not os.path.exists(tfile)) and not options['hcp_fs_existing_session']:
                    # -> longitudinal mode currently not supported
                    # if options['hcp_fs_longitudinal']:
                    #     if os.path.lexists(hcp['FS_long_results']):
                    #         r += "\n --> removing preexisting folder with longitudinal results [%s]" % (hcp['FS_long_results'])
                    #         shutil.rmtree(hcp['FS_long_results'])
                    # else:
                        if os.path.lexists(hcp['FS_folder']):
                            r += "\n ---> removing preexisting FS folder [%s]" % (hcp['FS_folder'])
                            shutil.rmtree(hcp['FS_folder'])
                        for toremove in ['fsaverage', 'lh.EC_average', 'rh.EC_average', os.path.join('xfms','OrigT1w2T1w.nii.gz')]:
                            rmtarget = os.path.join(hcp['T1w_folder'], toremove)
                            try:
                                if os.path.islink(rmtarget) or os.path.isfile(rmtarget):
                                    os.remove(rmtarget)
                                elif os.path.isdir(rmtarget):
                                    shutil.rmtree(rmtarget)
                            except:
                                r += "\n---> WARNING: Could not remove preexisting file/folder: %s! Please check your data!" % (rmtarget)
                                status = False
                if status:
                    r, endlog, report, failed = pc.runExternalForFile(tfile, comm, 'Running HCP FS', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=options['logtag'], fullTest=fullTest, shell=True, r=r)

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(tfile, fullTest, 'HCP FS', r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP FS can be run"
                    report = "HCP FS can be run"
                    failed = 0
        else:
            r += "\n---> Subject can not be processed."
            report = "FS can not be run"
            failed = 1

    except ge.CommandFailed as e:
        r +=  "\n\nERROR in completing %s at %s:\n     %s\n" % ('FreeSurfer', e.function, "\n     ".join(e.report))
        report = "FS failed"
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        failed = 1

    r += "\n\nHCP FS %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, (sinfo['id'], report, failed))



def longitudinal_freesurfer(sinfo, options, overwrite=False, thread=0):
    """
    ``longitudinal_freesurfer [... processing options]``

    Runs longitudinal FreeSurfer processing in cases when multiple sessions with
    structural data exist for a single subject.

    REQUIREMENTS
    ============

    The code expects the FreeSurfer Pipeline (hcp_pre_freesurfer) to have run
    successfully on all subject's session. In the batch file, there need to be
    clear separation between session id (`id` parameter) and subject id
    (`subject` parameter). So that the command can identify which sessions
    belong to which subject.

    INPUT
    =====

    General parameters
    ------------------

    When running the command, the following *general* processing parameters are
    taken into account:

    --sessions            The batch.txt file with all the sessions information.
                          [batch.txt]
    --sessionsfolder      The path to the study/subjects folder, where the
                          imaging data is supposed to go. [.]
    --parsessions         How many sessions to run in parallel. [1]
    --overwrite           Whether to overwrite existing data (yes) or not (no).
                          [no]
    --hcp_suffix          Specifies a suffix to the session id if multiple
                          variants are run, empty otherwise. []
    --logfolder           The path to the folder where runlogs and comlogs
                          are to be stored, if other than default. []
    --log                 Whether to keep ('keep') or remove ('remove') the
                          temporary logs once jobs are completed. ['keep']
                          When a comma or pipe ('|') separated list is given,
                          the log will be created at the first provided
                          location and then linked or copied to other
                          locations. The valid locations are:

                          - 'study' (for the default:
                            `<study>/processing/logs/comlogs` location)
                          - 'session' (for `<sessionid>/logs/comlogs`)
                          - 'hcp' (for `<hcp_folder>/logs/comlogs`)
                          - '<path>' (for an arbitrary directory)

    --hcp_folderstructure       Specifies the version of the folder structure to
                                use, 'initial' and 'hcpls' are supported.
                                ['hcpls']
    --hcp_filename              Specifies whether the standard ('standard')
                                filenames or the specified original names
                                ('original') are to be used. ['standard']

    Specific parameters
    -------------------

    In addition the following *specific* parameters will be used to guide the
    processing in this step:

    --hcp_t2                     NONE if no T2w image is available and the
                                 preprocessing should be run without them,
                                 anything else otherwise. [t2]
    --hcp_expert_file            Path to the read-in expert options file for
                                 FreeSurfer if one is prepared and should be
                                 used empty otherwise. []
    --hcp_control_points         Specify YES to use manual control points or
                                 empty otherwise. []
    --hcp_wm_edits               Specify YES to use manually edited WM mask or
                                 empty otherwise. []
    --hcp_fs_brainmask           Specify 'original' to keep the masked original
                                 brain image; 'manual' to use the manually
                                 edited brainmask file; default 'fs' uses the
                                 brainmask generated by mri_watershed. [fs]
    --hcp_autotopofix_off        Specify YES to turn off the automatic
                                 topological fix step in FS and compute WM
                                 surface deterministically from manual WM mask,
                                 or empty otherwise. []
    --hcp_freesurfer_home        Path for FreeSurfer home folder can be manually
                                 specified to override default environment
                                 variable to ensure backwards compatibility and
                                 hcp_freesurfer customization.
    --hcp_freesurfer_module      Whether to load FreeSurfer as a module on the
                                 cluster. You can specify using YES or empty
                                 otherwise. [] To ensure backwards compatibility
                                 and hcp_freesurfer customization.
    --hcp_fs_longitudinal        The name of the FS longitudinal template to
                                 be used for the template resulting from this
                                 command call.

    OUTPUTS
    =======

    The result is a longitudinal FreeSurfer template that is created in
    `FSTemplates` folder for each subject in a subfolder with the template name,
    but is also copied to each session's hcp folder in the T1w folder as
    subjectid.long.TemplateA. An example is shown below::

        study
        └─ subjects
           ├─ subject1_session1
           │  └─ hcp
           │     └─ subject1_session1
           │       └─ T1w
           │          ├─ subject1_session1 (FS folder - original)
           │          └─ subject1_session1.long.TemplateA (FS folder - longitudinal)
           ├─ subject1_session2
           ├─ ...
           └─ FSTemplates
              ├─ subject1
              │  └─ TemplateA
              └─ ...

    EXAMPLE USE
    ===========

    ::

        qunex longitudinal_freesurfer sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no parsessions=10

    ::

        qunex longitudinal_freesurfer sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no parsessions=10 hcp_t2=NONE

    ::

        qunex longitudinal_freesurfer sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no parsessions=10 hcp_t2=NONE \\
              hcp_freesurfer_home=<absolute_path_to_freesurfer_binary> \\
              hcp_freesurfer_module=YES
    """

    r = "\n------------------------------------------------------------"
    r += "\nSubject id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n\n%s Longitudinal FreeSurfer Pipeline [%s] ...\n" % (pc.action("Running", options['run']), options['hcp_processing_mode'])

    run           = True
    report        = "Error"
    sessionsid    = []
    sessionspaths = []
    resultspaths  = []

    try:

        # --- check that we have data for all sessions

        r += "\n---> Checking sessions for subject %s" % (sinfo['id'])

        for session in sinfo['sessions']:
            r += "\n     => session %s" % (session['id'])
            sessionsid.append(session['id'] + options['hcp_suffix'])
            sessionStatus = True

            try:
                pc.doOptionsCheck(options, sinfo, 'longitudinal_freesurfer')
                doHCPOptionsCheck(options, sinfo, 'longitudinal_freesurfer')
                hcp = getHCPPaths(session, options)
                sessionspaths.append(hcp['FS_folder'])
                resultspaths.append(hcp['FS_long_results'])
                # --- run checks

                if 'hcp' not in session:
                    r += "\n       -> ERROR: There is no hcp info for session %s in batch file" % (session['id'])
                    sessionStatus = False

                # --- check for T1w and T2w images

                for tfile in hcp['T1w'].split("@"):
                    if os.path.exists(tfile):
                        r += "\n       -> T1w image file present."
                    else:
                        r += "\n       -> ERROR: Could not find T1w image file."
                        sessionStatus = False

                if hcp['T2w'] == 'NONE':
                    r += "\n       -> Not using T2w image."
                else:
                    for tfile in hcp['T2w'].split("@"):
                        if os.path.exists(tfile):
                            r += "\n       -> T2w image file present."
                        else:
                            r += "\n       -> ERROR: Could not find T2w image file."
                            sessionStatus = False

                # -> Pre FS results

                if os.path.exists(os.path.join(hcp['T1w_folder'], 'T1w_acpc_dc_restore_brain.nii.gz')):
                    r += "\n       -> PreFS results present."
                else:
                    r += "\n       -> ERROR: Could not find PreFS processing results."
                    sessionStatus = False

                # -> FS results

                if os.path.exists(os.path.join(hcp['FS_folder'], 'mri', 'aparc+aseg.mgz')):
                    r += "\n       -> FS results present."
                else:
                    r += "\n       -> ERROR: Could not find Freesurfer processing results."
                    sessionStatus = False

                if sessionStatus:
                    r += "\n     => data check for session completed successfully!\n"
                else:
                    r += "\n     => data check for session failed!\n"
                    run = False
            except:
                r += "\n     => data check for session failed!\n"

        if run:
            r += "\n===> OK: Sessions check completed with success!"
        else:
            r += "\n===> ERROR: Sessions check failed. Please check your data before proceeding!"

        if hcp['T2w'] == 'NONE':
            t2w = 'NONE'
        else:
            t2w = 'T2w_acpc_dc_restore.nii.gz'

        # --- set up command

        comm = '%(script)s \
            --subject="%(subject)s" \
            --subjectDIR="%(subjectDIR)s" \
            --expertfile="%(expertfile)s" \
            --controlpoints="%(controlpoints)s" \
            --wmedits="%(wmedits)s" \
            --autotopofixoff="%(autotopofixoff)s" \
            --fsbrainmask="%(fsbrainmask)s" \
            --freesurferhome="%(freesurferhome)s" \
            --fsloadhpcmodule="%(fsloadhpcmodule)s" \
            --t1="%(t1)s" \
            --t1brain="%(t1brain)s" \
            --t2="%(t2)s" \
            --timepoints="%(timepoints)s" \
            --longitudinal="template"' % {
                'script'            : os.path.join(hcp['hcp_base'], 'FreeSurfer', 'FreeSurferPipeline.sh'),
                'subject'           : options['hcp_fs_longitudinal'],
                'subjectDIR'        : os.path.join(options['sessionsfolder'], 'FSTemplates', sinfo['id']),
                'freesurferhome'    : options['hcp_freesurfer_home'],      # -- Alan added option for --hcp_freesurfer_home flag passing
                'fsloadhpcmodule'   : options['hcp_freesurfer_module'],   # -- Alan added option for --hcp_freesurfer_module flag passing
                'expertfile'        : options['hcp_expert_file'],
                'controlpoints'     : options['hcp_control_points'],
                'wmedits'           : options['hcp_wm_edits'],
                'autotopofixoff'    : options['hcp_autotopofix_off'],
                'fsbrainmask'       : options['hcp_fs_brainmask'],
                't1'                : "",
                't1brain'           : "",
                't2'                : "",
                'timepoints'        : ",".join(sessionspaths)}

        # -- Report command
        if run:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

       # -- Test files

        if hcp['hcp_fslong_check']:
            fullTest = {'tfolder': hcp['base'], 'tfile': hcp['hcp_fslong_check'], 'fields': [('sessionid', sinfo['id'] + options['hcp_suffix'])], 'specfolder': options['specfolder']}
        else:
            fullTest = None

        # -- Run

        if run:
            if options['run'] == "run":
                lttemplate = hcp['FS_long_subject_template']
                tfile      = os.path.join(hcp['FS_long_results'], 'label', 'rh.entorhinal_exvivo.label')

                if overwrite or not os.path.exists(tfile):
                    try:
                        if os.path.exists(lttemplate):
                            rmfolder = lttemplate
                            shutil.rmtree(lttemplate)
                        for rmfolder in resultspaths:
                            if os.path.exists(rmfolder):
                                shutil.rmtree(rmfolder)
                    except:
                        r += "\n---> WARNING: Could not remove preexisting folder: %s! Please check your data!" % (rmfolder)
                        status = False

                    r, endlog, report, failed = pc.runExternalForFile(tfile, comm, 'Running HCP FS Longitudinal', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=options['logtag'], fullTest=fullTest, shell=True, r=r)

            # -- just checking
            else:
                r += "\n---> The command was tested for sessions: %s" % (", ".join(sessionsid))
                report = "Command can be run"
                failed = 0

        else:
            r += "\n---> The command could not be run on sessions: %s" % (", ".join(sessionsid))
            report = "Command can not be run"
            failed = 1

    except ge.CommandFailed as e:
        r +=  "\n\nERROR in completing %s at %s:\n     %s\n" % ('FreeSurferLongitudinal', e.function, "\n     ".join(e.report))
        report = "FSLong failed"
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        failed = 1

    r += "\n\nLongitudinal FreeSurfer %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, (sinfo['id'], report, failed))



def hcp_post_freesurfer(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_post_freesurfer [... processing options]``

    Runs the PostFS step of the HCP Pipeline.

    REQUIREMENTS
    ============

    The code expects the previous step (hcp_freesurfer) to have run successfully and
    checks for presence of the last file that should have been generated. Due
    to the number of files that it requires, it does not make a full check for
    all of them!

    RELEVANT PARAMETERS
    ===================

    General parameters
    ------------------

    When running the command, the following *general* processing parameters are
    taken into account:

    --sessions                  The batch.txt file with all the sessions
                                information. [batch.txt]
    --sessionsfolder            The path to the study/sessions folder, where the
                                imaging  data is supposed to go. [.]
    --parsessions               How many sessions to run in parallel. [1]
    --overwrite                 Whether to overwrite existing data (yes) or not
                                (no). [no]
    --hcp_suffix                Specifies a suffix to the session id if multiple
                                variants are run, empty otherwise. []
    --logfolder                 The path to the folder where runlogs and comlogs
                                are to be stored, if other than default. []
    --log                       Whether to keep ('keep') or remove ('remove')
                                the temporary logs once jobs are completed
                                ['keep']. When a comma or pipe ('|') separated
                                list is given, the log will be created at the
                                first provided location and then linked or
                                copied to other locations. The valid locations
                                are:

                                - 'study' (for the default:
                                  `<study>/processing/logs/comlogs` location)
                                - 'session' (for `<sessionid>/logs/comlogs`)
                                - 'hcp' (for `<hcp_folder>/logs/comlogs`)
                                - '<path>' (for an arbitrary directory)

    --hcp_processing_mode       Controls whether the HCP acquisition and
                                processing guidelines should be treated as
                                requirements (HCPStyleData) or if additional
                                processing functionality is allowed
                                (LegacyStyleData). In this case running
                                processing w/o a T2w image.
    --hcp_folderstructure       Specifies the version of the folder structure to
                                use, 'initial' and 'hcpls' are supported.
                                ['hcpls']
    --hcp_filename              Specifies whether the standard ('standard')
                                filenames or the specified original names
                                ('original') are to be used. ['standard']

    Specific parameters
    -------------------

    In addition the following *specific* parameters will be used to guide the
    processing in this step:

    --hcp_t2                     NONE if no T2w image is available and the
                                 preprocessing should be run without them,
                                 anything else otherwise [t2]. NONE is only
                                 valid if 'LegacyStyleData' processing mode was
                                 specified.
    --hcp_grayordinatesres       The resolution of the volume part of the
                                 grayordinate representation in mm. [2]
    --hcp_hiresmesh              The number of vertices for the high resolution
                                 mesh of each hemisphere (in thousands). [164]
    --hcp_lowresmesh             The number of vertices for the low resolution
                                 mesh of each hemisphere (in thousands). [32]
    --hcp_regname                The registration used, FS or MSMSulc. [MSMSulc]
    --hcp_mcsigma                Correction sigma used for metric smoothing.
                                 [sqrt(200)]
    --hcp_inflatescale           Inflate extra scale parameter. [1]
    --hcp_fs_longitudinal        The name of the FS longitudinal template if one
                                 was created and is to be used in this step.
                                 (currently not available)

    OUTPUTS
    =======

    The results of this step will be present in the MNINonLinear folder in the
    sessions's root hcp folder.

    USE
    ===

    Runs the PostFreeSurfer step of the HCP Pipeline. It creates Workbench compatible
    files based on the Freesurfer segmentation and surface registration. It uses
    the adjusted version of the HCP code that enables the preprocessing to run
    also if no T2w image is present.

    EXAMPLE USE
    ===========

    ::

        qunex hcp_post_freesurfer sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no parsessions=10

    ::

        qunex hcp_post_freesurfer sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no parsessions=10 hcp_t2=NONE
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP PostFreeSurfer Pipeline [%s] ...\n" % (pc.action("Running", options['run']), options['hcp_processing_mode'])

    run    = True
    report = "Error"

    try:
        pc.doOptionsCheck(options, sinfo, 'hcp_post_freesurfer')
        doHCPOptionsCheck(options, sinfo, 'hcp_post_freesurfer')
        hcp = getHCPPaths(sinfo, options)

        # --- run checks

        if 'hcp' not in sinfo:
            r += "\n---> ERROR: There is no hcp info for session %s in batch.txt" % (sinfo['id'])
            run = False

        # -> FS results

        if os.path.exists(os.path.join(hcp['FS_folder'], 'mri', 'aparc+aseg.mgz')):
            r += "\n---> FS results present."
        else:
            r += "\n---> ERROR: Could not find Freesurfer processing results."
            run = False

        # -> T2w image

        if hcp['T2w'] in ['', 'NONE'] and options['hcp_processing_mode'] == 'HCPStyleData':
            r += "\n---> ERROR: The requested HCP processing mode is 'HCPStyleData', however, no T2w image was specified!"
            run = False

        ## -> longitudinal processing is currently not supported
        #
        # identify template if longitudinal run
        #
        # lttemplate     = ""
        # fslongitudinal = ""
        #
        # if options['hcp_fs_longitudinal']:
        #     if 'subject' not in sinfo:
        #         r += "\n     ... 'subject' field not defined in batch file, can not run longitudinal FS"
        #         run = False
        #     elif sinfo['subject'] == sinfo['id']:
        #         r += "\n     ... 'subject' field is equal to session 'id' field, can not run longitudinal FS"
        #         run = False
        #     else:
        #         lttemplate = hcp['FS_long_subject_template']
        #         lresults = os.path.join(hcp['FS_long_results'], 'label', 'rh.entorhinal_exvivo.label')
        #         if not os.path.exists(lresults):
        #             r += "\n     ... ERROR: Results of the longitudinal run not present [%s]" % (lresults)
        #             r += "\n                Please check your data and settings!" % (lresults)
        #             run = False
        #         else:
        #             r += "\n     ... longitudinal template present"
        #             fslongitudinal = "run"


        comm = os.path.join(hcp['hcp_base'], 'PostFreeSurfer', 'PostFreeSurferPipeline.sh') + " "
        elements = [("path", sinfo['hcp']),
                    ('subject', sinfo['id'] + options['hcp_suffix']),
                    ('surfatlasdir', os.path.join(hcp['hcp_Templates'], 'standard_mesh_atlases')),
                    ('grayordinatesdir', os.path.join(hcp['hcp_Templates'], '91282_Greyordinates')),
                    ('grayordinatesres', options['hcp_grayordinatesres']),
                    ('hiresmesh', options['hcp_hiresmesh']),
                    ('lowresmesh', options['hcp_lowresmesh']),
                    ('subcortgraylabels', os.path.join(hcp['hcp_Config'], 'FreeSurferSubcorticalLabelTableLut.txt')),
                    ('freesurferlabels', os.path.join(hcp['hcp_Config'], 'FreeSurferAllLut.txt')),
                    ('refmyelinmaps', os.path.join(hcp['hcp_Templates'], 'standard_mesh_atlases', 'Conte69.MyelinMap_BC.164k_fs_LR.dscalar.nii')),
                    ('mcsigma', options['hcp_mcsigma']),
                    ('regname', options['hcp_regname']),
                    ('inflatescale', options['hcp_inflatescale']),
                    ('processing-mode', options['hcp_processing_mode'])]

        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])

        # -- Report command
        if run:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"


        # -- Test files

        if False: #  fslongitudinal not supported:
            tfolder = hcp['hcp_long_nonlin']
            tfile = os.path.join(tfolder, sinfo['id'] + options['hcp_suffix'] + '.long.' + options['hcp_fs_longitudinal'] + '.corrThickness.164k_fs_LR.dscalar.nii')
        else:
            tfolder = hcp['hcp_nonlin']
            tfile = os.path.join(tfolder, sinfo['id'] + options['hcp_suffix'] + '.corrThickness.164k_fs_LR.dscalar.nii')

        if hcp['hcp_postfs_check']:
            fullTest = {'tfolder': hcp['base'], 'tfile': hcp['hcp_postfs_check'], 'fields': [('sessionid', sinfo['id'] + options['hcp_suffix'])], 'specfolder': options['specfolder']}
        else:
            fullTest = None

        # -- run

        if run:
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, endlog, report, failed = pc.runExternalForFile(tfile, comm, 'Running HCP PostFS', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=options['logtag'], fullTest=fullTest, shell=True, r=r)

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(tfile, fullTest, 'HCP PostFS', r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP PostFS can be run"
                    report = "HCP PostFS can be run"
                    failed = 0
        else:
            r += "\n---> Session can not be processed."
            report = "HCP PostFS can not be run"
            failed = 1

    except ge.CommandFailed as e:
        r +=  "\n\nERROR in completing %s at %s:\n     %s\n" % ('PostFreeSurfer', e.function, "\n     ".join(e.report))
        report = "PostFS failed"
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        failed = 1

    r += "\n\nHCP PostFS %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, (sinfo['id'], report, failed))


def hcp_diffusion(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_diffusion [... processing options]``

    Runs the Diffusion step of HCP Pipeline.

    REQUIREMENTS
    ============

    The code expects the first HCP preprocessing step (hcp_pre_freesurfer) to have been
    run and finished successfully. It expects the DWI data to have been acquired
    in phase encoding reversed pairs, which should be present in the Diffusion
    folder in the sessions's root hcp folder.

    INPUTS
    ======

    General parameters
    ------------------

    When running the command, the following *general* processing parameters are
    taken into account:

    --sessions            The batch.txt file with all the sessions information.
                          [batch.txt]
    --sessionsfolder      The path to the study/sessions folder, where the
                          imaging data is supposed to go. [.]
    --parsessions         How many sessions to run in parallel. [1]
    --overwrite           Whether to overwrite existing data (yes) or not (no).
                          [no]
    --hcp_suffix          Specifies a suffix to the session id if multiple
                          variants are run, empty otherwise. []
    --logfolder           The path to the folder where runlogs and comlogs
                          are to be stored, if other than default. []
    --log                 Whether to keep ("keep") or remove ("remove") the
                          temporary logs once jobs are completed. ["keep"]
                          When a comma or pipe ("|") separated list is given,
                          the log will be created at the first provided location
                          and then linked or copied to other locations.
                          The valid locations are:

                          - "study" (for the default:
                            "<study>/processing/logs/comlogs" location)
                          - "session" (for "<sessionid>/logs/comlogs")
                          - "hcp" (for "<hcp_folder>/logs/comlogs")
                          - "<path>" (for an arbitrary directory)

    In addition a number of *specific* parameters can be used to guide the
    processing in this step:

    Image acquisition details
    -------------------------

    --hcp_dwi_echospacing   Echo Spacing or Dwelltime of DWI images.
                            [image specific]
    --use_sequence_info     A pipe, comma or space separated list of inline
                            sequence information to use in preprocessing of
                            specific image modalities.

                            Example specifications:

                            - "all": use all present inline information for
                              all modalities,
                            - "DwellTime": use DwellTime information for all
                              modalities,
                            - "T1w:all": use all present inline information
                              for T1w modality,
                            - "SE:EchoSpacing": use EchoSpacing information
                              for Spin-Echo fieldmap images.
                            - "none": do not use inline information

                            Modalities: T1w, T2w, SE, BOLD, dMRI
                            Inline information: TR, PEDirection, EchoSpacing
                            DwellTime, ReadoutDirection

                            If information is not specified it will not be
                            used. More general specification (e.g. "all")
                            implies all more specific cases (e.g. "T1w:all").
                            ["all"]

    Distortion correction details
    -----------------------------

    --hcp_dwi_phasepos      The direction of unwarping for positive phase.
                            Can be AP, PA, LR, or RL. Negative phase is
                            set automatically based on this setting. [PA]
    --hcp_dwi_gdcoeffs      A path to a file containing gradient distortion
                            coefficients, alternatively a string describing
                            multiple options (see below), or "NONE", if not
                            used [NONE].

    Eddy post processing parameters
    -------------------------------

    --hcp_dwi_dof           Degrees of Freedom for post eddy registration to
                            structural images. [6]
    --hcp_dwi_b0maxbval     Volumes with a bvalue smaller than this value
                            will be considered as b0s. [50]
    --hcp_dwi_combinedata   Specified value is passed as the CombineDataFlag
                            value for the eddy_postproc.sh script. If JAC
                            resampling has been used in eddy, this value
                            determines what to do with the output file.
                            2 - include in the output all volumes uncombined
                                (i.e. output file of eddy)
                            1 - include in the output and combine only
                                volumes where both LR/RL (or AP/PA) pairs
                                have been acquired
                            0 - As 1, but also include uncombined single
                                volumes
                            [1]
    --hcp_dwi_selectbestb0  If set selects the best b0 for each phase
                            encoding direction to pass on to topup rather
                            than the default behaviour of using equally
                            spaced b0's throughout the scan. The best b0
                            is identified as the least distorted (i.e., most
                            similar to the average b0 after registration).
                            The flag is not set by default.
    --hcp_dwi_extraeddyarg  A string specifying additional arguments to pass
                            to the DiffPreprocPipeline_Eddy.sh script and
                            subsequently to the run_eddy.sh script and
                            finally to the command that actually invokes the
                            eddy binary. The string is to be written as a
                            contiguous set of arguments to be added. Each
                            argument needs to be provided together with
                            dashes if it needs them. To provide multiple
                            arguments divide them with the pipe (|)
                            character,
                            e.g. --hcp_dwi_extraeddyarg="--niter=8|--nvoxhp=2000".
                            [""]

    Additional parameters
    ---------------------

    --hcp_dwi_name          Name to give DWI output directories. [Diffusion]
    --hcp_dwi_cudaversion   If using the GPU-enabled version of eddy, then
                            this option can be used to specify which
                            eddy_cuda binary version to use. If X.Y is
                            specified, then FSLDIR/bin/eddy_cudaX.Y will be
                            used. Note that CUDA 9.1 is installed in the
                            container. []
    --hcp_dwi_nogpu         If specified, use the non-GPU-enabled version
                            of eddy. Defaults to using the GPU-enabled
                            version of eddy. []

    Gradient Coefficient File Specification:
    ----------------------------------------

    --hcp_dwi_gdcoeffs parameter can be set to either "NONE", a path to a
    specific file to use, or a string that describes, which file to use in which
    case. Each option of the string has to be divided by a pipe "|" character
    and it has to specify, which information to look up, a possible value, and a
    file to use in that case, separated by a colon ":" character. The
    information too look up needs to be present in the description of that
    session. Standard options are e.g.::

        institution: Yale
        device: Siemens|Prisma|123456

    Where device is formatted as "<manufacturer>|<model>|<serial number>".

    If specifying a string it also has to include a "default" option, which
    will be used in the information was not found. An example could be::

        "default:/data/gc1.conf|model:Prisma:/data/gc/Prisma.conf|model:Trio:/data/gc/Trio.conf"

    With the information present above, the file "/data/gc/Prisma.conf" would
    be used.

    OUTPUTS
    =======

    The results of this step will be present in the Diffusion folder in the
    sessions's root hcp folder.

    USE
    ===

    Runs the Diffusion step of HCP Pipeline. It preprocesses diffusion weighted
    images (DWI). Specifically, after b0 intensity normalization, the b0 images
    of both phase encoding directions are used to calculate the
    susceptibility-induced B0 field deviations.The full timeseries from both
    phase encoding directions is used in the “eddy” tool for modeling of eddy
    current distortions and subject motion. Gradient distortion is corrected and
    the b0 image is registered to the T1w image using BBR. The diffusion data
    output from eddy are then resampled into 1.25mm native structural space and
    masked. Diffusion directions and the gradient deviation estimates are also
    appropriately rotated and registered into structural space. The function
    enables the use of a number of parameters to customize the specific
    preprocessing steps.

    EXAMPLE USE
    ===========

    Example run from the base study folder with test flag::

        qunex hcp_diffusion \
          --sessionsfolder="<path_to_study_folder>/sessions" \
          --sessions="<path_to_study_folder>/processing/batch.txt" \
          --overwrite="no" \\
          --test

    Run with scheduler, the compute node also loads the required CUDA module::

        qunex hcp_diffusion \
          --sessionsfolder="<path_to_study_folder>/sessions" \
          --sessions="$<path_to_study_folder>/processing/batch.txt" \
          --overwrite="yes" \\
          --bash="module load CUDA/9.1.85" \
          --scheduler="SLURM,time=24:00:00,ntasks=1,cpus-per-task=1,mem-per-cpu=16000,partition=GPU,gres=gpu:1"

    Run without a scheduler and without GPU support::

        qunex hcp_diffusion \
          --sessionsfolder="<path_to_study_folder>/sessions" \
          --sessions="<path_to_study_folder>/processing/batch.txt" \
          --overwrite="yes" \\
          --hcp_dwi_nogpu
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP DiffusionPreprocessing Pipeline [%s] ..." % (pc.action("Running", options['run']), options['hcp_processing_mode'])

    run    = True
    report = "Error"

    try:
        pc.doOptionsCheck(options, sinfo, 'hcp_diffusion')
        doHCPOptionsCheck(options, sinfo, 'hcp_diffusion')
        hcp = getHCPPaths(sinfo, options)

        if 'hcp' not in sinfo:
            r += "\n---> ERROR: There is no hcp info for session %s in batch.txt" % (sinfo['id'])
            run = False

        # --- using a legacy parameter?
        if 'hcp_dwi_PEdir' in options:
            r += "\n---> WARNING: you are still providing the hcp_dwi_PEdir parameter which has been replaced with hcp_dwi_phasepos! Please consult the documentation to see how to use it."
            r += "\n---> hcp_dwi_phasepos is currently set to %s." % options['hcp_dwi_phasepos']

        # --- set up data
        if options['hcp_dwi_phasepos'] == "PA":
            direction = [('pos', 'PA'), ('neg', 'AP')]
            pe_dir = 2
        elif options['hcp_dwi_phasepos'] == "AP":
            direction = [('pos', 'AP'), ('neg', 'PA')]
            pe_dir = 2
        elif options['hcp_dwi_phasepos'] == "LR":
            direction = [('pos', 'LR'), ('neg', 'RL')]
            pe_dir = 1
        elif options['hcp_dwi_phasepos'] == "RL":
            direction = [('pos', 'RL'), ('neg', 'LR')]
            pe_dir = 1
        else:
            r += "\n---> ERROR: Invalid value of the hcp_dwi_phasepos parameter [%s]" % options['hcp_dwi_phasepos']
            run = False

        if run:
            # get subject's DWIs
            dwis = dict()
            for k, v in sinfo.items():
                if k.isdigit() and v['name'] == 'DWI':
                    dwis[int(k)] = v["task"]

            # get dwi files
            dwi_data = dict()
            for ddir, dext in direction:
                dwi_files = glob.glob(os.path.join(hcp['DWI_source'], "*_%s.nii.gz" % (dext)))

                # sort by temporal order as specified in batch
                for dwi in sorted(dwis):
                    for dwi_file in dwi_files:
                        if dwis[dwi] in dwi_file:
                            if ddir in dwi_data:
                                dwi_data[ddir] = dwi_data[ddir] + "@" + dwi_file
                            else:
                                dwi_data[ddir] = dwi_file
                            break

            for ddir in ['pos', 'neg']:
                dfiles = dwi_data[ddir].split("@")

                if dfiles and dfiles != ['']:
                    r += "\n---> The following %s direction files were found:" % (ddir)
                    for dfile in dfiles:
                        r += "\n     %s" % (os.path.basename(dfile))
                else:
                    r += "\n---> ERROR: No %s direction files were found!" % ddir
                    run = False

        # --- lookup gdcoeffs file if needed
        gdcfile, r, run = checkGDCoeffFile(options['hcp_dwi_gdcoeffs'], hcp=hcp, sinfo=sinfo, r=r, run=run)

        # -- set echospacing
        dwiinfo = [v for (k, v) in sinfo.iteritems() if k.isdigit() and v['name'] == 'DWI'][0]

        if 'EchoSpacing' in dwiinfo and checkInlineParameterUse('dMRI', 'EchoSpacing', options):
            echospacing = dwiinfo['EchoSpacing']
            r += "\n---> Using image specific EchoSpacing: %s ms" % (echospacing)
        else:
            echospacing = options['hcp_dwi_echospacing']
            r += "\n---> Using study general EchoSpacing: %s ms" % (echospacing)

        # --- build the command
        if run:
            comm = '%(script)s \
                --path="%(path)s" \
                --subject="%(subject)s" \
                --PEdir=%(pe_dir)s \
                --posData="%(pos_data)s" \
                --negData="%(neg_data)s" \
                --echospacing="%(echospacing)s" \
                --gdcoeffs="%(gdcoeffs)s" \
                --dof="%(dof)s" \
                --b0maxbval="%(b0maxbval)s" \
                --combine-data-flag="%(combinedataflag)s" \
                --printcom="%(printcom)s"' % {
                    'script'            : os.path.join(hcp['hcp_base'], 'DiffusionPreprocessing', 'DiffPreprocPipeline.sh'),
                    'pos_data'          : dwi_data['pos'],
                    'neg_data'          : dwi_data['neg'],
                    'path'              : sinfo['hcp'],
                    'subject'           : sinfo['id'] + options['hcp_suffix'],
                    'echospacing'       : echospacing,
                    'pe_dir'            : pe_dir,
                    'gdcoeffs'          : gdcfile,
                    'dof'               : options['hcp_dwi_dof'],
                    'b0maxbval'         : options['hcp_dwi_b0maxbval'],
                    'combinedataflag'   : options['hcp_dwi_combinedata'],
                    'printcom'          : options['hcp_printcom']}

            # -- Optional parameters
            if options['hcp_dwi_extraeddyarg'] is not None:
                eddyoptions = options['hcp_dwi_extraeddyarg'].split("|")

                if eddyoptions != ['']:
                    for eddyoption in eddyoptions:
                        comm += "                --extra-eddy-arg=" + eddyoption

            if options['hcp_dwi_name'] is not None:
                comm += "                --dwiname=" + options['hcp_dwi_name']

            if options['hcp_dwi_selectbestb0'] == "True":
                comm += "                --select-best-b0"

            if options['hcp_dwi_cudaversion'] is not None:
                comm += "                --cuda-version=" + options['hcp_dwi_cudaversion']

            if options['hcp_dwi_nogpu'] == "True":
                comm += "                --no-gpu"


            # -- Report command
            if run:
                r += "\n\n------------------------------------------------------------\n"
                r += "Running HCP Pipelines command via QuNex:\n\n"
                r += comm.replace("                --", "\n    --")
                r += "\n------------------------------------------------------------\n"

            # -- Test files
            tfile = os.path.join(hcp['T1w_folder'], 'Diffusion', 'data.nii.gz')

            if hcp['hcp_dwi_check']:
                full_test = {'tfolder': hcp['base'], 'tfile': hcp['hcp_dwi_check'], 'fields': [('sessionid', sinfo['id'])], 'specfolder': options['specfolder']}
            else:
                full_test = None

        # -- Run
        if run:
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, endlog, report, failed  = pc.runExternalForFile(tfile, comm, 'Running HCP Diffusion Preprocessing', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=options['logtag'], fullTest=full_test, shell=True, r=r)

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(tfile, full_test, 'HCP Diffusion', r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP Diffusion can be run"
                    report = "HCP Diffusion can be run"
                    failed = 0

        else:
            r += "\n---> Session can not be processed."
            report = "HCP Diffusion can not be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        failed = 1

    r += "\n\nHCP Diffusion Preprocessing %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, (sinfo['id'], report, failed))



def hcp_fmri_volume(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_fmri_volume [... processing options]``

    Runs the fMRI Volume step of HCP Pipeline.

    REQUIREMENTS
    ============

    The code expects the first two HCP preprocessing steps (hcp_pre_freesurfer and
    hcp_freesurfer) to have been run and finished successfully. It also tests for the
    presence of fieldmap or spin-echo images if they were specified. It does
    not make a thorough check for PreFS and FS steps due to the large number
    of files. If `hcp_fs_longitudinal` is specified, it also checks for
    presence of the specified longitudinal data.

    INPUTS
    ======

    General parameters
    ------------------

    When running the command, the following *general* processing parameters are
    taken into account:

    --sessions              The batch.txt file with all the sessions
                            information. [batch.txt]
    --sessionsfolder        The path to the study/sessions folder, where the
                            imaging  data is supposed to go. [.]
    --parsessions           How many sessions to run in parallel. [1]
    --parelements           How many elements (e.g bolds) to run in
                            parallel. [1]
    --bolds                 Which bold images (as they are specified in the
                            batch.txt file) to process. It can be a single
                            type (e.g. 'task'), a pipe separated list (e.g.
                            'WM|Control|rest') or 'all' to process all.
                            [all]
    --overwrite             Whether to overwrite existing data (yes) or not
                            (no). [no]
    --hcp_suffix            Specifies a suffix to the session id if multiple
                            variants are run, empty otherwise. []
    --logfolder             The path to the folder where runlogs and comlogs
                            are to be stored, if other than default. []
    --log                   Whether to keep ('keep') or remove ('remove')
                            the temporary logs once jobs are completed
                            ['keep']. When a comma or pipe ('|') separated
                            list is given, the log will be created at the
                            first provided location and then linked or
                            copied to other locations. The valid locations
                            are:

                            - 'study' (for the default:
                              `<study>/processing/logs/comlogs` location)
                            - 'session' (for `<sessionid>/logs/comlogs`)
                            - 'hcp' (for `<hcp_folder>/logs/comlogs`)
                            - '<path>' (for an arbitrary directory)

    --hcp_processing_mode   Controls whether the HCP acquisition and
                            processing guidelines should be treated as
                            requirements (HCPStyleData) or if additional
                            processing functionality is allowed
                            (LegacyStyleData). In this case running
                            processing with slice timing correction,
                            external BOLD reference, or without a distortion
                            correction method.
    --hcp_folderstructure   Specifies the version of the folder structure to
                            use, 'initial' and 'hcpls' are supported.
                            ['hcpls']
    --hcp_filename          Specifies whether the standard ('standard')
                            filenames or the specified original names
                            ('original') are to be used. ['standard']


    In addition a number of *specific* parameters can be used to guide the
    processing in this step:

    Specific parameters
    -------------------

    --hcp_bold_biascorrection       Whether to perform bias correction for BOLD
                                    images. NONE or Legacy. [NONE]
    --hcp_bold_usejacobian          Whether to apply the jacobian of the
                                    distortion correction to fMRI data.

    Use of FS longitudinal template
    -------------------------------

    --hcp_fs_longitudinal   The name of the FS longitudinal template if one
                            was created and is to be used in this step.
                            (This parameter is currently not supported)

    Naming options
    --------------

    --hcp_bold_prefix       The prefix to use when generating BOLD names 
                            (see 'hcp_filename') for BOLD working folders 
                            and results. [BOLD]
    --hcp_filename          Specifies whether BOLD names are to be created
                            using sequential numbers ('standard') using the
                            formula `<hcp_bold_prefix>_[N]` (e.g. BOLD_3)
                            or actual bold names ('original', e.g.
                            rfMRI_REST1_AP). ['standard']

    Image acquisition details
    -------------------------

    --hcp_bold_echospacing  Echo Spacing or Dwelltime of BOLD images.
                            [0.00035]
    --hcp_bold_sbref        Whether BOLD Reference images should be used
                            - NONE or USE. [NONE]
    --use_sequence_info     A pipe, comma or space separated list of inline
                            sequence information to use in preprocessing of
                            specific image modalities.

                            Example specifications:

                            - `all`: use all present inline information for
                              all modalities,
                            - 'DwellTime': use DwellTime information for all
                              modalities,
                            - `T1w:all': use all present inline information
                              for T1w modality,
                            - `SE:EchoSpacing': use EchoSpacing information
                              for Spin-Echo fieldmap images.
                            - 'none': do not use inline information

                            Modalities: T1w, T2w, SE, BOLD, dMRi
                            Inline information: TR, PEDirection, EchoSpacing
                              DwellTime, ReadoutDirection

                            If information is not specified it will not be
                            used. More general specification (e.g. `all`)
                            implies all more specific cases (e.g. `T1w:all`).
                            ['all']

    Distortion correction details
    -----------------------------

    --hcp_bold_dcmethod     BOLD image deformation correction that should
                            be used: TOPUP, FIELDMAP / SiemensFieldMap,
                            GeneralElectricFieldMap, PhilipsFieldMap or NONE.
                            [TOPUP]
    --hcp_bold_echodiff     Delta TE for BOLD fieldmap images or NONE if
                            not used. [NONE]
    --hcp_bold_sephasepos   Label for the positive image of the Spin Echo
                            Field Map pair []
    --hcp_bold_sephaseneg   Label for the negative image of the Spin Echo
                            Field Map pair []
    --hcp_bold_unwarpdir    The direction of unwarping. Can be specified
                            separately for LR/RL : `'LR=x|RL=-x|x'` or
                            separately for PA/AP : `'PA=y|AP=y-|y-'`. [y]
    --hcp_bold_res          Target image resolution. 2mm recommended. [2].
    --hcp_bold_gdcoeffs     Gradient distortion correction coefficients
                            or NONE. [NONE]
    --hcp_bold_topupconfig  A full path to the topup configuration file to use.
                            Set to '' if the default is to be used or of TOPUP
                            distortion correction is not used.

    Slice timing correction
    -----------------------

    --hcp_bold_doslicetime          Whether to do slice timing correction TRUE
                                    or FALSE. []
    --hcp_bold_slicetimerparams     A comma or pipe separated string of
                                    parameters for FSL slicetimer.
    --hcp_bold_stcorrdir            (*) The direction of slice acquisition
                                    ('up' or 'down'. [up]
    --hcp_bold_stcorrint            (*) Whether slices were acquired in an
                                    interleaved fashion (odd) or not (empty).
                                    [odd]

    (*) These parameters are deprecated. If specified, they will be added to
    --hcp_bold_slicetimerparams.

    Motion correction and atlas registration
    ----------------------------------------

    --hcp_bold_preregistertool      What tool to use to preregister BOLDs before
                                    FSL BBR is run, epi_reg (default) or flirt.
                                    [epi_reg]
    --hcp_bold_movreg               Whether to use FLIRT (default and best for
                                    multiband images) or MCFLIRT for motion
                                    correction. [FLIRT]
    --hcp_bold_movref               (*) What reference to use for movement
                                    correction (independent, first).
                                    [independent]
    --hcp_bold_seimg                (*) What image to use for spin-echo
                                    distortion correction (independent, first).
                                    [independent]
    --hcp_bold_refreg               (*) Whether to use only linear (default) or
                                    also nonlinear registration of motion
                                    corrected bold to reference. [linear]
    --hcp_bold_mask                 (*) Specifies what mask to use for the final
                                    bold:

                                    - T1_fMRI_FOV: combined T1w brain mask and
                                      fMRI FOV masks
                                      (the default and HCPStyleData compliant)
                                    - T1_DILATED_fMRI_FOV: a once dilated T1w
                                      brain based mask combined with fMRI FOV
                                    - T1_DILATED2x_fMRI_FOV: a twice dilated T1w
                                      brain based mask combined with fMRI FOV
                                    - fMRI_FOV: a fMRI FOV mask

    (*) These parameters are only valid when running HCPpipelines using the
    LegacyStyleData processing mode!

    These last parameters enable fine-tuning of preprocessing and deserve
    additional information. In general the defaults should be appropriate for
    multiband images, single-band can profit from specific adjustments.
    Whereas FLIRT is best used for motion registration of high-resolution BOLD
    images, lower resolution single-band images might be better motion aligned
    using MCFLIRT (--hcp_bold_movreg).

    As a movement correction target, either each BOLD can be independently
    registered to T1 image, or all BOLD images can be motion correction aligned
    to the first BOLD in the series and only that image is registered to the T1
    structural image (--hcp_bold_moveref). Do note that in this case also
    distortion correction will be computed for the first BOLD image in the
    series only and applied to all subsequent BOLD images after they were
    motion-correction aligned to the first BOLD.

    Similarly, for distortion correction, either the last preceding spin-echo
    image pair can be used (independent) or only the first spin-echo pair is
    used for all BOLD images (first; --hcp_bold_seimg). Do note that this also
    affects the previous motion correction target setting. If independent
    spin-echo pairs are used, then the first BOLD image after a new spin-echo
    pair serves as a new starting motion-correction reference.

    If there is no spin-echo image pair and TOPUP correction was requested, an
    error will be reported and processing aborted. If there is no preceding
    spin-echo pair, but there is at least one following the BOLD image in
    question, the first following spin-echo pair will be used and no error will
    be reported. The spin-echo pair used is reported in the log.

    When BOLD images are registered to the first BOLD in the series, due to
    larger movement between BOLD images it might be advantageous to use also
    nonlinear alignment to the first bold reference image (--hcp_bold_refreg).

    Lastly, for lower resolution BOLD images it might be better not to use
    subject specific T1 image based brain mask, but rather a mask generated on
    the BOLD image itself or based on the dilated standard MNI brain mask.

    Gradient coefficient file specification:
    ----------------------------------------

    `--hcp_bold_gdcoeffs` parameter can be set to either 'NONE', a path to a
    specific file to use, or a string that describes, which file to use in which
    case. Each option of the string has to be divided by a pipe '|' character
    and it has to specify, which information to look up, a possible value, and a
    file to use in that case, separated by a colon ':' character. The
    information too look up needs to be present in the description of that
    session. Standard options are e.g.::

        institution: Yale
        device: Siemens|Prisma|123456

    Where device is formatted as ``<manufacturer>|<model>|<serial number>``.

    If specifying a string it also has to include a `default` option, which
    will be used in the information was not found. An example could be::

        "default:/data/gc1.conf|model:Prisma:/data/gc/Prisma.conf|model:Trio:/data/gc/Trio.conf"

    With the information present above, the file `/data/gc/Prisma.conf` would
    be used.

    OUTPUTS
    =======

    The results of this step will be present in the MNINonLinear folder in the
    sessions's root hcp folder. In case a longitudinal FS template is used, the
    results will be stored in a `MNINonlinear_<FS longitudinal template name>`
    folder::

        study
        └─ sessions
           └─ subject1_session1
              └─ hcp
                 └─ subject1_session1
                   ├─ MNINonlinear
                   │  └─ Results
                   │     └─ BOLD_1
                   └─ MNINonlinear_TemplateA
                      └─ Results
                         └─ BOLD_1

    USE
    ===

    Runs the fMRI Volume step of HCP Pipeline. It preprocesses BOLD images and
    linearly and nonlinearly registers them to the MNI atlas. It makes use of
    the PreFS and FS steps of the pipeline. It enables the use of a number of
    parameters to customize the specific preprocessing steps..

    EXAMPLE USE
    ===========

    ::

        qunex hcp_fmri_volume sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no parsessions=10

    ::

        qunex hcp_fmri_volume sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no parsessions=10 hcp_bold_movref=first hcp_bold_seimg=first \\
              hcp_bold_refreg=nonlinear hcp_bold_mask=DILATED
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP fMRI Volume registration [%s] ... " % (pc.action("Running", options['run']), options['hcp_processing_mode'])

    run    = True
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, 'hcp_fmri_volume')
        doHCPOptionsCheck(options, sinfo, 'hcp_fmri_volume')
        hcp = getHCPPaths(sinfo, options)

        # --- bold filtering not yet supported!
        # btargets = options['bolds'].split("|")

        # --- run checks

        if 'hcp' not in sinfo:
            r += "\n---> ERROR: There is no hcp info for session %s in batch.txt" % (sinfo['id'])
            run = False

        # -> Pre FS results

        if os.path.exists(os.path.join(hcp['T1w_folder'], 'T1w_acpc_dc_restore_brain.nii.gz')):
            r += "\n---> PreFS results present."
        else:
            r += "\n---> ERROR: Could not find PreFS processing results."
            run = False

        # -> FS results

        if False:  # Longitudinal processing is currently unavailanle # options['hcp_fs_longitudinal']:
            tfolder = hcp['FS_long_results']
        else:
            tfolder = hcp['FS_folder']

        if os.path.exists(os.path.join(tfolder, 'mri', 'aparc+aseg.mgz')):
            r += "\n---> FS results present."
        else:
            r += "\n---> ERROR: Could not find Freesurfer processing results."
            # if options['hcp_fs_longitudinal']:
            #     r += "\n--->        Please check that you have run FS longitudinal as specified,"
            #     r += "\n--->        and that %s template was successfully generated." % (options['hcp_fs_longitudinal'])

            run = False

        # -> PostFS results

        if False:  # Longitudinal processing is currently unavailanle # options['hcp_fs_longitudinal']:
            tfile = os.path.join(hcp['hcp_long_nonlin'], 'fsaverage_LR32k', sinfo['id'] + options['hcp_suffix'] + '.long.' + options['hcp_fs_longitudinal'] + options['hcp_suffix'] + '.32k_fs_LR.wb.spec')
        else:
            tfile = os.path.join(hcp['hcp_nonlin'], 'fsaverage_LR32k', sinfo['id'] + options['hcp_suffix'] + '.32k_fs_LR.wb.spec')

        if os.path.exists(tfile):
            r += "\n---> PostFS results present."
        else:
            r += "\n---> ERROR: Could not find PostFS processing results."
            # if options['hcp_fs_longitudinal']:
            #     r += "\n--->        Please check that you have run PostFS on FS longitudinal as specified,"
            #     r += "\n--->        and that %s template was successfully used." % (options['hcp_fs_longitudinal'])
            run = False

        # -> lookup gdcoeffs file if needed

        gdcfile, r, run = checkGDCoeffFile(options['hcp_bold_gdcoeffs'], hcp=hcp, sinfo=sinfo, r=r, run=run)

        # -> default parameter values

        spinP       = 0
        spinN       = 0
        spinNeg     = ""  # AP or LR
        spinPos     = ""  # PA or RL
        refimg      = "NONE"
        futureref   = "NONE"
        topupconfig = ""
        orient      = ""
        fmmag       = "NONE"
        fmphase     = "NONE"
        fmge        = "NONE"

        # -> Check for SE images

        sepresent = []
        sepairs = {}
        sesettings = False

        if options['hcp_bold_dcmethod'].lower() == 'topup':

            # -- spin echo settings

            sesettings = True
            for p in ['hcp_bold_sephaseneg', 'hcp_bold_sephasepos', 'hcp_bold_unwarpdir', 'hcp_bold_topupconfig']:
                if not options[p]:
                    r += '\n---> ERROR: TOPUP requested but %s parameter is not set! Please review parameter file!' % (p)
                    boldok = False
                    sesettings = False
                    run = False

            if sesettings:
                r += "\n---> Looking for spin echo fieldmap set images [%s/%s]." % (options['hcp_bold_sephasepos'], options['hcp_bold_sephaseneg'])

                for bold in range(50):
                    spinok = False

                    # check if folder exists
                    sepath = glob.glob(os.path.join(hcp['source'], "SpinEchoFieldMap%d*" % (bold)))
                    if sepath:
                        sepath = sepath[0]
                        r += "\n     ... identified folder %s" % (os.path.basename(sepath))
                        # get all *.nii.gz files in that folder
                        images = glob.glob(os.path.join(sepath, "*.nii.gz"))

                        # variable for checking se status
                        spinok = True
                        spinPos, spinNeg = None, None

                        # search in images
                        for i in images:
                            # look for phase positive
                            if "_" + options['hcp_bold_sephasepos'] in os.path.basename(i):
                                spinPos = i
                                r, spinok = pc.checkForFile2(r, spinPos, "\n     ... phase positive %s spin echo fieldmap image present" % (options['hcp_bold_sephasepos']), "\n         ERROR: %s spin echo fieldmap image missing!" % (options['hcp_bold_sephasepos']), status=spinok)
                            # look for phase negative
                            elif "_" + options['hcp_bold_sephaseneg'] in os.path.basename(i):
                                spinNeg = i
                                r, spinok = pc.checkForFile2(r, spinNeg, "\n     ... phase negative %s spin echo fieldmap image present" % (options['hcp_bold_sephaseneg']), "\n         ERROR: %s spin echo fieldmap image missing!" % (options['hcp_bold_sephaseneg']), status=spinok)

                        if not all([spinPos, spinNeg]):
                            r += "\n---> ERROR: Either one of both pairs of SpinEcho images are missing in the %s folder! Please check your data or settings!" % (os.path.basename(sepath))
                            spinok = False

                    if spinok:
                        sepresent.append(bold)
                        sepairs[bold] = {'spinPos': spinPos, 'spinNeg': spinNeg}

            # --> check for topupconfig

            if options['hcp_bold_topupconfig']:
                topupconfig = options['hcp_bold_topupconfig']
                if not os.path.exists(options['hcp_bold_topupconfig']):
                    topupconfig = os.path.join(hcp['hcp_Config'], options['hcp_bold_topupconfig'])
                    if not os.path.exists(topupconfig):
                        r += "\n---> ERROR: Could not find TOPUP configuration file: %s." % (options['hcp_bold_topupconfig'])
                        run = False
                    else:
                        r += "\n     ... TOPUP configuration file present"
                else:
                    r += "\n     ... TOPUP configuration file present"

        # --- Process unwarp direction

        if options['hcp_bold_dcmethod'].lower() in ['topup', 'fieldmap', 'siemensfieldmap', 'philipsfieldmap', 'generalelectricfieldmap']:
            unwarpdirs = [[f.strip() for f in e.strip().split("=")] for e in options['hcp_bold_unwarpdir'].split("|")]
            unwarpdirs = [['default', e[0]] if len(e) == 1 else e for e in unwarpdirs]
            unwarpdirs = dict(unwarpdirs)
        else:
            unwarpdirs = {'default': ""}

        # --- Get sorted bold numbers

        bolds, bskip, report['boldskipped'], r = pc.useOrSkipBOLD(sinfo, options, r)
        if report['boldskipped']:
            if options['hcp_filename'] == 'original':
                report['skipped'] = [bi.get('filename', str(bn)) for bn, bnm, bt, bi in bskip]
            else:
                report['skipped'] = [str(bn) for bn, bnm, bt, bi in bskip]

        # --- Preprocess

        boldsData = []

        if bolds:
            firstSE = bolds[0][3].get('se', None)

        for bold, boldname, boldtask, boldinfo in bolds:

            if 'filename' in boldinfo and options['hcp_filename'] == 'original':
                printbold  = boldinfo['filename']
                boldsource = boldinfo['filename']
                boldtarget = boldinfo['filename']
            else:
                printbold  = str(bold)
                boldsource = 'BOLD_%d' % (bold)
                boldtarget = "%s%s" % (options['hcp_bold_prefix'], printbold)

            r += "\n\n---> %s BOLD %s" % (pc.action("Preprocessing settings (unwarpdir, refimage, moveref, seimage) for", options['run']), printbold)
            boldok = True

            # ===> Check for and prepare distortion correction parameters

            echospacing = ""
            unwarpdir = ""

            if options['hcp_bold_dcmethod'].lower() in ['topup', 'fieldmap', 'siemensfieldmap', 'philipsfieldmap', 'generalelectricfieldmap']:

                # --- set unwarpdir

                if "o" in boldinfo:
                    orient    = "_" + boldinfo['o']
                    unwarpdir = unwarpdirs.get(boldinfo['o'])
                    if unwarpdir is None:
                        r += '\n     ... ERROR: No unwarpdir is defined for %s! Please check hcp_bold_unwarpdir parameter!' % (boldinfo['o'])
                        boldok = False
                elif 'phenc' in boldinfo:
                    orient    = "_" + boldinfo['phenc']
                    unwarpdir = unwarpdirs.get(boldinfo['phenc'])
                    if unwarpdir is None:
                        r += '\n     ... ERROR: No unwarpdir is defined for %s! Please check hcp_bold_unwarpdir parameter!' % (boldinfo['phenc'])
                        boldok = False
                elif 'PEDirection' in boldinfo and checkInlineParameterUse('BOLD', 'PEDirection', options):
                    if boldinfo['PEDirection'] in PEDirMap:
                        orient    = "_" + PEDirMap[boldinfo['PEDirection']]
                        unwarpdir = boldinfo['PEDirection']
                    else:
                        r += '\n     ... ERROR: Invalid PEDirection specified [%s]! Please check sequence specific PEDirection value!' % (boldinfo['PEDirection'])
                        boldok = False
                else:
                    orient = ""
                    unwarpdir = unwarpdirs.get('default')
                    if unwarpdir is None:
                        r += '\n     ... ERROR: No default unwarpdir is set! Please check hcp_bold_unwarpdir parameter!'
                        boldok = False

                if orient:
                    r += "\n     ... phase encoding direction: %s" % (orient[1:])
                else:
                    r += "\n     ... phase encoding direction not specified"

                r += "\n     ... unwarp direction: %s" % (unwarpdir)

                # -- set echospacing

                if 'EchoSpacing' in boldinfo and checkInlineParameterUse('BOLD', 'EchoSpacing', options):
                    echospacing = boldinfo['EchoSpacing']
                    r += "\n     ... using image specific EchoSpacing: %s s" % (echospacing)
                elif options['hcp_bold_echospacing']:
                    echospacing = options['hcp_bold_echospacing']
                    r += "\n     ... using study general EchoSpacing: %s s" % (echospacing)
                else:
                    echospacing = ""
                    r += "\n---> ERROR: EchoSpacing is not set! Please review parameter file."
                    boldok = False

            # --- check for spin-echo-fieldmap image

            if options['hcp_bold_dcmethod'].lower() == 'topup' and sesettings:

                if not sepresent:
                    r += '\n     ... ERROR: No spin echo fieldmap set images present!'
                    boldok = False

                elif options['hcp_bold_seimg'] == 'first':
                    if firstSE is None:
                        spinN = int(sepresent[0])
                        r += "\n     ... using the first recorded spin echo fieldmap set %d" % (spinN)
                    else:
                        spinN = int(firstSE)
                        r += "\n     ... using the spin echo fieldmap set for the first bold run, %d" % (spinN)
                    spinNeg = sepairs[spinN]['spinNeg']
                    spinPos = sepairs[spinN]['spinPos']

                else:
                    spinN = False
                    if 'se' in boldinfo:
                        spinN = int(boldinfo['se'])
                    else:
                        for sen in sepresent:
                            if sen <= bold:
                                spinN = sen
                            elif not spinN:
                                spinN = sen
                    spinNeg = sepairs[spinN]['spinNeg']
                    spinPos = sepairs[spinN]['spinPos']
                    r += "\n     ... using spin echo fieldmap set %d" % (spinN)
                    r += "\n         -> SE Positive image : %s" % (os.path.basename(spinPos))
                    r += "\n         -> SE Negative image : %s" % (os.path.basename(spinNeg))

                # -- are we using a new SE image?

                if spinN != spinP:
                    spinP = spinN
                    futureref = "NONE"

            # --- check for Siemens double TE-fieldmap image

            elif options['hcp_bold_dcmethod'].lower() in ['fieldmap', 'siemensfieldmap']:
                fmnum = boldinfo.get('fm', None)
                fieldok = True
                for i, v in hcp['fieldmap'].iteritems():
                    r, fieldok = pc.checkForFile2(r, hcp['fieldmap'][i]['magnitude'], '\n     ... Siemens fieldmap magnitude image %d present ' % (i), '\n     ... ERROR: Siemens fieldmap magnitude image %d missing!' % (i), status=fieldok)
                    r, fieldok = pc.checkForFile2(r, hcp['fieldmap'][i]['phase'], '\n     ... Siemens fieldmap phase image %d present ' % (i), '\n     ... ERROR: Siemens fieldmap phase image %d missing!' % (i), status=fieldok)
                    boldok = boldok and fieldok
                if not pc.is_number(options['hcp_bold_echospacing']):
                    fieldok = False
                    r += '\n     ... ERROR: hcp_bold_echospacing not defined correctly: "%s"!' % (options['hcp_bold_echospacing'])
                if not pc.is_number(options['hcp_bold_echodiff']):
                    fieldok = False
                    r += '\n     ... ERROR: hcp_bold_echodiff not defined correctly: "%s"!' % (options['hcp_bold_echodiff'])
                boldok = boldok and fieldok
                fmmag = hcp['fieldmap'][int(fmnum)]['magnitude']
                fmphase = hcp['fieldmap'][int(fmnum)]['phase']
                fmge = None

            # --- check for GE fieldmap image

            elif options['hcp_bold_dcmethod'].lower() in ['generalelectricfieldmap']:
                fmnum = boldinfo.get('fm', None)
                fieldok = True
                for i, v in hcp['fieldmap'].iteritems():
                    r, fieldok = pc.checkForFile2(r, hcp['fieldmap'][i]['GE'], '\n     ... GeneralElectric fieldmap image %d present ' % (i), '\n     ... ERROR: GeneralElectric fieldmap image %d missing!' % (i), status=fieldok)
                    boldok = boldok and fieldok
                fmmag = None
                fmphase = None
                fmge = hcp['fieldmap'][int(fmnum)]['GE']

            # --- check for Philips double TE-fieldmap image

            elif options['hcp_bold_dcmethod'].lower() in ['philipsfieldmap']:
                fmnum = boldinfo.get('fm', None)
                fieldok = True
                for i, v in hcp['fieldmap'].iteritems():
                    r, fieldok = pc.checkForFile2(r, hcp['fieldmap'][i]['magnitude'], '\n     ... Philips fieldmap magnitude image %d present ' % (i), '\n     ... ERROR: Philips fieldmap magnitude image %d missing!' % (i), status=fieldok)
                    r, fieldok = pc.checkForFile2(r, hcp['fieldmap'][i]['phase'], '\n     ... Philips fieldmap phase image %d present ' % (i), '\n     ... ERROR: Philips fieldmap phase image %d missing!' % (i), status=fieldok)
                    boldok = boldok and fieldok
                if not pc.is_number(options['hcp_bold_echospacing']):
                    fieldok = False
                    r += '\n     ... ERROR: hcp_bold_echospacing not defined correctly: "%s"!' % (options['hcp_bold_echospacing'])
                if not pc.is_number(options['hcp_bold_echodiff']):
                    fieldok = False
                    r += '\n     ... ERROR: hcp_bold_echodiff not defined correctly: "%s"!' % (options['hcp_bold_echodiff'])
                boldok = boldok and fieldok
                fmmag = hcp['fieldmap'][int(fmnum)]['magnitude']
                fmphase = hcp['fieldmap'][int(fmnum)]['phase']
                fmge = None

            # --- NO DC used

            elif options['hcp_bold_dcmethod'].lower() == 'none':
                r += '\n     ... No distortion correction used '
                if options['hcp_processing_mode'] == 'HCPStyleData':
                    r += "\n---> ERROR: The requested HCP processing mode is 'HCPStyleData', however, no distortion correction method was specified!\n            Consider using LegacyStyleData processing mode."
                    run = False

            # --- ERROR

            else:
                r += '\n     ... ERROR: Unknown distortion correction method: %s! Please check your settings!' % (options['hcp_bold_dcmethod'])
                boldok = False

            # --- set reference
            #
            # Need to make sure the right reference is used in relation to LR/RL AP/PA bolds
            # - have to keep track of whether an old topup in the same direction exists
            #

            # --- check for bold image

            if 'filename' in boldinfo and options['hcp_filename'] == 'original':
                boldroot = boldinfo['filename']
            else:
                boldroot = boldsource + orient

            boldimg = os.path.join(hcp['source'], "%s%s" % (boldroot, options['fctail']), "%s_%s.nii.gz" % (sinfo['id'], boldroot))
            r, boldok = pc.checkForFile2(r, boldimg, "\n     ... bold image present", "\n     ... ERROR: bold image missing [%s]!" % (boldimg), status=boldok)

            # --- check for ref image

            if options['hcp_bold_sbref'].lower() == 'use':
                refimg = os.path.join(hcp['source'], "%s_SBRef%s" % (boldroot, options['fctail']), "%s_%s_SBRef.nii.gz" % (sinfo['id'], boldroot))
                r, boldok = pc.checkForFile2(r, refimg, '\n     ... reference image present', '\n     ... ERROR: bold reference image missing!', status=boldok)
            else:
                r += "\n     ... reference image not used"

            # ---> Check the mask used
            if options['hcp_bold_mask']:
                if options['hcp_bold_mask'] != 'T1_fMRI_FOV' and options['hcp_processing_mode'] == 'HCPStyleData':
                    r += "\n---> ERROR: The requested HCP processing mode is 'HCPStyleData', however, %s was specified as bold mask to use!\n            Consider either using 'T1_fMRI_FOV' for the bold mask or LegacyStyleData processing mode."
                    run = False
                else:
                    r += '\n     ... using %s as BOLD mask' % (options['hcp_bold_mask'])
            else:
                r += '\n     ... using the HCPpipelines default BOLD mask'

            # --- set movement reference image

            fmriref = futureref
            if options['hcp_bold_movref'] == 'first':
                if futureref == "NONE":
                    futureref = boldtarget

            # --- are we using previous reference

            if fmriref is not "NONE":
                r += '\n     ... using %s as movement correction reference' % (fmriref)
                refimg = 'NONE'
                if options['hcp_processing_mode'] == 'HCPStyleData' and options['hcp_bold_refreg'] == 'nonlinear':
                    r += "\n---> ERROR: The requested HCP processing mode is 'HCPStyleData', however, a nonlinear registration to an external BOLD was specified!\n            Consider using LegacyStyleData processing mode."
                    run = False

            # store required data
            b = {'boldsource':   boldsource,
                 'boldtarget':   boldtarget,
                 'printbold':    printbold,
                 'run':          run,
                 'boldok':       boldok,
                 'boldimg':      boldimg,
                 'refimg':       refimg,
                 'gdcfile':      gdcfile,
                 'unwarpdir':    unwarpdir,
                 'echospacing':  echospacing,
                 'spinNeg':      spinNeg,
                 'spinPos':      spinPos,
                 'topupconfig':  topupconfig,
                 'fmmag':        fmmag,
                 'fmphase':      fmphase,
                 'fmge':         fmge,
                 'fmriref':      fmriref}
            boldsData.append(b)

        # --- Process
        r += "\n"

        parelements = max(1, min(options['parelements'], len(boldsData)))
        r += "\n%s %d BOLD images in parallel" % (pc.action("Running", options['run']), parelements)

        if (parelements == 1): # serial execution
            # loop over bolds
            for b in boldsData:
                # process
                result = executeHCPfMRIVolume(sinfo, options, overwrite, hcp, b)

                # merge r
                r += result['r']

                # merge report
                tempReport            = result['report']
                report['done']       += tempReport['done']
                report['incomplete'] += tempReport['incomplete']
                report['failed']     += tempReport['failed']
                report['ready']      += tempReport['ready']
                report['not ready']  += tempReport['not ready']
                report['skipped']    += tempReport['skipped']

        else: # parallel execution
            # if moveref equals first and seimage equals independent (complex scenario)
            if (options['hcp_bold_movref'] == 'first') and (options['hcp_bold_seimg'] == 'independent'):
                # loop over bolds to prepare processing pools
                boldsPool = []
                for b in boldsData:
                    fmriref = b['fmriref']
                    if (fmriref == "NONE"): # if fmriref is "NONE" then process the previous pool followed by this one as single
                        if (len(boldsPool) > 0):
                            r, report = executeMultipleHCPfMRIVolume(sinfo, options, overwrite, hcp, boldsPool, r, report)
                        boldsPool = []
                        r, report = executeSingleHCPfMRIVolume(sinfo, options, overwrite, hcp, b, r, report)
                    else: # else add to pool
                        boldsPool.append(b)

                # execute remaining pool
                r, report = executeMultipleHCPfMRIVolume(sinfo, options, overwrite, hcp, boldsPool, r, report)

            else:
                # if moveref equals first then process first one in serial
                if options['hcp_bold_movref'] == 'first':
                    # process first one
                    b = boldsData[0]
                    r, report = executeSingleHCPfMRIVolume(sinfo, options, overwrite, hcp, b, r, report)

                    # remove first one from array then process others in parallel
                    boldsData.pop(0)

                # process the rest in parallel
                r, report = executeMultipleHCPfMRIVolume(sinfo, options, overwrite, hcp, boldsData, r, report)

        rep = []
        for k in ['done', 'incomplete', 'failed', 'ready', 'not ready', 'skipped']:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (sinfo['id'], "HCP fMRI Volume: bolds " + "; ".join(rep), len(report['failed'] + report['incomplete'] + report['not ready']))

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        report = (sinfo['id'], 'HCP fMRI Volume failed', 1)
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        report = (sinfo['id'], 'HCP fMRI Volume failed', 1)

    r += "\n\nHCP fMRIVolume %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, report)

def executeSingleHCPfMRIVolume(sinfo, options, overwrite, hcp, b, r, report):
    # process
    result = executeHCPfMRIVolume(sinfo, options, overwrite, hcp, b)

    # merge r
    r += result['r']

    # merge report
    tempReport            = result['report']
    report['done']       += tempReport['done']
    report['incomplete'] += tempReport['incomplete']
    report['failed']     += tempReport['failed']
    report['ready']      += tempReport['ready']
    report['not ready']  += tempReport['not ready']
    report['skipped']    += tempReport['skipped']

    return r, report

def executeMultipleHCPfMRIVolume(sinfo, options, overwrite, hcp, boldsData, r, report):
    # parelements
    parelements = max(1, min(options['parelements'], len(boldsData)))

    # create a multiprocessing Pool
    processPoolExecutor = ProcessPoolExecutor(parelements)

    # partial function
    f = partial(executeHCPfMRIVolume, sinfo, options, overwrite, hcp)
    results = processPoolExecutor.map(f, boldsData)

    # merge r and report
    for result in results:
        r += result['r']
        tempReport            = result['report']
        report['done']       += tempReport['done']
        report['incomplete'] += tempReport['incomplete']
        report['failed']     += tempReport['failed']
        report['ready']      += tempReport['ready']
        report['not ready']  += tempReport['not ready']
        report['skipped']    += tempReport['skipped']

    return r, report

def executeHCPfMRIVolume(sinfo, options, overwrite, hcp, b):
    # extract data
    boldsource  = b['boldsource']
    boldtarget  = b['boldtarget']
    printbold   = b['printbold']
    gdcfile     = b['gdcfile']
    run         = b['run']
    boldok      = b['boldok']
    boldimg     = b['boldimg']
    refimg      = b['refimg']
    unwarpdir   = b['unwarpdir']
    echospacing = b['echospacing']
    spinNeg     = b['spinNeg']
    spinPos     = b['spinPos']
    topupconfig = b['topupconfig']
    fmmag       = b['fmmag']
    fmphase     = b['fmphase']
    fmge        = b['fmge']
    fmriref     = b['fmriref']

    # prepare return variables
    r = ""
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:

        # --- process additional parameters

        slicetimerparams = ""

        if options['hcp_bold_doslicetime'].lower() == 'true':

            slicetimerparams = re.split(' +|,|\|', options['hcp_bold_slicetimerparams'])

            stappendItems = []
            if options['hcp_bold_stcorrdir'] == 'down':
                stappendItems.append('--down')
            if options['hcp_bold_stcorrint'] == 'odd':
                stappendItems.append('--odd')

            for stappend in stappendItems:
                if stappend not in slicetimerparams:
                    slicetimerparams.append(stappend)

            slicetimerparams = [e for e in slicetimerparams if e]
            slicetimerparams = "@".join(slicetimerparams)

        # --- Set up the command

        if fmriref == 'NONE':
            fmrirefparam = ""
        else:
            fmrirefparam = fmriref

        comm = os.path.join(hcp['hcp_base'], 'fMRIVolume', 'GenericfMRIVolumeProcessingPipeline.sh') + " "

        print("=======================================================================================================================================")
        elements = [("path",                sinfo['hcp']),
                    ("subject",             sinfo['id'] + options['hcp_suffix']),
                    ("fmriname",            boldtarget),
                    ("fmritcs",             boldimg),
                    ("fmriscout",           refimg),
                    ("SEPhaseNeg",          spinNeg),
                    ("SEPhasePos",          spinPos),
                    ("fmapmag",             fmmag),
                    ("fmapphase",           fmphase),
                    ("fmapgeneralelectric", fmge),
                    ("echospacing",         echospacing),
                    ("echodiff",            options['hcp_bold_echodiff']),
                    ("unwarpdir",           unwarpdir),
                    ("fmrires",             options['hcp_bold_res']),
                    ("dcmethod",            options['hcp_bold_dcmethod']),
                    ("biascorrection",      options['hcp_bold_biascorrection']),
                    ("gdcoeffs",            gdcfile),
                    ("topupconfig",         topupconfig),
                    ("dof",                 options['hcp_bold_dof']),
                    ("printcom",            options['hcp_printcom']),
                    ("usejacobian",         options['hcp_bold_usejacobian']),
                    ("mctype",              options['hcp_bold_movreg'].upper()),
                    ("preregistertool",     options['hcp_bold_preregistertool']),
                    ("processing-mode",     options['hcp_processing_mode']),
                    ("doslicetime",         options['hcp_bold_doslicetime'].upper()),
                    ("slicetimerparams",    slicetimerparams),
                    ("fmriref",             fmrirefparam),
                    ("fmrirefreg",          options['hcp_bold_refreg']),
                    ("boldmask",            options['hcp_bold_mask'])]

        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])

        # -- Report command
        if boldok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test files

        if False:   # Longitudinal option currently not supported options['hcp_fs_longitudinal']:
            tfile = os.path.join(hcp['hcp_long_nonlin'], 'Results', "%s_%s" % (boldtarget, options['hcp_fs_longitudinal']), "%s%d_%s.nii.gz" % (options['hcp_bold_prefix'], boldtarget, options['hcp_fs_longitudinal']))
        else:
            tfile = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s.nii.gz" % (boldtarget))

        if hcp['hcp_bold_vol_check']:
            fullTest = {'tfolder': hcp['base'], 'tfile': hcp['hcp_bold_vol_check'], 'fields': [('sessionid', sinfo['id'] + options['hcp_suffix']), ('scan', boldtarget)], 'specfolder': options['specfolder']}
        else:
            fullTest = None

        # -- Run

        if run and boldok:
            if options['run'] == "run":
                if overwrite or not os.path.exists(tfile):

                    # ---> Clean up existing data
                    # -> bold working folder
                    bold_folder = os.path.join(hcp['base'], boldtarget)
                    if os.path.exists(bold_folder):
                        r += "\n     ... removing preexisting working bold folder [%s]" % (bold_folder)
                        shutil.rmtree(bold_folder)

                    # -> bold MNINonLinear results folder
                    bold_folder = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget)
                    if os.path.exists(bold_folder):
                        r += "\n     ... removing preexisting MNINonLinar results bold folder [%s]" % (bold_folder)
                        shutil.rmtree(bold_folder)

                    # -> bold T1w results folder
                    bold_folder = os.path.join(hcp['T1w_folder'], 'Results', boldtarget)
                    if os.path.exists(bold_folder):
                        r += "\n     ... removing preexisting T1w results bold folder [%s]" % (bold_folder)
                        shutil.rmtree(bold_folder)

                    # -> xfms in T1w folder
                    xfms_file = os.path.join(hcp['T1w_folder'], 'xfms', "%s2str.nii.gz" % (boldtarget))
                    if os.path.exists(xfms_file):
                        r += "\n     ... removing preexisting xfms file [%s]" % (xfms_file)
                        os.remove(xfms_file)

                    # -> xfms in MNINonLinear folder
                    xfms_file = os.path.join(hcp['hcp_nonlin'], 'xfms', "%s2str.nii.gz" % (boldtarget))
                    if os.path.exists(xfms_file):
                        r += "\n     ... removing preexisting xfms file [%s]" % (xfms_file)
                        os.remove(xfms_file)

                    # -> xfms in MNINonLinear folder
                    xfms_file = os.path.join(hcp['hcp_nonlin'], 'xfms', "standard2%s.nii.gz" % (boldtarget))
                    if os.path.exists(xfms_file):
                        r += "\n     ... removing preexisting xfms file [%s]" % (xfms_file)
                        os.remove(xfms_file)

                r, endlog, _, failed = pc.runExternalForFile(tfile, comm, 'Running HCP fMRIVolume', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=[options['logtag'], boldtarget], fullTest=fullTest, shell=True, r=r)

                if failed:
                    report['failed'].append(printbold)
                else:
                    report['done'].append(printbold)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(tfile, fullTest, 'HCP fMRIVolume ' + boldtarget, r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP fMRIVolume can be run"
                    report['ready'].append(printbold)
                else:
                    report['skipped'].append(printbold)

        elif run:
            report['not ready'].append(printbold)
            if options['run'] == "run":
                r += "\n---> ERROR: images or data parameters missing, skipping this BOLD!"
            else:
                r += "\n---> ERROR: images or data parameters missing, this BOLD would be skipped!"
        else:
            report['not ready'].append(printbold)
            if options['run'] == "run":
                r += "\n---> ERROR: No hcp info for session, skipping this BOLD!"
            else:
                r += "\n---> ERROR: No hcp info for session, this BOLD would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = "\n\n\n --- Failed during processing of bold %s with error:\n" % (printbold)
        r += str(errormessage)
        report['failed'].append(printbold)
    except:
        r += "\n --- Failed during processing of bold %s with error:\n %s\n" % (printbold, traceback.format_exc())
        report['failed'].append(printbold)

    return {'r': r, 'report': report}


def hcp_fmri_surface(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_fmri_surface [... processing options]``

    Runs the fMRI Surface step of HCP Pipeline.

    REQUIREMENTS
    ============

    The code expects all the previous HCP preprocessing steps (hcp_pre_freesurfer,
    hcp_freesurfer, hcp_post_freesurfer, hcp_fmri_volume) to have been run and finished
    successfully. The command will test for presence of key files but do note
    that it won't run a thorough check for all the required files.

    INPUTS
    ======

    General parameters
    ------------------

    When running the command, the following *general* processing parameters are
    taken into account:

    --sessions              The batch.txt file with all the sessions information.
                            [batch.txt]
    --sessionsfolder        The path to the study/sessions folder, where the
                            imaging data is supposed to go. [.]
    --parsessions           How many sessions to run in parallel. [1]
    --parelements           How many elements (e.g bolds) to run in parallel.
                            [1]
    --bolds                 Which bold images (as they are specified in the
                            batch.txt file) to process. It can be a single
                            type (e.g. 'task'), a pipe separated list (e.g.
                            'WM|Control|rest') or 'all' to process all [all].
    --overwrite             Whether to overwrite existing data (yes) or not (no).
                            [no]
    --hcp_suffix            Specifies a suffix to the session id if multiple
                            variants are run, empty otherwise. []
    --logfolder             The path to the folder where runlogs and comlogs
                            are to be stored, if other than default. []
    --log                   Whether to keep ('keep') or remove ('remove') the
                            temporary logs once jobs are completed. ['keep']
                            When a comma or pipe ('|') separated list is given,
                            the log will be created at the first provided
                            location and then linked or copied to other
                            locations. The valid locations are:

                            - 'study' (for the default:
                              `<study>/processing/logs/comlogs` location)
                            - 'session' (for `<sessionid>/logs/comlogs`)
                            - 'hcp' (for `<hcp_folder>/logs/comlogs`)
                            - '<path>' (for an arbitrary directory)

    --hcp_folderstructure   Specifies the version of the folder structure to use,
                            initial' and 'hcpls' are supported. ['hcpls']
    --hcp_filename          Specifies whether the standard ('standar
                            filenames or the specified original names
                            ('original') are to be used. ['standard']

    In addition a number of *specific* parameters can be used to guide the
    processing in this step:

    Use of FS longitudinal template
    -------------------------------

    --hcp_fs_longitudinal      (*) The name of the FS longitudinal template if
                               one was created and is to be used in this step.

    (*) This parameter is currently not in use

    Naming options
    --------------

    --hcp_bold_prefix       The prefix to use when generating BOLD names 
                            (see 'hcp_filename') for BOLD working folders 
                            and results. [BOLD]

    Grayordinate image mapping details
    ----------------------------------

    --hcp_lowresmesh             The number of vertices to be used in the
                                 low-resolution grayordinate mesh
                                 (in thousands). [32]
    --hcp_bold_res               The resolution of the BOLD volume data in mm.
                                 [2]
    --hcp_grayordinatesres       The size of voxels for the subcortical and
                                 cerebellar data in grayordinate space in mm.
                                 [2]
    --hcp_bold_smoothFWHM        The size of the smoothing kernel (in mm). [2]
    --hcp_regname                The name of the registration used. [MSMSulc]

    OUTPUTS
    =======

    The results of this step will be present in the MNINonLinear folder in the
    sessions's root hcp folder. In case a longitudinal FS template is used, the
    results will be stored in a `MNINonlinear_<FS longitudinal template name>`
    folder::

        study
        └─ sessions
           └─ session1_session1
              └─ hcp
                 └─ subject1_session1
                   ├─ MNINonlinear
                   │  └─ Results
                   │     └─ BOLD_1
                   └─ MNINonlinear_TemplateA
                      └─ Results
                         └─ BOLD_1

    USE
    ===

    Runs the fMRI Surface step of HCP Pipeline. It uses the FreeSurfer
    segmentation and surface reconstruction to map BOLD timeseries to
    grayordinate representation and generates .dtseries.nii files.

    EXAMPLE USE
    ===========

    ::

        qunex hcp_fmri_surface sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no parsessions=10

    ::

        qunex hcp_fmri_surface sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no parsessions=10
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP fMRI Surface registration [%s] ..." % (pc.action("Running", options['run']), options['hcp_processing_mode'])

    run    = True
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:

        # --- Base settings

        pc.doOptionsCheck(options, sinfo, 'hcp_fmri_surface')
        doHCPOptionsCheck(options, sinfo, 'hcp_fmri_surface')
        hcp = getHCPPaths(sinfo, options)

        # --- bold filtering not yet supported!
        # btargets = options['bolds'].split("|")

        # --- run checks

        if 'hcp' not in sinfo:
            r += "\n---> ERROR: There is no hcp info for session %s in batch.txt" % (sinfo['id'])
            run = False

        # -> PostFS results

        if options['hcp_fs_longitudinal']:
            tfile = os.path.join(hcp['hcp_long_nonlin'], 'fsaverage_LR32k', sinfo['id'] + options['hcp_suffix'] + '.long.' + options['hcp_fs_longitudinal'] + '.32k_fs_LR.wb.spec')
        else:
            tfile = os.path.join(hcp['hcp_nonlin'], 'fsaverage_LR32k', sinfo['id'] + options['hcp_suffix'] + '.32k_fs_LR.wb.spec')

        if os.path.exists(tfile):
            r += "\n---> PostFS results present."
        else:
            r += "\n---> ERROR: Could not find PostFS processing results."
            if options['hcp_fs_longitudinal']:
                r += "\n--->        Please check that you have run PostFS on FS longitudinal as specified,"
                r += "\n--->        and that %s template was successfully used." % (options['hcp_fs_longitudinal'])
            run = False

        # --- Get sorted bold numbers

        bolds, bskip, report['boldskipped'], r = pc.useOrSkipBOLD(sinfo, options, r)
        if report['boldskipped']:
            if options['hcp_filename'] == 'original':
                report['skipped'] = [bi.get('filename', str(bn)) for bn, bnm, bt, bi in bskip]
            else:
                report['skipped'] = [str(bn) for bn, bnm, bt, bi in bskip]

        parelements = max(1, min(options['parelements'], len(bolds)))
        r += "\n%s %d BOLD images in parallel" % (pc.action("Running", options['run']), parelements)

        if parelements == 1: # serial execution
            for b in bolds:
                # process
                result = executeHCPfMRISurface(sinfo, options, overwrite, hcp, run, b)

                # merge r
                r += result['r']

                # merge report
                tempReport            = result['report']
                report['done']       += tempReport['done']
                report['incomplete'] += tempReport['incomplete']
                report['failed']     += tempReport['failed']
                report['ready']      += tempReport['ready']
                report['not ready']  += tempReport['not ready']
                report['skipped']    += tempReport['skipped']

        else: # parallel execution
            # create a multiprocessing Pool
            processPoolExecutor = ProcessPoolExecutor(parelements)
            # process
            f = partial(executeHCPfMRISurface, sinfo, options, overwrite, hcp, run)
            results = processPoolExecutor.map(f, bolds)

            # merge r and report
            for result in results:
                r                    += result['r']
                tempReport            = result['report']
                report['done']       += tempReport['done']
                report['failed']     += tempReport['failed']
                report['incomplete'] += tempReport['incomplete']
                report['ready']      += tempReport['ready']
                report['not ready']  += tempReport['not ready']
                report['skipped']    += tempReport['skipped']

        rep = []
        for k in ['done', 'incomplete', 'failed', 'ready', 'not ready', 'skipped']:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (sinfo['id'], "HCP fMRI Surface: bolds " + "; ".join(rep), len(report['failed'] + report['incomplete'] + report['not ready']))

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        report = (sinfo['id'], 'HCP fMRI Surface failed')
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        report = (sinfo['id'], 'HCP fMRI Surface failed')

    r += "\n\nHCP fMRISurface %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, report)


def executeHCPfMRISurface(sinfo, options, overwrite, hcp, run, boldData):
    # extract data
    bold, boldname, task, boldinfo = boldData

    if 'filename' in boldinfo and options['hcp_filename'] == 'original':
        printbold  = boldinfo['filename']
        boldsource = boldinfo['filename']
        boldtarget = boldinfo['filename']
    else:
        printbold  = str(bold)
        boldsource = 'BOLD_%d' % (bold)
        boldtarget = "%s%s" % (options['hcp_bold_prefix'], printbold)

    # prepare return variables
    r = ""
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        r += "\n\n---> %s BOLD image %s" % (pc.action("Processing", options['run']), printbold)
        boldok = True

        # --- check for bold image
        boldimg = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s.nii.gz" % (boldtarget))
        r, boldok = pc.checkForFile2(r, boldimg, '\n     ... fMRIVolume preprocessed bold image present', '\n     ... ERROR: fMRIVolume preprocessed bold image missing!', status=boldok)

        # --- Set up the command

        comm = os.path.join(hcp['hcp_base'], 'fMRISurface', 'GenericfMRISurfaceProcessingPipeline.sh') + " "

        elements = [('path',              sinfo['hcp']),
                    ('subject',           sinfo['id'] + options['hcp_suffix']),
                    ('fmriname',          boldtarget),
                    ('lowresmesh',        options['hcp_lowresmesh']),
                    ('fmrires',           options['hcp_bold_res']),
                    ('smoothingFWHM',     options['hcp_bold_smoothFWHM']),
                    ('grayordinatesres',  options['hcp_grayordinatesres']),
                    ('regname',           options['hcp_regname']),
                    ('printcom',          options['hcp_printcom'])]

        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])

        # -- Report command
        if boldok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test files

        if False:   # Longitudinal option currently not supported options['hcp_fs_longitudinal']:
            tfile = os.path.join(hcp['hcp_long_nonlin'], 'Results', "%s_%s" % (boldtarget, options['hcp_fs_longitudinal']), "%s_%s%s.dtseries.nii" % (boldtarget, options['hcp_fs_longitudinal'], options['hcp_cifti_tail']))
        else:
            tfile = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s%s.dtseries.nii" % (boldtarget, options['hcp_cifti_tail']))

        if hcp['hcp_bold_surf_check']:
            fullTest = {'tfolder': hcp['base'], 'tfile': hcp['hcp_bold_surf_check'], 'fields': [('sessionid', sinfo['id'] + options['hcp_suffix']), ('scan', boldtarget)], 'specfolder': options['specfolder']}
        else:
            fullTest = None

        # -- Run

        if run and boldok:
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, endlog, _, failed = pc.runExternalForFile(tfile, comm, 'Running HCP fMRISurface', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=[options['logtag'], boldtarget], fullTest=fullTest, shell=True, r=r)

                if failed:
                    report['failed'].append(printbold)
                else:
                    report['done'].append(printbold)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(tfile, fullTest, 'HCP fMRISurface ' + boldtarget, r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP fMRISurface can be run"
                    report['ready'].append(printbold)
                else:
                    report['skipped'].append(printbold)

        elif run:
            report['not ready'].append(printbold)
            if options['run'] == "run":
                r += "\n---> ERROR: images missing, skipping this BOLD!"
            else:
                r += "\n---> ERROR: images missing, this BOLD would be skipped!"
        else:
            report['not ready'].append(printbold)
            if options['run'] == "run":
                r += "\n---> ERROR: No hcp info for session, skipping this BOLD!"
            else:
                r += "\n---> ERROR: No hcp info for session, this BOLD would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = "\n\n\n --- Failed during processing of bold %s with error:\n" % (printbold)
        r += str(errormessage)
        report['failed'].append(printbold)
    except:
        r += "\n --- Failed during processing of bold %s with error:\n %s\n" % (printbold, traceback.format_exc())
        report['failed'].append(printbold)

    return {'r': r, 'report': report}


def parseICAFixBolds(options, bolds, r, msmall=False):
    # --- Use hcp_icafix parameter to determine if a single fix or a multi fix should be used
    singleFix = True

    # variable for storing groups and their bolds
    hcpGroups = {}

    # variable for storing erroneously specified bolds
    boldError = []

    # flag that all is OK
    boldsOK= True

    # get all bold targets and tags
    boldtargets = []
    boldtags = []

    for b in bolds:
        # extract data
        printbold, _, _, boldinfo = b

        if 'filename' in boldinfo and options['hcp_filename'] == 'original':
            boldtarget = boldinfo['filename']
            boldtag = boldinfo['task']
        else:
            printbold = str(printbold)
            boldtarget = "%s%s" % (options['hcp_bold_prefix'], printbold)
            boldtag = boldinfo['task']

        boldtargets.append(boldtarget)
        boldtags.append(boldtag)

    hcpBolds = None
    if options['hcp_icafix_bolds'] is not None:
        hcpBolds = options['hcp_icafix_bolds']

    if hcpBolds:
        # if hcpBolds includes : then we have groups and we need multi fix
        if ":" in hcpBolds:
            # run multi fix
            singleFix = False

            # get all groups
            groups = str.split(hcpBolds, "|")

            # store all bolds in hcpBolds
            hcpBolds = []

            for g in groups:
                # get group name
                split = str.split(g, ":")

                # create group and add to dictionary
                if split[0] not in hcpGroups:
                    specifiedBolds = str.split(split[1], ",")
                    groupBolds = []

                    # iterate over all and add to bolds or inject instead of tags
                    for sb in specifiedBolds:
                        if sb not in boldtargets and sb not in boldtags:
                            boldError.append(sb)
                        else:
                            # counter
                            i = 0

                            for b in boldtargets:
                                if sb == boldtargets[i] or sb == boldtags[i]:
                                    if sb in hcpBolds:
                                        boldsOK = False
                                        r += "\n\nERROR: the bold [%s] is specified twice!" % b
                                    else:
                                        groupBolds.append(b)
                                        hcpBolds.append(b)

                                # increase counter
                                i = i + 1

                    hcpGroups[split[0]] = groupBolds
                else:
                    boldsOK = False
                    r += "\n\nERROR: multiple concatenations with the same name [%s]!" % split[0]

        # else we extract bolds and use single fix
        else:
            # specified bolds
            specifiedBolds = str.split(hcpBolds, ",")

            # variable for storing bolds
            hcpBolds = []

            # iterate over all and add to bolds or inject instead of tags
            for sb in specifiedBolds:
                if sb not in boldtargets and sb not in boldtags:
                    boldError.append(sb)
                else:
                    # counter
                    i = 0

                    for b in boldtargets:
                        if sb == boldtargets[i] or sb == boldtags[i]:
                            if sb in hcpBolds:
                                boldsOK = False
                                r += "\n\nERROR: the bold [%s] is specified twice!" % b
                            else:
                                hcpBolds.append(b)

                        # increase counter
                        i = i + 1

    # if hcp_icafix is empty then bundle all bolds
    else:
        # run multi fix
        singleFix = False
        hcpBolds = bolds
        hcpGroups = []
        hcpGroups.append({"name":"fMRI_CONCAT_ALL", "bolds":hcpBolds})

        # create specified bolds
        specifiedBolds = boldtargets

        r += "\nConcatenating all bolds\n"

    # --- Get hcp_icafix data from bolds
    # variable for storing skipped bolds
    boldSkip = []

    if hcpBolds is not bolds:
        # compare
        r += "\n\nComparing bolds with those specifed via parameters\n"

        # single fix
        if singleFix:
            # variable for storing bold data
            boldData = []

            # add data to list
            for b in hcpBolds:
                # get index
                i = boldtargets.index(b)

                # store data
                if b in boldtargets:
                    boldData.append(bolds[i])

            # skipped bolds
            for b in boldtargets:
                if b not in hcpBolds:
                    boldSkip.append(b)

            # store data into the hcpBolds variable
            hcpBolds = boldData

        # multi fix
        else:
            # variable for storing group data
            groupData = {}

            # variable for storing skipped bolds
            boldSkipDict = {}
            for b in boldtargets:
                boldSkipDict[b] = True

            # go over all groups
            for g in hcpGroups:
                # create empty dict entry for group
                groupData[g] = []

                # go over group bolds
                groupBolds = hcpGroups[g]

                # add data to list
                for b in groupBolds:
                    # get index
                    i = boldtargets.index(b)

                    # store data
                    if b in boldtargets:
                        groupData[g].append(bolds[i])

                # find skipped bolds
                for i in range(len(boldtargets)):
                    # bold is defined
                    if boldtargets[i] in groupBolds:
                        # append

                        boldSkipDict[boldtargets[i]] = False

            # cast boldSkip from dictionary to array
            for b in boldtargets:
                if boldSkipDict[b]:
                    boldSkip.append(b)

            # cast group data to array of dictionaries (needed for parallel)
            hcpGroups = []
            for g in groupData:
                hcpGroups.append({"name":g, "bolds":groupData[g]})

    # report that some hcp_icafix_bolds not found in bolds
    if len(boldSkip) > 0 or len(boldError) > 0:
        for b in boldSkip:
            r += "     ... skipping %s: it is not specified in hcp_icafix_bolds\n" % b
        for b in boldError:
            r += "     ... ERROR: %s specified in hcp_icafix_bolds but not found in bolds\n" % b
    else:
        r += "     ... all bolds specified via hcp_icafix_bolds are present\n"

    if (len(boldError) > 0):
        boldsOK = False

    # --- Report single fix or multi fix
    if singleFix:
        r += "\nSingle-run HCP ICAFix on %d bolds" % len(hcpBolds)
    else:
        r += "\nMulti-run HCP ICAFix on %d groups" % len(hcpGroups)

    # different output for msmall and singlefix
    if msmall and singleFix:
        # single group
        hcpGroups = []
        icafixGroup = {}
        icafixGroup["bolds"] = hcpBolds
        hcpGroups.append(icafixGroup)

        # bolds
        hcpBolds = specifiedBolds
    elif options['hcp_icafix_bolds'] is None:
        # bolds
        hcpBolds = specifiedBolds

    return (singleFix, hcpBolds, hcpGroups, boldsOK, r)


def hcp_icafix(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_icafix [... processing options]``

    Runs the ICAFix step of HCP Pipeline.

    REQUIREMENTS
    ============

    The code expects the input images to be named and present in the QuNex
    folder structure. The function will look into folder::

        <session id>/hcp/<session id>

    for files::

        MNINonLinear/Results/<boldname>/<boldname>.nii.gz

    INPUTS
    ======

    General parameters
    ------------------

    --sessions              The batch.txt file with all the sessions
                            information. [batch.txt]
    --sessionsfolder        The path to the study/sessions folder, where the
                            imaging  data is supposed to go. [.]
    --parsessions           How many sessions to run in parallel. [1]
    --parelements           How many elements (e.g bolds) to run in
                            parralel. [1]
    --overwrite             Whether to overwrite existing data (yes)
                            or not (no). [no]
    --hcp_suffix            Specifies a suffix to the session id if multiple
                            variants are run, empty otherwise. []
    --logfolder             The path to the folder where runlogs and comlogs
                            are to be stored, if other than default []
    --log                   Whether to keep ('keep') or remove ('remove') the
                            temporary logs once jobs are completed ['keep'].
                            When a comma or pipe ('|') separated list is given,
                            the log will be created at the first provided
                            location and then linked or copied to other
                            locations. The valid locations are:

                            - 'study' (for the default:
                              `<study>/processing/logs/comlogs` location)
                            - 'session' (for `<sessionid>/logs/comlogs`)
                            - 'hcp' (for `<hcp_folder>/logs/comlogs`)
                            - '<path>' (for an arbitrary directory)

    Specific parameters
    -------------------

    In addition the following *specific* parameters will be used to guide the
    processing in this step:

    --hcp_icafix_bolds                    Specify a list of bolds for ICAFix.
                                          You can specify a comma separated list
                                          of bolds, e.g.
                                          "<boldname1>,<boldname2>", in this
                                          case single-run HCP ICAFix will be
                                          executed over specified bolds. You can
                                          also specify how to group/concatenate
                                          bolds together, e.g.
                                          "<group1>:<boldname1>,<boldname2>|
                                          <group2>:<boldname3>,<boldname4>",
                                          in this case multi-run HCP ICAFix will
                                          be executed. Instead of full bold
                                          names, you can also use bold tags from
                                          the batch file. If this parameter is
                                          not provided ICAFix will bundle all
                                          bolds together and execute multi-run
                                          HCP ICAFix, the concatenated file will
                                          be named fMRI_CONCAT_ALL. []
    --hcp_icafix_highpass                 Value for the highpass filter,
                                          [0] for multi-run HCP ICAFix and
                                          [2000] for single-run HCP ICAFix.
    --hcp_matlab_mode                     Specifies the Matlab version, can be
                                          interpreted, compiled or octave.
                                          [compiled]
    --hcp_icafix_domotionreg              Whether to regress motion parameters
                                          as part of the cleaning. The default
                                          value for single-run HCP ICAFix is
                                          [TRUE], while the default for
                                          multi-run HCP ICAFix is [FALSE].
    --hcp_icafix_traindata                Which file to use for training data.
                                          You can provide a full path to a file
                                          or just a filename if the file is in
                                          the ${FSL_FIXDIR}/training_files
                                          folder. [] for single-run HCP ICAFix
                                          and
                                          [HCP_Style_Single_Multirun_Dedrift.RData]
                                          for multi-run HCP ICAFix.
    --hcp_icafix_threshold                ICAFix threshold that controls the
                                          sensitivity/specificity tradeoff. [10]
    --hcp_icafix_deleteintermediates      If TRUE, deletes both the concatenated
                                          high-pass filtered and non-filtered
                                          timeseries files that are
                                          prerequisites to FIX cleaning. [FALSE]
    --hcp_icafix_postfix                  Whether to automatically run HCP
                                          PostFix if HCP ICAFix finishes
                                          successfully. [TRUE]

    OUTPUTS
    =======

    The results of this step will be generated and populated in the
    MNINonLinear folder inside the same sessions's root hcp folder.

    The final clean ICA file can be found in::

        MNINonLinear/Results/<boldname>/<boldname>_hp<highpass>_clean.nii.gz,

    where highpass is the used value for the highpass filter. The default
    highpass value is 0 for multi-run HCP ICAFix and 2000 for single-run HCP
    ICAFix .

    USE
    ===

    Runs the ICAFix step of HCP Pipeline. This step attempts to auto-classify
    ICA components into good and bad components, so that the bad components
    can be then removed from the 4D FMRI data. If ICAFix step finishes
    successfully PostFix step will execute automatically, to disable this
    set the hcp_icafix_postfix to FALSE.

    If the hcp_icafix_bolds parameter is not provided ICAFix will bundle
    all bolds together and execute multi-run HCP ICAFix, the concatenated file
    will be named fMRI_CONCAT_ALL. WARNING: if session has many bolds such
    processing requires a lot of computational resources.

    EXAMPLE USE
    ===========

    ::

        qunex hcp_icafix \\
            --sessions=processing/batch.txt \\
            --sessionsfolder=sessions


    ::

        qunex hcp_icafix \\
            --sessions=processing/batch.txt \\
            --sessionsfolder=sessions \\
            --hcp_icafix_bolds="GROUP_1:BOLD_1,BOLD_2|GROUP_2:BOLD_3,BOLD_4"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP ICAFix registration [%s] ..." % (pc.action("Running", options['run']), options['hcp_processing_mode'])

    run    = True
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, 'hcp_icafix')
        doHCPOptionsCheck(options, sinfo, 'hcp_icafix')
        hcp = getHCPPaths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report['boldskipped'], r = pc.useOrSkipBOLD(sinfo, options, r)
        if report['boldskipped']:
            if options['hcp_filename'] == 'original':
                report['skipped'] = [bi.get('filename', str(bn)) for bn, bnm, bt, bi in bskip]
            else:
                report['skipped'] = [str(bn) for bn, bnm, bt, bi in bskip]

        # --- Parse icafix_bolds
        singleFix, icafixBolds, icafixGroups, parsOK, r = parseICAFixBolds(options, bolds, r)

        # --- Multi threading
        if singleFix:
            parelements = max(1, min(options['parelements'], len(icafixBolds)))
        else:
            parelements = max(1, min(options['parelements'], len(icafixGroups)))
        r += "\n\n%s %d ICAFix images in parallel" % (pc.action("Processing", options['run']), parelements)

        # matlab run mode, compiled=0, interpreted=1, octave=2
        if options['hcp_matlab_mode'] == "compiled":
            matlabrunmode = "0"
        elif options['hcp_matlab_mode'] == "interpreted":
            matlabrunmode = "1"
        elif options['hcp_matlab_mode'] == "octave":
            r += "\nWARNING: ICAFix runs with octave results are unstable!\n"
            matlabrunmode = "2"
        else:
            parsOK = False

        # set variable
        os.environ["FSL_FIX_MATLAB_MODE"] = matlabrunmode

        if not parsOK:
            raise ge.CommandFailed("hcp_icafix", "... invalid input parameters!")

        # --- Execute
        # single fix
        if singleFix:
            if parelements == 1: # serial execution
                for b in icafixBolds:
                    # process
                    result = executeHCPSingleICAFix(sinfo, options, overwrite, hcp, run, b)

                    # merge r
                    r += result['r']

                    # merge report
                    tempReport            = result['report']
                    report['done']       += tempReport['done']
                    report['incomplete'] += tempReport['incomplete']
                    report['failed']     += tempReport['failed']
                    report['ready']      += tempReport['ready']
                    report['not ready']  += tempReport['not ready']
                    report['skipped']    += tempReport['skipped']

            else: # parallel execution
                # create a multiprocessing Pool
                processPoolExecutor = ProcessPoolExecutor(parelements)
                # process
                f = partial(executeHCPSingleICAFix, sinfo, options, overwrite, hcp, run)
                results = processPoolExecutor.map(f, icafixBolds)

                # merge r and report
                for result in results:
                    r                    += result['r']
                    tempReport            = result['report']
                    report['done']       += tempReport['done']
                    report['failed']     += tempReport['failed']
                    report['incomplete'] += tempReport['incomplete']
                    report['ready']      += tempReport['ready']
                    report['not ready']  += tempReport['not ready']
                    report['skipped']    += tempReport['skipped']

        # multi fix
        else:
            if parelements == 1: # serial execution
                for g in icafixGroups:
                    # process
                    result = executeHCPMultiICAFix(sinfo, options, overwrite, hcp, run, g)

                    # merge r
                    r += result['r']

                    # merge report
                    tempReport            = result['report']
                    report['done']       += tempReport['done']
                    report['incomplete'] += tempReport['incomplete']
                    report['failed']     += tempReport['failed']
                    report['ready']      += tempReport['ready']
                    report['not ready']  += tempReport['not ready']
                    report['skipped']    += tempReport['skipped']

            else: # parallel execution
                # create a multiprocessing Pool
                processPoolExecutor = ProcessPoolExecutor(parelements)
                # process
                f = partial(executeHCPMultiICAFix, sinfo, options, overwrite, hcp, run)
                results = processPoolExecutor.map(f, icafixGroups)

                # merge r and report
                for result in results:
                    r                    += result['r']
                    tempReport            = result['report']
                    report['done']       += tempReport['done']
                    report['failed']     += tempReport['failed']
                    report['incomplete'] += tempReport['incomplete']
                    report['ready']      += tempReport['ready']
                    report['not ready']  += tempReport['not ready']
                    report['skipped']    += tempReport['skipped']

        # report
        rep = []
        for k in ['done', 'incomplete', 'failed', 'ready', 'not ready', 'skipped']:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (sinfo['id'], "HCP ICAFix: bolds " + "; ".join(rep), len(report['failed'] + report['incomplete'] + report['not ready']))

    except ge.CommandFailed as e:
        r +=  "\n\nERROR in completing %s:\n     %s\n" % (e.function, "\n     ".join(e.report))
        report = (sinfo['id'], 'HCP ICAFix failed')
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        report = (sinfo['id'], 'HCP ICAFix failed')
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        report = (sinfo['id'], 'HCP ICAFix failed')

    r += "\n\nHCP ICAFix %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, report)


def executeHCPSingleICAFix(sinfo, options, overwrite, hcp, run, bold):
    # extract data
    printbold, _, _, boldinfo = bold

    if 'filename' in boldinfo and options['hcp_filename'] == 'original':
        printbold  = boldinfo['filename']
        boldtarget = boldinfo['filename']
    else:
        printbold = str(printbold)
        boldtarget = "%s%s" % (options['hcp_bold_prefix'], printbold)

    # prepare return variables
    r = ""
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        r += "\n\n------------------------------------------------------------"
        r += "\n---> %s BOLD image %s" % (pc.action("Processing", options['run']), printbold)
        boldok = True

        # --- check for bold image
        boldimg = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s.nii.gz" % (boldtarget))
        r, boldok = pc.checkForFile2(r, boldimg, '\n     ... bold image %s present' % boldtarget, '\n     ... ERROR: bold image [%s] missing!' % boldimg, status=boldok)

        # bold in input format
        inputfile = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s" % (boldtarget))

        # bandpass value
        bandpass = 2000 if options['hcp_icafix_highpass'] is None else options['hcp_icafix_highpass']

        comm = '%(script)s \
                "%(inputfile)s" \
                %(bandpass)d \
                "%(domot)s" \
                "%(trainingdata)s" \
                %(fixthreshold)d \
                "%(deleteintermediates)s"' % {
                'script'                : os.path.join(hcp['hcp_base'], 'ICAFIX', 'hcp_fix'),
                'inputfile'             : inputfile,
                'bandpass'              : int(bandpass),
                'domot'                 : "TRUE" if options['hcp_icafix_domotionreg'] is None else options['hcp_icafix_domotionreg'],
                'trainingdata'          : options['hcp_icafix_traindata'],
                'fixthreshold'          : options['hcp_icafix_threshold'],
                'deleteintermediates'   : options['hcp_icafix_deleteintermediates']}

        # -- Report command
        if boldok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test file
        tfile = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s_hp%s_clean.nii.gz" % (boldtarget, bandpass))
        fullTest = None

        # -- Run
        if run and boldok:
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, endlog, _, failed = pc.runExternalForFile(tfile, comm, 'Running single-run HCP ICAFix', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=[options['logtag'], boldtarget], fullTest=fullTest, shell=True, r=r)

                if failed:
                    report['failed'].append(printbold)
                else:
                    report['done'].append(printbold)

                # if all ok execute PostFix if enabled
                if options['hcp_icafix_postfix'] == "True":
                    if report['incomplete'] == [] and report['failed'] == [] and report['not ready'] == []:
                        result = executeHCPPostFix(sinfo, options, overwrite, hcp, run, True, bold)
                        r += result['r']
                        report = result['report']

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(tfile, fullTest, 'single-run HCP ICAFix ' + boldtarget, r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> single-run HCP ICAFix can be run"
                    report['ready'].append(printbold)
                else:
                    report['skipped'].append(printbold)

        elif run:
            report['not ready'].append(printbold)
            if options['run'] == "run":
                r += "\n---> ERROR: images missing, skipping this BOLD!"
            else:
                r += "\n---> ERROR: images missing, this BOLD would be skipped!"
        else:
            report['not ready'].append(printbold)
            if options['run'] == "run":
                r += "\n---> ERROR: No hcp info for session, skipping this BOLD!"
            else:
                r += "\n---> ERROR: No hcp info for session, this BOLD would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = "\n\n\n --- Failed during processing of bold %s\n" % (printbold)
        r += str(errormessage)
        report['failed'].append(printbold)
    except:
        r += "\n --- Failed during processing of bold %s with error:\n %s\n" % (printbold, traceback.format_exc())
        report['failed'].append(printbold)

    return {'r': r, 'report': report}


def executeHCPMultiICAFix(sinfo, options, overwrite, hcp, run, group):
    # get group data
    groupname = group["name"]
    bolds = group["bolds"]

    # prepare return variables
    r = ""
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        r += "\n\n------------------------------------------------------------"
        r += "\n---> %s group %s" % (pc.action("Processing", options['run']), groupname)
        groupok = True

        # --- check for bold images and prepare images parameter
        boldimgs = ""

         # check if files for all bolds exist
        for b in bolds:
            # set ok to true for now
            boldok = True

            # extract data
            printbold, _, _, boldinfo = b

            if 'filename' in boldinfo and options['hcp_filename'] == 'original':
                printbold  = boldinfo['filename']
                boldtarget = boldinfo['filename']
            else:
                printbold  = str(printbold)
                boldtarget = "%s%s" % (options['hcp_bold_prefix'], printbold)

            boldimg = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s" % (boldtarget))
            r, boldok = pc.checkForFile2(r, "%s.nii.gz" % boldimg, '\n     ... bold image %s present' % boldtarget, '\n     ... ERROR: bold image [%s.nii.gz] missing!' % boldimg, status=boldok)

            if not boldok:
                groupok = False
                break
            else:
                # add @ separator
                if boldimgs is not "":
                    boldimgs = boldimgs + "@"

                # add latest image
                boldimgs = boldimgs + boldimg

        # construct concat file name
        concatfilename = os.path.join(hcp['hcp_nonlin'], 'Results', groupname, groupname)

        # bandpass
        bandpass = 0 if options['hcp_icafix_highpass'] is None else options['hcp_icafix_highpass']

        comm = '%(script)s \
                "%(inputfile)s" \
                %(bandpass)d \
                "%(concatfilename)s" \
                "%(domot)s" \
                "%(trainingdata)s" \
                %(fixthreshold)d \
                "%(deleteintermediates)s"' % {
                'script'                : os.path.join(hcp['hcp_base'], 'ICAFIX', 'hcp_fix_multi_run'),
                'inputfile'             : boldimgs,
                'bandpass'              : int(bandpass),
                'concatfilename'        : concatfilename,
                'domot'                 : "FALSE" if options['hcp_icafix_domotionreg'] is None else options['hcp_icafix_domotionreg'],
                'trainingdata'          : "HCP_Style_Single_Multirun_Dedrift.RData" if options['hcp_icafix_traindata'] is None else options['hcp_icafix_traindata'],
                'fixthreshold'          : options['hcp_icafix_threshold'],
                'deleteintermediates'   : options['hcp_icafix_deleteintermediates']}

        # -- Report command
        if groupok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test file
        tfile = concatfilename + "_hp%s_clean.nii.gz" % bandpass
        fullTest = None

        # -- Run
        if run and groupok:
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, endlog, _, failed = pc.runExternalForFile(tfile, comm, 'Running multi-run HCP ICAFix', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=[options['logtag'], groupname], fullTest=fullTest, shell=True, r=r)

                if failed:
                    report['failed'].append(groupname)
                else:
                    report['done'].append(groupname)

                # if all ok execute PostFix if enabled
                if options['hcp_icafix_postfix'] == "True":
                    if report['incomplete'] == [] and report['failed'] == [] and report['not ready'] == []:
                        result = executeHCPPostFix(sinfo, options, overwrite, hcp, run, False, groupname)
                        r += result['r']
                        report = result['report']

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(tfile, fullTest, 'multi-run HCP ICAFix ' + groupname, r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> multi-run HCP ICAFix can be run"
                    report['ready'].append(groupname)
                else:
                    report['skipped'].append(groupname)

        elif run:
            report['not ready'].append(groupname)
            if options['run'] == "run":
                r += "\n---> ERROR: images missing, skipping this group!"
            else:
                r += "\n---> ERROR: images missing, this group would be skipped!"
        else:
            report['not ready'].append(groupname)
            if options['run'] == "run":
                r += "\n---> ERROR: No hcp info for session, skipping this group!"
            else:
                r += "\n---> ERROR: No hcp info for session, this group would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = "\n\n\n --- Failed during processing of group %s with error:\n" % (groupname)
        r += str(errormessage)
        report['failed'].append(groupname)
    except:
        r += "\n --- Failed during processing of group %s with error:\n %s\n" % (groupname, traceback.format_exc())
        report['failed'].append(groupname)

    return {'r': r, 'report': report}


def hcp_post_fix(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_post_fix [... processing options]``

    Runs the PostFix step of HCP Pipeline.

    REQUIREMENTS
    ============

    The code expects the input images to be named and present in the QuNex
    folder structure. The function will look into folder::

        <session id>/hcp/<session id>

    for files::

        MNINonLinear/Results/<boldname>/<boldname>_hp<highpass>_clean.nii.gz

    INPUTS
    ======

    General parameters
    ------------------

    --sessions              The batch.txt file with all the sessions
                            information. [batch.txt]
    --sessionsfolder        The path to the study/sessions folder, where the
                            imaging  data is supposed to go. [.]
    --parsessions           How many sessions to run in parallel. [1]
    --parelements           How many elements (e.g bolds) to run in
                            parallel. [1]
    --overwrite             Whether to overwrite existing data (yes)
                            or not (no). [no]
    --hcp_suffix            Specifies a suffix to the session id if multiple
                            variants are run, empty otherwise. []
    --logfolder             The path to the folder where runlogs and comlogs
                            are to be stored, if other than default [].
    --log                   Whether to keep ('keep') or remove ('remove') the
                            temporary logs once jobs are completed. ['keep']
                            When a comma or pipe ('|') separated list is given,
                            the log will be created at the first provided
                            location and then linked or copied to other
                            locations. The valid locations are:

                            - 'study' (for the default:
                              `<study>/processing/logs/comlogs` location)
                            - 'session' (for `<sessionid>/logs/comlogs`)
                            - 'hcp' (for `<hcp_folder>/logs/comlogs`)
                            - '<path>' (for an arbitrary directory)

    Specific parameters
    -------------------

    In addition the following *specific* parameters will be used to guide the
    processing in this step:

    --hcp_icafix_bolds              Specify a list of bolds for ICAFix.
                                    You can specify a comma separated list
                                    of bolds, e.g. "<boldname1>,<boldname2>",
                                    in this case single-run HCP ICAFix will be
                                    executed over specified bolds. You can also
                                    specify how to group/concatenate bolds
                                    together, e.g.
                                    "<group1>:<boldname1>,<boldname2>|
                                    <group2>:<boldname3>,<boldname4>",
                                    in this case multi-run HCP ICAFix will be
                                    executed. Instead of full bold names, you
                                    can also use bold tags from the batch file.
                                    If this parameter is not provided
                                    ICAFix will bundle all bolds together and
                                    execute multi-run HCP ICAFix, the
                                    concatenated file will be named
                                    fMRI_CONCAT_ALL. []
    --hcp_icafix_highpass           Value for the highpass filter,
                                    [0] for multi-run HCP ICAFix and [2000]
                                    for single-run HCP ICAFix.
    --hcp_matlab_mode               Specifies the Matlab version, can be
                                    interpreted, compiled or octave.
                                    [compiled]
    --hcp_postfix_dualscene         Path to an alternative template scene, if
                                    empty HCP default dual scene will be used
                                    [].
    --hcp_postfix_singlescene       Path to an alternative template scene, if
                                    empty HCP default single scene will be used
                                    [].
    --hcp_postfix_reusehighpass     Whether to reuse highpass. [YES]

    OUTPUTS
    =======

    The results of this step will be generated and populated in the
    MNINonLinear folder inside the same sessions's root hcp folder.

    The final output files are::

        MNINonLinear/Results/<boldname>/
        <session id>_<boldname>_hp<highpass>_ICA_Classification_singlescreen.scene

    where highpass is the used value for the highpass filter. The default
    highpass value is 0 for multi-run HCP ICAFix and 2000 for single-run HCP
    ICAFix .

    USE
    ===

    Runs the PostFix step of HCP Pipeline. This step creates Workbench scene
    files that can be used to visually review the signal vs. noise
    classification generated by ICAFix.

    If the hcp_icafix_bolds parameter is not provided ICAFix will bundle
    all bolds together and execute multi-run HCP ICAFix, the concatenated file
    will be named fMRI_CONCAT_ALL. WARNING: if session has many bolds such
    processing requires a lot of computational resources.

    EXAMPLE USE
    ===========

    ::

        qunex hcp_post_fix \\
            --sessions=processing/batch.txt \\
            --sessionsfolder=sessions \\
            --hcp_matlab_mode="interpreted"

    ::

        qunex hcp_post_fix \\
            --sessions=processing/batch.txt \\
            --sessionsfolder=sessions \\
            --hcp_icafix_bolds="GROUP_1:BOLD_1,BOLD_2|GROUP_2:BOLD_3,BOLD_4" \\
            --hcp_matlab_mode="interpreted"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP PostFix registration [%s] ..." % (pc.action("Running", options['run']), options['hcp_processing_mode'])

    run    = True
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, 'hcp_post_fix')
        doHCPOptionsCheck(options, sinfo, 'hcp_post_fix')
        hcp = getHCPPaths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report['boldskipped'], r = pc.useOrSkipBOLD(sinfo, options, r)
        if report['boldskipped']:
            if options['hcp_filename'] == 'original':
                report['skipped'] = [bi.get('filename', str(bn)) for bn, bnm, bt, bi in bskip]
            else:
                report['skipped'] = [str(bn) for bn, bnm, bt, bi in bskip]

        # --- Parse icafix_bolds
        singleFix, icafixBolds, icafixGroups, parsOK, r = parseICAFixBolds(options, bolds, r)
        if not parsOK:
            raise ge.CommandFailed("hcp_post_fix", "... invalid input parameters!")

        # --- Multi threading
        if singleFix:
            parelements = max(1, min(options['parelements'], len(icafixBolds)))
        else:
            parelements = max(1, min(options['parelements'], len(icafixGroups)))
        r += "\n\n%s %d PostFixes in parallel" % (pc.action("Processing", options['run']), parelements)

        # --- Execute
        # single fix
        if not singleFix:
            # put all group bolds together
            icafixBolds = []
            for g in icafixGroups:
                groupBolds = g["name"]
                icafixBolds.append(groupBolds)

        if parelements == 1: # serial execution
            for b in icafixBolds:
                # process
                result = executeHCPPostFix(sinfo, options, overwrite, hcp, run, singleFix, b)

                # merge r
                r += result['r']

                # merge report
                tempReport            = result['report']
                report['done']       += tempReport['done']
                report['incomplete'] += tempReport['incomplete']
                report['failed']     += tempReport['failed']
                report['ready']      += tempReport['ready']
                report['not ready']  += tempReport['not ready']
                report['skipped']    += tempReport['skipped']

        else: # parallel execution
            # create a multiprocessing Pool
            processPoolExecutor = ProcessPoolExecutor(parelements)
            # process
            f = partial(executeHCPPostFix, sinfo, options, overwrite, hcp, run, singleFix)
            results = processPoolExecutor.map(f, icafixBolds)

            # merge r and report
            for result in results:
                r                    += result['r']
                tempReport            = result['report']
                report['done']       += tempReport['done']
                report['failed']     += tempReport['failed']
                report['incomplete'] += tempReport['incomplete']
                report['ready']      += tempReport['ready']
                report['not ready']  += tempReport['not ready']
                report['skipped']    += tempReport['skipped']

        # report
        rep = []
        for k in ['done', 'incomplete', 'failed', 'ready', 'not ready', 'skipped']:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (sinfo['id'], "HCP PostFix: bolds " + "; ".join(rep), len(report['failed'] + report['incomplete'] + report['not ready']))

    except ge.CommandFailed as e:
        r +=  "\n\nERROR in completing %s:\n     %s\n" % (e.function, "\n     ".join(e.report))
        report = (sinfo['id'], 'HCP PostFix failed')
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        report = (sinfo['id'], 'HCP PostFix failed')
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        report = (sinfo['id'], 'HCP PostFix failed')

    r += "\n\nHCP PostFix %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, report)


def executeHCPPostFix(sinfo, options, overwrite, hcp, run, singleFix, bold):
    # prepare return variables
    r = ""
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    # extract data
    r += "\n\n------------------------------------------------------------"

    if singleFix:
        # highpass
        highpass = 2000 if options['hcp_icafix_highpass'] is None else options['hcp_icafix_highpass']

        printbold, _, _, boldinfo = bold

        if 'filename' in boldinfo and options['hcp_filename'] == 'original':
            printbold  = boldinfo['filename']
            boldtarget = boldinfo['filename']
        else:
            printbold  = str(printbold)
            boldtarget = "%s%s" % (options['hcp_bold_prefix'], printbold)

        printica = "%s_hp%s_clean.nii.gz" % (boldtarget, highpass)
        icaimg = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, printica)
        r += "\n---> %s bold ICA %s" % (pc.action("Processing", options['run']), printica)

    else:
        # highpass
        highpass = 0 if options['hcp_icafix_highpass'] is None else options['hcp_icafix_highpass']

        printbold = bold
        boldtarget = bold

        printica = "%s_hp%s_clean.nii.gz" % (boldtarget, highpass)
        icaimg = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, printica)
        r += "\n---> %s group ICA %s" % (pc.action("Processing", options['run']), printica)

    try:
        boldok = True

        # --- check for ICA image
        r, boldok = pc.checkForFile2(r, icaimg, '\n     ... ICA %s present' % boldtarget, '\n     ... ERROR: ICA [%s] missing!' % icaimg, status=boldok)

        # hcp_postfix_reusehighpass
        if options['hcp_postfix_reusehighpass'] == "True":
            reusehighpass = "YES"
        else:
            reusehighpass = "NO"

        singlescene = os.path.join(hcp['hcp_base'], 'ICAFIX/PostFixScenes/', 'ICA_Classification_SingleScreenTemplate.scene')
        if options['hcp_postfix_singlescene'] is not None:
            singlescene = options['hcp_postfix_singlescene']

        dualscene = os.path.join(hcp['hcp_base'], 'ICAFIX/PostFixScenes/', 'ICA_Classification_DualScreenTemplate.scene')
        if options['hcp_postfix_dualscene'] is not None:
            dualscene = options['hcp_postfix_dualscene']

        # matlab run mode, compiled=0, interpreted=1, octave=2
        if options['hcp_matlab_mode'] == "compiled":
            matlabrunmode = 0
        elif options['hcp_matlab_mode'] == "interpreted":
            matlabrunmode = 1
        elif options['hcp_matlab_mode'] == "octave":
            r += "\nWARNING: ICAFix runs with octave results are unstable!"
            matlabrunmode = 2
        else:
            r += "\nERROR: wrong value for the hcp_matlab_mode parameter!"
            boldok = False

        # subject/session
        subject = sinfo['id'] + options['hcp_suffix']

        comm = '%(script)s \
            --study-folder="%(studyfolder)s" \
            --subject="%(subject)s" \
            --fmri-name="%(boldtarget)s" \
            --high-pass="%(highpass)d" \
            --template-scene-dual-screen="%(dualscene)s" \
            --template-scene-single-screen="%(singlescene)s" \
            --reuse-high-pass="%(reusehighpass)s" \
            --matlab-run-mode="%(matlabrunmode)d"' % {
                'script'            : os.path.join(hcp['hcp_base'], 'ICAFIX', 'PostFix.sh'),
                'studyfolder'       : sinfo['hcp'],
                'subject'           : subject,
                'boldtarget'        : boldtarget,
                'highpass'          : int(highpass),
                'dualscene'         : dualscene,
                'singlescene'       : singlescene,
                'reusehighpass'     : reusehighpass,
                'matlabrunmode'     : matlabrunmode}

        # -- Report command
        if boldok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test files
        tfile = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s_%s_hp%s_ICA_Classification_singlescreen.scene" % (subject, boldtarget, highpass))
        fullTest = None

        # -- Run
        if run and boldok:
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, endlog, _, failed = pc.runExternalForFile(tfile, comm, 'Running HCP PostFix', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task="hcp_post_fix", logfolder=options['comlogs'], logtags=[options['logtag'], boldtarget], fullTest=fullTest, shell=True, r=r)

                if failed:
                    report['failed'].append(printbold)
                else:
                    report['done'].append(printbold)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(tfile, fullTest, 'HCP PostFix ' + boldtarget, r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP PostFix can be run"
                    report['ready'].append(printbold)
                else:
                    report['skipped'].append(printbold)

        elif run:
            report['not ready'].append(printbold)
            if options['run'] == "run":
                r += "\n---> ERROR: images missing, skipping this BOLD!"
            else:
                r += "\n---> ERROR: images missing, this BOLD would be skipped!"
        else:
            report['not ready'].append(printbold)
            if options['run'] == "run":
                r += "\n---> ERROR: No hcp info for session, skipping this BOLD!"
            else:
                r += "\n---> ERROR: No hcp info for session, this BOLD would be skipped!"

        # log beautify
        r += "\n\n"

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = "\n\n\n --- Failed during processing of bold %s with error:\n" % (printbold)
        r += str(errormessage)
        report['failed'].append(printbold)
    except:
        r += "\n --- Failed during processing of bold %s with error:\n %s\n" % (printbold, traceback.format_exc())
        report['failed'].append(printbold)

    return {'r': r, 'report': report}


def hcp_reapply_fix(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_reapply_fix [... processing options]``

    Runs the ReApplyFix step of HCP Pipeline.

    REQUIREMENTS
    ============

    The code expects the input images to be named and present in the QuNex
    folder structure. The function will look into folder::

        <session id>/hcp/<session id>

    for files::

        MNINonLinear/Results/<boldname>/<boldname>.nii.gz

    INPUTS
    ======

    General parameters
    ------------------

    --sessions              The batch.txt file with all the sessions
                            information. [batch.txt]
    --sessionsfolder        The path to the study/sessions folder, where the
                            imaging  data is supposed to go. [.]
    --parsessions           How many sessions to run in parallel. [1]
    --parelements           How many elements (e.g bolds) to run in
                            parallel. [1]
    --overwrite             Whether to overwrite existing data (yes)
                            or not (no). [no]
    --hcp_suffix            Specifies a suffix to the session id if multiple
                            variants are run, empty otherwise. []
    --logfolder             The path to the folder where runlogs and comlogs
                            are to be stored, if other than default [].
    --log                   Whether to keep ('keep') or remove ('remove') the
                            temporary logs once jobs are completed ['keep'].
                            When a comma or pipe ('|') separated list is given,
                            the log will be created at the first provided
                            location and then linked or copied to other
                            locations. The valid locations are:

                            - 'study' (for the default:
                              `<study>/processing/logs/comlogs` location)
                            - 'session' (for `<sessionid>/logs/comlogs`)
                            - 'hcp' (for `<hcp_folder>/logs/comlogs`)
                            - '<path>' (for an arbitrary directory)

    Specific parameters
    -------------------

    In addition the following *specific* parameters will be used to guide the
    processing in this step:

    --hcp_icafix_bolds                  Specify a list of bolds for ICAFix.
                                        You can specify a comma separated list
                                        of bolds, e.g.
                                        "<boldname1>,<boldname2>", in this
                                        case single-run HCP ICAFix will be
                                        executed over specified bolds. You can
                                        also specify how to group/concatenate
                                        bolds together, e.g.
                                        "<group1>:<boldname1>,<boldname2>|
                                        <group2>:<boldname3>,<boldname4>",
                                        in this case multi-run HCP ICAFix will
                                        be executed. Instead of full bold
                                        names, you can also use bold tags from
                                        the batch file. If this parameter is
                                        not provided ICAFix will bundle all
                                        bolds together and execute multi-run
                                        HCP ICAFix, the concatenated file will
                                        be named fMRI_CONCAT_ALL. []
    --hcp_icafix_highpass               Value for the highpass filter,
                                        [0] for multi-run HCP ICAFix and
                                        [2000] for single-run HCP ICAFix.
    --hcp_matlab_mode                   Specifies the MATLAB version, can be
                                        interpreted, compiled or octave.
                                        [compiled]
    --hcp_icafix_domotionreg            Whether to regress motion parameters
                                        as part of the cleaning. The default
                                        value for single-run HCP ICAFix is
                                        [TRUE], while the default for
                                        multi-run HCP ICAFix is [FALSE].
    --hcp_icafix_deleteintermediates    If TRUE, deletes both the concatenated
                                        high-pass filtered and non-filtered
                                        timeseries files that are
                                        prerequisites to FIX cleaning. [FALSE]
    --hcp_icafix_regname                Specifies surface registration name.
                                        If NONE MSMSulc will be used. [NONE]
    --hcp_lowresmesh                    Specifies the low res mesh number.
                                        [32]

    OUTPUTS
    =======

    The results of this step will be generated and populated in the
    MNINonLinear folder inside the same sessions's root hcp folder.

    The final clean ICA file can be found in::

        MNINonLinear/Results/<boldname>/<boldname>_hp<highpass>_clean.nii.gz,

    where highpass is the used value for the highpass filter. The default
    highpass value is 0 for multi-run HCP ICAFix and 2000 for single-run HCP
    ICAFix.

    USE
    ===

    Runs the ReApplyFix step of HCP Pipeline. This function executes two steps,
    first it applies the hand reclassifications of noise and signal components
    from FIX using the ReclassifyAsNoise.txt and ReclassifyAsSignal.txt input
    files. Next it executes the HCP Pipeline's ReApplyFix or ReApplyFixMulti.

    If the hcp_icafix_bolds parameter is not provided ICAFix will bundle
    all bolds together and execute multi-run HCP ICAFix, the concatenated file
    will be named fMRI_CONCAT_ALL. WARNING: if session has many bolds such
    processing requires a lot of computational resources.

    EXAMPLE USE
    ===========

    ::

        qunex hcp_reapply_fix \\
            --sessions=processing/batch.txt \\
            --sessionsfolder=sessions \\
            --hcp_matlab_mode="interpreted"

    ::

        qunex hcp_reapply_fix \\
            --sessions=processing/batch.txt \\
            --sessionsfolder=sessions \\
            --hcp_icafix_bolds="GROUP_1:BOLD_1,BOLD_2|GROUP_2:BOLD_3,BOLD_4" \\
            --hcp_matlab_mode="interpreted"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP ReApplyFix registration [%s] ..." % (pc.action("Running", options['run']), options['hcp_processing_mode'])

    run    = True
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, 'hcp_reapply_fix')
        doHCPOptionsCheck(options, sinfo, 'hcp_reapply_fix')
        hcp = getHCPPaths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report['boldskipped'], r = pc.useOrSkipBOLD(sinfo, options, r)
        if report['boldskipped']:
            if options['hcp_filename'] == 'original':
                report['skipped'] = [bi.get('filename', str(bn)) for bn, bnm, bt, bi in bskip]
            else:
                report['skipped'] = [str(bn) for bn, bnm, bt, bi in bskip]

        # --- Parse icafix_bolds
        singleFix, icafixBolds, icafixGroups, parsOK, r = parseICAFixBolds(options, bolds, r)
        if not parsOK:
            raise ge.CommandFailed("hcp_reapply_fix", "... invalid input parameters!")

        # --- Multi threading
        if singleFix:
            parelements = max(1, min(options['parelements'], len(icafixBolds)))
        else:
            parelements = max(1, min(options['parelements'], len(icafixGroups)))
        r += "\n\n%s %d ReApplyFixes in parallel" % (pc.action("Processing", options['run']), parelements)

        # --- Execute
        # single fix
        if singleFix:
            if parelements == 1: # serial execution
                for b in icafixBolds:
                    # process
                    result = executeHCPSingleReApplyFix(sinfo, options, overwrite, hcp, run, b)

                    # merge r
                    r += result['r']

                    # merge report
                    tempReport            = result['report']
                    report['done']       += tempReport['done']
                    report['incomplete'] += tempReport['incomplete']
                    report['failed']     += tempReport['failed']
                    report['ready']      += tempReport['ready']
                    report['not ready']  += tempReport['not ready']
                    report['skipped']    += tempReport['skipped']

            else: # parallel execution
                # create a multiprocessing Pool
                processPoolExecutor = ProcessPoolExecutor(parelements)
                # process
                f = partial(executeHCPSingleReApplyFix, sinfo, options, overwrite, hcp, run)
                results = processPoolExecutor.map(f, icafixBolds)

                # merge r and report
                for result in results:
                    r                    += result['r']
                    tempReport            = result['report']
                    report['done']       += tempReport['done']
                    report['failed']     += tempReport['failed']
                    report['incomplete'] += tempReport['incomplete']
                    report['ready']      += tempReport['ready']
                    report['not ready']  += tempReport['not ready']
                    report['skipped']    += tempReport['skipped']

        # multi fix
        else:
            if parelements == 1: # serial execution
                for g in icafixGroups:
                    # process
                    result = executeHCPMultiReApplyFix(sinfo, options, overwrite, hcp, run, g)

                    # merge r
                    r += result['r']

                    # merge report
                    tempReport            = result['report']
                    report['done']       += tempReport['done']
                    report['incomplete'] += tempReport['incomplete']
                    report['failed']     += tempReport['failed']
                    report['ready']      += tempReport['ready']
                    report['not ready']  += tempReport['not ready']
                    report['skipped']    += tempReport['skipped']

            else: # parallel execution
                # create a multiprocessing Pool
                processPoolExecutor = ProcessPoolExecutor(parelements)
                # process
                f = partial(executeHCPMultiReApplyFix, sinfo, options, overwrite, hcp, run)
                results = processPoolExecutor.map(f, icafixGroups)

                # merge r and report
                for result in results:
                    r                    += result['r']
                    tempReport            = result['report']
                    report['done']       += tempReport['done']
                    report['failed']     += tempReport['failed']
                    report['incomplete'] += tempReport['incomplete']
                    report['ready']      += tempReport['ready']
                    report['not ready']  += tempReport['not ready']
                    report['skipped']    += tempReport['skipped']

        # report
        rep = []
        for k in ['done', 'incomplete', 'failed', 'ready', 'not ready', 'skipped']:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (sinfo['id'], "HCP ReApplyFix: bolds " + "; ".join(rep), len(report['failed'] + report['incomplete'] + report['not ready']))

    except ge.CommandFailed as e:
        r +=  "\n\nERROR in completing %s:\n     %s\n" % (e.function, "\n     ".join(e.report))
        report = (sinfo['id'], 'HCP ReApplyFix failed')
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        report = (sinfo['id'], 'HCP ReApplyFix failed')
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        report = (sinfo['id'], 'HCP ReApplyFix failed')

    r += "\n\nHCP ReApplyFix %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, report)


def executeHCPSingleReApplyFix(sinfo, options, overwrite, hcp, run, bold):
    # extract data
    printbold, _, _, boldinfo = bold

    if 'filename' in boldinfo and options['hcp_filename'] == 'original':
        printbold  = boldinfo['filename']
        boldtarget = boldinfo['filename']
    else:
        printbold  = str(printbold)
        boldtarget = "%s%s" % (options['hcp_bold_prefix'], printbold)

    # prepare return variables
    r = ""
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        # run HCP hand reclassification
        r += "\n------------------------------------------------------------"
        r += "\n---> Executing HCP Hand reclassification for bold: %s\n" % printbold
        result = executeHCPHandReclassification(sinfo, options, overwrite, hcp, run, True, boldtarget, printbold)

        # merge r
        r += result['r']

        # move on to ReApplyFix
        rcReport = result['report']
        if rcReport['incomplete'] == [] and rcReport['failed'] == [] and rcReport['not ready'] == []:
            boldok = True

            # highpass
            highpass = 2000 if options['hcp_icafix_highpass'] is None else options['hcp_icafix_highpass']

            # matlab run mode, compiled=0, interpreted=1, octave=2
            if options['hcp_matlab_mode'] == "compiled":
                matlabrunmode = 0
            elif options['hcp_matlab_mode'] == "interpreted":
                matlabrunmode = 1
            elif options['hcp_matlab_mode'] == "octave":
                r += "\nWARNING: ICAFix runs with octave results are unstable!"
                matlabrunmode = 2
            else:
                r += "\nERROR: wrong value for the hcp_matlab_mode parameter!"
                boldok = False

            comm = '%(script)s \
                --path="%(path)s" \
                --subject="%(subject)s" \
                --fmri-name="%(boldtarget)s" \
                --high-pass="%(highpass)d" \
                --reg-name="%(regname)s" \
                --low-res-mesh="%(lowresmesh)s" \
                --matlab-run-mode="%(matlabrunmode)d" \
                --motion-regression="%(motionregression)s" \
                --delete-intermediates="%(deleteintermediates)s"' % {
                    'script'              : os.path.join(hcp['hcp_base'], 'ICAFIX', 'ReApplyFixPipeline.sh'),
                    'path'                : sinfo['hcp'],
                    'subject'             : sinfo['id'] + options['hcp_suffix'],
                    'boldtarget'          : boldtarget,
                    'highpass'            : int(highpass),
                    'regname'             : options['hcp_icafix_regname'],
                    'lowresmesh'          : options['hcp_lowresmesh'],
                    'matlabrunmode'       : matlabrunmode,
                    'motionregression'    : "TRUE" if options['hcp_icafix_domotionreg'] is None else options['hcp_icafix_domotionreg'],
                    'deleteintermediates' : options['hcp_icafix_deleteintermediates']}

            # -- Report command
            if boldok:
                r += "\n------------------------------------------------------------\n"
                r += "Running HCP Pipelines command via QuNex:\n\n"
                r += comm.replace("--", "\n    --").replace("             ", "")
                r += "\n------------------------------------------------------------\n"

            # -- Test files
            # postfix
            postfix = "%s%s_hp%s_clean.dtseries.nii" % (boldtarget, options['hcp_cifti_tail'], highpass)
            if options['hcp_icafix_regname'] != "NONE" and options['hcp_icafix_regname'] != "":
                postfix = "%s%s_%s_hp%s_clean.dtseries.nii" % (boldtarget, options['hcp_cifti_tail'], options['hcp_icafix_regname'], highpass)

            tfile = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, postfix)
            fullTest = None

            # -- Run
            if run and boldok:
                if options['run'] == "run":
                    r, _, _, failed = pc.runExternalForFile(tfile, comm, 'Running single-run HCP ReApplyFix', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=[options['logtag'], boldtarget], fullTest=fullTest, shell=True, r=r)

                    if failed:
                        report['failed'].append(printbold)
                    else:
                        report['done'].append(printbold)

                # -- just checking
                else:
                    passed, _, r, failed = pc.checkRun(tfile, fullTest, 'single-run HCP ReApplyFix ' + boldtarget, r, overwrite=overwrite)
                    if passed is None:
                        r += "\n---> single-run HCP ReApplyFix can be run"
                        report['ready'].append(printbold)
                    else:
                        report['skipped'].append(printbold)

            elif run:
                report['not ready'].append(printbold)
                if options['run'] == "run":
                    r += "\n---> ERROR: images missing, skipping this BOLD!"
                else:
                    r += "\n---> ERROR: images missing, this BOLD would be skipped!"
            else:
                report['not ready'].append(printbold)
                if options['run'] == "run":
                    r += "\n---> ERROR: No hcp info for session, skipping this BOLD!"
                else:
                    r += "\n---> ERROR: No hcp info for session, this BOLD would be skipped!"

            # log beautify
            r += "\n\n"

        else:
            r += "\n===> ERROR: Hand reclassification failed for bold: %s!" % printbold
            report['failed'].append(printbold)
            boldok = False

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = "\n\n\n --- Failed during processing of bold %s with error:\n" % (printbold)
        r += str(errormessage)
        report['failed'].append(printbold)
    except:
        r += "\n --- Failed during processing of bold %s with error:\n %s\n" % (printbold, traceback.format_exc())
        report['failed'].append(printbold)

    return {'r': r, 'report': report}


def executeHCPMultiReApplyFix(sinfo, options, overwrite, hcp, run, group):
    # get group data
    groupname = group["name"]
    bolds = group["bolds"]

    # prepare return variables
    r = ""
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        r += "\n------------------------------------------------------------"
        r += "\n---> %s group %s" % (pc.action("Processing", options['run']), groupname)
        groupok = True

        # --- check for bold images and prepare images parameter
        boldtargets = ""

        # check if files for all bolds exist
        for b in bolds:
            # boldok
            boldok = True

            # extract data
            printbold, _, _, boldinfo = b

            if 'filename' in boldinfo and options['hcp_filename'] == 'original':
                printbold  = boldinfo['filename']
                boldtarget = boldinfo['filename']
            else:
                printbold  = str(printbold)
                boldtarget = "%s%s" % (options['hcp_bold_prefix'], printbold)

            boldimg = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s.nii.gz" % (boldtarget))
            r, boldok = pc.checkForFile2(r, boldimg, '\n     ... bold image %s present' % boldtarget, '\n     ... ERROR: bold image [%s] missing!' % boldimg, status=boldok)

            if not boldok:
                groupok = False
                break
            else:
                # add @ separator
                if boldtargets is not "":
                    boldtargets = boldtargets + "@"

                # add latest image
                boldtargets = boldtargets + boldtarget

        # run HCP hand reclassification
        r += "\n---> Executing HCP Hand reclassification for group: %s\n" % groupname
        result = executeHCPHandReclassification(sinfo, options, overwrite, hcp, run, False, groupname, groupname)

        # merge r
        r += result['r']

        # check if hand reclassification was OK
        rcReport = result['report']
        if rcReport['incomplete'] == [] and rcReport['failed'] == [] and rcReport['not ready'] == []:
            groupok = True

            # matlab run mode, compiled=0, interpreted=1, octave=2
            if options['hcp_matlab_mode'] == "compiled":
                matlabrunmode = 0
            elif options['hcp_matlab_mode'] == "interpreted":
                matlabrunmode = 1
            elif options['hcp_matlab_mode'] == "octave":
                r += "\nWARNING: ICAFix runs with octave results are unstable!"
                matlabrunmode = 2
            else:
                r += "\nERROR: wrong value for the hcp_matlab_mode parameter!"
                groupok = False

            # highpass
            highpass = 0 if options['hcp_icafix_highpass'] is None else options['hcp_icafix_highpass'] 

            comm = '%(script)s \
                --path="%(path)s" \
                --subject="%(subject)s" \
                --fmri-names="%(boldtargets)s" \
                --concat-fmri-name="%(groupname)s" \
                --high-pass="%(highpass)d" \
                --reg-name="%(regname)s" \
                --low-res-mesh="%(lowresmesh)s" \
                --matlab-run-mode="%(matlabrunmode)d" \
                --motion-regression="%(motionregression)s" \
                --delete-intermediates="%(deleteintermediates)s"' % {
                    'script'              : os.path.join(hcp['hcp_base'], 'ICAFIX', 'ReApplyFixMultiRunPipeline.sh'),
                    'path'                : sinfo['hcp'],
                    'subject'             : sinfo['id'] + options['hcp_suffix'],
                    'boldtargets'         : boldtargets,
                    'groupname'           : groupname,
                    'highpass'            : int(highpass),
                    'regname'             : options['hcp_icafix_regname'],
                    'lowresmesh'          : options['hcp_lowresmesh'],
                    'matlabrunmode'       : matlabrunmode,
                    'motionregression'    : "FALSE" if options['hcp_icafix_domotionreg'] is None else options['hcp_icafix_domotionreg'],
                    'deleteintermediates' : options['hcp_icafix_deleteintermediates']}

            # -- Report command
            if groupok:
                r += "\n------------------------------------------------------------\n"
                r += "Running HCP Pipelines command via QuNex:\n\n"
                r += comm.replace("--", "\n    --").replace("             ", "")
                r += "\n------------------------------------------------------------\n"

            # -- Test files
            # postfix
            postfix = "%s%s_hp%s_clean.dtseries.nii" % (groupname, options['hcp_cifti_tail'], highpass)
            if options['hcp_icafix_regname'] != "NONE" and options['hcp_icafix_regname'] != "":
                postfix = "%s%s_%s_hp%s_clean.dtseries.nii" % (groupname, options['hcp_cifti_tail'], options['hcp_icafix_regname'], highpass)

            tfile = os.path.join(hcp['hcp_nonlin'], 'Results', groupname, postfix)
            fullTest = None

            # -- Run
            if run and groupok:
                if options['run'] == "run":
                    r, endlog, _, failed = pc.runExternalForFile(tfile, comm, 'Running multi-run HCP ReApplyFix', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=[options['logtag'], groupname], fullTest=fullTest, shell=True, r=r)

                    if failed:
                        report['failed'].append(groupname)
                    else:
                        report['done'].append(groupname)

                # -- just checking
                else:
                    passed, _, r, failed = pc.checkRun(tfile, fullTest, 'multi-run HCP ReApplyFix ' + groupname, r, overwrite=overwrite)
                    if passed is None:
                        r += "\n---> multi-run HCP ReApplyFix can be run"
                        report['ready'].append(groupname)
                    else:
                        report['skipped'].append(groupname)

            elif run:
                report['not ready'].append(groupname)
                if options['run'] == "run":
                    r += "\n---> ERROR: images missing, skipping this group!"
                else:
                    r += "\n---> ERROR: images missing, this group would be skipped!"
            else:
                report['not ready'].append(groupname)
                if options['run'] == "run":
                    r += "\n---> ERROR: No hcp info for session, skipping this group!"
                else:
                    r += "\n---> ERROR: No hcp info for session, this group would be skipped!"

            # log beautify
            r += "\n\n"

        else:
            r += "\n===> ERROR: Hand reclassification failed for bold: %s!" % printbold

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = "\n\n\n --- Failed during processing of group %s with error:\n" % (groupname)
        r += str(errormessage)
        report['failed'].append(groupname)
    except:
        r += "\n --- Failed during processing of group %s with error:\n %s\n" % (groupname, traceback.format_exc())
        report['failed'].append(groupname)

    return {'r': r, 'report': report}


def executeHCPHandReclassification(sinfo, options, overwrite, hcp, run, singleFix, boldtarget, printbold):
    # prepare return variables
    r = ""
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        r += "\n---> %s ICA %s" % (pc.action("Processing", options['run']), printbold)
        boldok = True

        # load parameters or use default values
        if singleFix:
            highpass = 2000 if options['hcp_icafix_highpass'] is None else options['hcp_icafix_highpass']
        else:
            highpass = 0 if options['hcp_icafix_highpass'] is None else options['hcp_icafix_highpass']

        # --- check for bold image
        icaimg = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s_hp%s_clean.nii.gz" % (boldtarget, highpass))
        r, boldok = pc.checkForFile2(r, icaimg, '\n     ... ICA %s present' % boldtarget, '\n     ... ERROR: ICA [%s] missing!' % icaimg, status=boldok)

        comm = '%(script)s \
            --study-folder="%(studyfolder)s" \
            --subject="%(subject)s" \
            --fmri-name="%(boldtarget)s" \
            --high-pass="%(highpass)d"' % {
                'script'            : os.path.join(hcp['hcp_base'], 'ICAFIX', 'ApplyHandReClassifications.sh'),
                'studyfolder'       : sinfo['hcp'],
                'subject'           : sinfo['id'] + options['hcp_suffix'],
                'boldtarget'        : boldtarget,
                'highpass'          : int(highpass)}

        # -- Report command
        if boldok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test files
        tfile = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s_hp%s.ica" % (boldtarget, highpass), "HandNoise.txt")
        fullTest = None

        # -- Run
        if run and boldok:
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, endlog, _, failed = pc.runExternalForFile(tfile, comm, 'Running HCP HandReclassification', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task="hcp_HandReclassification", logfolder=options['comlogs'], logtags=[options['logtag'], boldtarget], fullTest=fullTest, shell=True, r=r)

                if failed:
                    report['failed'].append(printbold)
                else:
                    report['done'].append(printbold)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(tfile, fullTest, 'HCP HandReclassification ' + boldtarget, r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP HandReclassification can be run"
                    report['ready'].append(printbold)
                else:
                    report['skipped'].append(printbold)

        elif run:
            report['not ready'].append(printbold)
            if options['run'] == "run":
                r += "\n---> ERROR: images missing, skipping this BOLD!"
            else:
                r += "\n---> ERROR: images missing, this BOLD would be skipped!"
        else:
            report['not ready'].append(printbold)
            if options['run'] == "run":
                r += "\n---> ERROR: No hcp info for session, skipping this BOLD!"
            else:
                r += "\n---> ERROR: No hcp info for session, this BOLD would be skipped!"

        # log beautify
        r += "\n"

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = "\n\n\n --- Failed during processing of bold %s with error:\n" % (printbold)
        r = str(errormessage)
        report['failed'].append(printbold)
    except:
        r += "\n --- Failed during processing of bold %s with error:\n %s\n" % (printbold, traceback.format_exc())
        report['failed'].append(printbold)

    return {'r': r, 'report': report}


def parseMSMAllBolds(options, bolds, r):
    # parse the same way as with icafix first
    singleRun, hcpBolds, icafixGroups, parsOK, r = parseICAFixBolds(options, bolds, r, True)

    # extract the first one
    icafixGroup = icafixGroups[0]

    # if more than one group print a WARNING
    if (len(icafixGroups) > 1):
        # extract the first group
        r += "\n---> WARNING: multiple groups provided in hcp_icafix_bolds, running MSMAll by using only the first one [%s]!" % icafixGroup["name"]

    # validate that msmall bolds is a subset of icafixGroups
    if options['hcp_msmall_bolds'] is not None:
        msmallBolds = options['hcp_msmall_bolds'].split(",")

        for b in msmallBolds:
            if b not in hcpBolds:
                r += "\n---> ERROR: bold %s defined in hcp_msmall_bolds but not found in the used hcp_icafix_bolds!" % b
                parsOK = False

    return (singleRun, icafixGroup, parsOK, r)


def hcp_msmall(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_msmall [... processing options]``

    Runs the MSMAll step of the HCP Pipeline.

    REQUIREMENTS
    ============

    The code expects the input images to be named and present in the QuNex
    folder structure. The function will look into folder::

        <session id>/hcp/<session id>

    for files::

        MNINonLinear/Results/<boldname>/
        <boldname>_<hcp_cifti_tail>_hp<hcp_highpass>_clean.dtseries.nii

    INPUTS
    ======

    General parameters
    ------------------

    --sessions              The batch.txt file with all the sessions
                            information. [batch.txt]
    --sessionsfolder        The path to the study/sessions folder, where the
                            imaging  data is supposed to go. [.]
    --parsessions           How many sessions to run in parallel. [1]
    --overwrite             Whether to overwrite existing data (yes)
                            or not (no). [no]
    --hcp_suffix            Specifies a suffix to the session id if multiple
                            variants are run, empty otherwise. []
    --logfolder             The path to the folder where runlogs and comlogs
                            are to be stored, if other than default [].
    --log                   Whether to keep ('keep') or remove ('remove') the
                            temporary logs once jobs are completed. ['keep']
                            When a comma or pipe ('|') separated list is given,
                            the log will be created at the first provided
                            location and then linked or copied to other
                            locations. The valid locations are:

                            - 'study' (for the default:
                              `<study>/processing/logs/comlogs` location)
                            - 'session' (for `<sessionid>/logs/comlogs`)
                            - 'hcp' (for `<hcp_folder>/logs/comlogs`)
                            - '<path>' (for an arbitrary directory)

    Specific parameters
    -------------------

    In addition the following *specific* parameters will be used to guide the
    processing in this step:

    --hcp_icafix_bolds              List of bolds on which ICAFix was applied,
                                    with the same format as for ICAFix.
                                    Typically, this should be identical to the
                                    list used in the ICAFix run. If multi-run
                                    ICAFix was run with two or more groups then
                                    HCP MSMAll will be executed over the first
                                    specified group (and the scans listed for
                                    hcp_msmall_bolds must be limited to scans
                                    in the first concatenation group as well).
                                    If not provided MSMAll will assume multi-run
                                    ICAFix was executed with all bolds bundled
                                    together in a single concatenation called
                                    fMRI_CONCAT_ALL (i.e., same default
                                    behavior as in ICAFix). []
    --hcp_msmall_bolds              A comma separated list that defines the
                                    bolds that will be used in the computation
                                    of the MSMAll registration. Typically, this
                                    should be limited to resting-state scans.
                                    Specified bolds have to be a subset of bolds
                                    used from the hcp_icafix_bolds parameter
                                    [if not specified all bolds specified in
                                    hcp_icafix_bolds will be used, which is
                                    probably NOT what you want to do if
                                    hcp_icafix_bolds includes non-resting-state
                                    scans].
    --hcp_icafix_highpass           Value for the highpass filter, [0] for
                                    multi-run HCP ICAFix and [2000] for
                                    single-run HCP ICAFix. Should be identical
                                    to the value used for ICAFIX.
    --hcp_msmall_outfmriname        The name which will be given to the
                                    concatenation of scans specified by the
                                    hcp_msmall_bold parameter. [rfMRI_REST]
    --hcp_msmall_templates          Path to directory containing MSMAll template
                                    files.
                                    [<HCPPIPEDIR>/global/templates/MSMAll]
    --hcp_msmall_outregname         Output registration name.
                                    [MSMAll_InitialReg]
    --hcp_hiresmesh                 High resolution mesh node count. [164]
    --hcp_lowresmesh                Low resolution mesh node count. [32]
    --hcp_regname                   Input registration name. [MSMSulc]
    --hcp_matlab_mode               Specifies the MATLAB version, can be
                                    interpreted, compiled or octave.
                                    [compiled]
    --hcp_msmall_procstring         Identification for FIX cleaned dtseries to
                                    use.
                                    [<hcp_cifti_tail>_hp<hcp_highpass>_clean]
    --hcp_msmall_resample           Whether to automatically run
                                    HCP DeDriftAndResample if HCP MSMAll
                                    finishes successfully. [TRUE]

    OUTPUTS
    =======

    The results of this step will be generated and populated in the
    MNINonLinear folder inside the same sessions's root hcp folder.

    The final clean file can be found in::

        MNINonLinear/Results/<outfmriname>/
        <outfmriname>_<hcp_cifti_tail>_hp<hcp_highpass>_clean_vn.dtseries.nii

    where highpass is the used value for the highpass filter. The default
    highpass value is 0 for multi-run HCP ICAFix and 2000 for single-run HCP
    ICAFix. The default cifti tail (<hcp_cifti_tail>) is Atlas.

    USE
    ===

    Runs the MSMAll step of the HCP Pipeline. This function executes two steps,
    it first runs MSMAll and if it completes successfully it then executes
    the DeDriftAndResample step. To disable this automatic execution of
    DeDriftAndResample set hcp_msmall_resample to FALSE.

    The MSMAll step computes the MSMAll registration based on resting-state
    connectivity, resting-state topography, and myelin-map architecture.
    The DeDriftAndResample step applies the MSMAll registration to a specified
    set of maps and fMRI runs.

    MSMAll is intended for use with fMRI runs cleaned with hcp_icafix. Except
    for specialized/expert-user situations, the hcp_icafix_bolds parameter
    should be identical to what was used in hcp_icafix. If hcp_icafix_bolds
    is not provided MSMAll/DeDriftAndResample will assume multi-run ICAFix was
    executed with all bolds bundled together in a single concatenation called
    fMRI_CONCAT_ALL. (This is the default behavior if hcp_icafix_bolds
    parameter is not provided in the case of hcp_icafix).

    A key parameter in hcp_msmall is `hcp_msmall_bolds`, which controls the fMRI
    runs that enter into the computation of the MSMAll registration. Since
    MSMAll registration was designed to be computed from resting-state scans,
    this should be a list of the resting-state fMRI scans that you want to
    contribute to the computation of the MSMAll registration.

    However, it is perfectly fine to apply the MSMAll registration to task fMRI
    scans in the DeDriftAndResample step. The fMRI scans to which the MSMAll
    registration is applied are controlled by the `hcp_icafix_bolds` parameter,
    since typically one wants to apply the MSMAll registration to the same full
    set of fMRI scans that were cleaned using hcp_icafix.

    EXAMPLE USE
    ===========

    ::

        # HCP MSMAll after application of single-run ICAFix
        qunex hcp_msmall \\
            --sessions=processing/batch.txt \\
            --sessionsfolder=sessions \\
            --hcp_icafix_bolds="REST_1,REST_2,TASK_1,TASK_2" \\
            --hcp_msmall_bolds="REST_1,REST_2" \\
            --hcp_matlab_mode="interpreted"

    ::

        # HCP MSMAll after application of multi-run ICAFix
        qunex hcp_msmall \\
            --sessions=processing/batch.txt \\
            --sessionsfolder=sessions \\
            --hcp_icafix_bolds="GROUP_1:REST_1,REST_2,TASK_1|GROUP_2:REST_3,TASK_2" \\
            --hcp_msmall_bolds="REST_1,REST_2" \\
            --hcp_matlab_mode="interpreted"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP MSMAll registration [%s] ..." % (pc.action("Running", options['run']), options['hcp_processing_mode'])

    run    = True
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, 'hcp_msmall')
        doHCPOptionsCheck(options, sinfo, 'hcp_msmall')
        hcp = getHCPPaths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report['boldskipped'], r = pc.useOrSkipBOLD(sinfo, options, r)
        if report['boldskipped']:
            if options['hcp_filename'] == 'original':
                report['skipped'] = [bi.get('filename', str(bn)) for bn, bnm, bt, bi in bskip]
            else:
                report['skipped'] = [str(bn) for bn, bnm, bt, bi in bskip]

        # --- Parse msmall_bolds
        singleRun, msmallGroup, parsOK, r = parseMSMAllBolds(options, bolds, r)
        if not parsOK:
            raise ge.CommandFailed("hcp_msmall", "... invalid input parameters!")

        # --- Execute
        # single-run
        if singleRun:
            # process
            result = executeHCPSingleMSMAll(sinfo, options, overwrite, hcp, run, msmallGroup)
        # multi-run
        else:
            # process
            result = executeHCPMultiMSMAll(sinfo, options, overwrite, hcp, run, msmallGroup)

        # merge r
        r += result['r']

        # merge report
        tempReport            = result['report']
        report['done']       += tempReport['done']
        report['incomplete'] += tempReport['incomplete']
        report['failed']     += tempReport['failed']
        report['ready']      += tempReport['ready']
        report['not ready']  += tempReport['not ready']
        report['skipped']    += tempReport['skipped']

        # if all ok execute DeDrifAndResample if enabled
        if options['hcp_msmall_resample'] == "True":
            if report['incomplete'] == [] and report['failed'] == [] and report['not ready'] == []:
                # single-run
                if singleRun:
                    result = executeHCPSingleDeDriftAndResample(sinfo, options, overwrite, hcp, run, msmallGroup)
                # multi-run
                else:
                    result = executeHCPMultiDeDriftAndResample(sinfo, options, overwrite, hcp, run, [msmallGroup])

                r += result['r']
                report = result['report']

        # report
        rep = []
        for k in ['done', 'incomplete', 'failed', 'ready', 'not ready', 'skipped']:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (sinfo['id'], "HCP MSMAll: bolds " + "; ".join(rep), len(report['failed'] + report['incomplete'] + report['not ready']))

    except ge.CommandFailed as e:
        r +=  "\n\nERROR in completing %s:\n     %s\n" % (e.function, "\n     ".join(e.report))
        report = (sinfo['id'], 'HCP MSMAll failed')
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        report = (sinfo['id'], 'HCP MSMAll failed')
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        report = (sinfo['id'], 'HCP MSMAll failed')

    r += "\n\nHCP MSMAll %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, report)


def executeHCPSingleMSMAll(sinfo, options, overwrite, hcp, run, group):
    # prepare return variables
    r = ""
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        # get data
        bolds = group["bolds"]

        # msmallBolds
        msmallBolds = ""
        if options['hcp_msmall_bolds'] is not None:
            msmallBolds = options['hcp_msmall_bolds'].replace(",", "@")

        # outfmriname
        outfmriname = options['hcp_msmall_outfmriname']

        r += "\n\n------------------------------------------------------------"
        r += "\n---> %s MSMAll %s" % (pc.action("Processing", options['run']), outfmriname)
        boldsok = True

        # --- check for bold images and prepare targets parameter
        # highpass value
        highpass = 2000 if options['hcp_icafix_highpass'] is None else options['hcp_icafix_highpass'] 

        # fmriprocstring
        fmriprocstring = "%s_hp%s_clean" % (options['hcp_cifti_tail'], str(highpass))
        if options['hcp_msmall_procstring'] is not None:
            fmriprocstring = options['hcp_msmall_procstring']

        # check if files for all bolds exist
        for b in bolds:
            # set ok to true for now
            boldok = True

            # extract data
            printbold, _, _, boldinfo = b

            if 'filename' in boldinfo and options['hcp_filename'] == 'original':
                printbold  = boldinfo['filename']
                boldtarget = boldinfo['filename']
            else:
                printbold  = str(printbold)
                boldtarget = "%s%s" % (options['hcp_bold_prefix'], printbold)

            # input file check
            boldimg = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s%s.dtseries.nii" % (boldtarget, fmriprocstring))
            r, boldok = pc.checkForFile2(r, boldimg, '\n     ... bold image %s present' % boldtarget, '\n     ... ERROR: bold image [%s] missing!' % boldimg, status=boldok)

            if not boldok:
                boldsok = False

            # if msmallBolds is not defined add all icafix bolds
            if options['hcp_msmall_bolds'] is None:
                # add @ separator
                if msmallBolds is not "":
                    msmallBolds = msmallBolds + "@"

                # add latest image
                msmallBolds = msmallBolds + boldtarget

        if options['hcp_msmall_templates'] is None:
          msmalltemplates = os.path.join(hcp['hcp_base'], 'global', 'templates', 'MSMAll')
        else:
          msmalltemplates = options['hcp_msmall_templates']

        # matlab run mode, compiled=0, interpreted=1, octave=2
        if options['hcp_matlab_mode'] == "compiled":
            matlabrunmode = 0
        elif options['hcp_matlab_mode'] == "interpreted":
            matlabrunmode = 1
        elif options['hcp_matlab_mode'] == "octave":
            matlabrunmode = 2
        else:
            r += "\n---> ERROR: wrong value for the hcp_matlab_mode parameter!"
            boldsok = False

        comm = '%(script)s \
            --path="%(path)s" \
            --subject="%(subject)s" \
            --fmri-names-list="%(msmallBolds)s" \
            --multirun-fix-names="" \
            --multirun-fix-concat-name="" \
            --multirun-fix-names-to-use="" \
            --output-fmri-name="%(outfmriname)s" \
            --high-pass="%(highpass)d" \
            --fmri-proc-string="%(fmriprocstring)s" \
            --msm-all-templates="%(msmalltemplates)s" \
            --output-registration-name="%(outregname)s" \
            --high-res-mesh="%(highresmesh)s" \
            --low-res-mesh="%(lowresmesh)s" \
            --input-registration-name="%(inregname)s" \
            --matlab-run-mode="%(matlabrunmode)d"' % {
                'script'              : os.path.join(hcp['hcp_base'], 'MSMAll', 'MSMAllPipeline.sh'),
                'path'                : sinfo['hcp'],
                'subject'             : sinfo['id'] + options['hcp_suffix'],
                'msmallBolds'         : msmallBolds,
                'outfmriname'         : outfmriname,
                'highpass'            : int(highpass),
                'fmriprocstring'      : fmriprocstring,
                'msmalltemplates'     : msmalltemplates,
                'outregname'          : options['hcp_msmall_outregname'],
                'highresmesh'         : options['hcp_hiresmesh'],
                'lowresmesh'          : options['hcp_lowresmesh'],
                'inregname'           : options['hcp_regname'],
                'matlabrunmode'       : matlabrunmode}

        # -- Report command
        if boldsok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test file
        tfile = os.path.join(hcp['hcp_nonlin'], 'Results', outfmriname, "%s%s_vn.dtseries.nii" % (outfmriname, fmriprocstring))
        fullTest = None

        # -- Run
        if run and boldsok:
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, _, _, failed = pc.runExternalForFile(tfile, comm, 'Running HCP MSMAll', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=[options['logtag'], boldtarget], fullTest=fullTest, shell=True, r=r)

                if failed:
                    report['failed'].append(printbold)
                else:
                    report['done'].append(printbold)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(tfile, fullTest, 'HCP MSMAll ' + boldtarget, r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP MSMAll can be run"
                    report['ready'].append(printbold)
                else:
                    report['skipped'].append(printbold)

        elif run:
            report['not ready'].append(printbold)
            if options['run'] == "run":
                r += "\n---> ERROR: images missing, skipping this BOLD!"
            else:
                r += "\n---> ERROR: images missing, this BOLD would be skipped!"
        else:
            report['not ready'].append(printbold)
            if options['run'] == "run":
                r += "\n---> ERROR: No hcp info for session, skipping this BOLD!"
            else:
                r += "\n---> ERROR: No hcp info for session, this BOLD would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = "\n\n\n --- Failed during processing of bolds %s\n" % (msmallBolds)
        r += str(errormessage)
        report['failed'].append(msmallBolds)
    except:
        r += "\n --- Failed during processing of bolds %s with error:\n %s\n" % (msmallBolds, traceback.format_exc())
        report['failed'].append(msmallBolds)

    return {'r': r, 'report': report}


def executeHCPMultiMSMAll(sinfo, options, overwrite, hcp, run, group):
    # prepare return variables
    r = ""
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        # get group data
        groupname = group["name"]
        bolds = group["bolds"]

        # outfmriname
        outfmriname = options['hcp_msmall_outfmriname']

        r += "\n\n------------------------------------------------------------"
        r += "\n---> %s MSMAll %s" % (pc.action("Processing", options['run']), outfmriname)

        # --- check for bold images and prepare targets parameter
        boldtargets = ""

        # highpass
        highpass = 0 if options['hcp_icafix_highpass'] is None else options['hcp_icafix_highpass']

        # fmriprocstring
        fmriprocstring = "%s_hp%s_clean" % (options['hcp_cifti_tail'], str(highpass))
        if options['hcp_msmall_procstring'] is not None:
            fmriprocstring = options['hcp_msmall_procstring']

        # check if files for all bolds exist
        for b in bolds:
            # set ok to true for now
            boldok = True

            # extract data
            printbold, _, _, boldinfo = b

            if 'filename' in boldinfo and options['hcp_filename'] == 'original':
                printbold  = boldinfo['filename']
                boldtarget = boldinfo['filename']
            else:
                printbold  = str(printbold)
                boldtarget = "%s%s" % (options['hcp_bold_prefix'], printbold)

            # input file check
            boldimg = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s%s.dtseries.nii" % (boldtarget, fmriprocstring))
            r, boldok = pc.checkForFile2(r, boldimg, '\n     ... bold image %s present' % boldtarget, '\n     ... ERROR: bold image [%s] missing!' % boldimg, status=boldok)

            if not boldok:
                break
            else:
                # add @ separator
                if boldtargets is not "":
                    boldtargets = boldtargets + "@"

                # add latest image
                boldtargets = boldtargets + boldtarget

        if boldok:
            # check if group file exists
            groupica = "%s_hp%s_clean.nii.gz" % (groupname, highpass)
            groupimg = os.path.join(hcp['hcp_nonlin'], 'Results', groupname, groupica)
            r, boldok = pc.checkForFile2(r, groupimg, '\n     ... ICA %s present' % groupname, '\n     ... ERROR: ICA [%s] missing!' % groupimg, status=boldok)

        if options['hcp_msmall_templates'] is None:
          msmalltemplates = os.path.join(hcp['hcp_base'], 'global', 'templates', 'MSMAll')
        else:
          msmalltemplates = options['hcp_msmall_templates']

        # matlab run mode, compiled=0, interpreted=1, octave=2
        if options['hcp_matlab_mode'] == "compiled":
            matlabrunmode = 0
        elif options['hcp_matlab_mode'] == "interpreted":
            matlabrunmode = 1
        elif options['hcp_matlab_mode'] == "octave":
            matlabrunmode = 2
        else:
            r += "\n---> ERROR: wrong value for the hcp_matlab_mode parameter!"
            boldok = False

        # fix names to use
        fixnamestouse = boldtargets
        if options['hcp_msmall_bolds'] is not None:
            fixnamestouse = options['hcp_msmall_bolds'].replace(",", "@")

        comm = '%(script)s \
            --path="%(path)s" \
            --subject="%(subject)s" \
            --fmri-names-list="" \
            --multirun-fix-names="%(fixnames)s" \
            --multirun-fix-concat-name="%(concatname)s" \
            --multirun-fix-names-to-use="%(fixnamestouse)s" \
            --output-fmri-name="%(outfmriname)s" \
            --high-pass="%(highpass)d" \
            --fmri-proc-string="%(fmriprocstring)s" \
            --msm-all-templates="%(msmalltemplates)s" \
            --output-registration-name="%(outregname)s" \
            --high-res-mesh="%(highresmesh)s" \
            --low-res-mesh="%(lowresmesh)s" \
            --input-registration-name="%(inregname)s" \
            --matlab-run-mode="%(matlabrunmode)d"' % {
                'script'              : os.path.join(hcp['hcp_base'], 'MSMAll', 'MSMAllPipeline.sh'),
                'path'                : sinfo['hcp'],
                'subject'             : sinfo['id'] + options['hcp_suffix'],
                'fixnames'            : boldtargets,
                'concatname'          : groupname,
                'fixnamestouse'       : fixnamestouse,
                'outfmriname'         : outfmriname,
                'highpass'            : int(highpass),
                'fmriprocstring'      : fmriprocstring,
                'msmalltemplates'     : msmalltemplates,
                'outregname'          : options['hcp_msmall_outregname'],
                'highresmesh'         : options['hcp_hiresmesh'],
                'lowresmesh'          : options['hcp_lowresmesh'],
                'inregname'           : options['hcp_regname'],
                'matlabrunmode'       : matlabrunmode}

        # -- Report command
        if boldok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test file
        tfile = os.path.join(hcp['hcp_nonlin'], 'Results', outfmriname, "%s%s_vn.dtseries.nii" % (outfmriname, fmriprocstring))
        fullTest = None

        # -- Run
        if run and boldok:
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, endlog, _, failed = pc.runExternalForFile(tfile, comm, 'Running HCP MSMAll', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=[options['logtag'], groupname], fullTest=fullTest, shell=True, r=r)

                if failed:
                    report['failed'].append(groupname)
                else:
                    report['done'].append(groupname)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(tfile, fullTest, 'HCP MSMAll ' + groupname, r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP MSMAll can be run"
                    report['ready'].append(groupname)
                else:
                    report['skipped'].append(groupname)

        elif run:
            report['not ready'].append(groupname)
            if options['run'] == "run":
                r += "\n---> ERROR: images missing, skipping this group!"
            else:
                r += "\n---> ERROR: images missing, this group would be skipped!"
        else:
            report['not ready'].append(groupname)
            if options['run'] == "run":
                r += "\n---> ERROR: No hcp info for session, skipping this BOLD!"
            else:
                r += "\n---> ERROR: No hcp info for session, this BOLD would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = "\n\n\n --- Failed during processing of group %s with error:\n" % (groupname)
        r += str(errormessage)
        report['failed'].append(groupname)
    except:
        r += "\n --- Failed during processing of group %s with error:\n %s\n" % (groupname, traceback.format_exc())
        report['failed'].append(groupname)

    return {'r': r, 'report': report}


def hcp_dedrift_and_resample(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_dedrift_and_resample [... processing options]``

    Runs the DeDriftAndResample step of the HCP Pipeline.

    REQUIREMENTS
    ============

    The code expects the input images to be named and present in the QuNex
    folder structure. The function will look into folder::

        <session id>/hcp/<session id>

    for files::

        MNINonLinear/Results/<boldname>/
        <boldname>_<hcp_cifti_tail>_hp<hcp_highpass>_clean.dtseries.nii

    INPUTS
    ======

    General parameters
    ------------------

    --sessions          The batch.txt file with all the sessions
                        information. [batch.txt]
    --sessionsfolder    The path to the study/sessions folder, where the
                        imaging  data is supposed to go. [.]
    --parsessions       How many sessions to run in parallel. [1]
    --overwrite         Whether to overwrite existing data (yes)
                        or not (no). [no]
    --hcp_suffix        Specifies a suffix to the session id if multiple
                        variants are run, empty otherwise. []
    --logfolder         The path to the folder where runlogs and comlogs
                        are to be stored, if other than default [].
    --log               Whether to keep ('keep') or remove ('remove') the
                        temporary logs once jobs are completed. ['keep']
                        When a comma or pipe ('|') separated list is given,
                        the log will be created at the first provided
                        location and then linked or copied to other
                        locations. The valid locations are:

                        - 'study' (for the default:
                          `<study>/processing/logs/comlogs` location)
                        - 'session' (for `<sessionid>/logs/comlogs`)
                        - 'hcp' (for `<hcp_folder>/logs/comlogs`)
                        - '<path>' (for an arbitrary directory)

    Specific parameters
    -------------------

    In addition the following *specific* parameters will be used to guide the
    processing in this step:

    --hcp_icafix_bolds              List of bolds on which ICAFix was applied,
                                    with the same format as for ICAFix.
                                    Typically, this should be identical to the
                                    list used in the ICAFix run [same default
                                    as for hcp_icafix and hcp_msmall].
    --hcp_resample_concatregname    Output name of the dedrifted registration.
                                    [MSMAll]
    --hcp_resample_regname          Registration sphere name.
                                    [<hcp_msmall_outregname>_2_d40_WRN]
    --hcp_icafix_highpass           Value for the highpass filter, [0] for
                                    multi-run HCP ICAFix and [2000] for
                                    single-run HCP ICAFix. Should be identical
                                    to the value used for ICAFIX.
    --hcp_hiresmesh                 High resolution mesh node count. [164]
    --hcp_lowresmeshes              Low resolution meshes node count. To
                                    provide more values separate them with
                                    commas. [32]
    --hcp_resample_reg_files        Comma separated paths to the spheres
                                    output from the MSMRemoveGroupDrift
                                    pipeline
                                    [<HCPPIPEDIR>/global/templates/MSMAll/<file1>,
                                    <HCPPIPEDIR>/global/templates/MSMAll/<file2>].
                                    Where <file1> is equal to:
                                    DeDriftingGroup.L.sphere.DeDriftMSMAll.
                                    164k_fs_LR.surf.gii and <file2> is equal
                                    to DeDriftingGroup.R.sphere.DeDriftMSMAll.
                                    164k_fs_LR.surf.gii
    --hcp_resample_maps             Comma separated paths to maps that will
                                    have the MSMAll registration applied that
                                    are not myelin maps
                                    [sulc,curvature,corrThickness,thickness].
    --hcp_resample_myelinmaps       Comma separated paths to myelin maps
                                    [MyelinMap,SmoothedMyelinMap].
    --hcp_bold_smoothFWHM           Smoothing FWHM that matches what was
                                    used in the fMRISurface pipeline. [2]
    --hcp_matlab_mode               Specifies the Matlab version, can be
                                    interpreted, compiled or octave.
                                    [compiled]
    --hcp_icafix_domotionreg        Whether to regress motion parameters as
                                    part of the cleaning. The default value
                                    after a single-run HCP ICAFix is [TRUE],
                                    while the default after a multi-run HCP
                                    ICAFix is [FALSE].
    --hcp_resample_dontfixnames     A list of comma separated bolds that will
                                    not have HCP ICAFix reapplied to them.
                                    Only applicable if single-run ICAFix was
                                    used. Generally not recommended. [NONE]
    --hcp_resample_myelintarget     A myelin target file is required to run
                                    this pipeline when using a different mesh
                                    resolution than the original
                                    MSMAll registration. [NONE]
    --hcp_resample_inregname        A string to enable multiple fMRI
                                    resolutions (e.g._1.6mm). [NONE]

    OUTPUTS
    =======

    The results of this step will be populated in the MNINonLinear folder inside
    the same sessions's root hcp folder.


    EXAMPLE USE
    ===========

    ::

        # HCP DeDriftAndResample after application of single-run ICAFix
        qunex hcp_dedrift_and_resample \\
            --sessions=processing/batch.txt \\
            --sessionsfolder=sessions \\
            --hcp_icafix_bolds="REST_1,REST_2,TASK_1,TASK_2" \\
            --hcp_matlab_mode="interpreted"

    ::

        # HCP DeDriftAndResample after application of multi-run ICAFix
        qunex hcp_dedrift_and_resample \\
            --sessions=processing/batch.txt \\
            --sessionsfolder=sessions \\
            --hcp_icafix_bolds="GROUP_1:REST_1,REST_2,TASK_1|GROUP_2:REST_3,TASK_2" \\
            --hcp_matlab_mode="interpreted"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP DeDriftAndResample registration [%s] ..." % (pc.action("Running", options['run']), options['hcp_processing_mode'])

    run    = True
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        # --- Base settings
        pc.doOptionsCheck(options, sinfo, 'hcp_dedrift_and_resample')
        doHCPOptionsCheck(options, sinfo, 'hcp_dedrift_and_resample')
        hcp = getHCPPaths(sinfo, options)

        # --- Get sorted bold numbers and bold data
        bolds, bskip, report['boldskipped'], r = pc.useOrSkipBOLD(sinfo, options, r)
        if report['boldskipped']:
            if options['hcp_filename'] == 'original':
                report['skipped'] = [bi.get('filename', str(bn)) for bn, bnm, bt, bi in bskip]
            else:
                report['skipped'] = [str(bn) for bn, bnm, bt, bi in bskip]

        # --- Parse msmall_bolds
        singleRun, icafixBolds, dedriftGroups, parsOK, r = parseICAFixBolds(options, bolds, r, True)

        if not parsOK:
            raise ge.CommandFailed("hcp_dedrift_and_resample", "... invalid input parameters!")

        # --- Execute
        # single-run
        if singleRun:
            # process
            result = executeHCPSingleDeDriftAndResample(sinfo, options, overwrite, hcp, run, dedriftGroups[0])
        # multi-run
        else:
            # process
            result = executeHCPMultiDeDriftAndResample(sinfo, options, overwrite, hcp, run, dedriftGroups)

        # merge r
        r += result['r']

        # merge report
        tempReport            = result['report']
        report['done']       += tempReport['done']
        report['incomplete'] += tempReport['incomplete']
        report['failed']     += tempReport['failed']
        report['ready']      += tempReport['ready']
        report['not ready']  += tempReport['not ready']
        report['skipped']    += tempReport['skipped']

        # report
        rep = []
        for k in ['done', 'incomplete', 'failed', 'ready', 'not ready', 'skipped']:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (sinfo['id'], "HCP DeDriftAndResample: " + "; ".join(rep), len(report['failed'] + report['incomplete'] + report['not ready']))

    except ge.CommandFailed as e:
        r +=  "\n\nERROR in completing %s:\n     %s\n" % (e.function, "\n     ".join(e.report))
        report = (sinfo['id'], 'HCP DeDriftAndResample failed')
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        report = (sinfo['id'], 'HCP DeDriftAndResample failed')
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        report = (sinfo['id'], 'HCP DeDriftAndResample failed')

    r += "\n\nHCP DeDriftAndResample %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, report)


def executeHCPSingleDeDriftAndResample(sinfo, options, overwrite, hcp, run, group):
    # prepare return variables
    r = ""
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        # regname
        regname = "%s_2_d40_WRN" % options['hcp_msmall_outregname']
        if options['hcp_resample_regname'] is not None:
            regname = options['hcp_resample_regname']

        # get group data
        bolds = group["bolds"]

        r += "\n\n------------------------------------------------------------"
        r += "\n---> %s DeDriftAndResample" % (pc.action("Processing", options['run']))
        boldsok = True

        # --- check for bold images and prepare targets parameter
        boldtargets = ""

        # highpass
        highpass = 2000 if options['hcp_icafix_highpass'] is not None else options['hcp_icafix_highpass']

        # check if files for all bolds exist
        for b in bolds:
            # set ok to true for now
            boldok = True

            # extract data
            printbold, _, _, boldinfo = b

            if 'filename' in boldinfo and options['hcp_filename'] == 'original':
                printbold  = boldinfo['filename']
                boldtarget = boldinfo['filename']
            else:
                printbold  = str(printbold)
                boldtarget = "%s%s" % (options['hcp_bold_prefix'], printbold)

            # input file check
            boldimg = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s_hp%s_clean.nii.gz" % (boldtarget, highpass))
            r, boldok = pc.checkForFile2(r, boldimg, '\n     ... bold image %s present' % boldtarget, '\n     ... ERROR: bold image [%s] missing!' % boldimg, status=boldok)

            if not boldok:
                boldsok = False

            # add @ separator
            if boldtargets is not "":
                boldtargets = boldtargets + "@"

            # add latest image
            boldtargets = boldtargets + boldtarget

        # matlab run mode, compiled=0, interpreted=1, octave=2
        if options['hcp_matlab_mode'] == "compiled":
            matlabrunmode = 0
        elif options['hcp_matlab_mode'] == "interpreted":
            matlabrunmode = 1
        elif options['hcp_matlab_mode'] == "octave":
            matlabrunmode = 2
        else:
            r += "\n     ... ERROR: wrong value for the hcp_matlab_mode parameter!"
            boldsok = False

        # dedrift reg files
        regfiles = hcp['hcp_base'] + "/global/templates/MSMAll/DeDriftingGroup.L.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii" + "@" + hcp['hcp_base'] + "/global/templates/MSMAll/DeDriftingGroup.R.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii"
        if options['hcp_resample_reg_files'] is not None:
            regfiles = options['hcp_resample_reg_files'].replace(",", "@")

        comm = '%(script)s \
            --path="%(path)s" \
            --subject="%(subject)s" \
            --high-res-mesh="%(highresmesh)s" \
            --low-res-meshes="%(lowresmeshes)s" \
            --registration-name="%(regname)s" \
            --dedrift-reg-files="%(regfiles)s" \
            --concat-reg-name="%(concatregname)s" \
            --maps="%(maps)s" \
            --myelin-maps="%(myelinmaps)s" \
            --multirun-fix-names="NONE" \
            --multirun-fix-concat-names="NONE" \
            --fix-names="%(fixnames)s" \
            --dont-fix-names="%(dontfixnames)s" \
            --smoothing-fwhm="%(smoothingfwhm)s" \
            --high-pass="%(highpass)d" \
            --matlab-run-mode="%(matlabrunmode)d" \
            --motion-regression="%(motionregression)s" \
            --myelin-target-file="%(myelintargetfile)s" \
            --input-reg-name="%(inputregname)s"' % {
                'script'              : os.path.join(hcp['hcp_base'], 'DeDriftAndResample', 'DeDriftAndResamplePipeline.sh'),
                'path'                : sinfo['hcp'],
                'subject'             : sinfo['id'] + options['hcp_suffix'],
                'highresmesh'         : options['hcp_highresmesh'],
                'lowresmeshes'        : options['hcp_lowresmeshes'].replace(",", "@"),
                'regname'             : regname,
                'regfiles'            : regfiles,
                'concatregname'       : options['hcp_resample_concatregname'],
                'maps'                : options['hcp_resample_maps'].replace(",", "@"),
                'myelinmaps'          : options['hcp_resample_myelinmaps'].replace(",", "@"),
                'fixnames'            : boldtargets,
                'dontfixnames'        : options['hcp_resample_dontfixnames'].replace(",", "@"),
                'smoothingfwhm'       : options['hcp_bold_smoothFWHM'],
                'highpass'            : int(highpass),
                'matlabrunmode'       : matlabrunmode,
                'motionregression'    : "TRUE" if options['hcp_icafix_domotionreg'] is None else options['hcp_icafix_domotionreg'],
                'myelintargetfile'    : options['hcp_resample_myelintarget'],
                'inputregname'        : options['hcp_resample_inregname']}

        # -- Report command
        if boldsok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test file (currently check only last bold)
        lastbold = boldtargets.split("@")[-1]
        tfile = os.path.join(hcp['hcp_nonlin'], 'Results', lastbold, "%s%s_%s.dtseries.nii" % (lastbold, options['hcp_cifti_tail'], options['hcp_resample_concatregname']))
        fullTest = None

        # -- Run
        if run and boldsok:
            if options['run'] == "run":
                r, endlog, _, failed = pc.runExternalForFile(tfile, comm, 'Running HCP DeDriftAndResample', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task="hcp_dedrift_and_resample", logfolder=options['comlogs'], logtags=[options['logtag'], regname], fullTest=fullTest, shell=True, r=r)

                if failed:
                    report['failed'].append(regname)
                else:
                    report['done'].append(regname)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(tfile, fullTest, 'HCP DeDriftAndResample', r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP DeDriftAndResample can be run"
                    report['ready'].append(regname)
                else:
                    report['skipped'].append(regname)

        elif run:
            report['not ready'].append(regname)
            if options['run'] == "run":
                r += "\n---> ERROR: images missing, skipping this group!"
            else:
                r += "\n---> ERROR: images missing, this group would be skipped!"
        else:
            report['not ready'].append(regname)
            if options['run'] == "run":
                r += "\n---> ERROR: No hcp info for session, skipping this BOLD!"
            else:
                r += "\n---> ERROR: No hcp info for session, this BOLD would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = "\n\n\n --- Failed during processing of group %s with error:\n" % ("DeDriftAndResample")
        r += str(errormessage)
        report['failed'].append(regname)
    except:
        r += "\n --- Failed during processing of group %s with error:\n %s\n" % ("DeDriftAndResample", traceback.format_exc())
        report['failed'].append(regname)

    return {'r': r, 'report': report}


def executeHCPMultiDeDriftAndResample(sinfo, options, overwrite, hcp, run, groups):
    # prepare return variables
    r = ""
    report = {'done': [], 'incomplete': [], 'failed': [], 'ready': [], 'not ready': [], 'skipped': []}

    try:
        r += "\n\n------------------------------------------------------------"
        r += "\n---> %s DeDriftAndResample" % (pc.action("Processing", options['run']))

        # --- check for bold images and prepare targets parameter
        groupList = []
        grouptargets = ""
        boldList = []
        boldtargets = ""

        # highpass
        highpass = 0 if options['hcp_icafix_highpass'] is None else options['hcp_icafix_highpass']

        # runok
        runok = True

        # check if files for all bolds exist
        for g in groups:
            # get group data
            groupname = g["name"]
            bolds = g["bolds"]

            # for storing bolds
            groupbolds = ""

            for b in bolds:
                # extract data
                printbold, _, _, boldinfo = b

                if 'filename' in boldinfo and options['hcp_filename'] == 'original':
                    printbold  = boldinfo['filename']
                    boldtarget = boldinfo['filename']
                else:
                    printbold  = str(printbold)
                    boldtarget = "%s%s" % (options['hcp_bold_prefix'], printbold)

                # input file check
                boldimg = os.path.join(hcp['hcp_nonlin'], 'Results', boldtarget, "%s_hp%s_clean.nii.gz" % (boldtarget, highpass))
                r, boldok = pc.checkForFile2(r, boldimg, '\n     ... bold image %s present' % boldtarget, '\n     ... ERROR: bold image [%s] missing!' % boldimg)

                if not boldok:
                    runok = False

                # add @ separator
                if groupbolds is not "":
                    groupbolds = groupbolds + "@"

                # add latest image
                boldList.append(boldtarget)
                groupbolds = groupbolds + boldtarget

            # check if group file exists
            groupica = "%s_hp%s_clean.nii.gz" % (groupname, highpass)
            groupimg = os.path.join(hcp['hcp_nonlin'], 'Results', groupname, groupica)
            r, groupok = pc.checkForFile2(r, groupimg, '\n     ... ICA %s present' % groupname, '\n     ... ERROR: ICA [%s] missing!' % groupimg)

            if not groupok:
                runok = False

            # add @ or % separator
            if grouptargets is not "":
                grouptargets = grouptargets + "@"
                boldtargets = boldtargets + "%"

            # add latest group
            groupList.append(groupname)
            grouptargets = grouptargets + groupname
            boldtargets = boldtargets + groupbolds

        # matlab run mode, compiled=0, interpreted=1, octave=2
        if options['hcp_matlab_mode'] == "compiled":
            matlabrunmode = 0
        elif options['hcp_matlab_mode'] == "interpreted":
            matlabrunmode = 1
        elif options['hcp_matlab_mode'] == "octave":
            matlabrunmode = 2
        else:
            r += "\n---> ERROR: wrong value for the hcp_matlab_mode parameter!"
            runok = False

        # dedrift reg files
        regfiles = hcp['hcp_base'] + "/global/templates/MSMAll/DeDriftingGroup.L.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii" + "@" + hcp['hcp_base'] + "/global/templates/MSMAll/DeDriftingGroup.R.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii"
        if options['hcp_resample_reg_files'] is not None:
            regfiles = options['hcp_resample_reg_files'].replace(",", "@")

        # regname
        regname = "%s_2_d40_WRN" % options['hcp_msmall_outregname']
        if options['hcp_resample_regname'] is not None:
            regname = options['hcp_resample_regname']

        comm = '%(script)s \
            --path="%(path)s" \
            --subject="%(subject)s" \
            --high-res-mesh="%(highresmesh)s" \
            --low-res-meshes="%(lowresmeshes)s" \
            --registration-name="%(regname)s" \
            --dedrift-reg-files="%(regfiles)s" \
            --concat-reg-name="%(concatregname)s" \
            --maps="%(maps)s" \
            --myelin-maps="%(myelinmaps)s" \
            --multirun-fix-names="%(mrfixnames)s" \
            --multirun-fix-concat-names="%(mrfixconcatnames)s" \
            --fix-names="NONE" \
            --dont-fix-names="%(dontfixnames)s" \
            --smoothing-fwhm="%(smoothingfwhm)s" \
            --high-pass="%(highpass)d" \
            --matlab-run-mode="%(matlabrunmode)d" \
            --motion-regression="%(motionregression)s" \
            --myelin-target-file="%(myelintargetfile)s" \
            --input-reg-name="%(inputregname)s"' % {
                'script'              : os.path.join(hcp['hcp_base'], 'DeDriftAndResample', 'DeDriftAndResamplePipeline.sh'),
                'path'                : sinfo['hcp'],
                'subject'             : sinfo['id'] + options['hcp_suffix'],
                'highresmesh'         : options['hcp_hiresmesh'],
                'lowresmeshes'        : options['hcp_lowresmeshes'].replace(",", "@"),
                'regname'             : regname,
                'regfiles'            : regfiles,
                'concatregname'       : options['hcp_resample_concatregname'],
                'maps'                : options['hcp_resample_maps'].replace(",", "@"),
                'myelinmaps'          : options['hcp_resample_myelinmaps'].replace(",", "@"),
                'mrfixnames'          : boldtargets,
                'mrfixconcatnames'    : grouptargets,
                'dontfixnames'        : options['hcp_resample_dontfixnames'].replace(",", "@"),
                'smoothingfwhm'       : options['hcp_bold_smoothFWHM'],
                'highpass'            : int(highpass),
                'matlabrunmode'       : matlabrunmode,
                'motionregression'    : "FALSE" if options['hcp_icafix_domotionreg'] is not None else options['hcp_icafix_domotionreg'],
                'myelintargetfile'    : options['hcp_resample_myelintarget'],
                'inputregname'        : options['hcp_resample_inregname']}

        # -- Additional parameters
        # -- hcp_resample_extractnames
        if options['hcp_resample_extractnames'] is not None:
            # variables for storing
            extractnames = ""
            extractconcatnames = ""

            # split to groups
            ens = options['hcp_resample_extractnames'].split("|")
            # iterate
            for en in ens:
                en_split = en.split(":")
                concatname = en_split[0]

                # if none all is good
                if (concatname.upper() == "NONE"):
                    concatname = concatname.upper()
                    boldnames = "NONE"
                # wrong input
                elif len(en_split) == 0:
                    runok = False
                    r += "\n---> ERROR: invalid input, check the hcp_resample_extractnames parameter!"
                # else check if concatname is in groups
                else:
                    # extract fix names ok?
                    fixnames = en_split[1].split(",")
                    for fn in fixnames:
                        # extract fixname name ok?
                        if fn not in boldList:
                            runok = False
                            r += "\n---> ERROR: extract fix name [%s], not found in provided fix names!" % fn

                    if len(en_split) > 0:
                        boldnames = en_split[1].replace(",", "@")

                # add @ or % separator
                if extractnames is not "":
                    extractconcatnames = extractconcatnames + "@"
                    extractnames = extractnames + "%"

                # add latest group
                extractconcatnames = extractconcatnames + concatname
                extractnames = extractnames + boldnames

            # append to command
            comm += '             --multirun-fix-extract-names="%s"' % extractnames
            comm += '             --multirun-fix-extract-concat-names="%s"' % extractconcatnames

        # -- hcp_resample_extractextraregnames
        if options['hcp_resample_extractextraregnames'] is not None:
            comm += '             --multirun-fix-extract-extra-regnames="%s"' % options['hcp_resample_extractextraregnames']

        # -- hcp_resample_extractvolume
        if options['hcp_resample_extractvolume'] is not None:
            extractvolume = options['hcp_resample_extractvolume'].upper()

            # check value
            if extractvolume != "TRUE" and extractvolume != "FALSE":
                runok = False
                r += "\n---> ERROR: invalid extractvolume parameter [%s], expecting TRUE or FALSE!" % extractvolume

            # append to command
            comm += '             --multirun-fix-extract-volume="%s"' % extractvolume

        # -- Report command
        if runok:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test file
        tfile = os.path.join(hcp['hcp_nonlin'], 'Results', groupname, "%s%s_%s_hp%s_clean.dtseries.nii" % (groupname, options['hcp_cifti_tail'], options['hcp_resample_concatregname'], highpass))
        fullTest = None

        # -- Run
        if run and runok:
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, endlog, _, failed = pc.runExternalForFile(tfile, comm, 'Running HCP DeDriftAndResample', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task="hcp_dedrift_and_resample", logfolder=options['comlogs'], logtags=[options['logtag'], groupname], fullTest=fullTest, shell=True, r=r)

                if failed:
                    report['failed'].append(grouptargets)
                else:
                    report['done'].append(grouptargets)

            # -- just checking
            else:
                passed, _, r, failed = pc.checkRun(tfile, fullTest, 'HCP DeDriftAndResample', r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP DeDriftAndResample can be run"
                    report['ready'].append(grouptargets)
                else:
                    report['skipped'].append(grouptargets)

        elif run:
            report['not ready'].append(grouptargets)
            if options['run'] == "run":
                r += "\n---> ERROR: images missing, skipping this group!"
            else:
                r += "\n---> ERROR: images missing, this group would be skipped!"
        else:
            report['not ready'].append(grouptargets)
            if options['run'] == "run":
                r += "\n---> ERROR: No hcp info for session, skipping this BOLD!"
            else:
                r += "\n---> ERROR: No hcp info for session, this BOLD would be skipped!"

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = "\n\n\n --- Failed during processing of group %s with error:\n" % ("DeDriftAndResample")
        r += str(errormessage)
        report['failed'].append(grouptargets)
    except:
        r += "\n --- Failed during processing of group %s with error:\n %s\n" % ("DeDriftAndResample", traceback.format_exc())
        report['failed'].append(grouptargets)

    return {'r': r, 'report': report}


def hcp_dtifit(sinfo, options, overwrite=False, thread=0):
    """
    hcp_dtifit - documentation not yet available.
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP DTI Fix ..." % (pc.action("Running", options['run']))

    run    = True
    report = "Error"

    try:
        pc.doOptionsCheck(options, sinfo, 'hcp_dtifit')
        doHCPOptionsCheck(options, sinfo, 'hcp_dtifit')
        hcp = getHCPPaths(sinfo, options)

        if 'hcp' not in sinfo:
            r += "---> ERROR: There is no hcp info for session %s in batch.txt" % (sinfo['id'])
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

        # -- Report command
        if run:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- Test files

        tfile = os.path.join(hcp['T1w_folder'], 'Diffusion', 'dti_FA.nii.gz')

        # -- Run

        if run:

            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, _, report, failed = pc.runExternalForFile(tfile, comm, 'Running HCP DTI Fit', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=options['logtag'], shell=True, r=r)


            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(tfile, None, 'HCP DTI Fit', r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP DTI Fit can be run"
                    report = "HCP DTI Fit FS can be run"
                    failed = 0

        else:
            r += "---> Session can not be processed."
            report = "HCP DTI Fit can not be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        failed = 1

    r += "\n\nHCP Diffusion Preprocessing %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, (sinfo['id'], report, failed))


def hcp_bedpostx(sinfo, options, overwrite=False, thread=0):
    """
    hcp_bedpostx - documentation not yet available.
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP Bedpostx GPU ..." % (pc.action("Running", options['run']))

    run    = True
    report = "Error"

    try:
        pc.doOptionsCheck(options, sinfo, 'hcp_bedpostx')
        doHCPOptionsCheck(options, sinfo, 'hcp_bedpostx')
        hcp = getHCPPaths(sinfo, options)

        if 'hcp' not in sinfo:
            r += "---> ERROR: There is no hcp info for session %s in batch.txt" % (sinfo['id'])
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

        # -- Report command
        if run:
            r += "\n\n------------------------------------------------------------\n"
            r += "Running HCP Pipelines command via QuNex:\n\n"
            r += comm.replace("--", "\n    --").replace("             ", "")
            r += "\n------------------------------------------------------------\n"

        # -- test files

        tfile = os.path.join(hcp['T1w_folder'], 'Diffusion.bedpostX', 'mean_fsumsamples.nii.gz')

        # -- run

        if run:
            if options['run'] == "run":
                if overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, _, report, failed = pc.runExternalForFile(tfile, comm, 'Running HCP BedpostX', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=options['logtag'], shell=True, r=r)

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(tfile, None, 'HCP BedpostX', r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP BedpostX can be run"
                    report = "HCP BedpostX can be run"
                    failed = 0

        else:
            r += "---> Session can not be processed."
            report = "HCP BedpostX can not be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        failed = 1

    r += "\n\nHCP Diffusion Preprocessing %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    print r
    return (r, (sinfo['id'], report, failed))


def map_hcp_data(sinfo, options, overwrite=False, thread=0):
    """
    ``map_hcp_data [... processing options]``

    Maps the results of the HCP preprocessing.

    * T1w.nii.gz                            -> images/structural/T1w.nii.gz
    * aparc+aseg.nii.gz                     -> images/segmentation/freesurfer/mri/aparc+aseg_t1.nii.gz
                                            -> images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz
                                               (2mm iso downsampled version)
    * fsaverage_LR32k/*                     -> images/segmentation/hcp/fsaverage_LR32k
    * BOLD_[N][hcp_nifti_tail].nii.gz       -> images/functional/[boldname][N][qx_nifti_tail].nii.gz
    * BOLD_[N][hcp_cifti_tail].dtseries.nii -> images/functional/[boldname][N][qx_cifti_tail].dtseries.nii
    * Movement_Regressors.txt               -> images/functional/movement/[boldname][N]_mov.dat

    INPUTS
    ======

    The relevant processing parameters are:

    --sessions              The batch.txt file with all the session information.
                            [batch.txt]
    --sessionsfolder        The path to the study/sessions folder, where the
                            imaging data is supposed to go. [.]
    --parsessions           How many sessions to run in parallel. [1]
    --overwrite             Whether to overwrite existing data (yes) or not
                            (no). [no]
    --hcp_suffix            Specifies a suffix to the session id if multiple
                            variants are run, empty otherwise. []
    --hcp_bold_variant      Optional variant of HCP BOLD preprocessing. If
                            specified, the results will be copied/linked from
                            `Results<hcp_bold_variant>`. []
    --bolds                 Which bold images (as they are specified in the
                            batch.txt file) to copy over. It can be a single
                            type (e.g. 'task'), a pipe separated list (e.g.
                            'WM|Control|rest') or 'all' to copy all. [all]
    --boldname              The prefix for the fMRI files in the images folder.
                            [bold]
    --img_suffix            Specifies a suffix for 'images' folder to enable
                            support for multiple parallel workflows. Empty
                            if not used. []
    --qx_nifti_tail         The tail to use for the mapped volume files in the
                            QuNex file structure. If not specified or if set
                            to 'None', the value of hcp_nifti_tail will be used.
    --qx_cifti_tail         The tail to use for the mapped cifti files in the
                            QuNex file structure. If not specified or if set
                            to 'None', the value of hcp_cifti_tail will be used.
    --bold_variant          Optional variant for functional images. If
                            specified, functional images will be mapped into
                            `functional<bold_variant>` folder. []

    The parameters can be specified in command call or session.txt file.
    If possible, the files are not copied but rather hard links are created to
    save space. If hard links can not be created, the files are copied.

    Specific attention needs to be paid to the use of `hcp_nifti_tail`,
    `hcp_cifti_tail`, `hcp_suffix`, and `hcp_bold_variant` that relate to
    file location and naming within the HCP folder structure and
    `qx_nifti_tail`, `qx_cifti_tail`, `img_suffix`, and `bold_variant` that
    relate to file and folder naming within the QuNex folder structure.

    `hcp_suffix` parameter enables the use of a parallel HCP minimal processing
    stream. To enable the same separation in the QuNex folder structure,
    `img_suffix` parameter has to be set. In this case HCP data will be mapped
    to `<sessionsfolder>/<session id>/images<img_suffix>` folder instead of the
    default `<sessionsfolder>/<session id>/images` folder.

    Similarly, if separate variants of bold image processing were run, and the
    results were stored in `MNINonLinear/Results<hcp_bold_variant>`, the
    `hcp_bold_variant` parameter needs to be set to map the data from the
    correct location. `bold_variant` parameter on the other hand enables
    continued parallel processing of bold data in the QuNex folder structure
    by mapping bold data to `functional<bold_variant>` folder instead of the
    default `functional` folder.

    Based on HCP minimal preprocessing choices, both CIFTI and NIfTI volume
    files can be marked using different tails. E.g. CIFT files are marked with
    an `_Atlas` tail, NIfTI files are marked with `_hp2000_clean` tail after
    employing ICAFIX procedure. When mapping the data, it is important that
    the correct files are mapped. The correct tails for NIfTI volume, and
    CIFTI files are specified using the `hcp_nifti_tail` and `hcp_cifti_tail`
    parameters. When the data is mapped into QuNex folder structure the tails
    to be used for NIfTI and CIFTI data are specified with `qx_nifti_tail` and
    `qx_cifti_tail` parameters, respectively. If the `qx_*_tail` parameters
    are not provided explicitly, the values specified in the `hcp_*_tail`
    parameters will be used.

    USE
    ===

    map_hcp_data maps the results of the HCP preprocessing (in MNINonLinear) to
    the `<sessionsfolder>/<session id>/images<img_suffix>` folder structure.
    Specifically, it copies the files and folders:

    - T1w.nii.gz
        - images<img_suffix>/structural/T1w.nii.gz
    - aparc+aseg.nii.gz
        - images<img_suffix>/segmentation/freesurfer/mri/aparc+aseg_t1.nii.gz
        - images<img_suffix>/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz (2mm iso downsampled version)
    - fsaverage_LR32k/*
        - images<img_suffix>/segmentation/hcp/fsaverage_LR32k
    - BOLD_[N]<hcp_nifti_tail>.nii.gz
        - images<img_suffix>/functional<bold variant>/<boldname>[N]<qx_nifti_tail>.nii.gz
    - BOLD_[N]<hcp_cifti_tail>.dtseries.nii
        - images<img_suffix>/functional<bold variant>/<boldname>[N]<qx_cifti_tail>.dtseries.nii
    - Movement_Regressors.txt
        - images<img_suffix>/functional<bold variant>/movement/<boldname>[N]_mov.dat

    EXAMPLE USE
    ===========

    ::

        qunex map_hcp_data sessions=fcMRI/sessions_hcp.txt sessionsfolder=sessions \\
              overwrite=no hcp_cifti_tail=_Atlas bolds=all
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\nMapping HCP data ... \n"
    r += "\n   The command will map the results of the HCP preprocessing from sessions's hcp\n   to sessions's images folder. It will map the T1 structural image, aparc+aseg \n   segmentation in both high resolution as well as one downsampled to the \n   resolution of BOLD images. It will map the 32k surface mapping data, BOLD \n   data in volume and cifti representation, and movement correction parameters. \n\n   Please note: when mapping the BOLD data, two parameters are key: \n\n   --bolds parameter defines which BOLD files are mapped based on their\n     specification in batch.txt file. Please see documentation for formatting. \n        If the parameter is not specified the default value is 'all' and all BOLD\n        files will be mapped. \n\n   --hcp_nifti_tail and --hcp_cifti_tail specifiy which kind of the nifti and cifti files will be copied over. \n     The tail is added after the boldname[N] start. If the parameters are not specified \n     explicitly the default is ''.\n\n   Based on settings:\n\n    * %s BOLD files will be copied\n    * '%s' nifti tail will be used\n    * '%s' cifti tail will be used." % (", ".join(options['bolds'].split("|")), options['hcp_nifti_tail'], options['hcp_cifti_tail'])
    if any([options['hcp_suffix'], options['img_suffix']]) :
        r += "\n   Based on --hcp_suffix and --img_suffix parameters, the files will be mapped from hcp/%s%s/MNINonLinear to 'images%s' folder!" % (sinfo['id'], options['hcp_suffix'], options['img_suffix'])
    if any([options['hcp_bold_variant'], options['bold_variant']]) :
        r += "\n   Based on --hcp_bold_variant and --bold_variant parameters, the files will be mapped from MNINonLinear/Results%s to 'images%s/functional%s folder!" % (options['hcp_bold_variant'], options['img_suffix'], options['bold_variant'])
    r += "\n\n........................................................"

    # --- file/dir structure


    f = pc.getFileNames(sinfo, options)
    d = pc.getSessionFolders(sinfo, options)

    #    MNINonLinear/Results/<boldname>/<boldname>.nii.gz -- volume
    #    MNINonLinear/Results/<boldname>/<boldname>_Atlas.dtseries.nii -- cifti
    #    MNINonLinear/Results/<boldname>/Movement_Regressors.txt -- movement
    #    MNINonLinear/T1w.nii.gz -- atlas T1 hires
    #    MNINonLinear/aparc+aseg.nii.gz -- FS hires segmentation

    # ------------------------------------------------------------------------------------------------------------
    #                                                                                      map T1 and segmentation

    report = {}
    failed = 0

    r += "\n\nSource folder: " + d['hcp']
    r += "\nTarget folder: " + d['s_images']

    r += "\n\nStructural data: ..."
    status = True

    if os.path.exists(f['t1']) and not overwrite:
        r += "\n ... T1 ready"
        report['T1'] = 'present'
    else:
        status, r = gc.linkOrCopy(os.path.join(d['hcp'], 'MNINonLinear', 'T1w.nii.gz'), f['t1'], r, status, "T1")
        report['T1'] = 'copied'

    if os.path.exists(f['fs_aparc_t1']) and not overwrite:
        r += "\n ... highres aseg+aparc ready"
        report['hires aseg+aparc'] = 'present'
    else:
        status, r = gc.linkOrCopy(os.path.join(d['hcp'], 'MNINonLinear', 'aparc+aseg.nii.gz'), f['fs_aparc_t1'], r, status, "highres aseg+aparc")
        report['hires aseg+aparc'] = 'copied'

    if os.path.exists(f['fs_aparc_bold']) and not overwrite:
        r += "\n ... lowres aseg+aparc ready"
        report['lores aseg+aparc'] = 'present'
    else:
        if os.path.exists(f['fs_aparc_bold']):
            os.remove(f['fs_aparc_bold'])
        if os.path.exists(os.path.join(d['hcp'], 'MNINonLinear', 'T1w_restore.2.nii.gz')) and os.path.exists(f['fs_aparc_t1']):
            # prepare logtags
            if options['logtag'] != "":
                options['logtag'] += "_"
            logtags = options['logtag'] + "%s-flirt_%s" % (options['command_ran'], sinfo['id'])

            _, endlog, _, failedcom = pc.runExternalForFile(f['fs_aparc_bold'], 'flirt -interp nearestneighbour -ref %s -in %s -out %s -applyisoxfm 2' % (os.path.join(d['hcp'], 'MNINonLinear', 'T1w_restore.2.nii.gz'), f['fs_aparc_t1'], f['fs_aparc_bold']), ' ... resampling t1 cortical segmentation (%s) to bold space (%s)' % (os.path.basename(f['fs_aparc_t1']), os.path.basename(f['fs_aparc_bold'])), overwrite=overwrite, remove=options['log'] == 'remove', logfolder=options['comlogs'], logtags=logtags, shell=True)
            if failedcom:
                report['lores aseg+aparc'] = 'failed'
                failed += 1
            else:
                report['lores aseg+aparc'] = 'generated'
        else:
            r += "\n ... ERROR: could not generate downsampled aseg+aparc, files missing!"
            report['lores aseg+aparc'] = 'failed'
            status = False
            failed += 1

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
                if gc.linkOrCopy(sfile, tfile):
                    ncp += 1
                else:
                    r += "\n     -> ERROR: could not map or copy %s" % (sfile)
                    report['surface'] = 'error'
                    failed += 1
        if npre:
            r += "\n     -> %d files already copied" % (npre)
        if ncp:
            r += "\n     -> copied %d surface files" % (ncp)
    else:
        r += "\n ... ERROR: missing folder: %s!" % (os.path.join(d['hcp'], 'MNINonLinear', 'fsaverage_LR32k'))
        status = False
        report['surface'] = 'error'
        failed += 1

    # ------------------------------------------------------------------------------------------------------------
    #                                                                                          map functional data

    r += "\n\nFunctional data: \n ... mapping %s BOLD files\n ... mapping '%s' hcp nifti tail to '%s' qx nifti tail\n ... mapping '%s' hcp cifti tail to '%s' qx cifti tail\n" % (", ".join(options['bolds'].split("|")), options['hcp_nifti_tail'], options['qx_nifti_tail'], options['hcp_cifti_tail'], options['qx_cifti_tail'])

    report['boldok'] = 0
    report['boldfail'] = 0
    report['boldskipped'] = 0

    bolds, skipped, report['boldskipped'], r = pc.useOrSkipBOLD(sinfo, options, r)

    for boldnum, boldname, boldtask, boldinfo in bolds:

        r += "\n ... " + boldname

        # --- filenames
        f.update(pc.getBOLDFileNames(sinfo, boldname, options))

        status = True
        hcp_bold_name = ""

        try:
            # -- get source bold name

            if 'filename' in boldinfo and options['hcp_filename'] == 'original':
                hcp_bold_name = boldinfo['filename']
            elif 'bold' in boldinfo:
                hcp_bold_name = boldinfo['bold']
            else:
                hcp_bold_name = "%s%d" % (options['hcp_bold_prefix'], boldnum)

            # -- check if present and map

            hcp_bold_path = os.path.join(d['hcp'], 'MNINonLinear', 'Results' + options['hcp_bold_variant'], hcp_bold_name)

            if not os.path.exists(hcp_bold_path):
                r += "\n     ... ERROR: source folder does not exist [%s]!" % (hcp_bold_path)
                status = False

            else:
                if os.path.exists(f['bold_vol']) and not overwrite:
                    r += "\n     ... volume image ready"
                else:
                    # r += "\n     ... linking volume image \n         %s to\n         -> %s" % (os.path.join(hcp_bold_path, hcp_bold_name + '.nii.gz'), f['bold'])
                    status, r = gc.linkOrCopy(os.path.join(hcp_bold_path, hcp_bold_name + options['hcp_nifti_tail'] + '.nii.gz'), f['bold_qx_vol'], r, status, "volume image", "\n     ... ")

                if os.path.exists(f['bold_dts']) and not overwrite:
                    r += "\n     ... grayordinate image ready"
                else:
                    # r += "\n     ... linking cifti image\n         %s to\n         -> %s" % (os.path.join(hcp_bold_path, hcp_bold_name + options['hcp_cifti_tail'] + '.dtseries.nii'), f['bold_dts'])
                    status, r = gc.linkOrCopy(os.path.join(hcp_bold_path, hcp_bold_name + options['hcp_cifti_tail'] + '.dtseries.nii'), f['bold_qx_dts'], r, status, "grayordinate image", "\n     ... ")

                if os.path.exists(f['bold_mov']) and not overwrite:
                    r += "\n     ... movement data ready"
                else:
                    if os.path.exists(os.path.join(hcp_bold_path, 'Movement_Regressors.txt')):
                        mdata = [line.strip().split() for line in open(os.path.join(hcp_bold_path, 'Movement_Regressors.txt'))]
                        mfile = open(f['bold_mov'], 'w')
                        print >> mfile, "# Generated by QuNex %s on %s" % (gc.get_qunex_version(), datetime.now().strftime("%Y-%m-%d_%H.%M.%s"))
                        print >> mfile, "#"
                        print >> mfile, "#frame     dx(mm)     dy(mm)     dz(mm)     X(deg)     Y(deg)     Z(deg)"
                        c = 0
                        for mline in mdata:
                            if len(mline) >= 6:
                                c += 1
                                mline = "%6d   %s" % (c, "   ".join(mline[0:6]))
                                print >> mfile, mline.replace(' -', '-')
                        mfile.close()
                        r += "\n     ... movement data prepared"
                    else:
                        r += "\n     ... ERROR: could not prepare movement data, source does not exist: %s" % os.path.join(hcp_bold_path, 'Movement_Regressors.txt')
                        failed += 1
                        status = False

            if status:
                r += "\n     ---> Data ready!\n"
                report['boldok'] += 1
            else:
                r += "\n     ---> ERROR: Data missing, please check source!\n"
                report['boldfail'] += 1
                failed += 1

        except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
            r = str(errormessage)
            report['boldfail'] += 1
            failed += 1
        except:
            r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
            time.sleep(3)
            failed += 1

    if len(skipped) > 0:
        r += "\nThe following BOLD images were not mapped as they were not specified in\n'--bolds=\"%s\"':\n" % (options['bolds'])
        for boldnum, boldname, boldtask, boldinfo in skipped:
            if 'filename' in boldinfo and options['hcp_filename'] == 'original':
                r += "\n ... %s [task: '%s']" % (boldinfo['filename'], boldtask)
            else:
                r += "\n ... %s [task: '%s']" % (boldname, boldtask)

    r += "\n\nHCP data mapping completed on %s\n------------------------------------------------------------\n" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    rstatus = "T1: %(T1)s, aseg+aparc hires: %(hires aseg+aparc)s lores: %(lores aseg+aparc)s, surface: %(surface)s, bolds ok: %(boldok)d, bolds failed: %(boldfail)d, bolds skipped: %(boldskipped)d" % (report)

    # print r
    return (r, (sinfo['id'], rstatus, failed))

def hcp_task_fmri_analysis(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_task_fmri_analysis [... processing options]``

    Runs the Diffusion step of HCP Pipeline.

    REQUIREMENTS
    ============

    The requirement for this command is a successful completion of the
    minimal HCP preprocessing pipeline.

    INPUTS
    ======

    General parameters
    ------------------

    --sessions          The batch.txt file with all the sessions
                        information. [batch.txt]
    --sessionsfolder    The path to the study/sessions folder, where the
                        imaging  data is supposed to go. [.]
    --parsessions       How many sessions to run in parallel. [1]
    --overwrite         Whether to overwrite existing data (yes)
                        or not (no). [no]
    --hcp_suffix        Specifies a suffix to the session id if multiple
                        variants are run, empty otherwise. []
    --logfolder         The path to the folder where runlogs and comlogs
                        are to be stored, if other than default [].
    --log               Whether to keep ('keep') or remove ('remove') the
                        temporary logs once jobs are completed. ['keep']
                        When a comma or pipe ('|') separated list is given,
                        the log will be created at the first provided
                        location and then linked or copied to other
                        locations. The valid locations are:

                        - 'study' (for the default:
                          `<study>/processing/logs/comlogs` location)
                        - 'session' (for `<sessionid>/logs/comlogs`)
                        - 'hcp' (for `<hcp_folder>/logs/comlogs`)
                        - '<path>' (for an arbitrary directory)

    Specific parameters
    -------------------

    In addition the following *specific* parameters will be used to guide the
    processing in this step:

    --hcp_task_lvl1tasks            List of task fMRI scan names, which are
                                    the prefixes of the time series filename
                                    for the TaskName task. Multiple task fMRI
                                    scan names should be provided as a comma
                                    separated list. []
    --hcp_task_lvl1fsfs             List of design names, which are the prefixes
                                    of the fsf filenames for each scan run.
                                    Should contain same number of design files
                                    as time series images in --hcp_task_lvl1tasks
                                    option (N-th design will be used for N-th
                                    time series image). Provide a comma separated
                                    list of design names. If no value is passed
                                    to --hcp_task_lvl1fsfs, the value will be set
                                    to --hcp_task_lvl1tasks.
    --hcp_task_lvl2task             Name of Level2 subdirectory in which all
                                    Level2 feat directories are written for
                                    TaskName. [NONE]
    --hcp_task_lvl2fsf              Prefix of design.fsf filename for the Level2
                                    analysis for TaskName. If no value is passed
                                    to --hcp_task_lvl2fsf, the value will be set
                                    to the same list passed to
                                    --hcp_task_lvl2task.
    --hcp_task_summaryname          Naming convention for single-subject summary
                                    directory. Mandatory when running Level1
                                    analysis only, and should match naming of
                                    Level2 summary directories. Default when running
                                    Level2 analysis is derived from
                                    --hcp_task_lvl2task and --hcp_task_lvl2fsf options
                                    'tfMRI_TaskName/DesignName_TaskName'. [NONE]
    --hcp_task_confound             Confound matrix text filename (e.g., output
                                    of fsl_motion_outliers). Assumes file is in
                                    <SubjectID>/MNINonLinear/Results/<ScanName>.
                                    [NONE]
    --hcp_bold_smoothFWHM           Smoothing FWHM that matches what was used in
                                    the fMRISurface pipeline. [2]
    --hcp_bold_final_smoothFWHM     Value (in mm FWHM) of total desired
                                    smoothing, reached by calculating the
                                    additional smoothing required and applying
                                    that additional amount to data previously
                                    smoothed in fMRISurface. Default=2, which is
                                    no additional smoothing above HCP minimal
                                    preprocessing pipelines outputs.
    --hcp_task_highpass             Apply additional highpass filter (in seconds)
                                    to time series and task design. This is above
                                    and beyond temporal filter applied during
                                    preprocessing. To apply no additional
                                    filtering, set to 'NONE'. [200]
    --hcp_task_lowpass              Apply additional lowpass filter (in seconds)
                                    to time series and task design. This is above
                                    and beyond temporal filter applied during
                                    preprocessing. Low pass filter is generally
                                    not advised for Task fMRI analyses. [NONE]
    --hcp_task_procstring           String value in filename of time series
                                    image, specifying the additional processing
                                    that was previously applied (e.g.,
                                    FIX-cleaned data with 'hp2000_clean' in
                                    filename). [NONE]
    --hcp_regname                   Name of surface registration technique.
                                    [MSMSulc]
    --hcp_grayordinatesres          Value (in mm) that matches value in
                                    'Atlas_ROIs' filename. [2]
    --hcp_lowresmesh                Value (in mm) that matches surface resolution
                                    for fMRI data. [32]
    --hcp_task_vba                  A flag for using VBA. Only use this flag if you
                                    want unconstrained volumetric blurring of your
                                    data, otherwise set to NO for faster, less
                                    biased, and more senstive processing
                                    (grayordinates results do not use
                                    unconstrained volumetric blurring and are
                                    always produced). This flag is not set by
                                    defult.
    --hcp_task_parcellation         Name of parcellation scheme to conduct
                                    parcellated analysis. Default setting is
                                    NONE, which will perform dense analysis
                                    instead. Non-greyordinates parcellations
                                    are not supported because they are not valid
                                    for cerebral cortex. Parcellation supersedes
                                    smoothing (i.e. no smoothing is done). [NONE]
    --hcp_task_parcellation_file    Absolute path to the parcellation dlabel
                                    file [NONE]

    OUTPUTS
    =======

    The results of this step will be populated in the MNINonLinear folder inside
    the same sessions's root hcp folder.


    EXAMPLE USE
    ===========

    ::

        # First level HCP TaskfMRIanalysis
        qunex hcp_task_fmri_analysis \\
            --sessions=processing/batch.txt \\
            --sessionsfolder=sessions \\
            --hcp_task_lvl1tasks="TASK_1,TASK_2"

    ::

        # Second level HCP TaskfMRIanalysis
        qunex hcp_task_fmri_analysis \\
            --sessions=processing/batch.txt \\
            --sessionsfolder=sessions \\
            --hcp_task_lvl1tasks="TASK_1,TASK_2" \\
            --hcp_task_lvl2task="study/lvl2feats"
    """

    r = "\n------------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\n%s HCP fMRI task analysis pipeline [%s] ..." % (pc.action("Running", options['run']), options['hcp_processing_mode'])

    run    = True
    report = "Error"

    try:
        pc.doOptionsCheck(options, sinfo, 'hcp_task_fmri_analysis')
        doHCPOptionsCheck(options, sinfo, 'hcp_task_fmri_analysis')
        hcp = getHCPPaths(sinfo, options)

        if 'hcp' not in sinfo:
            r += "\n---> ERROR: There is no hcp info for session %s in batch.txt" % (sinfo['id'])
            run = False

        # parse input parameters
        # hcp_task_lvl1tasks
        lvl1tasks = ""
        if options['hcp_task_lvl1tasks'] is not None:
            lvl1tasks = options['hcp_task_lvl1tasks'].replace(",", "@")
        else:
            r += "\n---> ERROR: hcp_task_lvl1tasks parameter is not provided"
            run = False

        # --- build the command
        if run:
            comm = '%(script)s \
                --study-folder="%(studyfolder)s" \
                --subject="%(subject)s" \
                --lvl1tasks="%(lvl1tasks)s" ' % {
                    'script'             : os.path.join(hcp['hcp_base'], 'TaskfMRIAnalysis', 'TaskfMRIAnalysis.sh'),
                    'studyfolder'        : sinfo['hcp'],
                    'subject'            : sinfo['id'] + options['hcp_suffix'],
                    'lvl1tasks'          : lvl1tasks
                }

            # optional parameters

            # hcp_task_lvl1fsfs
            if options['hcp_task_lvl1fsfs'] is not None:
                lvl1fsfs = options['hcp_task_lvl1fsfs'].replace(",", "@")
                if (len(lvl1sfs.split(",")) != len(lvl1tasks.split(","))):
                    r += "\n---> ERROR: mismatch in the length of hcp_task_lvl1tasks and hcp_task_lvl1fsfs"
                    run = False

                comm += "                --lvl1fsfs=\"%s\"" % lvl1fsfs

            # hcp_task_lvl2task
            if options['hcp_task_lvl2task'] is not None:
                comm += "                --lvl2task=\"%s\"" % options['hcp_task_lvl2task']

                # hcp_task_lvl2fsf
                if options['hcp_task_lvl2fsf'] is not None:
                    comm += "                --lvl2fsf=\"%s\"" % options['hcp_task_lvl2fsf']

            # summary name
            # mandatory for Level1
            if options['hcp_task_lvl2task'] is None and options['hcp_task_summaryname'] is None:
                r += "\n---> ERROR: hcp_task_summaryname is mandatory when running Level1 analysis!"
                run = False
            
            if options['hcp_task_summaryname'] is not None:
                comm += "                --summaryname=\"%s\"" % options['hcp_task_summaryname']

            # confound
            if options['hcp_task_confound'] is not None:
                comm += "                --confound==\"%s\"" % options['hcp_task_confound']

            # origsmoothingFWHM
            if options['hcp_bold_smoothFWHM'] is not None and options['hcp_bold_smoothFWHM'] != "2":
                comm += "                --origsmoothingFWHM=\"%s\"" % options['hcp_bold_smoothFWHM']

            # finalsmoothingFWHM
            if options['hcp_bold_final_smoothFWHM'] is not None:
                comm += "                --finalsmoothingFWHM=\"%s\"" % options['hcp_bold_final_smoothFWHM']

            # highpassfilter
            if options['hcp_task_highpass'] is not None:
                comm += "                --highpassfilter=\"%s\"" % options['hcp_task_highpass']

            # lowpassfilter
            if options['hcp_task_lowpass'] is not None:
                comm += "                --lowpassfilter=\"%s\"" % options['hcp_task_lowpass']

            # procstring
            if options['hcp_task_procstring'] is not None:
                comm += "                --procstring=\"%s\"" % options['hcp_task_procstring']

            # regname
            if options['hcp_regname'] is not None and options['hcp_regname'] not in ["MSMSulc", "NONE", "none", "None"]:
                comm += "                --regname=\"%s\"" % options['hcp_regname']

            # grayordinatesres
            if options['hcp_grayordinatesres'] is not None and options['hcp_grayordinatesres'] != 2:
                comm += "                --grayordinatesres=\"%d\"" % options['hcp_grayordinatesres']

            # lowresmesh
            if options['hcp_lowresmesh'] is not None and options['hcp_lowresmesh'] != "32":
                comm += "                --lowresmesh=\"%s\"" % options['hcp_lowresmesh']

            # parcellation
            if options['hcp_task_parcellation'] is not None:
                comm += "                --parcellation=\"%s\"" % options['hcp_task_parcellation']

            # parcellationfile
            if options['hcp_task_parcellation_file'] is not None:
                comm += "                --parcellationfile=\"%s\"" % options['hcp_task_parcellation_file']

            # hcp_task_vba flag
            if options['hcp_task_vba']:
                comm += '                --vba="YES"'

            # -- Report command
            if run:
                r += "\n\n------------------------------------------------------------\n"
                r += "Running HCP Pipelines command via QuNex:\n\n"
                r += comm.replace("                --", "\n    --")
                r += "\n------------------------------------------------------------\n"

            # -- Test files
            tfile = None
            full_test = None

        # -- Run
        if run:
            if options['run'] == "run":
                if tfile is not None and overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                r, endlog, report, failed  = pc.runExternalForFile(tfile, comm, 'Running HCP fMRI task analysis', overwrite=overwrite, thread=sinfo['id'], remove=options['log'] == 'remove', task=options['command_ran'], logfolder=options['comlogs'], logtags=options['logtag'], fullTest=None, shell=True, r=r)

            # -- just checking
            else:
                passed, report, r, failed = pc.checkRun(tfile, full_test, 'HCP Diffusion', r, overwrite=overwrite)
                if passed is None:
                    r += "\n---> HCP fMRI task analysis can be run"
                    report = "HCP fMRI task analysis can be run"
                    failed = 0

        else:
            r += "\n---> Session can not be processed."
            report = "HCP fMRI task analysis can not be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder), errormessage:
        r = str(errormessage)
        failed = 1
    except:
        r += "\nERROR: Unknown error occured: \n...................................\n%s...................................\n" % (traceback.format_exc())
        failed = 1

    r += "\n\nHCP fMRI task analysis Preprocessing %s on %s\n------------------------------------------------------------" % (pc.action("completed", options['run']), datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))

    # print r
    return (r, (sinfo['id'], report, failed))
