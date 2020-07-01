#!/bin/sh
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## COPYRIGHT NOTICE
#
# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
#
# ## AUTHORS(s)
#
# * Alan Anticevic, N3 Division, Yale University
#
# ## PRODUCT
#
# AnalysisList.sh
#
# ## LICENSE
#
# * The AnalysisList.sh = the "Software"
# * This Software conforms to the license outlined in the Qu|Nex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ## TODO
#
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * N/A
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# * N/A
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are BOLD data from previous processing
# * These data are stored in: "$StudyFolder/sessions/$CASE/images/
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
     echo ""
     echo "-- DESCRIPTION for AnalysisList Function"
     echo ""
     echo "This function generates various analyses lists supported by the Qu|Nex Suite."
     echo ""
     echo ""
     exit 0
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]]; then
	usage
fi

# ------------------------------------------------------------------------------
# -- Parse arguments
# ------------------------------------------------------------------------------

# -- Get the command line options for this script
get_options() {

local scriptName=$(basename ${0})
local arguments=("$@")

# -- Report options
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo ""
echo ""
echo "   Running with default options... "
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""

}

# ------------------------------------------------------------------------------
# -- Check and Set ListPath variable
# ------------------------------------------------------------------------------

if [ -z "$ListPath" ]; then 
	unset ListPath
	mkdir "$StudyFolder"/../processing/lists &> /dev/null
	cd ${StudyFolder}/../processing/lists
	ListPath=`pwd`
	reho "Setting default path for list folder --> $ListPath"
fi

######################################### DO WORK ##########################################

main() {

# ------------------------------------------------------------------------------
# -- Code for generating analysis list files
# ------------------------------------------------------------------------------


# -- Hi-pass filtered versions for regular seed connectivity & GBC with SMOOTHING

echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".GSR.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_s_hpss_res-mVWMWB1d."$FileType" >> "$ListPath"/analysis."$ListName".GSR.udvarsme.surface.list
done

echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".noGSR.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_s_hpss_res-mVWM1d."$FileType" >> "$ListPath"/analysis."$ListName".noGSR.udvarsme.surface.list
done

# -- Hi-pass filtered versions for regular seed connectivity & GBC w/o SMOOTHING

echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".GSR.nosmooth.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_hpss_res-mVWMWB1d."$FileType" >> "$ListPath"/analysis."$ListName".GSR.nosmooth.udvarsme.surface.list
done

echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".noGSR.nosmooth.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_hpss_res-mVWM1d."$FileType" >> "$ListPath"/analysis."$ListName".noGSR.nosmooth.udvarsme.surface.list
done

# -- Lo-pass filtered versions for GBC w/ SMOOTHING

echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".gbc.GSR.lpss.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_s_hpss_res-mVWMWB1d_lpss."$FileType" >> "$ListPath"/analysis."$ListName".gbc.GSR.lpss.udvarsme.surface.list
done

echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".gbc.noGSR.lpss.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_s_hpss_res-mVWM1d_lpss."$FileType" >> "$ListPath"/analysis."$ListName".gbc.noGSR.lpss.udvarsme.surface.list
done

# -- Lo-pass filtered versions for GBC w/o SMOOTHING

echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".gbc.GSR.nosmooth.lpss.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_hpss_res-mVWMWB1d_lpss."$FileType" >> "$ListPath"/analysis."$ListName".gbc.GSR.nosmooth.lpss.udvarsme.surface.list
done

echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".gbc.noGSR.nosmooth.lpss.udvarsme.surface.list
for BOLD in "$BOLDS"; do
echo file:"$StudyFolder"/"$CASE"/images/functional/bold"$BOLD""$BoldSuffix"_hpss_res-mVWM1d_lpss."$FileType" >> "$ListPath"/analysis."$ListName".gbc.noGSR.nosmooth.lpss.udvarsme.surface.list
done

# ---------------------------------
# -- Generate parcellated lists
# ---------------------------------

if [ -n "$ParcellationFile" ]; then 

	echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".noGSR.nosmooth.lpss.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWM1d_lpss_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/analysis."$ListName".noGSR.nosmooth.lpss.udvarsme.surface."$ParcellationFile".list
	done
	
	echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".GSR.nosmooth.lpss.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWMWB1d_lpss_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/analysis."$ListName".GSR.nosmooth.lpss.udvarsme.surface."$ParcellationFile".list
	done
	
	echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".noGSR.nosmooth.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWM1d_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/analysis."$ListName".noGSR.nosmooth.udvarsme.surface."$ParcellationFile".list
	done
	
	echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".GSR.nosmooth.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWMWB1d_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/analysis."$ListName".GSR.nosmooth.udvarsme.surface."$ParcellationFile".list
	done
	
	echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".noGSR.nosmooth.lpss.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWM1d_lpss_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/analysis."$ListName".noGSR.nosmooth.lpss.udvarsme.surface."$ParcellationFile".list
	done
	
	echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".GSR.nosmooth.lpss.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWMWB1d_lpss_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/analysis."$ListName".GSR.nosmooth.lpss.udvarsme.surface."$ParcellationFile".list
	done
	
	echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".noGSR.nosmooth.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWM1d_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/analysis."$ListName".noGSR.nosmooth.udvarsme.surface."$ParcellationFile".list
	done
	
	echo session id:"$CASE" >> "$ListPath"/analysis."$ListName".GSR.nosmooth.udvarsme.surface.pconn.list
	for BOLD in "$BOLDS"; do
	echo file:"$StudyFolder"/Parcellated/BOLD/"$CASE"_bold"$BOLD"_hpss_res-mVWMWB1d_LR_"$ParcellationFile".pconn.nii >> "$ListPath"/analysis."$ListName".GSR.nosmooth.udvarsme.surface."$ParcellationFile".lists
	done
fi

}

echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@