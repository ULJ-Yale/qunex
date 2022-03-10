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
export mice_templates="${QUNEXLIBRARYETC}/mice_pipelines"


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
melodic_anatfile=`opts_GetOpt "--melodic_anatfile" $@`
fix_rdata=`opts_GetOpt "--fix_rdata" $@`
fix_threshold=`opts_GetOpt "--fix_threshold" $@`
fix_no_motion_cleanup=`opts_GetOpt "--fix_no_motion_cleanup" $@`
fix_aggressive_cleanup=`opts_GetOpt "--fix_aggressive_cleanup" $@`
highpass=`opts_GetOpt "--highpass" $@`
flirt_ref=`opts_GetOpt "--flirt_ref" $@`
band_ftop=`opts_GetOpt "--band_ftop" $@`

# check required parameters
if [[ -z "$work_dir" ]]; then reho "ERROR: Work directory is not set!"; exit 1; fi
if [[ -z "$session" ]]; then reho "ERROR: Session missing!"; exit 1; fi

# default values
if [[ -z "$melodic_anatfile" ]]; then melodic_anatfile=${mice_templates}/EPI_template_template.nii.gz; fi
if [[ -z "$fix_rdata" ]]; then fix_rdata=${mice_templates}/zerbi_2015_neuroimage.RData; fi
if [[ -z "$fix_threshold" ]]; then fix_threshold=20; fi
if [[ -z "$highpass" ]]; then highpass=100; fi
# calculate band_fbot
band_fbot=$(bc <<< "scale=2;$highpass/10000")
if [[ -z "$flirt_ref" ]]; then flirt_ref=${mice_templates}/EPI_template_template.nii.gz; fi
if [[ -z "$band_ftop" ]]; then band_ftop=0.25; fi


# list parameters
echo ""
echo " --> Executing setup_mice:"
echo "       Work directory: ${work_dir}"
echo "       Session: ${session}"
echo "       FIX RData file: ${fix_rdata}"
echo "       FIX threshold: ${fix_threshold}"
echo "       Highpass: ${highpass}"
echo "       FLIRT reference: ${flirt_ref}"
echo "       Bandpass top limit: ${band_ftop}"

# flags
motion_cleanup=" -m"
if [[ -n "$fix_no_motion_cleanup" ]]; then 
    motion_cleanup="";
    echo "       Motion cleanup: no"
else
    echo "       Motion cleanup: yes"
fi

aggressive_cleanup=""
if [[ -n "$fix_aggressive_cleanup" ]]; then
    aggressive_cleanup="-A";
    echo "       Aggressive cleanup: yes"
else
    echo "       Aggressive cleanup: no"
fi

echo ""

# ------------------------------------------------------------------------------
# -- MELODIC
# ------------------------------------------------------------------------------
geho " --> Starting MELODIC"

melodic_output=${work_dir}/melodic_output
ica_dir=${melodic_output}.ica
data_dir=${work_dir}

# copy fsf file
cp ${mice_templates}/rsfMRI_Standard_900.fsf ${work_dir}

for i in "${work_dir}/rsfMRI_Standard_900.fsf"; do
    sed -e 's@OUTPUT@'${melodic_output}'@g' \
    -e 's@ANATFILE@'${melodic_anatfile}'@g' \
    -e 's@DATA@'$data_dir'@g' <$i> ${work_dir}/rsfMRI_ds.fsf
done

feat ${work_dir}/rsfMRI_ds.fsf

geho " --> MELODIC completed"


# ------------------------------------------------------------------------------
# -- FIX the data
# ------------------------------------------------------------------------------
geho " --> Running FIX"
export FSL_FIX_MATLAB_MODE=1
fix ${ica_dir} ${fix_rdata} ${fix_threshold}${motion_cleanup} -h ${highpass} ${aggressive_cleanup}


# ------------------------------------------------------------------------------
# -- QC
# ------------------------------------------------------------------------------
geho " --> Copying registrations to the QC folder"

# create QC dir
if [[ ! -d ${work_dir}/QC ]]; then
    mkdir ${work_dir}/QC
fi

# copy the registration
cp ${melodic_output}.feat/reg/example_func2standard.png ${work_dir}/QC/example_func2standard.png

geho " --> You can check the registrations in ${work_dir}/QC"


# ------------------------------------------------------------------------------
# -- apply registrations
# ------------------------------------------------------------------------------
geho " --> Applying registrations"
ica_dir=${}
flirt -in ${ica_dir}/filtered_func_data_clean.nii.gz -ref ${flirt_ref} -out ${work_dir}/filtered_func_data_clean_EPI.nii.gz -init reg/example_func2highres.mat -applyxfm


# ------------------------------------------------------------------------------
# -- bandpass
# ------------------------------------------------------------------------------
geho " --> Applying bandpass"
3dBandpass -despike -prefix ${work_dir}/filtered_func_data_clean_BP 0.01 0.25 ${work_dir}/PREPROC_EPI_nodemean/filtered_func_data_clean_EPI.nii.gz


# ------------------------------------------------------------------------------
# -- Registration to Allen space
# ------------------------------------------------------------------------------
geho " --> Registering to Allen space bandpass"
WarpTimeSeriesImageMultiTransform 4 ${work_dir}/filtered_func_data_clean_BP.nii.gz filtered_func_data_clean_BP_ABI.nii.gz -R ${mice_templates}/ABI_template_2021_200um.nii ${mice_templates}/EPI_to_ABI_warp.nii.gz ${mice_templates}/EPI_to_ABI_affine.txt


# ------------------------------------------------------------------------------
# -- wrap up
# ------------------------------------------------------------------------------
reho "--> preprocess_mice successfully completed"
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""
exit 0
