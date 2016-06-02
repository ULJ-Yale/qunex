#!/bin/sh 
#set -x

# push test for aCode

## --> PENDING TASKS:
##
## --> build sub-routines for Concs, FILDs, etc
## --> Make sure to document adjustments to diffusion connectome code for GPU version [e.g. omission of matrixes etc.)
## --> Integrate functions for Stam's full dense connectomes independently of Matt's calls
## --> Integrate command line flags for functions into IF statements (Partially done but works; see example for hcpsync2)
## --> Integrate usage calls for each function (Partially done but works; see example dicomsort)
## --> Integrate log generation for each function and build IF statement to override log generation if nolog flag
## --> Issue w/logging - the exec function effectively double-logs everything for each case and for the whole command

## Commands for rsyncing to HPC clusters
##  rsync /usr/local/analysispipeline/AnalysisPipeline.sh aa353@omega1.hpc.yale.edu:/home/fas/anticevic/software/analysispipeline/

# GitRepo: https://bitbucket.org/alan.anticevic/analysispipeline/overview
## git commands:
## git add LICENSE.md
## git add AnalysisPipeline.sh
## git commit . -m'Update from nmda'
## git push origin master
## git pull origin master
## added AMPA sever - git remote add ampa ssh://aanticevic@ampa.yale.edu/usr/local/analysispipeline
## testing change from NMDA

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
# * dofcMRIp tools
# * PALM
# * Julia
# * Python (version 2.7 or above)
# * AFNI
# * Gradunwarp
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
#  General usage function
# ------------------------------------------------------------------------------

show_usage() {
  				echo ""
  				echo "HELP FOR ANALYSIS PIPELINE:"
  				echo ""
  				echo "		* GENERAL INTERACTIVE USAGE:"
  				echo "		AP <function_name> <study_folder> '<list of cases>' [options]"
  				echo ""
  				echo "		* GENERAL FLAG USAGE:"
  				echo "		AP --function=<function_name> --studyfolder=<study_folder> --subjects='<list of cases>' [options]"  				 
  				echo ""
  				echo "		* EXAMPLE TO RUN INTERACTIVELY FROM TERMINAL (NO FLAG]:"
  				echo "		AP dicomsort /Volumes/syn1/Studies/Connectome/subjects '100307 100408'"
  				echo ""
  				echo "		* EXAMPLE TO RUN WITH FLAGS (NO INTERACTIVE TERMINAL INPUT]:"
  				echo "		AP --function=dicomsort --studyfolder=/Volumes/syn1/Studies/Connectome/subjects --subjects='100307,100408'"
  				echo ""
  				echo "		* FUNCTION-SPECIFIC USAGE:"
  				echo "		AP dicomsort"
  				echo ""
  				echo "LIST OF SUPPORTED FUNCTIONS:"
  				echo ""  				
  				echo "		--- DATA ORGANIZATION FUNCTIONS ---"
  				echo "		dicomsort			SORT DICOMs and SETUP NIFTI FILES FROM DICOMS"
  				echo "		dicom2nii			CONVERT DICOMs TO NIFTI FILES"
  				echo "		setuphcp 			SETUP DATA STRUCTURE FOR HCP PROCESSING"
  				echo "		hpcsync 			SYNC WITH YALE HPC CLUSTER(S) FOR ORIGINAL HCP PIPELINES (StudyFolder/$ubject)"
  				echo "		hpcsync2			SYNC WITH YALE HPC CLUSTER(S) FOR dofcMRI INTEGRATION (StudyFolder/Subject/hcp/Subject)"
  				echo ""  				
  				echo "		--- HCP PIPELINES FUNCTIONS ---"
  				echo "		hpc1				PREFREESURFER COMPONENT OF THE HCP PIPELINE (CLUSTER AWARE)"
  				echo "		hpc2				FREESURFER COMPONENT OF THE HCP PIPELINE (CLUSTER AWARE)"
  				echo "		hpc3				POSTFREESURFER COMPONENT OF THE HCP PIPELINE (CLUSTER AWARE)"
  				echo "		hpc4				VOLUME COMPONENT OF THE HCP PIPELINE (CLUSTER AWARE)"
  				echo "		hpc5				SURFACE COMPONENT OF THE HCP PIPELINE (CLUSTER AWARE)"
  				echo "		hpcd				DIFFUSION COMPONENT OF THE HCP PIPELINE (CLUSTER AWARE)"
  				echo ""  				
  				echo "		--- GENERATE LISTS & QC FUNCTIONS ---"
  				echo "		setuplist	 		SETUP LIST FOR FCMRI ANALYSIS / PREPROCESSING or VOLUME SNR CALCULATIONS"
  				echo "		qaimages	 		RUN VISUAL QA FOR T1w and BOLD IMAGES"
  				echo "		nii4dfpconvert 		CONVERT NIFTI HCP-PROCESSED BOLD DATA TO 4DPF FORMAT FOR FILD ANALYSES"
  				echo "		cifti4dfpconvert 		CONVERT CIFTI HCP-PROCESSED BOLD DATA TO 4DPF FORMAT FOR FILD ANALYSES"
  				echo "		ciftismooth 		SMOOTH & CONVERT CIFTI BOLD DATA TO 4DPF FORMAT FOR FILD ANALYSES"
  				echo "		fidlconc 			SETUP CONC & FIDL EVEN FILES FOR GLM ANALYSES"
  				echo ""  				
  				echo "		--- TRACTOGRAPHY FUNCTIONS ---"
  				echo "		fsldtifit 			RUN FSL DTIFIT (CLUSTER AWARE)"
  				echo "		fslbedpostxgpu 			RUN FSL BEDPOSTX w/GPU (CLUSTER AWARE)"
  				echo "		isolatesubcortexrois 		ISOLATE SUBJECT-SPECIFIC SUBCORTICAL ROIs FOR TRACTOGRAPHY"
  				echo "		isolatethalamusfslnuclei 	ISOLATE FSL THALAMIC ROIs FOR TRACTOGRAPHY"
  				echo "		probtracksubcortex 		RUN FSL PROBTRACKX ACROSS SUBCORTICAL NUCLEI (CPU)"
  				echo "		pretractography			GENERATES SPACE FOR CORTICAL DENSE CONNECTOMES (CLUSTER AWARE)"
  				echo "		probtrackcortexgpu		RUN FSL PROBTRACKX ACROSS CORTICAL MESH FOR DENSE CONNECTOMES w/GPU (CLUSTER AWARE)"
  				echo "		makedenseconnectome		GENERATE DENSE CORTICAL CONNECTOMES (CLUSTER AWARE)"
  				echo ""  				
  				echo "		--- ANALYSES FUNCTIONS ---"  				
  				echo "		ciftiparcellate			PARCELLATE BOLD, DWI, MYELIN or THICKNESS DATA VIA 7 & 17 NETWORK SOLUTIONS"
  				echo "		printmatrix			EXTRACT PARCELLATED MATRIX FOR BOLD DATA VIA YEO 17 NETWORK SOLUTIONS"
  				echo "		boldmergenifti			MERGE SPECIFIED NII BOLD TIMESERIES"
  				echo "		boldmergecifti			MERGE SPECIFIED CITI BOLD TIMESERIES"
  				echo "		bolddense			COMPUTE BOLD DENSE CONNECTOME (NEEDS >30GB RAM PER BOLD)"
  				echo ""  				
  				echo "		--- FIX ICA DE-NOISING FUNCTIONS ---"    				
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
		cd ../fcMRI/lists
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


# ------------------------------------------------------------------------------------------------------
#  fidlconcorganize - Organize all CONCs and FIDL files for GLM analyses across various tasks
# ------------------------------------------------------------------------------------------------------

fidlconcorganize() {
	
	cd "$StudyFolder"
	cd ../GLM.Analyses/
	source "$ListFunction" #reads fidlconcorganize.sh 

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
  				echo "It explicitly preserves the the Human Connectome Project folder structure for preprocessing:"
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
			
			if [ "$Force" == "YES" ]; then
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
						if [ "$Force" == "YES" ]; then
						
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
					
						if [ "$Force" == "YES" ]; then
						
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
					
						if [ "$Force" == "YES" ]; then
						
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
				if [ "$Force" == "YES" ]; then
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
				if [ "$Force" == "YES" ]; then
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

    		fsl_sub.torque -Q "$QUEUE" \
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
		
		if [ "$Force" == "YES" ]; then
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
    		fsl_sub.torque -T 5000 -Q "$QUEUE" \
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
    		fsl_sub.torque -Q "$QUEUE" \
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
  		    fsl_sub.torque -Q "$QUEUE" \
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
      		fsl_sub.torque -Q "$QUEUE" \
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
#  hcpd - Executes the Diffusion Processing Script
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
		EchoSpacing="0.69" #EPI Echo Spacing for data (in msec)
		PEdir="1" #Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior
		Gdcoeffs="NONE"    
		#Gdcoeffs="/vols/Data/HCP/Pipelines/global/config/coeff_SC72C_Skyra.grad" #Coefficients that describe spatial variations of the scanner gradients. Use NONE if not available.

		#Input Variables
		Subject="$CASE"
  		SubjectID="$Subject" #Subject ID Name
  		#RawDataDir="$StudyFolder/$SubjectID/Diffusion" #Folder where unprocessed diffusion data are
  		#PosData="${RawDataDir}/RL_data1@${RawDataDir}/RL_data2@${RawDataDir}/RL_data3" #Data with positive Phase encoding direction. Up to N>=1 series (here N=2), separated by @
  		#NegData="${RawDataDir}/LR_data1@${RawDataDir}/LR_data2@${RawDataDir}/LR_data3" #Data with negative Phase encoding direction. Up to N>=1 series (here N=2), separated by @
                                                                                 #If corresponding series is missing [e.g. 2 RL series and 1 LR) use EMPTY.
  		PosData=`echo "${StudyFolder}/${Subject}/Diffusion/${Subject}_DWI_dir90_RL.nii.gz@${StudyFolder}/${Subject}/Diffusion/${Subject}_DWI_dir91_RL.nii.gz"` # "$1" #dataRL1@dataRL2@...dataRLN
  		NegData=`echo "${StudyFolder}/${Subject}/Diffusion/${Subject}_DWI_dir90_LR.nii.gz@${StudyFolder}/${Subject}/Diffusion/${Subject}_DWI_dir91_LR.nii.gz"` # "$2" #dataLR1@dataLR2@...dataLRN
   		
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
      	
      	fsl_sub.torque -T 3000 -Q "$QUEUE" \
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
 		fsl_sub.torque -Q "$QUEUE" dtifit --data="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./data --out="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./dti --mask="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./nodif_brain_mask --bvecs="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./bvecs --bvals="$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/./bvals
	fi
	fi
}

# ------------------------------------------------------------------------------------------------------
#  fslbedpostxgpu - Executes the bedpostx_gpu code from FSL (needed for probabilistic tractography)
# ------------------------------------------------------------------------------------------------------

fslbedpostxgpu() {

	cd "$StudyFolder"/../fcMRI/hcp.logs/

  	minimumfilesize=20000000
  	actualfilesize=$(wc -c <"$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion.bedpostX/merged_f1samples.nii.gz) > /dev/null 2>&1
  	if [ $(echo "$actualfilesize" | bc) -gt $(echo "$minimumfilesize" | bc) ]; then  > /dev/null 2>&1
  		echo "Bedpostx completed for $CASE"
  	else

	if [ "$Cluster" == 1 ]; then
				echo "Running bedpostx for $CASE ... "
				# load all needed modules
				module load Apps/FSL/5.0.6  > /dev/null 2>&1
				module load GPU/Cuda/5.0  > /dev/null 2>&1
				module load GPU/Cuda/6.5  > /dev/null 2>&1
				module load GPU/Cuda/7.0  > /dev/null 2>&1
				source "$TOOLS"/etc/fslconf/fsl.sh > /dev/null 2>&1
				
				if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/grad_dev.nii.gz ]; then
					echo "Found grad_dev.nii.gz and using -g flag... "
					bedpostx_gpu "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/. -n "$Fibers" -model "$Model" -b "$Burnin" -g --rician
				else	
					echo "Omitting -g flag... "
					bedpostx_gpu "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/. -n "$Fibers" -model "$Model" -b "$Burnin" --rician
				fi	
	else
				echo "Submitting bedpostx job for $CASE to $QUEUE queue ..."
				if [ -f "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/grad_dev.nii.gz ]; then
					echo "Found grad_dev.nii.gz and using -g flag... "
					fsl_sub.torque -Q "$QUEUE" bedpostx_gpu "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/. -n "$Fibers" -model "$Model" -b "$Burnin" -g --rician
				else
					echo "Omitting -g flag... "
					fsl_sub.torque -Q "$QUEUE" bedpostx_gpu "$StudyFolder"/"$CASE"/hcp/"$CASE"/T1w/Diffusion/. -n "$Fibers" -model "$Model" -b "$Burnin" --rician
				fi
	fi
	fi
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
    		fsl_sub.torque -Q "$QUEUE" \
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
#  probtrackcortexgpu - Executes the HCP Matrix1 code (Matt's original implementation for cortex)
# ------------------------------------------------------------------------------------------------------

probtrackcortexgpu() {

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
  						
  						if [ "$PD" == "YES" ]; then
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
								fsl_sub.torque -Q "$QUEUE" "$GitRepo"/DiffusionTractography/scripts/RunMatrix1Tractography_gpu.sh "$StudyFolder" "$Subject" "$DownSampleNameI" "$DiffusionResolution" "$Caret7_Command" "$Hemisphere" "$NumberOfSamples" "$StepSize" "$Curvature" "$DistanceThreshold" "$GlobalBinariesDir" "$PD"
							fi
							echo "set -- $StudyFolder $Subject $DownSampleNameI $DiffusionResolution $Caret7_Command $Hemisphere $NumberOfSamples $StepSize $Curvature $DistanceThreshold $GlobalBinariesDir $PD"
						fi
						unset ResultPD # clear directory variable
						unset PD
				done
			done
}

# ------------------------------------------------------------------------------------------------------
#  makedenseconnectome - Executes the code for creating dense cortical connectomes (Matt's original code)
# ------------------------------------------------------------------------------------------------------

makedenseconnectome() {

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
  					
  						if [ "$PD" == "YES" ]; then
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
						    	fsl_sub.torque -Q "$QUEUE" "$GitRepo"/DiffusionTractography/scripts/MakeTractographyDenseConnectomesNoMatrix2.sh "$StudyFolder" "$Subject" "$DownSampleNameI" "$DiffusionResolution" "$Caret7_Command" "$Hemisphere" "$MatrixNumber" "$PD" "$StepSize"
							fi
								echo "set -- $StudyFolder $Subject $DownSampleNameI $DiffusionResolution $Caret7_Command $Hemisphere $MatrixNumber $PD $StepSize"
						fi
				
						unset ResultPD # clear directory variable
						unset PD
				
				done
			done
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
#   checks command adds color to an echo call
#   Very useful for logging
#

ceho() {
    echo
    echo -e "\033[31m $1 \033[0m"
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

flag=`echo $1 | cut -c1-2`

if [ "$flag" == "--" ] ; then
	ceho "Running pipeline in flag mode."
	#
	# List of command line options across all functions
	#
	FunctionToRun=`opts_GetOpt1 "--function" $@` # function to execute
	StudyFolder=`opts_GetOpt1 "--path" $@` # local folder to work on
	CASES=`opts_GetOpt1 "--subjects" $@ | sed 's/,/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g'` # list of input cases; removing the comma
	NetID=`opts_GetOpt1 "--netid" $@` # NetID for cluster rsync command
	HCPStudyFolder=`opts_GetOpt1 "--clusterpath" $@` # cluster study folder for cluster rsync command
	Direction=`opts_GetOpt1 "--dir" $@` # direction of rsync command (1 to cluster; 2 from cluster)
	ClusterName=`opts_GetOpt1 "--cluster" $@` # cluster address [e.g. louise.yale.edu)
else
	ceho "Running pipeline in interactive mode."
	#
	# Read core interactive command line inputs as default positional variables (i.e. function, path & cases)
	#
	FunctionToRunInt="$1"
	StudyFolder="$2" 
	CASES="$3"
fi	

# Use --printcom=echo for just printing everything and not actually
# running the commands (the default is to actually run the commands)
#RUN=`opts_GetOpt1 "--printcom" $@`

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
#  Visual QC Images function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "qaimages" ]; then
	cd "$StudyFolder"/QC
	mkdir BOLD &> /dev/null
	mkdir T1 &> /dev/null
	mkdir T1nonlin &> /dev/null
	cd "$StudyFolder" &> /dev/null
	echo "Running QC on $CASES..."
	julia -e 'include("QC/qa.jl")' bold $CASES
	julia -e 'include("QC/qa.jl")' t1 $CASES
fi

if [ "$FunctionToRunInt" == "qaimages" ]; then
	
	cd "$StudyFolder"/QC
	mkdir BOLD &> /dev/null
	mkdir T1 &> /dev/null
	mkdir T1nonlin &> /dev/null
	cd "$StudyFolder" &> /dev/null
	
	echo "Enter all the cases you want to run QA on:"	
		if read answer; then
			QACases=$answer
			echo "Running QC..."
			julia -e 'include("QC/qa.jl")' bold $QACases
			julia -e 'include("QC/qa.jl")' t1 $QACases
		fi
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
				echo "Enter your HPC cluster folder where data are located... [e.g. /lustre/home/client/fas/anticevic/aa353/scratch/Anticevic.DP5/subjects)"
				if read answer; then
					HCPStudyFolder=$answer
					echo "Enter rsync direction [NMDA-->HPC: 1 or HPC-->NMDA: 2)"
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
				echo "Enter your HPC cluster folder where data are located... [e.g. /lustre/home/client/fas/anticevic/aa353/scratch/Anticevic.DP5/subjects)"
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
 					echo "Overwrite existing parcellation run [YES, NO]:"
						if read answer; then
						Force=$answer
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
 					echo "Overwrite existing parcellation run [YES, NO]:"
						if read answer; then
						Force=$answer
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
 					echo "Overwrite existing parcellation run [YES, NO]:"
						if read answer; then
						Force=$answer
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
  				 	echo "Overwrite existing parcellation run [YES, NO]:"
						if read answer; then
						Force=$answer
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

 	echo "Overwrite existing merged run [YES, NO]:"
		if read answer; then
		Force=$answer
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
	echo "Overwrite existing run [YES, NO]:"
		if read answer; then
		Force=$answer
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
	echo "Overwrite existing postfix scenes [YES, NO]:"
		if read answer; then
		Force=$answer
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

if [ "$FunctionToRunInt" == "fslbedpostxgpu" ]; then
	echo "Enter # of fibers per voxel [e.g. 3]:"
		if read answer; then
		Fibers=$answer 
		fi
	echo "Enter model for bedpostx [1 for monoexponential, 2 for multiexponential]:"
		if read answer; then
		Model=$answer 	
		fi
	echo "Enter burnin period for bedpostx [e.g. 3000; default 1000]:"
		if read answer; then
		Burnin=$answer
		fi 		
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
#  PreFreesurfer function loop (hcp1)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp1" ]; then
		echo "Note: Making sure global environment script is sourced..."
	if [ -f "$TOOLS/hcpsetup.sh" ]; then
		. "$TOOLS/hcpsetup.sh" 
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
  	else
		echo "ERROR: Environment script is missing. Check your user profile paths!"
	fi
fi

# ------------------------------------------------------------------------------
#  Freesurfer function loop (hcp2)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp2" ]; then
		echo "Note: Making sure global environment script is sourced..."
	if [ -f "$TOOLS/hcpsetup.sh" ]; then
		. "$TOOLS/hcpsetup.sh" 
		MasterFolder="$StudyFolder"
		echo "Overwrite FreeSurfer run (YES, NO]:"
	if read answer; then
		Force=$answer  
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
  	else
		echo "ERROR: Environment script is missing. Check your user profile paths!"
	fi
fi

# ------------------------------------------------------------------------------
#  PostFreesurfer function loop (hcp3)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp3" ]; then
		echo "Note: Making sure global environment script is sourced..."
	if [ -f "$TOOLS/hcpsetup.sh" ]; then
		. "$TOOLS/hcpsetup.sh" 
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
  	else
		echo "ERROR: Environment script is missing. Check your user profile paths!"
	fi
fi

# ------------------------------------------------------------------------------
#  Volume BOLD processing function loop (hcp4)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp4" ]; then
		echo "Note: Making sure global environment script is sourced..."
		if [ -f "$TOOLS/hcpsetup.sh" ]; then
		. "$TOOLS/hcpsetup.sh" 
		MasterFolder="$StudyFolder" 
		echo "Enter BOLD numbers you want to run the HCP Volume pipeline on [e.g. 1 2 3]:"
		if read answer; then
			BOLDS=$answer
		echo "Enter Phase Encoding Directions for BOLDs or only a single value if no counterbalancing (y=PA; y-=AP; x=RL; -x=LR]:"
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
  	else
		echo "ERROR: Environment script is missing. Check your user profile paths!"
	fi
fi

# ------------------------------------------------------------------------------
#  Surface BOLD processing function loop (hcp5)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcp5" ]; then
		echo "Note: Making sure global environment script is sourced..."
		if [ -f "$TOOLS/hcpsetup.sh" ]; then
		. "$TOOLS/hcpsetup.sh" 
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
  	else
		echo "ERROR: Environment script is missing. Check your user profile paths!"
	fi
fi

# ------------------------------------------------------------------------------
#  Diffusion processing function loop (hcpd)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "hcpd" ]; then
		echo "Note: Making sure global environment script is sourced..."
	if [ -f "$TOOLS/hcpsetup.sh" ]; then
		. "$TOOLS/hcpsetup.sh" 
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
  	else
		echo "ERROR: Environment script is missing. Check your user profile paths!"
	fi
fi


# ------------------------------------------------------------------------------
#  Pretractography processing function loop (Matt's original code)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "pretractography" ]; then
		echo "Note: Making sure global environment script is sourced..."
	if [ -f "$TOOLS/hcpsetup.sh" ]; then
		. "$TOOLS/hcpsetup.sh" 
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
   	else
		echo "ERROR: Environment script is missing. Check your user profile paths!"
	fi 	
fi


# ------------------------------------------------------------------------------
#  Matrix 1 Cortex processing function loop (Matt's original code w/o m2 and m4)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "probtrackcortexgpu" ]; then
		echo "Note: Making sure global environment script is sourced..."
	if [ -f "$TOOLS/hcpsetup.sh" ]; then
		. "$TOOLS/hcpsetup.sh" 
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
    else
		echo "ERROR: Environment script is missing. Check your user profile paths!"
	fi 	 	
fi
  

# ------------------------------------------------------------------------------
#  Dense Connectome Cortex function loop (Matt's original code following GPU)
# ------------------------------------------------------------------------------

if [ "$FunctionToRunInt" == "makedenseconnectome" ]; then
		echo "Note: Making sure global environment script is sourced..."
	if [ -f "$TOOLS/hcpsetup.sh" ]; then
		. "$TOOLS/hcpsetup.sh" 
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
  	else
		echo "ERROR: Environment script is missing. Check your user profile paths!"
	fi 	
fi  		

exit 0