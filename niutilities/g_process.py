#!/usr/bin/env python2.7
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
2018-11-14 Jure Demsar
         - Added parelements parameter for bold parallelization
2018-12-12 Jure Demsar
         - Added conc_use parameter for absolute or relative path
           interpretation from conc files.
2019-01-13 Jure Demsar
         - Fixed a bug that disabled parsessions parameter with the
           introduction of the parelements parameter.
2019-09-20 Jure Demsar
         - Have all the files listed with the original name
           in subject_<pipeline>.txt.
"""

# general imports
import g_core
import gp_workflow
import gp_simple
import gp_FS
import g_scheduler
import os
import os.path
from datetime import datetime
import niutilities.g_exceptions as ge
from concurrent.futures import ProcessPoolExecutor, as_completed

# pipelines imports
from HCP import gp_HCP


# =======================================================================
#                                                                 GLOBALS

log     = []
stati   = []
logname = ""


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
           ['sessions',           'batch.txt',                                   str,    "The file with sessions information."],
           ['subjectsfolder',     '',                                            os.path.abspath, 'The path to study subjects folder.'],
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
           ['sessionids',         '',                                            str,  "list of | separated session ids for which to run the command"],

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
           ['bold_prefix',        '',                                            str,    "an optional prefix to place in front of processing name extensions in the resulting files"],
           ['pignore',            '',                                            str,    "what to do with frames marked as bad"],
           ['event_file',         '',                                            str,    "the root name of the fidl event file for task regression"],
           ['event_string',       '' ,                                           str,    "string specifying what and how of task to regress out"],
           ['source_folder',      'True',                                        torf,   "hould we check for source folder (yes/no)"],
           ['wbmask',             '',                                            str,    "mask specifying what ROI to exclude from WB mask"],
           ['sbjroi',             '',                                            str,    "a mask used to specify subject specific WB"],
           ['nroi',               '',                                            str,    "additional nuisance regressors ROI and which not to mask by brain mask (e.g. 'nroi.names|eyes,scull')"],
           ['shrinknsroi',        'true',                                        str,    "whether to shrink signal nuisance ROI (V,WM,WB) true or false"],
           ['path_bold',          'bold[N]/*faln_dbnd_xr3d_atl.4dfp.img',        str,    "the mask to use for searching for bold images"],
           ['path_mov',           'movement/*_b[N]_faln_dbnd_xr3d.dat',          str,    "the mask to use for searching for movement files"],
           ['path_t1',            'atlas/*_mpr_n*_111_t88.4dfp.img',             str,    "the mask to use for searching for T1 file"],
           ['image_source',       'hcp',                                         str,    "what is the target source file format / structure (4dfp, hcp)"],
           ['image_target',       'nifti',                                       str,    "what is the target file format (4dfp, nifti, dtseries, ptseries)"],
           ['image_atlas',        'cifti',                                       str,    "what is the target atlas (711, cifti)"],
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

           ['# --- HCP options'],
           ['hcp_processing_mode',    'HCPStyleData',                             str,    "Controls whether the HCP acquisition and processing guidelines should be treated as requirements (HCPStyleData) or if additional processing functionality is allowed (LegacyStyleData)"],
           ['hcp_folderstructure',    'hcpls',                                    str,    "Which version of HCP folder structure to use, initial or hcpls ['hcpls']"],
           ['hcp_freesurfer_home',    '',                                         str,    "path to FreeSurfer base folder"],
           ['hcp_freesurfer_module',  '',                                         str,    "Whether to load FreeSurfer as a module on the cluster: YES or NONE"],
           ['hcp_Pipeline',           '',                                         str,    "path to pipeline base folder"],
           ['hcp_suffix',             '',                                         str,    "session id suffix if running HCP preprocessing variants"],
           ['hcp_filename',           'standard',                                 str,    "How to name the image files in the hcp structure. The default is to name them by their number ('standard') using formula '<hcp_bold_prefix>_[N]' (e.g. BOLD_1), the alternative is to use their actual names ('original') (e.g. rfMRI_REST1_AP). ['standard']"],
           ['hcp_brainsize',          '150',                                      int,    "human brain size in mm"],
           ['hcp_t2',                 't2',                                       str,    "whether T2 image is present - anything or NONE"],
           ['hcp_fmap',               '',                                         str,    "DEPRECATED!!! whether hi-res structural fieldmap is present - SiemensFieldMap for Siemens Phase/Magnitude pair, or GeneralElectricFieldMap for GE single B0 image, ['']"],
           ['hcp_echodiff',           '',                                         str,    "the delta in TE times for the hi-res fieldmap image ['']"],
           ['hcp_sephaseneg',         '',                                         str,    "spin echo field map volume with a negative phase encoding direction: (AP, PA, LR, RL) ['']"],
           ['hcp_sephasepos',         '',                                         str,    "spin echo field map volume with a positive phase encoding direction: (AP, PA, LR, RL) ['']"],
           ['hcp_seechospacing',      '',                                         str,    "Echo Spacing or Dwelltime of Spin Echo Field Map or '' if not used"],
           ['hcp_seunwarpdir',        '',                                         str,    "Phase encoding direction of the spin echo field map. (Only applies when using a spin echo field map.) ['']"],
           ['hcp_t1samplespacing',    '',                                         str,    "0.0000074 ... DICOM field (0019,1018) in s or '' if not used"],
           ['hcp_t2samplespacing',    '',                                         str,    "0.0000021 ... DICOM field (0019,1018) in s or '' if not used"],
           ['hcp_unwarpdir',          '',                                         str,    "Readout direction of the T1w and T2w images (Used with either a regular field map or a spin echo field map) z appears to be best or '' if not used"],
           ['hcp_gdcoeffs',           '',                                         str,    "Location of gradient coefficient file, a string describing mulitiple options, or '' to skip"],
           ['hcp_avgrdcmethod',       'NONE',                                     str,    "Averaging and readout distortion correction methods: 'NONE' = average any repeats with no readout correction 'FIELDMAP' or 'SiemensFieldMap' or 'GeneralElectricFieldMap' = average any repeats and use field map for readout correction 'TOPUP' = average and distortion correct at the same time with topup/applytopup only works for 2 images currently"],
           ['hcp_topupconfig',        '',                                         str,    "A full path to the topup configuration file to use. Set to '' if the default is to be used or of TOPUP distortion correction is not used."],
           ['hcp_bfsigma',            '',                                         str,    "Bias Field Smoothing Sigma (optional)"],
           ['hcp_prefs_check',        'last',                                     str,    "Whether to check the results of PreFreeSurfer pipeline by last file generated (last), the default list of all files (all) or using a specific check file (path to file) [last]"],
           ['hcp_prefs_custombrain',  '',                                         str,    "Whether to use a custom bain mask (MASK) or custom brain images (CUSTOM) in PreFS or not (NONE; the default)"],
           ['hcp_prefs_template_res', '0.7',                                      str,    "The resolution (in mm) of the structural images templates to use in the prefs step."],
           ['hcp_usejacobian',        '',                                         str,    "Not currently in usage (optional)"],
           ['hcp_printcom',           '',                                         str,    "Print command for the HCP scripts: set to echo to have commands printed and not executed."],
           ['hcp_expert_file',        '',                                         str,    "Name of the read-in expert options file for FreeSurfer"],
           ['hcp_control_points',     '',                                         str,    "Whether to run with manual control points"],
           ['hcp_wm_edits',           '',                                         str,    "Whether to run with manually edited WM mask file"],
           ['hcp_autotopofix_off',    '',                                         str,    "YES to turn off the automatic topologic fix step in FS and compute WM surface deterministically from manual WM mask (empty)"],
           ['hcp_fs_brainmask',       '',                                         str,    "Specify 'original' to keep the masked original brainimage; 'manual' to use the manually edited brainmask file; default 'fs'uses the brainmask generated by mri_watershed [fs]."],
           ['hcp_fs_longitudinal',    '',                                         str,    "Is this FreeSurfer run to be based on longitudional data? YES or NO, [NO]"],
           ['hcp_fs_seed',            '',                                         str,    "Recon-all seed value. If not specified, none will be used. HCP Pipelines specific!"],
           ['hcp_fs_existing_session','FALSE',                                    torf,   "Indicates that the command is to be run on top of an already existing analysis/subject. This excludes the `-i` flag from the invocation of recon-all. If set, the user needs to specify which recon-all stages to run using the --hcp_fs_extra_reconall parameter. Accepted values are TRUE or FALSE [FALSE]. HCP Pipelines specific!"],
           ['hcp_fs_extra_reconall',  '',                                         str,    "A string with extra parameters to pass to FreeSurfer recon-all. The extra parameters are to be listed in a pipe ('|') separated string. Parameters and their values need to be listed separately. E.g. to pass `-norm3diters 3` to reconall, the string has to be: \"-norm3diters|3\" []. HCP Pipelines specific!"],
           ['hcp_fs_no_conf2hires',   'FALSE',                                    torf,   "Indicates that (most commonly due to low resolution—1mm or less—of structural image(s), high-resolution steps of recon-all should be excluded. Accepted values are TRUE or FALSE [FALSE]"],
           ['hcp_fs_flair',           'FALSE',                                    torf,   "If set to TRUE indicates that recon-all is to be run with the -FLAIR/-FLAIRpial options(rather than the -T2/-T2pial options). The FLAIR input image itself should still be provided via the '--t2' argument."],
           ['hcp_fs_check',           'last',                                     str,    "Whether to check the results of FreeSurfer pipeline by last file generated (last), the default, list of all files (all), or using a specific check file (path to file) [last]"],
           ['hcp_fslong_check',       'last',                                     str,    "Whether to check the results of FreeSurferLongitudinal pipeline by last file generated (last), the default, list of all files (all), or using a specific check file (path to file) [last]"],
           ['hcp_postfs_check',       'last',                                     str,    "Whether to check the results of PostFreeSurfer pipeline by last file generated (last), the default, list of all files (all), or using a specific check file (path to file) [last]"],
           ['hcp_grayordinatesres',   '2',                                        int,    "Usually 2mm"],
           ['hcp_hiresmesh',          '164',                                      int,    "Usually 164 vertices"],
           ['hcp_lowresmesh',         '32',                                       int,    "Usually 32 vertices"],
           ['hcp_regname',            'MSMSulc',                                  str,    "What registration is used FS or MSMSulc. FS if none is provided."],
           ['hcp_mcsigma',            '',                                         str,    "Correction sigma used for metric smooting (sqrt(200): 14.14213562373095048801) ['']."],
           ['hcp_inflatescale',       '1',                                        str,    "Inflate extra scale parameter [1]."],
           ['hcp_cifti_tail',          '',                                        str,    "The tail of the cifti file to use when mapping data from the HCP MNINonLinear/Results folder."],
           ['hcp_bold_prefix',        'BOLD_',                                    str,    "The prefix to use when generating bold names (see 'hcp_bold_name') for bold working folders and results"],
           ['hcp_bold_variant',       '',                                         str,    "The suffix to add to 'MNINonLinear/Results' and 'images/functional' folders. '' by default"],
           ['hcp_bold_biascorrection','NONE',                                     str,    "Whether to perform bias correction for BOLD images. NONE, LEGACY or SEBASED (for TOPUP DC only). HCP Pipelines only!"],
           ['hcp_bold_usejacobian',   '',                                         str,    "Whether to apply the jacobian of the distortion correction to fMRI data. HCP Pipelines only!"],
           ['hcp_bold_echospacing',   '',                                         str,    "Echo Spacing or Dwelltime of fMRI image in seconds"],
           ['hcp_bold_dcmethod',      '',                                         str,    "BOLD image deformation correction: TOPUP, FIELDMAP / SiemensFieldMap, GeneralElectricFieldMap or NONE"],
           ['hcp_bold_sephaseneg',    '',                                         str,    "Spin echo field map volume to use for BOLD TOPUP with a negative phase encoding direction (AP, PA, LR, RL), ['']"],
           ['hcp_bold_sephasepos',    '',                                         str,    "Spin echo field map volume to use for BOLD TOPUP with a positive phase encoding direction (AP, PA, LR, RL), ['']"],           
           ['hcp_bold_topupconfig',   '',                                         str,    "A full path to the topup configuration file to use. Set to '' if the default is to be used or of TOPUP distortion correction is not used."],
           ['hcp_bold_dof',           '',                                         str,    "Degrees of freedom for EPI-T1 FLIRT. Empty to use HCP default."],
           ['hcp_bold_sbref',         'NONE',                                     str,    "Whether BOLD image Reference images should be used - NONE or USE"],
           ['hcp_bold_echodiff',      'NONE',                                     str,    "Delta TE in ms for BOLD fieldmap images or NONE if not used"],
           ['hcp_bold_unwarpdir',     'y',                                        str,    "The direction of unwarping, can be specified separately for LR/RL: e.g. 'LR=x|RL=-x|x' or similarly for AP/PA"],
           ['hcp_bold_res',           '2',                                        str,    "Target image resolution 2mm recommended"],
           ['hcp_bold_gdcoeffs',      'NONE',                                     str,    "Gradient distorsion correction coefficients or NONE"],
           ['hcp_bold_doslicetime',   '',                                         str,    "Whether to do slice timing correction TRUE or FALSE (default)"],
           ['hcp_bold_slicetimerparams' ,'',                                      str,    "A comma or pipe separated string of parameters for FSL slicetimer."],
           ['hcp_bold_stcorrdir',     '',                                         str,    "The direction of slice acquisition NOTE: deprecated!"],
           ['hcp_bold_stcorrint',     '',                                         str,    "Whether slices were acquired in an interleaved fashion (odd) or not (empty) NOTE: deprecated!"],
           ['hcp_bold_movref',        'independent',                              str,    "What reference to use for movement correction (independent, first)"],
           ['hcp_bold_seimg',         'independent',                              str,    "What image to use for spin-echo distorsion correction (independent, first)"],
           ['hcp_bold_smoothFWHM',    '2',                                        str,    "Whether slices were acquired in an interleaved fashion (odd or even) or not (empty)"],
           ['hcp_bold_mask',          '',                                         str,    "Specifies what mask to use for the final bold. T1_fMRI_FOV: combined T1w brain mask and fMRI FOV masks (the default), T1_DILATED_fMRI_FOV: a once dilated T1w brain based mask combined with fMRI FOV, T1_DILATED2x_fMRI_FOV: a twice dilated T1w brain based mask combined with fMRI FOV, fMRI_FOV: a fMRI FOV mask."],
           ['hcp_bold_preregistertool','',                                        str,    "What code to use to preregister BOLDs before FSL BBR epi_reg (default) or flirt"],
           ['hcp_bold_refreg',        '',                                         str,    "Whether to use only linaer (default) or also nonlinear registration of motion corrected bold to reference"],
           ['hcp_bold_movreg',        'MCFLIRT',                                  str,    "Whether to use FLIRT or MCFLIRT for motion correction"],
           ['hcp_bold_vol_check',     'last',                                     str,    "Whether to check the results of fMRIVolume pipeline by last file generated (last), the default, list of all files (all), or using a specific check file (path to file) [last]"],
           ['hcp_bold_surf_check',    'last',                                     str,    "Whether to check the results of fMRISurface pipeline by last file generated (last), the default, list of all files (all), or using a specific check file (path to file) [last]"],
           ['hcp_dwi_PEdir',          '1',                                        str,    "Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior"],
           ['hcp_dwi_gdcoeffs',       'NONE',                                     str,    "DWI specific gradient distorsion coefficients file or NONE"],
           ['hcp_dwi_echospacing',    '',                                         str,    "Echo spacing in msec."],
           ['hcp_dwi_dof',            '6',                                        str,    "Degrees of Freedom for post eddy registration to structural images. Defaults to 6."],
           ['hcp_dwi_b0maxbval',      '50',                                       str,    "Volumes with a bvalue smaller than this value will be considered as b0s. Defaults to 50"],
           ['hcp_dwi_extraeddyarg',   '',                                         str,    "A string specifying additional arguments to pass to eddy processing. Defaults to ''"],
           ['hcp_dwi_combinedata',    '1',                                        str,    "Specified value is passed as the CombineDataFlag value for the eddy_postproc.sh script. If JAC resampling has been used in eddy, this value determines what to do with the output file: 2 - include in the output all volumes uncombined (i.e. output file of eddy); 1 - include in the output and combine only volumes where both LR/RL (or AP/PA) pairs have been acquired; 0 - As 1, but also include uncombined single volumes. Defaults to 1"],
           ['hcp_dwi_check',          'last',                                     str,    "Whether to check the results of Diffusion pipeline by last file generated (last), the default, list of all files (all), or using a specific check file (path to file) [last]"],

           ['# --- Processing options'],
           ['run',                    'run',                                      str,    "run type: run - do the task, test - perform checks"],
           ['log',                    'keep',                                     str,    "Whether to remove ('remove') the temporary logs once jobs are completed, keep them in the study level processing/logs/comlogs folder ('keep' or 'study') in the hcp folder ('hcp') or in a <session id>/logs/comlogs folder ('sessions'). Multiple options can be specified separated by '|'."]
          ]


#   --------------------------------------------------------- PARAMETER MAPPING
#   For historical reasons and to maintain backward compatibility, some of the
#   parameters need to be mapped to a parameter with another name. The "tomap"
#   dictionary specifies what is mapped to what.

tomap = {'bppt':                    'bolds',
         'bppa':                    'bold_actions',
         'bppn':                    'bold_nuisance',
         'eventstring':             'event_string',
         'eventfile':               'event_file',
         'basefolder':              'subjectsfolder',
         'subjects':                'sessions',
         'bold_preprocess':         'bolds',
         'hcp_prefs_brainmask':     'hcp_prefs_custombrain',
         'hcp_mppversion':          'hcp_processing_mode',
         'hcp_dwelltime':           'hcp_seechospacing',
         'hcp_bold_ref':            'hcp_bold_sbref',
         'hcp_bold_preregister':    'hcp_bold_preregistertool',
         'hcp_bold_stcorr':         'hcp_bold_doslicetime',
         'hcp_bold_correct':        'hcp_bold_dcmethod',
         'hcp_bold_usemask':        'hcp_bold_mask',
         'hcp_bold_boldnamekey':    'hcp_filename',
         'hcp_dwi_dwelltime':       'hcp_dwi_echospacing',
         'cores':                   'parsessions',
         'threads':                 'parelements',
         'subjid':                  'sessionids',
         'sfolder':                 'sourcefolder',
         'tfolder':                 'targetfolder',
         'tfile':                   'targetfile',
         'sfile':                   {
                                        'sessionfile': ['runNIL', 'runNILFolder'],
                                        'sourcefiles': ['createBatch', 'pullSequenceNames', 'gatherBehavior'],
                                        'sourcefile': ['createSessionInfo', 'setupHCP', 'sliceImage']
                                    },
         'sfilter':                 'filter',
         'hcp_fs_existing_subject': 'hcp_fs_existing_session'
         }

mapValues = {'hcp_processing_mode': {'hcp': 'HCPStyleData', 'legacy': 'LegacyStyleData'},
             'hcp_filename': {'name': 'original', 'number': 'standard'}}

deprecated = {'hcp_bold_stcorrdir': 'hcp_bold_slicetimerparams', 
              'hcp_bold_stcorrint': 'hcp_bold_slicetimerparams',
              'hcp_bold_sequencetype': None,
              'hcp_biascorrect_t1w': None}


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

calist = [['mhd',     'mapHCPData',                  gp_HCP.mapHCPData,                              "Map HCP preprocessed data to sessions' image folder."],
          [],
          ['gbd',     'getBOLDData',                 gp_workflow.getBOLDData,                        "Copy functional data from 4dfp (NIL) processing pipeline."],
          ['bbm',     'createBOLDBrainMasks',        gp_workflow.createBOLDBrainMasks,               "Create brain masks for BOLD runs."],
          [],
          ['seg',     'runBasicSegmentation',        gp_FS.runBasicStructuralSegmentation,           "Run basic structural image segmentation."],
          ['gfs',     'getFSData',                   gp_FS.checkForFreeSurferData,                   "Copy existing FreeSurfer data to sessions' image folder."],
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
          ['hcp6',    'hcp_ICAFix',                  gp_HCP.hcpICAFix,                               "Run HCP ICAFix pipeline."],
          ['hcp7',    'hcp_PostFix',                 gp_HCP.hcpPostFix,                              "Run HCP PostFix pipeline."],
          ['hcp8',    'hcp_ReApplyFix',              gp_HCP.hcpReApplyFix,                           "Run HCP ReApplyFix pipeline."],
          ['hcp9',    'hcp_MSMAll',                  gp_HCP.hcpMSMAll,                               "Run HCP MSMAll pipeline."],
          ['hcp10',   'hcp_DeDriftAndResample',      gp_HCP.hcpDeDriftAndResample,                   "Run HCP DeDriftAndResample pipeline."],
          [],
          ['hcpd',    'hcp_Diffusion',               gp_HCP.hcpDiffusion,                            "Run HCP DWI pipeline."],
          # ['hcpdf',   'hcp_DTIFit',                  gp_HCP.hcpDTIFit,                               "Run FSL DTI fit."],
          # ['hcpdb',   'hcp_Bedpostx',                gp_HCP.hcpBedpostx,                             "Run FSL Bedpostx GPU."],
          [],
          ['rsc',     'runShellScript',              gp_simple.runShellScript,                       "Runs the specified script."],
          ]

lalist = [['lfs',     'longitudinalFS',              gp_HCP.longitudinalFS,                          "Runs longitudinal FreeSurfer across sessions."]
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

lactions = {}
for line in lalist:
    if len(line) == 4:
        lactions[line[0]] = line[2]
        lactions[line[1]] = line[2]

plactions = pactions.copy()
plactions.update(lactions)

sactions = {}
for line in salist:
    if len(line) == 4:
        sactions[line[0]] = line[2]
        sactions[line[1]] = line[2]

allactions = plactions.copy()
allactions.update(sactions)

flist = {}
for line in flaglist:
    if len(line) == 4:
        flist[line[0]] = [line[1], line[2]]


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
    print >> f, r
    f.close()


def procResponse(r):
    '''
    procResponse(r)
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
    if s in ['None', 'none', 'NONE', '']:
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


def updateOptions(session, options):
    '''
    updateOptions(session, options)
    Returns an updated copy of options dictionary where all keys from 
    sessions that started with an underscore '_' are mapped into options.
    '''
    soptions = dict(options)
    for key, value in session.iteritems():
        if key.startswith('_'):
            soptions[key[1:]] = value
    return soptions


def mapDeprecated(options, command):
    '''
    mapDeprecated(options, command)
    Checks for deprecated parameters, remaps deprecated ones
    and notifes the user.
    '''

    remapped   = []
    deprecated = []
    newvalues  = []

    # -> check remapped parameters
    # variable for storing new options
    newOptions = {}
    # iterate over all options
    for k, v in options.iteritems():
        if k in tomap:
            # if v is a dictionary then
            # the parameter was remaped to multiple values
            mapto = tomap[k]
            if type(mapto) is dict:
                for k2, v2 in mapto.iteritems():
                    if command in v2:
                        mapto = k2
                        break

            # remap
            newOptions[mapto] = v
            remapped.append(k)
        else:
            newOptions[k] = v

    # save
    options = newOptions

    if remapped:
        print("\nWARNING: Use of parameters with changed name(s)!\n       The following parameters have new names and will be deprecated:")
        for k in remapped:
            print("         ... %s is now %s!" % (k, tomap[k]))

        print("         Please correct the listed parameter names in command line or batch file!")

    # -> check deprecated parameters
    for k, v in options.iteritems():
        if k in deprecatedList:
            if v:
                deprecated.append((k, v, deprecatedList[k]))

    if deprecated:
        print "\nWARNING: Use of deprecated parameter(s)!"
        for k, v, n in deprecated:
            if n:
                print "         ... %s (current value: %s) is replaced by the parameter %s!" % (k, str(v), n)
            else:
                print "         ... %s (current value: %s) is being deprecated!" % (k, str(v))
        print "         Please stop using the listed parameters in command line or batch file, and, when indicated, consider using the replacement parameter!"  

    # -> check new parameter values
    for k, v in options.iteritems():
        if k in mapValues:
            if v in mapValues[k]:
                options[k] = mapValues[k][v]
                newvalues.append([k, v, mapValues[k][v]])

    if newvalues:
        print "\nWARNING: Use of deprecated parameter value(s)!\n       The following parameter values have new names:"
        for k, v, n in newvalues:
            print "         ... %s (%s) is now %s!" % (str(v), k, n)            
        print "         Please correct the listed parameter values in command line or batch file!"


# ==============================================================================
#                                                               RUNNING COMMANDS
#

def run(command, args):

    global log
    global stati
    global logname

    # --------------------------------------------------------------------------
    #                                                            Parsing options

    # --- set command

    options = {'command_ran': command}

    # --- set up default options

    for line in arglist:
        if len(line) == 4:
            options[line[0]] = line[1]

    # --- read options from batch.txt

    if 'sessions' in args:
        options['sessions'] = args['sessions']
    if 'sessionids' in args:
        options['sessionids'] = args['sessionids']
    if 'filter' in args:
        options['filter'] = args['filter']

    sessions, gpref = g_core.getSubjectList(options['sessions'], filter=options['filter'], sessionids=options['sessionids'], verbose=False)

    # --- check if we are running across subjects rather than sessions

    if command in lactions:
        subjectList = []
        subjectInfo = {}
        for session in sessions:
            if 'subject' not in session:
                raise ge.CommandFailed(command, "Missing subject information", "%s batch file does not provide subject information for session id %s." % (options['subjects'], subject['id']), "Please check the batch file!", "Aborting processing!")
            if session['subject'] not in subjectList:
                subjectList.append(subject['subject'])
                subjectInfo[session['subject']] = {'id': session['subject'], 'sessions': []}
            if session['subject'] == session['id']:
                raise ge.CommandFailed(command, "Session id matches subject id", "Session id [%s] is the same as subject id [%s]!" % (subject['id'], subject['subject']), "Please check the batch file!", "Aborting processing!")
            subjectInfo[session['subject']]['sessions'].append(session)
        sessions = [subjectInfo[e] for e in subjectList]

    # --- take parameters from batch file

    for (k, v) in gpref.iteritems():
        options[k] = v

    mapDeprecated(options, command)

    # --- parse command line options

    for (k, v) in args.iteritems():
        if k in flist:
            options[flist[k][0]] = flist[k][1]
        else:
            options[k] = v

    mapDeprecated(options, command)

    # ---- Recode

    for line in arglist:
        if len(line) == 4:
            try:
                options[line[0]] = line[2](options[line[0]])
            except:
                raise ge.CommandError(command, "Invalid parameter value!", "Parameter `%s` is specified but is set to an invalid value:" % (line[0]), '--> %s=%s' % (line[0], str(options[line[0]])), "Please check acceptable inputs for %s!" % (line[0]))


    # ---- Take care of variable expansion

    for key in options:
        if type(options[key]) is str:
            options[key] = os.path.expandvars(options[key])


    # ---- Set key parameters

    overwrite    = options['overwrite']
    parsessions  = options['parsessions']
    nprocess     = options['nprocess']
    printinfo    = options['datainfo']
    printoptions = options['printoptions']
   
    studyfolders = g_core.deduceFolders(options)
    logfolder    = studyfolders['logfolder']
    runlogfolder = os.path.join(logfolder, 'runlogs')
    comlogfolder = os.path.join(logfolder, 'comlogs')
    specfolder   = os.path.join(studyfolders['subjectsfolder'], 'specs')

    options['runlogs']    = runlogfolder
    options['comlogs']    = comlogfolder
    options['logfolder']  = logfolder
    options['specfolder'] = specfolder

    # --------------------------------------------------------------------------
    #                                                       start writing runlog

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

    if not sessions:
        sout += "\nERROR: No sessions specified to process. Please check your batch file, filtering options or sessionids parameter!"
        print sout
        writelog(sout)
        exit()

    elif options['run'] == 'run':
        sout += "\nStarting multiprocessing sessions in %s with a pool of %d concurrent processes\n" % (options['sessions'], parsessions)

    else:
        sout += "\nRunning test on %s ...\n" % (options['sessions'])

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
        print sessions


    # =======================================================================
    #                                               RUN BY SUBJECT PROCESSING

    if not os.path.exists(options['subjectsfolder']):
        os.mkdir(options['subjectsfolder'])

    if nprocess > 0:
        nsessions = [sessions.pop(0) for e in range(nprocess) if sessions]
        sessions = nsessions


    # -----------------------------------------------------------------------
    #                                                             local queue

    if options['scheduler'] == 'local' or options['run'] == 'test':

        consoleLog = ""

        print "---- Running local"
        c = 0
        if parsessions == 1 or options['run'] == 'test':
            if command in plactions:
                todo = plactions[command]
                for session in sessions:
                    if len(session['id']) > 1:
                        if options['run'] == 'test':
                            action = 'testing'
                        else:
                            action = 'processing'
                        soptions = updateOptions(session, options)
                        consoleLog += "\nStarting %s of sessions %s at %s" % (action, session['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
                        print "\nStarting %s of sessions %s at %s" % (action, session['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
                        r, status = procResponse(todo(session, soptions, overwrite, c + 1))
                        writelog(r)
                        consoleLog += r
                        print r
                        stati.append(status)
                        c += 1
                        if nprocess and c >= nprocess:
                            break

            if command in sactions:
                todo = sactions[command]
                soptions = updateOptions(session, options)
                r, status = procResponse(todo(sessions, soptions, overwrite))
                writelog(r)

        else:
            c = 0
            processPoolExecutor = ProcessPoolExecutor(parsessions)
            futures = []
            if command in plactions:
                todo = plactions[command]
                for session in sessions:
                    if len(session['id']) > 1:
                        soptions = updateOptions(session, options)
                        consoleLog += "\nAdding processing of session %s to the pool at %s" % (session['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
                        print "\nAdding processing of session %s to the pool at %s" % (session['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
                        future = processPoolExecutor.submit(todo, session, soptions, overwrite, c + 1)
                        futures.append(future)
                        c += 1
                        if nprocess and c >= nprocess:
                            break

                for future in as_completed(futures):
                    result = future.result()
                    writelog(result)
                    consoleLog += result[0]
                    print result[0]

            if command in sactions:
                todo = sactions[command]
                soptions = updateOptions(session, options)
                r, status = procResponse(todo(sessions, soptions, overwrite))
                writelog(r)

        # print console log
        # print consoleLog

        # --- Create log

        f = open(logname, "w")
        print >> f, "\n\n============================= LOG ================================\n"
        for e in log:
            print >> f, e

        print "\n\n===> Final report for command", options['command_ran']
        print >> f, "\n\n===> Final report for command", options['command_ran']
        failedTotal = 0

        for sid, report, failed in stati:
            if "Unknown" not in sid:
                print "... %s ---> %s" % (sid, report)
                print >> f, "... %s ---> %s" % (sid, report)
                if failed is None:
                    failedTotal = None
                else:
                    if failedTotal is not None:
                        failedTotal += failed
        if failedTotal is None:
            print "===> Success status not reported for some or all tasks"
            print >> f, "===> Success status not reported for some or all tasks"
        elif failedTotal > 0:
            print "===> Not all tasks completed fully!"
            print >> f, "===> Not all tasks completed fully!"
        else:
            print "===> Successful completion of all tasks"
            print >> f, "===> Successful completion of all tasks"

        f.close()


    # -----------------------------------------------------------------------
    #                                                  general scheduler code

    else:
        g_scheduler.runThroughScheduler(command, sessions=sessions, args=options, parsessions=parsessions, logfolder=os.path.join(logfolder, 'batchlogs'), logname=logname)

