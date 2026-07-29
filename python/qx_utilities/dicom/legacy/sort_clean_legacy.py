#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``legacy/sort_clean_legacy.py``

The superseded sort and clean helpers used by ``import_dicom_old``.

Replaced by the single pass engine in ``sort_dicom`` and ``clean_dicom``.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import glob
import os
from collections import Counter, defaultdict

import numpy as np

import qx_utilities.general.exceptions as ge
from qx_utilities.dicom.dicom_info import read_dicom_info, read_par_info
from qx_utilities.dicom.dicom_utils import clean_name
from qx_utilities.general.parsing import true_or_false

try:
    import pydicom
except Exception:
    import dicom as pydicom


def _sort_dicom_legacy(folder=".", **kwargs):
    """
    Legacy ``sort_dicom`` implementation retained for ``import_dicom_old``.

    ``sort_dicom [folder=.]``

    Sort DICOM files from the specified folder.

    Parameters:
        --folder (str, default '.'):
            The base session folder that contains the inbox subfolder with the
            unsorted DICOM files.

        --copy (str, default 'move'):
            Should we 'copy' or 'move'.

        --outdir (str, default detailed below):
            Optional directory where the sorted files are to be saved. Defaults
            to `folder` parameter if not set.

        --files (str, default detailed below):
            Comma separated list of files to sort. Defaults to files in `folder`.

    Notes:
        The command looks for the inbox subfolder in the specified session
        folder (folder) and checks for presence of DICOM or PAR/REC files in
        the inbox folder and its subfolders. It inspects the found files,
        creates a dicom folder and for each image a numbered subfolder. It then
        moves the found DICOM or PAR/REC files in the correct subfolders to
        prepare them for dicom2nii(x) processing. In the process it checks that
        PAR/REC extensions are uppercase and changes them if necessary. If log
        files are found, they are placed in a separate `log` subfolder.

        Multiple sessions and scheduling:
            The command can be run for multiple sessions by specifying
            `sessions` and optionally `sessionsfolder` and `parelements`
            parameters. In this case the command will be run for each of the
            specified sessions in the sessionsfolder (current directory by
            default). Optional `filter` and `sessionids` parameters can be used
            to filter sessions or limit them to just specified id codes. (for
            more information see online documentation). `sfolder` will be
            filled in automatically as each session's folder. Commands will
            run in parallel by utilizing the specified number of parelements (1
            by default).

            If `scheduler` parameter is set, the command will be run using the
            specified scheduler settings (see `qunex ?schedule` for more
            information). If set in combination with `sessions` parameter,
            sessions will be processed over multiple nodes, `core` parameter
            specifying how many sessions to run per node. Optional
            `scheduler_environment`, `scheduler_workdir`, `scheduler_sleep`,
            and `nprocess` parameters can be set.

            Set optional ``logfolder`` parameter to specify where the processing
            logs should be stored. Otherwise, the processor will make best
            guess, where the logs should go.

    Examples:
        Single sessions example::

            qunex sort_dicom \\
                --folder=OP667

        Multiple sessions example::

            qunex sort_dicom \\
                  --sessionsfolders="/data/my_study/sessions" \\
                  --sessions="OP*"
    """

    # --- should we copy or move

    print("Running sort_dicom\n=================")

    copy = kwargs.get("copy", None)
    outdir = kwargs.get("outdir", None)
    files = kwargs.get("files", None)

    if copy is None:
        copy = 'move'

    if copy == 'copy':
        from shutil import copy
        do_file = copy
    else:
        do_file = os.rename

    # --- establish target folder

    if outdir is None:
        dcmf = os.path.join(folder, "dicom")
    else:
        dcmf = os.path.join(outdir, "dicom")

    # --- get list of files

    if files is None:
        inbox = os.path.join(folder, "inbox")
        if not os.path.exists(inbox):
            raise ge.CommandFailed(
                "sort_dicom",
                "Inbox folder not found",
                "Please check your paths! [%s]" % (os.path.abspath(inbox)),
                "Aborting",
            )
        files_iter = glob.iglob(os.path.join(inbox, "**", "*"), recursive=True)

        # if len(files):
        #     files = []
        #     for droot, _, dfiles in os.walk(inbox):
        #         for dfile in dfiles:
        #             files.append(os.path.join(droot, dfile))
        #     print("---> Processing %d files from %s" % (len(files), inbox))
        # else:
        #     raise ge.CommandFailed("sort_dicom", "No files found", "Please check the specified inbox folder! [%s]" % (os.path.abspath(inbox)), "Aborting")
    else:
        files_iter = [e.strip() for e in files.split(",")]

    info = None

    if not os.path.exists(dcmf):
        os.makedirs(dcmf)
        print("---> Created a dicom superfolder")

    log_folder = os.path.join(dcmf, "log")

    dcmn = 0

    show_session_info = True

    for dcm in files_iter:
        if os.path.isdir(dcm):
            continue

        ext = dcm.split(".")[-1]

        if os.path.basename(dcm)[0:4] in ["XX_0", "PS_0"]:
            continue

        elif ext == "log":
            if not os.path.exists(log_folder):
                os.makedirs(log_folder)
                print("---> Created log folder")
            do_file(dcm, os.path.join(log_folder, os.path.basename(dcm)))
            continue

        elif ext.lower() == "par":
            info = read_par_info(dcm)

        else:
            try:
                info = read_dicom_info(dcm)
            except Exception:
                continue

        if show_session_info:
            if info and info["sessionid"]:
                print(
                    "---> Sorting dicoms for %s scanned on %s"
                    % (info["sessionid"], info["datetime"])
                )
                show_session_info = False

        if info["seriesNumber"] is None:
            print("---> Skipping file", dcm)
            continue

        sqid = str(info["seriesNumber"] * 10)
        sqfl = os.path.join(dcmf, sqid)

        if not os.path.exists(sqfl):
            os.makedirs(sqfl)
            print(
                "---> Created subfolder for sequence %s %s - %s"
                % (info["sessionid"], sqid, info["seriesDescription"])
            )

        if ext.lower() == "par":
            tgpar = os.path.join(sqfl, os.path.basename(dcm))
            tgpar = tgpar[:-3] + "PAR"
            do_file(dcm, tgpar)

            if os.path.exists(dcm[:-3] + "REC"):
                do_file(dcm[:-3] + "REC", tgpar[:-3] + "REC")
            elif os.path.exists(dcm[:-3] + "rec"):
                do_file(dcm[:-3] + "rec", tgpar[:-3] + "REC")
            else:
                print("---> Warning %s does not exist!" % (dcm[:-3] + "REC"))

        else:
            # --- get info for dcm naming

            dcmn += 1
            if info["SOPInstanceUID"]:
                sop = info["SOPInstanceUID"]
            else:
                sop = "%010d" % (dcmn)

            # --- check if for some reason we are dealing with gzipped dicom files and add an extension when renaming

            if ext == "gz":
                dext = ".gz"
            else:
                dext = ""

            # --- do the deed

            tgf = os.path.join(
                sqfl, "%s-%s-%s.dcm%s" % (clean_name(info["sessionid"]), sqid, sop, dext)
            )
            do_file(dcm, tgf)

    print("---> Processed %d dicom files from %s" % (dcmn, inbox))

    print("---> Done")
    return


def _clean_dicom_legacy(
    folder=".",
    tol_mm=0.2,
    min_files=10,
    verbose="yes",
    move_non_image=True,
    move_incomplete=True,
):
    r"""
    Legacy ``clean_dicom`` implementation retained for ``import_dicom_old``.

    ``clean_dicom [folder=.] [tol_mm=0.2] [min_files=10] [verbose=yes] [move_non_image=True] [move_incomplete=True]``

    Inspects DICOM files within sequence subfolders and identifies DICOM files
    that do not hold imaging data or that contain slice data that does not
    complete a full volume (e.g., from interrupted scans). These files are
    moved to designated removal folders to prevent processing errors during
    DICOM to NIfTI conversion.

    Parameters:
        --folder (str, default '.'):
            The base session folder that contains the 'dicom' subfolder with
            sorted DICOM files organized in numbered sequence subfolders. This
            parameter is typically the session folder path when called from
            import_dicom.

        --tol_mm (float, default 0.2):
            Tolerance in millimeters for clustering slice positions into Z
            indices. This parameter controls how strictly slice positions must
            match to be considered part of the same spatial location. Increase
            this value for acquisitions with slight positional variations;
            decrease it for more stringent matching. Default: 0.2 mm.

        --min_files (int, default 10):
            Minimum number of image files required for a sequence to be
            processed. Sequences with fewer image files than this threshold
            will be skipped and reported. This helps avoid false positives from
            localizer scans or other short sequences. Default: 10.

        --verbose (str, default 'yes'):
            Controls the verbosity of output messages. Set to 'yes' for detailed
            reporting of each sequence processed, including statistics on
            detected volumes and incomplete timepoints. Set to 'no' for minimal
            output showing only critical information and summary statistics.

        --move_non_image (bool, default True):
            Whether to move DICOM files that do not contain imaging data (e.g.,
            files with only metadata, presentation states, or other non-image
            DICOM objects) to the 'dicom/non-image' folder. When True, such
            files are moved; when False, they are left in place.

        --move_incomplete (bool, default True):
            Whether to move DICOM files that are part of incomplete volumes
            (volumes missing slices) to the 'dicom/_REMOVED' folder. When True,
            files from timepoints that do not contain all expected slices are
            moved; when False, they are left in place. This is the primary
            mechanism for handling interrupted scans.

    Notes:
        The command processes sorted DICOM files to identify and remove
        problematic files before conversion to NIfTI format. It is designed to
        handle the common scenario of interrupted fMRI acquisitions where some
        timepoints may be incomplete due to scanner interruption, subject
        motion, or other acquisition issues.

        The cleaning process consists of several steps:

        Sequence folder identification:
            The command scans the 'dicom' folder within the specified session
            folder for sequence subfolders. Sequence subfolders are identified
            by integer names (e.g., '1', '2', '3'). Special folders like
            '_REMOVED' and 'non-image' are excluded from processing. Each
            identified sequence folder is processed independently.

        DICOM header inspection:
            For each file in a sequence folder, the DICOM header is read using
            pydicom with stop_before_pixels=True for efficiency. Files are
            classified as either:

            - Image DICOMs: Files with valid Rows and Columns attributes,
              indicating they contain actual imaging data.
            - Non-image DICOMs: Files without imaging data (e.g., presentation
              states, reports, or metadata-only objects).
            - Unreadable files: Files that cannot be parsed as valid DICOM.

        Slice position clustering:
            For image DICOMs, the command computes a robust slice coordinate by:

            1. Extracting ImagePositionPatient (IPP) and ImageOrientationPatient
               (IOP) from the DICOM header.
            2. Computing the plane normal as: normal = row_direction × col_direction
            3. Calculating the slice coordinate as: coord = dot(normal, IPP)

            This approach works correctly for both standard acquisitions and
            oblique slices. The computed slice coordinates are then clustered
            using the specified tolerance (tol_mm) to identify unique slice
            positions. The number of clusters determines the expected number of
            slices per volume.

        Timepoint grouping:
            Files are grouped into volumetric timepoints using temporal
            information from DICOM headers. The command uses a prioritized
            hierarchy of temporal tags:

            1. TemporalPositionIdentifier (most reliable for fMRI)
            2. AcquisitionNumber
            3. TriggerTime (common in Philips fMRI data)
            4. AcquisitionTime (converted to milliseconds)
            5. InstanceNumber (least reliable, used as last resort)

            This ensures robust timepoint identification across different
            scanner manufacturers and sequence types.

        Volume completeness detection:
            Each timepoint is examined to determine if it contains all expected
            slices. The expected number of slices is computed as the mode of
            slice counts across all timepoints, which is more robust than using
            the total number of unique slice positions (which may include stray
            slices from partial volumes).

            A timepoint is considered incomplete if:

            - It contains fewer unique slice positions than expected.
            - Its slices cannot be mapped to the identified slice position
              clusters (due to invalid or missing IPP/IOP data).

        File removal:
            Based on the move_non_image and move_incomplete parameters:

            - Non-image DICOM files are moved to: dicom/non-image/
            - Files from incomplete volumes are moved to: dicom/_REMOVED/

            Files are renamed during the move to avoid collisions, with duplicate
            filenames receiving a numeric suffix (e.g., file__dup1.dcm,
            file__dup2.dcm).

        Edge cases and considerations:
            - If slice coordinates cannot be computed (missing IPP/IOP), the
              sequence is skipped with a warning.
            - Multi-echo or multi-phase sequences may require manual inspection
              if they share acquisition numbers but represent complete volumes.
            - Very short sequences (< min_files) are skipped to avoid false
              positives.
            - The command preserves the original DICOM folder structure except
              for moved files.

    Examples:
        Clean DICOM files in a single session (called from import_dicom)::

            clean_dicom(folder="/data/study/sessions/subj001")

        Clean DICOM files with custom parameters::

            clean_dicom(
                folder="/data/study/sessions/subj001",
                tol_mm=0.5,
                min_files=20,
                verbose="yes"
            )

        Clean DICOM files but only move non-image files::

            clean_dicom(
                folder="/data/study/sessions/subj001",
                move_non_image=True,
                move_incomplete=False
            )
    """

    def _is_image_dicom(ds):
        """Check if DICOM dataset contains imaging data."""
        return ds is not None and hasattr(ds, "Rows") and hasattr(ds, "Columns")

    def _safe_float(x, default=None):
        """Safely convert value to float."""
        try:
            return float(x)
        except Exception:
            return default

    def _read_header(path):
        """Read DICOM header without pixel data for efficiency."""
        try:
            # Only read specific tags we need for volume detection
            # This provides ~2-3x speedup vs reading all tags
            specific_tags = [
                (0x0020, 0x0032),  # ImagePositionPatient
                (0x0020, 0x0037),  # ImageOrientationPatient
                (0x0020, 0x1041),  # SliceLocation
                (0x0020, 0x0100),  # TemporalPositionIdentifier
                (0x0020, 0x0012),  # AcquisitionNumber
                (0x0028, 0x0010),  # Rows
                (0x0028, 0x0011),  # Columns
                (0x0020, 0x000E),  # SeriesInstanceUID
                (0x0008, 0x0018),  # SOPInstanceUID
                (0x0020, 0x0013),  # InstanceNumber
                (0x0008, 0x0032),  # AcquisitionTime
                (0x0018, 0x1060),  # TriggerTime
            ]
            ds = pydicom.filereader.dcmread(
                path,
                stop_before_pixels=True,
                specific_tags=specific_tags,
                force=False,  # Don't force reading invalid DICOM files
            )
            return ds
        except Exception:
            return None

    def _slice_coordinate(ds):
        """
        Compute robust slice coordinate using plane normal.
        coord = dot(normal, IPP) where normal = row_cosines × col_cosines
        Works across oblique acquisitions.
        """
        ipp = getattr(ds, "ImagePositionPatient", None)
        iop = getattr(ds, "ImageOrientationPatient", None)
        if ipp is None or iop is None:
            return None

        ipp = np.array([_safe_float(v) for v in ipp], dtype=float)
        if np.any(np.isnan(ipp)):
            return None

        iop = [_safe_float(v) for v in iop]
        if any(v is None for v in iop) or len(iop) != 6:
            return None

        row = np.array(iop[0:3], dtype=float)
        col = np.array(iop[3:6], dtype=float)
        normal = np.cross(row, col)
        nrm = np.linalg.norm(normal)
        if nrm == 0:
            return None
        normal = normal / nrm

        return float(np.dot(normal, ipp))

    def _cluster_values(values, tol):
        """
        Cluster numeric values into bins with tolerance.
        Returns cluster centers sorted, plus mapping function.
        """
        vals = sorted(v for v in values if v is not None)
        if not vals:
            return [], (lambda x: None)

        clusters = []
        current = [vals[0]]
        for v in vals[1:]:
            if abs(v - np.mean(current)) <= tol:
                current.append(v)
            else:
                clusters.append(float(np.mean(current)))
                current = [v]
        clusters.append(float(np.mean(current)))

        def assign(v):
            if v is None:
                return None
            idx = int(np.argmin([abs(v - c) for c in clusters]))
            if abs(v - clusters[idx]) <= tol:
                return clusters[idx]
            return None

        return clusters, assign

    def _choose_time_key(ds):
        """
        Choose temporal key for grouping slices into volumes.
        Priority: TemporalPositionIdentifier > AcquisitionNumber >
                  TriggerTime > AcquisitionTime > InstanceNumber
        """
        if hasattr(ds, "TemporalPositionIdentifier"):
            v = getattr(ds, "TemporalPositionIdentifier", None)
            if v is not None:
                return ("TPI", int(v))

        if hasattr(ds, "AcquisitionNumber"):
            v = getattr(ds, "AcquisitionNumber", None)
            if v is not None:
                return ("ACQ", int(v))

        if hasattr(ds, "TriggerTime"):
            v = _safe_float(getattr(ds, "TriggerTime", None))
            if v is not None:
                return ("TRIG", int(round(v)))

        at = getattr(ds, "AcquisitionTime", None)
        if at:
            try:
                s = str(at)
                hh = int(s[0:2])
                mm = int(s[2:4])
                ss = float(s[4:])
                sec = hh * 3600 + mm * 60 + ss
                return ("AT", int(round(sec * 1000)))
            except Exception:
                pass

        inst = getattr(ds, "InstanceNumber", None)
        if inst is not None:
            return ("INST", int(inst))

        return ("UNK", 0)

    def _process_sequence_folder(seq_folder, seq_name, removed_dir, non_image_dir):
        """Process a single sequence folder for incomplete volumes."""

        # Collect all files in sequence folder (use scandir for speed)
        # Pre-filter by extension to avoid reading non-DICOM files
        all_paths = []
        try:
            with os.scandir(seq_folder) as entries:
                for entry in entries:
                    if entry.is_file():
                        # Only process files that look like DICOMs
                        name_lower = entry.name.lower()
                        if (
                            name_lower.endswith(".dcm")
                            or name_lower.endswith(".dcm.gz")
                            or "."
                            not in entry.name  # DICOM files often have no extension
                            or name_lower.endswith(".ima")
                        ):
                            all_paths.append(entry.path)
        except Exception:
            # Fallback to os.walk if scandir fails
            for root, _, files in os.walk(seq_folder):
                for fn in files:
                    all_paths.append(os.path.join(root, fn))

        if not all_paths:
            return

        # Print early progress indication
        if verbose:
            print(
                f"---> Inspecting sequence {seq_name} (evaluating {len(all_paths)} files):"
            )

        # Batch read files into memory first (one sequential pass - faster on spinning disk)
        # Read first 64KB of each file (DICOM headers typically <16KB, 64KB provides safety margin)
        from io import BytesIO

        file_data = {}
        for p in all_paths:
            try:
                with open(p, "rb") as f:
                    file_data[p] = f.read(65536)  # 64KB
            except Exception:
                pass

        # Read headers and classify files (parsing from memory is faster)
        items = []
        non_images = []
        unreadable = 0

        specific_tags = [
            (0x0020, 0x0032),
            (0x0020, 0x0037),
            (0x0020, 0x1041),
            (0x0020, 0x0100),
            (0x0020, 0x0012),
            (0x0028, 0x0010),
            (0x0028, 0x0011),
            (0x0020, 0x000E),
            (0x0008, 0x0018),
            (0x0020, 0x0013),
            (0x0008, 0x0032),
            (0x0018, 0x1060),
        ]

        for p, data in file_data.items():
            try:
                ds = pydicom.filereader.dcmread(
                    BytesIO(data),
                    stop_before_pixels=True,
                    specific_tags=specific_tags,
                    force=False,
                )
            except Exception:
                unreadable += 1
                continue

            if not _is_image_dicom(ds):
                non_images.append(p)
                continue

            ser = getattr(ds, "SeriesInstanceUID", "NO_SERIES_UID")
            sop = getattr(ds, "SOPInstanceUID", os.path.basename(p))
            sc = _slice_coordinate(ds)
            tk = _choose_time_key(ds)

            items.append(
                {
                    "path": p,
                    "series": ser,
                    "sop": sop,
                    "slice_coord": sc,
                    "time_key": tk,
                }
            )

        # Skip if too few image files
        if len(items) < min_files:
            if verbose:
                print(
                    f"     Sequence {seq_name}: only {len(items)} image files, skipping (< {min_files})"
                )
                print()
            return

        # Group by series (should typically be one series per folder)
        by_series = defaultdict(list)
        for it in items:
            by_series[it["series"]].append(it)

        to_remove = []

        for series_uid, series_items in by_series.items():
            # Cluster slice coords into Z positions
            coords = [it["slice_coord"] for it in series_items]
            centers, assign_z = _cluster_values(coords, tol_mm)

            if not centers:
                if verbose:
                    print(
                        f"     Sequence {seq_name}: cannot cluster slice positions (missing/invalid IPP/IOP), skipping"
                    )
                    print()
                continue

            expected_z = len(centers)

            # Assign each file to a Z cluster
            valid = []
            unmapped = []
            for it in series_items:
                zc = assign_z(it["slice_coord"])
                if zc is None:
                    unmapped.append(it)
                else:
                    it2 = dict(it)
                    it2["z_center"] = zc
                    valid.append(it2)

            # Group by timepoint
            vols = defaultdict(list)
            for it in valid:
                vols[it["time_key"]].append(it)

            # Determine mode of z-count across volumes (more robust)
            z_counts = [
                len(set(it["z_center"] for it in vitems)) for vitems in vols.values()
            ]
            if z_counts:
                mode_z = Counter(z_counts).most_common(1)[0][0]
            else:
                mode_z = expected_z

            # Flag incomplete volumes
            flagged = []
            for tk, vitems in vols.items():
                zset = set(it["z_center"] for it in vitems)
                if len(zset) != mode_z:
                    flagged.extend(vitems)

            # Re-check unmapped files - they might be non-image DICOMs
            # that passed the initial Rows/Columns check
            unmapped_non_image = []
            unmapped_incomplete = []
            for it in unmapped:
                # Re-read the full header to check more thoroughly
                ds = _read_header(it["path"])
                # Check if this is truly an image by looking for additional image attributes
                if ds and (
                    not hasattr(ds, "ImagePositionPatient")
                    or not hasattr(ds, "ImageOrientationPatient")
                    or not hasattr(ds, "SliceLocation")
                ):
                    # Missing critical image geometry - likely non-image
                    unmapped_non_image.append(it["path"])
                else:
                    # Has some geometry but couldn't be clustered - incomplete
                    unmapped_incomplete.append(it["path"])

            # Add unmapped non-images to the non_images list
            non_images.extend(unmapped_non_image)

            # Report if verbose
            if verbose:
                bad_tks = sorted(set(it["time_key"] for it in flagged))
                print(
                    f"     Files (image): {len(series_items)} (valid: {len(valid)}, unmapped: {len(unmapped)})"
                )
                print(
                    f"     Slice clusters: {expected_z} (mode across volumes: {mode_z})"
                )
                print(f"     Timepoints detected: {len(vols)}")
                print(f"     Incomplete timepoints flagged: {len(bad_tks)}")
                if unmapped_non_image:
                    print(
                        f"     Unmapped files reclassified as non-image: {len(unmapped_non_image)}"
                    )

            # Add only truly incomplete unmapped files to removal list
            for p in unmapped_incomplete:
                to_remove.append(p)
            for it in flagged:
                to_remove.append(it["path"])

        # Move non-image files if requested
        if move_non_image and non_images:
            os.makedirs(non_image_dir, exist_ok=True)
            for p in non_images:
                if os.path.exists(p):
                    dst = os.path.join(non_image_dir, os.path.basename(p))
                    # Avoid collisions
                    if os.path.exists(dst):
                        base, ext = os.path.splitext(os.path.basename(p))
                        i = 1
                        while os.path.exists(dst):
                            dst = os.path.join(non_image_dir, f"{base}__dup{i}{ext}")
                            i += 1
                    os.rename(p, dst)
            if verbose:
                print(f"     Moved {len(non_images)} non-image files to non-image/")

        # Move incomplete volume files if requested
        if move_incomplete and to_remove:
            os.makedirs(removed_dir, exist_ok=True)
            moved = 0
            for p in set(to_remove):  # Deduplicate
                if os.path.exists(p):
                    dst = os.path.join(removed_dir, os.path.basename(p))
                    # Avoid collisions
                    if os.path.exists(dst):
                        base, ext = os.path.splitext(os.path.basename(p))
                        i = 1
                        while os.path.exists(dst):
                            dst = os.path.join(removed_dir, f"{base}__dup{i}{ext}")
                            i += 1
                    os.rename(p, dst)
                    moved += 1
            if verbose:
                print(f"     Moved {moved} files from incomplete volumes to _REMOVED/")

        # Add blank line at end of sequence report
        if verbose:
            print()

    # Main execution
    print("Running clean_dicom\n==================")

    verbose = true_or_false(verbose)

    dicom_folder = os.path.join(folder, "dicom")

    if not os.path.exists(dicom_folder):
        print(f"---> DICOM folder not found: {dicom_folder}")
        print("---> Skipping clean_dicom")
        return

    # Create removal directories
    removed_dir = os.path.join(dicom_folder, "_REMOVED")
    non_image_dir = os.path.join(dicom_folder, "non-image")

    # Find sequence folders (integer-named directories)
    sequence_folders = []
    for item in os.listdir(dicom_folder):
        item_path = os.path.join(dicom_folder, item)
        if os.path.isdir(item_path) and item.isdigit():
            sequence_folders.append((item, item_path))

    if not sequence_folders:
        print("---> No sequence folders found in dicom/")
        print("---> Skipping clean_dicom")
        return

    sequence_folders.sort(key=lambda x: int(x[0]))

    if verbose:
        print(f"---> Found {len(sequence_folders)} sequence folder(s) to process")

    # Process each sequence folder
    for seq_name, seq_path in sequence_folders:
        _process_sequence_folder(seq_path, seq_name, removed_dir, non_image_dir)

    print("---> Done")
    return
