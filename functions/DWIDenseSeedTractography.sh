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
#  DWIDenseSeedTractography.sh 
#
# ## LICENSE
#
# * The DWIDenseSeedTractography.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ## TODO
#
# ## DESCRIPTION 
#
# This script, DWIDenseSeedTractography.sh, is a wrapper for deducting dense 
# connectome DWI data with seed input. It implements reduction on the DWI dense 
# connectomes using a given 'seed' structure (e.g. thalamus)
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * Connectome Workbench (v1.0 or above)
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./DWIDenseSeedTractography.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are either Conn1.nii.gz or Conn3.nii.gz, both of which are results of the AP probtrackxgpudense function
# * These data are stored in: "$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/ 
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
    echo ""
    echo "-- DESCRIPTION:"
    echo ""
    echo "This function implements reduction on the DWI dense connectomes using a given 'seed' structure (e.g. thalamus)."
    echo "It explicitly assumes the the Human Connectome Project folder structure for preprocessing: "
    echo ""
    echo "INPUTS: <folder_with_subjects>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/ ---> Dense Connectome DWI data needs to be here"
    echo ""
    echo ""
    echo "OUTPUTS: "
    echo "         <folder_with_subjects>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<subject>_Conn<matrixversion>_<outname>.dconn.nii"
    echo "         --> Dense connectivity seed tractography file"
    echo ""
    echo "         <folder_with_subjects>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<subject>_Conn<matrixversion>_<outname>_Avg.dscalar.nii"
    echo "         --> Dense scalar seed tractography file"
    echo ""
    echo "-- REQUIRED PARMETERS:"
    echo ""
    echo "     --subjectsfolder=<folder_with_subjects>                       Path to study data folder"
    echo "     --subject=<list_of_cases>                   List of subjects to run"
    echo "     --matrixversion=<matrix_version_value>      Matrix solution verion to run parcellation on; e.g. 1 or 3"
    echo "     --seedfile=<file_for_seed_reduction>        Specify the absolute path of the seed file you want to use as a seed for dconn reduction (e.g. <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz )"
    echo "     --outname=<name_of_output_dscalar_file>     Specify the suffix output name of the dscalar file"
    echo ""
    echo "-- OPTIONAL PARMETERS:"
    echo "" 
    echo "     --overwrite=<clean_prior_run>               Delete prior run for a given subject"
    echo "     --waytotal=<none,standard,log>   Use the waytotal normalized or log-transformed waytotal normalized version of the DWI dense connectome. Default: [none]"
    echo ""
    echo "-- Example:"
    echo ""
    echo "DWIDenseSeedTractography.sh --subjectsfolder='<folder_with_subjects>' \ "
    echo "--subject='<case_id>' \ "
    echo "--matrixversion='3' \ "
    echo "--seedfile='<folder_with_subjects>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz' \ "
    echo "--overwrite='no' \ "
    echo "--outname='THALAMUS'"
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
# -- Parse arguments
# ------------------------------------------------------------------------------

########################################## INPUTS ########################################## 

# DWI Data and T1w data needed in HCP-style format and dense DWI probtrackX should be completed
# The data should be in $DiffFolder="$SubjectsFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/Tractography
# Mandatory input parameters:
    # SubjectsFolder # e.g. /gpfs/project/fas/n3/Studies/Connectome/subjects
    # Subject	  # e.g. 100307
    # MatrixVersion # e.g. 1 or 3
    # SeedFile  # e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii
    # OutName  # e.g. THALAMUS

########################################## OUTPUTS #########################################

# -- Outputs will be *pconn.nii files located here:
#    DWIOutput="$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"

# -- Get the command line options for this script

get_options() {

local scriptName=$(basename ${0})
local arguments=($@)

# -- Initialize global output variables
unset SubjectsFolder
unset Subject
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
        --subjectsfolder=*)
            SubjectsFolder=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --subject=*)
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
cd $SubjectsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null
    
# -- Report options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   SubjectsFolder: ${SubjectsFolder}"
echo "   Subject: ${CASE}"
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
reho "--- Establishing paths for all input and output folders:"
echo ""

# -- Define input and check if WayTotal normalization is selected
if [ ${WayTotal} == "standard" ]; then
	echo "--- Using waytotal normalized dconn file"
	DWIInput=`ls ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm.dconn.nii*`
	if [ $(echo $DWIInput | grep -c gz) -eq 1 ]; then
		DWIInput="${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm.dconn.nii.gz"
	else
		DWIInput="${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm.dconn.nii"	
	fi
	DWIOutFileDscalar="${CASE}_Conn${MatrixVersion}_waytotnorm_${OutName}_Avg.dscalar.nii"
	DWIOutFileDconn="${CASE}_Conn${MatrixVersion}_waytotnorm_${OutName}.dconn.nii"
elif [ ${WayTotal} == "log" ]; then
	echo "--- Using log-transformed waytotal normalized dconn file"
	DWIInput=`ls ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm_log.dconn.nii*`
	if [ $(echo $DWIInput | grep -c gz) -eq 1 ]; then
		DWIInput="${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm_log.dconn.nii.gz"
	else
		DWIInput="${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm_log.dconn.nii"	
	fi
	DWIOutFileDscalar="${CASE}_Conn${MatrixVersion}_waytotnorm_log_${OutName}_Avg.dscalar.nii"
	DWIOutFileDconn="${CASE}_Conn${MatrixVersion}_waytotnorm_log_${OutName}.dconn.nii"
elif ! { [ "${WayTotal}" = "log" ] || [ "${WayTotal}" = "standard" ]; }; then
	echo "--- Using dconn file without waytotal normalization"
	DWIInput=`ls $SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/Conn${MatrixVersion}.dconn.nii*`
	if [ $(echo $DWIInput | grep -c gz) -eq 1 ]; then
		DWIInput="$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/Conn${MatrixVersion}.dconn.nii.gz"
	else
		DWIInput="$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/Conn${MatrixVersion}.dconn.nii"	
	fi
	DWIOutFileDscalar="${CASE}_Conn${MatrixVersion}_${OutName}_Avg.dscalar.nii"
	DWIOutFileDconn="${CASE}_Conn${MatrixVersion}_${OutName}.dconn.nii"
fi

# -- Define output directory
DWIOutput="$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"
echo "--- Dense DWI Connectome Input:          ${DWIInput}"
echo "--- Parcellated DWI Connectome Output:   ${DWIOutput}/${DWIOutFileDscalar}"
echo ""

# -- Delete any existing output sub-directories
if [ "$Overwrite" == "yes" ]; then
	reho "--- Deleting prior runs in $DWIOutput..."
	echo ""
	rm -f ${DWIOutput}/${DWIOutFileDconn} > /dev/null 2>&1
	rm -f ${DWIOutput}/${DWIOutFileDscalar} > /dev/null 2>&1
fi

# -- Check if the dense parcellation was completed and exists
reho "--- Checking if parcellation was completed..."
echo ""
# -- Check if file present
if [ -f ${DWIOutput}/${DWIOutFileDscalar} ]; then
	geho "--- Dense scalar seed tractography data found: "
	echo ""
	echo "      ${DWIOutput}/${DWIOutFileDscalar}"
	echo ""
	exit 1
else
	reho "--- Dense scalar seed tractography data not found."
	echo ""
	geho "--- Computing dense DWI connectome restriction by COLUMN on $DWIInput..."
	echo ""
	# -- First restrict by COLUMN and save a *dconn file
	wb_command -cifti-restrict-dense-map ${DWIInput} COLUMN ${DWIOutput}/${DWIOutFileDconn} -vol-roi ${SeedFile}
	geho "--- Computing average of the restricted dense connectome across the input structure $SeedFile..."
	echo ""
	# -- Next average the restricted dense connectome across the input structure and save the dscalar
	wb_command -cifti-average-dense-roi ${DWIOutput}/${DWIOutFileDscalar} -cifti ${DWIOutput}/${DWIOutFileDconn} -vol-roi ${SeedFile}
fi	

# -- Perform completion checks
reho "--- Checking outputs..."
echo ""
if [ -f ${DWIOutput}/${DWIOutFileDconn} ]; then
	geho "--- Dense connectivity seed tractography file for Matrix $MatrixVersion:     ${DWIOutput}/${DWIOutFileDconn}"
	echo ""
else
	reho "--- Dense connectivity seed tractography file for Matrix $MatrixVersion is missing. Something went wrong."
	echo ""
	exit 1
fi

if [ -f ${DWIOutput}/${DWIOutFileDscalar} ]; then
	geho "--- Dense scalar seed tractography file for Matrix $MatrixVersion:     ${DWIOutput}/${DWIOutFileDconn}"
	echo ""
else
	reho "--- Dense scalar seed tractography file for Matrix $MatrixVersion is missing. Something went wrong."
	echo ""
	exit 1
fi

reho "--- DWI seed restriction of dense connectome successfully completed"
echo ""
geho "------------------------- End of work --------------------------------"
echo ""
}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
