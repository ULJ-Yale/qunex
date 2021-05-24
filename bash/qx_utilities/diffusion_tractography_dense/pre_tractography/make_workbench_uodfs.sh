#!/bin/bash
#
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

########################################## SUPPORT FUNCTIONS #####################################################
# function for parsing options
getopt1() {
    sopt="$1"
    shift 1
    for fn in $@ ; do
	if [ `echo $fn | grep -- "^${sopt}=" | wc -w` -gt 0 ] ; then
	    echo $fn | sed "s/^${sopt}=//"
	    return 0
	fi
    done
}

defaultopt() {
    echo $1
}


################################################## OPTION PARSING ###################################################
# Input Variables
StudyFolder=`getopt1 "--path" $@`                # "$1" #Path to Generic Study folder
Session=`getopt1 "--session" $@`                 # "$2" #SessionID
LowResMesh=`getopt1 "--lowresmesh" $@`  # "$3" #DownSampled number of CIFTI vertices
DiffusionResolution=`getopt1 "--diffresol" $@`   # "$4" #Diffusion Resolution in mm

Caret7_Command="$WORKBENCHDIR/wb_command"

#NamingConventions and Paths
trajectory="Whole_Brain_Trajectory"
T1wFolder="${StudyFolder}/${Session}/T1w"
BedpostXFolder="${StudyFolder}/${Session}/T1w/Diffusion.bedpostX"
MNINonLinearFolder="${StudyFolder}/${Session}/MNINonLinear"
NativeFolder="${StudyFolder}/${Session}/T1w/Native"
DownSampleFolder="${StudyFolder}/${Session}/T1w/fsaverage_LR${LowResMesh}k"

echo "Creating Fibre File for Connectome Workbench"
${Caret7_Command} -estimate-fiber-binghams ${BedpostXFolder}/merged_f1samples.nii.gz ${BedpostXFolder}/merged_th1samples.nii.gz ${BedpostXFolder}/merged_ph1samples.nii.gz ${BedpostXFolder}/merged_f2samples.nii.gz ${BedpostXFolder}/merged_th2samples.nii.gz ${BedpostXFolder}/merged_ph2samples.nii.gz ${BedpostXFolder}/merged_f3samples.nii.gz ${BedpostXFolder}/merged_th3samples.nii.gz ${BedpostXFolder}/merged_ph3samples.nii.gz ${T1wFolder}/${trajectory}_${DiffusionResolution}.nii.gz ${BedpostXFolder}/${trajectory}_${DiffusionResolution}.fiberTEMP.nii

${Caret7_Command} -add-to-spec-file ${NativeFolder}/${Session}.native.wb.spec INVALID ${BedpostXFolder}/${trajectory}_${DiffusionResolution}.fiberTEMP.nii
${Caret7_Command} -add-to-spec-file ${DownSampleFolder}/${Session}.${LowResMesh}k_fs_LR.wb.spec INVALID ${BedpostXFolder}/${trajectory}_${DiffusionResolution}.fiberTEMP.nii

