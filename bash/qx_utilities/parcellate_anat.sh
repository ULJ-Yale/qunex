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

This function implements parcellation on the dense cortical thickness OR myelin
files using a whole-brain parcellation (e.g. Glasser parcellation with
subcortical labels included).

Parameters:
    --sessionsfolder (str):
        Path to study data folder.
    --session (str):
        Comma separated list of sessions to run
    --inputdatatype (str):
        Specify the type of dense data for the input file (e.g. MyelinMap_BC or
        corrThickness).
    --parcellationfile (str):
        Specify the absolute path of the ∗.dlabel file you want to use for
        parcellation.
    --outname (str):
        Specify the suffix output name of the pconn file.
    --overwrite (str):
        Delete prior run for a given session ('yes' / 'no').
    --extractdata (flag):
        Specify if you want to save out the matrix as a CSV file.

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
        A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
        relevant options.

    For SLURM scheduler the string would look like this via the qunex call::

        --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

    ::

        qunex parcellate_anat \\
            --sessionsfolder='<folder_with_sessions>' \\
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
# -- Parse and check all arguments
# ------------------------------------------------------------------------------

########### INPUTS ###############

	# -- Data should be pre-processed and in CIFTI format
	# -- The data should be in the folder relative to the master study folder, specified by the inputfile

########## OUTPUTS ###############

	# -- Outputs will be *pconn.nii files located in the location specified in the outputpath

# -- Get the command line options for this script
get_options() {

local scriptName=$(basename ${0})
local arguments=($@)

# -- Initialize global output variables
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
if [ -z ${InputDataType} ]; then
    usage
    reho "ERROR: <type_of_dense_data_for_input_file>"
    echo ""
    exit 1
fi
if [ -z ${ParcellationFile} ]; then
    usage
    reho "ERROR: <file_for_parcellation> not specified>"
    echo ""
    exit 1
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
echo "   InputDataType: ${InputDataType}"
echo "   ParcellationFile: ${ParcellationFile}"
echo "   OutName: ${OutName}"
echo "   Overwrite: ${Overwrite}"
echo "   ExtractData: ${ExtractData}"
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
reho "--- Establishing paths for all input and output folders:"
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
	reho "--- Deleting prior $DATAOutput..."
	echo ""
	rm -f "$DATAOutput" > /dev/null 2>&1
fi
# -- Check if parcellation was completed
reho "--- Checking if parcellation was completed..."
echo ""
if [ -f "$DATAOutput" ]; then
	geho "Parcellation data already completed: "
	echo ""
	echo "      $DATAOutput"
	echo ""
	exit 0
else
	reho "Parcellation data not found."
	echo ""
	geho "Computing parcellation on $DATAInput..."
	echo ""
	# -- First parcellate by COLUMN and save a parcellated file
	wb_command -cifti-parcellate "$DATAInput" "$ParcellationFile" COLUMN "$DATAOutput"
	# -- Then check if extraction of data is set to 'yes'
	if [ "$ExtractData" == "yes" ]; then 
		geho "Saving out the data in a CSV file..."
		echo ""
		DATACSVOutput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/fsaverage_LR32k/$CASE.${InputDataType}.32k_fs_LR_${OutName}.csv"
		rm -f ${DATACSVOutput} > /dev/null 2>&1
		wb_command -nifti-information -print-matrix "$DATAOutput" >> "$DATACSVOutput"
	fi
fi	

# -- Perform completion checks
geho "--- Checking outputs..."
echo ""
if [ -f "$DATAOutput" ]; then
	geho "Parcellated file:           $DATAOutput"
	echo ""
else
	reho "Parcellated file $DATAOutput is missing. Something went wrong."
	echo ""
	exit 1
fi

geho "--- Parcellation successfully completed"
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
