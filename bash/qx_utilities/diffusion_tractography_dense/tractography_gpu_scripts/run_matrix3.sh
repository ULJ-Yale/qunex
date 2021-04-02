#!/bin/bash
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## Copyright Notice
##
# * Copyright (C) 2004 University of Oxford
# * Copyright (C) 2017 Yale University
#
# ## Author(s)
#
# Originally developed by Stam Sotiropoulos (Oxford)
# Modified by Alan Anticevic for LSF, PBS and SLURM compatibility via QuNex code (07/01/2017)
#
# ## Product
#
#  Wrapper for RunMatrix3 GPU without scheduler specification
#
# ## License
#
# * The run_matrix3.sh = the "Software"
# * This Software is distributed "AS IS" without warranty of any kind, either 
# * expressed or implied, including, but not limited to, the implied warranties
# * of merchantability and fitness for a particular purpose.
#
# ### TODO
#
# ## Description 
#   
# This script, run_matrix3.sh, implements gpu-based probtracX
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
# * These data are stored in: "$SessionsFolder/sessions/$CASE/hcp/$CASE/T1w/Diffusion.bedpostX/ 
#
#~ND~END~

# -- Check which CUDA version is being run and set where GPU probtrackx binary is # bindir=$FSLDIR/bin 
if [[ `nvcc --version | grep "release"` == *"7.5"* ]]; then bindir=${FSLGPUBinary}/probtrackx_gpu_cuda_7.5; fi
if [[ `nvcc --version | grep "release"` == *"8.0"* ]]; then bindir=${FSLGPUBinary}/probtrackx_gpu_cuda_8.0; fi
if [[ `nvcc --version | grep "release"` == *"9.1"* ]]; then bindir=${FSLGPUBinary}/probtrackx_gpu_cuda_9.1; fi

# -- Define paths
scriptsdir=$HCPPIPEDIR_dMRITractFull/tractography_gpu_scripts
TemplateFolder=$QUNEXLIBRARYETC/diffusion_tractography_dense/templates

# -- Check inputs
if [ "$2" == "" ];then
    echo ""
    echo "usage: $0 <SessionsFolder> <Session> <Number_of_Samples>"
    echo ""
    exit 1
fi

SessionsFolder=$1          # "$1" #Path to Generic Study folder
Session=$2              # "$2" #SessionID
Nsamples=$3				# "$3" #Number of Samples to compute

if [ "$3" == "" ];then Nsamples=3000; fi
OutFileName="Conn3.dconn.nii"

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
rm -rf $ResultsFolder/volseeds
rm -rf $ResultsFolder/wtstop
rm -f $ResultsFolder/Mat3_targets

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
generic_options=" --loopcheck --forcedir --fibthresh=0.01 -c 0.2 --sampvox=2 --randfib=1 -P ${Nsamples} -S 2000 --steplength=0.5"
oG=" -s $BedpostxFolder/merged -m $DtiMask --meshspace=caret"

# -- Define Seed
Seed=$ROIsFolder/Whole_Brain_Trajectory_ROI_2
StdRef=$FSLDIR/data/standard/MNI152_T1_2mm_brain_mask
oG=" $oG -x $Seed --seedref=$StdRef"
oG=" $oG --xfm=`echo $RegFolder/standard2acpc_dc` --invxfm=`echo $RegFolder/acpc_dc2standard`"

# -- Define Termination and Waypoint Masks
echo $ResultsFolder/pial.L.asc >> $ResultsFolder/stop                   # -- Pial Surface as Stop Mask
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
oG=" $oG --stop=${ResultsFolder}/stop --wtstop=$ResultsFolder/wtstop"  # -- Should we include an exclusion along the midsagittal plane (without the CC and the commisures)?
oG=" $oG --waypoints=${ROIsFolder}/Whole_Brain_Trajectory_ROI_2"       # -- Use a waypoint to exclude streamlines that go through CSF 

# -- Define Targets
echo $ResultsFolder/white.L.asc >> $ResultsFolder/Mat3_targets
echo $ResultsFolder/white.R.asc >> $ResultsFolder/Mat3_targets
cat $ResultsFolder/volseeds >> $ResultsFolder/Mat3_targets
o=" $oG --omatrix3 --target3=$ResultsFolder/Mat3_targets"


# ----------------------------------------------------------
# ------------------ Matrix Commands -----------------------
# ----------------------------------------------------------

# -- Clean prior results, specify commands and make executable
rm -f $ResultsFolder/commands_Mat3.sh &> /dev/null
rm -rf $ResultsFolder/Mat3_logs
mkdir -p $ResultsFolder/Mat3_logs
out=" --dir=$ResultsFolder"
echo $bindir/probtrackx2_gpu $generic_options $o $out  >> $ResultsFolder/commands_Mat3.sh
chmod 770 $ResultsFolder/commands_Mat3.sh

# -- Do Tractography (N100: ~5h, 50GB RAM)
echo ""
echo "-- Queueing Probtrackx" 
echo ""

# -- Execute commands_Mat3 file
bash ${ResultsFolder}/commands_Mat3.sh ########## <<< commands_Mat3.sh

# ----------------------------------------------------------
# --------------- POST Matrix Commands ---------------------
# ----------------------------------------------------------

# -- Create CIFTI file=Mat3+Mat3_transp (~1.5 hours, 50GB RAM)
echo ""
echo "-- Queueing Post-Matrix 3 Calls" 
echo ""

# -- Clean prior results, specify commands and make executable
PostProcMatrixCommand="${scriptsdir}/post_proc_matrix3.sh ${SessionsFolder} ${Session} ${TemplateFolder} ${OutFileName}"
rm -f $ResultsFolder/postcommands_Mat3.sh &> /dev/null
echo "${PostProcMatrixCommand}" >> $ResultsFolder/postcommands_Mat3.sh
chmod 770 $ResultsFolder/postcommands_Mat3.sh

# -- Execute PostProcMatrixCommand call
bash ${ResultsFolder}/postcommands_Mat3.sh ########## <<< postcommands_Mat3.sh

echo ""
echo "-- Matrix 3 Probtrackx Completed successfully."
echo ""
