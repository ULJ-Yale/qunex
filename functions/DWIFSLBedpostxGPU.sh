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
# DWIDenseParcellation.sh
#
# ## LICENSE
#
# * The FSLBedpostxGPU.sh = the "Software"
# * This Software conforms to the license outlined in the Qu|Nex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ## TODO
#
# ## DESCRIPTION 
#   
# This script, FSLBedpostxGPU.sh, implements FSL's bedpostX functionality within the Qu|Nex Suite with GPU support
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * Connectome Workbench (v1.0 or above)
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./FSLBedpostxGPU.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files: $SessionsFolder/subjects/$CASE/hcp/$CASE/T1w/Diffusion
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
echo ""
echo "-- DESCRIPTION for $UsageInput"
echo ""
echo "This function runs the FSL bedpostx_gpu processing using a GPU-enabled node or via a GPU-enabled queue if using the scheduler option."
echo "It explicitly assumes the Human Connectome Project folder structure for preprocessing and completed diffusion processing: "
echo ""
echo " <study_folder>/<case>/hcp/<case>/Diffusion ---> DWI data needs to be here"
echo ""
echo "-- REQUIRED PARMETERS:"
echo ""
echo "--function=<function_name>                            Explicitly specify name of function in flag or use function name as first argument (e.g. qunex <function_name> followed by flags)"
echo "--sessionsfolder=<folder_with_subjects>               Path to study folder that contains subjects"
echo "--subjects=<comma_separated_list_of_cases>            List of subjects to run"
echo "--fibers=<number_of_fibers>                           Number of fibres per voxel, default 3"
echo "--model=<deconvolution_model>                         Deconvolution model. 1: with sticks, 2: with sticks with a range of diffusivities <default>, 3: with zeppelins"
echo "--burnin=<burnin_period_value>                        Burnin period, default 1000"
echo "--rician=<set_rician_value>                           <yes> or <no>. Default is yes"
echo "--overwrite=<clean_prior_run>                         Delete prior run for a given subject"
echo "--scheduler=<name_of_cluster_scheduler_and_options>   A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo "                                                        e.g. for SLURM the string would look like this: "
echo "                                                         --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
echo "                                                           * Note: You need to specify a GPU-enabled queue or partition"
echo ""
echo "-- EXAMPLES:"
echo ""
echo "   --> Run directly via ${TOOLS}/${QUNEXREPO}/connector/functions/FSLBedpostxGPU.sh --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
echo ""
reho "           * NOTE: --scheduler is not available via direct script call."
echo ""
echo "   --> Run via qunex FSLBedpostxGPU --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
echo ""
geho "           * NOTE: scheduler is available via qunex call:"
echo "                   --scheduler=<name_of_cluster_scheduler_and_options>  A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo ""
echo "           * For SLURM scheduler the string would look like this via the qunex call: "
echo "                   --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
echo ""
echo ""     
echo ""
echo ""
echo "qunex --sessionsfolder='<path_to_study_subjects_folder>' \ "
echo "--function='FSLBedpostxGPU' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--fibers='3' \ "
echo "--burnin='3000' \ "
echo "--model='3' \ "
echo "--scheduler='<name_of_scheduler_and_options>' \ "
echo "--overwrite='yes'"
echo ""
exit 0
}

# ------------------------------------------------------------------------------
# -- Setup color outputs
# ------------------------------------------------------------------------------

reho() {
    echo -e "\033[31m $1 \033[0m"
}

geho() {
    echo -e "\033[32m $1 \033[0m"
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]]; then
	usage
fi

# ------------------------------------------------------------------------------
#  -- Parse arguments
# ------------------------------------------------------------------------------

########################################## INPUTS ########################################## 

# DWI Data and T1w data needed in HCP-style format

########################################## OUTPUTS #########################################

# -- Outputs will be *pconn.nii files located here:
#       DWIOutput="$SessionsFolder/$CASE/hcp/$CASE/T1w/Diffusion/"

# ------------------------------------------------------------------------------
# -- Check for options
# ------------------------------------------------------------------------------

opts_GetOpt() {
sopt="$1"
shift 1
for fn in "$@" ; do
    if [ `echo $fn | grep -- "^${sopt}=" | wc -w` -gt 0 ]; then
        echo $fn | sed "s/^${sopt}=//"
        return 0
    fi
done
}

# -- Get the command line options for this script
get_options() {
local scriptName=$(basename ${0})
local arguments=($@)
# -- Initialize global output variables
unset SessionsFolder
unset Subject
runcmd=""

# -- Parse arguments
Fibers=`opts_GetOpt "--fibers" $@`
Model=`opts_GetOpt "--model" $@`
Burnin=`opts_GetOpt "--burnin" $@`
Jumps=`opts_GetOpt "--jumps" $@`
Rician=`opts_GetOpt "--rician" $@`
Overwrite=`opts_GetOpt "--overwrite" $@`
CASE=`opts_GetOpt "--subject" $@`
SessionsFolder=`opts_GetOpt "--sessionsfolder" $@`

# -- Check required parameters
if [ -z "$SessionsFolder" ]; then reho "Error: Subjects Folder"; exit 1; fi
if [ -z "$CASE" ]; then reho "Error: Subject missing"; exit 1; fi
if [ -z "$Fibers" ]; then reho "Error: Fibers value missing"; exit 1; fi
if [ -z "$Model" ]; then reho "Error: Model value missing"; exit 1; fi
if [ -z "$Burnin" ]; then reho "Error: Burnin value missing"; exit 1; fi
if [ -z "$Rician" ]; then reho "Note: Rician flag missing. Setting to default --> YES"; Rician="YES"; fi

# -- Set StudyFolder
cd $SessionsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null

# -- Report options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   Study Folder: ${StudyFolder}"
echo "   Subjects Folder: ${SessionsFolder}"
echo "   Subject: ${CASE}"
echo "   Study Log Folder: ${LogFolder}"
echo "   Number of Fibers: ${Fibers}"
echo "   Model Type: ${Model}"
echo "   Burnin Period: ${Burnin}"
echo "   Rician flag: ${Rician}"
echo "   Overwrite prior run: ${Overwrite}"
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""
}

######################################### DO WORK ##########################################

main() {

# -- Get Command Line Options
get_options $@

# -- Establish global directory paths
T1wDiffFolder=${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion
BedPostXFolder=${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX
LogFolder="$BedPostXFolder"/logs
Overwrite="$Overwrite"
# -- Check if overwrite flag was set
if [ "$Overwrite" == "yes" ]; then
    echo ""
    reho "Removing existing Bedpostx run for $CASE..."
    echo ""
    rm -rf "$BedPostXFolder" > /dev/null 2>&1
fi
geho "Checking if Bedpostx was completed on $CASE..."
# Set file depending on model specification
if [ "$Model" == 2 ]; then
    CheckFile="mean_d_stdsamples.nii.gz"
fi
if [ "$Model" == 3 ]; then
    CheckFile="mean_Rsamples.nii.gz"
fi
if [ "$Rician" == "no" ] || [ "$Rician" == "NO" ]; then
    echo ""
    geho "Omitting --rician flag"
    RicianFlag=""
    echo ""
else
    echo ""
    geho "Setting --rician flag"
    RicianFlag="--rician"
    echo ""
fi

checkCompletion() {
# -- Check if the file exists
if [ -f ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/"$CheckFile" ]; then
    # -- Set file sizes to check for completion
    minimumfilesize=20000000
    actualfilesize=`wc -c < ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/merged_f1samples.nii.gz` > /dev/null 2>&1
    filecount=`ls ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/merged_*nii.gz | wc | awk {'print $1'}`
fi
# -- Then check if run is complete based on file count
if [ "$filecount" == 9 ]; then > /dev/null 2>&1
    echo ""
    cyaneho " --> $filecount merged samples for $CASE found."
    # -- Then check if run is complete based on file size
    if [ $(echo "$actualfilesize" | bc) -ge $(echo "$minimumfilesize" | bc) ]; then > /dev/null 2>&1
        echo ""
        cyaneho " --> Bedpostx outputs found and completed for $CASE"
        echo ""
        cyaneho "Check prior output logs here: $LogFolder"
        echo ""
        echo "--------------------------------------------------------------"
        echo ""
        RunCompleted="yes"
    else
        echo ""
        reho " --> Bedpostx outputs missing or incomplete for $CASE"
        echo ""
        reho "--------------------------------------------------------------"
        echo ""
        RunCompleted="no"
    fi
fi
}

checkCompletion
if [[ ${RunCompleted} == "yes" ]]; then
   exit 0
else
   echo ""
   reho " -- Prior BedpostX run not found or incomplete for $CASE. Setting up new run..."
   echo ""
fi

# -- Generate log folder
mkdir ${BedPostXFolder} > /dev/null 2>&1
# -- Command to run
if [ -f "$T1wDiffFolder"/grad_dev.nii.gz ]; then
    ${FSLGPUBinary}/bedpostx_gpu_noscheduler ${T1wDiffFolder}/. -n ${Fibers} -model ${Model} -b ${Burnin} -g ${RicianFlag}
else
    ${FSLGPUBinary}/bedpostx_gpu_noscheduler ${T1wDiffFolder}/. -n ${Fibers} -model ${Model} -b ${Burnin} ${RicianFlag}
fi

# -- Perform completion checks
reho "--- Checking outputs..."
echo ""
checkCompletion
if [[ ${RunCompleted} == "yes" ]]; then
    geho "BedpostX completed: ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/"
    echo ""
else
   echo ""
   reho " -- BedpostX run not found or incomplete for $CASE. Something went wrong." 
   reho "Check output: ${SessionsFolder}/${CASE}/hcp/${CASE}/T1w/Diffusion.bedpostX/"
   echo ""
   exit 1
fi

reho "--- BedpostX successfully completed"
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
