#!/bin/bash

# SPDX-FileCopyrightText: 2022 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Authors: Jure Demsar, Jie Lisa Ji and Valerio Zerbi


# ------------------------------------------------------------------------------
# -- Parse arguments
# ------------------------------------------------------------------------------
opts_GetOpt() {
sopt="$1"
shift 1
for fn in "$@" ; do
    if [[ `echo ${fn} | grep -- "^${sopt}=" | wc -w` -gt 0 ]]; then
        echo ${fn} | sed "s/^${sopt}=//"
        return 0
    fi
done
}

work_dir=`opts_GetOpt "--work_dir" $@`
bold=`opts_GetOpt "--bold" $@`
tr=`opts_GetOpt "--tr" $@`
voxel_increase=`opts_GetOpt "--voxel_increase" $@`
orientation=`opts_GetOpt "--orientation" $@`

# check required parameters
if [[ -z ${work_dir} ]]; then echo "ERROR: Work directory is not set!"; exit 1; fi
if [[ -z ${bold} ]]; then echo "ERROR: BOLD missing!"; exit 1; fi

# list parameters
echo ""
echo " ---> Executing setup_mice:"
echo "       Work directory: ${work_dir}"
echo "       BOLD: ${bold}"
echo "       TR: ${tr}"

# flags
if [[ -z ${voxel_increase} ]]; then 
    echo "       Increase voxel size: no"
else
    echo "       Increase voxel size by: ${voxel_increase}"
fi

if [[ -z ${orientation} ]]; then
    echo "       Orientation correction: none"
else
    orientation=${orientation//|/" "}
    echo "       Orientation correction: ${orientation}"
fi

# ------------------------------------------------------------------------------
# -- prep
# ------------------------------------------------------------------------------
# go to work dir
pushd ${work_dir} > /dev/null

# create a copy, leave the original
cp ${bold}.nii.gz ${bold}_SM.nii.gz

# ------------------------------------------------------------------------------
# -- increase voxel size
# ------------------------------------------------------------------------------
if [[ -n ${voxel_increase} ]]; then
    echo ""
    echo " ---> Increasing voxel size"

    # remove tmp.m
    if [[ -f voxel_increase_${bold}.m ]]; then
        rm voxel_increase_${bold}.m
    fi

    echo " ... Running 3dcalc -a ${bold}_SM.nii.gz -expr 'a' -prefix ${bold}_VI.hdr"
    3dcalc -a ${bold}_SM.nii.gz -expr 'a' -prefix ${bold}_VI.hdr

    echo " ... Changing the voxel dimensions"
    echo $"change_voxel_dimensions('${bold}_VI', ${voxel_increase});exit;">>voxel_increase_${bold}_VI.m
    $QUNEXMCOMMAND voxel_increase_${bold}_VI

    echo " ... fslchfiletype NIFTI_GZ ${bold}_SM.img"
    fslchfiletype NIFTI_GZ ${bold}_VI.img

    # rename the fixed image
    rm ${bold}_SM.nii.gz
    mv ${bold}_VI.nii.gz ${bold}_SM.nii.gz
fi


# ------------------------------------------------------------------------------
# -- check if TR is correct
# ------------------------------------------------------------------------------
echo ""
echo " ---> Verifying TR"

# check
echo " ... Running fslmerge -tr ${bold}_SM.nii.gz ${bold}_SM.nii.gz ${tr}"
fslmerge -tr ${bold}_SM.nii.gz ${bold}_SM.nii.gz ${tr}


# ------------------------------------------------------------------------------
# -- orientation correction
# ------------------------------------------------------------------------------
if [[ -n ${orientation} ]]; then
    echo " ---> Correcting orientation"

    echo " ... Running fslswapdim ${bold}_SM.nii.gz ${orientation} ${bold}_SM.nii.gz"
    fslswapdim ${bold}_SM.nii.gz ${orientation} ${bold}_SM.nii.gz 
    echo " ... Running fslorient -deleteorient ${bold}_SM.nii.gz"
    fslorient -deleteorient ${bold}_SM.nii.gz
    echo " ... Running 3drefit -orient RAI ${bold}_SM.nii.gz"
    3drefit -orient RAI ${bold}_SM.nii.gz
fi


# ------------------------------------------------------------------------------
# -- AFNI despike
# ------------------------------------------------------------------------------
echo ""
echo " ---> Despiking"

if [[ -f ${bold}_DS.nii.gz ]]; then
    rm ${bold}_DS.nii.gz
fi
if [[ -f ${bold}_DS+orig.HEAD ]]; then
    rm ${bold}_DS+orig.HEAD
fi
if [[ -f ${bold}_DS+orig.BRIK ]]; then
    rm ${bold}_DS+orig.BRIK
fi

echo " ... Running 3dDespike -NEW -nomask -prefix ${bold}_DS ${bold}_SM.nii.gz"
3dDespike -NEW -nomask -prefix ${bold}_DS ${bold}_SM.nii.gz
echo " ... Running 3dAFNItoNIFTI -prefix ${bold}_DS.nii.gz ${bold}_DS+orig.BRIK"
3dAFNItoNIFTI -prefix ${bold}_DS.nii.gz ${bold}_DS+orig.BRIK


# ------------------------------------------------------------------------------
# -- wrap up
# ------------------------------------------------------------------------------
echo " ---> Removing intermediate files"
rm ${bold}_DS+orig.BRIK
rm ${bold}_DS+orig.HEAD
rm ${bold}_SM*
rm *${bold}_VI.m

echo ""
echo " ---> setup_mice successfully completed"
echo ""
echo "------------------------ Successful completion of work ------------------------"
echo ""
exit 0

# back to starting dir
popd > /dev/null
