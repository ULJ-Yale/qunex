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
#  BOLDDense.sh
#
# ## LICENSE
#
# * The BOLDDense.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ## TODO
#
# --> Finish code
#
# ## DESCRIPTION 
#   
# This script, BOLDDense.sh, implements dense fc on BOLD timeseries
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * Connectome Workbench (v1.0 or above)
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./BOLDDense.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are BOLD data from previous processing
# * These data are stored in: "$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/ 
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
     echo ""
     echo "-- DESCRIPTION:"
     echo ""
     echo "This function implements dense fc on BOLD time series files."
     echo ""
     echo "-- REQUIRED PARMETERS:"
     echo ""
     echo "     --subjectsfolder=<folder_with_subjects>             Path to study folder that contains subjects"
     echo "     --subject=<list_of_cases>                           List of subjects to run"
     echo "     --inputfile=<file_to_compute_parcellation_on>       Specify the name of the file you want to use for parcellation (e.g. bold1_Atlas_MSMAll_hp2000_clean)"
     echo ""
     echo "-- OPTIONAL PARMETERS:"
     echo ""
     echo "     --overwrite=<clean_prior_run>                       Delete prior run"
     echo ""
     echo "-- Example:"
     echo ""
     echo "BOLDDense.sh --subjectsfolder='<folder_with_subjects>' \ "
     echo "--subject='<subj_id>' \ "
     echo "--inputfile='<name_of_input_file' \ "
     echo "--overwrite='no' \ "
     echo ""
     exit 0
}

# ------------------------------------------------------------------------------------------------------
# ----------------------------------------- FIX ICA CODE -----------------------------------------------
# ------------------------------------------------------------------------------------------------------

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

# -- Get the command line options for this script
get_options() {

local scriptName=$(basename ${0})
local arguments=($@)

# -- Initialize global output variables
unset SubjectsFolder
unset Subject
unset InputFile
unset InputDataType
unset Overwrite
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
            exit 0
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
        --inputfile=*)
            InputFile=${argument/*=/""}
            index=$(( index + 1 ))
            ;;              
        --inputpath=*)
            InputPath=${argument/*=/""}
            index=$(( index + 1 ))
            ;;            
        --inputdatatype=*)
            InputDataType=${argument/*=/""}
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

if [ -z ${InputFile} ]; then
    usage
    reho "ERROR: <file_to_compute_parcellation_on> not specified"
    echo ""
    exit 1
fi
if [ -z ${InputDataType} ]; then
	usage
	reho "ERROR: <type_of_dense_data_for_input_file"
	echo ""
	exit 1
fi
if [ -z ${OutName} ]; then
    usage
    reho "ERROR: <name_of_output_pconn_file> not specified"
    exit 1
fi

if [ -z ${OutPath} ]; then
    usage
    reho "ERROR: <path_for_output_file> not specified"
    exit 1
fi
if [ -z ${UseWeights} ]; then
    UseWeights="no"
    exit 1
fi

# -- Set StudyFolder
cd $SubjectsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null

# -- Report options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   SubjectsFolder: ${SubjectsFolder}"
echo "   Subject: ${CASE}"
echo "   InputFile: ${InputFile}"
echo "   OutName: ${OutName}"
echo "   InputDataType: ${InputDataType}"
echo "   Overwrite: ${Overwrite}"
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""
}

# ------------------------------------------------------------------------------------------------------
#  BOLDDense - Compute the dense connectome file for BOLD timeseries
# ------------------------------------------------------------------------------------------------------

BOLDDense() {
for STEP in $STEPS; do
	for BOLD in $BOLDS; do
		if [ -f ${SubjectsFolder}/${CASE}/images/functional/bold"$BOLD"_"$STEP".dconn.nii ]; then
			echo "Dense Connectome Computed for this for $CASE and $STEP. Skipping to next..."
		else
			echo "Running Dense Connectome on BOLD data for $CASE... (need ~30GB free RAM at any one time per subject)"
			# -- Dense connectome command - use in isolation due to RAM limits (need ~30GB free at any one time per subject)
			wb_command -cifti-correlation ${SubjectsFolder}/${CASE}/images/functional/bold"$BOLD"_"$STEP".dtseries.nii ${SubjectsFolder}/${CASE}/images/functional/bold"$BOLD"_"$STEP".dconn.nii -fisher-z -weights ${SubjectsFolder}/${CASE}/images/functional/movement/bold"$BOLD".use
		fi
	done
done
}

######################################### DO WORK ##########################################

main() {

# -- Get Command Line Options
get_options $@

# -- Define inputs and output
echo "--- Establishing paths for all input and output folders:"
echo ""

geho "--- BOLD dense fc completed. Check output log for outputs and errors."
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
