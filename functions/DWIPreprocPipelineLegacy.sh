#!/bin/bash
#set -x
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# # DiffPreprocPipelineLegacy.sh
#
# ## Copyright Notice
#
# Copyright (C)
#
# * Yale University
# * Oxford University
#
# ## Author(s)
#
# * Alan Anticevic, N3 Division, Yale University
# * Stamatios Sotiropoulos, FMRIB Analysis Group, Oxford University
#
# ## Product
#
# DWI Processing pipeline adaptation for legacy data
#
# ## License
#
# * The DWI Legacy Preprocessing Pipeline = the "Software"
# * This Software is distributed "AS IS" without warranty of any kind, either 
# * expressed or implied, including, but not limited to, the implied warranties
# * of merchantability and fitness for a particular purpose.
#
# ### TODO
#
# Find out what actual license terms are to be applied. Commercial use allowed? 
# If so, this would likely violate FSL terms.
#
# ## Description 
#   
# This script, DiffPreprocPieplineLegacy.sh, implements the Diffusion MRI Preprocessing
# on legacy data that is not HCP compliant and cannot be used in TOPUP 
# It generates data that can be used as input to the fibre orientation estimation 
# scripts.
# 
# ## Prerequisite Installed Software
#
# * [FSL] - FMRIB's Software Library - Version 5.0.9 or later
# * Needs CUDA libraries to run eddy_cuda (10x faster than on a CPU)
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. $./DiffPreprocPipelineLegacy.sh --help

# Load Function Libraries
source ${HCPPIPEDIR}/global/scripts/log.shlib     # log_ functions
source ${HCPPIPEDIR}/global/scripts/version.shlib # version_ functions

usage() {
                echo ""
                echo "-- DESCRIPTION:"
                echo ""
                echo "This function runs the DWI preprocessing using the FUGUE method for legacy data that are not TOPUP compatible"
                echo "It explicitly assumes the the Human Connectome Project folder structure for preprocessing: "
                echo ""
                echo " <study_folder>/<case>/hcp/<case>/Diffusion ---> DWI data needs to be here"
                echo " <study_folder>/<case>/hcp/<case>/T1w       ---> T1w data needs to be here"
                echo ""
                echo "    Note: "
                echo "         - If PreFreeSurfer component of the HCP Pipelines was run the function will make use of the T1w data [Results will be better due to superior brain stripping]."
                echo "         - If PreFreeSurfer component of the HCP Pipelines was NOT run the function will start from raw T1w data [Results may be less optimal]."
                echo "         - If you are this function interactively you need to be on a GPU-enabled node or send it to a GPU-enabled queue."
                echo ""
                echo "-- REQUIRED PARMETERS:"
                echo ""
                echo "        --subjectsfolder=<study_folder>                        Path to study data folder"
                echo "        --subjects=<list_of_cases>                    List of subjects to run"
                echo "        --scanner=<scanner_manufacturer>            Name of scanner manufacturer (siemens or ge supported) "
                echo "        --echospacing=<echo_spacing_value>            EPI Echo Spacing for data [in msec]; e.g. 0.69"
                echo "        --PEdir=<phase_encoding_direction>            Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior"
                echo "        --unwarpdir=<epi_phase_unwarping_direction>    Direction for EPI image unwarping; e.g. x or x- for LR/RL, y or y- for AP/PA; may been to try out both -/+ combinations"
                echo "        --usefieldmap=<yes/no>                        Whether to use the standard field map. If set to <yes> then the following parameters become mandatory:"
                echo "        --diffdatasuffix=<diffusion_data_name>        Name of the DWI image; e.g. if the data is called <SubjectID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR"
                echo " "
                echo "-- OPTIONAL PARMETERS:"
                echo ""
                echo "        --overwrite=<clean_prior_run>        Delete prior run for a given subject"
                echo ""
                echo "        FIELDMAP-SPECFIC PARAMETERS (these become mandatory if --usefieldmap=yes):"
                echo ""
                echo "        --TE=<delta_te_value_for_fieldmap>        This is the echo time difference of the fieldmap sequence - find this out form the operator - defaults are *usually* 2.46ms on SIEMENS"
                echo ""
                echo ""
                echo "-- EXAMPLES using Siemens FieldMap (needs GPU-enabled node):"
                echo ""
                echo "   --> Run directly via ${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
                echo ""
                reho "           * NOTE: --scheduler is not available via direct script call."
                echo ""
                echo "   --> Run via mnap computeBOLDfc --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
                echo ""
                geho "           * NOTE: scheduler is available via mnap call:"
                echo "                   --scheduler=<name_of_cluster_scheduler_and_options>  A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
                echo ""
                echo "           * For SLURM scheduler the string would look like this via the mnap call: "
                echo "                   --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
                echo ""
                echo ""
                echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
                echo "--subjects='<comma_separarated_list_of_cases>' \ "
                echo "--function='hcpdLegacy' \ "
                echo "--PEdir='1' \ "
                echo "--echospacing='0.69' \ "
                echo "--TE='2.46' \ "
                echo "--unwarpdir='x-' \ "
                echo "--diffdatasuffix='DWI_dir91_LR' \ "
                echo "--usefieldmap='yes' \ "
                echo "--scanner='siemens' \ "
                echo "--overwrite='yes'"
                echo ""
                echo "-- Example with flagged parameters for submission to the scheduler using Siemens FieldMap [ needs GPU-enabled queue ]:"
                echo ""
                echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
                echo "--subjects='<comma_separarated_list_of_cases>' \ "
                echo "--function='hcpdLegacy' \ "
                echo "--PEdir='1' \ "
                echo "--echospacing='0.69' \ "
                echo "--TE='2.46' \ "
                echo "--unwarpdir='x-' \ "
                echo "--diffdatasuffix='DWI_dir91_LR' \ "
                echo "--scheduler='<name_of_scheduler_and_options>' \ "
                echo "--usefieldmap='yes' \ "
                echo "--scanner='siemens' \ "
                echo "--overwrite='yes' \ "
                echo ""
                echo "-- Example with flagged parameters for submission to the scheduler using GE data w/out FieldMap [ needs GPU-enabled queue ]:"
                echo ""
                echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
                echo "--subjects='<comma_separarated_list_of_cases>' \ "
                echo "--function='hcpdLegacy' \ "
                echo "--diffdatasuffix='DWI_dir91_LR' \ "
                echo "--scheduler='<name_of_scheduler_and_options>' \ "
                echo "--usefieldmap='no' \ "
                echo "--PEdir='1' \ "
                echo "--echospacing='0.69' \ "
                echo "--unwarpdir='x-' \ "
                echo "--scanner='ge' \ "
                echo "--overwrite='yes' \ "
                echo ""
exit 0
}

# ------------------------------------------------------------------------------
#  Setup color outputs
# ------------------------------------------------------------------------------

reho() {
    echo -e "\033[31m $1 \033[0m"
}

geho() {
    echo -e "\033[32m $1 \033[0m"
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]]; then
	usage
fi

########################################## INPUTS ########################################## 

# DWI Data and T1w data needed in HCP-style format to perform legacy DWI preprocessing
# The data should be in $DiffFolder="$SubjectsFolder"/"$CASE"/hcp/"$CASE"/Diffusion
# Also assumes that hcp1 (PreFreeSurfeer) T1 preprocessing has been carried out with results in "$SubjectsFolder"/"$CASE"/hcp/"$CASE"/T1w
# Mandatory input parameters:

    # SubjectsFolder
    # Subject
    # Scanner
    # UseFieldmap
    
# -- Optional input parameters:
    
    # PEdir
    # EchoSpacing
    # TE
    # UnwarpDir
    # DiffDataSuffix
    # Overwrite

########################################## OUTPUTS #########################################

# DiffFolder=${SubjectsFolder}/${Subject}/Diffusion
# T1wDiffFolder=${SubjectsFolder}/${Subject}/T1w/Diffusion_"$DiffDataSuffix"
#
#    $DiffFolder/$DiffDataSuffix/rawdata
#    $DiffFolder/$DiffDataSuffix/eddy
#    $DiffFolder/$DiffDataSuffix/data
#    $DiffFolder/$DiffDataSuffix/reg
#    $DiffFolder/$DiffDataSuffix/logs
#    $T1wDiffFolder

# -- Get the command line options for this script

get_options() {
    local scriptName=$(basename ${0})
    local arguments=($@)
    
    # -- initialize global output variables
    unset SubjectsFolder
    unset Subject
    unset PEdir
    unset EchoSpacing
    unset TE
    unset UnwarpDir
    unset DiffDataSuffix
    unset Overwrite
    unset Scanner
    unset UseFieldmap
    runcmd=""
    # -- parse arguments
    local index=0
    local numArgs=${#arguments[@]}
    local argument
    while [ ${index} -lt ${numArgs} ]; do
        argument=${arguments[index]}

        case ${argument} in
            --help)
                usage
                exit 1
                ;;
            --version)
                version_show $@
                exit 0
                ;;
            --subjectsfolder=*)
                SubjectsFolder=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --subject=*)
                CASE=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --PEdir=*)
                PEdir=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --echospacing=*)
                EchoSpacing=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --TE=*)
                TE=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --unwarpdir=*)
                UnwarpDir=${argument/*=/""}
                index=$(( index + 1 ))
                ;;  
            --diffdatasuffix=*)
                DiffDataSuffix=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --overwrite=*)
                Overwrite=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
             --scanner=*)
                Scanner=${argument/*=/""}
                index=$(( index + 1 ))
                ;;    
            --usefieldmap=*)
                UseFieldmap=${argument/*=/""}
                index=$(( index + 1 ))
                ;;        
            *)
                usage
                echo "ERROR: Unrecognized Option: ${argument}"
                exit 1
                ;;
        esac
    done
    # -- check required parameters
    if [ -z ${SubjectsFolder} ]; then
        usage
        echo "ERROR: <study-path> not specified"
        exit 1
    fi
    if [ -z ${CASE} ]; then
        usage
        echo "ERROR: <subject-id> not specified"
        exit 1
    fi
    if [ -z ${Scanner} ]; then
        echo "Note: <scanner> specification not set"
        exit 1
    fi
    if [ -z ${PEdir} ]; then
        usage
        echo "ERROR: <phase-encoding-dir> not specified"
        exit 1
    fi
    if [ -z ${EchoSpacing} ]; then
        usage
        echo "ERROR: <echo-spacing> not specified"
        exit 1
    fi
    if [ -z ${UnwarpDir} ]; then
        usage
        echo "ERROR: <unwarp-direction> not specified"
        exit 1
    fi
    if [ -z ${UseFieldmap} ]; then
        echo "Note: <fieldmap> specification not set"
        exit 1
    fi    
    if [ ${UseFieldmap} == "yes" ]; then
        if [ -z ${TE} ]; then
            usage
            echo "ERROR: <TE> not specified"
            exit 1
        fi
    fi
    if [ -z ${DiffDataSuffix} ]; then
        usage
        echo "ERROR: <diffusion-data-suffix> not specified"
        exit 1
    fi
    # -- report options
    echo ""
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo "   SubjectsFolder: ${SubjectsFolder}"
    echo "   Subject: ${CASE}"
    echo "   Scanner: ${Scanner}"
    if [ ${UseFieldmap} == "yes" ]; then
        echo "   Using Fieldmap: ${UseFieldmap}"
        echo "   PEdir: ${PEdir}"
        echo "   EchoSpacing: ${EchoSpacing}"
        echo "   TE: ${TE}"
        echo "   UnwarpDir: ${UnwarpDir}"
    else
        echo "   Using Fieldmap: ${UseFieldmap}"
    fi
    echo "   DiffData: ${CASE}_${DiffDataSuffix}.nii.gz"
    echo "   Overwrite: ${Overwrite}"
    echo "-- ${scriptName}: Specified Command-Line Options - End --"
    echo ""
    geho "------------------------- Start of work --------------------------------"
    echo ""
}

######################################### DO WORK ##########################################

main() {
    # -- Get Command Line Options
    get_options $@

##############################
# Setup folders and variables
#############################

# -- Parse all Parameters
EchoSpacing="$EchoSpacing" #EPI Echo Spacing for data (in msec); e.g. 0.69
PEdir="$PEdir" #Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior
TE="$TE" #delta TE in ms for field map or "NONE" if not used
UnwarpDir="$UnwarpDir" # direction along which to unwarp
DiffData="$CASE"_"$DiffDataSuffix" # Diffusion data suffix name - e.g. if the data is called <SubjectID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR
DwellTime="$EchoSpacing" #same variable as EchoSpacing - if you have in-plane acceleration then this value needs to be divided by the GRAPPA or SENSE factor (miliseconds)
DwellTimeSec=`echo "scale=6; $DwellTime/1000" | bc` # set the dwell time to seconds

# -- Establish global directory paths
reho "--- Establishing paths for all input and output folders:"
echo ""

T1wFolder="$SubjectsFolder"/"$CASE"/hcp/"$CASE"/T1w
DiffFolder="$SubjectsFolder"/"$CASE"/hcp/"$CASE"/Diffusion
T1wDiffFolder="$SubjectsFolder"/"$CASE"/hcp/"$CASE"/T1w/T1wDiffusion_"$DiffDataSuffix"
FieldMapFolder="$SubjectsFolder"/"$CASE"/hcp/"$CASE"/FieldMap_strc
LogFolder="$SubjectsFolder"/"$CASE"/hcp/"$CASE"/Diffusion/"$DiffDataSuffix"/log
DiffFolderOut="$SubjectsFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion_"$DiffDataSuffix"

echo "T1Folder:         $T1wFolder"
echo "DiffFolder:       $DiffFolder"
echo "T1wDiffFolder:    $T1wDiffFolder"
echo "FieldMapFolder:   $FieldMapFolder"
echo "LogFolder:        $LogFolder"
echo ""

# -- Delete any existing output sub-directories        
if [ "$Overwrite" == "yes" ]; then
    reho "--- Deleting prior runs for $DiffData..."
    echo ""
    rm -rf "$DiffFolder"/"$DiffDataSuffix"/rawdata/"$DiffData"* > /dev/null 2>&1
    rm -rf "$DiffFolder"/"$DiffDataSuffix"/eddy/"$DiffData"* > /dev/null 2>&1
    rm -rf "$DiffFolder"/"$DiffDataSuffix"/reg/"$DiffData"* > /dev/null 2>&1
    rm -rf "$DiffFolder"/"$DiffDataSuffix"/fieldmap > /dev/null 2>&1
    rm -rf "$DiffFolder"/"$DiffDataSuffix"/acqparams/"$DiffData" > /dev/null 2>&1
    rm -rf "$DiffFolderOut"/"$DiffData"* > /dev/null 2>&1
    rm -rf "$T1wDiffFolder"/*"$DiffDataSuffix"* > /dev/null 2>&1
fi

# -- Make sure output directories exist
mkdir -p "$DiffFolder" > /dev/null 2>&1
mkdir -p "$DiffFolder"/"$DiffDataSuffix" /dev/null 2>&1
mkdir -p "$T1wDiffFolder" > /dev/null 2>&1
mkdir -p "$LogFolder" > /dev/null 2>&1
mkdir -p "$DiffFolderOut" > /dev/null 2>&1
mkdir -p "$DiffFolder"/"$DiffDataSuffix"/rawdata > /dev/null 2>&1
mkdir -p "$DiffFolder"/"$DiffDataSuffix"/eddy > /dev/null 2>&1
mkdir -p "$DiffFolder"/"$DiffDataSuffix"/reg > /dev/null 2>&1
mkdir -p "$DiffFolder"/"$DiffDataSuffix"/fieldmap > /dev/null 2>&1
mkdir -p "$DiffFolder"/"$DiffDataSuffix"/acqparams > /dev/null 2>&1

#########################################
# STEP 1 - setup acquisition parameters
#########################################

reho "--- Setting up acquisition parameters:"
echo ""
# -- Make subject-specific and acquisition-specific parameter folder
mkdir "$DiffFolder"/"$DiffDataSuffix"/acqparams/"$DiffData" > /dev/null 2>&1
# -- Create index file - parameter file for number of frames in the DWI image
sesdimt=`fslval "$DiffFolder"/"$DiffData" dim4` #Number of datapoints per Pos series
rm "$DiffFolder"/"$DiffDataSuffix"/acqparams/"$DiffData"/index.txt > /dev/null 2>&1
for (( j=0; j<${sesdimt}; j++ )); do echo "1" >> "$DiffFolder"/"$DiffDataSuffix"/acqparams/"$DiffData"/index.txt; done        
# -- Create phase encoding and dwelltime parameter file
rm "$DiffFolder"/"$DiffDataSuffix"/acqparams/"$DiffData"/acqparams.txt > /dev/null 2>&1
if [ "$PEdir" == "1" ]; then
VoxelNumber=`fslval "$DiffFolder"/"$DiffData" dim1`
TotReadoutTime=`echo "scale=6; $DwellTimeSec*($VoxelNumber-1)" | bc`
    echo "1 0 0 $TotReadoutTime" >> "$DiffFolder"/"$DiffDataSuffix"/acqparams/"$DiffData"/acqparams.txt
else
VoxelNumber=`fslval "$DiffFolder"/"$DiffData" dim2`
TotReadoutTime=`echo "scale=6; $DwellTimeSec*($VoxelNumber-1)" | bc`
    echo "0 1 0 $TotReadoutTime" >> "$DiffFolder"/"$DiffDataSuffix"/acqparams/"$DiffData"/acqparams.txt
fi
echo "Check acquisition parameter files:"
echo ""
echo "`ls $DiffFolder/$DiffDataSuffix/acqparams/$DiffData/`"
echo ""

############################################
# STEP 2 - Prepare FieldMaps and T1w Images
############################################

if [ ${UseFieldmap} == "yes" ]; then
    reho "--- Preparing FieldMaps and T1w images..."
    echo ""
    geho "Running conservative BET on the FieldMap Magnitude image..."
    echo ""
    bet "$FieldMapFolder"/"$CASE"_strc_FieldMap_Magnitude.nii.gz "$DiffFolder"/"$DiffDataSuffix"/fieldmap/"$CASE"_strc_FieldMap_Magnitude_brain -m -f 0.65 -v
    echo ""
    geho "Running fsl_prepare_fieldmap assuming SIEMENS data..."  ## fsl_prepare_fieldmap <scanner> <phase_image> <magnitude_image> <out_image> <deltaTE (in ms)
    echo ""
    fsl_prepare_fieldmap SIEMENS "$FieldMapFolder"/"$CASE"_strc_FieldMap_Phase.nii.gz "$DiffFolder"/"$DiffDataSuffix"/fieldmap/"$CASE"_strc_FieldMap_Magnitude_brain.nii.gz "$DiffFolder"/"$DiffDataSuffix"/fieldmap/"$CASE"_fmap_rads "$TE"
    echo ""
else 
    echo ""
    reho "--- Omitting FieldMap step..."
    echo ""
fi

# -- Run BET on the DWI data
geho "Getting the first volume of each DWI image..."
echo ""
fslroi "$DiffFolder"/"$DiffData" "$DiffFolder"/"$DiffDataSuffix"/rawdata/"$DiffData"_nodif 0 1
geho "Run BET on the B0 EPI image to create masks..."
echo ""
bet "$DiffFolder"/"$DiffDataSuffix"/rawdata/"$DiffData"_nodif "$DiffFolder"/"$DiffDataSuffix"/rawdata/"$DiffData"_nodif_brain -m -f 0.35 -v
echo ""

# -- Check if PreFreeSurfer was completed to use existing inputs and avoid re-running BET
reho "--- Checking if PreFreeSurfer was completed to obtain inputs for epi_reg..."
echo ""

if [ -f "$T1wFolder"/T1w_acpc_dc_restore_brain.nii.gz ]; then
    geho "PreFreeSurfer data found: "
    echo ""
    echo "$T1wFolder/T1w_acpc_dc_restore_brain.nii.gz"
    echo ""
    if [ -f "$T1wFolder"/T1w_acpc_dc_restore_brain_pve_2.nii.gz ]; then
        geho "FAST already completed."
        echo ""
    else
        geho "Running FAST for the $T1wFolder/T1w_acpc_dc_restore_brain.nii.gz image..."
        echo ""
        fast -v -b -B "$T1wFolder"/T1w_acpc_dc_restore_brain
    fi
    # -- Set all the input image variables for epi_reg
    geho "Setting inputs for epi_reg:"
    T1wImage="$T1wFolder"/T1w_acpc_dc_restore
    T1wBrainImage="$T1wFolder"/T1w_acpc_dc_restore_brain
    WMSegImage="$T1wFolder"/T1w_acpc_dc_restore_brain_pve_2
    T1wImageMask="$T1wFolder"/T1w_acpc_brain_mask
    geho ""
    geho "--> T1w Data:             $T1wImage"
    geho "--> T1w BET+FAST Data:    $T1wBrainImage"
    geho "--> WM Segment FAST Data: $WMSegImage"
    geho "--> T1w Brain Mask Data:  $T1wImageMask"
    echo ""
else
    geho "PreFreeSurfer data not found. Using raw $CASE_strc_T1w_MPR1.nii.gz as input..."
    echo ""
    if [ -f "$T1wDiffFolder"/"$CASE"_strc_T1w_MPR1_brain_pve_2.nii.gz ]; then
        geho "BET & FAST already completed."
        echo ""
    else
        geho "Running BET for $T1wFolder/$CASE_strc_T1w_MPR1.nii.gz image..."
        echo ""
        bet "$T1wFolder"/"$CASE"_strc_T1w_MPR1 "$T1wDiffFolder"/"$CASE"_strc_T1w_MPR1_brain -m -B -f 0.3 -v
        echo ""
        geho "Running FAST for the T1w image..."
        echo ""
        fast -v -b -B "$T1wDiffFolder"/"$CASE"_strc_T1w_MPR1_brain
        echo ""
    fi
    # -- Set all the input image variables for epi_reg
    geho "Setting inputs for epi_reg:"
    T1wImage="$T1wFolder"/"$CASE"_strc_T1w_MPR1
    T1wBrainImage="$T1wDiffFolder"/"$CASE"_strc_T1w_MPR1_brain_restore
    WMSegImage="$T1wDiffFolder"/"$CASE"_strc_T1w_MPR1_brain_pve_2
    T1wImageMask="$T1wFolder"/"$CASE"_strc_T1w_MPR1_brain_mask
    geho ""
    geho "--> T1w Data:             $T1wImage"
    geho "--> T1w BET+FAST Data:    $T1wBrainImage"
    geho "--> WM Segment FAST Data: $WMSegImage"
    geho "--> T1w Brain Mask Data:  $T1wImageMask"
    echo ""
fi

############################################
# STEP 3 - Run eddy_cuda
############################################    
    
    # -- Performs eddy call with --fwhm=10,0,0,0,0  --ff=10 -- this performs an initial FWHM smoothing for the first step of registration, then re-run with 4 more iterations without smoothing; the --ff flag adds a fat factor for angular smoothing. 
    # -- For best possible results you want opposing diff directions but in practice we distribute directions on the sphere. Instead we look at 'cones'. This does not smooth the data but rather the predictions to allow best possible estimation via EDDY.
    reho "--- Running eddy_cuda..."    
    echo ""
    geho "Using the following eddy_cuda binary:    ${EDDYCUDADIR}/${eddy_cuda}"
    echo ""
    
    # -- Eddy call with cuda with extra QC options
    ${EDDYCUDADIR}/${eddy_cuda} --imain="$DiffFolder"/"$DiffData" --mask="$DiffFolder"/"$DiffDataSuffix"/rawdata/"$DiffData"_nodif_brain_mask --acqp="$DiffFolder"/"$DiffDataSuffix"/acqparams/"$DiffData"/acqparams.txt --index="$DiffFolder"/"$DiffDataSuffix"/acqparams/"$DiffData"/index.txt --bvecs="$DiffFolder"/"$DiffData".bvec --bvals="$DiffFolder"/"$DiffData".bval --fwhm=10,0,0,0,0 --ff=10 --nvoxhp=2000 --flm=quadratic --out="$DiffFolder"/"$DiffDataSuffix"/eddy/"$DiffData"_eddy_corrected --data_is_shelled --repol -v
    
############################################
# STEP 4 - Run epi_reg w/fieldmap correction
############################################    

# -- Performs registration on the DWI EPI raw B0 image to T1w while using the Fieldmap. 
# -- This gives the EPI --> T1 transformation given the FieldMap. 
# -- This yields a transformation matrix that can then be applied to the DWI data. 

if [ ${UseFieldmap} == "yes" ]; then
    echo ""
    reho "--- Running epi_reg for EPI--T1 data with fieldmap specification..." 
    echo ""
    epi_reg --epi="$DiffFolder"/"$DiffDataSuffix"/rawdata/"$DiffData"_nodif_brain --t1="$T1wImage" --t1brain="$T1wBrainImage" --out="$DiffFolder"/"$DiffDataSuffix"/reg/"$DiffData"_nodif2T1 --fmap="$DiffFolder"/"$DiffDataSuffix"/fieldmap/"$CASE"_fmap_rads --wmseg="$WMSegImage" --fmapmag="$FieldMapFolder"/"$CASE"_strc_FieldMap_Magnitude --fmapmagbrain="$DiffFolder"/"$DiffDataSuffix"/fieldmap/"$CASE"_strc_FieldMap_Magnitude_brain --echospacing="$DwellTimeSec" --pedir="$UnwarpDir" -v
else
    echo ""
    reho "--- Running epi_reg for EPI--T1 data without fieldmap specification..." 
    echo ""
    epi_reg --epi="$DiffFolder"/"$DiffDataSuffix"/rawdata/"$DiffData"_nodif_brain --t1="$T1wImage" --t1brain="$T1wBrainImage" --out="$DiffFolder"/"$DiffDataSuffix"/reg/"$DiffData"_nodif2T1 --wmseg="$WMSegImage" --echospacing="$DwellTimeSec" --pedir="$UnwarpDir" -v
fi

################################################################################################
# STEP 5 - Apply the epi_reg warp field (fieldmap correction + BBR to T1) to all diffusion data
################################################################################################    

# -- Registers the eddy_corrected DWI data to T1w space
echo ""
reho "--- Registering the eddy_corrected DWI data to T1w space..."
echo ""
# -- First create a downsampled T1w image to use a target
DiffRes=`fslval "$DiffFolder"/"$DiffData" pixdim1`
DiffResExt=`echo $DiffRes | cut -c1-3`
geho "Downsampling the $T1wImage, $T1wBrainImage and $T1wImageMask to $DiffData resolution: $DiffResExt mm ..."
echo ""
flirt -in "$T1wImage" -ref "$T1wImage" -applyisoxfm "$DiffRes" -interp spline -out "$T1wDiffFolder"/"$CASE"_T1w_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt" -v
flirt -in "$T1wBrainImage" -ref "$T1wImage" -applyisoxfm "$DiffRes" -interp spline -out "$T1wDiffFolder"/"$CASE"_T1w_brain_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt" -v
flirt -in "$T1wImageMask" -ref "$T1wImage" -applyisoxfm "$DiffRes" -interp nearestneighbour -out "$T1wDiffFolder"/"$CASE"_T1w_brain_mask_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt" -v
flirt -in "$WMSegImage" -ref "$T1wImage" -applyisoxfm "$DiffRes" -interp spline -out "$T1wDiffFolder"/"$CASE"_T1w_WMSegImage_"$DiffDataSuffix"_"$DiffResExt" -v    
fslmaths "$T1wDiffFolder"/"$CASE"_T1w_brain_mask_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt" -fillh "$T1wDiffFolder"/"$CASE"_T1w_brain_mask_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt"
echo ""
# -- Registers the DWI data to T1w space
if [ ${UseFieldmap} == "yes" ]; then
    geho "Applying the warp for $DiffData to T1w space with fieldmap specification..."; echo ""
    applywarp -i "$DiffFolder"/"$DiffDataSuffix"/eddy/"$DiffData"_eddy_corrected -r "$T1wDiffFolder"/"$CASE"_T1w_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt" -o "$DiffFolderOut"/"$DiffData"_data -w "$DiffFolder"/"$DiffDataSuffix"/reg/"$DiffData"_nodif2T1_warp --interp=spline --rel -v
else
    geho "Applying the warp for $DiffData to T1w space without fieldmap specification via epi_reg..."; echo ""
    epi_reg --epi="$DiffFolder"/"$DiffDataSuffix"/eddy/"$DiffData"_eddy_corrected --t1="$T1wDiffFolder"/"$CASE"_T1w_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt" --t1brain="$T1wDiffFolder"/"$CASE"_T1w_brain_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt" --out="$DiffFolderOut"/"$DiffData"_data --wmseg="$T1wDiffFolder"/"$CASE"_T1w_WMSegImage_"$DiffDataSuffix"_"$DiffResExt" --echospacing="$DwellTimeSec" --pedir="$UnwarpDir" -v
fi
echo ""

# -- Alan edited on 1/16/17 due to poor BET performance
geho "Getting the first volume of the registered DWI image..."
echo ""
fslroi "$DiffFolderOut"/"$DiffData"_data "$DiffFolderOut"/"$DiffData"_data_1stframe 0 1
geho "Running BET for final DWI data: $DiffFolderOut/$DiffData_data"
echo ""
bet "$DiffFolderOut"/"$DiffData"_data_1stframe "$DiffFolderOut"/"$DiffData"_data_1stframe -m -f 0.35 -v

echo ""
geho "Running fslmaths to brain-mask $DiffData using the down-sampled $T1wImageMask..."
fslmaths "$T1wDiffFolder"/"$CASE"_T1w_brain_mask_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt" -mul "$DiffFolderOut"/"$DiffData"_data_1stframe_mask "$DiffFolderOut"/"$CASE"_T1w_brain_mask_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt"_masked_with_DWI1stframe
fslmaths "$DiffFolderOut"/"$DiffData"_data.nii.gz -mul "$T1wDiffFolder"/"$CASE"_T1w_brain_mask_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt" "$DiffFolderOut"/"$DiffData"_data_brain_masked_with_T1.nii.gz 
fslmaths "$DiffFolderOut"/"$DiffData"_data.nii.gz -mul "$DiffFolderOut"/"$DiffData"_data_1stframe_mask "$DiffFolderOut"/"$DiffData"_data_brain_masked_with_DWI.nii.gz 
fslmaths "$DiffFolderOut"/"$DiffData"_data.nii.gz -mul "$DiffFolderOut"/"$CASE"_T1w_brain_mask_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt"_masked_with_DWI1stframe "$DiffFolderOut"/"$DiffData"_data_brain_masked_with_T1orDWI.nii.gz 

echo ""
# -- Aligns the BVECS and BVALS using HCP 
reho "--- Aligning BVECS to T1 space using HCP code"
echo ""
$HCPPIPEDIR_Global/Rotate_bvecs.sh "$DiffFolder"/"$DiffData".bvec "$DiffFolder"/"$DiffDataSuffix"/reg/"$DiffData"_nodif2T1.mat "$DiffFolderOut"/bvecs
cp "$DiffFolder"/"$DiffData".bval "$DiffFolderOut"/bvals
echo ""
    
# -- Perform completion checks

reho "--- Checking outputs..."
echo ""
if [ -f "$T1wDiffFolder"/"$CASE"_T1w_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt".nii.gz ]; then
    OutFile="$T1wDiffFolder"/"$CASE"_T1w_downsampled2diff_"$DiffDataSuffix"_"$DiffResExt".nii.gz
    geho "T1w data in DWI resolution:           $OutFile"
    echo ""
else
    reho "T1w data in DWI resolution missing. Something went wrong."
    echo ""
    exit 1
fi
if [ -f "$DiffFolderOut"/"$DiffData"_data.nii.gz ]; then
    OutFile="$DiffFolderOut"/"$DiffData"_data.nii.gz
    geho "DWI final processed data:             $OutFile"
    echo ""
else
    reho "DWI final processed data missing. Something went wrong."
    echo ""
    exit 1
fi
if [ -f  "$DiffFolderOut"/"$DiffData"_data_brain_masked_with_T1orDWI.nii.gz ]; then
    OutFile="$DiffFolderOut"/"$DiffData"_data_brain_masked_with_T1orDWI.nii.gz 
    geho "DWI brain-masked data:                        $OutFile"
    echo ""
else
    reho "DWI brain-masked data missing. Something went wrong."
    echo ""
    exit 1
fi
if [ -f  "$DiffFolderOut"/bvecs ]; then
    OutFile="$DiffFolderOut"/_bvecs
    geho "DWI BVECS:                            $OutFile"
    echo ""
else
    reho "BVECS in $DiffFolderOut missing. Something went wrong."
    echo ""
    exit 1
fi
if [ -f  "$DiffFolderOut"/bvals ]; then
    OutFile="$DiffFolderOut"/bvals
    geho "DWI BVALS:                            $OutFile"
    echo ""
else
    reho "BVALS in $DiffFolderOut missing. Something went wrong."
    echo ""
    exit 1
fi

geho "--- DWI preprocessing successfully completed"
echo ""
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""

}

######################################### END OF WORK ##########################################

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
