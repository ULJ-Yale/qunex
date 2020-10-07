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
# DWIparcellate.sh
#
# ## LICENSE
#
# * The DWIparcellate.sh = the "Software"
# * This Software conforms to the license outlined in the Qu|Nex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ## TODO
#
# ## DESCRIPTION 
#   
# This script, DWIparcellate.sh, implements parcellation on the DWI dense connectomes 
# using a whole-brain parcellation (e.g.Glasser parcellation with subcortical labels included)
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * Connectome Workbench (v1.0 or above)
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./DWIparcellate.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are either Conn1.nii.gz or Conn3.nii.gz, both of which are results of the AP probtrackxgpudense function
# * These data are stored in: "$SessionsFolder/sessions/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/ 
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
 echo ""
 echo "This function implements parcellation on the DWI dense connectomes using a "
 echo "whole-brain parcellation (e.g. Glasser parcellation with subcortical labels "
 echo "included)."
 echo ""
 echo "It explicitly assumes the the Human Connectome Project folder structure for "
 echo "preprocessing. Dense Connectome DWI data needs to be in the following folder::"
 echo ""
 echo " <folder_with_sessions>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/"
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "--sessionsfolder    Path to study data folder"
 echo "--session           Comma separated list of sessions to run"
 echo "--matrixversion     Matrix solution version to run parcellation on; e.g. 1 or 3"
 echo "--parcellationfile  Specify the absolute path of the file you want to use for "
 echo "                    parcellation "
 echo "                    (e.g. /gpfs/project/fas/n3/Studies/Connectome/Parcellations/GlasserParcellation/LR_Colelab_partitions_v1d_islands_withsubcortex.dlabel.nii)"
 echo "--outname=          Specify the suffix output name of the pconn file"
 echo "--overwrite         Delete prior run for a given session (yes/no)"
 echo "--waytotal          Use the waytotal normalized version of the DWI dense "
 echo "                    connectome. Default: [none]"
 echo ""
 echo "                    - none     ... without waytotal normalization" 
 echo "                    - standard ... standard waytotal normalized"
 echo "                    - log      ... log-transformed waytotal normalized"
 echo ""
 echo "EXAMPLE USE"
 echo "==========="
 echo ""
 echo "Run directly via::"
 echo ""
 echo " ${TOOLS}/${QUNEXREPO}/connector/functions/DWIparcellate.sh \ "
 echo " --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
 echo ""
 reho "NOTE: --scheduler is not available via direct script call."
 echo ""
 echo "Run via:: "
 echo ""
 echo "  qunex DWIparcellate --<parameter1> --<parameter2> ... --<parameterN> "
 echo ""
 geho "NOTE: scheduler is available via qunex call."
 echo ""
 echo "--scheduler       A string for the cluster scheduler (e.g. LSF, PBS or SLURM) "
 echo "                  followed by relevant options"
 echo ""
 echo "For SLURM scheduler the string would look like this via the qunex call:: "
 echo ""                   
 echo "  --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
 echo ""
 echo "::"
 echo ""
 echo " qunex DWIparcellate --sessionsfolder='<folder_with_sessions>' \ "
 echo " --sessions='<comma_separarated_list_of_cases>' \ "
 echo " --matrixversion='3' \ "
 echo " --parcellationfile='<dlabel_file_for_parcellation>' \ "
 echo " --overwrite='no' \ "
 echo " --outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
 echo ""
 echo "Example with flagged parameters for submission to the scheduler::"
 echo ""
 echo " qunex DWIparcellate --sessionsfolder='<folder_with_sessions>' \ "
 echo " --sessions='<comma_separarated_list_of_cases>' \ "
 echo " --matrixversion='3' \ "
 echo " --parcellationfile='<dlabel_file_for_parcellation>' \ "
 echo " --overwrite='no' \ "
 echo " --outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
 echo " --scheduler='<name_of_scheduler_and_options>' \ "
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
#  -- Parse arguments
# ------------------------------------------------------------------------------

########################################## INPUTS ########################################## 

# DWI Data and T1w data needed in HCP-style format and dense DWI probtrackX should be completed
# The data should be in $DiffFolder="$SessionsFolder"/"$CASE"/hcp/"$CASE"/MNINonLinear/Results/Tractography
# Mandatory input parameters:
    # SessionsFolder 
    # Session        
    # MatrixVersion     e.g. 1 or 3
    # ParcellationFile  in *.dlabel.nii format
    # OutName  
########################################## OUTPUTS #########################################

# -- Outputs will be *pconn.nii files located here:
#       DWIOutput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"

# -- Get the command line options for this script
get_options() {
local scriptName=$(basename ${0})
local arguments=($@)
# -- Initialize global output variables
unset SessionsFolder
unset Session
unset MatrixVersion
unset ParcellationFile
unset OutName
unset Overwrite
unset WayTotal
unset DWIOutFilePconn
unset DWIOutFilePDconn
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
            ;;
        --version)
            version_show $@
            exit 0
            ;;
        --sessionsfolder=*)
            SessionsFolder=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --session=*)
            CASE=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --matrixversion=*)
            MatrixVersion=${argument/*=/""}
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
        --waytotal=*)
            WayTotal=${argument/*=/""}
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

# -- Check required parameters
if [ -z ${SessionsFolder} ]; then
    usage
    reho "ERROR: <sessions-folder-path> not specified>"
    echo ""
    exit 1
fi
if [ -z ${CASE} ]; then
    usage
    reho "ERROR: <session-id> not specified>"
    echo ""
    exit 1
fi
if [ -z ${MatrixVersion} ]; then
    usage
    reho "ERROR: <matrix_version_value> not specified>"
    echo ""
    exit 1
fi
if [ -z ${ParcellationFile} ]; then
    usage
    reho "ERROR: <file_for_parcellation> not specified>"
    echo ""
    exit 1
fi
if [ -z ${WayTotal} ]; then
    reho "No <use_waytotal_normalized_data> specified. Assuming default [none]"
    WayTotal=none
    echo ""
fi
if [ -z ${OutName} ]; then
    usage
    reho "ERROR: <name_of_output_pconn_file> not specified>"
    exit 1
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
echo "   MatrixVersion: ${MatrixVersion}"
echo "   ParcellationFile: ${ParcellationFile}"
echo "   Waytotal normalization: ${WayTotal}"
echo "   OutName: ${OutName}"
echo "   Overwrite: ${Overwrite}"
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""
}

######################################### DO WORK ##########################################

# gzip $ResultsFolder/${OutFileName} --fast
# gzip $ResultsFolder/${OutFileTemp}_waytotnorm.dconn.nii --fast

main() {

# -- Get Command Line Options
get_options $@

# -- Define inputs and output
echo "--- Establishing paths for all input and output folders:"; echo ""

# -- Define input and check if WayTotal normalization is selected
if [ "$WayTotal" == "none" ]; then
	echo "--- Using dconn file without waytotal normalization"; echo ""
	DWIInput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography/Conn${MatrixVersion}.dconn.nii.gz"
	DWIOutFilePconn="${CASE}_Conn${MatrixVersion}_${OutName}.pconn.nii"
	DWIOutFilePDconn="${CASE}_Conn${MatrixVersion}_${OutName}.pdconn.nii"
fi
if [ "$WayTotal" == "standard" ]; then
	echo "--- Using waytotal normalized dconn file"; echo ""
	DWIInput="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm.dconn.nii.gz"
	DWIOutFilePconn="${CASE}_Conn${MatrixVersion}_waytotnorm.${OutName}.pconn.nii"
	DWIOutFilePDconn="${CASE}_Conn${MatrixVersion}_waytotnorm.${OutName}.pdconn.nii"
fi
if [ "$WayTotal" == "log" ]; then
	echo "--- Using log-transformed waytotal normalized dconn file"; echo ""
	DWIInput="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography/Conn${MatrixVersion}_waytotnorm_log.dconn.nii.gz"
	DWIOutFilePconn="${CASE}_Conn${MatrixVersion}_waytotnorm_log.${OutName}.pconn.nii"
	DWIOutFilePDconn="${CASE}_Conn${MatrixVersion}_waytotnorm_log.${OutName}.pdconn.nii"
fi

# -- Define output
DWIOutput="$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/Tractography"
echo "      Dense DWI Connectome Input:              ${DWIInput}"; echo ""
echo "      Parcellated DWI Connectome Output:       ${DWIOutput}/${DWIOutFilePconn}"; echo ""

# -- Delete any existing output sub-directories
if [ "$Overwrite" == "yes" ]; then
	reho "--- Deleting prior runs for $DiffData..."
	echo ""
	rm -f "$DWIOutput"/"$DWIOutFilePDconn" > /dev/null 2>&1
	rm -f "$DWIOutput"/"$DWIOutFilePconn" > /dev/null 2>&1
fi

# -- Check if parcellation was completed
reho "--- Checking if parcellation was completed..."
echo ""

if [ -f ${DWIOutput}/${DWIOutFilePconn} ]; then
	geho "--- Parcellation data found: "
	echo ""
	echo "    ${DWIOutput}/${DWIOutFilePconn}"
	echo ""
	exit 1
else
	reho "--- Parcellation data not found."
	echo ""
	echo "--- Computing parcellation by COLUMN on $DWIInput..."
	echo ""
	# -- First parcellate by COLUMN and save a *pdconn file
	wb_command -cifti-parcellate "$DWIInput" "$ParcellationFile" COLUMN "$DWIOutput"/"$DWIOutFilePDconn"
	echo "--- Computing parcellation by ROW on ${DWIOutput}/${DWIOutFilePDconn} ..."
	echo ""
	# -- Next parcellate by ROW and save final *pconn file
	wb_command -cifti-parcellate "$DWIOutput"/"$DWIOutFilePDconn" "$ParcellationFile" ROW "$DWIOutput"/"$DWIOutFilePconn"
fi	

# -- Perform completion checks
reho "--- Checking outputs..."
echo ""
if [ -f ${DWIOutput}/${DWIOutFilePconn} ]; then
	geho "Parcellated (pconn) file for Matrix $MatrixVersion:     ${DWIOutput}/${DWIOutFilePconn}"
	echo ""
else
	reho "Parcellated (pconn) file for Matrix $MatrixVersion is missing. Something went wrong."
	echo ""
	exit 1
fi

reho "--- DWI Parcellation successfully completed"
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
