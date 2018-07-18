#!/bin/bash
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
# * Alan Anticevic, N3 Division, Yale University
# * Zailyn Tamayo, N3 Division, Yale University 
#
# ## PRODUCT
#
#  mnap_xnat_turnkey.sh
#
# ## LICENSE
#
# * The MNAP_XNAT_Turnkey.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ### TODO
#
# --> finish turnkey type and add ability to pick a step.
#
# ## Description 
#   
# This script, MNAP_XNAT_Turnkey.sh MNAP Suite workflows in the XNAT Docker Engine
# 
# ## Prerequisite Installed Software
#
# * MNAP Suite
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. $./MNAP_XNAT_Turnkey.sh --help
#
# ### Expected Previous Processing
# 
# * The necessary input files are BOLD from previous processing
# * These may be stored in: "$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/ 
#
#~ND~END~

###################################################################
# Variables that will be passed as container launch:
###################################################################
#
# batchfile (batch file with processing parameters)
# overwrite (overwrite prior run)
# mappingfile (file for mapping into desired file structure; e.g. hcp)
# xnataccsessionid (Imaging Session Accession ID)
# xnatsessionlabel (Imaging Session Label)
# xnatprojectid (Project ID of the Imaging Session)
# xnatsubjectid (Subject ID of the Imaging session)
# xnathost (URL of the xnat host)
# xnatuser (xnat user id)
# xnatpass (xnat user password)
#
##########################################################
# Assumes $TOOLS and $MNAPREPO are defined
##########################################################

# ------------------------------------------------------------------------------
#  Setup color outputs
# ------------------------------------------------------------------------------

BLACK_F="\033[30m"; BLACK_B="\033[40m"
RED_F="\033[31m"; RED_B="\033[41m"
GREEN_F="\033[32m"; GREEN_B="\033[42m"
YELLOW_F="\033[33m"; YELLOW_B="\033[43m"
BLUE_F="\033[34m"; BLUE_B="\033[44m"
MAGENTA_F="\033[35m"; MAGENTA_B="\033[45m"
CYAN_F="\033[36m"; CYAN_B="\033[46m"
WHITE_F="\033[37m"; WHITE_B="\033[47m"
reho() {
    echo -e "$RED_F$1 \033[0m"
}
geho() {
    echo -e "$GREEN_F$1 \033[0m"
}
yeho() {
    echo -e "$YELLOW_F$1 \033[0m"
}
beho() {
    echo -e "$BLUE_F$1 \033[0m"
}
mageho() {
    echo -e "$MAGENTA_F$1 \033[0m"
}
cyaneho() {
    echo -e "$CYAN_F$1 \033[0m"
}
weho() {
    echo -e "$WHITE_F$1 \033[0m"
}

source $TOOLS/$MNAPREPO/library/environment/mnap_environment.sh &> /dev/null
MNAPTurnkeyWorkflow="createStudy organizeDicom getHCPReady mapHCPFiles hcp1 hcp2 hcp3 hcp4 hcp5 hcpd QCPreproc"

usage() {
    echo ""
    echo "  -- DESCRIPTION:"
    echo ""
    echo "  This function implements MNAP Suite workflows as a turnkey function."
    echo "  It operates on a local server or cluster or within the XNAT Docker engine."
    echo ""
    geho "     --> Supported MNAP turnkey workflow steps:"
    geho "         ${MNAPTurnkeyWorkflow} "
    echo ""
    echo "  -- REQUIRED PARMETERS:"
    echo ""
    echo "    --turnkey=<turnkey_run_type>                  Specify type turnkey run. Options are: local or xnat"
    echo "                                                  If empty default is set to: [xnat]."
    echo ""
    echo "  -- XNAT HOST & PROJECT PARMETERS:"
    echo ""
    echo "    --batch=<batch_file>                          Batch file with processing parameters which exist as a project-level resource on XNAT"
    echo "    --mappingfile=<mapping_file>                  file for mapping into desired file structure, e.g. hcp, which exist as a project-level resource on XNAT"
    echo "    --xnatprojectid=<name_of_xnat_project_id>     Specify the XNAT site project id. This is the Project ID in XNAT and not the Project Title."
    echo "    --xnathost=<XNAT_site_URL>                    Specify the XNAT site hostname URL to push data to."
    echo "    --xnatsessionlabel=<session_id>               Name of session within XNAT for a given subject id."
    echo "    --xnatsubjectid=<subject_id>                  Name of XNAT database subject IDs Default it []."
    echo "    --xnatuser=<xnat_host_user_name>              Specify XNAT username."
    echo "    --xnatpass=<xnat_host_user_pass>              Specify XNAT password."
    echo ""
    echo "  -- OPTIONAL PARMETERS:"
    echo ""
    echo "    --path=<study_path>                                Path where study folder is located. If empty default is [/output/xnatprojectid] for XNAT run."
    echo "    --xnataccsessionid=<accesession_id>                Identifier of a subject across the entire XNAT database."
    echo "    --overwritesubject=<specify_subject_overwrite>     Specify <yes> or <no> for cleanup of prior subject run. Default is [no]."
    echo "    --overwriteproject=<specify_project_overwrite>     Specify <yes> or <no> for cleanup of entire project. Default is [no]."
    echo ""
    echo "  -- EXAMPLE:"
    echo ""
    echo "  MNAP_XNAT_Turnkey.sh \ "
    echo "   --turnkey=<turnkey_run_type> \ "
    echo "   --batchfile=<batch_file> \ "
    echo "   --overwrite=yes \ "
    echo "   --mappingfile=<mapping_file> \ "
    echo "   --xnatsessionlabel=<xnat_session_label> \ "
    echo "   --xnatprojectid=<name_of_xnat_project_id> \ "
    echo "   --xnathostname=<XNAT_site_URL> \ "
    echo "   --xnatuser=<your_username> \ "
    echo ""
}

# -- Check help call
if [[ -z $1 ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]]; then
	usage
	exit 0
fi

# -- Clear variables
unset BATCH_PARAMETERS_FILENAME
unset OVERWRITE_PROJECT
unset OVERWRITE_SUBJECT
unset SCAN_MAPPING_FILENAME
unset XNAT_ACCSESSION_ID
unset XNAT_SESSION_LABEL
unset XNAT_PROJECT_ID
unset XNAT_SUBJECT_ID
unset XNAT_HOST_NAME
unset XNAT_USER_NAME
unset XNAT_PASSWORD
unset TURNKEY_TYPE

# -- Parse arguments
while [ "$1" != "" ]; do
    PARAM=`echo $1 | awk -F= '{print $1}'`
    VALUE=`echo $1 | awk -F= '{print $2}'`
    case $PARAM in
        --path)
            STUDY_PATH=$VALUE
            ;;
        --batchfile)
            BATCH_PARAMETERS_FILENAME=$VALUE
            ;;
        --turnkey)
            TURNKEY_TYPE=$VALUE
        --overwritesubject)
            OVERWRITE_SUBJECT=$VALUE
            ;;
        --overwriteproject)
            OVERWRITE_PROJECT=$VALUE
            ;;
        --mappingfile)
            SCAN_MAPPING_FILENAME=$VALUE
            ;;
        --xnataccsessionid)
            XNAT_ACCSESSION_ID=$VALUE
            ;;
        --xnatsessionlabel)
            XNAT_SESSION_LABEL=$VALUE
            ;;
        --xnatprojectid)
            XNAT_PROJECT_ID=$VALUE
            ;;
        --xnatsubjectid)
            XNAT_SUBJECT_ID=$VALUE
            ;;
        --xnathost)
            XNAT_HOST_NAME=$VALUE
            ;;
        --xnatuser)
            XNAT_USER_NAME=$VALUE
            ;;
        --xnatpass)
            XNAT_PASSWORD=$VALUE
            ;;
        *)
            echo "ERROR: unknown parameter \"$PARAM\""
            usage
            exit 1
            ;;
    esac
    shift
done

# -- Check that all inputs are provided
if [ -z "$BATCH_PARAMETERS_FILENAME" ]; then reho "Error: --batchfile flag missing. Batch parameter file not specified."; exit 1; fi
if [ -z "$SCAN_MAPPING_FILENAME" ]; then reho "Error: --mappingfile flag missing. Batch parameter file not specified."; exit 1; fi
if [ -z "$XNAT_SESSION_LABEL" ]; then reho "Error: --xnatsessionlabel flag missing."; exit 1; fi
if [ -z "$XNAT_PROJECT_ID" ]; then reho "Error: --xnatprojectid flag missing. Batch parameter file not specified."; exit 1; fi
if [ -z "$XNAT_HOST_NAME" ]; then reho "Error: --xnathost flag missing. Batch parameter file not specified."; exit 1; fi
if [ -z "$XNAT_USER_NAME" ]; then reho "Error: --xnatuser flag missing. Batch parameter file not specified."; exit 1; fi
if [ -z "$XNAT_PASSWORD" ]; then reho "Error: --xnatpass flag missing. Batch parameter file not specified."; exit 1; fi
if [ -z "$OVERWRITE_SUBJECT" ]; then OVERWRITE_SUBJECT="no"; fi
if [ -z "$OVERWRITE_PROJECT" ]; then OVERWRITE_PROJECT="no"; fi
if [ -z "$STUDY_PATH" ]; then STUDY_PATH="/output/${XNAT_PROJECT_ID}"; reho "Note: Study path missing. Setting defaults: $STUDY_PATH"; fi
if [ -z "$TURNKEY_TYPE" ]; then TURNKEY_TYPE="xnat"; reho "Note: Setting turnkey: $TURNKEY_TYPE"; fi

# -- Define additional variables
local scriptName=$(basename ${0})
if [[ -z ${STUDY_PATH} ]]; then
	workdir="/output"
	mnap_studyfolder="${workdir}/${XNAT_PROJECT_ID}"
else
	mnap_studyfolder="${STUDY_PATH}"
fi
mnap_subjectsfolder="${mnap_studyfolder}/subjects"
mnap_workdir="${mnap_subjectsfolder}/${XNAT_SESSION_LABEL}"
logdir="${mnap_studyfolder}/processing/logs/"
specsdir="${mnap_subjectsfolder}/specs"
rawdir="${mnap_workdir}/inbox"
rawdir_temp="${mnap_workdir}/inbox_temp"
processingdir="${mnap_studyfolder}/processing"
project_batch_file="${processingdir}/${XNAT_PROJECT_ID}_batch_params.txt"
mnap='bash ${TOOLS}/${MNAPREPO}/connector/mnap.sh'

# -- Report options
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   "
echo "   MNAP Turnkey run type: ${TURNKEY_TYPE}"
echo "   XNAT Hostname: ${XNAT_HOST_NAME}"
echo "   XNAT Project ID: ${XNAT_PROJECT_ID}"
echo "   XNAT Session Label: ${XNAT_SESSION_LABEL}"
echo "   XNAT Resource Mapping file: ${XNAT_HOST_NAME}"
echo "   XNAT Resource Batch file: ${BATCH_PARAMETERS_FILENAME}"
echo "   Project-specific Batch file: ${project_batch_file}"
echo "   MNAP Study folder: ${mnap_studyfolder}"
echo "   MNAP Subject-specific working folder: ${rawdir}"
echo "   Overwrite for subject set to: ${OVERWRITE_SUBJECT}"
echo "   Overwrite for project set to: ${OVERWRITE_PROJECT}"
echo "   "
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""

# -- Check if overwrite is set to yes for subject and project
if [[ ${OVERWRITE_PROJECT} == "yes" ]]; then
	if [[ `ls -IQC -Ilists -Ispecs -Iinbox -Iarchive ${mnap_subjectsfolder}` == "$XNAT_SESSION_LABEL" ]]; then 
		reho "-- Found only ${XNAT_SESSION_LABEL} in ${mnap_subjectsfolder}."
		reho "   Removing entire project folder."; echo ""
		rm -rf ./${mnap_studyfolder}/ &> /dev/null
	else
		reho "-- There are more than ${XNAT_SESSION_LABEL} directories ${mnap_studyfolder}."
		reho "   Skipping project overwrite."; echo ""
	fi
fi
if [[ ${OVERWRITE_SUBJECT} == "yes" ]]; then
	reho "-- Removing ${mnap_workdir}."; echo ""
	rm -rf ./${mnap_workdir}/ &> /dev/null
fi

# -- Create study hieararchy and generate subject folders
geho " -- Checking for and generating study folder ${mnap_studyfolder}"; echo ""
if [ ! -d ${workdir} ]; then
	mkdir -p ${workdir} &> /dev/null
fi
if [ ! -d ${mnap_studyfolder} ]; then
	mnap createStudy --studyfolder="${mnap_studyfolder}"
fi
mkdir -p ${mnap_workdir} &> /dev/null
mkdir -p ${mnap_workdir}/inbox &> /dev/null
mkdir -p ${mnap_workdir}/inbox_temp &> /dev/null

# -- Get data from XNAT server
if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
	geho " -- Fetching batch and mapping files from ${XNAT_HOST_NAME}"; echo ""
	curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/919/files/${BATCH_PARAMETERS_FILENAME}" > ${specsdir}/${BATCH_PARAMETERS_FILENAME}
	curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/919/files/${SCAN_MAPPING_FILENAME}" > ${specsdir}/${SCAN_MAPPING_FILENAME} 
	echo ""
	geho " -- Linking DICOMs into ${rawdir}"; echo ""
	find /input/SCANS/ -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" -exec ln -s '{}' ${rawdir}/ ';' &> /dev/null
fi

# -- Organize DICOMs and map processing folder structure
mnap organizeDicom --subjectsfolder="${mnap_subjectsfolder}" --subjects="${XNAT_SESSION_LABEL}" --overwrite="${OVERWRITE}"
mnap getHCPReady --subjectsfolder="${mnap_subjectsfolder}" --subjects="${XNAT_SESSION_LABEL}" --mapping="${specsdir}/${SCAN_MAPPING_FILENAME}" --overwrite="${OVERWRITE}"
mnap mapHCPFiles --subjectsfolder="${mnap_subjectsfolder}" --subjects="${XNAT_SESSION_LABEL}" --overwrite="$OVERWRITE"

# -- Generate subject specific hcp processing file
geho " -- Generating ${project_batch_file}"; echo ""
cp ${specsdir}/${BATCH_PARAMETERS_FILENAME} ${project_batch_file}
cat ${mnap_workdir}/subject_hcp.txt >> ${project_batch_file}

# -- Execute processing and QC commands
geho " -- Starting HCP Processing and QC Calls"; echo ""; echo ""
geho " ---------------------------------------"; echo ""; echo ""
# =-=-=-=-=-=-= COMMANDS START =-=-=-=-=-=-=
#
mnap hcp1      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --logfolder="${logdir}"
mnap hcp2      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --logfolder="${logdir}"
mnap hcp3      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --logfolder="${logdir}"
mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --templatefolder="${TOOLS}/${MNAPREPO}/library/data" --outpath="${mnap_subjectsfolder}/QC/T1w" --modality="T1w" --overwrite="yes" --logfolder="${logdir}"
mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --templatefolder="${TOOLS}/${MNAPREPO}/library/data" --outpath="${mnap_subjectsfolder}/QC/T2w" --modality="T2w" --overwrite="yes" --logfolder="${logdir}"
mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --templatefolder="${TOOLS}/${MNAPREPO}/library/data" --outpath="${mnap_subjectsfolder}/QC/myelin" --modality="myelin" --overwrite="yes" --logfolder="${logdir}"
mnap hcp4      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --hcp_bold_usemask="DILATED" --overwrite="${OVERWRITE}" --logfolder="${logdir}"
mnap hcp5      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --logfolder="${logdir}"
mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --boldsuffix="Atlas" --templatefolder="${TOOLS}/${MNAPREPO}/library/data" --outpath="${mnap_subjectsfolder}/QC/BOLD" --modality="BOLD" --overwrite="yes" --logfolder="${logdir}"
mnap hcpd      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --logfolder="${logdir}"
mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --templatefolder="${TOOLS}/${MNAPREPO}/library/data" --outpath="${mnap_subjectsfolder}/QC/DWI" --dwilegacy="no" --dwidata="data" --dwipath="Diffusion" --modality="DWI" --overwrite="yes" --logfolder="${logdir}"
#
# =-=-=-=-=-=-= COMMANDS END =-=-=-=-=-=-= 
echo ""; echo ""
geho " -- HCP Processing and QC Calls done"; echo ""; echo ""
geho " ---------------------------------------"; echo ""; echo ""

# -- Check for completion
geho " -- Looking into ${sourcepath} for incomplete/failed process"
find ${logdir}/comlogs  -type f -not -name "done_*.log"  &> /dev/null
filecnt=$(find ${logdir}/comlogs/  -type f -not -name "done_*.log"  | wc -l)  &> /dev/null

if [[ ${filecnt} != "" ]]; then
	echo ""
	reho "Appears atleast ${filecnt} steps have failed"
	echo ""
else
	echo ""
	geho "------------------------- Successful end of work --------------------------------"
	echo ""
fi
