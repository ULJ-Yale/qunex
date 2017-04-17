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
#  Wrapper for isolating thalamic nuclei from the FSL thalamic atlss
#
# ## License
#
# * The isolatethalalamusfslnuclei.sh = the "Software"
# * This Software is distributed "AS IS" without warranty of any kind, either 
# * expressed or implied, including, but not limited to, the implied warranties
# * of merchantability and fitness for a particular purpose.
#
# ### TODO
#
# ## Description 
#   
# This script, isolatethalalamusfslnuclei.sh, isolates individual thalamic nuclei from 
# the FSL atlas
# 
# ## Prerequisite Installed Software
#
# * AFNI
# * Workbench
#
# ## Prerequisite Environment Variables
#
# $TOOLS pointing to the location of MNAP package
#
# ### Expected Previous Processing
# 
# * N/A
# * Outputs stored in: ${TOOLS}/MNAP/general/templates/Thalamus_Atlas
#
#~ND~END~

# ------------------------------------------------------------------------------
#  Setup color outputs
# ------------------------------------------------------------------------------

reho() {
    echo -e "\033[31m $1 \033[0m"
}

geho() {
    echo -e "\033[32m $1 \033[0m"
}

# ------------------------------------------------------------------------------------------------------
#  isolatethalamusfslnuclei - Find thalamic ROIs needed for subcortical seed-based tractography via FSL
# ------------------------------------------------------------------------------------------------------

show_usage() {
				echo ""
				echo "-- DESCRIPTION:"
				echo ""
				echo "This script, isolatethalalamusfslnuclei.sh, isolates individual thalamic nuclei from the FSL atlas."
				echo "It explicitly assumes the the Human Connectome Project folder structure for preprocessing: "
				echo ""
				echo "INPUTS: ${TOOLS}/MNAP/general/templates/Thalamus_Atlas"
				echo ""
				echo ""
				echo "OUTPUTS: "
				echo "         ${TOOLS}/MNAP/general/templates/Thalamus_Atlas"
				echo ""
				echo ""	
}

######################################### DO WORK ##########################################

isolatethalamusfslnuclei() {

	# isolate overal thalamus in MNI template space
	
	# isolate left thalamus from global mask file
    3dcalc -overwrite -a ${TOOLS}/MNAP/general/templates/Atlas_ROIs.2.nii.gz -expr 'equals(a,10)' -prefix ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Atlas_thalamus.L.nii.gz 
    # isolate right thalamus from global mask file
	3dcalc -overwrite -a ${TOOLS}/MNAP/general/templates/Atlas_ROIs.2.nii.gz -expr 'equals(a,49)' -prefix ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Atlas_thalamus.R.nii.gz
	# merge L+R thalamus
	3dcalc -overwrite -a ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Atlas_thalamus.R.nii.gz -b ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Atlas_thalamus.L.nii.gz -expr 'a+b' -prefix ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Atlas_thalamus.LR.nii.gz 
    
	# FSL thalamus values and labels
	#	thalamus_motor (1) SENS
	#	thalamus_sens (2) SENS
	#	thalamus_occ (3) SENS
	#	thalamus_pfc (4) ASSOC
	#	thalamus_premotor (5) ASSOC
	#	thalamus_parietal (6) ASSOC
	#	thalamus_temporal (7) SENS

	echo "Mask FSL Thalamic atlas with the CIFTI-based subcortical atlas template..."
	
	# first binarize the subcortical Atlas from a sample subject
	3dcalc -overwrite -a ${TOOLS}/MNAP/general/templates/Atlas_ROIs.2.nii.gz -expr 'step(a)' -prefix ${TOOLS}/MNAP/general/templates/Atlas_ROIs.2.Binary.nii
	# compute logical AND (overlap) between the FSL atlas and CIFTI space
	3dcalc -overwrite -a ${TOOLS}/MNAP/general/templates/Atlas_ROIs.2.Binary.nii -b ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.nii.gz -expr 'a*b' -prefix ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked.nii

	echo "Isolate FSL-intersecting thalamic voxels..."
	
	# isolate individual thalamic nuclei from the FSL atlas
	3dcalc -overwrite -x ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked.nii -expr 'within(x,0.5,1.5)' -prefix ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Motor.nii
	3dcalc -overwrite -x ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked.nii -expr 'within(x,1.5,2.5)' -prefix ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Sensory.nii
	3dcalc -overwrite -x ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked.nii -expr 'within(x,2.5,3.5)' -prefix ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Occipital.nii
	3dcalc -overwrite -x ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked.nii -expr 'within(x,3.5,5.5)' -prefix ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Prefrontal.nii
	3dcalc -overwrite -x ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked.nii -expr 'within(x,4.5,4.5)' -prefix ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Premotor.nii
	3dcalc -overwrite -x ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked.nii -expr 'within(x,5.5,6.5)' -prefix ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Parietal.nii
	3dcalc -overwrite -x ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked.nii -expr 'within(x,6.5,7.5)' -prefix ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Temporal.nii

	# Combine individual thalamic nuclei from the FSL atlas into associative nuclei
	3dcalc -overwrite -a ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Parietal.nii \
	-b ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Prefrontal.nii \
	-c ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Premotor.nii \
	-expr 'a+b+c' \
	-prefix ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Associative.nii
	
	# Combine individual thalamic nuclei from the FSL atlas into associative nuclei
	3dcalc -overwrite -a ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Motor.nii \
	-b ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Sensory.nii \
	-c ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Occipital.nii \
	-d ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Temporal.nii \
	-expr 'a+b+c+d' \
	-prefix ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-SomatomotorSensory.nii

	# Zero out surface data (saved in MNAP templates) 
	wb_command -metric-math 'a-1' ${TOOLS}/MNAP/general/templates/surface.L.mask.cifti.allvalueszero.32k_fs_LR.func.gii -var a ${TOOLS}/MNAP/general/templates/surface.L.mask.cifti.allvaluesone.32k_fs_LR.func.gii
	wb_command -metric-math 'a-1' ${TOOLS}/MNAP/general/templates/surface.R.mask.cifti.allvalueszero.32k_fs_LR.func.gii -var a ${TOOLS}/MNAP/general/templates/surface.R.mask.cifti.allvaluesone.32k_fs_LR.func.gii
	# construct new dense scalar file
	wb_command -cifti-create-dense-from-template ${TOOLS}/MNAP/general/templates/structures.allvaluesone.dtseries.nii ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked.dscalar.nii -volume-all ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked.nii -metric CORTEX_LEFT ${TOOLS}/MNAP/general/templates/surface.L.mask.cifti.allvaluesone.32k_fs_LR.func.gii -metric CORTEX_RIGHT ${TOOLS}/MNAP/general/templates/surface.R.mask.cifti.allvaluesone.32k_fs_LR.func.gii
	# change mapping to dtseries 
	wb_command -cifti-change-mapping ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked.dscalar.nii ROW ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked.dtseries.nii -series 1 1

	# -- Construct CIFTI averages for Associative
 	# construct new dense scalar file
 	wb_command -cifti-create-dense-from-template ${TOOLS}/MNAP/general/templates/structures.allvaluesone.dtseries.nii ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Associative.dscalar.nii -volume-all ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Associative.nii -metric CORTEX_LEFT ${TOOLS}/MNAP/general/templates/surface.L.mask.cifti.allvaluesone.32k_fs_LR.func.gii -metric CORTEX_RIGHT ${TOOLS}/MNAP/general/templates/surface.R.mask.cifti.allvaluesone.32k_fs_LR.func.gii
 	# change mapping to dtseries 
 	wb_command -cifti-change-mapping ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Associative.dscalar.nii ROW ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-Associative.dtseries.nii -series 1 1
    
	# -- Construct CIFTI averages for Associative
 	# construct new dense scalar file
 	wb_command -cifti-create-dense-from-template ${TOOLS}/MNAP/general/templates/structures.allvaluesone.dtseries.nii ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-SomatomotorSensory.dscalar.nii -volume-all ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-SomatomotorSensory.nii -metric CORTEX_LEFT ${TOOLS}/MNAP/general/templates/surface.L.mask.cifti.allvaluesone.32k_fs_LR.func.gii -metric CORTEX_RIGHT ${TOOLS}/MNAP/general/templates/surface.R.mask.cifti.allvaluesone.32k_fs_LR.func.gii
 	# change mapping to dtseries 
 	wb_command -cifti-change-mapping ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-SomatomotorSensory.dscalar.nii ROW ${TOOLS}/MNAP/general/templates/Thalamus_Atlas/Thalamus-maxprob-thr25-2mm.AtlasMasked-SomatomotorSensory.dtseries.nii -series 1 1

}

#
# Invoke the main function to get things started
#

# Check if help is specified
#

if [ "$1" == "help" ] || [ "$1" == "-help" ] || [ "$1" == "--help" ] || [ "$1" == "--h" ] || [ "$1" == "-h" ]; then
    show_usage
	exit 1
else
	isolatethalamusfslnuclei
fi