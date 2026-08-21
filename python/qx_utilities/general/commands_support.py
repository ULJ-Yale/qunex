#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``commands_support.py``

Helper code for perarations of commands and their parameters
"""

import fnmatch
import os
import re

from qx_utilities.general import exceptions as ge
from qx_utilities.general import extensions
from qx_utilities.general.log import INDENT

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
    "compute_bold_fc": [
        "BOLDcomputeFC",
        "bold_compute_fc",
        "compute_fc_bold",
        "fc_compute_wrapper",
        "computeBOLDfc",
    ],
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
    "extract_roi": ["extractROI", "ROIExtract", "roi_extract"],
    "matlab_help": ["matlabHelp"],
    "gmri_function": ["gmriFunction"],
    "organize_dicom": ["organizeDicom"],
    "dwi_pre_tractography": ["DWIpreTractography", "pretractographyDense"],
    "aws_hcp_sync": ["AWSHCPsync"],
    "map_hcp_files": ["mapHCPFiles"],
    "auto_ptx": ["autoPtx"],
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
# @register_command(
#     description="Checks for deprecated commands, remaps deprecated ones, and notifies the user.",
#     type="utility")
def check_deprecated_commands(command):
    """
    ``check_deprecated_commands command``

    Check for deprecated commands, print a warning if needed and
    return the updated command name.

    ..  qx_command:
        type: utility

    Parameters:
        --command (str):
        The command to check for deprecation.

    Returns:
        --new_command (str):
        The updated command name if it was deprecated, otherwise the original command name.
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
        "sessions": ["export_hcp"],
        "default": "sessionid",
    },
    "sbjroi": "sessionroi",
    "subjectf": "sessionf",
    "hcp_bold_sequencetype": None,
    "hcp_biascorrect_t1w": None,
    "args": "palm_args",
    "TR": "tr",
    "PEdir": "pedir",
    "sequenceinfo": "add_json_info",
    "hcp_icafix_traindata": "hcp_icafix_model",
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
#                                                     SESSION PARAMETER ENCODING
#
# QuNex used to encode "which batch file, which sessions" as `sessions=<path to
# the batch file>` plus `sessionids=<ids>`. The canonical encoding is
# `batchfile=<path>` plus `sessions=<ids>`, and the legacy one is mapped onto it
# here - once, for every entry point.
#
# The legacy spelling is a warning rather than an error because run_turnkey.sh
# hard-codes it in ~30 internal calls. Setting the constant below to True turns
# it into an error; that is the whole of the change, and it is due when
# run_turnkey is dropped.
SESSIONS_AS_BATCHFILE_IS_ERROR = False


def is_batchfile_path(sessions):
    """
    ``is_batchfile_path(sessions)``

    Checks whether a `sessions` value is a path to a batch file - the legacy
    spelling of `batchfile` - rather than a specification of sessions.

    A session specification is a comma, pipe or space separated list of session
    ids or globs, or a single `*.list` file. A path to a batch file is what is
    left: a single item, not a `*.list` file, that has either a directory
    component or a file extension.
    """

    if not isinstance(sessions, str) or not sessions.strip():
        return False

    sessions = sessions.strip()

    if len(sessions.split()) > 1 or "," in sessions or "|" in sessions:
        return False

    extension = os.path.splitext(sessions)[1].lower()
    if extension == ".list":
        return False

    return os.sep in sessions or extension != ""


def normalize_session_parameters(options, command):
    """
    ``normalize_session_parameters(options, command)``

    Maps the legacy `sessions=<batch file>` / `sessionids=<ids>` encoding onto
    the canonical `batchfile=<batch file>` / `sessions=<ids>` one, warning about
    each of the two legacy spellings, and returns the updated options.

    An empty value is treated as no value at all - the bash entry points pass
    every parameter they know of, set or not.
    """

    sessions = options.get("sessions")
    sessions = sessions.strip() if isinstance(sessions, str) else sessions

    # -- a batch file passed through sessions
    if is_batchfile_path(sessions):
        batchfile = sessions
        sessions = None

        if options.get("batchfile"):
            raise ge.CommandError(
                command,
                "Duplicate batch file",
                "The batch file was passed both through the sessions and through the batchfile parameter!",
                "Please pass it through batchfile only!",
            )

        if SESSIONS_AS_BATCHFILE_IS_ERROR:
            raise ge.CommandError(
                command,
                "Deprecated parameter use",
                "The sessions parameter no longer takes a path to a batch file [%s]!"
                % (batchfile),
                "Please use the batchfile parameter instead!",
            )

        print(
            "\nWARNING: Passing the batch file through the sessions parameter is deprecated!"
        )
        print("         Please use --batchfile='%s' instead." % (batchfile))

        options["batchfile"] = batchfile
        del options["sessions"]

    # -- sessionids is a deprecated alias of sessions
    if "sessionids" in options:
        sessionids = options.pop("sessionids")
        sessionids = sessionids.strip() if isinstance(sessionids, str) else sessionids

        if sessionids:
            if sessions and sessions != sessionids:
                raise ge.CommandError(
                    command,
                    "Duplicate session specification",
                    "Sessions were specified both through the sessions and through the sessionids parameter!",
                    "Please specify them through sessions only!",
                )

            print(
                "\nWARNING: The sessionids parameter is deprecated, please use sessions instead!"
            )
            options["sessions"] = sessionids

    return options


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

    # -> map the legacy batch file / sessions encoding onto the canonical one
    new_options = normalize_session_parameters(new_options, command)

    # custom remapping for log: it used to answer two questions -- whether to
    # keep a comlog and where to put it. The destinations moved to
    # comlog_folders, retention kept the name. Neither the declarative
    # mechanisms above can express a value moving to another parameter.
    if "log" in new_options and "comlog_folders" not in new_options:
        folders = [
            e.strip()
            for e in re.split(r" +|\||, *", str(new_options["log"]))
            if e.strip() and e.strip() not in ["keep", "remove"]
        ]
        if folders:
            print("\nWARNING: Use of deprecated parameter value(s)!")
            print(
                "         --log no longer says where a comlog goes, only whether it\n"
                "         is kept ('keep' or 'remove'). The destinations [%s] were\n"
                "         read as --comlog_folders=%s; please pass them that way."
                % (", ".join(folders), ",".join(folders))
            )
            new_options["comlog_folders"] = ",".join(folders)
            new_options["log"] = "keep"

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
#                                                   THE THREADS A COMMAND MAY USE
#
MAX_OMP_THREADS = 8


def set_omp_threads(options):
    """
    ``set_omp_threads(options)``

    Sets `OMP_NUM_THREADS` for the command about to be run: `--omp_threads` if
    the run states one, otherwise the cores available to this process shared
    between the parallel jobs it was asked for, at least one and at most eight.

    An environment that already states it is left alone. `bin/qunex.sh` sets
    the same variable the same way before it hands over, so a run started
    there arrives with it set and this changes nothing; a run started at
    `gmri` - a step of a recipe, a scheduler job, a call from a script - used
    to get the machine's default and oversubscribe the node.

    Parameters:
        --options   The merged options, from `process.merge_options`.

    Returns:
        The value it set, or None when the environment already stated one.
    """
    if options.get("omp_threads"):
        threads = int(options["omp_threads"])
    elif os.environ.get("OMP_NUM_THREADS"):
        return None
    else:
        # the cores this process may actually run on, which is what `nproc`
        # reports and what a scheduler restricts a job to
        cores = (
            len(os.sched_getaffinity(0))
            if hasattr(os, "sched_getaffinity")
            else os.cpu_count() or 1
        )
        parallel = int(options.get("parsessions", 1)) * int(
            options.get("parelements", 1)
        )
        threads = min(MAX_OMP_THREADS, max(1, cores // max(1, parallel)))

    os.environ["OMP_NUM_THREADS"] = str(threads)
    return threads


# ==============================================================================
#                                                          PARAMETER PROVENANCE
#
PER_SESSION = "batch file (session)"
RECIPE_RUN = "recipe run"

# How a recipe tells the step it starts which of the parameters on its command
# line came from the recipe: the names, comma separated, in the step's
# environment. A command line carries values and not the tier they came from,
# and the step is a process of its own.
RECIPE_PARAMETERS = "QX_RECIPE_PARAMETERS"

# The tiers that state parameters for a run rather than for one command: a
# batch file's header, and everything a recipe states for all of its steps --
# its global and recipe level parameters and the command line `run_recipe`
# itself was given. A value of theirs that a command cannot take was meant for
# another command of the same run, so it is dropped without a word. One
# written against the command itself is a mistake, and is named.
RUN_WIDE_SOURCES = ("batch file", PER_SESSION, RECIPE_RUN)

# ==============================================================================
#                                            NOT TAKING WHAT THE BATCH FILE SAYS
#
# A batch file states parameters for every command of a study, and since the
# header reaches every command class, a name it states can land somewhere its
# author did not have in mind -- `targetfile` is declared by four commands that
# write four different files. These say "not from there", one per batch tier,
# and they are run level parameters, so they can be written on the command line
# and at every level of a recipe.
UNSET_BATCH_HEADER = "unset_batch_header_parameters"
UNSET_BATCH_SESSION = "unset_batch_session_parameters"


def unset_patterns(stated):
    """
    ``unset_patterns(stated)``

    The patterns an unset states: a name, a comma separated list of them, or an
    array -- the forms a recipe's `unset_parameters` already takes, so there is
    one convention rather than two. An empty list states nothing, which is how
    a step opts back in under a run wide `all`.
    """
    if stated is None:
        return []
    if isinstance(stated, str):
        stated = stated.split(",")
    return [str(pattern).strip() for pattern in stated if str(pattern).strip()]


def is_unset(name, patterns):
    """
    ``is_unset(name, patterns)``

    Whether any of `patterns` unsets `name`. A pattern is a parameter name, a
    glob over parameter names (`hcp_*`), `*`, or `all` -- the last being the
    spelling QuNex uses for "every one of them" elsewhere, and free here since
    no command declares a parameter of that name.

    `fnmatchcase` rather than `fnmatch`, as in `batch_io`: the answer must not
    depend on the operating system. `_` is not a metacharacter, so `hcp_*`
    matches what it looks like it matches.
    """
    return any(
        pattern in ("all", "*") or name == pattern or fnmatch.fnmatchcase(name, pattern)
        for pattern in patterns
    )


def without_unset(options, patterns):
    """
    ``without_unset(options, patterns)``

    The options left once the patterns have taken out what they name, and the
    names they took. The names are returned because a pattern is not a list: a
    run has to be able to say what `hcp_*` removed on the day it ran, rather
    than leaving a reader to work it out from the release it ran on.
    """
    if not options or not patterns:
        return options, []

    unset = sorted(key for key in options if is_unset(key, patterns))

    return {key: value for key, value in options.items() if key not in unset}, unset


def declared_parameters(qx_command):
    """
    ``declared_parameters(qx_command)``

    The names a command declares: its signature arguments and its documented
    options. `qx_command.has_arg` answers for the signature alone, which is the
    whole story for a python command and none of it for a matlab or a bash one -
    their parameters are documented ones and live in `options`.
    """
    return {arg.name for arg in qx_command.args} | {
        option.name for option in qx_command.options
    }


def update_options(session, options, sources=None):
    """
    ``update_options(session, options, sources=None)``

    Returns a copy of the options with the parameters a batch file states for
    this session alone - the keys it prefixes with `_` or `--` - applied over
    them, and a copy of the sources recording those keys as having come from
    the batch file's entry for the session.

    What `unset_batch_session_parameters` names is not applied. The run states
    it and it travels in the options, so this is the only place that has to
    know about it - and it is the only place this tier is applied, `gp.run`
    being its one caller, so a processing command is the only kind that ever
    sees this tier at all.
    """
    soptions = dict(options)
    ssources = dict(sources or {})
    patterns = unset_patterns(options.get(UNSET_BATCH_SESSION))

    for key, value in session.items():
        if key.startswith("_"):
            key = key[1:]
        elif key.startswith("--"):
            key = key[2:]
        else:
            continue

        if is_unset(key, patterns):
            continue

        soptions[key] = value
        ssources[key] = PER_SESSION

    return soptions, ssources


def select_parameters(options, sources, qx_command):
    """
    ``select_parameters(options, sources, qx_command)``

    Narrows the merged options to the parameters the registry says the command
    accepts, and names the ones it does not.

    Fill, never override: only values somebody stated are returned, so the
    command keeps its own defaults for everything nobody named, and a caller
    that layers the command line back over the result gets a command line that
    always wins.

    Parameters:
        --options       The parameters to narrow - what the tiers stated, from
                        `process.merge_options`, or a recipe step's own.
        --sources       Where each of them came from.
        --qx_command    The registry entry of the command to be run.

    Returns:
        The parameters the command accepts, and the names of those it does
        not. Named are only the ones stated for this command: a run wide tier
        states parameters for every command in the run, and the run level
        parameters steer the run rather than the command.
    """
    declared = declared_parameters(qx_command)

    accepted, dropped = {}, []
    for key, value in options.items():
        source = sources.get(key, "default")

        if source == "default":
            continue
        elif key in declared:
            accepted[key] = value
        elif key not in extra_parameters and source not in RUN_WIDE_SOURCES:
            dropped.append(key)

    return accepted, dropped


def report_origin(qx_command):
    """
    ``report_origin(qx_command)``

    Where the command being run comes from, when that is not the core suite.

    A command an extension provides is otherwise indistinguishable in the
    run's own record from a core one -- the call echo, the parameter table
    and the runlog all name the command, and an extension command standing
    in for a core command of the same name has the same name. A study that
    behaves differently from another then has nothing in its logs to say why.

    Parameters:
        --qx_command    The registry entry of the command to be run.

    Returns:
        The line to head the banner with, or an empty string for a core
        command.
    """
    origin = getattr(qx_command, "origin", None) or "core"
    if origin == "core":
        return ""

    extension = origin.split(":", 1)[1] if ":" in origin else origin
    note = "\n---> Command %s is provided by extension %s" % (qx_command.name, extension)

    replaced = getattr(qx_command, "overrides", None)
    if replaced:
        note += ", replacing the %s command of the same name" % replaced

    return note + "\n"


def report_parameters(qx_command, options, sources, session=None):
    """
    ``report_parameters(qx_command, options, sources, session=None)``

    Renders the parameters a command is about to be run with, each one next to
    where its value came from. Written before the command runs, unconditionally,
    so that a run that does something unexpected says why in its own first
    lines.

    Reported are the parameters the command declares - its signature arguments
    and its documented options. A command that declares none that this run has
    a value for has nothing to narrow by, and reports what was specified
    instead: the run's ~450 defaults say nothing about a command that does not
    take them.

    Parameters:
        --qx_command    The registry entry of the command to be run.
        --options       The merged options, from `process.merge_options`.
        --sources       Where each of them came from, from the same call.
        --session       The session, when reporting the per session tier. Only
                        the parameters that tier states are then reported, the
                        rest having been reported for the run as a whole.

    Returns:
        The rendered table.
    """
    if session:
        reported = sorted(k for k in sources if sources[k] == PER_SESSION)
    else:
        declared = declared_parameters(qx_command)
        reported = sorted(k for k in options if k in declared)

        if not reported:
            reported = sorted(k for k in options if sources.get(k) != "default")

    rows = [(k, str(options[k]), sources.get(k, "default")) for k in reported]

    title = "%s\n---> Parameters for %s%s\n\n" % (
        # only once per run: the per session tier reports under a run that has
        # already said where the command comes from
        "" if session else report_origin(qx_command),
        qx_command.name,
        " on session %s" % session["id"] if session else "",
    )

    def table(rows):
        if not rows:
            return title + INDENT + "(none)\n"

        # the value goes last, and is the only column not padded: a path can
        # be a hundred characters wide, and a source read off the far side of
        # one is a source nobody reads
        names = max(len(name) for name, _, _ in rows + [("parameter", "", "")])
        origins = max(len(source) for _, _, source in rows + [("", "", "source")])
        values = max(len(value) for _, value, _ in rows + [("", "value", "")])
        rule = INDENT + "-" * (names + origins + values + 6) + "\n"

        text = title + "%s%-*s   %-*s   %s\n%s" % (
            INDENT,
            names,
            "parameter",
            origins,
            "source",
            "value",
            rule,
        )
        for name, value, source in rows:
            text += "%s%-*s   %-*s   %s\n" % (INDENT, names, name, origins, source, value)

        # closed at the bottom as well as the top: a long run's output scrolls,
        # and a table that ends without a line ends wherever the reader stops
        return text + rule

    return table(rows)


def report_unset(unset_from_header, options):
    """
    ``report_unset(unset_from_header, options)``

    What the run was told not to take from the batch file, rendered under the
    parameter table. An unset value never reaches the options, so the table
    says what applied and this says what did not.

    The header's removals are **named**, not counted: a pattern is not a list,
    and `hcp_*` removes whatever this study's header happens to state on the
    day the run happens. The per session tier can only be reported as the
    patterns themselves -- what they remove differs from one session to the
    next, and each session's own table shows the result.

    Parameters:
        --unset_from_header     The header keys an unset took out, from
                                `without_unset`.
        --options               The merged options, read for the per session
                                patterns.

    Returns:
        The rendered lines, or an empty string when the run unset nothing.
    """
    text = ""

    if unset_from_header:
        text += "\n%snot taken from the batch file header: %s\n" % (
            INDENT,
            ", ".join(unset_from_header),
        )

    per_session = unset_patterns(options.get(UNSET_BATCH_SESSION))
    if per_session:
        text += "\n%snot taken from any session's own entry: %s\n" % (
            INDENT,
            ", ".join(per_session),
        )

    return text


# ==============================================================================
#                                                               EXTRA PARAMETERS
#
extra_parameters = [
    "batchfile",
    "sessions",
    "sessionids",
    "filter",
    "sessionid",
    "scheduler",
    "parelements",
    "parsessions",
    "parjobs",
    "scheduler_environment",
    "scheduler_workdir",
    "scheduler_sleep",
    "nprocess",
    "omp_threads",
    "logging",
    "keep_comlogs",
    "runlog_content",
    "logfolder",
    "logstatus",
    "basefolder",
    "sessionsfolder",
    "sperlist",
    "runinpar",
    "ignore",
    "bash",
    "existing_study",
    UNSET_BATCH_HEADER,
    UNSET_BATCH_SESSION,
]


# ==============================================================================
#                                                SKIP LOGGING FOR THESE COMMANDS
#
# Legacy fallback, consulted by `general.log.resolve_logging` only for commands
# that do not state `logging:` in their `.. qx_command:` block. Annotate the
# command instead of extending this list; it goes away once all three are.
logskip_commands = [
    "batch_tag2namekey",
    "check_deprecated_commands",
    "list_sessions",
    "get_sessions_for_slurm_array",
]

# Add information from in extensions
extra_parameters += extensions.compile_list("extra_parameters")
logskip_commands += extensions.compile_list("logskip_commands")
