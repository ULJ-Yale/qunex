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
# This script, dwi_pre_tractography.sh, generates the dense trajectory
# space files that dwi_probtrackx_dense_gpu uses
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
# * The necessary input files are imaging data from HCP preprocessing and dwi_bedpostx_gpu
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
    cat << EOF
``dwi_pre_tractography``

Run the Pretractography Dense trajectory space generation.

..  qx_command:
    type: processing.session
    language: bash

Warning:
    This is a very quick function to run (less than 5min) so no overwrite
    options exist.

    It explicitly assumes the Human Connectome Project folder structure for
    preprocessing and completed diffusion and bedpostX processing.

    DWI data needs to be in the following folder::

        <sessionsfolder>/<session>/hcp/<session>/T1w/Diffusion

    This can be changed via the --diffusion_folder parameter.

    BedpostX output data needs to be in the following folder::

        <sessionsfolder>/<session>/hcp/<session>/T1w/Diffusion.bedpostX

Parameters:
    --studyfolder (str):
        The path to the study folder. The sessions are in its ``sessions``
        folder, unless --sessionsfolder names another one.

    --sessionsfolder (str, default '<studyfolder>/sessions'):
        The path to the folder with the sessions. Set it only when the
        sessions are not in the ``sessions`` folder of the study. One of
        --studyfolder and --sessionsfolder has to be given.

    --sessions (str):
        Comma separated list of sessions to run.

    --diffusion_folder (str):
        Path to the diffusion folder, the DWI data of which sets the
        diffusion resolution. The BedpostX outputs are always read from
        ``<sessionsfolder>/<session>/hcp/<session>/T1w/Diffusion.bedpostX``.

Examples:
    ::

        qunex dwi_pre_tractography \\
            --studyfolder='<path_to_study_folder>' \\
            --sessions='<comma_separated_list_of_cases>' \\
            --scheduler='<name_of_scheduler_and_options>'

    Direct usage::

        $0 <StudyFolder> <Session> <MSMflag> [<DiffusionFolder>]

    <StudyFolder> is the HCP Pipelines study folder, which is the session's
    ``hcp`` folder (``<sessionsfolder>/<session>/hcp``) and not the QuNex
    study folder. T1w and MNINonLinear folders are expected within
    <StudyFolder>/<Session>.

    MSMflag=0 uses the default surfaces, MSMflag=1 uses the MSM surfaces defined
    in make_trajectory_space_mni.sh.

EOF
exit 0
}

# ------------------------------------------------------------------------------
# -- Parse options
# ------------------------------------------------------------------------------

# -- Parses the command line for a flagged option, as the other qx_utilities
#    scripts do
get_options() {
    sopt="$1"
    shift 1
    for fn in "$@" ; do
        if [ `echo "$fn" | grep -c -- "^${sopt}="` -gt 0 ]; then
            echo "$fn" | sed "s/^${sopt}=//"
            return 0
        fi
    done
}

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]]; then
    usage
fi

scriptsdir="${HCPPIPEDIR_dMRITractFull}"/pre_tractography
configdir="${QUNEXLIBRARYETC}/pre_tractography/config"

# -- Flagged call, the way every other QuNex command is called. The positional
#    form below is what the shell front end used and what the usage documents
#    as direct use; both are kept.
if [[ $1 == --* ]]; then
    # the QuNex study folder, not the HCP Pipelines StudyFolder set below
    QuNexStudyFolder=`get_options "--studyfolder" "$@"`
    SessionsFolder=`get_options "--sessionsfolder" "$@"`
    Session=`get_options "--sessions" "$@"`
    if [[ -z ${Session} ]]; then
        Session=`get_options "--session" "$@"`
    fi
    DiffusionFolder=`get_options "--diffusion_folder" "$@"`
    MSMflag=0

    # the sessions are in the sessions folder of the study, unless
    # --sessionsfolder names another one
    if [[ -z ${SessionsFolder} ]] && [[ -n ${QuNexStudyFolder} ]]; then
        SessionsFolder="${QuNexStudyFolder}/sessions"
    fi

    if [[ -z ${SessionsFolder} ]]; then
        echo "ERROR: Neither --studyfolder nor --sessionsfolder specified"
        echo ""
        exit 1
    fi
    if [[ -z ${Session} ]]; then
        echo "ERROR: <session-id> not specified"
        echo ""
        exit 1
    fi

    # the folder the hcp data of this session sits in, which is what the
    # positional call was handed by bin/qunex.sh
    StudyFolder="${SessionsFolder}/${Session}/hcp"
else
    if [ "$3" == "" ]; then
        echo "ERROR: The direct usage needs <StudyFolder> <Session> <MSMflag>, see --help"
        echo ""
        exit 1
    fi
    StudyFolder=$1
    Session=$2
    MSMflag=$3
    DiffusionFolder=$4
fi

WholeBrainTrajectoryLabels=${configdir}/WholeBrainFreeSurferTrajectoryLabelTableLut.txt
LeftCerebralTrajectoryLabels=${configdir}/LeftCerebralFreeSurferTrajectoryLabelTableLut.txt
RightCerebralTrajectoryLabels=${configdir}/RightCerebralFreeSurferTrajectoryLabelTableLut.txt
FreeSurferLabels=${configdir}/FreeSurferAllLut.txt

if [[ -z ${DiffusionFolder} ]]; then
    DiffusionFolder="${StudyFolder}/${Session}/T1w/Diffusion"
fi

DiffusionResolution=`${FSLDIR}/bin/fslval ${DiffusionFolder}/data pixdim1`
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
