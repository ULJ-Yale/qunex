#!/bin/sh 
#set -x
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
# * Alan Anticevic, Department of Psychiatry, Yale University
#
# ## PRODUCT
#
#  QCPreprocessing.sh is a QC processing wrapper
#
# ## LICENSE
#
# * The QCPreprocessing.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ## TODO
#
# ## DESCRIPTION 
#
# This script, QCPreprocessing.sh, implements quality control for various stages of 
# HCP preprocessed data
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * Connectome Workbench (v1.0 or above)
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./QCPreprocessing.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are HCP files from previous processing
# * These may be stored in: "$SubjectsFolder/$CASE/hcp/$CASE/ 
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
     echo ""
     echo "-- DESCRIPTION for QCPreprocessing"
     echo ""
     echo "This function runs the QC preprocessing for a given specified modality. Supported: T1w, T2w, myelin, BOLD, DWI."
     echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing."
     echo ""
     echo ""
     echo "The function is compabible with both legacy data [without T2w scans] and HCP-compliant data [with T2w scans and DWI]."
     echo ""
     echo "The function generates 3 types of outputs, which are stored within the Study in <path_to_folder_with_subjects>/QC "
     echo ""
     echo "                *.scene files that contain all relevant data loadable into Connectome Workbench"
     echo "                *.png images that contain the output of the referenced scene file."
     echo "                *.zip file that contains all relevant files to download and re-generate the scene in Connectome Workbench."
     echo ""
     echo "                Note: For BOLD data there is also an SNR txt output if specified."
     echo ""
     echo "-- REQUIRED GENERAL PARMETERS:"
     echo ""
     echo "--function=<function_name>                                      Explicitly specify Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
     echo "--subjectsfolder=<folder_with_subjects>                         Path to study folder that contains subjects"
     echo "--subjects=<list_of_cases>                                      List of subjects to run, separated by commas"
     echo "--modality=<input_modality_for_qc>                              Specify the modality to perform QC on [Supported: T1w, T2w, myelin, BOLD, DWI]"
     echo ""
     echo "-- DWI PARMETERS"
     echo ""
     echo "--dwipath=<path_for_dwi_data>                                   Specify the input path for the DWI data [may differ across studies; e.g. Diffusion or Diffusion or Diffusion_DWI_dir74_AP_b1000b2500]"
     echo "--dwidata=<file_name_for_dwi_data>                              Specify the file name for DWI data [may differ across studies; e.g. data or DWI_dir74_AP_b1000b2500_data]"
     echo "--dtifitqc=<visual_qc_for_dtifit>                               Specify if dtifit visual QC should be completed [e.g. yes or no]"
     echo "--bedpostxqc=<visual_qc_for_bedpostx>                           Specify if BedpostX visual QC should be completed [e.g. yes or no]"
     echo "--eddyqcstats=<qc_stats_for_eddy>                               Specify if EDDY QC stats should be linked into QC folder and motion report generated [e.g. yes or no]"
     echo "--dwilegacy=<dwi_data_processed_via_legacy_pipeline>            Specify if DWI data was processed via legacy pipelines [e.g. yes or no]"
     echo ""
     echo "-- BOLD PARMETERS"
     echo ""
     echo "--bolddata=<bold_run_numbers>                                    Specify BOLD data numbers separated by comma, space or pipe."
     echo "                                                                   This flag is interchangeable with --bolds or --boldruns to allow more redundancy in specification"
     echo "                                                                   Note: If unspecified empty the QC script will by default look into /<path_to_study_subjects_folder>/<subject_id>/subject_hcp.txt and identify all BOLDs to process"
     echo "--boldprefix=<prefix_file_name_for_bold_data>                    Specify the prefix file name for BOLD dtseries data [may differ across studies depending on processing; e.g. BOLD or TASK or REST]"
     echo "                                                                   Note: If unspecified then QC script will assume that folder names containing processed BOLDs are named numerically only (e.g. 1, 2, 3)."
     echo "--boldsuffix=<suffix_file_name_for_bold_data>                    Specify the suffix file name for BOLD dtseries data [may differ across studies depending on processing; e.g. Atlas or MSMAll]"
     echo "--skipframes=<number_of_initial_frames_to_discard_for_bold_qc>   Specify the number of initial frames you wish to exclude from the BOLD QC calculation"
     echo "--snronly=<compute_snr_only_for_bold>                            Specify if you wish to compute only SNR BOLD QC calculation and skip image generation <yes/no>. Default is [no]"
     echo ""
     echo "-- OPTIONAL PARMETERS:"
     echo "" 
     echo "--overwrite=<clean_prior_run>                                    Delete prior QC run"
     echo "--templatefolder=<path_for_the_template_folder>                  Specify the absolute path name of the template folder (default: $TOOLS/${MNAPREPO}/library/data/templates)"
     echo "--outpath=<path_for_output_file>                                 Specify the absolute path name of the QC folder you wish the individual images and scenes saved to."
     echo "                                                                 If --outpath is unspecified then files are saved to: /<path_to_study_subjects_folder>/QC/<input_modality_for_qc>"
     echo "--scenezip=<zip_generate_scene_file>                             Generates a ZIP file with the scene and all relevant files for Connectome Workbench visualization [yes]"
     echo "                                                                 Note: If scene zip set to yes, then relevant scene files will be zipped with an updated relative base folder." 
     echo "                                                                       All paths will be relative to this base --> <path_to_study_subjects_folder>/<subject_id>/hcp/<subject_id>"
     echo "                                                                 The scene zip file will be saved to: "
     echo "                                                                     /<path_for_output_file>/<subject_id>.<input_modality_for_qc>.QC.wb.zip"
     echo ""
     echo "--scheduler=<name_of_cluster_scheduler_and_options>              A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
     echo "                                                                     e.g. for SLURM the string would look like this: "
     echo "                                                                    --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
     echo "--timestamp=<specify_time_stamp>                                 Allows user to specify unique time stamp or to parse a time stamp from connector wrapper"
     echo "--suffix=<specify_suffix_id_for_logging>                         Allows user to specify unique suffix or to parse a time stamp from connector wrapper Default is [ <subject_id>_<timestamp> ]"
     echo "" 
     echo ""
     echo "-- Complete examples for each supported modality:"
     echo ""
     echo ""
     echo "# -- T1w QC"
     echo "QCPreprocessing.sh --subjectsfolder='<path_to_study_subjects_folder>' \ "
     echo "--function='QCPreproc' \ "
     echo "--subjects='<comma_separated_list_of_cases>' \ "
     echo "--outpath='<path_for_output_file> \ "
     echo "--templatefolder='<path_for_the_template_folder>' \ "
     echo "--modality='T1w' \ "
     echo "--overwrite='yes' "
     echo ""
     echo "# -- T2w QC"
     echo "QCPreprocessing.sh --subjectsfolder='<path_to_study_subjects_folder>' \ "
     echo "--function='QCPreproc' \ "
     echo "--subjects='<comma_separated_list_of_cases>' \ "
     echo "--outpath='<path_for_output_file> \ "
     echo "--templatefolder='<path_for_the_template_folder>' \ "
     echo "--modality='T2w' \ "
     echo "--overwrite='yes'"
     echo ""
     echo "# -- Myelin QC"
     echo "QCPreprocessing.sh --subjectsfolder='<path_to_study_subjects_folder>' \ "
     echo "--function='QCPreproc' \ "
     echo "--subjects='<comma_separated_list_of_cases>' \ "
     echo "--outpath='<path_for_output_file> \ "
     echo "--templatefolder='<path_for_the_template_folder>' \ "
     echo "--modality='myelin' \ "
     echo "--overwrite='yes'"
     echo ""
     echo "# -- DWI QC "
     echo "QCPreprocessing.sh --subjectsfolder='<path_to_study_subjects_folder>' \ "
     echo "--function='QCPreproc' \ "
     echo "--subjects='<comma_separated_list_of_cases>' \ "
     echo "--templatefolder='<path_for_the_template_folder>' \ "
     echo "--modality='DWI' \ "
     echo "--outpath='<path_for_output_file> \ "
     echo "--dwilegacy='yes' \ "
     echo "--dwidata='<file_name_for_dwi_data>' \ "
     echo "--dwipath='<path_for_dwi_data>' \ "
     echo "--overwrite='yes'"
     echo ""
     echo "# -- BOLD QC"
     echo "QCPreprocessing.sh --subjectsfolder='<path_to_study_subjects_folder>' \ "
     echo "--function='QCPreproc' \ "
     echo "--subjects='<comma_separated_list_of_cases>' \ "
     echo "--outpath='<path_for_output_file> \ "
     echo "--templatefolder='<path_for_the_template_folder>' \ "
     echo "--modality='BOLD' \ "
     echo "--bolddata='1' \ "
     echo "--boldsuffix='Atlas' \ "
     echo "--overwrite='yes'"
     echo ""
     echo ""
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
# -- Parse and check all arguments
# ------------------------------------------------------------------------------

########### INPUTS ###############

	# -- Various HCP processed modalities

########## OUTPUTS ###############

	# -- Outputs will be files located in the location specified in the outputpath

# -- Set general options functions
opts_GetOpt() {
sopt="$1"
shift 1
for fn in "$@" ; do
	if [ `echo ${fn} | grep -- "^${sopt}=" | wc -w` -gt 0 ]; then
		echo "${fn}" | sed "s/^${sopt}=//"
		return 0
	fi
done
}

opts_CheckForHelpRequest() {
for fn in "$@" ; do
	if [ "$fn" = "--help" ]; then
		return 0
	fi
done
}

if [ $(opts_CheckForHelpRequest $@) ]; then
	showVersion
	show_usage
	exit 0
fi

# -- Get the command line options for this script
# get_options() {

# -- Initialize global variables
unset SubjectsFolder # --subjectsfolder=
unset CASE # --subject=
unset Overwrite # --overwrite=
unset OutPath # --outpath
unset TemplateFolder # --templatefolder
unset Modality # --modality
unset DWIPath # --dwipath
unset DWIData  # --dwidata
unset DtiFitQC # --dtifitqc
unset BedpostXQC # --bedpostxqc
unset EddyQCStats # --eddyqcstats
unset DWILegacy # --dwilegacy
unset BOLDS # --bolddata
unset BOLDPrefix # --boldprefix
unset BOLDSuffix # --boldsuffix
unset SkipFrames # --skipframes
unset SNROnly # --snronly
unset TimeStamp # --timestamp
unset Suffix # --suffix
unset SceneZip # --scenezip
runcmd=""

# -- Parse general arguments
SubjectsFolder=`opts_GetOpt "--subjectsfolder" $@`
CASE=`opts_GetOpt "--subject" $@`
Overwrite=`opts_GetOpt "--overwrite" $@`
OutPath=`opts_GetOpt "--outpath" $@`
TemplateFolder=`opts_GetOpt "--templatefolder" $@`
Modality=`opts_GetOpt "--modality" $@`

# -- Parse DWI arguments
DWIPath=`opts_GetOpt "--dwipath" $@`
DWIData=`opts_GetOpt "--dwidata" $@`
DtiFitQC=`opts_GetOpt "--dtifitqc" $@`
BedpostXQC=`opts_GetOpt "--bedpostxqc" $@`
EddyQCStats=`opts_GetOpt "--eddyqcstats" $@`
DWILegacy=`opts_GetOpt "--dwilegacy" $@`

# -- Parse BOLD arguments
BOLDDATA=`opts_GetOpt "--bolddata" "$@"` #| sed 's/,/ /g;s/|/ /g'`; BOLDDATA=`echo "$BOLDDATA" | sed 's/,/ /g;s/|/ /g'`
BOLDRUNS=`opts_GetOpt "--boldruns" "$@"` #| sed 's/,/ /g;s/|/ /g'`; BOLDRUNS=`echo "$BOLDRUNS" | sed 's/,/ /g;s/|/ /g'`
BOLDS=`opts_GetOpt "--bolds" "$@"` #| sed #'s/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`
if [[ ! -z $BOLDDATA ]]; then
	if [[ -z $BOLDS ]]; then
		BOLDS="${BOLDDATA}"
	fi
fi
if [[ ! -z $BOLDRUNS ]]; then
	if [[ -z $BOLDS ]]; then
		BOLDS="${BOLDDATA}"
	fi
fi
reho "${BOLDS}"

BOLDSuffix=`opts_GetOpt "--boldsuffix" $@`
BOLDPrefix=`opts_GetOpt "--boldprefix" $@`
SkipFrames=`opts_GetOpt "--skipframes" $@`
SNROnly=`opts_GetOpt "--snronly" $@`

# -- Parse optional arguments
TimeStamp=`opts_GetOpt "--timestamp" $@`
Suffix=`opts_GetOpt "--suffix" $@`
SceneZip=`opts_GetOpt "--scenezip" $@`

# -- Check general required parameters
if [ -z ${CASE} ]; then
    usage
    reho "ERROR: <subject_id> not specified."; echo ""
    exit 1
fi
if [ -z ${SubjectsFolder} ]; then
    usage
    reho "ERROR: <subjects_folder> not specified."; echo ""
    exit 1
fi
if [ -z ${Overwrite} ]; then
    Overwrite="no"
    echo "Overwrite value not explicitly specified. Using default: ${Overwrite}"; echo ""
fi
if [ -z ${OutPath} ]; then
    OutPath="${SubjectsFolder}/QC/${Modality}"
    echo "Output folder path value not explicitly specified. Using default: ${OutPath}"; echo ""
fi
if [ -z ${Modality} ]; then 
    usage
    reho "Error:  Modality to perform QC on missing [Supported: T1w, T2w, myelin, BOLD, DWI]"; echo ""
    exit 1
fi
if [ -z "$TemplateFolder" ]; then
    TemplateFolder="${TOOLS}/${MNAPREPO}/library/data/"
    echo "Template folder path value not explicitly specified. Using default: ${TemplateFolder}"; echo ""
fi
if [ -z ${TimeStamp} ]; then
   TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
   Suffix="$CASE_$TimeStamp"
   echo "Time stamp for logging not found. Setting now: ${TimeStamp}"; echo ""
fi
if [ -z ${Suffix} ]; then
   Suffix="$CASE_$TimeStamp"
   echo "Suffix not manually set. Setting default: ${Suffix}"; echo ""
fi
if [ -z ${SceneZip} ]; then
    SceneZip="yes"
    echo "Generation of scene zip file not explicitly provided. Using defaults: ${SceneZip}"; echo ""
fi

# -- DWI modality-specific settings:
if [ "$Modality" = "DWI" ]; then
	if [ -z "$DWIPath" ]; then DWIPath="Diffusion"; echo "DWI input path not explicitly specified. Using default: ${DWIPath}"; echo ""; fi
	if [ -z "$DWIData" ]; then DWIData="data"; echo "DWI data name not explicitly specified. Using default: ${DWIData}"; echo ""; fi
	if [ -z "$DWILegacy" ]; then DWILegacy="no"; echo "DWI legacy not specified. Using default: ${TemplateFolder}"; echo ""; fi
	if [ -z "$DtiFitQC" ]; then DtiFitQC="no"; echo "DWI dtifit QC not specified. Using default: ${DtiFitQC}"; echo ""; fi
	if [ -z "$BedpostXQC" ]; then BedpostXQC="no"; echo "DWI BedpostX not specified. Using default: ${BedpostXQC}"; echo ""; fi
	if [ -z "$EddyQCStats" ]; then EddyQCStats="no"; echo "DWI EDDY QC Stats not specified. Using default: ${EddyQCStats}"; echo ""; fi
fi
# -- BOLD modality-specific settings:
if [ "$Modality" = "BOLD" ]; then
	# - Check if BOLDS parameter is empty:
	if [ -z "$BOLDS" ]; then 
		echo ""
		reho "BOLD input list not specified. Relying subject_hcp.txt individual information files."
		BOLDS="subject_hcp.txt"
		echo ""
	fi
	# -- Check if subject_hcp.txt is present:
	if [[ ${BOLDS} == "subject_hcp.txt" ]]; then
		echo ""
		echo "--- Using subject_hcp.txt individual information files. Verifying that subject_hcp.txt exists."; echo ""
		if [[ -f ${SubjectsFolder}/${CASE}/subject_hcp.txt ]]; then
			echo "${SubjectsFolder}/${CASE}/subject_hcp.txt found. Proceeding..."
		else
			reho "${SubjectsFolder}/${CASE}/subject_hcp.txt NOT found. Check BOLD inputs."
			echo ""
			exit 1
		fi
	else
		# -- Remove commas or pipes from BOLD input list if still present if using manual input
		BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`
	fi
	# -- Set BOLD prefix correctly
	if [ -z "$BOLDPrefix" ]; then 
		BOLDPrefix=""; echo "BOLD prefix not specified. Assuming no prefix"; echo ""
	fi
	# -- Set BOLD suffix correctly
	if [ -z "$BOLDSuffix" ]; then 
		BOLDSuffix=""; echo "BOLD suffix not specified. Assuming no suffix"; echo ""
	else
		BOLDSuffix="_${BOLDSuffix}"
	fi
	# -- Clean prior TSNR reprots for this case and start fresh
	for BOLD in $BOLDS; do rm -f ${OutPath}/TSNR_Report_${BOLD}*.txt &> /dev/null; done
	# -- Set SkipFrames and SNROnly defaults if missing
	if [ -z "$SkipFrames" ]; then SkipFrames="0"; echo ""; fi
	if [ -z "$SNROnly" ]; then SNROnly="no"; echo ""; fi
fi

# -- Set StudyFolder
cd $SubjectsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null

scriptName=$(basename ${0})

# -- Report options
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "  Study Folder: ${StudyFolder}"
echo "  Subject Folder: ${SubjectsFolder}"
echo "  Subjects: ${CASE}"
echo "  QC Modality: ${Modality}"
echo "  QC Output Path: ${OutPath}"
echo "  QC Scene Template: ${TemplateFolder}"
echo "  Overwrite prior run: ${Overwrite}"
echo "  Time stamp for logging: ${TimeStamp}"
echo "  Zip Scene File: ${SceneZip}"
if [ "$Modality" = "DWI" ]; then
	echo "  DWI input path: ${DWIPath}"
	echo "  DWI input name: ${DWIData}"
	echo "  DWI legacy processing: ${DWILegacy}"
	echo "  DWI dtifit QC requested: ${DtiFitQC}"
	echo "  DWI bedpostX QC requested: ${BedpostXQC}"
	echo "  DWI EDDY QC Stats requested: ${EddyQCStats}"
fi
if [ "$Modality" = "BOLD" ]; then
	echo "  BOLD data input: ${BOLDS}"
	echo "  BOLD prefix: ${BOLDPrefix}"
	echo "  BOLD suffix: ${BOLDSuffix}"
	echo "  Skip Initial Frames: ${SkipFrames}"
	echo "  Compute SNR Only: ${SNROnly}"
	if [ "$SNROnly" == "yes" ]; then 
		echo ""
		echo "BOLD SNR only specified. Will skip QC images"
		echo ""
	fi
fi
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""

# }

######################################### DO WORK ##########################################

main() {

# -- Parse all the input cases for an individual or group run
INPUTCASES=`echo "$CASE" | sed 's/,/ /g'`
echo ""

# -- Define all inputs and outputs depending on data type input

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
		rm -f "$OutPath"/${CASE}."$Modality".* &> /dev/null
	fi
fi
# -- Check if a given case exists
if [ -f "$OutPath"/${CASE}."$Modality".QC.png ]; then
	echo ""
	geho " --- ${Modality} QC scene completed: ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
	echo ""
	return 1
else 
	# -- Start of generating QC
	echo ""
	geho " --- Generating ${Modality} QC scene: ${OutPath}/${CASE}.${Modality}.QC.wb.scene"
	echo ""
	echo ""
	geho " --- Checking and generating output folders..."
	echo ""
	# -- Check general output folders for QC
	if [ ! -d ${SubjectsFolder}/QC ]; then
		mkdir -p ${SubjectsFolder}/QC &> /dev/null
	fi
	# -- Check T1w output folders for QC
	if [ ! -d ${OutPath} ]; then
		mkdir -p ${OutPath} &> /dev/null
	fi
	# -- Define log folder
	LogFolder=${OutPath}/qclog
	if [ ! -d ${LogFolder} ]; then
		mkdir -p ${LogFolder}  &> /dev/null
	fi
	geho "    Logfolder: ${LogFolder}"
	geho "    Output path: ${OutPath}"
	echo ""
fi

# -------------------------------------------
# -- Start of BOLD QC Section
# -------------------------------------------

# -- Check if modality is BOLD
if [ "$Modality" == "BOLD" ]; then
	if [ "$BOLDS" == "subject_hcp.txt" ]; then
		geho "--- subject_hcp.txt parameter file specified. Verifying presence of subject_hcp.txt before running QC on all BOLDs..."; echo ""
		if [ -f ${SubjectsFolder}/${CASE}/subject_hcp.txt ]; then
			# -- Stalling on some systems --> BOLDCount=`more ${SubjectsFolder}/${CASE}/subject_hcp.txt | grep "bold" | grep -v "ref" | wc -l`
			BOLDCount=`grep "bold" ${SubjectsFolder}/${CASE}/subject_hcp.txt  | grep -v "ref" | wc -l`
			rm ${SubjectsFolder}/${CASE}/BOLDNumberTmp.txt &> /dev/null
			COUNTER=1; until [ $COUNTER -gt $BOLDCount ]; do echo "$COUNTER" >> ${SubjectsFolder}/${CASE}/BOLDNumberTmp.txt; let COUNTER=COUNTER+1; done
			# -- Stalling on some systems --> BOLDS=`more ${SubjectsFolder}/${CASE}/BOLDNumberTmp.txt`
			BOLDS=`cat ${SubjectsFolder}/${CASE}/BOLDNumberTmp.txt`
			rm ${SubjectsFolder}/${CASE}/BOLDNumberTmp.txt &> /dev/null
			geho "--- Information file ${SubjectsFolder}/${CASE}/subject_hcp.txt found. Proceeding to run QC on the following BOLDs:"; echo ""; echo "${BOLDS}"; echo ""
		else
			reho "--- ERROR: ${SubjectsFolder}/${CASE}/subject_hcp.txt not found. Check presence of file or specify specific BOLDs via input parameter."; echo ""
			exit 1
		fi
	else
		# -- Remove commas or pipes from BOLD input list if still present if using manual input
		BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`
	fi
	
	# -- Run BOLD loop across BOLD runs
	for BOLD in $BOLDS; do

		# -- Check if prefix is specified
		if [ ! -z "$BOLDPrefix" ]; then 
			echo ""
			BOLD="$BOLDPrefix_$BOLD"
			geho "-- BOLD Prefix specified. Appending to BOLD number: $BOLD"
			echo ""
		else
			# -- Check if BOLD folder with the given number contains additional prefix info and return an exit code if yes
			echo ""
			NoBOLDDirPreffix=`ls -d ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/*${BOLD}`
			NoBOLDPreffix=`ls -d ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/*${BOLD} | sed 's:/*$::' | sed 's:.*/::'`
			if [[ ! -z ${NoBOLDDirPreffix} ]]; then
				reho "-- A directory with the BOLD number is found but containing a prefix, yet no prefix was specified: "
				reho "   --> ${NoBOLDDirPreffix}"
				reho "-- Setting BOLD prefix to: $NoBOLDPreffix "
				echo ""
				reho "-- If this is not correct please re-run with correct --boldprefix flag to ensure correct BOLDs are specified."
				echo ""
				BOLD=$NoBOLDPreffix
			fi
		fi

		# -- Check if BOLD exists and skip if not it does not
		if [[ ! -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}.dtseries.nii ]]; then
			echo ""
			reho "--- BOLD data specified for BOLD ${BOLD} not found: "
			reho "     --> ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}.dtseries.nii "
			echo ""
			reho "--- Check presence of your inputs for BOLD ${BOLD} and re-run!"
			echo ""
			exit 1
		fi
		
		# -- Generate QC statistics for a given BOLD
		geho "--- BOLD data specified found. Generating QC statistics commands for BOLD ${BOLD} on ${CASE}..."
		echo ""
		# -- Reduce dtseries
		wb_command -cifti-reduce ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}.dtseries.nii \
		TSNR \
		${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_TSNR.dscalar.nii \
		-exclude-outliers 4 4
		# -- Compute SNR
		TSNR=`wb_command -cifti-stats ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_TSNR.dscalar.nii -reduce MEAN`
		# -- Record values 
		TSNRLog="${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_TSNR.dscalar.nii: ${TSNR}"
		TSNRReport="${OutPath}/TSNR_Report_${BOLD}_${TimeStampQCPreproc}.txt"
		printf "${TSNRLog}\n" >> ${TSNRReport}
		# -- Echo completion & Check SNROnly flag
		if [ -f ${TSNRReport} ]; then
			if [ SNROnly == "yes" ]; then 
				echo ""
				geho "--- Completed ONLY SNR calculations for ${TSNRLog}. Final report can be found here: ${TSNRReport}"; echo ""
				exit 1
			else
				geho "--- Completed SNR calculations for ${TSNRLog}. "
				geho "    Final report can be found here: ${TSNRReport}"
				echo ""
			fi
		else
			reho "--- SNR report not found. Something went wrong. Check inputs."; echo ""
		fi
		
		# -- Get values for plotting GS chart & Compute the GS scalar series file
		
		# -- Get TR
		TR=`fslval ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}.nii.gz pixdim4`
		
		# -- Clean preexisting outputs
		rm -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.txt &> /dev/null
		rm -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.dtseries.nii &> /dev/null
		rm -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.sdseries.nii &> /dev/null
		
		# -- Regenerate outputs
		wb_command -cifti-reduce ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}.dtseries.nii MEAN ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.dtseries.nii -direction COLUMN
		wb_command -cifti-stats ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.dtseries.nii -reduce MEAN >> ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.txt
		
		# -- Check skipped frames
		if [ ${SkipFrames} > 0 ]; then 
			rm -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS_omit_initial_${SkipFrames}_TRs.txt &> /dev/null
			tail -n +${SkipFrames} ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.txt >> ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS_omit_initial_${SkipFrames}_TRs.txt
			TR=`cat ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS_omit_initial_${SkipFrames}_TRs.txt | wc -l` 
			wb_command -cifti-create-scalar-series ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS_omit_initial_${SkipFrames}_TRs.txt ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.sdseries.nii -transpose -series SECOND 0 ${TR}
			xmax="$TR"
		else
			wb_command -cifti-create-scalar-series ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.txt ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.sdseries.nii -transpose -series SECOND 0 ${TR}
			xmax=`fslval ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}.nii.gz dim4`
		fi
		
		# -- Get mix/max stats
		ymax=`wb_command -cifti-stats ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.sdseries.nii -reduce MAX | sort -rn | head -n 1`	
		ymin=`wb_command -cifti-stats ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.sdseries.nii -reduce MAX | sort -n | head -n 1`
		
		# -- Rsync over template files for a given BOLD
		Com1="rsync -aWH ${TemplateFolder}/atlases/HCP/S900* ${OutPath}/ &> /dev/null "
		Com2="rsync -aWH ${TemplateFolder}/atlases/MNITemplates/MNI152_*_0.7mm.nii.gz ${OutPath}/ &> /dev/null "
		
		# -- Setup naming conventions before generating scene
		Com3="cp ${TemplateFolder}/scenes/qc/TEMPLATE.${Modality}.QC.wb.scene ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
		Com4="sed -i -e 's|DUMMYPATH|$SubjectsFolder|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene" 
		Com5="sed -i -e 's|DUMMYCASE|$CASE|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
		Com6="sed -i -e 's|DUMMYBOLDDATA|$BOLD|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
		Com7="sed -i -e 's|DUMMYXAXISMAX|$xmax|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
		Com8="sed -i -e 's|DUMMYYAXISMAX|$ymax|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
		Com9="sed -i -e 's|DUMMYYAXISMIN|$ymin|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
		
		# -- Set the BOLDSuffix variable
		Com10="sed -i -e 's|_DUMMYBOLDSUFFIX|$BOLDSuffix|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
		
		# -- Add timestamp to the scene
		Com11="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
		Com12="sed -i -e 's|DUMMYBOLDANNOT|$BOLD|g' ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
		
		# -- Output image of the scene
		Com13="wb_command -show-scene ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene 1 ${OutPath}/${CASE}.${Modality}.${BOLD}.GSmap.QC.wb.png 1194 539"
		Com14="wb_command -show-scene ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene 2 ${OutPath}/${CASE}.${Modality}.${BOLD}.GStimeseries.QC.wb.png 1194 539"
		
		# -- Clean temp scene
		Com15="rm ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene-e &> /dev/null"
		
		# -- Generate Scene Zip File if set to YES
		if [ "$SceneZip" == "yes" ]; then
			echo "--- Scene zip set to: $SceneZip. Relevant scene files will be zipped with the following base folder:" 
			echo "    ${SubjectsFolder}/${CASE}/hcp/${CASE}"
			echo ""
			echo "--- The zip file will be saved to: "
			echo "    ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.zip"
			echo ""
			RemoveScenePath="${SubjectsFolder}/${CASE}/hcp/${CASE}"
			Com16="cp ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.scene ${SubjectsFolder}/${CASE}/hcp/${CASE}/"
			Com17="rm ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.*.zip &> /dev/null "
			Com18="sed -i -e 's|$RemoveScenePath|.|g' ${SubjectsFolder}/${CASE}/hcp/${CASE}/${CASE}.${Modality}.${BOLD}.QC.wb.scene" 
			Com19="cd ${OutPath}; wb_command -zip-scene-file ${SubjectsFolder}/${CASE}/hcp/${CASE}/${CASE}.${Modality}.${BOLD}.QC.wb.scene pb0986.${Modality}.${BOLD}.QC.wb.${TimeStamp} ${CASE}.${Modality}.${BOLD}.QC.wb.${TimeStamp}.zip -base-dir ${SubjectsFolder}/${CASE}/hcp/${CASE}"
			Com20="rm ${SubjectsFolder}/${CASE}/hcp/${CASE}/${CASE}.${Modality}.${BOLD}.QC.wb.scene"
			Com21="mkdir -p ${SubjectsFolder}/${CASE}/hcp/${CASE}/qc &> /dev/null"
			Com22="cp ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.${TimeStamp}.zip ${SubjectsFolder}/${CASE}/hcp/${CASE}/qc/"
		fi
		
		# -- Combine all the calls into a single command
		if [ "$SceneZip" == "yes" ]; then
			ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com8; $Com9; $Com10; $Com11; $Com12; $Com13; $Com14; $Com15; $Com16; $Com17; $Com18; $Com19; $Com20; $Com21; $Com22"
		else
			ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com8; $Com9; $Com10; $Com11; $Com12; $Com13; $Com14; $Com15"
		fi
		
		# -- Clean up prior conflicting scripts, generate script and set permissions
		rm -f "$LogFolder"/${CASE}_ComQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh &> /dev/null
		echo "$ComQUEUE" >> "$LogFolder"/${CASE}_ComQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh
		chmod 770 "$LogFolder"/${CASE}_ComQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh
		
		# -- Run script
		"$LogFolder"/${CASE}_ComQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh |& tee -a "$LogFolder"/QC_"$CASE"_ComQUEUE_"$Modality"_"$TimeStamp".log
		
		# -- Check if Scene Zip file generated OK
		if [ "$SceneZip" == "yes" ]; then
			if [ -f ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.${TimeStamp}.zip ]; then
				echo ""
				echo "--- Scene zip file found and generated: "
				echo "    ${OutPath}/${CASE}.${Modality}.${BOLD}.QC.wb.${TimeStamp}.zip " 
				echo ""
			else
				echo ""
				reho "--- Scene zip generation for ${BOLD} failed. Check inputs."; echo ""
			fi
		fi
	done
	geho "--- QC Generation completed for ${Modality}. Check outputs and logs for errors."
	geho "---- Check output logs here: ${LogFolder}"
	echo ""
	geho "------------------------- End of work --------------------------------"
	echo ""
	return 0
fi
# -------------------------------------------
# -- End of BOLD QC Section
# -------------------------------------------

# --------------------------------------------------------------------------------
# -- Start of QC Section for remaining modalities 