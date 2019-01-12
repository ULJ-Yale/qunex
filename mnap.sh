#!/bin/bash
#
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

MNAPFunctions="matlabHelp gmriFunction organizeDicom mapHCPFiles createLists dataSync linkmovement hcpdLegacy eddyQC DWIDenseParcellation DWISeedTractography computeBOLDfc structuralParcellation BOLDParcellation ICAFIXhcp ROIExtract FSLDtifit FSLBedpostxGPU autoPtx pretractographyDense ProbtrackxGPUDense AWSHCPSync QCnifti QCPreproc runTurnkey commandExecute showVersion environment"

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
echo " runTurnkey ...... turnkey execution of MNAP workflow compatible with XNAT Docker engine"
echo ""
echo "QC functions"
echo "------------"
echo " eddyQC ...... run quality control on diffusion datasets following eddy outputs"
echo " QCnifti ...... run visual qc for raw nifti data in <subjects_folder>/<case>/nii"
echo " QCPreproc ...... run visual qc for a given modality (t1w,tw2,myelin,bold,dwi)"
echo ""
echo "DWI processing, analyses & probabilistic tractography functions"
echo "----------------------------------------------------------------"
echo " hcpdLegacy ...... diffusion image processing for data with or without standard fieldmaps"
echo " FSLDtifit ...... run FSL's dtifit tool (cluster usable)"
echo " FSLBedpostxGPU ...... run fsl bedpostx w/gpu"
echo " pretractographyDense ...... generates space for whole-brain dense connectomes"
echo " ProbtrackxGPUDense ...... run FSL's probtrackx for whole brain & generates dense "
echo "                          whole brain connectomes"
echo ""
echo "Misc. functions and analyses"
echo "---------------------------"
echo " ICAFIXhcp ...... ICA FIX for HCP minimally processed data"
echo " computeBOLDfc ...... computes seed or GBC BOLD functional connectivity"
echo " structuralParcellation ...... parcellate myelin or thickness"
echo " BOLDParcellation ...... parcellate BOLD data and generate pconn files"
echo " DWIDenseParcellation ...... parcellate dense dwi tractography data"
echo " DWISeedTractography ...... reduce dense DWI tractography data using a seed structure"
echo " ROIExtract ...... extract data from pre-specified ROIs in CIFTI or NIFTI"
echo " AWSHCPSync ...... sync hcp data from aws s3 cloud"
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
echo "    Example to pass function:                mnap <function_name> [options]"
echo "    Example to request help for function:    mnap ?<function_name>"
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


# ------------------------------------------------------------------------------
#  Print out environment
# ------------------------------------------------------------------------------

environment() {
    echo ""
    echo "--------------------------------------------------------------"
    echo " MNAP Environment"
    echo ""
    echo " Environment variables"
    echo ""
    echo "                  MNAPVer = $MNAPVer"    
    echo "                    TOOLS = $TOOLS"
    echo "                 MNAPREPO = $MNAPREPO"
    echo "                 MNAPPATH = $MNAPPATH"
    echo "           TemplateFolder = $TemplateFolder"
    echo ""
    echo "               FSL_FIXDIR = $FSL_FIXDIR"
    echo "            POSTFIXICADIR = $POSTFIXICADIR"
    echo "          FREESURFER_HOME = $FREESURFER_HOME"
    echo "     FREESURFER_SCHEDULER = $FREESURFER_SCHEDULER"
    echo "             WORKBENCHDIR = $WORKBENCHDIR"
    echo "                 AFNIPATH = $AFNIPATH"
    echo "                   DCMNII = $DCMNII"
    echo "                  DICMNII = $DICMNII"
if [ -f ~/.mnapuseoctave ]; then
    echo "             OCTAVEPKGDIR = $OCTAVEPKGDIR"
    echo "               OCTAVEPATH = $OCTAVEPATH"
fi
    echo "                   FSLDIR = $FSLDIR"
    echo "                FSLGPUDIR = $FSLGPUDIR"
    echo "                 PALMPATH = $PALMPATH"
    echo "            GRADUNWARPDIR = $GRADUNWARPDIR"
    echo "             MNAPMCOMMAND = $MNAPMCOMMAND"
    echo ""
    echo "               HCPPIPEDIR = $HCPPIPEDIR"
    echo "                CARET7DIR = $CARET7DIR"
    echo "            GRADUNWARPDIR = $GRADUNWARPDIR"
    echo "     HCPPIPEDIR_Templates = $HCPPIPEDIR_Templates"
    echo "           HCPPIPEDIR_Bin = $HCPPIPEDIR_Bin"
    echo "        HCPPIPEDIR_Config = $HCPPIPEDIR_Config"
    echo "         HCPPIPEDIR_PreFS = $HCPPIPEDIR_PreFS"
    echo "            HCPPIPEDIR_FS = $HCPPIPEDIR_FS"
    echo "        HCPPIPEDIR_PostFS = $HCPPIPEDIR_PostFS"
    echo "      HCPPIPEDIR_fMRISurf = $HCPPIPEDIR_fMRISurf"
    echo "       HCPPIPEDIR_fMRIVol = $HCPPIPEDIR_fMRIVol"
    echo "         HCPPIPEDIR_tfMRI = $HCPPIPEDIR_tfMRI"
    echo "          HCPPIPEDIR_dMRI = $HCPPIPEDIR_dMRI"
    echo "     HCPPIPEDIR_dMRITract = $HCPPIPEDIR_dMRITract"
    echo "        HCPPIPEDIR_Global = $HCPPIPEDIR_Global"
    echo " HCPPIPEDIR_tfMRIAnalysis = $HCPPIPEDIR_tfMRIAnalysis"
    echo "                   MSMBin = $MSMBin"
    echo "  HCPPIPEDIR_dMRITracFull = $HCPPIPEDIR_dMRITracFull"
    echo "    HCPPIPEDIR_dMRILegacy = $HCPPIPEDIR_dMRILegacy"
    echo "            AutoPtxFolder = $AutoPtxFolder"
    echo "             FSLGPUBinary = $FSLGPUBinary"
    echo "              EDDYCUDADIR = $EDDYCUDADIR"
    echo ""
    echo " Binary locations"
    echo ""
    echo "        FSL : $(which fsl)"   
    echo " FreeSurfer : $(which freesurfer 2>&1 | grep -v 'no freesurfer')"   
    echo "       afni : $(which afni 2>&1 | grep -v 'no afni')"   
    echo "   dcm2niix : $(which dcm2niix 2>&1 | grep -v 'no dcm2niix')"   
    echo "        fix : $(which fix 2>&1 | grep -v 'no fix')"   
if [ -f ~/.mnapuseoctave ]; then
    echo "     octave : $(which octave 2>&1 | grep -v 'no octave')"   
fi
    echo " wb_command : $(which wb_command 2>&1 | grep -v 'no wb_command')"   
    echo ""   
    echo "Software versions"   
    echo ""   
    echo "        FSL : $(cat $FSLDIR/etc/fslversion)"   
    echo " FreeSurfer :$(freesurfer | tail -n 2)"   
    echo "       afni : $(afni --version)"   
    echo "   dcm2niix : $(dcm2niix -v | head -1)"   
    echo "   dicm2nii : $(cat $DICMNII/README.md | grep "(version" )"   
    echo "        fix : $(fix -v | grep FMRIB)"   
    if [ -f ~/.mnapuseoctave ]; then
        echo "     octave : $(octave -q --eval "v=version;fprintf('%s', v);")"  
    # else
    #    echo "     matlab : $(matlab -nodisplay -nojvm -nosplash -r "v=version;fprintf('%s', v);" | tail -1)"  
    fi
    echo "       PALM : $(cat $PALMPATH/palm_version.txt)"
    echo " wb_command : $(wb_command | head -1)"
    echo ""   
    echo ""
    echo "Full environment paths"
    echo ""
    echo "PATH = $PATH"
    echo ""
    echo "PYTHONPATH = $PYTHONPATH"
    echo ""
    echo "MATLABPATH = $MATLABPATH"
    echo ""
    echo "--------------------------------------------------------------"
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

if [[ ${FunctionToRun} == "runTurnkey" ]]; then
   if [[ ! -z `echo ${TURNKEY_STEPS} | grep 'createStudy'` ]]; then
       if [[ ! -d ${workdir} ]]; then 
          mkdir -p ${workdir} &> /dev/null
       fi
   fi
fi

Platform="Platform Information: `uname -a`"

# -- Check if study folder is created
if [[ ! -f ${StudyFolder}/.mnapstudy ]]; then 
    echo "MNAP study folder specification in ${StudyFolder} not found. Generating now..."
    gmri createStudy "${StudyFolder}"
fi


# -- Check if part of the MNAP file hierarchy is missing
#
# --- analysis subfolder
# /analysis/scripts
# --- processing subfolders
# /processing/logs/comlogs
# /processing/logs/runlogs
# /processing/lists
# /processing/scripts
# /processing/scenes/QC/T1w
# /processing/scenes/QC/T2w
# /processing/scenes/QC/myelin
# /processing/scenes/QC/BOLD
# /processing/scenes/QC/DWI
# --- demographics subfolders
# /info/demographics
# /info/tasks
# /info/stimuli
# /info/BIDS
# --- subjects subfolders
# /subjects/inbox/MR
# /subjects/inbox/EEG
# /subjects/inbox/BIDS
# /subjects/inbox/behavior
# /subjects/inbox/concs
# /subjects/inbox/events
# /subjects/archive/MR
# /subjects/archive/EEG
# /subjects/archive/BIDS
# /subjects/archive/behavior
# /subjects/specs
# /subjects/QC
# 

MNAPFolders="analysis/scripts processing/logs/comlogs processing/logs/runlogs processing/lists processing/scripts processing/scenes/QC/T1w processing/scenes/QC/T2w processing/scenes/QC/myelin processing/scenes/QC/BOLD processing/scenes/QC/DWI info/demographics info/tasks info/stimuli info/BIDS subjects/inbox/MR subjects/inbox/EEG subjects/inbox/BIDS subjects/inbox/behavior subjects/inbox/concs subjects/inbox/events subjects/archive/MR subjects/archive/EEG subjects/archive/BIDS subjects/archive/behavior subjects/specs subjects/QC"
for MNAPFolder in ${MNAPFolders}; do
    if [[ ! -d ${StudyFolder}/${MNAPFolder} ]]; then
          echo "MNAP folder ${StudyFolder}/${MNAPFolder} not found. Generating now..."; echo ""
          mkdir -p ${StudyFolder}/${MNAPFolder} &> /dev/null
    fi
done
# -- Add check in case the subjects folder is distinct from the default name
MNAPSubjectsFolders="${SubjectsFolder}/inbox/MR ${SubjectsFolder}/inbox/EEG ${SubjectsFolder}/inbox/BIDS ${SubjectsFolder}/inbox/behavior ${SubjectsFolder}/inbox/concs ${SubjectsFolder}/inbox/events ${SubjectsFolder}/archive/MR ${SubjectsFolder}/archive/EEG ${SubjectsFolder}/archive/BIDS ${SubjectsFolder}/archive/behavior ${SubjectsFolder}/specs ${SubjectsFolder}/QC"
for MNAPSubjectsFolder in ${MNAPSubjectsFolders}; do
    if [[ ! -d ${MNAPSubjectsFolder} ]]; then
          echo "MNAP folder ${MNAPSubjectsFolder} not found. Generating now..."; echo ""
          mkdir -p ${MNAPSubjectsFolder} &> /dev/null
    fi
done

# -- If logfolder flag set then set it and set master log
if [ -z "$LogFolder" ]; then
    MasterLogFolder="${StudyFolder}/processing/logs"
else
    MasterLogFolder="$LogFolder"
fi

# -- Generate the master log, comlogs and runlogs folder
mkdir ${MasterLogFolder} &> /dev/null
MasterRunLogFolder="${MasterLogFolder}/runlogs"
MasterComlogFolder="${MasterLogFolder}/comlogs"
mkdir ${MasterRunLogFolder} &> /dev/null
mkdir ${MasterComlogFolder} &> /dev/null

cd ${MasterRunLogFolder}

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
ComlogTmp="${MasterComlogFolder}/tmp_${FunctionToRun}_${CASE}_${TimeStamp}.log"; touch ${ComlogTmp}; chmod 777 ${ComlogTmp}
ComRun="${MasterComlogFolder}/Run_${FunctionToRun}_${CASE}_${TimeStamp}.sh"; touch ${ComRun}; chmod 777 ${ComRun}
ComlogError="${MasterComlogFolder}/error_${FunctionToRun}_${CASE}_${TimeStamp}.log"
ComlogDone="${MasterComlogFolder}/done_${FunctionToRun}_${CASE}_${TimeStamp}.log"
CompletionCheck="${MasterComlogFolder}/Completion_${FunctionToRun}_${TimeStamp}.Check"

# -- Batchlog
#    <batch system>_<command name>_job<job number>.<date>_<hour>.<minute>.<microsecond>.log

# -- Code for debugging
echo ""
cyaneho "--------------------- Command to run: -----------------------"
echo ""
cyaneho "${CommandToRun}"
echo ""
cyaneho "--------------------------------------------------------------"
echo ""
echo ""

# -- Run commands
SuccessCheck="Successful completion"
echo "${CommandToRun}" >> ${Runlog}
echo "#!/bin/bash" >> ${ComRun}
echo "export PYTHONUNBUFFERED=1" >> ${ComRun}
echo "${CommandToRun}" >> ${ComRun}
chmod 777 ${ComRun}
 
# ComRunSet="cd ${MasterRunLogFolder}; echo ${CommandToRun} >> ${Runlog}; echo 'export PYTHONUNBUFFERED=1; ${CommandToRun}' >> ${ComRun}; chmod 777 ${ComRun}"

# -- Check that $ComRun is set properly
echo ""; if [ ! -f "${ComRun}" ]; then reho " ERROR: ${ComRun} file not found. Check your inputs"; echo ""; return 1; fi
ComRunSize=`wc -c < ${ComRun}` > /dev/null 2>&1
echo ""; if [[ "${ComRunSize}" == 0 ]]; then > /dev/null 2>&1; reho " ERROR: ${ComRun} file found but has no content. Check your inputs"; echo ""; return 1; fi

ComRunExec=". ${ComRun} 2>&1 | tee -a ${ComlogTmp}"
ComComplete="cat ${ComlogTmp} | grep '${SuccessCheck}' &> ${CompletionCheck}"
ComRunCheck="if [[ -s ${CompletionCheck} ]]; then mv ${ComlogTmp} ${ComlogDone}; echo ''; geho ' ===> Successful completion of ${FunctionToRun}. Check final MNAP log output:'; echo ''; geho '    ${ComlogDone}'; echo ''; rm ${CompletionCheck}; rm ${ComRun}; else mv ${ComlogTmp} ${ComlogError}; echo ''; reho ' ===> ERROR during ${FunctionToRun}. Check final MNAP error log output:'; echo ''; reho '    ${ComlogError}'; echo ''; rm ${CompletionCheck}; fi"
# -- Combine commands
ComRunAll="${ComRunExec}; ${ComComplete}; ${ComRunCheck}"

# -- Run the commands locally
if [[ "$Cluster" == 1 ]]; then
    geho "--------------------------------------------------------------"
    echo ""
    geho "   Running ${FunctionToRun} locally on `hostname`"
    geho "   Command log:     ${Runlog}  "
    geho "   Function output: ${ComlogTmp} "
    echo ""
    geho "--------------------------------------------------------------"
    echo ""
    eval "${ComRunAll}"
fi
# -- Run the commands via scheduler
if [[ "$Cluster" == 2 ]]; then
    cd ${MasterRunLogFolder}
    gmri schedule command="${ComRunAll}" settings="${Scheduler}"
    geho "--------------------------------------------------------------"
    echo ""
    geho "   Data successfully submitted to scheduler"
    geho "   Scheduler details: ${Scheduler}"
    geho "   Command log:     ${Runlog}  "
    geho "   Function output: ${ComlogTmp} "
    echo ""
    geho "--------------------------------------------------------------"
    echo ""
fi
}

# ---------------------------------------------------------------------------------------------------------------
#  runTurnkey - Turnkey execution of MNAP workflow via the XNAT docker engine
# ---------------------------------------------------------------------------------------------------------------

runTurnkey() {
# -- Specify command variable
unset CommandToRun
CommandToRun="${TOOLS}/${MNAPREPO}/connector/functions/RunTurnkey.sh --bolds='${BOLDS}' ${runTurnkeyArguments} --subjects='${CASE}' --turnkeysteps='${TURNKEY_STEPS}' --subjid='${SUBJID}'"
connectorExec
}

show_usage_runTurnkey() {
${TOOLS}/${MNAPREPO}/connector/functions/RunTurnkey.sh
}

# ---------------------------------------------------------------------------------------------------------------
#  organizeDicom - Sort original DICOMs into folders and generates NIFTI files using sortDicom and dicom2niix
# ---------------------------------------------------------------------------------------------------------------

organizeDicom() {
# -- Note:
#    This function passes parameters into two NIUtilities commands: sortDicom and dicom2niix
mkdir ${SubjectsFolder}/${CASE}/dicom &> /dev/null
if [ "$Overwrite" == "yes" ]; then
    echo ""
    reho "===> Removing prior DICOM run log. Will initiate new run."
    rm -f ${SubjectsFolder}/${CASE}/dicom/DICOM-Report.txt &> /dev/null
fi
echo ""
echo "===> Checking for presence of ${SubjectsFolder}/${CASE}/dicom/DICOM-Report.txt"
echo ""
# -- Check if DICOM-Report.txt is there
if (test -f ${SubjectsFolder}/${CASE}/dicom/DICOM-Report.txt); then
    echo ""
    geho "===> Found ${SubjectsFolder}/${CASE}/dicom/DICOM-Report.txt"
    geho "    Note: To re-run set --overwrite='yes'"
    echo ""
    geho " ... $CASE ---> organizeDicom done"
    echo ""
    return 0
fi

# -- Check if inbox missing or is empty
if [ ! -d ${SubjectsFolder}/${CASE}/dicom ]; then
    reho "===> ${SubjectsFolder}/${CASE}/dicom folder not found. Checking for ${SubjectsFolder}/${CASE}/inbox/"; echo ""
    if [ ! -d ${SubjectsFolder}/${CASE}/inbox ]; then
        reho "===> ${SubjectsFolder}/${CASE}/inbox not found. Make sure your DICOMs are present inside ${SubjectsFolder}/${CASE}/inbox/"; echo ""
        exit 1
    fi
fi
if [ -d ${SubjectsFolder}/${CASE}/dicom ]; then
     DicomCheck=`ls ${SubjectsFolder}/${CASE}/dicom/`
     InboxCheck=`ls ${SubjectsFolder}/${CASE}/inbox/`
     if [[ ${InboxCheck} != "" ]]; then
         reho "===> ${SubjectsFolder}/${CASE}/dicom/ found and data exists."; echo ""
         if [[ ${InboxCheck} == "" ]]; then
             reho "===> ${SubjectsFolder}/${CASE}/inbox/ found but empty. Will re-run sortDicom from ${SubjectsFolder}/${CASE}/dicom"; echo ""
         fi
    fi
fi

# -- Specify command variable
unset CommandToRun
ComA="cd ${SubjectsFolder}/${CASE}"
ComB="gmri sortDicom folder=. " 
ComC="gmri dicom2niix unzip=${Unzip} gzip=${Gzip} clean=${Clean} verbose=${VerboseRun} cores=${Cores} subjectid=${CASE}"
ComD="slicesdir ${SubjectsFolder}/${CASE}/nii/*.nii*"
CommandToRun="${ComA}; ${ComB}; ${ComC}; ${ComD}"
# -- Connector execute function
connectorExec
}

show_usage_organizeDicom() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function expects a set of raw DICOMs in <subjects_folder>/<case>/inbox "
echo "DICOMs are organized, gzipped and converted to NIFTI format for additional processing."
echo "subject.txt files will be generated with id and subject matching the <case>."
echo ""
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                             Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags)"
echo "--subjectsfolder=<folder_with_subjects>                Path to study folder that contains subjects. If missing then optional paramater --folder needs to be provided."
echo "--subjects=<comma_separated_list_of_cases>             List of subjects to run. If missing then --folder needs to be provided for a single-session run."
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
echo "--scheduler=<name_of_cluster_scheduler_and_options>    A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo "                                                       e.g. for SLURM the string would look like this: "
echo "                                                       --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
echo ""
echo "-- EXAMPLE:"
echo ""
echo "mnap --subjectsfolder='<folder_with_subjects>' \ "
echo "--function='organizeDicom' \ "
echo "--subjects='<comma_separarated_list_of_cases>' "
echo "--scheduler='<name_of_scheduler_and_options>'"
echo ""
}

# ---------------------------------------------------------------------------------------------------------------
#  QCnifti - QC nifti files following organizeDicom
# ---------------------------------------------------------------------------------------------------------------

QCnifti() {

# -- Specify command variable
unset CommandToRun
Com1="slicesdir ${SubjectsFolder}/${CASE}/nii/*.nii*"
Com2="if [ -f ${SubjectsFolder}/${CASE}/nii/slicesdir/index.html ]; then echo ''; geho '------------------------- Successful completion of work --------------------------------'; else echo ''; reho 'Something went wrong. Check output: ${SubjectsFolder}/${CASE}/nii/slicesdir/'; fi"
CommandToRun="${Com1}; ${Com2}"
# -- Connector execute function
connectorExec

}

show_usage_QCnifti() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function performs QC for raw NIFTI images in <subjects_folder>/<case>/nii "
echo ""
echo " * Input: requires NIFTI images in <subjects_folder>/<case>/nii/ after either BIDS import of DICOM organization. "
echo " * Subject-specific output: <subjects_folder>/<case>/nii/slicesdir "
echo " * Uses FSL's `slicesdir` script to generate PNGs and an HTML file in the above directory. "
echo ""
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--subjectsfolder=<folder_with_subjects>                Path to study folder that contains subjects. If missing then optional paramater --folder needs to be provided."
echo "--subjects=<comma_separated_list_of_cases>             List of subjects to run. If missing then --folder needs to be provided for a single-session run."
echo ""
echo "-- OPTIONAL PARAMETERS: "
echo ""
echo "--scheduler=<name_of_cluster_scheduler_and_options>    A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo "                                                       e.g. for SLURM the string would look like this: "
echo "                                                       --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
echo ""
echo "-- EXAMPLE:"
echo ""
echo "mnap niftiQC --subjectsfolder='<folder_with_subjects>' \ "
echo "--subjects='<comma_separarated_list_of_cases>' "
echo "--scheduler='<name_of_scheduler_and_options>'"
echo ""
}


# ------------------------------------------------------------------------------------------------------
#  mapHCPFiles - Setup the HCP File Structure to be fed to the Yale HCP
# ------------------------------------------------------------------------------------------------------

mapHCPFiles() {
# -- Specify command variable
if [[ ${Overwrite} == "yes" ]]; then
    HLinks=`ls ${SubjectsFolder}/${CASE}/hcp/${CASE}/*/*nii* 2>/dev/null`; for HLink in ${HLinks}; do unlink ${HLink}; done
fi
CommandToRun="cd ${SubjectsFolder}/${CASE}; echo '--> running mapHCPFiles for ${CASE}'; echo ''; gmri setupHCP"
# -- Connector execute function
connectorExec
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
CommandToRun=". ${TOOLS}/${MNAPREPO}/connector/functions/DataSync.sh \
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

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  hcpdLegacy - Executes the Diffusion Processing Script via FUGUE implementation for legacy data - (needed for legacy DWI data that is non-HCP compliant without counterbalanced phase encoding directions needed for topup)
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

hcpdLegacy() {

# -- Unique requirements for this function:
#      Needs CUDA libraries to run eddy_cuda (10x faster than on a CPU)

# -- Specify command variable
CommandToRun="${TOOLS}/${MNAPREPO}/connector/functions/DWIPreprocPipelineLegacy.sh \
--subjectsfolder=${SubjectsFolder} \
--subject=${CASE} \
--scanner=${Scanner} \
--usefieldmap=${UseFieldmap} \
--PEdir=${PEdir} \
--echospacing=${EchoSpacing} \
--TE=${TE} \
--unwarpdir=${UnwarpDir} \
--diffdatasuffix=${DiffDataSuffix} \
--overwrite=${Overwrite}"
# -- Connector execute function
connectorExec
}
show_usage_hcpdLegacy() {
echo ""; echo "-- DESCRIPTION for $UsageInput"
${TOOLS}/${MNAPREPO}/connector/functions/DWIPreprocPipelineLegacy.sh
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
# -- INPUTS:  eddy-cleaned DWI Data
# -- OUTPUTS: located in <eddyBase>.qc per EDDY QC specification

# -- Specify command variable
CommandToRun=". ${TOOLS}/${MNAPREPO}/connector/functions/DWIeddyQC.sh \
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
--overwrite=${Overwrite}"
# -- Connector execute function
connectorExec
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
CASE="$CASE"
MatrixVersion="$MatrixVersion"
ParcellationFile="$ParcellationFile"
OutName="$OutName"
DWIOutput="${SubjectsFolder}/${CASE}/hcp/$CASE/MNINonLinear/Results/Tractography"
Overwrite="$Overwrite"

CommandToRun=". ${TOOLS}/${MNAPREPO}/connector/functions/DWIDenseParcellation.sh \
--subjectsfolder=${SubjectsFolder} \
--subject=${CASE} \
--matrixversion=${MatrixVersion} \
--parcellationfile=${ParcellationFile} \
--waytotal=${WayTotal} \
--outname=${OutName} \
--overwrite=${Overwrite}"
# -- Connector execute function
connectorExec
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
echo "--waytotal=<use_waytotal_normalized_data>            Use the waytotal normalized version of the DWI dense connectome. Default: [none]"
echo "                                                     none: without waytotal normalization [Default]" 
echo "                                                     standard: standard waytotal normalized"
echo "                                                     log: log-transformed waytotal normalized"
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
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  ICAFIXhcp - Function for computing ICA FIX + PostFIX on HCP minimally processed BOLD data
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

ICAFIXhcp() {

# -- Specify command variable
CommandToRun="${TOOLS}/${MNAPREPO}/connector/functions/ICAFIXhcp.sh \
--subjectsfolder=${SubjectsFolder} \
--subjects=${CASES} \
--bolds=${BOLDS} \
--movcorr=${MovCorr} \
--icafixfunction=${ICAFIXFunction} \
--hpfilter=${HPFilter} \
--overwrite=${Overwrite}"

# -- Connector execute function
connectorExec
}
show_usage_hcpdLegacy() {
echo ""; echo "-- DESCRIPTION for $UsageInput"
${TOOLS}/${MNAPREPO}/connector/functions/ICAFIXhcp.sh
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
Calculation="$Calculation"        # --calculation=
RunType="$RunType"                # --runtype=
FileList="$FileList"            # --flist=
IgnoreFrames="$IgnoreFrames"    # --ignore=
MaskFrames="$MaskFrames"        # --mask=
Covariance="$Covariance"        # --covariance=
TargetROI="$TargetROI"            # --target=
RadiusSmooth="$RadiusSmooth"    # --rsmooth=
RadiusDilate="$RadiusDilate"    # --rdilate=
GBCCommand="$GBCCommand"        # --command=
Verbose="$Verbose"                # --verbose=
ComputeTime="$ComputeTime"        # --time=
VoxelStep="$VoxelStep"            # --vstep=
ROIInfo="$ROIInfo"                # --roinfo=
FCCommand="$FCCommand"            # --options=
Method="$Method"                # --method=
InputPath="$InputPath"            # --inputpath
Overwrite="$Overwrite"            # --overwrite
MemLimit="$MemLimit"            # --mem-limit=

# -- Check type of run
if [ "${RunType}" == "individual" ]; then
    OutPath="${SubjectsFolder}/${CASE}/${InputPath}"
    # -- Make sure individual runs default to the original input path location (/images/functional)
    if [ "$InputPath" == "" ]; then
        InputPath="${SubjectsFolder}/${CASE}/images/functional"
    fi
    # -- Make sure individual runs default to the original input path location (/images/functional)
    if [ "$OutPath" == "" ]; then
        OutPath="${SubjectsFolder}/${CASE}/${InputPath}"
    fi
fi

# -- Check type of connectivity calculation is seed
if [ ${Calculation} == "seed" ]; then
    echo ""
    # -- Specify command variable
    CommandToRun="${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh \
    --subjectsfolder=${SubjectsFolder} \
    --calculation=${Calculation} \
    --runtype=${RunType} \
    --subjects=${CASE} \
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
    # -- Specify command variable
    CommandToRun="${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh \
    --subjectsfolder=${SubjectsFolder} \
    --calculation=${Calculation} \
    --runtype=${RunType} \
    --subjects=${CASE} \
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
# -- Check type of connectivity calculation is seed
if [ ${Calculation} == "dense" ]; then
    echo ""
    # -- Specify command variable
    CommandToRun="${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh \
    --subjectsfolder=${SubjectsFolder} \
    --calculation=${Calculation} \
    --runtype=${RunType} \
    --subjects=${CASE} \
    --inputfiles=${InputFiles} \
    --inputpath=${InputPath} \
    --outname=${OutName} \
    --overwrite=${Overwrite} \
    --targetf=${OutPath} \
    --covariance=${Covariance} \
    --mem-limit=${MemLimit} "
    # -- Connector execute function
    connectorExec
fi
}
show_usage_computeBOLDfc() {
echo ""; echo "-- DESCRIPTION for $UsageInput"
${TOOLS}/${MNAPREPO}/connector/functions/ComputeFunctionalConnectivity.sh
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
Overwrite="$Overwrite"
# -- Command to run
CommandToRun=". ${TOOLS}/${MNAPREPO}/connector/functions/StructuralParcellation.sh \
--subjectsfolder=${SubjectsFolder} \
--subject=${CASE} \
--inputdatatype=${InputDataType} \
--parcellationfile=${ParcellationFile} \
--overwrite=${Overwrite} \
--outname=${OutName} \
--extractdata=${ExtractData}"
# -- Connector execute function
connectorExec
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
if [ -z ${SingleInputFile} ]; then
    BOLDOutput="${SubjectsFolder}/${CASE}/${OutPath}"
else
    BOLDOutput="${OutPath}"
fi
# -- Command to run
CommandToRun=". ${TOOLS}/${MNAPREPO}/connector/functions/BOLDParcellation.sh \
--subjectsfolder='${SubjectsFolder}' \
--subjects='${CASE}' \
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
--weightsfile='${WeightsFile}'"
# -- Connector execute function
connectorExec
}
show_usage_BOLDParcellation() {
echo ""; echo "-- DESCRIPTION for $UsageInput"
${TOOLS}/${MNAPREPO}/connector/functions/BOLDParcellation.sh
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
ExtractData="${ExtractData}"
if [ -z "$SingleInputFile" ]; then
    OutPath="${SubjectsFolder}/${CASE}/${OutPath}"
else
    OutPath="${OutPath}"
    InputFile="${SingleInputFile}"
fi
if [ "${ROIFileSubjectSpecific}" == "no" ]; then
    ROIFile="${ROIFile}"
else
    ROIFile="${SubjectsFolder}/${CASE}/${ROIFile}"
fi
# -- Command to run
CommandToRun=". /$TOOLS/${MNAPREPO}/connector/functions/ROIExtract.sh \
--roifile='${ROIFile}' \
--inputfile='${InputFile}' \
--outdir='${OutPath}' \
--outname='${OutName}'"
# -- Connector execute function
connectorExec
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
echo "<output_name>.csv      <-- matrix with one ROI per row and one column per frame/volume in singleinputfile"
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
# -- Command to run
CommandToRun=". ${TOOLS}/${MNAPREPO}/connector/functions/DWIFSLDtifit.sh \
--subjectsfolder='${SubjectsFolder}' \
--subject='${CASE}' \
--overwrite='${Overwrite}' "
# -- Connector execute function
connectorExec
}

show_usage_FSLDtifit() {
echo ""; echo "-- DESCRIPTION for $UsageInput"
${TOOLS}/${MNAPREPO}/connector/functions/DWIFSLDtifit.sh
}

# ------------------------------------------------------------------------------------------------------
#  FSLBedpostxGPU - Executes the bedpostx_gpu code from FSL (needed for probabilistic tractography)
# ------------------------------------------------------------------------------------------------------

FSLBedpostxGPU() {
# -- Command to run
CommandToRun=". ${TOOLS}/${MNAPREPO}/connector/functions/DWIFSLBedpostxGPU.sh \
--subjectsfolder='${SubjectsFolder}' \
--subject='${CASE}' \
--fibers='${Fibers}' \
--model='${Model}' \
--burnin='${Burnin}' \
--jumps='${Jumps}' \
--rician='${Rician}' \
--overwrite='${Overwrite}' "
# -- Connector execute function
connectorExec
}

show_usage_FSLBedpostxGPU() {
echo ""; echo "-- DESCRIPTION for $UsageInput"
${TOOLS}/${MNAPREPO}/connector/functions/DWIFSLBedpostxGPU.sh
}

# ------------------------------------------------------------------------------------------------------------------------------
#  autoPtx - Executes the autoptx script from FSL (needed for probabilistic estimation of large-scale fiber bundles / tracts)
# -------------------------------------------------------------------------------------------------------------------------------

autoPtx() {
# -- Check inputs
if [[ -d ${BedPostXFolder} ]]; then 
    reho "Prior BedpostX run not found or incomplete for $CASE. Check work and re-run."
    exit 1
fi
if [[ -z ${AutoPtxFolder} ]]; then 
    reho "AutoPtxFolder environment variable not. Set it correctly and re-run."
    exit 1
fi
# -- Set commands
Com1="${AutoPtxFolder}/autoptx ${SubjectsFolder} ${CASE} ${BedPostXFolder}"
Com2="${AutoPtxFolder}/Prepare_for_Display.sh ${StudyFolder}/${CASE}/MNINonLinear/Results/autoptx 0.005 1"
Com3="${AutoPtxFolder}/Prepare_for_Display.sh ${StudyFolder}/${CASE}/MNINonLinear/Results/autoptx 0.005 0"
# -- Command to run
CommandToRun="${Com1}; ${Com2}; ${Com3}"
# -- Connector execute function
connectorExec
}

show_usage_autoPtx() {
echo ""
echo "-- DESCRIPTION for $UsageInput "
echo ""
echo "This function runs the autoptx script in ${AutoPtxFolder}."
echo ""
echo "For full details on AutoPtx functionality see: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/AutoPtx"
echo ""
}

# -------------------------------------------------------------------------------------------------------------------
#  pretractographyDense - Executes the HCP Pretractography code [ Stam's implementation for all grayordinates ]
# ------------------------------------------------------------------------------------------------------------------

pretractographyDense() {
# -- Parse general parameters
ScriptsFolder="${HCPPIPEDIR_dMRITracFull}/PreTractography"
LogFolder="${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Results/log_pretractographydense"
RunFolder="${SubjectsFolder}/${CASE}/hcp/"
# -- Command to run
CommandToRun="${ScriptsFolder}/PreTractography.sh ${RunFolder} ${CASE} 0 "
# -- Connector execute function
connectorExec
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
echo "-- EXAMPLE:"
echo ""
echo "mnap --subjectsfolder='<path_to_study_subjects_folder>' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--function='pretractographyDense' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo ""
}

# --------------------------------------------------------------------------------------------------------------------------------------------------
#  ProbtrackxGPUDense - Executes the HCP Matrix1 and / or 3 code and generates WB dense connectomes (Stam's implementation for all grayordinates)
# --------------------------------------------------------------------------------------------------------------------------------------------------

ProbtrackxGPUDense() {
# -- Command to run
CommandToRun=". ${TOOLS}/${MNAPREPO}/connector/functions/ProbtrackxGPUDense.sh \
--subjectsfolder='${SubjectsFolder}' \
--scriptsfolder='${ScriptsFolder}' \
--infolder='${InFolder}' \
--outfolder='${OutFolder}' \
--omatrix1='${MatrixOne}' \
--omatrix3='${MatrixThree}' \
--nsamplesmatrix1='${NsamplesMatrixOne}' \
--nsamplesmatrix3='${NsamplesMatrixThree}' \
--overwrite='${Overwrite}' "
# -- Connector execute function
connectorExec
}

show_usage_ProbtrackxGPUDense() {
echo ""; echo "-- DESCRIPTION for $UsageInput"
${TOOLS}/${MNAPREPO}/connector/functions/ProbtrackxGPUDense.sh
}

# ------------------------------------------------------------------------------------------------------------------------------
#  Sync data from AWS buckets - customized for HCP
# -------------------------------------------------------------------------------------------------------------------------------

AWSHCPSync() {
mkdir ${SubjectsFolder}/aws.logs &> /dev/null
cd $SubjectsFolder}/aws.logs
if [ ${RunMethod} == "2" ]; then
    reho "AWS sync dry run..."
    if [ -d ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear ]; then
        mkdir ${SubjectsFolder}/${CASE}/hcp/${CASE}/${Modality} &> /dev/null
        AWSSyncTimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        time aws s3 sync --dryrun s3:/${Awsuri}/${CASE}/${Modality} ${SubjectsFolder}/${CASE}/hcp/${CASE}/${Modality}/ >> AWSHCPSync_${CASE}_${Modality}_${AWSSyncTimeStamp}.log
    else
        mkdir -p ${SubjectsFolder}/${CASE}/hcp/${CASE}/${Modality} &> /dev/null
        AWSSyncTimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        time aws s3 sync --dryrun s3:/${Awsuri}/${CASE}/${Modality} ${SubjectsFolder}/${CASE}/hcp/${CASE}/${Modality}/ >> AWSHCPSync_${CASE}_${Modality}_${AWSSyncTimeStamp}.log
    fi
fi
if [ ${RunMethod} == "1" ]; then
    geho "AWS sync running..."
    if [ -d ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear ]; then
        mkdir ${SubjectsFolder}/${CASE}/hcp/${CASE}/${Modality} &> /dev/null
        AWSSyncTimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        time aws s3 sync s3:/${Awsuri}/${CASE}/${Modality} ${SubjectsFolder}/${CASE}/hcp/${CASE}/${Modality}/ >> AWSHCPSync_${CASE}_${Modality}_${AWSSyncTimeStamp}.log
    else
        mkdir -p ${SubjectsFolder}/${CASE}/hcp/${CASE}/${Modality} &> /dev/null
        AWSSyncTimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        time aws s3 sync s3:/${Awsuri}/${CASE}/${Modality} ${SubjectsFolder}/${CASE}/hcp/${CASE}/${Modality}/ >> AWSHCPSync_${CASE}_${Modality}_${AWSSyncTimeStamp}.log
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
# -- Check general output folders for QC
if [ ! -d ${SubjectsFolder}/QC ]; then
    mkdir -p ${SubjectsFolder}/QC &> /dev/null
fi
# -- Check T1w output folders for QC
if [ ! -d ${OutPath} ]; then
    mkdir -p ${OutPath} &> /dev/null
fi
# -- Command to run
CommandToRun=". ${TOOLS}/${MNAPREPO}/connector/functions/QCPreprocessing.sh \
--subjectsfolder='${SubjectsFolder}' \
--subjects='${CASE}' \
--outpath='${OutPath}' \
--overwrite='${Overwrite}' \
--scenetemplatefolder='${scenetemplatefolder}' \
--modality='${Modality}' \
--datapath='${GeneralSceneDataPath}' \
--datafile='${GeneralSceneDataFile}' \
--customqc=${QCPreprocCustom} \
--omitdefaults=${OmitDefaults} \
--dwipath='${DWIPath}' \
--dwidata='${DWIData}' \
--dwilegacy='${DWILegacy}' \
--dtifitqc='${DtiFitQC}' \
--bedpostxqc='${BedpostXQC}' \
--eddyqcstats='${EddyQCStats}' \
--bolddata='${BOLDLIST}' \
--boldprefix='${BOLDPrefix}' \
--boldsuffix='${BOLDSuffix}' \
--skipframes='${SkipFrames}' \
--snronly='${SNROnly}' \
--timestamp='${TimeStamp}' \
--scenezip='${SceneZip}' \
--boldfc='${BOLDfc}' \
--boldfcinput='${BOLDfcInput}' \
--boldfcpath='${BOLDfcPath}' \
--suffix='${Suffix}' \
--hcp_suffix='${HCPSuffix}'"

# -- Connector execute function
connectorExec
}
show_usage_QCPreproc() {
echo ""; echo "-- DESCRIPTION for $UsageInput"
${TOOLS}/${MNAPREPO}/connector/functions/QCPreprocessing.sh
}

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=
# =-=-=-=-=-==-=-=-= Establish general MNAP functions and variables =-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=

# -- Setup this script such that if any command exits with a non-zero value, the
#    script itself exits and does not attempt any further processing.
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

# -- Set version variable
MNAPVer=`cat ${TOOLS}/${MNAPREPO}/VERSION.md`

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
    if [ "$UsageInput" == "environment" ]; then
        environment
        exit 0
    fi
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
unset SUBJID

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

if [ "$FunctionToRun" == "runTurnkey" ]; then
    runTurnkeyArguments="$@"
    runTurnkeyArguments=`printf '%s\n' "${runTurnkeyArguments//runTurnkey/}"`
    #echo ""
    #geho "Turnkey Arguments: ${runTurnkeyArguments}"
    #echo ""
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
    STUDY_PATH=${StudyFolderPath}
    SubjectsFolder=`opts_GetOpt "${setflag}subjectsfolder" $@` # subjects folder to work on
    SubjectFolder=`opts_GetOpt "${setflag}subjectfolder"  $@`  # subjects folder to work on
    if [[ ! -z ${STUDY_PATH} ]]; then StudyFolder=${STUDY_PATH}; fi 
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
    if [ -z "$STUDY_PATH" ]; then
         STUDY_PATH=${StudyFolder}
    fi
    # -- If logfolder flag set then set it and set master log
    if [ -z "$LogFolder" ]; then
        LogFolder="${StudyFolder}/processing/logs"
    fi
    
    # -- Set turnkey flags
    TURNKEY_TYPE=`opts_GetOpt "${setflag}turnkeytype" $@`
    TURNKEY_STEPS=`opts_GetOpt "${setflag}turnkeysteps" $@`
    STUDY_PATH=`opts_GetOpt "${setflag}path" $@`
    workdir=`opts_GetOpt "${setflag}workingdir" $@`
    PROJECT_NAME=`opts_GetOpt "${setflag}projectname" $@`
    CleanupSubject=`opts_GetOpt "${setflag}cleanupsubject" $@`
    CleanupProject=`opts_GetOpt "${setflag}cleanupproject" $@`
    RawDataInputPath=`opts_GetOpt "${setflag}rawdatainput" $@`
    mnap_subjectsfolder=`opts_GetOpt "${setflag}subjectsfolder" $@`
    OVERWRITE_SUBJECT=`opts_GetOpt "${setflag}overwritesubject" $@`
    OVERWRITE_STEP=`opts_GetOpt "${setflag}overwritestep" $@`
    OVERWRITE_PROJECT=`opts_GetOpt "${setflag}overwriteproject" $@`
    OVERWRITE_PROJECT_FORCE=`opts_GetOpt "${setflag}overwriteprojectforce" $@`
    OVERWRITE_PROJECT_XNAT=`opts_GetOpt "${setflag}overwriteprojectxnat" $@`
    BATCH_PARAMETERS_FILENAME=`opts_GetOpt "${setflag}batchfile" $@`
    LOCAL_BATCH_FILE=`opts_GetOpt "${setflag}local_batchfile" $@`
    SubjectBatchFile=`opts_GetOpt "--batchfile" $@`
    SCAN_MAPPING_FILENAME=`opts_GetOpt "${setflag}mappingfile" $@`
    XNAT_ACCSESSION_ID=`opts_GetOpt "${setflag}xnataccsessionid" $@`
    XNAT_SESSION_LABELS=`opts_GetOpt "${setflag}xnatsessionlabels" "$@" | sed 's/,/ /g;s/|/ /g'`; XNAT_SESSION_LABELS=`echo "${XNAT_SESSION_LABELS}" | sed 's/,/ /g;s/|/ /g'`
    XNAT_PROJECT_ID=`opts_GetOpt "${setflag}xnatprojectid" $@`
    XNAT_SUBJECT_ID=`opts_GetOpt "${setflag}xnatsubjectid" $@`
    XNAT_HOST_NAME=`opts_GetOpt "${setflag}xnathost" $@`
    XNAT_USER_NAME=`opts_GetOpt "${setflag}xnatuser" $@`
    XNAT_PASSWORD=`opts_GetOpt "${setflag}xnatpass" $@`
    XNAT_STUDY_INPUT_PATH=`opts_GetOpt "${setflag}xnatstudyinputpath" $@`

    # -- General flags
    CASES=`opts_GetOpt "${setflag}subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
    SUBJID=`opts_GetOpt "${setflag}subjid" "$@" | sed 's/,/ /g;s/|/ /g'`; SUBJID=`echo "$SUBJID" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
    Overwrite=`opts_GetOpt "${setflag}overwrite" $@`  # Clean prior run and starr fresh [yes/no]
    PRINTCOM=`opts_GetOpt "${setflag}printcom" $@`    # Option for printing the entire command
    Scheduler=`opts_GetOpt "${setflag}scheduler" $@`  # Specify the type of scheduler to use
    LogFolder=`opts_GetOpt "${setflag}logfolder" $@`  # Log location
    LogSave=`opts_GetOpt "${setflag}log" $@`          # Log save
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
    # -- g_PlotsBoldTS input flags
    QCPlotElements=`opts_GetOpt "${setflag}qcplotelements" $@`
    QCPlotImages=`opts_GetOpt "${setflag}qcplotimages" $@`
    QCPlotMasks=`opts_GetOpt "${setflag}qcplotmasks" $@`
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
    MemLimit=`opts_GetOpt "${setflag}mem-limit" $@`
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
    WeightsFile=`opts_GetOpt "${setflag}weightsfile" $@`
    ParcellationFile=`opts_GetOpt "${setflag}parcellationfile" $@`
    # -- hcpdLegacy input flags
    EchoSpacing=`opts_GetOpt "${setflag}echospacing" $@`
    PEdir=`opts_GetOpt "${setflag}PEdir" $@`
    TE=`opts_GetOpt "${setflag}TE" $@`
    UnwarpDir=`opts_GetOpt "${setflag}unwarpdir" $@`
    DiffDataSuffix=`opts_GetOpt "${setflag}diffdatasuffix" $@`
    Scanner=`opts_GetOpt "${setflag}scanner" $@`
    UseFieldmap=`opts_GetOpt "${setflag}usefieldmap" $@`
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
    # -- ProbtrackxGPUDense input flags
    MatrixOne=`opts_GetOpt "${setflag}omatrix1" $@`
    MatrixThree=`opts_GetOpt "${setflag}omatrix3" $@`
    NsamplesMatrixOne=`opts_GetOpt "${setflag}nsamplesmatrix1" $@`
    NsamplesMatrixThree=`opts_GetOpt "${setflag}nsamplesmatrix3" $@`
    ScriptsFolder=`opts_GetOpt "${setflag}scriptsfolder" $@`
    InFolder=`opts_GetOpt "${setflag}infolder" $@`
    OutFolder=`opts_GetOpt "${setflag}outfolder" $@`
    # -- AWSHCPSync input flags
    Awsuri=`opts_GetOpt "${setflag}awsuri" $@`
    # -- QCPreproc input flags
    OutPath=`opts_GetOpt "${setflag}outpath" $@`
    scenetemplatefolder=`opts_GetOpt "${setflag}scenetemplatefolder" $@`
    UserSceneFile=`opts_GetOpt "${setflag}userscenefile" $@`
    UserScenePath=`opts_GetOpt "${setflag}userscenepath" $@`
    Modality=`opts_GetOpt "${setflag}modality" $@`
    QCPreprocCustom=`opts_GetOpt "${setflag}customqc" $@`
    OmitDefaults=`opts_GetOpt "${setflag}omitdefaults" $@`
    HCPSuffix=`opts_GetOpt "${setflag}hcp_suffix" $@`
    DWIPath=`opts_GetOpt "${setflag}dwipath" $@`
    DWIData=`opts_GetOpt "${setflag}dwidata" $@`
    DtiFitQC=`opts_GetOpt "${setflag}dtifitqc" $@`
    BedpostXQC=`opts_GetOpt "${setflag}bedpostxqc" $@`
    EddyQCStats=`opts_GetOpt "${setflag}eddyqcstats" $@`
    DWILegacy=`opts_GetOpt "${setflag}dwilegacy" $@`
    GeneralSceneDataFile=`opts_GetOpt "${setflag}datafile" $@`
    GeneralSceneDataPath=`opts_GetOpt "${setflag}datapath" $@`
    # -- ICAFIXhcp input flags
    ICAFIXFunction=`opts_GetOpt "${setflag}icafixfunction" $@`
    HPFilter=`opts_GetOpt "${setflag}hpfilter" $@`
    MovCorr=`opts_GetOpt "${setflag}movcorr" $@`
    
    # -- Code block for BOLDs
    BOLDS=`opts_GetOpt "${setflag}bolds" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
    if [ -z "${BOLDS}" ]; then
        BOLDS=`opts_GetOpt "${setflag}boldruns" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
    fi
    if [ -z "${BOLDS}" ]; then
        BOLDS=`opts_GetOpt "${setflag}bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
    fi
    BOLDRUNS="${BOLDS}"
    BOLDDATA="${BOLDS}"
    BOLDfc=`opts_GetOpt "${setflag}boldfc" $@`
    BOLDfcInput=`opts_GetOpt "${setflag}boldfcinput" $@`
    BOLDfcPath=`opts_GetOpt "${setflag}boldfcpath" $@`
    
    if [ -z "${BOLDLIST}" ]; then BOLDLIST=`opts_GetOpt "${setflag}bolddata" "$@"`; fi
    if [ -z "${BOLDLIST}" ]; then BOLDLIST=`opts_GetOpt "${setflag}bolds" "$@"`; fi
    if [ -z "${BOLDLIST}" ]; then BOLDLIST=`opts_GetOpt "${setflag}boldruns" "$@"`; fi
    BOLDLIST=`echo "${BOLDLIST}" | sed 's/ /,/g;s/|/ /g'`
    BOLDSuffix=`opts_GetOpt "${setflag}boldsuffix" $@`
    BOLDPrefix=`opts_GetOpt "${setflag}boldprefix" $@`
    
    SkipFrames=`opts_GetOpt "${setflag}skipframes" $@`
    SNROnly=`opts_GetOpt "${setflag}snronly" $@`
    TimeStamp=`opts_GetOpt "${setflag}timestamp" $@`
    Suffix=`opts_GetOpt "${setflag}suffix" $@`
    SceneZip=`opts_GetOpt "${setflag}scenezip" $@`
    
    # -- Check if subject input is a parameter file instead of list of cases
    if [[ ${CASES} == *.txt ]]; then
        SubjectBatchFile="$CASES"
        echo ""
        echo "Using $SubjectBatchFile for input."
        echo ""
        CASES=`more ${SubjectBatchFile} | grep "id:"| cut -d " " -f 2`
    fi
fi

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-
# =-=-=-=-=-=-=-=-=-=-=-= Execute specific functions =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-

echo ""
geho "--- Running MNAP v${MNAPVer}: ${FunctionToRun} function"
echo ""

# ------------------------------------------------------------------------------
#  matlabHelp function
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "matlabHelp" ]; then
    ${FunctionToRun}
fi

# ------------------------------------------------------------------------------
#  runTurnkey function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "runTurnkey" ]; then
   # -- Check if cluster options are set
   Cluster="$RunMethod"
   if [ "$Cluster" == "2" ]; then
           if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
   fi
   runTurnkeyArgumentsInput="${runTurnkeyArguments}"
   runTurnkeyArguments=`echo "${runTurnkeyArguments}" | sed 's|--subjects=||g' | sed "s|${CASES}||g"`
   runTurnkeyArguments=`echo "${runTurnkeyArguments}" | sed 's|--turnkeysteps=||g' | sed "s|${TURNKEY_STEPS}||g"`
   runTurnkeyArguments=`echo "${runTurnkeyArguments}" | sed 's|--subjid=||g'`
   runTurnkeyArguments=`echo "${runTurnkeyArguments}" | sed 's|--bolds=||g'`
   runTurnkeyArguments=`echo "${runTurnkeyArguments}" | sed 's|--bolddata=||g'`
   runTurnkeyArguments=`echo "${runTurnkeyArguments}" | sed 's|--boldruns=||g'`
   
   echo ""
   echo "Running $FunctionToRun processing with the following parameters:"
   echo ""
   echo "--------------------------------------------------------------"
   echo ""
   echo " Turnkey steps: ${TURNKEY_STEPS} "
   echo " Turnkey arguments: ${runTurnkeyArguments} "
   echo ""
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
    echo "   Study Log Folder: ${LogFolder}"
    echo ""
    echo "--------------------------------------------------------------"
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  niftiQC function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "QCnifti" ]; then
   if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
   if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
   if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
   # -- Check if cluster options are set
   Cluster="$RunMethod"
   if [ "$Cluster" == "2" ]; then
           if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
   fi
   
   echo ""
   echo "Running $FunctionToRun processing with the following parameters:"
   echo ""
   echo "--------------------------------------------------------------"
   echo ""
   echo "   StudyFolder: ${StudyFolder}"
   echo "   Subjects Folder: ${SubjectsFolder}"
   echo "   Subject: ${CASE}"
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
    if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing."; exit 1; fi
    if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing."; exit 1; fi
    if [ -z "$CASES" ]; then reho "Error: List of subjects missing."; exit 1; fi
    if [ -z "$Modality" ]; then reho "Error:  Modality to perform QC on missing."; exit 1; fi
    if [ -z "$QCPreprocCustom" ]; then QCPreprocCustom="no"; fi
    if [ "$QCPreprocCustom" == "yes" ]; then scenetemplatefolder="${StudyFolder}/processing/scenes/QC/${Modality}"; fi
    if [ -z "$OmitDefaults" ]; then OmitDefaults="no"; fi
    Cluster="$RunMethod"
    if [ "$Cluster" == "2" ]; then
        if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Perform some careful scene checks
    if [ -z "$UserSceneFile" ]; then
        if [ ! -z "$UserScenePath" ]; then 
            reho "---> Provided --userscenepath but --userscenefile not specified."
            reho "     Check your inputs and re-run.";
            scenetemplatefolder="${TOOLS}/${MNAPREPO}/library/data/scenes/qc"
            reho "---> Reverting to MNAP defaults: ${scenetemplatefolder}"; echo ""
        fi
        if [ -z "$scenetemplatefolder" ]; then
            scenetemplatefolder="${TOOLS}/${MNAPREPO}/library/data/scenes/qc"
            reho "---> Template folder path value not explicitly specified."
            reho "---> Using MNAP defaults: ${scenetemplatefolder}"
        fi
        if ls ${scenetemplatefolder}/*${Modality}*.scene 1> /dev/null 2>&1; then 
            geho "---> Scene files found in `ls ${scenetemplatefolder}/*${Modality}*.scene` "; echo ""
        else 
            reho "---> Specified folder contains no scenes: ${scenetemplatefolder}" 
            scenetemplatefolder="${TOOLS}/${MNAPREPO}/library/data/scenes/qc"
            reho "---> Reverting to defaults: ${scenetemplatefolder} "; echo ""
        fi
    else
        if [ -f "$UserSceneFile" ]; then
            geho "---> User scene file found: ${UserSceneFile}"; echo ""
            UserScenePath=`echo ${UserSceneFile} | awk -F'/' '{print $1}'`
            UserSceneFile=`echo ${UserSceneFile} | awk -F'/' '{print $2}'`
            scenetemplatefolder=${UserScenePath}
        else
            if [ -z "$UserScenePath" ] && [ -z "$scenetemplatefolder" ]; then 
                reho "---> Error: Path for user scene file not specified."
                reho "     Specify --scenetemplatefolder or --userscenepath with correct path and re-run."; echo ""; exit 1
            fi
            if [ ! -z "$UserScenePath" ] && [ -z "$scenetemplatefolder" ]; then 
                scenetemplatefolder=${UserScenePath}
            fi
            if ls ${scenetemplatefolder}/${UserSceneFile} 1> /dev/null 2>&1; then 
                geho "---> User specified scene files found in: ${scenetemplatefolder}/${UserSceneFile} "; echo ""
            else 
                reho "---> Error: User specified scene ${scenetemplatefolder}/${UserSceneFile} not found." 
                reho "     Check your inputs and re-run."; echo ""; exit 1
            fi
        fi
    fi
    if [ -z "$OutPath" ]; then OutPath="${SubjectsFolder}/QC/${Modality}"; echo "Output folder path value not explicitly specified. Using default: ${OutPath}"; fi
    if [ -z "$SceneZip" ]; then SceneZip="yes"; echo "Generation of scene zip file not explicitly provided. Using default: ${SceneZip}"; fi
    # -- DWI modality-specific settings:
    if [ "$Modality" = "DWI" ]; then
        if [ -z "$DWIPath" ]; then DWIPath="Diffusion"; echo "DWI input path not explicitly specified. Using default: ${DWIPath}"; fi
        if [ -z "$DWIData" ]; then DWIData="data"; echo "DWI data name not explicitly specified. Using default: ${DWIData}"; fi
        if [ -z "$DWILegacy" ]; then DWILegacy="no"; echo "DWI legacy not specified. Using default: ${scenetemplatefolder}"; fi
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
    # -- General modality settings:
    if [ "$Modality" = "general" ] || [ "$Modality" = "General" ] || [ "$Modality" = "GENERAL" ] ; then
        if [ -z "$GeneralSceneDataFile" ]; then reho "Data input not specified"; echo ""; exit 1; fi
        if [ -z "$GeneralSceneDataPath" ]; then reho "Data input path not specified"; echo ""; exit 1; fi
    fi
    
    # -- Report parameters
    echo ""
    echo "Running $FunctionToRun processing with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Subject Folder: ${SubjectsFolder}"
    echo "   Subjects: ${CASES}"
    echo "   QC Modality: ${Modality}"
    echo "   QC Output Path: ${OutPath}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Custom QC requested: ${QCPreprocCustom}"
    echo "   HCP folder suffix: ${HCPSuffix}"
    if [ "$QCPreprocCustom" == "yes" ]; then
        echo "   Custom QC modalities: ${Modality}"
    fi
    if [ "$Modality" == "BOLD" ] || [ "$Modality" == "bold" ]; then
        if [[ ! -z ${BOLDRUNS} ]]; then
            echo "   BOLD runs requested: ${BOLDRUNS}"
        else
            echo "   BOLD runs requested: all"
        fi
    fi
    echo "   Omit default QC: ${OmitDefaults}"
    echo "   QC Scene Template Folder: ${scenetemplatefolder}"
    echo "   QC User-defined Scene: ${UserSceneFile}"
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
        if [[ ! -z ${BOLDfc} ]]; then
            echo "   BOLD FC requested: ${BOLDfc}"
            echo "   BOLD FC input: ${BOLDfcInput}"
            echo "   BOLD FC path: ${BOLDfcPath}"
        fi
    fi
    if [ "$Modality" = "general" ]; then
        echo "  Data input path: ${GeneralSceneDataPath}"
        echo "  Data input: ${GeneralSceneDataFile}"
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
            echo "   Study Log Folder: ${LogFolder}"
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
        echo "   Study Log Folder: ${LogFolder}"
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
    echo "Study Log Folder: ${LogFolder}"
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
    echo "   Study Log Folder: ${LogFolder}"
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
                reho "        ${HeaderBatch}"; echo ""
            else
                reho "---> ERROR: ${HeaderBatch} not found! Check MNAP environment variables."
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
        echo "   Study Log Folder: ${LogFolder}"
        echo "   List to generate: ${ListGenerate}"
        echo "   List path: ${ListPath}"
        echo "   List name: ${ListName}"
        echo "   Scheduler Name and Options: $Scheduler"
        echo "   Overwrite prior run: ${Overwrite}"
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
            echo "   Study Log Folder: ${LogFolder}"
            echo "   List to generate: ${ListGenerate}"
            echo "   Scheduler Name and Options: $Scheduler"
            echo "   Overwrite prior run: ${Overwrite}"
            echo "--------------------------------------------------------------"
            echo ""
            # -- Loop through all the cases
            for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
    fi
fi

# ------------------------------------------------------------------------------
#  ICAFIXhcp function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "ICAFIXhcp" ]; then
    # -- Check all the user-defined parameters:
    if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
    if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
    if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
    if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
    if [ -z "$BOLDS" ]; then reho "ERROR: <bolds_to_compute_fixica_and_postfix> not specified"; exit 1; fi
    Cluster="$RunMethod"
    if [ "$Cluster" == "2" ]; then
            if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Check optional parameters if not specified
    if [ -z ${ICAFIXFunction} ]; then ICAFIXFunction="all"; fi
    if [ -z ${Overwrite} ]; then Overwrite="no"; fi
    if [ -z ${HPFilter} ]; then Overwrite="2000"; fi
    if [ -z ${MovCorr} ]; then Overwrite="TRUE"; fi
    # -- Report parameters
    echo ""
    echo "Running $FunctionToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   SubjectsFolder: ${SubjectsFolder}"
    echo "   Subjects: ${CASES}"
    echo "   BOLDs to work on: ${BOLDS}"
    echo "   Function to run: ${ICAFIXFunction}"
    echo "   Filter: ${HPFilter}"
    echo "   Movement correction requested: ${MovCorr}"
    echo "   Overwrite prior run: ${Overwrite}"
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
    echo "   Study Log Folder: ${LogFolder}"
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
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Scheduler Name and Options: ${Scheduler}"
    echo "   Overwrite prior run: ${Overwrite}"
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
    Cluster=${RunMethod}
    # -- Report parameters
    echo ""
    echo "Running $FunctionToRun processing with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Subjects Folder: ${SubjectsFolder}"
    echo "   Subjects: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Number of Fibers: ${Fibers}"
    echo "   Model Type: ${Model}"
    echo "   Burnin Period: ${Burnin}"
    echo "   Rician flag: ${Rician}"
    echo "   Scheduler Name and Options: ${Scheduler}"
    echo "   Overwrite prior run: ${Overwrite}"
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
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Scanner: ${Scanner}"
    echo "   Using FieldMap: ${UseFieldmap}"
    echo "   Echo Spacing: ${EchoSpacing}"
    echo "   Phase Encoding Direction: ${PEdir}"
    echo "   TE value for Fieldmap: ${TE}"
    echo "   EPI Unwarp Direction: ${UnwarpDir}"
    echo "   Diffusion Data Suffix Name: ${DiffDataSuffix}"
    echo "   Overwrite prior run: ${Overwrite}"
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
    echo "   Study Log Folder: ${LogFolder}"
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
    if [ -z "$RunType" ] && [[ "$Calculation" != "dense" ]]; then reho "Error: Type of run (group or individual) missing"; exit 1; fi
    if [[ ${RunType} == "list" ]]; then
        if [ -z "$FileList" ]; then reho "Error: Group file list missing"; exit 1; fi
    fi
    if [[ ${RunType} == "individual" ]] || [[ ${RunType} == "group" ]]; then
        if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
        if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
        if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
        if [ -z "$InputFiles" ]; then reho "Error: Input file(s) value missing"; exit 1; fi
        if [ -z "$OutName" ]; then reho "Error: Output file name value missing"; exit 1; fi
        if [[ ${RunType} == "individual" ]]; then
            if [ -z "$InputPath" ]; then echo ""; reho "Warning: Input path value missing. Assuming individual folder structure for output"; fi
            if [ -z "$OutPathFC" ]; then echo ""; reho "Warning: Output path value missing. Assuming individual folder structure for output"; fi
        fi
        if [[ ${RunType} == "group" ]]; then
            if [ -z "$OutPathFC" ]; then reho "Error: Output path value missing and is needed for a group run."; exit 1; fi
        fi
    fi
    if [[ ${Calculation} == "gbc" ]]; then
        if [ -z "$TargetROI" ]; then TargetROI="[]"; fi
        if [ -z "$RadiusSmooth" ]; then RadiusSmooth="0"; fi
        if [ -z "$RadiusDilate" ]; then RadiusDilate="0"; fi
        if [ -z "$GBCCommand" ]; then GBCCommand="mFz:"; fi
        if [ -z "$Verbose" ]; then Verbose="true"; fi
        if [ -z "$ComputeTime" ]; then ComputeTime="true"; fi
        if [ -z "$VoxelStep" ]; then VoxelStep="1200"; fi
    fi
    if [[ ${Calculation} == "seed" ]]; then
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
    
    if [[ ${Calculation} == "dense" ]]; then 
        RunType="individual"; 
        if [ -z ${MemLimit} ]; then MemLimit="4"; reho "Warning: MemLimit value missing. Setting to $MemLimit"; fi
    fi

    # -- Report parameters
    echo ""
    echo "Running $FunctionToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Output Path: ${OutPathFC}"
    echo "   Extract data in CSV format: ${ExtractData}"
    echo "   Type of fc calculation: ${Calculation}"
    echo "   Type of run: ${RunType}"
    echo "   Calculate Covariance: ${Covariance}"
    if [[ ${Calculation} != "dense" ]]; then
        echo "   Ignore frames: ${IgnoreFrames}"
        echo "   Mask out frames: ${MaskFrames}"
    else
        echo "   Memory Limit: ${MemLimit}"
    fi
    if [[ ${RunType} == "list" ]]; then
        echo "   FileList: ${FileList}"
    fi
    if [[ ${RunType} == "individual" ]] || [[ ${RunType} == "group" ]]; then
        echo "   Study Folder: ${StudyFolder}"
        echo "   Subjects Folder: ${SubjectsFolder}"
        echo "   Subjects: ${CASES}"
        echo "   Input Files: ${InputFiles}"
        echo "   Input Path for Data: ${SubjectFolder}/<subject_id>/${InputPath}"
        echo "   Output Name: ${OutName}"
    fi
    if [[ ${Calculation} == "gbc" ]]; then
        echo "   Target ROI for GBC: ${TargetROI}"
        echo "   Radius Smooth for GBC: ${RadiusSmooth}"
        echo "   Radius Dilate for GBC: ${RadiusDilate}"
        echo "   GBC Commands to run: ${GBCCommand}"
        echo "   Verbose outout: ${Verbose}"
        echo "   Print Compute Time: ${ComputeTime}"
        echo "   Voxel Steps to use: ${VoxelStep}"
    fi
    if [[ ${Calculation} == "seed" ]]; then
        echo "   ROI Information for seed fc: ${ROIInfo}"
        echo "   FC Commands to run: ${FCCommand}"
        echo "   Method to compute fc: ${Method}"
    fi
    echo "--------------------------------------------------------------"
    echo ""
    if [[ ${RunType} == "individual" ]]; then
        for CASE in ${CASES}; do
            ${FunctionToRun} ${CASE}
        done
    fi
    if [[ ${RunType} == "group" ]]; then
        CASE=`echo "$CASES" | sed 's/ /,/g'`
        echo $CASE
        ${FunctionToRun} ${CASE}
    fi
    if [[ ${RunType} == "list" ]]; then
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
    echo "   Study Log Folder: ${LogFolder}"
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
    if [ -z "$WayTotal" ]; then WayTotal="no"; reho "--waytotal normalized data not specified. Assuming default [no]"; fi
    # -- Report parameters
    echo ""
    echo "Running $FunctionToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Subjects Folder: ${SubjectsFolder}"
    echo "   Subjects: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Matrix version used for input: ${MatrixVersion}"
    echo "   File to use for parcellation: ${ParcellationFile}"
    echo "   Dense DWI Parcellated Connectome Output Name: ${OutName}"
    echo "   Waytotal normalization: ${WayTotal}"
    echo "   Overwrite prior run: ${Overwrite}"
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
    echo "   Study Log Folder: ${LogFolder}"
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
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Matrix version used for input: ${MatrixVersion}"
    echo "   Dense dconn seed reduction: ${SeedFile}"
    echo "   Dense DWI Parcellated Connectome Output Name: ${OutName}"
    echo "   Waytotal normalization: ${WayTotal}"
    echo "   Overwrite prior run: ${Overwrite}"
    echo "--------------------------------------------------------------"
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  autoPtx function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "autoPtx" ]; then
    # -- Check all the user-defined parameters:
    if [ -z "$FunctionToRun" ]; then reho "Error: Explicitly specify name of function in flag or use function name as first argument (e.g. mnap <function_name> followed by flags) to run missing"; exit 1; fi
    if [ -z "$StudyFolder" ]; then reho "Error: Study folder missing"; exit 1; fi
    if [ -z "$SubjectsFolder" ]; then reho "Error: Subjects folder missing"; exit 1; fi
    if [ -z "$CASES" ]; then reho "Error: List of subjects missing"; exit 1; fi
    Cluster="$RunMethod"
    if [ "$Cluster" == "2" ]; then
        if [ -z "$Scheduler" ]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    if [[ -z ${BedPostXFolder} ]]; then BedPostXFolder=${SubjectsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX; fi
    
    # -- Report parameters
    echo ""
    echo "Running $FunctionToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Subjects Folder: ${SubjectsFolder}"
    echo "   Subjects: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   BedpostX Folder: ${BedPostXFolder} "
    echo "--------------------------------------------------------------"
    echo ""
    for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

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
    echo "   Study Log Folder: ${LogFolder}"
    echo "--------------------------------------------------------------"
    echo ""
    for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  ProbtrackxGPUDense function loop
# ------------------------------------------------------------------------------

if [ "$FunctionToRun" == "ProbtrackxGPUDense" ]; then
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
    # -- Optional parameters
    if [ -z ${ScriptsFolder} ]; then ScriptsFolder="${HCPPIPEDIR_dMRITracFull}/Tractography_gpu_scripts"; fi
    if [ -z ${OutFolder} ]; then OutFolder="${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography"; fi
    if [ -z ${InFolder} ]; then InFolder="${SubjectsFolder}/${CASE}/hcp"; fi
    minimumfilesize="100000000"

    # -- Report parameters
    echo ""
    echo "Running $FunctionToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Subjects Folder: ${SubjectsFolder}"
    echo "   Subjects: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Scheduler: ${Scheduler}"
    echo "   probtraxkX GPU scripts Folder: ${ScriptsFolder}"
    echo "   Input HCP folder: ${InFolder}"
    echo "   Output folder for probtrackX results: ${OutFolder}"
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
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Run Method: ${RunMethod}"
    echo "   Modality: ${Modality}"
    echo "   AWS URI Path: ${Awsuri}"
    echo "--------------------------------------------------------------"
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${FunctionToRun} ${CASE}; done
fi



