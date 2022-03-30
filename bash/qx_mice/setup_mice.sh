#!/bin/sh

# SPDX-FileCopyrightText: 2022 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Authors: Jure Demsar, Jie Lisa Ji and Valerio Zerbi

# ------------------------------------------------------------------------------
#  setup color outputs
# ------------------------------------------------------------------------------

red="\033[31m"
reho() {
    echo -e "$red$1 \033[0m"
}

green="\033[32m"
geho() {
    echo -e "$green$1 \033[0m"
}


# ------------------------------------------------------------------------------
# -- Parse arguments
# ------------------------------------------------------------------------------
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

work_dir=`opts_GetOpt "--work_dir" $@`
bold=`opts_GetOpt "--bold" $@`
tr=`opts_GetOpt "--tr" $@`
voxel_increase=`opts_GetOpt "--voxel_increase" $@`
no_orientation_correction=`opts_GetOpt "--no_orientation_correction" $@`

# check required parameters
if [[ -z $work_dir ]]; then reho "ERROR: Work directory is not set!"; exit 1; fi
if [[ -z $bold ]]; then reho "ERROR: BOLD missing!"; exit 1; fi

# list parameters
echo ""
echo " --> Executing setup_mice:"
echo "       Work directory: ${work_dir}"
echo "       BOLD: ${bold}"
echo "       TR: ${tr}"

# flags
if [[ -z ${voxel_increase} ]]; then 
    echo "       Increase voxel size: no"
else
    echo "       Increase voxel size by: ${voxel_increase}"
fi

if [[ -z $no_orientation_correction ]]; then 
    echo "       Orientation correction: yes"
else
    echo "       Orientation correction: no"
fi


# ------------------------------------------------------------------------------
# -- prep
# ------------------------------------------------------------------------------
# go to work dir
pushd ${work_dir}

# create a copy, leave the original
cp ${bold}.nii.gz ${bold}_SM.nii.gz

# ------------------------------------------------------------------------------
# -- increase voxel size
# ------------------------------------------------------------------------------
if [[ -n $voxel_increase ]]; then
    echo ""
    geho " --> Increasing voxel size"

    # remove tmp.m
    if [[ -f voxel_increase_${bold}.m ]]; then
        rm voxel_increase_${bold}.m
    fi

    echo " ... Running 3dcalc -a ${bold}_SM.nii.gz -expr 'a' -prefix ${bold}_SM.hdr"
    3dcalc -a ${bold}_SM.nii.gz -expr 'a' -prefix ${bold}_SM.hdr

    echo " ... Changing the voxel dimensions"
    echo $"change_voxel_dimensions('${bold}_SM', 10);exit;">>voxel_increase_${bold}_SM.m
    matlab -nodisplay -nosplash -nojvm -r voxel_increase_${bold}_SM

    echo " ... Appending the _SM suffix to the image"
    mv ${bold}.img ${bold}_SM.img

    echo " ... fslchfiletype NIFTI_GZ ${bold}_SM.img"
    fslchfiletype NIFTI_GZ ${bold}_SM.img
fi


# ------------------------------------------------------------------------------
# -- check if TR is correct
# ------------------------------------------------------------------------------
echo ""
geho " --> Verifying TR"

# check
echo " ... Running fslmerge -tr ${bold}_SM.nii.gz ${bold}_SM.nii.gz ${tr}"
fslmerge -tr ${bold}_SM.nii.gz ${bold}_SM.nii.gz ${tr}


# ------------------------------------------------------------------------------
# -- orientation correction (should user be able to flip x, y, z?)
# ------------------------------------------------------------------------------
if [ -z $no_orientation_correction ]; then
    geho " --> Correcting orientation"

    echo " ... Running fslswapdim ${bold}_SM.nii.gz -x y z ${bold}_SM.nii.gz"
    fslswapdim ${bold}_SM.nii.gz -x y z ${bold}_SM.nii.gz 
    echo " ... Running fslorient -deleteorient ${bold}_SM.nii.gz"
    fslorient -deleteorient ${bold}_SM.nii.gz
    echo " ... Running 3drefit -orient RAI ${bold}_SM.nii.gz"
    3drefit -orient RAI ${bold}_SM.nii.gz
fi


# ------------------------------------------------------------------------------
# -- AFNI despike
# ------------------------------------------------------------------------------
echo ""
geho " --> Despiking"

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
echo ""
reho "--> setup_mice successfully completed"
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""
exit 0

# back to starting dir
popd
