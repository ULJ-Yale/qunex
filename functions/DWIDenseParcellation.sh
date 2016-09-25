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
# * Murat Demirtas, N3 Division, Yale University
#
# ## Product
#
#  Parcellation wrapper for dense connectome DWI data
#
# ## License
#
# * The DWIDenseParcellation = the "Software"
# * This Software is distributed "AS IS" without warranty of any kind, either 
# * expressed or implied, including, but not limited to, the implied warranties
# * of merchantability and fitness for a particular purpose.
#
# ### TODO
#
# ## Description 
#   
# This script, DWIDenseParcellation.sh, implements parcellation on the DWI dense connectomes 
# using a whole-brain parcellation (e.g.Glasser parcellation with subcortical labels included)
# 
# ## Prerequisite Installed Software
#
# * Connectome Workbench (v1.0 or above)
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. $./DWIDenseParcellation.sh --help
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
				echo "This function implements parcellation on the DWI dense connectomes using a whole-brain parcellation (e.g.Glasser parcellation with subcortical labels included)."
				echo "It explicitly assumes the the Human Connectome Project folder structure for preprocessing: "
				echo ""
				echo " <study_folder>/<case>/hcp/<case>/MNINonLinear/Tractography/ ---> Dense Connectome DWI data needs to be here"
				echo ""
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
 				echo "		--path=<study_folder>				Path to study data folder"
				echo "		--subject=<list_of_cases>			List of subjects to run"
				echo "		--matrixversion=<matrix_version_value>		matrix solution verion to run parcellation on; e.g. 1 or 3"
				echo "		--parcellationfile=<file_for_parcellation>	Specify the absolute path of the file you want to use for parcellation"
				echo ""
				#echo "-- OPTIONAL PARMETERS:"
				#echo "" 
 				#echo "		--overwrite=<clean_prior_run>		Delete prior run for a given subject"
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
    # ParcellationFile  # e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii"

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
    unset Overwrite
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
                exit 0
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
            --parcellationfile=*)
                ParcellationFile=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --overwrite=*)
                Overwrite=${argument/*=/""}
                index=$(( index + 1 ))
                ;;      
            *)
                usage
                reho "ERROR: Unrecognized Option: ${argument}"
                exit 1
                ;;
        esac
    done

    # check required parameters
    if [ -z ${StudyFolder} ]; then
        usage
        reho "ERROR: <study-path> not specified"
        exit 1
    fi

    if [ -z ${CASE} ]; then
        usage
        reho "ERROR: <subject-id> not specified"
        exit 1
    fi

    if [ -z ${MatrixVersion} ]; then
        usage
        reho "ERROR: <phase-encoding-dir> not specified"
        exit 1
    fi

    if [ -z ${ParcellationFile} ]; then
        usage
        reho "ERROR: <echo-spacing> not specified"
        exit 1
    fi

    # report options
    echo ""
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo "   StudyFolder: ${StudyFolder}"
    echo "   Subject: ${CASE}"
    echo "   MatrixVersion: ${MatrixVersion}"
    echo "   ParcellationFile: ${ParcellationFile}"
    echo "   Overwrite: ${Overwrite}"
    echo "-- ${scriptName}: Specified Command-Line Options - End --"
    echo ""
    geho "------------------------- Start of work --------------------------------"
    echo ""
}

######################################### DO WORK ##########################################

main() {

    # Get Command Line Options
    get_options $@

# -- Define input
DWIInput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/Conn$MatrixVersion.dconn.nii.gz"
# -- Define output
DWIOutput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"
# -- Define cases to work on

# -- First parcellate by COLUMN and save a *pdconn file
wb_command -cifti-parcellate "$DWIInput" "$ParcellationFile" COLUMN "$DWIOutput"/Conn"$MatrixVersion".pdconn.nii
# -- Next parcellate by ROW and save final *pconn file
wb_command -cifti-parcellate "$DWIOutput"/Conn3.pdconn.nii "$ParcellationFile" ROW "$DWIOutput"/Conn"$MatrixVersion".pconn.nii
	
exit 1

# Perform completion checks"

	reho "--- Checking outputs..."
	echo ""
	if [ -f "$DWIOutput"/Conn3.pdconn.nii "$ParcellationFile" ROW "$DWIOutput"/Conn"$MatrixVersion".pconn.nii ]; then
		OutFile="$DWIOutput"/Conn3.pdconn.nii "$ParcellationFile" ROW "$DWIOutput"/Conn"$MatrixVersion".pconn.nii
		geho "Parcellated (pconn) file for Matrix $MatrixVersion:           $OutFile"
		echo ""
	else
		reho "Parcellated (pconn) file for Matrix $MatrixVersion is missing. Something went wrong."
		echo ""
		exit 1
	fi
	
	reho "--- DWI Parcellation successfully completed"
	echo ""
    geho "------------------------- End of work --------------------------------"

}	

#
# Invoke the main function to get things started
#
main $@
