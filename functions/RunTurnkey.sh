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
# * These may be stored in: "$mnap_subjectsfolder/$CASE/hcp/$CASE/MNINonLinear/Results/ 
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

MNAPTurnkeyWorkflow="createStudy mapRawData organizeDicom getHCPReady mapHCPFiles hcp1 hcp2 hcp3 QCPreprocT1W QCPreprocT2W QCPreprocMyelin hcp4 hcp5 QCPreprocBOLD hcpd QCPreprocDWI hcpdLegacy QCPreprocDWILegacy eddyQC QCPreprocDWIeddyQC FSLDtifit QCPreprocDWIDTIFIT FSLBedpostxGPU QCPreprocDWIProcess QCPreprocDWIBedpostX pretractographyDense DWIDenseParcellation DWISeedTractography QCPreprocCustom mapHCPData createBOLDBrainMasks computeBOLDStats createStatsReport extractNuisanceSignal preprocessBold preprocessConc g_PlotBoldTS BOLDParcellation computeBOLDfcSeed computeBOLDfcGBC QCPreprocBOLDfc MNAPClean"
QCPlotElements="type=stats|stats>plotdata=fd,imageindex=1>plotdata=dvarsme,imageindex=1;type=signal|name=V|imageindex=1|maskindex=1|colormap=hsv;type=signal|name=WM|imageindex=1|maskindex=1|colormap=jet;type=signal|name=GM|imageindex=1|maskindex=1;type=signal|name=GM|imageindex=2|use=1|scale=3"
SupportedAcceptanceTestSteps="hcp1 hcp2 hcp3 hcp4 hcp5"
MNAPTurnkeyClean="hcp4"

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
    echo "  -- GENERAL PARMETERS:"
    echo ""
    echo "    --turnkeytype=<turnkey_run_type>                          Specify type turnkey run. Options are: local or xnat"
    echo "                                                              If empty default is set to: [xnat]."
    echo "    --path=<study_path>                                       Path where study folder is located. If empty default is [/output/xnatprojectid] for XNAT run."
    echo "    --subjects=<subjects_to_run_turnkey_on>                   Subjects to run locally on the file system if not an XNAT run."
    echo "    --subjids=<comma_separated_list_of_subject_ids>           Ids to select for a run via gMRI engine from the batch file"
    echo "    --turnkeysteps=<turnkey_worlflow_steps>                   Specify specific turnkey steps you wish to run:"
    echo "                                                              Supported:   ${MNAPTurnkeyWorkflow} "
    echo "    --turnkeycleanstep=<clean_intermediate worlflow_steps>    Specify specific turnkey steps you wish to clean up intermediate files for:"
    echo "                                                              Supported:   ${MNAPTurnkeyClean}"
    echo ""
    echo "  -- ACCEPTANCE TESTING PARAMETERS:"
    echo ""
    echo "    --acceptancetest=<request_acceptance_test>         Specify if you wish to run a final acceptance test after each unit of processing. Default is [no]"
    echo "                                                       If --acceptancetest='yes', then --turnkeysteps must be provided and will be executed first."
    echo "                                                       If --acceptancetest='<turnkey_step>', then acceptance test will be run but step won't be executed."
    echo ""
    echo "  -- XNAT HOST, PROJECT and USER PARMETERS:"
    echo ""
    echo "    --xnathost=<xnat_host_url>                       Specify the XNAT site hostname URL to push data to."
    echo "    --xnatprojectid=<name_of_xnat_project_id>        Specify the XNAT site project id. This is the Project ID in XNAT and not the Project Title."
    echo "    --xnatuser=<xnat_host_user_name>                 Specify XNAT username."
    echo "    --xnatpass=<xnat_host_user_pass>                 Specify XNAT password."
    echo ""
    echo "  -- XNAT SUBJECT AND SESSION PARAMETERS:"
    echo ""
    echo "    --xnatsubjectid=<xnat_subject_id>                  ID for subject across the entire XNAT database. * Required or --xnatsubjectlabel needs to be set."
    echo "    --xnatsubjectlabel=<xnat_subject_label>            Label for subject within a project for the XNAT database. * Required or --xnatsubjectid needs to be set."
    echo "    --xnataccsessionid=<xnat_accesession_id>           ID for subject-specific session within the XNAT project. * Derived from XNAT but can be set manually."
    echo "    --xnatsessionlabel=<xnat_session_label>            Label for session within XNAT project. Note: may be general across multiple subjects (e.g. rest). * Required."
    echo ""
    echo "    --xnatstudyinputpath=<path>                        The path to the previously generated session data as mounted for the container. Default is /input/RESOURCES/mnap_session"
    echo "    --batchfile=<batch_file>                           Batch file with processing parameters which exist as a project-level resource on XNAT"
    echo "    --mappingfile=<mapping_file>                       File for mapping into desired file structure, e.g. hcp, which exist as a project-level resource on XNAT"
    echo ""
    echo ""
    echo "  -- MISC. PARMETERS:"
    echo ""
    echo "    --bidsformat=<specify_bids_input>                          Specify if input data is in BIDS format (yes/no). Default is [no]"
    echo "                                                               Note: If --bidsformat='yes' and XNAT run is requested then --xnatsessionlabel is required."
    echo "                                                                     If --bidsformat='yes' and XNAT run is NOT requested then "
    echo "                                                                          BIDS data expected in --> <subjects_folder/inbox/BIDS"
    echo ""
    echo "    --rawdatainput=<specify_absolute_path_of_raw_data>         If --turnkeytype is not XNAT then specify location of raw data on the file system for a subject."
    echo "                                                                    Default is [] for the XNAT type run as host is used to pull data."
    echo "    --workingdir=<specify_directory_where_study_is_located>    Specify where the study folder is to be created or resides. Default is [/output]."
    echo "    --projectname=<specify_project_name>                       Specify name of the project on local file system if XNAT is not specified."
    echo "    --local_batchfile=<batch_file>                             Absolute path to local batch file with pre-configured processing parameters. Not supported for XNAT run." 
    echo "                                                                 Default is ~/<project_name>/processing/<project_name>_batch_params.txt"
    echo "    --overwritestep=<specify_step_to_overwrite>                Specify <yes> or <no> for delete of prior workflow step. Default is [no]."
    echo "    --overwritesubject=<specify_subject_overwrite>             Specify <yes> or <no> for delete of prior subject run. Default is [no]."
    echo "    --overwriteproject=<specify_project_overwrite>             Specify <yes> or <no> for delete of entire project prior to run. Default is [no]."
    echo "    --overwriteprojectxnat=<specify_xnat_project_overwrite>    Specify <yes> or <no> for delete of entire XNAT project folder prior to run. Default is [no]."
    echo "    --cleanupsubject=<specify_subject_clean>                   Specify <yes> or <no> for cleanup of subject folder after steps are done. Default is [no]."
    echo "    --cleanupproject=<specify_project_clean>                   Specify <yes> or <no> for cleanup of entire project after steps are done. Default is [no]."
    echo "    --cleanupoldfiles=<specify_old_clean>                      Specify <yes> or <no> for cleanup of files that are older than start of run (XNAT run only). Default is [no]."
    echo ""
    echo "  -- OPTIONAL CUSTOM QC PARAMETERS:"
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
    echo "" 
    echo "-- EXAMPLES:"
    echo ""
    echo "   --> Run directly via ${TOOLS}/${MNAPREPO}/connector/functions/RunTurnkey.sh --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
    echo ""
    reho "           * NOTE: --scheduler is not available via direct script call."
    echo ""
    echo "   --> Run via mnap runTurnkey --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
    echo ""
    geho "           * NOTE: scheduler is available via mnap call:"
    echo "                   --scheduler=<name_of_cluster_scheduler_and_options>  A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
    echo ""
    echo "           * For SLURM scheduler the string would look like this via the mnap call: "
    echo "                   --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
    echo ""
    echo ""
    echo "  RunTurnkey.sh \ "
    echo "   --turnkeytype=<turnkey_run_type> \ "
    echo "   --turnkeysteps=<turnkey_worlflow_steps> \ "
    echo "   --batchfile=<batch_file> \ "
    echo "   --overwritestep=yes \ "
    echo "   --mappingfile=<mapping_file> \ "
    echo "   --xnatsubjectlabel=<XNAT_SUBJECT_LABEL> \ "
    echo "   --xnatsessionlabel=<XNAT_SESSION_LABEL> \ "
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
unset CASE
unset OVERWRITE_STEP
unset OVERWRITE_PROJECT
unset OVERWRITE_PROJECT_FORCE
unset OVERWRITE_PROJECT_XNAT
unset OVERWRITE_SUBJECT
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
unset workdir
unset RawDataInputPath
unset PROJECT_NAME
unset PlotElements
unset CleanupSubject
unset CleanupProject
unset STUDY_PATH
unset LOCAL_BATCH_FILE
unset BIDSFormat
unset AcceptanceTest
unset CleanupOldFiles

echo ""
echo " -- Reading inputs... "
echo ""

# =-=-=-=-=-= GENERAL OPTIONS =-=-=-=-=-=
#
# -- General input flags
STUDY_PATH=`opts_GetOpt "--path" $@`
workdir=`opts_GetOpt "--workingdir" $@`
PROJECT_NAME=`opts_GetOpt "--projectname" $@`
CleanupSubject=`opts_GetOpt "--cleanupsubject" $@`
CleanupProject=`opts_GetOpt "--cleanupproject" $@`
CleanupOldFiles=`opts_GetOpt "--cleanupoldfiles" $@`
RawDataInputPath=`opts_GetOpt "--rawdatainput" $@`
mnap_subjectsfolder=`opts_GetOpt "--subjectsfolder" $@`

#CASES=`opts_GetOpt "--subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "${CASES}" | sed 's/,/ /g;s/|/ /g'`
CASE=`opts_GetOpt "--subjects" "$@"`
if [ -z "$CASE" ]; then
CASE=`opts_GetOpt "--subject" "$@"`
fi
SUBJID=`opts_GetOpt "--subjids"`
if [ -z "$SUBJID" ]; then
SUBJID=`opts_GetOpt "--subjid"`
fi

OVERWRITE_SUBJECT=`opts_GetOpt "--overwritesubject" $@`
OVERWRITE_STEP=`opts_GetOpt "--overwritestep" $@`
OVERWRITE_PROJECT=`opts_GetOpt "--overwriteproject" $@`
OVERWRITE_PROJECT_FORCE=`opts_GetOpt "--overwriteprojectforce" $@`
OVERWRITE_PROJECT_XNAT=`opts_GetOpt "--overwriteprojectxnat" $@`
BATCH_PARAMETERS_FILENAME=`opts_GetOpt "--batchfile" $@`
LOCAL_BATCH_FILE=`opts_GetOpt "--local_batchfile" $@`
SCAN_MAPPING_FILENAME=`opts_GetOpt "--mappingfile" $@`

XNAT_HOST_NAME=`opts_GetOpt "--xnathost" $@`
XNAT_USER_NAME=`opts_GetOpt "--xnatuser" $@`
XNAT_PASSWORD=`opts_GetOpt "--xnatpass" $@`
XNAT_STUDY_INPUT_PATH=`opts_GetOpt "--xnatstudyinputpath" $@`
#  
#     INFO ON XNAT VARIABLE MAPPING FROM MNAP --> JSON --> XML specification
#
# project               --xnatprojectid        #  --> mapping in MNAP: XNAT_PROJECT_ID     --> mapping in JSON spec: #XNAT_PROJECT#   --> Corresponding to project id in XML. 
#   │ 
#   └──subject          --xnatsubjectid        #  --> mapping in MNAP: XNAT_SUBJECT_ID     --> mapping in JSON spec: #SUBJECTID#      --> Corresponding to subject ID in subject-level XML (Subject Accession ID). EXAMPLE in XML        <xnat:subject_ID>BID11_S00192</xnat:subject_ID>
#        │                                                                                                                                                                                                         EXAMPLE in Web UI     Accession number:  A unique XNAT-wide ID for a given human irrespective of project within the XNAT Site
#        │              --xnatsubjectlabel     #  --> mapping in MNAP: XNAT_SUBJECT_LABEL  --> mapping in JSON spec: #SUBJECTLABEL#   --> Corresponding to subject label in subject-level XML (Subject Label).     EXAMPLE in XML        <xnat:field name="SRC_SUBJECT_ID">CU0018</xnat:field>
#        │                                                                                                                                                                                                         EXAMPLE in Web UI     Subject Details:   A unique XNAT project-specific ID that matches the experimenter expectations
#        │ 
#        └──experiment  --xnataccsessionid     #  --> mapping in MNAP: XNAT_ACCSESSION_ID  --> mapping in JSON spec: #ID#             --> Corresponding to subject session ID in session-level XML (Subject Accession ID)   EXAMPLE in XML       <xnat:experiment ID="BID11_E00048" project="embarc_r1_0_0" visit_id="ses-wk2" label="CU0018_MRwk2" xsi:type="xnat:mrSessionData">
#                                                                                                                                                                                                                           EXAMPLE in Web UI    Accession number:  A unique project specific ID for that subject
#                       --xnatsessionlabel     #  --> mapping in MNAP: XNAT_SESSION_LABEL  --> mapping in JSON spec: #LABEL#          --> Corresponding to session label in session-level XML (Session/Experiment Label)    EXAMPLE in XML       <xnat:experiment ID="BID11_E00048" project="embarc_r1_0_0" visit_id="ses-wk2" label="CU0018_MRwk2" xsi:type="xnat:mrSessionData">
#                                                                                                                                                                                                                           EXAMPLE in Web UI    MR Session:   A project-specific, session-specific and subject-specific XNAT variable that defines the precise acquisition / experiment
#
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
TURNKEY_TYPE=`opts_GetOpt "--turnkeytype" $@`
TURNKEY_CLEAN=`opts_GetOpt "--turnkeycleanstep" $@`

BIDSFormat=`opts_GetOpt "--bidsformat" $@`
AcceptanceTest=`opts_GetOpt "--acceptancetest" "$@" | sed 's/,/ /g;s/|/ /g'`; AcceptanceTest=`echo "${AcceptanceTest}" | sed 's/,/ /g;s/|/ /g'`

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
# -- BOLDParcellation input flags
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
BOLDfc=`opts_GetOpt "--boldfc" $@`
BOLDfcInput=`opts_GetOpt "--boldfcinput" $@`
BOLDfcPath=`opts_GetOpt "--boldfcpath" $@`
GeneralSceneDataFile=`opts_GetOpt "--datafile" $@`
GeneralSceneDataPath=`opts_GetOpt "--datapath" $@`

BOLDS=`opts_GetOpt "--bolds" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`
if [ -z "${BOLDS}" ]; then
    BOLDS=`opts_GetOpt "--boldruns" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`
fi
if [ -z "${BOLDS}" ]; then
    BOLDS=`opts_GetOpt "--bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`
fi
BOLDRUNS="${BOLDS}"
BOLDDATA="${BOLDS}"

BOLDSuffix=`opts_GetOpt "--boldsuffix" $@`
BOLDPrefix=`opts_GetOpt "--boldprefix" $@`
SkipFrames=`opts_GetOpt "--skipframes" $@`
SNROnly=`opts_GetOpt "--snronly" $@`
TimeStamp=`opts_GetOpt "--timestamp" $@`
Suffix=`opts_GetOpt "--suffix" $@`
SceneZip=`opts_GetOpt "--scenezip" $@`
QCPreprocCustom=`opts_GetOpt "--customqc" $@`
HCPSuffix=`opts_GetOpt "--hcp_suffix" $@`

# -- g_PlotsBoldTS input flags
QCPlotElements=`opts_GetOpt "--qcplotelements" $@`
QCPlotImages=`opts_GetOpt "--qcplotimages" $@`
QCPlotMasks=`opts_GetOpt "--qcplotmasks" $@`

# -- Define script name
scriptName=$(basename ${0})

# -- Check workdir and STUDY_PATH
if [[ -z ${workdir} ]]; then 
    workdir="/output"; reho " -- Note: Working directory where study is located is missing. Setting defaults: ${workdir}"; echo ''
fi

# -- Check and set turnkey type
if [[ -z ${TURNKEY_TYPE} ]]; then 
    TURNKEY_TYPE="xnat"; reho " -- Note: Turnkey type not specified. Setting default turnkey type to: ${TURNKEY_TYPE}"; echo ''
fi

# -- Check and set AcceptanceTest type
if [[ -z ${AcceptanceTest} ]]; then 
    AcceptanceTest="no"; reho " -- Note: Acceptance Test type not specified. Setting default turnkey type to: ${AcceptanceTest}"; echo ''
fi

# -- Check and set turnkey clean
if [[ -z ${TURNKEY_CLEAN} ]]; then 
    TURNKEY_CLEAN="no"; reho " -- Note: Turnkey cleaning not specified. Setting default to: ${TURNKEY_CLEAN}"; echo ''
fi

########################  XNAT SPECIFIC CHECKS  ################################
#
# -- Check and set non-XNAT or XNAT specific parameters
if [[ ${TURNKEY_TYPE} != "xnat" ]]; then 
   if [[ -z ${PROJECT_NAME} ]]; then reho "Error: Project name is missing."; exit 1; echo ''; fi
   if [[ -z ${STUDY_PATH} ]]; then STUDY_PATH=${workdir}/${PROJECT_NAME}; fi
   if [[ -z ${CASE} ]]; then reho "Error: Requesting local run but --subject flag is missing."; exit 1; echo ''; fi
fi
if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
    if [[ -z ${XNAT_PROJECT_ID} ]]; then reho "Error: --xnatprojectid flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${XNAT_HOST_NAME} ]]; then reho "Error: --xnathost flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${XNAT_USER_NAME} ]]; then reho "Error: --xnatuser flag missing. Username parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${XNAT_PASSWORD} ]]; then reho "Error: --xnatpass flag missing. Password parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${STUDY_PATH} ]]; then STUDY_PATH=${workdir}/${XNAT_PROJECT_ID}; fi
    if [[ -z ${XNAT_SUBJECT_ID} ]] && [[ -z ${XNAT_SUBJECT_LABEL} ]]; then reho "Error: --xnatsubjectid or --xnatsubjectlabel flags are missing. Please specify either subject id or subject label and re-run."; echo ''; exit 1; fi
    if [[ -z ${XNAT_SUBJECT_ID} ]] && [[ ! -z ${XNAT_SUBJECT_LABEL} ]]; then reho " -- Note: --xnatsubjectid is not set. Using --xnatsubjectlabel to query XNAT."; echo ''; fi
    if [[ ! -z ${XNAT_SUBJECT_ID} ]] && [[ -z ${XNAT_SUBJECT_LABEL} ]]; then reho " -- Note: --xnatsubjectlabel is not set. Using --xnatsubjectid to query XNAT."; echo ''; fi
    if [[ -z ${XNAT_SESSION_LABEL} ]]; then reho "Error: --xnatsessionlabel flag missing. Please specify session label and re-run."; echo ''; exit 1; fi
    if [[ -z ${XNAT_STUDY_INPUT_PATH} ]]; then XNAT_STUDY_INPUT_PATH=/input/RESOURCES/mnap_study; reho " -- Note: XNAT session input path is not defined. Setting default path to: $XNAT_STUDY_INPUT_PATH"; echo ""; fi
    
    # -- Curl calls to set correct subject and session variables at start of RunTurnkey

    # -- Clean prior mapping
    rm -r ${HOME}/xnatlogs &> /dev/null
    mkdir ${HOME}/xnatlogs &> /dev/null
    XNATINFOTMP="${HOME}/xnatlogs"
    TimeStampCurl=`date +%Y-%m-%d_%H.%M.%10N`

    if [[ ${CleanupOldFiles} == "yes" ]]; then 
        if [ ! -d ${workdir} ]; then
            mkdir -p ${workdir} &> /dev/null
        fi
        touch ${workdir}/_startfile
    fi
    
    # -- Obtain temp info on subjects and experiments in the project
    curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/subjects?project=${XNAT_PROJECT_ID}&format=csv" > ${XNATINFOTMP}/${XNAT_PROJECT_ID}_subjects_${TimeStampCurl}.csv
    curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/experiments?project=${XNAT_PROJECT_ID}&format=csv" > ${XNATINFOTMP}/${XNAT_PROJECT_ID}_experiments_${TimeStampCurl}.csv
    
    # -- Define XNAT_SUBJECT_ID (i.e. Accession number) and XNAT_SESSION_LABEL (i.e. MR Session lablel) for the specific XNAT_SUBJECT_LABEL (i.e. subject)
    if [[ -z ${XNAT_SUBJECT_ID} ]]; then XNAT_SUBJECT_ID=`more ${XNATINFOTMP}/${XNAT_PROJECT_ID}_subjects_${TimeStampCurl}.csv | grep "${XNAT_SUBJECT_LABEL}" | awk  -F, '{print $1}'`; fi
    if [[ -z ${XNAT_SUBJECT_LABEL} ]]; then XNAT_SUBJECT_LABEL=`more ${XNATINFOTMP}/${XNAT_PROJECT_ID}_subjects_${TimeStampCurl}.csv | grep "${XNAT_SUBJECT_ID}" | awk  -F, '{print $3}'`; fi
    # -- Re-obtain the label from the database just in case it was mis-specified
    if [[ -z ${XNAT_SUBJECT_LABEL} ]]; then XNAT_SESSION_LABEL=`more ${XNATINFOTMP}/${XNAT_PROJECT_ID}_experiments_${TimeStampCurl}.csv | grep "${XNAT_SUBJECT_LABEL}" | grep "${XNAT_SESSION_LABEL}" | awk  -F, '{print $5}'`; fi
    if [[ -z ${XNAT_ACCSESSION_ID} ]]; then XNAT_ACCSESSION_ID=`more ${XNATINFOTMP}/${XNAT_PROJECT_ID}_experiments_${TimeStampCurl}.csv | grep "${XNAT_SUBJECT_LABEL}" | grep "${XNAT_SESSION_LABEL}" | awk  -F, '{print $1}'`; fi

    # -- Clean up temp curl call info
    rm -r ${HOME}/xnatInfoTmp &> /dev/null

    # -- Report error if variables remain undefined
    if [[ -z ${XNAT_SUBJECT_ID} ]] || [[ -z ${XNAT_SUBJECT_LABEL} ]] || [[ -z ${XNAT_ACCSESSION_ID} ]] || [[ -z ${XNAT_SESSION_LABEL} ]]; then 
        echo ""
        reho "Some or all of XNAT database variables were not set correctly: "
        echo ""
        reho "  --> XNAT_SUBJECT_ID     :  $XNAT_SUBJECT_ID "
        reho "  --> XNAT_SUBJECT_LABEL  :  $XNAT_SUBJECT_LABEL "
        reho "  --> XNAT_ACCSESSION_ID  :  $XNAT_ACCSESSION_ID "
        reho "  --> XNAT_SESSION_LABEL  :  $XNAT_SESSION_LABEL "
        echo ""        
        exit 1
    else
        echo ""
        geho "Successfully read all XNAT database variables: "
        echo ""
        geho "  --> XNAT_SUBJECT_ID     :  $XNAT_SUBJECT_ID "
        geho "  --> XNAT_SUBJECT_LABEL  :  $XNAT_SUBJECT_LABEL "
        geho "  --> XNAT_ACCSESSION_ID  :  $XNAT_ACCSESSION_ID "
        geho "  --> XNAT_SESSION_LABEL  :  $XNAT_SESSION_LABEL "
        echo ""
    fi

    # -- Define final variable set
    if [[ ${BIDSFormat} == "yes" ]]; then
        # -- Setup CASE without the 'MR' prefix in the XNAT_SESSION_LABEL
        #    Eventually deprecate once fixed in XNAT
        CASE=`echo ${XNAT_SESSION_LABEL} | sed 's|MR||g'`
        reho " -- Note: --bidsformat='yes' " 
        reho "       Combining XNAT_SUBJECT_LABEL and XNAT_SESSION_LABEL into unified BIDS-compliant subject variable for MNAP run: ${CASE}"
        echo ""
    else
        CASE="${XNAT_SUBJECT_LABEL}"
    fi
fi
#
################################################################################


# -- Check TURNKEY_STEPS
if [[ -z ${TURNKEY_STEPS} ]] && [ ! -z "${MNAPTurnkeyWorkflow##*${AcceptanceTest}*}" ]; then 
    echo ""
    reho "ERROR: Turnkey steps flag missing. Specify supported turnkey steps:"
    echo "-------------------------------------------------------------------"
    echo " ${MNAPTurnkeyWorkflow}"
    echo ''
    exit 1
fi

# -- Check TURNKEY_STEPS test flag
unset FoundSupported
echo ""
geho "--> Checking that requested ${TURNKEY_STEPS} are supported..."
echo ""
TurnkeyTestStepChecks="${TURNKEY_STEPS}"
unset TurnkeyTestSteps
for TurnkeyTestStep in ${TurnkeyTestStepChecks}; do
   if [ ! -z "${MNAPTurnkeyWorkflow##*${TurnkeyTestStep}*}" ]; then
       echo ""
       reho "--> ${TurnkeyTestStep} is not supported. Will remove from requested list."
       echo ""
   else
       echo ""
       geho "--> ${TurnkeyTestStep} is supported."
       echo ""
       FoundSupported="yes"
       TurnkeyTestSteps="${TurnkeyTestSteps} ${TurnkeyTestStep}"
   fi
done
if [[ -z ${FoundSupported} ]]; then 
    usage
    echo ""
    reho "ERROR: None of the requested acceptance tests are currently supported."; echo "";
    reho "Supported: ${MNAPTurnkeyWorkflow}"; echo "";
    exit 1
else
    TURNKEY_STEPS="${TurnkeyTestSteps}"
    echo ""
    geho "--> Verified list of supported Turnkey steps to be run: ${TURNKEY_STEPS}"
    echo ""
fi

# -- Check acceptance test flag
if [[ ! -z ${AcceptanceTestSteps} ]]; then 
    # -- Run checks for supported steps
    unset FoundSupported
    echo ""
    geho "--> Checking that requested ${AcceptanceTestSteps} are supported..."
    echo ""
    AcceptanceTestStepsChecks="${AcceptanceTestSteps}"
    unset AcceptanceTestSteps
    for AcceptanceTestStep in ${AcceptanceTestStepsChecks}; do
       if [ ! -z "${SupportedAcceptanceTestSteps##*${AcceptanceTestStep}*}" ]; then
           echo ""
           reho "--> ${AcceptanceTestStep} is not supported. Will remove from requested list."
           echo ""
       else
           echo ""
           geho "--> ${AcceptanceTestStep} is supported."
           echo ""
           FoundSupported="yes"
           AcceptanceTestSteps="${AcceptanceTestSteps} ${AcceptanceTestStep}"
       fi
    done
    if [[ -z ${FoundSupported} ]]; then 
        usage
        reho "ERROR: None of the requested acceptance tests are currently supported."; echo "";
        reho "Supported: ${SupportedAcceptanceTestSteps}"; echo "";
    fi
fi

# -- Check if subject input is a parameter file instead of list of cases
# if [[ ${CASE} == *.txt ]]; then
#     SubjectParamFile="$CASE"
#     echo ""
#     echo "Using $SubjectParamFile for input."
#     echo ""
#     CASE=`more ${SubjectParamFile} | grep "id:"| cut -d " " -f 2`
# fi

# -- Check and set mapRawData, mapHCPFiles, getHCPReady which rely on BATCH_PARAMETERS_FILENAME and SCAN_MAPPING_FILENAME
if [[ `echo ${TURNKEY_STEPS} | grep 'mapRawData'` ]]; then
    if [ -z "$BATCH_PARAMETERS_FILENAME" ]; then reho "Error: --batchfile flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    if [ -z "$SCAN_MAPPING_FILENAME" ]; then reho "Error: --mappingfile flag missing. Batch parameter file not specified."; echo ''; exit 1;  fi
fi
if [[ `echo ${TURNKEY_STEPS} | grep 'mapHCPFiles'` ]]; then
    if [ -z "$BATCH_PARAMETERS_FILENAME" ]; then reho "Error: --batchfile flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
fi
if [[ `echo ${TURNKEY_STEPS} | grep 'getHCPReady'` ]]; then
    if [ -z "$SCAN_MAPPING_FILENAME" ]; then reho "Error: --mappingfile flag missing. Batch parameter file not specified."; echo ''; exit 1;  fi
fi
if [[ ${TURNKEY_TYPE} != "xnat" ]] && [[ -z ${RawDataInputPath} ]] && [[ `echo ${TURNKEY_STEPS} | grep 'mapRawData'` ]]; then
   reho "Error. Raw data input flag missing "; exit 1
fi

########################  ALIGN SUBJECT INFORMATION  ###########################
#
#                    **** DEPRECATED AFTER BIDS UPGRADES *****
#
# -- non-XNAT run: Check and align CASE and XNAT_SUBJECT_LABEL variables
#
#   if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
#      if [ -z "$CASE" ]; then
#          if [ -z "$XNAT_SUBJECT_LABEL" ]; then
#              reho "Error: --xnatsubjectlabel and --subject flag missing. Specify one."; echo ""
#              exit 1
#          else
#              CASE="$XNAT_SUBJECT_LABEL"
#              reho " -- Note: --xnatsubjectlabel is specified. Assuming --subject info matches on local file system."; echo ""
#          fi
#      else
#          XNAT_SUBJECT_LABEL="$CASE"
#          reho " -- Note: --subject is specified. Assuming --xnatsubjectlabel info matches in XNAT database."; echo ""
#      fi
#   fi
#   #
#   # -- XNAT run: Align CASE and XNAT_SUBJECT_LABEL using XNAT_SUBJECT_LABEL or XNAT_SUBJECT_ID
#   #
#   if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
#      if [ -z "$XNAT_SUBJECT_LABEL" ]; then
#          if [ -z "$CASE" ]; then
#              reho "Error: --xnatsubjectlabel and --subject flag missing. Specify one."; echo ""
#              exit 1
#          else
#              XNAT_SUBJECT_LABEL="$CASE"
#              reho " -- Note: --subject is specified. Assuming --xnatsubjectlabel info matches in XNAT database."; echo ""
#          fi
#      else
#          CASE="$XNAT_SUBJECT_LABEL"
#          reho " -- Note: --xnatsubjectlabel is specified. Assuming --subject info matches on local file system."; echo ""
#      fi
#   fi
#
################################################################################

# -- Check and set overwrites
if [ -z "$OVERWRITE_STEP" ]; then OVERWRITE_STEP="no"; fi
if [ -z "$OVERWRITE_SUBJECT" ]; then OVERWRITE_SUBJECT="no"; fi
if [ -z "$OVERWRITE_PROJECT" ]; then OVERWRITE_PROJECT="no"; fi
if [[ -z "$OVERWRITE_PROJECT_XNAT" ]]; then OVERWRITE_PROJECT_XNAT="no"; fi
if [[ -z "$CleanupProject" ]]; then CleanupProject="no"; fi
if [[ -z "$CleanupSubject" ]]; then CleanupSubject="no"; fi

# -- Check and set QCPreprocCustom
if [ -z "$QCPreprocCustom" ] || [ "$QCPreprocCustom" == "no" ]; then QCPreprocCustom=""; MNAPTurnkeyWorkflow=`printf '%s\n' "${MNAPTurnkeyWorkflow//QCPreprocCustom/}"`; fi

# -- Check and set DWILegacy
if [ -z "$DWILegacy" ] || [ "$DWILegacy" == "no" ]; then 
    DWILegacy=""
    QCPreprocDWILegacy=""
    MNAPTurnkeyWorkflow=`printf '%s\n' "${MNAPTurnkeyWorkflow//hcpdLegacy/}"`
    MNAPTurnkeyWorkflow=`printf '%s\n' "${MNAPTurnkeyWorkflow//QCPreprocDWILegacy/}"`
fi

mnap_studyfolder="${STUDY_PATH}"
mnap_subjectsfolder="${STUDY_PATH}/subjects"
mnap_workdir="${STUDY_PATH}/subjects/${CASE}"
processingdir="${STUDY_PATH}/processing"
logdir="${STUDY_PATH}/processing/logs"
specsdir="${STUDY_PATH}/subjects/specs"
rawdir="${mnap_workdir}/inbox"
rawdir_temp="${mnap_workdir}/inbox_temp"
MNAPCOMMAND="${TOOLS}/${MNAPREPO}/connector/mnap.sh"

if [ "$TURNKEY_TYPE" == "xnat" ]; then
   project_batch_file="${processingdir}/${XNAT_PROJECT_ID}_batch_params.txt"
fi
if [ "$TURNKEY_TYPE" != "xnat" ] && [ -z "$LOCAL_BATCH_FILE" ]; then
   project_batch_file="${processingdir}/${PROJECT_NAME}_batch_params.txt"
fi
if [ "$TURNKEY_TYPE" != "xnat" ] && [ ! -z "$LOCAL_BATCH_FILE" ]; then
   project_batch_file="${LOCAL_BATCH_FILE}"
fi

# -- Report options
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   "
echo "   MNAP Turnkey run type: ${TURNKEY_TYPE}"
echo "   MNAP Turnkey clean interim files: ${TURNKEY_CLEAN}"

if [ "$TURNKEY_TYPE" == "xnat" ]; then
    echo "   XNAT Hostname: ${XNAT_HOST_NAME}"
    echo "   XNAT Project ID: ${XNAT_PROJECT_ID}"
    echo "   XNAT Subject Label: ${XNAT_SUBJECT_LABEL}"
    echo "   XNAT Subject ID: ${XNAT_SUBJECT_ID}"
    echo "   XNAT Session Label: ${XNAT_SESSION_LABEL}"
    echo "   XNAT Session ID: ${XNAT_ACCSESSION_ID}"
    echo "   XNAT Resource Mapping file: ${XNAT_HOST_NAME}"
    echo "   XNAT Resource Batch file: ${BATCH_PARAMETERS_FILENAME}"
    if [ "$BIDSFormat" == "yes" ]; then
        echo "   BIDS format input specified: ${BIDSFormat}"
        echo "   Combined BIDS-formatted subject name: ${CASE}"
    else 
        echo "   MNAP Subject variable name: ${CASE}" 
    fi
fi
if [ "$TURNKEY_TYPE" != "xnat" ]; then
    echo "   Local project name: ${PROJECT_NAME}"
    echo "   Raw data input path: ${RawDataInputPath}"
    echo "   MNAP Subject variable name: ${CASE}" 
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

if [ "$QCPreprocCustom" == "yes" ]; then
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

if [[ ! -z "${SUBJID}" ]]; then 
echo "   Subjid parameter: ${SUBJID}"
fi

if [ "$TURNKEY_STEPS" == "all" ]; then
    echo "   Turnkey workflow steps: ${MNAPTurnkeyWorkflow}"
else
    echo "   Turnkey workflow steps: ${TURNKEY_STEPS}"
fi
echo "   Acceptance test requested: ${AcceptanceTest}"
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of MNAP Turnkey Workflow --------------------------------"
echo ""

# --- Report the environment variables for MNAP Turnkey run: 
echo ""
bash ${TOOLS}/${MNAPREPO}/library/environment/mnap_envStatus.sh --envstatus
echo ""

# ---- Map the data from input to output when in XNAT workflow
if [[ ${TURNKEY_TYPE} == "xnat" ]] && [[ ${OVERWRITE_PROJECT_XNAT} != "yes" ]] ; then
    # --- Specify what to map
    firstStep=`echo ${TURNKEY_STEPS} | awk '{print $1;}'`
    echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: Initial data re-map from XNAT with ${firstStep} as starting point ..."; echo ""
    # --- Create a study folder
    geho " -- Creating study folder structure... "; echo ""
    ${MNAPCOMMAND} createStudy "${mnap_studyfolder}"
    geho " -- Mapping existing data into place to support the first turnkey step: ${firstStep}"; echo ""
    # --- Work through the mapping steps
    case ${firstStep} in
        organizeDicom)
            # --- rsync relevant dependencies if organizeDicom is starting point 
            RsyncCommand="rsync -avzH --include='/subjects' --include='${CASE}' --include='inbox/***' --include='specs/***' --include='/processing' --include='scenes/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${mnap_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        getHCPReady|mapHCPFiles)
            # --- rsync relevant dependencies if getHCPReady or mapHCPFiles is starting point 
            RsyncCommand="rsync -avzH --include='/subjects' --include='${CASE}' --include='*.txt' --include='specs/***' --include='nii/***' --include='/processing' --include='scenes/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${mnap_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        hcp1|hcp2|hcp3|QCPreprocT1W|QCPreprocT2W|QCPreprocMyelin)
            # --- rsync relevant dependencies if and hcp or QC step is starting point
            RsyncCommand="rsync -avzH --include='/processing' --include='scenes/***' --include='specs/***' --include='/subjects' --include='${CASE}' --include='*.txt' --include='hcp/' --include='MNINonLinear/***' --include='T1w/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${mnap_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        hcp4|hcp5|QCPreprocBOLD)
            # --- rsync relevant dependencies if and hcp or QC step is starting point
            RsyncCommand="rsync -avzH --include='/processing' --include='scenes/***' --include='specs/***' --include='/subjects' --include='${CASE}' --include='*.txt' --include='hcp/' --include='MNINonLinear/***' --include='T1w/***' --include='BOLD*/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${mnap_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        hcpd|QCPreprocDWI|hcpdLegacy|QCPreprocDWILegacy|eddyQC|QCPreprocDWIeddyQC|FSLDtifit|QCPreprocDWIDTIFIT|FSLBedpostxGPU|QCPreprocDWIProcess|QCPreprocDWIBedpostX|pretractographyDense|DWIDenseParcellation|DWISeedTractography|QCPreprocCustom)
            # --- rsync relevant dependencies if and hcp or QC step is starting point
            RsyncCommand="rsync -avzH --include='/processing' --include='scenes/***' --include='specs/***' --include='/subjects' --include='${CASE}' --include='*.txt' --include='hcp/' --include='MNINonLinear/***' --include='T1w/***' --include='Diffusion/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${mnap_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        QCPreprocCustom)
            # --- rsync relevant dependencies if and hcp or QC step is starting point
            RsyncCommand="rsync -avzH --include='/processing' --include='scenes/***' --include='specs/***' --include='/subjects' --include='${CASE}' --include='*.txt' --include='hcp/' --include='MNINonLinear/***' --include='T1w/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${mnap_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        mapHCPData)
            # --- rsync relevant dependencies if and mapHCPData is starting point
            RsyncCommand="rsync -avzH --include='/processing' --include='scenes/***' --include='specs/***' --include='/subjects' --include='${CASE}/' --include='*.txt' --include='hcp/' --include='MNINonLinear/***' --include='T1w/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${mnap_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        createBOLDBrainMasks|computeBOLDStats|createStatsReport|extractNuisanceSignal|preprocessBold|preprocessConc|g_PlotBoldTS|BOLDParcellation|computeBOLDfcGBC|computeBOLDfcSeed|QCPreprocBOLDfc)
            # --- rsync relevant dependencies if any BOLD fc step is starting point
            RsyncCommand="rsync -avzH --include='/processing' --include='specs/***' --include='scenes/***' --include='/subjects' --include='${CASE}' --include='*.txt' --include='images/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${mnap_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
    esac
    echo ""; cyaneho " ===> RunTurnkey ~~~ DONE: Initial data re-map from XNAT for ${firstStep} done."; echo ""
fi

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
        reho " -- Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${mnap_studyfolder}/ &> /dev/null
fi
if [[ ${OVERWRITE_PROJECT} == "yes" ]] && [[ ${TURNKEY_STEPS} == "all" ]]; then
    if [[ `ls -IQC -Ilists -Ispecs -Iinbox -Iarchive ${mnap_subjectsfolder}` == "$CASE" ]]; then
        reho " -- ${CASE} is the only folder in ${mnap_subjectsfolder}. OK to proceed!"
        reho "    Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${mnap_studyfolder}/ &> /dev/null
    else
        reho " -- ${CASE} is not the only folder in ${mnap_studyfolder}."
        reho "    Skipping recursive overwrite for project: ${XNAT_PROJECT_ID}"; echo ""
    fi
fi
if [[ ${OVERWRITE_PROJECT} == "yes" ]] && [[ ${TURNKEY_STEPS} == "createStudy" ]]; then
    if [[ `ls -IQC -Ilists -Ispecs -Iinbox -Iarchive ${mnap_subjectsfolder}` == "$CASE" ]]; then
        reho " -- ${CASE} is the only folder in ${mnap_subjectsfolder}. OK to proceed!"
        reho "    Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${mnap_studyfolder}/ &> /dev/null
    else
        reho " -- ${CASE} is not the only folder in ${mnap_studyfolder}."
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
        createStudy_ComlogTmp="${workdir}/tmp_createStudy_${CASE}_${TimeStamp}.log"; touch ${createStudy_ComlogTmp}; chmod 777 ${createStudy_ComlogTmp}
        createStudy_ComlogError="${logdir}/comlogs/error_createStudy_${CASE}_${TimeStamp}.log"
        createStudy_ComlogDone="${logdir}/comlogs/done_createStudy_${CASE}_${TimeStamp}.log"
        geho " -- Checking for and generating study folder ${mnap_studyfolder}"; echo ""
        if [ ! -d ${workdir} ]; then
            mkdir -p ${workdir} &> /dev/null
        fi
        if [ ! -d ${mnap_studyfolder} ]; then
            reho " -- Note: ${mnap_studyfolder} not found. Regenerating now..." 2>&1 | tee -a ${createStudy_ComlogTmp}  
            echo "" 2>&1 | tee -a ${createStudy_ComlogTmp}
            ${MNAPCOMMAND} createStudy "${mnap_studyfolder}"
            mv ${createStudy_ComlogTmp} ${logdir}/comlogs/
            createStudy_ComlogTmp="${logdir}/comlogs/tmp_createStudy_${CASE}_${TimeStamp}.log"
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
                    createStudy_ComlogTmp="${logdir}/comlogs/tmp_createStudy_${CASE}_${TimeStamp}.log"
                fi
            fi
        fi
        if [ ! -f ${mnap_studyfolder}/.mnapstudy ]; then
            reho " -- Note: ${mnap_studyfolder}mnapstudy file not found. Not a proper MNAP file hierarchy. Regenerating now..."; echo "";
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
        
        # Perform checks for output MNAP hierarchy
        if [ ! -d ${workdir} ]; then
            mkdir -p ${workdir} &> /dev/null
        fi
        if [ ! -d ${mnap_studyfolder} ]; then
            reho " -- Note: ${mnap_studyfolder} not found. Regenerating now..."; echo "";
            ${MNAPCOMMAND} createStudy "${mnap_studyfolder}"
        fi
        if [ ! -f ${mnap_studyfolder}/.mnapstudy ]; then
            reho " -- Note: ${mnap_studyfolder} mnapstudy file not found. Not a proper MNAP file hierarchy. Regenerating now..."; echo "";
            ${MNAPCOMMAND} createStudy "${mnap_studyfolder}"
        fi
        if [ ! -d ${mnap_subjectsfolder} ]; then
            reho " -- Note: ${mnap_subjectsfolder} folder not found. Not a proper MNAP file hierarchy. Regenerating now..."; echo "";
            ${MNAPCOMMAND} createStudy "${mnap_studyfolder}"
        fi
        if [ ! -f ${mnap_workdir} ]; then
            reho " -- Note: ${mnap_workdir} not found. Creating one now..."; echo ""
            mkdir -p ${mnap_workdir} &> /dev/null
            mkdir -p ${mnap_workdir}/inbox &> /dev/null
            mkdir -p ${mnap_workdir}/inbox_temp &> /dev/null
        fi
        
        # -- Perform overwrite checks
        if [[ ${OVERWRITE_STEP} == "yes" ]] && [[ ${TURNKEY_STEP} == "mapRawData" ]]; then
               rm -f ${mnap_workdir}/inbox/* &> /dev/null
        fi
        CheckInbox=`ls -1A ${rawdir} | wc -l`
        if [[ ${CheckInbox} != "0" ]] && [[ ${OVERWRITE_STEP} == "no" ]]; then
               reho "Error: ${mnap_workdir}/inbox/ is not empty and --overwritestep=${OVERWRITE_STEP} "
               reho "Set overwrite to 'yes' and re-run..."
               echo ""
               exit 1
        fi
           
        # -- Define specific logs
        mapRawData_Runlog="${logdir}/runlogs/Log-mapRawData_${TimeStamp}.log"
        mapRawData_ComlogTmp="${logdir}/comlogs/tmp_mapRawData_${CASE}_${TimeStamp}.log"; touch ${mapRawData_ComlogTmp}; chmod 777 ${mapRawData_ComlogTmp}
        mapRawData_ComlogError="${logdir}/comlogs/error_mapRawData_${CASE}_${TimeStamp}.log"
        mapRawData_ComlogDone="${logdir}/comlogs/done_mapRawData_${CASE}_${TimeStamp}.log"
        
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
            echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${BATCH_PARAMETERS_FILENAME}""
            echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${SCAN_MAPPING_FILENAME}""
            echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc/files?format=zip" > ${processingdir}/scenes/QC/scene_qc_files.zip"
            echo ""
            echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${BATCH_PARAMETERS_FILENAME}"" >> ${mapRawData_ComlogTmp}
            echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${SCAN_MAPPING_FILENAME}"" >> ${mapRawData_ComlogTmp}
            echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc/files?format=zip" > ${processingdir}/scenes/QC/scene_qc_files.zip"  >> ${mapRawData_ComlogTmp}

            curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${BATCH_PARAMETERS_FILENAME}" > ${specsdir}/${BATCH_PARAMETERS_FILENAME}
            curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/MNAP_PROC/files/${SCAN_MAPPING_FILENAME}" > ${specsdir}/${SCAN_MAPPING_FILENAME}
            curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc/files?format=zip" > ${processingdir}/scenes/QC/scene_qc_files.zip
               
            # -- Verify and unzip custom QC scene files
            if [ -f ${processingdir}/scenes/QC/scene_qc_files.zip ]; then
                echo ""; geho " -- Custom scene files found ${processingdir}/scenes/QC/scene_qc_files.zip "
                echo ""; geho " -- Checking ZIP integrity for ${processingdir}/scenes/QC/scene_qc_files.zip "
                CheckCustomQCScene=`zip -T ${processingdir}/scenes/QC/scene_qc_files.zip | grep "error"`
                if [[ ! -z ${CheckCustomQCScene} ]]; then
                    echo "" >> ${mapRawData_ComlogTmp}
                    reho " -- Note: QC scene zip file not validated. Custom scene may be missing or is corrupted." >> ${mapRawData_ComlogTmp}
                    echo "" >> ${mapRawData_ComlogTmp}
                    echo ""; reho " -- Note: QC scene zip file not validated. Custom scene may be missing or is corrupted."; echo ""
                else
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
                fi
           else
                geho " No custom scene files found as an XNAT resources. If this is an error check your project resources in the XNAT web interface." >> ${mapRawData_ComlogTmp}
                echo "" >> ${mapRawData_ComlogTmp}
           fi
        fi
            
        if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
            geho " --> Running turnkey via local: `hostname`"; echo ""
            RawDataInputPath="${RawDataInputPath}"
        fi
        
        if [[ ${BIDSFormat} != "yes" ]]; then
            # -- Check if BIDS format NOT requested
            # -- Link to inbox
            echo ""
            geho " -- Linking DICOMs into ${rawdir}"; echo ""
            echo "  find ${RawDataInputPath} -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" -exec ln -s '{}' ${rawdir}/ ';'" >> ${mapRawData_ComlogTmp}
            find ${RawDataInputPath} -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" -exec ln -s '{}' ${rawdir}/ ';' &> /dev/null
            DicomInputCount=`find ${RawDataInputPath} -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" | wc | awk '{print $1}'`
            DicomMappedCount=`ls ${rawdir}/* | wc | awk '{print $1}'`
            if [[ ${DicomInputCount} == ${DicomMappedCount} ]]; then FILECHECK="pass"; else FILECHECK="fail"; fi
        fi
        
        # -- Check if BIDS format requested
        if [[ ${BIDSFormat} == "yes" ]]; then
            # -- NOTE: IF XNAT run is not requested then it assumed that zipped BIDS data is prepared in $mnap_subjectsfolder/inbox/BIDS/*zip
            if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
                # -- Set IF statement to check if /input mapped from XNAT for container run or curl call needed
                if [[ -d ${RawDataInputPath} ]]; then
                   if [[ `find ${RawDataInputPath} -type f -name "*.json" | wc -l` -gt 0 ]] && [[ `find ${RawDataInputPath} -type f -name "*.nii" | wc -l` -gt 0 ]]; then 
                       echo ""; echo " -- BIDS JSON and NII data found"; echo ""
                       mkdir ${mnap_subjectsfolder}/inbox/BIDS/${CASE} &> /dev/null
                       cp -r ${RawDataInputPath}/* ${mnap_subjectsfolder}/inbox/BIDS/${CASE}/
                       cd ${mnap_subjectsfolder}/inbox/BIDS
                       zip -r ${CASE} ${CASE} 2> /dev/null
                   else
                       echo ""
                       geho " -- Running:  "
                       geho "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${mnap_subjectsfolder}/inbox/BIDS/${CASE}.zip "; echo ""
                       curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${mnap_subjectsfolder}/inbox/BIDS/${CASE}.zip
                   fi
                else
                    # -- Get the BIDS data in ZIP format via curl
                    echo ""
                    geho " -- Running:  "
                    geho "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${mnap_subjectsfolder}/inbox/BIDS/${CASE}.zip "; echo ""
                    curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${mnap_subjectsfolder}/inbox/BIDS/${CASE}.zip
                fi
            fi
            # -- Perform mapping of BIDS file structure into MNAP
            echo ""
            geho " -- Running:  "
            geho "  ${MNAPCOMMAND} BIDSImport --subjectsfolder="${mnap_subjectsfolder}" --inbox="${mnap_subjectsfolder}/inbox/BIDS/${CASE}.zip" --action=copy --overwrite=yes --archive=delete "; echo ""
            ${MNAPCOMMAND} BIDSImport --subjectsfolder="${mnap_subjectsfolder}" --inbox="${mnap_subjectsfolder}/inbox/BIDS/${CASE}.zip" --action=copy --overwrite=yes --archive=delete >> ${mapRawData_ComlogTmp}
            popd 2> /dev/null
            rm -rf ${mnap_subjectsfolder}/inbox/BIDS/${CASE}* &> /dev/null
            
            # -- Run BIDS completion checks on mapped data
            if [ -f ${mnap_subjectsfolder}/${CASE}/bids/bids2nii.log ]; then
                 FILESEXPECTED=`more ${mnap_subjectsfolder}/${CASE}/bids/bids2nii.log | grep "=>" | wc -l 2> /dev/null`
            else
                 FILECHECK="fail"
            fi
            FILEFOUND=`ls ${mnap_subjectsfolder}/${CASE}/nii/* | wc -l 2> /dev/null`
            if [ -z ${FILEFOUND} ]; then
                FILECHECK="fail"
            fi
            if [[ ${FILESEXPECTED} == ${FILEFOUND} ]]; then
                echo ""
                geho " -- BIDSImport successful. Expected $FILESEXPECTED files and found $FILEFOUND files."
                echo ""
                FILECHECK="pass"
            else
                FILECHECK="fail"
            fi
        fi
        
        # -- Check if mapping and batch files exist
        if [[ -f ${specsdir}/${BATCH_PARAMETERS_FILENAME} ]]; then BATCHFILECHECK="pass"; else BATCHFILECHECK="fail"; fi
        if [[ -f ${specsdir}/${SCAN_MAPPING_FILENAME} ]]; then MAPPINGFILECHECK="pass"; else MAPPINGFILECHECK="fail"; fi
        # -- Check if content of files OK
        if [[ -z `more ${specsdir}/${SCAN_MAPPING_FILENAME} | grep '=>'` ]]; then MAPPINGFILECHECK="fail"; fi
        if [[ -z `more ${specsdir}/${BATCH_PARAMETERS_FILENAME} | grep '_hcp_Pipeline'` ]]; then MAPPINGFILECHECK="fail"; fi
      
        # -- Declare checks
        echo "" >> ${mapRawData_ComlogTmp}
        echo "----------------------------------------------------------------------------" >> ${mapRawData_ComlogTmp}
        echo "  --> Batch file transfer check: ${BATCHFILECHECK}" >> ${mapRawData_ComlogTmp}
        echo "  --> Mapping file transfer check: ${MAPPINGFILECHECK}" >> ${mapRawData_ComlogTmp}
        if [[ ${BIDSFormat} == "yes" ]]; then
            echo "  --> BIDS mapping check: ${FILECHECK}" >> ${mapRawData_ComlogTmp}
        else
            echo "  --> DICOM file count in input folder /input/SCANS: ${DicomInputCount}" >> ${mapRawData_ComlogTmp}
            echo "  --> DICOM file count in output folder ${rawdir}: ${DicomMappedCount}" >> ${mapRawData_ComlogTmp}
            echo "  --> DICOM mapping check: ${FILECHECK}" >> ${mapRawData_ComlogTmp}
        fi
        echo "  --> DICOM file count in input folder /input/SCANS: ${DicomInputCount}" >> ${mapRawData_ComlogTmp}

        # -- Report and log final checks
        if [[ ${FILECHECK} == "pass" ]] && [[ ${BATCHFILECHECK} == "pass" ]] && [[ ${MAPPINGFILECHECK} == "pass" ]]; then
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
    
    # -- Organize DICOMs
    turnkey_organizeDicom() {
        if [[ ${BIDSFormat} != "yes" ]]; then 
            echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: organizeDicom ..."; echo ""
            ${MNAPCOMMAND} organizeDicom --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}"
            cd ${mnap_subjectsfolder}/${CASE}/nii; NIILeadZeros=`ls ./0*.nii.gz 2>/dev/null`; for NIIwithZero in ${NIILeadZeros}; do NIIwithoutZero=`echo ${NIIwithZero} | sed 's/0//g'`; mv ${NIIwithZero} ${NIIwithoutZero}; done
            if [ ${TURNKEY_TYPE} == "xnat" ]; then
                reho "---> Cleaning up: removing inbox folder"
                rm -rf ${mnap_workdir}/inbox &> /dev/null
            fi
        else
            echo ""; cyaneho " ===> RunTurnkey ~~~ SKIPPING: organizeDicom because data is in BIDS format ... "; echo ""
        fi
    }
    # -- Map processing folder structure
    turnkey_getHCPReady() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: getHCPReady ..."; echo ""
        TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        getHCPReady_Runlog="${logdir}/runlogs/Log-getHCPReady${TimeStamp}.log"
        getHCPReady_ComlogTmp="${logdir}/comlogs/tmp_getHCPReady_${CASE}_${TimeStamp}.log"; touch ${getHCPReady_ComlogTmp}; chmod 777 ${getHCPReady_ComlogTmp}
        getHCPReady_ComlogError="${logdir}/comlogs/error_getHCPReady_${CASE}_${TimeStamp}.log"
        getHCPReady_ComlogDone="${logdir}/comlogs/done_getHCPReady_${CASE}_${TimeStamp}.log"
        if [[ "${OVERWRITE_STEP}" == "yes" ]]; then
            rm -rf ${mnap_subjectsfolder}/${CASE}/subject_hcp.txt &> /dev/null
        fi
        if [ -f ${mnap_subjectsfolder}/subject_hcp.txt ]; then
            echo ""; geho " ===> ${mnap_subjectsfolder}/subject_hcp.txt exists. Set --overwrite='yes' to re-run."; echo ""; return 0
        fi
        Command="${MNAPCOMMAND} getHCPReady --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --mapping="${specsdir}/${SCAN_MAPPING_FILENAME}""
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
           HLinks=`ls ${mnap_subjectsfolder}/${CASE}/hcp/${CASE}/*/*nii* 2>/dev/null`; for HLink in ${HLinks}; do unlink ${HLink}; done
        fi
        Command="${MNAPCOMMAND} mapHCPFiles --subjectsfolder='${mnap_subjectsfolder}' --subjects='${CASE}' --overwrite='${OVERWRITE_STEP}'"
        echo ""; echo " -- Executed command:"; echo "   $Command"; echo ""
        eval ${Command}
        geho " -- Generating ${project_batch_file}"; echo ""
        cp ${specsdir}/${BATCH_PARAMETERS_FILENAME} ${project_batch_file}; cat ${mnap_workdir}/subject_hcp.txt >> ${project_batch_file}
    }
    #
    # --------------- Intial study and file organization end -------------------
    
    QCPreproc_Finalize() {
        QCPreprocComLog=`ls -t1 ${logdir}/comlogs/*_QCPreproc_${CASE}_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
        QCPreprocRunLog=`ls -t1 ${logdir}/runlogs/Log-QCPreproc_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
        rename QCPreproc QCPreproc${QCLogName} ${logdir}/comlogs/${QCPreprocComLog} 2> /dev/null
        rename QCPreproc QCPreproc${QCLogName} ${logdir}/runlogs/${QCPreprocRunLog} 2> /dev/null
        mkdir -p ${mnap_subjectsfolder}/${CASE}/logs/comlog 2> /dev/null
        mkdir -p ${mnap_subjectsfolder}/${CASE}/logs/runlog 2> /dev/null
        mkdir -p ${mnap_subjectsfolder}/${CASE}/QC/${Modality} 2> /dev/null
        cp ${logdir}/comlogs/${QCPreprocComLog} ${mnap_subjectsfolder}/${CASE}/logs/comlog/ 2> /dev/null
        cp ${logdir}/comlogs/${QCPreprocRunLog} ${mnap_subjectsfolder}/${CASE}/logs/comlog/ 2> /dev/null
        cp ${mnap_subjectsfolder}/subjects/QC/${Modality}/*${CASE}*scene ${mnap_subjectsfolder}/${CASE}/QC/${Modality}/ 2> /dev/null
        cp ${mnap_subjectsfolder}/subjects/QC/${Modality}/*${CASE}*zip ${mnap_subjectsfolder}/${CASE}/QC/${Modality}/ 2> /dev/null
    }

    # --------------- HCP Processing and relevant QC start ---------------------
    #
    # -- PreFreeSurfer
    turnkey_hcp1() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp1 (hcp_PreFS) ... "; echo ""
        ${MNAPCOMMAND} hcp1 --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --subjid="${SUBJID}"
    }
    # -- FreeSurfer
    turnkey_hcp2() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp2 (hcp_FS) ... "; echo ""
        ${MNAPCOMMAND} hcp2 --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --subjid="${SUBJID}"
        CleanupFiles=" talairach_with_skull.log lh.white.deformed.out lh.pial.deformed.out rh.white.deformed.out rh.pial.deformed.out"
        for CleanupFile in ${CleanupFiles}; do 
            cp ${logdir}/${CleanupFile} ${mnap_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/${CASE}/scripts/ 2>/dev/null
            rm -rf ${logdir}/${CleanupFile}
        done
        rm -rf ${mnap_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/fsaverage 2>/dev/null
        rm -rf ${mnap_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/rh.EC_average 2>/dev/null
        rm -rf ${mnap_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/lh.EC_average 2>/dev/null
        cp -r $FREESURFER_HOME/subjects/lh.EC_average ${mnap_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/ 2>/dev/null
        cp -r $FREESURFER_HOME/subjects/fsaverage ${mnap_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/ 2>/dev/null
        cp -r $FREESURFER_HOME/subjects/rh.EC_average ${mnap_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/ 2>/dev/null
    }
    # -- PostFreeSurfer
    turnkey_hcp3() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp3 (hcp_PostFS) ... "; echo ""
        ${MNAPCOMMAND} hcp3 --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --subjid="${SUBJID}"
    }
    # -- QCPreprocT1W (after hcp3)
    turnkey_QCPreprocT1w() {
        Modality="T1w"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc step for ${Modality} data ... "; echo ""
        ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --hcp_suffix="${HCPSuffix}"
        QCLogName="T1w"
        QCPreproc_Finalize
    }
    # -- QCPreprocT2W (after hcp3)
    turnkey_QCPreprocT2w() {
        Modality="T2w"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc step for ${Modality} data ... "; echo ""
        ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --hcp_suffix="${HCPSuffix}"
        QCLogName="T2w"
        QCPreproc_Finalize
    }
    # -- QCPreprocMyelin (after hcp3)
    turnkey_QCPreprocMyelin() {
        Modality="myelin"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc step for ${Modality} data ... "; echo ""
        ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --hcp_suffix="${HCPSuffix}"
        QCLogName="Myelin"
        QCPreproc_Finalize
    }
    # -- fMRIVolume
    turnkey_hcp4() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp4 (hcp_fMRIVolume) ... "; echo ""
        HCPLogName="hcpfMRIVolume"
        ${MNAPCOMMAND} hcp4 --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --subjid="${SUBJID}"
    }
    # -- fMRISurface
    turnkey_hcp5() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp5 (hcp_fMRISurface) ... "; echo ""
        HCPLogName="hcpfMRISurface"
        ${MNAPCOMMAND} hcp5 --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --subjid="${SUBJID}"
    }
    # -- QCPreprocBOLD (after hcp5)
    turnkey_QCPreprocBOLD() {
        Modality="BOLD"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc step for ${Modality} data ... "; echo ""
        if [ -z "${BOLDfc}" ]; then
            # if [ -z "${BOLDPrefix}" ]; then BOLDPrefix="bold"; fi   --- default for bold prefix is now ""
            if [ -z "${BOLDSuffix}" ]; then BOLDSuffix="Atlas"; fi
        fi
        if [ -z "${BOLDRUNS}" ]; then
             BOLDRUNS=`ls ${mnap_subjectsfolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/ | awk {'print $1'} 2> /dev/null`
        fi
        for BOLDRUN in ${BOLDRUNS}; do
            ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --boldprefix="${BOLDPrefix}" --boldsuffix="${BOLDSuffix}" --bolds="${BOLDRUN}" --hcp_suffix="${HCPSuffix}"
            QCPreprocComLog=`ls -t1 ${logdir}/comlogs/*_QCPreproc_${CASE}_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
            QCPreprocRunLog=`ls -t1 ${logdir}/runlogs/Log-QCPreproc_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
            rename QCPreproc QCPreprocBOLD${BOLD} ${logdir}/comlogs/${QCPreprocComLog}
            rename QCPreproc QCPreprocBOLD${BOLD} ${logdir}/runlogs/${QCPreprocRunLog} 2> /dev/null
        done
    }
    # -- Diffusion HCP (after hcp1)
    turnkey_hcpd() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcpd (hcp_Diffusion) ..."; echo ""
        ${MNAPCOMMAND} hcpd --subjectsfolder="${mnap_subjectsfolder}" --subjects="${project_batch_file}" --overwrite="${OVERWRITE_STEP}" --subjid="${SUBJID}"
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
        ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --dwidata="data" --dwipath="Diffusion" --dwilegacy="${DWILegacy}" --hcp_suffix="${HCPSuffix}"
        QCLogName="DWILegacy"
        QCPreproc_Finalize
    }
    # -- QCPreprocDWI (after hcpd)
    turnkey_QCPreprocDWI() {
        Modality="DWI"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc steps for ${Modality} HCP processing ... "; echo ""
        ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --outpath="${mnap_subjectsfolder}/QC/DWI" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --dwidata="data" --dwipath="Diffusion" --logfolder="${logdir}" --hcp_suffix="${HCPSuffix}"
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
        ${MNAPCOMMAND} eddyQC --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --eddybase="${EddyBase}" --eddypath="${EddyPath}" --report="${Report}" --bvalsfile="${BvalsFile}" --mask="${Mask}" --eddyidx="${EddyIdx}" --eddyparams="${EddyParams}" --bvecsfile="${BvecsFile}" --overwrite="${OVERWRITE_STEP}"
    }
    # -- QCPreprocDWIeddyQC (after eddyQC)
    turnkey_QCPreprocDWIeddyQC() {
        Modality="DWI"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc steps for ${Modality} eddyQC ... "; echo ""
        ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --outpath="${mnap_subjectsfolder}/QC/DWI" -modality="${Modality}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --eddyqcstats="yes" --hcp_suffix="${HCPSuffix}"
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
        ${MNAPCOMMAND} FSLDtifit --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}"
    }
    # -- FSLBedpostxGPU (after FSLDtifit)
    turnkey_FSLBedpostxGPU() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: FSLBedpostxGPU for DWI ... "
        if [ -z "$Fibers" ]; then Fibers="3"; fi
        if [ -z "$Model" ]; then Model="3"; fi
        if [ -z "$Burnin" ]; then Burnin="3000"; fi
        if [ -z "$Rician" ]; then Rician="yes"; fi
        ${MNAPCOMMAND} FSLBedpostxGPU --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --fibers="${Fibers}" --burnin="${Burnin}" --model="${Model}" --rician="${Rician}"
    }
    # -- QCPreprocDWIDTIFIT (after FSLDtifit)
    turnkey_QCPreprocDWIDTIFIT() {
        Modality="DWI"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc steps for ${Modality} FSL's dtifit analyses ... "; echo ""
        ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --outpath="${mnap_subjectsfolder}/QC/DWI" --modality="${Modality}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --dtifitqc="yes" --hcp_suffix="${HCPSuffix}"
        QCLogName="DWIDTIFIT" 
        QCPreproc_Finalize
    }
    # -- QCPreprocDWIBedpostX (after FSLBedpostxGPU)
    turnkey_QCPreprocDWIBedpostX() {
        Modality="DWI"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc steps for ${Modality} FSL's BedpostX analyses ... "; echo ""
        ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --outpath="${mnap_subjectsfolder}/QC/DWI" --modality="${Modality}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --bedpostxqc="yes" --hcp_suffix="${HCPSuffix}"
        QCLogName="DWIBedpostX" 
        QCPreproc_Finalize
    }
    # -- probtrackxGPUDense for DWI data (after FSLBedpostxGPU)
    turnkey_probtrackxGPUDense() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: probtrackxGPUDense ... "; echo ""
        ${MNAPCOMMAND} probtrackxGPUDense --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --omatrix1="yes" --omatrix3="yes"
    }
    # -- pretractographyDense for DWI data (after FSLBedpostxGPU)
    turnkey_pretractographyDense() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: pretractographyDense ... "; echo ""
        ${MNAPCOMMAND} pretractographyDense --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --omatrix1="yes" --omatrix3="yes"
    }
    # -- DWIDenseParcellationfor DWI data (after pretractographyDense)
    turnkey_DWIDenseParcellation() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: DWIDenseParcellation ... "; echo ""
        # Defaults if not specified:
        if [ -z "$WayTotal" ]; then WayTotal="standard"; fi
        if [ -z "$MatrixVersion" ]; then MatrixVersions="1"; fi
        # Cole-Anticevic Brain-wide Network Partition version 1.0 (CAB-NP v1.0)
        if [ -z "$ParcellationFile" ]; then ParcellationFile="${TOOLS}/${MNAPREPO}/library/data/parcellations/ColeAnticevicNetPartition/CortexSubcortex_ColeAnticevic_NetPartition_wSubcorGSR_parcels_LR.dlabel.nii"; fi
        if [ -z "$DWIOutName" ]; then DWIOutName="DWI-CAB-NP-v1.0"; fi
        for MatrixVersion in $MatrixVersions; do
            ${MNAPCOMMAND} DWIDenseParcellation --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --waytotal="${WayTotal}" --matrixversion="${MatrixVersion}" --parcellationfile="${ParcellationFile}" --outname="${DWIOutName}"
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
            ${MNAPCOMMAND} DWISeedTractography --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --matrixversion="${MatrixVersion}" --waytotal="${WayTotal}" --outname="${OutName}" --seedfile="${SeedFile}"
            # Thalamus Prefrontal
            SeedFile="${TOOLS}/${MNAPREPO}/library/data/atlases/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Prefrontal.symmetrical.intersectionLR.nii" 
            OutName="DWI_THALAMUS_FSL_LR_Prefrontal"
            ${MNAPCOMMAND} DWISeedTractography --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --matrixversion="${MatrixVersion}" --waytotal="${WayTotal}" --outname="${OutName}" --seedfile="${SeedFile}"
        fi
        OutNameGBC="DWI_GBC"
        ${MNAPCOMMAND} DWISeedTractography --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --matrixversion="${MatrixVersion}" --waytotal="${WayTotal}" --outname="${OutNameGBC}" --seedfile="gbc"
    }
    #
    # --------------- DWI Processing and analyses end --------------------------


    # --------------- Custom QC start ------------------------------------------
    # 
    # -- Check if Custom QC was requested
    turnkey_QCPreprocCustom() {
        unset RunCommand
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreprocCustom ... "; echo ""
        
        if [ -z "${Modality}" ]; then
            Modalities="T1w T2w myelin BOLD DWI"
            reho " --> Note: No modality specified. Trying all modalities: ${Modalities} "
        else
            Modalities="${Modality}"
            geho " --> User requested modalities: ${Modalities} "
        fi
        for Modality in ${Modalities}; do
            geho " --> Running modality: ${Modality} "; echo ""
            if [[ ${Modality} == "BOLD" ]]; then
                # if [ -z "${BOLDPrefix}" ]; then BOLDPrefix="bold"; fi    --- default for bold prefix is now ""
                if [ -z "${BOLDSuffix}" ]; then BOLDSuffix="Atlas"; fi
                if [ -z "${BOLDRUNS}" ]; then
                     BOLDRUNS=`ls ${mnap_subjectsfolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/ | awk {'print $1'} 2> /dev/null`
                     geho " --> BOLDs not explicitly requested. Will run all available data: ${BOLDRUNS} "
                fi
                echo "====> Looping through these BOLDRUNS: ${BOLDRUNS}"
                for BOLDRUN in ${BOLDRUNS}; do
                    echo "----> Now working on BOLDRUN: ${BOLDRUN}"
                    ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --boldprefix="${BOLDPrefix}" --boldsuffix="${BOLDSuffix}" --bolddata="${BOLDRUN}" --customqc='yes' --omitdefaults='yes' --hcp_suffix="${HCPSuffix}"
                    QCPreprocComLog=`ls -t1 ${logdir}/comlogs/*_QCPreproc_${CASE}_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
                    QCPreprocRunLog=`ls -t1 ${logdir}/runlogs/Log-QCPreproc_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
                    rename QCPreproc QCPreprocCustomBOLD${BOLD} ${logdir}/comlogs/${QCPreprocComLog}
                    rename QCPreproc QCPreprocCustomBOLD${BOLD} ${logdir}/runlogs/${QCPreprocRunLog} 2> /dev/null
                done
            elif [[ ${Modality} == "DWI" ]]; then
                ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --customqc="yes" --omitdefaults="yes" --hcp_suffix="${HCPSuffix}"
                QCLogName="Custom${Modality}"
                QCPreproc_Finalize
            else
                ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --customqc="yes" --omitdefaults="yes" --hcp_suffix="${HCPSuffix}"
                QCLogName="Custom${Modality}"
                if [[ ${Modality} == "myelin" ]]; then QCLogName="CustomMyelin"; fi
                QCPreproc_Finalize
            fi
        done
    }
    #
    # --------------- Custom QC end --------------------------------------------


    # --------------- BOLD FC Processing and analyses start --------------------
    #
    # -- Specific checks for BOLD Fc functions
    BOLDfcLogCheck() {
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
        mkdir -p ${mnap_subjectsfolder}/${CASE}/logs/comlog 2> /dev/null
        mkdir -p ${mnap_subjectsfolder}/${CASE}/logs/runlog 2> /dev/null
        cp ${CheckComLog} ${mnap_subjectsfolder}/${CASE}/logs/comlog 2> /dev/null
        cp ${CheckRunLog} ${mnap_subjectsfolder}/${CASE}/logs/runlog 2> /dev/null
           
        if [ -z "${CheckComLog}" ]; then
           TURNKEY_STEP_ERRORS="yes"
           reho " ===> ERROR: Completed ComLog file not found!"
        fi
        if [ ! -z "${CheckComLog}" ]; then
           geho " ===> Comlog file: ${CheckComLog}"
           chmod 777 ${CheckComLog} 2>/dev/null
        fi
        if [ -z `echo "${CheckComLog}" | grep 'done'` ]; then
            echo ""; reho " ===> ERROR: ${TURNKEY_STEP} step failed."
            TURNKEY_STEP_ERRORS="yes"
        else
            echo ""; cyaneho " ===> RunTurnkey ~~~ SUCCESS: ${TURNKEY_STEP} step passed!"; echo ""
            TURNKEY_STEP_ERRORS="no"
        fi
    }

    # -- Map HCP processed outputs for further FC BOLD analyses
    turnkey_mapHCPData() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: mapHCPData ... "; echo ""
        ${MNAPCOMMAND} mapHCPData \
        --subjects="${project_batch_file}" \
        --subjectsfolder="${mnap_subjectsfolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${logdir}" \
        --subjid="${SUBJID}"
    }
    # -- Generate brain masks for de-noising
    turnkey_createBOLDBrainMasks() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: createBOLDBrainMasks ... "; echo ""
        ${MNAPCOMMAND} createBOLDBrainMasks \
        --subjects="${project_batch_file}" \
        --subjectsfolder="${mnap_subjectsfolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${logdir}" \
        --subjid="${SUBJID}"
    }
    # -- Compute BOLD statistics
    turnkey_computeBOLDStats() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: computeBOLDStats ... "; echo ""
        ${MNAPCOMMAND} computeBOLDStats \
        --subjects="${project_batch_file}" \
        --subjectsfolder="${mnap_subjectsfolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${logdir}" \
        --subjid="${SUBJID}"
    }
    # -- Create final BOLD statistics report
    turnkey_createStatsReport() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: createStatsReport ... "; echo ""
        ${MNAPCOMMAND} createStatsReport \
        --subjects="${project_batch_file}" \
        --subjectsfolder="${mnap_subjectsfolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${logdir}" \
        --subjid="${SUBJID}"
    }
    # -- Extract nuisance signal for further de-noising
    turnkey_extractNuisanceSignal() {
        cyaneho " ===> RunTurnkey ~~~ RUNNING: extractNuisanceSignal ... "; echo ""
        ${MNAPCOMMAND} extractNuisanceSignal \
        --subjects="${project_batch_file}" \
        --subjectsfolder="${mnap_subjectsfolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${logdir}" \
        --subjid="${SUBJID}"
    }
    # -- Process BOLDs
    turnkey_preprocessBold() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: preprocessBold ... "; echo ""
        ${MNAPCOMMAND} preprocessBold \
        --subjects="${project_batch_file}" \
        --subjectsfolder="${mnap_subjectsfolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${logdir}" \
        --subjid="${SUBJID}"
    }
    # -- Process via CONC file
    turnkey_preprocessConc() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: preprocessConc ... "; echo ""
        ${MNAPCOMMAND} preprocessConc \
        --subjects="${project_batch_file}" \
        --subjectsfolder="${mnap_subjectsfolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${logdir}" \
        --subjid="${SUBJID}"
    }
    # -- Compute g_PlotBoldTS ==> (08/14/17 - 6:50PM): Coded but not final yet due to Octave/Matlab problems
    turnkey_g_PlotBoldTS() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: g_PlotBoldTS QC plotting ... "; echo ""
        TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        g_PlotBoldTS_Runlog="${logdir}/runlogs/Log-g_PlotBoldTS_${TimeStamp}.log"
        g_PlotBoldTS_ComlogTmp="${logdir}/comlogs/tmp_g_PlotBoldTS_${CASE}_${TimeStamp}.log"; touch ${g_PlotBoldTS_ComlogTmp}; chmod 777 ${g_PlotBoldTS_ComlogTmp}
        g_PlotBoldTS_ComlogError="${logdir}/comlogs/error_g_PlotBoldTS_${CASE}_${TimeStamp}.log"
        g_PlotBoldTS_ComlogDone="${logdir}/comlogs/done_g_PlotBoldTS_${CASE}_${TimeStamp}.log"
        
        if [ -z ${QCPlotElements} ]; then
              QCPlotElements="type=stats|stats>plotdata=fd,imageindex=1>plotdata=dvarsme,imageindex=1;type=signal|name=V|imageindex=1|maskindex=1|colormap=hsv;type=signal|name=WM|imageindex=1|maskindex=1|colormap=jet;type=signal|name=GM|imageindex=1|maskindex=1;type=signal|name=GM|imageindex=2|use=1|scale=3"
        fi
        if [ -z ${QCPlotMasks} ]; then
              QCPlotMasks="${mnap_subjectsfolder}/${CASE}/images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz"
        fi
        if [ -z ${images_folder} ]; then
            images_folder="${mnap_subjectsfolder}/$CASE/images/functional"
        fi
        if [ -z ${output_folder} ]; then
            output_folder="${mnap_subjectsfolder}/$CASE/images/functional/movement"
        fi
        if [ -z ${output_name} ]; then
            output_name="${CASE}_BOLD_GreyPlot_CIFTI.pdf"
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
           echo "${MNAPCOMMAND} g_PlotBoldTS --images="${QCPlotImages}" --elements="${QCPlotElements}" --masks="${QCPlotMasks}" --filename="${output_folder}/${output_name}" --skip="0" --subjid="${CASE}" --verbose="true"" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
           echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
           
           ${MNAPCOMMAND} g_PlotBoldTS --images="${QCPlotImages}" --elements="${QCPlotElements}" --masks="${QCPlotMasks}" --filename="${output_folder}/${output_name}" --skip="0" --subjid="${CASE}" --verbose="true"
           echo " -- Copying ${output_folder}/${output_name} to ${mnap_subjectsfolder}/QC/BOLD/" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
           echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
           cp ${output_folder}/${output_name} ${mnap_subjectsfolder}/QC/BOLD/
           if [[ -f ${mnap_subjectsfolder}/QC/BOLD/${output_name} ]]; then
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
    # -- BOLD Parcellation 
    turnkey_BOLDParcellation() {
        FunctionName="BOLDParcellation"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: BOLDParcellation ... "; echo ""
        # -- Defaults if not specified:
        # unset BOLDRUNS
        if [ -z ${BOLDRUNS} ]; then
            BOLDRUNS="1"
        fi
        # unset BOLDRUN
        for BOLDRUN in ${BOLDRUNS}; do
           if [ -z "$InputFile" ]; then InputFileParcellation="bold${BOLDRUN}_Atlas_g7_hpss_res-mVWMWB_lpss.dtseries.nii "; else InputFileParcellation="${InputFile}"; fi
           if [ -z "$UseWeights" ]; then UseWeights="yes"; fi
           if [ -z "$WeightsFile" ]; then UseWeights="images/functional/movement/bold${BOLDRUN}.use"; fi
           # -- Cole-Anticevic Brain-wide Network Partition version 1.0 (CAB-NP v1.0)
           if [ -z "$ParcellationFile" ]; then ParcellationFile="${TOOLS}/${MNAPREPO}/library/data/parcellations/ColeAnticevicNetPartition/CortexSubcortex_ColeAnticevic_NetPartition_wSubcorGSR_parcels_LR.dlabel.nii"; fi
           if [ -z "$OutName" ]; then OutNameParcelation="BOLD-CAB-NP-v1.0"; else OutNameParcelation="${OutName}"; fi
           if [ -z "$InputDataType" ]; then InputDataType="dtseries"; fi
           if [ -z "$InputPath" ]; then InputPath="/images/functional/"; fi
           if [ -z "$OutPath" ]; then OutPath="/images/functional/"; fi
           if [ -z "$ComputePConn" ]; then ComputePConn="yes"; fi
           if [ -z "$ExtractData" ]; then ExtractData="yes"; fi
           # -- Command
           RunCommand="${MNAPCOMMAND} BOLDParcellation --subjects='${CASE}' \
           --subjectsfolder='${mnap_subjectsfolder}' \
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
              # unset BOLDRUNS
              if [ -z ${BOLDRUNS} ]; then
                  BOLDRUNS="1"
              fi
              # unset BOLDRUN
              for BOLDRUN in ${BOLDRUNS}; do
                if [ -z "$InputFile" ]; then InputFileSeed="bold${BOLDRUN}_Atlas_g7_hpss_res-mVWMWB_lpss.dtseries.nii"; else InputFileSeed="${InputFile}"; fi
                if [ -z "$InputPath" ]; then InputPath="/images/functional"; fi
                if [ -z "$ExtractData" ]; then ExtractData=""; fi
                if [ -z "$OutName" ]; then OutNameSeed="seed_bold${BOLDRUN}_Atlas_g7_hpss_res-VWMWB_lpss"; else OutNameSeed="${OutName}"; fi
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
                --subjects='${CASE}' \
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
   turnkey_computeBOLDfcGBC() {
   FunctionName="computeBOLDfc"
       echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: computeBOLDfc processing steps for GBC ... "; echo ""
       # unset BOLDRUNS
       if [ -z ${BOLDRUNS} ]; then
           BOLDRUNS="1"
       fi
       #unset BOLDRUN
       for BOLDRUN in ${BOLDRUNS}; do
            if [ -z "$InputFile" ]; then InputFileGBC="bold${BOLDRUN}_Atlas_g7_hpss_res-mVWMWB_lpss.dtseries.nii"; else InputFileGBC="${InputFile}"; fi
            if [ -z "$InputPath" ]; then InputPath="/images/functional"; fi
            if [ -z "$ExtractData" ]; then ExtractData=""; fi
            if [ -z "$OutName" ]; then OutNameGBC="GBC_bold${BOLDRUN}_Atlas_g7_hpss_res-VWMWB_lpss"; else OutNameGBC="${OutName}"; fi
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
            --subjects='${CASE}' \
            --inputfiles='${InputFileGBC}' \
            --inputpath='${InputPath}' \
            --extractdata='${ExtractData}' \
            --outname='${OutNameGBC}' \
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
   # -- QCPreprocBOLD FC (after GBC/FC/PCONN)
   turnkey_QCPreprocBOLDfc() {
        Modality="BOLD"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QCPreproc step for ${Modality} FC ... "; echo ""
        if [ -z "${BOLDRUNS}" ]; then
             BOLDRUNS=`ls ${mnap_subjectsfolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/ | awk {'print $1'} 2> /dev/null`
        fi
        for BOLDRUN in ${BOLDRUNS}; do
            ${MNAPCOMMAND} QCPreproc --subjectsfolder="${mnap_subjectsfolder}" --subjects="${CASE}" --outpath="${mnap_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --boldprefix="${BOLDPrefix}" --boldsuffix="${BOLDSuffix}" --bolds="${BOLDRUN}" --boldfc="${BOLDfc}" --boldfcinput="${BOLDfcInput}" --boldfcpath="${BOLDfcPath}" --hcp_suffix="${HCPSuffix}"
            QCPreprocComLog=`ls -t1 ${logdir}/comlogs/*_QCPreproc_${CASE}_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
            QCPreprocRunLog=`ls -t1 ${logdir}/runlogs/Log-QCPreproc_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
            rename QCPreproc QCPreprocBOLDfc${BOLD} ${logdir}/comlogs/${QCPreprocComLog}
            rename QCPreproc QCPreprocBOLDfc${BOLD} ${logdir}/runlogs/${QCPreprocRunLog} 2> /dev/null
        done
    }
    
    #
    # --------------- BOLD FC Processing and analyses end ----------------------


    # --------------- RunAcceptanceTest start ---------------------------
    #
    # -- RunAcceptanceTest for a given step in XNAT
    #
    RunAcceptanceTestFunction() {
    
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: Acceptance Test Function ... "; echo ""
        
        if [[ -z "$TURNKEY_STEPS" ]] && [[ ! -z "$AcceptanceTest" ]] && [[ "$AcceptanceTest" != "yes" ]] && [[ ${TURNKEY_TYPE} == "xnat" ]]; then 
            for UnitTest in ${AcceptanceTest}; do
                RunCommand="MNAPAcceptanceTest.sh \
                --studyfolder='${mnap_studyfolder}' \
                --subjectsfolder='${mnap_subjectsfolder}' \
                --subjects='${CASE}' \
                --runtype='local' \
                --acceptancetest='${UnitTest}'"
                echo " -- Command: ${RunCommand}"
                eval ${RunCommand}
            done
        else
            RunCommand="MNAPAcceptanceTest.sh \
            --studyfolder='${mnap_studyfolder}' \
            --subjectsfolder='${mnap_subjectsfolder}' \
            --subjects='${CASE}' \
            --runtype='local' \
            --acceptancetest='${UnitTest}'"
           echo " -- Command: ${RunCommand}"
           eval ${RunCommand}
        fi
        
       # -- XNAT Call -- not supported currently. 
       #
       #    RunCommand="MNAPAcceptanceTest.sh \
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

    # --------------- MNAPTurnkeyCleanFunction start -------------
    #
    MNAPTurnkeyCleanFunction() {
        # -- Currently supporting hcp4 but this can be exanded
        if [[ "$TURNKEY_STEP" == "hcp4" ]]; then
            echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: MNAPClean Function for $TURNKEY_STEP ... "; echo ""
            rm -rf ${mnap_subjectsfolder}/${CASE}/hcp/${CASE}/[0-9]* &> /dev/null
        fi
    }
    #
    # --------------- MNAPTurnkeyCleanFunction end ----------------

#
# =-=-=-=-=-=-= TURNKEY COMMANDS END =-=-=-=-=-=-=


# =-=-=-=-=-=-= RUN SPECIFIC COMMANDS START =-=-=-=-=-=-=

if [ -z "$TURNKEY_STEPS" ] && [ ! -z "$AcceptanceTest" ] && [ "$AcceptanceTest" != "yes" ]; then
    echo ""; 
    geho "  ---------------------------------------------------------------------"
    echo ""
    geho "   ===> Performing completion check on specific MNAP turnkey units: ${AcceptanceTest}"
    echo ""
    geho "  ---------------------------------------------------------------------"
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
        geho "  ---------------------------------------------------------------------"
        echo ""
        geho "   ===> Executing all MNAP turkey workflow steps: ${MNAPTurnkeyWorkflow}"
        echo ""
        geho "  ---------------------------------------------------------------------"
        echo ""
        TURNKEY_STEPS=${MNAPTurnkeyWorkflow}
    fi
    if [ "$TURNKEY_STEPS" != "all" ]; then
        echo ""; 
        geho "  ---------------------------------------------------------------------"
        echo ""
        geho "   ===> Executing specific MNAP turkey workflow steps: ${TURNKEY_STEPS}"
        echo ""
        geho "  ---------------------------------------------------------------------"
        echo ""
    fi

    # -- Loop through specified Turnkey steps if requested
    unset TURNKEY_STEP_ERRORS
    for TURNKEY_STEP in ${TURNKEY_STEPS}; do
        
        # -- Execute turnkey
        turnkey_${TURNKEY_STEP}
        
        # -- Generate single subject log folders
        CheckComLog=`ls -t1 ${logdir}/comlogs/*${TURNKEY_STEP}*log 2> /dev/null | head -n 1`
        CheckRunLog=`ls -t1 ${logdir}/runlogs/Log-${TURNKEY_STEP}*log 2> /dev/null | head -n 1`
        mkdir -p ${mnap_subjectsfolder}/${CASE}/logs/comlog 2> /dev/null
        mkdir -p ${mnap_subjectsfolder}/${CASE}/logs/runlog 2> /dev/null
        cp ${CheckComLog} ${mnap_subjectsfolder}/${CASE}/logs/comlog 2> /dev/null
        cp ${CheckRunLog} ${mnap_subjectsfolder}/${CASE}/logs/runlog 2> /dev/null
        
        Modalities="T1w T2w myelin BOLD DWI"
        for Modality in ${Modalities}; do
            mkdir -p ${mnap_subjectsfolder}/${CASE}/QC/${Modality} 2> /dev/null
        done
    
        # -- Specific sets of functions for logging
        ConnectorBOLDFunctions="BOLDParcellation computeBOLDfcGBC computeBOLDfcSeed"
        NiUtilsFunctons="hcp1 hcp2 hcp3 hcp4 hcp5 hcpd mapHCPData createBOLDBrainMasks computeBOLDStats createStatsReport extractNuisanceSignal preprocessBold preprocessConc"
    
        # -- Check for completion of turnkey function for NIUtilities
        if [ -z "${NiUtilsFunctons##*${TURNKEY_STEP}*}" ] && [ ! -z "${ConnectorBOLDFunctions##*${TURNKEY_STEP}*}" ]; then
        geho " -- Looking for incomplete/failed process ..."; echo ""
            if [ -z "${CheckRunLog}" ]; then
               TURNKEY_STEP_ERRORS="yes"
               reho " ===> ERROR: Runlog file not found!"; echo ""
            fi
            if [ ! -z "${CheckRunLog}" ]; then
               geho " ===> Runlog file: ${CheckRunLog} "; echo ""
               CheckRunLogOut=`cat ${CheckRunLog} | grep '===> Successful completion'`
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
            if [ -z "${CheckComLog}" ]; then
               TURNKEY_STEP_ERRORS="yes"
               reho " ===> ERROR: Completed ComLog file not found!"
            fi
            if [ ! -z "${CheckComLog}" ]; then
               geho " ===> Comlog file: ${CheckComLog}"
               chmod 777 ${CheckComLog} 2>/dev/null
            fi
            if [ -z `echo "${CheckComLog}" | grep 'done'` ]; then
                echo ""; reho " ===> ERROR: ${TURNKEY_STEP} step failed."
                TURNKEY_STEP_ERRORS="yes"
            else
                echo ""; cyaneho " ===> RunTurnkey ~~~ SUCCESS: ${TURNKEY_STEP} step passed!"; echo ""
                TURNKEY_STEP_ERRORS="no"
            fi
        fi
        
        # -- Run acceptance tests for specific MNAP units
        if [[ AcceptanceTest == "yes" ]]; then
            UnitTest="${TURNKEY_STEP}"
            RunAcceptanceTestFunction
        fi
        
        # -- Run MNAP cleaning for specific unit
        #    Currently supporting hcp4
        if [[ ${TURNKEY_CLEAN} == "yes" ]]; then
           if [[ "${TURNKEY_STEP}" == "hcp4" ]]; then
               if [[ "${TURNKEY_STEP_ERRORS}" == "no" ]]; then
                   MNAPTurnkeyCleanFunction
               else
                   echo ""; reho " ===> ERROR: ${TURNKEY_STEP} step did not complete. Skipping cleaning for debugging purposes."; echo ""
               fi
           fi
        fi
    done
    
    if [ ${TURNKEY_TYPE} == "xnat" ]; then
        geho "---> Setting recursive r+w+x permissions on ${mnap_studyfolder}"
        chmod -R 777 ${mnap_studyfolder} 2> /dev/null
        cd ${processingdir}
        zip -r logs logs 2> /dev/null
        echo ""
        geho "---> Uploading all logs: curl -u XNAT_USER_NAME:XNAT_PASSWORD -X POST "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_ACCSESSION_ID}/resources/MNAP_LOGS/files/logs.zip?extract=true&overwrite=true&inbody=true" -d logs.zip "
        echo ""
        curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X POST "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_ACCSESSION_ID}/resources/MNAP_LOGS/files/logs.zip?extract=true&overwrite=true&inbody=true" -d logs.zip
        echo ""
        rm -rf ${processingdir}/logs.zip &> /dev/null
        popd 2> /dev/null
        geho "---> Cleaning up:"
        if [[ ${BIDSFormat} != "yes" ]]; then
            echo ""
            geho "     - removing dicom folder"
            rm -rf ${mnap_workdir}/dicom &> /dev/null
            echo ""
        fi
        geho "     - removing stray xml catalog files"
        find ${mnap_studyfolder} -name *catalog.xml -exec echo "       -> {}" \; -exec rm {} \; 2> /dev/null

        if [[ ${CleanupOldFiles} == "yes" ]]; then 
            geho "     - removing files older than run"
            find ${mnap_studyfolder} ! -newer ${workdir}/_startfile -exec echo "       -> {}" \; -exec rm {} \; 2> /dev/null
            rm ${workdir}/_startfile
        fi
    fi
fi

# =-=-=-=-=-=-= RUN SPECIFIC COMMANDS END =-=-=-=-=-=-=

# ------------------------------------------------------------------------------
# -- Report final error checks
# ------------------------------------------------------------------------------

if [[ "${TURNKEY_STEP_ERRORS}" == "yes" ]]; then
    echo ""
    reho " ===> Appears some RunTurnkey steps have failed."
    reho "       Check ${logdir}/comlogs/:"
    reho "       Check ${logdir}/runlogs/:"
    echo ""
    exit 1
else
    echo ""
    geho "------------------------- Successful completion of work --------------------------------"
    echo ""
fi

}

# ------------------------------------------------------------------------------
# -- Execute overall function and read arguments
# ------------------------------------------------------------------------------

main $@