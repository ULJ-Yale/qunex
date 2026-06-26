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

import general.commands_support as gcs
import general.core as gc
import general.exceptions as ge
import general.scheduler as gs
import qx_mice.process_mice
import qx_mice.setup_mice
from general import extensions
from general.bids import map_nii2bids
from general.parsing import flag, is_none
from general.parsing import true_or_false as torf

# pipelines imports
from hcp import process_hcp
from processing import dwi, fs, fsl, rapidtide, simple, workflow

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
        "printoptions",
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
        "omp_threads",
        "",
        is_none,
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
        int,
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
    ["hcp_unwarpdir", "z", str],
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
    ["hcp_bold_smoothFWHM", "2", int],
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
    ["hcp_high_myelin", "auto", str],
    ["hcp_dwi_selectbestb0", None, flag],
    ["hcp_dwi_even_slices", None, flag],
    ["hcp_dwi_topupconfig", "", is_none],
    ["hcp_dwi_posdata", "", is_none],
    ["hcp_dwi_negdata", "", is_none],
    ["hcp_dwi_dummy_bval_bvec", None, flag],
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
    ["hcp_nhp_freesurfer", process_hcp.hcp_nhp_freesurfer],
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
    ["hcp_fmri_stats", process_hcp.hcp_fmri_stats],
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
    ["hcp_prep_long", process_hcp.hcp_prep_long],
    ["hcp_long_freesurfer", process_hcp.hcp_long_freesurfer],
    ["hcp_long_post_freesurfer", process_hcp.hcp_long_post_freesurfer],
    ["hcp_long_msmall", process_hcp.hcp_long_msmall],
    ["hcp_long_transmit_bias", process_hcp.hcp_long_transmit_bias],
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

    timestamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
    studyfolders = gc.deduce_folders(options, command, timestamp)
    logfolder = studyfolders["logfolder"]
    comlogfolder = os.path.join(logfolder, "comlogs")
    specfolder = os.path.join(studyfolders["sessionsfolder"], "specs")

    options["comlogs"] = comlogfolder
    options["logfolder"] = logfolder
    options["specfolder"] = specfolder

    # --------------------------------------------------------------------------
    #                                                      start writing the log
    os.makedirs(comlogfolder, exist_ok=True)
    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")

    if not options["longitudinal"]:
        logname = os.path.join(logfolder, "Log-%s-%s.log") % (command, logstamp)
    else:
        logname = os.path.join(logfolder, "Log-%s-long-%s.log") % (command, logstamp)

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
            "\nStarting multiprocessing sessions in %s with a pool of %d concurrent processes\n"
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
