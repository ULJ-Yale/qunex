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
#  BOLDcomputeFC.sh
#
# ## LICENSE
#
# * The BOLDcomputeFC.sh = the "Software"
# * This Software conforms to the license outlined in the Qu|Nex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ### TODO
#
# ## Description 
#   
# This script, BOLDcomputeFC.sh, implements functional connectivity
# using Qu|Nex Suite Matlab tools (e.g. fc_ComputeSeedMapsMultiple)
# 
# ## Prerequisite Installed Software
#
# * Qu|Nex Suite
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. $./BOLDcomputeFC.sh --help
#
# ### Expected Previous Processing
# 
# * The necessary input files are BOLD from previous processing
# * These may be stored in: "$SessionsFolder/$CASE/hcp/$CASE/MNINonLinear/Results/ 
#
#~ND~END~

usage() {

# -------------------------------------------------------------------------------------------------------------------
# EXAMPLE inputs from Matlab into fc_ComputeSeedMapsMultiple and fc_ComputeGBC3:
# -------------------------------------------------------------------------------------------------------------------
#  fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf, method, ignore, cv)
#  INPUT
#  flist    - A .list file with session information.
#  roinfo   - An ROI file.
#  inmask   - An array mask defining which frames to use (1) and which not (0) [0]
#  options  - A string defining which session files to save ['']:
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
#  flist       - conc-like style list of session image files or conc files:
#                  session id:<session_id>
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
 echo "This function implements Global Brain Connectivity (GBC) or seed-based "
 echo "functional connectivity (FC) on the dense or parcellated (e.g. Glasser "
 echo "parcellation)."
 echo ""
 echo "For more detailed documentation run <help fc_ComputeGBC3>, "
 echo "<help nimage.img_ComputeGBC> or <help fc_ComputeSeedMapsMultiple> inside MATLAB."
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "--calculation    Run <seed>, <gbc> or <dense> calculation for functional"
 echo "                 connectivity."
 echo "--runtype        Run calculation on a <list> (requires a list input), on "
 echo "                 <individual> sessions (requires manual specification) or a "
 echo "                 <group> of individual sessions (equivalent to a list, but "
 echo "                 with manual specification)"
 echo "--targetf        Specify the absolute path for output folder. If using" 
 echo "                 --runtype='individual' and left empty the output will "
 echo "                 default to --inputpath location for each session"
 echo "--overwrite      Delete prior run for a given session [no]."
 echo "--covariance     Whether to compute covariances instead of correlations "
 echo "                 (true / false). Default is [false]"
 echo ""
 echo "INPUTS FOR A GROUP SEED/GBC RUN"
 echo "==============================="
 echo ""
 echo "--flist          Specify *.list file of session information. If specified then" 
 echo "                 --sessionsfolder, --inputfile, --session and --outname are"
 echo "                 omitted"
 echo ""
 echo "INPUTS FOR AN INDIVIDUAL SESSION SEED/GBC RUN"
 echo "============================================="
 echo ""
 echo "--sessionsfolder   Path to study sessions folder"
 echo "--sessions         Comma separated list of sessions to run"
 echo "--inputfiles       Specify the comma separated file names you want to use "
 echo "                   (e.g. /bold1_Atlas_MSMAll.dtseries.nii,bold2_Atlas_MSMAll.dtseries.nii)"
 echo "--inputpath        Specify path of the file you want to use relative to the "
 echo "                   master study folder and session directory "
 echo "                   (e.g. /images/functional/)"
 echo "--outname          Specify the suffix name of the output file name"  
 echo ""
 echo "INPUTS FOR GBC"
 echo "=============="
 echo ""
 echo "--target           Array of ROI codes that define target ROI"
 echo "                   [default: FreeSurfer cortex codes]"
 echo "--rsmooth          Radius for smoothing (no smoothing if empty). []"
 echo "--rdilate          Radius for dilating mask (no dilation if empty). []"
 echo "--gbc-command      Specify the the type of gbc to run. This is a string "
 echo "                   describing GBC to compute. "
 echo "                   E.g. 'mFz:0.1|mFz:0.2|aFz:0.1|aFz:0.2|pFz:0.1|pFz:0.2' "
 echo ""
 echo "                   mFz:t"
 echo "                       computes mean Fz value across all voxels (over "
 echo "                       threshold t)"
 echo "                   aFz:t"
 echo "                       computes mean absolute Fz value across all voxels "
 echo "                       (over threshold t) "
 echo "                   pFz:t"
 echo "                       computes mean positive Fz value across all voxels "
 echo "                       (over threshold t) "
 echo "                   nFz:t"
 echo "                       computes mean positive Fz value across all voxels "
 echo "                       (below threshold t) "
 echo "                   aD:t"
 echo "                       computes proportion of voxels with absolute r over t "
 echo "                   pD:t"
 echo "                       computes proportion of voxels with positive r over t "
 echo "                   nD:t"
 echo "                       computes proportion of voxels with negative r below t "
 echo "                   mFzp:n"
 echo "                       computes mean Fz value across n proportional ranges "
 echo "                   aFzp:n"
 echo "                       computes mean absolute Fz value across n proportional "
 echo "                       ranges "
 echo "                   mFzs:n"
 echo "                       computes mean Fz value across n strength ranges "
 echo "                   pFzs:n"
 echo "                       computes mean Fz value across n strength ranges for "
 echo "                       positive correlations "
 echo "                   nFzs:n"
 echo "                       computes mean Fz value across n strength ranges for "
 echo "                       negative correlations "
 echo "                   mDs:n"
 echo "                       computes proportion of voxels within n strength ranges "
 echo "                       of r "
 echo "                   aDs:n"
 echo "                       computes proportion of våoxels within n strength "
 echo "                       ranges of absolute r "
 echo "                   pDs:n"
 echo "                       computes proportion of voxels within n strength ranges "
 echo "                       of positive r "
 echo "                   nDs:n"
 echo "                       computes proportion of voxels within n strength ranges "
 echo "                       of negative r "  
 echo ""
 echo "--verbose          Report what is going on. Default is [false]"
 echo "--time             Whether to print timing information. [false]"
 echo "--vstep            How many voxels to process in a single step. [1200]"
 echo ""
 echo "INPUTS FOR SEED FC"
 echo "=================="
 echo ""
 echo "--roinfo           An ROI file for the seed connectivity "
 echo "--method           Method for extracting timeseries - 'mean' or 'pca' ['mean'] "
 echo "--options          A string defining which session files to save. Default "
 echo "                   assumes all [''] "
 echo ""
 echo "                   - r ... save map of correlations "
 echo "                   - f ... save map of Fisher z values "
 echo "                   - cv ... save map of covariances "
 echo "                   - z ... save map of Z scores "
 echo ""
 echo "INPUTS FOR SEED OR GBC"
 echo "======================"
 echo ""
 echo "--extractdata      Specify if you want to save out the matrix as a CSV file "
 echo "                   (only available if the file is a ptseries) "
 echo "--ignore           The column in *_scrub.txt file that matches bold file to "
 echo "                   be used for ignore mask. All if empty. Default is [] "
 echo "--mask             An array mask defining which frames to use (1) and which "
 echo "                   not (0). All if empty. If single value is specified then "
 echo "                   this number of frames is skipped."
 echo ""
 echo "INPUTS FOR DENSE FC RUN"
 echo "======================="
 echo ""
 echo "--mem-limit        Restrict memory. Memory limit expressed in gigabytes. [4]"
 echo ""
 echo "EXAMPLE USE"
 echo "==========="
 echo ""
 echo "Run directly via:: "
 echo ""
 echo "  ${TOOLS}/${QUNEXREPO}/connector/functions/BOLDcomputeFC.sh \ "
 echo "      --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
 echo ""
 reho "NOTE: --scheduler is not available via direct script call."
 echo ""
 echo "Run via:: "
 echo ""
 echo "  qunex BOLDcomputeFC --<parameter1> --<parameter2> ... --<parameterN> "
 echo ""
 geho "NOTE: scheduler is available via qunex call."
 echo ""
 echo "--scheduler       A string for the cluster scheduler (e.g. LSF, PBS or SLURM) "
 echo "                  followed by relevant options"
 echo ""
 echo "For SLURM scheduler the string would look like this via the qunex call:: "
 echo ""                   
 echo "  --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
 echo ""
 echo ""
 echo "::"
 echo ""
 echo "  qunex BOLDcomputeFC \ "
 echo "  --sessionsfolder='<folder_with_sessions>' \ "
 echo "  --calculation='seed' \ "
 echo "  --runtype='individual' \ "
 echo "  --sessions='<comma_separarated_list_of_cases>' \ "
 echo "  --inputfiles='<files_to_compute_connectivity_on>' \ "
 echo "  --inputpath='/images/functional' \ "
 echo "  --extractdata='yes' \ "
 echo "  --ignore='udvarsme' \ "
 echo "  --roinfo='ROI_Names_File.names' \ "
 echo "  --options='' \ "
 echo "  --method='' \ "
 echo "  --targetf='<path_for_output_file>' \ "
 echo "  --mask='5' \ "
 echo "  --covariance='false' "
 echo ""
 echo "  qunex BOLDcomputeFC \ "
 echo "  --sessionsfolder='<folder_with_sessions>' \ "
 echo "  --runtype='list' \ "
 echo "  --flist='sessions.list' \ "
 echo "  --extractdata='yes' \ "
 echo "  --outname='<name_of_output_file>' \ "
 echo "  --ignore='udvarsme' \ "
 echo "  --roinfo='ROI_Names_File.names' \ "
 echo "  --options='' \ "
 echo "  --method='' \ "
 echo "  --targetf='<path_for_output_file>' \ "
 echo "  --mask='5' "
 echo "  --covariance='false' "
 echo ""
 echo "  qunex BOLDcomputeFC \ "
 echo "  --sessionsfolder='<folder_with_sessions>' \ "
 echo "  --calculation='gbc' \ "
 echo "  --runtype='individual' \ "
 echo "  --sessions='<comma_separarated_list_of_cases>' \ "
 echo "  --inputfiles='bold1_Atlas_MSMAll.dtseries.nii' \ "
 echo "  --inputpath='/images/functional' \ "
 echo "  --extractdata='yes' \ "
 echo "  --outname='<name_of_output_file>' \ "
 echo "  --ignore='udvarsme' \ "
 echo "  --gbc-command='mFz:' \ "
 echo "  --targetf='<path_for_output_file>' \ "
 echo "  --mask='5' \ "
 echo "  --target='' \ "
 echo "  --rsmooth='0' \ "
 echo "  --rdilate='0' \ "
 echo "  --verbose='true' \ "
 echo "  --time='true' \ "
 echo "  --vstep='10000'"
 echo "  --covariance='false' "
 echo ""
 echo "  qunex BOLDcomputeFC \ "
 echo "  --sessionsfolder='<folder_with_sessions>' \ "
 echo "  --calculation='gbc' \ "
 echo "  --runtype='list' \ "
 echo "  --flist='sessions.list' \ "
 echo "  --extractdata='yes' \ "
 echo "  --outname='<name_of_output_file>' \ "
 echo "  --ignore='udvarsme' \ "
 echo "  --gbc-command='mFz:' \ "
 echo "  --targetf='<path_for_output_file>' \ "
 echo "  --mask='5' \ "
 echo "  --target='' \ "
 echo "  --rsmooth='0' \ "
 echo "  --rdilate='0' \ "
 echo "  --verbose='true' \ "
 echo "  --time='true' \ "
 echo "  --vstep='10000'"
 echo "  --covariance='false' "
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

unset SessionsFolder   # --sessionsfolder=
unset CASES            # --sessions=
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
        --sessionsfolder=*)
            SessionsFolder=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --sessions=*)
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
    if [ -z ${SessionsFolder} ]; then
        echo ""
        reho "ERROR: <sessions-folder-path> not specified>. Check usage."; echo ""
        echo ""
        exit 1
    fi
    if [ -z ${CASES} ]; then
        echo ""
        reho "ERROR: <session_ids> not specified. Check usage."; echo ""
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
cd $SessionsFolder/../ &> /dev/null
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
    echo "  SessionsFolder: ${SessionsFolder}"
    echo "  Sesssions: ${CASES}"
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
            OutPath=${SessionsFolder}/${INPUTCASE}/${InputPath}
        fi
        # -- Parse input from the InputFiles variable
        InputFiles=`echo "${InputFiles}" | sed 's/,/ /g;s/|/ /g'`
        if [ ${Calculation} != "dense" ]; then
            # -- Cleanup prior tmp lists
            rm -rf ${SessionsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName} > /dev/null 2>&1    
            # -- Generate output directories
            mkdir ${SessionsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName} > /dev/null 2>&1
            mkdir ${OutPath} > /dev/null 2>&1
            # -- Generate the temp list
            echo "session id:${INPUTCASE}" >> ${SessionsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName}/${OutName}.list
            for InputFile in ${InputFiles}; do echo "file:${SessionsFolder}/${INPUTCASE}/${InputPath}/${InputFile}" >> ${SessionsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName}/${OutName}.list; done
            FinalInput="${SessionsFolder}/${INPUTCASE}/${InputPath}/templist_${Calculation}_${OutName}/${OutName}.list"
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
        echo "session id:$INPUTCASE" >> ${OutPath}/templist_${Calculation}_${OutName}/${OutName}.list
        for InputFile in ${InputFiles}; do echo "file:${SessionsFolder}/${INPUTCASE}/${InputPath}/${InputFile}" >> ${OutPath}/templist_${Calculation}_${OutName}/${OutName}.list; done
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
        if [ -z "$ExtractData" ]; then ExtractData="no"; fi
        if [ -z "$Covariance" ]; then Covariance="true"; fi
        if [ -z "$Verbose" ]; then Verbose="true"; fi
        if [ -z "$MaskFrames" ]; then MaskFrames="0"; fi
        if [ -z "$OutPath" ]; then OutPath="/images/functional"; fi
        if [ -z "$IgnoreFrames" ]; then IgnoreFrames="udvarsme"; fi
    if [ ${Calculation} == "seed" ]; then
        # -- run FC seed command: 
        # Call to get matlab help --> ${QUNEXMCOMMAND} "help fc_ComputeGBC3,quit()"
        # Full function input     --> fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf, method, ignore, cv)
        # Example with string input --> ${QUNEXMCOMMAND} "fc_ComputeSeedMapsMultiple('listname:$CASE-$OutName|session id:$CASE|file:$InputFile', '$ROIInfo', $MaskFrames, '$FCCommand', '$OutPath', '$Method', '$IgnoreFrames', $Covariance);,quit()"
        if [ -z "$Method" ]; then Method="mean"; fi
        if [ -z "$FCCommand" ]; then FCCommand="all"; fi
        ${QUNEXMCOMMAND} "fc_ComputeSeedMapsMultiple('$FinalInput', '$ROIInfo', $MaskFrames, '$FCCommand', '${OutPath}', '$Method', '$IgnoreFrames', $Covariance);,quit()"
    fi
    # -- Check if GBC seed run is specified
    if [ ${Calculation} == "gbc" ]; then
        # -- run GBC seed command: 
        # Call to get matlab help --> ${QUNEXMCOMMAND} "help fc_ComputeGBC3,quit()"
        # Full function input     --> fc_ComputeGBC3(flist, command, mask, verbose, target, targetf, rsmooth, rdilate, ignore, time, cv, vstep)
        # Example with string input --> ${QUNEXMCOMMAND}"fc_ComputeGBC3('listname:$CASE-$OutName|session id:$CASE|file:$InputFile','$GBCCommand', $MaskFrames, $Verbose, $TargetROI, '$OutPath', $RadiusSmooth, $RadiusDilate, '$IgnoreFrames', $ComputeTime, $Covariance, $VoxelStep);,quit()"
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
        geho "--- Running Dense Connectome on BOLD data for ${INPUTCASE}. Note: need ~30GB free RAM at any one time per session!"
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
                wb_command -cifti-correlation ${SessionsFolder}/${INPUTCASE}/${InputPath}/${InputFile} \
                ${SessionsFolder}/${INPUTCASE}/${InputPath}/${InputFileName}_r_Fz.dconn.nii \
                -weights ${SessionsFolder}/${INPUTCASE}/${InputPath}/movement/bold${BOLDNumber}.use \
                -fisher-z -mem-limit ${MemLimit}
                OutDense="${SessionsFolder}/${INPUTCASE}/${InputPath}/${InputFileName}_r_Fz.dconn.nii"
            else
                wb_command -cifti-correlation ${SessionsFolder}/${INPUTCASE}/${InputPath}/${InputFile} \
                ${SessionsFolder}/${INPUTCASE}/${InputPath}/${InputFileName}_cov.dconn.nii \
                -weights ${SessionsFolder}/${INPUTCASE}/${InputPath}/movement/bold${BOLDNumber}.use \
                -mem-limit ${MemLimit} -covariance
                OutDense="${SessionsFolder}/${INPUTCASE}/${InputPath}/${InputFileName}_cov.dconn.nii"
            fi
            if [[ -f ${OutDense} ]]; then
                echo ""
                geho "--- Dense connectivity calculation completed for: "
                geho "     ${OutDense}"
                echo ""
            else
                echo ""
                reho "ERROR --- Result for ${OutDense} not found" 
                reho "    Something went wrong."
                echo ""
                RunError="yes"
            fi
        done
    done
fi

# -- Check if data extraction requested
if [[ "$ExtractData" == "yes" ]] && [[ ${Calculation} != "dense" ]] && [[ ! `echo ${InputFiles} | grep 'dtseries'` ]]; then 
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
        geho "--- Connectivity calculation completed. Look for files beginning with: "
        geho "    ${OutPath}/${OutName}"
        echo ""
    else
        echo ""
        reho "ERROR --- Result for ${OutPath}/${OutName} not found. Something went wrong."
        echo ""
        RunError="yes"
    fi
fi
if [[ ${RunType} == "individual" ]] && [[ ${Calculation} != "dense" ]]; then
    CheckRun=`ls -t1 ${OutPath}/${OutName}*.nii 2> /dev/null | head -n 1`
   if [[ ! -z ${CheckRun} ]]; then
        echo ""
        geho "--- Connectivity calculation completed. Look for files beginning with: "
        geho "    ${OutPath}/${OutName}"
        echo ""
    else
        echo ""
        reho "ERROR --- Result for ${OutPath}/${OutName} not found. Something went wrong."
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
    reho "ERROR --- Results missing. Something went wrong with ${Calculation} calculation."
    echo ""
    exit 1
fi

}

######################################### END OF WORK ##########################################

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
