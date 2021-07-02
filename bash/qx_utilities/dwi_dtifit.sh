#!/bin/sh

# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

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
  echo "--sessionsfolder   Path to study folder that contains sessions"
  echo "--sessions         Comma separated list of sessions to run"
  echo "--overwrite        Delete prior run for a given session (yes / no)"
  echo "--species          dtifit currently supports processing of human and macaque
                           data. If processing macaques set this parameter to macaque."
  echo "--mask             Bet binary mask file [T1w/diffusion/nodif_brain_mask]."
  echo "--bvecs            b vectors file [T1w/diffusion/bvecs]."
  echo "--bvals            b values file [T1w/diffusion/bvals]."
  echo "--cni              Input confound regressors [not set by default]."
  echo "--sse              Output sum of squared errors [not set by default]."
  echo "--wls              Fit the tensor with weighted least squares
                           [not set by default]."
  echo "--kurt             Output mean kurtosis map (for multi-shell data)
                           [not set by default]."
  echo "--kurtdir          Output parallel/perpendicular kurtosis maps
                           (for multi-shell data) [not set by default]."
  echo "--littlebit        Only process small area of brain [not set by default]."
  echo "--save_tensor      Save the elements of the tensor [not set by default]."
  echo "--zmin             Min z [not set by default]."
  echo "--zmax             Max z [not set by default]."
  echo "--ymin             Min y [not set by default]."
  echo "--ymax             Max y [not set by default]."
  echo "--xmin             Min x [not set by default]."
  echo "--xmax             Max x [not set by default]."
  echo "--gradnonlin       Gradient nonlinearity tensor file [not set by default]."
  echo "--scheduler        A string for the cluster scheduler (e.g. LSF, PBS or SLURM) "
  echo "                   followed by relevant options; e.g. for SLURM the string "
  echo "                   would look like this: "
  echo ""
  echo "                   --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>, cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
  echo ""
  echo "EXAMPLE USE"
  echo "==========="
  echo ""
  echo "Run directly via::"
  echo ""
  echo " ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_dtifit.sh \ "
  echo " --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
  echo ""
  reho "NOTE: --scheduler is not available via direct script call."
  echo ""
  echo "Run via:: "
  echo ""
  echo " qunex dwi_dtifit --<parameter1> --<parameter2> ... --<parameterN> "
  echo ""
  geho "NOTE: scheduler is available via qunex call."
  echo ""
  echo "--scheduler       A string for the cluster scheduler (e.g. LSF, PBS or SLURM) "
  echo "                  followed by relevant options"
  echo ""
  echo "For SLURM scheduler the string would look like this via the qunex call:: "
  echo ""                   
  echo " --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>, mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "     
  echo ""     
  echo "::"
  echo ""
  echo "qunex dwi_dtifit \ "
  echo "--sessionsfolder='<path_to_study_sessions_folder>' \ "
  echo "--sessions='<comma_separarated_list_of_cases>' \ "
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
# -- Check for options or flags
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

get_flags() {
sopt="$1"
shift 1
for fn in "$@" ; do
    if [ `echo $fn | grep -- "^${sopt}" | wc -w` -gt 0 ]; then
        echo "yes"
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
Species=`opts_GetOpt "--species" $@`
mask=`opts_GetOpt "--mask" $@`
bvecs=`opts_GetOpt "--bvecs" $@`
bvals=`opts_GetOpt "--bvals" $@`
cni=`opts_GetOpt "--cni" $@`
sse=`get_flags "--sse" $@`
wls=`get_flags "--wls" $@`
kurt=`get_flags "--kurt" $@`
kurtdir=`get_flags "--kurtdir" $@`
littlebit=`get_flags "--littlebit" $@`
save_tensor=`get_flags "--save_tensor" $@`
zmin=`opts_GetOpt "--zmin" $@`
zmax=`opts_GetOpt "--zmax" $@`
ymin=`opts_GetOpt "--ymin" $@`
ymax=`opts_GetOpt "--ymax" $@`
xmin=`opts_GetOpt "--xmin" $@`
xmax=`opts_GetOpt "--xmax" $@`
gradnonlin=`get_flags "--gradnonlin" $@`

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

# Report species if not default
if [[ -n ${Species} ]]; then
    echo "   Species: ${Species}"
fi

# -- Set paths
if [[ ${Species} == "macaque" ]]; then
    DiffusionFolder=${SessionsFolder}/${CASE}/NHP/dMRI
    DiffusionFile=${DiffusionFolder}/data.nii.gz
else
    DiffusionFolder=${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion
    DiffusionFile=${DiffusionFolder}/dti_FA.nii.gz
fi


# mask
if [[ -n ${mask} ]]; then
    echo "   mask: ${mask}"
else
    mask=${DiffusionFolder}/nodif_brain_mask
fi

# bvecs
if [[ -n ${bvecs} ]]; then
    echo "   bvecs: ${bvecs}"
else
    bvecs=${DiffusionFolder}/bvecs
fi

# bvals
if [[ -n ${bvals} ]]; then
    echo "   bvals: ${bvals}"
else
    bvals=${DiffusionFolder}/bvals
fi

# Optional parameters
optional_parameters=""

# cni
if [[ -n ${cni} ]]; then
    echo "   cni: ${cni}"
    optional_parameters="${optional_parameters} --cni='${cni}'"
fi

# sse
if [[ -n ${sse} ]]; then
    echo "   sse: yes"
    optional_parameters="${optional_parameters} --sse"
fi

# wls
if [[ -n ${wls} ]]; then
    echo "   wls: yes"
    optional_parameters="${optional_parameters} --wls"
fi

# kurt
if [[ -n ${kurt} ]]; then
    echo "   kurt: yes"
    optional_parameters="${optional_parameters} --kurt"
fi

# kurtdir
if [[ -n ${kurtdir} ]]; then
    echo "   kurtdir: yes"
    optional_parameters="${optional_parameters} --kurtdir"
fi

# littlebit
if [[ -n ${littlebit} ]]; then
    echo "   littlebit: yes"
    optional_parameters="${optional_parameters} --littlebit"
fi

# save_tensor
if [[ -n ${save_tensor} ]]; then
    echo "   save_tensor: yes"
    optional_parameters="${optional_parameters} --save_tensor"
fi

# zmin
if [[ -n ${zmin} ]]; then
    echo "   zmin: ${zmin}"
    optional_parameters="${optional_parameters} --zmin='${zmin}'"
fi

# zmax
if [[ -n ${zmax} ]]; then
    echo "   zmax: ${zmax}"
    optional_parameters="${optional_parameters} --zmax='${zmax}'"
fi

# ymin
if [[ -n ${ymin} ]]; then
    echo "   ymin: ${ymin}"
    optional_parameters="${optional_parameters} --ymin='${ymin}'"
fi

# ymax
if [[ -n ${ymax} ]]; then
    echo "   ymax: ${ymax}"
    optional_parameters="${optional_parameters} --ymax='${ymax}'"
fi

# xmin
if [[ -n ${xmin} ]]; then
    echo "   xmin: ${xmin}"
    optional_parameters="${optional_parameters} --xmin='${xmin}'"
fi

# xmax
if [[ -n ${xmax} ]]; then
    echo "   xmax: ${xmax}"
    optional_parameters="${optional_parameters} --xmax='${xmax}'"
fi

# gradnonlin
if [[ -n ${gradnonlin} ]]; then
    echo "   gradnonlin: yes"
    optional_parameters="${optional_parameters} --gradnonlin"
fi


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
    reho "Removing existing dtifit run for $CASE..."x
    echo ""
    rm -rf DiffusionFolder/dti_* > /dev/null 2>&1
fi

checkCompletion() {
# -- Check file presence
if [ -a ${DiffusionFolder}/dti_FA.nii.gz ]; then
    actualfilesize=$(wc -c <${DiffusionFolder}/dti_FA.nii.gz)
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
     geho "--- dtifit found and successfully completed for $CASE"
     echo ""
     geho "------------------------- Successful completion of work --------------------------------"
     echo ""
     exit 0
  else
     echo ""
     reho " -- Prior dtifit not found for $CASE. Setting up new run..."
     echo ""
  fi
fi

# -- Command to run
dtifit --data=${DiffusionFolder}/data --out=${DiffusionFolder}/dti --mask=${mask} --bvecs=${bvecs} --bvals=${bvals}${optional_parameters}

# -- Perform completion checks
reho "--- Checking outputs..."
echo ""
checkCompletion
if [[ ${RunCompleted} == "yes" ]]; then
    geho "dtifit completed: ${DiffusionFolder}"
    echo ""
    reho "--- dtifit successfully completed"
    echo ""
    geho "------------------------- Successful completion of work --------------------------------"
    echo ""
    exit 0
else
    echo ""
    reho " -- dtifit run not found or incomplete for $CASE. Something went wrong." 
    reho "    Check output: ${DiffusionFolder}"
    echo ""
    reho "ERROR: dtifit run did not complete successfully"
    echo ""
    exit 1
fi
}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
