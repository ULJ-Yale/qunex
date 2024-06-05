#!/bin/bash

# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

SupportedAcceptanceTestSteps="hcp_pre_freesurfer hcp_freesurfer hcp_post_freesurfer hcp_fmri_volume hcp_fmri_surface bold_images"

usage() {
 echo ""
 echo "QuNexAcceptanceTest"
 echo ""
 echo "This function implements QuNex acceptance testing per pipeline unit."
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "Local system variables if using QuNex hierarchy:"
 echo ""
 echo "--acceptancetest   Specify if you wish to run a final acceptance test after "
 echo "                   each unit of processing."
 echo "                   Supported: ${SupportedAcceptanceTestSteps}"
 echo "--studyfolder      Path to study data folder"
 echo "--sessionsfolder   Path to study data folder where the sessions folders reside"
 echo "--subjects         Comma separated list of subjects to run that are "
 echo "                   study-specific and correspond to XNAT database subject IDs"
 echo "--sessionlabels    Label for session within project. Note: may be general "
 echo "                   across multiple subjects (e.g. rest) or for longitudinal "
 echo "                   runs."
 echo "--runtype          Default is [], which executes a local file system run, but "
 echo "                   requires --studyfolder to set"
 echo ""
 echo "INPUTS RELATED TO XNAT"
 echo "----------------------"
 echo ""
 echo "Note: To invoke this function you need a credential file in your home folder or "
 echo "provide one using --xnatcredentials parameter or --xnatuser and --xnatpass "
 echo "parameters: " 
 echo ""
 echo "--xnatcredentialfile    Specify XNAT credential file name. [${HOME}/.xnat]"
 echo "                        This file stores the username and password for the "
 echo "                        XNAT site. Permissions of this file need to be set to "
 echo "                        400. If this file does not exist the script will "
 echo "                        prompt you to generate one using default name. If user "
 echo "                        provided a file name but it is not found, this name "
 echo "                        will be used to generate new credentials. User needs "
 echo "                        to provide this specific credential file for next run, "
 echo "                        as script by default expects ${HOME}/.xnat"
 echo "--xnatprojectid         Specify the XNAT site project id. This is the Project " 
 echo "                        ID in XNAT and not the Project Title. This project "
 echo "                        should be created on the XNAT Site prior to upload. If "
 echo "                        it is not found on the XNAT Site or not provided then "
 echo "                        the data will land into the prearchive and be left "
 echo "                        unassigned to a project."
 echo "                        Please check upon completion and specify assignment "
 echo "                        manually."
 echo "--xnathost              Specify the XNAT site hostname URL to push data to."
 echo "--xnatuser              Specify XNAT username required if credential file is "
 echo "                        not found"
 echo "--xnatpass              Specify XNAT password required if credential file is "
 echo "                        not found"
 echo "--bidsformat            Specify if XNAT data is in BIDS format (yes/no). [no]"
 echo "                        If --bidsformat='yes' then the subject naming follows "
 echo "                        <SubjectLabel_SessionLabel> convention"
 echo "--xnatsubjectid         ID for subject across the entire XNAT database. "
 echo "                        Required or --xnatsubjectlabels needs to be set."
 echo "--xnatsubjectlabels     Label for subject within a project for the XNAT "
 echo "                        database. Default assumes it matches --subjects."
 echo "                        If your XNAT database subject label is distinct from "
 echo "                        your local server subject id then please supply this "
 echo "                        flag."
 echo "                        Use if your XNAT database has a different set of "
 echo "                        subject ids."
 echo "--xnatsessionlabels     Label for session within XNAT project. Note: may be "
 echo "                        general across multiple subjects (e.g. rest). Required."
 echo "--xnataccsessionid      ID for subject-specific session within the XNAT "
 echo "                        project. Derived from XNAT but can be set manually."
 echo "--resetcredentials      Specify <yes> if you wish to reset your XNAT site user "
 echo "                        and password. Default is [no]"
 echo "--xnatgetqc             Specify if you wish to download QC PNG images and/or "
 echo "                        scene files for a given acceptance unit where QC is "
 echo "                        available. Default is [no]. Options: "
 echo ""
 echo "                        - 'image' ... download only the image files "
 echo "                        - 'scene' ... download only the scene files" 
 echo "                        - 'all'   ... download both png images and scene files"
 echo ""
 echo "--xnatarchivecommit     Specify if you wish to commit the results of "
 echo "                        acceptance testing back to the XNAT archive. Default "
 echo "                        is [no]. Options: "
 echo ""
 echo "                        -'session' ... commit to subject session only "
 echo "                        -'project' ... commit group results to project only" 
 echo "                        -'all'     ... commit both subject and group results"
 echo ""
 echo "BOLD PROCESSING ACCEPTANCE TEST INPUTS"
 echo "--------------------------------------"
 echo ""
 echo "--bolddata              Specify BOLD data numbers separated by comma or pipe. "
 echo "                        E.g. --bolddata='1,2,3,4,5'. This flag is "
 echo "                        interchangeable with --bolds or --boldruns to allow "
 echo "                        more redundancy in specification"
 echo "                        Note: If unspecified empty the QC script will by "
 echo "                        default look into "
 echo "                        /<path_to_study_sessions_folder>/<session_id>/session_hcp.txt"
 echo "                        and identify all BOLDs to process"
 echo "--boldimages            Specify a list of required BOLD images separated by "
 echo "                        comma or pipe. Where the number of the bold image "
 echo "                        would be, indicate by '{N}', e.g:"
 echo "                        --boldimages='bold{N}_Atlas.dtseries.nii|seed_bold{N}_Atlas_s_hpss_res-VWMWB_lpss_LR-Thal.dtseriesnii' "
 echo "                        When running the test, '{N}' will be replaced by the "
 echo "                        bold numbers given in --bolddata "
 echo ""
 echo "EXAMPLE USE"
 echo "==========="
 echo ""
 echo "::"
 echo ""
 echo " qunex_acceptance_test.sh --studyfolder='<absolute_path_to_study_folder>' \ "
 echo " --subjects='<subject_IDs_on_local_server>' \ "
 echo " --xnatprojectid='<name_of_xnat_project_id>' \ "
 echo " --xnathost='<XNAT_site_URL>' "
 echo ""
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]] || [[ $1 == "help" ]] || [[ $1 == "usage" ]]; then
    usage
fi

# ------------------------------------------------------------------------------
# -- Parse and check all arguments
# ------------------------------------------------------------------------------

# -- Set general options functions
opts_GetOpt() {
sopt="$1"
shift 1
for fn in "$@" ; do
    if [ `echo ${fn} | grep -- "^${sopt}=" | wc -w` -gt 0 ]; then
        echo "${fn}" | sed "s/^${sopt}=//"
        return 0
    fi
done
}

opts_CheckForHelpRequest() {
for fn in "$@" ; do
    if [ "$fn" = "--help" ]; then
        return 0
    fi
done
}

if [ $(opts_CheckForHelpRequest $@) ]; then
    showVersion
    show_usage
    exit 0
fi

# -- Initialize global output variables
unset CASES
unset StudyFolder
unset SessionsFolder
unset SESSIONS
unset SESSION_LABELS
unset BOLDS # --bolddata
unset BOLDRUNS # --bolddata
unset BOLDDATA # --bolddata
unset BOLDImages # --boldimages

unset XNAT_HOST_NAME
unset XNAT_USER_NAME
unset XNAT_PASSWORD
unset XNAT_PROJECT_ID

unset XNAT_ACCSESSION_ID
unset XNAT_SUBJECT_ID
unset XNAT_SUBJECT_LABEL
unset XNAT_SUBJECT_LABELS
unset XNAT_SESSION_LABELS
unset XNAT_CREDENTIALS
unset XNAT_CREDENTIAL_FILE
unset XNATgetQC
unset XNATArchiveCommit
unset XNATResetCredentials

unset AcceptanceTestSteps
unset BIDSFormat
unset RUN_TYPE



# -- Parse general arguments
StudyFolder=`opts_GetOpt "--studyfolder" $@`
CASES=`opts_GetOpt "--subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'`
SESSION_LABELS=`opts_GetOpt "--sessionlabel" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
if [[ -z ${SESSION_LABELS} ]]; then
SESSION_LABELS=`opts_GetOpt "--session" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
fi
if [[ -z ${SESSION_LABELS} ]]; then
SESSION_LABELS=`opts_GetOpt "--sessionlabels" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
fi
if [[ -z ${SESSION_LABELS} ]]; then
SESSION_LABELS=`opts_GetOpt "--sessions" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
fi
SESSIONS="${SESSION_LABELS}"
RUN_TYPE=`opts_GetOpt "--runtype" $@`
AcceptanceTestSteps=`opts_GetOpt "--acceptancetests" "$@" | sed 's/,/ /g;s/|/ /g'`; AcceptanceTestSteps=`echo "$AcceptanceTestSteps" | sed 's/,/ /g;s/|/ /g'`
if [[ -z ${AcceptanceTestSteps} ]]; then
AcceptanceTestSteps=`opts_GetOpt "--acceptancetest" "$@" | sed 's/,/ /g;s/|/ /g'`; AcceptanceTestSteps=`echo "$AcceptanceTestSteps" | sed 's/,/ /g;s/|/ /g'`
fi

# -- Parse BOLD arguments
BOLDS=`opts_GetOpt "--bolds" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
if [ -z "${BOLDS}" ]; then
    BOLDS=`opts_GetOpt "--boldruns" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
fi
if [ -z "${BOLDS}" ]; then
    BOLDS=`opts_GetOpt "--bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
fi
BOLDRUNS="${BOLDS}"
BOLDDATA="${BOLDS}"
BOLDSuffix=`opts_GetOpt "--boldsuffix" $@`
BOLDPrefix=`opts_GetOpt "--boldprefix" $@`
BOLDImages=`opts_GetOpt "--boldimages" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDImages=`echo "${BOLDImages}" | sed 's/,/ /g;s/|/ /g'`

# -- If data is in BIDS format on XNAT
BIDSFormat=`opts_GetOpt "--bidsformat" $@`

# -- Start of parsing XNAT arguments
#
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
#                                                                                                                                                                                                                           EXAMPLE in Web UI    MR Session:   A project-specific, session-specific and subject-specific XNAT variable that defines the precise acquisition / experiment
#
    XNAT_HOST_NAME=`opts_GetOpt "--xnathost" $@`
    XNAT_PROJECT_ID=`opts_GetOpt "--xnatprojectid" $@`
    XNAT_SUBJECT_LABELS=`opts_GetOpt "--xnatsubjectlabels" "$@" | sed 's/,/ /g;s/|/ /g'`; XNAT_SUBJECT_LABELS=`echo "$XNAT_SUBJECT_LABELS" | sed 's/,/ /g;s/|/ /g'`
    XNAT_SESSION_LABELS=`opts_GetOpt "--xnatsessionlabel" "$@" | sed 's/,/ /g;s/|/ /g'`; XNAT_SESSION_LABELS=`echo "$XNAT_SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
    if [[ -z ${XNAT_SESSION_LABELS} ]]; then
    XNAT_SESSION_LABELS=`opts_GetOpt "--xnatsessionlabels" "$@" | sed 's/,/ /g;s/|/ /g'`; XNAT_SESSION_LABELS=`echo "$XNAT_SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
    fi
    XNAT_SUBJECT_ID=`opts_GetOpt "--xnatsubjectid" $@`
    XNAT_ACCSESSION_ID=`opts_GetOpt "--xnataccsessionid" $@`
    XNAT_USER_NAME=`opts_GetOpt "--xnatuser" $@`
    XNAT_PASSWORD=`opts_GetOpt "--xnatpass" $@`
    XNAT_CREDENTIAL_FILE=`opts_GetOpt "--xnatcredentialfile" $@`
    XNATResetCredentials=`opts_GetOpt "--resetcredentials" $@`
    XNATArchiveCommit=`opts_GetOpt "--xnatarchivecommit" $@`
    XNATgetQC=`opts_GetOpt "--xnatgetqc" $@`
#
# -- END of parsing XNAT arguments

# -- Check acceptance test flag
if [[ -z ${AcceptanceTestSteps} ]]; then 
    usage
    echo "ERROR: --acceptancetest flag not specified. No steps to perform acceptance testing on."; echo "";
    exit 1
else
    # -- Run checks for supported steps
    unset FoundSupported
    echo ""
    echo "---> Checking that requested ${AcceptanceTestSteps} are supported..."
    echo ""
    AcceptanceTestStepsChecks="$AcceptanceTestSteps"
    unset AcceptanceTestSteps
    for AcceptanceTestStep in ${AcceptanceTestStepsChecks}; do
       if [ ! -z "${SupportedAcceptanceTestSteps##*${AcceptanceTestStep}*}" ]; then
           echo "---> ${AcceptanceTestStep} is not supported. Will remove from requested list."
       else
           echo "---> ${AcceptanceTestStep} is supported."
           FoundSupported="yes"
           AcceptanceTestSteps="${AcceptanceTestSteps} ${AcceptanceTestStep}"
       fi
    done
    if [[ -z ${FoundSupported} ]]; then 
        usage
        echo "ERROR: None of the requested acceptance tests are currently supported."; echo "";
        echo "Supported: ${SupportedAcceptanceTestSteps}"; echo "";
        exit 1
    fi
fi

# -- Check and set run type
if [[ -z ${RUN_TYPE} ]]; then 
    RUN_TYPE="local"
    echo "Note: Run type not specified. Setting default turnkey type to local run."; echo ""
    echo "Note: If you wish to run acceptance tests on an XNAT host, re-run with flag --runtype='xnat' "; echo ""
fi

######################## START NON-XNAT SPECIFIC CHECKS  #######################
#
if [[ ${RUN_TYPE} != "xnat" ]]; then 
   if [[ -z ${StudyFolder} ]]; then usage; echo "Error: Requesting local run but --studyfolder flag is missing."; echo ""; exit 1; fi
   if [[ -z ${CASES} ]]; then usage; echo "Error: Requesting local run but --subject flag is missing."; echo ""; exit 1; fi
   if [[ -z ${SESSION_LABELS} ]]; then usage; SESSION_LABELS=""; echo "Note: --sessionlabels are not defined. Assuming no label info."; echo ""; fi
    RunAcceptanceTestDir="${StudyFolder}/processing/logs/acceptTests"
    if [ -z ${SessionsFolder} ]; then SessionsFolder="${StudyFolder}/sessions"; fi
    echo ""
    echo "Note: Acceptance tests will be saved in selected study folder: $RunAcceptanceTestOut"
    echo ""
    if [[ ! -d ${RunAcceptanceTestDir} ]]; then mkdir -p ${RunAcceptanceTestDir} > /dev/null 2>&1; fi
fi
#
######################## END NON-XNAT SPECIFIC CHECKS  #########################

########################  START XNAT SPECIFIC CHECKS  ##########################
#
if [[ ${RUN_TYPE} == "xnat" ]]; then
    echo ""
    if [[ -z ${XNAT_PROJECT_ID} ]]; then usage; echo "Error: --xnatprojectid flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${XNAT_HOST_NAME} ]]; then usage; echo "Error: --xnathost flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${XNAT_SESSION_LABELS} ]] && [[ -z ${XNAT_ACCSESSION_ID} ]]; then usage; echo "Error: --xnatsessionlabels and --xnataccsessionid flags are both missing. Please specify session label and re-run."; echo ''; exit 1; fi
    if [[ -z ${XNATArchiveCommit} ]]; then unset XNATArchiveCommit; echo "Note: --xnatarchivecommit not requested. Results will only be stored locally."; echo ''; fi
    if [[  ${XNATArchiveCommit} != "session" &&  ${XNATArchiveCommit} != "project" &&  ${XNATArchiveCommit} != "all" ]]; then echo "Note: --xnatarchivecommit was set to '$XNATArchiveCommit', which is not supported. Check usage for available options."; unset XNATArchiveCommit; echo ''; fi
    if [[ -z ${XNATgetQC} ]]; then unset XNATgetQC; echo "Note: --xnatgetqc not requested. QC images will not be downloaded."; echo ''; fi
    if [[ ${XNATgetQC} != "scene" &&  ${XNATgetQC} != "image" &&  ${XNATgetQC} != "all" &&  ${XNATgetQC} != "png" &&  ${XNATgetQC} != "pngs" &&  ${XNATgetQC} != "images" &&  ${XNATgetQC} != "scenes" &&  ${XNATgetQC} != "snr" &&  ${XNATgetQC} != "SNR" &&  ${XNATgetQC} != "TSNR" &&  ${XNATgetQC} != "SNR" ]]; then 
        echo "Note: --xnatgetqc was set to '$XNATgetQC', which is not supported. Check usage for available options."; unset XNATgetQC; echo ''; 
    fi

    ## -- Check for subject labels
    if [[ -z ${CASES} ]] && [[ -z ${XNAT_SUBJECT_LABELS} ]]; then
        usage
        echo "ERROR: --subjects flag and --xnatsubjectlabels flag not specified. No cases to work with. Please specify either."
        echo ""
        exit 1
    fi
    ## -- Check CASES variable
    if [[ -z ${CASES} ]]; then
        CASES="$XNAT_SUBJECT_LABELS"
        echo "Note: --subjects flag omitted. Assuming specified --xnatsubjectlabels names match the subjects folders on the file system."
        echo ""
    fi
    ## -- Check XNAT_SUBJECT_LABELS
    if [[ -z ${XNAT_SUBJECT_LABELS} ]]; then
        XNAT_SUBJECT_LABELS="$CASES"
        echo ""
        echo "Note: --xnatsubjectlabels flag omitted. Assuming specified --subjects names match the subject labels in XNAT."
        echo ""
    fi

    # ------------------------------------------------------------------------------
    # -- First check if .xnat credentials exist:
    # ------------------------------------------------------------------------------
    
    ## -- Set reseting credentials to no if not provided 
    if [ -z ${XNATResetCredentials} ]; then XNATResetCredentials="no"; fi
    ## -- Set  credentials file name to default if not provided
    if [ -z ${XNAT_CREDENTIAL_FILE} ]; then XNAT_CREDENTIAL_FILE=".xnat"; fi

    ## -- Reset credentials
    if [[ "${ResetCredential}" == "yes" ]]; then
        echo ""
        echo " -- Reseting XNAT credentials in ${HOME}/${XNAT_CREDENTIAL_FILE} "
        rm -f ${HOME}/${XNAT_CREDENTIAL_FILE} &> /dev/null
    fi
    ## -- Check for valid xNAT credential file
    if [ -f ${HOME}/${XNAT_CREDENTIAL_FILE} ]; then
        echo ""
        ceho " -- XNAT credentials in ${HOME}/${XNAT_CREDENTIAL_FILE} found. Performing credential checks... "
        XNAT_USER_NAME=`cat ${HOME}/${XNAT_CREDENTIAL_FILE} | cut -d: -f1`
        XNAT_PASSWORD=`cat ${HOME}/${XNAT_CREDENTIAL_FILE} | cut -d: -f2`
        if [[ ! -z ${XNAT_USER_NAME} ]] && [[ ! -z ${XNAT_PASSWORD} ]]; then
            echo ""
            ceho " -- XNAT credentials parsed from ${HOME}/${XNAT_CREDENTIAL_FILE} " 
            echo ""
        fi
    else
        echo ""
        echo " -- XNAT credentials in ${HOME}/${XNAT_CREDENTIAL_FILE} NOT found. Checking for --xnatuser and --xnatpass flags."
        echo ""
        if [[ -z ${XNAT_USER_NAME} ]] || [[ -z ${XNAT_PASSWORD} ]]; then
            echo ""
            echo "ERROR: --xnatuser and/or --xnatpass flags are missing. Regenerating credentials now..."
            echo ""
            echo "   ---> Enter your XNAT XNAT_HOST_NAME username:"
            if read -s answer; then
                XNAT_USER_NAME=$answer
            fi
            echo "   ---> Enter your XNAT XNAT_HOST_NAME password:"
            if read -s answer; then
                XNAT_PASSWORD=$answer
            fi
        else
            echo $XNAT_USER_NAME:$XNAT_PASSWORD >> ${HOME}/${XNAT_CREDENTIAL_FILE}
            chmod 400 ${HOME}/${XNAT_CREDENTIAL_FILE}
            ceho " -- XNAT credentials generated in ${HOME}/${XNAT_CREDENTIAL_FILE}"
            echo ""
        fi
    fi
    ## -- Get credentials
    XNAT_CREDENTIALS=$(cat ${HOME}/${XNAT_CREDENTIAL_FILE})
    CheckXNATConnect=`curl -Is -u ${XNAT_CREDENTIALS} ${XNAT_HOST_NAME} | head -1 | grep "200 OK"`
    if [[ ! -z ${CheckXNATConnect} ]]; then
        ceho " -- XNAT Connection tested OK for ${XNAT_HOST_NAME}. Proceeding..."
        echo ""
        XNAT_USER_NAME=`echo $XNAT_CREDENTIALS | cut -d: -f1`; XNAT_PASSWORD=`echo $XNAT_CREDENTIALS | cut -d: -f2`
    else 
        echo "ERROR: XNAT credentials for ${XNAT_HOST_NAME} failed. Re-check your login and password and your ${HOME}/${XNAT_CREDENTIAL_FILE}"
        echo ""
        exit 1
    fi
    
    ## -- Setup XNAT log variables
    if [[ -z ${StudyFolder} ]]; then
        XNATInfoPath="${HOME}/acceptTests/xnatlogs"
        echo "Note: --sessionsfolder flag omitted. Setting logs to $XNATInfoPath"
        echo ""
    else
        XNATInfoPath="${StudyFolder}/processing/logs/acceptTests/xnatlogs"
    fi
    mkdir -p ${XNATInfoPath} &> /dev/null
    if [[ ! -d ${XNATInfoPath} ]]; then
        echo ""
        echo " -- XNAT info folder ${XNATInfoPath} still not found. Check file system paths or permissions..."
        echo ""
        exit 1
    else
        echo ""
        echo " -- XNAT info folder ${XNATInfoPath} generated. Proceeding..."
        echo ""
    fi
    
    ## -- Setup acceptance test location
    RunAcceptanceTestDir="$(dirname ${XNATInfoPath})"
    if [[ -z ${SessionsFolder} ]]; then SessionsFolder="${StudyFolder}/sessions"; fi
    
    echo ""
    echo "Note: Acceptance tests will be saved in selected study folder: $RunAcceptanceTestDir"
    echo ""
    if [[ ! -d ${RunAcceptanceTestDir} ]]; then mkdir -p ${RunAcceptanceTestDir} > /dev/null 2>&1; fi
    
    ## -- Obtain temp info on subjects and experiments in the project
    XNATTimeStamp=`date +%Y-%m-%d_%H.%M.%S.%6N`
    curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -m 30 -X GET "${XNAT_HOST_NAME}/data/sessions?project=${XNAT_PROJECT_ID}&format=csv" > ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${XNATTimeStamp}.csv
    curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -m 30 -X GET "${XNAT_HOST_NAME}/data/experiments?project=${XNAT_PROJECT_ID}&format=csv" > ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${XNATTimeStamp}.csv

    if [ -f ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${XNATTimeStamp}.csv ] && [ -f ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${XNATTimeStamp}.csv ]; then
       echo ""
       echo "  ---> Downloaded XNAT project info: "; echo ""
       echo "      ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${XNATTimeStamp}.csv"
       echo "      ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${XNATTimeStamp}.csv"
       echo ""
    else
       if [ ! -f ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${XNATTimeStamp}.csv ]; then
           echo ""
           echo " ERROR: ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${XNATTimeStamp}.csv not found! "
           echo ""
           exit 1
       fi
       if [ ! -f ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${XNATTimeStamp}.csv ]; then
           echo ""
           echo " ERROR: ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${XNATTimeStamp}.csv not found! "
           echo ""
           exit 1
       fi
    fi
fi
#
########################  END XNAT SPECIFIC CHECKS  ############################



# -- Report all requested options
    echo ""
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo ""
    echo "   QuNex Subjects labels: ${CASES}" 
    if [ "$RUN_TYPE" != "xnat" ]; then
        echo "   QuNex study folder: ${StudyFolder}"
        echo "   QuNex study sessions: ${SESSION_LABELS}"
    fi
    if [ "$RUN_TYPE" == "xnat" ]; then
        echo "   XNAT Hostname: ${XNAT_HOST_NAME}"
        echo "   Reset XNAT site credentials: ${XNATResetCredentials}"
        echo "   XNAT site credentials file: ${HOME}/${XNAT_CREDENTIAL_FILE}"
        echo "   XNAT Project ID: ${XNAT_PROJECT_ID}"
        echo "   XNAT Subject Labels: ${XNAT_SUBJECT_LABELS}"
        if [[ ! -z ${XNAT_SESSION_LABELS} ]]; then 
        echo "   XNAT Session Labels: ${XNAT_SESSION_LABELS}"
        fi
        if [[ ! -z ${XNAT_ACCSESSION_ID} ]]; then 
        echo "   XNAT Accession ID: ${XNAT_ACCSESSION_ID}"
        fi
        echo "   XNAT Archive Commit: ${XNATArchiveCommit}"
        echo "   XNAT get QC images or scenes: ${XNATgetQC}"

    fi
    echo "   QuNex Acceptance test steps: ${AcceptanceTestSteps}"
    if [[ -z ${BOLDS} ]]; then 
        echo "   BOLD runs: ${BOLDS}"
        if [[ -z ${BOLDImages} ]]; then 
            echo "   BOLD Images: ${BOLDImages}"
        fi
    fi
    echo "   QuNex Acceptance test output log: ${RunAcceptanceTestOut}"
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - End --"
    echo ""
    echo "------------------------- Start of work --------------------------------"
    echo ""

################################ DO WORK #######################################

main() {

echo ""
ceho "       *******************************************************"
ceho "       ****** Performing QuNex Unit Acceptance Tests ********"
ceho "       *******************************************************"
echo ""

# ------------------------------------------------------------------------------
# -- Check the server you are transfering data from:
# ------------------------------------------------------------------------------

TRANSFERNODE=`hostname`
echo ""
echo "-- Checking data from: ${TRANSFERNODE}"
echo ""

# ------------------------------------------------------------------------------
#  -- Set correct info per subject
# ------------------------------------------------------------------------------

    ## -- Function to run on each subject
    UnitTestingFunction() {
    
            if [ ${RUN_TYPE} == "xnat" ]; then
                XNAT_SUBJECT_LABEL="$CASE"
                unset Status
                # -- Define XNAT_SUBJECT_ID (i.e. Accession number) and XNAT_SESSION_LABEL (i.e. MR Session lablel) for the specific XNAT_SUBJECT_LABEL (i.e. subject)
                unset XNAT_SUBJECT_ID XNAT_SESSION_LABEL_HOST XNAT_ACCSESSION_ID
                XNAT_SUBJECT_ID=`cat ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${XNATTimeStamp}.csv | grep "${XNAT_SUBJECT_LABEL}" | awk  -F, '{print $1}'`
                XNAT_SUBJECT_LABEL=`cat ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${XNATTimeStamp}.csv | grep "${XNAT_SUBJECT_ID}" | awk  -F, '{print $3}'`
                if [[ -z ${XNAT_SESSION_LABEL} ]]; then
                    XNAT_SESSION_LABEL_HOST=`cat ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${XNATTimeStamp}.csv | grep "${XNAT_SUBJECT_LABEL}" | grep "${XNAT_ACCSESSION_ID}" | awk  -F, '{print $5}'`
                    XNAT_SESSION_LABEL=`echo ${XNAT_SESSION_LABEL_HOST} | sed 's|$CASE_||g'`
                else
                    XNAT_SESSION_LABEL_HOST=`cat ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${XNATTimeStamp}.csv | grep "${XNAT_SUBJECT_LABEL}" | grep "${XNAT_SESSION_LABEL}" | awk  -F, '{print $5}'`
                fi
                XNAT_ACCSESSION_ID=`cat ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${XNATTimeStamp}.csv | grep "${XNAT_SUBJECT_LABEL}" | grep "${XNAT_SESSION_LABEL}" | awk  -F, '{print $1}'`
                
                # -- Report error if variables remain undefined
                if [[ -z ${XNAT_SUBJECT_ID} ]] || [[ -z ${XNAT_SUBJECT_LABEL} ]] || [[ -z ${XNAT_ACCSESSION_ID} ]] || [[ -z ${XNAT_SESSION_LABEL_HOST} ]]; then 
                    echo ""
                    echo "Some or all of XNAT database variables were not set correctly: "
                    echo ""
                    echo "  ---> XNAT_SUBJECT_ID     :  $XNAT_SUBJECT_ID "
                    echo "  ---> XNAT_SUBJECT_LABEL  :  $XNAT_SUBJECT_LABEL "
                    echo "  ---> XNAT_ACCSESSION_ID  :  $XNAT_ACCSESSION_ID "
                    echo "  ---> XNAT_SESSION_LABEL  :  $XNAT_SESSION_LABEL_HOST "
                    echo ""
                    Status="FAIL"
                    # -- Set the XNAT_SESSION_LABEL_HOST were it correct to allow naming of the *.txt files
                    XNAT_SESSION_LABEL_HOST="${CASE}_${XNAT_SESSION_LABEL}"
                else
                    echo ""
                    echo "Successfully read all XNAT database variables: "
                    echo ""
                    echo "  ---> XNAT_SUBJECT_ID     :  $XNAT_SUBJECT_ID "
                    echo "  ---> XNAT_SUBJECT_LABEL  :  $XNAT_SUBJECT_LABEL "
                    echo "  ---> XNAT_ACCSESSION_ID  :  $XNAT_ACCSESSION_ID "
                    echo "  ---> XNAT_SESSION_LABEL  :  $XNAT_SESSION_LABEL_HOST "
                    echo ""
                fi
            
                # -- Define final variable set
                CASE="${XNAT_SUBJECT_LABEL}"
                fi
            fi
        
            UnitTests=${AcceptanceTestSteps}
            echo ""
            echo "-- Running QuNex unit tests: ${UnitTests}"

            
            ## -- Setup function to check presence of files on either local file system or on XNAT on 
            UnitTestDataCheck() {
                SubjectSessionTimeStamp=`date +%Y-%m-%d_%H.%M.%S.%6N`
                if [[ ${RUN_TYPE} == "xnat" ]]; then
                       if ( curl -k -b "JSESSIONID=$JSESSION" -m 20 -o/dev/null -sfI ${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_SESSION_LABEL_HOST}/resources/qunex_study/files/sessions/${CASE}/${UnitTestData} ); then 
                           Status="PASS"
                           echo "     ${UnitTest} PASS: ${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_SESSION_LABEL_HOST}/resources/qunex_study/files/sessions/${CASE}/${UnitTestData}"
                           echo "  ${UnitTest} PASS: ${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_SESSION_LABEL_HOST}/resources/qunex_study/files/sessions/${CASE}/${UnitTestData}" >> ${RunAcceptanceTestOut}
                           echo "  ${UnitTest} PASS: ${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_SESSION_LABEL_HOST}/resources/qunex_study/files/sessions/${CASE}/${UnitTestData}" >> ${RunAcceptanceTestDir}/${XNAT_SESSION_LABEL_HOST}_${UnitTest}_${SubjectSessionTimeStamp}_${Status}.txt
                       else 
                           Status="FAIL"
                           echo "     ${UnitTest} FAIL: ${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_SESSION_LABEL_HOST}/resources/qunex_study/files/sessions/${CASE}/${UnitTestData}"
                           echo "  ${UnitTest} FAIL: ${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_SESSION_LABEL_HOST}/resources/qunex_study/files/sessions/${CASE}/${UnitTestData}" >> ${RunAcceptanceTestOut}
                           echo "  ${UnitTest} FAIL: ${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_SESSION_LABEL_HOST}/resources/qunex_study/files/sessions/${CASE}/${UnitTestData}" >> ${RunAcceptanceTestDir}/${XNAT_SESSION_LABEL_HOST}_${UnitTest}_${SubjectSessionTimeStamp}_${Status}.txt
                       fi
                       if [ -f ${RunAcceptanceTestDir}/${XNAT_SESSION_LABEL_HOST}_${UnitTest}_${SubjectSessionTimeStamp}_${Status}.txt ]; then 
                           echo ""
                           echo "     Individual file saved for XNAT archiving: ${RunAcceptanceTestDir}/${XNAT_SESSION_LABEL_HOST}_${UnitTest}_${SubjectSessionTimeStamp}_${Status}.txt "
                       else
                           echo ""
                           echo "     ERROR: Individual file for XNAT archiving missing: ${RunAcceptanceTestDir}/${XNAT_SESSION_LABEL_HOST}_${UnitTest}_${SubjectSessionTimeStamp}_${Status}.txt "
                       fi
                else
                       if [ -f ${StudyFolder}/sessions/${CASE}/${UnitTestData} ]; then
                           echo "     ${UnitTest} PASS: ${StudyFolder}/sessions/${CASE}/${UnitTestData}"
                           echo "  ${UnitTest} PASS: ${StudyFolder}/sessions/${CASE}/${UnitTestData}" >> ${RunAcceptanceTestOut}
                       else 
                           echo "     ${UnitTest} FAIL: ${StudyFolder}/sessions/${CASE}/${UnitTestData}"
                           echo "  ${UnitTest} FAIL: ${StudyFolder}/sessions/${CASE}/${UnitTestData}" >> ${RunAcceptanceTestOut}
                       fi
                fi
                
                ## -- Get QC data from XNAT
                if [[ ! -z ${XNATgetQC} ]] && [[ ${UnitTest} == "hcp_pre_freesurfer" ||  ${UnitTest} == "hcp_freesurfer" ]]; then
                    unset UnitTestQCFolders
                    echo ""
                    echo "     Note: Requested XNAT QC for ${UnitTest} but this is step does not generate QC images."
                    echo ""
                fi
                if [[ ! -z ${XNATgetQC} ]] && [[ ! -z ${UnitTestQCFolders} ]]; then
                    echo ""
                    echo "     Requested XNAT QC ${XNATgetQC} for ${UnitTest}"
                    echo ""
                    if [[ ${XNATgetQC} == "png" ]] || [[ ${XNATgetQC} == "image" ]] || [[ ${XNATgetQC} == "pngs" ]] || [[ ${XNATgetQC} == "images" ]]; then
                        FileTypes="png"
                    fi
                    if [[ ${XNATgetQC} == "scene" ]] || [[ ${XNATgetQC} == "scenes" ]]; then
                        FileTypes="zip"
                    fi
                    if [[ ${XNATgetQC} == "all" ]]; then
                        FileTypes="png zip"
                    fi
                    if [[ ${UnitTest} == "hcp_fmri_volume" ]] || [[ ${UnitTest} == "hcp_fmri_surface" ]]; then
                        FileTypes="${FileTypes} TSNR"
                    fi
                    if [[ ${XNATgetQC} == "snr" ]] || [[ ${XNATgetQC} == "tsnr" ]] || [[ ${XNATgetQC} == "SNR" ]] || [[ ${XNATgetQC} == "TSNR" ]]; then
                        FileTypes="TSNR"
                    fi
                    for UnitTestQCFolder in ${UnitTestQCFolders}; do
                        mkdir -p ${RunAcceptanceTestDir}/QC/${UnitTestQCFolder} > /dev/null 2>&1
                        cd ${RunAcceptanceTestDir}/QC/${UnitTestQCFolder}
                        echo "      ---> Working on QC folder $UnitTestQCFolder | Requested QC file types: ${FileTypes}"
                        ceho "          Running: curl -k -b "JSESSIONID=$JSESSION" -s -m 30 -X GET ${XNAT_HOST_NAME}/data/experiments/${XNAT_ACCSESSION_ID}/resources/QC/files/${UnitTestQCFolder}/?format=csv > ${RunAcceptanceTestDir}/QC/${UnitTestQCFolder}/${XNAT_SESSION_LABEL_HOST}_${UnitTest}_${SubjectSessionTimeStamp}_QC_${UnitTestQCFolder}.csv"
                        curl -k -b "JSESSIONID=$JSESSION" -s -m 30 -X GET ${XNAT_HOST_NAME}/data/experiments/${XNAT_ACCSESSION_ID}/resources/QC/files/${UnitTestQCFolder}/?format=csv > ${RunAcceptanceTestDir}/QC/${UnitTestQCFolder}/${XNAT_SESSION_LABEL_HOST}_${UnitTest}_${SubjectSessionTimeStamp}_QC_${UnitTestQCFolder}.csv
                        unset QCFile QCFiles FileType
                        for FileType in ${FileTypes}; do
                            QCFiles=`cat ${XNAT_SESSION_LABEL_HOST}_${UnitTest}_${SubjectSessionTimeStamp}_QC_${UnitTestQCFolder}.csv | sed -e '1,1d' | awk  -F, '{print $1}' | grep "${FileType}"`
                            echo ""
                            for QCFile in ${QCFiles}; do
                                echo "          QC for ${UnitTest} found on XNAT: ${XNAT_HOST_NAME}/data/experiments/${XNAT_ACCSESSION_ID}/resources/QC/files/${UnitTestQCFolder}/${QCFile}"
                                if [[ -f ${RunAcceptanceTestDir}/QC/${UnitTestQCFolder}/${QCFile} ]]; then
                                    echo "          QC for ${UnitTest} found locally: ${RunAcceptanceTestDir}/QC/${UnitTestQCFolder}/${QCFile}"
                                else
                                    curl -k -b "JSESSIONID=$JSESSION" -s -m 30 -X GET "${XNAT_HOST_NAME}/data/experiments/${XNAT_ACCSESSION_ID}/resources/QC/files/${UnitTestQCFolder}/${QCFile}" > ${QCFile}
                                    if [[ -f ${RunAcceptanceTestDir}/QC/${UnitTestQCFolder}/${QCFile} ]]; then
                                        echo "          Results found: ${RunAcceptanceTestDir}/QC/${UnitTestQCFolder}/${QCFile}"
                                    else
                                        echo "          ERROR - results not found: ${RunAcceptanceTestDir}/QC/${UnitTestQCFolder}/${QCFile}"
                                    fi
                                fi
                            done
                            echo ""
                        done
                    done
                    rm ${RunAcceptanceTestDir}/QC/${UnitTestQCFolder}/*.csv > /dev/null 2>&1
                fi
            }
           
            ################## ACCEPTANCE TEST FOR EACH UNIT ###################
            #
            # -- SUPPORTED:
            #    UnitTests="hcp_pre_freesurfer hcp_freesurfer hcp_post_freesurfer hcp_fmri_volume hcp_fmri_surface hcpd dwi_dtifit dwi_bedpostx_gpu preprocess_bold compute_bold_fc_seed compute_bold_fc_gbc" 
            #
            # -- Needs to be added:
            #    UnitTests="hcpd dwi_legacy_gpu eddy_qc dwi_dtifit dwi_bedpostx_gpu dwi_pre_tractography dwi_parcellate dwi_seed_tractography_dense create_bold_brain_masks compute_bold_stats create_stats_report extract_nuisance_signal preprocess_bold preprocess_conc general_plot_bold_timeseries parcellate_bold compute_bold_fc_seed compute_bold_fc_gbc"
            #
            # -- FILES FOR EACH UNIT
            #
            #    hcp_pre_freesurfer:                    subjects/<session id>/hcp/<session id>/T1w/T1w_acpc_dc_restore_brain.nii.gz
            #    hcp_freesurfer: FS Version 6.0:        subjects/<session id>/hcp/<session id>/T1w/<session id>/label/BA_exvivo.thresh.ctab
            #    hcp_freesurfer: FS Version 5.3-HCP:    subjects/<session id>/hcp/<session id>/T1w/<session id>/label/rh.entorhinal_exvivo.label
            #    hcp_post_freesurfer:                   subjects/<session id>/hcp/<session id>/T1w/ribbon.nii.gz
            #    hcp_fmri_volume:                       subjects/<session id>/hcp/<session id>/MNINonLinear/Results/<bold code>/<bold code>.nii.gz
            #    hcp_fmri_surface:                      subjects/<session id>/hcp/<session id>/MNINonLinear/Results/<bold code>/<bold code>_Atlas.dtseries.nii
            #    hcp_diffusion:                         subjects/<session id>/hcp/<session id>/T1w/Diffusion/data.nii.gz
            #    hcpDTIFix:                  subjects/<session id>/hcp/<session id>/T1w/Diffusion/dti_FA.nii.gz
            #    hcpBedpostx:                subjects/<session id>/hcp/<session id>/T1w/hcpBedpostx/mean_fsumsamples.nii.gz
            #
            # -- To be tested for BOLD processing: 
            #
            #    DenoiseData="Atlas_s_hpss_res-mVWMWB_lpss.dtseries.nii"
            #    FCData="Atlas_s_hpss_res-mVWMWB_lpss_BOLD-CAB-NP-v1.0_r.pconn.nii"
            #    BOLDS="1"
            #
            ####################################################################
            
            ## -- Loop over units
            for UnitTest in ${UnitTests}; do
                
                if [ ! -z "${SupportedAcceptanceTestSteps##*${UnitTest}*}" ]; then
                    echo ""
                    echo "  -- ${UnitTest} is not supported. Skipping step for $CASE."
                    echo ""
                else
                    echo ""
                    echo "  -- ${UnitTest} is supported. Proceeding..."
                    echo ""
                    echo "  -- Checking ${UnitTest} for $CASE " >> ${RunAcceptanceTestOut}
                    ## -- Check units that may have multiple bolds
                    if [[ ${UnitTest} == "hcp_fmri_volume" ]] || [[ ${UnitTest} == "hcp_fmri_surface" ]] || [[ ${UnitTest} == "preprocess_bold" ]] || [[ ${UnitTest} == "compute_bold_fc_seed" ]] || [[ ${UnitTest} == "compute_bold_fc_gbc" ]] || [[ ${UnitTest} == "bold_images" ]]; then
                        echo ""
                        if [[ ! -z ${BOLDS} ]]; then
                            for BOLD in ${BOLDS}; do
                                if   [[ ${UnitTest} == "hcp_fmri_volume" ]];           then UnitTestData="hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}.nii.gz"; UnitTestQCFolders="BOLD"; UnitTestDataCheck
                                elif [[ ${UnitTest} == "hcp_fmri_surface" ]];           then UnitTestData="hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_Atlas.dtseries.nii"; UnitTestQCFolders="BOLD"; UnitTestDataCheck
                                elif [[ ${UnitTest} == "preprocess_bold" ]]; then UnitTestData="hcp/${CASE}/images/functional/bold${BOLD}_${DenoiseData}"; UnitTestQCFolders="movement"; UnitTestDataCheck
                                elif [[ ${UnitTest} == "compute_bold_fc_seed" ]] || [[ ${UnitTest} == "compute_bold_fc_gbc" ]];      then UnitTestData="hcp/${CASE}/images/functional/bold${BOLD}_${FCData}"; UnitTestQCFolders=""; UnitTestDataCheck
                                elif [[ ${UnitTest} == "bold_images" ]]; then
                                    for BOLDImage in ${BOLDImages}; do
                                        BOLDImage=`echo ${BOLDImage} | sed "s/{N}/${BOLD}/g"`
                                        UnitTestData="images/functional/${BOLDImage}"; UnitTestQCFolders=""; UnitTestDataCheck
                                    done
                                fi
                            done
                        else
                             echo "  -- Requested ${UnitTest} for ${CASE} but no BOLDS specified." >> ${RunAcceptanceTestOut}
                             echo "" >> ${RunAcceptanceTestOut}
                        fi
                    elif [[ ${UnitTest} == "hcp_pre_freesurfer" ]];    then UnitTestData="hcp/${CASE}/T1w/T1w_acpc_dc_restore_brain.nii.gz"; UnitTestDataCheck
                    elif [[ ${UnitTest} == "hcp_freesurfer" ]];    then UnitTestData="hcp/${CASE}/T1w/${CASE}/label/rh.entorhinal_exvivo.label"; UnitTestDataCheck
                    elif [[ ${UnitTest} == "hcp_post_freesurfer" ]];    then UnitTestData="hcp/${CASE}/MNINonLinear/ribbon.nii.gz"; UnitTestQCFolders="T1w T2w myelin"; UnitTestDataCheck
                    elif [[ ${UnitTest} == "hcpd" ]]; then UnitTestData="hcp/${CASE}/T1w/Diffusion/data.nii.gz"; UnitTestDataCheck
                    elif [[ ${UnitTest} == "dwi_dtifit" ]]; then UnitTestData="hcp/${CASE}/T1w/Diffusion/dti_FA.nii.gz"; UnitTestDataCheck
                    elif [[ ${UnitTest} == "dwi_bedpostx_gpu" ]]; then UnitTestData="hcp/${CASE}/T1w/Diffusion.bedpostX/mean_fsumsamples.nii.gz"; UnitTestDataCheck
                    fi
                    
                    if [[ ${RUN_TYPE} == "xnat" ]]; then 
                        if [[ ${XNATArchiveCommit} == "session" ]] || [[ ${XNATArchiveCommit} == "all" ]]; then
                            echo ""
                            echo "---> Setting recursive r+w+x permissions on ${RunAcceptanceTestOut}"
                            echo ""
                            chmod -R 777 ${RunAcceptanceTestDir} &> /dev/null
                            cd ${RunAcceptanceTestDir}
                            unset XNATUploadFile
                            XNATUploadFile="${XNAT_SESSION_LABEL_HOST}_${UnitTest}_${SubjectSessionTimeStamp}_${Status}.txt"
                            echo ""
                            echo "---> Uploading ${XNATUploadFile} to ${XNAT_HOST_NAME} "
                            echo "     curl -k -b "JSESSIONID=$JSESSION" -m 40 -X POST "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_ACCSESSION_ID}/resources/QUNEX_ACCEPT/files/${XNATUploadFile}?extract=true&overwrite=true" -F file=@${RunAcceptanceTestDir}/${XNATUploadFile} "
                            echo ""
                            curl -k -b "JSESSIONID=$JSESSION" -m 40 -X POST "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_ACCSESSION_ID}/resources/QUNEX_ACCEPT/files/${XNATUploadFile}?extract=true&overwrite=true" -F file=@${RunAcceptanceTestDir}/${XNATUploadFile} &> /dev/null
                            echo ""
                            if ( curl -k -b "JSESSIONID=$JSESSION" -o/dev/null -sfI ${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_SESSION_LABEL_HOST}/resources/QUNEX_ACCEPT/files/${XNATUploadFile} ); then 
                                echo " -- ${XNATUploadFile} uploaded to ${XNAT_HOST_NAME}"
                            else 
                                echo " -- ${XNATUploadFile} not found on ${XNAT_HOST_NAME} Something went wrong with curl."
                            fi
                        fi
                    fi
                fi
            done

    }

    ## -- Loop over subjects    
    if [[ -z ${SESSION_LABELS} ]] && [[ ${RUN_TYPE} != "xnat" ]] ; then
        SESSION_LABELS="_"
    fi
    
    if [[ ${RUN_TYPE} == "xnat" ]]; then
        SESSION_LABELS="${XNAT_SESSION_LABELS}"
    fi
    
    for SESSION_LABEL in ${SESSION_LABELS}; do
    
        if [[ ${RUN_TYPE} == "xnat" ]]; then
            XNAT_SESSION_LABEL="${SESSION_LABEL}"
            ## -- Setup relevant acceptance paths for XNAT run
            unset AcceptDirTimeStamp
            AcceptDirTimeStamp=`date +%Y-%m-%d_%H.%M.%S.%6N`
            RunAcceptanceTestOut="${RunAcceptanceTestDir}/QuNexAcceptanceTest_XNAT_${XNAT_SESSION_LABEL}_${AcceptDirTimeStamp}.txt"
            ## -- Open JSESSION to the XNAT Site
            JSESSION=$(curl -k -X POST -u "${XNAT_CREDENTIALS}" "${XNAT_HOST_NAME}/data/JSESSION" )
            echo ""
            echo "-- JSESSION created: ${JSESSION}"; echo ""
            echo "" >> ${RunAcceptanceTestOut}
            echo "  QuNex Acceptance Test Report for XNAT Run" >> ${RunAcceptanceTestOut}
            echo "  -----------------------------------------" >> ${RunAcceptanceTestOut}
            echo "" >> ${RunAcceptanceTestOut}
            echo "   QuNex Acceptance test steps:    ${AcceptanceTestSteps}" >> ${RunAcceptanceTestOut}
            echo "   XNAT Hostname:                  ${XNAT_HOST_NAME}" >> ${RunAcceptanceTestOut}
            echo "   XNAT Project ID:                ${XNAT_PROJECT_ID}" >> ${RunAcceptanceTestOut}
            echo "   XNAT Session Label:             ${XNAT_SESSION_LABEL}" >> ${RunAcceptanceTestOut}
            echo "" >> ${RunAcceptanceTestOut}
            echo "  ---------------------------" >> ${RunAcceptanceTestOut}
            echo "" >> ${RunAcceptanceTestOut}
        else
            ## -- Setup relevant acceptance paths for non-XNAT run
            unset AcceptDirTimeStamp
            AcceptDirTimeStamp=`date +%Y-%m-%d_%H.%M.%S.%6N`
            RunAcceptanceTestOut="${RunAcceptanceTestDir}/QuNexAcceptanceTest_${AcceptDirTimeStamp}.txt"
            echo "" >> ${RunAcceptanceTestOut}
            echo "  QuNex Acceptance Test Report for Local Run" >> ${RunAcceptanceTestOut}
            echo "  ------------------------------------------" >> ${RunAcceptanceTestOut}
            echo "" >> ${RunAcceptanceTestOut}
            echo "   QuNex Study folder:              ${StudyFolder}" >> ${RunAcceptanceTestOut}
            echo "   QuNex Acceptance test steps:     ${AcceptanceTestSteps}" >> ${RunAcceptanceTestOut}
            echo "" >> ${RunAcceptanceTestOut}
            echo "  ---------------------------" >> ${RunAcceptanceTestOut}
            echo "" >> ${RunAcceptanceTestOut}
        fi
    
        ## -- Execute core function over cases
        for CASE in ${CASES}; do UnitTestingFunction; done
        
        if [[ ${RUN_TYPE} == "xnat" ]]; then
            if [[ ${XNATArchiveCommit} == "all" ]] || [[ ${XNATArchiveCommit} == "project" ]]; then
                 chmod -R 777 ${RunAcceptanceTestDir} &> /dev/null
                 cd ${RunAcceptanceTestDir}
                 RunAcceptanceTestOutFile=$(basename $RunAcceptanceTestOut)
                 echo ""
                 echo "---> Uploading ${RunAcceptanceTestOut} to ${XNAT_HOST_NAME} "
                 echo "     curl -k -b "JSESSIONID=$JSESSION" -m 60 -X POST "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/QUNEX_ACCEPT/files/${RunAcceptanceTestOutFile}?extract=true&overwrite=true" -F file=@${RunAcceptanceTestOut} "
                 echo ""
                 curl -k -b "JSESSIONID=$JSESSION" -m 60 -X POST "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/QUNEX_ACCEPT/files/${RunAcceptanceTestOutFile}?extract=true&overwrite=true" -F file=@${RunAcceptanceTestOut} &> /dev/null
                 echo ""
                 if ( curl -k -b "JSESSIONID=$JSESSION" -m 20 -o/dev/null -sfI ${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/QUNEX_ACCEPT/files/${RunAcceptanceTestOutFile} ); then 
                     echo "-- Successfully uploaded ${RunAcceptanceTestOutFile} to ${XNAT_HOST_NAME} under project ${XNAT_PROJECT_ID} as a resource:"
                     echo "                ${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/QUNEX_ACCEPT/files/${RunAcceptanceTestOutFile}"
                 else 
                     echo "-- ${RunAcceptanceTestOutFile} not found on ${XNAT_HOST_NAME} Something went wrong with curl."
                 fi
            fi
        fi
        
        ## -- Close JSESSION
        if [[ ${RUN_TYPE} == "xnat" ]]; then
            curl -k -X DELETE -b "JSESSIONID=${JSESSION}" "${XNAT_HOST_NAME}/data/JSESSION"
            echo ""
            echo "-- JSESSION closed: ${JSESSION}"
        fi
        
    done

    echo ""
    ceho "---> Attempted acceptance testing for ${UnitTests} finished."
    echo ""
     if [ -f ${RunAcceptanceTestOut} ]; then
        echo ""
        ceho "---> Final acceptance testing results are stored locally:" 
        ceho "    ${RunAcceptanceTestOut}"
        echo ""
    else 
        echo ""
        echo " ERROR: None of the requested acceptance tests passed: ${UnitTests}"
        echo "        Final results missing:"
        echo "        ${RunAcceptanceTestOut}."
        echo ""
        echo ""
    fi

}

################################ END OF WORK ###################################


# ------------------------------------------------------------------------------
# -- Execute overall function and read arguments
# ------------------------------------------------------------------------------

main $@

# -- Reset sensitive XNAT variables
unset XNAT_USER_NAME XNAT_PASSWORD XNAT_CREDENTIALS XNAT_HOST_NAME &> /dev/null
