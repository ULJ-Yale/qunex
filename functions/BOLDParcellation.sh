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
#  Parcellation wrapper for dense BOLD data
#
# ## License
#
# * The BOLDParcellation.sh = the "Software"
# * This Software is distributed "AS IS" without warranty of any kind, either 
# * expressed or implied, including, but not limited to, the implied warranties
# * of merchantability and fitness for a particular purpose.
#
# ### TODO
#
# ## Description 
#   
# This script, BOLDParcellation.sh, implements parcellation on the DWI dense connectomes 
# using a whole-brain parcellation (e.g.Glasser parcellation with subcortical labels included)
# 
# ## Prerequisite Installed Software
#
# * Connectome Workbench (v1.0 or above)
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. $./BOLDParcellation.sh --help
#
# ### Expected Previous Processing
# 
# * The necessary input files are BOLD data from previous processing
# * These data are stored in: "$StudyFolder/subjects/$CASE/hcp/$CASE/MNINonLinear/Results/ 
#
#~ND~END~


usage() {
				
				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This function implements parcellation on the BOLD dense files using a whole-brain parcellation (e.g. Glasser parcellation with subcortical labels included)."
				echo ""
				echo ""
				echo "-- REQUIRED PARMETERS:"
				echo ""
 				echo "		--path=<study_folder>					Path to study data folder"
				echo "		--subject=<list_of_cases>				List of subjects to run"
				echo "		--inputfile=<file_to_compute_parcellation_on>		Specify the name of the file you want to use for parcellation (e.g. bold1_Atlas_MSMAll_hp2000_clean)"
				echo "		--inputpath=<path_for_input_file>			Specify path of the file you want to use for parcellation relative to the master study folder and subject directory (e.g. /images/functional/)"
				echo "		--inputdatatype=<type_of_dense_data_for_input_file>	Specify the type of data for the input file (e.g. dscalar or dtseries)"
				echo "		--parcellationfile=<file_for_parcellation>		Specify the absolute path of the file you want to use for parcellation (e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)"
				echo "		--outname=<name_of_output_pconn_file>			Specify the suffix output name of the pconn file"
				echo "		--outpath=<path_for_output_file>			Specify the output path name of the pconn file relative to the master study folder (e.g. /images/functional/)"
				echo ""
				echo "-- OPTIONAL PARMETERS:"
				echo "" 
 				echo "		--singleinputfile=<parcellate_single_file>				Parcellate only a single file in any location. Individual flags are not needed (--subject, --path, --inputfile)."
 				echo "		--overwrite=<clean_prior_run>						Delete prior run"
 				echo "		--computepconn=<specify_parcellated_connectivity_calculation>		Specify if a parcellated connectivity file should be computed (pconn). This is done using covariance and correlation (e.g. yes; default is set to no)."
 				echo "		--useweights=<clean_prior_run>						If computing a  parcellated connectivity file you can specify which frames to omit (e.g. yes' or no; default is set to no) "
 				echo "		--weightsfile=<location_and_name_of_weights_file>			Specify the location of the weights file relative to the master study folder (e.g. /images/functional/movement/bold1.use)"
				echo "		--extractdata=<save_out_the_data_as_as_csv>				Specify if you want to save out the matrix as a CSV file"
 				echo ""
 				echo "-- Example:"
				echo ""
				echo "BOLDParcellation.sh --path='/gpfs/project/fas/n3/Studies/Connectome/subjects' \ "
				echo "--subject='100206' \ "
				echo "--inputfile='bold1_Atlas_MSMAll_hp2000_clean' \ "
				echo "--inputpath='/images/functional/' \ "
				echo "--inputdatatype='dtseries' \ "
				echo "--parcellationfile='/gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii' \ "
				echo "--overwrite='no' \ "
				echo "--extractdata='yes' \ "
				echo "--outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
				echo "--outpath='/images/functional/'"
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
    # SingleInputFile # Input only a single file to parcellate
    # OutPath # e.g. /images/functional/
    # OutName # e.g. LR_Colelab_partitions_v1d_islands_withsubcortex
    # ParcellationFile  # e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii"
    # ComputePConn # Specify if a parcellated connectivity file should be computed (pconn). This is done using covariance and correlation (e.g. yes; default is set to no).
    # UseWeights  # If computing a  parcellated connectivity file you can specify which frames to omit (e.g. yes' or no; default is set to no) 
    # WeightsFile # Specify the location of the weights file relative to the master study folder (e.g. /images/functional/movement/bold1.use)
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
    unset SingleInputFile
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
            --singleinputfile=*)
                SingleInputFile=${argument/*=/""}
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
    
    if [ -z ${SingleInputFile} ]; then

    		if [ -z ${StudyFolder} ]; then
    		    usage
    		    reho "ERROR: <study-path> not specified"
    		    echo ""
    		    exit 1
    		fi
		
    		if [ -z ${CASE} ]; then
    		    usage
    		    reho "ERROR: <subject-id> not specified"
    		    echo ""
    		    exit 1
    		fi
		
    		if [ -z ${InputFile} ]; then
    		    usage
    		    reho "ERROR: <file_to_compute_parcellation_on> not specified"
    		    echo ""
    		    exit 1
    		fi
		
    		if [ -z ${InputPath} ]; then
    		    usage
    		    reho "ERROR: <path_for_input_file> not specified"
    		    echo ""
    		    exit 1
    		fi
    fi
    
    if [ -z ${InputDataType} ]; then
    	usage
    	reho "ERROR: <type_of_dense_data_for_input_file"
    	echo ""
    	exit 1
    fi
    
    if [ -z ${ParcellationFile} ]; then
        usage
        reho "ERROR: <file_for_parcellation> not specified"
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
    
    # report options
    echo ""
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo "   StudyFolder: ${StudyFolder}"
    echo "   Subject: ${CASE}"
    echo "   InputFile: ${InputFile}"
    echo "   SingleInputFile: ${SingleInputFile}"
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
echo "--- Establishing paths for all input and output folders:"
echo ""

# -- Define all inputs and outputs depending on data type input


if [ "$InputDataType" == "dtseries" ]; then 
	echo "      Working with dtseries files..."
	echo ""
	# -- Define extension 
	InputFileExt="dtseries.nii"
	OutFileExt="ptseries.nii"
	if [ -z "$SingleInputFile" ]; then
		# -- Define input
		BOLDInput="$StudyFolder/$CASE/$InputPath/${InputFile}.${InputFileExt}"
		# -- Define output
		BOLDOutput="$StudyFolder/$CASE/$OutPath/${InputFile}_${OutName}.${OutFileExt}"
	else
		# -- Define input
		BOLDInput="$InputPath/${SingleInputFile}.${InputFileExt}"
		# -- Define output
		BOLDOutput="$OutPath/${SingleInputFile}_${OutName}.${OutFileExt}"
	fi
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
	if [ -z "$SingleInputFile" ]; then
		# -- Define input
		BOLDInput="$StudyFolder/$CASE/$InputPath/${InputFile}.${InputFileExt}"
		# -- Define output
		BOLDOutput="$StudyFolder/$CASE/$OutPath/${InputFile}_${OutName}.${OutFileExt}"
	else
		# -- Define input
		BOLDInput="$InputPath/${SingleInputFile}.${InputFileExt}"
		# -- Define output
		BOLDOutput="$OutPath/${SingleInputFile}_${OutName}.${OutFileExt}"
	fi

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

echo "--- Checking if parcellation was completed..."
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
	geho "-- Computing parcellation on $BOLDInput..."
	echo ""
	
	# -- First parcellate by COLUMN and save a parcellated file
	wb_command -cifti-parcellate "$BOLDInput" "$ParcellationFile" COLUMN "$BOLDOutput"

	# -- Check if specified file was a *dtseries and compute a pconn file as well 
	if [ "$InputDataType" == "dtseries" ] && [ -z "$SingleInputFile" ]; then
	
		# Check if pconn calculation is requested
		if [ "$ComputePConn" == "yes" ]; then
		
		# -- Specify pconn file outputs for correlation (r) value and covariance 
		OutPConnFileExtR="r.pconn.nii"
		OutPConnFileExtCov="cov.pconn.nii"

		PConnBOLDOutputR="$StudyFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutPConnFileExtR}"
		PConnBOLDOutputCov="$StudyFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutPConnFileExtCov}"
		
		# - Check if weights file is specified
		geho "-- Using weights: $UseWeights"
		echo ""
		
		if [ "$UseWeights" == "yes" ]; then
		
			WeightsFile="${StudyFolder}/${CASE}/${WeightsFile}"
			
			geho "Using $WeightsFile to weight the calculations..."
			echo ""
			
			# -- Compute pconn using correlation
			geho "-- Computing pconn using correlation..."
			echo ""
			wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputR" -fisher-z -weights "$WeightsFile"
			
			# -- Compute pconn using covariance
			geho "-- Computing pconn using covariance..."
			echo ""
			wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputCov" -covariance -weights "$WeightsFile"
		fi
		
		if [ "$UseWeights" == "no" ]; then
		
			# -- Compute pconn using correlation
			geho "-- Computing pconn using correlation..."
			echo ""
			wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputR" -fisher-z
			
			# -- Compute pconn using covariance
			geho "-- Computing pconn using covariance..."
			echo ""
			wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputCov" -covariance
		fi
				
		fi
	fi
fi

if [ "$ExtractData" == "yes" ]; then 

		geho "--- Requested extraction of data in CSV format."
		echo ""
	
	if [ -z "$SingleInputFile" ] && [ "$InputDataType" == "dtseries" ] && [ "$ComputePConn" == "yes" ]; then
	
		geho "--- Saving out the parcellated dtseries data in a CSV file..."
		echo ""
	
		# -- Specify pconn file outputs for correlation (r) value and covariance 
	
		CSVOutPConnFileExtR="r.csv"
		CSVOutPConnFileExtCov="cov.csv"
	
		CSVPConnBOLDOutputR="$StudyFolder/$CASE/$OutPath/${InputFile}_${OutName}_${CSVOutPConnFileExtR}"
		CSVPConnBOLDOutputCov="$StudyFolder/$CASE/$OutPath/${InputFile}_${OutName}_${CSVOutPConnFileExtCov}"
		
		rm -f ${CSVPConnBOLDOutputR} > /dev/null 2>&1
		rm -f ${CSVPConnBOLDOutputCov} > /dev/null 2>&1
	
		wb_command -nifti-information -print-matrix "$PConnBOLDOutputR" >> "$CSVPConnBOLDOutputR"
		wb_command -nifti-information -print-matrix "$PConnBOLDOutputCov" >> "$CSVPConnBOLDOutputCov"
	
	fi
	
	if [ "$InputDataType" == "dscalar" ]; then

		geho "--- Saving out the parcellated dscalar data in a CSV file..."
		echo ""
	
		if [ -z "$SingleInputFile" ]; then
			DscalarFileExtCSV=".csv"
			CSVDPScalarBoldOut="$StudyFolder/$CASE/$OutPath/${InputFile}_${OutName}_${DscalarFileExtCSV}"
		else
			CSVDPScalarBoldOut="$OutPath/${SingleInputFile}_${OutName}_${DscalarFileExtCSV}"
		fi
		
		rm -f "$CSVDPScalarBoldOut" /dev/null 2>&1
		
		wb_command -nifti-information -print-matrix "$BOLDOutput" >> "$CSVDPScalarBoldOut"
	fi
	
	if [ -z "$SingleInputFile" ] && [ "$InputDataType" == "dtseries" ]; then
	
		geho "--- Saving out the parcellated single file dtseries data in a CSV file..."
		echo ""
		CSVDTseriesFileExtCSV=".csv"
		CSVDTseriesFileExtCSV="$StudyFolder/$CASE/$OutPath/${InputFile}_${OutName}_${CSVDTseriesFileExtCSV}"
		
		rm -f "$CSVDTseriesFileExtCSV" /dev/null 2>&1
		
		wb_command -nifti-information -print-matrix "$BOLDOutput" >> "$CSVDTseriesFileExtCSV"
	fi
	
fi	

# Perform completion checks"

	geho "--- Checking outputs..."
	echo ""
	if [ -f "$BOLDOutput" ]; then
		geho "Parcellated BOLD file:           $BOLDOutput"
		echo ""
	else
		reho "--- Parcellated BOLD file $BOLDOutput is missing. Something went wrong."
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
	
	geho "--- BOLD Parcellation completed. Check output log for outputs and errors."
	echo ""
    geho "------------------------- End of work --------------------------------"
    echo ""

exit 1

}	

#
# Invoke the main function to get things started
#

main $@
