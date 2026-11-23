#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_diffusion.py``

The HCP diffusion preprocessing pipeline.
"""

import glob
import os
import os.path

import qx_utilities.general.folders as gf
import qx_utilities.processing.core as pc
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.hcp.hcp_utils import (
    _check_dwi_echospacing,
    check_gdc_coeff_file,
    check_inline_parameter_use,
    do_hcp_options_check,
)


def _find_dwi_files(dwis, direction, hcp):
    """
    Match the batch file DWI names to the images in the unprocessed folder.

    Parameters:
        dwis: the batch file DWI names keyed by their sequence number.
        direction: the phase encoding labels keyed by ``pos``/``neg``.
        hcp: the session's HCP paths.

    Returns:
        ``(dwi_data, has_pair)``: each image's direction and file (``EMPTY``
        for a missing opposite pair) keyed by name, and whether any image has
        its opposite pair.
    """
    has_pair = False
    # get dwi files
    dwi_data = dict()
    # sort by temporal order as specified in batch
    for dwi in sorted(dwis):
        for ddir, dext in direction.items():
            dwi_files = glob.glob(
                os.path.join(hcp["DWI_source"], "*_%s.nii.gz" % (dext))
            )

            for dwi_file in dwi_files:
                if dwis[dwi] in dwi_file:
                    dwi_dict = {"dir": ddir, "ext": dext, "file": dwi_file}
                    dwi_data[dwis[dwi]] = dwi_dict

                    # add matching pair if it does not exist
                    opposite_dir = "pos"
                    if ddir == "pos":
                        opposite_dir = "neg"
                    opposite_exp = direction[opposite_dir]

                    dwi_matching = dwis[dwi].replace(dext, opposite_exp)

                    if dwi_matching not in dwi_data:
                        dwi_dict = {
                            "dir": opposite_dir,
                            "ext": opposite_exp,
                            "file": "EMPTY",
                        }
                        dwi_data[dwi_matching] = dwi_dict
                    else:
                        has_pair = True

    return dwi_data, has_pair


def _resolve_dwi_data(dwis, direction, hcp, options, _log):
    """
    Set up the posData and negData inputs from the unprocessed DWI images.

    Unless ``hcp_dwi_posdata``/``hcp_dwi_negdata`` name the images, the
    session's unprocessed Diffusion folder is searched for the DWI images in
    the batch file, in their temporal order. Only cross-sectional processing
    reads these images.

    Parameters:
        dwis: the batch file DWI names keyed by their sequence number.
        direction: the phase encoding labels keyed by ``pos``/``neg``.
        hcp: the session's HCP paths.
        options: the command options.
        _log: the log to report into.

    Returns:
        ``(pos_data, neg_data, has_pair, run)``: the ``@`` separated images of
        each direction, whether any image has its opposite pair, and whether
        the data was found.
    """
    run = True
    pos_data, neg_data = None, None

    # QuNex's automatic posData and negData setup
    has_pair = False
    if (
        options["hcp_dwi_posdata"] is None
        and options["hcp_dwi_negdata"] is None
    ):
        dwi_data, has_pair = _find_dwi_files(dwis, direction, hcp)

        # prepare pos and neg files
        dwi_files = dict()
        for _, dwi in dwi_data.items():
            if not has_pair and dwi["file"] == "EMPTY":
                continue

            if dwi["dir"] in dwi_files:
                dwi_files[dwi["dir"]] = (
                    dwi_files[dwi["dir"]] + "@" + dwi["file"]
                )
            else:
                dwi_files[dwi["dir"]] = dwi["file"]

        for ddir in ["pos", "neg"]:
            if ddir not in dwi_files:
                break

            dfiles = dwi_files[ddir].split("@")

            if dfiles and dfiles != [""] and dfiles != "EMPTY":
                _log.step(f"The following {ddir} direction files were found:")
                for dfile in dfiles:
                    _log.info(f"     {os.path.basename(dfile)}")
            else:
                _log.error(f"No {ddir} direction files were found! Both images with pos and neg directions are required for hcp_diffusion. If you have data with only one direction, you can use dwi_legacy_gpu.")
                run = False
                break

        # if both dirs are missing
        if "pos" not in dwi_files and "neg" not in dwi_files:
            _log.error(
                "No DWI data found, check your batchfile and command parameters!"
            )
            run = False
        elif "pos" not in dwi_files:
            pos_data = "EMPTY"
            neg_data = dwi_files["neg"]
        elif "neg" not in dwi_files:
            pos_data = dwi_files["pos"]
            neg_data = "EMPTY"
        else:
            pos_data = dwi_files["pos"]
            neg_data = dwi_files["neg"]

    # if both are None something is wrong
    elif (
        options["hcp_dwi_posdata"] is not None
        and options["hcp_dwi_negdata"] is None
    ) or (
        options["hcp_dwi_posdata"] is None
        and options["hcp_dwi_negdata"] is not None
    ):
        _log.error(
            "When manually overriding posData and negData, you need to set both hcp_dwi_posdata and hcp_dwi_negdata parameters. Set to EMPTY if you do not have data for one of the directions. If there are no pos/neg pairs, also set the --hcp_dwi_combinedata flag."
        )
        run = False
    else:
        pos_data = _dwi_paths_from_option(options["hcp_dwi_posdata"], hcp)
        neg_data = _dwi_paths_from_option(options["hcp_dwi_negdata"], hcp)

    return pos_data, neg_data, has_pair, run


def _dwi_paths_from_option(images, hcp):
    """
    Turn a comma separated hcp_dwi_posdata/negdata value into posData/negData.

    Parameters:
        images: the comma separated image names, ``EMPTY`` for none.
        hcp: the session's HCP paths.

    Returns:
        the ``@`` separated images, each in the unprocessed Diffusion folder.
    """
    paths = []
    for image in images.split(","):
        if image != "EMPTY":
            paths.append(hcp["DWI_source"] + "/" + image)
        else:
            paths.append(image)
    return "@".join(paths)


def _dwi_batch_has_pair(dwis, direction):
    """
    Whether any DWI in the batch file has its opposite phase encoding pair.

    Cross-sectional processing works this out from the unprocessed images, a
    longitudinal run has to do without them. The pairing decides the default
    ``--combine-data-flag``, which the longitudinal Post-Eddy step still uses,
    so it is worked out from the names the batch file declares.

    Parameters:
        dwis: the batch file DWI names keyed by their sequence number.
        direction: the phase encoding labels keyed by ``pos``/``neg``.

    Returns:
        whether a pos/neg pair is declared.
    """
    names = set(dwis.values())
    for name in names:
        for ddir, dext in direction.items():
            opposite = direction["neg" if ddir == "pos" else "pos"]
            if name.endswith("_" + dext) and name[: -len(dext)] + opposite in names:
                return True
    return False


def _check_longitudinal_dwi(hcp, options, _log):
    """
    Check for the cross-sectional output a longitudinal diffusion run reads.

    In longitudinal mode DiffPreprocPipeline.sh does not read the unprocessed
    DWI images: it copies the cross-sectional Pre-Eddy and Eddy outputs into
    the longitudinal session and runs only the Post-Eddy step there.

    Parameters:
        hcp: the session's HCP paths.
        options: the command options.
        _log: the log to report into.

    Returns:
        whether the cross-sectional output is present.
    """
    _log.step("Longitudinal mode: DWI images are not needed, the cross-sectional Pre-Eddy and Eddy outputs are reused.")
    if options["hcp_dwi_posdata"] is not None or options["hcp_dwi_negdata"] is not None:
        _log.detail("hcp_dwi_posdata and hcp_dwi_negdata are not used in longitudinal mode")

    dwifolder = os.path.join(hcp["base"], options["hcp_dwi_name"] or "Diffusion")
    if os.path.isdir(dwifolder):
        _log.step("Cross-sectional hcp_diffusion results present.")
        return True

    _log.error(f"Cross-sectional hcp_diffusion results missing [{dwifolder}]! Run hcp_diffusion without --longitudinal first.")
    return False


def _create_dummy_bval_bvec(pos_data, neg_data, options, _log):
    """
    Create dummy bval and bvec files beside the DWI images missing them.

    Parameters:
        pos_data: the ``@`` separated pos direction images.
        neg_data: the ``@`` separated neg direction images.
        options: the command options.
        _log: the log to report into.
    """
    for image in pos_data.split("@") + neg_data.split("@"):
        if image == "EMPTY":
            continue
        for ext, content in [(".bval", "0\n"), (".bvec", "0\n0\n0\n")]:
            target = image.replace(".nii.gz", ext)
            if os.path.isfile(target):
                continue
            if options["run"] != "run":
                _log.step(f"test, not created: dummy {ext[1:]} file for [{image}].")
                continue
            _log.step(f"Creating dummy {ext[1:]} file for [{image}].")
            with open(target, "w") as f:
                f.write(content)


def hcp_diffusion(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_diffusion [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run the Diffusion step of HCP Pipeline (DiffPreprocPipeline.sh). This
    command uses GPUs by default so CUDA Libraries are required for this to
    work. Use the hcp_nogpu flag to run without a GPU if needed, note that this
    results in much slower processing speed.

    ..  qx_command:
        type: processing.session

    Warning:
        The code expects the first HCP preprocessing step (hcp_pre_freesurfer)
        to have been run and finished successfully. It expects the DWI data to
        have been acquired in phase encoding reversed pairs, which should be
        present in the Diffusion folder in the session's root hcp folder.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --studyfolder (str):
            The path to the study folder. The sessions are in its `sessions`
            folder, unless --sessionsfolder names another one.

        --sessionsfolder (str, default '<studyfolder>/sessions'):
            The path to the folder with the sessions. Set it only when the
            sessions are not in the `sessions` folder of the study. With
            neither --studyfolder nor --sessionsfolder given, the current
            folder is used.

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

        --hcp_dwi_echospacing (str, default detailed below):
            Echo Spacing of DWI images in s. By default, QuNex will try to get
            this value from the imaging data.

        --use_sequence_info (str, default 'all'):
            A pipe, comma or space separated list of inline sequence
            information to use in preprocessing of specific image
            modalities.

            Example specifications:

            - `all`
                Use all present inline information for all modalities.
            - `DwellTime`
                Use DwellTime information for all modalities.
            - `T1w:all`
                Use all present inline information for T1w modality.
            - `SE:EchoSpacing`
                Use EchoSpacing information for Spin-Echo fieldmap images.
            - `none`
                Do not use inline information.

            Modalities: 'T1w', 'T2w', 'SE', 'BOLD', 'dMRi'.
            Inline information: 'TR', 'PEDirection', 'EchoSpacing' 'DwellTime',
            'ReadoutDirection'.

            If information is not specified it will not be used. More
            general specification (e.g. `all`) implies all more specific
            cases (e.g. `T1w:all`).

        --hcp_dwi_phasepos (str, default 'PA'):
            The direction of unwarping for positive phase. Can be AP,
            PA, LR, or RL. Negative phase is set automatically based on
            this setting.

        --hcp_dwi_gdcoeffs (str, default 'NONE'):
            A path to a file containing gradient distortion
            coefficients, alternatively a string describing multiple
            options (see below), or "NONE", if not used.

        --hcp_dwi_topupconfig (str, default $HCPPIPEDIR/global/config/b02b0.cnf):
            A full path to the topup configuration file to use.

        --hcp_dwi_dof (int, default 6):
            Degrees of Freedom for post eddy registration to structural images.

        --hcp_dwi_b0maxbval (int, default 50):
            Volumes with a bvalue smaller than this value will be
            considered as b0s.

        --hcp_dwi_combinedata (int, default 1):
            If JAC resampling has been used in eddy, this value determines what
            to do with the output file:

            - 2 ... include in the output all volumes uncombined (i.e. output
              file of eddy)
            - 1 ... include in the output and combine only volumes where
              both LR/RL (or AP/PA) pairs have been acquired
            - 0 ... As 1, but also include uncombined single volumes.

        --hcp_dwi_selectbestb0 (flag, optional):
            If set selects the best b0 for each phase encoding direction
            to pass on to topup rather than the default behaviour of
            using equally spaced b0's throughout the scan. The best b0
            is identified as the least distorted (i.e., most similar to
            the average b0 after registration). The flag is not set by
            default.

        --hcp_dwi_extraeddyarg (str, default ''):
            A string specifying additional arguments to pass to the
            DiffPreprocPipeline_Eddy.sh script and subsequently to the
            run_eddy.sh script and finally to the command that actually
            invokes the eddy binary. The string is to be written as a
            contiguous set of arguments to be added. Each argument
            needs to be provided together with dashes if it needs them.
            To provide multiple arguments divide them with the pipe (|)
            character, e.g.
            --hcp_dwi_extraeddyarg="--niter=8|--nvoxhp=2000".

        --hcp_dwi_name (str, default 'Diffusion'):
            Name to give DWI output directories.

        --hcp_nogpu (flag, optional):
            If specified, use the non-GPU-enabled version of eddy. The
            flag is not set by default.

        --hcp_cuda_version (str, default ''):
            The version of CUDA to use for GPU-enabled processing. This depends
            on the version of installed FSL and its CUDA support. Latest FSL
            versions do not have a version suffix, so this is empty by default.

        --hcp_dwi_even_slices (flag, optional):
            If set will ensure the input images to FSL's topup and eddy
            have an even number of slices by removing one slice if
            necessary. This behaviour used to be the default, but is
            now optional, because discarding a slice is incompatible
            with using slice-to-volume correction in FSL's eddy. The
            flag is not set by default.

        --hcp_dwi_posdata (str, default ''):
            Overrides the automatic QuNex's setup for the posData HCP pipelines'
            parameter. Provide a comma separated list of images with pos data.

        --hcp_dwi_negdata (str, default ''):
            Overrides the automatic QuNex's setup for the negData HCP pipelines'
            parameter. Provide a comma separated list of images with neg data.

        --hcp_dwi_dummy_bval_bvec (flag, optional):
            QuNex will create dummy bval and bvec files if they do not yet
            exist. Mainly useful when using distortion maps as part of the
            input data.

        --hcp_species (str, default ''):
            Species label (Human, Chimp, Macaque, Marmoset or NightMonkey).
            When unset the HCP pipeline default (Human) is used. Only relevant
            for non-human species.

        --hcp_truepatientposition (str, default ''):
            True patient position, e.g. HFS, FFS, HFSx, FFSx. Only relevant for
            non-human species.

        --hcp_scannerpatientposition (str, default ''):
            Scanner patient position, e.g. HFS, FFS. Only relevant for
            non-human species.

        --hcp_dwi_wmprojabs (str, default '2'):
            White matter projection absolute depth. Only relevant for non-human
            species.

        --hcp_dwi_resamp (str, default ''):
            The resamp value to pass to the eddy binary. When unset, no
            --resamp option is passed to eddy.

        --hcp_dwi_usephasezero (flag, optional):
            If set, phase zero is used. Only relevant for non-human species.
            The flag is not set by default.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --longitudinal:
            Set this flag if you are running the longitudinal variant of this
            command. A longitudinal run copies the cross-sectional Pre-Eddy and
            Eddy outputs and runs only the Post-Eddy step, so it reads the
            cross-sectional Diffusion folder and none of the unprocessed DWI
            images. hcp_dwi_posdata, hcp_dwi_negdata and hcp_dwi_echospacing
            are not used. Unless hcp_dwi_combinedata is set, its default is
            worked out from the DWI pairs declared in the batch file.

    Output files:
        The results of this command will be present in the folder named by
        --hcp_dwi_name, Diffusion by default, in the session's root hcp folder
        and in its T1w folder.

    Notes:
        Gradient Coefficient File Specification:
            --hcp_dwi_gdcoeffs parameter can be set to either "NONE", a path to
            a specific file to use, or a string that describes, which file to
            use in which case. Each option of the string has to be divided by a
            pipe "|" character and it has to specify, which information to look
            up, a possible value, and a file to use in that case, separated by
            a colon ":" character. The information to look up needs to be
            present in the description of that session. Standard options are
            e.g.::

                institution: Yale
                device: Siemens|Prisma|123456

            Where device is formatted as "<manufacturer>|<model>|<serial number>".

            If specifying a string it also has to include a "default" option,
            which will be used if the information was not found. An example
            could be::

                "default:/data/gc1.conf|model:Prisma:/data/gc/Prisma.conf|model:Trio:/data/gc/Trio.conf"

            With the information present above, the file "/data/gc/Prisma.conf"
            would be used.

        Apptainer (Singularity) and GPU support:
            If nogpu is not provided, this command will facilitate GPUs to speed
            up processing. Since the command uses CUDA binaries, an NVIDIA GPU
            is required. To give access to CUDA drivers to the system inside the
            Apptainer (Singularity) container, you need to use the --nv flag
            of the qunex_container script.

        Mapping of QuNex parameters onto HCP Pipelines parameters:
            Below is a detailed specification about how QuNex parameters are
            mapped onto the HCP Pipelines parameters.

            ============================== =====================================
            QuNex parameter                HCPpipelines parameter
            ============================== =====================================
            ``hcp_dwi_phasepos``           ``posData``, ``negData``, ``PEdir``
            ``hcp_dwi_echospacing``        ``echospacing-seconds``
            ``hcp_dwi_gdcoeffs``           ``gdcoeffs``
            ``hcp_dwi_dof``                ``dof``
            ``hcp_dwi_b0maxbval``          ``b0maxbval``
            ``hcp_dwi_combinedata``        ``combine-data-flag``
            ``hcp_printcom``               ``printcom``
            ``hcp_dwi_extraeddyarg``       ``extra-eddy-arg``
            ``hcp_dwi_name``               ``dwiname``
            ``hcp_dwi_selectbestb0``       ``select-best-b0``
            ``hcp_dwi_topupconfig``        ``topup-config-file``
            ``hcp_dwi_even_slices``        ``ensure-even-slices``
            ``hcp_dwi_posdata``            ``posData``
            ``hcp_dwi_negdata``            ``negData``
            ``hcp_nogpu``                  ``gpu``
            ``hcp_longitudinal_template``  ``longitudinal-session``
            ``longitudinal``               ``is-longitudinal``
            ``hcp_species``                ``species``
            ``hcp_truepatientposition``    ``truepatientposition``
            ``hcp_scannerpatientposition`` ``scannerpatientposition``
            ``hcp_dwi_wmprojabs``          ``wmprojabs``
            ``hcp_dwi_resamp``             ``resamp``
            ``hcp_dwi_usephasezero``       ``usephasezero``
            ============================== =====================================

        Use:
            Runs the Diffusion step of HCP Pipeline. It preprocesses diffusion
            weighted images (DWI). Specifically, after b0 intensity
            normalization, the b0 images of both phase encoding directions are
            used to calculate the susceptibility-induced B0 field deviations.
            The full timeseries from both phase encoding directions is used in
            the “eddy” tool for modeling of eddy current distortions and subject
            motion. Gradient distortion is corrected and the b0 image is
            registered to the T1w image using BBR. The diffusion data output
            from eddy are then resampled into 1.25mm native structural space and
            masked. Diffusion directions and the gradient deviation estimates
            are also appropriately rotated and registered into structural space.
            The function enables the use of a number of parameters to customize
            the specific preprocessing steps.

    Examples:
        Example run from the base study folder with test flag::

            qunex hcp_diffusion \\
                --studyfolder="<path_to_study_folder>" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --overwrite="no" \\
                --test

        Run with scheduler, the compute node also loads the required CUDA module::

            qunex hcp_diffusion \\
                --studyfolder="<path_to_study_folder>" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --overwrite="yes" \\
                --bash="module load CUDA/11.3.1" \\
                --scheduler="SLURM,time=24:00:00,cpus-per-task=1,mem-per-cpu=16000,partition=GPU,gpus=1"

        Run without a scheduler and without GPU support::

            qunex hcp_diffusion \\
                --studyfolder="<path_to_study_folder>" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --overwrite="yes" \\
                --hcp_nogpu
    """

    log = SessionLog(sinfo, options, "HCP DiffusionPreprocessing Pipeline")

    run = True
    report = "Error"

    try:
        pc.do_options_check(options, sinfo, "hcp_diffusion")
        do_hcp_options_check(options, "hcp_diffusion")
        hcp = get_hcp_paths(sinfo, options)

        if "hcp" not in sinfo:
            log.error(f"There is no hcp info for session {sinfo['id']} in batch.txt")
            run = False

        # --- using a legacy parameter?
        if "hcp_dwi_pedir" in options:
            log.warning("you are still providing the hcp_dwi_pedir parameter which has been replaced with hcp_dwi_phasepos! Please consult the documentation to see how to use it.")
            log.step(f"hcp_dwi_phasepos is currently set to {options['hcp_dwi_phasepos']}.")

        # --- set up data
        direction = None
        pe_dir = None
        if options["hcp_dwi_phasepos"] == "PA":
            direction = {"pos": "PA", "neg": "AP"}
            pe_dir = 2
        elif options["hcp_dwi_phasepos"] == "AP":
            direction = {"pos": "AP", "neg": "PA"}
            pe_dir = 2
        elif options["hcp_dwi_phasepos"] == "LR":
            direction = {"pos": "LR", "neg": "RL"}
            pe_dir = 1
        elif options["hcp_dwi_phasepos"] == "RL":
            direction = {"pos": "RL", "neg": "LR"}
            pe_dir = 1
        else:
            log.error(f"Invalid value of the hcp_dwi_phasepos parameter [{options['hcp_dwi_phasepos']}]")
            run = False

        if run:
            # get subject's DWIs
            dwis = dict()
            for k, v in sinfo.items():
                if k.isdigit() and v["name"] == "DWI":
                    dwis[int(k)] = v["task"]

            if options["longitudinal"]:
                pos_data, neg_data = None, None
                has_pair = _dwi_batch_has_pair(dwis, direction)
                run = _check_longitudinal_dwi(hcp, options, log) and run
            else:
                pos_data, neg_data, has_pair, dwiok = _resolve_dwi_data(
                    dwis, direction, hcp, options, log
                )
                run = run and dwiok

        # --- lookup gdcoeffs file if needed
        gdcfile, run = check_gdc_coeff_file(
            options["hcp_dwi_gdcoeffs"], hcp, sinfo, log, run
        )

        # -- check for DWI data
        dwi_found = False
        for k, v in sinfo.items():
            if k.isdigit() and v["name"] == "DWI":
                dwi_found = True

        if not dwi_found:
            log.error("No DWI files found in the batch file for one of the sessions!")
            run = False
        else:
            # -- set echospacing
            dwiinfo = [
                v for (k, v) in sinfo.items() if k.isdigit() and v["name"] == "DWI"
            ][0]

            echospacing = None
            if "EchoSpacing" in dwiinfo and check_inline_parameter_use(
                "dMRI", "EchoSpacing", options
            ):
                # echospacing read from image data
                echospacing = dwiinfo["EchoSpacing"]
                log.step(f"Using image specific EchoSpacing: {echospacing} s")

                # check validity
                echospacing, message = _check_dwi_echospacing(echospacing)
                log.raw(message)

            # if echospacing is none, set from parameter
            if not echospacing and options["hcp_dwi_echospacing"]:
                echospacing = options["hcp_dwi_echospacing"]
                log.step(f"Using study general EchoSpacing: {echospacing} s")

                # check validity
                echospacing, message = _check_dwi_echospacing(echospacing)
                log.raw(message)

            # -- check echospacing, a longitudinal run does not use it
            if not echospacing and options["longitudinal"]:
                log.detail("EchoSpacing is not used in longitudinal mode")
            elif not echospacing:
                log.error(
                    "QuNex was unable to acquire echospacing from the data and the parameter is not set!"
                )
                run = False

        # path
        path = sinfo["hcp"]

        # longitudinal mode
        if options["longitudinal"]:
            # replace path
            path = os.path.join(
                gf.subjects_folder(options["studyfolder"]), sinfo["subject"]
            )

        # --- build the command
        if run:
            # the raw inputs are only read cross-sectionally, a longitudinal run
            # reuses the cross-sectional Pre-Eddy and Eddy outputs
            args = [
                f'--path="{path}"',
                f'--session="{sinfo["id"] + options["hcp_suffix"]}"',
            ]
            if not options["longitudinal"]:
                args += [
                    f"--PEdir={pe_dir}",
                    f'--posData="{pos_data}"',
                    f'--negData="{neg_data}"',
                    f'--echospacing-seconds="{echospacing}"',
                ]
            args += [
                f'--gdcoeffs="{gdcfile}"',
                f'--printcom="{options["hcp_printcom"]}"',
            ]
            script = os.path.join(
                hcp["hcp_base"], "DiffusionPreprocessing", "DiffPreprocPipeline.sh"
            )
            comm = "                 ".join([script] + args)

            # -- Longitudinal parameters
            if options["longitudinal"]:
                comm += "                --is-longitudinal=1"
                comm += (
                    "                --longitudinal-session="
                    + f"{sinfo['id']}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}"
                )

            # -- Optional parameters
            # if there are no pairs combine-data-flag default is 2
            if options["hcp_dwi_combinedata"] is not None:
                comm += (
                    "                --combine-data-flag="
                    + options["hcp_dwi_combinedata"]
                )
            elif not has_pair:
                comm += "                --combine-data-flag=2"

            if options["hcp_dwi_b0maxbval"] is not None:
                comm += "                --b0maxbval=" + options["hcp_dwi_b0maxbval"]

            if options["hcp_dwi_dof"] is not None:
                comm += "                --dof=" + options["hcp_dwi_dof"]

            if options["hcp_dwi_extraeddyarg"] is not None:
                eddyoptions = options["hcp_dwi_extraeddyarg"].split("|")

                if eddyoptions != [""]:
                    for eddyoption in eddyoptions:
                        comm += "                --extra-eddy-arg=" + eddyoption

            if options["hcp_dwi_name"]:
                comm += "                --dwiname=" + options["hcp_dwi_name"]

            if options["hcp_dwi_selectbestb0"]:
                comm += "                --select-best-b0"

            if options["hcp_dwi_topupconfig"] is not None:
                comm += (
                    "                --topup-config-file="
                    + options["hcp_dwi_topupconfig"]
                )

            if options["hcp_dwi_even_slices"]:
                comm += "                --ensure-even-slices"

            # optional species / NHP parameters, these are only relevant for
            # non-human species, when unset the HCP pipeline defaults (Human)
            # are used
            if options["hcp_species"]:
                comm += "                --species=" + options["hcp_species"]

            if options["hcp_truepatientposition"]:
                comm += (
                    "                --truepatientposition="
                    + options["hcp_truepatientposition"]
                )

            if options["hcp_scannerpatientposition"]:
                comm += (
                    "                --scannerpatientposition="
                    + options["hcp_scannerpatientposition"]
                )

            if options["hcp_dwi_wmprojabs"]:
                comm += "                --wmprojabs=" + options["hcp_dwi_wmprojabs"]

            if options["hcp_dwi_resamp"]:
                comm += "                --resamp=" + options["hcp_dwi_resamp"]

            if options["hcp_dwi_usephasezero"]:
                comm += "                --usephasezero=True"

            if options["hcp_nogpu"]:
                comm += "                --gpu=False"
            else:
                comm += "                --gpu=True"
                if options["hcp_cuda_version"] is not None:
                    comm += (
                        f"               --cuda-version={options['hcp_cuda_version']}"
                    )

            # create dummy bvals and bvecs if demanded
            if options["hcp_dwi_dummy_bval_bvec"] and not options["longitudinal"]:
                _create_dummy_bval_bvec(pos_data, neg_data, options, log)

            # -- Report command
            if run:
                log.rule(before=1, after=1)
                log.raw("Running HCP Pipelines command via QuNex:\n\n")
                log.raw(comm.replace("                --", "\n    --"))
                log.rule(after=1)

            # -- Test files
            tfile = None
            full_test = None
            if not options["longitudinal"]:
                tfile = os.path.join(
                    hcp["T1w_folder"],
                    options["hcp_dwi_name"] or "Diffusion",
                    "data.nii.gz",
                )

                if hcp["hcp_dwi_check"]:
                    full_test = {
                        "tfolder": hcp["base"],
                        "tfile": hcp["hcp_dwi_check"],
                        "fields": [("sessionid", sinfo["id"])],
                        "specfolder": options["specfolder"],
                    }

        # -- Run
        if run:
            if options["run"] == "run":
                if not options["longitudinal"] and overwrite and os.path.exists(tfile):
                    os.remove(tfile)

                logtags = [options["logtag"]]
                if options["longitudinal"]:
                    logtags.append("long")

                _, report, failed = pc.run_external_for_file(
                    tfile,
                    comm,
                    "Running HCP Diffusion Preprocessing",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=logtags,
                    full_test=full_test,
                    shell=True,
                    exit_code_only=options["longitudinal"],
                    _log=log,
                )

            # -- just checking. A longitudinal run has no test file, and
            #    nothing to find done
            else:
                passed = None
                if tfile is not None:
                    passed, report, failed = pc.check_run(
                        tfile, full_test, "HCP Diffusion", overwrite=overwrite, _log=log
                    )
                if passed is None:
                    log.step("HCP Diffusion can be run")
                    report = "HCP Diffusion can be run"
                    failed = 0

        else:
            log.step("Session cannot be processed.")
            report = "HCP Diffusion cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        failed = 1
    except Exception:
        log.unknown_error()
        failed = 1

    log.close(pipeline="HCP Diffusion Preprocessing")

    return log.result(report, failed)

