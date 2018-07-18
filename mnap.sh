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
# * Grega Repovs , Department of Psychology,  University of Ljubljana
#
# ## PRODUCT
#
# * mnap.sh is a connector wrapper
#   developed as for front-end bash integration for the MNAP Suite
#
# ## LICENSE
#
# * The mnap.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
#
#~ND~END~

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= CODE START =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=

MNAPFunctions="matlabHelp gmriFunction organizeDicom mapHCPFiles createLists dataSync printMatrix BOLDDense linkmovement FIXICA postFIXICA BOLDHardLinkFIXICA FIXICAInsertMean FIXICARemoveMean hcpdLegacy eddyQC DWIDenseParcellation DWISeedTractography computeBOLDfc structuralParcellation BOLDParcellation ROIExtract FSLDtifit FSLBedpostxGPU autoPtx pretractographyDense probtrackxGPUDense AWSHCPSync QCPreproc MNAPXNATTurnkey commandExecute showVersion"

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

show_usage_matlabHelp() {
		echo ""
		echo ""
		echo "Complete listing of all MNAP-supported Matlab functions:"
		echo "--------------------------------------------------------"
		echo ""
		MatlabFunctions=`ls $TOOLS/$MNAPREPO/matlab/*/*.m | grep -v "archive/"`
		MatlabFunctionsfcMRI=`ls $TOOLS/$MNAPREPO/matlab/*/*.m | grep -v "archive/" | grep "/fcMRI/"`
		MatlabFunctionsGeneral=`ls $TOOLS/$MNAPREPO/matlab/*/*.m | grep -v "archive/" | grep "/general/"`
		MatlabFunctionsGMRI=`ls $TOOLS/$MNAPREPO/matlab/gmri/\@gmrimage/*.m`
		MatlabFunctionsStats=`ls $TOOLS/$MNAPREPO/matlab/*/*.m | grep -v "archive/" | grep "stats"`
		echo "  * Functional connectivity tools"; echo ""
		for MatlabFunction in $MatlabFunctionsfcMRI; do
			echo "      ==> $MatlabFunction";
		done
		echo ""
		echo "  * General image manipulation tools"; echo ""
		for MatlabFunction in $MatlabFunctionsGeneral; do
			echo "      ==> $MatlabFunction";
		done
		echo ""
		echo "  * Specific image analyses tools"; echo ""
		for MatlabFunction in $MatlabFunctionsGMRI; do
			echo "      ==> $MatlabFunction";
		done
		echo ""
		echo "  * Statistical tools"; echo ""
		for MatlabFunction in $MatlabFunctionsStats; do
			echo "      ==> $MatlabFunction";
		done
		echo ""
}

show_usage() {
geho ""
geho "                  ███╗   ███╗███╗   ██╗ █████╗ ██████╗                       "
geho "                  ████╗ ████║████╗  ██║██╔══██╗██╔══██╗                      "
geho "                  ██╔████╔██║██╔██╗ ██║███████║██████╔╝                      "
geho "                  ██║╚██╔╝██║██║╚██╗██║██╔══██║██╔═══╝                       "
geho "                  ██║ ╚═╝ ██║██║ ╚████║██║  ██║██║                           "
geho "                  ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝                           "
echo ""
geho "                                LICENSE:                                     "
geho " Use of this software is subject to the terms and conditions defined by the  "
geho " Yale University Copyright Policies:                                         "
geho "    http://ocr.yale.edu/faculty/policies/yale-university-copyright-policy    "
geho " and the terms and conditions defined in the file 'LICENSE.md' which is      "
geho " a part of this source code package."
echo ""
echo ""
echo "                             General Usage                                    "
echo " ---------------------------------------------------------------------------- "
echo ""
echo "  Usage:"
echo ""
echo "    mnap --function=<function_name> \ "
echo "         --subjectsfolder=<folder_with_subjects> \ "
echo "         --subjects='<comma_separarated_list_of_cases>' \ "
echo "         --extraflags=<extra_inputs> "
echo ""
echo "  Example:"
echo ""
echo "    mnap --function='organizeDicom' \ "
echo "         --subjectsfolder='<folder_with_subjects>' \ "
echo "         --subjects='<case_id1>,<case_id2>'"
echo ""
echo "  Specific function help:"
echo ""
echo "         mnap -<function_name>   "
echo "    OR   mnap ?<function_name>   "
echo "    OR   mnap <function_name>    "
echo ""
echo "............................................................................"
echo ""
echo "Note the following conventions used in help and documentation:"
echo ""
echo "    * Square brackets []: Specify a value that is optional."
echo "       Note: Value within brackets is the default value."
echo ""
echo "    * Angle brackets <>: Contents describe what should go there."
echo ""
echo "    * Dashes or flags -- : Define input variables."
echo ""
echo "    * All descriptions use regular case and all options use CAPS"
echo ""
echo "............................................................................"
echo ""
echo "                         Specific Functions                                  "
echo " ----------------------------------------------------------------------------"
echo ""
echo "Initial data organization functions"
echo "----------------------------"
echo " createStudy ...... generate study folder hierarchy per MNAP specification"
echo " organizeDicom ...... sort DICOMs and setup nifti files from DICOMs"
echo " mapHCPFiles ...... setup data structure for hcp processing"
echo " createList ...... setup subject lists for analyses" 
echo " createConc ...... setup conc files for analyses" 
echo " compileBatch ...... setup batch files for processing or analyses" 
echo " dataSync ...... sync/backup data across hpc cluster(s)"
echo " MNAPXNATTurnkey ...... turnkey execution of MNAP workflow via XNAT Docker engine"
echo ""
echo "QC functions"
echo "------------"
echo " eddyQC ...... run quality control on diffusion datasets following eddy outputs"
echo " QCPreproc ...... run visual qc for a given modality (t1w,tw2,myelin,bold,dwi)"
echo ""
echo "DWI processing, analyses & probabilistic tractography functions"
echo "----------------------------------------------------------------"
echo " hcpdLegacy ...... diffusion image processing for data with or without standard fieldmaps"
echo " FSLDtifit ...... run FSL's dtifit tool (cluster usable)"
echo " FSLBedpostxGPU ...... run fsl bedpostx w/gpu"
echo " pretractographyDense ...... generates space for whole-brain dense connectomes"
echo " probtrackxGPUDense ...... run FSL's probtrackx for whole brain & generates dense "
echo "                          whole brain connectomes"
echo ""
echo "Misc. functions and analyses"
echo "---------------------------"
echo " computeBOLDfc ...... computes seed or GBC BOLD functional connectivity"
echo " structuralParcellation ...... parcellate myelin or thickness"
echo " BOLDParcellation ...... parcellate BOLD data and generate pconn files"
echo " DWIDenseParcellation ...... parcellate dense dwi tractography data"
echo " DWISeedTractography ...... reduce dense DWI tractography data using a seed structure"
echo " printMatrix ...... extract parcellated matrix for dense CIFTI data using a network solution"
echo " BOLDDense ...... compute bold dense connectome (needs >30gb ram per bold)"
echo " CIFTISmooth ...... smooth CIFTI data"
echo " ROIExtract ...... extract data from pre-specified ROIs in CIFTI or NIFTI"
echo " AWSHCPSync ...... sync hcp data from aws s3 cloud"
echo ""
echo "FIX ICA de-noising functions"
echo "---------------------------"
echo " FIXICA ...... run FIX ICA de-noising on a given volume"
echo " postFIXICA ...... generates Workbench scenes for each subject directory"
echo " BOLDHardLinkFIXICA ...... setup hard links for single run FIX ICA results"
echo " FIXICAInsertMean ...... re-insert mean image back into mapped FIX ICA data"
echo " FIXICARemoveMean ...... remove mean image from mapped FIX ICA data"
echo " BOLDSeparateCIFTIFIXICA ...... separate specified bold timeseries (use if BOLDs merged)"
echo " BOLDHardLinkFIXICAMerged ...... setup sym links for merged FIX ICA results (use if BOLDs merged)"
echo ""
echo ""
echo "             General MRI Utilities for Preprocessing and Analyses          "
echo "---------------------------------------------------------------------------"
echo ""
echo " MNAP Suite workflows contain additional python-based 'general mri (gmri) utilities."
echo " These are accessed either directly via 'gmri' command from the terminal."
echo " Alternatively the 'mnap' connector wrapper parses all functions via "
echo " 'gmri' package as standard input."
echo ""
echo "	Example to pass function:                mnap <function_name> [options]"
echo "	Example to request help for function:    mnap ?<function_name>"
echo ""
echo "`gmri`"
echo "`gmri -l`"
echo ""
echo ""
echo " All supported MNAP stand-alone Matlab Tools "
echo "============================================"
echo ""
echo " ==> Matlab tools are located in: $TOOLS/$MNAPREPO/matlab"
echo ""
echo " The MNAP package contain a number of matlab-based stand-alone tools."
echo " These tools are used across various MNAP packages, but can be accessed"
echo " as stand-alone functions within Matlab. Help and documentation is"
echo " embedded within each stand-alone tool via standard Matlab help call."
echo ""
echo "To obtain a full listing of all MNAP-supported Matlab tools run: "
echo "   'mnap matlabHelp' "
echo ""
}

# ========================================================================================
# ===================== SPECIFIC FUNCTIONS START HERE ====================================
# ========================================================================================

# ------------------------------------------------------------------------------------------------------
#  gmri general wrapper - parse inputs into specific gmri functions via AP
# ------------------------------------------------------------------------------------------------------

gmriFunction() {
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

show_help_gmri() {
		echo ""
		gmri
		echo ""
}
show_options_gmri() {
		echo ""
		gmri -o
		echo ""
}
show_commands_gmri() {
		echo ""
		gmri -l
		echo ""
}
show_processing_gmri() {
		echo ""
		gmri -c
		echo ""
}

# ---------------------------------------------------------------------------------------------------------------
#  -- Master Execution and Logging function -- https://bitbucket.org/hidradev/mnaptools/wiki/Overview/Logging.md
# ---------------------------------------------------------------------------------------------------------------

connectorExec() {
# -- Set the time stamp for given job
TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
cd ${MasterRunLogFolder}
Platform="Platform Information: `uname -a`"

# -- Define specific logs
#
# -- Runlog
#    Specification: Log-<command name>-<date>_<hour>.<minute>.<microsecond>.log
#    Example:       Log-mapHCPData-2017-11-11_15.58.1510433930.log
#
Runlog="${MasterRunLogFolder}/Log-${FunctionToRun}_${TimeStamp}.log"

# -- Comlog
#    Specification:  tmp_<command_name>[_B<N>]_<subject code>_<date>_<hour>.<minute>.<microsecond>.log
#    Specification:  error_<command_name>[_B<N>]_<subject code>_<date>_<hour>.<minute>.<microsecond>.log
#    Specification:  done_<command_name>[_B<N>]_<subject code>_<date>_<hour>.<minute>.<microsecond>.log
#    Example:        done_ComputeBOLDStats_pb0986_2017-05-06_16.16.1494101784.log
#
ComlogTmp="${MasterComlogFolder}/tmp_${FunctionToRun}_${CASE}_${TimeStamp}.log"; touch ${ComlogTmp}
ComRun="${MasterComlogFolder}/Run_${FunctionToRun}_${CASE}_${TimeStamp}.sh"; touch ${ComRun}
ComlogError="${MasterComlogFolder}/error_${FunctionToRun}_${CASE}_${TimeStamp}.log"
ComlogDone="${MasterComlogFolder}/done_${FunctionToRun}_${CASE}_${TimeStamp}.log"
CompletionCheck="${MasterComlogFolder}/Completion_${FunctionToRun}_${TimeStamp}.Check"

# -- Batchlog
#    <batch system>_<command name>_job<job number>.<date>_<hour>.<minute>.<microsecond>.log
ComRunSet="cd ${MasterRunLogFolder}; echo ${CommandToRun} >> ${Runlog}; echo ${CommandToRun} >> ${ComRun}; chmod 770 ${ComRun}"
ComRunExec="${ComRun} 2>&1 | tee -a ${ComlogTmp}"
ComComplete="cat ${ComlogTmp} | grep 'Successful' &> ${CompletionCheck}"
ComRunCheck="if [[ -s ${CompletionCheck} ]]; then mv ${ComlogTmp} ${ComlogDone}; echo '--- DONE. Check final log output:'; echo ''; echo '${ComlogDone}'; echo ''; rm ${CompletionCheck}; else mv ${ComlogTmp} ${ComlogError}; echo '--- ERROR. Check error log output:'; echo ''; echo '${ComlogError}'; echo ''; rm ${CompletionCheck}; fi"
ComRunAll="${ComRunSet}; ${ComRunExec}; ${ComComplete}; ${ComRunCheck}"

# -- Run the local commands
if [[ "$Cluster" == 1 ]]; then
	echo "--------------------------------------------------------------"
	echo ""
	geho "   Running ${FunctionToRun} locally on `hostname`"
	geho "   Command log:     ${Runlog}  "
	geho "   Function output: ${ComlogTmp} "
	echo ""
	eval ${ComRunAll}
fi
# -- Run the scheduler commands
if [[ "$Cluster" == 2 ]]; then
	cd ${MasterRunLogFolder}
	gmri schedule command="${ComRunAll}" settings="${Scheduler}"
	echo "---------------------------------------------------------------------------------"
	echo ""
	geho "   Data successfully submitted to scheduler"
	geho "   Scheduler details: ${Scheduler}"
	geho "   Command log:     ${Runlog}  "
	geho "   Function output: ${ComlogTmp} "
	echo ""
fi
}

# ---------------------------------------------------------------------------------------------------------------
#  MNAPXNATTurnkey - Turnkey execution of MNAP workflow via the XNAT docker engine
# ---------------------------------------------------------------------------------------------------------------

MNAPXNATTurnkey() {
# -- Echo command
geho "Full command:"
echo "${TOOLS}/${MNAPREPO}/connector/MNAP_XNAT_Turnkey.sh \
--batchfile="${BATCH_PARAMETERS_FILENAME}" \
--overwrite="${overwrite}" \
--mappingfile="${SCAN_MAPPING_FILENAME}" \
--xnatsessionlabel="${XNAT_SESSION_LABEL}" \
--xnatprojectid="${XNAT_PROJECT_ID}" \
--xnathost="${XNAT_HOST_NAME}" \
--xnatuser="${XNAT_USER_NAME}" \
--xnatpass="${XNAT_PASSWORD}""
echo ""
# -- Specify command variable
CommandToRun=". ${TOOLS}/${MNAPREPO}/connector/MNAP_XNAT_Turnkey.sh \
--batchfile="${BATCH_PARAMETERS_FILENAME}" \
--overwrite="${overwrite}" \
--mappingfile="${SCAN_MAPPING_FILENAME}" \
--xnatsessionlabel="${XNAT_SESSION_LABEL}" \
--xnatprojectid="${XNAT_PROJECT_ID}" \
--xnathost="${XNAT_HOST_NAME}" \
--xnatuser="${XNAT_USER_NAME}" \
--xnatpass="${XNAT_PASSWORD}""
# -- Connector execute function
connectorExec
}
show_usage_MNAPXNATTurnkey() {
. ${TOOLS}/${MNAPREPO}/connector/functions/MNAP_XNAT_Turnkey.sh
}

# ---------------------------------------------------------------------------------------------------------------
#  organizeDicom - Sort original DICOMs into folders and generates NIFTI files using sortDicom and dicom2niix
# ---------------------------------------------------------------------------------------------------------------

organizeDicom() {
# -- Note:
#    This function passes parameters into two NIUtilities commands: sortDicom and dicom2niix
mkdir ${SubjectsFolder}/${CASE}/dicom &> /dev/null
if [ "$Overwrite" == "yes" ]; then
	reho "===> Removing prior DICOM run"
	rm -f ${SubjectsFolder}/${CASE}/dicom/DICOM-Report.txt &> /dev/null
fi
echo ""
reho "===> Checking for presence of ${SubjectsFolder}/${CASE}/dicom/DICOM-Report.txt"
echo ""

if (test -f ${SubjectsFolder}/${CASE}/dicom/DICOM-Report.txt); then
	echo ""
	geho "--- Found ${SubjectsFolder}/${CASE}/dicom/DICOM-Report.txt"
	geho "    Note: To re-run set --overwrite='yes'"
	echo ""
	geho " ... $CASE ---> organizeDicom done"
	echo ""
else
	echo "--- Did not find ${SubjectsFolder}/${CASE}/dicom/DICOM-Report.txt"
	echo ""
	# -- Combine all the calls into a single command
	Com1="cd ${SubjectsFolder}/${CASE}"
	echo " ---> running sortDicom and dicom2nii for $CASE"
	echo ""
	Com2="gmri sortDicom"
	Com3="gmri dicom2niix unzip=${Unzip} gzip=${Gzip} clean=${Clean} verbose=${VerboseRun} cores=${Cores} subjectid=${CASE}"
	ComQUEUE="$Com1; $Com2; $Com3"
	# -- Set the time stamp for job
	TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
	Suffix="${CASE}-${TimeStamp}"
	# -- Set the scheduler commands
	rm -f ${SubjectsFolder}/${CASE}/dicom/ComQUEUE_organizeDicom_"$Suffix".sh &> /dev/null
	echo "$ComQUEUE" >> ${SubjectsFolder}/${CASE}/dicom/ComQUEUE_organizeDicom_"$Suffix".sh
	chmod 770 ${SubjectsFolder}/${CASE}/dicom/ComQUEUE_organizeDicom_"$Suffix".sh
	# -- Check if job is set to local (1) or cluster run (2)
	if [ "$Cluster" == 1 ]; then
		echo ""
		echo "---------------------------------------------------------------------------------"
		echo "Running ${FunctionToRun} locally on `hostname`"
		echo "Check command log here: ${MasterRunLogFolder}"
		echo "Check output log here: ${MasterComLogFolder}"
		echo "---------------------------------------------------------------------------------"
		echo ""
		${SubjectsFolder}/${CASE}/dicom/ComQUEUE_organizeDicom_"$Suffix".sh 2>&1 | tee -a ${SubjectsFolder}/${CASE}/dicom/organizeDicom-${Suffix}.log
		# --> This fails on some OS |& versions due to BASH version incompatiblity - need to use full expansion 2>&1 | : 
		#${SubjectsFolder}/${CASE}/dicom/ComQUEUE_organizeDicom_"$Suffix".sh |& tee -a ${SubjectsFolder}/${CASE}/dicom/organizeDicom-${Suffix}.log
	else
		echo "Job ID:"
		# -- Run the scheduler commands
		cd ${SubjectsFolder}/${CASE}/dicom/
		gmri schedule command="${SubjectsFolder}/${CASE}/dicom/ComQUEUE_organizeDicom_${Suffix}.sh" \
		settings="${Scheduler}" output="stdout:${SubjectsFolder}/${CASE}/dicom/organizeDicom.${Suffix}.output.log|stderr:${SubjectsFolder}/${CASE}/dicom/organizeDicom.${Suffix}.error.log" \
		workdir="${SubjectsFolder}/${CASE}/dicom"
		echo ""
		echo "---------------------------------------------------------------------------------"
		echo "Data successfully submitted"
		echo "Scheduler: $Scheduler"
		echo "Check output logs here: ${SubjectsFolder}/${CASE}/dicom"
		echo "---------------------------------------------------------------------------------"
		echo ""
	fi
fi
}
show_usage_organizeDicom() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function expects a set of raw DICOMs in <study_folder>/<case>/inbox."
echo "DICOMs are organized, gzipped and converted to NIFTI format for additional processing."
echo "subject.txt files will be generated with id and subject matching the <case>."
echo ""
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                             Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>                Path to study folder that contains subjects. If missing then optional paramater --folder needs to be provided."
echo "--subjects=<comma_separated_list_of_cases>             List of subjects to run. If missing then --folder needs to be provided for a single-session run."
echo "--scheduler=<name_of_cluster_scheduler_and_options>    A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo "                                                       e.g. for SLURM the string would look like this: "
echo "                                                       --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
echo ""
echo "-- OPTIONAL PARAMETERS: "
echo ""
echo "--folder=<folder_with_subjects>       The base subject folder with the dicom subfolder that holds session numbered folders with dicom files. [.]"
echo "--overwrite=<re-run_organizeDicom>    Explicitly force a re-run of organizeDicom"
echo "--clean=<clean_NIfTI_files>           Whether to remove preexisting NIfTI files (yes), leave them and abort (no) or ask interactively (ask). [ask]"
echo "--overwrite=<re-run_organizeDicom>    Explicitly force a re-run of organizeDicom"
echo "--unzip=<unzip_dicoms>                If the dicom files are gziped whether to unzip them (yes), leave them be and abort (no) or ask interactively (ask). [ask]"
echo "--gzip=<zip_dicoms>                   After the dicom files were processed whether to gzip them (yes), leave them ungzipped (no) or ask interactively (ask). [ask]"
echo "--verbose=<print_verbose_output>      Whether to be report on the progress (True) or not (False). [True]"
echo "--cores=<number_of_cores>             How many parallel processes to run dcm2nii conversion with. "
echo "                                      The number is one by defaults, if specified as 'all', the number of available cores is utilized."
echo ""
echo ""
echo "-- Example with flagged parameters for a local run:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='organizeDicom' \ "
echo "--subjects='<comma_separarated_list_of_cases>' "
echo ""
echo "-- Example with flagged parameters for submission to the scheduler:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='organizeDicom' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--scheduler='<name_of_scheduler_and_options>'"
echo ""
echo ""
}

# ------------------------------------------------------------------------------------------------------
#  mapHCPFiles - Setup the HCP File Structure to be fed to the Yale HCP
# ------------------------------------------------------------------------------------------------------

mapHCPFiles() {
cd ${SubjectsFolder}/${CASE}
echo "--> running mapHCPFiles for $CASE"
echo ""
# -- Combine all the calls into a single command
Com1="cd ${SubjectsFolder}/${CASE}"
Com2="gmri setupHCP"
ComQUEUE="$Com1; $Com2"
# -- Generate timestamp for logs and scripts
TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
Suffix="${CASE}-${TimeStamp}"
# -- Set the scheduler commands
rm -f ${SubjectsFolder}/${CASE}/mapHCPFiles_${Suffix}.sh &> /dev/null
echo "$ComQUEUE" >> ${SubjectsFolder}/${CASE}/mapHCPFiles_${Suffix}.sh
chmod 770 ${SubjectsFolder}/${CASE}/mapHCPFiles_${Suffix}.sh
if [ "$Cluster" == 1 ]; then
	echo ""
	echo "---------------------------------------------------------------------------------"
	echo "Running mapHCPFiles locally on `hostname`"
	echo "Check output here: ${SubjectsFolder}/${CASE}/hcp "
	echo "---------------------------------------------------------------------------------"
	echo "" 
	${SubjectsFolder}/${CASE}/mapHCPFiles_${Suffix}.sh 2>&1 | tee -a ${SubjectsFolder}/${CASE}/mapHCPFiles-${Suffix}.log
	# --> This fails on some OS |& versions due to BASH version incompatiblity - need to use full expansion 2>&1 | : 
	# ${SubjectsFolder}/${CASE}/mapHCPFiles_${Suffix}.sh |& tee -a ${SubjectsFolder}/${CASE}/mapHCPFiles.${Suffix}.log
else
	echo "Job ID:"
	# -- Run the scheduler commands
	cd ${SubjectsFolder}/${CASE}/
	gmri schedule command="${SubjectsFolder}/${CASE}/mapHCPFiles_${Suffix}.sh" \
	settings="${Scheduler}" \
	output="stdout:${SubjectsFolder}/${CASE}/mapHCPFiles.${Suffix}.output.log|stderr:${SubjectsFolder}/${CASE}/mapHCPFiles.${Suffix}.error.log"  \
	workdir="${SubjectsFolder}/${CASE}"
	echo ""
	echo "---------------------------------------------------------------------------------"
	echo "Data successfully submitted"
	echo "Scheduler Name and Options: $Scheduler"
	echo "Check output logs here: ${SubjectsFolder}/${CASE}/"
	echo "---------------------------------------------------------------------------------"
	echo ""
fi
}
show_usage_mapHCPFiles() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function maps the Human Connectome Project folder structure for preprocessing."
echo "It should be executed after proper organizeDicom and subject.txt file has been vetted"
echo "and the subject_hcp.txt file was generated."
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                             Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>                Path to study folder that contains subjects"
echo "--subjects=<comma_separated_list_of_cases>             List of subjects to run"
echo "--scheduler=<name_of_cluster_scheduler_and_options>    A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo "                                                       e.g. for SLURM the string would look like this: "
echo "                                                       --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
echo ""
echo "-- Example with flagged parameters for a local run:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='mapHCPFiles' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo ""
echo "-- Example with flagged parameters for submission to the scheduler:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='mapHCPFiles' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--scheduler='<name_of_cluster_scheduler_and_options>' \ "
echo ""
echo ""
}

# ------------------------------------------------------------------------------------------------------
#  createLists - Generate batch processing & analysis lists
# ------------------------------------------------------------------------------------------------------

createLists() {
if [ "$ListGenerate" == "batch" ]; then
	# -- Check if appending list
	if [ "$Append" == "yes" ]; then
		# -- If append was set to yes and file exists then clear header
		HeaderBatch="no"
		echo ""
		geho "---------------------------------------------------------------------"
		geho "--> You are appending the batch header file with $CASE               "
		geho "--> --headerbatch is now set to 'no'                                 "
		geho "--> Check usage to overwrite the file                                "
		geho "---------------------------------------------------------------------"
		echo ""
	else
		echo ""
		geho "---------------------------------------------------------------------"
		geho "--> Generaring new batch file with specified header for $CASE        "
		geho "---------------------------------------------------------------------"
		echo ""
	fi
	echo "Running locally on `hostname`"
	echo "Check log file output here: $LogFolder"
	echo "--------------------------------------------------------------"
	echo ""
	${ListFunction} \
	--subjectsfolder="${SubjectsFolder}" \
	--subjects="${CASE}" \
	--outname="${ListName}" \
	--outpath="${ListPath}"
	echo ""
fi
if [ "$ListGenerate" == "analysis" ]; then
	unset HeaderBatch
	unset Append
	echo ""
	geho "---------------------------------------------------------------------"
	geho "--> Generaring analysis list files for $CASE... "
	geho "--> Check output here: ${SubjectsFolder}/lists... "
	geho "---------------------------------------------------------------------"
	echo ""
	source "$ListFunction"
fi
}

show_usage_createLists() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function generates a lists for processing or analyses for multiple subjects."
echo "The function supports generation of batch parameter files for HCP processing for either 'legacy' of multiband data."
echo ""
echo "Supported lists:"
echo ""
echo "    * batch    --> Subject parameter list with cases to preprocess"
echo "    * analysis --> List of cases to compute seed connectivity or GBC"
echo "    * snr      --> List of cases to compute signal-to-noise ratio [DEPRECATED for QCPreproc]"
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                  Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>     Path to study folder that contains subjects"
echo "--subjects=<comma_separated_list_of_cases>  List of subjects to run"
echo "--listtocreate=<type_of_list_to_generate>   Type of list to generate (e.g. batch). "
echo "--listname=<output_name_of_the_list>        Output name of the list to generate. "
echo "                                            Supported: batch, analysis, snr "
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
echo "--headerbatch=<header_file_for_the_batch_file>  Set header for the batch file."
echo ""
echo "    * Default:"
echo ""
echo "`ls ${TOOLS}/${MNAPREPO}/connector/functions/subjectparamlist_header_multiband.txt`"
echo ""
echo "    * Supported: "
echo ""
echo "`ls ${TOOLS}/${MNAPREPO}/connector/functions/subjectparamlist_header*` "
echo ""
echo "    * Note: If --headerbatch set to <no> then function will not add a header"
echo ""
echo "--listfunction=<function_used_to_create_list>   Point to external function to use"
echo "--bolddata=<comma_separated_list_of_bolds>      List of BOLD files to append to analysis or snr lists"
echo "--parcellationfile=<file_for_parcellation>      Specify the absolute file path for parcellation in $TOOLS/$MNAPREPO/connector/templates/Parcellations/ "
echo "--filetype=<file_extension>                     Extension for BOLDs in the analysis (e.g. _Atlas). Default empty []"
echo "--boldsuffix=<comma_separated_bold_suffix>      List of BOLDs to iterate over in the analysis list"
echo ""
echo "-- Example with flagged parameters:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='createLists' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--listtocreate='batch' \ "
echo "--overwrite='yes' \ "
echo "--listname='<list_to_generate>' \ "
echo "--headerbatch='no' \ "
echo "--append='yes' "
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='createLists' \ "
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
#  dataSync - Sync files to Yale HPC and back to the Yale server after HCP preprocessing
# ------------------------------------------------------------------------------------------------------

dataSync() {
	# -- Command to run
	CommandToRun="DataSync.sh \
	--syncfolders="${SyncFolders}" \
	--subjects="${CASE}" \
	--syncserver="${SyncServer}" \
	--synclogfolder="${SyncLogFolder}" \
	--syncdestination="${SyncDestination}""
	# -- Connector execute function
	connectorExec
}

show_usage_dataSync() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo "  This function runs rsync across the entire folder structure based on user specifications"
echo ""
echo "  * Mandatory Inputs:"
echo ""
echo "   --syncfolders=<path_to_folders>         Set path for folders that contains studies for syncing"
echo "   --syncserver=<sync_server>              Set sync server <UserName@some.server.address> or 'local' to sync locally"
echo "   --syncdestination=<destination_path>    Set sync destination path"
echo "   --synclogfolder=<path_to_log_folder>        Set log folder"
echo ""
echo "  * Optional Inputs:"
echo ""
echo "   --subjects=<lists_specific_subjects>      Set input subjects for backup. "
echo "                                             If set, then --backupfolders path has to contain input subjects."
echo ""
echo "* EXAMPLE:"
echo ""
echo "mnap --function=dataSync \ "
echo "--syncfolders=<path_to_folders> \ "
echo "--syncserver=<sync_server> \ "
echo "--syncdestination=<destination_path> \ "
echo "--synclogfolder=<path_to_log_folder>  \ "
echo ""
}

# ------------------------------------------------------------------------------------------------------
#  printMatrix - Extract matrix data from parcellated files (BOLD)
# ------------------------------------------------------------------------------------------------------

printMatrix() {
# -- Bold data
if [ "$DatatoPrint" == "bold" ]; then
	for STEP in $STEPS; do
			for BOLD in $BOLDS; do
				if [ -f ${SubjectsFolder}/../Parcellated/BOLD/${CASE}_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.csv ]; then
					echo "Matrix printing done for $CASE run $BOLD and $STEP. Skipping to next subject..."
				else
					echo "Printing parcellated data on BOLD data for $CASE..."
					wb_command -nifti-information -print-matrix ${SubjectsFolder}/../Parcellated/BOLD/${CASE}_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.pconn.nii > ${CASE}_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_networks.32k_fs_LR.csv
					wb_command -nifti-information -print-matrix ${SubjectsFolder}/../Parcellated/BOLD/${CASE}_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.pconn.nii > ${CASE}_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_networks.32k_fs_LR.csv
					wb_command -nifti-information -print-matrix ${SubjectsFolder}/../Parcellated/BOLD/${CASE}_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.pconn.nii > ${CASE}_bold"$BOLD"_"$STEP"_LR_RSN_CSC_7Networks_islands.32k_fs_LR.csv
					wb_command -nifti-information -print-matrix ${SubjectsFolder}/../Parcellated/BOLD/${CASE}_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.pconn.nii > ${CASE}_bold"$BOLD"_"$STEP"_LR_RSN_CSC_17Networks_islands.32k_fs_LR.csv
				fi
			done
	done
fi
}
show_usage_printMatrix() {
echo""
echo"--DESCRIPTION for $UsageInput"
echo""
echo"  USAGE INFO PENDING..."
echo""
echo""
}

# ------------------------------------------------------------------------------------------------------
#  BOLDDense - Compute the dense connectome file for BOLD timeseries
# ------------------------------------------------------------------------------------------------------

BOLDDense() {
for STEP in $STEPS; do
	for BOLD in $BOLDS; do
		if [ -f ${SubjectsFolder}/${CASE}/images/functional/bold"$BOLD"_"$STEP".dconn.nii ]; then
			echo "Dense Connectome Computed for this for $CASE and $STEP. Skipping to next..."
		else
			echo "Running Dense Connectome on BOLD data for $CASE... (need ~30GB free RAM at any one time per subject)"
			# -- Dense connectome command - use in isolation due to RAM limits (need ~30GB free at any one time per subject)
			wb_command -cifti-correlation ${SubjectsFolder}/${CASE}/images/functional/bold"$BOLD"_"$STEP".dtseries.nii ${SubjectsFolder}/${CASE}/images/functional/bold"$BOLD"_"$STEP".dconn.nii -fisher-z -weights ${SubjectsFolder}/${CASE}/images/functional/movement/bold"$BOLD".use
			ln -f ${SubjectsFolder}/${CASE}/images/functional/bold"$BOLD"_"$STEP".dconn.nii ${SubjectsFolder}/../Parcellated/BOLD/${CASE}_bold"$BOLD"_"$STEP".dconn.nii
		fi
	done
done
}
show_usage_BOLDDense(){
echo""
echo"--DESCRIPTIONfor$UsageInput"
echo""
echo"  USAGE INFO PENDING..."
echo""
}

# ------------------------------------------------------------------------------------------------------
# ----------------------------------------- FIX ICA CODE -----------------------------------------------
# ------------------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------------
#  linkMovement - Sets hard links for BOLDs into Parcellated folder for FIXICA use
# ------------------------------------------------------------------------------------------------------

linkMovement() {
for BOLD in $BOLDS; do
	echo "Linking scrubbing data - BOLD $BOLD for $CASE..."
	ln -f ${SubjectsFolder}/${CASE}/images/functional/movement/bold"$BOLD".use ${SubjectsFolder}/../Parcellated/BOLD/${CASE}_bold"$BOLD".use
	ln -f ${SubjectsFolder}/${CASE}/images/functional/movement/boldFIXICA"$BOLD".use ${SubjectsFolder}/../Parcellated/BOLD/${CASE}_boldFIXICA"$BOLD".use
done
}
show_usage_linkMovement() {
echo""
echo"--DESCRIPTIONfor$UsageInput"
echo""
echo"  USAGE INFO PENDING..."
echo""
}

# ------------------------------------------------------------------------------------------------------
#  FIXICA - Compute FIX ICA cleanup on BOLD timeseries following hcp pipelines
# ------------------------------------------------------------------------------------------------------

FIXICA() {
for BOLD in $BOLDS; do
		if [ "$Overwrite" == "yes" ]; then
			rm -r ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD"*_hp2000*  &> /dev/null
		fi
		if [ -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas_hp2000_clean.dtseries.nii ]; then
				echo "FIX ICA Computed for this for $CASE and $BOLD. Skipping to next..."
		else
				echo "Running FIX ICA on $BOLD data for $CASE... (note: this uses Melodic which is a slow single-threaded process)"
				rm -r *hp2000* &> /dev/null
				"$FIXICADIR"/hcp_fix.sh ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD".nii.gz 2000
		fi
done
}
show_usage_FIXICA() {
echo""
echo"--DESCRIPTIONfor$UsageInput"
echo""
echo"  USAGE INFO PENDING..."
echo""
}

# ------------------------------------------------------------------------------------------------------
#  postFIXICA - Compute PostFix code on FIX ICA cleaned BOLD timeseries to generate scene files
# ------------------------------------------------------------------------------------------------------

postFIXICA() {
for BOLD in $BOLDS; do
	if [ "$Overwrite" == "yes" ]; then
			rm -r ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/${CASE}_"$BOLD"_ICA_Classification_singlescreen.scene   &> /dev/null
		fi
		if [ -f  ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/${CASE}_"$BOLD"_ICA_Classification_singlescreen.scene ]; then
				echo "PostFix Computed for this for $CASE and $BOLD. Skipping to next..."
	else
				echo "Running PostFix script on $BOLD data for $CASE... "
				"$POSTFIXICADIR"/GitRepo/PostFix.sh ${SubjectsFolder}/${CASE}/hcp ${CASE} "$BOLD" /usr/local/PostFix_beta/GitRepo "$HighPass" wb_command /usr/local/PostFix_beta/GitRepo/PostFixScenes/ICA_Classification_DualScreenTemplate.scene /usr/local/PostFix_beta/GitRepo/PostFixScenes/ICA_Classification_SingleScreenTemplate.scene
	fi
done
}
show_usage_postFIXICA() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "   USAGE INFO PENDING ... "
echo ""
}

# ------------------------------------------------------------------------------------------------------
#  BOLDHardLinkFIXICA - Generate links for FIX ICA cleaned BOLDs for functional connectivity (dofcMRI)
# ------------------------------------------------------------------------------------------------------

BOLDHardLinkFIXICA() {
BOLDCount=0
for BOLD in $BOLDS
	do
		BOLDCount=$((BOLDCount+1))
		echo "Setting up hard links following FIX ICA for BOLD# $BOLD for $CASE... "
		# -- Setup folder strucrture if missing
		mkdir ${SubjectsFolder}/${CASE}/images    &> /dev/null
		mkdir ${SubjectsFolder}/${CASE}/images/functional	    &> /dev/null
		mkdir ${SubjectsFolder}/${CASE}/images/functional/movement    &> /dev/null
		# -- Setup hard links for images
		rm ${SubjectsFolder}/${CASE}/images/functional/boldFIXICA"$BOLD".dtseries.nii     &> /dev/null
		rm ${SubjectsFolder}/${CASE}/images/functional/boldFIXICA"$BOLD".nii.gz     &> /dev/null
		ln -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas_hp2000_clean.dtseries.nii ${SubjectsFolder}/${CASE}/images/functional/boldFIXICA"$BOLD".dtseries.nii
		ln -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD"_hp2000_clean.nii.gz ${SubjectsFolder}/${CASE}/images/functional/boldFIXICA"$BOLD".nii.gz
		ln -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas.dtseries.nii ${SubjectsFolder}/${CASE}/images/functional/bold"$BOLD".dtseries.nii
		ln -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD".nii.gz ${SubjectsFolder}/${CASE}/images/functional/bold"$BOLD".nii.gz
		#rm ${SubjectsFolder}/${CASE}/images/functional/boldFIXICArfMRI_REST*     &> /dev/null
		#rm ${SubjectsFolder}/${CASE}/images/functional/boldrfMRI_REST*     &> /dev/null
		echo "Setting up hard links for movement data for BOLD# $BOLD for $CASE... "
		# -- Clean up movement regressor file to match dofcMRIp convention and copy to movement directory
		export PATH=/usr/local/opt/gnu-sed/libexec/gnubin:$PATH     &> /dev/null
		rm ${SubjectsFolder}/${CASE}/images/functional/movement/boldFIXICA"$BOLD"_mov.dat     &> /dev/null
		rm ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit*     &> /dev/null
		cp ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors.txt ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit.txt
		sed -i.bak -E 's/.{67}$//' ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit.txt
		nl ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit.txt > ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit_fin.txt
		sed -i.bak '1i\#frame     dx(mm)     dy(mm)     dz(mm)     X(deg)     Y(deg)     Z(deg)' ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"//Movement_Regressors_edit_fin.txt
		cp ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit_fin.txt ${SubjectsFolder}/${CASE}/images/functional/movement/boldFIXICA"$BOLD"_mov.dat
		rm ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit*     &> /dev/null
done
}
show_usage_BOLDHardLinkFIXICA() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "Function for hard-linking minimally preprocessed HCP BOLD images after FIX ICA was done for further denoising."
echo ""
}

# ------------------------------------------------------------------------------------------------------
#  FIXICAInsertMean - Re-insert means into FIX ICA cleaned BOLDs for connectivity preprocessing (dofcMRI)
# ------------------------------------------------------------------------------------------------------

FIXICAInsertMean() {
for BOLD in $BOLDS; do
	cd ${SubjectsFolder}/${CASE}/images/functional/
	# -- First check if the boldFIXICA file has the mean inserted
	3dBrickStat -mean -non-zero boldFIXICA"$BOLD".nii.gz[1] >> boldFIXICA"$BOLD"_mean.txt
	ImgMean=`cat boldFIXICA"$BOLD"_mean.txt`
	if [ $(echo " $ImgMean > 1000" | bc) -eq 1 ]; then
	echo "1st frame mean=$ImgMean Mean inserted OK for subject $CASE and bold# $BOLD. Skipping to next..."
		else
		# -- Next check if the boldFIXICA file has the mean inserted twice by accident
		if [ $(echo " $ImgMean > 15000" | bc) -eq 1 ]; then
		echo "1st frame mean=$ImgMean ERROR: Mean has been inserted twice for $CASE and $BOLD."
			else
			# -- Command that inserts mean image back to the boldFIXICA file using g_InsertMean matlab function
			echo "Re-inserting mean image on the mapped $BOLD data for $CASE... "
			${MNAPMCOMMAND} "g_InsertMean(['bold' num2str($BOLD) '.dtseries.nii'], ['boldFIXICA' num2str($BOLD) '.dtseries.nii']),g_InsertMean(['bold' num2str($BOLD) '.nii.gz'], ['boldFIXICA' num2str($BOLD) '.nii.gz']),quit()"
		fi
	fi
	rm boldFIXICA"$BOLD"_mean.txt &> /dev/null
done
}
show_usage_FIXICAInsertMean() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "Function for imputing mean of the image after FIX ICA was done for further denoising."
echo ""
}

# ------------------------------------------------------------------------------------------------------
#  FIXICARemoveMean - Remove means from FIX ICA cleaned BOLDs for functional connectivity analysis
# ------------------------------------------------------------------------------------------------------

FIXICARemoveMean() {
for BOLD in $BOLDS; do
	cd ${SubjectsFolder}/${CASE}/images/functional/
	# First check if the boldFIXICA file has the mean inserted
	#3dBrickStat -mean -non-zero boldFIXICA"$BOLD".nii.gz[1] >> boldFIXICA"$BOLD"_mean.txt
	#ImgMean=`cat boldFIXICA"$BOLD"_mean.txt`
	#if [ $(echo " $ImgMean < 1000" | bc) -eq 1 ]; then
	#echo "1st frame mean=$ImgMean Mean removed OK for subject $CASE and bold# $BOLD. Skipping to next..."
	#	else
		# Next check if the boldFIXICA file has the mean inserted twice by accident
	#	if [ $(echo " $ImgMean > 15000" | bc) -eq 1 ]; then
	#	echo "1st frame mean=$ImgMean ERROR: Mean has been inserted twice for $CASE and $BOLD."
	#		else
			# Command that inserts mean image back to the boldFIXICA file using g_InsertMean matlab function
			echo "Removing mean image on the mapped CIFTI FIX ICA $BOLD data for $CASE... "
			${MNAPMCOMMAND} "g_RemoveMean(['bold' num2str($BOLD) '.dtseries.nii'], ['boldFIXICA' num2str($BOLD) '.dtseries.nii'], ['boldFIXICA_demean' num2str($BOLD) '.dtseries.nii']),quit()"
		#fi
	#fi
	#rm boldFIXICA"$BOLD"_mean.txt &> /dev/null
done
}

show_usage_FIXICARemoveMean() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "Function for removing the mean of the image after FIX ICA was done for further denoising."
echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  hcpdLegacy - Executes the Diffusion Processing Script via FUGUE implementation for legacy data - (needed for legacy DWI data that is non-HCP compliant without counterbalanced phase encoding directions needed for topup)
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

hcpdLegacy() {
# -- Unique requirements for this function:
#      Installed versions of: FSL5.0.9 or higher
#      Needs CUDA 6.0 libraries to run eddy_cuda (10x faster than on a CPU)
# -- Parse general parameters
EchoSpacing="$EchoSpacing" #EPI Echo Spacing for data (in msec); e.g. 0.69
PEdir="$PEdir" #Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior
TE="$TE" #delta TE in ms for field map or "NONE" if not used
UnwarpDir="$UnwarpDir" # direction along which to unwarp
DiffData="$DiffDataSuffix" # Diffusion data suffix name - e.g. if the data is called <SubjectID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR
CUDAQUEUE="$QUEUE" # Cluster queue name with GPU nodes - e.g. anticevic-gpu
DwellTime="$EchoSpacing" #same variable as EchoSpacing - if you have in-plane acceleration then this value needs to be divided by the GRAPPA or SENSE factor (miliseconds)
DwellTimeSec=`echo "scale=6; $DwellTime/1000" | bc` # set the dwell time to seconds
Scanner="$Scanner" #Scanner manufacturer (siemens or ge)
UseFieldmap="$UseFieldmap" #Whether or not to use standard fieldmap (yes/no)
# -- Establish global directory paths
T1wFolder=${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w
DiffFolder=${SubjectsFolder}/${CASE}/hcp/${CASE}/Diffusion
T1wDiffFolder=${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion
FieldMapFolder=${SubjectsFolder}/${CASE}/hcp/${CASE}/FieldMap_strc
LogFolder=${SubjectsFolder}/${CASE}/hcp/${CASE}/Diffusion/log
Overwrite="$Overwrite"
# -- Generate timestamp for logs and scripts
TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
Suffix="${CASE}-${TimeStamp}"
if [ "$Cluster" == 1 ]; then
	echo "Running locally on `hostname`"
	echo "Check log file output here: $LogFolder"
	echo "--------------------------------------------------------------"
	echo ""
	${HCPPIPEDIR}/DiffusionPreprocessingLegacy/DiffPreprocPipelineLegacy.sh \
	--subjectsfolder="${SubjectsFolder}" \
	--subject="${CASE}" \
	--scanner="${Scanner}" \
	--usefieldmap="${UseFieldmap}" \
	--PEdir="${PEdir}" \
	--echospacing="${EchoSpacing}" \
	--TE="${TE}" \
	--unwarpdir="${UnwarpDir}" \
	--overwrite="${Overwrite}" \
	--diffdatasuffix="${DiffDataSuffix}" >> "$LogFolder"/DiffPreprocPipelineLegacy_"$Suffix".log
else
	rm -f ${SubjectsFolder}/${CASE}/hcp/hcpd_legacy_${Suffix}.sh &> /dev/null
	echo "${HCPPIPEDIR}/DiffusionPreprocessingLegacy/DiffPreprocPipelineLegacy.sh \
	--subjectsfolder=${SubjectsFolder} \
	--subject=${CASE} \
	--scanner=${Scanner} \
	--usefieldmap=${UseFieldmap} \
	--PEdir=${PEdir} \
	--echospacing=${EchoSpacing} \
	--TE=${TE} \
	--unwarpdir=${UnwarpDir} \
	--diffdatasuffix=${DiffDataSuffix} \
	--overwrite=${Overwrite}" > ${SubjectsFolder}/${CASE}/hcp/hcpd_legacy_${Suffix}.sh
	# -- Make script executable
	chmod 770 ${SubjectsFolder}/${CASE}/hcp/hcpd_legacy_${Suffix}.sh
	cd ${SubjectsFolder}/${CASE}/hcp/
	# -- Send to scheduler
	gmri schedule command="${SubjectsFolder}/${CASE}/hcp/hcpd_legacy_${Suffix}.sh" \
	settings="${Scheduler}" \
	output="stdout:${SubjectsFolder}/${CASE}/hcp/hcpd_legacy.${Suffix}.output.log|stderr:${SubjectsFolder}/${CASE}/hcp/hcpd_legacy.${Suffix}.error.log" \
	workdir="${SubjectsFolder}/${CASE}/hcp/"
	echo "--------------------------------------------------------------"
	echo "Data successfully submitted"
	echo "Scheduler Name and Options: $Scheduler"
	echo "Check output logs here: $LogFolder"
	echo "--------------------------------------------------------------"
	echo ""
fi
}
show_usage_hcpdLegacy() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function runs the DWI preprocessing using the FUGUE method for legacy data that are not TOPUP compatible"
echo "It explicitly assumes the the Human Connectome Project folder structure for preprocessing: "
echo ""
echo " <study_folder>/<case>/hcp/<case>/Diffusion ---> DWI data needs to be here"
echo " <study_folder>/<case>/hcp/<case>/T1w       ---> T1w data needs to be here"
echo ""
echo "  Note: "
echo "  - If PreFreeSurfer component of the HCP Pipelines was run the function will make use of the T1w data [Results will be better due to superior brain stripping]."
echo "  - If PreFreeSurfer component of the HCP Pipelines was NOT run the function will start from raw T1w data [Results may be less optimal]."
echo "  - If you are this function interactively you need to be on a GPU-enabled node or send it to a GPU-enabled queue."
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "     --subjectsfolder=<folder_with_subjects>       Path to study folder that contains subjects"
echo "     --subject=<list_of_cases>                     List of subjects to run"
echo "     --scanner=<scanner_manufacturer>              Name of scanner manufacturer (siemens or ge supported) "
echo "     --usefieldmap=<yes_no>                        Whether to use the standard field map. If set to <yes> then the TE parameter becomes mandatory:"
echo "     --echospacing=<echo_spacing_value>            EPI Echo Spacing for data [in msec]; e.g. 0.69"
echo "     --PEdir=<phase_encoding_direction>            Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior"
echo "     --unwarpdir=<epi_phase_unwarping_direction>   Direction for EPI image unwarping; e.g. x or x- for LR/RL, y or y- for AP/PA; may been to try out both -/+ combinations"
echo "     --diffdatasuffix=<diffusion_data_name>        Name of the DWI image; e.g. if the data is called <SubjectID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR"
echo " "
echo "-- OPTIONAL PARMETERS:"
echo ""
echo "     --overwrite=<clean_prior_run>           Delete prior run for a given subject"
echo ""
echo " FIELDMAP-SPECFIC PARAMETERS (these become mandatory if --usefieldmap=yes):"
echo ""
echo "     --TE=<delta_te_value_for_fieldmap>      This is the echo time difference of the fieldmap sequence - find this out form the operator - defaults are *usually* 2.46ms on SIEMENS"
echo ""
echo ""
echo "-- Example with flagged parameters for a local run using Siemens FieldMap (needs GPU-enabled node):"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--function='hcpdLegacy' \ "
echo "--PEdir='1' \ "
echo "--echospacing='0.69' \ "
echo "--TE='2.46' \ "
echo "--unwarpdir='x-' \ "
echo "--diffdatasuffix='DWI_dir91_LR' \ "
echo "--usefieldmap='yes' \ "
echo "--scanner='siemens' \ "
echo "--overwrite='yes'"
echo ""
echo "-- Example with flagged parameters for submission to the scheduler using Siemens FieldMap [ needs GPU-enabled queue ]:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--function='hcpdLegacy' \ "
echo "--PEdir='1' \ "
echo "--echospacing='0.69' \ "
echo "--TE='2.46' \ "
echo "--unwarpdir='x-' \ "
echo "--diffdatasuffix='DWI_dir91_LR' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo "--usefieldmap='yes' \ "
echo "--scanner='siemens' \ "
echo "--overwrite='yes' \ "
echo ""
echo "-- Example with flagged parameters for submission to the scheduler using GE data w/out FieldMap [ needs GPU-enabled queue ]:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--function='hcpdLegacy' \ "
echo "--diffdatasuffix='DWI_dir91_LR' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo "--usefieldmap='no' \ "
echo "--PEdir='1' \ "
echo "--echospacing='0.69' \ "
echo "--unwarpdir='x-' \ "
echo "--scanner='ge' \ "
echo "--overwrite='yes' \ "
echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  eddyQC - Executes the DWI EddyQ C (DWIEddyQC.sh) via the MNAP connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

eddyQC() {
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
# -- eddy-cleaned DWI Data
########################################## OUTPUTS #########################################
# -- Outputs will be located in <eddyBase>.qc per EDDY QC specification
LogFolder="${EddyPath}/log_eddyqc"
mkdir ${LogFolder} > /dev/null 2>&1
# -- Generate timestamp for logs and scripts
TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
Suffix="${CASE}-${TimeStamp}"
if [ "$Cluster" == 1 ]; then
	echo "Running locally on `hostname`"
	echo "Check log file output here: $LogFolder"
	echo "--------------------------------------------------------------"
	echo ""
	eval "DWIeddyQC.sh \
	--subjectsfolder=${SubjectsFolder} \
	--subject=${CASE} \
	--eddybase=${EddyBase} \
	--eddypath=${EddyPath} \
	--report=${Report} \
	--bvalsfile=${BvalsFile} \
	--mask=${Mask} \
	--eddyidx=${EddyIdx} \
	--eddyparams=${EddyParams} \
	--bvecsfile=${BvecsFile} \
	--overwrite=${Overwrite}" >> "$LogFolder"/DWIEddyQC_"$Suffix".log
else
	# -- Clean prior command
	rm -f "$LogFolder"/DWIEddyQC_"$Suffix".sh &> /dev/null
	# -- Echo full command into a script
	echo "DWIeddyQC.sh \
	--subjectsfolder='${SubjectsFolder}' \
	--subject='${CASE}' \
	--eddybase='${EddyBase}' \
	--eddypath=${EddyPath} \
	--report='${Report}' \
	--bvalsfile='${BvalsFile}' \
	--mask='${Mask}' \
	--eddyidx='${EddyIdx}' \
	--eddyparams='${EddyParams}' \
	--bvecsfile='${BvecsFile}' \
	--overwrite='${Overwrite}'" > "$LogFolder"/DWIEddyQC_"$Suffix".sh
	# -- Make script executable
	chmod 770 "$LogFolder"/DWIEddyQC_"$Suffix".sh
	cd ${LogFolder}
	# -- Send to scheduler
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
show_usage_eddyQC() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function is based on FSL's eddy to perform quality control on diffusion mri (dMRI) datasets."
echo "It explicitly assumes the that eddy has been run and that EDDY QC by Matteo Bastiani, FMRIB has been installed. "
echo "For full documentation of the EDDY QC please examine the README file."
echo ""
echo "   <study_folder>/<case>/hcp/<case>/Diffusion/eddy/ ---> DWI eddy outputs would be here"
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                 Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>    Path to study folder that contains subjects"
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
echo "mnap --subjectsfolder='<path_to_study_folder_with_subject_directories>' \ "
echo "--function='eddyQC' \ "
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
#  DWIDenseParcellation - Executes the Diffusion Parcellation Script (DWIDenseParcellation.sh) via the MNAP connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

DWIDenseParcellation() {
# -- Parse general parameters
QUEUE="$QUEUE"
SubjectsFolder="$SubjectsFolder"
CASE=${CASE}
MatrixVersion="$MatrixVersion"
ParcellationFile="$ParcellationFile"
OutName="$OutName"
DWIOutput="${SubjectsFolder}/${CASE}/hcp/$CASE/MNINonLinear/Results/Tractography"
mkdir "$DWIOutput"/log > /dev/null 2>&1
LogFolder="$DWIOutput"/log
Overwrite="$Overwrite"
# -- Generate timestamp for logs and scripts
TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
Suffix="${CASE}-${TimeStamp}"
if [ "$Cluster" == 1 ]; then
	echo "Running locally on `hostname`"
	echo "Check log file output here: $LogFolder"
	echo "--------------------------------------------------------------"
	echo ""
	DWIDenseParcellation.sh \
	--subjectsfolder="${SubjectsFolder}" \
	--subject="${CASE}" \
	--matrixversion="${MatrixVersion}" \
	--parcellationfile="${ParcellationFile}" \
	--waytotal="${WayTotal}" \
	--outname="${OutName}" \
	--overwrite="${Overwrite}" >> "$LogFolder"/DWIDenseParcellation_"$Suffix".log
else
	# -- Clean prior command
	rm -f "$LogFolder"/DWIDenseParcellation_"$Suffix".sh &> /dev/null
	# -- Echo full command into a script
	echo "DWIDenseParcellation.sh \
	--subjectsfolder=${SubjectsFolder} \
	--subject=${CASE} \
	--matrixversion=${MatrixVersion} \
	--parcellationfile=${ParcellationFile} \
	--waytotal=${WayTotal} \
	--outname=${OutName} \
	--overwrite=${Overwrite}" > "$LogFolder"/DWIDenseParcellation_"$Suffix".sh
	# -- Make script executable
	chmod 770 "$LogFolder"/DWIDenseParcellation_"$Suffix".sh
	cd ${LogFolder}
	# -- Send to scheduler
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
show_usage_DWIDenseParcellation() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function implements parcellation on the DWI dense connectomes using a whole-brain parcellation (e.g.Glasser parcellation with subcortical labels included)."
echo "It explicitly assumes the the Human Connectome Project folder structure for preprocessing: "
echo ""
echo " <study_folder>/<case>/hcp/<case>/MNINonLinear/Tractography/ ---> Dense Connectome DWI data needs to be here"
echo ""
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                            Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>               Path to study folder that contains subjects"
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
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='DWIDenseParcellation' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--matrixversion='3' \ "
echo "--parcellationfile='<dlabel_file_for_parcellation>' \ "
echo "--overwrite='no' \ "
echo "--outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
echo ""
echo "-- Example with flagged parameters for submission to the scheduler:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='DWIDenseParcellation' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--matrixversion='3' \ "
echo "--parcellationfile='<dlabel_file_for_parcellation>' \ "
echo "--overwrite='no' \ "
echo "--outname='LR_Colelab_partitions_v1d_islands_withsubcortex' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  DWISeedTractography - Executes the Diffusion Seed Tractography Script (DWIDenseSeedTractography.sh) via the MNAP connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

DWISeedTractography() {
# -- Command to run
CommandToRun="DWIDenseSeedTractography.sh \
--subjectsfolder="${SubjectsFolder}" \
--subject="${CASE}" \
--matrixversion="${MatrixVersion}" \
--seedfile="${SeedFile}" \
--waytotal="${WayTotal}" \
--outname="${OutName}" \
--overwrite="${Overwrite}""
# -- Connector execute function
connectorExec
}
show_usage_DWISeedTractography() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function implements reduction on the DWI dense connectomes using a given 'seed' structure (e.g. thalamus)."
echo "It explicitly assumes the the Human Connectome Project folder structure for preprocessing: "
echo ""
echo " <folder_with_subjects>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/ ---> Dense Connectome DWI data needs to be here"
echo ""
echo ""
echo "OUTPUTS: "
echo "     <folder_with_subjects>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<subject>_Conn<matrixversion>_<outname>.dconn.nii"
echo "        --> Dense connectivity seed tractography file"
echo "" 
echo "      <folder_with_subjects>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/<subject>_Conn<matrixversion>_<outname>_Avg.dscalar.nii"
echo "         --> Dense scalar seed tractography file"
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                           Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>              Path to study folder that contains subjects"
echo "--subject=<comma_separated_list_of_cases>            List of subjects to run"
echo "--matrixversion=<matrix_version_value>               Matrix solution verion to run parcellation on; e.g. 1 or 3"
echo "--seedfile=<file_for_seed_reduction>                 Specify the absolute path of the seed file you want to use as a seed for dconn reduction"
echo "                                                     Note: If you specify --seedfile='gbc' then the function computes an average across all streamlines from every greyordinate to all other greyordinates."
echo "--outname=<name_of_output_dscalar_file>              Specify the suffix output name of the dscalar file"
echo "--scheduler=<name_of_cluster_scheduler_and_options>  A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo "                                                     e.g. for SLURM the string would look like this: "
echo "                                                     --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
echo ""
echo "-- OPTIONAL PARMETERS:"
echo ""
echo "--overwrite=<clean_prior_run>                        Delete prior run for a given subject"
echo "--waytotal=<use_waytotal_normalized_data>            Version of dense connectome to use as input" 
echo "                                                       none: without waytotal normalization [Default]" 
echo "                                                       standard: standard waytotal normalized"
echo "                                                       log: log-transformed waytotal normalized"
echo ""
echo "-- Example with flagged parameters for a local run:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='DWISeedTractography' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--matrixversion='3' \ "
echo "--seedfile='<folder_with_subjects>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz' \ "
echo "--overwrite='no' \ "
echo "--outname='Thalamus_Seed' \ "
echo ""
echo "-- Example with flagged parameters for submission to the scheduler:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='DWISeedTractography' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--matrixversion='3' \ "
echo "--seedfile='<folder_with_subjects>/<case>/hcp/<case>/MNINonLinear/Results/Tractography/CIFTI_STRUCTURE_THALAMUS_RIGHT.nii.gz' \ "
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
#  computeBOLDfc - Executes Global Brain Connectivity (GBC) or seed-based functional connectivity (ComputeFunctionalConnectivity.sh) via the MNAP connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

computeBOLDfc() {
# -- Parse general parameters
SubjectsFolder="$SubjectsFolder"
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
Overwrite="$Overwrite"			# --overwrite

# -- Check type of run
if [ "$RunType" == "individual" ]; then
	OutPath="${SubjectsFolder}/${CASE}/${InputPath}"
	# -- Make sure individual runs default to the original input path location (/images/functional)
	if [ "$InputPath" == "" ]; then
		InputPath="${SubjectsFolder}/${CASE}/images/functional"
	fi
	# -- Make sure individual runs default to the original input path location (/images/functional)
	if [ "$OutPath" == "" ]; then
		OutPath="${SubjectsFolder}/${CASE}/$InputPath"
	fi
fi

# -- Check type of connectivity calculation is seed
if [ ${Calculation} == "seed" ]; then
	echo ""
	# -- Echo command
	geho "Full Command:"; echo ""
	geho "${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh --subjectsfolder=${SubjectsFolder} --calculation=${Calculation} --runtype=${RunType} --subject=${CASE} --inputfiles=${InputFiles} --inputpath=${InputPath} --extractdata=${ExtractData} --outname=${OutName} --flist=${FileList} --overwrite=${Overwrite} --ignore=${IgnoreFrames} --roinfo=${ROIInfo} --options=${FCCommand} --method=${Method} --targetf=${OutPath} --mask=${MaskFrames} --covariance=${Covariance}"
	echo ""
	# -- Specify command variable
	CommandToRun="${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh \
	--subjectsfolder=${SubjectsFolder} \
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
	--mask='${MaskFrames}' \
	--covariance=${Covariance}"
	# -- Connector execute function
	connectorExec
fi
# -- Check type of connectivity calculation is gbc
if [ ${Calculation} == "gbc" ]; then
	echo ""
	# -- Echo command
	geho "Full Command:"; echo ""
	geho "${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh --subjectsfolder=${SubjectsFolder} --calculation=${Calculation} --runtype=${RunType} --subject=${CASE} --inputfiles=${InputFiles} --inputpath=${InputPath} --extractdata=${ExtractData} --flist=${FileList} --outname=${OutName} --overwrite=${Overwrite} --ignore=${IgnoreFrames} --target=${TargetROI} --command=${GBCCommand} --targetf=${OutPath} --mask=${MaskFrames} --rsmooth=${RadiusSmooth} --rdilate=${RadiusDilate} --verbose=${Verbose} --time=${ComputeTime} --vstep=${VoxelStep} --covariance=${Covariance}"
	echo ""
	# -- Specify command variable
	CommandToRun="${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh \
	--subjectsfolder=${SubjectsFolder} \
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
	--covariance=${Covariance}"
	# -- Connector execute function
	connectorExec
fi
}
show_usage_computeBOLDfc() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function implements Global Brain Connectivity (GBC) or seed-based functional connectivity (FC) on the dense or parcellated (e.g. Glasser parcellation)."
echo ""
echo ""
echo "For more detailed documentation run <help fc_ComputeGBC3>, <help gmrimage.mri_ComputeGBC> or <help fc_ComputeSeedMapsMultiple> inside matlab"
echo ""
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                            Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
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
echo "--subjectsfolder=<folder_with_subjects>            Path to study folder that contains subjects"
echo "--subjects=<list_of_cases>                         List of subjects to run"
echo "--inputfiles=<files_to_compute_connectivity_on>    Specify the comma separated file names you want to use (e.g. 'bold1_Atlas_MSMAll.dtseries.nii,bold2_Atlas_MSMAll.dtseries.nii')"
echo "--outname=<name_of_output_file>                    Specify the suffix name of the output file name"
echo ""
echo "-- OPTIONAL PARAMETERS FOR AN INDIVIDUAL SUBJECT RUN:"
echo "--inputpath=<path_for_input_file>                  Specify path of the file you want to use relative to the master study folder and subject directory (e.g. /images/functional/). Default [<study_folder>/subjects/<subject_id>/images/functional]"
echo "--targetf=<path_for_output_file>                   Specify the absolute path for result output folder. If using --runtype='individual' the output will default to --inputpath location for each individual subject unless otherwise specified."
echo ""
echo ""
echo "-- OPTIONAL GENERAL PARAMETERS: "
echo ""
echo "--overwrite=<clean_prior_run>                      Delete prior run for a given subject <yes/no>. Default is [no]"
echo "--extractdata=<save_out_the_data_as_as_csv>        Specify if you want to save out the matrix as a CSV file (only available if the file is a ptseries) <yes/no>. Default is [no]"
echo "--covariance=<compute_covariance>                  Whether to compute covariances instead of correlations (true / false). Default is [false]"
echo ""
echo "-- REQUIRED GBC PARMETERS:"
echo ""
echo "--target=<which_roi_to_use>                        Array of ROI codes that define target ROI [default: FreeSurfer cortex codes]"
echo "--rsmooth=<smoothing_radius>                       Radius for smoothing (no smoothing if empty). Default is []"
echo "--rdilate=<dilation_radius>                        Radius for dilating mask (no dilation if empty). Default is []"
echo "--command=<type_of_gbc_to_run>                     Specify the the type of gbc to run. This is a string describing GBC to compute. E.g. 'mFz:0.1|mFz:0.2|aFz:0.1|aFz:0.2|pFz:0.1|pFz:0.2' "
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
echo "                   > aDs:n  ... computes proportion of voxels within n strength ranges of absolute r "
echo "                   > pDs:n  ... computes proportion of voxels within n strength ranges of positive r "
echo "                   > nDs:n  ... computes proportion of voxels within n strength ranges of negative r "
echo ""
echo "-- OPTIONAL GBC PARMETERS:"
echo ""
echo "--verbose=<print_output_verbosely>                Report what is going on. Default is [false]"
echo "--time=<print_time_needed>                        Whether to print timing information. [false]"
echo "--vstep=<how_many_voxels>                         How many voxels to process in a single step. Default is [1200]"
echo ""
echo "-- REQUIRED SEED FC PARMETERS:"
echo ""
echo "--roinfo=<roi_seed_names_file>                         Region of interest (ROI) specification names file (*.names)"
echo "                                                       For an example see: $TOOLS/$MNAPREPO/library/data/roi/seeds_cifti.names"
echo "                                                       For detailed use specification see: https://bitbucket.org/hidradev/mnaptools/wiki/Overview/FileFormats.md"
echo ""
echo "-- OPTIONAL SEED FC PARMETERS: "
echo ""
echo "--method=<method_to_get_timeseries>               Method for extracting timeseries - 'mean' or 'pca' Default is ['mean'] "
echo "--options=<calculations_to_save>                  A string defining which subject files to save. Default assumes all [''] "
echo ""
echo "           > r ... save map of correlations "
echo "           > f ... save map of Fisher z values "
echo "           > cv ... save map of covariances "
echo "           > z ... save map of Z scores "
echo ""
echo ""
echo "-- Seed and GBC FC Examples with flagged parameters for submission to the scheduler:"
echo ""
echo "- Example for seed calculation for each individual subject:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='computeBOLDfc' \ "
echo "--calculation='seed' \ "
echo "--runtype='individual' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--inputfiles='<files_to_compute_connectivity_on>' \ "
echo "--inputpath='/images/functional' \ "
echo "--overwrite='yes' \ "
echo "--extractdata='yes' \ "
echo "--roinfo='ROI_Names_File.names' \ "
echo "--outname='<name_of_output_file>' \ "
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
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='computeBOLDfc' \ "
echo "--calculation='seed' \ "
echo "--runtype='group' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--inputfiles='<files_to_compute_connectivity_on>' \ "
echo "--inputpath='/images/functional' \ "
echo "--overwrite='yes' \ "
echo "--extractdata='yes' \ "
echo "--roinfo='ROI_Names_File.names' \ "
echo "--outname='<name_of_output_file>' \ "
echo "--ignore='' \ "
echo "--options='' \ "
echo "--method='' \ "
echo "--targetf='<path_for_output_file>' \ "
echo "--mask='5' \ "
echo "--covariance='false' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo ""
echo "- Example for gbc calculation for each individual subject:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='computeBOLDfc' \ "
echo "--calculation='gbc' \ "
echo "--runtype='individual' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--inputfiles='<files_to_compute_connectivity_on>' \ "
echo "--inputpath='/images/functional' \ "
echo "--overwrite='yes' \ "
echo "--extractdata='yes' \ "
echo "--outname='<name_of_output_file>' \ "
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
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='computeBOLDfc' \ "
echo "--calculation='gbc' \ "
echo "--runtype='group' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--inputfiles='<files_to_compute_connectivity_on>' \ "
echo "--inputpath='/images/functional' \ "
echo "--overwrite='yes' \ "
echo "--extractdata='yes' \ "
echo "--outname='<name_of_output_file>' \ "
echo "--ignore='' \ "
echo "--command='mFz:' \ "
echo "--targetf='<path_for_output_file>' \ "
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
#  structuralParcellation - Executes the Structural Parcellation Script (StructuralParcellation.sh) via the MNAP connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

structuralParcellation() {
# -- Parse general parameters
QUEUE="$QUEUE"
SubjectsFolder="$SubjectsFolder"
CASE=${CASE}
InputDataType="$InputDataType"
OutName="$OutName"
ParcellationFile="$ParcellationFile"
ExtractData="$ExtractData"
mkdir ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage_LR32k/structuralparcellation_log > /dev/null 2>&1
LogFolder=${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/fsaverage_LR32k/structuralparcellation_log
Overwrite="$Overwrite"
# -- Generate timestamp for logs and scripts
TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
Suffix="$CASE-$TimeStamp"
if [ "$Cluster" == 1 ]; then
	echo "Running locally on `hostname`"
	echo "Check log file output here: $LogFolder"
	echo "--------------------------------------------------------------"
	echo ""
	${TOOLS}/${MNAPREPO}/connector/functions/StructuralParcellation.sh \
	--subjectsfolder="${SubjectsFolder}" \
	--subject="${CASE}" \
	--inputdatatype="${InputDataType}" \
	--parcellationfile="${ParcellationFile}" \
	--overwrite="${Overwrite}" \
	--outname="${OutName}" \
	--extractdata="${ExtractData}" >> "$LogFolder"/StructuralParcellation_"$Suffix".log
else
	echo "${TOOLS}/${MNAPREPO}/connector/functions/StructuralParcellation.sh \
	--subjectsfolder=${SubjectsFolder} \
	--subject=${CASE} \
	--inputdatatype=${InputDataType} \
	--parcellationfile=${ParcellationFile} \
	--overwrite=${Overwrite} \
	--outname=${OutName} \
	--extractdata=${ExtractData}" > "$LogFolder"/StructuralParcellation_"$Suffix".sh &> /dev/null
	# -- Make script executable
	chmod 770 "$LogFolder"/StructuralParcellation_"$Suffix".sh &> /dev/null
	cd ${LogFolder}
	# -- Send to scheduler
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
show_usage_structuralParcellation() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function implements parcellation on the dense cortical thickness OR myelin files using a whole-brain parcellation [ e.g. Glasser parcellation with subcortical labels included ]"
echo ""
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                             Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>                Path to study folder that contains subjects"
echo "--subject=<comma_separated_list_of_cases>              List of subjects to run"
echo "--inputdatatype=<type_of_dense_data_for_input_file>    Specify the type of data for the input file [ e.g. MyelinMap_BC or corrThickness ] "
echo "--parcellationfile=<dlabel_file_for_parcellation>      Specify path of the file you want to use for parcellation relative to the master study folder [ e.g. /images/functional/bold1_Atlas_MSMAll_hp2000_clean.dtseries.nii ]"
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
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='structuralParcellation' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--inputdatatype='MyelinMap_BC' \ "
echo "--parcellationfile='<dlabel_file_for_parcellation>' \ "
echo "--overwrite='no' \ "
echo "--extractdata='yes' \ "
echo "--outname='<name_of_output_pconn_file>' "
echo ""
echo "-- Example with flagged parameters for submission to the scheduler:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='structuralParcellation' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--inputdatatype='MyelinMap_BC' \ "
echo "--parcellationfile='<dlabel_file_for_parcellation>' \ "
echo "--overwrite='no' \ "
echo "--extractdata='yes' \ "
echo "--outname='<name_of_output_pconn_file>' "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  BOLDParcellation - Executes the BOLD Parcellation Script (BOLDParcellation.sh) via the MNAP connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

BOLDParcellation() {
		# -- Parse general parameters
		QUEUE="$QUEUE"
		SubjectsFolder="$SubjectsFolder"
		CASE=${CASE}
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
			BOLDOutput="${SubjectsFolder}/${CASE}/$OutPath"
		else
			BOLDOutput="$OutPath"
		fi
		ExtractData="$ExtractData"
		mkdir "$BOLDOutput"/boldparcellation_log > /dev/null 2>&1
		LogFolder="$BOLDOutput"/boldparcellation_log
		Overwrite="$Overwrite"
		# -- Generate timestamp for logs and scripts
		TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
		Suffix="$CASE-$TimeStamp"
		if [ "$Cluster" == 1 ]; then
			echo "Running locally on `hostname`"
			echo "Check log file output here: $LogFolder"
			echo "--------------------------------------------------------------"
			echo ""
			BOLDParcellation.sh \
			--subjectsfolder="${SubjectsFolder}" \
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
			--subjectsfolder='${SubjectsFolder}' \
			--subject='${CASE}' \
			--inputfile='${InputFile}' \
			--singleinputfile='${SingleInputFile}' \
			--inputpath='${InputPath}' \
			--inputdatatype='${InputDataType}' \
			--parcellationfile='${ParcellationFile}' \
			--overwrite='${Overwrite}' \
			--outname='${OutName}' \
			--outpath='${OutPath}' \
			--computepconn='${ComputePConn}' \
			--extractdata='${ExtractData}' \
			--useweights='${UseWeights}' \
			--weightsfile='${WeightsFile}'" > "$LogFolder"/BOLDParcellation_"$Suffix".sh
			# -- Make script executable
			chmod 770 "$LogFolder"/BOLDParcellation_"$Suffix".sh &> /dev/null
			cd ${LogFolder}
			# -- Send to scheduler
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
show_usage_BOLDParcellation() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function implements parcellation on the BOLD dense files using a whole-brain parcellation [ e.g.Glasser parcellation with subcortical labels included ] "
echo ""
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                             Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>                Path to study folder that contains subjects"
echo "--subjects=<comma_separated_list_of_cases>             List of subjects to run"
echo "--inputfile=<file_to_compute_parcellation_on>          Specify the name of the file you want to use for parcellation [ e.g. bold1_Atlas_MSMAll_hp2000_clean ]"
echo "--inputpath=<path_for_input_file>                      Specify path of the file you want to use for parcellation relative to the master study folder and subject directory [ e.g. /images/functional/ ]"
echo "--inputdatatype=<type_of_dense_data_for_input_file>    Specify the type of data for the input file [ e.g. dscalar or dtseries ]"
echo "--parcellationfile=<dlabel_file_for_parcellation>      Specify path of the file you want to use for parcellation relative to the master study folder [ e.g. /images/functional/bold1_Atlas_MSMAll_hp2000_clean.dtseries.nii ]"
echo "--outname=<name_of_output_pconn_file>                  Specify the suffix output name of the pconn file"
echo "--outpath=<path_for_output_file>                       Specify the output path name of the pconn file relative to the master study folder [ e.g. /images/functional/ ]"
echo "--scheduler=<name_of_cluster_scheduler_and_options>    A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo "                                                       e.g. for SLURM the string would look like this: "
echo "                                                       --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
echo ""
echo "-- OPTIONAL PARMETERS:"
echo ""
echo "--singleinputfile=<parcellate_single_file>                     Parcellate only a single file in any location using an absolute path point to this file. Individual flags are not needed [ --subject, --studyfolder, -inputfile, --inputpath ]"
echo "--overwrite=<clean_prior_run>                                  Delete prior run"
echo "--computepconn=<specify_parcellated_connectivity_calculation>	 Specify if a parcellated connectivity file should be computed <pconn>. This is done using covariance and correlation [ e.g. yes; default is set to no ]"
echo "--useweights=<clean_prior_run>                                 If computing a  parcellated connectivity file you can specify which frames to omit [ e.g. yes' or no; default is set to no ] "
echo "--weightsfile=<location_and_name_of_weights_file>              Specify the location of the weights file relative to the master study folder [ e.g. /images/functional/movement/bold1.use ]"
echo "--extractdata=<save_out_the_data_as_as_csv>                    Specify if you want to save out the matrix as a CSV file"
echo ""
echo "-- Example with flagged parameters for a local run:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='BOLDParcellation' \ "
echo "--subjects='<comma_separated_list_of_cases>' \ "
echo "--inputfile='<name_of_input_file' \ "
echo "--inputpath='/images/functional/' \ "
echo "--inputdatatype='dtseries' \ "
echo "--parcellationfile='<dlabel_file_for_parcellation>' \ "
echo "--overwrite='no' \ "
echo "--outname='<name_of_output_pconn_file>' \ "
echo "--outpath='/images/functional/' \ "
echo "--computepconn='yes' \ "
echo "--extractdata='yes' \ "
echo "--useweights='no' \ "
echo ""
echo "-- Example with flagged parameters for submission to the scheduler:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='BOLDParcellation' \ "
echo "--subjects='100206' \ "
echo "--inputfile='bold1_Atlas_MSMAll_hp2000_clean' \ "
echo "--inputpath='/images/functional/' \ "
echo "--inputdatatype='dtseries' \ "
echo "--parcellationfile='<dlabel_file_for_parcellation>' \ "
echo "--overwrite='no' \ "
echo "--outname='<name_of_output_pconn_file>' \ "
echo "--outpath='/images/functional/' \ "
echo "--computepconn='yes' \ "
echo "--extractdata='yes' \ "
echo "--useweights='no' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  ROIExtract - Executes the ROI Extraction Script (ROIExtract.sh) via the MNAP connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

ROIExtract() {
# -- Parse general parameters
InputFile="$InputFile"
OutPath="$OutPath"
OutName="$OutName"
ROIFile="$ROIInputFile"
SubjectsFolder="$SubjectsFolder"
CASE=${CASE}
ROIFileSubjectSpecific="$ROIFileSubjectSpecific"
SingleInputFile="$SingleInputFile"
Cluster="$RunMethod"

if [ -z "$SingleInputFile" ]; then
	OutPath="${SubjectsFolder}/${CASE}/$OutPath"
else
	OutPath="$OutPath"
	InputFile="$SingleInputFile"
fi

if [ "$ROIFileSubjectSpecific" == "no" ]; then
	ROIFile="$ROIFile"
else
	ROIFile="${SubjectsFolder}/${CASE}/$ROIFile"
fi

ExtractData="$ExtractData"
mkdir "$OutPath"/roiextraction_log > /dev/null 2>&1
LogFolder="$OutPath"/roiextraction_log
Overwrite="$Overwrite"

# -- Generate timestamp for logs and scripts
TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
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

	# -- Make script executable
	chmod 770 "$LogFolder"/extract_ROIs_"$Suffix".sh &> /dev/null
	cd ${LogFolder}

	# -- Send to scheduler
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

show_usage_ROIExtract() {
echo ""
echo "DESCRIPTION for $UsageInput"
echo ""
echo " This function calls ROIExtract.sh and extracts data from an input file for every ROI in a given template file."
echo " The function needs a matching file type for the ROI input and the data input (i.e. both NIFTI or CIFTI)."
echo " It assumes that the template ROI file indicates each ROI in a single volume via unique scalar values."
echo ""
echo ""
echo "REQUIRED PARMETERS (for single input file):"
echo ""
echo "--function=<function_name>                 Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--singleinputfile=<file_to_be_extracted>   Extract data from a single file in any location using an absolute path point to this file"
echo "--roifile=<roi_template_file>              Specify path to the ROI template file (either a NIFTI or a CIFTI with distinct scalar values per ROI)"
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
echo "mnap --subjectsfolder='<path_to_study_folder>' \ "
echo "--function='ROIExtract' \ "
echo "--singleinputfile='<path_to_inputfile>' \ "
echo "--roifile='<path_to_roifile>' \ "
echo "--outpath='<output_path>' \ "
echo "--outname='<output_name>' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo ""
}

# ------------------------------------------------------------------------------------------------------
#  FSLDtifit - Executes the dtifit script from FSL (needed for probabilistic tractography)
# ------------------------------------------------------------------------------------------------------

FSLDtifit() {
mkdir ${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/dtifit_log > /dev/null 2>&1
LogFolder=${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/dtifit_log
# -- Check if overwrite flag was set
if [ "$Overwrite" == "yes" ]; then
	echo ""
	reho "Removing existing dtifit run for $CASE..."
	echo ""
	rm -rf ${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/dti_* > /dev/null 2>&1
fi
minimumfilesize=100000
if [ -a ${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/dti_FA.nii.gz ]; then
	actualfilesize=$(wc -c <${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/dti_FA.nii.gz)
else
	actualfilesize="0"
fi

if [ $(echo "$actualfilesize" | bc) -gt $(echo "$minimumfilesize" | bc) ]; then
	echo ""
	echo "--- DTI Fit completed for $CASE ---"
	echo ""
else
	# -- Generate timestamp for logs and scripts
	TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
	Suffix="$CASE-$TimeStamp"
	rm "$LogFolder"/fsldtifit_${Suffix}.sh &> /dev/null
	DtiFitCommand="dtifit --data=${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./data --out=${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./dti --mask=${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./nodif_brain_mask --bvecs=${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./bvecs --bvals=${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./bvals"
	geho "Running the following command"
	geho "${DtiFitCommand}"
	echo ""
	echo "${DtiFitCommand}" >> "$LogFolder"/fsldtifit_${Suffix}.sh &> /dev/null
	# -- Make script executable
	chmod 770 "$LogFolder"/fsldtifit_${Suffix}.sh &> /dev/null
	if [ "$Cluster" == 1 ]; then
		"$LogFolder"/fsldtifit_${Suffix}.sh 2>&1 | tee -a "$LogFolder"/fsldtifit-${Suffix}.log
		# --> This fails on some OS |& versions due to BASH version incompatiblity - need to use full expansion 2>&1 | : 
		# "$LogFolder"/fsldtifit_${Suffix}.sh |& tee -a "$LogFolder"/fsldtifit_${Suffix}.log
	fi
	if [ "$Cluster" == 2 ]; then
		# -- Send to scheduler
		cd ${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/
		gmri schedule command="${DtiFitCommand}" \
		settings="${Scheduler}" \
		output="stdout:${LogFolder}/fsldtifit.${Suffix}.output.log|stderr:${LogFolder}/fsldtifit.${Suffix}.error.log" \
		workdir="${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/"
		echo "--------------------------------------------------------------"
		echo "Data successfully submitted"
		echo "Scheduler Name and Options: $Scheduler"
		echo "Check output logs here: $LogFolder"
		echo "--------------------------------------------------------------"
		echo ""
	fi
fi
}
show_usage_FSLDtifit() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function runs the FSL dtifit processing locally or via a scheduler."
echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing and completed diffusion processing: "
echo ""
echo " <study_folder>/<case>/hcp/<case>/Diffusion ---> DWI data needs to be here"
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                           Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>              Path to study folder that contains subjects"
echo "--subjects=<comma_separated_list_of_cases>           List of subjects to run"
echo "--overwrite=<clean_prior_run>                        Delete prior run for a given subject"
echo "--scheduler=<name_of_cluster_scheduler_and_options>  A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo "                                                     e.g. for SLURM the string would look like this: "
echo "                                                     --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
echo ""
echo "-- Example with flagged parameters for submission to the scheduler:"
echo ""
echo "mnap --subjectsfolder='<path_to_study_subjects_folder>' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--function='FSLDtifit' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo "--overwrite='yes'"
echo ""
}

# ------------------------------------------------------------------------------------------------------
#  FSLBedpostxGPU - Executes the bedpostx_gpu code from FSL (needed for probabilistic tractography)
# ------------------------------------------------------------------------------------------------------

FSLBedpostxGPU() {
# -- Establish global directory paths
T1wDiffFolder=${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion
BedPostXFolder=${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX
LogFolder="$BedPostXFolder"/logs
Overwrite="$Overwrite"
# -- Hard-coded cuda call for HPC clusters
module load GPU/Cuda/6.5 > /dev/null 2>&1
# -- Check if overwrite flag was set
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
# -- Check if the file even exists
if [ -f ${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/"$CheckFile" ]; then
	# -- Set file sizes to check for completion
	minimumfilesize=20000000
	actualfilesize=`wc -c < ${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/merged_f1samples.nii.gz` > /dev/null 2>&1
	filecount=`ls ${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/merged_*nii.gz | wc | awk {'print $1'}`
fi
# -- Then check if run is complete based on file count
if [ "$filecount" == 9 ]; then > /dev/null 2>&1
	echo ""
	cyaneho " --> $filecount merged samples for $CASE found."
	# -- Then check if run is complete based on file size
	if [ $(echo "$actualfilesize" | bc) -ge $(echo "$minimumfilesize" | bc) ]; then > /dev/null 2>&1
		echo ""
		cyaneho " --> Bedpostx outputs found and completed for $CASE"
		echo ""
		cyaneho "Check prior output logs here: $LogFolder"
		echo ""
		echo "--------------------------------------------------------------"
		echo ""
		return 0
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
# -- Generate log folder
mkdir ${BedPostXFolder} > /dev/null 2>&1
mkdir ${LogFolder} > /dev/null 2>&1
# -- Generate timestamp for logs and scripts
TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
Suffix="${CASE}-${TimeStamp}"
if [ "$Cluster" == 1 ]; then
	echo "Running bedpostx_gpu locally on `hostname`"
	echo "Check log file output here: $LogFolder"
	echo "--------------------------------------------------------------"
	echo ""
	if [ -f "$T1wDiffFolder"/grad_dev.nii.gz ]; then
		${FSLGPUBinary}/bedpostx_gpu_noscheduler "$T1wDiffFolder"/. -n "$Fibers" -model "$Model" -b "$Burnin" -g "$RicianFlag" >> "$LogFolder"/bedpostX-"$Suffix".log
	else
		${FSLGPUBinary}/bedpostx_gpu_noscheduler "$T1wDiffFolder"/. -n "$Fibers" -model "$Model" -b "$Burnin" "$RicianFlag" >> "$LogFolder"/bedpostX-"$Suffix".log
	fi
fi
if [ "$Cluster" == 2 ]; then
	# -- Clean prior command
	rm -f "$LogFolder"/bedpostX_"$Suffix".sh &> /dev/null
	# -- Echo full command into a script
	if [ -f "$T1wDiffFolder"/grad_dev.nii.gz ]; then
		echo "${FSLGPUBinary}/bedpostx_gpu_noscheduler ${T1wDiffFolder}/. -n ${Fibers} -model ${Model} -b ${Burnin} -g ${RicianFlag}" > "$LogFolder"/bedpostX_"$Suffix".sh
	else
		echo "${FSLGPUBinary}/bedpostx_gpu_noscheduler ${T1wDiffFolder}/. -n ${Fibers} -model ${Model} -b ${Burnin} ${RicianFlag}" > "$LogFolder"/bedpostX_"$Suffix".sh
	fi
	# -- Make script executable
	chmod 770 "$LogFolder"/bedpostX_"$Suffix".sh
	cd ${LogFolder}
	# -- Send to scheduler
	gmri schedule command="${LogFolder}/bedpostX_${Suffix}.sh" \
	settings="${Scheduler}" \
	output="stdout:${LogFolder}/bedpostX.${Suffix}.output.log|stderr:${LogFolder}/bedpostX.${Suffix}.error.log" \
	workdir="${LogFolder}"
	echo "--------------------------------------------------------------"
	echo "Data successfully submitted"
	echo "Scheduler Name and Options: $Scheduler"
	echo "Check output logs here: $LogFolder/bedpostX-$Suffix.log "
	echo "--------------------------------------------------------------"
	echo ""
fi
}

show_usage_FSLBedpostxGPU() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function runs the FSL bedpostx_gpu processing using a GPU-enabled node or via a GPU-enabled queue if using the scheduler option."
echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing and completed diffusion processing: "
echo ""
echo " <study_folder>/<case>/hcp/<case>/Diffusion ---> DWI data needs to be here"
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                            Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>               Path to study folder that contains subjects"
echo "--subjects=<comma_separated_list_of_cases>            List of subjects to run"
echo "--fibers=<number_of_fibers>                           Number of fibres per voxel, default 3"
echo "--model=<deconvolution_model>                         Deconvolution model. 1: with sticks, 2: with sticks with a range of diffusivities <default>, 3: with zeppelins"
echo "--burnin=<burnin_period_value>                        Burnin period, default 1000"
echo "--rician=<set_rician_value>                           <yes> or <no>. Default is yes"
echo "--overwrite=<clean_prior_run>                         Delete prior run for a given subject"
echo "--scheduler=<name_of_cluster_scheduler_and_options>   A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo "                                                        e.g. for SLURM the string would look like this: "
echo "                                                         --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
echo "                                                           * Note: You need to specify a GPU-enabled queue or partition"
echo ""
echo "-- Example with flagged parameters for submission to the scheduler:"
echo ""
echo "mnap --subjectsfolder='<path_to_study_subjects_folder>' \ "
echo "--function='FSLBedpostxGPU' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--fibers='3' \ "
echo "--burnin='3000' \ "
echo "--model='3' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo "--overwrite='yes'"
echo ""
}

# ------------------------------------------------------------------------------------------------------------------------------
#  autoPtx - Executes the autoptx script from FSL (needed for probabilistic estimation of large-scale fiber bundles / tracts)
# -------------------------------------------------------------------------------------------------------------------------------

autoPtx() {
Subject=${CASE}
StudyFolder=${SubjectsFolder}/${CASE}/hcp/
BpxFolder="$BedPostXFolder"
QUEUE="$QUEUE"
if [ "$Cluster" == 1 ]; then
	echo "--------------------------------------------------------------"
	echo "Running locally on `hostname`"
	echo "Check log file output here: $LogFolder"
	echo "--------------------------------------------------------------"
	echo ""
	"$AutoPtxFolder"/autoptx "$SubjectsFolder" "$Subject" "$BpxFolder"
	"$AutoPtxFolder"/Prepare_for_Display.sh $StudyFolder/$Subject/MNINonLinear/Results/autoptx 0.005 1
	"$AutoPtxFolder"/Prepare_for_Display.sh $StudyFolder/$Subject/MNINonLinear/Results/autoptx 0.005 0
else
	# -- Set scheduler for fsl_sub command
	#fslsub="$Scheduler"
	#fsl_sub."$fslsub" -Q "$QUEUE" "$AutoPtxFolder"/autoPtx "$SubjectsFolder" "$Subject" "$BpxFolder"
	#fsl_sub."$fslsub" -Q "$QUEUE" -j <jid> "$AutoPtxFolder"/Prepare_for_Display.sh $SubjectsFolder/$Subject/MNINonLinear/Results/autoptx 0.005 1
	#fsl_sub."$fslsub" -Q "$QUEUE" -j <jid> "$AutoPtxFolder"/Prepare_for_Display.sh $SubjectsFolder/$Subject/MNINonLinear/Results/autoptx 0.005 0
	# -- Send to scheduler
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
show_usage_autoPtx() {
echo ""
echo "-- DESCRIPTION for $UsageInput "
echo ""
echo "USAGE PENDING... "
echo ""
}

# -------------------------------------------------------------------------------------------------------------------
#  pretractographyDense - Executes the HCP Pretractography code [ Stam's implementation for all grayordinates ]
# ------------------------------------------------------------------------------------------------------------------

pretractographyDense() {
# -- Parse general parameters
ScriptsFolder="$HCPPIPEDIR_dMRITracFull"/PreTractography
LogFolder=${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Results/log_pretractographydense
mkdir "$LogFolder"  &> /dev/null
RunFolder=${SubjectsFolder}/${CASE}/hcp/
if [ "$Cluster" == 1 ]; then
	echo ""
	echo "--------------------------------------------------------------"
	echo "Running Pretractography Dense locally on `hostname`"
	echo "Check output here: $LogFolder"
	echo "--------------------------------------------------------------"
	echo ""
	"$ScriptsFolder"/PreTractography.sh "$RunFolder" ${CASE} 0 >> "$LogFolder"/PretractographyDense_${CASE}_`date +%Y-%m-%d-%H-%M-%S`.log
else
	echo "Job ID:"
	PreTracCommand="${ScriptsFolder}/PreTractography.sh ${RunFolder} ${CASE} 0 "
	# -- Send to scheduler
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

show_usage_pretractographyDense() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
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
echo "--function=<function_name>                              Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>                 Path to study folder that contains subjects"
echo "--subjects=<comma_separated_list_of_cases>              List of subjects to run"
echo "--scheduler=<name_of_cluster_scheduler_and_options>     A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo "                                                        e.g. for SLURM the string would look like this: "
echo "                                                        --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
echo ""
echo "-- Example with flagged parameters for submission to the scheduler:"
echo ""
echo "mnap --subjectsfolder='<path_to_study_subjects_folder>' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--function='pretractographyDense' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo "--scheduler='LSF'"
echo ""
}

# --------------------------------------------------------------------------------------------------------------------------------------------------
#  probtrackxGPUDense - Executes the HCP Matrix1 and / or 3 code and generates WB dense connectomes (Stam's implementation for all grayordinates)
# --------------------------------------------------------------------------------------------------------------------------------------------------

probtrackxGPUDense() {
# -- Parse general parameters
ScriptsFolder="$HCPPIPEDIR_dMRITracFull"/Tractography_gpu_scripts
ResultsFolder=${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography
RunFolder=${SubjectsFolder}/${CASE}/hcp/
NsamplesMatrixOne="$NsamplesMatrixOne"
NsamplesMatrixThree="$NsamplesMatrixThree"
minimumfilesize=100000000
# -- Generate the results and log folders
mkdir "$ResultsFolder"  &> /dev/null
# -- Generate timestamp for logs and scripts
TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
Suffix="${CASE}-${TimeStamp}"

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
		# -- Submit script locally
		if [ "$Cluster" == 1 ]; then
			echo "Running probtrackxgpudense locally on `hostname`"
			echo "Check log file output here: $LogFolder"
			echo "--------------------------------------------------------------"
			echo ""
			"$ScriptsFolder"/RunMatrix${MNum}_NoScheduler.sh "$RunFolder" ${CASE} "$Nsamples" "$SchedulerType" >> "$LogFolder"/Matrix${MNum}_"$Suffix".log
		fi
		if [ "$Cluster" == 2 ]; then
			# -- Clean prior command
			rm -f "$LogFolder"/Matrix${MNum}_"$Suffix".sh &> /dev/null
			# -- Echo full command into a script
			echo "${ScriptsFolder}/RunMatrix${MNum}_NoScheduler.sh ${RunFolder} ${CASE} ${Nsamples} ${SchedulerType}" >> "$LogFolder"/Matrix${MNum}_"$Suffix".sh
			#echo "${ScriptsFolder}/RunMatrix${MNum}.sh ${RunFolder} ${CASE} ${Nsamples} ${SchedulerType}" > "$LogFolder"/Matrix${MNum}_"$Suffix".sh
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

show_usage_probtrackxGPUDense() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function runs the probtrackxgpu dense whole-brain connectome generation by calling $ScriptsFolder/RunMatrix1.sh or $ScriptsFolder/RunMatrix3.sh"
echo "Note that this function needs to send work to a GPU-enabled queue or you need to run it locally from a GPU-equiped machine"
echo "It explicitly assumes the Human Connectome Project folder structure and completed FSLBedpostxGPU and pretractographyDense functions processing:"
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
echo "-- Note on waytotal normalization and log transformation of streamline counts:"
echo ""
echo "  waytotal normalization is computed automatically as part of the run prior to any inter-subject or group comparisons"
echo "  to account for individual differences in geometry and brain size. The function divides the "
echo "  dense connectome by the waytotal value, turning absolute streamline counts into relative "
echo "  proportions of the total streamline count in each subject. "
echo ""
echo "  Next, a log transformation is computed on the waytotal normalized data, "
echo "  which will yield stronger connectivity values for longe-range projections. "
echo "  Log-transformation accounts for algorithmic distance bias in tract generation "
echo "  (path probabilities drop with distance as uncertainty is accumulated)."
echo "  See Donahue et al. • The Journal of Neuroscience, June 22, 2016 • 36(25):6758 – 6770. "
echo "      DOI: https://doi.org/10.1523/JNEUROSCI.0493-16.2016"
echo ""
echo "  The outputs for these files will be in:"
echo ""
echo "     /<path_to_study_subjects_folder>/<subject_id>/hcp/<subject_id>/MNINonLinear/Results/Tractography/<MatrixName>_waytotnorm.dconn.nii"
echo "     /<path_to_study_subjects_folder>/<subject_id>/hcp/<subject_id>/MNINonLinear/Results/Tractography/<MatrixName>_waytotnorm_log.dconn.nii"
echo ""
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                            Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>               Path to study folder that contains subjects"
echo "--subjects=<comma_separated_list_of_cases>            List of subjects to run"
echo "--scheduler=<name_of_cluster_scheduler_and_options>     A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo "                                                               e.g. for SLURM the string would look like this: "
echo "                                                                    --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
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
echo "mnap --subjectsfolder='<path_to_study_subjects_folder>' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--function='probtrackxGPUDense' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo "--omatrix1='yes' \ "
echo "--nsamplesmatrix1='10000' \ "
echo "--overwrite='no'"
echo ""
}

# ------------------------------------------------------------------------------------------------------------------------------
#  Sync data from AWS buckets - customized for HCP
# -------------------------------------------------------------------------------------------------------------------------------

AWSHCPSync() {
# -- Parse general parameters
mkdir "$SubjectsFolder"/aws.logs &> /dev/null
cd "$SubjectsFolder"/aws.logs
if [ "$RunMethod" == "2" ]; then
	echo "Dry run"
	if [ -d ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear ]; then
		mkdir ${SubjectsFolder}/${CASE}/hcp/${CASE}/"$Modality" &> /dev/null
		time aws s3 sync --dryrun s3:/"$Awsuri"/${CASE}/"$Modality" ${SubjectsFolder}/${CASE}/hcp/${CASE}/"$Modality"/ >> AWSHCPSync_${CASE}_"$Modality"_`date +%Y-%m-%d-%H-%M-%S`.log
	else
		mkdir ${SubjectsFolder}/${CASE} &> /dev/null
		mkdir ${SubjectsFolder}/${CASE}/hcp &> /dev/null
		mkdir ${SubjectsFolder}/${CASE}/hcp/${CASE} &> /dev/null
		mkdir ${SubjectsFolder}/${CASE}/hcp/${CASE}/"$Modality" &> /dev/null
		time aws s3 sync --dryrun s3:/"$Awsuri"/${CASE}/"$Modality" ${SubjectsFolder}/${CASE}/hcp/${CASE}/"$Modality"/ >> AWSHCPSync_${CASE}_"$Modality"_`date +%Y-%m-%d-%H-%M-%S`.log
	fi
fi
if [ "$RunMethod" == "1" ]; then
	echo "Syncing"
	if [ -d ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear ]; then
		mkdir ${SubjectsFolder}/${CASE}/hcp/${CASE}/"$Modality" &> /dev/null
		time aws s3 sync s3:/"$Awsuri"/${CASE}/"$Modality" ${SubjectsFolder}/${CASE}/hcp/${CASE}/"$Modality"/ >> AWSHCPSync_${CASE}_"$Modality"_`date +%Y-%m-%d-%H-%M-%S`.log
	else
		mkdir ${SubjectsFolder}/${CASE} &> /dev/null
		mkdir ${SubjectsFolder}/${CASE}/hcp &> /dev/null
		mkdir ${SubjectsFolder}/${CASE}/hcp/${CASE} &> /dev/null
		mkdir ${SubjectsFolder}/${CASE}/hcp/${CASE}/"$Modality" &> /dev/null
		echo "$Awsuri"/${CASE}/"$Modality"
		time aws s3 sync s3:/"$Awsuri"/${CASE}/"$Modality" ${SubjectsFolder}/${CASE}/hcp/${CASE}/"$Modality"/ >> AWSHCPSync_${CASE}_"$Modality"_`date +%Y-%m-%d-%H-%M-%S`.log
	fi
fi
}
show_usage_AWSHCPSync() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function enables syncing of HCP data from the Amazon AWS S3 repository."
echo "It assumes you have enabled your AWS credentials via the HCP website."
echo "These credentials are expected in your home folder under ./aws/credentials."
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                    Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>       Path to study folder that contains subjects"
echo "--subjects=<comma_separated_list_of_cases>    List of subjects to run"
echo "--modality=<modality_to_sync>                 Which modality or folder do you want to sync [e.g. MEG, MNINonLinear, T1w]"
echo "--awsuri=<aws_uri_location>                   Enter the AWS URI [e.g. /hcp-openaccess/HCP_900]"
echo ""
echo "-- Example with flagged parameters for submission to the scheduler:"
echo ""
echo "mnap --subjectsfolder='<path_to_study_subjects_folder>' \ "
echo "--subjects='<comma_separated_list_of_cases>' \ "
echo "--function='AWSHCPSync' \ "
echo "--modality='T1w' \ "
echo "--awsuri='/hcp-openaccess/HCP_900'"
echo ""
}

# ------------------------------------------------------------------------------------------------------------------------------
# QC - customized for HCP - QCPreproc
# -------------------------------------------------------------------------------------------------------------------------------

QCPreproc() {
# -- General parameters
StudyFolder="$StudyFolder"
SubjectsFolder="$SubjectsFolder"
CASE="$CASE"
Modality="$Modality"
OutPath="$OutPath"
TemplateFolder="$TemplateFolder"
Overwrite="$Overwrite"
Cluster="$RunMethod"
SceneZip="$SceneZip"
# -- DWI Parameters
DWIPath="$DWIPath"
DWIData="$DWIData"
DWILegacy="$DWILegacy"
DtiFitQC="$DtiFitQC"
BedpostXQC="$BedpostXQC"
EddyQCStats="$EddyQCStats"
# -- BOLD Parameters
BOLDS="$BOLDS"
BOLDPrefix="$BOLDPrefix"
BOLDSuffix="$BOLDSuffix"
SkipFrames="$SkipFrames"
SNROnly="SNROnly"

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

# -- Generate timestamp for logs and scripts
TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
Suffix="${CASE}-${TimeStamp}"

# -- Run locally or send to scheduler
if [ "$Cluster" == 1 ]; then
	echo "Running function locally on `hostname`"
	echo ""
	geho "Full Command:"
	geho "${TOOLS}/${MNAPREPO}/connector/functions/QCPreprocessing.sh \
	--subjectsfolder=${SubjectsFolder} \
	--subject=${CASE} \
	--outpath=${OutPath} \
	--overwrite=${Overwrite} \
	--templatefolder=${TemplateFolder} \
	--modality=${Modality} \
	--dwipath=${DWIPath} \
	--dwidata=${DWIData} \
	--dwilegacy=${DWILegacy} \
	--dtifitqc=${DtiFitQC} \
	--bedpostxqc=${BedpostXQC} \
	--eddyqcstats=${EddyQCStats} \
	--bolddata='${BOLDS}' \
	--boldprefix=${BOLDPrefix} \
	--boldsuffix=${BOLDSuffix} \
	--skipframes=${SkipFrames} \
	--snronly=${SNROnly} \
	--timestamp=${TimeStamp} \
	--suffix=${Suffix} \
	--scenezip=${SceneZip} "
	echo ""
	echo "Check log file output here when finished: $LogFolder/QCPreprocessing_$Suffix.log "
	echo "--------------------------------------------------------------"
	echo ""
	eval "${TOOLS}/${MNAPREPO}/connector/functions/QCPreprocessing.sh \
	--subjectsfolder='${SubjectsFolder}' \
	--subject='${CASE}' \
	--outpath='${OutPath}' \
	--overwrite='${Overwrite}' \
	--templatefolder='${TemplateFolder}' \
	--modality='${Modality}' \
	--dwipath='${DWIPath}' \
	--dwidata='${DWIData}' \
	--dwilegacy='${DWILegacy}' \
	--dtifitqc='${DtiFitQC}' \
	--bedpostxqc='${BedpostXQC}' \
	--eddyqcstats='${EddyQCStats}' \
	--bolddata='${BOLDS}' \
	--boldprefix='${BOLDPrefix}' \
	--boldsuffix='${BOLDSuffix}' \
	--skipframes='${SkipFrames}' \
	--snronly='${SNROnly}' \
	--timestamp='${TimeStamp}' \
	--scenezip='${SceneZip}' \
	--suffix='${Suffix}'" >> "$LogFolder"/QCPreprocessing_"$Suffix".log
else
	# -- Echo full command into a script
	echo ""
	geho "Full Command:"
	geho "${TOOLS}/${MNAPREPO}/connector/functions/QCPreprocessing.sh \
	--subjectsfolder=${SubjectsFolder} \
	--subject=${CASE} \
	--outpath=${OutPath} \
	--overwrite=${Overwrite} \
	--templatefolder=${TemplateFolder} \
	--modality=${Modality} \
	--dwipath=${DWIPath} \
	--dwidata=${DWIData} \
	--dwilegacy=${DWILegacy} \
	--dtifitqc=${DtiFitQC} \
	--bedpostxqc=${BedpostXQC} \
	--eddyqcstats=${EddyQCStats} \
	--bolddata='${BOLDS}' \
	--boldprefix=${BOLDPrefix} \
	--boldsuffix=${BOLDSuffix} \
	--skipframes=${SkipFrames} \
	--snronly=${SNROnly} \
	--timestamp=${TimeStamp} \
	--suffix=${Suffix} \
	--scenezip=${SceneZip}"
	echo ""
	echo "${TOOLS}/${MNAPREPO}/connector/functions/QCPreprocessing.sh \
	--subjectsfolder='${SubjectsFolder}' \
	--subject='${CASE}' \
	--outpath='${OutPath}' \
	--overwrite='${Overwrite}' \
	--templatefolder='${TemplateFolder}' \
	--modality='${Modality}' \
	--dwipath='${DWIPath}' \
	--dwidata='${DWIData}' \
	--dwilegacy='${DWILegacy}' \
	--dtifitqc='${DtiFitQC}' \
	--bedpostxqc='${BedpostXQC}' \
	--eddyqcstats='${EddyQCStats}' \
	--bolddata='${BOLDS}' \
	--boldprefix=${BOLDPrefix} \
	--boldsuffix='${BOLDSuffix}' \
	--skipframes='${SkipFrames}' \
	--snronly='${SNROnly}' \
	--timestamp='${TimeStamp}' \
	--suffix='${Suffix}' \
	--scenezip='${SceneZip}'" >> "$LogFolder"/QCPreprocessing_"$Suffix".sh
	# -- Make script executable
	chmod 770 "$LogFolder"/QCPreprocessing_"$Suffix".sh
	cd ${LogFolder}
	# -- Send to scheduler
	gmri schedule command="${LogFolder}/QCPreprocessing_${Suffix}.sh" \
	settings="${Scheduler}" \
	output="stdout:${LogFolder}/QCPreprocessing.${Suffix}.output.log|stderr:${LogFolder}/QCPreprocessing.${Suffix}.error.log" \
	workdir="${LogFolder}"
	echo ""
	echo "--------------------------------------------------------------"
	echo "Data successfully submitted "
	echo "Scheduler Options: $Scheduler "
	echo "Check output logs here: $LogFolder "
	echo "--------------------------------------------------------------"
	echo ""
fi
}
show_usage_QCPreproc() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function runs the QC preprocessing for a given specified modality. Supported: T1w, T2w, myelin, BOLD, DWI."
echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing."
echo ""
echo ""
echo "The function is compabible with both legacy data [without T2w scans] and HCP-compliant data [with T2w scans and DWI]"
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
echo ""
echo "-- Example with flagged parameters for a local run:"
echo ""
echo "mnap --subjectsfolder='<path_to_study_subjects_folder>' \ "
echo "--function='QCPreproc' \ "
echo "--subjects='<comma_separated_list_of_cases>' \ "
echo "--outpath='<path_for_output_file> \ "
echo "--templatefolder='<path_for_the_template_folder>' \ "
echo "--modality='<input_modality_for_qc>'"
echo "--overwrite='no' \ "
echo ""
echo "-- Example with flagged parameters for submission to the scheduler:"
echo ""
echo "mnap --subjectsfolder='<path_to_study_subjects_folder>' \ "
echo "--function='QCPreproc' \ "
echo "--subjects='<comma_separated_list_of_cases>' \ "
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
echo "# -- T1w QC"
echo "mnap --subjectsfolder='<path_to_study_subjects_folder>' \ "
echo "--function='QCPreproc' \ "
echo "--subjects='<comma_separated_list_of_cases>' \ "
echo "--outpath='<path_for_output_file> \ "
echo "--templatefolder='<path_for_the_template_folder>' \ "
echo "--modality='T1w' \ "
echo "--overwrite='yes' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo ""
echo "# -- T2w QC"
echo "mnap --subjectsfolder='<path_to_study_subjects_folder>' \ "
echo "--function='QCPreproc' \ "
echo "--subjects='<comma_separated_list_of_cases>' \ "
echo "--outpath='<path_for_output_file> \ "
echo "--templatefolder='<path_for_the_template_folder>' \ "
echo "--modality='T2w' \ "
echo "--overwrite='yes' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo ""
echo "# -- Myelin QC"
echo "mnap --subjectsfolder='<path_to_study_subjects_folder>' \ "
echo "--function='QCPreproc' \ "
echo "--subjects='<comma_separated_list_of_cases>' \ "
echo "--outpath='<path_for_output_file> \ "
echo "--templatefolder='<path_for_the_template_folder>' \ "
echo "--modality='myelin' \ "
echo "--overwrite='yes' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo ""
echo "# -- DWI QC "
echo "mnap --subjectsfolder='<path_to_study_subjects_folder>' \ "
echo "--function='QCPreproc' \ "
echo "--subjects='<comma_separated_list_of_cases>' \ "
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
echo "mnap --subjectsfolder='<path_to_study_subjects_folder>' \ "
echo "--function='QCPreproc' \ "
echo "--subjects='<comma_separated_list_of_cases>' \ "
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

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=
# =-=-=-=-=-==-=-=-= Establish general MNAP functions and variables =-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=

# ------------------------------------------------------------------------------
#  Set exit if error is reported (turn on for debugging)
# ------------------------------------------------------------------------------

# -- Setup this script such that if any command exits with a non-zero value, the
# -- script itself exits and does not attempt any further processing.
# set -e

# ------------------------------------------------------------------------------
#  Load relevant libraries for logging and parsing options
# ------------------------------------------------------------------------------

source $HCPPIPEDIR/global/scripts/log.shlib  # -- Logging related functions
source $HCPPIPEDIR/global/scripts/opts.shlib # -- Command line option functions

# ------------------------------------------------------------------------------
#  Establish tool name for logging
# ------------------------------------------------------------------------------

log_SetToolName "mnap.sh"

# ------------------------------------------------------------------------------
#  Load Core Functions
# ------------------------------------------------------------------------------

# -- Parses the input command line for a specified command line option
# -- The first parameter is the command line option to look for.
# -- The remaining parameters are the full list of flagged command line arguments

opts_GetOpt() {
sopt="$1"
shift 1
for fn in "$@" ; do
	if [ `echo $fn | grep -- "^${sopt}=" | wc -w` -gt 0 ]; then
		echo $fn | sed "s/^${sopt}=//"
		return 0
	fi
done
}

# -- Checks command line arguments for "--help" indicating that help has been requested
opts_CheckForHelpRequest() {
for fn in "$@" ; do
	if [ "$fn" = "--help" ]; then
		return 0
	fi
done
}

# -- Checks for version
showVersion() {
	MNAPVer=`cat ${TOOLS}/${MNAPREPO}/VERSION.md`
	echo ""
	geho "    Multimodal Neuroimaging Analysis Platform (MNAP) Version: v${MNAPVer}"
}

# ------------------------------------------------------------------------------
#  Parse Command Line Options
# ------------------------------------------------------------------------------

# -- Check if general help requested in three redundant ways (AP, AP --help or AP help)
if [ "$1" == "-version" ] || [ "$1" == "version" ] || [ "$1" == "--version" ] || [ "$1" == "--v" ] || [ "$1" == "-v" ]; then
	showVersion
	echo ""
	exit 0
fi
if [ $(opts_CheckForHelpRequest $@) ]; then
	showVersion
	show_usage
	exit 0
fi
if [ -z "$1" ]; then
	showVersion
	show_usage
	exit 0
fi
if [ "$1" == "help" ]; then
	showVersion
	show_usage
	exit 0
fi

if [ "$1" == "--envsetup" ] || [ "$1" == "-envsetup" ] || [ "$1" == "envsetup" ]; then
	showVersion
	echo ""
	echo "Printing help call for $TOOLS/$MNAPREPO/library/environment/mnap_environment.sh"
	echo ""
	$TOOLS/$MNAPREPO/library/environment/mnap_environment.sh --help
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
	# -- Check for input with question mark
	if [[ "$GmriFunctionToRun" =~ .*"?".* ]] && [ -z "$2" ]; then
		# -- Set UsageInput variable to pass and remove question mark
		UsageInput=`echo ${GmriFunctionToRun} | cut -c 2-`
		# -- If no other input is provided print help
		echo ""
		show_usage_gmri
		exit 0
	fi
	# -- Check for input with flag mark
	if [[ "$GmriFunctionToRun" =~ .*"-".* ]] && [ -z "$2" ]; then
		# -- Set UsageInput variable to pass and remove question mark
		UsageInput=`echo ${GmriFunctionToRun} | cut -c 2-`
		# -- If no other input is provided print help
		echo ""
		show_usage_gmri
		exit 0
	fi
	# -- Check for input is function name with no other arguments
	if [[ "$GmriFunctionToRun" != *"-"* ]] && [ -z "$2" ]; then
		UsageInput="$GmriFunctionToRun"
		# -- If no other input is provided print help
		echo ""
		show_usage_gmri
		exit 0
	else
		# -- Otherwise pass the function with all inputs from the command line
		gmriinput="$@"
		gmriFunction
		exit 0
	fi
fi

# ------------------------------------------------------------------------------
#  Check if specific function help requested
# ------------------------------------------------------------------------------

isMNAPFunction() {
MatlabFunctionsCheck=`find $TOOLS/$MNAPREPO/matlab/ -name "*.m" | grep -v "archive/"`
if [ -z "${MNAPFunctions##*$1*}" ]; then
	return 0
elif [[ ! -z `echo $MatlabFunctionsCheck | grep "$1"` ]]; then
	MNAPMatlabFunction="$1"
	echo ""
	echo "Requested $MatlabFunction function is part of the MNAP Matlab tools. Checking usage:"
	echo ""
	${MNAPMCOMMAND} "help ${MNAPMatlabFunction},quit()"
	exit 0
else
	echo ""
	reho "ERROR: $1 -- Requested function does not exist or not supported! Refer to general usage."
	echo ""
	exit 0
fi
}

# -- Get all the functions from the usage calls

# -- Check for input with double flags
if [[ "$1" =~ .*--.* ]] && [ -z "$2" ]; then
	Usage="$1"
	# -- Check for gmri help inputs (--o --l --c)
	if [[ "$Usage" == "--o" ]]; then
		show_options_gmri
		exit 0
	fi
	if [[ "$Usage" == "--l" ]]; then
		show_commands_gmri
		exit 0
	fi
	if [[ "$Usage" == "--c" ]]; then
		show_processing_gmri
		exit 0
	fi
	UsageInput=`echo ${Usage:2}`
	# -- Check if input part of function list
	isMNAPFunction $UsageInput
	showVersion
	show_usage_"$UsageInput"
	exit 0
fi
# -- Check for input with single flags
if [[ "$1" =~ .*-.* ]] && [ -z "$2" ]; then
	Usage="$1"
	# -- Check for gmri help inputs (--o --l --c)
	if [[ "$Usage" == "-o" ]]; then
		show_options_gmri
		exit 0
	fi
	if [[ "$Usage" == "-l" ]]; then
		show_commands_gmri
		exit 0
	fi
	if [[ "$Usage" == "-c" ]]; then
		show_processing_gmri
		exit 0
	fi
	UsageInput=`echo ${Usage:1}`
	# -- Check if input part of function list
	isMNAPFunction $UsageInput
	showVersion
	show_usage_"$UsageInput"
	exit 0
fi
# -- Check for input with question mark
HelpInputUsage="$1"
if [[ ${HelpInputUsage:0:1} == "?" ]] && [ -z "$2" ]; then
	Usage="$1"
	UsageInput=`echo ${Usage} | cut -c 2-`
	# -- Check if input part of function list
	isMNAPFunction $UsageInput
	showVersion
	show_usage_"$UsageInput"
	exit 0
fi
# -- Check for input with no flags
if [ -z "$2" ]; then
	UsageInput="$1"
	# -- Check if input part of function list
	isMNAPFunction $UsageInput
	showVersion
	show_usage_"$UsageInput"
	exit 0
fi

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

# -- Check if first parameter is missing flags and parse it as FunctionToRun
if [ -z `echo "$1" | grep '-'` ]; then
	FunctionToRun="$1"
	# -- Check if single or double flags are set
	doubleflagparameter=`echo $2 | cut -c1-2`
	singleflagparameter=`echo $2 | cut -c1`
	if [ "$doubleflagparameter" == "--" ]; then
		setflag="$doubleflagparameter"
	else
		if [ "$singleflagparameter" == "-" ]; then
			setflag="$singleflagparameter"
		fi
	fi
else
	# -- Check if single or double flags are set
	doubleflag=`echo $1 | cut -c1-2`
	singleflag=`echo $1 | cut -c1`
	if [ "$doubleflag" == "--" ]; then
		setflag="$doubleflag"
	else
		if [ "$singleflag" == "-" ]; then
			setflag="$singleflag"
		fi
	fi
fi

# -- Next check if any additional flags are set
if [[ "$setflag" =~ .*-.* ]]; then
	echo ""
	# ------------------------------------------------------------------------------
	#  List of command line options across all functions
	# ------------------------------------------------------------------------------

	# -- First get function / command input (to harmonize input with gmri)
	if [ -z "$FunctionToRun" ]; then
		FunctionInput=`opts_GetOpt "${setflag}function" "$@"` # function to execute
		CommandInput=`opts_GetOpt "${setflag}command" "$@"`  # function to execute
		# -- If input name uses 'command' instead of function set that to $FunctionToRun
		if [ -z "$FunctionInput" ]; then
			FunctionToRun="$CommandInput"
		else
			FunctionToRun="$FunctionInput"
		fi
	fi
	# -- SubjectsFolder and StudyFolder input flags
	StudyFolder=`opts_GetOpt "${setflag}studyfolder" $@`       # study folder to work on
	StudyFolderPath=`opts_GetOpt "${setflag}path" $@`          # local folder to work on
	SubjectsFolder=`opts_GetOpt "${setflag}subjectsfolder" $@` # subjects folder to work on
	SubjectFolder=`opts_GetOpt "${setflag}subjectfolder"  $@`  # subjects folder to work on
	# -- Check if SubjectFolder was set (i.e. missing 's') and correct variable
	if [ -z "$SubjectFolder" ]; then
		echo "" &> /dev/null
	else
		SubjectsFolder="$SubjectFolder"
	fi
	# -- If input name uses 'command' instead of function set that to $FunctionToRun
	if [ -z "$StudyFolder" ]; then
		StudyFolder="$StudyFolderPath"
	else
		StudyFolder="$StudyFolder"
	fi
	# -- If subjects folder is missing but study folder is defined assume standard MNAP folder structure
	if [ -z "$SubjectsFolder" ]; then
		if [ -z "$StudyFolder" ]; then
		echo "" &> /dev/null
		else
			SubjectsFolder="$StudyFolder/subjects"
		fi
	fi
	# -- If study folder is missing but subjects folder is defined assume standard MNAP folder structure
	if [ -z "$StudyFolder" ]; then
		if [ -z "$SubjectsFolder" ]; then
		echo "" &> /dev/null
		else
			cd $SubjectsFolder/../ &> /dev/null
			StudyFolder=`pwd` &> /dev/null
		fi
	fi
	# -- Set additional general flags
	CASES=`opts_GetOpt "${setflag}subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
	Overwrite=`opts_GetOpt "${setflag}overwrite" $@`  # Clean prior run and starr fresh [yes/no]
	PRINTCOM=`opts_GetOpt "${setflag}printcom" $@`    # Option for printing the entire command
	Scheduler=`opts_GetOpt "${setflag}scheduler" $@`  # Specify the type of scheduler to use
	LogFolder=`opts_GetOpt "${setflag}logfolder" $@`  # Log location
	LogSave=`opts_GetOpt "${setflag}log" $@`          # Log save
	# -- If logfolder flag set then set it and set master log
	if [ -z "$LogFolder" ]; then
		MasterLogFolder="${StudyFolder}/processing/logs"
	else
		MasterLogFolder="$LogFolder"
	fi
	# -- Generate the master log, comlogs and runlogs folder
	mkdir ${MasterLogFolder}  &> /dev/null
	MasterRunLogFolder="${MasterLogFolder}/runlogs"
	MasterComlogFolder="${MasterLogFolder}/comlogs"
	mkdir ${MasterRunLogFolder}  &> /dev/null
	mkdir ${MasterComlogFolder}  &> /dev/null
	# -- If log flag set then set it
	if [ -z "$LogSave" ] || [ "$LogSave" == "yes" ]; then
		LogSave="keep"
	fi
	if [ "$LogSave" == "no" ]; then
		LogSave="remove"
	fi
	# -- If scheduler flag set then set RunMethod variable
	if [ ! -z "$Scheduler" ]; then
		RunMethod="2"
	else
		RunMethod="1"
	fi
	# -- Set flags for MNAPXNATTurnkey and XNATCloudUpload
	BATCH_PARAMETERS_FILENAME=`opts_GetOpt "${setflag}batchfile" $@`
	SCAN_MAPPING_FILENAME=`opts_GetOpt "${setflag}mappingfile" $@`
	XNAT_ACCSESSION_ID=`opts_GetOpt "${setflag}xnataccsessionid" $@`
	XNAT_SESSION_LABEL=`opts_GetOpt "${setflag}xnatsessionlabel" $@`
	XNAT_PROJECT_ID=`opts_GetOpt "${setflag}xnatprojectid" $@`
	XNAT_SUBJECT_ID=`opts_GetOpt "${setflag}xnatsubjectid" $@`
	XNAT_HOST_NAME=`opts_GetOpt "${setflag}xnathost" $@`
	XNAT_USER_NAME=`opts_GetOpt "${setflag}xnatuser" $@`
	XNAT_PASSWORD=`opts_GetOpt "${setflag}xnatpass" $@`
	ResetCredentials=`opts_GetOpt "--resetcredentials" $@`
	XNAT_SUBJECT_IDS=`opts_GetOpt "--xnatsubjectids" $@`
	NIFTIUPLOAD=`opts_GetOpt "--niftiupload" $@`
	# -- Set flags for organizeDicom parameters
	Folder=`opts_GetOpt "${setflag}folder" $@`
	Clean=`opts_GetOpt "${setflag}clean" $@`
	Unzip=`opts_GetOpt "${setflag}unzip" $@`
	Gzip=`opts_GetOpt "${setflag}gzip" $@`
	VerboseRun=`opts_GetOpt "${setflag}verbose" $@`
	Cores=`opts_GetOpt "${setflag}cores" $@`
	# -- Path options for FreeSurfer or MNAP
	FreeSurferHome=`opts_GetOpt "${setflag}hcp_freesurfer_home" $@`
	MNAPVersion=`opts_GetOpt "${setflag}version" $@`
	# -- createLists input flags
	ListGenerate=`opts_GetOpt "${setflag}listtocreate" $@`
	Append=`opts_GetOpt "${setflag}append" $@`
	ListName=`opts_GetOpt "${setflag}listname" $@`
	HeaderBatch=`opts_GetOpt "${setflag}headerbatch" $@`
	ListFunction=`opts_GetOpt "${setflag}listfunction" $@`
	BOLDS=`opts_GetOpt "${setflag}bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`
	ParcellationFile=`opts_GetOpt "${setflag}parcellationfile" $@`
	FileType=`opts_GetOpt "${setflag}filetype" $@`
	BoldSuffix=`opts_GetOpt "${setflag}boldsuffix" $@`
	SubjectHCPFile=`opts_GetOpt "${setflag}subjecthcpfile" $@`
	ListPath=`opts_GetOpt "${setflag}listpath" $@`
	# -- dataSync input flags
	NetID=`opts_GetOpt "${setflag}netid" $@`
	HCPSubjectsFolder=`opts_GetOpt "${setflag}clusterpath" $@`
	Direction=`opts_GetOpt "${setflag}dir" $@`
	ClusterName=`opts_GetOpt "${setflag}cluster" $@`
	# -- hcpdLegacy input flags
	EchoSpacing=`opts_GetOpt "${setflag}echospacing" $@`
	PEdir=`opts_GetOpt "${setflag}PEdir" $@`
	TE=`opts_GetOpt "${setflag}TE" $@`
	UnwarpDir=`opts_GetOpt "${setflag}unwarpdir" $@`
	DiffDataSuffix=`opts_GetOpt "${setflag}diffdatasuffix" $@`
	Scanner=`opts_GetOpt "${setflag}scanner" $@`
	UseFieldmap=`opts_GetOpt "${setflag}usefieldmap" $@`
	# -- BOLDParcellation input flags
	InputFile=`opts_GetOpt "${setflag}inputfile" $@`
	InputPath=`opts_GetOpt "${setflag}inputpath" $@`
	InputDataType=`opts_GetOpt "${setflag}inputdatatype" $@`
	SingleInputFile=`opts_GetOpt "${setflag}singleinputfile" $@`
	OutPath=`opts_GetOpt "${setflag}outpath" $@`
	OutName=`opts_GetOpt "${setflag}outname" $@`
	ExtractData=`opts_GetOpt "${setflag}extractdata" $@`
	ComputePConn=`opts_GetOpt "${setflag}computepconn" $@`
	UseWeights=`opts_GetOpt "${setflag}useweights" $@`
	WeightsFile=`opts_GetOpt "${setflag}useweights" $@`
	ParcellationFile=`opts_GetOpt "${setflag}parcellationfile" $@`
	# -- ROIExtract input flags
	ROIInputFile=`opts_GetOpt "${setflag}roifile" $@`
	ROIFileSubjectSpecific=`opts_GetOpt "${setflag}subjectroifile" $@`
	# -- computeBOLDfc input flags
	InputFiles=`opts_GetOpt "${setflag}inputfiles" $@`
	OutPathFC=`opts_GetOpt "${setflag}targetf" $@`
	Calculation=`opts_GetOpt "${setflag}calculation" $@`
	RunType=`opts_GetOpt "${setflag}runtype" $@`
	FileList=`opts_GetOpt "${setflag}flist" $@`
	IgnoreFrames=`opts_GetOpt "${setflag}ignore" $@`
	MaskFrames=`opts_GetOpt "${setflag}mask" "$@"`
	Covariance=`opts_GetOpt "${setflag}covariance" $@`
	TargetROI=`opts_GetOpt "${setflag}target" $@`
	RadiusSmooth=`opts_GetOpt "${setflag}rsmooth" $@`
	RadiusDilate=`opts_GetOpt "${setflag}rdilate" $@`
	GBCCommand=`opts_GetOpt "${setflag}command" $@`
	Verbose=`opts_GetOpt "${setflag}verbose" $@`
	ComputeTime=`opts_GetOpt "${setflag}-time" $@`
	VoxelStep=`opts_GetOpt "${setflag}vstep" $@`
	ROIInfo=`opts_GetOpt "${setflag}roinfo" $@`
	FCCommand=`opts_GetOpt "${setflag}options" $@`
	Method=`opts_GetOpt "${setflag}method" $@`
	# -- DWIDenseParcellation input flags
	MatrixVersion=`opts_GetOpt "${setflag}matrixversion" $@`
	ParcellationFile=`opts_GetOpt "${setflag}parcellationfile" $@`
	OutName=`opts_GetOpt "${setflag}outname" $@`
	WayTotal=`opts_GetOpt "${setflag}waytotal" $@`
	# -- DWISeedTractography input flags
	SeedFile=`opts_GetOpt "${setflag}seedfile" $@`
	# -- eddyQC input flags
	EddyBase=`opts_GetOpt "${setflag}eddybase" $@`
	EddyPath=`opts_GetOpt "${setflag}eddypath" $@`
	Report=`opts_GetOpt "${setflag}report" $@`
	BvalsFile=`opts_GetOpt "${setflag}bvalsfile" $@`
	BvecsFile=`opts_GetOpt "${setflag}bvecsfile" $@`
	EddyIdx=`opts_GetOpt "${setflag}eddyidx" $@`
	EddyParams=`opts_GetOpt "${setflag}eddyparams" $@`
	List=`opts_GetOpt "${setflag}list" $@`
	Mask=`opts_GetOpt "${setflag}mask" $@`
	GroupBar=`opts_GetOpt "${setflag}groupvar" $@`
	OutputDir=`opts_GetOpt "${setflag}outputdir" $@`
	Update=`opts_GetOpt "${setflag}update" $@`
	# -- FSLBedpostxGPU input flags
	Fibers=`opts_GetOpt "${setflag}fibers" $@`
	Model=`opts_GetOpt "${setflag}model" $@`
	Burnin=`opts_GetOpt "${setflag}burnin" $@`
	Jumps=`opts_GetOpt "${setflag}jumps" $@`
	Rician=`opts_GetOpt "${setflag}rician" $@`
	# -- probtrackxGPUDense input flags
	MatrixOne=`opts_GetOpt "${setflag}omatrix1" $@`
	MatrixThree=`opts_GetOpt "${setflag}omatrix3" $@`
	NsamplesMatrixOne=`opts_GetOpt "${setflag}nsamplesmatrix1" $@`
	NsamplesMatrixThree=`opts_GetOpt "${setflag}nsamplesmatrix3" $@`
	# -- AWSHCPSync input flags
	Modality=`opts_GetOpt "${setflag}modality" $@`
	Awsuri=`opts_GetOpt "${setflag}awsuri" $@`
	# -- QCPreproc input flags
	OutPath=`opts_GetOpt "${setflag}outpath" $@`
	TemplateFolder=`opts_GetOpt "${setflag}templatefolder" $@`
	Modality=`opts_GetOpt "${setflag}modality" $@`
	DWIPath=`opts_GetOpt "${setflag}dwipath" $@`
	DWIData=`opts_GetOpt "${setflag}dwidata" $@`
	DtiFitQC=`opts_GetOpt "${setflag}dtifitqc" $@`
	BedpostXQC=`opts_GetOpt "${setflag}bedpostxqc" $@`
	EddyQCStats=`opts_GetOpt "${setflag}eddyqcstats" $@`
	DWILegacy=`opts_GetOpt "${setflag}dwilegacy" $@`
	BOLDDATA=`opts_GetOpt "${setflag}bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDDATA=`echo "$BOLDDATA" | sed 's/,/ /g;s/|/ /g'`
	BOLDRUNS=`opts_GetOpt "${setflag}boldruns" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDRUNS=`echo "$BOLDRUNS" | sed 's/,/ /g;s/|/ /g'`
	BOLDS=`opts_GetOpt "${setflag}bolds" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`
	if [[ ! -z $BOLDDATA ]]; then
		if [[ -z $BOLDS ]]; then
			BOLDS=$BOLDDATA
		fi
	fi
	if [[ ! -z $BOLDRUNS ]]; then
		if [[ -z $BOLDS ]]; then
			BOLDS=$BOLDRUNS
		fi
	fi
	BOLDSuffix=`opts_GetOpt "${setflag}boldsuffix" $@`
	BOLDPrefix=`opts_GetOpt "${setflag}boldprefix" $@`
	SkipFrames=`opts_GetOpt "${setflag}skipframes" $@`
	SNROnly=`opts_GetOpt "${setflag}snronly" $@`
	TimeStamp=`opts_GetOpt "${setflag}timestamp" $@`
	Suffix=`opts_GetOpt "${setflag}suffix" $@`
	SceneZip=`opts_GetOpt "${setflag}scenezip" $@`
	# -- Check if subject input is a parameter file instead of list of cases
	if [[ ${CASES} == *.txt ]]; then
		SubjectParamFile="$CASES"
		echo ""
		echo "Using $SubjectParamFile for input."
		echo ""
		CASES=`more ${SubjectParamFile} | grep "id:"| cut -d " " -f 2`
	fi
fi

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-
# =-=-=-=-=-=-=-=-=-=-=-= Execute specific functions =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-

echo ""
geho "--- Running ${FunctionToRun} function"
echo ""

# ------------------------------------------------------------------------------
#  matlabHelp function
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "matlabHelp" ]; then
	${FunctionToRun}
fi

# ------------------------------------------------------------------------------
#  MNAPXNATTurnkey function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "MNAPXNATTurnkey" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$BATCH_PARAMETERS_FILENAME" ]; then reho "Error: --batchfile flag missing. Batch parameter file not specified."; exit 1; fi
	if [ -z "$SCAN_MAPPING_FILENAME" ]; then reho "Error: --mappingfile flag missing. Batch parameter file not specified."; exit 1; fi
	if [ -z "$XNAT_SESSION_LABEL" ]; then reho "Error: --xnatsessionlabel flag missing."; exit 1; fi
	if [ -z "$XNAT_PROJECT_ID" ]; then reho "Error: --xnatprojectid flag missing. Batch parameter file not specified."; exit 1; fi
	if [ -z "$XNAT_HOST_NAME" ]; then reho "Error: --xnathost flag missing. Batch parameter file not specified."; exit 1; fi
	if [ -z "$XNAT_USER_NAME" ]; then reho "Error: --xnatuser flag missing. Batch parameter file not specified."; exit 1; fi
	if [ -z "$XNAT_PASSWORD" ]; then reho "Error: --xnatpass flag missing. Batch parameter file not specified."; exit 1; fi
	if [ -z "$CASES" ]; then reho "Note: List of subjects missing. Assuming $XNAT_SESSION_LABEL matches subject names."; CASES="$XNAT_SESSION_LABEL"; fi
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun processing with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   XNAT Hostname: ${XNAT_HOST_NAME}"
	echo "   XNAT Project ID: ${XNAT_PROJECT_ID}"
	echo "   XNAT Session Label: ${XNAT_SESSION_LABEL}"
	echo "   XNAT Resource Mapping file: ${XNAT_HOST_NAME}"
	echo "   XNAT Resource Batch file: ${BATCH_PARAMETERS_FILENAME}"
	echo "   Project-specific Batch file: ${project_batch_file}"
	echo "   MNAP Study folder: ${mnap_studyfolder}"
	echo "   MNAP Subject-specific working folder: ${rawdir}"
	echo "   OVERWRITE set to: ${OVERWRITE}"
	echo "--------------------------------------------------------------"
	# -- Loop through all the cases
	for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  organizeDicom function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "organizeDicom" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then
		if [ -z "$Folder" ]; then
			reho "Error: Study folder missing and optional parameter --folder not specified."
			exit 1
		fi
	fi
	if [ -z "$SubjectsFolder" ]; then
		if [ -z "$Folder" ]; then
			reho "Error: Subjects folder missing and optiona parameter --folder not specified"
			exit 1
		fi
	fi
	if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
	if [ -z "$Overwrite" ]; then Overwrite="no"; fi
	Cluster="$RunMethod"
	if [ "$Cluster" == "2" ]; then
			if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
	fi
	# -- Optional parameters
	if [ -z "$Folder" ]; then
		Folder="$SubjectsFolder"
	else
		if [ -z "$StudyFolder" ] && [ -z "$SubjectsFolder" ]; then
			SubjectsFolder="$Folder"
			StudyFolder="../$SubjectsFolder"
		fi
	fi
	if [ -z "$Clean" ]; then Clean="yes"; echo ""; echo "--clean not specified explicitly. Setting --clean=$Clean."; echo ""; fi
	if [ -z "$Unzip" ]; then Unzip="yes"; echo ""; echo "--unzip not specified explicitly. Setting --unzip=$Unzip."; echo ""; fi
	if [ -z "$Unzip" ]; then Gzip="yes"; echo ""; echo "--gzip not specified explicitly. Setting --gzip=$Gzip."; echo ""; fi
	if [ -z "$VerboseRun" ]; then VerboseRun="True"; echo ""; echo "--verbose not specified explicitly. Proceeding --verbose=$Verbose"; echo ""; fi
	if [ -z "$Cores" ]; then Cores="4"; echo ""; echo "--cores not specified explicitly. Proceeding --cores=$Cores"; echo ""; fi

	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun processing with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	if [ -z "$Folder" ]; then
		echo "   Optional --folder parameter not set. Using standard inputs."
		echo "   Study Folder: ${StudyFolder}"
		echo "   Subject Folder: ${SubjectsFolder}"
	else
		echo "Optional --folder parameter set explicitly. "
		echo "   Setting subjects folder and study accordingly."
		echo "   Study Folder: ${StudyFolder}"
		echo "   Subject Folder: ${SubjectsFolder}"
	fi
	echo "   Subjects: ${CASES}"
	echo "   Overwrite prior run: ${Overwrite}"
	echo ""
	# Report optional parameters
	echo "   Clean NIFTI files: ${Clean}"
	echo "   Unzip DICOM files: ${Unzip}"
	echo "   Gzip DICOM files: ${Gzip}"
	echo "   Report verbose run: ${VerboseRun}"
	echo "   Cores to use: ${Cores}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo ""
	echo "--------------------------------------------------------------"
	# -- Loop through all the cases
	for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  Visual QC Images function loop - QCPreproc - wb_command based
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "QCPreproc" ]; then
	# -- Check all the user-defined parameters:
	TimeStampQCPreproc=`date +%Y-%m-%d-%H-%M-%S`
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
	if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
	if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
	if [ -z "$Modality" ]; then reho "Error:  Modality to perform QC on missing [Supported: T1w, T2w, myelin, BOLD, DWI]"; exit 1; fi
	Cluster="$RunMethod"
	if [ "$Cluster" == "2" ]; then
		if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
	fi
	if [ -z "$TemplateFolder" ]; then TemplateFolder="${TOOLS}/${MNAPREPO}/library/data/"; echo "Template folder path value not explicitly specified. Using default: ${TemplateFolder}"; fi
	if [ -z "$OutPath" ]; then OutPath="${SubjectsFolder}/QC/${Modality}"; echo "Output folder path value not explicitly specified. Using default: ${OutPath}"; fi
	if [ -z "$SceneZip" ]; then SceneZip="yes"; echo "Generation of scene zip file not explicitly provided. Using default: ${SceneZip}"; fi
	# -- DWI modality-specific settings:
	if [ "$Modality" = "DWI" ]; then
		if [ -z "$DWIPath" ]; then DWIPath="Diffusion"; echo "DWI input path not explicitly specified. Using default: ${DWIPath}"; fi
		if [ -z "$DWIData" ]; then DWIData="data"; echo "DWI data name not explicitly specified. Using default: ${DWIData}"; fi
		if [ -z "$DWILegacy" ]; then DWILegacy="no"; echo "DWI legacy not specified. Using default: ${TemplateFolder}"; fi
		if [ -z "$DtiFitQC" ]; then DtiFitQC="no"; echo "DWI dtifit QC not specified. Using default: ${DtiFitQC}"; fi
		if [ -z "$BedpostXQC" ]; then BedpostXQC="no"; echo "DWI BedpostX not specified. Using default: ${BedpostXQC}"; fi
		if [ -z "$EddyQCStats" ]; then EddyQCStats="no"; echo "DWI EDDY QC Stats not specified. Using default: ${EddyQCStats}"; fi
	fi
	# -- BOLD modality-specific settings:
	if [ "$Modality" = "BOLD" ]; then
		# - Check if BOLDS parameter is empty:
		if [ -z "$BOLDS" ]; then
			echo ""
			reho "BOLD input list not specified. Relying on subject_hcp.txt individual information files."
			BOLDS="subject_hcp.txt"
			echo ""
		fi
		if [ -z "$BOLDPrefix" ]; then BOLDPrefix=""; echo "Input BOLD Prefix not specified. Assuming no BOLD name prefix."; fi
		if [ -z "$BOLDSuffix" ]; then BOLDSuffix=""; echo "Processed BOLD Suffix not specified. Assuming no BOLD output suffix."; fi
	fi
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun processing with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   Study Folder: ${StudyFolder}"
	echo "   Subject Folder: ${SubjectsFolder}"
	echo "   Subjects: ${CASES}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "   QC Modality: ${Modality}"
	echo "   QC Output Path: ${OutPath}"
	echo "   QC Scene Template: ${TemplateFolder}"
	echo "   Overwrite prior run: ${Overwrite}"
	echo "   Zip Scene File: ${SceneZip}"
	if [ "   $Modality" = "DWI" ]; then
		echo "   DWI input path: ${DWIPath}"
		echo "   DWI input name: ${DWIData}"
		echo "   DWI legacy processing: ${DWILegacy}"
		echo "   DWI dtifit QC requested: ${DtiFitQC}"
		echo "   DWI bedpostX QC requested: ${BedpostXQC}"
		echo "   DWI EDDY QC Stats requested: ${EddyQCStats}"
	fi
	if [ "$Modality" = "BOLD" ]; then
		echo "   BOLD data input: ${BOLDS}"
		echo "   BOLD Prefix: ${BOLDPrefix}"
		echo "   BOLD Suffix: ${BOLDSuffix}"
		echo "   Skip Initial Frames: ${SkipFrames}"
		echo "   Compute SNR Only: ${SNROnly}"
		if [ "$SNROnly" == "yes" ]; then echo ""; echo "   BOLD SNR only specified. Will skip QC images"; echo ""; fi
	fi
	echo "--------------------------------------------------------------"
	# -- Loop through all the cases
	for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  eddyQC function loop - eddyqc - uses EDDY QC by Matteo Bastiani, FMRIB
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "eddyQC" ]; then
	#unset EddyPath
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
	if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
	if [ -z "$Report" ]; then reho "Error: Report type missing"; exit 1; fi
	# -- Perform checks for individual run
	if [ "$Report" == "individual" ]; then
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$EddyBase" ]; then reho "Eddy base input name missing"; exit 1; fi
		if [ -z "$BvalsFile" ]; then reho "BVALS file missing"; exit 1; fi
		if [ -z "$EddyIdx" ]; then reho "Eddy index missing"; exit 1; fi
		if [ -z "$EddyParams" ]; then reho "Eddy parameters missing"; exit 1; fi
		if [ -z "$Mask" ]; then reho "Error: Mask missing"; exit 1; fi
		if [ -z "$BvecsFile" ]; then BvecsFile=""; fi
	fi
	# -- Perform checks for group run
	if [ "$Report" == "group" ]; then
		if [ -z "$List" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$Update" ]; then Update="false"; fi
		if [ -z "$GroupVar" ]; then GroupVar=""; fi
	fi
	# -- Check if cluster options are set
	Cluster="$RunMethod"
	if [ "$Cluster" == "2" ]; then
			if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
	fi
	# -- Loop through cases for an individual run call
	if [ ${Report} == "individual" ]; then
		for CASE in ${CASES}; do
			# -- Check in/out paths
			if [ -z ${EddyPath} ]; then
				reho "Eddy path not set. Assuming defaults."
				EddyPath="${SubjectsFolder}/${CASE}/hcp/${CASE}/Diffusion/eddy"
			else
				EddyPath="${SubjectsFolder}/${CASE}/hcp/${CASE}/$EddyPath"
				echo $EddyPath
			fi
			if [ -z ${OutputDir} ]; then
				reho "Output folder not set. Assuming defaults."
				OutputDir="${EddyPath}/${EddyBase}.qc"
			fi
			# -- Report individual parameters
			echo ""
			echo "Running $FunctionToRun processing with the following parameters:"
			echo ""
			echo "--------------------------------------------------------------"
			echo "   StudyFolder: ${StudyFolder}"
			echo "   Subjects Folder: ${SubjectsFolder}"
			echo "   Subject: ${CASE}"
			echo "   Study Log Folder: ${MasterLogFolder}"
			echo "   Report Type: ${Report}"
			echo "   Eddy QC Input Path: ${EddyPath}"
			echo "   Eddy QC Output Path: ${OutputDir}"
			echo "   Eddy Inputs Base Name: ${EddyBase}"
			echo "   Mask: ${EddyPath}/${Mask}"
			echo "   BVALS file: ${EddyPath}/${BvalsFile}"
			echo "   Eddy Index file: ${EddyPath}/${EddyIdx}"
			echo "   Eddy parameter file: ${EddyPath}/${EddyParams}"
			# Report optional parameters
			echo "   BvecsFile: ${EddyPath}/${BvecsFile}"
			echo "   Overwrite: ${EddyPath}/${Overwrite}"
			echo "--------------------------------------------------------------"
			# -- Execute function
			${FunctionToRun} ${CASE}
		done
	fi
	# -- Check if group call specified
	if [ ${Report} == "group" ]; then
		# -- Report group parameters
		echo ""
		echo "Running $FunctionToRun processing with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "   Study Folder: ${StudyFolder}"
		echo "   Subjects Folder: ${SubjectsFolder}"
		echo "   Study Log Folder: ${MasterLogFolder}"
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
#  mapHCPFiles function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "mapHCPFiles" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
	if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
	if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
	Cluster="$RunMethod"
	if [ "$Cluster" == "2" ]; then
			if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
	fi
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun processing with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "Study Folder: ${StudyFolder}"
	echo "Subjects Folder: ${SubjectsFolder}"
	echo "Subjects: ${CASES}"
	echo "Study Log Folder: ${MasterLogFolder}"
	echo "--------------------------------------------------------------"
	echo ""
	for CASE in ${CASES}; do
		echo "--> Ensuring that and correct subjects_hcp.txt files is generated..."; echo ""
		if [ -f ${SubjectsFolder}/${CASE}/subject_hcp.txt ]; then
			echo "--> ${SubjectsFolder}/${CASE}/subject_hcp.txt found"
			echo ""
			${FunctionToRun} ${CASE}
		else
			echo "--> ${SubjectsFolder}/${CASE}/subject_hcp.txt is missing - please setup the subject.txt files and re-run function."
		fi
	done
fi

# ------------------------------------------------------------------------------
#  dataSync function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "dataSync" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
	if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
	if [ -z "$CASES" ]; then reho "Specific subjects not provided"; fi
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun processing with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   Study Folder: ${StudyFolder}"
	echo "   Subjects Folder: ${SubjectsFolder}"
	echo "   Subjects: ${CASES}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "--------------------------------------------------------------"
	echo ""
	# -- Loop through all the cases
	for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  createLists function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "createLists" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
	if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
	if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
	if [ -z "$ListGenerate" ]; then reho "Error: Type of list to generate missing [batch, analysis, snr]"; exit 1; fi
	# -- Check optional parameters:
	if [ -z "$Append" ]; then Append="no"; reho "    Setting --append='no' by default"; echo ""; fi
	# -- Set list path if not set by user
	if [ -z "$ListPath" ]; then
		unset ListPath
		mkdir ${StudyFolder}/processing/lists &> /dev/null
		cd ${StudyFolder}/processing/lists
		ListPath=`pwd`
		reho "    Setting default path for list folder --> $ListPath"; echo ""
		export ListPath
	else
		export ListPath
	fi
	# --------------------------
	# --- preprocessing loop ---
	# --------------------------
	if [ "$ListGenerate" == "batch" ]; then
		# -- Check of overwrite flag was set
		if [ "$Overwrite" == "yes" ]; then
			echo ""
			reho "===> Deleting prior batch processing files"
			echo ""
			rm "$ListPath"/batch."$ListName".txt &> /dev/null
		fi
		if [ -z "$ListFunction" ]; then
			reho "    List function not set. Using default function."
			ListFunction="        ${TOOLS}/${MNAPREPO}/connector/functions/SubjectsParamList.sh"
			reho "$ListFunction"
			echo ""
		fi
		TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
		if [ -z "$ListName" ]; then
			ListName="$TimeStamp"
			reho "    Name of batch preprocessing file not specified. Using defaults with timestamp to avoid overwriting: $ListName"
		fi
		if [ -z "$HeaderBatch" ]; then
			echo ""
			reho "    Batch parameter header file not specified. Using defaults for multi-band data: "
			HeaderBatch="${TOOLS}/${MNAPREPO}/library/data/templates/batch_multiband_parameters.txt"
			if [ -f $HeaderBatch ]; then
				reho "        $HeaderBatch"; echo ""
			else
				reho "---> ERROR: $HeaderBatch not found! Check MNAP environment variables."
				echo ""
				exit 1
			fi
		fi
		# -- Check if skipping parameter file header
		if [ "$HeaderBatch" != "no" ]; then
			# -- Check if lists exists
			if [ -s ${ListPath}/batch."$ListName".txt ]; then
				# -- If HeaderBatch was set and file exists then exit and report error
				echo ""
				reho "---------------------------------------------------------------------"
				reho "--> The file exists and you are trying to set the header again"
				reho "--> Check usage to append the file or overwrite it."
				reho "---------------------------------------------------------------------"
				echo ""
				exit 1
			else
				cat ${HeaderBatch} >> ${ListPath}/batch."$ListName".txt
			fi
		fi
		# -- Report parameters
		echo ""
		echo "Running $FunctionToRun processing with the following parameters:"
		echo ""
		echo "--------------------------------------------------------------"
		echo "   Study Folder: ${StudyFolder}"
		echo "   Subjects Folder: ${SubjectsFolder}"
		echo "   Subjects: ${CASES}"
		echo "   Study Log Folder: ${MasterLogFolder}"
		echo "   List to generate: ${ListGenerate}"
		echo "   List path: ${ListPath}"
		echo "   List name: ${ListName}"
		echo "   Scheduler Name and Options: $Scheduler"
		echo "   Overwrite prior run: $Overwrite"
		echo "--------------------------------------------------------------"
		echo ""
		# -- Loop through all the cases
		for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
		echo ""
		geho "-------------------------------------------------------------------------------------------"
		geho "--> Check output:"
		geho "  `ls ${ListPath}/batch.${ListName}.txt `"
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
			rm ${ListPath}/analysis."$ListName".*.list &> /dev/null
		fi
			# -- Report parameters
			echo ""
			echo "Running $FunctionToRun processing with the following parameters:"
			echo ""
			echo "--------------------------------------------------------------"
			echo "   Study Folder: ${StudyFolder}"
			echo "   Subjects Folder: ${SubjectsFolder}"
			echo "   Subjects: ${CASES}"
			echo "   Study Log Folder: ${MasterLogFolder}"
			echo "   List to generate: ${ListGenerate}"
			echo "   Scheduler Name and Options: $Scheduler"
			echo "   Overwrite prior run: $Overwrite"
			echo "--------------------------------------------------------------"
			echo ""
			# -- Loop through all the cases
			for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
	fi
fi

# ------------------------------------------------------------------------------
#  printMatrix function loop -- under development
# ------------------------------------------------------------------------------

## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri #  FIXICA function loop
## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri
## -- FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "FIXICA" ]; then
## -- FIXICA Code - integrate into gmri 	echo "Note: Expects that minimally processed NIFTI & CIFTI BOLDs"
## -- FIXICA Code - integrate into gmri 	echo ""
## -- FIXICA Code - integrate into gmri 	echo "Overwrite existing run [yes, no]:"
## -- FIXICA Code - integrate into gmri 		if read answer; then
## -- FIXICA Code - integrate into gmri 		Overwrite=$answer
## -- FIXICA Code - integrate into gmri 		fi
## -- FIXICA Code - integrate into gmri 	echo "Enter BOLD numbers you want to run FIX ICA on - e.g. 1 2 3 or 1_3 for merged BOLDs:"
## -- FIXICA Code - integrate into gmri 		if read answer; then
## -- FIXICA Code - integrate into gmri 		BOLDS=$answer
## -- FIXICA Code - integrate into gmri 				for CASE in ${CASES}
## -- FIXICA Code - integrate into gmri 				do
## -- FIXICA Code - integrate into gmri   					"$FunctionToRunInt" ${CASE}
## -- FIXICA Code - integrate into gmri   				done
## -- FIXICA Code - integrate into gmri   		fi
## -- FIXICA Code - integrate into gmri fi

## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri #  postFIXICA function loop
## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri
## -- FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "postFIXICA" ]; then
## -- FIXICA Code - integrate into gmri 	echo "Note: This function depends on fsl, wb_command and matlab and expects startup.m to point to wb_command and fsl."
## -- FIXICA Code - integrate into gmri 	echo ""
## -- FIXICA Code - integrate into gmri 	echo "Overwrite existing postFIXICA scenes [yes, no]:"
## -- FIXICA Code - integrate into gmri 		if read answer; then
## -- FIXICA Code - integrate into gmri 		Overwrite=$answer
## -- FIXICA Code - integrate into gmri 		fi
## -- FIXICA Code - integrate into gmri 	echo "Enter BOLD numbers you want to run PostFix.sh on [e.g. 1 2 3]:"
## -- FIXICA Code - integrate into gmri 		if read answer; then
## -- FIXICA Code - integrate into gmri 		BOLDS=$answer
## -- FIXICA Code - integrate into gmri 			echo "Enter high pass filter used for FIX ICA [e.g. 2000]"
## -- FIXICA Code - integrate into gmri 				if read answer; then
## -- FIXICA Code - integrate into gmri 				HighPass=$answer
## -- FIXICA Code - integrate into gmri 					for CASE in ${CASES}
## -- FIXICA Code - integrate into gmri 					do
## -- FIXICA Code - integrate into gmri   						"$FunctionToRunInt" ${CASE}
## -- FIXICA Code - integrate into gmri   					done
## -- FIXICA Code - integrate into gmri   				fi
## -- FIXICA Code - integrate into gmri   		fi
## -- FIXICA Code - integrate into gmri fi

## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri #  boldseparateciftiFIXICA function loop
## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri
## -- FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "boldseparateciftiFIXICA" ]; then
## -- FIXICA Code - integrate into gmri 	echo "Enter which study and data you want to separate"
## -- FIXICA Code - integrate into gmri 	echo "supported: 1_4_raw 5_8_raw 10_13_raw 14_17_raw"
## -- FIXICA Code - integrate into gmri 			if read answer; then
## -- FIXICA Code - integrate into gmri 			DatatoSeparate=$answer
## -- FIXICA Code - integrate into gmri 					for CASE in ${CASES}
## -- FIXICA Code - integrate into gmri 					do
## -- FIXICA Code - integrate into gmri   						"$FunctionToRunInt" ${CASE}
## -- FIXICA Code - integrate into gmri   					done
## -- FIXICA Code - integrate into gmri   			fi
## -- FIXICA Code - integrate into gmri fi

## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri #  BOLDHardLinkFIXICA function loop
## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri
## -- FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "BOLDHardLinkFIXICA" ]; then
## -- FIXICA Code - integrate into gmri 	echo "Enter BOLD numbers you want to generate connectivity hard links for [e.g. 1 2 3 or 1_3 for merged BOLDs]:"
## -- FIXICA Code - integrate into gmri 		if read answer; then
## -- FIXICA Code - integrate into gmri 		BOLDS=$answer
## -- FIXICA Code - integrate into gmri 			for CASE in ${CASES}
## -- FIXICA Code - integrate into gmri 				do
## -- FIXICA Code - integrate into gmri   				"$FunctionToRunInt" ${CASE}
## -- FIXICA Code - integrate into gmri   			done
## -- FIXICA Code - integrate into gmri   		fi
## -- FIXICA Code - integrate into gmri fi
## -- FIXICA Code - integrate into gmri
## -- FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "boldhardlinkFIXICAmerged" ]; then
## -- FIXICA Code - integrate into gmri 				for CASE in ${CASES}
## -- FIXICA Code - integrate into gmri 				do
## -- FIXICA Code - integrate into gmri   					"$FunctionToRunInt" ${CASE}
## -- FIXICA Code - integrate into gmri   				done
## -- FIXICA Code - integrate into gmri fi
## -- FIXICA Code - integrate into gmri

## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri #  FIXICAInsertMean function loop
## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri
## -- FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "FIXICAInsertMean" ]; then
## -- FIXICA Code - integrate into gmri 	echo "Note: This function will insert mean images into FIX ICA files"
## -- FIXICA Code - integrate into gmri 	echo "Enter BOLD numbers you want to run mean insertion on [e.g. 1 2 3]:"
## -- FIXICA Code - integrate into gmri 		if read answer; then
## -- FIXICA Code - integrate into gmri 		BOLDS=$answer
## -- FIXICA Code - integrate into gmri 				for CASE in ${CASES}
## -- FIXICA Code - integrate into gmri 				do
## -- FIXICA Code - integrate into gmri   					"$FunctionToRunInt" ${CASE}
## -- FIXICA Code - integrate into gmri   				done
## -- FIXICA Code - integrate into gmri   		fi
## -- FIXICA Code - integrate into gmri fi

## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri #  FIXICARemoveMean function loop
## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri
## -- FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "FIXICARemoveMean" ]; then
## -- FIXICA Code - integrate into gmri 	echo "Note: This function will remove mean from mapped FIX ICA files and save new images"
## -- FIXICA Code - integrate into gmri 	echo "Enter BOLD numbers you want to run mean removal on [e.g. 1 2 3]:"
## -- FIXICA Code - integrate into gmri 		if read answer; then
## -- FIXICA Code - integrate into gmri 		BOLDS=$answer
## -- FIXICA Code - integrate into gmri 				for CASE in ${CASES}
## -- FIXICA Code - integrate into gmri 				do
## -- FIXICA Code - integrate into gmri   					"$FunctionToRunInt" ${CASE}
## -- FIXICA Code - integrate into gmri   				done
## -- FIXICA Code - integrate into gmri   		fi
## -- FIXICA Code - integrate into gmri fi

## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri #  linkMovement function loop
## -- FIXICA Code - integrate into gmri # ------------------------------------------------------------------------------
## -- FIXICA Code - integrate into gmri
## -- FIXICA Code - integrate into gmri if [ "$FunctionToRunInt" == "linkMovement" ]; then
## -- FIXICA Code - integrate into gmri 	echo "Enter BOLD numbers you want to link [e.g. 1 2 3 or 1-3 for merged BOLDs]:"
## -- FIXICA Code - integrate into gmri 		if read answer; then
## -- FIXICA Code - integrate into gmri 		BOLDS=$answer
## -- FIXICA Code - integrate into gmri 			for CASE in ${CASES}
## -- FIXICA Code - integrate into gmri 			do
## -- FIXICA Code - integrate into gmri   				"$FunctionToRunInt" ${CASE}
## -- FIXICA Code - integrate into gmri   			done
## -- FIXICA Code - integrate into gmri   		fi
## -- FIXICA Code - integrate into gmri fi

# ------------------------------------------------------------------------------
#  BOLDDense function loop  -- under development
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
#  FSLDtifit function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "FSLDtifit" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
	if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
	if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
	Cluster="$RunMethod"
	if [ "$Cluster" == "2" ]; then
		if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
	fi
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun processing with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   Study Folder: ${StudyFolder}"
	echo "   Subjects Folder: ${SubjectsFolder}"
	echo "   Subjects: ${CASES}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "   Scheduler Name and Options: $Scheduler"
	echo "   Overwrite prior run: $Overwrite"
	echo "--------------------------------------------------------------"
	echo ""
	# -- Loop through all the cases
	for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  FSLBedpostxGPU function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "FSLBedpostxGPU" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study Folder missing"; exit 1; fi
	if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
	if [ -z "$Fibers" ]; then reho "Error: Fibers value missing"; exit 1; fi
	if [ -z "$Model" ]; then reho "Error: Model value missing"; exit 1; fi
	if [ -z "$Burnin" ]; then reho "Error: Burnin value missing"; exit 1; fi
	if [ -z "$Rician" ]; then reho "Note: Rician flag missing. Setting to default --> YES"; Rician="YES"; fi
	Cluster=$RunMethod
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun processing with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   Study Folder: ${StudyFolder}"
	echo "   Subjects Folder: ${SubjectsFolder}"
	echo "   Subjects: ${CASES}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "   Number of Fibers: $Fibers"
	echo "   Model Type: $Model"
	echo "   Burnin Period: $Burnin"
	echo "   Rician flag: $Rician"
	echo "   EPI Unwarp Direction: $UnwarpDir"
	echo "   Scheduler Name and Options: $Scheduler"
	echo "   Overwrite prior run: $Overwrite"
	echo "--------------------------------------------------------------"
	echo ""
	# -- Loop through all the cases
	for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  Diffusion legacy processing function loop (hcpdLegacy)
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "hcpdLegacy" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$Scanner" ]; then reho "Error: Scanner manufacturer missing"; exit 1; fi
	if [ -z "$UseFieldmap" ]; then reho "Error: UseFieldmap yes/no specification missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
	if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
	if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
	if [ -z "$DiffDataSuffix" ]; then reho "Error: Diffusion Data Suffix Name missing"; exit 1; fi
	if [ ${UseFieldmap} == "yes" ]; then
		if [ -z "$TE" ]; then reho "Error: TE value for Fieldmap missing"; exit 1; fi
	elif [ ${UseFieldmap} == "no" ]; then
		reho "Note: Processing without FieldMap (TE option not needed)"
	fi
	Cluster="$RunMethod"
	if [ "$Cluster" == "2" ]; then
			if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
	fi
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   Study Folder: ${StudyFolder}"
	echo "   Subjects Folder: ${SubjectsFolder}"
	echo "   Subjects: ${CASES}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "   Scanner: $Scanner"
	echo "   Using FieldMap: $UseFieldmap"
	echo "   Echo Spacing: $EchoSpacing"
	echo "   Phase Encoding Direction: $PEdir"
	echo "   TE value for Fieldmap: $TE"
	echo "   EPI Unwarp Direction: $UnwarpDir"
	echo "   Diffusion Data Suffix Name: $DiffDataSuffix"
	echo "   Overwrite prior run: $Overwrite"
	echo "--------------------------------------------------------------"
	echo ""
	# -- Loop through all the cases
	for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  structuralParcellation function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "structuralParcellation" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
	if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
	if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
	if [ -z "$InputDataType" ]; then reho "Error: Input data type value missing"; exit 1; fi
	if [ -z "$OutName" ]; then reho "Error: Output file name value missing"; exit 1; fi
	if [ -z "$ParcellationFile" ]; then reho "Error: File to use for parcellation missing"; exit 1; fi
	Cluster="$RunMethod"
	if [ "$Cluster" == "2" ]; then
			if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
	fi
	# -- Check optional parameters if not specified
	if [ -z "$ExtractData" ]; then ExtractData="no"; fi
	if [ -z "$Overwrite" ]; then Overwrite="no"; fi
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   Study Folder: ${StudyFolder}"
	echo "   Subjects Folder: ${SubjectsFolder}"
	echo "   Subjects: ${CASES}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "   ParcellationFile: ${ParcellationFile}"
	echo "   Parcellated Data Output Name: ${OutName}"
	echo "   Input Data Type: ${InputDataType}"
	echo "   Extract data in CSV format: ${ExtractData}"
	echo "   Overwrite prior run: ${Overwrite}"
	echo "--------------------------------------------------------------"
	echo ""
	# -- Loop through all the cases
	for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  computeBOLDfc function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "computeBOLDfc" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$Calculation" ]; then reho "Error: Type of calculation to run (gbc or seed) missing"; exit 1; fi
	if [ -z "$RunType" ]; then reho "Error: Type of run (group or individual) missing"; exit 1; fi
	if [ ${RunType} == "list" ]; then
		if [ -z "$FileList" ]; then reho "Error: Group file list missing"; exit 1; fi
	fi
	if [ ${RunType} == "individual" ] || [ ${RunType} == "group" ]; then
		if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
		if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$InputFiles" ]; then reho "Error: Input file(s) value missing"; exit 1; fi
		if [ -z "$OutName" ]; then reho "Error: Output file name value missing"; exit 1; fi
		if [ ${RunType} == "individual" ]; then
		    if [ -z "$InputPath" ]; then echo ""; reho "Warning: Input path value missing. Assuming individual folder structure for output: ${SubjectsFolder}/${CASE}/images/functional"; InputPath="${SubjectsFolder}/${CASE}/images/functional"; fi
			if [ -z "$OutPathFC" ]; then echo ""; reho "Warning: Output path value missing. Assuming individual folder structure for output: ${SubjectsFolder}/${CASE}/images/functional"; OutPathFC="${SubjectsFolder}/${CASE}/images/functional"; fi
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
	# -- Check optional parameters if not specified
	if [ -z "$IgnoreFrames" ]; then IgnoreFrames=""; fi
	if [ -z "$MaskFrames" ]; then MaskFrames=""; fi
	if [ -z "$Covariance" ]; then Covariance=""; fi
	if [ -z "$ExtractData" ]; then ExtractData="no"; fi
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "   Output Path: ${OutPathFC}"
	echo "   Extract data in CSV format: ${ExtractData}"
	echo "   Type of fc calculation: ${Calculation}"
	echo "   Type of run: ${RunType}"
	echo "   Ignore frames: ${IgnoreFrames}"
	echo "   Mask out frames: ${MaskFrames}"
	echo "   Calculate Covariance: ${Covariance}"
	if [ ${RunType} == "list" ]; then
		echo "   FileList: ${FileList}"
	fi
	if [ ${RunType} == "individual" ] || [ ${RunType} == "group" ]; then
		echo "   Study Folder: ${StudyFolder}"
		echo "   Subjects Folder: ${SubjectsFolder}"
		echo "   Subjects: ${CASES}"
		echo "   Input Files: ${InputFiles}"
		echo "   Input Path for Data: ${SubjectFolder}/<subject_id>/${InputPath}"
		echo "   Output Name: ${OutName}"
	fi
	if [ ${Calculation} == "gbc" ]; then
		echo "   Target ROI for GBC: ${TargetROI}"
		echo "   Radius Smooth for GBC: ${RadiusSmooth}"
		echo "   Radius Dilate for GBC: ${RadiusDilate}"
		echo "   GBC Commands to run: ${GBCCommand}"
		echo "   Verbose outout: ${Verbose}"
		echo "   Print Compute Time: ${ComputeTime}"
		echo "   Voxel Steps to use: ${VoxelStep}"
	fi
	if [ ${Calculation} == "seed" ]; then
		echo "   ROI Information for seed fc: ${ROIInfo}"
		echo "   FC Commands to run: ${FCCommand}"
		echo "   Method to compute fc: ${Method}"
	fi
	echo "--------------------------------------------------------------"
	echo ""
	if [ ${RunType} == "individual" ]; then
		for CASE in ${CASES}; do
			${FunctionToRun} ${CASE}
		done
	fi
	if [ ${RunType} == "group" ]; then
		CASE=`echo "$CASES" | sed 's/ /,/g'`
		echo $CASE
		${FunctionToRun} ${CASE}
	fi
	if [ ${RunType} == "list" ]; then
		${FunctionToRun}
	fi
fi

# ------------------------------------------------------------------------------
#  BOLDParcellation function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "BOLDParcellation" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$InputPath" ]; then reho "Error: Input path value missing"; exit 1; fi
	if [ -z "$InputDataType" ]; then reho "Error: Input data type value missing"; exit 1; fi
	if [ -z "$OutPath" ]; then reho "Error: Output path value missing"; exit 1; fi
	if [ -z "$OutName" ]; then reho "Error: Output file name value missing"; exit 1; fi
	if [ -z "$ParcellationFile" ]; then reho "Error: File to use for parcellation missing"; exit 1; fi
	Cluster="$RunMethod"
	if [ "$Cluster" == "2" ]; then
			if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
	fi
	# -- Check optional parameters if not specified
	if [ -z "$UseWeights" ]; then UseWeights="no"; fi
	if [ -z "$ComputePConn" ]; then ComputePConn="no"; fi
	if [ -z "$WeightsFile" ]; then WeightsFile="no"; fi
	if [ -z "$ExtractData" ]; then ExtractData="no"; fi
	if [ -z "$SingleInputFile" ]; then SingleInputFile="";
		if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
		if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
		if [ -z "$InputFile" ]; then reho "Error: Input file value missing"; exit 1; fi
	fi
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   Study Folder: ${StudyFolder}"
	echo "   Subjects Folder: ${SubjectsFolder}"
	echo "   Subjects: ${CASES}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "   Input File: ${InputFile}"
	echo "   Input Path: ${InputPath}"
	echo "   Single Input File: ${SingleInputFile}"
	echo "   ParcellationFile: ${ParcellationFile}"
	echo "   BOLD Parcellated Connectome Output Name: ${OutName}"
	echo "   BOLD Parcellated Connectome Output Path: ${OutPath}"
	echo "   Input Data Type: ${InputDataType}"
	echo "   Compute PConn File: ${ComputePConn}"
	echo "   Weights file specified to omit certain frames: ${UseWeights}"
	echo "   Weights file name: ${WeightsFile}"
	echo "   Extract data in CSV format: ${ExtractData}"
	echo "   Overwrite prior run: ${Overwrite}"
	echo "--------------------------------------------------------------"
	echo ""
	if [ -z "$SingleInputFile" ]; then SingleInputFile="";
		# -- Loop through all the cases
		for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
	else
		# -- Execute on single case
		${FunctionToRun} ${CASE}
	fi
fi

# ------------------------------------------------------------------------------
#  DWIDenseParcellation function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "DWIDenseParcellation" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
	if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
	if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
	if [ -z "$MatrixVersion" ]; then reho "Error: Matrix version value missing"; exit 1; fi
	if [ -z "$ParcellationFile" ]; then reho "Error: File to use for parcellation missing"; exit 1; fi
	if [ -z "$OutName" ]; then reho "Error: Name of output pconn file missing"; exit 1; fi
	Cluster="$RunMethod"
	if [ "$Cluster" == "2" ]; then
			if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
	fi
	if [ -z "$WayTotal" ]; then reho "--waytotal normalized data not specified. Assuming default [no]"; fi
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   Study Folder: ${StudyFolder}"
	echo "   Subjects Folder: ${SubjectsFolder}"
	echo "   Subjects: ${CASES}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "   Matrix version used for input: $MatrixVersion"
	echo "   File to use for parcellation: $ParcellationFile"
	echo "   Dense DWI Parcellated Connectome Output Name: $OutName"
	echo "   Waytotal normalization: ${WayTotal}"
	echo "   Overwrite prior run: $Overwrite"
	echo "--------------------------------------------------------------"
	echo ""
	# -- Loop through all the cases
	for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  ROIExtract function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "ROIExtract" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$OutPath" ]; then reho "Error: Output path value missing"; exit 1; fi
	if [ -z "$OutName" ]; then reho "Error: Output file name value missing"; exit 1; fi
	if [ -z "$ROIInputFile" ]; then reho "Error: File to use for ROI extraction missing"; exit 1; fi
	Cluster="$RunMethod"
	if [ "$Cluster" == "2" ]; then
			if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
	fi
	# -- Check optional parameters if not specified
	if [ -z "$ROIFileSubjectSpecific" ]; then ROIFileSubjectSpecific="no"; fi
	if [ -z "$Overwrite" ]; then Overwrite="no"; fi
	if [ -z "$SingleInputFile" ]; then SingleInputFile="";
		if [ -z "$InputFile" ]; then reho "Error: Input file path value missing"; exit 1; fi
		if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
		if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
		if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
	fi
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun with the following parameters:"
	echo ""
	echo "   --------------------------------------------------------------"
	echo "   Study Folder: ${StudyFolder}"
	echo "   Subjects Folder: ${SubjectsFolder}"
	echo "   Subjects: ${CASES}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "   Input File: ${InputFile}"
	echo "   Output File Name: ${OutName}"
	echo "   Single Input File: ${SingleInputFile}"
	echo "   ROI File: ${ROIInputFile}"
	echo "   Subject specific ROI file set: ${ROIFileSubjectSpecific}"
	echo "   Overwrite prior run: ${Overwrite}"
	echo "--------------------------------------------------------------"
	echo ""
	if [ -z "$SingleInputFile" ]; then SingleInputFile="";
		# -- Loop through all the cases
		for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
	else
		# -- Execute on single input file
		${FunctionToRun}
	fi
fi

# ------------------------------------------------------------------------------
#  DWISeedTractography function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "DWISeedTractography" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
	if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
	if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
	if [ -z "$MatrixVersion" ]; then reho "Error: Matrix version value missing"; exit 1; fi
	if [ -z "$SeedFile" ]; then reho "Error: File to use for seed reduction missing"; exit 1; fi	
	if [ -z "$OutName" ]; then reho "Error: Name of output pconn file missing"; exit 1; fi
	Cluster="$RunMethod"
	if [ "$Cluster" == "2" ]; then
			if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
	fi
	if [ -z "$WayTotal" ]; then WayTotal="no"; reho "--waytotal normalized data not specified. Assuming default [no]"; fi
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   Study Folder: ${StudyFolder}"
	echo "   Subjects Folder: ${SubjectsFolder}"
	echo "   Subjects: ${CASES}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "   Matrix version used for input: $MatrixVersion"
	echo "   Dense dconn seed reduction: $SeedFile"
	echo "   Dense DWI Parcellated Connectome Output Name: $OutName"
	echo "   Waytotal normalization: ${WayTotal}"
	echo "   Overwrite prior run: $Overwrite"
	echo "--------------------------------------------------------------"
	echo ""
	# -- Loop through all the cases
	for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  autoPtx function loop --> NEED TO CODE
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
#  pretractographyDense function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "pretractographyDense" ]; then
	# -- Check all the user-defined parameters:
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
	if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
	if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
	Cluster="$RunMethod"
	if [ "$Cluster" == "2" ]; then
		if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
	fi
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   Study Folder: ${StudyFolder}"
	echo "   Subjects Folder: ${SubjectsFolder}"
	echo "   Subjects: ${CASES}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "--------------------------------------------------------------"
	echo ""
	for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  probtrackxGPUDense function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "probtrackxGPUDense" ]; then
	# Check all the user-defined parameters: 1.QUEUE, 2. Scheduler, 3. Matrix1, 4. Matrix2
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
	if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
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
	# -- Report parameters
	echo ""
	echo "Running $FunctionToRun with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   Study Folder: ${StudyFolder}"
	echo "   Subjects Folder: ${SubjectsFolder}"
	echo "   Subjects: ${CASES}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "   Scheduler: ${Scheduler}"
	echo "   Compute Matrix1: ${MatrixOne}"
	echo "   Compute Matrix3: ${MatrixThree}"
	echo "   Number of samples for Matrix1: ${NsamplesMatrixOne}"
	echo "   Number of samples for Matrix3: ${NsamplesMatrixThree}"
	echo "   Overwrite prior run: ${Overwrite}"
	echo "--------------------------------------------------------------"
	echo ""
	# -- Loop through all the cases
	for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  AWSHCPSync - AWS S3 Sync command wrapper
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "AWSHCPSync" ]; then
	# Check all the user-defined parameters: 1. Modality, 2. Awsuri, 3. RunMethod
	if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
	if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
	if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
	if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
	if [ -z "$Modality" ]; then reho "Error: Modality option [e.g. MEG, MNINonLinear, T1w] missing"; exit 1; fi
	if [ -z "$Awsuri" ]; then reho "Error: AWS URI option [e.g. /hcp-openaccess/HCP_900] missing"; exit 1; fi
	echo ""
	echo "Running $FunctionToRun with the following parameters:"
	echo ""
	echo "--------------------------------------------------------------"
	echo "   Study Folder: ${StudyFolder}"
	echo "   Subjects Folder: ${SubjectsFolder}"
	echo "   Subjects: ${CASES}"
	echo "   Study Log Folder: ${MasterLogFolder}"
	echo "   Run Method: $RunMethod"
	echo "   Modality: $Modality"
	echo "   AWS URI Path: $Awsuri"
	echo "--------------------------------------------------------------"
	echo ""
	# -- Loop through all the cases
	for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi
