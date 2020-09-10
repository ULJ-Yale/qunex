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
# DWIFSLDtifit.sh
#
# ## LICENSE
#
# * The DWIFSLDtifit.sh = the "Software"
# * This Software conforms to the license outlined in the Qu|Nex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ## TODO
#
# ## DESCRIPTION 
#   
# This script, DWIFSLDtifit.sh, implements FSL's DTIFIT functionality within the Qu|Nex Suite
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * FSL v.5.06 or higher
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./DWIFSLDtifit.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files: $SessionsFolder/sessions/$CASE/hcp/$CASE/T1w/Diffusion
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
 echo ""
 echo "This function runs the FSL dtifit processing locally or via a scheduler."
 echo "It explicitly assumes the Human Connectome Project folder structure for "
 echo " preprocessing and completed diffusion processing. "
 echo ""
 echo "The DWI data is expected to be in the following folder::"
 echo ""
 echo "  <study_folder>/<case>/hcp/<case>/Diffusion"
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "--function         Explicitly specify name of function in flag or use function "
 echo "                   name as first argument (e.g. qunex <function_name> followed "
 echo "                   by flags)"
 echo "--sessionsfolder   Path to study folder that contains sessions"
 echo "--sessions         Comma separated list of sessions to run"
 echo "--overwrite        Delete prior run for a given session (yes / no)"
 echo "--scheduler        A string for the cluster scheduler (e.g. LSF, PBS or SLURM) "
 echo "                   followed by relevant options; e.g. for SLURM the string "
 echo "                   would look like this: "
 echo ""
 echo "                   --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
 echo ""
 echo "EXAMPLE USE"
 echo "==========="
 echo ""
 echo "Run directly via::"
 echo ""
 echo " ${TOOLS}/${QUNEXREPO}/connector/functions/FSLDtifit.sh \ "
 echo " --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
 echo ""
 reho "NOTE: --scheduler is not available via direct script call."
 echo ""
 echo "Run via:: "
 echo ""
 echo " qunex FSLDtifit --<parameter1> --<parameter2> ... --<parameterN> "
 echo ""
 geho "NOTE: scheduler is available via qunex call."
 echo ""
 echo "--scheduler       A string for the cluster scheduler (e.g. LSF, PBS or SLURM) "
 echo "                  followed by relevant options"
 echo ""
 echo "For SLURM scheduler the string would look like this via the qunex call:: "
 echo ""                   
 echo " --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "     
 echo ""     
 echo "::"
 echo ""
 echo "qunex --sessionsfolder='<path_to_study_sessions_folder>' \ "
 echo "--sessions='<comma_separarated_list_of_cases>' \ "
 echo "--function='FSLDtifit' \ "
 echo "--scheduler='<name_of_scheduler_and_options>' \ "
 echo "--overwrite='yes'"
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
# -- Check for options
# ------------------------------------------------------------------------------

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

# -- Get the command line options for this script
get_options() {

local scriptName=$(basename ${0})
local arguments=($@)
# -- Initialize global output variables
unset SessionsFolder
unset Session
runcmd=""

# -- Parse arguments
CASE=`opts_GetOpt "--session" $@`
SessionsFolder=`opts_GetOpt "--sessionsfolder" $@`
Overwrite=`opts_GetOpt "--overwrite" $@`

# -- Check required parameters
if [ -z "$SessionsFolder" ]; then reho "Error: Sessions Folder"; exit 1; fi
if [ -z "$CASE" ]; then reho "Error: Session missing"; exit 1; fi

# -- Set StudyFolder
cd $SessionsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null

# -- Report options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   Study Folder: ${StudyFolder}"
echo "   Sessions Folder: ${SessionsFolder}"
echo "   Session: ${CASE}"
echo "   Study Log Folder: ${LogFolder}"
echo "   Overwrite prior run: ${Overwrite}"
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""

}

######################################### DO WORK ##########################################

main() {

# -- Get Command Line Options
get_options $@

# -- Check if overwrite flag was set
minimumfilesize=100000
if [ "$Overwrite" == "yes" ]; then
    echo ""
    reho "Removing existing dtifit run for $CASE..."
    echo ""
    rm -rf ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/dti_* > /dev/null 2>&1
fi

checkCompletion() {
# -- Check file presence
if [ -a ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/dti_FA.nii.gz ]; then
    actualfilesize=$(wc -c <${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/dti_FA.nii.gz)
else
    actualfilesize="0"
fi
if [ $(echo "$actualfilesize" | bc) -gt $(echo "$minimumfilesize" | bc) ]; then
    RunCompleted="yes"
else
    RunCompleted="no"
fi
}

if [[ ${Overwrite} == "no" ]]; then
  checkCompletion
  if [[ ${RunCompleted} == "yes" ]]; then
     echo ""
     geho "--- DTI FIT found and successfully completed for $CASE"
     echo ""
     geho "------------------------- Successful completion of work --------------------------------"
     echo ""
     exit 0
  else
     echo ""
     reho " -- Prior DTI FIT not found for $CASE. Setting up new run..."
     echo ""
  fi
fi

# -- Command to run
dtifit --data=${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./data --out=${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./dti --mask=${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./nodif_brain_mask --bvecs=${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./bvecs --bvals=${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/./bvals

# -- Perform completion checks
reho "--- Checking outputs..."
echo ""
checkCompletion
if [[ ${RunCompleted} == "yes" ]]; then
    geho "DTI FIT completed: ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/"
    echo ""
else
   echo ""
   reho " -- DTI FIT run not found or incomplete for $CASE. Something went wrong." 
   reho "    Check output: ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion/"
   echo ""
   exit 1
fi

reho "--- DTI FIT successfully completed"
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
