#!/bin/bash
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## COPYRIGHT NOTICE
#
# Copyright (C) 2015 Anticevic Lab, Yale University
#
# ## AUTHORS(s)
#
# * Alan Anticevic, Department of Psychiatry, Yale University
#
# ## PRODUCT
#
# Wrapper to run Pretractography function
#
# ## LICENCE
#
# * The PreTractography.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ## TODO
#
# ## DESCRIPTION 
#   
# This script, PreTractography.sh, implements ROI extraction
# using a pre-specified ROI file in NIFTI or CIFTI format
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * MNAP Suite
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./PreTractography.sh --help
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
echo ""
echo ""
echo "This function runs the Pretractography Dense trajectory space generation."
echo "Note that this is a very quick function to run [< 5min] so no overwrite options exist."
echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing and completed diffusion and bedpostX processing: "
echo ""
echo " <study_folder>/<case>/hcp/<case>/Diffusion ---> DWI data needs to be here"
echo " <study_folder>/<case>/hcp/<case>/T1w/Diffusion.bedpostX ---> BedpostX output data needs to be here"
echo ""
echo "-- REQUIRED PARMETERS VIA MNAP:"
echo ""
echo "--sessionsfolder=<folder_with_subjects>                 Path to study folder that contains subjects"
echo "--subjects=<comma_separated_list_of_cases>              List of subjects to run"
echo "--scheduler=<name_of_cluster_scheduler_and_options>     A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo "                                                        e.g. for SLURM the string would look like this: "
echo "                                                        --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
echo ""
echo "-- EXAMPLE:"
echo ""
echo "mnap pretractographyDense --sessionsfolder='<path_to_study_subjects_folder>' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo ""
echo "Direct usage: $0 <StudyFolder> <Session> <MSMflag>"
echo "       T1w and MNINonLinear folders are expected within <StudyFolder>/<Session>"
echo "       MSMflag=0 uses the default surfaces, MSMflag=1 uses the MSM surfaces defined in MakeTrajectorySpace_MNI.sh" 
echo ""
exit 0
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]] || [ "$3" == "" ]; then
    usage
fi

scriptsdir="${HCPPIPEDIR_dMRITracFull}"/PreTractography

StudyFolder=$1
Session=$2
MSMflag=$3

WholeBrainTrajectoryLabels=${scriptsdir}/config/WholeBrainFreeSurferTrajectoryLabelTableLut.txt
LeftCerebralTrajectoryLabels=${scriptsdir}/config/LeftCerebralFreeSurferTrajectoryLabelTableLut.txt 
RightCerebralTrajectoryLabels=${scriptsdir}/config/RightCerebralFreeSurferTrajectoryLabelTableLut.txt
FreeSurferLabels=${scriptsdir}/config/FreeSurferAllLut.txt

T1wDiffusionFolder="${StudyFolder}/${Session}/T1w/Diffusion"
DiffusionResolution=`${FSLDIR}/bin/fslval ${T1wDiffusionFolder}/data pixdim1`
DiffusionResolution=`printf "%0.2f" ${DiffusionResolution}`
LowResMesh=32
StandardResolution="2"

# -- Needed for making the fibre connectivity file in Diffusion space
${scriptsdir}/MakeTrajectorySpace.sh \
    --path="$StudyFolder" --subject="$Session" \
    --wholebrainlabels="$WholeBrainTrajectoryLabels" \
    --leftcerebrallabels="$LeftCerebralTrajectoryLabels" \
    --rightcerebrallabels="$RightCerebralTrajectoryLabels" \
    --diffresol="${DiffusionResolution}" \
    --freesurferlabels="${FreeSurferLabels}"

${scriptsdir}/MakeWorkbenchUODFs.sh \
--path="${StudyFolder}" \
--subject="${Session}" \
--lowresmesh="${LowResMesh}" \
--diffresol="${DiffusionResolution}"

# -- Create lots of files in MNI space used in tractography
${scriptsdir}/MakeTrajectorySpace_MNI.sh \
    --path="$StudyFolder" --subject="$Session" \
    --wholebrainlabels="$WholeBrainTrajectoryLabels" \
    --leftcerebrallabels="$LeftCerebralTrajectoryLabels" \
    --rightcerebrallabels="$RightCerebralTrajectoryLabels" \
    --standresol="${StandardResolution}" \
    --freesurferlabels="${FreeSurferLabels}" \
    --lowresmesh="${LowResMesh}" \
    --msmflag="${MSMflag}"