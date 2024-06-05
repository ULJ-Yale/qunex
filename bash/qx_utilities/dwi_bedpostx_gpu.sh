#!/bin/bash

# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
    cat << EOF
``dwi_bedpostx_gpu``

This function runs the FSL bedpostx command, by default it will facilitate
GPUs to speed the processing.

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

    --overwrite (str, default 'no'):
        Delete prior run for a given session.

    --scheduler (str):
        A string for the cluster scheduler (PBS or SLURM) followed by
        relevant options, e.g. for SLURM the string would look like this:
        --scheduler='SLURM,jobname=<name_of_job>,
        time=<job_duration>,
        cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,
        partition=<queue_to_send_job_to>'

    --nogpu (flag, default 'no'):
        If set, this command will be processed useing a CPU instead of a GPU.

Notes:
    Apptainer (Singularity) and GPU support:
        If nogpu is not provided, this command will facilitate GPUs to speed
        up processing. Since the command uses CUDA binaries, an NVIDIA GPU
        is required. To give access to CUDA drivers to the system inside the
        Apptainer (Singularity) container, you need to use the --nv flag
        of the qunex_container script.

Examples:

    Example with a scheduler and GPU processing:

    ::

        qunex dwi_bedpostx_gpu \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separarated_list_of_cases>' \\
            --fibers='3' \\
            --burnin='3000' \\
            --model='3' \\
            --scheduler='<name_of_scheduler_and_options>' \\
            --overwrite='yes'

    Example without GPU processing:

    ::

        qunex dwi_bedpostx_gpu \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separarated_list_of_cases>' \\
            --fibers='3' \\
            --burnin='3000' \\
            --model='3' \\
            --overwrite='yes' \\
            --nogpu='yes'

EOF
 exit 0
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
    nogpu=`opts_getopt "--nogpu" $@`

    # -- Check required parameters
    if [ -z "$sessionsfolder" ]; then echo "Error: sessions folder"; exit 1; fi
    if [ -z "$session" ]; then echo "Error: session missing"; exit 1; fi

    # -- Set defaults if not provided
    if [ -z "$fibers" ]; then echo "Note: The fibers parameter is not set, using default [3]"; fibers=3; fi
    if [ -z "$weight" ]; then echo "Note: The weight parameter is not set, using default [1]"; weight=1; fi
    if [ -z "$burnin" ]; then echo "Note: The burnin parameter is not set, using default [1000]"; burnin=1000; fi
    if [ -z "$jumps" ]; then echo "Note: The jumps parameter is not set, using default [1250]"; jumps=1250; fi
    if [ -z "$sample" ]; then echo "Note: The sample parameter is not set, using default [25]"; sample=25; fi
    if [ -z "$model" ]; then echo "Note: The model parameter is not set, using default [2]"; model=2; fi
    if [ -z "$rician" ]; then echo "Note: The rician parameter is not set, using default [yes]"; rician="yes"; fi

    # -- Set StudyFolder
    cd $sessionsfolder/../ &> /dev/null
    StudyFolder=`pwd` &> /dev/null

    # -- Report run parameters
    echo ""
    echo " ---> Executing ${script_name} dwi_bedpostx_gpu:"
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
    echo "     Overwrite prior run: ${overwrite}"
    echo "     No GPU: ${nogpu}"

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
        echo " ---> $filecount merged samples for $session found."
        # -- Then check if run is complete based on file size
        if [ $(echo "$actualfilesize" | bc) -ge $(echo "$minimumfilesize" | bc) ]; then > /dev/null 2>&1
            echo ""
            echo "---> bedpostx outputs found and completed for $session"
            echo "    Check prior output logs here: $bedpostx_folder/logs"
            echo ""
            echo "-----------------------------------------------------"
            RunCompleted="yes"
        else
            echo ""
            echo "---> bedpostx outputs missing or incomplete for $session"
            echo ""
            echo "----------------------------------------------------"
            RunCompleted="no"
        fi
    fi
}

######################################### DO WORK ##########################################

main() {

    echo "------------------------- Start of work --------------------------------"

    # -- Get Command Line Options
    get_options $@

    # -- Establish global directory paths
    if [[ ${species} == "macaque" ]]; then
        diffusion_folder=${sessionsfolder}/${session}/NHP/dMRI
        bedpostx_folder=${sessionsfolder}/${session}/NHP/dMRI.bedpostX
    else
        diffusion_folder=${sessionsfolder}/${session}/hcp/${session}/T1w/Diffusion
        bedpostx_folder=${diffusion_folder}.bedpostX
    fi

    # -- Check if overwrite flag was set
    overwrite="$overwrite"
    if [ "$overwrite" == "yes" ]; then
        echo ""
        echo "---> Removing existing bedpostx run for $session..."
        rm -rf "$bedpostx_folder" > /dev/null 2>&1
    fi
    echo ""
    echo "---> Checking if bedpostx was completed on $session..."
    checkCompletion
    if [[ ${RunCompleted} == "yes" ]]; then
        echo ""
        echo "---> bedpostx completed: ${bedpostx_folder}"
        echo "---> bedpostx successfully completed"
        echo ""
        echo "------------------------- Successful completion of work --------------------------------"
        echo ""
        exit 0
    else
        echo ""
        echo "---> Prior bedpostx run not found or incomplete for $session. Setting up new run..."
    fi

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
            echo "---> Using gradient nonlinearities flag -g"
            echo ""
            gradnonlin_flag=" -g"
        else
            echo ""
            echo "---> Not using gradient nonlinearities flag -g"
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
    echo "---> Running FSL command:"

    if [[ ${nogpu} == "yes" ]]; then
        bedpostx_bin=${FSLBINDIR}/bedpostx
    else
        bedpostx_bin=${FSLBINDIR}/bedpostx_gpu
    fi

    echo "    ${bedpostx_bin} ${diffusion_folder} -n ${fibers} -w ${weight} -b ${burnin} -j ${jumps} -s ${sample} -model ${model}${gradnonlin_flag}${rician_flag}"

    # -- Execute
    ${bedpostx_bin} ${diffusion_folder} -n ${fibers} -w ${weight} -b ${burnin} -j ${jumps} -s ${sample} -model ${model}${gradnonlin_flag}${rician_flag}

    # -- Perform completion checks
    echo ""
    echo "---> Checking outputs..."
    checkCompletion
    if [[ ${RunCompleted} == "yes" ]]; then
        echo ""
        echo "---> bedpostx completed: ${bedpostx_folder}"
        echo "---> bedpostx successfully completed"
        echo ""
        echo "------------------------- Successful completion of work --------------------------------"
        echo ""
        exit 0
    else
        echo ""
        echo "---> bedpostx run not found or incomplete for $session. Something went wrong." 
        echo "    Check output: ${bedpostx_folder}"
        echo ""
        echo "ERROR: bedpostx run did not complete successfully"
        echo ""
        exit 1
    fi
}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
