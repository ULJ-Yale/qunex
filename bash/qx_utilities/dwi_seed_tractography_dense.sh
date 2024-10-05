#!/bin/bash

# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

usage() {
    cat << EOF
``dwi_seed_tractography_dense``

This function implements reduction on the DWI dense connectomes using a given
'seed' structure (e.g. thalamus).

It explicitly assumes the the Human Connectome Project folder structure for
preprocessing. Dense Connectome DWI data needs to be in the following folder::

    <folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/

It produces the following outputs:

- Dense connectivity seed tractography file:
  ``<folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<session>_Conn<matrixversion>_<outname>.dconn.nii``
- Dense scalar seed tractography file:
  ``<folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<session>_Conn<matrixversion>_<outname>_Avg.dscalar.nii``

Parameters:
    --sessionsfolder (str):
        Path to study folder that contains sessions.

    --sessions (str):
        Comma separated list of sessions to run.

    --matrixversion (str):
        Matrix solution version to run parcellation on; e.g. 1 or 3.

    --seedfile (str):
        Specify the absolute path of the seed file you want to use as a seed for
        dconn reduction (e.g.
        <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz).
        Note: If you specify --seedfile='gbc' then the function computes an
        average across all streamlines from every greyordinate to all other
        greyordinates.

    --outname (str):
        Specify the suffix output name of the dscalar file.

    --overwrite (str, default 'no'):
        Whether to overwrite existing data (yes) or not (no). Note that
        previous data is deleted before the run, so in the case of a failed
        command run, previous results are lost.

    --waytotal (str, default 'none'):
        Use the waytotal normalized version of the DWI dense connectome.
        Default:

        - 'none'     ... without waytotal normalization
        - 'standard' ... standard waytotal normalized
        - 'log'      ... log-transformed waytotal normalized.

Examples:
    Run directly via::

        ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_seed_tractography_dense.sh \\
            --<parameter1> \\
            --<parameter2> \\
            --<parameter3> ... \\
            --<parameterN>

    NOTE: --scheduler is not available via direct script call.

    Run via::

        qunex dwi_seed_tractography_dense \\
            --<parameter1> \\
            --<parameter2> ... \\
            --<parameterN>

    NOTE: scheduler is available via qunex call.

    --scheduler
        A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
        relevant options.

    For SLURM scheduler the string would look like this via the qunex call::

        --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

    ::

        qunex dwi_seed_tractography_dense \\
            --sessionsfolder='<folder_with_sessions>' \\
            --session='<case_id>' \\
            --matrixversion='3' \\
            --seedfile='<folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz' \\
            --overwrite='no' \\
            --outname='THALAMUS'

EOF
exit 0
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
    # SeedFile  # e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/glasser_parcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii
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
            echo "ERROR: Unrecognized Option: ${argument}"
            echo ""
            exit 1
            ;;
    esac
done

# -- Check required parameters
if [ -z ${SessionsFolder} ]; then
    usage
    echo "ERROR: <sessions-folder-path> not specified>"
    echo ""
    exit 1
fi
if [ -z ${CASE} ]; then
    usage
    echo "ERROR: <session-id> not specified>"
    echo ""
    exit 1
fi
if [ -z ${MatrixVersion} ]; then
    usage
    echo "ERROR: <matrix_version_value> not specified"
    echo ""
    exit 1
fi
if [ -z ${WayTotal} ]; then
    echo "No <use_waytotal_normalized_data> specified. Assuming default [none]"
    echo ""
fi
if [ -z ${SeedFile} ]; then
    usage
    echo "ERROR: <structure_for_seeding> not specified"
    echo ""
    exit 1
fi
if [ -z ${OutName} ]; then
    usage
    echo "ERROR: <name_of_output_dscalar_file> not specified"
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
echo "------------------------- Start of work --------------------------------"
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
    echo "--- Deleting prior runs in $DWIOutput..."; echo ""
    rm -f ${DWIOutput}/${DWIOutFileDconn} > /dev/null 2>&1
    rm -f ${DWIOutput}/${DWIOutFileDscalar} > /dev/null 2>&1
fi

# -- Check if the dense parcellation was completed and exists
echo "--- Checking if parcellation was completed..."; echo ""
# -- Check if file present
if [ -f ${DWIOutput}/${DWIOutFileDscalar} ]; then
    echo "--- Dense scalar seed tractography data found: "
    echo ""
    echo "      ${DWIOutput}/${DWIOutFileDscalar}"
    echo ""
    exit 1
else
    echo "--- Dense scalar seed tractography data not found."; echo ""
    # -- Check of GBC only was requested 
    if [ ${SeedFile} == "gbc" ]; then
        echo "--- Computing dense DWI GBC on $DWIInput..."; echo ""
        wb_command -cifti-reduce ${DWIInput} MEAN ${DWIOutput}/${DWIOutFileDscalar}
    else
        # -- First restrict by COLUMN and save a *dconn file
        echo "--- Computing dense DWI connectome restriction by COLUMN on $DWIInput..."; echo ""
        wb_command -cifti-restrict-dense-map ${DWIInput} COLUMN ${DWIOutput}/${DWIOutFileDconn} -vol-roi ${SeedFile}
        echo "--- Computing average of the restricted dense connectome across the input structure $SeedFile..."; echo ""
        # -- Next average the restricted dense connectome across the input structure and save the dscalar
        wb_command -cifti-average-dense-roi ${DWIOutput}/${DWIOutFileDscalar} -cifti ${DWIOutput}/${DWIOutFileDconn} -vol-roi ${SeedFile}
    fi
fi    

# -- Perform completion checks
echo "--- Checking outputs..."; echo ""
if [ -f ${DWIOutput}/${DWIOutFileDscalar} ]; then
    echo "--- Dense scalar output file for Matrix ${MatrixVersion}:     ${DWIOutput}/${DWIOutFileDscalar}"
    echo ""
    echo "--- DWI restriction of dense connectome successfully completed "
    echo ""
    echo "------------------------- Successful completion of work --------------------------------"
    echo ""
else
    echo "--- Dense scalar output file for Matrix ${MatrixVersion} is missing. Something went wrong."
    echo ""
    exit 1
fi

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
