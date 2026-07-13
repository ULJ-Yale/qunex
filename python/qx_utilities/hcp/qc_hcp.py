#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``qc_hcp.py``

This file holds code for running visual QC (``hcp_run_qc``) for HCP-processed data.
It was split out of ``process_hcp.py``; the QC command and all its helpers live here.
"""

import os
import os.path
import glob
import json
import errno
import shutil
import subprocess
import traceback
import base64
import zipfile
import html as _html
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor

import nibabel as nib

import qx_utilities.processing.core as pc
import qx_utilities.general.exceptions as ge
from qx_utilities.hcp.process_hcp import getHCPPaths, doHCPOptionsCheck


# scene render resolution for `wb_command -show-scene` (width height)
QC_SCENE_RES = "2560 1080"


def _apply_on_existing(on_existing, patterns, label, rr):
    """Apply the ``--on_existing`` policy to a modality/run's existing outputs.

    on_existing:
        leave  ... do nothing (default); per-file overwrite still applies
        skip   ... if any output already exists, skip this modality/run
        delete ... remove existing outputs before running

    ``patterns`` is a list of glob patterns identifying the outputs. Returns
    ``(skip, rr)`` where ``skip`` is True only for ``on_existing='skip'`` when
    matching outputs are found.
    """

    on_existing = (on_existing or "leave").strip().lower()
    if on_existing == "leave":
        return False, rr

    existing = []
    for pat in patterns:
        existing.extend(glob.glob(pat))
    if not existing:
        return False, rr

    if on_existing == "skip":
        rr += "\n---> on_existing=skip: found %d existing %s output(s), skipping." % (
            len(existing),
            label,
        )
        return True, rr

    if on_existing == "delete":
        for f in existing:
            _safe_unlink(f)
        rr += "\n---> on_existing=delete: removed %d existing %s output(s) before running." % (
            len(existing),
            label,
        )
        return False, rr

    return False, rr


def _dummy_variable_check(template_scene, tokens, rr):
    """Return (ok, rr): verify the scene template contains the required DUMMY tokens."""

    try:
        with open(template_scene, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read()
    except OSError as e:
        return False, rr + "\n---> ERROR: cannot read scene template %s (%s)" % (template_scene, e)
    missing = [t for t in tokens if t not in txt]
    if missing:
        return False, rr + "\n---> ERROR: scene %s missing required tokens: %s" % (
            template_scene,
            ", ".join(missing),
        )
    return True, rr


def _qc_resolve_extra_templates(
    modality, scenetemplatefolder, studyfolder, userscenefile, userscenepath, processcustom
):
    """Return [(template_path, template_basename)] for user + custom QC scenes.

    A user scene (``userscenefile``) may be an absolute path or a name resolved
    against ``userscenepath`` (falling back to ``scenetemplatefolder``). Custom
    scenes are all ``*.scene`` files under
    ``<studyfolder>/processing/scenes/QC/<modality>`` when ``processcustom='yes'``.
    """

    templates = []
    if userscenefile:
        if os.path.isabs(userscenefile) and os.path.isfile(userscenefile):
            path = userscenefile
        else:
            folder = userscenepath or scenetemplatefolder
            path = os.path.join(folder, userscenefile)
        templates.append((path, os.path.basename(userscenefile)))
    if processcustom == "yes":
        custom_dir = os.path.join(studyfolder, "processing", "scenes", "QC", modality)
        for p in sorted(glob.glob(os.path.join(custom_dir, "*.scene"))):
            templates.append((p, os.path.basename(p)))
    return templates


def hcp_run_qc(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_run_qc [... processing options]``

    Run visual QC for a session.

    ..  qx_command:
        type: processing.session

    Parameters:
        --qc_modality (str, default 'BOLD'):
            One or more modalities to run QC for, as a comma-separated list (e.g.
            'BOLD,T1w,DWI'). Supported: 'rawNII', 'BOLD', 'BOLD_FC', 'T1w', 'T2w',
            'myelin', 'general', 'DWI'. Modalities (and, within BOLD/BOLD_FC, the
            individual runs) are processed in parallel (see Notes).

        --qc_outpath (str, default '<sessionsfolder>/QC/<modality>'):
            Output folder for QC artifacts. With multiple modalities and an explicit
            path, a per-modality subfolder is used.

        --qc_scenetemplatefolder (str, default '<QUNEXPATH>/qx_library/data/scenes/qc'):
            Folder containing the Workbench scene templates.

        --qc_scenezip (str, default 'yes'):
            If 'yes', also create a self-contained Workbench scene zip and copy it
            into <hcp>/qc/ (or the session's qc/ folder for the 'general' modality).

        --timestamp (str, default now):
            Timestamp suffix for the generated outputs.

        --parelements (int, default 1):
            Number of QC jobs to run in parallel within a session (see Notes). A job
            is a single non-BOLD modality, a single BOLD run, or a single BOLD_FC
            run/type.

        --hcp_suffix (str, default ''):
            Optional suffix for HCP folder naming (matches the bash --hcp_suffix).

        --on_existing (str, default 'leave'):
            Policy for pre-existing QC outputs of the requested modalities:

            - 'leave'  ... do nothing special; per-file recompute is still governed
              by --overwrite.
            - 'skip'   ... if outputs already exist for a modality/run, skip it.
            - 'delete' ... remove existing outputs for a modality/run before running.

        --qc_omitdefaults (str, default 'no'):
            If 'yes', skip the default template scene(s) for the requested modalities
            and only render user/custom scenes (see --qc_userscenefile /
            --qc_processcustom).

        --qc_userscenefile (str, default ''):
            A user-supplied scene template to render (in addition to the defaults).
            May be an absolute path or a bare name resolved against
            --qc_userscenepath (or the template folder). Non-BOLD user scenes are
            rendered with the common DUMMYPATH/DUMMYCASE/DUMMYTIMESTAMP/DUMMYPNGNAME
            substitutions; BOLD user scenes are rendered as full BOLD QC (with TSNR).

        --qc_userscenepath (str, default ''):
            Folder for --qc_userscenefile when it is given as a bare name.

        --qc_processcustom (str, default 'no'):
            If 'yes', also render every ``*.scene`` under
            <studyfolder>/processing/scenes/QC/<modality> for each requested modality.

        --bolds (str, default 'all'):
            Which BOLDs to run QC for (BOLD and BOLD_FC modalities). Follows the
            standard selection rules; may be numbers, tags, or 'all'.

        --hcp_bold_prefix (str, default ''):
            Prefix used for HCP BOLD names (e.g. ``BOLD_`` for BOLD_1). With
            ``hcp_filename=userdefined`` the filename from the batch file is used.

        --hcp_cifti_tail (str, default ''):
            CIFTI tail used in .dtseries naming (e.g. '_Atlas'). If empty, the code
            attempts to infer it by globbing (BOLD modality).

        --qc_bold_skipframes (int, default 0):
            Number of initial frames to omit from the GS plot range (BOLD modality).

        --qc_bold_snronly (str, default 'no'):
            If 'yes', compute the TSNR report only and skip scene/png (BOLD modality).

        --qc_boldfc (str, default 'pscalar,pconn'):
            Which BOLD FC map type(s) to QC for the BOLD_FC modality: 'pscalar',
            'pconn', or both (comma-separated, or 'both'). The two are not mutually
            exclusive. Only used when 'BOLD_FC' is in --qc_modality.

        --qc_boldfcinput (str, default ''):
            Generic FC input file name after the 'bold<N>_' prefix, e.g.
            'Atlas_hpss_res-mVWMWB_lpss_CAB-NP-718_r_Fz_GBC.pscalar.nii'. Used for a
            requested FC type unless a type-specific input is provided below.

        --qc_boldfcpscalarinput (str, default ''):
            FC input file name (after 'bold<N>_') for the 'pscalar' type. Overrides
            --qc_boldfcinput for pscalar; required when running both types.

        --qc_boldfcpconninput (str, default ''):
            FC input file name (after 'bold<N>_') for the 'pconn' type. Overrides
            --qc_boldfcinput for pconn; required when running both types.

        --qc_boldfcpath (str, default '<sessionsfolder>/<session>/images/functional'):
            Folder holding the FC input file(s) (BOLD_FC modality).

        --qc_datapath (str, default ''):
            For the 'general' modality: path, relative to
            <sessionsfolder>/<session>, of the folder holding the image to visualise.
            Required for 'general'.

        --qc_datafile (str, default ''):
            For the 'general' modality: file name of the image to visualise (found
            under --qc_datapath). Required for 'general'.

        --qc_dwi_path (str, default 'Diffusion'):
            DWI input folder under <hcp>/T1w (DWI modality).

        --qc_dwi_data (str, default 'data'):
            DWI data file name (without extension) under --qc_dwi_path (DWI modality).

        --qc_dwi_dtifit (str, default 'no'):
            If 'yes', also render a dtifit (FA/L3) variant scene; requires that FSL
            dtifit has run (dti_FA.nii.gz present).

        --qc_dwi_bedpostx (str, default 'no'):
            If 'yes', also render a BedpostX variant scene; requires a complete
            Diffusion.bedpostX output.

        --qc_dwi_eddyqcstats (str, default 'no'):
            If 'yes', hard-link the FSL EDDY qc.pdf into the QC folder and record
            qc_mot_abs motion into an EddyQCReport file; requires EDDY QC output.

    Notes:
        How the command runs:
            QC is a session-level command: it is dispatched across sessions in
            parallel using ``--parsessions``. Within each session, the requested
            modalities (and, for BOLD/BOLD_FC, the individual runs and FC types) are
            expanded into independent jobs and run in parallel using
            ``--parelements``. Each modality writes into
            ``<qc_outpath>/<modality>`` (default ``<sessionsfolder>/QC/<modality>``)
            and keeps per-run logs under a ``qclog`` subfolder.

            With the exception of 'rawNII', each modality renders one or more
            Workbench scenes to PNG and, when ``--qc_scenezip=yes``, produces a
            self-contained scene zip for re-loading in Connectome Workbench.
            ``--on_existing`` controls whether existing outputs are left, skipped, or
            deleted before a run; ``--overwrite`` governs per-file recomputation.

        rawNII:
            - Generates: ``<session>.RawNII.QC.zip`` (all slicesdir PNGs and the
              original index.html) and ``<session>.RawNII.QC.html`` -- a single
              self-contained HTML report with the PNGs embedded and, per raw
              sequence, its name and key parameters (TR, TE, resolution,
              dimensions x/y/z, number of volumes/directions) read from the JSON
              sidecars and NIfTI headers.
            - Prerequisites: raw NIfTIs (and, ideally, JSON sidecars) in
              ``<sessionsfolder>/<session>/nii`` after DICOM/BIDS import. Uses FSL
              ``slicesdir``.
            - Required parameters: none beyond ``--sessions`` /
              ``--sessionsfolder``.

        T1w / T2w / myelin:
            - Generates: a ``<session>.<modality>.QC.wb.scene``, a PNG, and (if
              enabled) a scene zip.
            - Prerequisites: a successful HCP structural run -- T1w/T2w require
              ``MNINonLinear/T{1,2}w_restore.nii.gz``; myelin requires the
              SmoothedMyelinMap gifti files.
            - Required parameters: none beyond session selection.

        BOLD:
            - Generates, per selected BOLD: a TSNR report, a
              ``<session>.BOLD.<bold>.QC.wb.scene``, GSmap and GStimeseries PNGs,
              and (if enabled) a scene zip.
            - Prerequisites: processed BOLD ``dtseries`` under
              ``MNINonLinear/Results/<bold>``.
            - Useful parameters: ``--bolds``, ``--hcp_bold_prefix``,
              ``--hcp_cifti_tail``, ``--qc_bold_skipframes``, ``--qc_bold_snronly``.

        BOLD_FC:
            - An independent modality (not a BOLD sub-option). Generates, per
              selected BOLD and per requested FC type, a
              ``<session>.<type>.BOLD.<bold>.QC.wb.scene``, a PNG, and (if enabled) a
              self-contained scene zip (the FC input is copied into the zip).
            - The two types 'pscalar' and 'pconn' are independent -- run one, the
              other, or both via ``--qc_boldfc``.
            - Prerequisites: the FC input file(s) at
              ``<qc_boldfcpath>/bold<N>_<input>``.
            - Required parameters: ``--qc_boldfc`` and an input per requested type
              (``--qc_boldfcinput`` and/or the type-specific
              ``--qc_boldfcpscalarinput`` / ``--qc_boldfcpconninput``).

        general:
            - Generates a ``<session>.general.QC.wb.scene`` and PNG for an arbitrary
              image within the session hierarchy.
            - Required parameters: ``--qc_datapath`` and ``--qc_datafile``.

        DWI:
            - Generates a ``<session>.DWI.QC.wb.scene`` and PNG (first/tenth frame),
              plus optional dtifit and BedpostX variant scenes and optional EDDY QC
              stats.
            - Prerequisites: ``<hcp>/T1w/<qc_dwi_path>/<qc_dwi_data>.nii.gz`` and
              ``nodif_brain_mask.nii.gz``; sub-steps require their own outputs
              (dtifit, Diffusion.bedpostX, EDDY qc).
            - Useful parameters: ``--qc_dwi_path``, ``--qc_dwi_data``,
              ``--qc_dwi_dtifit``, ``--qc_dwi_bedpostx``, ``--qc_dwi_eddyqcstats``.

    Examples:
        Run BOLD and structural QC for all sessions in a batch, 4 runs in parallel::

            qunex hcp_run_qc \\
                --sessionsfolder='<study>/sessions' \\
                --batchfile='<study>/processing/batch.txt' \\
                --qc_modality='BOLD,T1w,T2w,myelin' \\
                --parelements='4'

        Raw NIfTI QC (produces the zip + single-file HTML report)::

            qunex hcp_run_qc \\
                --sessionsfolder='<study>/sessions' \\
                --sessions='OP101,OP102' \\
                --qc_modality='rawNII'

        BOLD FC QC for both map types (each needs its own input)::

            qunex hcp_run_qc \\
                --sessionsfolder='<study>/sessions' \\
                --sessions='OP101' \\
                --qc_modality='BOLD_FC' \\
                --qc_boldfc='pscalar,pconn' \\
                --qc_boldfcpscalarinput='Atlas_..._GBC.pscalar.nii' \\
                --qc_boldfcpconninput='Atlas_..._Fz.pconn.nii' \\
                --bolds='1,2'

        DWI QC with dtifit, BedpostX and EDDY stats::

            qunex hcp_run_qc \\
                --sessionsfolder='<study>/sessions' \\
                --sessions='OP101' \\
                --qc_modality='DWI' \\
                --qc_dwi_dtifit='yes' \\
                --qc_dwi_bedpostx='yes' \\
                --qc_dwi_eddyqcstats='yes'

        General QC of an arbitrary image::

            qunex hcp_run_qc \\
                --sessionsfolder='<study>/sessions' \\
                --sessions='OP101' \\
                --qc_modality='general' \\
                --qc_datapath='images/functional' \\
                --qc_datafile='bold1_Atlas.dtseries.nii'

        Notes on the examples:
            - Combine modalities in a single call; they run in parallel per session.
            - For BOLD_FC, provide ``--qc_boldfcinput`` alone if running a single
              type, or the type-specific inputs when running both.
            - Use ``--on_existing='delete'`` to force a clean re-run, or
              ``--on_existing='skip'`` to leave completed sessions untouched.
    """

    def _get_opt(*keys, default=None):
        for key in keys:
            if key in options and options[key] not in [None, ""]:
                return options[key]
        return default

    # minimal defaults
    raw_modalities = (_get_opt("qc_modality", "modality", default="BOLD") or "BOLD")
    if isinstance(raw_modalities, (list, tuple, set)):
        modalities = [str(m).strip() for m in raw_modalities if str(m).strip()]
    else:
        modalities = [m.strip() for m in str(raw_modalities).split(",") if m.strip()]
    if not modalities:
        modalities = ["BOLD"]
    # normalize + dedupe (preserve order)
    modalities_norm = []
    seen = set()
    for m in modalities:
        key = m.strip().lower()
        if key and key not in seen:
            modalities_norm.append(m.strip())
            seen.add(key)

    canonical = {
        "bold": "BOLD",
        "bold_fc": "BOLD_FC",
        "boldfc": "BOLD_FC",
        "t1w": "T1w",
        "t2w": "T2w",
        "myelin": "Myelin",
        "general": "general",
        "rawnii": "rawNII",
        "rawnifti": "rawNII",
        "dwi": "DWI",
    }
    unsupported = [m for m in modalities_norm if m.strip().lower() not in canonical]
    if unsupported:
        raise ge.CommandError(
            "hcp_run_qc",
            "Unsupported qc_modality value(s): %s. Supported: %s."
            % (
                ", ".join(unsupported),
                ", ".join(["rawNII", "BOLD", "BOLD_FC", "T1w", "T2w", "myelin", "general", "DWI"]),
            ),
        )

    modalities_canon = []
    seen = set()
    for m in modalities_norm:
        key = m.strip().lower()
        if key in canonical and key not in seen:
            modalities_canon.append(canonical[key])
            seen.add(key)

    r = "\n---------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (
        sinfo["id"],
        datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
    )
    r += "\nRunning QC for: %s" % ", ".join(modalities_canon)

    # --- Base settings
    pc.doOptionsCheck(options, sinfo, "hcp_run_qc")
    doHCPOptionsCheck(options, "hcp_run_qc")
    hcp = getHCPPaths(sinfo, options)

    sessionsfolder = options["sessionsfolder"]

    # Standard HCP naming parameters (keep backward-compatible fallbacks)
    hcp_bold_prefix = _get_opt("hcp_bold_prefix", "boldprefix", default="") or ""
    hcp_cifti_tail = _get_opt("hcp_cifti_tail", "boldsuffix", default="") or ""
    scenezip = (_get_opt("qc_scenezip", "scenezip", default="yes") or "yes").strip().lower()
    snronly = (_get_opt("qc_bold_snronly", "snronly", default="no") or "no").strip().lower()
    skipframes = int(_get_opt("qc_bold_skipframes", "skipframes", default=0) or 0)
    dwi_path = _get_opt("qc_dwi_path", "dwipath", default="Diffusion") or "Diffusion"
    dwi_data = _get_opt("qc_dwi_data", "dwidata", default="data") or "data"
    dwi_dtifit = (_get_opt("qc_dwi_dtifit", "dtifitqc", default="no") or "no").strip().lower()
    dwi_bedpostx = (_get_opt("qc_dwi_bedpostx", "bedpostxqc", default="no") or "no").strip().lower()
    dwi_eddyqc = (_get_opt("qc_dwi_eddyqcstats", "eddyqcstats", default="no") or "no").strip().lower()
    # BOLD_FC modality: which FC type(s) to run (pscalar and/or pconn, non-exclusive)
    bold_fc_raw = (_get_opt("qc_boldfc", "boldfc", default="") or "").strip().lower()
    if bold_fc_raw in ("", "both", "all"):
        bold_fc_types = ["pscalar", "pconn"]
    else:
        bold_fc_types = [t.strip() for t in bold_fc_raw.replace("|", ",").split(",") if t.strip()]
    bad_fc = [t for t in bold_fc_types if t not in ("pscalar", "pconn")]
    if bad_fc:
        raise ge.CommandError(
            "hcp_run_qc",
            "Invalid --qc_boldfc value(s): %s. Supported: pscalar, pconn (comma-separated)."
            % ", ".join(bad_fc),
        )
    bold_fc_input = _get_opt("qc_boldfcinput", "boldfcinput", default="") or ""
    bold_fc_type_input = {
        "pscalar": _get_opt("qc_boldfcpscalarinput", default="") or bold_fc_input,
        "pconn": _get_opt("qc_boldfcpconninput", default="") or bold_fc_input,
    }
    bold_fc_path = _get_opt("qc_boldfcpath", "boldfcpath", default="") or ""
    omitdefaults = (_get_opt("qc_omitdefaults", "omitdefaults", default="no") or "no").strip().lower()
    userscenefile = _get_opt("qc_userscenefile", "userscenefile", default="") or ""
    userscenepath = _get_opt("qc_userscenepath", "userscenepath", default="") or ""
    processcustom = (_get_opt("qc_processcustom", "processcustom", default="no") or "no").strip().lower()
    studyfolder = os.path.dirname(os.path.normpath(sessionsfolder))
    on_existing = (_get_opt("on_existing", default="leave") or "leave").strip().lower()
    if on_existing not in ("leave", "skip", "delete"):
        raise ge.CommandError(
            "hcp_run_qc",
            "Invalid --on_existing value '%s'. Supported: leave, skip, delete." % on_existing,
        )
    timestamp = options.get("timestamp") or datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
    # resolve template folder
    scenetemplatefolder = _get_opt("qc_scenetemplatefolder", "scenetemplatefolder")
    if not scenetemplatefolder:
        if "QUNEXPATH" not in os.environ:
            raise ge.CommandError(
                "hcp_run_qc",
                "QUNEXPATH not set; provide --qc_scenetemplatefolder explicitly.",
            )
        scenetemplatefolder = os.path.join(os.environ["QUNEXPATH"], "qx_library", "data", "scenes", "qc")

    def _resolve_outpath(modality_name: str) -> str:
        base_outpath = _get_opt("qc_outpath", "outpath")
        if base_outpath:
            if len(modalities_canon) == 1:
                return base_outpath
            return os.path.join(base_outpath, modality_name)
        return os.path.join(sessionsfolder, "QC", modality_name)

    qc_report = {"done": [], "failed": []}

    r += "\nHCP folder: %s" % (hcp["base"])
    r += "\nTemplate folder: %s" % (scenetemplatefolder)

    # Build a single list of QC jobs (across modalities) and run them in one executor.
    jobs = []
    r += "\n\nPreparing QC jobs ..."

    for modality in modalities_canon:
        outpath = _resolve_outpath(modality)
        os.makedirs(outpath, exist_ok=True)
        qclog = os.path.join(outpath, "qclog")
        os.makedirs(qclog, exist_ok=True)

        if modality == "rawNII":
            r += "\n- rawNII: FSL slicesdir on raw NIFTIs"
            r += "\n  Output folder: %s" % (outpath)
            jobs.append(
                {
                    "modality": "rawNII",
                    "sinfo": sinfo,
                    "options": options,
                    "overwrite": overwrite,
                    "hcp": hcp,
                    "params": {
                        "run": True,
                        "outpath": outpath,
                        "qclog": qclog,
                        "timestamp": timestamp,
                        "on_existing": on_existing,
                    },
                }
            )

        elif modality == "BOLD":
            template_scene = os.path.join(scenetemplatefolder, "template_bold_qc.wb.scene")
            if not os.path.exists(template_scene):
                raise ge.CommandError("hcp_run_qc", f"Missing template scene: {template_scene}")

            r += "\n- BOLD: using template %s" % (template_scene)
            r += "\n  Output folder: %s" % (outpath)

            if "bolds" not in options or not options["bolds"]:
                options["bolds"] = "all"

            run_bold = True
            bolds, bskip, report_skipped, r = pc.use_or_skip_bold(sinfo, options, r)
            if len(bolds) == 0:
                r += "\n---> ERROR: No BOLD images found for session %s!" % (sinfo["id"])
                run_bold = False

            for boldinfo in bolds:
                jobs.append(
                    {
                        "modality": "BOLD",
                        "sinfo": sinfo,
                        "options": options,
                        "overwrite": overwrite,
                        "hcp": hcp,
                        "params": {
                            "run": run_bold,
                            "template_scene": template_scene,
                            "outpath": outpath,
                            "qclog": qclog,
                            "timestamp": timestamp,
                            "on_existing": on_existing,
                            "hcp_bold_prefix": hcp_bold_prefix,
                            "hcp_cifti_tail": hcp_cifti_tail,
                            "scenezip": scenezip,
                            "snronly": snronly,
                            "skipframes": skipframes,
                            "boldinfo": boldinfo,
                        },
                    }
                )

            # user/custom BOLD scenes (rendered as full BOLD QC with TSNR)
            for tmpl_path, tmpl_base in _qc_resolve_extra_templates(
                "BOLD", scenetemplatefolder, studyfolder,
                userscenefile, userscenepath, processcustom,
            ):
                r += "\n- BOLD user/custom scene: %s" % (tmpl_base)
                for boldinfo in bolds:
                    jobs.append(
                        {
                            "modality": "BOLD",
                            "sinfo": sinfo,
                            "options": options,
                            "overwrite": overwrite,
                            "hcp": hcp,
                            "params": {
                                "run": run_bold,
                                "template_scene": tmpl_path,
                                "working_suffix": tmpl_base,
                                "outpath": outpath,
                                "qclog": qclog,
                                "timestamp": timestamp,
                                "on_existing": on_existing,
                                "hcp_bold_prefix": hcp_bold_prefix,
                                "hcp_cifti_tail": hcp_cifti_tail,
                                "scenezip": scenezip,
                                "snronly": snronly,
                                "skipframes": skipframes,
                                "boldinfo": boldinfo,
                            },
                        }
                    )

        elif modality == "BOLD_FC":
            if "bolds" not in options or not options["bolds"]:
                options["bolds"] = "all"

            run_bold = True
            bolds, bskip, report_skipped, r = pc.use_or_skip_bold(sinfo, options, r)
            if len(bolds) == 0:
                r += "\n---> ERROR: No BOLD images found for session %s!" % (sinfo["id"])
                run_bold = False

            fc_template = {
                "pscalar": "template_scalar_bold_qc.wb.scene",
                "pconn": "template_pconn_bold_qc.wb.scene",
            }
            r += "\n- BOLD_FC: types %s" % ", ".join(bold_fc_types)
            r += "\n  Output folder: %s" % (outpath)

            for fctype in bold_fc_types:
                fcinput = bold_fc_type_input.get(fctype, "")
                if not fcinput:
                    raise ge.CommandError(
                        "hcp_run_qc",
                        "BOLD_FC type '%s' requires --qc_boldfc%sinput (or --qc_boldfcinput)."
                        % (fctype, fctype),
                    )
                template_scene = os.path.join(scenetemplatefolder, fc_template[fctype])
                if not os.path.exists(template_scene):
                    raise ge.CommandError("hcp_run_qc", f"Missing template scene: {template_scene}")
                r += "\n  - %s: using template %s" % (fctype, template_scene)
                for boldinfo in bolds:
                    jobs.append(
                        {
                            "modality": "BOLD_FC",
                            "sinfo": sinfo,
                            "options": options,
                            "overwrite": overwrite,
                            "hcp": hcp,
                            "params": {
                                "run": run_bold,
                                "template_scene": template_scene,
                                "outpath": outpath,
                                "qclog": qclog,
                                "timestamp": timestamp,
                                "on_existing": on_existing,
                                "hcp_bold_prefix": hcp_bold_prefix,
                                "scenezip": scenezip,
                                "boldinfo": boldinfo,
                                "bold_fc": fctype,
                                "bold_fc_input": fcinput,
                                "bold_fc_path": bold_fc_path,
                            },
                        }
                    )

        elif modality == "T1w":
            template_scene = os.path.join(scenetemplatefolder, "template_t1w_qc.wb.scene")
            if not os.path.exists(template_scene):
                raise ge.CommandError("hcp_run_qc", f"Missing template scene: {template_scene}")
            r += "\n- T1w: using template %s" % (template_scene)
            r += "\n  Output folder: %s" % (outpath)
            jobs.append(
                {
                    "modality": "T1w",
                    "sinfo": sinfo,
                    "options": options,
                    "overwrite": overwrite,
                    "hcp": hcp,
                    "params": {
                        "run": True,
                        "template_scene": template_scene,
                        "outpath": outpath,
                        "qclog": qclog,
                        "timestamp": timestamp,
                        "on_existing": on_existing,
                        "scenezip": scenezip,
                    },
                }
            )

        elif modality == "T2w":
            template_scene = os.path.join(scenetemplatefolder, "template_t2w_qc.wb.scene")
            if not os.path.exists(template_scene):
                raise ge.CommandError("hcp_run_qc", f"Missing template scene: {template_scene}")
            r += "\n- T2w: using template %s" % (template_scene)
            r += "\n  Output folder: %s" % (outpath)
            jobs.append(
                {
                    "modality": "T2w",
                    "sinfo": sinfo,
                    "options": options,
                    "overwrite": overwrite,
                    "hcp": hcp,
                    "params": {
                        "run": True,
                        "template_scene": template_scene,
                        "outpath": outpath,
                        "qclog": qclog,
                        "timestamp": timestamp,
                        "on_existing": on_existing,
                        "scenezip": scenezip,
                    },
                }
            )

        elif modality == "Myelin":
            template_scene = os.path.join(scenetemplatefolder, "template_myelin_qc.wb.scene")
            if not os.path.exists(template_scene):
                raise ge.CommandError("hcp_run_qc", f"Missing template scene: {template_scene}")
            r += "\n- Myelin: using template %s" % (template_scene)
            r += "\n  Output folder: %s" % (outpath)
            jobs.append(
                {
                    "modality": "Myelin",
                    "sinfo": sinfo,
                    "options": options,
                    "overwrite": overwrite,
                    "hcp": hcp,
                    "params": {
                        "run": True,
                        "template_scene": template_scene,
                        "outpath": outpath,
                        "qclog": qclog,
                        "timestamp": timestamp,
                        "on_existing": on_existing,
                        "scenezip": scenezip,
                    },
                }
            )

        elif modality == "general":
            template_scene = os.path.join(scenetemplatefolder, "template_general_qc.wb.scene")
            if not os.path.exists(template_scene):
                raise ge.CommandError("hcp_run_qc", f"Missing template scene: {template_scene}")

            datapath = _get_opt("qc_datapath", "datapath")
            datafile = _get_opt("qc_datafile", "datafile")
            if not datapath or not datafile:
                raise ge.CommandError(
                    "hcp_run_qc",
                    "general modality requires --qc_datapath and --qc_datafile (or legacy --datapath/--datafile).",
                )

            r += "\n- general: using template %s" % (template_scene)
            r += "\n  Output folder: %s" % (outpath)
            jobs.append(
                {
                    "modality": "general",
                    "sinfo": sinfo,
                    "options": options,
                    "overwrite": overwrite,
                    "hcp": hcp,
                    "params": {
                        "run": True,
                        "template_scene": template_scene,
                        "outpath": outpath,
                        "qclog": qclog,
                        "timestamp": timestamp,
                        "on_existing": on_existing,
                        "scenezip": scenezip,
                        "datapath": datapath,
                        "datafile": datafile,
                    },
                }
            )

        elif modality == "DWI":
            template_scene = os.path.join(scenetemplatefolder, "template_dwi_qc.wb.scene")
            if not os.path.exists(template_scene):
                raise ge.CommandError("hcp_run_qc", f"Missing template scene: {template_scene}")
            r += "\n- DWI: using template %s" % (template_scene)
            r += "\n  Output folder: %s" % (outpath)
            jobs.append(
                {
                    "modality": "DWI",
                    "sinfo": sinfo,
                    "options": options,
                    "overwrite": overwrite,
                    "hcp": hcp,
                    "params": {
                        "run": True,
                        "template_scene": template_scene,
                        "outpath": outpath,
                        "qclog": qclog,
                        "timestamp": timestamp,
                        "on_existing": on_existing,
                        "scenezip": scenezip,
                        "dwi_path": dwi_path,
                        "dwi_data": dwi_data,
                        "dwi_dtifit": dwi_dtifit,
                        "dwi_bedpostx": dwi_bedpostx,
                        "dwi_eddyqc": dwi_eddyqc,
                    },
                }
            )

        # user/custom scenes for non-BOLD modalities (BOLD is handled in its branch)
        if modality not in ("rawNII", "BOLD", "BOLD_FC"):
            for tmpl_path, tmpl_base in _qc_resolve_extra_templates(
                modality, scenetemplatefolder, studyfolder,
                userscenefile, userscenepath, processcustom,
            ):
                r += "\n- %s user/custom scene: %s" % (modality, tmpl_base)
                jobs.append(
                    {
                        "modality": "CUSTOM_SCENE",
                        "sinfo": sinfo,
                        "options": options,
                        "overwrite": overwrite,
                        "hcp": hcp,
                        "params": {
                            "run": True,
                            "template_scene": tmpl_path,
                            "template_basename": tmpl_base,
                            "modality_label": modality,
                            "outpath": outpath,
                            "qclog": qclog,
                            "timestamp": timestamp,
                            "on_existing": on_existing,
                            "scenezip": scenezip,
                        },
                    }
                )

    if omitdefaults == "yes":
        def _is_default_scene(job):
            m = job["modality"]
            if m in ("T1w", "T2w", "Myelin", "general", "DWI"):
                return True
            return m == "BOLD" and not job["params"].get("working_suffix")

        before = len(jobs)
        jobs = [j for j in jobs if not _is_default_scene(j)]
        r += "\n\n---> omitdefaults=yes: dropped %d default-scene job(s)." % (before - len(jobs))

    if len(jobs) == 0:
        r += "\n---> No QC jobs prepared."
    else:
        max_workers = max(1, min(int(options.get("parelements") or 1), len(jobs)))
        r += "\n\n%s %d QC jobs in parallel" % (pc.action("Running", options["run"]), max_workers)
        with ProcessPoolExecutor(max_workers) as processPoolExecutor:
            results = processPoolExecutor.map(_run_qc_executor, jobs)

        for result in results:
            r += result["r"]
            qc_report["done"] += result["report"]["done"]
            qc_report["failed"] += result["report"]["failed"]

    r += (
        "\n\nHCP run QC %s on %s\n---------------------------------------------------------"
        % (
            pc.action("completed", options["run"]),
            datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"),
        )
    )

    def _format_item_list(items):
        try:
            return "[" + ", ".join([str(x) for x in items]) + "]"
        except Exception:
            return "[]"

    failed_count = len(qc_report["failed"])
    status = "HCP run QC: done %d %s, failed %d %s" % (
        len(qc_report["done"]),
        _format_item_list(qc_report["done"]),
        failed_count,
        _format_item_list(qc_report["failed"]),
    )
    return (r, (sinfo["id"], status, failed_count))


def _run_qc_executor(job: dict):
    """Routes a single QC job to the relevant modality implementation."""
    modality = job.get("modality")
    sinfo = job.get("sinfo")
    options = job.get("options")
    overwrite = job.get("overwrite")
    hcp = job.get("hcp")
    params = job.get("params") or {}

    if modality == "rawNII":
        return _run_qc_rawnii(sinfo, options, overwrite, hcp, params)
    if modality == "BOLD":
        return _run_qc_bold(sinfo, options, overwrite, hcp, params)
    if modality == "BOLD_FC":
        return _run_qc_bold_fc(sinfo, options, overwrite, hcp, params)
    if modality == "T1w":
        return _run_qc_t1w(sinfo, options, overwrite, hcp, params)
    if modality == "T2w":
        return _run_qc_t2w(sinfo, options, overwrite, hcp, params)
    if modality == "Myelin":
        return _run_qc_myelin(sinfo, options, overwrite, hcp, params)
    if modality == "general":
        return _run_qc_general(sinfo, options, overwrite, hcp, params)
    if modality == "DWI":
        return _run_qc_dwi(sinfo, options, overwrite, hcp, params)
    if modality == "CUSTOM_SCENE":
        return _run_qc_custom_scene(sinfo, options, overwrite, hcp, params)

    raise ge.CommandError("hcp_run_qc", f"Unknown QC modality in job: {modality}")


def _copy_scene_for_zip(src: str, dst: str) -> None:
    """Copy a scene file to a zip staging location.

    Some mounted/bound filesystems reject setting atime/mtime (utime), which
    makes shutil.copy2() fail even though the file data copy succeeds.
    We fall back to copying contents only.
    """

    try:
        shutil.copy2(src, dst)
    except PermissionError:
        shutil.copyfile(src, dst)
    except OSError as e:
        if getattr(e, "errno", None) == errno.EPERM:
            shutil.copyfile(src, dst)
        else:
            raise


def _safe_copy(src: str, dst: str) -> None:
    """Copy a file with a fallback for restrictive filesystems.

    Prefer copy2() (preserve metadata), but fall back to copyfile() if metadata
    operations (utime/chmod) are not permitted.
    """

    try:
        shutil.copy2(src, dst)
    except PermissionError:
        shutil.copyfile(src, dst)
    except OSError as e:
        if getattr(e, "errno", None) == errno.EPERM:
            shutil.copyfile(src, dst)
        else:
            raise


def _stage_scene_for_zip(
    working_scene: str, base_dir: str, stage_dir: str, extra_replacements: dict = None
) -> str:
    """Create a temporary scene file for zipping.

    Workbench requires the scene file passed to `-zip-scene-file` to lie within
    `-base-dir`. Therefore `stage_dir` MUST be within `base_dir`.

    The staged scene replaces absolute `base_dir` paths with a relative prefix
    that is correct for the *staged scene location*. ``extra_replacements`` maps
    additional absolute paths (e.g. an out-of-tree BOLD-FC input folder) to the
    relative reference they should take in the staged scene.
    """

    base_dir_norm = os.path.normpath(base_dir)
    stage_dir_norm = os.path.normpath(stage_dir)

    # If stage_dir is inside base_dir, this will be '.' (staging at base) or '..'
    # (staging under base/qc), etc.
    rel_prefix = os.path.relpath(base_dir_norm, start=stage_dir_norm)
    if rel_prefix == ".":
        replacement = "."
    else:
        replacement = rel_prefix

    # Keep a normal Workbench scene filename so the file is openable by
    # double-click if it remains on disk (e.g., if cleanup fails due to FS perms).
    staged = os.path.join(stage_dir, os.path.basename(working_scene))
    with open(working_scene, "r", encoding="utf-8", errors="ignore") as f:
        st = f.read()

    for src_path, rel_target in (extra_replacements or {}).items():
        src_norm = os.path.normpath(src_path)
        st = st.replace(src_norm + os.sep, rel_target + os.sep)
        st = st.replace(src_norm, rel_target)

    # Replace both with and without trailing slash for robustness.
    st = st.replace(base_dir_norm + os.sep, replacement + os.sep)
    st = st.replace(base_dir_norm, replacement)

    with open(staged, "w", encoding="utf-8") as f:
        f.write(st)
    return staged


def _safe_unlink(path: str) -> None:
    """Best-effort unlink.

    On some shared/mounted filesystems, the process may be able to create/read a
    file but not delete it (permissions, ACLs, or user mapping). QC should not
    fail just because staging cleanup cannot delete the scene.
    """

    try:
        os.remove(path)
    except FileNotFoundError:
        return
    except PermissionError:
        return


def _write_qc_scene(template_scene: str, working_scene: str, substitutions: dict) -> None:
    """Render a working scene from a template by applying DUMMY* substitutions."""

    with open(template_scene, "r", encoding="utf-8", errors="ignore") as f:
        scene_txt = f.read()
    for token, value in substitutions.items():
        scene_txt = scene_txt.replace(token, value)
    with open(working_scene, "w", encoding="utf-8") as f:
        f.write(scene_txt)


def _show_scene_png(working_scene, png_out, qclog, thread, logtags, overwrite, desc, rr):
    """Render scene index 1 of ``working_scene`` to ``png_out`` at QC_SCENE_RES."""

    rr, _endlog, _status, _failed = pc.runExternalForFile(
        png_out,
        "wb_command -show-scene %s 1 %s %s" % (working_scene, png_out, QC_SCENE_RES),
        desc,
        overwrite=overwrite,
        thread=thread,
        task="hcp_run_qc_show_scene",
        logfolder=qclog,
        logtags=logtags,
        r=rr,
        shell=True,
    )
    return rr


def _render_scene_qc(
    template_scene,
    working_scene,
    substitutions,
    png_out,
    qclog,
    thread,
    logtags,
    overwrite,
    desc,
    rr,
):
    """Write a working scene and render its single QC png (scene index 1)."""

    _write_qc_scene(template_scene, working_scene, substitutions)
    return _show_scene_png(
        working_scene, png_out, qclog, thread, logtags, overwrite, desc, rr
    )


def _zip_qc_scene(
    working_scene, base_dir, qc_dir, outpath, timestamp, qclog, thread, logtags, rr
):
    """Stage, zip and copy a QC scene into the session/hcp ``qc`` folder.

    ``base_dir`` is the workbench zip base (paths are made relative to it);
    ``qc_dir`` is where the resulting zip is copied (must be within ``base_dir``).
    """

    os.makedirs(qc_dir, exist_ok=True)
    scene_for_zip = _stage_scene_for_zip(working_scene, base_dir, qc_dir)
    zip_out = os.path.join(
        outpath, "%s.%s.zip" % (os.path.basename(working_scene), timestamp)
    )
    try:
        rr, _endlog, _status, _failed = pc.runExternalForFile(
            zip_out,
            "cd %s && wb_command -zip-scene-file %s %s.%s %s -base-dir %s"
            % (
                outpath,
                scene_for_zip,
                os.path.basename(working_scene),
                timestamp,
                os.path.basename(zip_out),
                base_dir,
            ),
            "    ... zipping scene",
            overwrite=True,
            thread=thread,
            task="hcp_run_qc_zip_scene",
            logfolder=qclog,
            logtags=logtags,
            r=rr,
            shell=True,
        )
        _safe_copy(zip_out, os.path.join(qc_dir, os.path.basename(zip_out)))
    finally:
        _safe_unlink(scene_for_zip)
    return rr


def _rawnii_collect_sequences(nii_dir):
    """Read per-NIfTI QC info from JSON sidecars and NIfTI headers in ``nii_dir``.

    Returns a list of dicts (one per raw NIfTI) with name, file, TR, TE,
    resolution, in-plane dimensions and volume/direction count.
    """

    seqs = []
    niis = sorted(p for p in glob.glob(os.path.join(nii_dir, "*.nii*")) if not p.endswith(".json"))
    for path in niis:
        base = os.path.basename(path)
        stem = base
        for ext in (".nii.gz", ".nii"):
            if stem.endswith(ext):
                stem = stem[: -len(ext)]
                break
        info = {
            "file": base, "stem": stem, "name": stem,
            "tr": "n/a", "te": "n/a", "resolution": "n/a", "dims": "n/a", "nvol": "n/a",
        }

        jpath = os.path.join(nii_dir, stem + ".json")
        if os.path.exists(jpath):
            try:
                with open(jpath) as f:
                    j = json.load(f)
                info["name"] = j.get("SeriesDescription") or j.get("ProtocolName") or stem
                if "RepetitionTime" in j:
                    info["tr"] = "%.4g s" % float(j["RepetitionTime"])
                if "EchoTime" in j:
                    info["te"] = "%.4g s" % float(j["EchoTime"])
            except Exception:
                pass

        try:
            hdr = nib.load(path).header
            shp = hdr.get_data_shape()
            zooms = hdr.get_zooms()
            if len(shp) >= 3:
                info["dims"] = "%d x %d x %d" % (shp[0], shp[1], shp[2])
            info["nvol"] = shp[3] if len(shp) >= 4 else 1
            if len(zooms) >= 3:
                info["resolution"] = "%.3g x %.3g x %.3g mm" % (zooms[0], zooms[1], zooms[2])
            if info["tr"] == "n/a" and len(zooms) >= 4 and zooms[3] > 0:
                info["tr"] = "%.4g s" % zooms[3]
        except Exception:
            pass

        seqs.append(info)
    return seqs


def _rawnii_match_png(stem, pngs):
    """Best-effort match of a NIfTI stem to one of the slicesdir png paths."""

    for p in pngs:
        pb = os.path.basename(p)[:-4]
        for ext in (".nii.gz", ".nii"):
            if pb.endswith(ext):
                pb = pb[: -len(ext)]
        if pb == stem or stem in os.path.basename(p):
            return p
    return None


def _rawnii_html(session_id, timestamp, sequences, slicesdir):
    """Build a single self-contained HTML report embedding the slicesdir pngs."""

    def _b64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")

    def esc(v):
        return _html.escape(str(v))

    pngs = sorted(glob.glob(os.path.join(slicesdir, "*.png")))
    used = set()
    css = (
        "body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"
        "margin:0;padding:24px;background:#f5f6f8;color:#1b1f24}"
        "h1{font-size:20px;margin:0 0 4px}.meta{color:#586069;font-size:13px;margin-bottom:20px}"
        ".card{background:#fff;border:1px solid #e1e4e8;border-radius:8px;padding:16px;margin:0 0 18px}"
        ".card h2{font-size:15px;margin:0 0 10px}"
        "table.p{border-collapse:collapse;font-size:13px;margin:0 0 12px}"
        "table.p td{padding:2px 14px 2px 0;color:#24292e}table.p td.k{color:#586069;white-space:nowrap}"
        "img.slice{max-width:100%;height:auto;border:1px solid #e1e4e8;border-radius:4px}"
    )
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>%s raw NIfTI QC</title><style>%s</style></head><body>" % (esc(session_id), css),
        "<h1>Raw NIfTI QC &mdash; %s</h1>" % esc(session_id),
        "<div class='meta'>Generated %s &middot; %d sequence(s)</div>"
        % (esc(timestamp), len(sequences)),
    ]

    for seq in sequences:
        png = _rawnii_match_png(seq["stem"], pngs)
        img_html = ""
        if png:
            used.add(png)
            img_html = "<img class='slice' src='data:image/png;base64,%s' alt='%s'>" % (
                _b64(png), esc(seq["file"]))
        rows = "".join(
            "<tr><td class='k'>%s</td><td>%s</td></tr>" % (esc(k), esc(v))
            for k, v in (
                ("File", seq["file"]), ("TR", seq["tr"]), ("TE", seq["te"]),
                ("Resolution", seq["resolution"]), ("Dimensions (x, y, z)", seq["dims"]),
                ("Volumes / directions", seq["nvol"]),
            )
        )
        parts.append(
            "<div class='card'><h2>%s</h2><table class='p'>%s</table>%s</div>"
            % (esc(seq["name"]), rows, img_html))

    others = [p for p in pngs if p not in used]
    if others:
        parts.append("<div class='card'><h2>Other images</h2>")
        for p in others:
            parts.append(
                "<div style='margin-bottom:10px'><div class='meta'>%s</div>"
                "<img class='slice' src='data:image/png;base64,%s'></div>"
                % (esc(os.path.basename(p)), _b64(p)))
        parts.append("</div>")

    parts.append("</body></html>")
    return "\n".join(parts)


def _run_qc_rawnii(sinfo, options, overwrite, hcp, params: dict):
    rr = "\n\nWorking on: rawNII"
    report = {"done": [], "failed": []}

    run = params.get("run", True)
    outpath = params["outpath"]
    qclog = params["qclog"]
    timestamp = params["timestamp"]
    on_existing = params.get("on_existing", "leave")

    if not run:
        rr += "\n---> Skipping because session not ready."
        report["failed"].append("rawNII")
        return {"r": rr, "report": report}

    try:
        case = sinfo["id"]
        nii_dir = os.path.join(options["sessionsfolder"], case, "nii")
        zip_out = os.path.join(outpath, "%s.RawNII.QC.zip" % case)
        html_out = os.path.join(outpath, "%s.RawNII.QC.html" % case)

        skip, rr = _apply_on_existing(
            on_existing,
            [os.path.join(outpath, "%s.RawNII.QC.*" % case)],
            "rawNII",
            rr,
        )
        if skip:
            report["done"].append("rawNII")
            return {"r": rr, "report": report}

        if not os.path.isdir(nii_dir):
            rr += "\n---> ERROR: raw NIFTI folder not found: %s" % nii_dir
            report["failed"].append("rawNII")
            return {"r": rr, "report": report}

        slicesdir = os.path.join(nii_dir, "slicesdir")
        index_html = os.path.join(slicesdir, "index.html")

        rr, _endlog, _status, _failed = pc.runExternalForFile(
            index_html,
            "cd %s && slicesdir *.nii*" % nii_dir,
            "    ... running slicesdir on raw NIFTIs",
            overwrite=True,
            thread=sinfo["id"],
            task="hcp_run_qc_rawnii",
            logfolder=qclog,
            logtags=["rawNII"],
            r=rr,
            shell=True,
        )

        if not os.path.exists(index_html):
            rr += "\n---> ERROR: slicesdir did not produce %s" % index_html
            report["failed"].append("rawNII")
            return {"r": rr, "report": report}

        # zip the raw slicesdir output (pngs + index.html)
        _safe_unlink(zip_out)
        with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(glob.glob(os.path.join(slicesdir, "*"))):
                if os.path.isfile(f):
                    zf.write(f, os.path.basename(f))

        # build a self-contained html report (embedded pngs + sequence parameters)
        sequences = _rawnii_collect_sequences(nii_dir)
        with open(html_out, "w", encoding="utf-8") as f:
            f.write(_rawnii_html(case, timestamp, sequences, slicesdir))

        if os.path.isdir(slicesdir):
            shutil.rmtree(slicesdir, ignore_errors=True)

        rr += "\n    ... raw NIFTI QC written to %s and %s" % (zip_out, html_out)
        report["done"].append("rawNII")
        return {"r": rr, "report": report}

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        rr += str(errormessage)
        report["failed"].append("rawNII")
        return {"r": rr, "report": report}
    except Exception:
        rr += "\nERROR: Unknown error occured:\n...................................\n"
        rr += traceback.format_exc()
        rr += "\n...................................\n"
        report["failed"].append("rawNII")
        return {"r": rr, "report": report}


def _dwi_derived_scene(
    base_scene,
    derived_scene,
    swaps,
    png_out,
    base_dir,
    qc_dir,
    outpath,
    timestamp,
    qclog,
    thread,
    logtags,
    scenezip,
    overwrite,
    desc,
    rr,
):
    """Copy the base DWI scene, apply text swaps, render, and (optionally) zip."""

    with open(base_scene, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read()
    for a, b in swaps.items():
        txt = txt.replace(a, b)
    with open(derived_scene, "w", encoding="utf-8") as f:
        f.write(txt)

    rr = _show_scene_png(
        derived_scene, png_out, qclog, thread, logtags, overwrite, desc, rr
    )
    if scenezip == "yes":
        rr = _zip_qc_scene(
            derived_scene, base_dir, qc_dir, outpath, timestamp, qclog, thread, logtags, rr
        )
    return rr


def _run_qc_dwi_dtifit(
    dwidir, working_scene, case_name, base_dir, qc_dir, outpath, timestamp,
    qclog, thread, scenezip, overwrite, rr,
):
    """dtifit sub-QC: requires dti_FA.nii.gz; renders a dtifit variant scene."""

    fa = os.path.join(dwidir, "dti_FA.nii.gz")
    if not (os.path.exists(fa) and os.path.getsize(fa) > 100000):
        return rr + "\n---> WARNING: FSL dtifit not found (dti_FA.nii.gz); skipping dtifit QC."

    dti_scene = os.path.join(outpath, "%s.DWI.dtifit.QC.wb.scene" % case_name)
    dti_png = os.path.join(outpath, "%s.%s.png" % (os.path.basename(dti_scene), timestamp))
    return _dwi_derived_scene(
        working_scene,
        dti_scene,
        {
            "1st frame": "dti FA",
            "10th frame": "dti L3",
            "data_frame1_brain.nii.gz": "dti_FA.nii.gz",
            "data_frame10_brain.nii.gz": "dti_L3.nii.gz",
        },
        dti_png,
        base_dir,
        qc_dir,
        outpath,
        timestamp,
        qclog,
        thread,
        ["DWI", "dtifit"],
        scenezip,
        overwrite,
        "    ... rendering DWI dtifit QC png",
        rr,
    )


def _run_qc_dwi_bedpostx(
    hcp, dwi_path, working_scene, case_name, base_dir, qc_dir, outpath, timestamp,
    qclog, thread, scenezip, overwrite, rr,
):
    """BedpostX sub-QC: requires a complete Diffusion.bedpostX; renders a variant scene."""

    bpx = os.path.join(hcp["T1w_folder"], "Diffusion.bedpostX")
    f1 = os.path.join(bpx, "merged_f1samples.nii.gz")
    merged = glob.glob(os.path.join(bpx, "merged_*nii.gz"))
    if not (os.path.exists(f1) and len(merged) == 9 and os.path.getsize(f1) >= 20000000):
        return rr + "\n---> WARNING: FSL BedpostX outputs missing or incomplete; skipping BedpostX QC."

    bpx_scene = os.path.join(outpath, "%s.DWI.bedpostx.QC.wb.scene" % case_name)
    bpx_png = os.path.join(outpath, "%s.%s.png" % (os.path.basename(bpx_scene), timestamp))
    return _dwi_derived_scene(
        working_scene,
        bpx_scene,
        {
            "1st frame": "mean d diffusivity",
            "10th frame": "mean f anisotropy",
            "%s/data_frame1_brain.nii.gz" % dwi_path: "Diffusion.bedpostX/mean_dsamples.nii.gz",
            "%s/data_frame10_brain.nii.gz" % dwi_path: "Diffusion.bedpostX/mean_fsumsamples.nii.gz",
        },
        bpx_png,
        base_dir,
        qc_dir,
        outpath,
        timestamp,
        qclog,
        thread,
        ["DWI", "bedpostx"],
        scenezip,
        overwrite,
        "    ... rendering DWI bedpostx QC png",
        rr,
    )


def _run_qc_dwi_eddy(hcp, case_name, outpath, timestamp, rr):
    """EDDY QC stats: hard-link qc.pdf into the QC folder and record qc_mot_abs."""

    eddy_qc = os.path.join(hcp["base"], "Diffusion", "eddy", "eddy_unwarped_images.qc")
    qc_pdf = os.path.join(eddy_qc, "qc.pdf")
    if not os.path.exists(qc_pdf):
        return rr + "\n---> WARNING: EDDY QC outputs missing (%s); skipping EDDY QC." % qc_pdf

    mot_abs = os.path.join(eddy_qc, "%s_qc_mot_abs.txt" % case_name)
    if not os.path.exists(mot_abs):
        try:
            with open(os.path.join(eddy_qc, "qc.json")) as f:
                val = json.load(f).get("qc_mot_abs")
            with open(mot_abs, "w") as f:
                f.write("%s\n" % val)
        except Exception:
            rr += "\n---> WARNING: could not regenerate %s" % mot_abs

    eddy_pdf_dst = os.path.join(outpath, "%s.DWI.eddy.QC.pdf" % case_name)
    _safe_unlink(eddy_pdf_dst)
    try:
        os.link(qc_pdf, eddy_pdf_dst)
    except OSError:
        _safe_copy(qc_pdf, eddy_pdf_dst)

    report_txt = os.path.join(outpath, "EddyQCReport_qc_mot_abs_%s.txt" % timestamp)
    with open(report_txt, "a") as f:
        f.write("%s\n" % mot_abs)
    rr += "\n    ... EDDY QC linked to %s; motion recorded in %s" % (eddy_pdf_dst, report_txt)
    return rr


def _run_qc_custom_scene(sinfo, options, overwrite, hcp, params: dict):
    """Render a user-supplied or custom QC scene (non-BOLD, generic substitutions)."""

    modality = params["modality_label"]
    template_scene = params["template_scene"]
    template_basename = params["template_basename"]
    rr = "\n\nWorking on %s user/custom scene: %s" % (modality, template_basename)
    report = {"done": [], "failed": []}

    run = params.get("run", True)
    outpath = params["outpath"]
    qclog = params["qclog"]
    timestamp = params["timestamp"]
    scenezip = (params.get("scenezip", "yes") or "yes").strip().lower()
    on_existing = params.get("on_existing", "leave")
    label = "%s:%s" % (modality, template_basename)

    if not run:
        rr += "\n---> Skipping because session not ready."
        report["failed"].append(label)
        return {"r": rr, "report": report}

    try:
        case_name = "%s%s" % (sinfo["id"], options["hcp_suffix"])
        if not os.path.exists(template_scene):
            rr += "\n---> ERROR: scene template not found: %s" % template_scene
            report["failed"].append(label)
            return {"r": rr, "report": report}

        ok, rr = _dummy_variable_check(
            template_scene, ["DUMMYPATH", "DUMMYCASE", "DUMMYTIMESTAMP"], rr
        )
        if not ok:
            report["failed"].append(label)
            return {"r": rr, "report": report}

        working_scene = os.path.join(
            outpath, "%s.%s.%s" % (case_name, modality, template_basename)
        )
        skip, rr = _apply_on_existing(
            on_existing,
            [os.path.join(outpath, "%s.%s.%s*" % (case_name, modality, template_basename))],
            label,
            rr,
        )
        if skip:
            report["done"].append(label)
            return {"r": rr, "report": report}

        png_name = "%s.png" % os.path.basename(working_scene)
        png_out = os.path.join(outpath, "%s.%s.png" % (os.path.basename(working_scene), timestamp))
        rr = _render_scene_qc(
            template_scene,
            working_scene,
            {
                "DUMMYPATH": hcp["base"],
                "DUMMYCASE": case_name,
                "DUMMYTIMESTAMP": timestamp,
                "DUMMYPNGNAME": png_name,
            },
            png_out,
            qclog,
            sinfo["id"],
            [modality, "custom"],
            overwrite,
            "    ... rendering %s user/custom scene" % modality,
            rr,
        )
        if scenezip == "yes":
            rr = _zip_qc_scene(
                working_scene, hcp["base"], os.path.join(hcp["base"], "qc"),
                outpath, timestamp, qclog, sinfo["id"], [modality, "custom"], rr,
            )

        report["done"].append(label)
        return {"r": rr, "report": report}

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        rr += str(errormessage)
        report["failed"].append(label)
        return {"r": rr, "report": report}
    except Exception:
        rr += "\nERROR: Unknown error occured:\n...................................\n"
        rr += traceback.format_exc()
        rr += "\n...................................\n"
        report["failed"].append(label)
        return {"r": rr, "report": report}


def _run_qc_dwi_prep(dwidir, dwi_data, dwi_nii, mask, qclog, thread, overwrite, rr):
    """Split off DWI volumes 0 and 10, mask them, and drop the split volumes."""

    frame1 = os.path.join(dwidir, "data_frame1_brain.nii.gz")
    frame10 = os.path.join(dwidir, "data_frame10_brain.nii.gz")
    split_prefix = os.path.join(dwidir, "%s_split" % dwi_data)
    prep_cmd = (
        "fslsplit %s %s -t && "
        "fslmaths %s0000.nii.gz -mul %s %s && "
        "fslmaths %s0010.nii.gz -mul %s %s && "
        "rm -f %s*"
    ) % (
        dwi_nii, split_prefix,
        split_prefix, mask, frame1[:-7],
        split_prefix, mask, frame10[:-7],
        split_prefix,
    )
    rr, _e, _s, _f = pc.runExternalForFile(
        frame10,
        prep_cmd,
        "    ... preparing DWI QC frames",
        overwrite=overwrite,
        thread=thread,
        task="hcp_run_qc_dwi_prep",
        logfolder=qclog,
        logtags=["DWI"],
        r=rr,
        shell=True,
    )
    return rr


def _run_qc_dwi_base(
    template_scene, working_scene, case_name, base_dir, qc_dir, dwi_path,
    outpath, timestamp, qclog, thread, scenezip, overwrite, rr,
):
    """Render the base DWI QC scene and (optionally) zip it."""

    png_name = "%s.png" % os.path.basename(working_scene)
    png_out = os.path.join(outpath, "%s.%s.png" % (os.path.basename(working_scene), timestamp))
    rr = _render_scene_qc(
        template_scene,
        working_scene,
        {
            "DUMMYPATH": base_dir,
            "DUMMYCASE": case_name,
            "DUMMYDWIPATH": dwi_path,
            "DUMMYTIMESTAMP": timestamp,
            "DUMMYPNGNAME": png_name,
        },
        png_out,
        qclog,
        thread,
        ["DWI"],
        overwrite,
        "    ... rendering DWI QC png",
        rr,
    )
    if scenezip == "yes":
        rr = _zip_qc_scene(
            working_scene, base_dir, qc_dir, outpath, timestamp, qclog, thread, ["DWI"], rr
        )
    return rr


def _run_qc_dwi(sinfo, options, overwrite, hcp, params: dict):
    rr = "\n\nWorking on: DWI"
    report = {"done": [], "failed": []}

    run = params.get("run", True)
    template_scene = params["template_scene"]
    outpath = params["outpath"]
    qclog = params["qclog"]
    timestamp = params["timestamp"]
    scenezip = (params.get("scenezip", "yes") or "yes").strip().lower()
    on_existing = params.get("on_existing", "leave")
    dwi_path = params.get("dwi_path", "Diffusion")
    dwi_data = params.get("dwi_data", "data")
    dwi_dtifit = (params.get("dwi_dtifit", "no") or "no").strip().lower()
    dwi_bedpostx = (params.get("dwi_bedpostx", "no") or "no").strip().lower()
    dwi_eddyqc = (params.get("dwi_eddyqc", "no") or "no").strip().lower()

    if not run:
        rr += "\n---> Skipping because session not ready."
        report["failed"].append("DWI")
        return {"r": rr, "report": report}

    try:
        case_name = "%s%s" % (sinfo["id"], options["hcp_suffix"])
        base_dir = hcp["base"]
        qc_dir = os.path.join(base_dir, "qc")
        dwidir = os.path.join(hcp["T1w_folder"], dwi_path)
        dwi_nii = os.path.join(dwidir, "%s.nii.gz" % dwi_data)
        mask = os.path.join(dwidir, "nodif_brain_mask.nii.gz")

        skip, rr = _apply_on_existing(
            on_existing,
            [os.path.join(outpath, "%s.DWI.*" % case_name)],
            "DWI",
            rr,
        )
        if skip:
            report["done"].append("DWI")
            return {"r": rr, "report": report}

        if not os.path.exists(dwi_nii):
            rr += "\n---> ERROR: Preprocessed DWI data not found: %s" % dwi_nii
            report["failed"].append("DWI")
            return {"r": rr, "report": report}

        rr = _run_qc_dwi_prep(
            dwidir, dwi_data, dwi_nii, mask, qclog, sinfo["id"], overwrite, rr
        )

        working_scene = os.path.join(outpath, "%s.DWI.QC.wb.scene" % case_name)
        rr = _run_qc_dwi_base(
            template_scene, working_scene, case_name, base_dir, qc_dir, dwi_path,
            outpath, timestamp, qclog, sinfo["id"], scenezip, overwrite, rr,
        )

        if dwi_dtifit == "yes":
            rr = _run_qc_dwi_dtifit(
                dwidir, working_scene, case_name, base_dir, qc_dir, outpath,
                timestamp, qclog, sinfo["id"], scenezip, overwrite, rr,
            )
        if dwi_bedpostx == "yes":
            rr = _run_qc_dwi_bedpostx(
                hcp, dwi_path, working_scene, case_name, base_dir, qc_dir, outpath,
                timestamp, qclog, sinfo["id"], scenezip, overwrite, rr,
            )
        if dwi_eddyqc == "yes":
            rr = _run_qc_dwi_eddy(hcp, case_name, outpath, timestamp, rr)

        report["done"].append("DWI")
        return {"r": rr, "report": report}

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        rr += str(errormessage)
        report["failed"].append("DWI")
        return {"r": rr, "report": report}
    except Exception:
        rr += "\nERROR: Unknown error occured:\n...................................\n"
        rr += traceback.format_exc()
        rr += "\n...................................\n"
        report["failed"].append("DWI")
        return {"r": rr, "report": report}


def _zip_bold_fc_scene(
    working_scene, base_dir, boldfcpath, fc_src, fc_name, outpath, timestamp,
    qclog, thread, logtags, rr,
):
    """Zip a BOLD-FC scene: copy the FC input into <base>/qc and rewrite its path.

    Unlike the structural modalities, the FC input lives outside the HCP tree, so
    it is copied alongside the staged scene (in <base>/qc) and its absolute path is
    rewritten to '.' so the zipped scene is self-contained.
    """

    qc_dir = os.path.join(base_dir, "qc")
    os.makedirs(qc_dir, exist_ok=True)
    if os.path.exists(fc_src):
        _safe_copy(fc_src, os.path.join(qc_dir, fc_name))

    scene_for_zip = _stage_scene_for_zip(
        working_scene, base_dir, qc_dir, extra_replacements={boldfcpath: "."}
    )
    zip_out = os.path.join(
        outpath, "%s.%s.zip" % (os.path.basename(working_scene), timestamp)
    )
    try:
        rr, _e, _s, _f = pc.runExternalForFile(
            zip_out,
            "cd %s && wb_command -zip-scene-file %s %s.%s %s -base-dir %s"
            % (
                outpath,
                scene_for_zip,
                os.path.basename(working_scene),
                timestamp,
                os.path.basename(zip_out),
                base_dir,
            ),
            "    ... zipping FC scene",
            overwrite=True,
            thread=thread,
            task="hcp_run_qc_zip_scene",
            logfolder=qclog,
            logtags=logtags,
            r=rr,
            shell=True,
        )
        _safe_copy(zip_out, os.path.join(qc_dir, os.path.basename(zip_out)))
    finally:
        _safe_unlink(scene_for_zip)
    return rr


def _run_qc_bold_fc(sinfo, options, overwrite, hcp, params: dict):
    boldinfo = params["boldinfo"]
    rr = "\n\nWorking on BOLD FC: %s" % boldinfo["name"]
    report = {"done": [], "failed": []}

    run = params.get("run", True)
    template_scene = params["template_scene"]
    outpath = params["outpath"]
    qclog = params["qclog"]
    timestamp = params["timestamp"]
    scenezip = (params.get("scenezip", "yes") or "yes").strip().lower()
    on_existing = params.get("on_existing", "leave")
    bold_fc = params["bold_fc"]
    bold_fc_input = params["bold_fc_input"]
    bold_fc_path = params.get("bold_fc_path") or ""

    if not run:
        rr += "\n---> Skipping because session not ready."
        report["failed"].append(boldinfo["name"])
        return {"r": rr, "report": report}

    try:
        bold_num = str(boldinfo["bold_number"])
        report_label = "BOLD%s_%s" % (bold_num, bold_fc)
        case_name = "%s%s" % (sinfo["id"], options["hcp_suffix"])

        if not bold_fc_path:
            bold_fc_path = os.path.join(
                options["sessionsfolder"], sinfo["id"], "images", "functional"
            )
        fc_name = "bold%s_%s" % (bold_num, bold_fc_input)
        fc_src = os.path.join(bold_fc_path, fc_name)

        working_scene = os.path.join(
            outpath, "%s.%s.BOLD.%s.QC.wb.scene" % (case_name, bold_fc, bold_num)
        )

        skip, rr = _apply_on_existing(
            on_existing,
            [os.path.join(outpath, "%s.%s.BOLD.%s.*" % (case_name, bold_fc, bold_num))],
            report_label,
            rr,
        )
        if skip:
            report["done"].append(report_label)
            return {"r": rr, "report": report}

        if not os.path.exists(fc_src):
            rr += "\n---> ERROR: BOLD FC input not found: %s" % fc_src
            report["failed"].append(report_label)
            return {"r": rr, "report": report}

        png_out = os.path.join(
            outpath, "%s.%s.png" % (os.path.basename(working_scene), timestamp)
        )
        rr = _render_scene_qc(
            template_scene,
            working_scene,
            {
                "DUMMYPATH": hcp["base"],
                "DUMMYCASE": case_name,
                "DUMMYTIMESTAMP": timestamp,
                "DUMMYIMAGEPATH": bold_fc_path,
                "DUMMYIMAGEFILE": fc_name,
                "DUMMYPNGNAME": os.path.basename(png_out),
            },
            png_out,
            qclog,
            sinfo["id"],
            ["BOLD", "FC", bold_fc],
            overwrite,
            "    ... rendering BOLD FC QC png",
            rr,
        )
        if scenezip == "yes":
            rr = _zip_bold_fc_scene(
                working_scene, hcp["base"], bold_fc_path, fc_src, fc_name,
                outpath, timestamp, qclog, sinfo["id"], ["BOLD", "FC", bold_fc], rr,
            )

        report["done"].append(report_label)
        return {"r": rr, "report": report}

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        rr += str(errormessage)
        report["failed"].append(boldinfo["name"])
        return {"r": rr, "report": report}
    except Exception:
        rr += "\nERROR: Unknown error occured:\n...................................\n"
        rr += traceback.format_exc()
        rr += "\n...................................\n"
        report["failed"].append(boldinfo["name"])
        return {"r": rr, "report": report}


def _run_qc_bold(sinfo, options, overwrite, hcp, params: dict):
    boldinfo = params["boldinfo"]
    rr = "\n\nWorking on: %s" % (boldinfo["name"])
    report = {"done": [], "failed": []}

    run = params.get("run", True)
    template_scene = params["template_scene"]
    outpath = params["outpath"]
    qclog = params["qclog"]
    timestamp = params["timestamp"]
    hcp_bold_prefix = params.get("hcp_bold_prefix", "") or ""
    hcp_cifti_tail = params.get("hcp_cifti_tail", "") or ""
    scenezip = (params.get("scenezip", "yes") or "yes").strip().lower()
    snronly = (params.get("snronly", "no") or "no").strip().lower()
    skipframes = int(params.get("skipframes", 0) or 0)
    on_existing = params.get("on_existing", "leave")
    working_suffix = params.get("working_suffix", "QC.wb.scene")

    if not run:
        rr += "\n---> Skipping because session not ready."
        report["failed"].append(boldinfo["name"])
        return {"r": rr, "report": report}

    def _run_capture(cmd: str) -> str:
        return subprocess.check_output(cmd, shell=True, text=True).strip()

    def _infer_suffix(bold_name: str) -> str:
        candidates = sorted(
            glob.glob(
                os.path.join(
                    hcp["hcp_nonlin"],
                    "Results",
                    bold_name,
                    f"{bold_name}*.dtseries.nii",
                )
            )
        )
        if not candidates:
            return ""
        base = os.path.basename(candidates[0])
        stem = base.replace(".dtseries.nii", "")
        if stem == bold_name:
            return ""
        if stem.startswith(bold_name + "_"):
            return stem[len(bold_name) + 1 :]
        return ""

    try:
        bold_num = str(boldinfo["bold_number"])

        # HCP-style BOLD naming (matches use elsewhere in this module)
        if "filename" in boldinfo and options.get("hcp_filename") == "userdefined":
            bold_name = boldinfo["filename"]
            report_label = bold_name
        else:
            bold_name = f"{hcp_bold_prefix}{bold_num}" if hcp_bold_prefix else bold_num
            report_label = f"BOLD{bold_num}"

        # Template scene expects DUMMYBOLDSUFFIX *without* leading underscore because
        # it already inserts an underscore between DUMMYBOLDDATA and DUMMYBOLDSUFFIX.
        # HCP tail parameters typically come in with a leading underscore (e.g. _Atlas).
        suffix = ""
        if hcp_cifti_tail:
            suffix = str(hcp_cifti_tail)
            if suffix.startswith("_"):
                suffix = suffix[1:]
        if suffix == "":
            suffix = _infer_suffix(bold_name)

        dtstem = bold_name if suffix == "" else f"{bold_name}_{suffix}"

        case_name = "%s%s" % (sinfo["id"], options["hcp_suffix"])
        skip, rr = _apply_on_existing(
            on_existing,
            [
                os.path.join(outpath, "%s.BOLD.%s.*" % (case_name, bold_name)),
                os.path.join(outpath, "%s_%s_TSNR_Report_*" % (sinfo["id"], bold_name)),
            ],
            report_label,
            rr,
        )
        if skip:
            report["done"].append(report_label)
            return {"r": rr, "report": report}

        dtseries = os.path.join(
            hcp["hcp_nonlin"], "Results", bold_name, f"{dtstem}.dtseries.nii"
        )
        bold_nifti = os.path.join(
            hcp["hcp_nonlin"], "Results", bold_name, f"{bold_name}.nii.gz"
        )

        if not os.path.exists(dtseries):
            rr += "\n---> ERROR: missing dtseries: %s" % (dtseries)
            report["failed"].append(report_label)
            return {"r": rr, "report": report}

        tsnr_dscalar = os.path.join(
            hcp["hcp_nonlin"], "Results", bold_name, f"{dtstem}_TSNR.dscalar.nii"
        )
        gs_dtseries = os.path.join(
            hcp["hcp_nonlin"], "Results", bold_name, f"{dtstem}_GS.dtseries.nii"
        )
        gs_txt = os.path.join(hcp["hcp_nonlin"], "Results", bold_name, f"{dtstem}_GS.txt")
        gs_sdseries = os.path.join(
            hcp["hcp_nonlin"], "Results", bold_name, f"{dtstem}_GS.sdseries.nii"
        )

        rr, endlog, status, failed = pc.runExternalForFile(
            tsnr_dscalar,
            "wb_command -cifti-reduce %s TSNR %s -exclude-outliers 4 4" % (dtseries, tsnr_dscalar),
            "    ... computing TSNR for %s" % (dtstem),
            overwrite=overwrite,
            thread=sinfo["id"],
            task="hcp_run_qc_tsnr",
            logfolder=qclog,
            logtags=["BOLD", "B%s" % bold_num],
            r=rr,
            shell=True,
        )

        tsnr_mean = _run_capture("wb_command -cifti-stats %s -reduce MEAN" % tsnr_dscalar)

        rr, endlog, status, failed = pc.runExternalForFile(
            gs_dtseries,
            "wb_command -cifti-reduce %s MEAN %s -direction COLUMN" % (dtseries, gs_dtseries),
            "    ... computing global-signal dtseries",
            overwrite=overwrite,
            thread=sinfo["id"],
            task="hcp_run_qc_gs_reduce",
            logfolder=qclog,
            logtags=["BOLD", "B%s" % bold_num],
            r=rr,
            shell=True,
        )

        rr, endlog, status, failed = pc.runExternalForFile(
            gs_txt,
            "wb_command -cifti-stats %s -reduce MEAN > %s" % (gs_dtseries, gs_txt),
            "    ... writing global-signal txt",
            overwrite=True,
            thread=sinfo["id"],
            task="hcp_run_qc_gs_txt",
            logfolder=qclog,
            logtags=["BOLD", "B%s" % bold_num],
            r=rr,
            shell=True,
        )

        if os.path.exists(bold_nifti):
            tr_sec = float(_run_capture("fslval %s pixdim4" % bold_nifti))
            nvol = int(_run_capture("fslval %s dim4" % bold_nifti))
        else:
            tr_sec = 1.0
            with open(gs_txt, "r") as f:
                nvol = len([ln for ln in f.read().splitlines() if ln.strip()])

        xmax = max(0, nvol - max(0, skipframes))

        with open(gs_txt, "r") as f:
            vals = []
            for ln in f.read().splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    vals.append(float(ln))
                except ValueError:
                    pass
        vals = vals[skipframes:] if skipframes > 0 else vals
        ymin = min(vals) if vals else 0.0
        ymax = max(vals) if vals else 1.0

        rr, endlog, status, failed = pc.runExternalForFile(
            gs_sdseries,
            "wb_command -cifti-create-scalar-series %s %s -transpose -series SECOND 0 %s"
            % (gs_txt, gs_sdseries, tr_sec),
            "    ... creating GS scalar series",
            overwrite=overwrite,
            thread=sinfo["id"],
            task="hcp_run_qc_gs_sdseries",
            logfolder=qclog,
            logtags=["BOLD", "B%s" % bold_num],
            r=rr,
            shell=True,
        )

        tsnr_report_bold = os.path.join(
            outpath, "%s_%s_TSNR_Report_%s.txt" % (sinfo["id"], bold_name, timestamp)
        )
        with open(tsnr_report_bold, "w") as f:
            f.write("%s: %s\n" % (tsnr_dscalar, tsnr_mean))

        rr += "\n    ... TSNR(mean)=%s written to %s" % (tsnr_mean, tsnr_report_bold)

        if snronly == "yes":
            rr += "\n    ... qc_bold_snronly=yes, skipping scene/png."
            report["done"].append(report_label)
            return {"r": rr, "report": report}

        working_scene = os.path.join(
            outpath,
            "%s%s.BOLD.%s.%s"
            % (sinfo["id"], options["hcp_suffix"], bold_name, working_suffix),
        )
        with open(template_scene, "r", encoding="utf-8", errors="ignore") as f:
            scene_txt = f.read()

        scene_txt = scene_txt.replace("DUMMYPATH", hcp["base"])
        scene_txt = scene_txt.replace("DUMMYCASE", "%s%s" % (sinfo["id"], options["hcp_suffix"]))
        scene_txt = scene_txt.replace("DUMMYBOLDDATA", bold_name)
        scene_txt = scene_txt.replace("DUMMYBOLDSUFFIX", suffix)
        scene_txt = scene_txt.replace("DUMMYTIMESTAMP", timestamp)
        scene_txt = scene_txt.replace("DUMMYBOLDANNOT", bold_name)
        scene_txt = scene_txt.replace("DUMMYXAXISMAX", str(float(xmax)))
        scene_txt = scene_txt.replace("DUMMYYAXISMIN", str(float(ymin)))
        scene_txt = scene_txt.replace("DUMMYYAXISMAX", str(float(ymax)))

        png_gsmap_name = "%s.%s.GSmap.QC.wb.png" % (os.path.basename(working_scene), timestamp)
        png_gstime_name = "%s.%s.GStimeseries.QC.wb.png" % (
            os.path.basename(working_scene),
            timestamp,
        )
        scene_txt = scene_txt.replace("DUMMYPNGNAMEGSMAP", png_gsmap_name)
        scene_txt = scene_txt.replace("DUMMYPNGNAMEGSTIME", png_gstime_name)

        with open(working_scene, "w", encoding="utf-8") as f:
            f.write(scene_txt)

        png_gsmap = os.path.join(outpath, png_gsmap_name)
        png_gstime = os.path.join(outpath, png_gstime_name)

        rr, endlog, status, failed = pc.runExternalForFile(
            png_gsmap,
            "wb_command -show-scene %s 1 %s %s" % (working_scene, png_gsmap, QC_SCENE_RES),
            "    ... rendering GS map png",
            overwrite=overwrite,
            thread=sinfo["id"],
            task="hcp_run_qc_show_scene",
            logfolder=qclog,
            logtags=["BOLD", "B%s" % bold_num, "GSmap"],
            r=rr,
            shell=True,
        )
        rr, endlog, status, failed = pc.runExternalForFile(
            png_gstime,
            "wb_command -show-scene %s 2 %s %s" % (working_scene, png_gstime, QC_SCENE_RES),
            "    ... rendering GS timeseries png",
            overwrite=overwrite,
            thread=sinfo["id"],
            task="hcp_run_qc_show_scene",
            logfolder=qclog,
            logtags=["BOLD", "B%s" % bold_num, "GStime"],
            r=rr,
            shell=True,
        )

        if scenezip == "yes":
            rr = _zip_qc_scene(
                working_scene,
                hcp["base"],
                os.path.join(hcp["base"], "qc"),
                outpath,
                timestamp,
                qclog,
                sinfo["id"],
                ["BOLD", "B%s" % bold_num],
                rr,
            )

        report["done"].append(report_label)
        return {"r": rr, "report": report}

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        rr += str(errormessage)
        report["failed"].append(boldinfo["name"])
        return {"r": rr, "report": report}
    except Exception:
        rr += "\nERROR: Unknown error occured:\n...................................\n"
        rr += traceback.format_exc()
        rr += "\n...................................\n"
        report["failed"].append(boldinfo["name"])
        return {"r": rr, "report": report}


def _run_qc_t1w(sinfo, options, overwrite, hcp, params: dict):
    rr = "\n\nWorking on: T1w"
    report = {"done": [], "failed": []}

    run = params.get("run", True)
    template_scene = params["template_scene"]
    outpath = params["outpath"]
    qclog = params["qclog"]
    timestamp = params["timestamp"]
    scenezip = (params.get("scenezip", "yes") or "yes").strip().lower()
    on_existing = params.get("on_existing", "leave")

    if not run:
        rr += "\n---> Skipping because session not ready."
        report["failed"].append("T1w")
        return {"r": rr, "report": report}

    try:
        case_name = f"{sinfo['id']}{options['hcp_suffix']}"

        skip, rr = _apply_on_existing(
            on_existing,
            [os.path.join(outpath, f"{case_name}.T1w.*")],
            "T1w",
            rr,
        )
        if skip:
            report["done"].append("T1w")
            return {"r": rr, "report": report}

        t1w_restore = os.path.join(hcp["hcp_nonlin"], "T1w_restore.nii.gz")
        if not os.path.exists(t1w_restore):
            rr += "\n---> ERROR: Preprocessed T1w data not found: %s" % t1w_restore
            report["failed"].append("T1w")
            return {"r": rr, "report": report}

        working_scene = os.path.join(outpath, f"{case_name}.T1w.QC.wb.scene")
        png_name = f"{os.path.basename(working_scene)}.png"
        png_out = os.path.join(outpath, f"{os.path.basename(working_scene)}.{timestamp}.png")

        rr = _render_scene_qc(
            template_scene,
            working_scene,
            {
                "DUMMYPATH": hcp["base"],
                "DUMMYCASE": case_name,
                "DUMMYTIMESTAMP": timestamp,
                "DUMMYPNGNAME": png_name,
            },
            png_out,
            qclog,
            sinfo["id"],
            ["T1w"],
            overwrite,
            "    ... rendering T1w QC png",
            rr,
        )

        if scenezip == "yes":
            rr = _zip_qc_scene(
                working_scene,
                hcp["base"],
                os.path.join(hcp["base"], "qc"),
                outpath,
                timestamp,
                qclog,
                sinfo["id"],
                ["T1w"],
                rr,
            )

        report["done"].append("T1w")
        return {"r": rr, "report": report}

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        rr += str(errormessage)
        report["failed"].append("T1w")
        return {"r": rr, "report": report}
    except Exception:
        rr += "\nERROR: Unknown error occured:\n...................................\n"
        rr += traceback.format_exc()
        rr += "\n...................................\n"
        report["failed"].append("T1w")
        return {"r": rr, "report": report}


def _run_qc_t2w(sinfo, options, overwrite, hcp, params: dict):
    rr = "\n\nWorking on: T2w"
    report = {"done": [], "failed": []}

    run = params.get("run", True)
    template_scene = params["template_scene"]
    outpath = params["outpath"]
    qclog = params["qclog"]
    timestamp = params["timestamp"]
    scenezip = (params.get("scenezip", "yes") or "yes").strip().lower()
    on_existing = params.get("on_existing", "leave")

    if not run:
        rr += "\n---> Skipping because session not ready."
        report["failed"].append("T2w")
        return {"r": rr, "report": report}

    try:
        case_name = f"{sinfo['id']}{options['hcp_suffix']}"

        skip, rr = _apply_on_existing(
            on_existing,
            [os.path.join(outpath, f"{case_name}.T2w.*")],
            "T2w",
            rr,
        )
        if skip:
            report["done"].append("T2w")
            return {"r": rr, "report": report}

        t2w_restore = os.path.join(hcp["hcp_nonlin"], "T2w_restore.nii.gz")
        if not os.path.exists(t2w_restore):
            rr += "\n---> ERROR: Preprocessed T2w data not found: %s" % t2w_restore
            report["failed"].append("T2w")
            return {"r": rr, "report": report}

        working_scene = os.path.join(outpath, f"{case_name}.T2w.QC.wb.scene")
        png_name = f"{os.path.basename(working_scene)}.png"
        png_out = os.path.join(outpath, f"{os.path.basename(working_scene)}.{timestamp}.png")

        rr = _render_scene_qc(
            template_scene,
            working_scene,
            {
                "DUMMYPATH": hcp["base"],
                "DUMMYCASE": case_name,
                "DUMMYTIMESTAMP": timestamp,
                "DUMMYPNGNAME": png_name,
            },
            png_out,
            qclog,
            sinfo["id"],
            ["T2w"],
            overwrite,
            "    ... rendering T2w QC png",
            rr,
        )

        if scenezip == "yes":
            rr = _zip_qc_scene(
                working_scene,
                hcp["base"],
                os.path.join(hcp["base"], "qc"),
                outpath,
                timestamp,
                qclog,
                sinfo["id"],
                ["T2w"],
                rr,
            )

        report["done"].append("T2w")
        return {"r": rr, "report": report}

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        rr += str(errormessage)
        report["failed"].append("T2w")
        return {"r": rr, "report": report}
    except Exception:
        rr += "\nERROR: Unknown error occured:\n...................................\n"
        rr += traceback.format_exc()
        rr += "\n...................................\n"
        report["failed"].append("T2w")
        return {"r": rr, "report": report}


def _run_qc_myelin(sinfo, options, overwrite, hcp, params: dict):
    rr = "\n\nWorking on: Myelin"
    report = {"done": [], "failed": []}

    run = params.get("run", True)
    template_scene = params["template_scene"]
    outpath = params["outpath"]
    qclog = params["qclog"]
    timestamp = params["timestamp"]
    scenezip = (params.get("scenezip", "yes") or "yes").strip().lower()
    on_existing = params.get("on_existing", "leave")

    if not run:
        rr += "\n---> Skipping because session not ready."
        report["failed"].append("Myelin")
        return {"r": rr, "report": report}

    try:
        case_name = f"{sinfo['id']}{options['hcp_suffix']}"

        skip, rr = _apply_on_existing(
            on_existing,
            [os.path.join(outpath, f"{case_name}.Myelin.*")],
            "Myelin",
            rr,
        )
        if skip:
            report["done"].append("Myelin")
            return {"r": rr, "report": report}

        myelin_l = os.path.join(
            hcp["hcp_nonlin"], f"{case_name}.L.SmoothedMyelinMap.164k_fs_LR.func.gii"
        )
        myelin_r = os.path.join(
            hcp["hcp_nonlin"], f"{case_name}.R.SmoothedMyelinMap.164k_fs_LR.func.gii"
        )
        if not (os.path.exists(myelin_l) and os.path.exists(myelin_r)):
            rr += "\n---> ERROR: Preprocessed Smoothed Myelin data not found: %s.*.SmoothedMyelinMap.164k_fs_LR.func.gii" % (
                os.path.join(hcp["hcp_nonlin"], case_name)
            )
            report["failed"].append("Myelin")
            return {"r": rr, "report": report}

        working_scene = os.path.join(outpath, f"{case_name}.Myelin.QC.wb.scene")
        png_name = f"{os.path.basename(working_scene)}.png"
        png_out = os.path.join(outpath, f"{os.path.basename(working_scene)}.{timestamp}.png")

        rr = _render_scene_qc(
            template_scene,
            working_scene,
            {
                "DUMMYPATH": hcp["base"],
                "DUMMYCASE": case_name,
                "DUMMYTIMESTAMP": timestamp,
                "DUMMYPNGNAME": png_name,
            },
            png_out,
            qclog,
            sinfo["id"],
            ["Myelin"],
            overwrite,
            "    ... rendering Myelin QC png",
            rr,
        )

        if scenezip == "yes":
            rr = _zip_qc_scene(
                working_scene,
                hcp["base"],
                os.path.join(hcp["base"], "qc"),
                outpath,
                timestamp,
                qclog,
                sinfo["id"],
                ["Myelin"],
                rr,
            )

        report["done"].append("Myelin")
        return {"r": rr, "report": report}

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        rr += str(errormessage)
        report["failed"].append("Myelin")
        return {"r": rr, "report": report}
    except Exception:
        rr += "\nERROR: Unknown error occured:\n...................................\n"
        rr += traceback.format_exc()
        rr += "\n...................................\n"
        report["failed"].append("Myelin")
        return {"r": rr, "report": report}


def _run_qc_general(sinfo, options, overwrite, hcp, params: dict):
    rr = "\n\nWorking on: general"
    report = {"done": [], "failed": []}

    run = params.get("run", True)
    template_scene = params["template_scene"]
    outpath = params["outpath"]
    qclog = params["qclog"]
    timestamp = params["timestamp"]
    scenezip = (params.get("scenezip", "yes") or "yes").strip().lower()
    datapath = params.get("datapath")
    datafile = params.get("datafile")
    on_existing = params.get("on_existing", "leave")

    if not run:
        rr += "\n---> Skipping because session not ready."
        report["failed"].append("general")
        return {"r": rr, "report": report}

    try:
        case_name = f"{sinfo['id']}{options['hcp_suffix']}"
        session_path = os.path.join(options["sessionsfolder"], sinfo["id"])

        skip, rr = _apply_on_existing(
            on_existing,
            [os.path.join(outpath, f"{case_name}.general.*")],
            "general",
            rr,
        )
        if skip:
            report["done"].append("general")
            return {"r": rr, "report": report}

        data_path_check = os.path.join(session_path, datapath, datafile)

        if not os.path.exists(data_path_check):
            rr += "\n---> ERROR: Data requested not found: %s" % data_path_check
            report["failed"].append("general")
            return {"r": rr, "report": report}

        working_scene = os.path.join(outpath, f"{case_name}.general.QC.wb.scene")
        png_out = os.path.join(outpath, f"{os.path.basename(working_scene)}.{timestamp}.png")

        rr = _render_scene_qc(
            template_scene,
            working_scene,
            {
                "DUMMYPATH": hcp["base"],
                "DUMMYCASE": case_name,
                "DUMMYIMAGEPATH": os.path.join(session_path, datapath),
                "DUMMYIMAGEFILE": datafile,
            },
            png_out,
            qclog,
            sinfo["id"],
            ["general"],
            overwrite,
            "    ... rendering general QC png",
            rr,
        )

        if scenezip == "yes":
            rr = _zip_qc_scene(
                working_scene,
                session_path,
                os.path.join(session_path, "qc"),
                outpath,
                timestamp,
                qclog,
                sinfo["id"],
                ["general"],
                rr,
            )

        report["done"].append("general")
        return {"r": rr, "report": report}

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        rr += str(errormessage)
        report["failed"].append("general")
        return {"r": rr, "report": report}
    except Exception:
        rr += "\nERROR: Unknown error occured:\n...................................\n"
        rr += traceback.format_exc()
        rr += "\n...................................\n"
        report["failed"].append("general")
        return {"r": rr, "report": report}