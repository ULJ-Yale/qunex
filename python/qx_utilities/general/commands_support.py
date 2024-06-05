#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``commands_support.py``

Helper code for perarations of commands and their parameters
"""

from general import extensions

# ==============================================================================
#                                                            COMMAND DEPRECATION
#

# The "deprecated_commands" dictionary specifies old and new command names
# The format is as such:
# "new_command_name": ["deprecated_name1", "depercated_name2", ...]
deprecated_commands = {
    "fc_compute_ab_corr": ["fc_ComputeABCorr"],
    "fc_compute_ab_corr_kca": ["fc_ComputeABCorrKCA"],
    "fc_compute_gbc3": ["fc_ComputeGBC3"],
    "fc_compute_gbcd": ["fc_ComputeGBCd"],
    "fc_compute_roifc": [
        "fc_ComputeROIFC",
        "fc_ComputeROIFCGroup",
        "fc_compute_roifc_group",
    ],
    "fc_compute_seedmaps": [
        "fc_ComputeSeedMaps",
        "fc_compute_seedmaps_group",
        "fc_ComputeSeedMapsGroup",
    ],
    "fc_compute_seedmaps_multiple": ["fc_ComputeSeedMapsMultiple"],
    "fc_extract_roi_timeseries_masked": ["fc_ExtractROITimeseriesMasked"],
    "fc_extract_trial_timeseries_masked": ["fc_ExtractTrialTimeseriesMasked"],
    "fc_segment_mri": ["fc_fcMRISegment", "fc_mri_segment"],
    "fc_preprocess": ["fc_Preprocess"],
    "fc_preprocess_conc": ["fc_PreprocessConc"],
    "general_image_overlap": ["qa_imgOverlap"],
    "general_compute_bold_list_stats": ["g_ComputeBOLDListStats"],
    "general_compute_bold_stats": ["g_ComputeBOLDStats"],
    "general_compute_group_bold_stats": ["g_ComputeGroupBOLDStats"],
    "general_extract_roi_glm_values": ["g_ExtractROIGLMValues"],
    "general_extract_glm_volumes": ["g_ExtractGLMVolumes"],
    "general_extract_roi_values": ["g_ExtractROIValues"],
    "general_find_peaks": ["g_FindPeaks"],
    "general_parcellated2dense": ["g_Parcellated2Dense"],
    "general_plot_bold_timeseries": ["g_PlotBoldTS"],
    "general_plot_bold_timeseries_list": ["g_PlotBoldTSList"],
    "general_qa_concfile": ["g_QAConcFile"],
    "general_image_conjunction": ["g_ConjunctionG"],
    "stats_compute_behavioral_correlations": ["s_ComputeBehavioralCorrelations"],
    "stats_p2z": ["s_p2Z"],
    "stats_ttest_dependent": ["s_TTestDependent"],
    "stats_ttest_independent": ["s_TTestIndependent"],
    "stats_ttest_zero": ["s_TTestZero"],
    "run_qc": ["runQC", "RunQC", "QCPreproc"],
    "parcellate_anat": ["ANATparcellate", "anat_parcellate"],
    "fc_compute_wrapper": ["BOLDcomputeFC", "bold_compute_fc", "compute_fc_bold"],
    "parcellate_bold": ["BOLDparcellate", "bold_parcellate", "bold_parcellation"],
    "data_sync": ["DataSync"],
    "run_qc_dwi_eddy": ["runQC_DWIeddyQC"],
    "dwi_eddy_qc": ["DWIeddyQC"],
    "dwi_bedpostx_gpu": ["DWIFSLbedpostxGPU", "FSLBedpostxGPU", "dwi_fsl_bedpostx_gpu"],
    "dwi_dtifit": ["DWIFSLdtifit", "FSLDTtifit", "dwi_fsl_dtifit"],
    "run_qc_dwi_dtifit": [
        "runQC_DWIFSLdtifit",
        "run_qc_dwi_fsl_dtifit",
        "runQC_DWIDTIFIT",
    ],
    "dwi_legacy_gpu": ["dwi_legacy", "hcpdLegacy", "DWILegacy"],
    "dwi_parcellate": ["DWIparcellate", "DWIDenseParcellation"],
    "dwi_probtrackx_dense_gpu": ["DWIprobtrackxDenseGPU", "ProbtrackxGPUDense"],
    "dwi_seed_tractography_dense": ["DWIseedTractographyDense", "DWISeedTractography"],
    "roi_extract": ["ROIExtract"],
    "run_qc_t1w": ["runQC_T1w"],
    "run_qc_t2w": ["runQC_T2w"],
    "run_qc_myelin": ["runQC_Myelin"],
    "run_qc_bold": ["runQC_BOLD"],
    "run_qc_bold_fc": ["runQC_BOLDfc"],
    "run_qc_dwi": ["runQC_DWI"],
    "run_qc_dwi_process": ["runQC_DWIProcess"],
    "run_qc_dwi_bedpostx": ["runQC_DWIBedpostX"],
    "run_qc_custom": ["runQC_Custom"],
    "run_qc_rawnii": ["runQC_rawNII"],
    "run_turnkey": ["runTurnkey"],
    "extract_roi": ["extractROI"],
    "matlab_help": ["matlabHelp"],
    "gmri_function": ["gmriFunction"],
    "organize_dicom": ["organizeDicom"],
    "dwi_pre_tractography": ["DWIpreTractography", "pretractographyDense"],
    "aws_hcp_sync": ["AWSHCPsync"],
    "map_hcp_files": ["mapHCPFiles"],
    "auto_ptx": ["autoPtx"],
    "compute_bold_fc": ["computeBOLDfc"],
    "compute_bold_fc_gbc": ["computeBOLDfcGBC"],
    "compute_bold_fc_seed": ["computeBOLDfcSeed"],
    "list_dicom": ["listDicom"],
    "split_dicom": ["splitDicom"],
    "sort_dicom": ["sortDicom"],
    "import_hcp": ["HCPLSImport", "importHCP"],
    "import_bids": ["BIDSImport", "importBIDS"],
    "import_dicom": ["processInbox", "importDICOM"],
    "export_hcp": ["mapIO", "exportHCP"],
    "list_session_info": ["listSubjectInfo", "listSessionInfo"],
    "create_session_info": ["getHCPReady", "createSessionInfo"],
    "create_study": ["createStudy"],
    "get_dicom_info": ["getDICOMInfo"],
    "map_bids2nii": ["mapBIDS2nii"],
    "map_hcpls2nii": ["mapHCPLS2nii"],
    "run_nil_folder": ["runNILFolder"],
    "run_nil": ["runNIL"],
    "slice_image": ["sliceImage"],
    "setup_hcp": ["setupHCP"],
    "create_batch": ["createBatch"],
    "manage_study": ["manageStudy"],
    "create_list": ["createList"],
    "create_conc": ["createConc"],
    "gather_behavior": ["gatherBehavior"],
    "pull_sequence_names": ["pullSequenceNames"],
    "batch_tag2namekey": ["batchTag2NameKey"],
    "join_fidl": ["joinFidl"],
    "join_fidl_folder": ["joinFidlFolder"],
    "split_fidl": ["splitFidl"],
    "check_fidl": ["checkFidl"],
    "map2pals": ["map2PALS"],
    "map2hcp": ["map2HCP"],
    "mask_map": ["maskMap"],
    "join_maps": ["joinMaps"],
    "run_palm": ["runPALM"],
    "create_ws_palm_design": ["createWSPALMDesign"],
    "get_dicom_fields": ["getDICOMFields"],
    "change_dicom_files": ["changeDICOMFiles"],
    "map_hcp_data": ["mapHCPData"],
    "get_bold_data": ["getBOLDData"],
    "create_bold_brain_masks": ["createBOLDBrainMasks"],
    "run_basic_segmentation": ["runBasicSegmentation"],
    "get_fs_data": ["getFSData"],
    "run_subcortical_fs": ["runSubcorticalFS"],
    "run_full_fs": ["runFullFS"],
    "compute_bold_stats": ["computeBOLDStats"],
    "create_stats_report": ["createStatsReport"],
    "extract_nuisance_signal": ["extractNuisanceSignal"],
    "preprocess_bold": ["preprocessBold"],
    "preprocess_conc": ["preprocessConc"],
    "hcp_pre_freesurfer": ["hcp_PreFS", "hcp1"],
    "hcp_freesurfer": ["hcp_FS", "hcp2"],
    "hcp_post_freesurfer": ["hcp_PostFS", "hcp3"],
    "hcp_fmri_volume": ["hcp_fMRIVolume", "hcp4"],
    "hcp_fmri_surface": ["hcp_fMRISurface", "hcp5"],
    "hcp_icafix": ["hcp_ICAFix"],
    "hcp_post_fix": ["hcp_PostFix"],
    "hcp_reapply_fix": ["hcp_ReApplyFix"],
    "hcp_msmall": ["hcp_MSMAll"],
    "hcp_dedrift_and_resample": ["hcp_DeDriftAndResample"],
    "hcp_diffusion": ["hcp_Diffusion", "hcpd"],
    "hcp_dtifit": ["hcp_DTIFit"],
    "hcp_bedpostx": ["hcp_Bedpostx"],
    "run_shell_script": ["runShellScript"],
    "create_bold_list": ["createBoldList"],
    "create_conc_list": ["createConcList"],
    "map_raw_data": ["mapRawData"],
    "hcp_task_fmri_analysis": ["hcp_TaskfMRIAnalysis"],
    "dwi_xtract": ["fsl_xtract"],
    "dwi_f99": ["fsl_f99"],
}

# Add information provided in extensions
deprecated_commands.update(extensions.compile_dict("deprecated_commands"))

# the function for checking whether a command is deprecated or not


def check_deprecated_commands(command):
    """
    check_deprecated_commands(options, deprecatedCommands)
    Checks for deprecated commands, remaps deprecated ones
    and notifies the user.
    """

    # store the command
    new_command = command
    # is it depreacted?
    for new_name, old_names in deprecated_commands.items():
        # if deprecated warn the user and call the new one
        if command.lower() in [s.lower() for s in old_names] and command != new_name:
            new_command = new_name
            print(
                "\n\nWARNING: Use of a deprecated command! Command %s is now known as %s"
                % (command, new_command)
            )
            print("")
            break

    return new_command


# ==============================================================================
#                                                          PARAMETER DEPRECATION
#

# The "deprecated_parameters" dictionary specifies what is mapped to what
# If the mapping is 1:1 use 'old_value': 'new_value'
# If the mapping is 1:n (an old value was split to several new ones) then
# for each mapping define the new_value and the functions that use it
# None value tells that the parameter is no longer used by QuNex
deprecated_parameters = {
    "bppt": "bolds",
    "bppa": "bold_actions",
    "bppn": "bold_nuisance",
    "eventstring": "event_string",
    "eventfile": "event_file",
    "basefolder": "sessionsfolder",
    "subjects": "sessions",
    "bold_preprocess": "bolds",
    "hcp_prefs_brainmask": "hcp_prefs_custombrain",
    "hcp_mppversion": "hcp_processing_mode",
    "hcp_dwelltime": "hcp_seechospacing",
    "hcp_bold_ref": "hcp_bold_sbref",
    "hcp_bold_preregister": "hcp_bold_preregistertool",
    "hcp_bold_stcorr": "hcp_bold_doslicetime",
    "hcp_bold_correct": "hcp_bold_dcmethod",
    "hcp_bold_usemask": "hcp_bold_mask",
    "hcp_bold_boldnamekey": "hcp_filename",
    "hcp_dwi_dwelltime": "hcp_dwi_echospacing",
    "cores": "parsessions",
    "threads": "parelements",
    "sfolder": "sourcefolder",
    "tfolder": "targetfolder",
    "tfile": "targetfile",
    "sfile": {
        "sourcefiles": ["create_batch", "pull_sequence_names", "gather_behavior"],
        "sourcefile": [
            "create_session_info",
            "setup_hcp",
            "slice_image",
            "run_nil",
            "run_nil_folder",
        ],
        "default": "sourcefile",
    },
    "sfilter": "filter",
    "hcp_fs_existing_subject": "hcp_fs_existing_session",
    "subjectsfolder": "sessionsfolder",
    "subjid": {
        "sessionid": ["dicom2niix", "batch_tag2namekey"],
        "sessionids": "export_hcp",
        "default": "sessionid",
    },
    "sbjroi": "sessionroi",
    "subjectf": "sessionf",
    "hcp_bold_sequencetype": None,
    "hcp_biascorrect_t1w": None,
    "args": "palm_args",
    "TR": "tr",
    "PEdir": "pedir",
}

# The "deprecated_values" dictionary specifies remapping of deprecated values
deprecated_values = {
    "hcp_processing_mode": {"hcp": "HCPStyleData", "legacy": "LegacyStyleData"},
    "hcp_filename": {
        "name": "userdefined",
        "number": "automated",
        "original": "userdefined",
        "standard": "automated",
    },
    "hcp_folderstructure": {"initial": "hcpya"},
    "gzip": {"yes": "folder", "ask": "folder"},
    "clean": {"ask": "no"},
    "unzip": {"ask": "yes"},
}


# The "to_impute" list specifies, which (target) options have to be checked whether
# they were not specified and therefore have value None, and in those cases use values from
# other (source) options. The specification is provided as a list of tuples pairs where the first
# string in the pair identifies the target option (the option to check) and the second string
# identifies the source option (the option from which to take the value to impute). Please note
# that the imputation will follow the order in which tuples are listed.

to_impute = [
    ("qx_cifti_tail", "hcp_cifti_tail"),
    ("qx_nifti_tail", "hcp_nifti_tail"),
    ("cifti_tail", "qx_cifti_tail"),
    ("nifti_tail", "qx_nifti_tail"),
]

# The "towarn_parameters" dictionary warns users to check the provided values
# the array for each parameter name has two entries
# 1 - the value to look for in parameter value
# 2 - the warning message that gets printer if the value is found
towarn_parameters = {
    "sessionsfolder": [
        "subject",
        'The sessionfolder parameter includes "subject", in a recent QuNex update "subject" was renamed to "session". Please check if the value you provided is correct.',
    ],
    "sourcefolder": [
        "subject",
        'The sourcefolder parameter includes "subject", in a recent QuNex update "subject" was renamed to "session". Please check if the value you provided is correct.',
    ],
    "sourcefile": [
        "subject",
        'The sourcefile parameter includes "subject", in a recent QuNex update "subject" was renamed to "session". Please check if the value you provided is correct.',
    ],
    "sourcefiles": [
        "subject",
        'The sourcefiles parameter includes "subject", in a recent QuNex update "subject" was renamed to "session". Please check if the value you provided is correct.',
    ],
}

# Add information provided in extensions
deprecated_parameters.update(extensions.compile_dict("deprecated_parameters"))
deprecated_values.update(extensions.compile_dict("deprecated_values"))
to_impute += extensions.compile_list("to_impute")
towarn_parameters.update(extensions.compile_dict("towarn_parameters"))


# ==============================================================================
#                                                  MAPPING DEPRECATED PARAMETERS
#


def check_deprecated_parameters(options, command):
    """
    ``check_deprecated_parameters(options, command)``

    Checks for deprecated parameters, remaps deprecated ones
    and notifies the user.
    """

    remapped = []
    deprecated = []
    newvalues = []

    # -> check remapped parameters
    # variable for storing new options
    new_options = {}
    # iterate over all options
    for k, v in options.items():
        if k in deprecated_parameters:
            # if v is a dictionary then
            # the parameter was remaped to multiple values
            mapto = deprecated_parameters[k]
            if type(mapto) is dict:
                for k2, v2 in mapto.items():
                    if command in v2:
                        mapto = k2
                        break
                    elif k2 == "default":
                        mapto = v2
                        break

            # if v is None then parameter is no longer in use
            if v:
                # remap
                new_options[mapto] = v
                remapped.append(k)
            else:
                deprecated.append(k)
        else:
            new_options[k] = v

    # custom remapping for sessions, sessionids and batchfile
    sessions = None
    if "sessions" in new_options:
        sessions = new_options["sessions"]
    if "batchfile" in new_options:
        # if sessions and batchfile both provide a file
        if sessions is not None and ".txt" in sessions:
            print(
                "ERROR: It seems like you passed the batchfile both through the sessions and the batchfile parameters!"
            )
            exit(1)
        elif sessions is not None:
            # did we provide a list of sessions in sessionsids as well
            if "sessionids" in new_options:
                print(
                    "ERROR: It seems like you are passing a list of sessions both through the sessions parameter and through the sessionids parameter!"
                )
                exit(1)
            # remap so session are sessionids and batchfile is sessions
            else:
                new_options["sessionids"] = new_options["sessions"]
                new_options["sessions"] = new_options["batchfile"]
                del new_options["batchfile"]
        else:
            new_options["sessions"] = new_options["batchfile"]
            del new_options["batchfile"]

    if deprecated:
        print("\nWARNING: Use of deprecated parameters!")
        print("         The following parameters are no longer used:")
        for k in deprecated:
            print("         ... %s" % (k))

    # -> check new parameter values
    for k, v in new_options.items():
        if k in deprecated_values:
            if v in deprecated_values[k]:
                new_options[k] = deprecated_values[k][v]
                newvalues.append([k, v, deprecated_values[k][v]])

    if newvalues:
        print("\nWARNING: Use of deprecated parameter value(s)!")
        print("       The following parameter values have changed:")
        for k, v, n in newvalues:
            print("         ... %s (%s) is now %s!" % (str(v), k, n))
        print(
            "         Please correct the listed parameter values in command line or batch file!"
        )

    # -> warn if some parameter values might be deprecated
    for k, v in new_options.items():
        if k in towarn_parameters:
            # search string
            s = towarn_parameters[k][0]
            if s in v:
                # warning message
                msg = towarn_parameters[k][1]
                print("\nWARNING: %s\n" % msg)

    return new_options


# ==============================================================================
#                                                IMPUTING UNSPECIFIED PARAMETERS
#


def impute_parameters(options, command):
    """
    ``impute_parameters(options, command)``

    Checks if parameters are not specified and assigns them the value of another
    relevant parameter.
    """

    for target_option, source_option in to_impute:
        if options[target_option] is None:
            options[target_option] = options[source_option]

    return options


# ==============================================================================
#                                                               EXTRA PARAMETERS
#

extra_parameters = ['batchfile', 'sessions', 'sessionids', 'filter', 'sessionid', 'scheduler', 'parelements', 'scheduler_environment', 'scheduler_workdir', 'scheduler_sleep', 'nprocess', 'logfolder', 'basefolder', 'sessionsfolder', 'sperlist', 'runinpar', 'ignore', 'bash', 'existing_study']


# ==============================================================================
#                                                SKIP LOGGING FOR THESE COMMANDS
#

logskip_commands = [
    "batch_tag2namekey",
    "check_deprecated_commands",
    "get_sessions_for_slurm_array",
]


# Add information from in extensions
extra_parameters += extensions.compile_list("extra_parameters")
logskip_commands += extensions.compile_list("logskip_commands")
