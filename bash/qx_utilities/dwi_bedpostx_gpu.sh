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

    <study_folder>/<session>/hcp/<session>/T1w/Diffusion<_diffdatasuffix>

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
        burnin period.

    --jumps (str, default '1250'):
        Number of jumps.

    --sample (str, default '25'):
        sample every.

    --model (str, default '2'):
        Deconvolution model:

        - '1' ... with sticks,
        - '2' ... with sticks with a range of diffusivities,
        - '3' ... with zeppelins.

    --rician (str, default 'yes'):
        Replace the default Gaussian noise assumption with rician noise
        ('yes'/'no').

    --gradnonlin (str, default detailed below):
        Consider gradient nonlinearities ('yes'/'no'). By default set
        automatically. Set to 'yes' if the file grad_dev.nii.gz is present, set
        to 'no' if it is not.

    --diffdatasuffix (str):
        Name of the DWI image; e.g. if the data is called
        <session>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR.

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
            --<parameter1> \\
            --<parameter2> \\
            --<parameter3> ... \\
            --<parameterN>

    NOTE: --scheduler is not available via direct script call.

    Run via::

        qunex dwi_bedpostx_gpu \\
            --<parameter1> \\
            --<parameter2> ... \\
            --<parameterN>

    NOTE: scheduler is available via qunex call.

    --scheduler       A string for the cluster scheduler (LSF, PBS or SLURM)
                      followed by relevant options

    For SLURM scheduler the string would look like this via the qunex call::

        --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>, ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>, mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

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

# ------------------------------------------------------------------------------
# -- Check for options
# ------------------------------------------------------------------------------

opts_getopt() {
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
    local script_name=$(basename ${0})
    local arguments=($@)
    # -- Initialize global output variables
    unset sessionsfolder
    unset session
    runcmd=""

    # -- Parse arguments
    fibers=`opts_getopt "--fibers" $@`
    weight=`opts_getopt "--weight" $@`
    burnin=`opts_getopt "--burnin" $@`
    jumps=`opts_getopt "--jumps" $@`
    sample=`opts_getopt "--sample" $@`
    model=`opts_getopt "--model" $@`
    rician=`opts_getopt "--rician" $@`
    gradnonlin=`opts_getopt "--gradnonlin" $@`
    overwrite=`opts_getopt "--overwrite" $@`
    species=`opts_getopt "--species" $@`
    session=`opts_getopt "--session" $@`
    sessionsfolder=`opts_getopt "--sessionsfolder" $@`
    diffdatasuffix=`opts_getopt "--diffdatasuffix" $@`

    # -- Check required parameters
    if [ -z "$sessionsfolder" ]; then reho "Error: sessions folder"; exit 1; fi
    if [ -z "$session" ]; then reho "Error: session missing"; exit 1; fi

    # -- Set defaults if not provided
    if [ -z "$fibers" ]; then geho "Note: The fibers parameter is not set, using default [3]"; fibers=3; fi
    if [ -z "$weight" ]; then geho "Note: The weight parameter is not set, using default [1]"; weight=1; fi
    if [ -z "$burnin" ]; then geho "Note: The burnin parameter is not set, using default [1000]"; burnin=1000; fi
    if [ -z "$jumps" ]; then geho "Note: The jumps parameter is not set, using default [1250]"; jumps=1250; fi
    if [ -z "$sample" ]; then geho "Note: The sample parameter is not set, using default [25]"; sample=25; fi
    if [ -z "$model" ]; then geho "Note: The model parameter is not set, using default [2]"; model=2; fi
    if [ -z "$rician" ]; then geho "Note: The rician parameter is not set, using default [yes]"; rician="yes"; fi

    # -- Set StudyFolder
    cd $sessionsfolder/../ &> /dev/null
    StudyFolder=`pwd` &> /dev/null

    # -- Report run parameters
    echo ""
    echo " --> Executing ${script_name} dwi_bedpostx_gpu:"
    echo "     Study folder: ${StudyFolder}"
    echo "     Sessions Folder: ${sessionsfolder}"
    echo "     Session: ${session}"
    echo "     Number of fibers: ${fibers}"
    echo "     ARD weights: ${weight}"
    echo "     Burnin period: ${burnin}"
    echo "     Number of jumps: ${jumps}"
    echo "     Sample every: ${sample}"
    echo "     Model type: ${model}"
    echo "     Rician flag: ${rician}"
    echo "     Diffusion data suffix: ${diffdatasuffix}"
    echo "     Overwrite prior run: ${overwrite}"

    # Report species if not default
    if [[ -n ${species} ]]; then
        echo "     Species: ${species}"
    fi
}


checkCompletion() {
    # Set file depending on model specification
    if [ "$model" == 2 ]; then
        check_file="mean_d_stdsamples.nii.gz"
    fi
    if [ "$model" == 3 ]; then
        check_file="mean_Rsamples.nii.gz"
    fi

    # -- Check if the file exists
    if [ -f "${bedpostx_folder}/${check_file}" ]; then
        # -- Set file sizes to check for completion
        minimumfilesize=2000000
        actualfilesize=`wc -c < ${bedpostx_folder}/merged_f1samples.nii.gz` > /dev/null 2>&1
        filecount=`ls ${bedpostx_folder}/merged_*nii.gz | wc | awk {'print $1'}`
    fi

    # -- Then check if run is complete based on file count
    if [ "$filecount" == 9 ]; then > /dev/null 2>&1
        echo ""
        cyaneho " --> $filecount merged samples for $session found."
        # -- Then check if run is complete based on file size
        if [ $(echo "$actualfilesize" | bc) -ge $(echo "$minimumfilesize" | bc) ]; then > /dev/null 2>&1
            echo ""
            cyaneho "--> bedpostx outputs found and completed for $session"
            cyaneho "    Check prior output logs here: $bedpostx_folder/logs"
            echo ""
            echo "-----------------------------------------------------"
            RunCompleted="yes"
        else
            echo ""
            reho "--> bedpostx outputs missing or incomplete for $session"
            echo ""
            reho "----------------------------------------------------"
            RunCompleted="no"
        fi
    fi
}

######################################### DO WORK ##########################################

main() {

    geho "------------------------- Start of work --------------------------------"

    # -- Get Command Line Options
    get_options $@

    # -- Establish global directory paths
    if [[ ${species} == "macaque" ]]; then
        diffusion_folder=${sessionsfolder}/${session}/NHP/dMRI
        bedpostx_folder=${sessionsfolder}/${session}/NHP/dMRI.bedpostX
    else
        diffusion_folder=${sessionsfolder}/${session}/hcp/${session}/T1w/Diffusion

        if [[ -n ${diffdatasuffix} ]]; then
            diffusion_folder=${diffusion_folder}_${diffdatasuffix}
        fi

        bedpostx_folder=${diffusion_folder}.bedpostX
    fi

    # -- Check if overwrite flag was set
    overwrite="$overwrite"
    if [ "$overwrite" == "yes" ]; then
        echo ""
        reho "--> Removing existing bedpostx run for $session..."
        rm -rf "$bedpostx_folder" > /dev/null 2>&1
    fi
    echo ""
    geho "--> Checking if bedpostx was completed on $session..."
    checkCompletion
    if [[ ${RunCompleted} == "yes" ]]; then
    exit 0
    else
    echo ""
    reho "--> Prior bedpostx run not found or incomplete for $session. Setting up new run..."
    fi

    echo ""
    geho "--> Generating log folder"
    mkdir ${bedpostx_folder} > /dev/null 2>&1

    # -- Set rician flag
    if [ "$rician" == "no" ] || [ "$rician" == "NO" ]; then
        rician_flag=""
    else
        rician_flag=" --rician"
    fi

    # -- Gradnon lin
    # -- Set automatically by default 
    if [ -z "$gradnonlin" ]; then
        if [ -f "$diffusion_folder"/grad_dev.nii.gz ]; then
            echo ""
            geho "--> Using gradient nonlinearities flag -g"
            echo ""
            gradnonlin_flag=" -g"
        else
            echo ""
            geho "--> Not using gradient nonlinearities flag -g"
            echo ""
            gradnonlin_flag=""
        fi
    else
        if [ "$gradnonlin" == "no" ] || [ "$gradnonlin" == "NO" ]; then
            gradnonlin_flag=""
        else
            gradnonlin_flag=" -g"
        fi
    fi

    # -- Report
    geho "--> Running FSL command:"
    echo "    ${FSL_GPU_SCRIPTS}/bedpostx_gpu ${diffusion_folder}/. ${bedpostx_folder}/. -n ${fibers} -w ${weight} -b ${burnin} -j ${jumps} -s ${sample} -model ${model}${gradnonlin_flag}${rician_flag}"

    # -- Execute
    ${FSL_GPU_SCRIPTS}/bedpostx_gpu ${diffusion_folder}/. ${bedpostx_folder}/. -n ${fibers} -w ${weight} -b ${burnin} -j ${jumps} -s ${sample} -model ${model}${gradnonlin_flag}${rician_flag}

    # -- Link and backup if legacy processing
    if [[ -n ${diffdatasuffix} ]]; then
        original_bedpostx_folder=${sessionsfolder}/${session}/hcp/${session}/T1w/Diffusion.bedpostX
        echo ""
        geho "--> Linking ${bedpostx_folder} to ${original_bedpostx_folder}"

        # backup the old folder when running legacy
        if [[ -d ${original_bedpostx_folder} ]]; then
            mv ${original_bedpostx_folder} ${original_bedpostx_folder}.bkp
        fi

        # link
        ln -sf ${bedpostx_folder} ${original_bedpostx_folder}
    fi

    # -- Perform completion checks
    echo ""
    reho "--> Checking outputs..."
    checkCompletion
    if [[ ${RunCompleted} == "yes" ]]; then
        echo ""
        geho "--> bedpostx completed: ${bedpostx_folder}"
        reho "--> bedpostx successfully completed"
        echo ""
        geho "------------------------- Successful completion of work --------------------------------"
        echo ""
        exit 0
    else
        echo ""
        reho "--> bedpostx run not found or incomplete for $session. Something went wrong." 
        reho "    Check output: ${bedpostx_folder}"
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
