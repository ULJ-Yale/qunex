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
# * This Software conforms to the license outlined in the Qu|Nex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ### TODO
#
# --> finish remaining functions 
#
# ## Description 
#   
# This script, RunTurnkey.sh Qu|Nex Suite workflows in the XNAT Docker Engine
# 
# ## Prerequisite Installed Software
#
# * Qu|Nex Suite
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. $./RunTurnkey.sh --help
#
# ### Expected Previous Processing
# 
# * The necessary input files are BOLD from previous processing
# * These may be stored in: "$qunex_subjectsfolder/$CASE/hcp/$CASE/MNINonLinear/Results/ 
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
# Assumes $TOOLS and $QUNEXREPO are defined
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

# source $TOOLS/$QUNEXREPO/library/environment/qunex_environment.sh &> /dev/null
# $TOOLS/$QUNEXREPO/library/environment/qunex_environment.sh &> /dev/null

QuNexTurnkeyWorkflow="createStudy mapRawData organizeDicom processInbox getHCPReady setupHCP createBatch mapIO hcp1 hcp2 hcp3 runQC_T1w RunQC_T1w runQC_T2w RunQC_T2w runQC_Myelin RunQC_Myelin hcp4 hcp5 runQC_BOLD RunQC_BOLD hcpd runQC_DWI RunQC_DWI hcpdLegacy runQC_DWILegacy RunQC_DWILegacy eddyQC runQC_DWIeddyQC RunQC_DWIeddyQC FSLDtifit runQC_DWIDTIFIT RunQC_DWIDTIFIT FSLBedpostxGPU runQC_DWIProcess RunQC_DWIProcess runQC_DWIBedpostX RunQC_DWIBedpostX pretractographyDense DWIDenseParcellation DWISeedTractography runQC_Custom RunQC_Custom mapHCPData createBOLDBrainMasks computeBOLDStats createStatsReport extractNuisanceSignal preprocessBold preprocessConc g_PlotBoldTS BOLDParcellation computeBOLDfcSeed computeBOLDfcGBC runQC_BOLDfc RunQC_BOLDfc QuNexClean"
QCPlotElements="type=stats|stats>plotdata=fd,imageindex=1>plotdata=dvarsme,imageindex=1;type=signal|name=V|imageindex=1|maskindex=1|colormap=hsv;type=signal|name=WM|imageindex=1|maskindex=1|colormap=jet;type=signal|name=GM|imageindex=1|maskindex=1;type=signal|name=GM|imageindex=2|use=1|scale=3"
SupportedAcceptanceTestSteps="hcp1 hcp2 hcp3 hcp4 hcp5"
QuNexTurnkeyClean="hcp4"

# ------------------------------------------------------------------------------
# -- General usage
# ------------------------------------------------------------------------------

usage() {
    echo ""
    echo "  -- DESCRIPTION:"
    echo ""
    echo "  This function implements Qu|Nex Suite workflows as a turnkey function."
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
    echo "                                                              Supported:   ${QuNexTurnkeyWorkflow} "
    echo "    --turnkeycleanstep=<clean_intermediate worlflow_steps>    Specify specific turnkey steps you wish to clean up intermediate files for:"
    echo "                                                              Supported:   ${QuNexTurnkeyClean}"
    echo "    --batchfile=<batch_file>                                  Batch file with pre-configured header specifying processing parameters" 
    echo "                                                              Note: This file needs to be created *manually* prior to starting runTurnkey"
    echo "                                                              * IF executing a 'local' run then provide the absolute path to the file on the local file system:"
    echo "                                                                 If no absolute path is given then by default Qu|Nex looks for the file here: ~/<project_name>/processing/<project_name>_batch_params.txt"
    echo "                                                              * IF executing a run via the XNAT WebUI then provide the name of the file" 
    echo "                                                                This file should be created and uploaded manually as the project-level resource on XNAT"
    echo ""
    echo "    --mappingfile=<mapping_file>                             File for mapping NIFTI files into the desired Qu|Nex file structure (e.g. hcp , fMRIPrep, etc.)"
    echo "                                                             Note: This file needs to be created *manually* prior to starting runTurnkey"
    echo "                                                              * IF executing a 'local' run then provide the absolute path to the file on the local file system:"
    echo "                                                                 If no absolute path is given then by default Qu|Nex looks for the file here: ~/<project_name>/subjects/specs/final_mapping.txt"
    echo "                                                              * IF executing a run via the XNAT WebUI then provide the name of the file" 
    echo "                                                                This file should be created and uploaded manually as the project-level resource on XNAT"
    echo ""
    echo "  -- ACCEPTANCE TESTING PARAMETERS:"
    echo ""
    echo "    --acceptancetest=<request_acceptance_test>         Specify if you wish to run a final acceptance test after each unit of processing. Default is [no]"
    echo "                                                       If --acceptancetest='yes', then --turnkeysteps must be provided and will be executed first."
    echo "                                                       If --acceptancetest='<turnkey_step>', then acceptance test will be run but step won't be executed."
    echo ""
    echo "  -- XNAT HOST, PROJECT and USER PARMETERS:"
    echo ""
    echo "    --xnathost=<xnat_host_url>                         Specify the XNAT site hostname URL to push data to."
    echo "    --xnatprojectid=<name_of_xnat_project_id>          Specify the XNAT site project id. This is the Project ID in XNAT and not the Project Title."
    echo "    --xnatuser=<xnat_host_user_name>                   Specify XNAT username."
    echo "    --xnatpass=<xnat_host_user_pass>                   Specify XNAT password."
    echo ""
    echo "  -- XNAT SUBJECT AND SESSION PARAMETERS:"
    echo ""
    echo "    --xnatsubjectid=<xnat_subject_id>                  ID for subject across the entire XNAT database. * Required or --xnatsubjectlabel needs to be set."
    echo "    --xnatsubjectlabel=<xnat_subject_label>            Label for subject within a project for the XNAT database. * Required or --xnatsubjectid needs to be set."
    echo "    --xnataccsessionid=<xnat_accesession_id>           ID for subject-specific session within the XNAT project. * Derived from XNAT but can be set manually."
    echo "    --xnatsessionlabel=<xnat_session_label>            Label for session within XNAT project. Note: may be general across multiple subjects (e.g. rest). * Required."
    echo ""
    echo "    --xnatstudyinputpath=<path>                        The path to the previously generated session data as mounted for the container. Default is /input/RESOURCES/qunex_session"
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
    echo "                                  Note: The provided scene has to conform to Qu|Nex QC template standards.xw"
    echo "                                        See $TOOLS/$QUNEXREPO/library/data/scenes/qc/ for example templates."
    echo "                                        The qc path has to contain relevant files for the provided scene."
    echo ""
    echo "    --qcplotimages=<specify_plot_images>         Absolute path to images for g_PlotBoldTS. See 'qunex g_PlotBoldTS' for help. "
    echo "                                                 Only set if g_PlotBoldTS is requested then this is a required setting."
    echo "    --qcplotmasks=<specify_plot_masks>           Absolute path to one or multiple masks to use for extracting BOLD data. See 'qunex g_PlotBoldTS' for help. "
    echo "                                                 Only set if g_PlotBoldTS is requested then this is a required setting."
    echo "    --qcplotelements=<specify_plot_elements>     Plot element specifications for g_PlotBoldTS. See 'qunex g_PlotBoldTS' for help. "
    echo "                                                 Only set if g_PlotBoldTS is requested. If not set then the default is: "
    echo "        ${QCPlotElements}"
    echo ""
    echo "" 
    echo "-- EXAMPLES:"
    echo ""
    echo "   --> Run directly via ${TOOLS}/${QUNEXREPO}/connector/functions/RunTurnkey.sh --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
    echo ""
    reho "           * NOTE: --scheduler is not available via direct script call."
    echo ""
    echo "   --> Run via qunex runTurnkey --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
    echo ""
    geho "           * NOTE: scheduler is available via qunex call:"
    echo "                   --scheduler=<name_of_cluster_scheduler_and_options>  A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
    echo ""
    echo "           * For SLURM scheduler the string would look like this via the qunex call: "
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
unset SESSION
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
#unset LOCAL_BATCH_FILE -- Deprecated
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
qunex_subjectsfolder=`opts_GetOpt "--subjectsfolder" $@`

#CASES=`opts_GetOpt "--subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "${CASES}" | sed 's/,/ /g;s/|/ /g'`
CASE=`opts_GetOpt "--subjects" "$@"`
if [ -z "$CASE" ]; then
    CASE=`opts_GetOpt "--subject" "$@"`
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
SCAN_MAPPING_FILENAME=`opts_GetOpt "--mappingfile" $@`

XNAT_HOST_NAME=`opts_GetOpt "--xnathost" $@`
XNAT_USER_NAME=`opts_GetOpt "--xnatuser" $@`
XNAT_PASSWORD=`opts_GetOpt "--xnatpass" $@`
XNAT_STUDY_INPUT_PATH=`opts_GetOpt "--xnatstudyinputpath" $@`

# ----------------------------------------------------
#     INFO ON XNAT VARIABLE MAPPING FROM Qu|Nex --> JSON --> XML specification
#
# project               --xnatprojectid        #  --> mapping in Qu|Nex: XNAT_PROJECT_ID     --> mapping in JSON spec: #XNAT_PROJECT#   --> Corresponding to project id in XML. 
#   │ 
#   └──subject          --xnatsubjectid        #  --> mapping in Qu|Nex: XNAT_SUBJECT_ID     --> mapping in JSON spec: #SUBJECTID#      --> Corresponding to subject ID in subject-level XML (Subject Accession ID). EXAMPLE in XML        <xnat:subject_ID>BID11_S00192</xnat:subject_ID>
#        │                                                                                                                                                                                                         EXAMPLE in Web UI     Accession number:  A unique XNAT-wide ID for a given human irrespective of project within the XNAT Site
#        │              --xnatsubjectlabel     #  --> mapping in Qu|Nex: XNAT_SUBJECT_LABEL  --> mapping in JSON spec: #SUBJECTLABEL#   --> Corresponding to subject label in subject-level XML (Subject Label).     EXAMPLE in XML        <xnat:field name="SRC_SUBJECT_ID">CU0018</xnat:field>
#        │                                                                                                                                                                                                         EXAMPLE in Web UI     Subject Details:   A unique XNAT project-specific ID that matches the experimenter expectations
#        │ 
#        └──experiment  --xnataccsessionid     #  --> mapping in Qu|Nex: XNAT_ACCSESSION_ID  --> mapping in JSON spec: #ID#             --> Corresponding to subject session ID in session-level XML (Subject Accession ID)   EXAMPLE in XML       <xnat:experiment ID="BID11_E00048" project="embarc_r1_0_0" visit_id="ses-wk2" label="CU0018_MRwk2" xsi:type="xnat:mrSessionData">
#                                                                                                                                                                                                                           EXAMPLE in Web UI    Accession number:  A unique project specific ID for that subject
#                       --xnatsessionlabel     #  --> mapping in Qu|Nex: XNAT_SESSION_LABEL  --> mapping in JSON spec: #LABEL#          --> Corresponding to session label in session-level XML (Session/Experiment Label)    EXAMPLE in XML       <xnat:experiment ID="BID11_E00048" project="embarc_r1_0_0" visit_id="ses-wk2" label="CU0018_MRwk2" xsi:type="xnat:mrSessionData">
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
TURNKEY_STEPS=`echo "${TURNKEY_STEPS}" | sed 's/RunQC/runQC/g'`
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
RunParcellations=`opts_GetOpt "--runparcellations" $@`

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
# -- runQC input flags
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
runQC_Custom=`opts_GetOpt "--customqc" $@`
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

# -- Check that BATCH_PARAMETERS_FILENAME flag and parameter is set
if [[ -z ${BATCH_PARAMETERS_FILENAME} ]]; 
    then reho "ERROR: --batchfile flag missing. Batch parameter file not specified."; echo '';
    exit 1;
fi

########################  runTurnkey LOCAL vs. XNAT-SPECIFIC CHECKS  ################################
#
# -- Check and set non-XNAT or XNAT specific parameters
if [[ ${TURNKEY_TYPE} != "xnat" ]]; then 
   if [[ -z ${PROJECT_NAME} ]]; then reho "ERROR: Project name is missing."; exit 1; echo ''; fi
   if [[ -z ${STUDY_PATH} ]]; then STUDY_PATH=${workdir}/${PROJECT_NAME}; fi
   if [[ -z ${CASE} ]]; then reho "ERROR: Requesting local run but --subject flag is missing."; exit 1; echo ''; fi
fi
if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
    if [[ -z ${XNAT_PROJECT_ID} ]]; then reho "ERROR: --xnatprojectid flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${XNAT_HOST_NAME} ]]; then reho "ERROR: --xnathost flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${XNAT_USER_NAME} ]]; then reho "ERROR: --xnatuser flag missing. Username parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${XNAT_PASSWORD} ]]; then reho "ERROR: --xnatpass flag missing. Password parameter file not specified."; echo ''; exit 1; fi
    if [[ -z ${STUDY_PATH} ]]; then STUDY_PATH=${workdir}/${XNAT_PROJECT_ID}; fi
    if [[ -z ${XNAT_SUBJECT_ID} ]] && [[ -z ${XNAT_SUBJECT_LABEL} ]]; then reho "ERROR: --xnatsubjectid or --xnatsubjectlabel flags are missing. Please specify either subject id or subject label and re-run."; echo ''; exit 1; fi
    if [[ -z ${XNAT_SUBJECT_ID} ]] && [[ ! -z ${XNAT_SUBJECT_LABEL} ]]; then reho " -- Note: --xnatsubjectid is not set. Using --xnatsubjectlabel to query XNAT."; echo ''; fi
    if [[ ! -z ${XNAT_SUBJECT_ID} ]] && [[ -z ${XNAT_SUBJECT_LABEL} ]]; then reho " -- Note: --xnatsubjectlabel is not set. Using --xnatsubjectid to query XNAT."; echo ''; fi
    if [[ -z ${XNAT_SESSION_LABEL} ]]; then reho "ERROR: --xnatsessionlabel flag missing. Please specify session label and re-run."; echo ''; exit 1; fi
    if [[ -z ${XNAT_STUDY_INPUT_PATH} ]]; then XNAT_STUDY_INPUT_PATH=/input/RESOURCES/qunex_study; reho " -- Note: XNAT session input path is not defined. Setting default path to: $XNAT_STUDY_INPUT_PATH"; echo ""; fi
    
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
        CASE=`echo ${XNAT_SESSION_LABEL} | sed 's|_MR1$||' | sed 's|_MR|_|'`
        reho " -- Note: --bidsformat='yes' " 
        reho "       Combining XNAT_SUBJECT_LABEL and XNAT_SESSION_LABEL into unified BIDS-compliant subject variable for Qu|Nex run: ${CASE}"
        echo ""
    else
        CASE="${XNAT_SUBJECT_LABEL}"
    fi
fi
#
################################################################################

# -- Check TURNKEY_STEPS
if [[ -z ${TURNKEY_STEPS} ]] && [ ! -z "${QuNexTurnkeyWorkflow##*${AcceptanceTest}*}" ]; then 
    echo ""
    reho "ERROR: Turnkey steps flag missing. Specify supported turnkey steps:"
    echo "-------------------------------------------------------------------"
    echo " ${QuNexTurnkeyWorkflow}"
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
   if [ ! -z "${QuNexTurnkeyWorkflow##*${TurnkeyTestStep}*}" ]; then
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
    reho "Supported: ${QuNexTurnkeyWorkflow}"; echo "";
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

# -- Function to check for BATCH_PARAMETERS_FILENAME
checkBatchFileHeader() {
    if [[ -z ${BATCH_PARAMETERS_FILENAME} ]]; then reho "ERROR: --batchfile flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    if [[ -f ${BATCH_PARAMETERS_FILENAME} ]]; then
        BATCH_PARAMETERS_FILE_PATH="${BATCH_PARAMETERS_FILENAME}"
    else
        if [[ -f ${RawDataInputPath}/${BATCH_PARAMETERS_FILENAME} ]]; then
            BATCH_PARAMETERS_FILE_PATH="${RawDataInputPath}/${BATCH_PARAMETERS_FILENAME}"
        else
            if [[ ! `echo ${TURNKEY_STEPS} | grep 'createStudy'` ]]; then
                if [[ -f ${STUDY_PATH}/processing/${BATCH_PARAMETERS_FILENAME} ]]; then
                    BATCH_PARAMETERS_FILE_PATH="${STUDY_PATH}/subjects/specs/${BATCH_PARAMETERS_FILENAME}"
                fi
           fi
        fi
    fi
    if [[ ! -f ${BATCH_PARAMETERS_FILE_PATH} ]]; then reho "ERROR: --batchfile flag set but file not found in default locations: ${BATCH_PARAMETERS_FILENAME}"; echo ''; exit 1; fi
}

# -- Function to check for SCAN_MAPPING_FILENAME
checkMappingFile() {
    if [[ -z ${SCAN_MAPPING_FILENAME} ]]; then reho "ERROR: --mappingfile flag missing. Scanning file parameter file not specified."; echo ''; exit 1;  fi
    if [[ -f ${SCAN_MAPPING_FILENAME} ]]; then
        SCAN_MAPPING_FILENAME_PATH="${SCAN_MAPPING_FILENAME}"
    else
        if [[ -f ${RawDataInputPath}/${SCAN_MAPPING_FILENAME} ]]; then
            SCAN_MAPPING_FILENAME_PATH="${RawDataInputPath}/${SCAN_MAPPING_FILENAME}"
        else
            if [[ ! `echo ${TURNKEY_STEPS} | grep 'createStudy'` ]]; then
                if [[ -f ${STUDY_PATH}/processing/${SCAN_MAPPING_FILENAME} ]]; then
                    SCAN_MAPPING_FILENAME_PATH="${STUDY_PATH}/subjects/specs/${SCAN_MAPPING_FILENAME}"
                fi
           fi
        fi
    fi
    if [[ ! -f ${SCAN_MAPPING_FILENAME_PATH} ]]; then reho "ERROR: --mappingfile flag set but file not found in default locations: ${SCAN_MAPPING_FILENAME}"; echo ''; exit 1; fi
}



# -- Code for selecting BOLDS via Tags --> Check if both batch and bolds are specified for QC and if yes read batch explicitly
getBoldList() {
    if [[ ! -z ${ProcessingBatchFile} ]]; then
        LBOLDRUNS="${BOLDRUNS}"
        geho "  --> For ${CASE} searching for BOLD(s): '${LBOLDRUNS}'' in batch file ${ProcessingBatchFile} ... "; 
        if [[ -f ${ProcessingBatchFile} ]]; then
            # For debugging
            # echo "   gmri batchTag2NameKey filename="${ProcessingBatchFile}" subjid="${CASE}" bolds="${LBOLDRUNS}" | grep "BOLDS:" | sed 's/BOLDS://g'"
            LBOLDRUNS=`gmri batchTag2NameKey filename="${ProcessingBatchFile}" subjid="${CASE}" bolds="${LBOLDRUNS}" | grep "BOLDS:" | sed 's/BOLDS://g' | sed 's/,/ /g'`
            LBOLDRUNS="${LBOLDRUNS}"
        else
            reho " ERROR: Requested BOLD modality with a batch file but the batch file not found. Check your inputs!"; echo ""
            exit 1
        fi
        if [[ ! -z ${LBOLDRUNS} ]]; then
            geho "  --> Selected BOLDs: ${LBOLDRUNS} "
            echo ""
        else
            reho " ERROR: No BOLDs found! Something went wrong for ${CASE}. Check your batch file inputs!"; echo ""
            exit 1
        fi
    fi
}


# -- Perform explicit checks for steps which rely on BATCH_PARAMETERS_FILENAME and SCAN_MAPPING_FILENAME
if [[ `echo ${TURNKEY_STEPS} | grep 'createStudy'` ]] || [[ `echo ${TURNKEY_STEPS} | grep 'mapRawData'` ]]; then
    if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
        if [ -z "$BATCH_PARAMETERS_FILENAME" ]; then reho "ERROR: --batchfile flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
        if [ -z "$SCAN_MAPPING_FILENAME" ]; then reho "ERROR: --mappingfile flag missing. Batch parameter file not specified."; echo ''; exit 1;  fi
    fi
    if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
        if [[ `echo ${TURNKEY_STEPS} | grep 'mapRawData'` ]]; then 
            if [[ -z ${RawDataInputPath} ]]; then reho "ERROR: --rawdatainput flag missing. Input data not specified."; echo ''; exit 1; fi
        fi
        checkBatchFileHeader
        checkMappingFile
    fi
fi


# -- Perform checks that batchfile is provided if createBatch has been requested
if [[ `echo ${TURNKEY_STEPS} | grep 'createBatch'` ]]; then
    if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
        if [ -z "$BATCH_PARAMETERS_FILENAME" ]; then reho "ERROR: --batchfile flag missing. Batch parameter file not specified."; echo ''; exit 1; fi
    fi
    if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
        checkBatchFileHeader
    fi
fi

# -- Perform checks that mapping file is provided if getHCPReady has been requested
if [[ `echo ${TURNKEY_STEPS} | grep 'getHCPReady'` ]]; then
    if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
        if [ -z "$SCAN_MAPPING_FILENAME" ]; then reho "ERROR: --mappingfile flag missing. Mapping parameter file not specified."; echo ''; exit 1;  fi
    fi
    if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
        checkMappingFile
    fi
fi

# -- Check and set overwrites
if [ -z "$OVERWRITE_STEP" ]; then OVERWRITE_STEP="no"; fi
if [ -z "$OVERWRITE_SUBJECT" ]; then OVERWRITE_SUBJECT="no"; fi
if [ -z "$OVERWRITE_PROJECT" ]; then OVERWRITE_PROJECT="no"; fi
if [[ -z "$OVERWRITE_PROJECT_XNAT" ]]; then OVERWRITE_PROJECT_XNAT="no"; fi
if [[ -z "$CleanupProject" ]]; then CleanupProject="no"; fi
if [[ -z "$CleanupSubject" ]]; then CleanupSubject="no"; fi

# -- Check and set runQC_Custom
if [ -z "$runQC_Custom" ] || [ "$runQC_Custom" == "no" ]; then runQC_Custom=""; QuNexTurnkeyWorkflow=`printf '%s\n' "${QuNexTurnkeyWorkflow//runQC_Custom/}"`; fi

# -- Check and set DWILegacy
if [ -z "$DWILegacy" ] || [ "$DWILegacy" == "no" ]; then 
    DWILegacy=""
    runQC_DWILegacy=""
    QuNexTurnkeyWorkflow=`printf '%s\n' "${QuNexTurnkeyWorkflow//hcpdLegacy/}"`
    QuNexTurnkeyWorkflow=`printf '%s\n' "${QuNexTurnkeyWorkflow//runQC_DWILegacy/}"`
fi

qunex_studyfolder="${STUDY_PATH}"
qunex_subjectsfolder="${STUDY_PATH}/subjects"
qunex_workdir="${STUDY_PATH}/subjects/${CASE}"
processingdir="${STUDY_PATH}/processing"
logdir="${STUDY_PATH}/processing/logs"
specsdir="${STUDY_PATH}/subjects/specs"
rawdir="${qunex_workdir}/inbox"
rawdir_temp="${qunex_workdir}/inbox_temp"
QUNEXCOMMAND="${TOOLS}/${QUNEXREPO}/connector/qunex.sh"

if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
    SpecsBatchFileHeader="${specsdir}/${BATCH_PARAMETERS_FILENAME}"
    ProcessingBatchFile="${processingdir}/${BATCH_PARAMETERS_FILENAME}"
    SpecsMappingFile="${specsdir}/${SCAN_MAPPING_FILENAME}"
fi
if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
    BatchFileName=`basename ${BATCH_PARAMETERS_FILENAME}`
    MappingFileName=`basename ${SCAN_MAPPING_FILENAME}`
    SpecsMappingFile="${specsdir}/${MappingFileName}"
    SpecsBatchFileHeader="${specsdir}/${BatchFileName}"
    ProcessingBatchFile="${processingdir}/${BatchFileName}"
fi

# -- Report options
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   "
echo "   Qu|Nex Turnkey run type: ${TURNKEY_TYPE}"
echo "   Qu|Nex Turnkey clean interim files: ${TURNKEY_CLEAN}"

if [ "$TURNKEY_TYPE" == "xnat" ]; then
    echo "   XNAT Hostname: ${XNAT_HOST_NAME}"
    echo "   XNAT Project ID: ${XNAT_PROJECT_ID}"
    echo "   XNAT Subject Label: ${XNAT_SUBJECT_LABEL}"
    echo "   XNAT Subject ID: ${XNAT_SUBJECT_ID}"
    echo "   XNAT Session Label: ${XNAT_SESSION_LABEL}"
    echo "   XNAT Session ID: ${XNAT_ACCSESSION_ID}"
    echo "   XNAT Resource Mapping file: ${SCAN_MAPPING_FILENAME}"
    echo "   XNAT Resource Project-specific Batch file: ${BATCH_PARAMETERS_FILENAME}"
    if [ "$BIDSFormat" == "yes" ]; then
        echo "   BIDS format input specified: ${BIDSFormat}"
        echo "   Combined BIDS-formatted subject name: ${CASE}"
    else 
        echo "   Qu|Nex Subject variable name: ${CASE}" 
    fi
fi
if [ "$TURNKEY_TYPE" != "xnat" ]; then
    echo "   Local project name: ${PROJECT_NAME}"
    echo "   Raw data input path: ${RawDataInputPath}"
    echo "   Qu|Nex Subject variable name: ${CASE}" 
    echo "   Qu|Nex Batch file input: ${BATCH_PARAMETERS_FILENAME}"
    echo "   Qu|Nex Mapping file input: ${SCAN_MAPPING_FILENAME}"
fi

echo "   Qu|Nex Project-specific final Batch file path: ${ProcessingBatchFile}"
echo "   Qu|Nex Study folder: ${qunex_studyfolder}"
echo "   Qu|Nex Log folder: ${logdir}"
echo "   Qu|Nex Subject-specific working folder: ${rawdir}"
echo "   Overwrite for a given turnkey step set to: ${OVERWRITE_STEP}"
echo "   Overwrite for subject set to: ${OVERWRITE_SUBJECT}"
echo "   Overwrite for project set to: ${OVERWRITE_PROJECT}"
echo "   Overwrite for the entire XNAT project: ${OVERWRITE_PROJECT_XNAT}"
echo "   Cleanup for subject set to: ${CleanupSubject}"
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

if [[ ! -z "${SUBJID}" ]]; then 
echo "   Subjid parameter: ${SUBJID}"
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
geho "------------------------- Start of Qu|Nex Turnkey Workflow --------------------------------"
echo ""

# --- Report the environment variables for Qu|Nex Turnkey run: 
echo ""
bash ${TOOLS}/${QUNEXREPO}/library/environment/qunex_envStatus.sh --envstatus
echo ""

# ---- Map the data from input to output when in XNAT workflow
if [[ ${TURNKEY_TYPE} == "xnat" ]] && [[ ${OVERWRITE_PROJECT_XNAT} != "yes" ]] ; then
    # --- Specify what to map
    firstStep=`echo ${TURNKEY_STEPS} | awk '{print $1;}'`
    echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: Initial data re-map from XNAT with ${firstStep} as starting point ..."; echo ""
    # --- Create a study folder
    geho " -- Creating study folder structure... "; echo ""
    ${QUNEXCOMMAND} createStudy "${qunex_studyfolder}"
    geho " -- Mapping existing data into place to support the first turnkey step: ${firstStep}"; echo ""
    # --- Work through the mapping steps
    case ${firstStep} in
        processInbox)
            # --- rsync relevant dependencies if processInbox is starting point 
            RsyncCommand="rsync -avzH --include='/subjects' --include='${CASE}' --include='inbox/***' --include='specs/***' --include='/processing' --include='scenes/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${qunex_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        getHCPReady|setupHCP|createBatch)
            # --- rsync relevant dependencies if getHCPReady or setupHCP is starting point 
            RsyncCommand="rsync -avzH --include='/subjects' --include='${CASE}' --include='*.txt' --include='specs/***' --include='nii/***' --include='/processing' --include='scenes/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${qunex_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        hcp1|hcp2|hcp3|runQC_T1w|runQC_T2w|runQC_Myelin)
            # --- rsync relevant dependencies if and hcp or QC step is starting point
            RsyncCommand="rsync -avzH --include='/processing' --include='scenes/***' --include='specs/***' --include='/subjects' --include='${CASE}' --include='*.txt' --include='hcp/' --include='unprocessed/***' --include='MNINonLinear/***' --include='T1w/***' --include='T2w/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${qunex_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        hcp4|hcp5|runQC_BOLD)
            # --- rsync relevant dependencies if and hcp or QC step is starting point
            RsyncCommand="rsync -avzH --include='/processing' --include='scenes/***' --include='specs/***' --include='/subjects' --include='${CASE}' --include='*.txt' --include='hcp/' --include='unprocessed/***' --include='MNINonLinear/***' --include='T1w/***' --include='T2w/***' --include='BOLD*/***' --include='*fMRI*/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${qunex_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        hcpd|runQC_DWI|hcpdLegacy|runQC_DWILegacy|eddyQC|runQC_DWIeddyQC|FSLDtifit|runQC_DWIDTIFIT|FSLBedpostxGPU|runQC_DWIProcess|runQC_DWIBedpostX|pretractographyDense|DWIDenseParcellation|DWISeedTractography|runQC_Custom)
            # --- rsync relevant dependencies if and hcp or QC step is starting point
            RsyncCommand="rsync -avzH --include='/processing' --include='scenes/***' --include='specs/***' --include='/subjects' --include='${CASE}' --include='*.txt' --include='hcp/' --include='unprocessed/***' --include='MNINonLinear/***' --include='T1w/***' --include='Diffusion/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${qunex_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        runQC_Custom)
            # --- rsync relevant dependencies if and hcp or QC step is starting point
            RsyncCommand="rsync -avzH --include='/processing' --include='scenes/***' --include='specs/***' --include='/subjects' --include='${CASE}' --include='*.txt' --include='hcp/' --include='MNINonLinear/***' --include='T1w/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${qunex_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        mapHCPData)
            # --- rsync relevant dependencies if and mapHCPData is starting point
            RsyncCommand="rsync -avzH --include='/processing' --include='scenes/***' --include='specs/***' --include='/subjects' --include='${CASE}/' --include='*.txt' --include='hcp/' --include='MNINonLinear/***' --include='T1w/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${qunex_studyfolder}"
            echo ""; geho " -- Running rsync: ${RsyncCommand}"; echo ""
            eval ${RsyncCommand}
            ;;
        createBOLDBrainMasks|computeBOLDStats|createStatsReport|extractNuisanceSignal|preprocessBold|preprocessConc|g_PlotBoldTS|BOLDParcellation|computeBOLDfcGBC|computeBOLDfcSeed|runQC_BOLDfc)
            # --- rsync relevant dependencies if any BOLD fc step is starting point
            RsyncCommand="rsync -avzH --include='/processing' --include='specs/***' --include='scenes/***' --include='/subjects' --include='${CASE}' --include='*.txt' --include='images/***' --exclude='*' ${XNAT_STUDY_INPUT_PATH}/ ${qunex_studyfolder}"
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
            rm -rf ${qunex_studyfolder}/ &> /dev/null
        fi
fi
if [[ ${OVERWRITE_PROJECT_XNAT} == "yes" ]]; then
        reho " -- Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${qunex_studyfolder}/ &> /dev/null
fi
if [[ ${OVERWRITE_PROJECT} == "yes" ]] && [[ ${TURNKEY_STEPS} == "all" ]]; then
    if [[ `ls -IQC -Ilists -Ispecs -Iinbox -Iarchive ${qunex_subjectsfolder}` == "$CASE" ]]; then
        reho " -- ${CASE} is the only folder in ${qunex_subjectsfolder}. OK to proceed!"
        reho "    Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${qunex_studyfolder}/ &> /dev/null
    else
        reho " -- ${CASE} is not the only folder in ${qunex_studyfolder}."
        reho "    Skipping recursive overwrite for project: ${XNAT_PROJECT_ID}"; echo ""
    fi
fi
if [[ ${OVERWRITE_PROJECT} == "yes" ]] && [[ ${TURNKEY_STEPS} == "createStudy" ]]; then
    if [[ `ls -IQC -Ilists -Ispecs -Iinbox -Iarchive ${qunex_subjectsfolder}` == "$CASE" ]]; then
        reho " -- ${CASE} is the only folder in ${qunex_subjectsfolder}. OK to proceed!"
        reho "    Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
        rm -rf ${qunex_studyfolder}/ &> /dev/null
    else
        reho " -- ${CASE} is not the only folder in ${qunex_studyfolder}."
        reho "    Skipping recursive overwrite for project: ${XNAT_PROJECT_ID}"; echo ""
    fi
fi
if [[ ${OVERWRITE_SUBJECT} == "yes" ]]; then
    reho " -- Removing specific subject: ${qunex_workdir}."; echo ""
    rm -rf ${qunex_workdir} &> /dev/null
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
        geho " -- Checking for and generating study folder ${qunex_studyfolder}"; echo ""
        if [ ! -d ${workdir} ]; then
            mkdir -p ${workdir} &> /dev/null
        fi
        if [ ! -d ${qunex_studyfolder} ]; then
            reho " -- Note: ${qunex_studyfolder} not found. Regenerating now..." 2>&1 | tee -a ${createStudy_ComlogTmp}  
            echo "" 2>&1 | tee -a ${createStudy_ComlogTmp}
            ${QUNEXCOMMAND} createStudy "${qunex_studyfolder}"
            mv ${createStudy_ComlogTmp} ${logdir}/comlogs/
            createStudy_ComlogTmp="${logdir}/comlogs/tmp_createStudy_${CASE}_${TimeStamp}.log"
        else
            geho " -- Study folder ${qunex_studyfolder} already exits!" 2>&1 | tee -a ${createStudy_ComlogTmp}
            if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
                if [[ ${OVERWRITE_PROJECT_XNAT} == "yes" ]]; then
                    reho "    Overwrite set to 'yes' for XNAT run. Removing entire project: ${XNAT_PROJECT_ID}"; echo ""
                    rm -rf ${qunex_studyfolder}/ &> /dev/null
                    reho " -- Note: ${qunex_studyfolder} removed. Regenerating now..." 2>&1 | tee -a ${createStudy_ComlogTmp}  
                    echo "" 2>&1 | tee -a ${createStudy_ComlogTmp}
                    ${QUNEXCOMMAND} createStudy "${qunex_studyfolder}"
                    mv ${createStudy_ComlogTmp} ${logdir}/comlogs/
                    createStudy_ComlogTmp="${logdir}/comlogs/tmp_createStudy_${CASE}_${TimeStamp}.log"
                fi
            fi
        fi
        if [ ! -f ${qunex_studyfolder}/.qunexstudy ]; then
            reho " -- Note: ${qunex_studyfolder}qunexstudy file not found. Not a proper Qu|Nex file hierarchy. Regenerating now..."; echo "";
            ${QUNEXCOMMAND} createStudy "${qunex_studyfolder}"
        fi
        
        mkdir -p ${qunex_workdir} &> /dev/null
        mkdir -p ${qunex_workdir}/inbox &> /dev/null
        mkdir -p ${qunex_workdir}/inbox_temp &> /dev/null
        
        if [ -f ${qunex_studyfolder}/.qunexstudy ]; then CREATESTUDYCHECK="pass"; else CREATESTUDYCHECK="fail"; fi
       
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
        
        # Perform checks for output Qu|Nex hierarchy
        if [ ! -d ${workdir} ]; then
            mkdir -p ${workdir} &> /dev/null
        fi
        if [ ! -d ${qunex_studyfolder} ]; then
            reho " -- Note: ${qunex_studyfolder} not found. Regenerating now..."; echo "";
            ${QUNEXCOMMAND} createStudy "${qunex_studyfolder}"
        fi
        if [ ! -f ${qunex_studyfolder}/.qunexstudy ]; then
            reho " -- Note: ${qunex_studyfolder} qunexstudy file not found. Not a proper Qu|Nex file hierarchy. Regenerating now..."; echo "";
            ${QUNEXCOMMAND} createStudy "${qunex_studyfolder}"
        fi
        if [ ! -d ${qunex_subjectsfolder} ]; then
            reho " -- Note: ${qunex_subjectsfolder} folder not found. Not a proper Qu|Nex file hierarchy. Regenerating now..."; echo "";
            ${QUNEXCOMMAND} createStudy "${qunex_studyfolder}"
        fi
        if [ ! -d ${qunex_workdir} ]; then
            reho " -- Note: ${qunex_workdir} not found. Creating one now..."; echo ""
            mkdir -p ${qunex_workdir} &> /dev/null
            mkdir -p ${qunex_workdir}/inbox &> /dev/null
            mkdir -p ${qunex_workdir}/inbox_temp &> /dev/null
        fi
        
        # -- Perform overwrite checks
        if [[ ${OVERWRITE_STEP} == "yes" ]] && [[ ${TURNKEY_STEP} == "mapRawData" ]]; then
               rm -rf ${qunex_workdir}/inbox/* &> /dev/null
        fi
        CheckInbox=`ls -1A ${rawdir} | wc -l`
        if [[ ${CheckInbox} != "0" ]] && [[ ${OVERWRITE_STEP} == "no" ]]; then
               reho "ERROR: ${qunex_workdir}/inbox/ is not empty and --overwritestep=${OVERWRITE_STEP} "
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
            echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${BATCH_PARAMETERS_FILENAME}""
            echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${SCAN_MAPPING_FILENAME}""
            echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc/files?format=zip" > ${processingdir}/scenes/QC/scene_qc_files.zip"
            echo ""
            echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${BATCH_PARAMETERS_FILENAME}"" >> ${mapRawData_ComlogTmp}
            echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${SCAN_MAPPING_FILENAME}"" >> ${mapRawData_ComlogTmp}
            echo "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/resources/scenes_qc/files?format=zip" > ${processingdir}/scenes/QC/scene_qc_files.zip"  >> ${mapRawData_ComlogTmp}

            curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${BATCH_PARAMETERS_FILENAME}" > ${specsdir}/${BATCH_PARAMETERS_FILENAME}
            curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/projects/${XNAT_PROJECT_ID}/resources/QUNEX_PROC/files/${SCAN_MAPPING_FILENAME}" > ${specsdir}/${SCAN_MAPPING_FILENAME}
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
            
            # -- Perform checks for batch and mapping files being mapped correctly
            if [[ ! -f ${specsdir}/${BATCH_PARAMETERS_FILENAME} ]]; then
                echo " ==> ERROR: Scan batch file ${BATCH_PARAMETERS_FILENAME} not found in ${RawDataInputPath}!"
                BATCHFILECHECK="fail"
                exit 1
            else
                if [[ ! `more ${specsdir}/${BATCH_PARAMETERS_FILENAME} | grep '_hcp_Pipeline'` ]]; then
                    BATCHFILECHECK="fail"
                    echo " ==> ERROR: Scan batch file ${BATCH_PARAMETERS_FILENAME} content not correct in ${RawDataInputPath}!"
                    exit 1
                fi
            fi
            if [[ ! -f ${specsdir}/${SCAN_MAPPING_FILENAME} ]]; then
                echo " ==> ERROR: Scan mapping file ${SCAN_MAPPING_FILENAME_PATH} not found in ${RawDataInputPath}!"
                MAPPINGFILECHECK="fail"
                exit 1
            else
                if [[ ! `more ${specsdir}/${SCAN_MAPPING_FILENAME} | grep '=>'` ]]; then
                    echo " ==> ERROR: Scan mapping file ${SCAN_MAPPING_FILENAME_PATH} not found in ${RawDataInputPath}!"
                    MAPPINGFILECHECK="fail"
                    exit 1
                fi
            fi
        fi
        
        # -- Map data for local non-XNAT run
        if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
            geho " --> Running turnkey via local: `hostname`"; echo ""
            if [[ ! -f ${SpecsBatchFileHeader} ]]; then
                if [[ -f ${BATCH_PARAMETERS_FILE_PATH} ]]; then
                    cp ${BATCH_PARAMETERS_FILE_PATH} ${SpecsBatchFileHeader} &> /dev/null
                else
                    echo " ==> ERROR: Batch parameters file ${BATCH_PARAMETERS_FILENAME} not found in ${RawDataInputPath}!"
                fi
            fi
            if [[ ! -f ${SpecsMappingFile} ]]; then
                if [[ -f ${SCAN_MAPPING_FILENAME_PATH} ]]; then
                    geho "  cp ${SCAN_MAPPING_FILENAME_PATH} ${SpecsMappingFile}"
                    cp ${SCAN_MAPPING_FILENAME_PATH} ${SpecsMappingFile} &> /dev/null
                else
                    echo " ==> ERROR: Scan mapping file ${SCAN_MAPPING_FILENAME_PATH} not found in ${RawDataInputPath}!"
                fi
            fi
        fi
        
        # -- Check if BIDS format NOT requested
        if [[ ${BIDSFormat} != "yes" ]]; then
            unset FILECHECK
            echo ""
            geho " -- Linking DICOMs into ${rawdir}"; echo ""
            # -- Find and link DICOMs for XNAT run
            if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
                echo "  find ${RawDataInputPath} -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" -exec ln -s '{}' ${rawdir}/ ';'"
                find ${RawDataInputPath} -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" -exec ln -s '{}' ${rawdir}/ ';' &> /dev/null
                DicomInputCount=`find ${RawDataInputPath} -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" | wc | awk '{print $1}'`
                DicomMappedCount=`ls ${rawdir}/* | wc | awk '{print $1}'`
                if [[ ${DicomInputCount} == ${DicomMappedCount} ]]; then FILECHECK="pass"; else FILECHECK="fail"; fi
            fi
            # -- Find and link DICOMs for non-XNAT run
            if [[ ${TURNKEY_TYPE} != "xnat" ]]; then
                # -- Check if input is an archive file
                if [[ "$(ls ${RawDataInputPath}/*zip*)" ]] || [[ "$(ls ${RawDataInputPath}/*gz*)" ]]; then
                    InputArchive="yes"
                    # -- Hard link into masterinbox
                    ln ${RawDataInputPath}/*gz ${qunex_subjectsfolder}/${CASE}/inbox/ &> /dev/null
                    ln ${RawDataInputPath}/*zip ${qunex_subjectsfolder}/${CASE}/inbox/ &> /dev/null
                    CheckCASECount=`ls ${qunex_subjectsfolder}/${CASE}/inbox/* | wc -l`
                    CASEinbox=`basename ${qunex_subjectsfolder}/${CASE}/inbox/${CASE}*`
                    CASEext="${CASEinbox#*.}"
                    # -- Check for duplicates
                    if [[ "$CheckCASECount" -gt "1" ]]; then
                         reho " ===> Note: More than one zip file found for ${CASE}"
                    fi
                    if [[ -z `ls ${qunex_subjectsfolder}/${CASE}/inbox/${CASEinbox}` ]]; then
                        reho " ===> ERROR: no files found!"
                        echo ""
                        return 1
                    else
                        geho " -- Unzipping ${qunex_subjectsfolder}/${CASE}/inbox/${CASEinbox}"; echo ""
                        # --> Decompress mapped input
                        # -- ToDo --> Add support for Other types of arhive files
                        if [[ ${CASEext} == "zip" ]]; then
                            cd ${qunex_subjectsfolder}/${CASE}/inbox/
                            if [[ `unzip -t ${CASEinbox}` ]]; then
                                geho "   ZIP archive found and passed check."; echo ""
                                unzip ${CASEinbox} -d ${qunex_subjectsfolder}/${CASE}/inbox/ >/dev/null 2>&1; echo ""
                                # -- Map dicoms into ${qunex_subjectsfolder}/${CASE}/inbox
                                DicomInputCount=`find ${qunex_subjectsfolder}/${CASE}/inbox/ -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" | wc | awk '{print $1}'`
                                find ${qunex_subjectsfolder}/${CASE}/inbox/ -mindepth 2 -type f -not -name "*.xml" -not -name "*.gif" -exec mv '{}' ${rawdir}/ ';' &> /dev/null
                                rm -rf ${qunex_subjectsfolder}/${CASE}/inbox/${CASE}* >/dev/null 2>&1
                                DicomMappedCount=`ls ${rawdir}/* | wc | awk '{print $1}'`
                                if [[ ${DicomInputCount} == ${DicomMappedCount} ]]; then FILECHECK="pass"; else FILECHECK="fail"; fi
                                # -- ToDo --> Add support for NIFTI zip files
                            else
                                reho " ===> ERROR: ZIP archive found but did not pass check!"; echo ""
                                FILECHECK="fail"
                            fi
                        fi
                    fi
                else
                   # -- Find and link DICOMs for non-XNAT run from raw DICOM input
                   echo "  find ${RawDataInputPath} -type f -not -name "*.xml" -not -name "*.gif" -exec ln '{}' ${rawdir}/ ';'"
                   find ${RawDataInputPath} -type f -not -name "*.xml" -not -name "*.gif" -not -name "*.sh" -not -name "*.txt" -not -name ".*" -exec ln -s '{}' ${rawdir}/ ';' &> /dev/null
                   DicomInputCount=`find ${RawDataInputPath} -type f -not -name "*.xml" -not -name "*.gif" -not -name "*.sh" -not -name "*.txt" -not -name ".*" | wc | awk '{print $1}'`
                   DicomMappedCount=`ls ${rawdir}/* | wc | awk '{print $1}'`
                   if [[ ${DicomInputCount} == ${DicomMappedCount} ]]; then FILECHECK="pass"; else FILECHECK="fail"; fi
                fi
            fi
        fi

        # -- Check if BIDS format IS requested
        if [[ ${BIDSFormat} == "yes" ]]; then
            unset FILECHECK
            # -- NOTE: IF XNAT run is not requested then it assumed that zipped BIDS data is prepared in $qunex_subjectsfolder/inbox/BIDS/*zip
            if [[ ${TURNKEY_TYPE} == "xnat" ]]; then
                # -- Set IF statement to check if /input mapped from XNAT for container run or curl call needed
                if [[ -d ${RawDataInputPath} ]]; then
                   if [[ `find ${RawDataInputPath} -type f -name "*.json" | wc -l` -gt 0 ]] && [[ `find ${RawDataInputPath} -type f -name "*.nii" | wc -l` -gt 0 ]]; then 
                       echo ""; echo " -- BIDS JSON and NII data found"; echo ""
                       mkdir ${qunex_subjectsfolder}/inbox/BIDS/${CASE} &> /dev/null
                       cp -r ${RawDataInputPath}/* ${qunex_subjectsfolder}/inbox/BIDS/${CASE}/
                       cd ${qunex_subjectsfolder}/inbox/BIDS
                       zip -r ${CASE} ${CASE} 2> /dev/null
                   else
                       echo ""
                       geho " -- Running:  "
                       geho "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${qunex_subjectsfolder}/inbox/BIDS/${CASE}.zip "; echo ""
                       curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${qunex_subjectsfolder}/inbox/BIDS/${CASE}.zip
                   fi
                else
                    # -- Get the BIDS data in ZIP format via curl
                    echo ""
                    geho " -- Running:  "
                    geho "  curl -u XNAT_USER_NAME:XNAT_PASSWORD -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${qunex_subjectsfolder}/inbox/BIDS/${CASE}.zip "; echo ""
                    curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X GET "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SUBJECT_ID}/experiments/${XNAT_ACCSESSION_ID}/scans/ALL/files?format=zip" > ${qunex_subjectsfolder}/inbox/BIDS/${CASE}.zip
                fi
            else
                cp -r ${RawDataInputPath}/${CASE}.zip ${qunex_subjectsfolder}/inbox/BIDS/${CASE}.zip
            fi
            # -- Perform mapping of BIDS file structure into Qu|Nex
            echo ""
            geho " -- Running:  "
            geho "  ${QUNEXCOMMAND} BIDSImport --subjectsfolder="${qunex_subjectsfolder}" --inbox="${qunex_subjectsfolder}/inbox/BIDS/${CASE}.zip" --action="copy" --overwrite="yes" --archive="delete" "; echo ""
            ${QUNEXCOMMAND} BIDSImport --subjectsfolder="${qunex_subjectsfolder}" --inbox="${qunex_subjectsfolder}/inbox/BIDS/${CASE}.zip" --action="copy" --overwrite="yes" --archive="delete" >> ${mapRawData_ComlogTmp}
            popd 2> /dev/null
            rm -rf ${qunex_subjectsfolder}/inbox/BIDS/${CASE}* &> /dev/null
            # -- Run BIDS completion checks on mapped data
            if [ -f ${qunex_subjectsfolder}/${CASE}/bids/bids2nii.log ]; then
                 FILESEXPECTED=`more ${qunex_subjectsfolder}/${CASE}/bids/bids2nii.log | grep "=>" | wc -l 2> /dev/null`
            else
                 FILECHECK="fail"
            fi
            FILEFOUND=`ls ${qunex_subjectsfolder}/${CASE}/nii/* | wc -l 2> /dev/null`
            if [ -z ${FILEFOUND} ]; then
                FILECHECK="fail"
            fi
            if [[ ${FILESEXPECTED} == ${FILEFOUND} ]]; then
                echo ""
                geho " -- BIDSImport successful. Expected ${FILESEXPECTED} files and found ${FILEFOUND} files."
                echo ""
                FILECHECK="pass"
            else
                FILECHECK="fail"
            fi
        fi
        
        # -- Check if mapping and batch files exist and if content OK
        if [[ -f ${SpecsBatchFileHeader} ]]; then BATCHFILECHECK="pass"; else BATCHFILECHECK="fail"; fi
        if [[ -z `more ${SpecsBatchFileHeader} | grep '_hcp_Pipeline'` ]]; then BATCHFILECHECK="fail"; fi
        if [[ -f ${SpecsMappingFile} ]]; then MAPPINGFILECHECK="pass"; else MAPPINGFILECHECK="fail"; fi
        if [[ -z `more ${SpecsMappingFile} | grep '=>'` ]]; then MAPPINGFILECHECK="fail"; fi
        
        # -- Declare checks
        echo "" >> ${mapRawData_ComlogTmp}
        echo "----------------------------------------------------------------------------" >> ${mapRawData_ComlogTmp}
        echo "  --> Batch file transfer check: ${BATCHFILECHECK}" >> ${mapRawData_ComlogTmp}
        echo "  --> Mapping file transfer check: ${MAPPINGFILECHECK}" >> ${mapRawData_ComlogTmp}
        if [[ ${BIDSFormat} == "yes" ]]; then
            echo "  --> BIDS mapping check: ${FILECHECK}" >> ${mapRawData_ComlogTmp}
        fi
        if [[ ${InputArchive} != "yes" ]]; then
            echo "  --> DICOM file count in input folder /input/SCANS: ${DicomInputCount}" >> ${mapRawData_ComlogTmp}
            echo "  --> DICOM file count in output folder ${rawdir}: ${DicomMappedCount}" >> ${mapRawData_ComlogTmp}
            echo "  --> DICOM mapping check: ${FILECHECK}" >> ${mapRawData_ComlogTmp}
        fi
        if [[ ${InputArchive} == "yes" ]]; then
            echo "  --> Archive inbox processed: ${FILECHECK}" >> ${mapRawData_ComlogTmp}
        fi
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
    
    # -- processInbox for DICOMs
    turnkey_processInbox() {
        if [[ ${BIDSFormat} != "yes" ]]; then
            echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: processInbox ..."; echo ""
            # ------------------------------
            TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
            processInbox_Runlog="${logdir}/runlogs/Log-processInbox${TimeStamp}.log"
            processInbox_ComlogTmp="${logdir}/comlogs/tmp_processInbox_${CASE}_${TimeStamp}.log"; touch ${processInbox_ComlogTmp}; chmod 777 ${processInbox_ComlogTmp}
            processInbox_ComlogError="${logdir}/comlogs/error_processInbox_${CASE}_${TimeStamp}.log"
            processInbox_ComlogDone="${logdir}/comlogs/done_processInbox_${CASE}_${TimeStamp}.log"
            ExecuteCall="${QUNEXCOMMAND} processInbox --subjectsfolder='${qunex_subjectsfolder}' --sessions='${CASE}' --masterinbox='none' --archive='delete' --check='any' --overwrite='${OVERWRITE_STEP}'"
            echo ""; echo " -- Executed call:"; echo "   $ExecuteCall"; echo ""
            eval ${ExecuteCall} 2>&1 | tee -a ${processInbox_ComlogTmp}
            cd ${qunex_subjectsfolder}/${CASE}/nii; NIILeadZeros=`ls ./0*.nii.gz 2>/dev/null`; for NIIwithZero in ${NIILeadZeros}; do NIIwithoutZero=`echo ${NIIwithZero} | sed 's/0//g'`; mv ${NIIwithZero} ${NIIwithoutZero}; done
            if [[ ! -z `cat ${processInbox_ComlogTmp} | grep 'Successful completion'` ]]; then processInboxCheck="pass"; else processInboxCheck="fail"; fi
            if [[ ${processInboxCheck} == "pass" ]]; then
                mv ${processInbox_ComlogTmp} ${processInbox_ComlogDone}
                processInbox_Comlog=${processInbox_ComlogDone}
            else
               mv ${processInbox_ComlogTmp} ${processInbox_ComlogError}
               processInbox_Comlog=${processInbox_ComlogError}
            fi
            # ------------------------------
            if [ ${TURNKEY_TYPE} == "xnat" ]; then
                reho "---> Cleaning up: removing inbox folder"
                rm -rf ${qunex_workdir}/inbox &> /dev/null
            fi
        else
            echo ""; cyaneho " ===> RunTurnkey ~~~ SKIPPING: processInbox because data is in BIDS NII format."; echo ""
        fi
    }
     
    # -- Generate subject_hcp.txt file
    turnkey_getHCPReady() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: getHCPReady ..."; echo ""
        if [[ "${OVERWRITE_STEP}" == "yes" ]]; then
            rm -rf ${qunex_subjectsfolder}/${CASE}/subject_hcp.txt &> /dev/null
        fi
        if [ -f ${qunex_subjectsfolder}/subject_hcp.txt ]; then
            echo ""; geho " ===> ${qunex_subjectsfolder}/subject_hcp.txt exists. Set --overwrite='yes' to re-run."; echo ""; return 0
        fi
        # ------------------------------
        TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        getHCPReady_Runlog="${logdir}/runlogs/Log-getHCPReady${TimeStamp}.log"
        getHCPReady_ComlogTmp="${logdir}/comlogs/tmp_getHCPReady_${CASE}_${TimeStamp}.log"; touch ${getHCPReady_ComlogTmp}; chmod 777 ${getHCPReady_ComlogTmp}
        getHCPReady_ComlogError="${logdir}/comlogs/error_getHCPReady_${CASE}_${TimeStamp}.log"
        getHCPReady_ComlogDone="${logdir}/comlogs/done_getHCPReady_${CASE}_${TimeStamp}.log"
        ExecuteCall="${QUNEXCOMMAND} getHCPReady --subjectsfolder="${qunex_subjectsfolder}" --sessions="${CASE}" --mapping="${SpecsMappingFile}""
        echo ""; echo " -- Executed call:"; echo "   $ExecuteCall"; echo ""
        eval ${ExecuteCall}  2>&1 | tee -a ${getHCPReady_ComlogTmp}
        if [[ ! -z `cat ${getHCPReady_ComlogTmp} | grep 'Successful completion'` ]]; then getHCPReadyCheck="pass"; else getHCPReadyCheck="fail"; fi
        if [[ ${getHCPReadyCheck} == "pass" ]]; then
            mv ${getHCPReady_ComlogTmp} ${getHCPReady_ComlogDone}
            getHCPReady_Comlog=${getHCPReady_ComlogDone}
        else
           mv ${getHCPReady_ComlogTmp} ${getHCPReady_ComlogError}
           getHCPReady_Comlog=${getHCPReady_ComlogError}
        fi
        # ------------------------------
    }

    # -- Map files to hcp processing folder structure 
    turnkey_setupHCP() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: setupHCP ..."; echo ""
        # ------------------------------
        TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        setupHCP_Runlog="${logdir}/runlogs/Log-setupHCP${TimeStamp}.log"
        setupHCP_ComlogTmp="${logdir}/comlogs/tmp_setupHCP_${CASE}_${TimeStamp}.log"; touch ${setupHCP_ComlogTmp}; chmod 777 ${setupHCP_ComlogTmp}
        setupHCP_ComlogError="${logdir}/comlogs/error_setupHCP_${CASE}_${TimeStamp}.log"
        setupHCP_ComlogDone="${logdir}/comlogs/done_setupHCP_${CASE}_${TimeStamp}.log"
        if [[ ${OVERWRITE_STEP} == "yes" ]]; then
           echo "  -- Removing prior hard link mapping..."; echo ""
           # rm -rf ${ProcessingBatchFile} &> /dev/null
           HLinks=`ls ${qunex_subjectsfolder}/${CASE}/hcp/${CASE}/*/*nii* 2>/dev/null`; for HLink in ${HLinks}; do unlink ${HLink}; done
        fi        
        ExecuteCall="${QUNEXCOMMAND} setupHCP --subjectsfolder='${qunex_subjectsfolder}' --sessions='${CASE}' --existing='clear'"
        echo ""; echo " -- Executed call:"; echo "   $ExecuteCall"; echo ""
        eval ${ExecuteCall} 2>&1 | tee -a ${setupHCP_ComlogTmp}
        # geho " -- Generating ${ProcessingBatchFile}"; echo ""
        # cp ${SpecsBatchFileHeader} ${ProcessingBatchFile}; cat ${qunex_workdir}/subject_hcp.txt >> ${ProcessingBatchFile}
        if [[ ! -z `cat ${setupHCP_ComlogTmp} | grep 'Successful completion'` ]]; then setupHCPCheck="pass"; else setupHCPCheck="fail"; fi
        if [[ ${setupHCPCheck} == "pass" ]]; then
            mv ${setupHCP_ComlogTmp} ${setupHCP_ComlogDone}
            setupHCP_Comlog=${setupHCP_ComlogDone}
        else
           mv ${setupHCP_ComlogTmp} ${setupHCP_ComlogError}
           setupHCP_Comlog=${setupHCP_ComlogError}
        fi
        # ------------------------------
    }

    # -- Map files to hcp processing folder structure 
    turnkey_createBatch() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: createBatch ..."; echo ""
        # ------------------------------
        TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        createBatch_Runlog="${logdir}/runlogs/Log-createBatch${TimeStamp}.log"
        createBatch_ComlogTmp="${logdir}/comlogs/tmp_createBatch_${CASE}_${TimeStamp}.log"; touch ${createBatch_ComlogTmp}; chmod 777 ${createBatch_ComlogTmp}
        createBatch_ComlogError="${logdir}/comlogs/error_createBatch_${CASE}_${TimeStamp}.log"
        createBatch_ComlogDone="${logdir}/comlogs/done_createBatch_${CASE}_${TimeStamp}.log"
        ExecuteCall="${QUNEXCOMMAND} createBatch --subjectsfolder='${qunex_subjectsfolder}' --tfile='${ProcessingBatchFile}' --paramfile='${SpecsBatchFileHeader}' --sessions='${CASE}' --overwrite='yes'"
        echo ""; echo " -- Executed call:"; echo "   $ExecuteCall"; echo ""
        eval ${ExecuteCall} 2>&1 | tee -a ${createBatch_ComlogTmp}
        if [[ ! -z `cat ${createBatch_ComlogTmp} | grep 'Successful completion'` ]]; then createBatchCheck="pass"; else createBatchCheck="fail"; fi
        if [[ ${createBatchCheck} == "pass" ]]; then
            mv ${createBatch_ComlogTmp} ${createBatch_ComlogDone}
            createBatch_Comlog=${createBatch_ComlogDone}
        else
           mv ${createBatch_ComlogTmp} ${createBatch_ComlogError}
           createBatch_Comlog=${createBatch_ComlogError}
        fi
        # ------------------------------
    }

    #
    # --------------- Intial study and file organization end -------------------
    
    # --> FINISH adding rawNII checks here and integrate w/runQC function
    runQC_Finalize() {
        runQCComLog=`ls -t1 ${logdir}/comlogs/*_runQC_${CASE}_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
        runQCRunLog=`ls -t1 ${logdir}/runlogs/Log-runQC_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
        rename runQC runQC_${QCLogName} ${logdir}/comlogs/${runQCComLog} 2> /dev/null
        rename runQC runQC_${QCLogName} ${logdir}/runlogs/${runQCRunLog} 2> /dev/null
        mkdir -p ${qunex_subjectsfolder}/${CASE}/logs/comlog 2> /dev/null
        mkdir -p ${qunex_subjectsfolder}/${CASE}/logs/runlog 2> /dev/null
        mkdir -p ${qunex_subjectsfolder}/${CASE}/QC/${Modality} 2> /dev/null
        cp ${logdir}/comlogs/${runQCComLog} ${qunex_subjectsfolder}/${CASE}/logs/comlog/ 2> /dev/null
        cp ${logdir}/comlogs/${runQCRunLog} ${qunex_subjectsfolder}/${CASE}/logs/comlog/ 2> /dev/null
        cp ${qunex_subjectsfolder}/subjects/QC/${Modality}/*${CASE}*scene ${qunex_subjectsfolder}/${CASE}/QC/${Modality}/ 2> /dev/null
        cp ${qunex_subjectsfolder}/subjects/QC/${Modality}/*${CASE}*zip ${qunex_subjectsfolder}/${CASE}/QC/${Modality}/ 2> /dev/null
    }

    # -- runQC_rawNII (after organizing DICOM files)
    turnkey_runQC_rawNII() {
        Modality="rawNII"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: runQC step for ${Modality} data ... "; echo ""
        ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --modality="${Modality}"
        QCLogName="rawNII"
        runQC_Finalize
    }
    
    # --------------- HCP Processing and relevant QC start ---------------------
    #
    # -- PreFreeSurfer
    turnkey_hcp1() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp1 (hcp_PreFS) ... "; echo ""
        ${QUNEXCOMMAND} hcp1 --subjectsfolder="${qunex_subjectsfolder}" --sessions="${ProcessingBatchFile}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --subjid="${SUBJID}"
    }
    # -- FreeSurfer
    turnkey_hcp2() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp2 (hcp_FS) ... "; echo ""
        ${QUNEXCOMMAND} hcp2 --subjectsfolder="${qunex_subjectsfolder}" --sessions="${ProcessingBatchFile}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --subjid="${SUBJID}"
        CleanupFiles=" talairach_with_skull.log lh.white.deformed.out lh.pial.deformed.out rh.white.deformed.out rh.pial.deformed.out"
        for CleanupFile in ${CleanupFiles}; do 
            cp ${logdir}/${CleanupFile} ${qunex_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/${CASE}/scripts/ 2>/dev/null
            rm -rf ${logdir}/${CleanupFile}
        done
        rm -rf ${qunex_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/fsaverage 2>/dev/null
        rm -rf ${qunex_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/rh.EC_average 2>/dev/null
        rm -rf ${qunex_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/lh.EC_average 2>/dev/null
        cp -r $FREESURFER_HOME/subjects/lh.EC_average ${qunex_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/ 2>/dev/null
        cp -r $FREESURFER_HOME/subjects/fsaverage ${qunex_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/ 2>/dev/null
        cp -r $FREESURFER_HOME/subjects/rh.EC_average ${qunex_subjectsfolder}/${CASE}/hcp/${CASE}/T1w/ 2>/dev/null
    }
    # -- PostFreeSurfer
    turnkey_hcp3() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp3 (hcp_PostFS) ... "; echo ""
        ${QUNEXCOMMAND} hcp3 --subjectsfolder="${qunex_subjectsfolder}" --sessions="${ProcessingBatchFile}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --subjid="${SUBJID}"
    }
    # -- runQC_T1w (after hcp3)
    turnkey_runQC_T1w() {
        Modality="T1w"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: runQC step for ${Modality} data ... "; echo ""
        ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --outpath="${qunex_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --hcp_suffix="${HCPSuffix}"
        QCLogName="T1w"
        runQC_Finalize
    }
    # -- runQC_T2w (after hcp3)
    turnkey_runQC_T2w() {
        Modality="T2w"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: runQC step for ${Modality} data ... "; echo ""
        ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --outpath="${qunex_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --hcp_suffix="${HCPSuffix}"
        QCLogName="T2w"
        runQC_Finalize
    }
    # -- runQC_Myelin (after hcp3)
    turnkey_runQC_Myelin() {
        Modality="myelin"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: runQC step for ${Modality} data ... "; echo ""
        ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --outpath="${qunex_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --hcp_suffix="${HCPSuffix}"
        QCLogName="Myelin"
        runQC_Finalize
    }
    # -- fMRIVolume
    turnkey_hcp4() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp4 (hcp_fMRIVolume) ... "; echo ""
        HCPLogName="hcpfMRIVolume"
        ${QUNEXCOMMAND} hcp4 --subjectsfolder="${qunex_subjectsfolder}" --sessions="${ProcessingBatchFile}" --overwrite="${OVERWRITE_STEP}" --subjid="${SUBJID}"
    }
    # -- fMRISurface
    turnkey_hcp5() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcp5 (hcp_fMRISurface) ... "; echo ""
        HCPLogName="hcpfMRISurface"
        ${QUNEXCOMMAND} hcp5 --subjectsfolder="${qunex_subjectsfolder}" --sessions="${ProcessingBatchFile}" --overwrite="${OVERWRITE_STEP}" --subjid="${SUBJID}"
    }
    # -- runQC_BOLD (after hcp5)
    turnkey_runQC_BOLD() {
        Modality="BOLD"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: runQC step for ${Modality} data ... BOLDS: ${BOLDRUNS} "; echo ""
        if [ -z "${BOLDfc}" ]; then
            # if [ -z "${BOLDPrefix}" ]; then BOLDPrefix="bold"; fi   --- default for bold prefix is now ""
            if [ -z "${BOLDSuffix}" ]; then BOLDSuffix="Atlas"; fi
        fi
        # if [ -z "${BOLDRUNS}" ]; then
        #      BOLDRUNS=`ls ${qunex_subjectsfolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/ | awk {'print $1'} 2> /dev/null`
        # fi
        
        # -- Code for selecting BOLDS via Tags --> Check if both batch and bolds are specified for QC and if yes read batch explicitly
        getBoldList
        
        # -- Loop through BOLD runs
        for BOLDRUN in ${LBOLDRUNS}; do
            ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --outpath="${qunex_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --boldprefix="${BOLDPrefix}" --boldsuffix="${BOLDSuffix}" --bolds="${BOLDRUN}" --hcp_suffix="${HCPSuffix}"
            runQCComLog=`ls -t1 ${logdir}/comlogs/*_runQC_${CASE}_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
            runQCRunLog=`ls -t1 ${logdir}/runlogs/Log-runQC_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
            rename runQC runQC_BOLD${BOLD} ${logdir}/comlogs/${runQCComLog}
            rename runQC runQC_BOLD${BOLD} ${logdir}/runlogs/${runQCRunLog} 2> /dev/null
        done
    }
    # -- Diffusion HCP (after hcp1)
    turnkey_hcpd() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step: hcpd (hcp_Diffusion) ..."; echo ""
        ${QUNEXCOMMAND} hcpd --subjectsfolder="${qunex_subjectsfolder}" --subjects="${ProcessingBatchFile}" --overwrite="${OVERWRITE_STEP}" --subjid="${SUBJID}"
    }
    # -- Diffusion Legacy (after hcp1)
    turnkey_hcpdLegacy() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: HCP Pipelines step hcpdLegacy ..."; echo ""
        ${QUNEXCOMMAND} hcpdLegacy --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --scanner="${Scanner}" --usefieldmap="${UseFieldmap}" --echospacing="${EchoSpacing}" --PEdir="{PEdir}" --unwarpdir="${UnwarpDir}" --diffdatasuffix="${DiffDataSuffix}" --TE="${TE}"
    }
    # -- runQC_DWILegacy (after hcpd)
    turnkey_runQC_DWILegacy() {
        Modality="DWI"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: runQC step for ${Modality} legacy data ... "; echo ""
        ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --outpath="${qunex_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --dwidata="data" --dwipath="Diffusion" --dwilegacy="${DWILegacy}" --hcp_suffix="${HCPSuffix}"
        QCLogName="DWILegacy"
        runQC_Finalize
    }
    # -- runQC_DWI (after hcpd)
    turnkey_runQC_DWI() {
        Modality="DWI"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: runQC steps for ${Modality} HCP processing ... "; echo ""
        ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --outpath="${qunex_subjectsfolder}/QC/DWI" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --dwidata="data" --dwipath="Diffusion" --logfolder="${logdir}" --hcp_suffix="${HCPSuffix}"
        QCLogName="DWI"
        runQC_Finalize
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
        ${QUNEXCOMMAND} eddyQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --eddybase="${EddyBase}" --eddypath="${EddyPath}" --report="${Report}" --bvalsfile="${BvalsFile}" --mask="${Mask}" --eddyidx="${EddyIdx}" --eddyparams="${EddyParams}" --bvecsfile="${BvecsFile}" --overwrite="${OVERWRITE_STEP}"
    }
    # -- runQC_DWIeddyQC (after eddyQC)
    turnkey_runQC_DWIeddyQC() {
        Modality="DWI"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: runQC steps for ${Modality} eddyQC ... "; echo ""
        ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --outpath="${qunex_subjectsfolder}/QC/DWI" -modality="${Modality}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --eddyqcstats="yes" --hcp_suffix="${HCPSuffix}"
        QCLogName="DWIeddyQC"
        runQC_Finalize
    }
    #
    # --------------- HCP Processing and relevant QC end -----------------------

    # --------------- DWI additional analyses start ------------------------
    #
    # -- FSLDtifit (after hcpd or hcpdLegacy)
    turnkey_FSLDtifit() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: : FSLDtifit for DWI... "; echo ""
        ${QUNEXCOMMAND} FSLDtifit --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}"
    }
    # -- FSLBedpostxGPU (after FSLDtifit)
    turnkey_FSLBedpostxGPU() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: FSLBedpostxGPU for DWI ... "
        if [ -z "$Fibers" ]; then Fibers="3"; fi
        if [ -z "$Model" ]; then Model="3"; fi
        if [ -z "$Burnin" ]; then Burnin="3000"; fi
        if [ -z "$Rician" ]; then Rician="yes"; fi
        ${QUNEXCOMMAND} FSLBedpostxGPU --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --fibers="${Fibers}" --burnin="${Burnin}" --model="${Model}" --rician="${Rician}"
    }
    # -- runQC_DWIDTIFIT (after FSLDtifit)
    turnkey_runQC_DWIDTIFIT() {
        Modality="DWI"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: runQC steps for ${Modality} FSL's dtifit analyses ... "; echo ""
        ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --outpath="${qunex_subjectsfolder}/QC/DWI" --modality="${Modality}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --dtifitqc="yes" --hcp_suffix="${HCPSuffix}"
        QCLogName="DWIDTIFIT" 
        runQC_Finalize
    }
    # -- runQC_DWIBedpostX (after FSLBedpostxGPU)
    turnkey_runQC_DWIBedpostX() {
        Modality="DWI"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: runQC steps for ${Modality} FSL's BedpostX analyses ... "; echo ""
        ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --outpath="${qunex_subjectsfolder}/QC/DWI" --modality="${Modality}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --bedpostxqc="yes" --hcp_suffix="${HCPSuffix}"
        QCLogName="DWIBedpostX" 
        runQC_Finalize
    }
    # -- probtrackxGPUDense for DWI data (after FSLBedpostxGPU)
    turnkey_probtrackxGPUDense() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: probtrackxGPUDense ... "; echo ""
        ${QUNEXCOMMAND} probtrackxGPUDense --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --omatrix1="yes" --omatrix3="yes"
    }
    # -- pretractographyDense for DWI data (after FSLBedpostxGPU)
    turnkey_pretractographyDense() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: pretractographyDense ... "; echo ""
        ${QUNEXCOMMAND} pretractographyDense --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --omatrix1="yes" --omatrix3="yes"
    }
    # -- DWIDenseParcellationfor DWI data (after pretractographyDense)
    turnkey_DWIDenseParcellation() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: DWIDenseParcellation ... "; echo ""
        # Defaults if not specified:
        if [ -z "$WayTotal" ]; then WayTotal="standard"; fi
        if [ -z "$MatrixVersion" ]; then MatrixVersions="1"; fi
        # Cole-Anticevic Brain-wide Network Partition version 1.0 (CAB-NP v1.0)
        if [ -z "$ParcellationFile" ]; then ParcellationFile="${TOOLS}/${QUNEXREPO}/library/data/parcellations/ColeAnticevicNetPartition/CortexSubcortex_ColeAnticevic_NetPartition_wSubcorGSR_parcels_LR.dlabel.nii"; fi
        if [ -z "$DWIOutName" ]; then DWIOutName="DWI-CAB-NP-v1.0"; fi
        for MatrixVersion in $MatrixVersions; do
            ${QUNEXCOMMAND} DWIDenseParcellation --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --waytotal="${WayTotal}" --matrixversion="${MatrixVersion}" --parcellationfile="${ParcellationFile}" --outname="${DWIOutName}"
        done
    }
    # -- DWISeedTractography for DWI data (after pretractographyDense)
    turnkey_DWISeedTractography() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: DWISeedTractography ... "; echo "" 
        if [ -z "$MatrixVersion" ]; then MatrixVersions="1"; fi
        if [ -z "$WayTotal" ]; then WayTotal="standard"; fi
        if [ -z "$SeedFile" ]; then
            # Thalamus SomatomotorSensory
            SeedFile="${TOOLS}/${QUNEXREPO}/library/data/atlases/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-SomatomotorSensory.symmetrical.intersectionLR.nii" 
            OutName="DWI_THALAMUS_FSL_LR_SomatomotorSensory_Symmetrical_intersectionLR"
            ${QUNEXCOMMAND} DWISeedTractography --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --matrixversion="${MatrixVersion}" --waytotal="${WayTotal}" --outname="${OutName}" --seedfile="${SeedFile}"
            # Thalamus Prefrontal
            SeedFile="${TOOLS}/${QUNEXREPO}/library/data/atlases/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Prefrontal.symmetrical.intersectionLR.nii" 
            OutName="DWI_THALAMUS_FSL_LR_Prefrontal"
            ${QUNEXCOMMAND} DWISeedTractography --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --matrixversion="${MatrixVersion}" --waytotal="${WayTotal}" --outname="${OutName}" --seedfile="${SeedFile}"
        fi
        OutNameGBC="DWI_GBC"
        ${QUNEXCOMMAND} DWISeedTractography --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --overwrite="${OVERWRITE_STEP}" --matrixversion="${MatrixVersion}" --waytotal="${WayTotal}" --outname="${OutNameGBC}" --seedfile="gbc"
    }
    #
    # --------------- DWI Processing and analyses end --------------------------


    # --------------- Custom QC start ------------------------------------------
    # 
    # -- Check if Custom QC was requested
    turnkey_runQC_Custom() {
        unset RunCommand
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: runQC_Custom ... "; echo ""
        
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
                # if [ -z "${BOLDRUNS}" ]; then
                #      BOLDRUNS=`ls ${qunex_subjectsfolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/ | awk {'print $1'} 2> /dev/null`
                #      geho " --> BOLDs not explicitly requested. Will run all available data: ${BOLDRUNS} "
                # fi

                getBoldList

                echo "====> Looping through these BOLDRUNS: ${LBOLDRUNS}"
                for BOLDRUN in ${LBOLDRUNS}; do
                    echo "----> Now working on BOLDRUN: ${BOLDRUN}"
                    ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --outpath="${qunex_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --boldprefix="${BOLDPrefix}" --boldsuffix="${BOLDSuffix}" --bolddata="${BOLDRUN}" --customqc='yes' --omitdefaults='yes' --hcp_suffix="${HCPSuffix}"
                    runQCComLog=`ls -t1 ${logdir}/comlogs/*_runQC_${CASE}_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
                    runQCRunLog=`ls -t1 ${logdir}/runlogs/Log-runQC_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
                    rename runQC runQC_CustomBOLD${BOLD} ${logdir}/comlogs/${runQCComLog}
                    rename runQC runQC_CustomBOLD${BOLD} ${logdir}/runlogs/${runQCRunLog} 2> /dev/null
                done
            elif [[ ${Modality} == "DWI" ]]; then
                ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --outpath="${qunex_subjectsfolder}/QC/${Modality}" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --dwilegacy="${DWILegacy}" --dwidata="data" --dwipath="Diffusion" --customqc="yes" --omitdefaults="yes" --hcp_suffix="${HCPSuffix}"
                QCLogName="Custom${Modality}"
                runQC_Finalize
            else
                ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --outpath="${qunex_subjectsfolder}/QC/${Modality}" --modality="${Modality}"  --overwrite="${OVERWRITE_STEP}" --customqc="yes" --omitdefaults="yes" --hcp_suffix="${HCPSuffix}"
                QCLogName="Custom${Modality}"
                if [[ ${Modality} == "myelin" ]]; then QCLogName="CustomMyelin"; fi
                runQC_Finalize
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
        mkdir -p ${qunex_subjectsfolder}/${CASE}/logs/comlog 2> /dev/null
        mkdir -p ${qunex_subjectsfolder}/${CASE}/logs/runlog 2> /dev/null
        cp ${CheckComLog} ${qunex_subjectsfolder}/${CASE}/logs/comlog 2> /dev/null
        cp ${CheckRunLog} ${qunex_subjectsfolder}/${CASE}/logs/runlog 2> /dev/null
           
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
        ${QUNEXCOMMAND} mapHCPData \
        --sessions="${ProcessingBatchFile}" \
        --subjectsfolder="${qunex_subjectsfolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${logdir}" \
        --subjid="${SUBJID}"
    }
    # -- Generate brain masks for de-noising
    turnkey_createBOLDBrainMasks() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: createBOLDBrainMasks ... "; echo ""
        ${QUNEXCOMMAND} createBOLDBrainMasks \
        --sessions="${ProcessingBatchFile}" \
        --subjectsfolder="${qunex_subjectsfolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${logdir}" \
        --subjid="${SUBJID}"
    }
    # -- Compute BOLD statistics
    turnkey_computeBOLDStats() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: computeBOLDStats ... "; echo ""
        ${QUNEXCOMMAND} computeBOLDStats \
        --sessions="${ProcessingBatchFile}" \
        --subjectsfolder="${qunex_subjectsfolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${logdir}" \
        --subjid="${SUBJID}"
    }
    # -- Create final BOLD statistics report
    turnkey_createStatsReport() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: createStatsReport ... "; echo ""
        ${QUNEXCOMMAND} createStatsReport \
        --sessions="${ProcessingBatchFile}" \
        --subjectsfolder="${qunex_subjectsfolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${logdir}" \
        --subjid="${SUBJID}"
    }
    # -- Extract nuisance signal for further de-noising
    turnkey_extractNuisanceSignal() {
        cyaneho " ===> RunTurnkey ~~~ RUNNING: extractNuisanceSignal ... "; echo ""
        ${QUNEXCOMMAND} extractNuisanceSignal \
        --sessions="${ProcessingBatchFile}" \
        --subjectsfolder="${qunex_subjectsfolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${logdir}" \
        --subjid="${SUBJID}"
    }
    # -- Process BOLDs
    turnkey_preprocessBold() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: preprocessBold ... "; echo ""
        ${QUNEXCOMMAND} preprocessBold \
        --sessions="${ProcessingBatchFile}" \
        --subjectsfolder="${qunex_subjectsfolder}" \
        --overwrite="${OVERWRITE_STEP}" \
        --logfolder="${logdir}" \
        --subjid="${SUBJID}"
    }
    # -- Process via CONC file
    turnkey_preprocessConc() {
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: preprocessConc ... "; echo ""
        ${QUNEXCOMMAND} preprocessConc \
        --sessions="${ProcessingBatchFile}" \
        --subjectsfolder="${qunex_subjectsfolder}" \
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
              QCPlotMasks="${qunex_subjectsfolder}/${CASE}/images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz"
        fi
        if [ -z ${images_folder} ]; then
            images_folder="${qunex_subjectsfolder}/$CASE/images/functional"
        fi
        if [ -z ${output_folder} ]; then
            output_folder="${qunex_subjectsfolder}/$CASE/images/functional/movement"
        fi
        if [ -z ${output_name} ]; then
            output_name="${CASE}_BOLD_GreyPlot_CIFTI.pdf"
        fi
        #if [ -z ${BOLDRUNS} ]; then
        #    BOLDRUNS="1"
        #fi

        getBoldList

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
        for BOLDRUN in ${LBOLDRUNS}; do 
           cd ${images_folder} 
           if [ -z ${QCPlotImages} ]; then
               QCPlotImages="bold${BOLDRUN}.nii.gz;bold${BOLDRUN}_Atlas_g7_hpss_res-mVWMWB_lpss.dtseries.nii"
           fi
           echo "   QC Plot images: ${QCPlotImages}" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
           echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
           echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
           echo " -- Command: " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
           echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
           echo "${QUNEXCOMMAND} g_PlotBoldTS --images="${QCPlotImages}" --elements="${QCPlotElements}" --masks="${QCPlotMasks}" --filename="${output_folder}/${output_name}" --skip="0" --subjid="${CASE}" --verbose="true"" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
           echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
           
           ${QUNEXCOMMAND} g_PlotBoldTS --images="${QCPlotImages}" --elements="${QCPlotElements}" --masks="${QCPlotMasks}" --filename="${output_folder}/${output_name}" --skip="0" --subjid="${CASE}" --verbose="true"
           echo " -- Copying ${output_folder}/${output_name} to ${qunex_subjectsfolder}/QC/BOLD/" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
           echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
           cp ${output_folder}/${output_name} ${qunex_subjectsfolder}/QC/BOLD/
           if [[ -f ${qunex_subjectsfolder}/QC/BOLD/${output_name} ]]; then
               echo " -- Found ${qunex_subjectsfolder}/QC/BOLD/${output_name}" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
               echo "   " 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
               g_PlotBoldTS_Check="pass"
           else
               echo " -- Result ${qunex_subjectsfolder}/QC/BOLD/${output_name} missing!" 2>&1 | tee -a ${g_PlotBoldTS_ComlogTmp}
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
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: BOLDParcellation on BOLDS: ${BOLDRUNS} ... "; echo ""
        
        getBoldList

#        # -- Defaults if not specified:
#
#        local LBOLDRUNS="${BOLDRUNS}"
#
#        if [ -z "${LBOLDRUNS}" ]; then
#            LBOLDRUNS="1"
#        fi
#
#        BOLDS=`gmri batchTag2NameKey filename="${ProcessingBatchFile}" subjid="${CASE}" bolds="${LBOLDRUNS}" | grep "BOLDS:" | sed 's/BOLDS://g' | sed 's/,/ /g'`
#        LBOLDRUNS="${BOLDS}"
#
#        echo " ---> BOLDRUNS: ${LBOLDRUNS}"

        if [ -z ${RunParcellations} ]; then

            for BOLDRUN in ${LBOLDRUNS}; do
               if [ -z "$InputFile" ]; then InputFileParcellation="bold${BOLDRUN}_Atlas_g7_hpss_res-mVWMWB_lpss.dtseries.nii "; else InputFileParcellation="${InputFile}"; fi
               if [ -z "$UseWeights" ]; then UseWeights="yes"; fi
               if [ -z "$WeightsFile" ]; then UseWeights="images/functional/movement/bold${BOLDRUN}.use"; fi
               # -- Cole-Anticevic Brain-wide Network Partition version 1.0 (CAB-NP v1.0)
               if [ -z "$ParcellationFile" ]; then ParcellationFile="${TOOLS}/${QUNEXREPO}/library/data/parcellations/ColeAnticevicNetPartition/CortexSubcortex_ColeAnticevic_NetPartition_wSubcorGSR_parcels_LR.dlabel.nii"; fi
               if [ -z "$OutName" ]; then OutNameParcelation="BOLD-CAB-NP-v1.0"; else OutNameParcelation="${OutName}"; fi
               if [ -z "$InputDataType" ]; then InputDataType="dtseries"; fi
               if [ -z "$InputPath" ]; then InputPath="/images/functional/"; fi
               if [ -z "$OutPath" ]; then OutPath="/images/functional/"; fi
               if [ -z "$ComputePConn" ]; then ComputePConn="yes"; fi
               if [ -z "$ExtractData" ]; then ExtractData="yes"; fi
               # -- Command
               RunCommand="${QUNEXCOMMAND} BOLDParcellation --subjects='${CASE}' \
               --subjectsfolder='${qunex_subjectsfolder}' \
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

            echo ""; reho " ===> The following parcellations will be run: ${RunParcellations}"; echo ""

            for Parcellation in ${RunParcellations}; do
                if [ ${Parcellation} == "CANP" ]; then
                    ParcellationFile="${TOOLS}/${QUNEXREPO}/library/data/parcellations/ColeAnticevicNetPartition/CortexSubcortex_ColeAnticevic_NetPartition_wSubcorGSR_parcels_LR.dlabel.nii"
                    OutNameParcelation="BOLD-CAB-NP-v1.0"
                elif [ ${Parcellation} == "HCP" ]; then
                    ParcellationFile="${TOOLS}/${QUNEXREPO}/library/data/parcellations/GlasserParcellation/Q1-Q6_RelatedParcellation210.LR.CorticalAreas_dil_Colors.32k_fs_LR.dlabel.nii"
                    OutNameParcelation="HCP-210"
                elif [ ${Parcellation} == "YEO17" ]; then
                    ParcellationFile="${TOOLS}/${QUNEXREPO}/library/data/parcellations/RSN_Yeo_Buckner_Choi_Cortex_Cerebellum_Striatum/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_17networks_networks_MWfix.dlabel.nii"
                    OutNameParcelation="YEO17"
                elif [ ${Parcellation} == "YEO7" ]; then
                    ParcellationFile="${TOOLS}/${QUNEXREPO}/library/data/parcellations/RSN_Yeo_Buckner_Choi_Cortex_Cerebellum_Striatum/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_thalamus_7networks_networks_MWfix.dlabel.nii"
                    OutNameParcelation="YEO7"
                else
                    reho " ===> ERROR: ${Parcellation} not recognized as a valid parcellation name! Skipping";
                    continue
                fi

                echo ""; reho " ===> Now running parcellation ${Parcellation}"; echo ""

                for BOLDRUN in ${LBOLDRUNS}; do
                   if [ -z "$InputFile" ]; then InputFileParcellation="bold${BOLDRUN}_Atlas_g7_hpss_res-mVWMWB_lpss.dtseries.nii "; else InputFileParcellation="${InputFile}"; fi
                   if [ -z "$UseWeights" ]; then UseWeights="yes"; fi
                   if [ -z "$WeightsFile" ]; then UseWeights="images/functional/movement/bold${BOLDRUN}.use"; fi
                   if [ -z "$InputDataType" ]; then InputDataType="dtseries"; fi
                   if [ -z "$InputPath" ]; then InputPath="/images/functional/"; fi
                   if [ -z "$OutPath" ]; then OutPath="/images/functional/"; fi
                   if [ -z "$ComputePConn" ]; then ComputePConn="yes"; fi
                   if [ -z "$ExtractData" ]; then ExtractData="yes"; fi
                   # -- Command
                   RunCommand="${QUNEXCOMMAND} BOLDParcellation --subjects='${CASE}' \
                   --subjectsfolder='${qunex_subjectsfolder}' \
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
    turnkey_computeBOLDfcSeed() {
        FunctionName="computeBOLDfc"
        echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: computeBOLDfc processing steps for Seed FC ... "; echo ""
        if [ -z ${ROIInfo} ]; then
           ROINames="${TOOLS}/${QUNEXREPO}/library/data/roi/seeds_cifti.names ${TOOLS}/${QUNEXREPO}/library/data/atlases/Thalamus_Atlas/Thal.FSL.MNI152.CIFTI.Atlas.AllSurfaceZero.names"
        else
           ROINames=${ROIInfo}
        fi

        getBoldList

        for ROIInfo in ${ROINames}; do
            for BOLDRUN in ${LBOLDRUNS}; do
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
                RunCommand="${QUNEXCOMMAND} computeBOLDfc \
                --subjectsfolder='${qunex_subjectsfolder}' \
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

       getBoldList

       for BOLDRUN in ${LBOLDRUNS}; do
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
            RunCommand="${QUNEXCOMMAND} computeBOLDfc \
            --subjectsfolder='${qunex_subjectsfolder}' \
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
   # -- runQC_BOLD FC (after GBC/FC/PCONN)
   #turnkey_QCrun_BOLDfc
   turnkey_runQC_BOLDfc() {
        Modality="BOLD"
        # echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: runQC step for ${Modality} FC ... "; echo ""
        # if [ -z "${BOLDRUNS}" ]; then
        #      BOLDRUNS=`ls ${qunex_subjectsfolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/ | awk {'print $1'} 2> /dev/null`
        # fi

        getBoldList

        for BOLDRUN in ${LBOLDRUNS}; do
            ${QUNEXCOMMAND} runQC --subjectsfolder="${qunex_subjectsfolder}" --subjects="${CASE}" --outpath="${qunex_subjectsfolder}/QC/${Modality}" --modality="${Modality}" --overwrite="${OVERWRITE_STEP}" --logfolder="${logdir}" --boldprefix="${BOLDPrefix}" --boldsuffix="${BOLDSuffix}" --bolds="${BOLDRUN}" --boldfc="${BOLDfc}" --boldfcinput="${BOLDfcInput}" --boldfcpath="${BOLDfcPath}" --hcp_suffix="${HCPSuffix}"
            runQCComLog=`ls -t1 ${logdir}/comlogs/*_runQC_${CASE}_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
            runQCRunLog=`ls -t1 ${logdir}/runlogs/Log-runQC_*.log | head -1 | xargs -n 1 basename 2> /dev/null`
            rename runQC runQC_BOLDfc${BOLD} ${logdir}/comlogs/${runQCComLog}
            rename runQC runQC_BOLDfc${BOLD} ${logdir}/runlogs/${runQCRunLog} 2> /dev/null
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
                RunCommand="QuNexAcceptanceTest.sh \
                --studyfolder='${qunex_studyfolder}' \
                --subjectsfolder='${qunex_subjectsfolder}' \
                --subjects='${CASE}' \
                --runtype='local' \
                --acceptancetest='${UnitTest}'"
                echo " -- Command: ${RunCommand}"
                eval ${RunCommand}
            done
        else
            RunCommand="QuNexAcceptanceTest.sh \
            --studyfolder='${qunex_studyfolder}' \
            --subjectsfolder='${qunex_subjectsfolder}' \
            --subjects='${CASE}' \
            --runtype='local' \
            --acceptancetest='${UnitTest}'"
           echo " -- Command: ${RunCommand}"
           eval ${RunCommand}
        fi
        
       # -- XNAT Call -- not supported currently -->
       #
       #    RunCommand="QuNexAcceptanceTest.sh \
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
        # -- Currently supporting hcp4 but this can be exanded
        if [[ "$TURNKEY_STEP" == "hcp4" ]]; then
            echo ""; cyaneho " ===> RunTurnkey ~~~ RUNNING: QuNexClean Function for $TURNKEY_STEP ... "; echo ""
            rm -rf ${qunex_subjectsfolder}/${CASE}/hcp/${CASE}/[0-9]* &> /dev/null
        fi
    }
    #
    # --------------- QuNexTurnkeyCleanFunction end ----------------

#
# =-=-=-=-=-=-= TURNKEY COMMANDS END =-=-=-=-=-=-=


# =-=-=-=-=-=-= RUN SPECIFIC COMMANDS START =-=-=-=-=-=-=

if [ -z "$TURNKEY_STEPS" ] && [ ! -z "$AcceptanceTest" ] && [ "$AcceptanceTest" != "yes" ]; then
    echo ""; 
    geho "  ---------------------------------------------------------------------"
    echo ""
    geho "   ===> Performing completion check on specific Qu|Nex turnkey units: ${AcceptanceTest}"
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
        geho "   ===> Executing all Qu|Nex turkey workflow steps: ${QuNexTurnkeyWorkflow}"
        echo ""
        geho "  ---------------------------------------------------------------------"
        echo ""
        TURNKEY_STEPS=${QuNexTurnkeyWorkflow}
    fi
    if [ "$TURNKEY_STEPS" != "all" ]; then
        echo ""; 
        geho "  ---------------------------------------------------------------------"
        echo ""
        geho "   ===> Executing specific Qu|Nex turkey workflow steps: ${TURNKEY_STEPS}"
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
        mkdir -p ${qunex_subjectsfolder}/${CASE}/logs/comlog 2> /dev/null
        mkdir -p ${qunex_subjectsfolder}/${CASE}/logs/runlog 2> /dev/null
        cp ${CheckComLog} ${qunex_subjectsfolder}/${CASE}/logs/comlog 2> /dev/null
        cp ${CheckRunLog} ${qunex_subjectsfolder}/${CASE}/logs/runlog 2> /dev/null
        
        Modalities="T1w T2w myelin BOLD DWI"
        for Modality in ${Modalities}; do
            mkdir -p ${qunex_subjectsfolder}/${CASE}/QC/${Modality} 2> /dev/null
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
        
        # -- Run acceptance tests for specific Qu|Nex units
        if [[ AcceptanceTest == "yes" ]]; then
            UnitTest="${TURNKEY_STEP}"
            RunAcceptanceTestFunction
        fi
        
        # -- Run Qu|Nex cleaning for specific unit
        #    Currently supporting hcp4
        if [[ ${TURNKEY_CLEAN} == "yes" ]]; then
           if [[ "${TURNKEY_STEP}" == "hcp4" ]]; then
               if [[ "${TURNKEY_STEP_ERRORS}" == "no" ]]; then
                   QuNexTurnkeyCleanFunction
               else
                   echo ""; reho " ===> ERROR: ${TURNKEY_STEP} step did not complete. Skipping cleaning for debugging purposes."; echo ""
               fi
           fi
        fi
    done
    
    if [ ${TURNKEY_TYPE} == "xnat" ]; then
        geho "---> Setting recursive r+w+x permissions on ${qunex_studyfolder}"
        chmod -R 777 ${qunex_studyfolder} 2> /dev/null
        cd ${processingdir}
        zip -r logs logs 2> /dev/null
        echo ""
        geho "---> Uploading all logs: curl -u XNAT_USER_NAME:XNAT_PASSWORD -X POST "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_ACCSESSION_ID}/resources/QUNEX_LOGS/files/logs.zip?extract=true&overwrite=true&inbody=true" -d logs.zip "
        echo ""
        curl -u ${XNAT_USER_NAME}:${XNAT_PASSWORD} -X POST "${XNAT_HOST_NAME}/data/archive/projects/${XNAT_PROJECT_ID}/subjects/${XNAT_SUBJECT_LABEL}/experiments/${XNAT_ACCSESSION_ID}/resources/QUNEX_LOGS/files/logs.zip?extract=true&overwrite=true&inbody=true" -d logs.zip
        echo ""
        rm -rf ${processingdir}/logs.zip &> /dev/null
        popd 2> /dev/null
        geho "---> Cleaning up:"
        if [[ ${BIDSFormat} != "yes" ]]; then
            echo ""
            geho "     - removing dicom folder"
            rm -rf ${qunex_workdir}/dicom &> /dev/null
            echo ""
        fi
        geho "     - removing stray xml catalog files"
        find ${qunex_studyfolder} -name *catalog.xml -exec echo "       -> {}" \; -exec rm {} \; 2> /dev/null

        if [[ ${CleanupOldFiles} == "yes" ]]; then 
            geho "     - removing files older than run"
            find ${qunex_studyfolder} ! -newer ${workdir}/_startfile -exec echo "       -> {}" \; -exec rm {} \; 2> /dev/null
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

main ${@}
