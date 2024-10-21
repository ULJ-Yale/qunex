#!/bin/bash

# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

SupportedQC="rawNII, T1w, T2w, myelin, BOLD, DWI, general, eddyQC"

usage() {
    cat << EOF
``run_qc``

This function runs the QC preprocessing for a specified modality / processing
step.

Currently Supported: ${SupportedQC}

This function is compatible with both legacy data [without T2w scans] and
HCP-compliant data [with T2w scans and DWI].

Parameters:
    --sessionsfolder (str):
        Path to study folder that contains sessions.

    --sessions (str):
        Comma separated list of sessions to run.

    --modality (str):
        Specify the modality to perform QC on.
        Supported: 'rawNII', 'T1w', 'T2w', 'myelin', 'BOLD', 'DWI', 'general',
        'eddyQC'.

        Note: If selecting 'rawNII' this function performs QC for raw NIFTI
        images in <sessions_folder>/<case>/nii It requires NIFTI images in
        <sessions_folder>/<case>/nii/ after either BIDS import of DICOM
        organization.

        Session-specific output: <sessions_folder>/<case>/nii/slicesdir

        Uses FSL's 'slicesdir' script to generate PNGs and an HTML file in the
        above directory.

        Note: If using 'general' modality, then visualization is
        $TOOLS/$QUNEXREPO/qx_library/data/scenes/qc/template_general_qc.wb.scene

        This will work on any input file within the
        session-specific data hierarchy.

    --datapath (str):
        Required ---> Specify path for input path relative to the
        <sessions_folder> if scene is 'general'.

    --datafile (str):
        Required ---> Specify input data file name if scene is 'general'.

    --batchfile (str):
        Absolute path to local batch file with pre-configured processing
        parameters.

        Note: It can be used in combination with --sessions to select only
        specific cases to work on from the batch file. If --sessions is
        omitted, then all cases from the batch file are processed. It can also
        used in combination with --bolddata to select only specific BOLD runs
        to work on from the batch file. If --bolddata is omitted (see below),
        all BOLD runs in the batch file will be processed.

    --overwrite (str, default 'no'):
        Whether to overwrite existing data (yes) or not (no). Note that
        previous data is deleted before the run, so in the case of a failed
        command run, previous results are lost.

    --hcp_suffix (str, default ''):
        Allows user to specify session id suffix if running HCP preprocessing
        variants. E.g. ~/hcp/sub001 & ~/hcp/sub001-run2 ---> Here 'run2' would be
        specified as --hcp_suffix='-run2'

    --scenetemplatefolder (str, default '${TOOLS}/${QUNEXREPO}/qx_library/data/scenes/qc'):
        Specify the absolute path name of the template folder.

        Note: relevant scene template data has to be in the same folder as the
        template scenes.

    --outpath (str, default '<path_to_study_sessions_folder>/QC/<input_modality_for_qc>'):
        Specify the absolute path name of the QC folder you wish the individual
        images and scenes saved to. If --outpath is unspecified then files are
        saved to: '<path_to_study_sessions_folder>/QC/<input_modality_for_qc>'.

    --scenezip (str, default 'yes'):
        Yes or no. Generates a ZIP file with the scene and all relevant files
        for Connectome Workbench visualization.
        Note: If scene zip set to yes, then relevant scene files will be zipped
        with an updated relative base folder.
        All paths will be relative to this base --->
        <path_to_study_sessions_folder>/<session_id>/hcp/<session_id>
        The scene zip file will be saved to:
        <path_for_output_file>/<session_id>.<input_modality_for_qc>.QC.wb.zip

    --userscenefile (str, default ''):
        User-specified scene file name. --modality info is still required to
        ensure correct run. Relevant data needs to be provided.

    --userscenepath (str, default ''):
        Path for user-specified scene and relevant data in the same location.
        --modality info is still required to ensure correct run.

    --timestamp (str, default detailed below):
        Allows user to specify unique time stamp or to parse a time stamp from
        QuNex bash wrapper. Current time is used if no value is provided.

    --suffix (str, default '<session_id>_<timestamp>'):
        Allows user to specify unique suffix or to parse a time stamp from QuNex
        bash wrapper.

    --dwipath (str):
        Specify the input path for the DWI data (may differ across studies; e.g.
        'Diffusion' or 'Diffusion' or 'Diffusion_DWI_dir74_AP_b1000b2500').

    --dwidata (str):
        Specify the file name for DWI data (may differ across studies; e.g.
        'data' or 'DWI_dir74_AP_b1000b2500_data').

    --dtifitqc (str):
        Specify if dtifit visual QC should be completed (e.g. 'yes' or 'no').

    --bedpostxqc (str):
        Specify if BedpostX visual QC should be completed (e.g. 'yes' or 'no').

    --eddyqcstats (str):
        Specify if EDDY QC stats should be linked into QC folder and motion
        report generated (e.g. 'yes' or 'no').

    --boldprefix (str):
        Specify the prefix file name for BOLD dtseries data (may differ across
        studies depending on processing; e.g. 'BOLD' or 'TASK' or 'REST').
        Note: If unspecified then QC script will assume that folder names
        containing processed BOLDs are named numerically only (e.g. 1, 2, 3).

    --boldsuffix (str):
        Specify the suffix file name for BOLD dtseries data (may differ across
        studies depending on processing; e.g. 'Atlas' or 'MSMAll').

    --skipframes (str):
        Specify the number of initial frames you wish to exclude from the BOLD
        QC calculation.

    --snronly (str, default 'no'):
        Specify if you wish to compute only SNR BOLD QC calculation and skip
        image generation ('yes'/'no').

    --bolddata (str):
        Specify BOLD data numbers separated by comma or pipe. E.g.
        --bolddata='1,2,3,4,5'. This flag is interchangeable with --bolds or
        --boldruns to allow more redundancy in specification.

        Note: If --bolddata is unspecified, a batch file must be provided in
        --batchfile or an error will be reported. If --bolddata is empty and
        --batchfile is provided, by default QuNex will use the information in
        the batch file to identify all BOLDS to process.

    --boldfc (str, default ''):
        Specify if you wish to compute BOLD QC for FC-type BOLD results.
        Supported: pscalar or pconn.
        Requires --boldfc='<pconn or pscalar>', --boldfcinput=<image_input>,
        --bolddata or --boldruns or --bolds.

    --boldfcpath (str, default '<study_folder>/sessions/<session_id>/images/functional'):
        Specify path for input FC data.
        Requires --boldfc='<pconn or pscalar>', --boldfcinput=<image_input>,
        --bolddata or --boldruns or --bolds.

    --boldfcinput (str):
        Required. If no --boldfcpath is provided then specify only data input
        name after bold<Number>_ which is searched for in
        '<sessions_folder>/<session_id>/images/functional'.

        pscalar FC
           Atlas_hpss_res-mVWMWB_lpss_CAB-NP-718_r_Fz_GBC.pscalar.nii
        pconn FC
           Atlas_hpss_res-mVWMWB_lpss_CAB-NP-718_r_Fz.pconn.nii

        Requires --boldfc='<pconn or pscalar>', --boldfcinput=<image_input>,
        --bolddata or --boldruns or --bolds.

    --processcustom (str, default 'no'):
        Either 'yes' or 'no'. If set to 'yes' then the script looks into:
        ~/<study_path>/processing/scenes/QC/ for additional custom QC scenes.

        Note: The provided scene has to conform to QuNex QC template
        standards.xw

        See $TOOLS/$QUNEXREPO/qx_library/data/scenes/qc/ for example templates.
        The qc path has to contain relevant files for the provided scene.

    --omitdefaults (str, default 'no'):
        Either 'yes' or 'no'. If set to 'yes' then the script omits defaults.
    
    --sourcefile (str, default 'session_hcp.txt'):
            The name of the source session.txt file.

    --hcp_filename (str):
        Specify how files and folders should be named using HCP processing:

        - 'automated'   ... files should be named using QuNex automated naming
          (e.g. BOLD_1_PA)
        - 'userdefined' ... files should be named using user defined names (e.g.
          rfMRI_REST1_AP)

        Note that the filename to be used has to be provided in the
        session_hcp.txt file or the standard naming will be used. If not
        provided the default 'automated' will be used.

Output files:
    With the exception of rawNII, the function generates 3 types of outputs, which
    are stored within the Study in <path_to_folder_with_sessions>/QC :

    - .scene files that contain all relevant data loadable into Connectome Workbench
    - .png images that contain the output of the referenced scene file.
    - .zip file that contains all relevant files to download and re-generate the
      scene in Connectome Workbench.

    .. note::
       For BOLD data there is also an SNR txt output if specified.

    .. note::
       For raw NIFTI QC outputs are generated in:
       <sessions_folder>/<case>/nii/slicesdir

Notes:
    Raw NIFTI visual QC:
        -  Input: requires NIFTI images in ``<sessionsfolder>/<case>/nii`` after
           either BIDS import of DICOM organization
        -  Session-specific output: ``<sessionsfolder>/<case>/nii/slicesdir``
        -  Uses FSL’s ``slicesdir`` script to generate PNGs and an HTML file in
           the above directory.
        -  This can be invoked via the ``qunex run_qc`` command.

    T1w visual QC:
        -  Input: requires T1w images and hcp_pre_freesurfer-hcp_post_freesurfer
           to have run successfully
        -  Session-specific output: ``/<study>/sessions/<session>/QC/T1w``

           -  T1w.QC.png image files for each session will be located in this
              folder
           -  T1w.QC.wb.scene image files also produced and located in this
              folder

        -  Group outputs of all session files is specified via the optional
           ``--outpath`` flag.
        -  If ``--outpath`` is unspecified then files are saved to:
           ``/<path_to_study_sessions_folder>/QC/<input_modality_for_qc>``
        -  Log Location: logs are created in ``/<study>/sessions/QC/T1w/qclog``

           -  There will be error logs in this folder if QC could not be run
           -  Other errors can be found by looking at the QC images formed

    T2w visual QC:
        -  Input: requires T2w images and hcp_pre_freesurfer-hcp_post_freesurfer
           to have run successfully
        -  Session-specific output: ``/<study>/sessions/<session>/QC/T2w``

           -  T2w.QC.png image files for each session
           -  T2w.QC.wb.scene image files also produced

        -  Group outputs of all session files is specified via the optional
           ``--outpath`` flag.
        -  If ``--outpath`` is unspecified then files are saved to:
           ``/<path_to_study_sessions_folder>/QC/<input_modality_for_qc>``
        -  Log Location: logs are created in ``/<study>/sessions/QC/T2w/qclog``

           -  There will be error logs in this folder if QC could not be run
           -  Other errors will need to be found by looking at the structural
              images

    Myelin map visual QC:
        -  Input: requires BOLD runs and hcp_pre_freesurfer-hcp_fmri_surface to
           have run successfully
        -  Session-specific output: ``/<study>/sessions/<session>/QC/myelin``

           -  This will produce a .myelin.QC.wb.png image and a
              myelin.QC.wb.scene file for each session

        -  Group outputs of all session files is specified via the optional
           ``--outpath`` flag.
        -  If ``--outpath`` is unspecified then files are saved to:
           ``/<path_to_study_sessions_folder>/QC/<input_modality_for_qc>``
        -  Log Location: logs are created in
           ``/<study>/sessions/QC/myelin/qclog``

           -  There will be error logs in this folder if QC could not be run
           -  Other errors will need to be found by looking at the myelin images

    BOLD visual QC:
        -  Input: requires BOLD runs and hcp_pre_freesurfer-hcp_fmri_surface to
           have run successfully
        -  Session-specific output: ``/<study>/sessions/<session>/QC/BOLD``

           -  A .GStimeseries.QC.wb.png image will be produced for each BOLD in
              this folder
           -  A .GSmap.QC.wb.png image will be produced for each BOLD in this
              folder
           -  A QC.wb.scene file will be produced for each BOLD run for each
              session

        -  Group outputs of all session files is specified via the optional
           ``--outpath`` flag.
        -  If ``--outpath`` is unspecified then files are saved to:
           ``/<path_to_study_sessions_folder>/QC/<input_modality_for_qc>``
        -  Log Location: logs are created in ``/<study>/sessions/QC/BOLD/qclog``

           -  There will be error logs in this folder if QC could not be run
           -  Other errors will need to be found by looking at the BOLD images

        -  Note that IF no BOLD ``--bolddata`` is provided, then ``--batchfile``
           must be provided so that the script will look for
           ``session_<pipeline>.txt`` info file to determine which BOLDs to run.
           If neither ``--bolddata`` nor ``--batchfile`` is specified, the
           command will return an error.

    BOLD temporal Signal-to-noise (SNR):
        -  Input: requires BOLD runs and hcp_pre_freesurfer-hcp_fmri_surface to
           have run successfully
        -  Session-specific output: ``/<study>/sessions/<session>/QC/BOLD``

           -  A ``<SNR>`` file will be produced for each BOLD in this folder

        -  Group outputs of all session files is specified via the optional
           ``--outpath`` flag.
        -  If ``--outpath`` is unspecified then files are saved to:
           ``/<path_to_study_sessions_folder>/QC/<input_modality_for_qc>``
        -  Log Location: logs are created in ``/<study>/sessions/QC/BOLD/qclog``

           -  There will be error logs in this folder if QC could not be run
           -  Other errors will need to be found by looking at the BOLD images

        -  Note that IF no BOLD ``--bolddata`` is provided in the flag the
           script will look for ``session_<pipeline>.txt`` info file to
           determine which BOLDs to run
        -  Note that this SNR gets calculated automatically for every BOLD
        -  If you wish to compute SNR only but omit visual QC then use this
           flag:

           -  ``--snronly="yes"``

    BOLD FC QC for scalar and pconn data:
        -  Input: requires BOLD runs and hcp_pre_freesurfer-hcp_fmri_surface to
           have run successfully
        -  Session-specific output: ``/<study>/sessions/<session>/QC/BOLD``

           -  A \*.png image will be produced for each BOLD in this folder
              either for pconn or dscalar

        -  If ``--boldfcpath`` is unspecified then default is:
           ``/<path_to_study_sessions_folder>/sessions/<session>/images/functional``
        -  Log Location: logs are created in ``/<study>/sessions/QC/BOLD/qclog``

           -  There will be error logs in this folder if QC could not be run
           -  Other errors will need to be found by looking at the BOLD images

        -  Note that IF no BOLD ``--bolddata`` is provided in the flag the
           script will look for ``session_<pipeline>.txt`` info file to
           determine which BOLDs to run

    DWI visual and motion QC:
        -  Input: requires hcp_diffusion runs and
           hcp_pre_freesurfer-hcp_post_freesurfer to have run successfully
        -  Session-specific output: ``/<study>/sessions/<session>/QC/DWI``

           -  DWI.QC.png and DWI.QC.wb.scene files
           -  DWI.bedpostx.QC.png and DWI.bedpostx.QC.wb.scene files

        -  Group outputs of all session files is specified via the optional
           ``--outpath`` flag.
        -  If ``--outpath`` is unspecified then files are saved to:
           ``/<path_to_study_sessions_folder>/QC/<input_modality_for_qc>``

           -  DWI.dtifit.QC.png and DWI.dtifit.QC.wb.scene files

        -  Log Location: logs are created in ``/<study>/sessions/QC/DWI/qclog``

           -  There will be error logs in this folder if QC could not be run
           -  Other errors will need to be found by looking at the myelin images

    Running BOLD QC with tag selection:
        run_qc allows for processing BOLD runs directly via numeric selection
        (e.g. 1,2,3,4) or by using the ‘tag’ specification from the ‘batch’
        file. In other words, BOLD runs 1,2 could be tagged as ‘blink’ in the
        following example. This way, the user can filter and select which BOLDs
        to QC flexibly.

Examples:
    Run directly via::

        ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/run_qc.sh \\
            --<parameter1> \\
            --<parameter2> \\
            --<parameter3> ... \\
            --<parameterN>

    NOTE: --scheduler is not available via direct script call.

    Run via::

        qunex run_qc \\
            --<parameter1> \\
            --<parameter2> ... \\
            --<parameterN>

    NOTE: scheduler is available via qunex call.

    --scheduler
        A string for the cluster scheduler (e.g. PBS or SLURM) followed by
        relevant options.

    For SLURM scheduler the string would look like this via the qunex call::

        --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

    Raw NII QC::

        qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --modality='rawNII'

    T1w QC::

        qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --outpath='<path_for_output_file>' \\
            --scenetemplatefolder='<path_for_the_template_folder>' \\
            --modality='T1w' \\
            --overwrite='yes'

    T2w QC::

        qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --outpath='<path_for_output_file>' \\
            --scenetemplatefolder='<path_for_the_template_folder>' \\
            --modality='T2w' \\
            --overwrite='yes'

    Myelin QC::

        qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --outpath='<path_for_output_file>' \\
            --scenetemplatefolder='<path_for_the_template_folder>' \\
            --modality='myelin' \\
            --overwrite='yes'

    DWI QC::

        qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --scenetemplatefolder='<path_for_the_template_folder>' \\
            --modality='DWI' \\
            --outpath='<path_for_output_file>' \\
            --dwidata='<file_name_for_dwi_data>' \\
            --dwipath='<path_for_dwi_data>' \\
            --overwrite='yes'

    BOLD QC (for a specific BOLD run)::

        qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --outpath='<path_for_output_file>' \\
            --scenetemplatefolder='<path_for_the_template_folder>' \\
            --modality='BOLD' \\
            --bolddata='1' \\
            --boldsuffix='Atlas' \\
            --overwrite='yes'

    BOLD QC (search for all available BOLD runs)::

        qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --batchfile='<path_to_batch_file>' \\
            --outpath='<path_for_output_file>' \\
            --scenetemplatefolder='<path_for_the_template_folder>' \\
            --modality='BOLD' \\
            --boldsuffix='Atlas' \\
            --overwrite='yes'

    BOLD temporal SNR::

        qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions="<comma_separated_list_of_cases>" \\
            --outpath='<path_for_output_file>' \\
            --modality='BOLD' \\
            --snronly="yes" \\
            --bolddata='BOLD_#,BOLD_#' \\
            --boldsuffix='Atlas' \\
            --overwrite='no' \\
            --scheduler='<settings for scheduler>'

    BOLD FC QC [pscalar or pconn]::

        qunex run_qc \\
            --overwritestep='yes' \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --modality='BOLD' \\
            --boldfc='<pscalar_or_pconn>' \\
            --boldfcinput='<data_input_for_bold_fc>' \\
            --bolddata='1' \\
            --overwrite='yes'

    DWI visual and motion QC::

        qunex run_qc \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions="<comma_separated_list_of_cases>" \\
            --outpath='<path_for_output_file>' \\
            --templatefolder='<path_for_the_template_folder>' \\
            --modality='DWI' \\
            --dwidata='data' \\
            --dwipath='Diffusion' \\
            --dtifitqc='yes' \\
            --bedpostxqc='yes' \\
            --eddyqcstats='yes' \\
            --overwrite='no' \\
            --scheduler='<settings for scheduler>'

    
    Running BOLD QC with tag selection:
        run_qc call across several sessions using tag selection for all BOLDS::

            qunex run_qc \\
                --sessionsfolder='/gpfs/loomis/pi/n3/Studies/MBLab/HCPDev/OP2/sessions' \\
                --batchfile='/gpfs/loomis/pi/n3/Studies/MBLab/HCPDev/OP2/processing/batch.txt' \\
                --sessions='OP268_07032014,OP269_07032014,OP270_07082014' \\
                --modality='BOLD' \\
                --bolddata="all" \\
                --boldprefix="BOLD" \\
                --boldsuffix="Atlas" \\
                --overwrite='yes'

        run_qc call across several sessions using tag selection for specific BOLDS tagged as 'blink'::

            qunex run_qc --sessionsfolder='/gpfs/loomis/pi/n3/Studies/MBLab/HCPDev/OP2/sessions' \\
                --batchfile='/gpfs/loomis/pi/n3/Studies/MBLab/HCPDev/OP2/processing/batch.txt' \\
                --sessions='OP270_07082014,OP269_07032014' \\
                --modality='BOLD' \\
                --bolddata="blink" \\
                --boldprefix="BOLD" \\
                --boldsuffix="Atlas" \\
                --overwrite='yes'

        run_qc call across several sessions using numeric selection for select BOLDS::

            qunex run_qc \\
                --sessionsfolder='/gpfs/loomis/pi/n3/Studies/MBLab/HCPDev/OP2/sessions' \\
                --batchfile='/gpfs/loomis/pi/n3/Studies/MBLab/HCPDev/OP2/processing/batch.txt' \\
                --sessions='OP270_07082014,OP269_07032014' \\
                --modality='BOLD' \\
                --bolddata="1,6" \\
                --boldprefix="BOLD" \\
                --boldsuffix="Atlas" \\
                --overwrite='yes'

EOF
exit 0
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]]; then
    usage
fi

# ------------------------------------------------------------------------------
# -- Parse and check all arguments
# ------------------------------------------------------------------------------

get_options() {

########### INPUTS ###############

    # -- Various HCP processed modalities

########## OUTPUTS ###############

    # -- Outputs will be files located in the location specified in the outputpath

# -- Set general options functions
opts_GetOpt() {
sopt="$1"
shift 1
for fn in "$@" ; do
    if [ `echo $fn | grep -- "^${sopt}=" | wc -w` -gt 0 ]; then
        echo $fn | sed "s/^${sopt}=//"
        return 0
    fi
done
}

# -- Get the command line options for this script

# -- Initialize global variables
unset SessionsFolder # --sessionsfolder=
unset CASES # --sessions=
unset Overwrite # --overwrite=
unset OutPath # --outpath
unset scenetemplatefolder # --scenetemplatefolder
unset UserSceneFile # --userscenefile
unset UserScenePath # --userscenepath
unset Modality # --modality
unset DWIPath # --dwipath
unset DWIData  # --dwidata
unset DtiFitQC # --dtifitqc
unset BedpostXQC # --bedpostxqc
unset EddyQCStats # --eddyqcstats
unset BOLDS # --bolddata
unset BOLDRUNS # --bolddata
unset BOLDDATA # --bolddata
unset BOLDfc # --boldfc
unset BOLDfcInput # --boldfcinput
unset BOLDfcPath #boldfcpath
unset BOLDPrefix # --boldprefix
unset BOLDSuffix # --boldsuffix
unset SkipFrames # --skipframes
unset SNROnly # --snronly
unset TimeStamp # --timestamp
unset Suffix # --suffix
unset SceneZip # --scenezip
unset RunQCCustom # --processcustom
unset OmitDefaults # --omitdefault
unset HCPSuffix # --hcp_suffix
unset GeneralSceneDataFile # --datafile
unset GeneralSceneDataPath # --datapath
unset SessionBatchFile # --sessionsbatchfile
unset sourcefile # --sourcefile
unset hcp_filename # -- hcp_filename

runcmd=""

# -- Parse general arguments
SessionsFolder=`opts_GetOpt "--sessionsfolder" $@`
CASES=`opts_GetOpt "--sessions" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
Overwrite=`opts_GetOpt "--overwrite" $@`
OutPath=`opts_GetOpt "--outpath" $@`
scenetemplatefolder=`opts_GetOpt "--scenetemplatefolder" $@`
UserSceneFile=`opts_GetOpt "--userscenefile" $@`
UserScenePath=`opts_GetOpt "--userscenepath" $@`
RunQCCustom=`opts_GetOpt "--customqc" $@`
OmitDefaults=`opts_GetOpt "--omitdefaults" $@`
HCPSuffix=`opts_GetOpt "--hcp_suffix" $@`

# -- Carefully set modality
Modality=`opts_GetOpt "--modality" $@`
if [ "${Modality,,}" == "t1w" ];      then Modality="T1w";     fi
if [ "${Modality,,}" == "t2w" ];      then Modality="T2w";     fi
if [ "${Modality,,}" == "bold" ];     then Modality="BOLD";    fi
if [ "${Modality,,}" == "dwi" ];      then Modality="DWI";     fi
if [ "${Modality,,}" == "rawnii" ];   then Modality="rawNII";  fi
if [ "${Modality,,}" == "rawnifti" ]; then Modality="rawNII";  fi
modality_lower=${Modality,,}

# -- Parameters if requesting 'general' scene type
GeneralSceneDataFile=`opts_GetOpt "--datafile" $@`
GeneralSceneDataPath=`opts_GetOpt "--datapath" $@`

# -- Parse DWI arguments
DWIPath=`opts_GetOpt "--dwipath" $@`
DWIData=`opts_GetOpt "--dwidata" $@`
DtiFitQC=`opts_GetOpt "--dtifitqc" $@`
BedpostXQC=`opts_GetOpt "--bedpostxqc" $@`
EddyQCStats=`opts_GetOpt "--eddyqcstats" $@`
# -- Parse BOLD arguments
BOLDS=`opts_GetOpt "--bolds" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
if [ -z "${BOLDS}" ]; then
    BOLDS=`opts_GetOpt "--boldruns" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
fi
if [ -z "${BOLDS}" ]; then
    BOLDS=`opts_GetOpt "--bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
fi
# set to all if not specified
if [ -z "${BOLDS}" ]; then
    BOLDS="all"
fi

BOLDRUNS="${BOLDS}"
BOLDDATA="${BOLDS}"
BOLDSuffix=`opts_GetOpt "--boldsuffix" $@`
BOLDPrefix=`opts_GetOpt "--boldprefix" $@`
SkipFrames=`opts_GetOpt "--skipframes" $@`
SNROnly=`opts_GetOpt "--snronly" $@`
BOLDfc=`opts_GetOpt "--boldfc" $@`
BOLDfcInput=`opts_GetOpt "--boldfcinput" $@`
BOLDfcPath=`opts_GetOpt "--boldfcpath" $@`

# -- Parse optional arguments
TimeStamp=`opts_GetOpt "--timestamp" $@`
Suffix=`opts_GetOpt "--suffix" $@`
SceneZip=`opts_GetOpt "--scenezip" $@`

# -- Parse batch file input
SessionBatchFile=`opts_GetOpt "--batchfile" $@`
if [ -z "${SessionBatchFile}" ]; then
    SessionBatchFile=`opts_GetOpt "--sessionsbatchfile" $@`
fi

# -- Get source file and hcp_filename
sourcefile=`get_parameters "--sourcefile" $@`
hcp_filename=`get_parameters "--hcp_filename" $@`

# -- Check general required parameters
if [ -z ${CASES} ]; then
    usage
    echo "---> ERROR: <session_ids> not specified."; echo ""
    exit 1
fi
if [[ ${CASES} == *.txt ]]; then
    SessionBatchFile="$CASES"
    echo ""
    echo "---> Using $SessionBatchFile for input."
    echo ""
    CASES=`cat ${SessionBatchFile} | grep "id:" | cut -d ':' -f 2 | sed 's/[[:space:]]\+//g'`
fi
if [ -z ${SessionsFolder} ]; then
    usage
    echo "---> ERROR: <sessions_folder> not specified."; echo ""
    exit 1
fi
if [ -z ${Overwrite} ]; then
    Overwrite="no"
    echo "Overwrite value not explicitly specified. Using default: ${Overwrite}"; echo ""
fi
if [ -z ${OutPath} ]; then
    OutPath="${SessionsFolder}/QC/${Modality}"
    echo "---> Output folder path value not explicitly specified. Using default: ${OutPath}"; echo ""
fi
if [ -z ${Modality} ]; then 
    usage
    echo "---> ERROR:  Modality to perform QC on missing [Supported: T1w, T2w, myelin, BOLD, DWI]"; echo ""
    exit 1
fi
if [ -z "$RunQCCustom" ]; then 
    RunQCCustom="no"; 
fi
if [ "$RunQCCustom" == "yes" ]; then 
    scenetemplatefolder="${StudyFolder}/processing/scenes/QC/${Modality}"
fi

if [ -z "$OmitDefaults" ]; then 
    OmitDefaults="no"; 
fi
# -- Perform some careful scene checks
if [ -z "$UserSceneFile" ]; then
    if [ ! -z "$UserScenePath" ]; then 
        echo "---> Provided --userscenepath but --userscenefile not specified."
        echo "     Check your inputs and re-run.";
        scenetemplatefolder="${TOOLS}/${QUNEXREPO}/qx_library/data/scenes/qc"
        echo "---> Reverting to QuNex defaults: ${scenetemplatefolder}"; echo ""
    fi
    if [ -z "$scenetemplatefolder" ]; then
        scenetemplatefolder="${TOOLS}/${QUNEXREPO}/qx_library/data/scenes/qc"
        echo "---> Template folder path value not explicitly specified."; echo ""
        echo "---> Using QuNex defaults: ${scenetemplatefolder}"; echo ""
    fi
    if ls ${scenetemplatefolder}/*${modality_lower}*.scene 1> /dev/null 2>&1; then 
        echo ""
        echo "---> Scene files found in: "; echo ""
        echo "`ls ${scenetemplatefolder}/*${modality_lower}*.scene` "; echo ""
    else 
        echo "---> Specified folder contains no scenes: ${scenetemplatefolder}" 
        scenetemplatefolder="${TOOLS}/${QUNEXREPO}/qx_library/data/scenes/qc"
        echo "---> Reverting to defaults: ${scenetemplatefolder} "; echo ""
    fi
else
    if [ -f "$UserSceneFile" ]; then
        echo "---> User scene file found: ${UserSceneFile}"; echo ""
        UserScenePath=`echo ${UserSceneFile} | awk -F'/' '{print $1}'`
        UserSceneFile=`echo ${UserSceneFile} | awk -F'/' '{print $2}'`
        scenetemplatefolder=${UserScenePath}
    else
        if [ -z "$UserScenePath" ] && [ -z "$scenetemplatefolder" ]; then 
            echo "---> ERROR: Path for user scene file not specified."
            echo "     Specify --scenetemplatefolder or --userscenepath with correct path and re-run."; echo ""; exit 1
        fi
        if [ ! -z "$UserScenePath" ] && [ -z "$scenetemplatefolder" ]; then 
            scenetemplatefolder=${UserScenePath}
        fi
        if ls ${scenetemplatefolder}/${UserSceneFile} 1> /dev/null 2>&1; then 
            echo "---> User specified scene files found in: ${scenetemplatefolder}/${UserSceneFile} "; echo ""
        else 
            echo "---> ERROR: User specified scene ${scenetemplatefolder}/${UserSceneFile} not found." 
            echo "     Check your inputs and re-run."; echo ""; exit 1
        fi
    fi
fi
if [ -z ${TimeStamp} ]; then
    TimeStamp=`date +%Y-%m-%d_%H.%M.%S.%6N`
    Suffix="$CASE_$TimeStamp"
    echo "Time stamp for logging not found. Setting now: ${TimeStamp}"; echo ""
fi
if [ -z ${Suffix} ]; then
    Suffix="$CASE_$TimeStamp"
    echo "---> Suffix not manually set. Setting default: ${Suffix}"; echo ""
fi
if [ -z ${SceneZip} ]; then
    SceneZip="yes"
    echo "---> Generation of scene zip file not explicitly provided. Using defaults: ${SceneZip}"; echo ""
fi

if [ -z "$HCPSuffix" ]; then 
    echo "---> hcp_suffix flag not explicitly provided. Using defaults: ${HCPSuffix}"; echo ""
fi

# -- DWI modality-specific settings:
if [ "$Modality" = "DWI" ]; then
    if [ -z "$DWIPath" ]; then DWIPath="Diffusion"; echo "DWI input path not explicitly specified. Using default: ${DWIPath}"; echo ""; fi
    if [ -z "$DWIData" ]; then DWIData="data"; echo "DWI data name not explicitly specified. Using default: ${DWIData}"; echo ""; fi
    if [ -z "$DtiFitQC" ]; then DtiFitQC="no"; echo "DWI dtifit QC not specified. Using default: ${DtiFitQC}"; echo ""; fi
    if [ -z "$BedpostXQC" ]; then BedpostXQC="no"; echo "DWI BedpostX not specified. Using default: ${BedpostXQC}"; echo ""; fi
    if [ -z "$EddyQCStats" ]; then EddyQCStats="no"; echo "DWI EDDY QC Stats not specified. Using default: ${EddyQCStats}"; echo ""; fi
fi
# -- BOLD modality-specific settings:
if [ "$Modality" = "BOLD" ]; then
    if [ -z "$BOLDfc" ]; then
        # -- Set BOLD prefix correctly
        if [ -z "$BOLDPrefix" ]; then 
            BOLDPrefix=""; echo "BOLD prefix not specified. Assuming no prefix"; echo ""
        fi
        # -- Set BOLD suffix correctly
        if [ -z "$BOLDSuffix" ]; then 
            BOLDSuffix=""; echo "BOLD suffix not specified. Assuming no suffix"; echo ""
        else
            BOLDSuffix="_${BOLDSuffix}"
        fi
        # -- Set SkipFrames and SNROnly defaults if missing
        if [ -z "$SkipFrames" ]; then SkipFrames="0"; echo ""; fi
        if [ -z "$SNROnly" ]; then SNROnly="no"; echo ""; fi
    fi
    
    if [ ! -z "$BOLDfc" ]; then
        if [ -z "$BOLDfcInput" ]; then 
            echo "---> ERROR: Flag --boldfcinput is missing. Check your inputs and re-run."; echo ""; exit 1
        fi
    fi

    if [[ ! -z ${SessionBatchFile} ]]; then
        if [[ ! -f ${SessionBatchFile} ]]; then
            echo "---> ERROR: Requested BOLD modality with a batch file. Batch file not found."
            exit 1
        else
            BOLDSBATCH="${BOLDS}"
        fi
    else
        # if BOLDS is all we need a batch file
        if [[ ${BOLDS} == "all" ]]; then
            echo "---> ERROR: When running QC over all BOLDS you need to specify a batch file!"
            exit 1
        fi
    fi
fi

# -- General modality settings:
if [ "$Modality" = "general" ] ; then
    if [ -z "$GeneralSceneDataFile" ]; then echo "---> ERROR: Data input not specified"; echo ""; exit 1; fi
    if [ -z "$GeneralSceneDataPath" ]; then echo "---> ERROR: Data input path not specified"; echo ""; exit 1; fi
fi

# -- Set StudyFolder
cd $SessionsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null
scriptName=$(basename ${0})

# -- Report options
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "  Study Folder: ${StudyFolder}"
echo "  Session Folder: ${SessionsFolder}"
echo "  Sessions: ${CASES}"
echo "  QC Modality: ${Modality}"
echo "  QC Output Path: ${OutPath}"
echo "  Custom QC requested: ${RunQCCustom}"
echo "  HCP suffix: ${HCPSuffix}"
if [ "$RunQCCustom" == "yes" ]; then
    echo "   Custom QC modalities: ${Modality}"
fi
if [ "$Modality" == "BOLD" ] ; then
    if [[ ! -z ${SessionBatchFile} ]]; then
        if [[ ! -f ${SessionBatchFile} ]]; then
            echo " ERROR: Requested BOLD modality with a batch file. Batch file not found."
            exit 1
        else
            echo "   Session batch file requested: ${SessionBatchFile}"
            BOLDSBATCH="${BOLDS}"
        fi
    fi
    if [[ ! -z ${BOLDRUNS} ]]; then
        echo "   BOLD runs requested: ${BOLDS}"
    else
        echo "   BOLD runs requested: all"
    fi
fi
echo "  Omit default QC: ${OmitDefaults} "
echo "  QC Scene Template Folder: ${scenetemplatefolder}"
echo "  QC User-defined Scene: ${UserSceneFile}"
echo "  Overwrite prior run: ${Overwrite}"
echo "  Time stamp for logging: ${TimeStamp}"
echo "  Zip Scene File: ${SceneZip}"
if [ "$Modality" = "DWI" ]; then
    echo "  DWI input path: ${DWIPath}"
    echo "  DWI input name: ${DWIData}"
    echo "  DWI dtifit QC requested: ${DtiFitQC}"
    echo "  DWI bedpostX QC requested: ${BedpostXQC}"
    echo "  DWI EDDY QC Stats requested: ${EddyQCStats}"
fi
if [ "$Modality" = "BOLD" ]; then
    echo "  BOLD data input: ${BOLDS}"
    echo "  BOLD prefix: ${BOLDPrefix}"
    echo "  BOLD suffix: ${BOLDSuffix}"
    echo "  Skip Initial Frames: ${SkipFrames}"
    echo "  Compute SNR Only: ${SNROnly}"
    if [ "$SNROnly" == "yes" ]; then 
        echo ""
        echo "BOLD SNR only specified. Will skip QC images"
        echo ""
    fi
    if [[ ! -z ${BOLDfc} ]]; then
        echo "  BOLD FC requested: ${BOLDfc}"
        echo "  BOLD FC input: ${BOLDfcInput}"
        echo "  BOLD FC path: ${BOLDfcPath}"
    fi
fi
if [ "$Modality" = "general" ]; then
    echo "  Data input path: ${GeneralSceneDataPath}"
    echo "  Data input: ${GeneralSceneDataFile}"
fi
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
echo "------------------------- Start of work --------------------------------"
echo ""

}


######################################### SUPPORT FUNCTIONS ##########################################


# -------------------------------------------
# -- Final report function
# -------------------------------------------


finalReport(){

    if [ "${CompletionCheck}" == "fail" ]; then
        echo "------------------------- ERROR --------------------------------"
        echo ""
        echo "   QC generation did not complete correctly."
        echo "   Check outputs: ${RunQCLogFolder}/QC_${CASE}_ComQUEUE_${Modality}_${TimeStamp}.log"
        echo ""
        echo "----------------------------------------------------------------"
        echo ""
    else
        echo ""
        echo "------------------------- Successful completion of work --------------------------------"
        echo ""
    fi
}

# -------------------------------------------
# -- Completion checks functions
# -------------------------------------------

# check if a previous run was successful
previousCompletionCheck() {

    # set the default value for this check
    PreviousCompletionCheck="pass"

    # if Modality is not BOLD
    if [[ ${Modality} != "BOLD" ]]; then

        # check for working scene file
        if [ ! -f ${OutPath}/${WorkingSceneFile} ]; then
            PreviousCompletionCheck="fail"
            return 1
        fi

        # check for timestamped working scene file
        for f in ${OutPath}/${WorkingSceneFile}.*.png; do
            if [ ! -e $f ]; then
                PreviousCompletionCheck="fail"
                return 1
            fi
        done

        # check for working DTI scene file
        if [ "$DtiFitQC" == "yes" ]; then

            if [ ! -f ${OutPath}/${WorkingDTISceneFile} ]; then
                PreviousCompletionCheck="fail"
                return 1
            fi

            # check for timestamped working DTI scene file
            if [ "$SceneZip" == "yes" ]; then
                for f in ${OutPath}/${WorkingDTISceneFile}.*.zip; do
                    if [ ! -e $f ]; then
                        PreviousCompletionCheck="fail"
                        return 1
                    fi
                done
            fi
        fi
        
        # check for working BedpostX scene file
        if [ "$BedpostXQC" == "yes" ]; then
            if [ ! -f ${OutPath}/${WorkingBedpostXSceneFile} ]; then
                PreviousCompletionCheck="fail"
                return 1
            fi

            # check for working timestamped BedpostX scene file
            if [ "$SceneZip" == "yes" ]; then
                for f in ${OutPath}/${WorkingBedpostXSceneFile}.*.zip; do
                    if [ ! -e $f ]; then
                        PreviousCompletionCheck="fail"
                        return 1
                    fi
                done
            fi
        fi
    fi
 
    # if Modality is BOLD
    if [ ${Modality} == "BOLD" ]; then
        # iterate over BOLDS
        for BOLD in ${BOLDS}; do

            # Check if prefix is specified
            if [ ! -z "$BOLDPrefix" ]; then
                if [ `echo ${BOLDPrefix} | grep '_'` ]; then BOLD="${BOLDPrefix}${BOLD}"; else BOLD="${BOLDPrefix}_${BOLD}"; fi
            else
                # Check if BOLD folder with the given number contains additional prefix info and return an exit code if yes
                NoBOLDDirPreffix=`ls -d ${HCPFolder}/MNINonLinear/Results/${BOLD}`
                NoBOLDPreffix=`ls -d ${HCPFolder}/MNINonLinear/Results/${BOLD} | sed 's:/*$::' | sed 's:.*/::'`
                if [ ! -z ${NoBOLDDirPreffix} ]; then
                    BOLD=${NoBOLDPreffix}
                fi
            fi

            # BOLD FC completion check
            if [ ! -z ${BOLDfc} ]; then

                # set working scene file
                WorkingSceneFile="${CASEName}.${BOLDfc}.${Modality}.${BOLD}.QC.wb.scene"

                # check for working scene file
                if [ ! -f ${OutPath}/${WorkingSceneFile} ]; then
                    PreviousCompletionCheck="fail"
                    return 1
                fi

                # check for timestamped working scene file
                for f in ${OutPath}/${WorkingSceneFile}.*.png; do
                    if [ ! -e $f ]; then
                        PreviousCompletionCheck="fail"
                        return 1
                    fi
                done
            fi
            
            # BOLD raw dtseries cmpletion check
            if [ -z ${BOLDfc} ]; then

                # check for timestamped TSNR report
                for f in ${OutPath}/${CASEName}_${BOLD}_TSNR_Report_*.txt; do
                    if [ ! -e $f ]; then
                        PreviousCompletionCheck="fail"
                        return 1
                    fi
                done

                # BOLD raw scene completion check w/o TSNR
                if [ ${SNROnly} != "yes" ]; then

                    # set working scene file
                    WorkingSceneFile="${CASEName}.${Modality}.${BOLD}.QC.wb.scene"

                    # scene zip?
                    if [ "$SceneZip" == "yes" ]; then

                        # check for timestamped working scene zip file
                        for f in ${OutPath}/${WorkingSceneFile}.*.zip; do
                            if [ ! -e $f ]; then
                                PreviousCompletionCheck="fail"
                                return 1
                            fi
                        done

                    else
                        # check for working scene file
                        if [ ! -f ${OutPath}/${WorkingSceneFile} ]; then
                            PreviousCompletionCheck="fail"
                            return 1
                        fi

                        # check for timestamped working scene file
                        for f in ${OutPath}/${WorkingSceneFile}.*.GStimeseries.QC.wb.png; do
                            if [ ! -e $f ]; then
                                PreviousCompletionCheck="fail"
                                return 1
                            fi
                        done

                    fi
                fi
            fi
        done
    fi
}

# check if this run was successful
completionCheck() {
 
    echo ""
    echo " --- Running QC completion checks..."
    echo ""
 
    if [[ ${Modality} != "BOLD" ]]; then
        if [[ -z ${FinalLog} ]]; then echo "---> ERROR: Final log file not defined. Report this error to developers."; echo ""; exit 1; fi
        LogError=`cat ${FinalLog} | grep "ERROR"`
        if [ -f ${OutPath}/${WorkingSceneFile} ] && [ -f ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png ] && [[ ${LogError} == "" ]]; then
            echo ""
            echo "---> Scene file found and generated: ${OutPath}/${WorkingSceneFile}"
            echo ""
            echo ""
            echo "---> PNG file found and generated: ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png "
            echo ""
        else
            echo ""
            echo "---> ERROR: Scene generation and PNG output failed. Check work."; echo ""
            CompletionCheck="fail"
        fi
        if [ "$SceneZip" == "yes" ]; then
            if [ -f ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ]; then
                echo ""
                echo "---> Scene zip file found and generated: ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip"
                echo ""
            else
                echo ""
                echo "---> ERROR: Scene zip generation failed. Check work."
                echo ""
            fi
        fi
    
        if [ "$DtiFitQC" == "yes" ]; then
            if [ -f ${OutPath}/${WorkingDTISceneFile} ]; then
                echo ""
                echo "---> Scene file found and generated: ${OutPath}/${WorkingSceneFile}"
                echo ""
            else
                echo ""
                echo "---> ERROR: Scene generation failed for ${OutPath}/${WorkingDTISceneFile}. Check inputs."; echo ""
                CompletionCheck="fail"
                return 1
            fi
            if [ "$SceneZip" == "yes" ]; then
                if [[ -f ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.zip ]]; then
                    echo ""
                    echo "---> Scene zip file found and generated: ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.zip"
                    echo ""
                else
                    echo ""
                    echo "---> ERROR: Scene zip generation failed for ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.zip. Check work."; echo ""
                    CompletionCheck="fail"
                    return 1
                fi
            fi
        fi
        
        if [ "$BedpostXQC" == "yes" ]; then
            if [ -f ${OutPath}/${WorkingBedpostXSceneFile} ]; then
                echo ""
                echo "---> Scene file found and generated: ${OutPath}/${WorkingBedpostXSceneFile}"
                echo ""
            else
                echo ""
                echo "---> ERROR: Scene generation failed for ${OutPath}/${WorkingBedpostXSceneFile}. Check inputs."; echo ""
                CompletionCheck="fail"
                return 1
            fi
            if [ "$SceneZip" == "yes" ]; then
                if [ -f ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.zip ]; then
                    echo ""
                    echo "---> Scene zip file found and generated: ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.zip"
                    echo ""
                else
                    echo ""
                    echo "---> ERROR: Scene zip generation failed for ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.zip. Check work."; echo ""
                    CompletionCheck="fail"
                    return 1
                fi
            fi
        fi
    fi
 
    if [[ ${Modality} == "BOLD" ]]; then
        
        # -- BOLD FC completion check
        if [[ ! -z ${BOLDfc} ]]; then
            CompletionCheck=""
            if [[ -z ${FinalLog} ]]; then echo "---> ERROR: Final log file not defined. Report this error to developers."; echo ""; exit 1; fi
            LogError=`cat ${FinalLog} | grep 'ERROR'`

            if [ -f ${OutPath}/${WorkingSceneFile} ] && [ -f ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png ] && [[ ${LogError} == "" ]]; then
                echo ""
                echo "---> Scene file and PNG file found and generated: ${OutPath}/${WorkingSceneFile}"
                echo ""
                CompletionCheck=""
                return 0
                if [ "$SceneZip" == "yes" ]; then
                    if [ -f ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ]; then
                        echo ""
                        echo "---> Scene zip file found and generated: ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip"
                        echo ""
                        CompletionCheck=""
                        return 0
                    else
                        echo ""
                        echo "---> ERROR: Scene zip generation not completed."; echo ""
                        CompletionCheck="fail"
                    fi
                fi
            else
                echo ""
                echo "---> ERROR: Scene and PNG QC generation not completed."; echo ""
                CompletionCheck="fail"
            fi
        fi
        
        # BOLD raw dtseries QC check
        if [[ -z ${BOLDfc} ]]; then
            # Check TSNRReportBOLD regardless of SNROnly flag
            CompletionCheck=""

            # Echo completion & Check SNROnly flag
            if [ -f ${TSNRReportBOLD} ]; then
                echo ""
                echo "---> SNR calculation requested. SNR completed." 
                echo "     Session specific report can be found here: ${TSNRReportBOLD}"
                echo ""
                CompletionCheck=""
            else
                echo "---> ERROR: SNR report not found for ${CASE} and BOLD ${BOLD}."
                echo ""
                CompletionCheck="fail"
            fi

            # -- BOLD raw scene completion check w/o TSNR
            if [[ ${SNROnly} != "yes" ]]; then

                if [[ -z ${FinalLog} ]]; then echo "---> ERROR: Final log file not defined. Report this error to developers."; echo ""; exit 1; fi
                LogError=`cat ${FinalLog} | grep 'ERROR'`
                
                if [[ -f ${OutPath}/${WorkingSceneFile} ]] && [[ -f ${OutPath}/${WorkingSceneFile}.${TimeStamp}.GStimeseries.QC.wb.png ]] && [[ ${LogError} == "" ]]; then
                    echo ""
                    echo "---> Scene file found and generated: ${OutPath}/${WorkingSceneFile}"
                    echo ""
                    return 0
                    if [ "$SceneZip" == "yes" ]; then
                        if [ -f ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ]; then
                            echo ""
                            echo "---> Scene zip file found and generated: ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip"
                            echo ""
                            return 0
                        else
                            echo ""
                            echo "---> ERROR: Scene zip generation failed. Check work."; echo ""
                            CompletionCheck="fail"
                        fi
                    fi
                else
                    echo ""
                    echo "---> ERROR: Scene and PNG QC generation not completed."; echo ""
                    echo ""
                    echo "    ---> Check scene output: ${OutPath}/${WorkingSceneFile}"
                    echo "    ---> Check scene png: ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png"
                    echo "    ---> Check run-specific log: ${FinalLog}"; echo ""
                    CompletionCheck="fail"
                fi
            fi
        fi
    fi
}

# -------------------------------------------
# -- Dummy variable check
# ------------------------------------------

# Perform checks if scene has proper info: 
DummyVariable_Check () {
    if [[ ${Modality} != "BOLD" ]]; then
        DUMMYVARIABLES="DUMMYPATH DUMMYCASE DUMMYTIMESTAMP"
    fi
    if [[ ${Modality} == "BOLD" ]]; then
       DUMMYVARIABLES="DUMMYPATH DUMMYCASE DUMMYBOLDDATA _DUMMYBOLDSUFFIX DUMMYTIMESTAMP DUMMYBOLDANNOT"
    fi
    if [[ ${Modality} == "BOLD" ]] && [[ ! -z ${BOLDfc} ]]; then
       DUMMYVARIABLES="DUMMYPATH DUMMYCASE DUMMYIMAGEPATH DUMMYIMAGEFILE DUMMYTIMESTAMP"
    fi
    if [[ ${Modality} == "general" ]]; then
       DUMMYVARIABLES="DUMMYPATH DUMMYCASE DUMMYIMAGEPATH DUMMYIMAGEFILE DUMMYTIMESTAMP"
    fi
    for DUMMYVARIABLE in ${DUMMYVARIABLES}; do
        echo ""; echo "Checking $DUMMYVARIABLE is present in scene ${scenetemplatefolder}/${TemplateSceneFile} "; echo ""
        if [ -z `cat ${scenetemplatefolder}/${TemplateSceneFile} | grep "${DUMMYVARIABLE}"` ]; then
            echo ""
            echo " ---> ERROR: ${DUMMYVARIABLE} variable not defined in ${scenetemplatefolder}/${TemplateSceneFile} "
            echo "      Fix the scene and re-run!"
            echo ""
            exit 1
        else
            echo ""
            echo " ---> ${DUMMYVARIABLE} variable found in ${scenetemplatefolder}/${TemplateSceneFile} "
            echo "      Proceeding..."
            echo ""
        fi
    done
}



# -------------------------------------------
# -- BOLD Processing functions
# -------------------------------------------

# -- Function to run BOLD TSNR
runsnr_BOLD() {
    TSNRReport="${OutPath}/TSNR_Report_All_${TimeStamp}.txt"
    TSNRReportBOLD="${OutPath}/${CASEName}_${BOLD}_TSNR_Report_${TimeStamp}.txt"
    
    # -- Check completion
    if [ ${Overwrite} == "yes" ]; then
        rm -f ${HCPFolder}/${BOLDRoot}_GS.txt &> /dev/null
        rm -f ${HCPFolder}/${BOLDRoot}_GS.dtseries.nii &> /dev/null
        rm -f ${HCPFolder}/${BOLDRoot}_GS.sdseries.nii &> /dev/null
        rm -f ${OutPath}/${CASEname}_${BOLD}_TSNR_Report_*
    fi

    # -- Reduce dtseries
    wb_command -cifti-reduce ${HCPFolder}/${BOLDRoot}.dtseries.nii TSNR ${HCPFolder}/${BOLDRoot}_TSNR.dscalar.nii -exclude-outliers 4 4
    # -- Compute SNR
    TSNR=`wb_command -cifti-stats ${HCPFolder}/${BOLDRoot}_TSNR.dscalar.nii -reduce MEAN`
    # -- Record values 
    TSNRLog="${HCPFolder}/${BOLDRoot}_TSNR.dscalar.nii: ${TSNR}"
    # -- Get values for plotting GS chart & Compute the GS scalar series file ---> TR
    TR=`fslval ${HCPFolder}/MNINonLinear/Results/${BOLD}/${BOLD}.nii.gz pixdim4`
    # -- Regenerate outputs
    wb_command -cifti-reduce ${HCPFolder}/${BOLDRoot}.dtseries.nii MEAN ${HCPFolder}/${BOLDRoot}_GS.dtseries.nii -direction COLUMN
    wb_command -cifti-stats ${HCPFolder}/${BOLDRoot}_GS.dtseries.nii -reduce MEAN >> ${HCPFolder}/${BOLDRoot}_GS.txt
    # -- Check skipped frames
    if [ ${SkipFrames} > 0 ]; then 
        rm -f ${HCPFolder}/${BOLDRoot}_GS_omit_initial_${SkipFrames}_TRs.txt &> /dev/null
        tail -n +${SkipFrames} ${HCPFolder}/${BOLDRoot}_GS.txt >> ${HCPFolder}/${BOLDRoot}_GS_omit_initial_${SkipFrames}_TRs.txt
        TR=`cat ${HCPFolder}/${BOLDRoot}_GS_omit_initial_${SkipFrames}_TRs.txt | wc -l` 
        wb_command -cifti-create-scalar-series ${HCPFolder}/${BOLDRoot}_GS_omit_initial_${SkipFrames}_TRs.txt ${HCPFolder}/${BOLDRoot}_GS.sdseries.nii -transpose -series SECOND 0 ${TR}
        xmax="$TR"
    else
        wb_command -cifti-create-scalar-series ${HCPFolder}/${BOLDRoot}_GS.txt ${HCPFolder}/${BOLDRoot}_GS.sdseries.nii -transpose -series SECOND 0 ${TR}
        xmax=`fslval ${HCPFolder}/MNINonLinear/Results/${BOLD}/${BOLD}.nii.gz dim4`
    fi
    # -- Get mix/max stats
    ymax=`wb_command -cifti-stats ${HCPFolder}/${BOLDRoot}_GS.sdseries.nii -reduce MAX | sort -rn | head -n 1`
    ymin=`wb_command -cifti-stats ${HCPFolder}/${BOLDRoot}_GS.sdseries.nii -reduce MAX | sort -n | head -n 1`
    printf "${TSNRLog}\n" >> ${TSNRReport}
    printf "${TSNRLog}\n" >> ${TSNRReportBOLD}
}

# -- Function to run BOLD FC
runscene_BOLDfc() {
    if [ -z "$BOLDfcPath" ]; then 
        BOLDfcPath="${SessionsFolder}/${CASE}/images/functional"
        echo ""
        echo "---> Note: Flag --boldfcpath not provided. Setting now: ${BOLDfcPath}"
        echo ""
    fi

    echo "---> Setting up commands to run BOLD FC scene generation"; echo ""
    echo "---> Working on ${OutPath}/${WorkingSceneFile}"; echo ""
    # -- Setup naming conventions before generating scene
    ComRunBoldfc1="sed -i -e 's|DUMMYPATH|$HCPFolder|g' ${OutPath}/${WorkingSceneFile}" 
    ComRunBoldfc2="sed -i -e 's|DUMMYCASE|$CASEName|g' ${OutPath}/${WorkingSceneFile}"
    # -- Add timestamp to the scene and replace paths: DUMMYIMAGEPATH/DUMMYIMAGEFILE
    BOLDfcInput="bold${BOLD}_${BOLDfcInput}"
    ComRunBoldfc3="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingSceneFile}"
    ComRunBoldfc4="sed -i -e 's|DUMMYIMAGEPATH|$BOLDfcPath|g' ${OutPath}/${WorkingSceneFile}"
    ComRunBoldfc5="sed -i -e 's|DUMMYIMAGEFILE|$BOLDfcInput|g' ${OutPath}/${WorkingSceneFile}"
    # -- Add name of png to scene:
    PNGNameBOLDfc="${WorkingSceneFile}.${TimeStamp}.png"
    ComRunBoldPNGNameBOLDfc="sed -i -e 's|DUMMYPNGNAME|$PNGNameBOLDfc|g' ${OutPath}/${WorkingSceneFile}"
    # -- Output image of the scene
    ComRunBoldfc6="wb_command -show-scene ${OutPath}/${WorkingSceneFile} 1 ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png 1194 539"
    # -- Clean temp scene
    ComRunBoldfc7="rm ${OutPath}/${WorkingSceneFile}-e &> /dev/null"
    # -- Generate Scene Zip File if set to YES
    if [ "$SceneZip" == "yes" ]; then
        echo "---> Scene zip set to: $SceneZip. Relevant scene files will be zipped with the following base folder:" 
        echo "    ${HCPFolder}"
        echo ""
        echo "---> The zip file will be saved to: "
        echo "    ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip "
        echo ""
        RemoveScenePath="${HCPFolder}"
        ComRunBoldfc8="rm ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip &> /dev/null "
        ComRunBoldfc9="cp ${OutPath}/${WorkingSceneFile} ${SessionsFolder}/${CASE}/hcp/${CASE}${HCPSuffix}/"
        ComRunBoldfc10="mkdir -p ${HCPFolder}/qc &> /dev/null"
        ComRunBoldfc11="cp ${BOLDfcPath}/${BOLDfcInput} ${HCPFolder}/qc"
        ComRunBoldfc12="sed -i -e 's|$RemoveScenePath|.|g' ${HCPFolder}/${WorkingSceneFile}"
        ComRunBoldfc13="sed -i -e 's|$BOLDfcPath|./qc/|g' ${HCPFolder}/${WorkingSceneFile}" 
        ComRunBoldfc14="cd ${OutPath}; wb_command -zip-scene-file ${HCPFolder}/${WorkingSceneFile} ${WorkingSceneFile}.${TimeStamp} ${WorkingSceneFile}.${TimeStamp}.zip -base-dir ${HCPFolder}"
        ComRunBoldfc15="rm ${HCPFolder}/${WorkingSceneFile}"
        ComRunBoldfc16="cp ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ${HCPFolder}/qc/"
    fi
    # -- Combine all the calls into a single command
    if [ "$SceneZip" == "yes" ]; then
        ComRunBoldQUEUE="$ComQueue; $ComRunBoldfc1; $ComRunBoldfc2; $ComRunBoldfc3; $ComRunBoldfc4; $ComRunBoldfc5; $ComRunBoldPNGNameBOLDfc; $ComRunBoldfc6; $ComRunBoldfc7; $ComRunBoldfc8; $ComRunBoldfc9; $ComRunBoldfc10; $ComRunBoldfc11; $ComRunBoldfc12; $ComRunBoldfc13; $ComRunBoldfc14; $ComRunBoldfc15; $ComRunBoldfc16"
    else
        ComRunBoldQUEUE="$ComQueue; $ComRunBoldfc1; $ComRunBoldfc2; $ComRunBoldfc3; $ComRunBoldfc4; $ComRunBoldfc5; $ComRunBoldPNGNameBOLDfc; $ComRunBoldfc6; $ComRunBoldfc7"
    fi
}

# -- Function to run BOLD raw scene QC
runscene_BOLD() {
    # -- Setup naming conventions before generating scene
    ComRunBold1="sed -i -e 's|DUMMYPATH|$HCPFolder|g' ${OutPath}/${WorkingSceneFile}" 
    ComRunBold2="sed -i -e 's|DUMMYCASE|$CASEName|g' ${OutPath}/${WorkingSceneFile}"
    ComRunBold3="sed -i -e 's|DUMMYBOLDDATA|$BOLD|g' ${OutPath}/${WorkingSceneFile}"
    # -- Set the BOLDSuffix variable
    ComRunBold4="sed -i -e 's|_DUMMYBOLDSUFFIX|$BOLDSuffix|g' ${OutPath}/${WorkingSceneFile}"
    # -- Add timestamp to the scene
    ComRunBold5="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingSceneFile}"
    ComRunBold6="sed -i -e 's|DUMMYBOLDANNOT|$BOLD|g' ${OutPath}/${WorkingSceneFile}"
    # -- Add name of png to scene:
    PNGNameGSMap="${WorkingSceneFile}.GSmap.QC.wb.png"
    PNGNameGStimeseries="${WorkingSceneFile}.GStimeseries.QC.wb.png"
    ComRunBoldPngNameGSMap="sed -i -e 's|DUMMYPNGNAMEGSMAP|$PNGNameGSMap|g' ${OutPath}/${WorkingSceneFile}"
    ComRunBoldPngNameGStimeseries="sed -i -e 's|DUMMYPNGNAMEGSTIME|$PNGNameGStimeseries|g' ${OutPath}/${WorkingSceneFile}"
    # -- Output image of the scene
    ComRunBold7="wb_command -show-scene ${OutPath}/${WorkingSceneFile} 1 ${OutPath}/${WorkingSceneFile}.${TimeStamp}.GSmap.QC.wb.png 1194 539"
    ComRunBold8="wb_command -show-scene ${OutPath}/${WorkingSceneFile} 2 ${OutPath}/${WorkingSceneFile}.${TimeStamp}.GStimeseries.QC.wb.png 1194 539"
    # -- Clean temp scene
    ComRunBold9="rm ${OutPath}/${WorkingSceneFile}-e &> /dev/null"
    # -- Generate Scene Zip File if set to YES
    if [ "$SceneZip" == "yes" ]; then
        echo "---> Scene zip set to: $SceneZip. Relevant scene files will be zipped with the following base folder:" 
        echo "    ${HCPFolder}"
        echo ""
        echo "---> The zip file will be saved to: "
        echo "    ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip "
        echo ""
        RemoveScenePath="${HCPFolder}"
        ComRunBold10="cp ${OutPath}/${WorkingSceneFile} ${HCPFolder}/"
        ComRunBold11="rm ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip &> /dev/null "
        ComRunBold12="sed -i -e 's|$RemoveScenePath|.|g' ${HCPFolder}/${WorkingSceneFile}" 
        ComRunBold13="cd ${OutPath}; wb_command -zip-scene-file ${HCPFolder}/${WorkingSceneFile} ${WorkingSceneFile}.${TimeStamp} ${WorkingSceneFile}.${TimeStamp}.zip -base-dir ${HCPFolder}"
        ComRunBold14="rm ${HCPFolder}/${WorkingSceneFile}"
        ComRunBold15="mkdir -p ${HCPFolder}/qc &> /dev/null"
        ComRunBold16="cp ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ${HCPFolder}/qc/"
    fi
    # -- Combine all the calls into a single command
    if [ "$SceneZip" == "yes" ]; then
        ComRunBoldQUEUE="$ComQueue; $ComRunBold1; $ComRunBold2; $ComRunBold3; $ComRunBold4; $ComRunBold5; $ComRunBold6; $ComRunBoldPngNameGSMap; $ComRunBoldPngNameGStimeseries; $ComRunBold7; $ComRunBold8; $ComRunBold9; $ComRunBold10; $ComRunBold11; $ComRunBold12; $ComRunBold13; $ComRunBold14; $ComRunBold15; $ComRunBold16"
    else
        ComRunBoldQUEUE="$ComQueue; $ComRunBold1; $ComRunBold2; $ComRunBold3; $ComRunBold4; $ComRunBold5; $ComRunBold6; $ComRunBoldPngNameGSMap; $ComRunBoldPngNameGStimeseries; $ComRunBold7; $ComRunBold8; $ComRunBold9"
    fi
}


######################################### DO WORK ##########################################




main() {

    # -- Get Command Line Options
    get_options "$@"
    for CASE in ${CASES}; do
        # -- Set basics
        CASEName="${CASE}${HCPSuffix}"
        HCPFolder="${SessionsFolder}/${CASE}/hcp/${CASEName}"
        if [ ! -z "$HCPSuffix" ]; then 
           echo " ---> HCP suffix specified ${HCPSuffix}"; echo ""
           echo "      Setting hcp folder to: ${SessionsFolder}/${CASE}/hcp/${CASEName}"; echo ""
        fi

        # -- Check if raw NIFTI QC is requested and run it first
        if [ "$Modality" == "rawNII" ] ; then 
            unset CompletionCheck
            pushd ${SessionsFolder}/${CASE}/nii/
            slicesdir ${SessionsFolder}/${CASE}/nii/*.nii*
            popd > /dev/null
            if [ ! -f ${SessionsFolder}/${CASE}/nii/slicesdir/index.html ]; then
                CompletionCheck="fail"
            else
                mkdir -p ${OutPath}/${CASE}
                mv ${SessionsFolder}/${CASE}/nii/slicesdir/* ${OutPath}/${CASE}
            fi
        else
            # -- Set SessAcqInfoFile/source file
            if [ ! ${sourcefile} == "" ]; then
                echo ""
                echo "---> Using a custom sourcefile ${sourcefile}.";
                echo ""
                SessAcqInfoFile=${sourcefile}
            else
                if [ -f ${SessionsFolder}/${CASE}/session_hcp.txt ]; then
                    SessAcqInfoFile="session_hcp.txt"
                elif [ -f ${SessionsFolder}/${CASE}/subject_hcp.txt ]; then
                    SessAcqInfoFile="subject_hcp.txt"
                fi
            fi
           
            # -- Check if ${SessAcqInfoFile} is present:
            echo ""
            echo "---> Using ${SessAcqInfoFile} individual information files. Verifying that ${SessAcqInfoFile} exists.";
            echo ""
            if [[ -f "${SessionsFolder}/${CASE}/${SessAcqInfoFile}" ]]; then
                echo "${SessionsFolder}/${CASE}/${SessAcqInfoFile} found. Proceeding ..."
            else
                echo "${SessionsFolder}/${CASE}/${SessAcqInfoFile} NOT found. Check your data and inputs."
                echo ""
                exit 1
            fi

            # - If BOLDS parameter is empty then use session acquisition file
            if [ "$Modality" = "BOLD" ]; then
                if [ -z "$BOLDS" ]; then 
                    echo ""
                    echo "Note: BOLD input list not specified. Relying ${SessAcqInfoFile} individual information files."
                    BOLDS="${SessAcqInfoFile}"
                    echo ""
                fi
            fi

            # -- Proceed with other QC steps
            TemplateSceneFile="template_${modality_lower}_qc.wb.scene"
            WorkingSceneFile="${CASEName}.${Modality}.QC.wb.scene"
            
            if [ ! -z "$UserSceneFile" ]; then
                TemplateSceneFile"${UserSceneFile}"
                WorkingSceneFile="${CASEName}.${Modality}.${UserSceneFile}"
            fi
            
            if [ "$RunQCCustom" == "yes" ]; then
                scenetemplatefolder="${StudyFolder}/processing/scenes/QC/${Modality}"
                CustomTemplateSceneFiles=`ls -f ${scenetemplatefolder}/*.scene | xargs -n 1 basename`
                echo " ---> Custom scenes requested from ${scenetemplatefolder}"; echo ""
                echo "      ${CustomTemplateSceneFiles}"; echo ""
            fi

            # -- Check of overwrite flag was set
            if [ ${Overwrite} == "yes" ]; then
                echo ""
                if [ ${Modality} == "DWI" ]; then
                    echo " --- Note: Overwrite requested. "

                    # delete general DWI qc
                    rm -f ${OutPath}/${CASEName}.${Modality}.QC.* &> /dev/null

                    # if bedpostxqc is set delete bedpostx
                    if [ "$BedpostXQC" == "yes" ]; then
                        rm -f ${OutPath}/${CASEName}.${Modality}.bedpostx.QC.* &> /dev/null
                    fi

                    # if dtifitqc is set delete dtifitqx
                    if [ "$DtiFitQC" == "yes" ]; then
                        rm -f ${OutPath}/${CASEName}.${Modality}.dtifit.QC.* &> /dev/null
                    fi
                else
                    echo " --- Note: Overwrite requested. Removing existing ${Modality} QC scene: ${OutPath}/${WorkingSceneFile} "

                    rm -f ${OutPath}/${CASEName}.${Modality}.* &> /dev/null
                fi
                echo ""
            else
                echo "---> Overwrite is set to 'no'. Running checks for previously ran QC."
                previousCompletionCheck
                if [[ ${PreviousCompletionCheck} != "fail" ]]; then
                    echo ""
                    echo "---> Found files from a previous run, skipping this one"
                    echo ""
                    echo "------------------------- Successful completion of work --------------------------------"
                    return 0
                fi
            fi
            
            # -- Check if a given png exists
            # if [ -f ${OutPath}/${CASE}.${Modality}.QC.png ]; then
            #     echo ""
            #     echo " --- ${Modality} QC scene png file found: ${OutPath}/${WorkingSceneFile}"
            #     echo ""
            #     return 1
            # else
            
            # -- Start of generating QC
            echo ""
            echo " --- Generating ${Modality} QC scene here: ${OutPath}"
            echo ""
            echo ""
            echo " --- Checking and generating output folders..."
            echo ""
            # -- Check general output folders for QC
            if [ ! -d ${SessionsFolder}/QC ]; then
                mkdir -p ${SessionsFolder}/QC &> /dev/null
            fi
            # -- Check output folders for QC
            if [ ! -d ${OutPath} ]; then
                mkdir -p ${OutPath} &> /dev/null
            fi
            # -- Define log folder
            RunQCLogFolder=${OutPath}/qclog
            if [ ! -d ${RunQCLogFolder} ]; then
                mkdir -p ${RunQCLogFolder}  &> /dev/null
            fi
            echo "    RunQCLogFolder: ${RunQCLogFolder}"
            echo "    Output path: ${OutPath}"
            echo ""
            
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
            # =-=-=-=-=- Start of BOLD QC Section =-=-=-=-=
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
            
            # -- Check if modality is BOLD
            if [ "$Modality" == "BOLD" ] ; then
                # ----------------------------------------------------------------------
                # --       Block of code to set BOLD numbers correctly
                # ----------------------------------------------------------------------
                #
                #
                # -- Check if both batch and bolds are specified for QC and if yes read batch explicitly
                if [[ ! -z ${SessionBatchFile} ]]; then
                    echo "  ---> For ${CASE} searching for BOLD tags in batch file ${SessionBatchFile} ... "; echo ""
                    unset BOLDS BOLDLIST
                    if [[ -f ${SessionBatchFile} ]]; then
                        if [ "${hcp_filename}" == "userdefined" ]; then
                            output="name"
                        fi
                        # For debugging
                        echo "   gmri batch_tag2namekey filename="${SessionBatchFile}" subjid="${CASE}" bolds="${BOLDSBATCH}" prefix="" output="${output}" | grep "BOLDS:" | sed 's/BOLDS://g'"
                        BOLDS=`gmri batch_tag2namekey filename="${SessionBatchFile}" subjid="${CASE}" bolds="${BOLDSBATCH}" prefix="" output="${output}" | grep "BOLDS:" | sed 's/BOLDS://g'`
                        BOLDLIST="${BOLDS}"
                    else
                        echo " ERROR: Requested BOLD modality with a batch file but the batch file not found. Check your inputs!"; echo ""
                        exit 1
                    fi
                    if [[ ! -z ${BOLDLIST} ]]; then
                        echo "  ---> For ${CASE} referencing ${SessionBatchFile} to select BOLD runs using tag: ${BOLDSBATCH} "
                        echo "      ------------------------------------------ "
                        echo "      Selected BOLDs ---> ${BOLDS} "
                        echo "      ------------------------------------------ "
                        echo ""
                    else
                        echo " ERROR: BOLDS variable not set. Something went wrong for ${CASE}. Check your batch file inputs!"; echo ""
                        return 1
                    fi
                fi

                # -- Check if session_hcp is used
                if [ "$BOLDS" == "${SessAcqInfoFile}" ]; then
                    echo "---> ${SessAcqInfoFile} parameter file specified. Verifying presence of ${SessAcqInfoFile} before running QC on all BOLDs..."; echo ""
                    if [ -f ${SessionsFolder}/${CASE}/${SessAcqInfoFile} ]; then
                        # -- Stalling on some systems ---> BOLDCount=`more ${SessionsFolder}/${CASE}/${SessAcqInfoFile} | grep "bold" | grep -v "ref" | wc -l`
                        BOLDCount=`grep "bold" ${SessionsFolder}/${CASE}/${SessAcqInfoFile}  | grep -v "ref" | wc -l`
                        rm ${SessionsFolder}/${CASE}/BOLDNumberTmp.txt &> /dev/null
                        COUNTER=1; until [ $COUNTER -gt $BOLDCount ]; do echo "$COUNTER" >> ${SessionsFolder}/${CASE}/BOLDNumberTmp.txt; let COUNTER=COUNTER+1; done
                        # -- Stalling on some systems ---> BOLDS=`more ${SessionsFolder}/${CASE}/BOLDNumberTmp.txt`
                        BOLDS=`cat ${SessionsFolder}/${CASE}/BOLDNumberTmp.txt`
                        rm ${SessionsFolder}/${CASE}/BOLDNumberTmp.txt &> /dev/null
                        echo "---> Information file ${SessionsFolder}/${CASE}/${SessAcqInfoFile} found. Proceeding to run QC on the following BOLDs:"; echo ""; echo "${BOLDS}"; echo ""
                    else
                        echo "---> ERROR: ${SessionsFolder}/${CASE}/${SessAcqInfoFile} not found. Check presence of file or specify specific BOLDs via input parameter."; echo ""
                        exit 1
                    fi
                else
                    # -- Remove commas or pipes from BOLD input list if still present if using manual input
                    BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`
                fi

                if [ ${Overwrite} == "yes" ]; then
                    echo ""
                    echo " --- Note: Overwrite requested. "
                    for BOLD in $BOLDS
                    do
                        echo " --- Removing existing ${Modality} QC scene: ${OutPath}/${CASEName}.${Modality}.${BOLD}.* "
                        rm -f ${OutPath}/${CASEName}.${Modality}.${BOLD}.* &> /dev/null
                    done
                fi

                # ----------------------------------------------------------------------
                # -- Code block to run BOLD loop across BOLD runs
                # ----------------------------------------------------------------------
                #
                echo ""
                echo " ---> Looping through requested BOLDS: ${BOLDS}"
                echo ""
                for BOLD in ${BOLDS}; do

                    # -- Check if BOLD FC requested
                    if [[ ! -z ${BOLDfc} ]]; then
                        echo " --- Working on BOLD FC QC scene..."; echo ""
                        # Inputs
                        if [[ ${BOLDfc} == "pscalar" ]]; then
                            TemplateSceneFile="template_pscalar_${modality_lower}_qc.wb.scene"
                        fi
                        if [[ ${BOLDfc} == "pconn" ]]; then
                            TemplateSceneFile="template_pconn_${modality_lower}_qc.wb.scene"
                        fi
                        scenetemplatefolder="${TOOLS}/${QUNEXREPO}/qx_library/data/scenes/qc"
                        WorkingSceneFile="${CASEName}.${BOLDfc}.${Modality}.${BOLD}.QC.wb.scene"
                        # -- Rsync over template files for a given BOLD
                        Com1="rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/ &> /dev/null; rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/ &> /dev/null"
                        Com2="cp ${OutPath}/${TemplateSceneFile} ${OutPath}/${WorkingSceneFile} &> /dev/null"
                        ComQueue="$Com1; $Com2"
                        echo " --- Copied ${scenetemplatefolder}/${TemplateSceneFile} over to ${OutPath}"
                        runscene_BOLDfc
                        # -- Clean up prior conflicting scripts, generate script and set permissions
                        rm -f ${RunQCLogFolder}/${CASE}_ComQUEUE_${BOLDfc}_${Modality}_${BOLD}_${TimeStamp}.sh &> /dev/null
                        echo "$ComRunBoldQUEUE" >> ${RunQCLogFolder}/${CASE}_ComQUEUE_${BOLDfc}_${Modality}_${BOLD}_${TimeStamp}.sh
                        chmod 770 ${RunQCLogFolder}/${CASE}_ComQUEUE_${BOLDfc}_${Modality}_${BOLD}_${TimeStamp}.sh
                        # -- Run script
                        ${RunQCLogFolder}/${CASE}_ComQUEUE_${BOLDfc}_${Modality}_${BOLD}_${TimeStamp}.sh |& tee -a ${RunQCLogFolder}/QC_${CASE}_ComQUEUE_${BOLDfc}_${Modality}_${TimeStamp}.log
                        FinalLog="${RunQCLogFolder}/QC_${CASE}_ComQUEUE_${BOLDfc}_${Modality}_${TimeStamp}.log"
                        # only run completion check if file are missing for the previous run
                        if [ -z ${PreviousCompletionCheck} ] || [ ${PreviousCompletionCheck} == "fail" ]; then
                            completionCheck
                        fi
                    else

                    # -- Work on raw BOLD QC + TSNR
                        # -- Check if prefix is specified
                        if [[ ! -z "$BOLDPrefix" ]]; then
                            echo ""
                            echo ""
                            echo "  ---> Working on BOLD number: ${BOLD}"
                            echo ""
                            if [[ `echo ${BOLDPrefix} | grep '_'` ]]; then BOLD="${BOLDPrefix}${BOLD}"; else BOLD="${BOLDPrefix}_${BOLD}"; fi
                            echo "  --- BOLD Prefix specified. Appending to BOLD number: ${BOLD}"
                            echo ""
                        else
                            # -- Check if BOLD folder with the given number contains additional prefix info and return an exit code if yes
                            echo ""
                            NoBOLDDirPreffix=`ls -d ${HCPFolder}/MNINonLinear/Results/${BOLD}`
                            NoBOLDPreffix=`ls -d ${HCPFolder}/MNINonLinear/Results/${BOLD} | sed 's:/*$::' | sed 's:.*/::'`
                            if [[ ! -z ${NoBOLDDirPreffix} ]]; then
                                echo " --- Note: A directory with the BOLD number is found but containing a prefix, yet no prefix was specified: "
                                echo "           ---> ${NoBOLDDirPreffix}"
                                echo ""
                                echo " --- Setting BOLD prefix to: ${NoBOLDPreffix}"
                                echo ""
                                echo " --- If this is not correct please re-run with correct --boldprefix flag to ensure correct BOLDs are specified."
                                echo ""
                                BOLD=${NoBOLDPreffix}
                            fi
                        fi

                        BOLDRoot="MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}"

                        # -- Check if BOLD exists and skip if not it does not
                        if [[ ! -f ${HCPFolder}/${BOLDRoot}.dtseries.nii ]]; then
                            echo ""
                            echo "---> ERROR: BOLD data specified for BOLD ${BOLD} not found: "
                            echo "          ---> ${HCPFolder}/${BOLDRoot}.dtseries.nii "
                            echo ""
                            echo "---> Check presence of your inputs for ${CASE} and BOLD ${BOLD} and re-run! Proceeding to next BOLD run."
                            echo ""
                            CompletionCheck="fail"
                        else
                            # -- Generate QC statistics for a given BOLD
                            echo "---> Specified BOLD data found. Generating QC statistics commands for BOLD ${BOLD} on ${CASE}..."
                            echo ""
                            # Check if SNR only requested
                            if [ "$SNROnly" == "yes" ]; then 
                                runsnr_BOLD
                            else
                                # -- Check if running defaults w/o UserSceneFile
                                if [ -z "$UserSceneFile" ] && [ "$OmitDefaults" == 'no' ] && [ "$RunQCCustom" != "yes" ]; then
                                    # Inputs
                                    Modality="BOLD"
                                    TemplateSceneFile="template_${modality_lower}_qc.wb.scene"
                                    scenetemplatefolder="${TOOLS}/${QUNEXREPO}/qx_library/data/scenes/qc"
                                    WorkingSceneFile="${CASEName}.${Modality}.${BOLD}.QC.wb.scene"
                                    # -- Rsync over template files for a given BOLD
                                    runsnr_BOLD
                                    Com1="rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/ &> /dev/null; rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/ &> /dev/null"
                                    Com2="cp ${OutPath}/${TemplateSceneFile} ${OutPath}/${WorkingSceneFile} &> /dev/null"
                                    Com3="sed -i -e 's|DUMMYXAXISMAX|$xmax|g' ${OutPath}/${WorkingSceneFile}"
                                    Com4="sed -i -e 's|DUMMYYAXISMAX|$ymax|g' ${OutPath}/${WorkingSceneFile}"
                                    Com5="sed -i -e 's|DUMMYYAXISMIN|$ymin|g' ${OutPath}/${WorkingSceneFile}"
                                    ComQueue="$Com1; $Com2; $Com3; $Com4; $Com5"
                                    runscene_BOLD
                                    # -- Clean up prior conflicting scripts, generate script and set permissions
                                    rm -f ${RunQCLogFolder}/${CASEName}_ComQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh &> /dev/null
                                    echo "$ComRunBoldQUEUE" >> ${RunQCLogFolder}/${CASEName}_ComQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh
                                    chmod 770 ${RunQCLogFolder}/${CASEName}_ComQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh
                                    # -- Run script
                                    ${RunQCLogFolder}/${CASEName}_ComQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh |& tee -a ${RunQCLogFolder}/QC_${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.log
                                    FinalLog="${RunQCLogFolder}/QC_${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.log"
                                    # only run completion check if file are missing for the previous run
                                    if [ -z ${PreviousCompletionCheck} ] || [ ${PreviousCompletionCheck} == "fail" ]; then
                                        completionCheck
                                    fi
                                fi
                            fi
                            # -- Check if custom QC was specified
                            if [ "$RunQCCustom" == "yes" ]; then
                                runsnr_BOLD
                                for TemplateSceneFile in ${CustomTemplateSceneFiles}; do
                                    WorkingSceneFile="${CASEName}.${Modality}.${BOLD}.${TemplateSceneFile}"
                                    DummyVariable_Check
                                    # -- Rsync over template files for a given BOLD
                                    Com1="rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/ &> /dev/null; rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/ &> /dev/null"
                                    Com2="cp ${OutPath}/${TemplateSceneFile} ${OutPath}/${WorkingSceneFile} &> /dev/null"
                                    ComQueue="$Com1; $Com2"
                                    runscene_BOLD
                                    CustomRunQUEUE=${ComRunBoldQUEUE}
                                    # -- Clean up prior conflicting scripts, generate script and set permissions
                                    rm -f ${RunQCLogFolder}/${CASEName}_CustomRunQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh &> /dev/null
                                    echo "$CustomRunQUEUE" >> ${RunQCLogFolder}/${CASEName}_CustomRunQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh
                                    chmod 770 ${RunQCLogFolder}/${CASEName}_CustomRunQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh
                                    # -- Run script
                                    ${RunQCLogFolder}/${CASEName}_CustomRunQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh |& tee -a ${RunQCLogFolder}/QC_${CASEName}_CustomRunQUEUE_${Modality}_${TimeStamp}.log
                                    FinalLog="${RunQCLogFolder}/QC_${CASEName}_CustomRunQUEUE_${Modality}_${TimeStamp}.log"
                                done
                                # only run completion check if file are missing for the previous run
                                if [ -z ${PreviousCompletionCheck} ] && [ ${PreviousCompletionCheck} == "fail" ]; then
                                    completionCheck
                                fi
                            fi
                        fi
                    fi
                done
                #
                # End of Code block to run BOLD loop across BOLD runs 
                # ----------------------------------------------------------------------
            fi
            
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
            # =-=-=-=-=-=- End of BOLD QC Section =-=-=-=-=
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
            # =-=-= remaining modalities (i.e. T1w, T2w, Myelin or DWI) =-=
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
            
            if [ "$Modality" != "BOLD" ]; then
            
                # -- Check if running defaults w/o UserSceneFile
                if [ -z "$UserSceneFile" ] && [ "$OmitDefaults" == 'no' ]; then
                    # -- Setup naming conventions before generating scene
                    Com1="rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/ &> /dev/null; rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/ &> /dev/null"
                    Com2="cp ${OutPath}/${TemplateSceneFile} ${OutPath}/${WorkingSceneFile}"
                    Com3="sed -i -e 's|DUMMYPATH|$HCPFolder|g' ${OutPath}/${WorkingSceneFile}" 
                    Com4="sed -i -e 's|DUMMYCASE|$CASEName|g' ${OutPath}/${WorkingSceneFile}"
                    # -------------------------------------------
                    # -- General QC
                    # -------------------------------------------
                    
                    # -- Perform checks if modality is general
                    if [ "$Modality" == "general" ]; then
                        GeneralPathCheck="${SessionsFolder}/${CASE}/${GeneralSceneDataPath}/${GeneralSceneDataFile}"
                        # -- Check if Preprocessed T1w files are present
                        if [ ! -f ${GeneralPathCheck} ]; then
                            echo ""
                            echo "---> ERROR: Data requested not found: "
                            echo "           ---> ${GeneralPathCheck} "
                            echo ""
                            echo "Check presence of your inputs and re-run!"
                            CompletionCheck="fail"
                            echo ""
                            return 1
                        else
                            echo ""
                            echo "---> Data inputs found: ${GeneralPathCheck}"
                            echo ""
                            # -- Setup naming conventions for general inputs before generating scene
                            Com4a="sed -i -e 's|DUMMYIMAGEPATH|$SessionsFolder/$CASE/$GeneralSceneDataPath|g' ${OutPath}/${WorkingSceneFile}"
                            Com4b="sed -i -e 's|DUMMYIMAGEFILE|$GeneralSceneDataFile|g' ${OutPath}/${WorkingSceneFile}"
                            Com4="$Com4; $Com4a; $Com4b"
                        fi
                    fi
                    
                    # -------------------------------------------
                    # -- T1w QC
                    # -------------------------------------------
                    
                    # -- Perform checks if modality is T1w
                    if [ "$Modality" == "T1w" ]; then
                        # -- Check if Preprocessed T1w files are present
                        if [ ! -f ${HCPFolder}/MNINonLinear/T1w_restore.nii.gz ]; then
                            echo ""
                            echo "---> ERROR: Preprocessed T1w data not found: "
                            echo "           ---> ${HCPFolder}/MNINonLinear/T1w_restore.nii.gz "
                            echo ""
                            echo "Check presence of your T1w inputs and re-run!"
                            CompletionCheck="fail"
                            echo ""
                            return 1
                        else
                            echo ""
                            echo "---> T1w inputs found: ${HCPFolder}/MNINonLinear/T1w_restore.nii.gz"
                            echo ""
                        fi
                    fi
                    
                    # -------------------------------------------
                    # -- T2w QC
                    # -------------------------------------------
                    
                    # -- Perform checks if modality is T2w
                    if [ "$Modality" == "T2w" ]; then
                        # -- Check if T2w is found in the ${SessAcqInfoFile} mapping file
                        T2wCheck=`cat ${SessionsFolder}/${CASE}/${SessAcqInfoFile} | grep "T2w"`
                        if [[ -z $T2wCheck ]]; then
                            echo ""
                            echo "---> ERROR: T2w QC requested but T2w mapping in ${SessionsFolder}/${CASE}/${SessAcqInfoFile} not detected. Check your data and re-run if needed."
                            CompletionCheck="fail"
                            echo ""
                            return 1
                        else
                            echo ""
                            echo "---> T2w mapping found: ${SessionsFolder}/${CASE}/${SessAcqInfoFile}. Checking for T2w data next..."
                            echo ""
                            # -- If ${SessAcqInfoFile} mapping file present check if Preprocessed T2w files are present
                            if [ ! -f ${HCPFolder}/MNINonLinear/T2w_restore.nii.gz ]; then
                                echo ""
                                echo "---> ERROR: Preprocessed T2w data not found: "
                                echo "           ---> ${HCPFolder}/MNINonLinear/T2w_restore.nii.gz "
                                echo ""
                                echo "Check presence of your T2w inputs and re-run!"
                                CompletionCheck="fail"
                                echo ""
                                return 1
                            else
                                echo ""
                                echo "---> T2w inputs found: ${HCPFolder}/MNINonLinear/T2w_restore.nii.gz"
                                echo ""
                            fi
                        fi
                    fi
                    
                    # -------------------------------------------
                    # -- Myelin QC
                    # -------------------------------------------
                    
                    # -- Perform checks if modality is Myelin
                    if [ "$Modality" == "Myelin" ]; then
                        # -- Check if Preprocessed Myelin files are present
                        if [ ! -f ${HCPFolder}/MNINonLinear/${CASEName}.L.SmoothedMyelinMap.164k_fs_LR.func.gii ] || [ ! -f ${HCPFolder}/MNINonLinear/${CASEName}.R.SmoothedMyelinMap.164k_fs_LR.func.gii ]; then
                            echo ""
                            echo "---> ERROR: Preprocessed Smoothed Myelin data not found: "
                            echo "           ---> ${HCPFolder}/MNINonLinear/${CASEName}.*.SmoothedMyelinMap.164k_fs_LR.func.gii  "
                            echo ""
                            echo "---- Check presence of your Myelin inputs and re-run!"
                            CompletionCheck="fail"
                            echo ""
                            return 1
                        else
                            echo ""
                            echo "---> Myelin L hemisphere input found: ${HCPFolder}/MNINonLinear/${CASEName}.L.SmoothedMyelinMap.164k_fs_LR.func.gii "
                            echo "---> Myelin R hemisphere input found: ${HCPFolder}/MNINonLinear/${CASEName}.R.SmoothedMyelinMap.164k_fs_LR.func.gii "
                            echo ""
                        fi
                    fi
                    
                    # -------------------------------------------
                    # -- DWI QC
                    # -------------------------------------------
                    
                    # -- Perform checks if modality is DWI
                    if [ "$Modality" == "DWI" ]; then
                        unset "$DWIName" >/dev/null 2>&1
                        DWIName="${DWIData}"
                        NoDiffBrainMask="${HCPFolder}/T1w/${DWIPath}/nodif_brain_mask.nii.gz"

                        # -- Check if Preprocessed DWI files are present
                        if [ ! -f ${HCPFolder}/T1w/${DWIPath}/${DWIName}.nii.gz ]; then
                            echo ""
                            echo "---> ERROR: Preprocessed DWI data not found: "
                            echo "           ---> ${HCPFolder}/T1w/${DWIPath}/${DWIName}.nii.gz "
                            echo ""
                            echo "---> Check presence of your DWI inputs and re-run!"
                            echo ""
                            exit 1
                        else
                            echo ""
                            echo "---> DWI inputs found: ${HCPFolder}/T1w/${DWIPath}/${DWIName}.nii.gz "
                            echo ""
                            # -- Split the data and setup 1st and 2nd volumes for visualization
                            Com4a="fslsplit ${HCPFolder}/T1w/${DWIPath}/${DWIName}.nii.gz ${HCPFolder}/T1w/${DWIPath}/${DWIName}_split -t"
                            Com4b="fslmaths ${HCPFolder}/T1w/${DWIPath}/${DWIName}_split0000.nii.gz -mul ${NoDiffBrainMask} ${HCPFolder}/T1w/${DWIPath}/data_frame1_brain"
                            Com4c="fslmaths ${HCPFolder}/T1w/${DWIPath}/${DWIName}_split0010.nii.gz -mul ${NoDiffBrainMask} ${HCPFolder}/T1w/${DWIPath}/data_frame10_brain"
                            # -- Clean split volumes
                            Com4d="rm -f ${HCPFolder}/T1w/${DWIPath}/${DWIName}_split* &> /dev/null"
                            # -- Setup naming conventions for DWI before generating scene
                            Com4e="sed -i -e 's|DUMMYDWIPATH|$DWIPath|g' ${OutPath}/${WorkingSceneFile}"
                            Com4="$Com4; $Com4a; $Com4b; $Com4c; $Com4d; $Com4e"
                            # --------------------------------------------------
                            # -- Check if DTIFIT and BEDPOSTX flags are set
                            # --------------------------------------------------
                            # -- If dtifit qc is selected then generate dtifit scene
                            if [ "$DtiFitQC" == "yes" ]; then
                                if [ ! -z "$UserSceneFile" ]; then
                                    WorkingDTISceneFile="${CASEName}.${Modality}.dtifit.${UserSceneFile}"
                                else
                                    WorkingDTISceneFile="${CASEName}.${Modality}.dtifit.QC.wb.scene"
                                fi
                                echo ""
                                echo "---> QC for FSL dtifit requested. Checking if dtifit was completed..."
                                echo ""
                                # -- Check if dtifit is done
                                minimumfilesize=100000
                                if [ -a ${HCPFolder}/T1w/${DWIPath}/dti_FA.nii.gz ]; then 
                                    actualfilesize=$(wc -c <${HCPFolder}/T1w/${DWIPath}/dti_FA.nii.gz)
                                else
                                    actualfilesize="0"
                                fi
                                if [ $(echo "$actualfilesize" | bc) -gt $(echo "$minimumfilesize" | bc) ]; then
                                    echo ""
                                    echo "    ---> FSL dtifit results found here: ${HCPFolder}/T1w/${DWIPath}/"
                                    echo ""
                                    # -- Replace DWI scene specifications with the dtifit results
                                    Com4g1="cp ${OutPath}/${WorkingSceneFile} ${OutPath}/${WorkingDTISceneFile}"
                                    Com4g2="sed -i -e 's|1st frame|dti FA|g' ${OutPath}/${WorkingDTISceneFile}"
                                    Com4g3="sed -i -e 's|10th frame|dti L3|g' ${OutPath}/${WorkingDTISceneFile}"
                                    Com4g4="sed -i -e 's|data_frame1_brain.nii.gz|dti_FA.nii.gz|g' ${OutPath}/${WorkingDTISceneFile}"
                                    Com4g5="sed -i -e 's|data_frame10_brain.nii.gz|dti_L3.nii.gz|g' ${OutPath}/${WorkingDTISceneFile}"
                                    # -- Combine dtifit commands
                                    Com4g="$Com4g1; $Com4g2; $Com4g3; $Com4g4; $Com4g5"
                                    # -- Combine DWI commands
                                    Com4="$Com4; $Com4g"
                                else
                                    echo "---> ERROR: FSL dtifit not found for $CASEName. Skipping dtifit QC request for upcoming QC calls. Check dtifit results: "
                                    echo "           ---> ${HCPFolder}/T1w/${DWIPath}/ "
                                fi
                            fi
                            # -- If bedpostx qc is selected then generate bedpostx scene
                            if [ "$BedpostXQC" == "yes" ]; then
                                if [ ! -z "$UserSceneFile" ]; then
                                    WorkingBedpostXSceneFile="${CASEName}.${Modality}.bedpostx.${UserSceneFile}"
                                else
                                    WorkingBedpostXSceneFile="${CASEName}.${Modality}.bedpostx.QC.wb.scene"
                                fi
                                echo ""
                                echo "---> QC for FSL BedpostX requested. Checking if BedpostX was completed..."
                                echo ""
                                # -- Check if the file even exists
                                if [ -f ${HCPFolder}/T1w/Diffusion.bedpostX/merged_f1samples.nii.gz ]; then
                                    # -- Set file sizes to check for completion
                                    minimumfilesize=20000000
                                    actualfilesize=`wc -c < ${HCPFolder}/T1w/Diffusion.bedpostX/merged_f1samples.nii.gz` > /dev/null 2>&1          
                                    filecount=`ls ${HCPFolder}/T1w/Diffusion.bedpostX/merged_*nii.gz | wc | awk {'print $1'}`
                                    # -- Then check if run is complete based on file count
                                    if [ "$filecount" == 9 ]; then
                                        # -- Then check if run is complete based on file size
                                        if [ $(echo "$actualfilesize" | bc) -ge $(echo "$minimumfilesize" | bc) ]; then > /dev/null 2>&1
                                            echo ""
                                            echo "    ---> BedpostX outputs found and completed here: ${HCPFolder}/T1w/Diffusion.bedpostX/"
                                            echo ""
                                            # -- Replace DWI scene specifications with the dtifit results
                                            Com4h1="cp ${OutPath}/${WorkingSceneFile} ${OutPath}/${WorkingBedpostXSceneFile}"
                                            Com4h2="sed -i -e 's|1st frame|mean d diffusivity|g' ${OutPath}/${WorkingBedpostXSceneFile}"
                                            Com4h3="sed -i -e 's|10th frame|mean f anisotropy|g' ${OutPath}/${WorkingBedpostXSceneFile}"
                                            Com4h4="sed -i -e 's|$DWIPath/data_frame1_brain.nii.gz|Diffusion.bedpostX/mean_dsamples.nii.gz|g' ${OutPath}/${WorkingBedpostXSceneFile}"
                                            Com4h5="sed -i -e 's|$DWIPath/data_frame10_brain.nii.gz|Diffusion.bedpostX/mean_fsumsamples.nii.gz|g' ${OutPath}/${WorkingBedpostXSceneFile}"
                                            # -- combine BedpostX commands
                                            Com4h="$Com4h1; $Com4h2; $Com4h3; $Com4h4; $Com4h5"
                                            # -- Combine BedpostX commands
                                            Com4="$Com4; $Com4h"
                                        fi
                                    fi
                                else 
                                    echo ""
                                    echo "---> ERROR: FSLBedpostX outputs missing or incomplete for $CASEName. Skipping BedpostX QC request for upcoming QC calls. Check BedpostX results: "
                                    echo "           ---> ${HCPFolder}/T1w/Diffusion.bedpostX/ "
                                    echo ""
                                    BedpostXQC="no"
                                fi
                            fi
                            # -- If eddy qc is selected then create hard link to eddy qc pdf and print the qc_mot_abs for each subjec to a report
                            if [ "$EddyQCStats" == "yes" ]; then
                                echo ""
                                echo "---> QC Stats for FSL EDDY requested. Checking if EDDY QC was completed..."
                                echo ""
                                # -- Then check if eddy qc is completed
                                if [ -f ${HCPFolder}/Diffusion/eddy/eddy_unwarped_images.qc/qc.pdf ]; then
                                    echo "    ---> EDDY QC outputs found and completed here: "; echo ""
                                        # -- Regenerate the qc_mot_abs if missing
                                        if [ -f ${HCPFolder}/Diffusion/eddy/eddy_unwarped_images.qc/${CASEName}_qc_mot_abs.txt ]; then
                                            echo "        ${HCPFolder}/Diffusion/eddy/eddy_unwarped_images.qc/${CASEName}_qc_mot_abs.txt"
                                        else
                                            echo "        ${HCPFolder}/Diffusion/eddy/eddy_unwarped_images.qc/${CASEName}_qc_mot_abs.txt not found. Regenerating... "
                                            cat ${HCPFolder}/Diffusion/eddy/eddy_unwarped_images.qc/qc.json | grep "qc_mot_abs" | sed -n -e 's/^.*: //p' | tr -d ',' >> ${HCPFolder}/Diffusion/eddy/eddy_unwarped_images.qc/${CASEName}_qc_mot_abs.txt
                                        fi
                                    echo ""
                                    echo "        ${HCPFolder}/Diffusion/eddy/eddy_unwarped_images.qc/qc.pdf"
                                    echo ""
                                    # -- Run links and printing to reports
                                    ln ${HCPFolder}/Diffusion/eddy/eddy_unwarped_images.qc/qc.pdf ${OutPath}/${CASEName}.${Modality}.eddy.QC.pdf
                                    printf "${HCPFolder}/Diffusion/eddy/eddy_unwarped_images.qc/${CASEName}_qc_mot_abs.txt\n" >> ${OutPath}/EddyQCReport_qc_mot_abs_${TimeStampRunQC}.txt
                                    
                                    echo "---> Completed EDDY QC stats for ${CASEName}"
                                    echo "    Final report can be found here: ${OutPath}/EddyQCReport_qc_mot_abs_${TimeStampRunQC}.txt"; echo ""
                                else
                                    echo ""
                                    echo "---> ERROR: EDDY QC outputs missing or incomplete for $CASEName. Skipping EDDY QC request. Check EDDY results."
                                    echo ""
                                fi
                            fi
                        fi
                    fi
                
                    # -------------------------------------------
                    # -- Additional steps
                    # -------------------------------------------
                    
                    # -- Add timestamp to the scene
                    Com5="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingSceneFile}"
                    PNGName="${WorkingSceneFile}.png"
                    ComRunPngName="sed -i -e 's|DUMMYPNGNAME|$PNGName|g' ${OutPath}/${WorkingSceneFile}"
                    Com5="$Com5; $ComRunPngName"
                    # -- Output image of the scene
                    Com6="wb_command -show-scene ${OutPath}/${WorkingSceneFile} 1 ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png 1194 539 > /dev/null 2>&1"
                    echo ""
                    echo "---> Running PNG extraction using the following command..."
                    echo "      $Com6"
                    echo ""
                    
                    # -- Check if dtifit is requested
                    if [ "$DtiFitQC" == "yes" ]; then
                        Com5a="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingDTISceneFile}"
                        PNGNameDtiFit="${WorkingDTISceneFile}.png"
                        ComRunPngNameDtiFit="sed -i -e 's|DUMMYPNGNAME|$PNGName|g' ${OutPath}/${WorkingDTISceneFile}"
                        Com5b="wb_command -show-scene ${OutPath}/${CASEName}.${Modality}.dtifit.QC.wb.scene 1 ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.png 1194 539 > /dev/null 2>&1"
                        Com5="$Com5; $ComRunPngNameDtiFit; $Com5a; $Com5b"
                    fi
                    # -- Check of bedpostx QC is requested
                    if [ "$BedpostXQC" == "yes" ]; then
                        Com5c="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingBedpostXSceneFile}"
                        PNGNameBedpostX="${WorkingDTISceneFile}.png"
                        ComRunPngNameBedpostX="sed -i -e 's|DUMMYPNGNAME|$PNGName|g' ${OutPath}/${WorkingDTISceneFile}"
                        Com5d="wb_command -show-scene ${OutPath}/${CASEName}.${Modality}.bedpostx.QC.wb.scene 1 ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.png 1194 539 > /dev/null 2>&1"
                        Com5="$Com5; $ComRunPngNameBedpostX; $Com5c; $Com5d"
                    fi
                    
                    # -- Clean templates and files for next session
                    Com7="rm ${OutPath}/${WorkingSceneFile}-e &> /dev/null"
                    Com9="rm -f ${OutPath}/data_split*"
                    
                    # -------------------------------------------
                    # -- Zip QC Scenes
                    # -------------------------------------------
                    
                    # -- Generate Scene Zip File if set to YES
                    if [ "$SceneZip" == "yes" ]; then
                        echo ""
                        echo "---> Scene zip set to: $SceneZip. Relevant scene files will be zipped using the following base folder:" 
                        echo "    ${HCPFolder}"
                        echo ""
                        echo "---> The zip file will be saved to: "
                        echo "    ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip "
                        echo ""
                        if [[ ${Modality} == "general" ]]; then
                             echo "---> ${Modality} scene type requested. Outputs will be set relative to: "
                             echo "    ${SessionsFolder}/${CASE}"
                             echo ""
                             RemoveScenePath="${SessionsFolder}/${CASE}"
                             Com10a="cp ${OutPath}/${WorkingSceneFile} ${SessionsFolder}/${CASE}/"
                             Com10b="rm ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip  &> /dev/null"
                             Com10c="sed -i -e 's|$RemoveScenePath|.|g' ${SessionsFolder}/${CASE}/${WorkingSceneFile}" 
                             Com10d="cd ${OutPath}; wb_command -zip-scene-file ${SessionsFolder}/${CASE}/${WorkingSceneFile} ${WorkingSceneFile}.${TimeStamp} ${WorkingSceneFile}.${TimeStamp}.zip"
                             echo ""
                             echo "---> Running PNG extraction using the following command..."
                             echo "      $Com10d"
                             echo ""
                             Com10e="echo ${SessionsFolder}/${CASE}/${WorkingSceneFile}"
                             Com10f="mkdir -p ${SessionsFolder}/${CASE}/qc &> /dev/null"
                             Com10g="cp ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ${SessionsFolder}/${CASE}/qc/"
                             Com10="$Com10a; $Com10b; $Com10c; $Com10d; $Com10e; $Com10f; $Com10g"
                        else
                             echo "---> ${Modality} scene type requested. Outputs will be set relative to: "
                             echo "    ${HCPFolder}"
                             echo ""
                             RemoveScenePath="${HCPFolder}"
                             Com10a="cp ${OutPath}/${WorkingSceneFile} ${HCPFolder}/"
                             Com10b="rm ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip  &> /dev/null"
                             Com10c="sed -i -e 's|$RemoveScenePath|.|g' ${HCPFolder}/${WorkingSceneFile}" 
                             Com10d="cd ${OutPath}; wb_command -zip-scene-file ${HCPFolder}/${WorkingSceneFile} ${WorkingSceneFile}.${TimeStamp} ${WorkingSceneFile}.${TimeStamp}.zip -base-dir ${HCPFolder}"
                             Com10e="echo ${HCPFolder}/${WorkingSceneFile}"
                             Com10f="mkdir -p ${HCPFolder}/qc &> /dev/null"
                             Com10g="cp ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ${HCPFolder}/qc/"
                             Com10="$Com10a; $Com10b; $Com10c; $Com10d; $Com10e; $Com10f; $Com10g"
                        fi
                    fi

                    # -- Generate Zip files for dtifit scenes if requested
                    if [ "$DtiFitQC" == "yes" ] && [ "$SceneZip" == "yes" ]; then
                        echo ""
                        echo "---> Scene zip set to: $SceneZip. DtiFitQC set to: $DtiFitQC. Relevant scene files will be zipped using the following base folder:" 
                        echo "    ${HCPFolder}"
                        echo ""
                        echo "---> The zip file will be saved to: "
                        echo "    ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.zip"
                        echo ""
                        RemoveScenePath="${HCPFolder}"
                        Com11a="cp ${OutPath}/${WorkingDTISceneFile} ${HCPFolder}/"
                        Com11b="rm ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.zip &> /dev/null"
                        Com11c="sed -i -e 's|$RemoveScenePath|.|g' ${HCPFolder}/${WorkingDTISceneFile}" 
                        Com11d="cd ${OutPath}; wb_command -zip-scene-file ${HCPFolder}/${WorkingDTISceneFile} ${WorkingDTISceneFile}.${TimeStamp} ${WorkingDTISceneFile}.${TimeStamp}.zip -base-dir ${HCPFolder}"
                        Com11e="rm ${HCPFolder}/${WorkingDTISceneFile}"
                        Com11f="mkdir -p ${HCPFolder}/qc &> /dev/null"
                        Com11g="cp ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.zip ${HCPFolder}/qc/"
                        Com11="$Com11a; $Com11b; $Com11c; $Com11d; $Com11e; $Com11f; $Com11g"
                    fi
                    # -- Generate Zip files for bedpostx scenes if requested
                    if [ "$BedpostXQC" == "yes" ] && [ "$SceneZip" == "yes" ]; then
                        echo ""
                        echo "---> Scene zip set to: $SceneZip. BedpostXQC set to: $BedpostXQC. Relevant scene files will be zipped using the following base folder:" 
                        echo "    ${HCPFolder}"
                        echo ""
                        echo "---> The zip file will be saved to: "
                        echo "    ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.zip"
                        echo ""
                        RemoveScenePath="${HCPFolder}"
                        Com12a="cp ${OutPath}/${WorkingBedpostXSceneFile} ${HCPFolder}/"
                        Com12b="rm ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.zip &> /dev/null"
                        Com12c="sed -i -e 's|$RemoveScenePath|.|g' ${HCPFolder}/${WorkingBedpostXSceneFile}" 
                        Com12d="cd ${OutPath}; wb_command -zip-scene-file ${HCPFolder}/${WorkingBedpostXSceneFile} ${WorkingBedpostXSceneFile}.${TimeStamp} ${WorkingBedpostXSceneFile}.${TimeStamp}.zip -base-dir ${HCPFolder}"
                        Com12e="rm ${HCPFolder}/${WorkingBedpostXSceneFile}"
                        Com12f="mkdir -p ${HCPFolder}/qc &> /dev/null"
                        Com12g="cp ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.zip ${HCPFolder}/qc/"
                        Com12="$Com12a; $Com12b; $Com12c; $Com12d; $Com12e; $Com12f; $Com12g"
                    fi
                    # -- Combine all the calls into a single command based on various specifications
                    if [ "$SceneZip" == "yes" ]; then
                        if [ "$DtiFitQC" == "no" ]; then
                            if [ "$BedpostXQC" == "no" ]; then
                                ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com9; $Com10"
                            else
                                ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com9; $Com10; $Com12"
                            fi
                        else
                            if [ "$BedpostXQC" == "yes" ]; then
                                ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com9; $Com10; $Com11; $Com12"
                            else
                                ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com9; $Com10; $Com11"
                            fi
                        fi
                    else
                        ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com9"
                    fi
                    # -- Clean up prior conflicting scripts, generate script and set permissions
                    rm -f "$RunQCLogFolder"/${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.sh &> /dev/null
                    echo "$ComQUEUE" >> "$RunQCLogFolder"/${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.sh
                    chmod 770 "$RunQCLogFolder"/${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.sh
                    # -- Run Job
                    "$RunQCLogFolder"/${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.sh |& tee -a ${RunQCLogFolder}/QC_${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.log
                    echo ""
                    FinalLog="${RunQCLogFolder}/QC_${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.log"
                    # only run completion check if file are missing for the previous run
                    if [ -z ${PreviousCompletionCheck} ] || [ ${PreviousCompletionCheck} == "fail" ]; then
                        completionCheck
                    fi
                fi
                
                # -- Check if custom QC was specified
                if [ "$RunQCCustom" == "yes" ]; then
                    echo ""
                    echo "====================== Process custom scenes: $RunQCCustom ============================="
                    echo ""
                    Customscenetemplatefolder="${StudyFolder}/processing/scenes/QC/${Modality}"
                    CustomTemplateSceneFiles=`ls ${StudyFolder}/processing/scenes/QC/${Modality}/*.scene | xargs -n 1 basename`
                    echo "$CustomTemplateSceneFiles"
                    scenetemplatefolder=${Customscenetemplatefolder}
                    for TemplateSceneFile in ${CustomTemplateSceneFiles}; do
                        DummyVariable_Check
                        WorkingSceneFile="${CASEName}.${Modality}.${TemplateSceneFile}"
                        RunQCCustom1="rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/ &> /dev/null; rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/ &> /dev/null"
                        RunQCCustom2="cp ${OutPath}/${TemplateSceneFile} ${OutPath}/${WorkingSceneFile}"
                        RunQCCustom3="sed -i -e 's|DUMMYPATH|$HCPFolder|g' ${OutPath}/${WorkingSceneFile}" 
                        RunQCCustom4="sed -i -e 's|DUMMYCASE|$CASEName|g' ${OutPath}/${WorkingSceneFile}"
                        # -- Add timestamp to the scene
                        RunQCCustom5="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingSceneFile}"
                        # -- Add scene name
                        PNGName="${WorkingSceneFile}.pzwng"
                        ComRunBoldPngNameGSMap="sed -i -e 's|DUMMYPNGNAME|$PNGName|g' ${OutPath}/${WorkingSceneFile}"
                        # -- Output image of the scene
                        RunQCCustom6="wb_command -show-scene ${OutPath}/${WorkingSceneFile} 1 ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png 1194 539"
                        # -- Clean templates and files for next session
                        RunQCCustom7="rm ${OutPath}/${WorkingSceneFile}-e &> /dev/null"
                        RunQCCustom9="rm -f ${OutPath}/data_split*"
                        CustomRunQUEUE="$RunQCCustom1; $RunQCCustom2; $RunQCCustom3; $RunQCCustom4; $RunQCCustom5; $ComRunBoldPngNameGSMap; $RunQCCustom6; $RunQCCustom7; $RunQCCustom9"
                        if [ "$SceneZip" == "yes" ]; then
                            echo ""
                            echo "---> Scene zip set to: $SceneZip. Relevant scene files will be zipped using the following base folder:" 
                            echo "    ${HCPFolder}"
                            echo ""
                            echo "---> The zip file will be saved to: "
                            echo "    ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip "
                            echo ""
                            RemoveScenePath="${HCPFolder}"
                            RunQCCustom10="cp ${OutPath}/${WorkingSceneFile} ${HCPFolder}/"
                            RunQCCustom11="rm ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip  &> /dev/null"
                            RunQCCustom12="sed -i -e 's|$RemoveScenePath|.|g' ${HCPFolder}/${WorkingSceneFile}" 
                            RunQCCustom13="cd ${OutPath}; wb_command -zip-scene-file ${HCPFolder}/${WorkingSceneFile} ${WorkingSceneFile}.${TimeStamp} ${WorkingSceneFile}.${TimeStamp}.zip -base-dir ${HCPFolder}"
                            RunQCCustom14="rm ${HCPFolder}/${WorkingSceneFile}"
                            RunQCCustom15="mkdir -p ${HCPFolder}/qc &> /dev/null"
                            RunQCCustom16="cp ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ${HCPFolder}/qc/"
                            CustomRunQUEUE="$RunQCCustom1; $RunQCCustom2; $RunQCCustom3; $RunQCCustom4; $RunQCCustom5; $ComRunBoldPngNameGSMap; $RunQCCustom6; $RunQCCustom7; $RunQCCustom9; $RunQCCustom10; $RunQCCustom11; $RunQCCustom12; $RunQCCustom13; $RunQCCustom14; $RunQCCustom15; $RunQCCustom16"
                        fi
                        # -- Clean up prior conflicting scripts, generate script and set permissions
                        rm -f "$RunQCLogFolder"/${CASEName}_CustomRunQUEUE_${Modality}_${TimeStamp}.sh &> /dev/null
                        echo "$CustomRunQUEUE" >> "$RunQCLogFolder"/${CASEName}_CustomRunQUEUE_${Modality}_${TimeStamp}.sh
                        chmod 770 "$RunQCLogFolder"/${CASEName}_CustomRunQUEUE_${Modality}_${TimeStamp}.sh
                        # -- Run Job
                        "$RunQCLogFolder"/${CASEName}_CustomRunQUEUE_${Modality}_${TimeStamp}.sh |& tee -a ${RunQCLogFolder}/QC_${CASEName}_CustomRunQUEUE_${Modality}_${TimeStamp}.log
                        FinalLog="${RunQCLogFolder}/QC_${CASEName}_CustomRunQUEUE_${Modality}_${TimeStamp}.log"
                        # only run completion check if file are missing for the previous run
                        if [ -z ${PreviousCompletionCheck} ] || [ ${PreviousCompletionCheck} == "fail" ]; then
                            completionCheck
                        fi
                    done
                fi
                # -- Check if user specific scene path was provided
                if [ ! -z "$UserSceneFile" ]; then
                    TemplateSceneFile"${UserSceneFile}"
                    DummyVariable_Check
                    WorkingSceneFile="${CASEName}.${Modality}.${UserSceneFile}"
                    RunQCUser1="rsync -aWH ${scenetemplatefolder}/* ${OutPath}/ &> /dev/null; rsync -aWH ${scenetemplatefolder}/* ${OutPath}/ &> /dev/null"
                    RunQCUser2="cp ${OutPath}/${TemplateSceneFile} ${OutPath}/${WorkingSceneFile}"
                    RunQCUser3="sed -i -e 's|DUMMYPATH|$HCPFolder|g' ${OutPath}/${WorkingSceneFile}" 
                    RunQCUser4="sed -i -e 's|DUMMYCASE|$CASEName|g' ${OutPath}/${WorkingSceneFile}"
                    # -- Add timestamp to the scene
                    RunQCUser5="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingSceneFile}"
                    # -- Add scene name
                    PNGName="${WorkingSceneFile}.png"
                    ComRunBoldPngNameGSMap="sed -i -e 's|DUMMYPNGNAME|$PNGName|g' ${OutPath}/${WorkingSceneFile}"
                    # -- Output image of the scene
                    RunQCUser6="wb_command -show-scene ${OutPath}/${WorkingSceneFile} 1 ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png 1194 539"
                    # -- Clean templates and files for next session
                    RunQCUser7="rm ${OutPath}/${WorkingSceneFile}-e &> /dev/null"
                    RunQCUser9="rm -f ${OutPath}/data_split*"
                    ComQUEUE="$RunQCUser1; $RunQCUser2; $RunQCUser3; $RunQCUser4; $RunQCUser5; $ComRunBoldPngNameGSMap; $RunQCUser6; $RunQCUser7; $RunQCUser9"
                    if [ "$SceneZip" == "yes" ]; then
                        echo "---> Scene zip set to: $SceneZip. Relevant scene files will be zipped using the following base folder:" 
                        echo "    ${HCPFolder}"
                        echo ""
                        echo "---> The zip file will be saved to: "
                        echo "    ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip "
                        echo ""
                        RemoveScenePath="${HCPFolder}"
                        RunQCUser10="cp ${OutPath}/${WorkingSceneFile} ${HCPFolder}/"
                        RunQCUser11="rm ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip  &> /dev/null"
                        RunQCUser12="sed -i -e 's|$RemoveScenePath|.|g' ${HCPFolder}/${WorkingSceneFile}" 
                        RunQCUser13="cd ${OutPath}; wb_command -zip-scene-file ${HCPFolder}/${WorkingSceneFile} ${WorkingSceneFile}.${TimeStamp} ${WorkingSceneFile}.${TimeStamp}.zip -base-dir ${HCPFolder}"
                        RunQCUser14="rm ${HCPFolder}/${WorkingSceneFile}"
                        RunQCUser15="mkdir -p ${HCPFolder}/qc &> /dev/null"
                        RunQCUser16="cp ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ${HCPFolder}/qc/"
                        ComQUEUE="$RunQCUser1; $RunQCUser2; $RunQCUser3; $RunQCUser4; $RunQCUser5; $ComRunBoldPngNameGSMap; $RunQCUser6; $RunQCUser7; $RunQCUser9; $RunQCUser10; $RunQCUser11; $RunQCUser12; $RunQCUser13; $RunQCUser14; $RunQCUser15; $RunQCUser16"
                    fi
                    # -- Clean up prior conflicting scripts, generate script and set permissions
                    rm -f "$RunQCLogFolder"/${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.sh &> /dev/null
                    echo "$ComQUEUE" >> "$RunQCLogFolder"/${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.sh
                    chmod 770 "$RunQCLogFolder"/${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.sh
                    # -- Run Job
                    "$RunQCLogFolder"/${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.sh |& tee -a ${RunQCLogFolder}/QC_${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.log
                    FinalLog="${RunQCLogFolder}/QC_${CASEName}_ComQUEUE_${Modality}_${TimeStamp}.log"
                    # only run completion check if file are missing for the previous run
                    if [ -z ${PreviousCompletionCheck} ] || [ ${PreviousCompletionCheck} == "fail" ]; then
                        completionCheck
                    fi
                fi
            fi
        fi
    done
    finalReport
}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@

