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
# * The RunTurnkey.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ### TODO
#
# --> finish remaining functions 
#
# ## Description 
#   
# This script, RunTurnkey.sh MNAP Suite workflows in the XNAT Docker Engine
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
# Variables that will be passed as container launch in XNAT:
###################################################################
#
# batchfile (batch file with processing parameters)
# overwrite (overwrite prior run)
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
MNAPTurnkeyWorkflow="createStudy organizeDicom getHCPReady mapHCPFiles hcp1 hcp2 hcp3 hcp4 hcp5 hcpd FSLDtifit FSLBedpostxGPU eddyQC QCPreprocDWIProcess pretractographyDense DWIDenseParcellation DWISeedTractography QCPreprocCustom mapHCPData createBOLDBrainMasks computeBOLDStats createStatsReport extractNuisanceSignal preprocessBold preprocessConc computeBOLDfcGBC computeBOLDfcSeed"

# ------------------------------------------------------------------------------
# -- General usage
# ------------------------------------------------------------------------------

usage() {
    echo ""
    echo "  -- DESCRIPTION:"
    echo ""
    echo "  This function implements MNAP Suite workflows as a turnkey function."
    echo "  It operates on a local server or cluster or within the XNAT Docker engine."
    echo ""
    geho "     --> Supported MNAP turnkey workflow steps:"
    geho "         ${MNAPTurnkeyWorkflow}"
    echo ""
    echo "  -- PARMETERS:"
    echo ""
    echo "    --turnkey=<turnkey_run_type>                  Specify type turnkey run. Options are: local or xnat"
    echo "                                                  If empty default is set to: [xnat]."
    echo ""
    echo "  -- XNAT HOST & PROJECT PARMETERS:"
    echo ""
    echo "    --batch=<batch_file>                          Batch file with processing parameters which exist as a project-level resource on XNAT"
    echo "    --mappingfile=<mapping_file>                  File for mapping into desired file structure, e.g. hcp, which exist as a project-level resource on XNAT"
    echo "    --xnatprojectid=<name_of_xnat_project_id>     Specify the XNAT site project id. This is the Project ID in XNAT and not the Project Title."
    echo "    --xnathost=<XNAT_site_URL>                    Specify the XNAT site hostname URL to push data to."
    echo "    --xnatsessionlabels=<session_id>               Name of session within XNAT for a given subject id. If not provided then --subjects is needed."
    echo "    --xnatsubjectid=<subject_id>                  Name of XNAT database subject IDs Default it []."
    echo "    --xnatuser=<xnat_host_user_name>              Specify XNAT username."
    echo "    --xnatpass=<xnat_host_user_pass>              Specify XNAT password."
    echo ""
    echo "  -- XNAT HOST OPTIONAL PARMETERS:"
    echo ""
    echo "    --xnataccsessionid=<accesession_id>           Identifier of a subject across the entire XNAT database."
    echo ""
    echo "  -- OPTIONAL GENERAL PARMETERS:"
    echo ""
    echo "    --path=<study_path>                                Path where study folder is located. If empty default is [/output/xnatprojectid] for XNAT run."
    echo "    --subjects=<comma_separated_list_of_cases>             List of subjects to run locally if --xnatsessionlabels and --xnatsubjectid missing."
    echo "    --overwritesubject=<specify_subject_overwrite>     Specify <yes> or <no> for cleanup of prior subject run. Default is [no]. Also supports --overwrite"
    echo "    --overwriteproject=<specify_project_overwrite>     Specify <yes> or <no> for cleanup of entire project. Default is [no]."
    echo "    --turnkeysteps=<turnkey_worlflow_steps>            Specify specific turnkey steps you wish to run:"
    echo "                                                       Supported:   ${MNAPTurnkeyWorkflow} "
    echo ""
    echo "  -- OPTIONAL CUSTOM QC PARAMETER:"
    echo ""
    echo "    --customqc=<yes/no>     Default is [no]. If set to 'yes' then the script looks into: "
    echo "                            ~/<study_path>/processing/scenes/QC/ for additional custom QC scenes."
    echo "                                  Note: The provided scene has to conform to MNAP QC template standards.xw"
    echo "                                        See $TOOLS/$MNAPREPO/library/data/scenes/qc/ for example templates."
    echo "                                        The qc path has to contain relevant files for the provided scene."
    echo ""
    echo "  -- EXAMPLE:"
    echo ""
    echo "  RunTurnkey.sh \ "
    echo "   --turnkey=<turnkey_run_type> \ "
    echo "   --batchfile=<batch_file> \ "
    echo "   --overwrite=yes \ "
    echo "   --mappingfile=<mapping_file> \ "
    echo "   --xnatsessionlabels=<XNAT_SESSION_LABELS> \ "
    echo "   --xnatprojectid=<name_of_xnat_project_id> \ "
    echo "   --xnathostname=<XNAT_site_URL> \ "
    echo "   --xnatuser=<your_username> \ "
    echo ""
    exit 0
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]]; then
	usage
fi

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

get_options() {
# -- Clear variables
unset BATCH_PARAMETERS_FILENAME
unset OVERWRITE
unset OVERWRITE_PROJECT
unset OVERWRITE_SUBJECT
unset SCAN_MAPPING_FILENAME
unset XNAT_ACCSESSION_ID
unset XNAT_SESSION_LABELS
unset XNAT_PROJECT_ID
unset XNAT_SUBJECT_ID
unset XNAT_HOST_NAME
unset XNAT_USER_NAME
unset XNAT_PASSWORD
unset TURNKEY_TYPE
unset TURNKEY_STEP
unset setflag
unset doubleflag
unset singleflag

# -- Check if first parameter is missing flags and parse it as FunctionToRun
if [ -z `echo "$1" | grep '-'` ]; then
	FunctionToRun="$1"
	# -- Check if single or double flags are set
	doubleflagparameter=`echo $2 | cut -c1-2`
	singleflagparameter=`echo $2 | cut -c1`
	if [ "$doubleflagparameter" == "--" ]; then
		setflag="$doubleflagparameter"
	else
		if [ "$singleflagparameter" == "-" ]; then
			setflag="$singleflagparameter"
		fi
	fi
else
	# -- Check if single or double flags are set
	doubleflag=`echo $1 | cut -c1-2`
	singleflag=`echo $1 | cut -c1`
	if [ "$doubleflag" == "--" ]; then
		setflag="$doubleflag"
	else
		if [ "$singleflag" == "-" ]; then
			setflag="$singleflag"
		fi
	fi
fi

# =-=-=-=-=-= GENERAL OPTIONS =-=-=-=-=-=

# -- General input flags
STUDY_PATH=`opts_GetOpt "${setflag}path" $@`
CASES=`opts_GetOpt "${setflag}subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'`
OVERWRITE_SUBJECT=`opts_GetOpt "${setflag}overwritesubject" $@`
OVERWRITE_PROJECT=`opts_GetOpt "${setflag}overwriteproject" $@`
BATCH_PARAMETERS_FILENAME=`opts_GetOpt "${setflag}batchfile" $@`
SCAN_MAPPING_FILENAME=`opts_GetOpt "${setflag}mappingfile" $@`
XNAT_ACCSESSION_ID=`opts_GetOpt "${setflag}xnataccsessionid" $@`
XNAT_SESSION_LABELS=`opts_GetOpt "${setflag}xnatsessionlabels" $@`
XNAT_PROJECT_ID=`opts_GetOpt "${setflag}xnatprojectid" $@`
XNAT_SUBJECT_ID=`opts_GetOpt "${setflag}xnatsubjectid" $@`
XNAT_HOST_NAME=`opts_GetOpt "${setflag}xnathost" $@`
XNAT_USER_NAME=`opts_GetOpt "${setflag}xnatuser" $@`
XNAT_PASSWORD=`opts_GetOpt "${setflag}xnatpass" $@`

# =-=-=-=-=-= BOLD FC OPTIONS =-=-=-=-=-=

# -- computeBOLDfc input flags
InputFiles=`opts_GetOpt "${setflag}inputfiles" $@`
OutPathFC=`opts_GetOpt "${setflag}targetf" $@`
Calculation=`opts_GetOpt "${setflag}calculation" $@`
RunType=`opts_GetOpt "${setflag}runtype" $@`
FileList=`opts_GetOpt "${setflag}flist" $@`
IgnoreFrames=`opts_GetOpt "${setflag}ignore" $@`
MaskFrames=`opts_GetOpt "${setflag}mask" "$@"`
Covariance=`opts_GetOpt "${setflag}covariance" $@`
TargetROI=`opts_GetOpt "${setflag}target" $@`
RadiusSmooth=`opts_GetOpt "${setflag}rsmooth" $@`
RadiusDilate=`opts_GetOpt "${setflag}rdilate" $@`
GBCCommand=`opts_GetOpt "${setflag}command" $@`
Verbose=`opts_GetOpt "${setflag}verbose" $@`
ComputeTime=`opts_GetOpt "${setflag}-time" $@`
VoxelStep=`opts_GetOpt "${setflag}vstep" $@`
ROIInfo=`opts_GetOpt "${setflag}roinfo" $@`
FCCommand=`opts_GetOpt "${setflag}options" $@`
Method=`opts_GetOpt "${setflag}method" $@`

# =-=-=-=-=-= DIFFUSION OPTIONS =-=-=-=-=-=

# -- hcpdLegacy input flags
EchoSpacing=`opts_GetOpt "${setflag}echospacing" $@`
PEdir=`opts_GetOpt "${setflag}PEdir" $@`
TE=`opts_GetOpt "${setflag}TE" $@`
UnwarpDir=`opts_GetOpt "${setflag}unwarpdir" $@`
DiffDataSuffix=`opts_GetOpt "${setflag}diffdatasuffix" $@`
Scanner=`opts_GetOpt "${setflag}scanner" $@`
UseFieldmap=`opts_GetOpt "${setflag}usefieldmap" $@`
# -- DWIDenseParcellation input flags
MatrixVersion=`opts_GetOpt "${setflag}matrixversion" $@`
ParcellationFile=`opts_GetOpt "${setflag}parcellationfile" $@`
OutName=`opts_GetOpt "${setflag}outname" $@`
WayTotal=`opts_GetOpt "${setflag}waytotal" $@`
# -- DWISeedTractography input flags
SeedFile=`opts_GetOpt "${setflag}seedfile" $@`
# -- eddyQC input flags
EddyBase=`opts_GetOpt "${setflag}eddybase" $@`
EddyPath=`opts_GetOpt "${setflag}eddypath" $@`
Report=`opts_GetOpt "${setflag}report" $@`
BvalsFile=`opts_GetOpt "${setflag}bvalsfile" $@`
BvecsFile=`opts_GetOpt "${setflag}bvecsfile" $@`
EddyIdx=`opts_GetOpt "${setflag}eddyidx" $@`
EddyParams=`opts_GetOpt "${setflag}eddyparams" $@`
List=`opts_GetOpt "${setflag}list" $@`
Mask=`opts_GetOpt "${setflag}mask" $@`
GroupBar=`opts_GetOpt "${setflag}groupvar" $@`
OutputDir=`opts_GetOpt "${setflag}outputdir" $@`
Update=`opts_GetOpt "${setflag}update" $@`
# -- FSLBedpostxGPU input flags
Fibers=`opts_GetOpt "${setflag}fibers" $@`
Model=`opts_GetOpt "${setflag}model" $@`
Burnin=`opts_GetOpt "${setflag}burnin" $@`
Jumps=`opts_GetOpt "${setflag}jumps" $@`
Rician=`opts_GetOpt "${setflag}rician" $@`
# -- probtrackxGPUDense input flags
MatrixOne=`opts_GetOpt "${setflag}omatrix1" $@`
MatrixThree=`opts_GetOpt "${setflag}omatrix3" $@`
NsamplesMatrixOne=`opts_GetOpt "${setflag}nsamplesmatrix1" $@`
NsamplesMatrixThree=`opts_GetOpt "${setflag}nsamplesmatrix3" $@`

# =-=-=-=-=-= QC OPTIONS =-=-=-=-=-=

# -- QCPreproc input flags
OutPath=`opts_GetOpt "${setflag}outpath" $@`
TemplateFolder=`opts_GetOpt "${setflag}templatefolder" $@`
UserSceneFile=`opts_GetOpt "${setflag}userscenefile" $@`
UserScenePath=`opts_GetOpt "${setflag}userscenepath" $@`
Modality=`opts_GetOpt "${setflag}modality" $@`
DWIPath=`opts_GetOpt "${setflag}dwipath" $@`
DWIData=`opts_GetOpt "${setflag}dwidata" $@`
DtiFitQC=`opts_GetOpt "${setflag}dtifitqc" $@`
BedpostXQC=`opts_GetOpt "${setflag}bedpostxqc" $@`
EddyQCStats=`opts_GetOpt "${setflag}eddyqcstats" $@`
DWILegacy=`opts_GetOpt "${setflag}dwilegacy" $@`
BOLDDATA=`opts_GetOpt "${setflag}bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDDATA=`echo "$BOLDDATA" | sed 's/,/ /g;s/|/ /g'`
BOLDRUNS=`opts_GetOpt "${setflag}boldruns" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDRUNS=`echo "$BOLDRUNS" | sed 's/,/ /g;s/|/ /g'`
BOLDS=`opts_GetOpt "${setflag}bolds" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`
if [[ ! -z $BOLDDATA ]]; then
	if [[ -z $BOLDS ]]; then
		BOLDS=$BOLDDATA
	fi
fi
if [[ ! -z $BOLDRUNS ]]; then
	if [[ -z $BOLDS ]]; then
		BOLDS=$BOLDRUNS
	fi
fi
BOLDSuffix=`opts_GetOpt "${setflag}boldsuffix" $@`
BOLDPrefix=`opts_GetOpt "${setflag}boldprefix" $@`
SkipFrames=`opts_GetOpt "${setflag}skipframes" $@`
SNROnly=`opts_GetOpt "${setflag}snronly" $@`
TimeStamp=`opts_GetOpt "${setflag}timestamp" $@`
Suffix=`opts_GetOpt "${setflag}suffix" $@`
SceneZip=`opts_GetOpt "${setflag}scenezip" $@`
QCPreprocCustom=`opts_GetOpt "${setflag}customqc" $@`

# -- Check if subject input is a parameter file instead of list of cases
if [[ ${CASES} == *.txt ]]; then
	SubjectParamFile="$CASES"
	echo ""
	echo "Using $SubjectParamFile for input."
	echo ""
	CASES=`more ${SubjectParamFile} | grep "id:"| cut -d " " -f 2`
fi

# -- Check that all inputs are provided
if [ -z "$BATCH_PARAMETERS_FILENAME" ]; then reho "Error: --batchfile flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
if [ -z "$SCAN_MAPPING_FILENAME" ]; then reho "Error: --mappingfile flag missing. Batch parameter file not specified."; echo ''; exit 1;  fi
if [ -z "$XNAT_SESSION_LABELS" ] && [ -z "$CASES" ]; then reho "Error: --xnatsessionlabels and --subjects flag missing. Specify one."; echo ''; exit 1; fi
if [ -z "$XNAT_PROJECT_ID" ]; then reho "Error: --xnatprojectid flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
if [ -z "$XNAT_HOST_NAME" ]; then reho "Error: --xnathost flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
if [ -z "$XNAT_USER_NAME" ]; then reho "Error: --xnatuser flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
if [ -z "$XNAT_PASSWORD" ]; then reho "Error: --xnatpass flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
if [ -z "$OVERWRITE" ]; then OVERWRITE="no"; fi
if [ -z "$OVERWRITE_SUBJECT" ]; then OVERWRITE="no"; fi
if [ -z "$OVERWRITE_PROJECT" ]; then OVERWRITE_PROJECT="no"; fi
if [ -z "$STUDY_PATH" ]; then STUDY_PATH="/output/${XNAT_PROJECT_ID}"; reho "Note: Study path missing. Setting defaults: $STUDY_PATH"; fi
if [ -z "$TURNKEY_TYPE" ]; then TURNKEY_TYPE="xnat"; reho "Note: Setting turnkey to: $TURNKEY_TYPE"; fi
if [ -z "$OVERWRITE" ] && [ ! -z "$OVERWRITE_SUBJECT" ]; then OVERWRITE="OVERWRITE_SUBJECT"; fi
if [ -z "$TURNKEY_STEPS" ]; then TURNKEY_STEPS="all"; echo "Running all turnkey steps: ${MNAPTurnkeyWorkflow}"; fi
if [ -z "$QCPreprocCustom" ] || [ "$QCPreprocCustom" == "no" ]; then QCPreprocCustom="no"; MNAPTurnkeyWorkflow=`printf '%s\n' "${MNAPTurnkeyWorkflow//$QCPreprocCustom/}"`; fi

# -- Define script name
scriptName=$(basename ${0})

# -- Define additional variables
if [[ -z ${STUDY_PATH} ]]; then
	workdir="/output"
	mnap_studyfolder="${workdir}/${XNAT_PROJECT_ID}"
else
	mnap_studyfolder="${STUDY_PATH}"
fi
mnap_subjectsfolder="${mnap_studyfolder}/subjects"
mnap_workdir="${mnap_subjectsfolder}/${XNAT_SESSION_LABELS}"
logdir="${mnap_studyfolder}/processing/logs/"
specsdir="${mnap_subjectsfolder}/specs"
rawdir="${mnap_workdir}/inbox"
rawdir_temp="${mnap_workdir}/inbox_temp"
processingdir="${mnap_studyfolder}/processing"
project_batch_file="${processingdir}/${XNAT_PROJECT_ID}_batch_params.txt"
alias mnap='${TOOLS}/${MNAPREPO}/connector/mnap.sh'

# -- Report options
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   "
echo "   MNAP Turnkey run type: ${TURNKEY_TYPE}"
if [ "$TURNKEY_TYPE" == "xnat" ]; then
	CASES="$XNAT_SESSION_LABELS"
	echo "   XNAT Hostname: ${XNAT_HOST_NAME}"
	echo "   XNAT Project ID: ${XNAT_PROJECT_ID}"
	echo "   XNAT Session Label: ${XNAT_SESSION_LABELS}"
	echo "   XNAT Resource Mapping file: ${XNAT_HOST_NAME}"
	echo "   XNAT Resource Batch file: ${BATCH_PARAMETERS_FILENAME}"
fi
echo "   Project-specific Batch file: ${project_batch_file}"
echo "   MNAP Study folder: ${mnap_studyfolder}"
echo "   MNAP Subject-specific working folder: ${rawdir}"
echo "   Overwrite for subject set to: ${OVERWRITE_SUBJECT}"
echo "   Overwrite for project set to: ${OVERWRITE_PROJECT}"
echo "   Custom QC requested: ${QCPreprocCustom}"
if [ "$TURNKEY_STEPS" == "all" ]; then
	echo "   Turnkey workflow steps: ${MNAPTurnkeyWorkflow}"
else
	echo "   Turnkey workflow steps: ${TURNKEY_STEPS}"
fi
echo 
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""
}

main() {

# -- Get Command Line Options
get_options "$@"

# -- Check if overwrite is set to yes for subject and project
if [[ ${OVERWRITE_PROJECT} == "yes" ]]; then
	if [[ `ls -IQC -Ilists -Ispecs -Iinbox -Iarchive ${mnap_subjectsfolder}` == "$XNAT_SESSION_LABELS" ]]; then 
		reho "-- ${XNAT_SESSION_LABELS} is the only folder in ${mnap_subjectsfolder}. OK to proceed!"
		reho "   Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
		rm -rf ${mnap_studyfolder}/ &> /dev/null
	else
		reho "-- There are more than ${XNAT_SESSION_LABELS} directories ${mnap_studyfolder}."
		reho "   Skipping recursive overwrite for project: ${XNAT_PROJECT_ID}"; echo ""
	fi
fi
if [[ ${OVERWRITE} == "yes" ]]; then
	reho "-- Removing ${mnap_workdir}."; echo ""
	rm -rf ${mnap_workdir} &> /dev/null
fi

# -- Execute processing and QC commands
geho " ----- Starting Turnkey Processing -----"; echo ""; echo ""
geho " ---------------------------------------"; echo ""; echo ""

# =-=-=-=-=-=-= TURNKEY COMMANDS START =-=-=-=-=-=-= 
#
#
	# -- Create study hieararchy and generate subject folders
	turnkey_createStudy() {
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
	}
	
	# -- Get data from original location & organize DICOMs
	turnkey_organizeDicom() {
		if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
			geho " -- Fetching batch and mapping files from ${XNAT_HOST_NAME}"; echo ""
			curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/919/files/${BATCH_PARAMETERS_FILENAME}" > ${specsdir}/${BATCH_PARAMETERS_FILENAME}
			curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/919/files/${SCAN_MAPPING_FILENAME}" > ${specsdir}/${SCAN_MAPPING_FILENAME} 
			echo ""
			geho " -- Linking DICOMs into ${rawdir}"; echo ""
			find /input/SCANS/ -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" -exec ln -s '{}' ${rawdir}/ ';' &> /dev/null
		else
			reho " ===> Turnkey for local study execution not yet supported!"; echo ""; exit 0
		fi
		mnap organizeDicom --subjectsfolder="${mnap_subjectsfolder}" --subjects="${XNAT_SESSION_LABELS}" --overwrite="${OVERWRITE}"
	}
	
	# -- Map processing folder structure
	turnkey_getHCPReady() {
		mnap getHCPReady   --subjectsfolder="${mnap_subjectsfolder}" --subjects="${XNAT_SESSION_LABELS}" --mapping="${specsdir}/${SCAN_MAPPING_FILENAME}" --overwrite="${OVERWRITE}"
	}
	
	# -- Generate subject specific hcp processing file
	turnkey_mapHCPFiles() {
		mnap mapHCPFiles   --subjectsfolder="${mnap_subjectsfolder}" --subjects="${XNAT_SESSION_LABELS}" --overwrite="${OVERWRITE}"
		geho " -- Generating ${project_batch_file}"; echo ""
		cp ${specsdir}/${BATCH_PARAMETERS_FILENAME} ${project_batch_file}; cat ${mnap_workdir}/subject_hcp.txt >> ${project_batch_file}
	}
	
	# -- HCP processing steps and relevant QC
	turnkey_hcp1() {
		mnap hcp1      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --logfolder="${logdir}"
	}
	turnkey_hcp2() {
		mnap hcp2      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --logfolder="${logdir}"
	}
	turnkey_hcp3() {
		mnap hcp3      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --logfolder="${logdir}"
		mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/T1w"    --modality="T1w"    --overwrite="${OVERWRITE}"
		mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/T2w"    --modality="T2w"    --overwrite="${OVERWRITE}"
	}
	turnkey_hcp4() {
		mnap hcp4      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}"
	}
	turnkey_hcp5() {
		mnap hcp5      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}"
		mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/BOLD"   --modality="BOLD"   --overwrite="${OVERWRITE}" --boldsuffix="_Atlas"
	}
	turnkey_hcpd() {
		mnap hcpd      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}"
		mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/DWI"    --modality="DWI"    --overwrite="${OVERWRITE}" --dwidata="data" --dwipath="Diffusion"
	}
	turnkey_hcpdLegacy() {
		cyanecho "-- PENDING: hcpdLegacy processing steps and relevant QC go here... "
		# mnap hcpdLegacy --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --scanner="${Scanner}" --usefieldmap="${UseFieldmap}" --echospacing="${EchoSpacing}" --PEdir="{PEdir}" --unwarpdir="${UnwarpDir}" --diffdatasuffix="${DiffDataSuffix}" --TE="${TE}"
		# mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/DWI"    --modality="DWI"    --overwrite="${OVERWRITE}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion"
	}
	
	# -- FSLDtifit processing steps and relevant QC
	turnkey_FSLDtifit() {
		mnap FSLDtifit --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}"
	}
	
	# -- FSLBedpostxGPU processing steps and relevant QC
	turnkey_FSLBedpostxGPU() {
		if [ -z "$Fibers" ]; then Fibers="3"; fi
		if [ -z "$Model" ]; then Model="3"; fi
		if [ -z "$Burnin" ]; then Burnin="3000"; fi
		if [ -z "$Rician" ]; then Rician="yes"; fi
		mnap FSLBedpostxGPU --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --fibers="${Fibers}" --burnin="${Burnin}" --model="${Model}" --rician="${Rician}"
	}
	
	# -- eddyQC processing steps and relevant QC
	turnkey_eddyQC() {
		cyanecho "-- PENDING: eddyQC processing steps and relevant QC go here... "
		# mnap eddyQC --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --eddybase="eddy_unwarped_images" --report="individual" --bvalsfile="Pos_Neg.bvals" --mask="nodif_brain_mask.nii.gz" --eddyidx="index.txt" --eddyparams="acqparams.txt" --bvecsfile="Pos_Neg.bvecs"
	}
	
	# -- Processing for DWI analyses
	turnkey_QCPreprocDWIProcess() {
		cyanecho "-- PENDING: QCPreproc processing steps for DWI analyses... "
		#mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --outpath="${mnap_subjectsfolder}/QC/DWI" --modality="DWI" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --dtifitqc="yes" --bedpostxqc="yes" --eddyqcpdf="yes"
	}
	
	# -- Pre-tractography for DWI data
	turnkey_pretractographyDense() {
		cyanecho "-- PENDING: pretractographyDense steps for DWI analyses... "
		# mnap pretractographyDense --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --omatrix1="yes" --omatrix3="yes"
	}
	
	# -- Pre-tractography for DWI data
	turnkey_DWIDenseParcellation() {
		cyanecho "-- PENDING: DWIDenseParcellation steps for DWI analyses... "
		# mnap DWIDenseParcellation --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --waytotal="${WayTotal}" --matrixversion="${MatrixVersion}" --parcellationfile="${ParcellationFile}" --outname="${DWIOutName}"
	}
	
	# -- Pre-tractography for DWI data
	turnkey_DWISeedTractography() {
		cyanecho "-- PENDING: DWISeedTractography steps for DWI analyses... "
		# mnap DWISeedTractography --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --waytotal="${WayTotal}" --matrixversion="${MatrixVersion}" --outname="${DWIOutName}" --matrixversion='1' --seedfile="${SeedFile}"
		# mnap DWISeedTractography --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE}" --waytotal="${WayTotal}" --matrixversion="${MatrixVersion}" --outname="${DWIOutName}_GBC" --matrixversion='1' --seedfile="gbc"
	}
	
	# -- Check if Custom QC was requested
	turnkey_QCPreprocCustom() {
		Modalities="T1w, T2w, myelin, BOLD, DWI"
		for Modality in ${Modalities}; do
			if [[ ${Modality} == "BOLD" ]]; then
				mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE}" --boldsuffix="Atlas" --processcustom="yes" --omitdefaults="yes"
			fi
			if [[ ${Modality} == "DWI" ]]; then
				mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}"  --overwrite="${OVERWRITE}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --processcustom="yes" --omitdefaults="yes"
			else
				mnap QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}"  --overwrite="${OVERWRITE}" --processcustom="yes" --omitdefaults="yes"
			fi
		done
	}
	
	# -- Map HCP processed outputs for further FC BOLD analyses
	turnkey_mapHCPData() {
		cyanecho "-- PENDING: mapHCPData processing steps go here... "
		mnap mapHCPData \
		--subjects="${project_batch_file}" \
		--subjectsfolder="${mnap_subjectsfolder}" \
		--overwrite="${OVERWRITE}"
	}
	
	# -- Generate brain masks for de-noising
	turnkey_createBOLDBrainMasks() {
		cyanecho "-- PENDING: createBOLDBrainMasks processing steps go here... "
		mnap createBOLDBrainMasks \
		--subjects="${project_batch_file}" \
		--subjectsfolder="${mnap_subjectsfolder}" \
		--overwrite="${OVERWRITE}" \
		--logfolder="${logdir}" \
		--image_target="nifti"
	}
	
	# -- Compute BOLD statistics
	turnkey_computeBOLDStats() {
	cyanecho "-- PENDING: computeBOLDStats processing steps go here... "
		mnap computeBOLDStats \
		--subjects="${project_batch_file}" \
		--subjectsfolder="${mnap_subjectsfolder}" \
		--logfolder="${logdir}" \
		--overwrite="${OVERWRITE}" \
		--image_target="nifti"
	}
	
	# -- Create final BOLD statistics report
	turnkey_createStatsReport() {
		cyanecho "-- PENDING: createStatsReport processing steps go here... "
		mnap createStatsReport \
		--subjects="${project_batch_file}" \
		--subjectsfolder="${mnap_subjectsfolder}" \
		--logfolder="${logdir}" \
		--overwrite="${OVERWRITE}"
	}
	
	# -- Extract nuisance signal for further de-noising
	turnkey_extractNuisanceSignal() {
		cyanecho "-- PENDING: extractNuisanceSignal processing steps go here... "
		mnap extractNuisanceSignal \
		--subjects="${project_batch_file}" \
		--subjectsfolder="${mnap_subjectsfolder}" \
		--logfolder="${logdir}" \
		--overwrite="${OVERWRITE}"
	}
	
	# -- Process BOLDs
	turnkey_preprocessBold() {
	cyanecho "-- PENDING: preprocessBold processing steps go here... "
		mnap preprocessBold \
		--subjects="${project_batch_file}" \
		--subjectsfolder="${mnap_subjectsfolder}" \
		--logfolder="${logdir}" \
		--overwrite="${OVERWRITE}"
	}
	
	# -- Process via CONC file
	turnkey_preprocessConc() {
		cyanecho "-- PENDING: preprocessConc processing steps go here... "
		mnap preprocessConc \
		--subjects="${project_batch_file}" \
		--subjectsfolder="${mnap_subjectsfolder}" \
		--overwrite="${OVERWRITE}" \
		--logfolder="${logdir}"
	}
	
	# -- Compute GBC
	turnkey_computeBOLDfcGBC() {
	cyanecho "-- PENDING: computeBOLDfc processing steps for GBC go here... "
		InputFile="bold1_Atlas_scrub_g7_hpss_res-VWMWB.dtseries.nii"
		OutName="GBC_bold1_Atlas_scrub_g7_hpss_res-VWMWB"
		Ignore=""
		# mnap computeBOLDfc \
		# --subjectsfolder="${mnap_subjectsfolder}" \
		# --calculation="gbc" \
		# --runtype="individual" \
		# --subjects="${project_batch_file}" \
		# --inputfiles="${InputFile}" \
		# --inputpath="images/functional" \
		# --extractdata="yes" \
		# --outname="${OutName}" \
		# --overwrite="${OVERWRITE}" \
		# --ignore="${Ignore}" \
		# --target=[] \
		# --command="mFz:" \
		# --targetf="${mnap_subjectsfolder}/${CASE}/images/functional" \
		# --mask="5" \
		# --rsmooth="0" \
		# --rdilate="0" \
		# --verbose="true" \
		# --time="true" \
		# --vstep="1000" \
		# --covariance="true"
	}
	
	# -- Compute Seed FC for relevant ROIs
	turnkey_computeBOLDfcSeed() {
	cyanecho "-- PENDING: computeBOLDfc processing steps for seeds go here... "
		# mnap computeBOLDfc \
		# --subjectsfolder="${mnap_subjectsfolder}" \
		# --function="computeboldfc" \
		# --calculation="seed" \
		# --runtype="individual" \
		# --subjects="${project_batch_file}" \
		# --inputfiles="bold1_Atlas_scrub_g7_hpss_res-VWMWB_lpss.dtseries.nii" \
		# --inputpath="images/functional" \
		# --extractdata="yes" \
		# --outname="boldRest1AtlasScrubHPSSg7resVWMWB" \
		# --overwrite="${OVERWRITE}" \
		# --roinfo="/gpfs/project/fas/n3/software/MNAP/general/templates/Thalamus_Atlas/Thal.FSL.Associative.Sensory.MNI152.CIFTI.Atlas.names" \
		# --ignore="udvarsme" \
		# --options="" \
		# --method="" \
		# --targetf="" \
		# --mask="0" \
		# --covariance="true"
	}
#
#
# =-=-=-=-=-=-= TURNKEY COMMANDS END =-=-=-=-=-=-= 

# -- Check turnkey steps and execute
if [ "$TURNKEY_STEPS" == "all" ]; then
	geho "==> Running all Turkey workflow steps: ${MNAPTurnkeyWorkflow}"; echo ""
	for MNAPTurnkeyWorkflowStep in ${MNAPTurnkeyWorkflow}; do
		turnkey_${MNAPTurnkeyWorkflowStep}
	done
fi
if [ "$TURNKEY_STEPS" != "all" ]; then
	TURNKEY_STEPS
	geho "==> Running specific Turkey workflow steps: ${TURNKEY_STEPS}"; echo ""
	for TURNKEY_STEP in ${TURNKEY_STEPS}; do
		turnkey_${TURNKEY_STEP}
	done
fi

echo ""; echo ""
geho " ---- Turnkey Processing Calls done ----"; echo ""; echo ""
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
	geho "------------------------- Successful completion of work --------------------------------"
	echo ""
fi
}

main
