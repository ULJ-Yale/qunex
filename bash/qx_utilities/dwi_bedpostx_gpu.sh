#!/bin/sh

# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

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
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
    cat << EOF
``dwi_bedpostx_gpu``

This function runs the FSL bedpostx_gpu processing using a GPU-enabled
node or via a GPU-enabled queue if using the scheduler option.

It explicitly assumes the Human Connectome Project folder structure for
preprocessing and completed diffusion processing. DWI data is expected to
be in the following folder::

    <study_folder>/<session>/hcp/<session>/T1w/Diffusion

Parameters:
    --sessionsfolder (str):
        Path to study folder that contains sessions.
    --sessions (str):
        Comma separated list of sessions to run.
    --fibers (str, default '3'):
        Number of fibres per voxel.
    --weight (str, default '1'):
        ARD weight, more weight means less secondary fibres per voxel.
    --burnin (str, default '1000'):
        Burnin period.
    --jumps (str, default '1250'):
        Number of jumps.
    --sample (str, default '25'):
        Sample every.
    --model (str, default '2'):
        Deconvolution model:

        - '1' ... with sticks,
        - '2' ... with sticks with a range of diffusivities,
        - '3' ... with zeppelins.

    --rician (str, default 'yes'):
        Replace the default Gaussian noise assumption with Rician noise
        ('yes'/'no').
    --gradnonlin (str, default detailed below):
        Consider gradient nonlinearities ('yes'/'no'). By default set
        automatically. Set to 'yes' if the file grad_dev.nii.gz is present, set
        to 'no' if it is not.
    --overwrite (str, default 'no'):
        Delete prior run for a given session.
    --scheduler (str):
        A string for the cluster scheduler (LSF, PBS or SLURM) followed by
        relevant options, e.g. for SLURM the string would look like this:
        --scheduler='SLURM,jobname=<name_of_job>,
        time=<job_duration>,ntasks=<numer_of_tasks>,
        cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,
        partition=<queue_to_send_job_to>'
        Note: You need to specify a GPU-enabled queue or partition.

Examples:
    Run directly via::

        ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_bedpostx_gpu.sh \\
        --<parameter1> --<parameter2> --<parameter3> ... --<parameterN>

    NOTE: --scheduler is not available via direct script call.

    Run via::

        qunex dwi_bedpostx_gpu --<parameter1> --<parameter2> ... --<parameterN>

    NOTE: scheduler is available via qunex call.

    --scheduler       A string for the cluster scheduler (LSF, PBS or SLURM)
                      followed by relevant options

    For SLURM scheduler the string would look like this via the qunex call::

        --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>, \\
        ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>, \\
        mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

    ::

        qunex dwi_bedpostx_gpu \\
              --sessionsfolder='<path_to_study_sessions_folder>' \\
              --sessions='<comma_separarated_list_of_cases>' \\
              --fibers='3' \\
              --burnin='3000' \\
              --model='3' \\
              --scheduler='<name_of_scheduler_and_options>' \\
              --overwrite='yes'

EOF
 exit 0
}

# ------------------------------------------------------------------------------
# -- Setup color outputs
# ------------------------------------------------------------------------------

reho() {
    echo -e "\033[31m $1\033[0m"
}

geho() {
    echo -e "\033[32m $1\033[0m"
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

# DWI Data and T1w data needed in HCP-style format

########################################## OUTPUTS #########################################

# -- Outputs will be *pconn.nii files located here:
#       DWIOutput="$SessionsFolder/$CASE/hcp/$CASE/T1w/Diffusion/"

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
Fibers=`opts_GetOpt "--fibers" $@`
Weight=`opts_GetOpt "--weight" $@`
Burnin=`opts_GetOpt "--burnin" $@`
Jumps=`opts_GetOpt "--jumps" $@`
Sample=`opts_GetOpt "--sample" $@`
Model=`opts_GetOpt "--model" $@`
Rician=`opts_GetOpt "--rician" $@`
Gradnonlin=`opts_GetOpt "--gradnonlin" $@`
Overwrite=`opts_GetOpt "--overwrite" $@`
Species=`opts_GetOpt "--species" $@`
CASE=`opts_GetOpt "--session" $@`
SessionsFolder=`opts_GetOpt "--sessionsfolder" $@`

# -- Check required parameters
if [ -z "$SessionsFolder" ]; then reho "Error: Sessions folder"; exit 1; fi
if [ -z "$CASE" ]; then reho "Error: Session missing"; exit 1; fi

# -- Set defaults if not provided
if [ -z "$Fibers" ]; then geho "Note: The fibers parameter is not set, using default [3]"; Fibers=3; fi
if [ -z "$Weight" ]; then geho "Note: The weight parameter is not set, using default [1]"; Weight=1; fi
if [ -z "$Burnin" ]; then geho "Note: The burnin parameter is not set, using default [1000]"; Burnin=1000; fi
if [ -z "$Jumps" ]; then geho "Note: The jumps parameter is not set, using default [1250]"; Jumps=1250; fi
if [ -z "$Sample" ]; then geho "Note: The sample parameter is not set, using default [25]"; Sample=25; fi
if [ -z "$Model" ]; then geho "Note: The model parameter is not set, using default [2]"; Model=2; fi
if [ -z "$Rician" ]; then geho "Note: The Rician parameter is not set, using default [yes]"; Rician="yes"; fi

# -- Set StudyFolder
cd $SessionsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null

# -- Report run parameters
echo ""
echo " --> Executing ${scriptName} dwi_bedpostx_gpu:"
echo "     Study Folder: ${StudyFolder}"
echo "     Sessions Folder: ${SessionsFolder}"
echo "     Session: ${CASE}"
echo "     Number of Fibers: ${Fibers}"
echo "     ARD weights: ${Weight}"
echo "     Burnin Period: ${Burnin}"
echo "     Number of jumps: ${Jumps}"
echo "     Sample every: ${Sample}"
echo "     Model Type: ${Model}"
echo "     Rician flag: ${Rician}"
echo "     Overwrite prior run: ${Overwrite}"

# Report species if not default
if [[ -n ${Species} ]]; then
    echo "   Species: ${Species}"
fi

}

######################################### DO WORK ##########################################

main() {

geho "------------------------- Start of work --------------------------------"

# -- Get Command Line Options
get_options $@

# -- Establish global directory paths
if [[ ${Species} == "macaque" ]]; then
    DiffusionFolder=${SessionsFolder}/${CASE}/NHP/dMRI
    BedPostXFolder=${SessionsFolder}/${CASE}/NHP/dMRI.bedpostX
else
    DiffusionFolder=${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion
    BedPostXFolder=${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX
fi

LogFolder="$BedPostXFolder"/logs

# -- Check if overwrite flag was set
Overwrite="$Overwrite"
if [ "$Overwrite" == "yes" ]; then
    echo ""
    reho "--> Removing existing bedpostx run for $CASE..."
    rm -rf "$BedPostXFolder" > /dev/null 2>&1
fi
echo ""
geho "--> Checking if bedpostx was completed on $CASE..."
# Set file depending on model specification
if [ "$Model" == 2 ]; then
    CheckFile="mean_d_stdsamples.nii.gz"
fi
if [ "$Model" == 3 ]; then
    CheckFile="mean_Rsamples.nii.gz"
fi

checkCompletion() {
# -- Check if the file exists
if [ -f ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/"$CheckFile" ]; then
    # -- Set file sizes to check for completion
    minimumfilesize=20000000
    actualfilesize=`wc -c < ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/merged_f1samples.nii.gz` > /dev/null 2>&1
    filecount=`ls ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/merged_*nii.gz | wc | awk {'print $1'}`
fi

# -- Then check if run is complete based on file count
if [ "$filecount" == 9 ]; then > /dev/null 2>&1
    echo ""
    cyaneho " --> $filecount merged samples for $CASE found."
    # -- Then check if run is complete based on file size
    if [ $(echo "$actualfilesize" | bc) -ge $(echo "$minimumfilesize" | bc) ]; then > /dev/null 2>&1
        echo ""
        cyaneho "--> bedpostx outputs found and completed for $CASE"
        cyaneho "    Check prior output logs here: $LogFolder"
        echo ""
        echo "-----------------------------------------------------"
        RunCompleted="yes"
    else
        echo ""
        reho "--> bedpostx outputs missing or incomplete for $CASE"
        echo ""
        reho "----------------------------------------------------"
        RunCompleted="no"
    fi
fi
}

checkCompletion
if [[ ${RunCompleted} == "yes" ]]; then
   exit 0
else
   echo ""
   reho "--> Prior bedpostx run not found or incomplete for $CASE. Setting up new run..."
fi

echo ""
geho "--> Generating log folder"
mkdir ${BedPostXFolder} > /dev/null 2>&1

# -- Set rician flag
if [ "$Rician" == "no" ] || [ "$Rician" == "NO" ]; then
    RicianFlag=""
else
    RicianFlag="--rician"
fi

# -- Gradnon lin
# -- Set automatically by default 
if [ -z "$Gradnonlin" ]; then
    if [ -f "$DiffusionFolder"/grad_dev.nii.gz ]; then
        echo ""
        geho "--> Using gradient nonlinearities flag -g"
        echo ""
        GradientNonlinearitiesFlag="-g"
    else
        echo ""
        geho "--> Not using gradient nonlinearities flag -g"
        echo ""
        GradientNonlinearitiesFlag=""
    fi
else
    if [ "$Gradnonlin" == "no" ] || [ "$Gradnonlin" == "NO" ]; then
        GradientNonlinearitiesFlag=""
    else
        GradientNonlinearitiesFlag="-g"
    fi
fi

# -- Report
geho "--> Running FSL command:"
echo "    ${FSLGPUScripts}/bedpostx_gpu_noscheduler ${DiffusionFolder}/. -n ${Fibers} -w ${Weight} -b ${Burnin} -j ${Jumps} -s ${Sample} -model ${Model} ${GradientNonlinearitiesFlag} ${RicianFlag}"

# -- Execute
${FSLGPUScripts}/bedpostx_gpu_noscheduler ${DiffusionFolder}/. -n ${Fibers} -w ${Weight} -b ${Burnin} -j ${Jumps} -s ${Sample} -model ${Model} ${GradientNonlinearitiesFlag} ${RicianFlag}

# -- Perform completion checks
echo ""
reho "--> Checking outputs..."
checkCompletion
if [[ ${RunCompleted} == "yes" ]]; then
    echo ""
    geho "--> bedpostx completed: ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/"
    reho "--> bedpostx successfully completed"
    echo ""
    geho "------------------------- Successful completion of work --------------------------------"
    echo ""
    exit 0
else
    echo ""
    reho "--> bedpostx run not found or incomplete for $CASE. Something went wrong." 
    reho "    Check output: ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/"
    echo ""
    reho "ERROR: bedpostx run did not complete successfully"
    echo ""
    exit 1
fi
}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
