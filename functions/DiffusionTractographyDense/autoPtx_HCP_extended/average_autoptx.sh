#!/bin/bash

Usage() {
cat << EOF

Usage: average_autoptx <StudyFolder> <SessionId_list> <OutputFolder>

    For each SessionId in the provided list, the autoptx results are summed and averaged and saved in the outputFolder
    AutoPtx results for each subject are assumed saved in $StudyFolder/SessionId/MNINonLinear/Results/autoPtx

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
    if [ "$count" -eq "0" ]; then    #If first subject 
	error=0
	for j in $tracts; do
	   tmp=$StudyFolder/$i/$TractsPath/$j/tracts/tractsNorm.nii.gz
	   if [ ! -f $tmp ]; then
	       echo "File $tmp not found!"
	       error=1
	   else
	       imcp $tmp $OutputFolder/$j 
	   fi
	done
	if [ "$error" -eq "0" ]; then
	    count=$(( $count + 1))  
	fi
     else
	error=0
	for j in $tracts; do
	    tmp=$StudyFolder/$i/$TractsPath/$j/tracts/tractsNorm.nii.gz
	    if [ ! -f $tmp ]; then
		echo "File $tmp not found!"
		error=1
	    else
		fslmaths $OutputFolder/$j -add $tmp $OutputFolder/$j
	    fi
	done
	if [ "$error" -eq "0" ]; then
	    count=$(( $count + 1))  
	fi
    fi
done

for j in $tracts; do
    fslmaths $OutputFolder/$j -div $count $OutputFolder/$j
done

echo "AutoPtx results from $count subjects averaged"
