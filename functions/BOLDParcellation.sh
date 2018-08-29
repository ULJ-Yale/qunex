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
#  BOLDParcellation.sh
#
# ## LICENSE
#
# * The BOLDParcellation.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ## TODO
#
# ## DESCRIPTION 
#   
# This script, BOLDParcellation.sh, implements parcellation on BOLD data
# using a whole-brain parcellation (e.g.Glasser parcellation with subcortical labels included)
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * Connectome Workbench (v1.0 or above)
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./BOLDParcellation.sh --help
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
     echo "This function implements parcellation on the BOLD dense files using a whole-brain parcellation (e.g. Glasser parcellation with subcortical labels included)."
     echo ""
     echo "-- REQUIRED PARMETERS:"
     echo ""
     echo "     --subjectsfolder=<folder_with_subjects>             Path to study folder that contains subjects"
     echo "     --subjects=<list_of_cases>                           List of subjects to run"
     echo "     --inputfile=<file_to_compute_parcellation_on>       Specify the name of the file you want to use for parcellation (e.g. bold1_Atlas_MSMAll_hp2000_clean)"
     echo "     --inputpath=<path_for_input_file>                   Specify path of the file you want to use for parcellation relative to the master study folder and subject directory (e.g. /images/functional/)"
     echo "     --inputdatatype=<type_of_dense_data_for_input_file> Specify the type of data for the input file (e.g. dscalar or dtseries)"
     echo "     --parcellationfile=<dlabel_file_for_parcellation>   Specify the absolute path of the file you want to use for parcellation (e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)"
     echo "     --outname=<name_of_output_pconn_file>               Specify the suffix output name of the pconn file"
     echo "     --outpath=<path_for_output_file>                    Specify the output path name of the pconn file relative to the master study folder (e.g. /images/functional/)"
     echo ""
     echo "-- OPTIONAL PARMETERS:"
     echo ""
     echo "     --singleinputfile=<parcellate_single_file>          Parcellate only a single file in any location. Individual flags are not needed (--subject, --subjectsfolder, --inputfile)."
     echo "     --overwrite=<clean_prior_run>                       Delete prior run"
     echo "     --computepconn=<specify_parcellated_connectivity_calculation>       Specify if a parcellated connectivity file should be computed (pconn). This is done using covariance and correlation (e.g. yes; default is set to no)."
     echo "     --useweights=<clean_prior_run>                      If computing a  parcellated connectivity file you can specify which frames to omit (e.g. yes' or no; default is set to no) "
     echo "     --weightsfile=<location_and_name_of_weights_file>   Specify the location of the weights file relative to the master study folder (e.g. /images/functional/movement/bold1.use)"
     echo "     --extractdata=<save_out_the_data_as_as_csv>         Specify if you want to save out the matrix as a CSV file"
     echo ""
     echo "-- EXAMPLES:"
     echo ""
     echo "   --> Run directly via ${TOOLS}/${MNAPREPO}/connector/functions/BOLDParcellation.sh --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
     echo ""
     reho "           * NOTE: --scheduler is not available via direct script call."
     echo ""
     echo "   --> Run via mnap BOLDParcellation --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
     echo ""
     geho "           * NOTE: scheduler is available via mnap call:"
     echo "                   --scheduler=<name_of_cluster_scheduler_and_options>  A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
     echo ""
     echo "           * For SLURM scheduler the string would look like this via the mnap call: "
     echo "                   --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
     echo ""
     echo ""
     echo "BOLDParcellation.sh --subjectsfolder='<folder_with_subjects>' \ "
     echo "--subject='<subj_id>' \ "
     echo "--inputfile='<name_of_input_file' \ "
     echo "--inputpath='<path_for_input_file>' \ "
     echo "--inputdatatype='<type_of_dense_data_for_input_file>' \ "
     echo "--parcellationfile='<dlabel_file_for_parcellation>' \ "
     echo "--overwrite='no' \ "
     echo "--extractdata='yes' \ "
     echo "--outname='<name_of_output_pconn_file>' \ "
     echo "--outpath='<path_for_output_file>'"
     echo ""
     exit 0
}


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

# ------------------------------------------------------------------------------
# -- Check if command line arguments are specified
# ------------------------------------------------------------------------------

########################################## INPUTS ########################################## 

# BOLD data should be pre-processed and in CIFTI format
# The data should be in the folder relative to the master study folder, specified by the inputfile
# Mandatory input parameters:
    # SubjectsFolder # e.g. /gpfs/project/fas/n3/Studies/Connectome
    # Subject      # e.g. 100206
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

# -- Outputs will be *pconn.nii files located in the location specified in the outputpath

# -- Get the command line options for this script
get_options() {

local scriptName=$(basename ${0})
local arguments=($@)

# -- Initialize global output variables
unset SubjectsFolder
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

# -- Set pconn variables to defaults before parsing inputs
ComputePConn="no"
UseWeights="no"
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
        --subjects=*)
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

# -- Check required parameters
if [ -z ${SingleInputFile} ]; then
        if [ -z ${SubjectsFolder} ]; then
            usage
            reho "ERROR: <subjects-folder-path> not specified>"
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
    reho "ERROR: <type_of_dense_data_for_input_file> not specified"
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
    WeightsFile="no"
    reho "Note: Weights file not used."
fi
if [ -z ${WeightsFile} ]; then
    UseWeights="no"
    WeightsFile="no"
    reho "Note: Weights file not used."
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

# -- Get Command Line Options
get_options $@

# -- Define inputs and output
echo "--- Establishing paths for all input and output folders:"
echo ""

# -- Define all inputs and outputs depending on data type input
if [ "$InputDataType" == "dtseries" ]; then
    echo "      Working with dtseries files..."
    echo ""
    # -- Define extension
    if [ `echo ${InputFile} | grep '.dtseries.nii'` ]; then 
        InputFile=`echo ${InputFile} | sed 's|.dtseries.nii||g'`
    fi
    InputFileExt="dtseries.nii"
    OutFileExt="ptseries.nii"
    if [ -z "$SingleInputFile" ]; then
        # -- Define input
        BOLDInput="$SubjectsFolder/$CASE/$InputPath/${InputFile}.${InputFileExt}"
        # -- Define output
        BOLDOutput="$SubjectsFolder/$CASE/$OutPath/${InputFile}_${OutName}.${OutFileExt}"
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
    if [ `echo ${InputFile} | grep '.dscalar.nii'` ]; then 
        InputFile=`echo ${InputFile} | sed 's|.dscalar.nii||g'`
    fi
    InputFileExt="dscalar.nii"
    OutFileExt="pscalar.nii"
    if [ -z "$SingleInputFile" ]; then
        # -- Define input
        BOLDInput="$SubjectsFolder/$CASE/$InputPath/${InputFile}.${InputFileExt}"
        # -- Define output
        BOLDOutput="$SubjectsFolder/$CASE/$OutPath/${InputFile}_${OutName}.${OutFileExt}"
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

# -- Check if parcellation was completed
echo "--- Checking if parcellation was completed..."
echo ""
if [ -f "$BOLDOutput" ]; then
    geho "Parcellation data found: "
    echo ""
    echo "      $BOLDOutput"
    echo ""
if [[ ${Overwrite} == "no" ]]; then 
    echo ""
    echo "Overwrite set to no. Exiting. Set --overwrite='yes' to re-run."
    exit 0
fi
else
    reho "Parcellation data not found."
    echo ""
fi

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
        OutPConnFileExtRfZ="r_Fz.pconn.nii"
        OutPConnFileExtCov="cov.pconn.nii"
        PConnBOLDOutputR="$SubjectsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutPConnFileExtR}"
        PConnBOLDOutputRfZ="$SubjectsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutPConnFileExtRfZ}"
        PConnBOLDOutputCov="$SubjectsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutPConnFileExtCov}"
        OutGBCFileExtR="r_GBC.pscalar.nii"
        OutGBCFileExtRfZ="r_Fz_GBC.pscalar.nii"
        OutGBCFileExtCov="cov_GBC.pscalar.nii"
        GBCBOLDOutputR="$SubjectsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutGBCFileExtR}"
        GBCBOLDOutputRfZ="$SubjectsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutGBCFileExtRfZ}"
        GBCBOLDOutputCov="$SubjectsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutGBCFileExtCov}"
        # -- Check if weights file is specified
        geho "-- Using weights: $UseWeights"
        echo ""
        if [ "$UseWeights" == "yes" ]; then
            WeightsFile="${SubjectsFolder}/${CASE}/${WeightsFile}"
            geho "Using $WeightsFile to weight the calculations..."
            echo ""
            # -- Compute pconn using correlation
            geho "-- Computing pconn using correlation with weights file..."
            echo ""
            wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputR" -weights "$WeightsFile"
            # -- Compute GBC using correlation
            geho "-- Computing GBC using correlation with weights file..."
            echo ""
            wb_command -cifti-reduce ${PConnBOLDOutputR} MEAN ${GBCBOLDOutputR}
            # -- Compute pconn using covariance
            geho "-- Computing pconn using covariance with weights file..."
            echo ""
            wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputCov" -covariance -weights "$WeightsFile"
            # -- Compute GBC using covariance
            geho "-- Computing GBC using covariance with weights file..."
            echo ""
            wb_command -cifti-reduce ${PConnBOLDOutputCov} MEAN ${GBCBOLDOutputCov}
            # -- Compute pconn using fisher-z correlation
            geho "-- Computing pconn using correlation w/ fisher-z transform with weights file..."
            echo ""
            wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputRfZ" -fisher-z -weights "$WeightsFile"
            # -- Compute GC using fisher-z correlation
            geho "-- Computing GBC using correlation w/ fisher-z transform with weights file..."
            echo ""
            wb_command -cifti-reduce ${PConnBOLDOutputRfZ} MEAN ${GBCBOLDOutputRfZ}
        fi
        if [ "$UseWeights" == "no" ]; then
            # -- Compute pconn using correlation
            geho "-- Computing pconn using correlation..."
            echo ""
            wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputR"
            # -- Compute GBC using correlation
            geho "-- Computing GBC using correlation..."
            echo ""
            wb_command -cifti-reduce ${PConnBOLDOutputR} MEAN ${GBCBOLDOutputR}
            # -- Compute pconn using covariance
            geho "-- Computing pconn using covariance..."
            echo ""
            wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputCov" -covariance
            # -- Compute GBC using covariance
            geho "-- Computing GBC using covariance..."
            echo ""
            wb_command -cifti-reduce ${PConnBOLDOutputCov} MEAN ${GBCBOLDOutputCov}
            # -- Compute pconn using fisher-z correlation
            geho "-- Computing pconn using correlation w/ fisher-z transform..."
            echo ""
            wb_command -cifti-correlation "$BOLDOutput" "$PConnBOLDOutputRfZ" -fisher-z
            # -- Compute GBC using fisher-z correlation
            geho "-- Computing GBC using correlation w/ fisher-z transform..."
            echo ""
            wb_command -cifti-reduce ${PConnBOLDOutputRfZ} MEAN ${GBCBOLDOutputRfZ}
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
        CSVPConnBOLDOutputR="$SubjectsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${CSVOutPConnFileExtR}"
        CSVPConnBOLDOutputCov="$SubjectsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${CSVOutPConnFileExtCov}"
        rm -f ${CSVPConnBOLDOutputR} 2> /dev/null
        rm -f ${CSVPConnBOLDOutputCov} 2> /dev/null
        wb_command -nifti-information -print-matrix "$PConnBOLDOutputR" >> "$CSVPConnBOLDOutputR"
        wb_command -nifti-information -print-matrix "$PConnBOLDOutputCov" >> "$CSVPConnBOLDOutputCov"
    fi
    if [ "$InputDataType" == "dscalar" ]; then
        geho "--- Saving out the parcellated dscalar data in a CSV file..."
        echo ""
        if [ -z "$SingleInputFile" ]; then
            DscalarFileExtCSV=".csv"
            CSVDPScalarBoldOut="$SubjectsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${DscalarFileExtCSV}"
        else
            CSVDPScalarBoldOut="$OutPath/${SingleInputFile}_${OutName}_${DscalarFileExtCSV}"
        fi
        rm -f "$CSVDPScalarBoldOut" 2> /dev/null
        wb_command -nifti-information -print-matrix "$BOLDOutput" >> "$CSVDPScalarBoldOut"
    fi
    if [ -z "$SingleInputFile" ] && [ "$InputDataType" == "dtseries" ]; then
        geho "--- Saving out the parcellated single file dtseries data in a CSV file..."
        echo ""
        CSVDTseriesFileExtCSV=".csv"
        CSVDTseriesFileExtCSV="$SubjectsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${CSVDTseriesFileExtCSV}"
        rm -f "$CSVDTseriesFileExtCSV" 2> /dev/null
        wb_command -nifti-information -print-matrix "$BOLDOutput" >> "$CSVDTseriesFileExtCSV"
    fi
fi

# -- Perform completion checks
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
    if [ -f "$PConnBOLDOutputRfZ" ]; then
        geho "Parcellated connectivity (pconn) BOLD file using correlation w/ fisher-z transform:           $PConnBOLDOutputRfZ"
        echo ""
    else
        reho "Parcellated connectivity (pconn) BOLD file using correlation w/ fisher-z transform $PConnBOLDOutputRfZ is missing. Something went wrong."
        echo ""
        exit 1
    fi
fi

geho "--- BOLD Parcellation completed. Check output log for outputs and errors."
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@

