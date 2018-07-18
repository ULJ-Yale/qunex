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
# * Alan Anticevic, Department of Psychiatry, Yale University
#
# ## PRODUCT
#
#  StructuralParcellation.sh
#
# ## LICENSE
#
# * The StructuralParcellation.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ## TODO
#
# ## DESCRIPTION 
#   
# This script, StructuralParcellation.sh, implements parcellation structural data 
# such as dense thickness and myelin maps.
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * Connectome Workbench (v1.0 or above)
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./StructuralParcellation.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are thickness or myelin data from previous processing
# * These data are stored in: "$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/fsaverage_LR32k/ 
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
 echo ""
 echo "-- DESCRIPTION:"
 echo ""
 echo "This function implements parcellation on the dense cortical thickness OR myelin files using a whole-brain parcellation (e.g. Glasser parcellation with subcortical labels included)."
 echo ""
 echo ""
 echo "-- REQUIRED PARMETERS:"
 echo ""
 echo "    --subjectsfolder=<folder_with_subjects>               Path to study data folder"
 echo "    --subject=<list_of_cases>                             List of subjects to run"
 echo "    --inputdatatype=<type_of_dense_data_for_input_file>   Specify the type of data for the input file (e.g. MyelinMap_BC or corrThickness)"
 echo "    --parcellationfile=<dlabel_file_for_parcellation>     Specify the absolute path of the file you want to use for parcellation"
 echo "    --outname=<name_of_output_pconn_file>                 Specify the suffix output name of the pconn file"
 echo ""
 echo "-- OPTIONAL PARMETERS:"
 echo "" 
 echo "    --overwrite=<clean_prior_run>                         Delete prior run for a given subject"
 echo "    --extractdata=<save_out_the_data_as_as_csv>           Specify if you want to save out the matrix as a CSV file"
 echo ""
 echo "-- Example:"
 echo ""
 echo "MyelinThicknessParcellation.sh --subjectsfolder='<folder_with_subjects>' \ "
 echo "--subject='<case_id>' \ "
 echo "--inputdatatype='MyelinMap_BC' \ "
 echo "--parcellationfile='<dlabel_file_for_parcellation>' \ "
 echo "--overwrite='no' \ "
 echo "--extractdata='yes' \ "
 echo "--outname='<name_of_output_pconn_file>' "
 echo ""
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
unset SubjectsFolder
unset Subject
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
if [ -z ${SubjectsFolder} ]; then
    usage
    reho "ERROR: <subjects-folder-path> not specified>"
    echo ""
    exit 1
fi
if [ -z ${CASE} ]; then
    usage
    reho "ERROR: <subject-id> not specified>"
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
cd $SubjectsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null

# -- Report options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   SubjectsFolder: ${SubjectsFolder}"
echo "   Subject: ${CASE}"
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
DATAInput="$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/fsaverage_LR32k/$CASE.${InputDataType}.32k_fs_LR.${InputFileExt}"
# -- Define output
DATAOutput="$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/fsaverage_LR32k/$CASE.${InputDataType}.32k_fs_LR_${OutName}.${OutFileExt}"
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
		DATACSVOutput="$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/fsaverage_LR32k/$CASE.${InputDataType}.32k_fs_LR_${OutName}.csv"
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
geho "------------------------- Successful end of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
