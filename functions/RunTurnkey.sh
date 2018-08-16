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
#  RunTurnkey.sh
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
# See output of usage function: e.g. $./RunTurnkey.sh --help
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
$TOOLS/$MNAPREPO/library/environment/mnap_environment.sh &> /dev/null

MNAPTurnkeyWorkflow="createStudy mapRawData organizeDicom getHCPReady mapHCPFiles hcp1 hcp2 hcp3 QCPreprocT1W QCPreprocT2W QCPreprocMyelin hcp4 hcp5 QCPreprocBOLD hcpd QCPreprocDWI hcpdLegacy QCPreprocDWILegacy eddyQC QCPreprocDWIeddyQC FSLDtifit QCPreprocDWIDTIFIT FSLBedpostxGPU QCPreprocDWIProcess QCPreprocDWIBedpostX pretractographyDense DWIDenseParcellation DWISeedTractography QCPreprocCustom BOLDParcellation mapHCPData createBOLDBrainMasks computeBOLDStats createStatsReport extractNuisanceSignal preprocessBold preprocessConc g_PlotBoldTS computeBOLDfcGBC computeBOLDfcSeed"
QCPlotElements="'type=stats|stats>statstype=fd,img=1>statstype=dvarsme,img=1;type=image|name=V|img=1|mask=1|colormap=hsv;type=image|name=WM|img=1|mask=1|colormap=jet;type=image|name=GM|img=1|mask=1;type=image|name=GM|img=2|use=1','${mnap_subjectsfolder}/${CASES}/images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz'"

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
    echo ""
    echo "  -- PARMETERS:"
    echo ""
    echo "    --turnkeytype=<turnkey_run_type>                   Specify type turnkey run. Options are: local or xnat"
    echo "                                                       If empty default is set to: [xnat]."
    echo "    --path=<study_path>                                Path where study folder is located. If empty default is [/output/xnatprojectid] for XNAT run."
    echo "    --subjects=<comma_separated_list_of_cases>         List of subjects to run locally if --xnatsessionlabels and --xnatsubjectid missing."
    echo "    --turnkeysteps=<turnkey_worlflow_steps>            Specify specific turnkey steps you wish to run:"
    echo "                                                       Supported:   ${MNAPTurnkeyWorkflow} "
    echo ""
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
    echo "  -- GENERAL PARMETERS:"
    echo ""
    echo "    --rawdatainput=<specify_absolute_path_of_raw_data>         If --turnkeytype is not XNAT then specify location of raw data on the file system for a subject."
    echo "                                                                    Default is [] for the XNAT type run as host is used to pull data."
    echo "    --workingdir=<specify_directory_where_study_is_located>    Specify where the study folder is to be created or resides. Default is [/output]."
    echo "    --projectname=<specify_project_name>                       Specify name of the project on local file system if XNAT is not specified."
    echo "    --overwritestep=<specify_step_to_overwrite>                Specify <yes> or <no> for delete of prior workflow step. Default is [no]."
    echo "    --overwritesubject=<specify_subject_overwrite>             Specify <yes> or <no> for delete of prior subject run. Default is [no]."
    echo "    --overwriteproject=<specify_project_overwrite>             Specify <yes> or <no> for delete of entire project prior to run. Default is [no]."
    echo "    --overwriteprojectxnat=<specify_xnat_project_overwrite>    Specify <yes> or <no> for delete of entire XNAT project folder prior to run. Default is [no]."
    echo "    --cleanupsubject=<specify_subject_clean>                   Specify <yes> or <no> for cleanup of subject folder after steps are done. Default is [no]."
    echo "    --cleanupproject=<specify_subject_clean>                   Specify <yes> or <no> for cleanup of entire project after steps are done. Default is [no]."
    echo ""
    echo "  -- OPTIONAL CUSTOM QC PARAMETER:"
    echo ""
    echo "    --customqc=<yes/no>     Default is [no]. If set to 'yes' then the script looks into: "
    echo "                            ~/<study_path>/processing/scenes/QC/ for additional custom QC scenes."
    echo "                                  Note: The provided scene has to conform to MNAP QC template standards.xw"
    echo "                                        See $TOOLS/$MNAPREPO/library/data/scenes/qc/ for example templates."
    echo "                                        The qc path has to contain relevant files for the provided scene."
    echo ""
    echo "    --qcplotimages=<specify_plot_images>         Absolute path to images for g_PlotBoldTS. See 'mnap g_PlotBoldTS' for help. "
    echo "                                                 Only set if g_PlotBoldTS is requested then this is a required setting."
    echo "    --qcplotmasks=<specify_plot_masks>           Absolute path to one or multiple masks to use for extracting BOLD data. See 'mnap g_PlotBoldTS' for help. "
    echo "                                                 Only set if g_PlotBoldTS is requested then this is a required setting."
    echo "    --qcplotelements=<specify_plot_elements>     Plot element specifications for g_PlotBoldTS. See 'mnap g_PlotBoldTS' for help. "
    echo "                                                 Only set if g_PlotBoldTS is requested. If not set then the default is: "
    echo "        ${QCPlotElements}"
    echo ""
    echo "  -- EXAMPLE:"
    echo ""
    echo "  RunTurnkey.sh \ "
    echo "   --turnkeytype=<turnkey_run_type> \ "
    echo "   --turnkeysteps=<turnkey_worlflow_steps> \ "
    echo "   --batchfile=<batch_file> \ "
    echo "   --overwritestep=yes \ "
    echo "   --mappingfile=<mapping_file> \ "
    echo "   --xnatsessionlabels=<XNAT_SESSION_LABELS> \ "
    echo "   --xnatprojectid=<name_of_xnat_project_id> \ "
    echo "   --xnathostname=<XNAT_site_URL> \ "
    echo "   --xnatuser=<xnat_host_user_name> \ "
    echo "   --xnatpass=<xnat_host_user_pass> \ "
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
unset OVERWRITE_PROJECT_FORCE
unset OVERWRITE_PROJECT_XNAT
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
unset workdir
unset RawDataInputPath
unset PROJECT_NAME
unset PlotElements
unset CleanupSubject
unset CleanupProject

# =-=-=-=-=-= GENERAL OPTIONS =-=-=-=-=-=
#
# -- General input flags
STUDY_PATH=`opts_GetOpt "--path" $@`
workdir=`opts_GetOpt "--workingdir" $@`
PROJECT_NAME=`opts_GetOpt "--projectname" $@`
CleanupSubject=`opts_GetOpt "--cleanupsubject" $@`
CleanupProject=`opts_GetOpt "--cleanupproject" $@`
RawDataInputPath=`opts_GetOpt "--rawdatainput" $@`
StudyFolder=`opts_GetOpt "--path" $@`
SubjectsFolder=`opts_GetOpt "--subjectsfolder" $@`
CASES=`opts_GetOpt "--subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "${CASES}" | sed 's/,/ /g;s/|/ /g'`
OVERWRITE_SUBJECT=`opts_GetOpt "--overwritesubject" $@`
OVERWRITE_STEP=`opts_GetOpt "--overwritestep" $@`
OVERWRITE_PROJECT=`opts_GetOpt "--overwriteproject" $@`
OVERWRITE_PROJECT_FORCE=`opts_GetOpt "--overwriteprojectforce" $@`
OVERWRITE_PROJECT_XNAT=`opts_GetOpt "--overwriteprojectxnat" $@`
BATCH_PARAMETERS_FILENAME=`opts_GetOpt "--batchfile" $@`
SCAN_MAPPING_FILENAME=`opts_GetOpt "--mappingfile" $@`
XNAT_ACCSESSION_ID=`opts_GetOpt "--xnataccsessionid" $@`
XNAT_SESSION_LABELS=`opts_GetOpt "--xnatsessionlabels" "$@" | sed 's/,/ /g;s/|/ /g'`; XNAT_SESSION_LABELS=`echo "${XNAT_SESSION_LABELS}" | sed 's/,/ /g;s/|/ /g'`
XNAT_PROJECT_ID=`opts_GetOpt "--xnatprojectid" $@`
XNAT_SUBJECT_ID=`opts_GetOpt "--xnatsubjectid" $@`
XNAT_HOST_NAME=`opts_GetOpt "--xnathost" $@`
XNAT_USER_NAME=`opts_GetOpt "--xnatuser" $@`
XNAT_PASSWORD=`opts_GetOpt "--xnatpass" $@`
TURNKEY_STEPS=`opts_GetOpt "--turnkeysteps" "$@" | sed 's/,/ /g;s/|/ /g'`; TURNKEY_STEPS=`echo "${TURNKEY_STEPS}" | sed 's/,/ /g;s/|/ /g'`
TURNKEY_TYPE=`opts_GetOpt "--turnkeytype" $@`

# =-=-=-=-=-= BOLD FC OPTIONS =-=-=-=-=-=
#
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
#
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
#
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
if [[ ! -z $BOLDS ]]; then
    if [[ -z $BOLDRUNS ]]; then
        BOLDRUNS=$BOLDS
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
# -- g_PlotsBoldTS input flags
QCPlotElements=`opts_GetOpt "--qcplotelements" $@`
QCPlotImages=`opts_GetOpt "--qcplotimages" $@`
QCPlotMasks=`opts_GetOpt "--qcplotmasks" $@`

# -- Define script name
scriptName=$(basename ${0})

# -- Check if subject input is a parameter file instead of list of cases
echo ""
if [ -z "$TURNKEY_TYPE" ]; then TURNKEY_TYPE="xnat"; reho "Note: Setting turnkey to: $TURNKEY_TYPE"; echo ''; fi
if [[ ${CASES} == *.txt ]]; then
    SubjectParamFile="$CASES"
    echo ""
    echo "Using $SubjectParamFile for input."
    echo ""
    CASES=`more ${SubjectParamFile} | grep "id:"| cut -d " " -f 2`
fi

# -- Check that all inputs are provided
if [[ ${TURNKEY_TYPE} != "xnat" ]] && [[ -z ${RawDataInputPath} ]] && [[ ${TURNKEY_STEPS} == "all" ]] || [[ ${TURNKEY_STEPS} == "mapHCPFiles" ]]; then
   reho "Error. Raw data input flag missing "; return 1
fi
if [[ ${TURNKEY_TYPE} != "xnat" ]] && [[ -z ${PROJECT_NAME} ]] && [[ ${TURNKEY_STEPS} == "createStudy" ]]; then
   reho "Error. Project name flag missing "; return 1
fi
if [[ ${TURNKEY_TYPE} != "xnat" ]] && [[ -z ${workdir} ]] && [[ ${TURNKEY_STEPS} == "createStudy" ]]; then
   reho "Error. Working directory name flag missing "; return 1
fi

StudyFolder="${STUDY_PATH}"
SubjectsFolder="${STUDY_PATH}"
mnap_studyfolder="${STUDY_PATH}"

if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
   if [ -z "$STUDY_PATH" ]; then STUDY_PATH="/${workdir}/${PROJECT_NAME}"; reho "Note: Study path missing. Setting to: $STUDY_PATH"; echo ''; fi
   if [ -z "$CASES" ]; then
       if [ -z "$XNAT_SESSION_LABELS" ]; then
           reho "Error: --xnatsessionlabels or --subjects flag missing. Specify one."; echo ""
           exit 1
       else
           CASES="$XNAT_SESSION_LABELS"
       fi
   else
       XNAT_SESSION_LABELS="$CASES"
   fi
fi
if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
   if [ -z "$XNAT_SESSION_LABELS" ]; then
       if [ -z "$CASES" ]; then
           reho "Error: --xnatsessionlabels or --subjects flag missing. Specify one."; echo ""
           exit 1
       else
        XNAT_SESSION_LABELS="$CASES"
       fi
   else
       CASES="$XNAT_SESSION_LABELS"
   fi
fi

if [ -z "$TURNKEY_STEPS" ]; then reho "Turnkey steps flag missing. Specify turnkey steps:"; geho " ===> ${MNAPTurnkeyWorkflow}"; echo ''; exit 1; fi

if [[ "$TURNKEY_TYPE" == "xnat" ]]; then
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
    if [ -z "$XNAT_PROJECT_ID" ]; then reho "Error: --xnatprojectid flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    if [ -z "$XNAT_HOST_NAME" ]; then reho "Error: --xnathost flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    if [ -z "$XNAT_USER_NAME" ]; then reho "Error: --xnatuser flag missing. Username parameter file not specified."; echo ''; exit 1; fi
    if [ -z "$XNAT_PASSWORD" ]; then reho "Error: --xnatpass flag missing. Password parameter file not specified."; echo ''; exit 1; fi
    if [ -z "$STUDY_PATH" ]; then STUDY_PATH="/output/${XNAT_PROJECT_ID}"; reho "Note: Study path missing. Setting defaults: $STUDY_PATH"; echo ''; fi
fi

if [ -z "$OVERWRITE_STEP" ]; then OVERWRITE_STEP="no"; fi
if [ -z "$OVERWRITE_SUBJECT" ]; then OVERWRITE_SUBJECT="no"; fi
if [ -z "$OVERWRITE_PROJECT" ]; then OVERWRITE_PROJECT="no"; fi
if [[ -z "$OVERWRITE_PROJECT_XNAT" ]]; then OVERWRITE_PROJECT_XNAT="no"; fi
if [[ -z ${CleanupProject} ]]; then CleanupProject="no"; fi
if [[ -z ${CleanupSubject} ]]; then CleanupSubject="no"; fi

if [ -z "$QCPreprocCustom" ] || [ "$QCPreprocCustom" == "no" ]; then QCPreprocCustom=""; MNAPTurnkeyWorkflow=`printf '%s\n' "${MNAPTurnkeyWorkflow//QCPreprocCustom/}"`; fi
if [ -z "$DWILegacy" ] || [ "$DWILegacy" == "no" ]; then 
    DWILegacy=""
    QCPreprocDWILegacy=""
    MNAPTurnkeyWorkflow=`printf '%s\n' "${MNAPTurnkeyWorkflow//hcpdLegacy/}"`
    MNAPTurnkeyWorkflow=`printf '%s\n' "${MNAPTurnkeyWorkflow//QCPreprocDWILegacy/}"`
fi

# -- Define additional variables
if [[ -z ${workdir} ]] && [[ -z ${STUDY_PATH} ]] && [[ "$TURNKEY_TYPE" != "xnat" ]] && [ -z "$StudyFolder" ]; then
         workdir="/output"; reho "Note: Working directory where study is located is missing. Setting defaults: $workdir"; echo ''
         STUDY_PATH="${workdir}/${ROJECT_NAME}"
fi
if [[ -z ${workdir} ]] && [[ -z ${STUDY_PATH} ]] && [[ "$TURNKEY_TYPE" == "xnat" ]] && [ -z "$StudyFolder" ]; then
         workdir="/output"; reho "Note: Working directory where study is located is missing. Setting defaults: $workdir"; echo ''
         STUDY_PATH="${workdir}/${XNAT_PROJECT_ID}"
         mnap_studyfolder="${STUDY_PATH}"
fi
if [[ ${TURNKEY_TYPE} != "xnat" ]] && [[ `echo ${TURNKEY_STEPS} | grep 'createStudy'` ]]; then
    if [[ -z ${PROJECT_NAME} ]]; then reho "Error: project name parameter required when createStudy specified!"; echo ""; exit 1; fi
    if [[ -z ${workdir} ]]; then reho "Error: working directory parameter required when createStudy specified!"; echo ""; exit 1; fi
    STUDY_PATH="${workdir}/${PROJECT_NAME}"
    StudyFolder="${workdir}/${PROJECT_NAME}"
    SubjectsFolder="${workdir}/${PROJECT_NAME}/subjects"
fi

if [[ ${TURNKEY_TYPE} != "xnat" ]] && [[ `echo ${TURNKEY_STEPS} | grep 'mapHCPFiles'` ]]; then
        if [ -z "$BATCH_PARAMETERS_FILENAME" ]; then reho "Error: --batchfile flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
fi
if [[ ${TURNKEY_TYPE} != "xnat" ]] && [[ `echo ${TURNKEY_STEPS} | grep 'getHCPReady'` ]]; then
        if [ -z "$SCAN_MAPPING_FILENAME" ]; then reho "Error: --mappingfile flag missing. Batch parameter file not specified."; echo ''; exit 1;  fi
fi

mnap_subjectsfolder="${STUDY_PATH}/subjects"
mnap_workdir="${mnap_subjectsfolder}/${XNAT_SESSION_LABELS}"
logdir="${STUDY_PATH}/processing/logs"
specsdir="${mnap_subjectsfolder}/specs"
rawdir="${mnap_workdir}/inbox"
rawdir_temp="${mnap_workdir}/inbox_temp"
processingdir="${mnap_studyfolder}/processing"
MNAPCOMMAND="${TOOLS}/${MNAPREPO}/connector/mnap.sh"

if [ "$TURNKEY_TYPE" == "xnat" ]; then
   project_batch_file="${processingdir}/${XNAT_PROJECT_ID}_batch_params.txt"
fi
if [ "$TURNKEY_TYPE" != "xnat" ]; then
   project_batch_file="${processingdir}/${PROJECT_NAME}_batch_params.txt"
fi

StudyFolder="${STUDY_PATH}"
SubjectsFolder="${STUDY_PATH}"
mnap_studyfolder="${STUDY_PATH}"

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
if [ "$TURNKEY_TYPE" != "xnat" ]; then
    echo "   Local project name: ${PROJECT_NAME}"
    echo "   Raw data input path: ${RawDataInputPath}"
fi
echo "   Project-specific Batch file: ${project_batch_file}"
echo "   MNAP Study folder: ${mnap_studyfolder}"
echo "   MNAP Log folder: ${logdir}"
echo "   MNAP Subject-specific working folder: ${rawdir}"
echo "   Overwrite for a given turnkey step set to: ${OVERWRITE_STEP}"
echo "   Overwrite for subject set to: ${OVERWRITE_SUBJECT}"
echo "   Overwrite for project set to: ${OVERWRITE_PROJECT}"
echo "   Overwrite for the entire XNAT project: ${OVERWRITE_PROJECT_XNAT}"
echo "   Cleanup for subject set to: ${CleanupSubject}"
echo "   Cleanup for project set to: ${CleanupProject}"
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
if [[ ${OVERWRITE_PROJECT_FORCE} == "yes" ]]; then
        reho " ===> Force overwrite for entire project requested. Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        echo -n "     Confirm by typing 'yes' and then press [ENTER]: "
        read ManualOverwrite
        echo
        if [[ ${ManualOverwrite} == "yes" ]]; then
            rm -rf ${mnap_studyfolder}/ &> /dev/null
        fi
fi
if [[ ${OVERWRITE_PROJECT_XNAT} == "yes" ]]; then
        reho "    Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${mnap_studyfolder}/ &> /dev/null
fi
if [[ ${OVERWRITE_PROJECT} == "yes" ]] && [[ ${TURNKEY_STEPS} == "all" ]]; then
    if [[ `ls -IQC -Ilists -Ispecs -Iinbox -Iarchive ${mnap_subjectsfolder}` == "$XNAT_SESSION_LABELS" ]]; then
        reho " -- ${XNAT_SESSION_LABELS} is the only folder in ${mnap_subjectsfolder}. OK to proceed!"
        reho "    Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${mnap_studyfolder}/ &> /dev/null
    else
        reho " -- There are more than ${XNAT_SESSION_LABELS} directories ${mnap_studyfolder}."
        reho "    Skipping recursive overwrite for project: ${XNAT_PROJECT_ID}"; echo ""
    fi
fi
if [[ ${OVERWRITE_PROJECT} == "yes" ]] && [[ ${TURNKEY_STEPS} == "createStudy" ]]; then
    if [[ `ls -IQC -Ilists -Ispecs -Iinbox -Iarchive ${mnap_subjectsfolder}` == "$XNAT_SESSION_LABELS" ]]; then
        reho " -- ${XNAT_SESSION_LABELS} is the only folder in ${mnap_subjectsfolder}. OK to proceed!"
        reho "    Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${mnap_studyfolder}/ &> /dev/null
    else
        reho " -- There are more than ${XNAT_SESSION_LABELS} directories ${mnap_studyfolder}."
        reho "    Skipping recursive overwrite for project: ${XNAT_PROJECT_ID}"; echo ""
    fi
fi
if [[ ${OVERWRITE_SUBJECT} == "yes" ]]; then
    reho " -- Removing specific subject: ${mnap_workdir}."; echo ""
    rm -rf ${mnap_workdir} &> /dev/null
fi

# =-=-=-=-=-=-= TURNKEY COMMANDS START =-=-=-=-=-=-= 
#
#
    # --------------- Intial study and file organization start -----------------
    #
       # -- Create study hieararchy and generate subject folders
       turnkey_createStudy() {
           
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: createStudy ..."; echo ""
           TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
           createStudy_Runlog="${logdir}/runlogs/Log-createStudy_${TimeStamp}.log"
           createStudy_ComlogTmp="${workdir}/tmp_createStudy_${XNAT_SESSION_LABELS}_${TimeStamp}.log"; touch ${createStudy_ComlogTmp}; chmod 777 ${createStudy_ComlogTmp}
           createStudy_ComlogError="${logdir}/comlogs/error_createStudy_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
           createStudy_ComlogDone="${logdir}/comlogs/done_createStudy_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
           geho " -- Checking for and generating study folder ${mnap_studyfolder}"; echo ""
           if [ ! -d ${workdir} ]; then
               mkdir -p ${workdir} &> /dev/null
           fi
           
           if [ ! -d ${mnap_studyfolder} ]; then
               reho " -- Note: ${mnap_studyfolder} not found. Regenerating now..." 2>&1 | tee -a ${createStudy_ComlogTmp}  
               echo "" 2>&1 | tee -a ${createStudy_ComlogTmp}
               ${MNAPCOMMAND} createStudy "${mnap_studyfolder}"
               mv ${createStudy_ComlogTmp} ${logdir}/comlogs/
               createStudy_ComlogTmp="${logdir}/comlogs/tmp_createStudy_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
           else
               geho " -- Study folder ${mnap_studyfolder} already exits!" 2>&1 | tee -a ${createStudy_ComlogTmp}
               if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
                   if [[ ${OVERWRITE_PROJECT_XNAT} == "yes" ]]; then
                       reho "    Overwrite set to 'yes' for XNAT run. Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
                       rm -rf ${mnap_studyfolder}/ &> /dev/null
                       reho " -- Note: ${mnap_studyfolder} removed. Regenerating now..." 2>&1 | tee -a ${createStudy_ComlogTmp}  
                       echo "" 2>&1 | tee -a ${createStudy_ComlogTmp}
                       ${MNAPCOMMAND} createStudy "${mnap_studyfolder}"
                       mv ${createStudy_ComlogTmp} ${logdir}/comlogs/
                       createStudy_ComlogTmp="${logdir}/comlogs/tmp_createStudy_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
                   fi
               fi
           fi
           if [ ! -f ${mnap_studyfolder}/.mnapstudy ]; then
               reho "Note. ${mnap_studyfolder}mnapstudy file not found. Not a proper MNAP file hierarchy. Regenerating now..."; echo "";
               ${MNAPCOMMAND} createStudy "${mnap_studyfolder}"
           fi
           
           mkdir -p ${mnap_workdir} &> /dev/null
           mkdir -p ${mnap_workdir}/inbox &> /dev/null
           mkdir -p ${mnap_workdir}/inbox_temp &> /dev/null
           
           if [ -f ${mnap_studyfolder}/.mnapstudy ]; then CREATESTUDYCHECK="pass"; else CREATESTUDYCHECK="fail"; fi
          
           if [[ ${CREATESTUDYCHECK} == "pass" ]]; then
               echo "" >> ${createStudy_ComlogTmp}
               echo "------------------------- Successful completion of work --------------------------------" >> ${createStudy_ComlogTmp}
               echo "" >> ${createStudy_ComlogTmp}
               cp ${createStudy_ComlogTmp} ${createStudy_ComlogDone}
               createStudy_Comlog=${createStudy_ComlogDone}
           else
              echo "" >> ${createStudy_ComlogTmp}
              echo "Error. Something went wrong." >> ${createStudy_ComlogTmp}
              echo "" >> ${createStudy_ComlogTmp}
              cp ${createStudy_ComlogTmp} ${createStudy_ComlogError}
              createStudy_Comlog=${createStudy_ComlogError}
           fi
           
           rm ${createStudy_ComlogTmp}
       }
       
       # -- Get data from original location & organize DICOMs
       turnkey_mapRawData() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: mapRawData ..."; echo ""
           TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
           # Perform checks
           if [ ! -d ${workdir} ]; then
               reho "Error. ${workdir} not found."; echo ""; exit 1
           fi
           if [ ! -d ${mnap_studyfolder} ]; then
               reho "Note. ${mnap_studyfolder} not found. Regenerating now..."; echo "";
               ${MNAPCOMMAND} createStudy "${mnap_studyfolder}"
           fi
           if [ ! -f ${mnap_studyfolder}/.mnapstudy ]; then
               reho "Note. ${mnap_studyfolder} mnapstudy file not found. Not a proper MNAP file hierarchy. Regenerating now..."; echo "";
               ${MNAPCOMMAND} createStudy "${mnap_studyfolder}"
           fi
           if [ ! -d ${mnap_subjectsfolder} ]; then
               reho "Error. ${mnap_subjectsfolder} not found."; echo ""; exit 1
           fi
           if [ ! -f ${mnap_workdir} ]; then
               reho "Note. ${mnap_workdir} not found. Creating one now..."; echo ""
               mkdir -p ${mnap_workdir} &> /dev/null
               mkdir -p ${mnap_workdir}/inbox &> /dev/null
               mkdir -p ${mnap_workdir}/inbox_temp &> /dev/null
           fi
           if [[ ${OVERWRITE_STEP} == "yes" ]] && [[ ${TURNKEY_STEP} == "mapRawData" ]]; then
                  rm -f ${mnap_workdir}/inbox/* &> /dev/null
           fi
           CheckInbox=`ls -1A ${rawdir} | wc -l`
           if [[ ${CheckInbox} == "0" ]] && [[ ${OVERWRITE_STEP} == "no" ]]; then
                  reho "Error. ${mnap_workdir}/inbox/ is not empty and --overwritestep=${OVERWRITE_STEP} "
                  reho "Set overwrite to 'yes' and re-run..."
                  echo ""
                  exit 1
           fi
           # -- Define specific logs
           mapRawData_Runlog="${logdir}/runlogs/Log-mapRawData_${TimeStamp}.log"
           mapRawData_ComlogTmp="${logdir}/comlogs/tmp_mapRawData_${CASES}_${TimeStamp}.log"; touch ${mapRawData_ComlogTmp}; chmod 777 ${mapRawData_ComlogTmp}
           mapRawData_ComlogError="${logdir}/comlogs/error_mapRawData_${CASES}_${TimeStamp}.log"
           mapRawData_ComlogDone="${logdir}/comlogs/done_mapRawData_${CASES}_${TimeStamp}.log"
           # -- Map data from XNAT
           if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
               geho " --> Running turnkey via XNAT: ${XNAT_HOST_NAME}"; echo ""
               RawDataInputPath="/input/SCANS/"
               rm -rf ${specsdir}/${BATCH_PARAMETERS_FILENAME} &> /dev/null
               rm -rf ${specsdir}/${SCAN_MAPPING_FILENAME} &> /dev/null
               rm -rf ${processingdir}/scenes/QC/* &> /dev/null
               geho " -- Fetching batch and mapping files from ${XNAT_HOST_NAME}"; echo ""
               echo "" >> ${mapRawData_ComlogTmp}
               geho "  Logging turnkey_mapRawData output at time ${TimeStamp}:" >> ${mapRawData_ComlogTmp}
               echo "----------------------------------------------------------------------------------------" >> ${mapRawData_ComlogTmp}
               echo "" >> ${mapRawData_ComlogTmp}
               # -- Transfer data from XNAT HOST
               echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${BATCH_PARAMETERS_FILENAME}"" >> ${mapRawData_ComlogTmp}
               echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${SCAN_MAPPING_FILENAME}"" >> ${mapRawData_ComlogTmp}
               echo "  curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc/files?format=zip" > ${processingdir}/scenes/QC/scene_qc_files.zip"  >> ${mapRawData_ComlogTmp}
               curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${BATCH_PARAMETERS_FILENAME}" > ${specsdir}/${BATCH_PARAMETERS_FILENAME}
               curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${SCAN_MAPPING_FILENAME}" > ${specsdir}/${SCAN_MAPPING_FILENAME}
               curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc/files?format=zip" > ${processingdir}/scenes/QC/scene_qc_files.zip
               
               # -- BIDS support
               #if [[ ${GETBIDS} == "yes" ]]; then 
                   # echo "curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/SUBJECT_ID/experiments/EXPERIMENT_ID/scans/ALL/files?format=zip"  > ${mnap_subjectsfolder}/${CASES}/nii/bids_scans.zip" >> ${mapRawData_ComlogTmp}
                   # curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/SUBJECT_ID/experiments/EXPERIMENT_ID/scans/ALL/files?format=zip"  > ${mnap_subjectsfolder}/${CASES}/nii/bids_scans.zip
               #fi
               
               # -- Transfer data from XNAT HOST
               if [ -f ${processingdir}/scenes/QC/scene_qc_files.zip ]; then
                   echo ""; geho " -- Custom scene files found ${processingdir}/scenes/QC/scene_qc_files.zip "
                   geho " Unzipping ${processingdir}/scenes/QC/scene_qc_files.zip" >> ${mapRawData_ComlogTmp}
                   echo "" >> ${mapRawData_ComlogTmp}
                   cd ${processingdir}/scenes/QC; echo ""
                   unzip scene_qc_files.zip; echo ""
                   CustomQCModalities="T1w T2w myelin DWI BOLD"
                   for CustomQCModality in ${CustomQCModalities}; do
                       mkdir -p ${processingdir}/scenes/QC/${CustomQCModality} &> /dev/null
                       cp ${processingdir}/scenes/QC/${XNAT_PROJECT_ID}/resources/scenes_qc/files/${CustomQCModality}/*.scene ${processingdir}/scenes/QC/${CustomQCModality}/ &> /dev/null
                       CopiedSceneFile=`ls ${processingdir}/scenes/QC/${CustomQCModality}/*scene 2> /dev/null`
                       if [ ! -z ${CopiedSceneFile} ]; then
                          geho " -- Copied: $CopiedSceneFile"; echo ""
                          echo " Copied the following scenes from ${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc:" >> ${mapRawData_ComlogTmp}
                          echo " ${CopiedSceneFile}" >> ${mapRawData_ComlogTmp}
                       fi
                   done
                   rm -rf ${processingdir}/scenes/QC/${XNAT_PROJECT_ID} &> /dev/null
                   echo "" >> ${mapRawData_ComlogTmp}
               else
                    geho " No custom scene files found as an XNAT resources. If this is an error check your project resources in the XNAT web interface." >> ${mapRawData_ComlogTmp}
                    echo "" >> ${mapRawData_ComlogTmp}
               fi
            fi
            
            if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
                geho " --> Running turnkey via local: `hostname`"; echo ""
                RawDataInputPath="${RawDataInputPath}"
            fi
            # -- Link to inbox
            echo ""
            geho " -- Linking DICOMs into ${rawdir}"; echo ""
            echo "  find ${RawDataInputPath} -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" -exec ln -s '{}' ${rawdir}/ ';'" >> ${mapRawData_ComlogTmp}
            find ${RawDataInputPath} -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" -exec ln -s '{}' ${rawdir}/ ';' &> /dev/null
            # -- Perform checks
            DicomInputCount=`find ${RawDataInputPath} -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" | wc | awk '{print $1}'`
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
       }
       # -- organize DICOMs
       turnkey_organizeDicom() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: organizeDicom ..."; echo ""
           ${MNAPCOMMAND} organizeDicom --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}"
           cd ${mnap_subjectsfolder}/${CASES}/nii; NIILeadZeros=`ls ./0*.nii.gz 2>/dev/null`; for NIIwithZero in ${NIILeadZeros}; do NIIwithoutZero=`echo ${NIIwithZero} | sed 's/0//g'`; mv ${NIIwithZero} ${NIIwithoutZero}; done 
       }
       # -- Map processing folder structure
       turnkey_getHCPReady() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: getHCPReady ..."; echo ""
           TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
           getHCPReady_Runlog="${logdir}/runlogs/Log-getHCPReady${TimeStamp}.log"
           getHCPReady_ComlogTmp="${logdir}/comlogs/tmp_getHCPReady_${XNAT_SESSION_LABELS}_${TimeStamp}.log"; touch ${getHCPReady_ComlogTmp}; chmod 777 ${getHCPReady_ComlogTmp}
           getHCPReady_ComlogError="${logdir}/comlogs/error_getHCPReady_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
           getHCPReady_ComlogDone="${logdir}/comlogs/done_getHCPReady_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
           if [[ "${OVERWRITE_STEP}" == "yes" ]]; then
               rm -rf ${mnap_subjectsfolder}/${CASES}/subject_hcp.txt &> /dev/null
           fi
           if [ -f ${mnap_subjectsfolder}/subject_hcp.txt ]; then
               echo ""; geho " ===> ${mnap_subjectsfolder}/subject_hcp.txt exists. Set --overwrite='yes' to re-run."; echo ""; return 0
           fi
           Command="${MNAPCOMMAND} getHCPReady --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --mapping="${specsdir}/${SCAN_MAPPING_FILENAME}""
           echo ""; echo " -- Executed command:"; echo "   $Command"; echo ""
           eval ${Command}  2>&1 | tee -a ${getHCPReady_ComlogTmp}
           if [[ ! -z `cat ${getHCPReady_ComlogTmp} | grep 'Successful completion'` ]]; then ORGANIZEDICOMCHECK="pass"; else ORGANIZEDICOMCHECK="fail"; fi
           if [[ ${ORGANIZEDICOMCHECK} == "pass" ]]; then
               mv ${getHCPReady_ComlogTmp} ${getHCPReady_ComlogDone}
               getHCPReady_Comlog=${getHCPReady_ComlogDone}
           else
              mv ${getHCPReady_ComlogTmp} ${getHCPReady_ComlogError}
              getHCPReady_Comlog=${getHCPReady_ComlogError}
           fi
       }
       # -- Generate subject specific hcp processing file
       turnkey_mapHCPFiles() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: mapHCPFiles ..."; echo ""
           if [[ ${OVERWRITE_STEP} == "yes" ]]; then
              echo "  -- Removing prior hard link mapping..."; echo ""
              rm -rf ${project_batch_file} &> /dev/null
              HLinks=`ls ${SubjectsFolder}/${CASES}/hcp/${CASES}/*/*nii* 2>/dev/null`; for HLink in ${HLinks}; do unlink ${HLink}; done
           fi
           Command="${MNAPCOMMAND} mapHCPFiles --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}""
           echo ""; echo " -- Executed command:"; echo "   $Command"; echo ""
           eval ${Command}
           geho " -- Generating ${project_batch_file}"; echo ""
           cp ${specsdir}/${BATCH_PARAMETERS_FILENAME} ${project_batch_file}; cat ${mnap_workdir}/subject_hcp.txt >> ${project_batch_file}
       }
    #
    # --------------- Intial study and file organization end -------------------
    
       QCPreproc_Finalize() {
           QCPreprocComLog=`ls -t1 ${logdir}/comlogs/*_QCPreproc_${CASES}_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
           QCPreprocRunLog=`ls -t1 ${logdir}/runlogs/Log-QCPreproc-*.log | head -1 | xargs -n 1 basename 2> /dev/null`
           rename QCPreproc QCPreproc${QCLogName} ${logdir}/comlogs/${QCPreprocComLog} 2> /dev/null
           rename QCPreproc QCPreproc${QCLogName} ${logdir}/runlogs/${QCPreprocRunLog} 2> /dev/null
           mkdir -p ${mnap_subjectsfolder}/${CASES}/logs/comlog 2> /dev/null
           mkdir -p ${mnap_subjectsfolder}/${CASES}/logs/runlog 2> /dev/null
           mkdir -p ${mnap_subjectsfolder}/${CASES}/QC/${Modality} 2> /dev/null
           ln ${logdir}/comlogs/${QCPreprocComLog} ${mnap_subjectsfolder}/${CASES}/logs/comlog/${QCPreprocComLog} 2> /dev/null
           ln ${logdir}/comlogs/${QCPreprocRunLog} ${mnap_subjectsfolder}/${CASES}/logs/comlog/${QCPreprocRunLog} 2> /dev/null
           cp ${mnap_subjectsfolder}/subjects/QC/${Modality}/*${CASES}*scene ${mnap_subjectsfolder}/${CASES}/QC/${Modality}/ 2> /dev/null
           cp ${mnap_subjectsfolder}/subjects/QC/${Modality}/*${CASES}*zip ${mnap_subjectsfolder}/${CASES}/QC/${Modality}/ 2> /dev/null
      }

    # --------------- HCP Processing and relevant QC start ---------------------
    #
       # -- PreFreeSurfer
       turnkey_hcp1() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp1 (hcp_PreFS) ... "; echo ""
           ${MNAPCOMMAND} hcp1 --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}"
       }
       # -- FreeSurfer
       turnkey_hcp2() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp2 (hcp_FS) ... "; echo ""
           ${MNAPCOMMAND} hcp2 --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}"
           CleanupFiles=" talairach_with_skull.log lh.white.deformed.out lh.pial.deformed.out rh.white.deformed.out rh.pial.deformed.out"
           for CleanupFile in ${CleanupFiles}; do 
               cp ${logdir}/${CleanupFile} ${mnap_subjectsfolder}/${CASES}/hcp/pb0986/T1w/${CASES}/scripts/ 2>/dev/null
               rm -rf ${logdir}/${CleanupFile}
           done
       }
       # -- PostFreeSurfer
       turnkey_hcp3() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp3 (hcp_PostFS) ... "; echo ""
           ${MNAPCOMMAND} hcp3 --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}"
       }
       # -- QCPreprocT1W (after hcp3)
       turnkey_QCPreprocT1w() {
           Modality="T1w"
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc step for ${Modality} data ... "; echo ""
           ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}"
           QCLogName="T1w"
           QCPreproc_Finalize
       }
       # -- QCPreprocT2W (after hcp3)
       turnkey_QCPreprocT2w() {
           Modality="T2w"
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc step for ${Modality} data ... "; echo ""
           ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}"
           QCLogName="T2w"
           QCPreproc_Finalize
       }
       # -- QCPreprocMyelin (after hcp3)
       turnkey_QCPreprocMyelin() {
           Modality="myelin"
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc step for ${Modality} data ... "; echo ""
           ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}"
           QCLogName="Myelin"
           QCPreproc_Finalize
       }
       # -- fMRIVolume
       turnkey_hcp4() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp4 (hcp_fMRIVolume) ... "; echo ""
           HCPLogName="hcpfMRIVolume"
           ${MNAPCOMMAND} hcp4 --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}"
       }
       # -- fMRISurface
       turnkey_hcp5() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp4 (hcp_fMRISurface) ... "; echo ""
           HCPLogName="hcpfMRISurface"
           ${MNAPCOMMAND} hcp5 --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}"
       }
       # -- QCPreprocBOLD (after hcp5)
       turnkey_QCPreprocBOLD() {
           Modality="BOLD"
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc step for ${Modality} data ... "; echo ""
           if [ -z "${BOLDPrefix}" ]; then BOLDPrefix="bold"; fi
           if [ -z "${BOLDSuffix}" ]; then BOLDSuffix="Atlas"; fi
           if [ -z "${BOLDS}" ]; then
                BOLDS=`ls ${mnap_subjectsfolder}/${CASES}/hcp/${CASES}/MNINonLinear/Results/ | awk {'print $1'} 2> /dev/null`
           fi
           for BOLD in ${BOLDS}; do
               ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --boldprefix="${BOLDPrefix}" --boldsuffix="${BOLDSuffix}" --bolddata="${BOLD}"
               QCPreprocLog=`ls -t1 ${logdir}/comlogs/*_QCPreproc_${CASES}_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
               rename QCPreproc QCPreprocBOLD${BOLD} ${logdir}/comlogs/${QCPreprocLog}
           done
       }
       # -- Diffusion HCP (after hcp1)
       turnkey_hcpd() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp4 (hcp_Diffusion) ..."; echo ""
           ${MNAPCOMMAND} hcpd --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}"
       }
       # -- Diffusion Legacy (after hcp1)
       turnkey_hcpdLegacy() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step hcpdLegacy ..."; echo ""
           ${MNAPCOMMAND} hcpdLegacy --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --scanner="${Scanner}" --usefieldmap="${UseFieldmap}" --echospacing="${EchoSpacing}" --PEdir="{PEdir}" --unwarpdir="${UnwarpDir}" --diffdatasuffix="${DiffDataSuffix}" --TE="${TE}"
       }
       # -- QCPreprocDWILegacy (after hcpd)
       turnkey_QCPreprocDWILegacy() {
           Modality="DWI"
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc step for ${Modality} legacy data ... "; echo ""
           ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --dwidata="data" --dwipath="Diffusion" --dwilegacy="${DWILegacy}"
           QCLogName="DWILegacy"
           QCPreproc_Finalize
       }
       # -- QCPreprocDWI (after hcpd)
       turnkey_QCPreprocDWI() {
           Modality="DWI"
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc steps for ${Modality} HCP processing ... "; echo ""
           ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --outpath="${mnap_subjectsfolder}/QC/DWI" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --dwidata="data" --dwipath="Diffusion" --logfolder="${logdir}" 
           QCLogName="DWI"
           QCPreproc_Finalize
       }
       # -- eddyQC processing steps
       turnkey_eddyQC() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: eddyQC for DWI data ... "; echo ""
           # -- Defaults if values not set:
           if [ -z "$EddyBase" ]; then EddyBase="eddy_unwarped_images"; fi
           if [ -z "$Report" ]; then Report="individual"; fi
           if [ -z "$BvalsFile" ]; then BvalsFile="Pos_Neg.bvals"; fi
           if [ -z "$Mask" ]; then Mask="nodif_brain_mask.nii.gz"; fi
           if [ -z "$EddyIdx" ]; then EddyIdx="index.txt"; fi
           if [ -z "$EddyParams" ]; then EddyParams="acqparams.txt"; fi
           if [ -z "$BvecsFile" ]; then BvecsFile="Pos_Neg.bvecs"; fi
           #
           # --> Example for 'Legacy' data:
           # --eddypath='Diffusion/DWI_dir74_AP_b1000b2500/eddy/eddylinked' 
           # --eddybase='DWI_dir74_AP_b1000b2500_eddy_corrected' 
           # --bvalsfile='DWI_dir74_AP_b1000b2500.bval' 
           # --bvecsfile='DWI_dir74_AP_b1000b2500.bvec' 
           # --mask='DWI_dir74_AP_b1000b2500_nodif_brain_mask.nii.gz' 
           #
           ${MNAPCOMMAND} eddyQC --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --eddybase="${EddyBase}" --eddypath="${EddyPath}" --report="${Report}" --bvalsfile="${BvalsFile}" --mask="${Mask}" --eddyidx="${EddyIdx}" --eddyparams="${EddyParams}" --bvecsfile="${BvecsFile}" --overwrite="${OVERWRITE_STEP}"
       }
       # -- QCPreprocDWIeddyQC (after eddyQC)
       turnkey_QCPreprocDWIeddyQC() {
           Modality="DWI"
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc steps for ${Modality} eddyQC ... "; echo ""
           ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}" --outpath="${mnap_subjectsfolder}/QC/DWI" -modality="${Modality}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --eddyqcstats="yes"
           QCLogName="DWIeddyQC"
           QCPreproc_Finalize
       }
    #
    # --------------- HCP Processing and relevant QC end -----------------------

    # --------------- DWI additional analyses start ------------------------
    #
       # -- FSLDtifit (after hcpd or hcpdLegacy)
       turnkey_FSLDtifit() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: : FSLDtifit for DWI... "; echo ""
           ${MNAPCOMMAND} FSLDtifit --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}"
       }
       # -- FSLBedpostxGPU (after FSLDtifit)
       turnkey_FSLBedpostxGPU() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: FSLBedpostxGPU for DWI ... "
           if [ -z "$Fibers" ]; then Fibers="3"; fi
           if [ -z "$Model" ]; then Model="3"; fi
           if [ -z "$Burnin" ]; then Burnin="3000"; fi
           if [ -z "$Rician" ]; then Rician="yes"; fi
           ${MNAPCOMMAND} FSLBedpostxGPU --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}" --fibers="${Fibers}" --burnin="${Burnin}" --model="${Model}" --rician="${Rician}"
       }
       # -- QCPreprocDWIDTIFIT (after FSLDtifit)
       turnkey_QCPreprocDWIDTIFIT() {
           Modality="DWI"
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc steps for ${Modality} FSL's dtifit analyses ... "; echo ""
           ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}" --outpath="${mnap_subjectsfolder}/QC/DWI" --modality="${Modality}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --dtifitqc="yes" 
           QCLogName="DWIDTIFIT" 
           QCPreproc_Finalize
       }
       # -- QCPreprocDWIBedpostX (after FSLBedpostxGPU)
       turnkey_QCPreprocDWIBedpostX() {
           Modality="DWI"
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc steps for ${Modality} FSL's BedpostX analyses ... "; echo ""
           ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}" --outpath="${mnap_subjectsfolder}/QC/DWI" --modality="${Modality}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --bedpostxqc="yes"
           QCLogName="DWIBedpostX" 
           QCPreproc_Finalize
       }
       # -- probtrackxGPUDense for DWI data (after FSLBedpostxGPU)
       turnkey_probtrackxGPUDense() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: probtrackxGPUDense ... "; echo ""
           ${MNAPCOMMAND} probtrackxGPUDense --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}" --omatrix1="yes" --omatrix3="yes"
       }
       # -- pretractographyDense for DWI data (after FSLBedpostxGPU)
       turnkey_pretractographyDense() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: pretractographyDense ... "; echo ""
           ${MNAPCOMMAND} pretractographyDense --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}" --omatrix1="yes" --omatrix3="yes"
       }
       # -- DWIDenseParcellationfor DWI data (after pretractographyDense)
       turnkey_DWIDenseParcellation() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: DWIDenseParcellation ... "; echo ""
           # Defaults if not specified:
           if [ -z "$WayTotal" ]; then WayTotal="standard"; fi
           if [ -z "$MatrixVersion" ]; then MatrixVersions="1"; fi
           # Cole-Anticevic Brain-wide Network Partition version 1.0 (CAB-NP v1.0)
           if [ -z "$ParcellationFile" ]; then ParcellationFile="${TOOLS}/${MNAPREPO}/library/data/parcellations/Cole_GlasserNetworkAssignment_Final/final_LR_partition_modified_v2_filled.dlabel.nii"; fi
           if [ -z "$DWIOutName" ]; then DWIOutName="DWI-CAB-NP-v1.0"; fi
           for MatrixVersion in $MatrixVersions; do
               ${MNAPCOMMAND} DWIDenseParcellation --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}" --waytotal="${WayTotal}" --matrixversion="${MatrixVersion}" --parcellationfile="${ParcellationFile}" --outname="${DWIOutName}"
           done
       }
       # -- DWISeedTractography for DWI data (after pretractographyDense)
       turnkey_DWISeedTractography() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: DWISeedTractography ... "; echo "" 
           if [ -z "$MatrixVersion" ]; then MatrixVersions="1"; fi
           if [ -z "$WayTotal" ]; then WayTotal="standard"; fi
           if [ -z "$SeedFile" ]; then
               # Thalamus SomatomotorSensory
               SeedFile="${TOOLS}/${MNAPREPO}/library/data/atlases/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-SomatomotorSensory.symmetrical.intersectionLR.nii" 
               OutName="DWI_THALAMUS_FSL_LR_SomatomotorSensory_Symmetrical_intersectionLR"
               ${MNAPCOMMAND} DWISeedTractography --subjectsfolder="${SubjectsFolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}" --matrixversion="${MatrixVersion}" --waytotal="${WayTotal}" --outname="${OutName}" --seedfile="${SeedFile}"
               # Thalamus Prefrontal
               SeedFile="${TOOLS}/${MNAPREPO}/library/data/atlases/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Prefrontal.symmetrical.intersectionLR.nii" 
               OutName="DWI_THALAMUS_FSL_LR_Prefrontal"
               ${MNAPCOMMAND} DWISeedTractography --subjectsfolder="${SubjectsFolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}" --matrixversion="${MatrixVersion}" --waytotal="${WayTotal}" --outname="${OutName}" --seedfile="${SeedFile}"
           fi
           OutNameGBC="DWI_GBC"
           ${MNAPCOMMAND} DWISeedTractography --subjectsfolder="${SubjectsFolder}" --subjects="${CASES}" --overwrite="${OVERWRITE_STEP}" --matrixversion="${MatrixVersion}" --waytotal="${WayTotal}" --outname="${OutNameGBC}" --seedfile="gbc"
       }
    #
    # --------------- DWI Processing and analyses end --------------------------


    # --------------- Custom QC start ------------------------------------------
    # 
      # # -- Check if Custom QC was requested
      turnkey_QCPreprocCustom() {
          echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreprocCustom ... "; echo ""
          Modalities="T1w T2w myelin BOLD DWI"
          for Modality in ${Modalities}; do
              if [[ ${Modality} == "BOLD" ]]; then
                  ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --boldsuffix="Atlas" --processcustom="yes" --omitdefaults="yes"
                  QCLogName="Custom" 
                  QCPreproc_Finalize
              fi
              if [[ ${Modality} == "DWI" ]]; then
                  ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --processcustom="yes" --omitdefaults="yes"
                  QCLogName="Custom" 
                  QCPreproc_Finalize
              else
                  ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASES}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --processcustom="yes" --omitdefaults="yes"
                  QCLogName="Custom" 
                  QCPreproc_Finalize
              fi
          done
      }
    #
    # --------------- Custom QC end --------------------------------------------


    # --------------- BOLD FC Processing and analyses start --------------------
    #
    BOLDfcLogCheck() {
    # # -- Specific checks for BOLD Fc functions
    cd ${logdir}/comlogs/
    ComLogName=`ls -t1 ./*${FunctionName}*log | head -1 | xargs -n 1 basename 2> /dev/null`
    if [ ! -z ${ComLogName} ]; then echo " ===> Comlog: $ComLogName"; echo ""; fi
    rename ${FunctionName} ${TURNKEY_STEP} ${logdir}/comlogs/${ComLogName} 2> /dev/null

    cd ${logdir}/runlogs/
    RunLogName=`ls -t1 ./Log-${FunctionName}*log | head -1 | xargs -n 1 basename 2> /dev/null`
    if [ ! -z ${ComLogName} ]; then echo " ===> RunLog: $RunLogName"; echo ""; fi
    rename ${FunctionName} ${TURNKEY_STEP} ${logdir}/runlogs/${RunLogName} 2> /dev/null
    
    geho " -- Looking for incomplete/failed process ..."; echo ""
    
    CheckComLog=`ls -t1 ${logdir}/comlogs/*${TURNKEY_STEP}*log 2> /dev/null | head -n 1`
    CheckRunLog=`ls -t1 ${logdir}/runlogs/Log-${TURNKEY_STEP}*log 2> /dev/null | head -n 1`
    
    if [ -z "${CheckComLog}" ]; then
       TURNKEY_STEP_ERRORS="yes"
       reho " ===> ERROR: Completed ComLog file not found!"
    fi
    if [ ! -z "${CheckComLog}" ]; then
       geho " ===> Comlog file: ${CheckComLog}"
       chmod 777 ${CheckComLog} 2>/dev/null
       cp ${CheckComLog} ${mnap_subjectsfolder}/${CASES}/logs/comlog 2> /dev/null
       cp ${CheckRunLog} ${mnap_subjectsfolder}/${CASES}/logs/runlog 2> /dev/null
    fi
    if [ -z `echo "${CheckComLog}" | grep 'done'` ]; then
        echo ""; reho " ===> ERROR: ${TURNKEY_STEP} step failed."
        TURNKEY_STEP_ERRORS="yes"
    else
        echo ""; cyaneho " ===> RunTurnkey ~~~ SUCCESS: ${TURNKEY_STEP} step passed!"; echo ""
        TURNKEY_STEP_ERRORS="no"
    fi
    }

       # -- BOLD Parcellation 
       turnkey_BOLDParcellation() {
        FunctionName="BOLDParcellation"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: BOLDParcellation ... "; echo ""
        # -- Defaults if not specified:
        unset BOLDRUNS
        if [ -z ${BOLDRUNS} ]; then
            BOLDRUNS="1"
        fi
        unset BOLDRUN
        for BOLDRUN in ${BOLDRUNS}; do
           if [ -z "$InputFile" ]; then InputFile="bold${BOLDRUN}_Atlas_g7_hpss_res-mVWMWB_lpss"; fi
           if [ -z "$UseWeights" ]; then UseWeights="yes"; fi
           if [ -z "$WeightsFile" ]; then UseWeights="images/functional/movement/bold${BOLDRUN}.use"; fi
           # -- Cole-Anticevic Brain-wide Network Partition version 1.0 (CAB-NP v1.0)
           if [ -z "$ParcellationFile" ]; then ParcellationFile="${TOOLS}/${MNAPREPO}/library/data/parcellations/Cole_GlasserNetworkAssignment_Final/final_LR_partition_modified_v2_filled.dlabel.nii"; fi
           if [ -z "$OutName" ]; then OutName="BOLD-CAB-NP-v1.0"; fi
           if [ -z "$InputDataType" ]; then InputDataType="dtseries"; fi
           if [ -z "$InputPath" ]; then InputPath="/images/functional/"; fi
           if [ -z "$OutPath" ]; then OutPath="/images/functional/"; fi
           if [ -z "$ComputePConn" ]; then ComputePConn="yes"; fi
           if [ -z "$ExtractData" ]; then ExtractData="yes"; fi
           # -- Command
           RunCommand="${MNAPCOMMAND} BOLDParcellation --subjects='${CASES}' \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --inputfile='${InputFile}' \
           --singleinputfile='${SingleInputFile}' \
           --inputpath='${InputPath}' \
           --inputdatatype='${InputDataType}' \
           --parcellationfile='${ParcellationFile}' \
           --overwrite='${Overwrite}' \
           --outname='${OutName}' \
           --outpath='${OutPath}' \
           --computepconn='${ComputePConn}' \
           --extractdata='${ExtractData}' \
           --useweights='${UseWeights}' \
           --weightsfile='${WeightsFile}'"
           echo " -- Command: ${RunCommand}"
           eval ${RunCommand}
           BOLDfcLogCheck
        done
       }
       # -- Map HCP processed outputs for further FC BOLD analyses
       turnkey_mapHCPData() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: mapHCPData ... "; echo ""
           ${MNAPCOMMAND} mapHCPData \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --overwrite="${OVERWRITE_STEP}" \
           --logfolder="${logdir}"
       }
       # -- Generate brain masks for de-noising
       turnkey_createBOLDBrainMasks() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: createBOLDBrainMasks ... "; echo ""
           ${MNAPCOMMAND} createBOLDBrainMasks \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --overwrite="${OVERWRITE_STEP}" \
           --logfolder="${logdir}"
       }
       # -- Compute BOLD statistics
       turnkey_computeBOLDStats() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: computeBOLDStats ... "; echo ""
           ${MNAPCOMMAND} computeBOLDStats \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --overwrite="${OVERWRITE_STEP}" \
           --logfolder="${logdir}"
       }
       # -- Create final BOLD statistics report
       turnkey_createStatsReport() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: createStatsReport ... "; echo ""
           ${MNAPCOMMAND} createStatsReport \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --overwrite="${OVERWRITE_STEP}" \
           --logfolder="${logdir}"
       }
       # -- Extract nuisance signal for further de-noising
       turnkey_extractNuisanceSignal() {
           cyaneho " ===> RunTurnkey ~~~ RUNNING: extractNuisanceSignal ... "; echo ""
           ${MNAPCOMMAND} extractNuisanceSignal \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --overwrite="${OVERWRITE_STEP}" \
           --logfolder="${logdir}"
       }
       # -- Process BOLDs
       turnkey_preprocessBold() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: preprocessBold ... "; echo ""
           ${MNAPCOMMAND} preprocessBold \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --overwrite="${OVERWRITE_STEP}" \
           --logfolder="${logdir}"
       }
       # -- Process via CONC file
       turnkey_preprocessConc() {
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: preprocessConc ... "; echo ""
           ${MNAPCOMMAND} preprocessConc \
           --subjects="${project_batch_file}" \
           --subjectsfolder="${mnap_subjectsfolder}" \
           --overwrite="${OVERWRITE_STEP}" \
           --logfolder="${logdir}"
       }
       # -- Compute GBC
       turnkey_computeBOLDfcGBC() {
       FunctionName="computeBOLDfc"
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: computeBOLDfc processing steps for GBC ... "; echo ""
           unset BOLDRUNS
           if [ -z ${BOLDRUNS} ]; then
               BOLDRUNS="1"
           fi
           unset BOLDRUN
           for BOLDRUN in ${BOLDRUNS}; do
                if [ -z "$InputFile" ]; then InputFile="bold${BOLDRUN}_Atlas_g7_hpss_res-mVWMWB_lpss.dtseries.nii"; fi
                if [ -z "$InputPath" ]; then InputPath="/images/functional"; fi
                if [ -z "$ExtractData" ]; then ExtractData=""; fi
                if [ -z "$OutName" ]; then OutName="GBC_bold${BOLDRUN}_Atlas_g7_hpss_res-VWMWB_lpss"; fi
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
                RunCommand="${MNAPCOMMAND} computeBOLDfc \
                --subjectsfolder='${mnap_subjectsfolder}' \
                --calculation='gbc' \
                --runtype='individual' \
                --subjects='${CASES}' \
                --inputfiles='${InputFile}' \
                --inputpath='${InputPath}' \
                --extractdata='${ExtractData}' \
                --outname='${OutName}' \
                --flist='${FileList}' \
                --overwrite='${OVERWRITE_STEP}' \
                --ignore='${IgnoreFrames}' \
                --target='${TargetROI}' \
                --command='${GBCCommand}' \
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
       # -- Compute Seed FC for relevant ROIs
       turnkey_computeBOLDfcSeed() {
       FunctionName="computeBOLDfc"
           echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: computeBOLDfc processing steps for Seed FC ... "; echo ""
           if [ -z ${ROIInfo} ]; then
              ROINames="${TOOLS}/${MNAPREPO}/library/data/roi/seeds_cifti.names ${TOOLS}/${MNAPREPO}/library/data/atlases/Thalamus_Atlas/Thal.FSL.MNI152.CIFTI.Atlas.AllSurfaceZero.names"
           else
              ROINames=${ROIInfo}
           fi
        for ROIInfo in ${ROINames}; do
              unset BOLDRUNS
              if [ -z ${BOLDRUNS} ]; then
                  BOLDRUNS="1"
              fi
              unset BOLDRUN
              for BOLDRUN in ${BOLDRUNS}; do
                if [ -z "$InputFile" ]; then InputFile="bold${BOLDRUN}_Atlas_g7_hpss_res-mVWMWB_lpss.dtseries.nii"; fi
                if [ -z "$InputPath" ]; then InputPath="/images/functional"; fi
                if [ -z "$ExtractData" ]; then ExtractData=""; fi
                if [ -z "$OutName" ]; then OutName="seed_bold${BOLDRUN}_Atlas_g7_hpss_res-VWMWB_lpss"; fi
                if [ -z "$FileList" ]; then FileList=""; fi
                if [ -z "$OVERWRITE_STEP" ]; then OVERWRITE_STEP="yes"; fi
                if [ -z "$IgnoreFrames" ]; then IgnoreFrames="udvarsme"; fi
                if [ -z "$Method" ]; then Method="mean"; fi
                if [ -z "$FCCommand" ]; then FCCommand="all"; fi
                if [ -z "$OutPath" ]; then OutPath="/images/functional"; fi
                if [ -z "$MaskFrames" ]; then MaskFrames="0"; fi
                if [ -z "$Verbose" ]; then Verbose="true"; fi
                if [ -z "$Covariance" ]; then Covariance="true"; fi
                RunCommand="${MNAPCOMMAND} computeBOLDfc \
                --subjectsfolder='${mnap_subjectsfolder}' \
                --calculation='seed' \
                --runtype='individual' \
                --subjects='${CASES}' \
                --inputfiles='${InputFile}' \
                --inputpath='${InputPath}' \
                --extractdata='${ExtractData}' \
                --outname='${OutName}' \
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
       # -- Compute g_PlotBoldTS ==> (08/14/17 - 6:50PM): Coded but not final yet due to Octave/Matlab problems
       turnkey_g_PlotBoldTS() {
          echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: g_PlotBoldTS QC plotting ... "; echo ""
          TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
          g_PlotBoldTS_Runlog="${logdir}/runlogs/Log-g_PlotBoldTS_${TimeStamp}.log"
          g_PlotBoldTS_ComlogTmp="${logdir}/comlogs/tmp_g_PlotBoldTS_${XNAT_SESSION_LABELS}_${TimeStamp}.log"; touch ${g_PlotBoldTS_ComlogTmp}; chmod 777 ${g_PlotBoldTS_ComlogTmp}
          g_PlotBoldTS_ComlogError="${logdir}/comlogs/error_g_PlotBoldTS_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
          g_PlotBoldTS_ComlogDone="${logdir}/comlogs/done_g_PlotBoldTS_${XNAT_SESSION_LABELS}_${TimeStamp}.log"
          
          if [ -z ${QCPlotElements} ]; then
                QCPlotElements="type=stats|stats>plotdata=fd,imageindex=1>plotdata=dvarsme,imageindex=1;type=signal|name=V|imageindex=1|maskindex=1|colormap=hsv;type=signal|name=WM|imageindex=1|maskindex=1|colormap=jet;type=signal|name=GM|imageindex=1|maskindex=1;type=signal|name=GM|imageindex=2|use=1|scale=3"
          fi
          if [ -z ${QCPlotMasks} ]; then
                QCPlotMasks="${mnap_subjectsfolder}/${CASES}/images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz"
          fi
          if [ -z ${images_folder} ]; then
              images_folder="${mnap_subjectsfolder}/$CASES/images/functional"
          fi
          if [ -z ${output_folder} ]; then
              output_folder="${mnap_subjectsfolder}/$CASES/images/functional/movement"
          fi
          if [ -z ${output_name} ]; then
              output_name="${CASES}_BOLD_GreyPlot_CIFTI.pdf"
          fi
          if [ -z ${BOLDRUNS} ]; then
              BOLDRUNS="1"
          fi
          echo " -- Log folder: ${logdir}/comlogs/" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
          echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
          echo " -- Parameters for g_PlotBoldTS: " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
          echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
          echo "   QC Plot Masks: ${QCPlotMasks}" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
          echo "   QC Plot Elements: ${QCPlotElements}" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
          echo "   QC Plot image folder: ${images_folder}" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
          echo "   QC Plot output folder: ${output_folder}" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
          echo "   QC Plot output name: ${output_name}" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
          echo "   QC Plot BOLDS runs: ${BOLDRUNS}" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}

          unset BOLDRUN
          for BOLDRUN in ${BOLDRUNS}; do 
             cd ${images_folder} 
             if [ -z ${QCPlotImages} ]; then
                 QCPlotImages="bold${BOLDRUN}.nii.gz;bold${BOLDRUN}_Atlas_g7_hpss_res-mVWMWB_lpss.dtseries.nii"
             fi
             echo "   QC Plot images: ${QCPlotImages}" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
             echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
             echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
             echo " -- Command: " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
             echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
             echo "${MNAPCOMMAND} g_PlotBoldTS --images="${QCPlotImages}" --elements="${QCPlotElements}" --masks="${QCPlotMasks}" --filename="${output_folder}/${output_name}" --skip="0" --subjid="${CASES}" --verbose="true"" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
             echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
             
             ${MNAPCOMMAND} g_PlotBoldTS --images="${QCPlotImages}" --elements="${QCPlotElements}" --masks="${QCPlotMasks}" --filename="${output_folder}/${output_name}" --skip="0" --subjid="${CASES}" --verbose="true"
             echo " -- Copying ${output_folder}/${output_name} to ${mnap_subjectsfolder}/QC/BOLD/" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
             echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
             cp ${output_folder}/${output_name} ${mnap_subjectsfolder}/QC/BOLD/
             if [ -f ${mnap_subjectsfolder}/QC/BOLD/${output_name} ]; then
                 echo " -- Found ${mnap_subjectsfolder}/QC/BOLD/${output_name}" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
                 echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
                 g_PlotBoldTS_Check="pass"
             else
                 echo " -- Result ${mnap_subjectsfolder}/QC/BOLD/${output_name} missing!" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
                 echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
                 g_PlotBoldTS_Check="fail"
             fi
          done
          
          if [[ ${g_PlotBoldTS_Check} == "pass" ]]; then
              echo "" >> ${g_PlotBoldTS_ComlogTmp}
              echo "------------------------- Successful completion of work --------------------------------" >> ${g_PlotBoldTS_ComlogTmp}
              echo "" >> ${g_PlotBoldTS_ComlogTmp}
              cp ${g_PlotBoldTS_ComlogTmp} ${g_PlotBoldTS_ComlogDone}
              g_PlotBoldTS_Comlog=${g_PlotBoldTS_ComlogDone}
          else
             echo "" >> ${g_PlotBoldTS_ComlogTmp}
             echo "Error. Something went wrong." >> ${g_PlotBoldTS_ComlogTmp}
             echo "" >> ${g_PlotBoldTS_ComlogTmp}
             cp ${g_PlotBoldTS_ComlogTmp} ${g_PlotBoldTS_ComlogError}
             g_PlotBoldTS_Comlog=${g_PlotBoldTS_ComlogError}
          fi
          rm ${g_PlotBoldTS_ComlogTmp}
       }
    #
    # --------------- BOLD FC Processing and analyses end ----------------------

#
# =-=-=-=-=-=-= TURNKEY COMMANDS END =-=-=-=-=-=-= 

# -- Check turnkey steps and execute
if [ "$TURNKEY_STEPS" == "all" ]; then
    echo ""; 
    geho "  ---------------------------------------------------------------------"
    echo ""
    geho "   ===> EXECUTING all MNAP turkey workflow steps: ${MNAPTurnkeyWorkflow}"
    echo ""
    geho "  ---------------------------------------------------------------------"
    echo ""
    TURNKEY_STEPS=${MNAPTurnkeyWorkflow}
fi
if [ "$TURNKEY_STEPS" != "all" ]; then
    echo ""; 
    geho "  ---------------------------------------------------------------------"
    echo ""
    geho "   ===> EXECUTING specific MNAP turkey workflow steps: ${TURNKEY_STEPS}"
    echo ""
    geho "  ---------------------------------------------------------------------"
    echo ""
fi

# -- Lopp through specified Turnkey steps
unset TURNKEY_STEP_ERRORS
for TURNKEY_STEP in ${TURNKEY_STEPS}; do
    
    # -- Execute turnkey
    turnkey_${TURNKEY_STEP}
    
    # -- Generate single subject log folders
    mkdir -p ${mnap_subjectsfolder}/${CASES}/logs/comlog 2> /dev/null
    mkdir -p ${mnap_subjectsfolder}/${CASES}/logs/runlog 2> /dev/null
    Modalities="T1w T2w myelin BOLD DWI"
    for Modality in ${Modalities}; do
        mkdir -p ${mnap_subjectsfolder}/${CASES}/QC/${Modality} 2> /dev/null
    done

    # -- Check for completion of turnkey function
    # -- Specific checks for NIUtilities functions that run on multiple jobs
    ConnectorBOLDFunctions="BOLDParcellation computeBOLDfcGBC computeBOLDfcSeed"
    NiUtilsFunctons="hcp1 hcp2 hcp3 hcp4 hcp5 hcpd mapHCPData createBOLDBrainMasks computeBOLDStats createStatsReport extractNuisanceSignal preprocessBold preprocessConc"
    if [ -z "${NiUtilsFunctons##*${TURNKEY_STEP}*}" ] && [ ! -z "${ConnectorBOLDFunctions##*${TURNKEY_STEP}*}" ]; then
    geho " -- Looking for incomplete/failed process ..."; echo ""
       CheckRunLog=`ls -t1 ${logdir}/runlogs/Log-${TURNKEY_STEP}*log 2> /dev/null | head -n 1`
       CheckComLog=`ls -t1 ${logdir}/comlogs/*${TURNKEY_STEP}*log 2> /dev/null | head -n 1`
        if [ -z "${CheckRunLog}" ]; then
           TURNKEY_STEP_ERRORS="yes"
           reho " ===> ERROR: Runlog file not found!"; echo ""
        fi
        if [ ! -z "${CheckRunLog}" ]; then
           geho " ===> Runlog file: ${CheckRunLog} "; echo ""
           CheckRunLogOut=`cat ${CheckRunLog} | grep '===> Successful completion'`
           cp ${CheckComLog} ${mnap_subjectsfolder}/${CASES}/logs/comlogs/ 2> /dev/null
           cp ${CheckRunLog} ${mnap_subjectsfolder}/${CASES}/logs/runlogs/ 2> /dev/null
        fi
        if [ -z "${CheckRunLogOut}" ]; then
               TURNKEY_STEP_ERRORS="yes"
               reho " ===> ERROR: Run for ${TURNKEY_STEP} failed! Examine outputs: ${CheckRunLog}"; echo ""
           else
               echo ""; cyaneho " ===> RunTurnkey ~~~ SUCCESS: ${TURNKEY_STEP} step passed!"; echo ""
               TURNKEY_STEP_ERRORS="no"
        fi
    fi
    # -- Specific checks for all other functions
    if [ ! -z "${NiUtilsFunctons##*${TURNKEY_STEP}*}" ] && [ ! -z "${ConnectorBOLDFunctions##*${TURNKEY_STEP}*}" ]; then
    geho " -- Looking for incomplete/failed process ..."; echo ""
           CheckComLog=`ls -t1 ${logdir}/comlogs/*${TURNKEY_STEP}*log 2> /dev/null | head -n 1`
           CheckRunLog=`ls -t1 ${logdir}/runlogs/Log-${TURNKEY_STEP}*log 2> /dev/null | head -n 1`
        if [ -z "${CheckComLog}" ]; then
           TURNKEY_STEP_ERRORS="yes"
           reho " ===> ERROR: Completed ComLog file not found!"
        fi
        if [ ! -z "${CheckComLog}" ]; then
           geho " ===> Comlog file: ${CheckComLog}"
           chmod 777 ${CheckComLog} 2>/dev/null
           cp ${CheckComLog} ${mnap_subjectsfolder}/${CASES}/logs/comlog 2> /dev/null
           cp ${CheckRunLog} ${mnap_subjectsfolder}/${CASES}/logs/runlog 2> /dev/null
        fi
        if [ -z `echo "${CheckComLog}" | grep 'done'` ]; then
            echo ""; reho " ===> ERROR: ${TURNKEY_STEP} step failed."
            TURNKEY_STEP_ERRORS="yes"
        else
            echo ""; cyaneho " ===> RunTurnkey ~~~ SUCCESS: ${TURNKEY_STEP} step passed!"; echo ""
            TURNKEY_STEP_ERRORS="no"
        fi
    fi
done

if [[ "${TURNKEY_STEP_ERRORS}" == "yes" ]]; then
    echo ""
    reho " ===> Appears some RunTurnkey steps have failed."
    reho "       Check ${logdir}/comlogs/:"
    reho "       Check ${logdir}/runlogs/:"
    echo ""
else
    echo ""
    geho "------------------------- Successful completion of work --------------------------------"
    echo ""
fi

}

main $@

