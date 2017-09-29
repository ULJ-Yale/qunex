#!/bin/sh
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## Copyright Notice
#
# Copyright (C)
#
# * Yale University
#
# ## Author(s)
#
# * Alan Anticevic, N3 Division, Yale University
#
# ## Product
#
#  analysis list generation wrapper
#
# ## License
#
# * The AnalysisList.sh = the "Software"
# * This Software is distributed "AS IS" without warranty of any kind, either 
# * expressed or implied, including, but not limited to, the implied warranties
# * of merchantability and fitness for a particular purpose.
#
# ### TODO
#
# ## Prerequisite Installed Software
#
#
# ## Prerequisite Environment Variables
#
#
# ### Expected Previous Processing
# 
# * The necessary input files are BOLD data from previous processing
# * These data are stored in: "$StudyFolder/subjects/$CASE/images/
#
#~ND~END~

# -------------------------------------------------
# ------------ Set ListPath variable --------------
# -------------------------------------------------
		
	
	if [ -z "$ListPath" ]; then 
		unset ListPath
		mkdir "$StudyFolder"/../processing/lists &> /dev/null
		cd ${StudyFolder}/../processing/lists
		ListPath=`pwd`
		reho "Setting default path for list folder --> $ListPath"
	fi
	
# -------------------------------------------------
# --- Code for generating analysis list files -----
# -------------------------------------------------

# -- Hi-pass filtered versions for regular seed connectivity & GBC with SMOOTHING

echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".GSR.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_g7_hpss_res-mVWMWB1d."$FileType" >> "$ListPath"/subjects.analysis."$ListName".GSR.udvarsme.surface.list
done

echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".noGSR.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_g7_hpss_res-mVWM1d."$FileType" >> "$ListPath"/subjects.analysis."$ListName".noGSR.udvarsme.surface.list
done

# -- Hi-pass filtered versions for regular seed connectivity & GBC w/o SMOOTHING

echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".GSR.nosmooth.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_hpss_res-mVWMWB1d."$FileType" >> "$ListPath"/subjects.analysis."$ListName".GSR.nosmooth.udvarsme.surface.list
done

echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".noGSR.nosmooth.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_hpss_res-mVWM1d."$FileType" >> "$ListPath"/subjects.analysis."$ListName".noGSR.nosmooth.udvarsme.surface.list
done

# -- Lo-pass filtered versions for GBC w/ SMOOTHING

echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".gbc.GSR.lpss.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_g7_hpss_res-mVWMWB1d_lpss."$FileType" >> "$ListPath"/subjects.analysis."$ListName".gbc.GSR.lpss.udvarsme.surface.list
done

echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".gbc.noGSR.lpss.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_g7_hpss_res-mVWM1d_lpss."$FileType" >> "$ListPath"/subjects.analysis."$ListName".gbc.noGSR.lpss.udvarsme.surface.list
done

# -- Lo-pass filtered versions for GBC w/o SMOOTHING

echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".gbc.GSR.nosmooth.lpss.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_hpss_res-mVWMWB1d_lpss."$FileType" >> "$ListPath"/subjects.analysis."$ListName".gbc.GSR.nosmooth.lpss.udvarsme.surface.list
done

echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".gbc.noGSR.nosmooth.lpss.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_hpss_res-mVWM1d_lpss."$FileType" >> "$ListPath"/subjects.analysis."$ListName".gbc.noGSR.nosmooth.lpss.udvarsme.surface.list
done

# ---------------------------------
# -- GENERATE PARCELLATED LISTS
# ---------------------------------


if [ -n "$ParcellationFile" ]; then 

	echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".noGSR.nosmooth.lpss.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWM1d_lpss_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/subjects.analysis."$ListName".noGSR.nosmooth.lpss.udvarsme.surface."$ParcellationFile".list
	done
	
	echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".GSR.nosmooth.lpss.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWMWB1d_lpss_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/subjects.analysis."$ListName".GSR.nosmooth.lpss.udvarsme.surface."$ParcellationFile".list
	done
	
	echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".noGSR.nosmooth.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWM1d_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/subjects.analysis."$ListName".noGSR.nosmooth.udvarsme.surface."$ParcellationFile".list
	done
	
	echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".GSR.nosmooth.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWMWB1d_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/subjects.analysis."$ListName".GSR.nosmooth.udvarsme.surface."$ParcellationFile".list
	done
	
	echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".noGSR.nosmooth.lpss.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWM1d_lpss_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/subjects.analysis."$ListName".noGSR.nosmooth.lpss.udvarsme.surface."$ParcellationFile".list
	done
	
	echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".GSR.nosmooth.lpss.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWMWB1d_lpss_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/subjects.analysis."$ListName".GSR.nosmooth.lpss.udvarsme.surface."$ParcellationFile".list
	done
	
	echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".noGSR.nosmooth.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWM1d_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/subjects.analysis."$ListName".noGSR.nosmooth.udvarsme.surface."$ParcellationFile".list
	done
	
	echo subject id:"$CASE" >> "$ListPath"/subjects.analysis."$ListName".GSR.nosmooth.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWMWB1d_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/subjects.analysis."$ListName".GSR.nosmooth.udvarsme.surface."$ParcellationFile".lists
	done

fi