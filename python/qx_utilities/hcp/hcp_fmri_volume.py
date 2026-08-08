#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_fmri_volume.py``

The HCP fMRIVolume pipeline and its per-BOLD executors.
"""

import glob
import json
import os
import os.path
import re
import shutil
import traceback
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_paths import pe_dir_map, get_hcp_paths
from qx_utilities.general.log import SessionLog, ReportLog
from qx_utilities.hcp.hcp_utils import (
    check_gdc_coeff_file,
    _build_skipped_report,
    check_inline_parameter_use,
    do_hcp_options_check,
    resolve_session_relative_image,
)


def hcp_fmri_volume(sinfo, options, overwrite=False, thread=0):
    """
    ``hcp_fmri_volume [... processing options]``

    Run the fMRI Volume (GenericfMRIVolumeProcessingPipeline.sh) step of HCP
    Pipeline.

    Description:
        The command preprocesses BOLD images and linearly and nonlinearly
        registers them to the MNI atlas. It makes use of the PreFS and FS steps of
        the pipeline. It enables the use of a number of parameters to customize the
        specific preprocessing steps.

    ..  qx_command:
        type: processing.session

    Warning:
        The code expects the first two HCP preprocessing steps
        (hcp_pre_freesurfer and hcp_freesurfer) to have been run and finished
        successfully. It also tests for the presence of fieldmap or spin-echo
        images if they were specified. It does not make a thorough check for
        PreFS and FS steps due to the large number of files.

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the sessions information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging data is
            supposed to go.

        --parsessions (int, default 1):
            How many sessions to run in parallel.

        --parelements (int, default 1):
            How many elements (e.g. bolds) to run in parallel.

        --bolds (str, default 'all'):
            Which bold images (as they are specified in the batch.txt file) to
            process. It can be a single type (e.g. 'task'), a pipe separated
            list (e.g. 'WM|Control|rest') or 'all' to process all.

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
            case running processing with slice timing correction, external BOLD
            reference, or without a distortion correction method.

        --hcp_folderstructure (str, default 'hcpls'):
            If set to 'hcpya' the folder structure used in the initial HCP Young
            Adults study is used. Specifically, the source files are stored in
            individual folders within the main 'hcp' folder in parallel with the
            working folders and the 'MNINonLinear' folder with results. If set
            to 'hcpls' the folder structure used in the HCP Life Span study is
            used. Specifically, the source files are all stored within their
            individual subfolders located in the joint 'unprocessed' folder in
            the main 'hcp' folder, parallel to the working folders and the
            'MNINonLinear' folder.

        --hcp_filename (str, default 'automated'):
            How to name the BOLD files once mapped into the hcp input folder
            structure. The default ('automated') will automatically name each
            file by their number (e.g. `BOLD_1`). The alternative
            ('userdefined') is to use the file names, which can be defined by
            the user prior to mapping (e.g. `rfMRI_REST1_AP`).

        --hcp_bold_biascorrection (str, default 'NONE'):
            Whether to perform bias correction for BOLD images. NONE, LEGACY
            or SEBASED. With SEBASED must also use hcp_bold_dcmethod.

        --hcp_bold_usejacobian (str, default 'FALSE'):
            Whether to apply the jacobian of the distortion correction to fMRI
            data.

        --hcp_bold_prefix (str, default 'BOLD'):
            The prefix to use when generating BOLD names (see --hcp_filename)
            for BOLD working folders and results.

        --hcp_bold_echospacing (float):
            Echo Spacing of BOLD images in seconds.

        --hcp_bold_sbref (str, default 'NONE'):
            Whether BOLD Reference images should be used - NONE or USE.

        --use_sequence_info (str, default 'all'):
            A pipe, comma or space separated list of inline sequence information
            to use in preprocessing of specific image modalities.

            Example specifications:

            - `all`: use all present inline information for all
              modalities,
            - 'DwellTime': use DwellTime information for all modalities,
            - `T1w:all`: use all present inline information for T1w
              modality,
            - `SE:EchoSpacing`: use EchoSpacing information for
              Spin-Echo fieldmap images.
            - `none`: do not use inline information.

            Modalities: T1w, T2w, SE, BOLD, dMRi Inline information: TR,
            PEDirection, EchoSpacing, DwellTime, ReadoutDirection.

            If information is not specified it will not be used. More general
            specification (e.g. `all`) implies all more specific cases (e.g.
            `T1w:all`).

        --hcp_bold_dcmethod (str):
            BOLD image deformation correction that should be used: TOPUP,
            TOPUP_MISMATCHED, FIELDMAP / SiemensFieldMap, GEHealthCareFieldMap,
            GEHealthCareLegacyFieldMap, PhilipsFieldMap,
            PRECOMPUTED_FIELDMAP, OnScanner or NONE.

        --hcp_bold_precomputedfmap (str, default ''):
            Path to the precomputed fieldmap image, QuNex tries to
            automatically set this if left empty and PRECOMPUTED_FIELDMAP
            is selected. This parameter is used when hcp_bold_dcmethod is set to
            PRECOMPUTED_FIELDMAP. Usually this is set automatically based
            on the FM-Real image specified in the batch file.

        --hcp_bold_precomputedfmapmag (str, default ''):
            Path to the magnitude image in the same space as
            --hcp_bold_precomputedfmap (e.g., a b=0 volume from the diffusion
            acquisition). Used for fieldmap-to-T1w registration. This parameter
            is used when hcp_bold_dcmethod is set to PRECOMPUTED_FIELDMAP.
            Usually this is set automatically based on the FM-Magnitude image
            specified in the batch file.

        --hcp_bold_echodiff (str):
            Delta TE for BOLD fieldmap images or NONE if not used.

        --hcp_bold_sephasepos (str, default ''):
            Label for the positive image of the Spin Echo Field Map pair.

        --hcp_bold_sephaseneg (str, default ''):
            Label for the negative image of the Spin Echo Field Map pair.

        --hcp_bold_unwarpdir (str, default 'y'):
            The direction of unwarping. Can be specified separately for
            LR/RL : `'LR=x|RL=-x|x'` or separately for PA/AP :
            `'PA=y|AP=y-|y-'`.

        --hcp_bold_res (str, default '2'):
            Target image resolution. 2mm recommended.

        --hcp_bold_gdcoeffs (str, default 'NONE'):
            Gradient distortion correction coefficients or NONE.

        --hcp_bold_topupconfig (str, default detailed below):
            A full path to the topup configuration file to use. Do not set if
            the default is to be used or if TOPUP distortion correction is not
            used.

        --hcp_bold_doslicetime (str, default 'FALSE'):
            Whether to do slice timing correction 'TRUE' or 'FALSE'.

        --hcp_bold_slicetimingfile (str, default 'FALSE'):
            Whether to use custom slice timing file 'TRUE' or 'FALSE'.
            You can prepare these files manually or you can use the
            functinality witin the setup_hcp command. The file will be then used
            for the --tcustom parameter of FSL slicetimer. The file should be
            located in the BOLD folder, using the same name, but with the
            `_slicetimer.txt` suffix.

        --hcp_bold_slicetimerparams (str, default ''):
            A comma or pipe separated string of parameters for FSL slicetimer.

        --hcp_bold_stcorrdir (str, default 'up'):
            The direction of slice acquisition ('up' or 'down').
            This parameter is deprecated. If specified, it will be added to
            --hcp_bold_slicetimerparams.

        --hcp_bold_stcorrint (str, default 'odd'):
            Whether slices were acquired in an interleaved fashion ('odd') or
            not ('empty').
            This parameter is deprecated. If specified, it will be added to
            --hcp_bold_slicetimerparams.

        --hcp_bold_preregistertool (str, default 'epi_reg'):
            What tool to use to preregister BOLDs before FSL BBR is 'run',
            'epi_reg' (default) or 'flirt'.

        --hcp_bold_movreg (str, default 'MCFLIRT'):
            Whether to use 'FLIRT' (usually for multiband images) or 'MCFLIRT'
            (default) for motion correction.

        --hcp_bold_movref (str, default 'independent'):
            What reference to use for movement correction ('independent',
            'first').
            This parameter is only valid when running HCPpipelines using the
            LegacyStyleData processing mode!

        --hcp_bold_seimg (str, default 'independent'):
            What image to use for spin-echo distortion correction
            ('independent' | 'first').
            This parameter is only valid when running HCPpipelines
            using the LegacyStyleData processing mode!

        --hcp_bold_refreg (str, default 'linear'):
            Whether to use only 'linear' (default) or also 'nonlinear'
            registration of motion corrected bold to reference.
            This parameter is only valid when running HCPpipelines
            using the LegacyStyleData processing mode!

        --hcp_bold_mask (str, default 'T1_fMRI_FOV'):
            Specifies what mask to use for the final bold:

            - `T1_fMRI_FOV`           ... combined T1w brain mask and
              fMRI FOV masks (the default and HCPStyleData compliant)
            - `T1_DILATED_fMRI_FOV`   ... a once dilated T1w brain based
              mask combined with fMRI FOV
            - `T1_DILATED2x_fMRI_FOV` ... a twice dilated T1w brain
              based mask combined with fMRI FOV
            - `fMRI_FOV`              ... a fMRI FOV mask.

            This parameter is only valid when running HCPpipelines
            using the LegacyStyleData processing mode!

        --hcp_wb_resample:
            Set this flag to use wb command to do volume resampling instead of
            applywarp.

        --hcp_echo_te (str, default ''):
            Comma delimited list of numbers which represent TE for each echo
            (unused for single echo).

        --hcp_bold_seechospacing (str, default ''):
            Echo Spacing or of Spin Echo Field Maps in seconds or "NONE" if not
            used. Used when hcp_bold_dcmethod is set to TOPUP_MISMATCHED.

        --hcp_bold_seunwarpdir (str, default ''):
            Phase encoding direction of the Spin Echo Field Map (x, y or NONE).
            Used when hcp_bold_dcmethod is set to TOPUP_MISMATCHED.

        --hcp_species (str, default ''):
            Species label (Human, Macaque, Marmoset, etc.). When unset the HCP
            pipeline default (Human) is used. Only relevant for non-human
            species.

        --hcp_scale_factor (str, default ''):
            Brain scale factor for motion correction (e.g. 1 for human). Passed
            to the HCP pipeline as ``brainscalefactor``. Only relevant for
            non-human species.

        --hcp_runmode (str, default 'Default'):
            Specify from which step to resume the processing instead of
            starting from the beginning. Value must be one of: Default,
            DistortionCorrection, OneStepResampling.

        --hcp_truepatientposition (str, default 'HFS'):
            True patient position, e.g. HFS, FFS, HFSx, FFSx Only relevant for
            non-human species.

        --hcp_scannerpatientposition (str, default 'HFS'):
            Scanner patient position, e.g. HFS, FFS. Only relevant for non-human
            species.

        --hcp_bold_bbrcontrast (str, default 'T2w'):
            BBR contrast to use for EPI to T1w registration: T2w, T1w or NONE
            Ignored when hcp_species is Human.

        --hcp_bold_wmprojabs (str, default '2'):
            FreeSurfer wm-proj-abs value. Only relevant for non-human species.

        --hcp_bold_initworldmat (str, default ''):
            Initial world matrix to apply to sform (optional). Only relevant
            for non-human species.

        --hcp_bold_sephaseneg2 (str, default ''):
            Label of the second negative polarity SE-EPI image. Together with
            hcp_bold_sephasepos2 and hcp_senum2 it is used to locate the second
            spin echo pair in the SpinEchoFieldMap[hcp_senum2] folder (mirroring
            hcp_pre_freesurfer). An existing absolute path can also be provided
            directly. Only relevant for non-human species.

        --hcp_bold_sephasepos2 (str, default ''):
            Label of the second positive polarity SE-EPI image. See
            hcp_bold_sephaseneg2. Only relevant for non-human species.

        --hcp_senum2 (str, default ''):
            Number of the second Spin Echo Field Map pair to use for SE2. QuNex
            will use the files in the SpinEchoFieldMap[N] folder from the HCP
            unprocessed folder.

        --hcp_bold_sephasezero (str, default ''):
            Zero-phase SE-EPI image (for NHP this is typically the T2w image).
            The value is resolved by checking, in order: an absolute path, a
            path relative to the session's root hcp folder, and a path relative
            to the session's T2w folder (e.g. 'T2w'). This lets a single command
            call work across many sessions. If provided but none of the three
            candidates exist, processing is aborted. Only relevant for non-human
            species.

        --hcp_bold_sephasezerofsbrainmask (str, default ''):
            FS brainmask for hcp_bold_sephasezero (for NHP this is typically
            'T2w_brainmask_fs'). Resolved the same way as hcp_bold_sephasezero
            (absolute, then relative to the session's hcp folder, then relative
            to the T2w folder) and aborts processing if provided but none of the
            candidates exist. Only relevant for non-human species.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --longitudinal:
            Set this flag if you are running the longitudinal variant of this
            command.

        --hcp_longitudinal_subject (str, default ''):
            The subject id of the longitudinal subject. Mandatory for
            longitudinal processing.

        --hcp_longitudinal_sessions (str, default ''):
            A comma separated list of sessions for a given subject. Mandatory
            for longitudinal processing.

        --hcp_longitudinal_extract_all:
            Set this flag to extract all runs specified in hcp_tica_bolds, with
            output name matching the one from hcp_tica_mrfix_concat_name. Not
            set by default.

    Output files:
        The results of this step will be present in the MNINonLinear folder
        in the sessions's root hcp folder::

            study
            └─ sessions
               └─ subject1_session1
                  └─ hcp
                     └─ subject1_session1
                       └─ MNINonlinear
                          └─ Results
                             └─ BOLD_1

    Notes:
        These last parameters enable fine-tuning of preprocessing and deserve
        additional information. In general the defaults should be appropriate
        for multiband images, single-band can profit from specific adjustments.
        Whereas FLIRT is best used for motion registration of high-resolution
        BOLD images, lower resolution single-band images might be better motion
        aligned using MCFLIRT (--hcp_bold_movreg).

        As a movement correction target, either each BOLD can be independently
        registered to T1 image, or all BOLD images can be motion correction
        aligned to the first BOLD in the series and only that image is
        registered to the T1 structural image (--hcp_bold_moveref). Do note
        that in this case also distortion correction will be computed for the
        first BOLD image in the series only and applied to all subsequent BOLD
        images after they were motion-correction aligned to the first BOLD.

        Similarly, for distortion correction, either the last preceding
        spin-echo image pair can be used (independent) or only the first
        spin-echo pair is used for all BOLD images (first; --hcp_bold_seimg).
        Do note that this also affects the previous motion correction target
        setting. If independent spin-echo pairs are used, then the first BOLD
        image after a new spin-echo pair serves as a new starting
        motion-correction reference.

        If there is no spin-echo image pair and TOPUP correction was requested,
        an error will be reported and processing aborted. If there is no
        preceding spin-echo pair, but there is at least one following the BOLD
        image in question, the first following spin-echo pair will be used and
        no error will be reported. The spin-echo pair used is reported in the
        log.

        When BOLD images are registered to the first BOLD in the series, due to
        larger movement between BOLD images it might be advantageous to use
        also nonlinear alignment to the first bold reference image
        (--hcp_bold_refreg).

        Lastly, for lower resolution BOLD images it might be better not to use
        subject specific T1 image based brain mask, but rather a mask generated
        on the BOLD image itself or based on the dilated standard MNI brain
        mask.

        Gradient coefficient file specification:
            `--hcp_bold_gdcoeffs` parameter can be set to either 'NONE', a path
            to a specific file to use, or a string that describes, which file
            to use in which case. Each option of the string has to be divided
            by a pipe '|' character and it has to specify, which information to
            look up, a possible value, and a file to use in that case,
            separated by a colon ':' character. The information too look up
            needs to be present in the description of that session. Standard
            options are e.g.::

                institution: Yale
                device: Siemens|Prisma|123456

            Where device is formatted as ``<manufacturer>|<model>|<serial number>``.

            If specifying a string it also has to include a `default` option,
            which will be used in the information was not found. An example
            could be::

                "default:/data/gc1.conf|model:Prisma:/data/gc/Prisma.conf|model:Trio:/data/gc/Trio.conf"

            With the information present above, the file
            `/data/gc/Prisma.conf` would be used.

        Slice timing correction:
            Slice timing correction is performed using FSL slicetimer. For the
            correction to be done correctly, the data needs to be carefully
            inspected and the ``hcp_bold_slicetimerparams`` parameter has to be
            prepared with the valid information. For complex slice timing
            acquisition (e.g., multiband acquisition) it is best to prepare a
            slice timing file. The slice timing file has to be saved in the
            same folder as the respective BOLD file. It has to be named the
            same as the BOLD file with ``_slicetimer.txt`` tail and extension.
            The slice timing file can be prepared automatically using the
            ```setup_hcp`` <../../api/gmri/setup_hcp.rst>`__ command, if JSON
            sidecar files for BOLD images exist and have the correct slice
            timing information. Alternatively ``prepare_slice_timing`` command
            can be used. See the respective inline help for more information.

        Movement and spin-echo references:
            Whereas most of the options should be clear, the ones specifying
            movement and spin-echo reference present the most significant
            change from the original way fMRIVolume is run and should be
            explained more in detail. Originally, each fMRI image is processed
            independently and registered to the individual's T1w image. Whereas
            this works well for high-resolution multiband fMRI images, in our
            experience the results are not optimal for legacy (non-multiband)
            fMRI images of lower resolution. Due to slight changes in the
            optimal registration to T1w image, fMRI images would not be
            optimally spatially aligned to one another, which would lead to
            increased within-subject noise across fMRI images. Using the
            ``hcp_bold_movref`` parameter it is possible to instead align the
            first fMRI image to the T1w image and then align all the following
            fMRI images to the first fMRI rather than registering each of them
            separately and independently to T1w image.

            The original registration procedure (the steps in brackets are
            based on previously completed steps):

            ::

               bold1 -> T1w [-> MNI atlas]
               bold2 -> T1w [-> MNI atlas]
               bold3 -> T1w [-> MNI atlas]

            can be changed to:

            ::

               bold1 -> T1w [-> MNI atlas]
               bold2 -> bold1 [-> T1w -> MNI atlas]
               bold3 -> bold1 [-> T1w -> MNI atlas]

            To use the original procedure and align each BOLD independently to
            T1w image, the ``hcp_bold_movref`` parameter has to be set to
            ``independent``. To use the modified procedure set the parameter to
            ``first``. To remove additional mismatches that can arise due to
            changes in distortion because of larger head movements between
            acquisition of individual BOLD images, linear registration of
            references between BOLD images can be enhanced with additional
            nonlinear registration. To make use of the latter, set the
            ``hcp_bold_refreg`` parameter to ``nonlinear`` instead of
            ``linear``. Note that using the non-linear registration is not
            compliant with the ``HCPStyleData`` processing mode.

            The additional advantage of registration to the first BOLD image is
            reduction in processing as the previously computed distortion
            correction can be re-used. This can lead to noticeable reduction in
            processing time.

            When recording is interrupted for any reason (e.g. subject had to go
            to a toilet, or the recording was completed in two sessions), a
            novel spin-echo image might be acquired to account for movement and
            allow better registration with BOLD images. In such a case, if
            ``hcp_bold_seimg`` parameter is set to ``independent``, the
            modified HCP pipeline will use for each BOLD image the last
            spin-echo recorded before the BOLD image in question. In this case,
            if BOLD registration target is set to the first BOLD image (using
            ``hcp_bold_movref``), the BOLD image registration target will be
            also changed to the fist BOLD image after the new spin-echo pair.
            Specifically with ``independent`` ``hcp_bold_seimg`` an example
            sequence might be::

               se-pair1
               bold1 -> se-pair1 -> T1w [-> MNI atlas]
               bold2 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold3 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               se-pair2
               bold4 -> se-pair2 -> T1w [-> MNI atlas]
               bold5 -> bold4 [se-pair2 -> T1w -> MNI atlas]
               bold6 -> bold4 [se-pair2 -> T1w -> MNI atlas]

            If the ``hcp_bold_seimg`` parameter is set to ``first``, only the
            first spin-echo pair of images will be considered and all others
            will be ignored. The above sequence would then be changed to::

               se-pair1
               bold1 -> se-pair1 -> T1w [-> MNI atlas]
               bold2 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold3 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               se-pair2
               bold4 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold5 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold6 -> bold1 [se-pair1 -> T1w -> MNI atlas]

            In the rare cases, where a spin-echo pair of images would be
            recorded after the first BOLD image, the first spin-echo image
            found after the BOLD image would be used for distortion correction.
            An example of such a situation might be the following sequence::

               bold1 -> se-pair1 -> T1w [-> MNI atlas]
               bold2 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold3 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               se-pair1
               bold4 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold5 -> bold1 [se-pair1 -> T1w -> MNI atlas]
               bold6 -> bold1 [se-pair1 -> T1w -> MNI atlas]

            In our testing, using the following combination of settings resulted
            in smallest differences between registered BOLD legacy
            (non-multiband) images::

               # batch.txt settings
               --hcp_bold_movreg    : MCFLIRT
               --hcp_bold_movref    : first
               --hcp_bold_seimg     : first
               --hcp_bold_refreg    : nonlinear
               --hcp_bold_mask      : T1_DILATED2x_fMRI_FOV

            Do note that the best performing settings are study dependent and need
            to be evaluated on a study by study basis.

        hcp_fmri_volume parameter mapping:

            =================================== ==========================
            QuNex parameter                     HCPpipelines parameter
            =================================== ==========================
            ``hcp_bold_res``                    ``fmrires``
            ``hcp_bold_biascorrection``         ``biascorrection``
            ``hcp_bold_echodiff``               ``echodiff``
            ``hcp_gdcoeffs``                    ``gdcoeffs``
            ``hcp_bold_dcmethod``               ``dcmethod``
            ``hcp_bold_echospacing``            ``echospacing``
            ``hcp_bold_unwarpdir``              ``unwarpdir``
            ``hcp_bold_topupconfig``            ``topupconfig``
            ``hcp_bold_dof``                    ``dof``
            ``hcp_printcom``                    ``printcom``
            ``hcp_bold_usejacobian``            ``usejacobian``
            ``hcp_bold_movreg``                 ``mctype``
            ``hcp_bold_preregistertool``        ``preregistertool``
            ``hcp_processing_mode``             ``processing-mode``
            ``hcp_bold_doslicetime``            ``slicetimerparams``
            ``hcp_bold_slicetimerparams``       ``slicetimerparams``
            ``hcp_bold_slicetimingfile``        ``slicetimerparams``
            ``hcp_bold_stcorrdir``              ``slicetimerparams``
            ``hcp_bold_stcorrint``              ``slicetimerparams``
            ``hcp_bold_refreg``                 ``fmrirefreg``
            ``hcp_bold_mask``                   ``fmrimask``
            ``hcp_bold_seunwarpdir``            ``seunwarpdir``
            ``hcp_bold_seechospacing``          ``seechospacing``
            ``hcp_bold_precomputedfmap``        ``precomputedfmap``
            ``hcp_bold_precomputedfmapmag``     ``precomputedfmapmag``
            ``hcp_species``                     ``species``
            ``hcp_scale_factor``                ``brainscalefactor``
            ``hcp_runmode``                     ``runmode``
            ``hcp_truepatientposition``         ``truepatientposition``
            ``hcp_scannerpatientposition``      ``scannerpatientposition``
            ``hcp_bold_bbrcontrast``            ``bbr-contrast``
            ``hcp_bold_wmprojabs``              ``wmprojabs``
            ``hcp_bold_initworldmat``           ``initworldmat``
            ``hcp_bold_sephaseneg2``            ``SEPhaseNeg2``
            ``hcp_bold_sephasepos2``            ``SEPhasePos2``
            ``hcp_bold_sephasezero``            ``SEPhaseZero``
            ``hcp_bold_sephasezerofsbrainmask`` ``SEPhaseZeroFSBrainmask``
            ``wb-resample``                     ``hcp_wb_resample``
            ``echoTE``                          ``hcp_echo_te``
            ``matlab-run-mode``                 ``hcp_matlab_mode``
            ``hcp_longitudinal_template``       ``longitudinal-template``
            ``longitudinal``                    ``is-longitudinal``
            =================================== ==========================

    Examples:
        Example run from the base study folder with test flag::

            qunex hcp_fmri_volume  \\
                --batchfile="processing/batch.txt"  \\
                --sessionsfolder="sessions"  \\
                --parsessions="10"  \\
                --parelements="4"  \\
                --overwrite="no"  \\
                --test

        Run using absolute paths with additional options and scheduler::

            qunex hcp_fmri_volume  \\
                --batchfile="<path_to_study_folder>/processing/batch.txt"
                --sessionsfolder="<path_to_study_folder>/sessions"  \\
                --parsessions="4"  \\
                --parelements="2"  \\
                --hcp_bold_doslicetime="TRUE"  \\
                --hcp_bold_movereg="MCFLIRT"  \\
                --hcp_bold_moveref="first"  \\
                --hcp_bold_mask="T1_DILATED2x_fMRI_FOV"  \\
                --overwrite="yes"  \\
                --scheduler="SLURM,time=24:00:00,cpus-per-task=2,mem-per-cpu=1250,partition=day"

        Additional examples::

            qunex hcp_fmri_volume \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10

        ::

            qunex hcp_fmri_volume \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --hcp_bold_movref=first \\
                --hcp_bold_seimg=first \\
                --hcp_bold_refreg=nonlinear \\
                --hcp_bold_mask=DILATED

    """

    log = SessionLog(sinfo, options, "HCP fMRI Volume pipeline", tail=" ")

    run = True
    report = {
        "done": [],
        "incomplete": [],
        "failed": [],
        "ready": [],
        "not ready": [],
        "skipped": [],
    }

    try:
        # mandatory check
        if not options["hcp_bold_dcmethod"]:
            raise ge.CommandFailed(
                "hcp_fmri_volume",
                "... the hcp_bold_dcmethod parameter needs to be set manually! Since QuNex cannot robustly extract the information needed to set this from the data, you need to set this parameter by yourself.",
            )

        # --- Base settings
        pc.do_options_check(options, sinfo, "hcp_fmri_volume")
        do_hcp_options_check(options, "hcp_fmri_volume")
        hcp = get_hcp_paths(sinfo, options)

        # --- bold filtering not yet supported!
        # btargets = options['bolds'].split("|")

        # --- run checks
        if "hcp" not in sinfo:
            log.error("There is no hcp info for session %s in batch.txt"
                % (sinfo["id"]))
            run = False

        # -> Pre FS results
        if os.path.exists(
            os.path.join(hcp["T1w_folder"], "T1w_acpc_dc_restore_brain.nii.gz")
        ):
            log.step("PreFS results present.")
        else:
            log.error("Could not find PreFS processing results.")
            run = False

        # -> FS results
        tfolder = hcp["FS_folder"]

        if options["hcp_species"] is None or options["hcp_species"].lower() == "human":
            if os.path.exists(os.path.join(tfolder, "mri", "aparc+aseg.mgz")):
                log.step("FS results present.")
            else:
                log.error("Could not find Freesurfer processing results.")
                run = False

        # -> PostFS results
        tfile = os.path.join(
            hcp["hcp_nonlin"],
            "fsaverage_LR32k",
            sinfo["id"] + options["hcp_suffix"] + ".32k_fs_LR.wb.spec",
        )

        if os.path.exists(tfile):
            log.step("PostFS results present.")
        else:
            log.error("Could not find PostFS processing results.")
            run = False

        # -> lookup gdcoeffs file if needed
        gdcfile, run = check_gdc_coeff_file(options["hcp_bold_gdcoeffs"], hcp, sinfo, log, run)

        # -> default parameter values
        spin_p = 0
        spin_n = 0
        spin_neg = ""  # AP or LR
        spin_pos = ""  # PA or RL
        refimg = "NONE"
        futureref = "NONE"
        topupconfig = ""
        orient = ""
        fmmag = "NONE"
        fmphase = "NONE"
        fmcombined = "NONE"
        fmprecomputed = "NONE"
        fmprecomputedmag = "NONE"

        # -> NHP/species specific images (resolved below, empty for humans)
        sepos2 = ""
        seneg2 = ""
        sezero = ""
        sezerobrainmask = ""

        # -> Check for SE images
        sepresent = []
        sepairs = {}
        sesettings = False

        # check parameters values
        if options["hcp_bold_biascorrection"] not in ["LEGACY", "SEBASED", "NONE"]:
            log.error(f"invalid value for the hcp_bold_biascorrection parameter {options['hcp_bold_biascorrection']}!")
            run = False

        if options["hcp_bold_dcmethod"].lower() not in [
            "topup",
            "topup_mismatched",
            "fieldmap",
            "siemensfieldmap",
            "philipsfieldmap",
            "gehealthcarefieldmap",
            "gehealthcarelegacyfieldmap",
            "precomputed_fieldmap",
            "onscanner",
            "none",
        ]:
            log.error(f"invalid value for the hcp_bold_dcmethod parameter {options['hcp_bold_dcmethod']}!")
            run = False

        if options["hcp_bold_dcmethod"].lower() in ["topup", "topup_mismatched"]:
            # -- spin echo settings
            sesettings = True
            for p in [
                "hcp_bold_sephaseneg",
                "hcp_bold_sephasepos",
            ]:
                if not options[p]:
                    log.raw(f"\nERROR: {p} parameter not set! It needs to be set manually as QuNex cannot infer it from the data in a robust manner.")
                    boldok = False
                    sesettings = False
                    run = False

            if sesettings:
                log.step("Looking for spin echo fieldmap set images [%s/%s]." % (
                    options["hcp_bold_sephasepos"],
                    options["hcp_bold_sephaseneg"],
                ))

                for senum in range(50):
                    spinok = False

                    # check if folder exists
                    sepath = glob.glob(
                        os.path.join(hcp["source"], "SpinEchoFieldMap%d*" % (senum))
                    )
                    if sepath:
                        sepath = sepath[0]
                        log.detail("identified folder %s" % (
                            os.path.basename(sepath)
                        ))
                        # get all *.nii.gz files in that folder
                        images = glob.glob(os.path.join(sepath, "*.nii.gz"))

                        # variable for checking se status
                        spinok = True
                        spin_pos, spin_neg = None, None

                        # search in images
                        for i in images:
                            # look for phase positive
                            if "_" + options["hcp_bold_sephasepos"] in os.path.basename(
                                i
                            ):
                                spin_pos = i
                                spinok = log.check_for_file(spin_pos,
                                    "\n     ... phase positive %s spin echo fieldmap image present"
                                    % (options["hcp_bold_sephasepos"]),
                                    "\n         ERROR: %s spin echo fieldmap image missing!"
                                    % (options["hcp_bold_sephasepos"]),
                                    status=spinok,
                                )
                            # look for phase negative
                            elif "_" + options[
                                "hcp_bold_sephaseneg"
                            ] in os.path.basename(i):
                                spin_neg = i
                                spinok = log.check_for_file(spin_neg,
                                    "\n     ... phase negative %s spin echo fieldmap image present"
                                    % (options["hcp_bold_sephaseneg"]),
                                    "\n         ERROR: %s spin echo fieldmap image missing!"
                                    % (options["hcp_bold_sephaseneg"]),
                                    status=spinok,
                                )

                        if not all([spin_pos, spin_neg]):
                            log.error("Either one of both pairs of SpinEcho images are missing in the %s folder! Please check your data or settings!"
                                % (os.path.basename(sepath)))
                            spinok = False

                    if spinok:
                        sepresent.append(senum)
                        sepairs[senum] = {"spinPos": spin_pos, "spinNeg": spin_neg}

            # ---> check for topupconfig
            if (
                options["hcp_bold_topupconfig"]
                and options["hcp_bold_topupconfig"] != ""
            ):
                topupconfig = options["hcp_bold_topupconfig"]
                if not os.path.exists(options["hcp_bold_topupconfig"]):
                    topupconfig = os.path.join(
                        hcp["hcp_Config"], options["hcp_bold_topupconfig"]
                    )
                    if not os.path.exists(topupconfig):
                        log.error("Could not find TOPUP configuration file: %s."
                            % (options["hcp_bold_topupconfig"]))
                        run = False
                    else:
                        log.detail("TOPUP configuration file present")
                else:
                    log.detail("TOPUP configuration file present")
            else:
                topupconfig = ""

            # ---> second spin-echo pair (NHP), resolved through hcp_senum2
            # the labels hcp_bold_sephasepos2/hcp_bold_sephaseneg2 are matched
            # against the files in the SpinEchoFieldMap[hcp_senum2] folder, or
            # existing absolute paths can be provided directly
            if options["hcp_bold_sephasepos2"] and options["hcp_bold_sephaseneg2"]:
                if os.path.exists(options["hcp_bold_sephasepos2"]) and os.path.exists(
                    options["hcp_bold_sephaseneg2"]
                ):
                    sepos2 = options["hcp_bold_sephasepos2"]
                    seneg2 = options["hcp_bold_sephaseneg2"]
                    log.step("Second Spin-Echo pair of images present. [%s, %s]" % (
                        os.path.basename(sepos2),
                        os.path.basename(seneg2),
                    ))
                elif options["hcp_senum2"]:
                    tufolder2 = os.path.join(
                        hcp["source"],
                        "SpinEchoFieldMap%s%s"
                        % (options["hcp_senum2"], options["fctail"]),
                    )
                    try:
                        sepos2 = glob.glob(
                            os.path.join(
                                tufolder2,
                                "*_" + options["hcp_bold_sephasepos2"] + "*.nii.gz",
                            )
                        )[0]
                        seneg2 = glob.glob(
                            os.path.join(
                                tufolder2,
                                "*_" + options["hcp_bold_sephaseneg2"] + "*.nii.gz",
                            )
                        )[0]
                        log.step("Second Spin-Echo pair of images present. [%s]" % (
                            os.path.basename(tufolder2)
                        ))
                    except IndexError:
                        log.error("Could not find the relevant second Spin-Echo files! [%s]"
                            % (tufolder2))
                        run = False
                else:
                    sepos2, sepos2_found = resolve_session_relative_image(
                        options["hcp_bold_sephasepos2"], hcp["base"]
                    )
                    seneg2, seneg2_found = resolve_session_relative_image(
                        options["hcp_bold_sephaseneg2"], hcp["base"]
                    )

                    if sepos2_found and seneg2_found:
                        log.step("Second Spin-Echo pair of images present. [%s, %s]"
                            % (
                                sepos2,
                                seneg2,
                            ))
                    else:
                        log.error("Could not find the relevant second Spin-Echo files for hcp_bold_sephasepos2/hcp_bold_sephaseneg2! "
                            "Checked each value as an absolute path, relative to the session's hcp folder, and relative to the T2w folder.")
                        run = False

        # --- NHP zero-phase SE image (typically the T2w) and its FS brainmask.
        # each value is resolved by checking, in order, an absolute path, a path
        # relative to the session's root hcp folder, and a path relative to the
        # session's T2w folder, so that a single command call works across many
        # sessions. if a value is set but none of the candidates exist,
        # processing is aborted.
        if options["hcp_bold_sephasezero"]:
            sezero, sezero_found = resolve_session_relative_image(
                options["hcp_bold_sephasezero"], hcp["base"]
            )
            if sezero_found:
                log.step("Zero-phase SE image: %s" % (sezero))
            else:
                log.error("Could not find the zero-phase SE image for hcp_bold_sephasezero [%s]! Checked as an absolute path, relative to the session's hcp folder, and relative to the T2w folder."
                    % (options["hcp_bold_sephasezero"]))
                run = False

        if options["hcp_bold_sephasezerofsbrainmask"]:
            sezerobrainmask, sezerobrainmask_found = resolve_session_relative_image(
                options["hcp_bold_sephasezerofsbrainmask"], hcp["base"]
            )
            if sezerobrainmask_found:
                log.step("Zero-phase SE FS brainmask: %s" % (sezerobrainmask))
            else:
                log.error("Could not find the zero-phase SE FS brainmask for hcp_bold_sephasezerofsbrainmask [%s]! Checked as an absolute path, relative to the session's hcp folder, and relative to the T2w folder."
                    % (options["hcp_bold_sephasezerofsbrainmask"]))
                run = False

        # --- Process unwarp direction
        if options["hcp_bold_dcmethod"].lower() in [
            "topup",
            "topup_mismatched",
            "fieldmap",
            "siemensfieldmap",
            "philipsfieldmap",
            "gehealthcarefieldmap",
            "gehealthcarelegacyfieldmap",
            "precomputed_fieldmap",
        ]:
            unwarpdirs = [
                [f.strip() for f in e.strip().split("=")]
                for e in options["hcp_bold_unwarpdir"].split("|")
            ]
            unwarpdirs = [["default", e[0]] if len(e) == 1 else e for e in unwarpdirs]
            unwarpdirs = dict(unwarpdirs)
        else:
            unwarpdirs = {"default": ""}

        # --- Get sorted bold numbers
        bolds, bskip, report["boldskipped"] = log.use_or_skip_bold(sinfo, options)
        if len(bolds) == 0:
            log.error("No BOLD images found for session %s! Check your data or the contents of the batch file."
                % (sinfo["id"]))
            run = False

        _build_skipped_report(report, bskip, options)

        # --- Preprocess
        bolds_data = []

        first_se = None
        if bolds:
            first_se = bolds[0].get("se", None)

        for boldinfo in bolds:
            printbold, boldtarget, boldsource = pc.get_bold_names(boldinfo, options)

            log.raw("\n\n---> %s BOLD %s" % (
                pc.action(
                    "Preprocessing settings (unwarpdir, refimage, moveref, seimage) for",
                    options["run"],
                ),
                printbold,
            ))
            boldok = True

            # ---> Check for and prepare distortion correction parameters
            echospacing = ""
            unwarpdir = ""

            dcset = options["hcp_bold_dcmethod"].lower() in [
                "topup",
                "topup_mismatched",
                "fieldmap",
                "siemensfieldmap",
                "philipsfieldmap",
                "gehealthcarefieldmap",
                "gehealthcarelegacyfieldmap",
                "precomputed_fieldmap",
            ]

            # --- set unwarpdir and orient
            if "o" in boldinfo:
                orient = "_" + boldinfo["o"]
                if dcset:
                    unwarpdir = unwarpdirs.get(boldinfo["o"])
                    if unwarpdir is None:
                        log.error("No unwarpdir is defined for %s! Please check hcp_bold_unwarpdir parameter!"
                            % (boldinfo["o"]), depth=1)
                        boldok = False
            elif "phenc" in boldinfo:
                orient = "_" + boldinfo["phenc"]
                if dcset:
                    unwarpdir = unwarpdirs.get(boldinfo["phenc"])
                    if unwarpdir is None:
                        log.error("No unwarpdir is defined for %s! Please check hcp_bold_unwarpdir parameter!"
                            % (boldinfo["phenc"]), depth=1)
                        boldok = False
            elif "PEDirection" in boldinfo and check_inline_parameter_use(
                "BOLD", "PEDirection", options
            ):
                if boldinfo["PEDirection"] in pe_dir_map:
                    orient = "_" + pe_dir_map[boldinfo["PEDirection"]]
                    if dcset:
                        unwarpdir = boldinfo["PEDirection"]
                else:
                    log.error("Invalid PEDirection specified [%s]! Please check sequence specific PEDirection value!"
                        % (boldinfo["PEDirection"]), depth=1)
                    boldok = False
            else:
                orient = ""
                if dcset:
                    unwarpdir = unwarpdirs.get("default")
                    if unwarpdir is None:
                        log.error("No default unwarpdir is set! Please check hcp_bold_unwarpdir parameter!", depth=1)
                        boldok = False

            if orient:
                log.detail("phase encoding direction: %s" % (orient[1:]))
            else:
                log.detail("phase encoding direction not specified")

            if dcset:
                log.detail("unwarp direction: %s" % (unwarpdir))

            # --- check for bold image
            if "filename" in boldinfo and options["hcp_filename"] == "userdefined":
                boldroot = boldinfo["filename"]
            else:
                boldroot = boldsource + orient

            boldimgs = []
            boldimgs.append(
                os.path.join(
                    hcp["source"],
                    "%s%s" % (boldroot, options["fctail"]),
                    "%s_%s.nii.gz" % (sinfo["id"], boldroot),
                )
            )

            # -- set echospacing
            if dcset:
                if "EchoSpacing" in boldinfo and check_inline_parameter_use(
                    "BOLD", "EchoSpacing", options
                ):
                    echospacing = boldinfo["EchoSpacing"]
                    log.detail("using image specific EchoSpacing: %s s" % (
                        echospacing
                    ))
                elif options["hcp_bold_echospacing"]:
                    echospacing = options["hcp_bold_echospacing"]
                    log.detail("using study general EchoSpacing: %s s" % (
                        echospacing
                    ))
                else:
                    # try to set from the JSON sidecar
                    json_sidecar = boldimgs[0].replace(".nii.gz", ".json")
                    if os.path.exists(json_sidecar):
                        log.detail("trying to set hcp_bold_echospacing from the JSON sidecar")
                        with open(json_sidecar, "r") as file:
                            sidecar_data = json.load(file)
                            if "EffectiveEchoSpacing" in sidecar_data:
                                echospacing = sidecar_data["EffectiveEchoSpacing"]
                                log.detail(f"hcp_bold_echospacing set to {echospacing}")

                    if not options["hcp_bold_echospacing"]:
                        echospacing = ""
                        log.error("EchoSpacing is not set! Please review parameter file.")
                        boldok = False

            # --- check for spin-echo-fieldmap image
            if (
                options["hcp_bold_dcmethod"].lower() in ["topup", "topup_mismatched"]
                and sesettings
            ):
                if not sepresent:
                    log.error("No spin echo fieldmap set images present!", depth=1)
                    boldok = False

                elif options["hcp_bold_seimg"] == "first":
                    if first_se is None:
                        spin_n = int(sepresent[0])
                        log.detail("using the first recorded spin echo fieldmap set %d"
                            % (spin_n))
                    else:
                        spin_n = int(first_se)
                        log.detail("using the spin echo fieldmap set for the first bold run, %d"
                            % (spin_n))
                    spin_neg = sepairs[spin_n]["spinNeg"]
                    spin_pos = sepairs[spin_n]["spinPos"]

                else:
                    spin_n = False
                    if "se" in boldinfo:
                        spin_n = int(boldinfo["se"])
                    else:
                        for sen in sepresent:
                            if sen <= boldinfo["bold_number"]:
                                spin_n = sen
                            elif not spin_n:
                                spin_n = sen

                    spin_neg = sepairs[spin_n]["spinNeg"]
                    spin_pos = sepairs[spin_n]["spinPos"]
                    log.detail("using spin echo fieldmap set %d" % (spin_n))
                    log.raw("\n         -> SE Positive image : %s" % (
                        os.path.basename(spin_pos)
                    ))
                    log.raw("\n         -> SE Negative image : %s" % (
                        os.path.basename(spin_neg)
                    ))

                # -- are we using a new SE image?
                if spin_n != spin_p:
                    spin_p = spin_n
                    futureref = "NONE"

            # --- check for Siemens double TE-fieldmap image
            elif options["hcp_bold_biascorrection"].lower() != "sebased" and options[
                "hcp_bold_dcmethod"
            ].lower() in [
                "fieldmap",
                "siemensfieldmap",
            ]:
                fmnum = boldinfo.get("fm", None)
                if fmnum is None:
                    log.error("No fieldmap number specified for the BOLD image!")
                    run = False
                else:
                    fieldok = True
                    for i, v in hcp["fieldmap"].items():
                        if isinstance(hcp["fieldmap"][i]["magnitude"], list):
                            fieldok = log.check_for_file(hcp["fieldmap"][i]["magnitude"][0],
                                "\n     ... Siemens fieldmap magnitude image %d present "
                                % (i),
                                "\n     ... ERROR: Siemens fieldmap magnitude image %d missing!"
                                % (i),
                                status=fieldok,
                            )
                            fieldok = log.check_for_file(hcp["fieldmap"][i]["magnitude"][1],
                                "\n     ... Siemens fieldmap magnitude image %d present "
                                % (i),
                                "\n     ... ERROR: Siemens fieldmap magnitude image %d missing!"
                                % (i),
                                status=fieldok,
                            )
                        else:
                            fieldok = log.check_for_file(hcp["fieldmap"][i]["magnitude"],
                                "\n     ... Siemens fieldmap magnitude image %d present "
                                % (i),
                                "\n     ... ERROR: Siemens fieldmap magnitude image %d missing!"
                                % (i),
                                status=fieldok,
                            )

                        fieldok = log.check_for_file(hcp["fieldmap"][i]["phase"],
                            "\n     ... Siemens fieldmap phase image %d present " % (i),
                            "\n     ... ERROR: Siemens fieldmap phase image %d missing!"
                            % (i),
                            status=fieldok,
                        )
                        boldok = boldok and fieldok
                    if not pc.is_number(echospacing):
                        fieldok = False
                        log.error('hcp_bold_echospacing not defined correctly: "%s"!'
                            % (options["hcp_bold_echospacing"]), depth=1)

                    # try to set hcp_bold_echodiff from the JSON sidecar if not yet set
                    if (
                        not options["hcp_bold_echodiff"]
                        or options["hcp_bold_echodiff"] == "NONE"
                    ):
                        fmfolder = os.path.join(
                            hcp["source"],
                            "FieldMap%s%s" % (fmnum, options["fctail"]),
                        )

                        fmap_json = glob.glob(os.path.join(fmfolder, "*Phase.json"))

                        if len(fmap_json) != 0:
                            fmap_json = fmap_json[0]
                            json_sidecar = os.path.join(fmfolder, fmap_json)

                            if os.path.exists(json_sidecar):
                                log.detail("Trying to set hcp_echodiff from the JSON sidecar.")
                                with open(json_sidecar, "r") as file:
                                    sidecar_data = json.load(file)
                                    if (
                                        "EchoTime1" in sidecar_data
                                        and "EchoTime2" in sidecar_data
                                    ):
                                        echodiff = (
                                            sidecar_data["EchoTime2"]
                                            - sidecar_data["EchoTime1"]
                                        )
                                        # from s to ms
                                        echodiff = echodiff * 1000
                                        options["hcp_bold_echodiff"] = (
                                            f"{echodiff:.10f}"
                                        )
                                        log.detail(f"hcp_bold_echodiff set to {options['hcp_bold_echodiff']}")
                            else:
                                log.step("hcp_bold_echodiff not provided and not found in the JSON sidecar, setting it to NONE.")
                                options["hcp_bold_echodiff"] = None
                        else:
                            log.step("JSON sidecar not found, setting hcp_bold_echodiff to NONE.")
                            options["hcp_bold_echodiff"] = None

                    if not pc.is_number(options["hcp_bold_echodiff"]):
                        fieldok = False
                        log.error('hcp_bold_echodiff not defined correctly: "%s"!'
                            % (options["hcp_bold_echodiff"]), depth=1)
                    boldok = boldok and fieldok
                    fmmag = hcp["fieldmap"][int(fmnum)]["magnitude"]
                    if isinstance(fmmag, list):
                        fmmag = "@".join(fmmag)
                    fmphase = hcp["fieldmap"][int(fmnum)]["phase"]
                    fmcombined = None

            # --- check for GE legacy fieldmap image
            elif (
                options["hcp_bold_biascorrection"].lower() != "sebased"
                and options["hcp_bold_dcmethod"].lower() == "gehealthcarelegacyfieldmap"
            ):
                fmnum = boldinfo.get("fm", None)
                if fmnum is None:
                    log.error("No fieldmap number specified for the BOLD image!")
                    run = False
                else:
                    fieldok = True
                    for i, v in hcp["fieldmap"].items():
                        fieldok = log.check_for_file(hcp["fieldmap"][i]["GE"],
                            "\n     ... GeneralElectric legacy fieldmap image %d present "
                            % (i),
                            "\n     ... ERROR: GeneralElectric legacy fieldmap image %d missing!"
                            % (i),
                            status=fieldok,
                        )
                        boldok = boldok and fieldok
                    fmmag = None
                    fmphase = None
                    fmcombined = hcp["fieldmap"][int(fmnum)]["GE"]

            # --- check for GE double TE-fieldmap image
            elif (
                options["hcp_bold_biascorrection"].lower() != "sebased"
                and options["hcp_bold_dcmethod"].lower() == "gehealthcarefieldmap"
            ):
                fmnum = boldinfo.get("fm", None)
                if fmnum is None:
                    log.error("No fieldmap number specified for the BOLD image!")
                    run = False
                else:
                    fieldok = True
                    for i, v in hcp["fieldmap"].items():
                        fieldok = log.check_for_file(hcp["fieldmap"][i]["magnitude"],
                            "\n     ... GE fieldmap magnitude image %d present " % (i),
                            "\n     ... ERROR: GE fieldmap magnitude image %d missing!"
                            % (i),
                            status=fieldok,
                        )
                        fieldok = log.check_for_file(hcp["fieldmap"][i]["phase"],
                            "\n     ... GE fieldmap phase image %d present " % (i),
                            "\n     ... ERROR: GE fieldmap phase image %d missing!"
                            % (i),
                            status=fieldok,
                        )
                        boldok = boldok and fieldok
                    if not pc.is_number(echospacing):
                        fieldok = False
                        log.error('hcp_bold_echospacing not defined correctly: "%s"!'
                            % (options["hcp_bold_echospacing"]), depth=1)
                    boldok = boldok and fieldok
                    fmmag = hcp["fieldmap"][int(fmnum)]["magnitude"]
                    fmphase = hcp["fieldmap"][int(fmnum)]["phase"]
                    fmcombined = None

            # --- check for Philips double TE-fieldmap image
            elif (
                options["hcp_bold_biascorrection"].lower() != "sebased"
                and options["hcp_bold_dcmethod"].lower() == "philipsfieldmap"
            ):
                fmnum = boldinfo.get("fm", None)
                if fmnum is None:
                    log.error("No fieldmap number specified for the BOLD image!")
                    run = False
                else:
                    fieldok = True
                    for i, v in hcp["fieldmap"].items():
                        fieldok = log.check_for_file(hcp["fieldmap"][i]["magnitude"],
                            "\n     ... Philips fieldmap magnitude image %d present "
                            % (i),
                            "\n     ... ERROR: Philips fieldmap magnitude image %d missing!"
                            % (i),
                            status=fieldok,
                        )
                        fieldok = log.check_for_file(hcp["fieldmap"][i]["phase"],
                            "\n     ... Philips fieldmap phase image %d present " % (i),
                            "\n     ... ERROR: Philips fieldmap phase image %d missing!"
                            % (i),
                            status=fieldok,
                        )
                        boldok = boldok and fieldok
                    if not pc.is_number(echospacing):
                        fieldok = False
                        log.error('hcp_bold_echospacing not defined correctly: "%s"!'
                            % (options["hcp_bold_echospacing"]), depth=1)
                    boldok = boldok and fieldok
                    fmmag = hcp["fieldmap"][int(fmnum)]["magnitude"]
                    fmphase = hcp["fieldmap"][int(fmnum)]["phase"]
                    fmcombined = None

            # --- check for real fieldmap image
            elif (
                options["hcp_bold_biascorrection"].lower() != "sebased"
                and options["hcp_bold_dcmethod"].lower() == "precomputed_fieldmap"
            ):
                if options["hcp_bold_precomputedfmap"] is not None:
                    if not os.path.exists(options["hcp_bold_precomputedfmap"]):
                        log.error("Could not find precomputed fieldmap image specified in hcp_bold_precomputedfmap parameter: %s."
                            % (options["hcp_bold_precomputedfmap"]))
                        fieldok = False
                    else:
                        log.detail("real fieldmap image present")
                        fieldok = True
                    boldok = boldok and fieldok
                    fmprecomputed = options["hcp_bold_precomputedfmap"]
                    fmmag = None
                    fmphase = None
                    fmcombined = None
                else:
                    fmnum = boldinfo.get("fm", None)
                    if fmnum is None:
                        log.error("No fieldmap number specified for the BOLD image!")
                        run = False
                    else:
                        fieldok = True
                        for i, v in hcp["fieldmap"].items():
                            fieldok = log.check_for_file(hcp["fieldmap"][i]["Real"],
                                "\n     ... Real fieldmap image %d present " % (i),
                                "\n     ... ERROR: Real fieldmap image %d missing!"
                                % (i),
                                status=fieldok,
                            )
                            boldok = boldok and fieldok
                        if not pc.is_number(echospacing):
                            fieldok = False
                            log.error('hcp_bold_echospacing not defined correctly: "%s"!'
                                % (options["hcp_bold_echospacing"]), depth=1)
                        boldok = boldok and fieldok
                        fmprecomputed = hcp["fieldmap"][int(fmnum)]["Real"]
                        fmmag = None
                        fmphase = None
                        fmcombined = None

                # --- check for precomputedfmapmag
                if options["hcp_bold_precomputedfmapmag"] is not None:
                    # --- user provided a path to a magnitude image
                    if os.path.exists(options["hcp_bold_precomputedfmapmag"]):
                        fmprecomputedmag = options["hcp_bold_precomputedfmapmag"]
                        log.detail("precomputed fieldmap magnitude image present: %s"
                            % (fmprecomputedmag))
                    else:
                        log.error("Could not find precomputed fieldmap magnitude image specified in the hcp_bold_precomputedfmapmag parameter: %s."
                            % (options["hcp_bold_precomputedfmapmag"]))
                        boldok = False
                else:
                    # --- try to auto-detect from fieldmap dict using fm number from bold info
                    fmnum_mag = boldinfo.get("fm", None)
                    if (
                        fmnum_mag is not None
                        and int(fmnum_mag) in hcp["fieldmap"]
                        and "Magnitude" in hcp["fieldmap"][int(fmnum_mag)]
                    ):
                        auto_precomputedfmapmag = hcp["fieldmap"][int(fmnum_mag)][
                            "Magnitude"
                        ]
                        boldok = log.check_for_file(auto_precomputedfmapmag,
                            "\n     ... precomputed fieldmap magnitude image auto-detected and present: %s"
                            % (auto_precomputedfmapmag),
                            "\n---> ERROR: Could not find auto-detected precomputed fieldmap magnitude image: %s."
                            % (auto_precomputedfmapmag),
                            status=boldok,
                        )
                        if os.path.exists(auto_precomputedfmapmag):
                            fmprecomputedmag = auto_precomputedfmapmag
                    else:
                        log.warning("hcp_bold_precomputedfmapmag is not set and could not be auto-detected. The HCP pipelines require this for PRECOMPUTED_FIELDMAP.")

            # --- NO DC used
            elif options["hcp_bold_dcmethod"].lower() == "none":
                log.detail("No distortion correction used ")
                if options["hcp_processing_mode"] == "HCPStyleData":
                    log.error("The requested HCP processing mode is 'HCPStyleData', however, no distortion correction method was specified!\n            Consider using LegacyStyleData processing mode.")
                    run = False

            # --- SEBASED
            elif options["hcp_bold_biascorrection"].lower() == "sebased":
                log.detail("SEBASED bias correction used")
                if options["hcp_bold_dcmethod"].lower() not in [
                    "topup",
                    "topup_mismatched",
                ]:
                    log.error("SEBASED hcp_bold_biascorrection requires hcp_bold_dcmethod TOPUP or TOPUP_MISMATCHED!")
                    run = False

            # --- OnScanner
            elif options["hcp_bold_dcmethod"].lower() == "onscanner":
                log.detail("OnScanner distortion correction used ")

            # --- ERROR
            else:
                log.error("Issues detected with distortion correction setup! Please check related parameters!", depth=1)
                boldok = False

            # --- set reference
            # Need to make sure the right reference is used in relation to LR/RL AP/PA bolds
            # - have to keep track of whether an old topup in the same direction exists
            if options["hcp_folderstructure"] == "hcpya":
                boldimgs.append(
                    os.path.join(
                        hcp["source"],
                        "%s%s" % (boldroot, options["fctail"]),
                        "%s%s_%s.nii.gz" % (sinfo["id"], options["fctail"], boldroot),
                    )
                )

            boldok, boldimg = log.check_for_files(boldimgs,
                "\n     ... bold image present",
                "\n     ... ERROR: bold image missing, searched for %s!" % (boldimgs),
                status=boldok,
            )

            # --- check for ref image
            if options["hcp_bold_sbref"].lower() == "use":
                refimg = os.path.join(
                    hcp["source"],
                    "%s_SBRef%s" % (boldroot, options["fctail"]),
                    "%s_%s_SBRef.nii.gz" % (sinfo["id"], boldroot),
                )
                boldok = log.check_for_file(refimg,
                    "\n     ... reference image present",
                    "\n     ... ERROR: bold reference image missing!",
                    status=boldok,
                )
            else:
                log.detail("reference image not used")

            # --- check the mask used
            if options["hcp_bold_mask"]:
                if (
                    options["hcp_bold_mask"] != "T1_fMRI_FOV"
                    and options["hcp_processing_mode"] == "HCPStyleData"
                ):
                    log.error("The requested HCP processing mode is 'HCPStyleData', however, %s was specified as bold mask to use!\n            Consider either using 'T1_fMRI_FOV' for the bold mask or LegacyStyleData processing mode.")
                    run = False
                else:
                    log.detail("using %s as BOLD mask" % (options["hcp_bold_mask"]))
            else:
                log.detail("using the HCPpipelines default BOLD mask")

            # --- set movement reference image
            fmriref = futureref
            if options["hcp_bold_movref"] == "first":
                if futureref == "NONE":
                    futureref = boldtarget

            # --- are we using previous reference
            if fmriref != "NONE":
                log.detail("using %s as movement correction reference" % (fmriref))
                refimg = "NONE"
                if (
                    options["hcp_processing_mode"] == "HCPStyleData"
                    and options["hcp_bold_refreg"] == "nonlinear"
                ):
                    log.error("The requested HCP processing mode is 'HCPStyleData', however, a nonlinear registration to an external BOLD was specified!\n            Consider using LegacyStyleData processing mode.")
                    run = False

            # --- Check for slice timing file
            if options["hcp_bold_doslicetime"] and options["hcp_bold_slicetimingfile"]:
                stfile = os.path.join(
                    hcp["source"],
                    "%s%s" % (boldroot, options["fctail"]),
                    "%s_%s_slicetimer.txt" % (sinfo["id"], boldroot),
                )
                boldok = log.check_for_file(stfile,
                    "\n     ... slice timing file present",
                    "\n     ... ERROR: slice timing file missing!",
                    status=boldok,
                )
            else:
                stfile = None

            # store required data
            b = {
                "boldsource": boldsource,
                "boldtarget": boldtarget,
                "printbold": printbold,
                "run": run,
                "boldok": boldok,
                "boldimg": boldimg,
                "refimg": refimg,
                "stfile": stfile,
                "gdcfile": gdcfile,
                "unwarpdir": unwarpdir,
                "echospacing": echospacing,
                "spinNeg": spin_neg,
                "spinPos": spin_pos,
                "sepos2": sepos2,
                "seneg2": seneg2,
                "sezero": sezero,
                "sezerobrainmask": sezerobrainmask,
                "topupconfig": topupconfig,
                "fmmag": fmmag,
                "fmphase": fmphase,
                "fmcombined": fmcombined,
                "fmprecomputed": fmprecomputed,
                "fmprecomputedmag": fmprecomputedmag,
                "fmriref": fmriref,
            }
            bolds_data.append(b)

        # --- Process
        log.raw("\n")

        # if moveref equals first and seimage equals independent (complex scenario)
        if (
            not options["longitudinal"]
            and options["hcp_bold_movref"] == "first"
            and options["hcp_bold_seimg"] == "independent"
        ):
            # loop over bolds to prepare processing pools
            bolds_pool = []
            for b in bolds_data:
                fmriref = b["fmriref"]
                # if fmriref is "NONE" then process the previous pool followed by this one as single
                if fmriref == "NONE":
                    if len(bolds_pool) > 0:
                        report = execute_multiple_hcp_fmri_volume(
                            sinfo, options, overwrite, hcp, bolds_pool, log, report)
                    bolds_pool = []
                    report = execute_single_hcp_fmri_volume(
                        sinfo, options, overwrite, hcp, b, log, report)
                else:  # else add to pool
                    bolds_pool.append(b)

            # execute remaining pool
            report = execute_multiple_hcp_fmri_volume(
                sinfo, options, overwrite, hcp, bolds_pool, log, report)

        else:
            # if moveref equals first then process first one in serial
            if not options["longitudinal"] and options["hcp_bold_movref"] == "first":
                # process first one
                b = bolds_data[0]
                report = execute_single_hcp_fmri_volume(
                    sinfo, options, overwrite, hcp, b, log, report)

                # remove first one from array then process others in parallel
                bolds_data.pop(0)

            # process the rest in parallel
            report = execute_multiple_hcp_fmri_volume(
                sinfo, options, overwrite, hcp, bolds_data, log, report)

        rep = []
        for k in ["done", "incomplete", "failed", "ready", "not ready", "skipped"]:
            if len(report[k]) > 0:
                rep.append("%s %s" % (", ".join(report[k]), k))

        report = (
            sinfo["id"],
            "HCP fMRI Volume: bolds " + "; ".join(rep),
            len(report["failed"] + report["incomplete"] + report["not ready"]),
        )

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        report = (sinfo["id"], "HCP fMRI Volume failed", 1)
    except Exception:
        log.unknown_error()
        report = (sinfo["id"], "HCP fMRI Volume failed", 1)

    log.close(pipeline="HCP fMRIVolume")

    return log.result(report)


def execute_single_hcp_fmri_volume(sinfo, options, overwrite, hcp, b, log, report):
    # process
    result = execute_hcp_fmri_volume(sinfo, options, overwrite, hcp, b)

    # merge r
    log.raw(result["r"])

    # merge report
    temp_report = result["report"]
    report["done"] += temp_report["done"]
    report["incomplete"] += temp_report["incomplete"]
    report["failed"] += temp_report["failed"]
    report["ready"] += temp_report["ready"]
    report["not ready"] += temp_report["not ready"]
    report["skipped"] += temp_report["skipped"]

    return report


def execute_multiple_hcp_fmri_volume(sinfo, options, overwrite, hcp, bolds_data, log, report):
    # parelements
    parelements = max(1, min(options["parelements"], len(bolds_data)))

    # create a multiprocessing Pool
    process_pool_executor = ProcessPoolExecutor(parelements)

    # partial function
    f = partial(execute_hcp_fmri_volume, sinfo, options, overwrite, hcp)
    results = process_pool_executor.map(f, bolds_data)

    # merge r and report
    for result in results:
        log.raw(result["r"])
        temp_report = result["report"]
        report["done"] += temp_report["done"]
        report["incomplete"] += temp_report["incomplete"]
        report["failed"] += temp_report["failed"]
        report["ready"] += temp_report["ready"]
        report["not ready"] += temp_report["not ready"]
        report["skipped"] += temp_report["skipped"]

    return report


def execute_hcp_fmri_volume(sinfo, options, overwrite, hcp, b):
    # extract data
    boldtarget = b["boldtarget"]
    printbold = b["printbold"]
    gdcfile = b["gdcfile"]
    run = b["run"]
    boldok = b["boldok"]
    boldimg = b["boldimg"]
    refimg = b["refimg"]
    stfile = b["stfile"]
    unwarpdir = b["unwarpdir"]
    echospacing = b["echospacing"]
    spin_neg = b["spinNeg"]
    spin_pos = b["spinPos"]
    sepos2 = b["sepos2"]
    seneg2 = b["seneg2"]
    sezero = b["sezero"]
    sezerobrainmask = b["sezerobrainmask"]
    topupconfig = b["topupconfig"]
    fmmag = b["fmmag"]
    fmphase = b["fmphase"]
    fmcombined = b["fmcombined"]
    fmprecomputed = b["fmprecomputed"]
    fmprecomputedmag = b["fmprecomputedmag"]
    fmriref = b["fmriref"]

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
        # --- process additional parameters
        doslicetime = "FALSE"
        slicetimerparams = ""

        if options["hcp_bold_doslicetime"]:
            doslicetime = "TRUE"

            slicetimerparams = re.split(
                r" +|,|\|", options["hcp_bold_slicetimerparams"]
            )

            slicetimerparams = [e for e in slicetimerparams if e]

            if (
                options["hcp_bold_stcorrdir"] != ""
                and options["hcp_bold_stcorrdir"] not in slicetimerparams
            ):
                slicetimerparams.append(options["hcp_bold_stcorrdir"])
            if (
                options["hcp_bold_stcorrint"] != ""
                and options["hcp_bold_stcorrint"] not in slicetimerparams
            ):
                slicetimerparams.append(options["hcp_bold_stcorrint"])
            if options["hcp_bold_slicetimingfile"]:
                slicetimingfile = f"--tcustom={stfile}"
                if slicetimingfile not in slicetimerparams:
                    slicetimerparams.append(slicetimingfile)

            # iterate over slicetimerparams
            for i in range(len(slicetimerparams)):
                if not slicetimerparams[i].startswith("--"):
                    slicetimerparams[i] = f"--{slicetimerparams[i]}"

            slicetimerparams = "@".join(slicetimerparams)

        # --- Set up the command
        if fmriref == "NONE":
            fmrirefparam = ""
        else:
            fmrirefparam = fmriref

        comm = (
            os.path.join(
                hcp["hcp_base"], "fMRIVolume", "GenericfMRIVolumeProcessingPipeline.sh"
            )
            + " "
        )

        print(
            "======================================================================================================================================="
        )
        elements = [
            ("path", sinfo["hcp"]),
            ("session", sinfo["id"] + options["hcp_suffix"]),
            ("fmriname", boldtarget),
            ("fmritcs", boldimg),
            ("fmriscout", refimg),
            ("SEPhaseNeg", spin_neg),
            ("SEPhasePos", spin_pos),
            ("fmapmag", fmmag),
            ("fmapphase", fmphase),
            ("fmapcombined", fmcombined),
            ("precomputedfmap", fmprecomputed),
            ("precomputedfmapmag", fmprecomputedmag),
            ("echospacing", echospacing),
            ("echodiff", options["hcp_bold_echodiff"]),
            ("unwarpdir", unwarpdir),
            ("fmrires", options["hcp_bold_res"]),
            ("dcmethod", options["hcp_bold_dcmethod"]),
            ("biascorrection", options["hcp_bold_biascorrection"]),
            ("gdcoeffs", gdcfile),
            ("topupconfig", topupconfig),
            ("dof", options["hcp_bold_dof"]),
            ("printcom", options["hcp_printcom"]),
            ("usejacobian", options["hcp_bold_usejacobian"]),
            ("mctype", options["hcp_bold_movreg"].upper()),
            ("preregistertool", options["hcp_bold_preregistertool"]),
            ("processing-mode", options["hcp_processing_mode"]),
            ("doslicetime", doslicetime),
            ("slicetimerparams", slicetimerparams),
            ("fmriref", fmrirefparam),
            ("fmrirefreg", options["hcp_bold_refreg"]),
            ("fmrimask", options["hcp_bold_mask"]),
        ]

        # optional parameters
        if options["hcp_wb_resample"]:
            elements.append(("wb-resample", "1"))

        if options["hcp_echo_te"]:
            echo_te = ("echoTE", options["hcp_echo_te"].replace(",", "@"))
            elements.append(echo_te)

        # matlab run mode, compiled=0, interpreted=1, octave=2
        if options["hcp_matlab_mode"]:
            if options["hcp_matlab_mode"] == "compiled":
                elements.append(("matlab-run-mode", "0"))
            elif options["hcp_matlab_mode"] == "interpreted":
                elements.append(("matlab-run-mode", "1"))
            elif options["hcp_matlab_mode"] == "octave":
                elements.append(("matlab-run-mode", "2"))
            else:
                log.error("unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n")
                run = False

        if options["hcp_bold_seechospacing"]:
            elements.append(("seechospacing", options["hcp_bold_seechospacing"]))

        if options["hcp_bold_seunwarpdir"]:
            elements.append(("seunwarpdir", options["hcp_bold_seunwarpdir"]))

        # optional species / NHP parameters
        # these are only relevant for non-human species, when unset the HCP
        # pipeline defaults (Human) are used
        if options["hcp_species"]:
            elements.append(("species", options["hcp_species"]))

        if options["hcp_scale_factor"]:
            elements.append(("brainscalefactor", options["hcp_scale_factor"]))

        if options["hcp_runmode"]:
            elements.append(("runmode", options["hcp_runmode"]))

        if options["hcp_truepatientposition"]:
            elements.append(("truepatientposition", options["hcp_truepatientposition"]))

        if options["hcp_scannerpatientposition"]:
            elements.append((
                "scannerpatientposition",
                options["hcp_scannerpatientposition"],
            ))

        if options["hcp_bold_bbrcontrast"]:
            elements.append(("bbr-contrast", options["hcp_bold_bbrcontrast"]))

        if options["hcp_bold_wmprojabs"]:
            elements.append(("wmprojabs", options["hcp_bold_wmprojabs"]))

        if options["hcp_bold_initworldmat"]:
            elements.append(("initworldmat", options["hcp_bold_initworldmat"]))

        # second spin-echo pair and zero-phase SE images (NHP), resolved in the
        # main body and passed in via the bold data dictionary
        if seneg2:
            elements.append(("SEPhaseNeg2", seneg2))

        if sepos2:
            elements.append(("SEPhasePos2", sepos2))

        if sezero:
            elements.append(("SEPhaseZero", sezero))

        if sezerobrainmask:
            elements.append(("SEPhaseZeroFSBrainmask", sezerobrainmask))

        # longitudinal mode
        if options["longitudinal"]:
            studyfolder = gc.deduce_folders(options)["basefolder"]
            if not studyfolder:
                log.raw("\nERROR: cannot deduce the QuNex study folder from provided parameters! Please provide the sessionsfolder or the studyfolder parameter.")
                run = False
            # replace path (elements[0])
            elements[0] = (
                "path",
                os.path.join(studyfolder, "subjects", sinfo["subject"]),
            )
            elements.append(("is-longitudinal", "1"))
            elements.append((
                "longitudinal-session",
                f"{sinfo['id']}{options['hcp_suffix']}.long.{options['hcp_longitudinal_template']}",
            ))

        comm += " ".join(['--%s="%s"' % (k, v) for k, v in elements if v])

        # -- Report command
        if boldok:
            log.pipeline_command(comm)

        # -- Test files
        tfile = None
        full_test = None
        if not options["longitudinal"]:
            tfile = os.path.join(
                hcp["hcp_nonlin"], "Results", boldtarget, "%s.nii.gz" % (boldtarget)
            )

            if hcp["hcp_bold_vol_check"]:
                full_test = {
                    "tfolder": hcp["base"],
                    "tfile": hcp["hcp_bold_vol_check"],
                    "fields": [
                        ("sessionid", sinfo["id"] + options["hcp_suffix"]),
                        ("scan", boldtarget),
                    ],
                    "specfolder": options["specfolder"],
                }

        # -- Run
        if run and boldok:
            if options["run"] == "run":
                if not options["longitudinal"] and (
                    overwrite or not os.path.exists(tfile)
                ):
                    # ---> Clean up existing data
                    # -> bold working folder
                    bold_folder = os.path.join(hcp["base"], boldtarget)
                    if os.path.exists(bold_folder):
                        log.detail("removing preexisting working bold folder [%s]"
                            % (bold_folder))
                        shutil.rmtree(bold_folder)

                    # -> bold MNINonLinear results folder
                    bold_folder = os.path.join(hcp["hcp_nonlin"], "Results", boldtarget)
                    if os.path.exists(bold_folder):
                        log.detail("removing preexisting MNINonLinar results bold folder [%s]"
                            % (bold_folder))
                        shutil.rmtree(bold_folder)

                    # -> bold T1w results folder
                    bold_folder = os.path.join(hcp["T1w_folder"], "Results", boldtarget)
                    if os.path.exists(bold_folder):
                        log.detail("removing preexisting T1w results bold folder [%s]"
                            % (bold_folder))
                        shutil.rmtree(bold_folder)

                    # -> xfms in T1w folder
                    xfms_file = os.path.join(
                        hcp["T1w_folder"], "xfms", "%s2str.nii.gz" % (boldtarget)
                    )
                    if os.path.exists(xfms_file):
                        log.detail("removing preexisting xfms file [%s]" % (
                            xfms_file
                        ))
                        os.remove(xfms_file)

                    # -> xfms in MNINonLinear folder
                    xfms_file = os.path.join(
                        hcp["hcp_nonlin"], "xfms", "%s2str.nii.gz" % (boldtarget)
                    )
                    if os.path.exists(xfms_file):
                        log.detail("removing preexisting xfms file [%s]" % (
                            xfms_file
                        ))
                        os.remove(xfms_file)

                    # -> xfms in MNINonLinear folder
                    xfms_file = os.path.join(
                        hcp["hcp_nonlin"], "xfms", "standard2%s.nii.gz" % (boldtarget)
                    )
                    if os.path.exists(xfms_file):
                        log.detail("removing preexisting xfms file [%s]" % (
                            xfms_file
                        ))
                        os.remove(xfms_file)

                logtags = [options["logtag"], boldtarget]
                if options["longitudinal"]:
                    logtags.append("long")

                _, _, failed = log.run_external(
                    tfile,
                    comm,
                    "Running HCP fMRIVolume",
                    overwrite=overwrite,
                    thread=sinfo["id"],
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=logtags,
                    full_test=full_test,
                    shell=True,
                )

                if failed:
                    report["failed"].append(printbold)
                else:
                    report["done"].append(printbold)

            # -- just checking
            else:
                passed, _, failed = log.check_run(
                    tfile,
                    full_test,
                    "HCP fMRIVolume " + boldtarget,
                    overwrite=overwrite,
                )
                if passed is None:
                    log.step("HCP fMRIVolume can be run")
                    report["ready"].append(printbold)
                else:
                    report["skipped"].append(printbold)

        else:
            report["not ready"].append(printbold)
            if options["run"] == "run":
                log.error("something missing, skipping this BOLD!")
            else:
                log.error("something missing, this BOLD would be skipped!")

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw("\n\n\n --- Failed during processing of bold %s with error:\n" % (printbold))
        log.raw(str(errormessage))
        report["failed"].append(printbold)
    except Exception:
        log.raw("\n --- Failed during processing of bold %s with error:\n %s\n" % (
            printbold,
            traceback.format_exc(),
        ))
        report["failed"].append(printbold)

    return {"r": log.text, "report": report}
