#!/bin/sh
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## Copyright Notice
#
# Copyright (C)
#
# * Yale University
#
# ## Author(s)
#
# * Alan Anticevic, N3 Division, Yale University
#
# ## Product
#
#  Wrapper for deducting dense connectome DWI data with seed input
#
# ## License
#
# * The DWIDenseSeedTractography.sh = the "Software"
# * This Software is distributed "AS IS" without warranty of any kind, either 
# * expressed or implied, including, but not limited to, the implied warranties
# * of merchantability and fitness for a particular purpose.
#
# ### TODO
#
# ## Description 
#   
# This script, DWIDenseSeedTractography.sh, implements reduction on the DWI dense connectomes 
# using a given 'seed' structure (e.g. thalamus)
# 
# ## Prerequisite Installed Software
#
# * Connectome Workbench (v1.0 or above)
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. $./DWIDenseSeedTractography.sh --help
#
# ### Expected Previous Processing
# 
# * The necessary input files are either Conn1.nii.gz or Conn3.nii.gz, both of which are results of the AP probtrackxgpudense function
# * These data are stored in: "$StudyFolder/subjects/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/ 
#
#~ND~END~


usage() {
				
				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function implements reduction on the DWI dense connectomes using a given 'seed' structure (e.g. thalamus)."
				echo "It explicitly assumes the the Human Connectome Project folder structure for preprocessing: "
				echo ""
				echo "INPUTS: <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/ ---> Dense Connectome DWI data needs to be here"
				echo ""
				echo ""
				echo "OUTPUTS: "
				echo "         <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<subject>_Conn<matrixversion>_<outname>.dconn.nii"
				echo "         --> Dense connectivity seed tractography file"
				echo ""
				echo "         <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<subject>_Conn<matrixversion>_<outname>_Avg.dscalar.nii"
				echo "         --> Dense scalar seed tractography file"
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
 				echo "		--path=<study_folder>                       Path to study data folder"
				echo "		--subject=<list_of_cases>                   List of subjects to run"
				echo "		--matrixversion=<matrix_version_value>      Matrix solution verion to run parcellation on; e.g. 1 or 3"
				echo "		--seedfile=<file_for_seed_reduction>        Specify the absolute path of the seed file you want to use as a seed for dconn reduction (e.g. <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz )"
				echo "		--outname=<name_of_output_dscalar_file>     Specify the suffix output name of the dscalar file"
				echo ""
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
 				echo "		--overwrite=<clean_prior_run>               Delete prior run for a given subject"
				echo "		--waytotal=<none,standard,log>   Use the waytotal normalized or log-transformed waytotal normalized version of the DWI dense connectome. Default: [none]"
 				echo ""
 				echo "-- Example:"
				echo ""
				echo "DWIDenseSeedTractography.sh --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--subject='100206' \ "
				echo "--matrixversion='3' \ "
				echo "--seedfile='<study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz' \ "
				echo "--overwrite='no' \ "
				echo "--outname='THALAMUS'"
				echo ""	
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

########################################## INPUTS ########################################## 

# DWI Data and T1w data needed in HCP-style format and dense DWI probtrackX should be completed
# The data should be in $DiffFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/Tractography
# Mandatory input parameters:
    # StudyFolder # e.g. /gpfs/project/fas/n3/Studies/Connectome
    # Subject	  # e.g. 100307
    # MatrixVersion # e.g. 1 or 3
    # SeedFile  # e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii
    # OutName  # e.g. THALAMUS

########################################## OUTPUTS #########################################

# Outputs will be *pconn.nii files located here:
#    DWIOutput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"

#  Get the command line options for this script
#

get_options() {
    local scriptName=$(basename ${0})
    local arguments=($@)
    
    # initialize global output variables
    unset StudyFolder
    unset Subject
    unset MatrixVersion
    unset ParcellationFile
    unset OutName
    unset Overwrite
    unset WayTotal
	unset DWIOutFileDscalar
	unset DWIOutFileDconn

    runcmd=""

    # parse arguments
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
            --path=*)
                StudyFolder=${argument/*=/""}
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

    # check required parameters
    if [ -z ${StudyFolder} ]; then
        usage
        reho "ERROR: <study-path> not specified"
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
    
    # report options
    echo ""
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo "   StudyFolder: ${StudyFolder}"
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
if [ ${WayTotal} == "none" ]; then
	echo "--- Using dconn file without waytotal normalization"
	DWIInput=`ls $StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/Conn$MatrixVersion.dconn.nii*`
	if grep "gz" $DWIInput; then
		DWIInput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/Conn$MatrixVersion.dconn.nii.gz"
	else
		DWIInput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/Conn$MatrixVersion.dconn.nii"	
	fi
	DWIOutFileDscalar="${CASE}_Conn${MatrixVersion}_${OutName}_Avg.dscalar.nii"
	DWIOutFileDconn="${CASE}_Conn${MatrixVersion}_${OutName}.dconn.nii"
fi
if [ ${WayTotal} == "standard" ]; then
	echo "--- Using waytotal normalized dconn file"
	DWIInput=`ls ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm.dconn.nii*`
	if grep "gz" $DWIInput; then
		DWIInput="${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm.dconn.nii.gz"
	else
		DWIInput="${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm.dconn.nii.nii"	
	fi
	DWIOutFileDscalar="${CASE}_Conn${MatrixVersion}_waytotnorm_${OutName}_Avg.dscalar.nii"
	DWIOutFileDconn="${CASE}_Conn${MatrixVersion}_waytotnorm_${OutName}.dconn.nii"
fi
if [ ${WayTotal} == "log" ]; then
	echo "--- Using log-transformed waytotal normalized dconn file"
	DWIInput=`ls ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm_log.dconn.nii*`
	if grep "gz" $DWIInput; then
		DWIInput="${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm_log.dconn.nii.gz"
	else
		DWIInput="${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm_log.dconn.nii.nii"	
	fi
	DWIOutFileDscalar="${CASE}_Conn${MatrixVersion}_waytotnorm_log_${OutName}_Avg.dscalar.nii"
	DWIOutFileDconn="${CASE}_Conn${MatrixVersion}_waytotnorm_log_${OutName}.dconn.nii"
fi

# -- Define output directory
DWIOutput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"

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

# -- Perform completion checks"
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

exit 1

}	

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
