#!/bin/sh 
#set -x

## --> PENDING GENERAL TASKS:
## ------------------------------------------------------------------------------------------------------------------------------------------
## --> Make sure to document adjustments to diffusion connectome code for GPU version [e.g. omission of matrixes etc.]
## --> Integrate all command line flags for functions into IF statements [In progress... see example for hcpdlegacy]
## --> Integrate usage calls for each function [In progress]
## --> Integrate log generation for each function and build IF statement to override log generation if nolog flag [In progress]
## --> Issue w/logging - the exec function effectively double-logs everything for each case and for the whole command
## --> Finish autoptx function
## --> Add MYELIN or THICKNESS parcellation functions as with boldparcellation and dwidenseparcellation
## --> Optimize list generation function to take multiple inputs and naming conventions
## ------------------------------------------------------------------------------------------------------------------------------------------

## ---->  Full Automation of Preprocessing Effort (work towards turn-key solution)
## ------------------------------------------------------------------------------------------------------------------------------------------
## - Sync to Grace crontab job 																				-- DONE
## - Rsync to subject folder based on acq_log.txt															-- IN PROGRESS
## - Dicomsort if data complete w/o error															        -- IN PROGRESS
## - Generate subject.txt -- IF 0 ERR then RUN; ELSE ABORT													-- IN PROGRESS
## - Run HCP 1-5 via bash script submitted to bigmem02; setup checkpoints (will need param file)			-- IN PROGRESS
## - Run QC: i) SNR, ii) Visual, iii) fcMRI 															    -- IN PROGRESS (Need to vet w/Grega)
## - dtifit																									-- IN PROGRESS
## - bedpostX																								-- IN PROGRESS
## - probtrackX																								-- IN PROGRESS
## - dwidenseparcellated																					-- IN PROGRESS
## - FIX ICA / denoising (will need param file)																-- IN PROGRESS
## ------------------------------------------------------------------------------------------------------------------------------------------

## --> BITBUCKET INFO:
## ------------------------------------------------------------------------------------------------------------------------------------------
## GitRepo: https://bitbucket.org/alan.anticevic/analysispipeline/overview
## git command reference:
## git add LICENSE.md
## git add AnalysisPipeline.sh
## git commit . --message="Update"
## git push origin master
## git pull origin master
## added AMPA sever - git remote add ampa ssh://aanticevic@ampa.yale.edu/usr/local/analysispipeline
## ------------------------------------------------------------------------------------------------------------------------------------------

#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# # AnalysisPipeline.sh
#
# ## Copyright Notice
#
# Copyright (C) 2015 Anticevic Lab
#
# * Yale University
#
# ## Author(s)
#
# * Alan Anticevic, Department of Psychiatry, Yale University
#
# ## Product
#
# * Analysis Pipelines for the general lab neuroimaging workflow
#
# ## License
#
# See the [LICENSE](https://bitbucket.org/alan.anticevic/analysispipeline/LICENSE.md) file
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
# * gCode (all repositories)
# * PALM
# * Julia
# * Python (version 2.7 or above)
# * AFNI
# * Gradunwarp
# * CodeHCPe (HCP Pipelines modified code)
# * R Software library
#
# ### Expected Environment Variables
#
# * HCPPIPEDIR
# * CARET7DIR
# * FSLDIR
# * Note: This script expects hcpsetup.sh in your .bash_profile to ensure correct paths to all the tools
# * Note: also source hcpsetup.sh in your .bash_profile to ensure correct paths to all the tools
#
# ### Expected Previous Processing
# 
# * The necessary input files for higher-level analyses come from HCP pipelines and/or dofcMRI
#
#~ND~END~

###########################################################################################################################
###################################################  CODE START ###########################################################
###########################################################################################################################

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
  				cyaneho "	-------- GENERAL HELP FOR ANALYSIS PIPELINE: --------"
  				echo ""
  				weho "		* GENERAL INTERACTIVE USAGE:"
  				echo "		AP <function_name> <study_folder> '<list of cases>' [options]"
  				echo ""
  				weho "		* GENERAL FLAG USAGE:"
  				echo "		AP --function=<function_name> --studyfolder=<study_folder> --subjects='<list of cases>' [options]"  				 
  				echo ""
  				weho "		* EXAMPLE TO RUN INTERACTIVELY FROM TERMINAL (NO FLAG]:"
  				echo "		AP dicomsort /Volumes/syn1/Studies/Connectome/subjects '100307 100408'"
  				echo ""
  				weho "		* EXAMPLE TO RUN WITH FLAGS (NO INTERACTIVE TERMINAL INPUT]:"
  				echo "		AP --function=dicomsort --studyfolder=/Volumes/syn1/Studies/Connectome/subjects --subjects='100307,100408'"
  				echo ""
  				weho "		* FUNCTION-SPECIFIC USAGE:"
  				echo "		AP dicomsort"
  				echo ""
  				cyaneho "	-------- LIST OF SPECIFIC SUPPORTED FUNCTIONS: --------"
  				echo ""  				
  				weho "		--- DATA ORGANIZATION FUNCTIONS ---"
  				echo "		dicomsort			SORT DICOMs and SETUP NIFTI FILES FROM DICOMS"
  				echo "		dicom2nii			CONVERT DICOMs TO NIFTI FILES"
  				echo "		setuphcp 			SETUP DATA STRUCTURE FOR HCP PROCESSING"
  				echo "		hpcsync 			SYNC WITH YALE HPC CLUSTER(S) FOR ORIGINAL HCP PIPELINES (StudyFolder/$ubject)"
  				echo "		hpcsync2			SYNC WITH YALE HPC CLUSTER(S) FOR dofcMRI INTEGRATION (StudyFolder/Subject/hcp/Subject)"
  				echo "		awshcpsync			SYNC HCP DATA FROM AWS S3 CLOUD"
  				echo ""  				
  				weho "		--- HCP PIPELINES FUNCTIONS ---"
  				echo "		hpc1				PREFREESURFER COMPONENT OF THE HCP PIPELINE (CLUSTER AWARE)"
  				echo "		hpc2				FREESURFER COMPONENT OF THE HCP PIPELINE (CLUSTER AWARE)"
  				echo "		hpc3				POSTFREESURFER COMPONENT OF THE HCP PIPELINE (CLUSTER AWARE)"
  				echo "		hpc4				VOLUME COMPONENT OF THE HCP PIPELINE (CLUSTER AWARE)"
  				echo "		hpc5				SURFACE COMPONENT OF THE HCP PIPELINE (CLUSTER AWARE)"
  				echo "		hpcd				DIFFUSION COMPONENT OF THE HCP PIPELINE (CLUSTER AWARE)"
  				echo "		hcpdlegacy			DIFFUSION PROCESSING THAT IS HCP COMPLIANT FOR LEGACY DATA WITH STANDARD FIELDMAPS (CLUSTER AWARE)"
  				echo ""  				
  				weho "		--- GENERATE LISTS & QC FUNCTIONS ---"
  				echo "		setuplist	 		SETUP LIST FOR FCMRI ANALYSIS / PREPROCESSING or VOLUME SNR CALCULATIONS"
  				echo "		qaimages	 		RUN VISUAL QC FOR T1w and BOLD IMAGES"
  				echo "		nii4dfpconvert 			CONVERT NIFTI HCP-PROCESSED BOLD DATA TO 4DPF FORMAT FOR FILD ANALYSES"
  				echo "		cifti4dfpconvert 		CONVERT CIFTI HCP-PROCESSED BOLD DATA TO 4DPF FORMAT FOR FILD ANALYSES"
  				echo "		ciftismooth 			SMOOTH & CONVERT CIFTI BOLD DATA TO 4DPF FORMAT FOR FILD ANALYSES"
  				echo "		fidlconc 			SETUP CONC & FIDL EVEN FILES FOR GLM ANALYSES"
  				echo "		qcstructural	 		RUN VISUAL QC FOR T1w IMAGES"

  				echo ""  				
  				weho "		--- DWI ANALYSES & TRACTOGRAPHY FUNCTIONS ---"
  				echo "		fsldtifit 			RUN FSL DTIFIT (CLUSTER AWARE)"
  				echo "		fslbedpostxgpu 			RUN FSL BEDPOSTX w/GPU (CLUSTER AWARE)"
  				echo "		isolatesubcortexrois 		ISOLATE SUBJECT-SPECIFIC SUBCORTICAL ROIs FOR TRACTOGRAPHY"
  				echo "		isolatethalamusfslnuclei 	ISOLATE FSL THALAMIC ROIs FOR TRACTOGRAPHY"
  				echo "		probtracksubcortex 		RUN FSL PROBTRACKX ACROSS SUBCORTICAL NUCLEI (CPU)"
  				echo "		pretractography			GENERATES SPACE FOR CORTICAL DENSE CONNECTOMES (CLUSTER AWARE)"
  				echo "		pretractographydense		GENERATES SPACE FOR WHOLE-BRAIN DENSE CONNECTOMES (CLUSTER AWARE)"
  				echo "		probtrackxgpucortex		RUN FSL PROBTRACKX ACROSS CORTICAL MESH FOR DENSE CONNECTOMES w/GPU (CLUSTER AWARE)"
  				echo "		makedensecortex			GENERATE DENSE CORTICAL CONNECTOMES (CLUSTER AWARE)"
  				echo "		probtrackxgpudense		RUN FSL PROBTRACKX FOR WHOLE BRAIN & GENERATEs DENSE WHOLE-BRAIN CONNECTOMES (CLUSTER AWARE)"
  				echo ""  				
  				weho "		--- ANALYSES FUNCTIONS ---"  				
  				echo "		ciftiparcellate			PARCELLATE BOLD, DWI, MYELIN or THICKNESS DATA VIA 7 & 17 NETWORK SOLUTIONS"
  				echo "		boldparcellation		PARCELLATE BOLD DATA and GENERATE PCONN FILES VIA USER-SPECIFIED PARCELLATION"
  				echo "		dwidenseparcellation		PARCELLATE DENSE DWI TRACTOGRAPHY DATA VIA USER-SPECIFIED PARCELLATION"
  				echo "		printmatrix			EXTRACT PARCELLATED MATRIX FOR BOLD DATA VIA YEO 17 NETWORK SOLUTIONS"
  				echo "		boldmergenifti			MERGE SPECIFIED NII BOLD TIMESERIES"
  				echo "		boldmergecifti			MERGE SPECIFIED CITI BOLD TIMESERIES"
  				echo "		bolddense			COMPUTE BOLD DENSE CONNECTOME (NEEDS >30GB RAM PER BOLD)"
  				echo "		palmanalysis			RUN PALM AND EXTRACT DATA FROM ROIs (CLUSTER AWARE)"
  				echo ""  				
  				weho "		--- FIX ICA DE-NOISING FUNCTIONS ---"    				
  				echo "		fixica				RUN FIX ICA DE-NOISING ON A GIVEN VOLUME"
  				echo "		postfix				GENERATES WB_VIEW SCENE FILES IN EACH SUBJECTS DIRECTORY FOR FIX ICA RESULTS"
  				echo "		boldhardlinkfixica		SETUP HARD LINKS FOR SINGLE RUN FIX ICA RESULTS"  				
  				echo "		fixicainsertmean		RE-INSERT MEAN IMAGE BACK INTO MAPPED FIX ICA DATA (NEEDED PRIOR TO dofcMRIp)"
  				echo "		fixicaremovemean		REMOVE MEAN IMAGE FROM MAPPED FIX ICA DATA"
  				echo "		boldseparateciftifixica		SEPARATE SPECIFIED BOLD TIMESERIES (RESULTS FROM FIX ICA - USE IF BOLDs MERGED)"
  				echo "		boldhardlinkfixicamerged	SETUP HARD LINKS FOR MERGED FIX ICA RESULTS (USE IF BOLDs MERGED)"  				
  				echo ""
}

###########################################################################################################################
###########################################################################################################################
####################################  SPECIFIC ANALYSIS FUNCTIONS START HERE ##############################################
###########################################################################################################################
###########################################################################################################################

# ------------------------------------------------------------------------------------------------------
#  dicomsort - Sort original DICOMs into sub-folders and then generate NIFTI files
# ------------------------------------------------------------------------------------------------------

dicomsort() {

	cd "$StudyFolder"/"$CASE"

	echo " ---> running sortDicom"
	gmri sortDicom

	echo " ---> running dicom2nii"
	gmri dicom2nii unzip=yes gzip=yes clean=yes	
	
}

show_usage_dicomsort() {
  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
  				echo "This function expects a set of raw DICOMs in <study_folder>/<case>/inbox."
  				echo "DICOMs are organized, gzipped and converted to NIFTI format for additional processing."
  				echo ""
    			echo "-- USAGE FOR dicomsort"
    			echo ""
				echo "* Example with interactive terminal:"
				echo "AP dicomsort <study_folder> '<list of cases>'"
    			echo ""
				echo "* Example with flags:"
				echo "AP --function=dicomsort --path=<study_folder> --subjects='<list of cases>'"
    			echo ""
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
    			echo "-- USAGE FOR dicom2nii"
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
	
	#exec &> >(tee $(timestamp setuphcp))
	
	#echo ""
	#echo "Paramaters:"
	#echo ""
	#echo "--function=setuphcp"
	#echo "--studyfolder=$StudyFolder"
	#echo "--studyfolder=$CASE"
	#echo ""

	cd "$StudyFolder"/"$CASE"

	echo " ---> running setupHCP"
	gmri setupHCP
	
}

show_usage_setuphcp() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
  				echo "This function generates the Human Connectome Project folder structure for preprocessing."
  				echo "It should be executed after proper dicomsort and subject.txt file has been vetted."
  				echo ""
    			echo "-- USAGE FOR setuphcp"
    			echo ""
				echo "* Example with interactive terminal:"
				echo "AP dicom2nii <study_folder> '<list of cases>'"
    			echo ""
				echo "* Example with flags:"
				echo "AP --function=setuphcp --path=<study_folder> --subjects='<list of cases>'"
    			echo ""
    			echo ""
    			echo ""
}


# ------------------------------------------------------------------------------------------------------
#  setuplist - Generate processing & analysis lists for fcMRI
# ------------------------------------------------------------------------------------------------------

setuplist() {

	if [ "$ListGenerate" == "fcmri" ]; then
		#generate fcMRI analysis list for all subjects across all BOLDs
		cd "$StudyFolder"
		cd "$StudyFolder"/../fcMRI/lists
		ln -s "$APPATH"/functions/"$ListFunction" ./"$ListFunction" &> /dev/null
		source "$ListFunction"
	fi
	
	if [ "$ListGenerate" == "snr" ]; then
		#generate subject SNR list for all subjects across all BOLDs
		cd "$StudyFolder"/QC/snr
		for BOLD in $BOLDS
		do
			echo subject id:"$CASE" >> subjects.snr.txt
			echo file:"$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD".nii.gz >> subjects.snr.txt
		done
	fi
	
	if [ "$ListGenerate" == "fcmripreprocess" ]; then
		#generate fcMRI preprocess list for all subjects across all BOLDs
		cd "$StudyFolder"
		cd ../fcMRI
		source "$ListFunction"
	fi
}

show_usage_setuplist() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "USAGE INFO PENDING..."
    			echo ""
}


# ------------------------------------------------------------------------------------------------------
#  fidlconcorganize - Organize all CONCs and FIDL files for GLM analyses across various tasks
# ------------------------------------------------------------------------------------------------------

fidlconcorganize() {
	
	cd "$StudyFolder"
	cd ../GLM.Analyses/
	source "$ListFunction" #reads fidlconcorganize.sh 

}

show_usage_fidlconcorganize() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "USAGE INFO PENDING..."
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
    			echo "USAGE INFO PENDING..."
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
    			echo "USAGE INFO PENDING..."
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
    			echo "USAGE INFO PENDING..."
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  hpcsync - Sync files to Yale HPC and back to the Yale server after HCP preprocessing
# ------------------------------------------------------------------------------------------------------

hpcsync() {

	if [ "$Direction" == 1 ]; then
		echo "Syncing data to $ClusterName for $CASE ..."
		rsync --checksum --rsh=ssh -avz --exclude=* "$StudyFolder"/"$CASE"/hcp/"$CASE" "$NetID"@"$ClusterName":"$HCPStudyFolder"/ &> /dev/null
		rsync --checksum --rsh=ssh --exclude=*dicom* --exclude=*Results* --exclude=inbox --exclude=images -avz "$StudyFolder"/"$CASE"/hcp/"$CASE" "$NetID"@"$ClusterName":"$HCPStudyFolder"/ &> /dev/null
	else 
		echo "Syncing data from $ClusterName for $CASE ..." 
		rsync --checksum --rsh=ssh -avz "$NetID"@"$ClusterName":"$HCPStudyFolder"/"$CASE"/MNINonLinear "$StudyFolder"/"$CASE"/hcp/"$CASE"/ &> /dev/null
		rsync --checksum --rsh=ssh -avz "$NetID"@"$ClusterName":"$HCPStudyFolder"/"$CASE"/T1w "$StudyFolder"/"$CASE"/hcp/"$CASE"/ &> /dev/null
	fi
}


hpcsync2() {

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

show_usage_hpcsync2() {
  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "This function runs rsync to or from the Yale Clusters [e.g. Omega, Louise, Grace) and local servers."
  				echo "It explicitly preserves the Human Connectome Project folder structure for preprocessing:"
  				echo "    <study_folder>/<case>/hcp/<case>"
  				echo ""
    			echo "-- USAGE FOR hpcsync2"
    			echo ""
				echo "* Example with interactive terminal:"
				echo "AP hpcsync2 <study_folder> '<list of cases>'"
    			echo ""
    			echo ""
				echo "* Example with flags:"
				echo "AP --function=hpcsync2 --path=<study_folder> --subjects='<list of cases>'--cluster=<cluster_address> --dir=<rsync_direction> --netid=<Yale_NetID> --clusterpath=<cluster_study_folder>"
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
    			echo "USAGE INFO PENDING..."
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  isolatethalamusfslnuclei - Find thalamic ROIs needed for subcortical seed-based tractography via FSL
# ------------------------------------------------------------------------------------------------------

isolatethalamusfslnuclei() {

	# isolate FSL-intersecting thalamic voxels 
	#cp "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm.nii.gz ./
	# FSL thalamus values and labels
	#	thalamus_motor (1) SENS
	#	thalamus_sens (2) SENS
	#	thalamus_occ (3) SENS
	#	thalamus_pfc (4) ASSOC
	#	thalamus_premotor (5) ASSOC
	#	thalamus_parietal (6) ASSOC
	#	thalamus_temporal (7) SENS
	
	# Isolate individual nuclei from FSL thalamus atlas
    #3dcalc -overwrite -a "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm.nii.gz  -expr 'equals(a,1)' -prefix "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-motor.nii.gz # isolate motor-projecting thalamus from FSL atlas file
    #3dcalc -overwrite -a "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm.nii.gz  -expr 'equals(a,2)' -prefix "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-sens.nii.gz # isolate sensory-projecting thalamus from FSL atlas file
    #3dcalc -overwrite -a "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm.nii.gz  -expr 'equals(a,3)' -prefix "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-occ.nii.gz # isolate occipital-projecting thalamus from FSL atlas file
    #3dcalc -overwrite -a "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm.nii.gz  -expr 'equals(a,4)' -prefix "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-pfc.nii.gz # isolate pfc-projecting thalamus from FSL atlas file
    #3dcalc -overwrite -a "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm.nii.gz  -expr 'equals(a,5)' -prefix "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-premotor.nii.gz # isolate premotor-projecting thalamus from FSL atlas file
    #3dcalc -overwrite -a "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm.nii.gz  -expr 'equals(a,6)' -prefix "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-par.nii.gz # isolate motor parietal-projecting from FSL atlas file
    #3dcalc -overwrite -a "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm.nii.gz  -expr 'equals(a,7)' -prefix "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-temp.nii.gz # isolate motor temporal-projecting from FSL atlas file
	
	# Combine into sensory and associative nuclei
	#3dcalc -overwrite -a "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-par.nii.gz -b "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-premotor.nii.gz -c "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-pfc.nii.gz -expr 'a+b+c' -prefix "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-associative.nii.gz
	#3dcalc -overwrite -a "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-sens.nii.gz -b "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-motor.nii.gz -c "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-occ.nii.gz -d "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-temp.nii.gz -expr 'a+b+c+d' -prefix "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-sensory.nii.gz
	
	# Check volumes 
	#fslstats Thalamus-maxprob-thr0-2mm-sensory.nii.gz -V # 2909 23272.000000 
	#fslstats Thalamus-maxprob-thr0-2mm-associative.nii.gz -V # 3655 29240.000000 

	cd "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/ROIs
	3dcalc -overwrite -a "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-sensory.nii.gz -b Atlas_thalamus.R.nii.gz  -expr 'a*b' -prefix Atlas_thalamus_sensory.R.nii.gz # isolate right thalamus from FSL mask file
	3dcalc -overwrite -a "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-sensory.nii.gz -b Atlas_thalamus.L.nii.gz  -expr 'a*b' -prefix Atlas_thalamus_sensory.L.nii.gz # isolate right thalamus from FSL mask file
	3dcalc -overwrite -a "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-associative.nii.gz -b Atlas_thalamus.R.nii.gz  -expr 'a*b' -prefix Atlas_thalamus_associative.R.nii.gz # isolate right thalamus from FSL mask file
	3dcalc -overwrite -a "$StudyFolder"/../fcMRI/roi/Thalamus/Thalamus-maxprob-thr0-2mm-associative.nii.gz -b Atlas_thalamus.L.nii.gz  -expr 'a*b' -prefix Atlas_thalamus_associative.L.nii.gz # isolate right thalamus from FSL mask file
	
	# Get FSL-intersecting thalamus sub-nuclei volumes
	#thal_sensory_lvol_L=`fslstats Atlas_thalamus_sensory.L.nii.gz -V | cut -d " " -f 1` #70 - get # of L thalamic voxels needed to adjust the nsamples flag - 5000 * 456 / 32492 number of vertices
	#thal_sensory_lvol_R=`fslstats Atlas_thalamus_sensory.R.nii.gz -V | cut -d " " -f 1` #74 - get # of R thalamic voxels needed to adjust the nsamples flag - 5000 * 483 / 32492 number of vertices
	#thal_associative_lvol_L=`fslstats Atlas_thalamus_associative.L.nii.gz -V | cut -d " " -f 1` #128 - get # of L thalamic voxels needed to adjust the nsamples flag - 5000 * 832 / 32492 number of vertices
	#thal_associative_lvol_R=`fslstats Atlas_thalamus_associative.R.nii.gz -V | cut -d " " -f 1` #117 - get # of R thalamic voxels needed to adjust the nsamples flag - 5000 * 765 / 32492 number of vertices

}

show_usage_isolatethalamusfslnuclei() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			echo "USAGE INFO PENDING..."
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
    			reho "		*** This function is deprecated and not supported any longer since the dense connectome implementation."
    			reho "		*** The new usage for dense connectome computation can be found via the following functions:"
    			echo ""
  				echo "		probtrackxgpudense		RUN FSL PROBTRACKX FOR WHOLE BRAIN & GENERATEs DENSE WHOLE-BRAIN CONNECTOMES (CLUSTER AWARE)"
    			echo ""
}

# ------------------------------------------------------------------------------------------------------
#  ciftiparcellate - Generate parcellated data across modalities (DWI, BOLD, MYELIN, THICKNESS)
# ------------------------------------------------------------------------------------------------------
	

ciftiparcellate() {

			# David's Yeo 17 network file: "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii

			# check order for labels 
			# wb_command -cifti-label-export-table "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii 1 "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.txt

			# first separate parcellation for L and R hemis
			#wb_command -cifti-separate Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN -label CORTEX_LEFT Yeo2011_17Networks.L.50sqmm_dilate3.0.32k_fs_LR.label.gii -roi Yeo_L_17Networks.func.gii
			#wb_command -cifti-separate Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN -label CORTEX_RIGHT Yeo2011_17Networks.R.50sqmm_dilate3.0.32k_fs_LR.label.gii -roi Yeo_R_17Networks.func.gii
			#wb_command -cifti-create-label Yeo2011_17Networks.L.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii -left-label Yeo2011_17Networks.L.50sqmm_dilate3.0.32k_fs_LR.label.gii -roi-left Yeo_L_17Networks.func.gii
			#wb_command -cifti-create-label Yeo2011_17Networks.R.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii -right-label Yeo2011_17Networks.R.50sqmm_dilate3.0.32k_fs_LR.label.gii -roi-right Yeo_R_17Networks.func.gii
    		
    		
    		# Lisa's Yeo 7 & 17 network file: /Volumes/syn1/Studies/Anticevic.DP5/fcMRI/roi/RSN_Yeo_Buckner_Choi_Cortex_Cerebellum_Striatum/Yeo_Cortex

			#wb_command -cifti-separate rsn_yeo_cortex_7Networks_islands.dlabel.nii COLUMN -label CORTEX_LEFT rsn_yeo_cortex_7Networks_islands_L.32k_fs_LR.label.gii -roi rsn_yeo_cortex_7Networks_islands_L.func.gii
			#wb_command -cifti-separate rsn_yeo_cortex_7Networks_islands.dlabel.nii COLUMN -label CORTEX_RIGHT rsn_yeo_cortex_7Networks_islands_R.32k_fs_LR.label.gii -roi rsn_yeo_cortex_7Networks_islands_R.func.gii
			#wb_command -cifti-create-label rsn_yeo_cortex_7Networks_islands_L.dlabel.nii -left-label rsn_yeo_cortex_7Networks_islands_L.32k_fs_LR.label.gii -roi-left rsn_yeo_cortex_7Networks_islands_L.func.gii
			#wb_command -cifti-create-label rsn_yeo_cortex_7Networks_islands_R.dlabel.nii -right-label rsn_yeo_cortex_7Networks_islands_R.32k_fs_LR.label.gii -roi-right rsn_yeo_cortex_7Networks_islands_R.func.gii
    		
    		#wb_command -cifti-separate rsn_yeo_cortex_17Networks_islands.dlabel.nii COLUMN -label CORTEX_LEFT rsn_yeo_cortex_17Networks_islands_L.32k_fs_LR.label.gii -roi rsn_yeo_cortex_17Networks_islands_L.func.gii
			#wb_command -cifti-separate rsn_yeo_cortex_17Networks_islands.dlabel.nii COLUMN -label CORTEX_RIGHT rsn_yeo_cortex_17Networks_islands_R.32k_fs_LR.label.gii -roi rsn_yeo_cortex_17Networks_islands_R.func.gii
			#wb_command -cifti-create-label rsn_yeo_cortex_17Networks_islands_L.dlabel.nii -left-label rsn_yeo_cortex_17Networks_islands_L.32k_fs_LR.label.gii -roi-left rsn_yeo_cortex_17Networks_islands_L.func.gii
			#wb_command -cifti-create-label rsn_yeo_cortex_17Networks_islands_R.dlabel.nii -right-label rsn_yeo_cortex_17Networks_islands_R.32k_fs_LR.label.gii -roi-right rsn_yeo_cortex_17Networks_islands_R.func.gii
    		
			##################################################################
		 	##################  DWI - cortex2cortex ##########################
			##################################################################
			
			
			NetworkFolder="/Volumes/syn1/Studies/Anticevic.DP5/fcMRI/roi/RSN_Yeo_Buckner_Choi_Cortex_Cerebellum_Striatum/Yeo_Cortex"
			
			## Parcellation for the N=7 Network Solution (David's version)
					
			if [ "$DatatoParcellate" == "dwi_cortex" ]; then
			
			if [ "$Overwrite" == "yes" ]; then
				rm -r "$StudyFolder"/../Parcellated/DWI/"$CASE"*matrix1*.pconn.nii
				rm -r "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"*matrix1*.pconn.nii
				rm -r "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/"$CASE"*matrix1*pconn.nii
				rm -r "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/"$CASE"*matrix1*pconn.nii
			fi
			
					if [ -f "$StudyFolder"/../Parcellated/DWI/"$CASE"_L_fdt_matrix1_CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii ]; then
						echo "Parcellation done for $CASE for left hemisphere. Skipping to next subject..."
					else		
						echo "Running Cortex2Cortex Yeo 17 network parcellation on DWI data Left Hemisphere for $CASE..."
						mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated  &> /dev/null
					
						# run parcellations for each and distance adjustment
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/fdt_matrix1.dconn.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/"$CASE"_L_fdt_matrix1_Yeo2011_17Networks.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/"$CASE"_L_fdt_matrix1_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii ROW "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/"$CASE"_L_fdt_matrix1_CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/fdt_matrix1.dconn.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_L_fdt_matrix1_pd_Yeo2011_17Networks.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_L_fdt_matrix1_pd_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii ROW "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_L_fdt_matrix1_pd_CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii
				
						# setup hard links
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/*CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/*CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/*CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/DWI
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/*CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/DWI
					fi
			
					if [ -f "$StudyFolder"/../Parcellated/DWI/"$CASE"_R_fdt_matrix1_CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii ]; then
						echo "Parcellation done for $CASE for right hemisphere. Skipping to next subject..."
					else
						echo "Running Cortex2Cortex Yeo 17 network parcellation on DWI data Right Hemisphere for $CASE..."
						mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated  &> /dev/null

						# run parcellations for each and distance adjustment
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/fdt_matrix1.dconn.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/"$CASE"_R_fdt_matrix1_Yeo2011_17Networks.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/"$CASE"_R_fdt_matrix1_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii ROW "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/"$CASE"_R_fdt_matrix1_CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/fdt_matrix1.dconn.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_R_fdt_matrix1_pd_Yeo2011_17Networks.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_R_fdt_matrix1_pd_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii ROW "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_R_fdt_matrix1_pd_CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii
						
						# setup hard links
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/*CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/*CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/*CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/DWI
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/*CR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/DWI

					fi
					
					## Parcellation for the N=17 Network Solution (Lisa's version)
			
					if [ -f "$StudyFolder"/../Parcellated/DWI/"$CASE"_L_fdt_matrix1_CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii ]; then
						
						echo "Parcellation done for $CASE for left hemisphere. Skipping to next subject..."
					else		
						echo "Running Cortex2Cortex Yeo 17 network parcellation on DWI data Left Hemisphere for $CASE..."
						mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated  &> /dev/null
						
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/*_RSN_CSC_17Networks*.nii  &> /dev/null	
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/*_RSN_CSC_17Networks*.nii  &> /dev/null
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/*_fdt_matrix1_CR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii  &> /dev/null
						
						# run parcellations for each and distance adjustment
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/fdt_matrix1.dconn.nii "$NetworkFolder"/rsn_yeo_cortex_17Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/"$CASE"_L_fdt_matrix1_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/"$CASE"_L_fdt_matrix1_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$NetworkFolder"/rsn_yeo_cortex_17Networks_islands.dlabel.nii ROW "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/"$CASE"_L_fdt_matrix1_CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/fdt_matrix1.dconn.nii "$NetworkFolder"/rsn_yeo_cortex_17Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_L_fdt_matrix1_pd_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_L_fdt_matrix1_pd_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$NetworkFolder"/rsn_yeo_cortex_17Networks_islands.dlabel.nii ROW "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_L_fdt_matrix1_pd_CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii
				
						# setup hard links
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/*CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/*CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/*CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/DWI
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/*CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/DWI
					fi
			
					if [ -f "$StudyFolder"/../Parcellated/DWI/"$CASE"_R_fdt_matrix1_CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii ]; then
						echo "Parcellation done for $CASE for right hemisphere. Skipping to next subject..."
					else
						echo "Running Cortex2Cortex Yeo 17 network parcellation on DWI data Right Hemisphere for $CASE..."
						mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated  &> /dev/null
						
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/*_RSN_CSC_17Networks*.nii  &> /dev/null	
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/*_RSN_CSC_17Networks*.nii  &> /dev/null
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/*_fdt_matrix1_CR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii  &> /dev/null

						# run parcellations for each and distance adjustment
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/fdt_matrix1.dconn.nii "$NetworkFolder"/rsn_yeo_cortex_17Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/"$CASE"_R_fdt_matrix1_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/"$CASE"_R_fdt_matrix1_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$NetworkFolder"/rsn_yeo_cortex_17Networks_islands.dlabel.nii ROW "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/"$CASE"_R_fdt_matrix1_CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/fdt_matrix1.dconn.nii "$NetworkFolder"/rsn_yeo_cortex_17Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_R_fdt_matrix1_pd_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_R_fdt_matrix1_pd_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$NetworkFolder"/rsn_yeo_cortex_17Networks_islands.dlabel.nii ROW "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_R_fdt_matrix1_pd_CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii
						
						# setup hard links
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/*CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/*CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/*CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/DWI
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/*CR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/DWI

					fi
					
					## Parcellation for the N=7 Network Solution (Lisa's version)
					
					if [ -f "$StudyFolder"/../Parcellated/DWI/"$CASE"_L_fdt_matrix1_CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii ]; then
						
						echo "Parcellation done for $CASE for left hemisphere. Skipping to next subject..."
					else		
						echo "Running Cortex2Cortex Yeo 7 network parcellation on DWI data Left Hemisphere for $CASE..."
						mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated  &> /dev/null
						
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/*_RSN_CSC_7Networks*.nii  &> /dev/null	
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/*_RSN_CSC_7Networks*.nii  &> /dev/null
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/*_fdt_matrix1_CR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii  &> /dev/null
					
						# run parcellations for each and distance adjustment
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/fdt_matrix1.dconn.nii "$NetworkFolder"/rsn_yeo_cortex_7Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/"$CASE"_L_fdt_matrix1_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/"$CASE"_L_fdt_matrix1_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$NetworkFolder"/rsn_yeo_cortex_7Networks_islands.dlabel.nii ROW "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/"$CASE"_L_fdt_matrix1_CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/fdt_matrix1.dconn.nii "$NetworkFolder"/rsn_yeo_cortex_7Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_L_fdt_matrix1_pd_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_L_fdt_matrix1_pd_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$NetworkFolder"/rsn_yeo_cortex_7Networks_islands.dlabel.nii ROW "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_L_fdt_matrix1_pd_CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
				
						# setup hard links
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/*CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/*CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_pd_"$StepSize"/*CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/DWI
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/L_Trajectory_Matrix1_"$StepSize"/*CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/DWI
					fi
			
					if [ -f "$StudyFolder"/../Parcellated/DWI/"$CASE"_R_fdt_matrix1_CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii ]; then
						echo "Parcellation done for $CASE for right hemisphere. Skipping to next subject..."
					else
						echo "Running Cortex2Cortex Yeo 7 network parcellation on DWI data Right Hemisphere for $CASE..."
						mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated  &> /dev/null
						
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/*_RSN_CSC_7Networks*.nii  &> /dev/null	
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/*_RSN_CSC_7Networks*.nii  &> /dev/null
						rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/*_fdt_matrix1_CR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii  &> /dev/null
							
						# run parcellations for each and distance adjustment
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/fdt_matrix1.dconn.nii "$NetworkFolder"/rsn_yeo_cortex_7Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/"$CASE"_R_fdt_matrix1_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/"$CASE"_R_fdt_matrix1_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$NetworkFolder"/rsn_yeo_cortex_7Networks_islands.dlabel.nii ROW "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/"$CASE"_R_fdt_matrix1_CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/fdt_matrix1.dconn.nii "$NetworkFolder"/rsn_yeo_cortex_7Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_R_fdt_matrix1_pd_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
						wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_R_fdt_matrix1_pd_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$NetworkFolder"/rsn_yeo_cortex_7Networks_islands.dlabel.nii ROW "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/"$CASE"_R_fdt_matrix1_pd_CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii						
						# setup hard links
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/*CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/*CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_pd_"$StepSize"/*CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/DWI
						ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Results/R_Trajectory_Matrix1_"$StepSize"/*CR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/DWI

					fi	
			fi
			
			##################################################################
		 	##################  DWI - thalmus2cortex #########################
			##################################################################
			
			if [ "$DatatoParcellate" == "dwi_subcortex" ]; then
			
			# supported: thalamus caudate accumbens putamen pallidum thalamus_sensory thalamus_associative
			
			for STRUCTURE in $STRUCTURES
    		do
			
			if [ -f "$StudyFolder"/../Parcellated/DWI/"$CASE"_"$STRUCTURE"2cortex_L_norm_Yeo2011_17Networks.32k_fs_LR.pscalar.nii ]; then
				echo "Parcellation done for $CASE and $STRUCTURE for left hemisphere. Skipping to next subject..."
			else
				echo "Running Subcortex2Cortex Yeo 17 network parcellation on DWI data left hemisphere for $CASE..."
					
					# clean up older work
					rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_L/*_"$STRUCTURE"2cortex_*Yeo*.pscalar.nii &> /dev/null
					rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/*_"$STRUCTURE"2cortex_*Yeo*.pscalar.nii &> /dev/null

					# run parcellations for normalized and non-normalized data
					wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_L/"$CASE"_"$STRUCTURE"2cortex_L_norm.dscalar.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_L/"$CASE"_"$STRUCTURE"2cortex_L_norm_Yeo2011_17Networks.32k_fs_LR.pscalar.nii
					wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_L/"$CASE"_"$STRUCTURE"2cortex_L.dscalar.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_L/"$CASE"_"$STRUCTURE"2cortex_L_Yeo2011_17Networks.32k_fs_LR.pscalar.nii
					
					mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated &> /dev/null
					
					# setup hard links
					ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_L/*_"$STRUCTURE"2cortex_*Yeo*.pscalar.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
					ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_L/*_"$STRUCTURE"2cortex_*Yeo*.pscalar.nii "$StudyFolder"/../Parcellated/DWI
			fi

			if [ -f "$StudyFolder"/../Parcellated/DWI/"$CASE"_"$STRUCTURE"2cortex_R_norm_Yeo2011_17Networks.32k_fs_LR.pscalar.nii ]; then
				echo "Parcellation done for $CASE and $STRUCTURE for right hemisphere. Skipping to next subject..."
			else
				echo "Running Subcortex2Cortex Yeo 17 network parcellation on DWI data right hemisphere for $CASE..."

					# clean up older work
					rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_R/*_"$STRUCTURE"2cortex_*Yeo*.pscalar.nii &> /dev/null
					rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/*_"$STRUCTURE"2cortex_*Yeo*.pscalar.nii &> /dev/null
					
					# run parcellations for normalized and non-normalized data
					wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_R/"$CASE"_"$STRUCTURE"2cortex_R_norm.dscalar.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_R/"$CASE"_"$STRUCTURE"2cortex_R_norm_Yeo2011_17Networks.32k_fs_LR.pscalar.nii
					wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_R/"$CASE"_"$STRUCTURE"2cortex_R.dscalar.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_R/"$CASE"_"$STRUCTURE"2cortex_R_Yeo2011_17Networks.32k_fs_LR.pscalar.nii

					mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated &> /dev/null
					
					# setup hard links
					ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_R/*_"$STRUCTURE"2cortex_*Yeo*.pscalar.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
					ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/fdt_paths_"$STRUCTURE"_R/*_"$STRUCTURE"2cortex_*Yeo*.pscalar.nii "$StudyFolder"/../Parcellated/DWI
			fi
			
			done
			
			fi
			
			##################################################################
		 	##################  Structure - myelin ###########################
			##################################################################
			
			# Note: Use _BC_ file for intensity normalization for residual transmit field effects to remove variability across subjects dur to head size / shape 
			
			if [ "$DatatoParcellate" == "myelin" ]; then
			
			if [ -f "$StudyFolder"/../Parcellated/Myelin/"$CASE".LR.MyelinMap_BC_Yeo2011_17Networks.32k_fs_LR.pscalar.nii ]; then
				echo "Parcellation done for $CASE. Skipping to next subject..."
			else
					echo "Running Yeo 17 network parcellation on MyelinMap data across hemispheres for $CASE..."

					# clean up older work
					rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".*.MyelinMap_BC_Yeo2011_17Networks.32k_fs_LR.pscalar.nii &> /dev/null

					# run parcellations across hemispheres
					wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".MyelinMap_BC.32k_fs_LR.dscalar.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.L.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".L.MyelinMap_BC_Yeo2011_17Networks.32k_fs_LR.pscalar.nii
					wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".MyelinMap_BC.32k_fs_LR.dscalar.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.R.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".R.MyelinMap_BC_Yeo2011_17Networks.32k_fs_LR.pscalar.nii
					wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".MyelinMap_BC.32k_fs_LR.dscalar.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".LR.MyelinMap_BC_Yeo2011_17Networks.32k_fs_LR.pscalar.nii

					mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated &> /dev/null
					
					# setup hard links
					ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/*.MyelinMap_BC_Yeo2011_17Networks.32k_fs_LR.pscalar.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
					ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/*.MyelinMap_BC_Yeo2011_17Networks.32k_fs_LR.pscalar.nii "$StudyFolder"/../Parcellated/Myelin
			fi
			fi
			
			##################################################################
		 	##################  Structure - thickness ########################
			##################################################################
			
			if [ "$DatatoParcellate" == "thickness" ]; then
			
			if [ -f "$StudyFolder"/../Parcellated/Thickness/"$CASE".LR.corrThickness_Yeo2011_17Networks.32k_fs_LR.pscalar.nii ]; then
				echo "Parcellation done for $CASE. Skipping to next subject..."
			else
					echo "Running Yeo 17 network parcellation on corrThickness data across hemispheres for $CASE..."

					# clean up older work
					rm "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".*.corrThickness_Yeo2011_17Networks.32k_fs_LR.pscalar.nii &> /dev/null

					# run parcellations across hemispheres
					wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".corrThickness.32k_fs_LR.dscalar.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.L.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".L.corrThickness_Yeo2011_17Networks.32k_fs_LR.pscalar.nii
					wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".corrThickness.32k_fs_LR.dscalar.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.R.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".R.corrThickness_Yeo2011_17Networks.32k_fs_LR.pscalar.nii
					wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".corrThickness.32k_fs_LR.dscalar.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/"$CASE".LR.corrThickness_Yeo2011_17Networks.32k_fs_LR.pscalar.nii

					mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated &> /dev/null
					
					# setup hard links
					ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/*.corrThickness_Yeo2011_17Networks.32k_fs_LR.pscalar.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated
					ln -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/fsaverage_LR32k/*.corrThickness_Yeo2011_17Networks.32k_fs_LR.pscalar.nii "$StudyFolder"/../Parcellated/Thickness
			fi
			fi
			
			##################################################
		 	##################  BOLD  ########################
			##################################################
			
			if [ "$DatatoParcellate" == "bold" ]; then
			
			NetworkFolder="/Volumes/syn1/Studies/Anticevic.DP5/fcMRI/roi/RSN_Yeo_Buckner_Choi_Cortex_Cerebellum_Striatum"

    		for STEP in $STEPS
    		do
					for BOLD in $BOLDS
					do
						if [ "$Overwrite" == "yes" ]; then
						
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null

							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
						
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
						
						fi
						
						if [ -f "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii ]; then
												
							echo "Cortex2Cortex Yeo 17 Parcellation done for $CASE run $BOLD and $STEP. Skipping to next subject..."
						else		
					    	echo "Running Cortex2Cortex Yeo 17 network parcellation on BOLD data for $CASE and $STEP..."
						
							mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated &> /dev/null
    		
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.L.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.R.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii
				
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii
						 
						 	ln -f "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD".use

						fi
						
						if [ -f "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii ]; then

							echo "Full RSN Yeo/Buckner/Choi 7 & 17 Parcellation done for $CASE run $BOLD and $STEP. Skipping to next subject..."
						else		
					    	echo "Running Full RSN Yeo/Buckner/Choi 7 & 17 area and network parcellation on BOLD data for $CASE and $STEP..."
						
							mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated &> /dev/null
						
							# Network-level
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$NetworkFolder"/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_7network_networks.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$NetworkFolder"/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_17network_networks.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii
							
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii
						
							# Parcell-level
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$NetworkFolder"/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_7network_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$NetworkFolder"/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_17network_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii
						
						fi
						
						if [ -f "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii ]; then

							echo "Cortex2Cortex RSN Yeo/Buckner/Choi 7 & 17 Parcellation done for $CASE run $BOLD and $STEP. Skipping to next subject..."
						else		
					    	echo "Running Cortex2Cortex RSN Yeo/Buckner/Choi 7 & 17 area and network parcellation on BOLD data for $CASE and $STEP..."
						
							mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated &> /dev/null
						
							# Parcell-level LR
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_7Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_17Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							# Parcell-level L
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_7Networks_islands_L.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_17Networks_islands_L.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii
							# Parcell-level R
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_7Networks_islands_R.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_17Networks_islands_R.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_"$STEP"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_"$STEP"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_"$STEP"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

						fi						
						
					done
			done
			fi

			if [ "$DatatoParcellate" == "boldfixica" ]; then
			
			NetworkFolder="/Volumes/syn1/Studies/Anticevic.DP5/fcMRI/roi/RSN_Yeo_Buckner_Choi_Cortex_Cerebellum_Striatum"

					for BOLD in $BOLDS
					do
					
						if [ "$Overwrite" == "yes" ]; then
						
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null

							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_L_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null

							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_R_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null

							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null

							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null

						fi
											
						if [ -f "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii ]; then
												
							echo "Cortex2Cortex Yeo 17 Parcellation done for $CASE run $BOLD. Skipping to next subject..."
						else		
					    	echo "Running Cortex2Cortex Yeo 17 network parcellation on BOLD data for $CASE..."
						
							mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated &> /dev/null
    		
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.L.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.R.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii
				
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii
							
							ln -f "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD".use
						
						fi
						
						if [ -f "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii ]; then

							echo "Full RSN Yeo/Buckner/Choi 7 & 17 Parcellation done for $CASE run $BOLD. Skipping to next subject..."
						else		
					    	echo "Running Full RSN Yeo/Buckner/Choi 7 & 17 area and network parcellation on BOLD data for $CASE..."
						
							mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated &> /dev/null
						
							# Network-level
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii "$NetworkFolder"/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_7network_networks.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii "$NetworkFolder"/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_17network_networks.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii
							
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii
						
							# Parcell-level
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii "$NetworkFolder"/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_7network_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii "$NetworkFolder"/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_17network_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii
						
						fi

						if [ -f "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii ]; then

							echo "Cortex2Cortex RSN Yeo/Buckner/Choi 7 & 17 Parcellation done for $CASE run $BOLD and $STEP. Skipping to next subject..."
						else		
					    	echo "Running Cortex2Cortex RSN Yeo/Buckner/Choi 7 & 17 area and network parcellation on BOLD data for $CASE..."
						
							mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated &> /dev/null
						
							# Parcell-level LR
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_7Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_17Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							# Parcell-level L
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_7Networks_islands_L.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_17Networks_islands_L.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							# Parcell-level R
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_7Networks_islands_R.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_17Networks_islands_R.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/boldfixica"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_boldfixica"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/boldfixica"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_boldfixica"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

						fi						
						
					done
				fi

			if [ "$DatatoParcellate" == "bold_raw" ]; then
			
			NetworkFolder="/Volumes/syn1/Studies/Anticevic.DP5/fcMRI/roi/RSN_Yeo_Buckner_Choi_Cortex_Cerebellum_Striatum"

					for BOLD in $BOLDS
					do
					
						if [ "$Overwrite" == "yes" ]; then
						
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null

							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_L_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null

							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_R_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null

							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii &> /dev/null

							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null
							rm -r "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii &> /dev/null

						fi
											
						if [ -f "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii ]; then
												
							echo "Cortex2Cortex Yeo 17 Parcellation done for $CASE run $BOLD. Skipping to next subject..."
						else		
					    	echo "Running Cortex2Cortex Yeo 17 network parcellation on BOLD data for $CASE..."
						
							mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated &> /dev/null
    		
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.L.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.R.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii "$StudyFolder"/../Parcellated/YeoFinal/Yeo2011_17Networks.LR.50sqmm_dilate3.0.32k_fs_LR.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_L_Yeo2011_17Networks.32k_fs_LR.pconn.nii
				
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_R_Yeo2011_17Networks.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii
						
						fi
						
						if [ -f "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii ]; then

							echo "Full RSN Yeo/Buckner/Choi 7 & 17 Parcellation done for $CASE run $BOLD. Skipping to next subject..."
						else		
					    	echo "Running Full RSN Yeo/Buckner/Choi 7 & 17 area and network parcellation on BOLD data for $CASE..."
						
							mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated &> /dev/null
						
							# Network-level
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii "$NetworkFolder"/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_7network_networks.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii "$NetworkFolder"/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_17network_networks.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii
							
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii
						
							# Parcell-level
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii "$NetworkFolder"/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_7network_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii "$NetworkFolder"/rsn_yeo-cortex_buckner-cerebellum_choi-striatum_17network_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii
						
						fi

						if [ -f "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii ]; then

							echo "Cortex2Cortex RSN Yeo/Buckner/Choi 7 & 17 Parcellation done for $CASE run $BOLD and $STEP. Skipping to next subject..."
						else		
					    	echo "Running Cortex2Cortex RSN Yeo/Buckner/Choi 7 & 17 area and network parcellation on BOLD data for $CASE..."
						
							mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated &> /dev/null
						
							# Parcell-level LR
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_7Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_17Networks_islands.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_LR_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							# Parcell-level L
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_7Networks_islands_L.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_17Networks_islands_L.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_L_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_L_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							# Parcell-level R
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_7Networks_islands_R.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							wb_command -cifti-parcellate "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD".dtseries.nii "$NetworkFolder"/Yeo_Cortex/rsn_yeo_cortex_17Networks_islands_R.dlabel.nii COLUMN "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use
							wb_command -cifti-correlation "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii -fisher-z -weights "$StudyFolder"/"$CASE"/images/functional/movement/bold"$BOLD".use

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Parcellated/"$CASE"_bold"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii

							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_R_RSN_Cortex_7Networks_islands.32k_fs_LR.pconn.nii
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii  "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.ptseries.nii 
							ln -f "$StudyFolder"/"$CASE"/images/functional/bold"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii "$StudyFolder"/../Parcellated/BOLD/"$CASE"_bold"$BOLD"_R_RSN_Cortex_17Networks_islands.32k_fs_LR.pconn.nii
				
						fi						
						
					done
				fi
}

show_usage_ciftiparcellate() {

  				echo ""
  				echo "-- DESCRIPTION:"
    			echo ""
    			reho "		*** This function is deprecated and not supported any longer."
    			reho "		*** The new usage for parcellartion can be found via the following functions:"
    			echo ""
    			echo "		boldparcellation		PARCELLATE BOLD DATA and GENERATE PCONN FILES VIA USER-SPECIFIED PARCELLATION"
    			echo "		dwidenseparcellation		PARCELLATE DENSE DWI TRACTOGRAPHY DATA VIA USER-SPECIFIED PARCELLATION"
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
    			echo "USAGE INFO PENDING..."
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
    			echo "USAGE INFO PENDING..."
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
						hcp_fix.sh "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/"$BOLD"/"$BOLD".nii.gz 2000
				fi
		done

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
						/usr/local/PostFix_beta/GitRepo/PostFix.sh "$StudyFolder"/"$CASE"/hcp "$CASE" "$BOLD" /usr/local/PostFix_beta/GitRepo "$HighPass" wb_command /usr/local/PostFix_beta/GitRepo/PostFixScenes/ICA_Classification_DualScreenTemplate.scene /usr/local/PostFix_beta/GitRepo/PostFixScenes/ICA_Classification_SingleScreenTemplate.scene
				fi
			done
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
				
				#echo "Setting up hard links for movement data for BOLD# $BOLD for $CASE... "
				
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

#########################################################################################################################
#########################################################################################################################
################################################  HCP Pipeline Wrapper Functions ########################################
#########################################################################################################################
#########################################################################################################################

# ------------------------------------------------------------------------------------------------------
#  hcp1 - Executes the PreFreeSurfer Script
# ------------------------------------------------------------------------------------------------------

hcp1() {

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

# ------------------------------------------------------------------------------------------------------
#  hcp2 - Executes the FreeSurfer Script
# ------------------------------------------------------------------------------------------------------

hcp2() {

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

# ------------------------------------------------------------------------------------------------------
#  hcp3 - Executes the PostFreeSurfer Script
# ------------------------------------------------------------------------------------------------------

hcp3() {
		
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


# ------------------------------------------------------------------------------------------------------
#  hcp4 - Executes the Volume BOLD Script
# ------------------------------------------------------------------------------------------------------

hcp4() {
		
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

# ------------------------------------------------------------------------------------------------------
#  hcp5 - Executes the Surface BOLD Script
# ------------------------------------------------------------------------------------------------------

hcp5() {

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

# ------------------------------------------------------------------------------------------------------
#  hcpd - Executes the Diffusion Processing HCP Script using TOPUP implementation
# ------------------------------------------------------------------------------------------------------

hcpd() {

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
				echo "		--subjects=<list_of_cases>			List of subjects to run"
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
    	# ParcellationFile  # e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii"

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
				echo "		--subject=<list_of_cases>			List of subjects to run"
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
				echo "--parcellationfile='/gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii' \ "
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
				echo "--parcellationfile='/gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii' \ "
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
		# ParcellationFile  # e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii"
		# ComputePConn # Specify if a parcellated connectivity file should be computed (pconn). This is done using covariance and correlation (e.g. yes; default is set to no).
		# UseWeights  # If computing a  parcellated connectivity file you can specify which frames to omit (e.g. yes' or no; default is set to no) 
		# WeightsFile # Specify the location of the weights file relative to the master study folder (e.g. /images/functional/movement/bold1.use)

		########################################## OUTPUTS #########################################

		# Outputs will be *pconn.nii files located in the location specified in the outputpath:
		#    DWIOutput="$StudyFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"

		
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
				echo "		--subject=<list_of_cases>				List of subjects to run"
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
 				echo ""
				echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--function='boldparcellation' \ "
				echo "--subjects='100206' \ "
				echo "--inputfile='bold1_Atlas_MSMAll_hp2000_clean' \ "
				echo "--inputpath='/images/functional/' \ "
				echo "--inputdatatype='dtseries' \ "
				echo "--parcellationfile='/gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
				echo "--outpath='/images/functional/' \ "
				echo "--computepconn='yes' \ "
				echo "--useweights='no' \"
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
				echo "--parcellationfile='/gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
				echo "--outpath='/images/functional/' \ "
				echo "--computepconn='yes' \ "
				echo "--useweights='no' \"
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
	
	cd "$StudyFolder"/../fcMRI/hcp.logs/
	
	minimumfilesize=100000
  	actualfilesize=$(wc -c <"$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/dti_FA.nii.gz)
  	if [ $(echo "$actualfilesize" | bc) -gt $(echo "$minimumfilesize" | bc) ]; then
  		echo "DTI Fit completed for $CASE"
  	else
  	
	if [ "$Cluster" == 1 ]; then
 		dtifit --data="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./data --out="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./dti --mask="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./nodif_brain_mask --bvecs="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./bvecs --bvals="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./bvals
	else
 		fsl_sub."$fslsub" -Q "$QUEUE" dtifit --data="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./data --out="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./dti --mask="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./nodif_brain_mask --bvecs="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./bvecs --bvals="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./bvals
	fi
	fi
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
				
		echo ""
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
  		
  			# Then check if run is complete based on size
  			if [ $(echo "$actualfilesize" | bc) -ge $(echo "$minimumfilesize" | bc) ]; then > /dev/null 2>&1
  				echo ""
  				cyaneho "DONE -- Bedpostx completed for $CASE"
  				echo ""
  				cyaneho "Check prior output logs here: $LogFolder"
  				echo ""
  				echo "--------------------------------------------------------------"
  				echo ""  			
  			fi
  		
  		else	
  				geho "Prior BedpostX run not found or incomplete for $CASE. Setting up new run..."
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
		fi	
}

show_usage_fslbedpostxgpu() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function runs the FSL bedpostx_gpu processing using a GPU-enabled node"
				echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing and completed diffusion processing: "
				echo ""
				echo " <study_folder>/<case>/hcp/<case>/Diffusion ---> DWI data needs to be here"
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>			Name of function"
				echo "		--path=<study_folder>				Path to study data folder"
				echo "		--subjects=<list_of_cases>			List of subjects to run"
				echo "		--fibers=<number_of_fibers>			Number of fibres per voxel, default 3"
				echo "		--model=<deconvolution_model>			Deconvolution model. 1: with sticks, 2: with sticks with a range of diffusivities (default), 3: with zeppelins"
				echo "		--burnin=<burnin_period_value>			Burnin period, default 1000"
				echo "		--queue=<name_of_cluster_queue>			Cluster queue name"
				echo "		--runmethod=<type_of_run>			Perform Local Interactive Run [1] or Send to scheduler [2] [If local/interactive then log will be continuously generated in different format]"
				echo "		--overwrite=<clean_prior_run>			Delete prior run for a given subject"
				echo "" 
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Anticevic.DP5/subjects' --subjects='ta6455' --function='fslbedpostxgpu' --fibers='3' --burnin='3000' --model='3' --queue='anticevic-gpu' --runmethod='2' --overwrite='yes'"
				echo ""				
				echo "-- Example with interactive terminal:"
				echo ""
				echo "AP fslbedpostxgpu /gpfs/project/fas/n3/Studies/Anticevic.DP5/subjects 'ta6455' "
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
				echo "USAGE PENDING..."
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
				echo "		--subjects=<list_of_cases>			List of subjects to run"
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
				echo "Note that this function needs to be send work to a GPU-enabled queue. It is cluster-enabled by default."
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
				echo "		--subjects=<list_of_cases>					List of subjects to run"
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

if [ "$RunType" == "1" ]; then

	if [ -d "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear ]; then
		
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality" &> /dev/null

		time aws s3 sync --dryrun s3:/"$AwsFolder"/"$CASE"/"$Modality" "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality"/ >> awshcpsync_"$CASE"_"$Modality"_`date +%Y-%m-%d-%H-%M-%S`.log 

	else

		mkdir "$StudyFolder"/"$CASE" &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE" &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality" &> /dev/null

		time aws s3 sync --dryrun s3:/"$AwsFolder"/"$CASE"/"$Modality" "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality"/ >> awshcpsync_"$CASE"_"$Modality"_`date +%Y-%m-%d-%H-%M-%S`.log 

	fi

fi

if [ "$RunType" == "2" ]; then

	if [ -d "$StudyFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear ]; then
	
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality" &> /dev/null

		time aws s3 sync s3:/"$AwsFolder"/"$CASE"/"$Modality" "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality"/ >> awshcpsync_"$CASE"_"$Modality"_`date +%Y-%m-%d-%H-%M-%S`.log 

	else

		mkdir "$StudyFolder"/"$CASE" &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE" &> /dev/null
		mkdir "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality" &> /dev/null

		time aws s3 sync s3:/"$AwsFolder"/"$CASE"/"$Modality" "$StudyFolder"/"$CASE"/hcp/"$CASE"/"$Modality"/ >> awshcpsync_"$CASE"_"$Modality"_`date +%Y-%m-%d-%H-%M-%S`.log 

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
				echo "		--subjects=<list_of_cases>			List of subjects to run"
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
#  Structural QC - customized for HCP - qcstructural
# -------------------------------------------------------------------------------------------------------------------------------

qcstructural() {


	# The following only needs modification if you have modified the
	# provided TEMPLATE_structuralQC.scene file
	DummyPath="DUMMYPATH" #This is an actual string in the TEMPLATE_structuralQC.scene file.
	
	# -- Check of overwrite flag was set
	if [ "$Overwrite" == "yes" ]; then
		echo ""
		reho " --- Removing existing structural QC scene: ${OutPath}/${CASE}.structuralQC.wb.scene"
		echo ""
		rm -f "$OutPath"/"$CASE".structuralQC.wb.scene &> /dev/null
	fi
	
	# -- Check if a given case exists
	if [ -f "$OutPath"/"$CASE".structuralQC.wb.scene ]; then
		echo ""
		geho " --- Structural QC scene completed: ${OutPath}/${CASE}.structuralQC.wb.scene"
		echo ""
		exit 1
	fi

		geho " --- Generating Structural QC scene: ${OutPath}/${CASE}.structuralQC.wb.scene"
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
	LogFolder="$OutPath"/log_qcstructural
	mkdir "$LogFolder"  &> /dev/null
	
	# -- Copy over template files
	cp -r "$TemplateFolder"/. "$OutPath" &> /dev/null
	rm "$OutPath"/TEMPLATE_original_structuralQC.scene &> /dev/null


	# -- Generate a QC scene file appropriate for each subject
	
		if [ "$Cluster" == 1 ]; then
  					echo ""
  					echo "--------------------------------------------------------------"
					echo "Running QC locally on `hostname`"
					echo "Check output here: $OutPath"
					echo "--------------------------------------------------------------"
					echo ""
					# -- Generate scene # >> "$LogFolder"/QC_"$CASE"_`date +%Y-%m-%d-%H-%M-%S`.log
					
					# -- Correct path names in scene
					#CASEPATH="$CASE/hcp/$CASE"
					#BROKENPATH="MNINonLinear/$CASE/hcp"
					
					#SurfacesName="${CASE}/hcp/${CASE} surfaces"
					#ArealName="${CASE}/hcp/${CASE} Areal Distortion"
					#VolumeName="${CASE}/hcp/${CASE} Volume Distortion"
					
					#SurfacesNameCorr="${CASE} surfaces"
					#ArealNameCorr="${CASE} Areal Distortion"
					#VolumeNameCorr="${CASE} Volume Distortion"
										
					cp "$OutPath"/TEMPLATE_structuralQC.scene "$OutPath"/"$CASE".structuralQC.wb.scene
					sed -i -e "s|DUMMYPATH|${StudyFolder}|g" "$OutPath"/"$CASE".structuralQC.wb.scene
					sed -i -e "s|DUMMYCASE|${CASE}|g" "$OutPath"/"$CASE".structuralQC.wb.scene
					#sed -i -e "s|${BROKENPATH}|MNINonLinear|g" "$OutPath"/"$CASE".structuralQC.wb.scene
					
					#sed -i -e "s|${SurfacesName}|${SurfacesNameCorr}|g" ta6455.structuralQC.wb.scene
					#sed -i -e "s|${ArealName}|${ArealNameCorr}|g" ta6455.structuralQC.wb.scene
					#sed -i -e "s|${VolumeName}|${SurfacesNameCorr}|g" ta6455.structuralQC.wb.scene

					# -- Output image of the scene
					wb_command -show-scene "$OutPath"/"$CASE".structuralQC.wb.scene 1 "$OutPath"/"$CASE".structuralQC.png 1194 539
					
					rm "$CASE".structuralQC.wb.scene-e &> /dev/null
		else
					Command1='sed "s#${DummyPath}#${StudyFolder}#g" ${OutPath}/TEMPLATE_structuralQC.scene | sed "s#100307#${CASE}#g" > ${OutPath}/${CASE}.structuralQC.wb.scene"'
					Command2='wb_command -show-scene ${OutPath}/${CASE}.structuralQC.wb.scene ${OutPath}/${CASE}.structuralQC.png 1194 539'
					Command3="$Command1 ; $Command2"
					echo "Job ID:"
					fslsub="$Scheduler" # set scheduler for fsl_sub command
					fsl_sub."$fslsub" -Q "$QUEUE" -l "$LogFolder" -R 10000 "$Command3"
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


show_usage_qcstructural() {

				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function runs the DWI preprocessing using the FUGUE method for legacy data that are not TOPUP compatible"
				echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing: "
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
				echo "		--function=<function_name>					Name of function"
				echo "		--path=<study_folder>						Path to study data folder"
				echo "		--subjects=<list_of_cases>					List of subjects to run"
				echo "		--outpath=<path_for_output_file>				Specify the output path name of the QC folder"
				echo "		--templatefolder=<path_for_the_template_folder>			Specify the output path name of the template folder (default: $TOOLS/aCode/templates)"
				echo "		--queue=<name_of_cluster_queue>					Cluster queue name"
				echo "		--scheduler=<name_of_cluster_scheduler>				Cluster scheduler program: e.g. LSF or PBS"
				echo "		--runmethod=<type_of_run>					Perform Local Interactive Run [1] or Send to scheduler [2] [If local/interactive then log will be continuously generated in different format]"
				echo "" 
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
 				echo "		--overwrite=<clean_prior_run>		Delete prior QC run"
				echo ""
				echo "-- Example with flagged parameters for a local run:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--function='qcstructural' \ "
				echo "--subjects='100206' \ "
				echo "--outpath='/gpfs/project/fas/n3/Studies/Connectome/subjects/QC/T1w' \ "
				echo "--templatefolder='$TOOLS/aCode/templates' \ "
				echo "--overwrite='no' \ "
				echo "--runmethod='1'"
				echo ""
				echo "-- Example with flagged parameters for submission to the scheduler:"
				echo ""
				echo "AP --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--function='qcstructural' \ "
				echo "--subjects='100206' \ "
				echo "--outpath='/gpfs/project/fas/n3/Studies/Connectome/subjects/QC/T1w' \ "
				echo "--templatefolder='$TOOLS/aCode/templates' \ "
				echo "--overwrite='no' \ "
				echo "--queue='anticevic' \ "
				echo "--runmethod='2' \ "
				echo "--scheduler='lsf' "
				echo "" 			
				echo "-- Example with interactive terminal:"
				echo ""
				echo "AP qcstructural /gpfs/project/fas/n3/Studies/Anticevic.DP5/subjects 'ta6455' "
				echo ""
}

#################################################################################################################################
#################################################################################################################################
################################## SOURCE REPOS, SETUP LOG & PARSE COMMAND LINE INPUTS ACROSS FUNCTIONS #########################
#################################################################################################################################
#################################################################################################################################

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

opts_GetOpt1() {
    sopt="$1"
    shift 1
    for fn in $@ ; do
    if [ `echo $fn | grep -- "^${sopt}=" | wc -w` -gt 0 ] ; then
        echo $fn | sed "s/^${sopt}=//"
        return 0
    fi
    done
}

#
# Description: 
#
#   checks command line arguments for "--help" indicating that 
#   help has been requested
#
# Input: 
#
#   The full list of command line arguments
#
   
opts_CheckForHelpRequest() {
    for fn in $@ ; do
        if [ "$fn" = "--help" ]; then
            return 0
        fi
    done
    return 1
}

#
# Description: 
#
#   Generates a timestamp for the log exec call
#

timestamp() {
 
   echo "AP.$1.`date "+%Y.%m.%d.%H.%M.%S"`.txt"
}

opts_ShowVersionIfRequested $@

# ------------------------------------------------------------------------------
#  Parse Command Line Options
# ------------------------------------------------------------------------------

# Check if general help requested in three redundant ways (AP, AP --help or AP help)

if opts_CheckForHelpRequest $@; then
    show_usage
    exit 0
fi

if [ -z "$1" ]; then
    show_usage
    exit 0

fi

if [ "$1" == "help" ]; then
	show_usage
	exit 0
fi

# Check if specific function help requested

if [ -z "$2" ]; then
    show_usage_"$1"
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

# Clear variables for new run

unset FunctionToRun
unset FunctionToRunInt
unset StudyFolder
unset CASES
unset Overwrite
unset Scheduler
unset QUEUE
unset NetID
unset ClusterName

flag=`echo $1 | cut -c1-2`

if [ "$flag" == "--" ] ; then
	echo ""
	reho "-----------------------------------------------------"
	reho "--- Running pipeline in parameter mode with flags ---"
	reho "-----------------------------------------------------"
	echo ""
	
	#
	# List of command line options across all functions
	#
	# generic input flags
	FunctionToRun=`opts_GetOpt1 "--function" $@` # function to execute
	StudyFolder=`opts_GetOpt1 "--path" $@` # local folder to work on
	CASES=`opts_GetOpt1 "--subjects" $@ | sed 's/,/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g'` # list of input cases; removing the comma
	QUEUE=`opts_GetOpt1 "--queue" $@` # <name_of_cluster_queue>			Cluster queue name	
	PRINTCOM=`opts_GetOpt1 "--printcom" $@` #Option for printing the entire command
	Scheduler=`opts_GetOpt1 "--scheduler" $@` #Specify the type of scheduler to use 
	Overwrite=`opts_GetOpt1 "--overwrite" $@` #Clean prior run and starr fresh [yes/no]
	RunMethod=`opts_GetOpt1 "--runmethod" $@` # Specifies whether to run on the cluster or on the local node
	
	# hpcsync input flags
	NetID=`opts_GetOpt1 "--netid" $@` # NetID for cluster rsync command
	HCPStudyFolder=`opts_GetOpt1 "--clusterpath" $@` # cluster study folder for cluster rsync command
	Direction=`opts_GetOpt1 "--dir" $@` # direction of rsync command (1 to cluster; 2 from cluster)
	ClusterName=`opts_GetOpt1 "--cluster" $@` # cluster address [e.g. louise.yale.edu)

	# hcpdlegacy input flags
	EchoSpacing=`opts_GetOpt1 "--echospacing" $@` # <echo_spacing_value>		EPI Echo Spacing for data [in msec]; e.g. 0.69
	PEdir=`opts_GetOpt1 "--PEdir" $@` # <phase_encoding_direction>		Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior
	TE=`opts_GetOpt1 "--TE" $@` # <delta_te_value_for_fieldmap>		This is the echo time difference of the fieldmap sequence - find this out form the operator - defaults are *usually* 2.46ms on SIEMENS
	UnwarpDir=`opts_GetOpt1 "--unwarpdir" $@` # <epi_phase_unwarping_direction>	Direction for EPI image unwarping; e.g. x or x- for LR/RL, y or y- for AP/PA; may been to try out both -/+ combinations
	DiffDataSuffix=`opts_GetOpt1 "--diffdatasuffix" $@` # <diffusion_data_name>		Name of the DWI image; e.g. if the data is called <SubjectID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR
	
	# boldparcellation input flags
	InputFile=`opts_GetOpt1 "--inputfile" $@` # --inputfile=<file_to_compute_parcellation_on>		Specify the name of the file you want to use for parcellation (e.g. bold1_Atlas_MSMAll_hp2000_clean)
	InputPath=`opts_GetOpt1 "--inputpath" $@` # --inputpath=<path_for_input_file>			Specify path of the file you want to use for parcellation relative to the master study folder and subject directory (e.g. /images/functional/)
	InputDataType=`opts_GetOpt1 "--inputdatatype" $@` # --inputdatatype=<type_of_dense_data_for_input_file>	Specify the type of data for the input file (e.g. dscalar or dtseries)
	OutPath=`opts_GetOpt1 "--outpath" $@` # --outpath=<path_for_output_file>			Specify the output path name of the pconn file relative to the master study folder (e.g. /images/functional/)
	OutName=`opts_GetOpt1 "--outname" $@` # --outname=<name_of_output_pconn_file>			Specify the suffix output name of the pconn file
	ComputePConn=`opts_GetOpt1 "--computepconn" $@` # --computepconn=<specify_parcellated_connectivity_calculation>		Specify if a parcellated connectivity file should be computed (pconn). This is done using covariance and correlation (e.g. yes; default is set to no).
	UseWeights=`opts_GetOpt1 "--useweights" $@` # --useweights=<clean_prior_run>						If computing a  parcellated connectivity file you can specify which frames to omit (e.g. yes' or no; default is set to no) 
	WeightsFile=`opts_GetOpt1 "--useweights" $@` # --weightsfile=<location_and_name_of_weights_file>			Specify the location of the weights file relative to the master study folder (e.g. /images/functional/movement/bold1.use)
	ParcellationFile=`opts_GetOpt1 "--parcellationfile" $@` # --parcellationfile=<file_for_parcellation>		Specify the absolute path of the file you want to use for parcellation (e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)

	# dwidenseparcellation input flags
	MatrixVersion=`opts_GetOpt1 "--matrixversion" $@` # --matrixversion=<matrix_version_value>		matrix solution verion to run parcellation on; e.g. 1 or 3
	ParcellationFile=`opts_GetOpt1 "--parcellationfile" $@` # --parcellationfile=<file_for_parcellation>		Specify the absolute path of the file you want to use for parcellation (e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)
	OutName=`opts_GetOpt1 "--outname" $@` # --outname=<name_of_output_pconn_file>	Specify the suffix output name of the pconn file
	
	# fslbedpostxgpu input flags
	Fibers=`opts_GetOpt1 "--fibers" $@`  # <number_of_fibers>		Number of fibres per voxel, default 3
	Model=`opts_GetOpt1 "--model" $@`    # <deconvolution_model>		Deconvolution model. 1: with sticks, 2: with sticks with a range of diffusivities (default), 3: with zeppelins
	Burnin=`opts_GetOpt1 "--burnin" $@`  # <burnin_period_value>		Burnin period, default 1000
	Jumps=`opts_GetOpt1 "--jumps" $@`    # <number_of_jumps>		Number of jumps, default 1250
	
	# probtrackxgpudense input flags
	MatrixOne=`opts_GetOpt1 "--omatrix1" $@`  # <matrix1_model>		Specify if you wish to run matrix 1 model [yes or omit flag]
	MatrixThree=`opts_GetOpt1 "--omatrix3" $@`  # <matrix3_model>		Specify if you wish to run matrix 3 model [yes or omit flag]
	NsamplesMatrixOne=`opts_GetOpt1 "--nsamplesmatrix1" $@`  # <Number_of_Samples_for_Matrix1>		Number of samples - default=5000
	NsamplesMatrixThree=`opts_GetOpt1 "--nsamplesmatrix3" $@`  # <Number_of_Samples_for_Matrix3>>		Number of samples - default=5000
	
	# awshcpsync input flags
	 Modality=`opts_GetOpt1 "--modality" $@` # <modality_to_sync>			Which modality or folder do you want to sync [e.g. MEG, MNINonLinear, T1w]"
	 Awsuri=`opts_GetOpt1 "--awsuri" $@`	 # <aws_uri_location>			Enter the AWS URI [e.g. /hcp-openaccess/HCP_900]"
		
	# qc input flags
	OutPath=`opts_GetOpt1 "--outpath" $@` # --outpath=<path_for_output_file>			Specify the output path name of the QC folder
	TemplateFolder=`opts_GetOpt1 "--templatefolder" $@` # --templatefolder=<path_for_the_template_folder>			Specify the output path name of the template folder (default: "$TOOLS"/aCode/templates)


else
	echo ""
	reho "--------------------------------------------"
	reho "--- Running pipeline in interactive mode ---"
	reho "--------------------------------------------"
	echo ""
	#
	# Read core interactive command line inputs as default positional variables (i.e. function, path & cases)
	#
	FunctionToRunInt="$1"
	StudyFolder="$2" 
	CASES="$3"
fi	


#################################################################################################################################
#################################################################################################################################
################################## EXECUTE SELECTED FUNCTION AND LOOP THROUGH ALL THE CASES #####################################
#################################################################################################################################
#################################################################################################################################


# ------------------------------------------------------------------------------
#  dicomsort function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "dicomsort" ]; then
	for CASE in $CASES
	do
  		"$FunctionToRun" "$CASE"
  	done
fi
if [ "$FunctionToRunInt" == "dicomsort" ]; then
	for CASE in $CASES
	do
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
#  Visual QC Images function loop - Julia Based
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "qaimages" ]; then
	#module load Langs/Julia/0.4.6
	cd "$StudyFolder"/QC
	rm -f ./qa.jl
	ln -s "$TOOLS"/bin/qa.jl ./ &> /dev/null
	mkdir BOLD &> /dev/null
	mkdir T1 &> /dev/null
	mkdir T1nonlin &> /dev/null
	cd "$StudyFolder" &> /dev/null
	echo "Running QC on $CASES..."
	julia -e 'include("./QC/qa.jl")' bold $CASES
	julia -e 'include("./QC/qa.jl")' t1 $CASES
fi

if [ "$FunctionToRunInt" == "qaimages" ]; then
	module load Langs/Julia/0.4.0
	cd "$StudyFolder"/QC
	ln -s "$TOOLS"/bin/qa.jl ./
	mkdir BOLD &> /dev/null
	mkdir T1 &> /dev/null
	mkdir T1nonlin &> /dev/null
	cd "$StudyFolder" &> /dev/null
	
	echo "Enter all the cases you want to run QA on:"	
		if read answer; then
			QACases=$answer
			echo "Running QC..."
			julia -e 'include("./QC/qa.jl")' bold $QACases
			julia -e 'include("./QC/qa.jl")' t1 $QACases
		fi
fi

if [ "$FunctionToRunInt" == "qcstructural" ]; then
	
	for CASE in $CASES; do
	  	"$FunctionToRunInt" "$CASE"
	done
fi

# ------------------------------------------------------------------------------
#  Visual QC Images function loop - qcstructural - wb_command based
# ------------------------------------------------------------------------------


if [ "$FunctionToRun" == "qcstructural" ]; then
	
		# Check all the user-defined parameters: 1. Overwrite, 2. OutPath, 3. TemplateFolder, 4. Cluster, 5. QUEUE
	
		if [ -z "$FunctionToRun" ]; then reho "Error: Name of function to run missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$OutPath" ]; then reho "Error: Output QC folder path value missing"; exit 1; fi
		if [ -z "$RunMethod" ]; then reho "Error: Run Method option [1=Run Locally on Node; 2=Send to Cluster] missing"; exit 1; fi
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler option missing for fsl_sub command [e.g. lsf or torque]"; exit 1; fi
		fi
		
		if [ -z "$TemplateFolder" ]; then TemplateFolder="${TOOLS}/aCode/templates"; echo "Template folder path value not explicitly specified. Using default: ${TemplateFolder}"; fi
		
		echo ""
		echo "Running qcstructural with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Study Folder: ${StudyFolder}"
		echo "Subjects: ${CASES}"
		echo "QC Output Path: ${OutPath}"
		echo "QC Scene Template: ${TemplateFolder}"
		echo "Overwrite prior run: ${Overwrite}"
		echo "--------------------------------------------------------------"
		echo "Job ID:"
		
		for CASE in $CASES
		do
  			"$FunctionToRun" "$CASE"
  		done
fi

if [ "$FunctionToRunInt" == "qcstructural" ]; then

	echo "Running qcstructural processing interactively. First enter the necessary parameters."
	# Request all the user-defined parameters: 1. Overwrite, 2. OutPath, 3. TemplateFolder, 4. Cluster, 5. QUEUE
	echo ""
	echo "Overwrite existing run [yes, no]:"
	if read answer; then Overwrite=$answer; fi
	echo ""
	echo "Enter Output QC folder path:"
	if read answer; then OutPath=$answer; fi
	echo ""
	echo "Enter template scene folder path value:"
	if read answer; then TemplateFolder=$answer; else 
	TemplateFolder="${TOOLS}/aCode/templates"
	echo "Template folder path value not explicitly specified. Using default: ${TemplateFolder}"
	fi
	echo ""
	echo "-- Run locally [1] or run on cluster [2]"
	if read answer; then Cluster=$answer; fi
	echo ""
	if [ "$Cluster" == "2" ]; then
		echo "-- Enter queue name - always submit this job to a GPU-enabled queue [e.g. anticevic-gpu]"
		if read answer; then QUEUE=$answer; fi
		echo ""
	fi
		echo "Running qcstructural with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "Study Folder: ${StudyFolder}"
		echo "Subjects: ${CASES}"
		echo "QC Output Path: ${OutPath}"
		echo "QC Scene Template: ${TemplateFolder}"
		echo "Overwrite prior run: ${Overwrite}"
		
		for CASE in $CASES
			do
  			"$FunctionToRunInt" "$CASE"
  		done
fi



# ------------------------------------------------------------------------------
#  setuphcp function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "setuphcp" ]; then
	echo "Did you make sure to check and correct subjects.txt files after the scan? [yes/no]:"
		if read answer; then
		if [ "$answer" == "yes" ]; then
			for CASE in $CASES
				do
  				"$FunctionToRun" "$CASE"
  			done
  		else
  			echo "Please setup the subject.txt files and re-run function."
		fi
		fi
fi

if [ "$FunctionToRunInt" == "setuphcp" ]; then
	echo "Did you make sure to check and correct subjects.txt files after the scan? [yes/no]:"
		if read answer; then
		if [ "$answer" == "yes" ]; then
			for CASE in $CASES
				do
  				"$FunctionToRunInt" "$CASE"
  			done
  		else
  			echo "Please setup the subject.txt files and re-run function."
		fi
		fi
fi

# ------------------------------------------------------------------------------
#  hpcsync function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "hpcsync" ]; then
	echo "You are about to sync data between the local server and Yale HPC Clusters."
		for CASE in $CASES
			do
  			"$FunctionToRun" "$CASE"
  		done
fi

if [ "$FunctionToRun" == "hpcsync2" ]; then
	echo "You are about to sync data between the local server and Yale HPC Clusters."
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

if [ "$FunctionToRunInt" == "hpcsync2" ]; then
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
#  setuplist function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "setuplist" ]; then
	echo "Enter which type of list you want to run [supported: fcmri, snr, fcmripreprocess]:"
		if read answer; then
			ListGenerate=$answer
			
			if [ "$ListGenerate" == "fcmri" ]; then
				echo "Make sure that you have setup the list script in ~/fcMRI/lists folder."
				echo "Now enter name of fcMRI analysis list script you want to use [e.g. fcmrianalysislist_cifti.sh]:"
					if read answer; then
					ListFunction=$answer 
						echo "Enter name of group you want to generate a list for [e.g. scz, hcs, ocd... ]:"
							if read answer; then
							GROUP=$answer
								echo "Note: pre-existing lists will now be deleted..."
								cd "$StudyFolder"
								cd ../fcMRI/lists
								rm subjects."$GROUP".*.list &> /dev/null
								for CASE in $CASES
									do
  									"$FunctionToRunInt" "$CASE"
  								done
  							fi
  					fi
  			fi
  			
  			if [ "$ListGenerate" == "snr" ]; then
  				echo "Note: pre-existing snr lists will now be deleted..."
  				cd "$StudyFolder"
				cd ../subjects/QC/snr
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
  		
  			if [ "$ListGenerate" == "fcmripreprocess" ]; then
				echo "Make sure that you have setup the list script in ~/fcMRI folder."
				echo "Now enter name of fcMRI analysis list script you want to use [e.g. fcmri.preprocess.list.sh]:"
					if read answer; then
					ListFunction=$answer 
						echo "Enter name of group you want to generate a list for [e.g. scz, hcs, ocd... ]:"
							if read answer; then
							GROUP=$answer
								echo "Note: pre-existing list will now be deleted..."
								cd "$StudyFolder"
								cd ../fcMRI/lists
								rm subjects."$GROUP".list &> /dev/null
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
#  ciftiparcellate function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "ciftiparcellate" ]; then
	echo "Enter which type of data you want to parcelate [supported: bold, boldfixica, bold_raw, dwi_cortex, dwi_subcortex, myelin, thickness]:"
			if read answer; then
			DatatoParcellate=$answer
				if [ "$DatatoParcellate" == "bold" ]; then
 					echo "Overwrite existing parcellation run [yes, no]:"
						if read answer; then
						Overwrite=$answer
						fi  
					echo "Enter BOLD numbers you want to run the parcellation on [e.g. 1 2 3 or 1_3 for merged BOLDs]:"
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
 				if [ "$DatatoParcellate" == "boldfixica" ]; then
 					echo "Overwrite existing parcellation run [yes, no]:"
						if read answer; then
						Overwrite=$answer
						fi  
					echo "Enter BOLD numbers you want to run the parcellation on [e.g. 1 2 3 or 1_3 for merged BOLDs]:"
						if read answer; then
						BOLDS=$answer 
								for CASE in $CASES
									do
  									"$FunctionToRunInt" "$CASE"
  								done
  						fi
  				fi 	
 				if [ "$DatatoParcellate" == "bold_raw" ]; then
 					echo "Overwrite existing parcellation run [yes, no]:"
						if read answer; then
						Overwrite=$answer
						fi  
					echo "Enter BOLD numbers you want to run the parcellation on [e.g. 1 2 3 or 1_3 for merged BOLDs]:"
						if read answer; then
						BOLDS=$answer 
								for CASE in $CASES
									do
  									"$FunctionToRunInt" "$CASE"
  								done
  						fi
  				fi 	  							
  				if [ "$DatatoParcellate" == "dwi_cortex" ]; then
  				 	echo "Overwrite existing parcellation run [yes, no]:"
						if read answer; then
						Overwrite=$answer
						fi  
					echo "Enter Step Size [Yale: 0.45, HCP: 0.3125]"
						if read answer; then
						StepSize=$answer
  							for CASE in $CASES
								do
  								"$FunctionToRunInt" "$CASE"
  							done
  						fi
  				fi
  				if [ "$DatatoParcellate" == "dwi_subcortex" ]; then
  					echo "Enter which subcortical structure probrackx results you want to parcellate"
					echo "supported: thalamus caudate accumbens putamen pallidum thalamus_sensory thalamus_associative"
						if read answer; then
						STRUCTURES=$answer
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
#  PreFreesurfer function loop (hcp1)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp1" ]; then
	
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
#  Freesurfer function loop (hcp2)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp2" ]; then
	
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
#  PostFreesurfer function loop (hcp3)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp3" ]; then
		
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
#  Volume BOLD processing function loop (hcp4)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp4" ]; then

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
#  Surface BOLD processing function loop (hcp5)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp5" ]; then
	
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
#  Diffusion processing function loop (hcpd)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcpd" ]; then
	
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
#  BOLDeParcellation function loop (boldparcellation)
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
		if [ -z "$RunMethod" ]; then reho "Error: Run Method option [1=Run Locally on Node; 2=Send to Cluster] missing"; exit 1; fi
		Cluster="$RunMethod"
		if [ "$Cluster" == "2" ]; then
				if [ -z "$QUEUE" ]; then reho "Error: Queue name missing"; exit 1; fi
				if [ -z "$Scheduler" ]; then reho "Error: Scheduler option missing for fsl_sub command [e.g. lsf or torque]"; exit 1; fi
		fi
		
		# Parse optional parameters if not specified 
		if [ -z "$UseWeights" ]; then UseWeights="no"; fi
		if [ -z "$ComputePConn" ]; then ComputePConn="no"; fi
		if [ -z "$WeightsFile" ]; then WeightsFile="no"; fi
		
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
		echo "-- Specify the absolute path of the file you want to use for parcellation (e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)"
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
		echo "-- Specify the absolute path of the file you want to use for parcellation (e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)"
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
		echo "CASES: $CASES"
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
#  palmanalysis function loop
# ------------------------------------------------------------------------------

## -- NEED TO CODE

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