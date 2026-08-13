#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``workflow/preprocess_conc.py``

Processes concatenated BOLD files.
"""

# Created by Grega Repovs on 2016-12-17.
# Code split from dofcMRIp_core gCodeP/preprocess codebase.
# Copyright (c) Grega Repovs. All rights reserved.

import os
import time
import traceback
from datetime import datetime

import qx_utilities.processing.core as pc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.img as gi
from qx_utilities.general.log import ReportLog
from qx_utilities.processing.workflow import dryrun
from qx_utilities.processing.workflow.dryrun import mcommand


def preprocess_conc(sinfo, options, overwrite=False, thread=0):
    r"""
    ``preprocess_conc [... processing options]``

    Preproces conc bundles of BOLD images.

    Description:
        Performs spatial smoothing, temporal filtering, removal of nuisance signals
        and complex modeling of events.

        preprocess_conc is a complex general purpose command implementing spatial
        and temporal filtering, and multiple regression (GLM) to enable both
        preprocessing and denoising of BOLD files for further analysis, as well as
        complex activation modeling that creates GLM files for second-level
        analyses. The function enables the following actions:

        - spatial smoothing (3D or 2D for cifti files)
        - temporal filtering (high-pass, low-pass)
        - removal of nuisance signal
        - complex modeling of events.

        The function makes use of a number of files and accepts a long list of
        arguments that make it very powerful and flexible but also require care in
        its use. What follows is a detailed documentation of its actions and
        parameters organized by actions in the order they would be most commonly
        done. Use and parameter description will be intertwined.

    ..  qx_command:
        type: processing.session



    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the session information.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder, where the imaging  data is
            supposed to go.

        --parsessions (str, default 1):
            How many sessions to run in parallel.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --boldname (str, default 'bold'):
            The default name of the bold files in the images folder.

        --image_target (str, default 'nifti'):
            The target format to work with, one of '4dfp', 'nifti', 'dtseries'
            or 'ptseries'.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --log (str, default 'keep'):
            Whether to keep ('keep') or remove ('remove') the temporary logs
            once jobs are completed. A comlog that recorded an error is kept
            whichever is asked for, and a removed one still leaves its
            completion status in the run log.

        --comlog_folders (str, default ''):
            A comma or pipe ('|') separated list of locations the comlogs are
            placed in. The comlog is created at the first provided location and
            then linked or copied to the others. The valid locations are:

            - 'study'   (for the default:
              ``<study>/processing/logs/comlogs`` location)
            - 'session' (for ``<sessionid>/logs/comlogs``)
            - 'hcp'     (for ``<hcp_folder>/logs/comlogs``)
            - <path>  (for an arbitrary directory).

            When empty, the value from the settings file is used, which
            defaults to 'study'.

        --bolds (str, default 'all'):
            A pipe ('|') separated list of conc names to process.

        --event_file (str, default ''):
            A pipe ('|') separated list of fidl names to use, that
            matches the conc list.

        --bold_actions (str, default 's,h,r,c,l'):
            A string specifying which actions, and in what sequence
            to perform.

        --nifti_tail (str, default ''):
            The tail of NIfTI volume images to use.

        --cifti_tail (str, default ''):
            The tail of CIFTI images to use.

        --bold_prefix (str, default ''):
            An optional prefix to place in front of processing name extensions
            in the resulting files, e.g. bold3<bold_prefix>_s_hpss.nii.gz.

        --bold_variant (str, default detailed below):
            Optional variant of HCP BOLD preprocessing. If specified, the BOLD
            images in `images/functional<bold_variant>` will be processed.

        --img_suffix (str, default ''):
            Specifies a suffix for 'images' folder to enable support for
            multiple parallel workflows. Empty if not used.

    Output files:
        This step results in the following files (if requested):

        - residual image::

            <root>_res-<regressors><glm name>.<ext>

        - GLM image::

            <bold name><bold tail>_conc_<event root>_res-<regressors><glm name>_Bcoeff.<ext>

        - text GLM regressor matrix::

            glm/<bold name><bold tail>_GLM-X_<event root>_res-<regressors><glm name>.txt

        - image of a regressor matrix::

            ``glm/<bold name><bold tail>_GLM-X_<event root>_res-<regressors><glm name>.png``

    Notes:
        The --bolds and --event_file parameters provide names based on which the
        the appropriate .conc and .fidl files are searched for. Both are first
        searched for in `images<img_suffix>/functional<bold_variant>/concs` and
        images<img_suffix>/functional<bold_variant>/events folders
        respectively. There they would be named as `[<session
        id>_]<boldname>_<image_target>_<conc name>.conc` and `[<session
        id>_]<boldname>_<image_target>_<fidl name>.fidl`. If the files are not
        present in the relevant individual session's folders, they are searched
        for in the `<sessionsfolder>/inbox/events` and
        `<sessionsfolder>/inbox/concs` folder. In that case the "<session id>_"
        in the \*.fidl and \*.conc file name is not optional but required.

        The --bold_actions parameter specifies the actions, denoted by a single
        letter, that will be executed in the sequence listed:

        --m     Motion scrubbing.
        --s     Spatial smoothing.
        --h     High-pass filtering.
        --r     Regression (nuisance and/or task) with an optional number 0, 1,
                or 2 specifying the type of regression to use (see REGRESSION
                below).
        --l     Low-pass filtering.

        So the default 's,h,r,c,l' --bold_actions parameter would lead to the
        files first being smoothed, then high-pass filtered. Next a regression
        step would follow in which nuisance signal and/or task related signal
        would be estimated and regressed out, then the related beta estimates
        would be saved. Lastly the BOLDs would be also low-pass filtered.

        Relative vs. absolute use of conc files:
            If `conc_use` is set to relative (the default), then the only
            information taken from the conc files will be the bold numbers. The
            actual location of the bold files will be constructed from the
            information on the location of the session's sesion folder present
            in the batch file, and the `bold_variant` setting, whereas the
            specific bold file name and file format (e.g. .nii.gz vs.
            .dtseries.nii) to use will depend on `boldname`, `image_target`,
            `nifti_tail` and `cifti_tail` settings. This allows for flexible
            use of conc files. That is, the same conc files can be used for
            NIfTI and CIFTI versions of bold files, across bold variants, and
            even when the actual study location changes, e.g. when moving the
            study from one server, volume or folder to another. In most cases
            this use will be prefered.

            If the information in the conc file is to be used literally, e.g. in
            cases when you want to work with a specific preprocessed version of
            the BOLD files, then `conc_use` should be set to `absolute`. In
            this case both the specific location as well as the specific
            filename specified in the conc file will be used exactly as
            specified. In this case, do check and make sure that the
            information in the conc file is valid and it matches with
            `boldname` and `image_target` parameters, and that the `nifti_tail`
            is specified correctly, as it will be used to obtain bold
            statistics and nuisance information!

        Scrubbing:
            The command either makes use of scrubbing information or performs
            scrubbing comuputation on its own (when 'm' is part of the
            command). In the latter case, all the scrubbing parameters need to
            be specified:

            --mov_radius (int, default 50):
                Estimated head radius (in mm) for computing frame displacement
                statistics.
            --mov_fd (float, default 0.5):
                Frame displacement threshold (in mm) to use for identifying bad
                frames.
            --mov_dvars (float, default 3.0):
                The (mean normalized) dvars threshold to use for identifying bad
                frames.
            --mov_dvarsme (float, default 1.5):
                The (median normalized) dvarsm threshold to use for identifying
                bad frames.
            --mov_after (int, default 0):
                How many frames after each frame identified as bad to also
                exclude from further processing and analysis.
            --mov_before (int, default 0):
                How many frames before each frame identified as bad to also
                exclude from further processing and analysis.
            --mov_bad (str, default 'udvarsme'):
                Which criteria to use for identification of bad frames.

            Criteria for identification of bad frames can be one out of:

            --mov
                Frame displacement threshold (fdt) is exceeded.
            --dvars
                Image intensity normalized root mean squared error (RMSE)
                threshold (dvarsmt) is exceeded.
            --dvarsme
                Median normalised RMSE (dvarsmet) threshold is exceeded.
            --idvars
                Both fdt and dvarsmt are exceeded (i for intersection).
            --uvars
                Either fdt or dvarsmt are exceeded (u for union).
            --idvarsme
                Both fdt and dvarsmet are exceeded.
            --udvarsme
                Either fdt or dvarsmet are exceeded.

            For more detailed description please see wiki entry on Movement
            scrubbing.

            In any case, if scrubbing was done beforehand or as a part of this
            command, one has to specify, how the scrubbing information is used:

            --pignore
                String describing how to deal with bad frames.

            The string has the following format::

                'hipass:<filtering opt.>|regress:<regression opt.>|lopass:<filtering opt.>'

            Filtering options are:

            --keep
                Keep all the bad frames unchanged.
            --linear
                Replace bad frames with linear interpolated values based on
                neighboring good frames.
            --spline
                Replace bad frames with spline interpolated values based on
                neighboring good frames.

            To prevent artifacts present in bad frames to be temporarily spread,
            use either 'linear' or 'spline' options.

            Regression options are:

            --keep
                Keep the bad frames and use them in the regression.
            --ignore
                Exclude bad frames from regression.
            --mark
                Exclude bad frames from regression and mark the bad frames as
                NaN.
            --linear
                Replace bad frames with linear interpolated values based on
                neighboring good frames.
            --spline
                Replace bad frames with spline interpolated values based on
                neighboring good frames.

            Please note that when the bad frames are not kept, the original
            values will be retained in the residual signal. In this case they
            have to be excluded or ignored also in all following analyses,
            otherwise they can be a significant source of artifacts.

        Spatial smoothing:
            Volume smoothing:
                For volume formats the images will be smoothed using the
                img_smooth_3d nimage method. For cifti format the smooting will
                be done by calling the relevant wb_command command. The
                smoothing parameters are:

                --voxel_smooth (int, default 1):
                    Gaussian smoothing FWHM in voxels.
                --smooth_mask (str, default false):
                    Whether to smooth only within a mask, and what mask to use
                    (nonzero|brainsignal|brainmask|<filename>|false).
                --dilate_mask (str, default false):
                    Whether to dilate the image after masked smoothing and what
                    mask to use
                    (nonzero|brainsignal|brainmask|same|<filename>|false).

                If a smoothing mask is set, only the signal within the specified
                mask will be used in the smoothing. If a dilation mask is set,
                after smoothing within a mask, the resulting signal will be
                constrained / dilated to the specified dilation mask.

                For both parameters the possible options are:

                --nonzero
                    Mask will consist of all the nonzero voxels of the first
                    BOLD frame.
                --brainsignal
                    Mask will consist of all the voxels that are of value 300 or
                    higher in the first BOLD frame (this gave a good coarse
                    brain mask for images intensity normalized to mode 1000 in
                    the NIL preprocessing stream).
                --brainmask
                    Mask will be the actual bet extracted brain mask based on
                    the first BOLD frame (generated using in the
                    creatBOLDBrainMasks command).
                --filename
                    All the non-zero voxels in a specified volume file will be
                    used as a mask.
                --false
                    No mask will be used.
                --same
                    Only for dilate_mask, the mask used will be the same as
                    smoothing mask.

            Cifti smoothing:
                For cifti format images, smoothing will be run using wb_command.
                The following parameters can be set:

                --surface_smooth (float, default 2.0):
                    FWHM for Gaussian surface smoothing in mm.
                --volume_smooth (float, default 2.0):
                    FWHM for Gaussian volume smoothing in mm.
                --framework_path (str, default ''):
                    The path to framework libraries on the Mac system. No need
                    to use it currently if installed correctly.
                --wb_command_path (str, default ''):
                    The path to the wb_command executive. No need to use it
                    currently if installed correctly.

                Results:
                    The resulting smoothed files are saved with '_s' added to
                    the BOLD root filename.


        Temporal filtering:
            Temporal filtering is accomplished using img_filter nimage method.
            The code is adopted from the FSL C++ code enabling appropriate
            handling of bad frames (as described above - see SCRUBBING). The
            parameters are:

            --hipass_filter (float, default 0.008):
                The frequency for high-pass filtering in Hz.
            --lopass_filter (float, default 0.09):
                The frequency for low-pass filtering in Hz.

            Please note that the values finally passed to img_filter method are
            the respective sigma values computed from the specified frequencies
            and TR.

            Filtering of nuisance signal, movement, task, and events
            Besides data, nuisance signal, motion parameters, and event
            regressors can be filtered as well. What to filter beside data can
            be specified by a comma separated list using the following
            parameters:

            --hipass_do (str, default 'nuisance')
                What to high-pass filter besides data – options are: nuisance,
                movement, events, task. Default is 'nuisance'.

            --lopass_do (str, default 'nuisance,movement,task,events')
                What to lo-pass filter besides data – options are: nuisance,
                movement, events, task. Default is 'nuisance, movement, task,
                events'.

            Note that 'events' refers to regressors created based on events
            as specified in the fidl file, whereas 'task' refers to a task
            matrix that is passed directy in the matlab function call.

            Results:
                The resulting filtered files are saved with '_hpss' or '_bpss'
                added to the BOLD root filename for high-pass and low-pass
                filtering, respectively.

        Regression:
            Regression is a complex step in which GLM is used to estimate the
            beta weights for the specified nuisance regressors and events. The
            resulting beta weights are then stored in a GLM file (a regular
            file with additional information on the design used) and residuals
            are stored in a separate file. This step can therefore be used for
            two purposes: (1) to remove nuisance signal and event structure
            from BOLD files, removing unwanted potential sources of correlation
            for further functional connectivity analyses, and (2) to get task
            beta estimates for further activation analyses. The following
            parameters are used in this step:

            --bold_nuisance (str, default 'm,m1d,mSq,m1dSq,V,WM,WB,1d'):
                A comma separated list of regressors to include in GLM.
                Possible values are:

                - 'm'     ... motion parameters
                - 'm1d'   ... first derivative of motion parameters
                - 'mSq'   ... squared motion parameters
                - 'm1dSq' ... squared first derivative of motion parameters
                - 'V'     ... ventricles signal
                - 'WM'    ... white matter signal
                - 'WB'    ... whole brain signal
                - '1d'    ... first derivative of above nuisance signals
                - 'e'     ... events listed in the provided fidl files.

            --event_string (str, default ''):
                A string describing, how to model the events listed in the
                provided fidl files.
            --glm_matrix (str, default 'none'):
                Whether to save the GLM matrix as a text file ('text'), a png
                image file ('image'), both ('both') or not ('none').
            --glm_results (str, default 'c,r')
                A string  which of the GLM analysis results are saved.
                Possible values are:

                - 'c'   ... Saving of resulting beta coefficients.
                - 'z'   ... Saving of resulting z-scores of beta coefficients.
                - 'p'   ... Saving of session-level coefficient p-values.
                - 'se'  ... Saving of standard errors of beta coefficients.
                - 'r'   ... Saving of resulting residuals of the GLM.
                - 'all' ... Saving all of the results above.

            --glm_name (str, default ''):
                An additional name to add to the residuals and GLM files to
                distinguish between different possible models used.

            GLM modeling:
                There are two important variables that affect the exact GLM
                model used to estimate nuisance and task beta coefficients and
                regress them from the signal. The first is the optional number
                following the 'r' command in the --bold_actions parameter.
                There are three options:

                - '0' ... Estimate nuisance regressors for each bold file
                  separately, however, model events across all bold files (the
                  default if no number is) specified.
                - '1' ... Estimate both nuisance regressors and task regressors
                  for each bold run separately.
                - '2' ... Estimate both nuisance regressors as well as task
                  regressors across all bold runs.

                The second key variable is the event string provided by the
                --event_string parameter. The event string is a pipe ('|')
                separated list of regressor specifications. The possibilities
                are discussed below:

                Unassumed Modeling:
                    ::

                        <fidl code>:<length in frames>

                    Where <fidl code> is the code for the event used in the fidl
                    file, and <length in frames> specifies, for how many frames
                    of the bold run (since the onset of the event) the event
                    should be modeled.

                Assumed Modeling:
                    ::

                        <fidl code>:<hrf>[-run|-uni][:<length>]

                    Where <fidl code> is the same as above, <hrf> is the type of
                    the hemodynamic response function to use, '-run' and '-uni'
                    specify how the regressor should be normalized, and
                    <length> is an optional parameter, with its value dependent
                    on the model used. The allowed <hrf> are:

                    - 'boynton' ... uses the Boynton HRF
                    - 'SPM'     ... uses the SPM double gaussian HRF
                    - 'u'       ... unassumed (see above)
                    - 'block'   ... block response.

                    For the first two, the <length> parameter is optional and
                    would override the event duration information provided in
                    the fidl file. For 'u' the length is the same as in
                    previous section: the number of frames to model. For
                    'block' length should be two numbers separated by a colon
                    (e.g. 2:9) that specify the start and end offset (from the
                    event onset) to model as a block.

                    Assumed HRF regressors normalization:
                        hrf_types `boynton` and `SPM` can be marked with an
                        additional flag denoting how to normalize the
                        regressor.

                        In case of `<hrf function>-uni`, e.g. 'boynton-uni' or
                        'SPM-uni', the HRF function will be normalized to have
                        the area under the curve equal to 1. This ensures
                        uniform and universal, scaling of the resulting
                        regressor across all event lengths. In addition, the
                        scaling is not impacted by weights (e.g. behavioral
                        coregressors), which in turn ensures that the weights
                        are not scaled.

                        In case of `<hrf function>-run`, e.g. `boynton-run` or
                        `SPM-run`, the resulting regressor is normalized to
                        amplitude of 1 within each bold run separately. This
                        can result in different scaling of regressors with
                        different durations, and of the same regressor across
                        different runs. Scaling in this case is performed after
                        the signal is weighted, so in effect the scaling of
                        weights (e.g. behavioral regressors), can differ across
                        bold runs.

                        The flag can be abbreviated to '-r' and '-u'. If not
                        specified, '-run' will be assumed (the default might
                        change).

                Naming And Behavioral Regressors:
                    Each of the above (unassumed and assumed modeling
                    specification) can be followed by a ">" (greater-than
                    character), which signifies additional information in the
                    form::

                        <name>[:<column>[:<normalization_span>[:<normalization_method>]]]

                    --name
                        The name of the resulting regressor.
                    --column
                        The number of the additional behavioral regressors
                        column in the fidl file (1-based) to use as a weight
                        for the regressors.
                    --normalization_span
                        Whether to normalize the behavioral weight within a
                        specific event type ('within') or across all events
                        ('across'). [within]
                    --normalization_method
                        The method to use for normalization. Options are:

                        - 'z'    (compute Z-score)
                        - '01'   (normalize to fixed range 0 to 1)
                        - '-11'  (normalize to fixed range -1 to 1)
                        - 'none' (use weights as provided in fidl file)

                    Example string::

                        'block:boynton|target:9|target:9>target_rt:1:within:z'

                    This would result in three sets of task regressors: one
                    assumed task regressor for the sustained activity across
                    the block, one unassumed task regressor set spanning 9
                    frames that would model the presentation of the target, and
                    one behaviorally weighted unassumed regressor that would
                    for each frame estimate the variability in response as
                    explained by the reaction time to the target.

    Examples:
        Activation analysis::

            qunex preprocess_conc \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --bolds=SRT \\
                --event_file=SRT \\
                --glm_name=-M1 \\
                --bold_actions="s,r,c" \\
                --bold_nuisance=e \\
                --mov_bad=none \\
                --event_string="block:boynton|target:9|target:9>target_rt:1:within:z" \\
                --glm_matrix=both \\
                --glm_residuals=none \\
                --pignore="hipass=keep|regress=keep|lopass=keep"

        Functional connectivity preprocessing::

            qunex preprocess_conc \\
                --batchfile=fcMRI/sessions_hcp.txt \\
                --sessionsfolder=sessions \\
                --overwrite=no \\
                --parsessions=10 \\
                --bolds=SRT \\
                --event_file=SRT \\
                --glm_name=-FC \\
                --bold_actions="s,h,r,c,l" \\
                --bold_nuisance="m,V,WM,WB,1d,e" \\
                --mov_bad=udvarsme \\
                --event_string="block:boynton|target:9" \\
                --glm_matrix=none \\
                --glm_residuals=save \\
                --pignore="hipass=linear|regress=ignore|lopass=linear"
    """
    log = ReportLog()

    pc.do_options_check(options, sinfo, "preprocess_conc")

    log.rule()
    log.info(f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]")
    log.action("Running", "Preprocessing conc bundles ...", options["run"], level="info")
    log.info(f"Files in 'images{options['img_suffix']}/functional{options['bold_variant']} will be processed.")

    # --- extract conc and fidl names
    concs = [e.strip().replace(".conc", "") for e in options["bolds"].split("|")]
    fidls = [e.strip().replace(".fidl", "") for e in options["event_file"].split("|")]

    # --- define the tail
    options["bold_tail"] = options["nifti_tail"]
    if options["image_target"] in ["cifti", "dtseries", "ptseries"]:
        options["bold_tail"] = options["cifti_tail"]

    concroot = "_".join(
        e
        for e in [
            options["boldname"] + options["bold_tail"],
            options["image_target"].replace("cifti", "dtseries"),
        ]
        if e
    )
    report = ""

    failed = 0
    if len(concs) != len(fidls):
        log.error(f"Number of conc files ({len(concs)}) does not match number of event files ({len(fidls)}), processing aborted!")

    else:
        for nb in range(0, len(concs)):
            tconc = concs[nb]
            tfidl = fidls[nb]
            options["concname"] = tconc
            if tfidl:
                options["fidlname"] = tfidl
            else:
                options["fidlname"] = ""

            try:
                log.raw(f"\n\nConc bundle: {tconc}")

                d = pc.get_session_folders(sinfo, options)
                f = {}
                f_conc = os.path.join(
                    d["s_bold_concs"], concroot + "_" + tconc + ".conc"
                )
                f_fidl = os.path.join(d["s_bold_events"], tfidl + ".fidl")

                # --- find conc data

                if overwrite or not os.path.exists(f_conc):
                    tf = pc.find_file(sinfo, options, tconc + ".conc")
                    if tf:
                        log.detail(f"getting conc data from {tf}")
                        if os.path.exists(f_conc):
                            dryrun.remove(log, options, f_conc)
                        dryrun.copy(log, options, tf, f_conc)

                    else:
                        log.error(f"Conc data file ({tconc}) does not exist in the expected locations! Skipping this conc bundle.", depth=1)
                        failed += 1
                        continue
                else:
                    log.detail("conc data present")

                # --- find fidl data

                if "e" in [e.strip() for e in options["bold_nuisance"].split(",")]:
                    if overwrite or not os.path.exists(f_fidl):
                        tf = pc.find_file(sinfo, options, tfidl + ".fidl")
                        if tf:
                            log.detail(f"getting event data from {tf}")
                            if os.path.exists(f_fidl):
                                dryrun.remove(log, options, f_fidl)
                            dryrun.copy(log, options, tf, f_fidl)
                        else:
                            log.error(f"Event data file ({tfidl}) does not exist in the expected locations! Skipping this conc bundle.", depth=1)
                            failed += 1
                            continue
                    else:
                        log.detail("event data present")
                else:
                    log.detail(f"event data not needed (e not specified in --bold_nuisance) {options['bold_nuisance']}")

                # --- loop through bold files

                conc = gi.read_conc(f_conc, boldname=options["boldname"])
                nconc = []
                bolds = []
                rstatus = True
                check = {"ok": [], "bad": []}

                if len(conc) == 0:
                    log.error(f"No valid image files in conc file ({f_conc})! Skipping this conc bundle.", depth=1)
                    failed += 1
                    continue

                for c in conc:
                    # print("c from conc:", c)
                    boldnum = c[1]
                    boldname = options["boldname"] + boldnum
                    bolds.append(boldnum)

                    # if absolute path flag use session folder from conc file
                    if options["conc_use"] == "absolute":
                        # extract session folder from conc file
                        options["sessionsfolder"] = (c[0].split(sinfo["id"]))[0]
                        d["s_base"] = options["sessionsfolder"] + sinfo["id"]
                        options["bold_tail"] = (c[0].split(boldname))[1].replace(
                            pc.get_extension(options["image_target"]), ""
                        )

                    log.raw("\n\nLooking up: " + boldname + " ...")

                    # --- filenames
                    f = pc.get_file_names(sinfo, options)
                    f.update(pc.get_bold_file_names(sinfo, boldname, options))

                    # if absolute path flag use also exact filename (extension)
                    if options["conc_use"] == "absolute":
                        f["bold"] = c[0]

                    # --- check for data availability

                    # r += '\n    ... checking for data'
                    status = True

                    # --- bold
                    status = pc.check_for_file(f["bold"],
                        "bold data present",
                        f"bold data missing [{f['bold']}]",
                        status=status,
                        _log=log,
                    )
                    nconc.append((f["bold"], boldnum))

                    # --- movement
                    if "r" in options["bold_actions"] and (
                        "m" in options["bold_nuisance"]
                        or "m" in options["bold_actions"]
                    ):
                        status = pc.check_for_file(f["bold_mov"],
                            "movement data present",
                            f"movement data missing [{f['bold_mov']}]",
                            status=status,
                            _log=log,
                        )

                    # --- bold stats
                    if "m" in options["bold_actions"]:
                        status = pc.check_for_file(f["bold_stats"],
                            "bold statistics data present",
                            f"bold statistics data missing [{f['bold_stats']}]",
                            status=status,
                            _log=log,
                        )

                    # --- bold scrub
                    if any(
                        [
                            e in options["pignore"]
                            for e in ["linear", "spline", "ignore"]
                        ]
                    ):
                        status = pc.check_for_file(f["bold_scrub"],
                            "bold scrubbing data present",
                            f"bold scrubbing data missing [{f['bold_scrub']}]",
                            status=status,
                            _log=log,
                        )

                    # --- check for nuisance data files if doing regression

                    if "r" in options["bold_actions"] and any(
                        [e in options["bold_nuisance"] for e in ["V", "WM", "WB"]]
                    ):
                        status = pc.check_for_file(f["bold_nuisance"],
                            "bold nuisance signal data present",
                            f"bold nuisance signal data missing [{f['bold_nuisance']}]",
                            status=status,
                            _log=log,
                        )

                    # --- check
                    if not status:
                        log.error("Files missing!")
                        rstatus = False
                        check["bad"].append(boldnum)
                    else:
                        check["ok"].append(boldnum)

                # --- all files reviewed continuing conc processing

                report = ""
                if len(check["ok"]) > 0:
                    report += "%d bolds ok [%s], " % (
                        len(check["ok"]),
                        " ".join(check["ok"]),
                    )
                else:
                    report += "0 bolds ok, "

                if len(check["bad"]) > 0:
                    report += "%d bold not ok [%s], " % (
                        len(check["bad"]),
                        " ".join(check["bad"]),
                    )
                else:
                    report += "0 bolds not ok"

                if not rstatus:
                    log.error("Due to missing data we are skipping this conc bundle!")
                    report += " => missing data"
                    failed += 1
                    continue

                if options["run"] == "run":
                    gi.write_conc(f_conc, nconc)
                else:
                    log.detail(f"test, not rewritten: {f_conc}")

                # --- run matlab preprocessing script

                if overwrite:
                    boldow = "true"
                else:
                    boldow = "false"

                done = f["conc_final"] + ".ok"

                scrub = (
                    "radius:%(mov_radius)d|fdt:%(mov_fd).2f|dvarsmt:%(mov_dvars).2f|dvarsmet:%(mov_dvarsme).2f|after:%(mov_after)d|before:%(mov_before)d|reject:%(mov_bad)s"
                    % (options)
                )
                opts = (
                    "boldname=%(boldname)s|fidlname=%(fidlname)s|concname=%(concname)s|surface_smooth=%(surface_smooth)f|volume_smooth=%(volume_smooth)f|voxel_smooth=%(voxel_smooth)f|hipass_filter=%(hipass_filter)f|lopass_filter=%(lopass_filter)f|framework_path=%(framework_path)s|wb_command_path=%(wb_command_path)s|smooth_mask=%(smooth_mask)s|dilate_mask=%(dilate_mask)s|glm_matrix=%(glm_matrix)s|glm_residuals=%(glm_residuals)s|glm_results=%(glm_results)s|glm_name=%(glm_name)s|bold_tail=%(bold_tail)s|ref_bold_tail=%(nifti_tail)s|bold_variant=%(bold_variant)s|img_suffix=%(img_suffix)s"
                    % (options)
                )

                mcomm = (
                    "fc_preprocess_conc('%s', [%s], '%s', %.3f,  %d, '%s', [], '%s.fidl', '%s', '%s', %s, '%s', '%s', '%s', '%s', '%s')"
                    % (
                        d["s_base"],  # --- session folder
                        " ".join(
                            bolds
                        ),  # --- vector of bold runs in the order of the conc file
                        options[
                            "bold_actions"
                        ],  # --- which steps to perform in what order (s, h, r0/r1/r2, c, p, l)
                        options["tr"],  # --- TR
                        options[
                            "omit"
                        ],  # --- the number of frames to omit at the start of each run
                        options[
                            "bold_nuisance"
                        ],  # --- nuisance regressors (m, v, wm, wb, d, t, e)
                        tfidl,  # --- event file to be used for task regression (w/o .fidl)
                        options[
                            "event_string"
                        ],  # --- event string specifying what and how of task to regress
                        options[
                            "bold_prefix"
                        ],  # --- optional prefix to the resulting bolds
                        boldow,  # --- whether to overwrite existing files
                        gi.get_img_format(
                            f["bold_final"]
                        ),  # --- the format of the images (.nii vs. .4dfp.img)
                        scrub,  # --- scrub parameters string
                        options[
                            "pignore"
                        ],  # --- how to deal with bad frames ('hipass:keep/linear/spline|regress:keep/ignore|lopass:keep/linear/spline')
                        opts,  # --- additional options
                        done,
                    )
                )  # --- file to save when done

                comm = (
                    '%s "try %s; catch ME, general_report_crash(ME); exit(1), end; exit;"'
                    % (mcommand, mcomm)
                )

                log.blank()
                log.action(
                    "Running", "nuisance and task removal", options["run"], level="info"
                )
                if options["print_command"] == "yes":
                    log.raw("\n" + comm + "\n")
                if options["run"] == "run":
                    # the third return is this call's failure flag, not the
                    # count of failed conc bundles this loop is accumulating
                    endlog, status, _ = pc.run_external_for_file(
                        done,
                        comm,
                        "running matlab/octave fc_preprocess_conc on bolds [%s]"
                        % (" ".join(bolds)),
                        overwrite=overwrite,
                        thread=sinfo["id"],
                        remove=options["log"] == "remove",
                        task=options["command_ran"],
                        logfolder=options["comlogs"],
                        logtags=[
                            options["bold_variant"],
                            options["bolds"],
                            options["glm_name"],
                            options["logtag"],
                        ],
                        shell=True,
                        _log=log,
                    )
                    status = pc.check_for_file(
                        done,
                        bad=f"Matlab/Octave has failed preprocessing BOLD using command: \n---> {mcomm}\n",
                        bad_level="error",
                        _log=log,
                    )
                    if os.path.exists(done):
                        os.remove(done)
                    if status:
                        report += " => processed ok"
                    else:
                        report += " => processing failed"
                        failed += 1
                else:
                    log.detail(f"test, not run: {comm}", depth=1)
                    if os.path.exists(done):
                        report += " => already done"
                    else:
                        report += " => ready"
                        failed += 1

            except ge.CommandFailed as e:
                log.raw("\n" + ge.report_command_failed("preprocess_conc", e))
                report += " => processing failed"
                failed += 1
            except ge.CommandError as e:
                log.raw("\n" + ge.report_command_error("preprocess_conc", e))
                report += " => processing failed"
                failed += 1
            except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
                log.raw(str(errormessage))
                report += " => processing failed"
                failed += 1
            except Exception:
                report += " => processing failed"
                log.error(f"Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n")
                time.sleep(5)
                failed += 1

    log.blank()
    log.info(f"Conc preprocessing (v2) completed on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}")
    log.rule()

    # print r
    return log.result(report, failed, sinfo["id"])
