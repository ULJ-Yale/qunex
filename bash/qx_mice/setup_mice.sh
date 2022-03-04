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
# -- general help usage function
# ------------------------------------------------------------------------------

usage() {
 echo "TODO"
}


# ------------------------------------------------------------------------------
# -- set folders
# ------------------------------------------------------------------------------
export MICE_TEMPLATES="${QUNEXLIBRARYETC}/mice_pipelines/"


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
session=`opts_GetOpt "--session" $@`
voxel_increase=`opts_GetOpt "--increase_voxel_size" $@`
tr=`opts_GetOpt "--tr" $@`
orientation_correction=`opts_GetOpt "--orientation_correction" $@`
despike=`opts_GetOpt "--despike" $@`

# check required parameters
if [[ -z "$work_dir" ]]; then reho "ERROR: Work directory not set!"; exit 1; fi
if [[ -z "$session" ]]; then reho "ERROR: Session missing!"; exit 1; fi

# list parameters
echo ""
echo " --> Executing setup_mice:"
echo "       Work directory: ${work_dir}"
echo "       Session: ${session}"
echo "       Increase voxel size by: ${voxel_increase}"
echo "       TR: ${tr}"
echo "       Orientation correction: ${orientation_correction}"
echo "       Despike: ${despike}"
echo ""

# ------------------------------------------------------------------------------
# -- prep
# ------------------------------------------------------------------------------
# create backup dir
if [[ ! -d ${work_dir}/backup ]]; then
    mkdir ${work_dir}/backup
fi


# ------------------------------------------------------------------------------
# -- increase voxel size
# ------------------------------------------------------------------------------
if [[ -n "$voxel_increase" ]]; then
    geho " --> Increasing voxel size"

    # backup the original hdr file
    if [[ ! -f ${work_dir}/backup/${session}.hdr ]]; then
        cp ${work_dir}/${session}.hdr ${work_dir}/backup/${session}.hdr
    fi

    rm ${work_dir}/tmp.m
    echo $"change_voxel_dimensions('${work_dir}/${session}', 10);exit;">>tmp.m
    matlab -nodisplay -nosplash -nojvm -r tmp
    rm ${work_dir}/tmp.m
fi


# ------------------------------------------------------------------------------
# -- check if TR is correct
# ------------------------------------------------------------------------------
geho " --> Verifying TR"

# backup the original nii.gz file
if [[ ! -f ${work_dir}/backup/${session}.nii.gz ]]; then
    cp ${work_dir}/${session}.nii.gz ${work_dir}/backup/${session}.nii.gz
fi

# check
fslmerge -tr ${work_dir}/${session}.nii.gz ${work_dir}/${session}.nii.gz ${tr}


# ------------------------------------------------------------------------------
# -- orientation correction (should user be able to flip x, y, z?)
# ------------------------------------------------------------------------------
if [ -n "$orientation_correction" ]; then
    geho " --> Correcting orientation"

    fslswapdim ${work_dir}/${session}.nii.gz -x y z ${work_dir}/${session}.nii.gz 
    fslorient -deleteorient ${work_dir}/${session}.nii.gz
    3drefit -orient RAI ${work_dir}/${session}.nii.gz
fi


# ------------------------------------------------------------------------------
# -- AFNI despike
# ------------------------------------------------------------------------------
if [ -n "$despike" ]; then
    geho " --> Despiking"

    3dDespike -NEW -nomask -prefix ${session}_ds ${work_dir}/${session}.nii.gz
    3dAFNItoNIFTI -prefix ${session}_ds.nii.gz ${session}_ds+orig.BRIK

    # remove unnecessary files
    rm ${work_dir}/*.BRIK
    rm ${work_dir}/*.HEAD
    rm ${work_dir}/lsf.*
    rm ${work_dir}/*_m.nii.gz
fi

geho " --> Despiking"


# ------------------------------------------------------------------------------
# -- wrap up
# ------------------------------------------------------------------------------
reho "--> setup_mice successfully completed"
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""
exit 0
