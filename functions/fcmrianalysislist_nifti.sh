#!/bin/sh
#set -x

########################################################
############build analysis list for fcMRI ##############
########################################################

### Hi-pass filtered versions for regular seed connectivity & GBC with SMOOTHING

echo subject id:"$CASE" >> subjects."$GROUP".GSR.udvarsme.volume.list
echo roi:"$StudyFolder"/"$CASE"/images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz >> subjects."$GROUP".GSR.udvarsme.volume.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_g7_hpss_res-mVWMWB1d.nii.gz >> subjects."$GROUP".GSR.udvarsme.volume.list

echo subject id:"$CASE" >> subjects."$GROUP".noGSR.udvarsme.volume.list
echo roi:"$StudyFolder"/"$CASE"/images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz >> subjects."$GROUP".GSR.udvarsme.volume.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_g7_hpss_res-mVWM1d.nii.gz >> subjects."$GROUP".noGSR.udvarsme.volume.list


### Hi-pass filtered versions for regular seed connectivity & GBC w/o SMOOTHING

echo subject id:"$CASE" >> subjects."$GROUP".GSR.nosmooth.udvarsme.volume.list
echo roi:"$StudyFolder"/"$CASE"/images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz >> subjects."$GROUP".GSR.udvarsme.volume.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_hpss_res-mVWMWB1d.nii.gz >> subjects."$GROUP".GSR.nosmooth.udvarsme.volume.list

echo subject id:"$CASE" >> subjects."$GROUP".noGSR.nosmooth.udvarsme.volume.list
echo roi:"$StudyFolder"/"$CASE"/images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz >> subjects."$GROUP".GSR.udvarsme.volume.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_hpss_res-mVWM1d.nii.gz >> subjects."$GROUP".noGSR.nosmooth.udvarsme.volume.list


### Lo-pass filtered versions for GBC w/ SMOOTHING

echo subject id:"$CASE" >> subjects."$GROUP".gbc.GSR.lpss.udvarsme.volume.list
echo roi:"$StudyFolder"/"$CASE"/images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz >> subjects."$GROUP".GSR.udvarsme.volume.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_g7_hpss_res-mVWMWB1d_lpss.nii.gz >> subjects."$GROUP".gbc.GSR.lpss.udvarsme.volume.list

echo subject id:"$CASE" >> subjects."$GROUP".gbc.noGSR.lpss.udvarsme.volume.list
echo roi:"$StudyFolder"/"$CASE"/images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz >> subjects."$GROUP".GSR.udvarsme.volume.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_g7_hpss_res-mVWM1d_lpss.nii.gz >> subjects."$GROUP".gbc.noGSR.lpss.udvarsme.volume.list


### Lo-pass filtered versions for GBC w/o SMOOTHING

echo subject id:"$CASE" >> subjects."$GROUP".gbc.GSR.nosmooth.lpss.udvarsme.volume.list
echo roi:"$StudyFolder"/"$CASE"/images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz >> subjects."$GROUP".GSR.udvarsme.volume.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_hpss_res-mVWMWB1d_lpss.nii.gz >> subjects."$GROUP".gbc.GSR.nosmooth.lpss.udvarsme.volume.list

echo subject id:"$CASE" >> subjects."$GROUP".gbc.noGSR.nosmooth.lpss.udvarsme.volume.list
echo roi:"$StudyFolder"/"$CASE"/images/segmentation/freesurfer/mri/aparc+aseg_bold.nii.gz >> subjects."$GROUP".GSR.udvarsme.volume.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_hpss_res-mVWM1d_lpss.nii.gz >> subjects."$GROUP".gbc.noGSR.nosmooth.lpss.udvarsme.volume.list




