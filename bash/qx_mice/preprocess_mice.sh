#!/bin/bash

# SPDX-FileCopyrightText: 2022 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Authors: Jure Demsar, Jie Lisa Ji and Valerio Zerbi


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
bold=`opts_GetOpt "--bold" $@`
bias_field_correction=`opts_GetOpt "--bias_field_correction" $@`
melodic_anatfile=`opts_GetOpt "--melodic_anatfile" $@`
fix_rdata=`opts_GetOpt "--fix_rdata" $@`
fix_threshold=`opts_GetOpt "--fix_threshold" $@`
fix_no_motion_cleanup=`opts_GetOpt "--fix_no_motion_cleanup" $@`
fix_aggressive_cleanup=`opts_GetOpt "--fix_aggressive_cleanup" $@`
highpass=`opts_GetOpt "--mice_highpass" $@`
lowpass=`opts_GetOpt "--mice_lowpass" $@`
flirt_ref=`opts_GetOpt "--flirt_ref" $@`
volumes=`opts_GetOpt "--mice_volumes" $@`

# check required parameters
if [[ -z $work_dir ]]; then echo "ERROR: Work directory is not set!"; exit 1; fi
if [[ -z $bold ]]; then echo "ERROR: BOLD missing!"; exit 1; fi

# default values
if [[ -z $bias_field_correction ]]; then bias_field_correction="yes"; fi
if [[ -z $melodic_anatfile ]]; then melodic_anatfile="${mice_templates}/EPI_brain"; fi
if [[ -z $fix_rdata ]]; then fix_rdata="${mice_templates}/zerbi_2015_neuroimage.RData"; fi
if [[ -z $fix_threshold ]]; then fix_threshold=20; fi
if [[ -z $highpass ]]; then highpass=0.01; fi
# calculate fix_highpass
fix_highpass=$(bc <<< "scale=2;$highpass * 10000")
if [[ -z $flirt_ref ]]; then flirt_ref="${mice_templates}/EPI_template.nii.gz"; fi
if [[ -z $lowpass ]]; then lowpass=0.25; fi
if [[ -z $volumes ]]; then volumes=900; fi


# list parameters
echo ""
echo " ---> Executing preprocess_mice:"
echo "       Work directory: ${work_dir}"
echo "       BOLD: ${bold}"
echo "       Bias field correction: ${bias_field_correction}"
echo "       FIX RData file: ${fix_rdata}"
echo "       FIX threshold: ${fix_threshold}"
echo "       Highpass: ${highpass}"
echo "       Lowpass: ${lowpass}"
echo "       FLIRT reference: ${flirt_ref}"
echo "       Volumes: ${volumes}"

# flags
motion_cleanup=" -m"
if [[ -n $fix_no_motion_cleanup ]]; then 
    motion_cleanup="";
    echo "       Motion cleanup: no"
else
    echo "       Motion cleanup: yes"
fi

aggressive_cleanup=""
if [[ -n $fix_aggressive_cleanup ]]; then
    aggressive_cleanup="-A";
    echo "       Aggressive cleanup: yes"
else
    echo "       Aggressive cleanup: no"
fi

echo ""

# go to work dir and set user - required by feat
pushd ${work_dir}
if [[ -z $USER ]]; then
    export USER=`whoami`
fi

# ------------------------------------------------------------------------------
# -- BIAS FIELD CORRECTION
# ------------------------------------------------------------------------------
if [[ $bias_field_correction == "yes" ]]; then
    echo ""
    echo " ---> Starting BIAS FIELD CORRECTION"
    N4BiasFieldCorrection -d 4 -i ${work_dir}/${bold}_DS.nii.gz -o ${work_dir}/${bold}_BC.nii.gz
    bold_suffix="BC"
    echo " ---> BIAS FIELD CORRECTION completed"
else
    bold_suffix="DS"
fi


# ------------------------------------------------------------------------------
# -- MELODIC
# ------------------------------------------------------------------------------
echo ""
echo " ---> Starting MELODIC"

# set variables
melodic_output="${work_dir}/${bold}_melodic_output"
ica_dir="${melodic_output}.ica"

# remove the previous dir if it exists
if [[ -d ${ica_dir} ]]; then rm -rf ${ica_dir}; fi

# copy the fsf file
cp ${mice_templates}/rsfMRI_Standard.fsf ${work_dir}/${bold}_rsfMRI_Standard.fsf

# inject varibale values into the fsf file
for i in "${work_dir}/${bold}_rsfMRI_Standard.fsf"; do
    sed -e 's@OUTPUT@'${melodic_output}'@g' \
    -e 's@ANATFILE@'${melodic_anatfile}'@g' \
    -e 's@VOLUMES@'${volumes}'@g' \
    -e 's@FSLDIR@'${FSLDIR}'@g' \
    -e 's@DATA@'${work_dir}/${bold}_${bold_suffix}'@g' <$i> ${work_dir}/${bold}_${bold_suffix}.fsf
done

# feat
echo " ... Running feat ${work_dir}/${bold}_${bold_suffix}.fsf"
feat ${work_dir}/${bold}_${bold_suffix}.fsf

echo " ---> MELODIC completed"


# ------------------------------------------------------------------------------
# -- FIX the data
# ------------------------------------------------------------------------------
echo ""
echo " ---> Running FIX"
echo " ... Running fix ${ica_dir} ${fix_rdata} ${fix_threshold}${motion_cleanup} -h ${fix_highpass} ${aggressive_cleanup}"
fix ${ica_dir} ${fix_rdata} ${fix_threshold}${motion_cleanup} -h ${fix_highpass} ${aggressive_cleanup}


# ------------------------------------------------------------------------------
# -- QC
# ------------------------------------------------------------------------------
echo ""
echo " ---> Copying registrations to the QC folder"

# create QC dir
if [[ ! -d ${work_dir}/QC ]]; then
    mkdir ${work_dir}/QC
fi

# copy the registration
cp ${ica_dir}/reg/example_func2highres.png ${work_dir}/QC/${bold}_example_func2highres.png
echo " ---> You can check the registrations in ${work_dir}/QC"


# ------------------------------------------------------------------------------
# -- apply registrations
# ------------------------------------------------------------------------------
echo ""
echo " ---> Applying registrations"
echo " ... Running flirt -in ${ica_dir}/filtered_func_data_clean.nii.gz -ref ${flirt_ref} -out ${work_dir}/${bold}_filtered_func_data_clean_BP_EPI.nii.gz -init ${ica_dir}/reg/example_func2highres.mat -applyxfm"
flirt -in ${ica_dir}/filtered_func_data_clean.nii.gz -ref ${flirt_ref} -out ${work_dir}/${bold}_filtered_func_data_clean_BP_EPI.nii.gz -init ${ica_dir}/reg/example_func2highres.mat -applyxfm


# ------------------------------------------------------------------------------
# -- bandpass
# ------------------------------------------------------------------------------
echo ""
echo " ---> Applying bandpass"
if [[ -f ${work_dir}/${bold}_filtered_func_data_clean_BP+orig.BRIK ]]; then
    rm ${work_dir}/${bold}_filtered_func_data_clean_BP+orig.BRIK
fi
if [[ -f ${work_dir}/${bold}_filtered_func_data_clean_BP+orig.HEAD ]]; then
    rm ${work_dir}/${bold}_filtered_func_data_clean_BP+orig.HEAD
fi
echo " ... Running 3dBandpass -despike -prefix ${work_dir}/${bold}_filtered_func_data_clean_BP ${highpass} ${lowpass} ${work_dir}/${bold}_filtered_func_data_clean_BP_EPI.nii.gz"
3dBandpass -despike -prefix ${work_dir}/${bold}_filtered_func_data_clean_BP ${highpass} ${lowpass} ${work_dir}/${bold}_filtered_func_data_clean_BP_EPI.nii.gz


# ------------------------------------------------------------------------------
# -- transform to nifti
# ------------------------------------------------------------------------------
echo ""
echo " ---> Transforming to nifti"
echo " ... Running 3dAFNItoNIFTI -prefix ${work_dir}/${bold}_filtered_func_data_clean_BP.nii.gz ${work_dir}/${bold}_filtered_func_data_clean_BP+orig.BRIK"
3dAFNItoNIFTI -prefix ${work_dir}/${bold}_filtered_func_data_clean_BP.nii.gz ${work_dir}/${bold}_filtered_func_data_clean_BP+orig.BRIK


# ------------------------------------------------------------------------------
# -- Registration to Allen space
# ------------------------------------------------------------------------------
echo ""
echo " ---> Registering to Allen space"
echo " ... Running WarpTimeSeriesImageMultiTransform 4 ${work_dir}/${bold}_filtered_func_data_clean_BP.nii.gz ${work_dir}/${bold}_filtered_func_data_clean_BP_ABI.nii.gz -R ${mice_templates}/ABI_template_2021_200um.nii ${mice_templates}/EPI_to_ABI_warp.nii.gz ${mice_templates}/EPI_to_ABI_affine.txt"
WarpTimeSeriesImageMultiTransform 4 ${work_dir}/${bold}_filtered_func_data_clean_BP_EPI.nii.gz ${work_dir}/${bold}_filtered_func_data_clean_BP_ABI.nii.gz -R ${mice_templates}/ABI_template_2021_200um.nii ${mice_templates}/EPI_to_ABI_warp.nii.gz ${mice_templates}/EPI_to_ABI_affine.txt


# ------------------------------------------------------------------------------
# -- wrap up
# ------------------------------------------------------------------------------
echo " ---> Removing intermediate files"
rm ${work_dir}/${bold}_rsfMRI_Standard.fsf
rm ${work_dir}/${bold}_${bold_suffix}.fsf
rm ${work_dir}/${bold}*_BP+orig.BRIK
rm ${work_dir}/${bold}*_BP+orig.HEAD
rm ${work_dir}/${bold}*_BP.nii.gz

# go back to start dir
popd

echo ""
echo " ---> preprocess_mice successfully completed"
echo ""
echo "------------------------ Successful completion of work ------------------------"
echo ""
exit 0
