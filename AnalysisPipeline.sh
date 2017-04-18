#!/bin/sh 
#set -x

## --> PENDING GENERAL TASKS:
## ------------------------------------------------------------------------------------------------------------------------------------------
##
## --> Make sure to document adjustments to diffusion connectome code for GPU version [e.g. omission of matrixes etc.]
## --> Integrate log generation for each function and build IF statement to override log generation if nolog flag [In progress]
## --> Issue w/logging - the exec function effectively double-logs everything for each case and for the whole command
## --> Finish autoptx function
## --> Add MYELIN or THICKNESS parcellation functions as with boldparcellation and dwidenseparcellation
## --> Write function / wrapper for StarCluster deployment
## --> printmatrix needs to be updated to work with any input parcellation
## --> isolatethalamusfslnuclei needs to be finished to get atlas-based ROIs
## --> boldmergecifti & boldmergenifti need to be updated and made more general; perhaps rely on concatenation files?
## --> boldseparateciftifixica needs to be updated
##
## ------------------------------------------------------------------------------------------------------------------------------------------
## ---->  Full Automation of Preprocessing Effort (work towards turn-key solution)
## ------------------------------------------------------------------------------------------------------------------------------------------
##
##	- Sync to Grace crontab job -- DONE
## 	- Rsync to subject folder based on acquisition log -- IN PROGRESS (Charlie)
##	--dicomsort if data complete w/o error -- IN PROGRESS (Charlie)
##  - Generate subject_hcp.txt -- IF 0 ERR then RUN; ELSE ABORT -- IN PROGRESS
##	--setuphcp
##	--createlist to Generate parameter file
##	--hcp1 --> setup checkpoints
##	--hcp2 --> setup checkpoints
##	--hcp3 --> setup checkpoints
##	--hcp4 --> setup checkpoints
##	--hcp5 --> setup checkpoints
##	--hcpd or --hcpdlegacy --> setup checkpoints
##	--qcpreproc (DWI, BOLD, T1w, T2w, myelin)
##	--fixica å
##	--postfix 
##	--mapHCPData 
##	--createBOLDBrainMasks 
##	--computeBOLDStats 
##	--createStatsReport 
##	--extractNuisanceSignal 
##	--preprocessBold 
##	--preprocessConc 
##	--fsldtifit 
##	--fslbedpostxgpu 
##	--pretractography 
##	--pretractographydense 
##	--probtrackxgpudense 
##	--boldparcellation 
##	--dwidenseparcellation
##
## ------------------------------------------------------------------------------------------------------------------------------------------
## --> BITBUCKET INFO:
## ------------------------------------------------------------------------------------------------------------------------------------------
## GitRepo for MNAP pipelines: https://bitbucket.org/mnap/
## GitRepo for general pipeline wrapper: https://bitbucket.org/mnap/general
## ------------------------------------------------------------------------------------------------------------------------------------------

#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# # AnalysisPipeline.sh
#
# ## Copyright Notice
#
# Copyright (C) 2015 Anticevic Lab 
# Copyright (C) 2015 MBLAB 
#
# * Yale University
# * University of Ljubljana
#
# ## Author(s)
#
# * Alan Anticevic, Department of Psychiatry, Yale University
# * Grega Repovs , Department of Psychology,  University of Ljubljana
#
# ## Product
#
# * Analysis Pipelines for the general neuroimaging workflow and bash wrapper for MNAP
#
# ## License
#
# See the [LICENSE](https://bitbucket.org/mnap/general/LICENSE.md) file
#
# ## Description:
#
# * This is a general lab pipeline developed as for front-end organization prior to HCP pipelines, for running HCP pipelines functions, and back-end analysis following dofcMRI
#
# ### Installed Software (Prerequisites) - these are sourced in $TOOLS/hcpsetup.sh 
#
# * Connectome Workbench (v1.0 or above)
# * FSL (version 5.0.6 or above)
# * MATLAB (version 2012b or above)
# * FIX ICA
# * MNAP (all repositories)
# * PALM
# * Python (version 2.7 or above)
# * AFNI
# * Gradunwarp
# * HCP Pipelines modified code for legacy BOLD data
# * R Software library
#
# ### Expected Environment Variables
#
# * HCPPIPEDIR
# * CARET7DIR
# * FSLDIR
#
# ### Expected Previous Processing
# 
# * The necessary input files for higher-level analyses come from HCP pipelines and/or dofcMRI
#
#~ND~END~

# ===============================================================================================================================
# ================================================== CODE START  ================================================================
# ===============================================================================================================================

# ------------------------------------------------------------------------------
#  Setup color outputs
# ------------------------------------------------------------------------------

BLACK_F="\033[30m"; BLACK_B="\033[40m"
RED_F="\033[31m"; RED_B="\033[41m"
GREEN_F="\033[32m"; GREEN_B="\033[42m"
YELLOW_F="\033[33m"; YELLOW_B="\033[43m"
BLUE_F="\033[34m"; BLUE_B="\033[44m"
MAGENTA_F="\033[35m"; MAGENTA_B="\033[45m"
CYAN_F="\033[36m"; CYAN_B="\033[46m"
WHITE_F="\033[37m"; WHITE_B="\033[47m"

reho() {
    echo -e "$RED_F $1 \033[0m"
}

geho() {
    echo -e "$GREEN_F $1 \033[0m"
}

yeho() {
    echo -e "$YELLOW_F $1 \033[0m"
}

beho() {
    echo -e "$BLUE_F $1 \033[0m"
}

mageho() {
    echo -e "$MAGENTA_F $1 \033[0m"
}

cyaneho() {
    echo -e "$CYAN_F $1 \033[0m"
}

weho() {
    echo -e "$WHITE_F $1 \033[0m"
}


# ------------------------------------------------------------------------------
#  General usage function
# ------------------------------------------------------------------------------

show_usage() {
  				echo ""
  				cyaneho "General help for MNAP analysis pipeline"
  				cyaneho "================================================================================"
  				echo ""
  				echo "* interactive usage:"
  				echo "ap <command> <study_folder> '<list of cases>' [options]"
  				echo ""
  				echo "* flagged usage:"
  				echo "ap --function=<command> --studyfolder=<study_folder> \ " 
  				echo "--subjects='<list of cases>' [options]"  				 
  				echo ""
  				echo "* interactive example (no flags):"
  				echo "ap dicomsort /some/path/to/study/subjects '100001 100002'"
  				echo ""
  				echo "* flagged example (no interactive terminal input):"
  				echo "ap --function=dicomsort \ "
  				echo "--studyfolder=/some/path/to/study/subjects \ "
  				echo "--subjects='100001,100002'"
  				echo ""
  				echo "* function-specific help and usage:"
  				echo "ap -<command>   OR   ap ?<command>"
  				echo ""
  				echo ""
  				echo "* Square brackets []: Specify a value that is optional."
  				echo "			Note: Value within brackets is the default value."
  				echo "* Angle brackets <>: Contents describe what should go there."
				echo "* Dashes or flags -- : Define input variables."
				echo "* All descriptions use regular case and all options use CAPS"
  				echo ""
  				echo ""
  				echo "Note: All gmri functions are supported and take the list of arguments."
  				echo ""
  				echo ""
  				cyaneho "List of specific supported functions"
  				cyaneho "================================================================================"
  				echo ""  				
  				cyaneho "Data organization functions"
  				cyaneho "----------------------------"
  				echo "dicomsort		sort dicoms and setup nifti files from dicoms"
  				echo "dicom2nii		convert dicoms to nifti files"
  				echo "setuphcp		setup data structure for hcp processing"
  				echo "createlists		setup subject lists for preprocessing or analyses"
  				echo "hpcsync			sync with hpc cluster(s) for preprocessing"
  				echo "awshcpsync		sync hcp data from aws s3 cloud"
  				echo ""  				
  				echo ""
  				cyaneho "HCP Pipelines original calls directly from HCP code (deprecated in 2017)"
  				cyaneho "------------------------------------------------------------------------"
  				echo "hcp1_orig		prefreesurfer component of the hcp pipeline (cluster usable)"
  				echo "hcp2_orig		freesurfer component of the hcp pipeline (cluster usable)"
  				echo "hcp3_orig		postfreesurfer component of the hcp pipeline (cluster usable)"
  				echo "hcp4_orig		volume component of the hcp pipeline (cluster usable)"
  				echo "hcp5_orig		surface component of the hcp pipeline (cluster usable)"
  				echo "hcpd_orig		dwi component of the hcp pipeline (cluster usable)"
  				echo ""
  				cyaneho "QC and Misc processing functions"
  				cyaneho "--------------------------------"
  				echo "qcpreproc		run visual qc for a given modality (t1w,tw2,myelin,bold,dwi)"
  				echo ""  				
  				cyaneho "DWI processing, analyses & probabilistic tractography functions"
  				cyaneho "----------------------------------------------------------------"
  				echo "hcpdlegacy			dwi processing for data with standard fieldmaps (cluster usable)"
  				echo "fsldtifit 			run fsl dtifit (cluster usable)"
  				echo "fslbedpostxgpu 			run fsl bedpostx w/gpu (cluster usable)"
  				echo "isolatesubcortexrois 		isolate subject-specific subcortical rois for tractography"
  				echo "probtracksubcortex 		run fsl probtrackx across subcortical nuclei (cpu) (deprecated for probtrackxgpudense & dwiseedtractography)"
  				echo "pretractography			generates space for cortical dense connectomes (cluster usable)"
  				echo "pretractographydense		generates space for whole-brain dense connectomes (cluster usable)"
  				echo "probtrackxgpucortex		run fsl probtrackx across cortical mesh for dense connectomes w/gpu (cluster usable)"
  				echo "makedensecortex			generate dense cortical connectomes (cluster usable)"
  				echo "probtrackxgpudense		run fsl probtrackx for whole brain & generates dense whole-brain connectomes (cluster usable)"
  				echo ""  				
  				cyaneho "Misc functions and analyses"  	
  				cyaneho "---------------------------"			
  				echo "structuralparcellation		parcellate myelin or thickness data via user-specified parcellation"
  				echo "boldparcellation		parcellate bold data and generate pconn files via user-specified parcellation"
  				echo "dwidenseparcellation		parcellate dense dwi tractography data via user-specified parcellation"
  				echo "dwiseedtractography		reduce dense dwi tractography data via user-specified seed structure"
  				echo "printmatrix			extract parcellated matrix for bold data via yeo 17 network solutions"
  				echo "boldmergenifti			merge specified nii bold timeseries"
  				echo "boldmergecifti			merge specified citi bold timeseries"
  				echo "bolddense			compute bold dense connectome (needs >30gb ram per bold)"
  				echo "nii4dfpconvert			convert nifti hcp-processed bold data to 4dpf format for fild analyses"
  				echo "cifti4dfpconvert		convert cifti hcp-processed bold data to 4dpf format for fild analyses"
  				echo "ciftismooth			smooth & convert cifti bold data to 4dpf format for fild analyses"
  				echo ""  				
  				cyaneho "FIX ICA de-noising"    
  				cyaneho "---------------------------"							
  				echo "fixica				run fix ica de-noising on a given volume"
  				echo "postfix				generates wb_view scene files in each subjects directory for fix ica results"
  				echo "boldhardlinkfixica		setup hard links for single run fix ica results"  				
  				echo "fixicainsertmean		re-insert mean image back into mapped fix ica data (needed prior to dofcmrip calls)"
  				echo "fixicaremovemean		remove mean image from mapped fix ica data"
  				echo "boldseparateciftifixica		separate specified bold timeseries (results from fix ica - use if bolds merged)"
  				echo "boldhardlinkfixicamerged	setup hard links for merged fix ica results (use if bolds merged)" 
  				echo ""
  				cyaneho "GMRI utilities for preprocessing and analyses"
  				cyaneho "---------------------------------------------"							    
  				echo ""
  				echo " * Note: ap parses all functions from gmri as standard input"	
  				echo "`gmri`"
  				echo "`gmri -l`"
  				echo ""
  				echo""
}

###########################################################################################################################
###########################################################################################################################
####################################  SPECIFIC ANALYSIS FUNCTIONS START HERE ##############################################
###########################################################################################################################
###########################################################################################################################

# ------------------------------------------------------------------------------------------------------
#  gmri general wrapper - parse inputs into specific gmri functions via AP 
# ------------------------------------------------------------------------------------------------------


gmri_function() {

	# Issue the complete gmri originating call
	echo ""
	gmri ${gmriinput}
	echo ""
	exit 0 

}

show_usage_gmri() {
  				
  	gmri
  	cyaneho " Help for ${UsageInput}"
  	cyaneho "----------------------------------------------------------------------------"
  	gmri ?${UsageInput}
  	echo ""
}

# ------------------------------------------------------------------------------------------------------
#  dicomsort - Sort original DICOMs into sub-folders and then generate NIFTI files
# ------------------------------------------------------------------------------------------------------

dicomsort() {
	  				
	  		mkdir ${StudyFolder}/${CASE}/dicom &> /dev/null
	  		
	  		# -- Check of overwrite flag was set
			if [ "$Overwrite" == "no" ]; then
			echo ""
			reho "===> Checking for presence of ${StudyFolder}/${CASE}/dicom/DICOM-Report.txt"
			
			if (test -f ${StudyFolder}/${CASE}/dicom/DICOM-Report.txt); then
				echo ""
				geho "--- Found ${StudyFolder}/${CASE}/dicom/DICOM-Report.txt"
				geho "    Note: To re-run set --overwrite='yes'"
				echo ""
				geho " ... $CASE ---> dicomsort done"
				echo ""

			else
			
			echo ""
	  		
	  		# -- Combine all the calls into a single command
		 	Com1="cd ${StudyFolder}/${CASE}"
			echo " ---> running sortDicom and dicom2nii for $CASE"
			echo ""
			Com2="gmri sortDicom"
			Com3="gmri dicom2nii unzip=yes gzip=yes clean=yes"
			ComQUEUE="$Com1; $Com2; $Com3"
		
			if [ "$Cluster" == 1 ]; then

			  	echo ""
  				echo "---------------------------------------------------------------------------------"
				echo "Running dicomsort locally on `hostname`"
				echo "Check output here: $StudyFolder/$CASE/dicom "
				echo "---------------------------------------------------------------------------------"
		 		echo ""
		 		eval "$ComQUEUE"

			else
			
				echo "Job ID:"
				fslsub="$Scheduler" # set scheduler for fsl_sub command
				# -- Set the scheduler commands
				rm -f "$StudyFolder"/"$CASE"/dicom/"$CASE"_ComQUEUE_dicomsort.sh &> /dev/null
				echo "$ComQUEUE" >> "$StudyFolder"/"$CASE"/dicom/"$CASE"_ComQUEUE_dicomsort.sh
				chmod 770 "$StudyFolder"/"$CASE"/dicom/"$CASE"_ComQUEUE_dicomsort.sh
				# -- Run the scheduler commands
				fsl_sub."$fslsub" -Q "$QUEUE" -l "$StudyFolder/$CASE/dicom" -R 10000 "$StudyFolder"/"$CASE"/dicom/"$CASE"_ComQUEUE_dicomsort.sh
				
				echo ""
				echo "---------------------------------------------------------------------------------"
				echo "Scheduler: $Scheduler"
				echo "QUEUE Name: $QUEUE"
				echo "Data successfully submitted to $QUEUE" 
				echo "Check output logs here: $StudyFolder/$CASE/dicom"
				echo "---------------------------------------------------------------------------------"
				echo ""
			
			fi
			fi
			fi
}

show_usage_dicomsort() {
  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
  				echo "This function expects a set of raw DICOMs in <study_folder>/<case>/inbox."
  				echo "DICOMs are organized, gzipped and converted to NIFTI format for additional processing."
  				echo ""
  				echo ""
  				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>				Name of function"
				echo "		--path=<study_folder>					Path to study data folder"
				echo "		--subjects=<comma_separated_list_of_cases>		List of subjects to run"
				echo "		--runmethod=<type_of_run>				Perform Local Interactive Run [1] or Send to scheduler [2] [If local/interactive then log will be continuously generated in different format]"
				echo "		--queue=<name_of_cluster_queue>				Cluster queue name"
				echo "		--scheduler=<name_of_cluster_scheduler>			Cluster scheduler program: e.g. LSF or PBS"
				echo ""
				echo "-- OPTIONAL PARAMETERS: "
				echo ""
				echo "		--overwrite=<re-run_dicomsort>				Explicitly force a re-run of dicomsort"
				echo ""
				echo ""  
    			echo "-- Usage for dicomsort"
    			echo ""
				echo "* Example with interactive terminal:"
				echo "AP dicomsort <study_folder> 'comma_separarated_list_of_cases>'"
    			echo ""
    			echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "AP --path='<study_folder>' \ "
				echo "--function='dicomsort' \ "
				echo "--subjects='<comma_separarated_list_of_cases>' \ "
				echo "--runmethod='1'"
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='<study_folder>' \ "
				echo "--function='dicomsort' \ "
				echo "--subjects='<comma_separarated_list_of_cases>' \ "
				echo "--runmethod='2' \ "
				echo "--queue='<name_of_queue>' \ "
				echo "--scheduler='<name_of_scheduler>' "
				echo "" 
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  dicom2nii - Convert DICOMs to NIFTI files
# ------------------------------------------------------------------------------------------------------

dicom2nii() {

	cd "$StudyFolder"/"$CASE"

	echo " ---> running dicom2nii"
	gmri dicom2nii unzip=yes gzip=yes clean=yes	
	
}

show_usage_dicom2nii() {
  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
  				echo "This function converts DICOMs to NIFTI format for additional processing."
  				echo ""
    			echo "-- Usage for dicom2nii"
    			echo ""
				echo "* Example with interactive terminal:"
				echo "AP dicom2nii <study_folder> '<list of cases>'"
    			echo ""
				echo "* Example with flags:"
				echo "AP --function=dicom2nii --path=<study_folder> --subjects='<list of cases>'"
    			echo ""
    			echo ""
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  setuphcp - Setup the HCP File Structure to be fed to the Yale HCP
# ------------------------------------------------------------------------------------------------------

setuphcp() {

	cd "$StudyFolder"/"$CASE"
		
  				
			echo " ---> running setuphcp for $CASE"
		 	echo ""
		 	# -- Combine all the calls into a single command
		 	Com1="cd ${StudyFolder}/${CASE}"
			Com2="gmri setupHCP"
			ComQUEUE="$Com1; $Com2"
			
			if [ "$Cluster" == 1 ]; then
			
				echo ""
  				echo "---------------------------------------------------------------------------------"
				echo "Running setuphcp locally on `hostname`"
				echo "Check output here: $StudyFolder/$CASE/hcp "
				echo "---------------------------------------------------------------------------------"
		 		echo ""
				eval "$ComQUEUE"

			else
			
				echo "Job ID:"
				fslsub="$Scheduler" # set scheduler for fsl_sub command
				# -- Set the scheduler commands
				rm -f "$StudyFolder"/"$CASE"/"$CASE"_setuphcp.sh &> /dev/null
				echo "$ComQUEUE" >> "$StudyFolder"/"$CASE"/"$CASE"_setuphcp.sh
				chmod 770 "$StudyFolder"/"$CASE"/"$CASE"_setuphcp.sh
				# -- Run the scheduler commands
				fsl_sub."$fslsub" -Q "$QUEUE" -l "$StudyFolder/$CASE/" -R 10000 "$StudyFolder"/"$CASE"/"$CASE"_setuphcp.sh
				
				echo ""
				echo "---------------------------------------------------------------------------------"
				echo "Scheduler: $Scheduler"
				echo "QUEUE Name: $QUEUE"
				echo "Data successfully submitted to $QUEUE" 
				echo "Check output logs here: $StudyFolder/$CASE/dicom"
				echo "---------------------------------------------------------------------------------"
				echo ""
			
			fi
	
}

show_usage_setuphcp() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
  				echo "This function generates the Human Connectome Project folder structure for preprocessing."
  				echo "It should be executed after proper dicomsort and subject.txt file has been vetted."
  				echo ""
  				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>				Name of function"
				echo "		--path=<study_folder>					Path to study data folder"
				echo "		--subjects=<comma_separated_list_of_cases>		List of subjects to run"
				echo "		--runmethod=<type_of_run>				Perform Local Interactive Run [1] or Send to scheduler [2] [If local/interactive then log will be continuously generated in different format]"
				echo "		--queue=<name_of_cluster_queue>				Cluster queue name"
				echo "		--scheduler=<name_of_cluster_scheduler>			Cluster scheduler program: e.g. LSF or PBS"
				echo "" 
    			echo "-- Usage for setuphcp"
    			echo ""
				echo "* Example with interactive terminal:"
				echo "AP setuphcp <study_folder> 'comma_separarated_list_of_cases>'"
				echo "AP setuphcp <study_folder> '<list of cases>'"
    			echo ""
				echo "* Example with flags:"
				echo "AP --function=setuphcp --path=<study_folder> --subjects='<list of cases>'"
    			echo ""
    			echo ""
    			echo ""
    			echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "AP --path='<study_folder>' \ "
				echo "--function='setuphcp' \ "
				echo "--subjects='<comma_separarated_list_of_cases>' \ "
				echo "--runmethod='1'"
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='<study_folder>' \ "
				echo "--function='setuphcp' \ "
				echo "--subjects='<comma_separarated_list_of_cases>' \ "
				echo "--runmethod='2' \ "
				echo "--queue='<name_of_queue>' \ "
				echo "--scheduler='<name_of_scheduler>' "
				echo "" 
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  createlists - Generate processing & analysis lists for fcMRI
# ------------------------------------------------------------------------------------------------------

createlists() {

	if [ "$ListGenerate" == "preprocessing" ]; then
			
	# - Check if appending list
	if [ "$Append" == "yes" ]; then
	
		# --> If append was set to yes and file exists then clear header
		ParameterFile="no"
		
		echo ""
		geho "---------------------------------------------------------------------"
		geho "--> You are appending the paramater file with $CASE                  "
		geho "--> --parameterfile flag will be cleared"
		geho "--> Check usage to overwrite the file"
		geho "---------------------------------------------------------------------"
		echo ""
		
		source "$ListFunction"
	
	else
		
		echo ""
		geho "---------------------------------------------------------------------"
		geho "--> Generaring new file with parameter header for $CASE              "
		geho "---------------------------------------------------------------------"
		echo ""
		
		source "$ListFunction"
		
	fi
	fi

	if [ "$ListGenerate" == "analysis" ]; then
	
		unset ParameterFile
		unset Append
		
		echo ""
		geho "---------------------------------------------------------------------"
		geho "--> Generaring analysis list files for $CASE... "
		geho "--> Check output here: ${StudyFolder}/lists... "
		geho "---------------------------------------------------------------------"
		echo ""
		
		source "$ListFunction"

	fi
	
	if [ "$ListGenerate" == "snr" ]; then
	
		# - generate subject SNR list for all subjects across all BOLDs
		cd "$StudyFolder"/QC/snr
		for BOLD in $BOLDS
		do
			echo subject id:"$CASE" >> subjects.snr.txt
			echo file:"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD".nii.gz >> "$StudyFolder"/QC/snr/subjects.snr.txt
		done
	fi
}

show_usage_createlists() {
  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
  				echo "This function generates a lists for processing or analyses for multiple subjects."
  				echo "The function supports generation of parameter files for HCP processing for either 'legacy' of multiband data."
  				echo ""
  				echo "Supported lists:"
  				echo ""
  				echo "	* preprocessing --> Subject parameter list with cases to preprocess"
  				echo "	* analysis --> List of cases to compute seed connectivity or GBC"
  				echo "	* snr --> List of cases to compute signal-to-noise ratio"
  				echo ""
  				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>				Name of function"
				echo "		--path=<study_folder>					Path to study data folder"
				echo "		--subjects=<comma_separated_list_of_cases>		List of subjects to run"
				echo "		--listtocreate=<type_of_list_to_generate>		Type of list to generate (e.g. preprocessing). "
				echo "		--listname=<output_name_of_the_list>			Output name of the list to generate. "
				echo "	 	* Supported: preprocessing, analysis, snr"
				echo ""
				echo "-- OPTIONAL PARAMETERS: "
				echo ""
				echo "		--overwrite=<yes/no>					Explicitly delete any prior lists"
				echo "		--append=<yes>						Explicitly append the existing list"
				echo ""
				echo "		* Note: If --append set to <yes> then function will append new cases to the end"
				echo ""								
				echo "		--parameterfile=<header_file_for_processing_list>	Set header for the processing list."
				echo ""
				echo "		* Default:"
				echo ""
				echo "`ls ${TOOLS}/MNAP/general/functions/subjectparamlist_header_multiband.txt`"
				echo ""
				echo "		* Supported: "
				echo ""
				echo "`ls ${TOOLS}/MNAP/general/functions/subjectparamlist_header*` "
				echo ""
				echo "		* Note: If --parameterfile set to <no> then function will not add a header"
				echo ""								
				echo "      --listfunction=<function_used_to_create_list>   	Point to external function to use"
				echo "      --bolddata=<comma_separated_list_of_bolds>   	List of BOLD files to append to analysis or snr lists"
				echo "      --parcellationfile=<file_for_parcellation>	Specify the absolute file path for parcellation in $MNAPPATH/general/templates/Parcellations/ "
				echo "      --filetype=<file_extension>			Extension for BOLDs in the analysis (e.g. _Atlas). Default empty []"
				echo "      --boldsuffix=<comma_separated_bold_suffix>	List of BOLDs to iterate over in the analysis list"
#    			echo "		--subjecthcpfile=<yes/no>		Use individual subject_hcp.txt file for for appending the parameter list"
    			echo ""
    			echo "-- Usage for createsubjectlists"
    			echo ""
				echo "* Example with interactive terminal:"
				echo ""
				echo "AP createlists <study_folder> 'comma_separarated_list_of_cases>'"
    			echo ""
    			echo "-- Example with flagged parameters:"
				echo ""
				echo "AP --path='<study_folder>' \ "
				echo "--function='createlists' \ "
				echo "--subjects='<comma_separarated_list_of_cases>' \ "
				echo "--listtocreate='preprocessing' \ "
				echo "--overwrite='yes' \ "
				echo "--listname='<list_to_generate>' \ "
				echo "--parameterfile='no' \ "
				echo "--append='yes' "
				echo ""
				echo "AP --path='<study_folder>' \ "
				echo "--function='createlists' \ "
				echo "--subjects='<comma_separarated_list_of_cases>' \ "
				echo "--listtocreate='analysis' \ "
				echo "--overwrite='yes' \ "
				echo "--bolddata='1' \ "	
				echo "--filetype='dtseries.nii' \ "											
				echo "--listname='<list_to_generate>' \ "
				echo "--append='yes' "				
				echo ""
				echo "" 
    			echo ""
}


# ------------------------------------------------------------------------------------------------------
#  nii4dfpconvert - Convert NIFTI files into 4DFP for FIDL GLM analyses
# ------------------------------------------------------------------------------------------------------

nii4dfpconvert() {

for BOLD in $BOLDS
do
	cd "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"
	
	if [ -f "$BOLD".4dfp.img ]; 
	then
		echo "NIFTI 4dfp conversion done for $CASE and "$BOLD".nii.gz"
	else
		echo "Running NIFTI-->4dfp conversion for $CASE and "$BOLD".nii.gz"
		gunzip -f "$BOLD".nii.gz
		nifti_4dfp -4 "$BOLD".nii "$BOLD".4dfp.ifh
		gzip "$BOLD".nii
	fi
	
	if [ -f "$BOLD"_hp2000_clean.4dfp.img ]; 
	then
		echo "NIFTI 4dfp conversion done for $CASE and "$BOLD"_hp2000_clean.nii.gz"
	else
		echo "Running NIFTI-->4dfp conversion for $CASE and "$BOLD"_hp2000_clean.nii.gz"
		gunzip -f "$BOLD"_hp2000_clean.nii.gz
		nifti_4dfp -4 "$BOLD"_hp2000_clean.nii "$BOLD"_hp2000_clean.4dfp.ifh
		gzip "$BOLD"_hp2000_clean.nii
	fi

done
}

show_usage_nii4dfpconvert() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "This function converts NII files to legacy 4dfp file format used by WashU NIL pipelines."
    			echo ""
    			echo "Note: Assumptions are made that there exists _hp2000_clean NIFTI file in the HCP folder structure."
    			echo ""
    			echo "Example: AP nii4dfpconvert <absolute_path_to_subjects_folder> 'list_of_cases' "
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  cifti4dfpconvert - Convert CIFTI *dtseries.nii files into 4DFP for FIDL GLM analyses
# ------------------------------------------------------------------------------------------------------

cifti4dfpconvert() {

for BOLD in $BOLDS
do
	cd "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"
	
	if [ -f "$BOLD"_Atlas.dtseries.4dfp.img ];
	then
		echo "CIFTI 4dfp conversion done for $CASE and "$BOLD"_Atlas_hp2000_clean.dtseries.nii"
	else
		echo "Running CIFTI-->4dfp conversion for $CASE and "$BOLD"_Atlas.dtseries.nii"
		# first take a given *_Atlas.dtseries.nii BOLD run and convert to NIFTI
		wb_command -cifti-convert -to-nifti "$BOLD"_Atlas.dtseries.nii "$BOLD"_Atlas.nifti.dtseries.nii
		# next convert NIFTI file to 4dfp to be used in FIDL
		nifti_4dfp -4 "$BOLD"_Atlas.nifti.dtseries.nii "$BOLD"_Atlas.dtseries.4dfp.ifh
	fi

	if [ -f "$BOLD"_Atlas_hp2000_clean.dtseries.4dfp.img ];
	then
		echo "CIFTI 4dfp conversion done for $CASE and "$BOLD"_Atlas_hp2000_clean.dtseries.nii"
	else
		echo "Running CIFTI-->4dfp conversion for $CASE and "$BOLD"_Atlas_hp2000_clean.dtseries.nii"
		# first take a given *_Atlas.dtseries.nii BOLD run and convert to NIFTI
		wb_command -cifti-convert -to-nifti "$BOLD"_Atlas_hp2000_clean.dtseries.nii "$BOLD"_Atlas_hp2000_clean.nifti.dtseries.nii
		# next convert NIFTI file to 4dfp to be used in FIDL
		nifti_4dfp -4 "$BOLD"_Atlas_hp2000_clean.nifti.dtseries.nii "$BOLD"_Atlas_hp2000_clean.dtseries.4dfp.ifh
	fi

done
}

show_usage_cifti4dfpconvert() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Function for converting a CIFTI file to a legacy 4dfp 4dfp file format used by WashU NIL pipelines for a given BOLD file."
    			echo ""
    			echo "Note: Assumptions are made that there exists _hp2000_clean CIFTI file in the HCP folder structure."
    			echo ""
    			echo "Example: AP cifti4dfpconvert <absolute_path_to_subjects_folder> 'list_of_cases' "
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  ciftismooth - Smooth CIFTI *dtseries.nii for FIDL GLM analyses
# ------------------------------------------------------------------------------------------------------

ciftismooth() {

for BOLD in $BOLDS
do

	for KERNEL in $KERNELS
	do	

	if [ -f "$BOLD"_s"$KERNEL"_Atlas.dtseries.4dfp.img ];
	then
		echo "CIFTI Smoothing and 4dfp conversion done for $CASE and $BOLD_s$KERNEL_Atlas.dtseries.nii"
	else
		echo "Running CIFTI-->4dfp conversion for $CASE bold# $BOLD and smoothing kernel $KERNEL..."
		# CIFTI smooth
		wb_command -cifti-smoothing "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas.dtseries.nii "$KERNEL" "$KERNEL" COLUMN "$BOLD"_s"$KERNEL"_Atlas.dtseries.nii -left-surface "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".L.midthickness.32k_fs_LR.surf.gii -right-surface "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".R.midthickness.32k_fs_LR.surf.gii
		# first take a given *_Atlas.dtseries.nii BOLD run and convert to NIFTI
		wb_command -cifti-convert -to-nifti "$BOLD"_s"$KERNEL"_Atlas.dtseries.nii "$BOLD"_s"$KERNEL"_Atlas.nifti.dtseries.nii
		# next convert NIFTI file to 4dfp to be used in FIDL
		nifti_4dfp -4 "$BOLD"_s"$KERNEL"_Atlas.nifti.dtseries.nii "$BOLD"_s"$KERNEL"_Atlas.dtseries.4dfp.ifh
	fi
	
	if [ -f "$BOLD"_s"$KERNEL"_Atlas_hp2000_clean.dtseries.4dfp.img ];
	then
		echo "CIFTI Smoothing and 4dfp conversion done for $CASE and $BOLD_s$KERNEL_Atlas_hp2000_clean.dtseries.nii"
	else
		echo "Running CIFTI-->4dfp conversion for $CASE bold# $BOLD and smoothing kernel $KERNEL..."
		# CIFTI smooth
		wb_command -cifti-smoothing "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas_hp2000_clean.dtseries.nii "$KERNEL" "$KERNEL" COLUMN "$BOLD"_s"$KERNEL"_Atlas_hp2000_clean.dtseries.nii -left-surface "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".L.midthickness.32k_fs_LR.surf.gii -right-surface "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".R.midthickness.32k_fs_LR.surf.gii
		# first take a given *_Atlas.dtseries.nii BOLD run and convert to NIFTI
		wb_command -cifti-convert -to-nifti "$BOLD"_s"$KERNEL"_Atlas_hp2000_clean.dtseries.nii "$BOLD"_s"$KERNEL"_Atlas_hp2000_clean.nifti.dtseries.nii
		# next convert NIFTI file to 4dfp to be used in FIDL
		nifti_4dfp -4 "$BOLD"_s"$KERNEL"_Atlas_hp2000_clean.nifti.dtseries.nii "$BOLD"_s"$KERNEL"_Atlas_hp2000_clean.dtseries.4dfp.ifh
	fi
	
	done
done
}

show_usage_ciftismooth() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Function for CIFTI smoothing."
    			echo ""
    			echo "Note: Assumptions are made that there exists _hp2000_clean NIFTI file in the HCP folder structure."
    			echo ""
    			echo "Example: AP ciftismooth <absolute_path_to_subjects_folder> 'list_of_cases' "
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  hpcsync - Sync files to Yale HPC and back to the Yale server after HCP preprocessing
# ------------------------------------------------------------------------------------------------------


hpcsync() {

	if [ "$Direction" == 1 ]; then
		echo "Syncing data to $ClusterName for $CASE ..."
		rsync --checksum --rsh=ssh -avz --exclude=* "$StudyFolder"/"$CASE" "$NetID"@"$ClusterName":"$HCPStudyFolder"/ &> /dev/null
		rsync --checksum --rsh=ssh --exclude=*dicom* --exclude=*4dfp* --exclude=nii --exclude=*Results* --exclude=inbox --exclude=images -avz "$StudyFolder"/"$CASE" "$NetID"@"$ClusterName":"$HCPStudyFolder"/ &> /dev/null
		#rsync --checksum --rsh=ssh --exclude=*dicom* --exclude=*_s2_Atlas* --exclude=*_s3_Atlas* --exclude=Parcellated --exclude=FieldMap_strc --exclude=SpinEchoFieldMap1_fncb --exclude=T2w --exclude=*4dfp* --exclude=nii --exclude=BOLD_*fncb --exclude=images --exclude=hcp_washu --exclude=1_4 --exclude=5_8 --exclude=10_13 --exclude=14_17 --exclude=inbox -avz "$StudyFolder"/"$CASE" "$NetID"@"$ClusterName":"$HCPStudyFolder"/
	else
		echo "Syncing data from $ClusterName for $CASE ..." 
		mkdir "$StudyFolder"/"$CASE"  &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp  &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"  &> /dev/null
		rsync --checksum --rsh=ssh -avz "$NetID"@"$ClusterName":"$HCPStudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear "$StudyFolder"/"$CASE"/hcp/"$CASE"/ &> /dev/null
		rsync --checksum --rsh=ssh -avz "$NetID"@"$ClusterName":"$HCPStudyFolder"/"$CASE"/hcp/"$CASE"/T1w "$StudyFolder"/"$CASE"/hcp/"$CASE"/ &> /dev/null
	fi
}

show_usage_hpcsync() {
  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "This function runs rsync to or from the Yale Clusters [e.g. Omega, Louise, Grace) and local servers."
  				echo "It explicitly preserves the Human Connectome Project folder structure for preprocessing:"
  				echo "    <study_folder>/<case>/hcp/<case>"
  				echo ""
    			echo "-- Usage for hpcsync"
    			echo ""
				echo "* Example with interactive terminal:"
				echo "AP hpcsync <study_folder> '<list of cases>'"
    			echo ""
    			echo ""
				echo "* Example with flags:"
				echo "AP --function=hpcsync --path=<study_folder> --subjects='<list of cases>'--cluster=<cluster_address> --dir=<rsync_direction> --netid=<Yale_NetID> --clusterpath=<cluster_study_folder>"
    			echo ""
    			echo ""
  				echo "-- OPTIONS:"
    			echo ""
    			echo "   --function=<function_name>   Name of function (required)"	
    			echo "   --path=<study_folder>        Path to study data folder (required)"	
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  isolatesubcortexrois - Find subcortical ROIs needed for subcortical seed-based tractography 
# ------------------------------------------------------------------------------------------------------

isolatesubcortexrois() {

	# This function is designed to isolate subject-specific subcortical ROIs which are used as targets in the function below

	# Isolate thalamus seeds for analyses #THALAMUS_LEFT 10 0 118 14 255 #THALAMUS RIGHT 49 0 118 255
	cd "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs
    3dcalc -overwrite -a Atlas_ROIs.2.nii.gz  -expr 'equals(a,10)' -prefix Atlas_thalamus.L.nii.gz # isolate left thalamus from global mask file
	3dcalc -overwrite -a Atlas_ROIs.2.nii.gz  -expr 'equals(a,49)' -prefix Atlas_thalamus.R.nii.gz # isolate right thalamus from global mask file
	# Get thalamic volumes
	#thalvol_L=`fslstats Atlas_thalamus.L.nii.gz -V | cut -d " " -f 1` #198 - get # of L thalamic voxels needed to adjust the nsamples flag - 5000 * 1288 / 32492 number of vertices
	#thalvol_R=`fslstats Atlas_thalamus.R.nii.gz -V | cut -d " " -f 1` #192 - get # of R thalamic voxels needed to adjust the nsamples flag - 5000 * 1248 / 32492 number of vertices
	
	# Isolate accumbens seeds for analyses #accumbens_LEFT 26 0 118 14 255 #accumbens RIGHT 58 0 118 255
	cd "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs
    3dcalc -overwrite -a Atlas_ROIs.2.nii.gz  -expr 'equals(a,26)' -prefix Atlas_accumbens.L.nii.gz # isolate left accumbens from global mask file
	3dcalc -overwrite -a Atlas_ROIs.2.nii.gz  -expr 'equals(a,58)' -prefix Atlas_accumbens.R.nii.gz # isolate right accumbens from global mask file
	# Get accumbens volumes
	#accvol_L=`fslstats Atlas_accumbens.L.nii.gz -V | cut -d " " -f 1` #25 - get # of L thalamic voxels needed to adjust the nsamples flag - 5000 * 135 / 32492 number of vertices
	#accvol_R=`fslstats Atlas_accumbens.R.nii.gz -V | cut -d " " -f 1` #25 - get # of R thalamic voxels needed to adjust the nsamples flag - 5000 * 140 / 32492 number of vertices

	# Isolate caudate seeds for analyses #caudate_LEFT 11 0 118 14 255 #caudate RIGHT 50 0 118 255
	cd "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs
    3dcalc -overwrite -a Atlas_ROIs.2.nii.gz  -expr 'equals(a,11)' -prefix Atlas_caudate.L.nii.gz # isolate left caudate from global mask file
	3dcalc -overwrite -a Atlas_ROIs.2.nii.gz  -expr 'equals(a,50)' -prefix Atlas_caudate.R.nii.gz # isolate right caudate from global mask file
	# Get caudate volumes
	#caudvol_L=`fslstats Atlas_caudate.L.nii.gz -V | cut -d " " -f 1` #112 - get # of L thalamic voxels needed to adjust the nsamples flag - 5000 * 728 / 32492 number of vertices
	#caudvol_R=`fslstats Atlas_caudate.R.nii.gz -V | cut -d " " -f 1` #116 - get # of R thalamic voxels needed to adjust the nsamples flag - 5000 * 755 / 32492 number of vertices
	
	# Isolate putamen seeds for analyses #putamen_LEFT 12 0 118 14 255 #putamen RIGHT 51 0 118 255
	cd "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs
    3dcalc -overwrite -a Atlas_ROIs.2.nii.gz  -expr 'equals(a,12)' -prefix Atlas_putamen.L.nii.gz # isolate left putamen from global mask file
	3dcalc -overwrite -a Atlas_ROIs.2.nii.gz  -expr 'equals(a,51)' -prefix Atlas_putamen.R.nii.gz # isolate right putamen from global mask file
	# Get putamen volumes
	#putvol_L=`fslstats Atlas_putamen.L.nii.gz -V | cut -d " " -f 1` #163 - get # of L thalamic voxels needed to adjust the nsamples flag - 5000 * 1060 / 32492 number of vertices
	#putvol_R=`fslstats Atlas_putamen.R.nii.gz -V | cut -d " " -f 1` #155 - get # of R thalamic voxels needed to adjust the nsamples flag - 5000 * 1010 / 32492 number of vertices

	# Isolate putamen seeds for analyses #pallidum_LEFT 12 0 118 14 255 #pallidum RIGHT 51 0 118 255
	cd "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs
    3dcalc -overwrite -a Atlas_ROIs.2.nii.gz  -expr 'equals(a,13)' -prefix Atlas_pallidum.L.nii.gz # isolate left pallidum from global mask file
	3dcalc -overwrite -a Atlas_ROIs.2.nii.gz  -expr 'equals(a,52)' -prefix Atlas_pallidum.R.nii.gz # isolate right pallidum from global mask file
	# Get putamen volumes
	#pallvol_L=`fslstats Atlas_pallidum.L.nii.gz -V | cut -d " " -f 1` #46 - get # of L thalamic voxels needed to adjust the nsamples flag - 5000 * 297 / 32492 number of vertices
	#pallvol_R=`fslstats Atlas_pallidum.R.nii.gz -V | cut -d " " -f 1` #40 - get # of R thalamic voxels needed to adjust the nsamples flag - 5000 * 260 / 32492 number of vertices

}

show_usage_isolatesubcortexrois() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Function for isolating subcortical ROIs based on individual anatomy to be used in probabilistic tractography."
    			echo ""
    			echo "Note: it assumes that there is data inside <$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/ROIs> "
    			echo ""
}
	

# ------------------------------------------------------------------------------------------------------
#  probtracksubcortex - For a given subcortical ROI run probabilistic tractography (CPU version)
# ------------------------------------------------------------------------------------------------------

probtracksubcortex() {

	# This function is designed to track from uni-lateral sub-cortical nucleus to the cortical surface in MNI space for each subject to standardize the # of voxels within each thalamus
    
    for STRUCTURE in $STRUCTURES
    do
		#set # of samples for each specific structure
		if [ "$STRUCTURE" == "pallidum" ]; then
			nsample=46
			LABEL="PALLIDUM"
			rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
			rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
			echo "$LABEL"_LEFT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
			echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
			echo "$LABEL"_RIGHT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
			echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt   
		else
			if [ "$STRUCTURE" == "thalamus" ]; then
				nsample=200
				LABEL="THALAMUS"
				rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
				rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
				echo "$LABEL"_LEFT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
				echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
				echo "$LABEL"_RIGHT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
				echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt    
			else
				if [ "$STRUCTURE" == "caudate" ]; then
					nsample=115
					LABEL="CAUDATE"
					rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
					rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
					echo "$LABEL"_LEFT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
					echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
					echo "$LABEL"_RIGHT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
					echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt  
				else
					if [ "$STRUCTURE" == "accumbens" ]; then
						nsample=25
						LABEL="ACCUMBENS"
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
						echo "$LABEL"_LEFT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
						echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
						echo "$LABEL"_RIGHT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
						echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt  
					else
						if [ "$STRUCTURE" == "putamen" ]; then
							nsample=165
							LABEL="ACCUMBENS"
							rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
							rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
							echo "$LABEL"_LEFT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
							echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
							echo "$LABEL"_RIGHT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
							echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt  
						else
							if [ "$STRUCTURE" == "thalamus_sensory" ]; then
								nsample=75
								LABEL="THALAMUS"
								rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
								rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
								echo "$LABEL"_LEFT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
								echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
								echo "$LABEL"_RIGHT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
								echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
							else
								if [ "$STRUCTURE" == "thalamus_associative" ]; then
									nsample=75
									LABEL="THALAMUS"
									rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
									rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
									echo "$LABEL"_LEFT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
									echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_L.txt
									echo "$LABEL"_RIGHT >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
									echo 1 1 0 0 1 >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_R.txt
								else   
									echo "Undefined Structure - check structure input string"
								fi	
							fi	
						fi
					fi
				fi
			fi
		fi		
		

		# For each hemisphere track from surface to "$STRUCTURE"
		HEMIS="R"
		for HEMI in $HEMIS
		do
			if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI"/"$CASE"_"$STRUCTURE"2cortex_"$HEMI"_norm.dscalar.nii ];
			then
				echo "Tractography done for $CASE and $STRUCTURE. Skipping to next subject..."
			else
				echo "Running tractography for $CASE and $STRUCTURE..."
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_dwi_stop_"$HEMI".txt
				    	echo "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/Atlas_"$STRUCTURE"."$HEMI".nii.gz >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_dwi_stop_"$HEMI".txt
    					echo "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE"."$HEMI".pial.32k_fs_LR.surf.gii >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_dwi_stop_"$HEMI".txt
						
						probtrackx2 --target2="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/Atlas_"$STRUCTURE"."$HEMI".nii.gz --mask="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Whole_Brain_Trajectory_"$DWIRes".nii.gz --samples="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion.bedpostX/merged --dir="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI" --forcedir --opd --nsamples="$nsample" --nsteps=2000 --steplength=0.45 --cthr=0 --fibthresh=0.05 --loopcheck --randfib=2 --seed="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE"."$HEMI".white.32k_fs_LR.surf.gii --meshspace=caret --seedref="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/Atlas_ROIs.2.nii.gz --omatrix2 --invxfm="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/xfms/acpc_dc2standard.nii.gz --xfm="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/xfms/standard2acpc_dc.nii.gz --waypoints="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/Atlas_"$STRUCTURE"."$HEMI".nii.gz --stop="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_dwi_stop_"$HEMI".txt
												
						## COMPLETE probtrackx2 COMMAND GUIDE
						#probtrackx2 --target2="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/Atlas_thalamus.L.nii.gz  \ # unilateral thalamic seed to start from
						#--mask="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Whole_Brain_Trajectory_1.80.nii.gz \ # space in which to do tractogrphy
						#--samples="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion.bedpostX/merged \ # diffusion orientation from which to sample from
						#--dir="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_thalamus_L \ # results dir
						#--forcedir \ # forces overwrite
						#--opd \ # streamline count in every brain voxel
						#--stop="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/Atlas_thalamus.L.nii.gz \ # halt tractography here
						#--nsamples=198 \ # how many samples per seed voxel do you send out - #5000 * thalamus voxels / number of vertices
						#--nsteps=2000 \ # how many samples can you take
						#--steplength=0.45 \ # distance in mm between samples
						#--cthr=0 \ # curvature threshold
						#--fibthresh=0.05 \ # how strong is fiber after the 1st fiber have to be to use it; 5% of the signal
						#--loopcheck \ # prevent loops
						#--randfib=2 \ # send seeds in proportion to fibers
						#--seed="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/ta6361.L.white.32k_fs_LR.surf.gii
						#--meshspace=caret \
						#--seedref="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/Atlas_ROIs.2.nii.gz \
						#--omatrix2
						#--xfm=acpc_dc2standard.nii.gz
						#--invxfm=standard2acpc_dc.nii.gz
						
						wb_command -metric-math "var - var +1" "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI"/AllOnes.func.gii -var var "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE"."$HEMI".atlasroi.32k_fs_LR.shape.gii # makes a metric file that can be used by the 2nd command; # this would correspond to the -row-surface flag of wb_command -probtrackx-dot-convert
						wb_command -volume-label-import "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/Atlas_"$STRUCTURE"."$HEMI".nii.gz "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/"$CASE"."$STRUCTURE"_label_"$HEMI".txt "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/Atlas_"$STRUCTURE"."$HEMI".nii.gz
						wb_command -probtrackx-dot-convert "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI"/fdt_matrix2.dot  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI"/fdt_matrix2.dconn.nii -row-surface "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI"/AllOnes.func.gii -col-voxels "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI"/tract_space_coords_for_fdt_matrix2 "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs/Atlas_"$STRUCTURE"."$HEMI".nii.gz # the 2nd command convert from probtrax sparse to a wm readable format, # for one dim you would use a surface metric for the other dim you would use your "$STRUCTURE" roi
						wb_command -cifti-transpose "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI"/fdt_matrix2.dconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI"/fdt_matrix2_trans.dconn.nii #transpose and then sum across all thalamic voxels once the results are done
						wb_command -cifti-reduce "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI"/fdt_matrix2_trans.dconn.nii SUM "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI"/"$CASE"_"$STRUCTURE"2cortex_"$HEMI".dscalar.nii	
						Waytotal=`cat "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI"/waytotal` 
						wb_command -cifti-math "var / "$Waytotal"" "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI"/"$CASE"_"$STRUCTURE"2cortex_"$HEMI"_norm.dscalar.nii -var var "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_"$HEMI"/"$CASE"_"$STRUCTURE"2cortex_"$HEMI".dscalar.nii
			fi
		done
	done

}

show_usage_probtracksubcortex() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			reho "		*** As of 2017 this function is deprecated and not supported any longer since the dense connectome implementation."
    			reho "		*** The new usage for dense connectome computation can be found via the following functions:"
    			echo ""
  				echo "		probtrackxgpudense		RUN FSL PROBTRACKX FOR WHOLE BRAIN & GENERATEs DENSE WHOLE-BRAIN CONNECTOMES (cluster usable)"
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  printmatrix - Sets hard links for BOLDs into Parcellated folder for modeling use
# ------------------------------------------------------------------------------------------------------

linkmovement() {

			for BOLD in $BOLDS
			do
				echo "Linking scrubbing data - BOLD $BOLD for $CASE..."
				ln -f "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD".use
				ln -f "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD".use
			done
}

show_usage_linkmovement() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Function links processed motion data from the HCP folder structure into the appropriate 'Parcellated' folder structure for later use."
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  printmatrix - Extract matrix data from parcellated files (BOLD)
# ------------------------------------------------------------------------------------------------------

printmatrix() {

			##################################################
		 	##################  BOLD  ########################
			##################################################
			
			if [ "$DatatoPrint" == "bold" ]; then
			
    		for STEP in $STEPS
    		do
					for BOLD in $BOLDS
					do
						if [ -f "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.csv ]; then
							echo "Matrix printing done for $CASE run $BOLD and $STEP. Skipping to next subject..."
						else		
					    	echo "Printing parcellated data on BOLD data for $CASE..."
							wb_command -nifti-information -print-matrix "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii > "$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.csv
							wb_command -nifti-information -print-matrix "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii > "$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.csv
							wb_command -nifti-information -print-matrix "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii > "$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.csv
							wb_command -nifti-information -print-matrix "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii > "$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.csv
						fi
						
					done
			done
			fi

}


show_usage_printmatrix() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Function prints a data matrix in CVS format for a given parcellation."
    			echo ""
    			echo "Note: Currently the function is hard coded to support only the LR_RSN_CSC_7Networks_networks file."
    			echo ""
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  boldmergenifti - Merge NIFTI files across runs *** needs cleanup
# ------------------------------------------------------------------------------------------------------

boldmergenifti() {
		
		if [ "$DatatoMerge" == "1_8_orig" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_8/1_8.nii.gz ]; then
					echo "Merging done for selected BOLD data for $CASE. Skipping to next subject..."
		else		
				echo "Merging BOLDs 1 - 8 for Rest and WM cases run 1 for $CASE..."
				mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_8 &> /dev/null
				fslmerge -tr "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_8/1_8.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1/1.nii.gz  \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/2/2.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/3/3.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/4/4.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5/5.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/6/6.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/7/7.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/8/8.nii.gz 0.7
		fi
		fi
		
		if [ "$DatatoMerge" == "10_17_orig" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_17/10_17.nii.gz ]; then
					echo "Merging done for selected BOLD data for $CASE. Skipping to next subject..."
		else		
				echo "Merging BOLDs 10 - 17 for Rest and WM cases run 1 for $CASE ..."
				mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_17 &> /dev/null
				fslmerge -tr "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_17/10_17.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10/10.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/11/11.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/12/12.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/13/13.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14/14.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/15/15.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/16/16.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/17/17.nii.gz 0.7
		fi
		fi
		
		if [ "$DatatoMerge" == "1_4_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_4.nii.gz ]; then
					echo "Merging done for selected BOLD data for $CASE. Skipping to next subject..."
		else		
				echo "Merging BOLDs 1 - 4 for Rest and WM cases run 1 for $CASE..."
				mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4 &> /dev/null
				fslmerge -tr "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_4.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1/1.nii.gz  \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/2/2.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/3/3.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/4/4.nii.gz 0.7
		fi
		fi
		
		if [ "$DatatoMerge" == "5_8_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_8.nii.gz ]; then
					echo "Merging done for selected BOLD data for $CASE. Skipping to next subject..."
		else		
				echo "Merging BOLDs 5 - 8 for Rest and WM cases run 1 for $CASE..."
				mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8 &> /dev/null
				fslmerge -tr "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_8.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5/5.nii.gz  \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/6/6.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/7/7.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/8/8.nii.gz 0.7
		fi
		fi
		
				if [ "$DatatoMerge" == "10_13_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_13.nii.gz ]; then
					echo "Merging done for selected BOLD data for $CASE. Skipping to next subject..."
		else		
				echo "Merging BOLDs 10 - 13 for Rest and WM cases run 1 for $CASE..."
				mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13 &> /dev/null
				fslmerge -tr "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_13.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10/10.nii.gz  \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/11/11.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/12/12.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/13/13.nii.gz 0.7
		fi
		fi
		
		if [ "$DatatoMerge" == "14_17_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_17.nii.gz ]; then
					echo "Merging done for selected BOLD data for $CASE. Skipping to next subject..."
		else		
				echo "Merging BOLDs 14 - 17 for Rest and WM cases run 1 for $CASE..."
				mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17 &> /dev/null
				fslmerge -tr "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_17.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14/14.nii.gz  \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/15/15.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/16/16.nii.gz \
				"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/17/17.nii.gz 0.7
		fi
		fi
}

show_usage_boldmergenifti() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "USAGE INFO PENDING..."
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  boldmergecifti - Merge CIFTI files across runs *** needs cleanup
# ------------------------------------------------------------------------------------------------------

boldmergecifti() {

		if [ "$DatatoMerge" == "1_4_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_4_"$STEP".dtseries.nii ]; then
					echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 1 - 4 for Rest and WM cases run 1 for $CASE and $STEP..."
				mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4 &> /dev/null
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_4_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1/1_"$STEP".dtseries.nii  \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/2/2_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/3/3_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/4/4_"$STEP".dtseries.nii 
			done
			cat "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/2/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/3/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/4/Movement_Regressors.txt >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/Movement_Regressors.txt
		fi
		fi

		if [ "$DatatoMerge" == "5_8_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_8_"$STEP".dtseries.nii ]; then
					echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 5 - 8 for Rest and WM cases run 1 for $CASE and $STEP..."
				mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8 &> /dev/null
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_8_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5/5_"$STEP".dtseries.nii  \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/6/6_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/7/7_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/8/8_"$STEP".dtseries.nii 
			done
			cat "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/6/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/7/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/8/Movement_Regressors.txt >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/Movement_Regressors.txt
		fi
		fi

		if [ "$DatatoMerge" == "10_13_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_13_"$STEP".dtseries.nii ]; then
					echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 1 - 4 for Rest and WM cases run 1 for $CASE and $STEP..."
				mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13 &> /dev/null
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_13_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10/10_"$STEP".dtseries.nii  \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/11/11_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/12/12_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/13/13_"$STEP".dtseries.nii 
			done
			cat "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/11/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/12/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/13/Movement_Regressors.txt >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/Movement_Regressors.txt
		fi
		fi

		if [ "$DatatoMerge" == "14_17_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_17_"$STEP".dtseries.nii ]; then
					echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 5 - 8 for Rest and WM cases run 1 for $CASE and $STEP..."
				mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17 &> /dev/null
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_17_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14/14_"$STEP".dtseries.nii  \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/15/15_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/16/16_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/17/17_"$STEP".dtseries.nii 
			done
			cat "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/15/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/16/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/17/Movement_Regressors.txt >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/Movement_Regressors.txt
		fi
		fi

		if [ "$DatatoMerge" == "1_8_orig" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_8/1_8_"$STEP".dtseries.nii ]; then
					echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 1 - 8 for Rest and WM cases run 1 for $CASE and $STEP..."
				mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_8 &> /dev/null
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_8/1_8_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1/1_"$STEP".dtseries.nii  \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/2/2_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/3/3_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/4/4_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5/5_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/6/6_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/7/7_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/8/8_"$STEP".dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/2/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/3/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/4/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/6/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/7/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/8/Movement_Regressors.txt >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_8/Movement_Regressors.txt
		fi
		fi
		
		if [ "$DatatoMerge" == "10_17_orig" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_17/10_17_"$STEP".dtseries.nii ]; then
					echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 10 - 17 for Rest and WM cases run 1 for $CASE and $STEP..."
				mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_17 &> /dev/null
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_17/10_17_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10/10_"$STEP".dtseries.nii  \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/11/11_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/12/12_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/13/13_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14/14_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/15/15_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/16/16_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/17/17_"$STEP".dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/11/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/12/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/13/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/15/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/16/Movement_Regressors.txt \
			"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/17/Movement_Regressors.txt >> "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_17/Movement_Regressors.txt
		fi
		fi

		if [ "$DatatoMerge" == "dp5_dwi" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold1_2_"$STEP".dtseries.nii ]; then
			echo "Merging done for selected BOLD data for $CASE. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 1 & 2 for DWI acquisition for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold1_2_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold1_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold2_"$STEP".dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold1.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold2.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold1_2.use
		fi
		fi
		
		if [ "$DatatoMerge" == "1_8_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold10_8.dtseries.nii ]; then
					echo "Merging done for selected raw BOLD data for $CASE. Skipping to next subject..."
		else		
				echo "Merging BOLDs 1 - 8 for Rest and WM cases run 1 for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold1_8.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold1.dtseries.nii -column 101 -up-to 400 \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold2.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold3.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold4.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold5.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold6.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold7.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold8.dtseries.nii

			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold1.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold2.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold3.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold4.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold5.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold6.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold7.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold8.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold1_8.use
			sed -i -e '1,100d' "$StudyFolder"/"$CASE"/images/functional/movement/bold1_8.use
		fi
		fi
		
		if [ "$DatatoMerge" == "10_17_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold10_17.dtseries.nii ]; then
					echo "Merging done for selected raw BOLD data for $CASE. Skipping to next subject..."
		else	
				echo "Merging BOLDs 10 - 17 for Rest & WM cases run 2 for $CASE..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold10_17.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold10.dtseries.nii -column 101 -up-to 400 \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold11.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold12.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold13.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold14.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold15.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold16.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold17.dtseries.nii

			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold10.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold11.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold12.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold13.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold14.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold15.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold16.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold17.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold10_17.use
			sed -i -e '1,100d' "$StudyFolder"/"$CASE"/images/functional/movement/bold10_17.use
		fi
		fi
		if [ "$DatatoMerge" == "1_8" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold1_8_"$STEP".dtseries.nii ]; then
					echo "Merging done for selected hpss BOLD data for $CASE and $STEP. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 1 - 8 for Rest and WM cases run 1 for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold1_8_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold1_"$STEP".dtseries.nii -column 101 -up-to 400 \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold2_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold3_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold4_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold5_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold6_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold7_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold8_"$STEP"e.dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold1.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold2.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold3.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold4.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold5.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold6.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold7.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold8.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold1_8.use
			sed -i -e '1,100d' "$StudyFolder"/"$CASE"/images/functional/movement/bold1_8.use
		fi
		
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold1_8_"$STEP"_lpss.dtseries.nii ]; then
					echo "Merging done for selected lpss BOLD data for $CASE and $STEP. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 1 - 8 for Rest and WM cases run 1 with lpss for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold1_8_"$STEP"_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold1_"$STEP"_lpss.dtseries.nii -column 101 -up-to 400 \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold2_"$STEP"e_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold3_"$STEP"e_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold4_"$STEP"e_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold5_"$STEP"e_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold6_"$STEP"e_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold7_"$STEP"e_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold8_"$STEP"e_lpss.dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold1.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold2.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold3.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold4.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold5.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold6.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold7.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold8.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold1_8.use
			sed -i -e '1,100d' "$StudyFolder"/"$CASE"/images/functional/movement/bold1_8.use
		fi
		fi
		
		if [ "$DatatoMerge" == "10_17" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold10_17_"$STEP".dtseries.nii ]; then
					echo "Merging done for selected hpss BOLD data for $CASE and $STEP. Skipping to next subject..."
		else	
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 10 - 17 for Rest & WM cases run 2 for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold10_17_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold10_"$STEP".dtseries.nii -column 101 -up-to 400 \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold11_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold12_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold13_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold14_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold15_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold16_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold17_"$STEP"e.dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold10.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold11.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold12.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold13.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold14.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold15.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold16.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold17.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold10_17.use
			sed -i -e '1,100d' "$StudyFolder"/"$CASE"/images/functional/movement/bold10_17.use
		fi
		
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold10_17_"$STEP"_lpss.dtseries.nii ]; then
					echo "Merging done for selected lpss BOLD data for $CASE and $STEP. Skipping to next subject..."
		else	
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 10 - 17 for Rest & WM cases run 2 with lpss for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold10_17_"$STEP"_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold10_"$STEP"_lpss.dtseries.nii -column 101 -up-to 400 \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold11_"$STEP"e_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold12_"$STEP"e_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold13_"$STEP"e_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold14_"$STEP"e_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold15_"$STEP"e_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold16_"$STEP"e_lpss.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold17_"$STEP"e_lpss.dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold10.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold11.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold12.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold13.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold14.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold15.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold16.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold17.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold10_17.use
			sed -i -e '1,100d' "$StudyFolder"/"$CASE"/images/functional/movement/bold10_17.use
		fi
		fi
		
		if [ "$DatatoMerge" == "2_8" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold2_8_"$STEP".dtseries.nii ]; then
			echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 2 - 8 for WM cases run 1 for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold2_8_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold2_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold3_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold4_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold5_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold6_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold7_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold8_"$STEP".dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold2.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold3.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold4.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold5.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold6.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold7.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold8.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold2_8.use
		fi
		fi
		
		if [ "$DatatoMerge" == "11_17" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold11_17_"$STEP".dtseries.nii ]; then
			echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 11 - 17 for WM cases run 2 for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold11_17_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold11_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold12_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold13_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold14_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold15_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold16_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold17_"$STEP".dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold11.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold12.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold13.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold14.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold15.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold16.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold17.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold11_17.use
		fi
		fi
		
		if [ "$DatatoMerge" == "ocd_rest" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold1_3_"$STEP".dtseries.nii ]; then
			echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 1 & 3 for OCD study for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold1_3_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold1_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold3_"$STEP".dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold1.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold3.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold1_3.use
		fi
		fi
		
		if [ "$DatatoMerge" == "ocd_rest_t1000forHCP" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold1_3_t1000forHCP_"$STEP".dtseries.nii ]; then
			echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 1 & 3 for OCD study for HCP for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold1_3_t1000forHCP_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold1_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold3_"$STEP".dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold1.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold3.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold1_3_t1000forHCP.use
		fi
		fi
		
		if [ "$DatatoMerge" == "dp5_wm_run1_t1000forHCP" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold2_4_t1000forHCP_"$STEP".dtseries.nii ]; then
			echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else	
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 2 - 4 for WM cases run 1 matched to HCP (1000 frames) for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold2_4_t1000forHCP_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold2_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold3_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold4_"$STEP".dtseries.nii -column 1 -up-to 200
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold2.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold3.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold4.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold2_4_t1000forHCP.use
			sed -i -e '1001,1200d' "$StudyFolder"/"$CASE"/images/functional/movement/bold2_4_t1000forHCP.use
		fi
		fi
		
		if [ "$DatatoMerge" == "dp5_wm_run1_t2470forHCP" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold2_8_t2470forHCP_"$STEP".dtseries.nii ]; then
			echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 2 - 8 for WM cases run 1 matched to HCP (2470 frames) for  $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold2_8_t2470forHCP_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold2_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold3_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold4_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold5_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold6_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold7_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold8_"$STEP".dtseries.nii -column 1 -up-to 70
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold2.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold3.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold4.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold5.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold6.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold7.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold8.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold2_8_t2470forHCP.use
		sed -i -e '2471,2800d' "$StudyFolder"/"$CASE"/images/functional/movement/bold2_8_t2470forHCP.use
		fi
		fi
		
		if [ "$DatatoMerge" == "hcp_rest_t973forYale" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold1_t973forYale_"$STEP".dtseries.nii ]; then
			echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else
			for STEP in $STEPS
    		do
				echo "Truncating BOLD 1 for HCP cases to match Yale 1000 Frames for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold1_t973forYale_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold1_"$STEP".dtseries.nii -column 1 -up-to 973
			done
			cp "$StudyFolder"/"$CASE"/images/functional/movement/bold1.use "$StudyFolder"/"$CASE"/images/functional/movement/bold1_t973forYale.use
			sed -i -e '974,1200d' "$StudyFolder"/"$CASE"/images/functional/movement/bold1_t973forYale.use
		fi
		fi
		
		if [ "$DatatoMerge" == "hcp_1_2" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold1_2_"$STEP".dtseries.nii ]; then
			echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 1 & 2 for HCP for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/bold1_2_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold1_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/bold2_"$STEP".dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/bold1.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/bold2.use > "$StudyFolder"/"$CASE"/images/functional/movement/bold1_2.use
		fi
		fi

		if [ "$DatatoMerge" == "hcp_1_2_fixica" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/boldfixica1_2.dtseries.nii ]; then
			echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else
				echo "Merging BOLDs 1 & 2 for FIX ICA HCP for $CASE ..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/boldfixica1_2.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica1.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica2.dtseries.nii
				cat "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1.use \
				"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica2.use > "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1_2.use
		fi
		fi
		
		if [ "$DatatoMerge" == "hcp_1_2_fixica_processed" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/bold1_8_"$STEP".dtseries.nii ]; then
			echo "Merging done for selected BOLD data for $CASE and $STEP. Skipping to next subject..."
		else
			for STEP in $STEPS
    		do
				echo "Merging BOLDs 1 & 2 for HCP for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/boldfixica1_2_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica1_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica2_"$STEP".dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica2.use > "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1_2.use
		fi
		fi
		
		if [ "$DatatoMerge" == "fixica1_8_taskonly" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/boldfixica1_8_"$STEP".dtseries.nii ]; then
					echo "Merging done for selected boldfixica data for $CASE and $STEP. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging boldfixicas 1 - 8 for Rest and WM cases run 1 for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/boldfixica1_8_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica1.dtseries.nii -column 101 -up-to 400 \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica2_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica3_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica4_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica5_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica6_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica7_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica8_"$STEP".dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica2.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica3.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica4.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica5.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica6.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica7.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica8.use > "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1_8.use
			sed -i -e '1,100d' "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1_8.use
		fi
		fi
		
		
		if [ "$DatatoMerge" == "fixica10_17_taskonly" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/boldfixica10_17_"$STEP".dtseries.nii ]; then
					echo "Merging done for selected boldfixica data for $CASE and $STEP. Skipping to next subject..."
		else	
			for STEP in $STEPS
    		do
				echo "Merging boldfixicas 10 - 17 for Rest & WM cases run 2 for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/boldfixica10_17_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica10.dtseries.nii -column 101 -up-to 400 \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica11_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica12_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica13_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica14_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica15_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica16_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica17_"$STEP".dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica10.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica11.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica12.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica13.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica14.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica15.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica16.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica17.use > "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica10_17.use
			sed -i -e '1,100d' "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica10_17.use
		fi
		fi		
					
		if [ "$DatatoMerge" == "fixica1_8_processed" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/boldfixica1_8_"$STEP".dtseries.nii ]; then
					echo "Merging done for selected boldfixica data for $CASE and $STEP. Skipping to next subject..."
		else		
			for STEP in $STEPS
    		do
				echo "Merging boldfixicas 1 - 8 for Rest and WM cases run 1 for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/boldfixica1_8_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica1_"$STEP".dtseries.nii -column 101 -up-to 400 \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica2_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica3_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica4_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica5_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica6_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica7_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica8_"$STEP"e.dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica2.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica3.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica4.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica5.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica6.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica7.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica8.use > "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1_8.use
			sed -i -e '1,100d' "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1_8.use
		fi
		fi
		
		
		if [ "$DatatoMerge" == "fixica10_17_processed" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/boldfixica10_17_"$STEP".dtseries.nii ]; then
					echo "Merging done for selected boldfixica data for $CASE and $STEP. Skipping to next subject..."
		else	
			for STEP in $STEPS
    		do
				echo "Merging boldfixicas 10 - 17 for Rest & WM cases run 2 for $CASE and $STEP..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/boldfixica10_17_"$STEP".dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica10_"$STEP".dtseries.nii -column 101 -up-to 400 \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica11_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica12_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica13_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica14_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica15_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica16_"$STEP"e.dtseries.nii \
				-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica17_"$STEP"e.dtseries.nii
			done
			cat "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica10.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica11.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica12.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica13.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica14.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica15.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica16.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica17.use > "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica10_17.use
			sed -i -e '1,100d' "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica10_17.use
		fi
		fi
		
		
		if [ "$DatatoMerge" == "fixica1_8" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/boldfixica1_8.dtseries.nii ]; then
					echo "Merging done for selected boldfixica data for $CASE. Skipping to next subject..."
		else
			rm "$StudyFolder"/"$CASE"/images/functional/boldfixica1_8.dtseries.nii  &> /dev/null 		

			echo "Merging boldfixicas 1 - 8 for Rest and WM cases run 1 for $CASE..."
			wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/boldfixica1_8.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica1.dtseries.nii -column 101 -up-to 400 \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica2.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica3.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica4.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica5.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica6.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica7.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica8.dtseries.nii

			rm "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1_8.use &> /dev/null
			cat "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica2.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica3.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica4.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica5.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica6.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica7.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica8.use > "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1_8.use
			sed -i -e '1,100d' "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1_8.use
		fi
		fi
		
		if [ "$DatatoMerge" == "fixica10_17" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/boldfixica10_17.dtseries.nii ]; then
					echo "Merging done for selected boldfixica data for $CASE. Skipping to next subject..."
		else
			rm "$StudyFolder"/"$CASE"/images/functional/boldfixica10_17.dtseries.nii  &> /dev/null 

			echo "Merging boldfixicas 10 - 17 for Rest & WM cases run 2 for $CASE..."
			wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/boldfixica10_17.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica10.dtseries.nii -column 101 -up-to 400 \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica11.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica12.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica13.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica14.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica15.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica16.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica17.dtseries.nii
			
			rm "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica10_17.use &> /dev/null
			cat "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica10.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica11.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica12.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica13.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica14.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica15.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica16.use \
			"$StudyFolder"/"$CASE"/images/functional/movement/boldfixica17.use > "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica10_17.use
			sed -i -e '1,100d' "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica10_17.use
		fi
		fi

		if [ "$DatatoMerge" == "fixica1_8_demean" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean1_8.dtseries.nii ]; then
					echo "Merging done for selected boldfixica data for $CASE. Skipping to next subject..."
					cp "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1_8.use "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica_demean1_8.use &> /dev/null
		else
			rm "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean1_8.dtseries.nii  &> /dev/null 		

			echo "Merging boldfixicas 1 - 8 for Rest and WM cases run 1 for $CASE..."
			wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean1_8.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean1.dtseries.nii -column 101 -up-to 400 \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean2.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean3.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean4.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean5.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean6.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean7.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean8.dtseries.nii

			cp "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica1_8.use "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica_demean1_8.use &> /dev/null

		fi
		fi
		
		if [ "$DatatoMerge" == "fixica10_17_demean" ]; then
		if [ -f "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean1000_17.dtseries.nii ]; then
					echo "Merging done for selected boldfixica data for $CASE. Skipping to next subject..."
					cp "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica10_17.use "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica_demean10_17.use &> /dev/null
		else
			rm "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean10_17.dtseries.nii  &> /dev/null 

			echo "Merging boldfixicas 10 - 17 for Rest & WM cases run 2 for $CASE..."
			wb_command -cifti-merge "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean10_17.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean10.dtseries.nii -column 101 -up-to 400 \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean11.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean12.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean13.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean14.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean15.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean16.dtseries.nii \
			-cifti "$StudyFolder"/"$CASE"/images/functional/boldfixica_demean17.dtseries.nii
			
			cp "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica10_17.use "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica_demean10_17.use &> /dev/null

		fi
		fi

}

show_usage_boldmergecifti() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "USAGE INFO PENDING..."
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  boldseparateciftifixica - Separate CIFTI files across runs *** needs cleanup
# ------------------------------------------------------------------------------------------------------


boldseparateciftifixica() {
		
		
		if [ "$DatatoSeparate" == "1_4_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/4_hp2000_clean.nii.gz ]; then
					echo "Separating done for selected BOLD data for $CASE. Skipping to next subject..."
		else		
				echo "Separating CIFTI BOLDs 1 - 4 for $CASE..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_4_Atlas_hp2000_clean.dtseries.nii -column 1 -up-to 400
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/2_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_4_Atlas_hp2000_clean.dtseries.nii -column 401 -up-to 800
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/3_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_4_Atlas_hp2000_clean.dtseries.nii -column 801 -up-to 1200
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/4_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_4_Atlas_hp2000_clean.dtseries.nii -column 1201 -up-to 1600

				echo "Separating NIFTI BOLDs 1 - 4 for $CASE..."
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_4_hp2000_clean.nii.gz -subvolume 1 -up-to 400
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/2_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_4_hp2000_clean.nii.gz -subvolume 401 -up-to 800
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/3_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_4_hp2000_clean.nii.gz -subvolume 801 -up-to 1200
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/4_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_4_hp2000_clean.nii.gz -subvolume 1201 -up-to 1600
				
				echo "Cleaning old hard links for BOLDs 1 - 4 for $CASE..."
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica1.nii &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica2.nii &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica3.nii &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica4.nii &> /dev/null
	
				echo "Gzipping BOLDs 1 - 4 for $CASE..."	
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_hp2000_clean.nii &> /dev/null
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/2_hp2000_clean.nii &> /dev/null
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/3_hp2000_clean.nii &> /dev/null
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/4_hp2000_clean.nii &> /dev/null

				# Setup hard links for separated cleaned images
				echo "Setting up hard links for BOLDs 1 - 4 for $CASE..."				
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica1.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/2_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica2.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/3_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica3.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/4_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica4.dtseries.nii
				
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica1.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/2_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica2.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/3_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica3.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/4_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica4.nii.gz
		fi
		fi
		
		if [ "$DatatoSeparate" == "5_8_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/8_hp2000_clean.nii.gz ]; then
					echo "Separating done for selected BOLD data for $CASE. Skipping to next subject..."
		else		
				echo "Separating CIFTI BOLDs 5 - 8 for $CASE..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_8_Atlas_hp2000_clean.dtseries.nii -column 1 -up-to 400
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/6_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_8_Atlas_hp2000_clean.dtseries.nii -column 401 -up-to 800
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/7_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_8_Atlas_hp2000_clean.dtseries.nii -column 801 -up-to 1200
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/8_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_8_Atlas_hp2000_clean.dtseries.nii -column 1201 -up-to 1600

				echo "Separating NIFTI BOLDs 5 - 8 for $CASE..."
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_8_hp2000_clean.nii.gz -subvolume 1 -up-to 400
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/6_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_8_hp2000_clean.nii.gz -subvolume 401 -up-to 800
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/7_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_8_hp2000_clean.nii.gz -subvolume 801 -up-to 1200
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/8_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_8_hp2000_clean.nii.gz -subvolume 1201 -up-to 1600

				echo "Cleaning old hard links for BOLDs 5 - 8 for $CASE..."
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica5.nii &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica6.nii &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica7.nii &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica8.nii &> /dev/null

				echo "Gzipping BOLDs 5 - 8 for $CASE..."	
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_hp2000_clean.nii &> /dev/null
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/6_hp2000_clean.nii &> /dev/null
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/7_hp2000_clean.nii &> /dev/null
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/8_hp2000_clean.nii &> /dev/null
				
				# Setup hard links for separated cleaned images
				echo "Setting up hard links for BOLDs 5 - 8 for $CASE..."				
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica5.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/6_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica6.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/7_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica7.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/8_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica8.dtseries.nii

				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica5.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/6_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica6.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/7_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica7.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/8_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica8.nii.gz
		fi
		fi
		
		if [ "$DatatoSeparate" == "10_13_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/13_hp2000_clean.nii.gz ]; then
					echo "Separating done for selected BOLD data for $CASE. Skipping to next subject..."
		else		
				echo "Separating CIFTI BOLDs 10 - 13 for $CASE..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_13_Atlas_hp2000_clean.dtseries.nii -column 1 -up-to 400
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/11_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_13_Atlas_hp2000_clean.dtseries.nii -column 401 -up-to 800
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/12_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_13_Atlas_hp2000_clean.dtseries.nii -column 801 -up-to 1200
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/13_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_13_Atlas_hp2000_clean.dtseries.nii -column 1201 -up-to 1600

				echo "Separating NIFTI BOLDs 10 - 13 for $CASE..."
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_13_hp2000_clean.nii.gz -subvolume 1 -up-to 400
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/11_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_13_hp2000_clean.nii.gz -subvolume 401 -up-to 800
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/12_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_13_hp2000_clean.nii.gz -subvolume 801 -up-to 1200
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/13_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_13_hp2000_clean.nii.gz -subvolume 1201 -up-to 1600

				echo "Cleaning old hard links for BOLDs 10 - 13 for $CASE..."
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica10.nii &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica11.nii &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica12.nii &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica13.nii &> /dev/null
	
				echo "Gzipping BOLDs 10 - 13 for $CASE..."
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_hp2000_clean.nii &> /dev/null 
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/11_hp2000_clean.nii &> /dev/null 
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/12_hp2000_clean.nii &> /dev/null
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/13_hp2000_clean.nii &> /dev/null
				
				# Setup hard links for separated cleaned images
				echo "Setting up hard links for BOLDs 10 - 13 for $CASE..."
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica10.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/11_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica11.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/12_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica12.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/13_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica13.dtseries.nii

				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica10.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/11_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica11.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/12_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica12.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/13_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica13.nii.gz
		fi
		fi
		
		if [ "$DatatoSeparate" == "14_17_raw" ]; then
		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/17_hp2000_clean.nii.gz ]; then
					echo "Separating done for selected BOLD data for $CASE. Skipping to next subject..."
		else		
				echo "Separating CIFTI BOLDs 14 - 17 for $CASE..."
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_17_Atlas_hp2000_clean.dtseries.nii -column 1 -up-to 400
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/15_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_17_Atlas_hp2000_clean.dtseries.nii -column 401 -up-to 800
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/16_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_17_Atlas_hp2000_clean.dtseries.nii -column 801 -up-to 1200
				wb_command -cifti-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/17_Atlas_hp2000_clean.dtseries.nii -cifti "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_17_Atlas_hp2000_clean.dtseries.nii -column 1201 -up-to 1600

				echo "Separating NIFTI BOLDs 14 - 17 for $CASE..."
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_17_hp2000_clean.nii.gz -subvolume 1 -up-to 400
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/15_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_17_hp2000_clean.nii.gz -subvolume 401 -up-to 800
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/16_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_17_hp2000_clean.nii.gz -subvolume 801 -up-to 1200
				wb_command -volume-merge "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/17_hp2000_clean.nii -volume "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_17_hp2000_clean.nii.gz -subvolume 1201 -up-to 1600

				echo "Cleaning old hard links for BOLDs 14 - 17 for $CASE..."
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica14.nii &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica15.nii &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica16.nii &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica17.nii &> /dev/null
	
				echo "Gzipping BOLDs 14 - 17 for $CASE..."
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_hp2000_clean.nii &> /dev/null
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/15_hp2000_clean.nii &> /dev/null
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/16_hp2000_clean.nii &> /dev/null
				gzip -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/17_hp2000_clean.nii &> /dev/null
				
				# Setup hard links for separated cleaned images
				echo "Setting up hard links for BOLDs 14 - 17 for $CASE..."
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica14.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/15_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica15.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/16_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica16.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/17_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica17.dtseries.nii

				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica14.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/15_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica15.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/16_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica16.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/17_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica17.nii.gz
		fi
		fi
		
}

show_usage_boldseparateciftifixica() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "USAGE INFO PENDING..."
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  bolddense - Compute the dense connectome file for BOLD timeseries
# ------------------------------------------------------------------------------------------------------

bolddense() {

 		for STEP in $STEPS
    		do
					for BOLD in $BOLDS
					do
						if [ -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dconn.nii ]; then
							echo "Dense Connectome Computed for this for $CASE and $STEP. Skipping to next..."
						else		
					    	echo "Running Dense Connectome on BOLD data for $CASE... (need ~30GB free RAM at any one time per subject)"
							# Dense connectome command - use in isolation due to RAM limits (need ~30GB free at any one time per subject)
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP".dconn.nii
						fi
					done
			done
}

show_usage_bolddense() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "USAGE INFO PENDING..."
    			echo ""
}


# ------------------------------------------------------------------------------------------------------
#  fixica - Compute FIX ICA cleanup on BOLD timeseries following hcp pipelines 
# ------------------------------------------------------------------------------------------------------

fixica() {

		for BOLD in $BOLDS
			do
				if [ "$Overwrite" == "yes" ]; then
					rm -r "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD"*_hp2000*  &> /dev/null
				fi		
				
				
				if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas_hp2000_clean.dtseries.nii ]; then
						echo "FIX ICA Computed for this for $CASE and $BOLD. Skipping to next..."
				else		
					    echo "Running FIX ICA on $BOLD data for $CASE... (note: this uses Melodic which is a slow single-threaded process)"
						rm -r *hp2000* &> /dev/null
						"$FIXICADIR"/hcp_fix.sh "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD".nii.gz 2000
				fi
		done

}

show_usage_fixica() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "USAGE INFO FOR FIX ICA PENDING..."
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  postfix - Compute PostFix code on FIX ICA cleaned BOLD timeseries to generate scene files
# ------------------------------------------------------------------------------------------------------

postfix() {

		for BOLD in $BOLDS
			do
				if [ "$Overwrite" == "yes" ]; then
					rm -r "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$CASE"_"$BOLD"_ICA_Classification_singlescreen.scene   &> /dev/null
				fi					
					
				if [ -f  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$CASE"_"$BOLD"_ICA_Classification_singlescreen.scene ]; then
						echo "PostFix Computed for this for $CASE and $BOLD. Skipping to next..."
			else	
					    echo "Running PostFix script on $BOLD data for $CASE... "						
						"$POSTFIXICADIR"/GitRepo/PostFix.sh "$StudyFolder"/"$CASE"/hcp "$CASE" "$BOLD" /usr/local/PostFix_beta/GitRepo "$HighPass" wb_command /usr/local/PostFix_beta/GitRepo/PostFixScenes/ICA_Classification_DualScreenTemplate.scene /usr/local/PostFix_beta/GitRepo/PostFixScenes/ICA_Classification_SingleScreenTemplate.scene
				fi
			done
}

show_usage_postfix() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "USAGE INFO PENDING ... "
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  boldhardlinkfixica - Generate links for FIX ICA cleaned BOLDs for functional connectivity (dofcMRI)
# ------------------------------------------------------------------------------------------------------

boldhardlinkfixica() {
		
		BOLDCount=0
		for BOLD in $BOLDS
			do	
				BOLDCount=$((BOLDCount+1))
				echo "Setting up hard links following FIX ICA for BOLD# $BOLD for $CASE... "
				
				# setup folder strucrture if missing
				mkdir "$StudyFolder"/"$CASE"/images    &> /dev/null
				mkdir "$StudyFolder"/"$CASE"/images/functional	    &> /dev/null
				mkdir "$StudyFolder"/"$CASE"/images/functional/movement    &> /dev/null
				
				# setup hard links for images						
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii     &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".nii.gz     &> /dev/null
				
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD"_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD".nii.gz "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".nii.gz
				
				#rm "$StudyFolder"/"$CASE"/images/functional/boldfixicarfMRI_REST*     &> /dev/null
				#rm "$StudyFolder"/"$CASE"/images/functional/boldrfMRI_REST*     &> /dev/null
				
				echo "Setting up hard links for movement data for BOLD# $BOLD for $CASE... "
				
				# Clean up movement regressor file to match dofcMRIp convention and copy to movement directory
				export PATH=/usr/local/opt/gnu-sed/libexec/gnubin:$PATH     &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD"_mov.dat     &> /dev/null
				rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit*     &> /dev/null
				cp "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/Movement_Regressors.txt "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit.txt 		
				sed -i.bak -E 's/.{67}$//' "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit.txt 		
				nl "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit.txt > "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit_fin.txt	
				sed -i.bak '1i\#frame     dx(mm)     dy(mm)     dz(mm)     X(deg)     Y(deg)     Z(deg)' "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"//Movement_Regressors_edit_fin.txt	
				cp "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit_fin.txt "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD"_mov.dat			
				rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit*     &> /dev/null
						
			done		
}

show_usage_boldhardlinkfixica() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Function for hard-linking minimally preprocessed HCP BOLD images after FIX ICA was done for further denoising."
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  fixicainsertmean - Re-insert means into FIX ICA cleaned BOLDs for connectivity preprocessing (dofcMRI)
# ------------------------------------------------------------------------------------------------------

fixicainsertmean() {

		for BOLD in $BOLDS
			do		
					cd "$StudyFolder"/"$CASE"/images/functional/
					# First check if the boldfixica file has the mean inserted
					3dBrickStat -mean -non-zero boldfixica"$BOLD".nii.gz[1] >> boldfixica"$BOLD"_mean.txt
					ImgMean=`cat boldfixica"$BOLD"_mean.txt`
					if [ $(echo " $ImgMean > 1000" | bc) -eq 1 ]; then
					echo "1st frame mean=$ImgMean Mean inserted OK for subject $CASE and bold# $BOLD. Skipping to next..."
						else
						# Next check if the boldfixica file has the mean inserted twice by accident
						if [ $(echo " $ImgMean > 15000" | bc) -eq 1 ]; then
						echo "1st frame mean=$ImgMean ERROR: Mean has been inserted twice for $CASE and $BOLD."	
							else
							# Command that inserts mean image back to the boldfixica file using g_InsertMean matlab function
							echo "Re-inserting mean image on the mapped $BOLD data for $CASE... "
							matlab -nosplash -nodisplay -nojvm -r "g_InsertMean(['bold' num2str($BOLD) '.dtseries.nii'], ['boldfixica' num2str($BOLD) '.dtseries.nii']),g_InsertMean(['bold' num2str($BOLD) '.nii.gz'], ['boldfixica' num2str($BOLD) '.nii.gz']),quit()"

						fi
					fi
					rm boldfixica"$BOLD"_mean.txt &> /dev/null
			done
}

show_usage_fixicainsertmean() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Function for imputing mean of the image after FIX ICA was done for further denoising."
    			echo ""
}


# ------------------------------------------------------------------------------------------------------
#  fixicaremovemean - Remove means from FIX ICA cleaned BOLDs for functional connectivity analysis
# ------------------------------------------------------------------------------------------------------

fixicaremovemean() {

		for BOLD in $BOLDS
			do		
					cd "$StudyFolder"/"$CASE"/images/functional/
					# First check if the boldfixica file has the mean inserted
					#3dBrickStat -mean -non-zero boldfixica"$BOLD".nii.gz[1] >> boldfixica"$BOLD"_mean.txt
					#ImgMean=`cat boldfixica"$BOLD"_mean.txt`
					#if [ $(echo " $ImgMean < 1000" | bc) -eq 1 ]; then
					#echo "1st frame mean=$ImgMean Mean removed OK for subject $CASE and bold# $BOLD. Skipping to next..."
					#	else
						# Next check if the boldfixica file has the mean inserted twice by accident
					#	if [ $(echo " $ImgMean > 15000" | bc) -eq 1 ]; then
					#	echo "1st frame mean=$ImgMean ERROR: Mean has been inserted twice for $CASE and $BOLD."	
					#		else
							# Command that inserts mean image back to the boldfixica file using g_InsertMean matlab function
							echo "Removing mean image on the mapped CIFTI FIX ICA $BOLD data for $CASE... "
							matlab -nosplash -nodisplay -nojvm -r "g_RemoveMean(['bold' num2str($BOLD) '.dtseries.nii'], ['boldfixica' num2str($BOLD) '.dtseries.nii'], ['boldfixica_demean' num2str($BOLD) '.dtseries.nii']),quit()"
						#fi
					#fi
					#rm boldfixica"$BOLD"_mean.txt &> /dev/null
			done
}

show_usage_fixicaremovemean() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Function for removing the mean of the image after FIX ICA was done for further denoising."
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  boldhardlinkfixicamerged - Generate links for FIX ICA cleaned BOLDs for functional connectivity (dofcMRI)
# ------------------------------------------------------------------------------------------------------


boldhardlinkfixicamerged() {
				
				echo "Setting up hard links for BOLDs 1 - 4, 5 - 8, 10 - 13, 14 - 17 for $CASE..."	
							
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica1.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/2_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica2.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/3_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica3.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/4_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica4.dtseries.nii
				
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/1_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica1.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/2_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica2.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/3_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica3.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/1_4/4_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica4.nii.gz

				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica5.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/6_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica6.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/7_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica7.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/8_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica8.dtseries.nii

				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/5_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica5.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/6_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica6.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/7_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica7.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/5_8/8_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica8.nii.gz
	
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica10.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/11_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica11.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/12_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica12.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/13_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica13.dtseries.nii

				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/10_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica10.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/11_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica11.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/12_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica12.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/10_13/13_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica13.nii.gz

				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica14.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/15_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica15.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/16_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica16.dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/17_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica17.dtseries.nii

				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/14_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica14.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/15_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica15.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/16_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica16.nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/14_17/17_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica17.nii.gz

}	

show_usage_boldhardlinkfixicamerged() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Function for hard-linking minimally preprocessed and merged HCP BOLD images after FIX ICA was done for further denoising."
    			echo ""
    			echo "NOTE: This function needs cleanup as it was designed for a specific study"
    			echo ""
}			

#########################################################################################################################
#########################################################################################################################
################################################  HCP Pipeline Wrapper Functions ########################################
#########################################################################################################################
#########################################################################################################################

# ------------------------------------------------------------------------------------------------------
#  hcp1 - Executes the PreFreeSurfer Script
# ------------------------------------------------------------------------------------------------------

hcp1_orig() {

		########################################## INPUTS ########################################## 

		#Scripts called by this script do NOT assume anything about the form of the input names or paths.
		#This batch script assumes the HCP raw data naming convention, e.g.

		#	${StudyFolder}/${Subject}T1w_MPR1/${Subject}_3T_T1w_MPR1.nii.gz
		#	${StudyFolder}/${Subject}T1w_MPR2/${Subject}_3T_T1w_MPR2.nii.gz

		#	${StudyFolder}/${Subject}T2w_SPC1/${Subject}_3T_T2w_SPC1.nii.gz
		#	${StudyFolder}/${Subject}T2w_SPC2/${Subject}_3T_T2w_SPC2.nii.gz

		#	${StudyFolder}/${Subject}T1w_MPR1/${Subject}_3T_FieldMap_Magnitude.nii.gz
		#	${StudyFolder}/${Subject}T1w_MPR1/${Subject}_3T_FieldMap_Phase.nii.gz

		#Change Scan Settings: FieldMap Delta TE, Sample Spacings, and $UnwarpDir to match your images

		#If using gradient distortion correction, use the coefficents from your scanner
		#The HCP gradient distortion coefficents are only available through Siemens
		#Gradient distortion in standard scanners like the Trio is much less than for the HCP Skyra.

		######################################### DO WORK ##########################################

		
		#EnvironmentScript="$StudyFolder/../../../fcMRI/hcpsetup.sh" #Pipeline environment script
		cd "$StudyFolder"/../../../fcMRI/hcp.logs/

		# Requirements for this function
		#  installed versions of: FSL5.0.2 or higher , FreeSurfer (version 5.2 or higher) , gradunwarp (python code from MGH)
		#  environment: FSLDIR , FREESURFER_HOME , HCPPIPEDIR , CARET7DIR , PATH (for gradient_unwarp.py)

		#Set up pipeline environment variables and software
		#. ${EnvironmentScript}

		# Log the originating call
		echo "$@"

			Subject="$CASE"
    		#Input Images
 			#Detect Number of T1w Images
  			numT1ws=`ls ${StudyFolder}/${Subject} | grep T1w | wc -l`
  			T1wInputImages=""
  			i=1
  			while [ $i -le $numT1ws ] ; do
    			T1wInputImages=`echo "${T1wInputImages}${StudyFolder}/${Subject}/T1w/${Subject}_strc_T1w_MPR${i}.nii.gz@"`
    			i=$(($i+1))
  			done
  
  			#Detect Number of T2w Images
  			numT2ws=`ls ${StudyFolder}/${Subject} | grep T2w | wc -l`
  			T2wInputImages=""
  			i=1
 			while [ $i -le $numT2ws ] ; do
    			T2wInputImages=`echo "${T2wInputImages}${StudyFolder}/${Subject}/T2w/${Subject}_strc_T2w_SPC${i}.nii.gz@"`
    			i=$(($i+1))
  			done
  			
  			MagnitudeInputName="${StudyFolder}/${Subject}/FieldMap_strc/${Subject}_strc_FieldMap_Magnitude.nii.gz" #Expects 4D magitude volume with two 3D timepoints or "NONE" if not used
  			PhaseInputName="${StudyFolder}/${Subject}/FieldMap_strc/${Subject}_strc_FieldMap_Phase.nii.gz" #Expects 3D phase difference volume or "NONE" if not used
  
  			SpinEchoPhaseEncodeNegative="NONE" #For the spin echo field map volume with a negative phase encoding direction (LR in HCP data), set to NONE if using regular FIELDMAP
  			SpinEchoPhaseEncodePositive="NONE" #For the spin echo field map volume with a positive phase encoding direction (RL in HCP data), set to NONE if using regular FIELDMAP

  			#Templates -- NOTE: Alan changed to match Yale acquisition
  			T1wTemplate="${HCPPIPEDIR_Templates}/MNI152_T1_0.8mm.nii.gz" #MNI0.8mm template
  			T1wTemplateBrain="${HCPPIPEDIR_Templates}/MNI152_T1_0.8mm_brain.nii.gz" #Brain extracted MNI0.8mm template
  			T1wTemplate2mm="${HCPPIPEDIR_Templates}/MNI152_T1_2mm.nii.gz" #MNI2mm template
  			T2wTemplate="${HCPPIPEDIR_Templates}/MNI152_T2_0.8mm.nii.gz" #MNI0.8mm T2wTemplate
  			T2wTemplateBrain="${HCPPIPEDIR_Templates}/MNI152_T2_0.8mm_brain.nii.gz" #Brain extracted MNI0.8mm T2wTemplate
  			T2wTemplate2mm="${HCPPIPEDIR_Templates}/MNI152_T2_2mm.nii.gz" #MNI2mm T2wTemplate
  			TemplateMask="${HCPPIPEDIR_Templates}/MNI152_T1_0.8mm_brain_mask.nii.gz" #Brain mask MNI0.8mm template
  			Template2mmMask="${HCPPIPEDIR_Templates}/MNI152_T1_2mm_brain_mask_dil.nii.gz" #MNI2mm template

  			#Scan Settings -- NOTE: Alan changed to match Yale acquisition
  			TE="2.46" #delta TE in ms for field map or "NONE" if not used
  			DwellTime="NONE" #Echo Spacing or Dwelltime of Spin Echo Field Map or "NONE" if not used
  			SEUnwarpDir="NONE" #x or y (minus or not does not matter) "NONE" if not used 
  			T1wSampleSpacing="0.0000065" #DICOM field (0019,1018) in s or "NONE" if not used
  			T2wSampleSpacing="0.0000021" #DICOM field (0019,1018) in s or "NONE" if not used
  			UnwarpDir="z" #z appears to be best or "NONE" if not used
  			#GradientDistortionCoeffs="NONE" #Location of Coeffs file or "NONE" to skip
  			#GradientDistortionCoeffs="${HCPPIPEDIR_Config}/coeff_SC72C_Skyra.grad" #Location of Coeffs file or "NONE" to skip
  			GradientDistortionCoeffs="${HCPPIPEDIR_Config}/Trio_coeff.grad" #Location of Coeffs file or "NONE" to skip

  			#Config Settings
  			BrainSize="150" #BrainSize in mm, 150 for humans
  			FNIRTConfig="${HCPPIPEDIR_Config}/T1_2_MNI152_2mm.cnf" #FNIRT 2mm T1w Config
  			AvgrdcSTRING="FIELDMAP" #Averaging and readout distortion correction methods: "NONE" = average any repeats with no readout correction "FIELDMAP" = average any repeats and use field map for readout correction "TOPUP" = average and distortion correct at the same time with topup/applytopup only works for 2 images currently
  			TopupConfig="NONE" #Config for topup or "NONE" if not used

  		if [ "$Cluster" == 1 ]; then
  		
     		${HCPPIPEDIR}/PreFreeSurfer/PreFreeSurferPipeline.sh \
      		--path="$StudyFolder" \
      		--subject="$Subject" \
      		--t1="$T1wInputImages" \
      		--t2="$T2wInputImages" \
      		--t1template="$T1wTemplate" \
      		--t1templatebrain="$T1wTemplateBrain" \
      		--t1template2mm="$T1wTemplate2mm" \
      		--t2template="$T2wTemplate" \
      		--t2templatebrain="$T2wTemplateBrain" \
      		--t2template2mm="$T2wTemplate2mm" \
      		--templatemask="$TemplateMask" \
      		--template2mmmask="$Template2mmMask" \
      		--brainsize="$BrainSize" \
      		--fnirtconfig="$FNIRTConfig" \
      		--fmapmag="$MagnitudeInputName" \
      		--fmapphase="$PhaseInputName" \
      		--echodiff="$TE" \
      		--SEPhaseNeg="$SpinEchoPhaseEncodeNegative" \
      		--SEPhasePos="$SpinEchoPhaseEncodePositive" \
      		--echospacing="$DwellTime" \
      		--seunwarpdir="$SEUnwarpDir" \
      		--t1samplespacing="$T1wSampleSpacing" \
      		--t2samplespacing="$T2wSampleSpacing" \
      		--unwarpdir="$UnwarpDir" \
      		--gdcoeffs="$GradientDistortionCoeffs" \
      		--avgrdcmethod="$AvgrdcSTRING" \
      		--topupconfig="$TopupConfig" \
      		--printcom=$PRINTCOM
    	
    	else

    		fsl_sub."$fslsub" -Q "$QUEUE" \
     		${HCPPIPEDIR}/PreFreeSurfer/PreFreeSurferPipeline.sh \
      		--path="$StudyFolder" \
      		--subject="$Subject" \
      		--t1="$T1wInputImages" \
      		--t2="$T2wInputImages" \
      		--t1template="$T1wTemplate" \
      		--t1templatebrain="$T1wTemplateBrain" \
      		--t1template2mm="$T1wTemplate2mm" \
      		--t2template="$T2wTemplate" \
      		--t2templatebrain="$T2wTemplateBrain" \
      		--t2template2mm="$T2wTemplate2mm" \
      		--templatemask="$TemplateMask" \
      		--template2mmmask="$Template2mmMask" \
      		--brainsize="$BrainSize" \
      		--fnirtconfig="$FNIRTConfig" \
      		--fmapmag="$MagnitudeInputName" \
      		--fmapphase="$PhaseInputName" \
      		--echodiff="$TE" \
      		--SEPhaseNeg="$SpinEchoPhaseEncodeNegative" \
      		--SEPhasePos="$SpinEchoPhaseEncodePositive" \
      		--echospacing="$DwellTime" \
      		--seunwarpdir="$SEUnwarpDir" \
      		--t1samplespacing="$T1wSampleSpacing" \
      		--t2samplespacing="$T2wSampleSpacing" \
      		--unwarpdir="$UnwarpDir" \
      		--gdcoeffs="$GradientDistortionCoeffs" \
      		--avgrdcmethod="$AvgrdcSTRING" \
      		--topupconfig="$TopupConfig" \
      		--printcom=$PRINTCOM
    	fi
    	
    	# The following lines are used for interactive debugging to set the positional parameters: $1 $2 $3 ...
  		echo "set -- --path=${StudyFolder} \
      		--subject=${Subject} \
      		--t1=${T1wInputImages} \
          	--t2=${T2wInputImages} \
          	--t1template=${T1wTemplate} \
          	--t1templatebrain=${T1wTemplateBrain} \
          	--t1template2mm=${T1wTemplate2mm} \
          	--t2template=${T2wTemplate} \
          	--t2templatebrain=${T2wTemplateBrain} \
          	--t2template2mm=${T2wTemplate2mm} \
          	--templatemask=${TemplateMask} \
          	--template2mmmask=${Template2mmMask} \
          	--brainsize=${BrainSize} \
          	--fnirtconfig=${FNIRTConfig} \
          	--fmapmag=${MagnitudeInputName} \
          	--fmapphase=${PhaseInputName} \
          	--echodiff=${TE} \
          	--SEPhaseNeg=${SpinEchoPhaseEncodeNegative} \
          	--SEPhasePos=${SpinEchoPhaseEncodePositive} \
          	--echospacing=${DwellTime} \
          	--seunwarpdir=${SEUnwarpDir} \     
          	--t1samplespacing=${T1wSampleSpacing} \
          	--t2samplespacing=${T2wSampleSpacing} \
          	--unwarpdir=${UnwarpDir} \
          	--gdcoeffs=${GradientDistortionCoeffs} \
          	--avgrdcmethod=${AvgrdcSTRING} \
          	--topupconfig=${TopupConfig} \
          	--printcom=${PRINTCOM}"

  			#echo ". ${EnvironmentScript}"
  		
}

show_usage_hcp1_orig() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Original implementation of the PreFreeSurfer (hcp1) code."
    			echo ""
    			echo "Note: This function is deprecated as of 01/2017. The maintained function is hcp1, called via gmri functions."
    			echo "		--> run ap ?hcp1 for up-to-date help call of the supported function"
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  hcp2 - Executes the FreeSurfer Script
# ------------------------------------------------------------------------------------------------------

hcp2_orig() {

		# Cleanup FS run if force flag on
		
		if [ "$Overwrite" == "yes" ]; then
			rm -r "$StudyFolder"/"$CASE"/T1w/"$CASE"   &> /dev/null
		fi
		
		#EnvironmentScript="$StudyFolder/../../../fcMRI/hcpsetup.sh" #Pipeline environment script
		cd "$StudyFolder"/../../../fcMRI/hcp.logs/

		# Requirements for this function
		#  installed versions of: FSL5.0.2 or higher , FreeSurfer (version 5.2 or higher) , gradunwarp (python code from MGH)
		#  environment: FSLDIR , FREESURFER_HOME , HCPPIPEDIR , CARET7DIR , PATH (for gradient_unwarp.py)

		#Set up pipeline environment variables and software
		#. ${EnvironmentScript}

		# Log the originating call
		echo "$@"
		
		########################################## INPUTS ########################################## 

		#Scripts called by this function do assume they run on the outputs of the PreFreeSurfer Pipeline

		######################################### DO WORK ##########################################

		#Input Variables
		Subject="$CASE"
  		SubjectID="$CASE" #FreeSurfer Subject ID Name
   		SubjectDIR="${StudyFolder}/${Subject}/T1w" #Location to Put FreeSurfer Subject's Folder
  		T1wImage="${StudyFolder}/${Subject}/T1w/T1w_acpc_dc_restore.nii.gz" #T1w FreeSurfer Input (Full Resolution)
  		T1wImageBrain="${StudyFolder}/${Subject}/T1w/T1w_acpc_dc_restore_brain.nii.gz" #T1w FreeSurfer Input (Full Resolution)
  		T2wImage="${StudyFolder}/${Subject}/T1w/T2w_acpc_dc_restore.nii.gz" #T2w FreeSurfer Input (Full Resolution)

  		if [ "$Cluster" == 1 ]; then
     		${HCPPIPEDIR}/FreeSurfer/FreeSurferPipeline.sh \
      		--subject="$Subject" \
      		--subjectDIR="$SubjectDIR" \
      		--t1="$T1wImage" \
      		--t1brain="$T1wImageBrain" \
      		--t2="$T2wImage" \
      		--printcom=$PRINTCOM
  		else 
    		fsl_sub."$fslsub" -T 5000 -Q "$QUEUE" \
     		${HCPPIPEDIR}/FreeSurfer/FreeSurferPipeline.sh \
      		--subject="$Subject" \
      		--subjectDIR="$SubjectDIR" \
      		--t1="$T1wImage" \
      		--t1brain="$T1wImageBrain" \
      		--t2="$T2wImage" \
      		--printcom=$PRINTCOM
  		fi
  		 
  		# The following lines are used for interactive debugging to set the positional parameters: $1 $2 $3 ...
  		echo "set -- --subject={$Subject} \
      		--subjectDIR={$SubjectDIR} \
      		--t1={$T1wImage} \
      		--t1brain={$T1wImageBrain} \
      		--t2={$T2wImage} \
      		--printcom=$PRINTCOM"

  		#echo ". ${EnvironmentScript}"
}

show_usage_hcp2_orig() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Original implementation of the FreeSurfer (hcp2) code."
    			echo ""
    			echo "Note: This function is deprecated as of 01/2017. The maintained function is hcp2, called via gmri functions."
    			echo "		--> run ap ?hcp2 for up-to-date help call of the supported function"
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  hcp3 - Executes the PostFreeSurfer Script
# ------------------------------------------------------------------------------------------------------

hcp3_orig() {
		
		#EnvironmentScript="$StudyFolder/../../../fcMRI/hcpsetup.sh" #Pipeline environment script
		cd "$StudyFolder"/../../../fcMRI/hcp.logs/
		rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/* &> /dev/null

		# Requirements for this function
		#  installed versions of: FSL5.0.2 or higher , FreeSurfer (version 5.2 or higher) , gradunwarp (python code from MGH)
		#  environment: FSLDIR , FREESURFER_HOME , HCPPIPEDIR , CARET7DIR , PATH (for gradient_unwarp.py)

		#Set up pipeline environment variables and software
		#. ${EnvironmentScript}

		# Log the originating call
		echo "$@"
		
		########################################## INPUTS ########################################## 

		#Scripts called by this script do assume they run on the outputs of the FreeSurfer Pipeline

		######################################### DO WORK ##########################################

		#Input Variables
 		SurfaceAtlasDIR="${HCPPIPEDIR_Templates}/standard_mesh_atlases" #(Need to rename make surf.gii and add 32k)
  		GrayordinatesSpaceDIR="${HCPPIPEDIR_Templates}/91282_Greyordinates" #(Need to copy these in)
  		GrayordinatesResolution="2" #Usually 2mm
  		HighResMesh="164" #Usually 164k vertices
  		LowResMesh="32" #Usually 32k vertices
  		SubcorticalGrayLabels="${HCPPIPEDIR_Config}/FreeSurferSubcorticalLabelTableLut.txt"
  		FreeSurferLabels="${HCPPIPEDIR_Config}/FreeSurferAllLut.txt"
  		ReferenceMyelinMaps="${HCPPIPEDIR_Templates}/standard_mesh_atlases/Conte69.MyelinMap_BC.164k_fs_LR.dscalar.nii"
  		RegName="FS" #MSMSulc is recommended, if binary is not available use FS (FreeSurfer)
  		Subject="$CASE"

  		if [ "$Cluster" == 1 ]; then
     		${HCPPIPEDIR}/PostFreeSurfer/PostFreeSurferPipeline.sh \
      		--path="$StudyFolder" \
      		--subject="$Subject" \
      		--surfatlasdir="$SurfaceAtlasDIR" \
      		--grayordinatesdir="$GrayordinatesSpaceDIR" \
      		--grayordinatesres="$GrayordinatesResolution" \
      		--hiresmesh="$HighResMesh" \
      		--lowresmesh="$LowResMesh" \
      		--subcortgraylabels="$SubcorticalGrayLabels" \
      		--freesurferlabels="$FreeSurferLabels" \
      		--refmyelinmaps="$ReferenceMyelinMaps" \
      		--regname="$RegName" \
      		--printcom=$PRINTCOM
  		else 
    		fsl_sub."$fslsub" -Q "$QUEUE" \
     		${HCPPIPEDIR}/PostFreeSurfer/PostFreeSurferPipeline.sh \
      		--path="$StudyFolder" \
      		--subject="$Subject" \
      		--surfatlasdir="$SurfaceAtlasDIR" \
      		--grayordinatesdir="$GrayordinatesSpaceDIR" \
      		--grayordinatesres="$GrayordinatesResolution" \
      		--hiresmesh="$HighResMesh" \
      		--lowresmesh="$LowResMesh" \
      		--subcortgraylabels="$SubcorticalGrayLabels" \
      		--freesurferlabels="$FreeSurferLabels" \
      		--refmyelinmaps="$ReferenceMyelinMaps" \
      		--regname="$RegName" \
      		--printcom=$PRINTCOM
  		fi
  		
  		  # The following lines are used for interactive debugging to set the positional parameters: $1 $2 $3 ...
   			echo "set -- --path="$StudyFolder" \
      		--subject="$Subject" \
      		--surfatlasdir="$SurfaceAtlasDIR" \
      		--grayordinatesdir="$GrayordinatesSpaceDIR" \
      		--grayordinatesres="$GrayordinatesResolution" \
      		--hiresmesh="$HighResMesh" \
      		--lowresmesh="$LowResMesh" \
      		--subcortgraylabels="$SubcorticalGrayLabels" \
      		--freesurferlabels="$FreeSurferLabels" \
      		--refmyelinmaps="$ReferenceMyelinMaps" \
      		--regname="$RegName" \
      		--printcom=$PRINTCOM"

  		#echo ". ${EnvironmentScript}"
  		
}

show_usage_hcp3_orig() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Original implementation of the PostFreeSurfer (hcp3) code."
    			echo ""
    			echo "Note: This function is deprecated as of 01/2017. The maintained function is hcp3, called via gmri functions."
    			echo "		--> run ap ?hcp3 for up-to-date help call of the supported function"
    			echo ""
}


# ------------------------------------------------------------------------------------------------------
#  hcp4 - Executes the Volume BOLD Script
# ------------------------------------------------------------------------------------------------------

hcp4_orig() {
		
		#EnvironmentScript="$StudyFolder/../../../fcMRI/hcpsetup.sh" #Pipeline environment script
		cd "$StudyFolder"/../../../fcMRI/hcp.logs/

		# Requirements for this function
		#  installed versions of: FSL5.0.2 or higher , FreeSurfer (version 5.2 or higher) , gradunwarp (python code from MGH)
		#  environment: FSLDIR , FREESURFER_HOME , HCPPIPEDIR , CARET7DIR , PATH (for gradient_unwarp.py)

		#Set up pipeline environment variables and software
		#. ${EnvironmentScript}

		# Log the originating call
		echo "$@"

		########################################## INPUTS ########################################## 

		#Scripts called by this script do NOT assume anything about the form of the input names or paths.
		#This batch script assumes the HCP raw data naming convention, e.g. for ta5310_fncb_BOLD_1.nii.gz and ta5310_fncb_BOLD_1_SBRef.nii.gz:

		#	${StudyFolder}/${Subject}/hcp/${Subject}/BOLD_1_fncb/${Subject}_fncb_BOLD_1.nii.gz
		#	${StudyFolder}/${Subject}/hcp/${Subject}/BOLD_1_fncb/${Subject}_fncb_BOLD_1_SBRef.nii.gz

		#	${StudyFolder}/${Subject}/hcp/${Subject}/SpinEchoFieldMap1_fncb/${Subject}_fncb_BOLD_AP_SB_SE.nii.gz
		#	${StudyFolder}/${Subject}/hcp/${Subject}/SpinEchoFieldMap1_fncb/${Subject}_fncb_BOLD_PA_SB_SE.nii.gz

		#Change Scan Settings: Dwelltime, FieldMap Delta TE (if using), and $PhaseEncodinglist to match your images
		#These are set to match the HCP Protocol by default

		#If using gradient distortion correction, use the coefficents from your scanner
		#The HCP gradient distortion coefficents are only available through Siemens
		#Gradient distortion in standard scanners like the Trio is much less than for the HCP Skyra.

		#To get accurate EPI distortion correction with TOPUP, the flags in PhaseEncodinglist must match the phase encoding
		#direction of the EPI scan, and you must have used the correct images in SpinEchoPhaseEncodeNegative and Positive
		#variables.  If the distortion is twice as bad as in the original images, flip either the order of the spin echo
		#images or reverse the phase encoding list flag.  The pipeline expects you to have used the same phase encoding
		#axis in the fMRI data as in the spin echo field map data (x/-x or y/-y).  

		######################################### DO WORK ##########################################
		
		Subject="$CASE"
		#PhaseEncodinglist="y-" # this can be a list of directions across BOLDs
		PhaseEncodinglist="$PhaseEncodinglist" # this can be a list of directions across BOLDs

		i=1
		
  		for BOLD in $BOLDS ; do
  		
  			# clean up old runs to avoid errors 
  			rm -r "$StudyFolder"/"$Subject"/"$BOLD" &> /dev/null
  			rm -r "$StudyFolder"/"$Subject"/MNINonLinear/Results/"$BOLD" &> /dev/null
  		
    		fMRIName="$BOLD"
    		UnwarpDir=`echo $PhaseEncodinglist | cut -d " " -f $i`
    		fMRITimeSeries="${StudyFolder}/${Subject}/BOLD_${fMRIName}_fncb/${Subject}_fncb_BOLD_${fMRIName}.nii.gz"
    		fMRISBRef="${StudyFolder}/${Subject}/BOLD_${fMRIName}_SBRef_fncb/${Subject}_fncb_BOLD_${fMRIName}_SBRef.nii.gz" #A single band reference image (SBRef) is recommended if using multiband, set to NONE if you want to use the first volume of the timeseries for motion correction
    		DwellTime="0.00058" #Echo Spacing or Dwelltime of fMRI image -- #from ConnectomeDB #DICOM field (0019,1028) BandwidthPerPixelPhaseEncode & (0051,100b) AcquisitionMatrixText of which the first value is used (# phase encoding samples); the formula is 1/(BwPPPE * #PES) --> 1/(20.525*84) --> 0.00058
    		DistortionCorrection="TOPUP" #FIELDMAP or TOPUP, distortion correction is required for accurate processing
    
		    SpinEchoPhaseEncodeNegative="${StudyFolder}/${Subject}/SpinEchoFieldMap1_fncb/${Subject}_fncb_BOLD_AP_SB_SE.nii.gz" #For the spin echo field map volume with a negative phase encoding direction (LR in HCP data), set to NONE if using regular FIELDMAP
    		SpinEchoPhaseEncodePositive="${StudyFolder}/${Subject}/SpinEchoFieldMap1_fncb/${Subject}_fncb_BOLD_PA_SB_SE.nii.gz" #For the spin echo field map volume with a positive phase encoding direction (RL in HCP data), set to NONE if using regular FIELDMAP
   
    		MagnitudeInputName="NONE" #Expects 4D Magnitude volume with two 3D timepoints, set to NONE if using TOPUP
    		PhaseInputName="NONE" #Expects a 3D Phase volume, set to NONE if using TOPUP
    		DeltaTE="NONE" #2.46ms for 3T, 1.02ms for 7T, set to NONE if using TOPUP
    		FinalFMRIResolution="2" #Target final resolution of fMRI data. 2mm is recommended.  
  			GradientDistortionCoeffs="NONE" #Location of Coeffs file or "NONE" to skip
  			#GradientDistortionCoeffs="${HCPPIPEDIR_Config}/Trio_coeff.grad" #Location of Coeffs file or "NONE" to skip
  			#GradientDistortionCoeffs="${HCPPIPEDIR_Config}/coeff_SC72C_Skyra.grad" #Location of Coeffs file or "NONE" to skip
    		TopUpConfig="${HCPPIPEDIR_Config}/b02b0.cnf" #Topup config if using TOPUP, set to NONE if using regular FIELDMAP
    
  		if [ "$Cluster" == 1 ]; then
      		${HCPPIPEDIR}/fMRIVolume/GenericfMRIVolumeProcessingPipeline.sh \
      		--path="$StudyFolder" \
      		--subject="$Subject" \
      		--fmriname="$fMRIName" \
      		--fmritcs="$fMRITimeSeries" \
      		--fmriscout="$fMRISBRef" \
      		--SEPhaseNeg="$SpinEchoPhaseEncodeNegative" \
      		--SEPhasePos="$SpinEchoPhaseEncodePositive" \
      		--fmapmag="$MagnitudeInputName" \
      		--fmapphase="$PhaseInputName" \
      		--echospacing="$DwellTime" \
      		--echodiff="$DeltaTE" \
      		--unwarpdir="$UnwarpDir" \
      		--fmrires="$FinalFMRIResolution" \
      		--dcmethod="$DistortionCorrection" \
      		--gdcoeffs="$GradientDistortionCoeffs" \
      		--topupconfig="$TopUpConfig" \
      		--printcom="$PRINTCOM"
  		else 
  		    fsl_sub."$fslsub" -Q "$QUEUE" \
      		${HCPPIPEDIR}/fMRIVolume/GenericfMRIVolumeProcessingPipeline.sh \
      		--path="$StudyFolder" \
      		--subject="$Subject" \
      		--fmriname="$fMRIName" \
      		--fmritcs="$fMRITimeSeries" \
      		--fmriscout="$fMRISBRef" \
      		--SEPhaseNeg="$SpinEchoPhaseEncodeNegative" \
      		--SEPhasePos="$SpinEchoPhaseEncodePositive" \
      		--fmapmag="$MagnitudeInputName" \
      		--fmapphase="$PhaseInputName" \
      		--echospacing="$DwellTime" \
      		--echodiff="$DeltaTE" \
      		--unwarpdir="$UnwarpDir" \
      		--fmrires="$FinalFMRIResolution" \
      		--dcmethod="$DistortionCorrection" \
      		--gdcoeffs="$GradientDistortionCoeffs" \
      		--topupconfig="$TopUpConfig" \
      		--printcom="$PRINTCOM"

  		# The following lines are used for interactive debugging to set the positional parameters: $1 $2 $3 ...

  		echo "set -- --path=$StudyFolder \
      		--subject=$Subject \
      		--fmriname=$fMRIName \
      		--fmritcs=$fMRITimeSeries \
      		--fmriscout=$fMRISBRef \
      		--SEPhaseNeg=$SpinEchoPhaseEncodeNegative \
      		--SEPhasePos=$SpinEchoPhaseEncodePositive \
      		--fmapmag=$MagnitudeInputName \
      		--fmapphase=$PhaseInputName \
      		--echospacing=$DwellTime \
      		--echodiff=$DeltaTE \
      		--unwarpdir=$UnwarpDir \
      		--fmrires=$FinalFMRIResolution \
      		--dcmethod=$DistortionCorrection \
      		--gdcoeffs=$GradientDistortionCoeffs \
      		--topupconfig=$TopUpConfig \
      		--printcom=$PRINTCOM"

  		#echo ". ${EnvironmentScript}"
		
		fi
		
    		i=$(($i+1))
    		
  		done
		
}

show_usage_hcp4_orig() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Original implementation of the HCP Volume Preprocessing (hcp4) code."
    			echo ""
    			echo "Note: This function is deprecated as of 01/2017. The maintained function is hcp4, called via gmri functions."
    			echo "		--> run ap ?hcp4 for up-to-date help call of the supported function"
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  hcp5 - Executes the Surface BOLD Script
# ------------------------------------------------------------------------------------------------------

hcp5_orig() {

		#EnvironmentScript="$StudyFolder/../../../fcMRI/hcpsetup.sh" #Pipeline environment script
		mkdir "$StudyFolder"/../../../fcMRI/hcp.logs/ &> /dev/null 	
		cd "$StudyFolder"/../../../fcMRI/hcp.logs/

		# Requirements for this script
		#  installed versions of: FSL5.0.2 or higher , FreeSurfer (version 5.2 or higher) , gradunwarp (python code from MGH)
		#  environment: FSLDIR , FREESURFER_HOME , HCPPIPEDIR , CARET7DIR , PATH (for gradient_unwarp.py)

		#Set up pipeline environment variables and software
		#. ${EnvironmentScript}

		# Log the originating call
		echo "$@"

		########################################## INPUTS ########################################## 

		#Scripts called by this script do assume they run on the outputs of the FreeSurfer Pipeline

		######################################### DO WORK ##########################################

		Subject="$CASE"

  		for BOLD in $BOLDS ; do

    		LowResMesh="32" #Needs to match what is in PostFreeSurfer
    		FinalfMRIResolution="2" #Needs to match what is in fMRIVolume
    		SmoothingFWHM="2" #Recommended to be roughly the voxel size
    		GrayordinatesResolution="2" #Needs to match what is in PostFreeSurfer. Could be the same as FinalfRMIResolution something different, which will call a different module for subcortical processing
			fMRIName="$BOLD"
			RegName="FS" #MSMSulc is recommended, if binary is not available use FS (FreeSurfer)
		
		if [ "$Cluster" == 1 ]; then
			
      		${HCPPIPEDIR}/fMRISurface/GenericfMRISurfaceProcessingPipeline.sh \
      		--path="$StudyFolder" \
      		--subject="$Subject" \
      		--fmriname="$fMRIName" \
      		--lowresmesh="$LowResMesh" \
      		--fmrires="$FinalfMRIResolution" \
      		--smoothingFWHM="$SmoothingFWHM" \
      		--grayordinatesres="$GrayordinatesResolution" \
      		--regname="$RegName"
      	else
      		fsl_sub."$fslsub" -Q "$QUEUE" \
      		${HCPPIPEDIR}/fMRISurface/GenericfMRISurfaceProcessingPipeline.sh \
      		--path="$StudyFolder" \
      		--subject="$Subject" \
      		--fmriname="$fMRIName" \
      		--lowresmesh="$LowResMesh" \
      		--fmrires="$FinalfMRIResolution" \
      		--smoothingFWHM="$SmoothingFWHM" \
      		--grayordinatesres="$GrayordinatesResolution" \
      		--regname="$RegName"
      		
  			# The following lines are used for interactive debugging to set the positional parameters: $1 $2 $3 ...
      		echo "set -- --path=$StudyFolder \
      		--subject=$Subject \
      		--fmriname=$fMRIName \
      		--lowresmesh=$LowResMesh \
      		--fmrires=$FinalfMRIResolution \
      		--smoothingFWHM=$SmoothingFWHM \
      		--grayordinatesres=$GrayordinatesResolution \
      		--regname=$RegName"

      		#echo ". ${EnvironmentScript}"
      	fi	
            
		done
}

show_usage_hcp5_orig() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Original implementation of the HCP Surface Preprocessing (hcp5) code."
    			echo ""
    			echo "Note: This function is deprecated as of 01/2017. The maintained function is hcp5, called via gmri functions."
    			echo "		--> run ap ?hcp5 for up-to-date help call of the supported function"
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  hcpd - Executes the Diffusion Processing HCP Script using TOPUP implementation
# ------------------------------------------------------------------------------------------------------

hcpd_orig() {

		#EnvironmentScript="$StudyFolder/../../../fcMRI/hcpsetup.sh" #Pipeline environment script
		cd "$StudyFolder"/../../../fcMRI/hcp.logs/

		# Requirements for this script
		#  installed versions of: FSL5.0.2 or higher , FreeSurfer (version 5.2 or higher) , gradunwarp (python code from MGH)
		#  environment: FSLDIR , FREESURFER_HOME , HCPPIPEDIR , CARET7DIR , PATH (for gradient_unwarp.py)

		#Set up pipeline environment variables and software
		#. ${EnvironmentScript}

		# Log the originating call
		echo "$@"

		PRINTCOM=""

		########################################## INPUTS ########################################## 

		#Scripts called by this script do assume they run on the outputs of the PreFreeSurfer Pipeline

		#Change Scan Settings: FieldMap Delta TE, Sample Spacings, and $UnwarpDir to match your images
		
		#If using gradient distortion correction, use the coefficents from your scanner
		
		#The HCP gradient distortion coefficents are only available through Siemens
		
		#Gradient distortion in standard scanners like the Trio is much less than for the HCP Skyra.

		######################################### DO WORK ##########################################

		#Acquisition Parameters
		EchoSpacing="$EchoSpacing" #EPI Echo Spacing for data (in msec); e.g. 0.69
		PEdir="$PEdir" #Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior
		Gdcoeffs="NONE"
		Directions="$Directions"    
		BVal="$BVal"
		#Gdcoeffs="/vols/Data/HCP/Pipelines/global/config/coeff_SC72C_Skyra.grad" #Coefficients that describe spatial variations of the scanner gradients. Use NONE if not available.

		if [ "$PEdir" == 1 ]; then
			PEdirPos="RL"
			PEdirNeg="LR"
		else
			PEdirPos="AP"
			PEdirNeg="PA"
		fi

		#Input Variables
		Subject="$CASE"
  		SubjectID="$Subject" #Subject ID Name
  		
  		#RawDataDir="$StudyFolder/$SubjectID/Diffusion" #Folder where unprocessed diffusion data are
  		#PosData="${RawDataDir}/RL_data1@${RawDataDir}/RL_data2@${RawDataDir}/RL_data3" #Data with positive Phase encoding direction. Up to N>=1 series (here N=2), separated by @
  		#NegData="${RawDataDir}/LR_data1@${RawDataDir}/LR_data2@${RawDataDir}/LR_data3" #Data with negative Phase encoding direction. Up to N>=1 series (here N=2), separated by @
                                                                                 #If corresponding series is missing [e.g. 2 RL series and 1 LR) use EMPTY.
		
		PosData=`echo "${StudyFolder}/${Subject}/Diffusion/${Subject}_DWI_dir${Directions}_${PEdirPos}.nii.gz@${StudyFolder}/${Subject}/Diffusion/${Subject}_DWI_dir${Directions}_${PEdirPos}.nii.gz"` # "$1" #dataRL1@dataRL2@...dataRLN
  		NegData=`echo "${StudyFolder}/${Subject}/Diffusion/${Subject}_DWI_dir${Directions}_${PEdirNeg}.nii.gz@${StudyFolder}/${Subject}/Diffusion/${Subject}_DWI_dir${Directions}_${PEdirNeg}.nii.gz"` # "$2" #dataLR1@dataLR2@...dataLRN
   		
		if [ "$Cluster" == 1 ]; then
		
		${HCPPIPEDIR}/DiffusionPreprocessing/DiffPreprocPipeline.sh \
      	--posData="${PosData}" \
      	--negData="${NegData}" \
      	--path="${StudyFolder}" \
      	--subject="${SubjectID}" \
      	--echospacing="${EchoSpacing}" \
      	--PEdir="${PEdir}" \
      	--gdcoeffs="${Gdcoeffs}" \
      	--printcom="$PRINTCOM"
		
      	else
      	
      	fsl_sub."$fslsub" -T 3000 -Q "$QUEUE" \
		${HCPPIPEDIR}/DiffusionPreprocessing/DiffPreprocPipeline.sh \
      	--posData="${PosData}" \
      	--negData="${NegData}" \
      	--path="${StudyFolder}" \
      	--subject="${SubjectID}" \
      	--echospacing="${EchoSpacing}" \
      	--PEdir="${PEdir}" \
      	--gdcoeffs="${Gdcoeffs}" \
      	--printcom="$PRINTCOM"
      	
      	echo "set -- --posData=$PosData \
      		--negData=$NegData \
      		--path=$StudyFolder \
      		--subject=$SubjectID \
      		--echospacing=$EchoSpacing \
      		--PEdir=$PEdir \
      		--gdcoeffs=$Gdcoeffs \
      		--printcom=$PRINTCOM"
      	fi	
      	
}

show_usage_hcpd_orig() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Original implementation of the HCP Diffusion Preprocessing (hcpd) code."
    			echo ""
    			echo "Note: This function is deprecated as of 01/2017. The maintained function is hcpd, called via gmri functions."
    			echo "		--> run ap ?hcpd for up-to-date help call of the supported function"
    			echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  hcpdlegacy - Executes the Diffusion Processing Script via FUGUE implementation for legacy data - (needed for legacy DWI data that is non-HCP compliant without counterbalanced phase encoding directions needed for topup)
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

hcpdlegacy() {

		# Requirements for this function
		# installed versions of: FSL5.0.9 or higher
		# environment: FSLDIR
		# Needs CUDA 6.0 libraries to run eddy_cuda (10x faster than on a CPU)
		
		########################################## INPUTS ########################################## 

		# DWI Data and T1w data needed in HCP-style format to perform legacy DWI preprocessing
		# The data should be in $DiffFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/Diffusion
		# Also assumes that hcp1 (PreFreeSurfeer) T1 preprocessing has been carried out with results in "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w
		# Mandatory input parameters:
    		# StudyFolder
    		# Subject
    		# PEdir
    		# EchoSpacing
    		# TE
    		# UnwarpDir
    		# DiffDataSuffix
    	# Additional parameters that AP demands:	
    		# QUEUE
    		# Cluster
    		# Scheduler
		
		########################################## OUTPUTS #########################################
		
		# DiffFolder=${StudyFolder}/${Subject}/Diffusion
		# T1wDiffFolder=${StudyFolder}/${Subject}/T1w/Diffusion
		#    $DiffFolder/rawdata
		#    $DiffFolder/topup    
		#    $DiffFolder/eddy
		#    $DiffFolder/data
		#    $DiffFolder/reg
		#    $DiffFolder/logs
		#    $T1wDiffFolder
		
		# Parse all Parameters
		EchoSpacing="$EchoSpacing" #EPI Echo Spacing for data (in msec); e.g. 0.69
		PEdir="$PEdir" #Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior
		TE="$TE" #delta TE in ms for field map or "NONE" if not used
		UnwarpDir="$UnwarpDir" # direction along which to unwarp
		DiffData="$DiffDataSuffix" # Diffusion data suffix name - e.g. if the data is called <SubjectID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR
		CUDAQUEUE="$QUEUE" # Cluster queue name with GPU nodes - e.g. anticevic-gpu
		DwellTime="$EchoSpacing" #same variable as EchoSpacing - if you have in-plane acceleration then this value needs to be divided by the GRAPPA or SENSE factor (miliseconds)
		DwellTimeSec=`echo "scale=6; $DwellTime/1000" | bc` # set the dwell time to seconds:

		# Establish global directory paths
		T1wFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w
		DiffFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/Diffusion
		T1wDiffFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion
		FieldMapFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/FieldMap_strc
		LogFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/Diffusion/log
		Overwrite="$Overwrite"
		
		if [ "$Cluster" == 1 ]; then
		
		echo "Running locally on `hostname`"
		echo "Check log file output here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""
				
		${HCPPIPEDIR}/DiffusionPreprocessingLegacy/DiffPreprocPipelineLegacy.sh \
		--path="${StudyFolder}" \
		--subject="${CASE}" \
		--PEdir="${PEdir}" \
		--echospacing="${EchoSpacing}" \
		--TE="${TE}" \
		--unwarpdir="${UnwarpDir}" \
		--overwrite="${Overwrite}" \
		--diffdatasuffix="${DiffDataSuffix}" >> "$LogFolder"/DiffPreprocPipelineLegacy_"$CASE"_`date +%Y-%m-%d-%H-%M-%S`.log
				
		# Print log on screen
		#LogFile=`ls -ltr $LogFolder/DiffPreprocPipelineLegacy_$CASE_*log | tail -n 1 | awk '{ print $9 }'`
		#echo ""
		#echo "Log file location:"
		#echo "$LogFolder/$LogFile"
		#echo ""
		#echo `tail -f $LogFolder/$LogFile`
		
		else
		
		# set scheduler for fsl_sub command
		fslsub="$Scheduler"
		
		fsl_sub."$fslsub" -Q "$CUDAQUEUE" -l "$LogFolder" ${HCPPIPEDIR}/DiffusionPreprocessingLegacy/DiffPreprocPipelineLegacy.sh \
		--path="${StudyFolder}" \
		--subject="${CASE}" \
		--PEdir="${PEdir}" \
		--echospacing="${EchoSpacing}" \
		--TE="${TE}" \
		--unwarpdir="${UnwarpDir}" \
		--diffdatasuffix="${DiffDataSuffix}" \
		--overwrite="${Overwrite}"

		echo "--------------------------------------------------------------"
		echo "Data successfully submitted to $QUEUE" 
		echo "Check output logs here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""
		fi
}

show_usage_hcpdlegacy() {
				
				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function runs the DWI preprocessing using the FUGUE method for legacy data that are not TOPUP compatible"
				echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing: "
				echo ""
				echo " <study_folder>/<case>/hcp/<case>/Diffusion ---> DWI data needs to be here"
				echo " <study_folder>/<case>/hcp/<case>/T1w       ---> T1w data needs to be here"
				echo ""
				echo "	Note: "
				echo " 		- If PreFreeSurfer component of the HCP Pipelines was run the function will make use of the T1w data [Results will be better due to superior brain stripping]."
				echo " 		- If PreFreeSurfer component of the HCP Pipelines was NOT run the function will start from raw T1w data [Results may be less optimal]."
				echo "		- If you are this function interactively you need to be on a GPU-enabled node or send it to a GPU-enabled queue."
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>			Name of function"
				echo "		--path=<study_folder>				Path to study data folder"
				echo "		--subjects=<comma_separated_list_of_cases>			List of subjects to run"
				echo "		--echospacing=<echo_spacing_value>		EPI Echo Spacing for data [in msec]; e.g. 0.69"
				echo "		--PEdir=<phase_encoding_direction>		Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior"
				echo "		--TE=<delta_te_value_for_fieldmap>		This is the echo time difference of the fieldmap sequence - find this out form the operator - defaults are *usually* 2.46ms on SIEMENS"
				echo "		--unwarpdir=<epi_phase_unwarping_direction>	Direction for EPI image unwarping; e.g. x or x- for LR/RL, y or y- for AP/PA; may been to try out both -/+ combinations"
				echo "		--diffdatasuffix=<diffusion_data_name>		Name of the DWI image; e.g. if the data is called <SubjectID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR"
				echo "		--queue=<name_of_cluster_queue>			Cluster queue name"
				echo "		--scheduler=<name_of_cluster_scheduler>		Cluster scheduler program: e.g. LSF or PBS"
				echo "		--runmethod=<type_of_run>			Perform Local Interactive Run [1] or Send to scheduler [2] [If local/interactive then log will be continuously generated in different format]"
				echo "" 
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
 				echo "		--overwrite=<clean_prior_run>		Delete prior run for a given subject"
				echo ""
				echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Anticevic.DP5/subjects' --subjects='ta6455' --function='hcpdlegacy' --PEdir='1' --echospacing='0.69' --TE='2.46' --unwarpdir='x-' --diffdatasuffix='DWI_dir91_LR' --queue='anticevic-gpu' --runmethod='1' --overwrite='yes'"
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Anticevic.DP5/subjects' --subjects='ta6455' --function='hcpdlegacy' --PEdir='1' --echospacing='0.69' --TE='2.46' --unwarpdir='x-' --diffdatasuffix='DWI_dir91_LR' --queue='anticevic-gpu' --runmethod='2' --scheduler='lsf' --overwrite='yes'"
				echo ""				
				echo "-- Example with interactive terminal:"
				echo ""
				echo "AP hcpdlegacy /gpfs/project/fas/n3/Studies/Anticevic.DP5/subjects 'ta6455' "
				echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  dwidenseparcellation - Executes the Diffusion Parcellation Script (DWIDenseParcellation.sh) via the AP wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

dwidenseparcellation() {

		# Requirements for this function
		# Connectome Workbench (v1.0 or above)
		
		########################################## INPUTS ########################################## 

		# DWI Data and T1w data needed in HCP-style format and dense DWI probtrackX should be completed
		# The data should be in $DiffFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/Tractography
		# Mandatory input parameters:
    	# StudyFolder # e.g. /gpfs/project/fas/n3/Studies/Connectome
    	# Subject	  # e.g. 100307
    	# MatrixVersion # e.g. 1 or 3
    	# ParcellationFile  # e.g. {$TOOLS}/MNAP/general/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii"

		########################################## OUTPUTS #########################################

		# Outputs will be *pconn.nii files located here:
		#    DWIOutput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"

		
		# Parse General Parameters
		QUEUE="$QUEUE" # Cluster queue name with GPU nodes - e.g. anticevic-gpu
		StudyFolder="$StudyFolder"
		CASE="$CASE"
		MatrixVersion="$MatrixVersion"
		ParcellationFile="$ParcellationFile"
		OutName="$OutName"
		DWIOutput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"
		mkdir "$DWIOutput"/log > /dev/null 2>&1
		LogFolder="$DWIOutput"/log
		Overwrite="$Overwrite"
		
		if [ "$Cluster" == 1 ]; then
		
		echo "Running locally on `hostname`"
		echo "Check log file output here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""
				
		DWIDenseParcellation.sh \
		--path="${StudyFolder}" \
		--subject="${CASE}" \
		--matrixversion="${MatrixVersion}" \
		--parcellationfile="${ParcellationFile}" \
		--outname="${OutName}" \
		--overwrite="${Overwrite}" >> "$LogFolder"/DWIDenseParcellation_"$CASE"_`date +%Y-%m-%d-%H-%M-%S`.log
		
		else
		
		# set scheduler for fsl_sub command
		fslsub="$Scheduler"
		
		fsl_sub."$fslsub" -Q "$QUEUE" -l "$LogFolder" DWIDenseParcellation.sh \
		--path="${StudyFolder}" \
		--subject="${CASE}" \
		--matrixversion="${MatrixVersion}" \
		--parcellationfile="${ParcellationFile}" \
		--outname="${OutName}" \
		--overwrite="${Overwrite}"

		echo "--------------------------------------------------------------"
		echo "Data successfully submitted to $QUEUE" 
		echo "Check output logs here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""
		fi
}

show_usage_dwidenseparcellation() {

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
				echo "		--function=<function_name>			Name of function"
				echo "		--path=<study_folder>				Path to study data folder"
				echo "		--subject=<comma_separated_list_of_cases>	List of subjects to run"
				echo "		--matrixversion=<matrix_version_value>		matrix solution verion to run parcellation on; e.g. 1 or 3"
				echo "		--parcellationfile=<file_for_parcellation>	Specify the absolute path of the file you want to use for parcellation"
				echo "		--outname=<name_of_output_pconn_file>		Specify the suffix output name of the pconn file"
				echo "		--queue=<name_of_cluster_queue>			Cluster queue name"
				echo "		--scheduler=<name_of_cluster_scheduler>		Cluster scheduler program: e.g. LSF or PBS"
				echo "		--runmethod=<type_of_run>			Perform Local Interactive Run [1] or Send to scheduler [2] [If local/interactive then log will be continuously generated in different format]"
				echo "" 
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
 				echo "		--overwrite=<clean_prior_run>		Delete prior run for a given subject"
 				echo ""
				echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--function='dwidenseparcellation' \ "
				echo "--subjects='100206' \ "
				echo "--matrixversion='3' \ "
				echo "--parcellationfile='{$TOOLS}/MNAP/general/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
				echo "--runmethod='1'"
				echo ""	
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--function='dwidenseparcellation' \ "
				echo "--subjects='100206' \ "
				echo "--matrixversion='3' \ "
				echo "--parcellationfile='{$TOOLS}/MNAP/general/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
				echo "--queue='anticevic' \ "
				echo "--runmethod='2' \ "
				echo "--scheduler='lsf'"
				echo ""
				echo "-- Example with interactive terminal:"
				echo ""
				echo "AP dwidenseparcellation /gpfs/project/fas/n3/Studies/Connectome/subjects '100206' "
				echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  dwiseedtractography - Executes the Diffusion Seed Tractography Script (DWIDenseSeedTractography.sh) via the AP wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

dwiseedtractography() {

		# Requirements for this function
		# Connectome Workbench (v1.0 or above)
		
		########################################## INPUTS ########################################## 

		# The data should be in $DiffFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/Tractography
		# Mandatory input parameters:
    	# StudyFolder # e.g. /gpfs/project/fas/n3/Studies/Connectome
    	# Subject	  # e.g. 100307
    	# MatrixVersion # e.g. 1 or 3
    	# SeedFile  # e.g. <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz"

		########################################## OUTPUTS #########################################

		# Outputs will be *pconn.nii files located here:
		#    DWIOutput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"

		
		# Parse General Parameters
		QUEUE="$QUEUE" # Cluster queue name with GPU nodes - e.g. anticevic-gpu
		StudyFolder="$StudyFolder"
		CASE="$CASE"
		MatrixVersion="$MatrixVersion"
		SeedFile="$SeedFile"
		OutName="$OutName"
		DWIOutput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"
		mkdir "$DWIOutput"/log > /dev/null 2>&1
		LogFolder="$DWIOutput"/log
		Overwrite="$Overwrite"
		
		if [ "$Cluster" == 1 ]; then
		
		echo "Running locally on `hostname`"
		echo "Check log file output here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""
				
		DWIDenseSeedTractography.sh \
		--path="${StudyFolder}" \
		--subject="${CASE}" \
		--matrixversion="${MatrixVersion}" \
		--seedfile="${SeedFile}" \
		--outname="${OutName}" \
		--overwrite="${Overwrite}" >> "$LogFolder"/DWIDenseParcellation_"$CASE"_`date +%Y-%m-%d-%H-%M-%S`.log
		
		else
		
		# set scheduler for fsl_sub command
		fslsub="$Scheduler"
		
		fsl_sub."$fslsub" -Q "$QUEUE" -l "$LogFolder" DWIDenseSeedTractography.sh \
		--path="${StudyFolder}" \
		--subject="${CASE}" \
		--matrixversion="${MatrixVersion}" \
		--seedfile="${SeedFile}" \
		--outname="${OutName}" \
		--overwrite="${Overwrite}"

		echo "--------------------------------------------------------------"
		echo "Data successfully submitted to $QUEUE" 
		echo "Check output logs here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""
		fi
}

show_usage_dwiseedtractography() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function implements reduction on the DWI dense connectomes using a given 'seed' structure (e.g. thalamus)."
				echo "It explicitly assumes the the Human Connectome Project folder structure for preprocessing: "
				echo ""
				echo " <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/ ---> Dense Connectome DWI data needs to be here"
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
				echo "		--function=<function_name>			Name of function"
				echo "		--path=<study_folder>				Path to study data folder"
				echo "		--subject=<comma_separated_list_of_cases>	List of subjects to run"
				echo "		--matrixversion=<matrix_version_value>		matrix solution verion to run parcellation on; e.g. 1 or 3"
				echo "		--seedfile=<file_for_seed_reduction>		Specify the absolute path of the seed file you want to use as a seed for dconn reduction"
				echo "		--outname=<name_of_output_dscalar_file>		Specify the suffix output name of the dscalar file"
				echo "		--queue=<name_of_cluster_queue>			Cluster queue name"
				echo "		--scheduler=<name_of_cluster_scheduler>		Cluster scheduler program: e.g. LSF or PBS"
				echo "		--runmethod=<type_of_run>			Perform Local Interactive Run [1] or Send to scheduler [2] [If local/interactive then log will be continuously generated in different format]"
				echo "" 
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
 				echo "		--overwrite=<clean_prior_run>		Delete prior run for a given subject"
 				echo ""
				echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--function='dwiseedtractography' \ "
				echo "--subjects='100206' \ "
				echo "--matrixversion='3' \ "
				echo "--seedfile='<study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz' \ "
				echo "--overwrite='no' \ "
				echo "--outname='Thalamus_Seed' \ "
				echo "--runmethod='1'"
				echo ""	
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--function='dwiseedtractography' \ "
				echo "--subjects='100206' \ "
				echo "--matrixversion='3' \ "
				echo "--seedfile='<study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz' \ "
				echo "--overwrite='no' \ "
				echo "--outname='Thalamus_Seed' \ "
				echo "--queue='anticevic' \ "
				echo "--runmethod='2' \ "
				echo "--scheduler='lsf'"
				echo ""
				echo "-- Example with interactive terminal:"
				echo ""
				echo "Interactive terminal run method not supported for this function"
				echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  structuralparcellation - Executes the Structural Parcellation Script (StructuralParcellation.sh) via the AP wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

structuralparcellation() {

		# Requirements for this function
		# Connectome Workbench (v1.0 or above)
		
		########################################## INPUTS ########################################## 

		# Data should be pre-processed and in CIFTI format
		# The data should be in the folder relative to the master study folder, specified by the inputfile
		# Mandatory input parameters:
   	 	# StudyFolder # e.g. /gpfs/project/fas/n3/Studies/Connectome
    	# Subject	  # e.g. 100206
    	# InputDataType # e.g. myelin
    	# OutName # e.g. LR_Colelab_partitions
    	# ExtractData # yes/no
    	# ParcellationFile  # e.g. /gpfs/project/fas/n3/software/MNAP/general/templates/Parcellations/Cole_GlasserNetworkAssignment_Final/final_LR_FIXICA_noGSR_reassigned.dlabel.nii"

		########################################## OUTPUTS #########################################

		# Outputs will be *pconn.nii files located in the location specified in the outputpath
		
		# Parse General Parameters
		QUEUE="$QUEUE" # Cluster queue name with GPU nodes - e.g. anticevic-gpu
		StudyFolder="$StudyFolder"
		CASE="$CASE"
		InputDataType="$InputDataType"
		OutName="$OutName"
		ParcellationFile="$ParcellationFile"
		ExtractData="$ExtractData"
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/structuralparcellation_log > /dev/null 2>&1
		LogFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/structuralparcellation_log
		Overwrite="$Overwrite"
		
		if [ "$Cluster" == 1 ]; then
		
		echo "Running locally on `hostname`"
		echo "Check log file output here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""
				
		${TOOLS}/MNAP/general/functions/StructuralParcellation.sh \
		--path="${StudyFolder}" \
		--subject="${CASE}" \
		--inputdatatype="${InputDataType}" \
		--parcellationfile="${ParcellationFile}" \
		--overwrite="${Overwrite}" \
		--outname="${OutName}" \
		--extractdata="${ExtractData}" >> "$LogFolder"/StructuralParcellation_"$CASE"_`date +%Y-%m-%d-%H-%M-%S`.log
		
		else
		
		# set scheduler for fsl_sub command
		fslsub="$Scheduler"
		
		fsl_sub."$fslsub" -Q "$QUEUE" -l "$LogFolder" ${TOOLS}/MNAP/general/functions/StructuralParcellation.sh \
		--path="${StudyFolder}" \
		--subject="${CASE}" \
		--inputdatatype="${InputDataType}" \
		--parcellationfile="${ParcellationFile}" \
		--overwrite="${Overwrite}" \
		--outname="${OutName}" \
		--extractdata="${ExtractData}"
		
		echo "--------------------------------------------------------------"
		echo "Data successfully submitted to $QUEUE" 
		echo "Check output logs here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""
		fi
}

show_usage_structuralparcellation() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function implements parcellation on the dense cortical thickness OR myelin files using a whole-brain parcellation (e.g. Glasser parcellation with subcortical labels included)."
				echo ""
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>				Name of function"
 				echo "		--path=<study_folder>					Path to study data folder"
				echo "		--subject=<comma_separated_list_of_cases>				List of subjects to run"
				echo "		--inputdatatype=<type_of_dense_data_for_input_file>	Specify the type of data for the input file (e.g. MyelinMap_BC or corrThickness)"
				echo "		--parcellationfile=<file_for_parcellation>		Specify path of the file you want to use for parcellation relative to the master study folder (e.g. /images/functional/bold1_Atlas_MSMAll_hp2000_clean.dtseries.nii)"
				echo "		--outname=<name_of_output_pconn_file>			Specify the suffix output name of the pconn file"
				echo "		--queue=<name_of_cluster_queue>				Cluster queue name"
				echo "		--scheduler=<name_of_cluster_scheduler>			Cluster scheduler program: e.g. LSF or PBS"
				echo "		--runmethod=<type_of_run>				Perform Local Interactive Run [1] or Send to scheduler [2] [If local/interactive then log will be continuously generated in different format]"
				echo "" 
				echo ""
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
 				echo "		--overwrite=<clean_prior_run>						Delete prior run for a given subject"
 				echo "		--extractdata=<save_out_the_data_as_as_csv>				Specify if you want to save out the matrix as a CSV file"
 				echo ""
				echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--function='structuralparcellation' \ "
				echo "--subjects='100206' \ "
				echo "--inputdatatype='MyelinMap_BC' \ "
				echo "--parcellationfile='{$TOOLS}/MNAP/general/templates/Parcellations/Cole_GlasserNetworkAssignment_Final/final_LR_FIXICA_noGSR_reassigned.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions' \ "
				echo "--extractdata='yes' "
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--function='structuralparcellation' \ "
				echo "--subjects='100206' \ "
				echo "--inputdatatype='MyelinMap_BC' \ "
				echo "--parcellationfile='$TOOLS/MNAP/general/templates/Parcellations/Cole_GlasserNetworkAssignment_Final/final_LR_FIXICA_noGSR_reassigned.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions' \ "
				echo "--extractdata='yes' "
				echo "--queue='anticevic' \ "
				echo "--runmethod='2' \ "
				echo "--scheduler='lsf' "
				echo "" 
 				echo ""
				echo "-- Example with interactive terminal:"
				echo ""
				echo "AP structuralparcellation /gpfs/project/fas/n3/Studies/Connectome/subjects '100206' "
				echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  boldparcellation - Executes the BOLD Parcellation Script (BOLDParcellation.sh) via the AP wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

boldparcellation() {

		# Requirements for this function
		# Connectome Workbench (v1.0 or above)
		
		########################################## INPUTS ########################################## 

		# BOLD data should be pre-processed and in CIFTI format
		# The data should be in the folder relative to the master study folder, specified by the inputfile
		# Mandatory input parameters:
		# StudyFolder # e.g. /gpfs/project/fas/n3/Studies/Connectome
		# Subject	  # e.g. 100206
		# InputFile # e.g. bold1_Atlas_MSMAll_hp2000_clean.dtseries.nii
		# InputPath # e.g. /images/functional/
		# InputDataType # e.g.dtseries
		# OutPath # e.g. /images/functional/
		# OutName # e.g. LR_Colelab_partitions_v1d_islands_withsubcortex
		# ParcellationFile  # e.g. {$TOOLS}/MNAP/general/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii"
		# ComputePConn # Specify if a parcellated connectivity file should be computed (pconn). This is done using covariance and correlation (e.g. yes; default is set to no).
		# UseWeights  # If computing a  parcellated connectivity file you can specify which frames to omit (e.g. yes' or no; default is set to no) 
		# WeightsFile # Specify the location of the weights file relative to the master study folder (e.g. /images/functional/movement/bold1.use)
		# ExtractData # yes/no
		
		########################################## OUTPUTS #########################################

		# Outputs will be files located in the location specified in the outputpath
		
		# Parse General Parameters
		QUEUE="$QUEUE" # Cluster queue name with GPU nodes - e.g. anticevic-gpu
		StudyFolder="$StudyFolder"
		CASE="$CASE"
		InputFile="$InputFile"
		InputPath="$InputPath"
		InputDataType="$InputDataType"
		OutPath="$OutPath"
		OutName="$OutName"
		ComputePConn="$ComputePConn"
		UseWeights="$UseWeights"
		WeightsFile="$WeightsFile"
		ParcellationFile="$ParcellationFile"
		BOLDOutput="$StudyFolder/$CASE$OutPath"
		ExtractData="$ExtractData"
		mkdir "$BOLDOutput"/boldparcellation_log > /dev/null 2>&1
		LogFolder="$BOLDOutput"boldparcellation_log
		Overwrite="$Overwrite"
		
		if [ "$Cluster" == 1 ]; then
		
		echo "Running locally on `hostname`"
		echo "Check log file output here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""
				
		BOLDParcellation.sh \
		--path="${StudyFolder}" \
		--subject="${CASE}" \
		--inputfile="${InputFile}" \
		--inputpath="${InputPath}" \
		--inputdatatype="${InputDataType}" \
		--parcellationfile="${ParcellationFile}" \
		--overwrite="${Overwrite}" \
		--outname="${OutName}" \
		--outpath="${OutPath}" \
		--computepconn="${ComputePConn}" \
		--extractdata="${ExtractData}" \
		--useweights="${UseWeights}" \
		--weightsfile="${WeightsFile}" >> "$LogFolder"/BOLDParcellation_"$CASE"_`date +%Y-%m-%d-%H-%M-%S`.log
		
		else
		
		# set scheduler for fsl_sub command
		fslsub="$Scheduler"
		
		fsl_sub."$fslsub" -Q "$QUEUE" -l "$LogFolder" BOLDParcellation.sh \
		--path="${StudyFolder}" \
		--subject="${CASE}" \
		--inputfile="${InputFile}" \
		--inputpath="${InputPath}" \
		--inputdatatype="${InputDataType}" \
		--parcellationfile="${ParcellationFile}" \
		--overwrite="${Overwrite}" \
		--outname="${OutName}" \
		--outpath="${OutPath}" \
		--computepconn="${ComputePConn}" \
		--extractdata="${ExtractData}" \
		--useweights="${UseWeights}" \
		--weightsfile="${WeightsFile}"
		
		echo "--------------------------------------------------------------"
		echo "Data successfully submitted to $QUEUE" 
		echo "Check output logs here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""
		fi
}

show_usage_boldparcellation() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function implements parcellation on the BOLD dense files using a whole-brain parcellation (e.g.Glasser parcellation with subcortical labels included)."
				echo ""
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>				Name of function"
 				echo "		--path=<study_folder>					Path to study data folder"
				echo "		--subject=<comma_separated_list_of_cases>				List of subjects to run"
				echo "		--inputfile=<file_to_compute_parcellation_on>		Specify the name of the file you want to use for parcellation (e.g. bold1_Atlas_MSMAll_hp2000_clean)"
				echo "		--inputpath=<path_for_input_file>			Specify path of the file you want to use for parcellation relative to the master study folder and subject directory (e.g. /images/functional/)"
				echo "		--inputdatatype=<type_of_dense_data_for_input_file>	Specify the type of data for the input file (e.g. dscalar or dtseries)"
				echo "		--parcellationfile=<file_for_parcellation>		Specify path of the file you want to use for parcellation relative to the master study folder (e.g. /images/functional/bold1_Atlas_MSMAll_hp2000_clean.dtseries.nii)"
				echo "		--outname=<name_of_output_pconn_file>			Specify the suffix output name of the pconn file"
				echo "		--outpath=<path_for_output_file>			Specify the output path name of the pconn file relative to the master study folder (e.g. /images/functional/)"
				echo "		--queue=<name_of_cluster_queue>				Cluster queue name"
				echo "		--scheduler=<name_of_cluster_scheduler>			Cluster scheduler program: e.g. LSF or PBS"
				echo "		--runmethod=<type_of_run>				Perform Local Interactive Run [1] or Send to scheduler [2] [If local/interactive then log will be continuously generated in different format]"
				echo "" 
				echo ""
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
 				echo "		--overwrite=<clean_prior_run>						Delete prior run for a given subject"
 				echo "		--computepconn=<specify_parcellated_connectivity_calculation>		Specify if a parcellated connectivity file should be computed (pconn). This is done using covariance and correlation (e.g. yes; default is set to no)."
 				echo "		--useweights=<clean_prior_run>						If computing a  parcellated connectivity file you can specify which frames to omit (e.g. yes' or no; default is set to no) "
 				echo "		--weightsfile=<location_and_name_of_weights_file>			Specify the location of the weights file relative to the master study folder (e.g. /images/functional/movement/bold1.use)"
 				echo "		--extractdata=<save_out_the_data_as_as_csv>				Specify if you want to save out the matrix as a CSV file"
 				echo ""
				echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--function='boldparcellation' \ "
				echo "--subjects='100206' \ "
				echo "--inputfile='bold1_Atlas_MSMAll_hp2000_clean' \ "
				echo "--inputpath='/images/functional/' \ "
				echo "--inputdatatype='dtseries' \ "
				echo "--parcellationfile='{$TOOLS}/MNAP/general/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
				echo "--outpath='/images/functional/' \ "
				echo "--computepconn='yes' \ "
				echo "--extractdata='yes' \ "
				echo "--useweights='no' \ "
				echo "--runmethod='1' "
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--function='boldparcellation' \ "
				echo "--subjects='100206' \ "
				echo "--inputfile='bold1_Atlas_MSMAll_hp2000_clean' \ "
				echo "--inputpath='/images/functional/' \ "
				echo "--inputdatatype='dtseries' \ "
				echo "--parcellationfile='$TOOLS/MNAP/general/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
				echo "--outpath='/images/functional/' \ "
				echo "--computepconn='yes' \ "
				echo "--extractdata='yes' \ "
				echo "--useweights='no' \ "
				echo "--queue='anticevic' \ "
				echo "--runmethod='2' \ "
				echo "--scheduler='lsf' "
				echo "" 
 				echo ""
				echo "-- Example with interactive terminal:"
				echo ""
				echo "AP boldparcellation /gpfs/project/fas/n3/Studies/Connectome/subjects '100206' "
				echo ""
}


# ------------------------------------------------------------------------------------------------------
#  fsldtifit - Executes the dtifit script from FSL (needed for probabilistic tractography)
# ------------------------------------------------------------------------------------------------------

fsldtifit() {
	
	mkdir "$StudyFolder"/../fcMRI/hcp.logs/ > /dev/null 2>&1
	cd "$StudyFolder"/../fcMRI/hcp.logs/
	
			# Check if overwrite flag was set
	if [ "$Overwrite" == "yes" ]; then
		echo ""
		reho "Removing existing dtifit run for $CASE..."
		echo ""
		rm -rf "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/dti_* > /dev/null 2>&1
	fi
	
	minimumfilesize=100000
  	
  	if [ -a "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/dti_FA.nii.gz ]; then 
  		actualfilesize=$(wc -c <"$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/dti_FA.nii.gz)
  	else
  		actualfilesize="0"
  	fi
  	
  	if [ $(echo "$actualfilesize" | bc) -gt $(echo "$minimumfilesize" | bc) ]; then
  		echo ""
  		echo "--- DTI Fit completed for $CASE ---"
  		echo ""
  	else
  	
	if [ "$Cluster" == 1 ]; then
 		dtifit --data="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./data --out="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./dti --mask="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./nodif_brain_mask --bvecs="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./bvecs --bvals="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./bvals
	else
 		fslsub="$Scheduler"
 		fsl_sub."$fslsub" -Q "$QUEUE" dtifit --data="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./data --out="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./dti --mask="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./nodif_brain_mask --bvecs="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./bvecs --bvals="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./bvals
	fi
	fi
}

show_usage_fsldtifit() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function runs the FSL dtifit processing locally or via a scheduler."
				echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing and completed diffusion processing: "
				echo ""
				echo " <study_folder>/<case>/hcp/<case>/Diffusion ---> DWI data needs to be here"
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>			Name of function"
				echo "		--path=<study_folder>				Path to study data folder"
				echo "		--subjects=<comma_separated_list_of_cases>			List of subjects to run"
				echo "		--queue=<name_of_cluster_queue>			Cluster queue name"
				echo "		--runmethod=<type_of_run>			Perform Local Interactive Run [1] or Send to scheduler [2] [If local/interactive then log will be continuously generated in different format]"
				echo "		--overwrite=<clean_prior_run>			Delete prior run for a given subject"
				echo "" 
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='<path_to_study_subjects_folder>' --subjects='<case_id>' --function='fsldtifit' --queue='anticevic-gpu' --runmethod='2' --overwrite='yes'"
				echo ""				
				echo "-- Example with interactive terminal:"
				echo ""
				echo "AP fsldtifit <path_to_study_subjects_folder> '<case_id>' "
				echo ""
}

# ------------------------------------------------------------------------------------------------------
#  fslbedpostxgpu - Executes the bedpostx_gpu code from FSL (needed for probabilistic tractography)
# ------------------------------------------------------------------------------------------------------

fslbedpostxgpu() {

		# Establish global directory paths
		FSLGECUDAQ="$QUEUE" # Cluster queue name with GPU nodes - e.g. anticevic-gpu
		T1wDiffFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion
		BedPostXFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion.bedpostX
		LogFolder="$BedPostXFolder"/logs
		Overwrite="$Overwrite"
		export FSLGECUDAQ
		export SGE_ROOT=1
		NJOBS=4
		module load GPU/Cuda/6.5
		
		# Check if overwrite flag was set
		if [ "$Overwrite" == "yes" ]; then
			echo ""
			reho "Removing existing Bedpostx run for $CASE..."
			echo ""
			rm -rf "$BedPostXFolder" > /dev/null 2>&1
		fi
				
  		geho "Checking if Bedpostx was completed on $CASE..."
  		  		
  		# Set file depending on model specification
  		if [ "$Model" == 2 ]; then  
  			CheckFile="mean_d_stdsamples.nii.gz"
  		fi
  		if [ "$Model" == 3 ]; then
  			CheckFile="mean_Rsamples.nii.gz"
		fi

  		# Check if the file even exists
  		if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion.bedpostX/"$CheckFile" ]; then
  		
  		# Set file sizes to check for completion
		minimumfilesize=20000000
  		actualfilesize=`wc -c < "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion.bedpostX/merged_f1samples.nii.gz` > /dev/null 2>&1  		
  		filecount=`ls "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion.bedpostX/merged_*nii.gz | wc | awk {'print $1'}`
  		
  		fi
  			
  			# Then check if run is complete based on file count
  			if [ "$filecount" == 9 ]; then > /dev/null 2>&1
  				echo ""
  				cyaneho " --> $filecount merged samples for $CASE found."  			
  			# Then check if run is complete based on file size
  			if [ $(echo "$actualfilesize" | bc) -ge $(echo "$minimumfilesize" | bc) ]; then > /dev/null 2>&1
  				echo ""
  				cyaneho " --> Bedpostx outputs found and completed for $CASE"
  				echo ""
  				cyaneho "Check prior output logs here: $LogFolder"
  				echo ""
  				echo "--------------------------------------------------------------"
  				echo "" 
  				return 1
  			else 
  				echo ""
  				reho " --> Bedpostx outputs missing or incomplete for $CASE"
  				echo ""
  				reho "--------------------------------------------------------------"
  				echo ""  			
  			fi
  			fi
  		
  			echo ""
  			reho "Prior BedpostX run not found or incomplete for $CASE. Setting up new run..."
  			echo ""
  				
  				if [ "$Cluster" == 1 ]; then
  				
  					# unset the queue variables
  				    unset SGE_ROOT
					unset FSLGECUDAQ
		
					echo "Running bedpostx_gpu locally on `hostname`"
					echo "Check log file output here: $LogFolder"
					echo "--------------------------------------------------------------"
					echo ""
  	  	
					if [ -f "$T1wDiffFolder"/grad_dev.nii.gz ]; then
						bedpostx_gpu "$T1wDiffFolder"/. -n "$Fibers" -model "$Model" -b "$Burnin" -g --rician
					else	
  						bedpostx_gpu "$T1wDiffFolder"/. -n "$Fibers" -model "$Model" -b "$Burnin" --rician
					fi
		
				else
				
					# set scheduler for fsl_sub command
					fslsub="$Scheduler"
					# set the queue variables
					FSLGECUDAQ="$QUEUE" # Cluster queue name with GPU nodes - e.g. anticevic-gpu
					export FSLGECUDAQ
					export SGE_ROOT=1
					NJOBS=4
				
					if [ -f "$T1wDiffFolder"/grad_dev.nii.gz ]; then
						bedpostx_gpu "$T1wDiffFolder"/. -n "$Fibers" -model "$Model" -b "$Burnin" -g --rician
					else	
  						bedpostx_gpu "$T1wDiffFolder"/. -n "$Fibers" -model "$Model" -b "$Burnin" --rician
					fi
				
					geho "---------------------------------------------------------------------------------------"
					geho "Data successfully submitted to $QUEUE" 
					geho "Check output logs here: $LogFolder"
					geho "---------------------------------------------------------------------------------------"
					echo ""
				fi
}

show_usage_fslbedpostxgpu() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function runs the FSL bedpostx_gpu processing using a GPU-enabled node."
				echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing and completed diffusion processing: "
				echo ""
				echo " <study_folder>/<case>/hcp/<case>/Diffusion ---> DWI data needs to be here"
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>			Name of function"
				echo "		--path=<study_folder>				Path to study data folder"
				echo "		--subjects=<comma_separated_list_of_cases>			List of subjects to run"
				echo "		--fibers=<number_of_fibers>			Number of fibres per voxel, default 3"
				echo "		--model=<deconvolution_model>			Deconvolution model. 1: with sticks, 2: with sticks with a range of diffusivities (default), 3: with zeppelins"
				echo "		--burnin=<burnin_period_value>			Burnin period, default 1000"
				echo "		--queue=<name_of_cluster_queue>			Cluster queue name"
				echo "		--runmethod=<type_of_run>			Perform Local Interactive Run [1] or Send to scheduler [2] [If local/interactive then log will be continuously generated in different format]"
				echo "		--overwrite=<clean_prior_run>			Delete prior run for a given subject"
				echo "" 
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='<path_to_study_subjects_folder>' --subjects='<case_id>' --function='fslbedpostxgpu' --fibers='3' --burnin='3000' --model='3' --queue='anticevic-gpu' --runmethod='2' --overwrite='yes'"
				echo ""				
				echo "-- Example with interactive terminal:"
				echo ""
				echo "AP fslbedpostxgpu <path_to_study_subjects_folder> '<case_id>' "
				echo ""
}


# ------------------------------------------------------------------------------------------------------
#  pretractography - Executes the HCP Pretractography code (Matt's original implementation for cortex)
# ------------------------------------------------------------------------------------------------------

pretractography() {

		#EnvironmentScript="$StudyFolder/../fcMRI/hcpsetup.sh" #Pipeline environment script
				
		mkdir "$StudyFolder"/../../../fcMRI/hcp.logs/ &> /dev/null
		cd "$StudyFolder"/../../../fcMRI/hcp.logs/ &> /dev/null

		# Requirements for this function
		#  installed versions of: FSL5.0.2 or higher , FreeSurfer (version 5.2 or higher) , gradunwarp (python code from MGH)
		#  environment: FSLDIR , FREESURFER_HOME , HCPPIPEDIR , CARET7DIR , PATH (for gradient_unwarp.py)

		#Set up pipeline environment variables and software
		#. ${EnvironmentScript}

		# Log the originating call
		echo "$@"

		########################################## INPUTS ########################################## 

		#Scripts called by this script do assume they run on the results of the HCP minimal preprocesing pipelines from Q2

		######################################### DO WORK ##########################################

		LowResMesh="32" #32 if using HCP minimal preprocessing pipeline outputs
		Subject="$CASE"
	
  		if [ "$Cluster" == 1 ]; then
    		${HCPPIPEDIR}/DiffusionTractography/PreTractography.sh \
    		--path="$StudyFolder" \
    		--subject="$Subject" \
    		--lowresmesh="$LowResMesh"
    	else
    		fsl_sub."$fslsub" -Q "$QUEUE" \
    	    ${HCPPIPEDIR}/DiffusionTractography/PreTractography.sh \
    		--path="$StudyFolder" \
    		--subject="$Subject" \
    		--lowresmesh="$LowResMesh" 	
    	fi
    	
    	echo "set --path=$StudyFolder \
    	--subject=$Subject \
    	--lowresmesh=$LowResMesh"
}

show_usage_pretractography() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Function to generate the cortical dense connectome trajectory space."
    			echo ""
    			echo "Note: This function is deprecated as of 01/2017. The maintained function is pretractographydense"
    			echo "		-- run ap probtrackxgpudense for up-to-date help call of the supported function"
    			
}

# ------------------------------------------------------------------------------------------------------
#  probtrackxgpucortex - Executes the HCP Matrix1 code (Matt's original implementation for cortex)
# ------------------------------------------------------------------------------------------------------

probtrackxgpucortex() {

		mkdir "$StudyFolder"/../../../fcMRI/hcp.logs/ &> /dev/null
		cd "$StudyFolder"/../../../fcMRI/hcp.logs/ &> /dev/null
		
		# Requirements for this function
		#  installed versions of: FSL5.0.6 or higher with probtrackx2_gpu binary
		#  environment: FSLDIR , FREESURFER_HOME , HCPPIPEDIR , CARET7DIR

  		########################################## INPUTS ########################################## 
  		
  		#Scripts called by this script do assume they run on the results of the HCP minimal preprocesing pipelines from Q2

  		GitRepo="$HCPPIPEDIR"
  		Subject="$CASE"
  		DownSampleNameI="32"
  		DiffusionResolution="$DiffusionResolution" #Set to diffusion voxel resolution
  		Caret7_Command="wb_command"
  		HemisphereSTRING="$HemisphereSTRING" #L@R or L or R or Whole
  		NumberOfSamples="5000" #1 sample then 2 and calculate total time required per sample
  		StepSize="$StepSize" #1/4 diffusion resolution recommended???
  		Curvature="0" #Inverse cosine of this value is the angle, default 0.2=~78 degrees, 0=90 degrees
  		DistanceThreshold="0" #Start at zero?
  		PDSTRING="$PDSTRING" #Set to YES to use --pd flag in probtrackx or NO to not use it
  		GlobalBinariesDir="${GitRepo}/global/binaries"
  		
  		######################################### DO WORK ##########################################


  			for Hemisphere in $HemisphereSTRING ; do
  			  	for PD in $PDSTRING ; do
  				  		
  				  		minimumfilesize=50000000 # define file size for checking
  						
  						if [ "$PD" == "yes" ]; then
  							PDPath="pd_"
  							ResultPD="$StudyFolder"/"$CASE"/T1w/Results/"$Hemisphere"_Trajectory_Matrix1_"$PDPath""$StepSize"
  						fi
  						if [ "$PD" == "NO" ]; then
  							PDPath=""
  							ResultPD="$StudyFolder"/"$CASE"/T1w/Results/"$Hemisphere"_Trajectory_Matrix1_"$PDPath""$StepSize"
  						fi
  						
  						# Check if result exists and if exceeds min size
  						echo "Checking Matrix1 for $CASE $Hemisphere hemisphere and distance parameter $PD"
  						#echo `ls $ResultPD/fdt_matrix1.dot`
  						if [ -f "$ResultPD"/fdt_matrix1.dot ] && [ $(echo ""$(wc -c <"$ResultPD"/fdt_matrix1.dot)"" | bc) -gt $(echo "$minimumfilesize" | bc) ]; then
  							echo "Data Found: $ResultPD/fdt_matrix1.dot"
  							echo "Tractography completed for $CASE $Hemisphere hemisphere and distance parameter $PD"
  						else
  					  		# Execute calls
  					  		if [ "$Cluster" == 1 ]; then
  					  			echo "Running probtrackx2_gpu for $CASE $Hemisphere hemisphere and distance parameter $PD..."
    							"$GitRepo"/DiffusionTractography/scripts/RunMatrix1Tractography_gpu.sh "$StudyFolder" "$Subject" "$DownSampleNameI" "$DiffusionResolution" "$Caret7_Command" "$Hemisphere" "$NumberOfSamples" "$StepSize" "$Curvature" "$DistanceThreshold" "$GlobalBinariesDir" "$PD"
							else
								echo "Submitting probtrackx2_gpu job $CASE $HemisphereSTRING hemisphere and distance parameter $PDSTRING to $QUEUE queue..."
								fsl_sub."$fslsub" -Q "$QUEUE" "$GitRepo"/DiffusionTractography/scripts/RunMatrix1Tractography_gpu.sh "$StudyFolder" "$Subject" "$DownSampleNameI" "$DiffusionResolution" "$Caret7_Command" "$Hemisphere" "$NumberOfSamples" "$StepSize" "$Curvature" "$DistanceThreshold" "$GlobalBinariesDir" "$PD"
							fi
							echo "set -- $StudyFolder $Subject $DownSampleNameI $DiffusionResolution $Caret7_Command $Hemisphere $NumberOfSamples $StepSize $Curvature $DistanceThreshold $GlobalBinariesDir $PD"
						fi
						unset ResultPD # clear directory variable
						unset PD
				done
			done
}

show_usage_probtrackxgpucortex() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Original implementation of cortical dense connectome."
    			echo ""
    			echo "Note: This function is deprecated as of 01/2017. The maintained function is probtrackxgpudense"
    			echo "		-- run ap probtrackxgpudense for up-to-date help call of the supported function"
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  makedensecortex - Executes the code for creating dense cortical connectomes (Matt's original code)
# ------------------------------------------------------------------------------------------------------

makedensecortex() {

		# Requirements for this function
		#  installed versions of: FSL5.0.6 or higher with probtrackx2_gpu binary
		#  environment: FSLDIR , FREESURFER_HOME , HCPPIPEDIR , CARET7DIR
		
		mkdir "$StudyFolder"/../../../fcMRI/hcp.logs/ &> /dev/null
		cd "$StudyFolder"/../../../fcMRI/hcp.logs/ &> /dev/null
		
  		########################################## INPUTS ########################################## 
  		
  		#Scripts called by this script do assume they run on the results of the HCP minimal preprocesing pipelines from Q2

  		GitRepo="$HCPPIPEDIR"
  		Subject="$CASE"
  		DownSampleNameI="32"
  		DiffusionResolution="$DiffusionResolution" #Set to diffusion voxel resolution
  		Caret7_Command="wb_command"
  		HemisphereSTRING="$HemisphereSTRING" #L@R or L or R or Whole
  		StepSize="$StepSize" #1/4 diffusion resolution recommended???
  		PDSTRING="$PDSTRING" #Set to YES to use --pd flag in probtrackx or NO to not use it
  		MatrixNumber="1" #1 or 3
  		GlobalBinariesDir="${GitRepo}/global/binaries"
  		
  		######################################### DO WORK ##########################################
		  			
  			for Hemisphere in $HemisphereSTRING ; do
  			  	for PD in $PDSTRING ; do
  				  		
  				  		minimumfilesize=100000000 # define file size for checking
  					
  						if [ "$PD" == "yes" ]; then
  							PDPath="pd_"
  							ResultPD="$StudyFolder"/"$CASE"/T1w/Results/"$Hemisphere"_Trajectory_Matrix1_"$PDPath""$StepSize"
  						fi
  						if [ "$PD" == "NO" ]; then
  							PDPath=""
  							ResultPD="$StudyFolder"/"$CASE"/T1w/Results/"$Hemisphere"_Trajectory_Matrix1_"$PDPath""$StepSize"
  						fi
  						
  						# Check if result exists and if exceeds min size
  						echo "Checking Dense Connectome for $CASE $Hemisphere hemisphere and distance parameter $PD"
  						#echo `ls $ResultPD/fdt_matrix1.dconn.nii` &> /dev/null
  						if [ -f "$ResultPD"/fdt_matrix1.dconn.nii ] && [ $(echo ""$(wc -c <"$ResultPD"/fdt_matrix1.dconn.nii)"" | bc) -gt $(echo "$minimumfilesize" | bc) ]; then
  							echo "Data Found: $ResultPD/fdt_matrix1.dconn.nii"
  							echo "Dense Connectome completed for $CASE $Hemisphere hemisphere and distance parameter $PD"
  						else
  					  		# Execute calls
  					  		if [ "$Cluster" == 1 ]; then
  					  			echo "Running dense connectome for $CASE $Hemisphere hemisphere and distance parameter $PD..."  				
      							"$GitRepo"/DiffusionTractography/scripts/MakeTractographyDenseConnectomesNoMatrix2.sh "$StudyFolder" "$Subject" "$DownSampleNameI" "$DiffusionResolution" "$Caret7_Command" "$Hemisphere" "$MatrixNumber" "$PD" "$StepSize"
							else
								echo "Submitting dense connectome job $CASE $HemisphereSTRING hemisphere and distance parameter $PDSTRING to $QUEUE queue..."
						    	fsl_sub."$fslsub" -Q "$QUEUE" "$GitRepo"/DiffusionTractography/scripts/MakeTractographyDenseConnectomesNoMatrix2.sh "$StudyFolder" "$Subject" "$DownSampleNameI" "$DiffusionResolution" "$Caret7_Command" "$Hemisphere" "$MatrixNumber" "$PD" "$StepSize"
							fi
								echo "set -- $StudyFolder $Subject $DownSampleNameI $DiffusionResolution $Caret7_Command $Hemisphere $MatrixNumber $PD $StepSize"
						fi
				
						unset ResultPD # clear directory variable
						unset PD
				
				done
			done
}

show_usage_makedensecortex() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "Original implementation of cortical dense connectome final file generation."
    			echo ""
    			echo "Note: This function is deprecated as of 01/2017. The maintained function is probtrackxgpudense"
    			echo "		-- run ap probtrackxgpudense for up-to-date help call of the supported function"
    			echo ""
}


# ------------------------------------------------------------------------------------------------------------------------------
#  autoptx - Executes the autoptx script from FSL (needed for probabilistic estimation of large-scale fiber bundles / tracts)
# -------------------------------------------------------------------------------------------------------------------------------

autoptx() {

Subject="$CASE"
StudyFolder="$StudyFolder"/"$CASE"/hcp/
BpxFolder="$BedPostXFolder"
QUEUE="$QUEUE"

if [ "$Cluster" == 1 ]; then

		echo "--------------------------------------------------------------"
		echo "Running locally on `hostname`"
		echo "Check log file output here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""

		"$AutoPtxFolder"/autoPtx "$StudyFolder" "$Subject" "$BpxFolder"
		"$AutoPtxFolder"/Prepare_for_Display.sh $StudyFolder/$Subject/MNINonLinear/Results/autoptx 0.005 1
		"$AutoPtxFolder"/Prepare_for_Display.sh $StudyFolder/$Subject/MNINonLinear/Results/autoptx 0.005 0

else 

		# set scheduler for fsl_sub command
		fslsub="$Scheduler"
		fsl_sub."$fslsub" -Q "$QUEUE" "$AutoPtxFolder"/autoPtx "$StudyFolder" "$Subject" "$BpxFolder"
		fsl_sub."$fslsub" -Q "$QUEUE" -j <jid> "$AutoPtxFolder"/Prepare_for_Display.sh $StudyFolder/$Subject/MNINonLinear/Results/autoptx 0.005 1
		fsl_sub."$fslsub" -Q "$QUEUE" -j <jid> "$AutoPtxFolder"/Prepare_for_Display.sh $StudyFolder/$Subject/MNINonLinear/Results/autoptx 0.005 0

		echo "--------------------------------------------------------------"
		echo "Data successfully submitted to $QUEUE" 
		echo "Check output logs here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""
fi
}

show_usage_autoptx() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "USAGE PENDING..."
				echo ""
}

# -------------------------------------------------------------------------------------------------------------------
#  pretractographydense - Executes the HCP Pretractography code (Stam's implementation for all grayordinates)
# ------------------------------------------------------------------------------------------------------------------

pretractographydense() {

		ScriptsFolder="$HCPPIPEDIR_dMRITracFull"/PreTractography
		LogFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/log_pretractographydense
		mkdir "$LogFolder"  &> /dev/null
		RunFolder="$StudyFolder"/"$CASE"/hcp/
		
		if [ "$Cluster" == 1 ]; then
  				
  					echo ""
  					echo "--------------------------------------------------------------"
					echo "Running Pretractography Dense locally on `hostname`"
					echo "Check output here: $LogFolder"
					echo "--------------------------------------------------------------"
					echo ""
					"$ScriptsFolder"/PreTractography.sh "$RunFolder" "$CASE" 0 >> "$LogFolder"/PretractographyDense_"$CASE"_`date +%Y-%m-%d-%H-%M-%S`.log
		else
				
					echo "Job ID:"
					fslsub="$Scheduler" # set scheduler for fsl_sub command
					fsl_sub."$fslsub" -Q "$QUEUE" -l "$LogFolder" -R 10000 "$ScriptsFolder"/PreTractography.sh "$RunFolder" "$CASE" 0

					echo ""
					echo "--------------------------------------------------------------"
					echo "Scheduler: $Scheduler"
					echo "QUEUE Name: $QUEUE"
					echo "Data successfully submitted to $QUEUE" 
					echo "Check output logs here: $LogFolder"
					echo "--------------------------------------------------------------"
					echo ""
	fi

}

show_usage_pretractographydense() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function runs the Pretractography Dense trajectory space generation."
				echo "Note that this is a very quick function to run [< 5min] so no overwrite options exist."
				echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing and completed diffusion and bedpostX processing: "
				echo ""
				echo " <study_folder>/<case>/hcp/<case>/Diffusion ---> DWI data needs to be here"
				echo " <study_folder>/<case>/hcp/<case>/T1w/Diffusion.bedpostX ---> BedpostX output data needs to be here"
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>			Name of function"
				echo "		--path=<study_folder>				Path to study data folder"
				echo "		--subjects=<comma_separated_list_of_cases>	List of subjects to run"
				echo "		--queue=<name_of_cluster_queue>			Cluster queue name"
				echo "		--runmethod=<type_of_run>			Perform Local Interactive Run [1] or Send to scheduler [2] [If local/interactive then log will be continuously generated in different format]"
				echo "		--scheduler=<name_of_cluster_scheduler>		Cluster scheduler program: e.g. LSF or PBS"
				echo "" 
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Anticevic.DP5/subjects' --subjects='ta9342' --function='pretractographydense' --queue='anticevic' --runmethod='2' --scheduler='lsf'"
				echo ""				
				echo "-- Example with interactive terminal:"
				echo ""
				echo "AP pretractographydense /gpfs/project/fas/n3/Studies/Anticevic.DP5/subjects 'ta6455' "
				echo ""
}

# --------------------------------------------------------------------------------------------------------------------------------------------------
#  probtrackxgpudense - Executes the HCP Matrix1 and / or 3 code and generates WB dense connectomes (Stam's implementation for all grayordinates)
# --------------------------------------------------------------------------------------------------------------------------------------------------

probtrackxgpudense() {

		# -- Set parameters
		ScriptsFolder="$HCPPIPEDIR_dMRITracFull"/Tractography_gpu_scripts
		ResultsFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/Tractography
		RunFolder="$StudyFolder"/"$CASE"/hcp/
		NsamplesMatrixOne="$NsamplesMatrixOne"
		NsamplesMatrixThree="$NsamplesMatrixThree"
		
		# -- Generate the results and log folders
		mkdir "$ResultsFolder"  &> /dev/null
		mkdir "$LogFolder"  &> /dev/null
		
		# -- Set the CUDA queue 
		FSLGECUDAQ="$QUEUE"
		export FSLGECUDAQ="$QUEUE"
		
		# -------------------------------------------------
		# -- Do work for Matrix 1 if --omatrix1 flag set 
		# -------------------------------------------------
		
		if [ "$MatrixOne" == "yes" ]; then
		
			LogFolder="$ResultsFolder"/Mat1_logs
		
			# -- Check of overwrite flag was set
			if [ "$Overwrite" == "yes" ]; then
				echo ""
				reho " --- Removing existing Probtrackxgpu Matrix1 dense run for $CASE..."
				echo ""
				rm -f "$ResultsFolder"/Conn1.dconn.nii.gz &> /dev/null
			fi
			
			# -- Check for Matrix 1 completion
			echo ""
  			geho "Checking if ProbtrackX Matrix 1 and dense connectome was completed on $CASE..."
  			echo ""
  			
  			# -- Check if the file even exists
  			if [ -f "$ResultsFolder"/Conn1.dconn.nii.gz ]; then
  		
  				# -- Set file sizes to check for completion
				minimumfilesize=100000000
  				actualfilesize=`wc -c < "$ResultsFolder"/Conn1.dconn.nii.gz` > /dev/null 2>&1  		
  				
  				# -- Then check if Matrix 1 run is complete based on size
  				if [ $(echo "$actualfilesize" | bc) -ge $(echo "$minimumfilesize" | bc) ]; then > /dev/null 2>&1
  					echo ""
  					cyaneho "DONE -- ProbtrackX Matrix1 solution and dense connectome was completed for $CASE"
  					cyaneho "To re-run set overwrite flag to 'yes'"
  					cyaneho "Check prior output logs here: $LogFolder"
  					echo ""
  					echo "--------------------------------------------------------------"
  					echo ""  			
  				fi

			else 
				
				# -- If run is incomplete perform run for Matrix 1
				echo ""
  				geho "ProbtrackX Matrix1 solution and dense connectome incomplete for $CASE. Starting run..."
  				echo ""
  								
				# -- Set nsamples variable 
				if [ "$NsamplesMatrixOne" == "" ];then NsamplesMatrixOne=10000; fi
		
				# -- submit script
				# set scheduler for fsl_sub command
				fslsub="$Scheduler"
				echo ""
				echo "Job ID:"
				echo ""
				"$ScriptsFolder"/RunMatrix1.sh "$RunFolder" "$CASE" "$NsamplesMatrixOne" "$Scheduler"

					
				# -- record output calls
				echo ""
				echo "Submitted Matrix 1 job for $CASE"
				echo ""
				echo ""
				echo "--------------------------------------------------------------"
				echo "Scheduler: $Scheduler"
				echo "QUEUE Name: $QUEUE"
				echo "Data successfully submitted to $QUEUE" 
				echo "Number of samples for Matrix1: $NsamplesMatrixOne"
				echo "Check output logs here: $LogFolder"
				echo "--------------------------------------------------------------"
				echo ""
			fi	
		fi
		
		# -------------------------------------------------
		# -- Do work for Matrix 3 if --omatrix3 flag set 
		# -------------------------------------------------
		
		if [ "$MatrixThree" == "yes" ]; then
		
			LogFolder="$ResultsFolder"/Mat3_logs
		
			# -- Check of overwrite flag was set
			if [ "$Overwrite" == "yes" ]; then
				echo ""
				reho " --- Removing existing Probtrackxgpu Matrix3 dense run for $CASE..."
				echo ""
				rm -f "$ResultsFolder"/Conn3.dconn.nii.gz  &> /dev/null
			fi
			
			# -- Check for Matrix 3 completion
			echo ""
  			geho "Checking if ProbtrackX Matrix 3 and dense connectome was completed on $CASE..."
  			echo ""
  			
  			# -- Check if the file even exists
  			if [ -f "$ResultsFolder"/Conn3.dconn.nii.gz ]; then
  		
  				# -- Set file sizes to check for completion
				minimumfilesize=100000000
  				actualfilesize=`wc -c < "$ResultsFolder"/Conn3.dconn.nii.gz` > /dev/null 2>&1  		
  				
  				# -- Then check if Matrix 3 run is complete based on size
  				if [ $(echo "$actualfilesize" | bc) -ge $(echo "$minimumfilesize" | bc) ]; then > /dev/null 2>&1
  					echo ""
  					cyaneho "DONE -- ProbtrackX Matrix3 solution and dense connectome was completed for $CASE"
  					cyaneho "To re-run set overwrite flag to 'yes'"
  					cyaneho "Check prior output logs here: $LogFolder"
  					echo ""
  					echo "--------------------------------------------------------------"
  					echo ""  			
  				fi
			
			else 
			
				# -- If run is incomplete perform run for Matrix 3
  				geho "ProbtrackX Matrix3 solution and dense connectome incomplete for $CASE. Starting run..."
  				echo ""
  				
				# -- Set nsamples variable 
				if [ "$NsamplesMatrixThree" == "" ];then NsamplesMatrixThree=3000; fi
		
				# -- submit script
				# set scheduler for fsl_sub command
				fslsub="$Scheduler"
				echo ""
				echo "Job ID:"
				echo ""
				"$ScriptsFolder"/RunMatrix3.sh "$RunFolder" "$CASE" "$NsamplesMatrixThree" "$Scheduler"

				# -- record output calls
				echo ""
				echo "Submitted Matrix 3 job for $CASE"
				echo ""
				echo ""
				echo "--------------------------------------------------------------"
				echo "Scheduler: $Scheduler"
				echo "QUEUE Name: $QUEUE"
				echo "Data successfully submitted to $QUEUE" 
				echo "Number of samples for Matrix3: $NsamplesMatrixThree"
				echo "Check output logs here: $LogFolder"
				echo "--------------------------------------------------------------"
				echo ""
			fi	
		fi		
}

show_usage_probtrackxgpudense() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function runs the probtrackxgpu dense whole-brain connectome generation by calling $ScriptsFolder/RunMatrix1.sh or $ScriptsFolder/RunMatrix3.sh"
				echo "Note that this function needs to send work to a GPU-enabled queue. It is cluster-enabled by default."
				echo "It explicitly assumes the Human Connectome Project folder structure and completed fslbedpostxgpu and pretractographydense functions processing:"
				echo ""
				echo " <study_folder>/<case>/hcp/<case>/T1w/Diffusion            ---> Processed DWI data needs to be here"
				echo " <study_folder>/<case>/hcp/<case>/T1w/Diffusion.bedpostX   ---> BedpostX output data needs to be here"
				echo " <study_folder>/<case>/hcp/<case>/MNINonLinear             ---> T1w images need to be in MNINonLinear space here"
				echo ""
				echo "Outputs will be here:"
				echo ""
				echo " <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Conn1.dconn.nii.gz   ---> Dense Connectome CIFTI Results in MNI space for Matrix1"
				echo " <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Conn3.dconn.nii.gz   ---> Dense Connectome CIFTI Results in MNI space for Matrix3"
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>					Name of function"
				echo "		--path=<study_folder>						Path to study data folder"
				echo "		--subjects=<comma_separated_list_of_cases>			List of subjects to run"
				echo "		--queue=<name_of_cluster_queue>					Cluster queue name"
				echo "		--scheduler=<name_of_cluster_scheduler>				Cluster scheduler program: e.g. LSF or PBS"
				echo "		--overwrite=<clean_prior_run>					Delete a prior run for a given subject [Note: this will delete only the Matrix run specified by the -omatrix flag]"
				echo "		--omatrix1=<matrix1_model>					Specify if you wish to run matrix 1 model [yes or omit flag]"
				echo "		--omatrix3=<matrix3_model>					Specify if you wish to run matrix 3 model [yes or omit flag]"
				echo "		--nsamplesmatrix1=<Number_of_Samples_for_Matrix1>		Number of samples - default=10000" 
				echo "		--nsamplesmatrix3=<Number_of_Samples_for_Matrix3>		Number of samples - default=3000" 
				echo "" 
				echo "-- GENERIC PARMETERS SET BY DEFAULT:"
				echo ""
				echo "       --loopcheck --forcedir --fibthresh=0.01 -c 0.2 --sampvox=2 --randfib=1 -S 2000 --steplength=0.5"
				echo ""
				echo "       ** The function calls either of these based on the --omatrix1 and --omatrix3 flags: "
				echo ""
				echo "                               $HCPPIPEDIR_dMRITracFull/Tractography_gpu_scripts/RunMatrix1.sh"
				echo "                               $HCPPIPEDIR_dMRITracFull/Tractography_gpu_scripts/RunMatrix3.sh"
				echo ""
				echo "                               --> both are cluster-aware and send the jobs to the GPU-enabled queue. They do not work interactively."
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Anticevic.DP5/subjects' --subjects='ta9776' --function='probtrackxgpudense' --queue='anticevic-gpu' --scheduler='lsf' --omatrix1='yes' --nsamplesmatrix1='10000' --overwrite='no'"
				echo ""				
				echo "-- Example with interactive terminal:"
				echo ""
				echo "AP probtrackxgpudense /gpfs/project/fas/n3/Studies/Anticevic.DP5/subjects 'ta9776' "
				echo ""
}

# ------------------------------------------------------------------------------------------------------------------------------
#  Sync data from AWS buckets - customized for HCP
# -------------------------------------------------------------------------------------------------------------------------------

awshcpsync() {

mkdir "$StudyFolder"/aws.logs &> /dev/null
cd "$StudyFolder"/aws.logs

if [ "$RunMethod" == "1" ]; then

	if [ -d "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear ]; then
		
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality" &> /dev/null
		time aws s3 sync --dryrun s3:/"$Awsuri"/"$CASE"/"$Modality" "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality"/ >> awshcpsync_"$CASE"_"$Modality"_`date +%Y-%m-%d-%H-%M-%S`.log 

	else

		mkdir "$StudyFolder"/"$CASE" &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE" &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality" &> /dev/null
		time aws s3 sync --dryrun s3:/"$Awsuri"/"$CASE"/"$Modality" "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality"/ >> awshcpsync_"$CASE"_"$Modality"_`date +%Y-%m-%d-%H-%M-%S`.log 

	fi

fi

if [ "$RunMethod" == "2" ]; then

	if [ -d "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear ]; then
	
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality" &> /dev/null
		time aws s3 sync s3:/"$Awsuri"/"$CASE"/"$Modality" "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality"/ >> awshcpsync_"$CASE"_"$Modality"_`date +%Y-%m-%d-%H-%M-%S`.log 

	else

		mkdir "$StudyFolder"/"$CASE" &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE" &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality" &> /dev/null
		time aws s3 sync s3:/"$Awsuri"/"$CASE"/"$Modality" "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality"/ >> awshcpsync_"$CASE"_"$Modality"_`date +%Y-%m-%d-%H-%M-%S`.log 

	fi

fi
	
}

show_usage_awshcpsync() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function enables syncing of HCP data from the Amazon AWS S3 repository."
				echo "It assumes you have enabled your AWS credentials via the HCP website."
				echo "These credentials are expected in your home folder under ./aws/credentials."
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>			Name of function"
				echo "		--path=<study_folder>				Path to study data folder"
				echo "		--subjects=<comma_separated_list_of_cases>	List of subjects to run"
				echo "		--modality=<modality_to_sync>			Which modality or folder do you want to sync [e.g. MEG, MNINonLinear, T1w]"
				echo "		--awsuri=<aws_uri_location>			Enter the AWS URI [e.g. /hcp-openaccess/HCP_900]"
				echo "		--runmethod=<type_of_run>			Perform a dry test run [1] or real run [2]"
				echo "" 
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='/Volumes/syn5science/Studies/Connectome/subjects' --subjects='173536' --function='awshcpsync' --modality='T1w' --awsuri='/hcp-openaccess/HCP_900' --runmethod='2'"
				echo ""				
				echo "-- Example with interactive terminal:"
				echo ""
				echo "AP awshcpsync /Volumes/syn5science/Studies/Connectome/subjects '173536' "
				echo ""
}

# ------------------------------------------------------------------------------------------------------------------------------
#  Structural QC - customized for HCP - qcpreproc
# -------------------------------------------------------------------------------------------------------------------------------

qcpreproc() {
	
	# -- Check of overwrite flag was set
	if [ "$Overwrite" == "yes" ]; then
		echo ""
		reho " --- Removing existing ${Modality} QC scene: ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
		echo ""
		if [ "$Modality" == "BOLD" ]; then
			for BOLD in $BOLDS
			do
				rm -f ${OutPath}/${CASE}.${Modality}.${BOLD}.* &> /dev/null
			done
		else
			rm -f "$OutPath"/"$CASE"."$Modality".* &> /dev/null
		fi	
	fi
	
	# -- Check if a given case exists
	if [ -f "$OutPath"/"$CASE"."$Modality".QC.png ]; then
		echo ""
		geho " --- ${Modality} QC scene completed: ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
		echo ""
	else
		geho " --- Generating ${Modality} QC scene: ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
		echo ""
	
	# -- Check general output folders for QC
	if [ ! -d "$StudyFolder"/QC ]; then
		mkdir -p "$StudyFolder"/QC &> /dev/null
	fi
	# -- Check T1w output folders for QC
	if [ ! -d "$OutPath" ]; then
		mkdir -p "$OutPath" &> /dev/null
	fi
	# -- Define log folder
	LogFolder="$OutPath"/qclog
	mkdir "$LogFolder"  &> /dev/null
		
	
	if [ "$Modality" == "BOLD" ]; then
		for BOLD in $BOLDS; 
		do
			# -- Generate QC statistics for a given BOLD
			geho " --- Generating QC statistics commands for BOLD ${BOLD} on ${CASE}..."
			echo ""
			
			# -- Compute TSNR and log it
			wb_command -cifti-reduce ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}.dtseries.nii TSNR ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_TSNR.dscalar.nii -exclude-outliers 4 4
			TSNR=`wb_command -cifti-stats ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_TSNR.dscalar.nii -reduce MEAN`
			TSNRLog="${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_TSNR.dscalar.nii: ${TSNR}"
			printf "${TSNRLog}\n" >> ${OutPath}/TSNR_Report_${BOLD}_`date +%Y-%m-%d`.txt

			# -- Get values for plotting GS chart & Compute the GS scalar series file
			# -- Get TR
			TR=`fslval ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}.nii.gz pixdim4`
			# -- Clean preexisting outputs
			rm -f ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS.txt &> /dev/null
			rm -f ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS.dtseries.nii &> /dev/null
			rm -f ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS.sdseries.nii &> /dev/null
			# -- Regenerate outputs
			wb_command -cifti-reduce ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}.dtseries.nii MEAN ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS.dtseries.nii -direction COLUMN
			wb_command -cifti-stats ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS.dtseries.nii -reduce MEAN >> ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS.txt

			if [ ${SkipFrames} > 0 ]; then 
				rm -f ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS_omit_initial_${SkipFrames}_TRs.txt &> /dev/null
				tail -n +${SkipFrames} ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS.txt >> ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS_omit_initial_${SkipFrames}_TRs.txt
				TR=`cat ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS_omit_initial_${SkipFrames}_TRs.txt | wc -l` 
				wb_command -cifti-create-scalar-series ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS_omit_initial_${SkipFrames}_TRs.txt ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS.sdseries.nii -transpose -series SECOND 0 ${TR}
				xmax="$TR"
			else
				wb_command -cifti-create-scalar-series ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS.txt ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS.sdseries.nii -transpose -series SECOND 0 ${TR}
				xmax=`fslval ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}.nii.gz dim4`
			fi
			
			# -- Get mix/max stats
			ymax=`wb_command -cifti-stats ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS.sdseries.nii -reduce MAX | sort -rn | head -n 1`	
			ymin=`wb_command -cifti-stats ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_${BOLDSuffix}_GS.sdseries.nii -reduce MAX | sort -n | head -n 1`
	
			# -- Rsync over template files for a given BOLD
			Com1="rsync -aWH ${TemplateFolder}/S900* ${OutPath}/ &> /dev/null"
			Com2="rsync -aWH ${TemplateFolder}/MNI* ${OutPath}/ &> /dev/null"
	
			# -- Setup naming conventions before generating scene
			Com3="cp ${TemplateFolder}/TEMPLATE.${Modality}.QC.wb.scene ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
			Com4="sed -i -e 's|DUMMYPATH|$StudyFolder|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene" 
			Com5="sed -i -e 's|DUMMYCASE|$CASE|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
			Com6="sed -i -e 's|DUMMYBOLDDATA|$BOLD|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"

			Com7="sed -i -e 's|DUMMYXAXISMAX|$xmax|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
			Com8="sed -i -e 's|DUMMYYAXISMAX|$ymax|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
			Com9="sed -i -e 's|DUMMYYAXISMIN|$ymin|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"

			# -- Set the BOLDSuffix variable
			if [ "$BOLDSuffix" == "" ]; then
				Com10="sed -i -e 's|_DUMMYBOLDSUFFIX|$BOLDSuffix|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
			else
				Com10="sed -i -e 's|DUMMYBOLDSUFFIX|$BOLDSuffix|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
			fi
						
			# -- Output image of the scene
			Com11="wb_command -show-scene ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene 1 ${OutPath}/${CASE}.${Modality}.${BOLD}.GSmap.QC.wb.png 1194 539"
			Com12="wb_command -show-scene ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene 2 ${OutPath}/${CASE}.${Modality}.${BOLD}.GStimeseries.QC.wb.png 1194 539"

			# -- Clean temp scene
			Com13="rm ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene-e &> /dev/null"
			
			# -- Combine all the calls into a single command
			ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com8; $Com9; $Com10; $Com11; $Com12; $Com13"
	
			if [ "$Cluster" == 1 ]; then
  				echo ""
  				echo "---------------------------------------------------------------------------------"
				echo "Running QC locally on `hostname`"
				echo "Check output here: $LogFolder"
				echo "---------------------------------------------------------------------------------"
		 		echo ""
				eval "$ComQUEUE" &> "$LogFolder"/QC_"$CASE"_`date +%Y-%m-%d-%H-%M-%S`.log
			else
				echo "Job ID:"
				fslsub="$Scheduler" # set scheduler for fsl_sub command
				rm -f "$LogFolder"/"$CASE"_ComQUEUE_"$BOLD".sh &> /dev/null
				echo "$ComQUEUE" >> "$LogFolder"/"$CASE"_ComQUEUE_"$BOLD".sh
				chmod 770 "$LogFolder"/"$CASE"_ComQUEUE_"$BOLD".sh
				fsl_sub."$fslsub" -Q "$QUEUE" -l "$LogFolder" -R 10000 "$LogFolder"/"$CASE"_ComQUEUE_"$BOLD".sh
				echo ""
				echo "---------------------------------------------------------------------------------"
				echo "Scheduler: $Scheduler"
				echo "QUEUE Name: $QUEUE"
				echo "Data successfully submitted to $QUEUE" 
				echo "Check output logs here: $LogFolder"
				echo "---------------------------------------------------------------------------------"
				echo ""
			fi
		done
	else	
	
	# -- Generate a QC scene file appropriate for each subject for each modality
	
	# -- Rsync over template files for a given modality
	Com1="rsync -aWH ${TemplateFolder}/S900* ${OutPath}/ &> /dev/null"
	Com2="rsync -aWH ${TemplateFolder}/MNI* ${OutPath}/ &> /dev/null"
	Com3="rsync -aWH ${TemplateFolder}/TEMPLATE.${Modality}.QC.wb.scene ${OutPath} &> /dev/null"
	
	# -- Setup naming conventions before generating scene
	Com4="cp ${OutPath}/TEMPLATE.${Modality}.QC.wb.scene ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
	Com5="sed -i -e 's|DUMMYPATH|$StudyFolder|g' ${OutPath}/${CASE}.${Modality}.QC.wb.scene" 
	Com6="sed -i -e 's|DUMMYCASE|$CASE|g' ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
	
	if [ "$Modality" == "DWI" ]; then
		# -- Setup naming conventions for DWI before generating scene
		Com6a="sed -i -e 's|DUMMYDWIPATH|$DWIPath|g' ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
			if [ "$DWILegacy" == "yes" ]; then
				unset "$DWIDataLegacy" >/dev/null 2>&1
				DWIDataLegacy="${CASE}_${DWIData}"
				Com6b="sed -i -e 's|DUMMYDWIDATA|$DWIDataLegacy|g' ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
			else
				Com6b="sed -i -e 's|DUMMYDWIDATA|$DWIData|g' ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
			fi
		Com6="$Com6; $Com6a; $Com6b"
	fi
	
	# -- Output image of the scene
	Com7="wb_command -show-scene ${OutPath}/${CASE}.${Modality}.QC.wb.scene 1 ${OutPath}/${CASE}.${Modality}.QC.png 1194 539"
	# -- Clean templates for next subject
	Com8="rm ${OutPath}/${CASE}.${Modality}.QC.wb.scene-e &> /dev/null"
	Com9="rm ${OutPath}/TEMPLATE.${Modality}.QC.wb.scene &> /dev/null"
	# -- Combine all the calls into a single command
	ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com8; $Com9"
	
	# -- queue a local task or a scheduler job
 	
	if [ "$Cluster" == 1 ]; then
  		echo ""
  		echo "---------------------------------------------------------------------------------"
		echo "Running QC locally on `hostname`"
		echo "Check output here: $LogFolder"
		echo "---------------------------------------------------------------------------------"
		echo ""
		eval "$ComQUEUE" &> "$LogFolder"/QC_"$CASE"_`date +%Y-%m-%d-%H-%M-%S`.log
	fi
	if [ "$Cluster" == 2 ]; then
		echo "Job ID:"
		fslsub="$Scheduler" # set scheduler for fsl_sub command
		rm -f "$LogFolder"/"$CASE"_ComQUEUE.sh &> /dev/null
		echo "$ComQUEUE" >> "$LogFolder"/"$CASE"_ComQUEUE.sh
		chmod 700 "$LogFolder"/"$CASE"_ComQUEUE.sh
		fsl_sub."$fslsub" -Q "$QUEUE" -l "$LogFolder" -R 10000 "$LogFolder"/"$CASE"_ComQUEUE.sh
		echo ""
		echo "---------------------------------------------------------------------------------"
		echo "Scheduler: $Scheduler"
		echo "QUEUE Name: $QUEUE"
		echo "Data successfully submitted to $QUEUE" 
		echo "Check output logs here: $LogFolder"
		echo "---------------------------------------------------------------------------------"
		echo ""
	fi
	fi
	fi

}

show_usage_qcpreproc() {
				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function runs the QC preprocessing for a given specified modality. Supported: T1w, T2w, myelin, BOLD, DWI."
				echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing."
				echo ""
				echo ""
				echo "The function is compabible with both legacy data [without T2w scans] and HCP-compliant data [with T2w scans and DWI]"
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>					Name of function"
				echo "		--path=<study_folder>						Path to study data folder"
				echo "		--subjects=<comma_separated_list_of_cases>					List of subjects to run"
				echo "		--subjects=<list_of_cases>					List of subjects to run, separated by commas"
				echo "		--modality=<input_modality_for_qc>				Specify the modality to perform QC on [Supported: T1w, T2w, myelin, BOLD, DWI]"
				echo "		--runmethod=<type_of_run>					Perform Local Interactive Run [1] or Send to scheduler [2] [If local/interactive then log will be continuously generated in different format]"
				echo "		--queue=<name_of_cluster_queue>					Cluster queue name"
				echo "		--scheduler=<name_of_cluster_scheduler>				Cluster scheduler program: e.g. LSF or PBS"
				echo "" 
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
 				echo "		--overwrite=<clean_prior_run>					Delete prior QC run"
 				echo "		--templatefolder=<path_for_the_template_folder>			Specify the output path name of the template folder (default: $TOOLS/MNAP/general/templates)"
				echo "		--outpath=<path_for_output_file>				Specify the output path name of the QC folder"
				echo "		--dwipath=<path_for_dwi_data>					Specify the input path for the DWI data [may differ across studies; e.g. Diffusion or Diffusion or Diffusion_DWI_dir74_AP_b1000b2500]"
				echo "		--dwidata=<file_name_for_dwi_data>				Specify the file name for DWI data [may differ across studies; e.g. data or DWI_dir74_AP_b1000b2500_data]"
				echo "		--dwilegacy=<dwi_data_processed_via_legacy_pipeline>		Specify is DWI data was processed via legacy pipelines [e.g. YES or NO]"
				echo "		--bolddata=<file_names_for_bold_data>				Specify the file names for BOLD data separated by comma [may differ across studies; e.g. 1, 2, 3 or BOLD_1 or rfMRI_REST1_LR,rfMRI_REST2_LR]"
				echo "		--boldsuffix=<file_name_for_bold_data>				Specify the file name for BOLD data [may differ across studies; e.g. Atlas or MSMAll]"
				echo "		--skipframes=<number_of_initial_frames_to_discard_for_bold_qc>				Specify the number of initial frames you wish to exclude from the BOLD QC calculation"
				echo ""
				echo ""
				echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='100206,100207' \ "
				echo "--outpath='/gpfs/project/fas/n3/Studies/Connectome/subjects/QC/T1w' \ "
				echo "--templatefolder='$TOOLS/MNAP/general/templates' \ "
				echo "--modality='T1w'"
				echo "--overwrite='no' \ "
				echo "--runmethod='1'"
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='100206,100207' \ "
				echo "--outpath='/gpfs/project/fas/n3/Studies/Connectome/subjects/QC/T1w' \ "
				echo "--templatefolder='$TOOLS/MNAP/general/templates' \ "
				echo "--modality='T1w'"
				echo "--overwrite='no' \ "
				echo "--runmethod='2' \ "
				echo "--queue='anticevic' \ "
				echo "--scheduler='lsf' "
				echo "" 			
				echo "-- Example with interactive terminal:"
				echo ""
				echo "AP qcpreproc /gpfs/project/fas/n3/Studies/Connectome/subjects '100206' "
				echo ""
				echo ""
				echo "-- Complete examples for each supported modality:"
				echo ""
				echo ""
				echo "# -- T1 QC"
				echo "AP --path='/gpfs/project/fas/n3/Studies/NAPLS3/subjects_organized' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='01_S0301_00_2015-02-23,01_S0301_00_2015-02-24' \ "
				echo "--outpath='/gpfs/project/fas/n3/Studies/NAPLS3/subjects_organized/QC/T1w' \ "
				echo "--templatefolder='${TOOLS}/MNAP/general/templates' \ "
				echo "--modality='T1w' \ "
				echo "--overwrite='yes' \ "
				echo "--runmethod='2' \ "
				echo "--queue='anticevic' \ "
				echo "--scheduler='lsf' "
				echo ""
				echo "# -- T2 QC"
				echo "AP --path='/gpfs/project/fas/n3/Studies/NAPLS3/subjects_organized' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='01_S0301_00_2015-02-23,01_S0301_00_2015-02-24' \ "
				echo "--outpath='/gpfs/project/fas/n3/Studies/NAPLS3/subjects_organized/QC/T2w' \ "
				echo "--templatefolder='${TOOLS}/MNAP/general/templates' \ "
				echo "--modality='T2w' \ "
				echo "--overwrite='yes' \ "
				echo "--runmethod='2' \ "
				echo "--queue='anticevic' \ "
				echo "--scheduler='lsf' "
				echo ""
				echo "# -- Myelin QC"
				echo "AP --path='/gpfs/project/fas/n3/Studies/NAPLS3/subjects_organized' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='01_S0301_00_2015-02-23,01_S0301_00_2015-02-24' \ "
				echo "--outpath='/gpfs/project/fas/n3/Studies/NAPLS3/subjects_organized/QC/myelin' \ "
				echo "--templatefolder='${TOOLS}/MNAP/general/templates' \ "
				echo "--modality='myelin' \ "
				echo "--overwrite='yes' \ "
				echo "--runmethod='2' \ "
				echo "--queue='anticevic' \ "
				echo "--scheduler='lsf' "
				echo ""
				echo "# -- DWI QC "
				echo "AP --path='/gpfs/project/fas/n3/Studies/NAPLS3/subjects_organized' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='01_S0301_00_2015-02-23,01_S0301_00_2015-02-24' \ "
				echo "--templatefolder='${TOOLS}/MNAP/general/templates' \ "
				echo "--modality='DWI' \ "
				echo "--outpath='/gpfs/project/fas/n3/Studies/NAPLS3/subjects_organized/QC/DWI_1k25k' \ "
				echo "--dwilegacy='yes' \ "
				echo "--dwidata='DWI_dir74_AP_b1000b2500_data_brain' \ "
				echo "--dwipath='Diffusion_DWI_dir74_AP_b1000b2500' \ "
				echo "--overwrite='yes' \ "
				echo "--runmethod='2' \ "
				echo "--queue='anticevic' \ "
				echo "--scheduler='lsf' "
				echo ""
				echo "# -- BOLD QC"
				echo "AP --path='/gpfs/project/fas/n3/Studies/NAPLS3/subjects_organized' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='01_S0301_00_2015-02-23,01_S0301_00_2015-02-24' \ "
				echo "--outpath='/gpfs/project/fas/n3/Studies/NAPLS3/subjects_organized/QC/BOLD' \ "
				echo "--templatefolder='${TOOLS}/MNAP/general/templates' \ "
				echo "--modality='BOLD' \ "
				echo "--bolddata='1' \ "
				echo "--boldsuffix='Atlas' \ "
				echo "--overwrite='yes' \ "
				echo "--runmethod='2' \ "
				echo "--queue='anticevic' \ "
				echo "--scheduler='lsf' "
				echo ""
				echo ""
}

# ===============================================================================================================================
# ================================ SOURCE REPOS, SETUP LOG & PARSE COMMAND LINE INPUTS ACROSS FUNCTIONS =========================
# ===============================================================================================================================

# ------------------------------------------------------------------------------
#  Set exit if error is reported (turn on for debugging)
# ------------------------------------------------------------------------------

# Setup this script such that if any command exits with a non-zero value, the 
# script itself exits and does not attempt any further processing.
#set -e

# ------------------------------------------------------------------------------
#  Source relevant repositories
# ------------------------------------------------------------------------------

	#if [ -f "$TOOLS/hcpsetup.sh" ]; then
	#	. "$TOOLS/hcpsetup.sh" &> /dev/null
	#else
	#	echo "ERROR: Environment script is missing. Check your user profile paths!"
	#fi
# ------------------------------------------------------------------------------
#  Load relevant libraries for logging and parsing options
# ------------------------------------------------------------------------------

source $HCPPIPEDIR/global/scripts/log.shlib  # Logging related functions
source $HCPPIPEDIR/global/scripts/opts.shlib # Command line option functions

# ------------------------------------------------------------------------------
#  Establish tool name for logging
# ------------------------------------------------------------------------------

log_SetToolName "AnalysisPipeline.sh"

# ------------------------------------------------------------------------------
#  Load Core Functions
# ------------------------------------------------------------------------------

#
# Description:
# 
#   parses the input command line for a specified command line option
#
# Input:
# 
#   The first parameter is the command line option to look for.
#   The remaining parameters are the full list of command line arguments
#

opts_GetOpt() {
    sopt="$1"
    shift 1
    for fn in "$@" ; do
    if [ `echo $fn | grep -- "^${sopt}=" | wc -w` -gt 0 ] ; then
        echo $fn | sed "s/^${sopt}=//"
        return 0
    fi
    done
}

#
# -- DESCRIPTION: 
#
#   checks command line arguments for "--help" indicating that 
#   help has been requested
#
   
opts_CheckForHelpRequest() {
    for fn in "$@" ; do
        if [ "$fn" = "--help" ]; then
            return 0
        fi
    done
    return 1
}

#
# -- DESCRIPTION: 
#
#   Generates a timestamp for the log exec call
#

timestamp() {
 
   echo "AP.$1.`date "+%Y.%m.%d.%H.%M.%S"`.txt"
}

#
# -- DESCRIPTION: 
#
#   Checks for version
#

show_version() {
 
 	APVer=`cat $TOOLS/MNAP/general/VERSION`
 	echo ""
	reho "Multimodal Neuroimaging Analysis Pipeline (MNAP) Version: v$APVer"
}

# opts_ShowVersionIfRequested "$@"

# ------------------------------------------------------------------------------
#  Parse Command Line Options
# ------------------------------------------------------------------------------

# -- Check if general help requested in three redundant ways (AP, AP --help or AP help)

if [ "$1" == "-version" ] || [ "$1" == "version" ] || [ "$1" == "--version" ] || [ "$1" == "--v" ] || [ "$1" == "-v" ]; then
	show_version
	echo ""
	exit 0
fi

if opts_CheckForHelpRequest $@; then
    show_version
    show_usage
    exit 0
fi

if [ -z "$1" ]; then
    show_version
    show_usage
    exit 0

fi

if [ "$1" == "help" ]; then
    show_version
	show_usage
	exit 0
fi

# ------------------------------------------------------------------------------
#  gmri function loop outside local functions to bypass checking
# ------------------------------------------------------------------------------

# -- Get list of all supported gmri functions
gmrifunctions=`gmri -available`

# -- Check if command-line input matches any of the gmri functions
if [ -z "${gmrifunctions##*$1*}" ]; then

	# -- If yes then set the gmri function variable
	GmriFunctionToRun="$1"
	GmriFunctionToRunEcho=`echo ${GmriFunctionToRun} | cut -c 2-`
	
	# -- Print message that command is running via AP wrapper
	echo ""
	cyaneho "Running gmri function $GmriFunctionToRunEcho via AP wrapper"
  	cyaneho "----------------------------------------------------------------------------"
	
	# -- check for input with question mark
	if [[ "$GmriFunctionToRun" =~ .*?.* ]] && [ -z "$2" ]; then 
		# Set UsageInput variable to pass and remove question mark
		UsageInput=`echo ${GmriFunctionToRun} | cut -c 2-`
	  	# If no other input is provided print help
		show_usage_gmri
		exit 0
	else
	# -- check for input with flag
	if [[ "$GmriFunctionToRun" =~ .*-.* ]] && [ -z "$2" ]; then 
		# Set UsageInput variable to pass and remove flag	
		UsageInput=`echo ${GmriFunctionToRun} | cut -c 2-`
	  	# If no other input is provided print help
		show_usage_gmri
		exit 0
    else
    	# -- Otherwise pass the function with all inputs from the command line
    	gmriinput="$@"
		gmri_function
		exit 0
	fi
	fi		
fi

# ------------------------------------------------------------------------------
#  LSF scheduler engine -- IN PROGRESS
# ------------------------------------------------------------------------------

schedulerfunction() {

echo "Scheduler testing..."

#elif options['scheduler'] == 'LSF':

        # ---- setup options to pass to each job

        #nopt = []
        #for (k, v) in args.iteritems():
        #    if k not in ['LSF_environ', 'LSF_folder', 'LSF_options', 'scheduler', 'nprocess']:
         #       nopt.append((k, v))

        #nopt.append(('scheduler', 'local'))
        #nopt.append(('nprocess', '0'))

        # ---- open log

        #flog = open(logname + '.log', "w")
        #print >> flog, "\n\n============================= LOG ================================\n"

        # ---- parse options string

        #lsfo = dict([e.strip().split("=") for e in options['LSF_options'].split(",")])

        # ---- run jobs

        #if options['jobname'] == "":
         #   options['jobname'] = "gmri"

        #c = 0
        #while subjects:

         #   c += 1

            # ---- construct the bsub input
            # -M mem_limit in kb
            # -n min[, max] ... minimal and maximal number of processors to use
            # -o output file ... %J adds job id
            # -P project name
            # -q queue_name   ("shared" for 24 h more on "long")
            # -R "res_req" ... resource requirement string
            #              ... select[selection_string] order[order_string] rusage[usage_string [, usage_string][|| usage_string] ...] span[span_string] same[same_string] cu[cu_string]] affinity[affinity_string]
            # -R 'span[hosts=1]' ... so that all slots are on the same machine
            # -W hour:minute  runtime limit
            # -We hour:minute  estimated runtime
            #  bsub '-M <P>' option specifies the memory limit for each process, while '-R "rusage[mem=<N>]"' specifies the memory to reserve for this job on each node. ... in MB - 5GB default

            #cstr  = "#BSUB -o %s-%s_#%02d_%%J\n" % (options['jobname'], command, c)
            #cstr += "#BSUB -q %s\n" % (lsfo['queue'])
            #cstr += "#BSUB -R 'span[hosts=1] rusage[mem=%s]'\n" % (lsfo['mem'])
            #cstr += "#BSUB -W %s\n" % (lsfo['walltime'])
            #cstr += "#BSUB -n %s\n" % (lsfo['cores'])
            #if len(options['jobname']) > 0:
             #   cstr += "#BSUB -P %s-%s\n" % (options['jobname'], command)
             #   cstr += "#BSUB -J %s-%s_%d\n" % (options['jobname'], command, c)


            #if options['LSF_environ'] != '':
             #   cstr += "\n# --- Setting up environment\n\n"
             #   cstr += file(options['LSF_environ']).read()

            #if options['LSF_folder'] != '':
             #   cstr += "\n# --- changing to the right folder\n\n"
             #   cstr += "cd %s" % (options['LSF_folder'])

            # ---- construct the gmri command

            #cstr += "\ngmri " + command

            #for (k, v) in nopt:
             #   if k not in ['subjid', 'scheduler', 'queue']:
             #       cstr += ' --%s="%s"' % (k, v)

 			#slist = []
            #[slist.append(subjects.pop(0)['subject']) for e in range(cores) if subjects]   # might need to change to id

            #cstr += ' --subjid="%s"' % ("|".join(slist))
            #cstr += ' --scheduler="local"'
            #cstr += '\n'

            # ---- pass the command string to qsub

            #print "\n==============> submitting %s_#%02d\n" % ("-".join(args), c)
            #print cstr

            #print >> flog, "\n==============> submitting %s_#%02d\n" % ("-".join(args), c)

            #lsf = subprocess.Popen("bsub", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
            #lsf.stdin.write(cstr)
            #lsf.stdin.close()

            # ---- storing results

            #result = lsf.stdout.read()

            #print "\n----------"
            #print result

            #print >> flog, "\n----------"
            #print >> flog, result

            #time.sleep(options['LSF_sleep'])

        #print "\n\n============================= DONE ================================\n"
        #print >> flog, "\n\n============================= DONE ================================\n"
        #flog.close()

}

# ------------------------------------------------------------------------------
#  Check if specific function help requested
# ------------------------------------------------------------------------------
	
	# -- get all the functions from the usage calls
	unset UsageName
	unset APFunctions
	UsageName=`more ${TOOLS}/MNAP/general/AnalysisPipeline.sh | grep show_usage_${1}`
	APFunctions=`more ${TOOLS}/MNAP/general/AnalysisPipeline.sh | grep "() {" | grep -v "usage" | grep -v "eho" | grep -v "opts_" | sed "s/() {//g" | sed ':a;N;$!ba;s/\n/ /g'`

	# -- check for input with double flags
	if [[ "$1" =~ .*--.* ]] && [ -z "$2" ]; then 
		Usage="$1"
		UsageInput=`echo ${Usage:2}`
			# -- check if input part of function list
			if [[ "$APFunctions" != *${UsageInput}* ]]; then
				echo ""
				reho "Function $UsageInput does not exist! Refer to general usage below: "
				echo ""
				show_version
				show_usage
				exit 0
			else	
				show_version
    			show_usage_"$UsageInput"
    		fi
    	exit 0
	fi
		
	# -- check for input with single flags
	if [[ "$1" =~ .*-.* ]] && [ -z "$2" ]; then 
		Usage="$1"
		UsageInput=`echo ${Usage:1}`
			# -- check if input part of function list
			if [[ "$APFunctions" != *${UsageInput}* ]]; then
				echo ""
				reho "Function $UsageInput does not exist! Refer to general usage below: "
				echo ""
				show_version
				show_usage
				exit 0
			else	
				show_version
    			show_usage_"$UsageInput"
    		fi
    	exit 0
	fi
	
	# -- check for input with question mark
    HelpInputUsage="$1"	
    if [[ ${HelpInputUsage:0:1} == "?" ]] && [ -z "$2" ]; then 
    	Usage="$1"
		UsageInput=`echo ${Usage} | cut -c 2-`
			# -- check if input part of function list
			if [[ "$APFunctions" != *${UsageInput}* ]]; then
				echo ""
				reho "Function $UsageInput does not exist! Refer to general usage below: "
				echo ""
				show_version
				show_usage
				exit 0
			else	
			    show_version
    			show_usage_"$UsageInput"
    		fi
    	exit 0
	fi
			
	# -- check for input with no flags
	if [ -z "$2" ]; then
			UsageInput="$1"
			# -- check if input part of function list
			if [[ "$APFunctions" != *${UsageInput}* ]]; then
				echo ""
				reho "Function $UsageInput does not exist! Refer to general usage below: "
				echo ""
				show_version
				show_usage
				exit 0
			else	
				show_version
    			show_usage_"$UsageInput"
    		fi
    	exit 0
	fi
		
# ------------------------------------------------------------------------------
#  Setup log calls
# ------------------------------------------------------------------------------

log_Msg "Platform Information Follows: " 
uname -a

log_Msg "Parsing Command Line Options: "

# ------------------------------------------------------------------------------
#  Check if running script interactively or using flag arguments
# ------------------------------------------------------------------------------

# -- Clear variables for new run

unset FunctionToRun
unset subjects
unset FunctionToRunInt
unset StudyFolder
unset CASES
unset Overwrite
unset Scheduler
unset QUEUE
unset NetID
unset ClusterName
unset setflag
unset doubleflag
unset singleflag

# -- Check for generic flags

# -- First check if single or double flags are set
doubleflag=`echo $1 | cut -c1-2`
singleflag=`echo $1 | cut -c1`

if [ "$doubleflag" == "--" ]; then

	setflag="$doubleflag"

else

	if [ "$singleflag" == "-" ]; then

		setflag="$singleflag"
		
	fi	

fi

# -- Next check if any flags are set
if [[ "$setflag" =~ .*-.* ]]; then

	echo ""
	reho "-----------------------------------------------------"
	reho "------- Running pipeline with flagged inputs --------"
	reho "-----------------------------------------------------"
	echo ""
	
	# ------------------------------------------------------------------------------
	#  List of command line options across all functions
	# ------------------------------------------------------------------------------
	
	# First get function / command input (to harmonize input with gmri)
	FunctionInput=`opts_GetOpt "${setflag}function" "$@"` # function to execute
	CommamndInput=`opts_GetOpt "${setflag}command" "$@"` # function to execute
	
	# If input name uses 'command' instead of function set that to $FunctionToRun
	if [[ -z "$FunctionInput" ]]; then
		FunctionToRun="$CommamndInput"
	else
		FunctionToRun="$FunctionInput"		
	fi
	
	# -- general input flags
	StudyFolder=`opts_GetOpt "${setflag}path" $@` # local folder to work on
	CASES=`opts_GetOpt "${setflag}subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
	QUEUE=`opts_GetOpt "${setflag}queue" $@` # <name_of_cluster_queue>			Cluster queue name	
	PRINTCOM=`opts_GetOpt "${setflag}printcom" $@` #Option for printing the entire command
	Scheduler=`opts_GetOpt "${setflag}scheduler" $@` #Specify the type of scheduler to use 
	Overwrite=`opts_GetOpt "${setflag}overwrite" $@` #Clean prior run and starr fresh [yes/no]
	RunMethod=`opts_GetOpt "${setflag}runmethod" $@` # Specifies whether to run on the cluster or on the local node
	FreeSurferHome=`opts_GetOpt "${setflag}hcp_freesurfer_home" $@` # Specifies homefolder for FreeSurfer binary to use
	APVersion=`opts_GetOpt "${setflag}version" $@` # Specifies homefolder for FreeSurfer binary to use
	
	# -- create lists input flags
	ListGenerate=`opts_GetOpt "${setflag}listtocreate" $@` # Which lists to generate
	Append=`opts_GetOpt "${setflag}append" $@` # Append the list
	ListName=`opts_GetOpt "${setflag}listname" $@` # Name of the list
	ParameterFile=`opts_GetOpt "${setflag}parameterfile" $@` # Use parameter file header
	ListFunction=`opts_GetOpt "${setflag}listfunction" $@` # Which function to use to generate the list
	BOLDS=`opts_GetOpt "${setflag}bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'` # --bolddata=<file_names_for_bold_data>				Specify the file names for BOLD data separated by comma [may differ across studies; e.g. 1, 2, 3 or BOLD_1 or rfMRI_REST1_LR,rfMRI_REST2_LR]
	ParcellationFile=`opts_GetOpt "${setflag}parcellationfile" $@` # --parcellationfile=<file_for_parcellation>		Specify the absolute path of the file you want to use for parcellation (e.g. {$TOOLS}/MNAP/general/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)
	FileType=`opts_GetOpt "${setflag}filetype" $@` # --filetype=<file_extension>
	BoldSuffix=`opts_GetOpt "${setflag}boldsuffix" $@` # --boldsuffix=<bold_suffix>
	SubjectHCPFile=`opts_GetOpt "${setflag}subjecthcpfile" $@` # Use subject HCP File for appending the parameter list

	# -- hpcsync input flags
	NetID=`opts_GetOpt "${setflag}netid" $@` # NetID for cluster rsync command
	HCPStudyFolder=`opts_GetOpt "${setflag}clusterpath" $@` # cluster study folder for cluster rsync command
	Direction=`opts_GetOpt "${setflag}dir" $@` # direction of rsync command (1 to cluster; 2 from cluster)
	ClusterName=`opts_GetOpt "${setflag}cluster" $@` # cluster address [e.g. louise.yale.edu)

	# -- hcpdlegacy input flags
	EchoSpacing=`opts_GetOpt "${setflag}echospacing" $@` # <echo_spacing_value>		EPI Echo Spacing for data [in msec]; e.g. 0.69
	PEdir=`opts_GetOpt "${setflag}PEdir" $@` # <phase_encoding_direction>		Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior
	TE=`opts_GetOpt "${setflag}TE" $@` # <delta_te_value_for_fieldmap>		This is the echo time difference of the fieldmap sequence - find this out form the operator - defaults are *usually* 2.46ms on SIEMENS
	UnwarpDir=`opts_GetOpt "${setflag}unwarpdir" $@` # <epi_phase_unwarping_direction>	Direction for EPI image unwarping; e.g. x or x- for LR/RL, y or y- for AP/PA; may been to try out both -/+ combinations
	DiffDataSuffix=`opts_GetOpt "${setflag}diffdatasuffix" $@` # <diffusion_data_name>		Name of the DWI image; e.g. if the data is called <SubjectID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR
	
	# -- boldparcellation input flags
	InputFile=`opts_GetOpt "${setflag}inputfile" $@` # --inputfile=<file_to_compute_parcellation_on>		Specify the name of the file you want to use for parcellation (e.g. bold1_Atlas_MSMAll_hp2000_clean)
	InputPath=`opts_GetOpt "${setflag}inputpath" $@` # --inputpath=<path_for_input_file>			Specify path of the file you want to use for parcellation relative to the master study folder and subject directory (e.g. /images/functional/)
	InputDataType=`opts_GetOpt "${setflag}inputdatatype" $@` # --inputdatatype=<type_of_dense_data_for_input_file>	Specify the type of data for the input file (e.g. dscalar or dtseries)
	OutPath=`opts_GetOpt "${setflag}outpath" $@` # --outpath=<path_for_output_file>			Specify the output path name of the pconn file relative to the master study folder (e.g. /images/functional/)
	OutName=`opts_GetOpt "${setflag}outname" $@` # --outname=<name_of_output_pconn_file>			Specify the suffix output name of the pconn file
	ExtractData=`opts_GetOpt "${setflag}extractdata" $@` # --extractdata=<save_out_the_data_as_as_csv>				Specify if you want to save out the matrix as a CSV file
	ComputePConn=`opts_GetOpt "${setflag}computepconn" $@` # --computepconn=<specify_parcellated_connectivity_calculation>		Specify if a parcellated connectivity file should be computed (pconn). This is done using covariance and correlation (e.g. yes; default is set to no).
	UseWeights=`opts_GetOpt "${setflag}useweights" $@` # --useweights=<clean_prior_run>						If computing a  parcellated connectivity file you can specify which frames to omit (e.g. yes' or no; default is set to no) 
	WeightsFile=`opts_GetOpt "${setflag}useweights" $@` # --weightsfile=<location_and_name_of_weights_file>			Specify the location of the weights file relative to the master study folder (e.g. /images/functional/movement/bold1.use)
	ParcellationFile=`opts_GetOpt "${setflag}parcellationfile" $@` # --parcellationfile=<file_for_parcellation>		Specify the absolute path of the file you want to use for parcellation (e.g. {$TOOLS}/MNAP/general/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)

	# -- dwidenseparcellation input flags
	MatrixVersion=`opts_GetOpt "${setflag}matrixversion" $@` # --matrixversion=<matrix_version_value>		matrix solution verion to run parcellation on; e.g. 1 or 3
	ParcellationFile=`opts_GetOpt "${setflag}parcellationfile" $@` # --parcellationfile=<file_for_parcellation>		Specify the absolute path of the file you want to use for parcellation (e.g. {$TOOLS}/MNAP/general/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)
	OutName=`opts_GetOpt "${setflag}outname" $@` # --outname=<name_of_output_pconn_file>	Specify the suffix output name of the pconn file
	
	# -- dwiseedtractography input flags
	SeedFile=`opts_GetOpt "${setflag}seedfile" $@` # --seedfile=<structure_for_seeding>	Specify the absolute path of the seed file you want to use as a seed for dconn reduction
	
	# -- fslbedpostxgpu input flags
	Fibers=`opts_GetOpt "${setflag}fibers" $@`  # <number_of_fibers>		Number of fibres per voxel, default 3
	Model=`opts_GetOpt "${setflag}model" $@`    # <deconvolution_model>		Deconvolution model. 1: with sticks, 2: with sticks with a range of diffusivities (default), 3: with zeppelins
	Burnin=`opts_GetOpt "${setflag}burnin" $@`  # <burnin_period_value>		Burnin period, default 1000
	Jumps=`opts_GetOpt "${setflag}jumps" $@`    # <number_of_jumps>		Number of jumps, default 1250
	
	# -- probtrackxgpudense input flags
	MatrixOne=`opts_GetOpt "${setflag}omatrix1" $@`  # <matrix1_model>		Specify if you wish to run matrix 1 model [yes or omit flag]
	MatrixThree=`opts_GetOpt "${setflag}omatrix3" $@`  # <matrix3_model>		Specify if you wish to run matrix 3 model [yes or omit flag]
	NsamplesMatrixOne=`opts_GetOpt "${setflag}nsamplesmatrix1" $@`  # <Number_of_Samples_for_Matrix1>		Number of samples - default=5000
	NsamplesMatrixThree=`opts_GetOpt "${setflag}nsamplesmatrix3" $@`  # <Number_of_Samples_for_Matrix3>>		Number of samples - default=5000
	
	# -- awshcpsync input flags
	Modality=`opts_GetOpt "${setflag}modality" $@` # <modality_to_sync>			Which modality or folder do you want to sync [e.g. MEG, MNINonLinear, T1w]"
	Awsuri=`opts_GetOpt "${setflag}awsuri" $@`	 # <aws_uri_location>			Enter the AWS URI [e.g. /hcp-openaccess/HCP_900]"
		
	# -- qcpreproc input flags
	OutPath=`opts_GetOpt "${setflag}outpath" $@` # --outpath=<path_for_output_file>			Specify the output path name of the QC folder
	TemplateFolder=`opts_GetOpt "${setflag}templatefolder" $@` # --templatefolder=<path_for_the_template_folder>			Specify the output path name of the template folder (default: "$TOOLS"/MNAP/general/templates)
	Modality=`opts_GetOpt "${setflag}modality" $@` # --modality=<input_modality_for_qc>			Specify the modality to perform QC on (Supported: T1w, T2w, myelin, BOLD, DWI)
	DWIPath=`opts_GetOpt "${setflag}dwipath" $@` # --dwipath=<path_for_dwi_data>				Specify the input path for the DWI data (may differ across studies)
	DWIData=`opts_GetOpt "${setflag}dwidata" $@` # --dwidata=<file_name_for_dwi_data>				Specify the file name for DWI data (may differ across studies)
	DWILegacy=`opts_GetOpt "${setflag}dwilegacy" $@` # --dwilegacy=<dwi_data_processed_via_legacy_pipeline>				Specify is DWI data was processed via legacy pipelines [e.g. YES; default NO]
	BOLDS=`opts_GetOpt "${setflag}bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'` # --bolddata=<file_names_for_bold_data>				Specify the file names for BOLD data separated by comma [may differ across studies; e.g. 1, 2, 3 or BOLD_1 or rfMRI_REST1_LR,rfMRI_REST2_LR]
	BOLDSuffix=`opts_GetOpt "${setflag}boldsuffix" $@` # --boldsuffix=<file_name_for_bold_data>				Specify the file name for BOLD data [may differ across studies; e.g. Atlas or MSMAll]
	SkipFrames=`opts_GetOpt "${setflag}skipframes" $@` # --skipframes=<number_of_initial_frames_to_discard_for_bold_qc>				Specify the number of initial frames you wish to exclude from the BOLD QC calculation
	
	# -- Check if subject input is a parameter file instead of list of cases
	if [[ ${CASES} == *.txt ]]; then
		SubjectParamFile="$CASES"
		echo ""
		echo "Using $SubjectParamFile for input."
		echo ""
		CASES=`more ${SubjectParamFile} | grep "id:"| cut -d " " -f 2`
	fi

else

	# -- If no flags were found the pipeline defaults to 'interactive' mode. 
	# -- Not all functions are supported in interactive mode
	echo ""
	reho "--------------------------------------------"
	reho "--- Running pipeline in interactive mode ---"
	reho "--------------------------------------------"
	echo ""
	#
	# -- Read core interactive command line inputs as default positional variables (i.e. function, path & cases)
	#
	FunctionToRunInt="$1"
	StudyFolder="$2" 
	CASESInput="$3"
	
	# -- Make list of subjects compatible with either space- or comma-delimited input:
	CASES=`echo ${CASESInput} | sed 's/,/ /g'`

fi	

# ===============================================================================================================================
# ================================ EXECUTE SELECTED FUNCTION AND LOOP THROUGH ALL THE CASES =====================================
# ===============================================================================================================================

# ------------------------------------------------------------------------------
#  dicomsort function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "dicomsort" ]; then

		# Check all the user-defined parameters: 1. Cluster, 2. QUEUE.
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$RunMethod" ]; then reho "Error: Run Method option [1=Run Locally on Node; 2=Send to Cluster] missing"; exit 1; fi
		if [ -z "$Overwrite" ]; then Overwrite="no"; fi
		
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler option missing for fsl_sub command [e.g. lsf or torque]"; exit 1; fi
		fi
		
	for CASE in $CASES; do
  		"$FunctionToRun" "$CASE"
  	done
fi

if [ "$FunctionToRunInt" == "dicomsort" ]; then
	
	Cluster=1
	echo "Re-run existing run [yes, no]:"
	if read answer; then Overwrite=$answer; fi
	echo ""
	
	for CASE in $CASES; do
  		"$FunctionToRunInt" "$CASE"
  	done  	
fi

# ------------------------------------------------------------------------------
#  dicom2nii function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "dicom2nii" ]; then
		
	for CASE in $CASES
	do
  		"$FunctionToRun" "$CASE"
  	done
fi

if [ "$FunctionToRunInt" == "dicom2nii" ]; then
	for CASE in $CASES
	do
  		"$FunctionToRunInt" "$CASE"
  	done
fi

# ------------------------------------------------------------------------------
#  Visual QC Images function loop - qcpreproc - wb_command based
# ------------------------------------------------------------------------------


if [ "$FunctionToRun" == "qcpreproc" ]; then
	
		# Check all the user-defined parameters: 1. Overwrite, 2. OutPath, 3. TemplateFolder, 4. Cluster, 5. QUEUE. 6. Modality. 7. SkipFrames
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$Modality" ]; then reho "Error:  Modality to perform QC on missing [Supported: T1w, T2w, myelin, BOLD, DWI]"; exit 1; fi
		if [ -z "$RunMethod" ]; then reho "Error: Run Method option [1=Run Locally on Node; 2=Send to Cluster] missing"; exit 1; fi
		
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler option missing for fsl_sub command [e.g. lsf or torque]"; exit 1; fi
		fi
		
		if [ -z "$TemplateFolder" ]; then TemplateFolder="${TOOLS}/MNAP/general/templates"; echo "Template folder path value not explicitly specified. Using default: ${TemplateFolder}"; fi
		if [ -z "$OutPath" ]; then OutPath="${StudyFolder}/QC/${Modality}"; echo "Output folder path value not explicitly specified. Using default: ${OutPath}"; fi

		if [ "$Modality" = "DWI" ]; then
			if [ -z "$DWIPath" ]; then DWIPath="Diffusion"; echo "DWI input path not explicitly specified. Using default: ${DWIPath}"; fi
			if [ -z "$DWIData" ]; then DWIData="data"; echo "DWI data name not explicitly specified. Using default: ${DWIData}"; fi
			if [ -z "$DWILegacy" ]; then DWILegacy="NO"; echo "DWI legacy not specified. Using default: ${TemplateFolder}"; fi
		fi

		if [ "$Modality" = "BOLD" ]; then
			for BOLD in $BOLDS; do rm -f ${OutPath}/TSNR_Report_${BOLD}*.txt &> /dev/null; done
			if [ -z "$BOLDS" ]; then reho "Error: BOLD input names missing"; exit 1; fi
			if [ -z "$BOLDSuffix" ]; then BOLDSuffix=""; echo "BOLD suffix not specified. Assuming no suffix"; fi
			if [ -z "$SkipFrames" ]; then SkipFrames="0"; fi
		fi

		echo ""
		echo "Running qcpreproc with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Study Folder: ${StudyFolder}"
		echo "Subjects: ${CASES}"
		echo "QC Modality: ${Modality}"
		echo "QC Output Path: ${OutPath}"
		echo "QC Scene Template: ${TemplateFolder}"
		echo "Overwrite prior run: ${Overwrite}"
		if [ "$Modality" = "DWI" ]; then
		echo "DWI input path: ${DWIPath}"
		echo "DWI input name: ${DWIData}"
		echo "DWI legacy processing: ${DWILegacy}"
		fi
		if [ "$Modality" = "BOLD" ]; then
		echo "BOLD data input: ${BOLDS}"
		echo "BOLD suffix: ${BOLDSuffix}"
		echo "Skip Initial Frames: ${SkipFrames}"
		fi
		echo "--------------------------------------------------------------"
		
		for CASE in $CASES
		do
  			"$FunctionToRun" "$CASE"
  		done
fi

if [ "$FunctionToRunInt" == "qcpreproc" ]; then

	echo "Running qcpreproc processing interactively. First enter the necessary parameters."
	# Request all the user-defined parameters: 1. Overwrite, 2. OutPath, 3. TemplateFolder, 4. Cluster, 5. QUEUE. 6. Modality
	echo ""
	echo "Overwrite existing run [yes, no]:"
	if read answer; then Overwrite=$answer; fi
	echo ""
	echo "Enter modality to perform QC on [Supported: T1w, T2w, myelin, BOLD, DWI]:"
	if read answer; then Modality=$answer; fi
	echo ""
	
	#echo "Enter Output QC folder path [uses defaults if nothing specified]:"
	#if read answer; then OutPath=$answer; else echo "Using default: ${OutPath}"; fi
	#echo ""
	#echo "Enter template scene folder path value [uses defaults if nothing specified]:"
	#if read answer; then TemplateFolder=$answer; else echo "Using default: ${TemplateFolder}"; fi
	#echo ""
	
	# Set defaults for templates and outputs
	TemplateFolder="${TOOLS}/MNAP/general/templates"
	OutPath="${StudyFolder}/QC/${Modality}" 
	
	echo "-- Run locally [1] or run on cluster [2]"
	if read answer; then Cluster=$answer; fi
	echo ""
	if [ "$Cluster" == "2" ]; then
		echo "-- Enter queue name - always submit this job to a GPU-enabled queue [e.g. anticevic-gpu]"
		if read answer; then QUEUE=$answer; fi
		echo ""
	fi
	
	if [ "$Modality" = "DWI" ]; then
			echo "-- Specify the input path for the DWI data [e.g. Diffusion]"
			if read answer; then DWIPath=$answer; fi
			echo "-- Specify the input name for the DWI data [e.g. data]"
			if read answer; then DWIData=$answer; fi
			echo "-- Specify if DWI data was processed via legacy pipelines [YES or NO]"
			if read answer; then DWILegacy=$answer; fi
	fi
	
	if [ "$Modality" = "BOLD" ]; then
			for BOLD in $BOLDS; do rm -f ${OutPath}/TSNR_Report_${BOLD}*.txt &> /dev/null; done
			echo "-- Specify the input name for the BOLD data [e.g. 1 or rfMRI_REST1_LR]"
			if read answer; then BOLDS=$answer; fi
			echo "-- Specify the suffix for the BOLD data [Atlas]"
			if read answer; then BOLDSuffix=$answer; fi
			echo "-- Specify the number of initial frames to skip for BOLD QC"
			if read answer; then SkipFrames=$answer; fi
	fi
	
		echo "Running qcpreproc with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Study Folder: ${StudyFolder}"
		echo "Subjects: ${CASES}"
		echo "QC Modality: ${Modality}"
		echo "QC Output Path: ${OutPath}"
		echo "QC Scene Template: ${TemplateFolder}"
		echo "Overwrite prior run: ${Overwrite}"
		if [ "$Modality" = "DWI" ]; then
		echo "DWI input path: ${DWIPath}"
		echo "DWI input name: ${DWIData}"
		echo "DWI legacy processing: ${DWILegacy}"
		fi
		if [ "$Modality" = "BOLD" ]; then
		echo "BOLD data input: ${BOLDS}"
		echo "BOLD suffix: ${BOLDSuffix}"
		echo "Skip Initial Frames: ${SkipFrames}"
		fi
		echo "--------------------------------------------------------------"
		
		for CASE in $CASES
			do
  			"$FunctionToRunInt" "$CASE"
  		done
fi

# ------------------------------------------------------------------------------
#  setuphcp function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "setuphcp" ]; then
	
		# Check all the user-defined parameters: 1. Cluster, 2. QUEUE.
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$RunMethod" ]; then reho "Error: Run Method option [1=Run Locally on Node; 2=Send to Cluster] missing"; exit 1; fi
		
		Cluster="$RunMethod"
		
		if [ "$Cluster" == "2" ]; then
				if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler option missing for fsl_sub command [e.g. lsf or torque]"; exit 1; fi
		fi
		
		echo "Makeing sure that and correct subjects_hcp.txt files is generated..."
				
			for CASE in $CASES
			do
				if [ -f "$StudyFolder"/"$CASE"/subject_hcp.txt ]; then 
  					"$FunctionToRun" "$CASE"
  				else	
  					echo "--> $StudyFolder/$CASE/subject_hcp.txt is missing - please setup the subject.txt files and re-run function."
  				fi
  			done
fi

if [ "$FunctionToRunInt" == "setuphcp" ]; then
			
			# Always run locally if command is interactive
			Cluster=1
			
			for CASE in $CASES
			do
				if [ -f "$StudyFolder"/"$CASE"/subject_hcp.txt ]; then 
  					"$FunctionToRunInt" "$CASE"
  				else	
  					echo "--> $StudyFolder/$CASE/subject_hcp.txt is missing - please setup the subject.txt files and re-run function."
  				fi
  			done
fi

# ------------------------------------------------------------------------------
#  hpcsync function loop
# ------------------------------------------------------------------------------


if [ "$FunctionToRun" == "hpcsync" ]; then

	echo "Syncing data between the local server and Yale HPC Clusters."
	echo ""
		for CASE in $CASES
			do
  			"$FunctionToRun" "$CASE"
  		done
fi

if [ "$FunctionToRunInt" == "hpcsync" ]; then
	echo "You are about to sync data between the local server and Yale HPC Clusters."
	echo "Note: Make sure your HPC ssh key is setup on your local NMDA account."
	echo "Enter exact HPC cluster address [e.g. louise.hpc.yale.edu or omega1.hpc.yale.edu]:"
		if read answer; then
			ClusterName=$answer
			echo "Enter your NetID..."
			if read answer; then
				NetID=$answer
				echo "Enter your HPC cluster folder where data are located... [e.g. /lustre/home/client/fas/anticevic/aa353/scratch/Anticevic.DP5/subjects]"
				if read answer; then
					HCPStudyFolder=$answer
					echo "Enter rsync direction [NMDA-->HPC: 1 or HPC-->NMDA: 2]"
					if read answer; then
					Direction=$answer
						for CASE in $CASES
							do
  							"$FunctionToRunInt" "$CASE"
  						done
  					fi
  				fi
  			fi
  		else
  			 echo "Something is wrong with your input. Refer to function usage."
		fi
fi


# ------------------------------------------------------------------------------
#  createlists function loop
# ------------------------------------------------------------------------------


if [ "$FunctionToRun" == "createlists" ]; then
		
		mkdir "$StudyFolder"/lists &> /dev/null

		# Check all the user-defined parameters: 1. Cluster, 2. QUEUE. 3. GROUP. 
		# 4. ListFunction 5. ListGenerate. 6. BOLDS 7. Append 8. ParameterFile
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$ListGenerate" ]; then reho "Error: Type of list to generate missing [preprocessing, analysis, snr]"; exit 1; fi
		# - Check optional parameters
		if [ -z "$Append" ]; then Append="no"; reho "Setting --append='no' by default"; fi
		
		# -- Omit scheduler commands here
		#if [ -z "$RunMethod" ]; then reho "Error: Run Method option [1=Run Locally on Node; 2=Send to Cluster] missing"; exit 1; fi
		#Cluster="$RunMethod"
		#if [ "$Cluster" == "2" ]; then
		#		if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
		#		if [ -z "$Scheduler" ]; then reho "Error: Scheduler option missing for fsl_sub command [e.g. lsf or torque]"; exit 1; fi
		#fi
		
		# --------------------------
		# --- preprocessing loop ---
		# --------------------------
		if [ "$ListGenerate" == "preprocessing" ]; then
		
			# -- Check of overwrite flag was set
			if [ "$Overwrite" == "yes" ]; then
				
				echo ""
				reho "===> Deleting prior processing lists"
  				echo ""
				rm "$StudyFolder"/lists/subjects.preprocessing."$ListName".param &> /dev/null
  			fi			
		
			if [ -z "$ListFunction" ]; then 
				reho "List function not set. Using default function."
				ListFunction="${TOOLS}/MNAP/general/functions/subjectsparamlist.sh"
				echo ""
				reho "$ListFunction"
				echo ""
			fi
			
			if [ -z "$ListName" ]; then reho "Name of preprocessing list for is missing."; exit 1; fi
			
			if [ -z "$ParameterFile" ]; then 
				echo ""
				echo "No parameter header file set - Using defaults: "
				ParameterFile="${TOOLS}/MNAP/general/functions/subjectparamlist_header_multiband.txt"
				echo "--> $ParameterFile"
				echo ""
			fi
			
			# - Check if skipping parameter file header
			if [ "$ParameterFile" != "no" ]; then
				# - Check if lists exists  
				if [ -s "$StudyFolder"/lists/subjects.preprocessing."$ListName".param ]; then
					# --> If ParameterFile was set and file exists then exit and report error
					echo ""
					reho "---------------------------------------------------------------------"
					reho "--> The file exists and you are trying to set the header again"
					reho "--> Check usage to append the file or overwrite it."
					reho "---------------------------------------------------------------------"
					echo ""
					exit 1
				else
					echo ""
					echo "-- Adding Parameter Header: "
					echo "--> ${ParameterFile}"
					cat ${ParameterFile} >> ${StudyFolder}/lists/subjects.preprocessing.${ListName}.param
				fi 
			fi	
  			  	
  			for CASE in $CASES; do
  				"$FunctionToRun" "$CASE"
  			done
	  			
  			echo ""
  			geho "-------------------------------------------------------------------------------------------"
  			geho "--> Check output:"
  			geho "  `ls ${StudyFolder}/lists/subjects.preprocessing.${ListName}.param `"
  			geho "-------------------------------------------------------------------------------------------"
  			echo ""
		fi
		
		# --------------------------
		# --- analysis loop --------
		# --------------------------
		if [ "$ListGenerate" == "analysis" ]; then		
		
			if [ -z "$ListFunction" ]; then 
			reho "List function not set. Using default function."
				ListFunction="${TOOLS}/MNAP/general/functions/analysislist.sh"
				echo ""
				reho "$ListFunction"
				echo ""
			fi
			
			if [ -z "$ListName" ]; then reho "Name of analysis list for is missing."; exit 1; fi
			if [ -z "$BOLDS" ]; then reho "List of BOLDs missing."; exit 1; fi

			# -- Check of overwrite flag was set
			if [ "$Overwrite" == "yes" ]; then
				echo ""
				reho "===> Deleting prior analysis lists"
  				echo ""
				rm "$StudyFolder"/lists/subjects.analysis."$ListName".*.list &> /dev/null
  			fi
  			
  			for CASE in $CASES; do
  				"$FunctionToRun" "$CASE"
  			done
		fi	
		
		# ----------------
		# --- snr loop ---
		# ----------------
		if [ "$ListGenerate" == "snr" ]; then		
		if [ -z "$BOLDS" ]; then reho "Error: BOLDs to generate the snr list for missing"; exit 1; fi
			
			# -- Check of overwrite flag was set
			if [ "$Overwrite" == "yes" ]; then
				
				echo ""
				reho "===> Deleting prior snr lists"
  				echo ""
  				cd "$StudyFolder"/QC/snr
				rm *subjects.snr.txt  &> /dev/null
  			
  			  	for CASE in $CASES; do
  						"$FunctionToRun" "$CASE"
  				done
			fi	
		fi				
fi			

if [ "$FunctionToRunInt" == "createlists" ]; then
	echo "Enter which type of list you want to run?"
	echo ""
	echo "	* preprocessing --> Subject parameter list with cases to preprocess"
  	echo "	* analysis --> List of cases to compute seed connectivity or GBC"
  	echo "	* SNR --> List of cases to compute signal-to-noise ratio"
  	echo ""
		if read answer; then
			
			ListGenerate=$answer
			
			if [ "$ListGenerate" == "analysis" ]; then
				echo "Enter name of analysis list script you want to use?"
				ListFunctions=`ls ${TOOLS}/MNAP/general/functions/analysislist*.sh`
				echo ""
				echo "Supported: "
				echo "$ListFunctions"
				echo ""
					if read answer; then
					ListFunction=$answer 
						echo "Enter name of group you want to generate a list for [e.g. scz, hcs, ocd... ]:"
							if read answer; then
							GROUP=$answer
								echo "Note: pre-existing lists will now be deleted..."
								rm "$StudyFolder"/subjects/lists/subjects.analysis."$GROUP".list &> /dev/null
								for CASE in $CASES
									do
  									"$FunctionToRunInt" "$CASE"
  								done
  							fi
  					fi
  			fi
  			
  			if [ "$ListGenerate" == "snr" ]; then
  				echo "Note: pre-existing snr lists will now be deleted..."
  				cd "$StudyFolder"/subjects/QC/snr
				rm *subjects.snr.txt  &> /dev/null
  				echo "Enter BOLD numbers you want to generate the SNR List for [e.g. 1 2 3]:"
				if read answer; then
				BOLDS=$answer 
  			  		for CASE in $CASES
						do
  						"$FunctionToRunInt" "$CASE"
  					done
  				fi
  			fi
  		
  			if [ "$ListGenerate" == "preprocessing" ]; then
				echo "Now enter name of preprocessing list script you want to use?"
				ListFunctions=`ls ${TOOLS}/MNAP/general/functions/*paramlist*.sh`
				echo ""
				echo "Supported: "
				echo "$ListFunctions"
				echo ""
					if read answer; then
					ListFunction=$answer 
						echo "Enter name of group you want to generate a list for [e.g. scz, hcs, ocd... ]:"
							if read answer; then
							GROUP=$answer
								echo "Note: pre-existing list will now be deleted..."
								rm "$StudyFolder"/subjects/lists/subjects.preprocessing."$GROUP".list &> /dev/null
								for CASE in $CASES
									do
  									"$FunctionToRunInt" "$CASE"
  								done
  							fi
  					fi
  			fi
  		fi
fi

# ------------------------------------------------------------------------------
#  nii4dfpconvert function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "nii4dfpconvert" ]; then
	echo "Enter BOLD numbers you want to run the conversion on [e.g. 1 2 3]:"
		if read answer; then
		BOLDS=$answer 
			for CASE in $CASES
				do
  				"$FunctionToRunInt" "$CASE"
  			done
		fi
fi

# ------------------------------------------------------------------------------
#  cifti4dfpconvert function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "cifti4dfpconvert" ]; then
	echo "Enter BOLD numbers you want to run the conversion on [e.g. 1 2 3]:"
		if read answer; then
		BOLDS=$answer 
			for CASE in $CASES
				do
  				"$FunctionToRunInt" "$CASE"
  			done
		fi
fi

# ------------------------------------------------------------------------------
#  ciftismooth function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "ciftismooth" ]; then
	echo "Enter BOLD numbers you want to run CIFTI smoothing & 4dfp conversion on [e.g. 1 2 3]:"
		if read answer; then
		BOLDS=$answer 
	echo "Enter smoothing kernel levels [e.g. 1 2 3]:"
		if read answer; then
		KERNELS=$answer 
			for CASE in $CASES
				do
  				"$FunctionToRunInt" "$CASE"
  			done
		fi
		fi
fi

# ------------------------------------------------------------------------------
#  isolatesubcortexrois function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "isolatesubcortexrois" ]; then
	echo "Isolating subcortical ROIs for probabilistic tractography based on FreeSurfer segmentation"
	for CASE in $CASES
		do
  		"$FunctionToRunInt" "$CASE"
  	done
fi

# ------------------------------------------------------------------------------
#  probtracksubcortex function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "probtracksubcortex" ]; then
	echo "Enter which subcortical structure you want to run probtrackx on"
	echo "supported: thalamus caudate accumbens putamen pallidum thalamus_sensory thalamus_associative"
			if read answer; then
			STRUCTURES=$answer
				echo "Enter DWI resolution [Yale:1.80 or HCP:1.25]"
				if read answer; then
				DWIRes=$answer
					for CASE in $CASES
					do
  						"$FunctionToRunInt" "$CASE"
  					done
  				fi
  			fi
fi

# ------------------------------------------------------------------------------
#  linkmovement function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "linkmovement" ]; then
	echo "Enter BOLD numbers you want to link [e.g. 1 2 3 or 1-3 for merged BOLDs]:"
		if read answer; then
		BOLDS=$answer 
			for CASE in $CASES
			do
  				"$FunctionToRunInt" "$CASE"
  			done
  		fi
fi

# ------------------------------------------------------------------------------
#  printmatrix function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "printmatrix" ]; then
	echo "Enter which type of data you want to print the matrix for [supported: bold]:"
			if read answer; then
			DatatoPrint=$answer
				if [ "$DatatoPrint" == "bold" ]; then
					echo "Enter BOLD numbers you want to run the parcellation on [e.g. 1 2 3 or 1-3 for merged BOLDs]:"
						if read answer; then
						BOLDS=$answer 
						echo "Enter BOLD processing steps you want to run the parcellation on [e.g. g7_hpss_res-mVWM g7_hpss_res-mVWMWB hpss_res-mVWM hpss_res-mVWMWB]:"
							if read answer; then
							STEPS=$answer 
								for CASE in $CASES
									do
  									"$FunctionToRunInt" "$CASE"
  								done
  							fi
  						fi
  				fi
			fi
fi


# ------------------------------------------------------------------------------
#  boldmergecifti function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "boldmergecifti" ]; then

 	echo "Overwrite existing merged run [yes, no]:"
		if read answer; then
		Overwrite=$answer
		fi  
	echo "Enter which study and data you want to merge"
	echo ""
	echo "supported for DP5: 1_8 10_17 fixica1_8 fixica10_17 fixica1_8_processed fixica10_17_processed fixica1_8_taskonly fixica10_17_taskonly 1_4_raw 5_8_raw 10_13_raw 14_17_raw 1_8_raw 10_17_raw 2_8 11_17 dp5_dwi dp5_wm_run1_t1000forHCP dp5_wm_run1_t2470forHCP"
	echo "supported for OCD: ocd_rest_t1000forHCP"
	echo "supported for OCD: hcp_1_2 hcp_1_2_fixica hcp_1_2_fixica_processed hcp_rest_t973forYale"

			if read answer; then
			DatatoMerge=$answer
			echo "Enter BOLD processing step you want to run the merging on [e.g. Atlas [i.e. raw] g7_hpss_res-mVWM g7_hpss_res-mVWMWB hpss_res-mVWM hpss_res-mVWMWB]:"
				if read answer; then
				STEPS=$answer 
					for CASE in $CASES
					do
  						"$FunctionToRunInt" "$CASE"
  					done
  				fi
  			fi
fi

if [ "$FunctionToRunInt" == "boldmergenifti" ]; then

	echo "Enter which study and data you want to merge"
	echo "supported: 1_4_raw 5_8_raw 10_13_raw 14_17_raw 1_8_raw 10_17_raw"
			if read answer; then
			DatatoMerge=$answer
					for CASE in $CASES
					do
  						"$FunctionToRunInt" "$CASE"
  					done
  			fi
fi

# ------------------------------------------------------------------------------
#  fixica function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "fixica" ]; then
	echo "Note: Expects that minimally processed NIFTI & CIFTI BOLDs"
	echo ""
	echo "Overwrite existing run [yes, no]:"
		if read answer; then
		Overwrite=$answer
		fi  
	echo "Enter BOLD numbers you want to run FIX ICA on - e.g. 1 2 3 or 1_3 for merged BOLDs:"
		if read answer; then
		BOLDS=$answer 
				for CASE in $CASES
				do
  					"$FunctionToRunInt" "$CASE"
  				done
  		fi	
fi

# ------------------------------------------------------------------------------
#  postfix function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "postfix" ]; then
	echo "Note: This function depends on fsl, wb_command and matlab and expects startup.m to point to wb_command and fsl."
	echo ""
	echo "Overwrite existing postfix scenes [yes, no]:"
		if read answer; then
		Overwrite=$answer
		fi  
	echo "Enter BOLD numbers you want to run PostFix.sh on [e.g. 1 2 3]:"
		if read answer; then
		BOLDS=$answer 
			echo "Enter high pass filter used for FIX ICA [e.g. 2000]"
				if read answer; then
				HighPass=$answer 
					for CASE in $CASES
					do
  						"$FunctionToRunInt" "$CASE"
  					done
  				fi
  		fi	
fi

# ------------------------------------------------------------------------------
#  boldseparateciftifixica function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "boldseparateciftifixica" ]; then
	echo "Enter which study and data you want to separate"
	echo "supported: 1_4_raw 5_8_raw 10_13_raw 14_17_raw"
			if read answer; then
			DatatoSeparate=$answer
					for CASE in $CASES
					do
  						"$FunctionToRunInt" "$CASE"
  					done
  			fi
fi

# ------------------------------------------------------------------------------
#  boldhardlinkfixica function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "boldhardlinkfixica" ]; then
	echo "Enter BOLD numbers you want to generate connectivity hard links for [e.g. 1 2 3 or 1_3 for merged BOLDs]:"
		if read answer; then
		BOLDS=$answer 
			for CASE in $CASES
				do
  				"$FunctionToRunInt" "$CASE"
  			done
  		fi	
fi

if [ "$FunctionToRunInt" == "boldhardlinkfixicamerged" ]; then
				for CASE in $CASES
				do
  					"$FunctionToRunInt" "$CASE"
  				done
fi


# ------------------------------------------------------------------------------
#  fixicainsertmean function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "fixicainsertmean" ]; then
	echo "Note: This function will insert mean images into FIX ICA files"
	echo "Enter BOLD numbers you want to run mean insertion on [e.g. 1 2 3]:"
		if read answer; then
		BOLDS=$answer 
				for CASE in $CASES
				do
  					"$FunctionToRunInt" "$CASE"
  				done
  		fi	
fi

# ------------------------------------------------------------------------------
#  fixicaremovemean function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "fixicaremovemean" ]; then
	echo "Note: This function will remove mean from mapped FIX ICA files and save new images"
	echo "Enter BOLD numbers you want to run mean removal on [e.g. 1 2 3]:"
		if read answer; then
		BOLDS=$answer 
				for CASE in $CASES
				do
  					"$FunctionToRunInt" "$CASE"
  				done
  		fi	
fi

# ------------------------------------------------------------------------------
#  bolddense function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "bolddense" ]; then
	echo "Enter BOLD numbers you want to run dense connectome on [e.g. 1 2 3 or 1_3 for merged BOLDs]:"
		if read answer; then
		BOLDS=$answer 
				for CASE in $CASES
				do
  					"$FunctionToRunInt" "$CASE"
  				done
  		fi	
fi

# ------------------------------------------------------------------------------
#  fsldtifit function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "fsldtifit" ]; then
	echo "Run locally [1] or run on cluster [2]:"
	if read answer; then
	Cluster=$answer 
		if [ "$Cluster" == "2" ]; then
			echo "Enter queue name to submit jobs to [e.g. general, scavenge, anticevic, anti_gpu]:"
			if read answer; then
			QUEUE=$answer 
				for CASE in $CASES
				do
  					"$FunctionToRunInt" "$CASE"
  				done
  			fi
  		else
  				for CASE in $CASES
				do
  					"$FunctionToRunInt" "$CASE"
  				done	
  		fi	
  	fi
fi

if [ "$FunctionToRun" == "fsldtifit" ]; then
	
		# Check all the user-defined parameters: 1. Overwrite, 2. Cluster, 3. QUEUE
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
		if [ -z "$RunMethod" ]; then reho "Error: Run Method option [1=Run Locally on Node; 2=Send to Cluster] missing"; exit 1; fi
		
		Cluster="$RunMethod"
				
		echo ""
		echo "Running fsldtifit processing with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "QUEUE Name: $QUEUE"
		echo "Overwrite prior run: $Overwrite"
		echo "--------------------------------------------------------------"
		echo "Job ID:"
		
		for CASE in $CASES
		do
  			"$FunctionToRun" "$CASE"
  		done
fi

# ------------------------------------------------------------------------------
#  fslbedpostxgpu function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "fslbedpostxgpu" ]; then
	
		# Check all the user-defined parameters: 1. Overwrite, 2. Fibers, 3. Model, 4. Burnin, 5. Cluster, 6. QUEUE
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$Fibers" ]; then reho "Error: Fibers value missing"; exit 1; fi
		if [ -z "$Model" ]; then reho "Error: Model value missing"; exit 1; fi
		if [ -z "$Burnin" ]; then reho "Error: Burnin value missing"; exit 1; fi
		if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
		if [ -z "$RunMethod" ]; then reho "Error: Run Method option [1=Run Locally on Node; 2=Send to Cluster] missing"; exit 1; fi
		
		Cluster="$RunMethod"
		
		if [ "$Cluster" == "2" ]; then
				FSLGECUDAQ="$QUEUE" # Cluster queue name with GPU nodes - e.g. anticevic-gpu
				export FSLGECUDAQ
				export SGE_ROOT=1
				NJOBS=4
		fi				
		
		echo ""
		echo "Running fslbedpostxgpu processing with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Subjects: $CASES"		
		echo "Number of Fibers: $Fibers"
		echo "Model Type: $Model"
		echo "Burnin Period: $Burnin"
		echo "EPI Unwarp Direction: $UnwarpDir"
		echo "QUEUE Name: $QUEUE"
		echo "Overwrite prior run: $Overwrite"
		echo "--------------------------------------------------------------"
		echo "Job ID:"
		
		for CASE in $CASES
		do
  			"$FunctionToRun" "$CASE"
  		done
fi

if [ "$FunctionToRunInt" == "fslbedpostxgpu" ]; then

	echo "Running fslbedpostxgpu processing interactively. First enter the necessary parameters."
	# Request all the user-defined parameters: 1. Overwrite, 2. Fibers, 3. Model, 4. Burnin, 5. Cluster, 6. QUEUE
	echo ""
	echo "Overwrite existing run [yes, no]:"
	if read answer; then Overwrite=$answer; fi
	echo ""
	echo "Enter # of fibers per voxel [e.g. 3]:"
	if read answer; then Fibers=$answer; fi
	echo ""
	echo "Enter model for bedpostx [1 for monoexponential, 2 for multiexponential, 3 for multiexponential-deconvolution]:"
	if read answer; then Model=$answer; fi
	echo ""
	echo "Enter burnin period for bedpostx [e.g. 3000; default 1000]:"
	if read answer; then Burnin=$answer; fi 	
	echo ""	
	echo "-- Run locally [1] or run on cluster [2]"
	if read answer; then Cluster=$answer; fi
	echo ""
	if [ "$Cluster" == "2" ]; then
		echo "-- Enter queue name - always submit this job to a GPU-enabled queue [e.g. anticevic-gpu]"
		if read answer; then QUEUE=$answer; fi
		echo ""
	fi
		echo "Running fslbedpostxgpu processing with the following parameters:"
		echo ""
		echo "-------------------------------------------------------------"
		echo "Number of Fibers: $Fibers"
		echo "Model Type: $Model"
		echo "Burnin Period: $Burnin"
		echo "EPI Unwarp Direction: $UnwarpDir"
		echo "QUEUE Name: $QUEUE"
		echo "Overwrite prior run: $Overwrite"
		
		for CASE in $CASES
			do
  			"$FunctionToRunInt" "$CASE"
  		done
fi

# ------------------------------------------------------------------------------
#  PreFreesurfer function loop (hcp1_orig)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp1_orig" ]; then
	
	#echo "Note: Making sure global environment script is sourced..."
	#if [ -f "$TOOLS/hcpsetup.sh" ]; then
	#	. "$TOOLS/hcpsetup.sh" 
	#else
	#	echo "ERROR: Environment script is missing. Check your user profile paths!"
	#fi 	
	
	MasterFolder="$StudyFolder" 
	echo "Run locally [1] or run on cluster [2]:"
	if read answer; then
		Cluster=$answer 
		if [ "$Cluster" == "2" ]; then
			echo "Enter queue name to submit jobs to [e.g. general, scavenge, anticevic, anti_gpu]:"
			if read answer; then
			QUEUE=$answer 
				for CASE in $CASES
				do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"
  					"$FunctionToRunInt" "$CASE"
  				done
  			fi
  		else
  				for CASE in $CASES
				do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"
  					"$FunctionToRunInt" "$CASE"
  				done	
  		fi	
  	fi
fi

# ------------------------------------------------------------------------------
#  Freesurfer function loop (hcp2_orig)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp2_orig" ]; then
	
	#echo "Note: Making sure global environment script is sourced..."
	#if [ -f "$TOOLS/hcpsetup.sh" ]; then
	#	. "$TOOLS/hcpsetup.sh" 
	#else
	#	echo "ERROR: Environment script is missing. Check your user profile paths!"
	#fi 	
	
	MasterFolder="$StudyFolder"
	echo "Overwrite existing run [yes, no]:"
	if read answer; then
		Overwrite=$answer  
		echo "Run locally [1] or run on cluster [2]:"
	if read answer; then
		Cluster=$answer 
		if [ "$Cluster" == "2" ]; then
			echo "Enter queue name to submit jobs to [e.g. general, scavenge, anticevic, anti_gpu]:"
			if read answer; then
			QUEUE=$answer 
				for CASE in $CASES
				do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"
  					"$FunctionToRunInt" "$CASE"
  				done
  			fi
  		else
  				for CASE in $CASES
				do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"				
  					"$FunctionToRunInt" "$CASE"
  				done	
  		fi	
  	fi
  	fi
fi

# ------------------------------------------------------------------------------
#  PostFreesurfer function loop (hcp3_orig)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp3_orig" ]; then
		
	#echo "Note: Making sure global environment script is sourced..."
	#if [ -f "$TOOLS/hcpsetup.sh" ]; then
	#	. "$TOOLS/hcpsetup.sh" 
	#else
	#	echo "ERROR: Environment script is missing. Check your user profile paths!"
	#fi
	
	MasterFolder="$StudyFolder" 
	echo "Run locally [1] or run on cluster [2]:"
	if read answer; then
		Cluster=$answer 
		if [ "$Cluster" == "2" ]; then
			echo "Enter queue name to submit jobs to [e.g. general, scavenge, anticevic, anti_gpu]:"
			if read answer; then
			QUEUE=$answer 
				for CASE in $CASES
				do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"
  					"$FunctionToRunInt" "$CASE"
  				done
  			fi
  		else
  				for CASE in $CASES
				do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"				
  					"$FunctionToRunInt" "$CASE"
  				done	
  		fi	
  	fi
fi

# ------------------------------------------------------------------------------
#  Volume BOLD processing function loop (hcp4_orig)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp4_orig" ]; then

		#echo "Note: Making sure global environment script is sourced..."
		#if [ -f "$TOOLS/hcpsetup.sh" ]; then
		#	. "$TOOLS/hcpsetup.sh" 
		#else
		#	echo "ERROR: Environment script is missing. Check your user profile paths!"
		#fi 	
		
		MasterFolder="$StudyFolder" 
		echo "Enter BOLD numbers you want to run the HCP Volume pipeline on [e.g. 1 2 3]:"
		if read answer; then
			BOLDS=$answer
		echo "Enter Phase Encoding Directions for BOLDs or only a single value if no counterbalancing [y=PA; y-=AP; x=RL; -x=LR]:"
		if read answer; then
			PhaseEncodinglist=$answer 	 
		echo "Run locally [1] or run on cluster [2]:"
		if read answer; then
			Cluster=$answer 
			if [ "$Cluster" == "2" ]; then
				echo "Enter queue name to submit jobs to [e.g. general, scavenge, anticevic, anti_gpu]:"
				if read answer; then
					QUEUE=$answer 
					for CASE in $CASES
					do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"
  						"$FunctionToRunInt" "$CASE"
  					done
  				fi
  			else
  				for CASE in $CASES
				do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"
  					"$FunctionToRunInt" "$CASE"
  				done	
  			fi	
  		fi
  		fi
  		fi
fi

# ------------------------------------------------------------------------------
#  Surface BOLD processing function loop (hcp5_orig)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp5_orig" ]; then
	
		#echo "Note: Making sure global environment script is sourced..."
		#if [ -f "$TOOLS/hcpsetup.sh" ]; then
		#	. "$TOOLS/hcpsetup.sh" 
		#else
		#	echo "ERROR: Environment script is missing. Check your user profile paths!"
		#fi 	
		
		MasterFolder="$StudyFolder" 
		echo "Enter BOLD numbers you want to run the HCP Surface pipeline on [e.g. 1 2 3]:"
		if read answer; then
			BOLDS=$answer
		echo "Run locally [1] or run on cluster [2]:"
		if read answer; then
			Cluster=$answer 
			if [ "$Cluster" == "2" ]; then
				echo "Enter queue name to submit jobs to [e.g. general, scavenge, anticevic, anti_gpu]:"
				if read answer; then
					QUEUE=$answer 
					for CASE in $CASES
					do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"
					"$FunctionToRunInt" "$CASE"
  					done
  				fi
  			else
					for CASE in $CASES
					do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"
					"$FunctionToRunInt" "$CASE"
  					done
  			fi	
  		fi
  		fi  	
fi

# ------------------------------------------------------------------------------
#  Diffusion processing function loop (hcpd_orig)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcpd_orig" ]; then
	
	#echo "Note: Making sure global environment script is sourced..."
	#if [ -f "$TOOLS/hcpsetup.sh" ]; then
	#	. "$TOOLS/hcpsetup.sh" 
	#fi
	#else
	#	echo "ERROR: Environment script is missing. Check your user profile paths!"
	#fi
	
	MasterFolder="$StudyFolder" 
	echo "Run locally [1] or run on cluster [2]:"
	if read answer; then
		Cluster=$answer 
		if [ "$Cluster" == "2" ]; then
			echo "Enter queue name to submit jobs to [e.g. general, scavenge, anticevic, anti_gpu]:"
			if read answer; then
			QUEUE=$answer 
				for CASE in $CASES
				do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"
  					"$FunctionToRunInt" "$CASE"
  				done
  			fi
  		else
  				for CASE in $CASES
				do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"
  					"$FunctionToRunInt" "$CASE"
  				done	
  		fi	
  	fi
fi


# ------------------------------------------------------------------------------
#  Diffusion legacy processing function loop (hcpdlegacy)
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "hcpdlegacy" ]; then
	
	# Check all the user-defined parameters: 1. EchoSpacing, 2. PEdir, 3. TE, 4. UnwarpDir, 5. DiffDataSuffix, 6. QUEUE
	
#	if [ "$#" -ne 10 ]; then
#		reho "Error: Your input parameters are incomplete. Please check usage by running <AP hcpdlegacy>"	

		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$EchoSpacing" ]; then reho "Error: Echo Spacing value missing"; exit 1; fi
		if [ -z "$PEdir" ]; then reho "Error: Phase Encoding Direction value missing"; exit 1; fi
		if [ -z "$TE" ]; then reho "Error: TE value for Fieldmap missing"; exit 1; fi
		if [ -z "$UnwarpDir" ]; then reho "Error: EPI Unwarp Direction value missing"; exit 1; fi
		if [ -z "$DiffDataSuffix" ]; then reho "Error: Diffusion Data Suffix Name missing"; exit 1; fi
		if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
		if [ -z "$RunMethod" ]; then reho "Error: Run Method option [1=Run Locally on Node; 2=Send to Cluster] missing"; exit 1; fi
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
		if [ -z "$Scheduler" ]; then reho "Error: Scheduler option missing for fsl_sub command [e.g. lsf or torque]"; exit 1; fi
		fi		
		echo ""
		echo "Running DWI legacy processing with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Echo Spacing: $EchoSpacing"
		echo "Phase Encoding Direction: $PEdir"
		echo "TE value for Fieldmap: $TE"
		echo "EPI Unwarp Direction: $UnwarpDir"
		echo "Diffusion Data Suffix Name: $DiffDataSuffix"
		echo "Overwrite prior run: $Overwrite"
		echo "--------------------------------------------------------------"
		echo "Job ID:"
		
		for CASE in $CASES
		do
  			"$FunctionToRun" "$CASE"
  		done
fi

if [ "$FunctionToRunInt" == "hcpdlegacy" ]; then

	echo "Running DWI legacy processing interactively. First enter the necessary parameters."
	# Request all the user-defined parameters: 1. EchoSpacing, 2. PEdir, 3. TE, 4. UnwarpDir, 5. DiffDataSuffix, 6. QUEUE
	echo ""
	echo ""
	
		echo "-- EPI Echo Spacing for data [in msec]; e.g. 0.69"
		if read answer; then EchoSpacing=$answer; fi
		echo ""
		echo "-- Phase Encoding Direction - Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior"
		if read answer; then PEdir=$answer; fi
		echo ""
		echo "-- Enter Delta TE value for fieldmap - This is the echo time difference of the fieldmap sequence - find this out form the operator - defaults are *usually* 2.46ms on SIEMENS"
		if read answer; then TE=$answer; fi
		echo ""
		echo "-- Epi phase unwarping direction - Direction for EPI image unwarping; e.g. x or x- for LR/RL, y or y- for AP/PA; may been to try out both -/+ combinations"
		if read answer; then UnwarpDir=$answer; fi
		echo ""
		echo "-- Diffusion data suffix name - e.g. if the data is called <SubjectID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR"
		if read answer; then DiffDataSuffix=$answer; fi
		echo ""
		echo "Overwrite existing run [yes, no]:"
		if read answer; then Overwrite=$answer; fi  
		echo ""
		echo "-- Run locally [1] or run on cluster [2]"
		if read answer; then Cluster=$answer; fi
		echo ""
		if [ "$Cluster" == "2" ]; then
			echo "-- Enter queue name - always submit this job to a GPU-enabled queue [e.g. anticevic-gpu]"
			if read answer; then QUEUE=$answer; fi
			echo ""
			echo "-- Enter scheduler name for fsl_sub command [e.g. lsf or torque]"
			if read answer; then Scheduler=$answer; fi
			echo ""
		fi
		
		echo "Running DWI legacy processing with the following parameters:"
		echo ""
		echo "-------------------------------------------------------------"
		echo "Echo Spacing: $EchoSpacing"
		echo "Phase Encoding Direction: $PEdir"
		echo "TE value for Fieldmap: $TE"
		echo "EPI Unwarp Direction: $UnwarpDir"
		echo "Diffusion Data Suffix Name: $DiffDataSuffix"
		
		for CASE in $CASES
			do
  			"$FunctionToRunInt" "$CASE"
  		done
fi

# ------------------------------------------------------------------------------
#  StructuralParcellation function loop (structuralparcellation)
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "structuralparcellation" ]; then	
	
# Check all the user-defined parameters: 1. InputDataType, 2. OutName, 3. ParcellationFile, 4. QUEUE, 5. RunMethod, 6. Scheduler
# Optional: ComputePConn, UseWeights, WeightsFile
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$InputDataType" ]; then reho "Error: Input data type value missing"; exit 1; fi
		if [ -z "$OutName" ]; then reho "Error: Output file name value missing"; exit 1; fi
		if [ -z "$ParcellationFile" ]; then reho "Error: File to use for parcellation missing"; exit 1; fi
		if [ -z "$RunMethod" ]; then reho "Run Method option missing. Assuming local run. [1=Run Locally on Node; 2=Send to Cluster]"; RunMethod="1"; fi
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler option missing for fsl_sub command [e.g. lsf or torque]"; exit 1; fi
		fi
		
		# Parse optional parameters if not specified 
		if [ -z "$ExtractData" ]; then ExtractData="no"; fi
		if [ -z "$Overwrite" ]; then Overwrite="no"; fi
		
		echo ""
		echo "Running StructuralParcellation function with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Study Folder: ${StudyFolder}"
		echo "Subjects: ${CASES}"
		echo "ParcellationFile: ${ParcellationFile}"
		echo "Parcellated Data Output Name: ${OutName}"
		echo "Input Data Type: ${InputDataType}"
		echo "Extract data in CSV format: ${ExtractData}"		
		echo "Overwrite prior run: ${Overwrite}"
		echo "--------------------------------------------------------------"
		echo "Job ID:"
		
		for CASE in $CASES
		do
  			"$FunctionToRun" "$CASE"
  		done
fi

# ------------------------------------------------------------------------------
#  BOLDParcellation function loop (boldparcellation)
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "boldparcellation" ]; then	
	
# Check all the user-defined parameters: 1. InputFile, 2. InputPath, 3. InputDataType, 4. OutPath, 5. OutName, 6. ParcellationFile, 7. QUEUE, 8. RunMethod, 9. Scheduler
# Optional: ComputePConn, UseWeights, WeightsFile
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$InputFile" ]; then reho "Error: Input file value missing"; exit 1; fi
		if [ -z "$InputPath" ]; then reho "Error: Input path value missing"; exit 1; fi
		if [ -z "$InputDataType" ]; then reho "Error: Input data type value missing"; exit 1; fi
		if [ -z "$OutPath" ]; then reho "Error: Output path value missing"; exit 1; fi
		if [ -z "$OutName" ]; then reho "Error: Output file name value missing"; exit 1; fi
		if [ -z "$ParcellationFile" ]; then reho "Error: File to use for parcellation missing"; exit 1; fi
		if [ -z "$RunMethod" ]; then reho "Run Method option missing. Assuming local run. [1=Run Locally on Node; 2=Send to Cluster]"; RunMethod="1"; fi
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler option missing for fsl_sub command [e.g. lsf or torque]"; exit 1; fi
		fi
		
		# Parse optional parameters if not specified 
		if [ -z "$UseWeights" ]; then UseWeights="no"; fi
		if [ -z "$ComputePConn" ]; then ComputePConn="no"; fi
		if [ -z "$WeightsFile" ]; then WeightsFile="no"; fi
		if [ -z "$ExtractData" ]; then ExtractData="no"; fi

		echo ""
		echo "Running BOLDParcellation function with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Study Folder: ${StudyFolder}"
		echo "Subjects: ${CASES}"
		echo "Input File: ${InputFile}"
		echo "Input Path: ${InputPath}"
		echo "ParcellationFile: ${ParcellationFile}"
		echo "BOLD Parcellated Connectome Output Name: ${OutName}"
		echo "BOLD Parcellated Connectome Output Path: ${OutPath}"
		echo "Input Data Type: ${InputDataType}"
		echo "Compute PConn File: ${ComputePConn}"
		echo "Weights file specified to omit certain frames: ${UseWeights}"
		echo "Weights file name: ${WeightsFile}"
		echo "Extract data in CSV format: ${ExtractData}"		
		echo "Overwrite prior run: ${Overwrite}"
		echo "--------------------------------------------------------------"
		echo "Job ID:"
		
		for CASE in $CASES
		do
  			"$FunctionToRun" "$CASE"
  		done
fi

if [ "$FunctionToRunInt" == "boldparcellation" ]; then

	echo "Running BOLDParcellation function interactively. First enter the necessary parameters."
	# Check all the user-defined parameters: 1. InputFile, 2. InputPath, 3. InputDataType, 4. OutPath, 5. OutName, 6. ParcellationFile, 7. QUEUE, 8. RunMethod, 9. Scheduler
	# Optional: ComputePConn, UseWeights, WeightsFile	echo ""
			
	echo ""
	
		echo "-- Specify the name of the file you want to use for parcellation (e.g. bold1_Atlas_MSMAll_hp2000_clean)"
		if read answer; then InputFile=$answer; fi
		echo ""
		echo "-- Specify path of the file you want to use for parcellation relative to the master study folder and subject directory (e.g. /images/functional/)"
		if read answer; then InputPath=$answer; fi
		echo ""
		echo "-- Specify the type of data for the input file (e.g. dscalar or dtseries)"
		if read answer; then InputDataType=$answer; fi
		echo ""
		echo "-- Specify the absolute path of the file you want to use for parcellation (e.g. {$TOOLS}/MNAP/general/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)"
		if read answer; then ParcellationFile=$answer; fi
		echo ""
		echo "-- Specify the suffix output name of the pconn file"
		if read answer; then OutName=$answer; fi
		echo ""
		echo "-- Specify the output path name of the pconn file relative to the master study folder [e.g. /images/functional/]"
		if read answer; then OutPath=$answer; fi
		echo ""
		# Ask for optional parameters
		echo "-- Specify if a parcellated connectivity file should be computed (pconn). This is done using covariance and correlation [e.g. yes; default is set to no]"
		if read answer; then ComputePConn=$answer; fi
		echo ""
		echo "-- If computing a  parcellated connectivity file you can specify which frames to omit [e.g. yes' or no; default is set to no]"
		if read answer; then UseWeights=$answer; fi
		echo ""
		echo "-- Specify the location of the weights file relative to the master study folder [e.g. /images/functional/movement/bold1.use]"
		if read answer; then WeightsFile=$answer; fi
		echo ""
		echo "-- Overwrite existing run [yes, no]:"
		if read answer; then Overwrite=$answer; fi  
		echo ""
		echo "-- Run locally [1] or run on cluster [2]"
		if read answer; then Cluster=$answer; fi
		echo ""
		if [ "$Cluster" == "2" ]; then
			echo "-- Enter queue name [e.g. anticevic]"
			if read answer; then QUEUE=$answer; fi
			echo ""
			echo "-- Enter scheduler name for fsl_sub command [e.g. lsf or torque]"
			if read answer; then Scheduler=$answer; fi
			echo ""
		fi
		
		echo "Running DWI legacy processing with the following parameters:"
		echo ""
		echo "-------------------------------------------------------------"
		echo "Study Folder: ${StudyFolder}"
		echo "Subjects: ${CASES}"
		echo "Input File: ${InputFile}"
		echo "Input Path: ${InputPath}"
		echo "ParcellationFile: ${ParcellationFile}"
		echo "BOLD Parcellated Connectome Output Name: ${OutName}"
		echo "BOLD Parcellated Connectome Output Path: ${OutPath}"
		echo "Input Data Type: ${InputDataType}"
		echo "Compute PConn File: ${ComputePConn}"
		echo "Weights file specified to omit certain frames: ${UseWeights}"
		echo "Weights file name: ${WeightsFile}"
		echo "Overwrite prior run: ${Overwrite}"
		
		for CASE in $CASES
			do
  			"$FunctionToRunInt" "$CASE"
  		done
fi


# ------------------------------------------------------------------------------
#  DWIDenseParcellation function loop (dwidenseparcellation)
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "dwidenseparcellation" ]; then
	
# Check all the user-defined parameters: 1. MatrixVersion, 2. ParcellationFile, 3. OutName, 4. QUEUE, 5. RunMethod
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$MatrixVersion" ]; then reho "Error: Matrix version value missing"; exit 1; fi
		if [ -z "$ParcellationFile" ]; then reho "Error: File to use for parcellation missing"; exit 1; fi
		if [ -z "$OutName" ]; then reho "Error: Name of output pconn file missing"; exit 1; fi
		if [ -z "$RunMethod" ]; then reho "Error: Run Method option [1=Run Locally on Node; 2=Send to Cluster] missing"; exit 1; fi
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler option missing for fsl_sub command [e.g. lsf or torque]"; exit 1; fi
		fi		
		echo ""
		echo "Running DWIDenseParcellation function with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Matrix version used for input: $MatrixVersion"
		echo "File to use for parcellation: $ParcellationFile"
		echo "Dense DWI Parcellated Connectome Output Name: $OutName"
		echo "Overwrite prior run: $Overwrite"
		echo "--------------------------------------------------------------"
		echo "Job ID:"
		
		for CASE in $CASES
		do
  			"$FunctionToRun" "$CASE"
  		done
fi

if [ "$FunctionToRunInt" == "dwidenseparcellation" ]; then

	echo "Running DWIDenseParcellation function interactively. First enter the necessary parameters."
	# Request all the user-defined parameters:  1. MatrixVersion, 2. ParcellationFile, 3. OutName, 4. QUEUE, 5. RunMethod
	echo ""
	echo ""
	
		echo "-- Specify Matrix Version; e.g. 1 or 3"
		if read answer; then MatrixVersion=$answer; fi
		echo ""
		echo "-- Specify the absolute path of the file you want to use for parcellation (e.g. {$TOOLS}/MNAP/general/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)"
		if read answer; then ParcellationFile=$answer; fi
		echo ""
		echo "-- Specify name of output pconn file"
		if read answer; then OutName=$answer; fi
		echo ""
		echo "-- Overwrite existing run [yes, no]:"
		if read answer; then Overwrite=$answer; fi  
		echo ""
		echo "-- Run locally [1] or run on cluster [2]"
		if read answer; then Cluster=$answer; fi
		echo ""
		if [ "$Cluster" == "2" ]; then
			echo "-- Enter queue name [e.g. anticevic]"
			if read answer; then QUEUE=$answer; fi
			echo ""
			echo "-- Enter scheduler name for fsl_sub command [e.g. lsf or torque]"
			if read answer; then Scheduler=$answer; fi
			echo ""
		fi
		
		echo "Running DWI legacy processing with the following parameters:"
		echo ""
		echo "-------------------------------------------------------------"
		echo "Matrix version used for input: $MatrixVersion"
		echo "File to use for parcellation: $ParcellationFile"
		echo "Dense DWI Parcellated Connectome Output Name: $OutName"
		echo "Overwrite prior run: $Overwrite"
		
		for CASE in $CASES
			do
  			"$FunctionToRunInt" "$CASE"
  		done
fi

# ------------------------------------------------------------------------------
#  DWIDenseSeedTractography function loop (dwiseedtractography)
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "dwiseedtractography" ]; then
	
# Check all the user-defined parameters: 1. MatrixVersion, 2. ParcellationFile, 3. OutName, 4. QUEUE, 5. RunMethod
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$MatrixVersion" ]; then reho "Error: Matrix version value missing"; exit 1; fi
		if [ -z "$SeedFile" ]; then reho "Error: File to use for seed reduction missing"; exit 1; fi
		if [ -z "$OutName" ]; then reho "Error: Name of output pconn file missing"; exit 1; fi
		if [ -z "$RunMethod" ]; then reho "Error: Run Method option [1=Run Locally on Node; 2=Send to Cluster] missing"; exit 1; fi
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler option missing for fsl_sub command [e.g. lsf or torque]"; exit 1; fi
		fi		
		echo ""
		echo "Running DWIDenseParcellation function with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Matrix version used for input: $MatrixVersion"
		echo "File to use for seed reduction: $SeedFile"
		echo "Dense DWI Parcellated Connectome Output Name: $OutName"
		echo "Overwrite prior run: $Overwrite"
		echo "--------------------------------------------------------------"
		echo "Job ID:"
		
		for CASE in $CASES
		do
  			"$FunctionToRun" "$CASE"
  		done
fi

# ------------------------------------------------------------------------------
#  Pretractography processing function loop (Matt's original code)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "pretractography" ]; then

	#echo "Note: Making sure global environment script is sourced..."
	#if [ -f "$TOOLS/hcpsetup.sh" ]; then
	#	. "$TOOLS/hcpsetup.sh" 
	#else
	#	echo "ERROR: Environment script is missing. Check your user profile paths!"
	#fi 	
	
	MasterFolder="$StudyFolder" 	
	echo "Run locally [1] or run on cluster [2]:"
	if read answer; then
	Cluster=$answer 
		if [ "$Cluster" == "2" ]; then
			echo "Enter queue name to submit jobs to [e.g. general, scavenge, anticevic, anti_gpu]:"
			if read answer; then
			QUEUE=$answer 
				for CASE in $CASES
				do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"				
  					"$FunctionToRunInt" "$CASE"
  				done
  			fi
  		else
  				for CASE in $CASES
				do
					StudyFolder="$MasterFolder"/"$CASE"/hcp
					echo "$StudyFolder"				
  					"$FunctionToRunInt" "$CASE"
  				done	
  		fi	
  	fi
fi


# ------------------------------------------------------------------------------
#  Matrix 1 Cortex processing function loop (Matt's original code w/o m2 and m4)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "probtrackxgpucortex" ]; then
	
	#echo "Note: Making sure global environment script is sourced..."
	#if [ -f "$TOOLS/hcpsetup.sh" ]; then
	#	. "$TOOLS/hcpsetup.sh" 
	#else
	#	echo "ERROR: Environment script is missing. Check your user profile paths!"
	#fi 	
	
	MasterFolder="$StudyFolder" 	
	echo "Run locally [1] or run on cluster [2]:"
	if read answer; then
	Cluster=$answer 
		if [ "$Cluster" == "2" ]; then
			echo "Enter queue name to submit jobs to [e.g. general, scavenge, anticevic, anti_gpu]:"
			if read answer; then
			QUEUE=$answer 
					echo "Enter Step Size [Yale: 0.45, HCP: 0.3125]:"
						if read answer; then
						StepSize=$answer
					echo "Enter Diffusion Resolution [Yale: 1.80, HCP: 1.25]:"
						if read answer; then
						DiffusionResolution=$answer
					echo "Enter Hemispheres [e.g. L R]:"
						if read answer; then
						HemisphereSTRING=$answer
					echo "Enter if Distance Adjustment is Performed [e.g. YES NO]:"
						if read answer; then
						PDSTRING=$answer				
							for CASE in $CASES
							do
								StudyFolder="$MasterFolder"/"$CASE"/hcp
								echo "$StudyFolder"
  								"$FunctionToRunInt" "$CASE"
  							done
  						fi
  						fi
  						fi
  						fi
  			fi
  		else # for running locally
					echo "Enter Step Size [Yale: 0.45, HCP: 0.3125]:"
						if read answer; then
						StepSize=$answer
					echo "Enter Diffusion Resolution [Yale: 1.80, HCP: 1.25]:"
						if read answer; then
						DiffusionResolution=$answer
					echo "Enter Hemispheres [e.g. L R]:"
						if read answer; then
						HemisphereSTRING=$answer
					echo "Enter if Distance Adjustment is Performed [e.g. YES NO]:"
						if read answer; then
						PDSTRING=$answer				
							for CASE in $CASES
							do
								StudyFolder="$MasterFolder"/"$CASE"/hcp
								echo "$StudyFolder"							
  								"$FunctionToRunInt" "$CASE"
  							done
  						fi
  						fi
  						fi
  						fi
  		fi	
  	fi
fi
  

# ------------------------------------------------------------------------------
#  Dense Connectome Cortex function loop (Matt's original code following GPU)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "makedensecortex" ]; then
	
	#echo "Note: Making sure global environment script is sourced..."
	#if [ -f "$TOOLS/hcpsetup.sh" ]; then
	#	. "$TOOLS/hcpsetup.sh" 
	#else
	#	echo "ERROR: Environment script is missing. Check your user profile paths!"
	#fi 		
	
	MasterFolder="$StudyFolder" 	
	echo "Run locally [1] or run on cluster [2]:"
	if read answer; then
	Cluster=$answer 
		if [ "$Cluster" == "2" ]; then
			echo "Enter queue name to submit jobs to [e.g. general, scavenge, anticevic, anti_gpu]:"
			if read answer; then
			QUEUE=$answer 
					echo "Enter Step Size [e.g. Yale: 0.45, HCP: 0.3125]"
						if read answer; then
						StepSize=$answer
					echo "Enter Diffusion Resolution [e.g. Yale: 1.80, HCP: 1.25]"
						if read answer; then
						DiffusionResolution=$answer	
					echo "Enter Hemispheres [e.g. L R]:"
						if read answer; then
						HemisphereSTRING=$answer
					echo "Enter if Distance Adjustment is Performed [e.g. YES NO]:"
						if read answer; then
						PDSTRING=$answer				
							for CASE in $CASES
							do
								StudyFolder="$MasterFolder"/"$CASE"/hcp
								echo "$StudyFolder"
  								"$FunctionToRunInt" "$CASE"
  							done
  						fi
  						fi
  						fi
  						fi
  			fi
  		else # for running locally
					echo "Enter Step Size [e.g. Yale: 0.45, HCP: 0.3125]"
						if read answer; then
						StepSize=$answer
					echo "Enter Diffusion Resolution [e.g. Yale: 1.80, HCP: 1.25]:"
						if read answer; then
						DiffusionResolution=$answer	
					echo "Enter Hemispheres [e.g. L R]:"
						if read answer; then
						HemisphereSTRING=$answer
					echo "Enter if Distance Adjustment is Performed [e.g. YES NO]:"
						if read answer; then
						PDSTRING=$answer				
							for CASE in $CASES
							do
								StudyFolder="$MasterFolder"/"$CASE"/hcp
								echo "$StudyFolder"
  								"$FunctionToRunInt" "$CASE"
  							done
  						fi
  						fi
  						fi
  						fi
  		fi	
  	fi
fi


# ------------------------------------------------------------------------------
#  autoptx function loop
# ------------------------------------------------------------------------------

## -- NEED TO CODE

# ------------------------------------------------------------------------------
#  pretractographydense function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "pretractographydense" ]; then
	
		# Check all the user-defined parameters: 1. RunMethod, 2. QUEUE, 3. Scheduler
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$RunMethod" ]; then reho "Error: Run Method option [1=Run Locally on Node; 2=Send to Cluster] missing"; exit 1; fi
		
		Cluster="$RunMethod"
		
		if [ "$Cluster" == "2" ]; then
				if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler option missing for fsl_sub command [e.g. lsf or torque]"; exit 1; fi
		fi				
		
		echo ""
		echo "Running Pretractography Dense processing with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Subjects: $CASES"
		echo "--------------------------------------------------------------"
		
		for CASE in $CASES
		do
  			"$FunctionToRun" "$CASE"
  		done
fi

if [ "$FunctionToRunInt" == "pretractographydense" ]; then

	echo "Running Pretractography Dense processing interactively. First enter the necessary parameters."
	# Request all the user-defined parameters: 1. RunMethod, 2. QUEUE, 3. Scheduler
	echo ""
	echo "-- Run locally [1] or run on cluster [2]"
	if read answer; then Cluster=$answer; fi
	echo ""
		if [ "$Cluster" == "2" ]; then
			echo "-- Enter queue name [e.g. anticevic]"
			if read answer; then QUEUE=$answer; fi
			echo ""
			echo "-- Enter scheduler name for fsl_sub command [e.g. lsf or torque]"
			if read answer; then Scheduler=$answer; fi
			echo ""
		fi
		
		echo "Running Pretractography processing with the following parameters:"
		echo ""
		echo "-------------------------------------------------------------"
		echo "CASES: $CASES"
		echo "--------------------------------------------------------------"
		
		for CASE in $CASES
			do
  			"$FunctionToRunInt" "$CASE"
  		done
fi

# ------------------------------------------------------------------------------
#  probtrackxgpudense function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "probtrackxgpudense" ]; then
	
		# Check all the user-defined parameters: 1.QUEUE, 2. Scheduler, 3. Matrix1, 4. Matrix2
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
		if [ -z "$Scheduler" ]; then reho "Error: Scheduler option missing for fsl_sub command [e.g. lsf or torque]"; exit 1; fi
		if [ -z "$MatrixOne" ] && [ -z "$MatrixThree" ]; then reho "Error: Matrix option missing. You need to specify at least one. [e.g. --omatrix1='yes' and/or --omatrix2='yes']"; exit 1; fi
		if [ "$MatrixOne" == "yes" ]; then
			if [ -z "$NsamplesMatrixOne" ]; then NsamplesMatrixOne=10000; fi
		fi
		if [ "$MatrixThree" == "yes" ]; then
			if [ -z "$NsamplesMatrixThree" ]; then NsamplesMatrixThree=3000; fi
		fi

		echo ""
		echo "Running Pretractography Dense processing with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "CASES: $CASES"
		echo "QUEUE: $QUEUE"
		echo "Compute Matrix1: $MatrixOne"
		echo "Compute Matrix3: $MatrixThree"
		echo "Number of samples for Matrix1: $NsamplesMatrixOne"
		echo "Number of samples for Matrix3: $NsamplesMatrixThree"
		echo "Overwrite prior run: $Overwrite"
		echo "--------------------------------------------------------------"
		
		for CASE in $CASES
		do
  			"$FunctionToRun" "$CASE"
  		done
fi

if [ "$FunctionToRunInt" == "probtrackxgpudense" ]; then

	echo "Running Pretractography Dense processing interactively. First enter the necessary parameters."
	# Request all the user-defined parameters: 1.QUEUE, 2. Scheduler, 3. Matrix1, 4. Matrix2
	echo ""
	echo "-- Enter queue name [e.g. anticevic]"
	if read answer; then QUEUE=$answer; fi
	echo ""
	echo "-- Enter scheduler name for fsl_sub command [e.g. lsf or torque]"
	if read answer; then Scheduler=$answer; fi
	echo ""
	echo "-- Compute Matrix1 [e.g. yes or leave empty]"
	if read answer; then Matrix1=$answer; fi
	echo ""
	echo "-- Compute Matrix3 [e.g. yes or leave empty]"
	if read answer; then Matrix3=$answer; fi
	echo ""
	echo "-- Number of samples for Matrix1 [Default - 10000]"
	if read answer; then NsamplesMatrixOne=$answer; fi
	echo ""
	echo "-- Number of samples for Matrix3 [Default - 3000]"
	if read answer; then NsamplesMatrixThree=$answer; fi
	echo ""
	
		#Set job limits
		#JobLimitMatrix1=0
		#JobLimitMatrix3=0
		
		echo "Running Pretractography processing with the following parameters:"
		echo ""
		echo "-------------------------------------------------------------"
		echo "CASES: $CASES"
		echo "QUEUE: $QUEUE"
		echo "Compute Matrix1: $MatrixOne"
		echo "Compute Matrix3: $MatrixThree"
		echo "Number of samples for Matrix1: $NsamplesMatrixOne"
		echo "Number of samples for Matrix3: $NsamplesMatrixThree"
		echo "Overwrite prior run: $Overwrite"
		echo "--------------------------------------------------------------"
		
		for CASE in $CASES
		do
  			"$FunctionToRunInt" "$CASE"
  		done
fi

# ------------------------------------------------------------------------------
#  awshcpsync - AWS S3 Sync command wrapper
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "awshcpsync" ]; then
	
		# Check all the user-defined parameters: 1. Modality, 2. Awsuri, 3. RunMethod
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$RunMethod" ]; then reho "Error: Run Method option [1=Dry Run; 2=Real Run] missing"; exit 1; fi
		if [ -z "$Modality" ]; then reho "Error: Modality option [e.g. MEG, MNINonLinear, T1w] missing"; exit 1; fi
		if [ -z "$Awsuri" ]; then reho "Error: AWS URI option [e.g. /hcp-openaccess/HCP_900] missing"; exit 1; fi
		
		echo ""
		echo "Running sync for HCP data from Amazon AWS S3 with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "CASES: $CASES"
		echo "Run Method: $RunMethod"
		echo "Modality: $Modality"
		echo "AWS URI Path: $Awsuri"
		echo "--------------------------------------------------------------"
		echo ""
		
		for CASE in $CASES
		do
  			"$FunctionToRun" "$CASE"
  		done
fi		
		
if [ "$FunctionToRunInt" == "awshcpsync" ]; then
	
	echo "Running AWS S3 Sync... Make sure you configured your AWS credentials"
	echo "Dry run [1] or real run [2]"
	
	if read answer; then
		RunType=$answer
	fi
	echo "Enter the AWS URI [e.g. /hcp-openaccess/HCP_900]"
	if read answer; then
		AwsFolder=$answer
	fi
	echo "Which modality or folder do you want to sync [e.g. MEG, MNINonLinear, T1w]"
	if read answer; then
		Modality=$answer
	fi

	for CASE in $CASES
	do
  		"$FunctionToRunInt" "$CASE"
	done
fi

exit 0