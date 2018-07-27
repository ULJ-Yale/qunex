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
#  FIXICA.sh
#
# ## LICENSE
#
# * The FIXICA.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ## TODO
#
# --> Finish code
#
# ## DESCRIPTION 
#   
# This script, FIXICA.sh, implements FIXICA on BOLD data
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * Connectome Workbench (v1.0 or above)
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./FIXICA.sh --help
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
     echo "This function implements FIX ICA on the BOLD dense files."
     echo ""
     echo "-- REQUIRED PARMETERS:"
     echo ""
     echo "     --subjectsfolder=<folder_with_subjects>             Path to study folder that contains subjects"
     echo "     --subject=<list_of_cases>                           List of subjects to run"
     echo "     --inputfile=<file_to_compute_parcellation_on>       Specify the name of the file you want to use for parcellation (e.g. bold1_Atlas_MSMAll_hp2000_clean)"
     echo "     --inputdatatype=<type_of_dense_data_for_input_file> Specify the type of data for the input file (e.g. dscalar or dtseries)"
     echo ""
     echo "-- OPTIONAL PARMETERS:"
     echo ""
     echo "     --overwrite=<clean_prior_run>                       Delete prior run"
     echo ""
     echo "-- Example:"
     echo ""
     echo "FIXICA.sh --subjectsfolder='<folder_with_subjects>' \ "
     echo "--subject='<subj_id>' \ "
     echo "--inputfile='<name_of_input_file' \ "
     echo "--inputdatatype='<type_of_dense_data_for_input_file>' \ "
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
#  linkMovement - Sets hard links for BOLDs into Parcellated folder for FIXICA use
# ------------------------------------------------------------------------------------------------------

linkMovement() {
for BOLD in $BOLDS; do
	echo "Linking scrubbing data - BOLD $BOLD for $CASE..."
	ln -f ${SubjectsFolder}/${CASE}/images/functional/movement/bold"$BOLD".use ${SubjectsFolder}/../Parcellated/BOLD/${CASE}_bold"$BOLD".use
	ln -f ${SubjectsFolder}/${CASE}/images/functional/movement/boldFIXICA"$BOLD".use ${SubjectsFolder}/../Parcellated/BOLD/${CASE}_boldFIXICA"$BOLD".use
done
}

# ------------------------------------------------------------------------------------------------------
#  FIXICA - Compute FIX ICA cleanup on BOLD timeseries following hcp pipelines
# ------------------------------------------------------------------------------------------------------

FIXICA() {
for BOLD in $BOLDS; do
		if [ "$Overwrite" == "yes" ]; then
			rm -r ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD"*_hp2000*  &> /dev/null
		fi
		if [ -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas_hp2000_clean.dtseries.nii ]; then
				echo "FIX ICA Computed for this for $CASE and $BOLD. Skipping to next..."
		else
			echo "Running FIX ICA on $BOLD data for $CASE... (note: this uses Melodic which is a slow single-threaded process)"
			rm -r *hp2000* &> /dev/null
			"$FIXICADIR"/hcp_fix.sh ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD".nii.gz 2000
		fi
done
}

# ------------------------------------------------------------------------------------------------------
#  postFIXICA - Compute PostFix code on FIX ICA cleaned BOLD timeseries to generate scene files
# ------------------------------------------------------------------------------------------------------

postFIXICA() {
for BOLD in $BOLDS; do
	if [ "$Overwrite" == "yes" ]; then
			rm -r ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/${CASE}_"$BOLD"_ICA_Classification_singlescreen.scene   &> /dev/null
		fi
		if [ -f  ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/${CASE}_"$BOLD"_ICA_Classification_singlescreen.scene ]; then
				echo "PostFix Computed for this for $CASE and $BOLD. Skipping to next..."
	else
				echo "Running PostFix script on $BOLD data for $CASE... "
				"$POSTFIXICADIR"/GitRepo/PostFix.sh ${SubjectsFolder}/${CASE}/hcp ${CASE} "$BOLD" /usr/local/PostFix_beta/GitRepo "$HighPass" wb_command /usr/local/PostFix_beta/GitRepo/PostFixScenes/ICA_Classification_DualScreenTemplate.scene /usr/local/PostFix_beta/GitRepo/PostFixScenes/ICA_Classification_SingleScreenTemplate.scene
	fi
done
}

# ------------------------------------------------------------------------------------------------------
#  BOLDHardLinkFIXICA - Generate links for FIX ICA cleaned BOLDs for functional connectivity (dofcMRI)
# ------------------------------------------------------------------------------------------------------

BOLDHardLinkFIXICA() {
BOLDCount=0
for BOLD in $BOLDS
	do
		BOLDCount=$((BOLDCount+1))
		echo "Setting up hard links following FIX ICA for BOLD# $BOLD for $CASE... "
		# -- Setup folder strucrture if missing
		mkdir ${SubjectsFolder}/${CASE}/images    &> /dev/null
		mkdir ${SubjectsFolder}/${CASE}/images/functional	    &> /dev/null
		mkdir ${SubjectsFolder}/${CASE}/images/functional/movement    &> /dev/null
		# -- Setup hard links for images
		rm ${SubjectsFolder}/${CASE}/images/functional/boldFIXICA"$BOLD".dtseries.nii     &> /dev/null
		rm ${SubjectsFolder}/${CASE}/images/functional/boldFIXICA"$BOLD".nii.gz     &> /dev/null
		ln -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas_hp2000_clean.dtseries.nii ${SubjectsFolder}/${CASE}/images/functional/boldFIXICA"$BOLD".dtseries.nii
		ln -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD"_hp2000_clean.nii.gz ${SubjectsFolder}/${CASE}/images/functional/boldFIXICA"$BOLD".nii.gz
		ln -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas.dtseries.nii ${SubjectsFolder}/${CASE}/images/functional/bold"$BOLD".dtseries.nii
		ln -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD".nii.gz ${SubjectsFolder}/${CASE}/images/functional/bold"$BOLD".nii.gz
		#rm ${SubjectsFolder}/${CASE}/images/functional/boldFIXICArfMRI_REST*     &> /dev/null
		#rm ${SubjectsFolder}/${CASE}/images/functional/boldrfMRI_REST*     &> /dev/null
		echo "Setting up hard links for movement data for BOLD# $BOLD for $CASE... "
		# -- Clean up movement regressor file to match dofcMRIp convention and copy to movement directory
		export PATH=/usr/local/opt/gnu-sed/libexec/gnubin:$PATH     &> /dev/null
		rm ${SubjectsFolder}/${CASE}/images/functional/movement/boldFIXICA"$BOLD"_mov.dat     &> /dev/null
		rm ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit*     &> /dev/null
		cp ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors.txt ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit.txt
		sed -i.bak -E 's/.{67}$//' ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit.txt
		nl ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit.txt > ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit_fin.txt
		sed -i.bak '1i\#frame     dx(mm)     dy(mm)     dz(mm)     X(deg)     Y(deg)     Z(deg)' ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"//Movement_Regressors_edit_fin.txt
		cp ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit_fin.txt ${SubjectsFolder}/${CASE}/images/functional/movement/boldFIXICA"$BOLD"_mov.dat
		rm ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit*     &> /dev/null
done
}

# ------------------------------------------------------------------------------------------------------
#  FIXICAInsertMean - Re-insert means into FIX ICA cleaned BOLDs for connectivity preprocessing (dofcMRI)
# ------------------------------------------------------------------------------------------------------

FIXICAInsertMean() {
for BOLD in $BOLDS; do
	cd ${SubjectsFolder}/${CASE}/images/functional/
	# -- First check if the boldFIXICA file has the mean inserted
	3dBrickStat -mean -non-zero boldFIXICA"$BOLD".nii.gz[1] >> boldFIXICA"$BOLD"_mean.txt
	ImgMean=`cat boldFIXICA"$BOLD"_mean.txt`
	if [ $(echo " $ImgMean > 1000" | bc) -eq 1 ]; then
	echo "1st frame mean=$ImgMean Mean inserted OK for subject $CASE and bold# $BOLD. Skipping to next..."
		else
		# -- Next check if the boldFIXICA file has the mean inserted twice by accident
		if [ $(echo " $ImgMean > 15000" | bc) -eq 1 ]; then
		echo "1st frame mean=$ImgMean ERROR: Mean has been inserted twice for $CASE and $BOLD."
			else
			# -- Command that inserts mean image back to the boldFIXICA file using g_InsertMean matlab function
			echo "Re-inserting mean image on the mapped $BOLD data for $CASE... "
			${MNAPMCOMMAND} "g_InsertMean(['bold' num2str($BOLD) '.dtseries.nii'], ['boldFIXICA' num2str($BOLD) '.dtseries.nii']),g_InsertMean(['bold' num2str($BOLD) '.nii.gz'], ['boldFIXICA' num2str($BOLD) '.nii.gz']),quit()"
		fi
	fi
	rm boldFIXICA"$BOLD"_mean.txt &> /dev/null
done
}
# ------------------------------------------------------------------------------------------------------
#  FIXICARemoveMean - Remove means from FIX ICA cleaned BOLDs for functional connectivity analysis
# ------------------------------------------------------------------------------------------------------

FIXICARemoveMean() {
for BOLD in $BOLDS; do
	cd ${SubjectsFolder}/${CASE}/images/functional/
	# First check if the boldFIXICA file has the mean inserted
	#3dBrickStat -mean -non-zero boldFIXICA"$BOLD".nii.gz[1] >> boldFIXICA"$BOLD"_mean.txt
	#ImgMean=`cat boldFIXICA"$BOLD"_mean.txt`
	#if [ $(echo " $ImgMean < 1000" | bc) -eq 1 ]; then
	#echo "1st frame mean=$ImgMean Mean removed OK for subject $CASE and bold# $BOLD. Skipping to next..."
	#	else
		# Next check if the boldFIXICA file has the mean inserted twice by accident
	#	if [ $(echo " $ImgMean > 15000" | bc) -eq 1 ]; then
	#	echo "1st frame mean=$ImgMean ERROR: Mean has been inserted twice for $CASE and $BOLD."
	#		else
			# Command that inserts mean image back to the boldFIXICA file using g_InsertMean matlab function
			echo "Removing mean image on the mapped CIFTI FIX ICA $BOLD data for $CASE... "
			${MNAPMCOMMAND} "g_RemoveMean(['bold' num2str($BOLD) '.dtseries.nii'], ['boldFIXICA' num2str($BOLD) '.dtseries.nii'], ['boldFIXICA_demean' num2str($BOLD) '.dtseries.nii']),quit()"
		#fi
	#fi
	#rm boldFIXICA"$BOLD"_mean.txt &> /dev/null
done
}

######################################### DO WORK ##########################################

main() {

# -- Get Command Line Options
get_options $@

# -- Define inputs and output
echo "--- Establishing paths for all input and output folders:"
echo ""

geho "--- FIX ICA completed. Check output log for outputs and errors."
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
