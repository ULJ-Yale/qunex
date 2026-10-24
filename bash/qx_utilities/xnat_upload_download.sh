#!/bin/bash

# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
 echo ""
 echo "XNATUploadDownload"
 echo ""
 echo "This function implements syncing to a specified XNAT server via the CURL REST "
 echo "API."
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "--xnatcredentialfile   Specify XNAT credential file name. "
 echo "                       Default: ${HOME}/.xnat "
 echo ""
 echo "                       This file stores the username and password for the XNAT "
 echo "                       site. Permissions of this file need to be set to 400. If "
 echo "                       this file does not exist the script will prompt you to "
 echo "                       generate one using default name. If user provided a file "
 echo "                       name but it is not found, this name will be used to "
 echo "                       generate new credentials. User needs to provide this "
 echo "                       specific credential file for next run, as script by "
 echo "                       default expects ${HOME}/.xnat"
 echo "--xnatuser             Specify XNAT username required if credential file is not "
 echo "                       found"
 echo "--xnatpass             Specify XNAT password required if credential file is not "
 echo "                       found"
 echo "--runtype              Select --runtype='upload' or --runtype='download' "
 echo ""
 echo "Local system variables if using QuNex hierarchy:"
 echo ""
 echo "--studyfolder          Path to the study folder. The sessions are in its "
 echo "                       sessions folder, unless --sessionsfolder names another "
 echo "                       one."
 echo "--sessionsfolder       Path to the folder with the sessions. Default: "
 echo "                       <studyfolder>/sessions. Set it only when the sessions "
 echo "                       are not in the sessions folder of the study. One of "
 echo "                       --studyfolder and --sessionsfolder has to be given for "
 echo "                       an upload without --dicompath and for a download "
 echo "                       without --downloadpath."
 echo "--sessions             List of sessions to run that are study-specific and "
 echo "                       correspond to XNAT database session IDs"
 echo "--downloadpath         Specify path to download. Default: "
 echo "                       <sessionsfolder>/inbox or, with --bidsformat='yes', "
 echo "                       <sessionsfolder>/inbox/BIDS"
 echo "--bidsformat           Specify if XNAT data is in BIDS format (yes/no). Default "
 echo "                       is [no]."
 echo ""
 echo "                       If --bidsformat='yes' and XNAT download run is requested "
 echo "                       then BIDS data is by default placed in "
 echo "                       <sessionsfolder>/inbox/BIDS"
 echo "--logfolder            The folder the run logs in. A download saves the XNAT "
 echo "                       project information it fetches there, in "
 echo "                       XNATInfo_<timestamp>. Default: the run's log folder, "
 echo "                       decided as for every QuNex run: "
 echo "                       <studyfolder>/logs/<timestamp>_xnat_upload_download "
 echo "                       (<studyfolder>/processing/logs with "
 echo "                       --logfolder=legacy or the legacy layout), or, without "
 echo "                       a study folder, "
 echo "                       ~/qunex_logs/<timestamp>_xnat_upload_download or "
 echo "                       where the outside_study logging setting says. A "
 echo "                       relative path is taken from the study folder, else "
 echo "                       from the current folder."
 echo ""
 echo "Local system variables if using generic DICOM location for a single XNAT upload:"
 echo ""
 echo "--dicompath            Path to folder where the DICOMs reside"
 echo ""
 echo "XNAT HOST VARIABLES"
 echo "-------------------"
 echo ""
 echo "--xnatprojectid        Specify the XNAT site project id. This is the Project ID "
 echo "                       in XNAT and not the Project Title."
 echo ""
 echo "                       This project should be created on the XNAT Site prior to "
 echo "                       upload. If it is not found on the XNAT Site or not "
 echo "                       provided then the data will land into the prearchive and "
 echo "                       be left unassigned to a project."
 echo "                       Please check upon completion and specify assignment "
 echo "                       manually."
 echo "--xnathost             Specify the XNAT site hostname URL to push data to."
 echo ""
 echo ""
 echo "XNAT SUBJECT AND SESSION INPUTS"
 echo "-------------------------------"
 echo ""
 echo "--xnatsubjectlabels     Label for subject within a project for the XNAT "
 echo "                        database. Default assumes it matches --sessions."
 echo ""
 echo "                        If your XNAT database subject label is distinct from "
 echo "                        your local server subject id then please supply this "
 echo "                        flag."
 echo ""
 echo "                        Use if your XNAT database has a different set of subject "
 echo "                        ids."
 echo "--xnatsessionlabel      Label for session within XNAT project. Note: may be "
 echo "                        general across multiple subjects (e.g. rest). Required."
 echo "--niftiupload           Specify <yes> or <no> for NIFTI upload. Default is [no]."
 echo "--overwrite             Specify <yes> or <no> for cleanup of prior upload on "
 echo "                        the host server. Default is [yes]."
 echo "--resetcredentials      Specify <yes> if you wish to reset your XNAT site user "
 echo "                        and password. Default is [no]"
 echo ""
 echo "USE"
 echo "==="
 echo ""
 echo "Note: To invoke this function you need a credential file in your home folder or "
 echo "provide one using --xnatcredentialfile parameter or --xnatuser and --xnatpass "
 echo "parameters."
 echo ""
 echo "EXAMPLE USE"
 echo "==========="
 echo ""
 echo "Example for XNAT upload::"
 echo ""
 echo " xnat_upload_download.sh \ "
 echo " --runtype='upload' \ "
 echo " --studyfolder='<path_to_study_folder>' \ "
 echo " --sessions='<session_label>' \ "
 echo " --xnatcredentialfile='.somefilename' \ "
 echo " --xnatsessionlabel='<session_label>' \ "
 echo " --xnatprojectid='<xnat_project>' \ "
 echo " --xnathost='<host_url>' "
 echo ""
 echo "Example for XNAT download::"
 echo ""
 echo " xnat_upload_download.sh \ "
 echo " --runtype='download' \ "
 echo " --studyfolder='<path_to_study_folder>' \ "
 echo " --sessions='<xnat_subject_labels>' \ "
 echo " --downloadpath='<optional_download_path>' \ "
 echo " --xnatcredentialfile='.somefilename' \ "
 echo " --xnatsessionlabel='<session_label>' \ "
 echo " --xnatprojectid='<xnat_project>' \ "
 echo " --xnathost='<host_url>' \ "
 echo " --bidsformat='yes' "
 echo ""
}

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
return 1
}

if opts_CheckForHelpRequest "$@"; then
    usage
    exit 0
fi

scriptName=$(basename "${0}")
RunTimeStamp=`date +%Y-%m-%d_%H.%M.%S.%6N`

# the folder this run logs in, decided by the rule every QuNex run is placed
# by, as bin/qunex.sh decides it: gmri log_folder, from the folders and the
# --logfolder the run was given. Prints the folder and exits on failure
decide_log_folder() {
    local gmri decided status
    local -a run_gmri
    gmri="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null && pwd)/../../python/qx_utilities/gmri"
    if [ ! -x "${gmri}" ]; then
        gmri=$(command -v gmri)
    fi
    if [ -z "${gmri}" ]; then
        echo "ERROR: gmri not found, so the log folder of ${scriptName} can not be decided."
        echo "       Run it from a QuNex installation, or set up the QuNex environment."
        exit 1
    fi
    # gmri is python started as `python`; where there is only python3, it runs with that
    run_gmri=("${gmri}")
    if ! command -v python > /dev/null 2>&1 && head -n 1 "${gmri}" | grep -q python; then
        if command -v python3 > /dev/null 2>&1; then
            run_gmri=("$(command -v python3)" "${gmri}")
        else
            echo "ERROR: python not found, so the log folder of ${scriptName} can not be decided."
            echo "       A download runs QuNex (gmri): put python or python3 on PATH, or set up the QuNex environment."
            exit 1
        fi
    fi
    decided=$("${run_gmri[@]}" log_folder --command=xnat_upload_download --timestamp="${RunTimeStamp}" \
            ${StatedStudyFolder:+--studyfolder="${StatedStudyFolder}"} \
            ${StatedSessionsFolder:+--sessionsfolder="${StatedSessionsFolder}"} \
            ${LogFolder:+--logfolder="${LogFolder}"})
    status=$?
    # 126/127: the interpreter gmri names could not be run, which is not the inputs' fault
    if [ ${status} -eq 126 ] || [ ${status} -eq 127 ]; then
        echo "${decided}"
        echo "ERROR: QuNex (gmri) could not be run, so the log folder of ${scriptName} can not be decided."
        echo "       Put python on PATH, or set up the QuNex environment."
        exit 1
    elif [ ${status} -ne 0 ]; then
        echo "${decided}"
        echo "ERROR: Could not decide where the logs of ${scriptName} go. Check your inputs."
        exit 1
    fi
    # the folder is the last line, after anything gmri warns about
    LogFolder=$(echo "${decided}" | tail -n 1)
    if ! mkdir -p "${LogFolder}"; then
        echo "ERROR: Could not create the log folder ${LogFolder}. Check that it can be written to."
        exit 1
    fi
}

# -- Initialize global output variables
unset CASES
unset StudyFolder
unset SessionsFolder
unset XNAT_HOST_NAME
unset XNAT_CREDENTIALS
unset XNAT_CREDENTIAL_FILE
unset XNAT_USER_NAME
unset XNAT_PASSWORD
unset XNAT_PROJECT_ID
unset XNAT_SUBJECT_LABELS
unset XNAT_SESSION_LABEL
unset RUN_TYPE
unset NIFTIUPLOAD
unset OVERWRITE
unset ResetCredentials
unset DICOMPath
unset XNATUploadError
unset XNATErrorsUpload
unset XNATSuccessUpload
unset BIDSFormat
unset DownloadPath
unset LogFolder

# -- Parse arguments
StudyFolder=`opts_GetOpt "--studyfolder" $@`
SessionsFolder=`opts_GetOpt "--sessionsfolder" $@`
ResetCredentials=`opts_GetOpt "--resetcredentials" $@`
CASES=`opts_GetOpt "--sessions" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'`
XNAT_CREDENTIAL_FILE=`opts_GetOpt "--xnatcredentialfile" $@`
XNAT_USER_NAME=`opts_GetOpt "--xnatuser" "$@"`
XNAT_PASSWORD=`opts_GetOpt "--xnatpass" "$@"`
XNAT_HOST_NAME=`opts_GetOpt "--xnathost" $@`
XNAT_PROJECT_ID=`opts_GetOpt "--xnatprojectid" $@`
XNAT_SUBJECT_LABELS=`opts_GetOpt "--xnatsubjectlabels" "$@" | sed 's/,/ /g;s/|/ /g'`; XNAT_SUBJECT_LABELS=`echo "$XNAT_SUBJECT_LABELS" | sed 's/,/ /g;s/|/ /g'`
XNAT_SESSION_LABEL=`opts_GetOpt "--xnatsessionlabel" "$@"`
XNAT_ACCSESSION_ID=`opts_GetOpt "--xnataccsessionid" $@`
XNAT_SUBJECT_ID=`opts_GetOpt "--xnatsubjectid" $@`
NIFTIUPLOAD=`opts_GetOpt "--niftiupload" $@`
OVERWRITE=`opts_GetOpt "--overwrite" $@`
DICOMPath=`opts_GetOpt "--dicompath" $@`
RUN_TYPE=`opts_GetOpt "--runtype" $@`
BIDSFormat=`opts_GetOpt "--bidsformat" $@`
DownloadPath=`opts_GetOpt "--downloadpath" $@`
LogFolder=`opts_GetOpt "--logfolder" "$@"`

# the run's log folder is decided from the folders as they were given
StatedStudyFolder="${StudyFolder}"
StatedSessionsFolder="${SessionsFolder}"

# the sessions are in the sessions folder of the study, unless --sessionsfolder
# names another one
if [ -z "${SessionsFolder}" ] && [ -n "${StudyFolder}" ]; then
    SessionsFolder="${StudyFolder}/sessions"
fi
# an upload changes into the folders it reads, so the existing ones are made
# absolute. The study, when not given, is the folder the sessions folder is in
if [ -d "${SessionsFolder}" ]; then
    SessionsFolder=$(cd "${SessionsFolder}" > /dev/null && pwd)
fi
if [ -d "${DICOMPath}" ]; then
    DICOMPath=$(cd "${DICOMPath}" > /dev/null && pwd)
fi
if [ -z "${StudyFolder}" ] && [ -n "${SessionsFolder}" ]; then
    StudyFolder=$(dirname "${SessionsFolder}")
fi

## -- Check run type
if [[ -z ${RUN_TYPE} ]]; then
    usage
    echo "ERROR: --runtype flag not specified. Specify --runtype='upload' or --runtype='download'."
    echo ""
    exit 1
fi
## -- Check XNAT Host variable
if [[ -z ${XNAT_HOST_NAME} ]]; then
    usage
    echo "ERROR: --xnathost flag not specified"
    echo ""
    exit 1
fi
## -- Check for session variables
if [[ -z ${CASES} ]] && [[ -z ${XNAT_SUBJECT_LABELS} ]]; then
    usage
    echo "ERROR: --sessions flag and --xnatsubjectlabels flag not specified. No cases to work with. Please specify either."
    echo ""
    exit 1
fi
## -- Check XNAT_SESSION_LABEL
if [[ -z ${XNAT_SESSION_LABEL} ]]; then
    XNAT_SESSION_LABEL=""
    usage
    echo "Note: --xnatsessionlabel flag not specified. Assuming that the experiment / session label matches XNAT subject label."
    echo ""
fi
## -- Check CASES variable is not set
if [[ -z ${CASES} ]]; then
    CASES="$XNAT_SUBJECT_LABELS"
    echo ""
    echo "Note: --sessions flag omitted. Assuming specified --xnatsubjectlabels names match the sessions folders on the file system."
    echo ""
fi
## -- Check XNAT_SUBJECT_LABELS
if [[ -z ${XNAT_SUBJECT_LABELS} ]]; then
    XNAT_SUBJECT_LABELS="$CASES"
    echo ""
    echo "Note: --xnatsubjectlabels flag omitted. Assuming specified --sessions names match the subject labels in XNAT."
    echo ""
fi

## -- Checks if running download
if [[ ${RUN_TYPE} == "download" ]]; then
    ## -- Check XNAT Project variable
    if [ -z ${XNAT_PROJECT_ID} ]; then
        usage
        echo "ERROR: --xnatprojectid flag, which defines the XNAT Site Project is not specified."
        echo ""
        exit 1
    fi
    ## -- Check BIDS format
    if [[ -z ${BIDSFormat} ]]; then
        BIDSFormat="no"
        echo "Note: --bidsformat flag not specified. Setting to --bidsformat=$BIDSFormat."
        echo ""
    fi
    # the data goes to the inbox of the sessions folder, unless --downloadpath
    # names another folder
    if [[ -z ${DownloadPath} ]]; then
        if [ -z "${SessionsFolder}" ]; then
            usage
            echo "ERROR: Neither --studyfolder nor --sessionsfolder specified, and no --downloadpath given."
            echo ""
            exit 1
        fi
        if [[ ${BIDSFormat} == "yes" ]]; then
            DownloadPath="${SessionsFolder}/inbox/BIDS"
        else
            DownloadPath="${SessionsFolder}/inbox"
        fi
    fi
    # the XNAT project information the download fetches is kept in the run's
    # log folder
    decide_log_folder
fi

## -- Checks if running upload
if [[ ${RUN_TYPE} == "upload" ]]; then
    ## -- Check XNAT Project variable
    if [ -z ${XNAT_PROJECT_ID} ]; then
        echo ""
        echo "Note: --xnatprojectid flag, which defines the XNAT Site Project is not specified."
        echo "      Data will be pushed in the XNAT Site prearchive and left unassigned. Please check upon completion and specify assignment manually."
        echo ""
    fi
    ## -- Check if single upload requested
    if [ -z ${DICOMPath} ]; then
        ## -- Check session folder if DICOMPath is not set
        if [ -z "${SessionsFolder}" ]; then
            usage
            echo "ERROR: Neither --studyfolder nor --sessionsfolder specified, and no --dicompath given."
            echo ""
            exit 1
        fi
    else 
        ## -- Generic DICOM path is set outside of QuNex hierarchy
        echo "Note: --dicompath=${DICOMPath} specified, which assumes DICOM location for a single XNAT upload."; echo ""
        ## -- Check XNAT session label if DICOMPath is set
        if [[ -z ${XNAT_SUBJECT_LABELS} ]]; then
            XNAT_SUBJECT_LABELS=""
            echo ""
            echo "Note: --xnatsubjectlabels flag omitted. Data will be pushed in the XNAT Site prearchive and left unassigned. Please check upon completion and specify assignment manually."
            echo "    If you wish to upload a new session for this subject id please supply this flag."
            echo ""
        fi
        ## -- Check XNAT experiment label if DICOMPath is set
        if [[ -z ${XNAT_SESSION_LABEL} ]]; then
            XNAT_SESSION_LABEL=""
            echo ""
            echo "Note: --xnatexperiment flag omitted. Data will be pushed in the XNAT Site prearchive and left unassigned. Please check upon completion and specify assignment manually."
            echo "    If you wish to upload a new session for this subject id please supply this flag."
            echo ""
        fi
    fi
fi

## -- Check if NIFTI upload is requested
if [[ -z ${NIFTIUPLOAD} ]]; then NIFTIUPLOAD="no"; fi
## -- Check if overwrite is requested
if [[ -z ${OVERWRITE} ]]; then OVERWRITE="yes"; fi
## -- Set reseting credentials to no if not provided 
if [[ -z ${ResetCredentials} ]]; then ResetCredentials="no"; fi
## -- Set  credentials file name to default if not provided
if [[ -z ${XNAT_CREDENTIAL_FILE} ]]; then XNAT_CREDENTIAL_FILE=".xnat"; fi

## -- Reset credentials
if [[ "${ResetCredentials}" == "yes" ]]; then
    echo ""
    echo " -- Reseting XNAT credentials in ${HOME}/${XNAT_CREDENTIAL_FILE} "
    echo ""
    rm -f ${HOME}/${XNAT_CREDENTIAL_FILE} &> /dev/null
    echo ""
fi
## -- Check for valid xNAT credential file
if [ -f ${HOME}/${XNAT_CREDENTIAL_FILE} ]; then
    echo ""
    echo " -- XNAT credentials in ${HOME}/${XNAT_CREDENTIAL_FILE} found. Performing credential checks... "
    echo ""
    XNAT_USER_NAME=`cat ${HOME}/${XNAT_CREDENTIAL_FILE} | cut -d: -f1`
    XNAT_PASSWORD=`cat ${HOME}/${XNAT_CREDENTIAL_FILE} | cut -d: -f2-`
    if [[ ! -z ${XNAT_USER_NAME} ]] && [[ ! -z ${XNAT_PASSWORD} ]]; then
        echo ""
        echo " -- XNAT credentials generated in ${HOME}/${XNAT_CREDENTIAL_FILE} " 
        echo ""
        echo " -- Proceeding with XNAT ${RUN_TYPE}..."
        echo ""
    else
        echo ""
        echo "ERROR: ${HOME}/${XNAT_CREDENTIAL_FILE} does not hold a username and a password."
        echo "       Re-run with --resetcredentials=yes to regenerate it."
        echo ""
        exit 1
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

        # nothing is read without a terminal (e.g. under a scheduler), and an
        # empty credential file would be used as it is by the next run
        if [[ -z ${XNAT_USER_NAME} ]] || [[ -z ${XNAT_PASSWORD} ]]; then
            echo ""
            echo "ERROR: No XNAT username and password given. Use --xnatuser and --xnatpass,"
            echo "       or run interactively to generate ${HOME}/${XNAT_CREDENTIAL_FILE}."
            echo ""
            exit 1
        fi

        echo $XNAT_USER_NAME:$XNAT_PASSWORD >> ${HOME}/${XNAT_CREDENTIAL_FILE}
        chmod 400 ${HOME}/${XNAT_CREDENTIAL_FILE}
        echo ""
        echo " -- XNAT credentials generated in ${HOME}/${XNAT_CREDENTIAL_FILE}"
        echo ""
        echo " -- Proceeding with XNAT ${RUN_TYPE}..."
        echo ""
    fi
fi
  
# -- Report all requested options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    if [[ -z ${DICOMPath} ]]; then
        echo "   Study folder: ${StudyFolder}"
        echo "   Folder with all sessions: ${SessionsFolder}"
        echo "   Sessions to process: ${CASES}"
    else
        echo "   Folder DICOMs : ${DICOMPath}"
    fi
    echo "   XNAT Subject labels (should match --sessions): ${XNAT_SUBJECT_LABELS}"
    echo "   XNAT Session Label: ${XNAT_SESSION_LABEL}"
    echo "   NIFTI upload: ${NIFTIUPLOAD}"
    echo "   OVERWRITE set to: ${OVERWRITE}"
    echo "   Reset XNAT site credentials: ${ResetCredentials}"
    echo "   XNAT Hostname: ${XNAT_HOST_NAME}"
    echo "   XNAT Project ID: ${XNAT_PROJECT_ID}"
    echo "   XNAT Run Type: ${RUN_TYPE}"
    echo "   XNAT BIDS format: ${BIDSFormat}"
    if [[ ${RUN_TYPE} == "download" ]]; then
        echo "   Download path: ${DownloadPath}"
        echo "   Log folder: ${LogFolder}"
    fi
    if [[ ${BIDSFormat} == "yes" ]]; then
        echo "   BIDS format input specified: ${BIDSFormat}"
        echo "   Combined BIDS-formatted session name: ${CASE}"
    else 
        echo "   QuNex Session variable name: ${CASE}" 
    fi
    echo "-- ${scriptName}: Specified Command-Line Options - End --"
    echo ""
    echo "------------------------- Start of work --------------------------------"
echo ""

######################################### DO WORK ##########################################

main() {

############################ START OF DOWNLOAD CODE ############################

if [[ ${RUN_TYPE} == "download" ]]; then

    echo ""
    echo "       ********************************************"
    echo "       ****** Setting up XNAT host download *******"
    echo "       ********************************************"
    echo ""
    
    ## -- Function to run on each session
    XNATDownloadFunction() {
    
            # -- Define XNAT_SUBJECT_ID (i.e. Accession number) and XNAT_SESSION_LABEL (i.e. MR Session lablel) for the specific XNAT_SUBJECT_LABEL (i.e. subject)
            XNAT_SUBJECT_ID=`cat ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${TimeStamp}.csv | grep "${XNAT_SUBJECT_LABEL}" | awk  -F, '{print $1}'`
            XNAT_SUBJECT_LABEL=`cat ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${TimeStamp}.csv | grep "${XNAT_SUBJECT_ID}" | awk  -F, '{print $3}'`
            XNAT_ACCSESSION_ID=`cat ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${TimeStamp}.csv | grep "${XNAT_SUBJECT_LABEL}" | grep "${XNAT_SESSION_LABEL}" | awk  -F, '{print $1}'`
        
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
            if [[ ${BIDSFormat} == "yes" ]]; then
                # -- Setup CASE without the 'MR' prefix in the XNAT_SESSION_LABEL
                #    Eventually deprecate once fixed in XNAT
                CASE="${XNAT_SUBJECT_LABEL}_${XNAT_SESSION_LABEL}"
                CASE=`echo ${CASE} | sed 's|MR||g'`
                echo " -- Note: --bidsformat='yes' " 
                echo "    Combining XNAT_SUBJECT_LABEL and XNAT_SESSION_LABEL into unified BIDS-compliant subject variable for QuNex run: ${CASE}"
                echo ""
            else
                CASE="${XNAT_SUBJECT_LABEL}"
            fi
            
            echo ""
            echo " -- Running:    curl -k -b "JSESSIONID=$JSESSION" -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${DownloadPath}/${CASE}.zip "
            echo ""
            curl -k -b "JSESSIONID=$JSESSION" -m 3600 -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${DownloadPath}/${CASE}.zip
            
            ## -- Run check that data is in the right location
            if [ -f ${DownloadPath}/${CASE}.zip ]; then
                CheckZIP=`zip -T ${DownloadPath}/${CASE}.zip | grep "error"`
                if [[ -z ${CheckZIP} ]]; then
                     echo ""
                     echo " -- XNAT download completed and validated for ${DownloadPath}/${CASE}.zip"
                     echo ""
                     XNATSuccessDownload="$XNATSuccessDownload\n   ---> Subject label: $XNAT_SUBJECT_LABEL | Session label: $XNAT_SESSION_LABEL | Download: ${DownloadPath}/${CASE}.zip"
                else
                     echo ""
                     echo " -- XNAT download file found but not valid for ${DownloadPath}/${CASE}.zip"
                     echo ""
                     XNATErrorsDownload="$XNATErrorsDownload\n   ---> Subject label: $XNAT_SUBJECT_LABEL | Session label: $XNAT_SESSION_LABEL | Download: ${DownloadPath}/${CASE}.zip"
                     DownloadError="yes"
                fi
            else
                echo ""
                echo " -- XNAT download file not found for ${DownloadPath}/${CASE}.zip"
                echo ""
                XNATErrorsDownload="$XNATErrorsDownload\n   ---> Subject label: $XNAT_SUBJECT_LABEL | Session label: $XNAT_SESSION_LABEL | Download: ${DownloadPath}/${CASE}.zip"
                DownloadError="yes"
            fi
    }
    
    # ------------------------------------------------------------------------------
    # -- Check the server you are transfering data from:
    # ------------------------------------------------------------------------------
    TRANSFERNODE=`hostname`
        echo ""
        echo "-- Transferring data from: $TRANSFERNODE"
        echo ""
    
    # ------------------------------------------------------------------------------
    #  -- Setup the JSESSION and clean up prior temp folders:
    # ------------------------------------------------------------------------------
    ## -- Get credentials, read from the credential file or given with
    ## --xnatuser and --xnatpass
    XNAT_CREDENTIALS="${XNAT_USER_NAME}:${XNAT_PASSWORD}"
    ## -- Open JSESSION to the XNAT Site
    JSESSION=$(curl -k -X POST -u "$XNAT_CREDENTIALS" "${XNAT_HOST_NAME}/data/JSESSION" )
    echo ""
    echo "-- JSESSION created: ${JSESSION}"; echo ""
    
    ## -- Check if downloadpath can be found:
    if [[ -d ${DownloadPath} ]]; then
        echo ""
        echo " -- Download path ${DownloadPath} found. Proceeding..."
        echo ""
    else
        echo ""
        echo " -- Download path ${DownloadPath} not found. Generating now..."
        echo ""
        mkdir -p ${DownloadPath} &> /dev/null
        if [[ ! -d ${DownloadPath} ]]; then
            echo ""
            echo " -- Download path ${DownloadPath} still not found. Check file system paths or permissions..."
            echo ""
            exit 1
        fi
    fi
    
    ## -- the project information is kept in the run's log folder, in a folder
    ## of its own, as a log folder may be shared by runs (the legacy layout)
    unset TimeStamp XNATInfoPath
    XNATInfoPath="${LogFolder}/XNATInfo_${RunTimeStamp}"
    mkdir -p "${XNATInfoPath}" &> /dev/null
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
    TimeStamp=`date +%Y-%m-%d_%H.%M.%S.%6N`
    
    ## -- Obtain temp info on subjects and experiments in the project
    curl -k -b "JSESSIONID=$JSESSION" -m 30 -X GET "${XNAT_HOST_NAME}/data/sessions?project=${XNAT_PROJECT_ID}&format=csv" > ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${TimeStamp}.csv
    curl -k -b "JSESSIONID=$JSESSION" -m 30 -X GET "${XNAT_HOST_NAME}/data/experiments?project=${XNAT_PROJECT_ID}&format=csv" > ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${TimeStamp}.csv
        
    if [ -f ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${TimeStamp}.csv ] && [ -f ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${TimeStamp}.csv ]; then
       echo ""
       echo "  ---> Downloaded XNAT project info: "; echo ""
       echo "      ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${TimeStamp}.csv"
       echo "      ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${TimeStamp}.csv"
       echo ""
    else
       if [ ! -f ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${TimeStamp}.csv ]; then
           echo ""
           echo " ERROR: ${XNATInfoPath}/${XNAT_PROJECT_ID}_subjects_${TimeStamp}.csv not found! "
           echo ""
           exit 1
       fi
       if [ ! -f ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${TimeStamp}.csv ]; then
           echo ""
           echo " ERROR: ${XNATInfoPath}/${XNAT_PROJECT_ID}_experiments_${TimeStamp}.csv not found! "
           echo ""
           exit 1
       fi
    fi
    
    unset DownloadError
    XNATErrorsDownload="\n"
    XNATSuccessDownload="\n"
    
    ## -- Loop over subjects
    for XNAT_SUBJECT_LABEL in ${XNAT_SUBJECT_LABELS}; do XNATDownloadFunction; done
    
    ## -- Close JSESSION
    curl -k -X DELETE -b "JSESSIONID=${JSESSION}" "${XNAT_HOST_NAME}/data/JSESSION"
    echo ""
    echo "-- JSESSION closed: ${JSESSION}"
    
    ## -- Final download check
    if [[ -z ${DownloadError} ]]; then
        echo ""
        echo -e "-- SUCCESS: XNAT download from ${XNAT_HOST_NAME} completed without error for following sessions: ${XNATSuccessDownload}"
        echo ""
        echo "------------------------- Successful completion of work --------------------------------"
        echo ""
    fi
    if [[ ${DownloadError} == 'yes' ]]; then
        echo ""
        echo -e "-- ERROR: XNAT download to ${XNAT_HOST_NAME} failed for following sessions: ${XNATErrorsDownload}"
        echo ""
    fi
    
fi

############################ END OF DOWNLOAD CODE ##############################




############################ START OF UPLOAD CODE ##############################

if [[ ${RUN_TYPE} == "upload" ]]; then
    
    unset TimeStamp
    TimeStamp=`date +%Y-%m-%d_%H.%M.%S.%6N`

    echo ""
    echo "       ********************************************"
    echo "       ****** Setting up XNAT host upload *********"
    echo "       ********************************************"
    echo ""
    
    # ------------------------------------------------------------------------------
    # -- Upload function
    # ------------------------------------------------------------------------------
    CountFailList=""
    CountOKList=""
    
    uploadDICOMSCurl() {
        ## -- Upload DICOMs
        unset UPLOADDICOMS
        unset FileCount
        unset DICOMCount
        echo "-- Uploading individual DICOMs ... "
            if [ -z ${DICOMPath} ]; then
                DICOMPath="${SessionsFolder}/xnatupload/temp_${TimeStamp}/working"
            fi
            echo ""
            echo "    -- Dicom Path: $DICOMPath"
            echo ""
            cd ${DICOMPath}
            UPLOADDICOMS=`ls ./* | cut -f2 -d'/'`
            DICOMCount=`echo ${UPLOADDICOMS} | wc -w`
            echo ""
            echo "--------------------- DICOMs Staged for XNAT Upload: -------------------"
            echo ""
            echo "   File count: ${DICOMCount}"
            echo ""
            echo "------------------------------------------------------------------------"
            echo ""
            # -- Set file count check to 0
            FileCount=0
            ## -- Loop over DICOM files
            for DCM in ${UPLOADDICOMS}; do
                if [[ -z `ls ${DICOMPath}/${DCM}` ]]; then
                    echo "---> ERROR: File not found ${DICOMPath}/${DCM}"
                    exit 1
                fi
                echo ""
                echo "    -- Working on: ${DICOMPath}/${DCM}"
                echo ""
                ## -- DESCRIPTION OF XNAT Site Variables for the curl command:
                ## 
                ##    -b "JSESSIONID=$JSESSION" ---> XNAT Site Open Session Variable
                ##    -X ---> Here $XNAT_HOST_NAME corresponds to the XNAT URL; 
                ##  
                ##     INFO ON XNAT VARIABLE MAPPING FROM QuNex ---> JSON ---> XML specification
                ##
                ## project               --xnatprojectid        #  ---> mapping in QuNex: XNAT_PROJECT_ID     ---> mapping in JSON spec: #XNAT_PROJECT#   ---> Corresponding to project id in XML. 
                ##   │ 
                ##   └──subject          --xnatsubjectid        #  ---> mapping in QuNex: XNAT_SUBJECT_ID     ---> mapping in JSON spec: #SUBJECTID#      ---> Corresponding to subject ID in subject-level XML (Subject Accession ID). EXAMPLE in XML        <xnat:subject_ID>BID11_S00192</xnat:subject_ID>
                ##        │                                                                                                                                                                                                         EXAMPLE in Web UI     Accession number:  A unique XNAT-wide ID for a given human irrespective of project within the XNAT Site
                ##        │              --xnatsubjectlabel     #  ---> mapping in QuNex: XNAT_SUBJECT_LABEL  ---> mapping in JSON spec: #SUBJECTLABEL#   ---> Corresponding to subject label in subject-level XML (Subject Label).     EXAMPLE in XML        <xnat:field name="SRC_SUBJECT_ID">CU0018</xnat:field>
                ##        │                                                                                                                                                                                                         EXAMPLE in Web UI     Subject Details:   A unique XNAT project-specific ID that matches the experimenter expectations
                ##        │ 
                ##        └──experiment  --xnataccsessionid     #  ---> mapping in QuNex: XNAT_ACCSESSION_ID  ---> mapping in JSON spec: #ID#             ---> Corresponding to subject session ID in session-level XML (Subject Accession ID)   EXAMPLE in XML       <xnat:experiment ID="BID11_E00048" project="embarc_r1_0_0" visit_id="ses-wk2" label="CU0018_MRwk2" xsi:type="xnat:mrSessionData">
                ##                                                                                                                                                                                                                           EXAMPLE in Web UI    Accession number:  A unique project specific ID for that subject
                ##                       --xnatsessionlabel     #  ---> mapping in QuNex: XNAT_SESSION_LABEL  ---> mapping in JSON spec: #LABEL#          ---> Corresponding to session label in session-level XML (Session/Experiment Label)    EXAMPLE in XML       <xnat:experiment ID="BID11_E00048" project="embarc_r1_0_0" visit_id="ses-wk2" label="CU0018_MRwk2" xsi:type="xnat:mrSessionData">
                ##                                                                                                                                                                                                                           EXAMPLE in Web UI    MR Session:   A project-specific, session-specific and subject-specific XNAT variable that defines the precise acquisition / experiment
                ##      
                ##    -F "${DCM}=@${DCM}"       ---> What you are sending to the XNAT Site
                ##
                ## -------------------------------------------------------------
                ##
                ## -- Next upload individual dicom files
                ## -- Curl call echoed to screen
                echo curl -k -b "JSESSIONID=$JSESSION" -X POST "${XNAT_HOST_NAME}/data/services/import?import-handler=gradual-DICOM&PROJECT_ID=${XNAT_PROJECT_ID}&SUBJECT_ID=${XNAT_SUBJECT_LABEL}&EXPT_LABEL=${XNAT_SESSION_LABEL}" -F "${DCM}=@${DCM}"
                ## -- Curl captured in variable
                PREARCPATH=$(curl -k -b "JSESSIONID=$JSESSION" -X POST "${XNAT_HOST_NAME}/data/services/import?import-handler=gradual-DICOM&PROJECT_ID=${XNAT_PROJECT_ID}&SUBJECT_ID=${XNAT_SUBJECT_LABEL}&EXPT_LABEL=${XNAT_SESSION_LABEL}" -F "${DCM}=@${DCM}")
                ## -- Increase file counter
                FileCount=$((FileCount+1))
            done
        echo ""
        ## -- Perform DICOM count check and report
        CountCheck="${DICOMPath} ---> Uploaded DICOMS=${FileCount}"
        if [[ ${FileCount} == ${DICOMCount} ]]; then
            CountOKList="${CountOKList}\n${CountCheck}"
            echo "-- Upload done for: ${CountCheck}"
            echo "-- Total uploaded DICOMs OK: ${FileCount}"; echo ""
        else
            CountFailList="${CountFailList}\n${CountCheck}"
            echo "-- Upload not complete for: ${CountCheck}"
            echo "-- Total uploaded DICOMs ${FileCount} does not match input DICOM count ${DICOMCount}. Check and re-run."; echo ""
        fi
        echo ""
        ## -- Report PREARCHIVE XNAT path
        echo ""
        echo "-- PREARCHIVE XNAT path: ${PREARCPATH}"
        echo ""
    }
    
    # ------------------------------------------------------------------------------
    # -- Check the server you are transfering data from:
    # ------------------------------------------------------------------------------
    
    TRANSFERNODE=`hostname`
        echo ""
        echo "-- Transferring data from: $TRANSFERNODE"
        echo ""
    
    # ------------------------------------------------------------------------------
    #  -- Setup the JSESSION and clean up prior temp folders:
    # ------------------------------------------------------------------------------
    
    START=$(date +"%s")
    
    ## -- Get credentials, read from the credential file or given with
    ## --xnatuser and --xnatpass
    XNAT_CREDENTIALS="${XNAT_USER_NAME}:${XNAT_PASSWORD}"
    
    ## -- Open JSESSION to the XNAT Site
    JSESSION=$(curl -k -X POST -u "$XNAT_CREDENTIALS" "${XNAT_HOST_NAME}/data/JSESSION" )
    echo ""
    echo "-- JSESSION created: ${JSESSION}"; echo ""
    
    ## -- Set DICOM counter
    COUNTER=1
    
    ## -- Clean prior temp folders
    rm -r ${SessionsFolder}/xnatupload/temp_${TimeStamp}/working &> /dev/null
    
    # -------------------------------------------------------------------------
    # -- XNAT DICOM upload over multiple cases assuming the QuNex data hierarchy
    # -------------------------------------------------------------------------
    
    if [ -z ${DICOMPath} ]; then
        
        # ------------------------------------------------------------------------------
        # -- Iterate over CASES:
        # ------------------------------------------------------------------------------
    
        XNATErrorsUpload="\n"
        XNATSuccessUpload="\n"
        
        cd ${SessionsFolder}
        for CASE in ${CASES}; do
        
            ## -- If XNAT_SUBJECT_LABEL is empty set it to CASE
            if [ -z ${XNAT_SUBJECT_LABEL} ]; then
                XNAT_SUBJECT_LABEL="$CASE"
                echo "-- Setting XNAT session label to: $XNAT_SESSION_LABEL"; echo ""
            fi
            if [ -z ${XNAT_SESSION_LABEL} ]; then
                XNAT_SESSION_LABEL="$CASE"
                echo "-- Setting XNAT experiment to: $XNAT_SESSION_LABEL"; echo ""
            fi
            ## -- First check if data is present for upload
            if [ ! -d ${SessionsFolder}/${CASE}/dicom ]; then
                echo ""
                echo "-- ERROR: ${SessionsFolder}/${CASE}/dicom is not found on file system! Check your inputs. Proceeding to next session..."
                echo ""
                XNATUploadError="yes"
                XNATErrorsUpload="${XNATErrorsUpload}\n    ---> Subject label: $XNAT_SUBJECT_LABEL | Session label: $XNAT_SESSION_LABEL "
            else
                if [ -n "$(find "${SessionsFolder}/${CASE}/dicom" -maxdepth 0 -type d -empty 2>/dev/null)" ]; then 
                    echo ""
                    echo "-- ERROR: ${SessionsFolder}/${CASE}/dicom is found but empty! Check your data. Proceeding to next session..."
                    echo ""
                    XNATUploadError="yes"
                    XNATErrorsUpload="${XNATErrorsUpload}\n    ---> Subject label: $XNAT_SUBJECT_LABEL | Session label: $XNAT_SESSION_LABEL "
                else
                    echo ""
                    echo "-- Found and working on ${SessionsFolder}/${CASE}/dicom ..."
                    echo ""
                    
                    ## -- Obtain all dicoms
                    cd ${SessionsFolder}/${CASE}/dicom/
                    DICOMSERIES=`ls -vd */ | cut -f1 -d'/'`
                    
                    ## -- Iterate over DICOM SERIES
                    DICOMCOUNTER=0
                    for SERIES in $DICOMSERIES; do
                        
                        DICOMCOUNTER=$((DICOMCOUNTER+1))
                        
                        echo "-- Working on SERIES: $SERIES"
                        echo ""
                        mkdir -p ${SessionsFolder}/xnatupload/ &> /dev/null
                        mkdir -p ${SessionsFolder}/xnatupload/ &> /dev/null
                        mkdir -p ${SessionsFolder}/xnatupload/temp_${TimeStamp}/ &> /dev/null
                        mkdir -p ${SessionsFolder}/xnatupload/temp_${TimeStamp}/working/ &> /dev/null
                        
                        ## -- Unzip DICOM files for upload
                        echo "-- Unzipping DICOMs and linking into temp location ---> ${SessionsFolder}/xnatupload/temp_${TimeStamp}/working/"
                        echo ""
                        cp ${SessionsFolder}/${CASE}/dicom/${SERIES}/* ${SessionsFolder}/xnatupload/temp_${TimeStamp}/working/
                        gunzip ${SessionsFolder}/xnatupload/temp_${TimeStamp}/working/*.gz &> /dev/null
                        
                        ## -- DICOM upload function
                        uploadDICOMSCurl
                        
                        ## -- Check timestamp format matches the inputs
                        TIMESTAMP=$(echo ${PREARCPATH} | cut -d'/' -f 6 | tr -d '/')
                        PATTERN="[0-9]_[0-9]"
                        if [[ ${TIMESTAMP} =~ ${PATTERN} ]]; then
                            PREARCPATHFINAL="/data/prearchive/projects/${XNAT_PROJECT_ID}/${TIMESTAMP}/${XNAT_SESSION_LABEL}"
                            echo "-- Debug PAF is ${PREARCPATHFINAL}"
                        else
                            echo `date` "-- Debug TS doesn't pass: ${TIMESTAMP}"
                        fi
                        ## - Clean up and gzip data
                        rm -rf ${SessionsFolder}/xnatupload/temp_${TimeStamp}/ &> /dev/null
                        gzip ${SessionsFolder}/${CASE}/dicom/${SERIES}/* &> /dev/null
                        unset UPLOADDICOMS
                        echo ""
                        echo "-- DICOM SERIES $SERIES upload completed"
                        echo "------------------------------------------"
                        echo ""
                    done
            
                    ## -- Commit session (builds prearchive xml)
                    echo "-- Committing XNAT session to prearchive..."
                    echo ""
                    curl -k -b "JSESSIONID=${JSESSION}" -X POST "${XNAT_HOST_NAME}${PREARCPATHFINAL}?action=build" &> /dev/null
                    ## -- Archive session
                    curl -k -b "JSESSIONID=${JSESSION}" -X POST -H "Content-Type: application/x-www-form-urlencoded" "${XNAT_HOST_NAME}/data/services/archive?src=${PREARCPATHFINAL}&overwrite=delete"
                    echo ""
                    echo ""
                    echo "-- DICOM archiving completed completed for a total of $DICOMCOUNTER series"
                    echo "--------------------------------------------------------------------------------"
                    echo ""
                fi
            fi
        
            ## ------------------------------------------------------------------
            ## -- Code for uploading extra directories, such as NIFTI, HCP ect.
            ## ------------------------------------------------------------------
        
            if [ "$NIFTIUPLOAD" == "yes" ]; then
                echo "-- Uploading individual NIFTIs ... "
                echo ""
                cd ${SessionsFolder}/${CASE}/nii/
                NIFTISERIES=`ls | cut -f1 -d"." | uniq`
                #NIFTISERIES="01"
                ## -- Iterate over individual nifti files
                SCANCOUNTER=0
                for NIFTIFILE in $NIFTISERIES; do
                    SCANCOUNTER=$((SCANCOUNTER+1))
                    MULTIFILES=`ls ./$NIFTIFILE.*`
                    FILESTOUPLOAD=`echo $MULTIFILES | sed -e 's,./,,g'`
                    for NIFTIFILEUPLOAD in $FILESTOUPLOAD; do
                        ## -- Start the upload for NIFTI files
                        echo "-- Uploading NIFTI $NIFTIFILEUPLOAD"
                        echo ""
                        ## -- Clean existing nii session if requested
                        if [ "$OVERWRITE" == "yes" ]; then
                            curl -k -b "JSESSIONID=${JSESSION}" -X DELETE "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_SESSION_LABEL}/scans/${SCANCOUNTER}/resources/nii"
                        fi
                        ## -- Create a folder for nii scans
                        curl -k -b "JSESSIONID=${JSESSION}" -X PUT "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_SESSION_LABEL}/scans/${SCANCOUNTER}/resources/nii"
                        ## -- Upload a specific nii session
                        curl -k -b "JSESSIONID=${JSESSION}" -X POST "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/sessions/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_SESSION_LABEL}/scans/${SCANCOUNTER}/resources/nii/files/${NIFTIFILEUPLOAD}?inbody=true&overwrite=delete" --data-binary "@${NIFTIFILEUPLOAD}"
                    done
                    echo "-- NIFTI series $NIFTIFILE upload completed"
                done
                echo ""
                echo "-- NIFTI upload completed with a total of $SCANCOUNTER scans"
                echo "--------------------------------------------------------------------------------"
                echo ""
            fi
        XNATSuccessUpload="${XNATSuccessUpload}\n    ---> Subject label: $XNAT_SUBJECT_LABEL | Session label: $XNAT_SESSION_LABEL "
        done
    
    else
       
        # -------------------------------------------------------------------------
        # -- XNAT DICOM upload for a single session
        # -------------------------------------------------------------------------
     
         ## -- First check if data is present for upload
         if [ ! -d ${DICOMPath} ]; then
             echo ""
             echo "-- ERROR: ${DICOMPath} is not found on file system! Check your inputs."
             echo ""
             XNATUploadError="yes"
             XNATErrorsUpload="$DICOMPath"
         else
             if [ -n "$(find "${DICOMPath}" -maxdepth 0 -type d -empty 2>/dev/null)" ]; then 
                 echo ""
                 echo "-- ERROR: ${DICOMPath} is found but empty! Check your data."
                 echo ""
                 XNATUploadError="yes"
                 XNATErrorsUpload="$DICOMPath"
             else
                 echo ""
                 echo "-- Found and working on ${DICOMPath} ..."
                 echo ""
                 
                 ## -- If XNAT_SUBJECT_LABEL is empty set it to CASE
                 echo ""
                 if [ -z ${XNAT_SUBJECT_LABEL} ]; then
                     XNAT_SUBJECT_LABEL=`basename ${DICOMPath}`
                     echo "-- Setting XNAT session label to: $XNAT_SUBJECT_LABEL"; echo ""
                 fi
                 ## -- If XNAT_SESSION_LABEL is empty set it to CASE
                 if [ -z ${XNAT_SESSION_LABEL} ]; then
                     XNAT_SESSION_LABEL=`basename ${DICOMPath}`
                     echo "-- Setting XNAT experiment to: $XNAT_SESSION_LABEL"; echo ""
                 fi
                 
                 ## -- DICOM upload function
                 uploadDICOMSCurl
                 
                 ## -- Check timestamp format matches the inputs
                 TIMESTAMP=$(echo ${PREARCPATH} | cut -d'/' -f 6 | tr -d '/')
                 PATTERN="[0-9]_[0-9]"
                 if [[ ${TIMESTAMP} =~ ${PATTERN} ]]; then
                     PREARCPATHFINAL="/data/prearchive/projects/${XNAT_PROJECT_ID}/${TIMESTAMP}/${XNAT_SESSION_LABEL}"
                     echo "-- Debug PAF is ${PREARCPATHFINAL}"
                 else
                     echo `date` "-- Debug TS doesn't pass: ${TIMESTAMP}"
                 fi
                 ## - Clean up
                 unset UPLOADDICOMS
                 ## -- Commit session (builds prearchive xml)
                 echo "-- Committing XNAT session to prearchive..."
                 echo ""
                 curl -k -b "JSESSIONID=${JSESSION}" -X POST "${XNAT_HOST_NAME}${PREARCPATHFINAL}?action=build" &> /dev/null
                 ## -- Archive session
                 curl -k -b "JSESSIONID=${JSESSION}" -X POST -H "Content-Type: application/x-www-form-urlencoded" "${XNAT_HOST_NAME}/data/services/archive?src=${PREARCPATHFINAL}&overwrite=delete"
                 echo ""
                 echo ""
                 echo "-- DICOM archiving completed completed for a total of ${FileCount} files"
                 echo "--------------------------------------------------------------------------------"
                 echo ""
            fi
        fi
    
    fi
    
    ## -- Close JSESSION
    curl -k -X DELETE -b "JSESSIONID=${JSESSION}" "${XNAT_HOST_NAME}/data/JSESSION"
    
    ## -- DICOMPATH completion checks
    if [[ ! ${CountFailList}=="" ]]; then
        echo ""
        echo "--- XNAT upload failed for the following uploads:"
        echo "    -------------------------------------------------"
        echo ""
        echo -e "${CountFailList}"
        echo ""
        echo "   -------------------------------------------------"
        echo ""
    fi
    
    if [[ ! ${CountOKList}=="" ]]; then
        echo ""
        echo "--- XNAT upload failed for the following uploads:"
        echo "    -------------------------------------------------"
        echo ""
        echo -e "${CountOKList}"
        echo ""
        echo "   -------------------------------------------------"
        echo ""
    fi
    
    ## -- Final check
    if [[ ${CountFailList}=="" ]]; then 
        if [[ -z ${XNATUploadError} ]]; then
            echo ""
            echo -e "-- SUCCESS: XNAT upload to ${XNAT_HOST_NAME} completed without error for following sessions: ${XNATSuccessUpload}"
            echo ""
            echo "------------------------- Successful completion of work --------------------------------"
            echo ""
        fi
    fi
    if [[ ${XNATUploadError} == 'yes' ]]; then
        echo ""
        echo -e "-- ERROR: XNAT upload to ${XNAT_HOST_NAME} failed for following sessions: ${XNATErrorsUpload}"
        echo ""
    fi
    
fi
############################ END OF UPLOAD CODE ################################
    
}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@

unset XNAT_USER_NAME XNAT_PASSWORD XNAT_CREDENTIALS XNAT_HOST_NAME &> /dev/null
