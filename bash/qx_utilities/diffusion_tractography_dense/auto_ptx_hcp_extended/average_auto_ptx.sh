#!/bin/bash
#
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

Usage() {
cat << EOF

Usage: average_auto_ptx <StudyFolder> <SessionId_list> <OutputFolder>

    For each SessionId in the provided list, the autoptx results are summed and averaged and saved in the outputFolder
    AutoPtx results for each session are assumed saved in <StudyFolder>/<SessionId>/MNINonLinear/Results/autoPtx,
    so <StudyFolder> has to hold every listed session, as an HCP study folder does. In QuNex each session's
    results are in its own <sessionsfolder>/<SessionId>/hcp/<SessionId>: link those into one folder first,
    e.g. ln -s <sessionsfolder>/<SessionId>/hcp/<SessionId> <StudyFolder>/<SessionId>, and give that folder.

    A session that lacks any of the tracts is left out of the average.

EOF
    exit 1
}

[ "$3" = "" ] && Usage

StudyFolder=$1
list=$2
OutputFolder=$3

rm -rf $OutputFolder
mkdir -p $OutputFolder

tracts="ar_l atr_l cgc_l cgh_l cst_l fma ifo_l ilf_l ml_l ptr_l slf_l slf1_l slf2_l slf3_l str_l unc_l ar_r atr_r cgc_r cgh_r cst_r fmi ifo_r ilf_r mcp ml_r ptr_r slf_r slf1_r slf2_r slf3_r str_r unc_r"

TractsPath="MNINonLinear/Results/autoPtx"
count=0
for i in $list; do
    echo $i
    # a session counts only with all its tracts, so every average has the same sessions
    error=0
    for j in $tracts; do
        tmp=$StudyFolder/$i/$TractsPath/$j/tracts/tractsNorm.nii.gz
        if [ ! -f $tmp ]; then
            echo "File $tmp not found!"
            error=1
        fi
    done
    if [ "$error" -eq "1" ]; then
        echo "Session $i left out of the average"
        continue
    fi
    for j in $tracts; do
        tmp=$StudyFolder/$i/$TractsPath/$j/tracts/tractsNorm.nii.gz
        if [ "$count" -eq "0" ]; then
            imcp $tmp $OutputFolder/$j
        else
            fslmaths $OutputFolder/$j -add $tmp $OutputFolder/$j
        fi
    done
    count=$(( $count + 1))
done

if [ "$count" -eq "0" ]; then
    echo "ERROR: average_auto_ptx: no session has all the autoPtx tracts."
    exit 1
fi

for j in $tracts; do
    fslmaths $OutputFolder/$j -div $count $OutputFolder/$j
done

echo "AutoPtx results from $count sessions averaged"
