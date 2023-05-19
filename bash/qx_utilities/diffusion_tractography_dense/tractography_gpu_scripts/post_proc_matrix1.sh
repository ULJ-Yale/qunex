#!/bin/bash -eu
#
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

Caret7_command=$WORKBENCHDIR/wb_command

if [ "$4" == "" ];then
    echo ""
    echo "usage: $0 <SessionsFolder> <Session> <GrayOrdinates_Templatedir> <OutFileName>"
    echo "Convert the merged.dot file to .dconn.nii"
    exit 1
fi

SessionsFolder=$1 # "$1" #Path to Generic Study folder
Session=$2 # "$2" #SessionID
TemplateFolder=$3
OutFileName=$4

ResultsFolder="$SessionsFolder"/"$Session"/hcp/"$Session"/MNINonLinear/Results/Tractography

${Caret7_command} -probtrackx-dot-convert ${ResultsFolder}/fdt_matrix1.dot ${ResultsFolder}/Mat1.dconn.nii -row-cifti ${TemplateFolder}/91282_Greyordinates.dscalar.nii COLUMN -col-cifti ${TemplateFolder}/91282_Greyordinates.dscalar.nii COLUMN
${Caret7_command} -cifti-transpose ${ResultsFolder}/Mat1.dconn.nii ${ResultsFolder}/Mat1_transp.dconn.nii
${Caret7_command} -cifti-average ${ResultsFolder}/${OutFileName} -cifti ${ResultsFolder}/Mat1.dconn.nii -cifti ${ResultsFolder}/Mat1_transp.dconn.nii

# create RowSum of dconn to check gyral bias
OutFileTemp=`echo ${OutFileName//".dconn.nii"/""}`
${Caret7_command} -cifti-reduce ${ResultsFolder}/${OutFileName} SUM ${ResultsFolder}/${OutFileTemp}_sum.dscalar.nii
mv $ResultsFolder/waytotal $ResultsFolder/${OutFileTemp}_waytotal

waytotal=`cat $ResultsFolder/${OutFileTemp}_waytotal`
waytotal="$(echo -e "${waytotal}" | sed -e 's/[[:space:]]*$//')"
${Caret7_command} -cifti-math "a/${waytotal}" $ResultsFolder/${OutFileTemp}_waytotnorm.dconn.nii -var a $ResultsFolder/${OutFileTemp}.dconn.nii
${Caret7_command} -cifti-math "log(1+a)" $ResultsFolder/${OutFileTemp}_waytotnorm_log.dconn.nii -var a $ResultsFolder/${OutFileTemp}_waytotnorm.dconn.nii

gzip --force $ResultsFolder/${OutFileName} --fast
gzip --force $ResultsFolder/${OutFileTemp}_waytotnorm.dconn.nii --fast
gzip --force $ResultsFolder/${OutFileTemp}_waytotnorm_log.dconn.nii --fast
gzip --force $ResultsFolder/Mat1.dconn.nii --fast
gzip --force $ResultsFolder/Mat1_transp.dconn.nii --fast
gzip --force ${ResultsFolder}/fdt_matrix1.dot --fast

if [ -f ${ResultsFolder}/fdt_matrix1_lengths.dot ]; then
    ${Caret7_command} -probtrackx-dot-convert ${ResultsFolder}/fdt_matrix1_lengths.dot ${ResultsFolder}/Mat1_lengths.dconn.nii -row-cifti ${TemplateFolder}/91282_Greyordinates.dscalar.nii COLUMN -col-cifti ${TemplateFolder}/91282_Greyordinates.dscalar.nii COLUMN

    ${Caret7_command} -cifti-transpose ${ResultsFolder}/Mat1_lengths.dconn.nii ${ResultsFolder}/Mat1_lengths_transp.dconn.nii

    ${Caret7_command} -cifti-average ${ResultsFolder}/${OutFileTemp}_lengths.dconn.nii -cifti ${ResultsFolder}/Mat1_lengths.dconn.nii -cifti ${ResultsFolder}/Mat1_lengths_transp.dconn.nii

    gzip --force ${ResultsFolder}/fdt_matrix1_lengths.dot --fast
    gzip --force ${ResultsFolder}/Mat1_lengths.dconn.nii --fast
    gzip --force ${ResultsFolder}/Mat1_lengths_transp.dconn.nii --fast
    gzip --force ${ResultsFolder}/${OutFileTemp}_lengths.dconn.nii --fast
fi
