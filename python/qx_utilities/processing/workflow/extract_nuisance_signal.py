#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``workflow/extract_nuisance_signal.py``

Extracts the nuisance signal used in the regressions.
"""

# Created by Grega Repovs on 2016-12-17.
# Code split from dofcMRIp_core gCodeP/preprocess codebase.
# Copyright (c) Grega Repovs. All rights reserved.

import os
import textwrap
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from functools import partial

import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog
from qx_utilities.processing.workflow import dryrun
from qx_utilities.processing.workflow.dryrun import mcommand


# --------------------------------------------------------- the command preamble
#
# What the command does, shown once at the head of every session report, and
# the parameters it quotes back. A dedented block rather than lines carrying
# their own `\n    `: this is prose, it is read as prose, and it should be
# reviewable as prose. The parameter list is a list rather than a format string
# with one interpolation each, so it cannot drift from `options`.

# the only one of the four that names the files it writes, so it is a template.
# Wrapped here for review and re-wrapped after substitution -- `nifti_tail` and
# `img_suffix` are empty as often as not, and a paragraph laid out around their
# widest form comes out ragged when they are short
NUISANCE_PURPOSE = """\
Nuisance signal is extracted from each of the specified BOLD files. The results
are saved as {boldname}[N]{nifti_tail}.nuisance files in the
images{img_suffix}/movement subfolder. Only the images named by --bolds are
processed. Note that the NIfTI volume image is used even when the target format
is CIFTI."""

NUISANCE_PARAMETERS = ["wbmask", "sessionroi", "nroi", "shrinknsroi"]

# what the preamble is wrapped to
PURPOSE_WIDTH = 79


# -> @register_command(
#        description="Extract nuisance signal from BOLD images.",
#         type="processing.session")
def extract_nuisance_signal(sinfo, options, overwrite=False, thread=0):
    """
    ``extract_nuisance_signal [... processing options]``

    Extract nuisance signal from volume BOLD files.

    ..  qx_command:
        type: processing.session

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the session information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --bolds (str, default 'rest'):
            Which bold images (as they are specified in the batch.txt file) to
            copy over. It can be a single type (e.g. 'task'), a pipe separated
            list (e.g. 'WM|Control|rest') or 'all' to copy all.

        --boldname (str, default 'bold'):
            The default name of the bold files in the images folder.

        --nifti_tail (str, default ''):
            The tail of NIfTI volume images to use.

        --bold_variant (str, default ''):
            Optional variant of bold preprocessing. If specified, the BOLD
            images in `images/functional<bold_variant>` will be processed.

        --img_suffix (str, default ''):
            Specifies a suffix for 'images' folder to enable support for
            multiple parallel workflows. Empty if not used.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --wbmask (str, default ''):
            A path to an optional file that specifies which regions are to be
            excluded from the whole-brain mask. It can be used in the case of
            ROI analyses for which one does not want to include the ROI specific
            signals in the global signal regression.

        --nroi (str, default ''):
            The path to additional nuisance regressors file. It can be either a
            binary mask or a '.names' file that specifies the ROI to be used.
            Based on other options, the ROI can be further masked by session
            specific files or not masked at all (see Use section below).

        --sessionroi (str, default ''):
            A string specifying which session specific mask to use for further
            masking the additional roi. The two options are 'wb' or 'aseg' for
            whole brain mask or FreeSurfer aseg+aparc mask, respectively.

        --shrinknsroi (str, default 'true'):
            A string specifying whether to shrink ('true') the whole
            brain and white matter masks or not ('false').

    Output files:
        The command generates the following files:

        - `bold[N]<nifti_tail>.nuisance`
              A text file that lists for each volume frame the information
              on mean intensity across the ventricle, white matter and whole
              brain voxels, and any additional nuisance ROI specified using
              parameters. The file is stored in the
              `images<img_suffix>/functional<bold_variant>/movement` folder.

        - `bold[N]<nifti_tail>_nuisance.png`
            A PNG image of axial slices of the first BOLD frame over which
            the identified nuisance regions are overlayed. Ventricles in
            green, white matter in red and the rest of the brain in blue.
            The ventricle and white matter regions are defined based on
            FreeSurfer segmentation. Each region is "trimmed" before use, so
            that there is at least one voxel buffer between each nuisance
            region mask. The image is stored in
            images<img_suffix>/ROI/nuisance<bold_variant>`.

        - `bold[N]<nifti_tail>_nuisance.<image format>`
            An image file of the relevant image format that holds the same
            information as the above PNG. It is a file of five volumes, the
            first volume holds the first BOLD frame, the second the whole
            brain mask, the third the ventricles mask and the fourth the
            white matter mask. The fifth volume stores all three masks coded
            as 1 (whole brain), 2 (ventricles), or 3 (white matter). The
            image is stored in `images<img_suffix>/ROI/nuisance<bold_variant>`
            folder.

    Notes:
        extract_nuisance_signal is used to extract nuisance signal from volume
        BOLD files to be used in the latter steps of preprocessing,
        specifically for regression of nuisance signals. By default, it
        extracts nuisance signals from ventricles, white matter and whole
        brain. Whole brain is defined as those parts of the brain that are not
        ventricles or white matter, which results in whole brain to mostly
        overlap with gray matter.

        Using parameters listed below, it is also possible to specify
        additional ROIs for which nuisance signal is to be extracted and/or ROI
        that are to be excluded from the whole brain mask.

        To exclude specific ROI from the whole brain mask, use the '--wbmask'
        option. This should be a path to a file that specifies, which ROI are
        to be excluded from the whole-brain mask. The reason for exclusion
        might be when one does not want the signals from specific ROI to be
        included in the global signal regression, thereby resolving some issues
        taken as arguments against using global signal regression. The file can
        be either a binary mask, or a '.names' file. In the latter case, it is
        possible to additional mask the ROI to be excluded based on session
        specific aseg+aparc image (see description of .names file format).

        Another option is to include additional independent nuisance regions
        that might or might not overlap with the existing masks. Two parameters
        are used to specify this. The first is the '--nroi' parameter. This,
        again, is a path to either a binary image or a '.names' file. In the
        latter case, it is again possible to mask the additional ROI either by
        the binary whole brain mask or the individuals aseg+aparc file. To
        achieve this, set the additional '--sessionroi' parameter to 'wb' or
        'aseg', respectively. If some additional ROI are to be excluded, even
        though they fall outside the brain, then these are to be listed as
        comma separated list of ROI names (that match the ROI names in the
        .names file), separated from the path by a pipe ('|') symbol. For
        instance if one also would like to include eyes and scull as two
        additional nuiscance regions, one has to create a volume mask + a
        .names file pair, and pass it as the '--nroi' parameter, e.g.::

            --nroi="<path to ROI>/nroi.names|eyes,scull"

        Extra notes and dependencies:
            When 'cifti' is the specified image target, the related nifti volume
            files will be processed as only they provide all the information for
            computing the relevant parameters

            The command runs the general_extract_nuisance.m Matlab function for
            actual nuisance signal extraction. It expects that bold images,
            whole brain masks, and aseg+aparc imags to be present in the
            expected locations.

    Examples:
        ::

            qunex extract_nuisance_signal \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --bolds=all \\
                --parsessions=10
    """
    log = ReportLog()

    report = {
        "bolddone": 0,
        "boldok": 0,
        "boldfail": 0,
        "boldmissing": 0,
        "boldskipped": 0,
    }

    log.rule()
    log.info(f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]")
    log.action("Extracting", "BOLD nuisance signal ...", options["run"], level="info")
    log.blank()
    log.info(textwrap.fill(
        NUISANCE_PURPOSE.format(
            boldname=options["boldname"],
            nifti_tail=options["nifti_tail"],
            img_suffix=options["img_suffix"],
        ),
        PURPOSE_WIDTH,
    ))

    pc.do_options_check(options, sinfo, "extract_nuisance_signal")
    d = pc.get_session_folders(sinfo, options)

    if overwrite:
        ostatus = "will"
    else:
        ostatus = "will not"

    log.step("Using parameters when extracting nuisance signal")
    for name in NUISANCE_PARAMETERS:
        log.detail(f"--{name}: {options[name]}")

    log.step(f"Working on BOLD images in {d['s_bold']}")
    log.detail(f"images{options['img_suffix']}/functional{options['bold_variant']} will be processed")
    log.detail(f"the resulting files will be in {d['s_bold_mov']}")
    log.detail(f"{', '.join(options['bolds'].split('|'))} BOLD files will be processed (see --bolds)")
    log.detail(f"existing nuisance files {ostatus} be overwritten (see --overwrite)")

    bolds, bskip, report["boldskipped"] = pc.use_or_skip_bold(sinfo, options, _log=log)

    parelements = options["parelements"]
    log.info(f"Processing {parelements} BOLDs in parallel")

    if parelements == 1:  # serial execution
        for b in bolds:
            # process
            result = execute_extract_nuisance_signal(sinfo, options, overwrite, b)

            # merge r
            log.raw(result["r"])

            # merge report
            temp_report = result["report"]
            report["bolddone"] += temp_report["bolddone"]
            report["boldok"] += temp_report["boldok"]
            report["boldfail"] += temp_report["boldfail"]
            report["boldmissing"] += temp_report["boldmissing"]
    else:  # parallel execution
        # create a multiprocessing Pool
        process_pool_executor = ProcessPoolExecutor(parelements)
        # process
        f = partial(execute_extract_nuisance_signal, sinfo, options, overwrite)
        results = process_pool_executor.map(f, bolds)

        # merge r and report
        for result in results:
            log.raw(result["r"])
            temp_report = result["report"]
            report["bolddone"] += temp_report["bolddone"]
            report["boldok"] += temp_report["boldok"]
            report["boldfail"] += temp_report["boldfail"]
            report["boldmissing"] += temp_report["boldmissing"]

    log.blank()
    log.info(f"Bold nuisance signal extraction completed on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}")
    log.rule()
    rstatus = (
        "BOLDS done: %(bolddone)2d, missing data: %(boldmissing)2d, failed: %(boldfail)2d, skipped: %(boldskipped)2d, processed: %(boldok)2d"
        % (report)
    )

    return log.result(rstatus, report["boldmissing"] + report["boldfail"], sinfo["id"])


def execute_extract_nuisance_signal(sinfo, options, overwrite, boldinfo):

    # prepare return variables
    log = ReportLog()
    report = {"bolddone": 0, "boldok": 0, "boldfail": 0, "boldmissing": 0}

    log.step("Working on " + boldinfo["name"] + " ...")

    try:
        # --- filenames
        f = pc.get_file_names(sinfo, options)
        f.update(pc.get_bold_file_names(sinfo, boldinfo["name"], options))
        d = pc.get_session_folders(sinfo, options)

        # --- check for data availability

        log.detail("checking for data")
        status = True

        # --- bold mask
        status = pc.check_for_file(f["bold1_brain_mask"],
            "bold brain mask present",
            f"bold brain mask missing [{f['bold1_brain_mask']}]",
            status=status,
            _log=log,
        )

        # --- aseg
        astat = pc.check_for_file(f["fs_aseg_bold"],
            "freesurfer aseg present",
            f"freesurfer aseg missing [{f['fs_aseg_bold']}]",
            status=True,
            _log=log,
        )
        if not astat:
            astat = pc.check_for_file(f["fs_aparc_bold"],
                "freesurfer aparc present",
                f"freesurfer aparc missing [{f['fs_aparc_bold']}]",
                status=True,
                _log=log,
            )
            segfile = f["fs_aparc_bold"]
        else:
            segfile = f["fs_aseg_bold"]

        status = status and astat

        # --- bold
        status = pc.check_for_file(f["bold_vol"],
            "bold data present",
            f"bold data missing [{f['bold_vol']}]",
            status=status,
            _log=log,
        )

        # --- check
        if not status:
            log.error("Files missing, skipping this bold run!")
            report["boldmissing"] += 1
            return {"r": log.text, "report": report}

        # --- running nuisance extraction

        comm = (
            "%s \"try general_extract_nuisance('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, %s); catch ME, general_report_crash(ME); exit(1), end; exit\""
            % (
                mcommand,  # --- matlab command to run
                f["bold_vol"],  # --- bold volume file to process
                segfile,  # --- aseg or aparc file
                f["bold1_brain_mask"],  # --- bold brain mask
                d["s_bold_mov"],  # --- functional/movement subfolder
                d["s_nuisance"],  # --- roi/nuisance subfolder
                options["wbmask"],  # --- mask to exclude ROI from WB
                options["sessionroi"],  # --- a mask used to specify session specific WB
                options["nroi"],  # --- additional nuisance regressors ROI
                options["shrinknsroi"],  # --- shrink nuisance signal ROI
                "true",
            )
        )  # --- verbosity

        if options["print_command"] == "yes":
            log.pipeline_command(comm, title="Running:")

        runit = True
        if os.path.exists(f["bold_nuisance"]):
            report["bolddone"] += 1
            runit = False
        endlog, status, failed = dryrun.run_external(
            log,
            options,
            f["bold_nuisance"],
            comm,
            "... running matlab general_extract_nuisance on %s" % (f["bold_vol"]),
            overwrite=overwrite,
            thread=sinfo["id"],
            remove=options["log"] == "remove",
            task=options["command_ran"],
            logfolder=options["comlogs"],
            logtags=[
                options["bold_variant"],
                options["logtag"],
                "B%d" % boldinfo["bold_number"],
            ],
            shell=True,
        )
        status = pc.check_for_file(
            f["bold_nuisance"],
            bad=f"Matlab/Octave has failed preprocessing BOLD using command: {comm}",
            bad_level="error",
            _log=log,
        )

        if runit and status:
            report["boldok"] += 1
        elif runit:
            report["boldfail"] += 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        report["boldfail"] += 1
    except Exception:
        log.error(f"Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n")
        report["boldfail"] += 1

    return {"r": log.text, "report": report}
