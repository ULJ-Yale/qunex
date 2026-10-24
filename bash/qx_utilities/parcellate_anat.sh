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
``parcellate_anat``

Run parcellation on the dense cortical thickness OR myelin files using a 
whole-brain parcellation (e.g. Glasser parcellation with subcortical labels 
included).

..  qx_command:
    type: processing.session
    language: bash

Parameters:
    --studyfolder (str):
        The path to the study folder. The sessions are in its ``sessions``
        folder, unless --sessionsfolder names another one.

    --sessionsfolder (str, default '<studyfolder>/sessions'):
        The path to the folder with the sessions. Set it only when the
        sessions are not in the ``sessions`` folder of the study. One of
        --studyfolder and --sessionsfolder has to be given.

    --session (str):
        The id of the session to run. To run the command over several
        sessions, give them with --sessions or --batchfile instead: qunex then
        runs it once for each session.

    --inputdatatype (str):
        Specify the type of dense data for the input file (e.g. MyelinMap_BC or
        corrThickness).

    --parcellationfile (str):
        Specify the ∗.dlabel file you want to use for parcellation: an absolute
        path, or one relative to the study folder.

    --outname (str):
        Specify the suffix output name of the pconn file.

    --overwrite (str, default 'no'):
        Whether to overwrite existing data (yes) or not (no). Note that
        previous data is deleted before the run, so in the case of a failed
        command run, previous results are lost.

    --extractdata (str, default 'no'):
        Specify if you want to save out the matrix as a CSV file ('yes' /
        'no').

Examples:
    Run directly via::

        ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/parcellate_anat.sh \\
            --<parameter1> \\
            --<parameter2> \\
            --<parameter3> ... \\
            --<parameterN>

    NOTE: --scheduler is not available via direct script call.

    Run via::

        qunex parcellate_anat \\
            --<parameter1> \\
            --<parameter2> \\
            --<parameter3> ... \\
            --<parameterN>

    NOTE: scheduler is available via qunex call:

    --scheduler
        A string for the cluster scheduler (e.g. PBS or SLURM) followed by
        relevant options.

    For SLURM scheduler the string would look like this via the qunex call::

        --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

    ::

        qunex parcellate_anat \\
            --studyfolder='<path_to_study_folder>' \\
            --session='<case_id>' \\
            --inputdatatype='MyelinMap_BC' \\
            --parcellationfile='<dlabel_file_for_parcellation>' \\
            --overwrite='no' \\
            --extractdata='yes' \\
            --outname='<name_of_output_pconn_file>'

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
# -- Parse and check all arguments
# ------------------------------------------------------------------------------

########### INPUTS ###############

	# -- Data should be pre-processed and in CIFTI format
	# the data should be in <sessionsfolder>/<session>/hcp/<session>/MNINonLinear/fsaverage_LR32k

########## OUTPUTS ###############

	# outputs are *pscalar.nii files written next to the input

# -- Get the command line options for this script
get_options() {

local scriptName=$(basename ${0})
local arguments=($@)

# -- Initialize global output variables
unset StudyFolder
unset SessionsFolder
unset Session
unset InputDataType
unset ParcellationFile
unset OutName
unset Overwrite
unset ExtractData

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
        --studyfolder=*)
            StudyFolder=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --sessionsfolder=*)
            SessionsFolder=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --session=*)
            CASE=${argument/*=/""}
            index=$(( index + 1 ))
            ;;                    
        --inputdatatype=*)
            InputDataType=${argument/*=/""}
            index=$(( index + 1 ))
            ;; 
        --extractdata=*)
            ExtractData=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        # --extractdata was documented as a flag, given without a value it
        # asks for the CSV file
        --extractdata)
            ExtractData="yes"
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
        --overwrite=*)
            Overwrite=${argument/*=/""}
            index=$(( index + 1 ))
            ;;      
        *)
            echo "ERROR: Unrecognized Option: ${argument}"
            echo ""
            exit 1
            ;;
    esac
done

# the sessions are in the sessions folder of the study, unless --sessionsfolder
# names another one
if [ -z "${SessionsFolder}" ] && [ -n "${StudyFolder}" ]; then
    SessionsFolder="${StudyFolder}/sessions"
fi

# -- Check required parameters
if [ -z "${SessionsFolder}" ]; then
    echo "ERROR: Neither --studyfolder nor --sessionsfolder specified"
    echo ""
    exit 1
fi
if [ -z ${CASE} ]; then
    echo "ERROR: <session-id> not specified"
    echo ""
    exit 1
fi
if [ -z ${InputDataType} ]; then
    echo "ERROR: <type_of_dense_data_for_input_file> not specified"
    echo ""
    exit 1
fi
if [ -z ${ParcellationFile} ]; then
    echo "ERROR: <file_for_parcellation> not specified"
    echo ""
    exit 1
fi
if [ -z ${OutName} ]; then
    echo "ERROR: <name_of_output_pconn_file> not specified"
    exit 1
fi

# -- Report options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   SessionsFolder: ${SessionsFolder}"
echo "   Session: ${CASE}"
echo "   InputDataType: ${InputDataType}"
echo "   ParcellationFile: ${ParcellationFile}"
echo "   OutName: ${OutName}"
echo "   Overwrite: ${Overwrite}"
echo "   ExtractData: ${ExtractData}"
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
echo "--- Establishing paths for all input and output folders:"
echo ""
# -- Define all inputs and outputs depending on data type input
echo "       Working with $InputDataType dscalar files..."
echo ""
# -- Define extension 
InputFileExt="dscalar.nii"
OutFileExt="pscalar.nii"
# -- Define input
DATAInput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/fsaverage_LR32k/$CASE.${InputDataType}.32k_fs_LR.${InputFileExt}"
# -- Define output
DATAOutput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/fsaverage_LR32k/$CASE.${InputDataType}.32k_fs_LR_${OutName}.${OutFileExt}"
echo "      Dense $InputDataType Input:              ${DATAInput}"
echo ""
echo "      Parcellated $InputDataType Output:       ${DATAOutput}"
echo ""

# -- Delete any existing output sub-directories
if [ "$Overwrite" == "yes" ]; then
	echo "--- Deleting prior $DATAOutput..."
	echo ""
	rm -f "$DATAOutput" > /dev/null 2>&1
fi
# -- Check if parcellation was completed
echo "--- Checking if parcellation was completed..."
echo ""
if [ -f "$DATAOutput" ]; then
	echo "Parcellation data already completed: "
	echo ""
	echo "      $DATAOutput"
	echo ""
	exit 0
else
	echo "Parcellation data not found."
	echo ""
	echo "Computing parcellation on $DATAInput..."
	echo ""
	# -- First parcellate by COLUMN and save a parcellated file
	wb_command -cifti-parcellate "$DATAInput" "$ParcellationFile" COLUMN "$DATAOutput"
	# -- Then check if extraction of data is set to 'yes'
	if [ "$ExtractData" == "yes" ]; then 
		echo "Saving out the data in a CSV file..."
		echo ""
		DATACSVOutput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/fsaverage_LR32k/$CASE.${InputDataType}.32k_fs_LR_${OutName}.csv"
		rm -f ${DATACSVOutput} > /dev/null 2>&1
		wb_command -nifti-information -print-matrix "$DATAOutput" >> "$DATACSVOutput"
	fi
fi	

# -- Perform completion checks
echo "--- Checking outputs..."
echo ""
if [ -f "$DATAOutput" ]; then
	echo "Parcellated file:           $DATAOutput"
	echo ""
else
	echo "Parcellated file $DATAOutput is missing. Something went wrong."
	echo ""
	exit 1
fi

echo "--- Parcellation successfully completed"
echo ""
echo "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
