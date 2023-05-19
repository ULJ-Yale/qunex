#!/bin/bash -eu
#
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

Caret7_command=$WORKBENCHDIR/wb_command

if [ "$3" == "" ];then
    echo ""
    echo "usage: $0 <SessionsFolder> <Session> <GrayOrdinates_Templatedir> <OutFileName>"
    echo "Final Merge of the three .dconn /wbsparse blocks"
    exit 1
fi

SessionsFolder=$1 # "$1" #Path to Generic Study folder
Session=$2 # "$2" #SessionID
TemplateFolder=$3
OutFileName=$4

ResultsFolder="$SessionsFolder"/"$Session"/hcp/"$Session"/MNINonLinear/Results/Tractography

${Caret7_command} -probtrackx-dot-convert ${ResultsFolder}/fdt_matrix3.dot ${ResultsFolder}/${OutFileName} -row-cifti ${TemplateFolder}/91282_Greyordinates.dscalar.nii COLUMN -col-cifti ${TemplateFolder}/91282_Greyordinates.dscalar.nii COLUMN -make-symmetric

# Create RowSum of dconn to check gyral bias
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
gzip --force ${ResultsFolder}/fdt_matrix3.dot --fast

if [ -f ${ResultsFolder}/fdt_matrix3_lengths.dot ]; then
    grep -v ' 0\(\.0*\)\?$' ${ResultsFolder}/fdt_matrix3_lengths.dot > ${ResultsFolder}/fdt_matrix3_lengths_temp.dot
    echo 91282 91282 0 >> ${ResultsFolder}/fdt_matrix3_lengths_temp.dot

    ${Caret7_command} -probtrackx-dot-convert ${ResultsFolder}/fdt_matrix3_lengths_temp.dot ${ResultsFolder}/${OutFileTemp}_lengths.dconn.nii -row-cifti ${TemplateFolder}/91282_Greyordinates.dscalar.nii COLUMN -col-cifti ${TemplateFolder}/91282_Greyordinates.dscalar.nii COLUMN -make-symmetric

    rm ${ResultsFolder}/fdt_matrix3_lengths_temp.dot

    gzip --force ${ResultsFolder}/fdt_matrix3_lengths.dot --fast
    gzip --force ${ResultsFolder}/${OutFileTemp}_lengths.dconn.nii --fast
fi
