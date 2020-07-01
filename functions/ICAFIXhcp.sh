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
#  FIXICA.sh
#
# ## LICENSE
#
# * The FIXICA.sh = the "Software"
# * This Software conforms to the license outlined in the Qu|Nex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ## TODO
#
# --> Finish code
#
# ## DESCRIPTION 
#   
# This script, ICAFIXHCP.sh, implements FIXICA on HCP Processed BOLD data
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * Connectome Workbench (v1.0 or above)
# * HCP Pipelines
# * FSL
# * FIX 1.067
# * MATLAB with official toolboxes:
#      Statistics
#      Signal Processing
# * R free statistics software (version >=3.3.0), with the following packages:
#     'kernlab' version 0.9.24
#     'ROCR' version 1.0.7
#     'class' version 7.3.14
#     'party' version 1.0.25
#     'e1071' version 1.6.7
#     'randomForest' version 4.6.12
# * CIFTIMatlabReaderWriter (https://git.fmrib.ox.ac.uk/saad/ActPred/tree/604df783e7ac39d9be9b319057242170675cec90/extras/CIFTIMatlabReaderWriter)
# * MATLAB GIFTI Library (https://www.artefact.tk/software/matlab/gifti/)
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./ICAFIXHCP.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are BOLD data from previous processing
# * These data are stored in: "$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/ 
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# -- Setup color outputs
# ------------------------------------------------------------------------------

reho() {
    echo -e "\033[31m $1 \033[0m"
}

geho() {
    echo -e "\033[32m $1 \033[0m"
}

usage() {
     echo ""
     echo "-- DESCRIPTION:"
     echo ""
     echo "This function implements FIX ICA and Post FIX on the BOLD dense CIFTI files."
     echo ""
     geho " PREREQUISITE INSTALLED SOFTWARE (Configured automatically via Qu|Nex environment):"
     geho "    ~ Note: If the dependencies below have changed please notify Qu|Nex developers to ensure updates are reflected."
     geho ""
     geho "    --> Connectome Workbench (v1.0 or above)"
     geho "    --> HCP Pipelines"
     geho "    --> FSL 5.0.9 or greater"
     geho "    --> FIX 1.067"
     geho "    --> MATLAB with official toolboxes:"
     geho "         Statistics "
     geho "         Signal Processing "
     geho "    --> R free statistics software (version >=3.3.0), with the following packages: "
     geho "        'kernlab' version 0.9.24 "
     geho "        'ROCR' version 1.0.7 "
     geho "        'class' version 7.3.14 "
     geho "        'party' version 1.0.25 "
     geho "        'e1071' version 1.6.7 "
     geho "        'randomForest' version 4.6.12 "
     geho "    --> CIFTIMatlabReaderWriter (https://git.fmrib.ox.ac.uk/saad/ActPred/tree/604df783e7ac39d9be9b319057242170675cec90/extras/CIFTIMatlabReaderWriter) "
     geho "    --> MATLAB GIFTI Library (https://www.artefact.tk/software/matlab/gifti/) "
     echo ""
     echo ""
     echo "-- REQUIRED PARMETERS:"
     echo ""
     echo "     --sessionsfolder=<folder_with_sessions>           Path to study folder that contains sessions"
     echo "     --sessions=<session_ids>                          List of sessions to run"
     echo "     --bolds=<bolds_to_compute_fixica_and_postfix>     Specify the name of the file you want to use for parcellation (e.g. bold1_Atlas_MSMAll_hp2000_clean)"
     echo ""
     echo "-- OPTIONAL ICA FIX PARMETERS:"
     echo ""
     echo "     --hpfilter=<specify_filter>                       Filter for FIX ICA. Default [2000]"
     echo "     --movcorr=<movement_correction>                   Do motion correction for FIX ICA. Default [TRUE]"
     echo ""
     echo "-- OPTIONAL PARMETERS:"
     echo ""
     echo "     --overwrite=<clean_prior_run>                     Delete prior run: yes / no. Default [no]"
     echo "     --icafixfunction=<select_which_function_to_run>   Specify which call to run: "
     echo "                                                       1=FIXICA, 2=PostFIX; all=Run all Sequentially. Default [3]"
     echo ""
     echo "-- EXAMPLES:"
     echo ""
     echo "   --> Run directly via ${TOOLS}/${QUNEXREPO}/connector/functions/ICAFIXhcp.sh --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
     echo ""
     reho "           * NOTE: --scheduler is not available via direct script call."
     echo ""
     echo "   --> Run via qunex ICAFIXhcp --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
     echo ""
     geho "           * NOTE: scheduler is available via qunex call:"
     echo "                   --scheduler=<name_of_cluster_scheduler_and_options>  A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
     echo ""
     echo "           * For SLURM scheduler the string would look like this via the qunex call: "
     echo "                   --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
     echo ""     
     echo ""
     echo "  ${TOOLS}/${QUNEXREPO}/connector/functions/ICAFIXhcp.sh \ "
     echo "    --sessionsfolder='<folder_with_sessions>' \ "
     echo "    --sessions='<session_ids>' \ "
     echo "    --bolds='<bolds_to_compute_fixica_and_postfix>' \ "
     echo "    --overwrite='<clean_prior_run>' \ "
     echo "    --icafixfunction='<select_which_function_to_run>' \ "
     echo ""
     exit 0
}

# ------------------------------------------------------------------------------------------------------
# ----------------------------------------- FIX ICA CODE -----------------------------------------------
# ------------------------------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]]; then
    usage
fi

# -- Get the command line options for this script
get_options() {

# -- Set general options functions
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

# -- Initialize global output variables
unset SessionsFolder
unset Sessions
unset BOLDS
unset Overwrite
unset HPFilter
unset MovCorr
unset ICAFIXFunction

# -- Parse arguments
SessionsFolder=`opts_GetOpt "--sessionsfolder" $@`
CASES=`opts_GetOpt "--sessions" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
Overwrite=`opts_GetOpt "--overwrite" $@`
ICAFIXFunction=`opts_GetOpt "--icafixfunction" $@`
HPFilter=`opts_GetOpt "--hpfilter" $@`
MovCorr=`opts_GetOpt "--movcorr" $@`

# -- Parse BOLD arguments
BOLDS=`opts_GetOpt "--bolds" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
if [ -z "${BOLDS}" ]; then
    BOLDS=`opts_GetOpt "--boldruns" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
fi
if [ -z "${BOLDS}" ]; then
    BOLDS=`opts_GetOpt "--bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
fi
BOLDRUNS="${BOLDS}"
BOLDDATA="${BOLDS}"

if [ -z ${SessionsFolder} ]; then
    usage
    reho "ERROR: <folder_with_sessions> not specified"
    echo ""
    exit 1
fi
if [ -z ${BOLDS} ]; then
    usage
    reho "ERROR: <bolds_to_compute_fixica_and_postfix> not specified"
    exit 1
fi

if [ -z ${CASES} ]; then
    usage
    reho "ERROR: <session_ids> not specified"
    exit 1
fi

if [ -z ${ICAFIXFunction} ]; then ICAFIXFunction="all"; fi
if [ -z ${Overwrite} ]; then Overwrite="no"; fi
if [ -z ${HPFilter} ]; then Overwrite="2000"; fi
if [ -z ${MovCorr} ]; then Overwrite="TRUE"; fi

# -- Set StudyFolder
cd $SessionsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null

scriptName=$(basename ${0})
# -- Report options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   SessionsFolder: ${SessionsFolder}"
echo "   Sessions: ${CASES}"
echo "   BOLDs to work on: ${BOLDS}"
echo "   Function to run: ${ICAFIXFunction}"
echo "   Filter: ${HPFilter}"
echo "   Movement correction requested: ${MovCorr}"
echo "   Overwrite prior run: ${Overwrite}"
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""

}

# ------------------------------------------------------------------------------------------------------
#  linkMovement - Sets hard links for BOLDs into Parcellated folder for FIXICA use
# ------------------------------------------------------------------------------------------------------

main() {

get_options "$@"

linkMovement() {
for BOLD in $BOLDS; do
    echo "Linking scrubbing data - BOLD $BOLD for $CASE..."
    ln -f ${SessionsFolder}/${CASE}/images/functional/movement/bold"$BOLD".use ${SessionsFolder}/../Parcellated/BOLD/${CASE}_bold"$BOLD".use
    ln -f ${SessionsFolder}/${CASE}/images/functional/movement/boldFIXICA"$BOLD".use ${SessionsFolder}/../Parcellated/BOLD/${CASE}_boldFIXICA"$BOLD".use
done
}

# ------------------------------------------------------------------------------
# ICA Decomposition & FIX (ICAFIX)
# ------------------------------------------------------------------------------
icafix() {

# -- Set R dependencies and create a file .Renviron in your home directory
echo ""
geho " ===> Setting local R environment for ICA FIX ..."
echo "" 
mkdir ~/R_libs &> /dev/null
echo "export R_LIBS=~/R_libs/" > ~/.Renviron
Rscript ${FIXDIR_DEPEND}/FIXICA_dependencies.R
echo ""
geho " ===> RUNNING: ICA FIX ..."
echo ""
ICAFIXFail=""
# -- Sessions loop
for CASE in $CASES; do
        FailedBOLDS=""
        # -- BOLD loop
        for BOLD in ${BOLDS}; do
            TimeLog=`date '+%Y-%m-%d-%H-%M-%S'`
            OutputLogFIX="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/fixica_${CASE}_bold${BOLD}_${TimeLog}.log"
            # -- Echo ICA FIX run for each BOLD
            echo "" 2>&1 | tee -a ${OutputLogFIX}
            geho "   --- ICAFIX for session $CASE and BOLD run $BOLD..." 2>&1 | tee -a ${OutputLogFIX}
            echo "" 2>&1 | tee -a ${OutputLogFIX}
            CheckBOLD="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}_Atlas_hp2000_clean.dtseries.nii"
            # -- Overwrite existing run
            if [[ ${Overwrite} == "yes" ]]; then
                reho "   --- Overwrite requested. Deleting existing ICA FIX run: ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}"; echo ""
                rm -r ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}*_hp2000* &> /dev/null
            fi
            # -- Check if run completed
            if [[ -f ${CheckBOLD} ]]; then
                echo ""; geho "  --- ICAFIX $CheckBOLD is done. Skipping."; echo ""
            else
                # -- Define input parameters
                if [[ -z ${HPFilter} ]]; then HPFilter="2000"; fi
                if [[ -z ${MovCorr} ]]; then MovCorr="TRUE"; fi
                # -- Define command
                RunCommand="${HCPPIPEDIR}/ICAFIX/hcp_fix ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}.nii.gz ${HPFilter} ${MovCorr} "
                # -- Echo the command
                echo "Running the following ICA FIX command: "; echo ""
                echo "---------------------------"
                echo ""
                echo "   ${RunCommand}"
                echo ""
                echo "---------------------------"; echo ""
                # -- Eval the command
                eval "${RunCommand}" 2>&1 | tee -a ${OutputLogFIX}
            fi
            if [[ -f ${CheckBOLD} ]]; then
                echo ""; geho "  --- ICAFIX $CheckBOLD ran OK."; echo ""
            else
                ICAFIXFail="True"
                FailedBOLDS="${FailedBOLDS}\n${CheckBOLD}"
            fi
        done
        # -- Report checks
        if [[ ${ICAFIXFail} == "True" ]]; then
            echo "" 2>&1 | tee -a ${OutputLogFIX}
            geho " ===> FINISHED: ICAFIX for ${CASE} and ${BOLDS}..." 2>&1 | tee -a ${OutputLogFIX}
            echo "" 2>&1 | tee -a ${OutputLogFIX}
        else
            echo "" 2>&1 | tee -a ${OutputLogFIX}
            reho " ===> ERROR: ICAFIX failed for ${CASE} "        2>&1 | tee -a ${OutputLogFIX}
            echo ""                                               2>&1 | tee -a ${OutputLogFIX}
            reho "  -- ICA FIX failed for the following BOLD runs: " 2>&1 | tee -a ${OutputLogFIX}
            reho "-----------------------"                        2>&1 | tee -a ${OutputLogFIX}
            echo ""                                               2>&1 | tee -a ${OutputLogFIX}
            reho "    ${FailedBOLDS}"                             2>&1 | tee -a ${OutputLogFIX} 
            echo ""                                               2>&1 | tee -a ${OutputLogFIX}
            reho "-----------------------"                        2>&1 | tee -a ${OutputLogFIX}
            echo "" 2>&1 | tee -a ${OutputLogFIX}
        fi
done
}

# ------------------------------------------------------------------------------
# POSTFIX
# ------------------------------------------------------------------------------

postfix() {

echo ""
geho " ===> RUNNING: Post FIX ..."
echo ""

# -- Define input parameters
if [[ -z ${HPFilter} ]]; then HPFilter="2000"; fi
ReUseHighPass="NO" # Use YES if using multi-run ICA-FIX, otherwise use NO
DualScene="${HCPPIPEDIR}/PostFix/PostFixScenes/ICA_Classification_DualScreenTemplate.scene"
SingleScene="${HCPPIPEDIR}/PostFix/PostFixScenes/ICA_Classification_SingleScreenTemplate.scene"
MatlabMode="1" #Mode=0 compiled Matlab, Mode=1 interpreted Matlab

# -- Sessions loop
for CASE in $CASES ; do
    # -- BOLD loop
    for BOLD in ${BOLDS} ; do
        TimeLog=`date '+%Y-%m-%d-%H-%M-%S'`
        OutputLogPostFIX="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/postfix_${CASE}_bold${BOLD}_${TimeLog}.log"
        # -- Echo POSTFIX run for each BOLD
        echo "" 2>&1 | tee -a ${OutputLogPostFIX}
        geho "  --- Post FIX for $CASE and $BOLD..." 2>&1 | tee -a ${OutputLogPostFIX}
        echo "" 2>&1 | tee -a ${OutputLogPostFIX}
        # -- Define the command
        RunCommand="${HCPPIPEDIR}/PostFix/PostFix.sh --study-folder=${StudyFolder} --session=${CASE} --fmri-name=${BOLD} --high-pass=${HPFilter} --template-scene-dual-screen=${DualScene} --template-scene-single-screen=${SingleScene} --reuse-high-pass=${ReUseHighPass} --matlab-run-mode=${MatlabMode} "
        # -- Echo the command
        echo "Running the following POSTFIX command: "; echo ""
        echo "---------------------------"
        echo ""
        echo "   ${RunCommand}"
        echo ""
        echo "---------------------------"; echo ""
        # -- Eval the command
        eval "${RunCommand}" 2>&1 | tee -a ${OutputLogPostFIX}
        echo "" 2>&1 | tee -a ${OutputLogPostFIX}
    done
done

echo "" 2>&1 | tee -a ${OutputLogPostFIX}
geho " ===> FINISHED: Post FIX ..." 2>&1 | tee -a ${OutputLogPostFIX}
echo "" 2>&1 | tee -a ${OutputLogPostFIX}

}

# 
# ------------------------------------------------------------------------------------------------------
#  BOLDHardLinkFIXICA - Generate links for FIX ICA cleaned BOLDs for functional connectivity (dofcMRI)
# ------------------------------------------------------------------------------------------------------

# BOLDHardLinkFIXICA() {
# BOLDCount=0
# for BOLD in $BOLDS
#     do
#         BOLDCount=$((BOLDCount+1))
#         echo "Setting up hard links following FIX ICA for BOLD# $BOLD for $CASE... "
#         # -- Setup folder strucrture if missing
#         mkdir ${SessionsFolder}/${CASE}/images    &> /dev/null
#         mkdir ${SessionsFolder}/${CASE}/images/functional        &> /dev/null
#         mkdir ${SessionsFolder}/${CASE}/images/functional/movement    &> /dev/null
#         # -- Setup hard links for images
#         rm ${SessionsFolder}/${CASE}/images/functional/boldFIXICA"$BOLD".dtseries.nii     &> /dev/null
#         rm ${SessionsFolder}/${CASE}/images/functional/boldFIXICA"$BOLD".nii.gz     &> /dev/null
#         ln -f ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas_hp2000_clean.dtseries.nii ${SessionsFolder}/${CASE}/images/functional/boldFIXICA"$BOLD".dtseries.nii
#         ln -f ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD"_hp2000_clean.nii.gz ${SessionsFolder}/${CASE}/images/functional/boldFIXICA"$BOLD".nii.gz
#         ln -f ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD"_Atlas.dtseries.nii ${SessionsFolder}/${CASE}/images/functional/bold"$BOLD".dtseries.nii
#         ln -f ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/"$BOLD".nii.gz ${SessionsFolder}/${CASE}/images/functional/bold"$BOLD".nii.gz
#         #rm ${SessionsFolder}/${CASE}/images/functional/boldFIXICArfMRI_REST*     &> /dev/null
#         #rm ${SessionsFolder}/${CASE}/images/functional/boldrfMRI_REST*     &> /dev/null
#         echo "Setting up hard links for movement data for BOLD# $BOLD for $CASE... "
#         # -- Clean up movement regressor file to match dofcMRIp convention and copy to movement directory
#         export PATH=/usr/local/opt/gnu-sed/libexec/gnubin:$PATH     &> /dev/null
#         rm ${SessionsFolder}/${CASE}/images/functional/movement/boldFIXICA"$BOLD"_mov.dat     &> /dev/null
#         rm ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit*     &> /dev/null
#         cp ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors.txt ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit.txt
#         sed -i.bak -E 's/.{67}$//' ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit.txt
#         nl ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit.txt > ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit_fin.txt
#         sed -i.bak '1i\#frame     dx(mm)     dy(mm)     dz(mm)     X(deg)     Y(deg)     Z(deg)' ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"//Movement_Regressors_edit_fin.txt
#         cp ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit_fin.txt ${SessionsFolder}/${CASE}/images/functional/movement/boldFIXICA"$BOLD"_mov.dat
#         rm ${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/"$BOLD"/Movement_Regressors_edit*     &> /dev/null
# done
# }

# ------------------------------------------------------------------------------------------------------
#  FIXICAInsertMean - Re-insert means into FIX ICA cleaned BOLDs for connectivity preprocessing (dofcMRI)
# ------------------------------------------------------------------------------------------------------
# 
# FIXICAInsertMean() {
# for BOLD in $BOLDS; do
#     cd ${SessionsFolder}/${CASE}/images/functional/
#     # -- First check if the boldFIXICA file has the mean inserted
#     3dBrickStat -mean -non-zero boldFIXICA"$BOLD".nii.gz[1] >> boldFIXICA"$BOLD"_mean.txt
#     ImgMean=`cat boldFIXICA"$BOLD"_mean.txt`
#     if [ $(echo " $ImgMean > 1000" | bc) -eq 1 ]; then
#     echo "1st frame mean=$ImgMean Mean inserted OK for session $CASE and bold# $BOLD. Skipping to next..."
#         else
#         # -- Next check if the boldFIXICA file has the mean inserted twice by accident
#         if [ $(echo " $ImgMean > 15000" | bc) -eq 1 ]; then
#         echo "1st frame mean=$ImgMean ERROR: Mean has been inserted twice for $CASE and $BOLD."
#             else
#             # -- Command that inserts mean image back to the boldFIXICA file using g_InsertMean matlab function
#             echo "Re-inserting mean image on the mapped $BOLD data for $CASE... "
#             ${QUNEXMCOMMAND} "g_InsertMean(['bold' num2str($BOLD) '.dtseries.nii'], ['boldFIXICA' num2str($BOLD) '.dtseries.nii']),g_InsertMean(['bold' num2str($BOLD) '.nii.gz'], ['boldFIXICA' num2str($BOLD) '.nii.gz']),quit()"
#         fi
#     fi
#     rm boldFIXICA"$BOLD"_mean.txt &> /dev/null
# done
# }

# ------------------------------------------------------------------------------------------------------
#  FIXICARemoveMean - Remove means from FIX ICA cleaned BOLDs for functional connectivity analysis
# ------------------------------------------------------------------------------------------------------

# FIXICARemoveMean() {
# for BOLD in $BOLDS; do
#     cd ${SessionsFolder}/${CASE}/images/functional/
#     # First check if the boldFIXICA file has the mean inserted
#     #3dBrickStat -mean -non-zero boldFIXICA"$BOLD".nii.gz[1] >> boldFIXICA"$BOLD"_mean.txt
#     #ImgMean=`cat boldFIXICA"$BOLD"_mean.txt`
#     #if [ $(echo " $ImgMean < 1000" | bc) -eq 1 ]; then
#     #echo "1st frame mean=$ImgMean Mean removed OK for session $CASE and bold# $BOLD. Skipping to next..."
#     #    else
#         # Next check if the boldFIXICA file has the mean inserted twice by accident
#     #    if [ $(echo " $ImgMean > 15000" | bc) -eq 1 ]; then
#     #    echo "1st frame mean=$ImgMean ERROR: Mean has been inserted twice for $CASE and $BOLD."
#     #        else
#             # Command that inserts mean image back to the boldFIXICA file using g_InsertMean matlab function
#             echo "Removing mean image on the mapped CIFTI FIX ICA $BOLD data for $CASE... "
#             ${QUNEXMCOMMAND} "g_RemoveMean(['bold' num2str($BOLD) '.dtseries.nii'], ['boldFIXICA' num2str($BOLD) '.dtseries.nii'], ['boldFIXICA_demean' num2str($BOLD) '.dtseries.nii']),quit()"
#         #fi
#     #fi
#     #rm boldFIXICA"$BOLD"_mean.txt &> /dev/null
# done
# }

######################################### DO WORK ##########################################


if [[ ${ICAFIXFunction} == "1" ]]; then 
    icafix
fi

if [[ ${ICAFIXFunction} == "2" ]]; then 
    postfix
fi

if [[ ${ICAFIXFunction} == "all" ]]; then 
    icafix
    postfix
fi

if [[ ${ICAFIXFail} == "True" ]]; then
   echo ""
   reho " ===> ERROR. Check logs --> ${OutputLogFIX}" 
   echo ""
   reho "  --- ICA FIX failed for the following BOLD runs: "
   reho "-----------------------"
   echo ""
   reho "    ${FailedBOLDS}"
   echo ""
   reho "-----------------------"
   echo ""
else
   echo ""
   geho " ===> ICA FIX ran OK for the following sessions: ${CASES}"
   echo ""
   geho "------------------------- Successful completion of work --------------------------------"
   echo ""
fi

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
