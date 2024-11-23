#!/bin/bash
#
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## Author(s)
#
# Originally developed by Stam Sotiropoulos (Oxford)
# Modified by Alan Anticevic for PBS and SLURM compatibility via QuNex code (07/01/2017)
#
# ## Product
#
#  Wrapper for RunMatrix1 GPU without scheduler specification
#
# ## Description 
#   
# This script, run_matrix1ents gpu-based probtracX
# 
# ## Prerequisite Installed Software
#
# * FSL with GPU binaries
#
# ## Prerequisite Environment Variables
#
#
# ### Expected Previous Processing
# 
# * The necessary input files are DWI data from previous processing
# * These data are stored in: "$SessionsFolder/$CASE/hcp/$CASE/T1w/Diffusion.bedpostX/ 
#
#~ND~END~

# -- Define paths
scriptsdir=$HCPPIPEDIR_dMRITractFull/tractography_gpu_scripts
TemplateFolder=$QUNEXLIBRARYETC/diffusion_tractography_dense/templates

# -- Check inputs
if [ "$2" == "" ];then
    echo ""
    echo "usage: $0 <SessionsFolder> <Session> <Number_of_Samples> <Scheduler>"
    echo ""
    exit 1
fi

# input parameters
SessionsFolder=$1 # "$1" #Path to Generic Study folder
Session=$2 # "$2" #SessionID
Nsamples=$3 # "$3" #Number of Samples to compute

# -- distance correction flag
distance_correction=$4
if [ "$distance_correction" == "yes" ]; then
    distance_correction_flag="--pd"
else
    distance_correction_flag=""
fi

# -- store streamlines length flag
store_streamlines_length=$5
if [ "$store_streamlines_length" == "yes" ]; then
    store_streamlines_length_flag="--ompl"
else
    store_streamlines_length_flag=""
fi

# -- nogpu
nogpu=$6

# Out name
OutFileName="Conn1.dconn.nii"

# -- Generate folder structure
ResultsFolder="$SessionsFolder"/"$Session"/hcp/"$Session"/MNINonLinear/Results/Tractography
RegFolder="$SessionsFolder"/"$Session"/hcp/"$Session"/MNINonLinear/xfms
ROIsFolder="$SessionsFolder"/"$Session"/hcp/"$Session"/MNINonLinear/ROIs
if [ ! -e ${ResultsFolder} ] ; then
  mkdir -p ${ResultsFolder}
fi

# -- Use BedpostX samples
BedpostxFolder="$SessionsFolder"/"$Session"/hcp/"$Session"/T1w/Diffusion.bedpostX
DtiMask=$BedpostxFolder/nodif_brain_mask

# -- Clean prior results
rm -rf $ResultsFolder/stop
rm -rf $ResultsFolder/wtstop
rm -rf $ResultsFolder/volseeds
rm -rf $ResultsFolder/Mat1_seeds

# -- Temporarily here, should be in Prepare_Seeds
echo $ResultsFolder/CIFTI_STRUCTURE_ACCUMBENS_LEFT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_ACCUMBENS_RIGHT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_AMYGDALA_LEFT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_AMYGDALA_RIGHT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_BRAIN_STEM >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_CAUDATE_LEFT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_CAUDATE_RIGHT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_CEREBELLUM_LEFT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_CEREBELLUM_RIGHT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_DIENCEPHALON_VENTRAL_LEFT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_DIENCEPHALON_VENTRAL_RIGHT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_HIPPOCAMPUS_LEFT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_HIPPOCAMPUS_RIGHT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_PALLIDUM_LEFT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_PALLIDUM_RIGHT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_PUTAMEN_LEFT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_PUTAMEN_RIGHT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_THALAMUS_LEFT >> $ResultsFolder/volseeds
echo $ResultsFolder/CIFTI_STRUCTURE_THALAMUS_RIGHT >> $ResultsFolder/volseeds

# -- Define Generic Options
generic_options=" --loopcheck --forcedir --fibthresh=0.01 --cthr=0.2 --sampvox=2 --randfib=1 --nsamples=${Nsamples} --nsteps=2000 --steplength=0.5 $distance_correction_flag $store_streamlines_length_flag"
o=" --samples=$BedpostxFolder/merged --mask=$DtiMask --meshspace=caret"

# -- Define Seed
echo $ResultsFolder/white.L.asc >> $ResultsFolder/Mat1_seeds
echo $ResultsFolder/white.R.asc >> $ResultsFolder/Mat1_seeds
cat $ResultsFolder/volseeds >> $ResultsFolder/Mat1_seeds
Seed="$ResultsFolder/Mat1_seeds"
StdRef=$FSLDIR/data/standard/MNI152_T1_2mm_brain_mask
o=" $o --seed=$Seed --seedref=$StdRef"
o=" $o --xfm=`echo $RegFolder/standard2acpc_dc` --invxfm=`echo $RegFolder/acpc_dc2standard`"

# -- Define Termination and Waypoint Masks
echo $ResultsFolder/pial.L.asc >> $ResultsFolder/stop      # -- Pial Surface as Stop Mask
echo $ResultsFolder/pial.R.asc >> $ResultsFolder/stop
echo $ResultsFolder/CIFTI_STRUCTURE_ACCUMBENS_LEFT >> $ResultsFolder/wtstop    # -- WM boundary Surface and subcortical volumes as Wt_Stop Masks
echo $ResultsFolder/CIFTI_STRUCTURE_ACCUMBENS_RIGHT >> $ResultsFolder/wtstop   # -- Exclude Brainstem and diencephalon, otherwise cortico-cerebellar connections are stopped!
echo $ResultsFolder/CIFTI_STRUCTURE_AMYGDALA_LEFT >> $ResultsFolder/wtstop
echo $ResultsFolder/CIFTI_STRUCTURE_AMYGDALA_RIGHT >> $ResultsFolder/wtstop
echo $ResultsFolder/CIFTI_STRUCTURE_CAUDATE_LEFT >> $ResultsFolder/wtstop
echo $ResultsFolder/CIFTI_STRUCTURE_CAUDATE_RIGHT >> $ResultsFolder/wtstop
echo $ResultsFolder/CIFTI_STRUCTURE_CEREBELLUM_LEFT >> $ResultsFolder/wtstop
echo $ResultsFolder/CIFTI_STRUCTURE_CEREBELLUM_RIGHT >> $ResultsFolder/wtstop
echo $ResultsFolder/CIFTI_STRUCTURE_HIPPOCAMPUS_LEFT >> $ResultsFolder/wtstop
echo $ResultsFolder/CIFTI_STRUCTURE_HIPPOCAMPUS_RIGHT >> $ResultsFolder/wtstop
echo $ResultsFolder/CIFTI_STRUCTURE_PALLIDUM_LEFT >> $ResultsFolder/wtstop
echo $ResultsFolder/CIFTI_STRUCTURE_PALLIDUM_RIGHT >> $ResultsFolder/wtstop
echo $ResultsFolder/CIFTI_STRUCTURE_PUTAMEN_LEFT >> $ResultsFolder/wtstop
echo $ResultsFolder/CIFTI_STRUCTURE_PUTAMEN_RIGHT >> $ResultsFolder/wtstop
echo $ResultsFolder/CIFTI_STRUCTURE_THALAMUS_LEFT >> $ResultsFolder/wtstop
echo $ResultsFolder/CIFTI_STRUCTURE_THALAMUS_RIGHT >> $ResultsFolder/wtstop
echo $ResultsFolder/white.L.asc >> $ResultsFolder/wtstop
echo $ResultsFolder/white.R.asc >> $ResultsFolder/wtstop
o=" $o --stop=${ResultsFolder}/stop --wtstop=$ResultsFolder/wtstop --forcefirststep"  # -- Should we include an exclusion along the midsagittal plane (without the CC and the commisures)?
o=" $o --waypoints=${ROIsFolder}/Whole_Brain_Trajectory_ROI_2"       # -- Use a waypoint to exclude streamlines that go through CSF 

# -- Define Targets
o=" $o --omatrix1"

# ----------------------------------------------------------
# ------------------ Matrix Commands -----------------------
# ----------------------------------------------------------

# -- Clean prior results, specify commands and make executable
rm -f $ResultsFolder/commands_Mat1.sh &> /dev/null
rm -rf $ResultsFolder/Mat1_logs
mkdir -p $ResultsFolder/Mat1_logs
out=" --dir=$ResultsFolder"

if [[ ${nogpu} == "yes" ]]; then
    probtrack_bin=${FSLBINDIR}/probtrackx2
else
    probtrack_bin=${FSLBINDIR}/probtrackx2_gpu${DEFAULT_CUDA_VERSION}
fi

echo $probtrack_bin $generic_options $o $out  >> $ResultsFolder/commands_Mat1.sh
chmod 770 $ResultsFolder/commands_Mat1.sh

# -- Do Tractography (N100: ~5h, 50GB RAM)
echo ""
echo "-- Queueing Probtrackx"
echo ""

# -- Execute commands_Mat1 file
bash ${ResultsFolder}/commands_Mat1.sh ########## <<< commands_Mat1.sh

# ----------------------------------------------------------
# --------------- POST Matrix Commands ---------------------
# ----------------------------------------------------------

# -- Create CIFTI file=Mat1+Mat1_transp (~1.5 hours, 50GB RAM)
echo ""
echo "-- Queueing Post-Matrix 1 Calls" 
echo ""

# -- Clean prior results, specify commands and make executable
PostProcMatrixCommand="${scriptsdir}/post_proc_matrix1.sh ${SessionsFolder} ${Session} ${TemplateFolder} ${OutFileName}"
rm -f $ResultsFolder/postcommands_Mat1.sh &> /dev/null
echo "${PostProcMatrixCommand}" >> $ResultsFolder/postcommands_Mat1.sh
chmod 770 $ResultsFolder/postcommands_Mat1.sh

# -- Execute PostProcMatrixCommand call
bash ${ResultsFolder}/postcommands_Mat1.sh ########## <<< postcommands_Mat1.sh

echo ""
echo "-- Matrix 1 Probtrackx Completed successfully."
echo ""
