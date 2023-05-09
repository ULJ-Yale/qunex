#!/bin/bash

# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
    cat << EOF
``dwi_parcellate``

This function implements parcellation on the DWI dense connectomes using a
whole-brain parcellation (e.g. Glasser parcellation with subcortical labels
included).

It explicitly assumes the the Human Connectome Project folder structure for
preprocessing. Dense Connectome DWI data needs to be in the following folder::

    <folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/

Parameters:
    --sessionsfolder (str):
        Path to study data folder.

    --session (str):
        Comma separated list of sessions to run.

    --matrixversion (str):
        Matrix solution version to run parcellation on; e.g. 1 or 3.

    --parcellationfile (str):
        Specify the absolute path of the file you want to use for parcellation
        (e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/glasser_parcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii).

    --outname (str):
        Specify the suffix output name of the pconn file.

    --lengths (str, defaults 'no'):
        Parcellate lengths matrix ('yes' / 'no').

    --waytotal (str, defaults 'none'):
        Use the waytotal normalized version of the DWI dense connectome.
        Default:

        - 'none'     ... without waytotal normalization
        - 'standard' ... standard waytotal normalized
        - 'log'      ... log-transformed waytotal normalized.

Examples:
    Run directly via:

    ::

        ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_parcellate.sh \\
            --<parameter1> \\
            --<parameter2> \\
            --<parameter3> ... \\
            --<parameterN>

    NOTE: --scheduler is not available via direct script call.

    Run via::

        qunex dwi_parcellate \\
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

        qunex dwi_parcellate \\
            --sessionsfolder='<folder_with_sessions>' \\
            --sessions='<comma_separarated_list_of_cases>' \\
            --matrixversion='3' \\
            --parcellationfile='<dlabel_file_for_parcellation>' \\
            --overwrite='no' \\
            --outname='LR_Colelab_partitions_v1d_islands_withsubcortex'

    Example with flagged parameters for submission to the scheduler:

    ::

        qunex dwi_parcellate \\
            --sessionsfolder='<folder_with_sessions>' \\
            --sessions='<comma_separarated_list_of_cases>' \\
            --matrixversion='3' \\
            --parcellationfile='<dlabel_file_for_parcellation>' \\
            --overwrite='no' \\
            --outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \\
            --scheduler='<name_of_scheduler_and_options>'

EOF
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
#  -- Parse arguments
# ------------------------------------------------------------------------------

########################################## INPUTS ##########################################
# DWI Data and T1w data needed in HCP-style format and dense DWI probtrackX should be completed
# The data should be in $DiffFolder="$SessionsFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/Tractography
# Mandatory input parameters:
    # SessionsFolder 
    # Session        
    # MatrixVersion     e.g. 1 or 3
    # ParcellationFile  in *.dlabel.nii format
    # OutName

########################################## OUTPUTS #########################################
# -- Outputs will be *pconn.nii files located here:
#       DWIOutput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"

# -- Get the command line options for this script
get_options() {
local scriptName=$(basename ${0})
local arguments=($@)
# -- Initialize global output variables
unset SessionsFolder
unset Session
unset MatrixVersion
unset ParcellationFile
unset OutName
unset Overwrite
unset WayTotal
unset Lengths
unset DWIOutFilePconn
unset DWIOutFilePDconn
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
            ;;
        --version)
            version_show $@
            exit 0
            ;;
        --sessionsfolder=*)
            SessionsFolder=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --session=*)
            CASE=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --matrixversion=*)
            MatrixVersion=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --parcellationfile=*)
            ParcellationFile=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --outname=*)
            OutName=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --waytotal=*)
            WayTotal=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --lengths=*)
            Lengths=${argument/*=/""}
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
    reho "ERROR: <matrix_version_value> not specified>"
    echo ""
    exit 1
fi
if [ -z ${ParcellationFile} ]; then
    usage
    reho "ERROR: <file_for_parcellation> not specified>"
    echo ""
    exit 1
fi
if [ -z ${WayTotal} ]; then
    reho "No <use_waytotal_normalized_data> specified. Assuming default [none]"
    WayTotal=none
    echo ""
fi
if [ -z ${Lengths} ]; then
    reho "No <parcellate_streamline_lengths> specified. Assuming default [no]"
    Lengths="no"
    echo ""
fi
if [ -z ${OutName} ]; then
    usage
    reho "ERROR: <name_of_output_pconn_file> not specified>"
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
echo "   Session: ${CASE}"
echo "   MatrixVersion: ${MatrixVersion}"
echo "   ParcellationFile: ${ParcellationFile}"
echo "   Waytotal normalization: ${WayTotal}"
echo "   Streamline Lengths: ${Lengths}"
echo "   OutName: ${OutName}"
echo "   Overwrite: ${Overwrite}"
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""
}

######################################### DO WORK ##########################################
# gzip $ResultsFolder/${OutFileName} --fast
# gzip $ResultsFolder/${OutFileTemp}_waytotnorm.dconn.nii --fast

main() {
# -- Get Command Line Options
get_options $@

# -- Define inputs and output
echo "--- Establishing paths for all input and output folders:"; echo ""

# -- Define input. If not using the lengths matrix, then check if WayTotal normalization is selected
if [ "$Lengths" == "yes" ]; then
    echo "--- Using streamline length dconn file"; echo ""
    DWIInput="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_lengths.dconn.nii.gz"
    DWIOutFilePconn="${CASE}_Conn${MatrixVersion}_lengths_${OutName}.pconn.nii"
    DWIOutFilePDconn="${CASE}_Conn${MatrixVersion}_lengths_${OutName}.pdconn.nii"
    if [ ! "$WayTotal" == "none" ]; then
        echo "--- ignoring waytotal argument (should be set to none when parcellating the streamline lengths matrix)"; echo ""
    fi 
else

    if [ "$WayTotal" == "none" ]; then
        echo "--- Using dconn file without waytotal normalization"; echo ""
        DWIInput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/Conn${MatrixVersion}.dconn.nii.gz"
        DWIOutFilePconn="${CASE}_Conn${MatrixVersion}_${OutName}.pconn.nii"
        DWIOutFilePDconn="${CASE}_Conn${MatrixVersion}_${OutName}.pdconn.nii"
    fi
    if [ "$WayTotal" == "standard" ]; then
        echo "--- Using waytotal normalized dconn file"; echo ""
        DWIInput="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm.dconn.nii.gz"
        DWIOutFilePconn="${CASE}_Conn${MatrixVersion}_waytotnorm_${OutName}.pconn.nii"
        DWIOutFilePDconn="${CASE}_Conn${MatrixVersion}_waytotnorm_${OutName}.pdconn.nii"
    fi
    if [ "$WayTotal" == "log" ]; then
        echo "--- Using log-transformed waytotal normalized dconn file"; echo ""
        DWIInput="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm_log.dconn.nii.gz"
        DWIOutFilePconn="${CASE}_Conn${MatrixVersion}_waytotnorm_log_${OutName}.pconn.nii"
        DWIOutFilePDconn="${CASE}_Conn${MatrixVersion}_waytotnorm_log_${OutName}.pdconn.nii"
    fi

fi

# -- Define output
DWIOutput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"
echo "      Dense DWI Connectome Input:              ${DWIInput}"; echo ""
echo "      Parcellated DWI Connectome Output:       ${DWIOutput}/${DWIOutFilePconn}"; echo ""

# -- Delete any existing output sub-directories
if [ "$Overwrite" == "yes" ]; then
    reho "--- Deleting prior runs for $DiffData..."
    echo ""
    rm -f "$DWIOutput"/"$DWIOutFilePDconn" > /dev/null 2>&1
    rm -f "$DWIOutput"/"$DWIOutFilePconn" > /dev/null 2>&1
fi

# -- Check if parcellation was completed
reho "--- Checking if parcellation was completed..."
echo ""

if [ -f ${DWIOutput}/${DWIOutFilePconn} ]; then
    geho "--- Parcellation data found: "
    echo ""
    echo "    ${DWIOutput}/${DWIOutFilePconn}"
    echo ""
    exit 1
else
    reho "--- Parcellation data not found."
    echo ""
    echo "--- Computing parcellation by COLUMN on $DWIInput..."
    echo ""
    # -- First parcellate by COLUMN and save a *pdconn file
    wb_command -cifti-parcellate "$DWIInput" "$ParcellationFile" COLUMN "$DWIOutput"/"$DWIOutFilePDconn"
    echo "--- Computing parcellation by ROW on ${DWIOutput}/${DWIOutFilePDconn} ..."
    echo ""
    # -- Next parcellate by ROW and save final *pconn file
    wb_command -cifti-parcellate "$DWIOutput"/"$DWIOutFilePDconn" "$ParcellationFile" ROW "$DWIOutput"/"$DWIOutFilePconn"
fi

# -- Perform completion checks
reho "--- Checking outputs..."
echo ""
if [ -f ${DWIOutput}/${DWIOutFilePconn} ]; then
    geho "Parcellated (pconn) file for Matrix $MatrixVersion:     ${DWIOutput}/${DWIOutFilePconn}"
    echo ""
else
    reho "Parcellated (pconn) file for Matrix $MatrixVersion is missing. Something went wrong."
    echo ""
    exit 1
fi

reho "--- DWI Parcellation successfully completed"
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
