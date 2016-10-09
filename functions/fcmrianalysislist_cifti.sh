#!/bin/sh
#set -x

########################################################
############build analysis list for fcMRI ##############
########################################################

### Hi-pass filtered versions for regular seed connectivity & GBC with SMOOTHING

echo subject id:"$CASE" >> subjects."$GROUP".GSR.udvarsme.surface.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_g7_hpss_res-mVWMWB1d.dtseries.nii >> subjects."$GROUP".GSR.udvarsme.surface.list

echo subject id:"$CASE" >> subjects."$GROUP".noGSR.udvarsme.surface.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_g7_hpss_res-mVWM1d.dtseries.nii >> subjects."$GROUP".noGSR.udvarsme.surface.list


### Hi-pass filtered versions for regular seed connectivity & GBC w/o SMOOTHING

echo subject id:"$CASE" >> subjects."$GROUP".GSR.nosmooth.udvarsme.surface.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_hpss_res-mVWMWB1d.dtseries.nii >> subjects."$GROUP".GSR.nosmooth.udvarsme.surface.list

echo subject id:"$CASE" >> subjects."$GROUP".noGSR.nosmooth.udvarsme.surface.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_hpss_res-mVWM1d.dtseries.nii >> subjects."$GROUP".noGSR.nosmooth.udvarsme.surface.list


### Lo-pass filtered versions for GBC w/ SMOOTHING

echo subject id:"$CASE" >> subjects."$GROUP".gbc.GSR.lpss.udvarsme.surface.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_g7_hpss_res-mVWMWB1d_lpss.dtseries.nii >> subjects."$GROUP".gbc.GSR.lpss.udvarsme.surface.list

echo subject id:"$CASE" >> subjects."$GROUP".gbc.noGSR.lpss.udvarsme.surface.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_g7_hpss_res-mVWM1d_lpss.dtseries.nii >> subjects."$GROUP".gbc.noGSR.lpss.udvarsme.surface.list


### Lo-pass filtered versions for GBC w/o SMOOTHING

echo subject id:"$CASE" >> subjects."$GROUP".gbc.GSR.nosmooth.lpss.udvarsme.surface.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_hpss_res-mVWMWB1d_lpss.dtseries.nii >> subjects."$GROUP".gbc.GSR.nosmooth.lpss.udvarsme.surface.list

echo subject id:"$CASE" >> subjects."$GROUP".gbc.noGSR.nosmooth.lpss.udvarsme.surface.list
echo file:"$StudyFolder"/"$CASE"/images/functional/bold1_hpss_res-mVWM1d_lpss.dtseries.nii >> subjects."$GROUP".gbc.noGSR.nosmooth.lpss.udvarsme.surface.list


### PARCELLATED LISTS

echo subject id:"$CASE" >> subjects."$GROUP".noGSR.nosmooth.lpss.udvarsme.surface.pconn.list
echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold1_hpss_res-mVWM1d_lpss_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii >> subjects."$GROUP".noGSR.nosmooth.lpss.udvarsme.surface.pconn.list

echo subject id:"$CASE" >> subjects."$GROUP".GSR.nosmooth.lpss.udvarsme.surface.pconn.list
echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold1_hpss_res-mVWMWB1d_lpss_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii >> subjects."$GROUP".GSR.nosmooth.lpss.udvarsme.surface.pconn.list

echo subject id:"$CASE" >> subjects."$GROUP".noGSR.nosmooth.udvarsme.surface.pconn.list
echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold1_hpss_res-mVWM1d_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii >> subjects."$GROUP".noGSR.nosmooth.udvarsme.surface.pconn.list

echo subject id:"$CASE" >> subjects."$GROUP".GSR.nosmooth.udvarsme.surface.pconn.list
echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold1_hpss_res-mVWMWB1d_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii >> subjects."$GROUP".GSR.nosmooth.udvarsme.surface.pconn.list

echo subject id:"$CASE" >> subjects."$GROUP".noGSR.nosmooth.lpss.udvarsme.surface.pconn.list
echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold1_hpss_res-mVWM1d_lpss_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii >> subjects."$GROUP".noGSR.nosmooth.lpss.udvarsme.surface.pconn.list

echo subject id:"$CASE" >> subjects."$GROUP".GSR.nosmooth.lpss.udvarsme.surface.pconn.list
echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold1_hpss_res-mVWMWB1d_lpss_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii >> subjects."$GROUP".GSR.nosmooth.lpss.udvarsme.surface.pconn.list

echo subject id:"$CASE" >> subjects."$GROUP".noGSR.nosmooth.udvarsme.surface.pconn.list
echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold1_hpss_res-mVWM1d_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii >> subjects."$GROUP".noGSR.nosmooth.udvarsme.surface.pconn.list

echo subject id:"$CASE" >> subjects."$GROUP".GSR.nosmooth.udvarsme.surface.pconn.list
echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold1_hpss_res-mVWMWB1d_LR_Yeo2011_17Networks.32k_fs_LR.pconn.nii >> subjects."$GROUP".GSR.nosmooth.udvarsme.surface.pconn.list



