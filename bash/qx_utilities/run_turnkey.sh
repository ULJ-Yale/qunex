#!/bin/bash

# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

###################################################################
# Variables that will be passed as container launch in XNAT:
###################################################################
#
# paramfile (file with processing parameters)
# mappingfile (file for mapping into desired file structure; e.g. hcp)
# xnataccsessionid (Imaging Session Accession ID)
# xnatsessionlabels (Imaging Session Label)
# xnatprojectid (Project ID of the Imaging Session)
# xnatsubjectid (Subject ID of the Imaging session)
# xnathost (URL of the xnat host)
# xnatuser (xnat user id)
# xnatpass (xnat user password)
#
##########################################################
# Assumes $TOOLS and $QUNEXREPO are defined
##########################################################

# version
QuNexVer=`cat ${TOOLS}/${QUNEXREPO}/VERSION.md`

# source $TOOLS/$QUNEXREPO/env/qunex_environment.sh &> /dev/null
# $TOOLS/$QUNEXREPO/env/qunex_environment.sh &> /dev/null

QuNexTurnkeyWorkflow="create_study map_raw_data import_dicom run_qc_rawnii create_session_info setup_hcp create_batch export_hcp hcp_pre_freesurfer hcp_freesurfer hcp_post_freesurfer run_qc_t1w run_qc_t2w run_qc_myelin hcp_fmri_volume hcp_fmri_surface run_qc_bold hcp_diffusion run_qc_dwi dwi_legacy_gpu dwi_eddy_qc run_qc_dwi_eddy dwi_dtifit run_qc_dwi_dtifit dwi_bedpostx_gpu run_qc_dwi_process run_qc_dwi_bedpostx dwi_probtrackx_dense_gpu dwi_pre_tractography dwi_parcellate dwi_seed_tractography_dense run_qc_custom map_hcp_data create_bold_brain_masks compute_bold_stats create_stats_report extract_nuisance_signal preprocess_bold preprocess_conc general_plot_bold_timeseries parcellate_bold parcellate_bold compute_bold_fc_seed compute_bold_fc_gbc run_qc_bold_fc"

QCPlotElements="type=stats|stats>plotdata=fd,imageindex=1>plotdata=dvarsme,imageindex=1;type=signal|name=V|imageindex=1|maskindex=1|colormap=hsv;type=signal|name=WM|imageindex=1|maskindex=1|colormap=jet;type=signal|name=GM|imageindex=1|maskindex=1;type=signal|name=GM|imageindex=2|use=1|scale=3"

SupportedAcceptanceTestSteps="hcp_pre_freesurfer hcp_freesurfer hcp_post_freesurfer hcp_fmri_volume hcp_fmri_surface"

QuNexTurnkeyClean="hcp_fmri_volume"

# ------------------------------------------------------------------------------
# -- General usage
# ------------------------------------------------------------------------------

usage() {
    cat << EOF
``run_turnkey``

This function implements QuNex Suite workflows as a turnkey function.
It operates on a local server or cluster or within the XNAT Docker engine.

Parameters:
    --turnkeytype (str, default 'xnat'):
        Specify type turnkey run. Options are: 'local' or 'xnat'.

    --path (str, default '/output/xnatprojectid'):
        Path where study folder is located. If empty default is for XNAT run.

    --sessions (str):
        Sessions to run locally on the file system if not an XNAT run.

    --sessionids (str):
        Comma separated list of session IDs to select for a run via gMRI engine
        from the batch file.

    --turnkeysteps (str):
        Specify specific turnkey steps you wish to run.

    --turnkeycleanstep (str):
        Specify specific turnkey steps you wish to clean up intermediate files
        for.

    --paramfile (str):
        File with pre-configured header specifying processing parameters.

        Note: This file needs to be created *manually* prior to starting
        run_turnkey.

        - IF executing a 'local' run then provide the absolute path to the file
          on the local file system:
          If no file name is given then by default QuNex run_turnkey will exit
          with an error.
        - IF executing a run via the XNAT WebUI then provide the name of the
          file. This file should be created and uploaded manually as the
          project-level resource on XNAT.

    --mappingfile (str):
        File for mapping NIFTI files into the desired QuNex file structure (e.g.
        'hcp', 'fMRIPrep' etc.)

        Note: This file needs to be created *manually* prior to starting
        run_turnkey.

        - IF executing a 'local' run then provide the absolute path to the file
          on the local file system:
          If no file name is given then by default QuNex run_turnkey will exit
          with an error.
        - IF executing a run via the XNAT WebUI then provide the name of the
          file. This file should be created and uploaded manually as the
          project-level resource on XNAT.

    --acceptancetest (str, default 'no'):
        Specify if you wish to run a final acceptance test after each unit of
        processing.

        If --acceptancetest='yes', then --turnkeysteps must be provided and will
        be executed first.

        If --acceptancetest='<turnkey_step>', then acceptance test will be run
        but step won't be executed.

    --xnathost (str):
        Specify the XNAT site hostname URL to push data to.

    --xnatprojectid (str):
        Specify the XNAT site project id. This is the Project ID in XNAT and not
        the Project Title.

    --xnatuser (str):
        Specify XNAT username.

    --xnatpass (str):
        Specify XNAT password.

    --xnatsubjectid (str):
        ID for subject across the entire XNAT database.
        Required or --xnatsubjectlabel needs to be set.

    --xnatsubjectlabel (str):
        Label for subject within a project for the XNAT database.
        Required or --xnatsubjectid needs to be set.

    --xnataccsessionid (str):
        ID for subject-specific session within the XNAT project.
        Derived from XNAT but can be set manually.

    --xnatsessionlabel (str):
        Label for session within XNAT project.
        Note: may be general across multiple subjects (e.g. rest). Required.

    --xnatstudyinputpath (str, default 'input/RESOURCES/qunex_study'):
        The path to the previously generated session data as mounted for the
        container.

    --dataformat (str, default 'DICOM'):
        Specify the format in which the data is. Acceptable values are:

        - 'DICOM' ... datasets with images in DICOM format
        - 'BIDS'  ... BIDS compliant datasets
        - 'HCPLS' ... HCP Life Span datasets
        - 'HCPYA' ... HCP Young Adults (1200) dataset.

    --hcp_filename (str):
        Specify how files and folders should be named using HCP processing:

        - 'automated'   ... files should be named using QuNex automated naming
          (e.g. BOLD_1_PA)
        - 'userdefined' ... files should be named using user defined names (e.g.
          rfMRI_REST1_AP)

        Note that the filename to be used has to be provided in the
        session_hcp.txt file or the standard naming will be used. If not
        provided the default 'automated' will be used.

    --bidsformat (str, default 'no'):
        Note: this parameter is deprecated and is kept for backward
        compatibility.

        If set to 'yes', it will set --dataformat to BIDS. If left undefined or
        set to 'no', the --dataformat value will be used. The specification of
        the parameter follows ...

        Specify if input data is in BIDS format (yes/no). Default is [no]. If
        set to yes, it overwrites the --dataformat parameter.

        Note:

        - If --bidsformat='yes' and XNAT run is requested then
          --xnatsessionlabel is required.
        - If --bidsformat='yes' and XNAT run is NOT requested
          then BIDS data expected in <sessions_folder/inbox/BIDS.

    --bidsname (str, default detailed below):
        The name of the BIDS dataset. The dataset level information that does
        not pertain to a specific session will be stored in
        <projectname>/info/bids/<bidsname>. If bidsname is not provided, it
        will be deduced from the name of the folder in which the BIDS database
        is stored or from the zip package name.

    --rawdatainput (str, default ''):
        If --turnkeytype is not XNAT then specify location of raw data on the
        file system for a session. Default is '' for the XNAT type run as host
        is used to pull data.

    --workingdir (str, default '/output'):
        Specify where the study folder is to be created or resides.

    --projectname (str):
        Specify name of the project on local file system if XNAT is not
        specified.

    --overwritestep (str, default 'no'):
        Specify 'yes' or 'no' for delete of prior workflow step.

    --overwritesession (str, default 'no'):
        Specify 'yes' or 'no' for delete of prior session run.

    --overwriteproject (str, default 'no'):
        Specify 'yes' or 'no' for delete of entire project prior to run.

    --overwriteprojectxnat (str, default 'no'):
        Specify 'yes' or 'no' for delete of entire XNAT project folder prior to
        run.

    --cleanupsession (str, default 'no'):
        Specify 'yes' or 'no' for cleanup of session folder after steps are
        done.

    --cleanupproject (str, default 'no'):
        Specify 'yes' or 'no' for cleanup of entire project after steps are
        done.

    --cleanupoldfiles (str, default 'no'):
        Specify <yes> or <no> for cleanup of files that are older than start of
        run (XNAT run only).

    --bolds (str, default 'all'):
        For commands that work with BOLD images this flag specifies which
        specific BOLD images to process. The list of BOLDS has to be specified
        as a comma or pipe '|' separated string of bold numbers or bold tags as
        they are specified in the session_hcp.txt or batch.txt file.

        Example: '--bolds=1,2,rest' would process BOLD run 1, BOLD run 2 and any
        other BOLD image that is tagged with the string 'rest'.

        If the parameter is not specified, the default value 'all' will be used.
        In this scenario every BOLD image that is specified in the group
        batch.txt file for that session will be processed.

        **Note**: This parameter takes precedence over the 'bolds' parameter in
        the batch.txt file. Therefore when run_turnkey is executed and this
        parameter is ommitted the '_bolds' specification in the batch.txt file
        never takes effect, because the default value 'all' will take
        precedence.

    --customqc (str, default 'no'):
        Either 'yes' or 'no'. If set to 'yes' then the script ooks into:
        ~/<study_path>/processing/scenes/QC/ for additional custom QC scenes.

        Note: The provided scene has to conform to QuNex QC template
        standards.xw

        See /opt/qunex/qx_library/data/scenes/qc/ for example templates.

        The qc path has to contain relevant files for the provided scene.

    --qcplotimages (str):
        Absolute path to images for general_plot_bold_timeseries. See
        'qunex general_plot_bold_timeseries' for help.

        Only set if general_plot_bold_timeseries is requested then this is a
        required setting.

    --qcplotmasks (str):
        Absolute path to one or multiple masks to use for extracting BOLD data.
        See 'qunex general_plot_bold_timeseries' for help.

        Only set if general_plot_bold_timeseries is requested then this is a
        required setting.

    --qcplotelements (str):
        Plot element specifications for general_plot_bold_timeseries. See
        'qunex general_plot_bold_timeseries' for help.

        Only set if general_plot_bold_timeseries is requested.

Notes:
    A complete list of commands that can be used with turnkey:

    * create_study
    * map_raw_data
    * import_dicom
    * run_qc_rawnii
    * create_session_info
    * setup_hcp
    * create_batch
    * export_hcp
    * hcp_pre_freesurfer
    * hcp_freesurfer
    * hcp_post_freesurfer
    * run_qc_t1w
    * run_qc_t2w
    * run_qc_myelin
    * hcp_fmri_volume
    * hcp_fmri_surface
    * run_qc_bold
    * hcp_diffusion
    * run_qc_dwi
    * dwi_legacy_gpu
    * dwi_eddy_qc
    * run_qc_dwi_eddy
    * dwi_dtifit
    * run_qc_dwi_dtifit
    * dwi_bedpostx_gpu
    * run_qc_dwi_process
    * run_qc_dwi_bedpostx
    * dwi_probtrackx_dense_gpu
    * dwi_pre_tractography
    * dwi_parcellate
    * dwi_seed_tractography_dense
    * run_qc_custom
    * map_hcp_data
    * create_bold_brain_masks
    * compute_bold_stats
    * create_stats_report
    * extract_nuisance_signal
    * preprocess_bold
    * preprocess_conc
    * general_plot_bold_timeseries
    * parcellate_bold
    * parcellate_bold
    * compute_bold_fc_seed
    * compute_bold_fc_gbc
    * run_qc_bold_fc.

    List of Turnkey Steps:
        Most turnkey steps have exact matching qunex commands with several
        exceptions that fall into two categories:

        * ``map_raw_data`` step is only relevant to ``run_turnkey``, which maps
          files on a local filesystem or in XNAT to the study folder.
        * ``run_qc*`` and ``compute_bold_fc*`` are two groups of turnkey steps that
          have qunex commands as their prefixes. The suffixes of these commands
          are options of the corresponding qunex command.

    Tracking progress:
        Progress can be tracked by keeping track of the standard out and by log files generated in:

        ``${WORK_DIR}/${STUDY_NAME}/processing/logs/runlogs/``

        ``${WORK_DIR}/${STUDY_NAME}/processing/logs/comlogs/``

Examples:
    Run directly via::

         ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/run_turnkey.sh \\
             --<parameter1> \\
             --<parameter2> \\
             --<parameter3> ... \\
             --<parameterN>

    Run via::

        qunex run_turnkey \\
            --<parameter1> \\
            --<parameter2> ... \\
            --<parameterN>

    --scheduler
        A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
        relevant options.

    For SLURM scheduler the string would look like this via the qunex call::

        --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

    ::

        qunex run_turnkey \\
            --turnkeytype=<turnkey_run_type> \\
            --turnkeysteps=<turnkey_worlflow_steps> \\
            --paramfile=<parameters_file> \\
            --overwritestep=yes \\
            --mappingfile=<mapping_file> \\
            --xnatsubjectlabel=<XNAT_SUBJECT_LABEL> \\
            --xnatsessionlabel=<XNAT_SESSION_LABEL> \\
            --xnatprojectid=<name_of_xnat_project_id> \\
            --xnathostname=<XNAT_site_URL> \\
            --xnatuser=<xnat_host_user_name> \\
            --xnatpass=<xnat_host_user_pass>

EOF
exit 0
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]] || [[ $1 == "help" ]] || [[ $1 == "usage" ]]; then
    usage
fi

main() {

# ------------------------------------------------------------------------------
# -- Check for options
# ------------------------------------------------------------------------------

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

# ------------------------------------------------------------------------------
# -- Setup variables
# ------------------------------------------------------------------------------

# -- Clear variables
unset BATCH_PARAMETERS_FILENAME
unset CASE
unset SESSION
unset OVERWRITE_STEP
unset OVERWRITE_PROJECT
unset OVERWRITE_PROJECT_FORCE
unset OVERWRITE_PROJECT_XNAT
unset OVERWRITE_SESSION
unset SCAN_MAPPING_FILENAME

unset XNAT_HOST_NAME
unset XNAT_USER_NAME
unset XNAT_PASSWORD
unset XNAT_PROJECT_ID

unset XNAT_ACCSESSION_ID
unset XNAT_SUBJECT_ID
unset XNAT_SUBJECT_LABEL
unset XNAT_SESSION_LABEL

unset TURNKEY_TYPE
unset TURNKEY_STEPS
unset TURNKEY_CLEAN
unset WORKDIR
unset RawDataInputPath
unset PROJECT_NAME
unset BIDS_NAME
unset PlotElements
unset CleanupSession
unset CleanupProject
unset STUDY_PATH
unset SessionsFolderName
unset BIDSFormat
unset HCPFilename
unset DATAFormat
unset AcceptanceTest
unset CleanupOldFiles

# get version
QuNexVer=`cat ${TOOLS}/${QUNEXREPO}/VERSION.md`

echo ""
echo "---> Executing QuNex run_turnkey workflow..."
echo ""

echo ""
echo "------------------------ Initiating QuNex Turnkey Workflow -------------------------------"
echo ""

# =-=-=-=-=-= GENERAL OPTIONS =-=-=-=-=-=
#
# -- General input flags

WORKDIR=`opts_GetOpt "--workingdir" $@`

# -- Check WORKDIR
if [[ -z ${WORKDIR} ]]; then
    WORKDIR="/output"; echo " ---> Note: Working directory where study is located is missing. Setting defaults: ${WORKDIR}"; echo ''
fi

STUDY_PATH=`opts_GetOpt "--path" $@`
StudyFolder=`opts_GetOpt "--studyfolder" $@`
if [[ -z ${StudyFolder} ]]; then
    StudyFolder="${STUDY_PATH}"
fi
if [[ -z ${STUDY_PATH} ]]; then
    STUDY_PATH="${StudyFolder}"
fi
StudyFolderPath="${StudyFolder}"

PROJECT_NAME=`opts_GetOpt "--projectname" $@`
BIDS_NAME=`opts_GetOpt "--bidsname" $@`
CleanupSession=`opts_GetOpt "--cleanupsession" $@`
CleanupProject=`opts_GetOpt "--cleanupproject" $@`
CleanupOldFiles=`opts_GetOpt "--cleanupoldfiles" $@`
RawDataInputPath=`opts_GetOpt "--rawdatainput" $@`

# sessions folder name
SessionsFolderName=`opts_GetOpt "--sessionsfoldername" $@`

if [[ -z ${SessionsFolderName} ]]; then
    SessionsFolderName="sessions"
fi

#CASES=`opts_GetOpt "--sessions" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "${CASES}" | sed 's/,/ /g;s/|/ /g'`
CASE=`opts_GetOpt "--sessions" "$@"`
if [ -z "$CASE" ]; then
    CASE=`opts_GetOpt "--session" "$@"`
fi
SESSION=`opts_GetOpt "--sessions" "$@"`
if [ -z "$SESSION" ]; then
    SESSION=`opts_GetOpt "--session" "$@"`
fi
if [ -z "$SESSION" ] && [ ! -z "$CASE" ] ; then
    SESSION="${CASE}"
fi
if [ ! -z "$SESSION" ] && [ -z "$CASE" ] ; then
    CASE="${SESSION}"
fi
SESSIONIDS=`opts_GetOpt "--sessionids" "$@"`
if [ -z "$SESSIONIDS" ]; then
    SESSIONIDS=`opts_GetOpt "--sessionid" "$@"`
fi
if [ -z "$SESSIONIDS" ]; then
    SESSIONIDS=${CASE}
fi

OVERWRITE_SESSION=`opts_GetOpt "--overwritesession" $@`
OVERWRITE_STEP=`opts_GetOpt "--overwritestep" $@`
if [ -z "$OVERWRITE_STEP" ]; then
    OVERWRITE_STEP=`opts_GetOpt "--overwrite" "$@"`
fi
OVERWRITE_PROJECT=`opts_GetOpt "--overwriteproject" $@`
OVERWRITE_PROJECT_FORCE=`opts_GetOpt "--overwriteprojectforce" $@`
OVERWRITE_PROJECT_XNAT=`opts_GetOpt "--overwriteprojectxnat" $@`
BATCH_PARAMETERS_FILENAME=`opts_GetOpt "--paramfile" $@`

# BACKWARDS COMPATIBILITY
if [[ -z ${BATCH_PARAMETERS_FILENAME} ]]; then
    BATCH_PARAMETERS_FILENAME=`opts_GetOpt "--batchfile" $@`
fi

SCAN_MAPPING_FILENAME=`opts_GetOpt "--mappingfile" $@`

XNAT_HOST_NAME=`opts_GetOpt "--xnathost" $@`
XNAT_USER_NAME=`opts_GetOpt "--xnatuser" $@`
XNAT_PASSWORD=`opts_GetOpt "--xnatpass" $@`
XNAT_STUDY_INPUT_PATH=`opts_GetOpt "--xnatstudyinputpath" $@`

# ----------------------------------------------------
#     INFO ON XNAT VARIABLE MAPPING FROM QuNex ---> JSON ---> XML specification
#
# project               --xnatprojectid        #  ---> mapping in QuNex: XNAT_PROJECT_ID     ---> mapping in JSON spec: #XNAT_PROJECT#   ---> Corresponding to project id in XML.
#   │
#   └──subject          --xnatsubjectid        #  ---> mapping in QuNex: XNAT_SUBJECT_ID     ---> mapping in JSON spec: #SUBJECTID#      ---> Corresponding to subject ID in subject-level XML (Subject Accession ID). EXAMPLE in XML        <xnat:subject_ID>BID11_S00192</xnat:subject_ID>
#        │                                                                                                                                                                                                         EXAMPLE in Web UI     Accession number:  A unique XNAT-wide ID for a given human irrespective of project within the XNAT Site
#        │              --xnatsubjectlabel     #  ---> mapping in QuNex: XNAT_SUBJECT_LABEL  ---> mapping in JSON spec: #SUBJECTLABEL#   ---> Corresponding to subject label in subject-level XML (Subject Label).     EXAMPLE in XML        <xnat:field name="SRC_SUBJECT_ID">CU0018</xnat:field>
#        │                                                                                                                                                                                                         EXAMPLE in Web UI     Subject Details:   A unique XNAT project-specific ID that matches the experimenter expectations
#        │
#        └──experiment  --xnataccsessionid     #  ---> mapping in QuNex: XNAT_ACCSESSION_ID  ---> mapping in JSON spec: #ID#             ---> Corresponding to subject session ID in session-level XML (Subject Accession ID)   EXAMPLE in XML       <xnat:experiment ID="BID11_E00048" project="embarc_r1_0_0" visit_id="ses-wk2" label="CU0018_MRwk2" xsi:type="xnat:mrSessionData">
#                                                                                                                                                                                                                           EXAMPLE in Web UI    Accession number:  A unique project specific ID for that subject
#                       --xnatsessionlabel     #  ---> mapping in QuNex: XNAT_SESSION_LABEL  ---> mapping in JSON spec: #LABEL#          ---> Corresponding to session label in session-level XML (Session/Experiment Label)    EXAMPLE in XML       <xnat:experiment ID="BID11_E00048" project="embarc_r1_0_0" visit_id="ses-wk2" label="CU0018_MRwk2" xsi:type="xnat:mrSessionData">
# ----------------------------------------------------

XNAT_PROJECT_ID=`opts_GetOpt "--xnatprojectid" $@`
XNAT_SUBJECT_ID=`opts_GetOpt "--xnatsubjectid" $@`
XNAT_SUBJECT_LABEL=`opts_GetOpt "--xnatsubjectlabels" "$@"`
if [ -z "$XNAT_SUBJECT_LABEL" ]; then
XNAT_SUBJECT_LABEL=`opts_GetOpt "--xnatsubjectlabel" "$@"`
fi
XNAT_ACCSESSION_ID=`opts_GetOpt "--xnataccsessionid" $@`
#XNAT_SESSION_LABELS=`opts_GetOpt "--xnatsessionlabels" "$@" | sed 's/,/ /g;s/|/ /g'`; XNAT_SESSION_LABELS=`echo "${XNAT_SESSION_LABELS}" | sed 's/,/ /g;s/|/ /g'`
XNAT_SESSION_LABEL=`opts_GetOpt "--xnatsessionlabels" "$@"`
if [ -z "$XNAT_SESSION_LABEL" ]; then
XNAT_SESSION_LABEL=`opts_GetOpt "--xnatsessionlabel" "$@"`
fi

TURNKEY_STEPS=`opts_GetOpt "--turnkeysteps" "$@" | sed 's/,/ /g;s/|/ /g'`; TURNKEY_STEPS=`echo "${TURNKEY_STEPS}" | sed 's/,/ /g;s/|/ /g'`

# remap turnkey steps by using the deprecated commands mapping
unset NEW_TURNKEY_STEPS
for STEP in ${TURNKEY_STEPS}; do
    # check if deprecated
    NEW_STEP=`gmri check_deprecated_commands --command="$STEP" | grep "is now known as" | sed 's/^.*is now known as //g'`

    # is it deprecated or not?
    if [[ -n $NEW_STEP ]]; then
        NEW_STEP=${NEW_STEP}
    else
        NEW_STEP=${STEP}
    fi

    # append
    if [[ -z $NEW_TURNKEY_STEPS ]]; then
        NEW_TURNKEY_STEPS="${NEW_STEP}"
    else
        NEW_TURNKEY_STEPS="${NEW_TURNKEY_STEPS} ${NEW_STEP}"
    fi

    # empty line for beutification
    echo ""
done

# set TURNKEY_STEPS to new list
TURNKEY_STEPS=${NEW_TURNKEY_STEPS}

TURNKEY_TYPE=`opts_GetOpt "--turnkeytype" $@`
TURNKEY_CLEAN=`opts_GetOpt "--turnkeycleanstep" $@`

DATAFormat=`opts_GetOpt "--dataformat" $@`
BIDSFormat=`opts_GetOpt "--bidsformat" $@`
HCPFilename=`opts_GetOpt "--hcp_filename" $@`

# backwards compatibility and default value
if [ -z "$HCPFilename" ]; then HCPFilename=`opts_GetOpt "--hcpfilename" $@`; fi
if [ -z "$HCPFilename" ]; then HCPFilename="automated"; fi
if [ "${HCPFilename}" == 'name' ]; then HCPFilename="userdefined"; fi
if [ "${HCPFilename}" == 'number' ]; then HCPFilename="automated"; fi
if [ "${HCPFilename}" == 'original' ]; then HCPFilename="userdefined"; fi
if [ "${HCPFilename}" == 'standard' ]; then HCPFilename="automated"; fi

if [ -z "$DATAFormat" ]; then DATAFormat=DICOM; fi
if [ "${BIDSFormat}" == 'yes' ]; then DATAFormat="BIDS"; fi
if [ "${DATAFormat}" == 'BIDS' ]; then BIDSFormat="yes"; else BIDSFormat="no"; fi

AcceptanceTest=`opts_GetOpt "--acceptancetest" "$@" | sed 's/,/ /g;s/|/ /g'`; AcceptanceTest=`echo "${AcceptanceTest}" | sed 's/,/ /g;s/|/ /g'`

# =-=-=-=-=-= import_dicom OPTIONS =-=-=-=-=-=
#
AddImageType=`opts_GetOpt "--add_image_type" $@`
AddJsonInfo=`opts_GetOpt "--add_json_info" $@`
Gzip=`opts_GetOpt "--gzip" $@`

# =-=-=-=-=-= BOLD FC OPTIONS =-=-=-=-=-=
#
# -- compute_bold_fc input flags
InputFiles=`opts_GetOpt "--inputfiles" $@`
OutPathFC=`opts_GetOpt "--targetf" $@`
Calculation=`opts_GetOpt "--calculation" $@`
RunType=`opts_GetOpt "--runtype" $@`
FileList=`opts_GetOpt "--flist" $@`
IgnoreFrames=`opts_GetOpt "--ignore" $@`
MaskFrames=`opts_GetOpt "--mask" "$@"`
Covariance=`opts_GetOpt "--covariance" $@`
TargetROI=`opts_GetOpt "--target" $@`
RadiusSmooth=`opts_GetOpt "--rsmooth" $@`
RadiusDilate=`opts_GetOpt "--rdilate" $@`
GBCCommand=`opts_GetOpt "--command" $@`
Verbose=`opts_GetOpt "--verbose" $@`
ComputeTime=`opts_GetOpt "---time" $@`
VoxelStep=`opts_GetOpt "--vstep" $@`
ROIInfo=`opts_GetOpt "--roinfo" $@`
FCCommand=`opts_GetOpt "--options" $@`
Method=`opts_GetOpt "--method" $@`
# -- parcellate_bold input flags
InputFile=`opts_GetOpt "--inputfile" $@`
InputPath=`opts_GetOpt "--inputpath" $@`
InputDataType=`opts_GetOpt "--inputdatatype" $@`
SingleInputFile=`opts_GetOpt "--singleinputfile" $@`
OutPath=`opts_GetOpt "--outpath" $@`
OutName=`opts_GetOpt "--outname" $@`
ExtractData=`opts_GetOpt "--extractdata" $@`
ComputePConn=`opts_GetOpt "--computepconn" $@`
UseWeights=`opts_GetOpt "--useweights" $@`
WeightsFile=`opts_GetOpt "--weightsfile" $@`
ParcellationFile=`opts_GetOpt "--parcellationfile" $@`
RunParcellations=`opts_GetOpt "--runparcellations" $@`

# =-=-=-=-=-= DIFFUSION OPTIONS =-=-=-=-=-=
#
# -- dwi_legacy input flags
EchoSpacing=`opts_GetOpt "--echospacing" $@`
pedir=`opts_GetOpt "--pedir" $@`
TE=`opts_GetOpt "--TE" $@`
UnwarpDir=`opts_GetOpt "--unwarpdir" $@`
DiffDataSuffix=`opts_GetOpt "--diffdatasuffix" $@`
Scanner=`opts_GetOpt "--scanner" $@`
UseFieldmap=`opts_GetOpt "--usefieldmap" $@`
# -- dwi_parcellate input flags
MatrixVersion=`opts_GetOpt "--matrixversion" $@`
ParcellationFile=`opts_GetOpt "--parcellationfile" $@`
OutName=`opts_GetOpt "--outname" $@`
WayTotal=`opts_GetOpt "--waytotal" $@`
# -- dwi_seed_tractography_dense input flags
SeedFile=`opts_GetOpt "--seedfile" $@`
# -- dwi_eddy_qc input flags
EddyBase=`opts_GetOpt "--eddybase" $@`
EddyPath=`opts_GetOpt "--eddypath" $@`
Report=`opts_GetOpt "--report" $@`
BvalsFile=`opts_GetOpt "--bvalsfile" $@`
BvecsFile=`opts_GetOpt "--bvecsfile" $@`
EddyIdx=`opts_GetOpt "--eddyidx" $@`
EddyParams=`opts_GetOpt "--eddyparams" $@`
List=`opts_GetOpt "--list" $@`
Mask=`opts_GetOpt "--mask" $@`
GroupBar=`opts_GetOpt "--groupvar" $@`
OutputDir=`opts_GetOpt "--outputdir" $@`
Update=`opts_GetOpt "--update" $@`
# -- dwi_bedpostx_gpu input flags
Fibers=`opts_GetOpt "--fibers" $@`
Model=`opts_GetOpt "--model" $@`
Burnin=`opts_GetOpt "--burnin" $@`
Jumps=`opts_GetOpt "--jumps" $@`
Rician=`opts_GetOpt "--rician" $@`
Gradnonlin=`opts_GetOpt "--gradnonlin" $@`
# -- dwi_probtrackx_dense_gpu input flags
MatrixOne=`opts_GetOpt "--omatrix1" $@`
MatrixThree=`opts_GetOpt "--omatrix3" $@`
NsamplesMatrixOne=`opts_GetOpt "--nsamplesmatrix1" $@`
NsamplesMatrixThree=`opts_GetOpt "--nsamplesmatrix3" $@`

# =-=-=-=-=-= QC OPTIONS =-=-=-=-=-=
#
# -- run_qc input flags
OutPath=`opts_GetOpt "--outpath" $@`
SceneTemplateFolder=`opts_GetOpt "--scenetemplatefolder" $@`
UserSceneFile=`opts_GetOpt "--userscenefile" $@`
UserScenePath=`opts_GetOpt "--userscenepath" $@`
Modality=`opts_GetOpt "--modality" $@`
DWIPath=`opts_GetOpt "--dwipath" $@`
DWIData=`opts_GetOpt "--dwidata" $@`
DtiFitQC=`opts_GetOpt "--dtifitqc" $@`
BedpostXQC=`opts_GetOpt "--bedpostxqc" $@`
EddyQCStats=`opts_GetOpt "--eddyqcstats" $@`
BOLDfc=`opts_GetOpt "--boldfc" $@`
BOLDfcInput=`opts_GetOpt "--boldfcinput" $@`
BOLDfcPath=`opts_GetOpt "--boldfcpath" $@`
GeneralSceneDataFile=`opts_GetOpt "--datafile" $@`
GeneralSceneDataPath=`opts_GetOpt "--datapath" $@`


BOLDS=`opts_GetOpt "--bolds" "$@"`
if [ -z "${BOLDS}" ]; then
    BOLDS=`opts_GetOpt "--boldruns" "$@"`
fi
if [ -z "${BOLDS}" ]; then
    BOLDS=`opts_GetOpt "--bolddata" "$@"`
fi
if [ -z "${BOLDS}" ]; then
    BOLDS='all'
fi
BOLDRUNS=`echo ${BOLDS} | sed 's/,/ /g;s/|/ /g'`; BOLDRUNS=`echo "$BOLDRUNS" | sed 's/,/ /g;s/|/ /g'`

BOLDSuffix=`opts_GetOpt "--boldsuffix" $@`
BOLDPrefix=`opts_GetOpt "--boldprefix" $@`
SkipFrames=`opts_GetOpt "--skipframes" $@`
SNROnly=`opts_GetOpt "--snronly" $@`
TimeStamp=`opts_GetOpt "--timestamp" $@`
Suffix=`opts_GetOpt "--suffix" $@`
SceneZip=`opts_GetOpt "--scenezip" $@`
runQC_Custom=`opts_GetOpt "--customqc" $@`
HCPSuffix=`opts_GetOpt "--hcp_suffix" $@`

# -- general_plot_bold_timeseries input flags
QCPlotElements=`opts_GetOpt "--qcplotelements" $@`
QCPlotImages=`opts_GetOpt "--qcplotimages" $@`
QCPlotMasks=`opts_GetOpt "--qcplotmasks" $@`

# -- Define script name
scriptName=$(basename ${0})

# -- Check and set turnkey type
if [[ -z ${TURNKEY_TYPE} ]]; then
    TURNKEY_TYPE="xnat"; echo " ---> Note: Turnkey type not specified. Setting default turnkey type to: ${TURNKEY_TYPE}"; echo ''
fi

# -- Check and set AcceptanceTest type
if [[ -z ${AcceptanceTest} ]]; then
    AcceptanceTest="no"; echo " ---> Note: Acceptance Test type not specified. Setting default type to: ${AcceptanceTest}"; echo ''
fi

# -- Check and set turnkey clean
if [[ -z ${TURNKEY_CLEAN} ]]; then
    TURNKEY_CLEAN="no"; echo " ---> Note: Turnkey cleaning not specified. Setting default to: ${TURNKEY_CLEAN}"; echo ''
fi

# -- Check that BATCH_PARAMETERS_FILENAME flag and parameter is set
if [[ -z ${BATCH_PARAMETERS_FILENAME} ]];
    then echo "ERROR: --paramfile flag missing. Parameter file not specified."; echo '';
    exit 1;
fi

########################  run_turnkey LOCAL vs. XNAT-SPECIFIC CHECKS  ################################
#
# -- Check and set non-XNAT or XNAT specific parameters
if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
    if [[ -z ${PROJECT_NAME} ]]; then echo "ERROR: Project name is missing."; exit 1; echo ''; fi

    # create STUDY_PATH and/or StudyFolder if not defined explicitly
    if [[ -z ${StudyFolder} ]]; then
        StudyFolder="${WORKDIR}/${PROJECT_NAME}"
    fi
    if [[ -z ${STUDY_PATH} ]]; then
        STUDY_PATH=${WORKDIR}/${PROJECT_NAME}
    fi

    if [[ ${STUDY_PATH} == ${WORKDIR} ]]; then
            echo "ERROR: --workingdir and --path variables are set to the same location. Check your inputs and re-run."
            echo "       ${WORKDIR}"
            exit 1
    fi

    if [[ -z ${SessionsFolder} ]]; then
        SessionsFolder=${StudyFolder}/${SessionsFolderName}
    fi

    if [[ -z ${CASE} ]]; then echo "ERROR: Requesting local run but --session flag is missing."; exit 1; echo ''; fi
fi

if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
    if [[ -z ${XNAT_PROJECT_ID} ]]; then echo "ERROR: --xnatprojectid flag missing. Parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${XNAT_HOST_NAME} ]]; then echo "ERROR: --xnathost flag missing. Parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${XNAT_USER_NAME} ]]; then echo "ERROR: --xnatuser flag missing. Username parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${XNAT_PASSWORD} ]]; then echo "ERROR: --xnatpass flag missing. Password parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${STUDY_PATH} ]]; then STUDY_PATH=${WORKDIR}/${XNAT_PROJECT_ID}; fi
    if [[ -z ${StudyFolder} ]]; then StudyFolder=${STUDY_PATH}; fi
    if [[ -z ${XNAT_SUBJECT_ID} ]] && [[ -z ${XNAT_SUBJECT_LABEL} ]]; then echo "ERROR: --xnatsubjectid or --xnatsubjectlabel flags are missing. Please specify either subject id or subject label and re-run."; echo ''; exit 1; fi
    if [[ -z ${XNAT_SUBJECT_ID} ]] && [[ ! -z ${XNAT_SUBJECT_LABEL} ]]; then echo " ---> Note: --xnatsubjectid is not set. Using --xnatsubjectlabel to query XNAT."; echo ''; fi
    if [[ ! -z ${XNAT_SUBJECT_ID} ]] && [[ -z ${XNAT_SUBJECT_LABEL} ]]; then echo " ---> Note: --xnatsubjectlabel is not set. Using --xnatsubjectid to query XNAT."; echo ''; fi
    if [[ -z ${XNAT_SESSION_LABEL} ]]; then echo "ERROR: --xnatsessionlabel flag missing. Please specify session label and re-run."; echo ''; exit 1; fi
    if [[ -z ${XNAT_STUDY_INPUT_PATH} ]]; then XNAT_STUDY_INPUT_PATH=/input/RESOURCES/qunex_study; echo " ---> Note: XNAT session input path is not defined. Setting default path to: $XNAT_STUDY_INPUT_PATH"; echo ""; fi

    # -- Curl calls to set correct subject and session variables at start of run_turnkey

    # -- Clean prior mapping
    rm -r ${HOME}/xnatlogs &> /dev/null
    mkdir ${HOME}/xnatlogs &> /dev/null
    XNATINFOTMP="${HOME}/xnatlogs"
    TimeStampCurl=`date +%Y-%m-%d_%H.%M.%S.%6N`

    if [[ ${CleanupOldFiles} == "yes" ]]; then
        if [ ! -d ${WORKDIR} ]; then
            mkdir -p ${WORKDIR} &> /dev/null
        fi
        touch ${WORKDIR}/_startfile
    fi

    # -- Obtain temp info on subjects and experiments in the project
    curl -k -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/subjects?project=${XNAT_PROJECT_ID}&format=csv" > ${XNATINFOTMP}/${XNAT_PROJECT_ID}_subjects_${TimeStampCurl}.csv
    curl -k -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/experiments?project=${XNAT_PROJECT_ID}&format=csv" > ${XNATINFOTMP}/${XNAT_PROJECT_ID}_experiments_${TimeStampCurl}.csv

    # -- Define XNAT_SUBJECT_ID (i.e. Accession number) and XNAT_SESSION_LABEL (i.e. MR Session lablel) for the specific XNAT_SUBJECT_LABEL (i.e. subject)
    if [[ -z ${XNAT_SUBJECT_ID} ]]; then XNAT_SUBJECT_ID=`cat ${XNATINFOTMP}/${XNAT_PROJECT_ID}_subjects_${TimeStampCurl}.csv | grep "${XNAT_SUBJECT_LABEL}" | awk  -F, '{print $1}'`; fi
    if [[ -z ${XNAT_SUBJECT_LABEL} ]]; then XNAT_SUBJECT_LABEL=`cat ${XNATINFOTMP}/${XNAT_PROJECT_ID}_subjects_${TimeStampCurl}.csv | grep "${XNAT_SUBJECT_ID}" | awk  -F, '{print $3}'`; fi
    # -- Re-obtain the label from the database just in case it was mis-specified
    if [[ -z ${XNAT_SUBJECT_LABEL} ]]; then XNAT_SESSION_LABEL=`cat ${XNATINFOTMP}/${XNAT_PROJECT_ID}_experiments_${TimeStampCurl}.csv | grep "${XNAT_SUBJECT_LABEL}" | grep "${XNAT_SESSION_LABEL}" | awk  -F, '{print $5}'`; fi
    if [[ -z ${XNAT_ACCSESSION_ID} ]]; then XNAT_ACCSESSION_ID=`cat ${XNATINFOTMP}/${XNAT_PROJECT_ID}_experiments_${TimeStampCurl}.csv | grep "${XNAT_SUBJECT_LABEL}" | grep "${XNAT_SESSION_LABEL}" | awk  -F, '{print $1}'`; fi

    # -- Clean up temp curl call info
    rm -r ${HOME}/xnatInfoTmp &> /dev/null

    # -- Report error if variables remain undefined
    if [[ -z ${XNAT_SUBJECT_ID} ]] || [[ -z ${XNAT_SUBJECT_LABEL} ]] || [[ -z ${XNAT_ACCSESSION_ID} ]] || [[ -z ${XNAT_SESSION_LABEL} ]]; then
        echo ""
        echo "Some or all of XNAT database variables were not set correctly: "
        echo ""
        echo "  ---> XNAT_SUBJECT_ID     :  $XNAT_SUBJECT_ID "
        echo "  ---> XNAT_SUBJECT_LABEL  :  $XNAT_SUBJECT_LABEL "
        echo "  ---> XNAT_ACCSESSION_ID  :  $XNAT_ACCSESSION_ID "
        echo "  ---> XNAT_SESSION_LABEL  :  $XNAT_SESSION_LABEL "
        echo ""
        exit 1
    else
        echo ""
        echo "Successfully read all XNAT database variables: "
        echo ""
        echo "  ---> XNAT_SUBJECT_ID     :  $XNAT_SUBJECT_ID "
        echo "  ---> XNAT_SUBJECT_LABEL  :  $XNAT_SUBJECT_LABEL "
        echo "  ---> XNAT_ACCSESSION_ID  :  $XNAT_ACCSESSION_ID "
        echo "  ---> XNAT_SESSION_LABEL  :  $XNAT_SESSION_LABEL "
        echo ""
    fi

    # -- Define final variable set
    CASE="${XNAT_SESSION_LABEL}"
fi

#
################################################################################

# ------------------------------------------------------------------------------
# -- subjects vs. sessions folder backwards compatibility settings
# ------------------------------------------------------------------------------

# -- subjects vs. sessions folder backwards compatibility settings
if [[ -d "${StudyFolder}/subjects" ]] && [[ -d "${StudyFolder}/${SessionsFolderName}" ]]; then
    echo ""
    echo "WARNING: You are attempting to execute run_turnkey using a conflicting QuNex file hierarchy:"
    echo ""
    echo "     Found: ---> ${StudyFolder}/subjects"
    echo "     Found: ---> ${StudyFolder}/${SessionsFolderBase}"
    echo ""
    echo "     Note: Current version of QuNex supports the following default specification: "
    echo "            ---> ${StudyFolder}/sessions"
    echo ""
    echo "     To avoid the possibility of a backwards incompatible or duplicate "
    echo "     QuNex runs please review the study directory structure and consider"
    echo "     resolving the conflict such that a consistent folder specification is used. "
    echo ""
    echo "     QuNex will proceed but please consider renaming your directories per latest specs:"
    echo "          https://qunex.readthedocs.io/en/latest/wiki/Overview/DataHierarchy"
    echo ""
fi

if [[ -d "${StudyFolder}/subjects" ]] && [[ ! -d "${StudyFolder}/${SessionsFolderName}" ]]; then
    echo ""
    echo "WARRNING: You are attempting to execute run_turnkey using an outdated QuNex file hierarchy:"
    echo ""
    echo "     Found: ---> ${StudyFolder}/subjects"
    echo ""
    echo "     Note: Current version of QuNex supports the following default specification: "
    echo "            ---> ${StudyFolder}/sessions"
    echo ""
    echo "     To avoid the possibility of a backwards incompatible or duplicate "
    echo "     QuNex runs please review the study directory structure and consider"
    echo "     resolving the conflict such that a consistent folder specification is used. "
    echo ""
    echo "     QuNex will proceed but please consider renaming your directories per latest specs:"
    echo "          https://qunex.readthedocs.io/en/latest/wiki/Overview/DataHierarchy"
    echo ""
    SessionsFolder="${STUDY_PATH}/subjects"
    SessionsFolderName="subjects"
fi

if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
    if [[ -d "${StudyFolder}/sessions" ]] && [[ ! -d "${StudyFolder}/subjects" ]]; then
        SessionsFolder="${STUDY_PATH}/sessions"
        SessionsFolderName="sessions"
    fi
    if [[ ! -d "${StudyFolder}/sessions" ]] && [[ ! -d "${StudyFolder}/subjects" ]] && [[ ! -d "${StudyFolder}" ]]; then
        SessionsFolder="${STUDY_PATH}/sessions"
        SessionsFolderName="sessions"
    fi
fi

# -- Check TURNKEY_STEPS
if [[ -z ${TURNKEY_STEPS} ]] && [ ! -z "${QuNexTurnkeyWorkflow##*${AcceptanceTest}*}" ]; then
    echo ""
    echo "ERROR: Turnkey steps flag missing. Specify supported turnkey steps:"
    echo "-------------------------------------------------------------------"
    echo " ${QuNexTurnkeyWorkflow}"
    echo ''
    exit 1
fi

# -- Check TURNKEY_STEPS test flag
unset FoundSupported
echo ""
echo "---> Checking that requested ${TURNKEY_STEPS} are supported..."
echo ""
TurnkeyTestStepChecks="${TURNKEY_STEPS}"
unset TurnkeyTestSteps
for TurnkeyTestStep in ${TurnkeyTestStepChecks}; do
   if [ ! -z "${QuNexTurnkeyWorkflow##*${TurnkeyTestStep}*}" ]; then
       echo "     ${TurnkeyTestStep} is not supported. Will remove from requested list."
   else
       echo "     ${TurnkeyTestStep} is supported."
       FoundSupported="yes"
       TurnkeyTestSteps="${TurnkeyTestSteps} ${TurnkeyTestStep}"
   fi
done
if [[ -z ${FoundSupported} ]]; then
    usage
    echo ""
    echo "ERROR: None of the requested acceptance tests are currently supported."; echo "";
    echo "Supported: ${QuNexTurnkeyWorkflow}"; echo "";
    exit 1
else
    TURNKEY_STEPS="${TurnkeyTestSteps}"
    echo ""
    echo "---> Verified list of supported Turnkey steps to be run: ${TURNKEY_STEPS}"
    echo ""
fi

# -- Check acceptance test flag
if [[ ! -z ${AcceptanceTestSteps} ]]; then
    # -- Run checks for supported steps
    unset FoundSupported
    echo ""
    echo "---> Checking that requested ${AcceptanceTestSteps} are supported..."
    echo ""
    AcceptanceTestStepsChecks="${AcceptanceTestSteps}"
    unset AcceptanceTestSteps
    for AcceptanceTestStep in ${AcceptanceTestStepsChecks}; do
       if [ ! -z "${SupportedAcceptanceTestSteps##*${AcceptanceTestStep}*}" ]; then
           echo ""
           echo "---> ${AcceptanceTestStep} is not supported. Will remove from requested list."
           echo ""
       else
           echo ""
           echo "---> ${AcceptanceTestStep} is supported."
           echo ""
           FoundSupported="yes"
           AcceptanceTestSteps="${AcceptanceTestSteps} ${AcceptanceTestStep}"
       fi
    done
    if [[ -z ${FoundSupported} ]]; then
        usage
        echo "ERROR: None of the requested acceptance tests are currently supported."; echo "";
        echo "Supported: ${SupportedAcceptanceTestSteps}"; echo "";
    fi
fi

# -- Function to check for BATCH_PARAMETERS_FILENAME
checkBatchFileHeader() {
    if [[ -z ${BATCH_PARAMETERS_FILENAME} ]]; then echo "ERROR: --paramfile flag missing. Parameter file not specified."; echo ''; exit 1; fi
    if [[ -f ${BATCH_PARAMETERS_FILENAME} ]]; then
        BATCH_PARAMETERS_FILE_PATH="${BATCH_PARAMETERS_FILENAME}"
    else
        if [[ -f ${RawDataInputPath}/${BATCH_PARAMETERS_FILENAME} ]]; then
            BATCH_PARAMETERS_FILE_PATH="${RawDataInputPath}/${BATCH_PARAMETERS_FILENAME}"
        else
            if [[ ! `echo ${TURNKEY_STEPS} | grep 'create_study'` ]]; then
                if [[ -f ${STUDY_PATH}/processing/${BATCH_PARAMETERS_FILENAME} ]]; then
                    BATCH_PARAMETERS_FILE_PATH="${SessionsFolder}/specs/${BATCH_PARAMETERS_FILENAME}"
                fi
           fi
        fi
    fi
    if [[ ! -f ${BATCH_PARAMETERS_FILE_PATH} ]]; then echo "ERROR: --paramfile flag set but file not found in default locations: ${BATCH_PARAMETERS_FILENAME}"; echo ''; exit 1; fi
}

# -- Function to check for SCAN_MAPPING_FILENAME
checkMappingFile() {
    if [[ -z ${SCAN_MAPPING_FILENAME} ]]; then echo "ERROR: --mappingfile flag missing. Scanning file parameter file not specified."; echo ''; exit 1;  fi
    if [[ -f ${SCAN_MAPPING_FILENAME} ]]; then
        SCAN_MAPPING_FILENAME_PATH="${SCAN_MAPPING_FILENAME}"
    else
        if [[ -f ${RawDataInputPath}/${SCAN_MAPPING_FILENAME} ]]; then
            SCAN_MAPPING_FILENAME_PATH="${RawDataInputPath}/${SCAN_MAPPING_FILENAME}"
        else
            if [[ ! `echo ${TURNKEY_STEPS} | grep 'create_study'` ]]; then
                if [[ -f ${STUDY_PATH}/processing/${SCAN_MAPPING_FILENAME} ]]; then
                    SCAN_MAPPING_FILENAME_PATH="${SessionsFolder}/specs/${SCAN_MAPPING_FILENAME}"
                fi
           fi
        fi
    fi
    if [[ ! -f ${SCAN_MAPPING_FILENAME_PATH} ]]; then echo "ERROR: --mappingfile flag set but file not found in default locations: ${SCAN_MAPPING_FILENAME}"; echo ''; exit 1; fi
}


# -- Code for selecting BOLDS via Tags ---> Check if both batch and bolds are specified for QC and if yes read batch explicitly
getBoldList() {
    if [[ ! -z ${ProcessingBatchFile} ]]; then
        LBOLDRUNS="${BOLDRUNS}"
        echo "  ---> For ${CASE} searching for BOLD(s): '${LBOLDRUNS}' in batch file ${ProcessingBatchFile} ... ";

        # set output type
        unset BOLDnameOutput
        if [[ ! -z ${HCPFilename} ]] && [[ ${HCPFilename} == "userdefined" ]]; then
            BOLDnameOutput="name";
        else
            HCPFilename="standard"
            BOLDnameOutput="number";
        fi

        echo "  ---> Using ${HCPFilename} hcp_filename [${BOLDnameOutput}] ... ";

        if [[ -f ${ProcessingBatchFile} ]]; then
            LBOLDRUNS=`gmri batch_tag2namekey filename="${ProcessingBatchFile}" sessionid="${CASE}" bolds="${LBOLDRUNS}" output="${BOLDnameOutput}" prefix="" | grep "BOLDS:" | sed 's/BOLDS://g' | sed 's/,/ /g'`
            LBOLDRUNS="${LBOLDRUNS}"
        else
            echo " ERROR: Requested BOLD modality with a batch file but the batch file not found. Check your inputs!"; echo ""
            exit 1
        fi
        if [[ ! -z ${LBOLDRUNS} ]]; then
            echo "  ---> Selected BOLDs: ${LBOLDRUNS} "
            echo ""
        else
            echo " ERROR: No BOLDs found! Something went wrong for ${CASE}. Check your batch file inputs!"; echo ""
            exit 1
        fi
    fi
}


# -- Code for getting BOLD numbers
getBoldNumberList() {
    if [[ ! -z ${ProcessingBatchFile} ]]; then
        LBOLDRUNS="${BOLDRUNS}"
        echo "  ---> For ${CASE} searching for BOLD(s): '${LBOLDRUNS}' in batch file ${ProcessingBatchFile} ... ";
        if [[ -f ${ProcessingBatchFile} ]]; then
            LBOLDRUNS=`gmri batch_tag2namekey filename="${ProcessingBatchFile}" sessionid="${CASE}" bolds="${LBOLDRUNS}" output="number" prefix="" | grep "BOLDS:" | sed 's/BOLDS://g' | sed 's/,/ /g'`
            LBOLDRUNS="${LBOLDRUNS}"
        else
            echo " ERROR: Requested BOLD modality with a batch file but the batch file not found. Check your inputs!"; echo ""
            exit 1
        fi
        if [[ ! -z ${LBOLDRUNS} ]]; then
            echo "  ---> Selected BOLDs: ${LBOLDRUNS} "
            echo ""
        else
            echo " ERROR: No BOLDs found! Something went wrong for ${CASE}. Check your batch file inputs!"; echo ""
            exit 1
        fi
    fi
}


# -- Perform explicit checks for steps which rely on BATCH_PARAMETERS_FILENAME and SCAN_MAPPING_FILENAME
if [[ `echo ${TURNKEY_STEPS} | grep 'create_study'` ]] || [[ `echo ${TURNKEY_STEPS} | grep 'map_raw_data'` ]]; then
    if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
        if [ -z "$BATCH_PARAMETERS_FILENAME" ]; then echo "ERROR: --paramfile flag missing. Parameter file not specified."; echo ''; exit 1; fi
        if [ -z "$SCAN_MAPPING_FILENAME" ]; then echo "ERROR: --mappingfile flag missing. Parameter file not specified."; echo ''; exit 1;  fi
    fi
    if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
        if [[ `echo ${TURNKEY_STEPS} | grep 'map_raw_data'` ]]; then
            if [[ -z ${RawDataInputPath} ]]; then echo "ERROR: --rawdatainput flag missing. Input data not specified."; echo ''; exit 1; fi
        fi
        checkBatchFileHeader
        checkMappingFile
    fi
fi


# -- Perform checks that batchfile is provided if create_batch has been requested
if [[ `echo ${TURNKEY_STEPS} | grep 'create_batch'` ]]; then
    if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
        if [ -z "$BATCH_PARAMETERS_FILENAME" ]; then echo "ERROR: --paramfile flag missing. Parameter file not specified."; echo ''; exit 1; fi
    fi
    if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
        checkBatchFileHeader
    fi
fi

# -- Perform checks that mapping file is provided if create_session_info has been requested
if [[ `echo ${TURNKEY_STEPS} | grep 'create_session_info'` ]]; then
    if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
        if [ -z "$SCAN_MAPPING_FILENAME" ]; then echo "ERROR: --mappingfile flag missing. Mapping parameter file not specified."; echo ''; exit 1;  fi
    fi
    if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
        checkMappingFile
    fi
fi

# -- Check and set overwrites
if [ -z "$OVERWRITE_STEP" ]; then OVERWRITE_STEP="no"; fi
if [ -z "$OVERWRITE_SESSION" ]; then OVERWRITE_SESSION="no"; fi
if [ -z "$OVERWRITE_PROJECT" ]; then OVERWRITE_PROJECT="no"; fi
if [[ -z "$OVERWRITE_PROJECT_XNAT" ]]; then OVERWRITE_PROJECT_XNAT="no"; fi
if [[ -z "$CleanupProject" ]]; then CleanupProject="no"; fi
if [[ -z "$CleanupSession" ]]; then CleanupSession="no"; fi

# -- Check and set runQC_Custom
if [ -z "$runQC_Custom" ] || [ "$runQC_Custom" == "no" ]; then runQC_Custom=""; QuNexTurnkeyWorkflow=`printf '%s\n' "${QuNexTurnkeyWorkflow//runQC_Custom/}"`; fi

QuNexWorkDir="${SessionsFolder}/${CASE}"
QuNexProcessingDir="${STUDY_PATH}/processing"
QuNexMasterLogFolder="${STUDY_PATH}/processing/logs"
QuNexSpecsDir="${SessionsFolder}/specs"
QuNexRawInboxDir="${QuNexWorkDir}/inbox"
QuNexRawInboxDir_temp="${QuNexWorkDir}/inbox_temp"
QuNexCommand="${TOOLS}/${QUNEXREPO}/bin/qunex.sh"

if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
    SpecsBatchFileHeader="${QuNexSpecsDir}/${BATCH_PARAMETERS_FILENAME}"
    ProcessingBatchFile="${QuNexProcessingDir}/${BATCH_PARAMETERS_FILENAME}"
    SpecsMappingFile="${QuNexSpecsDir}/${SCAN_MAPPING_FILENAME}"
fi
if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
    BatchFileName=`basename ${BATCH_PARAMETERS_FILENAME}`
    MappingFileName=`basename ${SCAN_MAPPING_FILENAME}`
    SpecsMappingFile="${QuNexSpecsDir}/${MappingFileName}"
    SpecsBatchFileHeader="${QuNexSpecsDir}/${BatchFileName}"
    ProcessingBatchFile="${QuNexProcessingDir}/${BatchFileName}"
fi

# -- Report options
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   "
echo "   QuNex Turnkey run type: ${TURNKEY_TYPE}"
echo "   QuNex Turnkey clean interim files: ${TURNKEY_CLEAN}"

if [ "$TURNKEY_TYPE" == "xnat" ]; then
    echo "   XNAT Hostname: ${XNAT_HOST_NAME}"
    echo "   XNAT Project ID: ${XNAT_PROJECT_ID}"
    echo "   XNAT Subject Label: ${XNAT_SUBJECT_LABEL}"
    echo "   XNAT Subject ID: ${XNAT_SUBJECT_ID}"
    echo "   XNAT Session Label: ${XNAT_SESSION_LABEL}"
    echo "   XNAT Session ID: ${XNAT_ACCSESSION_ID}"
    echo "   XNAT Resource Mapping file: ${SCAN_MAPPING_FILENAME}"
    echo "   XNAT Resource Project-specific Batch file: ${BATCH_PARAMETERS_FILENAME}"
    if [ "$DATAFormat" == "BIDS" ]; then
        echo "   BIDS format input specified!"
        echo "   Combined BIDS-formatted session name: ${CASE}"
    else
        echo "   QuNex Session variable name: ${CASE}"
    fi
fi
if [ "$TURNKEY_TYPE" != "xnat" ]; then
    echo "   Local project name: ${PROJECT_NAME}"
    echo "   Raw data input path: ${RawDataInputPath}"
    echo "   QuNex Session variable name: ${CASE}"
    echo "   QuNex Parameters file input: ${BATCH_PARAMETERS_FILENAME}"
    echo "   QuNex Mapping file input: ${SCAN_MAPPING_FILENAME}"
fi

echo "   QuNex Project-specific final Batch file path: ${QuNexProcessingDir}"
echo "   QuNex Study folder: ${STUDY_PATH}"
echo "   QuNex Log folder: ${QuNexMasterLogFolder}"
echo "   QuNex Session-specific working folder: ${QuNexRawInboxDir}"
echo "   Overwrite for a given turnkey step set to: ${OVERWRITE_STEP}"
echo "   Overwrite for session set to: ${OVERWRITE_SESSION}"
echo "   Overwrite for project set to: ${OVERWRITE_PROJECT}"
echo "   Overwrite for the entire XNAT project: ${OVERWRITE_PROJECT_XNAT}"
echo "   Cleanup for session set to: ${CleanupSession}"
echo "   Cleanup for project set to: ${CleanupProject}"
echo "   Custom QC requested: ${runQC_Custom}"

if [ "$runQC_Custom" == "yes" ]; then
    echo "   Custom QC modalities: ${Modality}"
fi

if [ "$Modality" == "BOLD" ] || [ "$Modality" == "bold" ]; then
    if [[ ! -z ${BOLDRUNS} ]]; then
        echo "   BOLD runs requested: ${BOLDRUNS}"
    else
        echo "   BOLD runs requested: all"
    fi
    if [[ ! -z ${BOLDfc} ]]; then
        echo "   BOLD FC requested: ${BOLDfc}"
        echo "   BOLD FC input: ${BOLDfcInput}"
        echo "   BOLD FC path: ${BOLDfcPath}"
    fi
fi

if [ "$Modality" = "general" ]; then
    echo "  Data input path: ${GeneralSceneDataPath}"
    echo "  Data input: ${GeneralSceneDataFile}"
fi

if [[ ! -z "${SESSIONIDS}" ]]; then
echo "   Sessionids parameter: ${SESSIONIDS}"
fi

if [ "$TURNKEY_STEPS" == "all" ]; then
    echo "   Turnkey workflow steps: ${QuNexTurnkeyWorkflow}"
else
    echo "   Turnkey workflow steps: ${TURNKEY_STEPS}"
fi

echo "   Acceptance test requested: ${AcceptanceTest}"
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
echo ""
echo "------------------------- Starting QuNex Turnkey Workflow --------------------------------"
echo ""


# --- Report the environment variables for QuNex Turnkey run:
echo ""
bash ${TOOLS}/${QUNEXREPO}/env/qunex_env_status.sh --envstatus
echo ""

# ---- Map the data from input to output when in XNAT workflow
if [[ ${TURNKEY_TYPE} == "xnat" ]] ; then
    # --- Specify what to map
    firstStep=`echo ${TURNKEY_STEPS} | awk '{print $1;}'`
    echo ""; echo " ---> RUNNING run_turnkey step ~~~ Initial data re-map from XNAT with ${firstStep} as starting point ."; echo ""
    # --- Study folder created in `qunex.sh`
    echo " -- Mapping existing data into place to support the first turnkey step: ${firstStep}"; echo ""
    # --- Work through the mapping steps
    case ${firstStep} in
        create_session_info) # create_session_info setup_hcp create_batch export_hcp
            RsyncCommand="rsync -avzH \
            --include='/${SessionsFolderName}' \
            --include='/${SessionsFolderName}/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/*.txt' \
            --include='/${SessionsFolderName}/${CASE}/nii' \
            --include='/${SessionsFolderName}/${CASE}/nii/***' \
            --include='/${SessionsFolderName}/specs' \
            --include='/${SessionsFolderName}/specs/***' \
            --include='/processing' \
            --include='/processing/*.txt' \
            --include='/processing/scenes' \
            --include='/processing/scenes/***' \
            --exclude='*' \
            ${XNAT_STUDY_INPUT_PATH}/ ${STUDY_PATH}"
            echo ""; echo " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        hcp_pre_freesurfer) # hcp_pre_freesurfer hcp_freesurfer hcp_post_freesurfer run_qc_t1w run_qc_t2w run_qc_myelin
            RsyncCommand="rsync -avzH \
            --include='/${SessionsFolderName}' \
            --include='/${SessionsFolderName}/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/*.txt' \
            --include='/${SessionsFolderName}/${CASE}/hcp' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/unprocessed' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/unprocessed/***' \
            --include='/${SessionsFolderName}/specs' \
            --include='/${SessionsFolderName}/specs/***' \
            --include='/processing' \
            --include='/processing/*.txt' \
            --include='/processing/scenes' \
            --include='/processing/scenes/***' \
            --exclude='*' \
            ${XNAT_STUDY_INPUT_PATH}/ ${STUDY_PATH}"
            echo ""; echo " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        hcp_freesurfer) # hcp_freesurfer hcp_post_freesurfer run_qc_t1w run_qc_t2w run_qc_myelin
            RsyncCommand="rsync -avzH \
            --include='/${SessionsFolderName}' \
            --include='/${SessionsFolderName}/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/*.txt' \
            --include='/${SessionsFolderName}/${CASE}/hcp' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/*nii*' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/xfms' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/xfms/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T2w' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T2w/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/unprocessed' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/unprocessed/***' \
            --include='/${SessionsFolderName}/specs' \
            --include='/${SessionsFolderName}/specs/***' \
            --include='/processing' \
            --include='/processing/*.txt' \
            --include='/processing/scenes' \
            --include='/processing/scenes/***' \
            --exclude='*' \
            --exclude='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/${CASE}' \
            ${XNAT_STUDY_INPUT_PATH}/ ${STUDY_PATH}"
            echo ""; echo " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        hcp_post_freesurfer) # hcp_freesurfer hcp_post_freesurfer run_qc_t1w run_qc_t2w run_qc_myelin
            RsyncCommand="rsync -avzH \
            --include='/${SessionsFolderName}' \
            --include='/${SessionsFolderName}/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/*.txt' \
            --include='/${SessionsFolderName}/${CASE}/hcp' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/*nii*' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/xfms' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/xfms/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T2w' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T2w/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/unprocessed' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/unprocessed/***' \
            --include='/${SessionsFolderName}/specs' \
            --include='/${SessionsFolderName}/specs/***' \
            --include='/processing' \
            --include='/processing/*.txt' \
            --include='/processing/scenes' \
            --include='/processing/scenes/***' \
            --exclude='*' \
            --exclude='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/*Results*' \
            --exclude='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage_LR32k' \
            --exclude='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage' \
            ${XNAT_STUDY_INPUT_PATH}/ ${STUDY_PATH}"
            echo ""; echo " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        run_qc_t1w|run_qc_t2w|run_qc_myelin|run_qc_bold)
            # --- rsync relevant dependencies if and hcp or QC step is starting point
            RsyncCommand="rsync -avzH \
            --include='/${SessionsFolderName}' \
            --include='/${SessionsFolderName}/specs' \
            --include='/${SessionsFolderName}/specs/***' \
            --include='/${SessionsFolderName}/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/*.txt' \
            --include='/${SessionsFolderName}/${CASE}/hcp/' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/*Results*' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/Results' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/Results/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/*nii*' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/*gii*' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/xfms/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/ROIs/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/Native/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage_LR32k/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T2w/***' \
            --include='/processing' \
            --include='/processing/*.txt' \
            --include='/processing/scenes' \
            --include='/processing/scenes/***' \
            --exclude='*' \
            ${XNAT_STUDY_INPUT_PATH}/ ${STUDY_PATH}"
            echo ""; echo " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        hcp_fmri_volume) # hcp_fmri_volume hcp_fmri_surface run_qc_bold
            RsyncCommand="rsync -avzH \
            --include='/${SessionsFolderName}' \
            --include='/${SessionsFolderName}/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/*.txt' \
            --include='/${SessionsFolderName}/${CASE}/hcp' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/*nii*' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/Native' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/Native/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/ROIs' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/ROIs/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage_LR32k' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage_LR32k/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/xfms' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/xfms/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/${CASE}/mri' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/${CASE}/mri/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/${CASE}/surf' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/${CASE}/surf/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/*nii*' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/unprocessed' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/unprocessed/***' \
            --include='/${SessionsFolderName}/specs' \
            --include='/${SessionsFolderName}/specs/***' \
            --include='/processing' \
            --include='/processing/*.txt' \
            --include='/processing/scenes' \
            --include='/processing/scenes/***' \
            --exclude='*' \
            ${XNAT_STUDY_INPUT_PATH}/ ${STUDY_PATH}"
            echo ""; echo " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        map_hcp_data)
            RsyncCommand="rsync -avzH \
            --include='/${SessionsFolderName}' \
            --include='/${SessionsFolderName}/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/*.txt' \
            --include='/${SessionsFolderName}/${CASE}/hcp' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/*nii*' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/Native' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/Native/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/ROIs' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/ROIs/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/Results' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/Results/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage_LR32k' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage_LR32k/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/xfms' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/xfms/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/${CASE}/mri' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/${CASE}/mri/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/${CASE}/surf' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/${CASE}/surf/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/*nii*' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/unprocessed' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/unprocessed/***' \
            --include='/${SessionsFolderName}/specs' \
            --include='/${SessionsFolderName}/specs/***' \
            --include='/processing' \
            --include='/processing/*.txt' \
            --include='/processing/scenes' \
            --include='/processing/scenes/***' \
            --exclude='*' \
            ${XNAT_STUDY_INPUT_PATH}/ ${STUDY_PATH}"
            echo ""; echo " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        create_bold_brain_masks|compute_bold_stats|create_stats_report|extract_nuisance_signal|preprocess_bold|preprocess_conc|general_plot_bold_timeseries|parcellate_bold|compute_bold_fc_gbc|compute_bold_fc_seed|run_qc_bold_fc)
            RsyncCommand="rsync -avzH \
            --include='/${SessionsFolderName}' \
            --include='/${SessionsFolderName}/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/*.txt' \
            --include='/${SessionsFolderName}/${CASE}/images' \
            --include='/${SessionsFolderName}/${CASE}/images/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/T1w_restore.nii.gz' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage_LR32k' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage_LR32k/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/*Results*' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/Results' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/Results/***' \
            --include='/${SessionsFolderName}/specs' \
            --include='/${SessionsFolderName}/specs/***' \
            --include='/processing' \
            --include='/processing/*.txt' \
            --include='/processing/scenes' \
            --include='/processing/scenes/***' \
            --exclude='*' \
            ${XNAT_STUDY_INPUT_PATH}/ ${STUDY_PATH}"
            echo ""; echo " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        hcp_diffusion|run_qc_dwi|dwi_legacy_gpu|dwi_eddy_qc|run_qc_dwi_eddy|dwi_dtifit|run_qc_dwi_dtifit|dwi_bedpostx_gpu|run_qc_dwi_process|run_qc_dwi_bedpostx)
            # --- rsync relevant dependencies if and hcp or QC step is starting point
            RsyncCommand="rsync -avzH \
            --include='/${SessionsFolderName}' \
            --include='/${SessionsFolderName}/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/*.txt' \
            --include='/${SessionsFolderName}/${CASE}/hcp' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/Diffusion' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/Diffusion/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/Diffusion' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/Diffusion/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/MNINonLinear/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T1w/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T2w' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/T2w/***' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/unprocessed' \
            --include='/${SessionsFolderName}/${CASE}/hcp/${CASE}/unprocessed/***' \
            --include='/${SessionsFolderName}/specs' \
            --include='/${SessionsFolderName}/specs/***' \
            --include='/processing' \
            --include='/processing/*.txt' \
            --include='/processing/scenes' \
            --include='/processing/scenes/***' \
            --exclude='*' \
            ${XNAT_STUDY_INPUT_PATH}/ ${STUDY_PATH}"
            echo ""; echo " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        dwi_pre_tractography|dwi_seed_tractography_dense|dwi_parcellate)
            # --- rsync relevant dependencies if and hcp or QC step is starting point
            RsyncCommand="rsync -avzH --include='/processing' --include='scenes/***' --include='specs/***' --include='/${SessionsFolderName}' --include='${CASE}' --include='*.txt' --include='hcp/' --include='T1w/***' --include='MNINonLinear/*nii*' --include='MNINonLinear/*gii*' --include='MNINonLinear/xfms/***' --include='MNINonLinear/ROIs/***' --include='MNINonLinear/Native/***' --include='MNINonLinear/fsaverage/***' --include='MNINonLinear/fsaverage_LR32k/***' --include='MNINonLinear/Results/Tractography/*nii*' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${STUDY_PATH}"
            echo ""; echo " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
    esac

    # -- Fetch latest batch file, mapping file, and qc scene from XNAT HOST
    echo "  curl -k -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${BATCH_PARAMETERS_FILENAME}""
    echo "  curl -k -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${SCAN_MAPPING_FILENAME}""
    echo "  curl -k -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc/files?format=zip" > ${QuNexProcessingDir}/scenes/QC/scene_qc_files.zip"

    curl -k -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${BATCH_PARAMETERS_FILENAME}" > ${QuNexSpecsDir}/${BATCH_PARAMETERS_FILENAME}
    curl -k -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${SCAN_MAPPING_FILENAME}" > ${QuNexSpecsDir}/${SCAN_MAPPING_FILENAME}
    curl -k -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc/files?format=zip" > ${QuNexProcessingDir}/scenes/QC/scene_qc_files.zip

    echo ""; echo " ---> run_turnkey ~~~ DONE: Initial data re-map from XNAT for ${firstStep} done."; echo ""
fi

# -- Check if overwrite is set to yes for session and project
if [[ ${OVERWRITE_PROJECT_FORCE} == "yes" ]]; then
        echo " ---> Force overwrite for entire project requested. Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        echo -n "     Confirm by typing 'yes' and then press [ENTER]: "
        read ManualOverwrite
        echo
        if [[ ${ManualOverwrite} == "yes" ]]; then
            rm -rf ${StudyFolder}/ &> /dev/null
        fi
fi
if [[ ${OVERWRITE_PROJECT_XNAT} == "yes" ]]; then
        echo " -- Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${StudyFolder}/ &> /dev/null
fi
if [[ ${OVERWRITE_PROJECT} == "yes" ]] && [[ ${TURNKEY_STEPS} == "all" ]]; then
    if [[ `ls -IQC -Ilists -Ispecs -Iinbox -Iarchive ${SessionsFolder}` == "$CASE" ]]; then
        echo " -- ${CASE} is the only folder in ${SessionsFolder}. OK to proceed!"
        echo "    Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${StudyFolder}/ &> /dev/null
    else
        echo " -- ${CASE} is not the only folder in ${StudyFolder}."
        echo "    Skipping recursive overwrite for project: ${XNAT_PROJECT_ID}"; echo ""
    fi
fi
if [[ ${OVERWRITE_PROJECT} == "yes" ]] && [[ ${TURNKEY_STEPS} == "create_study" ]]; then
    if [[ `ls -IQC -Ilists -Ispecs -Iinbox -Iarchive ${SessionsFolder}` == "$CASE" ]]; then
        echo " -- ${CASE} is the only folder in ${SessionsFolder}. OK to proceed!"
        echo "    Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${StudyFolder}/ &> /dev/null
    else
        echo " -- ${CASE} is not the only folder in ${StudyFolder}."
        echo "    Skipping recursive overwrite for project: ${XNAT_PROJECT_ID}"; echo ""
    fi
fi
if [[ ${OVERWRITE_SESSION} == "yes" ]]; then
    echo " -- Removing specific session: ${QuNexWorkDir}"; echo ""
    rm -rf ${QuNexWorkDir} &> /dev/null
fi


# =-=-=-=-=-=-= TURNKEY COMMANDS START =-=-=-=-=-=-=
#
#
    # --------------- Intial study and file organization start -----------------
    #
    # -- Create study hieararchy and generate session folders
    turnkey_create_study() {

        echo ""; echo " ---> RUNNING run_turnkey step ~~~ create_study"; echo ""

        echo " -- Checking for and generating study folder ${StudyFolder}"; echo ""
        if [ ! -d ${WORKDIR} ]; then
            mkdir -p ${WORKDIR} &> /dev/null
        fi
        if [ ! -d ${StudyFolder} ]; then
            echo " ---> Note: ${StudyFolder} not found. Regenerating now..."
            echo ""
            ${QuNexCommand} create_study --studyfolder="${StudyFolder}"
            mv ${createStudy_ComlogTmp} ${QuNexMasterLogFolder}/comlogs/
        else
            echo " -- Study folder ${StudyFolder} already exists!"
            if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
                if [[ ${OVERWRITE_PROJECT_XNAT} == "yes" ]]; then
                    echo "    Overwrite set to 'yes' for XNAT run. Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
                    rm -rf ${StudyFolder}/ &> /dev/null
                    echo " ---> Note: ${StudyFolder} removed. Regenerating now..."
                    echo ""
                    ${QuNexCommand} create_study --studyfolder="${StudyFolder}"
                    mv ${createStudy_ComlogTmp} ${QuNexMasterLogFolder}/comlogs/
                fi
            fi
        fi
        if [ ! -f ${StudyFolder}/.qunexstudy ]; then
            echo " ---> Note: ${StudyFolder}/.qunexstudy file not found. Not a proper QuNex file hierarchy. Regenerating now."; echo "";
            ${QuNexCommand} create_study --studyfolder="${StudyFolder}"
        fi

        mkdir -p ${QuNexWorkDir} &> /dev/null
        mkdir -p ${QuNexWorkDir}/inbox &> /dev/null
        mkdir -p ${QuNexWorkDir}/inbox_temp &> /dev/null
    }

    # -- Get data from original location & organize DICOMs
    turnkey_map_raw_data() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ map_raw_data"; echo ""
        TimeStamp=`date +%Y-%m-%d_%H.%M.%S.%6N`

        # Perform checks for output QuNex hierarchy
        if [ ! -d ${WORKDIR} ]; then
            mkdir -p ${WORKDIR} &> /dev/null
        fi
        if [ ! -d ${StudyFolder} ]; then
            echo " ---> Note: ${StudyFolder} not found. Regenerating now."; echo "";
            ${QuNexCommand} create_study --studyfolder="${StudyFolder}"
        fi
        if [ ! -f ${StudyFolder}/.qunexstudy ]; then
            echo " ---> Note: ${StudyFolder} qunexstudy file not found. Not a proper QuNex file hierarchy. Regenerating now."; echo "";
            ${QuNexCommand} create_study --studyfolder="${StudyFolder}"
        fi
        if [ ! -d ${SessionsFolder} ]; then
            echo " ---> Note: ${SessionsFolder} folder not found. Not a proper QuNex file hierarchy. Regenerating now."; echo "";
            ${QuNexCommand} create_study --studyfolder="${StudyFolder}"
        fi
        if [ ! -d ${QuNexWorkDir} ]; then
            echo " ---> Note: ${QuNexWorkDir} not found. Creating one now."; echo ""
            mkdir -p ${QuNexWorkDir} &> /dev/null
            mkdir -p ${QuNexWorkDir}/inbox &> /dev/null
            mkdir -p ${QuNexWorkDir}/inbox_temp &> /dev/null
        fi

        # -- Perform overwrite checks
        if [[ ${OVERWRITE_STEP} == "yes" ]] && [[ ${TURNKEY_STEP} == "map_raw_data" ]]; then
               rm -rf ${QuNexWorkDir}/inbox/* &> /dev/null
        fi
        CheckInbox=`ls -1A ${QuNexRawInboxDir} | wc -l`
        if [[ ${CheckInbox} != "0" ]] && [[ ${OVERWRITE_STEP} == "no" ]]; then
               echo "ERROR: ${QuNexWorkDir}/inbox/ is not empty and --overwritestep=${OVERWRITE_STEP} "
               echo "Set overwrite to 'yes' and re-run..."
               echo ""
               exit 1
        fi

        # -- Define specific logs
        mapRawData_Runlog="${QuNexMasterLogFolder}/runlogs/Log-map_raw_data_${TimeStamp}.log"; touch ${mapRawData_Runlog}; chmod 777 ${mapRawData_Runlog}
        mapRawData_ComlogTmp="${QuNexMasterLogFolder}/comlogs/tmp_map_raw_data_${CASE}_${TimeStamp}.log"; touch ${mapRawData_ComlogTmp}; chmod 777 ${mapRawData_ComlogTmp}
        mapRawData_ComlogError="${QuNexMasterLogFolder}/comlogs/error_map_raw_data_${CASE}_${TimeStamp}.log"
        mapRawData_ComlogDone="${QuNexMasterLogFolder}/comlogs/done_map_raw_data_${CASE}_${TimeStamp}.log"

        # -- Add header to log
        echo "# Generated by QuNex ${QuNexVer} on ${TimeStamp}" >> ${mapRawData_Runlog}
        echo "#" >> ${mapRawData_Runlog}
        echo "# Generated by QuNex ${QuNexVer} on ${TimeStamp}" >> ${mapRawData_ComlogTmp}
        echo "#" >> ${mapRawData_ComlogTmp}

        # -- Map data from XNAT
        if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
            echo " ---> Running turnkey via XNAT: ${XNAT_HOST_NAME}"; echo ""
            RawDataInputPath="/input/SCANS/"
            rm -rf ${QuNexSpecsDir}/${BATCH_PARAMETERS_FILENAME} &> /dev/null
            rm -rf ${QuNexSpecsDir}/${SCAN_MAPPING_FILENAME} &> /dev/null
            rm -rf ${QuNexProcessingDir}/scenes/QC/* &> /dev/null
            echo " -- Fetching parameters and mapping files from ${XNAT_HOST_NAME}"; echo ""
            echo "" >> ${mapRawData_ComlogTmp}
            echo "  Logging turnkey_map_raw_data output at time ${TimeStamp}:" >> ${mapRawData_ComlogTmp}
            echo "----------------------------------------------------------------------------------------" >> ${mapRawData_ComlogTmp}
            echo "" >> ${mapRawData_ComlogTmp}

            # -- Transfer data from XNAT HOST
            echo "  curl -k -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${BATCH_PARAMETERS_FILENAME}""
            echo "  curl -k -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${SCAN_MAPPING_FILENAME}""
            echo "  curl -k -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc/files?format=zip" > ${QuNexProcessingDir}/scenes/QC/scene_qc_files.zip"
            echo ""
            echo "  curl -k -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${BATCH_PARAMETERS_FILENAME}"" >> ${mapRawData_ComlogTmp}
            echo "  curl -k -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${SCAN_MAPPING_FILENAME}"" >> ${mapRawData_ComlogTmp}
            echo "  curl -k -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc/files?format=zip" > ${QuNexProcessingDir}/scenes/QC/scene_qc_files.zip"  >> ${mapRawData_ComlogTmp}

            curl -k -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${BATCH_PARAMETERS_FILENAME}" > ${QuNexSpecsDir}/${BATCH_PARAMETERS_FILENAME}
            curl -k -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${SCAN_MAPPING_FILENAME}" > ${QuNexSpecsDir}/${SCAN_MAPPING_FILENAME}
            curl -k -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc/files?format=zip" > ${QuNexProcessingDir}/scenes/QC/scene_qc_files.zip

            # -- Verify and unzip custom QC scene files
            if [ -f ${QuNexProcessingDir}/scenes/QC/scene_qc_files.zip ]; then
                echo ""; echo " -- Custom scene files found ${QuNexProcessingDir}/scenes/QC/scene_qc_files.zip "
                echo ""; echo " -- Checking ZIP integrity for ${QuNexProcessingDir}/scenes/QC/scene_qc_files.zip "
                CheckCustomQCScene=`zip -T ${QuNexProcessingDir}/scenes/QC/scene_qc_files.zip | grep "error"`
                if [[ ! -z ${CheckCustomQCScene} ]]; then
                    echo "" >> ${mapRawData_ComlogTmp}
                    echo " ---> Note: QC scene zip file not validated. Custom scene may be missing or is corrupted." >> ${mapRawData_ComlogTmp}
                    echo "" >> ${mapRawData_ComlogTmp}
                    echo ""; echo " ---> Note: QC scene zip file not validated. Custom scene may be missing or is corrupted."; echo ""
                else
                    echo " Unzipping ${QuNexProcessingDir}/scenes/QC/scene_qc_files.zip" >> ${mapRawData_ComlogTmp}
                    echo "" >> ${mapRawData_ComlogTmp}
                    cd ${QuNexProcessingDir}/scenes/QC; echo ""
                    unzip scene_qc_files.zip; echo ""
                    CustomQCModalities="T1w T2w myelin DWI BOLD"
                    for CustomQCModality in ${CustomQCModalities}; do
                        mkdir -p ${QuNexProcessingDir}/scenes/QC/${CustomQCModality} &> /dev/null
                        cp ${QuNexProcessingDir}/scenes/QC/${XNAT_PROJECT_ID}/resources/scenes_qc/files/${CustomQCModality}/*.scene ${QuNexProcessingDir}/scenes/QC/${CustomQCModality}/ &> /dev/null
                        CopiedSceneFile=`ls ${QuNexProcessingDir}/scenes/QC/${CustomQCModality}/*scene 2> /dev/null`
                        if [ ! -z ${CopiedSceneFile} ]; then
                            echo " -- Copied: $CopiedSceneFile"; echo ""
                            echo " Copied the following scenes from ${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc:" >> ${mapRawData_ComlogTmp}
                            echo " ${CopiedSceneFile}" >> ${mapRawData_ComlogTmp}
                        fi
                    done
                    rm -rf ${QuNexProcessingDir}/scenes/QC/${XNAT_PROJECT_ID} &> /dev/null
                    echo "" >> ${mapRawData_ComlogTmp}
                fi
           else
                echo " No custom scene files found as an XNAT resources. If this is an error check your project resources in the XNAT web interface." >> ${mapRawData_ComlogTmp}
                echo "" >> ${mapRawData_ComlogTmp}
           fi

            # -- Perform checks for parameters and mapping files being mapped correctly
            if [[ ! -f ${QuNexSpecsDir}/${BATCH_PARAMETERS_FILENAME} ]]; then
                echo " ---> ERROR: Scan parameters file ${BATCH_PARAMETERS_FILENAME} not found in ${RawDataInputPath}!"
                BATCHFILECHECK="fail"
                exit 1
            fi
            if [[ ! -f ${QuNexSpecsDir}/${SCAN_MAPPING_FILENAME} ]]; then
                echo " ---> ERROR: Scan mapping file ${SCAN_MAPPING_FILENAME_PATH} not found in ${RawDataInputPath}!"
                MAPPINGFILECHECK="fail"
                exit 1
            else
                if [[ ! `cat ${QuNexSpecsDir}/${SCAN_MAPPING_FILENAME} | grep '=>'` ]]; then
                    echo " ---> ERROR: Scan mapping file ${SCAN_MAPPING_FILENAME_PATH} not found in ${RawDataInputPath}!"
                    MAPPINGFILECHECK="fail"
                    exit 1
                fi
            fi
        fi

        # -- Map data for local non-XNAT run
        if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
            echo " ---> Running turnkey via local: `hostname`"; echo ""
            if [[ ! -f ${SpecsBatchFileHeader} ]]; then
                if [[ -f ${BATCH_PARAMETERS_FILE_PATH} ]]; then
                    cp ${BATCH_PARAMETERS_FILE_PATH} ${SpecsBatchFileHeader} >> ${mapRawData_ComlogTmp}
                else
                    echo " ---> ERROR: Parameters file ${BATCH_PARAMETERS_FILENAME} not found in ${RawDataInputPath}!"
                fi
            fi
            if [[ ! -f ${SpecsMappingFile} ]]; then
                if [[ -f ${SCAN_MAPPING_FILENAME_PATH} ]]; then
                    echo "  cp ${SCAN_MAPPING_FILENAME_PATH} ${SpecsMappingFile}"
                    cp ${SCAN_MAPPING_FILENAME_PATH} ${SpecsMappingFile} >> ${mapRawData_ComlogTmp}
                else
                    echo " ---> ERROR: Scan mapping file ${SCAN_MAPPING_FILENAME_PATH} not found in ${RawDataInputPath}!"
                fi
            fi
        fi

        # -- Check if BIDS format NOT requested
        if [[ ${DATAFormat} == "DICOM" ]]; then
            unset FILECHECK
            echo ""
            echo " -- Linking DICOMs into ${QuNexRawInboxDir}" 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
            # -- Find and link DICOMs for XNAT run
            if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
                RsyncCommand='rsync -azH --exclude "*.xml" --exclude "*.gif" ${RawDataInputPath}/ ${QuNexRawInboxDir}'
                echo ""; echo " -- Running rsync: ${RsyncCommand}"; echo ""
                eval ${RsyncCommand}
                DicomInputCount=`find ${RawDataInputPath} -type f -not -name "*.xml" -not -name "*.gif" | wc | awk '{print $1}'`
                DicomMappedCount=`find ${QuNexRawInboxDir} -type f -not -name "*.xml" -not -name "*.gif" | wc | awk '{print $1}'`
                if [[ ${DicomInputCount} == ${DicomMappedCount} ]]; then FILECHECK="pass"; else FILECHECK="fail"; fi
            fi
            # -- Find and link DICOMs for non-XNAT run
            if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
                # -- Check if we have an archive in a folder
                if [[ "$(ls ${RawDataInputPath}/${CASE}*zip* 2> /dev/null)" ]] || [[ "$(ls ${RawDataInputPath}/${CASE}*gz* 2> /dev/null)" ]]; then
                    InputArchive="yes"
                    # -- Hard link into session inbox
                    cp ${RawDataInputPath}/${CASE}*gz ${SessionsFolder}/${CASE}/inbox/ &> /dev/null
                    cp ${RawDataInputPath}/${CASE}*zip ${SessionsFolder}/${CASE}/inbox/ &> /dev/null
                    CheckCASECount=`ls ${SessionsFolder}/${CASE}/inbox/${CASE}* | wc -l`
                    # -- Check for duplicates
                    if [[ "$CheckCASECount" -gt "1" ]]; then
                        echo " ---> ERROR: More than one zip file found for ${CASE}" 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                        echo ""
                        FILECHECK="fail"
                    fi
                    CASEinbox=`basename ${SessionsFolder}/${CASE}/inbox/${CASE}*`
                    CASEext="${CASEinbox#*.}"
                    if [[ ${CASEext} == "zip" ]]; then
                        cd ${SessionsFolder}/${CASE}/inbox/
                        if [[ ! -z `unzip -t ${CASEinbox} 2>&1 | tee -a ${mapRawData_ComlogTmp} | grep 'No errors'` ]]; then
                            echo "   ZIP archive found and passed check." 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                            FILECHECK="pass"
                        else
                            echo " ---> ERROR: ZIP archive found but did not pass check!" 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                            FILECHECK="fail"
                        fi
                    else
                        echo "   ${CASEext} archive found." 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                        FILECHECK="pass"
                    fi
                else
                    # -- Find and link DICOMs for non-XNAT run from raw DICOM input
                    if [ -d "${RawDataInputPath}/${CASE}" ]; then
                        CaseInputFile="${RawDataInputPath}/${CASE}"
                    else
                        CaseInputFile="${RawDataInputPath}"
                    fi
                    RsyncCommand='rsync -azH --exclude "*.xml" --exclude "*.gif" --exclude "*.sh" --exclude "*.txt" --exclude ".*" ${CaseInputFile}/ ${QuNexRawInboxDir}'
                    echo ""; echo " -- Running rsync: ${RsyncCommand}"; echo ""
                    eval ${RsyncCommand}
                    DicomInputCount=`find ${CaseInputFile} -type f -not -name "*.xml" -not -name "*.gif" -not -name "*.sh" -not -name "*.txt" -not -name ".*" | wc | awk '{print $1}'`
                    DicomMappedCount=`find ${QuNexRawInboxDir} -type f -not -name ".*" | wc | awk '{print $1}'`
                    # DicomMappedCount=`ls ${QuNexRawInboxDir}/* | wc | awk '{print $1}'`
                    if [[ ${DicomInputCount} == ${DicomMappedCount} ]]; then FILECHECK="pass"; else FILECHECK="fail"; fi
                fi
            fi
        fi

        # -- Check if BIDS format is requested
        if [[ ${DATAFormat} == "BIDS" ]]; then
            unset INTYPE
            unset FILECHECK

            if [[ -z "${BIDS_NAME}" ]]; then
                bids_name_parameter=""
            else
                bids_name_parameter="--bidsname=\"${BIDS_NAME}\""
            fi

            if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
                # -- Set IF statement to check if /input mapped from XNAT for container run or curl call needed
                if [[ -d ${RawDataInputPath} ]]; then
                   if [[ `find ${RawDataInputPath} -type f -name "*.json" | wc -l` -gt 0 ]] && [[ `find ${RawDataInputPath} -type f -name "*.nii" | wc -l` -gt 0 ]]; then
                       echo ""; echo " -- BIDS JSON and NII data found"; echo ""
                       mkdir ${SessionsFolder}/inbox/BIDS/${CASE} &> /dev/null
                       cp -r ${RawDataInputPath}/* ${SessionsFolder}/inbox/BIDS/${CASE}/
                       cd ${SessionsFolder}/inbox/BIDS
                       zip -r ${CASE} ${CASE} 2> /dev/null
                   else
                       echo ""
                       echo " -- Running:  " 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                       echo "  curl -k -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${SessionsFolder}/inbox/BIDS/${CASE}.zip " 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                       curl -k -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${SessionsFolder}/inbox/BIDS/${CASE}.zip
                   fi
                else
                    # -- Get the BIDS data in ZIP format via curl
                    echo ""
                    echo " -- Running:  " 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                    echo "  curl -k -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${SessionsFolder}/inbox/BIDS/${CASE}.zip " 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                    curl -k -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${SessionsFolder}/inbox/BIDS/${CASE}.zip
                fi
                INTYPE=zip
            else
                # --- we have a zip file
                if [ -e ${RawDataInputPath}/${CASE}.zip ]; then
                    cp -r ${RawDataInputPath}/${CASE}.zip ${SessionsFolder}/inbox/BIDS/${CASE}.zip
                    INTYPE=zip
                else
                    INTYPE=dataset
                fi
            fi
            # -- Perform mapping of BIDS file structure into QuNex
            echo ""
            echo " -- Running:  " 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}

            if [[ ${INTYPE} == "zip" ]]; then
                echo "  ---> processing a single BIDS formated package [${CASE}.zip]" 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                echo "  ${QuNexCommand} import_bids --sessionsfolder=\"${SessionsFolder}\" --inbox=\"${SessionsFolder}/inbox/BIDS/${CASE}.zip\" --action=\"copy\" --overwrite=\"yes\" --archive=\"delete\" ${bids_name_parameter} " 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                ${QuNexCommand} import_bids --sessionsfolder="${SessionsFolder}" --inbox="${SessionsFolder}/inbox/BIDS/${CASE}.zip" --action="copy" --overwrite="yes" --archive="delete" ${bids_name_parameter} >> ${mapRawData_ComlogTmp}
            elif [[  ${INTYPE} == "dataset" ]]; then
                echo "  ---> processing a single BIDS session [${CASE}] from the BIDS dataset" 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                echo "  ${QuNexCommand} import_bids --sessionsfolder=\"${SessionsFolder}\" --inbox=\"${RawDataInputPath}\" --sessions=\"${CASE}\" --action=\"copy\" --overwrite=\"yes\" --archive=\"leave\" ${bids_name_parameter} " 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                ${QuNexCommand} import_bids --sessionsfolder="${SessionsFolder}" --inbox="${RawDataInputPath}" --sessions="${CASE}" --action="copy" --overwrite="yes" --archive="leave" ${bids_name_parameter} 2>&1 | tee -a ${mapRawData_ComlogTmp}; echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
            fi

            #popd > /dev/null
            rm -rf ${SessionsFolder}/inbox/BIDS/${CASE}* &> /dev/null

            # -- Run BIDS completion checks on mapped data
            if [ -f ${SessionsFolder}/${CASE}/bids/bids2nii.log ]; then
                 FILESEXPECTED=`cat ${SessionsFolder}/${CASE}/bids/bids2nii.log | grep ".nii.gz" | wc -l 2> /dev/null`
            else
                 FILECHECK="fail"
            fi
            FILEFOUND=`ls ${SessionsFolder}/${CASE}/nii/*.nii.gz | wc -l 2> /dev/null`
            if [ -z ${FILEFOUND} ]; then
                FILECHECK="fail"
            fi
            if [[ ${FILESEXPECTED} == ${FILEFOUND} ]]; then
                echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                echo " -- import_bids successful. Expected ${FILESEXPECTED} files and found ${FILEFOUND} files." 2>&1 | tee -a ${mapRawData_ComlogTmp}
                echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                FILECHECK="pass"
            else
                FILECHECK="fail"
            fi
        fi

        # -- Check if HCP format is requested
        if [[ ${DATAFormat} == "HCPLS" ]] || [[ ${DATAFormat} == "HCPYA" ]] ; then
            unset INTYPE
            unset FILECHECK

            if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
                # -- Set IF statement to check if /input mapped from XNAT for container run or curl call needed
                if [[ -d ${RawDataInputPath} ]]; then
                   if [[ `find ${RawDataInputPath} -type f -name "*T1w_MP*.nii.gz" | wc -l` -gt 0 ]]; then
                       echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                       echo " -- HCP DATA FOUND " 2>&1 | tee -a ${mapRawData_ComlogTmp}
                       echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                       mkdir ${SessionsFolder}/inbox/BIDS/${CASE} &> /dev/null
                       cp -r ${RawDataInputPath}/* ${SessionsFolder}/inbox/${DATAFormat}/${CASE}/
                       INTYPE=dataset
                   else
                       echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                       echo " -- Running:  " 2>&1 | tee -a ${mapRawData_ComlogTmp}
                       echo "  curl -k -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${SessionsFolder}/inbox/HCPLS/${CASE}.zip " 2>&1 | tee -a ${mapRawData_ComlogTmp}
                       echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                       curl -k -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${SessionsFolder}/inbox/HCPLS/${CASE}.zip
                   fi
                else
                    # -- Get the BIDS data in ZIP format via curl
                    echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                    echo " -- Running:  " 2>&1 | tee -a ${mapRawData_ComlogTmp}
                    echo "  curl -k -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${SessionsFolder}/inbox/HCPLS/${CASE}.zip " 2>&1 | tee -a ${mapRawData_ComlogTmp}
                    echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                    curl -k -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${SessionsFolder}/inbox/HCPLS/${CASE}.zip
                    INTYPE=zip
                fi
            else
                # --- we have a zip file
                if [ -e ${RawDataInputPath}/${CASE}.zip ]; then
                    cp -r ${RawDataInputPath}/${CASE}.zip ${SessionsFolder}/inbox/HCPLS/${CASE}.zip
                    INTYPE=zip
                else
                    INTYPE=dataset
                fi
            fi
            # -- Perform mapping of HCP file structure into QuNex
            echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
            echo " -- Running:  " 2>&1 | tee -a ${mapRawData_ComlogTmp}
            echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}

            if [[ ${INTYPE} == "zip" ]]; then
                echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}

                echo "  ---> processing a single ${DATAFormat} formated package [${CASE}.zip]" 2>&1 | tee -a ${mapRawData_ComlogTmp}

                # HCPYA requires custom nameformat
                if [[ ${DATAFormat} == "HCPYA" ]]; then
                    HCPLSNameFormat="(?P<subject_id>[^/]+?)/unprocessed/(?P<session_name>.*?)/(?P<data>.*)"
                    HCPLSName="hcpya"

                    echo "  ${QuNexCommand} import_hcp --sessionsfolder=\"${SessionsFolder}\" --inbox=\"${SessionsFolder}/inbox/HCPLS/${CASE}.zip\" --action=\"copy\" --overwrite=\"yes\" --archive=\"delete\" --nameformat=\"$HCPLSNameFormat\" --hcplsname=\"${HCPLSName}\" " 2>&1 | tee -a ${mapRawData_ComlogTmp}

                    echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}

                    ${QuNexCommand} import_hcp --sessionsfolder="${SessionsFolder}" --inbox="${SessionsFolder}/inbox/HCPLS/${CASE}.zip" --action="copy" --overwrite="yes" --archive="delete" --nameformat="$HCPLSNameFormat" --hcplsname="${HCPLSName}" >> ${mapRawData_ComlogTmp}
                else
                    HCPLSName="hcpls"

                    echo "  ${QuNexCommand} import_hcp --sessionsfolder=\"${SessionsFolder}\" --inbox=\"${SessionsFolder}/inbox/HCPLS/${CASE}.zip\" --action=\"copy\" --overwrite=\"yes\" --archive=\"delete\" --hcplsname=\"${HCPLSName}\" " 2>&1 | tee -a ${mapRawData_ComlogTmp}

                    echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}

                    ${QuNexCommand} import_hcp --sessionsfolder="${SessionsFolder}" --inbox="${SessionsFolder}/inbox/HCPLS/${CASE}.zip" --action="copy" --overwrite="yes" --archive="delete" --hcplsname="${HCPLSName}" >> ${mapRawData_ComlogTmp}
                fi

            elif [[  ${INTYPE} == "dataset" ]]; then
                echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}

                echo "  ---> processing a single ${DATAFormat} session [${CASE}] from the ${DATAFormat} dataset" 2>&1 | tee -a ${mapRawData_ComlogTmp}

                # HCPYA requires custom nameformat
                if [[ ${DATAFormat} == "HCPYA" ]]; then
                    HCPLSNameFormat="(?P<subject_id>[^/]+?)/unprocessed/(?P<session_name>.*?)/(?P<data>.*)"
                    HCPLSName="hcpya"

                    echo "  ${QuNexCommand} import_hcp --sessionsfolder=\"${SessionsFolder}\" --inbox=\"${RawDataInputPath}\" --sessions=\"${CASE}\" --action=\"copy\" --overwrite=\"yes\" --archive=\"leave\" --nameformat=\"$HCPLSNameFormat\" --hcplsname=\"${HCPLSName}\" " 2>&1 | tee -a ${mapRawData_ComlogTmp}

                    echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}

                    ${QuNexCommand} import_hcp --sessionsfolder="${SessionsFolder}" --inbox="${RawDataInputPath}" --sessions="${CASE}" --action="copy" --overwrite="yes" --archive="leave" --nameformat="$HCPLSNameFormat" --hcplsname="${HCPLSName}" >> ${mapRawData_ComlogTmp}
                else
                    HCPLSName="hcpls"

                    echo "  ${QuNexCommand} import_hcp --sessionsfolder=\"${SessionsFolder}\" --inbox=\"${RawDataInputPath}\" --sessions=\"${CASE}\" --action=\"copy\" --overwrite=\"yes\" --archive=\"leave\" --hcplsname=\"${HCPLSName}\" " 2>&1 | tee -a ${mapRawData_ComlogTmp}

                    echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}

                    ${QuNexCommand} import_hcp --sessionsfolder="${SessionsFolder}" --inbox="${RawDataInputPath}" --sessions="${CASE}" --action="copy" --overwrite="yes" --archive="leave" --hcplsname="${HCPLSName}" >> ${mapRawData_ComlogTmp}
                fi

            fi

            #popd > /dev/null
            rm -rf ${SessionsFolder}/inbox/HCPLS/${CASE}* &> /dev/null

            # -- Run HCPLS completion checks on mapped data
            if [ -f ${SessionsFolder}/${CASE}/hcpls/hcpls2nii.log ]; then
                FILESEXPECTED=`cat ${SessionsFolder}/${CASE}/hcpls/hcpls2nii.log | grep "=>" | wc -l 2> /dev/null`
            else
                FILECHECK="fail"
            fi
            FILEFOUND=`ls ${SessionsFolder}/${CASE}/nii/* | wc -l 2> /dev/null`
            if [ -z ${FILEFOUND} ]; then
                FILECHECK="fail"
            fi
            if [[ ${FILESEXPECTED} == ${FILEFOUND} ]]; then
                echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                echo " -- import_hcp successful. Expected ${FILESEXPECTED} files and found ${FILEFOUND} files." 2>&1 | tee -a ${mapRawData_ComlogTmp}
                echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                FILECHECK="pass"
            else
                FILECHECK="fail"
            fi
        fi

        # -- Clean up inbox_temp
        rm -r -p ${QuNexWorkDir}/inbox_temp &> /dev/null

        # -- Check if mapping and batch files exist and if content OK
        if [[ -f ${SpecsBatchFileHeader} ]]; then BATCHFILECHECK="pass"; else BATCHFILECHECK="fail"; fi
        if [[ ${DATAFormat} == "HCPLS" ]]; then
            MAPPINGFILECHECK=pass
        else
            if [[ -f ${SpecsMappingFile} ]]; then MAPPINGFILECHECK="pass"; else MAPPINGFILECHECK="fail"; fi
            if [[ -z `cat ${SpecsMappingFile} | grep '=>'` ]]; then MAPPINGFILECHECK="fail"; fi
        fi

        # -- Declare checks
        echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
        echo "----------------------------------------------------------------------------" 2>&1 | tee -a ${mapRawData_ComlogTmp}
        echo "  ---> Batch file transfer check: ${BATCHFILECHECK}" 2>&1 | tee -a ${mapRawData_ComlogTmp}
        echo "  ---> Mapping file transfer check: ${MAPPINGFILECHECK}" 2>&1 | tee -a ${mapRawData_ComlogTmp}
        if [[ ${DATAFormat} != "DICOM" ]]; then
            echo "  ---> ${DATAFormat} mapping check: ${FILECHECK}" 2>&1 | tee -a ${mapRawData_ComlogTmp}
        else
            if [[ ${InputArchive} != "yes" ]]; then
                echo "  ---> DICOM file count in input folder /input/SCANS: ${DicomInputCount}" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                echo "  ---> DICOM file count in output folder ${QuNexRawInboxDir}: ${DicomMappedCount}" 2>&1 | tee -a ${mapRawData_ComlogTmp}
                echo "  ---> DICOM mapping check: ${FILECHECK}" 2>&1 | tee -a ${mapRawData_ComlogTmp}
            fi
            if [[ ${InputArchive} == "yes" ]]; then
                echo "  ---> Archive inbox processed: ${FILECHECK}" 2>&1 | tee -a ${mapRawData_ComlogTmp}
            fi
        fi

        # -- Report and log final checks
        if [[ ${FILECHECK} == "pass" ]] && [[ ${BATCHFILECHECK} == "pass" ]] && [[ ${MAPPINGFILECHECK} == "pass" ]]; then
            echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
            echo "------------------------- Successful completion of work --------------------------------" 2>&1 | tee -a ${mapRawData_ComlogTmp}
            echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
            mv ${mapRawData_ComlogTmp} ${mapRawData_ComlogDone}
            mapRawData_Comlog=${mapRawData_ComlogDone}

            # runlog
            echo "map_raw_data" 2>&1 | tee -a ${mapRawData_Runlog}
            echo "" 2>&1 | tee -a ${mapRawData_Runlog}
            echo "------------------------- Successful completion of work --------------------------------" 2>&1 | tee -a ${mapRawData_Runlog}
        else
            echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
            echo "ERROR. Something went wrong." 2>&1 | tee -a ${mapRawData_ComlogTmp}
            echo "" 2>&1 | tee -a ${mapRawData_ComlogTmp}
            mv ${mapRawData_ComlogTmp} ${mapRawData_ComlogError}
            mapRawData_Comlog=${mapRawData_ComlogError}

            # runlog
            echo "map_raw_data"  2>&1 | tee -a ${mapRawData_Runlog}
            echo "" 2>&1 | tee -a ${mapRawData_Runlog}
            echo "ERROR. Something went wrong." 2>&1 | tee -a ${mapRawData_Runlog}
        fi
    }

    # -- import_dicom
    turnkey_import_dicom() {
        if [[ ${DATAFormat} == "DICOM" ]]; then
            # ------------------------------ non-XNAT code
            echo ""
            echo " ---> RUNNING run_turnkey step ~~~ import_dicom"
            echo ""
            if [[ -z ${Gzip} ]]; then
                if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
                    Gzip="no"
                else
                    Gzip="folder"
                fi
            fi

            ExecuteCall="${QuNexCommand} import_dicom --sessionsfolder='${SessionsFolder}' --sessions='${CASE}' --masterinbox='none' --archive='delete' --check='any' --unzip='yes' --add_image_type='${AddImageType}' --add_json_info='${AddJsonInfo}' --gzip='${Gzip}' --overwrite='${OVERWRITE_STEP}'"
            echo ""
            echo " -- Executed call:"
            echo "    $ExecuteCall"
            echo ""
            eval ${ExecuteCall}
            cd ${SessionsFolder}/${CASE}/nii; NIILeadZeros=`ls ./0*.nii.gz 2>/dev/null`; for NIIwithZero in ${NIILeadZeros}; do NIIwithoutZero=`echo ${NIIwithZero} | sed 's/0//g'`; mv ${NIIwithZero} ${NIIwithoutZero}; done

            # ------------------------------ XNAT code
            if [ ${TURNKEY_TYPE} == "xnat" ]; then
                echo ""
                echo "---> Cleaning up XNAT run working directory and removing inbox folder"
                echo ""
                rm -rf ${QuNexWorkDir}/inbox &> /dev/null
            fi
            # ------------------------------ END XNAT code
        else
            echo ""
            echo " ---> run_turnkey ~~~ SKIPPING: import_dicom because data is not in DICOM format."
            echo ""
        fi
    }

    # -- Generate session_hcp.txt file
    turnkey_create_session_info() {
        echo ""
        echo " ---> RUNNING run_turnkey step ~~~ create_session_info"
        echo ""

        if [[ "${OVERWRITE_STEP}" == "yes" ]]; then
            rm -rf ${SessionsFolder}/${CASE}/session_hcp.txt &> /dev/null
        fi
        if [ -f ${SessionsFolder}/session_hcp.txt ]; then
            echo ""
            echo " ---> ${SessionsFolder}/session_hcp.txt exists. Set --overwrite='yes' to re-run."
            echo ""
            return 0
        fi
        # ------------------------------
        ExecuteCall="${QuNexCommand} create_session_info --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --mapping="${SpecsMappingFile}""
        echo ""
        echo " -- Executed call:"
        echo "    $ExecuteCall"
        echo ""
        eval ${ExecuteCall}
        # ------------------------------
    }

    # -- Map files to hcp processing folder structure
    turnkey_setup_hcp() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ setup_hcp"; echo ""

        if [[ ${OVERWRITE_STEP} == "yes" ]]; then
           echo "  -- Removing prior hard link mapping."; echo ""
           HLinks=`ls ${SessionsFolder}/${CASE}/hcp/${CASE}/*/*nii* 2>/dev/null`; for HLink in ${HLinks}; do unlink ${HLink}; done
        fi
        ExecuteCall="${QuNexCommand} setup_hcp --sessionsfolder='${SessionsFolder}' --sessions='${CASE}' --existing='clear' --hcp_filename='${HCPFilename}' --hcp_suffix='${HCPSuffix}'"
        echo ""; echo " -- Executed call:"; echo "   $ExecuteCall"; echo ""

        eval ${ExecuteCall}
        # ------------------------------
    }

    # -- Generate batch file for the study
    turnkey_create_batch() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ create_batch"; echo ""

        # is overwrite yes?
        TURNKEY_OVERWRITE="append"
        if [[ ${OVERWRITE_STEP} == "yes" ]]; then
            TURNKEY_OVERWRITE="yes"
        fi

        # ------------------------------
        ExecuteCall="${QuNexCommand} create_batch --sessionsfolder='${SessionsFolder}' --targetfile='${ProcessingBatchFile}' --paramfile='${SpecsBatchFileHeader}' --sessions='${CASE}' --overwrite='${TURNKEY_OVERWRITE}'"
        echo ""
        echo ""; echo " -- Executed call:"; echo "   $ExecuteCall"; echo ""
        eval ${ExecuteCall}
        # ------------------------------
    }

    #
    # ------------------------ run_qc_rawnii -----------------------------------
    # -- run_qc_rawnii (after organizing DICOM files)
    turnkey_run_qc_rawnii() {
        Modality="rawNII"
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ run_qc step for ${Modality} data."; echo ""
        ${QuNexCommand} run_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --modality="${Modality}"
    }

    # --------------- HCP Processing and relevant QC start ---------------------
    #
    # -- PreFreeSurfer
    turnkey_hcp_pre_freesurfer() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ HCP Pipelines - hcp_pre_freesurfer."; echo ""
        ${QuNexCommand} hcp_pre_freesurfer --sessionsfolder="${SessionsFolder}" --sessions="${ProcessingBatchFile}" --overwrite="${OVERWRITE_STEP}" --logfolder="${QuNexMasterLogFolder}" --sessionids="${SESSIONIDS}"
    }
    # -- FreeSurfer
    turnkey_hcp_freesurfer() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ HCP Pipelines step - hcp_freesurfer."; echo ""
        ${QuNexCommand} hcp_freesurfer --sessionsfolder="${SessionsFolder}" --sessions="${ProcessingBatchFile}" --overwrite="${OVERWRITE_STEP}" --logfolder="${QuNexMasterLogFolder}" --sessionids="${SESSIONIDS}"
        CleanupFiles=" talairach_with_skull.log lh.white.deformed.out lh.pial.deformed.out rh.white.deformed.out rh.pial.deformed.out"
        for CleanupFile in ${CleanupFiles}; do
            cp ${QuNexMasterLogFolder}/${CleanupFile} ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/${CASE}/scripts/ 2>/dev/null
            rm -rf ${QuNexMasterLogFolder}/${CleanupFile}
        done
        rm -rf ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/fsaverage 2>/dev/null
        rm -rf ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/rh.EC_average 2>/dev/null
        rm -rf ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/lh.EC_average 2>/dev/null
        cp -r $FREESURFER_HOME/sessions/lh.EC_average ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/ 2>/dev/null
        cp -r $FREESURFER_HOME/sessions/fsaverage ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/ 2>/dev/null
        cp -r $FREESURFER_HOME/sessions/rh.EC_average ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/ 2>/dev/null
    }
    # -- PostFreeSurfer
    turnkey_hcp_post_freesurfer() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ HCP Pipelines step - hcp_post_freesurfer."; echo ""
        ${QuNexCommand} hcp_post_freesurfer --sessionsfolder="${SessionsFolder}" --sessions="${ProcessingBatchFile}" --overwrite="${OVERWRITE_STEP}" --logfolder="${QuNexMasterLogFolder}" --sessionids="${SESSIONIDS}"
    }
    # -- run_qc_t1w (after hcp_post_freesurfer)
    turnkey_run_qc_t1w() {
        Modality="T1w"
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ run_qc step for ${Modality} data."; echo ""
        ${QuNexCommand} run_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --outpath="${SessionsFolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${QuNexMasterLogFolder}" --hcp_suffix="${HCPSuffix}"
    }
    # -- run_qc_t2w (after hcp_post_freesurfer)
    turnkey_run_qc_t2w() {
        Modality="T2w"
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ run_qc step for ${Modality} data."; echo ""
        ${QuNexCommand} run_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --outpath="${SessionsFolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${QuNexMasterLogFolder}" --hcp_suffix="${HCPSuffix}"
    }
    # -- run_qc_myelin (after hcp_post_freesurfer)
    turnkey_run_qc_myelin() {
        Modality="myelin"
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ run_qc step for ${Modality} data."; echo ""
        ${QuNexCommand} run_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --outpath="${SessionsFolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${QuNexMasterLogFolder}" --hcp_suffix="${HCPSuffix}"
    }
    # -- fMRIVolume
    turnkey_hcp_fmri_volume() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ HCP Pipelines - hcp_fmri_volume. ${BOLDS:+BOLDS:} ${BOLDS}"; echo ""
        HCPLogName="hcp_fmri_volume"
        ${QuNexCommand} hcp_fmri_volume --sessionsfolder="${SessionsFolder}" --sessions="${ProcessingBatchFile}" --overwrite="${OVERWRITE_STEP}" --sessionids="${SESSIONIDS}" ${BOLDS:+--bolds=}"$BOLDS"
    }
    # -- fMRISurface
    turnkey_hcp_fmri_surface() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ HCP Pipelines - hcp_fmri_surface. ${BOLDS:+BOLDS:} ${BOLDS}"; echo ""
        HCPLogName="hcp_fmri_surface"
        ${QuNexCommand} hcp_fmri_surface --sessionsfolder="${SessionsFolder}" --sessions="${ProcessingBatchFile}" --overwrite="${OVERWRITE_STEP}" --sessionids="${SESSIONIDS}" ${BOLDS:+--bolds=}"$BOLDS"
    }
    # -- run_qc_bold (after hcp_fmri_surface)
    turnkey_run_qc_bold() {
        Modality="BOLD"
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ run_qc step for ${Modality} data. BOLDS: ${BOLDRUNS} "; echo ""
        if [ -z "${BOLDfc}" ]; then
            # if [ -z "${BOLDPrefix}" ]; then BOLDPrefix="bold"; fi   --- default for bold prefix is now ""
            if [ -z "${BOLDSuffix}" ]; then BOLDSuffix="Atlas"; fi
        fi

        # -- Code for selecting BOLDS via Tags ---> Check if both batch and bolds are specified for QC and if yes read batch explicitly
        getBoldList

        # -- Loop through BOLD runs
        for BOLDRUN in ${LBOLDRUNS}; do
            ${QuNexCommand} run_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --outpath="${SessionsFolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${QuNexMasterLogFolder}" --boldprefix="${BOLDPrefix}" --boldsuffix="${BOLDSuffix}" --bolds="${BOLDRUN}" --hcp_suffix="${HCPSuffix}"
        done
    }
    # -- Diffusion HCP (after hcp_pre_freesurfer)
    turnkey_hcp_diffusion() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ HCP Pipelines step - hcp_diffusion."; echo ""
        ${QuNexCommand} hcp_diffusion --sessionsfolder="${SessionsFolder}" --sessions="${ProcessingBatchFile}" --overwrite="${OVERWRITE_STEP}" --sessionids="${SESSIONIDS}"
    }
    # -- Diffusion Legacy (after hcp_pre_freesurfer)
    turnkey_dwi_legacy_gpu() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ HCP Pipelines: dwi_legacy_gpu"; echo ""
        ${QuNexCommand} dwi_legacy_gpu --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --overwrite="${OVERWRITE_STEP}" --scanner="${Scanner}" --usefieldmap="${UseFieldmap}" --echospacing="${EchoSpacing}" --pedir="${pedir}" --unwarpdir="${UnwarpDir}" --diffdatasuffix="${DiffDataSuffix}" --TE="${TE}"
    }
    # -- run_qc_dwi
    turnkey_run_qc_dwi() {
        Modality="DWI"
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ run_qc steps for ${Modality} HCP processing."; echo ""
        ${QuNexCommand} run_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --outpath="${SessionsFolder}/QC/DWI" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --dwidata="data" --dwipath="Diffusion" --logfolder="${QuNexMasterLogFolder}" --hcp_suffix="${HCPSuffix}"
    }
    # -- dwi_eddy_qc processing steps
    turnkey_dwi_eddy_qc() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ dwi_eddy_qc for DWI data."; echo ""
        # -- Defaults if values not set:
        if [ -z "$EddyBase" ]; then EddyBase="eddy_unwarped_images"; fi
        if [ -z "$Report" ]; then Report="individual"; fi
        if [ -z "$BvalsFile" ]; then BvalsFile="Pos_Neg.bvals"; fi
        if [ -z "$Mask" ]; then Mask="nodif_brain_mask.nii.gz"; fi
        if [ -z "$EddyIdx" ]; then EddyIdx="index.txt"; fi
        if [ -z "$EddyParams" ]; then EddyParams="acqparams.txt"; fi
        if [ -z "$BvecsFile" ]; then BvecsFile="Pos_Neg.bvecs"; fi
        #
        # ---> Example for 'Legacy' data:
        # --eddypath='Diffusion/DWI_dir74_AP_b1000b2500/eddy/eddylinked'
        # --eddybase='DWI_dir74_AP_b1000b2500_eddy_corrected'
        # --bvalsfile='DWI_dir74_AP_b1000b2500.bval'
        # --bvecsfile='DWI_dir74_AP_b1000b2500.bvec'
        # --mask='DWI_dir74_AP_b1000b2500_nodif_brain_mask.nii.gz'
        #
        ${QuNexCommand} dwi_eddy_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --eddybase="${EddyBase}" --eddypath="${EddyPath}" --report="${Report}" --bvalsfile="${BvalsFile}" --mask="${Mask}" --eddyidx="${EddyIdx}" --eddyparams="${EddyParams}" --bvecsfile="${BvecsFile}" --overwrite="${OVERWRITE_STEP}"
    }
    # -- run_qc_dwi_eddy (after dwi_eddy_qc)
    turnkey_run_qc_dwi_eddy() {
        Modality="DWI"
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ run_qc steps for ${Modality} dwi_eddy_qc."; echo ""
        ${QuNexCommand} run_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --overwrite="${OVERWRITE_STEP}" --outpath="${SessionsFolder}/QC/DWI" --modality="${Modality}" --dwidata="data" --dwipath="Diffusion" --eddyqcstats="yes" --hcp_suffix="${HCPSuffix}"
    }
    #
    # --------------- HCP Processing and relevant QC end -----------------------

    # --------------- DWI additional analyses start ------------------------
    #
    # -- dwi_dtifit (after hcpd or dwi_legacy_gpu)
    turnkey_dwi_dtifit() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ : dwi_dtifit for DWI data."; echo ""
        ${QuNexCommand} dwi_dtifit --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --overwrite="${OVERWRITE_STEP}"
    }
    # -- dwi_bedpostx_gpu (after dwi_dtifit)
    turnkey_dwi_bedpostx_gpu() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ dwi_bedpostx_gpu for DWI data."
        if [ -z "$Fibers" ]; then Fibers="3"; fi
        if [ -z "$Model" ]; then Model="3"; fi
        if [ -z "$Burnin" ]; then Burnin="3000"; fi
        if [ -z "$Rician" ]; then Rician="yes"; fi
        # if [ -z "$Gradnonlin" ]; then Gradnonlin="yes"; fi
        ${QuNexCommand} dwi_bedpostx_gpu --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --overwrite="${OVERWRITE_STEP}" --fibers="${Fibers}" --burnin="${Burnin}" --model="${Model}" --rician="${Rician}" --gradnonlin="${Gradnonlin}"
    }
    # -- run_qc_dwi_dtifit (after dwi_dtifit)
    turnkey_run_qc_dwi_dtifit() {
        Modality="DWI"
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ run_qc steps for ${Modality} FSL's dtifit analyses."; echo ""
        ${QuNexCommand} run_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --overwrite="${OVERWRITE_STEP}" --outpath="${SessionsFolder}/QC/DWI" --modality="${Modality}" --dwidata="data" --dwipath="Diffusion" --dtifitqc="yes" --hcp_suffix="${HCPSuffix}"
    }
    # -- run_qc_dwi_bedpostx (after dwi_bedpostx_gpu)
    turnkey_run_qc_dwi_bedpostx() {
        Modality="DWI"
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ run_qc steps for ${Modality} FSL's BedpostX analyses."; echo ""
        ${QuNexCommand} run_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --overwrite="${OVERWRITE_STEP}" --outpath="${SessionsFolder}/QC/DWI" --modality="${Modality}" --dwidata="data" --dwipath="Diffusion" --bedpostxqc="yes" --hcp_suffix="${HCPSuffix}"
    }
    # -- dwi_probtrackx_dense_gpu for DWI data (after dwi_bedpostx_gpu)
    turnkey_dwi_probtrackx_dense_gpu() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ dwi_probtrackx_dense_gpu"; echo ""
        ${QuNexCommand} dwi_probtrackx_dense_gpu --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --overwrite="${OVERWRITE_STEP}" --omatrix1="yes" --omatrix3="yes"
    }
    # -- dwi_pre_tractography for DWI data (after dwi_bedpostx_gpu)
    turnkey_dwi_pre_tractography() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ dwi_pre_tractography"; echo ""
        ${QuNexCommand} dwi_pre_tractography --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --overwrite="${OVERWRITE_STEP}" --omatrix1="yes" --omatrix3="yes"
    }
    # -- dwi_parcellate for DWI data (after dwi_pre_tractography)
    turnkey_dwi_parcellate() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ dwi_parcellate"; echo ""
        # Defaults if not specified:
        if [ -z "$WayTotal" ]; then WayTotal="standard"; fi
        if [ -z "$MatrixVersion" ]; then MatrixVersions="1"; fi
        # Cole-Anticevic Brain-wide Network Partition version 1.0 (CAB-NP v1.0)
        if [ -z "$ParcellationFile" ]; then ParcellationFile="${TOOLS}/${QUNEXREPO}/qx_library/data/parcellations/cole_anticevic_net_partition/CortexSubcortex_ColeAnticevic_NetPartition_wSubcorGSR_parcels_LR_ReorderedByNetworks.dlabel.nii"; fi
        if [ -z "$DWIOutName" ]; then DWIOutName="DWI-CAB-NP-v1.0"; fi
        for MatrixVersion in $MatrixVersions; do
            ${QuNexCommand} dwi_parcellate --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --overwrite="${OVERWRITE_STEP}" --waytotal="${WayTotal}" --matrixversion="${MatrixVersion}" --parcellationfile="${ParcellationFile}" --outname="${DWIOutName}"
        done
    }
    # -- dwi_seed_tractography_dense for DWI data (after dwi_pre_tractography)
    turnkey_dwi_seed_tractography_dense() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ dwi_seed_tractography_dense"; echo ""
        if [ -z "$MatrixVersion" ]; then MatrixVersions="1"; fi
        if [ -z "$WayTotal" ]; then WayTotal="standard"; fi
        if [ -z "$SeedFile" ]; then
            # Thalamus SomatomotorSensory
            SeedFile="${TOOLS}/${QUNEXREPO}/qx_library/data/atlases/thalamus_atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-SomatomotorSensory.symmetrical.intersectionLR.nii"
            OutName="DWI_THALAMUS_FSL_LR_SomatomotorSensory_Symmetrical_intersectionLR"
            ${QuNexCommand} dwi_seed_tractography_dense --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --overwrite="${OVERWRITE_STEP}" --matrixversion="${MatrixVersion}" --waytotal="${WayTotal}" --outname="${OutName}" --seedfile="${SeedFile}"
            # Thalamus Prefrontal
            SeedFile="${TOOLS}/${QUNEXREPO}/qx_library/data/atlases/thalamus_atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Prefrontal.symmetrical.intersectionLR.nii"
            OutName="DWI_THALAMUS_FSL_LR_Prefrontal"
            ${QuNexCommand} dwi_seed_tractography_dense --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --overwrite="${OVERWRITE_STEP}" --matrixversion="${MatrixVersion}" --waytotal="${WayTotal}" --outname="${OutName}" --seedfile="${SeedFile}"
        fi
        OutNameGBC="DWI_GBC"
        ${QuNexCommand} dwi_seed_tractography_dense --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --overwrite="${OVERWRITE_STEP}" --matrixversion="${MatrixVersion}" --waytotal="${WayTotal}" --outname="${OutNameGBC}" --seedfile="gbc"
    }
    #
    # --------------- DWI Processing and analyses end --------------------------


    # --------------- Custom QC start ------------------------------------------
    #
    # -- Check if Custom QC was requested
    turnkey_run_qc_custom() {
        unset RunCommand
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ run_qc_custom"; echo ""

        if [ -z "${Modality}" ]; then
            Modalities="T1w T2w myelin BOLD DWI"
            echo " ---> Note: No modality specified. Trying all modalities: ${Modalities} "
        else
            Modalities="${Modality}"
            echo " ---> User requested modalities: ${Modalities} "
        fi
        for Modality in ${Modalities}; do
            echo " ---> Running modality: ${Modality} "; echo ""
            if [[ ${Modality} == "BOLD" ]]; then
                # if [ -z "${BOLDPrefix}" ]; then BOLDPrefix="bold"; fi    --- default for bold prefix is now ""
                if [ -z "${BOLDSuffix}" ]; then BOLDSuffix="Atlas"; fi

                getBoldList

                echo "---> Looping through these BOLDRUNS: ${LBOLDRUNS}"
                for BOLDRUN in ${LBOLDRUNS}; do
                    echo "---> Now working on BOLDRUN: ${BOLDRUN}"
                    ${QuNexCommand} run_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --outpath="${SessionsFolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${QuNexMasterLogFolder}" --boldprefix="${BOLDPrefix}" --boldsuffix="${BOLDSuffix}" --bolddata="${BOLDRUN}" --customqc='yes' --omitdefaults='yes' --hcp_suffix="${HCPSuffix}"
                done
            elif [[ ${Modality} == "DWI" ]]; then
                ${QuNexCommand} run_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --outpath="${SessionsFolder}/QC/${Modality}" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --dwidata="data" --dwipath="Diffusion" --customqc="yes" --omitdefaults="yes" --hcp_suffix="${HCPSuffix}"
            else
                ${QuNexCommand} run_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --outpath="${SessionsFolder}/QC/${Modality}" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --customqc="yes" --omitdefaults="yes" --hcp_suffix="${HCPSuffix}"
            fi
        done
    }
    #
    # --------------- Custom QC end --------------------------------------------


    # --------------- BOLD FC Processing and analyses start --------------------
    #
    # -- Specific checks for BOLD Fc functions
    BOLDfcLogCheck() {
        cd ${QuNexMasterLogFolder}/comlogs/

        ComLogName=`ls -t1 ./*${FunctionName}*${CASE}*log | head -1 | xargs -n 1 basename 2> /dev/null`
        if [ ! -z ${ComLogName} ]; then echo " ---> Comlog: $ComLogName"; echo ""; fi
        rename ${FunctionName} ${TURNKEY_STEP} ${QuNexMasterLogFolder}/comlogs/${ComLogName} 2> /dev/null

        echo " ---> run_turnkey acceptance testing ${TURNKEY_STEP} logs for completion."; echo ""

        CheckComLog=`ls -t1 ${QuNexMasterLogFolder}/comlogs/*${FunctionName}_${CASE}*log 2> /dev/null | head -n 1`

        if [ -z "${CheckComLog}" ]; then
           TURNKEY_STEP_ERRORS="yes"
           echo " ---> ERROR: comlog file for ${TURNKEY_STEP} step not found during run_turnkey acceptance test!"
        fi
        if [ ! -z "${CheckComLog}" ]; then
           echo " ---> run_turnkey acceptance testing found comlog file for ${TURNKEY_STEP} step:"
           echo "      ${CheckComLog}"
           chmod 777 ${CheckComLog} 2>/dev/null
        fi
        if [ -z `echo "${CheckComLog}" | grep 'done'` ]; then
            echo ""; echo " ---> ERROR: run_turnkey acceptance test for ${TURNKEY_STEP} step failed."
            TURNKEY_STEP_ERRORS="yes"
        else
            echo ""; echo " ---> SUCCESSFUL run_turnkey acceptance test for ${TURNKEY_STEP}"; echo ""
            TURNKEY_STEP_ERRORS="no"
        fi
    }

    # -- Map HCP processed outputs for further FC BOLD analyses
    turnkey_map_hcp_data() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ map_hcp_data"; echo ""
        # ------------------------------
        ExecuteCall="${QuNexCommand} map_hcp_data --sessions='${ProcessingBatchFile}' --sessionsfolder='${SessionsFolder}' --overwrite='${OVERWRITE_STEP}' --logfolder='${QuNexMasterLogFolder}' --sessionids='${SESSIONIDS}' ${BOLDS:+--bolds=\"${BOLDS}\"}"
        echo ""; echo " -- Executed call:"; echo "   $ExecuteCall"; echo ""
        eval ${ExecuteCall}
    }
    # -- Generate brain masks for de-noising
    turnkey_create_bold_brain_masks() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ create_bold_brain_masks"; echo ""
        ExecuteCall="${QuNexCommand} create_bold_brain_masks --sessions='${ProcessingBatchFile}' --sessionsfolder='${SessionsFolder}' --overwrite='${OVERWRITE_STEP}' --logfolder='${QuNexMasterLogFolder}' --sessionids='${SESSIONIDS}' ${BOLDS:+--bolds=\"${BOLDS}\"}"
        echo ""; echo " -- Executed call:"; echo "   $ExecuteCall"; echo ""
        eval ${ExecuteCall}
    }
    # -- Compute BOLD statistics
    turnkey_compute_bold_stats() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ compute_bold_stats"; echo ""
        ${QuNexCommand} compute_bold_stats \
        --sessions="${ProcessingBatchFile}" \
        --sessionsfolder="${SessionsFolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${QuNexMasterLogFolder}" \
        --sessionids="${SESSIONIDS}" \
        ${BOLDS:+--bolds="${BOLDS}"}
    }
    # -- Create final BOLD statistics report
    turnkey_create_stats_report() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ create_stats_report"; echo ""
        ${QuNexCommand} create_stats_report \
        --sessions="${ProcessingBatchFile}" \
        --sessionsfolder="${SessionsFolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${QuNexMasterLogFolder}" \
        --sessionids="${SESSIONIDS}" \
        ${BOLDS:+--bolds="${BOLDS}"}
    }
    # -- Extract nuisance signal for further de-noising
    turnkey_extract_nuisance_signal() {
        echo " ---> RUNNING run_turnkey step ~~~ extract_nuisance_signal"; echo ""
        echo ""
        ExecuteCall="${QuNexCommand} extract_nuisance_signal --sessions='${ProcessingBatchFile}' --sessionsfolder='${SessionsFolder}' --overwrite='${OVERWRITE_STEP}' --logfolder='${QuNexMasterLogFolder}' --sessionids='${SESSIONIDS}' ${BOLDS:+--bolds=\"${BOLDS}\"}"
        echo ""; echo " -- Executed call:"; echo "   $ExecuteCall"; echo ""
        echo ""
        eval ${ExecuteCall}
    }
    # -- Process BOLDs
    turnkey_preprocess_bold() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ preprocess_bold"; echo ""
        ${QuNexCommand} preprocess_bold \
        --sessions="${ProcessingBatchFile}" \
        --sessionsfolder="${SessionsFolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${QuNexMasterLogFolder}" \
        --sessionids="${SESSIONIDS}" \
        ${BOLDS:+--bolds="${BOLDS}"}
    }
    # -- Process via CONC file
    turnkey_preprocess_conc() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ preprocess_conc"; echo ""
        ${QuNexCommand} preprocess_conc \
        --sessions="${ProcessingBatchFile}" \
        --sessionsfolder="${SessionsFolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${QuNexMasterLogFolder}" \
        --sessionids="${SESSIONIDS}" \
        ${BOLDS:+--bolds="${BOLDS}"}
    }
    # -- Compute general_plot_bold_timeseries ---> (08/14/17 - 6:50PM): Coded but not final yet due to Octave/Matlab problems
    turnkey_general_plot_bold_timeseries() {
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ general_plot_bold_timeseries QC plotting"; echo ""
        TimeStamp=`date +%Y-%m-%d_%H.%M.%S.%6N`
        general_plot_bold_timeseries_Runlog="${QuNexMasterLogFolder}/runlogs/Log-general_plot_bold_timeseries_${TimeStamp}.log"
        general_plot_bold_timeseries_ComlogTmp="${QuNexMasterLogFolder}/comlogs/tmp_general_plot_bold_timeseries_${CASE}_${TimeStamp}.log"; touch ${general_plot_bold_timeseries_ComlogTmp}; chmod 777 ${general_plot_bold_timeseries_ComlogTmp}
        general_plot_bold_timeseries_ComlogError="${QuNexMasterLogFolder}/comlogs/error_general_plot_bold_timeseries_${CASE}_${TimeStamp}.log"
        general_plot_bold_timeseries_ComlogDone="${QuNexMasterLogFolder}/comlogs/done_general_plot_bold_timeseries_${CASE}_${TimeStamp}.log"

        # -- Add header to log
        echo "# Generated by QuNex ${QuNexVer} on ${TimeStamp}" >> ${general_plot_bold_timeseries_ComlogTmp}
        echo "#" >> ${general_plot_bold_timeseries_ComlogTmp}

        if [ -z ${QCPlotElements} ]; then
              QCPlotElements="type=stats|stats>plotdata=fd,imageindex=1>plotdata=dvarsme,imageindex=1;type=signal|name=V|imageindex=1|maskindex=1|colormap=hsv;type=signal|name=WM|imageindex=1|maskindex=1|colormap=jet;type=signal|name=GM|imageindex=1|maskindex=1;type=signal|name=GM|imageindex=2|use=1|scale=3"
        fi
        if [ -z ${QCPlotMasks} ]; then
              QCPlotMasks="${SessionsFolder}/${CASE}/images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz"
        fi
        if [ -z ${images_folder} ]; then
            images_folder="${SessionsFolder}/$CASE/images/functional"
        fi
        if [ -z ${output_folder} ]; then
            output_folder="${SessionsFolder}/$CASE/images/functional/movement"
        fi
        if [ -z ${output_name} ]; then
            output_name="${CASE}_BOLD_GreyPlot_CIFTI.pdf"
        fi

        getBoldList

        echo " -- Log folder: ${QuNexMasterLogFolder}/comlogs/" 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
        echo "   " 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
        echo " -- Parameters for general_plot_bold_timeseries: " 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
        echo "   " 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
        echo "   QC Plot Masks: ${QCPlotMasks}" 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
        echo "   QC Plot Elements: ${QCPlotElements}" 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
        echo "   QC Plot image folder: ${images_folder}" 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
        echo "   QC Plot output folder: ${output_folder}" 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
        echo "   QC Plot output name: ${output_name}" 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
        echo "   QC Plot BOLDS runs: ${BOLDRUNS}" 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}

        unset BOLDRUN
        for BOLDRUN in ${LBOLDRUNS}; do
           cd ${images_folder}
           if [ -z ${QCPlotImages} ]; then
               QCPlotImages="bold${BOLDRUN}.nii.gz;bold${BOLDRUN}_Atlas_s_hpss_res-mVWMWB_lpss.dtseries.nii"
           fi
           echo "   QC Plot images: ${QCPlotImages}" 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
           echo "   " 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
           echo "   " 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
           echo " -- Command: " 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
           echo "   " 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
           echo "${QuNexCommand} general_plot_bold_timeseries --images="${QCPlotImages}" --elements="${QCPlotElements}" --masks="${QCPlotMasks}" --filename="${output_folder}/${output_name}" --skip="0" --sessionids="${CASE}" --verbose="true"" 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
           echo "   " 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}

           ${QuNexCommand} general_plot_bold_timeseries --images="${QCPlotImages}" --elements="${QCPlotElements}" --masks="${QCPlotMasks}" --filename="${output_folder}/${output_name}" --skip="0" --sessionids="${CASE}" --verbose="true"
           echo " -- Copying ${output_folder}/${output_name} to ${SessionsFolder}/QC/BOLD/" 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
           echo "   " 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
           cp ${output_folder}/${output_name} ${SessionsFolder}/QC/BOLD/
           if [[ -f ${SessionsFolder}/QC/BOLD/${output_name} ]]; then
               echo " -- Found ${SessionsFolder}/QC/BOLD/${output_name}" 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
               echo "   " 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
               general_plot_bold_timeseries_Check="pass"
           else
               echo " -- Result ${SessionsFolder}/QC/BOLD/${output_name} missing!" 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
               echo "   " 2>&1 | tee -a ${general_plot_bold_timeseries_ComlogTmp}
               general_plot_bold_timeseries_Check="fail"
           fi
        done

        if [[ ${general_plot_bold_timeseries_Check} == "pass" ]]; then
            echo "" >> ${general_plot_bold_timeseries_ComlogTmp}
            echo "------------------------- Successful completion of work --------------------------------" >> ${general_plot_bold_timeseries_ComlogTmp}
            echo "" >> ${general_plot_bold_timeseries_ComlogTmp}
            cp ${general_plot_bold_timeseries_ComlogTmp} ${general_plot_bold_timeseries_ComlogDone}
            general_plot_bold_timeseries_Comlog=${general_plot_bold_timeseries_ComlogDone}
        else
           echo "" >> ${general_plot_bold_timeseries_ComlogTmp}
           echo "Error. Something went wrong." >> ${general_plot_bold_timeseries_ComlogTmp}
           echo "" >> ${general_plot_bold_timeseries_ComlogTmp}
           cp ${general_plot_bold_timeseries_ComlogTmp} ${general_plot_bold_timeseries_ComlogError}
           general_plot_bold_timeseries_Comlog=${general_plot_bold_timeseries_ComlogError}
        fi
        rm ${general_plot_bold_timeseries_ComlogTmp}
    }
    # -- BOLD Parcellation
    turnkey_parcellate_bold() {
        FunctionName="parcellate_bold"

        getBoldNumberList
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ parcellate_bold on BOLDS: ${LBOLDRUNS}"; echo ""

        if [ -z ${RunParcellations} ]; then

            for BOLDRUN in ${LBOLDRUNS}; do
               if [ -z "$InputFile" ]; then InputFileParcellation="bold${BOLDRUN}_Atlas_s_hpss_res-mVWMWB_lpss.dtseries.nii "; else InputFileParcellation="${InputFile}"; fi
               if [ -z "$UseWeights" ]; then UseWeights="yes"; fi
               if [ -z "$WeightsFile" ]; then UseWeights="images/functional/movement/bold${BOLDRUN}.use"; fi
               # -- Cole-Anticevic Brain-wide Network Partition version 1.0 (CAB-NP v1.0)
               if [ -z "$ParcellationFile" ]; then ParcellationFile="${TOOLS}/${QUNEXREPO}/qx_library/data/parcellations/cole_anticevic_net_partition/CortexSubcortex_ColeAnticevic_NetPartition_wSubcorGSR_parcels_LR_ReorderedByNetworks.dlabel.nii"; fi
               if [ -z "$OutName" ]; then OutNameParcelation="BOLD-CAB-NP-v1.0"; else OutNameParcelation="${OutName}"; fi
               if [ -z "$InputDataType" ]; then InputDataType="dtseries"; fi
               if [ -z "$InputPath" ]; then InputPath="/images/functional/"; fi
               if [ -z "$OutPath" ]; then OutPath="/images/functional/"; fi
               if [ -z "$ComputePConn" ]; then ComputePConn="yes"; fi
               if [ -z "$ExtractData" ]; then ExtractData="yes"; fi
               # -- Command
               RunCommand="${QuNexCommand} parcellate_bold --sessions='${CASE}' \
               --sessionsfolder='${SessionsFolder}' \
               --inputfile='${InputFileParcellation}' \
               --singleinputfile='${SingleInputFile}' \
               --inputpath='${InputPath}' \
               --inputdatatype='${InputDataType}' \
               --parcellationfile='${ParcellationFile}' \
               --overwrite='${Overwrite}' \
               --outname='${OutNameParcelation}' \
               --outpath='${OutPath}' \
               --computepconn='${ComputePConn}' \
               --extractdata='${ExtractData}' \
               --useweights='${UseWeights}' \
               --weightsfile='${WeightsFile}'"
               echo " -- Command: ${RunCommand}"
               eval ${RunCommand}
               BOLDfcLogCheck
            done

        else

            if [[ ${RunParcellations} == "all" ]] || [[ ${RunParcellations} == "ALL" ]]; then
                RunParcellations="CANP HCP YEO7 YEO17"
            fi
            RunParcellations=`echo ${RunParcellations} | sed 's/,/ /g;s/|/ /g'`

            echo ""; echo " ---> The following parcellations will be run: ${RunParcellations}"; echo ""

            for Parcellation in ${RunParcellations}; do
                if [ ${Parcellation} == "CANP" ]; then
                    ParcellationFile="${TOOLS}/${QUNEXREPO}/qx_library/data/parcellations/cole_anticevic_net_partition/CortexSubcortex_ColeAnticevic_NetPartition_wSubcorGSR_parcels_LR_ReorderedByNetworks.dlabel.nii"
                    OutNameParcelation="BOLD-CAB-NP-v1.0"
                elif [ ${Parcellation} == "HCP" ]; then
                    ParcellationFile="${TOOLS}/${QUNEXREPO}/qx_library/data/parcellations/glasser_parcellation/Q1-Q6_RelatedParcellation210.LR.CorticalAreas_dil_Colors.32k_fs_LR.dlabel.nii"
                    OutNameParcelation="HCP-210"
                elif [ ${Parcellation} == "YEO17" ]; then
                    ParcellationFile="${TOOLS}/${QUNEXREPO}/qx_library/data/parcellations/rsn_yeo_buckner_choi_cortex_cerebellum_striatum/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_17networks_networks_MWfix.dlabel.nii"
                    OutNameParcelation="YEO17"
                elif [ ${Parcellation} == "YEO7" ]; then
                    ParcellationFile="${TOOLS}/${QUNEXREPO}/qx_library/data/parcellations/rsn_yeo_buckner_choi_cortex_cerebellum_striatum/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_thalamus_7networks_networks_MWfix.dlabel.nii"
                    OutNameParcelation="YEO7"
                else
                    echo " ---> ERROR: ${Parcellation} not recognized as a valid parcellation name! Skipping";
                    continue
                fi

                echo ""; echo " ---> Now running parcellation ${Parcellation}"; echo ""

                for BOLDRUN in ${LBOLDRUNS}; do
                   if [ -z "$InputFile" ]; then InputFileParcellation="bold${BOLDRUN}_Atlas_s_hpss_res-mVWMWB_lpss.dtseries.nii "; else InputFileParcellation="${InputFile}"; fi
                   if [ -z "$UseWeights" ]; then UseWeights="yes"; fi
                   if [ -z "$WeightsFile" ]; then UseWeights="images/functional/movement/bold${BOLDRUN}.use"; fi
                   if [ -z "$InputDataType" ]; then InputDataType="dtseries"; fi
                   if [ -z "$InputPath" ]; then InputPath="/images/functional/"; fi
                   if [ -z "$OutPath" ]; then OutPath="/images/functional/"; fi
                   if [ -z "$ComputePConn" ]; then ComputePConn="yes"; fi
                   if [ -z "$ExtractData" ]; then ExtractData="yes"; fi
                   # -- Command
                   RunCommand="${QuNexCommand} parcellate_bold --sessions='${CASE}' \
                   --sessionsfolder='${SessionsFolder}' \
                   --inputfile='${InputFileParcellation}' \
                   --singleinputfile='${SingleInputFile}' \
                   --inputpath='${InputPath}' \
                   --inputdatatype='${InputDataType}' \
                   --parcellationfile='${ParcellationFile}' \
                   --overwrite='${Overwrite}' \
                   --outname='${OutNameParcelation}' \
                   --outpath='${OutPath}' \
                   --computepconn='${ComputePConn}' \
                   --extractdata='${ExtractData}' \
                   --useweights='${UseWeights}' \
                   --weightsfile='${WeightsFile}'"
                   echo " -- Command: ${RunCommand}"
                   eval ${RunCommand}
                   BOLDfcLogCheck
                done
            done
        fi
    }
    # -- Compute Seed FC for relevant ROIs
    turnkey_compute_bold_fc_seed() {
        FunctionName="compute_bold_fc"
        echo ""; echo " ---> RUNNING run_turnkey step ~~~ compute_bold_fc processing steps for Seed FC."; echo ""
        if [ -z ${ROIInfo} ]; then
           ROINames="${TOOLS}/${QUNEXREPO}/qx_library/data/roi/seeds_cifti.names ${TOOLS}/${QUNEXREPO}/qx_library/data/atlases/thalamus_atlas/Thal.FSL.MNI152.CIFTI.Atlas.AllSurfaceZero.names"
        else
           ROINames=${ROIInfo}
        fi

        getBoldNumberList

        for ROIInfo in ${ROINames}; do
            for BOLDRUN in ${LBOLDRUNS}; do
                if [ -z "$InputFile" ]; then InputFileSeed="bold${BOLDRUN}_Atlas_s_hpss_res-mVWMWB_lpss.dtseries.nii"; else InputFileSeed="${InputFile}"; fi
                if [ -z "$InputPath" ]; then InputPath="/images/functional"; fi
                if [ -z "$ExtractData" ]; then ExtractData="no"; fi
                if [ -z "$OutName" ]; then OutNameSeed="seed_bold${BOLDRUN}_Atlas_s_hpss_res-VWMWB_lpss"; else OutNameSeed="${OutName}"; fi
                if [ -z "$FileList" ]; then FileList=""; fi
                if [ -z "$OVERWRITE_STEP" ]; then OVERWRITE_STEP="yes"; fi
                if [ -z "$IgnoreFrames" ]; then IgnoreFrames="udvarsme"; fi
                if [ -z "$Method" ]; then Method="mean"; fi
                if [ -z "$FCCommand" ]; then FCCommand="all"; fi
                if [ -z "$OutPath" ]; then OutPath="/images/functional"; fi
                if [ -z "$MaskFrames" ]; then MaskFrames="0"; fi
                if [ -z "$Verbose" ]; then Verbose="true"; fi
                if [ -z "$Covariance" ]; then Covariance="true"; fi
                RunCommand="${QuNexCommand} compute_bold_fc \
                --sessionsfolder='${SessionsFolder}' \
                --calculation='seed' \
                --runtype='individual' \
                --sessions='${CASE}' \
                --inputfiles='${InputFileSeed}' \
                --inputpath='${InputPath}' \
                --extractdata='${ExtractData}' \
                --outname='${OutNameSeed}' \
                --overwrite='${OVERWRITE_STEP}' \
                --ignore='${IgnoreFrames}' \
                --roinfo='${ROIInfo}' \
                --options='${FCCommand}' \
                --method='${Method}' \
                --targetf='${OutPath}' \
                --mask='${MaskFrames}' \
                --covariance='${Covariance}'"
                echo " -- Command: ${RunCommand}"
                eval ${RunCommand}
                BOLDfcLogCheck
            done
        done
    }
   # -- Compute GBC
   turnkey_compute_bold_fc_gbc() {
   FunctionName="compute_bold_fc"
       echo ""; echo " ---> RUNNING run_turnkey step ~~~ compute_bold_fc processing steps for GBC."; echo ""

       getBoldNumberList

       for BOLDRUN in ${LBOLDRUNS}; do
            if [ -z "$InputFile" ]; then InputFileGBC="bold${BOLDRUN}_Atlas_s_hpss_res-mVWMWB_lpss.dtseries.nii"; else InputFileGBC="${InputFile}"; fi
            if [ -z "$InputPath" ]; then InputPath="/images/functional"; fi
            if [ -z "$ExtractData" ]; then ExtractData="no"; fi
            if [ -z "$OutName" ]; then OutNameGBC="GBC_bold${BOLDRUN}_Atlas_s_hpss_res-VWMWB_lpss"; else OutNameGBC="${OutName}"; fi
            if [ -z "$FileList" ]; then FileList=""; fi
            if [ -z "$OVERWRITE_STEP" ]; then OVERWRITE_STEP="yes"; fi
            if [ -z "$IgnoreFrames" ]; then IgnoreFrames="udvarsme"; fi
            if [ -z "$TargetROI" ]; then TargetROI=""; fi
            if [ -z "$GBCCommand" ]; then GBCCommand="mFz:"; fi
            if [ -z "$OutPath" ]; then OutPath="/images/functional"; fi
            if [ -z "$MaskFrames" ]; then MaskFrames="0"; fi
            if [ -z "$RadiusSmooth" ]; then RadiusSmooth="0"; fi
            if [ -z "$RadiusDilate" ]; then RadiusDilate="0"; fi
            if [ -z "$Verbose" ]; then Verbose="true"; fi
            if [ -z "$ComputeTime" ]; then ComputeTime="true"; fi
            if [ -z "$VoxelStep" ]; then VoxelStep="1000"; fi
            if [ -z "$Covariance" ]; then Covariance="true"; fi
            RunCommand="${QuNexCommand} compute_bold_fc \
            --sessionsfolder='${SessionsFolder}' \
            --calculation='gbc' \
            --runtype='individual' \
            --sessions='${CASE}' \
            --inputfiles='${InputFileGBC}' \
            --inputpath='${InputPath}' \
            --extractdata='${ExtractData}' \
            --outname='${OutNameGBC}' \
            --flist='${FileList}' \
            --overwrite='${OVERWRITE_STEP}' \
            --ignore='${IgnoreFrames}' \
            --target='${TargetROI}' \
            --gbc-command='${GBCCommand}' \
            --targetf='${OutPath}' \
            --mask='${MaskFrames}' \
            --rsmooth='${RadiusSmooth}' \
            --rdilate='${RadiusDilate}' \
            --verbose='${Verbose}' \
            --time='${ComputeTime}' \
            --vstep='${VoxelStep}' \
            --covariance='${Covariance}'"
            echo " -- Command: ${RunCommand}"
            eval ${RunCommand}
            BOLDfcLogCheck
        done
   }
   # -- run_qc_bold FC (after GBC/FC/PCONN)
   #turnkey_QCrun_BOLDfc
   turnkey_run_qc_bold_fc() {
        Modality="BOLD"

        getBoldList

        for BOLDRUN in ${LBOLDRUNS}; do
            ${QuNexCommand} run_qc --sessionsfolder="${SessionsFolder}" --sessions="${CASE}" --outpath="${SessionsFolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${QuNexMasterLogFolder}" --boldprefix="${BOLDPrefix}" --boldsuffix="${BOLDSuffix}" --bolds="${BOLDRUN}" --boldfc="${BOLDfc}" --boldfcinput="${BOLDfcInput}" --boldfcpath="${BOLDfcPath}" --hcp_suffix="${HCPSuffix}"
        done
    }

    #
    # --------------- BOLD FC Processing and analyses end ----------------------


    # --------------- RunAcceptanceTest start ---------------------------
    #
    # -- RunAcceptanceTest for a given step in XNAT
    #
    RunAcceptanceTestFunction() {

        echo ""; echo " ---> RUNNING run_turnkey step ~~~ Acceptance Test Function."; echo ""

        if [[ -z "$TURNKEY_STEPS" ]] && [[ ! -z "$AcceptanceTest" ]] && [[ "$AcceptanceTest" != "yes" ]] && [[ ${TURNKEY_TYPE} == "xnat" ]]; then
            for UnitTest in ${AcceptanceTest}; do
                RunCommand="qunex_acceptance_test.sh \
                --studyfolder='${StudyFolder}' \
                --sessionsfolder='${SessionsFolder}' \
                --sessions='${CASE}' \
                --runtype='local' \
                --acceptancetest='${UnitTest}'"
                echo " -- Command: ${RunCommand}"
                eval ${RunCommand}
            done
        else
            RunCommand="qunex_acceptance_test.sh \
            --studyfolder='${StudyFolder}' \
            --sessionsfolder='${SessionsFolder}' \
            --sessions='${CASE}' \
            --runtype='local' \
            --acceptancetest='${UnitTest}'"
           echo " -- Command: ${RunCommand}"
           eval ${RunCommand}
        fi

       # -- XNAT Call -- not supported currently --->
       #
       #    RunCommand="qunex_acceptance_test.sh \
       #    --xnatuser='${XNAT_USER_NAME}' \
       #    --xnatpass='${XNAT_PASSWORD}' \
       #    --xnatprojectid='${XNAT_PROJECT_ID}' \
       #    --xnathost='${XNAT_HOST_NAME} \
       #    --subjects='${XNAT_SUBJECT_LABEL}' \
       #    --xnataccsessionid='${XNAT_ACCSESSION_ID}'
       #    --runtype='xnat' \
       #    --acceptancetest='${UnitTest}' \
       #    --bidsformat='${BIDSFormat}' \
       #    --xnatarchivecommit='session' "
    }
    #
    # --------------- RunAcceptanceTest end ----------------------

    # --------------- QuNexTurnkeyCleanFunction start -------------
    #
    QuNexTurnkeyCleanFunction() {
        # -- Currently supporting hcp_fmri_volume but this can be exanded
        if [[ "$TURNKEY_STEP" == "hcp_fmri_volume" ]]; then
            echo ""; echo " ---> RUNNING run_turnkey step ~~~ qunex_clean Function for $TURNKEY_STEP"; echo ""
            rm -rf ${SessionsFolder}/${CASE}/hcp/${CASE}/[0-9]* &> /dev/null
        fi
    }
    #
    # --------------- QuNexTurnkeyCleanFunction end ----------------

#
# =-=-=-=-=-=-= TURNKEY COMMANDS END =-=-=-=-=-=-=


# =-=-=-=-=-=-= RUN SPECIFIC COMMANDS START =-=-=-=-=-=-=

if [ -z "$TURNKEY_STEPS" ] && [ ! -z "$AcceptanceTest" ] && [ "$AcceptanceTest" != "yes" ]; then
    echo "";
    echo "  ---------------------------------------------------------------------"
    echo ""
    echo "   ---> Performing completion check on specific QuNex turnkey units: ${AcceptanceTest}"
    echo ""
    echo "  ---------------------------------------------------------------------"
    echo ""

    # --------------------------------------------------------------------------
    # -- Only perform completion checks
    # --------------------------------------------------------------------------

    RunAcceptanceTestFunction

else

    # --------------------------------------------------------------------------
    # -- Check turnkey steps and execute in a loop
    # --------------------------------------------------------------------------

    if [ "$TURNKEY_STEPS" == "all" ]; then
        echo "";
        echo "  ---------------------------------------------------------------------"
        echo ""
        echo "   ---> Executing all QuNex turkey workflow steps: ${QuNexTurnkeyWorkflow}"
        echo ""
        echo "  ---------------------------------------------------------------------"
        echo ""
        TURNKEY_STEPS=${QuNexTurnkeyWorkflow}
    fi
    if [ "$TURNKEY_STEPS" != "all" ]; then
        echo "";
        echo "  ---------------------------------------------------------------------"
        echo ""
        echo "   ---> Executing specific QuNex turkey workflow steps: ${TURNKEY_STEPS}"
        echo ""
        echo "  ---------------------------------------------------------------------"
        echo ""
    fi

    # -- Loop through specified Turnkey steps if requested
    unset TURNKEY_STEP_ERRORS
    for TURNKEY_STEP in ${TURNKEY_STEPS}; do

        # -- Execute turnkey
        turnkey_${TURNKEY_STEP}

        # -- Generate single session log folders
        if [[ ${TURNKEY_STEP} == "create_study" ]] || [[ ${TURNKEY_STEP} == "create_batch" ]] || [[ ${TURNKEY_STEP} == "create_session_info" ]] || [[ ${TURNKEY_STEP} == "import_dicom" ]]; then
            CheckComLog=`ls -t1 ${QuNexMasterLogFolder}/comlogs/*${TURNKEY_STEP}*log 2> /dev/null | head -n 1`
        else
            CheckComLog=`ls -t1 ${QuNexMasterLogFolder}/comlogs/*${TURNKEY_STEP}*${CASE}*log 2> /dev/null | head -n 1`
        fi

        # -- Specific sets of functions for logging
        BashBOLDFunctions="parcellate_bold compute_bold_fc_gbc compute_bold_fc_seed"
        NiUtilsFunctions="setup_hcp hcp_pre_freesurfer hcp_freesurfer hcp_post_freesurfer hcp_fmri_volume hcp_fmri_surface hcpd compute_bold_stats create_stats_report extract_nuisance_signal preprocess_bold preprocess_conc"

        # -- Specific checks for all other functions
        if [ ! -z "${NiUtilsFunctions##*${TURNKEY_STEP}*}" ] && [ ! -z "${BashBOLDFunctions##*${TURNKEY_STEP}*}" ]; then
            echo " ---> run_turnkey acceptance testing ${TURNKEY_STEP} logs for completion."; echo ""
            if [ -z "${CheckComLog}" ]; then
               TURNKEY_STEP_ERRORS="yes"
               echo " ---> ERROR: comlog file for ${TURNKEY_STEP} step not found during run_turnkey acceptance testing."
            fi
            if [ ! -z "${CheckComLog}" ]; then
               echo " ---> run_turnkey acceptance testing found comlog file for ${TURNKEY_STEP} step:"
               echo "      ${CheckComLog}"
               chmod 777 ${CheckComLog} 2>/dev/null
            fi
            if [ -z `echo "${CheckComLog}" | grep 'done'` ]; then
                echo ""; echo " ---> ERROR: run_turnkey acceptance test for ${TURNKEY_STEP} step failed."
                TURNKEY_STEP_ERRORS="yes"
            else
                echo ""; echo " ---> SUCCESSFUL run_turnkey acceptance test for ${TURNKEY_STEP}"; echo ""
                TURNKEY_STEP_ERRORS="no"
            fi
        fi

        # -- Run acceptance tests for specific QuNex units
        if [[ AcceptanceTest == "yes" ]]; then
            UnitTest="${TURNKEY_STEP}"
            RunAcceptanceTestFunction
        fi

        # -- Run QuNex cleaning for specific unit
        #    Currently supporting hcp_fmri_volume
        if [[ ${TURNKEY_CLEAN} == "yes" ]]; then
           if [[ "${TURNKEY_STEP}" == "hcp_fmri_volume" ]]; then
               if [[ "${TURNKEY_STEP_ERRORS}" == "no" ]]; then
                   QuNexTurnkeyCleanFunction
               else
                   echo ""; echo " ---> ERROR: ${TURNKEY_STEP} step did not complete. Skipping cleaning for debugging purposes."; echo ""
               fi
           fi
        fi
    done

    if [ ${TURNKEY_TYPE} == "xnat" ]; then
        echo "---> Cleaning up DICOMs from build directory to save space:"
        if [[ ${DATAFormat} == "DICOM" ]]; then
            echo ""
            echo "     - removing dicom files"
            # Temp storage for kept files
            mkdir ${QuNexWorkDir}/dicomtmp
            #check for logs and move them
            logCount=`ls ${QuNexWorkDir}/dicom/*.log | wc -l`
            if [ $logCount != 0 ]; then
                mv ${QuNexWorkDir}/dicom/*.log ${QuNexWorkDir}/dicomtmp
            fi
            #check for txt files and move them
            logCount=`ls ${QuNexWorkDir}/dicom/*.txt | wc -l`
            if [ $logCount != 0 ]; then
                mv ${QuNexWorkDir}/dicom/*.txt ${QuNexWorkDir}/dicomtmp
            fi
            rm  -rf ${QuNexWorkDir}/dicom &> /dev/null
            mv ${QuNexWorkDir}/dicomtmp ${QuNexWorkDir}/dicom
            echo ""
        fi
        echo "     - removing stray xml catalog files"
        find ${StudyFolder} -name *catalog.xml -exec echo "       -> {}" \; -exec rm {} \; 2> /dev/null

        if [[ ${CleanupOldFiles} == "yes" ]]; then
            echo "     - removing files older than run"
            find ${StudyFolder} ! -newer ${WORKDIR}/_startfile -exec echo "       -> {}" \; -exec rm {} \; 2> /dev/null
            rm ${WORKDIR}/_startfile
        fi
    fi
fi

# =-=-=-=-=-=-= RUN SPECIFIC COMMANDS END =-=-=-=-=-=-=

# ------------------------------------------------------------------------------
# -- Report final error checks
# ------------------------------------------------------------------------------

if [[ "${TURNKEY_STEP_ERRORS}" == "yes" ]]; then
    echo ""
    echo " ---> Appears some run_turnkey steps have failed."
    echo ""
    echo "       Check ${QuNexMasterLogFolder}/comlogs"
    echo "       Check ${QuNexMasterLogFolder}/runlogs"
    echo ""
    exit 1
else
    echo ""
    echo "------------------------- Successful completion of work --------------------------------"
    echo ""
fi

}

# ------------------------------------------------------------------------------
# -- Execute overall function and read arguments
# ------------------------------------------------------------------------------

main $@
