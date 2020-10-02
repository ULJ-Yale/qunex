#!/bin/bash

#
# 	Original code developed by Stam Sotiropoulos (Oxford University)
#
#	Modified by Alan Anticevic (Yale University) for LSF, PBS and SLURM compatibility via MNAP code (09/22/2017)
#

# - Check which CUDA version is being run and set where GPU probtrackx binary is # bindir=$FSLDIR/bin 
if [[ `nvcc --version | grep "release"` == *"7.5"* ]]; then bindir=${FSLGPUBinary}/probtrackx_gpu_cuda_7.5; fi
if [[ `nvcc --version | grep "release"` == *"8.0"* ]]; then bindir=${FSLGPUBinary}/probtrackx_gpu_cuda_8.0; fi
if [[ `nvcc --version | grep "release"` == *"9.1"* ]]; then bindir=${FSLGPUBinary}/probtrackx_gpu_cuda_9.1; fi

scriptsdir=$HCPPIPEDIR/DiffusionTractographyDense/Tractography_gpu_scripts
TemplateFolder=$HCPPIPEDIR/DiffusionTractographyDense/91282_Greyordinates
cuda_queue=$FSLGECUDAQ

if [ "$2" == "" ];then
    echo ""
    echo "usage: $0 <StudyFolder> <Session> <Number_of_Samples> <Scheduler>"
    echo ""
    exit 1
fi

StudyFolder=$1          # "$1" #Path to Generic Study folder
Session=$2              # "$2" #SessionID
Nsamples=$3				# "$3" #Number of Samples to compute
Scheduler=$4			# "$4" #Scheduler to use for the fsl_sub command

if [ "$3" == "" ];then Nsamples=10000; fi
OutFileName="Conn1.dconn.nii"

ResultsFolder="$StudyFolder"/"$Session"/MNINonLinear/Results/Tractography
RegFolder="$StudyFolder"/"$Session"/MNINonLinear/xfms
ROIsFolder="$StudyFolder"/"$Session"/MNINonLinear/ROIs
if [ ! -e ${ResultsFolder} ] ; then
  mkdir -p ${ResultsFolder}
fi

#Use BedpostX samples
BedpostxFolder="$StudyFolder"/"$Session"/T1w/Diffusion.bedpostX
DtiMask=$BedpostxFolder/nodif_brain_mask

rm -rf $ResultsFolder/stop
rm -rf $ResultsFolder/wtstop
rm -rf $ResultsFolder/volseeds
rm -rf $ResultsFolder/Mat1_seeds

#Temporarily here, should be in Prepare_Seeds
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

#Define Generic Options
generic_options=" --loopcheck --forcedir --fibthresh=0.01 -c 0.2 --sampvox=2 --randfib=1 -P ${Nsamples} -S 2000 --steplength=0.5"
o=" -s $BedpostxFolder/merged -m $DtiMask --meshspace=caret"

#Define Seed
echo $ResultsFolder/white.L.asc >> $ResultsFolder/Mat1_seeds
echo $ResultsFolder/white.R.asc >> $ResultsFolder/Mat1_seeds
cat $ResultsFolder/volseeds >> $ResultsFolder/Mat1_seeds
Seed="$ResultsFolder/Mat1_seeds"
StdRef=$FSLDIR/data/standard/MNI152_T1_2mm_brain_mask
o=" $o -x $Seed --seedref=$StdRef"
o=" $o --xfm=`echo $RegFolder/standard2acpc_dc` --invxfm=`echo $RegFolder/acpc_dc2standard`"

#Define Termination and Waypoint Masks
echo $ResultsFolder/pial.L.asc >> $ResultsFolder/stop      #Pial Surface as Stop Mask
echo $ResultsFolder/pial.R.asc >> $ResultsFolder/stop

echo $ResultsFolder/CIFTI_STRUCTURE_ACCUMBENS_LEFT >> $ResultsFolder/wtstop    #WM boundary Surface and subcortical volumes as Wt_Stop Masks
echo $ResultsFolder/CIFTI_STRUCTURE_ACCUMBENS_RIGHT >> $ResultsFolder/wtstop   #Exclude Brainstem and diencephalon, otherwise cortico-cerebellar connections are stopped!
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
o=" $o --stop=${ResultsFolder}/stop --wtstop=$ResultsFolder/wtstop --forcefirststep"  #Should we include an exclusion along the midsagittal plane (without the CC and the commisures)?
o=" $o --waypoints=${ROIsFolder}/Whole_Brain_Trajectory_ROI_2"       #Use a waypoint to exclude streamlines that go through CSF 

#Define Targets
o=" $o --omatrix1"

rm -rf $ResultsFolder/commands_Mat1.txt
rm -rf $ResultsFolder/Mat1_logs
mkdir -p $ResultsFolder/Mat1_logs

out=" --dir=$ResultsFolder"
rm -f $ResultsFolder/commands_Mat1.sh &> /dev/null
echo $bindir/probtrackx2_gpu $generic_options $o $out  >> $ResultsFolder/commands_Mat1.sh
chmod 770 $ResultsFolder/commands_Mat1.sh

# -- Do Tractography (N100: ~5h, 35GB RAM)

echo ""
echo "-- Queueing Probtrackx" 
echo ""

# - Specify scheduler options
if [ $Scheduler == "SLURM" ]; then
	SchedulerOptions="job-name=${Session}_ptx_run,time=8:00:00,ntasks=1,cpus-per-task=1,mem=40000,partition=$cuda_queue,gres=gpu:1"
	echo $SchedulerOptions >> $ResultsFolder/commands_Mat1_sc.sh
fi
if [ $Scheduler == "PBS" ]; then
	SchedulerOptions="N=${Session}_ptx_run,walltime=8:00:00,q=$cuda_queue,nodes=1:ppn=1:cpus=10,mem=40000"
fi
if [ $Scheduler == "LSF" ]; then
	SchedulerOptions="J=${Session}_ptx_run,walltime=8:00:00,queue=$cuda_queue,cores=10,mem=40000"
fi
	
ptx_id=`gmri schedule command="${ResultsFolder}/commands_Mat1.sh" settings="${Scheduler},${SchedulerOptions}" output="stdout:${ResultsFolder}/Mat1_logs/Mat1.output.log|stderr:${ResultsFolder}/Mat1_logs/Mat1.error.log" workdir="${ResultsFolder}"`
#echo $ptx_id >> $ResultsFolder/schedulercommand.txt
# -- Create CIFTI file=Mat1+Mat1_transp (1.5 hours, 36 GB)

echo ""
echo "-- Queueing Post-Matrix 1 Calls" 
echo ""

# - Specify scheduler options & Set dependencies on all prior jobs
ptx_id=`more ${ResultsFolder}/Mat1_logs/Mat1.output.log | awk 'NF{ print $NF }'`

# - Specify scheduler options
if [ $Scheduler == "SLURM" ]; then
	SchedulerOptions="job-name=bedpostx_gpu,depend=afterok:${ptx_id},time=3:00:00,ntasks=1,cpus-per-task=1,mem=40000,partition=$cuda_queue,gres=gpu:1"
fi
if [ $Scheduler == "PBS" ]; then
	SchedulerOptions="N=bedpostx_gpu,d=${ptx_id},walltime=3:00:00,nodes=1:ppn=1:cpus=1,mem=40000,q=$cuda_queue"
fi
if [ $Scheduler == "LSF" ]; then
	SchedulerOptions="J=bedpostx_gpu,w=${ptx_id},walltime=3:00:00,cores=5,mem=40000,q=$cuda_queue"
fi

# -- Deprecated fsl_sub call
# $FSLDIR/bin/fsl_sub."$fslsub" -T 180 -R 48000 -n 10 -Q $cuda_queue -j $ptx_id -l ${ResultsFolder}/Mat1_logs -N Mat1_conn ${scriptsdir}/PostProcMatrix1.sh ${StudyFolder} ${Session} ${TemplateFolder} ${OutFileName}

PostProcMatrixCommand="${scriptsdir}/PostProcMatrix1.sh ${StudyFolder} ${Session} ${TemplateFolder} ${OutFileName}"

rm -f $ResultsFolder/postcommands_Mat1.sh &> /dev/null
echo "${PostProcMatrixCommand}" >> $ResultsFolder/postcommands_Mat1.sh
chmod 770 $ResultsFolder/postcommands_Mat1.sh

gmri schedule command="${ResultsFolder}/postcommands_Mat1.sh" settings="${Scheduler},${SchedulerOptions}" output="stdout:${ResultsFolder}/Mat1_logs/Mat1Post.output.log|stderr:${ResultsFolder}/Mat1_logs/Mat1Post.error.log" workdir="${ResultsFolder}"`

echo ""
echo "-- Matrix 1 Probtrackx Submitted successfully."
echo ""