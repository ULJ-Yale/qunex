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
#  ProbtrackxGPUDense.sh
#
# ## LICENSE
#
# * The ProbtrackxGPUDense.sh = the "Software"
# * This Software conforms to the license outlined in the Qu|Nex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ## TODO
#
#
#
# ## DESCRIPTION 
#   
# This script, ProbtrackxGPUDense.sh, implements probtrackX GPU version on HCP-processed DWI data
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * HCP Pipelines
# * FSL
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./ProbtrackxGPUDense.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are BOLD data from previous processing
# * These data are stored in: "$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/T1w/Diffusion/BedpostX 
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# -- Setup color outputs
# ------------------------------------------------------------------------------

reho() {
    echo -e "\033[31m $1 \033[0m"
}

geho() {
    echo -e "\033[32m $1 \033[0m"
}

usage() {
     echo ""
     echo "-- DESCRIPTION:"
     echo ""
     echo "This function runs the probtrackxgpu dense whole-brain connectome generation by calling ${ScriptsFolder}/RunMatrix1.sh or ${ScriptsFolder}/RunMatrix3.sh"
     echo "Note that this function needs to send work to a GPU-enabled queue or you need to run it locally from a GPU-equiped machine"
     echo "It explicitly assumes the Human Connectome Project folder structure and completed FSLBedpostxGPU and pretractographyDense functions processing:"
     echo ""     
     geho ""
     geho "    --> HCP Pipelines"
     geho "    --> FSL 5.0.9 or greater"
     echo ""
     echo ""
     echo " <study_folder>/<case>/hcp/<case>/T1w/Diffusion            ---> Processed DWI data needs to be here"
     echo " <study_folder>/<case>/hcp/<case>/T1w/Diffusion.bedpostX   ---> BedpostX output data needs to be here"
     echo " <study_folder>/<case>/hcp/<case>/MNINonLinear             ---> T1w images need to be in MNINonLinear space here"
     echo ""
     echo "  -- Outputs will be here:"
     echo ""
     echo "      <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Conn1.dconn.nii.gz   ---> Dense Connectome CIFTI Results in MNI space for Matrix1"
     echo "      <study_folder>/<case>/hcp/<case>/MNINonLinear/Results/Conn3.dconn.nii.gz   ---> Dense Connectome CIFTI Results in MNI space for Matrix3"
     echo ""
     echo "  -- Note on waytotal normalization and log transformation of streamline counts:"
     echo ""
     echo "  waytotal normalization is computed automatically as part of the run prior to any inter-subject or group comparisons"
     echo "  to account for individual differences in geometry and brain size. The function divides the "
     echo "  dense connectome by the waytotal value, turning absolute streamline counts into relative "
     echo "  proportions of the total streamline count in each subject. "
     echo ""
     echo "  Next, a log transformation is computed on the waytotal normalized data, "
     echo "  which will yield stronger connectivity values for longe-range projections. "
     echo "  Log-transformation accounts for algorithmic distance bias in tract generation "
     echo "  (path probabilities drop with distance as uncertainty is accumulated)."
     echo "  See Donahue et al. • The Journal of Neuroscience, June 22, 2016 • 36(25):6758 – 6770. "
     echo "      DOI: https://doi.org/10.1523/JNEUROSCI.0493-16.2016"
     echo ""
     echo "  -- The outputs for these files will be in:"
     echo ""
     echo "     /<path_to_study_subjects_folder>/<subject_id>/hcp/<subject_id>/MNINonLinear/Results/Tractography/<MatrixName>_waytotnorm.dconn.nii"
     echo "     /<path_to_study_subjects_folder>/<subject_id>/hcp/<subject_id>/MNINonLinear/Results/Tractography/<MatrixName>_waytotnorm_log.dconn.nii"
     echo ""
     echo ""
     echo "  -- REQUIRED PARMETERS:"
     echo ""
     echo "    --function=<function_name>                            Explicitly specify name of function in flag or use function name as first argument (e.g. qunex <function_name> followed by flags)"
     echo "    --subjectsfolder=<folder_with_subjects>               Path to study folder that contains subjects"
     echo "    --subjects=<comma_separated_list_of_cases>            List of subjects to run"
     echo "    --overwrite=<clean_prior_run>                         Delete a prior run for a given subject [Note: this will delete only the Matrix run specified by the -omatrix flag]"
     echo "    --omatrix1=<matrix1_model>                            Specify if you wish to run matrix 1 model [yes or omit flag]"
     echo "    --omatrix3=<matrix3_model>                            Specify if you wish to run matrix 3 model [yes or omit flag]"
     echo ""
     echo "  -- OPTIONAL PARMETERS:"
     echo ""
     echo "    --nsamplesmatrix1=<Number_of_Samples_for_Matrix1>     Number of samples - default=10000"
     echo "    --nsamplesmatrix3=<Number_of_Samples_for_Matrix3>     Number of samples - default=3000"
     echo "    --infolder=<path_for_hcp_input_folder>                Input HCP folder where minimally preprocessed results reside"
     echo "                                                          Default: <path_to_study_subjects_folder>/<subject_id>/hcp"
     echo "    --outfolder=<probtrackX_output_folder_locaition>      Output folder for probtrackX results."
     echo "                                                          Default: <path_to_study_subjects_folder>/<subject_id>/hcp/<subject_id>/MNINonLinear/Results/Tractography"     
     echo "    --scriptsfolder=<folder_with_probtrackX_GPU_scripts>  Location of the probtrackX GPU scripts"
     echo ""
     echo ""
     echo ""
     echo "-- GENERIC PARMETERS SET BY DEFAULT (will be parameterized in the future):"
     echo ""
     echo "    --loopcheck --forcedir --fibthresh=0.01 -c 0.2 --sampvox=2 --randfib=1 -S 2000 --steplength=0.5"
     echo ""
     echo "** The function calls either of these based on the --omatrix1 and --omatrix3 flags: "
     echo ""
     echo "    $HCPPIPEDIR_dMRITracFull/Tractography_gpu_scripts/RunMatrix1.sh"
     echo "    $HCPPIPEDIR_dMRITracFull/Tractography_gpu_scripts/RunMatrix3.sh"
     echo ""
     echo "    --> both are cluster-aware and send the jobs to the GPU-enabled queue. They do not work interactively."
     echo ""
     echo "  -- EXAMPLE with flagged parameters for submission to the scheduler (needs to be GPU-enabled):"
     echo ""
     echo "                                                      1=FIXICA, 2=PostFIX; all=Run all Sequentially. Default [3]"
     echo ""
     echo ""
     echo "   --> Run directly via ${TOOLS}/${QUNEXREPO}/connector/functions/ICAFIXhcp.sh --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
     echo ""
     reho "           * NOTE: --scheduler is not available via direct script call."
     echo ""
     echo "   --> Run via qunex ICAFIXhcp --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
     echo ""
     geho "           * NOTE: scheduler is available via qunex call:"
     echo "                   --scheduler=<name_of_cluster_scheduler_and_options>  A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
     echo ""
     echo "           * For SLURM scheduler the string would look like this via the qunex call: "
     echo "                   --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
     echo ""     
     echo "-- EXAMPLE with flagged parameters:"
     echo ""
     echo "qunex ProbtrackxGPUDense --subjectsfolder='<path_to_study_subjects_folder>' \ "
     echo "--subjects='<comma_separarated_list_of_cases>' \ "
     echo "--scheduler='<name_of_scheduler_and_options>' \ "
     echo "--omatrix1='yes' \ "
     echo "--nsamplesmatrix1='10000' \ "
     echo "--overwrite='no'"
     exit 0
}

# ------------------------------------------------------------------------------------------------------
# ----------------------------------------- ProbtrackxGPUDense CODE -----------------------------------------------
# ------------------------------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]]; then
    usage
fi

# -- Get the command line options for this script
get_options() {

# -- Set general options functions
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

# -- Initialize global output variables
unset SubjectsFolder
unset Subjects
unset Overwrite
unset ScriptsFolder        
unset OutFolder        
unset InFolder            
unset NsamplesMatrixOne    
unset NsamplesMatrixThree  
unset MatrixOne    
unset MatrixThree  
unset minimumfilesize      

# -- Parse arguments
SubjectsFolder=`opts_GetOpt "--subjectsfolder" $@`
CASES=`opts_GetOpt "--subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
Overwrite=`opts_GetOpt "--overwrite" $@`
ScriptsFolder=`opts_GetOpt "--scriptsfolder" $@`
InFolder=`opts_GetOpt "--infolder" $@`
OutFolder=`opts_GetOpt "--outfolder" $@`
MatrixOne=`opts_GetOpt "--omatrix1" $@`
MatrixThree=`opts_GetOpt "--omatrix3" $@`
NsamplesMatrixOne=`opts_GetOpt "--nsamplesmatrix1" $@`
NsamplesMatrixThree=`opts_GetOpt "--nsamplesmatrix3" $@`

if [ -z ${SubjectsFolder} ]; then
    usage
    reho "ERROR: <folder_with_subjects> not specified"
    echo ""
    exit 1
fi
if [ -z ${CASES} ]; then
    usage
    reho "ERROR: <subject_ids> not specified"
    exit 1
fi

# -- Check if Matrix 1 or 3 flag set
if [ -z "$MatrixOne" ] && [ -z "$MatrixThree" ]; then reho "Error: Matrix option missing. You need to specify at least one. [e.g. --omatrix1='yes' and/or --omatrix2='yes']"; exit 1; fi
if [ "$MatrixOne" == "yes" ]; then
    if [ -z "$NsamplesMatrixOne" ]; then NsamplesMatrixOne=10000; fi
fi
if [ "$MatrixThree" == "yes" ]; then
    if [ -z "$NsamplesMatrixThree" ]; then NsamplesMatrixThree=3000; fi
fi
if [ "$MatrixOne" == "yes" ] && [ "$MatrixThree" == "yes" ]; then
    MNumber="1 3"
fi

# -- Optional parameters
if [ -z ${ScriptsFolder} ]; then ScriptsFolder="${HCPPIPEDIR_dMRITracFull}/Tractography_gpu_scripts"; fi
if [ -z ${OutFolder} ]; then OutFolder="${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/Tractography"; fi
if [ -z ${InFolder} ]; then InFolder="${SubjectsFolder}/${CASE}/hcp"; fi
minimumfilesize="100000000"

# -- Set StudyFolder
cd $SubjectsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null

scriptName=$(basename ${0})
# -- Report options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   Study Folder: ${StudyFolder}"
echo "   Subjects Folder: ${SubjectsFolder}"
echo "   Subjects: ${CASES}"
echo "   probtraxkX GPU scripts Folder: ${ScriptsFolder}"
echo "   Input HCP folder: ${InFolder}"
echo "   Output folder for probtrackX results: ${OutFolder}"
echo "   Compute Matrix1: ${MatrixOne}"
echo "   Compute Matrix3: ${MatrixThree}"
echo "   Number of samples for Matrix1: ${NsamplesMatrixOne}"
echo "   Number of samples for Matrix3: ${NsamplesMatrixThree}"
echo "   Overwrite prior run: ${Overwrite}"
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""
}

######################################### DO WORK ##########################################

main() {

get_options "$@"

# -- Generate the results and log folders
mkdir ${OutFolder}  &> /dev/null

# -------------------------------------------------
# -- Do work for Matrix 1 or 3 for each CASE
# -------------------------------------------------

for CASE in $CASES; do
    TimeLog=`date '+%Y-%m-%d-%H-%M-%S'`
    OutputLogProbtrackxGPUDense="${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/fixica_${CASE}_bold${BOLD}_${TimeLog}.log"
    
    # -- Echo probtrackX log for each case
            echo ""                                                   2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
    geho "   --- probtrackX GPU for subject $CASE..."                 2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            echo ""                                                   2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
    
    for MNum in $MNumber; do
        if [ "$MNum" == "1" ]; then NSamples="${NsamplesMatrixOne}"; fi
        if [ "$MNum" == "3" ]; then NSamples="${NsamplesMatrixThree}"; fi
        # -- Check of overwrite flag was set
        if [ "$Overwrite" == "yes" ]; then
            echo ""                                                                          2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            reho " --- Removing existing Probtrackxgpu Matrix${MNum} dense run for $CASE..." 2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            echo ""                                                                          2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            rm -f ${OutFolder}/Conn${MNum}.dconn.nii.gz &> /dev/null
        fi
        # -- Check for Matrix completion
        echo "" 2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
        geho "Checking if ProbtrackX Matrix ${MNum} and dense connectome was completed on $CASE..." 2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
        echo "" 2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
        # -- Check if the file even exists
        if [ -f ${OutFolder}/Conn${MNum}.dconn.nii.gz ]; then
            # -- Set file sizes to check for completion
            actualfilesize=`wc -c < "$OutFolder"/Conn${MNum}.dconn.nii.gz` > /dev/null 2>&1
            # -- Then check if Matrix run is complete based on size
            if [ $(echo ${actualfilesize} | bc) -ge $(echo ${minimumfilesize} | bc) ]; then > /dev/null 2>&1
                echo ""                                                               2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
                cyaneho "DONE -- ProbtrackX Matrix ${MNum} solution and dense connectome was completed for ${CASE}" 2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
                cyaneho "To re-run set overwrite flag to 'yes'"                       2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
                echo ""                                                               2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
                echo "--------------------------------------------------------------" 2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
                echo ""                                                               2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            fi
        else
            # -- If run is incomplete perform run for Matrix
            echo "" 2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            geho "ProbtrackX Matrix ${MNum} solution and dense connectome incomplete for $CASE. Starting run with $NSamples samples..." 2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            echo ""                                                   2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            # -- Command to run
            ProbtrackxGPUDenseCommand="${ScriptsFolder}/RunMatrix${MNum}_NoScheduler.sh ${RunFolder} ${CASE} ${Nsamples} ${SchedulerType}"
            # -- Echo the command
            echo "Running the following probtrackX GPU command: "     2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            echo ""                                                   2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            echo "---------------------------"                        2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            echo ""                                                   2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            echo "   ${ProbtrackxGPUDenseCommand}"                    2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            echo ""                                                   2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            echo "---------------------------"                        2>&1 | tee -a ${OutputLogProbtrackxGPUDense}
            # -- Eval the command
            eval "${ProbtrackxGPUDenseCommand}"                       2>&1 | tee -a ${OutputLogProbtrackxGPUDense}        
        fi
    done
done

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
