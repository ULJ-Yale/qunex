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
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

import qx_utilities.general.commands_support as gcs
import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.scheduler as gs
from qx_utilities.general import extensions

# pipelines imports
# qx_mice
from qx_utilities.general.parsing import flag, is_none
from qx_utilities.general.parsing import true_or_false as torf


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
    ["logfolder", "", is_none],
    [
        "logtag",
        "",
        str,
    ],
    [
        "overwrite",
        "no",
        torf,
    ],
    [
        "parsubjects",
        "1",
        int,
    ],
    [
        "parsessions",
        "1",
        int,
    ],
    [
        "parelements",
        "1",
        int,
    ],
    [
        "nprocess",
        "0",
        int,
    ],
    [
        "datainfo",
        "False",
        torf,
    ],
    [
        "filter",
        "",
        str,
    ],
    [
        "script",
        "",
        is_none,
    ],
    [
        "sessionid",
        "",
        str,
    ],
    [
        "sessionids",
        "",
        str,
    ],
    ["# ---- Preprocessing options"],
    [
        "bet",
        "-f 0.5",
        str,
    ],
    [
        "fast",
        "-t 1 -n 3 --nopve",
        str,
    ],
    [
        "betboldmask",
        "-R -m",
        str,
    ],
    [
        "tr",
        "2.5",
        float,
    ],
    [
        "omit",
        "5",
        int,
    ],
    [
        "bold_actions",
        "shrcl",
        str,
    ],
    [
        "bold_nuisance",
        "m,V,WM,WB,1d",
        str,
    ],
    [
        "bolds",
        "all",
        str,
    ],
    [
        "boldname",
        "bold",
        str,
    ],
    [
        "qx_nifti_tail",
        "",
        is_none,
    ],
    [
        "qx_cifti_tail",
        "",
        is_none,
    ],
    [
        "nifti_tail",
        "",
        is_none,
    ],
    [
        "cifti_tail",
        "",
        is_none,
    ],
    [
        "bold_prefix",
        "",
        str,
    ],
    [
        "bold_variant",
        "",
        str,
    ],
    [
        "img_suffix",
        "",
        str,
    ],
    [
        "pignore",
        "",
        str,
    ],
    [
        "event_file",
        "",
        str,
    ],
    [
        "event_string",
        "",
        str,
    ],
    [
        "source_folder",
        "True",
        torf,
    ],
    [
        "wbmask",
        "",
        str,
    ],
    [
        "sessionroi",
        "",
        str,
    ],
    [
        "nroi",
        "",
        str,
    ],
    [
        "shrinknsroi",
        "true",
        str,
    ],
    [
        "path_bold",
        "bold[N]/*faln_dbnd_xr3d_atl.4dfp.img",
        str,
    ],
    [
        "path_mov",
        "movement/*_b[N]_faln_dbnd_xr3d.dat",
        str,
    ],
    [
        "path_t1",
        "atlas/*_mpr_n*_111_t88.4dfp.img",
        str,
    ],
    [
        "image_source",
        "hcp",
        str,
    ],
    [
        "image_target",
        "nifti",
        str,
    ],
    [
        "image_atlas",
        "cifti",
        str,
    ],
    [
        "use_sequence_info",
        "all",
        gc.pcslist,
    ],
    [
        "conc_use",
        "relative",
        str,
    ],
    ["# ---- GLM related options"],
    [
        "glm_matrix",
        "none",
        str,
    ],
    [
        "glm_residuals",
        "save",
        str,
    ],
    [
        "glm_results",
        "c,r",
        str,
    ],
    [
        "glm_name",
        "",
        str,
    ],
    ["# ---- Movement thresholding and report options"],
    [
        "mov_dvars",
        "3.0",
        float,
    ],
    [
        "mov_dvarsme",
        "1.5",
        float,
    ],
    [
        "mov_fd",
        "0.5",
        float,
    ],
    [
        "mov_radius",
        "50.0",
        float,
    ],
    [
        "mov_scrub",
        "yes",
        str,
    ],
    [
        "mov_fidl",
        "udvarsme",
        str,
    ],
    [
        "mov_plot",
        "mov_report",
        str,
    ],
    [
        "mov_post",
        "udvarsme",
        str,
    ],
    [
        "mov_before",
        "0",
        int,
    ],
    [
        "mov_after",
        "0",
        int,
    ],
    [
        "mov_bad",
        "udvarsme",
        str,
    ],
    [
        "mov_mreport",
        "movement_report.txt",
        str,
    ],
    [
        "mov_preport",
        "movement_report_post.txt",
        str,
    ],
    [
        "mov_sreport",
        "movement_scrubbing_report.txt",
        str,
    ],
    [
        "mov_pdf",
        "movement_plots",
        str,
    ],
    [
        "mov_pref",
        "",
        str,
    ],
    ["# ---- CIFTI related options"],
    [
        "surface_smooth",
        "2.0",
        float,
    ],
    [
        "volume_smooth",
        "2.0",
        float,
    ],
    [
        "voxel_smooth",
        "1",
        float,
    ],
    [
        "smooth_mask",
        "false",
        str,
    ],
    [
        "dilate_mask",
        "false",
        str,
    ],
    [
        "hipass_filter",
        "0.008",
        float,
    ],
    [
        "lopass_filter",
        "0.09",
        float,
    ],
    [
        "hipass_do",
        "nuisance",
        str,
    ],
    [
        "lopass_do",
        "nuisance,movement,events,task",
        str,
    ],
    [
        "framework_path",
        "",
        str,
    ],
    [
        "wb_command_path",
        "",
        str,
    ],
    [
        "print_command",
        "no",
        str,
    ],
    ["# ---- scheduler options"],
    [
        "scheduler",
        "local",
        str,
    ],
    [
        "scheduler_environment",
        "",
        is_none,
    ],
    [
        "scheduler_workdir",
        "",
        is_none,
    ],
    [
        "scheduler_sleep",
        "1",
        float,
    ],
    ["# --- general HCP options"],
    [
        "hcp_processing_mode",
        "HCPStyleData",
        str,
    ],
    [
        "hcp_folderstructure",
        "hcpls",
        str,
    ],
    [
        "hcp_freesurfer_home",
        "",
        str,
    ],
    [
        "hcp_freesurfer_module",
        "",
        str,
    ],
    [
        "hcp_suffix",
        "",
        str,
    ],
    [
        "hcp_t2",
        "t2",
        str,
    ],
    [
        "hcp_printcom",
        "",
        str,
    ],
    [
        "hcp_bold_prefix",
        "BOLD_",
        str,
    ],
    [
        "hcp_filename",
        "automated",
        str,
    ],
    [
        "hcp_lowresmesh",
        "32",
        str,
    ],
    [
        "hcp_lowresmeshes",
        "32",
        str,
    ],
    [
        "hcp_hiresmesh",
        "164",
        int,
    ],
    [
        "hcp_bold_res",
        "2",
        str,
    ],
    [
        "hcp_grayordinatesres",
        "2",
        str,
    ],
    [
        "hcp_surfatlasdir",
        "",
        is_none,
    ],
    [
        "hcp_grayordinatesdir",
        "",
        is_none,
    ],
    [
        "hcp_subcortgraylabels",
        "",
        is_none,
    ],
    [
        "hcp_refmyelinmaps",
        "",
        is_none,
    ],
    [
        "hcp_regname",
        "MSMSulc",
        str,
    ],
    [
        "hcp_cifti_tail",
        "_Atlas",
        str,
    ],
    [
        "hcp_bold_variant",
        "",
        str,
    ],
    [
        "additional_bolds",
        "",
        is_none,
    ],
    [
        "hcp_nifti_tail",
        "",
        str,
    ],
    [
        "hcp_config",
        "",
        is_none,
    ],
    ["# --- hcp_pre_freesurfer options"],
    ["hcp_brainsize", "150", int],
    ["hcp_t1samplespacing", "NONE", str],
    ["hcp_t2samplespacing", "NONE", str],
    ["hcp_gdcoeffs", "", str],
    ["hcp_bfsigma", "", str],
    ["hcp_avgrdcmethod", "", is_none],
    ["hcp_unwarpdir", "", is_none],
    ["hcp_echodiff", "", is_none],
    ["hcp_topupconfig", "NONE", str],
    ["hcp_prefs_custombrain", "", str],
    ["hcp_prefs_template_res", "", is_none],
    ["hcp_sephaseneg", "", is_none],
    ["hcp_sephasepos", "", is_none],
    ["hcp_senum", "", is_none],
    ["hcp_sephaseneg2", "", is_none],
    ["hcp_sephasepos2", "", is_none],
    ["hcp_senum2", "", is_none],
    ["hcp_seechospacing", "", is_none],
    ["hcp_seunwarpdir", "", is_none],
    ["hcp_bold_smoothFWHM", "2", str],
    ["hcp_prefs_t1template", "", is_none],
    ["hcp_prefs_t1templatebrain", "", is_none],
    ["hcp_prefs_t1template2mm", "", is_none],
    ["hcp_prefs_t2template", "", is_none],
    ["hcp_prefs_t2templatebrain", "", is_none],
    ["hcp_prefs_t2template2mm", "", is_none],
    ["hcp_prefs_templatemask", "", is_none],
    ["hcp_prefs_template2mmmask", "", is_none],
    ["hcp_prefs_fnirtconfig", "", is_none],
    ["hcp_species", "", is_none],
    ["hcp_runmode", "", is_none],
    ["hcp_truepatientposition", "", is_none],
    ["hcp_scannerpatientposition", "", is_none],
    ["hcp_betcenter", "", is_none],
    ["hcp_betradius", "", is_none],
    ["hcp_betfraction", "", is_none],
    ["hcp_bettop2center", "", is_none],
    ["hcp_brainextract", "", is_none],
    ["hcp_use_t2w_phase_zero", "", is_none],
    ["hcp_bias_field_sigma_no_t2w", "", is_none],
    ["hcp_betbiasfieldcor", "", is_none],
    ["# --- hcp_freesurfer options"],
    ["hcp_fs_seed", "", is_none],
    ["hcp_fs_existing_session", "False", torf],
    ["hcp_fs_edits", "FALSE", str],
    ["hcp_fs_extra_reconall", "", str],
    ["hcp_expert_file", "", str],
    ["hcp_fs_flair", "False", torf],
    ["hcp_conf2hires", "", is_none],
    ["hcp_hires", "", is_none],
    ["# --- hcp_nhp_freesurfer options"],
    ["hcp_scale_factor", "", is_none],
    ["hcp_fs_t1wdivflair", "False", torf],
    ["# --- hcp_post_freesurfer options"],
    ["hcp_mcsigma", "", str],
    ["hcp_inflatescale", "1", str],
    ["hcp_fs_ind_mean", "YES", str],
    ["hcp_myelin_volume_fwhm", "", is_none],
    ["hcp_myelin_surface_fwhm", "", is_none],
    ["hcp_msmsulc_conf", "", is_none],
    ["hcp_flatmap_root_name", "", is_none],
    ["# --- hcp_fmri_volume options"],
    ["hcp_bold_biascorrection", "NONE", str],
    ["hcp_bold_usejacobian", "", str],
    ["hcp_bold_echospacing", "", is_none],
    ["hcp_bold_sbref", "NONE", str],
    ["hcp_bold_dcmethod", "", is_none],
    ["hcp_bold_echodiff", "", is_none],
    ["hcp_bold_unwarpdir", "y", str],
    ["hcp_bold_gdcoeffs", "NONE", str],
    ["hcp_bold_doslicetime", "False", torf],
    ["hcp_bold_slicetimingfile", "False", torf],
    ["hcp_bold_slicetimerparams", "", str],
    ["hcp_bold_movreg", "MCFLIRT", str],
    ["hcp_bold_movref", "independent", str],
    ["hcp_bold_seimg", "independent", str],
    ["hcp_bold_refreg", "", str],
    ["hcp_bold_mask", "", str],
    ["hcp_bold_sephaseneg", "", is_none],
    ["hcp_bold_sephasepos", "", is_none],
    ["hcp_bold_seechospacing", "", is_none],
    ["hcp_bold_seunwarpdir", "", is_none],
    ["hcp_bold_topupconfig", "", is_none],
    ["hcp_bold_preregistertool", "", str],
    ["hcp_bold_dof", "", str],
    ["hcp_bold_stcorrdir", "", str],
    ["hcp_bold_stcorrint", "", str],
    ["hcp_bold_precomputedfmap", "", is_none],
    ["hcp_bold_precomputedfmapmag", "", is_none],
    ["hcp_bold_sephaseneg2", "", is_none],
    ["hcp_bold_sephasepos2", "", is_none],
    ["hcp_bold_sephasezero", "", is_none],
    ["hcp_bold_sephasezerofsbrainmask", "", is_none],
    ["hcp_bold_bbrcontrast", "", is_none],
    ["hcp_bold_wmprojabs", "", is_none],
    ["hcp_bold_initworldmat", "", is_none],
    ["hcp_wb_resample", "", flag],
    ["hcp_echo_te", "", is_none],
    ["longitudinal", None, flag],
    ["# --- hcp_diffusion options"],
    ["hcp_dwi_echospacing", "", str],
    ["hcp_dwi_phasepos", "PA", str],
    ["hcp_dwi_gdcoeffs", "NONE", str],
    ["hcp_dwi_dof", "", is_none],
    ["hcp_dwi_b0maxbval", "", is_none],
    ["hcp_dwi_combinedata", "", is_none],
    ["hcp_dwi_extraeddyarg", "", is_none],
    ["hcp_dwi_name", "", is_none],
    ["hcp_nogpu", None, flag],
    ["hcp_cuda_version", "", is_none],
    ["hcp_high_myelin", "auto", str],
    ["hcp_dwi_selectbestb0", None, flag],
    ["hcp_dwi_even_slices", None, flag],
    ["hcp_dwi_topupconfig", "", is_none],
    ["hcp_dwi_posdata", "", is_none],
    ["hcp_dwi_negdata", "", is_none],
    ["hcp_dwi_dummy_bval_bvec", None, flag],
    ["hcp_dwi_wmprojabs", "", is_none],
    ["hcp_dwi_resamp", "", is_none],
    ["hcp_dwi_usephasezero", None, flag],
    ["# --- dwi_f99, dwi_xtract and dwi_noddi_gpu options"],
    ["diffusion_folder", "", is_none],
    [
        "# --- general hcp_icafix, hcp_post_fix, hcp_reapply_fix, hcp_msmall, hcp_dedrift_and_resample options"
    ],
    ["hcp_icafix_bolds", "", is_none],
    ["hcp_icafix_highpass", "", is_none],
    ["hcp_matlab_mode", "", is_none],
    ["hcp_icafix_domotionreg", "", is_none],
    ["hcp_icafix_deleteintermediates", "", is_none],
    ["hcp_icafix_fallbackthreshold", "", is_none],
    ["hcp_icafix_parallel_limit", "", is_none],
    ["hcp_clean_substring", "", is_none],
    ["# --- hcp_icafix options"],
    ["hcp_icafix_model", "", is_none],
    ["hcp_icafix_threshold", "", is_none],
    ["hcp_icafix_postfix", "True", torf],
    ["hcp_icafix_processingmode", "", is_none],
    ["hcp_icafix_icadim_mode", "", is_none],
    ["hcp_reuse_existing_ica", "", is_none],
    ["hcp_fix_backup", "", is_none],
    ["hcp_t1wtemplatebrain", "", is_none],
    ["hcp_ica_method", "", is_none],
    ["hcp_vol_wisharts", "", is_none],
    ["hcp_cifti_wisharts", "", is_none],
    ["hcp_icadim_mode", "", is_none],
    ["hcp_legacy_fix", "", flag],
    ["hcp_icafix_concatenate_only", "", flag],
    ["# --- hcp_post_fix options"],
    ["hcp_postfix_dualscene", "", is_none],
    ["hcp_postfix_singlescene", "", is_none],
    ["hcp_postfix_reusehighpass", "True", torf],
    ["# --- hcp_reapply_fix options"],
    ["hcp_icafix_regname", "NONE", str],
    ["# --- hcp_msmall options options"],
    ["hcp_msmall_bolds", "", is_none],
    ["hcp_msmall_outfmriname", "rfMRI_REST", str],
    ["hcp_msmall_templates", "", is_none],
    ["hcp_msmall_outregname", "MSMAll_InitialReg", str],
    ["hcp_msmall_procstring", "", is_none],
    ["hcp_msmall_resample", "True", torf],
    ["hcp_msmall_myelin_target", "", is_none],
    ["hcp_msmall_module_name", "", is_none],
    ["hcp_msmall_iteration_modes", "", is_none],
    ["hcp_msmall_method", "", is_none],
    ["hcp_msmall_use_migp", "", flag],
    ["hcp_msmall_ica_dim", "", is_none],
    ["hcp_msmall_low_sica_dims", "", is_none],
    ["hcp_msmall_vn", "", flag],
    ["hcp_msmall_reg_conf_path", "", is_none],
    ["hcp_msmall_reg_vars", "", is_none],
    ["hcp_msmall_rsn_template", "", is_none],
    ["hcp_msmall_rsn_weights", "", is_none],
    ["hcp_msmall_topography_roi", "", is_none],
    ["hcp_msmall_topography_target", "", is_none],
    ["hcp_msmall_no_ind_mean", "", flag],
    ["hcp_msmall_start_frame", "", is_none],
    ["hcp_msmall_end_frame", "", is_none],
    ["# --- hcp_dedrift_and_resample options"],
    ["hcp_resample_concatregname", "MSMAll", str],
    ["hcp_resample_regname", "", is_none],
    ["hcp_resample_reg_files", "", is_none],
    ["hcp_resample_maps", "sulc,curvature,corrThickness,thickness", str],
    ["hcp_resample_myelinmaps", "MyelinMap,SmoothedMyelinMap", str],
    ["hcp_resample_dontfixnames", "", is_none],
    ["hcp_resample_inregname", "", is_none],
    ["hcp_resample_use_ind_mean", "", is_none],
    ["hcp_resample_extractnames", "", is_none],
    ["hcp_resample_extractextraregnames", "", is_none],
    ["hcp_resample_extractvolume", "", is_none],
    ["# --- hcp_task_fmri_analysis options"],
    ["hcp_task_lvl1tasks", "", is_none],
    ["hcp_task_lvl1fsfs", "", is_none],
    ["hcp_task_lvl2task", "", is_none],
    ["hcp_task_lvl2fsf", "", is_none],
    ["hcp_task_summaryname", "", is_none],
    ["hcp_task_confound", "", is_none],
    ["hcp_bold_final_smoothFWHM", "", is_none],
    ["hcp_task_highpass", "", is_none],
    ["hcp_task_lowpass", "", is_none],
    ["hcp_task_procstring", "", is_none],
    ["hcp_task_parcellation", "", is_none],
    ["hcp_task_parcellation_file", "", is_none],
    ["hcp_task_vba", None, flag],
    ["# --- hcp_asl options"],
    ["hcp_asl_mtname", "", is_none],
    ["hcp_asl_territories_atlas", "", is_none],
    ["hcp_asl_territories_labels", "", is_none],
    ["hcp_asl_cores", "", is_none],
    ["hcp_asl_interpolation", "", is_none],
    ["hcp_asl_use_t1", None, flag],
    ["hcp_asl_nobandingcorr", None, flag],
    ["hcp_asl_stages", None, is_none],
    ["hcp_asl_ntis", None, is_none],
    ["hcp_asl_tis", None, is_none],
    ["hcp_asl_rpts", None, is_none],
    ["hcp_asl_bolus", None, is_none],
    ["hcp_asl_slicedt", None, is_none],
    ["hcp_asl_sliceband", None, is_none],
    ["hcp_asl_te", None, is_none],
    ["hcp_asl_tail_discard_vols", None, is_none],
    ["hcp_asl_ibf", None, is_none],
    ["# --- hcp_temporal_ica options"],
    ["hcp_tica_studyfolder", "", is_none],
    ["hcp_tica_bolds", "", is_none],
    ["hcp_tica_outfmriname", "rfMRI_REST", str],
    ["hcp_tica_surfregname", "", is_none],
    ["hcp_tica_procstring", "", is_none],
    ["hcp_outgroupname", "", is_none],
    ["hcp_tica_timepoints", "", is_none],
    ["hcp_tica_num_wishart", "", is_none],
    ["hcp_tica_mrfix_concat_name", "", is_none],
    ["hcp_tica_icamode", "", is_none],
    ["hcp_tica_precomputed_clean_folder", "", is_none],
    ["hcp_tica_precomputed_fmri_name", "", is_none],
    ["hcp_tica_precomputed_group_name", "", is_none],
    ["hcp_tica_extra_output_suffix", "", is_none],
    ["hcp_tica_pca_out_dim", "", is_none],
    ["hcp_tica_pca_internal_dim", "", is_none],
    ["hcp_tica_migp_resume", "", is_none],
    ["hcp_tica_sicadim_iters", "", is_none],
    ["hcp_tica_sicadim_override", "", is_none],
    ["hcp_low_sica_dims", "", is_none],
    ["hcp_tica_reclean_mode", "", is_none],
    ["hcp_tica_starting_step", "", is_none],
    ["hcp_tica_stop_after_step", "ComputeTICAFeatures", str],
    ["hcp_tica_remove_manual_components", "", is_none],
    ["hcp_tica_fix_legacy_bias", "", is_none],
    ["hcp_parallel_limit", "", is_none],
    ["hcp_tica_average_dataset", "", is_none],
    ["hcp_tica_extract_fmri_name_list", "", is_none],
    ["hcp_tica_extract_fmri_out", "", is_none],
    ["hcp_tica_config_out", None, flag],
    ["hcp_tica_longitudinal_extract_all", None, flag],
    ["hcp_longitudinal_subject", None, is_none],
    ["hcp_longitudinal_sessions", None, is_none],
    ["# --- hcp_fmri_stats options"],
    ["hcp_concat_names", "fMRI_CONCAT_ALL", str],
    ["hcp_fmristats_process_volume", "", is_none],
    ["hcp_fmristats_cleanup_effects", "", is_none],
    ["hcp_fmristats_procstring", "", is_none],
    ["hcp_fmristats_icamode", "", is_none],
    ["hcp_fmristats_fmri_names", "", is_none],
    ["hcp_fmristats_tica_component_tcs", "", is_none],
    ["hcp_fmristats_tica_component_noise", "", is_none],
    ["hcp_fmristats_regname", "", is_none],
    ["# --- hcp_cortical_thickness options"],
    ["hcp_corrthick_regnames", "", is_none],
    ["hcp_corrthick_hemi", "", is_none],
    ["hcp_corrthick_surf", "", is_none],
    ["hcp_corrthick_patch_size", "", is_none],
    ["hcp_corrthick_surf_smooth", "", is_none],
    ["hcp_corrthick_metric_smooth", "", is_none],
    ["hcp_corrthick_skip_computation", "", is_none],
    ["# --- hcp_apply_auto_reclean options"],
    ["hcp_autoreclean_model_folder", "", is_none],
    ["hcp_autoreclean_model_to_use", "", is_none],
    ["hcp_autoreclean_vote_threshold", "", is_none],
    ["# --- hcp_make_average_dataset options"],
    ["hcp_surface_atlas_dir", "", is_none],
    ["hcp_grayordinates_dir", "", is_none],
    ["hcp_freesurfer_labels", "", is_none],
    ["hcp_thickness_regression", "", is_none],
    ["hcp_pregradient_smoothing", "1", int],
    ["hcp_mad_regname", "MSMAll", str],
    [
        "hcp_mad_videen_maps",
        "corrThickness,thickness,MyelinMap_BC,SmoothedMyelinMap_BC",
        str,
    ],
    ["hcp_mad_greyscale_maps", "sulc,curvature", str],
    [
        "hcp_mad_distortion_maps",
        "SphericalDistortion,ArealDistortion,EdgeDistortion",
        str,
    ],
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
    # empty means "take the settings value", so a per-command
    # --comlog_folders overrides the policy and the policy supplies the default
    ["comlog_folders", "", str],
    ["# --- mice pipelines"],
    ["voxel_increase", "", is_none],
    ["orientation", "x -y z", str],
    ["no_despike", "", flag],
    ["bias_field_correction", "yes", str],
    ["melodic_anatfile", "", is_none],
    ["fix_rdata", "", is_none],
    ["fix_threshold", "20", int],
    ["fix_no_motion_cleanup", "", flag],
    ["fix_aggressive_cleanup", "", flag],
    ["mice_highpass", "0.01", str],
    ["mice_lowpass", "0.25", str],
    ["mice_volumes", "900", int],
    ["flirt_ref", "", is_none],
    ["# --- hcp_long_freesurfer options"],
    ["hcp_longitudinal_template", "base", str],
    ["hcp_no_t2w", "", flag],
    ["hcp_seed", "", is_none],
    ["hcp_parallel_mode", "BUILTIN", str],
    ["hcp_fslsub_queue", "", is_none],
    ["hcp_max_jobs", "", is_none],
    ["hcp_start_stage", "", is_none],
    ["hcp_end_stage", "", is_none],
    ["# --- hcp_transmit_bias_individual options"],
    ["hcp_transmit_mode", "", is_none],
    ["hcp_gmwm_template", "", is_none],
    ["hcp_group_corrected_myelin", "", is_none],
    ["hcp_afi_image", "", is_none],
    ["hcp_afi_tr_one", "", is_none],
    ["hcp_afi_tr_two", "", is_none],
    ["hcp_afi_angle", "", is_none],
    ["hcp_b1tx_magnitude", "", is_none],
    ["hcp_b1tx_phase", "", is_none],
    ["hcp_b1tx_phase_divisor", "", is_none],
    ["hcp_pt_fmri_names", "", is_none],
    ["hcp_pt_bbr_threshold", "", is_none],
    ["hcp_myelin_template", "", is_none],
    ["hcp_group_uncorrected_myelin", "", is_none],
    ["hcp_pt_reference_value_file", "", is_none],
    ["hcp_unproc_t1w_list", "", is_none],
    ["hcp_unproc_t2w_list", "", is_none],
    ["hcp_receive_bias_body_coil", "", is_none],
    ["hcp_receive_bias_head_coil", "", is_none],
    ["hcp_raw_psn_t1w", "", is_none],
    ["hcp_raw_nopsn_t1w", "", is_none],
    ["hcp_transmit_res", "", is_none],
    ["hcp_myelin_mapping_fwhm", "", is_none],
    ["hcp_old_myelin_mapping", "", flag],
    ["# --- hcp_transmit_bias_individual_align options"],
    ["hcp_manual_receive", "False", torf],
    ["# --- hcp_transmit_bias_group_average_fit options"],
    ["hcp_all_uncorrected_myelin", "", is_none],
    ["hcp_transmit_group_name", "", is_none],
    ["# --- hcp_transmit_bias_group_average_corrected_maps options"],
    ["hcp_average_myelin", "", is_none],
    ["hcp_voltages", "", is_none],
    ["# --- fsl_feat options"],
    ["feat_file", "", is_none],
    ["# --- fsl_melodic options"],
    ["input_files", "", is_none],
    ["melodic_extra_args", "", is_none],
    ["# --- rapidtide options"],
    [
        "despecklepasses",
        "",
        is_none,
    ],
    [
        "filterband",
        "",
        is_none,
    ],
    [
        "searchrange",
        "",
        is_none,
    ],
    [
        "nprocs",
        "",
        is_none,
    ],
    [
        "nofitfilt",
        "",
        flag,
    ],
    [
        "similaritymetric",
        "",
        is_none,
    ],
    [
        "ampthresh",
        "",
        is_none,
    ],
    [
        "numnull",
        "",
        is_none,
    ],
    [
        "outputlevel",
        "",
        is_none,
    ],
    [
        "spatialfilt",
        "",
        is_none,
    ],
    [
        "simcalcrange",
        "",
        is_none,
    ],
    [
        "brainmask",
        "",
        is_none,
    ],
    [
        "graymattermask",
        "",
        is_none,
    ],
    [
        "whitemattermask",
        "",
        is_none,
    ],
    [
        "refineexclude",
        "",
        is_none,
    ],
    [
        "nodenoise",
        "",
        flag,
    ],
    ["rapidtide_extra_args", "", is_none],
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
    ["test", "test", "run"],
    ["overwrite", True],
    ["hcp_nogpu", True],
    ["hcp_dwi_selectbestb0", True],
    ["hcp_asl_use_t1", True],
    ["hcp_asl_nobandingcorr", True],
    ["hcp_task_vba", True],
    ["hcp_tica_config_out", False],
    ["no_despike", True],
    ["fix_no_motion_cleanup", True],
    ["fix_aggressive_cleanup", False],
    ["longitudinal", True],
    ["hcp_tica_longitudinal_extract_all", True],
    ["hcp_icafix_concatenate_only", True],
    ["hcp_old_myelin_mapping", True],
    ["nofitfilt", True],
    ["nodenoise", True],
    ["hcp_msmall_use_migp", True],
    ["hcp_msmall_vn", True],
    ["hcp_msmall_no_ind_mean", True],
]

# Add flags used in extensions
flaglist += extensions.compile_list("flaglist")

#   ------------------------------------------------------------------ OPTIONS
#   The options dictionary
options = {}

flist = {}
for line in flaglist:
    if len(line) == 2:
        flist[line[0]] = [line[0], line[1]]
    else:
        flist[line[0]] = [line[2], line[1]]


# ==============================================================================
#                                                              MERGING PARAMETERS
#
def merge_options(command, args, header=None):
    """
    ``merge_options(command, args, header=None)``

    Merges the parameter tiers into the one options dictionary every command is
    run from: the `arglist` defaults, then the batch file header, then the
    command line, each overriding the one before it.

    Done once per invocation, in `gmri.runCommand`, so that every command class
    starts from the same dictionary and the study the batch file names is known
    before the run's logging is resolved.

    Parameters:
        --command   The name of the command to be run.
        --args      The parsed command line arguments.
        --header    The parameters from the batch file header, if there was one.

    Returns:
        The merged options, and for every name in them the tier its value came
        from - one of "default", "batch file", "recipe" or "command line".
    """
    options = {"command_ran": command}
    sources = {"command_ran": "default"}

    def take(source, items):
        for key, value in items:
            options[key] = value
            sources[key] = source

    # the defaults
    take("default", [(line[0], line[1]) for line in arglist if len(line) == 3])

    # the batch file header
    if header:
        take("batch file", gcs.check_deprecated_parameters(header, command).items())

    # the command line, where a flag stands for a value
    for key, value in args.items():
        if key in flist:
            take(
                "command line",
                [(flist[key][0], value if value is not True else flist[key][1])],
            )
        else:
            take("command line", [(key, value)])

    # take care of variable expansion
    for key in options:
        if type(options[key]) is str:
            options[key] = os.path.expandvars(options[key])

    # recode as last step before options are used
    for line in arglist:
        if len(line) == 3:
            try:
                options[line[0]] = line[2](options[line[0]])
            except Exception:
                raise ge.CommandError(
                    command,
                    "Invalid parameter value!",
                    "Parameter `%s` is specified but is set to an invalid value:"
                    % (line[0]),
                    "---> %s=%s" % (line[0], str(options[line[0]])),
                    "Please check acceptable inputs for %s!" % (line[0]),
                )

    # impute unspecified parameters. An imputed value stays "default": nobody
    # specified it, which is what the source says
    options = gcs.impute_parameters(options, command)

    return options, sources


# ==============================================================================
#                                                               RUNNING COMMANDS
#
def run(qx_command, args, sessions, options, sources, run_context):
    """
    ``run(qx_command, args, sessions, options, sources, run_context)``

    Runs a processing command over the sessions it was given, locally or
    through a scheduler, and records what happened in the run's runlog.

    The sessions, the merged options and the run's logs are all settled by
    `gmri.runCommand` before the dispatch - the batch file can name a different
    study, so they have to be, or the run would log itself somewhere else.
    What is left here is the per-session tier: the `_key` overrides a batch file
    states for one session only.

    Parameters:
        --qx_command    The registry entry of the command to run.
        --args          The parsed command line arguments, for the call echo.
        --sessions      The sessions to process.
        --options       The merged options, from `merge_options`.
        --sources       Where each of them came from, from the same call.
        --run_context   The run's logs.
    """
    processing_type = "session"
    if "subject" in qx_command.type:
        processing_type = "subject"
    elif "study" in qx_command.type:
        processing_type = "study"

    # -- do we need a list of subjects?
    subjects = []
    if processing_type == "subject":
        # check if all sessions have subjects for longitudinal
        missing_subjects = sessions.dont_have_key("subject")
        if missing_subjects:
            missing_list = missing_subjects.get_list_by_key("id")
            raise ge.CommandFailed(
                qx_command.name,
                "Missing subject information",
                "No subject information provided for session ids: %s." % (missing_list),
                "Please check the batch file!",
                "Aborting processing!",
            )
        subjects = sessions.group_by_key("subject")

    # set key parameters
    overwrite = options["overwrite"]
    parsessions = options["parsessions"]
    parsubjects = options["parsubjects"]
    nprocess = options["nprocess"]
    printinfo = options["datainfo"]

    logfolder = run_context.logfolder
    comlogfolder = run_context.comlogfolder
    specfolder = os.path.join(options["sessionsfolder"], "specs")

    options["comlogs"] = comlogfolder
    options["logfolder"] = logfolder
    options["specfolder"] = specfolder

    # --------------------------------------------------------------------------
    #                                                      start writing the log
    os.makedirs(comlogfolder, exist_ok=True)

    stati = []

    def session_options(session):
        """The per session tier, applied and -- when there is one -- reported."""
        soptions, ssources = gcs.update_options(session, options, sources)
        if ssources != sources:
            banner = gcs.report_parameters(
                qx_command, soptions, ssources, session=session
            )
            print(banner)
            run_context.write(banner)

        return soptions

    # `sout` follows the header and the parameter report, both of which
    # `gmri.runCommand` has already written
    sout = ""

    # no parsessions for subject and multi-session commands
    if processing_type in ["subject", "study"]:
        if parsessions > 1:
            sout += f"\nWARNING: parsessions [{parsessions}] will be set to 1 because you are running a multi-session command!\n"
            parsessions = 1

    parprocesses = parsubjects if processing_type == "subject" else parsessions

    # check if there are no sessions
    if not sessions or processing_type == "subject" and not subjects:
        sout += f"\nERROR: No {processing_type}s specified to process. Please check your batch file, filtering options or sessions parameter!\n"
        print(sout)
        run_context.write(sout)
        exit()

    elif options["run"] == "run":
        sout += f"\nStarting multiprocessing {processing_type}s in {options['sessions']} with a pool of {parprocesses} concurrent processes\n"

    else:
        sout += "\nRunning test on %s ...\n" % (options["sessions"])

    print(sout)
    run_context.write(sout)

    # -----------------------------------------------------------------------
    #                                                              print info
    if printinfo:
        if processing_type == "subject":
            print(subjects)
        else:
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
        # testing or processing
        action = "testing" if options["run"] == "test" else "processing"
        pending_actions = qx_command.load_callable()

        c = 0
        if parprocesses == 1 or options["run"] == "test":
            # ------------------------------------------------------------------
            #                                          study processing commands
            if processing_type == "study":
                sessionid_list = sessions.get_list_by_key("id")

                # update options and prepare the all sessions string for labeling
                # TODO: soptions may be invalid here!
                for session in sessions:
                    soptions, _ = gcs.update_options(session, options, sources)

                message = f"\nStarting {action} of sessions {sessionid_list} at {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}"
                print(message)

                # process and write log
                log = pending_actions(sessions, soptions, overwrite, c + 1)
                log.write_to(run_context)
                stati.append(log.status)

            # ------------------------------------------------------------------
            #                                        subject processing commands
            elif processing_type == "subject":
                for subject in subjects:
                    session_ids = ", ".join([s["id"] for s in subject])
                    message = f"\nProcessing subject {subject[0]['subject']} with sessions {session_ids} at {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}"
                    print(message)

                    log = pending_actions(subject, options, overwrite, c + 1)
                    log.write_to(run_context)
                    stati.append(log.status)
                    c += 1
                    if nprocess and c >= nprocess:
                        break

            # ------------------------------------------------------------------
            #                                        session processing commands
            else:
                for session in sessions:
                    if len(session["id"]) > 1:
                        message = f"\nStarting {action} of session {session['id']} at {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}"
                        print(message)

                        soptions = session_options(session)

                        log = pending_actions(session, soptions, overwrite, c + 1)
                        log.write_to(run_context)
                        stati.append(log.status)
                        c += 1
                        if nprocess and c >= nprocess:
                            break

        else:
            c = 0
            process_pool_executor = ProcessPoolExecutor(parprocesses)
            futures = []

            # ------------------------------------------------------------------
            #                                        subject processing commands

            if processing_type == "subject":
                for subject in subjects:
                    message = f"\nAdding processing of subject {subject[0]['subject']} with sessions {', '.join([s['id'] for s in subject])} to the pool at {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}"
                    print(message)

                    future = process_pool_executor.submit(
                        pending_actions, subject, options, overwrite, c + 1
                    )
                    futures.append(future)
                    c += 1
                    if nprocess and c >= nprocess:
                        break

            # ------------------------------------------------------------------
            #                                        session processing commands

            if processing_type == "session":
                for session in sessions:
                    if len(session["id"]) > 1:
                        soptions = session_options(session)
                        message = f"\nAdding processing of session {session['id']} to the pool at {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}"
                        print(message)

                        future = process_pool_executor.submit(
                            pending_actions, session, soptions, overwrite, c + 1
                        )
                        futures.append(future)
                        c += 1
                        if nprocess and c >= nprocess:
                            break

            for future in as_completed(futures):
                # the log comes back through the pickle the pool made of it;
                # `__getstate__` dropped its streams on the way out, so it
                # arrives with its text and its counts and nothing to close
                log = future.result()
                log.write_to(run_context)
                stati.append(log.status)

        # the reports were appended as the sessions completed; all that is
        # left is the digest
        run_context.final_report(stati)

        # and, when a parent process asked for it, the same digest as data
        run_context.write_status(stati)

        # a failed session makes the command fail: the caller -- a shell, CI,
        # or run_recipe -- learns it from the exit code rather than by reading
        # the report
        if any(failed for _, _, failed in stati):
            raise ge.CommandFailed(
                qx_command.name,
                "Not all tasks completed fully",
                "Please check the logs in %s" % (logfolder),
            )

    # -----------------------------------------------------------------------
    #                                                  general scheduler code
    #
    # TODO: adapt for subject and study level processing
    else:
        # schedule
        gs.run_through_scheduler(
            qx_command.name,
            sessions=sessions,
            args=args,
            parsessions=parsessions,
            run=run_context,
        )
