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
# * qunex.sh is a connector wrapper
#   developed as for front-end bash integration for the Qu|Nex Suite
#
# ## LICENSE
#
# * The qunex.sh = the "Software"
# * This Software conforms to the license outlined in the Qu|Nex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
#
#~ND~END~

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= CODE START =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=

QuNexCommands="nitoolsHelp gmriFunction dataSync organizeDicom mapHCPFiles hcpdLegacy eddyQC DWIDenseParcellation DWIDenseSeedTractography computeBOLDfc structuralParcellation BOLDParcellation ICAFIXhcp ROIExtract FSLDtifit FSLBedpostxGPU autoPtx pretractographyDense ProbtrackxGPUDense AWSHCPSync runQC RunQC QCPreproc runTurnkey commandExecute showVersion environment"

# ------------------------------------------------------------------------------
#  -- Setup color outputs
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
#  -- Splash call
# ------------------------------------------------------------------------------

show_splash() {
 geho ""
 geho " Logged in as User: `whoami`                                                 "
 geho " Node info: `hostname`                                                       "
 geho " OS: $OSInfo $OperatingSystem                                                "
 geho ""
 geho ""
 geho "        ██████\                  ║      ██\   ██\                    "
 geho "       ██  __██\                 ║      ███\  ██ |                   "
 geho "       ██ /  ██ |██\   ██\       ║      ████\ ██ | ██████\ ██\   ██\ "
 geho "       ██ |  ██ |██ |  ██ |      ║      ██ ██\██ |██  __██\\\\\██\ ██  |"
 geho "       ██ |  ██ |██ |  ██ |      ║      ██ \████ |████████ |\████  / "
 geho "       ██ ██\██ |██ |  ██ |      ║      ██ |\███ |██   ____|██  ██<  "
 geho "       \██████ / \██████  |      ║      ██ | \██ |\███████\██  /\██\ "
 geho "        \___███\  \______/       ║      \__|  \__| \_______\__/  \__|"
 geho "            \___|                ║                                   "
 geho ""
 geho "                       DEVELOPED & MAINTAINED BY: "
 geho ""
 geho "                    Anticevic Lab, Yale University                           "
 geho "               Mind & Brain Lab, University of Ljubljana                     "
 geho "                     Murray Lab, Yale University                             "
 geho ""
 geho "                      COPYRIGHT & LICENSE NOTICE:                            "
 geho ""
 geho "Use of this software is subject to the terms and conditions defined by the   "
 geho "Yale University Copyright Policies: "
 geho "http://ocr.yale.edu/faculty/policies/yale-university-copyright-policy "
 geho "and the terms and conditions defined in the file 'LICENSE.md' which is "
 geho "a part of the Qu|Nex Suite source code package: "
 geho "https://bitbucket.org/hidradev/qunextools/src/master/LICENSE.md"
 geho ""
}

# ------------------------------------------------------------------------------
#  -- General help usage
# ------------------------------------------------------------------------------

show_usage() {
 echo ""
 echo "General Qu|Nex Usage                             "
 echo "====================                        "
 echo ""
 echo "General Command Call Syntax:: "
 echo ""
 echo "  qunex --command=<command_name> \ "
 echo "        --parameterA=<parameter_A_specification> \ "
 echo "        --parameterB='<parameter_B_specification>' \ "
 echo "        --parameterC='<parameter_C_specification>' "
 echo "        --parameterN='<parameter_N_specification>' "
 echo ""
 echo "Obtaining Command Help and Usage::"
 echo ""
 echo " qunex ?<command_name> "
 echo " qunex <command_name> "
 echo ""
 echo ""
 echo "Conventions used in help and documentation:"
 echo ""
 echo "- Square brackets []: Specify a value that is optional."
 echo "  Note: Value within brackets is the default value."
 echo "- Angle brackets <>: Contents describe what should go there."
 echo "- Dashes or flags -- : Define input variables."
 echo ""
 echo ""
 echo "Overview of Qu|Nex Commands    "
 echo "==========================="
 echo ""
 echo "To obtain a full listing of all Qu|Nex-supported NITools commands run:: "
 echo ""
 echo " qunex --allcommands "
 echo ""
 echo ""
 geho "'Connector' Commands for Turnkey Processing and Misc. Analyses            "
 geho "--------------------------------------------------------------"
 echo ""
 echo "Connector commands are located in::"
 echo ""
 echo " $TOOLS/$QUNEXREPO/connector"
 echo ""
 echo "Qu|Nex Suite workflows is integrated via BASH 'connector' commands."
 echo "The connector commands also contain 'stand alone' processing or analyses tools."
 echo "These can be called either directly or via the qunex wrapper"
 echo ""
 echo ""
 geho "General NeuroImaging Utilities (NIUtilities) for Preprocessing and Analyses  "
 geho "--------------------------------------------------------------------------- "
 echo ""
 echo "NIUtilities are located in:: $TOOLS/$QUNEXREPO/niutilities"
 echo ""
 echo "Qu|Nex Suite workflows contain additional python-based 'general mri (gmri) "
 echo "utilities. These are accessed either directly via 'gmri' command from the "
 echo "terminal. Alternatively the 'qunex' connector wrapper parses all commands via "
 echo "'gmri' package as standard input."
 echo ""
 echo ""
 geho "Neuroimaging Tools (NITools) for Signal Processing and Statistics   "
 geho "----------------------------------------------------------------- "
 echo ""
 echo "NITools tools are located in::"
 echo ""
 echo " $TOOLS/$QUNEXREPO/nitools"
 echo ""    
 echo "The Qu|Nex package contain a number of matlab-based stand-alone commands. These "
 echo "tools are used across various Qu|Nex packages, but can be accessed as "
 echo "stand-alone command within Matlab. Help and documentation is embedded within "
 echo "each stand-alone command via standard Matlab help call."
 echo ""
 echo ""
}

qunexFailed() {
    reho ''
    reho ' ▄▄▄▄▄▄▄         ||  ▄▄   ▄▄                                                 '
    reho ' ▓▓    ▓         ||  ▓▓▓▄ ▓▓                ▓▓▓▓▓ ▄▓▓▓▓  ▓ ▄▓    ▄▓▓▓ ▓▓▓▄   '
    reho ' ▓▓  ▓ ▓  ▓   ▓  ||  ▓▓ ▐▓▓▓ ▄▄▄▄ ▀▓▓ ▓▓▀   ▓▓    ▓  ▓▓ ▓▓ ▓▓   ▄▓▓▄  ▓  ▓▓  '
    reho ' ▓▓▄▄▓▄▓  ▓▓  ▓  ||  ▓▓   ▓▓ ▓▄▄▓    ▓▄     ▓▓▀▀  ▓▓▓▓▓ ▓▌ ▓▓   ▀▓▓   ▓  ▓▓  '
    reho '     ▓▄▄  ▓▓▄▄▓  ||  ▓▓    ▓ ▓▄▄  ▄▓▓ ▓▓▄   ▓     ▓▀ ▓  ▓  ▓▓▓▀▀ ▓▓▓▓ ▓▓▓▀   ' 
    reho '                 ||                                                          '
    reho ''
}
 
qunexPassed() {
    geho ''
    geho '    ______         ║   _   _               ____                        _  '
    geho '   / ___  \_   _   ║  | \ | | _____  __   |  _ \ __ _ ___ ___  ___  __| | '
    geho '  | |   | | | | |  ║  |  \| |/ _ \ \/ /   | |_) / _` / __/ __|/ _ \/ _` | '
    geho '  | |_/\| | |_| |  ║  | |\  |  __/>  <    |  __| (_| \__ \__ |  __| (_| | '
    geho '   \__\ \ /\__,_|  ║  |_| \_|\___/_/\_\   |_|   \__,_|___|___/\___|\__,_| '
    geho '       \_\         ║                                                      '
    geho ''
}

# =======================================================================================================
# =========================================== CODE STARTS HERE ==========================================
# =======================================================================================================

# ------------------------------------------------------------------------------------------------------
#  -- Help calls for NIUtilities, NITools and Connector Functions
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
show_processingcommandlist_gmri() {
        echo ""
        gmri -l
        echo ""
}
show_processingoptions_gmri() {
        echo ""
        gmri -o
        echo ""
}
show_allcommands_gmri() {
        echo ""
        echo ""
        geho "Listing of all Qu|Nex supported NIUtilitties commands"
        geho "-----------------------------------------------------"
        echo ""
        gmri -available | sed 1,1d
        echo ""
}
show_usage_nitoolsHelp() {
        echo ""
        echo ""
        geho "Listing of all Qu|Nex supported NITools MATLAB commands"
        geho "-------------------------------------------------------"
        echo ""
        MatlabFunctions=`ls $TOOLS/$QUNEXREPO/nitools/*/*.m | grep -v "archive/"`
        MatlabFunctionsfcMRI=`ls $TOOLS/$QUNEXREPO/nitools/*/*.m | grep -v "archive/" | grep "/fcMRI/"`
        MatlabFunctionsGeneral=`ls $TOOLS/$QUNEXREPO/nitools/*/*.m | grep -v "archive/" | grep "/general/"`
        MatlabFunctionsNIMG=`ls $TOOLS/$QUNEXREPO/nitools/img/\@nimage/*.m`
        MatlabFunctionsStats=`ls $TOOLS/$QUNEXREPO/nitools/*/*.m | grep -v "archive/" | grep "stats"`
        echo "Qu|Nex NITools functional connectivity tools"; echo ""
        for MatlabFunction in $MatlabFunctionsfcMRI; do
            echo "- $MatlabFunction";
        done
        echo ""
        echo "Qu|Nex NITools general image manipulation tools"; echo ""
        for MatlabFunction in $MatlabFunctionsGeneral; do
            echo "- $MatlabFunction";
        done
        echo ""
        echo "Qu|Nex NITools specific image analyses tools"; echo ""
        for MatlabFunction in $MatlabFunctionsNIMG; do
            echo "- $MatlabFunction";
        done
        echo ""
        echo "Qu|Nex NITools statistical tools"; echo ""
        for MatlabFunction in $MatlabFunctionsStats; do
            echo "- $MatlabFunction";
        done
        echo ""
}
show_allcommands_connector() {
 echo ""
 echo ""
 geho "Listing of all Qu|Nex supported Connector commands"
 geho "--------------------------------------------------"
 echo ""
 echo "Connector functions are located in::"
 echo ""
 echo " $TOOLS/$QUNEXREPO/connector"
 echo ""
 echo "Qu|Nex Suite workflows is integrated via BASH 'connector' functions."
 echo "The connector function also contain 'stand alone' processing or analyses tools."
 echo "These can be called either directly or via the qunex wrapper"
 echo ""
 echo "Qu|Nex Turnkey functions"
 echo "------------------------"
 echo ""
 echo "organizeDicom "
 echo "     sort DICOMs and setup nifti files from DICOMs"
 echo ""
 echo "mapHCPFiles "
 echo "     setup data structure for hcp processing"
 echo ""
 echo "runTurnkey"
 echo "     turnkey execution of Qu|Nex workflow compatible with XNAT Docker engine"
 echo ""
 echo "QC functions"
 echo "------------"
 echo ""
 echo "runQC"
 echo "     run visual qc for a given modality: raw nifti,t1w,tw2,myelin,bold,dwi"
 echo ""
 echo "DWI processing, QC, analyses & probabilistic tractography functions"
 echo "-------------------------------------------------------------------"
 echo ""
 echo "hcpdLegacy"
 echo "     diffusion image processing for data with or without standard fieldmaps"
 echo ""
 echo "eddyQC"
 echo "     run quality control on diffusion datasets following eddy outputs"
 echo ""
 echo "FSLDtifit"
 echo "     run FSL's dtifit tool (cluster usable)"
 echo ""
 echo "FSLBedpostxGPU"
 echo "     run FSL bedpostx with GPU"
 echo ""
 echo "pretractographyDense"
 echo "     generates space for whole-brain dense connectomes"
 echo ""
 echo "ProbtrackxGPUDense"
 echo "     run FSL's probtrackx for whole brain & generates dense whole brain "
 echo "     connectomes"
 echo ""
 echo "DWIDenseSeedTractography"
 echo "     reduce dense DWI tractography data using a seed structure"
 echo ""
 echo "Miscellaneous analyses"
 echo "----------------------"
 echo ""
 echo "computeBOLDfc"
 echo "     computes seed or GBC BOLD functional connectivity"
 echo ""
 echo "structuralParcellation"
 echo "     parcellate myelin or thickness"
 echo ""
 echo "BOLDParcellation"
 echo "     parcellate BOLD data and generate pconn files"
 echo ""
 echo "DWIDenseParcellation"
 echo "     parcellate dense dwi tractography data"
 echo ""
 echo "ROIExtract"
 echo "     extract data from pre-specified ROIs in CIFTI or NIFTI"
 echo ""
 echo "AWSHCPSync"
 echo "     sync hcp data from aws s3 cloud"
 echo ""
 echo "dataSync"
 echo "     sync/backup data across hpc cluster(s)"
 echo ""
 echo ""
}

# ---------------------------------------------------------------------------------------------------------------
#  -- Master Execution and Logging -- https://bitbucket.org/oriadev/qunex/wiki/Overview/Logging.md
# ---------------------------------------------------------------------------------------------------------------

connectorExec() {

# -- Set the time stamp for given job
TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`

if [[ ${CommandToRun} == "runTurnkey" ]]; then
   if [[ ! -z `echo ${TURNKEY_STEPS} | grep 'createStudy'` ]]; then
       if [[ ! -d ${WORKDIR} ]]; then 
          mkdir -p ${WORKDIR} &> /dev/null
       fi
   fi
fi

Platform="Platform Information: `uname -a`"

# -- Check if study folder is created
if [[ ! -f ${StudyFolder}/.qunexstudy ]]; then 
    echo "Qu|Nex study folder specification in ${StudyFolder} not found. Generating now..."
    gmri createStudy "${StudyFolder}"
fi

# -- Check if part of the Qu|Nex file hierarchy is missing
QuNexFolders="analysis/scripts processing/logs/comlogs processing/logs/runlogs processing/lists processing/scripts processing/scenes/QC/T1w processing/scenes/QC/T2w processing/scenes/QC/myelin processing/scenes/QC/BOLD processing/scenes/QC/DWI info/demographics info/hcpls info/tasks info/stimuli info/bids sessions/inbox/MR sessions/inbox/EEG sessions/inbox/BIDS sessions/inbox/behavior sessions/inbox/concs sessions/inbox/events sessions/archive/MR sessions/archive/EEG sessions/archive/BIDS sessions/archive/behavior sessions/specs sessions/QC"
for QuNexFolder in ${QuNexFolders}; do
    if [[ ! -d ${StudyFolder}/${QuNexFolder} ]]; then
          echo "Qu|Nex folder ${StudyFolder}/${QuNexFolder} not found. Generating now..."; echo ""
          mkdir -p ${StudyFolder}/${QuNexFolder} &> /dev/null
    fi
done

# -- Add check in case the sessions folder is distinct from the default name
QuNexSessionsFolders="${SessionsFolder}/inbox/MR ${SessionsFolder}/inbox/EEG ${SessionsFolder}/inbox/BIDS ${SessionsFolder}/inbox/behavior ${SessionsFolder}/inbox/concs ${SessionsFolder}/inbox/events ${SessionsFolder}/archive/MR ${SessionsFolder}/archive/EEG ${SessionsFolder}/archive/BIDS ${SessionsFolder}/archive/HCPLS ${SessionsFolder}/archive/behavior ${SessionsFolder}/specs ${SessionsFolder}/QC"
for QuNexSessionsFolder in ${QuNexSessionsFolders}; do
    if [[ ! -d ${QuNexSessionsFolder} ]]; then
          echo "Qu|Nex folder ${QuNexSessionsFolder} not found. Generating now..."; echo ""
          mkdir -p ${QuNexSessionsFolder} &> /dev/null
    fi
done

# -- If logfolder flag set then set it and set master log
if [[ -z ${LogFolder} ]]; then
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
Runlog="${MasterRunLogFolder}/Log-${CommandToRun}_${TimeStamp}.log"

# -- Comlog
#    Specification:  tmp_<command_name>[_B<N>]_<session code>_<date>_<hour>.<minute>.<microsecond>.log
#    Specification:  error_<command_name>[_B<N>]_<session code>_<date>_<hour>.<minute>.<microsecond>.log
#    Specification:  done_<command_name>[_B<N>]_<session code>_<date>_<hour>.<minute>.<microsecond>.log
#    Example:        done_ComputeBOLDStats_pb0986_2017-05-06_16.16.1494101784.log
#

ComlogTmp="${MasterComlogFolder}/tmp_${CommandToRun}_${CASE}_${TimeStamp}.log"; touch ${ComlogTmp}; chmod 777 ${ComlogTmp}
ComRun="${MasterComlogFolder}/Run_${CommandToRun}_${CASE}_${TimeStamp}.sh"; touch ${ComRun}; chmod 777 ${ComRun}
ComlogError="${MasterComlogFolder}/error_${CommandToRun}_${CASE}_${TimeStamp}.log"
ComlogDone="${MasterComlogFolder}/done_${CommandToRun}_${CASE}_${TimeStamp}.log"
CompletionCheckPass="${MasterComlogFolder}/CompletionCheck_${CommandToRun}_${TimeStamp}.Pass"
CompletionCheckFail="${MasterComlogFolder}/CompletionCheck_${CommandToRun}_${TimeStamp}.Fail"

# echo "--------- DEBUG INFO ------------"
# echo "MasterComlogFolder: ${MasterComlogFolder}"
# echo "QuNexCallToRun: ${QuNexCallToRun}"
# echo "CASE: ${CASE}"
# echo "TimeStamp: ${TimeStamp}"
# echo "ComlogTmp: ${ComlogTmp}"
# echo "RunLog: ${Runlog}"

# -- Batchlog
#    <batch system>_<command name>_job<job number>.<date>_<hour>.<minute>.<microsecond>.log

# -- Code for debugging
echo ""
cyaneho "--------------------- Full call to run: -----------------------"
echo ""
cyaneho "${QuNexCallToRun}"
echo ""
cyaneho "--------------------------------------------------------------"
echo ""
echo ""

# -- Run commands
echo "${QuNexCallToRun}" >> ${Runlog}
echo "#!/bin/bash" >> ${ComRun}
echo "export PYTHONUNBUFFERED=1" >> ${ComRun}
echo "${QuNexCallToRun}" >> ${ComRun}
chmod 777 ${ComRun}
 
# ComRunSet="cd ${MasterRunLogFolder}; echo ${QuNexCallToRun} >> ${Runlog}; echo 'export PYTHONUNBUFFERED=1; ${QuNexCallToRun}' >> ${ComRun}; chmod 777 ${ComRun}"

# -- Check that $ComRun is set properly
echo ""; if [ ! -f "${ComRun}" ]; then reho " ERROR: ${ComRun} file not found. Check your inputs"; echo ""; return 1; fi
ComRunSize=`wc -c < ${ComRun}` > /dev/null 2>&1
echo ""; if [[ "${ComRunSize}" == 0 ]]; then > /dev/null 2>&1; reho " ERROR: ${ComRun} file found but has no content. Check your inputs"; echo ""; return 1; fi


# -- Define command to execute
ComRunExec=". ${ComRun} 2>&1 | tee -a ${ComlogTmp}"
# -- Acceptance tests
#ComComplete="if [[ $(cat ${ComlogTmp}| grep -c 'Successful completion') != 0 ]]; then echo 'Log: ${ComlogDone}' >> ${CompletionCheckPass}; echo '===> Successful completion of ${CommandToRun}' >> ${CompletionCheckPass}; fi"
#ComError="if [[ $(cat ${ComlogTmp}| grep -c 'ERROR') != 0 ]]; then echo 'Log: ${ComlogError}' >> ${CompletionCheckFail}; echo '===> ERROR in ${CommandToRun}' >> ${CompletionCheckFail}; fi"
ComComplete="cat ${ComlogTmp} | grep 'Successful completion' > ${CompletionCheckPass}"
ComError="cat ${ComlogTmp} | grep 'ERROR' > ${CompletionCheckFail}"
# -- Command to perform acceptance test
ComRunCheck="if [[ -e ${CompletionCheckPass} && ! -s ${CompletionCheckFail} ]]; then mv ${ComlogTmp} ${ComlogDone}; echo ''; geho ' ===> Successful completion of ${CommandToRun}. Check final Qu|Nex log output:'; echo ''; geho '    ${ComlogDone}'; qunexPassed; echo ''; else mv ${ComlogTmp} ${ComlogError}; echo ''; reho ' ===> ERROR during ${CommandToRun}. Check final Qu|Nex error log output:'; echo ''; reho '    ${ComlogError}'; echo ''; qunexFailed; fi"
# -- Combine final string of commands
ComRunAll="${ComRunExec}; ${ComComplete}; ${ComError}; ${ComRunCheck}"


# -- Run the commands locally
if [[ ${Cluster} == 1 ]]; then
    geho "--------------------------------------------------------------"
    echo ""
    geho "   Running ${CommandToRun} locally on `hostname`"
    geho "   Command log:     ${Runlog}  "
    geho "   Command output: ${ComlogTmp} "
    echo ""
    geho "--------------------------------------------------------------"
    echo ""
    eval "${ComRunAll}"
fi
# -- Run the commands via scheduler
if [[ ${Cluster} == 2 ]]; then
    cd ${MasterRunLogFolder}
    gmri schedule command="${ComRunAll}" settings="${Scheduler}"
    geho "--------------------------------------------------------------"
    echo ""
    geho "   Data successfully submitted to scheduler"
    geho "   Scheduler details: ${Scheduler}"
    geho "   Command log:     ${Runlog}  "
    geho "   Command output: ${ComlogTmp} "
    echo ""
    geho "--------------------------------------------------------------"
    echo ""
fi
}

# ---------------------------------------------------------------------------------------------------------------
#  -- runTurnkey - Turnkey execution of Qu|Nex workflow via the XNAT docker engine
# ---------------------------------------------------------------------------------------------------------------

runTurnkey() {
# -- Specify command variable
unset QuNexCallToRun
QuNexCallToRun="${TOOLS}/${QUNEXREPO}/connector/functions/RunTurnkey.sh --bolds=\"${BOLDS// /,}\" ${runTurnkeyArguments} --sessions=\"${CASE}\" --turnkeysteps=\"${TURNKEY_STEPS// /,}\" --sessionids=\"${SESSIONIDS}\""
connectorExec
}

show_usage_runTurnkey() {
${TOOLS}/${QUNEXREPO}/connector/functions/RunTurnkey.sh
}

# ---------------------------------------------------------------------------------------------------------------
#  -- organizeDicom - Sort original DICOMs into folders and generates NIFTI files using sortDicom and dicom2niix
# ---------------------------------------------------------------------------------------------------------------

organizeDicom() {
# -- Note: This command passes parameters into two NIUtilities commands: sortDicom and dicom2niix
mkdir ${SessionsFolder}/${CASE}/dicom &> /dev/null
if [[ ${Overwrite} == "yes" ]]; then
    echo ""
    reho "===> Removing prior DICOM run log. Will initiate new run."
    rm -f ${SessionsFolder}/${CASE}/dicom/DICOM-Report.txt &> /dev/null
fi
echo ""
echo "===> Checking for presence of ${SessionsFolder}/${CASE}/dicom/DICOM-Report.txt"
echo ""
# -- Check if DICOM-Report.txt is there
if (test -f ${SessionsFolder}/${CASE}/dicom/DICOM-Report.txt); then
    echo ""
    geho "===> Found ${SessionsFolder}/${CASE}/dicom/DICOM-Report.txt"
    geho "    Note: To re-run set --overwrite='yes'"
    echo ""
    geho " ... $CASE ---> organizeDicom done"
    echo ""
    return 0
fi
# -- Check if inbox missing or is empty
if [ ! -d ${SessionsFolder}/${CASE}/dicom ]; then
    reho "===> ${SessionsFolder}/${CASE}/dicom folder not found. Checking for ${SessionsFolder}/${CASE}/inbox/"; echo ""
    if [ ! -d ${SessionsFolder}/${CASE}/inbox ]; then
        reho "===> ${SessionsFolder}/${CASE}/inbox not found. Make sure your DICOMs are present inside ${SessionsFolder}/${CASE}/inbox/"; echo ""
        exit 1
    fi
fi
if [ -d ${SessionsFolder}/${CASE}/dicom ]; then
     DicomCheck=`ls ${SessionsFolder}/${CASE}/dicom/`
     InboxCheck=`ls ${SessionsFolder}/${CASE}/inbox/`
     if [[ ${InboxCheck} != "" ]]; then
         reho "===> ${SessionsFolder}/${CASE}/dicom/ found and data exists."; echo ""
         if [[ ${InboxCheck} == "" ]]; then
             reho "===> ${SessionsFolder}/${CASE}/inbox/ found but empty. Will re-run sortDicom from ${SessionsFolder}/${CASE}/dicom"; echo ""
         fi
    fi
fi
# -- Specify command variable
unset CommandToRun
ComA="cd ${SessionsFolder}/${CASE}"
ComB="gmri sortDicom folder=. "
ComC="gmri dicom2niix unzip=${Unzip} gzip=${Gzip} clean=${Clean} verbose=${VerboseRun} parelements=${ParElements} sessionid=${CASE}"
ComD="slicesdir ${SessionsFolder}/${CASE}/nii/*.nii*"
QuNexCallToRun="${ComA}; ${ComB}; ${ComC}; ${ComD}"
# -- Connector execute function
connectorExec
}

show_usage_organizeDicom() {
 echo ""
 echo "qunex organizeDicom"
 echo ""
 echo "This command expects a set of raw DICOMs in <sessionsfolder>/<case>/inbox "
 echo "DICOMs are organized, gzipped and converted to NIFTI format for additional "
 echo "processing."
 echo ""
 echo "session.txt files will be generated with id and sessions matching the <case>."
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "--sessionsfolder  Path to study folder that contains sessions. If missing then "
 echo "                  optional paramater --folder needs to be provided."
 echo "--sessions        Comma-separated list of sessions to run. If missing then "
 echo "                  --folder needs to be provided for a single-session run."
 echo "--folder          The base sessions folder with the dicom subfolder that holds "
 echo "                  session numbered folders with dicom files. [.]"
 echo "--overwrite>      Explicitly force a re-run of organizeDicom"
 echo "--clean           Whether to remove preexisting NIfTI files (yes), leave them "
 echo "                  and abort (no) or ask interactively (ask). [ask]"
 echo "--unzip           If the dicom files are gziped whether to unzip them (yes), "
 echo "                  leave them be and abort (no) or ask interactively (ask). [ask]"
 echo "--gzip            After the dicom files were processed whether to gzip them "
 echo "                  (yes), leave them ungzipped (no) or ask interactively (ask). "
 echo "                  [ask]"
 echo "--verbose         Whether to be report on the progress (True) or not (False). "
 echo "                  [True]"
 echo "--parelements     Degree of parallelism (number of parallel processes) to run "
 echo "                  dcm2nii conversion with."
 echo "                  The number is one by defaults, if specified as 'all', all "
 echo "                  available resource are utilized."
 echo ""
 echo "--scheduler       A string for the cluster scheduler (e.g. LSF, PBS or SLURM) "
 echo "                  followed by relevant optionsm e.g. for SLURM the string would "
 echo "                  look like this:: "
 echo ""
 echo "                  --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
 echo ""
 echo "EXAMPLE USE"
 echo "==========="
 echo ""
 echo "::"
 echo ""
 echo " qunex organizeDicom --sessionsfolder='<folder_with_sessions>' \ "
 echo " --sessions='<comma_separarated_list_of_cases>' "
 echo " --scheduler='<name_of_scheduler_and_options>'"
 echo ""
}

# ------------------------------------------------------------------------------------------------------
#  -- mapHCPFiles - Setup the HCP File Structure
# ------------------------------------------------------------------------------------------------------

mapHCPFiles() {
# -- Specify command variable
if [[ ${Overwrite} == "yes" ]]; then
    HLinks=`ls ${SessionsFolder}/${CASE}/hcp/${CASE}/*/*nii* 2>/dev/null`; for HLink in ${HLinks}; do unlink ${HLink}; done
fi
QuNexCallToRun="cd ${SessionsFolder}/${CASE}; echo '--> running mapHCPFiles for ${CASE}'; echo ''; gmri setupHCP"
# -- Connector execute function
connectorExec
}
show_usage_mapHCPFiles() {
 echo ""
 echo "qunex mapHCPFiles"
 echo ""
 echo "This command maps the Human Connectome Project folder structure for "
 echo "preprocessing. It should be executed after proper organizeDicom and session.txt "
 echo "file has been vetted and the session_hcp.txt file was generated."
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "--sessionsfolder    Path to study folder that contains sessions"
 echo "--sessions          Comma separated list of sessions to run"
 echo "--scheduler         A string for the cluster scheduler (e.g. LSF, PBS or SLURM) "
 echo "                    followed by relevant options"
 echo ""
 echo "For SLURM scheduler the string would look like this via the qunex call:: "
 echo ""
 echo " --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
 echo ""
 echo "EXAMPLE USE"
 echo "==========="
 echo ""
 echo "Example with flagged parameters for a local run::"
 echo ""
 echo " qunex mapHCPFiles --sessionsfolder='<folder_with_sessions>' \ "
 echo "     --sessions='<comma_separarated_list_of_cases>' \ "
 echo ""
 echo "Example with flagged parameters for submission to the scheduler::"
 echo ""
 echo " qunex mapHCPFiles --sessionsfolder='<folder_with_sessions>' \ "
 echo "     --sessions='<comma_separarated_list_of_cases>' \ "
 echo "     --scheduler='<name_of_cluster_scheduler_and_options>' \ "
 echo ""
}

# ------------------------------------------------------------------------------------------------------
#  -- dataSync - Sync files to Yale HPC and back to the Yale server after HCP preprocessing
# ------------------------------------------------------------------------------------------------------

dataSync() {
# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/connector/functions/DataSync.sh \
--syncfolders="${SyncFolders}" \
--sessions="${CASE}" \
--syncserver="${SyncServer}" \
--synclogfolder="${SyncLogFolder}" \
--syncdestination="${SyncDestination}""
# -- Connector execute function
connectorExec
}
show_usage_dataSync() {
 echo ""
 echo "qunex dataSync"
 echo ""
 echo "This command runs rsync across the entire folder structure based on user "
 echo "specifications."
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "--syncfolders         Set path for folders that contains studies for syncing"
 echo "--syncserver          Set sync server <UserName@some.server.address> or 'local' "
 echo "                      to sync locally"
 echo "--syncdestination     Set sync destination path"
 echo "--synclogfolder       Set log folder"
 echo "--sessions            Set input sessions for backup. "
 echo "                      If set, then --backupfolders path has to contain input "
 echo "                      sessions."
 echo ""
 echo "EXAMPLE USE"
 echo "==========="
 echo ""
 echo "::"
 echo ""
 echo " qunex --command=dataSync \ "
 echo "   --syncfolders=<path_to_folders> \ "
 echo "   --syncserver=<sync_server> \ "
 echo "   --syncdestination=<destination_path> \ "
 echo "   --synclogfolder=<path_to_log_folder>  \ "
 echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- hcpdLegacy - Executes the Diffusion Processing Script via FUGUE implementation for legacy data - (needed for legacy DWI data that is non-HCP compliant without counterbalanced phase encoding directions needed for topup)
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

hcpdLegacy() {
# -- Unique requirements for This command:
#    Needs CUDA libraries to run eddy_cuda (10x faster than on a CPU)

# -- Specify command variable
QuNexCallToRun="${TOOLS}/${QUNEXREPO}/connector/functions/DWIPreprocPipelineLegacy.sh \
--sessionsfolder=${SessionsFolder} \
--session=${CASE} \
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
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/DWIPreprocPipelineLegacy.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- eddyQC - Executes the DWI EddyQ C (DWIEddyQC.sh) via the Qu|Nex connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

eddyQC() {
# -- Check if eddy_squad and eddy_quad exist in user path
EddySquadCheck=`which eddy_squad`
EddyQuadCheck=`which eddy_quad`
if [[ -z ${EddySquadCheck} ]] || [[ -z ${EddySquadCheck} ]]; then
    echo ""
    reho " -- ERROR: EDDY QC does not seem to be installed on this system."
    echo ""
    exit 1
fi
# -- INPUTS:  eddy-cleaned DWI Data
# -- OUTPUTS: located in <eddyBase>.qc per EDDY QC specification

# -- Specify command variable
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/connector/functions/DWIeddyQC.sh \
--sessionsfolder=${SessionsFolder} \
--session=${CASE} \
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
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/DWIeddyQC.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- DWIDenseParcellation - Executes the Diffusion Parcellation Script (DWIDenseParcellation.sh) via the Qu|Nex connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

DWIDenseParcellation() {
#DWIOutput="${SessionsFolder}/${CASE}/hcp/$CASE/MNINonLinear/Results/Tractography"
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/connector/functions/DWIDenseParcellation.sh \
--sessionsfolder=${SessionsFolder} \
--session=${CASE} \
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
echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/DWIDenseParcellation.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- DWIDenseSeedTractography - Executes the Diffusion Seed Tractography Script (DWIDenseSeedTractography.sh) via the Qu|Nex connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

DWIDenseSeedTractography() {
# -- Command to run
QuNexCallToRun="DWIDenseSeedTractography.sh \
--sessionsfolder="${SessionsFolder}" \
--sessions="${CASE}" \
--matrixversion="${MatrixVersion}" \
--seedfile="${SeedFile}" \
--waytotal="${WayTotal}" \
--outname="${OutName}" \
--overwrite="${Overwrite}""
# -- Connector execute function
connectorExec
}
show_usage_DWIDenseSeedTractography() {
echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/DWIDenseSeedTractography.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- computeBOLDfc - Executes Global Brain Connectivity (GBC) or seed-based functional connectivity (ComputeFunctionalConnectivity.sh) via the Qu|Nex connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

computeBOLDfc() {

# -- Check type of run
OutPath="$OutPathFC"
if [[ ${RunType} == "individual" ]]; then
    OutPath="${SessionsFolder}/${CASE}/${InputPath}"
    # -- Make sure individual runs default to the original input path location (/images/functional)
    if [[ ${InputPath} == "" ]]; then
        InputPath="${SessionsFolder}/${CASE}/images/functional"
    fi
    # -- Make sure individual runs default to the original input path location (/images/functional)
    if [[ ${OutPath} == "" ]]; then
        OutPath="${SessionsFolder}/${CASE}/${InputPath}"
    fi
fi

# -- Check type of connectivity calculation is seed
if [[ ${Calculation} == "seed" ]]; then
    echo ""
    # -- Specify command variable
    QuNexCallToRun="${TOOLS}/${QUNEXREPO}/connector/functions/ComputeFunctionalConnectivity.sh \
    --sessionsfolder=${SessionsFolder} \
    --calculation=${Calculation} \
    --runtype=${RunType} \
    --sessions=${CASE} \
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
if [[ ${Calculation} == "gbc" ]]; then
    echo ""
    # -- Specify command variable
    QuNexCallToRun="${TOOLS}/${QUNEXREPO}/connector/functions/ComputeFunctionalConnectivity.sh \
    --sessionsfolder=${SessionsFolder} \
    --calculation=${Calculation} \
    --runtype=${RunType} \
    --sessions=${CASE} \
    --inputfiles=${InputFiles} \
    --inputpath=${InputPath} \
    --extractdata=${ExtractData} \
    --outname=${OutName} \
    --flist=${FileList} \
    --overwrite=${Overwrite} \
    --ignore=${IgnoreFrames} \
    --target=${TargetROI} \
    --gbc-command=${GBCCommand} \
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
if [[ ${Calculation} == "dense" ]]; then
    echo ""
    # -- Specify command variable
    QuNexCallToRun="${TOOLS}/${QUNEXREPO}/connector/functions/ComputeFunctionalConnectivity.sh \
    --sessionsfolder=${SessionsFolder} \
    --calculation=${Calculation} \
    --runtype=${RunType} \
    --sessions=${CASE} \
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
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/ComputeFunctionalConnectivity.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- structuralParcellation - Executes the Structural Parcellation Script (StructuralParcellation.sh) via the Qu|Nex connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

structuralParcellation() {
# -- Parse general parameters
QUEUE="$QUEUE"
SessionsFolder="$SessionsFolder"
CASE=${CASE}
InputDataType="$InputDataType"
OutName="$OutName"
ParcellationFile="$ParcellationFile"
ExtractData="$ExtractData"
Overwrite="$Overwrite"
# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/connector/functions/StructuralParcellation.sh \
--sessionsfolder=${SessionsFolder} \
--session=${CASE} \
--inputdatatype=${InputDataType} \
--parcellationfile=${ParcellationFile} \
--overwrite=${Overwrite} \
--outname=${OutName} \
--extractdata=${ExtractData}"
# -- Connector execute function
connectorExec
}
show_usage_structuralParcellation() {
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/StructuralParcellation.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- BOLDParcellation - Executes the BOLD Parcellation Script (BOLDParcellation.sh) via the Qu|Nex connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

BOLDParcellation() {
# -- Parse general parameters
if [[ -z ${SingleInputFile} ]]; then
    BOLDOutput="${SessionsFolder}/${CASE}/${OutPath}"
else
    BOLDOutput="${OutPath}"
fi
# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/connector/functions/BOLDParcellation.sh \
--sessionsfolder='${SessionsFolder}' \
--sessions='${CASE}' \
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
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/BOLDParcellation.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- ROIExtract - Executes the ROI Extraction Script (ROIExtract.sh) via the Qu|Nex connector wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

ROIExtract() {
# -- Parse general parameters
ROIFileSessionSpecific="$ROIFileSessionSpecific"
SingleInputFile="$SingleInputFile"
if [[ -z ${SingleInputFile} ]]; then
    OutPath="${SessionsFolder}/${CASE}/${OutPath}"
else
    OutPath="${OutPath}"
    InputFile="${SingleInputFile}"
fi
if [[ ${ROIFileSessionSpecific} == "no" ]]; then
    ROIFile="${ROIFile}"
else
    ROIFile="${SessionsFolder}/${CASE}/${ROIFile}"
fi
# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/connector/functions/ROIExtract.sh \
--roifile='${ROIInputFile}' \
--inputfile='${InputFile}' \
--outdir='${OutPath}' \
--outname='${OutName}'"
# -- Connector execute function
connectorExec
}
show_usage_ROIExtract() {
echo ""
echo "DESCRIPTION for ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/ROIExtract.sh
}

# ------------------------------------------------------------------------------------------------------
#  -- FSLDtifit - Executes the dtifit script from FSL (needed for probabilistic tractography)
# ------------------------------------------------------------------------------------------------------

FSLDtifit() {
# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/connector/functions/DWIFSLDtifit.sh \
--sessionsfolder='${SessionsFolder}' \
--session='${CASE}' \
--overwrite='${Overwrite}' "
# -- Connector execute function
connectorExec
}
show_usage_FSLDtifit() {
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/DWIFSLDtifit.sh
}

# ------------------------------------------------------------------------------------------------------
#  -- FSLBedpostxGPU - Executes the bedpostx_gpu code from FSL (needed for probabilistic tractography)
# ------------------------------------------------------------------------------------------------------

FSLBedpostxGPU() {
# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/connector/functions/DWIFSLBedpostxGPU.sh \
--sessionsfolder='${SessionsFolder}' \
--session='${CASE}' \
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
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/DWIFSLBedpostxGPU.sh
}

# ------------------------------------------------------------------------------------------------------------------------------
#  -- autoPtx - Executes the autoptx script from FSL (needed for probabilistic estimation of large-scale fiber bundles / tracts)
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
Com1="${AutoPtxFolder}/autoptx ${SessionsFolder} ${CASE} ${BedPostXFolder}"
Com2="${AutoPtxFolder}/Prepare_for_Display.sh ${StudyFolder}/${CASE}/MNINonLinear/Results/autoptx 0.005 1"
Com3="${AutoPtxFolder}/Prepare_for_Display.sh ${StudyFolder}/${CASE}/MNINonLinear/Results/autoptx 0.005 0"
# -- Command to run
QuNexCallToRun="${Com1}; ${Com2}; ${Com3}"
# -- Connector execute function
connectorExec
}

show_usage_autoPtx() {
echo ""
echo "qunex ${UsageInput} "
echo ""
echo "This command runs the autoptx script in ${AutoPtxFolder}."
echo ""
echo "For full details on AutoPtx functionality see: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/AutoPtx"
echo ""
}

# -------------------------------------------------------------------------------------------------------------------
#  -- pretractographyDense - Executes the HCP Pretractography code [ Stam's implementation for all grayordinates ]
# ------------------------------------------------------------------------------------------------------------------

pretractographyDense() {
# -- Parse general parameters
LogFolder="${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Results/log_pretractographydense"
RunFolder="${SessionsFolder}/${CASE}/hcp/"
# -- Command to run
QuNexCallToRun="${HCPPIPEDIR_dMRITracFull}/PreTractography/PreTractography.sh ${RunFolder} ${CASE} 0 "
# -- Connector execute function
connectorExec
}
show_usage_pretractographyDense() {
echo ""; echo "qunex ${UsageInput}"
${HCPPIPEDIR_dMRITracFull}/PreTractography/PreTractography.sh
}

# --------------------------------------------------------------------------------------------------------------------------------------------------
#  -- ProbtrackxGPUDense - Executes the HCP Matrix1 and / or 3 code and generates WB dense connectomes (Stam's implementation for all grayordinates)
# --------------------------------------------------------------------------------------------------------------------------------------------------

ProbtrackxGPUDense() {
# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/connector/functions/ProbtrackxGPUDense.sh \
--sessionsfolder='${SessionsFolder}' \
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
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/ProbtrackxGPUDense.sh
}

# ------------------------------------------------------------------------------------------------------------------------------
#  -- Sync data from AWS buckets - customized for HCP
# -------------------------------------------------------------------------------------------------------------------------------
AWSHCPSync() {
mkdir ${SessionsFolder}/aws.logs &> /dev/null
cd $SessionsFolder}/aws.logs
if [ ${RunMethod} == "2" ]; then
    reho "AWS sync dry run..."
    if [ -d ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear ]; then
        mkdir ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality} &> /dev/null
        AWSSyncTimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        time aws s3 sync --dryrun s3:/${Awsuri}/${CASE}/${Modality} ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality}/ >> AWSHCPSync_${CASE}_${Modality}_${AWSSyncTimeStamp}.log
    else
        mkdir -p ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality} &> /dev/null
        AWSSyncTimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        time aws s3 sync --dryrun s3:/${Awsuri}/${CASE}/${Modality} ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality}/ >> AWSHCPSync_${CASE}_${Modality}_${AWSSyncTimeStamp}.log
    fi
fi
if [ ${RunMethod} == "1" ]; then
    geho "AWS sync running..."
    if [ -d ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear ]; then
        mkdir ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality} &> /dev/null
        AWSSyncTimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        time aws s3 sync s3:/${Awsuri}/${CASE}/${Modality} ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality}/ >> AWSHCPSync_${CASE}_${Modality}_${AWSSyncTimeStamp}.log
    else
        mkdir -p ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality} &> /dev/null
        AWSSyncTimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        time aws s3 sync s3:/${Awsuri}/${CASE}/${Modality} ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality}/ >> AWSHCPSync_${CASE}_${Modality}_${AWSSyncTimeStamp}.log
    fi
fi
}
show_usage_AWSHCPSync() {
echo ""
echo "qunex AWSHCPSync"
echo ""
echo "This command enables syncing of HCP data from the Amazon AWS S3 repository."
echo "It assumes you have enabled your AWS credentials via the HCP website."
echo "These credentials are expected in your home folder under ./aws/credentials."
echo ""
echo "INPUTS"
echo "======"
echo ""
echo "--sessionsfolder  Path to study folder that contains sessions"
echo "--sessions        List of sessions to run"
echo "--modality        Which modality or folder do you want to sync [e.g. MEG, MNINonLinear, T1w]"
echo "--awsuri          Enter the AWS URI [e.g. /hcp-openaccess/HCP_900]"
echo ""
echo "EXAMPLE USE"
echo "==========="
echo ""
echo "Example with flagged parameters for submission to the scheduler::"
echo ""
echo "  qunex AWSHCPSync"
echo "        --sessionsfolder='<path_to_study_sessions_folder>' \ "
echo "        --sessions='<comma_separated_list_of_cases>' \ "
echo "        --command='' \ "
echo "        --modality='T1w' \ "
echo "        --awsuri='/hcp-openaccess/HCP_900'"
echo ""
}

# ------------------------------------------------------------------------------------------------------------------------------
# -- runQC - Performs various QC operations across modalities
# -------------------------------------------------------------------------------------------------------------------------------

runQC() {
# -- Check general output folders for QC
if [ ! -d ${SessionsFolder}/QC ]; then
    mkdir -p ${SessionsFolder}/QC &> /dev/null
fi
# -- Check T1w output folders for QC
if [ ! -d ${OutPath} ]; then
    mkdir -p ${OutPath} &> /dev/null
fi

# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/connector/functions/RunQC.sh \
--sessionsfolder='${SessionsFolder}' \
--sessions='${CASE}' \
--outpath='${OutPath}' \
--overwrite='${Overwrite}' \
--scenetemplatefolder='${scenetemplatefolder}' \
--modality='${Modality}' \
--datapath='${GeneralSceneDataPath}' \
--datafile='${GeneralSceneDataFile}' \
--customqc=${runQC_Custom} \
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
--hcp_suffix='${HCPSuffix}' \
--batchfile='${SessionBatchFile}' "
# -- Connector execute function
connectorExec
}
# -- Check for deprecated name and redundant camel case
show_usage_runQC() {
UsageInput="runQC"
echo ""
reho "==> NOTE: QCPreproc is deprecated. New function name --> ${UsageInput}"
echo ""
echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/RunQC.sh
}
show_usage_runQC() {
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/RunQC.sh
}
show_usage_runQC() {
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/connector/functions/RunQC.sh
}

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=
# =-=-=-=-=-==-=-=-= Establish general Qu|Nex functions and variables =-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=

# -- Setup this script such that if any command exits with a non-zero value, the
#    script itself exits and does not attempt any further processing.
# set -e

# ------------------------------------------------------------------------------
#  Load relevant libraries for logging and parsing options
# ------------------------------------------------------------------------------
if [[ ! -z $HCPPIPEDIR ]]; then
    source $HCPPIPEDIR/global/scripts/log.shlib  # -- Logging related functions
    source $HCPPIPEDIR/global/scripts/opts.shlib # -- Command line option functions
fi

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
    if [[ ${fn} = "--help" ]]; then
        return 0
    fi
done
}

# -- Set version variable
QuNexVer=`cat ${TOOLS}/${QUNEXREPO}/VERSION.md`

# -- Checks for version
showVersion() {
    QuNexVer=`cat ${TOOLS}/${QUNEXREPO}/VERSION.md`
    echo ""
    geho "Quantitative Neuroimaging Environment & Toolbox (Qu|Nex) Version: v${QuNexVer}"
    echo ""
}

# ------------------------------------------------------------------------------
#  Parse Command Line Options
# ------------------------------------------------------------------------------

# -- Check if version was requested
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
if [[ -z ${1} ]]; then
    showVersion
    show_usage
    exit 0
fi
if [[ ${1} == "help" ]]; then
    showVersion
    show_usage
    exit 0
fi

if [[ ${1} == "--envsetup" ]] || [[ ${1} == "-envsetup" ]] || [[ ${1} == "envsetup" ]]; then
    showVersion
    echo ""
    echo "Printing help call for $TOOLS/$QUNEXREPO/library/environment/qunex_environment.sh"
    echo ""
    bash ${TOOLS}/$QUNEXREPO/library/environment/qunex_environment.sh --help
    exit 0
fi

# ------------------------------------------------------------------------------
#  gmri loop outside local functions to bypass checking
# ------------------------------------------------------------------------------

# -- Get list of all supported gmri functions
gmrifunctions=`gmri -available`
# -- Check if command-line input matches any of the gmri functions
if [[ -z "${gmrifunctions##*$1*}" ]]; then
    # -- If yes then set the gmri function variable
    GmriCommandToRun="$1"
    # -- Check for input with question mark
    if [[ "$GmriCommandToRun" =~ .*"?".* ]] && [[ -z ${2} ]]; then
        # -- Set UsageInput variable to pass and remove question mark
        UsageInput=`echo ${GmriCommandToRun} | cut -c 2-`
        # -- If no other input is provided print help
        echo ""
        show_usage_gmri
        exit 0
    fi
    # -- Check for input with flag mark
    if [[ "$GmriCommandToRun" =~ .*"-".* ]] && [[ -z ${2} ]]; then
        # -- Set UsageInput variable to pass and remove question mark
        UsageInput=`echo ${GmriCommandToRun} | cut -c 2-`
        # -- If no other input is provided print help
        echo ""
        show_usage_gmri
        exit 0
    fi
    # -- Check for input is command name with no other arguments
    if [[ "$GmriCommandToRun" != *"-"* ]] && [[ -z ${2} ]]; then
        UsageInput="$GmriCommandToRun"
        # -- If no other input is provided print help
        echo ""
        show_usage_gmri
        exit 0
    else
        # -- Otherwise pass the command with all inputs from the command line
        
        # -- Clear white spaces for input into NIUtilities
        unset gmriinput
        whitespace="[[:space:]]"
        for inputarg in "$@"; do
            if [[ $inputarg =~ ${whitespace} ]]; then
                inputarg=`echo "${inputarg}" | sed "s/${whitespace}/,/g"`
            fi
            if [[ ${inputarg} =~ '=' ]] && [[ -z `echo ${inputarg} | grep '-'` ]]; then
                inputarg="--${inputarg}"
            fi
            gmriinput="${gmriinput} ${inputarg}"
            gmriinputecho="${gmriinputecho} ${inputarg}"
        done
        
        # # -- Report NIUtilities for debugging
        #  echo ""
        #  cyaneho "-------- Running NIUtilities command: ----------"
        #  echo ""
        #  cyaneho "  qunex ${gmriinputecho}"
        #  echo ""
        #  cyaneho "-------------------------------------------------"
        #  echo ""
        
        # -- Execute NIUtilities
        gmriFunction
        exit 0
    fi
fi

# ------------------------------------------------------------------------------
#  Check if specific command help requested
# ------------------------------------------------------------------------------

isQuNexFunction() {
MatlabFunctionsCheck=`find $TOOLS/$QUNEXREPO/nitools/ -name "*.m" | grep -v "archive/"`
if [[ -z "${QuNexCommands##*$1*}" ]]; then
    return 0
elif [[ ! -z `echo $MatlabFunctionsCheck | grep "$1"` ]]; then
    QuNexMatlabFunction="$1"
    echo ""
    echo "Requested $MatlabFunction function is part of the Qu|Nex nitools. Checking usage:"
    echo ""
    ${QUNEXMCOMMAND} "help ${QuNexMatlabFunction},quit()"
    exit 0
else
    echo ""
    reho "ERROR: $1 --> Requested function is not supported. Refer to general Qu|Nex usage."
    echo ""
    exit 0
fi
}

# -- Get all the functions from the usage calls

# -- Check for input with double flags
if [[ ${1} =~ .*--.* ]] && [[ -z ${2} ]]; then
    Usage="$1"
    # -- Check for gmri help inputs (--o --l --c)
    if [[  ${Usage}  == "--o" ]]; then
        show_processingoptions_gmri
        exit 0
    fi
    if [[ ${Usage} == "--a" ]] || [[ ${Usage} == "--all" ]] || [[ ${Usage} == "--allcommands" ]] || [[ ${Usage} == "-a" ]] || [[ ${Usage} == "-all" ]] || [[ ${Usage} == "-allcommands" ]]; then
    show_splash
        show_allcommands_connector
        show_allcommands_gmri
        show_usage_nitoolsHelp
        exit 0
    fi
    if [[ ${Usage} == "-c" ]] || [[ ${Usage} == "--c" ]]; then
        show_processingcommandlist_gmri
        exit 0
    fi
    if [[ ${Usage} == "-l" ]] || [[ ${Usage} == "--l" ]]; then
        show_processingcommandlist_gmri
        exit 0
    fi
    UsageInput=`echo ${Usage:2}`
    # -- Check if input part of function list
    isQuNexFunction ${UsageInput}
    showVersion
    show_usage_"${UsageInput}"
    exit 0
fi
# -- Check for input with single flags
if [[ ${1} =~ .*-.* ]] && [[ -z ${2} ]]; then
    Usage="$1"
    # -- Check for gmri help inputs (-o -l -c)
    if [[ ${Usage} == "-o" ]]; then
        show_processingoptions_gmri
        exit 0
    fi
    if [[ ${Usage} == "-a" ]] || [[ ${Usage} == "-all" ]] || [[ ${Usage} == "-allcommands" ]]; then
        show_splash
        show_allcommands_connector
        show_allcommands_gmri
        show_usage_nitoolsHelp
        exit 0
    fi
    if [[ ${Usage} == "-c" ]]; then
        show_processingcommandlist_gmri
        exit 0
    fi
    if [[ ${Usage} == "-l" ]]; then
        show_processingcommandlist_gmri
        exit 0
    fi    
    UsageInput=`echo ${Usage:1}`
    # -- Check if input part of function list
    isQuNexFunction ${UsageInput}
    showVersion
    show_usage_"${UsageInput}"
    exit 0
fi
# -- Check for input with question mark
HelpInputUsage="$1"
if [[ ${HelpInputUsage:0:1} == "?" ]] && [[ -z ${2} ]]; then
    Usage="$1"
    UsageInput=`echo ${Usage} | cut -c 2-`
    # -- Check if input part of function list
    isQuNexFunction ${UsageInput}
    showVersion
    show_usage_"${UsageInput}"
    exit 0
fi
# -- Check for input with no flags
if [[ -z ${2} ]]; then
    UsageInput="$1"
    # -- Check if input part of function list
    isQuNexFunction ${UsageInput}
    showVersion
    show_usage_"${UsageInput}"
    exit 0
fi

# ------------------------------------------------------------------------------
#  Check if running script interactively or using flag arguments
# ------------------------------------------------------------------------------

# -- Clear variables for new run
unset CommandToRun
unset sessions
unset StudyFolder
unset CASES
unset Overwrite
unset Scheduler
unset ClusterName
unset setflag
unset doubleflag
unset singleflag
unset SESSIONIDS
unset SESSIONS
unset SESSION_LABELS

# -- Check if first parameter is missing flags and parse it as CommandToRun
if [ -z `echo "$1" | grep '-'` ]; then
    CommandToRun="$1"
    # -- Check if single or double flags are set
    doubleflagparameter=`echo $2 | cut -c1-2`
    singleflagparameter=`echo $2 | cut -c1`
    if [[ ${doubleflagparameter} == "--" ]]; then
        setflag="$doubleflagparameter"
    else
        if [[ ${singleflagparameter} == "-" ]]; then
            setflag="$singleflagparameter"
        fi
    fi
else
    # -- Check if single or double flags are set
    doubleflag=`echo $1 | cut -c1-2`
    singleflag=`echo $1 | cut -c1`
    if [[ ${doubleflag} == "--" ]]; then
        setflag="$doubleflag"
    else
        if [[ ${singleflag} == "-" ]]; then
            setflag="$singleflag"
        fi
    fi
fi

if [[ ${CommandToRun} == "runTurnkey" ]]; then
    runTurnkeyArguments="$@"
    runTurnkeyArguments=`printf '%s\n' "${runTurnkeyArguments//runTurnkey/}"`
    #echo ""
    #geho "Turnkey Arguments: ${runTurnkeyArguments}"
    #echo ""
fi

# -- Next check if any additional flags are set
if [[ ${setflag} =~ .*-.* ]]; then
    echo ""
    # ------------------------------------------------------------------------------
    #  List of command line options across all functions
    # ------------------------------------------------------------------------------

    # -- First get function / command input (to harmonize input with gmri)
    if [[ -z ${CommandToRun} ]]; then
        FunctionInput=`opts_GetOpt "${setflag}function" "$@"` # function to execute
        CommandInput=`opts_GetOpt "${setflag}command" "$@"`   # command to execute
        # -- If input name uses 'command' instead of function set that to $CommandToRun
        if [[ -z ${FunctionInput} ]]; then
            CommandToRun="$CommandInput"
        else
            CommandToRun="$FunctionInput"
        fi
    fi
    # -- StudyFolder & SessionsFolder input flags
    StudyFolder=`opts_GetOpt "${setflag}studyfolder" $@`        # study folder to work on
    StudyFolderPath=`opts_GetOpt "${setflag}path" $@`           # local folder to work on
    SessionsFolder=`opts_GetOpt "${setflag}sessionsfolder" $@`  # sessions folder to work on
    SubjectFolder=`opts_GetOpt "${setflag}sessionfolder"  $@`   # sessions folder to work on
    STUDY_PATH=${StudyFolderPath}                               # local path for study folder
    
    # -- sessionsfolder used to be subjectsfolder
    if [[ -z ${SessionsFolder} ]]; then
        SessionsFolder==`opts_GetOpt "${setflag}subjectsfolder" $@`
    fi

    if [[ ! -z ${STUDY_PATH} ]]; then StudyFolder=${STUDY_PATH}; fi
    
    # -- Check StudyFolder and set
    if [[ -z ${StudyFolder} ]] && [[ ! -z ${StudyFolderPath} ]]; then
        StudyFolder="$StudyFolderPath"
    fi

    # -- If sessions folder is missing but study folder is defined assume standard Qu|Nex folder structure
    if [[ -z ${SessionsFolder} ]]; then
        if [[ ! -z ${SubjectFolder} ]]; then
            SessionsFolder="${SubjectFolder}"
        fi
        if [[ -z ${StudyFolder} ]]; then
            echo "" &> /dev/null
        else
            SessionsFolder="$StudyFolder/sessions"
        fi
    fi

    # -- If study folder is missing but sessions folder is defined assume standard Qu|Nex folder structure
    if [[ -z ${StudyFolder} ]]; then
        if [[ -z ${SessionsFolder} ]]; then
        echo "" &> /dev/null
        else
            cd ${SessionsFolder}/../ &> /dev/null
            StudyFolder=`pwd` &> /dev/null
        fi
    fi
    if [[ -z ${STUDY_PATH} ]]; then
         STUDY_PATH=${StudyFolder}
    fi
    # -- If logfolder flag set then set it and set master log
    if [[ -z ${LogFolder} ]]; then
        LogFolder="${StudyFolder}/processing/logs"
    fi
            
    # -- Set additional RunTurnkey flags
    STUDY_PATH=`opts_GetOpt "${setflag}path" $@`
    TURNKEY_TYPE=`opts_GetOpt "${setflag}turnkeytype" $@`
    TURNKEY_STEPS=`opts_GetOpt "${setflag}turnkeysteps" $@`
    WORKDIR=`opts_GetOpt "${setflag}workingdir" $@`
    PROJECT_NAME=`opts_GetOpt "${setflag}projectname" $@`
    CleanupSession=`opts_GetOpt "${setflag}cleanupsession" $@`
    CleanupProject=`opts_GetOpt "${setflag}cleanupproject" $@`
    RawDataInputPath=`opts_GetOpt "${setflag}rawdatainput" $@`
    QuNexSessionsFolder=`opts_GetOpt "${setflag}sessionsfolder" $@`
    OVERWRITE_SESSION=`opts_GetOpt "${setflag}overwritesession" $@`
    OVERWRITE_STEP=`opts_GetOpt "${setflag}overwritestep" $@`
    OVERWRITE_PROJECT=`opts_GetOpt "${setflag}overwriteproject" $@`
    OVERWRITE_PROJECT_FORCE=`opts_GetOpt "${setflag}overwriteprojectforce" $@`
    OVERWRITE_PROJECT_XNAT=`opts_GetOpt "${setflag}overwriteprojectxnat" $@`
    BATCH_PARAMETERS_FILENAME=`opts_GetOpt "${setflag}batchfile" $@`
    LOCAL_BATCH_FILE=`opts_GetOpt "${setflag}local_batchfile" $@`
    SessionBatchFile=`opts_GetOpt "${setflag}batchfile" $@`
    SCAN_MAPPING_FILENAME=`opts_GetOpt "${setflag}mappingfile" $@`
    XNAT_ACCSESSION_ID=`opts_GetOpt "${setflag}xnataccsessionid" $@`
    XNAT_SESSION_LABELS=`opts_GetOpt "${setflag}xnatsessionlabels" "$@" | sed 's/,/ /g;s/|/ /g'`; XNAT_SESSION_LABELS=`echo "${XNAT_SESSION_LABELS}" | sed 's/,/ /g;s/|/ /g'`
    XNAT_PROJECT_ID=`opts_GetOpt "${setflag}xnatprojectid" $@`
    XNAT_SUBJECT_ID=`opts_GetOpt "${setflag}xnatsubjectid" $@`
    XNAT_HOST_NAME=`opts_GetOpt "${setflag}xnathost" $@`
    XNAT_USER_NAME=`opts_GetOpt "${setflag}xnatuser" $@`
    XNAT_PASSWORD=`opts_GetOpt "${setflag}xnatpass" $@`
    XNAT_STUDY_INPUT_PATH=`opts_GetOpt "${setflag}xnatstudyinputpath" $@`

    # -- Backwards comapatibility, sessionsfolder used to be subjectsfolder
    if [[ -z ${QuNexSessionsFolder} ]]; then
        QuNexSessionsFolder==`opts_GetOpt "${setflag}subjectsfolder" $@`
        echo "WARNING: the subjectsfolder parameter is now known as sessionsfolder.";
    fi

    # -- General session and session flags
    CASES=`opts_GetOpt "${setflag}sessions" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
    SESSIONIDS=`opts_GetOpt "${setflag}sessionids" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSIONIDS=`echo "$SESSIONIDS" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes

    # -- Backwards comapatibility, session* used to be subject* 
    if [[ -z ${CASES} ]]; then
        CASES=`opts_GetOpt "${setflag}subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
        echo "WARNING: the subjects parameter is now known as sessions.";
    fi
    if [[ -z ${SESSIONIDS} ]]; then
        SESSIONIDS=`opts_GetOpt "${setflag}subjid" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
        echo "WARNING: the subjid parameter is now known as sessionids.";
    fi

    SESSION_LABELS=`opts_GetOpt "--sessionlabel" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
    if [[ -z ${SESSION_LABELS} ]]; then
        SESSION_LABELS=`opts_GetOpt "--session" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
    fi
    if [[ -z ${SESSION_LABELS} ]]; then
        SESSION_LABELS=`opts_GetOpt "--sessionlabels" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
    fi
    if [[ -z ${SESSION_LABELS} ]]; then
       SESSION_LABELS=`opts_GetOpt "--sessions" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
    fi
    SESSIONS="${SESSION_LABELS}"
    if [[ -z ${CASES} ]]; then
        if [[ ! -z ${SESSIONS} ]]; then
            CASES="$SESSIONS"
        fi
    fi

    if [[ -z ${SESSION_LABELS} ]]; then
        SESSION_LABELS=`opts_GetOpt "--session" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
    fi
    if [[ -z ${SESSION_LABELS} ]]; then
        SESSION_LABELS=`opts_GetOpt "--sessionlabels" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
    fi
    if [[ -z ${SESSION_LABELS} ]]; then
       SESSION_LABELS=`opts_GetOpt "--sessions" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
    fi
    SESSIONS="${SESSION_LABELS}"
    if [[ -z ${CASES} ]]; then
        if [[ ! -z ${SESSIONS} ]]; then
            CASES="$SESSIONS"
        fi
    fi

    # -- General operational flags
    Overwrite=`opts_GetOpt "${setflag}overwrite" $@`  # Clean prior run and starr fresh [yes/no]
    PRINTCOM=`opts_GetOpt "${setflag}printcom" $@`    # Option for printing the entire command
    Scheduler=`opts_GetOpt "${setflag}scheduler" $@`  # Specify the type of scheduler to use
    LogFolder=`opts_GetOpt "${setflag}logfolder" $@`  # Log location
    LogSave=`opts_GetOpt "${setflag}log" $@`          # Log save
    # -- If log flag set then set it
    if [[ -z ${LogSave} ]] || [[ ${LogSave} == "yes" ]]; then
        LogSave="keep"
    fi
    if [[ ${LogSave} == "no" ]]; then
        LogSave="remove"
    fi
    # -- If scheduler flag set then set RunMethod variable
    if [[ ! -z ${Scheduler} ]]; then
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
    ParElements=`opts_GetOpt "${setflag}parelements" $@`
    # -- Path options for FreeSurfer or Qu|Nex
    FreeSurferHome=`opts_GetOpt "${setflag}hcp_freesurfer_home" $@`
    QuNexVersion=`opts_GetOpt "${setflag}version" $@`
    # -- createLists input flags
    ListGenerate=`opts_GetOpt "${setflag}listtocreate" $@`
    Append=`opts_GetOpt "${setflag}append" $@`
    ListName=`opts_GetOpt "${setflag}listname" $@`
    HeaderBatch=`opts_GetOpt "${setflag}headerbatch" $@`
    ListFunction=`opts_GetOpt "${setflag}listfunction" $@`
    ParcellationFile=`opts_GetOpt "${setflag}parcellationfile" $@`
    FileType=`opts_GetOpt "${setflag}filetype" $@`
    BoldSuffix=`opts_GetOpt "${setflag}boldsuffix" $@`
    SessionHCPFile=`opts_GetOpt "${setflag}sessionhcpfile" $@`
    ListPath=`opts_GetOpt "${setflag}listpath" $@`
    # -- dataSync input flags
    NetID=`opts_GetOpt "${setflag}netid" $@`
    HCPSessionsFolder=`opts_GetOpt "${setflag}clusterpath" $@`
    Direction=`opts_GetOpt "${setflag}dir" $@`
    ClusterName=`opts_GetOpt "${setflag}cluster" $@`
    # -- ROIExtract input flags
    ROIFile=`opts_GetOpt "${setflag}roifile" $@`
    ROIFileSessionSpecific=`opts_GetOpt "${setflag}sessionroifile" $@`
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
    # -- DWIDenseSeedTractography input flags
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
    # -- runQC input flags
    OutPath=`opts_GetOpt "${setflag}outpath" $@`
    scenetemplatefolder=`opts_GetOpt "${setflag}scenetemplatefolder" $@`
    UserSceneFile=`opts_GetOpt "${setflag}userscenefile" $@`
    UserScenePath=`opts_GetOpt "${setflag}userscenepath" $@`
    Modality=`opts_GetOpt "${setflag}modality" $@`
    runQC_Custom=`opts_GetOpt "${setflag}customqc" $@`
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
    if [[ -z ${BOLDS} ]]; then
        BOLDS=`opts_GetOpt "${setflag}boldruns" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
    fi
    if [[ -z ${BOLDS} ]]; then
        BOLDS=`opts_GetOpt "${setflag}bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
    fi
    BOLDRUNS="${BOLDS}"
    BOLDDATA="${BOLDS}"
    BOLDfc=`opts_GetOpt "${setflag}boldfc" $@`
    BOLDfcInput=`opts_GetOpt "${setflag}boldfcinput" $@`
    BOLDfcPath=`opts_GetOpt "${setflag}boldfcpath" $@`
    
    if [[ -z ${BOLDLIST} ]]; then BOLDLIST=`opts_GetOpt "${setflag}bolddata" "$@"`; fi
    if [[ -z ${BOLDLIST} ]]; then BOLDLIST=`opts_GetOpt "${setflag}bolds" "$@"`; fi
    if [[ -z ${BOLDLIST} ]]; then BOLDLIST=`opts_GetOpt "${setflag}boldruns" "$@"`; fi
    BOLDLIST=`echo "${BOLDLIST}" | sed 's/ /,/g;s/|/ /g'`
    BOLDSuffix=`opts_GetOpt "${setflag}boldsuffix" $@`
    BOLDPrefix=`opts_GetOpt "${setflag}boldprefix" $@`
    
    SkipFrames=`opts_GetOpt "${setflag}skipframes" $@`
    SNROnly=`opts_GetOpt "${setflag}snronly" $@`
    TimeStamp=`opts_GetOpt "${setflag}timestamp" $@`
    Suffix=`opts_GetOpt "${setflag}suffix" $@`
    SceneZip=`opts_GetOpt "${setflag}scenezip" $@`
    
    # -- Check if session input is a parameter file instead of list of cases
    if [[ ${CASES} == *.txt ]]; then
        SessionBatchFile="$CASES"
        echo ""
        echo "Using $SessionBatchFile for input."
        echo ""
        CASES=`more ${SessionBatchFile} | grep "id:"| cut -d " " -f 2`
    fi
    
fi

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-
# =-=-=-=-=-=-=-=-=-=-=-= Execute specific functions =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-

echo ""
geho "--- Running Qu|Nex v${QuNexVer}: ${CommandToRun} function"
echo ""

# ------------------------------------------------------------------------------
#  nitoolsHelp
# ------------------------------------------------------------------------------

if [[ ${CommandToRun} == "nitoolsHelp" ]] || [[ ${CommandToRun} == "qunexnitoolsHelp" ]]; then
    ${CommandToRun}
fi

# ------------------------------------------------------------------------------
#  runTurnkey loop
# ------------------------------------------------------------------------------

if [[ ${CommandToRun} == "runTurnkey" ]]; then

    # -- Check for cases
    if [[ -z ${CASES} ]]; then
        if [[ ! -z ${XNAT_SESSION_LABELS} ]]; then
            CASES="$XNAT_SESSION_LABELS"
        fi
    fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    
    # -- Check for WORKDIR and StudyFolder for an XNAT run
    if [[ -z ${WORKDIR} ]]; then 
        if [[ ! -z ${XNAT_PROJECT_ID} ]]; then
            WORKDIR="/output"; reho " -- Note: Working directory where study is located is missing. Setting defaults: ${WORKDIR}"; echo ''
        fi
    fi
    if [[ -z ${WORKDIR} ]]; then reho "Error: Working folder for $CommandToRun missing."; exit 1; fi
    
    if [[ -z ${StudyFolder} ]]; then 
        if [[ ! -z ${XNAT_PROJECT_ID} ]]; then
            StudyFolder="${WORKDIR}/${XNAT_PROJECT_ID}"
        fi
    fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing."; exit 1; fi

   # -- Check if cluster options are set
   Cluster="$RunMethod"
   if [[ ${Cluster} == "2" ]]; then
           if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
   fi
   # -- Clean up argument flags
   runTurnkeyArgumentsInput="${runTurnkeyArguments}"
   runTurnkeyArguments=`echo "${runTurnkeyArguments}" | sed 's|--sessions=.[^-]*||g'`
   runTurnkeyArguments=`echo "${runTurnkeyArguments}" | sed 's|--turnkeysteps=.[^-]*||g'`
   runTurnkeyArguments=`echo "${runTurnkeyArguments}" | sed 's|--sessionids=.[^-]*||g'`
   runTurnkeyArguments=`echo "${runTurnkeyArguments}" | sed 's|--bolds=.[^-]*||g'`
   runTurnkeyArguments=`echo "${runTurnkeyArguments}" | sed 's|--bolddata=.[^-]*||g'`
   runTurnkeyArguments=`echo "${runTurnkeyArguments}" | sed 's|--boldruns=.[^-]*||g'`
   echo ""
   echo "Running $CommandToRun processing with the following parameters:"
   echo ""
   echo "--------------------------------------------------------------"
   echo ""
   echo " Turnkey steps: ${TURNKEY_STEPS} "
   echo " Turnkey arguments: ${runTurnkeyArguments} "
   echo ""
   echo "--------------------------------------------------------------"
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun}; done

fi

# ------------------------------------------------------------------------------
#  organizeDicom loop
# ------------------------------------------------------------------------------

if [[ ${CommandToRun} == "organizeDicom" ]]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then
        if [[ -z ${Folder} ]]; then
            reho "Error: Study folder missing and optional parameter --folder not specified."
            exit 1
        fi
    fi
    if [[ -z ${SessionsFolder} ]]; then
        if [[ -z ${Folder} ]]; then
            reho "Error: Sesssions folder missing and options parameter --folder not specified"
            exit 1
        fi
    fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    if [[ -z ${Overwrite} ]]; then Overwrite="no"; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Optional parameters
    if [[ -z ${Folder} ]]; then
        Folder="$SessionsFolder"
    else
        if [[ -z ${StudyFolder} ]] && [[ -z ${SessionsFolder} ]]; then
            SessionsFolder="$Folder"
            StudyFolder="../$SessionsFolder"
        fi
    fi
    if [[ -z ${Clean} ]]; then Clean="yes"; echo ""; echo "--clean not specified explicitly. Setting --clean=$Clean."; echo ""; fi
    if [[ -z ${Unzip} ]]; then Unzip="yes"; echo ""; echo "--unzip not specified explicitly. Setting --unzip=$Unzip."; echo ""; fi
    if [[ -z ${Unzip} ]]; then Gzip="yes"; echo ""; echo "--gzip not specified explicitly. Setting --gzip=$Gzip."; echo ""; fi
    if [[ -z ${VerboseRun} ]]; then VerboseRun="True"; echo ""; echo "--verbose not specified explicitly. Proceeding --verbose=$Verbose"; echo ""; fi
    if [[ -z ${ParElements} ]]; then ParElements="4"; echo ""; echo "--parelements not specified explicitly. Proceeding --parelements=$ParElements"; echo ""; fi

    # -- Report parameters
    echo ""
    echo "Running $CommandToRun processing with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    if [[ -z ${Folder} ]]; then
        echo "   Optional --folder parameter not set. Using standard inputs."
        echo "   Study Folder: ${StudyFolder}"
        echo "   Sessions Folder: ${SessionsFolder}"
    else
        echo "Optional --folder parameter set explicitly. "
        echo "   Setting sessions folder and study accordingly."
        echo "   Study Folder: ${StudyFolder}"
        echo "   Sessions Folder: ${SessionsFolder}"
    fi
    echo "   Sessions: ${CASES}"
    echo "   Overwrite prior run: ${Overwrite}"
    echo ""
    # -- Report optional parameters
    echo "   Clean NIFTI files: ${Clean}"
    echo "   Unzip DICOM files: ${Unzip}"
    echo "   Gzip DICOM files: ${Gzip}"
    echo "   Report verbose run: ${VerboseRun}"
    echo "   Elements to run in parallel: ${ParElements}"
    echo "   Study log folder: ${LogFolder}"
    echo ""
    echo "--------------------------------------------------------------"
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  runQC loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "QCPreproc" ] || [ "$CommandToRun" == "runQC" ] || [ "$CommandToRun" == "RunQC" ]; then
    if [ "$CommandToRun" == "QCPreproc" ]; then
       echo ""
       reho "==> NOTE: QCPreproc is deprecated. New function name --> ${CommandToRun}"
       echo ""
    fi
    CommandToRun="runQC"
    
    # -- Check all the user-defined parameters:
    TimeStampRunQC=`date +%Y-%m-%d-%H-%M-%S`
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing."; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing."; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing."; exit 1; fi
    if [[ -z ${Modality} ]]; then reho "Error:  Modality to perform QC on missing."; exit 1; fi
    if [[ -z ${runQC_Custom} ]]; then runQC_Custom="no"; fi
    if [[ ${runQC_Custom} == "yes" ]]; then scenetemplatefolder="${StudyFolder}/processing/scenes/QC/${Modality}"; fi
    if [[ -z ${OmitDefaults} ]]; then OmitDefaults="no"; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
        if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    
    # -- Perform some careful scene checks
    if [[ -z ${UserSceneFile} ]]; then
        if [ ! -z "$UserScenePath" ]; then 
            reho "---> Provided --userscenepath but --userscenefile not specified."; echo "";
            reho "     Check your inputs and re-run."; echo "";
            scenetemplatefolder="${TOOLS}/${QUNEXREPO}/library/data/scenes/qc"
            reho "---> Reverting to Qu|Nex defaults: ${scenetemplatefolder}"; echo ""
        fi
        if [ -z "$scenetemplatefolder" ]; then
            scenetemplatefolder="${TOOLS}/${QUNEXREPO}/library/data/scenes/qc"
            reho "---> Template folder path value not explicitly specified."; echo ""
            reho "---> Using Qu|Nex defaults: ${scenetemplatefolder}"; echo ""
        fi
        if ls ${scenetemplatefolder}/*${Modality}*.scene 1> /dev/null 2>&1; then 
            geho "---> Scene files found in:"; geho "`ls ${scenetemplatefolder}/*${Modality}*.scene`"; echo ""
        else 
            reho "---> Specified folder contains no scenes: ${scenetemplatefolder}"; echo ""
            scenetemplatefolder="${TOOLS}/${QUNEXREPO}/library/data/scenes/qc"
            reho "---> Reverting to defaults: ${scenetemplatefolder} "; echo ""
        fi
    else
        if [[ -f ${UserSceneFile} ]]; then
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
    if [ -z "$OutPath" ]; then OutPath="${SessionsFolder}/QC/${Modality}"; echo "Output folder path value not explicitly specified. Using default: ${OutPath}"; fi
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
    if [[ ${Modality} = "BOLD" ]]; then
        # - Check if BOLDS parameter is empty:
        if [ -z "$BOLDS" ]; then
            echo ""
            reho "BOLD input list not specified. Relying on session_hcp.txt individual information files."
            BOLDS="session_hcp.txt"
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
    echo "Running $CommandToRun processing with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   QC Modality: ${Modality}"
    echo "   QC Output Path: ${OutPath}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Custom QC requested: ${runQC_Custom}"
    echo "   HCP folder suffix: ${HCPSuffix}"
    if [ "$runQC_Custom" == "yes" ]; then
        echo "   Custom QC modalities: ${Modality}"
    fi
    if [ "$Modality" == "BOLD" ] || [ "$Modality" == "bold" ]; then
        if [[ ! -z ${SessionBatchFile} ]]; then
            if [[ ! -f ${SessionBatchFile} ]]; then
                reho " ERROR: Requested BOLD modality with a batch file. Batch file not found."
                exit 1
            else
                echo "   Session batch file requested: ${SessionBatchFile}"
                BOLDSBATCH="${BOLDRUNS}"
            fi
        fi
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
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  eddyQC loop - eddyqc - uses EDDY QC by Matteo Bastiani, FMRIB
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "eddyQC" ]; then
    #unset EddyPath
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
    if [ -z "$Report" ]; then reho "Error: Report type missing"; exit 1; fi
    # -- Perform checks for individual run
    if [ "$Report" == "individual" ]; then
        if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
        if [ -z "$EddyBase" ]; then reho "Eddy base input name missing"; exit 1; fi
        if [ -z "$BvalsFile" ]; then reho "BVALS file missing"; exit 1; fi
        if [ -z "$EddyIdx" ]; then reho "Eddy index missing"; exit 1; fi
        if [ -z "$EddyParams" ]; then reho "Eddy parameters missing"; exit 1; fi
        if [ -z "$Mask" ]; then reho "Error: Mask missing"; exit 1; fi
        if [ -z "$BvecsFile" ]; then BvecsFile=""; fi
    fi
    # -- Perform checks for group run
    if [ "$Report" == "group" ]; then
        if [ -z "$List" ]; then reho "Error: List of sessions missing"; exit 1; fi
        if [ -z "$Update" ]; then Update="false"; fi
        if [ -z "$GroupVar" ]; then GroupVar=""; fi
    fi
    # -- Check if cluster options are set
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Loop through cases for an individual run call
    if [ ${Report} == "individual" ]; then
        for CASE in ${CASES}; do
            # -- Check in/out paths
            if [ -z ${EddyPath} ]; then
                reho "Eddy path not set. Assuming defaults."
                EddyPath="${SessionsFolder}/${CASE}/hcp/${CASE}/Diffusion/eddy"
            else
                EddyPath="${SessionsFolder}/${CASE}/hcp/${CASE}/$EddyPath"
                echo $EddyPath
            fi
            if [ -z ${OutputDir} ]; then
                reho "Output folder not set. Assuming defaults."
                OutputDir="${EddyPath}/${EddyBase}.qc"
            fi
            # -- Report individual parameters
            echo ""
            echo "Running $CommandToRun processing with the following parameters:"
            echo ""
            echo "--------------------------------------------------------------"
            echo "   StudyFolder: ${StudyFolder}"
            echo "   Sessions Folder: ${SessionsFolder}"
            echo "   Session: ${CASE}"
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
            ${CommandToRun} ${CASE}
        done
    fi
    # -- Check if group call specified
    if [ ${Report} == "group" ]; then
        # -- Report group parameters
        echo ""
        echo "Running $CommandToRun processing with the following parameters:"
        echo ""
        echo "--------------------------------------------------------------"
        echo "   Study Folder: ${StudyFolder}"
        echo "   Sessions Folder: ${SessionsFolder}"
        echo "   Study Log Folder: ${LogFolder}"
        echo "   Report Type: ${Report}"
        echo "   Eddy QC Input Path: ${EddyPath}"
        echo "   Eddy QC Output Path: ${OutputDir}"
        echo "   List: ${List}"
        echo "   Grouping Variable: ${GroupVar}"
        echo "   Update single sessions: ${Update}"
        echo "   Overwrite: ${EddyPath}/${Overwrite}"
        echo "--------------------------------------------------------------"
        # ---> Add function all here
    fi
fi

# ------------------------------------------------------------------------------
#  mapHCPFiles loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "mapHCPFiles" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun processing with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "Study Folder: ${StudyFolder}"
    echo "Sessions Folder: ${SessionsFolder}"
    echo "Sessions: ${CASES}"
    echo "Study Log Folder: ${LogFolder}"
    echo "--------------------------------------------------------------"
    echo ""
    for CASE in ${CASES}; do
        echo "--> Ensuring that and correct session_hcp.txt files is generated..."; echo ""
        if [ -f ${SessionsFolder}/${CASE}/session_hcp.txt ]; then
            echo "--> ${SessionsFolder}/${CASE}/session_hcp.txt found"
            echo ""
            ${CommandToRun} ${CASE}
        else
            echo "--> ${SessionsFolder}/${CASE}/session_hcp.txt is missing - please setup the session.txt files and re-run function."
        fi
    done
fi

# ------------------------------------------------------------------------------
#  dataSync loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "dataSync" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Specific sessions not provided"; fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun processing with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "--------------------------------------------------------------"
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  structuralParcellation loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "structuralParcellation" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    if [ -z "$InputDataType" ]; then reho "Error: Input data type value missing"; exit 1; fi
    if [[ -z ${OutName} ]]; then reho "Error: Output file name value missing"; exit 1; fi
    if [ -z "$ParcellationFile" ]; then reho "Error: File to use for parcellation missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Check optional parameters if not specified
    if [ -z "$ExtractData" ]; then ExtractData="no"; fi
    if [ -z "$Overwrite" ]; then Overwrite="no"; fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   ParcellationFile: ${ParcellationFile}"
    echo "   Parcellated Data Output Name: ${OutName}"
    echo "   Input Data Type: ${InputDataType}"
    echo "   Extract data in CSV format: ${ExtractData}"
    echo "   Overwrite prior run: ${Overwrite}"
    echo "--------------------------------------------------------------"
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  FSLDtifit loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "FSLDtifit" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
        if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun processing with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Scheduler Name and Options: ${Scheduler}"
    echo "   Overwrite prior run: ${Overwrite}"
    echo "--------------------------------------------------------------"
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  FSLBedpostxGPU loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "FSLBedpostxGPU" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study Folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    if [ -z "$Fibers" ]; then reho "Error: Fibers value missing"; exit 1; fi
    if [ -z "$Model" ]; then reho "Error: Model value missing"; exit 1; fi
    if [ -z "$Burnin" ]; then reho "Error: Burnin value missing"; exit 1; fi
    if [ -z "$Rician" ]; then reho "Note: Rician flag missing. Setting to default --> YES"; Rician="YES"; fi
    Cluster=${RunMethod}
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun processing with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
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
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  Diffusion legacy processing loop (hcpdLegacy)
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "hcpdLegacy" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [ -z "$Scanner" ]; then reho "Error: Scanner manufacturer missing"; exit 1; fi
    if [ -z "$UseFieldmap" ]; then reho "Error: UseFieldmap yes/no specification missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    if [ -z "$DiffDataSuffix" ]; then reho "Error: Diffusion Data Suffix Name missing"; exit 1; fi
    if [ ${UseFieldmap} == "yes" ]; then
        if [ -z "$TE" ]; then reho "Error: TE value for Fieldmap missing"; exit 1; fi
    elif [ ${UseFieldmap} == "no" ]; then
        reho "Note: Processing without FieldMap (TE option not needed)"
    fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
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
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  structuralParcellation loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "structuralParcellation" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    if [ -z "$InputDataType" ]; then reho "Error: Input data type value missing"; exit 1; fi
    if [[ -z ${OutName} ]]; then reho "Error: Output file name value missing"; exit 1; fi
    if [ -z "$ParcellationFile" ]; then reho "Error: File to use for parcellation missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Check optional parameters if not specified
    if [ -z "$ExtractData" ]; then ExtractData="no"; fi
    if [ -z "$Overwrite" ]; then Overwrite="no"; fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   ParcellationFile: ${ParcellationFile}"
    echo "   Parcellated Data Output Name: ${OutName}"
    echo "   Input Data Type: ${InputDataType}"
    echo "   Extract data in CSV format: ${ExtractData}"
    echo "   Overwrite prior run: ${Overwrite}"
    echo "--------------------------------------------------------------"
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  computeBOLDfc loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "computeBOLDfc" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${Calculation} ]]; then reho "Error: Type of calculation to run (gbc or seed) missing"; exit 1; fi
    if [[ -z ${RunType} ]] && [[ ${Calculation} != "dense" ]]; then reho "Error: Type of run (group or individual) missing"; exit 1; fi
    if [[ ${RunType} == "list" ]]; then
        if [ -z "$FileList" ]; then reho "Error: Group file list missing"; exit 1; fi
    fi
    if [[ ${RunType} == "individual" ]] || [[ ${RunType} == "group" ]]; then
        if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
        if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
        if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
        if [ -z "$InputFiles" ]; then reho "Error: Input file(s) value missing"; exit 1; fi
        if [[ -z ${OutName} ]]; then reho "Error: Output file name value missing"; exit 1; fi
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
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
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
    echo "Running $CommandToRun with the following parameters:"
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
        echo "   Sessions Folder: ${SessionsFolder}"
        echo "   Sessions: ${CASES}"
        echo "   Input Files: ${InputFiles}"
        echo "   Input Path for Data: ${SessionsFolder}/<session_id>/${InputPath}"
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
            ${CommandToRun} ${CASE}
        done
    fi
    if [[ ${RunType} == "group" ]]; then
        CASE=`echo "$CASES" | sed 's/ /,/g'`
        echo $CASE
        ${CommandToRun} ${CASE}
    fi
    if [[ ${RunType} == "list" ]]; then
        ${CommandToRun}
    fi
fi

# ------------------------------------------------------------------------------
#  BOLDParcellation loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "BOLDParcellation" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [ -z "$InputPath" ]; then reho "Error: Input path value missing"; exit 1; fi
    if [ -z "$InputDataType" ]; then reho "Error: Input data type value missing"; exit 1; fi
    if [ -z "$OutPath" ]; then reho "Error: Output path value missing"; exit 1; fi
    if [[ -z ${OutName} ]]; then reho "Error: Output file name value missing"; exit 1; fi
    if [ -z "$ParcellationFile" ]; then reho "Error: File to use for parcellation missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
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
    if [[ -z ${SingleInputFile} ]]; then SingleInputFile="";
        if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
        if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
        if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
        if [ -z "$InputFile" ]; then reho "Error: Input file value missing"; exit 1; fi
    fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
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
    if [[ -z ${SingleInputFile} ]]; then SingleInputFile="";
        # -- Loop through all the cases
        for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
    else
        # -- Execute on single case
        ${CommandToRun} ${CASE}
    fi
fi

# ------------------------------------------------------------------------------
#  DWIDenseParcellation loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "DWIDenseParcellation" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    if [ -z "$MatrixVersion" ]; then reho "Error: Matrix version value missing"; exit 1; fi
    if [ -z "$ParcellationFile" ]; then reho "Error: File to use for parcellation missing"; exit 1; fi
    if [[ -z ${OutName} ]]; then reho "Error: Name of output pconn file missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    if [ -z "$WayTotal" ]; then WayTotal="no"; reho "--waytotal normalized data not specified. Assuming default [no]"; fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Matrix version used for input: ${MatrixVersion}"
    echo "   File to use for parcellation: ${ParcellationFile}"
    echo "   Dense DWI Parcellated Connectome Output Name: ${OutName}"
    echo "   Waytotal normalization: ${WayTotal}"
    echo "   Overwrite prior run: ${Overwrite}"
    echo "--------------------------------------------------------------"
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  ROIExtract loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "ROIExtract" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [ -z "$OutPath" ]; then reho "Error: Output path value missing"; exit 1; fi
    if [[ -z ${OutName} ]]; then reho "Error: Output file name value missing"; exit 1; fi
    if [ -z "$ROIFile" ]; then reho "Error: File to use for ROI extraction missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Check optional parameters if not specified
    if [ -z "$ROIFileSessionSpecific" ]; then ROIFileSessionSpecific="no"; fi
    if [ -z "$Overwrite" ]; then Overwrite="no"; fi
    if [[ -z ${SingleInputFile} ]]; then SingleInputFile="";
        if [ -z "$InputFile" ]; then reho "Error: Input file path value missing"; exit 1; fi
        if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
        if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
        if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo ""
    echo "   --------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Input File: ${InputFile}"
    echo "   Output File Name: ${OutName}"
    echo "   Single Input File: ${SingleInputFile}"
    echo "   ROI File: ${ROIFile}"
    echo "   Session specific ROI file set: ${ROIFileSessionSpecific}"
    echo "   Overwrite prior run: ${Overwrite}"
    echo "--------------------------------------------------------------"
    echo ""
    if [[ -z ${SingleInputFile} ]]; then SingleInputFile="";
        # -- Loop through all the cases
        for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
    else
        # -- Execute on single input file
        ${CommandToRun}
    fi
fi

# ------------------------------------------------------------------------------
#  DWIDenseSeedTractography loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "DWIDenseSeedTractography" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    if [ -z "$MatrixVersion" ]; then reho "Error: Matrix version value missing"; exit 1; fi
    if [ -z "$SeedFile" ]; then reho "Error: File to use for seed reduction missing"; exit 1; fi    
    if [[ -z ${OutName} ]]; then reho "Error: Name of output pconn file missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    if [ -z "$WayTotal" ]; then WayTotal="no"; reho "--waytotal normalized data not specified. Assuming default [no]"; fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Matrix version used for input: ${MatrixVersion}"
    echo "   Dense dconn seed reduction: ${SeedFile}"
    echo "   Dense DWI Parcellated Connectome Output Name: ${OutName}"
    echo "   Waytotal normalization: ${WayTotal}"
    echo "   Overwrite prior run: ${Overwrite}"
    echo "--------------------------------------------------------------"
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  autoPtx loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "autoPtx" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
        if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    if [[ -z ${BedPostXFolder} ]]; then BedPostXFolder=${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX; fi
    
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   BedpostX Folder: ${BedPostXFolder} "
    echo "--------------------------------------------------------------"
    echo ""
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  pretractographyDense loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "pretractographyDense" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
        if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "--------------------------------------------------------------"
    echo ""
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  ProbtrackxGPUDense loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "ProbtrackxGPUDense" ]; then
    # Check all the user-defined parameters: 1.QUEUE, 2. Scheduler, 3. Matrix1, 4. Matrix2
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    if [ -z "$MatrixOne" ] && [ -z "$MatrixThree" ]; then reho "Error: Matrix option missing. You need to specify at least one. [e.g. --omatrix1='yes' and/or --omatrix2='yes']"; exit 1; fi
    if [ "$MatrixOne" == "yes" ]; then
        if [ -z "$NsamplesMatrixOne" ]; then NsamplesMatrixOne=10000; fi
    fi
    if [ "$MatrixThree" == "yes" ]; then
        if [ -z "$NsamplesMatrixThree" ]; then NsamplesMatrixThree=3000; fi
    fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
        if [[ -z ${Scheduler} ]]; then reho "Error: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Optional parameters
    if [ -z ${ScriptsFolder} ]; then ScriptsFolder="${HCPPIPEDIR_dMRITracFull}/Tractography_gpu_scripts"; fi
    if [ -z ${OutFolder} ]; then OutFolder="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography"; fi
    if [ -z ${InFolder} ]; then InFolder="${SessionsFolder}/${CASE}/hcp"; fi
    minimumfilesize="100000000"

    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
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
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  AWSHCPSync - AWS S3 Sync command wrapper
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "AWSHCPSync" ]; then
    # Check all the user-defined parameters: 1. Modality, 2. Awsuri, 3. RunMethod
    if [[ -z ${CommandToRun} ]]; then reho "Error: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "Error: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "Error: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "Error: List of sessions missing"; exit 1; fi
    if [[ -z ${Modality} ]]; then reho "Error: Modality option [e.g. MEG, MNINonLinear, T1w] missing"; exit 1; fi
    if [ -z "$Awsuri" ]; then reho "Error: AWS URI option [e.g. /hcp-openaccess/HCP_900] missing"; exit 1; fi
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo ""
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Run Method: ${RunMethod}"
    echo "   Modality: ${Modality}"
    echo "   AWS URI Path: ${Awsuri}"
    echo "--------------------------------------------------------------"
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

