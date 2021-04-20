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
    echo ""
    echo "This function runs the probtrackxgpu dense whole-brain connectome generation by "
    echo "calling ${ScriptsFolder}/run_matrix1.sh or ${ScriptsFolder}/run_matrix3.sh."
    echo "Note that this function needs to send work to a GPU-enabled queue or you need "
    echo "to run it locally from a GPU-equiped machine."
    echo ""
    echo "It explicitly assumes the Human Connectome Project folder structure and "
    echo "completed dwi_fsl_bedpostx_gpu and dwi_pre_tractography functions processing:"
    echo ""     
    geho " - HCP Pipelines"
    geho " - FSL 5.0.9 or greater"
    echo ""
    echo "Processed DWI data needs to be here::"
    echo ""
    echo " <study_folder>/<session>/hcp/<session>/T1w/Diffusion"
    echo ""
    echo "BedpostX output data needs to be here::"
    echo ""
    echo " <study_folder>/<session>/hcp/<session>/T1w/Diffusion.bedpostX"
    echo ""
    echo "T1w images need to be in MNINonLinear space here::"
    echo ""
    echo " <study_folder>/<session>/hcp/<session>/MNINonLinear"
    echo ""
    echo "INPUTS"
    echo "======"
    echo ""
    echo "--sessionsfolder    Path to study folder that contains sessions"
    echo "--sessions          Comma separated list of sessions to run"
    echo "--overwrite         Delete a prior run for a given session (yes / no) [Note: "
    echo "                    this will delete only the Matrix run specified by the "
    echo "                    -omatrix flag]"
    echo "--omatrix1          Specify if you wish to run matrix 1 model [yes or omit flag]"
    echo "--omatrix3          Specify if you wish to run matrix 3 model [yes or omit flag]"
    echo "--nsamplesmatrix1   Number of samples [10000]"
    echo "--nsamplesmatrix3   Number of samples [3000]"
    echo "--scriptsfolder     Location of the probtrackX GPU scripts"
    echo ""
    echo "Generic parameters set by default (will be parameterized in the future)::"
    echo ""
    echo " --loopcheck --forcedir --fibthresh=0.01 -c 0.2 --sampvox=2 --randfib=1 -S 2000 \ "
    echo " --steplength=0.5"
    echo ""
    echo "OUTPUTS"
    echo "======="
    echo ""
    echo "Dense Connectome CIFTI Results in MNI space for Matrix1 will be here::"
    echo ""
    echo "   <study_folder>/<session>/hcp/<session>/MNINonLinear/Results/Conn1.dconn.nii.gz"
    echo ""
    echo "Dense Connectome CIFTI Results in MNI space for Matrix3 will be here::"
    echo ""
    echo "   <study_folder>/<session>/hcp/<session>/MNINonLinear/Results/Conn3.dconn.nii.gz"
    echo ""
    echo "USE"
    echo "==="
    echo ""
    echo "The function calls either of these based on the --omatrix1 and --omatrix3 flags:: "
    echo ""
    echo " $HCPPIPEDIR_dMRITractFull/tractography_gpu_scripts/run_matrix1.sh"
    echo " $HCPPIPEDIR_dMRITractFull/tractography_gpu_scripts/run_matrix3.sh"
    echo ""
    echo "Both functions are cluster-aware and send the jobs to the GPU-enabled queue. "
    echo "They do not work interactively."
    echo ""
    echo "NOTES"
    echo "====="
    echo ""
    echo "Note on waytotal normalization and log transformation of streamline counts:"
    echo ""
    echo "waytotal normalization is computed automatically as part of the run prior to "
    echo "any inter-session or group comparisons to account for individual differences in "
    echo "geometry and brain size. The function divides the dense connectome by the "
    echo "waytotal value, turning absolute streamline counts into relative proportions of "
    echo "the total streamline count in each session. "
    echo ""
    echo "Next, a log transformation is computed on the waytotal normalized data, which "
    echo "will yield stronger connectivity values for longe-range projections. "
    echo "Log-transformation accounts for algorithmic distance bias in tract generation "
    echo "(path probabilities drop with distance as uncertainty is accumulated)."
    echo ""
    echo "See Donahue et al. (2016) The Journal of Neuroscience, 36(25):6758–6770. "
    echo "DOI: https://doi.org/10.1523/JNEUROSCI.0493-16.2016"
    echo ""
    echo "The outputs for these files will be in::"
    echo ""
    echo " /<path_to_study_sessions_folder>/<session>/hcp/<session>/MNINonLinear/Results/Tractography/<MatrixName>_waytotnorm.dconn.nii"
    echo " /<path_to_study_sessions_folder>/<session>/hcp/<session>/MNINonLinear/Results/Tractography/<MatrixName>_waytotnorm_log.dconn.nii"
    echo ""
    echo "EXAMPLE USE"
    echo "==========="
    echo ""
    echo "Run directly via::"
    echo ""
    echo " ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/dwi_probtrackx_dense_gpu.sh \ "
    echo " --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
    echo ""
    reho "NOTE: --scheduler is not available via direct script call."
    echo ""
    echo "Run via:: "
    echo ""
    echo " qunex dwi_probtrackx_dense_gpu --<parameter1> --<parameter2> ... --<parameterN> "
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
    echo " qunex dwi_probtrackx_dense_gpu --sessionsfolder='<path_to_study_sessions_folder>' \ "
    echo " --sessions='<comma_separarated_list_of_cases>' \ "
    echo " --scheduler='<name_of_scheduler_and_options>' \ "
    echo " --omatrix1='yes' \ "
    echo " --nsamplesmatrix1='10000' \ "
    echo " --overwrite='no'"
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
    unset Sessions
    unset Overwrite
    unset ScriptsFolder
    unset NsamplesMatrixOne
    unset NsamplesMatrixThree
    unset MatrixOne
    unset MatrixThree
    unset minimumfilesize

    # -- Parse arguments
    SessionsFolder=`opts_GetOpt "--sessionsfolder" $@`
    CASES=`opts_GetOpt "--sessions" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
    Overwrite=`opts_GetOpt "--overwrite" $@`
    ScriptsFolder=`opts_GetOpt "--scriptsfolder" $@`
    MatrixOne=`opts_GetOpt "--omatrix1" $@`
    MatrixThree=`opts_GetOpt "--omatrix3" $@`
    NsamplesMatrixOne=`opts_GetOpt "--nsamplesmatrix1" $@`
    NsamplesMatrixThree=`opts_GetOpt "--nsamplesmatrix3" $@`

    if [[ -z ${SessionsFolder} ]]; then
        reho "ERROR: <sessionsfolder> not specified"
        echo ""
        exit 1
    fi
    if [[ -z ${CASES} ]]; then
        reho "ERROR: <sessions> not specified"
        echo ""
        exit 1
    fi

    # -- Check if Matrix 1 or 3 flag set
    if [[ -z "$MatrixOne" ]]  && [[ -z "$MatrixThree" ]]; then reho "ERROR: Matrix option missing. You need to specify at least one. [e.g. --omatrix1='yes' and/or --omatrix3='yes']"; exit 1; fi
    if [[ "$MatrixOne" == "yes" ]]; then
        if [[ -z "$NsamplesMatrixOne" ]]; then NsamplesMatrixOne=10000; fi
    fi
    if [[ "$MatrixThree" == "yes" ]]; then
        if [[ -z "$NsamplesMatrixThree" ]]; then NsamplesMatrixThree=3000; fi
    fi
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

    scriptName=$(basename ${0})
    # -- Report options
    echo ""
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo "   Study Folder: ${StudyFolder}"
    echo "   Sessions Folder: ${SessionsFolder}"
    echo "   Sessions: ${CASES}"
    echo "   probtrackX GPU scripts Folder: ${ScriptsFolder}"
    echo "   Compute Matrix1: ${MatrixOne}"
    echo "   Compute Matrix3: ${MatrixThree}"
    echo "   Number of samples for Matrix1: ${NsamplesMatrixOne}"
    echo "   Number of samples for Matrix3: ${NsamplesMatrixThree}"
    echo "   Overwrite prior run: ${Overwrite}"
    echo "-- ${scriptName}: Specified Command-Line Options - End --"
    echo ""
    geho "------------------------- Start of work --------------------------------"
    echo ""
}

######################################### DO WORK ##########################################

main() {
    get_options "$@"

    # -------------------------------------------------
    # -- Do work for Matrix 1 or 3 for each CASE
    # -------------------------------------------------

    # completion check
    COMPLETIONCHECK=1

    for CASE in $CASES; do
        # output folder
        OutFolder="${SessionsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography";

        # -- Generate the results and log folders
        mkdir ${OutFolder}  &> /dev/null

        # -- Echo probtrackX log for each case
        echo ""
        geho "   --- probtrackX GPU for session $CASE..."
        echo ""
        
        for MNum in $MNumber; do
            if [[ "$MNum" == "1" ]]; then NSamples="${NsamplesMatrixOne}"; fi
            if [[ "$MNum" == "3" ]]; then NSamples="${NsamplesMatrixThree}"; fi
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
                DWIprobtrackxDenseGPUCommand="${ScriptsFolder}/run_matrix${MNum}.sh ${SessionsFolder} ${CASE} ${Nsamples}"
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
                # set as failed
                COMPLETIONCHECK=0
            else
                # pring sucess for this case
                geho "dwi_probtracx_dense_gpu for $CASE completed successfully!"
            fi
        done
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
