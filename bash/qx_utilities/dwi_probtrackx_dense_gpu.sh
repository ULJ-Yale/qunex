#!/bin/sh

# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

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
    cat << EOF
``dwi_probtrackx_dense_gpu``

This function runs the probtrackxgpu dense whole-brain connectome generation by
calling ${ScriptsFolder}/run_matrix1.sh or ${ScriptsFolder}/run_matrix3.sh.
Note that this function needs to send work to a GPU-enabled queue or you need
to run it locally from a GPU-equiped machine.

It explicitly assumes the Human Connectome Project folder structure and
completed dwi_bedpostx_gpu and dwi_pre_tractography functions processing:

- HCP Pipelines
- FSL 5.0.9 or greater

Processed DWI data needs to be here::

    <study_folder>/<session>/hcp/<session>/T1w/Diffusion

BedpostX output data needs to be here::

    <study_folder>/<session>/hcp/<session>/T1w/Diffusion.bedpostX

T1w images need to be in MNINonLinear space here::

    <study_folder>/<session>/hcp/<session>/MNINonLinear

Parameters:
    --sessionsfolder (str):
        Path to study folder that contains sessions.
    --sessions (str):
        Comma separated list of sessions to run.
    --overwrite (str):
        Delete a prior run for a given session ('yes' / 'no').
        Note: this will delete only the Matrix run specified by the -omatrix
        flag.
    --omatrix1 (str):
        Specify if you wish to run matrix 1 model [yes or omit flag]
    --omatrix3 (str):
        Specify if you wish to run matrix 3 model [yes or omit flag]
    --nsamplesmatrix1 (str, default '10000'):
        Number of samples.
    --nsamplesmatrix3 (str, default '3000'):
        Number of samples.
    --distancecorrection (str, default 'no'):
        Use distance correction.
    --storestreamlineslength (str, default 'no'):
        Store average length of the streamlines.
    --scriptsfolder (str):
        Location of the probtrackX GPU scripts.
    --loopcheck (flag):
        Generic parameter set by default (will be parameterized in the future).
    --forcedir (flag):
        Generic parameter set by default (will be parameterized in the future).
    --fibthresh (str, default '0.01'):
        Generic parameter set by default (will be parameterized in the future).
    --c (str, default '0.2'):
        Generic parameter set by default (will be parameterized in the future).
    --sampvox (str, default '2'):
        Generic parameter set by default (will be parameterized in the future).
    --randfib (str, default '1'):
        Generic parameter set by default (will be parameterized in the future).
    --S (str, default '2000'):
        Generic parameter set by default (will be parameterized in the future).
    --steplength (str, default '0.5'):
        Generic parameter set by default (will be parameterized in the future).

Output files:
    Dense Connectome CIFTI Results in MNI space for Matrix1 will be here::

       <study_folder>/<session>/hcp/<session>/MNINonLinear/Results/Conn1.dconn.nii.gz

    Dense Connectome CIFTI Results in MNI space for Matrix3 will be here::

       <study_folder>/<session>/hcp/<session>/MNINonLinear/Results/Conn3.dconn.nii.gz

Notes:
    Use:
        The function calls either of these based on the --omatrix1 and --omatrix3 flags::

            $HCPPIPEDIR_dMRITractFull/tractography_gpu_scripts/run_matrix1.sh
            $HCPPIPEDIR_dMRITractFull/tractography_gpu_scripts/run_matrix3.sh

        Both functions are cluster-aware and send the jobs to the GPU-enabled
        queue. They do not work interactively.

    Note on waytotal normalization and log transformation of streamline counts:
        waytotal normalization is computed automatically as part of the run
        prior to any inter-session or group comparisons to account for
        individual differences in geometry and brain size. The function divides
        the dense connectome by the waytotal value, turning absolute streamline
        counts into relative proportions of the total streamline count in each
        session.

        Next, a log transformation is computed on the waytotal normalized data,
        which will yield stronger connectivity values for longe-range
        projections. Log-transformation accounts for algorithmic distance bias
        in tract generation (path probabilities drop with distance as
        uncertainty is accumulated).

        See Donahue et al. (2016) The Journal of Neuroscience, 36(25):6758–6770.
        DOI: https://doi.org/10.1523/JNEUROSCI.0493-16.2016

        The outputs for these files will be in::

            /<path_to_study_sessions_folder>/<session>/hcp/<session>/MNINonLinear/Results/Tractography/<MatrixName>_waytotnorm.dconn.nii
            /<path_to_study_sessions_folder>/<session>/hcp/<session>/MNINonLinear/Results/Tractography/<MatrixName>_waytotnorm_log.dconn.nii

Examples:
    Run directly via::

        ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_probtrackx_dense_gpu.sh \\
            --<parameter1>  \\
            --<parameter2>  \\
            --<parameter3>  \\
            ...  --<parameterN>

    NOTE: --scheduler is not available via direct script call.

    Run via::

        qunex dwi_probtrackx_dense_gpu \\
            --<parameter1> \\
            --<parameter2> ... \\
            --<parameterN>

    NOTE: scheduler is available via qunex call.

    --scheduler
        A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
        relevant options.

    For SLURM scheduler the string would look like this via the qunex call::

        --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

    ::

        qunex dwi_probtrackx_dense_gpu \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separarated_list_of_cases>' \\
            --scheduler='<name_of_scheduler_and_options>' \\
            --omatrix1='yes' \\
            --nsamplesmatrix1='10000' \\
            --overwrite='no'

EOF
    exit 0
}

# ------------------------------------------------------------------------------------------------------
# ----------------------------------- dwi_probtrackx_dense_gpu CODE ------------------------------------
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
        if [[ `echo $fn | grep -- "^${sopt}=" | wc -w` -gt 0 ]]; then
            echo $fn | sed "s/^${sopt}=//"
            return 0
        fi
    done
    }

    # -- Initialize global output variables
    unset SessionsFolder
    unset Session
    unset Overwrite
    unset ScriptsFolder
    unset NSamplesMatrixOne
    unset NSamplesMatrixThree
    unset MatrixOne
    unset MatrixThree
    unset minimumfilesize
    unset distance_correction
    unset store_streamlines_length

    # -- Parse arguments
    SessionsFolder=`opts_GetOpt "--sessionsfolder" $@`
    CASE=`opts_GetOpt "--session" "$@" | sed 's/,/ /g;s/|/ /g'`
    Overwrite=`opts_GetOpt "--overwrite" $@`
    ScriptsFolder=`opts_GetOpt "--scriptsfolder" $@`
    MatrixOne=`opts_GetOpt "--omatrix1" $@`
    MatrixThree=`opts_GetOpt "--omatrix3" $@`
    NSamplesMatrixOne=`opts_GetOpt "--nsamplesmatrix1" $@`
    NSamplesMatrixThree=`opts_GetOpt "--nsamplesmatrix3" $@`
    distance_correction=`opts_GetOpt "--distancecorrection" $@`
    store_streamlines_length=`opts_GetOpt "--storestreamlineslength" $@`

    if [[ -z ${SessionsFolder} ]]; then
        reho "ERROR: <sessionsfolder> not specified"
        echo ""
        exit 1
    fi
    if [[ -z ${CASE} ]]; then
        reho "ERROR: <sessions> not specified"
        echo ""
        exit 1
    fi

    # -- Check if Matrix 1 or 3 flag set
    if [[ -z "$MatrixOne" ]]  && [[ -z "$MatrixThree" ]]; then reho "ERROR: Matrix option missing. You need to specify at least one. [e.g. --omatrix1='yes' and/or --omatrix3='yes']"; exit 1; fi
    if [ -z "$MatrixOne" ]; then MatrixOne="no"; fi
    if [ -z "$MatrixThree" ]; then MatrixThree="no"; fi
    if [[ -z "$NSamplesMatrixOne" ]]; then NSamplesMatrixOne=10000; fi
    if [[ -z "$NSamplesMatrixThree" ]]; then NSamplesMatrixThree=3000; fi
    if [[ "$MatrixOne" == "yes" ]] && [[ "$MatrixThree" == "yes" ]]; then
        MNumber="1 3"
    elif [[ "$MatrixOne" == "yes" ]]; then
        MNumber="1"
    elif [[ "$MatrixThree" == "yes" ]]; then
        MNumber="3"
    fi

    # -- Optional parameters
    if [[ -z ${ScriptsFolder} ]]; then ScriptsFolder="${HCPPIPEDIR_dMRITractFull}/tractography_gpu_scripts"; fi

    # minimumfilesize
    minimumfilesize="100000000"

    # -- Set StudyFolder
    cd $SessionsFolder/../ &> /dev/null
    StudyFolder=`pwd` &> /dev/null

    # -- distance correction flag
    if [ "$distance_correction" == "yes" ] || [ "$distance_correction" == "YES" ]; then
        distance_correction="yes"
    else
        distance_correction="no"
    fi

    # -- store streamlines length flag
    if [ "$store_streamlines_length" == "yes" ] || [ "$store_streamlines_length" == "YES" ]; then
        store_streamlines_length="yes"
    else
        store_streamlines_length="no"
    fi

    scriptName=$(basename ${0})
    # -- Report options
    echo ""
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Session: ${CASE}"
    echo "   probtrackX GPU scripts Folder: ${ScriptsFolder}"
    echo "   Compute Matrix1: ${MatrixOne}"
    echo "   Compute Matrix3: ${MatrixThree}"
    echo "   Number of samples for Matrix1: ${NSamplesMatrixOne}"
    echo "   Number of samples for Matrix3: ${NSamplesMatrixThree}"
    echo "   Distance correction: ${distance_correction}"
    echo "   Store streamlines length: ${store_streamlines_length}"
    echo "   Overwrite prior run: ${Overwrite}"
    echo "-- ${scriptName}: Specified Command-Line Options - End --"
    echo ""
    geho "------------------------- Start of work --------------------------------"
    echo ""
}

######################################### DO WORK ##########################################

main() {
    get_options "$@"

    # -------------------------------
    # -- Do work for Matrix 1 or 3 --
    # -------------------------------

    # completion check
    COMPLETIONCHECK=0

    # output folder
    OutFolder="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography";

    # -- Generate the results and log folders
    mkdir ${OutFolder}  &> /dev/null

    # -- Echo probtrackX log
    echo ""
    geho "   --- probtrackX GPU for session $CASE..."
    echo ""
    
    for MNum in $MNumber; do
        if [[ "$MNum" == "1" ]]; then NSamples="${NSamplesMatrixOne}"; fi
        if [[ "$MNum" == "3" ]]; then NSamples="${NSamplesMatrixThree}"; fi

        # -- Check of overwrite flag was set
        if [[ "$Overwrite" == "yes" ]]; then
            echo ""
            reho " --- Removing existing Probtrackxgpu Matrix${MNum} dense run for $CASE..."
            echo ""
            rm -f ${OutFolder}/Conn${MNum}.dconn.nii.gz &> /dev/null
        fi

        # -- Check for Matrix completion
        echo ""
        geho "Checking if ProbtrackX Matrix ${MNum} and dense connectome was completed on $CASE..."
        echo ""

        # -- Check if the file even exists
        if [[ -f ${OutFolder}/Conn${MNum}.dconn.nii.gz ]]; then

            # -- Set file sizes to check for completion
            actualfilesize=`wc -c < "$OutFolder"/Conn${MNum}.dconn.nii.gz` > /dev/null 2>&1

            # -- Then check if Matrix run is complete based on size
            if [[ $(echo ${actualfilesize} | bc) -ge $(echo ${minimumfilesize} | bc) ]]; then > /dev/null 2>&1
                echo ""
                cyaneho "DONE -- ProbtrackX Matrix ${MNum} solution and dense connectome was completed for ${CASE}"
                cyaneho "To re-run set overwrite flag to 'yes'"
                echo ""
                echo "--------------------------------------------------------------"
                echo ""
            fi
        else
            # -- If run is incomplete perform run for Matrix
            echo ""
            geho "ProbtrackX Matrix ${MNum} solution and dense connectome incomplete for $CASE. Starting run with $NSamples samples..."
            echo ""

            # -- Command to run
            DWIprobtrackxDenseGPUCommand="${ScriptsFolder}/run_matrix${MNum}.sh ${SessionsFolder} ${CASE} ${NSamples} ${distance_correction} ${store_streamlines_length}"

            # -- Echo the command
            echo "Running the following probtrackX GPU command: "
            echo ""
            echo "---------------------------"
            echo ""
            echo "   ${DWIprobtrackxDenseGPUCommand}"
            echo ""
            echo "---------------------------"

            # -- Eval the command
            eval "${DWIprobtrackxDenseGPUCommand}"
        fi

        # completion check
        if [[ ! -f ${OutFolder}/Conn${MNum}.dconn.nii.gz ]]; then
            # print error for this case
            reho "ERROR: dwi_probtracx_dense_gpu for $CASE failed!"
        else
            # print success for this case
            geho "dwi_probtracx_dense_gpu for $CASE completed successfully!"
            
            # set as success
            COMPLETIONCHECK=1
        fi
    done

    # final completion check
    if [[ "$COMPLETIONCHECK" == 1 ]]; then
        echo ""
        geho "------------------------- Successful completion of work --------------------------------"
        echo ""
        exit 0
    else
        echo ""
        reho "ERROR: dwi_probtracx_dense_gpu run did not complete successfully"
        echo ""
        exit 1
    fi
}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
