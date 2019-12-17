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
#  ComputeFunctionalConnectivity.sh
#
# ## LICENSE
#
# * The ComputeFunctionalConnectivity.sh = the "Software"
# * This Software conforms to the license outlined in the Qu|Nex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ### TODO
#
# ## Description 
#   
# This script, ComputeFunctionalConnectivity.sh, implements functional connectivity
# using Qu|Nex Suite Matlab tools (e.g. fc_ComputeSeedMapsMultiple)
# 
# ## Prerequisite Installed Software
#
# * Qu|Nex Suite
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. $./ComputeFunctionalConnectivity.sh --help
#
# ### Expected Previous Processing
# 
# * The necessary input files are BOLD from previous processing
# * These may be stored in: "$SubjectsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/ 
#
#~ND~END~

usage() {

# -------------------------------------------------------------------------------------------------------------------
# EXAMPLE inputs from Matlab into fc_ComputeSeedMapsMultiple and fc_ComputeGBC3:
# -------------------------------------------------------------------------------------------------------------------
#  fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf, method, ignore, cv)
#  INPUT
#  flist    - A .list file of subject information.
#  roinfo   - An ROI file.
#  inmask   - An array mask defining which frames to use (1) and which not (0) [0]
#  options  - A string defining which subject files to save ['']:
#  r        - save map of correlations
#  f        - save map of Fisher z values
#  cv       - save map of covariances
#  z        - save map of Z scores
#  targetf  - The folder to save images in ['.'].
#  method   - Method for extracting timeseries - 'mean' or 'pca' ['mean'].
#  ignore   - Do we omit frames to be ignored ['no']
#                  -> no:    do not ignore any additional frames
#                  -> event: ignore frames as marked in .fidl file
#                  -> other: the column in *_scrub.txt file that matches bold file to be used for ignore mask
#  cv       - Whether covariances should be computed instead of correlations.
# -------------------------------------------------------------------------------------------------------------------   
#  fc_ComputeGBC3(flist, command, mask, verbose, target, targetf, rsmooth, rdilate, ignore, time, cv, vstep) 
#  INPUT 
#  flist       - conc-like style list of subject image files or conc files:
#                  subject id:<subject_id>
#                  roi:<path to the individual's ROI file>
#                  file:<path to bold files - one per line>
#               or a well strucutured string (see g_ReadFileList).
#  command     - the type of gbc to run: mFz, aFz, pFz, nFz, aD, pD, nD,
#               mFzp, aFzp, ...
#               <type of gbc>:<parameter>|<type of gbc>:<parameter> ...
#  mask        - An array mask defining which frames to use (1) and
#               which not (0). All if empty.
#  verbose     - Report what is going on. [false]
#  target      - Array of ROI codes that define target ROI [default:
#               FreeSurfer cortex codes]
#  targetf     - Target folder for results.
#  rsmooth     - Radius for smoothing (no smoothing if empty). []
#  rdilate     - Radius for dilating mask (no dilation if empty). []
#  ignore      - The column in *_scrub.txt file that matches bold file to
#               be used for ignore mask. All if empty. []
#  time        - Whether to print timing information. [false]
#  cv          - Whether to compute covariances instead of correlations.
#               [false]
#  vstep       - How many voxels to process in a single step. [1200]
# -------------------------------------------------------------------------------------------------------------------

echo ""
echo "This function implements Global Brain Connectivity (GBC) or seed-based functional connectivity (FC) on the dense or parcellated (e.g. Glasser parcellation)."
echo ""
echo "For more detailed documentation run <help fc_ComputeGBC3>, <help gmrimage.mri_ComputeGBC> or <help fc_ComputeSeedMapsMultiple> inside matlab"
echo ""
echo "-- GENERAL PARMETERS:"
echo ""
echo "      --calculation=<type_of_calculation>      Run <seed>, <gbc> or <dense> calculation for functional connectivity."
echo "      --runtype=<type_of_run>                  Run calculation on a <list> (requires a list input), on <individual> subjects (requires manual specification) or a <group> of individual subjects (equivalent to a list, but with manual specification)"
echo "      --targetf=<path_for_output_file>         Specify the absolute path for output folder. If using --runtype='individual' and left empty the output will default to --inputpath location for each subject"
echo "      --overwrite=<clean_prior_run>            Delete prior run for a given subject. Default [no]."
echo ""
echo "-- REQUIRED GENERAL PARMETERS FOR A GROUP SEED/GBC RUN:"
echo ""
echo "      --flist=<subject_list_file>              Specify *.list file of subject information. If specified then --subjectsfolder, --inputfile, --subject and --outname are omitted"
echo ""
echo "-- REQUIRED GENERAL PARMETERS FOR AN INDIVIDUAL SUBJECT SEED/GBC RUN:"
echo ""
echo "      --subjectsfolder=<folder_with_subjects>             Path to study subjects folder"
echo "      --subjects=<list_of_cases>                          List of subjects to run"
echo "      --inputfiles=<files_to_compute_connectivity_on>     Specify the comma separated file names you want to use (e.g. /bold1_Atlas_MSMAll.dtseries.nii,bold2_Atlas_MSMAll.dtseries.nii)"
echo "      --inputpath=<path_for_input_file>                   Specify path of the file you want to use relative to the master study folder and subject directory (e.g. /images/functional/)"
echo "      --outname=<name_of_output_file>                     Specify the suffix name of the output file name"  
echo ""
echo "-- REQUIRED GBC PARMETERS:"
echo ""
echo "      --target=<which_roi_to_use>             Array of ROI codes that define target ROI [default: FreeSurfer cortex codes]"
echo "      --rsmooth=<smoothing_radius>            Radius for smoothing (no smoothing if empty). Default is []"
echo "      --rdilate=<dilation_radius>             Radius for dilating mask (no dilation if empty). Default is []"
echo "      --gbc-command=<type_of_gbc_to_run>      Specify the the type of gbc to run. This is a string describing GBC to compute. E.g. 'mFz:0.1|mFz:0.2|aFz:0.1|aFz:0.2|pFz:0.1|pFz:0.2' "
echo ""
echo "          > mFz:t  ... computes mean Fz value across all voxels (over threshold t) "
echo "          > aFz:t  ... computes mean absolute Fz value across all voxels (over threshold t) "
echo "          > pFz:t  ... computes mean positive Fz value across all voxels (over threshold t) "
echo "          > nFz:t  ... computes mean positive Fz value across all voxels (below threshold t) "
echo "          > aD:t   ... computes proportion of voxels with absolute r over t "
echo "          > pD:t   ... computes proportion of voxels with positive r over t "
echo "          > nD:t   ... computes proportion of voxels with negative r below t "
echo "          > mFzp:n ... computes mean Fz value across n proportional ranges "
echo "          > aFzp:n ... computes mean absolute Fz value across n proportional ranges "
echo "          > mFzs:n ... computes mean Fz value across n strength ranges "
echo "          > pFzs:n ... computes mean Fz value across n strength ranges for positive correlations "
echo "          > nFzs:n ... computes mean Fz value across n strength ranges for negative correlations "
echo "          > mDs:n  ... computes proportion of voxels within n strength ranges of r "
echo "          > aDs:n  ... computes proportion of våoxels within n strength ranges of absolute r "
echo "          > pDs:n  ... computes proportion of voxels within n strength ranges of positive r "
echo "          > nDs:n  ... computes proportion of voxels within n strength ranges of negative r "  
echo ""
echo "-- OPTIONAL GBC PARMETERS:"
echo ""
echo "      --verbose=<print_output_verbosely>   Report what is going on. Default is [false]"
echo "      --time=<print_time_needed>           Whether to print timing information. [false]"
echo "      --vstep=<how_many_voxels>            How many voxels to process in a single step. Default is [1200]"
echo ""
echo "-- REQUIRED SEED FC PARMETERS:"
echo ""
echo "      --roinfo=<roi_seed_files>            An ROI file for the seed connectivity "
echo ""
echo "-- OPTIONAL SEED FC PARMETERS: "
echo ""
echo "      --method=<method_to_get_timeseries>  Method for extracting timeseries - 'mean' or 'pca' Default is ['mean'] "
echo "      --options=<calculations_to_save>     A string defining which subject files to save. Default assumes all [''] "
echo ""
echo "         > r ... save map of correlations "
echo "         > f ... save map of Fisher z values "
echo "         > cv ... save map of covariances "
echo "         > z ... save map of Z scores "
echo ""
echo "-- OPTIONAL SEED OR GBC PARAMETERS: "   
echo ""
echo "      --extractdata=<save_out_the_data_as_as_csv>      Specify if you want to save out the matrix as a CSV file (only available if the file is a ptseries) "
echo "      --covariance=<compute_covariance>                Whether to compute covariances instead of correlations (true / false). Default is [false]"
echo "      --ignore=<frames_to_ignore>              The column in *_scrub.txt file that matches bold file to be used for ignore mask. All if empty. Default is [] "
echo "      --mask=<which_frames_to_use>             An array mask defining which frames to use (1) and which not (0). All if empty. If single value is specified then this number of frames is skipped."
echo ""
echo "-- REQUIRED PARMETERS FOR A DENSE FC RUN:"
echo ""
echo "      --subjectsfolder=<folder_with_subjects>             Path to study subjects folder"
echo "      --subjects=<list_of_cases>                          List of subjects to run"
echo "      --inputfiles=<files_to_compute_connectivity_on>     Specify the comma separated file names you want to use (e.g. bold1_Atlas_MSMAll.dtseries.nii,bold2_Atlas_MSMAll.dtseries.nii)"
echo "      --mem-limit=<limit-GB>                              Restrict memory. Memory limit expressed in gigabytes. Default [4]"
echo ""
echo "-- OPTIONAL SEED, GBC or DENSE PARAMETERS: "   
echo ""
echo "      --covariance=<compute_covariance>                   Whether to compute covariances instead of correlations (true / false). Default is [false]"
echo ""
echo ""
echo "-- EXAMPLES:"
echo ""
echo "   --> Run directly via ${TOOLS}/${QUNEXREPO}/connector/functions/ComputeFunctionalConnectivity.sh --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
echo ""
reho "           * NOTE: --scheduler is not available via direct script call."
echo ""
echo "   --> Run via qunex computeBOLDfc --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
echo ""
geho "           * NOTE: scheduler is available via qunex call:"
echo "                   --scheduler=<name_of_cluster_scheduler_and_options>  A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
echo ""
echo "           * For SLURM scheduler the string would look like this via the qunex call: "
echo "                   --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
echo ""
echo ""
echo ""
echo "qunex computeBOLDfc \ "
echo "--subjectsfolder='<folder_with_subjects>' \ "
echo "--calculation='seed' \ "
echo "--runtype='individual' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--inputfiles='<files_to_compute_connectivity_on>' \ "
echo "--inputpath='/images/functional' \ "
echo "--extractdata='yes' \ "
echo "--extractdata='yes' \ "
echo "--ignore='udvarsme' \ "
echo "--roinfo='ROI_Names_File.names' \ "
echo "--options='' \ "
echo "--method='' \ "
echo "--targetf='<path_for_output_file>' \ "
echo "--mask='5' \ "
echo "--covariance='false' "
echo ""
echo "qunex computeBOLDfc \ "
echo "--subjectsfolder='<folder_with_subjects>' \ "
echo "--runtype='list' \ "
echo "--flist='subjects.list' \ "
echo "--extractdata='yes' \ "
echo "--outname='<name_of_output_file>' \ "
echo "--ignore='udvarsme' \ "
echo "--roinfo='ROI_Names_File.names' \ "
echo "--options='' \ "
echo "--method='' \ "
echo "--targetf='<path_for_output_file>' \ "
echo "--mask='5' "
echo "--covariance='false' "
echo ""
echo "qunex computeBOLDfc \ "
echo "--subjectsfolder='<folder_with_subjects>' \ "
echo "--calculation='gbc' \ "
echo "--runtype='individual' \ "
echo "--subjects='<comma_separarated_list_of_cases>' \ "
echo "--inputfiles='bold1_Atlas_MSMAll.dtseries.nii' \ "
echo "--inputpath='/images/functional' \ "
echo "--extractdata='yes' \ "
echo "--outname='<name_of_output_file>' \ "
echo "--ignore='udvarsme' \ "
echo "--gbc-command='mFz:' \ "
echo "--targetf='<path_for_output_file>' \ "
echo "--mask='5' \ "
echo "--target='' \ "
echo "--rsmooth='0' \ "
echo "--rdilate='0' \ "
echo "--verbose='true' \ "
echo "--time='true' \ "
echo "--vstep='10000'"
echo "--covariance='false' "
echo ""
echo "qunex computeBOLDfc \ "
echo "--subjectsfolder='<folder_with_subjects>' \ "
echo "--calculation='gbc' \ "
echo "--runtype='list' \ "
echo "--flist='subjects.list' \ "
echo "--extractdata='yes' \ "
echo "--outname='<name_of_output_file>' \ "
echo "--ignore='udvarsme' \ "
echo "--gbc-command='mFz:' \ "
echo "--targetf='<path_for_output_file>' \ "
echo "--mask='5' \ "
echo "--target='' \ "
echo "--rsmooth='0' \ "
echo "--rdilate='0' \ "
echo "--verbose='true' \ "
echo "--time='true' \ "
echo "--vstep='10000'"
echo "--covariance='false' "
echo ""
exit 0
}

# ------------------------------------------------------------------------------
#  -- Setup color outputs
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

# BOLD data should be pre-processed and in NIFTI or CIFTI format
# Mandatory input parameters are defined in the help call

########################################## OUTPUTS #########################################

# -- Outputs will be files located in the location specified in the outputpath

# -- Get the command line options for this script

get_options() {

# opts_GetOpt() {
# sopt="$1"
# shift 1
# for fn in "$@" ; do
#     if [ `echo "$fn" | grep -- "^${sopt}=" | wc -w` -gt 0 ]; then
#         echo "$@" | grep -o -P 'mask.{0,20000}' | sed "s/mask=//" | sed 's/-.*//'
#         MaskVariable=`echo "$@" | grep -o -P 'mask.{0,20000}' | sed "s/mask=//" | sed 's/-.*//'`
#         MaskVariable="--mask=${MaskVariable}"
#         #echo $MaskVariable
#         return 0
#     fi
# done
# }
# 
# MaskFrames=`opts_GetOpt "--mask" "$@"`
# 
# reho "${MaskFrames}"

local scriptName=$(basename ${0})
local arguments=("$@")

# -- Initialize global output variables

unset SubjectsFolder   # --subjectsfolder=
unset CASES            # --subjects=
unset InputFiles       # --inputfile=
unset InputPath        # --inputpath=
unset OutName          #  --outname=
unset OutPath          # --targetf=         
unset Overwrite        # --overwrite=      
unset ExtractData      # --extractdata=
unset Calculation      # --calculation=   
unset RunType          # --runtype=       
unset FileList         # --flist=         
unset IgnoreFrames     # --ignore=         
unset MaskFrames       # --mask=      
unset Covariance       # --covariance=      
unset TargetROI        # --target=         
unset RadiusSmooth     # --rsmooth=      
unset RadiusDilate     # --rdilate=      
unset GBCCommand       # --gbc-command=      
unset Verbose          # --verbose=      
unset ComputeTime      # --time=         
unset VoxelStep        # --vstep=         
unset ROIInfo          # --roinfo=         
unset FCCommand        # --options=      
unset Method           # --method=      
unset MemLimit         # --mem-limit=      

runcmd=""

# -- Parse arguments
local index=0
local numArgs=${#arguments[@]}
local argument

while [ ${index} -lt ${numArgs} ]; do
    argument=${arguments[index]}
    case ${argument} in
        --help)
            usage
            ;;
        --version)
            version_show $@
            exit 0
            ;;
        --subjectsfolder=*)
            SubjectsFolder=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --subjects=*)
            CASES=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --inputfiles=*)
            InputFiles=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --inputpath=*)
            InputPath=${argument/*=/""}
            index=$(( index + 1 ))
            ;;                   
        --outname=*)
            OutName=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --targetf=*)
            OutPath=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --overwrite=*)
            Overwrite=${argument/*=/""}
            index=$(( index + 1 ))
            ;;      
        --extractdata=*)
            ExtractData=${argument/*=/""}
            index=$(( index + 1 ))
            ;;    
        --calculation=*)
            Calculation=${argument/*=/""}
            index=$(( index + 1 ))
            ;;       
        --runtype=*)
            RunType=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --flist=*)
            FileList=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --ignore=*)
            IgnoreFrames=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --mask=*)
             MaskFrames=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --covariance=*)
            Covariance=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --target=*)
            TargetROI=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --rsmooth=*)
            RadiusSmooth=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --rdilate=*)
            RadiusDilate=${argument/*=/""}
            index=$(( index + 1 ))
            ;;  
        --gbc-command=*)
            GBCCommand=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --verbose=*)
            Verbose=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --time=*)
            ComputeTime=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --vstep=*)
            VoxelStep=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --roinfo=*)
            ROIInfo=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --options=*)
            FCCommand=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --method=*)
            Method=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --mem-limit=*)
            MemLimit=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        *)
              usage
              reho "ERROR: Unrecognized Option: ${argument}"
              echo ""
              exit 1
             ;;
    esac
done
echo ""

# -- Check general required parameters

if [ -z ${OutPath} ]; then
    echo ""
    reho "ERROR: <path_for_output> not specified. Check usage."; echo ""
    exit 1
fi
if [ -z ${Calculation} ]; then
    echo ""
    reho "ERROR: <type_of_calculation> not specified. Check usage."; echo ""
    exit 1
fi
if [ ${Calculation} == "dense" ]; then
    RunType="individual"
fi
if [ -z ${RunType} ]; then
    echo ""
    reho "ERROR: <type_of_run> not specified. Check usage."; echo ""
    exit 1
fi
    
# -- Check run type (group or individual)
if [ ${RunType} == "individual" ] || [ ${RunType} == "group" ]; then
    # -- Check options for individual run
    if [ -z ${SubjectsFolder} ]; then
        echo ""
        reho "ERROR: <subjects-folder-path> not specified>. Check usage."; echo ""
        echo ""
        exit 1
    fi
    if [ -z ${CASES} ]; then
        echo ""
        reho "ERROR: <subject_ids> not specified. Check usage."; echo ""
        echo ""
        exit 1
    fi
    if [ -z ${InputFiles} ]; then
        echo ""
        reho "ERROR: <file(s)_to_compute_connectivity_on> not specified. Check usage."; echo ""
        echo ""
        exit 1
    fi
    if [ -z ${InputPath} ]; then
        echo ""
        reho "ERROR: <absolute_path_to_data> not specified. Check usage."; echo ""
        echo ""
        exit 1
    fi
    if [ -z ${OutName} ]; then
        echo ""
        reho "ERROR: <name_of_output_file> not specified. Check usage."; echo ""
        exit 1
    fi
fi

# -- Check options for group run
if [ ${RunType} == "list" ]; then
    if [ -z ${FileList} ]; then
        echo ""
        reho "ERROR: <group_list_file_to_compute_connectivity_on> not specified. Check usage."; echo ""
        echo ""
        exit 1
    fi
fi
# -- Check additional mandatory options
if [ ${Calculation} != "dense" ]; then
    if [ -z ${IgnoreFrames} ]; then
        reho "WARNING: <bad_movement_frames_to_ignore_command> not specified. Assuming no input."
        IgnoreFrames=""
        echo ""
    fi
    if [ -z ${MaskFrames} ]; then
        reho "WARNING: <frames_to_mask_out> not specified. Assuming zero."
        MaskFrames=""
        echo ""
    fi
    if [ -z ${Covariance} ]; then
        reho "WARNING: <compute_covariance> not specified. Assuming correlation."
        Covariance="false"
        echo ""
    fi
fi
if [ ${Calculation} == "dense" ]; then
    if [ ${RunType} == "list" ] || [ ${RunType} == "group" ]; then
        echo ""
        reho "ERROR: dense calculation and <list> or <group> selection are not supported. Use <individual>."
        echo ""
        exit 1
    fi
    if [ -z ${MemLimit} ]; then
        reho "WARNING: Memory limit not specified. Assuming 4GB as limit."
        MemLimit="4"
        echo ""
    fi
    if [ -z ${Covariance} ]; then
        reho "WARNING: <compute_covariance> not specified. Assuming correlation."
        Covariance="false"
        echo ""
    fi
fi

# -- Check which function is specified and then check additional needed parameters

# -- Check options for seed FC
if [ ${Calculation} == "seed" ]; then
    if [ -z ${ROIInfo} ]; then
        echo ""
        reho "ERROR: <roi_seed_file> not specified."
        echo ""
        exit 1
    fi
    if [ -z ${FCCommand} ]; then
        reho "WARNING: <calculations_to_save> for seed FC not specified. Assuming all calculations should be saved."
        FCCommand=""
        echo ""
    fi
    if [ -z ${Method} ]; then
        reho "WARNING: <method_to_get_timeseries> not specified. Assuming defaults [mean]."
        Method=""
        echo ""
    fi
fi

# -- Check options for GBC
if [ ${Calculation} == "gbc" ]; then
    if [ -z ${GBCCommand} ]; then
        echo ""
        reho "WARNNING: <commands_for_gbc> not specified. Assuming standard mFz calculation."
        GBCCommand="mFz:"
        echo ""
    fi
    if [ -z ${TargetROI} ]; then
        echo ""
        reho "WARNING: <target_roi_for_gbc> not specified. Assuming whole-brain calculation."
        TargetROI="[]"
        echo ""
    fi
    if [ -z ${RadiusSmooth} ]; then
        echo ""
        reho "WARNING: <smoothing_radius> not specified. Assuming no smoothing."
        RadiusSmooth="0"
        echo ""
    fi
    if [ -z ${RadiusDilate} ]; then
        echo ""
        reho "WARNING: <dilation_radius>. Assuming no dilation."
        RadiusDilate="0"
        echo ""
    fi
    if [ -z ${Verbose} ]; then
        echo ""
        reho "WARNING: <verbose_output> not specified. Assuming 'true'."
        Verbose="true"
        echo ""
    fi
    if [ -z ${ComputeTime} ]; then
        echo ""
        reho "WARNING: <computation_time> not specified. Assuming 'true'"
        ComputeTime="true"
        echo ""
    fi
    if [ -z ${VoxelStep} ]; then
        echo ""
        reho "WARNING: <voxel_steps_to_use> not specified. Assuming '1200'"
        VoxelStep="1200"
        echo ""
    fi
fi

# -- Set StudyFolder
cd $SubjectsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null

# -- Report options
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "  OutPath: ${OutPath}"
echo "  Overwrite: ${Overwrite}"
echo "  ExtractData: ${ExtractData}"
echo "  Calculation: ${Calculation}"
echo "  RunType: ${RunType}"
echo "  IgnoreFrames: ${IgnoreFrames}"
echo "  MaskFrames: ${MaskFrames}"
echo "  Covariance: ${Covariance}"
if [ ${RunType} == "list" ]; then
    echo "  FileList: ${FileList}"
fi
if [ ${RunType} == "individual" ] || [ ${RunType} == "group" ]; then
    echo "  SubjectsFolder: ${SubjectsFolder}"
    echo "  Subjects: ${CASES}"
    echo "  InputFiles: ${InputFiles}"
    echo "  InputPath: ${InputPath}"
    echo "  OutName: ${OutName}"
fi
if [ ${Calculation} == "gbc" ]; then
    echo "  TargetROI: ${TargetROI}"
    echo "  RadiusSmooth: ${RadiusSmooth}"
    echo "  RadiusDilate: ${RadiusDilate}"
    echo "  GBCCommand: ${GBCCommand}"
    echo "  Verbose: ${Verbose}"
    echo "  ComputeTime: ${ComputeTime}"
    echo "  VoxelStep: ${VoxelStep}"
fi
if [ ${Calculation} == "seed" ]; then
    echo "  ROIInfo: ${ROIInfo}"
    echo "  FCCommand: ${FCCommand}"
    echo "  Method: ${Method}"
fi
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""

}

######################################### DO WORK ##########################################

main() {

# -- Get Command Line Options
get_options $@

# -- Parse all the input cases for an individual or group run
INPUTCASES=`echo "$CASES" | sed 's/,/ /g'`

# -- Define all inputs and outputs depending on data type input
if [ ${RunType} == "individual" ]; then
    for INPUTCASE in ${INPUTCASES}; do
        # -- Define inputs
        geho "--- Establishing paths for all input and output folders:"
        echo ""
        if [ ${OutPath} == "" ]; then
            OutPath=${SubjectsFolder}/${INPUTCASE}/${InputPath}
        fi
        # -- Parse input from the InputFiles variable
        InputFiles=`echo "${InputFiles}" | sed 's/,/ /g;s/|/ /g'`
        if [ ${Calculation} != "dense" ]; then
            # -- Cleanup prior tmp lists
            rm -rf ${SubjectsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName} > /dev/null 2>&1    
            # -- Generate output directories
            mkdir ${SubjectsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName} > /dev/null 2>&1
            mkdir ${OutPath} > /dev/null 2>&1
            # -- Generate the temp list
            echo "subject id:${INPUTCASE}" >> ${SubjectsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName}/${OutName}.list
            for InputFile in ${InputFiles}; do echo "file:${SubjectsFolder}/${INPUTCASE}/${InputPath}/${InputFile}" >> ${SubjectsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName}/${OutName}.list; done
            FinalInput="${SubjectsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName}/${OutName}.list"
        fi
    done
fi

if [ ${RunType} == "group" ] && [ ${Calculation} != "dense" ]; then
    # -- Generate output directories
    mkdir ${OutPath} > /dev/null 2>&1
    # -- Cleanup prior tmp lists
    rm -rf ${OutPath}/templist_${Calculation}_${OutName} > /dev/null 2>&1    
    mkdir ${OutPath}/templist_${Calculation}_${OutName} > /dev/null 2>&1    
    for INPUTCASE in $INPUTCASES; do
        # -- Define inputs
        geho "--- Establishing paths for all input and output folders for $INPUTCASE:"
        echo ""
        # -- Parse input from the InputFiles variable
        InputFiles=`echo "$InputFiles" | sed 's/,/ /g;s/|/ /g'`
        # -- Generate the temp list
        echo "subject id:$INPUTCASE" >> ${OutPath}/templist_${Calculation}_${OutName}/${OutName}.list
        for InputFile in ${InputFiles}; do echo "file:${SubjectsFolder}/${INPUTCASE}/${InputPath}/${InputFile}" >> ${OutPath}/templist_${Calculation}_${OutName}/${OutName}.list; done
        FinalInput="${OutPath}/templist_${Calculation}_${OutName}/${OutName}.list"
    done
fi

if [ ${Calculation} != "dense" ]; then
    # -- Echo inputs
    echo ""
    echo "--- Functional connectivity inputs:"
    echo ""
    more ${FinalInput}
    echo ""
    # -- Echo outputs
    echo "Seed functional connectivity will be saved here for each specified ROI:"
    echo "  --> ${OutPath}"
    # -- Check if list set
    if [ ${RunType} == "list" ]; then
        FinalInput=${FileList}
    fi
    # -- Check if FC seed run is specified
        if [ -z "$ExtractData" ]; then ExtractData=""; fi
        if [ -z "$Covariance" ]; then Covariance="true"; fi
        if [ -z "$Verbose" ]; then Verbose="true"; fi
        if [ -z "$MaskFrames" ]; then MaskFrames="0"; fi
        if [ -z "$OutPath" ]; then OutPath="/images/functional"; fi
        if [ -z "$IgnoreFrames" ]; then IgnoreFrames="udvarsme"; fi
    if [ ${Calculation} == "seed" ]; then
        # -- run FC seed command: 
        # Call to get matlab help --> ${QUNEXMCOMMAND} "help fc_ComputeGBC3,quit()"
        # Full function input     --> fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf, method, ignore, cv)
        # Example with string input --> ${QUNEXMCOMMAND} "fc_ComputeSeedMapsMultiple('listname:$CASE-$OutName|subject id:$CASE|file:$InputFile', '$ROIInfo', $MaskFrames, '$FCCommand', '$OutPath', '$Method', '$IgnoreFrames', $Covariance);,quit()"
        if [ -z "$Method" ]; then Method="mean"; fi
        if [ -z "$FCCommand" ]; then FCCommand="all"; fi
        ${QUNEXMCOMMAND} "fc_ComputeSeedMapsMultiple('$FinalInput', '$ROIInfo', $MaskFrames, '$FCCommand', '${OutPath}', '$Method', '$IgnoreFrames', $Covariance);,quit()"
    fi
    # -- Check if GBC seed run is specified
    if [ ${Calculation} == "gbc" ]; then
        # -- run GBC seed command: 
        # Call to get matlab help --> ${QUNEXMCOMMAND} "help fc_ComputeGBC3,quit()"
        # Full function input     --> fc_ComputeGBC3(flist, command, mask, verbose, target, targetf, rsmooth, rdilate, ignore, time, cv, vstep)
        # Example with string input --> ${QUNEXMCOMMAND}"fc_ComputeGBC3('listname:$CASE-$OutName|subject id:$CASE|file:$InputFile','$GBCCommand', $MaskFrames, $Verbose, $TargetROI, '$OutPath', $RadiusSmooth, $RadiusDilate, '$IgnoreFrames', $ComputeTime, $Covariance, $VoxelStep);,quit()"
        if [ -z "$TargetROI" ]; then TargetROI=""; fi
        if [ -z "$GBCCommand" ]; then GBCCommand="mFz:"; fi
        if [ -z "$RadiusSmooth" ]; then RadiusSmooth="0"; fi
        if [ -z "$RadiusDilate" ]; then RadiusDilate="0"; fi
        if [ -z "$ComputeTime" ]; then ComputeTime="true"; fi
        if [ -z "$VoxelStep" ]; then VoxelStep="1000"; fi
        ${QUNEXMCOMMAND} "fc_ComputeGBC3('$FinalInput','$GBCCommand', $MaskFrames, $Verbose, $TargetROI, '${OutPath}', $RadiusSmooth, $RadiusDilate, '$IgnoreFrames', $ComputeTime, $Covariance, $VoxelStep);,quit()"
    fi
    # -- Remove temp lists
    echo ""
    echo ""
    echo ""
    geho "--- Removing temporary list files: ${OutPath}/templist_${Calculation}_${OutName}"
    echo ""
    rm -rf ${OutPath}/templist_${Calculation}_${OutName} > /dev/null 2>&1
fi

# -- Check if dense run is specified
if [ ${Calculation} == "dense" ]; then
    for INPUTCASE in ${INPUTCASES}; do
        geho "--- Running Dense Connectome on BOLD data for ${INPUTCASE}. Note: need ~30GB free RAM at any one time per subject!"
        echo ""
        # -- Parse input from the InputFiles variable
        InputFiles=`echo "${InputFiles}" | sed 's/,/ /g;s/|/ /g'`
        # -- Generate output directories
        mkdir ${OutPath} > /dev/null 2>&1
        # -- Generate the temp list
        for InputFile in ${InputFiles}; do
            dtseriesCheck=`echo ${InputFile} | grep ".dtseries.nii"`
            if [[ ! -z ${dtseriesCheck} ]]; then
                InputFileName=`echo ${InputFile} | sed 's/.dtseries.nii//'`
                BOLDNumber=`echo ${InputFile} | egrep -o [0-9]+ | head -n1`
            else
                reho " ---> Requesting ${InputFile}. This is not a valid .dtseries.nii file"
                return 1
            fi
            # -- Parameters for wb_command -cifti-correlation: 
                #
                # [-weights] - specify column weights
                #    <weight-file> - text file containing one weight per column
                # [-fisher-z] - apply fisher small z transform (ie, artanh) to correlation
                # [-no-demean] - instead of correlation, do dot product of rows, then
                #    normalize by diagonal
                # [-covariance] - compute covariance instead of correlation
                # [-mem-limit] - restrict memory
                #    <limit-GB> - memory limit in gigabytes
                #
            if [[ ${Covariance} == "false" ]]; then
                wb_command -cifti-correlation ${SubjectsFolder}/${INPUTCASE}/${InputPath}/${InputFile} \
                ${SubjectsFolder}/${INPUTCASE}/${InputPath}/${InputFileName}_r_Fz.dconn.nii \
                -weights ${SubjectsFolder}/${INPUTCASE}/${InputPath}/movement/bold${BOLDNumber}.use \
                -fisher-z -mem-limit ${MemLimit}
                OutDense="${SubjectsFolder}/${INPUTCASE}/${InputPath}/${InputFileName}_r_Fz.dconn.nii"
            else
                wb_command -cifti-correlation ${SubjectsFolder}/${INPUTCASE}/${InputPath}/${InputFile} \
                ${SubjectsFolder}/${INPUTCASE}/${InputPath}/${InputFileName}_cov.dconn.nii \
                -weights ${SubjectsFolder}/${INPUTCASE}/${InputPath}/movement/bold${BOLDNumber}.use \
                -mem-limit ${MemLimit} -covariance
                OutDense="${SubjectsFolder}/${INPUTCASE}/${InputPath}/${InputFileName}_cov.dconn.nii"
            fi
            if [[ -f ${OutDense} ]]; then
                echo ""
                geho "--- Dense connectivity calculation completed for: "
                geho "     ${OutDense}"
                echo ""
            else
                echo ""
                reho "--- Result for ${OutDense} not found" 
                reho "    Something went wrong."
                echo ""
                RunError="yes"
            fi
        done
    done
fi

# -- Check if data extraction requested
if [[ "$ExtractData" == "yes" ]] && [[ ${Calculation} != "dense" ]]; then 
    geho "--- Saving out the data in a CSV file..."
    # -- Specify pconn file inputs and outputs
    PConnBOLDInputs=`ls ${OutPath}/${OutName}*ptseries.nii`
    if [ -z ${PConnBOLDInputs} ]; then
        echo ""
        reho "WARNING: No parcellated files found for this run."
        echo ""
    else
        for PConnBOLDInput in ${PConnBOLDInputs}; do 
            CSVPConnFileExt=".csv"
            CSVPConnBOLDOutput="${PConnBOLDInput}_${CSVPConnFileExt}"
            rm -f ${CSVPConnBOLDOutput} > /dev/null 2>&1
            wb_command -nifti-information -print-matrix "$PConnBOLDInput" >> "$CSVPConnBOLDOutput"
        done
    fi
fi
# -- Perform completion checks
if [[ ${RunType} == "group" ]] && [[ ${Calculation} != "dense" ]]; then
    CheckRun=`ls -t1 ${OutPath}/${OutName}*.nii 2> /dev/null | head -n 1`
   if [[ ! -z ${CheckRun} ]]; then
        echo ""
        geho "--- Connectivity calculation completed for ${OutPath}/${OutName}."
        echo ""
    else
        echo ""
        reho "--- Result for ${OutPath}/${OutName} not found. Something went wrong."
        echo ""
        RunError="yes"
    fi
fi
if [[ ${RunType} == "individual" ]] && [[ ${Calculation} != "dense" ]]; then
    CheckRun=`ls -t1 ${OutPath}/${OutName}*.nii 2> /dev/null | head -n 1`
   if [[ ! -z ${CheckRun} ]]; then
        echo ""
        geho "--- Connectivity calculation completed for ${OutPath}/${OutName}."
        echo ""
    else
        echo ""
        reho "--- Result for ${OutPath}/${OutName} not found. Something went wrong."
        echo ""
        RunError="yes"
    fi
fi
if [[ -z ${RunError} ]]; then 
    echo ""
    geho "------------------------- Successful completion of work --------------------------------"
    echo ""
else
    echo ""
    reho "--- Results missing. Something went wrong with ${Calculation} calculation."
    echo ""
    exit 1
fi

}

######################################### END OF WORK ##########################################

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
