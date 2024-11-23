#!/bin/bash

# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
cat << EOF
``parcellate_bold``

This function implements parcellation on the BOLD dense files using a
whole-brain parcellation (e.g. Glasser parcellation with subcortical labels
included).

Parameters:
    --sessionsfolder (str):
        Path to study folder that contains sessions.

    --sessions (str):
        Comma separated list of sessions to run.

    --inputfile (str):
        Specify the name of the file you want to use for parcellation (e.g.
        'bold1_Atlas_MSMAll_hp2000_clean').

    --inputpath (str):
        Specify path of the file you want to use for parcellation relative to
        the master study folder and session directory (e.g.
        '/images/functional/').

    --inputdatatype (str):
        Specify the type of data for the input file (e.g. 'dscalar' or
        'dtseries').

    --parcellationfile (str):
       Specify the absolute path of the file you want to use for parcellation
       (e.g. '/gpfs/project/fas/n3/Studies/Connectome/Parcellations/glasser_parcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii').

    --singleinputfile (str):
       Parcellate only a single file in any location. Individual flags are not
       needed (--session, --sessionsfolder, --inputfile).

    --overwrite (str, default 'no'):
        Whether to overwrite existing data (yes) or not (no). Note that
        previous data is deleted before the run, so in the case of a failed
        command run, previous results are lost.

    --computepconn (str, default 'no'):
        Specify if a parcellated connectivity file should be computed (pconn).
        This is done using covariance and correlation ('yes' / 'no').

    --outname (str):
        Specify the suffix output name of the pconn file.

    --outpath (str):
        Specify the output path name of the pconn file relative to the master
        study folder (e.g. '/images/functional/').

    --useweights (str, default 'no'):
        If computing a parcellated connectivity file you can specify which
        frames to omit (e.g. 'yes' or 'no').

    --weightsfile (str):
        Specify the location of the weights file relative to the master study
        folder (e.g. '/images/functional/movement/bold1.use').

    --extractdata (str):
        Specify if you want to save out the matrix as a CSV file.

Examples:
    Run directly via::

        ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/parcellate_bold.sh \\
            --<parameter1> \\
            --<parameter2> \\
            --<parameter3> ... \\
            --<parameterN>

    NOTE: --scheduler is not available via direct script call.

    Run via::

        qunex parcellate_bold \\
            --<parameter1> \\
            --<parameter2> ... \\
            --<parameterN>

    NOTE: scheduler is available via qunex call.

    --scheduler
        A string for the cluster scheduler (e.g. PBS or SLURM) followed by
        relevant options.

    For SLURM scheduler the string would look like this via the qunex call::

        --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

    ::

        qunex parcellate_bold \\
            --sessionsfolder='<folder_with_sessions>' \\
            --session='<session_id>' \\
            --inputfile='<name_of_input_file' \\
            --inputpath='<path_for_input_file>' \\
            --inputdatatype='<type_of_dense_data_for_input_file>' \\
            --parcellationfile='<dlabel_file_for_parcellation>' \\
            --overwrite='no' \\
            --extractdata='yes' \\
            --outname='<name_of_output_pconn_file>' \\
            --outpath='<path_for_output_file>'

EOF
exit 0
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
    # SessionsFolder # e.g. /gpfs/project/fas/n3/Studies/Connectome
    # Session      # e.g. 100206
    # InputFile # e.g. bold1_Atlas_MSMAll_hp2000_clean.dtseries.nii
    # InputPath # e.g. /images/functional/
    # InputDataType # e.g.dtseries
    # SingleInputFile # Input only a single file to parcellate
    # OutPath # e.g. /images/functional/
    # OutName # e.g. LR_Colelab_partitions_v1d_islands_withsubcortex
    # ParcellationFile  # e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/glasser_parcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii"
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
unset SessionsFolder
unset Session
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
        --sessionsfolder=*)
            SessionsFolder=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --sessions=*)
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
            echo "ERROR: Unrecognized Option: ${argument}"
            echo ""
            exit 1
            ;;
    esac
done

# -- Check required parameters
if [ -z ${SingleInputFile} ]; then
        if [ -z ${SessionsFolder} ]; then
            usage
            echo "ERROR: <sessions-folder-path> not specified>"
            echo ""
            exit 1
        fi
        if [ -z ${CASE} ]; then
            usage
            echo "ERROR: <session-id> not specified"
            echo ""
            exit 1
        fi
        if [ -z ${InputFile} ]; then
            usage
            echo "ERROR: <file_to_compute_parcellation_on> not specified"
            echo ""
            exit 1
        fi
        if [ -z ${InputPath} ]; then
            usage
            echo "ERROR: <path_for_input_file> not specified"
            echo ""
            exit 1
        fi
fi
if [ -z ${InputDataType} ]; then
    usage
    echo "ERROR: <type_of_dense_data_for_input_file> not specified"
    echo ""
    exit 1
fi
if [ -z ${ParcellationFile} ]; then
    usage
    echo "ERROR: <file_for_parcellation> not specified"
    echo ""
    exit 1
fi
if [ -z ${OutName} ]; then
    usage
    echo "ERROR: <name_of_output_pconn_file> not specified"
    exit 1
fi

if [ -z ${OutPath} ]; then
    usage
    echo "ERROR: <path_for_output_file> not specified"
    exit 1
fi
if [ -z ${UseWeights} ]; then
    UseWeights="no"
    WeightsFile="no"
    echo "Note: Weights file not used."
fi
if [ -z ${WeightsFile} ]; then
    UseWeights="no"
    WeightsFile="no"
    echo "Note: Weights file not used."
fi

# -- Set StudyFolder
cd $SessionsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null

# -- Report options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   SessionsFolder: ${SessionsFolder}"
echo "   Session: ${CASE}"
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
echo "------------------------- Start of work --------------------------------"
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
        BOLDInput="$SessionsFolder/$CASE/$InputPath/${InputFile}.${InputFileExt}"
        # -- Define output
        BOLDOutput="$SessionsFolder/$CASE/$OutPath/${InputFile}_${OutName}.${OutFileExt}"
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
        BOLDInput="$SessionsFolder/$CASE/$InputPath/${InputFile}.${InputFileExt}"
        # -- Define output
        BOLDOutput="$SessionsFolder/$CASE/$OutPath/${InputFile}_${OutName}.${OutFileExt}"
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
    echo "-- Deleting prior $BOLDOutput..."
    echo ""
    rm -f "$BOLDOutput" > /dev/null 2>&1
fi

# -- Check if parcellation was completed
echo "-- Checking if parcellation was completed..."
echo ""
if [ -f "$BOLDOutput" ]; then
    echo "Parcellation data found: "
    echo ""
    echo "      $BOLDOutput"
    echo ""
if [[ ${Overwrite} == "no" ]]; then 
    echo ""
    echo " ---> Overwrite set to no. If you wish to overwrite, set --overwrite='yes' and re-run."
    echo ""
    echo ""
    echo "--- BOLD Parcellation completed. Check output log for outputs and possible issues."
    echo ""
    echo "------------------------- Successful completion of work --------------------------------"
    echo ""
    exit 0
fi
else
    if [ "$Overwrite" == "yes" ]; then
        echo "-- Note: Prior parcellation data not found because you requested to overwrite."
        echo ""
    else
        echo "-- Note: Prior parcellation data not found."
        echo ""
    fi
fi

echo "-- Computing parcellation on $BOLDInput..."
echo ""
# -- First parcellate by COLUMN and save a parcellated file
wb_command -cifti-parcellate ${BOLDInput} ${ParcellationFile} COLUMN ${BOLDOutput} -only-numeric
# -- Check if specified file was a *dtseries and compute a pconn file as well 
if [ "$InputDataType" == "dtseries" ] && [ -z "$SingleInputFile" ]; then
    # Check if pconn calculation is requested
    if [ "$ComputePConn" == "yes" ]; then
        # -- Specify pconn file outputs for correlation (r) value and covariance 
        OutPConnFileExtR="r.pconn.nii"
        OutPConnFileExtRfZ="r_Fz.pconn.nii"
        OutPConnFileExtCov="cov.pconn.nii"
        PConnBOLDOutputR="$SessionsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutPConnFileExtR}"
        PConnBOLDOutputRfZ="$SessionsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutPConnFileExtRfZ}"
        PConnBOLDOutputCov="$SessionsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutPConnFileExtCov}"
        OutGBCFileExtR="r_GBC.pscalar.nii"
        OutGBCFileExtRfZ="r_Fz_GBC.pscalar.nii"
        OutGBCFileExtCov="cov_GBC.pscalar.nii"
        GBCBOLDOutputR="$SessionsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutGBCFileExtR}"
        GBCBOLDOutputRfZ="$SessionsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutGBCFileExtRfZ}"
        GBCBOLDOutputCov="$SessionsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${OutGBCFileExtCov}"
        # -- Check if weights file is specified
        echo "-- Using weights: $UseWeights"
        echo ""
        if [ "$UseWeights" == "yes" ]; then
            WeightsFile="${SessionsFolder}/${CASE}/${WeightsFile}"
            echo "Using $WeightsFile to weight the calculations..."
            echo ""
            # -- Compute pconn using correlation
            echo "-- Computing pconn using correlation with weights file..."
            echo ""
            wb_command -cifti-correlation ${BOLDOutput} ${PConnBOLDOutputR} -weights ${WeightsFile}
            # -- Compute GBC using correlation
            echo "-- Computing GBC using correlation with weights file..."
            echo ""
            wb_command -cifti-reduce ${PConnBOLDOutputR} MEAN ${GBCBOLDOutputR} -only-numeric
            # -- Compute pconn using covariance
            echo "-- Computing pconn using covariance with weights file..."
            echo ""
            wb_command -cifti-correlation ${BOLDOutput} ${PConnBOLDOutputCov} -covariance -weights ${WeightsFile}
            # -- Compute GBC using covariance
            echo "-- Computing GBC using covariance with weights file..."
            echo ""
            wb_command -cifti-reduce ${PConnBOLDOutputCov} MEAN ${GBCBOLDOutputCov} -only-numeric
            # -- Compute pconn using fisher-z correlation
            echo "-- Computing pconn using correlation w/ fisher-z transform with weights file..."
            echo ""
            wb_command -cifti-correlation ${BOLDOutput} ${PConnBOLDOutputRfZ} -fisher-z -weights ${WeightsFile}
            # -- Compute GC using fisher-z correlation
            echo "-- Computing GBC using correlation w/ fisher-z transform with weights file..."
            echo ""
            wb_command -cifti-reduce ${PConnBOLDOutputRfZ} MEAN ${GBCBOLDOutputRfZ} -only-numeric
        fi
        if [ "$UseWeights" == "no" ]; then
            # -- Compute pconn using correlation
            echo "-- Computing pconn using correlation..."
            echo ""
            wb_command -cifti-correlation ${BOLDOutput} ${PConnBOLDOutputR}
            # -- Compute GBC using correlation
            echo "-- Computing GBC using correlation..."
            echo ""
            wb_command -cifti-reduce ${PConnBOLDOutputR} MEAN ${GBCBOLDOutputR} -only-numeric
            # -- Compute pconn using covariance
            echo "-- Computing pconn using covariance..."
            echo ""
            wb_command -cifti-correlation ${BOLDOutput} ${PConnBOLDOutputCov} -covariance
            # -- Compute GBC using covariance
            echo "-- Computing GBC using covariance..."
            echo ""
            wb_command -cifti-reduce ${PConnBOLDOutputCov} MEAN ${GBCBOLDOutputCov} -only-numeric
            # -- Compute pconn using fisher-z correlation
            echo "-- Computing pconn using correlation w/ fisher-z transform..."
            echo ""
            wb_command -cifti-correlation ${BOLDOutput} ${PConnBOLDOutputRfZ} -fisher-z
            # -- Compute GBC using fisher-z correlation
            echo "-- Computing GBC using correlation w/ fisher-z transform..."
            echo ""
            wb_command -cifti-reduce ${PConnBOLDOutputRfZ} MEAN ${GBCBOLDOutputRfZ} -only-numeric
        fi
    fi
fi

if [ "$ExtractData" == "yes" ]; then 
    echo "--- Requested extraction of data in CSV format."
    echo ""
    if [ -z "$SingleInputFile" ] && [ "$InputDataType" == "dtseries" ] && [ "$ComputePConn" == "yes" ]; then
        echo "--- Saving out the parcellated data in a CSV file..."
        echo ""
        # -- Specify pconn file outputs for correlation (r) value and covariance 
        CSVOutPConnFileExtR="r.csv"
        CSVOutPConnFileExtCov="cov.csv"
        CSVOutPConnFileExtRfZ="r_Fz.csv"
        CSVPConnBOLDOutputR="$SessionsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${CSVOutPConnFileExtR}"
        CSVPConnBOLDOutputCov="$SessionsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${CSVOutPConnFileExtCov}"
        CSVPConnBOLDOutputRfZ="$SessionsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${CSVOutPConnFileExtRfZ}"
        rm -f ${CSVPConnBOLDOutputR} 2> /dev/null
        rm -f ${CSVPConnBOLDOutputCov} 2> /dev/null
        rm -f ${CSVPConnBOLDOutputRfZ} 2> /dev/null
        wb_command -nifti-information -print-matrix ${PConnBOLDOutputR} >> ${CSVPConnBOLDOutputR}
        wb_command -nifti-information -print-matrix ${PConnBOLDOutputCov} >> ${CSVPConnBOLDOutputCov}
        wb_command -nifti-information -print-matrix ${PConnBOLDOutputRfZ} >> ${CSVPConnBOLDOutputRfZ}
    fi
    if [ "$InputDataType" == "dscalar" ]; then
        echo "--- Saving out the parcellated dscalar data in a CSV file..."
        echo ""
        if [ -z "$SingleInputFile" ]; then
            DscalarFileExtCSV=".csv"
            CSVDPScalarBoldOut="$SessionsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${DscalarFileExtCSV}"
        else
            CSVDPScalarBoldOut="$OutPath/${SingleInputFile}_${OutName}_${DscalarFileExtCSV}"
        fi
        rm -f "$CSVDPScalarBoldOut" 2> /dev/null
        wb_command -nifti-information -print-matrix ${BOLDOutput} >> ${CSVDPScalarBoldOut}
    fi
    if [ -z "$SingleInputFile" ] && [ "$InputDataType" == "dtseries" ]; then
        echo "--- Saving out the parcellated single file dtseries data in a CSV file..."
        echo ""
        CSVDTseriesFileExtCSV=".csv"
        CSVDTseriesFileExtCSV="$SessionsFolder/$CASE/$OutPath/${InputFile}_${OutName}_${CSVDTseriesFileExtCSV}"
        rm -f "$CSVDTseriesFileExtCSV" 2> /dev/null
        wb_command -nifti-information -print-matrix ${BOLDOutput} >> ${CSVDTseriesFileExtCSV}
    fi
fi

# -- Perform completion checks
echo "-- Checking outputs..."
echo ""
if [ -f "$BOLDOutput" ]; then
    echo "Parcellated BOLD file:           $BOLDOutput"
    echo ""
else
    echo "ERROR: Parcellated BOLD file $BOLDOutput is missing. Something went wrong."
    echo ""
    exit 1
fi
if [ "$ComputePConn" == "yes" ]; then
    if [ -f "$PConnBOLDOutputR" ]; then
        echo "Parcellated connectivity (pconn) BOLD file using correlation:           $PConnBOLDOutputR"
        echo ""
    else
        echo "ERROR: Parcellated connectivity (pconn) BOLD file using correlation $PConnBOLDOutputR is missing. Something went wrong."
        echo ""
        exit 1
    fi
    if [ -f "$PConnBOLDOutputCov" ]; then
        echo "Parcellated connectivity (pconn) BOLD file using covariance:           $PConnBOLDOutputCov"
        echo ""
    else
        echo "ERROR: Parcellated connectivity (pconn) BOLD file using covariance $PConnBOLDOutputCov is missing. Something went wrong."
        echo ""
        exit 1
    fi
    if [ -f "$PConnBOLDOutputRfZ" ]; then
        echo "Parcellated connectivity (pconn) BOLD file using correlation w/ fisher-z transform:           $PConnBOLDOutputRfZ"
        echo ""
    else
        echo "ERROR: Parcellated connectivity (pconn) BOLD file using correlation w/ fisher-z transform $PConnBOLDOutputRfZ is missing. Something went wrong."
        echo ""
        exit 1
    fi
fi

echo "--- BOLD Parcellation completed. Check output log for outputs and possible issues."
echo ""
echo "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@

