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
import sys
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

import general.scheduler as gs
import general.core as gc
import general.exceptions as ge
import general.commands_support as gcs
from processing import fs, simple, workflow, dwi, fsl, rapidtide
from general.bids import map_nii2bids
from general import extensions

# pipelines imports
from hcp import process_hcp

# qx_mice
import qx_mice
from qx_mice import setup_mice, process_mice


# =======================================================================
#                                                                 GLOBALS
log = []
stati = []
logname = ""


# =======================================================================
#                                                       SUPPORT FUNCTIONS
def writelog(item):
    """
    ``writelog(item)``

    Splits the passed item into two parts and appends the first to the
    global log list, and the second to the global stati list. It also
    prints the contents to the file specified in the global logname
    variable.
    """
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
    """
    ``procResponse(r)``

    It processes the response returned from the utilities functions
    called. It splits it into the report string and status tuple. If
    no status tupple is present, it adds an "Unknown" tupple. If the
    third element is missing, it assumes it ran ok and sets it to
    0.
    """

    if type(r) is tuple:
        if len(r) == 2:
            if len(r[1]) == 2:
                return (r[0], (r[1][0], r[1][1], None))
            elif len(r[1]) == 3:
                return r
            else:
                return ("Unknown", ("Unknown", "Unknown", None))
        else:
            return ("Unknown", ("Unknown", "Unknown", None))
    else:
        return (r, ("Unknown", "Unknown", None))


def torf(s):
    """
    ``torf(s)``

    First checks if string is "None", 'none', or "NONE" and returns
    None, then Checks if s is any of the possible true strings: "True", "true",
    or "TRUE" and returns a boolean result of the check.
    """
    if s in ["None", "none", "NONE"]:
        return None
    else:
        return s in ["True", "true", "TRUE", "yes", "Yes", "YES", True]


def flag(f):
    """
    ``flag(f)``

    Converts a flag (f) passed as a string to a boolean.
    """

    if type(f) == bool:
        return f
    elif f in ["True", "true", "TRUE", "yes", "Yes", "YES"]:
        return True
    else:
        return False


def isNone(s):
    """
    ``isNone(s)``

    Check if the string is "" and returns None, otherwise
    returns the passed string.
    """

    if s in [""]:
        return None
    else:
        return s


def update_options(session, options):
    """
    ``update_options(session, options)``

    Returns an updated copy of options dictionary where all keys from
    sessions that started with an underscore '_' are mapped into options.
    """
    soptions = dict(options)
    for key, value in session.items():
        if key.startswith("_"):
            soptions[key[1:]] = value
        elif key.startswith("--"):
            soptions[key[2:]] = value

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
#
#  Parameters are divided into sections. Every section starts with a list
#  of a single string element in the form "# ---- <section title>".
arglist = [
    ["# ---- Basic settings"],
    ["batchfile", "", str],
    ["sessions", "", str],
    ["sessionsfolder", "", os.path.abspath],
    ["logfolder", "", isNone],
    ["logtag", "", str,],
    ["overwrite", "no", torf,],
    ["parsubjects", "1", int,],
    ["parsessions", "1", int,],
    ["parelements", "1", int,],
    ["nprocess", "0", int,],
    ["datainfo", "False", torf,],
    ["printoptions", "False", torf,],
    ["filter", "", str,],
    ["script", "", isNone,],
    ["sessionid", "", str,],
    ["sessionids", "", str,],
    ["# ---- Preprocessing options"],
    ["bet", "-f 0.5", str,],
    ["fast", "-t 1 -n 3 --nopve", str,],
    ["betboldmask", "-R -m", str,],
    ["tr", "2.5", float,],
    ["omit", "5", int,],
    ["bold_actions", "shrcl", str,],
    ["bold_nuisance", "m,V,WM,WB,1d", str,],
    ["bolds", "all", str,],
    ["boldname", "bold", str,],
    ["qx_nifti_tail", "", isNone,],
    ["qx_cifti_tail", "", isNone,],
    ["nifti_tail", "", isNone,],
    ["cifti_tail", "", isNone,],
    ["bold_prefix", "", str,],
    ["bold_variant", "", str,],
    ["img_suffix", "", str,],
    ["pignore", "", str,],
    ["event_file", "", str,],
    ["event_string", "", str,],
    ["source_folder", "True", torf,],
    ["wbmask", "", str,],
    ["sessionroi", "", str,],
    ["nroi", "", str,],
    ["shrinknsroi", "true", str,],
    ["path_bold", "bold[N]/*faln_dbnd_xr3d_atl.4dfp.img", str,],
    ["path_mov", "movement/*_b[N]_faln_dbnd_xr3d.dat", str,],
    ["path_t1", "atlas/*_mpr_n*_111_t88.4dfp.img", str,],
    ["image_source", "hcp", str,],
    ["image_target", "nifti", str,],
    ["image_atlas", "cifti", str,],
    ["use_sequence_info", "all", gc.pcslist,],
    ["conc_use", "relative", str,],
    ["# ---- GLM related options"],
    ["glm_matrix", "none", str,],
    ["glm_residuals", "save", str,],
    ["glm_results", "c,r", str,],
    ["glm_name", "", str,],
    ["# ---- Movement thresholding and report options"],
    ["mov_dvars", "3.0", float,],
    ["mov_dvarsme", "1.5", float,],
    ["mov_fd", "0.5", float,],
    ["mov_radius", "50.0", float,],
    ["mov_scrub", "yes", str,],
    ["mov_fidl", "udvarsme", str,],
    ["mov_plot", "mov_report", str,],
    ["mov_post", "udvarsme", str,],
    ["mov_before", "0", int,],
    ["mov_after", "0", int,],
    ["mov_bad", "udvarsme", str,],
    ["mov_mreport", "movement_report.txt", str,],
    ["mov_preport", "movement_report_post.txt", str,],
    ["mov_sreport", "movement_scrubbing_report.txt", str,],
    ["mov_pdf", "movement_plots", str,],
    ["mov_pref", "", str,],
    ["# ---- CIFTI related options"],
    ["surface_smooth", "2.0", float,],
    ["volume_smooth", "2.0", float,],
    ["voxel_smooth", "1", float,],
    ["smooth_mask", "false", str,],
    ["dilate_mask", "false", str,],
    ["hipass_filter", "0.008", float,],
    ["lopass_filter", "0.09", float,],
    ["hipass_do", "nuisance", str,],
    ["lopass_do", "nuisance,movement,events,task", str,],
    ["omp_threads", "", isNone,],
    ["framework_path", "", str,],
    ["wb_command_path", "", str,],
    ["print_command", "no", str,],
    ["# ---- scheduler options"],
    ["scheduler", "local", str,],
    ["scheduler_environment", "", isNone,],
    ["scheduler_workdir", "", isNone,],
    ["scheduler_sleep", "1", float,],
    ["# --- general HCP options"],
    ["hcp_processing_mode", "HCPStyleData", str,],
    ["hcp_folderstructure", "hcpls", str,],
    ["hcp_freesurfer_home", "", str,],
    ["hcp_freesurfer_module", "", str,],
    ["hcp_suffix", "", str,],
    ["hcp_t2", "t2", str,],
    ["hcp_printcom", "", str,],
    ["hcp_bold_prefix", "BOLD_", str,],
    ["hcp_filename", "automated", str,],
    ["hcp_lowresmesh", "32", str,],
    ["hcp_lowresmeshes", "32", str,],
    ["hcp_hiresmesh", "164", int,],
    ["hcp_bold_res", "2", str,],
    ["hcp_grayordinatesres", "2", int,],
    ["hcp_surfatlasdir", "", isNone,],
    ["hcp_grayordinatesdir", "", isNone,],
    ["hcp_subcortgraylabels", "", isNone,],
    ["hcp_refmyelinmaps", "", isNone,],
    ["hcp_regname", "MSMSulc", str,],
    ["hcp_cifti_tail", "_Atlas", str,],
    ["hcp_bold_variant", "", str,],
    ["additional_bolds", "", isNone,],
    ["hcp_nifti_tail", "", str,],
    ["hcp_config", "", isNone,],
    ["# --- hcp_pre_freesurfer options"],
    ["hcp_brainsize", "150", int],
    ["hcp_t1samplespacing", "NONE", str],
    ["hcp_t2samplespacing", "NONE", str],
    ["hcp_gdcoeffs", "", str],
    ["hcp_bfsigma", "", str],
    ["hcp_avgrdcmethod", "", isNone],
    ["hcp_unwarpdir", "z", str],
    ["hcp_echodiff", "", isNone],
    ["hcp_topupconfig", "NONE", str],
    ["hcp_prefs_custombrain", "", str],
    ["hcp_prefs_template_res", "", isNone],
    ["hcp_sephaseneg", "", isNone],
    ["hcp_sephasepos", "", isNone],
    ["hcp_seechospacing", "", isNone],
    ["hcp_seunwarpdir", "", isNone],
    ["hcp_bold_smoothFWHM", "2", int],
    ["hcp_prefs_t1template", "", isNone],
    ["hcp_prefs_t1templatebrain", "", isNone],
    ["hcp_prefs_t1template2mm", "", isNone],
    ["hcp_prefs_t2template", "", isNone],
    ["hcp_prefs_t2templatebrain", "", isNone],
    ["hcp_prefs_t2template2mm", "", isNone],
    ["hcp_prefs_templatemask", "", isNone],
    ["hcp_prefs_template2mmmask", "", isNone],
    ["hcp_prefs_fnirtconfig", "", isNone],
    ["# --- hcp_freesurfer options"],
    ["hcp_fs_seed", "", str],
    ["hcp_fs_existing_session", "FALSE", torf],
    ["hcp_fs_extra_reconall", "", str],
    ["hcp_expert_file", "", str],
    ["hcp_fs_flair", "FALSE", torf],
    ["hcp_fs_no_conf2hires", "FALSE", torf],
    ["# --- hcp_post_freesurfer options"],
    ["hcp_mcsigma", "", str],
    ["hcp_inflatescale", "1", str],
    ["hcp_fs_ind_mean", "YES", str],
    ["# --- hcp_fmri_volume options"],
    ["hcp_bold_biascorrection", "NONE", str],
    ["hcp_bold_usejacobian", "", str],
    ["hcp_bold_echospacing", "", isNone],
    ["hcp_bold_sbref", "NONE", str],
    ["hcp_bold_dcmethod", "", isNone],
    ["hcp_bold_echodiff", "", isNone],
    ["hcp_bold_unwarpdir", "y", str],
    ["hcp_bold_gdcoeffs", "NONE", str],
    ["hcp_bold_doslicetime", "", torf],
    ["hcp_bold_slicetimingfile", "FALSE", torf],
    ["hcp_bold_slicetimerparams", "", str],
    ["hcp_bold_movreg", "MCFLIRT", str],
    ["hcp_bold_movref", "independent", str],
    ["hcp_bold_seimg", "independent", str],
    ["hcp_bold_refreg", "", str],
    ["hcp_bold_mask", "", str],
    ["hcp_bold_sephaseneg", "", isNone],
    ["hcp_bold_sephasepos", "", isNone],
    ["hcp_bold_seechospacing", "", isNone],
    ["hcp_bold_seunwarpdir", "", isNone],
    ["hcp_bold_topupconfig", "", isNone],
    ["hcp_bold_preregistertool", "", str],
    ["hcp_bold_dof", "", str],
    ["hcp_bold_stcorrdir", "", str],
    ["hcp_bold_stcorrint", "", str],
    ["hcp_wb_resample", "", flag],
    ["hcp_echo_te", "", isNone],
    ["longitudinal", None, flag],
    ["# --- hcp_diffusion options"],
    ["hcp_dwi_echospacing", "", str],
    ["hcp_dwi_phasepos", "PA", str],
    ["hcp_dwi_gdcoeffs", "NONE", str],
    ["hcp_dwi_dof", "", isNone],
    ["hcp_dwi_b0maxbval", "", isNone],
    ["hcp_dwi_combinedata", "1", str],
    ["hcp_dwi_extraeddyarg", "", isNone],
    ["hcp_dwi_name", "", isNone],
    ["hcp_nogpu", None, flag],
    ["hcp_high_myelin", "", isNone],
    ["hcp_dwi_selectbestb0", None, flag],
    ["hcp_dwi_even_slices", None, flag],
    ["hcp_dwi_topupconfig", "", isNone],
    ["hcp_dwi_posdata", "", isNone],
    ["hcp_dwi_negdata", "", isNone],
    ["hcp_dwi_dummy_bval_bvec", None, flag],
    ["# --- general hcp_icafix, hcp_post_fix, hcp_reapply_fix, hcp_msmall, hcp_dedrift_and_resample options"],
    ["hcp_icafix_bolds", "", isNone],
    ["hcp_icafix_highpass", "", isNone],
    ["hcp_matlab_mode", "", isNone],
    ["hcp_icafix_domotionreg", "", isNone],
    ["hcp_icafix_deleteintermediates", "", isNone],
    ["hcp_icafix_fallbackthreshold", "", isNone],
    ["hcp_icafix_parallel_limit", "", isNone],
    ["hcp_clean_substring", "", isNone],
    ["# --- hcp_icafix options"],
    ["hcp_icafix_model", "", isNone],
    ["hcp_icafix_threshold", "", isNone],
    ["hcp_icafix_postfix", "TRUE", torf],
    ["hcp_icafix_processingmode", "", isNone],
    ["hcp_icafix_icadim_mode", "", isNone],
    ["hcp_reuse_existing_ica", "", isNone],
    ["hcp_fix_backup", "", isNone],
    ["hcp_t1wtemplatebrain", "", isNone],
    ["hcp_ica_method", "", isNone],
    ["hcp_vol_wisharts", "", isNone],
    ["hcp_cifti_wisharts", "", isNone],
    ["hcp_icadim_mode", "", isNone],
    ["hcp_legacy_fix", "", flag],
    ["hcp_icafix_concatenate_only", "", flag],
    ["# --- hcp_post_fix options"],
    ["hcp_postfix_dualscene", "", isNone],
    ["hcp_postfix_singlescene", "", isNone],
    ["hcp_postfix_reusehighpass", "TRUE", torf],
    ["# --- hcp_reapply_fix options"],
    ["hcp_icafix_regname", "NONE", str],
    ["# --- hcp_msmall options options"],
    ["hcp_msmall_bolds", "", isNone],
    ["hcp_msmall_outfmriname", "rfMRI_REST", str],
    ["hcp_msmall_templates", "", isNone],
    ["hcp_msmall_outregname", "MSMAll_InitialReg", str],
    ["hcp_msmall_procstring", "", isNone],
    ["hcp_msmall_resample", "TRUE", torf],
    ["hcp_msmall_myelin_target", "", isNone],
    ["# --- hcp_dedrift_and_resample options"],
    ["hcp_resample_concatregname", "MSMAll", str],
    ["hcp_resample_regname", "", isNone],
    ["hcp_resample_reg_files", "", isNone],
    ["hcp_resample_maps", "sulc,curvature,corrThickness,thickness", str],
    ["hcp_resample_myelinmaps", "MyelinMap,SmoothedMyelinMap", str],
    ["hcp_resample_dontfixnames", "", isNone],
    ["hcp_resample_inregname", "", isNone],
    ["hcp_resample_use_ind_mean", "", isNone],
    ["hcp_resample_extractnames", "", isNone],
    ["hcp_resample_extractextraregnames", "", isNone],
    ["hcp_resample_extractvolume", "", isNone],
    ["# --- hcp_task_fmri_analysis options"],
    ["hcp_task_lvl1tasks", "", isNone],
    ["hcp_task_lvl1fsfs", "", isNone],
    ["hcp_task_lvl2task", "", isNone],
    ["hcp_task_lvl2fsf", "", isNone],
    ["hcp_task_summaryname", "", isNone],
    ["hcp_task_confound", "", isNone],
    ["hcp_bold_final_smoothFWHM", "", isNone],
    ["hcp_task_highpass", "", isNone],
    ["hcp_task_lowpass", "", isNone],
    ["hcp_task_procstring", "", isNone],
    ["hcp_task_parcellation", "", isNone],
    ["hcp_task_parcellation_file", "", isNone],
    ["hcp_task_vba", None, flag],
    ["# --- hcp_asl options"],
    ["hcp_asl_mtname", "", isNone],
    ["hcp_asl_territories_atlas", "", isNone],
    ["hcp_asl_territories_labels", "", isNone],
    ["hcp_asl_cores", "", isNone],
    ["hcp_asl_interpolation", "", isNone],
    ["hcp_asl_use_t1", None, flag],
    ["hcp_asl_nobandingcorr", None, flag],
    ["hcp_asl_stages", None, isNone],
    ["# --- hcp_temporal_ica options"],
    ["hcp_tica_studyfolder", "", isNone],
    ["hcp_tica_bolds", "", isNone],
    ["hcp_tica_outfmriname", "rfMRI_REST", str],
    ["hcp_tica_surfregname", "", isNone],
    ["hcp_tica_procstring", "", isNone],
    ["hcp_outgroupname", "", isNone],
    ["hcp_tica_timepoints", "", isNone],
    ["hcp_tica_num_wishart", "", isNone],
    ["hcp_tica_mrfix_concat_name", "", isNone],
    ["hcp_tica_icamode", "", isNone],
    ["hcp_tica_precomputed_clean_folder", "", isNone],
    ["hcp_tica_precomputed_fmri_name", "", isNone],
    ["hcp_tica_precomputed_group_name", "", isNone],
    ["hcp_tica_extra_output_suffix", "", isNone],
    ["hcp_tica_pca_out_dim", "", isNone],
    ["hcp_tica_pca_internal_dim", "", isNone],
    ["hcp_tica_migp_resume", "", isNone],
    ["hcp_tica_sicadim_iters", "", isNone],
    ["hcp_tica_sicadim_override", "", isNone],
    ["hcp_low_sica_dims", "", isNone],
    ["hcp_tica_reclean_mode", "", isNone],
    ["hcp_tica_starting_step", "", isNone],
    ["hcp_tica_stop_after_step", "ComputeTICAFeatures", str],
    ["hcp_tica_remove_manual_components", "", isNone],
    ["hcp_tica_fix_legacy_bias", "", isNone],
    ["hcp_parallel_limit", "", isNone],
    ["hcp_tica_average_dataset", "", isNone],
    ["hcp_tica_extract_fmri_name_list", "", isNone],
    ["hcp_tica_extract_fmri_out", "", isNone],
    ["hcp_tica_config_out", None, flag],
    ["hcp_tica_longitudinal_extract_all", None, flag],
    ["hcp_longitudinal_subject", None, isNone],
    ["hcp_longitudinal_sessions", None, isNone],
    ["# --- hcp_apply_auto_reclean options"],
    ["hcp_autoreclean_model_folder", "", isNone],
    ["hcp_autoreclean_model_to_use", "", isNone],
    ["hcp_autoreclean_vote_threshold", "", isNone],
    ["# --- hcp_make_average_dataset options"],
    ["hcp_surface_atlas_dir", "", isNone],
    ["hcp_grayordinates_dir", "", isNone],
    ["hcp_freesurfer_labels", "", isNone],
    ["hcp_pregradient_smoothing", "1", int],
    ["hcp_mad_regname", "MSMAll", str],
    ["hcp_mad_videen_maps", "corrThickness,thickness,MyelinMap_BC,SmoothedMyelinMap_BC", str],
    ["hcp_mad_greyscale_maps", "sulc,curvature", str],
    ["hcp_mad_distortion_maps", "SphericalDistortion,ArealDistortion,EdgeDistortion", str],
    ["hcp_mad_gradient_maps", "MyelinMap_BC,SmoothedMyelinMap_BC,corrThickness", str],
    ["hcp_mad_std_maps", "sulc@curvature,corrThickness,thickness,MyelinMap_BC", str],
    ["hcp_mad_multi_maps", "NONE", str],
    ["# --- HCP file checking"],
    ["hcp_prefs_check", "last", str],
    ["hcp_fs_check", "last", str],
    ["hcp_fslong_check", "last", str],
    ["hcp_postfs_check", "last", str],
    ["hcp_bold_vol_check", "last", str],
    ["hcp_bold_surf_check", "last", str],
    ["hcp_dwi_check", "last", str],
    ["# --- Processing options"],
    ["run", "run", str],
    ["log", "keep", str],
    ["# --- mice pipelines"],
    ["voxel_increase", "", isNone],
    ["orientation", "x -y z", str],
    ["no_despike", "", flag],
    ["bias_field_correction", "yes", str],
    ["melodic_anatfile", "", isNone],
    ["fix_rdata", "", isNone],
    ["fix_threshold", "20", int],
    ["fix_no_motion_cleanup", "", flag],
    ["fix_aggressive_cleanup", "", flag],
    ["mice_highpass", "0.01", str],
    ["mice_lowpass", "0.25", str],
    ["mice_volumes", "900", int],
    ["flirt_ref", "", isNone],
    ["# --- hcp_long_freesurfer options"],
    ["hcp_longitudinal_template", "base", str],
    ["hcp_no_t2w", "", flag],
    ["hcp_seed", "", isNone],
    ["hcp_parallel_mode", "BUILTIN", str],
    ["hcp_fslsub_queue", "", isNone],
    ["hcp_max_jobs", "", isNone],
    ["hcp_start_stage", "", isNone],
    ["hcp_end_stage", "", isNone],
    ["# --- hcp_transmit_bias_individual options"],
    ["hcp_transmit_mode", "", isNone],
    ["hcp_gmwm_template", "", isNone],
    ["hcp_group_corrected_myelin", "", isNone],
    ["hcp_afi_image", "", isNone],
    ["hcp_afi_tr_one", "", isNone],
    ["hcp_afi_tr_two", "", isNone],
    ["hcp_afi_angle", "", isNone],
    ["hcp_b1tx_magnitude", "", isNone],
    ["hcp_b1tx_phase", "", isNone],
    ["hcp_b1tx_phase_divisor", "", isNone],
    ["hcp_pt_fmri_names", "", isNone],
    ["hcp_pt_bbr_threshold", "", isNone],
    ["hcp_myelin_template", "", isNone],
    ["hcp_group_uncorrected_myelin", "", isNone],
    ["hcp_pt_reference_value_file", "", isNone],
    ["hcp_unproc_t1w_list", "", isNone],
    ["hcp_unproc_t2w_list", "", isNone],
    ["hcp_receive_bias_body_coil", "", isNone],
    ["hcp_receive_bias_head_coil", "", isNone],
    ["hcp_raw_psn_t1w", "", isNone],
    ["hcp_raw_nopsn_t1w", "", isNone],
    ["hcp_transmit_res", "", isNone],
    ["hcp_myelin_mapping_fwhm", "", isNone],
    ["hcp_old_myelin_mapping", "", flag],
    ["# --- fsl_feat options"],
    ["feat_file", "", isNone],
    ["# --- fsl_melodic options"],
    ["input_files", "", isNone],
    ["melodic_extra_args", "", isNone],
    ["# --- rapidtide options"],
    ["despecklepasses", "", isNone,],
    ["filterband", "", isNone,],
    ["searchrange", "", isNone,],
    ["nprocs", "", isNone,],
    ["nofitfilt", "", flag,],
    ["similaritymetric", "", isNone,],
    ["ampthresh", "", isNone,],
    ["numnull", "", isNone,],
    ["outputlevel", "", isNone,],
    ["spatialfilt", "", isNone,],
    ["simcalcrange", "", isNone,],
    ["brainmask", "", isNone,],
    ["graymattermask", "", isNone,],
    ["whitemattermask", "", isNone,],
    ["refineexclude", "", isNone,],
    ["nodenoise", "", flag,],
    ["rapidtide_extra_args", "", isNone],
]

# Add arguments used in extensions
arglist += extensions.compile_list("arglist")
arglist += extensions.arglist

#   ---------------------------------------------------------- FLAG DESCRIPTION
#   A list of flags, arguments that do not require additional values. They are
#   listed as a list of flags, each flag is specified with the following
#   elements:
#
#   1/ the name of the element
#   2/ what value does it set to the parameter it maps to
#   3/ optional: what parameter does it map to
flaglist = [
    ["test", "test", "run",],
    ["overwrite", True,],
    ["hcp_nogpu", True,],
    ["hcp_dwi_selectbestb0", True,],
    ["hcp_asl_use_t1", True,],
    ["hcp_asl_nobandingcorr", True,],
    ["hcp_task_vba", True,],
    ["hcp_tica_config_out", False,],
    ["no_despike", True,],
    ["fix_no_motion_cleanup", True,],
    ["fix_aggressive_cleanup", False,],
    ["longitudinal", True,],
    ["hcp_tica_longitudinal_extract_all", True,],
    ["hcp_icafix_concatenate_only", True,],
    ["hcp_old_myelin_mapping", True,],
    ["nofitfilt", True,],
    ["nodenoise", True,],
]

# Add flags used in extensions
flaglist += extensions.compile_list("flaglist")

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
#   1/ command long name
#   2/ the actual function ran for the command
#
#   Empty lists denote there should be a blank line when printing out a command
#   list.
# processing commands
calist = [
    ["map_hcp_data", process_hcp.map_hcp_data],
    [],
    ["get_bold_data", workflow.get_bold_data],
    ["create_bold_brain_masks", workflow.create_bold_brain_masks],
    [],
    ["run_basic_segmentation", fs.runBasicStructuralSegmentation],
    ["get_fs_data", fs.checkForFreeSurferData],
    ["run_subcortical_fs", fs.runFreeSurferSubcorticalSegmentation],
    ["run_full_fs", fs.runFreeSurferFullSegmentation],
    [],
    ["compute_bold_stats", workflow.compute_bold_stats],
    ["create_stats_report", workflow.create_stats_report],
    ["extract_nuisance_signal", workflow.extract_nuisance_signal],
    [],
    ["preprocess_bold", workflow.preprocess_bold],
    ["preprocess_conc", workflow.preprocess_conc],
    [],
    ["hcp_pre_freesurfer", process_hcp.hcp_pre_freesurfer],
    ["hcp_freesurfer", process_hcp.hcp_freesurfer],
    ["hcp_post_freesurfer", process_hcp.hcp_post_freesurfer],
    ["hcp_fmri_volume", process_hcp.hcp_fmri_volume],
    ["hcp_fmri_surface", process_hcp.hcp_fmri_surface],
    ["hcp_icafix", process_hcp.hcp_icafix],
    ["hcp_post_fix", process_hcp.hcp_post_fix],
    ["hcp_reapply_fix", process_hcp.hcp_reapply_fix],
    ["hcp_msmall", process_hcp.hcp_msmall],
    ["hcp_dedrift_and_resample", process_hcp.hcp_dedrift_and_resample],
    ["hcp_task_fmri_analysis", process_hcp.hcp_task_fmri_analysis],
    [],
    ["hcp_diffusion", process_hcp.hcp_diffusion],
    ["hcp_apply_auto_reclean", process_hcp.hcp_apply_auto_reclean],
    ["hcp_asl", process_hcp.hcp_asl],
    ["hcp_transmit_bias_individual", process_hcp.hcp_transmit_bias_individual],
    [],
    ["run_shell_script", simple.run_shell_script],
    [],
    ["dwi_f99", dwi.dwi_f99],
    ["dwi_xtract", dwi.dwi_xtract],
    ["dwi_noddi_gpu", dwi.dwi_noddi_gpu],
    [],
    ["setup_mice", qx_mice.setup_mice.setup_mice],
    ["preprocess_mice", qx_mice.process_mice.preprocess_mice],
    ["map_mice_data", qx_mice.process_mice.map_mice_data],
    [],
    ["fsl_feat", fsl.fsl_feat],
    ["rapidtide", rapidtide.rapidtide],
]

# longitudinal commands
lalist = [
    ["hcp_long_freesurfer", process_hcp.hcp_long_freesurfer],
    ["hcp_long_post_freesurfer", process_hcp.hcp_long_post_freesurfer],
    ["hcp_long_msmall", process_hcp.hcp_long_msmall],
    ["fsl_melodic", fsl.fsl_melodic],
]

# multi-session commands
malist = [
    ["hcp_temporal_ica", process_hcp.hcp_temporal_ica],
    ["hcp_make_average_dataset", process_hcp.hcp_make_average_dataset],
]

salist = [
    ["create_bold_list", simple.create_bold_list],
    ["create_conc_list", simple.create_conc_list],
    ["list_session_info", simple.list_session_info],
    ["map_nii2bids", map_nii2bids],
]

# Add command lists used in extensions
calist += extensions.compile_list("calist")
lalist += extensions.compile_list("lalist")
malist += extensions.compile_list("malist")
salist += extensions.compile_list("salist")

calist += extensions.calist
lalist += extensions.lalist
malist += extensions.malist
salist += extensions.salist

#   -------------------------------------------------------- COMMAND DICTIONARY
#   Code that transcribes the comand specifications into a dictionary for
#   calling the relevant command when specified.

pactions = {}
for line in calist:
    if len(line) == 2:
        pactions[line[0]] = line[1]

lactions = {}
for line in lalist:
    if len(line) == 2:
        lactions[line[0]] = line[1]

mactions = {}
for line in malist:
    if len(line) == 2:
        mactions[line[0]] = line[1]

sactions = {}
for line in salist:
    if len(line) == 2:
        sactions[line[0]] = line[1]

# all actions
allactions = {}
allactions.update(pactions.copy())
allactions.update(lactions.copy())
allactions.update(mactions.copy())
allactions.update(sactions.copy())

flist = {}
for line in flaglist:
    if len(line) == 2:
        flist[line[0]] = [line[0], line[1]]
    else:
        flist[line[0]] = [line[2], line[1]]


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
    options = {"command_ran": command}

    # setup default options
    for line in arglist:
        if len(line) == 3:
            options[line[0]] = line[1]

    # read options from batch.txt
    if "sessions" in args:
        options["sessions"] = args["sessions"]
    if "sessionids" in args:
        options["sessionids"] = args["sessionids"]
    if "filter" in args:
        options["filter"] = args["filter"]

    sessions, gpref = gc.get_sessions_list(
        options["sessions"],
        filter=options["filter"],
        sessionids=options["sessionids"],
        verbose=False,
    )

    # check if all sessions have subjects for longitudinal
    if command in lactions:
        subject_list = []
        if sessions is not None:
            for session in sessions:
                if "subject" not in session:
                    raise ge.CommandFailed(
                        command,
                        "Missing subject information",
                        f"No subject information provided for session id: {session['id']}.",
                        "Please check the batch file!",
                        "Aborting processing!",
                    )
                if session["subject"] not in subject_list:
                    subject_list.append(session["subject"])

    # take parameters from batch file
    batch_args = gcs.check_deprecated_parameters(gpref, command)

    for k, v in batch_args.items():
        options[k] = v

    # parse command line options
    for k, v in args.items():
        if k in flist:
            if v != True:
                options[flist[k][0]] = v
            else:
                options[flist[k][0]] = flist[k][1]
        else:
            options[k] = v

    # take care of variable expansion
    for key in options:
        if type(options[key]) is str:
            options[key] = os.path.expandvars(options[key])

    # recode as last step before options are used
    for line in arglist:
        if len(line) == 3:
            try:
                options[line[0]] = line[2](options[line[0]])
            except:
                raise ge.CommandError(
                    command,
                    "Invalid parameter value!",
                    "Parameter `%s` is specified but is set to an invalid value:"
                    % (line[0]),
                    "---> %s=%s" % (line[0], str(options[line[0]])),
                    "Please check acceptable inputs for %s!" % (line[0]),
                )

    # impute unspecified parameters
    options = gcs.impute_parameters(options, command)

    # set key parameters
    overwrite = options["overwrite"]
    parsessions = options["parsessions"]
    nprocess = options["nprocess"]
    printinfo = options["datainfo"]
    printoptions = options["printoptions"]

    studyfolders = gc.deduceFolders(options)
    logfolder = studyfolders["logfolder"]
    runlogfolder = os.path.join(logfolder, "runlogs")
    comlogfolder = os.path.join(logfolder, "comlogs")
    specfolder = os.path.join(studyfolders["sessionsfolder"], "specs")

    options["runlogs"] = runlogfolder
    options["comlogs"] = comlogfolder
    options["logfolder"] = logfolder
    options["specfolder"] = specfolder

    # --------------------------------------------------------------------------
    #                                                       start writing runlog
    for cfolder in [runlogfolder, comlogfolder]:
        if not os.path.exists(cfolder):
            os.makedirs(cfolder)
    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")

    if not options["longitudinal"]:
        logname = os.path.join(runlogfolder, "Log-%s-%s.log") % (command, logstamp)
    else:
        logname = os.path.join(runlogfolder, "Log-%s-long-%s.log") % (command, logstamp)

    log = []
    stati = []
    sout = gc.print_qunex_header()
    sout += "#\n"
    sout += "=================================================================\n"
    sout += "qunex " + command + " \\"

    arg_items = list(args.items())
    for i, (k, v) in enumerate(arg_items):
        if i < len(arg_items) - 1:
            sout += '\n  --%s="%s" \\' % (k, v)
        else:
            sout += '\n  --%s="%s"' % (k, v)

    sout += "\n=================================================================\n"

    # no parsessions for longitudinal and multi-session commands
    if (command in lactions) or (command in mactions):
        if parsessions > 1:
            sout += f"\nWARNING: parsessions [{parsessions}] will be set to 1 because you are running a longitudinal or a multi-session command!\n"
            parsessions = 1

    # check if there are no sessions
    if not sessions:
        sout += "\nERROR: No sessions specified to process. Please check your batch file, filtering options or sessionids parameter!\n"
        print(sout)
        writelog(sout)
        exit()

    elif options["run"] == "run":
        sout += (
            f"\nStarting multiprocessing sessions in %s with a pool of %d concurrent processes\n"
            % (options["sessions"], parsessions)
        )

    else:
        sout += "\nRunning test on %s ...\n" % (options["sessions"])

    print(sout)
    writelog(sout)

    # -----------------------------------------------------------------------
    #                                                           print options
    if printoptions:
        print("\nFull list of options:")
        writelog("\nFull list of options:\n")
        for line in arglist:
            if len(line) == 3:
                print("%-25s :" % (line[0]), options[line[0]])
                writelog("  %-25s : %s" % (line[0], str(options[line[0]])))

    # -----------------------------------------------------------------------
    #                                                              print info
    if printinfo:
        print(sessions)

    # =======================================================================
    #                                               RUN BY SESSION PROCESSING
    if not os.path.exists(options["sessionsfolder"]):
        os.mkdir(options["sessionsfolder"])

    if nprocess > 0:
        nsessions = [sessions.pop(0) for e in range(nprocess) if sessions]
        sessions = nsessions

    # -----------------------------------------------------------------------
    #                                                             local queue
    if options["scheduler"] == "local":
        consoleLog = ""

        c = 0
        if parsessions == 1 or options["run"] == "test":
            # processing commands
            if command in pactions:
                pending_actions = pactions[command]
                for session in sessions:
                    if len(session["id"]) > 1:
                        if options["run"] == "test":
                            action = "testing"
                        else:
                            action = "processing"
                        soptions = update_options(session, options)
                        consoleLog += "\nStarting %s of sessions %s at %s" % (
                            action,
                            session["id"],
                            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
                        )
                        print(
                            "\nStarting %s of sessions %s at %s"
                            % (
                                action,
                                session["id"],
                                datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
                            )
                        )
                        r, status = procResponse(
                            pending_actions(session, soptions, overwrite, c + 1)
                        )
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
                if options["run"] == "test":
                    action = "testing"
                else:
                    action = "processing"

                # update options and prepare the all sessions string for labeling
                sessionids = ""
                for session in sessions:
                    soptions = update_options(session, options)

                    if sessionids == "":
                        sessionids = session["id"]
                    else:
                        sessionids = sessionids + "," + session["id"]

                # log
                consoleLog += "\nStarting %s of sessions %s at %s" % (
                    action,
                    sessionids,
                    datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
                )
                print(
                    "\nStarting %s of sessions %s at %s"
                    % (
                        action,
                        sessionids,
                        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
                    )
                )

                # process
                r, status = procResponse(
                    pending_actions(sessions, sessionids, soptions, overwrite, c + 1)
                )

                # write log
                writelog(r)
                consoleLog += r
                print(r)
                stati.append(status)

            # longitudinal commands
            elif command in lactions:
                pending_actions = lactions[command]

                # test or processing
                if options["run"] == "test":
                    action = "testing"
                else:
                    action = "processing"

                # update options and prepare the all subjects string for labeling
                for session in sessions:
                    soptions = update_options(session, options)

                subjectids = ",".join(subject_list)

                # log
                consoleLog += "\nStarting %s of subjects %s at %s" % (
                    action,
                    subjectids,
                    datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
                )
                print(
                    "\nStarting %s of subjects %s at %s"
                    % (
                        action,
                        subjectids,
                        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
                    )
                )

                # process
                r, status = procResponse(
                    pending_actions(sessions, subjectids, soptions, overwrite, c + 1)
                )

                # write log
                writelog(r)
                consoleLog += r
                print(r)
                stati.append(status)

            # simple processing commands
            elif command in sactions:
                pending_actions = sactions[command]
                for session in sessions:
                    soptions = update_options(session, options)
                r, status = procResponse(pending_actions(sessions, soptions, overwrite))
                writelog(r)

        else:
            c = 0
            processPoolExecutor = ProcessPoolExecutor(parsessions)
            futures = []
            if command in pactions:
                pending_actions = pactions[command]
                for session in sessions:
                    if len(session["id"]) > 1:
                        soptions = update_options(session, options)
                        consoleLog += (
                            "\nAdding processing of session %s to the pool at %s"
                            % (
                                session["id"],
                                datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
                            )
                        )
                        print(
                            "\nAdding processing of session %s to the pool at %s"
                            % (
                                session["id"],
                                datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
                            )
                        )
                        future = processPoolExecutor.submit(
                            pending_actions, session, soptions, overwrite, c + 1
                        )
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
                soptions = update_options(session, options)
                r, status = procResponse(pending_actions(sessions, soptions, overwrite))
                writelog(r)

        # print(console log)
        # print(consoleLog)

        # create log
        f = open(logname, "w")
        # header
        gc.print_qunex_header(file=f)
        # print("# Generated by QuNex %s on %s" % (gc.get_qunex_version(), datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")), file=f)
        print("#", file=f)
        print(
            "\n\n============================= LOG ================================\n",
            file=f,
        )
        for e in log:
            print(e, file=f)

        print("\n\n---> Final report for command", options["command_ran"])
        print("\n\n---> Final report for command", options["command_ran"], file=f)
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
            print("---> Success status not reported for some or all tasks")
            print("---> Success status not reported for some or all tasks", file=f)
        elif failedTotal > 0:
            print("---> Not all tasks completed fully!")
            print("---> Not all tasks completed fully!", file=f)
        else:
            print("---> Successful completion of all tasks")
            print("---> Successful completion of all tasks", file=f)

        f.close()

    # -----------------------------------------------------------------------
    #                                                  general scheduler code
    else:
        # schedule
        gs.runThroughScheduler(
            command,
            sessions=sessions,
            args=args,
            parsessions=parsessions,
            logfolder=os.path.join(logfolder, "batchlogs"),
            logname=logname,
        )
