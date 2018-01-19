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
#  Parcellation wrapper for dense thickness and myelin data
#
# ## License
#
# * The ComputeFunctionalConnectivity.sh = the "Software"
# * This Software is distributed "AS IS" without warranty of any kind, either 
# * expressed or implied, including, but not limited to, the implied warranties
# * of merchantability and fitness for a particular purpose.
#
# ### TODO
#
# ## Description 
#   
# This script, ComputeFunctionalConnectivity.sh, implements parcellation on the DWI dense connectomes 
# using a whole-brain parcellation (e.g. Glasser parcellation with subcortical labels included)
# 
# ## Prerequisite Installed Software
#
# * Connectome Workbench (v1.0 or above)
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. $./ComputeFunctionalConnectivity.sh --help
#
# ### Expected Previous Processing
# 
# * The necessary input files are BOLD from previous processing
# * These may be stored in: "$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/ 
#
#~ND~END~

usage() {

# -------------------------------------------------------------------------------------------------------------------
# EXAMPLE inputs from Matlab into fc_ComputeSeedMapsMultiple and fc_ComputeGBC3:
# -------------------------------------------------------------------------------------------------------------------
# 		fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf, method, ignore, cv)
# 		INPUT
# 		flist   	- A .list file of subject information.
# 		roinfo	    - An ROI file.
# 		inmask		- An array mask defining which frames to use (1) and which not (0) [0]
# 		options		- A string defining which subject files to save ['']:
# 		r		- save map of correlations
# 		f     - save map of Fisher z values
# 		cv	- save map of covariances
# 		z		- save map of Z scores
# 		targetf	- The folder to save images in ['.'].
# 		method    - Method for extracting timeseries - 'mean' or 'pca' ['mean'].
# 		ignore    - Do we omit frames to be ignored ['no']
# 		                -> no:    do not ignore any additional frames
# 		                -> event: ignore frames as marked in .fidl file
# 		                -> other: the column in *_scrub.txt file that matches bold file to be used for ignore mask
# 		cv        - Whether covariances should be computed instead of correlations.
# ------------------------------------------------------------------------------------------------------------------- 		
# 		fc_ComputeGBC3(flist, command, mask, verbose, target, targetf, rsmooth, rdilate, ignore, time, cv, vstep) 
# 		INPUT 
# 		flist       - conc-like style list of subject image files or conc files:
# 		                subject id:<subject_id>
# 		                roi:<path to the individual's ROI file>
# 		                file:<path to bold files - one per line>
# 		             or a well strucutured string (see g_ReadFileList).
# 		command     - the type of gbc to run: mFz, aFz, pFz, nFz, aD, pD, nD,
# 		             mFzp, aFzp, ...
# 		             <type of gbc>:<parameter>|<type of gbc>:<parameter> ...
# 		mask        - An array mask defining which frames to use (1) and
# 		             which not (0). All if empty.
# 		verbose     - Report what is going on. [false]
# 		target      - Array of ROI codes that define target ROI [default:
# 		             FreeSurfer cortex codes]
# 		targetf     - Target folder for results.
# 		rsmooth     - Radius for smoothing (no smoothing if empty). []
# 		rdilate     - Radius for dilating mask (no dilation if empty). []
# 		ignore      - The column in *_scrub.txt file that matches bold file to
# 		             be used for ignore mask. All if empty. []
# 		time        - Whether to print timing information. [false]
# 		cv          - Whether to compute covariances instead of correlations.
# 		             [false]
# 		vstep       - How many voxels to process in a single step. [1200]
# -------------------------------------------------------------------------------------------------------------------
	
				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function implements Global Brain Connectivity (GBC) or seed-based functional connectivity (FC) on the dense or parcellated (e.g. Glasser parcellation)."
				echo ""
				echo ""
				echo "For more detailed documentation run <help fc_ComputeGBC3>, <help gmrimage.mri_ComputeGBC> or <help fc_ComputeSeedMapsMultiple> inside matlab"
				echo ""
				echo ""
				echo "-- REQUIRED GENERAL PARMETERS FOR A GROUP RUN:"
				echo ""
				echo "		--calculation=<type_of_calculation>					Run <seed> or <gbc> calculation for functional connectivity."
				echo "		--runtype=<type_of_run>					Run calculation on a <list> (requires a list input), on <individual> subjects (requires manual specification) or a <group> of individual subjects (equivalent to a list, but with manual specification)"
				echo "		--flist=<subject_list_file>				Specify *.list file of subject information. If specified then --subjectsfolder, --inputfile, --subject and --outname are omitted"
				echo "		--targetf=<path_for_output_file>			Specify the absolute path for output folder. If using --runtype='individual' and left empty the output will default to --inputpath location for each subject"
				echo "		--ignore=<frames_to_ignore>				The column in *_scrub.txt file that matches bold file to be used for ignore mask. All if empty. Default is [] "
				echo "		--mask=<which_frames_to_use>				An array mask defining which frames to use (1) and which not (0). All if empty. If single value is specified then this number of frames is skipped."
				echo ""
				echo "-- REQUIRED GENERAL PARMETERS FOR AN INDIVIDUAL SUBJECT RUN:"
				echo ""
 				echo "		--subjectsfolder=<folder_with_subjects>					Path to study subjects folder"
				echo "		--subject=<list_of_cases>				List of subjects to run"
				echo "		--inputfiles=<files_to_compute_connectivity_on>		Specify the comma separated file names you want to use (e.g. /bold1_Atlas_MSMAll.dtseries.nii,bold2_Atlas_MSMAll.dtseries.nii)"
				echo "		--inputpath=<path_for_input_file>			Specify path of the file you want to use relative to the master study folder and subject directory (e.g. /images/functional/)"
				echo "		--outname=<name_of_output_file>				Specify the suffix name of the output file name"  
				echo ""
				echo "-- OPTIONAL GENERAL PARAMETERS: "	
				echo ""
			 	echo "		--overwrite=<clean_prior_run>				Delete prior run for a given subject"
				echo "		--extractdata=<save_out_the_data_as_as_csv>		Specify if you want to save out the matrix as a CSV file (only available if the file is a ptseries) "
				echo "		--covariance=<compute_covariance>			Whether to compute covariances instead of correlations (true / false). Default is [false]"
				echo ""
				echo "-- REQUIRED GBC PARMETERS:"
				echo ""
				echo "		--target=<which_roi_to_use>				Array of ROI codes that define target ROI [default: FreeSurfer cortex codes]"
				echo "		--rsmooth=<smoothing_radius>				Radius for smoothing (no smoothing if empty). Default is []"
				echo "		--rdilate=<dilation_radius>				Radius for dilating mask (no dilation if empty). Default is []"
				echo "		--command=<type_of_gbc_to_run>				Specify the the type of gbc to run. This is a string describing GBC to compute. E.g. 'mFz:0.1|mFz:0.2|aFz:0.1|aFz:0.2|pFz:0.1|pFz:0.2' "
				echo ""
				echo "                   > mFz:t  ... computes mean Fz value across all voxels (over threshold t) "
				echo "                   > aFz:t  ... computes mean absolute Fz value across all voxels (over threshold t) "
				echo "                   > pFz:t  ... computes mean positive Fz value across all voxels (over threshold t) "
				echo "                   > nFz:t  ... computes mean positive Fz value across all voxels (below threshold t) "
				echo "                   > aD:t   ... computes proportion of voxels with absolute r over t "
				echo "                   > pD:t   ... computes proportion of voxels with positive r over t "
				echo "                   > nD:t   ... computes proportion of voxels with negative r below t "
				echo "                   > mFzp:n ... computes mean Fz value across n proportional ranges "
				echo "                   > aFzp:n ... computes mean absolute Fz value across n proportional ranges "
				echo "                   > mFzs:n ... computes mean Fz value across n strength ranges "
				echo "                   > pFzs:n ... computes mean Fz value across n strength ranges for positive correlations "
				echo "                   > nFzs:n ... computes mean Fz value across n strength ranges for negative correlations "
				echo "                   > mDs:n  ... computes proportion of voxels within n strength ranges of r "
				echo "                   > aDs:n  ... computes proportion of våoxels within n strength ranges of absolute r "
				echo "                   > pDs:n  ... computes proportion of voxels within n strength ranges of positive r "
				echo "                   > nDs:n  ... computes proportion of voxels within n strength ranges of negative r "  
				echo ""
				echo "-- OPTIONAL GBC PARMETERS:"
				echo "" 
				echo "		--verbose=<print_output_verbosely>			Report what is going on. Default is [false]"
				echo "		--time=<print_time_needed>				Whether to print timing information. [false]"
				echo "		--vstep=<how_many_voxels>				How many voxels to process in a single step. Default is [1200]"
				echo ""
				echo "-- REQUIRED SEED FC PARMETERS:"
				echo ""
 				echo "		--roinfo=<roi_seed_files>				An ROI file for the seed connectivity "
				echo ""
				echo "-- OPTIONAL SEED FC PARMETERS: "
			 	echo ""
 				echo "		--method=<method_to_get_timeseries>		Method for extracting timeseries - 'mean' or 'pca' Default is ['mean'] "
 				echo "		--options=<calculations_to_save>			A string defining which subject files to save. Default assumes all [''] "
 				echo ""
 				echo "			> r ... save map of correlations "
  				echo "			> f ... save map of Fisher z values "
 				echo "			> cv ... save map of covariances "
  				echo "			> z ... save map of Z scores "
 				echo ""
 				echo "-- Examples:"
				echo ""
				echo "ComputeFunctionalConnectivity.sh \ "
				echo "--subjectsfolder='<folder_with_subjects>' \ "
				echo "--calculation='seed' \ "
				echo "--runtype='individual' \ "
				echo "--subject='<case_id>' \ "
				echo "--inputfiles='bold1_Atlas_MSMAll.dtseries.nii' \ "
				echo "--inputpath='/images/functional' \ "
				echo "--extractdata='yes' \ "
				echo "--extractdata='yes' \ "
				echo "--ignore='udvarsme' \ "
				echo "--roinfo='ROI_Names_File.names' \ "
				echo "--options='' \ "
				echo "--method='' \ "
				echo "--targetf='<path_for_output_file>' \ "
				echo "--mask='5' \ "
				echo "--covariance='false' "
				echo ""	
				echo "ComputeFunctionalConnectivity.sh \ "
				echo "--subjectsfolder='<folder_with_subjects>' \ "
				echo "--runtype='list' \ "
				echo "--flist='subjects.list' \ "
				echo "--extractdata='yes' \ "
				echo "--outname='<name_of_output_file>' \ "
				echo "--ignore='udvarsme' \ "
				echo "--roinfo='ROI_Names_File.names' \ "
				echo "--options='' \ "
				echo "--method='' \ "
				echo "--targetf='<path_for_output_file>' \ "
				echo "--mask='5' "
				echo "--covariance='false' "
				echo ""
				echo "ComputeFunctionalConnectivity.sh \ "
				echo "--subjectsfolder='<folder_with_subjects>' \ "
				echo "--calculation='gbc' \ "
				echo "--runtype='individual' \ "
				echo "--subject='100206' \ "
				echo "--inputfiles='bold1_Atlas_MSMAll.dtseries.nii' \ "
				echo "--inputpath='/images/functional' \ "
				echo "--extractdata='yes' \ "
				echo "--outname='GBC' \ "
				echo "--ignore='udvarsme' \ "
				echo "--command='mFz:' \ "
				echo "--targetf='<path_for_output_file>' \ "
				echo "--mask='5' \ "
				echo "--target='' \ "
				echo "--rsmooth='0' \ "
				echo "--rdilate='0' \ "
				echo "--verbose='true' \ "
				echo "--time='true' \ "
				echo "--vstep='10000'"
				echo "--covariance='false' "
				echo ""
				echo ""	
				echo "ComputeFunctionalConnectivity.sh \ "
				echo "--subjectsfolder='<folder_with_subjects>' \ "
				echo "--calculation='gbc' \ "
				echo "--runtype='list' \ "
				echo "--flist='subjects.list' \ "
				echo "--extractdata='yes' \ "
				echo "--outname='GBC' \ "
				echo "--ignore='udvarsme' \ "
				echo "--command='mFz:' \ "
				echo "--targetf='<path_for_output_file>' \ "
				echo "--mask='5' \ "
				echo "--target='' \ "
				echo "--rsmooth='0' \ "
				echo "--rdilate='0' \ "
				echo "--verbose='true' \ "
				echo "--time='true' \ "
				echo "--vstep='10000'"
				echo "--covariance='false' "
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

# BOLD data should be pre-processed and in NIFTI or CIFTI format
# Mandatory input parameters are defined in the help call

########################################## OUTPUTS #########################################

# Outputs will be  files located in the location specified in the outputpath

#  Get the command line options for this script
#

get_options() {
    local scriptName=$(basename ${0})
    local arguments=($@)
    
    # initialize global output variables

    unset SubjectsFolder	# --subjectsfolder=				
    unset CASE				# --subject=		
    unset InputFiles		# --inputfile=		
    unset InputPath			# --inputpath=		
    unset OutName			# --outname=		
    unset OutPath			# --targetf=			
    unset Overwrite			# --overwrite=		
    unset ExtractData		# --extractdata=
    unset Calculation		# --calculation=	
   
    unset RunType			# --runtype= 		
    unset FileList			# --flist=			
	unset IgnoreFrames		# --ignore=			
	unset MaskFrames		# --mask=		
	unset Covariance 		# --covariance=		
	
	unset TargetROI			# --target=			
	unset RadiusSmooth		# --rsmooth=		
	unset RadiusDilate		# --rdilate=		
	unset GBCCommand		# --command=		
	unset Verbose			# --verbose=		
	unset ComputeTime		# --time=			
	unset VoxelStep			# --vstep=			
	
	unset ROIInfo			# --roinfo=			
	unset FCCommand			# --options=		
	unset Method			# --method=		
    
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
            --subjectsfolder=*)
                SubjectsFolder=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --subject=*)
                CASE=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --inputfiles=*)
                InputFiles=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --inputpath=*)
                InputPath=${argument/*=/""}
                index=$(( index + 1 ))
                ;;                   
            --outname=*)
                OutName=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --targetf=*)
                OutPath=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --overwrite=*)
                Overwrite=${argument/*=/""}
                index=$(( index + 1 ))
                ;;      
            --extractdata=*)
                ExtractData=${argument/*=/""}
                index=$(( index + 1 ))
                ;;	
            --calculation=*)
                Calculation=${argument/*=/""}
                index=$(( index + 1 ))
                ;;       
            --runtype=*)
                RunType=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --flist=*)
                FileList=${argument/*=/""}
                index=$(( index + 1 ))
                ;;                                    
            --ignore=*)
                IgnoreFrames=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --mask=*)
                MaskFrames=${argument/*=/""}
                index=$(( index + 1 ))
                ;;             
            --covariance=*)
                Covariance=${argument/*=/""}
                index=$(( index + 1 ))
                ;;       
            --target=*)
                TargetROI=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --rsmooth=*)
                RadiusSmooth=${argument/*=/""}
                index=$(( index + 1 ))
                ;;                                
            --rdilate=*)
                RadiusDilate=${argument/*=/""}
                index=$(( index + 1 ))
                ;;  
            --command=*)
                GBCCommand=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --verbose=*)
                Verbose=${argument/*=/""}
                index=$(( index + 1 ))
                ;;   
            --time=*)
                ComputeTime=${argument/*=/""}
                index=$(( index + 1 ))
                ;;                                
            --vstep=*)
                VoxelStep=${argument/*=/""}
                index=$(( index + 1 ))
                ;;       
            --roinfo=*)
                ROIInfo=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --options=*)
                FCCommand=${argument/*=/""}
                index=$(( index + 1 ))
                ;;                  
            --method=*)
                Method=${argument/*=/""}
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

echo ""

    # -- check general required parameters
    
    if [ -z ${OutPath} ]; then
        usage
        reho "ERROR: <path_for_output> not specified."
        exit 1
    fi
    
    if [ -z ${Calculation} ]; then
        usage
        reho "ERROR: <type_of_calculation> not specified."
        exit 1
    fi
    
    if [ -z ${RunType} ]; then
        usage
        reho "ERROR: <type_of_run> not specified."
        exit 1
    fi
    
    # -- check run type (group or individual
    		
    # - check options for individual run
    if [ ${RunType} == "individual" ] || [ ${RunType} == "group" ]; then
    	if [ -z ${SubjectsFolder} ]; then
        	usage
            reho "ERROR: <subjects-folder-path> not specified>"
        	echo ""
        	exit 1
    	fi
    	if [ -z ${CASE} ]; then
        	usage
        	reho "ERROR: <subject_id> not specified."
        	echo ""
        	exit 1
    	fi
    	if [ -z ${InputFiles} ]; then
        	usage
        	reho "ERROR: <file(s)_to_compute_connectivity_on> not specified."
        	echo ""
        	exit 1
    	fi
        if [ -z ${InputPath} ]; then
        	usage
        	reho "ERROR: <absolute_path_to_data> not specified."
        	echo ""
        	exit 1
    	fi
    	if [ -z ${OutName} ]; then
        	usage
        	reho "ERROR: <name_of_output_file> not specified."
        exit 1
    	fi
    fi
    
    # - check options for group run
    if [ ${RunType} == "list" ]; then
    	if [ -z ${FileList} ]; then
        	usage
        	reho "ERROR: <group_list_file_to_compute_connectivity_on> not specified."
        	echo ""
        	exit 1
    	fi
    fi
    
    # -- check additional mandatory options
    if [ -z ${IgnoreFrames} ]; then
        reho "WARNING: <bad_movement_frames_to_ignore_command> not specified. Assuming no input."
        IgnoreFrames=""
        echo ""
    fi
    
    if [ -z ${MaskFrames} ]; then
        reho "WARNING: <frames_to_mask_out> not specified. Assuming zero."
        MaskFrames=""
        echo ""
    fi
	
	if [ -z ${Covariance} ]; then
        reho "WARNING: <compute_covariance> not specified. Assuming correlation."
        Covariance="false"
        echo ""
    fi
    
    # -- check which function is specified and then check additional needed parameters
    
   	# - check options for seed FC
    if [ ${Calculation} == "seed" ]; then
   		if [ -z ${ROIInfo} ]; then
        	usage
        	reho "ERROR: <roi_seed_file> not specified."
        	echo ""
        	exit 1
    	fi
        if [ -z ${FCCommand} ]; then
        	reho "WARNING: <calculations_to_save> for seed FC not specified. Assuming all calculations should be saved."
        	FCCommand=""
        	echo ""
    	fi
    	if [ -z ${Method} ]; then
        	reho "WARNING: <method_to_get_timeseries> not specified. Assuming defaults [mean]."
        	Method=""
        	echo ""
    	fi
    fi
    
    # - check options for GBC
    if [ ${Calculation} == "gbc" ]; then
        if [ -z ${GBCCommand} ]; then
        	reho "WARNNING: <commands_for_gbc> not specified. Assuming standard mFz calculation."
        	GBCCommand="mFz:"
        	echo ""
    	fi
    	if [ -z ${TargetROI} ]; then
        	reho "WARNING: <target_roi_for_gbc> not specified. Assuming whole-brain calculation."
        	TargetROI="[]"
        	echo ""
    	fi
    	if [ -z ${RadiusSmooth} ]; then
        	reho "WARNING: <smoothing_radius> not specified. Assuming no smoothing."
        	RadiusSmooth="0"
    	    echo ""
    	fi
    	if [ -z ${RadiusDilate} ]; then
        	reho "WARNING: <dilation_radius>. Assuming no dilation."
        	RadiusDilate="0"
    	    echo ""
    	fi
    	if [ -z ${Verbose} ]; then
        	reho "WARNING: <verbose_output> not specified. Assuming 'true'."
        	Verbose="true"
    	    echo ""
    	fi
    	if [ -z ${ComputeTime} ]; then
        	reho "WARNING: <computation_time> not specified. Assuming 'true'"
        	ComputeTime="true"
    	    echo ""
    	fi
    	if [ -z ${VoxelStep} ]; then
        	reho "WARNING: <voxel_steps_to_use> not specified. Assuming '1200'"
        	VoxelStep="1200"	
    	    echo ""
    	fi
    fi

	# set StudyFolder
	cd $SubjectsFolder/../ &> /dev/null
	StudyFolder=`pwd` &> /dev/null
			    
    # report options
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo "	OutPath: ${OutPath}"
    echo "	Overwrite: ${Overwrite}"
    echo "	ExtractData: ${ExtractData}"
    echo "	Calculation: ${Calculation}"
    echo "	RunType: ${RunType}"
    echo "	IgnoreFrames: ${IgnoreFrames}"
    echo "	MaskFrames: ${MaskFrames}"
    echo "	Covariance: ${Covariance}"
    if [ ${RunType} == "list" ]; then
    echo "	FileList: ${FileList}"
    fi
    if [ ${RunType} == "individual" ] || [ ${RunType} == "group" ]; then
    echo "	SubjectsFolder: ${SubjectsFolder}"
    echo "	Subjects: ${CASE}"
    echo "	InputFiles: ${InputFiles}"
    echo "	InputPath: ${SubjectsFolder}/<subject_id>/${InputPath}"
    echo "	OutName: ${OutName}"
    fi
    if [ ${Calculation} == "gbc" ]; then
    echo "	TargetROI: ${TargetROI}"
    echo "	RadiusSmooth: ${RadiusSmooth}"
    echo "	RadiusDilate: ${RadiusDilate}"
    echo "	GBCCommand: ${GBCCommand}"
    echo "	Verbose: ${Verbose}"
    echo "	ComputeTime: ${ComputeTime}"
    echo "	VoxelStep: ${VoxelStep}"
    fi
	if [ ${Calculation} == "seed" ]; then
    echo "	ROIInfo: ${ROIInfo}"
    echo "	FCCommand: ${FCCommand}"
    echo "	Method: ${Method}"
    fi
    echo "-- ${scriptName}: Specified Command-Line Options - End --"
    echo ""
    geho "------------------------- Start of work --------------------------------"
    echo ""
}

######################################### DO WORK ##########################################

main() {

# Get Command Line Options
get_options $@

# parse all the input cases for an individual or group run
INPUTCASES=`echo "$CASE" | sed 's/,/ /g'`
echo ""

# -- Define all inputs and outputs depending on data type input

if [ ${RunType} == "individual" ]; then
	
	for INPUTCASE in $INPUTCASES; do
			# -- Define inputs
			geho "--- Establishing paths for all input and output folders:"
			echo ""
			if [ ${OutPath} == "" ]; then
				OutPath=${SubjectsFolder}/${INPUTCASE}/${InputPath}
			fi
			# parse input from the InputFiles variable
			InputFiles=`echo "$InputFiles" | sed 's/,/ /g;s/|/ /g'`
			# cleanup prior tmp lists
			rm -rf ${SubjectsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName} > /dev/null 2>&1	
			# generate output directories
			mkdir ${SubjectsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName} > /dev/null 2>&1
			mkdir ${OutPath} > /dev/null 2>&1
			# generate the temp list
			echo "subject id:$INPUTCASE" >> ${SubjectsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName}/${OutName}.list
			for InputFile in $InputFiles; do echo "file:$SubjectsFolder/$INPUTCASE/$InputPath/$InputFile" >> ${SubjectsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName}/${OutName}.list; done	
			FinalInput="${SubjectsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName}/${OutName}.list"
	done
fi

if [ ${RunType} == "group" ]; then
	
	# generate output directories
	mkdir ${OutPath} > /dev/null 2>&1
	# cleanup prior tmp lists
	rm -rf ${OutPath}/templist_${Calculation}_${OutName} > /dev/null 2>&1	
	mkdir ${OutPath}/templist_${Calculation}_${OutName} > /dev/null 2>&1	
			
	for INPUTCASE in $INPUTCASES; do
			# -- Define inputs
			geho "--- Establishing paths for all input and output folders for $INPUTCASE:"
			echo ""
			# parse input from the InputFiles variable
			InputFiles=`echo "$InputFiles" | sed 's/,/ /g;s/|/ /g'`
			# generate the temp list
			echo "subject id:$INPUTCASE" >> ${OutPath}/templist_${Calculation}_${OutName}/${OutName}.list
			for InputFile in $InputFiles; do echo "file:$SubjectsFolder/$INPUTCASE/$InputPath/$InputFile" >> ${OutPath}/templist_${Calculation}_${OutName}/${OutName}.list; done	
			FinalInput="${OutPath}/templist_${Calculation}_${OutName}/${OutName}.list"
	done
fi
	# -- Echo inputs
	echo ""
	echo "Seed functional connectivity inputs:"
	echo ""
	more $FinalInput
	echo ""	
	# -- Echo outputs
	echo "Seed functional connectivity will be saved here for each specified ROI:"
	echo "--> ${OutPath}"

if [ ${RunType} == "list" ]; then
	FinalInput=${FileList}
fi
	
	# check if FC seed run is specified
	if [ ${Calculation} == "seed" ]; then
		# -- run FC seed command: 
		# Call to get matlab help --> matlab -nosplash -nodisplay -nojvm -r "help fc_ComputeGBC3,quit()"
		# Full function input     --> fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf, method, ignore, cv)
		# Example with string input --> matlab -nosplash -nodisplay -nojvm -r "fc_ComputeSeedMapsMultiple('listname:$CASE-$OutName|subject id:$CASE|file:$InputFile', '$ROIInfo', $MaskFrames, '$FCCommand', '$OutPath', '$Method', '$IgnoreFrames', $Covariance);,quit()"
		matlab -nosplash -nodisplay -nojvm -r "fc_ComputeSeedMapsMultiple('$FinalInput', '$ROIInfo', $MaskFrames, '$FCCommand', '$OutPath', '$Method', '$IgnoreFrames', $Covariance);,quit()"
	fi
	
	# check if GBC seed run is specified
	if [ ${Calculation} == "gbc" ]; then	
		# -- run GBC seed command: 
		# Call to get matlab help --> matlab -nosplash -nodisplay -nojvm -r "help fc_ComputeGBC3,quit()"
		# Full function input     --> fc_ComputeGBC3(flist, command, mask, verbose, target, targetf, rsmooth, rdilate, ignore, time, cv, vstep)
		# Example with string input --> matlab -nosplash -nodisplay -nojvm -r "fc_ComputeGBC3('listname:$CASE-$OutName|subject id:$CASE|file:$InputFile','$GBCCommand', $MaskFrames, $Verbose, $TargetROI, '$OutPath', $RadiusSmooth, $RadiusDilate, '$IgnoreFrames', $ComputeTime, $Covariance, $VoxelStep);,quit()"
		matlab -nosplash -nodisplay -nojvm -r "fc_ComputeGBC3('$FinalInput','$GBCCommand', $MaskFrames, $Verbose, $TargetROI, '$OutPath', $RadiusSmooth, $RadiusDilate, '$IgnoreFrames', $ComputeTime, $Covariance, $VoxelStep);,quit()"
	fi
	
	echo ""
	echo ""
	echo ""
	geho "--- Removing temporary list files: ${OutPath}/templist_${Calculation}_${OutName}"
	echo ""
	rm -rf ${OutPath}/templist_${Calculation}_${OutName} > /dev/null 2>&1

if [ "$ExtractData" == "yes" ]; then 
	geho "--- Saving out the data in a CSV file..."
	# -- Specify pconn file inputs and outputs
	PConnBOLDInputs=`ls ${OutPath}/${CASE}-${OutName}*ptseries.nii > /dev/null 2>&1`
	if [ -z ${PConnBOLDInputs} ]; then
        	echo ""
        	reho "WARNING: No parcellated files found for this run."
        	echo ""
	else
		for PConnBOLDInput in $PConnBOLDInputs; do 
			CSVPConnFileExt=".csv"
			CSVPConnBOLDOutput="${PConnBOLDInput}_${CSVPConnFileExt}"
			rm -f ${CSVPConnBOLDOutput} > /dev/null 2>&1
			wb_command -nifti-information -print-matrix "$PConnBOLDInput" >> "$CSVPConnBOLDOutput"
		done
	fi
fi
	
	geho "--- Connectivity calculation completed. Check outputs and logs for errors."
	echo ""
    geho "------------------------- End of work --------------------------------"
    echo ""

exit 1

}	

#
# Invoke the main function to get things started
#

main $@
