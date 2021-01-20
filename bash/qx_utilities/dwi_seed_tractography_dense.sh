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
# * Alan Anticevic, N3 Division, Yale University
#
# ## PRODUCT
#
# dwi_seed_tractography_dense.sh 
#
# ## LICENSE
#
# * The dwi_seed_tractography_dense.sh = the "Software"
# * This Software conforms to the license outlined in the QuNex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ## DESCRIPTION
#
# This script, dwi_seed_tractography_dense.sh, is a wrapper for deducting dense 
# connectome DWI data with seed input. It implements reduction on the DWI dense 
# connectomes using a given 'seed' structure (e.g. thalamus)
#
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * Connectome Workbench (v1.0 or above)
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./dwi_seed_tractography_dense.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are either Conn1.nii.gz or Conn3.nii.gz, both of which are results of the AP probtrackxgpudense function
# * These data are stored in: "$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/ 
#
#~ND~END~
#
# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
 echo ""
 echo "This function implements reduction on the DWI dense connectomes using a given "
 echo "'seed' structure (e.g. thalamus)."
 echo ""
 echo "It explicitly assumes the the Human Connectome Project folder structure for "
 echo "preprocessing. Dense Connectome DWI data needs to be in the following folder::"
 echo ""
 echo " <folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/"
 echo ""
 echo "It produces the following outputs::"
 echo ""
 echo "- Dense connectivity seed tractography file:"
 echo "  <folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<session>_Conn<matrixversion>_<outname>.dconn.nii"
 echo "- Dense scalar seed tractography file:"
 echo "  <folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<session>_Conn<matrixversion>_<outname>_Avg.dscalar.nii"
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "--sessionsfolder    Path to study folder that contains sessions"
 echo "--sessions          Comma separated list of sessions to run"
 echo "--matrixversion     Matrix solution verion to run parcellation on; e.g. 1 or 3"
 echo "--seedfile          Specify the absolute path of the seed file you want to use "
 echo "                    as a seed for dconn reduction "
 echo "                    (e.g. <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz)"
 echo ""
 echo "                    Note: If you specify --seedfile='gbc' then the function "
 echo "                    computes an average across all streamlines from every "
 echo "                    greyordinate to all other greyordinates."
 echo "--outname           Specify the suffix output name of the dscalar file"
 echo "--overwrite         Delete prior run for a given session (yes / no)"
 echo "--waytotal          Use the waytotal normalized version of the DWI dense "
 echo "                    connectome. Default: [none]"
 echo ""
 echo "                    - none     ... without waytotal normalization" 
 echo "                    - standard ... standard waytotal normalized"
 echo "                    - log      ... log-transformed waytotal normalized"
 echo ""
 echo "EXAMPLE USE"
 echo "==========="
 echo ""
 echo "Run directly via::"
 echo ""
 echo " ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_seed_tractography_dense.sh \ "
 echo " --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
 echo ""
 reho "NOTE: --scheduler is not available via direct script call."
 echo ""
 echo "Run via:: "
 echo ""
 echo "  qunex dwi_seed_tractography_dense --<parameter1> --<parameter2> ... --<parameterN> "
 echo ""
 geho "NOTE: scheduler is available via qunex call."
 echo ""
 echo "--scheduler       A string for the cluster scheduler (e.g. LSF, PBS or SLURM) "
 echo "                  followed by relevant options"
 echo ""
 echo "For SLURM scheduler the string would look like this via the qunex call:: "
 echo ""                   
 echo "  --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
 echo ""
 echo "::"
 echo ""
 echo " qunex dwi_seed_tractography_dense --sessionsfolder='<folder_with_sessions>' \ "
 echo " --session='<case_id>' \ "
 echo " --matrixversion='3' \ "
 echo " --seedfile='<folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz' \ "
 echo " --overwrite='no' \ "
 echo " --outname='THALAMUS'"
 echo ""
 exit 0
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

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]]; then
    usage
fi

# ------------------------------------------------------------------------------
# -- Parse arguments
# ------------------------------------------------------------------------------

########################################## INPUTS ########################################## 

# DWI Data and T1w data needed in HCP-style format and dense DWI probtrackX should be completed
# The data should be in $DiffFolder="$SessionsFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/Tractography
# Mandatory input parameters:
    # SessionsFolder # e.g. /gpfs/project/fas/n3/Studies/Connectome/sessions
    # Session      # e.g. 100307
    # MatrixVersion # e.g. 1 or 3
    # SeedFile  # e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii
    # OutName  # e.g. THALAMUS

########################################## OUTPUTS #########################################

# -- Outputs will be *pconn.nii files located here:
#    DWIOutput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"

# -- Get the command line options for this script

get_options() {

local scriptName=$(basename ${0})
local arguments=($@)

# -- Initialize global output variables
unset SessionsFolder
unset Sessions
unset MatrixVersion
unset ParcellationFile
unset OutName
unset Overwrite
unset WayTotal
unset DWIOutFileDscalar
unset DWIOutFileDconn

runcmd=""

# -- Parse arguments
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
            exit 1
            ;;
        --sessionsfolder=*)
            SessionsFolder=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --sessions=*)
            CASE=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --matrixversion=*)
            MatrixVersion=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --seedfile=*)
            SeedFile=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --waytotal=*)
            WayTotal=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --outname=*)
            OutName=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --overwrite=*)
            Overwrite=${argument/*=/""}
            index=$(( index + 1 ))
            ;;      
        *)
            usage
            reho "ERROR: Unrecognized Option: ${argument}"
            echo ""
            exit 1
            ;;
    esac
done

# -- Check required parameters
if [ -z ${SessionsFolder} ]; then
    usage
    reho "ERROR: <sessions-folder-path> not specified>"
    echo ""
    exit 1
fi
if [ -z ${CASE} ]; then
    usage
    reho "ERROR: <session-id> not specified>"
    echo ""
    exit 1
fi
if [ -z ${MatrixVersion} ]; then
    usage
    reho "ERROR: <matrix_version_value> not specified"
    echo ""
    exit 1
fi
if [ -z ${WayTotal} ]; then
    reho "No <use_waytotal_normalized_data> specified. Assuming default [none]"
    echo ""
fi
if [ -z ${SeedFile} ]; then
    usage
    reho "ERROR: <structure_for_seeding> not specified"
    echo ""
    exit 1
fi
if [ -z ${OutName} ]; then
    usage
    reho "ERROR: <name_of_output_dscalar_file> not specified"
    exit 1
fi

# -- Set StudyFolder
cd $SessionsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null

# -- Report options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   SessionsFolder: ${SessionsFolder}"
echo "   Sessions: ${CASE}"
echo "   MatrixVersion: ${MatrixVersion}"
echo "   SeedFile: ${SeedFile}"
echo "   Waytotal normalization: ${WayTotal}"
echo "   OutName: ${OutName}"
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

# -- Define inputs and output
echo "--- Establishing paths for all input and output folders:"; echo ""

# -- Define input and check if WayTotal normalization is selected
if [ ${WayTotal} == "standard" ]; then
    echo "--- Using waytotal normalized dconn file"; echo ""
    DWIInput=`ls ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm.dconn.nii*`
    if [ $(echo $DWIInput | grep -c gz) -eq 1 ]; then
        DWIInput="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm.dconn.nii.gz"
    else
        DWIInput="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm.dconn.nii"    
    fi
    DWIOutFileDscalar="${CASE}_Conn${MatrixVersion}_waytotnorm_${OutName}_Avg.dscalar.nii"
    DWIOutFileDconn="${CASE}_Conn${MatrixVersion}_waytotnorm_${OutName}.dconn.nii"
    DWIOutFileDscalarGBC="${CASE}_Conn${MatrixVersion}_waytotnorm_${OutName}_Avg_GBC.dscalar.nii"
elif [ ${WayTotal} == "log" ]; then
    echo "--- Using log-transformed waytotal normalized dconn file"; echo ""
    DWIInput=`ls ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm_log.dconn.nii*`
    if [ $(echo $DWIInput | grep -c gz) -eq 1 ]; then
        DWIInput="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm_log.dconn.nii.gz"
    else
        DWIInput="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm_log.dconn.nii"    
    fi
    DWIOutFileDscalar="${CASE}_Conn${MatrixVersion}_waytotnorm_log_${OutName}_Avg.dscalar.nii"
    DWIOutFileDconn="${CASE}_Conn${MatrixVersion}_waytotnorm_log_${OutName}.dconn.nii"
    DWIOutFileDscalarGBC="${CASE}_Conn${MatrixVersion}_waytotnorm_log_${OutName}_Avg_GBC.dscalar.nii"
elif ! { [ "${WayTotal}" = "log" ] || [ "${WayTotal}" = "standard" ]; }; then
    echo "--- Using dconn file without waytotal normalization"; echo ""
    DWIInput=`ls $SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/Conn${MatrixVersion}.dconn.nii*`
    if [ $(echo $DWIInput | grep -c gz) -eq 1 ]; then
        DWIInput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/Conn${MatrixVersion}.dconn.nii.gz"
    else
        DWIInput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/Conn${MatrixVersion}.dconn.nii"    
    fi
    DWIOutFileDconn="${CASE}_Conn${MatrixVersion}_${OutName}.dconn.nii"
    DWIOutFileDscalar="${CASE}_Conn${MatrixVersion}_${OutName}_Avg.dscalar.nii"
    DWIOutFileDscalarGBC="${CASE}_Conn${MatrixVersion}_${OutName}_Avg_GBC.dscalar.nii"
fi

# -- Check if GBC requested
if [ ${SeedFile} == "gbc" ]; then
    DWIOutFileDscalar="$DWIOutFileDscalarGBC"
fi

# -- Define output directory
DWIOutput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"
echo "--- Dense DWI Connectome Input:          ${DWIInput}"; echo ""
echo "--- Parcellated DWI Connectome Output:   ${DWIOutput}/${DWIOutFileDscalar}"; echo ""

# -- Delete any existing output sub-directories
if [ "$Overwrite" == "yes" ]; then
    reho "--- Deleting prior runs in $DWIOutput..."; echo ""
    rm -f ${DWIOutput}/${DWIOutFileDconn} > /dev/null 2>&1
    rm -f ${DWIOutput}/${DWIOutFileDscalar} > /dev/null 2>&1
fi

# -- Check if the dense parcellation was completed and exists
echo "--- Checking if parcellation was completed..."; echo ""
# -- Check if file present
if [ -f ${DWIOutput}/${DWIOutFileDscalar} ]; then
    geho "--- Dense scalar seed tractography data found: "
    echo ""
    echo "      ${DWIOutput}/${DWIOutFileDscalar}"
    echo ""
    exit 1
else
    reho "--- Dense scalar seed tractography data not found."; echo ""
    # -- Check of GBC only was requested 
    if [ ${SeedFile} == "gbc" ]; then
        geho "--- Computing dense DWI GBC on $DWIInput..."; echo ""
        wb_command -cifti-reduce ${DWIInput} MEAN ${DWIOutput}/${DWIOutFileDscalar}
    else
        # -- First restrict by COLUMN and save a *dconn file
        geho "--- Computing dense DWI connectome restriction by COLUMN on $DWIInput..."; echo ""
        wb_command -cifti-restrict-dense-map ${DWIInput} COLUMN ${DWIOutput}/${DWIOutFileDconn} -vol-roi ${SeedFile}
        geho "--- Computing average of the restricted dense connectome across the input structure $SeedFile..."; echo ""
        # -- Next average the restricted dense connectome across the input structure and save the dscalar
        wb_command -cifti-average-dense-roi ${DWIOutput}/${DWIOutFileDscalar} -cifti ${DWIOutput}/${DWIOutFileDconn} -vol-roi ${SeedFile}
    fi
fi    

# -- Perform completion checks
echo "--- Checking outputs..."; echo ""
if [ -f ${DWIOutput}/${DWIOutFileDscalar} ]; then
    geho "--- Dense scalar output file for Matrix ${MatrixVersion}:     ${DWIOutput}/${DWIOutFileDscalar}"
    echo ""
    geho "--- DWI restriction of dense connectome successfully completed "
    echo ""
    geho "------------------------- Successful completion of work --------------------------------"
    echo ""
else
    reho "--- Dense scalar output file for Matrix ${MatrixVersion} is missing. Something went wrong."
    echo ""
    exit 1
fi

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
