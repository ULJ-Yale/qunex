#!/usr/bin/env python
# encoding: utf-8
"""
This file holds the core preprocessing hub functions and information it
defines the commands that can be run, it specifies the options and their
default values. It has a few support functions and the key `run` function
that processes the input, prints some of the help and calls processing
functions either localy or through supported scheduler systems.

None of the code is run directly from the terminal interface.

Created by Grega Repovs on 2016-12-17.
Code merge from dofcMRIp gCodeP/preprocess codebase.
Copyright (c) Grega Repovs. All rights reserved.

---
Changelog
2017-07-10 Grega Repovs
         - Simplified scheduler interface, now uses g_scheduler

"""

import sys
import time
import getopt
import subprocess
import gp_core
import g_core
import gp_HCP
import gp_workflow
import gp_simple
import gp_FS
import g_scheduler
import os
import os.path
from multiprocessing import Pool
from datetime import datetime


# =======================================================================
#                                                                 GLOBALS

log     = []
stati   = []
logname = ""


# =======================================================================
#                                                       SUPPORT FUNCTIONS

def writelog(item):
    '''
    writelog(item)
    Splits the passed item into two parts and appends the first to the
    global log list, and the second to the global stati list. It also
    prints the contents to the file specified in the global logname
    variable.
    '''
    global logname
    global log
    global stati
    r, status = procResponse(item)
    log.append(r)
    stati.append(status)
    f = open(logname, "a")
    print >> f, item
    f.close()


def procResponse(r):
    '''
    procResponse(r)
    It processes the response returned from the utilities functions
    called. It splits it into the report string and status tuple. If
    no status tupple is present, it adds an "Unknown" tupple.
    '''
    if type(r) is tuple:
        return r
    else:
        return (r, ("Unknown", "Unknown"))


def torf(s):
    '''
    torf(s)
    First checks if string is "None", 'none', or "NONE" and returns
    None, then Checks if s is any of the possible true strings: "True", "true",
    or "TRUE" and retuns a boolean result of the check.
    '''
    if s in ['None', 'none', 'NONE']:
        return None
    else:
        return s in ['True', 'true', 'TRUE', 'yes', 'Yes', 'YES']


def isNone(s):
    '''
    isNone(s)
    Check if the string is "None", "none" or "NONE" and returns None, otherwise
    returns the passed string.
    '''
    if s in ['None', 'none', 'NONE']:
        return None
    else:
        return s


def plist(s):
    '''
    plist(s)
    Processes the string, spliting it by the pipe "|" symbol, trimming
    any whitespace caracters form start or end of each resulting
    substring, and retuns an array of substrings of length more than 0.
    '''
    s = s.split('|')
    s = [e.strip() for e in s]
    s = [e for e in s if len(e) > 0]
    return s


# =======================================================================
#                                                              PARAMETERS

# -----------------------------------------------------------------------
#                                   list of parameters and default values

#  A list of possible parameters / arguments follows. Every parameter is
#  specified as a list of four values:
#
#  1/ the name of the parameter
#     ... This is the name that will be used to identify the parameter in
#         the command line and/or the batch.txt file. It is also the
#         name under which the parameter value will be accessible in the
#         options dictionary.
#  2/ the default value
#     ... This is the default value that will be used if the parameter is
#         not explicity specified in either the command line or in
#         batch.txt file.
#  3/ the convert function
#     ... This is the convert function used to transform the string input
#         into the value needed. Most commonly used functions are str
#         (keep the value as string), int (convert the value to integer),
#         float (convert the value to float), torf (check if the string
#         denotes a "true" value and return a bulean representation). Any
#         other function that takes string as an input and does not
#         require any other parameters is valid.
#  4/ a short description
#     ... A short description of the parameter.
#
#  Parameters are divided into sections. Every section starts with a list
#  of a single string element in the form "# ---- <section title>".
#


arglist = [['# ---- Basic settings'],
           ['subjects',           'batch.txt',                                   str,    "The file with subject information."],
           ['subjectsfolder',     '',                                            os.path.abspath, 'The path to study subjects folder.'],
           ['logfolder',          'None',                                        isNone,    'The path to log folder.'],
           ['overwrite',          'no',                                          torf,   'Whether to overwrite existing results.'],
           ['cores',              '1',                                           int,    'How many processor cores to use.'],
           ['nprocess',           '0',                                           int,    'How many subjects to process (0 - all).'],
           ['datainfo',           'False',                                       torf,   'Whether to print information.'],
           ['printoptions',       'False',                                       torf,   'Whether to print options.'],
           ['filter',             '',                                            str,    'Filtering information.'],
           ['script',             'None',                                        isNone, 'The script to be executed.'],
           ['subjid',              '',                                           str,  "list of | separated subject ids for which to run the command"],

           ['# ---- Preprocessing options'],
           ['bet',                '-f 0.5',                                      str,    "options to be passed to BET in brain extraction"],
           ['fast',               '-t 1 -n 3 --nopve',                           str,    "options to be passed to FAST in brain segmentation"],
           ['betboldmask',        '-R -m',                                       str,    "options to be passed to BET when creating bold brain masks"],
           ['TR',                 '2.5',                                         float,  "TR of the bold data"],
           ['omit',               '5',                                           int,    "how many frames to omit at the start of each bold run"],
           ['bold_actions',       'shrcl',                                       str,    "what processing steps to include in bold preprocessing"],
           ['bold_nuisance',      'm,V,WM,WB,1d',                                str,    "what regressors to include in nuisance removal"],
           ['bold_preprocess',    'all',                                         str,    "which bolds to process (can be multiple joind with | )"],
           ['boldname',           'bold',                                        str,    "the default name for the bold files"],
           ['pignore',            '',                                            str,    "what to do with frames marked as bad"],
           ['event_file',         '',                                            str,    "the root name of the fidl event file for task regression"],
           ['event_string',       '' ,                                           str,    "string specifying what and how of task to regress out"],
           ['source_folder',      'True',                                        torf,   "hould we check for source folder (yes/no)"],
           ['bold_prefix',        '',                                            str,    "what prefix to add at the start of the generated files"],
           ['wbmask',             '',                                            str,    "mask specifying what ROI to exclude from WB mask"],
           ['sbjroi',             '',                                            str,    "a mask used to specify subject specific WB"],
           ['nroi',               '',                                            str,    "additional nuisance regressors ROI and which not to mask by brain mask (e.g. 'nroi.names|eyes,scull')"],
           ['shrinknsroi',        'true',                                        str,    "whether to shrink signal nuisance ROI (V,WM,WB) true or false"],
           ['path_bold',          'bold[N]/*faln_dbnd_xr3d_atl.4dfp.img',        str,    "the mask to use for searching for bold images"],
           ['path_mov',           'movement/*_b[N]_faln_dbnd_xr3d.dat',          str,    "the mask to use for searching for movement files"],
           ['path_t1',            'atlas/*_mpr_n*_111_t88.4dfp.img',             str,    "the mask to use for searching for T1 file"],
           ['image_source',       '4dfp',                                        str,    "what is the target source file format / structure (4dfp, hcp)"],
           ['image_target',       '4dfp',                                        str,    "what is the target file format (4dfp, nifti, dtseries, ptseries)"],
           ['image_atlas',        '711',                                         str,    "what is the target atlas (711, cifti)"],

           ['# ---- GLM related options'],
           ['glm_matrix',          'none',                                        str,    "Whether to save GLM regressor matrix in text (text), image (image) or both (both) formats, or not (none)."],
           ['glm_residuals',       'save',                                        str,    "Whether to save GLM residuals (save) or not (forget)."],
           ['glm_name',            '',                                            str,    "Additional name to the residuals and coefficient file to distinguish between different posible models."],

           ['# ---- Movement thresholding and report options'],
           ['mov_dvars',           '3.0',                                         float,  "the dvars threshold to use for identifying bad frames"],
           ['mov_dvarsme',         '1.5',                                         float,  "the dvarsme threshold to use for identifying bad frames"],
           ['mov_fd',              '0.5',                                         float,  "frame displacement threshold to use for identifying bad frames"],
           ['mov_radius',          '50.0',                                        float,  "the assumed radius of the brain"],
           ['mov_scrub',           'yes',                                         str,    "whether to output a scrub file when processing motion statistics (not used in the new scrubbing pipeline)"],
           ['mov_fidl',            'udvarsme',                                    str,    "which scrub column to use when creating fidl ignore file or none"],
           ['mov_plot',            'mov_report',                                  str,    "root name of the plot file, none to omit plotting"],
           ['mov_post',            'udvarsme',                                    str,    "which column to use for generating post-scrubbing movement report or none"],
           ['mov_before',          '0',                                           int,    "how many frames preceeding bad frames to also exclude"],
           ['mov_after',           '0',                                           int,    "how many frames following bad frames to also exclude"],
           ['mov_bad',             'udvarsme',                                    str,    "what scrub column to use to mark bad frames"],
           ['mov_mreport',         'movement_report.txt',                         str,    "the name of the movement report file"],
           ['mov_preport',         'movement_report_post.txt',                    str,    "the name of the post scrub movement report file"],
           ['mov_sreport',         'movement_scrubbing_report.txt',               str,    "the name of the scrubbing report file"],
           ['mov_pdf',             'movement_plots',                              str,    "the name of the folder that holds movement stats plots"],
           ['mov_pref',            "",                                            str,    "the prefix for the movement report files"],

           ['# ---- CIFTI related options'],
           ['surface_smooth',      '6.0',                                         float,  "sigma for cifti surface smoothing"],
           ['volume_smooth',       '6.0',                                         float,  "sigma for cifti volume smoothing"],
           ['voxel_smooth',        '2',                                           float,  "extent of volume smoothing in voxels"],
           ['smooth_mask',         'false',                                       str,    "whether to use masked smoothing and what mask to use"],
           ['dilate_mask',         'false',                                       str,    "whether to use dilation after smoothing and what mask to use"],
           ['hipass_filter',       '0.008',                                       float,  "highpass filter to use"],
           ['lopass_filter',       '0.09',                                        float,  "lopass filter to use"],
           ['omp_threads',         '0',                                           int,    "number of cores to be used in wb_command (0 - don't change system settings)"],
           ['framework_path',      '',                                            str,    "the path to framework libraries on mac system"],
           ['wb_command_path',     '',                                            str,    "the path to wb_command"],
           ['print_command',       'no',                                          str,    "whether to print the command run within the preprocessing steps"],

           ['# ---- scheduler options'],
           ['scheduler',             'local',                                     str,    "the scheduler to use (local|PBS|LSF|SLURM) and any additional settings"],
           ['scheduler_environment', 'None',                                      isNone, "the path to the script setting up the environment to run the commands in"],
           ['scheduler_workdir',     'None',                                      isNone, "the path to working directory from which to run jobs on the cluster"],
           ['scheduler_sleep',       '1',                                         float,  "time in seconds between submission of individual scheduler jobs"],


           ['# --- HCP options'],
           ['hcp_freesurfer_home',    '',                                         str,    "path to FreeSurfer base folder"],
           ['hcp_freesurfer_module',  '',                                         str,    "Whether to load FreeSurfer as a module on the cluster: YES or NONE"],
           ['hcp_Pipeline',           '',                                         str,    "path to pipeline base folder"],
           ['hcp_suffix',             '',                                         str,    "subject id suffix if running HCP preprocessing variants"],
           ['hcp_brainsize',          '150',                                      int,    "human brain size in mm"],
           ['hcp_t2',                 't2',                                       str,    "whether T2 image is present - anything or NONE"],
           ['hcp_fmap',               'NONE',                                     str,    "DEPRECATED!!! whether hi-res structural fieldmap is present - SiemensFieldMap for Siemens Phase/Magnitude pair, GeneralElectricFieldMap for GE single B0 image, or NONE"],
           ['hcp_biascorrect_t1w',    'NONE',                                     str,    "Whether to run T1w image bias correction in PreFS step: YES or NONE"],
           ['hcp_echodiff',           'NONE',                                     str,    "the delta in TE times for the hi-res fieldmap image"],
           ['hcp_sephaseneg',         'NONE',                                     str,    "spin echo field map volume with a negative phase encoding direction: LR, RL, NONE"],
           ['hcp_sephasepos',         'NONE',                                     str,    "spin echo field map volume with a positive phase encoding direction: LR, RL, NONE"],
           ['hcp_dwelltime',          'NONE',                                     str,    "Echo Spacing or Dwelltime of Spin Echo Field Map or 'NONE' if not used"],
           ['hcp_seunwarpdir',        'NONE',                                     str,    "Phase encoding direction of the spin echo field map. (Only applies when using a spin echo field map.)"],
           ['hcp_t1samplespacing',    'NONE',                                     str,    "0.0000074 ... DICOM field (0019,1018) in s or 'NONE' if not used"],
           ['hcp_t2samplespacing',    'NONE',                                     str,    "0.0000021 ... DICOM field (0019,1018) in s or 'NONE' if not used"],
           ['hcp_unwarpdir',          'NONE',                                     str,    "Readout direction of the T1w and T2w images (Used with either a regular field map or a spin echo field map) z appears to be best or 'NONE' if not used"],
           ['hcp_gdcoeffs',           'NONE',                                     str,    "'${HCPPIPEDIR_Config}/coeff_SC72C_Skyra.grad' ... Location of Coeffs file or 'NONE' to skip"],
           ['hcp_avgrdcmethod',       'NONE',                                     str,    "'FIELDMAP' ... Averaging and readout distortion correction methods: 'NONE' = average any repeats with no readout correction 'FIELDMAP' or 'SiemensFieldMap' or 'GeneralElectricFieldMap' = average any repeats and use field map for readout correction 'TOPUP' = average and distortion correct at the same time with topup/applytopup only works for 2 images currently"],
           ['hcp_topupconfig',        'NONE',                                     str,    "Config for topup or 'NONE' if not used"],
           ['hcp_bfsigma',            '',                                         str,    "Bias Field Smoothing Sigma (optional)"],
           ['hcp_printcom',           '',                                         str,    "Print command for the HCP scripts"],
           ['hcp_grayordinatesres',   '2',                                        int,    "Usually 2mm"],
           ['hcp_hiresmesh',          '164',                                      int,    "Usually 164 vertices"],
           ['hcp_lowresmesh',         '32',                                       int,    "Usually 32 vertices"],
           ['hcp_regname',            'FS',                                       str,    "What registration is used."],
           ['hcp_cifti_tail',          '',                                        str,    "The tail of the cifti file to use when mapping data from the HCP MNINonLinear/Results folder."],
           ['hcp_bold_sequencetype',  'single',                                   str,    "The type of the sequence used: multi(band) vs single(band)"],
           ['hcp_bold_prefix',        'BOLD_',                                    str,    "The prefix to use for bold working folders and results"],
           ['hcp_bold_echospacing',   '0.00035',                                  str,    "Echo Spacing or Dwelltime of fMRI image"],
           ['hcp_bold_correct',       'TOPUP',                                    str,    "BOLD image deformation correction: TOPUP, FIELDMAP / SiemensFieldMap, GeneralElectricFieldMap or NONE"],
           ['hcp_bold_ref',           'NONE',                                     str,    "Whether BOLD image Reference images should be recorded - NONE or USE"],
           ['hcp_bold_echodiff',      'NONE',                                     str,    "Delta TE for BOLD fieldmap images or NONE if not used"],
           ['hcp_expert_file',        '',                                         str,    "Name of the read-in expert options file for FreeSurfer"],
           ['hcp_control_points',     '',                                         str,    "Whether to run with manual control points"],
           ['hcp_wm_edits',           '',                                         str,    "Whether to run with manually edited WM mask file"],
           ['hcp_bold_unwarpdir',     'y',                                        str,    "The direction of unwarping, can be specified separately for LR/RL : 'LR=x|RL=-x|x'"],
           ['hcp_bold_res',           '2',                                        str,    "Target image resolution 2mm recommended"],
           ['hcp_bold_gdcoeffs',      'NONE',                                     str,    "Gradient distorsion correction coefficients or NONE"],
           ['hcp_bold_stcorr',        'TRUE',                                     str,    "Whether to do slice timing correction TRUE or NONE"],
           ['hcp_bold_stcorrdir',     'up',                                       str,    "The direction of slice acquisition"],
           ['hcp_bold_stcorrint',     'odd',                                      str,    "Whether slices were acquired in an interleaved fashion (odd) or not (empty)"],
           ['hcp_bold_movref',        'independent',                              str,    "What reference to use for movement correction (independent, first)"],
           ['hcp_bold_seimg',         'independent',                              str,    "What image to use for spin-echo distorsion correction (independent, first)"],
           ['hcp_bold_smoothFWHM',    '2',                                        str,    "Whether slices were acquired in an interleaved fashion (odd or even) or not (empty)"],
           ['hcp_bold_usemask',       'T1',                                       str,    "what mask to use for the bold images (T1: default, BOLD: mask based on bet of the scout, NONE: do not use a mask)"],
           ['hcp_bold_preregister',   'epi_reg',                                  str,    "What code to use to preregister BOLDs before FSL BBR epi_reg (default) or flirt"],
           ['hcp_bold_refreg',        'linear',                                   str,    "Whether to use only linaer (default) or also nonlinear registration of motion corrected bold to reference"],
           ['hcp_bold_movreg',        'FLIRT',                                    str,    "Whether to use FLIRT (default and best for multiband images) or McFLIRT for motion correction"],
           ['hcp_dwi_PEdir',          '1',                                        str,    "Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior"],
           ['hcp_dwi_gdcoeffs',       'NONE',                                     str,    "DWI specific gradient distorsion coefficients file or NONE"],
           ['hcp_dwi_dwelltime',      '',                                         str,    "Echo spacing in msec."],

           ['# --- Processing options'],
           ['run',                    'run',                                      str,    "run type: run - do the task, test - perform checks"],
           ['log',                    'remove',                                   str,    "Whether to keep ('keep') or remove ('remove') the temporary logs once jobs are completed."]
           ]

#   --------------------------------------------------------- PARAMETER MAPPING
#   For historical reasons and to maintain backward compatibility, some of the
#   parameters need to be mapped to a parameter with another name. The "tomap"
#   dictionary specifies what is mapped to what.

tomap = {'bppt':        'bold_preprocess',
         'bppa':        'bold_actions',
         'bppn':        'bold_nuisance',
         'eventstring': 'event_string',
         'eventfile':   'event_file',
         'basefolder':  'subjectsfolder'}

#   ---------------------------------------------------------- FLAG DESCRIPTION
#   A list of flags, arguments that do not require additional values. They are
#   listed as a list of flags, each flag is specified with the following
#   elements:
#
#   1/ the name of the element
#   2/ what parameter does it map to
#   3/ what value does it set to the parameter it maps to
#   4/ short description

flaglist = [['test',                  'run',                                      'test', "run a test only"]
            ]

#   ------------------------------------------------------------------ OPTIONS
#   The options dictionary

options = {}


# ==============================================================================
#                                                                   COMMAND LIST
#
#   Commands are specified in the calist and salist lists. calist specifies
#   commands that can be run in parallel, one instance per subeject. salist
#   specifies commands that need to be run as a single process across all the
#   subjects. Both are a list of commands in which each command is specified
#   as list of four values:
#
#   1/ command short name
#   2/ command long name
#   3/ the actual function ran for the command
#   4/ a short description of the command
#
#   Empty lists denote there should be a blank line when printing out a command
#   list.

calist = [['mhd',     'mapHCPData',                  gp_HCP.mapHCPData,                              "Map HCP preprocessed data to subjects' image folder."],
          [],
          ['gbd',     'getBOLDData',                 gp_workflow.getBOLDData,                        "Copy functional data from 4dfp (NIL) processing pipeline."],
          ['bbm',     'createBOLDBrainMasks',        gp_workflow.createBOLDBrainMasks,               "Create brain masks for BOLD runs."],
          [],
          ['seg',     'runBasicSegmentation',        gp_FS.runBasicStructuralSegmentation,           "Run basic structural image segmentation."],
          ['gfs',     'getFSData',                   gp_FS.checkForFreeSurferData,                   "Copy existing FreeSurfer data to subjects' image folder."],
          ['fss',     'runSubcorticalFS',            gp_FS.runFreeSurferSubcorticalSegmentation,     "Run subcortical freesurfer segmentation."],
          ['fsf',     'runFullFS',                   gp_FS.runFreeSurferFullSegmentation,            "Run full freesurfer segmentation"],
          [],
          ['cbs',     'computeBOLDStats',            gp_workflow.computeBOLDStats,                   "Compute BOLD movement and signal statistics."],
          ['csr',     'createStatsReport',           gp_workflow.createStatsReport,                  "Create BOLD movement statistic reports and plots."],
          ['ens',     'extractNuisanceSignal',       gp_workflow.extractNuisanceSignal,              "Extract nuisance signal from BOLD images."],
          [],
          ['bpp',     'preprocessBold',              gp_workflow.preprocessBold,                     "Preprocess BOLD images (using old Matlab code)."],
          ['cpp',     'preprocessConc',              gp_workflow.preprocessConc,                     "Preprocess conc bundle of BOLD images (using old Matlab code)."],
          [],
          ['hcp1',    'hcp_PreFS',                   gp_HCP.hcpPreFS,                                "Run HCP PreFS pipeline."],
          ['hcp2',    'hcp_FS',                      gp_HCP.hcpFS,                                   "Run HCP FS pipeline."],
          ['hcp3',    'hcp_PostFS',                  gp_HCP.hcpPostFS,                               "Run HCP PostFS pipeline."],
          ['hcp4',    'hcp_fMRIVolume',              gp_HCP.hcpfMRIVolume,                           "Run HCP fMRI Volume pipeline."],
          ['hcp5',    'hcp_fMRISurface',             gp_HCP.hcpfMRISurface,                          "Run HCP fMRI Surface pipeline."],
          [],
          ['hcpd',    'hcp_Diffusion',               gp_HCP.hcpDiffusion,                            "Run HCP DWI pipeline."],
          ['hcpdf',   'hcp_DTIFit',                  gp_HCP.hcpDTIFit,                               "Run FSL DTI fit."],
          ['hcpdb',   'hcp_Bedpostx',                gp_HCP.hcpBedpostx,                             "Run FSL Bedpostx GPU."],
          [],
          ['rsc',     'runShellScript',              gp_simple.runShellScript,                       "Runs the specified script."],
          ]

salist = [['cbl',     'createBoldList',              gp_simple.createBoldList,                       'createBoldList'],
          ['ccl',     'createConcList',              gp_simple.createConcList,                       'createConcList'],
          ['lsi',     'listSubjectInfo',             gp_simple.listSubjectInfo,                      'listSubjectInfo']
          ]


#   -------------------------------------------------------- COMMAND DICTIONARY
#   Code that transcribes the comand specifications into a dictionary for
#   calling the relevant command when specified.

pactions = {}
for line in calist:
    if len(line) == 4:
        pactions[line[0]] = line[2]
        pactions[line[1]] = line[2]

sactions = {}
for line in salist:
    if len(line) == 4:
        sactions[line[0]] = line[2]
        sactions[line[1]] = line[2]

flist = {}
for line in flaglist:
    if len(line) == 4:
        flist[line[0]] = [line[1], line[2]]


# ==============================================================================
#                                                               RUNNING COMMANDS
#

def run(command, args):

    global log
    global stati
    global logname

    # --------------------------------------------------------------------------
    #                                                            Parsing options

    options = {}

    # --- set up default options

    for line in arglist:
        if len(line) == 4:
            options[line[0]] = line[1]

    # --- read options from batch.txt

    if 'subjects' in args:
        options['subjects'] = args['subjects']
    if 'subjid' in args:
        options['subjid'] = args['subjid']
    if 'filter' in args:
        options['filter'] = args['filter']

    subjects, gpref = g_core.getSubjectList(options['subjects'], sfilter=options['filter'], subjid=options['subjid'], verbose=False)

    for (k, v) in gpref.iteritems():
        options[k] = v

    # --- parse command line options

    for (k, v) in args.iteritems():
        if k in flist:
            options[flist[k][0]] = flist[k][1]
        else:
            options[k] = v

    # ---- Recode

    for line in arglist:
        if len(line) == 4:
            options[line[0]] = line[2](options[line[0]])

    # ---- Take care of mapping

    mapwarn = False
    for k, v in args.iteritems():
        if k in tomap:
            if not mapwarn:
                print "\nERROR: Use of deprecated parameter name(s)!\n       The following parameters have new names:"
                mapwarn = True
            print"       ... %s is now %s!" % (k, tomap[k])
    if mapwarn:
        print "       Please correct the listed parameter names in command line or batch file and run the command again!"
        exit()

    # ---- Set key parameters

    overwrite    = options['overwrite']
    cores        = options['cores']
    nprocess     = options['nprocess']
    printinfo    = options['datainfo']
    printoptions = options['printoptions']

    logfolder    = g_core.deduceFolders(options)['logfolder']

    runlogfolder = os.path.join(logfolder, 'runlogs')
    comlogfolder = os.path.join(logfolder, 'comlogs')

    options['runlogs']   = runlogfolder
    options['comlogs']   = comlogfolder
    options['logfolder'] = logfolder

    # --------------------------------------------------------------------------
    #                                                          start writing log

    for cfolder in [runlogfolder, comlogfolder]:
        if not os.path.exists(cfolder):
            os.makedirs(cfolder)
    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%s")
    logname = os.path.join(runlogfolder, "Log-%s-%s.log") % (command, logstamp)

    log   = []
    stati = []

    sout = "\n\n=================================================================\n"
    sout += "gmri " + command + " \\\n"

    for (k, v) in args.iteritems():
        sout += '  --%s="%s" \\\n' % (k, v)

    sout += "=================================================================\n"

    # --- check if there are no subjects

    if not subjects:
        sout += "\nERROR: No subjects specified to process. Please check your batch file, filtering options or subjid parameter!"
        print sout
        writelog(sout)
        exit()

    elif options['run'] == 'run':
        sout += "\nStarting multiprocessing subjects in %s with a pool of %d concurrent processes\n" % (options['subjects'], cores)

    else:
        sout += "\nRunning test on %s ...\n" % (options['subjects'])

    print sout
    writelog(sout)

    # -----------------------------------------------------------------------
    #                                                           print options

    if printoptions:
        print "\nFull list of options:"
        writelog("\nFull list of options:\n")
        for line in arglist:
            if len(line) == 4:
                print "%-25s :" % (line[0]), options[line[0]]
                writelog("  %-25s : %s" % (line[0], str(options[line[0]])))

    # -----------------------------------------------------------------------
    #                                                              print info

    if printinfo:
        print subjects


    # =======================================================================
    #                                               RUN BY SUBJECT PROCESSING

    if not os.path.exists(options['subjectsfolder']):
        os.mkdir(options['subjectsfolder'])

    if nprocess > 0:
        nsubjects = [subjects.pop(0) for e in range(nprocess) if subjects]
        subjects = nsubjects


    # -----------------------------------------------------------------------
    #                                                               local cue

    if options['scheduler'] == 'local' or options['run'] == 'test':

        print "---- Running local"
        pool = Pool(processes=cores)
        result = []
        c = 0
        if cores == 1 or options['run'] == 'test':
            if command in pactions:
                todo = pactions[command]
                for subject in subjects:
                    if len(subject['id']) > 1:
                        if options['run'] == 'test':
                            action = 'testing'
                        else:
                            action = 'processing'
                        print "Starting %s of subject %s at %s" % (action, subject['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
                        r, status = procResponse(todo(subject, options, overwrite, c + 1))
                        writelog(r)
                        stati.append(status)
                        c += 1
                        if nprocess and c >= nprocess:
                            break

            if command in sactions:
                todo = sactions[command]
                r, status = procResponse(todo(subjects, options, overwrite))
                writelog(r)

            f = open(logname + '2.log', "w")
            print >> f, "\n\n============================= LOG ================================\n"
            for e in log:
                print >> f, e
            f.close()

        else:
            c = 0
            if command in pactions:
                todo = pactions[command]
                for subject in subjects:
                    if len(subject['id']) > 1:
                        print "Adding processing of subject %s to the pool at %s" % (subject['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
                        result.append(pool.apply_async(todo, (subject, options, overwrite, c + 1), callback=writelog))
                        c += 1
                        if nprocess and c >= nprocess:
                            break

            if command in sactions:
                todo = sactions[command]
                r, status = procResponse(todo(subjects, options, overwrite))
                writelog(r)

            pool.close()
            pool.join()

            f = open(logname + '2.log', "w")
            print >> f, "\n\n============================= LOG ================================\n"
            for e in log:
                print >> f, e
            f.close()

        print "\n\n===> Final report\n"
        for sid, status in stati:
            if "Unknown" not in sid:
                print "... %s ---> %s" % (sid, status)


    # -----------------------------------------------------------------------
    #                                                  general scheduler code

    else:
        g_scheduler.runThroughScheduler(command, subjects=subjects, args=options, cores=cores, logfolder=os.path.join(logfolder, 'batchlogs'), logname=logname)

