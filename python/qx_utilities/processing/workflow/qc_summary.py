#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``workflow/qc_summary.py``

The quality control measures ``run_qc_summary`` compiles, read from what the
processing pipelines have already written.

One function per processing stage, each returning a ``{metric: value}``
dictionary and each surviving anything it cannot read: a stage that produced
nothing yields no keys, which the tables render as blanks. Which sessions are
missing what is one of the things the summary is for, so absence is reported
rather than swallowed -- but only absence. A stage that was found contributes
its numbers and no commentary: on a healthy study of several hundred sessions,
a line per stage per session would bury the sessions worth looking at.

**Every read of image data goes through the three helpers at the head of the
file** -- :func:`_load_volume`, :func:`_load_cifti_cortex` and
:func:`timeseries_stats`. The library behind them is ``nibabel``; the python
``nimage`` port covers neither the FreeSurfer MGH/MGZ volumes
:func:`contrast_metrics` reads nor the resampling :func:`group_registration`
needs, so it would be a second library rather than a replacement. Funnelling
the reads is what makes that a decision to revisit in one place.

``nibabel.processing`` is imported inside :func:`group_registration` rather than
at the top: it pulls in scipy, which the test workflow does not install, and
every other measure here has to remain readable without it.
"""

import glob
import json
import os
import shutil
import subprocess
import tempfile

import numpy as np
import nibabel as nib

from qx_utilities.general.log import log_or_console


# the stages that can be asked for with --qc_summary_modules, and one metric
# per stage that says the stage produced something. `completeness` counts these
STAGE_METRICS = {
    "prefs": ["reg_group_ncc", "mni_brain_volume_ml", "t1t2_ratio_median", "warp_jac_min"],
    "fs": ["fs_surface_holes", "fs_mean_thickness", "t1_wg_cnr"],
    "postfs": ["myelin_mean_L", "thickness_mean", "areal_distortion_p95"],
    "bold": ["bold_n"],
    "dwi": ["dwi_outliers_pct", "dwi_cnr_mean", "dwi_motion_abs"],
}


# ---------------------------------------------------------------- reading data


def _load_volume(path):
    """
    Read a volume image as ``(data, image)``, the data as float32.

    ``dataobj`` rather than ``get_fdata()``: the latter converts to float64 and
    caches the result on the image object, which for a 1200 frame dense
    timeseries is most of a gigabyte held for the sake of one mean.
    """
    img = nib.load(path)

    return np.asanyarray(img.dataobj, dtype=np.float32), img


def _load_cifti_cortex(path):
    """
    Read a CIFTI scalar map as ``{"L": array, "R": array}`` of cortical values.

    A hemisphere the file does not describe is simply absent from the result.
    """
    cii = nib.load(path)
    data = np.asanyarray(cii.dataobj, dtype=np.float32).squeeze()
    axis = cii.header.get_axis(cii.ndim - 1)

    out = {}
    for name, index, _ in axis.iter_structures():
        if "CORTEX_LEFT" in name:
            out["L"] = np.asarray(data[index], dtype=np.float64)
        if "CORTEX_RIGHT" in name:
            out["R"] = np.asarray(data[index], dtype=np.float64)

    return out


def timeseries_stats(path):
    """
    Median cortical temporal SNR and cortical coverage for a dense timeseries.

    Coverage is the fraction of cortical grayordinates carrying usable signal.
    The HCP `goodvoxels` step sets dropout to zero, so a BOLD that is
    misregistered or heavy with dropout reads as low coverage even where the
    temporal SNR of what remains looks respectable.

    Returns ``(tsnr, coverage)``, either of them NaN when it cannot be had.
    """
    cii = nib.load(path)
    ts = np.asanyarray(cii.dataobj, dtype=np.float32)
    if ts.ndim != 2 or ts.shape[0] < 5:
        return np.nan, np.nan

    mean, sd = ts.mean(0), ts.std(0, ddof=1)

    cortex = np.zeros(ts.shape[1], bool)
    for name, index, _ in cii.header.get_axis(1).iter_structures():
        if "CORTEX" in name:
            cortex[index] = True
    if not cortex.any():
        cortex = np.ones(ts.shape[1], bool)

    usable = (sd > 0) & (mean > 0)
    cortical = usable & cortex

    tsnr = float(np.median(mean[cortical] / sd[cortical])) if cortical.any() else np.nan
    coverage = round(100.0 * float(np.mean(usable[cortex])), 3)

    return tsnr, coverage


# ------------------------------------------------------------------- utilities


def _first(*patterns):
    """
    The first existing file matching any of the patterns, in order given.

    ``recursive=True``, so a ``**`` in a pattern spans any number of folders.
    Without it glob reads ``**`` as a plain ``*`` and matches one level only,
    which is not what a pattern is written with ``**`` for.
    """
    for pattern in patterns:
        hits = sorted(glob.glob(pattern, recursive=True))
        if hits:
            return hits[0]

    return None


def _nzstats(values):
    """Mean and standard deviation over the finite, non-zero values."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values) & (values != 0)]
    if values.size == 0:
        return np.nan, np.nan

    return float(np.mean(values)), float(np.std(values, ddof=1))


def _ncc(a, b):
    """
    Correlation of two images over the voxels either of them covers.

    NaN rather than a number when there is too little overlap to mean anything,
    or when one of the two is flat.
    """
    a, b = a.ravel(), b.ravel()
    covered = (a != 0) | (b != 0)
    a, b = a[covered], b[covered]
    if a.size < 100 or np.std(a) == 0 or np.std(b) == 0:
        return np.nan

    return float(np.corrcoef(a, b)[0, 1])


# ----------------------------------------------------- registration to MNI ---
#
# The nonlinear volume warp is written by PreFreeSurfer and is not overwritten
# by PostFreeSurfer, so everything read here reports the PreFreeSurfer step.


def prefs_metrics(base, *, _log=None):
    """
    Brain volume in MNI space and the median T1w/T2w ratio.

    Parameters:
        base (str): the session's HCP folder.
        _log: the log to report into.

    Returns:
        dict: the metrics that could be read.
    """
    log = log_or_console(_log)
    out = {}

    t1 = _first(os.path.join(base, "MNINonLinear", "T1w_restore_brain.nii.gz"))
    t2 = _first(os.path.join(base, "MNINonLinear", "T2w_restore_brain.nii.gz"))

    if not t1:
        log.detail("no MNINonLinear T1w brain, skipping registration measures")
        return out

    try:
        t1data, img = _load_volume(t1)
        voxel = float(np.prod(img.header.get_zooms()[:3]))
        out["mni_brain_volume_ml"] = float((t1data > 0).sum()) * voxel / 1000.0
    except Exception as error:
        log.warning(f"could not read {os.path.basename(t1)}: {error}")
        return out

    if t2:
        try:
            t2data, _ = _load_volume(t2)
            both = (t1data > 0) & (t2data > 0)
            if both.sum() > 100:
                out["t1t2_ratio_median"] = float(np.median(t1data[both] / t2data[both]))
        except Exception as error:
            log.warning(f"could not compute the T1w/T2w ratio: {error}")

    return out


def warp_jacobian(base, run="run", *, _log=None):
    """
    Minimum, maximum and percentage folded of the warp's Jacobian determinant.

    The determinant is computed by FSL ``fnirtfileutils``, which knows the
    fnirt/flirt warp convention, over ``acpc_dc2standard.nii.gz`` within the
    brain. A determinant at or below zero means the warp folds space onto
    itself, which is physically impossible and a clear failure of the
    registration.

    Parameters:
        base (str): the session's HCP folder.
        run (str): the run mode; nothing is executed unless it is ``run``.
        _log: the log to report into.

    Returns:
        dict: the metrics that could be read; empty without FSL or the warp.
    """
    log = log_or_console(_log)
    out = {}

    warp = _first(os.path.join(base, "MNINonLinear", "xfms", "acpc_dc2standard.nii.gz"))
    reference = _first(os.path.join(base, "MNINonLinear", "T1w_restore.nii.gz"),
                       os.path.join(base, "MNINonLinear", "T1w_restore_brain.nii.gz"))

    if not warp or not reference:
        log.detail("no MNINonLinear warp, skipping the Jacobian measures")
        return out
    if shutil.which("fnirtfileutils") is None:
        log.detail("fnirtfileutils not on the path, skipping the Jacobian measures")
        return out

    if run != "run":
        log.detail("test, not run: fnirtfileutils "
                   f"--in={warp} --ref={reference} --jac=<temporary>")
        return out

    workfolder = tempfile.mkdtemp(prefix="qc_summary_jac_")
    jacobian = os.path.join(workfolder, "jacobian.nii.gz")
    try:
        command = ["fnirtfileutils", f"--in={warp}", f"--ref={reference}", f"--jac={jacobian}"]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=900)
        if completed.returncode != 0 or not os.path.isfile(jacobian):
            log.warning(f"fnirtfileutils failed: {completed.stderr.strip()}")
            return out

        determinant, _ = _load_volume(jacobian)

        # within the brain where there is a mask to say where that is
        mask = _first(os.path.join(base, "MNINonLinear", "T1w_restore_brain.nii.gz"),
                      os.path.join(base, "MNINonLinear", "brainmask_fs.nii.gz"))
        values = None
        if mask:
            maskdata, _ = _load_volume(mask)
            if maskdata.shape == determinant.shape:
                values = determinant[maskdata > 0]
        if values is None:
            values = determinant[determinant != 0]

        values = values[np.isfinite(values)]
        if values.size:
            out["warp_jac_min"] = round(float(np.min(values)), 4)
            out["warp_jac_max"] = round(float(np.max(values)), 4)
            out["warp_jac_pct_folded"] = round(100.0 * float(np.mean(values <= 0)), 4)
    except Exception as error:
        log.warning(f"could not compute the warp Jacobian: {error}")
    finally:
        shutil.rmtree(workfolder, ignore_errors=True)

    return out


def group_registration(bases, run_folder, mni_template=None, run="run", *, _log=None):
    """
    Similarity of each session's MNI brain to the group mean, and to a template.

    A warp that has broken no longer puts the brain where the rest of the study
    puts it, and the correlation collapses -- which is a measure of registration
    that needs no atlas, only the study itself.

    Read in two passes so that memory does not grow with the study: the first
    resamples each brain to 2 mm, adds it into a running sum and writes it to
    ``run_folder``; the second reads those back and correlates each against the
    mean. One resampling each, one volume in memory at a time.

    Parameters:
        bases (dict): ``{session id: HCP folder}``.
        run_folder (str): folder to hold the resampled volumes while working.
        mni_template (str): optional template for the second similarity measure.
        run (str): the run mode; nothing is read or written unless it is ``run``.
        _log: the log to report into.

    Returns:
        tuple: ``({id: group ncc}, {id: template ncc})``, either possibly empty.
    """
    log = log_or_console(_log)

    if run != "run":
        log.detail(f"test, not computed: registration similarity over {len(bases)} sessions")
        return {}, {}

    try:
        from nibabel.processing import resample_to_output, resample_from_to
    except ImportError:
        log.warning("scipy is not available, skipping the registration similarity measures")
        return {}, {}

    workfolder = os.path.join(run_folder, ".qc_summary_2mm")
    os.makedirs(workfolder, exist_ok=True)
    try:
        # pass one: resample, accumulate the sum, keep each volume on disk
        total, reference, resampled = None, None, {}
        for session, base in bases.items():
            t1 = _first(os.path.join(base, "MNINonLinear", "T1w_restore_brain.nii.gz"))
            if not t1:
                continue
            try:
                img = nib.load(t1)
                downsampled = resample_to_output(img, voxel_sizes=2.0, order=1)
                if reference is None:
                    reference = downsampled
                elif (downsampled.shape != reference.shape
                        or not np.allclose(downsampled.affine, reference.affine)):
                    # the first session read sets the grid the rest are put on
                    downsampled = resample_from_to(
                        img, (reference.shape, reference.affine), order=1)
                data = np.asanyarray(downsampled.dataobj, dtype=np.float32)
            except Exception as error:
                log.warning(f"{session}: could not resample the MNI brain: {error}")
                continue

            path = os.path.join(workfolder, f"{session}.npy")
            np.save(path, data)
            resampled[session] = path
            total = data.astype(np.float64) if total is None else total + data

        if len(resampled) < 2:
            log.detail("fewer than two sessions with an MNI brain, "
                       "skipping the registration similarity measures")
            return {}, {}

        mean_brain = (total / len(resampled)).astype(np.float32)

        template = None
        if mni_template and os.path.isfile(mni_template):
            try:
                template = np.asanyarray(
                    resample_from_to(nib.load(mni_template),
                                     (reference.shape, reference.affine), order=1).dataobj,
                    dtype=np.float32)
            except Exception as error:
                log.warning(f"could not read the MNI template {mni_template}: {error}")
        elif mni_template:
            log.warning(f"the MNI template does not exist: {mni_template}")

        # pass two: correlate each against the mean, one volume at a time
        group, against_template = {}, {}
        for session, path in resampled.items():
            data = np.load(path)
            group[session] = _ncc(data, mean_brain)
            if template is not None:
                against_template[session] = _ncc(data, template)

        return group, against_template
    finally:
        shutil.rmtree(workfolder, ignore_errors=True)


# --------------------------------------------------- the FreeSurfer recon ----


def fs_metrics(base, session, *, _log=None):
    """
    Intracranial and brain segmentation volumes, surface holes, mean thickness.

    Read from the ``aseg.stats`` and ``?h.aparc.stats`` tables recon-all wrote.
    The surface holes are the Euler number burden: how many topological defects
    the reconstruction had to repair.

    Parameters:
        base (str): the session's HCP folder.
        session (str): the session id as it names the FreeSurfer folder.
        _log: the log to report into.

    Returns:
        dict: the metrics that could be read.
    """
    log = log_or_console(_log)
    out = {}

    aseg = os.path.join(base, "T1w", session, "stats", "aseg.stats")
    if not os.path.isfile(aseg):
        log.detail("no aseg.stats, skipping the FreeSurfer measures")
        return out

    # a measure line names the quantity twice -- `# Measure <long>, <short>, <description>,
    # <value>, <unit>` -- and the two names are the same word for most of them but not for
    # all: intracranial volume is `EstimatedTotalIntraCranialVol` long and `eTIV` short.
    # Both are recorded, so a lookup by either finds it
    measures = {}
    try:
        with open(aseg) as stats:
            for line in stats:
                if not line.startswith("# Measure"):
                    continue
                fields = [field.strip() for field in line.split(",")]
                if len(fields) >= 4:
                    try:
                        value = float(fields[3])
                    except ValueError:
                        continue
                    measures[fields[0][len("# Measure"):].strip()] = value
                    measures[fields[1]] = value
    except Exception as error:
        log.warning(f"could not read aseg.stats: {error}")

    for metric, measure, scale in [
        ("fs_etiv_ml", "EstimatedTotalIntraCranialVol", 1000.0),
        ("fs_brainseg_ml", "BrainSegVol", 1000.0),
        ("fs_surface_holes", "SurfaceHoles", 1.0),
    ]:
        if measure in measures:
            out[metric] = measures[measure] / scale

    thicknesses = []
    for hemisphere in ("lh", "rh"):
        aparc = os.path.join(base, "T1w", session, "stats", f"{hemisphere}.aparc.stats")
        if not os.path.isfile(aparc):
            continue
        try:
            with open(aparc) as stats:
                for line in stats:
                    if "MeanThickness" in line:
                        thicknesses.append(float([f.strip() for f in line.split(",")][3]))
        except Exception as error:
            log.warning(f"could not read {hemisphere}.aparc.stats: {error}")

    if thicknesses:
        out["fs_mean_thickness"] = float(np.mean(thicknesses))

    return out


def contrast_metrics(base, session, *, _log=None):
    """
    White-gray percent contrast and contrast-to-noise.

    A low contrast T1w can reconstruct cleanly -- few holes, no complaint from
    recon-all -- and still give unreliable surfaces, so this catches a failure
    that topology misses. Read from the recon-all ``?h.w-g.pct.mgh`` overlays,
    falling back to a volume contrast-to-noise computed from ``norm.mgz`` and
    the segmentation. Higher means better separated tissue.

    Parameters:
        base (str): the session's HCP folder.
        session (str): the session id as it names the FreeSurfer folder.
        _log: the log to report into.

    Returns:
        dict: the metrics that could be read.
    """
    log = log_or_console(_log)
    out = {}

    surf = os.path.join(base, "T1w", session, "surf")
    means, ratios = [], []
    for hemisphere in ("lh", "rh"):
        overlay = _first(os.path.join(surf, f"{hemisphere}.w-g.pct.mgh"))
        if not overlay:
            continue
        try:
            values = np.asanyarray(nib.load(overlay).dataobj, dtype=np.float32).ravel()
            values = values[np.isfinite(values) & (values != 0)]
            if values.size:
                mean = float(np.mean(values))
                sd = float(np.std(values, ddof=1))
                means.append(mean)
                if sd > 0:
                    ratios.append(mean / sd)
        except Exception as error:
            log.warning(f"could not read {hemisphere}.w-g.pct.mgh: {error}")

    if means:
        out["t1_wg_contrast"] = round(float(np.mean(means)), 4)
        if ratios:
            out["t1_wg_cnr"] = round(float(np.mean(ratios)), 4)
        return out

    norm = _first(os.path.join(base, "T1w", session, "mri", "norm.mgz"),
                  os.path.join(base, "T1w", session, "mri", "brain.mgz"))
    aseg = _first(os.path.join(base, "T1w", session, "mri", "aseg.mgz"))
    if not norm or not aseg:
        log.detail("no white-gray contrast overlays or segmentation, "
                   "skipping the contrast measures")
        return out

    try:
        intensity = np.asanyarray(nib.load(norm).dataobj, dtype=np.float32)
        labels = np.asanyarray(nib.load(aseg).dataobj, dtype=np.float32)
        white = intensity[np.isin(labels, [2, 41])]
        gray = intensity[np.isin(labels, [3, 42])]
        white, gray = white[white > 0], gray[gray > 0]
        if white.size > 100 and gray.size > 100:
            white_mean, gray_mean = float(white.mean()), float(gray.mean())
            noise = float(np.sqrt((white.std(ddof=1) ** 2 + gray.std(ddof=1) ** 2) / 2))
            if noise > 0:
                out["t1_wg_cnr"] = round(abs(white_mean - gray_mean) / noise, 4)
            out["t1_wg_contrast"] = round(
                100.0 * (white_mean - gray_mean) / (0.5 * (white_mean + gray_mean)), 4)
    except Exception as error:
        log.warning(f"could not compute the volume contrast: {error}")

    return out


# ------------------------------------- the fs_LR surfaces and myelin maps ----


def postfs_metrics(base, session, *, _log=None):
    """
    Myelin, thickness and surface registration distortion on the fs_LR mesh.

    The MSMSulc surface registration and the myelin maps are PostFreeSurfer's
    work. A large left-right myelin asymmetry points at a lopsided registration
    or a bias field; high areal or edge distortion says the registration had to
    strain to reach the atlas.

    Parameters:
        base (str): the session's HCP folder.
        session (str): the session id as it names the HCP folder.
        _log: the log to report into.

    Returns:
        dict: the metrics that could be read.
    """
    log = log_or_console(_log)
    out = {}

    fs_lr = os.path.join(base, "MNINonLinear", "fsaverage_LR32k")

    def named(name):
        return _first(os.path.join(fs_lr, f"{session}.{name}.32k_fs_LR.dscalar.nii"))

    myelin = named("MyelinMap_BC") or named("MyelinMap") or named("SmoothedMyelinMap")
    if not myelin:
        log.detail("no fs_LR myelin map, skipping the surface measures")
        return out

    try:
        hemispheres = _load_cifti_cortex(myelin)
        left, _ = _nzstats(hemispheres.get("L", []))
        right, _ = _nzstats(hemispheres.get("R", []))
        out["myelin_mean_L"], out["myelin_mean_R"] = left, right

        both = np.concatenate([hemispheres.get("L", []), hemispheres.get("R", [])])
        mean, sd = _nzstats(both)
        if np.isfinite(mean) and mean != 0:
            out["myelin_cv"] = sd / mean
            if np.isfinite(left) and np.isfinite(right):
                out["myelin_asym"] = abs(left - right) / mean

        out["n_vertices_L"] = int(np.size(hemispheres.get("L", [])))
        out["n_vertices_R"] = int(np.size(hemispheres.get("R", [])))
    except Exception as error:
        log.warning(f"could not read the myelin map: {error}")

    thickness = named("thickness") or named("corrThickness")
    if thickness:
        try:
            hemispheres = _load_cifti_cortex(thickness)
            mean, sd = _nzstats(
                np.concatenate([hemispheres.get("L", []), hemispheres.get("R", [])]))
            out["thickness_mean"], out["thickness_sd"] = mean, sd
        except Exception as error:
            log.warning(f"could not read the fs_LR thickness map: {error}")

    for metric, maps, summarise in [
        ("areal_distortion_p95",
         ["ArealDistortion_MSMSulc", "ArealDistortion_MSMAll", "ArealDistortion_FS"],
         lambda values: float(np.percentile(values, 95))),
        ("edge_distortion_mean",
         ["EdgeDistortion_MSMSulc", "EdgeDistortion_MSMAll"],
         lambda values: float(np.mean(values))),
    ]:
        distortion = _first(*[os.path.join(fs_lr, f"{session}.{name}.32k_fs_LR.dscalar.nii")
                              for name in maps])
        if not distortion:
            continue
        try:
            hemispheres = _load_cifti_cortex(distortion)
            values = np.abs(
                np.concatenate([hemispheres.get("L", []), hemispheres.get("R", [])]))
            values = values[np.isfinite(values)]
            if values.size:
                out[metric] = summarise(values)
        except Exception as error:
            log.warning(f"could not read {os.path.basename(distortion)}: {error}")

    return out


# ------------------------------------------------------------- diffusion -----


def dwi_metrics(base, *, _log=None):
    """
    Motion, outlier slices and contrast-to-noise, from the FSL eddy QC report.

    Parameters:
        base (str): the session's HCP folder.
        _log: the log to report into.

    Returns:
        dict: the metrics that could be read.
    """
    log = log_or_console(_log)
    out = {}

    report = _first(os.path.join(base, "Diffusion", "**", "qc.json"),
                    os.path.join(base, "**", "eddy", "**", "qc.json"))
    if not report:
        log.detail("no eddy qc.json, skipping the diffusion measures")
        return out

    try:
        with open(report) as qc:
            measures = json.load(qc)
    except Exception as error:
        log.warning(f"could not read the eddy QC report: {error}")
        return out

    for metric, key in [("dwi_motion_abs", "qc_mot_abs"),
                        ("dwi_motion_rel", "qc_mot_rel"),
                        ("dwi_outliers_pct", "qc_outliers_tot"),
                        ("dwi_cnr_mean", "qc_cnr_avg")]:
        if key not in measures:
            continue
        value = measures[key]
        out[metric] = float(np.mean(value)) if isinstance(value, (list, tuple)) else float(value)

    return out


# ------------------------------------------------- where it likely went wrong

# how far from the study's own middle a value has to be, for the diagnosis to
# call it atypical, is `--qc_summary_diag_k` robust standard deviations. These
# four are the measures it reads
DIAGNOSED = ["reg_group_ncc", "mni_brain_volume_ml", "areal_distortion_p95", "fs_surface_holes"]

# the correlation below which registration is called low whatever the study
# looks like. It is a floor rather than a sample comparison, and it is there to
# catch a study whose sessions are *all* misregistered -- where the sample
# median is bad too and nothing stands out from it. Because the two arms mean
# different things, the evidence says which one fired
ABSOLUTE_REGISTRATION_FLOOR = 0.9


def _robust(values):
    """
    The middle of a sample and its spread, as ``(median, MAD)``.

    The median absolute deviation, scaled to read like a standard deviation, so
    that a handful of badly broken sessions do not widen the spread until they
    look ordinary. ``None`` when there are fewer than three values to describe.
    """
    values = np.array(
        [value for value in values if value is not None and np.isfinite(value)], float)
    if values.size < 3:
        return None

    median = np.median(values)
    mad = np.median(np.abs(values - median)) * 1.4826
    if mad == 0:
        mad = np.std(values) or 1.0

    return median, mad


def diagnose(rows, k=3.0):
    """
    Name the step each session's trouble most likely arose at, and say why.

    A pointer, not a verdict: it reads each session against the rest of the
    study and reports which probes fired, in the order the pipeline runs, so
    that the earliest stage that could explain the rest is the one named.
    Registration reads the PreFreeSurfer warp, surface distortion the
    PostFreeSurfer MSMSulc step, and surface holes the native recon.

    Adds ``likely_failure_step`` and ``diagnosis_evidence`` to each row.

    Parameters:
        rows (list): the session rows, modified in place.
        k (float): how many robust standard deviations count as atypical.
    """
    spread = {name: _robust([row.get(name) for row in rows]) for name in DIAGNOSED}

    def z(name, value):
        if spread.get(name) is None or not finite(value):
            return None
        median, mad = spread[name]
        return (value - median) / mad

    def finite(value):
        return value is not None and np.isfinite(value)

    for row in rows:
        holes = row.get("fs_surface_holes")
        registration = row.get("reg_group_ncc")
        volume = row.get("mni_brain_volume_ml")
        folded = row.get("warp_jac_pct_folded")
        jacobian = row.get("warp_jac_min")
        distortion = row.get("areal_distortion_p95")

        pre, post, recon = [], [], []

        if finite(folded) and folded > 0.1:
            pre.append(f"warp folding {folded:.2f}%")
        if finite(jacobian) and jacobian < 0:
            pre.append(f"negative Jacobian ({jacobian:.2f})")

        # the two arms are reported apart: one says the session stands out from
        # this study, the other that it is poor by any measure. A reader acts
        # on them differently, and a study where every session trips the floor
        # is saying something about the study rather than about a session
        if finite(registration):
            deviation = z("reg_group_ncc", registration)
            if deviation is not None and deviation < -k:
                pre.append(f"reg similarity low for this study ({registration:.2f})")
            elif registration < ABSOLUTE_REGISTRATION_FLOOR:
                pre.append(f"reg similarity low ({registration:.2f}, "
                           f"below {ABSOLUTE_REGISTRATION_FLOOR})")

        deviation = z("mni_brain_volume_ml", volume)
        if deviation is not None and abs(deviation) > k:
            pre.append(f"MNI brain volume atypical ({volume:.0f} ml)")

        deviation = z("areal_distortion_p95", distortion)
        if deviation is not None and deviation > k:
            post.append(f"areal distortion high ({distortion:.2f})")

        deviation = z("fs_surface_holes", holes)
        if deviation is not None and deviation > k:
            recon.append(f"surface holes high ({holes:.0f})")

        if not finite(holes) and not finite(registration) and not finite(volume):
            step, evidence = "Pipeline incomplete", ["no FreeSurfer or MNINonLinear outputs"]
        elif not finite(holes):
            step, evidence = "FreeSurfer (incomplete)", ["recon-all outputs missing"]
        elif pre:
            step = "PreFreeSurfer (volume warp)"
            evidence = pre + (["also: " + ", ".join(post + recon)] if post or recon else [])
        elif post:
            step, evidence = "PostFreeSurfer (surface reg)", post + recon
        elif recon:
            step, evidence = "FreeSurfer (recon quality)", recon
        else:
            step, evidence = "OK", []

        row["likely_failure_step"] = step
        row["diagnosis_evidence"] = "; ".join(evidence)


def note_completeness(rows, modules):
    """
    Record how many of the requested stages each session produced data for.

    Adds ``completeness`` -- ``N/M`` over the stages that were asked for -- and
    ``stages_missing``. A session is never dropped for being incomplete: how
    much of the pipeline it has been through is one of the things being
    reported, and it is also the caveat on everything else in its row.

    Parameters:
        rows (list): the session rows, modified in place.
        modules (list): the stages that were asked for.
    """
    expected = [stage for stage in modules if stage in STAGE_METRICS]

    def has(value):
        return (value is not None and value != ""
                and (not isinstance(value, float) or np.isfinite(value)))

    for row in rows:
        present = [stage for stage in expected
                   if any(has(row.get(metric)) for metric in STAGE_METRICS[stage])]
        row["completeness"] = f"{len(present)}/{len(expected)}" if expected else ""
        row["stages_missing"] = ",".join(
            stage for stage in expected if stage not in present)
