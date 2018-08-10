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

source /opt/mnaptools/library/environment/mnap_environment.sh

$TOOLS/$MNAPREPO/library/environment/mnap_environment.sh &> /dev/null
MNAPTurnkeyWorkflow="createStudy mapRawData organizeDicom getHCPReady mapHCPFiles hcp1 hcp2 hcp3 hcp4 hcp5 hcpd FSLDtifit FSLBedpostxGPU eddyQC QCPreprocDWIProcess pretractographyDense DWIDenseParcellation DWISeedTractography QCPreprocCustom mapHCPData createBOLDBrainMasks computeBOLDStats createStatsReport extractNuisanceSignal preprocessBold preprocessConc computeBOLDfcGBC computeBOLDfcSeed"

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
    echo "    --turnkeytype=<turnkey_run_type>              Specify type turnkey run. Options are: local or xnat"
    echo "                                                  If empty default is set to: [xnat]."
    echo "  -- XNAT HOST & PROJECT PARMETERS:"
    echo ""
    echo "    --batch=<batch_file>                          Batch file with processing parameters which exist as a project-level resource on XNAT"
    echo "    --mappingfile=<mapping_file>                  File for mapping into desired file structure, e.g. hcp, which exist as a project-level resource on XNAT"
    echo "    --xnatprojectid=<name_of_xnat_project_id>     Specify the XNAT site project id. This is the Project ID in XNAT and not the Project Title."
    echo "    --xnathost=<XNAT_site_URL>                    Specify the XNAT site hostname URL to push data to."
    echo "    --xnatsessionlabels=<session_id>              Name of session within XNAT for a given subject id. If not provided then --subjects is needed."
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
    echo "    --overwritestep=<specify_step_to_overwrite>        Specify <yes> or <no> for cleanup of prior workflow step. Default is [no]."
    echo "    --overwritesubject=<specify_subject_overwrite>     Specify <yes> or <no> for cleanup of prior subject run. Default is [no]."
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
    echo "   --overwritestep=yes \ "
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
unset OVERWRITE_STEP
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
unset TURNKEY_STEPS

# =-=-=-=-=-= GENERAL OPTIONS =-=-=-=-=-=

# -- General input flags
STUDY_PATH=`opts_GetOpt "--path" $@`
CASES=`opts_GetOpt "--subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'`
OVERWRITE_SUBJECT=`opts_GetOpt "--overwritesubject" $@`
OVERWRITE_STEP=`opts_GetOpt "--overwritestep" $@`
OVERWRITE_PROJECT=`opts_GetOpt "--overwriteproject" $@`
BATCH_PARAMETERS_FILENAME=`opts_GetOpt "--batchfile" $@`
SCAN_MAPPING_FILENAME=`opts_GetOpt "--mappingfile" $@`
XNAT_ACCSESSION_ID=`opts_GetOpt "--xnataccsessionid" $@`
XNAT_SESSION_LABELS=`opts_GetOpt "--xnatsessionlabels" $@`
XNAT_PROJECT_ID=`opts_GetOpt "--xnatprojectid" $@`
XNAT_SUBJECT_ID=`opts_GetOpt "--xnatsubjectid" $@`
XNAT_HOST_NAME=`opts_GetOpt "--xnathost" $@`
XNAT_USER_NAME=`opts_GetOpt "--xnatuser" $@`
XNAT_PASSWORD=`opts_GetOpt "--xnatpass" $@`
TURNKEY_STEPS=`opts_GetOpt "--turnkeysteps" $@`
TURNKEY_TYPE=`opts_GetOpt "--turnkeytype" $@`

# =-=-=-=-=-= BOLD FC OPTIONS =-=-=-=-=-=

# -- computeBOLDfc input flags
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

# =-=-=-=-=-= DIFFUSION OPTIONS =-=-=-=-=-=

# -- hcpdLegacy input flags
EchoSpacing=`opts_GetOpt "--echospacing" $@`
PEdir=`opts_GetOpt "--PEdir" $@`
TE=`opts_GetOpt "--TE" $@`
UnwarpDir=`opts_GetOpt "--unwarpdir" $@`
DiffDataSuffix=`opts_GetOpt "--diffdatasuffix" $@`
Scanner=`opts_GetOpt "--scanner" $@`
UseFieldmap=`opts_GetOpt "--usefieldmap" $@`
# -- DWIDenseParcellation input flags
MatrixVersion=`opts_GetOpt "--matrixversion" $@`
ParcellationFile=`opts_GetOpt "--parcellationfile" $@`
OutName=`opts_GetOpt "--outname" $@`
WayTotal=`opts_GetOpt "--waytotal" $@`
# -- DWISeedTractography input flags
SeedFile=`opts_GetOpt "--seedfile" $@`
# -- eddyQC input flags
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
# -- FSLBedpostxGPU input flags
Fibers=`opts_GetOpt "--fibers" $@`
Model=`opts_GetOpt "--model" $@`
Burnin=`opts_GetOpt "--burnin" $@`
Jumps=`opts_GetOpt "--jumps" $@`
Rician=`opts_GetOpt "--rician" $@`
# -- probtrackxGPUDense input flags
MatrixOne=`opts_GetOpt "--omatrix1" $@`
MatrixThree=`opts_GetOpt "--omatrix3" $@`
NsamplesMatrixOne=`opts_GetOpt "--nsamplesmatrix1" $@`
NsamplesMatrixThree=`opts_GetOpt "--nsamplesmatrix3" $@`

# =-=-=-=-=-= QC OPTIONS =-=-=-=-=-=

# -- QCPreproc input flags
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
DWILegacy=`opts_GetOpt "--dwilegacy" $@`
BOLDDATA=`opts_GetOpt "--bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDDATA=`echo "$BOLDDATA" | sed 's/,/ /g;s/|/ /g'`
BOLDRUNS=`opts_GetOpt "--boldruns" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDRUNS=`echo "$BOLDRUNS" | sed 's/,/ /g;s/|/ /g'`
BOLDS=`opts_GetOpt "--bolds" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`
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
BOLDSuffix=`opts_GetOpt "--boldsuffix" $@`
BOLDPrefix=`opts_GetOpt "--boldprefix" $@`
SkipFrames=`opts_GetOpt "--skipframes" $@`
SNROnly=`opts_GetOpt "--snronly" $@`
TimeStamp=`opts_GetOpt "--timestamp" $@`
Suffix=`opts_GetOpt "--suffix" $@`
SceneZip=`opts_GetOpt "--scenezip" $@`
QCPreprocCustom=`opts_GetOpt "--customqc" $@`

# -- Check if subject input is a parameter file instead of list of cases
echo ""
if [[ ${CASES} == *.txt ]]; then
    SubjectParamFile="$CASES"
    echo ""
    echo "Using $SubjectParamFile for input."
    echo ""
    CASES=`more ${SubjectParamFile} | grep "id:"| cut -d " " -f 2`
fi

# -- Check that all inputs are provided
if [ -z "$CASES" ]; then
     if [ -z "$XNAT_SESSION_LABELS" ]; then
        reho "Error: --xnatsessionlabels or --subjects flag missing. Specify one."; echo ''
        exit 1
    fi
fi
if [ -z "$TURNKEY_TYPE" ]; then TURNKEY_TYPE="xnat"; reho "Note: Setting turnkey to: $TURNKEY_TYPE"; echo ''; fi
if [ -z "$TURNKEY_STEPS" ]; then reho "Turnkey steps flag missing. Specify turnkey steps:"; geho " ===> ${MNAPTurnkeyWorkflow}"; echo ''; exit 1; fi
if [[ ${TURNKEY_STEPS} == "mapRawData" ]] || [[ ${TURNKEY_STEPS} == "all" ]]; then
    if [ -z "$BATCH_PARAMETERS_FILENAME" ]; then reho "Error: --batchfile flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    if [ -z "$SCAN_MAPPING_FILENAME" ]; then reho "Error: --mappingfile flag missing. Batch parameter file not specified."; echo ''; exit 1;  fi
fi
if [[ ${TURNKEY_STEPS} == "mapHCPFiles" ]]; then
    if [ -z "$BATCH_PARAMETERS_FILENAME" ]; then reho "Error: --batchfile flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
fi
if [[ ${TURNKEY_STEPS} == "getHCPReady" ]]; then
    if [ -z "$SCAN_MAPPING_FILENAME" ]; then reho "Error: --mappingfile flag missing. Batch parameter file not specified."; echo ''; exit 1;  fi
fi
if [[ "$TURNKEY_TYPE" == "xnat" ]]; then
    if [ -z "$XNAT_PROJECT_ID" ]; then reho "Error: --xnatprojectid flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    if [ -z "$XNAT_HOST_NAME" ]; then reho "Error: --xnathost flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    if [ -z "$XNAT_USER_NAME" ]; then reho "Error: --xnatuser flag missing. Username parameter file not specified."; echo ''; exit 1; fi
    if [ -z "$XNAT_PASSWORD" ]; then reho "Error: --xnatpass flag missing. Password parameter file not specified."; echo ''; exit 1; fi
fi

if [ -z "$OVERWRITE_STEP" ]; then OVERWRITE_STEP="no"; fi
if [ -z "$OVERWRITE_SUBJECT" ]; then OVERWRITE_SUBJECT="no"; fi
if [ -z "$OVERWRITE_PROJECT" ]; then OVERWRITE_PROJECT="no"; fi
if [ -z "$STUDY_PATH" ]; then STUDY_PATH="/output/${XNAT_PROJECT_ID}"; reho "Note: Study path missing. Setting defaults: $STUDY_PATH"; echo ''; fi
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
logdir="${mnap_studyfolder}/processing/logs"
specsdir="${mnap_subjectsfolder}/specs"
rawdir="${mnap_workdir}/inbox"
rawdir_temp="${mnap_workdir}/inbox_temp"
processingdir="${mnap_studyfolder}/processing"
project_batch_file="${processingdir}/${XNAT_PROJECT_ID}_batch_params.txt"
MNAPCOMMAND="${TOOLS}/${MNAPREPO}/connector/mnap.sh"

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
echo "   Overwrite for a given turnkey step set to: ${OVERWRITE_STEP}"
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
geho "------------------------- Start of MNAP Turnkey Workflow --------------------------------"
echo ""

# -- Check if overwrite is set to yes for subject and project
if [[ ${OVERWRITE_PROJECT} == "yes" ]] && [[ ${TURNKEY_STEPS} == "all" ]]; then
    if [[ `ls -IQC -Ilists -Ispecs -Iinbox -Iarchive ${mnap_subjectsfolder}` == "$XNAT_SESSION_LABELS" ]]; then
        reho "-- ${XNAT_SESSION_LABELS} is the only folder in ${mnap_subjectsfolder}. OK to proceed!"
        reho "   Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${mnap_studyfolder}/ &> /dev/null
    else
        reho "-- There are more than ${XNAT_SESSION_LABELS} directories ${mnap_studyfolder}."
        reho "   Skipping recursive overwrite for project: ${XNAT_PROJECT_ID}"; echo ""
    fi
fi

if [[ ${OVERWRITE_PROJECT} == "yes" ]] && [[ ${TURNKEY_STEPS} == "createStudy" ]]; then
    if [[ `ls -IQC -Ilists -Ispecs -Iinbox -Iarchive ${mnap_subjectsfolder}` == "$XNAT_SESSION_LABELS" ]]; then
        reho "-- ${XNAT_SESSION_LABELS} is the only folder in ${mnap_subjectsfolder}. OK to proceed!"
        reho "   Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${mnap_studyfolder}/ &> /dev/null
    else
        reho "-- There are more than ${XNAT_SESSION_LABELS} directories ${mnap_studyfolder}."
        reho "   Skipping recursive overwrite for project: ${XNAT_PROJECT_ID}"; echo ""
    fi
fi

if [[ ${OVERWRITE_SUBJECT} == "yes" ]]; then
    reho "-- Removing specific subject: ${mnap_workdir}."; echo ""
    rm -rf ${mnap_workdir} &> /dev/null
fi

# =-=-=-=-=-=-= TURNKEY COMMANDS START =-=-=-=-=-=-= 
#
#
    # --------------- Intial study and file organization start -----------------
    #
       # -- Create study hieararchy and generate subject folders
       turnkey_createStudy() {
           TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
           createStudy_Runlog="${logdir}/runlogs/Log-createStudy_${TimeStamp}.log"
           createStudy_ComlogTmp="/output/tmp_createStudy_${XNAT_SESSION_LABELS}_${TimeStamp}.log"; touch ${createStudy_ComlogTmp}; chmod 777 ${createStudy_ComlogTmp}
           createStudy_ComlogError="${logdir}/comlogs/error_createStudy_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
           createStudy_ComlogDone="${logdir}/comlogs/done_createStudy_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
           cyaneho "-- RUNNING createStudy..."
           echo ""
           geho " -- Checking for and generating study folder ${mnap_studyfolder}"; echo ""
           if [ ! -d ${workdir} ]; then
               mkdir -p ${workdir} &> /dev/null
           fi
           if [ ! -d ${mnap_studyfolder} ]; then
               ${MNAPCOMMAND} createStudy --studyfolder="${mnap_studyfolder}" 2>&1 | tee -a ${createStudy_ComlogTmp}
               mv ${createStudy_ComlogTmp} ${logdir}/comlogs/
               createStudy_ComlogTmp="${logdir}/comlogs/tmp_createStudy_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
           else
               createStudy_ComlogTmp="${logdir}/comlogs/tmp_createStudy_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
               geho " -- Study folder ${mnap_studyfolder} already exits!" 2>&1 | tee -a ${createStudy_ComlogTmp}
           fi
           mkdir -p ${mnap_workdir} &> /dev/null
           mkdir -p ${mnap_workdir}/inbox &> /dev/null
           mkdir -p ${mnap_workdir}/inbox_temp &> /dev/null
           if [ -f ${mnap_studyfolder}/.mnapstudy ]; then CREATESTUDYCHECK="pass"; else CREATESTUDYCHECK="fail"; fi
           if [[ ${CREATESTUDYCHECK} == "pass" ]]; then
               echo "" >> ${createStudy_ComlogTmp}
               echo "------------------------- Successful completion of work --------------------------------" >> ${createStudy_ComlogTmp}
               echo "" >> ${createStudy_ComlogTmp}
               mv ${createStudy_ComlogTmp} ${createStudy_ComlogDone}
               createStudy_Comlog=${createStudy_ComlogDone}
           else
              echo "" >> ${createStudy_ComlogTmp}
              echo "Error. Something went wrong." >> ${createStudy_ComlogTmp}
              echo "" >> ${createStudy_ComlogTmp}
              mv ${createStudy_ComlogTmp} ${createStudy_ComlogError}
              createStudy_Comlog=${createStudy_ComlogError}
          fi
       }
       # -- Get data from original location & organize DICOMs
       turnkey_mapRawData() {
           TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
           # -- Define specific logs
           mapRawData_Runlog="${logdir}/runlogs/Log-mapRawData_${TimeStamp}.log"
           mapRawData_ComlogTmp="${logdir}/comlogs/tmp_mapRawData_${XNAT_SESSION_LABELS}_${TimeStamp}.log"; touch ${mapRawData_ComlogTmp}; chmod 777 ${mapRawData_ComlogTmp}
           mapRawData_ComlogError="${logdir}/comlogs/error_mapRawData_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
           mapRawData_ComlogDone="${logdir}/comlogs/done_mapRawData_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
           if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
               rm -rf ${specsdir}/${BATCH_PARAMETERS_FILENAME} &> /dev/null
               rm -rf ${specsdir}/${SCAN_MAPPING_FILENAME} &> /dev/null
               rm -rf ${processingdir}/scenes/QC/* &> /dev/null
               if [[ ${OVERWRITE_STEP} == "yes" ]]; then
                  rm ${rawdir}/*
               fi
               geho " -- Fetching batch and mapping files from ${XNAT_HOST_NAME}"; echo ""
               echo "" >> ${mapRawData_ComlogTmp}
               geho "  Logging turnkey_mapRawData output at time ${TimeStamp}:" >> ${mapRawData_ComlogTmp}
               echo "----------------------------------------------------------------------------------------" >> ${mapRawData_ComlogTmp}
               echo "" >> ${mapRawData_ComlogTmp}
               echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${BATCH_PARAMETERS_FILENAME}"" >> ${mapRawData_ComlogTmp}
               echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${SCAN_MAPPING_FILENAME}"" >> ${mapRawData_ComlogTmp}
               curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${BATCH_PARAMETERS_FILENAME}" > ${specsdir}/${BATCH_PARAMETERS_FILENAME}
               curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${SCAN_MAPPING_FILENAME}" > ${specsdir}/${SCAN_MAPPING_FILENAME}
               #curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/scenes_qc/*" > ${processingdir}/scenes/QC/
               echo ""
               geho " -- Linking DICOMs into ${rawdir}"; echo ""
               echo "  find /input/SCANS/ -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" -exec ln -s '{}' ${rawdir}/ ';'" >> ${mapRawData_ComlogTmp}
               find /input/SCANS/ -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" -exec ln -s '{}' ${rawdir}/ ';' &> /dev/null
               # -- Perform checks
               DicomInputCount=`find /input/SCANS/ -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" | wc | awk '{print $1}'`
               DicomMappedCount=`ls ${rawdir}/* | wc | awk '{print $1}'`
               if [[ ${DicomInputCount} == ${DicomMappedCount} ]]; then DICOMCOUNTCHECK="pass"; else DICOMCOUNTCHECK="fail"; fi
               if [[ -f ${specsdir}/${BATCH_PARAMETERS_FILENAME} ]]; then BATCHFILECHECK="pass"; else BATCHFILECHECK="fail"; fi
               if [[ -f ${specsdir}/${SCAN_MAPPING_FILENAME} ]]; then MAPPINGFILECHECK="pass"; else MAPPINGFILECHECK="fail"; fi
               echo "" >> ${mapRawData_ComlogTmp}
               echo "----------------------------------------------------------------------------" >> ${mapRawData_ComlogTmp}
               echo "  --> Batch file transfer check: ${BATCHFILECHECK}" >> ${mapRawData_ComlogTmp}
               echo "  --> Mapping file transfer check: ${MAPPINGFILECHECK}" >> ${mapRawData_ComlogTmp}
               echo "  --> DICOM file count in input folder /input/SCANS: ${DicomInputCount}" >> ${mapRawData_ComlogTmp}
               echo "  --> DICOM file count in output folder ${rawdir}: ${DicomMappedCount}" >> ${mapRawData_ComlogTmp}
               echo "  --> DICOM mapping check: ${DICOMCOUNTCHECK}" >> ${mapRawData_ComlogTmp}
               echo "----------------------------------------------------------------------------" >> ${mapRawData_ComlogTmp}
               if [[ ${DICOMCOUNTCHECK} == "pass" ]] && [[ ${BATCHFILECHECK} == "pass" ]] && [[ ${MAPPINGFILECHECK} == "pass" ]]; then
                   echo "" >> ${mapRawData_ComlogTmp}
                   geho "------------------------- Successful completion of work --------------------------------" >> ${mapRawData_ComlogTmp}
                   echo "" >> ${mapRawData_ComlogTmp}
                  mv ${mapRawData_ComlogTmp} ${mapRawData_ComlogDone}
                  mapRawData_Comlog=${mapRawData_ComlogDone}
               else
                   echo "" >> ${mapRawData_ComlogTmp}
                   echo "Error. Something went wrong." >> ${mapRawData_ComlogTmp}
                   echo "" >> ${mapRawData_ComlogTmp}
                  mv ${mapRawData_ComlogTmp} ${mapRawData_ComlogError}
                  mapRawData_Comlog=${mapRawData_ComlogError}
               fi
               unset XNAT_PASSWORD
               unset XNAT_USER_NAME
           else
               reho " ===> Turnkey for local study execution not yet supported!"; echo ""; exit 0
           fi
       }
       # -- organize DICOMs
       turnkey_organizeDicom() {
           cyaneho "-- RUNNING organizeDicom..."
           ${MNAPCOMMAND} organizeDicom --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}"
       }
       # -- Map processing folder structure
       turnkey_getHCPReady() {
           cyaneho "-- RUNNING getHCPReady..."
           ${MNAPCOMMAND} getHCPReady   --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --mapping="${specsdir}/${SCAN_MAPPING_FILENAME}" --overwrite="${OVERWRITE_STEP}"
       }
       # -- Generate subject specific hcp processing file
       turnkey_mapHCPFiles() {
           cyaneho "-- RUNNING mapHCPFiles..."
           ${MNAPCOMMAND} mapHCPFiles   --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}"
           geho " -- Generating ${project_batch_file}"; echo ""
           if [[ ${OVERWRITE_STEP} == "yes" ]]; then
              rm ${project_batch_file}
           fi
           cp ${specsdir}/${BATCH_PARAMETERS_FILENAME} ${project_batch_file}; cat ${mnap_workdir}/subject_hcp.txt >> ${project_batch_file}
       }
    #
    # --------------- Intial study and file organization end -------------------
    

    # --------------- HCP Processing and relevant QC start ---------------------
    #
       # -- PreFreeSurfer
       turnkey_hcp1() {
           cyaneho "-- RUNNING HCP Pipelines step: hcp1 (hcp_PreFS)"
           HCPLogName="hcpPreFS"
           ${MNAPCOMMAND} hcp1      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}"
       }
       # -- FreeSurfer
       turnkey_hcp2() {
           cyaneho "-- RUNNING HCP Pipelines step: hcp2 (hcp_FS)"
           HCPLogName="hcpFS"
           ${MNAPCOMMAND} hcp2      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}"
       }
       # -- PostFreeSurfer
       turnkey_hcp3() {
           cyaneho "-- RUNNING HCP Pipelines step: hcp3 (hcp_PostFS)"
           HCPLogName="hcpPostFS"
           ${MNAPCOMMAND} hcp3      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}"
           ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/T1w"    --modality="T1w"    --overwrite="${OVERWRITE_STEP}"
           if [ -z `ls -t1 *_${QCPreproc}*log 2>/dev/null | head -n 1` ]; then 
              CheckLogQCT1w=""
           else
              CheckLogQCT1w=`ls -t1 *_${QCPreproc}*log | head -n 1`
           fi
           ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/T2w"    --modality="T2w"    --overwrite="${OVERWRITE_STEP}"
           if [ -z `ls -t1 *_${QCPreproc}*log 2>/dev/null | head -n 1` ]; then 
              CheckLogQCT2w=""
           else
              CheckLogQCT2w=`ls -t1 *_${QCPreproc}*log | head -n 1`
           fi
           ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/myelin"  --modality="myelin" --overwrite="${OVERWRITE_STEP}"
           if [ -z `ls -t1 *_${QCPreproc}*log 2>/dev/null | head -n 1` ]; then 
              CheckLogQCMyelin=""
           else
              CheckLogQCMyelin=`ls -t1 *_${QCPreproc}*log | head -n 1`
           fi
       }
       # -- fMRIVolume
       turnkey_hcp4() {
           cyaneho "-- RUNNING HCP Pipelines step: hcp4 (hcp_fMRIVolume)"
           HCPLogName="hcpfMRIVolume"
           ${MNAPCOMMAND} hcp4      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}"
       }
       # -- fMRISurface
       turnkey_hcp5() {
           cyaneho "-- RUNNING HCP Pipelines step: hcp4 (hcp_fMRISurface)"
           HCPLogName="hcpfMRISurface"
           ${MNAPCOMMAND} hcp5      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}"
           ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/BOLD"   --modality="BOLD"   --overwrite="${OVERWRITE_STEP}" --boldsuffix="_Atlas"
           if [ -z `ls -t1 *_${QCPreproc}*log 2>/dev/null | head -n 1` ]; then 
              CheckLogQCTBOLD=""
           else
              CheckLogQCTBOLD=`ls -t1 *_${QCPreproc}*log | head -n 1`
           fi
       }
       # -- Diffusion
       turnkey_hcpd() {
       cyaneho "-- RUNNING HCP Pipelines step: hcp4 (hcp_Diffusion)"
           HCPLogName="hcpDiffusion"
           ${MNAPCOMMAND} hcpd      --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}"
           ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/DWI"    --modality="DWI"    --overwrite="${OVERWRITE_STEP}" --dwidata="data" --dwipath="Diffusion"
           if [ -z `ls -t1 *_${QCPreproc}*log 2>/dev/null | head -n 1` ]; then 
              CheckLogQCDWI=""
           else
              CheckLogQCDWI=`ls -t1 *_${QCPreproc}*log | head -n 1`
           fi
       }
       # -- Diffusion Legacy
       turnkey_hcpdLegacy() {
           cyaneho "-- PENDING: HCP Pipelines step: hcpdLegacy"
           # ${MNAPCOMMAND} hcpdLegacy --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --scanner="${Scanner}" --usefieldmap="${UseFieldmap}" --echospacing="${EchoSpacing}" --PEdir="{PEdir}" --unwarpdir="${UnwarpDir}" --diffdatasuffix="${DiffDataSuffix}" --TE="${TE}"
           # ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/DWI"    --modality="DWI"    --overwrite="${OVERWRITE_STEP}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion"
       }
    #
    # --------------- HCP Processing and relevant QC end -----------------------


    # --------------- DWI Processing and analyses start ------------------------
    #
       # -- FSLDtifit processing steps and relevant QC
       turnkey_FSLDtifit() {
           cyaneho "-- PENDING: FSLDtifit for DWI... "
           ${MNAPCOMMAND} FSLDtifit --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}"
       }
       # -- FSLBedpostxGPU processing steps and relevant QC
       turnkey_FSLBedpostxGPU() {
           cyaneho "-- PENDING: FSLBedpostxGPU for DWI... "
           if [ -z "$Fibers" ]; then Fibers="3"; fi
           if [ -z "$Model" ]; then Model="3"; fi
           if [ -z "$Burnin" ]; then Burnin="3000"; fi
           if [ -z "$Rician" ]; then Rician="yes"; fi
           ${MNAPCOMMAND} FSLBedpostxGPU --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --fibers="${Fibers}" --burnin="${Burnin}" --model="${Model}" --rician="${Rician}"
       }
       # -- eddyQC processing steps and relevant QC
       turnkey_eddyQC() {
           cyaneho "-- PENDING: eddyQC for DWI... "
           # ${MNAPCOMMAND} eddyQC --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --eddybase="eddy_unwarped_images" --report="individual" --bvalsfile="Pos_Neg.bvals" --mask="nodif_brain_mask.nii.gz" --eddyidx="index.txt" --eddyparams="acqparams.txt" --bvecsfile="Pos_Neg.bvecs"
       }
       # -- Processing for DWI analyses
       turnkey_QCPreprocDWIProcess() {
           cyaneho "-- PENDING: QCPreproc processing steps for DWI analyses... "
           #${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --outpath="${mnap_subjectsfolder}/QC/DWI" --modality="DWI" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --dtifitqc="yes" --bedpostxqc="yes" --eddyqcpdf="yes"
       }
       # -- Pre-tractography for DWI data
       turnkey_pretractographyDense() {
           cyaneho "-- PENDING: pretractographyDense... "
           # ${MNAPCOMMAND} pretractographyDense --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --omatrix1="yes" --omatrix3="yes"
       }
       # -- Pre-tractography for DWI data
       turnkey_DWIDenseParcellation() {
           cyaneho "-- PENDING: DWIDenseParcellation... "
           # ${MNAPCOMMAND} DWIDenseParcellation --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --waytotal="${WayTotal}" --matrixversion="${MatrixVersion}" --parcellationfile="${ParcellationFile}" --outname="${DWIOutName}"
       }
       # -- Pre-tractography for DWI data
       turnkey_DWISeedTractography() {
           cyaneho "-- PENDING: DWISeedTractography... "
           # ${MNAPCOMMAND} DWISeedTractography --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --waytotal="${WayTotal}" --matrixversion="${MatrixVersion}" --outname="${DWIOutName}" --matrixversion='1' --seedfile="${SeedFile}"
           # ${MNAPCOMMAND} DWISeedTractography --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --waytotal="${WayTotal}" --matrixversion="${MatrixVersion}" --outname="${DWIOutName}_GBC" --matrixversion='1' --seedfile="gbc"
       }
    #
    # --------------- DWI Processing and analyses end --------------------------


    # --------------- Custom QC start ------------------------------------------
    # 
       # -- Check if Custom QC was requested
       turnkey_QCPreprocCustom() {
           cyaneho "-- QCPreprocCustom... "
           Modalities="T1w, T2w, myelin, BOLD, DWI"
           for Modality in ${Modalities}; do
               if [[ ${Modality} == "BOLD" ]]; then
                   ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --boldsuffix="Atlas" --processcustom="yes" --omitdefaults="yes"
                   if [ -z `ls -t1 *_${QCPreproc}*log 2>/dev/null | head -n 1` ]; then 
                      CheckLogQCBOLDCustom=""
                   else
                      CheckLogQCBOLDCustom=`ls -t1 *_${QCPreproc}*log | head -n 1`
                   fi
               fi
               if [[ ${Modality} == "DWI" ]]; then
                   ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --processcustom="yes" --omitdefaults="yes"
                   if [ -z `ls -t1 *_${QCPreproc}*log 2>/dev/null | head -n 1` ]; then 
                      CheckLogQCDWICustom=""
                   else
                      CheckLogQCDWICustom=`ls -t1 *_${QCPreproc}*log | head -n 1`
                   fi
               else
                   ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --processcustom="yes" --omitdefaults="yes"
                   CheckLogQC${Modality}Custom=`ls -t1 *_${QCPreproc}*log | head -n 1`
                   if [ -z `ls -t1 *_${QCPreproc}*log 2>/dev/null | head -n 1` ]; then 
                      CheckLogQC${Modality}Custom=""
                   else
                      CheckLogQC${Modality}Custom=`ls -t1 *_${QCPreproc}*log | head -n 1`
                   fi
               fi
           done
       }
    #
    # --------------- Custom QC end --------------------------------------------


    # --------------- BOLD FC Processing and analyses start --------------------
    #
       # -- Map HCP processed outputs for further FC BOLD analyses
       turnkey_mapHCPData() {
           echo ""; cyaneho "-- mapHCPData "; echo ""
           ${MNAPCOMMAND} mapHCPData \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --overwrite="${OVERWRITE_STEP}"
       }
       # -- Generate brain masks for de-noising
       turnkey_createBOLDBrainMasks() {
           cyaneho "-- PENDING: createBOLDBrainMasks processing steps go here... "
           ${MNAPCOMMAND} createBOLDBrainMasks \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --overwrite="${OVERWRITE_STEP}" \
           --logfolder="${logdir}" \
           --image_target="nifti"
       }
       # -- Compute BOLD statistics
       turnkey_computeBOLDStats() {
           cyaneho "-- PENDING: computeBOLDStats processing steps go here... "
           ${MNAPCOMMAND} computeBOLDStats \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --logfolder="${logdir}" \
           --overwrite="${OVERWRITE_STEP}" \
           --image_target="nifti"
       }
       # -- Create final BOLD statistics report
       turnkey_createStatsReport() {
           cyaneho "-- PENDING: createStatsReport processing steps go here... "
           ${MNAPCOMMAND} createStatsReport \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --logfolder="${logdir}" \
           --overwrite="${OVERWRITE_STEP}"
       }
       # -- Extract nuisance signal for further de-noising
       turnkey_extractNuisanceSignal() {
           cyaneho "-- PENDING: extractNuisanceSignal processing steps go here... "
           ${MNAPCOMMAND} extractNuisanceSignal \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --logfolder="${logdir}" \
           --overwrite="${OVERWRITE_STEP}"
       }
       # -- Process BOLDs
       turnkey_preprocessBold() {
           cyaneho "-- PENDING: preprocessBold processing steps go here... "
           ${MNAPCOMMAND} preprocessBold \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --logfolder="${logdir}" \
           --overwrite="${OVERWRITE_STEP}"
       }
       # -- Process via CONC file
       turnkey_preprocessConc() {
           cyaneho "-- PENDING: preprocessConc processing steps go here... "
           ${MNAPCOMMAND} preprocessConc \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --overwrite="${OVERWRITE_STEP}" \
           --logfolder="${logdir}"
       }
       # -- Compute GBC
       turnkey_computeBOLDfcGBC() {
       cyaneho "-- PENDING: computeBOLDfc processing steps for GBC go here... "
           InputFile="bold1_Atlas_scrub_g7_hpss_res-VWMWB.dtseries.nii"
           OutName="GBC_bold1_Atlas_scrub_g7_hpss_res-VWMWB"
           Ignore=""
           # ${MNAPCOMMAND} computeBOLDfc \
           # --subjectsfolder="${mnap_subjectsfolder}" \
           # --calculation="gbc" \
           # --runtype="individual" \
           # --subjects="${project_batch_file}" \
           # --inputfiles="${InputFile}" \
           # --inputpath="images/functional" \
           # --extractdata="yes" \
           # --outname="${OutName}" \
           # --overwrite="${OVERWRITE_STEP}" \
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
       cyaneho "-- PENDING: computeBOLDfc processing steps for seeds go here... "
           # ${MNAPCOMMAND} computeBOLDfc \
           # --subjectsfolder="${mnap_subjectsfolder}" \
           # --function="computeboldfc" \
           # --calculation="seed" \
           # --runtype="individual" \
           # --subjects="${project_batch_file}" \
           # --inputfiles="bold1_Atlas_scrub_g7_hpss_res-VWMWB_lpss.dtseries.nii" \
           # --inputpath="images/functional" \
           # --extractdata="yes" \
           # --outname="boldRest1AtlasScrubHPSSg7resVWMWB" \
           # --overwrite="${OVERWRITE_STEP}" \
           # --roinfo="/gpfs/project/fas/n3/software/MNAP/general/templates/Thalamus_Atlas/Thal.FSL.Associative.Sensory.MNI152.CIFTI.Atlas.names" \
           # --ignore="udvarsme" \
           # --options="" \
           # --method="" \
           # --targetf="" \
           # --mask="0" \
           # --covariance="true"
       }
    #
    # --------------- BOLD FC Processing and analyses end ----------------------
    
#
# =-=-=-=-=-=-= TURNKEY COMMANDS END =-=-=-=-=-=-= 

# -- Check turnkey steps and execute
if [ "$TURNKEY_STEPS" == "all" ]; then
    geho "==> Running all MNAP turkey workflow steps: ${MNAPTurnkeyWorkflow}"; echo ""
    TURNKEY_STEPS=${MNAPTurnkeyWorkflow}
fi
if [ "$TURNKEY_STEPS" != "all" ]; then
    echo ""; cyaneho "==> Running specific MNAP turkey workflow steps: ${TURNKEY_STEPS}"; echo ""
fi
unset TURNKEY_STEP_ERRORS

for TURNKEY_STEP in ${TURNKEY_STEPS}; do
    turnkey_${TURNKEY_STEP}
    # -- Check for completion of turnkey function
    cd ${logdir}/comlogs
    if [ -z `ls -t1 *_${TURNKEY_STEP}*log 2>/dev/null | head -n 1` ]; then 
        CheckLog=""
    else
        CheckLog=`ls -t1 *_${TURNKEY_STEP}*log | head -n 1`
    fi
    # -- More robust logging check for hcp functions
    if [[ ${TURNKEY_STEP} == "hcp1" ]] || [[ ${TURNKEY_STEP} == "hcp2" ]] || [[ ${TURNKEY_STEP} == "hcp3" ]] || [[ ${TURNKEY_STEP} == "hcp4" ]] || [[ ${TURNKEY_STEP} == "hcp5" ]] || [[ ${TURNKEY_STEP} == "hcpd" ]]; then
        if [[ -z ${CheckLog} ]]; then
           CheckLog=`ls -t1 *_${HCPLogName}*log | head -n 1`
        fi
    fi
    geho " -- Looking for incomplete/failed process"
    if [[ ! -z `echo "${CheckLog}" | grep 'done'` ]]; then
    
       if  [[ ${TURNKEY_STEP} == "hcp3" ]]; then
           if [[ -z `echo "${CheckLogQCT1w}" | grep 'done'` ]] || [[ -z `echo "${CheckLogQCT2w}" | grep 'done'` ]] || [[ -z `echo "${CheckLogQCMyelin}" | grep 'done'` ]]; then
              echo ""; reho " ===> ERROR: ${TURNKEY_STEP} step failed. Check ${logdir}/comlogs."
              TURNKEY_STEP_ERRORS="yes"
           fi
       fi
       if  [[ ${TURNKEY_STEP} == "hcp5" ]]; then
           if [[ -z `echo "${CheckLogQCBOLD}" | grep 'done'` ]]; then
              echo ""; reho " ===> ERROR: ${TURNKEY_STEP} step failed. Check ${logdir}/comlogs."
              TURNKEY_STEP_ERRORS="yes"
           fi
       fi
       if  [[ ${TURNKEY_STEP} == "hcpd" ]]; then
           if [[ -z `echo "${CheckLogQCDWI}" | grep 'done'` ]]; then
              echo ""; reho " ===> ERROR: ${TURNKEY_STEP} step failed. Check ${logdir}/comlogs."
              TURNKEY_STEP_ERRORS="yes"
           fi
       fi
       echo ""; geho " ===> Success: ${TURNKEY_STEP} step passed"
    else
        echo ""; reho " ===> ERROR: ${TURNKEY_STEP} step failed. Check ${logdir}/comlogs."
        TURNKEY_STEP_ERRORS="yes"
    fi
done

if [[ ${TURNKEY_STEP_ERRORS} == "yes" ]]; then
    echo ""
    reho " ===> Appears some turnkey steps have failed. Check ${logdir}/comlogs/"
    echo ""
else
    echo ""
    geho "------------------------- Successful completion of work --------------------------------"
    echo ""
fi

}

main $@
