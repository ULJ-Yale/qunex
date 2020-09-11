#!/bin/bash

#Check which CUDA version is being run and set where GPU probtrackx binary is # bindir=$FSLDIR/bin 

if [[ `nvcc --version | grep "release"` == *"6.0"* ]]; then bindir=${FSLGPUBinary}/probtrackx_gpu_cuda_6.0; fi
if [[ `nvcc --version | grep "release"` == *"6.5"* ]]; then bindir=${FSLGPUBinary}/probtrackx_gpu_cuda_6.5; fi
if [[ `nvcc --version | grep "release"` == *"7.0"* ]]; then bindir=${FSLGPUBinary}/probtrackx_gpu_cuda_7.0; fi
if [[ `nvcc --version | grep "release"` == *"7.5"* ]]; then bindir=${FSLGPUBinary}/probtrackx_gpu_cuda_7.5; fi
if [[ `nvcc --version | grep "release"` == *"8.0"* ]]; then bindir=${FSLGPUBinary}/probtrackx_gpu_cuda_8.0; fi
if [[ `nvcc --version | grep "release"` == *"9.1"* ]]; then bindir=${FSLGPUBinary}/probtrackx_gpu_cuda_9.1; fi

scriptsdir=$HCPPIPEDIR/DiffusionTractographyDense/Tractography_gpu_scripts
TemplateFolder=$HCPPIPEDIR/DiffusionTractographyDense/91282_Greyordinates
cuda_queue=$FSLGECUDAQ

#this is specific for WashU cluster
#export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/moises/PTX2/lib:/export/cuda-6.0/lib64

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

if [ "$3" == "" ];then Nsamples=3000; fi
OutFileName="Conn3.dconn.nii"

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
rm -rf $ResultsFolder/volseeds
rm -rf $ResultsFolder/wtstop
rm -f $ResultsFolder/Mat3_targets

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
oG=" -s $BedpostxFolder/merged -m $DtiMask --meshspace=caret"

#Define Seed
Seed=$ROIsFolder/Whole_Brain_Trajectory_ROI_2
StdRef=$FSLDIR/data/standard/MNI152_T1_2mm_brain_mask
oG=" $oG -x $Seed --seedref=$StdRef"
oG=" $oG --xfm=`echo $RegFolder/standard2acpc_dc` --invxfm=`echo $RegFolder/acpc_dc2standard`"

#Define Termination and Waypoint Masks
echo $ResultsFolder/pial.L.asc >> $ResultsFolder/stop                   #Pial Surface as Stop Mask
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

oG=" $oG --stop=${ResultsFolder}/stop --wtstop=$ResultsFolder/wtstop"  #Should we include an exclusion along the midsagittal plane (without the CC and the commisures)?
oG=" $oG --waypoints=${ROIsFolder}/Whole_Brain_Trajectory_ROI_2"       #Use a waypoint to exclude streamlines that go through CSF 

#Define Targets
echo $ResultsFolder/white.L.asc >> $ResultsFolder/Mat3_targets
echo $ResultsFolder/white.R.asc >> $ResultsFolder/Mat3_targets
cat $ResultsFolder/volseeds >> $ResultsFolder/Mat3_targets
o=" $oG --omatrix3 --target3=$ResultsFolder/Mat3_targets"

rm -f $ResultsFolder/commands_Mat3.txt
rm -rf $ResultsFolder/Mat3_logs
mkdir -p $ResultsFolder/Mat3_logs

out=" --dir=$ResultsFolder"
echo $bindir/probtrackx2_gpu $generic_options $o $out >> $ResultsFolder/commands_Mat3.txt

# - Do Tractography #N100: ~5h, 35GB RAM

echo "Queueing Probtrackx" 

# - Specify scheduler options
if [ $Scheduler == "SLURM" ]; then
	SchedulerOptions="job-name=${Session}_ptx_run,time=12:00:00,ntasks=1,cpus-per-task=10,mem=40000,partition=$LSFPartitionName,gres=gpu:1"
fi

if [ $Scheduler == "PBS" ]; then
	SchedulerOptions="N=${Session}_ptx_run,walltime=12:00:00,q=$cuda_queue,nodes=1:ppn=1:cpus=10,mem=40000"
fi

if [ $Scheduler == "LSF" ]; then
	SchedulerOptions="J=${Session}_ptx_run,walltime=12:00:00,queue=$cuda_queue,cores=10,mem=40000"
fi

ptx_id=`gmri schedule command="${ResultsFolder}/commands_Mat3.txt" settings="${Scheduler},${SchedulerOptions}" output="stdout:${ResultsFolder}/Mat1_logs|stderr:${ResultsFolder}/Mat1_logs_error" workdir="${ResultsFolder}" | grep "Submitted batch" | sed 's/.* //g'`

	## -- DEPRECATED SCHEDULER CALLS:
	# USING SGE-FMRIB - note that -n is set to 10 for Yale GPU queue 
	# ptx_id=`$FSLDIR/bin/fsl_sub.${fslsub} -T 720 -R 48000 -Q $cuda_queue -n 10 -l ${ResultsFolder}/Mat3_logs -N ptx2_Mat3 -t ${ResultsFolder}/commands_Mat3.txt`
	# USING PBS-WASHUå
	#torque_command="qsub -q $cuda_queue -V -l nodes=1:ppn=1:gpus=1,walltime=12:00:00 -N ptx2_Mat3 -o $ResultsFolder/Mat3_logs  -e $ResultsFolder/Mat3_logs "
	#ptx_id=`exec $torque_command $ResultsFolder/commands_Mat3.txt | awk '{print $1}' | awk -F. '{print $1}'`
	#sleep 10 

# - Create CIFTI file=Mat3+Mat3_transp (1.5 hours, 36 GB)

	## -- DEPRECATED SCHEDULER CALLS:
	#$FSLDIR/bin/fsl_sub."$fslsub" -T 180 -R 48000 -n 10 -Q $cuda_queue -j $ptx_id -l ${ResultsFolder}/Mat3_logs -N Mat3_conn ${scriptsdir}/PostProcMatrix3.sh ${StudyFolder} ${Session} ${TemplateFolder} ${OutFileName}

# - Specify scheduler options
if [ $Scheduler == "SLURM" ]; then
	SchedulerOptions="depend=done:${Session}_ptx_run,time=12:00:00,ntasks=1,cpus-per-task=5,mem=40000,partition=$LSFPartitionName"
fi

if [ $Scheduler == "PBS" ]; then
	SchedulerOptions="depend=${Session}_ptx_run,walltime=12:00:00,nodes=1:ppn=1:cpus=5,mem=40000"
fi

if [ $Scheduler == "LSF" ]; then
	SchedulerOptions="w=done(${Session}_ptx_run),walltime=12:00:00,cores=5,mem=40000"
fi

CreateCIFTIFileCommand="${scriptsdir}/PostProcMatrix3.sh ${StudyFolder} ${Session} ${TemplateFolder} ${OutFileName}"
gmri schedule command="${CreateCIFTIFileCommand}" settings="${Scheduler},${SchedulerOptions}" output="stdout:${ResultsFolder}/Mat1_logs|stderr:${ResultsFolder}/Mat1_logs_error" workdir="${ResultsFolder}"`


