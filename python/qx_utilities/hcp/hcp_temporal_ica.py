#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

"""
``hcp_temporal_ica.py``

The HCP temporal ICA pipeline.
"""

import os
import os.path

import qx_utilities.general.folders as gf
import qx_utilities.hcp.tica_folders as tf
import qx_utilities.processing.core as pc
from qx_utilities.general.log import SessionLog
from qx_utilities.hcp.hcp_make_average_dataset import (
    average_dataset_folder,
    average_dataset_study,
)
from qx_utilities.hcp.hcp_utils import (
    do_hcp_options_check,
)


def hcp_temporal_ica(sessions, options, overwrite=True, thread=0):
    """
    ``hcp_temporal_ica [studyfolder=<path to study folder>] [sessionsfolder=<studyfolder>/sessions] [... processing options]``

    Run the HCP temporal ICA pipeline (tICAPipeline.sh).

    ..  qx_command:
        type: processing.study
        aliases: hcp_tica

    Warning:
        The code expects the HCP minimal preprocessing pipeline, HCP ICAFix,
        HCP MSMAll and HCP make average dataset to be executed.

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

        --hcp_suffix (str, default ''):
            Specifies a suffix to the session id if multiple variants are run,
            empty otherwise.

        --logfolder (str, default ''):
            The path to the folder where logs are to be stored,
            if other than default.

        --hcp_tica_studyfolder (str, default ''):
            Overwrite the automatic QuNex's setup of the study folder, mainly
            useful for REUSE mode and advanced users.

        --hcp_tica_bolds (str, default ''):
            A comma separated list of fmri run names. Set to all session BOLDs
            by default.

        --hcp_tica_outfmriname (str, default 'rfMRI_REST'):
            Name to use for tICA pipeline outputs.

        --hcp_tica_surfregname (str, default ''):
            The registration string corresponding to the input files.

        --hcp_icafix_highpass (str, default detailed below):
            Value for the highpass filter, [0] for multi-run HCP ICAFix and
            [2000] for single-run HCP ICAFix.

        --hcp_tica_procstring (str, default '_Atlas_<hcp_tica_surfregname>_hp<hcp_icafix_highpass>_clean'):
            File name component representing the preprocessing already done,
            e.g. '_Atlas_MSMAll_hp0_clean'.

        --hcp_outgroupname (str, default ''):
            Name to use for the group output folder.

        --hcp_bold_res (str, default '2'):
            Resolution of data.

        --hcp_tica_timepoints (str, default ''):
            Output spectra size for sICA individual projection,
            RunsXNumTimePoints, like '4800'.

        --hcp_tica_num_wishart (str, default ''):
            How many wisharts to use in icaDim.

        --hcp_lowresmesh (str, default '32'):
            Mesh resolution.

        --hcp_tica_mrfix_concat_name (str, default ''):
            If multi-run FIX was used, you must specify the concat name
            with this option.

        --hcp_tica_icamode (str, default 'NEW'):
            Whether to use parts of a previous tICA run (for instance, if this
            group has too few subjects to simply estimate a new tICA). Defaults
            to NEW, all other modes require specifying the
            `hcp_tica_precomputed_*` parameters. Value must be one of:

            - 'NEW'             ... estimate a new sICA and a new tICA,
            - 'REUSE_SICA_ONLY' ... reuse an existing sICA and estimate a new
              tICA,
            - 'INITIALIZE_TICA' ... reuse an existing sICA and use an
              existing tICA to start the estimation,
            - 'REUSE_TICA'      ... reuse an existing sICA and an existing tICA.

        --hcp_tica_precomputed_clean_folder (str, default ''):
            Group folder containing an existing tICA cleanup to make use
            of for REUSE or INITIALIZE modes. It cannot be the group folder
            of the run itself, which the results are written into, when a
            step of the run writes into it (in REUSE_TICA mode indProjSICA,
            ConcatGroupSICA and ComputeGroupTICA do).

        --hcp_tica_precomputed_fmri_name (str, default ''):
            The output fMRI name used in the previously computed tICA.

        --hcp_tica_precomputed_group_name (str, default ''):
            The group name used during the previously computed tICA.

        --hcp_tica_extra_output_suffix (str, default ''):
            Add something extra to most output filenames, for collision
            avoidance.

        --hcp_tica_pca_out_dim (str, default ''):
            Override number of PCA components to use for group sICA.

        --hcp_tica_pca_internal_dim (str, default ''):
            Override internal MIGP dimensionality.

        --hcp_tica_migp_resume (str, default 'YES'):
            Resume from a previous interrupted MIGP run, if present.

        --hcp_tica_sicadim_iters (int, default 100):
            Number of iterations or mode for estimating sICA dimensionality.

        --hcp_tica_sicadim_override (str, default ''):
            Use this dimensionality instead of icaDim's estimate.

        --hcp_low_sica_dims (str, default '7@8@9@10@11@12@13@14@15@16@17@18@19@20@21'):
            The low sICA dimensionalities to use for determining weighting for
            individual projection.

        --hcp_tica_reclean_mode (str, default ''):
            Whether the data should use ReCleanSignal.txt for DVARS.

        --hcp_tica_starting_step (str, default ''):
            What step to start processing at, one of:

            - 'MIGP',
            - 'GroupSICA',
            - 'indProjSICA',
            - 'ConcatGroupSICA',
            - 'ComputeGroupTICA',
            - 'indProjTICA',
            - 'ComputeTICAFeatures',
            - 'ClassifyTICA',
            - 'CleanData'.

        --hcp_tica_stop_after_step (str, default 'ComputeTICAFeatures'):
            What step to stop processing after, same valid values as for
            hcp_tica_starting_step.

        --hcp_tica_remove_manual_components (str, default ''):
            Text file containing the component numbers to be removed by
            cleanup, separated by spaces, requires either:
            --hcp_tica_icamode=REUSE_TICA or
            --hcp_tica_starting_step=CleanData.

        --hcp_tica_fix_legacy_bias (str, default 'NO'):
            Whether the input data used the legacy bias correction, YES or NO.

        --hcp_parallel_limit (str, default ''):
            How many subjects to do in parallel (local, not
            cluster-distributed) during individual projection.

        --hcp_tica_config_out (flag, optional):
            A flag that determines whether to generate config file for rerunning
            with similar settings, or for reusing these results for future
            cleaning. Not set by default.

        --hcp_tica_average_dataset (str, default ''):
            An average dataset to use in place of the study's own: the folder
            that holds its MNINonLinear, made with the same --hcp_outgroupname
            (hcp_make_average_dataset makes it in
            <sessionsfolder>/average_dataset/<hcp_outgroupname>/<hcp_outgroupname>).
            It is linked in as the group folder, so the results are written
            into it. When a step of the run reads it (ComputeTICAFeatures,
            which REUSE_TICA skips), it has to hold
            MNINonLinear/<hcp_outgroupname>_Averagewmparc.nii.gz. A
            multi-session run without it uses the average dataset already in
            its group folder, else the study's own (see Output files); set it
            to use the average dataset of another study.

        --hcp_tica_extract_fmri_name_list (str, default ''):
            A comma separated list of list of fMRI run names to concatenate into
            the --hcp_tica_extract_fmri_out output after tICA cleanup.

        --hcp_tica_extract_fmri_out (str, default ''):
            fMRI name for concatenated extracted runs, requires
            --hcp_tica_extract_fmri_name_list.

        --hcp_matlab_mode (str, default default detailed below):
            Specifies the Matlab version, can be 'interpreted', 'compiled' or
            'octave'. Inside the container 'compiled' will be used, outside
            'interpreted' is the default.

        --hcp_longitudinal_template (str, default 'base'):
            Name of the longitudinal template.

        --longitudinal:
            Set this flag if you are running the longitudinal variant of this
            command.

        --hcp_tica_longitudinal_extract_all (str, default ''):
            Extract all runs specified in hcp_tica_bolds, with output name
            matching the one from hcp_tica_mrfix_concat_name.

    Output files:
        The results of each session are written into the session's own
        folder, and those of the group into the group folder:

        - a single session: <hcp_outgroupname> in the session's hcp folder,
        - several sessions:
          <sessionsfolder>/<hcp_outgroupname>/<hcp_outgroupname>, in the
          folder the sessions are linked into. It is a link to the average
          dataset hcp_make_average_dataset made,
          <sessionsfolder>/average_dataset/<hcp_outgroupname>/<hcp_outgroupname>,
          unless --hcp_tica_average_dataset names another, or the group
          folder already holds an average dataset: a link an earlier run
          made to a named dataset, or a folder from an older QuNex layout,
          is used as it is. To use the study's own average dataset again,
          remove that link or name the dataset with
          --hcp_tica_average_dataset. A run none of whose steps reads an
          average dataset needs none, and without one its group folder is
          its own,
        - longitudinal:
          <studyfolder>/subjects/<hcp_longitudinal_subject>/<hcp_outgroupname>.
          The link to <sessionsfolder>/average_dataset/<hcp_outgroupname>
          that earlier versions made there is replaced by this folder.

    Notes:
        The HCP Temporal ICA Pipeline needs to be executed in two steps, the
        first step runs the following steps:

        -  ``MIGP``,
        -  ``GroupSICA``,
        -  ``indProjSICA``,
        -  ``ConcatGroupSICA``,
        -  ``ComputeGroupTICA``,
        -  ``indProjTICA``,
        -  ``ComputeTICAFeatures``.

        Since automatic classification is not yet supported, users need to
        classify the components manually and then rerun temporal ICA from
        CleanData step onwards. This is the reason that the
        ``hcp_tica_stop_after_step`` is by default set to
        ``ComputeTICAFeatures``. After the manual classification both
        ``hcp_tica_starting_step`` and ``hcp_tica_stop_after_step`` need to be
        set to ``CleanData``.

        In practice this means that after the HCP Temporal ICA Pipeline
        requirements have been satisfied (you need to run the HCP Minimal
        Preprocessing Pipeline,
        ```hcp_icafix`` <../../api/gmri/hcp_icafix.rst>`__,
        ```hcp_msmall`` <../../api/gmri/hcp_msmall.rst>`__ and
        ```hcp_make_average_dataset`` <../../api/gmri/hcp_make_average_dataset.rst>`__)
        you can run the first processing part, for example:

        .. code:: bash

           qunex hcp_temporal_ica \\
               --studyfolder="<path_to_study_folder>" \\
               --batchfile="<path_to_study_folder>/processing/batch.txt" \\
               --hcp_tica_bolds="fMRI_CONCAT_ALL" \\
               --hcp_tica_outfmriname="fMRI_CONCAT_ALL" \\
               --hcp_tica_mrfix_concat_name="fMRI_CONCAT_ALL" \\
               --hcp_tica_surfregname="MSMAll" \\
               --hcp_icafix_highpass="0" \\
               --hcp_outgroupname="hcp_group" \\
               --hcp_tica_timepoints=<read from post_fix logs> \\
               --hcp_tica_num_wishart="6" \\
               --hcp_parallel_limit="4"

        The ``hcp_tica_timepoints`` parameter value can be found inside the
        ``hcp post_fix`` logs under the label ``NumTimePoints``. If your study
        has many sessions you also need to set the ``hcp_parallel_limit`` to
        prevent too many sessions from processing in parallel. If you do not
        limit this, your system will most likely run out of memory. Once this
        part is done (note that this can take a couple of days with larger
        studies), the command will store the components in
        ``<path_to_study_folder>/sessions/hcp_group/hcp_group/MNINonLinear/Results/fMRI_CONCAT_ALL/tICA_d<N>``
        where ``<N>`` denotes the number of temporal ICA components. To inspect
        the components you can create a ``wb_command`` scene file:

        .. code:: bash

           GroupAverageName='hcp_group'
           tICADim=<N>
           TemplateFolder="${HCPPIPEDIR}/global/templates/tICA"
           ResultsFolder="<path_to_study_folder>/sessions/hcp_group/hcp_group/MNINonLinear/Results/fMRI_CONCAT_ALL/tICA_d<N>"
           TemplateComponentScene="${TemplateFolder}/tICA.scene"
           ResultComponentSceneFile="${ResultsFolder}/tICA_hcp_group.scene"
           ResultComponentSceneFileFinal="${ResultsFolder}/tICA_hcp_group_final.scene"
           cp ${TemplateComponentScene} ${ResultComponentSceneFile}
           cat "${TemplateComponentScene}" | sed s/ExampleGroupAverageName/${GroupAverageName}/g | sed s/ExampleDim/${tICADim}/g >| "${ResultComponentSceneFile}"

        Your scene file called tICA_hcp_group.scene will be created in
        ``<path_to_study_folder>/sessions/hcp_group/hcp_group/MNINonLinear/Results/fMRI_CONCAT_ALL/tICA_d<N>``.
        You can then zip the scene file in order to download it and explore it
        with Workbench on your computer:

        .. code:: bash

           cd ${ResultsFolder}
           wb_command -zip-scene-file \\
               tICA_hcp_group.scene \\
               tICA_hcp_group_fMRI_CONCAT_ALL \\
               -skip-missing \\
               tICA_hcp_group_fMRI_CONCAT_ALL.zip

        MATLAB large variable error:
            If receiving an error in MATLAB saying that a variable was not saved
            because it is larger than 2GB, you need to set the default saving format
            in MATLAB, to do this run MATLAB and execute:

            .. code:: matlab

               s = settings();
               s.matlab.general.matfile.SaveFormat.PersonalValue = 'v7.3';

        Mapping of QuNex parameters onto HCP temporal ICA parameters:
            Below is a detailed specification about how QuNex parameters are
            mapped onto the HCP temporal ICA parameters.

            ===================================== ===============================
            QuNex parameter                       HCP temporal ICA parameter
            ===================================== ===============================
            ``hcp_tica_bolds``                    ``fmri-names``
            ``hcp_tica_outfmriname``              ``output-fmri-name``
            ``hcp_tica_surfregname``              ``surf-reg-name``
            ``hcp_tica_procstring``               ``proc-string``
            ``hcp_outgroupname``                  ``out-group-name``
            ``hcp_bold_res``                      ``fmri-resolution``
            ``hcp_tica_timepoints``               ``session-expected-timepoints``
            ``hcp_tica_num_wishart``              ``num-wishart``
            ``hcp_lowresmesh``                    ``low-res``
            ``hcp_tica_mrfix_concat_name``        ``mrfix-concat-name``
            ``hcp_tica_icamode``                  ``ica-mode``
            ``hcp_tica_precomputed_clean_folder`` ``precomputed-clean-folder``
            ``hcp_tica_precomputed_fmri_name``    ``precomputed-clean-fmri-name``
            ``hcp_tica_precomputed_group_name``   ``precomputed-group-name``
            ``hcp_tica_extra_output_suffix``      ``extra-output-suffix``
            ``hcp_tica_pca_out_dim``              ``pca-out-dim``
            ``hcp_tica_pca_internal_dim``         ``pca-internal-dim``
            ``hcp_tica_migp_resume``              ``migp-resume``
            ``hcp_tica_sicadim_iters``            ``sicadim-iters``
            ``hcp_tica_sicadim_override``         ``sicadim-override``
            ``hcp_low_sica_dims``                 ``low-sica-dims``
            ``hcp_tica_reclean_mode``             ``reclean-mode``
            ``hcp_tica_starting_step``            ``starting-step``
            ``hcp_tica_stop_after_step``          ``stop-after-step``
            ``hcp_tica_remove_manual_components`` ``manual-components-to-remove``
            ``hcp_tica_fix_legacy_bias``          ``fix-legacy-bias``
            ``hcp_parallel_limit``                ``parallel-limit``
            ``hcp_tica_config_out``               ``config-out``
            ``hcp_tica_extract_fmri_name_list``   ``extract-fmri-name-list``
            ``hcp_tica_extract_fmri_out``         ``extract-fmri-out``
            ``hcp_matlab_mode``                   ``matlab-run-mode``
            ``longitudinal``                      ``is-longitudinal``
            ``hcp_longitudinal_template``         ``longitudinal-template``
            ``hcp_tica_longitudinal_extract_all`` ``longitudinal-extract-all``
            ===================================== ===============================


    Examples:
        Example run::

            qunex hcp_temporal_ica \\
                --studyfolder="<path_to_study_folder>" \\
                --batchfile="<path_to_study_folder>/processing/batch.txt" \\
                --hcp_tica_bolds="fMRI_CONCAT_ALL" \\
                --hcp_tica_outfmriname="fMRI_CONCAT_ALL" \\
                --hcp_tica_mrfix_concat_name="fMRI_CONCAT_ALL" \\
                --hcp_tica_surfregname="MSMAll" \\
                --hcp_icafix_highpass="0" \\
                --hcp_outgroupname="hcp_group" \\
                --hcp_tica_timepoints="<value can be found in hcp_post_fix logs>" \\
                --hcp_tica_num_wishart="6" \\
                --hcp_matlab_mode="interpreted"

    """
    sessionid_list = sessions.get_list_by_key("id", sep=",")
    log = SessionLog({"id": sessionid_list}, options, "HCP temporal ICA Pipeline", label="Session ids")

    run = True
    report = "Error"

    try:
        # if longitudinal is set, session list needs to be provided
        if options["longitudinal"]:
            session_list = ""
            if not options["hcp_longitudinal_sessions"]:
                log.error("hcp_longitudinal_sessions is not provided!")
                run = False
            else:
                session_list = options["hcp_longitudinal_sessions"].replace(",", "@")

        # if sessions is not a batch file skip batch file validity checks
        elif ("sessions" in options and os.path.exists(options["sessions"])) or (
            "batchfile" in options and os.path.exists(options["batchfile"])
        ):
            do_hcp_options_check(options, "hcp_temporal_ica")

            # session_list
            session_list = ""

            # check sessions
            for session in sessions:
                if "hcp" not in session:
                    log.error(f"There is no hcp info for session {session['id']} in batch.txt")
                    run = False

                # session_list
                if session_list == "":
                    session_list = session["id"] + options["hcp_suffix"]
                else:
                    session_list = (
                        session_list + "@" + session["id"] + options["hcp_suffix"]
                    )
        else:
            # session_list
            session_list = ""

            for session in sessions:
                # session_list
                if session_list == "":
                    session_list = session["id"] + options["hcp_suffix"]
                else:
                    session_list = (
                        session_list + "@" + session["id"] + options["hcp_suffix"]
                    )

        # mandatory parameters
        # hcp_tica_bolds
        fmri_names = ""
        if options["hcp_tica_bolds"] is None:
            log.error("hcp_tica_bolds is not provided!")
            run = False
        else:
            # defined bolds
            fmri_names = options["hcp_tica_bolds"].replace(",", "@")

        # hcp_tica_outfmriname
        out_fmri_name = ""
        if options["hcp_tica_outfmriname"] is None:
            log.error("hcp_tica_outfmriname is not provided!")
            run = False
        else:
            out_fmri_name = options["hcp_tica_outfmriname"]

        # hcp_tica_surfregname
        surfregname = ""
        if options["hcp_tica_surfregname"] is None:
            log.error("hcp_tica_surfregname is not provided!")
            run = False
        else:
            surfregname = options["hcp_tica_surfregname"]

        # hcp_icafix_highpass
        icafix_highpass = ""
        if options["hcp_icafix_highpass"] is None:
            log.error("hcp_icafix_highpass is not provided!")
            run = False
        else:
            icafix_highpass = options["hcp_icafix_highpass"]

        # hcp_tica_procstring
        if options["hcp_tica_procstring"] is None:
            proc_string = ""
            if "hcp_cifti_tail" in options:
                proc_string = "%s_" % "_Atlas"

            proc_string = "%s%s_hp%s_clean" % (
                proc_string,
                surfregname,
                icafix_highpass,
            )
        else:
            proc_string = options["hcp_tica_procstring"]

        # hcp_outgroupname
        outgroupname = ""
        if options["hcp_outgroupname"] is None:
            log.error("hcp_outgroupname is not provided!")
            run = False
        else:
            outgroupname = options["hcp_outgroupname"]

        # hcp_tica_timepoints
        timepoints = ""
        if options["hcp_tica_timepoints"] is None:
            log.error("hcp_tica_timepoints is not provided!")
            run = False
        else:
            timepoints = options["hcp_tica_timepoints"]

        # hcp_tica_num_wishart
        num_wishart = ""
        if options["hcp_tica_num_wishart"] is None:
            log.error("hcp_tica_num_wishart is not provided!")
            run = False
        else:
            num_wishart = options["hcp_tica_num_wishart"]

        # the average dataset linked in as the group folder: the one named,
        # else in a multi-session run the one hcp_make_average_dataset made
        average_dataset = options["hcp_tica_average_dataset"]

        # if using a manual study_dir bypass all validity checks and preparation
        if options["hcp_tica_studyfolder"]:
            study_dir = options["hcp_tica_studyfolder"]
        else:
            study_dir = ""

            # longitudinal
            if options["longitudinal"]:
                if not options["hcp_longitudinal_subject"]:
                    log.error("hcp_longitudinal_subject is a mandatory parameter for the longitudinal mode of temporal ICA!")
                    run = False
                else:
                    # set study dir
                    study_dir = os.path.join(
                        gf.subjects_folder(options["studyfolder"]),
                        options["hcp_longitudinal_subject"],
                    )

                    # create folder
                    tf.make_folder(log, options, study_dir)

                    # the subject's own group folder: a longitudinal run is
                    # REUSE_TICA, which reads no average dataset. Earlier
                    # versions linked the average dataset's study folder, which
                    # every subject shares, in its place
                    earlier = [
                        average_dataset_study(folder, outgroupname)
                        for folder in (
                            options["sessionsfolder"],
                            os.path.join(options["studyfolder"], "sessions"),
                        )
                    ]
                    if not tf.make_group_folder(log, options, study_dir, outgroupname, average_dataset, earlier):
                        run = False

            # single session
            elif len(sessions) == 1:
                # get session info
                study_dir = sessions[0]["hcp"]
                if not tf.make_group_folder(log, options, study_dir, outgroupname, average_dataset):
                    run = False

            # multi session, in a group folder named by hcp_outgroupname: without
            # one the sessions would be linked onto the session folders
            elif outgroupname:
                # set study dir
                study_dir = os.path.join(options["sessionsfolder"], outgroupname)

                # create folder
                tf.make_folder(log, options, study_dir)

                # link sessions
                for session in sessions:
                    # prepare folders
                    session_name = session["id"] + options["hcp_suffix"]
                    source_dir = os.path.join(session["hcp"], session_name)
                    target_dir = os.path.join(study_dir, session_name)

                    # link
                    if not tf.link_folder(log, options, source_dir, target_dir):
                        run = False

                # the group folder is the average dataset tICAPipeline.sh
                # reads: one already in place is used as it is, else the one
                # hcp_make_average_dataset made is linked in. A run none of
                # whose steps reads it needs none, its group folder is its own
                if average_dataset is None:
                    group_dir = os.path.join(study_dir, outgroupname)
                    made = average_dataset_folder(options["sessionsfolder"], outgroupname)
                    if os.path.exists(tf.average_wmparc(group_dir, outgroupname)):
                        if os.path.realpath(group_dir) != os.path.realpath(made):
                            log.detail(f"{group_dir} holds an average dataset, used as it is")
                            if os.path.islink(group_dir):
                                log.detail(
                                    f"to use {made} instead, remove the link "
                                    "or name it with --hcp_tica_average_dataset"
                                )
                    elif os.path.exists(tf.average_wmparc(made, outgroupname)):
                        average_dataset = made
                    elif not tf.reads_average_wmparc(options):
                        if not tf.make_group_folder(log, options, study_dir, outgroupname, None):
                            run = False
                    else:
                        log.error(f"{tf.average_wmparc(made, outgroupname)} does not exist!")
                        log.error(
                            "You need to run hcp_make_average_dataset with "
                            f"--hcp_outgroupname={outgroupname} before running "
                            "hcp_temporal_ica, or name an average dataset with "
                            "--hcp_tica_average_dataset!"
                        )
                        run = False

            # a named average dataset is linked in as the group folder
            named = options["hcp_tica_average_dataset"]
            if named is not None and outgroupname and not tf.is_average_dataset(log, options, named, outgroupname):
                run = False

        # the group folder cannot be the precomputed tICA: a REUSE or
        # INITIALIZE mode reads that one and writes into the group folder, and
        # the average dataset of a group is also the folder of its results.
        # The group folder is compared by its path too, as the link that
        # makes it the average dataset may not be there yet. A run none of
        # whose steps writes into the group folder is not refused
        precomputed = options["hcp_tica_precomputed_clean_folder"]
        if study_dir and outgroupname and precomputed is not None and tf.writes_group_folder(options):
            group_dir = os.path.join(study_dir, outgroupname)
            written = os.path.realpath(average_dataset or group_dir)
            if os.path.realpath(precomputed) == written or os.path.abspath(precomputed) == os.path.abspath(group_dir):
                log.error(f"The group folder {group_dir} is the precomputed tICA {precomputed}, the run would write over it!")
                log.error("Use another --hcp_outgroupname, or another average dataset with --hcp_tica_average_dataset!")
                run = False

        # matlab run mode, compiled=0, interpreted=1, octave=2
        matlabrunmode = None
        if options["hcp_matlab_mode"] is None:
            if "FSL_FIX_MATLAB_MODE" not in os.environ:
                log.error("hcp_matlab_mode not set and FSL_FIX_MATLAB_MODE not set in the environment, set either one!\n")
                run = False
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
                log.error("unknown setting for hcp_matlab_mode, use compiled, interpreted or octave!\n")
                run = False

        # build the command
        if run:
            comm = (
                '%(script)s \
                --study-folder="%(study_dir)s" \
                --session-list="%(session_list)s" \
                --fmri-names="%(fmri_names)s" \
                --output-fmri-name="%(output_fmri_name)s" \
                --surf-reg-name="%(surf_reg_name)s" \
                --fix-high-pass="%(icafix_highpass)s" \
                --proc-string="%(proc_string)s" \
                --out-group-name="%(outgroupname)s" \
                --fmri-resolution="%(fmri_resolution)s" \
                --session-expected-timepoints="%(timepoints)s" \
                --num-wishart="%(num_wishart)s" \
                --low-res="%(low_res)s" \
                --matlab-run-mode="%(matlabrunmode)s" \
                --stop-after-step="%(stopafterstep)s"'
                % {
                    "script": os.path.join(
                        os.environ["HCPPIPEDIR"], "tICA", "tICAPipeline.sh"
                    ),
                    "study_dir": study_dir,
                    "session_list": session_list,
                    "fmri_names": fmri_names,
                    "output_fmri_name": out_fmri_name,
                    "surf_reg_name": surfregname,
                    "icafix_highpass": icafix_highpass,
                    "proc_string": proc_string,
                    "outgroupname": outgroupname,
                    "fmri_resolution": options["hcp_bold_res"],
                    "timepoints": timepoints,
                    "num_wishart": num_wishart,
                    "low_res": options["hcp_lowresmesh"],
                    "matlabrunmode": matlabrunmode,
                    "stopafterstep": options["hcp_tica_stop_after_step"],
                }
            )

            # -- Optional parameters
            # hcp_tica_mrfix_concat_name
            if options["hcp_tica_mrfix_concat_name"] is not None:
                comm += (
                    '                    --mrfix-concat-name="%s"'
                    % options["hcp_tica_mrfix_concat_name"]
                )

            # hcp_tica_icamode
            if options["hcp_tica_icamode"] is not None:
                comm += (
                    '                    --ica-mode="%s"' % options["hcp_tica_icamode"]
                )

            # hcp_tica_precomputed_clean_folder
            if options["hcp_tica_precomputed_clean_folder"] is not None:
                comm += (
                    '                    --precomputed-clean-folder="%s"'
                    % options["hcp_tica_precomputed_clean_folder"]
                )

            # hcp_tica_precomputed_fmri_name
            if options["hcp_tica_precomputed_fmri_name"] is not None:
                comm += (
                    '                    --precomputed-clean-fmri-name="%s"'
                    % options["hcp_tica_precomputed_fmri_name"]
                )

            # hcp_tica_precomputed_group_name
            if options["hcp_tica_precomputed_group_name"] is not None:
                comm += (
                    '                    --precomputed-group-name="%s"'
                    % options["hcp_tica_precomputed_group_name"]
                )

            # hcp_tica_extra_output_suffix
            if options["hcp_tica_extra_output_suffix"] is not None:
                comm += (
                    '                    --extra-output-suffix="%s"'
                    % options["hcp_tica_extra_output_suffix"]
                )

            # hcp_tica_pca_out_dim
            if options["hcp_tica_pca_out_dim"] is not None:
                comm += (
                    '                    --pca-out-dim="%s"'
                    % options["hcp_tica_pca_out_dim"]
                )

            # hcp_tica_pca_internal_dim
            if options["hcp_tica_pca_internal_dim"] is not None:
                comm += (
                    '                    --pca-internal-dim="%s"'
                    % options["hcp_tica_pca_internal_dim"]
                )

            # hcp_tica_migp_resume
            if options["hcp_tica_migp_resume"] is not None:
                comm += (
                    '                    --migp-resume="%s"'
                    % options["hcp_tica_migp_resume"]
                )

            # hcp_tica_sicadim_iters
            if options["hcp_tica_sicadim_iters"] is not None:
                comm += (
                    '                    --sicadim-iters="%s"'
                    % options["hcp_tica_sicadim_iters"]
                )

            # hcp_tica_sicadim_override
            if options["hcp_tica_sicadim_override"] is not None:
                comm += (
                    '                    --sicadim-override="%s"'
                    % options["hcp_tica_sicadim_override"]
                )

            # hcp_low_sica_dims
            if options["hcp_low_sica_dims"] is not None:
                comm += (
                    '                    --low-sica-dims="%s"'
                    % options["hcp_low_sica_dims"]
                )

            # hcp_tica_reclean_mode
            if options["hcp_tica_reclean_mode"] is not None:
                comm += (
                    '                    --reclean-mode="%s"'
                    % options["hcp_tica_reclean_mode"]
                )

            # hcp_tica_starting_step
            if options["hcp_tica_starting_step"] is not None:
                comm += (
                    '                    --starting-step="%s"'
                    % options["hcp_tica_starting_step"]
                )

            # hcp_tica_remove_manual_components
            if options["hcp_tica_remove_manual_components"] is not None:
                comm += (
                    '                    --manual-components-to-remove="%s"'
                    % options["hcp_tica_remove_manual_components"]
                )

            # hcp_tica_fix_legacy_bias
            if options["hcp_tica_fix_legacy_bias"] is not None:
                comm += (
                    '                    --fix-legacy-bias="%s"'
                    % options["hcp_tica_fix_legacy_bias"]
                )

            # hcp_parallel_limit
            if options["hcp_parallel_limit"] is not None:
                comm += (
                    '                    --parallel-limit="%s"'
                    % options["hcp_parallel_limit"]
                )

            # hcp_tica_config_out
            if options["hcp_tica_config_out"]:
                comm += "                    --config-out"

            # hcp_tica_extract_fmri_name_list
            if options["hcp_tica_extract_fmri_name_list"]:
                comm += f'                    --extract-fmri-name-list="{options["hcp_tica_extract_fmri_name_list"].replace(",", "@")}"'

            # hcp_tica_extract_fmri_out
            if options["hcp_tica_extract_fmri_out"]:
                comm += f'                    --extract-fmri-out="{options["hcp_tica_extract_fmri_out"]}"'

            # longitudinal
            if options["longitudinal"]:
                comm += '                --is-longitudinal="TRUE"'
                comm += (
                    '                --longitudinal-template="'
                    + options["hcp_longitudinal_template"]
                    + '"'
                )
                comm += (
                    '                --longitudinal-subject="'
                    + options["hcp_longitudinal_subject"]
                    + '"'
                )
                if options["hcp_tica_longitudinal_extract_all"]:
                    comm += '                --longitudinal-extract-all="TRUE"'

                if not options["hcp_tica_icamode"]:
                    comm += '                    --ica-mode="REUSE_TICA"'
                elif options["hcp_tica_icamode"] != "REUSE_TICA":
                    log.error("Longitudinal processing is set, but hcp_tica_icamode is not set to REUSE_TICA, this will not work!")
                    run = False

            # the average dataset is linked in as the group folder, which takes
            # a study dir and a group name, only once every check has passed:
            # a later run uses a group folder in place as it is
            if run and study_dir and outgroupname and average_dataset is not None:
                group_dir = os.path.join(study_dir, outgroupname)
                if not tf.link_folder(log, options, average_dataset, group_dir):
                    run = False

            # -- Report command
            if run:
                log.rule(before=1, after=1)
                log.raw("Running HCP Pipelines command via QuNex:\n\n")
                log.raw(comm.replace("                --", "\n    --"))
                log.rule(after=1)

        # -- Run
        if run:
            if options["run"] == "run":
                logtags = [options["logtag"]]
                if options["longitudinal"]:
                    logtags.append("long")

                _, report, failed = pc.run_external_for_file(
                    None,
                    comm,
                    "Running HCP temporal ICA",
                    overwrite=True,
                    thread=outgroupname,
                    remove=options["log"] == "remove",
                    task=options["command_ran"],
                    logfolder=options["comlogs"],
                    logtags=logtags,
                    full_test=None,
                    shell=True,
                    _log=log,
                )

            # just checking, there is no test file to check against
            else:
                log.step("HCP temporal ICA can be run")
                report = "HCP temporal ICA can be run"
                failed = 0

        else:
            log.step("Session cannot be processed.")
            report = "HCP temporal ICA cannot be run"
            failed = 1

    except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
        log.raw(str(errormessage))
        failed = 1
    except Exception:
        log.unknown_error()
        failed = 1

    log.close(pipeline="HCP temporal ICA Preprocessing")

    return log.result((sessionid_list, report, failed))
