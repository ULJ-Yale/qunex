#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``process.py``

This file holds the core preprocessing hub functions and information it
defines the commands that can be run, it specifies the options and their
default values. It has a few support functions and the key `run` function
that processes the input, prints some of the help and calls processing
functions either localy or through supported scheduler systems.

None of the code is run directly from the terminal interface.
"""

# imports
import os
import os.path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

import general.scheduler as gs
import general.core as gc
import general.exceptions as ge
import general.commands_support as gcs
from processing import fs, fsl, simple, workflow


# pipelines imports
from hcp import process_hcp


# =======================================================================
#                                                                 GLOBALS

log     = []
stati   = []
logname = ""


# =======================================================================
#                                                       SUPPORT FUNCTIONS

def writelog(item):
    '''
    ``writelog(item)``

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
    print(r, file=f)
    f.close()


def procResponse(r):
    '''
    ``procResponse(r)``

    It processes the response returned from the utilities functions
    called. It splits it into the report string and status tuple. If
    no status tupple is present, it adds an "Unknown" tupple. If the 
    third element is missing, it assumes it ran ok and sets it to
    0.
    '''

    if type(r) is tuple:
        if len(r) == 2:
            if len(r[1]) == 2:
                return (r[0], (r[1][0], r[1][1], None))
            elif len(r[1]) == 3:
                return r
            else:
                return("Unknown", ("Unknown", "Unknown", None))
        else:
            return("Unknown", ("Unknown", "Unknown", None))
    else:
        return (r, ("Unknown", "Unknown", None))


def torf(s):
    '''
    ``torf(s)``

    First checks if string is "None", 'none', or "NONE" and returns
    None, then Checks if s is any of the possible true strings: "True", "true",
    or "TRUE" and retuns a boolean result of the check.
    '''
    if s in ['None', 'none', 'NONE']:
        return None
    else:
        return s in ['True', 'true', 'TRUE', 'yes', 'Yes', 'YES']


def flag(f):
    '''
    ``flag(f)``

    Converts a flag (f) passed as a string to a boolean.
    '''

    if type(f) == bool:
        return f
    elif f in ['True', 'true', 'TRUE', 'yes', 'Yes', 'YES']:
        return True
    else:
        return False


def isNone(s):
    '''
    ``isNone(s)``

    Check if the string is "None", "none" or "NONE" and returns None, otherwise
    returns the passed string.
    '''
    if s in ['None', 'none', 'NONE', '']:
        return None
    else:
        return s


def updateOptions(session, options):
    '''
    ``updateOptions(session, options)``

    Returns an updated copy of options dictionary where all keys from 
    sessions that started with an underscore '_' are mapped into options.
    '''
    soptions = dict(options)
    for key, value in session.items():
        if key.startswith('_'):
            soptions[key[1:]] = value
    return soptions


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


arglist = [
           ['# ---- Basic settings'],
           ['sessions',           'batch.txt',                                   str,    "The file with sessions information."],
           ['sessionsfolder',     '',                                            os.path.abspath, 'The path to study sessions folder.'],
           ['logfolder',          '',                                            isNone, 'The path to log folder.'],
           ['logtag',             '',                                            str,    'An optional additional tag to add to the log file after the command name.'],
           ['overwrite',          'no',                                          torf,   'Whether to overwrite existing results.'],
           ['parsessions',        '1',                                           int,    'How many processor sessions to run in parallel.'],
           ['parelements',        '1',                                           int,    'How many elements to run in parralel.'],
           ['nprocess',           '0',                                           int,    'How many sessions to process (0 - all).'],
           ['datainfo',           'False',                                       torf,   'Whether to print information.'],
           ['printoptions',       'False',                                       torf,   'Whether to print options.'],
           ['filter',             '',                                            str,    'Filtering information.'],
           ['script',             'None',                                        isNone, 'The script to be executed.'],
           ['sessionid',          '',                                            str,    "a session id for which to run the command"],
           ['sessionids',         '',                                            str,    "list of | separated session ids for which to run the command"],

           ['# ---- Preprocessing options'],
           ['bet',                '-f 0.5',                                      str,    "options to be passed to BET in brain extraction"],
           ['fast',               '-t 1 -n 3 --nopve',                           str,    "options to be passed to FAST in brain segmentation"],
           ['betboldmask',        '-R -m',                                       str,    "options to be passed to BET when creating bold brain masks"],
           ['TR',                 '2.5',                                         float,  "TR of the bold data"],
           ['omit',               '5',                                           int,    "how many frames to omit at the start of each bold run"],
           ['bold_actions',       'shrcl',                                       str,    "what processing steps to include in bold preprocessing"],
           ['bold_nuisance',      'm,V,WM,WB,1d',                                str,    "what regressors to include in nuisance removal"],
           ['bolds',              'all',                                         str,    "which bolds to process (can be multiple joind with | )"],
           ['boldname',           'bold',                                        str,    "the default name for the bold files"],
           ['qx_nifti_tail',      'None',                                        isNone, "The tail of the nifti (volume) file assigned when mapping data to QuNex images/functional folder. If not set or set to 'None', it defaults to the value of hcp_nifti_tail"],
           ['qx_cifti_tail',      'None',                                        isNone, "The tail of the cifti file assigned when mapping data to QuNex images/functional folder. If not set or set to 'None', it defaults to the value of hcp_cifti_tail"],
           ['nifti_tail',         'None',                                        isNone, "The tail of the nifti (volume) file to be processed. If not set or set to 'None', it defaults to the value of qx_nifti_tail"],
           ['cifti_tail',         'None',                                        isNone, "The tail of the cifti file to be processed. If not set or set to 'None', it defaults to the value of qx_cifti_tail"],           
           ['bold_prefix',        '',                                            str,    "an optional prefix to place in front of processing name extensions in the resulting files"],
           ['bold_variant',       '',                                            str,    "The suffix to add to 'images/functional' folders. '' by default"],
           ['img_suffix',         '',                                            str,    "an optional suffix for the images folder, to be used when working with multiple parallel workflows"],
           ['pignore',            '',                                            str,    "what to do with frames marked as bad"],
           ['event_file',         '',                                            str,    "the root name of the fidl event file for task regression"],
           ['event_string',       '' ,                                           str,    "string specifying what and how of task to regress out"],
           ['source_folder',      'True',                                        torf,   "hould we check for source folder (yes/no)"],
           ['wbmask',             '',                                            str,    "mask specifying what ROI to exclude from WB mask"],
           ['sessionroi',         '',                                            str,    "a mask used to specify session specific WB"],
           ['nroi',               '',                                            str,    "additional nuisance regressors ROI and which not to mask by brain mask (e.g. 'nroi.names|eyes,scull')"],
           ['shrinknsroi',        'true',                                        str,    "whether to shrink signal nuisance ROI (V,WM,WB) true or false"],
           ['path_bold',          'bold[N]/*faln_dbnd_xr3d_atl.4dfp.img',        str,    "the mask to use for searching for bold images"],
           ['path_mov',           'movement/*_b[N]_faln_dbnd_xr3d.dat',          str,    "the mask to use for searching for movement files"],
           ['path_t1',            'atlas/*_mpr_n*_111_t88.4dfp.img',             str,    "the mask to use for searching for T1 file"],
           ['image_source',       'hcp',                                         str,    "what is the target source file format / structure (4dfp, hcp)"],
           ['image_target',       'nifti',                                       str,    "what is the target file format (4dfp, nifti, dtseries, ptseries)"],
           ['image_atlas',        'cifti',                                       str,    "what is the target atlas (711, cifti)"],
           ['use_sequence_info',  'all',                                         gc.pcslist, "which sequence specific information extracted from JSON sidecar files and present inline in batch file to use (pipe, comma or space separated list of <information>, <modality>:<information>, 'all' or 'none')"],
           ['conc_use',           'relative',                                    str,    "how the paths in the .conc file will be used (relative, absolute)"],

           ['# ---- GLM related options'],
           ['glm_matrix',          'none',                                        str,    "Whether to save GLM regressor matrix in text (text), image (image) or both (both) formats, or not (none)."],
           ['glm_residuals',       'save',                                        str,    "Whether to save GLM residuals (save) or not (none)."],
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
           ['mov_bad',             'udvarsme',                                    str,    "what scrub column to use to mark bad frames (one of mov, dvars, dvarsme, idvars, udvars, idvarsme, udvarsme--see documentation on motion scrubbing)"],
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

           ['# --- general HCP options'],
           ['hcp_processing_mode',    'HCPStyleData',                             str,    "Controls whether the HCP acquisition and processing guidelines should be treated as requirements (HCPStyleData) or if additional processing functionality is allowed (LegacyStyleData)."],
           ['hcp_folderstructure',    'hcpls',                                    str,    "If set to 'hcpya' the folder structure used in the initial HCP Young Adults study is used. Specifically, the source files are stored in individual folders within the main 'hcp' folder in parallel with the working folders and the 'MNINonLinear' folder with results. If set to 'hcpls' the folder structure used in the HCP Life Span study is used. Specifically, the source files are all stored within their individual subfolders located in the joint 'unprocessed' folder in the main 'hcp' folder, parallel to the working folders and the 'MNINonLinear' folder. ['hcpls']"],
           ['hcp_freesurfer_home',    '',                                         str,    "path to FreeSurfer base folder."],
           ['hcp_freesurfer_module',  '',                                         str,    "Whether to load FreeSurfer as a module on the cluster: YES or NONE."],
           ['hcp_pipeline',           '',                                         isNone, "Path to the HCP pipeline base folder."],
           ['hcp_suffix',             '',                                         str,    "session id suffix if running HCP preprocessing variants."],
           ['hcp_t2',                 't2',                                       str,    "whether T2 image is present - anything or NONE."],
           ['hcp_printcom',           '',                                         str,    "Print command for the HCP scripts: set to echo to have commands printed and not executed.."],
           ['hcp_bold_prefix',        'BOLD_',                                    str,    "The prefix to use when generating bold names (see 'hcp_filename') for bold working folders and results."],
           ['hcp_filename',           'automated',                                str,    "How to name the image files in the hcp structure. The default ('automated') is to name them automatically by their number using formula '<hcp_bold_prefix>_[N]' (e.g. BOLD_1), the alternative ('userdefined') is to use their user defined names (e.g. rfMRI_REST1_AP). ['automated']."],
           ['hcp_lowresmesh',         '32',                                       str,    "Usually 32 vertices."],
           ['hcp_lowresmeshes',       '32',                                       str,    "Usually 32 vertices."],
           ['hcp_hiresmesh',          '164',                                      int,    "Usually 164 vertices."],
           ['hcp_bold_res',           '2',                                        str,    "Target image resolution 2mm recommended."],
           ['hcp_grayordinatesres',   '2',                                        int,    "Usually 2mm."],
           ['hcp_regname',            'MSMSulc',                                  str,    "What registration is used FS or MSMSulc. FS if none is provided."],
           ['hcp_fs_longitudinal',    '',                                         str,    "Is this FreeSurfer run to be based on longitudional data? YES or NO, [NO]."],
           ['hcp_cifti_tail',          '',                                        str,    "The tail of the cifti file used when mapping data from the HCP MNINonLinear/Results folder and processing."],
           ['hcp_bold_variant',       '',                                         str,    "The suffix to add to 'MNINonLinear/Results' folder. '' by default."],
           ['hcp_nifti_tail',          '',                                        str,    "The tail of the nifti (volume) file used when mapping data from the HCP MNINonLinear/Results folder and processing."],

           ['# --- hcp_pre_freesurfer options'],
           ['hcp_brainsize',          '150',                                      int,    "Human brain size in mm."],
           ['hcp_t1samplespacing',    '',                                         str,    "0.0000074 ... DICOM field (0019,1018) in s or '' if not used."],
           ['hcp_t2samplespacing',    '',                                         str,    "0.0000021 ... DICOM field (0019,1018) in s or '' if not used."],
           ['hcp_gdcoeffs',           '',                                         str,    "Location of gradient coefficient file, a string describing mulitiple options, or '' to skip."],
           ['hcp_bfsigma',            '',                                         str,    "Bias Field Smoothing Sigma (optional)."],
           ['hcp_avgrdcmethod',       'NONE',                                     str,    "Averaging and readout distortion correction methods: 'NONE' = average any repeats with no readout correction 'FIELDMAP' or 'SiemensFieldMap' or 'GeneralElectricFieldMap' = average any repeats and use field map for readout correction 'TOPUP' = average and distortion correct at the same time with topup/applytopup only works for 2 images currently."],
           ['hcp_unwarpdir',          '',                                         str,    "Readout direction of the T1w and T2w images (Used with either a regular field map or a spin echo field map) z appears to be best or '' if not used."],
           ['hcp_echodiff',           '',                                         str,    "the delta in TE times for the hi-res fieldmap image ['']."],
           ['hcp_seechospacing',      '',                                         str,    "Echo Spacing or Dwelltime of Spin Echo Field Map or '' if not used."],
           ['hcp_seunwarpdir',        '',                                         str,    "Phase encoding direction of the spin echo field map. (Only applies when using a spin echo field map.) ['']."],
           ['hcp_topupconfig',        '',                                         str,    "A full path to the topup configuration file to use. Set to '' if the default is to be used or of TOPUP distortion correction is not used."],
           ['hcp_prefs_custombrain',  '',                                         str,    "Whether to use a custom bain mask (MASK) or custom brain images (CUSTOM) in PreFS or not (NONE; the default)."],
           ['hcp_prefs_template_res', '0.7',                                      str,    "The resolution (in mm) of the structural images templates to use in the prefs step."],
           ['hcp_sephaseneg',         '',                                         str,    "spin echo field map volume with a negative phase encoding direction: (AP, PA, LR, RL) ['']."],
           ['hcp_sephasepos',         '',                                         str,    "spin echo field map volume with a positive phase encoding direction: (AP, PA, LR, RL) ['']."],
           ['hcp_bold_smoothFWHM',    '',                                         isNone, "Whether slices were acquired in an interleaved fashion (odd or even) or not (empty)."],

           ['# --- hcp_freesurfer options'],
           ['hcp_fs_seed',            '',                                         str,    "Recon-all seed value. If not specified, none will be used. HCP Pipelines specific!"],
           ['hcp_fs_existing_session','FALSE',                                    torf,   "Indicates that the command is to be run on top of an already existing analysis/session. This excludes the `-i` flag from the invocation of recon-all. If set, the user needs to specify which recon-all stages to run using the --hcp_fs_extra_reconall parameter. Accepted values are TRUE or FALSE [FALSE]. HCP Pipelines specific!"],
           ['hcp_fs_extra_reconall',  '',                                         str,    "A string with extra parameters to pass to FreeSurfer recon-all. The extra parameters are to be listed in a pipe ('|') separated string. Parameters and their values need to be listed separately. E.g. to pass `-norm3diters 3` to reconall, the string has to be: \"-norm3diters|3\" []. HCP Pipelines specific!"],
           ['hcp_expert_file',        '',                                         str,    "Name of the read-in expert options file for FreeSurfer."],
           ['hcp_control_points',     '',                                         str,    "Whether to run with manual control points."],
           ['hcp_wm_edits',           '',                                         str,    "Whether to run with manually edited WM mask file."],
           ['hcp_autotopofix_off',    '',                                         str,    "YES to turn off the automatic topologic fix step in FS and compute WM surface deterministically from manual WM mask (empty)."],
           ['hcp_fs_brainmask',       '',                                         str,    "Specify 'original' to keep the masked original brainimage; 'manual' to use the manually edited brainmask file; default 'fs'uses the brainmask generated by mri_watershed [fs]."],
           ['hcp_fs_flair',           'FALSE',                                    torf,   "If set to TRUE indicates that recon-all is to be run with the -FLAIR/-FLAIRpial options(rather than the -T2/-T2pial options). The FLAIR input image itself should still be provided via the '--t2' argument."],
           ['hcp_fs_no_conf2hires',   'FALSE',                                    torf,   "Indicates that (most commonly due to low resolution—1mm or less—of structural image(s), high-resolution steps of recon-all should be excluded. Accepted values are TRUE or FALSE [FALSE]."],

           ['# --- hcp_post_freesurfer options'],
           ['hcp_mcsigma',            '',                                         str,    "Correction sigma used for metric smooting (sqrt(200): 14.14213562373095048801) ['']."],
           ['hcp_inflatescale',       '1',                                        str,    "Inflate extra scale parameter [1]."],

           ['# --- hcp_fmri_volume options'],
           ['hcp_bold_biascorrection','NONE',                                     str,    "Whether to perform bias correction for BOLD images. NONE, LEGACY or SEBASED (for TOPUP DC only). HCP Pipelines only!"],
           ['hcp_bold_usejacobian',   '',                                         str,    "Whether to apply the jacobian of the distortion correction to fMRI data. HCP Pipelines only!"],
           ['hcp_bold_echospacing',   '',                                         str,    "Echo Spacing or Dwelltime of fMRI image in seconds."],
           ['hcp_bold_sbref',         'NONE',                                     str,    "Whether BOLD image Reference images should be used - NONE or USE."],
           ['hcp_bold_dcmethod',      '',                                         str,    "BOLD image deformation correction: TOPUP, FIELDMAP / SiemensFieldMap, GeneralElectricFieldMap or NONE."],
           ['hcp_bold_echodiff',      'NONE',                                     str,    "Delta TE in ms for BOLD fieldmap images or NONE if not used."],
           ['hcp_bold_unwarpdir',     'y',                                        str,    "The direction of unwarping, can be specified separately for LR/RL: e.g. 'LR=x|RL=-x|x' or similarly for AP/PA."],
           ['hcp_bold_gdcoeffs',      'NONE',                                     str,    "Gradient distortion correction coefficients or NONE."],
           ['hcp_bold_doslicetime',   '',                                         str,    "Whether to do slice timing correction TRUE or FALSE (default)."],
           ['hcp_bold_slicetimerparams' ,'',                                      str,    "A comma or pipe separated string of parameters for FSL slicetimer."],
           ['hcp_bold_movreg',        'MCFLIRT',                                  str,    "Whether to use FLIRT or MCFLIRT for motion correction."],
           ['hcp_bold_movref',        'independent',                              str,    "What reference to use for movement correction (independent, first)."],
           ['hcp_bold_seimg',         'independent',                              str,    "What image to use for spin-echo distortion correction (independent, first)."],
           ['hcp_bold_refreg',        '',                                         str,    "Whether to use only linaer (default) or also nonlinear registration of motion corrected bold to reference."],
           ['hcp_bold_mask',          '',                                         str,    "Specifies what mask to use for the final bold. T1_fMRI_FOV: combined T1w brain mask and fMRI FOV masks (the default), T1_DILATED_fMRI_FOV: a once dilated T1w brain based mask combined with fMRI FOV, T1_DILATED2x_fMRI_FOV: a twice dilated T1w brain based mask combined with fMRI FOV, fMRI_FOV: a fMRI FOV mask."],
           ['hcp_bold_sephaseneg',    '',                                         str,    "Spin echo field map volume to use for BOLD TOPUP with a negative phase encoding direction (AP, PA, LR, RL), ['']."],
           ['hcp_bold_sephasepos',    '',                                         str,    "Spin echo field map volume to use for BOLD TOPUP with a positive phase encoding direction (AP, PA, LR, RL), ['']."],
           ['hcp_bold_topupconfig',   '',                                         str,    "A full path to the topup configuration file to use. Set to '' if the default is to be used or of TOPUP distortion correction is not used."],
           ['hcp_bold_preregistertool', '',                                       str,    "What code to use to preregister BOLDs before FSL BBR epi_reg (default) or flirt."],
           ['hcp_bold_dof',           '',                                         str,    "Degrees of freedom for EPI-T1 FLIRT. Empty to use HCP default."],
           ['hcp_bold_stcorrdir',     '',                                         str,    "The direction of slice acquisition NOTE: deprecated!"],
           ['hcp_bold_stcorrint',     '',                                         str,    "Whether slices were acquired in an interleaved fashion (odd) or not (empty) NOTE: deprecated!"],

           ['# --- hcp_diffusion options'],
           ['hcp_dwi_echospacing',    '',                                         str,    "Echo spacing in msec."],
           ['hcp_dwi_phasepos',       'PA',                                       str,    "The direction of unwarping for positive phase."],
           ['hcp_dwi_gdcoeffs',       'NONE',                                     str,    "DWI specific gradient distortion coefficients file or NONE."],
           ['hcp_dwi_dof',            '6',                                        str,    "Degrees of Freedom for post eddy registration to structural images. Defaults to 6."],
           ['hcp_dwi_b0maxbval',      '50',                                       str,    "Volumes with a bvalue smaller than this value will be considered as b0s. Defaults to 50."],
           ['hcp_dwi_combinedata',    '1',                                        str,    "Specified value is passed as the CombineDataFlag value for the eddy_postproc.sh script. If JAC resampling has been used in eddy, this value determines what to do with the output file: 2 - include in the output all volumes uncombined (i.e. output file of eddy); 1 - include in the output and combine only volumes where both LR/RL (or AP/PA) pairs have been acquired; 0 - As 1, but also include uncombined single volumes. Defaults to 1."],
           ['hcp_dwi_extraeddyarg',   '',                                         isNone, "A string specifying additional arguments to pass to eddy processing. Defaults to ''."],
           ['hcp_dwi_name',           '',                                         isNone, "Name to give DWI output directories."],
           ['hcp_dwi_cudaversion',    '',                                         isNone, "If using the GPU-enabled version of eddy, then this option can be used to specify which eddy_cuda binary version to use. If X.Y is specified, then FSLDIR/bin/eddy_cudaX.Y will be used. Note that CUDA 9.1 is installed in the container."],
           ['hcp_dwi_nogpu',          None,                                       flag, 'If specified, use the non-GPU-enabled version of eddy. Defaults to using the GPU-enabled version of eddy.'],
           ['hcp_dwi_selectbestb0',   None,                                       flag, "If set selects the best b0 for each phase encoding direction to pass on to topup rather than the default behaviour of using equally spaced b0's throughout the scan. The best b0  is identified as the least distorted (i.e., most similar to the average b0 after registration). The flag is not set by default."],

           ['# --- general hcp_icafix, hcp_post_fix, hcp_reapply_fix, hcp_msmall, hcp_dedrift_and_resample options'],
           ['hcp_icafix_bolds',       '',                                         isNone, "A string specifying a list of bolds for ICAFix. Also used later in PostFix, ReApplyFix, MSMAll and DeDriftAndResample. Defaults to ''."],
           ['hcp_icafix_highpass',    '',                                         isNone, "Value for the highpass filter, [0] for multi-run HCP ICAFix and [2000] for single-run HCP ICAFix."],
           ['hcp_matlab_mode',        'compiled',                                 str, "Specifies the Matlab version, can be interpreted, compiled or octave."],
           ['hcp_icafix_domotionreg', '',                                         isNone, "Whether to regress motion parameters as part of the cleaning. The default value for single-run HCP ICAFix is [TRUE], while the default for multi-run HCP ICAFix is [FALSE]."],
           ['hcp_icafix_deleteintermediates', 'FALSE',                            torf,   "If TRUE, deletes both the concatenated high-pass filtered and non-filtered timeseries files that are prerequisites to FIX cleaning [FALSE]."],

           ['# --- hcp_icafix options'],
           ['hcp_icafix_traindata',   '',                                         str,    "Which file to use for training data. [] for single-run HCP ICAFix and [HCP_Style_Single_Multirun_Dedrift.RData] for multi-run HCP ICAFix."],
           ['hcp_icafix_threshold',   '10',                                       int,    "ICAFix threshold that controls the sensitivity/specificity tradeoff."],
           ['hcp_icafix_postfix',     'TRUE',                                     torf,   "Whether to automatically run HCP PostFix if HCP ICAFix finishes successfully."],

           ['# --- hcp_post_fix options'],
           ['hcp_postfix_dualscene',  '',                                         isNone, "Path to an alternative template scene, if empty HCP default dual scene will be used."],
           ['hcp_postfix_singlescene', '',                                        isNone, "Path to an alternative template scene, if empty HCP default single scene will be used."],
           ['hcp_postfix_reusehighpass', 'TRUE',                                  torf,   "Whether to reuse highpass."],

           ['# --- hcp_reapply_fix options'],
           ['hcp_icafix_regname',     'NONE',                                     str,    "Specifies surface registration name. If NONE MSMSulc will be used."],

           ['# --- hcp_msmall options options'],
           ['hcp_msmall_bolds',       '',                                         isNone, "A comma separated list that defines the bolds that will be used in the computation of the MSMAll registration."],
           ['hcp_msmall_outfmriname', 'rfMRI_REST',                               str,    "The name which will be given to the concatenation of scans specified by the hcp_msmall_bolds parameter."],
           ['hcp_msmall_templates',   '',                                         isNone, "Path to directory containing MSMAll template files."],
           ['hcp_msmall_outregname',  'MSMAll_InitialReg',                        str,    "Output registration name."],
           ['hcp_msmall_procstring',  '',                                         isNone, "Identification for FIX cleaned dtseries to use."],
           ['hcp_msmall_resample',    'TRUE',                                     torf,   "Whether to automatically run HCP DeDriftAndResample if HCP MSMAll finishes successfully."],

           ['# --- hcp_dedrift_and_resample options'],
           ['hcp_resample_concatregname', 'MSMAll',                               str,    "Output name of the dedrifted registration."],
           ['hcp_resample_regname',   '',                                         isNone, "Registration sphere name."],
           ['hcp_resample_reg_files', '',                                         isNone, "Comma separated paths to the spheres output from the MSMRemoveGroupDrift pipeline."],
           ['hcp_resample_maps',      'sulc,curvature,corrThickness,thickness',   str,    "Comma separated paths to maps that will have the MSMAll registration applied that are not myelin maps."],
           ['hcp_resample_myelinmaps', 'MyelinMap,SmoothedMyelinMap',             str,    "Comma separated paths to myelin maps."],
           ['hcp_resample_dontfixnames', 'NONE',                                  str,    "A list of comma separated bolds that will not have HCP ICAFix reapplied to them. Only applicable if single-run ICAFix was used. Generally not recommended."],
           ['hcp_resample_myelintarget', 'NONE',                                  str,    "A myelin target file is required to run this pipeline when using a different mesh resolution than the original MSMAll registration."],
           ['hcp_resample_inregname', 'NONE',                                     str,    "A string to enable multiple fMRI resolutions (e.g._1.6mm)."],
           ['hcp_resample_extractnames', '',                                      isNone, "List of bolds and concat names provided in the same format as the hcp_icafix_bolds parameter. Defines which bolds to extract. Exists to enable extraction of a subset of the runs in a multi-run HCP ICAFix group into a new concatenated series."],
           ['hcp_resample_extractextraregnames', '',                              isNone, "Extract multi-run HCP ICAFix runs for additional surface registrations, often MSMSulc."],
           ['hcp_resample_extractvolume', '',                                     isNone, "Whether to also extract the specified multi-run HCP ICAFix from the volume data, requires hcp_resample_extractnames to work."],

           ['# --- hcp_task_fmri_analysis options'],
           ['hcp_task_lvl1tasks', '',                                             isNone, "Comma separated list of task fMRI scan names."],
           ['hcp_task_lvl1fsfs', '',                                              isNone, "Comma separated list of of design names."],
           ['hcp_task_lvl2task', '',                                              isNone, "Name of Level2 subdirectory in which all Level2 feat directories are written for TaskName."],
           ['hcp_task_lvl2fsf', '',                                               isNone, "Prefix of design.fsf filename for the Level2 analysis for TaskName."],
           ['hcp_task_summaryname', '',                                           isNone, "Naming convention for single-subject summary directory. Mandatory when running Level1 analysis only, and should match naming of Level2 summary directories. Default when running Level2 analysis is derived from --hcp_task_lvl2task and --hcp_task_lvl2fsf options tfMRI_TaskName/DesignName_TaskName."],
           ['hcp_task_confound', '',                                              isNone, "Confound matrix text filename (e.g., output of fsl_motion_outliers)."],
           ['hcp_bold_final_smoothFWHM', '',                                      isNone, "Value (in mm FWHM) of total desired smoothing."],
           ['hcp_task_highpass', '',                                              isNone, "Apply additional highpass filter (in seconds) to time series and task design."],
           ['hcp_task_lowpass', '',                                               isNone, "Apply additional lowpass filter (in seconds) to time series and task design."],
           ['hcp_task_procstring', '',                                            isNone, "String value in filename of time series image."],
           ['hcp_task_parcellation', '',                                          isNone, "Name of parcellation scheme to conduct parcellated analysis."],
           ['hcp_task_parcellation_file', '',                                     isNone, "Absolute path to the parcellation dlabel."],
           ['hcp_task_vba', None,                                                 flag,   "VBA YES/NO."],

           ['# --- hcp_asl options'],
           ['hcp_asl_mtname', '',                                                 isNone,  "Filename for empirically estimated MT-correction scaling factors."],
           ['hcp_asl_territories_atlas', '',                                      isNone,  "Atlas of vascular territories from Mutsaerts."],
           ['hcp_asl_territories_labels', '',                                     isNone,  "Labels corresponding to territories_atlas."],
           ['hcp_asl_cores', '',                                                  isNone,  "Number of cores to use when applying motion correction and other potentially multi-core operations."],
           ['hcp_asl_interpolation', '',                                          isNone, "Interpolation order for registrations corresponding to scipy’s map_coordinates function."],
           ['hcp_asl_use_t1', None,                                               flag,   "If specified, the T1 estimates from the satrecov model fit will be used in perfusion estimation in oxford_asl."],
           ['hcp_asl_nobandingcorr', None,                                        flag,   "If this option is provided, MT and ST banding corrections won’t be applied."],

           ['# --- hcp_temporal_ica options'],
           ['hcp_tica_bolds', '',                                                 isNone,  "A comma separated list of fmri run names. Set to all session BOLDs by default."],
           ['hcp_tica_outfmriname',  'rfMRI_REST',                                str,     "Name to use for tICA pipeline outputs."],
           ['hcp_tica_surfregname', '',                                           isNone,  "The registration string corresponding to the input files."],
           ['hcp_tica_procstring', '',                                            isNone,  "File name component representing the preprocessing already done, e.g. _Atlas_MSMAll_hp0_clean."],
           ['hcp_tica_outgroupname', '',                                          isNone,  "Name to use for the group output folder."],
           ['hcp_tica_timepoints', '',                                            isNone,  "Output spectra size for sICA individual projection, RunsXNumTimePoints, like '4800'."],
           ['hcp_tica_num_wishart', '',                                           isNone,  "How many wisharts to use in icaDim."],
           ['hcp_tica_mrfix_concat_name', '',                                     isNone,  "If multi-run FIX was used, you must specify the concat name with this option."],
           ['hcp_tica_icamode', '',                                               isNone,  "Whether to use parts of a previous tICA run"],
           ['hcp_tica_precomputed_clean_folder', '',                              isNone,  "Group folder containing an existing tICA cleanup to make use of for REUSE or INITIALIZE modes."],
           ['hcp_tica_precomputed_fmri_name', '',                                 isNone,  "The output fMRI name used in the previously computed tICA."],
           ['hcp_tica_precomputed_group_name', '',                                isNone,  "The group name used during the previously computed tICA."],
           ['hcp_tica_extra_output_suffix', '',                                   isNone,  "Add something extra to most output filenames, for collision avoidance."],
           ['hcp_tica_pca_out_dim', '',                                           isNone,  "Override number of PCA components to use for group sICA."],
           ['hcp_tica_pca_internal_dim', '',                                      isNone,  "Override internal MIGP dimensionality."],
           ['hcp_tica_migp_resume', '',                                           isNone,  "Resume from a previous interrupted MIGP run, if present. Set to NO to disable this behavior."],
           ['hcp_tica_sicadim_iters', '',                                         isNone,  "Number of iterations or mode for estimating sICA dimensionality, default 100."],
           ['hcp_tica_sicadim_override', '',                                      isNone,  "Use this dimensionality instead of icaDim's estimate., default 100."],
           ['hcp_low_sica_dims', '',                                              isNone,  "The low sICA dimensionalities to use for determining weighting for individual projection."],
           ['hcp_tica_reclean_mode', '',                                          isNone,  "Whether the data should use ReCleanSignal.txt for DVARS."],
           ['hcp_tica_starting_step', '',                                         isNone,  "What step to start processing at, one of: MIGP, GroupSICA, indProjSICA, ConcatGroupSICA, ComputeGroupTICA, indProjTICA, ComputeTICAFeatures, ClassifyTICA, CleanData."],
           ['hcp_tica_stop_after_step', '',                                       isNone,  "What step to stop processing after, same valid values as for hcp_tica_starting_step."],
           ['hcp_tica_remove_manual_components', '',                              isNone,  "Text file containing the component numbers to be removed by cleanup, separated by spaces, requires either --hcp_tica_icamode=REUSE_TICA or --hcp_tica_starting_step=CleanData."],
           ['hcp_tica_fix_legacy_bias', '',                                       isNone,  "Whether the input data used the legacy bias correction, YES or NO."],
           ['hcp_tica_parallel_limit', '',                                        isNone,  "How many subjects to do in parallel (local, not cluster-distributed) during individual projection."],

           ['# --- HCP file checking'],
           ['hcp_prefs_check',        'last',                                     str,    "Whether to check the results of PreFreeSurfer pipeline by last file generated (last), the default list of all files (all) or using a specific check file (path to file)."],
           ['hcp_fs_check',           'last',                                     str,    "Whether to check the results of FreeSurfer pipeline by last file generated (last), the default, list of all files (all), or using a specific check file (path to file)."],
           ['hcp_fslong_check',       'last',                                     str,    "Whether to check the results of FreeSurferLongitudinal pipeline by last file generated (last), the default, list of all files (all), or using a specific check file (path to file)."],
           ['hcp_postfs_check',       'last',                                     str,    "Whether to check the results of PostFreeSurfer pipeline by last file generated (last), the default, list of all files (all), or using a specific check file (path to file)."],
           ['hcp_bold_vol_check',     'last',                                     str,    "Whether to check the results of fMRIVolume pipeline by last file generated (last), the default, list of all files (all), or using a specific check file (path to file)."],
           ['hcp_bold_surf_check',    'last',                                     str,    "Whether to check the results of fMRISurface pipeline by last file generated (last), the default, list of all files (all), or using a specific check file (path to file)."],
           ['hcp_dwi_check',          'last',                                     str,    "Whether to check the results of Diffusion pipeline by last file generated (last), the default, list of all files (all), or using a specific check file (path to file)."],

           ['# --- Processing options'],
           ['run',                    'run',                                      str,    "Run type: run - do the task, test - perform checks."],
           ['log',                    'keep',                                     str,    "Whether to remove ('remove') the temporary logs once jobs are completed, keep them in the study level processing/logs/comlogs folder ('keep' or 'study') in the hcp folder ('hcp') or in a <session id>/logs/comlogs folder ('sessions'). Multiple options can be specified separated by '|'."],
]


#   ---------------------------------------------------------- FLAG DESCRIPTION
#   A list of flags, arguments that do not require additional values. They are
#   listed as a list of flags, each flag is specified with the following
#   elements:
#
#   1/ the name of the element
#   2/ what parameter does it map to
#   3/ what value does it set to the parameter it maps to
#   4/ short description

flaglist = [
    ['test',                     'run',                   'test', 'Run a test only.'],
    ['hcp_dwi_nogpu',            'hcp_dwi_nogpu',         True, 'If specified, use the non-GPU-enabled version of eddy. Defaults to using the GPU-enabled version of eddy.'],
    ['hcp_dwi_selectbestb0',     'hcp_dwi_selectbestb0',  True, "If set selects the best b0 for each phase encoding direction to pass on to topup rather than the default behaviour of using equally spaced b0's throughout the scan. The best b0  is identified as the least distorted (i.e., most similar to the average b0 after registration). The flag is not set by default."],
    ['hcp_asl_use_t1',           'hcp_asl_use_t1',        True, 'If specified, the T1 estimates from the satrecov model fit will be used in perfusion estimation in oxford_asl.'],
    ['hcp_asl_nobandingcorr',    'hcp_asl_nobandingcorr', True, 'If this option is provided, MT and ST banding corrections won’t be applied.'],
    ['hcp_task_vba',             'hcp_task_vba',          True, "VBA YES/NO."],
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
#   sessions. Both are a list of commands in which each command is specified
#   as list of four values:
#
#   1/ command short name
#   2/ command long name
#   3/ the actual function ran for the command
#   4/ a short description of the command
#
#   Empty lists denote there should be a blank line when printing out a command
#   list.

# processing commands
calist = [['mhd',     'map_hcp_data',               process_hcp.map_hcp_data,                       "Map HCP preprocessed data to sessions' image folder."],
          [],
          ['gbd',     'get_bold_data',              workflow.get_bold_data,                         "Copy functional data from 4dfp (NIL) processing pipeline."],
          ['bbm',     'create_bold_brain_masks',    workflow.create_bold_brain_masks,               "Create brain masks for BOLD runs."],
          [],
          ['seg',     'run_basic_segmentation',     fs.runBasicStructuralSegmentation,              "Run basic structural image segmentation."],
          ['gfs',     'get_fs_data',                fs.checkForFreeSurferData,                      "Copy existing FreeSurfer data to sessions' image folder."],
          ['fss',     'run_subcortical_fs',         fs.runFreeSurferSubcorticalSegmentation,        "Run subcortical freesurfer segmentation."],
          ['fsf',     'run_full_fs',                fs.runFreeSurferFullSegmentation,               "Run full freesurfer segmentation"],
          [],
          ['cbs',     'compute_bold_stats',         workflow.compute_bold_stats,                    "Compute BOLD movement and signal statistics."],
          ['csr',     'create_stats_report',        workflow.create_stats_report,                   "Create BOLD movement statistic reports and plots."],
          ['ens',     'extract_nuisance_signal',    workflow.extract_nuisance_signal,               "Extract nuisance signal from BOLD images."],
          [],
          ['bpp',     'preprocess_bold',            workflow.preprocess_bold,                       "Preprocess BOLD images (using old Matlab code)."],
          ['cpp',     'preprocess_conc',            workflow.preprocess_conc,                       "Preprocess conc bundle of BOLD images (using old Matlab code)."],
          [],
          ['hcp1',    'hcp_pre_freesurfer',         process_hcp.hcp_pre_freesurfer,                 "Run HCP PreFS pipeline."],
          ['hcp2',    'hcp_freesurfer',             process_hcp.hcp_freesurfer,                     "Run HCP FS pipeline."],
          ['hcp3',    'hcp_post_freesurfer',        process_hcp.hcp_post_freesurfer,                "Run HCP PostFS pipeline."],
          ['hcp4',    'hcp_fmri_volume',            process_hcp.hcp_fmri_volume,                    "Run HCP fMRI Volume pipeline."],
          ['hcp5',    'hcp_fmri_surface',           process_hcp.hcp_fmri_surface,                   "Run HCP fMRI Surface pipeline."],
          ['hcp6',    'hcp_icafix',                 process_hcp.hcp_icafix,                         "Run HCP ICAFix pipeline."],
          ['hcp7',    'hcp_post_fix',               process_hcp.hcp_post_fix,                       "Run HCP PostFix pipeline."],
          ['hcp8',    'hcp_reapply_fix',            process_hcp.hcp_reapply_fix,                    "Run HCP ReApplyFix pipeline."],
          ['hcp9',    'hcp_msmall',                 process_hcp.hcp_msmall,                         "Run HCP MSMAll pipeline."],
          ['hcp10',   'hcp_dedrift_and_resample',   process_hcp.hcp_dedrift_and_resample,           "Run HCP DeDriftAndResample pipeline."],
          ['hcp11',   'hcp_task_fmri_analysis',     process_hcp.hcp_task_fmri_analysis,             "Run HCP TaskfMRIanalysis pipeline."],
          [],
          ['hcpd',    'hcp_diffusion',              process_hcp.hcp_diffusion,                      "Run HCP DWI pipeline."],
          ['hpca',    'hcp_asl',                    process_hcp.hcp_asl,                            "Run HCP ASL pipeline."],
          # ['hcpdf',   'hcp_dtifit',                 process_hcp.hcp_dtifit,                         "Run FSL DTI fit."],
          # ['hcpdb',   'hcp_bedpostx',               process_hcp.hcp_bedpostx,                       "Run FSL Bedpostx GPU."],
          [],
          ['rsc',     'run_shell_script',           simple.run_shell_script,                        "Runs the specified script."],
          [],
          ['f99',    'dwi_f99',                     fsl.dwi_f99,                                    "Run FSL F99 command."],
          ['fslx',   'dwi_xtract',                  fsl.dwi_xtract,                                 "Run FSL XTRACT command."],
]

# longitudinal commands
lalist = [['lfs',     'longitudinal_freesurfer',    process_hcp.longitudinal_freesurfer,            "Runs longitudinal FreeSurfer across sessions."]]

# multi-session commands
malist = [['hpc_tica', 'hcp_temporal_ica',          process_hcp.hcp_temporal_ica,                   "Run HCP temporal ICA pipeline."]]

salist = [['cbl',     'create_bold_list',           simple.create_bold_list,                        "Create BOLD list"],
          ['ccl',     'create_conc_list',           simple.create_conc_list,                        "Create conc list"],
          ['lsi',     'list_session_info',          simple.list_session_info,                       "List session info"]
]


#   -------------------------------------------------------- COMMAND DICTIONARY
#   Code that transcribes the comand specifications into a dictionary for
#   calling the relevant command when specified.

pactions = {}
for line in calist:
    if len(line) == 4:
        # deprecated command abbreviations 
        # pactions[line[0]] = line[2]
        pactions[line[1]] = line[2]

lactions = {}
for line in lalist:
    if len(line) == 4:
        # deprecated command abbreviations 
        # lactions[line[0]] = line[2]
        lactions[line[1]] = line[2]

mactions = {}
for line in malist:
    if len(line) == 4:
        # deprecated command abbreviations 
        # sactions[line[0]] = line[2]
        mactions[line[1]] = line[2]

sactions = {}
for line in salist:
    if len(line) == 4:
        # deprecated command abbreviations 
        # sactions[line[0]] = line[2]
        sactions[line[1]] = line[2]

# processing, longitudinal and multi-session actions
plactions = {}
plactions.update(pactions.copy())
plactions.update(lactions.copy())

# all actions
allactions = {}
allactions.update(plactions.copy())
allactions.update(mactions.copy())
allactions.update(sactions.copy())

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

    # set command
    options = {'command_ran': command}

    # setup default options
    for line in arglist:
        if len(line) == 4:
            options[line[0]] = line[1]

    # read options from batch.txt
    if 'sessions' in args:
        options['sessions'] = args['sessions']
    if 'sessionids' in args:
        options['sessionids'] = args['sessionids']
    if 'filter' in args:
        options['filter'] = args['filter']

    sessions, gpref = gc.getSessionList(options['sessions'], filter=options['filter'], sessionids=options['sessionids'], verbose=False)

    # check if we are running across subjects rather than sessions
    if command in lactions:
        subjectList = []
        subjectInfo = {}
        for session in sessions:
            if 'subject' not in session:
                raise ge.CommandFailed(command, "Missing subject information", "%s batch file does not provide subject information for session id %s." % (options['subjects'], session['id']), "Please check the batch file!", "Aborting processing!")
            if session['subject'] not in subjectList:
                subjectList.append(session['subject'])
                subjectInfo[session['subject']] = {'id': session['subject'], 'sessions': []}
            if session['subject'] == session['id']:
                raise ge.CommandFailed(command, "Session id matches subject id", "Session id [%s] is the same as subject id [%s]!" % (session['id'], session['subject']), "Please check the batch file!", "Aborting processing!")
            subjectInfo[session['subject']]['sessions'].append(session)
        sessions = [subjectInfo[e] for e in subjectList]

    # take parameters from batch file
    batch_args = gcs.check_deprecated_parameters(gpref, command)
    for (k, v) in batch_args.items():
        options[k] = v

    # parse command line options
    for (k, v) in args.items():
        if k in flist:
            if v != True:
                options[flist[k][0]] = v
            else:
                options[flist[k][0]] = flist[k][1]

        else:
            options[k] = v

    # recode
    for line in arglist:
        if len(line) == 4:
            try:
                options[line[0]] = line[2](options[line[0]])
            except:
                raise ge.CommandError(command, "Invalid parameter value!", "Parameter `%s` is specified but is set to an invalid value:" % (line[0]), '--> %s=%s' % (line[0], str(options[line[0]])), "Please check acceptable inputs for %s!" % (line[0]))

    # take care of variable expansion
    for key in options:
        if type(options[key]) is str:
            options[key] = os.path.expandvars(options[key])

    # set key parameters
    overwrite    = options['overwrite']
    parsessions  = options['parsessions']
    nprocess     = options['nprocess']
    printinfo    = options['datainfo']
    printoptions = options['printoptions']
   
    studyfolders = gc.deduceFolders(options)
    logfolder    = studyfolders['logfolder']
    runlogfolder = os.path.join(logfolder, 'runlogs')
    comlogfolder = os.path.join(logfolder, 'comlogs')
    specfolder   = os.path.join(studyfolders['sessionsfolder'], 'specs')

    options['runlogs']    = runlogfolder
    options['comlogs']    = comlogfolder
    print(f"!!!!! {comlogfolder}")
    options['logfolder']  = logfolder
    options['specfolder'] = specfolder

    # impute unspecified parameters
    options = gcs.impute_parameters(options, command)

    # --------------------------------------------------------------------------
    #                                                       start writing runlog

    for cfolder in [runlogfolder, comlogfolder]:
        if not os.path.exists(cfolder):
            os.makedirs(cfolder)
    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%s")
    logname = os.path.join(runlogfolder, "Log-%s-%s.log") % (command, logstamp)

    log   = []
    stati = []
    sout = "#\nGenerated by QuNex %s on %s\n" % (gc.get_qunex_version(), datetime.now().strftime("%Y-%m-%d_%H.%M.%s"))
    sout += "#\n"
    sout += "=================================================================\n"
    sout += "gmri " + command + " \\\n"

    for (k, v) in args.items():
        sout += '  --%s="%s" \\\n' % (k, v)

    sout += "=================================================================\n"

    # no parsessions for longitudinal and multi-session commands
    if (command in lactions) or (command in mactions):
        if parsessions > 1:
            parsessions = 1
            sout += "\nWARNING: parsessions will be set to 1 because you are running a longitudinal or a multi-session command!\n"

    # check if there are no sessions
    if not sessions:
        sout += "\nERROR: No sessions specified to process. Please check your batch file, filtering options or sessionids parameter!\n"
        print(sout)
        writelog(sout)
        exit()

    elif options['run'] == 'run':
        sout += "\nStarting multiprocessing sessions in %s with a pool of %d concurrent processes\n" % (options['sessions'], parsessions)

    else:
        sout += "\nRunning test on %s ...\n" % (options['sessions'])

    print(sout)
    writelog(sout)

    # -----------------------------------------------------------------------
    #                                                           print options

    if printoptions:
        print("\nFull list of options:")
        writelog("\nFull list of options:\n")
        for line in arglist:
            if len(line) == 4:
                print("%-25s :" % (line[0]), options[line[0]])
                writelog("  %-25s : %s" % (line[0], str(options[line[0]])))

    # -----------------------------------------------------------------------
    #                                                              print info

    if printinfo:
        print(sessions)


    # =======================================================================
    #                                               RUN BY SESSION PROCESSING

    if not os.path.exists(options['sessionsfolder']):
        os.mkdir(options['sessionsfolder'])

    if nprocess > 0:
        nsessions = [sessions.pop(0) for e in range(nprocess) if sessions]
        sessions = nsessions


    # -----------------------------------------------------------------------
    #                                                             local queue

    if options['scheduler'] == 'local':

        consoleLog = ""

        print("---- Running local")
        c = 0
        if parsessions == 1 or options['run'] == 'test':
            # processing and longitudinal commands
            if command in plactions:
                pending_actions = plactions[command]
                for session in sessions:
                    if len(session['id']) > 1:
                        if options['run'] == 'test':
                            action = 'testing'
                        else:
                            action = 'processing'
                        soptions = updateOptions(session, options)
                        consoleLog += "\nStarting %s of sessions %s at %s" % (action, session['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
                        print("\nStarting %s of sessions %s at %s" % (action, session['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S")))
                        r, status = procResponse(pending_actions(session, soptions, overwrite, c + 1))
                        writelog(r)
                        consoleLog += r
                        print(r)
                        stati.append(status)
                        c += 1
                        if nprocess and c >= nprocess:
                            break

            # multi-session commands
            elif command in mactions:
                pending_actions = mactions[command]

                # test or processing
                if options['run'] == 'test':
                    action = 'testing'
                else:
                    action = 'processing'

                # update options and prepare the all sessions string for labeling
                sessionids = ""
                for session in sessions:
                    soptions = updateOptions(session, options)

                    if sessionids == "":
                        sessionids = session['id']
                    else:
                        sessionids = sessionids + "," + session['id']

                # log
                consoleLog += "\nStarting %s of sessions %s at %s" % (action, sessionids, datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
                print("\nStarting %s of sessions %s at %s" % (action, sessionids, datetime.now().strftime("%A, %d. %B %Y %H:%M:%S")))

                # process
                r, status = procResponse(pending_actions(sessions, sessionids, soptions, overwrite, c + 1))

                # write log
                writelog(r)
                consoleLog += r
                print(r)
                stati.append(status)

            # simple processing commands
            elif command in sactions:
                pending_actions = sactions[command]
                soptions = updateOptions(session, options)
                r, status = procResponse(pending_actions(sessions, soptions, overwrite))
                writelog(r)

        else:
            c = 0
            processPoolExecutor = ProcessPoolExecutor(parsessions)
            futures = []
            if command in pactions:
                pending_actions = pactions[command]
                for session in sessions:
                    if len(session['id']) > 1:
                        soptions = updateOptions(session, options)
                        consoleLog += "\nAdding processing of session %s to the pool at %s" % (session['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
                        print("\nAdding processing of session %s to the pool at %s" % (session['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S")))
                        future = processPoolExecutor.submit(pending_actions, session, soptions, overwrite, c + 1)
                        futures.append(future)
                        c += 1
                        if nprocess and c >= nprocess:
                            break

                for future in as_completed(futures):
                    result = future.result()
                    writelog(result)
                    consoleLog += result[0]
                    print(result[0])

            elif command in sactions:
                pending_actions = sactions[command]
                soptions = updateOptions(session, options)
                r, status = procResponse(pending_actions(sessions, soptions, overwrite))
                writelog(r)

        # print(console log)
        # print(consoleLog)

        # create log
        f = open(logname, "w")
        # header
        print("# Generated by QuNex %s on %s" % (gc.get_qunex_version(), datetime.now().strftime("%Y-%m-%d_%H.%M.%s")), file=f)
        print("#", file=f)
        print("\n\n============================= LOG ================================\n", file=f)
        for e in log:
            print(e, file=f)

        print("\n\n===> Final report for command", options['command_ran'])
        print("\n\n===> Final report for command", options['command_ran'], file=f)
        failedTotal = 0

        for sid, report, failed in stati:
            if "Unknown" not in sid:
                print("... %s ---> %s" % (sid, report))
                print("... %s ---> %s" % (sid, report), file=f)
                if failed is None:
                    failedTotal = None
                else:
                    if failedTotal is not None:
                        failedTotal += failed
        if failedTotal is None:
            print("===> Success status not reported for some or all tasks")
            print("===> Success status not reported for some or all tasks", file=f)
        elif failedTotal > 0:
            print("===> Not all tasks completed fully!")
            print("===> Not all tasks completed fully!", file=f)
        else:
            print("===> Successful completion of all tasks")
            print("===> Successful completion of all tasks", file=f)

        f.close()


    # -----------------------------------------------------------------------
    #                                                  general scheduler code

    else:
        # schedule
        gs.runThroughScheduler(command, sessions=sessions, args=args, parsessions=parsessions, logfolder=os.path.join(logfolder, 'batchlogs'), logname=logname)
