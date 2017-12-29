#!/bin/sh 
#set -x

#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# # mnap.sh
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
# * MNAP Connector Wrapper for the general neuroimaging workflow
#
# ## License
#
# See the [LICENSE](https://bitbucket.org/mnap/connector/LICENSE.md) file
#
# ## Description:
#
# * This is a MNAP connector wrapper developed as for front-end bash integration for MNAP
#
# ### Installed Software (Prerequisites) - these are sourced in ~MNAP/library/environment/mnap_environment.sh
#
# * * All MNAP repositories (git clone git@bitbucket.org:mnap/mnaptools.git)
# * * Connectome Workbench (v1.0 or above)
# * * FSL (version 5.0.9 or above with GPU-enabled DWI tools)
# * * FreeSurfer (5.3 HCP version for HCP-compatible data)
# * * FreeSurfer (6.0 version for all other data)
# * * MATLAB (version 2012b or above with Signal Processing, Statistics and Machine Learning and Image Processing Toolbox)
# * * FIX ICA
# * * PALM
# * * Python (version 2.7 or above with numpy, pydicom, scipy & nibabel)
# * * AFNI
# * * Gradunwarp (https://github.com/ksubramz/gradunwarp)
# * * Human Connectome Pipelines for modified MNAP (https://bitbucket.org/mnap/hcpmodified)
# * * R Statistical Environment with ggplot
# * * dcm2nii (23-June-2017 release) # Expected Environment Variables
#
# * HCPPIPEDIR
# * CARET7DIR
# * FSLDIR
#
# ### Expected Previous Processing
# 
# * The necessary input files for higher-level analyses come from HCP pipelines and/or gmri
#
#~ND~END~

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= CODE START =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=

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
    echo -e "$RED_F$1 \033[0m"
}

geho() {
    echo -e "$GREEN_F$1 \033[0m"
}

yeho() {
    echo -e "$YELLOW_F$1 \033[0m"
}

beho() {
    echo -e "$BLUE_F$1 \033[0m"
}

mageho() {
    echo -e "$MAGENTA_F$1 \033[0m"
}

cyaneho() {
    echo -e "$CYAN_F$1 \033[0m"
}

weho() {
    echo -e "$WHITE_F$1 \033[0m"
}

# ------------------------------------------------------------------------------
#  General help usage function
# ------------------------------------------------------------------------------

show_usage() {

geho ""
geho "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
geho "................. ███╗   ███╗███╗   ██╗ █████╗ ██████╗ ......................" 
geho "................. ████╗ ████║████╗  ██║██╔══██╗██╔══██╗ ....................." 
geho "................. ██╔████╔██║██╔██╗ ██║███████║██████╔╝ ....................."
geho "................. ██║╚██╔╝██║██║╚██╗██║██╔══██║██╔═══╝ ......................"
geho "................. ██║ ╚═╝ ██║██║ ╚████║██║  ██║██║ .........................."  
geho "................. ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝ .........................."
geho "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
geho "                     Software Licence Disclaimer:                            "
geho "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
geho " Use of this software is subject to the terms and conditions defined by the  "
geho " Yale University Copyright Policies:                                         "
geho "    http://ocr.yale.edu/faculty/policies/yale-university-copyright-policy    "
geho " and the terms and conditions defined in the file 'LICENSE.txt' which is     "
geho " a part of this source code package.                                         "
geho "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
echo ""
echo "-----------------------------------------------------------------------------"
echo "---------------------------  General Usage  ---------------------------------"
echo "-----------------------------------------------------------------------------"
echo ""
echo "Usage:"
echo ""
echo "    mnap --function=<command> --studyfolder=<study_folder> \ "
echo "    --subjects='<list_of_cases>' [options]"
echo ""
echo "Example:"
echo ""
echo "    mnap --function=dicomorganize \ "
echo "    --studyfolder=/some/path/to/study/subjects \ "
echo "    --subjects='<case_id1>,<case_id2>'"
echo ""
echo "Specific function help:"
echo ""
echo "    mnap -<command>   OR   mnap ?<command>   OR   mnap <command>"
echo ""
echo "............................................................................"
echo ""
echo "Note the following conventions used in help and documentation:"
echo ""
echo "    * Square brackets []: Specify a value that is optional."
echo "			Note: Value within brackets is the default value."
echo ""
echo "    * Angle brackets <>: Contents describe what should go there."
echo ""
echo "    * Dashes or flags -- : Define input variables."
echo ""
echo "    * All descriptions use regular case and all options use CAPS"
echo ""
echo "---------------------------------------------------------------------------"
echo "------------------------ MNAP Specific Functions --------------------------"
echo "---------------------------------------------------------------------------"
echo ""
echo "Data organization functions"
echo "----------------------------"
echo "dicomorganize ...... sort dicoms and setup nifti files from dicoms"
echo "setuphcp ...... setup data structure for hcp processing"
echo "createlists ...... setup subject lists for preprocessing or analyses"
echo "hpcsync ...... sync with hpc cluster(s) for preprocessing"
echo "awshcpsync ...... sync hcp data from aws s3 cloud"
echo ""
echo ""
echo "QC functions"
echo "------------"
echo "eddyqc ...... run quality control on diffusion datasets following eddy outputs"
echo "qcpreproc ...... run visual qc for a given modality (t1w,tw2,myelin,bold,dwi)"
echo ""  				
echo ""
echo "DWI processing, analyses & probabilistic tractography functions"
echo "----------------------------------------------------------------"
echo "hcpdlegacy ...... dwi processing for data with standard fieldmaps"
echo "fsldtifit ...... run fsl dtifit (cluster usable)"
echo "fslbedpostxgpu ...... run fsl bedpostx w/gpu"
echo "pretractographydense ...... generates space for whole-brain dense connectomes"
echo "probtrackxgpudense ...... run fsl probtrackx for whole brain & generates dense "
echo "                          whole-brain connectomes"
echo ""
echo ""
echo "Misc. functions and analyses"
echo "---------------------------"
echo "computeboldfc ...... computes seed or gbc BOLD functional connectivity"
echo "structuralparcellation ...... parcellate myelin or thickness"
echo "boldparcellation ...... parcellate bold data and generate pconn files"
echo "dwidenseparcellation ...... parcellate dense dwi tractography data"
echo "dwiseedtractography ...... reduce dense dwi tractography data using a seed structure"
echo "printmatrix ...... extract parcellated matrix for dense CIFTI data using a network solution"
echo "bolddense ...... compute bold dense connectome (needs >30gb ram per bold)"
echo "ciftismooth ...... smooth cifti data"
echo "roiextract ...... extract data from pre-specified ROIs in CIFTI or NIFTI"
echo ""
echo ""
echo "FIX ICA de-noising functions"
echo "---------------------------"
echo "fixica ...... run fix ica de-noising on a given volume"
echo "postfix ...... generates workbench scenes for each subject directory"
echo "boldhardlinkfixica ...... setup hard links for single run fix ica results"
echo "fixicainsertmean ...... re-insert mean image back into mapped fix ica data"
echo "fixicaremovemean ...... remove mean image from mapped fix ica data"
echo "boldseparateciftifixica ...... separate specified bold timeseries (use if bolds merged)"
echo "boldhardlinkfixicamerged ...... setup sym links for merged fix ica results (use if bolds merged)" 
echo ""
echo ""
echo "---------------------------------------------------------------------------"
echo "------- General MRI (gmri) utilities for preprocessing and analyses -------"
echo "---------------------------------------------------------------------------"
echo ""
echo "The MNAP pipelines contain additional python-based gmri utilities."
echo "These are accessed either directly via 'gmri' command from the terminal."
echo "Alternatively the 'mnap' connector wrapper parses all functions from "
echo "'gmri' package as standard input."
echo ""
echo ""
echo "	--> Example to pass command:    mnap <command> [options]"
echo "	--> Example to request help for command:    mnap ?<command>"
echo ""
echo "`gmri`"
echo "`gmri -l`"
echo ""
echo ""
echo "---------------------------------------------------------------------------"
echo "------------- All Supported MNAP Stand-alone Matlab Tools -----------------"
echo "---------------------------------------------------------------------------"
echo ""
echo "==> MNAP Matlab tools are located in: $TOOLS/$MNAPREPO/matlab"
echo ""
echo "The MNAP package contain additional matlab-based stand-alone tools."
echo "These tools are used across various MNAP packages, but can be accessed"
echo "as stand-alone functions within Matlab. Help and documentation is"
echo "embedded within each stand-alone tool via standard Matlab help call." 
echo ""
echo "-- MNAP Matlab Analyses Utilities --- Statistical functions:"
echo ""
ls $TOOLS/$MNAPREPO/matlab/*/*.m | grep -o 'stats.*' | cut -f2- -d/
echo ""
echo "-- MNAP Matlab Analyses Utilities --- General functions:"
echo ""
ls $TOOLS/$MNAPREPO/matlab/*/*.m | grep -o 'stats.*' | cut -f2- -d/
echo ""
echo "-- MNAP Matlab Analyses Utilities --- gmrimage functions:"
echo ""
ls $TOOLS/$MNAPREPO/matlab/*/*.m | grep -o 'stats.*' | cut -f2- -d/
echo ""
echo "-- MNAP Matlab Analyses Utilities --- Functional connectivity functions:"
echo ""
ls $TOOLS/$MNAPREPO/matlab/*/*.m | grep -o 'stats.*' | cut -f2- -d/
echo ""
echo ""
}

# ========================================================================================
# ===================== SPECIFIC ANALYSIS FUNCTIONS START HERE ===========================
# ========================================================================================

matlabhelp() {
		echo ""
}

show_usage_matlabhelp() {

		echo ""
		echo "=================================================================="
		echo "==== All Supported MNAP Independent Matlab Analyses Utilities ===="
		echo "=================================================================="
		echo ""
		echo "==> Matlab tools are located in: $TOOLS/$MNAPREPO/matlab"
		echo ""
		echo "-- MNAP Matlab Analyses Utilities --- Statistical functions:"
		echo ""
		ls $TOOLS/$MNAPREPO/matlab/*/*.m | grep -o 'stats.*' | cut -f2- -d/
		echo ""
		echo "-- MNAP Matlab Analyses Utilities --- General functions:"
		echo ""
		ls $TOOLS/$MNAPREPO/matlab/*/*.m | grep -o 'stats.*' | cut -f2- -d/
		echo ""
		echo "-- MNAP Matlab Analyses Utilities --- gmrimage functions:"
		echo ""
		ls $TOOLS/$MNAPREPO/matlab/*/*.m | grep -o 'stats.*' | cut -f2- -d/
		echo ""
		echo "-- MNAP Matlab Analyses Utilities --- Functional connectivity functions:"
		echo ""
		ls $TOOLS/$MNAPREPO/matlab/*/*.m | grep -o 'stats.*' | cut -f2- -d/
		echo ""
		echo ""
}

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
  	echo ""
  	gmri ?${UsageInput}
  	echo ""
}

# ------------------------------------------------------------------------------------------------------
#  dicomorganize - Sort original DICOMs into sub-folders and then generate NIFTI files
# ------------------------------------------------------------------------------------------------------

dicomorganize() {
				  		
	  		mkdir ${StudyFolder}/${CASE}/dicom &> /dev/null
	  		
	  		if [ "$Overwrite" == "yes" ]; then
				reho "===> Removing prior DICOM run"
				rm -f ${StudyFolder}/${CASE}/dicom/DICOM-Report.txt &> /dev/null
	  		fi

				echo ""
				reho "===> Checking for presence of ${StudyFolder}/${CASE}/dicom/DICOM-Report.txt"
				echo ""
					if (test -f ${StudyFolder}/${CASE}/dicom/DICOM-Report.txt); then
						echo ""
						geho "--- Found ${StudyFolder}/${CASE}/dicom/DICOM-Report.txt"
						geho "    Note: To re-run set --overwrite='yes'"
						echo ""
						geho " ... $CASE ---> dicomorganize done"
						echo ""
					else
						echo "--- Did not find ${StudyFolder}/${CASE}/dicom/DICOM-Report.txt"
						echo ""
	  					# -- Combine all the calls into a single command
		 				Com1="cd ${StudyFolder}/${CASE}"
						echo " ---> running sortDicom and dicom2nii for $CASE"
						echo ""
						Com2="gmri sortDicom"
						Com3="gmri dicom2niix unzip=yes gzip=yes clean=yes verbose=true cores=4"
						ComQUEUE="$Com1; $Com2; $Com3"
						
						TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
						Suffix="$CASE_$TimeStamp"
							
						if [ "$Cluster" == 1 ]; then
						  	echo ""
  							echo "---------------------------------------------------------------------------------"
							echo "Running dicomorganize locally on `hostname`"
							echo "Check output here: $StudyFolder/$CASE/dicom "
							echo "---------------------------------------------------------------------------------"
		 					echo ""
		 					eval "$ComQUEUE"
						else
							echo "Job ID:"
							# -- Set the scheduler commands
							rm -f "$StudyFolder"/"$CASE"/dicom/ComQUEUE_dicomorganize_"$Suffix".sh &> /dev/null
							echo "$ComQUEUE" >> "$StudyFolder"/"$CASE"/dicom/ComQUEUE_dicomorganize_"$Suffix".sh
							chmod 770 "$StudyFolder"/"$CASE"/dicom/ComQUEUE_dicomorganize_"$Suffix".sh
							
							# -- Run the scheduler commands
							cd "$StudyFolder"/"$CASE"/dicom/
							gmri schedule command="${StudyFolder}/${CASE}/dicom/ComQUEUE_dicomorganize_${Suffix}.sh" \
							settings="${Scheduler}" output="stdout:${StudyFolder}/${CASE}/dicom/dicomorganize.${Suffix}.output.log|stderr:${StudyFolder}/${CASE}/dicom/dicomorganize.${Suffix}.error.log" \
							workdir="${StudyFolder}/${CASE}/dicom" 
							
							echo ""
							echo "---------------------------------------------------------------------------------"
							echo "Data successfully submitted" 
							echo "Scheduler: $Scheduler"
							echo "Check output logs here: $StudyFolder/$CASE/dicom"
							echo "---------------------------------------------------------------------------------"
							echo ""
						fi
					fi
}

show_usage_dicomorganize() {
  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
  				echo "This function expects a set of raw DICOMs in <study_folder>/<case>/inbox."
  				echo "DICOMs are organized, gzipped and converted to NIFTI format for additional processing."
  				echo ""
  				echo ""
  				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "--function=<function_name>                             Name of function"
				echo "--path=<study_folder>                                  Path to study data folder"
				echo "--subjects=<comma_separated_list_of_cases>             List of subjects to run"
				echo "--scheduler=<name_of_cluster_scheduler_and_options>    A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                       e.g. for SLURM the string would look like this: "
				echo "                                                       --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
				echo ""
				echo "-- OPTIONAL PARAMETERS: "
				echo ""
				echo "--overwrite=<re-run_dicomorganize>                     Explicitly force a re-run of dicomorganize"
				echo ""
    			echo ""
    			echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='dicomorganize' \ "
				echo "--subjects='<comma_separarated_list_of_cases>' "
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='dicomorganize' \ "
				echo "--subjects='<comma_separarated_list_of_cases>' \ "
				echo "--scheduler='<name_of_scheduler_and_options>'"
				echo "" 
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  setuphcp - Setup the HCP File Structure to be fed to the Yale HCP
# ------------------------------------------------------------------------------------------------------

setuphcp() {

	cd "$StudyFolder"/"$CASE"
		
			echo "--> running setuphcp for $CASE"
		 	echo ""
		 	# -- Combine all the calls into a single command
		 	Com1="cd ${StudyFolder}/${CASE}"
			Com2="gmri setupHCP"
			ComQUEUE="$Com1; $Com2"
			
			# Generate timestamp for logs and scripts
			TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
			Suffix="$CASE_$TimeStamp"
			
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
				
				# -- Set the scheduler commands
				rm -f "$StudyFolder"/"$CASE"/setuphcp_${Suffix}.sh &> /dev/null
				echo "$ComQUEUE" >> "$StudyFolder"/"$CASE"/setuphcp_${Suffix}.sh
				chmod 770 "$StudyFolder"/"$CASE"/setuphcp_${Suffix}.sh				
				
				# -- Run the scheduler commands
				cd "$StudyFolder"/"$CASE"/
				gmri schedule command="${StudyFolder}/${CASE}/setuphcp_${Suffix}.sh" \
				settings="${Scheduler}" \
				output="stdout:${StudyFolder}/${CASE}/setuphcp.${Suffix}.output.log|stderr:${StudyFolder}/${CASE}/setuphcp.${Suffix}.error.log"  \
				workdir="${StudyFolder}/${CASE}"  
				
				echo ""
				echo "---------------------------------------------------------------------------------"
				echo "Data successfully submitted" 
				echo "Scheduler Name and Options: $Scheduler"
				echo "Check output logs here: $StudyFolder/$CASE/"
				echo "---------------------------------------------------------------------------------"
				echo ""
			fi
}

show_usage_setuphcp() {
  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
  				echo "This function generates the Human Connectome Project folder structure for preprocessing."
  				echo "It should be executed after proper dicomorganize and subject.txt file has been vetted."
  				echo ""
  				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "--function=<function_name>                             Name of function"
				echo "--path=<study_folder>                                  Path to study data folder"
				echo "--subjects=<comma_separated_list_of_cases>             List of subjects to run"
				echo "--scheduler=<name_of_cluster_scheduler_and_options>    A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                       e.g. for SLURM the string would look like this: "
				echo "                                                       --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
    			echo ""
    			echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='setuphcp' \ "
				echo "--subjects='<comma_separarated_list_of_cases>' \ "
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='setuphcp' \ "
				echo "--subjects='<comma_separarated_list_of_cases>' \ "
				echo "--scheduler='<name_of_cluster_scheduler_and_options>' \ "
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
  				echo "    * preprocessing --> Subject parameter list with cases to preprocess"
  				echo "    * analysis --> List of cases to compute seed connectivity or GBC"
  				echo "    * snr --> List of cases to compute signal-to-noise ratio"
  				echo ""
  				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "--function=<function_name>                  Name of function"
				echo "--path=<study_folder>                       Path to study data folder"
				echo "--subjects=<comma_separated_list_of_cases>  List of subjects to run"
				echo "--listtocreate=<type_of_list_to_generate>   Type of list to generate (e.g. preprocessing). "
				echo "--listname=<output_name_of_the_list>        Output name of the list to generate. "
				echo "                                            Supported: preprocessing, analysis, snr "
				echo ""
				echo "-- OPTIONAL PARAMETERS: "
				echo ""
				echo "--overwrite=<yes/no>                        Explicitly delete any prior lists"
				echo "--append=<yes>                              Explicitly append the existing list"
				echo "--listpath=<absolute_path_to_list_folder>   Explicitly set path where you want the lists generated"
				echo "                                            Default: <study_folder>/processing/lists "
				echo ""
				echo "    * Note: If --append set to <yes> then function will append new cases to the end"
				echo ""								
				echo "--parameterfile=<header_file_for_processing_list>	Set header for the processing list."
				echo ""
				echo "    * Default:"
				echo ""
				echo "`ls ${TOOLS}/${MNAPREPO}/connector/functions/subjectparamlist_header_multiband.txt`"
				echo ""
				echo "    * Supported: "
				echo ""
				echo "`ls ${TOOLS}/${MNAPREPO}/connector/functions/subjectparamlist_header*` "
				echo ""
				echo "    * Note: If --parameterfile set to <no> then function will not add a header"
				echo ""								
				echo "--listfunction=<function_used_to_create_list>   Point to external function to use"
				echo "--bolddata=<comma_separated_list_of_bolds>      List of BOLD files to append to analysis or snr lists"
				echo "--parcellationfile=<file_for_parcellation>      Specify the absolute file path for parcellation in $MNAPPATH/connector/templates/Parcellations/ "
				echo "--filetype=<file_extension>                     Extension for BOLDs in the analysis (e.g. _Atlas). Default empty []"
				echo "--boldsuffix=<comma_separated_bold_suffix>      List of BOLDs to iterate over in the analysis list"
#    			echo "--subjecthcpfile=<yes/no>                       Use individual subject_hcp.txt file for for appending the parameter list"
    			echo ""
    			echo "-- Example with flagged parameters:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='createlists' \ "
				echo "--subjects='<comma_separarated_list_of_cases>' \ "
				echo "--listtocreate='preprocessing' \ "
				echo "--overwrite='yes' \ "
				echo "--listname='<list_to_generate>' \ "
				echo "--parameterfile='no' \ "
				echo "--append='yes' "
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='createlists' \ "
				echo "--subjects='<comma_separarated_list_of_cases>' \ "
				echo "--listtocreate='analysis' \ "
				echo "--overwrite='yes' \ "
				echo "--bolddata='1' \ "	
				echo "--filetype='dtseries.nii' \ "											
				echo "--listname='<list_to_generate>' \ "
				echo "--append='yes' "				
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
				echo "mnap hpcsync <study_folder> '<list of cases>'"
    			echo ""
    			echo ""
				echo "* Example with flags:"
				echo "mnap --function=hpcsync --path=<study_folder> --subjects='<list of cases>'--cluster=<cluster_address> --dir=<rsync_direction> --netid=<Yale_NetID> --clusterpath=<cluster_study_folder>"
    			echo ""
    			echo ""
  				echo "-- OPTIONS:"
    			echo ""
    			echo "--function=<function_name>   Name of function (required)"	
    			echo "--path=<study_folder>        Path to study data folder (required)"	
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
							# -- Dense connectome command - use in isolation due to RAM limits (need ~30GB free at any one time per subject)
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
# ----------------------------------------- FIX ICA CODE -----------------------------------------------
# ------------------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------------
#  linkmovement - Sets hard links for BOLDs into Parcellated folder for fixica use
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
				
				# -- setup folder strucrture if missing
				mkdir "$StudyFolder"/"$CASE"/images    &> /dev/null
				mkdir "$StudyFolder"/"$CASE"/images/functional	    &> /dev/null
				mkdir "$StudyFolder"/"$CASE"/images/functional/movement    &> /dev/null
				
				# -- setup hard links for images						
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii     &> /dev/null
				rm "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".nii.gz     &> /dev/null
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas_hp2000_clean.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD"_hp2000_clean.nii.gz "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".nii.gz
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas.dtseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii
				ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD".nii.gz "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".nii.gz
				#rm "$StudyFolder"/"$CASE"/images/functional/boldfixicarfMRI_REST*     &> /dev/null
				#rm "$StudyFolder"/"$CASE"/images/functional/boldrfMRI_REST*     &> /dev/null
				
				echo "Setting up hard links for movement data for BOLD# $BOLD for $CASE... "
				
				# -- Clean up movement regressor file to match dofcMRIp convention and copy to movement directory
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
					
					# -- First check if the boldfixica file has the mean inserted
					3dBrickStat -mean -non-zero boldfixica"$BOLD".nii.gz[1] >> boldfixica"$BOLD"_mean.txt
					ImgMean=`cat boldfixica"$BOLD"_mean.txt`
					if [ $(echo " $ImgMean > 1000" | bc) -eq 1 ]; then
					echo "1st frame mean=$ImgMean Mean inserted OK for subject $CASE and bold# $BOLD. Skipping to next..."
						else
						# -- Next check if the boldfixica file has the mean inserted twice by accident
						if [ $(echo " $ImgMean > 15000" | bc) -eq 1 ]; then
						echo "1st frame mean=$ImgMean ERROR: Mean has been inserted twice for $CASE and $BOLD."	
							else
							# -- Command that inserts mean image back to the boldfixica file using g_InsertMean matlab function
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
		
		# -- Parse all Parameters
		EchoSpacing="$EchoSpacing" #EPI Echo Spacing for data (in msec); e.g. 0.69
		PEdir="$PEdir" #Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior
		TE="$TE" #delta TE in ms for field map or "NONE" if not used
		UnwarpDir="$UnwarpDir" # direction along which to unwarp
		DiffData="$DiffDataSuffix" # Diffusion data suffix name - e.g. if the data is called <SubjectID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR
		CUDAQUEUE="$QUEUE" # Cluster queue name with GPU nodes - e.g. anticevic-gpu
		DwellTime="$EchoSpacing" #same variable as EchoSpacing - if you have in-plane acceleration then this value needs to be divided by the GRAPPA or SENSE factor (miliseconds)
		DwellTimeSec=`echo "scale=6; $DwellTime/1000" | bc` # set the dwell time to seconds:
		
		# -- Establish global directory paths
		T1wFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w
		DiffFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/Diffusion
		T1wDiffFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion
		FieldMapFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/FieldMap_strc
		LogFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/Diffusion/log
		Overwrite="$Overwrite"
		
		# Generate timestamp for logs and scripts
		TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
		Suffix="$CASE_$TimeStamp"
		
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
			--diffdatasuffix="${DiffDataSuffix}" >> "$LogFolder"/DiffPreprocPipelineLegacy_"$Suffix".log
		else
			rm -f ${StudyFolder}/${CASE}/hcp/hcpd_legacy_${Suffix}.sh &> /dev/null		
			echo "${HCPPIPEDIR}/DiffusionPreprocessingLegacy/DiffPreprocPipelineLegacy.sh \
			--path=${StudyFolder} \
			--subject=${CASE} \
			--PEdir=${PEdir} \
			--echospacing=${EchoSpacing} \
			--TE=${TE} \
			--unwarpdir=${UnwarpDir} \
			--diffdatasuffix=${DiffDataSuffix} \
			--overwrite=${Overwrite}" > ${StudyFolder}/${CASE}/hcp/hcpd_legacy_${Suffix}.sh
			
			# - Make script executable 
			chmod 770 ${StudyFolder}/${CASE}/hcp/hcpd_legacy_${Suffix}.sh
			cd ${StudyFolder}/${CASE}/hcp/
			
			# - Send to scheduler 
			gmri schedule command="${StudyFolder}/${CASE}/hcp/hcpd_legacy_${Suffix}.sh" \
			settings="${Scheduler}" \
			output="stdout:${StudyFolder}/${CASE}/hcp/hcpd_legacy.${Suffix}.output.log|stderr:${StudyFolder}/${CASE}/hcp/hcpd_legacy.${Suffix}.error.log" \
			workdir="${StudyFolder}/${CASE}/hcp/"
			
			echo "--------------------------------------------------------------"
			echo "Data successfully submitted" 
			echo "Scheduler Name and Options: $Scheduler"
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
				echo "--function=<function_name>                   Name of function"
				echo "--path=<study_folder>                        Path to study data folder"
				echo "--subjects=<comma_separated_list_of_cases>   List of subjects to run"
				echo "--echospacing=<echo_spacing_value>           EPI Echo Spacing for data [in msec]; e.g. 0.69"
				echo "--PEdir=<phase_encoding_direction>           Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior"
				echo "--TE=<delta_te_value_for_fieldmap>           This is the echo time difference of the fieldmap sequence - find this out form the operator - defaults are *usually* 2.46ms on SIEMENS"
				echo "--unwarpdir=<epi_phase_unwarping_direction>  Direction for EPI image unwarping; e.g. x or x- for LR/RL, y or y- for AP/PA; may been to try out both -/+ combinations"
				echo "--diffdatasuffix=<diffusion_data_name>       Name of the DWI image; e.g. if the data is called <SubjectID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR"
				echo "--scheduler=<name_of_cluster_scheduler_and_options>         A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                            e.g. for SLURM the string would look like this: "
				echo "                                                            --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
				echo "" 
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
				echo "--overwrite=<clean_prior_run>                Delete prior run for a given subject"
				echo ""
				echo "-- Example with flagged parameters for a local run (needs GPU-enabled node):"
				echo ""
				echo "mnap --path='/gpfs/project/fas/n3/Studies/Anticevic.DP5/subjects' \ "
				echo "--subjects='ta6455' \ "
				echo "--function='hcpdlegacy' \ " 
				echo "--PEdir='1' \ "
				echo "--echospacing='0.69' \ "
				echo "--TE='2.46' \ "
				echo "--unwarpdir='x-' \ "
				echo "--diffdatasuffix='DWI_dir91_LR' \ "
				echo "--overwrite='yes'"
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler [ needs GPU-enabled queue ]:"
				echo ""
				echo "mnap --path='/gpfs/project/fas/n3/Studies/Anticevic.DP5/subjects' \ "
				echo "--subjects='ta6455' \ "
				echo "--function='hcpdlegacy' \ "
				echo "--PEdir='1' \ "
				echo "--echospacing='0.69' \ "
				echo "--TE='2.46' \ "
				echo "--unwarpdir='x-' \ "
				echo "--diffdatasuffix='DWI_dir91_LR' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo "--overwrite='yes' \ "
				echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  eddyqc - Executes the DWI EddyQ C (DWIEddyQC.sh) via the MNAP connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

eddyqc() {

		################# CHECK eddy_squad and eddy_squad INSTALL ################################
		
		# -- Check if eddy_squad and eddy_quad exist in user path
		EddySquadCheck=`which eddy_squad`
		EddyQuadCheck=`which eddy_quad`
		
		if [ -z ${EddySquadCheck} ] || [ -z ${EddySquadCheck} ]; then
			echo ""
		    reho " -- ERROR: EDDY QC does not seem to be installed on this system."
		    echo ""
		    exit 1
		fi
		    
		########################################## INPUTS ########################################## 
		
		# eddy-cleaned DWI Data
		
		########################################## OUTPUTS #########################################
		
		# Outputs will be located in <eddyBase>.qc per EDDY QC specification
		
		LogFolder="${EddyPath}/log_eddyqc"
		mkdir ${LogFolder} > /dev/null 2>&1
		
		# Generate timestamp for logs and scripts
		TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
		Suffix="$CASE_$TimeStamp"
			
		if [ "$Cluster" == 1 ]; then
			echo "Running locally on `hostname`"
			echo "Check log file output here: $LogFolder"
			echo "--------------------------------------------------------------"
			echo ""
			DWIeddyQC.sh \
			--path=${StudyFolder} \
			--subject=${CASE} \
			--eddybase=${EddyBase} \
			--report=${Report} \
			--bvalsfile=${BvalsFile} \
			--mask=${Mask} \
			--eddyidx=${EddyIdx} \
			--eddyparams=${EddyParams} \
			--bvecsfile=${BvecsFile} \
			--overwrite=${Overwrite} >> "$LogFolder"/DWIEddyQC_"$Suffix".log
		else
			# - Clean prior command 
			rm -f "$LogFolder"/DWIEddyQC_"$Suffix".sh &> /dev/null	
			# - Echo full command into a script
			echo "DWIeddyQC.sh \
			--path='${StudyFolder}' \
			--subject='${CASE}' \
			--eddybase='${EddyBase}' \s
			--report='${Report}' \
			--bvalsfile='${BvalsFile}' \
			--mask='${Mask}' \
			--eddyidx='${EddyIdx}' \
			--eddyparams='${EddyParams}' \
			--bvecsfile='${BvecsFile}' \
			--overwrite='${Overweite}'" > "$LogFolder"/DWIEddyQC_"$Suffix".sh
			
			# - Make script executable 
			chmod 770 "$LogFolder"/DWIEddyQC_"$Suffix".sh
			cd ${LogFolder}
			
			# - Send to scheduler 
			gmri schedule command="${LogFolder}/DWIEddyQC_${Suffix}.sh" \
			settings="${Scheduler}" \
			output="stdout:${LogFolder}/DWIEddyQC.${Suffix}.output.log|stderr:${LogFolder}/DWIEddyQC.${Suffix}.error.log" \
			workdir="${LogFolder}"
			
			echo "--------------------------------------------------------------"
			echo "Data successfully submitted" 
			echo "Scheduler Name and Options: $Scheduler"
			echo "Check output logs here: $LogFolder"
			echo "--------------------------------------------------------------"
			echo ""
		fi
}

show_usage_eddyqc() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function is based on FSL's eddy to perform quality control on diffusion mri (dMRI) datasets."
				echo "It explicitly assumes the that eddy has been run and that EDDY QC by Matteo Bastiani, FMRIB has been installed. "
				echo "For full documentation of the EDDY QC please examine the README file."
				echo ""
				echo "   <study_folder>/<case>/hcp/<case>/Diffusion/eddy/ ---> DWI eddy outputs would be here"
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "--function=<function_name>                 Name of function --> eddyqc "
 				echo "--path=<study_folder>                      Path to study data folder"
				echo "--subject=<subj_id>                        Subjects ID to run EDDY QC on"
 				echo "--eddybase=<eddy_input_base_name>          This is the basename specified when running EDDY (e.g. eddy_unwarped_images)"
 				echo "--eddyidx=<eddy_index_file>                EDDY index file"
 				echo "--eddyparams=<eddy_param_file>             EDDY parameters file"
 				echo "--mask=<mask_file>                         Binary mask file (most qc measures will be averaged across voxels labeled in the mask)"
 				echo "--bvalsfile=<bvals_file>                   bvals input file"
 				echo "--report=<run_group_or_individual_report>  If you want to generate a group report [individual or group  Default: individual]"
 				echo ""
 				echo "    *IF* --report='group' *THEN* this argument needs to be specificed: "
 				echo ""
 				echo "--list=<group_list_input>                  Text file containing a list of qc.json files obtained from SQUAD"
				echo ""
				echo ""
    			echo "-- OPTIONAL PARMETERS:"
				echo "" 
 				echo "--overwrite=<clean_prior_run>                          Delete prior run for a given subject"
				echo "--eddypath=<eddy_folder_relative_to_subject_folder>    Specify the relative path of the eddy folder you want to use for inputs"
				echo "                                                       Default: <study_folder>/<case>/hcp/<case>/Diffusion/eddy/ "
				echo "--bvecsfile=<bvecs_file>                               If specified, the tool will create a bvals_no_outliers.txt "
				echo "                                                        & a bvecs_no_outliers.txt file that contain the bvals and bvecs of the non outlier volumes, based on the MSR estimates)"
				echo "--scheduler=<name_of_cluster_scheduler_and_options>    A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                       e.g. for SLURM the string would look like this: "
				echo "                                                       --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
				echo ""
    			echo "-- EXTRA OPTIONAL PARMETERS IF --report='group' "
    			echo ""
				echo "--groupvar=<extra_grouping_variable>           Text file containing extra grouping variable"
				echo "--outputdir=<name_of_cleaned_eddy_output>      Output directory - default = '<eddyBase>.qc' "
				echo "--update=<setting_to_update_subj_reports>      Applies only if --report='group' - set to <true> to update existing single subject qc reports "
				echo ""
 				echo ""
 				echo "-- EXAMPLE:"
				echo ""
				echo "mnap --path='<path_to_study_folder_with_subject_directories>' \ "
				echo "--function='eddyqc' \ "
				echo "--subject='<subj_id>' \ "
				echo "--eddybase='<eddy_base_name>' \ "
				echo "--report='individual'"
				echo "--bvalsfile='<bvals_file>' \ "
				echo "--mask='<mask_file>' \ "
				echo "--eddyidx='<eddy_index_file>' \ "
				echo "--eddyparams='<eddy_param_file>' \ "
				echo "--bvecsfile='<bvecs_file>' \ "
				echo "--overwrite='yes' "
				echo "--scheduler='<name_of_scheduler_and_options>' "
				echo ""	
				echo "-- OUTPUTS FOR INDIVIDUAL RUN: "
				echo "" 
   				echo " - qc.pdf: single subject QC report "
				echo " - qc.json: single subject QC and data info"
    			echo " - vols_no_outliers.txt: text file that contains the list of the non-outlier volumes (based on eddy residuals)"
				echo ""
				echo "-- OUTPUTS FOR GROUP RUN: "
				echo "" 
   				echo " - group_qc.pdf: single subject QC report "
				echo " - group_qc.db: database"  
				echo ""
				echo ""  
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  dwidenseparcellation - Executes the Diffusion Parcellation Script (DWIDenseParcellation.sh) via the MNAP connector wrapper
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
		# ParcellationFile  # e.g. ${TOOLS}/${MNAPREPO}/library/data/parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii"
		########################################## OUTPUTS #########################################

		# Outputs will be *pconn.nii files located here:
		# DWIOutput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"
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
		
		# Generate timestamp for logs and scripts
		TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
		Suffix="$CASE_$TimeStamp"
			
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
			--waytotal="${WayTotal}" \
			--outname="${OutName}" \
			--overwrite="${Overwrite}" >> "$LogFolder"/DWIDenseParcellation_"$Suffix".log
		else
			# - Clean prior command 
			rm -f "$LogFolder"/DWIDenseParcellation_"$Suffix".sh &> /dev/null	
			# - Echo full command into a script
			echo "DWIDenseParcellation.sh \
			--path=${StudyFolder} \
			--subject=${CASE} \
			--matrixversion=${MatrixVersion} \
			--parcellationfile=${ParcellationFile} \
			--waytotal=${WayTotal} \
			--outname=${OutName} \
			--overwrite=${Overwrite}" > "$LogFolder"/DWIDenseParcellation_"$Suffix".sh
			
			# - Make script executable 
			chmod 770 "$LogFolder"/DWIDenseParcellation_"$Suffix".sh
			cd ${LogFolder}
			
			# - Send to scheduler 
			gmri schedule command="${LogFolder}/DWIDenseParcellation_${Suffix}.sh" \
			settings="${Scheduler}" \
			output="stdout:${LogFolder}/DWIDenseParcellation.${Suffix}.output.log|stderr:${LogFolder}/DWIDenseParcellation.${Suffix}.error.log" \
			workdir="${LogFolder}"
			
			echo "--------------------------------------------------------------"
			echo "Data successfully submitted" 
			echo "Scheduler Name and Options: $Scheduler"
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
				echo "--function=<function_name>                            Name of function"
				echo "--path=<study_folder>                                 Path to study data folder"
				echo "--subject=<comma_separated_list_of_cases>             List of subjects to run"
				echo "--matrixversion=<matrix_version_value>                Matrix solution verion to run parcellation on; e.g. 1 or 3"
				echo "--parcellationfile=<file_for_parcellation>            Specify the absolute path of the file you want to use for parcellation"
				echo "--outname=<name_of_output_pconn_file>                 Specify the suffix output name of the pconn file"
				echo "--scheduler=<name_of_cluster_scheduler_and_options>   A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                      e.g. for SLURM the string would look like this: "
				echo "                                                      --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
				echo "--overwrite=<clean_prior_run>                        Delete prior run for a given subject"
				echo "--waytotal=<use_waytotal_normalized_data>            Use the waytotal normalized version of the DWI dense connectome. Default: [no]"
				echo ""
				echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='dwidenseparcellation' \ "
				echo "--subjects='100206' \ "
				echo "--matrixversion='3' \ "
				echo "--parcellationfile='{$TOOLS}/${MNAPREPO}/connector/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
				echo ""	
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='dwidenseparcellation' \ "
				echo "--subjects='100206' \ "
				echo "--matrixversion='3' \ "
				echo "--parcellationfile='{$TOOLS}/${MNAPREPO}/connector/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  dwiseedtractography - Executes the Diffusion Seed Tractography Script (DWIDenseSeedTractography.sh) via the MNAP connector wrapper
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
		# DWIOutput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"
		# Parse General Parameters
		# QUEUE="$QUEUE" # Cluster queue name with GPU nodes - e.g. anticevic-gpu
		
		StudyFolder="$StudyFolder"
		CASE="$CASE"
		MatrixVersion="$MatrixVersion"
		SeedFile="$SeedFile"
		OutName="$OutName"
		DWIOutput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"
		mkdir "$DWIOutput"/log > /dev/null 2>&1
		LogFolder="$DWIOutput"/log
		Overwrite="$Overwrite"
		
		# Generate timestamp for logs and scripts
		TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
		Suffix="$CASE_$TimeStamp"
			
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
			--waytotal="${WayTotal}" \
			--outname="${OutName}" \
			--overwrite="${Overwrite}" >> "$LogFolder"/DWIDenseSeedTractography_"$Suffix".log
		else
			# - Clean prior command 
			rm -f "$LogFolder"/DWIDenseSeedTractography_"$Suffix".sh &> /dev/null	
			# - Echo full command into a script
			echo "DWIDenseSeedTractography.sh \
			--path=${StudyFolder} \
			--subject=${CASE} \
			--matrixversion=${MatrixVersion} \
			--seedfile=${SeedFile} \
			--waytotal=${WayTotal} \
			--outname=${OutName} \
			--overwrite=${Overwrite}" > "$LogFolder"/DWIDenseSeedTractography_"$Suffix".sh
			
			# - Make script executable 
			chmod 770 "$LogFolder"/DWIDenseSeedTractography_"$Suffix".sh
			cd ${LogFolder}
			
			# - Send to scheduler
			gmri schedule command="${LogFolder}/DWIDenseSeedTractography_${Suffix}.sh" \
			settings="${Scheduler}" \
			output="stdout:${LogFolder}/DWIDenseSeedTractography.${Suffix}.output.log|stderr:${LogFolder}/DWIDenseSeedTractography.${Suffix}.error.log" \
			workdir="${LogFolder}"
			
			echo "--------------------------------------------------------------"
			echo "Data successfully submitted" 
			echo "Scheduler Name and Options: $Scheduler"
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
				echo "			<study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<subject>_Conn<matrixversion>_<outname>.dconn.nii"
				echo "			 --> Dense connectivity seed tractography file"
				echo ""
				echo "			<study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<subject>_Conn<matrixversion>_<outname>_Avg.dscalar.nii"
				echo "			--> Dense scalar seed tractography file"
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "--function=<function_name>                           Name of function"
				echo "--path=<study_folder>                                Path to study data folder"
				echo "--subject=<comma_separated_list_of_cases>            List of subjects to run"
				echo "--matrixversion=<matrix_version_value>               Matrix solution verion to run parcellation on; e.g. 1 or 3"
				echo "--seedfile=<file_for_seed_reduction>                 Specify the absolute path of the seed file you want to use as a seed for dconn reduction"
				echo "--outname=<name_of_output_dscalar_file>              Specify the suffix output name of the dscalar file"
				echo "--scheduler=<name_of_cluster_scheduler_and_options>  A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                     e.g. for SLURM the string would look like this: "
				echo "                                                     --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
				echo "" 
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
				echo "--overwrite=<clean_prior_run>                        Delete prior run for a given subject"
				echo "--waytotal=<use_waytotal_normalized_data>            Use the waytotal normalized version of the DWI dense connectome. Default: [no]"
				echo ""
				echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='dwiseedtractography' \ "
				echo "--subjects='100206' \ "
				echo "--matrixversion='3' \ "
				echo "--seedfile='<study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz' \ "
				echo "--overwrite='no' \ "
				echo "--outname='Thalamus_Seed' \ "
				echo ""	
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='dwiseedtractography' \ "
				echo "--subjects='100206' \ "
				echo "--matrixversion='3' \ "
				echo "--seedfile='<study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz' \ "
				echo "--overwrite='no' \ "
				echo "--outname='Thalamus_Seed' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo ""
				echo "-- Example with interactive terminal:"
				echo ""
				echo "Interactive terminal run method not supported for this function"
				echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  computeboldfc - Executes Global Brain Connectivity (GBC) or seed-based functional connectivity (ComputeFunctionalConnectivity.sh) via the MNAP connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

computeboldfc() {

		# Requirements for this function
		# Connectome Workbench (v1.0 or above)
		
		########################################## INPUTS ########################################## 
		# BOLD data should be pre-processed and in CIFTI or NIFTI format
		########################################## OUTPUTS #########################################

		# Outputs will be files located in the location specified in the outputpath

		# -- Parse General Parameters
		StudyFolder="$StudyFolder"
		CASE="$CASE"
		InputFiles="$InputFiles"
		OutPath="$OutPathFC"
		OutName="$OutName"
		ExtractData="$ExtractData"

		# -- Parse additional parameters
		Calculation="$Calculation"		# --calculation=	
		RunType="$RunType"				# --runtype= 		
		FileList="$FileList"			# --flist=			
		IgnoreFrames="$IgnoreFrames"	# --ignore=			
		MaskFrames="$MaskFrames"		# --mask=		
		Covariance="$Covariance"		# --covariance=		
		TargetROI="$TargetROI"			# --target=			
		RadiusSmooth="$RadiusSmooth"	# --rsmooth=		
		RadiusDilate="$RadiusDilate"	# --rdilate=		
		GBCCommand="$GBCCommand"		# --command=		
		Verbose="$Verbose"				# --verbose=		
		ComputeTime="$ComputeTime"		# --time=			
		VoxelStep="$VoxelStep"			# --vstep=			
		ROIInfo="$ROIInfo"				# --roinfo=			
		FCCommand="$FCCommand"			# --options=		
		Method="$Method"				# --method=
		InputPath="$InputPath"			# --inputpath		
		
		# -- make sure individual runs default to the original input path location
		if [ "$OutPath" == "" ]; then
			OutPath="$StudyFolder/$CASE/$InputPath"
		fi
		
		if [ "$RunType" == "individual" ]; then
			OutPath="$StudyFolder/$CASE/$InputPath"
			TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
			Suffix="${CASE}_${TimeStamp}"
		fi
		
		if [ "$RunType" == "group" ]; then
			TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
			Suffix="GroupRun_${TimeStamp}"
  		fi
  	
			
		mkdir "$OutPath" > /dev/null 2>&1
		mkdir "$OutPath"/computeboldfc_log > /dev/null 2>&1
		
		LogFolder="$OutPath/computeboldfc_log"
		Overwrite="$Overwrite"

		if [ ${Calculation} == "seed" ]; then
			rm -f "$LogFolder"/ComputeFunctionalConnectivity_"$Suffix".sh &> /dev/null
			if [ "$Cluster" == 1 ]; then
				echo "Running locally on `hostname`"
				echo "Check log file output here: $LogFolder"
				echo "--------------------------------------------------------------"
				echo " ${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh \
				--path=${StudyFolder} \
				--calculation=${Calculation} \
				--runtype=${RunType} \
				--subject=${CASE} \
				--inputfiles=${InputFiles} \
				--inputpath=${InputPath} \
				--extractdata=${ExtractData} \
				--outname=${OutName} \
				--flist=${FileList} \
				--overwrite=${Overwrite} \
				--ignore=${IgnoreFrames} \
				--roinfo=${ROIInfo} \
				--options=${FCCommand} \
				--method=${Method} \
				--targetf=${OutPath} \
				--mask=${MaskFrames} \
				--covariance=${Covariance}" >> "$LogFolder"/ComputeFunctionalConnectivity_"$Suffix".log
			else			
				# - Echo full command into a script
				echo ""
				geho "Full Command:"
				geho "${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh --path=${StudyFolder} --calculation=${Calculation} --runtype=${RunType} --subject=${CASE} --inputfiles=${InputFiles} --inputpath=${InputPath} --extractdata=${ExtractData} --outname=${OutName} --flist=${FileList} --overwrite=${Overwrite} --ignore=${IgnoreFrames} --roinfo=${ROIInfo} --options=${FCCommand} --method=${Method} --targetf=${OutPath} --mask=${MaskFrames} --covariance=${Covariance}"
				echo ""	
				
				echo "${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh \
				--path=${StudyFolder} \
				--calculation=${Calculation} \
				--runtype=${RunType} \
				--subject=${CASE} \
				--inputfiles=${InputFiles} \
				--inputpath=${InputPath} \
				--extractdata=${ExtractData} \
				--outname=${OutName} \
				--flist=${FileList} \
				--overwrite=${Overwrite} \
				--ignore=${IgnoreFrames} \
				--roinfo=${ROIInfo} \
				--options=${FCCommand} \
				--method=${Method} \
				--targetf=${OutPath} \
				--mask=${MaskFrames} \
				--covariance=${Covariance}" >> "$LogFolder"/ComputeFunctionalConnectivity_"$Suffix".sh
				
				# - Make script executable 
				chmod 770 "$LogFolder"/ComputeFunctionalConnectivity_"$Suffix".sh
				
				# - Send to scheduler 
				cd "$LogFolder"  		
				gmri schedule command="${LogFolder}/ComputeFunctionalConnectivity_${Suffix}.sh" \
				settings="${Scheduler}" \
				output="stdout:${LogFolder}/ComputeFunctionalConnectivity.${Suffix}.output.log|stderr:${LogFolder}/ComputeFunctionalConnectivity.${Suffix}.error.log" \
				workdir="${LogFolder}"
				
				echo "--------------------------------------------------------------"
				echo "Data successfully submitted" 
				echo "Scheduler Name and Options: $Scheduler"
				echo "Check output logs here: $LogFolder"
				echo "--------------------------------------------------------------"
				echo ""
			fi
		fi

		if [ ${Calculation} == "gbc" ]; then		
			rm -f "$LogFolder"/ComputeFunctionalConnectivity_gbc_"$Suffix".sh &> /dev/null
			if [ "$Cluster" == 1 ]; then
				echo "Running locally on `hostname`"
				echo "Check log file output here: $LogFolder"
				echo "--------------------------------------------------------------"
				
				echo " ${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh \
				--path=${StudyFolder} \
				--calculation=${Calculation} \
				--runtype=${RunType} \
				--subject=${CASE} \
				--inputfiles=${InputFiles} \
				--inputpath=${InputPath} \
				--extractdata=${ExtractData} \
				--outname=${OutName} \
				--flist=${FileList} \
				--overwrite=${Overwrite} \
				--ignore=${IgnoreFrames} \
				--target=${TargetROI} \
				--command=${GBCCommand} \
				--targetf=${OutPath} \
				--mask=${MaskFrames} \
				--rsmooth=${RadiusSmooth} \
				--rdilate=${RadiusDilate} \
				--verbose=${Verbose} \
				--time=${ComputeTime} \
				--vstep=${VoxelStep} \
				--covariance=${Covariance}" >> "$LogFolder"/ComputeFunctionalConnectivity_gbc_"$Suffix".log
			else 
				# - Echo full command into a script
				echo ""
				geho "Full Command:"
				geho "${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh --path=${StudyFolder} --calculation=${Calculation} --runtype=${RunType} --subject=${CASE} --inputfiles=${InputFiles} --inputpath=${InputPath} --extractdata=${ExtractData} --flist=${FileList} --outname=${OutName} --overwrite=${Overwrite} --ignore=${IgnoreFrames} --target=${TargetROI} --command=${GBCCommand} --targetf=${OutPath} --mask=${MaskFrames} --rsmooth=${RadiusSmooth} --rdilate=${RadiusDilate} --verbose=${Verbose} --time=${ComputeTime} --vstep=${VoxelStep} --covariance=${Covariance}"
				echo ""				
				echo "${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh \
				--path=${StudyFolder} \
				--calculation=${Calculation} \
				--runtype=${RunType} \
				--subject=${CASE} \
				--inputfiles=${InputFiles} \
				--inputpath=${InputPath} \
				--extractdata=${ExtractData} \
				--flist=${FileList} \
				--outname=${OutName} \
				--overwrite=${Overwrite} \
				--ignore=${IgnoreFrames} \
				--target=${TargetROI} \
				--command=${GBCCommand} \
				--targetf=${OutPath} \
				--mask=${MaskFrames} \
				--rsmooth=${RadiusSmooth} \
				--rdilate=${RadiusDilate} \
				--verbose=${Verbose} \
				--time=${ComputeTime} \
				--vstep=${VoxelStep} \
				--covariance=${Covariance}" >> "$LogFolder"/ComputeFunctionalConnectivity_gbc_"$Suffix".sh 
				
				# - Make script executable 
				chmod 770 "$LogFolder"/ComputeFunctionalConnectivity_gbc_"$Suffix".sh &> /dev/null
				
				# - Send to scheduler     		
				cd "$LogFolder"  		
				gmri schedule command="${LogFolder}/ComputeFunctionalConnectivity_gbc_${Suffix}.sh" \
				settings="${Scheduler}" \
				output="stdout:${LogFolder}/ComputeFunctionalConnectivity_gbc.${Suffix}.output.log|stderr:${LogFolder}/ComputeFunctionalConnectivity_gbc.${Suffix}.error.log" \
				workdir="${LogFolder}"
				
				echo "--------------------------------------------------------------"
				echo "Data successfully submitted" 
				echo "Scheduler Name and Options: $Scheduler"
				echo "Check output logs here: $LogFolder"
				echo "--------------------------------------------------------------"
				echo ""
			fi
		fi
		
}

show_usage_computeboldfc() {
				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function implements Global Brain Connectivity (GBC) or seed-based functional connectivity (FC) on the dense or parcellated (e.g. Glasser parcellation)."
				echo ""
				echo ""
				echo "For more detailed documentation run <help fc_ComputeGBC3>, <help gmrimage.mri_ComputeGBC> or <help fc_ComputeSeedMapsMultiple> inside matlab"
				echo ""
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "--function=<function_name>                            Name of function"
				echo "--scheduler=<name_of_cluster_scheduler_and_options>   A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                      e.g. for SLURM the string would look like this: "
				echo "                                                      --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
				echo "" 
				echo "-- REQUIRED GENERAL PARMETERS FOR A GROUP RUN:"
				echo ""
				echo "--calculation=<type_of_calculation>           Run <seed> or <gbc> calculation for functional connectivity."
				echo "--runtype=<type_of_run>                       Run calculation on a <list> (requires a list input), on <individual> subjects (requires manual specification) or a <group> of individual subjects (equivalent to a list, but with manual specification)"
				echo "--flist=<subject_list_file>                   Specify *.list file of subject information. If specified then --inputfile, --subject --inputpath --inputdatatype and --outname are omitted"
				echo "--targetf=<path_for_output_file>              Specify the absolute path for group result output folder. If using --runtype='individual' the output will default to --inputpath location for each individual subject"
				echo "--ignore=<frames_to_ignore>                   The column in *_scrub.txt file that matches bold file to be used for ignore mask. All if empty. Default is [] "
				echo "--mask=<which_frames_to_use>                  An array mask defining which frames to use (1) and which not (0). All if empty. If single value is specified then this number of frames is skipped." # inmask for fc_ComputeSeedMapsMultiple
				echo ""
				echo "-- REQUIRED GENERAL PARMETERS FOR AN INDIVIDUAL SUBJECT RUN:"
				echo ""
				echo "--path=<study_folder>                              Path to study data folder"
				echo "--subject=<list_of_cases>                          List of subjects to run"
				echo "--inputfiles=<files_to_compute_connectivity_on>    Specify the comma separated file names you want to use (e.g. /bold1_Atlas_MSMAll.dtseries.nii,bold2_Atlas_MSMAll.dtseries.nii)"
				echo "--inputpath=<path_for_input_file>                  Specify path of the file you want to use relative to the master study folder and subject directory (e.g. /images/functional/)"
				echo "--outname=<name_of_output_file>                    Specify the suffix name of the output file name"  
				echo ""
				echo "-- OPTIONAL GENERAL PARAMETERS: "	
				echo ""
				echo "--overwrite=<clean_prior_run>                      Delete prior run for a given subject"
				echo "--extractdata=<save_out_the_data_as_as_csv>        Specify if you want to save out the matrix as a CSV file (only available if the file is a ptseries) "
				echo "--covariance=<compute_covariance>                  Whether to compute covariances instead of correlations (true / false). Default is [false]"
				echo ""
				echo "-- REQUIRED GBC PARMETERS:"
				echo ""
				echo "--target=<which_roi_to_use>                        Array of ROI codes that define target ROI [default: FreeSurfer cortex codes]"
				echo "--rsmooth=<smoothing_radius>                       Radius for smoothing (no smoothing if empty). Default is []"
				echo "--rdilate=<dilation_radius>                        Radius for dilating mask (no dilation if empty). Default is []"
				echo "--command=<type_of_gbc_to_run>                     Specify the the type of gbc to run. This is a string describing GBC to compute. E.g. 'mFz:0.1|mFz:0.2|aFz:0.1|aFz:0.2|pFz:0.1|pFz:0.2' "
				echo ""
				echo "                   	> mFz:t  ... computes mean Fz value across all voxels (over threshold t) "
				echo "                   	> aFz:t  ... computes mean absolute Fz value across all voxels (over threshold t) "
				echo "                   	> pFz:t  ... computes mean positive Fz value across all voxels (over threshold t) "
				echo "                   	> nFz:t  ... computes mean positive Fz value across all voxels (below threshold t) "
				echo "                   	> aD:t   ... computes proportion of voxels with absolute r over t "
				echo "                     	> pD:t   ... computes proportion of voxels with positive r over t "
				echo "                     	> nD:t   ... computes proportion of voxels with negative r below t "
				echo "                     	> mFzp:n ... computes mean Fz value across n proportional ranges "
				echo "                     	> aFzp:n ... computes mean absolute Fz value across n proportional ranges "
				echo "                     	> mFzs:n ... computes mean Fz value across n strength ranges "
				echo "                    	> pFzs:n ... computes mean Fz value across n strength ranges for positive correlations "
				echo "                     	> nFzs:n ... computes mean Fz value across n strength ranges for negative correlations "
				echo "                     	> mDs:n  ... computes proportion of voxels within n strength ranges of r "
				echo "                     	> aDs:n  ... computes proportion of voxels within n strength ranges of absolute r "
				echo "                     	> pDs:n  ... computes proportion of voxels within n strength ranges of positive r "
				echo "                     	> nDs:n  ... computes proportion of voxels within n strength ranges of negative r "  
				echo ""
				echo "-- OPTIONAL GBC PARMETERS:"
				echo "" 
				echo "--verbose=<print_output_verbosely>                Report what is going on. Default is [false]"
				echo "--time=<print_time_needed>                        Whether to print timing information. [false]"
				echo "--vstep=<how_many_voxels>                         How many voxels to process in a single step. Default is [1200]"
				echo ""
				echo "-- REQUIRED SEED FC PARMETERS:"
				echo ""
				echo "--roinfo=<roi_seed_files>                         An ROI file for the seed connectivity "
				echo ""
				echo "-- OPTIONAL SEED FC PARMETERS: "
				echo ""
				echo "--method=<method_to_get_timeseries>               Method for extracting timeseries - 'mean' or 'pca' Default is ['mean'] "
				echo "--options=<calculations_to_save>                  A string defining which subject files to save. Default assumes all [''] "
				echo ""
				echo "			> r ... save map of correlations "
				echo "			> f ... save map of Fisher z values "
				echo "			> cv ... save map of covariances "
				echo "			> z ... save map of Z scores "
				echo ""
				echo ""
				echo "-- Seed and GBC FC Examples with flagged parameters for submission to the scheduler:"
				echo ""
				echo "- Example for seed calculation for each individual subject:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='computeboldfc' \ "
				echo "--calculation='seed' \ "
				echo "--runtype='individual' \ "
				echo "--subjects='100206,100610,101006' \ "
				echo "--inputfiles='bold2143_Atlas_MSMAll_hp2000_clean_demean-100f.dtseries.nii' \ "
				echo "--inputpath='/images/functional' \ "
				echo "--overwrite='yes' \ "
				echo "--extractdata='yes' \ "
				echo "--roinfo='/gpfs/project/fas/n3/Studies/BSNIP/fcMRI/roi/Thal.FSL.MNI152.CIFTI.Atlas.names' \ "
				echo "--outname='bold2143AtlasMSMAllhp2000cleanhpssdemean' \ "
				echo "--ignore='' \ "
				echo "--options='' \ "
				echo "--method='' \ "
				echo "--targetf='' \ "
				echo "--mask='5' \ "
				echo "--covariance='false' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo ""
				echo "- Example for seed calculation for a group of three subjects with the absolute path for a target folder:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='computeboldfc' \ "
				echo "--calculation='seed' \ "
				echo "--runtype='group' \ "
				echo "--subjects='100206,100610,101006' \ "
				echo "--inputfiles='bold2143_Atlas_MSMAll_hp2000_clean_demean-100f.dtseries.nii' \ "
				echo "--inputpath='/images/functional' \ "
				echo "--overwrite='yes' \ "
				echo "--extractdata='yes' \ "
				echo "--roinfo='/gpfs/project/fas/n3/Studies/BSNIP/fcMRI/roi/Thal.FSL.MNI152.CIFTI.Atlas.names' \ "
				echo "--outname='bold2143AtlasMSMAllhp2000cleanhpssdemean' \ "
				echo "--ignore='' \ "
				echo "--options='' \ "
				echo "--method='' \ "
				echo "--targetf='/gpfs/project/fas/n3/Studies/Connectome/fcMRI/results_udvarsme_surface_testing' \ "
				echo "--mask='5' \ "
				echo "--covariance='false' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo ""
				echo "- Example for gbc calculation for each individual subject:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='computeboldfc' \ "
				echo "--calculation='gbc' \ "
				echo "--runtype='individual' \ "
				echo "--subjects='100206,100610,101006' \ "
				echo "--inputfiles='bold2143_Atlas_MSMAll_hp2000_clean_demean-100f.dtseries.nii' \ "
				echo "--inputpath='/images/functional' \ "
				echo "--overwrite='yes' \ "
				echo "--extractdata='yes' \ "
				echo "--outname='bold2143AtlasMSMAllhp2000cleanhpssdemean' \ "
				echo "--ignore='' \ "
				echo "--command='mFz:' \ "
				echo "--targetf='' \ "
				echo "--mask='5' \ "
				echo "--target='' \ "
				echo "--rsmooth='0' \ "
				echo "--rdilate='0' \ "
				echo "--verbose='true' \ "
				echo "--time='true' \ "
				echo "--vstep='5000' \ "
				echo "--covariance='false' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo ""
				echo "- Example for gbc calculation for a group of three subjects with the absolute path for a target folder:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='computeboldfc' \ "
				echo "--calculation='gbc' \ "
				echo "--runtype='group' \ "
				echo "--subjects='100206,100610,101006' \ "
				echo "--inputfiles='bold2143_Atlas_MSMAll_hp2000_clean_demean-100f.dtseries.nii' \ "
				echo "--inputpath='/images/functional' \ "
				echo "--overwrite='yes' \ "
				echo "--extractdata='yes' \ "
				echo "--outname='bold2143AtlasMSMAllhp2000cleanhpssdemean' \ "
				echo "--ignore='' \ "
				echo "--command='mFz:' \ "
				echo "--targetf='/gpfs/project/fas/n3/Studies/Connectome/fcMRI/results_udvarsme_surface_testing' \ "
				echo "--mask='5' \ "
				echo "--target='' \ "
				echo "--rsmooth='0' \ "
				echo "--rdilate='0' \ "
				echo "--verbose='true' \ "
				echo "--time='true' \ "
				echo "--vstep='5000' \ "
				echo "--covariance='false' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  structuralparcellation - Executes the Structural Parcellation Script (StructuralParcellation.sh) via the MNAP connector wrapper
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
		# ParcellationFile  # e.g. /${TOOLS}/${MNAPREPO}/library/data/parcellations/Cole_GlasserNetworkAssignment_Final/final_LR_FIXICA_noGSR_reassigned.dlabel.nii"
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
		
		# Generate timestamp for logs and scripts
		TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
		Suffix="$OutName_$TimeStamp"
		
		if [ "$Cluster" == 1 ]; then
			echo "Running locally on `hostname`"
			echo "Check log file output here: $LogFolder"
			echo "--------------------------------------------------------------"
			echo ""
			${TOOLS}/${MNAPREPO}/connector/functions/StructuralParcellation.sh \
			--path="${StudyFolder}" \
			--subject="${CASE}" \
			--inputdatatype="${InputDataType}" \
			--parcellationfile="${ParcellationFile}" \
			--overwrite="${Overwrite}" \
			--outname="${OutName}" \
			--extractdata="${ExtractData}" >> "$LogFolder"/StructuralParcellation_"$Suffix".log
		else
			echo "${TOOLS}/${MNAPREPO}/connector/functions/StructuralParcellation.sh \
			--path=${StudyFolder} \
			--subject=${CASE} \
			--inputdatatype=${InputDataType} \
			--parcellationfile=${ParcellationFile} \
			--overwrite=${Overwrite} \
			--outname=${OutName} \
			--extractdata=${ExtractData}" > "$LogFolder"/StructuralParcellation_"$Suffix".sh &> /dev/null
			# - Make script executable 
			chmod 770 "$LogFolder"/StructuralParcellation_"$Suffix".sh &> /dev/null
			cd ${LogFolder}     		
			# - Send to scheduler
			gmri schedule command="${LogFolder}/StructuralParcellation_${Suffix}.sh" \
			settings="${Scheduler}" \
			output="stdout:${LogFolder}/StructuralParcellation.${Suffix}.output.log|stderr:${LogFolder}/StructuralParcellation.${Suffix}.error.log" \
			workdir="${LogFolder}"
			echo "--------------------------------------------------------------"
			echo "Data successfully submitted" 
			echo "Scheduler Name and Options: $Scheduler"
			echo "Check output logs here: $LogFolder"
			echo "--------------------------------------------------------------"
			echo ""
		fi
}

show_usage_structuralparcellation () {
				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function implements parcellation on the dense cortical thickness OR myelin files using a whole-brain parcellation [ e.g. Glasser parcellation with subcortical labels included ]"
				echo ""
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "--function=<function_name>                             Name of function"
				echo "--path=<study_folder>                                  Path to study data folder"
				echo "--subject=<comma_separated_list_of_cases>              List of subjects to run"
				echo "--inputdatatype=<type_of_dense_data_for_input_file>    Specify the type of data for the input file [ e.g. MyelinMap_BC or corrThickness ] "
				echo "--parcellationfile=<file_for_parcellation>             Specify path of the file you want to use for parcellation relative to the master study folder [ e.g. /images/functional/bold1_Atlas_MSMAll_hp2000_clean.dtseries.nii ]"
				echo "--outname=<name_of_output_pconn_file>                  Specify the suffix output name of the pconn file"
				echo "--scheduler=<name_of_cluster_scheduler_and_options>    A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                         e.g. for SLURM the string would look like this: "
				echo "                                                         --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
				echo "" 
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
				echo "--overwrite=<clean_prior_run>                          Delete prior run for a given subject"
				echo "--extractdata=<save_out_the_data_as_as_csv>            Specify if you want to save out the matrix as a CSV file"
				echo ""
				echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='structuralparcellation' \ "
				echo "--subjects='100206' \ "
				echo "--inputdatatype='MyelinMap_BC' \ "
				echo "--parcellationfile='{$TOOLS}/${MNAPREPO}/connector/templates/Parcellations/Cole_GlasserNetworkAssignment_Final/final_LR_FIXICA_noGSR_reassigned.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions' \ "
				echo "--extractdata='yes' "
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='structuralparcellation' \ "
				echo "--subjects='100206' \ "
				echo "--inputdatatype='MyelinMap_BC' \ "
				echo "--parcellationfile='$TOOLS/${MNAPREPO}/connector/templates/Parcellations/Cole_GlasserNetworkAssignment_Final/final_LR_FIXICA_noGSR_reassigned.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions' \ "
				echo "--extractdata='yes' "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo "" 
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  boldparcellation - Executes the BOLD Parcellation Script (BOLDParcellation.sh) via the MNAP connector wrapper
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
		# SingleInputFile # Input for a specific file
		# InputPath # e.g. /images/functional/
		# InputDataType # e.g.dtseries
		# OutPath # e.g. /images/functional/
		# OutName # e.g. LR_Colelab_partitions_v1d_islands_withsubcortex
		# ParcellationFile  # e.g. {$TOOLS}/${MNAPREPO}/library/data/parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii"
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
		SingleInputFile="$SingleInputFile"
		OutPath="$OutPath"
		OutName="$OutName"
		ComputePConn="$ComputePConn"
		UseWeights="$UseWeights"
		WeightsFile="$WeightsFile"
		ParcellationFile="$ParcellationFile"
		Cluster="$RunMethod"
		
		if [ -z "$SingleInputFile" ]; then
			BOLDOutput="$StudyFolder/$CASE/$OutPath"
		else
			BOLDOutput="$OutPath"
		fi
		
		ExtractData="$ExtractData"
		mkdir "$BOLDOutput"/boldparcellation_log > /dev/null 2>&1
		LogFolder="$BOLDOutput"/boldparcellation_log
		Overwrite="$Overwrite"
		
		# Generate timestamp for logs and scripts
		TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
		Suffix="$CASE_$TimeStamp"
		
		if [ "$Cluster" == 1 ]; then
			echo "Running locally on `hostname`"
			echo "Check log file output here: $LogFolder"
			echo "--------------------------------------------------------------"
			echo ""
			BOLDParcellation.sh \
			--path="${StudyFolder}" \
			--subject="${CASE}" \
			--inputfile="${InputFile}" \
			--singleinputfile="${SingleInputFile}" \
			--inputpath="${InputPath}" \
			--inputdatatype="${InputDataType}" \
			--parcellationfile="${ParcellationFile}" \
			--overwrite="${Overwrite}" \
			--outname="${OutName}" \
			--outpath="${OutPath}" \
			--computepconn="${ComputePConn}" \
			--extractdata="${ExtractData}" \
			--useweights="${UseWeights}" \
			--weightsfile="${WeightsFile}" >> "$LogFolder"/BOLDParcellation_"$Suffix".log
		else
			echo "BOLDParcellation.sh \
			--path=${StudyFolder} \
			--subject=${CASE} \
			--inputfile=${InputFile} \
			--singleinputfile=${SingleInputFile} \
			--inputpath=${InputPath} \
			--inputdatatype=${InputDataType} \
			--parcellationfile=${ParcellationFile} \
			--overwrite=${Overwrite} \
			--outname=${OutName} \
			--outpath=${OutPath} \
			--computepconn=${ComputePConn} \
			--extractdata=${ExtractData} \
			--useweights=${UseWeights} \
			--weightsfile=${WeightsFile}" > "$LogFolder"/BOLDParcellation_"$Suffix".sh &> /dev/null
			# - Make script executable 
			chmod 770 "$LogFolder"/BOLDParcellation_"$Suffix".sh &> /dev/null
			cd ${LogFolder}
			# - Send to scheduler     		
			gmri schedule command="${LogFolder}/BOLDParcellation_${Suffix}.sh" \
			settings="${Scheduler}" \
			output="stdout:${LogFolder}/BOLDParcellation.${Suffix}.output.log|stderr:${LogFolder}/BOLDParcellation.${Suffix}.error.log" \
			workdir="${LogFolder}"
			echo "--------------------------------------------------------------"
			echo "Data successfully submitted "
			echo "Scheduler Options: $Scheduler "
			echo "Check output logs here: $LogFolder "
			echo "--------------------------------------------------------------"
			echo ""
		fi
}

show_usage_boldparcellation() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function implements parcellation on the BOLD dense files using a whole-brain parcellation [ e.g.Glasser parcellation with subcortical labels included ] "
				echo ""
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "--function=<function_name>                             Name of function"
				echo "--path=<study_folder>                                  Path to study data folder"
				echo "--subject=<comma_separated_list_of_cases>              List of subjects to run"
				echo "--inputfile=<file_to_compute_parcellation_on>          Specify the name of the file you want to use for parcellation [ e.g. bold1_Atlas_MSMAll_hp2000_clean ]"
				echo "--inputpath=<path_for_input_file>                      Specify path of the file you want to use for parcellation relative to the master study folder and subject directory [ e.g. /images/functional/ ]"
				echo "--inputdatatype=<type_of_dense_data_for_input_file>    Specify the type of data for the input file [ e.g. dscalar or dtseries ]"
				echo "--parcellationfile=<file_for_parcellation>             Specify path of the file you want to use for parcellation relative to the master study folder [ e.g. /images/functional/bold1_Atlas_MSMAll_hp2000_clean.dtseries.nii ]"
				echo "--outname=<name_of_output_pconn_file>                  Specify the suffix output name of the pconn file"
				echo "--outpath=<path_for_output_file>                       Specify the output path name of the pconn file relative to the master study folder [ e.g. /images/functional/ ]"
				echo "--scheduler=<name_of_cluster_scheduler_and_options>    A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                       e.g. for SLURM the string would look like this: "
				echo "                                                       --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
				echo ""
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
				echo "--singleinputfile=<parcellate_single_file>                     Parcellate only a single file in any location using an absolute path point to this file. Individual flags are not needed [ --subject, --path, -inputfile, --inputpath ]"
				echo "--overwrite=<clean_prior_run>                                  Delete prior run"
				echo "--computepconn=<specify_parcellated_connectivity_calculation>	 Specify if a parcellated connectivity file should be computed <pconn>. This is done using covariance and correlation [ e.g. yes; default is set to no ]"
				echo "--useweights=<clean_prior_run>                                 If computing a  parcellated connectivity file you can specify which frames to omit [ e.g. yes' or no; default is set to no ] "
				echo "--weightsfile=<location_and_name_of_weights_file>              Specify the location of the weights file relative to the master study folder [ e.g. /images/functional/movement/bold1.use ]"
				echo "--extractdata=<save_out_the_data_as_as_csv>                    Specify if you want to save out the matrix as a CSV file"
				echo ""
				echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='boldparcellation' \ "
				echo "--subjects='<comma_separated_list_of_cases>' \ "
				echo "--inputfile='bold1_Atlas_MSMAll_hp2000_clean' \ "
				echo "--inputpath='/images/functional/' \ "
				echo "--inputdatatype='dtseries' \ "
				echo "--parcellationfile='{$TOOLS}/${MNAPREPO}/connector/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
				echo "--outpath='/images/functional/' \ "
				echo "--computepconn='yes' \ "
				echo "--extractdata='yes' \ "
				echo "--useweights='no' \ "
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "mnap --path='<study_folder>' \ "
				echo "--function='boldparcellation' \ "
				echo "--subjects='100206' \ "
				echo "--inputfile='bold1_Atlas_MSMAll_hp2000_clean' \ "
				echo "--inputpath='/images/functional/' \ "
				echo "--inputdatatype='dtseries' \ "
				echo "--parcellationfile='$TOOLS/${MNAPREPO}/connector/templates/Parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
				echo "--outpath='/images/functional/' \ "
				echo "--computepconn='yes' \ "
				echo "--extractdata='yes' \ "
				echo "--useweights='no' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
 				echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  roiextract - Executes the ROI Extraction Script (ROIExtract.sh) via the MNAP connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

roiextract() {

		# Requirements for this function
		########################################## INPUTS ########################################## 
		# BOLD data should in CIFTI or NIFTI format
		# Mandatory input parameters:
		# StudyFolder # e.g. /gpfs/project/fas/n3/Studies/Connectome
		# Subject	  # e.g. 100206
		# InputFile # e.g. bold1_Atlas_MSMAll_hp2000_clean.dtseries.nii
		# SingleInputFile # Input for a specific file
		# InputPath # e.g. /images/functional/
		# OutPath # e.g. /images/functional/
		# OutName # e.g. LR_Colelab_partitions_v1d_islands_withsubcortex
		# ROIFile  # e.g. {$TOOLS}/${MNAPREPO}/library/data/parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii"
		########################################## OUTPUTS #########################################
		
		# Outputs will be files located in the location specified in the outputpath
		# Parse General Parameters
		InputFile="$InputFile"
		OutPath="$OutPath"
		OutName="$OutName"
		ROIFile="$ROIInputFile"
		StudyFolder="$StudyFolder"
		CASE="$CASE"
		ROIFileSubjectSpecific="$ROIFileSubjectSpecific"
		SingleInputFile="$SingleInputFile"
		Cluster="$RunMethod"
		
		if [ -z "$SingleInputFile" ]; then
			OutPath="$StudyFolder/$CASE/$OutPath"
		else
			OutPath="$OutPath"
			InputFile="$SingleInputFile"
		fi
		
		if [ "$ROIFileSubjectSpecific" == "no" ]; then
			ROIFile="$ROIFile"
		else
			ROIFile="$StudyFolder/$CASE/$ROIFile"
		fi
		
		ExtractData="$ExtractData"
		mkdir "$OutPath"/roiextraction_log > /dev/null 2>&1
		LogFolder="$OutPath"/roiextraction_log
		Overwrite="$Overwrite"
		
		# Generate timestamp for logs and scripts
		TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
		Suffix="$OutName_$TimeStamp"
		
		if [ "$Cluster" == 1 ]; then
			echo "Running locally on `hostname`"
			echo "Check log file output here: $LogFolder"
			echo "--------------------------------------------------------------"
			echo ""
			/$TOOLS/${MNAPREPO}/connector/functions/ROIExtract.sh \
			--roifile="${ROIFile}" \
			--inputfile="${InputFile}" \
			--outpath="${OutPath}" \
			--outname="${OutName}" >> "$LogFolder"/extract_ROIs_"$Suffix".log
		else
			echo "/$TOOLS/${MNAPREPO}/connector/functions/ROIExtract.sh \
			--roifile='${ROIFile}' \
			--inputfile='${InputFile}' \
			--outdir='${OutPath}' \		
			--outname='${OutName}'" > "$LogFolder"/extract_ROIs_"$Suffix".sh &> /dev/null
			
			# - Make script executable 
			chmod 770 "$LogFolder"/extract_ROIs_"$Suffix".sh &> /dev/null
			cd ${LogFolder}
			
			# - Send to scheduler     		
			gmri schedule command="${LogFolder}/extract_ROIs_${Suffix}.sh" \
			settings="${Scheduler}" \
			output="stdout:${LogFolder}/extract_ROIs.${Suffix}.output.log|stderr:${LogFolder}/extract_ROIs.${Suffix}.error.log" \
			workdir="${LogFolder}"
			echo "--------------------------------------------------------------"
			echo "Data successfully submitted "
			echo "Scheduler Options: $Scheduler "
			echo "Check output logs here: $LogFolder "
			echo "--------------------------------------------------------------"
			echo ""
		fi
}

show_usage_roiextract() {

				echo ""
				echo "DESCRIPTION:"
				echo ""
				echo " This function calls ROIExtract.sh and extracts data from an input file for every ROI in a given template file."
				echo " The function needs a matching file type for the ROI input and the data input (i.e. both NIFTI or CIFTI)."
				echo " It assumes that the template ROI file indicates each ROI in a single volume via unique scalar values."
				echo ""
				echo ""
				echo "REQUIRED PARMETERS (for single input file):"
				echo ""
				echo "--function=<function_name>                 Name of function"
				echo "--singleinputfile=<file_to_be_extracted>   Extract data from a single file in any location using an absolute path point to this file"
				echo "--roifile=<roi_template_file>              Specify path to the ROI template file (either a NIFTI or a CIFTI with distinct scalar values per ROI) [e.g. /gpfs/project/fas/n3/software/MNAP/library/data/parcellations/GlasserParcellation/Q1-Q6_RelatedParcellation210.LR.CorticalAreas_dil_Colors.32k_fs_LR_subcortexfilled.dlabel.nii]"
				echo "--outpath=<path_for_output_file>           Specify the absolute path to the directory in which to save output file"
				echo "--outname=<name_of_output_file>            Specify base name of the output .csv saved in outpath"
				echo " "
				echo "-- OUTPUT FORMAT:"
				echo ""
				echo "<output_name>.csv	  <-- matrix with one ROI per row and one column per frame/volume in singleinputfile"
				echo ""
				echo ""
				echo "OPTIONAL PARMETERS:"
				echo ""
				echo "--scheduler=<name_of_cluster_scheduler_and_options> A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                    ==> e.g. for SLURM the string would look like this: "
				echo "                                                    --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' " 
				echo "--overwrite=<clean_prior_run>                       Delete prior run"
				echo ""
				echo "Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "mnap --path='<path_to_study_folder>' \ "
				echo "--function='roiextract' \ "
				echo "--singleinputfile='<path_to_inputfile>' \ "
				echo "--roifile='<path_to_roifile>' \ "
				echo "--outpath='<output_path>' \ "
				echo "--outname='<output_name>' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
 				echo ""
}

# ------------------------------------------------------------------------------------------------------
#  fsldtifit - Executes the dtifit script from FSL (needed for probabilistic tractography)
# ------------------------------------------------------------------------------------------------------

fsldtifit() {

	mkdir ${StudyFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/dtifit_log > /dev/null 2>&1
	LogFolder=${StudyFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/dtifit_log
		
	# -- Check if overwrite flag was set
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
		# Generate timestamp for logs and scripts
		TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
		Suffix="$CASE_$TimeStamp"	
		rm "$LogFolder"/fsldtifit_${Suffix}.sh &> /dev/null
		DtiFitCommand="dtifit --data=${StudyFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./data --out=${StudyFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./dti --mask=${StudyFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./nodif_brain_mask --bvecs=${StudyFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./bvecs --bvals=${StudyFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./bvals"
		geho "Running the following command"
		geho "${DtiFitCommand}"
		echo ""
		echo "${DtiFitCommand}" >> "$LogFolder"/fsldtifit_${Suffix}.sh &> /dev/null
		# - Make script executable 
		chmod 770 "$LogFolder"/fsldtifit_${Suffix}.sh &> /dev/null
		
		if [ "$Cluster" == 1 ]; then
			eval ${DtiFitCommand} >> "$LogFolder"/fsldtifit_${Suffix}.log
		fi
		if [ "$Cluster" == 2 ]; then
			# -- Send to scheduler 
			cd ${StudyFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/
			gmri schedule command="${DtiFitCommand}" \
			settings="${Scheduler}" \
			output="stdout:${LogFolder}/fsldtifit.${Suffix}.output.log|stderr:${LogFolder}/fsldtifit.${Suffix}.error.log" \
			workdir="${StudyFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/"
			
			echo "--------------------------------------------------------------"
			echo "Data successfully submitted" 
			echo "Scheduler Name and Options: $Scheduler"
			echo "Check output logs here: $LogFolder"
			echo "--------------------------------------------------------------"
			echo ""
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
				echo "--function=<function_name>                           Name of function"
				echo "--path=<study_folder>                                Path to study data folder"
				echo "--subjects=<comma_separated_list_of_cases>           List of subjects to run"
				echo "--overwrite=<clean_prior_run>                        Delete prior run for a given subject"
				echo "--scheduler=<name_of_cluster_scheduler_and_options>  A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                     e.g. for SLURM the string would look like this: "
				echo "                                                     --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
				echo "" 
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "mnap --path='<path_to_study_subjects_folder>' \ "
				echo "--subjects='<case_id>' \ "
				echo "--function='fsldtifit' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo "--overwrite='yes'"
				echo ""
}

# ------------------------------------------------------------------------------------------------------
#  fslbedpostxgpu - Executes the bedpostx_gpu code from FSL (needed for probabilistic tractography)
# ------------------------------------------------------------------------------------------------------

fslbedpostxgpu() {

		# -- Establish global directory paths
		T1wDiffFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion
		BedPostXFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion.bedpostX
		LogFolder="$BedPostXFolder"/logs
		Overwrite="$Overwrite"
		
		# -- hard-coded cuda call for HPC clusters
		module load GPU/Cuda/6.5 > /dev/null 2>&1 
		
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
		if [ "$Rician" == "no" ] || [ "$Rician" == "NO" ]; then
			echo ""
			geho "Omitting --rician flag"
			RicianFlag=""
			echo ""
		else
			echo ""
			geho "Setting --rician flag"
			RicianFlag="--rician"
			echo ""			
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
		
		reho "Prior BedpostX run not found or incomplete for $CASE. Setting up new run..."
		echo ""
		
		# Generate log folder
		mkdir ${BedPostXFolder} > /dev/null 2>&1
		mkdir ${LogFolder} > /dev/null 2>&1
		
		# Generate timestamp for logs and scripts
		TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
		Suffix="${CASE}_${TimeStamp}"
		
		if [ "$Cluster" == 1 ]; then
			echo "Running bedpostx_gpu locally on `hostname`"
			echo "Check log file output here: $LogFolder"
			echo "--------------------------------------------------------------"
			echo ""
			if [ -f "$T1wDiffFolder"/grad_dev.nii.gz ]; then
				${FSLGPUBinary}/bedpostx_gpu_noscheduler "$T1wDiffFolder"/. -n "$Fibers" -model "$Model" -b "$Burnin" -g "$RicianFlag" >> "$LogFolder"/bedpostX_"$Suffix".log
			else	
				${FSLGPUBinary}/bedpostx_gpu_noscheduler "$T1wDiffFolder"/. -n "$Fibers" -model "$Model" -b "$Burnin" "$RicianFlag" >> "$LogFolder"/bedpostX_"$Suffix".log
			fi
		fi
		
		if [ "$Cluster" == 2 ]; then
			# - Clean prior command 
			rm -f "$LogFolder"/bedpostX_"$Suffix".sh &> /dev/null	
			
			# - Echo full command into a script
			if [ -f "$T1wDiffFolder"/grad_dev.nii.gz ]; then
				echo "${FSLGPUBinary}/bedpostx_gpu_noscheduler ${T1wDiffFolder}/. -n ${Fibers} -model ${Model} -b ${Burnin} -g ${RicianFlag}" > "$LogFolder"/bedpostX_"$Suffix".sh
			else
				echo "${FSLGPUBinary}/bedpostx_gpu_noscheduler ${T1wDiffFolder}/. -n ${Fibers} -model ${Model} -b ${Burnin} ${RicianFlag}" > "$LogFolder"/bedpostX_"$Suffix".sh
			fi
			
			# - Make script executable 
			chmod 770 "$LogFolder"/bedpostX_"$Suffix".sh
			cd ${LogFolder}
			
			# - Send to scheduler 
			gmri schedule command="${LogFolder}/bedpostX_${Suffix}.sh" \
			settings="${Scheduler}" \
			output="stdout:${LogFolder}/bedpostX.${Suffix}.output.log|stderr:${LogFolder}/bedpostX.${Suffix}.error.log" \
			workdir="${LogFolder}"			
			
			echo "--------------------------------------------------------------"
			echo "Data successfully submitted" 
			echo "Scheduler Name and Options: $Scheduler"
			echo "Check output logs here: $LogFolder"
			echo "--------------------------------------------------------------"
			echo ""
		fi
}

show_usage_fslbedpostxgpu() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function runs the FSL bedpostx_gpu processing using a GPU-enabled node or via a GPU-enabled queue if using the scheduler option."
				echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing and completed diffusion processing: "
				echo ""
				echo " <study_folder>/<case>/hcp/<case>/Diffusion ---> DWI data needs to be here"
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "--function=<function_name>                            Name of function"
				echo "--path=<study_folder>                                 Path to study data folder"
				echo "--subjects=<comma_separated_list_of_cases>            List of subjects to run"
				echo "--fibers=<number_of_fibers>                           Number of fibres per voxel, default 3"
				echo "--model=<deconvolution_model>                         Deconvolution model. 1: with sticks, 2: with sticks with a range of diffusivities <default>, 3: with zeppelins"
				echo "--burnin=<burnin_period_value>                        Burnin period, default 1000"
				echo "--rician=<set_rician_value>                           <yes> or <no>. Default is yes"
				echo "--overwrite=<clean_prior_run>                         Delete prior run for a given subject"
				echo "--scheduler=<name_of_cluster_scheduler_and_options>   A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                        e.g. for SLURM the string would look like this: "
				echo "                                                         --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
				echo "														* Note: You need to specify a GPU-enabled queue or partition"
				echo "" 
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "mnap --path='<path_to_study_subjects_folder>' \ "
				echo "--function='fslbedpostxgpu' \ "
				echo "--subjects='<case_id>' \ "
				echo "--fibers='3' \ "
				echo "--burnin='3000' \ "
				echo "--model='3' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo "--overwrite='yes'"
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
		#fslsub="$Scheduler"
		#fsl_sub."$fslsub" -Q "$QUEUE" "$AutoPtxFolder"/autoPtx "$StudyFolder" "$Subject" "$BpxFolder"
		#fsl_sub."$fslsub" -Q "$QUEUE" -j <jid> "$AutoPtxFolder"/Prepare_for_Display.sh $StudyFolder/$Subject/MNINonLinear/Results/autoptx 0.005 1
		#fsl_sub."$fslsub" -Q "$QUEUE" -j <jid> "$AutoPtxFolder"/Prepare_for_Display.sh $StudyFolder/$Subject/MNINonLinear/Results/autoptx 0.005 0
		
		# - Send to scheduler     		
		#gmri schedule command="ComputeFunctionalConnectivity_gbc_${CASE}.sh" \
		#settings="${Scheduler}" \
		#output="stdout:ComputeFunctionalConnectivity_gbc.output.log|stderr:ComputeFunctionalConnectivity_gbc.error.log" \
		#workdir="${LogFolder}"
		
		echo "--------------------------------------------------------------"
		echo "Data successfully submitted" 
		echo "Scheduler Name and Options: $Scheduler"
		echo "Check output logs here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""
	fi
}

show_usage_autoptx() {
				echo ""
				echo "-- DESCRIPTION: "
				echo ""
				echo "USAGE PENDING... "
				echo ""
}

# -------------------------------------------------------------------------------------------------------------------
#  pretractographydense - Executes the HCP Pretractography code [ Stam's implementation for all grayordinates ]
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
			PreTracCommand="${ScriptsFolder}/PreTractography.sh ${RunFolder} ${CASE} 0 "
			# - Send to scheduler     		
			cd ${LogFolder}
			gmri schedule command="${PreTracCommand}" \
			settings="${Scheduler}" \
			output="stdout:${LogFolder}/pretractographydense.output.log|stderr:${LogFolder}/pretractographydense.error.log" \
			workdir="${LogFolder}"
			echo ""
			echo "--------------------------------------------------------------"
			echo "Data successfully submitted" 
			echo "Scheduler Name and Options: $Scheduler"
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
				echo "--function=<function_name>                              Name of function"
				echo "--path=<study_folder>                                   Path to study data folder"
				echo "--subjects=<comma_separated_list_of_cases>              List of subjects to run"
				echo "--scheduler=<name_of_cluster_scheduler_and_options>     A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                        e.g. for SLURM the string would look like this: "
				echo "                                                        --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
				echo "" 
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "mnap --path='<path_to_study_subjects_folder>' \ "
				echo "--subjects='<case_id>' \ "
				echo "--function='pretractographydense' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo "--scheduler='LSF'"
				echo ""
}

# --------------------------------------------------------------------------------------------------------------------------------------------------
#  probtrackxgpudense - Executes the HCP Matrix1 and / or 3 code and generates WB dense connectomes (Stam's implementation for all grayordinates)
# --------------------------------------------------------------------------------------------------------------------------------------------------

probtrackxgpudense() {
		
		# -- Set general parameters
		ScriptsFolder="$HCPPIPEDIR_dMRITracFull"/Tractography_gpu_scripts
		ResultsFolder="$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/Tractography
		RunFolder="$StudyFolder"/"$CASE"/hcp/
		NsamplesMatrixOne="$NsamplesMatrixOne"
		NsamplesMatrixThree="$NsamplesMatrixThree"
		minimumfilesize=100000000
		
		# -- Generate the results and log folders
		mkdir "$ResultsFolder"  &> /dev/null
		
		# -- Generate timestamp for logs and scripts
		TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
		Suffix="${CASE}_${TimeStamp}"
		
		# -------------------------------------------------
		# -- Check if Matrix 1 or 3 flag set 
		# -------------------------------------------------
		
		if [ "$MatrixOne" == "yes" ]; then
			MNumber="1"
			if [ "$NsamplesMatrixOne" == "" ];then NsamplesMatrixOne=10000; fi
		fi
		
		if [ "$MatrixThree" == "yes" ]; then
			MNumber="3"
			if [ "$NsamplesMatrixOne" == "" ];then NsamplesMatrixThree=3000; fi
		fi
		
		if [ "$MatrixOne" == "yes" ] && [ "$MatrixThree" == "yes" ]; then
			MNumber="1 3"
		fi
		
		# -------------------------------------------------
		# -- Do work for Matrix 1 or 3
		# -------------------------------------------------
			
		for MNum in $MNumber; do
			
			if [ "$MNum" == "1" ]; then NSamples="$NsamplesMatrixOne"; fi
			if [ "$MNum" == "3" ]; then NSamples="$NsamplesMatrixThree"; fi
			
			LogFolder="$ResultsFolder"/Mat${MNum}_logs
			mkdir "$LogFolder"  &> /dev/null
		
			# -- Check of overwrite flag was set
			if [ "$Overwrite" == "yes" ]; then
				echo ""
				reho " --- Removing existing Probtrackxgpu Matrix${MNum} dense run for $CASE..."
				echo ""
				rm -f "$ResultsFolder"/Conn${MNum}.dconn.nii.gz &> /dev/null
			fi
			
			# -- Check for Matrix completion
			echo ""
			geho "Checking if ProbtrackX Matrix ${MNum} and dense connectome was completed on $CASE..."
			echo ""
			
			# -- Check if the file even exists
			if [ -f "$ResultsFolder"/Conn${MNum}.dconn.nii.gz ]; then
				
				# -- Set file sizes to check for completion
				actualfilesize=`wc -c < "$ResultsFolder"/Conn${MNum}.dconn.nii.gz` > /dev/null 2>&1  		
				
				# -- Then check if Matrix run is complete based on size
				if [ $(echo "$actualfilesize" | bc) -ge $(echo "$minimumfilesize" | bc) ]; then > /dev/null 2>&1
					echo ""
					cyaneho "DONE -- ProbtrackX Matrix ${MNum} solution and dense connectome was completed for $CASE"
					cyaneho "To re-run set overwrite flag to 'yes'"
					cyaneho "Check prior output logs here: $LogFolder"
					echo ""
					echo "--------------------------------------------------------------"
					echo ""
				fi
			
			else
				
				# -- If run is incomplete perform run for Matrix
				echo ""
				geho "ProbtrackX Matrix ${MNum} solution and dense connectome incomplete for $CASE. Starting run with $NSamples samples..."
				echo ""
		
				# -- submit script locally
				if [ "$Cluster" == 1 ]; then
					echo "Running probtrackxgpudense locally on `hostname`"
					echo "Check log file output here: $LogFolder"
					echo "--------------------------------------------------------------"
					echo ""
					"$ScriptsFolder"/RunMatrix${MNum}_NoScheduler.sh "$RunFolder" "$CASE" "$Nsamples" "$SchedulerType" >> "$LogFolder"/Matrix${MNum}_"$Suffix".log
				fi
				
				if [ "$Cluster" == 2 ]; then
					# -- Clean prior command 
					rm -f "$LogFolder"/Matrix${MNum}_"$Suffix".sh &> /dev/null	
					
					# -- Echo full command into a script
					echo "${ScriptsFolder}/RunMatrix${MNum}_NoScheduler.sh ${RunFolder} ${CASE} ${Nsamples} ${SchedulerType}" > "$LogFolder"/Matrix${MNum}_"$Suffix".sh
			
					# -- Make script executable 
					chmod 770 "$LogFolder"/Matrix${MNum}_"$Suffix".sh
					cd ${LogFolder}
					
					# -- Send to scheduler 
					gmri schedule command="${LogFolder}/Matrix${MNum}_${Suffix}.sh" \
					settings="${Scheduler}" \
					output="stdout:${LogFolder}/Matrix${MNum}.${Suffix}.output.log|stderr:${LogFolder}/Matrix${MNum}.${Suffix}.error.log" \
					workdir="${LogFolder}"			
					
					echo "--------------------------------------------------------------"
					echo "Data successfully submitted" 
					echo "Scheduler Name and Options: $Scheduler"
					echo "Check output logs here: $LogFolder"
					echo "--------------------------------------------------------------"
					echo ""
				fi
			fi
		done
			
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
				echo "--function=<function_name>                            Name of function"
				echo "--path=<study_folder>                                 Path to study data folder"
				echo "--subjects=<comma_separated_list_of_cases>            List of subjects to run"
				echo "--scheduler=<name_of_cluster_scheduler>               A string for the cluster scheduler (e.g. LSF, PBS or SLURM) without any options (they are hard coded in the sub-script calls)"
				echo "--overwrite=<clean_prior_run>                         Delete a prior run for a given subject [Note: this will delete only the Matrix run specified by the -omatrix flag]"
				echo "--omatrix1=<matrix1_model>                            Specify if you wish to run matrix 1 model [yes or omit flag]"
				echo "--omatrix3=<matrix3_model>                            Specify if you wish to run matrix 3 model [yes or omit flag]"
				echo "--nsamplesmatrix1=<Number_of_Samples_for_Matrix1>     Number of samples - default=10000" 
				echo "--nsamplesmatrix3=<Number_of_Samples_for_Matrix3>     Number of samples - default=3000" 
				echo "" 
				echo "-- GENERIC PARMETERS SET BY DEFAULT:"
				echo ""
				echo "--loopcheck --forcedir --fibthresh=0.01 -c 0.2 --sampvox=2 --randfib=1 -S 2000 --steplength=0.5"
				echo ""
				echo "** The function calls either of these based on the --omatrix1 and --omatrix3 flags: "
				echo ""
				echo "    $HCPPIPEDIR_dMRITracFull/Tractography_gpu_scripts/RunMatrix1.sh"
				echo "    $HCPPIPEDIR_dMRITracFull/Tractography_gpu_scripts/RunMatrix3.sh"
				echo ""
				echo "    --> both are cluster-aware and send the jobs to the GPU-enabled queue. They do not work interactively."
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler (needs to be GPU-enabled):"
				echo ""
				echo "mnap --path='<path_to_study_subjects_folder>' \ "
				echo "--subjects='<case_id>' \ "
				echo "--function='probtrackxgpudense' \ "
				echo "--scheduler='<name_of_scheduler>' \ "
				echo "--omatrix1='yes' \ " 
				echo "--nsamplesmatrix1='10000' \ "
				echo "--overwrite='no'" 
				echo ""				
}

# ------------------------------------------------------------------------------------------------------------------------------
#  Sync data from AWS buckets - customized for HCP
# -------------------------------------------------------------------------------------------------------------------------------

awshcpsync() {

mkdir "$StudyFolder"/aws.logs &> /dev/null
cd "$StudyFolder"/aws.logs
if [ "$RunMethod" == "2" ]; then
	echo "Dry run"
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
if [ "$RunMethod" == "1" ]; then
	echo "Syncing"
	if [ -d "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear ]; then
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality" &> /dev/null
		time aws s3 sync s3:/"$Awsuri"/"$CASE"/"$Modality" "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality"/ >> awshcpsync_"$CASE"_"$Modality"_`date +%Y-%m-%d-%H-%M-%S`.log 
	else
		mkdir "$StudyFolder"/"$CASE" &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE" &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality" &> /dev/null
		echo "$Awsuri"/"$CASE"/"$Modality"
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
				echo "--function=<function_name>                    Name of function"
				echo "--path=<study_folder>                         Path to study data folder"
				echo "--subjects=<comma_separated_list_of_cases>    List of subjects to run"
				echo "--modality=<modality_to_sync>                 Which modality or folder do you want to sync [e.g. MEG, MNINonLinear, T1w]"
				echo "--awsuri=<aws_uri_location>                   Enter the AWS URI [e.g. /hcp-openaccess/HCP_900]"
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "mnap --path='<path_to_study_subjects_folder>' --subjects='<case_id>' --function='awshcpsync' --modality='T1w' --awsuri='/hcp-openaccess/HCP_900'"
				echo ""				
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
		echo ""
		geho "--- Generating ${Modality} QC scene: ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
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
	
	# -- Check if modality is BOLD
	if [ "$Modality" == "BOLD" ]; then
		for BOLD in $BOLDS; 
		do
			# -- Generate QC statistics for a given BOLD
			geho "--- Generating QC statistics commands for BOLD ${BOLD} on ${CASE}..."
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
			Com1="rsync -aWH ${TemplateFolder}/atlases/HCP/S900* ${OutPath}/ &> /dev/null"
			Com2="rsync -aWH ${TemplateFolder}/atlases/MNITemplates/MNI152_*_0.7mm.nii.gz ${OutPath}/ &> /dev/null"		
			
			# -- Setup naming conventions before generating scene
			Com3="cp ${TemplateFolder}/scenes/qc/TEMPLATE.${Modality}.QC.wb.scene ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
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
				echo "Job Information:"
				rm -f "$LogFolder"/"$CASE"_ComQUEUE_"$BOLD".sh &> /dev/null
				echo "$ComQUEUE" >> "$LogFolder"/"$CASE"_ComQUEUE_"$BOLD".sh
				chmod 770 "$LogFolder"/"$CASE"_ComQUEUE_"$BOLD".sh
				cd ${LogFolder}
				
				gmri schedule command="${LogFolder}/${CASE}_ComQUEUE_${BOLD}.sh" settings="${Scheduler}" output="stdout:${LogFolder}/qcpreproc.output.log|stderr:${LogFolder}/qcpreproc.error.log" workdir="${LogFolder}" 
				echo ""
				echo "---------------------------------------------------------------------------------"
				echo "Data successfully submitted" 
				echo "Scheduler Name and Options: $Scheduler"
				echo "Check output logs here: $LogFolder"
				echo "---------------------------------------------------------------------------------"
				echo ""
			fi
		done
	
	else
	
		# -- Generate a QC scene file appropriate for each subject for each modality
		
		# -- Rsync over template files for a given modality		
		Com1="rsync -aWH ${TemplateFolder}/atlases/HCP/S900* ${OutPath}/ &> /dev/null"
		Com2="rsync -aWH ${TemplateFolder}/atlases/MNITemplates/MNI152_*_0.7mm.nii.gz ${OutPath}/ &> /dev/null"
		Com3="rsync -aWH ${TemplateFolder}/scenes/qc/TEMPLATE.${Modality}.QC.wb.scene ${OutPath} &> /dev/null"
		
		# -- Setup naming conventions before generating scene
		Com4="cp ${OutPath}/TEMPLATE.${Modality}.QC.wb.scene ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
		Com5="sed -i -e 's|DUMMYPATH|$StudyFolder|g' ${OutPath}/${CASE}.${Modality}.QC.wb.scene" 
		Com6="sed -i -e 's|DUMMYCASE|$CASE|g' ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
		
		# -- Check if modality is DWI
		if [ "$Modality" == "DWI" ]; then
			
			# -- Split the data and setup 1st and 2nd volumes for visualization
			Com6a="fslsplit ${StudyFolder}/${CASE}/hcp/${CASE}/T1w/${DWIPath}/${DWIData}.nii.gz ${StudyFolder}/${CASE}/hcp/${CASE}/T1w/${DWIPath}/${DWIData}_split -t"
			Com6b="fslmaths ${StudyFolder}/${CASE}/hcp/${CASE}/T1w/${DWIPath}/${DWIData}_split0000.nii.gz -mul ${StudyFolder}/${CASE}/hcp/${CASE}/T1w/${DWIPath}/nodif_brain_mask.nii.gz ${StudyFolder}/${CASE}/hcp/${CASE}/T1w/${DWIPath}/${DWIData}_split1_brain"
			Com6c="fslmaths ${StudyFolder}/${CASE}/hcp/${CASE}/T1w/${DWIPath}/${DWIData}_split0001.nii.gz -mul ${StudyFolder}/${CASE}/hcp/${CASE}/T1w/${DWIPath}/nodif_brain_mask.nii.gz ${StudyFolder}/${CASE}/hcp/${CASE}/T1w/${DWIPath}/${DWIData}_split2_brain"
			
			# -- Clean split volumes
			Com6d="rm -f ${StudyFolder}/${CASE}/hcp/${CASE}/T1w/${DWIPath}/${DWIData}_split0*  &> /dev/null"
			
			# -- Setup naming conventions for DWI before generating scene
			Com6e="sed -i -e 's|DUMMYDWIPATH|$DWIPath|g' ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
			# -- Check if legacy setting is YES
			if [ "$DWILegacy" == "yes" ]; then
				unset "$DWIDataLegacy" >/dev/null 2>&1
				DWIDataLegacy="${CASE}_${DWIData}"
				Com6f="sed -i -e 's|DUMMYDWIDATA|$DWIDataLegacy|g' ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
			else
				Com6f="sed -i -e 's|DUMMYDWIDATA|$DWIData|g' ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
			fi
			
			Com6="$Com6; $Com6a; $Com6b; $Com6c; $Com6d; $Com6e; $Com6f"

			# --------------------------------------------------
			# -- Check if DTIFIT and BEDPOSTX flags are set
			# --------------------------------------------------
			
			# -- if dtifit qc is selected then generate dtifit scene
			if [ "$DtiFitQC" == "yes" ]; then
				echo ""
				geho "--- QC for FSL dtifit requested. Checking if dtifit was completed..."
				echo ""
				
				# -- check if dtifit is done
				minimumfilesize=100000
				if [ -a "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/${DWIPath}/dti_FA.nii.gz ]; then 
					actualfilesize=$(wc -c <"$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/${DWIPath}/dti_FA.nii.gz)
				else
					actualfilesize="0"
				fi
				
				if [ $(echo "$actualfilesize" | bc) -gt $(echo "$minimumfilesize" | bc) ]; then
					echo ""
					geho "    --> FSL dtifit results found here: ${StudyFolder}/${CASE}/hcp/${CASE}/T1w/${DWIPath}/"
					echo ""
					
					# -- replace DWI scene specifications with the dtifit results
					Com6g1="cp ${OutPath}/${CASE}.${Modality}.QC.wb.scene ${OutPath}/${CASE}.${Modality}.dtifit.QC.wb.scene"
					Com6g2="sed -i -e 's|1st Frame|dti_FA|g' ${OutPath}/${CASE}.${Modality}.dtifit.QC.wb.scene"
					Com6g3="sed -i -e 's|2nd Frame|dti_L3|g' ${OutPath}/${CASE}.${Modality}.dtifit.QC.wb.scene"
					Com6g4="sed -i -e 's|data_split1_brain.nii.gz|dti_FA.nii.gz|g' ${OutPath}/${CASE}.${Modality}.dtifit.QC.wb.scene"
					Com6g5="sed -i -e 's|data_split2_brain.nii.gz|dti_L3.nii.gz|g' ${OutPath}/${CASE}.${Modality}.dtifit.QC.wb.scene"
					# -- combine dtifit commands
					Com6g="$Com6g1; $Com6g2; $Com6g3; $Com6g4; $Com6g5"
					# -- Combine DWI commands
					Com6="$Com6; $Com6g"
				else
					reho "    --> FSL dtifit not found for $CASE. Skipping dtifit QC request. Check dtifit results. "
				fi
			fi
				
			# -- if bedpostx qc is selected then generate bedpostx scene
			if [ "$BedpostXQC" == "yes" ]; then
				echo ""
				geho "--- QC for FSL BedpostX requested. Checking if BedpostX was completed..."
				echo ""
				
				# -- Check if the file even exists
				if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion.bedpostX/merged_f1samples.nii.gz ]; then
					# -- Set file sizes to check for completion
					minimumfilesize=20000000
					actualfilesize=`wc -c < "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion.bedpostX/merged_f1samples.nii.gz` > /dev/null 2>&1  		
					filecount=`ls "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion.bedpostX/merged_*nii.gz | wc | awk {'print $1'}`
				
					# -- Then check if run is complete based on file count
					if [ "$filecount" == 9 ]; then
						# -- Then check if run is complete based on file size
						if [ $(echo "$actualfilesize" | bc) -ge $(echo "$minimumfilesize" | bc) ]; then > /dev/null 2>&1
							echo ""
							geho "    --> BedpostX outputs found and completed here: ${StudyFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/"
							echo ""
							# -- replace DWI scene specifications with the dtifit results
							Com6h1="cp ${OutPath}/${CASE}.${Modality}.QC.wb.scene ${OutPath}/${CASE}.${Modality}.bedpostx.QC.wb.scene"
							Com6h2="sed -i -e 's|1st Frame|mean d diffusivity|g' ${OutPath}/${CASE}.${Modality}.bedpostx.QC.wb.scene"
							Com6h3="sed -i -e 's|2nd Frame|mean f anisotropy|g' ${OutPath}/${CASE}.${Modality}.bedpostx.QC.wb.scene"
							Com6h4="sed -i -e 's|$DWIPath/data_split1_brain.nii.gz|Diffusion.bedpostX/mean_dsamples.nii.gz|g' ${OutPath}/${CASE}.${Modality}.bedpostx.QC.wb.scene"
							Com6h5="sed -i -e 's|$DWIPath/data_split2_brain.nii.gz|Diffusion.bedpostX/mean_fsumsamples.nii.gz|g' ${OutPath}/${CASE}.${Modality}.bedpostx.QC.wb.scene"
							# -- combine dtifit commands
							Com6h="$Com6h1; $Com6h2; $Com6h3; $Com6h4; $Com6h5"
							# -- Combine DWI commands
							Com6="$Com6; $Com6h"
						fi
					fi
				else 
					echo ""
					reho "    --> FSLBedpostX outputs missing or incomplete for $CASE. Skipping BedpostX QC request. Check BedpostX results."
					echo ""
					BedpostXQC="no"
				fi
			fi
		
			# -- if eddy qc is selected then create hard link to eddy qc pdf
			if [ "$EddyQCPDF" == "yes" ]; then
				echo ""
				geho "--- QC for FSL EDDY requested. Checking if EDDY QC was completed..."
				echo ""
				# -- Then check if eddy qc is completed
				if [ -f ${StudyFolder}/${CASE}/hcp/${CASE}/Diffusion/eddy/eddy_unwarped_images.qc/qc.pdf ]; then
					echo ""
					geho "    --> EDDY QC outputs found and completed here: ${StudyFolder}/${CASE}/hcp/${CASE}/Diffusion/eddy/eddy_unwarped_images.qc/qc.pdf"
					echo ""
					ln ${StudyFolder}/${CASE}/hcp/${CASE}/Diffusion/eddy/eddy_unwarped_images.qc/qc.pdf ${OutPath}/${CASE}.${Modality}.eddy.QC.pdf
				else
					echo ""
					reho "--- EDDY QC outputs missing or incomplete for $CASE. Skipping EDDY QC request. Check EDDY results."
					echo ""
				fi
			fi
		fi
				
		# -- Output image of the scene
		Com7="wb_command -show-scene ${OutPath}/${CASE}.${Modality}.QC.wb.scene 1 ${OutPath}/${CASE}.${Modality}.QC.png 1194 539"
		
		# -- Check if dtifit and bedpostx QC is requested
		if [ "$DtiFitQC" == "yes" ]; then
			Com7a="wb_command -show-scene ${OutPath}/${CASE}.${Modality}.dtifit.QC.wb.scene 1 ${OutPath}/${CASE}.${Modality}.dtifit.QC.png 1194 539"
			Com7="$Com7; $Com7a"
		fi
		if [ "$BedpostXQC" == "yes" ]; then
				Com7b="wb_command -show-scene ${OutPath}/${CASE}.${Modality}.bedpostx.QC.wb.scene 1 ${OutPath}/${CASE}.${Modality}.bedpostx.QC.png 1194 539"
				Com7="$Com7; $Com7b"
		fi
				
		# -- Clean templates and files for next subject
		Com8="rm ${OutPath}/${CASE}.${Modality}.QC.wb.scene-e &> /dev/null"
		Com9="rm ${OutPath}/TEMPLATE.${Modality}.QC.wb.scene &> /dev/null"
		Com10="rm -f ${OutPath}/data_split*"
		
		# -- Combine all the calls into a single command
		ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com8; $Com9; $Com10"
				
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
			# -- prep scheduler script
			echo "Job Information:"
			rm -f "$LogFolder"/"$CASE"_ComQUEUE.sh &> /dev/null
			echo "$ComQUEUE" >> "$LogFolder"/"$CASE"_ComQUEUE.sh
			chmod 700 "$LogFolder"/"$CASE"_ComQUEUE.sh
			cd ${LogFolder}
			# -- scheduler command
			gmri schedule command="${LogFolder}/${CASE}_ComQUEUE.sh" settings="${Scheduler}" \
			output="stdout:${LogFolder}/qcpreproc.output.log|stderr:${LogFolder}/qcpreproc.error.log" \
			workdir="${LogFolder}" 
			# -- echo command details
			echo ""
			echo "---------------------------------------------------------------------------------"
			echo "Data successfully submitted" 
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
				echo "--function=<function_name>                  Name of function"
				echo "--path=<study_folder>                       Path to study data folder"
				echo "--subjects=<list_of_cases>                  List of subjects to run, separated by commas"
				echo "--modality=<input_modality_for_qc>          Specify the modality to perform QC on [Supported: T1w, T2w, myelin, BOLD, DWI]"
				echo "--scheduler=<name_of_cluster_scheduler_and_options>     A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
				echo "                                                               e.g. for SLURM the string would look like this: "
				echo "                                                                    --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
				echo "" 
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
				echo "--overwrite=<clean_prior_run>                    Delete prior QC run"
				echo "--templatefolder=<path_for_the_template_folder>  Specify the output path name of the template folder (default: $TOOLS/${MNAPREPO}/library/data/templates)"
				echo "--outpath=<path_for_output_file>                 Specify the output path name of the QC folder"
				echo "--dwipath=<path_for_dwi_data>                    Specify the input path for the DWI data [may differ across studies; e.g. Diffusion or Diffusion or Diffusion_DWI_dir74_AP_b1000b2500]"
				echo "--dwidata=<file_name_for_dwi_data>               Specify the file name for DWI data [may differ across studies; e.g. data or DWI_dir74_AP_b1000b2500_data]"
				echo "--dtifitqc=<visual_qc_for_dtifit>                Specify if dtifit visual QC should be completed [e.g. yes or no]"
				echo "--bedpostxqc=<visual_qc_for_bedpostx>            Specify if BedpostX visual QC should be completed [e.g. yes or no]"
				echo "--eddyqcpdf=<pdf_qc_for_eddy>                    Specify if EDDY PDF QC should be linked into QC folder [e.g. yes or no]"
				echo "--dwilegacy=<dwi_data_processed_via_legacy_pipeline>     Specify if DWI data was processed via legacy pipelines [e.g. yes or no]"
				echo "--bolddata=<file_names_for_bold_data>                    Specify the file names for BOLD data separated by comma [may differ across studies; e.g. 1, 2, 3 or BOLD_1 or rfMRI_REST1_LR,rfMRI_REST2_LR]"
				echo "--boldsuffix=<file_name_for_bold_data>                   Specify the file name for BOLD data [may differ across studies; e.g. Atlas or MSMAll]"
				echo "--skipframes=<number_of_initial_frames_to_discard_for_bold_qc>   Specify the number of initial frames you wish to exclude from the BOLD QC calculation"
				echo ""
				echo ""
				echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "mnap --path='<path_to_study_subjects_folder>' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='<list_of_cases>' \ "
				echo "--outpath='<path_for_output_file> \ "
				echo "--templatefolder='<path_for_the_template_folder>' \ "
				echo "--modality='<input_modality_for_qc>'"
				echo "--overwrite='no' \ "
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "mnap --path='<path_to_study_subjects_folder>' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='<list_of_cases>' \ "
				echo "--outpath='<path_for_output_file> \ "
				echo "--templatefolder='<path_for_the_template_folder>' \ "
				echo "--modality='<input_modality_for_qc>'"
				echo "--overwrite='no' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo "" 			
				echo ""
				echo "-- Complete examples for each supported modality:"
				echo ""
				echo ""
				echo "# -- T1 QC"
				echo "mnap --path='<path_to_study_subjects_folder>' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='01_S0301_00_2015-02-23,01_S0301_00_2015-02-24' \ "
				echo "--outpath='<path_for_output_file> \ "
				echo "--templatefolder='<path_for_the_template_folder>' \ "
				echo "--modality='T1w' \ "
				echo "--overwrite='yes' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo ""
				echo "# -- T2 QC"
				echo "mnap --path='<path_to_study_subjects_folder>' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='<list_of_cases>' \ "
				echo "--outpath='<path_for_output_file> \ "
				echo "--templatefolder='<path_for_the_template_folder>' \ "
				echo "--modality='T2w' \ "
				echo "--overwrite='yes' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo ""
				echo "# -- Myelin QC"
				echo "mnap --path='<path_to_study_subjects_folder>' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='<list_of_cases>' \ "
				echo "--outpath='<path_for_output_file> \ "
				echo "--templatefolder='<path_for_the_template_folder>' \ "
				echo "--modality='myelin' \ "
				echo "--overwrite='yes' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo ""
				echo "# -- DWI QC "
				echo "mnap --path='<path_to_study_subjects_folder>' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='<list_of_cases>' \ "
				echo "--templatefolder='<path_for_the_template_folder>' \ "
				echo "--modality='DWI' \ "
				echo "--outpath='<path_for_output_file> \ "
				echo "--dwilegacy='yes' \ "
				echo "--dwidata='<file_name_for_dwi_data>' \ "
				echo "--dwipath='<path_for_dwi_data>' \ "
				echo "--overwrite='yes' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo ""
				echo "# -- BOLD QC"
				echo "mnap --path='<path_to_study_subjects_folder>' \ "
				echo "--function='qcpreproc' \ "
				echo "--subjects='<list_of_cases>' \ "
				echo "--outpath='<path_for_output_file> \ "
				echo "--templatefolder='<path_for_the_template_folder>' \ "
				echo "--modality='BOLD' \ "
				echo "--bolddata='1' \ "
				echo "--boldsuffix='Atlas' \ "
				echo "--overwrite='yes' \ "
				echo "--scheduler='<name_of_scheduler_and_options>' \ "
				echo ""
				echo ""
}

# ========================================================================================
# ======= SOURCE REPOS, SETUP LOG & PARSE COMMAND LINE INPUTS ACROSS FUNCTIONS ===========
# ========================================================================================

# ------------------------------------------------------------------------------
#  Set exit if error is reported (turn on for debugging)
# ------------------------------------------------------------------------------

# Setup this script such that if any command exits with a non-zero value, the 
# script itself exits and does not attempt any further processing.
# set -e

# ------------------------------------------------------------------------------
#  Load relevant libraries for logging and parsing options
# ------------------------------------------------------------------------------

source $HCPPIPEDIR/global/scripts/log.shlib  # Logging related functions
source $HCPPIPEDIR/global/scripts/opts.shlib # Command line option functions

# ------------------------------------------------------------------------------
#  Establish tool name for logging
# ------------------------------------------------------------------------------

log_SetToolName "mnap.sh"

# ------------------------------------------------------------------------------
#  Load Core Functions
# ------------------------------------------------------------------------------

# -- DESCRIPTION: parses the input command line for a specified command line option
# Input:
#   The first parameter is the command line option to look for.
#   The remaining parameters are the full list of flagged command line arguments

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

# -- DESCRIPTION: checks command line arguments for "--help" indicating that help has been requested
opts_CheckForHelpRequest() {
for fn in "$@" ; do
	if [ "$fn" = "--help" ]; then
		return 0
	fi
done
return 1
}

# -- DESCRIPTION: Generates a timestamp for the log exec call
timestamp() {
	echo "mnap.$1.`date "+%Y.%m.%d.%H.%M.%S"`.txt"
}

# -- DESCRIPTION: Checks for version
show_version() {
	MNAPVer=`cat ${TOOLS}/${MNAPREPO}/VERSION.md`
	echo ""
	reho "Multimodal Neuroimaging Analysis Pipeline (MNAP) Version: v${MNAPVer}"
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
	
	# -- check for input with question mark
	if [[ "$GmriFunctionToRun" =~ .*"?".* ]] && [ -z "$2" ]; then 
		# Set UsageInput variable to pass and remove question mark
		UsageInput=`echo ${GmriFunctionToRun} | cut -c 2-`
		# If no other input is provided print help
		echo ""
		show_version
		show_usage_gmri
		exit 0
	else		
	# -- check for input is function name with no other arguments
	if [[ "$GmriFunctionToRun" != *"-"* ]] && [ -z "$2" ]; then 	
		# Set UsageInput variable to pass and remove flag	
		UsageInput="$GmriFunctionToRun"
	  	# If no other input is provided print help
		echo ""
		show_version
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
#  Check if specific function help requested
# ------------------------------------------------------------------------------
	
	# -- get all the functions from the usage calls
	unset UsageName
	unset MNAPFunctions
	UsageName=`more ${TOOLS}/${MNAPREPO}/connector/mnap.sh | grep show_usage_${1}`
	MNAPFunctions=`more ${TOOLS}/${MNAPREPO}/connector/mnap.sh | grep "() {" | grep -v "usage" | grep -v "eho" | grep -v "opts_" | sed "s/() {//g" | sed ':a;N;$!ba;s/\n/ /g'`
	# -- check for input with double flags
	if [[ "$1" =~ .*--.* ]] && [ -z "$2" ]; then 
		Usage="$1"
		UsageInput=`echo ${Usage:2}`
			# -- check if input part of function list
			if [[ "$MNAPFunctions" != *${UsageInput}* ]]; then
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
			if [[ "$MNAPFunctions" != *${UsageInput}* ]]; then
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
			if [[ "$MNAPFunctions" != *${UsageInput}* ]]; then
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
			if [[ "$MNAPFunctions" != *${UsageInput}* ]]; then
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
	reho "----------------------------------------"
	reho "--- Running MNAP with flagged inputs ---"
	reho "----------------------------------------"
	echo ""
	
	# ------------------------------------------------------------------------------
	#  List of command line options across all functions
	# ------------------------------------------------------------------------------
	
	# -- First get function / command input (to harmonize input with gmri)
	FunctionInput=`opts_GetOpt "${setflag}function" "$@"` # function to execute
	CommamndInput=`opts_GetOpt "${setflag}command" "$@"` # function to execute
	
	# -- If input name uses 'command' instead of function set that to $FunctionToRun
	if [[ -z "$FunctionInput" ]]; then
		FunctionToRun="$CommamndInput"
	else
		FunctionToRun="$FunctionInput"		
	fi
	
	# -- general input flags
	StudyFolder=`opts_GetOpt "${setflag}path" $@` 																			# local folder to work on
	CASES=`opts_GetOpt "${setflag}subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` 	# list of input cases; removing comma or pipes
	Overwrite=`opts_GetOpt "${setflag}overwrite" $@` 																		# Clean prior run and starr fresh [yes/no]
	
	PRINTCOM=`opts_GetOpt "${setflag}printcom" $@` 																			# Option for printing the entire command	
	Scheduler=`opts_GetOpt "${setflag}scheduler" $@` 																		# Specify the type of scheduler to use 
	# -- if scheduler flag set then set RunMethod variable
	if [ ! -z "$Scheduler" ]; then
		RunMethod="2"
	else
		RunMethod="1"	
	fi
	
	# -- path options for FreeSurfer or MNAP
	FreeSurferHome=`opts_GetOpt "${setflag}hcp_freesurfer_home" $@` 														# Specifies homefolder for FreeSurfer binary to use
	APVersion=`opts_GetOpt "${setflag}version" $@` 																			# Specifies homefolder for FreeSurfer binary to use
	
	# -- create lists input flags
	ListGenerate=`opts_GetOpt "${setflag}listtocreate" $@` 																	# Which lists to generate
	Append=`opts_GetOpt "${setflag}append" $@` 																				# Append the list
	ListName=`opts_GetOpt "${setflag}listname" $@` 																			# Name of the list
	ParameterFile=`opts_GetOpt "${setflag}parameterfile" $@` 																# Use parameter file header
	ListFunction=`opts_GetOpt "${setflag}listfunction" $@` 																	# Which function to use to generate the list
	BOLDS=`opts_GetOpt "${setflag}bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'` 	# --bolddata=<file_names_for_bold_data>   Specify the file names for BOLD data separated by comma [may differ across studies; e.g. 1, 2, 3 or BOLD_1 or rfMRI_REST1_LR,rfMRI_REST2_LR]
	ParcellationFile=`opts_GetOpt "${setflag}parcellationfile" $@` 															# --parcellationfile=<file_for_parcellation>   Specify the absolute path of the file you want to use for parcellation (e.g. ${TOOLS}/${MNAPREPO}/library/data/parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)
	FileType=`opts_GetOpt "${setflag}filetype" $@` 																			# --filetype=<file_extension>
	BoldSuffix=`opts_GetOpt "${setflag}boldsuffix" $@` 																		# --boldsuffix=<bold_suffix>
	SubjectHCPFile=`opts_GetOpt "${setflag}subjecthcpfile" $@` 																# Use subject HCP File for appending the parameter list
	ListPath=`opts_GetOpt "${setflag}listpath" $@` 																			# Path of list to generate

	# -- hpcsync input flags
	NetID=`opts_GetOpt "${setflag}netid" $@` 																				# Yale NetID for cluster rsync command
	HCPStudyFolder=`opts_GetOpt "${setflag}clusterpath" $@` 																# cluster study folder for cluster rsync command
	Direction=`opts_GetOpt "${setflag}dir" $@` 																				# direction of rsync command (1 to cluster; 2 from cluster)
	ClusterName=`opts_GetOpt "${setflag}cluster" $@` 																		# cluster address [e.g. louise.yale.edu)

	# -- hcpdlegacy input flags
	EchoSpacing=`opts_GetOpt "${setflag}echospacing" $@`																	# <echo_spacing_value>   EPI Echo Spacing for data [in msec]; e.g. 0.69
	PEdir=`opts_GetOpt "${setflag}PEdir" $@` 																				# <phase_encoding_direction>   Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior
	TE=`opts_GetOpt "${setflag}TE" $@` 																						# <delta_te_value_for_fieldmap>   This is the echo time difference of the fieldmap sequence - find this out form the operator - defaults are *usually* 2.46ms on SIEMENS
	UnwarpDir=`opts_GetOpt "${setflag}unwarpdir" $@` 																		# <epi_phase_unwarping_direction>   Direction for EPI image unwarping; e.g. x or x- for LR/RL, y or y- for AP/PA; may been to try out both -/+ combinations
	DiffDataSuffix=`opts_GetOpt "${setflag}diffdatasuffix" $@` 																# <diffusion_data_name>   Name of the DWI image; e.g. if the data is called <SubjectID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR
	
	# -- boldparcellation input flags
	InputFile=`opts_GetOpt "${setflag}inputfile" $@` 																		# --inputfile=<file_to_compute_parcellation_on>   Specify the name of the file you want to use for parcellation (e.g. bold1_Atlas_MSMAll_hp2000_clean)
	InputPath=`opts_GetOpt "${setflag}inputpath" $@` 																		# --inputpath=<path_for_input_file>   Specify path of the file you want to use for parcellation relative to the master study folder and subject directory (e.g. /images/functional/)
	InputDataType=`opts_GetOpt "${setflag}inputdatatype" $@` 																# --inputdatatype=<type_of_dense_data_for_input_file>   Specify the type of data for the input file (e.g. dscalar or dtseries)
	SingleInputFile=`opts_GetOpt "${setflag}singleinputfile" $@` 															# --singleinputfile
	OutPath=`opts_GetOpt "${setflag}outpath" $@` 																			# --outpath=<path_for_output_file>   Specify the output path name of the pconn file relative to the master study folder (e.g. /images/functional/)
	OutName=`opts_GetOpt "${setflag}outname" $@` 																			# --outname=<name_of_output_pconn_file>   Specify the suffix output name of the pconn file
	ExtractData=`opts_GetOpt "${setflag}extractdata" $@` 																	# --extractdata=<save_out_the_data_as_as_csv>   Specify if you want to save out the matrix as a CSV file
	ComputePConn=`opts_GetOpt "${setflag}computepconn" $@` 																	# --computepconn=<specify_parcellated_connectivity_calculation>   Specify if a parcellated connectivity file should be computed (pconn). This is done using covariance and correlation (e.g. yes; default is set to no).
	UseWeights=`opts_GetOpt "${setflag}useweights" $@` 																		# --useweights=<clean_prior_run>   If computing a  parcellated connectivity file you can specify which frames to omit (e.g. yes' or no; default is set to no) 
	WeightsFile=`opts_GetOpt "${setflag}useweights" $@` 																	# --weightsfile=<location_and_name_of_weights_file>   Specify the location of the weights file relative to the master study folder (e.g. /images/functional/movement/bold1.use)
	ParcellationFile=`opts_GetOpt "${setflag}parcellationfile" $@` 															# --parcellationfile=<file_for_parcellation>   Specify the absolute path of the file you want to use for parcellation (e.g. ${TOOLS}/${MNAPREPO}/library/data/parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)

	# -- roiextract input flags
	ROIInputFile=`opts_GetOpt "${setflag}roifile" $@` 																		# --roifile=<filepath>   Path ROI file (either a NIFTI or a CIFTI with distinct scalar values per ROI)"
	ROIFileSubjectSpecific=`opts_GetOpt "${setflag}subjectroifile" $@` 														# --subjectroifile=<use_a_subject_specific_roi_file>   Specify if you want to use a subject-specific ROI file"
	
	# -- computeboldfc input flags
	#InputFiles=`opts_GetOpt "${setflag}inputfiles" "$@" | sed 's/,/ /g;s/|/ /g'`; InputFiles=`echo "$InputFiles" | sed 's/,/ /g;s/|/ /g'` 	# --inputfiles=
	InputFiles=`opts_GetOpt "${setflag}inputfiles" $@` 																		# --inputfiles=
	OutPathFC=`opts_GetOpt "${setflag}targetf" $@`																			# --targetf=			
	Calculation=`opts_GetOpt "${setflag}calculation" $@`																	# --calculation=	
	RunType=`opts_GetOpt "${setflag}runtype" $@`																			# --runtype=   
	FileList=`opts_GetOpt "${setflag}flist" $@`																				# --flist=   
	IgnoreFrames=`opts_GetOpt "${setflag}ignore" $@`																		# --ignore=   
	MaskFrames=`opts_GetOpt "${setflag}mask" $@`																			# --mask=		
	Covariance=`opts_GetOpt "${setflag}covariance" $@`																		# --covariance=		
	TargetROI=`opts_GetOpt "${setflag}target" $@`																			# --target=			
	RadiusSmooth=`opts_GetOpt "${setflag}rsmooth" $@`																		# --rsmooth=		
	RadiusDilate=`opts_GetOpt "${setflag}rdilate" $@`																		# --rdilate=		
	GBCCommand=`opts_GetOpt "${setflag}command" $@`																			# --command=		
	Verbose=`opts_GetOpt "${setflag}verbose" $@`																			# --verbose=		
	ComputeTime=`opts_GetOpt "${setflag}-time" $@`																			# --time=			
	VoxelStep=`opts_GetOpt "${setflag}vstep" $@`																			# --vstep=			
	ROIInfo=`opts_GetOpt "${setflag}roinfo" $@`																				# --roinfo=			
	FCCommand=`opts_GetOpt "${setflag}options" $@`																			# --options=		
	Method=`opts_GetOpt "${setflag}method" $@`																				# --method=		
		
	# -- dwidenseparcellation input flags
	MatrixVersion=`opts_GetOpt "${setflag}matrixversion" $@` 																# --matrixversion=<matrix_version_value>   matrix solution verion to run parcellation on; e.g. 1 or 3
	ParcellationFile=`opts_GetOpt "${setflag}parcellationfile" $@` 															# --parcellationfile=<file_for_parcellation>   Specify the absolute path of the file you want to use for parcellation (e.g. ${TOOLS}/${MNAPREPO}/library/data/parcellations/Cole_GlasserParcellation_Beta/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)
	OutName=`opts_GetOpt "${setflag}outname" $@` 																			# --outname=<name_of_output_pconn_file>   Specify the suffix output name of the pconn file
	WayTotal=`opts_GetOpt "${setflag}waytotal" $@`																			# --waytotal=<use_waytotal_normalized_data>   Use the waytotal normalized version of the DWI dense connectome. Default: [no] 	
	
	# -- dwiseedtractography input flags
	SeedFile=`opts_GetOpt "${setflag}seedfile" $@` 																			# --seedfile=<structure_for_seeding>   Specify the absolute path of the seed file you want to use as a seed for dconn reduction
	
	# -- eddyqc input flags
	EddyBase=`opts_GetOpt "${setflag}eddybase" $@` 																			# <eddy_input_base_name>   This is the basename specified when running EDDY (e.g. eddy_unwarped_images)
	EddyPath=`opts_GetOpt "${setflag}eddypath" $@` 																			# <eddy_folder_relative_to_subject_folder>   Specify the relative path of the eddy folder you want to use for inputs 
	Report=`opts_GetOpt "${setflag}report" $@`   																			# <run_group_or_individual_report>   If you want to generate a group report [individual or group  Default: individual
	BvalsFile=`opts_GetOpt "${setflag}bvalsfile" $@` 																		# <bvals_file>   bvals input file
	BvecsFile=`opts_GetOpt "${setflag}bvecsfile" $@` 																		# <bvecs_file>   bvecs input file
	EddyIdx=`opts_GetOpt "${setflag}eddyidx" $@`   																			# <eddy_index_file>   EDDY index file
	EddyParams=`opts_GetOpt "${setflag}eddyparams" $@`   																	# <eddy_param_file>   EDDY parameters file
	List=`opts_GetOpt "${setflag}list" $@`   																				# <group_list_input>   Text file containing a list of qc.json files obtained from SQUAD 
	Mask=`opts_GetOpt "${setflag}mask" $@`   																				# <mask_file>   Binary mask file (most qc measures will be averaged across voxels labeled in the mask)
	GroupBar=`opts_GetOpt "${setflag}groupvar" $@`   																		# <extra_grouping_variable>   Text file containing extra grouping variable
	OutputDir=`opts_GetOpt "${setflag}outputdir" $@`   																		# <name_of_cleaned_eddy_output>   Output directory - default = '<eddyBase>.qc'
	Update=`opts_GetOpt "${setflag}update" $@`   																			# <setting_to_update_subj_reports>   Applies only if --report='group' - set to <true> to update existing single subject qc reports
				
	# -- fslbedpostxgpu input flags
	Fibers=`opts_GetOpt "${setflag}fibers" $@` 																				# <number_of_fibers>   Number of fibres per voxel, default 3
	Model=`opts_GetOpt "${setflag}model" $@`   																				# <deconvolution_model>   Deconvolution model. 1: with sticks, 2: with sticks with a range of diffusivities (default), 3: with zeppelins
	Burnin=`opts_GetOpt "${setflag}burnin" $@` 																				# <burnin_period_value>   Burnin period, default 1000
	Jumps=`opts_GetOpt "${setflag}jumps" $@`   																				# <number_of_jumps>   Number of jumps, default 1250
	Rician=`opts_GetOpt "${setflag}rician" $@`   																			# <set_rician_value>   Default it YES
	
	# -- probtrackxgpudense input flags
	MatrixOne=`opts_GetOpt "${setflag}omatrix1" $@`  																		# <matrix1_model>   Specify if you wish to run matrix 1 model [yes or omit flag]
	MatrixThree=`opts_GetOpt "${setflag}omatrix3" $@`  																		# <matrix3_model>   Specify if you wish to run matrix 3 model [yes or omit flag]
	NsamplesMatrixOne=`opts_GetOpt "${setflag}nsamplesmatrix1" $@`  														# <Number_of_Samples_for_Matrix1>   Number of samples - default=5000
	NsamplesMatrixThree=`opts_GetOpt "${setflag}nsamplesmatrix3" $@`  														# <Number_of_Samples_for_Matrix3>>   Number of samples - default=5000
	
	# -- awshcpsync input flags
	Modality=`opts_GetOpt "${setflag}modality" $@` 																			# <modality_to_sync>   Which modality or folder do you want to sync [e.g. MEG, MNINonLinear, T1w]"
	Awsuri=`opts_GetOpt "${setflag}awsuri" $@`	 																			# <aws_uri_location>   Enter the AWS URI [e.g. /hcp-openaccess/HCP_900]"
		
	# -- qcpreproc input flags
	OutPath=`opts_GetOpt "${setflag}outpath" $@` 																			# --outpath=<path_for_output_file>   Specify the output path name of the QC folder
	TemplateFolder=`opts_GetOpt "${setflag}templatefolder" $@` 																# --templatefolder=<path_for_the_template_folder>   Specify the output path name of the template folder (default: ${TOOLS}/${MNAPREPO}/library/data/scenes/qc)
	Modality=`opts_GetOpt "${setflag}modality" $@` 																			# --modality=<input_modality_for_qc>   Specify the modality to perform QC on (Supported: T1w, T2w, myelin, BOLD, DWI)
	DWIPath=`opts_GetOpt "${setflag}dwipath" $@` 																			# --dwipath=<path_for_dwi_data>   Specify the input path for the DWI data (may differ across studies)
	DWIData=`opts_GetOpt "${setflag}dwidata" $@` 																			# --dwidata=<file_name_for_dwi_data>   Specify the file name for DWI data (may differ across studies)
	DtiFitQC=`opts_GetOpt "${setflag}dtifitqc" $@` 																			# --dtifitqc=<visual_qc_for_dtifit>   Specify if dtifit visual QC should be completed [e.g. YES or NO]
	BedpostXQC=`opts_GetOpt "${setflag}bedpostxqc" $@` 																		# --bedpostxqc=<visual_qc_for_bedpostx>   Specify if BedpostX visual QC should be completed [e.g. YES or NO]
	EddyQCPDF=`opts_GetOpt "${setflag}eddyqcpdf" $@` 																		# --eddyqcpdf=<pdf_qc_for_eddy>   Specify if EDDY PDF QC should be linked into QC folder [e.g. yes or no]
	DWILegacy=`opts_GetOpt "${setflag}dwilegacy" $@` 																		# --dwilegacy=<dwi_data_processed_via_legacy_pipeline>   Specify is DWI data was processed via legacy pipelines [e.g. YES; default NO]
	BOLDS=`opts_GetOpt "${setflag}bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'` 	# --bolddata=<file_names_for_bold_data>   Specify the file names for BOLD data separated by comma [may differ across studies; e.g. 1, 2, 3 or BOLD_1 or rfMRI_REST1_LR,rfMRI_REST2_LR]
	BOLDSuffix=`opts_GetOpt "${setflag}boldsuffix" $@` 																		# --boldsuffix=<file_name_for_bold_data>   Specify the file name for BOLD data [may differ across studies; e.g. Atlas or MSMAll]
	SkipFrames=`opts_GetOpt "${setflag}skipframes" $@` 																		# --skipframes=<number_of_initial_frames_to_discard_for_bold_qc>   Specify the number of initial frames you wish to exclude from the BOLD QC calculation
	
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
	# 	 * Note: Not all functions are supported in interactive mode
	echo ""
	reho "--------------------------------------------"
	reho "--- Running pipeline in interactive mode ---"
	reho "--------------------------------------------"
	echo ""
	
	# -- Read core interactive command line inputs as default positional variables (i.e. function, path & cases)
	FunctionToRunInt="$1"
	StudyFolder="$2" 
	CASESInput="$3"
	# -- Make list of subjects compatible with either space- or comma-delimited input:
	CASES=`echo ${CASESInput} | sed 's/,/ /g'`
fi	

# ========================================================================================
# ============ EXECUTE SELECTED FUNCTION AND LOOP THROUGH ALL THE CASES ==================
# ========================================================================================

# ------------------------------------------------------------------------------
#  matlabhelp function
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "matlabhelp" ]; then
  		"$FunctionToRun"
fi

# ------------------------------------------------------------------------------
#  dicomorganize function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "dicomorganize" ]; then
		# -- Check all the user-defined parameters:
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$Overwrite" ]; then Overwrite="no"; fi
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
		fi
	for CASE in $CASES; do
  		"$FunctionToRun" "$CASE"
  	done
fi

# ------------------------------------------------------------------------------
#  Visual QC Images function loop - qcpreproc - wb_command based
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "qcpreproc" ]; then
		# -- Check all the user-defined parameters:	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$Modality" ]; then reho "Error:  Modality to perform QC on missing [Supported: T1w, T2w, myelin, BOLD, DWI]"; exit 1; fi

		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
		fi
		
		if [ -z "$TemplateFolder" ]; then TemplateFolder="${TOOLS}/${MNAPREPO}/library/data/"; echo "Template folder path value not explicitly specified. Using default: ${TemplateFolder}"; fi
		if [ -z "$OutPath" ]; then OutPath="${StudyFolder}/QC/${Modality}"; echo "Output folder path value not explicitly specified. Using default: ${OutPath}"; fi
		
		if [ "$Modality" = "DWI" ]; then
			if [ -z "$DWIPath" ]; then DWIPath="Diffusion"; echo "DWI input path not explicitly specified. Using default: ${DWIPath}"; fi
			if [ -z "$DWIData" ]; then DWIData="data"; echo "DWI data name not explicitly specified. Using default: ${DWIData}"; fi
			if [ -z "$DWILegacy" ]; then DWILegacy="no"; echo "DWI legacy not specified. Using default: ${TemplateFolder}"; fi
			if [ -z "$DtiFitQC" ]; then DtiFitQC="no"; echo "DWI dtifit QC not specified. Using default: ${DtiFitQC}"; fi
			if [ -z "$BedpostXQC" ]; then BedpostXQC="no"; echo "DWI BedpostX not specified. Using default: ${BedpostXQC}"; fi
			if [ -z "$EddyQCPDF" ]; then EddyQCPDF="no"; echo "DWI EDDY not specified. Using default: ${EddyQCPDF}"; fi		
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
		echo "DWI dtifit QC requested: ${DtiFitQC}"
		echo "DWI bedpostX QC requested: ${BedpostXQC}"
		echo "DWI EDDY QC PDF requested: ${EddyQCPDF}"
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

# ------------------------------------------------------------------------------
#  Eddy QC function loop - eddyqc - uses EDDY QC by Matteo Bastiani, FMRIB
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "eddyqc" ]; then
		unset EddyPath
		# -- Check all the user-defined parameters:	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$Report" ]; then reho "Error: Report type missing"; exit 1; fi
		# -- perform checks for individual run
		if [ "$Report" == "individual" ]; then
			if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
			if [ -z "$EddyBase" ]; then reho "Eddy base input name missing"; exit 1; fi
			if [ -z "$BvalsFile" ]; then reho "BVALS file missing"; exit 1; fi
			if [ -z "$EddyIdx" ]; then reho "Eddy index missing"; exit 1; fi
			if [ -z "$EddyParams" ]; then reho "Eddy parameters missing"; exit 1; fi
			if [ -z "$Mask" ]; then reho "Error: Mask missing"; exit 1; fi
			if [ -z "$BvecsFile" ]; then BvecsFile=""; fi
		fi
		# -- perform checks for group run
		if [ "$Report" == "group" ]; then
			if [ -z "$List" ]; then reho "Error: List of subjects missing"; exit 1; fi
			if [ -z "$Update" ]; then Update="false"; fi
			if [ -z "$GroupVar" ]; then GroupVar=""; fi
		fi
		# -- check if cluster options are set
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
		fi
		
		# -- loop through cases for an individual run call
		if [ ${Report} == "individual" ]; then
			for CASE in ${CASES}
			do
				# -- check in/out paths
				if [ -z ${EddyPath} ]; then
					reho "Eddy path not set. Assuming defaults."
        			EddyPath="${StudyFolder}/${CASE}/hcp/${CASE}/Diffusion/eddy"
    			fi
	    		if [ -z ${OutputDir} ]; then
	    			reho "Output folder not set. Assuming defaults."
    			    OutputDir="${EddyPath}/${EddyBase}.qc"
    			fi
    			# -- report individual parameters
    			echo ""
				echo "Running individual eddyqc with the following parameters:"
				echo ""
				echo "--------------------------------------------------------------"
  				echo "   StudyFolder: ${StudyFolder}"
  				echo "   Subject: ${CASE}"
  				echo "   Report Type: ${Report}"
  				echo "   Eddy QC Input Path: ${EddyPath}"
  				echo "   Eddy QC Output Path: ${OutputDir}"
  				echo "   Eddy Inputs Base Name: ${EddyBase}"
  				echo "   Mask: ${EddyPath}/${Mask}"
  				echo "   BVALS file: ${EddyPath}/${BvalsFile}"
  				echo "   Eddy Index file: ${EddyPath}/${EddyIdx}"
  				echo "   Eddy parameter file: ${EddyPath}/${EddyParams}"
				# report optional parameters
  				echo "   BvecsFile: ${EddyPath}/${BvecsFile}"
  				echo "   Overwrite: ${EddyPath}/${Overwrite}"
				echo "--------------------------------------------------------------"
				# -- execute function
				"$FunctionToRun" "$CASE"
			done
		fi
		
		# -- group call
		if [ ${Report} == "group" ]; then
		    	# -- report group parameters
    			echo ""
				echo "Running group eddyqc with the following parameters:"
				echo ""
				echo "--------------------------------------------------------------"
  				echo "   StudyFolder: ${StudyFolder}"
  				echo "   Report Type: ${Report}"
  				echo "   Eddy QC Input Path: ${EddyPath}"
  				echo "   Eddy QC Output Path: ${OutputDir}"
  				echo "   List: ${List}"
  				echo "   Grouping Variable: ${GroupVar}"
  				echo "   Update single subjects: ${Update}"
  				echo "   Overwrite: ${EddyPath}/${Overwrite}"
				echo "--------------------------------------------------------------"
				
				# ---> Add function all here 
		fi    		
fi

# ------------------------------------------------------------------------------
#  setuphcp function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "setuphcp" ]; then
	
		# -- Check all the user-defined parameters:		
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		
		Cluster="$RunMethod"
		
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
		fi
		echo ""
		echo "--> Ensuring that and correct subjects_hcp.txt files is generated..."
		echo ""
				
			for CASE in $CASES
			do
				if [ -f "$StudyFolder"/"$CASE"/subject_hcp.txt ]; then 
					echo "--> $StudyFolder/$CASE/subject_hcp.txt found"
					echo ""
					"$FunctionToRun" "$CASE"
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

# ------------------------------------------------------------------------------
#  createlists function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "createlists" ]; then
		

		
		# -- Check all the user-defined parameters:
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$ListGenerate" ]; then reho "Error: Type of list to generate missing [preprocessing, analysis, snr]"; exit 1; fi
		
		# - Check optional parameters:
		if [ -z "$Append" ]; then Append="no"; reho "Setting --append='no' by default"; fi
		# - Set list path if not set by user
		if [ -z "$ListPath" ]; then 
			unset ListPath
			mkdir "$StudyFolder"/../processing/lists &> /dev/null
			cd ${StudyFolder}/../processing/lists
			ListPath=`pwd`
			reho "Setting default path for list folder --> $ListPath"
			export ListPath
		fi
		
		# --------------------------
		# --- preprocessing loop ---
		# --------------------------
		if [ "$ListGenerate" == "preprocessing" ]; then
			# -- Check of overwrite flag was set
			if [ "$Overwrite" == "yes" ]; then
				
				echo ""
				reho "===> Deleting prior processing lists"
				echo ""
				rm "$ListPath"/subjects.preprocessing."$ListName".param &> /dev/null
			fi
		
			if [ -z "$ListFunction" ]; then 
				reho "List function not set. Using default function."
				ListFunction="${TOOLS}/${MNAPREPO}/connector/functions/SubjectsParamList.sh"
				echo ""
				reho "$ListFunction"
				echo ""
			fi
			
			if [ -z "$ListName" ]; then reho "Name of preprocessing list for is missing."; exit 1; fi
			
			if [ -z "$ParameterFile" ]; then 
				echo ""
				echo "No parameter header file set - Using defaults: "
				ParameterFile="${TOOLS}/${MNAPREPO}/connector/functions/subjectparamlist_header_multiband.txt"
				echo "--> $ParameterFile"
				echo ""
			fi
			# -- Check if skipping parameter file header
			if [ "$ParameterFile" != "no" ]; then
				# -- Check if lists exists  
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
					cat ${ParameterFile} >> ${ListPath}/subjects.preprocessing.${ListName}.param
				fi 
			fi	
			for CASE in $CASES; do
				"$FunctionToRun" "$CASE"
			done
			echo ""
			geho "-------------------------------------------------------------------------------------------"
			geho "--> Check output:"
			geho "  `ls ${ListPath}/subjects.preprocessing.${ListName}.param `"
			geho "-------------------------------------------------------------------------------------------"
			echo ""
		fi
		# --------------------------
		# --- analysis loop --------
		# --------------------------
		if [ "$ListGenerate" == "analysis" ]; then		
			if [ -z "$ListFunction" ]; then 
			reho "List function not set. Using default function."
				ListFunction="${TOOLS}/${MNAPREPO}/connector/functions/AnalysisList.sh"
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
				rm ${ListPath}/subjects.analysis."$ListName".*.list &> /dev/null
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

# ------------------------------------------------------------------------------
#  printmatrix function loop -- under development
# ------------------------------------------------------------------------------

# if [ "$FunctionToRunInt" == "printmatrix" ]; then
#	echo "Enter which type of data you want to print the matrix for [supported: bold]:"
#			if read answer; then
#			DatatoPrint=$answer
#				if [ "$DatatoPrint" == "bold" ]; then
#					echo "Enter BOLD numbers you want to run the parcellation on [e.g. 1 2 3 or 1-3 for merged BOLDs]:"
#						if read answer; then
#						BOLDS=$answer 
#						echo "Enter BOLD processing steps you want to run the parcellation on [e.g. g7_hpss_res-mVWM g7_hpss_res-mVWMWB hpss_res-mVWM hpss_res-mVWMWB]:"
#							if read answer; then
#							STEPS=$answer 
#								for CASE in $CASES
#									do
#									"$FunctionToRunInt" "$CASE"
#								done
#							fi
#						fi
#				fi
#			fi
# fi

## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri #  fixica function loop
## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri 
## - FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "fixica" ]; then
## - FIXICA Code - integrate into gmri 	echo "Note: Expects that minimally processed NIFTI & CIFTI BOLDs"
## - FIXICA Code - integrate into gmri 	echo ""
## - FIXICA Code - integrate into gmri 	echo "Overwrite existing run [yes, no]:"
## - FIXICA Code - integrate into gmri 		if read answer; then
## - FIXICA Code - integrate into gmri 		Overwrite=$answer
## - FIXICA Code - integrate into gmri 		fi  
## - FIXICA Code - integrate into gmri 	echo "Enter BOLD numbers you want to run FIX ICA on - e.g. 1 2 3 or 1_3 for merged BOLDs:"
## - FIXICA Code - integrate into gmri 		if read answer; then
## - FIXICA Code - integrate into gmri 		BOLDS=$answer 
## - FIXICA Code - integrate into gmri 				for CASE in $CASES
## - FIXICA Code - integrate into gmri 				do
## - FIXICA Code - integrate into gmri   					"$FunctionToRunInt" "$CASE"
## - FIXICA Code - integrate into gmri   				done
## - FIXICA Code - integrate into gmri   		fi	
## - FIXICA Code - integrate into gmri fi

## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri #  postfix function loop
## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri 
## - FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "postfix" ]; then
## - FIXICA Code - integrate into gmri 	echo "Note: This function depends on fsl, wb_command and matlab and expects startup.m to point to wb_command and fsl."
## - FIXICA Code - integrate into gmri 	echo ""
## - FIXICA Code - integrate into gmri 	echo "Overwrite existing postfix scenes [yes, no]:"
## - FIXICA Code - integrate into gmri 		if read answer; then
## - FIXICA Code - integrate into gmri 		Overwrite=$answer
## - FIXICA Code - integrate into gmri 		fi  
## - FIXICA Code - integrate into gmri 	echo "Enter BOLD numbers you want to run PostFix.sh on [e.g. 1 2 3]:"
## - FIXICA Code - integrate into gmri 		if read answer; then
## - FIXICA Code - integrate into gmri 		BOLDS=$answer 
## - FIXICA Code - integrate into gmri 			echo "Enter high pass filter used for FIX ICA [e.g. 2000]"
## - FIXICA Code - integrate into gmri 				if read answer; then
## - FIXICA Code - integrate into gmri 				HighPass=$answer 
## - FIXICA Code - integrate into gmri 					for CASE in $CASES
## - FIXICA Code - integrate into gmri 					do
## - FIXICA Code - integrate into gmri   						"$FunctionToRunInt" "$CASE"
## - FIXICA Code - integrate into gmri   					done
## - FIXICA Code - integrate into gmri   				fi
## - FIXICA Code - integrate into gmri   		fi	
## - FIXICA Code - integrate into gmri fi

## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri #  boldseparateciftifixica function loop
## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri 
## - FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "boldseparateciftifixica" ]; then
## - FIXICA Code - integrate into gmri 	echo "Enter which study and data you want to separate"
## - FIXICA Code - integrate into gmri 	echo "supported: 1_4_raw 5_8_raw 10_13_raw 14_17_raw"
## - FIXICA Code - integrate into gmri 			if read answer; then
## - FIXICA Code - integrate into gmri 			DatatoSeparate=$answer
## - FIXICA Code - integrate into gmri 					for CASE in $CASES
## - FIXICA Code - integrate into gmri 					do
## - FIXICA Code - integrate into gmri   						"$FunctionToRunInt" "$CASE"
## - FIXICA Code - integrate into gmri   					done
## - FIXICA Code - integrate into gmri   			fi
## - FIXICA Code - integrate into gmri fi

## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri #  boldhardlinkfixica function loop
## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri 
## - FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "boldhardlinkfixica" ]; then
## - FIXICA Code - integrate into gmri 	echo "Enter BOLD numbers you want to generate connectivity hard links for [e.g. 1 2 3 or 1_3 for merged BOLDs]:"
## - FIXICA Code - integrate into gmri 		if read answer; then
## - FIXICA Code - integrate into gmri 		BOLDS=$answer 
## - FIXICA Code - integrate into gmri 			for CASE in $CASES
## - FIXICA Code - integrate into gmri 				do
## - FIXICA Code - integrate into gmri   				"$FunctionToRunInt" "$CASE"
## - FIXICA Code - integrate into gmri   			done
## - FIXICA Code - integrate into gmri   		fi	
## - FIXICA Code - integrate into gmri fi
## - FIXICA Code - integrate into gmri 
## - FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "boldhardlinkfixicamerged" ]; then
## - FIXICA Code - integrate into gmri 				for CASE in $CASES
## - FIXICA Code - integrate into gmri 				do
## - FIXICA Code - integrate into gmri   					"$FunctionToRunInt" "$CASE"
## - FIXICA Code - integrate into gmri   				done
## - FIXICA Code - integrate into gmri fi
## - FIXICA Code - integrate into gmri 

## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri #  fixicainsertmean function loop
## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri 
## - FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "fixicainsertmean" ]; then
## - FIXICA Code - integrate into gmri 	echo "Note: This function will insert mean images into FIX ICA files"
## - FIXICA Code - integrate into gmri 	echo "Enter BOLD numbers you want to run mean insertion on [e.g. 1 2 3]:"
## - FIXICA Code - integrate into gmri 		if read answer; then
## - FIXICA Code - integrate into gmri 		BOLDS=$answer 
## - FIXICA Code - integrate into gmri 				for CASE in $CASES
## - FIXICA Code - integrate into gmri 				do
## - FIXICA Code - integrate into gmri   					"$FunctionToRunInt" "$CASE"
## - FIXICA Code - integrate into gmri   				done
## - FIXICA Code - integrate into gmri   		fi	
## - FIXICA Code - integrate into gmri fi

## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri #  fixicaremovemean function loop
## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri 
## - FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "fixicaremovemean" ]; then
## - FIXICA Code - integrate into gmri 	echo "Note: This function will remove mean from mapped FIX ICA files and save new images"
## - FIXICA Code - integrate into gmri 	echo "Enter BOLD numbers you want to run mean removal on [e.g. 1 2 3]:"
## - FIXICA Code - integrate into gmri 		if read answer; then
## - FIXICA Code - integrate into gmri 		BOLDS=$answer 
## - FIXICA Code - integrate into gmri 				for CASE in $CASES
## - FIXICA Code - integrate into gmri 				do
## - FIXICA Code - integrate into gmri   					"$FunctionToRunInt" "$CASE"
## - FIXICA Code - integrate into gmri   				done
## - FIXICA Code - integrate into gmri   		fi	
## - FIXICA Code - integrate into gmri fi

## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri #  linkmovement function loop
## - FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## - FIXICA Code - integrate into gmri 
## - FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "linkmovement" ]; then
## - FIXICA Code - integrate into gmri 	echo "Enter BOLD numbers you want to link [e.g. 1 2 3 or 1-3 for merged BOLDs]:"
## - FIXICA Code - integrate into gmri 		if read answer; then
## - FIXICA Code - integrate into gmri 		BOLDS=$answer 
## - FIXICA Code - integrate into gmri 			for CASE in $CASES
## - FIXICA Code - integrate into gmri 			do
## - FIXICA Code - integrate into gmri   				"$FunctionToRunInt" "$CASE"
## - FIXICA Code - integrate into gmri   			done
## - FIXICA Code - integrate into gmri   		fi
## - FIXICA Code - integrate into gmri fi

# ------------------------------------------------------------------------------
#  bolddense function loop  -- under development
# ------------------------------------------------------------------------------

#if [ "$FunctionToRun" == "bolddense" ]; then
#	echo "Enter BOLD numbers you want to run dense connectome on [e.g. 1 2 3 or 1_3 for merged BOLDs]:"
#		if read answer; then
#		BOLDS=$answer 
#				for CASE in $CASES
#				do
#  					"$FunctionToRunInt" "$CASE"
#  				done
#  		fi	
#fi

# ------------------------------------------------------------------------------
#  fsldtifit function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "fsldtifit" ]; then
	
		# -- Check all the user-defined parameters:		
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi

		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
		fi
				
		echo ""
		echo "Running fsldtifit processing with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Data successfully submitted" 
		echo "Scheduler Name and Options: $Scheduler"
		#echo "Scheduler Options: $SchedulerOptions"
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
	
		# -- Check all the user-defined parameters:		
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$Fibers" ]; then reho "Error: Fibers value missing"; exit 1; fi
		if [ -z "$Model" ]; then reho "Error: Model value missing"; exit 1; fi
		if [ -z "$Burnin" ]; then reho "Error: Burnin value missing"; exit 1; fi		
		if [ -z "$Rician" ]; then reho "Note: Rician flag missing. Setting to default --> YES"; Rician="YES"; fi
		
		Cluster=$RunMethod
			
		echo ""
		echo "Running fslbedpostxgpu processing with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Subjects: $CASES"		
		echo "Number of Fibers: $Fibers"
		echo "Model Type: $Model"
		echo "Burnin Period: $Burnin"
		echo "Rician flag: $Rician"
		echo "EPI Unwarp Direction: $UnwarpDir"
		echo "Scheduler Name and Options: $Scheduler"
		echo "Overwrite prior run: $Overwrite"
		echo "--------------------------------------------------------------"
		echo "Job ID:"
		
		for CASE in $CASES
		do
			"$FunctionToRun" "$CASE"
		done
fi

# ------------------------------------------------------------------------------
#  Diffusion legacy processing function loop (hcpdlegacy)
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "hcpdlegacy" ]; then
	
		# -- Check all the user-defined parameters:		
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$EchoSpacing" ]; then reho "Error: Echo Spacing value missing"; exit 1; fi
		if [ -z "$PEdir" ]; then reho "Error: Phase Encoding Direction value missing"; exit 1; fi
		if [ -z "$TE" ]; then reho "Error: TE value for Fieldmap missing"; exit 1; fi
		if [ -z "$UnwarpDir" ]; then reho "Error: EPI Unwarp Direction value missing"; exit 1; fi
		if [ -z "$DiffDataSuffix" ]; then reho "Error: Diffusion Data Suffix Name missing"; exit 1; fi
		
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
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

# ------------------------------------------------------------------------------
#  StructuralParcellation function loop (structuralparcellation)
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "structuralparcellation" ]; then
	
		# -- Check all the user-defined parameters:
		#    Optional: ComputePConn, UseWeights, WeightsFile
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$InputDataType" ]; then reho "Error: Input data type value missing"; exit 1; fi
		if [ -z "$OutName" ]; then reho "Error: Output file name value missing"; exit 1; fi
		if [ -z "$ParcellationFile" ]; then reho "Error: File to use for parcellation missing"; exit 1; fi
		
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
		fi
		
		# -- Parse optional parameters if not specified 
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
#  ComputeFunctionalConnectivity function loop (computeboldfc)
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "computeboldfc" ]; then	
		# -- Check all the user-defined parameters:		
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$Calculation" ]; then reho "Error: Type of calculation to run (gbc or seed) missing"; exit 1; fi
		if [ -z "$RunType" ]; then reho "Error: Type of run (group or individual) missing"; exit 1; fi
		if [ ${RunType} == "list" ]; then
		 	if [ -z "$FileList" ]; then reho "Error: Group file list missing"; exit 1; fi
		fi
		if [ ${RunType} == "individual" ] || [ ${RunType} == "group" ]; then
			if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
			if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
			if [ -z "$InputFiles" ]; then reho "Error: Input file(s) value missing"; exit 1; fi
			if [ -z "$InputPath" ]; then reho "Error: Input data path value missing"; exit 1; fi
			if [ -z "$OutName" ]; then reho "Error: Output file name value missing"; exit 1; fi
			if [ ${RunType} == "individual" ]; then
				if [ -z "$OutPathFC" ]; then reho "Warrning: Output path value missing. Assuming individual folder structure for output"; fi
			fi
			if [ ${RunType} == "group" ]; then
				if [ -z "$OutPathFC" ]; then reho "Error: Output path value missing and is needed for a group run."; exit 1; fi
			fi
    	fi
    	if [ ${Calculation} == "gbc" ]; then
    		if [ -z "$TargetROI" ]; then TargetROI="[]"; fi
			if [ -z "$RadiusSmooth" ]; then RadiusSmooth="0"; fi
			if [ -z "$RadiusDilate" ]; then RadiusDilate="0"; fi
			if [ -z "$GBCCommand" ]; then GBCCommand="mFz:"; fi
			if [ -z "$Verbose" ]; then Verbose="true"; fi
			if [ -z "$ComputeTime" ]; then ComputeTime="true"; fi
			if [ -z "$VoxelStep" ]; then VoxelStep="5000"; fi
		fi
    	if [ ${Calculation} == "seed" ]; then
    		if [ -z "$ROIInfo" ]; then reho "Error: ROI seed file not specified"; exit 1; fi
			if [ -z "$FCCommand" ]; then FCCommand=""; fi
			if [ -z "$Method" ]; then Method="mean"; fi
		fi		
		
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
		fi
		
		# -- Parse optional parameters if not specified 
		if [ -z "$IgnoreFrames" ]; then IgnoreFrames=""; fi
		if [ -z "$MaskFrames" ]; then MaskFrames=""; fi
		if [ -z "$Covariance" ]; then Covariance=""; fi
		if [ -z "$ExtractData" ]; then ExtractData="no"; fi

		echo ""
		echo "Running ComputeFunctionalConnectivity function with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Output Path: ${OutPathFC}"
  		echo "Extract data in CSV format: ${ExtractData}"
  		echo "Type of fc calculation: ${Calculation}"
  		echo "Type of run: ${RunType}"
  		echo "Ignore frames: ${IgnoreFrames}"
  		echo "Mask out frames: ${MaskFrames}"
  		echo "Calculate Covariance: ${Covariance}"
  		if [ ${RunType} == "list" ]; then
  		echo "FileList: ${FileList}"
  		fi
  		if [ ${RunType} == "individual" ] || [ ${RunType} == "group" ]; then
  		echo "StudyFolder: ${StudyFolder}"
  		echo "Subjects: ${CASES}"
  		echo "Input Files: ${InputFiles}"
  		echo "Input Path for Data: ${StudyFolder}/<subject_id>/${InputPath}"
  		echo "Output Name: ${OutName}"
  		fi
  		if [ ${Calculation} == "gbc" ]; then
  		echo "Target ROI for GBC: ${TargetROI}"
  		echo "Radius Smooth for GBC: ${RadiusSmooth}"
  		echo "Radius Dilate for GBC: ${RadiusDilate}"
  		echo "GBC Commands to run: ${GBCCommand}"
  		echo "Verbose outout: ${Verbose}"
  		echo "Print Compute Time: ${ComputeTime}"
  		echo "Voxel Steps to use: ${VoxelStep}"
  		fi
		if [ ${Calculation} == "seed" ]; then
  		echo "ROI Information for seed fc: ${ROIInfo}"
  		echo "FC Commands to run: ${FCCommand}"
  		echo "Method to compute fc: ${Method}"
  		fi
		echo "--------------------------------------------------------------"
		echo "Job ID:"
		
		if [ ${RunType} == "individual" ]; then
			for CASE in $CASES; do
				"$FunctionToRun" "$CASE"
			done
  		fi
  		
  		if [ ${RunType} == "group" ]; then
  			CASE=`echo "$CASES" | sed 's/ /,/g'`
  			echo $CASE
			"$FunctionToRun" "$CASE"
  		fi
  		
  		if [ ${RunType} == "list" ]; then
			"$FunctionToRun"
  		fi
fi

# ------------------------------------------------------------------------------
#  BOLDParcellation function loop (boldparcellation)
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "boldparcellation" ]; then	
	
		# -- Check all the user-defined parameters:
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$InputPath" ]; then reho "Error: Input path value missing"; exit 1; fi
		if [ -z "$InputDataType" ]; then reho "Error: Input data type value missing"; exit 1; fi
		if [ -z "$OutPath" ]; then reho "Error: Output path value missing"; exit 1; fi
		if [ -z "$OutName" ]; then reho "Error: Output file name value missing"; exit 1; fi
		if [ -z "$ParcellationFile" ]; then reho "Error: File to use for parcellation missing"; exit 1; fi
		
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
		fi
		
		# -- Parse optional parameters if not specified 
		if [ -z "$UseWeights" ]; then UseWeights="no"; fi
		if [ -z "$ComputePConn" ]; then ComputePConn="no"; fi
		if [ -z "$WeightsFile" ]; then WeightsFile="no"; fi
		if [ -z "$ExtractData" ]; then ExtractData="no"; fi
		if [ -z "$SingleInputFile" ]; then SingleInputFile=""; 
			if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
			if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
			if [ -z "$InputFile" ]; then reho "Error: Input file value missing"; exit 1; fi
		fi
		echo ""
		echo "Running BOLDParcellation function with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Study Folder: ${StudyFolder}"
		echo "Subjects: ${CASES}"
		echo "Input File: ${InputFile}"
		echo "Input Path: ${InputPath}"
		echo "Single Input File: ${SingleInputFile}"
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
		
		if [ -z "$SingleInputFile" ]; then SingleInputFile=""; 
			for CASE in $CASES; do "$FunctionToRun" "$CASE"; done
		else
			"$FunctionToRun" "$CASE"
		fi
fi

# ------------------------------------------------------------------------------
#  DWIDenseParcellation function loop (dwidenseparcellation)
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "dwidenseparcellation" ]; then
	
		# -- Check all the user-defined parameters:		
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$MatrixVersion" ]; then reho "Error: Matrix version value missing"; exit 1; fi
		if [ -z "$ParcellationFile" ]; then reho "Error: File to use for parcellation missing"; exit 1; fi
		if [ -z "$OutName" ]; then reho "Error: Name of output pconn file missing"; exit 1; fi
		
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
		fi	

		if [ -z "$WayTotal" ]; then reho "--waytotal normalized data not specified. Assuming default [no]"; fi

		echo ""
		echo "Running DWIDenseParcellation function with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Matrix version used for input: $MatrixVersion"
		echo "File to use for parcellation: $ParcellationFile"
		echo "Dense DWI Parcellated Connectome Output Name: $OutName"
		echo "Waytotal normalization: ${WayTotal}"
		echo "Overwrite prior run: $Overwrite"
		echo "--------------------------------------------------------------"
		echo "Job ID:"
		
		for CASE in $CASES
		do
			"$FunctionToRun" "$CASE"
		done
fi

# ------------------------------------------------------------------------------
#  ROIExtract function loop (roiextract)
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "roiextract" ]; then	
	
		# -- Check all the user-defined parameters:
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$OutPath" ]; then reho "Error: Output path value missing"; exit 1; fi
		if [ -z "$OutName" ]; then reho "Error: Output file name value missing"; exit 1; fi
		if [ -z "$ROIInputFile" ]; then reho "Error: File to use for ROI extraction missing"; exit 1; fi
		
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
		fi
		
		# -- Parse optional parameters if not specified 
		if [ -z "$ROIFileSubjectSpecific" ]; then ROIFileSubjectSpecific="no"; fi
		if [ -z "$Overwrite" ]; then Overwrite="no"; fi
		if [ -z "$SingleInputFile" ]; then SingleInputFile=""; 
			if [ -z "$InputFile" ]; then reho "Error: Input file path value missing"; exit 1; fi
			if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
			if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		fi
		
		echo ""
		echo "Running ROIExtract function with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Study Folder: ${StudyFolder}"
		echo "Subjects: ${CASES}"
		echo "Input File: ${InputFile}"
		echo "Output File Name: ${OutName}"
		echo "Single Input File: ${SingleInputFile}"
		echo "ROI File: ${ROIInputFile}"
		echo "Subject specific ROI file set: ${ROIFileSubjectSpecific}"		
		echo "Overwrite prior run: ${Overwrite}"
		echo "--------------------------------------------------------------"
		echo "Job ID:"
		
		if [ -z "$SingleInputFile" ]; then SingleInputFile=""; 
			for CASE in $CASES; do "$FunctionToRun" "$CASE"; done
		else
			"$FunctionToRun"
		fi
fi

# ------------------------------------------------------------------------------
#  DWIDenseSeedTractography function loop (dwiseedtractography)
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "dwiseedtractography" ]; then
	
		# -- Check all the user-defined parameters:		
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$MatrixVersion" ]; then reho "Error: Matrix version value missing"; exit 1; fi
		if [ -z "$SeedFile" ]; then reho "Error: File to use for seed reduction missing"; exit 1; fi
		if [ -z "$OutName" ]; then reho "Error: Name of output pconn file missing"; exit 1; fi
		
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
		fi

		if [ -z "$WayTotal" ]; then WayTotal="no"; reho "--waytotal normalized data not specified. Assuming default [no]"; fi
			
		echo ""
		echo "Running DWIDenseSeedTractography function with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Matrix version used for input: $MatrixVersion"
		echo "File to use for seed reduction: $SeedFile"
		echo "Dense DWI Parcellated Connectome Output Name: $OutName"
		echo "Waytotal normalization: ${WayTotal}"
		echo "Overwrite prior run: $Overwrite"
		echo "--------------------------------------------------------------"
		echo "Job ID:"
		
		for CASE in $CASES
		do
			"$FunctionToRun" "$CASE"
		done
fi


# ------------------------------------------------------------------------------
#  autoptx function loop
# ------------------------------------------------------------------------------

## -- NEED TO CODE

# ------------------------------------------------------------------------------
#  pretractographydense function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "pretractographydense" ]; then
	
		# -- Check all the user-defined parameters:		
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
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

# ------------------------------------------------------------------------------
#  probtrackxgpudense function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "probtrackxgpudense" ]; then
	
		# Check all the user-defined parameters: 1.QUEUE, 2. Scheduler, 3. Matrix1, 4. Matrix2
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi		
		if [ -z "$MatrixOne" ] && [ -z "$MatrixThree" ]; then reho "Error: Matrix option missing. You need to specify at least one. [e.g. --omatrix1='yes' and/or --omatrix2='yes']"; exit 1; fi
		if [ "$MatrixOne" == "yes" ]; then
			if [ -z "$NsamplesMatrixOne" ]; then NsamplesMatrixOne=10000; fi
		fi
		if [ "$MatrixThree" == "yes" ]; then
			if [ -z "$NsamplesMatrixThree" ]; then NsamplesMatrixThree=3000; fi
		fi
		
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
		fi
		
		echo ""
		echo "Running Pretractography Dense processing with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "CASES: $CASES"
		echo "Scheduler: $Scheduler"
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

# ------------------------------------------------------------------------------
#  awshcpsync - AWS S3 Sync command wrapper
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "awshcpsync" ]; then
		# Check all the user-defined parameters: 1. Modality, 2. Awsuri, 3. RunMethod
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
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

exit 0