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
``dwi_dtifit``

This function runs the FSL dtifit processing locally or via a scheduler.
It explicitly assumes the Human Connectome Project folder structure for
preprocessing and completed diffusion processing.

The DWI data is expected to be in the following folder, to use different data,
you can use the diffdata parameter::

    <study_folder>/<session>/hcp/<session>/T1w/Diffusion

Parameters:
    --sessionsfolder (str):
        Path to study folder that contains sessions.

    --sessions (str):
        The sessions to run.

    --overwrite (str, default 'no'):
        Whether to overwrite existing data (yes) or not (no). Note that
        previous data is deleted before the run, so in the case of a failed
        command run, previous results are lost.

    --species (str):
        dtifit currently supports processing of human and macaqu data. If
        processing macaques set this parameter to macaque.

    --mask (str, default 'T1w/Diffusion/nodif_brain_mask'):
        Set binary mask file.

    --bvecs (str, default 'T1w/Diffusion/bvecs'):
        b vectors file.

    --bvals (str, default 'T1w/Diffusion/bvals'):
        b values file.

    --diffdata (str, default '/T1w/Diffusion/data.nii.gz'):
        Diffusion data file.

    --cni (str):
        Input confound regressors [not set by default].

    --sse (str):
        Output sum of squared errors [not set by default].

    --wls (str):
        Fit the tensor with weighted least square [not set by default].

    --kurt (str):
        Output mean kurtosis map (for multi-shell data [not set by default].

    --kurtdir (str):
        Output parallel/perpendicular kurtosis map (for multi-shell data) [not
        set by default].

    --littlebit (str):
        Only process small area of brain [not set by default].

    --save_tensor (str):
        Save the elements of the tensor [not set by default].

    --zmin (str):
        Min z [not set by default].

    --zmax (str):
        Max z [not set by default].

    --ymin (str):
        Min y [not set by default].

    --ymax (str):
        Max y [not set by default].

    --xmin (str):
        Min x [not set by default].

    --xmax (str):
        Max x [not set by default].

    --gradnonlin (str):
        Gradient nonlinearity tensor file [not set by default].

    --scheduler (str):
        A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
        relevant options; e.g. for SLURM the string would look like this::

            --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

Examples:
    Run directly via::

        ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_dtifit.sh \\
            --<parameter1> \\
            --<parameter2> \\
            --<parameter3> ... \\
            --<parameterN>

    NOTE: --scheduler is not available via direct script call.

    Run via::

        qunex dwi_dtifit \\
            --<parameter1> \\
            --<parameter2> ... \\
            --<parameterN>

    NOTE: scheduler is available via qunex call.

    --scheduler
        A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
        relevant options.

    For SLURM scheduler the string would look like this via the qunex call::

     --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

    ::

        qunex dwi_dtifit \\
            --sessionsfolder='<path_to_study_sessionsfolder>' \\
            --session='<session_id>' \\
            --scheduler='<name_of_scheduler_and_options>' \\
            --overwrite='yes'

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
# -- Check for options or flags
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

    local script_name=$(basename ${0})
    local arguments=($@)
    # -- Initialize global output variables
    runcmd=""

    # -- Parse arguments
    session=`opts_getopt "--session" $@`
    sessionsfolder=`opts_getopt "--sessionsfolder" $@`
    overwrite=`opts_getopt "--overwrite" $@`
    species=`opts_getopt "--species" $@`
    mask=`opts_getopt "--mask" $@`
    bvecs=`opts_getopt "--bvecs" $@`
    bvals=`opts_getopt "--bvals" $@`
    diffdata=`opts_getopt "--diffdata" $@`
    cni=`opts_getopt "--cni" $@`
    sse=`get_flags "--sse" $@`
    wls=`get_flags "--wls" $@`
    kurt=`get_flags "--kurt" $@`
    kurtdir=`get_flags "--kurtdir" $@`
    littlebit=`get_flags "--littlebit" $@`
    save_tensor=`get_flags "--save_tensor" $@`
    zmin=`opts_getopt "--zmin" $@`
    zmax=`opts_getopt "--zmax" $@`
    ymin=`opts_getopt "--ymin" $@`
    ymax=`opts_getopt "--ymax" $@`
    xmin=`opts_getopt "--xmin" $@`
    xmax=`opts_getopt "--xmax" $@`
    gradnonlin=`opts_getopt "--gradnonlin" $@`

    # -- Check required parameters
    if [ -z "$sessionsfolder" ]; then echo "Error: sessionsfolder missing"; exit 1; fi
    if [ -z "$session" ]; then echo "Error: session missing"; exit 1; fi

    # -- Set study_folder
    cd $sessionsfolder/../ &> /dev/null
    study_folder=`pwd` &> /dev/null

    # -- Report options
    echo ""
    echo ""
    echo "-- ${script_name}: Specified Command-Line Options - Start --"
    echo "   Study Folder: ${study_folder}"
    echo "   Sessions Folder: ${sessionsfolder}"
    echo "   Session: ${session}"
    echo "   Study Log Folder: ${LogFolder}"
    echo "   overwrite prior run: ${overwrite}"

    # Report species if not default
    if [[ -n ${species} ]]; then
        echo "   species: ${species}"
    fi

    # -- Set paths
    if [[ ${species} == "macaque" ]]; then
        diffusion_folder=${sessionsfolder}/${session}/NHP/dMRI
    else
        diffusion_folder=${sessionsfolder}/${session}/hcp/${session}/T1w/Diffusion
    fi
    in_file="${diffusion_folder}/data"
    if [[ -n ${diffdata} ]]; then
        in_file=${diffdata}
        if [[ ! -f ${in_file} ]]; then
            in_file=${diffusion_folder}/${in_file}
        fi
    fi
    echo "   diffdata: ${in_file}"

    out_file=${diffusion_folder}/dti_FA.nii.gz
    echo "   output: ${out_file}"

    # mask
    if [[ -n ${mask} ]]; then
        if [[ ! -f ${mask} ]]; then
            mask=${diffusion_folder}/${mask}
        fi
    else
        mask=${diffusion_folder}/nodif_brain_mask
    fi
    echo "   mask: ${mask}"

    # bvecs
    if [[ -n ${bvecs} ]]; then
        if [[ ! -f ${bvecs} ]]; then
            bvecs=${diffusion_folder}/${bvecs}
        fi
    else
        bvecs=${diffusion_folder}/bvecs
    fi
    echo "   bvecs: ${bvecs}"

    # bvals
    if [[ -n ${bvals} ]]; then
        if [[ ! -f ${bvals} ]]; then
            bvals=${diffusion_folder}/${bvals}
        fi
    else
        bvals=${diffusion_folder}/bvals
    fi
    echo "   bvals: ${bvals}"

    # Optional parameters
    optional_parameters=""

    # cni
    if [[ -n ${cni} ]]; then
        echo "   cni: ${cni}"
        optional_parameters="${optional_parameters} --cni=${cni}"
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
        optional_parameters="${optional_parameters} --zmin=${zmin}"
    fi

    # zmax
    if [[ -n ${zmax} ]]; then
        echo "   zmax: ${zmax}"
        optional_parameters="${optional_parameters} --zmax=${zmax}"
    fi

    # ymin
    if [[ -n ${ymin} ]]; then
        echo "   ymin: ${ymin}"
        optional_parameters="${optional_parameters} --ymin=${ymin}"
    fi

    # ymax
    if [[ -n ${ymax} ]]; then
        echo "   ymax: ${ymax}"
        optional_parameters="${optional_parameters} --ymax=${ymax}"
    fi

    # xmin
    if [[ -n ${xmin} ]]; then
        echo "   xmin: ${xmin}"
        optional_parameters="${optional_parameters} --xmin=${xmin}"
    fi

    # xmax
    if [[ -n ${xmax} ]]; then
        echo "   xmax: ${xmax}"
        optional_parameters="${optional_parameters} --xmax=${xmax}"
    fi

    # gradnonlin
    if [[ -n ${gradnonlin} ]]; then
        if [[ ! -f ${gradnonlin} ]]; then
            gradnonlin=${diffusion_folder}/${gradnonlin}
        fi
        echo "   gradnonlin: ${gradnonlin}"
        optional_parameters="${optional_parameters} --gradnonlin=${gradnonlin}"
    fi

    echo "-- ${script_name}: Specified Command-Line Options - End --"
    echo ""
    echo "------------------------- Start of work --------------------------------"
    echo ""

}

######################################### DO WORK ##########################################

main() {

    # -- Get Command Line Options
    get_options $@

    # -- Check if overwrite flag was set
    minimumfilesize=100000
    if [ "$overwrite" == "yes" ]; then
        echo ""
        echo "Removing existing dtifit run for $session..."
        echo ""
        rm -rf ${out_file} > /dev/null 2>&1
    fi

    check_completion() {
        # -- Check file presence
        if [ -a ${out_file} ]; then
            actualfilesize=$(wc -c <${out_file})
        else
            actualfilesize="0"
        fi
        if [ $(echo "$actualfilesize" | bc) -gt $(echo "$minimumfilesize" | bc) ]; then
            run_completed="yes"
        else
            run_completed="no"
        fi
    }

    if [[ ${overwrite} == "no" ]]; then
    check_completion
    if [[ ${run_completed} == "yes" ]]; then
        echo ""
        echo "--- dtifit found and successfully completed for $session"
        echo ""
        echo "------------------------- Successful completion of work --------------------------------"
        echo ""
        exit 0
    else
        echo ""
        echo " -- Prior dtifit not found for $session. Setting up new run..."
        echo ""
    fi
    fi

    # -- Command to run
    echo "Running command:"
    echo ""
    echo "dtifit --data=${in_file} --out=${diffusion_folder}/dti --mask=${mask} --bvecs=${bvecs} --bvals=${bvals}${optional_parameters}"
    dtifit --data=${in_file} --out=${diffusion_folder}/dti --mask=${mask} --bvecs=${bvecs} --bvals=${bvals}${optional_parameters}

    # -- Perform completion checks
    echo "--- Checking outputs..."
    echo ""
    check_completion
    if [[ ${run_completed} == "yes" ]]; then
        echo "dtifit completed: ${diffusion_folder}"
        echo ""
        echo "--- dtifit successfully completed"
        echo ""
        echo "------------------------- Successful completion of work --------------------------------"
        echo ""
        exit 0
    else
        echo ""
        echo " -- dtifit run not found or incomplete for $session. Something went wrong." 
        echo "    Check output: ${diffusion_folder}"
        echo ""
        echo "ERROR: dtifit run did not complete successfully"
        echo ""
        exit 1
    fi
}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
