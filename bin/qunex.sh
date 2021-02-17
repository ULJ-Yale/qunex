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
# qunex.sh is a front-end bash integration script for the QuNex Suite
#
# ## LICENSE
#
# * The qunex.sh = the "Software"
# * This Software conforms to the license outlined in the QuNex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
#
#~ND~END~

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= CODE START =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=

QuNexCommands="matlab_help gmri_function data_sync organize_dicom map_hcp_files dwi_legacy dwi_eddy_qc dwi_parcellate dwi_seed_tractography_dense dwi_fsl_dtifit dwi_fsl_bedpostx_gpu dwi_pre_tractography dwi_probtrackx_dense_gpu auto_ptx compute_bold_fc bold_compute_fc anat_parcellate bold_parcellation bold_parcellate extract_roi aws_hcp_sync run_qc run_turnkey show_version environment"

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
 geho "       ██ ██\██ |██ |  ██ |      ║      ██ |\███ |██   ____|██  ██\  "
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
 geho "a part of the QuNex Suite source code package: "
 geho "https://bitbucket.org/hidradev/qunextools/src/master/LICENSE.md"
 geho ""
}

# ------------------------------------------------------------------------------
#  -- General help usage
# ------------------------------------------------------------------------------

show_usage() {

cat << EOF

 General QuNex Usage Syntax
=============================
 
 qunex <command-name> \
   --parameterA=<required-parameter-args> \
   [--parameterB=<optional-parameter-args>]

  =>  --   Dashes or “flags” denote input parameters.
  =>  []   Square brackets denote optional parameters. 
        Note: Arguments is shown inside [] denote default behavior of optional parameters. 
  =>  <>   Angle brackets denote user-specified arguments for a given parameter.
  => Command names, parameters and arguments are shown in small or “camel” case.


 Specific Command Help and Usage
=================================
  
 qunex <command_name> 


 Display Info on QuNex Modules
================================

 qunex --modules


 Display Listing of All QuNex Commands across Modules
=======================================================

  qunex --allcommands


EOF
 
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
#  -- Help calls for QuNex Functions
# ------------------------------------------------------------------------------------------------------

gmri_function() {
        echo ""
        eval gmri ${gmriinput}
        echo ""
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
        echo "Listing of all QuNex supported NIUtilitties commands"
        echo "===================================================="
        gmri -available | sed 1,1d
}
show_usage_matlab_help() {
        echo ""
        echo ""
        echo "Listing of all QuNex supported MATLAB commands"
        echo "=============================================="
        echo ""
        MatlabFunctionsGeneral=`ls $TOOLS/$QUNEXREPO/matlab/qx_utilities/*/*.m | grep "/general/"`
        MatlabFunctionsFC=`ls $TOOLS/$QUNEXREPO/matlab/qx_mri/*/*.m | grep "/fc/"`
        MatlabFunctionsMRIGeneral=`ls $TOOLS/$QUNEXREPO/matlab/qx_mri/*/*.m | grep "/general/"`
        MatlabFunctionsNIMG=`ls $TOOLS/$QUNEXREPO/matlab/qx_mri/img/\@nimage/*.m`
        MatlabFunctionsStats=`ls $TOOLS/$QUNEXREPO/matlab/qx_mri/*/*.m | grep "/stats/"`
        echo "QuNex MATLAB general tools"; echo ""
        for MatlabFunction in $MatlabFunctionsGeneral; do
            MatlabFunction=`basename $MatlabFunction`
            echo "  $MatlabFunction";
        done
        echo ""
        echo "QuNex MATLAB MRI functional connectivity tools"; echo ""
        for MatlabFunction in $MatlabFunctionsFC; do
            MatlabFunction=`basename $MatlabFunction`
            echo "  $MatlabFunction";
        done
        echo ""
        echo "QuNex MATLAB MRI tools"; echo ""
        for MatlabFunction in $MatlabFunctionsFC; do
            MatlabFunction=`basename $MatlabFunction`
            echo "  $MatlabFunction";
        done
        echo ""
        echo "QuNex MATLAB MRI analyses tools"; echo ""
        for MatlabFunction in $MatlabFunctionsNIMG; do
            MatlabFunction=`basename $MatlabFunction`
            echo "  $MatlabFunction";
        done
        echo ""
        echo "QuNex MATLAB MRI statistical tools"; echo ""
        for MatlabFunction in $MatlabFunctionsStats; do
            MatlabFunction=`basename $MatlabFunction`
            echo "  $MatlabFunction";
        done
        echo ""
}

show_allcommands_bash() {
 
cat << EOF

=============================================
 Listing of all QuNex supported bash commands
=============================================
 
  QuNex bash commands are located in:
    $TOOLS/$QUNEXREPO/bash/qx_utilities
 
  QuNex Suite workflows are integrated via QuNex bash functions.
  The QuNex bash functions also contain 'stand alone' processing
  or analyses tools. These can be called either directly or via
  the qunex wrapper
 
 QuNex Turnkey function
=======================
 
  run_turnkey                turnkey execution of QuNex workflow compatible with XNAT Docker engine

 QC functions
=============
 
  run_qc                     run visual qc for a given modality: raw nifti,t1w,tw2,myelin,bold,dwi
 
 DWI processing, QC, analyses & probabilistic tractography functions
=====================================================================
 
  dwi_legacy                  diffusion image processing for data with or without standard fieldmaps
  dwi_eddy_qc                 run quality control on diffusion datasets following eddy outputs
  dwi_fsl_dtifit              run FSL's dtifit tool (cluster usable)
  dwi_fsl_bedpostx_gpu        run FSL GPU-enabled bedpostx
  dwi_pre_tractography        generates space for dense whole-brain connectomes
  dwi_probtrackx_dense_gpu    run FSL's GPU-enabled probtrackx for dense whole-brain connectomes
  dwi_seed_tractography_dense reduce dense tractography data using a seed structure
  dwi_parcellate              parcellate dense tractography data
 
 Miscellaneous analyses
========================
 
  bold_compute_fc   computes seed or GBC BOLD functional connectivity
  bold_parcellate   parcellate BOLD data and generate pconn files
  anat_parcellate   parcellate T1w and T2w derived measures (e.g. myelin or thickness)
  extract_roi       extract data from pre-specified ROIs in CIFTI or NIFTI
  aws_hcp_sync      sync HCP data from aws s3 cloud
  data_sync         sync/backup data across hpc cluster(s)
  organize_dicom    sort DICOMs and setup nifti files from DICOMs
  map_hcp_files     setup data structure for hcp processing
 
EOF
 
}

# ---------------------------------------------------------------------------------------------------------------
#  -- Master Execution and Logging -- https://bitbucket.org/oriadev/qunex/wiki/Overview/Logging.md
# ---------------------------------------------------------------------------------------------------------------

bashExec() {

Platform="Platform Information: `uname -a`"

# -- Set the time stamp for given job
TimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
if [[ ${CommandToRun} == "run_turnkey" ]]; then
    unset GmriCommandToRun
    if [[ ! -z `echo ${TURNKEY_STEPS} | grep -E 'create_study|createStudy'` ]] && [[ ! -f ${StudyFolder}/.qunexstudy ]]; then
        if [[ ! -d ${WORKDIR} ]]; then 
            mkdir -p ${WORKDIR} &> /dev/null
        fi
        gmri create_study ${StudyFolder}
    fi
fi

# -- Check if Matlab command
unset QuNexMatlabCall
MatlabFunctionsCheck=`find $TOOLS/$QUNEXREPO/matlab/ -name "*.m" | grep -v "archive/"`
if [[ ! -z `echo $MatlabFunctionsCheck | grep "$CommandToRun"` ]]; then
    QuNexMatlabCall="$CommandToRun"
    echo ""
    echo " ==> Note: $QuNexMatlabCall is part of the QuNex MATLAB."
    echo ""
fi 

# -- Check if study folder is created
if [[ ! -f ${StudyFolder}/.qunexstudy ]] && [[ -d ${StudyFolder} ]] && [[ -z ${QuNexMatlabCall} ]]; then 
    echo ""
    mageho "WARNING: QuNex study folder specification .qunexstudy in ${StudyFolder} not found."
    mageho "         Check that ${StudyFolder} is a valid QuNex folder."
    mageho "         Consider re-generating QuNex hierarchy..."; echo ""
    # gmri create_study ${StudyFolder}
fi

if [[ -z ${QuNexMatlabCall} ]] && [[ -d ${StudyFolder}/sessions ]] && [[ ${SessionsFolder} != "sessions" ]] && [[ -f ${StudyFolder}/.qunexstudy ]]; then
    # -- Add check in case the sessions folder is distinct from the default name
    # -- Eventually use the template file to replace hard-coded values
    QuNexSessionsSubFolders=`more $TOOLS/$QUNEXREPO/python/qx_utilities/templates/study_folders_default.txt | tr -d '\r'`
    QuNexSessionsFolders="${SessionsFolder}/inbox/MR ${SessionsFolder}/inbox/EEG ${SessionsFolder}/inbox/BIDS ${SessionsFolder}/inbox/HCPLS ${SessionsFolder}/inbox/behavior ${SessionsFolder}/inbox/concs ${SessionsFolder}/inbox/events ${SessionsFolder}/archive/MR ${SessionsFolder}/archive/EEG ${SessionsFolder}/archive/BIDS ${SessionsFolder}/archive/HCPLS ${SessionsFolder}/archive/behavior ${SessionsFolder}/specs ${SessionsFolder}/QC"
    for QuNexSessionsFolder in ${QuNexSessionsFolders}; do
        if [[ ! -d ${QuNexSessionsFolder} ]]; then
              echo "QuNex folder ${QuNexSessionsFolder} not found. Generating now..."; echo ""
              mkdir -p ${QuNexSessionsFolder} &> /dev/null
        fi
    done
fi

# -- If logfolder flag set then set it and set master log
if [[ -z ${LogFolder} ]]; then
    MasterLogFolder="${StudyFolder}/processing/logs"
else
    MasterLogFolder="$LogFolder"
fi
if [[ ! -d ${MasterLogFolder} ]]; then
    mkdir ${MasterLogFolder} &> /dev/null
fi
# -- Set and generate runlogs folder
MasterRunLogFolder="${MasterLogFolder}/runlogs"
if [[ ! -d ${MasterRunLogFolder} ]]; then
    mkdir ${MasterRunLogFolder} &> /dev/null
fi
# -- Set and generate comlogs folder
MasterComlogFolder="${MasterLogFolder}/comlogs"
if [[ ! -d ${MasterComlogFolder} ]]; then
    mkdir ${MasterComlogFolder} &> /dev/null
fi
# -- Set and generate runchecks folder
RunChecksFolder="${StudyFolder}/processing/runchecks"
if [[ ! -d ${RunChecksFolder} ]]; then
    mkdir ${RunChecksFolder} &> /dev/null
fi

# -- Specific call for python qx_utilities functions
if [[ ${GmriCommandToRun} ]]; then
    echo ""
    cyaneho "--- Full QuNex call for command: ${GmriCommandToRun}"
    echo ""
    cyaneho "gmri ${gmriinput}"
    echo ""
    cyaneho "---------------------------------------------------------"
    echo ""
    echo ""
    gmri_function
    # -- Debugging for python qx_utilities functions that are not logging natively yet
    #
    # if [[ ${GmriCommandToRun} != "create_study" ]]; then
    #     GmriComLogFile=`ls -Art ${MasterComlogFolder}/*${GmriCommandToRun}_*.log | tail -n 1`
    #     # -- Temporary patch to allow for unified log handling in python qx_utilities
    #     if [[ `echo $GmriComLogFile | grep "tmp"` ]]; then
    #         echo ""
    #         mageho " NOTE: comlog file for ${GmriCommandToRun} is not generated directly via python qx_utilities but rather via run_turnkey."
    #         # mageho "       $GmriComLogFile"
    #         echo ""
    #         # GmriCompletionCheckPass="${RunChecksFolder}/CompletionCheck_${GmriCommandToRun}_${TimeStamp}.Pass"
    #         # GmriCompletionCheckFail="${RunChecksFolder}/CompletionCheck_${GmriCommandToRun}_${TimeStamp}.Fail"
    #         # GmriComComplete="cat ${GmriComLogFile} | grep 'Successful completion' > ${GmriCompletionCheckPass}"
    #         # GmriComError="cat ${GmriComLogFile} | grep 'ERROR' > ${GmriCompletionCheckFail}"
    #         # GmriComRunCheck="if [[ -e ${GmriCompletionCheckPass} && ! -s ${GmriCompletionCheckFail} ]]; then echo ''; geho ' ===> Successful completion of ${GmriCommandToRun}'; qunexPassed; echo ''; else echo ''; echo ' ===> ERROR during ${CommandToRun}'; echo ''; qunexFailed;o ''; fi"
    #         # GmriComRunAll="${GmriComComplete}; ${GmriComError}; ${GmriComRunCheck}"
    #         # eval "${GmriComRunAll}"
    #     fi
    # fi
    # --------------------------------------------------------------------------
else
# -- Specific call for QuNex bash functions
    
    # -- Define specific logs
    #
    # -- Runlog
    #    Specification: Log-<command name>-<date>_<hour>.<minute>.<microsecond>.log
    #    Example:       Log-map_hcp_data-2017-11-11_15.58.1510433930.log
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
    ComlogDone="${MasterComlogFolder}/done_${CommandToRun}_${CASE}_${TimeStamp}.log"
    CompletionCheckPass="${RunChecksFolder}/CompletionCheck_${CommandToRun}_${TimeStamp}.Pass"
    ComlogError="${MasterComlogFolder}/error_${CommandToRun}_${CASE}_${TimeStamp}.log"
    CompletionCheckFail="${RunChecksFolder}/CompletionCheck_${CommandToRun}_${TimeStamp}.Fail"
    
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
    cyaneho "--- Full QuNex call for command: ${CommandToRun}"
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
     
    # -- Check that $ComRun is set properly
    echo ""; if [ ! -f "${ComRun}" ]; then reho "ERROR: ${ComRun} file not found. Check your inputs"; echo ""; return 1; fi
    ComRunSize=`wc -c < ${ComRun}` > /dev/null 2>&1
    echo ""; if [[ "${ComRunSize}" == 0 ]]; then > /dev/null 2>&1; reho "ERROR: ${ComRun} file found but has no content. Check your inputs"; echo ""; return 1; fi

    # -- Define command to execute
    ComRunExec=". ${ComRun} 2>&1 | tee -a ${ComlogTmp}"
    # -- Acceptance tests
    ComComplete="cat ${ComlogTmp} | grep 'Successful completion' > ${CompletionCheckPass}"
    ComError="cat ${ComlogTmp} | grep 'ERROR' > ${CompletionCheckFail}"

    # -- Run the commands locally
    if [[ ${Cluster} == 1 ]]; then
        # -- Command to perform acceptance test
        ComRunCheck="if [[ ! -s ${CompletionCheckPass} && ! -s ${CompletionCheckFail} ]]; then mv ${ComlogTmp} ${ComlogDone}; echo ''; echo ' ===> Successful completion of ${CommandToRun}. Check final QuNex log output:'; echo ''; echo '    ${ComlogDone}'; qunexPassed; echo ''; else mv ${ComlogTmp} ${ComlogError}; echo ''; echo ' ===> ERROR during ${CommandToRun}. Check final QuNex error log output:'; echo ''; echo '    ${ComlogError}'; echo ''; qunexFailed; fi"
        # -- Combine final string of commands
        ComRunAll="${ComRunExec}; ${ComComplete}; ${ComError}; ${ComRunCheck}"

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
        # -- Command to perform acceptance test
        ComRunCheck="if [[ ! -s ${CompletionCheckPass} && ! -s ${CompletionCheckFail} ]]; then mv ${ComlogTmp} ${ComlogDone}; echo ''; echo ' ===> Successful completion of ${CommandToRun}. Check final QuNex log output:'; echo ''; echo '    ${ComlogDone}'; echo ''; echo 'QUNEX PASSED!'; echo ''; else mv ${ComlogTmp} ${ComlogError}; echo ''; echo ' ===> ERROR during ${CommandToRun}. Check final QuNex error log output:'; echo ''; echo '    ${ComlogError}'; echo ''; echo ''; echo 'QUNEX FAILED!'; fi"
        # -- Combine final string of commands
        ComRunAll="${ComRunExec}; ${ComComplete}; ${ComError}; ${ComRunCheck}"

        cd ${MasterRunLogFolder}
        gmri schedule command="${ComRunAll}" settings="${Scheduler}" bash="${Bash}"
        geho "--------------------------------------------------------------"
        echo ""
        geho "   Data successfully submitted to scheduler"
        geho "   Scheduler details: ${Scheduler}"
        geho "   Command log: ${Runlog}"
        geho "   Command output: ${ComlogTmp} "
        echo ""
        geho "--------------------------------------------------------------"
        echo ""
    fi

fi

}

# ---------------------------------------------------------------------------------------------------------------
#  -- run_turnkey - Turnkey execution of QuNex workflow via the XNAT docker engine
# ---------------------------------------------------------------------------------------------------------------

run_turnkey() {
# -- Specify command variable
unset QuNexCallToRun
unset GmriCommandToRun
QuNexCallToRun="${TOOLS}/${QUNEXREPO}/bash/qx_utilities/run_turnkey.sh --bolds=\"${BOLDS// /,}\" ${runTurnkeyArguments} --sessions=\"${CASE}\" --turnkeysteps=\"${TURNKEY_STEPS// /,}\" --sessionids=\"${CASE}\""
bashExec
}
show_usage_run_turnkey() {
${TOOLS}/${QUNEXREPO}/bash/qx_utilities/run_turnkey.sh
}

# ----------------------------------------------------------------------------------------------------------------
#  -- organize_dicom - Sort original DICOMs into folders and generates NIFTI files using sort_dicom and dicom2niix
# ----------------------------------------------------------------------------------------------------------------

organize_dicom() {
# -- Note: This command passes parameters into two python qx_utilities commands: sort_dicom and dicom2niix
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
    geho "     NOTE: To re-run set --overwrite='yes'"
    echo ""
    geho " ... $CASE ---> organize_dicom done"
    echo ""
    return 0
fi
# -- Check if inbox missing or is empty
if [ ! -d ${SessionsFolder}/${CASE}/dicom ]; then
    echo "WARNING: ${SessionsFolder}/${CASE}/dicom folder not found. Checking for ${SessionsFolder}/${CASE}/inbox/"; echo ""
    if [ ! -d ${SessionsFolder}/${CASE}/inbox ]; then
        reho "ERROR: ${SessionsFolder}/${CASE}/inbox not found. Make sure your DICOMs are present inside ${SessionsFolder}/${CASE}/inbox/"; echo ""
        exit 1
    fi
fi
if [ -d ${SessionsFolder}/${CASE}/dicom ]; then
     DicomCheck=`ls ${SessionsFolder}/${CASE}/dicom/`
     InboxCheck=`ls ${SessionsFolder}/${CASE}/inbox/`
     if [[ ${InboxCheck} != "" ]]; then
         echo "===> ${SessionsFolder}/${CASE}/dicom/ found and data exists."; echo ""
         if [[ ${InboxCheck} == "" ]]; then
             reho "ERROR: ${SessionsFolder}/${CASE}/inbox/ found but empty. Will re-run sort_dicom from ${SessionsFolder}/${CASE}/dicom"; echo ""
         fi
    fi
fi
# -- Specify command variable
unset CommandToRun
ComA="cd ${SessionsFolder}/${CASE}"
ComB="gmri sort_dicom folder=. "
ComC="gmri dicom2niix unzip=${Unzip} gzip=${Gzip} clean=${Clean} verbose=${VerboseRun} parelements=${ParElements} sessionid=${CASE}"
ComD="slicesdir ${SessionsFolder}/${CASE}/nii/*.nii*"
QuNexCallToRun="${ComA}; ${ComB}; ${ComC}; ${ComD}"
# -- QuNex bash execute function
bashExec
}

show_usage_organize_dicom() {
 echo ""
 echo "qunex organize_dicom"
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
 echo "--overwrite       Explicitly force a re-run of organize_dicom"
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
 echo " qunex organize_dicom --sessionsfolder='<folder_with_sessions>' \ "
 echo " --sessions='<comma_separarated_list_of_cases>' "
 echo " --scheduler='<name_of_scheduler_and_options>'"
 echo ""
}

# ------------------------------------------------------------------------------------------------------
#  -- map_hcp_files - Setup the HCP File Structure
# ------------------------------------------------------------------------------------------------------

map_hcp_files() {
# -- Specify command variable
if [[ ${Overwrite} == "yes" ]]; then
    HLinks=`ls ${SessionsFolder}/${CASE}/hcp/${CASE}/*/*nii* 2>/dev/null`; for HLink in ${HLinks}; do unlink ${HLink}; done
fi
QuNexCallToRun="cd ${SessionsFolder}/${CASE}; echo '--> running map_hcp_files for ${CASE}'; echo ''; gmri setup_hcp"
# -- QuNex bash execute function
bashExec
}
show_usage_map_hcp_files() {
 echo ""
 echo "qunex map_hcp_files"
 echo ""
 echo "This command maps the Human Connectome Project folder structure for "
 echo "preprocessing. It should be executed after proper organize_dicom and session.txt "
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
 echo " qunex map_hcp_files --sessionsfolder='<folder_with_sessions>' \ "
 echo "     --sessions='<comma_separarated_list_of_cases>' \ "
 echo ""
 echo "Example with flagged parameters for submission to the scheduler::"
 echo ""
 echo " qunex map_hcp_files --sessionsfolder='<folder_with_sessions>' \ "
 echo "     --sessions='<comma_separarated_list_of_cases>' \ "
 echo "     --scheduler='<name_of_cluster_scheduler_and_options>' \ "
 echo ""
}

# ------------------------------------------------------------------------------------------------------
#  -- data_sync - Sync files to Yale HPC and back to the Yale server after HCP preprocessing
# ------------------------------------------------------------------------------------------------------

data_sync() {
# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/data_sync.sh \
--syncfolders="${SyncFolders}" \
--sessions="${CASE}" \
--syncserver="${SyncServer}" \
--synclogfolder="${SyncLogFolder}" \
--syncdestination="${SyncDestination}""
# -- QuNex bash execute function
bashExec
}
show_usage_data_sync() {
 echo ""
 echo "qunex data_sync"
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
 echo " qunex --command=data_sync \ "
 echo "   --syncfolders=<path_to_folders> \ "
 echo "   --syncserver=<sync_server> \ "
 echo "   --syncdestination=<destination_path> \ "
 echo "   --synclogfolder=<path_to_log_folder>  \ "
 echo ""
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- dwi_legacy - Executes the Diffusion Processing Script via FUGUE implementation for legacy data - (needed for legacy DWI data that is non-HCP compliant without counterbalanced phase encoding directions needed for topup)
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

dwi_legacy() {
# -- Unique requirements for This command:
#    Needs CUDA libraries to run eddy_cuda (10x faster than on a CPU)

# -- Specify command variable
QuNexCallToRun="${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_legacy.sh \
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
# -- QuNex bash execute function
bashExec
}
show_usage_dwi_legacy() {
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_legacy.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- dwi_eddy_qc - Executes the DWI EddyQ C (dwi_eddy_qc.sh) via the QuNex bash wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

dwi_eddy_qc() {
# -- Check if eddy_squad and eddy_quad exist in user path
EddySquadCheck=`which eddy_squad`
EddyQuadCheck=`which eddy_quad`
if [[ -z ${EddySquadCheck} ]] || [[ -z ${EddySquadCheck} ]]; then
    echo ""
    reho "ERROR: EDDY QC does not seem to be installed on this system."
    echo ""
    exit 1
fi
# -- INPUTS:  eddy-cleaned DWI Data
# -- OUTPUTS: located in <eddyBase>.qc per EDDY QC specification

# -- Specify command variable
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_eddy_qc.sh \
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
# -- QuNex bash execute function
bashExec
}
show_usage_dwi_eddy_qc() {
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_eddy_qc.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- dwi_parcellate - Executes the Diffusion Parcellation Script (dwi_parcellate.sh) via the QuNex bash wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

dwi_parcellate() {
#DWIOutput="${SessionsFolder}/${CASE}/hcp/$CASE/MNINonLinear/Results/Tractography"
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_parcellate.sh \
--sessionsfolder=${SessionsFolder} \
--session=${CASE} \
--matrixversion=${MatrixVersion} \
--parcellationfile=${ParcellationFile} \
--waytotal=${WayTotal} \
--outname=${OutName} \
--overwrite=${Overwrite}"
# -- QuNex bash execute function
bashExec
}
show_usage_dwi_parcellate() {
echo ""
echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_parcellate.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- dwi_seed_tractography_dense - Executes the Diffusion Seed Tractography Script (dwi_seed_tractography_dense.sh) via the QuNex bash wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

dwi_seed_tractography_dense() {
# -- Command to run
QuNexCallToRun="dwi_seed_tractography_dense.sh \
--sessionsfolder="${SessionsFolder}" \
--sessions="${CASE}" \
--matrixversion="${MatrixVersion}" \
--seedfile="${SeedFile}" \
--waytotal="${WayTotal}" \
--outname="${OutName}" \
--overwrite="${Overwrite}""
# -- QuNex bash execute function
bashExec
}
show_usage_dwi_seed_tractography_dense() {
echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_seed_tractography_dense.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- compute_bold_fc - Executes Global Brain Connectivity (GBC) or seed-based functional connectivity (bold_compute_fc.sh) via the QuNex bash wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

compute_bold_fc() {

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
    QuNexCallToRun="${TOOLS}/${QUNEXREPO}/bash/qx_utilities/bold_compute_fc.sh \
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
    # -- QuNex bash execute function
    bashExec
fi
# -- Check type of connectivity calculation is gbc
if [[ ${Calculation} == "gbc" ]]; then
    echo ""
    # -- Specify command variable
    QuNexCallToRun="${TOOLS}/${QUNEXREPO}/bash/qx_utilities/bold_compute_fc.sh \
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
    # -- QuNex bash execute function
    bashExec
fi
# -- Check type of connectivity calculation is seed
if [[ ${Calculation} == "dense" ]]; then
    echo ""
    # -- Specify command variable
    QuNexCallToRun="${TOOLS}/${QUNEXREPO}/bash/qx_utilities/bold_compute_fc.sh \
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
    # -- QuNex bash execute function
    bashExec
fi
}

show_usage_compute_bold_fc() {
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/bash/qx_utilities/bold_compute_fc.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- anat_parcellate - Executes the Structural Parcellation Script (StructuralParcellation.sh) via the QuNex bash wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

anat_parcellate() {
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
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/anat_parcellate.sh \
--sessionsfolder=${SessionsFolder} \
--session=${CASE} \
--inputdatatype=${InputDataType} \
--parcellationfile=${ParcellationFile} \
--overwrite=${Overwrite} \
--outname=${OutName} \
--extractdata=${ExtractData}"
# -- QuNex bash execute function
bashExec
}
show_usage_anat_parcellate() {
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/bash/qx_utilities/anat_parcellate.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- bold_parcellate - Executes the BOLD Parcellation Script (bold_parcellate.sh) via the QuNex bash wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

bold_parcellation() {
# -- Parse general parameters
if [[ -z ${SingleInputFile} ]]; then
    BOLDOutput="${SessionsFolder}/${CASE}/${OutPath}"
else
    BOLDOutput="${OutPath}"
fi
# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/bold_parcellate.sh \
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
# -- QuNex bash execute function
bashExec
}

show_usage_bold_parcellation() {
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/bash/qx_utilities/bold_parcellate.sh
}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  -- extract_roi - Executes the ROI Extraction Script (extract_roi.sh) via the QuNex bash wrapper
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

extract_roi() {
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
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/extract_roi.sh \
--roifile='${ROIInputFile}' \
--inputfile='${InputFile}' \
--outdir='${OutPath}' \
--outname='${OutName}'"
# -- QuNex bash execute function
bashExec
}
show_usage_roi_extract() {
echo ""
echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/bash/qx_utilities/extract_roi.sh
}

# ------------------------------------------------------------------------------------------------------
#  -- dwi_fsl_dtifit - Executes the dtifit script from FSL (needed for probabilistic tractography)
# ------------------------------------------------------------------------------------------------------

dwi_fsl_dtifit() {

# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_fsl_dtifit.sh \
--sessionsfolder='${SessionsFolder}' \
--session='${CASE}' \
--overwrite='${Overwrite}' \
--species='${Species}' "
# -- QuNex bash execute function
bashExec
}
show_usage_dwi_fsl_dtifit() {
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_fsl_dtifit.sh
}

# ------------------------------------------------------------------------------------------------------
#  -- dwi_fsl_bedpostx_gpu - Executes the bedpostx_gpu code from FSL (needed for probabilistic tractography)
# ------------------------------------------------------------------------------------------------------

dwi_fsl_bedpostx_gpu() {
# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_fsl_bedpostx_gpu.sh \
--sessionsfolder='${SessionsFolder}' \
--session='${CASE}' \
--fibers='${Fibers}' \
--weight='${Weight}' \
--burnin='${Burnin}' \
--jumps='${Jumps}' \
--sample='${Sample}' \
--model='${Model}' \
--rician='${Rician}' \
--overwrite='${Overwrite}' \
--species=${Species}"
# -- QuNex bash execute function
bashExec
}

show_usage_dwi_fsl_bedpostx_gpu() {
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_fsl_bedpostx_gpu.sh
}

# ------------------------------------------------------------------------------------------------------------------------------
#  -- auto_ptx - Executes the auto_ptx script from FSL (needed for probabilistic estimation of large-scale fiber bundles / tracts)
# -------------------------------------------------------------------------------------------------------------------------------

auto_ptx() {
geho "WARNING: auto_ptx is deprecated, you should probably use fsl_xtract instead!"

# -- Check inputs
if [[ -d ${BedPostXFolder} ]]; then 
    reho "ERROR: Prior BedpostX run not found or incomplete for $CASE. Check work and re-run."
    exit 1
fi
if [[ -z ${AutoPtxFolder} ]]; then 
    reho "ERROR: AutoPtxFolder environment variable not. Set it correctly and re-run."
    exit 1
fi
# -- Set commands
Com1="${AutoPtxFolder}/autoptx ${SessionsFolder} ${CASE} ${BedPostXFolder}"
Com2="${AutoPtxFolder}/Prepare_for_Display.sh ${StudyFolder}/${CASE}/MNINonLinear/Results/autoptx 0.005 1"
Com3="${AutoPtxFolder}/Prepare_for_Display.sh ${StudyFolder}/${CASE}/MNINonLinear/Results/autoptx 0.005 0"
# -- Command to run
QuNexCallToRun="${Com1}; ${Com2}; ${Com3}"
# -- QuNex bash execute function
bashExec
}

show_usage_auto_ptx() {
echo ""
echo "qunex ${UsageInput} "
echo ""
echo "This command runs the auto_ptx script in ${AutoPtxFolder}."
echo ""
echo "For full details on auto_ptx functionality see: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/AutoPtx"
echo ""
}

# -------------------------------------------------------------------------------------------------------------------
#  -- dwi_pre_tractography
#  - Executes the HCP Pretractography (dwi_pre_tractography) [ Stam's implementation for all grayordinates ]
# ------------------------------------------------------------------------------------------------------------------

dwi_pre_tractography() {
# -- Parse general parameters
TimeLog=`date '+%Y-%m-%d-%H-%M-%S'`
LogFile="${StudyFolder}/processing/logs/comlogs/dwi_pre_tractography_${CASE}_${TimeLog}.log"
RunFolder="${SessionsFolder}/${CASE}/hcp/"
# -- Command to run
QuNexCallToRun="${HCPPIPEDIR_dMRITractFull}/pre_tractography/pre_tractography.sh ${RunFolder} ${CASE} 0 ${LogFile}"
# -- QuNex bash execute function
bashExec
}
show_usage_dwi_pre_tractography() {
echo ""; echo "qunex ${UsageInput}"
${HCPPIPEDIR_dMRITractFull}/pre_tractography/pre_tractography.sh
}

# --------------------------------------------------------------------------------------------------------------------------------------------------
#  -- dwi_probtrackx_dense_gpu - Executes the HCP Matrix1 and / or 3 code and generates WB dense connectomes (Stam's implementation for all grayordinates)
# --------------------------------------------------------------------------------------------------------------------------------------------------

dwi_probtrackx_dense_gpu() {
# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_probtrackx_dense_gpu.sh \
--sessionsfolder='${SessionsFolder}' \
--sessions='${CASES}' \
--scriptsfolder='${ScriptsFolder}' \
--omatrix1='${MatrixOne}' \
--omatrix3='${MatrixThree}' \
--nsamplesmatrix1='${NsamplesMatrixOne}' \
--nsamplesmatrix3='${NsamplesMatrixThree}' \
--overwrite='${Overwrite}' "
# -- QuNex bash execute function
bashExec
}
show_usage_dwi_probtrackx_dense_gpu() {
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_probtrackx_dense_gpu.sh
}

# ------------------------------------------------------------------------------------------------------------------------------
#  -- Sync data from AWS buckets - customized for HCP
# -------------------------------------------------------------------------------------------------------------------------------
aws_hcp_sync() {
mkdir ${SessionsFolder}/aws.logs &> /dev/null
cd $SessionsFolder}/aws.logs
if [ ${RunMethod} == "2" ]; then
    echo "AWS sync dry run..."
    if [ -d ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear ]; then
        mkdir ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality} &> /dev/null
        AWSSyncTimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        time aws s3 sync --dryrun s3:/${Awsuri}/${CASE}/${Modality} ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality}/ >> aws_hcp_sync_${CASE}_${Modality}_${AWSSyncTimeStamp}.log
    else
        mkdir -p ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality} &> /dev/null
        AWSSyncTimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        time aws s3 sync --dryrun s3:/${Awsuri}/${CASE}/${Modality} ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality}/ >> aws_hcp_sync_${CASE}_${Modality}_${AWSSyncTimeStamp}.log
    fi
fi
if [ ${RunMethod} == "1" ]; then
    geho "AWS sync running..."
    if [ -d ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear ]; then
        mkdir ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality} &> /dev/null
        AWSSyncTimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        time aws s3 sync s3:/${Awsuri}/${CASE}/${Modality} ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality}/ >> aws_hcp_sync_${CASE}_${Modality}_${AWSSyncTimeStamp}.log
    else
        mkdir -p ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality} &> /dev/null
        AWSSyncTimeStamp=`date +%Y-%m-%d_%H.%M.%10N`
        time aws s3 sync s3:/${Awsuri}/${CASE}/${Modality} ${SessionsFolder}/${CASE}/hcp/${CASE}/${Modality}/ >> aws_hcp_sync_${CASE}_${Modality}_${AWSSyncTimeStamp}.log
    fi
fi
}
show_usage_aws_hcp_sync() {
echo ""
echo "qunex aws_hcp_sync"
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
echo "  qunex aws_hcp_sync"
echo "        --sessionsfolder='<path_to_study_sessions_folder>' \ "
echo "        --sessions='<comma_separated_list_of_cases>' \ "
echo "        --command='' \ "
echo "        --modality='T1w' \ "
echo "        --awsuri='/hcp-openaccess/HCP_900'"
echo ""
}

# ------------------------------------------------------------------------------------------------------------------------------
# -- run_qc - Performs various QC operations across modalities
# -------------------------------------------------------------------------------------------------------------------------------

run_qc() {
# -- Check general output folders for QC
if [ ! -d ${SessionsFolder}/QC ]; then
    mkdir -p ${SessionsFolder}/QC &> /dev/null
fi
# -- Check T1w output folders for QC
if [ ! -d ${OutPath} ]; then
    mkdir -p ${OutPath} &> /dev/null
fi

# -- Command to run
QuNexCallToRun=". ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/run_qc.sh \
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
# -- QuNex bash execute function
bashExec
}
show_usage_run_qc() {
echo ""; echo "qunex ${UsageInput}"
${TOOLS}/${QUNEXREPO}/bash/qx_utilities/run_qc.sh
}

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=
# =-=-=-=-=-==-=-=-= Establish general QuNex functions and variables =-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=

# -- Setup this script such that if any command exits with a non-zero value, the
#    script itself exits and does not attempt any further processing.
# set -e

# ------------------------------------------------------------------------------
#  Capture current working directory
# ------------------------------------------------------------------------------
dirs -c  &> /dev/null
pushd `pwd`  &> /dev/null 

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
show_version() {
    QuNexVer=`cat ${TOOLS}/${QUNEXREPO}/VERSION.md`
    echo ""
    echo "Quantitative Neuroimaging Environment & Toolbox (QuNex) Suite Version: v${QuNexVer}"
    echo ""
}

# ------------------------------------------------------------------------------
#  Parse Command Line Options
# ------------------------------------------------------------------------------

# -- Check if version was requested
if [ "$1" == "-version" ] || [ "$1" == "version" ] || [ "$1" == "--version" ] || [ "$1" == "--v" ] || [ "$1" == "-v" ]; then
    show_version
    echo ""
    exit 0
fi
if [ $(opts_CheckForHelpRequest $@) ]; then
    show_version
    show_usage
    exit 0
fi
if [[ -z ${1} ]]; then
    show_version
    show_usage
    exit 0
fi
if [[ ${1} == "help" ]]; then
    show_version
    show_usage
    exit 0
fi

if [[ ${1} == "--envsetup" ]] || [[ ${1} == "-envsetup" ]] || [[ ${1} == "envsetup" ]]; then
    show_version
    echo ""
    echo "Printing help call for $TOOLS/$QUNEXREPO/env/qunex_environment.sh"
    echo ""
    bash ${TOOLS}/$QUNEXREPO/env/qunex_environment.sh --help
    exit 0
fi


# ------------------------------------------------------------------------------
#  map deprecated commands
# ------------------------------------------------------------------------------

# use the check_deprecated_commands from niutilities to remap 
if [[ $1 != --* ]]; then
    COMMANDNAME=`gmri check_deprecated_commands --command="$1" | grep "is now known as" | sed 's/^.*is now known as //g'`
    if [[ -n $COMMANDNAME ]]; then
        set -- ${COMMANDNAME} "${@:2}"
    fi
fi


# ------------------------------------------------------------------------------
#  gmri loop outside local functions to bypass checking
# ------------------------------------------------------------------------------

# -- Get list of all supported gmri functions
gmrifunctions=`gmri -available`
# -- Check if command-line input matches any of the gmri functions
unset GmriCommandToRun
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

        # -- Insert double quotes if an argument has whitespaces in its value
        unset gmriinput
        whitespace="[[:space:]]"
        for inputarg in "$@"; do
            if [[ $inputarg =~ ${whitespace} ]]; then
                inputarg=`echo "${inputarg}\"" | sed "s/=/=\"/g"`
            fi
            if [[ ${inputarg} =~ '=' ]] && [[ -z `echo ${inputarg} | grep '-'` ]]; then
                inputarg="--${inputarg}"
            fi

            if [[ -z $gmriinput ]]; then
                gmriinput="${inputarg}"
            else
                gmriinput="${gmriinput} ${inputarg}"
            fi
        done
    fi
else
    unset GmriCommandToRun
fi


# ------------------------------------------------------------------------------
#  Check if specific command help requested
# ------------------------------------------------------------------------------

isQuNexFunction() {
MatlabFunctionsCheck=`find $TOOLS/$QUNEXREPO/matlab/ -name "*.m" | grep -v "archive/"`
if [[ -z "${QuNexCommands##*$1*}" ]]; then
    return 0
elif [[ ! -z `echo $MatlabFunctionsCheck | grep "$1"` ]]; then
    QuNexMatlabFunction="$1"
    echo ""
    echo "Requested $MatlabFunction function is part of the QuNex MATLAB. Checking usage:"
    echo ""
    ${QUNEXMCOMMAND} "help ${QuNexMatlabFunction},quit()"
    exit 0
else
    echo ""
    reho "ERROR: $1 --> Requested function is not supported. Refer to general QuNex usage."
    echo ""
    exit 0
fi
}

# -- Get all the functions from the usage calls

# -- Check for input with double flags
if [[ ${1} =~ .*--.* ]] && [[ -z ${2} ]] || [[ ${1} =~ .*-.* ]] && [[ -z ${2} ]]; then
    Usage="$1"
    # -- Check for gmri help inputs (--o --l --c)
    if [[  ${Usage}  == "--o" ]]; then
        show_processingoptions_gmri
        exit 0
    fi
    if [[ ${Usage} == "--a" ]] || [[ ${Usage} == "--all" ]] || [[ ${Usage} == "--allcommands" ]] || [[ ${Usage} == "-a" ]] || [[ ${Usage} == "-all" ]] || [[ ${Usage} == "-allcommands" ]]; then
        show_splash
        show_allcommands_bash
        show_allcommands_gmri
        show_usage_matlab_help
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
    show_version
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
        show_allcommands_bash
        show_allcommands_gmri
        show_usage_matlab_help
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
    show_version
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
    show_version
    show_usage_"${UsageInput}"
    exit 0
fi
# -- Check for input with no flags
if [[ -z ${2} ]]; then
    UsageInput="$1"
    # -- Check if input part of function list
    isQuNexFunction ${UsageInput}
    show_version
    show_usage_"${UsageInput}"
    exit 0
fi

echo ""
geho " ........................ Running QuNex v${QuNexVer} ........................"
echo ""


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

if [[ ${CommandToRun} == "run_turnkey" ]]; then
    runTurnkeyArguments="$@"
    runTurnkeyArguments=`printf '%s\n' "${runTurnkeyArguments//run_turnkey/}"`
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
    StudyFolder=`opts_GetOpt "${setflag}studyfolder" $@`                      # study folder to work on
    if [[ -z ${StudyFolder} ]]; then
        StudyFolder=`opts_GetOpt "${setflag}path" $@`                         # local folder to work on
    fi
    StudyFolderPath="${StudyFolder}"
    STUDY_PATH="${StudyFolder}"    

    SessionsFolder=`opts_GetOpt "${setflag}sessionsfolder" $@`                # sessions folder path to work on
    if [[ -z ${SessionsFolder} ]]; then
       SessionsFolder=`opts_GetOpt "${setflag}sessionfolder"  $@`                # sessions folder path to work on
    fi    
    # -- backwards compatibility -- sessionsfolder used to be supported by --subjectsfolder or --subjectfolder
    if [[ -z ${SessionsFolder} ]]; then
        SubjectFolder=`opts_GetOpt "${setflag}subjectsfolder" $@`
        SessionsFolder="${SubjectFolder}"
        if [[ ! -z ${SubjectFolder} ]]; then
            mageho "WARNING: The --subjectsfolder parameter is now renamed to --sessionsfolder"
        fi
    fi
    if [[ -z ${SessionsFolder} ]]; then
        SubjectFolder=`opts_GetOpt "${setflag}subjectfolder" $@`
        SessionsFolder="${SubjectFolder}"
        if [[ ! -z ${SubjectFolder} ]]; then
            mageho "WARNING: The --subjectfolder parameter is now renamed to --sessionsfolder"
        fi
    fi
    
    # -- Check StudyFolder and set
    if [[ -z ${StudyFolder} ]] && [[ ! -z ${StudyFolderPath} ]]; then
        StudyFolder="$StudyFolderPath"
        STUDY_PATH="${StudyFolderPath}"
    fi
    if [[ ! -z ${StudyFolder} ]] && [[ -z ${StudyFolderPath} ]]; then
        StudyFolderPath="$StudyFolder"
        STUDY_PATH="${StudyFolder}"
    fi

    # -- If study folder is missing but sessions folder is defined assume standard QuNex folder structure
    if [[ -z ${StudyFolder} ]]; then
        if [[ ! -z ${SessionsFolder} ]] && [[ -d ${SessionsFolder} ]]; then
            cd ${SessionsFolder}/../ &> /dev/null
            StudyFolder=`pwd` &> /dev/null
            popd  &> /dev/null
            
            StudyFolderPath="${StudyFolder}"
            STUDY_PATH="${StudyFolder}"
        else
            StudyFolder=`echo ${SessionsFolder%/*}`
            if [[ -d ${StudyFolder} ]]; then
                SessionsFolderName=`basename ${SessionsFolder}`
                echo ""
                mageho "WARNING: ${StudyFolder}/${SessionsFolderName} is not present."
                echo ""
                echo "    ---> Found: ${StudyFolder}"
                SessionsFolderName="sessions"
                SessionsFolder="${StudyFolder}/${SessionsFolderName}"
            fi
            if [ -d ${SessionsFolder} ]; then
                echo "    ---> Resetting to defaults: ${SessionsFolder}"
                echo ""
            else
                echo ""
                echo ""
                reho "ERROR: Study folder or sessions folder is not defined or missing."
                reho "       Check your inputs and re-run QuNex."
                echo ""
                exit 1
            fi
        fi
    fi
    
    # -- Check if SessionsFolderName and SessionsFolder match
    if [[ ! -z ${SessionsFolder} ]] && [[ ! -z ${SessionsFolderName} ]]; then
        SessionsFolderBase=`basename ${SessionsFolder}`
        if [[ ${SessionsFolderBase} != ${SessionsFolderName} ]]; then 
            mageho "WARNING: Sessions folder base is mismatching the --sessionsfoldername input."
            echo ""
            echo "    ---> Aligning variables to match ${SessionsFolder}"
            SessionsFolderName=`basename ${SessionsFolder}`
            echo "    ---> Session folder name set to: ${SessionsFolderName}"
            echo ""
        fi
    fi
    

    # -- If sessions folder is missing but study folder is defined assume standard QuNex folder structure
    if [[ -z ${SessionsFolder} ]]; then
       if [[ -z ${SessionsFolderName} ]]; then
           SessionsFolderName="sessions"
           if [[ ! -z ${SubjectFolder} ]]; then
               SessionsFolder="${SubjectFolder}"
           fi
           if [[ -z ${StudyFolder} ]]; then
               echo "" &> /dev/null
           else
               SessionsFolder="$StudyFolder/$SessionsFolderName"
           fi
       fi
    fi

    # -- If session folder name is missing but absolute path sessions folder is defined assume standard QuNex folder structure or check basename
    if [[ -z ${SessionsFolderName} ]]; then
        if [[ -z ${SessionsFolder} ]]; then
            SessionsFolderName="sessions"
            if [[ ! -z ${StudyFolder} ]]; then
                SessionsFolder="${StudyFolder}/${SessionsFolderName}"
            else
                echo "" &> /dev/null
            fi
        else
            SessionsFolderName=`basename ${SessionsFolder}`
        fi
    fi
    
    if [[ -z ${STUDY_PATH} ]]; then
         STUDY_PATH=${StudyFolder}
    fi
    if [[ -z ${StudyFolderPath} ]]; then
         StudyFolderPath=${StudyFolder}
    fi

    # -- If logfolder flag set then set it and set master log
    if [[ -z ${LogFolder} ]]; then
        LogFolder="${StudyFolder}/processing/logs"
    fi
            
    # -- Set additional RunTurnkey flags
    TURNKEY_TYPE=`opts_GetOpt "${setflag}turnkeytype" $@`
    TURNKEY_STEPS=`opts_GetOpt "${setflag}turnkeysteps" $@`
    WORKDIR=`opts_GetOpt "${setflag}workingdir" $@`
    PROJECT_NAME=`opts_GetOpt "${setflag}projectname" $@`
    CleanupSession=`opts_GetOpt "${setflag}cleanupsession" $@`
    CleanupProject=`opts_GetOpt "${setflag}cleanupproject" $@`
    RawDataInputPath=`opts_GetOpt "${setflag}rawdatainput" $@`
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

    # -- General sessions and sessionids flags
    CASES=`opts_GetOpt "${setflag}sessions" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
    SESSIONIDS=`opts_GetOpt "${setflag}sessionids" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSIONIDS=`echo "$SESSIONIDS" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
    if [[ -z ${CASES} ]]; then
        if [[ ! -z ${SESSIONIDS} ]]; then
            CASES="$SESSIONIDS"
            SESSIONS="$SESSIONIDS"
        fi
    fi
     
    # -- Backwards comapatibility, session* used to be subject* 
    if [[ -z ${CASES} ]]; then
        CASES=`opts_GetOpt "${setflag}subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
        SESSIONS="$CASES"
        SESSIONIDS="$CASES"
        if [[ ! -z ${CASES} ]]; then
            mageho "WARNING: The --subjects parameter is now renamed to --sessions"
        fi
    fi
    
    # -- Backwards compatibility, sessionids* used to be subjid* 
    if [[ -z ${CASES} ]]; then
        if [[ -z ${SESSIONIDS} ]]; then
            SESSIONIDS=`opts_GetOpt "${setflag}subjid" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSIONIDS=`echo "$SESSIONIDS" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
            SESSIONS="$SESSIONIDS"
            CASES="$SESSIONS"
            if [[ ! -z ${SESSIONIDS} ]]; then
                mageho "WARNING: The --subjid parameter is now renamed to  --sessionids"
            fi
        fi
    fi

    if [[ -z ${CASES} ]]; then
        if [[ -z ${SESSION_LABELS} ]]; then
            SESSION_LABELS=`opts_GetOpt "--session" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
            SESSIONS="$SESSION_LABELS"
            CASES="$SESSION_LABELS"
            SESSIONIDS="$SESSION_LABELS"
        fi
    fi
    
    if [[ -z ${CASES} ]]; then
        if [[ -z ${SESSION_LABELS} ]]; then
            SESSION_LABELS=`opts_GetOpt "--sessionlabels" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
            SESSIONS="$SESSION_LABELS"
            CASES="$SESSION_LABELS"
            SESSIONIDS="$SESSION_LABELS"
        fi
    fi
    
    if [[ -z ${CASES} ]]; then
        if [[ -z ${SESSION_LABELS} ]]; then
            SESSION_LABELS=`opts_GetOpt "--sessions" "$@" | sed 's/,/ /g;s/|/ /g'`; SESSION_LABELS=`echo "$SESSION_LABELS" | sed 's/,/ /g;s/|/ /g'`
            SESSIONS="$SESSION_LABELS"
            CASES="$SESSION_LABELS"   
            SESSIONIDS="$SESSION_LABELS"
        fi
    fi

    # -- General operational flags
    Overwrite=`opts_GetOpt "${setflag}overwrite" $@`  # Clean prior run and starr fresh [yes/no]
    PRINTCOM=`opts_GetOpt "${setflag}printcom" $@`    # Option for printing the entire command
    Scheduler=`opts_GetOpt "${setflag}scheduler" $@`  # Specify the type of scheduler to use
    Bash=`opts_GetOpt "${setflag}bash" "$@"`          # Specify bash commands to run on the compute node
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

    # -- general_plot_bold_timeseries input flags
    QCPlotElements=`opts_GetOpt "${setflag}qcplotelements" $@`
    QCPlotImages=`opts_GetOpt "${setflag}qcplotimages" $@`
    QCPlotMasks=`opts_GetOpt "${setflag}qcplotmasks" $@`
    # -- Set flags for organize_dicom parameters
    Folder=`opts_GetOpt "${setflag}folder" $@`
    Clean=`opts_GetOpt "${setflag}clean" $@`
    Unzip=`opts_GetOpt "${setflag}unzip" $@`
    Gzip=`opts_GetOpt "${setflag}gzip" $@`
    VerboseRun=`opts_GetOpt "${setflag}verbose" $@`
    ParElements=`opts_GetOpt "${setflag}parelements" $@`
    # -- Path options for FreeSurfer or QuNex
    FreeSurferHome=`opts_GetOpt "${setflag}hcp_freesurfer_home" $@`
    QuNexVersion=`opts_GetOpt "${setflag}version" $@`
    # -- create_list input flags
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
    # -- data_sync input flags
    NetID=`opts_GetOpt "${setflag}netid" $@`
    HCPSessionsFolder=`opts_GetOpt "${setflag}clusterpath" $@`
    Direction=`opts_GetOpt "${setflag}dir" $@`
    ClusterName=`opts_GetOpt "${setflag}cluster" $@`
    # -- extract_roi input flags
    ROIFile=`opts_GetOpt "${setflag}roifile" $@`
    ROIFileSessionSpecific=`opts_GetOpt "${setflag}sessionroifile" $@`
    # -- compute_bold_fc input flags
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
    # -- bold_parcellation input flags
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
    # -- DWIlegacy input flags
    EchoSpacing=`opts_GetOpt "${setflag}echospacing" $@`
    PEdir=`opts_GetOpt "${setflag}PEdir" $@`
    TE=`opts_GetOpt "${setflag}TE" $@`
    UnwarpDir=`opts_GetOpt "${setflag}unwarpdir" $@`
    DiffDataSuffix=`opts_GetOpt "${setflag}diffdatasuffix" $@`
    Scanner=`opts_GetOpt "${setflag}scanner" $@`
    UseFieldmap=`opts_GetOpt "${setflag}usefieldmap" $@`
    # -- dwi_parcellate input flags
    MatrixVersion=`opts_GetOpt "${setflag}matrixversion" $@`
    ParcellationFile=`opts_GetOpt "${setflag}parcellationfile" $@`
    OutName=`opts_GetOpt "${setflag}outname" $@`
    WayTotal=`opts_GetOpt "${setflag}waytotal" $@`
    # -- dwi_seed_tractography_dense input flags
    SeedFile=`opts_GetOpt "${setflag}seedfile" $@`
    # -- dwi_eddy_qc input flags
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
    # -- dwi_fsl_bedpostx_gpu input flags
    Fibers=`opts_GetOpt "${setflag}fibers" $@`
    Weight=`opts_GetOpt "${setflag}weight" $@`
    Burnin=`opts_GetOpt "${setflag}burnin" $@`
    Jumps=`opts_GetOpt "${setflag}jumps" $@`
    Sample=`opts_GetOpt "${setflag}sample" $@`
    Model=`opts_GetOpt "${setflag}model" $@`
    Rician=`opts_GetOpt "${setflag}rician" $@`
    # -- dwi_probtrackx_dense_gpu input flags
    MatrixOne=`opts_GetOpt "${setflag}omatrix1" $@`
    MatrixThree=`opts_GetOpt "${setflag}omatrix3" $@`
    NsamplesMatrixOne=`opts_GetOpt "${setflag}nsamplesmatrix1" $@`
    NsamplesMatrixThree=`opts_GetOpt "${setflag}nsamplesmatrix3" $@`
    ScriptsFolder=`opts_GetOpt "${setflag}scriptsfolder" $@`
    # -- aws_hcp_sync input flags
    Awsuri=`opts_GetOpt "${setflag}awsuri" $@`
    # -- run_qc input flags
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

    # -- Get species flag for NHP pipelines
    Species=`opts_GetOpt "${setflag}species" $@`
fi

# ------------------------------------------------------------------------------
# -- subjects vs. sessions folder backwards compatibility settings
# ------------------------------------------------------------------------------

if [[ -z ${GmriCommandToRun} ]]; then
    if [[ ${SessionsFolderName} != "subjects" ]]; then
    if [[ -d "${StudyFolder}/subjects" ]] && [[ -d "${StudyFolder}/${SessionsFolderName}" ]]; then
        mageho "WARNING: You are attempting to execute a QuNex command using a conflicting QuNex file hierarchy:"
        echo ""
        echo "     Found: --> ${StudyFolder}/subjects"
        echo "     Found: --> ${StudyFolder}/${SessionsFolderName}"
        echo ""
        if [[ ${SessionsFolderName} != "sessions" ]]; then
            echo ""
            echo "     Note: Current version of QuNex supports the following default specification: "
            echo "            --> ${StudyFolder}/sessions"
            echo ""
        fi
        echo "     To avoid the possibility of a backwards incompatible or duplicate "
        echo "     QuNex runs please review the study directory structure and consider" 
        echo "     resolving the conflict such that a consistent folder specification is used. "
        echo ""
        echo "     QuNex will proceed but please consider renaming your directories per latest specs:"
        echo "          https://bitbucket.org/oriadev/qunex/wiki/Overview/DataHierarchy"
        echo ""
    fi
    if [[ -d "${StudyFolder}/subjects" ]] && [[ ! -d "${StudyFolder}/${SessionsFolderName}" ]]; then
        SessionsFolderBase=`base $SessionsFolder`
        if [[ ${SessionsFolderBase} == "subjects" ]]; then 
            SessionsFolderName="${SessionsFolderBase}"
            mageho "WARNING: You are attempting to execute QuNex command using an outdated QuNex file hierarchy:"
            echo ""
            echo "     Found: --> ${StudyFolder}/${SessionsFolderName}"
            echo ""
            echo "     Note: Current version of QuNex supports the following default specification: "
            echo "            --> ${StudyFolder}/sessions"
            echo ""
            echo "     QuNex will proceed but please consider renaming your directories per latest specs:"
            echo "          https://bitbucket.org/oriadev/qunex/wiki/Overview/DataHierarchy"
            echo ""
        else
            mageho "WARNING: You are attempting to execute QuNex command using a conflicting QuNex file hierarchy:"
            echo ""
            echo "     Found: --> ${StudyFolder}/subjects"
            echo "     Found: --> ${StudyFolder}/${SessionsFolderBase}"
            echo ""
            echo "     Note: Current version of QuNex supports the following default specification: "
            echo "            --> ${StudyFolder}/sessions"
            echo ""
            echo "     To avoid the possibility of a backwards incompatible or duplicate "
            echo "     QuNex runs please review the study directory structure and consider" 
            echo "     resolving the conflict such that a consistent folder specification is used. "
            echo ""
            echo "     QuNex will proceed but please consider renaming your directories per latest specs:"
            echo "          https://bitbucket.org/oriadev/qunex/wiki/Overview/DataHierarchy"
            echo ""
        fi
    fi
    fi

    if [[ ${SessionsFolderName} == "subjects" ]] && [[ -d "${StudyFolder}/${SessionsFolderName}" ]]; then
        mageho "WARNING: You are attempting to execute QuNex command using an outdated QuNex file hierarchy:"
        echo ""
        echo "       Found: --> ${StudyFolder}/${SessionsFolderName}"
        echo ""
        echo "     Note: Current version of QuNex supports the following default specification: "
        echo "       --> ${StudyFolder}/sessions"
        echo ""
        echo "       QuNex will proceed but please consider renaming your directories per latest specs:"
        echo "          https://bitbucket.org/oriadev/qunex/wiki/Overview/DataHierarchy"
        echo ""
    fi
fi


if [[ -d "${StudyFolder}/sessions" ]] && [[ ! -d "${StudyFolder}/subjects" ]] && [[ ! -d "${StudyFolder}/${SessionsFolderName}" ]]; then
    QuNexSessionsFolder="${StudyFolder}/sessions"
    SessionsFolderName="sessions"
fi
if [[ ! -d "${StudyFolder}/sessions" ]] && [[ ! -d "${StudyFolder}/subjects" ]] && [[ ! -d "${StudyFolder}/${SessionsFolderName}" ]]; then
    QuNexSessionsFolder="${StudyFolder}/sessions"
    SessionsFolderName="sessions"
fi


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-
# =-=-=-=-=-=-=-=-=-=-=-= Execute specific functions =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-

# ------------------------------------------------------------------------------
#  MATLAB execution and help
# ------------------------------------------------------------------------------

# -- Execute python qx_utilities
if [[ ${GmriCommandToRun} ]]; then
   bashExec
fi

if [[ ${CommandToRun} == "matlab_help" ]]; then
    ${CommandToRun}
fi

# ------------------------------------------------------------------------------
#  run_turnkey loop
# ------------------------------------------------------------------------------

if [[ ${CommandToRun} == "run_turnkey" ]]; then

    # -- Check for cases
    if [[ -z ${CASES} ]]; then
        if [[ ! -z ${XNAT_SESSION_LABELS} ]]; then
            CASES="$XNAT_SESSION_LABELS"
        fi
    fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    
    # -- Check for WORKDIR and StudyFolder for an XNAT run
    if [[ -z ${WORKDIR} ]]; then 
        if [[ ! -z ${XNAT_PROJECT_ID} ]]; then
            WORKDIR="/output"; echo "NOTE: Working directory where study is located is missing. Setting defaults: ${WORKDIR}"; echo ''
        fi
    fi
    if [[ -z ${WORKDIR} ]]; then reho "ERROR: Working folder for $CommandToRun missing."; exit 1; fi
    
    if [[ -z ${StudyFolder} ]]; then 
        if [[ ! -z ${XNAT_PROJECT_ID} ]]; then
            StudyFolder="${WORKDIR}/${XNAT_PROJECT_ID}"
        fi
    fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing."; exit 1; fi

   # -- Check if cluster options are set
   Cluster="$RunMethod"
   if [[ ${Cluster} == "2" ]]; then
           if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
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
   echo "Running $CommandToRun with the following parameters:"
   echo "--------------------------------------------------------------"
   echo ""
   echo " Turnkey steps: ${TURNKEY_STEPS} "
   echo " Turnkey arguments:"
   echo "${runTurnkeyArguments} " | sed -e $'s/ /\\\n/g'
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun}; done

fi

# ------------------------------------------------------------------------------
#  organize_dicom loop
# ------------------------------------------------------------------------------

if [[ ${CommandToRun} == "organize_dicom" ]]; then

    CommandToRun="organize_dicom"

    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then
        if [[ -z ${Folder} ]]; then
            reho "ERROR: Study folder missing and optional parameter --folder not specified."
            exit 1
        fi
    fi
    if [[ -z ${SessionsFolder} ]]; then
        if [[ -z ${Folder} ]]; then
            reho "ERROR: Sesssions folder missing and options parameter --folder not specified"
            exit 1
        fi
    fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    if [[ -z ${Overwrite} ]]; then Overwrite="no"; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
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
    echo "Running $CommandToRun with the following parameters:"
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
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  run_qc loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "qc_preproc" ] || [ "$CommandToRun" == "run_qc" ]; then
    if [ "$CommandToRun" == "qc_preproc" ]; then
       echo ""
       reho "---> NOTE: qc_preproc is deprecated. New function name --> ${CommandToRun}"
       echo ""
    fi
    CommandToRun="run_qc"
    
    # -- Check all the user-defined parameters:
    TimeStampRunQC=`date +%Y-%m-%d-%H-%M-%S`
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing."; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing."; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing."; exit 1; fi
    if [[ -z ${Modality} ]]; then reho "ERROR: Modality to perform QC on missing."; exit 1; fi
    if [[ -z ${runQC_Custom} ]]; then runQC_Custom="no"; fi
    if [[ ${runQC_Custom} == "yes" ]]; then scenetemplatefolder="${StudyFolder}/processing/scenes/QC/${Modality}"; fi
    if [[ -z ${OmitDefaults} ]]; then OmitDefaults="no"; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
        if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi
    
    # -- Perform some careful scene checks
    if [[ -z ${UserSceneFile} ]]; then
        if [ ! -z "$UserScenePath" ]; then 
            echo "---> Provided --userscenepath but --userscenefile not specified."; echo "";
            echo "     Check your inputs and re-run."; echo "";
            scenetemplatefolder="${TOOLS}/${QUNEXREPO}/qx_library/data/scenes/qc"
            geho "---> Reverting to QuNex defaults: ${scenetemplatefolder}"; echo ""
        fi
        if [ -z "$scenetemplatefolder" ]; then
            scenetemplatefolder="${TOOLS}/${QUNEXREPO}/qx_library/data/scenes/qc"
            echo "---> Template folder path value not explicitly specified."; echo ""
            geho "---> Using QuNex defaults: ${scenetemplatefolder}"; echo ""
        fi
        if ls ${scenetemplatefolder}/*${Modality}*.scene 1> /dev/null 2>&1; then 
            geho "---> Scene files found in:"; geho "`ls ${scenetemplatefolder}/*${Modality}*.scene`"; echo ""
        else 
            echo "---> Specified folder contains no scenes: ${scenetemplatefolder}"; echo ""
            scenetemplatefolder="${TOOLS}/${QUNEXREPO}/qx_library/data/scenes/qc"
            geho "---> Reverting to defaults: ${scenetemplatefolder} "; echo ""
        fi
    else
        if [[ -f ${UserSceneFile} ]]; then
            geho "---> User scene file found: ${UserSceneFile}"; echo ""
            UserScenePath=`echo ${UserSceneFile} | awk -F'/' '{print $1}'`
            UserSceneFile=`echo ${UserSceneFile} | awk -F'/' '{print $2}'`
            scenetemplatefolder=${UserScenePath}
        else
            if [ -z "$UserScenePath" ] && [ -z "$scenetemplatefolder" ]; then 
                reho "---> ERROR: Path for user scene file not specified."
                reho "     Specify --scenetemplatefolder or --userscenepath with correct path and re-run."; echo ""; exit 1
            fi
            if [ ! -z "$UserScenePath" ] && [ -z "$scenetemplatefolder" ]; then 
                scenetemplatefolder=${UserScenePath}
            fi
            if ls ${scenetemplatefolder}/${UserSceneFile} 1> /dev/null 2>&1; then 
                geho "---> User specified scene files found in: ${scenetemplatefolder}/${UserSceneFile} "; echo ""
            else 
                reho "---> ERROR: User specified scene ${scenetemplatefolder}/${UserSceneFile} not found." 
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
            echo "WARNING: BOLD input list not specified. Relying on session_hcp.txt individual information files."
            BOLDS="session_hcp.txt"
            echo ""
        fi
        if [ -z "$BOLDPrefix" ]; then BOLDPrefix=""; echo "Input BOLD Prefix not specified. Assuming no BOLD name prefix."; fi
        if [ -z "$BOLDSuffix" ]; then BOLDSuffix=""; echo "Processed BOLD Suffix not specified. Assuming no BOLD output suffix."; fi
    fi
    
    # -- General modality settings:
    if [ "$Modality" = "general" ] || [ "$Modality" = "General" ] || [ "$Modality" = "GENERAL" ] ; then
        if [ -z "$GeneralSceneDataFile" ]; then reho "ERROR: Data input not specified"; echo ""; exit 1; fi
        if [ -z "$GeneralSceneDataPath" ]; then reho "ERROR: Data input path not specified"; echo ""; exit 1; fi
    fi
    
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
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
                reho "ERROR: Requested BOLD modality with a batch file. Batch file not found."
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
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  dwi_eddy_qc loop - eddyqc - uses EDDY QC by Matteo Bastiani, FMRIB
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "dwi_eddy_qc" ]; then
    #unset EddyPath
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
    if [ -z "$Report" ]; then reho "ERROR: Report type missing"; exit 1; fi
    # -- Perform checks for individual run
    if [ "$Report" == "individual" ]; then
        if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
        if [ -z "$EddyBase" ]; then reho "Eddy base input name missing"; exit 1; fi
        if [ -z "$BvalsFile" ]; then reho "BVALS file missing"; exit 1; fi
        if [ -z "$EddyIdx" ]; then reho "Eddy index missing"; exit 1; fi
        if [ -z "$EddyParams" ]; then reho "Eddy parameters missing"; exit 1; fi
        if [ -z "$Mask" ]; then reho "ERROR: Mask missing"; exit 1; fi
        if [ -z "$BvecsFile" ]; then BvecsFile=""; fi
    fi
    # -- Perform checks for group run
    if [ "$Report" == "group" ]; then
        if [ -z "$List" ]; then reho "ERROR: List of sessions missing"; exit 1; fi
        if [ -z "$Update" ]; then Update="false"; fi
        if [ -z "$GroupVar" ]; then GroupVar=""; fi
    fi
    # -- Check if cluster options are set
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
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
            echo "Running $CommandToRun with the following parameters:"
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
            echo ""
            # -- Execute function
            ${CommandToRun} ${CASE}
        done
    fi
    # -- Check if group call specified
    if [ ${Report} == "group" ]; then
        # -- Report group parameters
        echo ""
        echo "Running $CommandToRun with the following parameters:"
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
        echo ""
        # ---> Add function all here
    fi
fi

# ------------------------------------------------------------------------------
#  map_hcp_files loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "map_hcp_files" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo "--------------------------------------------------------------"
    echo "Study Folder: ${StudyFolder}"
    echo "Sessions Folder: ${SessionsFolder}"
    echo "Sessions: ${CASES}"
    echo "Study Log Folder: ${LogFolder}"
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
#  data_sync loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "data_sync" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: Specific sessions not provided"; exit 1; fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  anat_parcellate loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "anat_parcellate" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    if [ -z "$InputDataType" ]; then reho "ERROR: Input data type value missing"; exit 1; fi
    if [[ -z ${OutName} ]]; then reho "ERROR: Output file name value missing"; exit 1; fi
    if [ -z "$ParcellationFile" ]; then reho "ERROR: File to use for parcellation missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Check optional parameters if not specified
    if [ -z "$ExtractData" ]; then ExtractData="no"; fi
    if [ -z "$Overwrite" ]; then Overwrite="no"; fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
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
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  dwi_fsl_dtifit loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "dwi_fsl_dtifit" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
        if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Scheduler Name and Options: ${Scheduler}"
    echo "   Overwrite prior run: ${Overwrite}"
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  dwi_fsl_bedpostx_gpu loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "dwi_fsl_bedpostx_gpu" ]; then

    # -- Check required parameters
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study Folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    Cluster=${RunMethod}

    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done

fi

# ------------------------------------------------------------------------------
#  Diffusion legacy processing loop (dwi_legacy)
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "dwi_legacy" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [ -z "$Scanner" ]; then reho "ERROR: Scanner manufacturer missing"; exit 1; fi
    if [ -z "$UseFieldmap" ]; then reho "ERROR: UseFieldmap yes/no specification missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    if [ -z "$DiffDataSuffix" ]; then reho "ERROR: Diffusion Data Suffix Name missing"; exit 1; fi
    if [ ${UseFieldmap} == "yes" ]; then
        if [ -z "$TE" ]; then reho "ERROR: TE value for Fieldmap missing"; exit 1; fi
    elif [ ${UseFieldmap} == "no" ]; then
        echo "NOTE: Processing without FieldMap (TE option not needed)"
    fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
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
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  anat_parcellate loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "anat_parcellate" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    if [ -z "$InputDataType" ]; then reho "ERROR: Input data type value missing"; exit 1; fi
    if [[ -z ${OutName} ]]; then reho "ERROR: Output file name value missing"; exit 1; fi
    if [ -z "$ParcellationFile" ]; then reho "ERROR: File to use for parcellation missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Check optional parameters if not specified
    if [ -z "$ExtractData" ]; then ExtractData="no"; fi
    if [ -z "$Overwrite" ]; then Overwrite="no"; fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
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
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  bold_compute_fc loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "compute_bold_fc" ] || [ "$CommandToRun" == "bold_compute_fc" ]; then
    CommandToRun="compute_bold_fc"

    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${Calculation} ]]; then reho "ERROR: Type of calculation to run (gbc or seed) missing"; exit 1; fi
    if [[ -z ${RunType} ]] && [[ ${Calculation} != "dense" ]]; then reho "ERROR: Type of run (group or individual) missing"; exit 1; fi
    if [[ ${RunType} == "list" ]]; then
        if [ -z "$FileList" ]; then reho "ERROR: Group file list missing"; exit 1; fi
    fi
    if [[ ${RunType} == "individual" ]] || [[ ${RunType} == "group" ]]; then
        if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
        if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
        if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
        if [ -z "$InputFiles" ]; then reho "ERROR: Input file(s) value missing"; exit 1; fi
        if [[ -z ${OutName} ]]; then reho "ERROR: Output file name value missing"; exit 1; fi
        if [[ ${RunType} == "individual" ]]; then
            if [ -z "$InputPath" ]; then echo ""; echo "WARNING: Input path value missing. Assuming individual folder structure for output"; fi
            if [ -z "$OutPathFC" ]; then echo ""; echo "WARNING: Output path value missing. Assuming individual folder structure for output"; fi
        fi
        if [[ ${RunType} == "group" ]]; then
            if [ -z "$OutPathFC" ]; then reho "ERROR: Output path value missing and is needed for a group run."; exit 1; fi
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
        if [ -z "$ROIInfo" ]; then reho "ERROR: ROI seed file not specified"; exit 1; fi
        if [ -z "$FCCommand" ]; then FCCommand=""; fi
        if [ -z "$Method" ]; then Method="mean"; fi
    fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Check optional parameters if not specified
    if [ -z "$IgnoreFrames" ]; then IgnoreFrames=""; fi
    if [ -z "$MaskFrames" ]; then MaskFrames=""; fi
    if [ -z "$Covariance" ]; then Covariance=""; fi
    if [ -z "$ExtractData" ]; then ExtractData="no"; fi
    
    if [[ ${Calculation} == "dense" ]]; then 
        RunType="individual"; 
        if [ -z ${MemLimit} ]; then MemLimit="4"; echo "WARNING: MemLimit value missing. Setting to $MemLimit"; fi
    fi

    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
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
#  bold_parcellate loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "bold_parcellation" ] || [ "$CommandToRun" == "bold_parcellate" ]; then
    CommandToRun="bold_parcellation"

    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [ -z "$InputPath" ]; then reho "ERROR: Input path value missing"; exit 1; fi
    if [ -z "$InputDataType" ]; then reho "ERROR: Input data type value missing"; exit 1; fi
    if [ -z "$OutPath" ]; then reho "ERROR: Output path value missing"; exit 1; fi
    if [[ -z ${OutName} ]]; then reho "ERROR: Output file name value missing"; exit 1; fi
    if [ -z "$ParcellationFile" ]; then reho "ERROR: File to use for parcellation missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Check optional parameters if not specified
    if [ -z ${UseWeights} ]; then
        UseWeights="no"
        WeightsFile="no"
        echo "NOTE: Weights file not used."
    fi
    if [ -z ${WeightsFile} ]; then
        UseWeights="no"
        WeightsFile="no"
        echo "NOTE: Weights file not used."
    fi
    if [ -z "$ComputePConn" ]; then ComputePConn="no"; fi
    if [ -z "$WeightsFile" ]; then WeightsFile="no"; fi
    if [ -z "$ExtractData" ]; then ExtractData="no"; fi
    if [[ -z ${SingleInputFile} ]]; then SingleInputFile="";
        if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
        if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
        if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
        if [ -z "$InputFile" ]; then reho "ERROR: Input file value missing"; exit 1; fi
    fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
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
#  dwi_parcellate loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "dwi_parcellate" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    if [ -z "$MatrixVersion" ]; then reho "ERROR: Matrix version value missing"; exit 1; fi
    if [ -z "$ParcellationFile" ]; then reho "ERROR: File to use for parcellation missing"; exit 1; fi
    if [[ -z ${OutName} ]]; then reho "ERROR: Name of output pconn file missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi
    if [ -z "$WayTotal" ]; then WayTotal="no"; echo "NOTE: --waytotal normalized data not specified. Assuming default [no]"; fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
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
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  extract_roi loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "extract_roi" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [ -z "$OutPath" ]; then reho "ERROR: Output path value missing"; exit 1; fi
    if [[ -z ${OutName} ]]; then reho "ERROR: Output file name value missing"; exit 1; fi
    if [ -z "$ROIFile" ]; then reho "ERROR: File to use for ROI extraction missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Check optional parameters if not specified
    if [ -z "$ROIFileSessionSpecific" ]; then ROIFileSessionSpecific="no"; fi
    if [ -z "$Overwrite" ]; then Overwrite="no"; fi
    if [[ -z ${SingleInputFile} ]]; then SingleInputFile="";
        if [ -z "$InputFile" ]; then reho "ERROR: Input file path value missing"; exit 1; fi
        if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
        if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
        if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo "--------------------------------------------------------------"
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
#  dwi_seed_tractography_dense loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "dwi_seed_tractography_dense" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    if [ -z "$MatrixVersion" ]; then reho "ERROR: Matrix version value missing"; exit 1; fi
    if [ -z "$SeedFile" ]; then reho "ERROR: File to use for seed reduction missing"; exit 1; fi
    if [[ -z ${OutName} ]]; then reho "ERROR: Name of output pconn file missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
            if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi
    if [ -z "$WayTotal" ]; then WayTotal="no"; echo "NOTE: --waytotal normalized data not specified. Assuming default [no]"; fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
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
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  auto_ptx loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "auto_ptx" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
        if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi
    if [[ -z ${BedPostXFolder} ]]; then BedPostXFolder=${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX; fi
    
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   BedpostX Folder: ${BedPostXFolder} "
    echo ""
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  dwi_pre_tractography loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "dwi_pre_tractography" ]; then
    # -- Check all the user-defined parameters:
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
        if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi
    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo ""
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

# ------------------------------------------------------------------------------
#  dwi_probtrackx_dense_gpu loop
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "dwi_probtrackx_dense_gpu" ]; then
    # Check all the user-defined parameters: 1.QUEUE, 2. Scheduler, 3. Matrix1, 4. Matrix2
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    if [ -z "$MatrixOne" ] && [ -z "$MatrixThree" ]; then reho "ERROR: Matrix option missing. You need to specify at least one. [e.g. --omatrix1='yes' and/or --omatrix2='yes']"; exit 1; fi
    if [ "$MatrixOne" == "yes" ]; then
        if [ -z "$NsamplesMatrixOne" ]; then NsamplesMatrixOne=10000; fi
    fi
    if [ "$MatrixThree" == "yes" ]; then
        if [ -z "$NsamplesMatrixThree" ]; then NsamplesMatrixThree=3000; fi
    fi
    Cluster="$RunMethod"
    if [[ ${Cluster} == "2" ]]; then
        if [[ -z ${Scheduler} ]]; then reho "ERROR: Scheduler specification and options missing."; exit 1; fi
    fi

    # -- Optional parameters
    if [ -z ${ScriptsFolder} ]; then ScriptsFolder="${HCPPIPEDIR_dMRITractFull}/tractography_gpu_scripts"; fi
    minimumfilesize="100000000"

    # -- In and out folders for reporting
    if [[ -z ${OutFolder} ]]; then
        OutFolderReport="${SessionsFolder}/<session>/hcp/<session>/MNINonLinear/Results/Tractography";
    else
        OutFolderReport=${OutFolder}
    fi

    # -- Report parameters
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Scheduler: ${Scheduler}"
    echo "   probtraxkX GPU scripts Folder: ${ScriptsFolder}"
    echo "   Compute Matrix1: ${MatrixOne}"
    echo "   Compute Matrix3: ${MatrixThree}"
    echo "   Number of samples for Matrix1: ${NsamplesMatrixOne}"
    echo "   Number of samples for Matrix3: ${NsamplesMatrixThree}"
    echo "   Overwrite prior run: ${Overwrite}"
    echo ""

    # -- execute
    ${CommandToRun}
fi

# ------------------------------------------------------------------------------
#  aws_hcp_sync - AWS S3 Sync command wrapper
# ------------------------------------------------------------------------------

if [ "$CommandToRun" == "aws_hcp_sync" ]; then
    # Check all the user-defined parameters: 1. Modality, 2. Awsuri, 3. RunMethod
    if [[ -z ${CommandToRun} ]]; then reho "ERROR: Explicitly specify name of command in flag or use function name as first argument (e.g. qunex<command_name> followed by flags) to run missing"; exit 1; fi
    if [[ -z ${StudyFolder} ]]; then reho "ERROR: Study folder missing"; exit 1; fi
    if [[ -z ${SessionsFolder} ]]; then reho "ERROR: Sessions folder missing"; exit 1; fi
    if [[ -z ${CASES} ]]; then reho "ERROR: List of sessions missing"; exit 1; fi
    if [[ -z ${Modality} ]]; then reho "ERROR: Modality option [e.g. MEG, MNINonLinear, T1w] missing"; exit 1; fi
    if [ -z "$Awsuri" ]; then reho "ERROR: AWS URI option [e.g. /hcp-openaccess/HCP_900] missing"; exit 1; fi
    echo ""
    echo "Running $CommandToRun with the following parameters:"
    echo "--------------------------------------------------------------"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   Run Method: ${RunMethod}"
    echo "   Modality: ${Modality}"
    echo "   AWS URI Path: ${Awsuri}"
    echo ""
    # -- Loop through all the cases
    for CASE in ${CASES}; do ${CommandToRun} ${CASE}; done
fi

