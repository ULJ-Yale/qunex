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
# * These may be stored in: "$StudyFolder/subjects/$CASE/hcp/$CASE/MNINonLinear/Results/ 
#
#~ND~END~

usage() {

# function [] = fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf, method, ignore, cv)
# INPUT
# flist   	- A .list file of subject information.
# roinfo	    - An ROI file.
# inmask		- An array mask defining which frames to use (1) and which not (0) [0]
# options		- A string defining which subject files to save ['']:
# r		- save map of correlations
# f     - save map of Fisher z values
# cv	- save map of covariances
# z		- save map of Z scores
# tagetf	- The folder to save images in ['.'].
# method    - Method for extracting timeseries - 'mean' or 'pca' ['mean'].
# ignore    - Do we omit frames to be ignored ['no']
#                 -> no:    do not ignore any additional frames
#                 -> event: ignore frames as marked in .fidl file
#                 -> other: the column in *_scrub.txt file that matches bold file to be used for ignore mask
# cv        - Whether covariances should be computed instead of correlations.
  
# function [] =             fc_ComputeGBC3(flist, command, mask, verbose, target, targetf, rsmooth, rdilate, ignore, time, cv, vstep) 
# INPUT 
# flist       - conc-like style list of subject image files or conc files:
#                 subject id:<subject_id>
#                 roi:<path to the individual's ROI file>
#                 file:<path to bold files - one per line>
#              or a well strucutured string (see g_ReadFileList).
# command     - the type of gbc to run: mFz, aFz, pFz, nFz, aD, pD, nD,
#              mFzp, aFzp, ...
#              <type of gbc>:<parameter>|<type of gbc>:<parameter> ...
# mask        - An array mask defining which frames to use (1) and
#              which not (0). All if empty.
# verbose     - Report what is going on. [false]
# target      - Array of ROI codes that define target ROI [default:
#              FreeSurfer cortex codes]
# targetf     - Target folder for results.
# rsmooth     - Radius for smoothing (no smoothing if empty). []
# rdilate     - Radius for dilating mask (no dilation if empty). []
# ignore      - The column in *_scrub.txt file that matches bold file to
#              be used for ignore mask. All if empty. []
# time        - Whether to print timing information. [false]
# cv          - Whether to compute covariances instead of correlations.
#              [false]
# vstep       - How many voxels to process in a single step. [1200]

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
 				echo "		--path=<study_folder>					Path to study data folder"
				echo "		--calculation=<type_of_calculation>					Run seed FC or GBC calculation <gbc> or <seed>"
				echo "		--runtype=<type_of_run>					Run calculation on a group (requires a list) or on individual subjects (requires individual specification) (group or individual)"
				echo "		--flist=<subject_list_file>				Specify *.list file of subject information. If specified then --inputfile, --subject --inputpath --inputdatatype and --outname are omitted"
				echo "		--tagetf=<path_for_output_file>			Specify the absolute path for output folder"
				echo "		--ignore=<frames_to_ignore>				The column in *_scrub.txt file that matches bold file to be used for ignore mask. All if empty. Default is [] "
				echo "		--mask=<which_frames_to_use>				An array mask defining which frames to use (1) and which not (0). All if empty. If single value is specified then this number of frames is skipped." # inmask for fc_ComputeSeedMapsMultiple
				echo ""
				echo "-- REQUIRED GENERAL PARMETERS FOR AN INDIVIDUAL SUBJECT RUN:"
				echo ""
				echo "		--subject=<list_of_cases>				List of subjects to run"
				echo "		--inputfile=<file_to_compute_parcellation_on>		Specify the absolute path of the file you want to use for parcellation (e.g. bold1_Atlas_MSMAll_hp2000_clean)"
				echo "		--inputdatatype=<type_of_dense_data_for_input_file>	Specify the type of data for the input file (e.g. ptseries or dtseries)"
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
				echo "		--verbose=<print_output_verbosely>			Report what is going on. Default is [false]"
				echo "		--time=<print_time_needed>				Whether to print timing information. [false]"
				echo "		--vstep=<how_many_voxels>				How many voxels to process in a single step. Default is [1200]"
				echo ""
				echo "-- REQUIRED SEED FC PARMETERS:"
				echo ""
 				echo "		--roinfo=<roi_seed_files>				An ROI file for the seed connectivity "
 				echo "		--options=<calculations_to_save>			A string defining which subject files to save [''] "
 				echo ""
 				echo "			> r ... save map of correlations "
  				echo "			> f ... save map of Fisher z values "
 				echo "			> cv ... save map of covariances "
  				echo "			> z ... save map of Z scores "
				echo ""
				echo "-- OPTIONAL SEED FC PARMETERS: "
			 	echo ""
 				echo "		--method=<calculation_to_get_timeseries>		Method for extracting timeseries - 'mean' or 'pca' Default is ['mean'] "
 				echo ""
 				echo "-- Examples:"
				echo ""
				echo "ComputeFunctionalConnectivity.sh --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--calculation='seed' \ "
				echo "--runtype='individual' \ "
				echo "--subject='100206' \ "
				echo "--inputfile='/gpfs/project/fas/n3/Studies/Connectome/subjects/100206/images/functional/bold1_Atlas_MSMAll.dtseries.nii' \ "
				echo "--inputpath='/images/functional/' \ "
				echo "--inputdatatype='dtseries' \ "
				echo "--overwrite='no' \ "
				echo "--extractdata='yes' \ "
				echo "--outname='Thal.FSL.MNI152.CIFTI.Atlas.SomatomotorSensory' \ "
				echo "--ignore='udvarsme' \ "
				echo "--roinfo='/gpfs/project/fas/n3/Studies/BSNIP/fcMRI/roi/Thal.FSL.MNI152.CIFTI.Atlas.SomatomotorSensory.names' \ "
				echo "--options='' \ "
				echo "--method='' \ "
				echo "--outpath='/gpfs/project/fas/n3/Studies/Connectome/fcMRI/results_udvarsme_surface_testing' \ "
				echo "--mask='5' "
				echo ""	
				echo "ComputeFunctionalConnectivity.sh --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--calculation='seed' \ "
				echo "--runtype='group' \ "
				echo "--subject='100206' \ "
				echo "--flist='/gpfs/project/fas/n3/Studies/Connectome/subjects/lists/subjects.list' \ "
				echo "--inputdatatype='dtseries' \ "
				echo "--overwrite='no' \ "
				echo "--extractdata='yes' \ "
				echo "--outname='Thal.FSL.MNI152.CIFTI.Atlas.SomatomotorSensory' \ "
				echo "--ignore='udvarsme' \ "
				echo "--roinfo='/gpfs/project/fas/n3/Studies/BSNIP/fcMRI/roi/Thal.FSL.MNI152.CIFTI.Atlas.SomatomotorSensory.names' \ "
				echo "--options='' \ "
				echo "--method='' \ "
				echo "--outpath='/gpfs/project/fas/n3/Studies/Connectome/fcMRI/results_udvarsme_surface_testing' \ "
				echo "--mask='5' "
				echo ""
				echo "ComputeFunctionalConnectivity.sh --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--calculation='gbc' \ "
				echo "--runtype='individual' \ "
				echo "--subject='100206' \ "
				echo "--inputfile='/gpfs/project/fas/n3/Studies/Connectome/subjects/100206/images/functional/bold1_Atlas_MSMAll.dtseries.nii' \ "
				echo "--inputpath='/images/functional/' \ "
				echo "--inputdatatype='dtseries' \ "
				echo "--overwrite='no' \ "
				echo "--extractdata='yes' \ "
				echo "--outname='GBC' \ "
				echo "--ignore='udvarsme' \ "
#				echo "--roinfo='/gpfs/project/fas/n3/Studies/BSNIP/fcMRI/roi/Thal.FSL.MNI152.CIFTI.Atlas.SomatomotorSensory.names' \ "
				echo "--command='' \ "
#				echo "--method='' \ "
				echo "--outpath='/gpfs/project/fas/n3/Studies/Connectome/fcMRI/results_udvarsme_surface_testing' \ "
				echo "--mask='5' "
				echo "--target='' "
				echo "--rsmooth='' "
				echo "--rdilate='' "
				echo ""	
				echo "ComputeFunctionalConnectivity.sh --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--calculation='gbc' \ "
				echo "--runtype='group' \ "
				echo "--subject='100206' \ "
				echo "--flist='/gpfs/project/fas/n3/Studies/Connectome/subjects/lists/subjects.list' \ "
				echo "--inputdatatype='dtseries' \ "
				echo "--overwrite='no' \ "
				echo "--extractdata='yes' \ "
				echo "--outname='GBC' \ "
				echo "--ignore='udvarsme' \ "
#				echo "--roinfo='/gpfs/project/fas/n3/Studies/BSNIP/fcMRI/roi/Thal.FSL.MNI152.CIFTI.Atlas.SomatomotorSensory.names' \ "
				echo "--command='' \ "
#				echo "--method='' \ "
				echo "--outpath='/gpfs/project/fas/n3/Studies/Connectome/fcMRI/results_udvarsme_surface_testing' \ "
				echo "--mask='5' "
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
    # ExtractData # yes/no

########################################## OUTPUTS #########################################

# Outputs will be *pconn.nii files located in the location specified in the outputpath

#  Get the command line options for this script
#

get_options() {
    local scriptName=$(basename ${0})
    local arguments=($@)
    
    # initialize global output variables
    unset StudyFolder
    unset Subject
    unset InputFile
    unset InputPath
    unset InputDataType
    unset ParcellationFile
    unset OutName
    unset OutPath
    unset Overwrite
    unset ComputePConn
    unset UseWeights
    unset WeightsFile
    unset ExtractData

	# set pconn variables to defaults before parsing inputs
    ComputePConn="no"
    UseWeights="no"
    
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
            --parcellationfile=*)
                ParcellationFile=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --outname=*)
                OutName=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --outpath=*)
                OutPath=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --overwrite=*)
                Overwrite=${argument/*=/""}
                index=$(( index + 1 ))
                ;;      
            --computepconn=*)
                ComputePConn=${argument/*=/""}
                index=$(( index + 1 ))
                ;; 
            --useweights=*)
                UseWeights=${argument/*=/""}
                index=$(( index + 1 ))
                ;; 
            --weightsfile=*)
                WeightsFile=${argument/*=/""}
                index=$(( index + 1 ))
                ;; 
            --extractdata=*)
                ExtractData=${argument/*=/""}
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
        reho "ERROR: <study-path> not specified>"
        echo ""
        exit 1
    fi

    if [ -z ${CASE} ]; then
        usage
        reho "ERROR: <subject-id> not specified>"
        echo ""
        exit 1
    fi

    if [ -z ${InputFile} ]; then
        usage
        reho "ERROR: <file_to_compute_parcellation_on> not specified>"
        echo ""
        exit 1
    fi

    if [ -z ${InputPath} ]; then
        usage
        reho "ERROR: <path_for_input_file> not specified>"
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
    
    if [ -z ${OutPath} ]; then
        usage
        reho "ERROR: <path_for_output_file> not specified>"
        exit 1
    fi
    
    if [ -z ${UseWeights} ]; then
        UseWeights="no"
        exit 1
    fi
    
    # report options
    echo ""
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo "   StudyFolder: ${StudyFolder}"
    echo "   Subject: ${CASE}"
    echo "   InputFile: ${InputFile}"
    echo "   InputPath: ${InputPath}"
    echo "   ParcellationFile: ${ParcellationFile}"
    echo "   OutName: ${OutName}"
    echo "   OutPath: ${OutPath}"
    echo "   InputDataType: ${InputDataType}"
    echo "   Overwrite: ${Overwrite}"
    echo "   ComputePConn: ${ComputePConn}"
    echo "   UseWeights: ${UseWeights}"
    echo "   WeightsFile: ${WeightsFile}"
    echo "   ExtractData: ${ExtractData}"
    echo "-- ${scriptName}: Specified Command-Line Options - End --"
    echo ""
    geho "------------------------- Start of work --------------------------------"
    echo ""
}

######################################### DO WORK ##########################################

main() {

    # Get Command Line Options
    get_options $@

# -- Define inputs and output
reho "--- Establishing paths for all input and output folders:"
echo ""

# -- Define all inputs and outputs depending on data type input

if [ "$InputDataType" == "dtseries" ]; then 
	echo "       Working with dtseries files..."
	echo ""
	# -- Define extension 
	InputFileExt="dtseries.nii"
	OutFileExt="ptseries.nii"
	# -- Define input
	BOLDInput="$StudyFolder/$CASE/$InputPath/${InputFile}.${InputFileExt}"
	# -- Define output
	BOLDOutput="$StudyFolder/$CASE/$OutPath/${CASE}_${InputFile}_${OutName}.${OutFileExt}"

	echo "      Dense BOLD Input:              ${BOLDInput}"
	echo ""
	echo "      Parcellated BOLD Output:       ${BOLDOutput}"
	echo ""
fi

if [ "$InputDataType" == "dscalar" ]; then 
	echo "       Working with dscalar files..."
	echo ""
	# -- Define extension 
	InputFileExt="dscalar.nii"
	OutFileExt="pscalar.nii"
	# -- Define input
	BOLDInput="$StudyFolder/$CASE/$InputPath/${InputFile}.${InputFileExt}"
	# -- Define output
	BOLDOutput="$StudyFolder/$CASE/$OutPath/${CASE}_${InputFile}_${OutName}.${OutFileExt}"

	echo "      Dense BOLD Input:              ${BOLDInput}"
	echo ""
	echo "      Parcellated BOLD Output:       ${BOLDOutput}"
	echo ""
fi


# -- Delete any existing output sub-directories
if [ "$Overwrite" == "yes" ]; then
	reho "--- Deleting prior $BOLDOutput..."
	echo ""
	rm -f "$BOLDOutput" > /dev/null 2>&1
fi

# Check if parcellation was completed

reho "--- Checking if parcellation was completed..."
echo ""

if [ -f "$BOLDOutput" ]; then
	geho "Parcellation data found: "
	echo ""
	echo "      $BOLDOutput"
	echo ""
	exit 1
else
	reho "Parcellation data not found."
	echo ""
	geho "Computing parcellation on $BOLDInput..."
	echo ""
	
	# -- First parcellate by COLUMN and save a parcellated file
	wb_command -cifti-parcellate "$BOLDInput" "$ParcellationFile" COLUMN "$BOLDOutput"

	# -- Check if specified file was a *dtseries and compute a pconn file as well 
	if [ "$InputDataType" == "dtseries" ]; then
	
		# Check if pconn calculation is requested
		if [ "$ComputePConn" == "yes" ]; then
		
		# -- Specify pconn file outputs for correlation (r) value and covariance 
		OutPConnFileExtR="r.pconn.nii"
		PConnBOLDOutputR="$StudyFolder/$CASE/$OutPath/${CASE}_${InputFile}_${OutName}_${OutPConnFileExtR}"
		OutPConnFileExtCov="cov.pconn.nii"
		PConnBOLDOutputCov="$StudyFolder/$CASE/$OutPath/${CASE}_${InputFile}_${OutName}_${OutPConnFileExtCov}"
		
		# - Check if weights file is specified
		geho "Using weights: $UseWeights"
		echo ""
		
		if [ "$UseWeights" == "yes" ]; then
		
			WeightsFile="${StudyFolder}/${CASE}/${WeightsFile}"
			
			geho "Using $WeightsFile to weight the calculations..."
			echo ""
			
			# -- Compute pconn using correlation
			geho "Computing pconn using correlation..."
			echo ""
			wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputR" -fisher-z -weights "$WeightsFile"
			
			# -- Compute pconn using covariance
			geho "Computing pconn using covariance..."
			echo ""
			wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputCov" -covariance -weights "$WeightsFile"
		fi
		
		if [ "$UseWeights" == "no" ]; then
		
			# -- Compute pconn using correlation
			geho "Computing pconn using correlation..."
			echo ""
			wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputR" -fisher-z
			
			# -- Compute pconn using covariance
			geho "Computing pconn using covariance..."
			echo ""
			wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputCov" -covariance
		fi
				
		fi
	fi
fi

if [ "$ExtractData" == "yes" ]; then 
	geho "Saving out the data in a CSV file..."
	echo ""
	# -- Specify pconn file outputs for correlation (r) value and covariance 
	CSVOutPConnFileExtR="r.csv"
	CSVPConnBOLDOutputR="$StudyFolder/$CASE/$OutPath/${CASE}_${InputFile}_${OutName}_${CSVOutPConnFileExtR}"
	CSVOutPConnFileExtCov="cov.csv"
	CSVPConnBOLDOutputCov="$StudyFolder/$CASE/$OutPath/${CASE}_${InputFile}_${OutName}_${CSVOutPConnFileExtCov}"
	
	rm -f ${CSVPConnBOLDOutputR} > /dev/null 2>&1
	rm -f ${CSVPConnBOLDOutputCov} > /dev/null 2>&1

	wb_command -nifti-information -print-matrix "$PConnBOLDOutputR" >> "$CSVPConnBOLDOutputR"
	wb_command -nifti-information -print-matrix "$PConnBOLDOutputCov" >> "$CSVPConnBOLDOutputCov"

fi	

# Perform completion checks"

	reho "--- Checking outputs..."
	echo ""
	if [ -f "$BOLDOutput" ]; then
		geho "Parcellated BOLD file:           $BOLDOutput"
		echo ""
	else
		reho "Parcellated BOLD file $BOLDOutput is missing. Something went wrong."
		echo ""
		exit 1
	fi
	
	if [ "$ComputePConn" == "yes" ]; then
	
	if [ -f "$PConnBOLDOutputR" ]; then
		geho "Parcellated connectivity (pconn) BOLD file using correlation:           $PConnBOLDOutputR"
		echo ""
	else
		reho "Parcellated connectivity (pconn) BOLD file using correlation $PConnBOLDOutputR is missing. Something went wrong."
		echo ""
		exit 1
	fi
	
	if [ -f "$PConnBOLDOutputCov" ]; then
		geho "Parcellated connectivity (pconn) BOLD file using covariance:           $PConnBOLDOutputCov"
		echo ""
	else
		reho "Parcellated connectivity (pconn) BOLD file using covariance $PConnBOLDOutputCov is missing. Something went wrong."
		echo ""
		exit 1
	fi
	
	fi
	
	reho "--- BOLD Parcellation successfully completed"
	echo ""
    geho "------------------------- End of work --------------------------------"
    echo ""

exit 1

}	

#
# Invoke the main function to get things started
#

main $@
