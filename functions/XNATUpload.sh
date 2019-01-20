#!/bin/sh
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## COPYRIGHT NOTICE
#
# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
#
# ## AUTHORS(s)
#
# * Alan Anticevic, Department of Psychiatry, Yale University
#
# ## PRODUCT
#
#  XNATUpload.sh
#
# ## LICENSE
#
# * The XNATUpload.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ## TODO
#
# --> Add functionality to take in all data types into the XNAT database
# --> Add functionality to loop over --xnatsubjectids for each --subject
#     Here need to check if variable lenghts are the same
#     Here need to take positional xnatsubjectid for each CASE within the CASES loop.
#     Do the same for session ID
#     Right now -sessionid is a SINGLE variable that is assumed to be the same for all CASES
#
# ## DESCRIPTION 
#   
# This script, XNATCloudUpload.sh, implements upload of the data to the XNAT host via the curl API 
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * curl
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./XNATUpload.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are data stored in the following format
# * These data are stored in: "$SubjectsFolder/$CASE/
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
    echo ""
    echo "-- DESCRIPTION:"
    echo ""
    echo "This function implements syncing to the XNAT cloud XNAT_HOST_NAME via the CURL REST API."
    echo ""
    echo "Note: To invoke this function you need a credential file in your home folder: " 
    echo ""
    echo "   ~/.xnat     --> This file stores the username and password for the XNAT site"
    echo "                       Permissions of this file need to be set to 400 "
    echo "                       If this file does not exist the script will prompt you to generate one"
    echo ""
    echo "-- REQUIRED PARMETERS:"
    echo ""
    echo "-- Local system variables if using MNAP hierarchy:"
    echo ""
    echo "          --subjectsfolder=<folder_with_subjects_data>  Path to study data folder where the subjects folders reside"
    echo "          --subjects=<list_of_cases>                    List of subjects to run that are study-specific and correspond to XNAT database subject IDs"
    echo ""
    echo "-- Local system variables if using generic DICOM location for a single XNAT upload:"
    echo ""
    echo "          --dicompath=<folder_with_dicoms>  Path to folder where the DICOMs reside"
    echo ""
    echo "-- XNAT site variables"
    echo ""
    echo "          --xnatprojectid=<name_of_xnat_project_id>     Specify the XNAT site project id. This is the Project ID in XNAT and not the Project Title."
    echo "                                                        This project should be created on the XNAT Site prior to upload."
    echo "                                                        If it is not found on the XNAT Site or not provided then the data will land into the prearchive and be left unassigned to a project."
    echo "                                                        Please check upon completion and specify assignment manually."
    echo "          --xnathost=<XNAT_site_URL>                    Specify the XNAT site hostname URL to push data to."
    echo ""
    echo "-- OPTIONAL PARMETERS:"
    echo "" 
    echo ""
    echo "          --xnatsubjectids=<list_of_cases>                       List of XNAT database subject IDs Default assumes it matches --subjects."
    echo "                                                                 If your XNAT database subject id is distinct from your local server subject id then please supply this flag."
    echo "                                                                 Use if your XNAT database has a different set of subject ids."
    echo "          --xnatexperiment=<xnat_experiment_name>                Name of experiment within XNAT for a given subject id. Default []. Assuming it matches --subjects."
    echo "          --xnatsessionlabel=<session_id>                        Name of session within XNAT for a given subject id. Default []. Assuming it matches --subjects. "
    echo "                                                                 Use if you wish to upload multiple distinct sessions per subject id."
    echo "                                                                 If you wish to upload a new session for this subject id please supply this flag."
    echo "          --niftiupload=<specify_nifti_upload>                   Specify <yes> or <no> for NIFTI upload. Default is [no]"
    echo "          --overwrite=<specify_overwrite>                        Specify <yes> or <no> for cleanup of prior upload on the host server. Default is [yes]"
    echo "          --resetcredentials=<reset_credentials_for_xnat_site_>  Specify <yes> if you wish to reset your XNAT site user and password. Default is [no]"
    echo ""
    echo "-- Example:"
    echo ""
    echo "XNATUpload.sh --subjectsfolder='<absolute_path_to_subjects_folder>' \ "
    echo "--subjects='<subject_IDs_on_local_server>' \ "
    echo "--xnatprojectid='<name_of_xnat_project_id>' \ "
    echo "--xnathost='<XNAT_site_URL>' "
    echo ""
}

# ------------------------------------------------------------------------------
# -- Setup color outputs
# ------------------------------------------------------------------------------

reho() {
    echo -e "\033[31m $1 \033[0m"
}

geho() {
    echo -e "\033[32m $1 \033[0m"
}

ceho() {
    echo -e "\033[36m $1 \033[0m"
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
}

if [ $(opts_CheckForHelpRequest $@) ]; then
    showVersion
    show_usage
    exit 0
fi

# -- Initialize global output variables
unset SubjectsFolder
unset XNAT_HOST_NAME
unset XNAT_CREDENTIALS
unset XNAT_PROJECT_ID
unset CASES
unset XNAT_SUBJECT_IDS
unset XNAT_SESSION_LABEL
unset XNAT_EXPT_LABEL
unset NIFTIUPLOAD
unset OVERWRITE
unset ResetCredentials
unset DICOMPath

# -- Parse arguments
SubjectsFolder=`opts_GetOpt "--subjectsfolder" $@`
ResetCredentials=`opts_GetOpt "--resetcredentials" $@`
XNAT_HOST_NAME=`opts_GetOpt "--xnathost" $@`
XNAT_PROJECT_ID=`opts_GetOpt "--xnatprojectid" $@`
CASES=`opts_GetOpt "--subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'`
XNAT_SUBJECT_IDS=`opts_GetOpt "--xnatsubjectids" $@`
XNAT_SESSION_LABEL=`opts_GetOpt "--xnatsessionlabel" $@`
XNAT_EXPT_LABEL=`opts_GetOpt "--xnatexperiment" $@`
NIFTIUPLOAD=`opts_GetOpt "--niftiupload" $@`
OVERWRITE=`opts_GetOpt "--overwrite" $@`
DICOMPath=`opts_GetOpt "--dicompath" $@`

# -- Check required parameters

if [ -z ${DICOMPath} ]; then
    ## -- Check subject folder if DICOMPath is not set
    if [ -z ${SubjectsFolder} ]; then
        usage
        reho "ERROR: <folder-with-subjects> not specified"
        echo ""
        exit 1
    fi
    ## -- Check requested subjects if DICOMPath is not set
    if [ -z ${CASES} ]; then
        usage
        reho "ERROR: --subjects flag not specified"
        echo ""
        exit 1
    fi
    ## -- Check XNAT session label if DICOMPath is not set
    if [ -z ${XNAT_SESSION_LABEL} ]; then
        XNAT_SESSION_LABEL=""
        echo ""
        reho "Note: --xnatsessionlabel flag omitted. Assuming specified subject names match --xnatsessionlabel in XNAT."
        reho "    If you wish to upload a new session for this subject id please supply this flag."
        echo ""
    fi
    ## -- Check XNAT experiment label if DICOMPath is not set
    if [ -z ${XNAT_EXPT_LABEL} ]; then
        XNAT_EXPT_LABEL=""
        echo ""
        reho "Note: --xnatexperiment flag omitted. Assuming specified subject names match --xnatexperiment in XNAT."
        reho "    If you wish to upload a new session for this subject id please supply this flag."
        echo ""
    fi
    ## -- Check XNAT subject IDs if DICOMPath is not set
    if [ -z ${XNAT_SUBJECT_IDS} ]; then
        XNAT_SUBJECT_IDS="$CASES"
        echo ""
        reho "Note: --xnatsubjectids flag omitted. Assuming --subjects flag matches --xnatsubjectids in XNAT."
        reho "    If your XNAT database subject id is distinct from your local server subject id then please supply this flag."
        echo ""
    fi
    
else 
    ## -- Generic DICOM path is set outside of MNAP hierarchy
    reho "Note: --dicompath=${DICOMPath} specified, which assumes DICOM location for a single XNAT upload."; echo ""
    ## -- Check XNAT session label if DICOMPath is set
    if [ -z ${XNAT_SESSION_LABEL} ]; then
        XNAT_SESSION_LABEL=""
        echo ""
        reho "Note: --xnatsessionlabel flag omitted. Data will be pushed in the XNAT Site prearchive and left unassigned. Please check upon completion and specify assignment manually."
        reho "    If you wish to upload a new session for this subject id please supply this flag."
        echo ""
    fi
    ## -- Check XNAT experiment label if DICOMPath is set
    if [ -z ${XNAT_EXPT_LABEL} ]; then
        XNAT_EXPT_LABEL=""
        echo ""
        reho "Note: --xnatexperiment flag omitted. Data will be pushed in the XNAT Site prearchive and left unassigned. Please check upon completion and specify assignment manually."
        reho "    If you wish to upload a new session for this subject id please supply this flag."
        echo ""
    fi
    ## -- Check XNAT subject IDs if DICOMPath is set
    if [ -z ${XNAT_SUBJECT_IDS} ]; then
        XNAT_SUBJECT_IDS=""
        echo ""
        reho "Note: --xnatsubjectids flag omitted. Data will be pushed in the XNAT Site prearchive and left unassigned. Please check upon completion and specify assignment manually."
        reho "    If your XNAT database subject id is distinct from your local server subject id then please supply this flag."
        echo ""
    fi
fi

## -- Check XNAT Host variable
if [ -z ${XNAT_HOST_NAME} ]; then
    usage
    reho "ERROR: XNAT hostname not specified"
    echo ""
    exit 1
fi
## -- Check XNAT Project variable
if [ -z ${XNAT_PROJECT_ID} ]; then
    usage
    reho "Note: --xnatprojectid flag, which defines the XNAT Site Project is not specified."
    reho "      Data will be pushed in the XNAT Site prearchive and left unassigned. Please check upon completion and specify assignment manually."
    echo ""
fi
## -- Check if NIFTI upload is requested
if [ -z ${NIFTIUPLOAD} ]; then
    NIFTIUPLOAD="no"
fi
## -- Check if reseting credentials is requested
if [ -z ${ResetCredentials} ]; then
    ResetCredentials="no"
fi
## -- Check if overwrite is requested
if [ -z ${OVERWRITE} ]; then
    OVERWRITE="yes"
fi
  
# -- Report all requested options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    if [ -z ${DICOMPath} ]; then
        echo "   Folder with all subjects: ${SubjectsFolder}"
        echo "   Subjects to process: ${CASES}"
    else
        echo "   Folder DICOMs : ${DICOMPath}"
    fi
    echo "   XNAT IDs for subjects (in order matching subjects to process): ${XNAT_SUBJECT_IDS}"
    echo "   XNAT Session Label: ${XNAT_SESSION_LABEL}"
    echo "   XNAT Experiment: ${XNAT_EXPT_LABEL}"
    echo "   NIFTI upload: ${NIFTIUPLOAD}"
    echo "   OVERWRITE set to: ${OVERWRITE}"
    echo "   Reset XNAT site credentials: ${ResetCredentials}"
    echo "   XNAT Hostname: ${XNAT_HOST_NAME}"
    echo "   XNAT Project ID: ${XNAT_PROJECT_ID}"
    echo "-- ${scriptName}: Specified Command-Line Options - End --"
    echo ""
    geho "------------------------- Start of work --------------------------------"
echo ""

######################################### DO WORK ##########################################

main() {

TimeStamp=`date +%Y-%m-%d-%H-%M-%S`

# -- Get Command Line Options

echo ""
ceho "       ********************************************"
ceho "       ****** Setting up XNAT cloud upload ********"
ceho "       ********************************************"
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
    geho "-- Uploading individual DICOMs ... "
        if [ -z ${DICOMPath} ]; then
            DICOMPath="${SubjectsFolder}/xnatupload/temp_${TimeStamp}/working"
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
                reho "--> ERROR: File not found ${DICOMPath}/${DCM}"
                exit 1
            fi
            echo ""
            geho "    -- Working on: ${DICOMPath}/${DCM}"
            echo ""
            ## -- DESCRIPTION OF XNAT Site Variables for the curl command:
            ## 
            ##    -b "JSESSIONID=$JSESSION" --> XNAT Site Open Session Variable
            ##    -X --> Here $XNAT_HOST_NAME corresponds to the XNAT URL; 
            ##       --> PROJECT_ID corresponds to the XNAT Project ID in the Site URL; 
            ##           if not defined or not found then data goes into prearchive and left unassigned
            ##
            ##       --> SUBJECT_ID    ==> EXAMPLE in XML    ==>  <xnat:subject_ID>BID11_S00192</xnat:subject_ID>
            ##                         ==> EXAMPLE in Web UI ==> Accession number:  A unique XNAT-wide ID for a given human irrespective of project within the XNAT Site
            ##         
            ##       --> SUBJECT_LABEL ==> EXAMPLE in XML    ==> <xnat:field name="SRC_SUBJECT_ID">CU0018</xnat:field>
            ##                         ==> EXAMPLE in Web UI ==> Subject Details:   A unique XNAT project-specific ID that matches the experimenter expectations
            ##                     
            ##       --> EXPT_LABEL    ==> EXAMPLE in XML    ==> <xnat:experiment ID="BID11_E00048" project="embarc_r1_0_0" visit_id="ses-wk2" label="CU0018_MRwk2" xsi:type="xnat:mrSessionData">
            ##                         ==> EXAMPLE in Web UI ==> MR Session:        A project-specific, session-specific and subject-specific XNAT variable that defines the precise acquisition / experiment
            ##       
            ##    -F "${DCM}=@${DCM}"       --> What you are sending to the XNAT Site
            ##
            ## -------------------------------------------------------------
            ##
            ## -- Next upload individual dicom files
            ## -- Curl call echoed to screen
            echo curl -k -b "JSESSIONID=$JSESSION" -X POST "${XNAT_HOST_NAME}/data/services/import?import-handler=gradual-DICOM&PROJECT_ID=${XNAT_PROJECT_ID}&SUBJECT_ID=${XNAT_SESSION_LABEL}&EXPT_LABEL=${XNAT_EXPT_LABEL}" -F "${DCM}=@${DCM}"
            ## -- Curl captured in variable
            PREARCPATH=$(curl -k -b "JSESSIONID=$JSESSION" -X POST "${XNAT_HOST_NAME}/data/services/import?import-handler=gradual-DICOM&PROJECT_ID=${XNAT_PROJECT_ID}&SUBJECT_ID=${XNAT_SESSION_LABEL}&EXPT_LABEL=${XNAT_EXPT_LABEL}" -F "${DCM}=@${DCM}")
            ## -- Increase file counter
            FileCount=$((FileCount+1))
        done
    echo ""
    ## -- Perform DICOM count check and report
    CountCheck="${DICOMPath} ===> Uploaded DICOMS=${FileCount}"
    if [[ ${FileCount} == ${DICOMCount} ]]; then
        CountOKList="${CountOKList}\n${CountCheck}"
        geho "-- Upload done for: ${CountCheck}"
        geho "-- Total uploaded DICOMs OK: ${FileCount}"; echo ""
    else
        CountFailList="${CountFailList}\n${CountCheck}"
        reho "-- Upload not complete for: ${CountCheck}"
        reho "-- Total uploaded DICOMs ${FileCount} does not match input DICOM count ${DICOMCount}. Check and re-run."; echo ""
    fi
    echo ""
    ## -- Report PREARCHIVE XNAT path
    echo ""
    geho "-- PREARCHIVE XNAT path: ${PREARCPATH}"
    echo ""
}

# ------------------------------------------------------------------------------
# -- First check if .xnat credentials exist:
# ------------------------------------------------------------------------------

if [[ "${ResetCredential}" == "yes" ]]; then
    echo ""
    reho " -- Reseting XNAT credentials in ${HOME}/.xnat "
    echo ""
    rm -f ${HOME}/.xnat &> /dev/null
    echo ""
fi

if [ -f ${HOME}/.xnat ]; then
    echo ""
    ceho " -- XNAT credentials in ${HOME}/.xnat found. Proceeding with upload.        "
    echo ""
else
    reho " -- XNAT credentials in ${HOME}/.xnat NOT found. Please generate them now."
    echo ""
    reho "   --> Enter your XNAT XNAT_HOST_NAME username:"
    if read -s answer; then
        XNATUser=$answer
    fi
    reho "   --> Enter your XNAT XNAT_HOST_NAME password:"
    if read -s answer; then
        XNATPass=$answer
    fi
    echo $XNATUser:$XNATPass >> ${HOME}/.xnat
    chmod 400 ${HOME}/.xnat
    unset XNATUser
    unset XNATPass
    echo ""
    ceho " -- XNAT credentials generated in ${HOME}/.xnat " 
    echo ""
    ceho " -- Proceeding with upload.        "
    echo ""
fi

# ------------------------------------------------------------------------------
# -- Check the server you are transfering data from:
# ------------------------------------------------------------------------------

TRANSFERNODE=`hostname`
    echo ""
    geho "-- Transferring data from: $TRANSFERNODE"
    echo ""

# ------------------------------------------------------------------------------
#  -- Setup the JSESSION and clean up prior temp folders:
# ------------------------------------------------------------------------------

START=$(date +"%s")

## -- Get credentials
XNAT_CREDENTIALS=$(cat ${HOME}/.xnat)

## -- Open JSESSION to the XNAT Site
JSESSION=$(curl -k -X POST -u "$XNAT_CREDENTIALS" "${XNAT_HOST_NAME}/data/JSESSION" )
echo ""
geho "-- JSESSION created: ${JSESSION}"; echo ""
COUNTER=1
## -- Clean prior temp folders
rm -r ${SubjectsFolder}/xnatupload/temp_${TimeStamp}/working &> /dev/null

# ------------------------------------------------------------------------------
# -- Iterate over CASES:
# ------------------------------------------------------------------------------

if [ -z ${DICOMPath} ]; then
    
    # -- XNAT DICOM upload over multiple cases assuming the MNAP data hierarchy
    cd ${SubjectsFolder}
    for CASE in ${CASES}; do
    
        ## -- Unset XNAT variales
        unset XNATSubjectID
        unset XNAT_SESSION_LABEL
        unset XNAT_EXPT_LABEL
    
        ## -- If XNAT_SESSION_LABEL is empty set it to CASE
        if [ -z ${XNAT_SESSION_LABEL} ]; then
            XNAT_SESSION_LABEL="$CASE"
            echo "-- Setting XNAT session label to: $XNAT_SESSION_LABEL"; echo ""
        fi
        if [ -z ${XNAT_EXPT_LABEL} ]; then
            XNAT_EXPT_LABEL="$CASE"
            echo "-- Setting XNAT experiment to: $XNAT_EXPT_LABEL"; echo ""
        fi
        ## -- If XNATSubjectID is empty set it to CASE
        if [ -z ${XNATSubjectID} ]; then
            XNATSubjectID="$CASE"
            echo "-- Setting XNAT subject id to: $XNATSubjectID"; echo ""
        fi
        ## -- First check if data drop is present or if inbox is populated
        cd ${SubjectsFolder}/${CASE}/dicom
        echo ""
        geho "-- Working on subject: ${CASE}"
        cd ${SubjectsFolder}/${CASE}/dicom/
        echo ""
        DICOMSERIES=`ls -vd */ | cut -f1 -d'/'`
        ## -- Iterate over DICOM SERIES
        DICOMCOUNTER=0
        for SERIES in $DICOMSERIES; do
            DICOMCOUNTER=$((DICOMCOUNTER+1))
            geho "-- Working on SERIES: $SERIES"
            echo ""
            mkdir -p ${SubjectsFolder}/xnatupload/ &> /dev/null
            mkdir -p ${SubjectsFolder}/xnatupload/ &> /dev/null
            mkdir -p ${SubjectsFolder}/xnatupload/temp_${TimeStamp}/ &> /dev/null
            mkdir -p ${SubjectsFolder}/xnatupload/temp_${TimeStamp}/working/ &> /dev/null
            
            ## -- Unzip DICOM files for upload
            geho "-- Unzipping DICOMs and linking into temp location --> ${SubjectsFolder}/xnatupload/temp_${TimeStamp}/working/"
            echo ""
            cp ${SubjectsFolder}/${CASE}/dicom/${SERIES}/* ${SubjectsFolder}/xnatupload/temp_${TimeStamp}/working/
            gunzip ${SubjectsFolder}/xnatupload/temp_${TimeStamp}/working/*.gz &> /dev/null
            
            ## -- DICOM upload function
            uploadDICOMSCurl
            
            ## -- Check timestamp format matches the inputs
            TIMESTAMP=$(echo ${PREARCPATH} | cut -d'/' -f 6 | tr -d '/')
            PATTERN="[0-9]_[0-9]"
            if [[ ${TIMESTAMP} =~ ${PATTERN} ]]; then
                PREARCPATHFINAL="/data/prearchive/projects/${XNAT_PROJECT_ID}/${TIMESTAMP}/${XNAT_SESSION_LABEL}"
                geho "-- Debug PAF is ${PREARCPATHFINAL}"
            else
                reho `date` "- Debug TS doesn't pass! ${TIMESTAMP}"
            fi
            ## - Clean up and gzip data
            rm -rf ${SubjectsFolder}/xnatupload/temp_${TimeStamp}/ &> /dev/null
            gzip ${SubjectsFolder}/${CASE}/dicom/${SERIES}/* &> /dev/null
            clear UPLOADDICOMS
            echo ""
            geho "-- DICOM SERIES $SERIES upload completed"
            geho "------------------------------------------"
            echo ""
        done
        
        ## -- Commit session (builds prearchive xml)
        geho "-- Committing XNAT session to prearchive..."
        echo ""
        curl -k -b "JSESSIONID=${JSESSION}" -X POST "${XNAT_HOST_NAME}${PREARCPATHFINAL}?action=build" &> /dev/null
        ## -- Archive session
        curl -k -b "JSESSIONID=${JSESSION}" -X POST -H "Content-Type: application/x-www-form-urlencoded" "${XNAT_HOST_NAME}/data/services/archive?src=${PREARCPATHFINAL}&overwrite=delete"
        echo ""
        echo ""
        geho "-- DICOM archiving completed completed for a total of $DICOMCOUNTER series"
        geho "--------------------------------------------------------------------------------"
        echo ""
    
        ## ------------------------------------------------------------------
        ## -- Code for uploading extra directories, such as NIFTI, HCP ect.
        ## ------------------------------------------------------------------
    
        if [ "$NIFTIUPLOAD" == "yes" ]; then
            geho "-- Uploading individual NIFTIs ... "
            echo ""
            cd ${SubjectsFolder}/${CASE}/nii/
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
                    geho "-- Uploading NIFTI $NIFTIFILEUPLOAD"
                    echo ""
                    ## -- Clean existing nii session if requested
                    if [ "$OVERWRITE" == "yes" ]; then
                        curl -k -b "JSESSIONID=${JSESSION}" -X DELETE "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SESSION_LABEL}/experiments/${XNAT_SESSION_LABEL}/scans/${SCANCOUNTER}/resources/nii"
                    fi
                    ## -- Create a folder for nii scans
                    curl -k -b "JSESSIONID=${JSESSION}" -X PUT "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SESSION_LABEL}/experiments/${XNAT_SESSION_LABEL}/scans/${SCANCOUNTER}/resources/nii"
                    ## -- Upload a specific nii session
                    curl -k -b "JSESSIONID=${JSESSION}" -X POST "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SESSION_LABEL}/experiments/${XNAT_SESSION_LABEL}/scans/${SCANCOUNTER}/resources/nii/files/${NIFTIFILEUPLOAD}?inbody=true&overwrite=delete" --data-binary "@${NIFTIFILEUPLOAD}"
                done
                geho "-- NIFTI series $NIFTIFILE upload completed"
            done
            echo ""
            geho "-- NIFTI upload completed with a total of $SCANCOUNTER scans"
            geho "--------------------------------------------------------------------------------"
            echo ""
        fi
    
    done

else
    
    # -- XNAT DICOM upload for a single session
    
    ## -- Unset XNAT variales
    unset XNATSubjectID
    unset XNAT_SESSION_LABEL
    unset XNAT_EXPT_LABEL
    
    ## -- If XNAT_SESSION_LABEL is empty set it to CASE
    echo ""
    if [ -z ${XNAT_SESSION_LABEL} ]; then
        XNAT_SESSION_LABEL=`basename ${DICOMPath}`
        echo "-- Setting XNAT session label to: $XNAT_SESSION_LABEL"; echo ""
    fi
    ## -- If XNAT_EXPT_LABEL is empty set it to CASE
    if [ -z ${XNAT_EXPT_LABEL} ]; then
        XNAT_EXPT_LABEL=`basename ${DICOMPath}`
        echo "-- Setting XNAT experiment to: $XNAT_EXPT_LABEL"; echo ""
    fi
    ## -- If XNATSubjectID is empty set it to CASE
    if [ -z ${XNATSubjectID} ]; then
        XNATSubjectID=`basename ${DICOMPath}`
        echo "-- Setting XNAT subject id to: $XNATSubjectID"; echo ""
    fi
 
    ## -- DICOM upload function
    uploadDICOMSCurl
    
    ## -- Check timestamp format matches the inputs
    TIMESTAMP=$(echo ${PREARCPATH} | cut -d'/' -f 6 | tr -d '/')
    PATTERN="[0-9]_[0-9]"
    if [[ ${TIMESTAMP} =~ ${PATTERN} ]]; then
        PREARCPATHFINAL="/data/prearchive/projects/${XNAT_PROJECT_ID}/${TIMESTAMP}/${XNAT_SESSION_LABEL}"
        geho "-- Debug PAF is ${PREARCPATHFINAL}"
    else
        reho `date` "- Debug TS doesn't pass! ${TIMESTAMP}"
    fi
    ## - Clean up
    clear UPLOADDICOMS
    ## -- Commit session (builds prearchive xml)
    geho "-- Committing XNAT session to prearchive..."
    echo ""
    curl -k -b "JSESSIONID=${JSESSION}" -X POST "${XNAT_HOST_NAME}${PREARCPATHFINAL}?action=build" &> /dev/null
    ## -- Archive session
    curl -k -b "JSESSIONID=${JSESSION}" -X POST -H "Content-Type: application/x-www-form-urlencoded" "${XNAT_HOST_NAME}/data/services/archive?src=${PREARCPATHFINAL}&overwrite=delete"
    echo ""
    echo ""
    geho "-- DICOM archiving completed completed for a total of ${FileCount} files"
    geho "--------------------------------------------------------------------------------"
    echo ""

fi

## -- Close JSESSION
curl -k -X DELETE -b "JSESSIONID=${JSESSION}" "${XNAT_HOST_NAME}/data/JSESSION"

## -- DICOMPATH completion checks
if [[ ! ${CountFailList}=="" ]]; then
    echo ""
    reho "--- XNAT upload failed for the following uploads:"
    reho "    -------------------------------------------------"
    echo ""
    echo -e "${CountFailList}"
    echo ""
    reho "   -------------------------------------------------"
    echo ""
fi

if [[ ! ${CountOKList}=="" ]]; then
    echo ""
    reho "--- XNAT upload failed for the following uploads:"
    reho "    -------------------------------------------------"
    echo ""
    echo -e "${CountOKList}"
    echo ""
    reho "   -------------------------------------------------"
    echo ""
fi

## -- Final check
if [[ ${CountFailList}=="" ]]; then
    echo ""
    geho "------------------------- Successful completion of work --------------------------------"
    echo ""
fi

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main