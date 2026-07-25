#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_utils.py``

Helpers shared by more than one HCP processing command: per-session report
boilerplate, option checks, gradient distortion coefficient resolution, the
non-human primate template configuration, and the executors that several
denoising commands drive.

Path resolution lives in ``hcp_paths``; the structured runlog lives in
``general.log``.
"""

import json
import os
import os.path
import re
import traceback
from datetime import datetime

import nibabel as nib

import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.snapshots as gs
import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog
from qx_utilities.hcp.hcp_paths import get_hcp_paths


# separator used to frame the per-session command reports
REPORT_RULE = "------------------------------------------------------------"


# timestamp format used in the per-session command reports
REPORT_TIME = "%A, %d. %B %Y %H:%M:%S"


def session_report_header(sinfo: dict) -> str:
    """
    Build the opening lines of a per-session report: the rule, the session id and
    the start timestamp.

    Commands whose "running ..." line does not follow the common shape build on
    this directly; the rest go through :func:`start_session_report`.

    Parameters:
        sinfo: session information dictionary, ``id`` is used.

    Returns:
        The opening report lines.
    """
    return "\n%s\nSession id: %s \n[started on %s]" % (
        REPORT_RULE,
        sinfo["id"],
        datetime.now().strftime(REPORT_TIME),
    )


# the buckets an executor report is made of, in the order commands summarize them
REPORT_KEYS = ["done", "incomplete", "failed", "ready", "not ready", "skipped"]


def new_report() -> dict:
    """
    Build an empty executor report.

    Returns:
        A report dictionary with an empty list per :data:`REPORT_KEYS` bucket.
    """
    return {key: [] for key in REPORT_KEYS}


def stage_report(report: dict, stage: str) -> dict:
    """
    Name the stage that produced each entry in a report, in place.

    Commands that chain a second pipeline onto the first -- ICAFix into PostFix,
    MSMAll into DeDriftAndResample -- report both stages against the same BOLD or
    group name. Without the stage name a failure in the second stage is
    indistinguishable from a failure in the first, so a run whose comlog says
    ``done`` still summarizes as ``<group> failed``.

    Parameters:
        report: the report to tag.
        stage: the stage name, e.g. ``"ICAFix"``.

    Returns:
        The same report, tagged.
    """
    for key in REPORT_KEYS:
        report[key] = ["%s (%s)" % (entry, stage) for entry in report[key]]
    return report


def merge_report(report: dict, other: dict, stage: str = None) -> dict:
    """
    Merge an executor report into a command report, in place.

    Parameters:
        report: the report to merge into.
        other: the executor report to merge.
        stage: when given, the stage name each merged entry is tagged with; when
            ``None`` the entries are merged unchanged, which is what a command
            running a single stage wants.

    Returns:
        The same report, extended.
    """
    for key in REPORT_KEYS:
        entries = other.get(key, [])
        if stage is not None:
            entries = ["%s (%s)" % (entry, stage) for entry in entries]
        report[key] += entries
    return report


def _build_skipped_report(report, skipped, options):
    """
    Function builds the skipped report based on the skipped list and the
    hcp_filename option setting.
    """
    if report["boldskipped"]:
        if options["hcp_filename"] == "userdefined":
            report["skipped"] = [
                binfo.get("filename", str(binfo["bold_number"])) for binfo in skipped
            ]
        else:
            report["skipped"] = [str(binfo["bold_number"]) for binfo in skipped]


def _check_hcp_info(sinfo, options):
    """
    Check that all sessions have hcp info. Return procesed hcp paths
    """
    missing_hcp = sinfo.dont_have_key("hcp")
    if len(missing_hcp) > 0:
        raise ge.CommandFailed(
            "hcp_prep_long",
            "missing hcp info",
            f"Sessions: {', '.join([s['id'] for s in missing_hcp])} are missing hcp info.",
        )

    hcp = get_hcp_paths(sinfo[0], options)
    return hcp


def _append_sorted_logdir_to_log(log_file, logdir):
    """Append the contents of all files in a log directory into a single log.

    Files are listed in a consistent order:
    - first by increasing integer N in filenames matching '*.N.{e,o}.log'
    - then with '.e.log' preceding '.o.log' for the same N
    - any non-matching files are appended last in lexicographic order

    Parameters:
        log_file: open file handle to write to.
        logdir (str): directory with log files to append.
    """

    def _log_sort_key(filename):
        match = re.match(
            r"^(?P<prefix>.*)\.(?P<n>\d+)\.(?P<stream>[eo])\.log$", filename
        )
        if not match:
            return (float("inf"), 2, filename)

        n = int(match.group("n"))
        stream = match.group("stream")
        stream_order = 0 if stream == "e" else 1
        return (n, stream_order, filename)

    try:
        filenames = [entry.name for entry in os.scandir(logdir) if entry.is_file()]
    except FileNotFoundError:
        print(f"\n---> WARNING: log directory not found: {logdir}", file=log_file)
        return

    for filename in sorted(filenames, key=_log_sort_key):
        file_path = os.path.join(logdir, filename)
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                content = file.read()
        except OSError as err:
            content = f"[Could not read {file_path}: {err}]"

        print(file=log_file)
        print("----------------------------------------", file=log_file)
        print(f"Contents of {filename}:", file=log_file)
        print("----------------------------------------", file=log_file)
        print(content, file=log_file)


def _get_postfreesurfer_snapshot_paths(hcp):
    """Return the snapshot artifacts used to roll back PostFreeSurfer outputs."""

    return {
        "start": os.path.join(hcp["snapshots"], "postfreesurfer_start.txt"),
        "diff": os.path.join(hcp["snapshots"], "postfreesurfer_diff.txt"),
        "backup": os.path.join(hcp["snapshots"], "postfreesurfer_backup"),
    }


def _prepare_postfreesurfer_snapshot_state(hcp):
    """Refresh rollback metadata used before rerunning FreeSurfer after PostFS."""

    paths = _get_postfreesurfer_snapshot_paths(hcp)

    gs.record_snapshot(
        targetfolder=hcp["base"],
        outfile=paths["start"],
        exclude=hcp["snapshots"],
    )

    gs.backup_files(
        source=hcp["base"],
        target=paths["backup"],
        filelist=[
            "MNINonLinear/T1w.nii.gz",
            "MNINonLinear/T1w_restore.nii.gz",
            "MNINonLinear/T1w_restore_brain.nii.gz",
            "MNINonLinear/T2w.nii.gz",
            "MNINonLinear/T2w_restore.nii.gz",
            "MNINonLinear/T2w_restore_brain.nii.gz",
            "MNINonLinear/xfms/NonlinearRegJacobians.nii.gz",
            "T1w/T1w_acpc_dc.nii.gz",
            "T1w/T1w_acpc_dc_restore.nii.gz",
            "T1w/T1w_acpc_dc_restore_brain.nii.gz",
            "T1w/T2w_acpc_dc.nii.gz",
            "T1w/T2w_acpc_dc_restore.nii.gz",
            "T1w/T2w_acpc_dc_restore_brain.nii.gz",
        ],
        overwrite=True,
    )

    return paths


def do_hcp_options_check(options, command):
    if options["hcp_folderstructure"] not in ["hcpya", "hcpls"]:
        raise ge.CommandFailed(
            command,
            "Unknown HCP folder structure version",
            "The specified HCP folder structure version is unknown: %s"
            % (options["hcp_folderstructure"]),
            "Please check the 'hcp_folderstructure' parameter!",
        )

    if options["hcp_folderstructure"] == "hcpya":
        options["fctail"] = "_fncb"
        options["fmtail"] = "_strc"
    else:
        options["fctail"] = ""
        options["fmtail"] = ""


def check_inline_parameter_use(modality, parameter, options):
    return any([
        e in options["use_sequence_info"]
        for e in [
            "all",
            parameter,
            "%s:all" % (modality),
            "%s:%s" % (modality, parameter),
        ]
    ])


def check_gdc_coeff_file(gdcstring, hcp, sinfo, log, run=True):
    """
    Function that extract the information on the correct gdc file to be used and tests for its presence;
    """

    if gdcstring not in ["", "NONE"]:
        if any([e in gdcstring for e in ["|", "default"]]):
            try:
                try:
                    device = {}
                    dmanufacturer, dmodel, dserial = [
                        e.strip() for e in sinfo.get("device", "NA|NA|NA").split("|")
                    ]
                    device["manufacturer"] = dmanufacturer
                    device["model"] = dmodel
                    device["serial"] = dserial
                except Exception:
                    log.raw("\n---> WARNING: device information for this session is malformed: %s"
                        % (sinfo.get("device", "---")))
                    raise

                gdcoptions = [
                    [ee.strip() for ee in e.strip().split(":")]
                    for e in gdcstring.split("|")
                ]
                gdcfile = [e[1] for e in gdcoptions if e[0] == "default"][0]
                gdcfileused = "default"

                for ginfo, gwhat, gfile in [e for e in gdcoptions if e[0] != "default"]:
                    if ginfo in device:
                        if device[ginfo] == gwhat:
                            gdcfile = gfile
                            gdcfileused = "%s: %s" % (ginfo, gwhat)
                            break
                    if ginfo in sinfo:
                        if sinfo[ginfo] == gwhat:
                            gdcfile = gfile
                            gdcfileused = "%s: %s" % (ginfo, gwhat)
                            break
            except Exception:
                log.raw("\n---> ERROR: malformed specification of gdcoeffs: %s!" % (
                    gdcstring
                ))
                run = False
                raise

            if gdcfile in ["", "NONE"]:
                log.warning("Specific gradient distortion coefficients file could not be identified! None will be used.")
                gdcfile = "NONE"
            else:
                log.raw("\n---> Specific gradient distortion coefficients file identified (%s):\n     %s"
                    % (gdcfileused, gdcfile))

        else:
            gdcfile = gdcstring

        if gdcfile not in ["", "NONE"]:
            if not os.path.exists(gdcfile):
                gdcoeffs = os.path.join(hcp["hcp_Config"], gdcfile)
                if not os.path.exists(gdcoeffs):
                    log.raw("\n---> ERROR: Could not find gradient distortion coefficients file: %s."
                        % (gdcfile))
                    run = False
                else:
                    log.step("Gradient distortion coefficients file present.")
            else:
                log.step("Gradient distortion coefficients file present.")
    else:
        gdcfile = "NONE"

    return gdcfile, run


def resolve_session_relative_image(value, hcp_base):
    """
    Resolve an image path that may be provided in a session flexible way.

    Checks, in order:
      1. the value as an absolute path,
      2. a path relative to the session's root hcp folder,
      3. a path relative to the session's T2w folder.

    Images are passed to FSL without an extension, so ``.nii.gz`` and ``.nii``
    are also probed when testing for existence. Returns a ``(path, found)``
    tuple, where ``path`` is the first existing candidate (without appended
    extension) or the T2w fallback when none exist.
    """

    candidates = [
        value,
        os.path.join(hcp_base, value),
        os.path.join(hcp_base, "T2w", value),
    ]

    for candidate in candidates:
        # test for a file (not a directory, e.g. the T2w folder itself)
        if any(os.path.isfile(candidate + ext) for ext in ("", ".nii.gz", ".nii")):
            return candidate, True

    return candidates[-1], False


def _check_dwi_echospacing(echospacing):
    """
    Checks the echospacing parameter for the hcp_diffusion command.
    """
    echospacing = float(echospacing)

    # convert to milis
    echospacing_mili = float(echospacing) * 1000

    # all good
    if echospacing_mili > 0.1 and echospacing_mili < 1:
        return (echospacing, "")

    # maybe it was provided in miliseconds already
    if echospacing > 0.1 and echospacing < 1:
        echospacing = echospacing / 1000
        return (
            echospacing,
            f"\nWARNING: the provided value of echospacing seems to be in ms, converted to s [{echospacing}]!",
        )

    # maybe OK?
    if echospacing_mili > 0.01 and echospacing_mili < 10:
        return (
            echospacing,
            f"\nWARNING: the value of echospacing in seconds [{echospacing}] is out of the expected range, please check!",
        )

    # maybe OK in ms?
    if echospacing > 0.01 and echospacing < 10:
        echospacing = echospacing / 1000
        message = f"\nWARNING: the provided value of echospacing seems to be in ms, converted to s [{echospacing}]!"
        message += f"\nWARNING: the value of echospacing in seconds [{echospacing}] is out of the expected range, please check!"
        return (echospacing, message)

    # not OK
    return (
        None,
        f"\n---> ERROR: the value of echospacing in seconds [{echospacing}] is way out of the expected range!",
    )


def _set_hcp_prefs_template_res(image):
    """
    Set the template resolution based on the pixdim of the T1w image.

    Parameters:
        image: image to use for pixel setting.
    """

    img = nib.load(image)
    pixdim1, pixdim2, pixdim3 = img.header["pixdim"][1:4]

    # do they match
    epsilon = 0.05
    r = ""
    if abs(pixdim1 - pixdim2) > epsilon or abs(pixdim1 - pixdim3) > epsilon:
        r = f"\n     ... ERROR: T1w pixdim mismatch [{pixdim1, pixdim2, pixdim3}], please set hcp_prefs_template_res manually!"
        return (0, r)
    else:
        # upscale slightly and use the closest that matches
        pixdim = pixdim1 * 1.05

        if pixdim > 2:
            r = f"\n     ... ERROR: weird T1w pixdim found [{pixdim1, pixdim2, pixdim3}], please set the associated parameters manually!"
            return (0, r)
        elif pixdim > 1:
            r = f"\n     ... Based on T1w pixdim [{pixdim1, pixdim2, pixdim3}] the hcp_prefs_template_res parameter was set to 1.0!"
            return (1, r)
        elif pixdim > 0.8:
            r = f"\n     ... Based on T1w pixdim [{pixdim1, pixdim2, pixdim3}] the hcp_prefs_template_res parameter was set to 0.8!"
            return (0.8, r)
        elif pixdim > 0.65:
            r = f"\n     ... Based on T1w pixdim [{pixdim1, pixdim2, pixdim3}] the hcp_prefs_template_res parameter was set to to 0.7!"
            return (0.7, r)
        else:
            r = f"\n     ... ERROR: weird T1w pixdim found [{pixdim1, pixdim2, pixdim3}], please set the associated parameters manually!"
            return (0, r)


# ------------------------------------------------------------------------------
#                                      Non-human primate template configuration


# non-human primate (NHP) template configuration
# each entry maps a token (matched case-insensitively as a substring of
# hcp_species) to its species-specific template settings:
#   brain_template  the BrainTemplate folder / file name prefix in NHP_NNP
#   lowres          the low resolution used for the coarse ("2mm equivalent")
#                   atlas registration in PreFreeSurfer
#   restore         whether the structural template file names carry the
#                   "restore" tag
#   mask2mm_suffix  the suffix of the low-res structural template mask
#   atlas_dir       the surface atlas / grayordinates folder, note that
#                   ChimpYerkes29 ships it as "standard_mesh_atlas" (singular)
#   myelin_map      the reference myelin map inside atlas_dir
# mirrors HCPpipelines Examples/Scripts/SetUpSPECIES.sh
# order matters, more specific tokens (e.g. mac30bs) come before broader ones
_NHP_TEMPLATES = [
    (
        "mac30bs",
        {
            "brain_template": "Mac30BS",
            "lowres": "1.0",
            "restore": True,
            "mask2mm_suffix": "_brain_mask",
            "atlas_dir": "standard_mesh_atlases",
            "myelin_map": "MacaqueRIKEN16.Parial.MyelinMap_GroupCorr.164k_fs_LR.dscalar.nii",
        },
    ),
    (
        "cyno",
        {
            "brain_template": "Mac25Cyno",
            "lowres": "1.0",
            "restore": True,
            "mask2mm_suffix": "_brain_mask",
            "atlas_dir": "standard_mesh_atlases",
            "myelin_map": "Mac25Cyno_v3.Partial.MyelinMap_GroupCorr.164k_fs_LR.dscalar.nii",
        },
    ),
    (
        "rhesus",
        {
            "brain_template": "Mac25Rhesus",
            "lowres": "1.0",
            "restore": True,
            "mask2mm_suffix": "_brain_mask",
            "atlas_dir": "standard_mesh_atlases",
            "myelin_map": "Mac25Rhesus_v5.Partial.MyelinMap_GroupCorr.164k_fs_LR.dscalar.nii",
        },
    ),
    (
        "snow",
        {
            "brain_template": "Mac6Snow",
            "lowres": "1.0",
            "restore": True,
            "mask2mm_suffix": "_brain_mask",
            "atlas_dir": "standard_mesh_atlases",
            "myelin_map": "MacaqueRIKEN16.Parial.MyelinMap_GroupCorr.164k_fs_LR.dscalar.nii",
        },
    ),
    (
        "marmoset",
        {
            "brain_template": "MarmosetRIKEN25",
            "lowres": "0.4",
            "restore": True,
            "mask2mm_suffix": "_brain_mask_dilM",
            "atlas_dir": "standard_mesh_atlases",
            "myelin_map": "MyelinMap_B0B1TxBC.164k_fs_LR.dscalar.nii",
        },
    ),
    (
        "nightmonkey",
        {
            "brain_template": "NightMonkey9",
            "lowres": "0.5",
            "restore": True,
            "mask2mm_suffix": "_brain_mask",
            "atlas_dir": "standard_mesh_atlases",
            "myelin_map": "MyelinMap_BC.164k_fs_LR.dscalar.nii",
        },
    ),
    (
        "chimp",
        {
            "brain_template": "ChimpYerkes29",
            "lowres": "1.6",
            "restore": False,
            "mask2mm_suffix": "_brain_mask",
            "atlas_dir": "standard_mesh_atlas",
            "myelin_map": "ChimpYerkes29.MyelinMap_BC.164k_fs_LR.dscalar.nii",
        },
    ),
]


def _nhp_species_config(species):
    """
    Look up the NHP template configuration for a species.

    Parameters:
        species: the hcp_species value, matched case-insensitively against the
            tokens in _NHP_TEMPLATES.

    Returns:
        The matching configuration dict, or None if the species is not
        recognized.
    """

    species_l = species.lower()
    for token, config in _NHP_TEMPLATES:
        if token in species_l:
            return config

    return None


def _nhp_template_paths(templates_dir, species, res):
    """
    Build the PreFreeSurfer structural template paths for a non-human primate
    species, mirroring HCPpipelines Examples/Scripts/SetUpSPECIES.sh.

    Parameters:
        templates_dir: the HCP global templates folder (hcp["hcp_Templates"]).
        species: the hcp_species value (matched against _NHP_TEMPLATES).
        res: the structural resolution (hcp_prefs_template_res), in mm.

    Returns:
        A dict with the eight PreFreeSurfer template paths, or None if the
        species is not recognized.
    """

    config = _nhp_species_config(species)
    if config is None:
        return None

    brain_template = config["brain_template"]
    lowres = config["lowres"]
    base = os.path.join(templates_dir, "NHP_NNP", brain_template, "MNINonLinear")
    tag = "restore_" if config["restore"] else ""

    def _t(modality, resolution, suffix=""):
        return os.path.join(
            base, f"{brain_template}_{modality}_{tag}{resolution}mm{suffix}.nii.gz"
        )

    return {
        "t1template": _t("T1w", res),
        "t1templatebrain": _t("T1w", res, "_brain"),
        "t1template2mm": _t("T1w", lowres),
        "t2template": _t("T2w", res),
        "t2templatebrain": _t("T2w", res, "_brain"),
        "t2template2mm": _t("T2w", lowres),
        "templatemask": _t("T1w", res, "_brain_mask"),
        "template2mmmask": _t("T1w", lowres, config["mask2mm_suffix"]),
    }


def _nhp_postfs_paths(templates_dir, species):
    """
    Build the PostFreeSurfer surface atlas, grayordinates and reference myelin
    map paths for a non-human primate species, mirroring HCPpipelines
    Examples/Scripts/SetUpSPECIES.sh.

    Parameters:
        templates_dir: the HCP global templates folder (hcp["hcp_Templates"]).
        species: the hcp_species value (matched against _NHP_TEMPLATES).

    Returns:
        A dict with the surfatlasdir, grayordinatesdir and refmyelinmaps paths,
        or None if the species is not recognized. For NHP species the surface
        atlas and the grayordinates folder are one and the same.
    """

    config = _nhp_species_config(species)
    if config is None:
        return None

    atlas_dir = os.path.join(
        templates_dir, "NHP_NNP", config["brain_template"], config["atlas_dir"]
    )

    return {
        "surfatlasdir": atlas_dir,
        "grayordinatesdir": atlas_dir,
        "refmyelinmaps": os.path.join(atlas_dir, config["myelin_map"]),
    }


# ------------------------------------------------------------------------------
#                                                      Shared denoising helpers


def parse_icafix_bolds(options, bolds, log, msmall=False):
    # --- Use hcp_icafix parameter to determine if a single fix or a multi fix should be used
    single_fix = True

    # variable for storing groups and their bolds
    hcp_groups = {}

    # variable for storing erroneously specified bolds
    bold_error = []

    # flag that all is OK
    bolds_ok = True

    # get all bold targets and tags
    boldtargets = []
    boldtags = []

    for boldinfo in bolds:
        _, boldtarget, _ = pc.get_bold_names(boldinfo, options)
        boldtag = boldinfo["task"]

        boldtargets.append(boldtarget)
        boldtags.append(boldtag)

    hcp_bolds = None
    if options["hcp_icafix_bolds"] is not None:
        hcp_bolds = options["hcp_icafix_bolds"]

    if hcp_bolds:
        # if hcpBolds includes : then we have groups and we need multi fix
        if ":" in hcp_bolds:
            # run multi fix
            single_fix = False

            # get all groups
            groups = str.split(hcp_bolds, "|")

            # store all bolds in hcpBolds
            hcp_bolds = []

            for g in groups:
                # get group name
                split = str.split(g, ":")

                # create group and add to dictionary
                if split[0] not in hcp_groups:
                    specified_bolds = str.split(split[1], ",")
                    group_bolds = []

                    # iterate over all and add to bolds or inject instead of tags
                    for sb in specified_bolds:
                        if sb not in boldtargets and sb not in boldtags:
                            bold_error.append(sb)
                        else:
                            # counter
                            i = 0

                            for b in boldtargets:
                                if sb == boldtargets[i] or sb == boldtags[i]:
                                    if sb in hcp_bolds:
                                        bolds_ok = False
                                        log.raw("\n\nERROR: the bold [%s] is specified twice!"
                                            % b)
                                    else:
                                        group_bolds.append(b)
                                        hcp_bolds.append(b)

                                # increase counter
                                i = i + 1

                    hcp_groups[split[0]] = group_bolds
                else:
                    bolds_ok = False
                    log.raw("\n\nERROR: multiple concatenations with the same name [%s]!"
                        % split[0])

        # else we extract bolds and use single fix
        else:
            # specified bolds
            specified_bolds = str.split(hcp_bolds, ",")

            # variable for storing bolds
            hcp_bolds = []

            # iterate over all and add to bolds or inject instead of tags
            for sb in specified_bolds:
                if sb not in boldtargets and sb not in boldtags:
                    bold_error.append(sb)
                else:
                    # counter
                    i = 0

                    for b in boldtargets:
                        if sb == boldtargets[i] or sb == boldtags[i]:
                            if sb in hcp_bolds:
                                bolds_ok = False
                                log.raw("\n\nERROR: the bold [%s] is specified twice!" % b)
                            else:
                                hcp_bolds.append(b)

                        # increase counter
                        i = i + 1

    # if hcp_icafix is empty then bundle all bolds
    else:
        # run multi fix
        single_fix = False
        hcp_bolds = bolds
        hcp_groups = []
        hcp_groups.append({"name": "fMRI_CONCAT_ALL", "bolds": hcp_bolds})

        # create specified bolds
        specified_bolds = boldtargets

        log.raw("\nConcatenating all bolds\n")

    # --- Get hcp_icafix data from bolds
    # variable for storing skipped bolds
    bold_skip = []

    if hcp_bolds is not bolds:
        # compare
        log.raw("\n\nComparing bolds with those specifed via parameters\n")

        # single fix
        if single_fix:
            # variable for storing bold data
            bold_data = []

            # add data to list
            for b in hcp_bolds:
                # get index
                i = boldtargets.index(b)

                # store data
                if b in boldtargets:
                    bold_data.append(bolds[i])

            # skipped bolds
            for b in boldtargets:
                if b not in hcp_bolds:
                    bold_skip.append(b)

            # store data into the hcpBolds variable
            hcp_bolds = bold_data

        # multi fix
        else:
            # variable for storing group data
            group_data = {}

            # variable for storing skipped bolds
            bold_skip_dict = {}
            for b in boldtargets:
                bold_skip_dict[b] = True

            # go over all groups
            for g in hcp_groups:
                # create empty dict entry for group
                group_data[g] = []

                # go over group bolds
                group_bolds = hcp_groups[g]

                # add data to list
                for b in group_bolds:
                    # get index
                    i = boldtargets.index(b)

                    # store data
                    if b in boldtargets:
                        group_data[g].append(bolds[i])

                # find skipped bolds
                for i in range(len(boldtargets)):
                    # bold is defined
                    if boldtargets[i] in group_bolds:
                        # append

                        bold_skip_dict[boldtargets[i]] = False

            # cast boldSkip from dictionary to array
            for b in boldtargets:
                if bold_skip_dict[b]:
                    bold_skip.append(b)

            # cast group data to array of dictionaries (needed for parallel)
            hcp_groups = []
            for g in group_data:
                hcp_groups.append({"name": g, "bolds": group_data[g]})

    # report that some hcp_icafix_bolds not found in bolds
    if len(bold_skip) > 0 or len(bold_error) > 0:
        for b in bold_skip:
            log.raw("     ... skipping %s: it is not specified in hcp_icafix_bolds\n" % b)
        for b in bold_error:
            log.raw("     ... ERROR: %s specified in hcp_icafix_bolds but not found in bolds\n"
                % b)
    else:
        log.raw("     ... all bolds specified via hcp_icafix_bolds are present\n")

    if len(bold_error) > 0:
        bolds_ok = False

    # --- Report single fix or multi fix
    if single_fix:
        log.raw("\nSingle-run HCP ICAFix on %d bolds" % len(hcp_bolds))
    else:
        log.raw("\nMulti-run HCP ICAFix on %d groups" % len(hcp_groups))

    # different output for msmall and singlefix
    if msmall and single_fix:
        # single group
        hcp_groups = []
        icafix_group = {}
        icafix_group["bolds"] = hcp_bolds
        hcp_groups.append(icafix_group)

        # bolds
        hcp_bolds = specified_bolds
    elif options["hcp_icafix_bolds"] is None:
        # bolds
        hcp_bolds = specified_bolds

    return (single_fix, hcp_bolds, hcp_groups, bolds_ok)


def parse_msmall_bolds(options, bolds, log):
    # parse the same way as with icafix first
    single_run, _, icafix_groups, pars_ok = parse_icafix_bolds(
        options, bolds, log, True
    )

    msmall_groups = []

    for icafix_group in icafix_groups:
        # validate that msmall bolds is a subset of icafixGroups
        if options["hcp_msmall_bolds"] is not None:
            msmall_bolds = options["hcp_msmall_bolds"].split(",")
            hcp_msmall_bolds = []

            for mb in msmall_bolds:
                hmb = None
                for b in bolds:
                    # does the name match?
                    if (
                        "filename" in b
                        and mb == b["filename"]
                        and options["hcp_filename"] == "userdefined"
                    ):
                        hmb = b["filename"]
                        break
                    # does the number match?
                    if "bold_number" in b and mb == b["bold_number"]:
                        hmb = f"{options['hcp_bold_prefix']}{b}"
                        break
                    # does the tag match?
                    if "task" in b and mb == b["task"]:
                        if "filename" in b and options["hcp_filename"] == "userdefined":
                            hmb = b["filename"]
                            break
                        else:
                            hmb = f"{options['hcp_bold_prefix']}{b[0]}"
                            break

                if hmb is None:
                    log.raw(f"\n---> ERROR: bold {mb} used in hcp_msmall_bolds but not found in hcp_icafix_bolds!")
                    pars_ok = False
                    break
                else:
                    if hmb not in hcp_msmall_bolds:
                        hcp_msmall_bolds.append(hmb)

            icafix_group["msmall_bolds"] = hcp_msmall_bolds
        else:
            msmall_bolds = []
            for bold in icafix_group["bolds"]:
                if "filename" in bold and options["hcp_filename"] == "userdefined":
                    msmall_bolds.append(bold["filename"])
                else:
                    msmall_bolds.append(
                        f"{options['hcp_bold_prefix']}{bold['bold_number']}"
                    )

            icafix_group["msmall_bolds"] = msmall_bolds

        msmall_groups.append(icafix_group)

    return (msmall_groups, single_run, pars_ok)


def execute_hcp_post_fix(sinfo, options, hcp, run, single_fix, boldinfo):
    # prepare return variables
    log = ReportLog()
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    # extract data
    log.raw("\n\n------------------------------------------------------------")

    if single_fix:
        # highpass
        highpass = (
            2000
            if options["hcp_icafix_highpass"] is None
            else options["hcp_icafix_highpass"]
        )

        printbold, boldtarget, _ = pc.get_bold_names(boldinfo, options)

        printica = "%s_hp%s_clean.nii.gz" % (boldtarget, highpass)
        icaimg = os.path.join(hcp["hcp_nonlin"], "Results", boldtarget, printica)
        log.raw("\n---> %s bold ICA %s" % (
            pc.action("Processing", options["run"]),
            printica,
        ))

    else:
        # highpass
        highpass = (
            0
            if options["hcp_icafix_highpass"] is None
            else options["hcp_icafix_highpass"]
        )

        printbold = boldinfo
        boldtarget = boldinfo

        printica = "%s_hp%s_clean.nii.gz" % (boldtarget, highpass)
        icaimg = os.path.join(hcp["hcp_nonlin"], "Results", boldtarget, printica)
        log.raw("\n---> %s group ICA %s" % (
            pc.action("Processing", options["run"]),
            printica,
        ))

    try:
        boldok = True

        # --- check for ICA image
        boldok = log.check_for_file(icaimg,
            "\n     ... ICA %s present" % boldtarget,
            "\n     ... ERROR: ICA [%s] missing!" % icaimg,
            status=boldok,
        )

        # hcp_postfix_reusehighpass
        if options["hcp_postfix_reusehighpass"]:
            reusehighpass = "YES"
        else:
            reusehighpass = "NO"

        singlescene = os.path.join(
            hcp["hcp_base"],
            "ICAFIX/PostFixScenes/",
            "ICA_Classification_SingleScreenTemplate.scene",
        )
        if options["hcp_postfix_singlescene"] is not None:
            singlescene = options["hcp_postfix_singlescene"]

        dualscene = os.path.join(
            hcp["hcp_base"],
            "ICAFIX/PostFixScenes/",
            "ICA_Classification_DualScreenTemplate.scene",
        )
        if options["hcp_postfix_dualscene"] is not None:
            dualscene = options["hcp_postfix_dualscene"]

        # matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                log.raw("\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n")
                boldok = False
            else:
                matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
        else:
            if options["hcp_matlab_mode"] == "compiled":
                matlabrunmode = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                matlabrunmode = "1"
            elif options["hcp_matlab_mode"] == "octave":
                matlabrunmode = "2"
            else:
                log.raw("\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n")
                boldok = False

        # subject/session
        subject = sinfo["id"] + options["hcp_suffix"]

        comm = (
            '%(script)s \
            --study-folder="%(studyfolder)s" \
            --subject="%(subject)s" \
            --fmri-name="%(boldtarget)s" \
            --high-pass="%(highpass)s" \
            --template-scene-dual-screen="%(dualscene)s" \
            --template-scene-single-screen="%(singlescene)s" \
            --reuse-high-pass="%(reusehighpass)s" \
            --matlab-run-mode="%(matlabrunmode)s"'
            % {
                "script": os.path.join(hcp["hcp_base"], "ICAFIX", "PostFix.sh"),
                "studyfolder": sinfo["hcp"],
                "subject": subject,
                "boldtarget": boldtarget,
                "highpass": highpass,
                "dualscene": dualscene,
                "singlescene": singlescene,
                "reusehighpass": reusehighpass,
                "matlabrunmode": matlabrunmode,
            }
        )

        # -- Report command
        if boldok:
            log.raw("\n\n------------------------------------------------------------\n")
            log.raw("Running HCP Pipelines command via QuNex:\n\n")
            log.raw(comm.replace("--", "\n    --").replace("             ", ""))
            log.raw("\n------------------------------------------------------------\n")

        # -- Run
        if run and boldok:
            if options["run"] == "run":
                endlog, _, failed = log.run_external(
                    checkfile=None,
                    command=comm,
                    description="Running HCP PostFix",
                    overwrite=False,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task="hcp_post_fix",
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], boldtarget],
                    full_test=None,
                    shell=True,
                )

                if failed:
                    report["failed"].append(printbold)
                else:
                    report["done"].append(printbold)

            # -- just checking
            else:
                passed, _, failed = log.check_run(
                    None, None, "HCP PostFix " + boldtarget, overwrite=False
                )
                if passed is None:
                    log.step("HCP PostFix can be run")
                    report["ready"].append(printbold)
                else:
                    report["skipped"].append(printbold)

        else:
            report["not ready"].append(printbold)
            if options["run"] == "run":
                log.error("something missing, skipping this BOLD!")
            else:
                log.error("something missing, this BOLD would be skipped!")

        # log beautify
        log.raw("\n\n")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.capture("\n\n\n --- Failed during processing of bold %s with error:\n" % (printbold))
        log.raw(str(errormessage))
        report["failed"].append(printbold)
    except Exception:
        log.raw("\n --- Failed during processing of bold %s with error:\n %s\n" % (
            printbold,
            traceback.format_exc(),
        ))
        report["failed"].append(printbold)

    return {"r": log.text, "report": report}


# ------------------------------------------------------------------------------
#                                                  DeDriftAndResample executors


def execute_hcp_single_dedrift_and_resample(sinfo, options, hcp, run, group):
    # prepare return variables
    log = ReportLog()
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # get group data
        bolds = group["bolds"]

        log.raw("\n\n------------------------------------------------------------")
        log.raw("\n---> %s DeDriftAndResample" % (pc.action("Processing", options["run"])))
        boldsok = True

        # --- check for bold images and prepare targets parameter
        boldtargets = ""

        # highpass
        highpass = (
            2000
            if options["hcp_icafix_highpass"] is not None
            else options["hcp_icafix_highpass"]
        )

        # check if files for all bolds exist
        for boldinfo in bolds:
            # set ok to true for now
            boldok = True

            _, boldtarget, _ = pc.get_bold_names(boldinfo, options)

            # input file check
            boldimg = os.path.join(
                hcp["hcp_nonlin"],
                "Results",
                boldtarget,
                "%s_hp%s_clean.nii.gz" % (boldtarget, highpass),
            )
            boldok = log.check_for_file(boldimg,
                "\n     ... bold image %s present" % boldtarget,
                "\n     ... ERROR: bold image [%s] missing!" % boldimg,
                status=boldok,
            )

            if not boldok:
                boldsok = False

            # add @ separator
            if boldtargets != "":
                boldtargets = boldtargets + "@"

            # add latest image
            boldtargets = boldtargets + boldtarget

        # regname
        regname = "%s_2_d40_WRN" % options["hcp_msmall_outregname"]
        if options["hcp_resample_regname"] is not None:
            regname = options["hcp_resample_regname"]

        # dedrift reg files
        regfiles = (
            hcp["hcp_base"]
            + "/global/templates/MSMAll/DeDriftingGroup.L.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii"
            + "@"
            + hcp["hcp_base"]
            + "/global/templates/MSMAll/DeDriftingGroup.R.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii"
        )
        if options["hcp_resample_reg_files"] is not None:
            regfiles = options["hcp_resample_reg_files"].replace(",", "@")

        if options["hcp_msmall_templates"] is None:
            msmalltemplates = os.path.join(
                hcp["hcp_base"], "global", "templates", "MSMAll"
            )
        else:
            msmalltemplates = options["hcp_msmall_templates"]

        if options["hcp_msmall_myelin_target"] is None:
            myelintarget = os.path.join(
                msmalltemplates,
                "Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii",
            )
        else:
            myelintarget = options["hcp_msmall_myelin_target"]

        # matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                log.raw("\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n")
            else:
                matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
        else:
            if options["hcp_matlab_mode"] == "compiled":
                matlabrunmode = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                matlabrunmode = "1"
            elif options["hcp_matlab_mode"] == "octave":
                matlabrunmode = "2"
            else:
                log.raw("\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n")
                boldsok = False

        comm = (
            '%(script)s \
            --path="%(path)s" \
            --subject="%(subject)s" \
            --fix-names="%(fixnames)s" \
            --high-res-mesh="%(highresmesh)s" \
            --low-res-meshes="%(lowresmeshes)s" \
            --registration-name="%(regname)s" \
            --maps="%(maps)s" \
            --smoothing-fwhm="%(smoothingfwhm)s" \
            --high-pass="%(highpass)s" \
            --motion-regression="%(motionregression)s" \
            --dedrift-reg-files="%(regfiles)s" \
            --concat-reg-name="%(concatregname)s" \
            --myelin-maps="%(myelinmaps)s" \
            --myelin-target-file="%(myelintarget)s" \
            --matlab-run-mode="%(matlabrunmode)s"'
            % {
                "script": os.path.join(
                    hcp["hcp_base"],
                    "DeDriftAndResample",
                    "DeDriftAndResamplePipeline.sh",
                ),
                "path": sinfo["hcp"],
                "subject": sinfo["id"] + options["hcp_suffix"],
                "fixnames": boldtargets,
                "highresmesh": options["hcp_hiresmesh"],
                "lowresmeshes": options["hcp_lowresmeshes"].replace(",", "@"),
                "regname": regname,
                "maps": options["hcp_resample_maps"].replace(",", "@"),
                "smoothingfwhm": options["hcp_bold_smoothFWHM"],
                "highpass": highpass,
                "motionregression": (
                    "TRUE"
                    if options["hcp_icafix_domotionreg"] is None
                    else options["hcp_icafix_domotionreg"]
                ),
                "regfiles": regfiles,
                "concatregname": options["hcp_resample_concatregname"],
                "myelinmaps": options["hcp_resample_myelinmaps"].replace(",", "@"),
                "myelintarget": myelintarget,
                "matlabrunmode": matlabrunmode,
            }
        )

        # optional parameters
        if options["hcp_resample_dontfixnames"] is not None:
            comm += "                --dont-fix-names=" + options[
                "hcp_resample_dontfixnames"
            ].replace(",", "@")

        if options["hcp_msmall_myelin_target"] is not None:
            comm += (
                "                --myelin-target-file="
                + options["hcp_msmall_myelin_target"]
            )

        if options["hcp_resample_inregname"] is not None:
            comm += (
                "                --input-reg-name=" + options["hcp_resample_inregname"]
            )

        if options["hcp_resample_use_ind_mean"] is not None:
            comm += (
                "                --use-ind-mean=" + options["hcp_resample_use_ind_mean"]
            )

        # -- Report command
        if boldsok:
            log.raw("\n\n------------------------------------------------------------\n")
            log.raw("Running HCP Pipelines command via QuNex:\n\n")
            log.raw(comm.replace("--", "\n    --").replace("             ", ""))
            log.raw("\n------------------------------------------------------------\n")

        # -- Run
        if run and boldsok:
            if options["run"] == "run":
                endlog, _, failed = log.run_external(
                    None,
                    comm,
                    "Running HCP DeDriftAndResample",
                    overwrite=True,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task="hcp_dedrift_and_resample",
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], regname],
                    full_test=None,
                    shell=True,
                )

                if failed:
                    report["failed"].append(regname)
                else:
                    report["done"].append(regname)

            # -- just checking
            else:
                passed, _, failed = log.check_run(
                    None, None, "HCP DeDriftAndResample", overwrite=True
                )
                if passed is None:
                    log.step("HCP DeDriftAndResample can be run")
                    report["ready"].append(regname)
                else:
                    report["skipped"].append(regname)

        else:
            report["not ready"].append(regname)
            if options["run"] == "run":
                log.error("something missing, skipping this group!")
            else:
                log.error("something missing, this group would be skipped!")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.capture("\n\n\n --- Failed during processing of group %s with error:\n" % (
            "DeDriftAndResample"
        ))
        log.raw(str(errormessage))
        report["failed"].append(regname)
    except Exception:
        log.raw("\n --- Failed during processing of group %s with error:\n %s\n" % (
            "DeDriftAndResample",
            traceback.format_exc(),
        ))
        report["failed"].append(regname)

    return {"r": log.text, "report": report}


def execute_hcp_multi_dedrift_and_resample(sinfo, options, hcp, run, group):
    # prepare return variables
    log = ReportLog()
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        log.raw("\n\n------------------------------------------------------------")
        log.raw("\n---> %s DeDriftAndResample" % (pc.action("Processing", options["run"])))

        # --- check for bold images and prepare targets parameter
        group_list = []
        grouptargets = ""
        bold_list = []
        boldtargets = ""

        # highpass
        highpass = (
            0
            if options["hcp_icafix_highpass"] is None
            else options["hcp_icafix_highpass"]
        )

        # runok
        runok = True

        # check if files for all bolds exist
        # get group data
        groupname = group["name"]
        bolds = group["bolds"]

        # for storing bolds
        groupbolds = ""

        for boldinfo in bolds:
            _, boldtarget, _ = pc.get_bold_names(boldinfo, options)

            # input file check
            boldimg = os.path.join(
                hcp["hcp_nonlin"],
                "Results",
                boldtarget,
                "%s_hp%s_clean.nii.gz" % (boldtarget, highpass),
            )
            boldok = log.check_for_file(boldimg,
                "\n     ... bold image %s present" % boldtarget,
                "\n     ... ERROR: bold image [%s] missing!" % boldimg,
            )

            if not boldok:
                runok = False

            # add @ separator
            if groupbolds != "":
                groupbolds = groupbolds + "@"

            # add latest image
            bold_list.append(boldtarget)
            groupbolds = groupbolds + boldtarget

        # check if group file exists
        groupica = "%s_hp%s_clean.nii.gz" % (groupname, highpass)
        groupimg = os.path.join(hcp["hcp_nonlin"], "Results", groupname, groupica)
        groupok = log.check_for_file(groupimg,
            "\n     ... ICA %s present" % groupname,
            "\n     ... ERROR: ICA [%s] missing!" % groupimg,
        )

        if not groupok:
            runok = False

        # add @ or % separator
        if grouptargets != "":
            grouptargets = grouptargets + "@"
            boldtargets = boldtargets + "%"

        # add latest group
        group_list.append(groupname)
        grouptargets = grouptargets + groupname
        boldtargets = boldtargets + groupbolds

        # regname
        regname = "%s_2_d40_WRN" % options["hcp_msmall_outregname"]
        if options["hcp_resample_regname"] is not None:
            regname = options["hcp_resample_regname"]

        # dedrift reg files
        regfiles = (
            hcp["hcp_base"]
            + "/global/templates/MSMAll/DeDriftingGroup.L.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii"
            + "@"
            + hcp["hcp_base"]
            + "/global/templates/MSMAll/DeDriftingGroup.R.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii"
        )
        if options["hcp_resample_reg_files"] is not None:
            regfiles = options["hcp_resample_reg_files"].replace(",", "@")

        if options["hcp_msmall_templates"] is None:
            msmalltemplates = os.path.join(
                hcp["hcp_base"], "global", "templates", "MSMAll"
            )
        else:
            msmalltemplates = options["hcp_msmall_templates"]

        if options["hcp_msmall_myelin_target"] is None:
            myelintarget = os.path.join(
                msmalltemplates,
                "Q1-Q6_RelatedParcellation210.MyelinMap_BC_MSMAll_2_d41_WRN_DeDrift.32k_fs_LR.dscalar.nii",
            )
        else:
            myelintarget = options["hcp_msmall_myelin_target"]

        # matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                log.raw("\\nERROR: hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n")
                runok = False
            else:
                matlabrunmode = os.environ["FSL_FIX_MATLAB_MODE"]
        else:
            if options["hcp_matlab_mode"] == "compiled":
                matlabrunmode = "0"
            elif options["hcp_matlab_mode"] == "interpreted":
                matlabrunmode = "1"
            elif options["hcp_matlab_mode"] == "octave":
                matlabrunmode = "2"
            else:
                log.raw("\\nERROR: unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n")
                runok = False

        comm = (
            '%(script)s \
            --path="%(path)s" \
            --subject="%(subject)s" \
            --high-res-mesh="%(highresmesh)s" \
            --low-res-meshes="%(lowresmeshes)s" \
            --registration-name="%(regname)s" \
            --maps="%(maps)s" \
            --smoothing-fwhm="%(smoothingfwhm)s" \
            --high-pass="%(highpass)s" \
            --motion-regression="%(motionregression)s" \
            --dedrift-reg-files="%(regfiles)s" \
            --concat-reg-name="%(concatregname)s" \
            --myelin-maps="%(myelinmaps)s" \
            --myelin-target-file="%(myelintarget)s" \
            --matlab-run-mode="%(matlabrunmode)s"'
            % {
                "script": os.path.join(
                    hcp["hcp_base"],
                    "DeDriftAndResample",
                    "DeDriftAndResamplePipeline.sh",
                ),
                "path": sinfo["hcp"],
                "subject": sinfo["id"] + options["hcp_suffix"],
                "highresmesh": options["hcp_hiresmesh"],
                "lowresmeshes": options["hcp_lowresmeshes"].replace(",", "@"),
                "regname": regname,
                "maps": options["hcp_resample_maps"].replace(",", "@"),
                "smoothingfwhm": options["hcp_bold_smoothFWHM"],
                "highpass": highpass,
                "motionregression": (
                    "FALSE"
                    if options["hcp_icafix_domotionreg"] is None
                    else options["hcp_icafix_domotionreg"]
                ),
                "regfiles": regfiles,
                "concatregname": options["hcp_resample_concatregname"],
                "myelinmaps": options["hcp_resample_myelinmaps"].replace(",", "@"),
                "myelintarget": myelintarget,
                "matlabrunmode": matlabrunmode,
            }
        )

        # do not set --multirun-fix-names and --multirun-fix-concat-names for the second step of longitudinal processing
        if "long" not in sinfo or sinfo["long"] == 1:
            comm += "                --multirun-fix-names=" + boldtargets
            comm += "                --multirun-fix-concat-names=" + grouptargets

        # optional parameters
        if options["hcp_resample_dontfixnames"] is not None:
            comm += "                --dont-fix-names=" + options[
                "hcp_resample_dontfixnames"
            ].replace(",", "@")

        if options["hcp_msmall_myelin_target"] is not None:
            comm += (
                "                --myelin-target-file="
                + options["hcp_msmall_myelin_target"]
            )

        if options["hcp_resample_inregname"] is not None:
            comm += (
                "                --input-reg-name=" + options["hcp_resample_inregname"]
            )

        if options["hcp_resample_use_ind_mean"] is not None:
            comm += (
                "                --use-ind-mean=" + options["hcp_resample_use_ind_mean"]
            )

        # -- hcp_resample_extractnames
        if options["hcp_resample_extractnames"] is not None:
            # variables for storing
            boldnames = ""
            extractnames = ""
            extractconcatnames = ""

            # split to groups
            ens = options["hcp_resample_extractnames"].split("|")
            # iterate
            for en in ens:
                en_split = en.split(":")
                concatname = en_split[0]

                # if none all is good
                if concatname.upper() == "NONE":
                    concatname = concatname.upper()
                    boldnames = "NONE"
                # wrong input
                elif len(en_split) == 0:
                    runok = False
                    log.error("invalid input, check the hcp_resample_extractnames parameter!")
                # else check if concatname is in groups
                else:
                    # extract fix names ok?
                    fixnames = en_split[1].split(",")
                    for fn in fixnames:
                        # extract fixname name ok?
                        if fn not in bold_list:
                            runok = False
                            log.raw("\n---> ERROR: extract fix name [%s], not found in provided fix names!"
                                % fn)

                    if len(en_split) > 0:
                        boldnames = en_split[1].replace(",", "@")

                # add @ or % separator
                if extractnames != "":
                    extractconcatnames = extractconcatnames + "@"
                    extractnames = extractnames + "%"

                # add latest group
                extractconcatnames = extractconcatnames + concatname
                extractnames = extractnames + boldnames

            # append to command
            comm += '             --multirun-fix-extract-names="%s"' % extractnames
            comm += (
                '             --multirun-fix-extract-concat-names="%s"'
                % extractconcatnames
            )

        # -- hcp_resample_extractextraregnames
        if options["hcp_resample_extractextraregnames"] is not None:
            comm += (
                '             --multirun-fix-extract-extra-regnames="%s"'
                % options["hcp_resample_extractextraregnames"]
            )

        # -- hcp_resample_extractvolume
        if options["hcp_resample_extractvolume"] is not None:
            extractvolume = options["hcp_resample_extractvolume"].upper()

            # check value
            if extractvolume != "TRUE" and extractvolume != "FALSE":
                runok = False
                log.raw("\n---> ERROR: invalid extractvolume parameter [%s], expecting TRUE or FALSE!"
                    % extractvolume)

            # append to command
            comm += '             --multirun-fix-extract-volume="%s"' % extractvolume

        # -- Report command
        if runok:
            log.raw("\n\n------------------------------------------------------------\n")
            log.raw("Running HCP Pipelines command via QuNex:\n\n")
            log.raw(comm.replace("--", "\n    --").replace("             ", ""))
            log.raw("\n------------------------------------------------------------\n")

        # -- Run
        if run and runok:
            if options["run"] == "run":
                _, _, failed = log.run_external(
                    None,
                    comm,
                    "Running HCP DeDriftAndResample",
                    overwrite=True,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task="hcp_dedrift_and_resample",
                    logfolder=options["comlogs"],
                    logtags=[options["logtag"], groupname],
                    full_test=None,
                    shell=True,
                )

                if failed:
                    report["failed"].append(grouptargets)
                else:
                    report["done"].append(grouptargets)

            # -- just checking
            else:
                passed, _, failed = log.check_run(
                    None, None, "HCP DeDriftAndResample", overwrite=True
                )
                if passed is None:
                    log.step("HCP DeDriftAndResample can be run")
                    report["ready"].append(grouptargets)
                else:
                    report["skipped"].append(grouptargets)

        else:
            report["not ready"].append(grouptargets)
            if options["run"] == "run":
                log.error("something missing, skipping this group!")
            else:
                log.error("something missing, this group would be skipped!")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.capture("\n\n\n --- Failed during processing of group %s with error:\n" % (
            "DeDriftAndResample"
        ))
        log.raw(str(errormessage))
        report["failed"].append(grouptargets)
    except Exception:
        log.raw("\n --- Failed during processing of group %s with error:\n %s\n" % (
            "DeDriftAndResample",
            traceback.format_exc(),
        ))
        report["failed"].append(grouptargets)

    return {"r": log.text, "report": report}


def handle_hcp_links(groupfolder, sessions, options, remove=False):
    """
    Creates/removes soft links to session HCP folders for commands that operate 
    across multiple sessions
    """

    if not os.path.exists(groupfolder):
        os.makedirs(groupfolder)

    abs_sessionsfolder = os.path.abspath(options['sessionsfolder'])

    for session in sessions:
        session_id = session['id']
        source_path = os.path.join(abs_sessionsfolder, session_id, 'hcp', session_id)
        target_path = os.path.join(groupfolder, session_id + options["hcp_suffix"])

        if not remove:
            gc.link_or_copy(source_path, target_path, symlink=True)
        else:
            if os.path.exists(target_path):
                os.unlink(target_path)

    return


def write_transmit_bias_voltages(sessions, options, voltages_file, log):
    """
    Write one TxRefAmp value per session into ``voltages_file``.

    Used by hcp_transmit_bias_group_average_corrected_maps (phase 4) and by
    the create_transmit_bias_voltages_file command.

    The output file order matches the order of the supplied sessions.
    """

    values = []

    for session in sessions:
        subject = session["id"] + options["hcp_suffix"]

        json_file = os.path.join(
            options["sessionsfolder"],
            session["id"],
            "hcp",
            subject,
            "unprocessed",
            "rfMRI_REST1_AP",
            f"{subject}_rfMRI_REST1_AP.json",
        )

        if not os.path.exists(json_file):
            log.raw(f"\n---> ERROR: Cannot create hcp_voltages file. JSON file not found for session {session['id']}: {json_file}")
            return False

        try:
            with open(json_file, "r") as f:
                metadata = json.load(f)
        except Exception as e:
            log.raw(f"\n---> ERROR: Cannot create hcp_voltages file. Failed to read JSON file for session {session['id']}: {json_file}. Error: {e}")
            return False

        if "TxRefAmp" not in metadata:
            log.raw(f"\n---> ERROR: Cannot create hcp_voltages file. TxRefAmp not found for session {session['id']} in JSON file: {json_file}")
            return False

        values.append(str(metadata["TxRefAmp"]))

    output_dir = os.path.dirname(voltages_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        with open(voltages_file, "w") as f:
            for value in values:
                f.write(value + "\n")
    except Exception as e:
        log.raw(f"\n---> ERROR: Cannot write hcp_voltages file: {voltages_file}. Error: {e}")
        return False

    log.raw(f"\n---> Created hcp_voltages file: {voltages_file}")
    return True
