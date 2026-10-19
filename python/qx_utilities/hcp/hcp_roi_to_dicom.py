#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``hcp_roi_to_dicom.py``

Burning an ROI into the original T1w DICOM series of an HCP-processed session.
"""

import json
import os
import os.path
import shutil
import tempfile

import nibabel as nib
import numpy as np
from nibabel.orientations import io_orientation, ornt_transform

import qx_utilities.processing.core as pc
from qx_utilities.dicom.dicom_archive import _unzip_dicom_folder
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.hcp.hcp_utils import do_hcp_options_check

# qunex parameters passed to ROI_to_DICOM.sh only when set
_OPTIONAL_FLAGS = [
    ("hcp_roidicom_series", "dicom-series"),
    ("hcp_roidicom_grayordinates", "grayordinates"),
    ("hcp_roidicom_cifti_roi", "cifti-roi-in"),
    ("hcp_roidicom_volume_roi", "volume-roi-in"),
    ("hcp_roidicom_volume_space", "volume-space"),
    ("hcp_roidicom_vertex", "vertex-in"),
    ("hcp_roidicom_vertex_structure", "vertex-structure"),
    ("hcp_roidicom_vertex_radius", "vertex-radius"),
    ("hcp_roidicom_burn_value", "burn-value"),
    ("hcp_roidicom_outline", "outline"),
    ("hcp_roidicom_outline_type", "outline-type"),
]

# the three ways of specifying the ROI, exactly one has to be used
_ROI_SOURCES = [
    "hcp_roidicom_cifti_roi",
    "hcp_roidicom_volume_roi",
    "hcp_roidicom_vertex",
]

# import_dicom sorts a series into dicom/<series number * 10>, by default archived
_ARCHIVES = [".tar.gz", ".tgz", ".tar", ".zip", ".tar.bz2", ".tar.xz"]


def hcp_roi_to_dicom(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_roi_to_dicom [... processing options]``

    Runs the ROI to DICOM step of HCP Pipeline (ROI_to_DICOM.sh). Takes the
    original T1w DICOM series and an ROI, given as a CIFTI dscalar file, a
    volume file or a surface vertex, and creates a new T1w DICOM series with
    the ROI "burned in" to the voxel values, e.g. for use with a
    neuronavigation system.

    ..  qx_command:
        type: processing.session

    Warning:
        The code expects the input images to be named and present in the QuNex
        folder structure. The function will look into folder::

            <session id>/hcp/<session id>

        for data. The session has to be processed with hcp_pre_freesurfer,
        hcp_freesurfer and hcp_post_freesurfer (and hcp_msmall when
        ``hcp_roidicom_regname`` is ``MSMAll``). The DICOM input has to be the
        series of the first T1w image used in hcp_pre_freesurfer, which QuNex
        finds in the session's ``dicom`` folder unless ``hcp_roidicom_input``
        is set.

        When hcp_pre_freesurfer averaged several T1w images, the ROI is mapped
        through the transform of the first image to the average, which needs
        a version of ROI_to_DICOM.sh that supports averaged T1w images.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). If the
            output DICOM folder already exists the session is skipped unless
            overwrite is set to yes.

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --log (str, default 'keep'):
            Whether to keep ('keep') or remove ('remove') the temporary logs.

        --hcp_roidicom_input (str, default detailed below):
            The folder containing the original T1w DICOM series, it has to be
            the first T1w input used in hcp_pre_freesurfer. If not set, QuNex
            reads the series number of that image from its JSON sidecar and
            uses the series in the session's ``dicom`` folder. A series that
            import_dicom archived (e.g. ``dicom/190.tar.gz``) is extracted into
            a temporary folder, which is removed once the command is done.
            When there are several T1w images, the first one is the one that
            matches ``T1w/T1w1_gdc.nii.gz`` best. To set the folder for each
            session, use ``_hcp_roidicom_input: <path>`` in the batch file.

        --hcp_roidicom_series (str, default ''):
            If the input folder contains multiple series, the DICOM series
            number of the appropriate T1w.

        --hcp_roidicom_output (str, default detailed below):
            The folder to write the modified DICOM series to. Defaults to
            ``<session id>/hcp/<session id>/T1w/T1w_with_ROI_DICOM``. Its
            parent folder has to exist.

        --hcp_roidicom_grayordinates (str, default '91282'):
            The grayordinates CIFTI space the ROI or vertex is based on,
            91282 or 170494.

        --hcp_roidicom_regname (str, default 'MSMSulc'):
            The surface registration to use, e.g. MSMSulc or MSMAll.

        --hcp_roidicom_cifti_roi (str, default ''):
            A CIFTI (dscalar) file containing the binary ROI.

        --hcp_roidicom_volume_roi (str, default ''):
            A volume file containing the binary ROI, requires
            ``hcp_roidicom_volume_space``.

        --hcp_roidicom_volume_space (str, default ''):
            The volume space of ``hcp_roidicom_volume_roi``, MNINonLinear or
            T1w.

        --hcp_roidicom_vertex (str, default ''):
            A single vertex index (0-based) to draw an ROI from, requires
            ``hcp_roidicom_vertex_structure`` and uses the surface mesh
            implied by ``hcp_roidicom_grayordinates``.

        --hcp_roidicom_vertex_structure (str, default ''):
            The surface the vertex is in, CORTEX_LEFT or CORTEX_RIGHT.

        --hcp_roidicom_vertex_radius (str, default '0'):
            A distance in mm around ``hcp_roidicom_vertex`` to include in the
            ROI, 0 means just the vertex.

        --hcp_roidicom_burn_value (str, default detailed below):
            The value to overwrite in-ROI voxels with. Defaults to 20% above
            the voxelwise maximum.

        --hcp_roidicom_outline (str, default ''):
            Use an outline with the given thickness in mm instead of occluding
            the ROI location.

        --hcp_roidicom_outline_type (str, default 'INSIDE'):
            The outline behavior, INSIDE (do not draw any voxels outside of
            the ROI, only make some of the ROI interior transparent) or
            OUTSIDE (draw voxels outside the ROI and make the entire ROI
            transparent).

    Output files:
        The modified DICOM series is written to the ``hcp_roidicom_output``
        folder, with the series description ``T1w_with_ROI`` and the series
        number of the input series with ``001`` appended.

        The transformations between the raw T1w and the T1w_PreFS space are
        saved in the session's ``T1w/xfms`` folder.

    Notes:
        Exactly one of ``hcp_roidicom_cifti_roi``,
        ``hcp_roidicom_volume_roi`` or ``hcp_roidicom_vertex`` has to be
        provided.

        hcp_roi_to_dicom parameter mapping:

            ================================= ======================
            QuNex parameter                   HCPpipelines parameter
            ================================= ======================
            ``hcp_roidicom_input``            ``dicom-input``
            ``hcp_roidicom_series``           ``dicom-series``
            ``hcp_roidicom_output``           ``dicom-output``
            ``hcp_roidicom_grayordinates``    ``grayordinates``
            ``hcp_roidicom_regname``          ``surf-reg-name``
            ``hcp_roidicom_cifti_roi``        ``cifti-roi-in``
            ``hcp_roidicom_volume_roi``       ``volume-roi-in``
            ``hcp_roidicom_volume_space``     ``volume-space``
            ``hcp_roidicom_vertex``           ``vertex-in``
            ``hcp_roidicom_vertex_structure`` ``vertex-structure``
            ``hcp_roidicom_vertex_radius``    ``vertex-radius``
            ``hcp_roidicom_burn_value``       ``burn-value``
            ``hcp_roidicom_outline``          ``outline``
            ``hcp_roidicom_outline_type``     ``outline-type``
            ================================= ======================

    Examples:
        ::

            qunex hcp_roi_to_dicom \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --sessions=OP101 \\
                --hcp_roidicom_cifti_roi=roi.dscalar.nii \\
                --hcp_roidicom_regname=MSMAll \\
                --hcp_roidicom_outline=2

        ::

            qunex hcp_roi_to_dicom \\
                --batchfile=processing/batch.txt \\
                --sessionsfolder=sessions \\
                --sessions=OP101 \\
                --hcp_roidicom_input=sessions/OP101/dicom/20 \\
                --hcp_roidicom_vertex=12345 \\
                --hcp_roidicom_vertex_structure=CORTEX_LEFT \\
                --hcp_roidicom_vertex_radius=5
    """

    log = SessionLog(sinfo, options, "HCP ROI to DICOM pipeline")

    report = "HCP ROI to DICOM"
    failed = 0
    workdir = None

    try:
        # --- Base settings
        pc.do_options_check(options, sinfo, "hcp_roi_to_dicom")
        do_hcp_options_check(options, "hcp_roi_to_dicom")
        hcp = get_hcp_paths(sinfo, options)

        run = _check_roi_options(options, log)

        # --- Find the T1w DICOM series
        dicom = None
        if run:
            dicom, workdir = _prepare_dicom_input(sinfo, options, hcp, log)
            run = dicom is not None

        # --- Build and report the command
        comm, output = _build_command(sinfo, options, hcp, dicom)
        if run:
            log.pipeline_command(comm, marker="            --")

        # -- Run
        if run:
            if options["run"] == "run":
                endlog, report, failed = pc.run_external_for_file(
                    output,
                    comm,
                    "Running HCP ROI to DICOM",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=options["logtag"],
                    full_test=None,
                    shell=True,
                    _log=log,
                )

            # -- just checking
            else:
                passed, report, failed = pc.check_run(
                    output, None, "HCP ROI to DICOM", overwrite=overwrite, _log=log
                )
                if passed is None:
                    log.step("HCP ROI to DICOM can be run")
                    report = "HCP ROI to DICOM can be run"
                    failed = 0

        else:
            log.step("Session cannot be processed.")
            report = "HCP ROI to DICOM cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        failed = 1
    except Exception:
        log.unknown_error()
        failed = 1
    finally:
        # an extracted series is a copy of the archive in the dicom folder
        if workdir is not None:
            shutil.rmtree(workdir, ignore_errors=True)

    return log.finish(report, failed, pipeline="HCP ROI to DICOM")


def _check_roi_options(options: dict, log: SessionLog) -> bool:
    """Log every missing or conflicting input and return whether the command can run."""
    ok = True

    sources = [e for e in _ROI_SOURCES if options[e] is not None]
    if len(sources) != 1:
        log.error(
            "exactly one of %s has to be provided, got %s!"
            % (", ".join(_ROI_SOURCES), ", ".join(sources) or "none")
        )
        ok = False

    if options["hcp_roidicom_volume_roi"] is not None and options["hcp_roidicom_volume_space"] is None:
        log.error("hcp_roidicom_volume_roi requires the hcp_roidicom_volume_space parameter!")
        ok = False

    if options["hcp_roidicom_vertex"] is not None and options["hcp_roidicom_vertex_structure"] is None:
        log.error("hcp_roidicom_vertex requires the hcp_roidicom_vertex_structure parameter!")
        ok = False

    return ok


def _prepare_dicom_input(
    sinfo: dict, options: dict, hcp: dict, log: SessionLog
) -> tuple[str | None, str | None]:
    """
    Return the folder holding the T1w DICOM series and the work folder to
    remove once the command is done, or ``(None, None)`` if there is no series.
    """
    if options["hcp_roidicom_input"] is not None:
        return options["hcp_roidicom_input"], None

    image = _first_t1w(hcp, log)
    series = _series_number(image, log) if image else None
    if series is None:
        return None, None

    folder = sinfo.get("dicom") or os.path.join(
        options["sessionsfolder"], sinfo["id"], "dicom"
    )
    source = _find_series(folder, series)
    if source is None:
        log.error(
            f"DICOM series {series} of {os.path.basename(image)} not found in"
            f" {folder}, set the hcp_roidicom_input parameter!"
        )
        return None, None
    log.step(f"T1w DICOM series {series} of {os.path.basename(image)}: {source}")

    if os.path.isdir(source):
        return source, None
    if options["run"] != "run":
        log.detail(f"test, not extracted: {source}")
        return os.path.join(hcp["T1w_folder"], "ROI_to_DICOM_XXXXXX", "dicom"), None

    workdir = tempfile.mkdtemp(prefix="ROI_to_DICOM_", dir=hcp["T1w_folder"])
    result = _unzip_dicom_folder(source, os.path.join(workdir, "dicom"))
    if result["status"] != "ok":
        shutil.rmtree(workdir, ignore_errors=True)
        log.error(f"could not extract {source}: {result['exception']}")
        return None, None
    return os.path.join(workdir, "dicom"), workdir


def _first_t1w(hcp: dict, log: SessionLog) -> str | None:
    """
    Return the unprocessed T1w image hcp_pre_freesurfer used first.

    With several T1w images the order hcp_pre_freesurfer got them in followed
    the directory listing, so the first one is told by its data instead: it is
    the one its T1w/T1w1_gdc copy matches best.
    """
    images = [e for e in hcp["T1w"].split("@") if e and e != "NONE"]
    if not images:
        log.error(f"no T1w image found in {hcp['T1w_source']}!")
        return None
    if len(images) == 1:
        return images[0]

    reference = os.path.join(hcp["T1w_folder"], "T1w1_gdc.nii.gz")
    if not os.path.exists(reference):
        log.error(f"{reference} not found, run hcp_pre_freesurfer first!")
        return None

    ref = nib.load(reference)
    match = {e: _similarity(e, ref) for e in images}
    return max(match, key=match.get)


def _similarity(image: str, ref: nib.Nifti1Image) -> float:
    """Correlation of an image with the reference, once in its voxel order."""
    img = nib.load(image)
    img = img.as_reoriented(
        ornt_transform(io_orientation(img.affine), io_orientation(ref.affine))
    )
    if img.shape[:3] != ref.shape[:3]:
        return -1.0

    # every 4th voxel is plenty to tell the images apart
    a = np.asarray(img.dataobj[::4, ::4, ::4], dtype=np.float64).ravel()
    b = np.asarray(ref.dataobj[::4, ::4, ::4], dtype=np.float64).ravel()
    if a.std() == 0 or b.std() == 0:
        return -1.0
    return float(np.corrcoef(a, b)[0, 1])


def _series_number(image: str, log: SessionLog) -> int | None:
    """Return the DICOM series number of an image, from its JSON sidecar."""
    sidecar = image[: -len(".nii.gz")] + ".json"
    try:
        with open(sidecar) as f:
            return int(json.load(f)["SeriesNumber"])
    except (OSError, ValueError, KeyError, TypeError):
        log.error(
            f"could not read the series number of {os.path.basename(image)} from"
            f" {sidecar}, set the hcp_roidicom_input parameter!"
        )
        return None


def _find_series(folder: str, series: int) -> str | None:
    """Return the folder or archive of a DICOM series in a session's dicom folder."""
    path = os.path.join(folder, str(series * 10))
    if os.path.isdir(path):
        return path
    for extension in _ARCHIVES:
        if os.path.isfile(path + extension):
            return path + extension
    return None


def _build_command(sinfo: dict, options: dict, hcp: dict, dicom: str | None) -> tuple[str, str]:
    """Return the ROI_to_DICOM.sh command and the output DICOM folder it writes."""
    output = options["hcp_roidicom_output"]
    if output is None:
        output = os.path.join(hcp["T1w_folder"], "T1w_with_ROI_DICOM")

    comm = (
        '%(script)s \
            --study-folder="%(studyfolder)s" \
            --subject="%(subject)s" \
            --dicom-input="%(dicominput)s" \
            --dicom-output="%(dicomoutput)s" \
            --surf-reg-name="%(regname)s"'
        % {
            "script": os.path.join(
                os.environ["HCPPIPEDIR"], "global", "scripts", "ROI_to_DICOM.sh"
            ),
            "studyfolder": sinfo["hcp"],
            "subject": sinfo["id"] + options["hcp_suffix"],
            "dicominput": dicom,
            "dicomoutput": output,
            "regname": options["hcp_roidicom_regname"],
        }
    )

    for option, flag in _OPTIONAL_FLAGS:
        if options[option] is not None:
            comm += '            --%s="%s"' % (flag, options[option])

    return comm, output
