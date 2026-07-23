#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_pre_freesurfer.py``

The HCP PreFreeSurfer pipeline.
"""

import glob
import json
import os
import os.path

import qx_utilities.general.exceptions as ge
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_paths import se_dir_map, get_hcp_paths
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_utils import (
    check_gdc_coeff_file,
    _set_hcp_prefs_template_res,
    check_inline_parameter_use,
    do_hcp_options_check,
    resolve_session_relative_image,
)
from qx_utilities.hcp.hcp_utils import _nhp_template_paths


def hcp_pre_freesurfer(sinfo, options, overwrite=False, thread=0):
    r"""
    ``hcp_pre_freesurfer [... processing options]``

    Run the pre-FS step of the HCP Pipeline (PreFreeSurferPipeline.sh).

    ..  qx_command:
        type: processing.session

    Warning:
        The code expects the input images to be named and present in the
        specific folder structure. Specifically it will look within the
        folder::

            <session id>/hcp/<session id>

        for folders and files::

            T1w/\*T1w_MPR[N]\*
            T2w/\*T2w_MPR[N]\*

        There has to be at least one T1w image present. If there are more than
        one T1w or T2w images, they will all be used and averaged together.

        Depending on the type of distortion correction method specified by the
        `--hcp_avgrdcmethod` argument (see below), it will also expect the
        presence of the following files:

        **TOPUP**::

            SpinEchoFieldMap[N]\*/\*_<hcp_sephasepos>_\*
            SpinEchoFieldMap[N]\*/\*_<hcp_sephaseneg>_\*

        **SiemensFieldMap, GEHealthCareFieldMap or PhilipsFieldMap**::

            FieldMap/<session id>_FieldMap_Magnitude.nii.gz
            FieldMap/<session id>_FieldMap_Phase.nii.gz

        **GEHealthCareLegacyFieldMap**::

            FieldMap/<session id>_FieldMap_GE.nii.gz

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_processing_mode (str, default 'HCPStyleData'):
            Controls whether the HCP acquisition and processing guidelines
            should be treated as requirements ('HCPStyleData') or if additional
            processing functionality is allowed ('LegacyStyleData'). In this
            case running processing w/o a T2w image.

        --hcp_folderstructure (str, default 'hcpls'):
            If set to 'hcpya' the folder structure used in the initial HCP
            Young Adults study is used. Specifically, the source files are
            stored in individual folders within the main 'hcp' folder in
            parallel with the working folders and the 'MNINonLinear' folder
            with results. If set to 'hcpls' the folder structure used in the
            HCP Life Span study is used. Specifically, the source files are
            all stored within their individual subfolders located in the joint
            'unprocessed' folder in the main 'hcp' folder, parallel to the
            working folders and the 'MNINonLinear' folder.

        --hcp_filename (str, default 'automated'):
            How to name the BOLD files once mapped into the hcp input folder
            structure. The default ('automated') will automatically name each
            file by their number (e.g. BOLD_1). The alternative ('userdefined')
            is to use the file names, which can be defined by the user prior to
            mapping (e.g. rfMRI_REST1_AP).

        --hcp_t2 (str, default 't2'):
            'NONE' if no T2w image is available and the preprocessing should be
            run without them, anything else otherwise [t2]. 'NONE' is only valid
            if 'LegacyStyleData' processing mode was specified.

        --hcp_brainsize (int, default 150):
             Specifies the size of the brain in mm. 170 is FSL default and seems
             to be a good choice, HCP uses 150, which can lead to problems with
             larger heads.

        --hcp_t1samplespacing (str, default 'NONE'):
            T1 image sample spacing, 'NONE' if not used.

        --hcp_t2samplespacing (str, default 'NONE'):
            T2 image sample spacing, 'NONE' if not used.

        --hcp_gdcoeffs (str, default 'NONE'):
            Path to a file containing gradient distortion coefficients,
            alternatively a string describing multiple options (see below), or
            "NONE", if not used.

        --hcp_bfsigma (str, default ''):
            Bias Field Smoothing Sigma (optional).

        --hcp_avgrdcmethod (str):
            Averaging and readout distortion correction method.
            Can take the following values:

            - 'NONE' (average any repeats with no readout correction)
            - 'FIELDMAP' (average any repeats and use Siemens field map for
              readout correction)
            - 'SiemensFieldMap' (average any repeats and use Siemens field map
              for readout correction)
            - 'GEHealthCareFieldMap' (average any repeats and use GE field
              map for readout correction)
            - 'GEHealthCareLegacyFieldMap' (average any repeats and use GE field
              map for readout correction, for legacy, combined GE field maps)
            - 'PhilipsFieldMap' (average any repeats and use Philips field map
              for readout correction)
            - 'TOPUP' (average any repeats and use spin echo field map for
              readout correction).

        --hcp_unwarpdir (str, default ''):
            Readout direction of the T1w and T2w images (x, y, z or NONE); used
            with either a regular field map or a spin echo field map.

        --hcp_echodiff (str):
            Difference in TE times if a fieldmap image is used, set to NONE if
            not used.

        --hcp_seechospacing (str, default ''):
            Echo Spacing or of Spin Echo Field Maps in seconds or "NONE" if not
            used.

        --hcp_sephasepos (str, default ''):
            Label for the positive image of the Spin Echo Field Map pair.

        --hcp_sephaseneg (str, default ''):
            Label for the negative image of the Spin Echo Field Map pair.

        --hcp_senum (str, default ''):
            Number of the Spin Echo Field Map pair to use, will be set
            automatically based on the batch/session file. If set, QuNex will
            use the files in the SpinEchoFieldMap[N] folder from the HCP
            unprocessed folder.

        --hcp_seunwarpdir (str, default ''):
            Phase encoding direction of the Spin Echo Field Map (x, y or NONE).

        --hcp_topupconfig (str, default 'NONE'):
            Path to a configuration file for TOPUP method or "NONE" if not used.

        --hcp_prefs_custombrain (str, default 'NONE'):
            Whether to only run the final registration using either a custom
            prepared brain mask (MASK) or custom prepared brain images
            (CUSTOM), or to run the full set of processing steps (NONE).
            If a mask is to be used (MASK) then a
            `"custom_acpc_dc_restore_mask.nii.gz"` image needs to be placed in
            the `<session>/T1w` folder. If a custom brain is to be used
            (BRAIN), then the following images in `<session>/T1w` folder need
            to be adjusted:

            - `T1w_acpc_dc_restore_brain.nii.gz`
            - `T1w_acpc_dc_restore.nii.gz`
            - `T2w_acpc_dc_restore_brain.nii.gz`
            - `T2w_acpc_dc_restore.nii.gz`.

        --hcp_prefs_template_res (float, default set from imaging data):
            The resolution (in mm) of the structural images templates to use in
            the preFS step. Note: it should match the resolution of the
            acquired structural images. If no value is provided, QuNex will try
            to use the imaging data to set a sensible default value. It will
            notify you about which setting it used, you should pay attention to
            this piece of information and manually overwrite the default if
            something is off. For non-human species (hcp_species other than
            'Human') this parameter cannot be inferred automatically and must
            be set explicitly, as it also selects the species-specific template
            (e.g. 0.5, 0.3 or 0.25 for a macaque).

        --hcp_prefs_t1template (str):
            Path to the T1 template to be used by PreFreeSurfer. By default the
            used template is determined through the resolution provided by the
            hcp_prefs_template_res parameter. For non-human species (hcp_species
            other than 'Human') the default is taken from the species-specific
            NHP_NNP template folder instead of the human MNI152 templates.

        --hcp_prefs_t1templatebrain (str):
            Path to the T1 brain template to be used by PreFreeSurfer. By
            default the used template is determined through the resolution
            provided by the hcp_prefs_template_res parameter.

        --hcp_prefs_t1template2mm (str):
            Path to the T1 2mm template to be used by PreFreeSurfer. By default
            the used template is HCP's MNI152_T1_2mm.nii.gz.

        --hcp_prefs_t2template (str):
            Path to the T2 template to be used by PreFreeSurfer. By default the
            used template is determined through the resolution provided by the
            hcp_prefs_template_res parameter.

        --hcp_prefs_t2templatebrain (str):
            Path to the T2 brain template to be used by PreFreeSurfer. By
            default the used template is determined through the resolution
            provided by the hcp_prefs_template_res parameter.

        --hcp_prefs_t2template2mm (str):
            Path to the T2 2mm template to be used by PreFreeSurfer. By default
            the used template is HCP's MNI152_T2_2mm.nii.gz.

        --hcp_prefs_templatemask (str):
            Path to the template mask to be used by PreFreeSurfer. By default
            the used template mask is determined through the resolution provided
            by the hcp_prefs_template_res parameter.

        --hcp_prefs_template2mmmask (str):
            Path to the template mask to be used by PreFreeSurfer. By default
            the used 2mm template mask is HCP's
            MNI152_T1_2mm_brain_mask_dil.nii.gz.

        --hcp_prefs_fnirtconfig (str):
            Path to the used FNIRT config. Set to the HCP's T1_2_MNI152_2mm.cnf
            by default.

        --use_sequence_info (str, default 'all'):
            A pipe, comma or space separated list of inline sequence information
            to use in preprocessing of specific image modalities.

            Example specifications:

            - `all`: use all present inline information for all modalities,
            - 'DwellTime': use DwellTime information for all modalities,
            - `T1w:all`: use all present inline information for T1w modality,
            - `SE:EchoSpacing`: use EchoSpacing information for Spin-Echo
              fieldmap images.
            - `none`: do not use inline information

            Modalities: T1w, T2w, SE, BOLD, dMRi Inline information: TR,
            PEDirection, EchoSpacing DwellTime, ReadoutDirection.

            If information is not specified it will not be used. More general
            specification (e.g. `all`) implies all more specific cases (e.g.
            `T1w:all`).

        --hcp_sephasepos2 (str, default ''):
            Label for the positive image of the second Spin Echo Field Map pair.

        --hcp_sephaseneg2 (str, default ''):
            Label for the negative image of the second Spin Echo Field Map pair.

        --hcp_senum2 (str, default ''):
            Number of the second Spin Echo Field Map pair to use for SE2. QuNex
            will use the files in the SpinEchoFieldMap[N] folder from the HCP
            unprocessed folder.

        --hcp_species (str, default ''):
            Species (default: Human). When set to a non-human species QuNex
            switches to the species-specific NHP templates (from the NHP_NNP
            template folder) and requires hcp_prefs_template_res to be set
            explicitly. Recognized non-human species are: Chimp, MacaqueCyno,
            MacaqueRhesus, MacaqueSnow, MacaqueMac30BS, Marmoset, NightMonkey.

        --hcp_runmode (str, default ''):
            Specify from which step to resume the processing instead of
            starting from the beginning. Value must be one of: Default,
            ACPCAlignment, BrainExtraction, T2wToT1wRegAndBiasCorrection,
            AtlasRegistration (default: Default).

        --hcp_truepatientposition (str, default ''):
            True patient position (default: HFS).

        --hcp_scannerpatientposition (str, default ''):
            Scanner patient position (default: HFS).

        --hcp_betcenter (str, default ''):
            Center coordinates for BET (default: 45,55,39).

        --hcp_betradius (str, default ''):
            Radius for BET (default: 75).

        --hcp_betfraction (str, default ''):
            Fraction for BET (default: 0.3).

        --hcp_bettop2center (str, default ''):
            Distance from top to center for BET (default: 86).

        --hcp_brainextract (str, default ''):
            Brain extraction method (default: INVIVO).

        --hcp_use_t2w_phase_zero (str, default ''):
            Indicates whether to add T2-weighted image as a phase zero volume,
            for bright-CSF T2w contrast acquisition types (e.g., not FLAIR).
            Accepted values are 'TRUE' and 'FALSE'.

        --hcp_bias_field_sigma_no_t2w (str, default ''):
            Bias Field Smoothing Sigma for Bias Field Correction using T1w
            image only (only for NHP, default: 20).

        --hcp_betbiasfieldcor (str, default ''):
            Indicates whether to correct bias field for BET (default: FALSE).
            Accepted values are 'TRUE' and 'FALSE'.

    Output files:
        The results of this step will be present in the above mentioned T1w
        and T2w folders as well as MNINonLinear folder generated and
        populated in the same sessions's root hcp folder.

    Notes:
        Gradient coefficient file specification:
            ``--hcp_gdcoeffs`` parameter can be set to either 'NONE', a path to
            a specific file to use, or a string that describes, which file to
            use in which case. Each option of the string has to be divided by a
            pipe '|' character and it has to specify, which information to look
            up, a possible value, and a file to use in that case, separated by
            a colon ':' character. The information too look up needs to be
            present in the description of that session. Standard options are
            e.g.::

                institution: Yale
                device: Siemens|Prisma|123456

            Where device is formatted as <manufacturer>|<model>|<serial number>.

            If specifying a string it also has to include a `default` option,
            which will be used in the information was not found. An example
            could be::

                "default:/data/gc1.conf|model:Prisma:/data/gc/Prisma.conf|model:Trio:/data/gc/Trio.conf"

            With the information present above, the file `/data/gc/Prisma.conf`
            would be used.

        hcp_pre_freesurfer parameter mapping:

            =============================== ===========================
            QuNex parameter                 HCPpipelines parameter
            =============================== ===========================
            ``hcp_prefs_t1template``        ``t1template``
            ``hcp_prefs_t1templatebrain``   ``t1templatebrain``
            ``hcp_prefs_t1template2mm``     ``t1template2mm``
            ``hcp_prefs_t2template``        ``t2template``
            ``hcp_prefs_t2templatebrain``   ``t2templatebrain``
            ``hcp_prefs_t2template2mm``     ``t2template2mm``
            ``hcp_prefs_templatemask``      ``templatemask``
            ``hcp_prefs_template2mmmask``   ``template2mmmask``
            ``hcp_brainsize``               ``brainsize``
            ``hcp_prefs_fnirtconfig``       ``fnirtconfig``
            ``hcp_sephaseneg``              ``SEPhaseNeg``
            ``hcp_sephasepos``              ``SEPhasePos``
            ``hcp_seechospacing``           ``seechospacing``
            ``hcp_seunwarpdir``             ``seunwarpdir``
            ``hcp_t1samplespacing``         ``t1samplespacing``
            ``hcp_t2samplespacing``         ``t2samplespacing``
            ``hcp_gdcoeffs``                ``gdcoeffs``
            ``hcp_avgrdcmethod``            ``avgrdcmethod``
            ``hcp_topupconfig``             ``topupconfig``
            ``hcp_bfsigma``                 ``bfsigma``
            ``hcp_prefs_custombrain``       ``custombrain``
            ``hcp_processing_mode``         ``processing-mode``
            ``hcp_sephaseneg2``             ``SEPhaseNeg2``
            ``hcp_sephasepos2``             ``SEPhasePos2``
            ``hcp_species``                 ``species``
            ``hcp_runmode``                 ``runmode``
            ``hcp_truepatientposition``     ``truepatientposition``
            ``hcp_scannerpatientposition``  ``scannerpatientposition``
            ``hcp_betcenter``               ``betcenter``
            ``hcp_betradius``               ``betradius``
            ``hcp_betfraction``             ``betfraction``
            ``hcp_bettop2center``           ``bettop2center``
            ``hcp_brainextract``            ``brainextract``
            ``hcp_use_t2w_phase_zero``      ``use-t2w-phase-zero``
            ``hcp_bias_field_sigma_no_t2w`` ``bias-field-sigma-no-T2w``
            ``hcp_betbiasfieldcor``         ``betbiasfieldcor``
            =============================== ===========================

        Use:
            Runs the PreFreeSurfer step of the HCP Pipeline. It looks for T1w
            and T2w images in sessions's T1w and T2w folder, averages them (if
            multiple present) and linearly and nonlinearly aligns them to the
            MNI atlas. It uses the adjusted version of the HCP that enables the
            preprocessing to run with of without T2w image(s).

    Examples:
        ::

            qunex hcp_pre_freesurfer \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --hcp_brainsize=170

        ::

            qunex hcp_pre_freesurfer \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --hcp_t2=NONE
    """

    log = SessionLog(sinfo, options, "HCP PreFreeSurfer Pipeline", tail="\n")

    run = True
    report = "Error"

    try:
        # mandatory check
        if not options["hcp_avgrdcmethod"]:
            raise ge.CommandFailed(
                "hcp_pre_freesurfer",
                "... the hcp_avgrdcmethod parameter needs to be set manually! Since QuNex cannot robustly extract the information needed to set this from the data, you need to set this parameter by yourself.",
            )

        # --- Base settings
        pc.do_options_check(options, sinfo, "hcp_pre_freesurfer")
        do_hcp_options_check(options, "hcp_pre_freesurfer")
        hcp = get_hcp_paths(sinfo, options)

        # --- run checks
        if "hcp" not in sinfo:
            log.raw("\n---> ERROR: There is no hcp info for session %s in batch.txt"
                % (sinfo["id"]))
            run = False

        # --- check for T1w and T2w images
        for tfile in hcp["T1w"].split("@"):
            if os.path.exists(tfile):
                log.step("T1w image file present.")
                t1w = [
                    v for (k, v) in sinfo.items() if k.isdigit() and v["name"] == "T1w"
                ][0]

                if "DwellTime" in t1w and check_inline_parameter_use(
                    "T1w", "DwellTime", options
                ):
                    options["hcp_t1samplespacing"] = f"{float(t1w['DwellTime']):.10f}"
                    log.raw("\n---> T1w image specific EchoSpacing: %s s"
                        % (options["hcp_t1samplespacing"]))
                elif "EchoSpacing" in t1w and check_inline_parameter_use(
                    "T1w", "EchoSpacing", options
                ):
                    options["hcp_t1samplespacing"] = f"{float(t1w['EchoSpacing']):.10f}"
                    log.raw("\n---> T1w image specific EchoSpacing: %s s"
                        % (options["hcp_t1samplespacing"]))

                if (
                    options["hcp_unwarpdir"] is None
                    and "UnwarpDir" in t1w
                    and check_inline_parameter_use("T1w", "UnwarpDir", options)
                ):
                    options["hcp_unwarpdir"] = t1w["UnwarpDir"]
                    log.raw("\n---> T1w image specific unwarp direction: %s"
                        % (options["hcp_unwarpdir"]))

                # try to set hcp_t1samplespacing from the JSON sidecar if not yet set
                if options["hcp_t1samplespacing"] == "NONE":
                    json_sidecar = tfile.replace("nii.gz", "json")
                    if os.path.exists(json_sidecar):
                        log.step("Trying to set hcp_t1samplespacing from the JSON sidecar.")
                        with open(json_sidecar, "r") as file:
                            sidecar_data = json.load(file)
                            if "DwellTime" in sidecar_data:
                                options["hcp_t1samplespacing"] = (
                                    f"{float(sidecar_data['DwellTime']):.10f}"
                                )
                                log.raw(f"\n       - hcp_t1samplespacing set to {options['hcp_t1samplespacing']}")

        if hcp["T2w"] in ["", "NONE"]:
            if options["hcp_processing_mode"] == "HCPStyleData":
                log.error("The requested HCP processing mode is 'HCPStyleData', however, no T2w image was specified!\n            Consider using LegacyStyleData processing mode.")
                run = False
            else:
                log.step("Not using T2w image.")
        else:
            for tfile in hcp["T2w"].split("@"):
                if os.path.exists(tfile):
                    log.step("T2w image file present.")
                    t2w = [
                        v
                        for (k, v) in sinfo.items()
                        if k.isdigit() and v["name"] == "T2w"
                    ][0]
                    if "DwellTime" in t2w and check_inline_parameter_use(
                        "T2w", "DwellTime", options
                    ):
                        options["hcp_t2samplespacing"] = (
                            f"{float(t2w['DwellTime']):.10f}"
                        )
                        log.raw("\n---> T2w image specific EchoSpacing: %s s"
                            % (options["hcp_t2samplespacing"]))
                    elif "EchoSpacing" in t2w and check_inline_parameter_use(
                        "T2w", "EchoSpacing", options
                    ):
                        options["hcp_t2samplespacing"] = (
                            f"{float(t2w['EchoSpacing']):.10f}"
                        )
                        log.raw("\n---> T2w image specific EchoSpacing: %s s"
                            % (options["hcp_t2samplespacing"]))

                    # try to set hcp_t2samplespacing from the JSON sidecar if not yet set
                    if options["hcp_t2samplespacing"] == "NONE":
                        json_sidecar = tfile.replace("nii.gz", "json")
                        if os.path.exists(json_sidecar):
                            log.step("Trying to set hcp_t2samplespacing from the JSON sidecar.")
                            with open(json_sidecar, "r") as file:
                                sidecar_data = json.load(file)
                                if "DwellTime" in sidecar_data:
                                    options["hcp_t2samplespacing"] = (
                                        f"{float(sidecar_data['DwellTime']):.10f}"
                                    )
                                    log.raw(f"\n       - hcp_t2samplespacing set to {options['hcp_t2samplespacing']}")

                else:
                    log.raw("\n---> ERROR: Could not find T2w image file. [%s]" % (tfile))
                    run = False

        # --- do we need spinecho images
        sepos = ""
        seneg = ""
        topupconfig = ""
        senum = None
        tufolder = None
        fmmag = ""
        fmphase = ""
        fmcombined = ""
        echodiff = "NONE"
        if options["hcp_avgrdcmethod"].lower() == "topup":
            try:
                # -- spin echo settings
                t1w = [
                    v for (k, v) in sinfo.items() if k.isdigit() and v["name"] == "T1w"
                ][0]
                senum = t1w.get("se", None)
                # overwrite senum if set
                if options["hcp_senum"]:
                    senum = options["hcp_senum"]
                    log.raw("\n---> Overwriting automatically extracted Spin-Echo pair number with a user specified value: %s"
                        % (options["hcp_senum"]))
                if senum:
                    try:
                        senum = int(senum)
                        if senum > 0:
                            tufolder = os.path.join(
                                hcp["source"],
                                "SpinEchoFieldMap%d%s" % (senum, options["fctail"]),
                            )
                            log.raw("\n---> TOPUP Correction, Spin-Echo pair %d specified"
                                % (senum))
                        else:
                            log.raw("\n---> ERROR: No Spin-Echo image pair specified for T1w image! [%d]"
                                % (senum))
                            run = False
                    except Exception:
                        log.raw("\n---> ERROR: Could not process the specified Spin-Echo information [%s]! "
                            % (str(senum)))
                        run = False

            except Exception:
                pass

            if senum is None:
                try:
                    tufolder = glob.glob(
                        os.path.join(hcp["source"], "SpinEchoFieldMap*")
                    )[0]
                    senum = int(
                        os.path
                        .basename(tufolder)
                        .replace("SpinEchoFieldMap", "")
                        .replace("_fncb", "")
                    )
                    log.raw("\n---> TOPUP Correction, no Spin-Echo pair explicitly specified, using pair %d"
                        % (senum))
                except Exception:
                    log.raw("\n---> ERROR: Could not find folder with files for TOPUP processing of session %s."
                        % (sinfo["id"]))
                    run = False
                    raise

            # try to set hcp_seechospacing from the JSON sidecar if not yet set
            if options["hcp_seechospacing"] is None and tufolder:
                fmap_json = glob.glob(os.path.join(tufolder, "*AP*.json"))
                if len(fmap_json) == 0:
                    fmap_json = glob.glob(os.path.join(tufolder, "*LR*.json"))

                if len(fmap_json) != 0:
                    fmap_json = fmap_json[0]
                    json_sidecar = os.path.join(tufolder, fmap_json)

                    if os.path.exists(json_sidecar):
                        log.step("Trying to set hcp_seechospacing from the JSON sidecar.")
                        with open(json_sidecar, "r") as file:
                            sidecar_data = json.load(file)
                            if "EffectiveEchoSpacing" in sidecar_data:
                                options["hcp_seechospacing"] = (
                                    f"{float(sidecar_data['EffectiveEchoSpacing']):.10f}"
                                )
                                log.raw(f"\n       - hcp_seechospacing set to {options['hcp_seechospacing']}")

            # -- spin echo settings
            sesettings = True
            for p in [
                "hcp_sephaseneg",
                "hcp_sephasepos",
            ]:
                if not options[p]:
                    log.raw(f"\nERROR: {p} parameter not set! It needs to be set manually as QuNex cannot infer it from the data in a robust manner.")
                    run = False
                    sesettings = False

            try:
                # se phase pos and neg
                # full paths
                if sesettings:
                    if os.path.exists(options["hcp_sephasepos"]) and os.path.exists(
                        options["hcp_sephaseneg"]
                    ):
                        sepos = options["hcp_sephasepos"]
                        seneg = options["hcp_sephaseneg"]
                        log.raw("\n---> Spin-Echo pair of images present. [%s, %s]" % (
                            os.path.basename(sepos),
                            os.path.basename(seneg),
                        ))
                    # labels
                    elif tufolder:
                        sepos = glob.glob(
                            os.path.join(
                                tufolder, "*_" + options["hcp_sephasepos"] + "*.nii.gz"
                            )
                        )[0]
                        seneg = glob.glob(
                            os.path.join(
                                tufolder, "*_" + options["hcp_sephaseneg"] + "*.nii.gz"
                            )
                        )[0]

                        if all([sepos, seneg]):
                            log.raw("\n---> Spin-Echo pair of images present. [%s]" % (
                                os.path.basename(tufolder)
                            ))
                        else:
                            log.raw("\n---> ERROR: Could not find the relevant Spin-Echo files! [%s]"
                                % (tufolder))
                            run = False

                # get SE info from session info
                try:
                    se_info = [
                        v
                        for (k, v) in sinfo.items()
                        if k.isdigit()
                        and "SE-FM" in v["name"]
                        and "se" in v
                        and v["se"] == str(senum)
                    ][0]
                except Exception:
                    se_info = None

                if options["hcp_seechospacing"] is None:
                    if (
                        se_info
                        and "EchoSpacing" in se_info
                        and check_inline_parameter_use("SE", "EchoSpacing", options)
                    ):
                        options["hcp_seechospacing"] = se_info["EchoSpacing"]
                        log.raw("\n---> Spin-Echo images specific EchoSpacing: %s s"
                            % (options["hcp_seechospacing"]))

                if options["hcp_seunwarpdir"] is None:
                    if se_info and "phenc" in se_info:
                        options["hcp_seunwarpdir"] = se_dir_map[se_info["phenc"]]
                        log.raw("\n---> Spin-Echo unwarp direction: %s"
                            % (options["hcp_seunwarpdir"]))
                    elif (
                        se_info
                        and "PEDirection" in se_info
                        and check_inline_parameter_use("SE", "PEDirection", options)
                    ):
                        options["hcp_seunwarpdir"] = se_info["PEDirection"]
                        log.raw("\n---> Spin-Echo unwarp direction: %s"
                            % (options["hcp_seunwarpdir"]))

                if options["hcp_topupconfig"] != "NONE" and options["hcp_topupconfig"]:
                    topupconfig = options["hcp_topupconfig"]
                    if not os.path.exists(options["hcp_topupconfig"]):
                        topupconfig = os.path.join(
                            hcp["hcp_Config"], options["hcp_topupconfig"]
                        )
                        if not os.path.exists(topupconfig):
                            log.raw("\n---> ERROR: Could not find TOPUP configuration file: %s."
                                % (topupconfig))
                            run = False
                        else:
                            log.step("TOPUP configuration file present.")
                    else:
                        log.step("TOPUP configuration file present.")

                for p in [
                    "hcp_seechospacing",
                    "hcp_seunwarpdir",
                ]:
                    if p in options and not options[p]:
                        log.raw(f"\nERROR: {p} parameter not set manually and QuNex was unable to set it automatically.")
                        run = False

            except Exception:
                log.raw("\n---> ERROR: Could not find files for TOPUP processing of session %s."
                    % (sinfo["id"]))
                run = False
                raise

        elif options["hcp_avgrdcmethod"].lower() == "gehealthcarelegacyfieldmap":
            fmnum = t1w.get("fm", None)

            if fmnum is None:
                log.error("No fieldmap number specified for the T1w image!")
                run = False
            else:
                for i, v in hcp["fieldmap"].items():
                    if os.path.exists(hcp["fieldmap"][i]["GE"]):
                        log.raw("\n---> Gradient Echo Field Map %d file present." % (i))
                    else:
                        log.raw("\n---> ERROR: Could not find Gradient Echo Field Map %d file for session %s.\n            Expected location: %s"
                            % (i, sinfo["id"], hcp["fmapge"]))
                        run = False

                fmmag = None
                fmphase = None
                fmcombined = hcp["fieldmap"][int(fmnum)]["GE"]

        elif options["hcp_avgrdcmethod"].lower() in [
            "fieldmap",
            "siemensfieldmap",
            "philipsfieldmap",
            "gehealthcarefieldmap",
        ]:
            fmnum = t1w.get("fm", None)

            if fmnum is None:
                log.error("No fieldmap number specified for the T1w image!")
                run = False
            else:
                for i, v in hcp["fieldmap"].items():
                    if isinstance(hcp["fieldmap"][i]["magnitude"], list):
                        if all(
                            os.path.exists(mag)
                            for mag in hcp["fieldmap"][i]["magnitude"]
                        ):
                            log.raw("\n---> Magnitude Field Map %d files present." % (i))
                        else:
                            log.raw("\n---> ERROR: Could not find all Magnitude Field Map %d files for session %s.\n            Expected locations: %s"
                                % (i, sinfo["id"], hcp["fieldmap"][i]["magnitude"]))
                            run = False
                    else:
                        if os.path.exists(hcp["fieldmap"][i]["magnitude"]):
                            log.raw("\n---> Magnitude Field Map %d file present." % (i))
                        else:
                            log.raw("\n---> ERROR: Could not find Magnitude Field Map %d file for session %s.\n            Expected location: %s"
                                % (i, sinfo["id"], hcp["fieldmap"][i]["magnitude"]))
                            run = False
                    if os.path.exists(hcp["fieldmap"][i]["phase"]):
                        log.raw("\n---> Phase Field Map %d file present." % (i))
                    else:
                        log.raw("\n---> ERROR: Could not find Phase Field Map %d file for session %s.\n            Expected location: %s"
                            % (i, sinfo["id"], hcp["fmapphase"]))
                        run = False

                fmmag = hcp["fieldmap"][int(fmnum)]["magnitude"]
                if isinstance(fmmag, list):
                    fmmag = "@".join(fmmag)
                fmphase = hcp["fieldmap"][int(fmnum)]["phase"]
                fmcombined = None

                # try to set hcp_echodiff from the JSON sidecar if not yet set
                if not options["hcp_echodiff"]:
                    fmfolder = os.path.join(
                        hcp["source"],
                        "FieldMap%s%s" % (fmnum, options["fctail"]),
                    )

                    fmap_json = glob.glob(os.path.join(fmfolder, "*Phase.json"))

                    if len(fmap_json) != 0:
                        fmap_json = fmap_json[0]
                        json_sidecar = os.path.join(fmfolder, fmap_json)

                        if os.path.exists(json_sidecar):
                            log.step("Trying to set hcp_echodiff from the JSON sidecar.")
                            with open(json_sidecar, "r") as file:
                                sidecar_data = json.load(file)
                                if (
                                    "EchoTime1" in sidecar_data
                                    and "EchoTime2" in sidecar_data
                                ):
                                    et2 = float(sidecar_data["EchoTime2"])
                                    et1 = float(sidecar_data["EchoTime1"])
                                    echodiff = (et2 - et1) * 1000
                                    echodiff = f"{echodiff:.10f}"
                                    log.raw(f"\n       - hcp_echodiff set to {echodiff}")
                        else:
                            log.step("hcp_echodiff not provided and not found in the JSON sidecar, setting it to 'NONE'.")
                            echodiff = "NONE"
                            if options["hcp_avgrdcmethod"].lower() == "fieldmap":
                                log.error("hcp_echodiff is not set and cannot be deducted from the JSON sidecar.")
                                run = False
                    else:
                        log.step("JSON sidecar not found, setting hcp_echodiff to 'NONE'.")
                        echodiff = "NONE"
                        if options["hcp_avgrdcmethod"].lower() == "fieldmap":
                            log.error("hcp_echodiff is not set and cannot be deducted from the JSON sidecar.")
                            run = False
                else:
                    echodiff = options["hcp_echodiff"]

        else:
            log.warning("No distortion correction method specified.")

        # --- lookup gdcoeffs file if needed
        gdcfile, run = check_gdc_coeff_file(options["hcp_gdcoeffs"], hcp, sinfo, log, run)

        # --- see if we have set up to use custom mask
        if options["hcp_prefs_custombrain"] == "MASK":
            tfile = os.path.join(hcp["T1w_folder"], "T1w_acpc_dc_restore_brain.nii.gz")
            mfile = os.path.join(
                hcp["T1w_folder"], "custom_acpc_dc_restore_mask.nii.gz"
            )
            log.step("Set to run only final atlas registration with a custom mask.")

            if os.path.exists(tfile):
                log.detail("Previous results present.")
                if os.path.exists(mfile):
                    log.detail("Custom mask present.")
                else:
                    log.raw("\n     ... ERROR: Custom mask missing! [%s]!." % (mfile))
                    run = False
            else:
                run = False
                log.detail("ERROR: No previous results found! Please run PreFS without hcp_prefs_custombrain set to MASK first!")
                if os.path.exists(mfile):
                    log.detail("Custom mask present.")
                else:
                    log.raw("\n     ... ERROR: Custom mask missing as well! [%s]!." % (
                        mfile
                    ))

        # --- check if we are using a custom brain
        if options["hcp_prefs_custombrain"] == "CUSTOM":
            t1files = ["T1w_acpc_dc_restore_brain.nii.gz", "T1w_acpc_dc_restore.nii.gz"]
            t2files = ["T2w_acpc_dc_restore_brain.nii.gz", "T2w_acpc_dc_restore.nii.gz"]
            if hcp["T2w"] in ["", "NONE"]:
                tfiles = t1files
            else:
                tfiles = t1files + t2files

            log.step("Set to run only final atlas registration with custom brain images.")

            missingfiles = []
            for tfile in tfiles:
                if not os.path.exists(os.path.join(hcp["T1w_folder"], tfile)):
                    missingfiles.append(tfile)

            if missingfiles:
                run = False
                log.raw("\n     ... ERROR: The following brain files are missing in %s:"
                    % (hcp["T1w_folder"]))
                for tfile in missingfiles:
                    log.raw("\n                %s" % tfile)

        # -- Prepare templates
        # non-human species use species-specific templates from a different
        # folder (NHP_NNP) with a different naming convention, see the
        # _nhp_template_paths helper and HCPpipelines SetUpSPECIES.sh
        species = options["hcp_species"]
        is_human = not species or species.lower() == "human"

        # resolve the template resolution
        if is_human:
            # try to set hcp_prefs_template_res automatically if not set yet
            if not options["hcp_prefs_template_res"]:
                log.step("Trying to set the hcp_prefs_template_res parameter automatically.")
                t1w = hcp["T1w"].split("@")[0]
                resolution, res_report = _set_hcp_prefs_template_res(t1w)
                log.raw(res_report)
                if resolution == 0:
                    run = False
                    log.detail("ERROR: unable to set hcp_prefs_template_res automatically, please set it manually!")
                else:
                    options["hcp_prefs_template_res"] = resolution
        elif not options["hcp_prefs_template_res"]:
            # non-human resolution cannot be inferred and selects the
            # species-specific template, so it has to be set explicitly
            log.raw("\n---> ERROR: hcp_prefs_template_res must be set explicitly for non-human species '%s'; QuNex cannot infer it from the data."
                % (species))
            run = False

        # if hcp_prefs_template_res cannot be converted to a number something went wrong
        if options["hcp_prefs_template_res"]:
            try:
                float(options["hcp_prefs_template_res"])
            except Exception:
                log.raw("\n---> ERROR: hcp_prefs_template_res  [%s] is not a number! It could be that automatic setup did not work, set it manually."
                    % (options["hcp_prefs_template_res"]))
                run = False

        # default structural template paths; human templates live in the
        # MNI152 space, non-human ones in the species-specific NHP_NNP folder
        if is_human:
            res = options["hcp_prefs_template_res"]
            tdir = hcp["hcp_Templates"]
            tpl = {
                "t1template": os.path.join(tdir, "MNI152_T1_%smm.nii.gz" % res),
                "t1templatebrain": os.path.join(
                    tdir, "MNI152_T1_%smm_brain.nii.gz" % res
                ),
                "t1template2mm": os.path.join(tdir, "MNI152_T1_2mm.nii.gz"),
                "t2template": os.path.join(tdir, "MNI152_T2_%smm.nii.gz" % res),
                "t2templatebrain": os.path.join(
                    tdir, "MNI152_T2_%smm_brain.nii.gz" % res
                ),
                "t2template2mm": os.path.join(tdir, "MNI152_T2_2mm.nii.gz"),
                "templatemask": os.path.join(
                    tdir, "MNI152_T1_%smm_brain_mask.nii.gz" % res
                ),
                "template2mmmask": os.path.join(
                    tdir, "MNI152_T1_2mm_brain_mask_dil.nii.gz"
                ),
            }
        else:
            tpl = _nhp_template_paths(
                hcp["hcp_Templates"], species, options["hcp_prefs_template_res"]
            )
            if tpl is None:
                tpl = {}
                log.raw("\n---> NOTE: species '%s' is not in QuNex's built-in NHP template map; "
                    "the structural template paths have to be provided explicitly via "
                    "hcp_prefs_t1template and the related parameters." % (species))

        # hcp_prefs_t1template
        if options["hcp_prefs_t1template"] is None:
            t1template = tpl.get("t1template")
        else:
            t1template = options["hcp_prefs_t1template"]

        # hcp_prefs_t1templatebrain
        if options["hcp_prefs_t1templatebrain"] is None:
            t1templatebrain = tpl.get("t1templatebrain")
        else:
            t1templatebrain = options["hcp_prefs_t1templatebrain"]

        # hcp_prefs_t1template2mm
        if options["hcp_prefs_t1template2mm"] is None:
            t1template2mm = tpl.get("t1template2mm")
        else:
            t1template2mm = options["hcp_prefs_t1template2mm"]

        # hcp_prefs_t2template
        if options["hcp_t2"] == "NONE":
            t2template = "NONE"
        elif options["hcp_prefs_t2template"] is None:
            t2template = tpl.get("t2template")
        else:
            t2template = options["hcp_prefs_t2template"]

        # hcp_prefs_t2templatebrain
        if options["hcp_t2"] == "NONE":
            t2templatebrain = "NONE"
        elif options["hcp_prefs_t2templatebrain"] is None:
            t2templatebrain = tpl.get("t2templatebrain")
        else:
            t2templatebrain = options["hcp_prefs_t2templatebrain"]

        # hcp_prefs_t2template2mm
        if options["hcp_t2"] == "NONE":
            t2template2mm = "NONE"
        elif options["hcp_prefs_t2template2mm"] is None:
            t2template2mm = tpl.get("t2template2mm")
        else:
            t2template2mm = options["hcp_prefs_t2template2mm"]

        # hcp_prefs_templatemask
        if options["hcp_prefs_templatemask"] is None:
            templatemask = tpl.get("templatemask")
        else:
            templatemask = options["hcp_prefs_templatemask"]

        # hcp_prefs_template2mmmask
        if options["hcp_prefs_template2mmmask"] is None:
            template2mmmask = tpl.get("template2mmmask")
        else:
            template2mmmask = options["hcp_prefs_template2mmmask"]

        # for non-human species make sure the required templates got resolved
        if not is_human:
            required = [
                ("hcp_prefs_t1template", t1template),
                ("hcp_prefs_t1templatebrain", t1templatebrain),
                ("hcp_prefs_t1template2mm", t1template2mm),
                ("hcp_prefs_templatemask", templatemask),
                ("hcp_prefs_template2mmmask", template2mmmask),
            ]
            for pname, pvalue in required:
                if not pvalue:
                    log.raw("\n---> ERROR: could not determine %s for species '%s', please set it manually."
                        % (pname, species))
                    run = False

        # hcp_prefs_fnirtconfig
        if options["hcp_prefs_fnirtconfig"] is None:
            if is_human:
                fnirtconfig = os.path.join(hcp["hcp_Config"], "T1_2_MNI152_2mm.cnf")
            elif species.lower() == "marmoset":
                fnirtconfig = os.path.join(
                    hcp["hcp_Config"], "T1_2_NHP_NNP_Marmoset_0.4mm.cnf"
                )
            elif "macaque" in species.lower():
                fnirtconfig = os.path.join(
                    hcp["hcp_Config"], "T1_2_NHP_NNP_Macaque_1mm.cnf"
                )
        else:
            fnirtconfig = options["hcp_prefs_fnirtconfig"]

        # --- Set up the command
        comm = (
            os.path.join(hcp["hcp_base"], "PreFreeSurfer", "PreFreeSurferPipeline.sh")
            + " "
        )

        # if hcp_seechospacing and hcp_seunwarpdir are None at this point, set to "NONE"
        if options["hcp_seechospacing"] is None:
            options["hcp_seechospacing"] = "NONE"
        if options["hcp_seunwarpdir"] is None:
            options["hcp_seunwarpdir"] = "NONE"

        elements = [
            ("path", sinfo["hcp"]),
            ("subject", sinfo["id"] + options["hcp_suffix"]),
            ("t1", hcp["T1w"]),
            ("t2", hcp["T2w"]),
            ("t1template", t1template),
            ("t1templatebrain", t1templatebrain),
            ("t1template2mm", t1template2mm),
            ("t2template", t2template),
            ("t2templatebrain", t2templatebrain),
            ("t2template2mm", t2template2mm),
            ("templatemask", templatemask),
            ("template2mmmask", template2mmmask),
            ("brainsize", options["hcp_brainsize"]),
            ("fnirtconfig", fnirtconfig),
            ("fmapmag", fmmag),
            ("fmapphase", fmphase),
            ("fmapcombined", fmcombined),
            ("echodiff", echodiff),
            ("SEPhaseNeg", seneg),
            ("SEPhasePos", sepos),
            ("seechospacing", options["hcp_seechospacing"]),
            ("seunwarpdir", options["hcp_seunwarpdir"]),
            ("t1samplespacing", options["hcp_t1samplespacing"]),
            ("t2samplespacing", options["hcp_t2samplespacing"]),
            ("unwarpdir", options["hcp_unwarpdir"]),
            ("gdcoeffs", gdcfile),
            ("avgrdcmethod", options["hcp_avgrdcmethod"]),
            ("topupconfig", topupconfig),
            ("bfsigma", options["hcp_bfsigma"]),
            ("printcom", options["hcp_printcom"]),
            ("custombrain", options["hcp_prefs_custombrain"]),
            ("processing-mode", options["hcp_processing_mode"]),
        ]

        # optional parameters
        # hcp_sephasepos2, hcp_sephaseneg2, hcp_senum2 for a second SE pair for TOPUP
        if options["hcp_sephasepos2"] and options["hcp_sephaseneg2"]:
            if os.path.exists(options["hcp_sephasepos2"]) and os.path.exists(
                options["hcp_sephaseneg2"]
            ):
                sepos2 = options["hcp_sephasepos2"]
                seneg2 = options["hcp_sephaseneg2"]
                log.raw("\n---> Second Spin-Echo pair of images present. [%s, %s]" % (
                    os.path.basename(sepos2),
                    os.path.basename(seneg2),
                ))
            # labels
            elif options["hcp_senum2"]:
                try:
                    tufolder2 = os.path.join(
                        hcp["source"],
                        "SpinEchoFieldMap%s%s"
                        % (options["hcp_senum2"], options["fctail"]),
                    )
                    sepos2 = glob.glob(
                        os.path.join(
                            tufolder2, "*_" + options["hcp_sephasepos2"] + "*.nii.gz"
                        )
                    )[0]
                    seneg2 = glob.glob(
                        os.path.join(
                            tufolder2, "*_" + options["hcp_sephaseneg2"] + "*.nii.gz"
                        )
                    )[0]

                    if all([sepos2, seneg2]):
                        log.raw("\n---> Spin-Echo pair of images present. [%s]" % (
                            os.path.basename(tufolder2)
                        ))
                    else:
                        log.raw("\n---> ERROR: Could not find the relevant second Spin-Echo files! [%s]"
                            % (tufolder2))
                        run = False
                except Exception:
                    log.raw("\n---> ERROR: Could not find the relevant second Spin-Echo files! [%s]"
                        % (tufolder2))
                    run = False
            else:
                sepos2, sepos2_found = resolve_session_relative_image(
                    options["hcp_sephasepos2"], hcp["base"]
                )
                seneg2, seneg2_found = resolve_session_relative_image(
                    options["hcp_sephaseneg2"], hcp["base"]
                )

                if sepos2_found and seneg2_found:
                    log.raw("\n---> Second Spin-Echo pair of images present. [%s, %s]" % (
                        sepos2,
                        seneg2,
                    ))
                else:
                    log.raw("\n---> ERROR: Could not find the relevant second Spin-Echo files for hcp_sephasepos2/hcp_sephaseneg2! "
                        "Checked each value as an absolute path, relative to the session's hcp folder, and relative to the T2w folder.")
                    run = False

            elements += [
                ("SEPhasePos2", sepos2),
                ("SEPhaseNeg2", seneg2),
            ]

        # optional parameters: species, runmode, patient positions, BET settings, brain extraction
        if options["hcp_species"]:
            elements.append(("species", options["hcp_species"]))

        if options["hcp_runmode"]:
            elements.append(("runmode", options["hcp_runmode"]))

        if options["hcp_truepatientposition"]:
            elements.append(("truepatientposition", options["hcp_truepatientposition"]))

        if options["hcp_scannerpatientposition"]:
            elements.append((
                "scannerpatientposition",
                options["hcp_scannerpatientposition"],
            ))

        if options["hcp_betcenter"]:
            elements.append(("betcenter", options["hcp_betcenter"]))

        if options["hcp_betradius"]:
            elements.append(("betradius", options["hcp_betradius"]))

        if options["hcp_betfraction"]:
            elements.append(("betfraction", options["hcp_betfraction"]))

        if options["hcp_bettop2center"]:
            elements.append(("bettop2center", options["hcp_bettop2center"]))

        if options["hcp_brainextract"]:
            elements.append(("brainextract", options["hcp_brainextract"]))

        if options["hcp_use_t2w_phase_zero"]:
            elements.append(("use-t2w-phase-zero", options["hcp_use_t2w_phase_zero"]))

        if options["hcp_bias_field_sigma_no_t2w"]:
            elements.append((
                "bias-field-sigma-no-T2w",
                options["hcp_bias_field_sigma_no_t2w"],
            ))

        if options["hcp_betbiasfieldcor"]:
            elements.append(("betbiasfieldcor", options["hcp_betbiasfieldcor"]))

        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])

        # -- Report command
        if run:
            log.pipeline_command(comm)

        # -- Test files
        tfile = os.path.join(hcp["hcp_nonlin"], "T1w_restore_brain.nii.gz")
        if hcp["hcp_prefs_check"]:
            full_test = {
                "tfolder": hcp["base"],
                "tfile": hcp["hcp_prefs_check"],
                "fields": [("sessionid", sinfo["id"] + options["hcp_suffix"])],
                "specfolder": options["specfolder"],
            }
        else:
            full_test = None

        # -- Run
        if run:
            if options["run"] == "run":
                if overwrite:
                    if os.path.exists(tfile):
                        os.remove(tfile)

                    # additional cleanup for stability and compatibility purposes
                    image = os.path.join(
                        hcp["T1w_folder"], "T1w_acpc_dc_restore.nii.gz"
                    )
                    if os.path.exists(image):
                        os.remove(image)

                    brain = os.path.join(
                        hcp["T1w_folder"], "T1w_acpc_dc_restore_brain.nii.gz"
                    )
                    if os.path.exists(brain):
                        os.remove(brain)

                    bias = os.path.join(hcp["T1w_folder"], "BiasField_acpc_dc.nii.gz")
                    if os.path.exists(bias):
                        os.remove(bias)

                _, report, failed = log.run_external(
                    tfile,
                    comm,
                    "Running HCP PreFS",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    full_test=full_test,
                    shell=True,
                )

            # -- just checking
            else:
                passed, report, failed = log.check_run(
                    tfile, full_test, "HCP PreFS", overwrite=overwrite
                )
                if passed is None:
                    log.step("HCP PreFS can be run")
                    report = "HCP Pre FS can be run"
                    failed = 0
        else:
            log.step("Due to missing files session cannot be processed.")
            report = "Files missing, PreFS cannot be run"
            failed = 1

    except ge.CommandFailed as e:
        log.command_failed(e, "PreFreeSurfer")
        report = "PreFS failed"
        failed = 1
    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.capture(str(errormessage))
        report = "PreFS failed"
        failed = 1
    except Exception:
        log.unknown_error()
        report = "PreFS failed"
        failed = 1

    log.close(pipeline="HCP PreFS", lead="\n")

    return log.result(report, failed)
