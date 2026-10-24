#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``folders.py``

The layout of a QuNex study, in one place: where its sessions, subjects and
processing folders are, and how a session file records a session's folders.

The study folder is the root everything else is found from. A run names it
with ``--studyfolder``, and its sessions folder is then the study's
``sessions`` folder -- unless ``--sessionsfolder`` names another one, which
always wins. A run that names only a sessions folder is in the study that
folder is in.

A session file -- and a batch file, which is a header followed by session
files -- records a session's folders (``dicom``, ``raw_data``, ``data``,
``hcp``, ``bids``, ``hcpls``, ``nhp``) relative to the session's own folder,
so a study can be moved, copied or mounted somewhere else without being
edited. A value that is absolute, as every value written before was, is used
as it is.

Where a run logs is part of the layout as well, and :func:`run_folders` is the
one place that decides it: for ``gmri`` and every command it runs, for
``run_recipe`` called on its own, for ``bin/qunex_container`` on the host,
through its copy of this module, and for ``bin/qunex.sh`` through
``gmri log_folder``. :func:`path_base` is the folder a run takes its relative
paths from, and ``general/placement.py`` enters it. A run is filed under its
command's current name, so the table of renamed commands
(``DEPRECATED_COMMANDS``, which ``commands_support`` takes) is kept here too.

Imports nothing from QuNex, so that anything in the tree can import it, and
nothing beyond the standard library: ``qunex build_qx_container`` splices this
module into the container launcher, which runs in the host python, and
``tests/test_container_drift.py`` keeps the copy current.
"""

import os
import re
from collections import namedtuple

SESSIONS = "sessions"
SUBJECTS = "subjects"
PROCESSING = "processing"

# what marks a folder as the root of a study (`.mnapstudy` before QuNex)
STUDY_MARKERS = (".qunexstudy", ".mnapstudy")

# the fields of a session record that name one of the session's folders
SESSION_FOLDER_FIELDS = ("dicom", "raw_data", "data", "hcp", "bids", "hcpls", "nhp")


# ------------------------------------------------------------------------------
#                                                                   study layout


def sessions_folder(studyfolder=None, sessionsfolder=None, default="."):
    """
    ``sessions_folder(studyfolder=None, sessionsfolder=None, default=".")``

    The sessions folder a command works on: ``sessionsfolder`` when it is
    given, else the ``sessions`` folder of ``studyfolder``, else ``default``.
    Returned as given, not made absolute.
    """
    if sessionsfolder:
        return sessionsfolder
    if studyfolder:
        return os.path.join(studyfolder, SESSIONS)
    return default


def study_folder(studyfolder=None, sessionsfolder=None):
    """
    ``study_folder(studyfolder=None, sessionsfolder=None)``

    The absolute path of the study folder: ``studyfolder`` when it is given,
    else the folder ``sessionsfolder`` is in, else None.
    """
    if studyfolder:
        return os.path.abspath(studyfolder)
    if sessionsfolder:
        return os.path.dirname(os.path.abspath(sessionsfolder))
    return None


def subjects_folder(studyfolder):
    """The study's subjects folder, where longitudinal results are kept."""
    return os.path.join(studyfolder, SUBJECTS)


def processing_folder(studyfolder):
    """The study's processing folder, where batch files and lists are kept."""
    return os.path.join(studyfolder, PROCESSING)


def find_study(path):
    """
    ``find_study(path)``

    The study ``path`` is in: the first folder from ``path`` upwards that
    carries a study marker, or None when there is none. ``path`` itself is
    tested first, so a command run from the root of a study is run inside it.
    """
    folder = os.path.abspath(path)
    while folder and folder != os.path.dirname(folder):
        if any(os.path.exists(os.path.join(folder, m)) for m in STUDY_MARKERS):
            return folder
        folder = os.path.dirname(folder)
    return None


# ------------------------------------------------------------------------------
#                                                   folders in a session record


def session_relative(path, session_folder):
    """
    ``session_relative(path, session_folder)``

    How a session file records ``path``: relative to ``session_folder`` when
    it is inside it, absolute when it is somewhere else -- a relative value
    is read back against the session folder, so it has to be one.
    """
    if not path:
        return path

    folder = os.path.abspath(session_folder)
    target = os.path.abspath(path)

    if target == folder or target.startswith(folder + os.sep):
        return os.path.relpath(target, folder)

    return target


def resolve_session_folders(record, session_folder):
    """
    ``resolve_session_folders(record, session_folder)``

    Makes the folders a session record names absolute, against the session's
    own folder. An absolute value, and one starting with ``~``, is left as it
    is. Changes the record in place and returns it.
    """
    for field in SESSION_FOLDER_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            continue
        value = value.strip()
        if os.path.isabs(value) or value.startswith("~"):
            continue
        record[field] = os.path.normpath(
            os.path.join(os.path.abspath(session_folder), value)
        )
    return record


def resolve_sessions_folders(sessions, sessionsfolder):
    """
    ``resolve_sessions_folders(sessions, sessionsfolder)``

    Makes the folders every session record names absolute, each against its
    session's folder -- the folder in ``sessionsfolder`` named after the
    session's id. A record without an id is left as it is. Changes the
    records in place and returns them.
    """
    for record in sessions or []:
        if isinstance(record, dict) and record.get("id"):
            resolve_session_folders(record, os.path.join(sessionsfolder, record["id"]))
    return sessions


# ------------------------------------------------------------------------------
#                                                               where a run logs
#
# a run keeps its logs in one folder -- its runlog, its comlogs, the output of
# the jobs it submits, the job scripts a launcher writes for it and the status
# records of a recipe -- decided once, by the entry point the run was started
# at, with `run_folders`; everything the run starts is handed that folder with
# `--logfolder` and uses it as it is, so nothing below the entry point decides
# again (`run_qc` alone keeps working files of its own, the scene scripts it
# writes and their output, in its `qclog` folder)
#
# the same call says which folder the run takes its relative paths from: the
# study it knows, once that study exists and unless the run creates it

# the folder of a study its runs log in, and the folder of the legacy layout
LOGS = "logs"
LEGACY_LOGS = os.path.join(PROCESSING, "logs")

# the folder under the home folder the runs outside any study log in
OUTSIDE_STUDY_LOGS = "qunex_logs"

# `--logfolder=legacy` names the legacy layout rather than a folder
LEGACY = "legacy"

# the log layouts, and the named values of the `outside_study` setting
LAYOUTS = ("default", "legacy", "nested")
OUTSIDE_STUDY = ("home", "cwd")

# the settings files the layout and `outside_study` are read from: the user's,
# accepted in exactly one of these places, and the study's own
USER_SETTINGS_PATHS = (
    "~/.qunex_settings.yaml",
    "~/qunex_settings.yaml",
    "~/qunex/qunex_settings.yaml",
    "~/.qunex/qunex_settings.yaml",
)
STUDY_SETTINGS_FILE = "qunex_settings.yaml"

# the stamp a run's folder, its runlog and its comlogs carry
TIMESTAMP = "%Y-%m-%d_%H.%M.%S.%f"

# the deprecated names of the parameters that place a run -- the part of
# `commands_support.deprecated_parameters` this rule reads, kept here because
# the container launcher can not import that module;
# `tests/test_log_placement.py` fails when the two disagree
FOLDER_ALIASES = {
    "basefolder": "sessionsfolder",
    "subjectsfolder": "sessionsfolder",
    "sfolder": "sourcefolder",
}

# the commands QuNex has renamed, and the names each had before:
# "new_command_name": ["deprecated_name1", "deprecated_name2", ...]. Kept here,
# rather than in `commands_support`, which takes it from here and adds the
# ones extensions declare, because the container launcher can not import that
# module and names a run after its command as QuNex does (`run_name`)
DEPRECATED_COMMANDS = {
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

# a deprecated name, in lower case, and the name it has now
_CURRENT_COMMANDS = {
    old.lower(): new for new, olds in DEPRECATED_COMMANDS.items() for old in olds
}


# where a run that names no study looks for the one it is in, in this order,
# before it looks at the current folder
STUDY_HINTS = ("logfolder", "sourcefolder", "folder", "reference")

# every parameter that places a run
PLACEMENT_PARAMETERS = ("studyfolder", "sessionsfolder") + STUDY_HINTS

# how a recipe says that a parameter is not to be inherited
UNSET_PARAMETERS = "unset_parameters"

# a `{{$NAME}}` label in a recipe file, found as `run_recipe` finds it: from
# `{{` to the first `}}` after it, across a line break as well
_LABEL = re.compile(r"\{\{.*?\}\}", re.S)

# what `run_folders` returns: the name the run is filed under; its study, and
# whether the study is known (named, rather than found by its marker); the
# folder it takes its relative paths from, None for the current folder; its
# log folder; and the settings the `settings` callable returned for the study
Placement = namedtuple("Placement", "name studyfolder known base logfolder settings")

# the two settings that place a run's logs
LogPlacement = namedtuple("LogPlacement", "layout outside_study")


class PlacementError(ValueError):
    """A run that can not be placed: an unset label, or an invalid setting."""


def current_command(command):
    """
    ``current_command(command)``

    The name `command` has now: a deprecated name of a QuNex command, in any
    case, is the name it was renamed to (``DEPRECATED_COMMANDS``), as
    ``commands_support.check_deprecated_commands`` maps it; any other is
    returned as it is.
    """
    if not isinstance(command, str):
        return command
    return _CURRENT_COMMANDS.get(command.lower(), command)


def run_name(command, args=None):
    """
    ``run_name(command, args=None)``

    The name a run's log folder and runlog are filed under: the command, by
    the name it has now (:func:`current_command`), and for ``run_recipe`` the
    recipe as well -- ``run_recipe_<recipe>``, a path separator in the
    recipe's name read as ``_``, or ``run_recipe_steps`` for a run of
    ``--steps`` without a recipe file.
    """
    command = current_command(command)
    if command != "run_recipe":
        return command

    args = args or {}
    if not args.get("recipe_file"):
        return "run_recipe_steps"
    if args.get("recipe"):
        return "run_recipe_%s" % str(args["recipe"]).replace(os.sep, "_")
    return command


def recipe_parameters(recipe_data, recipe):
    """
    ``recipe_parameters(recipe_data, recipe)``

    The parameters a parsed recipe file states for every step of ``recipe``:
    its ``global_parameters``, overridden by the recipe's own ``parameters``,
    less the ones the recipe unsets. Labels are left as they are written. An
    empty dict when the file holds no such recipe, and a section that is not a
    mapping states nothing -- `run_recipe` reports both, and validates how an
    unset is spelled.
    """
    recipes = recipe_data.get("recipes") if isinstance(recipe_data, dict) else None
    if not isinstance(recipes, dict) or not isinstance(recipes.get(recipe), dict):
        return {}

    parameters = recipe_data.get("global_parameters")
    parameters = dict(parameters) if isinstance(parameters, dict) else {}
    own = recipes[recipe].get("parameters")
    own = dict(own) if isinstance(own, dict) else {}

    stated = own.pop(UNSET_PARAMETERS, None)
    if isinstance(stated, str):
        unset = stated.split(",")
    elif isinstance(stated, (list, tuple)):
        unset = [str(name) for name in stated]
    else:
        unset = []
    for key in [key for key in own if isinstance(key, str) and key.startswith("-")]:
        own.pop(key)
        unset.append(key[1:])

    parameters.update(own)
    for name in unset:
        parameters.pop(name.strip(), None)
    return parameters


def inject_labels(value, environ=None):
    """
    ``inject_labels(value, environ=None)``

    ``value`` with every ``{{$NAME}}`` label of a recipe file replaced by
    ``NAME`` from ``environ``, the environment unless another is given.
    Anything that is not a string holding a label is returned as it is.
    Raises PlacementError on a label ``environ`` does not hold: a recipe can
    not be run half resolved.
    """
    if not isinstance(value, str) or "{{" not in value or "}}" not in value:
        return value

    environ = os.environ if environ is None else environ
    for label in _LABEL.findall(value):
        name = label.replace("{", "").replace("}", "")
        if not name.startswith("$") or name[1:] not in environ:
            raise PlacementError(
                "Cannot inject values marked with double curly braces in the "
                "recipe. Label [%s] not found in system environment variables." % label
            )
        value = value.replace(label, environ[name[1:]])
    return value


def _canonical(parameters):
    """
    `parameters` under the names they have now, remapped as
    `commands_support.check_deprecated_parameters` remaps them: a later key
    wins over an earlier one, and a deprecated name with no value is dropped
    rather than taking the place of the name it has now.
    """
    canonical = {}
    for key, value in (parameters or {}).items():
        if key in FOLDER_ALIASES:
            if not value:
                continue
            key = FOLDER_ALIASES[key]
        canonical[key] = value
    return canonical


def recipe_placement(recipe_data, recipe, environ=None):
    """
    ``recipe_placement(recipe_data, recipe, environ=None)``

    The recipe file's tier of the parameters that place a `run_recipe` run:
    those of :func:`recipe_parameters` that are among `PLACEMENT_PARAMETERS`,
    under the names they have now, with their labels injected from
    ``environ`` -- the environment unless another is given. QuNex and the
    container launcher read the tier with it; the launcher on the host may
    not hold every variable the run will.

    Returns:
        ``(parameters, unresolved)``: the parameters, and a ``(name, message)``
        pair for each one with a label ``environ`` does not hold. Such a
        parameter is left out rather than raised on, so that the caller can
        say so and place the run by the other tiers.
    """
    parameters, unresolved = {}, []
    for key, value in _canonical(recipe_parameters(recipe_data, recipe)).items():
        if key not in PLACEMENT_PARAMETERS:
            continue
        try:
            parameters[key] = inject_labels(value, environ)
        except PlacementError as e:
            unresolved.append((key, str(e)))
    return parameters, unresolved


def placement_parameters(*tiers):
    """
    ``placement_parameters(*tiers)``

    The parameters that place a run, each from the first tier that states it.
    The tiers are given highest first -- the command line, the recipe file of
    a `run_recipe` run, the batch file header -- and a deprecated name counts
    as the name it has now. An empty value, as from a recipe variable that
    expanded to nothing, is not stated, and ``$NAME`` and ``~`` are expanded,
    as `process.merge_options` and `batch_io.run_path` expand them, so that
    the folders a run logs to are the ones its command works in.
    """
    stated = {}
    for tier in tiers:
        for key, value in _canonical(tier).items():
            if key in stated or key not in PLACEMENT_PARAMETERS:
                continue
            if not isinstance(value, str) or not value.strip():
                continue
            stated[key] = os.path.expanduser(os.path.expandvars(value.strip()))
    return stated


def _absolute(path, base):
    """`path` made absolute against `base`, and normalised."""
    return os.path.normpath(os.path.join(base, path))


def run_study(stated, cwd=None):
    """
    ``run_study(stated, cwd=None)``

    The study a run is in, and whether it is known. The study is known when
    the run names it, or names a sessions folder, which is in its study.
    Otherwise it is the study marked by `.qunexstudy` at or above the first of
    `STUDY_HINTS` the run states that is in one, else at or above the current
    folder; else there is none and the run is outside a study. Takes what
    `placement_parameters` returns.
    """
    cwd = os.path.abspath(cwd or os.getcwd())

    if stated.get("studyfolder"):
        return _absolute(stated["studyfolder"], cwd), True
    if stated.get("sessionsfolder"):
        return os.path.dirname(_absolute(stated["sessionsfolder"], cwd)), True

    for hint in STUDY_HINTS:
        value = stated.get(hint)
        if value and value != LEGACY:
            study = find_study(_absolute(value, cwd))
            if study:
                return study, False

    return find_study(cwd), False


def study_exists(folder):
    """
    ``study_exists(folder)``

    Whether the study ``folder`` exists: a folder holding something other than
    QuNex's logs. A run's logs are written into the study it names before the
    command runs, so a folder holding nothing but those logs -- ``logs``, or
    ``processing`` with nothing but ``logs`` in it -- is a study that does not
    exist yet. A second run, a job the run submitted, and a recipe's external
    step then decide as the first run did.
    """
    if not folder:
        return False
    try:
        entries = set(os.listdir(folder)) - {LOGS}
    except OSError:
        return False
    if entries != {PROCESSING}:
        return bool(entries)
    try:
        return bool(set(os.listdir(os.path.join(folder, PROCESSING))) - {LOGS})
    except OSError:
        # a `processing` that can not be listed is not one the logs made
        return True


def path_base(study, known, creating=False):
    """
    ``path_base(study, known, creating=False)``

    The folder a run takes its relative paths from: the study it knows -- the
    one it names, or the one a sessions folder it names is in -- once that
    study exists (:func:`study_exists`), unless the run's command creates it.
    None means the current folder, which is where a run that names neither
    folder takes them from, even inside a study its marker shows.
    """
    if study and known and not creating and study_exists(study):
        return study
    return None


def outside_folder(outside_study="home", cwd=None, home=None):
    """
    ``outside_folder(outside_study="home", cwd=None, home=None)``

    The folder the runs outside any study log in, by the ``outside_study``
    setting: ``home`` is ``~/qunex_logs``, ``cwd`` the current folder, and
    anything else a path -- taken against the current folder when it is
    relative, there being no study to take it against.
    """
    cwd = os.path.abspath(cwd or os.getcwd())

    if not outside_study or outside_study == "home":
        return os.path.join(home or os.path.expanduser("~"), OUTSIDE_STUDY_LOGS)
    if outside_study == "cwd":
        return cwd
    if home and (outside_study == "~" or outside_study.startswith("~/")):
        outside_study = home + outside_study[1:]
    return _absolute(os.path.expanduser(outside_study), cwd)


def log_folder(
    name,
    timestamp,
    stated,
    study,
    known,
    layout="default",
    outside_study="home",
    cwd=None,
    home=None,
    creating=False,
):
    """
    ``log_folder(name, timestamp, stated, study, known, layout="default", outside_study="home", cwd=None, home=None, creating=False)``

    The folder a run logs in. A ``logfolder`` the run states is that folder;
    a relative one is taken from the folder the run takes every relative path
    from -- :func:`path_base`, else the current folder. Otherwise the run gets
    a folder of its own, ``<timestamp>_<name>``: in the study's ``logs``
    folder, or -- under ``--logfolder=legacy`` or ``layout: legacy`` -- the
    study's ``processing/logs``, which every run of the study shares. A run
    outside a study gets its folder in the ``outside_study`` folder, whatever
    the layout: there is no study to collect it in.
    """
    named = (stated or {}).get("logfolder")
    if named and named != LEGACY:
        base = path_base(study, known, creating)
        return _absolute(named, base or os.path.abspath(cwd or os.getcwd()))

    if study:
        if named == LEGACY or layout == LEGACY:
            return os.path.join(study, LEGACY_LOGS)
        return os.path.join(study, LOGS, "%s_%s" % (timestamp, name))

    return os.path.join(
        outside_folder(outside_study, cwd, home), "%s_%s" % (timestamp, name)
    )


def user_settings_files(home=None):
    """The user settings files that exist, of the places one is accepted in."""
    home = home or os.path.expanduser("~")
    paths = [os.path.join(home, path[2:]) for path in USER_SETTINGS_PATHS]
    return [path for path in paths if os.path.isfile(path)]


def placement_settings(*sections):
    """
    ``placement_settings(*sections)``

    The ``layout`` and ``outside_study`` the ``logging:`` sections of the
    settings files state, each later section overriding the earlier ones key
    by key -- the user's first, then the study's. Raises PlacementError on a
    section that is not a mapping, and on a value QuNex does not take.
    """
    merged = {}
    for section in sections:
        if section and not isinstance(section, dict):
            raise PlacementError(
                "logging must be a mapping of settings, got: %r" % (section,)
            )
        merged.update(section or {})

    layout = merged.get("layout", "default")
    outside_study = merged.get("outside_study", "home")
    if layout not in LAYOUTS:
        raise PlacementError(
            "logging.layout must be one of [%s], got: %r" % (", ".join(LAYOUTS), layout)
        )
    if not isinstance(outside_study, str):
        raise PlacementError(
            "logging.outside_study must be one of [%s] or a path, got: %r"
            % (", ".join(OUTSIDE_STUDY), outside_study)
        )
    return LogPlacement(layout, outside_study)


def run_folders(
    name, tiers, timestamp, settings=None, cwd=None, home=None, creating=False
):
    """
    ``run_folders(name, tiers, timestamp, settings=None, cwd=None, home=None, creating=False)``

    Where a QuNex run is, where it takes its relative paths from, and where it
    logs: the one rule every entry point follows -- `gmri` for every command
    it runs, `run_recipe` called on its own, `qunex_container` on the host
    through its copy of this module, and `bin/qunex.sh` through
    `gmri log_folder`.

    Parameters:
        name: what the run is filed under, from :func:`run_name`.
        tiers: the dictionaries that state the run's parameters, highest
            first: the command line, the recipe file's run wide parameters
            for `run_recipe`, the batch file header.
        timestamp: the run's stamp, as :data:`TIMESTAMP` formats it.
        settings: a callable given the study (or None) that returns the
            resolved logging settings -- anything with ``layout`` and
            ``outside_study`` -- or None for the defaults.
        cwd, home: the current and the home folder, for tests.
        creating: whether the run's command creates the study it names
            (``create_study``, ``manage_study``, ``copy_study``), and so takes
            no relative path from it.

    Returns:
        a :data:`Placement`.
    """
    stated = placement_parameters(*tiers)
    study, known = run_study(stated, cwd)
    base = path_base(study, known, creating)
    resolved = settings(study) if settings else LogPlacement("default", "home")
    logfolder = log_folder(
        name,
        timestamp,
        stated,
        study,
        known,
        resolved.layout,
        resolved.outside_study,
        cwd,
        home,
        creating,
    )
    return Placement(name, study, known, base, logfolder, resolved)
