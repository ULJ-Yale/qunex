#!/bin/bash
#
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## PRODUCT
#
# Wrapper to run dwi_pre_tractography function
#
# ## DESCRIPTION 
#   
# This script, dwi_pre_tractography.sh, implements ROI extraction
# using a pre-specified ROI file in NIFTI or CIFTI format
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * QuNex Suite
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./dwi_pre_tractography.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are imaging data from previous processing and ROI file
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
    cat << EOF
``dwi_pre_tractography``

This function runs the Pretractography Dense trajectory space generation.

Note that this is a very quick function to run (less than 5min) so no overwrite
options exist.

Warning:

    It explicitly assumes the Human Connectome Project folder structure for
    preprocessing and completed diffusion and bedpostX processing.

    DWI data needs to be in the following folder::

        <study_folder>/<session>/hcp/<session>/T1w/Diffusion

    BedpostX output data needs to be in the following folder::

        <study_folder>/<case>/hcp/<case>/T1w/Diffusion.bedpostX

Parameters:
    --sessionsfolder (str):
        Path to study folder that contains sessions.

    --sessions (str):
        Comma separated list of sessions to run.

    --scheduler (str):
        A string for the cluster scheduler (e.g. PBS or SLURM) followed by
        relevant options e.g. for SLURM the string would look like this::

            --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

Examples:
    ::

        qunex pretractography_dense \\
            --sessionsfolder='<path_to_study_sessions_folder>' \\
            --sessions='<comma_separarated_list_of_cases>' \\
            --scheduler='<name_of_scheduler_and_options>'

    Direct usage::

        $0 <StudyFolder> <Session> <MSMflag>

    T1w and MNINonLinear folders are expected within <StudyFolder>/<Session>.

    MSMflag=0 uses the default surfaces, MSMflag=1 uses the MSM surfaces defined
    in make_trajectory_space_mni.sh.

EOF
exit 0
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]] || [ "$3" == "" ]; then
    usage
fi

scriptsdir="${HCPPIPEDIR_dMRITractFull}"/pre_tractography
configdir="${QUNEXLIBRARYETC}/pre_tractography/config"

StudyFolder=$1
Session=$2
MSMflag=$3

WholeBrainTrajectoryLabels=${configdir}/WholeBrainFreeSurferTrajectoryLabelTableLut.txt
LeftCerebralTrajectoryLabels=${configdir}/LeftCerebralFreeSurferTrajectoryLabelTableLut.txt 
RightCerebralTrajectoryLabels=${configdir}/RightCerebralFreeSurferTrajectoryLabelTableLut.txt
FreeSurferLabels=${configdir}/FreeSurferAllLut.txt

T1wDiffusionFolder="${StudyFolder}/${Session}/T1w/Diffusion"
DiffusionResolution=`${FSLDIR}/bin/fslval ${T1wDiffusionFolder}/data pixdim1`
DiffusionResolution=`printf "%0.2f" ${DiffusionResolution}`
ResultsFolder="${StudyFolder}/${Session}/MNINonLinear/Results/Tractography"
LowResMesh=32
StandardResolution="2"

# -- Needed for making the fibre connectivity file in Diffusion space
echo "---> Running make_trajectory_space.sh"
${scriptsdir}/make_trajectory_space.sh \
    --path="$StudyFolder" --session="$Session" \
    --wholebrainlabels="$WholeBrainTrajectoryLabels" \
    --leftcerebrallabels="$LeftCerebralTrajectoryLabels" \
    --rightcerebrallabels="$RightCerebralTrajectoryLabels" \
    --diffresol="${DiffusionResolution}" \
    --freesurferlabels="${FreeSurferLabels}"

echo "---> Running make_workbench_uodfs.sh"
${scriptsdir}/make_workbench_uodfs.sh \
--path="${StudyFolder}" \
--session="${Session}" \
--lowresmesh="${LowResMesh}" \
--diffresol="${DiffusionResolution}"

# -- Create lots of files in MNI space used in tractography
echo "---> Running make_trajectory_space_mni.sh"
${scriptsdir}/make_trajectory_space_mni.sh \
    --path="$StudyFolder" --session="$Session" \
    --wholebrainlabels="$WholeBrainTrajectoryLabels" \
    --leftcerebrallabels="$LeftCerebralTrajectoryLabels" \
    --rightcerebrallabels="$RightCerebralTrajectoryLabels" \
    --standresol="${StandardResolution}" \
    --freesurferlabels="${FreeSurferLabels}" \
    --lowresmesh="${LowResMesh}" \
    --msmflag="${MSMflag}"

# -- Check completion
if [[ -s "${ResultsFolder}/pial.R.asc" ]]; then
    echo ""
    echo "------------------------- Successful completion of work --------------------------------"
    echo ""
    exit 0
else
    echo ""
    echo "ERROR: dwi_pre_tractography run did not complete successfully"
    echo ""
    exit 1
fi
