#!/bin/sh 
#set -x
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
# * Alan Anticevic, Department of Psychiatry, Yale University
#
# ## PRODUCT
#
#  RunQC.sh is a QC processing wrapper
#
# ## LICENSE
#
# * The RunQC.sh = the "Software"
# * This Software conforms to the license outlined in the QuNex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ## TODO
#
# ## DESCRIPTION 
#
# This script, RunQC.sh, implements quality control for various stages of 
# HCP preprocessed data
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * Connectome Workbench (v1.0 or above)
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./RunQC.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are HCP files from previous processing
# * These may be stored in: "$SubjectsFolder/$CASE/hcp/$CASE/ 
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

SupportedQC="rawNII, T1w, T2w, myelin, BOLD, DWI, general, eddyQC"

usage() {
     echo ""
     echo "This function runs the QC preprocessing for a specified modality / processing step."
     echo ""
     echo "  --> Currently Supported: ${SupportedQC}"
     echo ""
     echo " This function is compatible with both legacy data [without T2w scans] and HCP-compliant data [with T2w scans and DWI]."
     echo ""
     echo " With the exception of rawNII, the function generates 3 types of outputs, which are stored within the Study in <path_to_folder_with_subjects>/QC "
     echo ""
     echo "                *.scene files that contain all relevant data loadable into Connectome Workbench"
     echo "                *.png images that contain the output of the referenced scene file."
     echo "                *.zip file that contains all relevant files to download and re-generate the scene in Connectome Workbench."
     echo ""
     echo "                Note: For BOLD data there is also an SNR txt output if specified."
     echo "                Note: For raw NIFTI QC outputs are generated in: <subjects_folder>/<case>/nii/slicesdir"
     echo ""
     echo "-- REQUIRED GENERAL PARMETERS:"
     echo ""
     echo "--subjectsfolder=<folder_with_subjects>                         Path to study folder that contains subjects"
     echo "--subjects=<list_of_cases>                                      List of subjects to run, separated by commas"
     echo "--modality=<input_modality_for_qc>                              Specify the modality to perform QC on. "
     echo "                                                                Supported ==> rawNII, T1w, T2w, myelin, BOLD, DWI, general, eddyQC"
     echo "                                                                      Note: If selecting 'rawNII' this function performs QC for raw NIFTI images in <subjects_folder>/<case>/nii "
     echo "                                                                            It requires NIFTI images in <subjects_folder>/<case>/nii/ after either BIDS import of DICOM organization. "
     echo "                                                                            Subject-specific output: <subjects_folder>/<case>/nii/slicesdir "
     echo "                                                                            Uses FSL's `slicesdir` script to generate PNGs and an HTML file in the above directory. "
     echo ""
     echo "                                                                      Note: If using 'general' modality, then visualization is $TOOLS/$QuNexREPO/library/data/scenes/qc/TEMPLATE.general.QC.wb.scene"
     echo "                                                                            * This will work on any input file within the subject-specific data hierarchy."
     echo "     --datapath=<path_for_general_scene>                                    * Required ==> Specify path for input path relative to the <subjects_folder> if scene is 'general'."
     echo "     --datafile=<data_input_for_general_scene>                              * Required ==> Specify input data file name"
     echo ""
     echo ""
     echo "-- DWI PARMETERS"
     echo ""
     echo "--dwipath=<path_for_dwi_data>                                   Specify the input path for the DWI data [may differ across studies; e.g. Diffusion or Diffusion or Diffusion_DWI_dir74_AP_b1000b2500]"
     echo "--dwidata=<file_name_for_dwi_data>                              Specify the file name for DWI data [may differ across studies; e.g. data or DWI_dir74_AP_b1000b2500_data]"
     echo "--dtifitqc=<visual_qc_for_dtifit>                               Specify if dtifit visual QC should be completed [e.g. yes or no]"
     echo "--bedpostxqc=<visual_qc_for_bedpostx>                           Specify if BedpostX visual QC should be completed [e.g. yes or no]"
     echo "--eddyqcstats=<qc_stats_for_eddy>                               Specify if EDDY QC stats should be linked into QC folder and motion report generated [e.g. yes or no]"
     echo "--dwilegacy=<dwi_data_processed_via_legacy_pipeline>            Specify if DWI data was processed via legacy pipelines [e.g. yes or no]"
     echo ""
     echo "-- BOLD PARMETERS"
     echo ""
     echo "--boldprefix=<prefix_file_name_for_bold_data>                    Specify the prefix file name for BOLD dtseries data [may differ across studies depending on processing; e.g. BOLD or TASK or REST]"
     echo "                                                                   Note: If unspecified then QC script will assume that folder names containing processed BOLDs are named numerically only (e.g. 1, 2, 3)."
     echo "--boldsuffix=<suffix_file_name_for_bold_data>                    Specify the suffix file name for BOLD dtseries data [may differ across studies depending on processing; e.g. Atlas or MSMAll]"
     echo "--skipframes=<number_of_initial_frames_to_discard_for_bold_qc>   Specify the number of initial frames you wish to exclude from the BOLD QC calculation"
     echo "--snronly=<compute_snr_only_for_bold>                            Specify if you wish to compute only SNR BOLD QC calculation and skip image generation <yes/no>. Default is [no]"
     echo ""
     echo "--bolddata=<bold_run_numbers>                                    Specify BOLD data numbers separated by comma or pipe. E.g. --bolddata='1,2,3,4,5' "
     echo "                                                                   This flag is interchangeable with --bolds or --boldruns to allow more redundancy in specification"
     echo "                                                                   Note: If unspecified empty the QC script will by default look into /<path_to_study_subjects_folder>/<subject_id>/subject_hcp.txt and identify all BOLDs to process"
     echo ""
     # echo "--filterbolds=<select_only_specific_bolds>                       Specify a string that matches the BOLD name in the subjects batch file. E.g. --filterbolds='rest'."
     # echo "                                                                     Note: If --filterbolds is selected, then --subjects input has to be a batch file. 
     # echo "                                                                           Alternatively. it has to be provided in the --subjectsbatchfile parmeter if you wish to work only on select subjects by explicitly setting --subjects flag."
     echo ""
     echo "-- BOLD FC PARMETERS (Requires --boldfc='<pconn or pscalar>',--boldfcinput=<image_input>, --bolddata or --boldruns or --bolds"
     echo ""
     echo "--boldfc=<compute_qc_for_bold_fc>                                Specify if you wish to compute BOLD QC for FC-type BOLD results. Supported: pscalar or pconn. Default is []"
     echo "--boldfcpath=<path_for_bold_fc>                                  Specify path for input FC data. Default is [ <study_folder>/subjects/<subject_id>/images/functional ]"
     echo "--boldfcinput=<data_input_for_bold_fc>                           Required. If no --boldfcpath is provided then specify only data input name after bold<Number>_ which is searched for in <subjects_folder>/<subject_id>/images/functional "
     echo "                                                                 ==> pscalar FC: Atlas_hpss_res-mVWMWB_lpss_CAB-NP-718_r_Fz_GBC.pscalar.nii" 
     echo "                                                                 ==> pconn FC:  Atlas_hpss_res-mVWMWB_lpss_CAB-NP-718_r_Fz.pconn.nii"
     echo ""
     echo ""
     echo "-- OPTIONAL PARMETERS:"
     echo "" 
     echo "--subjectsbatchfile=<subjects_batch_file>                        Absolute path to local batch file with pre-configured processing parameters. " 
     echo "                                                                 Note: It can be used in combination with --subjects to select only specific cases to work on from the batch file." 
     echo "                                                                 Note: If --subjects is omitted in favor of --subjectsbatchfile OR if batch file is provided as input for --subjects flag, then all cases from the batch file are processed."
     echo "--overwrite=<clean_prior_run>                                    Delete prior QC run: yes/no [Default: no]"
     echo "--hcp_suffix=<specify_hcp_suffix_folder_name>                    Allows user to specify subject id suffix if running HCP preprocessing variants []"
     echo "                                                                  e.g. ~/hcp/sub001 & ~/hcp/sub001-run2 ==> Here 'run2' would be specified as --hcp_suffix='run2' "
     echo "--scenetemplatefolder=<path_for_the_template_folder>             Specify the absolute path name of the template folder (default: $TOOLS/${QuNexREPO}/library/data/scenes/qc)"
     echo "                                                                 Note: relevant scene template data has to be in the same folder as the template scenes"
     echo "--outpath=<path_for_output_file>                                 Specify the absolute path name of the QC folder you wish the individual images and scenes saved to."
     echo "                                                                 If --outpath is unspecified then files are saved to: /<path_to_study_subjects_folder>/QC/<input_modality_for_qc>"
     echo "--scenezip=<zip_generate_scene_file>                             Generates a ZIP file with the scene and all relevant files for Connectome Workbench visualization [yes]"
     echo "                                                                 Note: If scene zip set to yes, then relevant scene files will be zipped with an updated relative base folder." 
     echo "                                                                       All paths will be relative to this base --> <path_to_study_subjects_folder>/<subject_id>/hcp/<subject_id>"
     echo "                                                                 The scene zip file will be saved to: "
     echo "                                                                     /<path_for_output_file>/<subject_id>.<input_modality_for_qc>.QC.wb.zip"
     echo "--userscenefile=<user_specified_scene_file>                      User-specified scene file name. --modality info is still required to ensure correct run. Relevant data needs to be provided. Default []"
     echo "--userscenepath=<user_specified_scene_data_path>                 Path for user-specified scene and relevant data in the same location. --modality info is still required to ensure correct run. Default []"
     echo ""
     echo "--timestamp=<specify_time_stamp>                                 Allows user to specify unique time stamp or to parse a time stamp from connector wrapper"
     echo "--suffix=<specify_suffix_id_for_logging>                         Allows user to specify unique suffix or to parse a time stamp from connector wrapper Default is [ <subject_id>_<timestamp> ]"
     echo ""
     echo ""
     echo "  -- OPTIONAL QC PARAMETERS FOR CUSTOM SCENE:"
     echo ""
     echo "--processcustom=<yes/no>                                         Default is [no]. If set to 'yes' then the script looks into: "
     echo "                                                                   ~/<study_path>/processing/scenes/QC/ for additional custom QC scenes."
     echo "                                                                      Note: The provided scene has to conform to QuNex QC template standards.xw"
     echo "                                                                            See $TOOLS/$QuNexREPO/library/data/scenes/qc/ for example templates."
     echo "                                                                            The qc path has to contain relevant files for the provided scene."
     echo ""
     echo "--omitdefaults=<yes/no>     Default is [no]. If set to 'yes' then the script omits defaults."
     echo ""
     echo "-- EXAMPLES:"
     echo ""
     echo "   --> Run directly via ${TOOLS}/${QuNexREPO}/connector/functions/RunQC.sh --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
     echo ""
     reho "           * NOTE: --scheduler is not available via direct script call."
     echo ""
     echo "   --> Run via qunex RunQC --<parameter1> --<parameter2> --<parameter3> ... --<parameterN> "
     echo ""
     geho "           * NOTE: scheduler is available via qunex call:"
     echo "                   --scheduler=<name_of_cluster_scheduler_and_options>  A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by relevant options"
     echo ""
     echo "           * For SLURM scheduler the string would look like this via the qunex call: "
     echo "                   --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<numer_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>' "
     echo ""
     echo ""
     echo "# -- raw NII QC"
     echo "qunex runQC \ "
     echo "--subjectsfolder='<path_to_study_subjects_folder>' \ "
     echo "--subjects='<comma_separated_list_of_cases>' \ "
     echo "--modality='rawNII' "
     echo ""
     echo "# -- T1w QC"
     echo "qunex runQC \ "
     echo "--subjectsfolder='<path_to_study_subjects_folder>' \ "
     echo "--subjects='<comma_separated_list_of_cases>' \ "
     echo "--outpath='<path_for_output_file> \ "
     echo "--scenetemplatefolder='<path_for_the_template_folder>' \ "
     echo "--modality='T1w' \ "
     echo "--overwrite='yes' "
     echo ""
     echo "# -- T2w QC"
     echo "qunex runQC \ "
     echo "--subjectsfolder='<path_to_study_subjects_folder>' \ "
     echo "--subjects='<comma_separated_list_of_cases>' \ "
     echo "--outpath='<path_for_output_file> \ "
     echo "--scenetemplatefolder='<path_for_the_template_folder>' \ "
     echo "--modality='T2w' \ "
     echo "--overwrite='yes'"
     echo ""
     echo "# -- Myelin QC"
     echo "qunex runQC \ "
     echo "--subjectsfolder='<path_to_study_subjects_folder>' \ "
     echo "--subjects='<comma_separated_list_of_cases>' \ "
     echo "--outpath='<path_for_output_file> \ "
     echo "--scenetemplatefolder='<path_for_the_template_folder>' \ "
     echo "--modality='myelin' \ "
     echo "--overwrite='yes'"
     echo ""
     echo "# -- DWI QC "
     echo "qunex runQC \ "
     echo "--subjectsfolder='<path_to_study_subjects_folder>' \ "
     echo "--subjects='<comma_separated_list_of_cases>' \ "
     echo "--scenetemplatefolder='<path_for_the_template_folder>' \ "
     echo "--modality='DWI' \ "
     echo "--outpath='<path_for_output_file> \ "
     echo "--dwilegacy='yes' \ "
     echo "--dwidata='<file_name_for_dwi_data>' \ "
     echo "--dwipath='<path_for_dwi_data>' \ "
     echo "--overwrite='yes'"
     echo ""
     echo "# -- BOLD QC"
     echo "qunex runQC \ "
     echo "--subjectssfolder='<path_to_study_subjects_folder>' \ "
     echo "--subjects='<comma_separated_list_of_cases>' \ "
     echo "--outpath='<path_for_output_file> \ "
     echo "--scenetemplatefolder='<path_for_the_template_folder>' \ "
     echo "--modality='BOLD' \ "
     echo "--bolddata='1' \ "
     echo "--boldsuffix='Atlas' \ "
     echo "--overwrite='yes'"
     echo ""
     echo "# -- BOLD FC QC [pscalar or pconn]"
     echo "qunex runQC \ "
     echo "--overwritestep='yes' \ "
     echo "--subjectsfolder='<path_to_study_subjects_folder>' \ "
     echo "--subjects='<comma_separated_list_of_cases>' \ "
     echo "--modality='BOLD' \ "
     echo "--boldfc='<pscalar_or_pconn>' \ "
     echo "--boldfcinput='<data_input_for_bold_fc>' \ "
     echo "--bolddata='1' \ "
     echo "--overwrite='yes' "
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
# -- Parse and check all arguments
# ------------------------------------------------------------------------------

get_options() {

########### INPUTS ###############

    # -- Various HCP processed modalities

########## OUTPUTS ###############

    # -- Outputs will be files located in the location specified in the outputpath

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

# -- Get the command line options for this script

# -- Initialize global variables
unset SubjectsFolder # --subjectssfolder=
unset CASES # --subjects=
unset Overwrite # --overwrite=
unset OutPath # --outpath
unset scenetemplatefolder # --scenetemplatefolder
unset UserSceneFile # --userscenefile
unset UserScenePath # --userscenepath
unset Modality # --modality
unset DWIPath # --dwipath
unset DWIData  # --dwidata
unset DtiFitQC # --dtifitqc
unset BedpostXQC # --bedpostxqc
unset EddyQCStats # --eddyqcstats
unset DWILegacy # --dwilegacy
unset BOLDS # --bolddata
unset BOLDRUNS # --bolddata
unset BOLDDATA # --bolddata
unset BOLDfc # --boldfc
unset BOLDfcInput # --boldfcinput
unset BOLDfcPath #boldfcpath
unset BOLDPrefix # --boldprefix
unset BOLDSuffix # --boldsuffix
unset SkipFrames # --skipframes
unset SNROnly # --snronly
unset TimeStamp # --timestamp
unset Suffix # --suffix
unset SceneZip # --scenezip
unset RunQCCustom # --processcustom
unset OmitDefaults # --omitdefault
unset HCPSuffix # --hcp_suffix
unset GeneralSceneDataFile # --datafile
unset GeneralSceneDataPath # --datapath
unset SubjectBatchFile # --subjectsbatchfile

runcmd=""

# -- Parse general arguments
SubjectsFolder=`opts_GetOpt "--subjectsfolder" $@`
CASES=`opts_GetOpt "--subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$CASES" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
Overwrite=`opts_GetOpt "--overwrite" $@`
OutPath=`opts_GetOpt "--outpath" $@`
scenetemplatefolder=`opts_GetOpt "--scenetemplatefolder" $@`
Modality=`opts_GetOpt "--modality" $@`
UserSceneFile=`opts_GetOpt "--userscenefile" $@`
UserScenePath=`opts_GetOpt "--userscenepath" $@`
RunQCCustom=`opts_GetOpt "--customqc" $@`
OmitDefaults=`opts_GetOpt "--omitdefaults" $@`
HCPSuffix=`opts_GetOpt "--hcp_suffix" $@`
# -- Parameters if requesting 'general' scene type
GeneralSceneDataFile=`opts_GetOpt "--datafile" $@`
GeneralSceneDataPath=`opts_GetOpt "--datapath" $@`

# -- Parse DWI arguments
DWIPath=`opts_GetOpt "--dwipath" $@`
DWIData=`opts_GetOpt "--dwidata" $@`
DtiFitQC=`opts_GetOpt "--dtifitqc" $@`
BedpostXQC=`opts_GetOpt "--bedpostxqc" $@`
EddyQCStats=`opts_GetOpt "--eddyqcstats" $@`
DWILegacy=`opts_GetOpt "--dwilegacy" $@`
# -- Parse BOLD arguments
BOLDS=`opts_GetOpt "--bolds" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
if [ -z "${BOLDS}" ]; then
    BOLDS=`opts_GetOpt "--boldruns" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
fi
if [ -z "${BOLDS}" ]; then
    BOLDS=`opts_GetOpt "--bolddata" "$@" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`
fi
BOLDRUNS="${BOLDS}"
BOLDDATA="${BOLDS}"
BOLDSuffix=`opts_GetOpt "--boldsuffix" $@`
BOLDPrefix=`opts_GetOpt "--boldprefix" $@`
SkipFrames=`opts_GetOpt "--skipframes" $@`
SNROnly=`opts_GetOpt "--snronly" $@`
BOLDfc=`opts_GetOpt "--boldfc" $@`
BOLDfcInput=`opts_GetOpt "--boldfcinput" $@`
BOLDfcPath=`opts_GetOpt "--boldfcpath" $@`

# -- Parse optional arguments
TimeStamp=`opts_GetOpt "--timestamp" $@`
Suffix=`opts_GetOpt "--suffix" $@`
SceneZip=`opts_GetOpt "--scenezip" $@`

# -- Parse batch file input
SubjectBatchFile=`opts_GetOpt "--subjectsbatchfile" $@`

# -- Check general required parameters
if [ -z ${CASES} ]; then
    usage
    reho "ERROR: <subject_ids> not specified."; echo ""
    exit 1
fi
if [[ ${CASES} == *.txt ]]; then
    SubjectBatchFile="$CASES"
    echo ""
    echo "Using $SubjectBatchFile for input."
    echo ""
    CASES=`more ${SubjectBatchFile} | grep "id:"| cut -d " " -f 2`
fi
if [ -z ${SubjectsFolder} ]; then
    usage
    reho "ERROR: <subjects_folder> not specified."; echo ""
    exit 1
fi
if [ -z ${Overwrite} ]; then
    Overwrite="no"
    echo "Overwrite value not explicitly specified. Using default: ${Overwrite}"; echo ""
fi
if [ -z ${OutPath} ]; then
    OutPath="${SubjectsFolder}/QC/${Modality}"
    echo "Output folder path value not explicitly specified. Using default: ${OutPath}"; echo ""
fi
if [ -z ${Modality} ]; then 
    usage
    reho "ERROR:  Modality to perform QC on missing [Supported: T1w, T2w, myelin, BOLD, DWI]"; echo ""
    exit 1
fi
if [ -z "$RunQCCustom" ]; then 
    RunQCCustom="no"; 
fi
if [ "$RunQCCustom" == "yes" ]; then 
    scenetemplatefolder="${StudyFolder}/processing/scenes/QC/${Modality}"
fi

if [ -z "$OmitDefaults" ]; then 
    OmitDefaults="no"; 
fi
# -- Perform some careful scene checks
if [ -z "$UserSceneFile" ]; then
    if [ ! -z "$UserScenePath" ]; then 
        reho "---> Provided --userscenepath but --userscenefile not specified."
        reho "     Check your inputs and re-run.";
        scenetemplatefolder="${TOOLS}/${QuNexREPO}/library/data/scenes/qc"
        reho "---> Reverting to QuNex defaults: ${scenetemplatefolder}"; echo ""
    fi
    if [ -z "$scenetemplatefolder" ]; then
        scenetemplatefolder="${TOOLS}/${QuNexREPO}/library/data/scenes/qc"
        reho "---> Template folder path value not explicitly specified."; echo ""
        reho "---> Using QuNex defaults: ${scenetemplatefolder}"; echo ""
    fi
    if ls ${scenetemplatefolder}/*${Modality}*.scene 1> /dev/null 2>&1; then 
        echo ""
        geho "---> Scene files found in: "; echo ""
        geho "`ls ${scenetemplatefolder}/*${Modality}*.scene` "; echo ""
    else 
        reho "---> Specified folder contains no scenes: ${scenetemplatefolder}" 
        scenetemplatefolder="${TOOLS}/${QuNexREPO}/library/data/scenes/qc"
        reho "---> Reverting to defaults: ${scenetemplatefolder} "; echo ""
    fi
else
    if [ -f "$UserSceneFile" ]; then
        geho "---> User scene file found: ${UserSceneFile}"; echo ""
        UserScenePath=`echo ${UserSceneFile} | awk -F'/' '{print $1}'`
        UserSceneFile=`echo ${UserSceneFile} | awk -F'/' '{print $2}'`
        scenetemplatefolder=${UserScenePath}
    else
        if [ -z "$UserScenePath" ] && [ -z "$scenetemplatefolder" ]; then 
            reho "---> ERROR: Path for user scene file not specified."
            reho "     Specify --scenetemplatefolder or --userscenepath with correct path and re-run."; echo ""; exit 1
        fi
        if [ ! -z "$UserScenePath" ] && [ -z "$scenetemplatefolder" ]; then 
            scenetemplatefolder=${UserScenePath}
        fi
        if ls ${scenetemplatefolder}/${UserSceneFile} 1> /dev/null 2>&1; then 
            geho "---> User specified scene files found in: ${scenetemplatefolder}/${UserSceneFile} "; echo ""
        else 
            reho "---> ERROR: User specified scene ${scenetemplatefolder}/${UserSceneFile} not found." 
            reho "     Check your inputs and re-run."; echo ""; exit 1
        fi
    fi
fi
if [ -z ${TimeStamp} ]; then
   TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
   Suffix="$CASE_$TimeStamp"
   echo "Time stamp for logging not found. Setting now: ${TimeStamp}"; echo ""
fi
if [ -z ${Suffix} ]; then
   Suffix="$CASE_$TimeStamp"
   echo "Suffix not manually set. Setting default: ${Suffix}"; echo ""
fi
if [ -z ${SceneZip} ]; then
    SceneZip="yes"
    echo "Generation of scene zip file not explicitly provided. Using defaults: ${SceneZip}"; echo ""
fi

if [ -z "$HCPSuffix" ]; then 
    echo "hcp_suffix flag not explicitly provided. Using defaults: ${HCPSuffix}"; echo ""
fi

# -- DWI modality-specific settings:
if [ "$Modality" = "DWI" ]; then
    if [ -z "$DWIPath" ]; then DWIPath="Diffusion"; echo "DWI input path not explicitly specified. Using default: ${DWIPath}"; echo ""; fi
    if [ -z "$DWIData" ]; then DWIData="data"; echo "DWI data name not explicitly specified. Using default: ${DWIData}"; echo ""; fi
    if [ -z "$DWILegacy" ]; then DWILegacy="no"; echo "DWI legacy not specified. Using default: ${scenetemplatefolder}"; echo ""; fi
    if [ -z "$DtiFitQC" ]; then DtiFitQC="no"; echo "DWI dtifit QC not specified. Using default: ${DtiFitQC}"; echo ""; fi
    if [ -z "$BedpostXQC" ]; then BedpostXQC="no"; echo "DWI BedpostX not specified. Using default: ${BedpostXQC}"; echo ""; fi
    if [ -z "$EddyQCStats" ]; then EddyQCStats="no"; echo "DWI EDDY QC Stats not specified. Using default: ${EddyQCStats}"; echo ""; fi
fi
# -- BOLD modality-specific settings:
if [ "$Modality" = "BOLD" ]; then
    # - Check if BOLDS parameter is empty:
    if [ -z "$BOLDS" ]; then 
        echo ""
        echo "Note: BOLD input list not specified. Relying subject_hcp.txt individual information files."
        BOLDS="subject_hcp.txt"
        echo ""
    fi
    
    if [ -z "$BOLDfc" ]; then
        # -- Set BOLD prefix correctly
        if [ -z "$BOLDPrefix" ]; then 
            BOLDPrefix=""; echo "BOLD prefix not specified. Assuming no prefix"; echo ""
        fi
        # -- Set BOLD suffix correctly
        if [ -z "$BOLDSuffix" ]; then 
            BOLDSuffix=""; echo "BOLD suffix not specified. Assuming no suffix"; echo ""
        else
            BOLDSuffix="_${BOLDSuffix}"
        fi
        # -- Set SkipFrames and SNROnly defaults if missing
        if [ -z "$SkipFrames" ]; then SkipFrames="0"; echo ""; fi
        if [ -z "$SNROnly" ]; then SNROnly="no"; echo ""; fi
    fi
    
    if [ ! -z "$BOLDfc" ]; then
        if [ -z "$BOLDfcInput" ]; then 
            reho "--> ERROR: Flag --boldfcinput is missing. Check your inputs and re-run."; echo ""; exit 1
        fi
    fi
fi

# -- General modality settings:
if [ "$Modality" = "general" ] || [ "$Modality" = "General" ] || [ "$Modality" = "GENERAL" ] ; then
    if [ -z "$GeneralSceneDataFile" ]; then reho "--> ERROR: Data input not specified"; echo ""; exit 1; fi
    if [ -z "$GeneralSceneDataPath" ]; then reho "--> ERROR: Data input path not specified"; echo ""; exit 1; fi
fi

# -- Set StudyFolder
cd $SubjectsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null
scriptName=$(basename ${0})

# -- Report options
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "  Study Folder: ${StudyFolder}"
echo "  Subject Folder: ${SubjectsFolder}"
echo "  Subjects: ${CASES}"
echo "  QC Modality: ${Modality}"
echo "  QC Output Path: ${OutPath}"
echo "  Custom QC requested: ${RunQCCustom}"
echo "  HCP suffix: ${HCPSuffix}"
if [ "$RunQCCustom" == "yes" ]; then
    echo "   Custom QC modalities: ${Modality}"
fi
if [ "$Modality" == "BOLD" ] || [ "$Modality" == "bold" ]; then
    if [[ ! -z ${BOLDS} ]]; then
        echo "  BOLD runs requested: ${BOLDS}"
    else
        echo "  BOLD runs requested: all"
    fi
fi
echo "  Omit default QC: ${OmitDefaults} "
echo "  QC Scene Template Folder: ${scenetemplatefolder}"
echo "  QC User-defined Scene: ${UserSceneFile}"
echo "  Overwrite prior run: ${Overwrite}"
echo "  Time stamp for logging: ${TimeStamp}"
echo "  Zip Scene File: ${SceneZip}"
if [ "$Modality" = "DWI" ]; then
    echo "  DWI input path: ${DWIPath}"
    echo "  DWI input name: ${DWIData}"
    echo "  DWI legacy processing: ${DWILegacy}"
    echo "  DWI dtifit QC requested: ${DtiFitQC}"
    echo "  DWI bedpostX QC requested: ${BedpostXQC}"
    echo "  DWI EDDY QC Stats requested: ${EddyQCStats}"
fi
if [ "$Modality" = "BOLD" ]; then
    echo "  BOLD data input: ${BOLDS}"
    echo "  BOLD prefix: ${BOLDPrefix}"
    echo "  BOLD suffix: ${BOLDSuffix}"
    echo "  Skip Initial Frames: ${SkipFrames}"
    echo "  Compute SNR Only: ${SNROnly}"
    if [ "$SNROnly" == "yes" ]; then 
        echo ""
        echo "BOLD SNR only specified. Will skip QC images"
        echo ""
    fi
    if [[ ! -z ${BOLDfc} ]]; then
        echo "  BOLD FC requested: ${BOLDfc}"
        echo "  BOLD FC input: ${BOLDfcInput}"
        echo "  BOLD FC path: ${BOLDfcPath}"
    fi
fi
if [ "$Modality" = "general" ]; then
    echo "  Data input path: ${GeneralSceneDataPath}"
    echo "  Data input: ${GeneralSceneDataFile}"
fi
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""

}

######################################### DO WORK ##########################################

main() {

# -- Get Command Line Options
get_options "$@"

# -- Define final report function
finalReport(){
    if [ "${CompletionCheck}" == "fail" ]; then
       reho "------------------------- ERROR --------------------------------"
       echo ""
       reho "   QC generation did not complete correctly."
       reho "   Check outputs: ${RunQCLogFolder}/QC_${CASE}_UserRunQUEUE_${Modality}_${TimeStamp}.log"
       echo ""
       reho "----------------------------------------------------------------"
       echo ""
    else
       echo ""
       geho "------------------------- Successful completion of work --------------------------------"
       echo ""
    fi
}

for CASE in ${CASES}; do
    
# -- Check if raw NIFTI QC is requested and run it first
if [ "$Modality" == "rawNII" ] || [ "$Modality" == "rawnii" ] || [ "$Modality" == "rawNIFTI" ] || [ "$Modality" == "rawnifti" ]; then 
       Modality="rawNII"
       unset CompletionCheck
       slicesdir ${SubjectsFolder}/${CASE}/nii/*.nii*
       if [ ! -f ${SubjectsFolder}/${CASE}/nii/slicesdir/index.html ]; then
          CompletionCheck="fail"
       fi
    
else
    
    # -- Proceed with other QC steps
    if [ ! -z "$HCPSuffix" ]; then 
        SetHCPSuffix="-${HCPSuffix}"
        geho " ===> HCP suffix specified ${HCPSuffix}"; echo ""
        geho "      Setting hcp folder to: ${StudyFolder}/subjects/${CASE}/hcp/${CASE}${SetHCPSuffix}"; echo ""
    fi

    if [ "$Modality" == "BOLD" ] || [ "$Modality" == "bold" ]; then Modality="BOLD"; fi
    if [ "$Modality" == "DWI" ] || [ "$Modality" == "dwi" ]; then Modality="DWI"; fi
    if [ "$Modality" == "general" ] || [ "$Modality" == "General" ] || [ "$Modality" == "GENERAL" ]; then Modality="general"; fi
    
    TemplateSceneFile="TEMPLATE.${Modality}.QC.wb.scene"
    WorkingSceneFile="${CASE}.${Modality}.QC.wb.scene"
    
    if [ ! -z "$UserSceneFile" ]; then
        TemplateSceneFile"${UserSceneFile}"
        WorkingSceneFile="${CASE}.${Modality}.${UserSceneFile}"
    fi
    
    if [ "$RunQCCustom" == "yes" ]; then
        scenetemplatefolder="${StudyFolder}/processing/scenes/QC/${Modality}"
        CustomTemplateSceneFiles=`ls -f ${scenetemplatefolder}/*.scene | xargs -n 1 basename`
        geho " ===> Custom scenes requested from ${scenetemplatefolder}"; echo ""
        geho "      ${CustomTemplateSceneFiles}"; echo ""
    fi
    
    # -- Check if subject_hcp.txt is present:
    if [[ ${BOLDS} == "subject_hcp.txt" ]]; then
        echo ""
        echo "--- Using subject_hcp.txt individual information files. Verifying that subject_hcp.txt exists."; echo ""
        if [[ -f ${SubjectsFolder}/${CASE}/subject_hcp.txt ]]; then
            echo "${SubjectsFolder}/${CASE}/subject_hcp.txt found. Proceeding..."
        else
            reho "${SubjectsFolder}/${CASE}/subject_hcp.txt NOT found. Check BOLD inputs."
            echo ""
            exit 1
        fi
    fi
        
    # -- Check of overwrite flag was set
    if [ ${Overwrite} == "yes" ]; then
        echo ""
        echo " --- Note: Overwrite requested. Removing existing ${Modality} QC scene: ${OutPath}/${WorkingSceneFile} "
        echo ""
        if [ ${Modality} == "BOLD" ]; then
            for BOLD in $BOLDS
            do
                rm -f ${OutPath}/${CASE}.${Modality}.${BOLD}.* &> /dev/null
            done
        else
            rm -f ${OutPath}/${CASE}.${Modality}.* &> /dev/null
        fi
    fi
    
    # -- Check if a given png exists
    # if [ -f ${OutPath}/${CASE}.${Modality}.QC.png ]; then
    #     echo ""
    #     geho " --- ${Modality} QC scene png file found: ${OutPath}/${WorkingSceneFile}"
    #     echo ""
    #     return 1
    # else
    
    # -- Start of generating QC
    echo ""
    geho " --- Generating ${Modality} QC scene here: ${OutPath}"
    echo ""
    echo ""
    geho " --- Checking and generating output folders..."
    echo ""
    # -- Check general output folders for QC
    if [ ! -d ${SubjectsFolder}/QC ]; then
        mkdir -p ${SubjectsFolder}/QC &> /dev/null
    fi
    # -- Check T1w output folders for QC
    if [ ! -d ${OutPath} ]; then
        mkdir -p ${OutPath} &> /dev/null
    fi
    # -- Define log folder
    RunQCLogFolder=${OutPath}/qclog
    if [ ! -d ${RunQCLogFolder} ]; then
        mkdir -p ${RunQCLogFolder}  &> /dev/null
    fi
    geho "    RunQCLogFolder: ${RunQCLogFolder}"
    geho "    Output path: ${OutPath}"
    echo ""
    
    # fi
    
    # Perform checks if scene has proper info: 
    DummyVariable_Check () {
    if [[ ${Modality} != "BOLD" ]]; then
        DUMMYVARIABLES="DUMMYPATH DUMMYCASE DUMMYTIMESTAMP"
    fi
    if [[ ${Modality} == "BOLD" ]]; then
       DUMMYVARIABLES="DUMMYPATH DUMMYCASE DUMMYBOLDDATA _DUMMYBOLDSUFFIX DUMMYTIMESTAMP DUMMYBOLDANNOT"
    fi
    if [[ ${Modality} == "BOLD" ]] && [[ ! -z ${BOLDfc} ]]; then
       DUMMYVARIABLES="DUMMYPATH DUMMYCASE DUMMYIMAGEPATH DUMMYIMAGEFILE DUMMYTIMESTAMP"
    fi
    if [[ ${Modality} == "general" ]]; then
       DUMMYVARIABLES="DUMMYPATH DUMMYCASE DUMMYIMAGEPATH DUMMYIMAGEFILE DUMMYTIMESTAMP"
    fi
        for DUMMYVARIABLE in ${DUMMYVARIABLES}; do
            echo ""; echo "Checking $DUMMYVARIABLE is present in scene ${scenetemplatefolder}/${TemplateSceneFile} "; echo ""
            if [ -z `cat ${scenetemplatefolder}/${TemplateSceneFile} | grep "${DUMMYVARIABLE}"` ]; then
                echo ""
                reho " ---> ERROR: ${DUMMYVARIABLE} variable not defined in ${scenetemplatefolder}/${TemplateSceneFile} "
                reho "      Fix the scene and re-run!"
                echo ""
                exit 1
            else
                echo ""
                geho " ---> ${DUMMYVARIABLE} variable found in ${scenetemplatefolder}/${TemplateSceneFile} "
                reho "      Proceeding..."
                echo ""
            fi
        done
    }
    
    # -------------------------------------------
    # -- Completion checks
    # -------------------------------------------
    
    completionCheck() {
    
        if [[ ${Modality} != "BOLD" ]]; then
            if [[ -z ${FinalLog} ]]; then reho "--- ERROR: Final log file not defined. Report this error to developers."; echo ""; exit 1; fi
            LogError=`cat ${FinalLog} | grep "ERROR"`
            if [ -f ${OutPath}/${WorkingSceneFile} ] && [ -f ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png ] && [[ ${LogError} == "" ]]; then
                echo ""
                geho "--- Scene file found and generated: ${OutPath}/${WorkingSceneFile}"
                echo ""
                echo ""
                geho "--- PNG file found and generated: ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png "
                echo ""
            else
                echo ""
                reho "--- ERROR: Scene generation for ${OutPath}/${WorkingSceneFile} failed. Check work."; echo ""
                CompletionCheck="fail"
            fi
            if [ "$SceneZip" == "yes" ]; then
                if [ -f ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ]; then
                    echo ""
                    geho "--- Scene zip file found and generated: ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip"
                    echo ""
                else
                    echo ""
                    reho "--- ERROR: Scene zip generation failed. Check work."
                    echo ""
                fi
            fi
        
            if [ "$DtiFitQC" == "yes" ]; then
                ZipSceneFile=${WorkingDTISceneFile}.${TimeStamp}.zip
                if [ -f ${OutPath}/${WorkingDTISceneFile} ]; then
                    echo ""
                    geho "--- Scene file found and generated: ${OutPath}/${WorkingSceneFile}"
                    echo ""
                else
                    echo ""
                    reho "--- ERROR: Scene generation failed for ${OutPath}/${WorkingDTISceneFile}. Check inputs."; echo ""
                    CompletionCheck="fail"
                    return 1
                fi
                if [ "$SceneZip" == "yes" ]; then
                    if [ -f ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.zip]; then
                        echo ""
                        geho "--- Scene zip file found and generated: ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.zip"
                        echo ""
                    else
                        echo ""
                        reho "--- ERROR: Scene zip generation failed for ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.zip. Check work."; echo ""
                        CompletionCheck="fail"
                        return 1
                    fi
                fi
            fi
            
            if [ "$BedpostXQC" == "yes" ]; then
                ZipSceneFile=${WorkingBedpostXSceneFile}.${TimeStamp}.zip
                if [ -f ${OutPath}/${WorkingBedpostXSceneFile} ]; then
                    echo ""
                    geho "--- Scene file found and generated: ${OutPath}/${WorkingBedpostXSceneFile}"
                    echo ""
                else
                    echo ""
                    reho "--- ERROR: Scene generation failed for ${OutPath}/${WorkingBedpostXSceneFile}. Check inputs."; echo ""
                    CompletionCheck="fail"
                    return 1
                fi
                if [ "$SceneZip" == "yes" ]; then
                    if [ -f ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.zip]; then
                        echo ""
                        geho "--- Scene zip file found and generated: ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.zip"
                        echo ""
                    else
                        echo ""
                        reho "--- ERROR: Scene zip generation failed for ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.zip. Check work."; echo ""
                        CompletionCheck="fail"
                        return 1
                    fi
                fi
            fi
        fi

        if [[ ${Modality} == "BOLD" ]]; then
            
            # -- BOLD FC completion check
            if [[ ! -z ${BOLDfc} ]]; then
                 CompletionCheck=""
                 if [[ -z ${FinalLog} ]]; then reho "--- ERROR: Final log file not defined. Report this error to developers."; echo ""; exit 1; fi
                 LogError=`cat ${FinalLog} | grep 'ERROR'`
                 if [ -f ${OutPath}/${WorkingSceneFile} ] && [ -f ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png ] && [[ ${LogError} == "" ]]; then
                     echo ""
                     geho "--- Scene file and PNG file found and generated: ${OutPath}/${WorkingSceneFile}"
                     echo ""
                     CompletionCheck=""
                     return 0
                     if [ "$SceneZip" == "yes" ]; then
                         if [ -f ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ]; then
                             echo ""
                             geho "--- Scene zip file found and generated: ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip"
                             echo ""
                             CompletionCheck=""
                             return 0
                         else
                             echo ""
                             reho "--- ERROR: Scene zip generation not completed."; echo ""
                             CompletionCheck="fail"
                         fi
                     fi
                 else
                     echo ""
                     reho "--- ERROR: Scene and PNG QC generation not completed."; echo ""
                     CompletionCheck="fail"
                 fi
            fi
            
            # -- BOLD raw dtseries QC check
            if [[ -z ${BOLDfc} ]]; then
                # -- TSNR completion check
                TSNRReport="${OutPath}/TSNR_Report_All_${TimeStamp}.txt"
                TSNRReportBOLD="${OutPath}/${CASE}_${BOLD}_TSNR_Report_${TimeStamp}.txt"
                if [[ ${SNROnly} == "yes" ]]; then
                    CompletionCheck=""
                    # -- Echo completion & Check SNROnly flag
                    if [ -f ${TSNRReportBOLD} ]; then
                               echo ""
                               geho "---  SNR calculation requested. SNR completed." 
                               geho "     Subject specific report can be found here: ${TSNRReportBOLD}"
                               echo ""
                               CompletionCheck=""
                    else
                           reho "--- ERROR: SNR report not found for ${CASE} and BOLD ${BOLD}."
                           echo ""
                           CompletionCheck="fail"
                    fi
                fi
                # -- BOLD raw scene completion check w/o TSNR
                if [[ ${SNROnly} != "yes" ]]; then
                   CompletionCheck=""
                   if [ -f ${TSNRReportBOLD} ]; then
                               echo ""
                               geho "---  SNR calculation requested. SNR completed." 
                               geho "     Subject specific report can be found here: ${TSNRReportBOLD}"
                               echo ""
                               CompletionCheck=""
                    else
                           reho "--- ERROR: SNR report not found for ${CASE} and BOLD ${BOLD}."
                           echo ""
                           CompletionCheck="fail"
                    fi
                    
                    if [[ -z ${FinalLog} ]]; then reho "--- ERROR: Final log file not defined. Report this error to developers."; echo ""; exit 1; fi
                    LogError=`cat ${FinalLog} | grep 'ERROR'`
                    
                    if [[ -f ${OutPath}/${WorkingSceneFile} ]] && [[ -f ${OutPath}/${WorkingSceneFile}.${TimeStamp}.GStimeseries.QC.wb.png ]] && [[ ${LogError} == "" ]]; then
                        echo ""
                        geho "--- Scene file found and generated: ${OutPath}/${WorkingSceneFile}"
                        echo ""
                        return 0
                        if [ "$SceneZip" == "yes" ]; then
                            if [ -f ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ]; then
                                echo ""
                                geho "--- Scene zip file found and generated: ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip"
                                echo ""
                                return 0
                            else
                                echo ""
                                reho "--- ERROR: Scene zip generation failed. Check work."; echo ""
                                CompletionCheck="fail"
                            fi
                        fi
                    else
                         echo ""
                         reho "--- ERROR: Scene and PNG QC generation not completed."; echo ""
                         echo ""
                         reho "    ---> Check scene output: ${OutPath}/${WorkingSceneFile}"
                         reho "    ---> Check scene png: ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png"
                         reho "    ---> Check run-specific log: ${FinalLog}"; echo ""
                         CompletionCheck="fail"
                    fi
                fi
            fi
        fi
    }
    
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # =-=-=-=-=- Start of BOLD QC Section =-=-=-=-=
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    
    # -- Check if modality is BOLD
    if [ "$Modality" == "BOLD" ] || [ "$Modality" == "bold" ]; then
        
        # -- Block of code to set BOLD numbers correctly
        # ----------------------------------------------------------------------
        #
        if [ "$BOLDS" == "subject_hcp.txt" ]; then
            geho "--- subject_hcp.txt parameter file specified. Verifying presence of subject_hcp.txt before running QC on all BOLDs..."; echo ""
            if [ -f ${SubjectsFolder}/${CASE}/subject_hcp.txt ]; then
                # -- Stalling on some systems --> BOLDCount=`more ${SubjectsFolder}/${CASE}/subject_hcp.txt | grep "bold" | grep -v "ref" | wc -l`
                BOLDCount=`grep "bold" ${SubjectsFolder}/${CASE}/subject_hcp.txt  | grep -v "ref" | wc -l`
                rm ${SubjectsFolder}/${CASE}/BOLDNumberTmp.txt &> /dev/null
                COUNTER=1; until [ $COUNTER -gt $BOLDCount ]; do echo "$COUNTER" >> ${SubjectsFolder}/${CASE}/BOLDNumberTmp.txt; let COUNTER=COUNTER+1; done
                # -- Stalling on some systems --> BOLDS=`more ${SubjectsFolder}/${CASE}/BOLDNumberTmp.txt`
                BOLDS=`cat ${SubjectsFolder}/${CASE}/BOLDNumberTmp.txt`
                rm ${SubjectsFolder}/${CASE}/BOLDNumberTmp.txt &> /dev/null
                geho "--- Information file ${SubjectsFolder}/${CASE}/subject_hcp.txt found. Proceeding to run QC on the following BOLDs:"; echo ""; echo "${BOLDS}"; echo ""
            else
                reho "--- ERROR: ${SubjectsFolder}/${CASE}/subject_hcp.txt not found. Check presence of file or specify specific BOLDs via input parameter."; echo ""
                exit 1
            fi
        else
            # -- Remove commas or pipes from BOLD input list if still present if using manual input
            BOLDS=`echo "${BOLDS}" | sed 's/,/ /g;s/|/ /g'`; BOLDS=`echo "$BOLDS" | sed 's/,/ /g;s/|/ /g'`
        fi
        #
        # ----------------------------------------------------------------------
        
        # -- Function to run BOLD TSNR
        runsnr_BOLD() {
            TSNRReport="${OutPath}/TSNR_Report_All_${TimeStamp}.txt"
            TSNRReportBOLD="${OutPath}/${CASE}_${BOLD}_TSNR_Report_${TimeStamp}.txt"
            # -- Check completion
            if [[ ${Overwrite} == "yes" ]]; then
                 rm -f ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.txt &> /dev/null
                 rm -f ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.dtseries.nii &> /dev/null
                 rm -f ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.sdseries.nii &> /dev/null
                 rm -f ${OutPath}/${CASE}_${BOLD}_TSNR_Report_*
            fi
            if [[ ${Overwrite} == "no" ]]; then 
                echo ""
                geho "--- Overwrite is set to 'no'. Running checks for completed QC."
                completionCheck
                echo ""
                if [[ ${CompletionCheck} != "fail" ]]; then
                    return 0
                fi
            fi
            # -- Reduce dtseries
            wb_command -cifti-reduce ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}.dtseries.nii TSNR ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_TSNR.dscalar.nii -exclude-outliers 4 4
            # -- Compute SNR
            TSNR=`wb_command -cifti-stats ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_TSNR.dscalar.nii -reduce MEAN`
            # -- Record values 
            TSNRLog="${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_TSNR.dscalar.nii: ${TSNR}"
            # -- Get values for plotting GS chart & Compute the GS scalar series file --> TR
            TR=`fslval ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}.nii.gz pixdim4`
            # -- Regenerate outputs
            wb_command -cifti-reduce ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}.dtseries.nii MEAN ${SubjectsFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.dtseries.nii -direction COLUMN
            wb_command -cifti-stats ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.dtseries.nii -reduce MEAN >> ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.txt
            # -- Check skipped frames
            if [ ${SkipFrames} > 0 ]; then 
                rm -f ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS_omit_initial_${SkipFrames}_TRs.txt &> /dev/null
                tail -n +${SkipFrames} ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.txt >> ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS_omit_initial_${SkipFrames}_TRs.txt
                TR=`cat ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS_omit_initial_${SkipFrames}_TRs.txt | wc -l` 
                wb_command -cifti-create-scalar-series ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS_omit_initial_${SkipFrames}_TRs.txt ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.sdseries.nii -transpose -series SECOND 0 ${TR}
                xmax="$TR"
            else
                wb_command -cifti-create-scalar-series ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.txt ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.sdseries.nii -transpose -series SECOND 0 ${TR}
                xmax=`fslval ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}.nii.gz dim4`
            fi
            # -- Get mix/max stats
            ymax=`wb_command -cifti-stats ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.sdseries.nii -reduce MAX | sort -rn | head -n 1`
            ymin=`wb_command -cifti-stats ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}_GS.sdseries.nii -reduce MAX | sort -n | head -n 1`
            printf "${TSNRLog}\n" >> ${TSNRReport}
            printf "${TSNRLog}\n" >> ${TSNRReportBOLD}
        }
        
        # -- Function to run BOLD FC
        runscene_BOLDfc() {
            if [ -z "$BOLDfcPath" ]; then 
               BOLDfcPath="${SubjectsFolder}/${CASE}/images/functional"
               echo ""
               echo "--- Note: Flag --boldfcpath not provided. Setting now: ${BOLDfcPath}"
               echo ""
            fi
            if [[ ${Overwrite} == "no" ]]; then
                echo ""
                geho "--- Overwrite is set to 'no'. Running checks for completed QC."
                completionCheck
                if [[ ${CompletionCheck} != "fail" ]]; then
                    return 0
                fi
            fi
            echo " ==> Setting up commands to run BOLD FC scene generation"; echo ""
            echo " --- Working on ${OutPath}/${WorkingSceneFile}"; echo ""
            # -- Setup naming conventions before generating scene
            ComRunBoldfc1="sed -i -e 's|DUMMYPATH|$SubjectsFolder|g' ${OutPath}/${WorkingSceneFile}" 
            ComRunBoldfc2="sed -i -e 's|DUMMYCASE|$CASE|g' ${OutPath}/${WorkingSceneFile}"
            # -- Add timestamp to the scene and replace paths: DUMMYIMAGEPATH/DUMMYIMAGEFILE
            BOLDfcInput="bold${BOLD}_${BOLDfcInput}"
            ComRunBoldfc3="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingSceneFile}"
            ComRunBoldfc4="sed -i -e 's|DUMMYIMAGEPATH|$BOLDfcPath|g' ${OutPath}/${WorkingSceneFile}"
            ComRunBoldfc5="sed -i -e 's|DUMMYIMAGEFILE|$BOLDfcInput|g' ${OutPath}/${WorkingSceneFile}"
            # -- Add name of png to scene:
            PNGNameBOLDfc="${WorkingSceneFile}.${TimeStamp}.png"
            ComRunBoldPNGNameBOLDfc="sed -i -e 's|DUMMYPNGNAME|$PNGNameBOLDfc|g' ${OutPath}/${WorkingSceneFile}"
            # -- Output image of the scene
            ComRunBoldfc6="wb_command -show-scene ${OutPath}/${WorkingSceneFile} 1 ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png 1194 539"
            # -- Clean temp scene
            ComRunBoldfc7="rm ${OutPath}/${WorkingSceneFile}-e &> /dev/null"
            # -- Generate Scene Zip File if set to YES
            if [ "$SceneZip" == "yes" ]; then
                geho "--- Scene zip set to: $SceneZip. Relevant scene files will be zipped with the following base folder:" 
                geho "    ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
                echo ""
                geho "--- The zip file will be saved to: "
                geho "    ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip "
                echo ""
                RemoveScenePath="${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
                ComRunBoldfc8="rm ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip &> /dev/null "
                ComRunBoldfc9="cp ${OutPath}/${WorkingSceneFile} ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/"
                ComRunBoldfc10="mkdir -p ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc &> /dev/null"
                ComRunBoldfc11="cp ${BOLDfcPath}/${BOLDfcInput} ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc"
                ComRunBoldfc12="sed -i -e 's|$RemoveScenePath|.|g' ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile}"
                ComRunBoldfc13="sed -i -e 's|$BOLDfcPath|./qc/|g' ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile}" 
                ComRunBoldfc14="cd ${OutPath}; wb_command -zip-scene-file ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile} ${WorkingSceneFile}.${TimeStamp} ${WorkingSceneFile}.${TimeStamp}.zip -base-dir ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
                ComRunBoldfc15="rm ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile}"
                ComRunBoldfc16="cp ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc/"
            fi
            # -- Combine all the calls into a single command
            if [ "$SceneZip" == "yes" ]; then
                ComRunBoldQUEUE="$ComQueue; $ComRunBoldfc1; $ComRunBoldfc2; $ComRunBoldfc3; $ComRunBoldfc4; $ComRunBoldfc5; $ComRunBoldPNGNameBOLDfc; $ComRunBoldfc6; $ComRunBoldfc7; $ComRunBoldfc8; $ComRunBoldfc9; $ComRunBoldfc10; $ComRunBoldfc11; $ComRunBoldfc12; $ComRunBoldfc13; $ComRunBoldfc14; $ComRunBoldfc15; $ComRunBoldfc16"
            else
                ComRunBoldQUEUE="$ComQueue; $ComRunBoldfc1; $ComRunBoldfc2; $ComRunBoldfc3; $ComRunBoldfc4; $ComRunBoldfc5; $ComRunBoldPNGNameBOLDfc; $ComRunBoldfc6; $ComRunBoldfc7"
            fi
        }
        
        # -- Function to run BOLD raw scene QC
        runscene_BOLD() {
            if [[ ${Overwrite} == "no" ]]; then 
                echo ""
                geho "--- Overwrite is set to 'no'. Running checks for completed QC."
                completionCheck
                echo ""
                if [[ ${CompletionCheck} != "fail" ]]; then
                    return 0
                fi
            fi
            # -- Setup naming conventions before generating scene
            ComRunBold1="sed -i -e 's|DUMMYPATH|$SubjectsFolder|g' ${OutPath}/${WorkingSceneFile}" 
            ComRunBold2="sed -i -e 's|DUMMYCASE|$CASE|g' ${OutPath}/${WorkingSceneFile}"
            ComRunBold3="sed -i -e 's|DUMMYBOLDDATA|$BOLD|g' ${OutPath}/${WorkingSceneFile}"
            # -- Set the BOLDSuffix variable
            ComRunBold4="sed -i -e 's|_DUMMYBOLDSUFFIX|$BOLDSuffix|g' ${OutPath}/${WorkingSceneFile}"
            # -- Add timestamp to the scene
            ComRunBold5="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingSceneFile}"
            ComRunBold6="sed -i -e 's|DUMMYBOLDANNOT|$BOLD|g' ${OutPath}/${WorkingSceneFile}"
            # -- Add name of png to scene:
            PNGNameGSMap="${WorkingSceneFile}.GSmap.QC.wb.png"
            PNGNameGStimeseries="${WorkingSceneFile}.GStimeseries.QC.wb.png"
            ComRunBoldPngNameGSMap="sed -i -e 's|DUMMYPNGNAMEGSMAP|$PNGNameGSMap|g' ${OutPath}/${WorkingSceneFile}"
            ComRunBoldPngNameGStimeseries="sed -i -e 's|DUMMYPNGNAMEGSTIME|$PNGNameGStimeseries|g' ${OutPath}/${WorkingSceneFile}"
            # -- Output image of the scene
            ComRunBold7="wb_command -show-scene ${OutPath}/${WorkingSceneFile} 1 ${OutPath}/${WorkingSceneFile}.${TimeStamp}.GSmap.QC.wb.png 1194 539"
            ComRunBold8="wb_command -show-scene ${OutPath}/${WorkingSceneFile} 2 ${OutPath}/${WorkingSceneFile}.${TimeStamp}.GStimeseries.QC.wb.png 1194 539"
            # -- Clean temp scene
            ComRunBold9="rm ${OutPath}/${WorkingSceneFile}-e &> /dev/null"
            # -- Generate Scene Zip File if set to YES
            if [ "$SceneZip" == "yes" ]; then
                geho "--- Scene zip set to: $SceneZip. Relevant scene files will be zipped with the following base folder:" 
                geho "    ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
                echo ""
                geho "--- The zip file will be saved to: "
                geho "    ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip "
                echo ""
                RemoveScenePath="${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
                ComRunBold10="cp ${OutPath}/${WorkingSceneFile} ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/"
                ComRunBold11="rm ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip &> /dev/null "
                ComRunBold12="sed -i -e 's|$RemoveScenePath|.|g' ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile}" 
                ComRunBold13="cd ${OutPath}; wb_command -zip-scene-file ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile} ${WorkingSceneFile}.${TimeStamp} ${WorkingSceneFile}.${TimeStamp}.zip -base-dir ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
                ComRunBold14="rm ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile}"
                ComRunBold15="mkdir -p ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc &> /dev/null"
                ComRunBold16="cp ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc/"
            fi
            # -- Combine all the calls into a single command
            if [ "$SceneZip" == "yes" ]; then
                ComRunBoldQUEUE="$ComQueue; $ComRunBold1; $ComRunBold2; $ComRunBold3; $ComRunBold4; $ComRunBold5; $ComRunBold6; $ComRunBoldPngNameGSMap; $ComRunBoldPngNameGStimeseries; $ComRunBold7; $ComRunBold8; $ComRunBold9; $ComRunBold10; $ComRunBold11; $ComRunBold12; $ComRunBold13; $ComRunBold14; $ComRunBold15; $ComRunBold16"
            else
                ComRunBoldQUEUE="$ComQueue; $ComRunBold1; $ComRunBold2; $ComRunBold3; $ComRunBold4; $ComRunBold5; $ComRunBold6; $ComRunBoldPngNameGSMap; $ComRunBoldPngNameGStimeseries; $ComRunBold7; $ComRunBold8; $ComRunBold9"
            fi
        }

        # -- Code block to run BOLD loop across BOLD runs
        # ----------------------------------------------------------------------
        #
        echo ""
        echo " ==> Looping through requested BOLDS: ${BOLDS}"
        echo ""
        for BOLD in ${BOLDS}; do
            # -- Check if BOLD FC requested
            if [[ ! -z ${BOLDfc} ]]; then
                echo " --- Working on BOLD FC QC scene..."; echo ""
                # Inputs
                Modality="BOLD"
                if [[ ${BOLDfc} == "pscalar" ]]; then
                    TemplateSceneFile="TEMPLATE.PSCALAR.${Modality}.QC.wb.scene"
                fi
                if [[ ${BOLDfc} == "pconn" ]]; then
                    TemplateSceneFile="TEMPLATE.PCONN.${Modality}.QC.wb.scene"
                fi
                scenetemplatefolder="${TOOLS}/${QuNexREPO}/library/data/scenes/qc"
                WorkingSceneFile="${CASE}.${BOLDfc}.${Modality}.${BOLD}.QC.wb.scene"
                # -- Rsync over template files for a given BOLD
                Com1="rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/"
                Com2="cp ${OutPath}/${TemplateSceneFile} ${OutPath}/${WorkingSceneFile} &> /dev/null"
                ComQueue="$Com1; $Com2"
                echo " --- Copied ${scenetemplatefolder}/${TemplateSceneFile} over to ${OutPath}"
                runscene_BOLDfc
                # -- Clean up prior conflicting scripts, generate script and set permissions
                rm -f ${RunQCLogFolder}/${CASE}_ComQUEUE_${BOLDfc}_${Modality}_${BOLD}_${TimeStamp}.sh &> /dev/null
                echo "$ComRunBoldQUEUE" >> ${RunQCLogFolder}/${CASE}_ComQUEUE_${BOLDfc}_${Modality}_${BOLD}_${TimeStamp}.sh
                chmod 770 ${RunQCLogFolder}/${CASE}_ComQUEUE_${BOLDfc}_${Modality}_${BOLD}_${TimeStamp}.sh
                # -- Run script
                ${RunQCLogFolder}/${CASE}_ComQUEUE_${BOLDfc}_${Modality}_${BOLD}_${TimeStamp}.sh |& tee -a ${RunQCLogFolder}/QC_${CASE}_ComQUEUE_${BOLDfc}_${Modality}_${TimeStamp}.log
                FinalLog="${RunQCLogFolder}/QC_${CASE}_ComQUEUE_${BOLDfc}_${Modality}_${TimeStamp}.log"
                rm ${OutPath}/${TemplateSceneFile} &> /dev/null
                completionCheck
            else
            # -- Work on raw BOLD QC + TSNR
                # -- Check if prefix is specified
                if [[ ! -z "$BOLDPrefix" ]]; then
                    echo ""
                    echo ""
                    geho "  ==> Working on BOLD number: ${BOLD}"
                    echo ""
                    if [[ `echo ${BOLDPrefix} | grep '_'` ]]; then BOLD="${BOLDPrefix}${BOLD}"; else BOLD="${BOLDPrefix}_${BOLD}"; fi
                    geho "  --- BOLD Prefix specified. Appending to BOLD number: ${BOLD}"
                    echo ""
                else
                    # -- Check if BOLD folder with the given number contains additional prefix info and return an exit code if yes
                    echo ""
                    NoBOLDDirPreffix=`ls -d ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/*${BOLD}`
                    NoBOLDPreffix=`ls -d ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/*${BOLD} | sed 's:/*$::' | sed 's:.*/::'`
                    if [[ ! -z ${NoBOLDDirPreffix} ]]; then
                        echo " --- Note: A directory with the BOLD number is found but containing a prefix, yet no prefix was specified: "
                        echo "           --> ${NoBOLDDirPreffix}"
                        echo ""
                        echo " --- Setting BOLD prefix to: ${NoBOLDPreffix}"
                        echo ""
                        echo " --- If this is not correct please re-run with correct --boldprefix flag to ensure correct BOLDs are specified."
                        echo ""
                        BOLD=${NoBOLDPreffix}
                    fi
                fi
                # -- Check if BOLD exists and skip if not it does not
                if [[ ! -f ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}.dtseries.nii ]]; then
                    echo ""
                    reho "--- ERROR: BOLD data specified for BOLD ${BOLD} not found: "
                    reho "          --> ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/Results/${BOLD}/${BOLD}${BOLDSuffix}.dtseries.nii "
                    echo ""
                    reho "--- Check presence of your inputs for ${CASE} and BOLD ${BOLD} and re-run! Proceeding to next BOLD run."
                    echo ""
                    CompletionCheck="fail"
                else
                    # -- Generate QC statistics for a given BOLD
                    geho "--- Specified BOLD data found. Generating QC statistics commands for BOLD ${BOLD} on ${CASE}..."
                    echo ""
                    # Check if SNR only requested
                    if [ "$SNROnly" == "yes" ]; then 
                            runsnr_BOLD
                    else
                       # -- Check if running defaults w/o UserSceneFile
                       if [ -z "$UserSceneFile" ] && [ "$OmitDefaults" == 'no' ] && [ "$RunQCCustom" != "yes" ]; then
                           # Inputs
                           Modality="BOLD"
                           TemplateSceneFile="TEMPLATE.${Modality}.QC.wb.scene"
                           scenetemplatefolder="${TOOLS}/${QuNexREPO}/library/data/scenes/qc"
                           WorkingSceneFile="${CASE}.${Modality}.${BOLD}.QC.wb.scene"
                           # -- Rsync over template files for a given BOLD
                           runsnr_BOLD
                           Com1="rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/"
                           Com2="cp ${OutPath}/${TemplateSceneFile} ${OutPath}/${WorkingSceneFile} &> /dev/null "
                           Com3="sed -i -e 's|DUMMYXAXISMAX|$xmax|g' ${OutPath}/${WorkingSceneFile}"
                           Com4="sed -i -e 's|DUMMYYAXISMAX|$ymax|g' ${OutPath}/${WorkingSceneFile}"
                           Com5="sed -i -e 's|DUMMYYAXISMIN|$ymin|g' ${OutPath}/${WorkingSceneFile}"
                           ComQueue="$Com1; $Com2; $Com3; $Com4; $Com5"
                           runscene_BOLD
                           # -- Clean up prior conflicting scripts, generate script and set permissions
                           rm -f ${RunQCLogFolder}/${CASE}_ComQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh &> /dev/null
                           echo "$ComRunBoldQUEUE" >> ${RunQCLogFolder}/${CASE}_ComQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh
                           chmod 770 ${RunQCLogFolder}/${CASE}_ComQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh
                           # -- Run script
                           ${RunQCLogFolder}/${CASE}_ComQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh |& tee -a ${RunQCLogFolder}/QC_${CASE}_ComQUEUE_${Modality}_${TimeStamp}.log
                           rm ${OutPath}/${TemplateSceneFile} &> /dev/null
                           FinalLog="${RunQCLogFolder}/QC_${CASE}_ComQUEUE_${Modality}_${TimeStamp}.log"
                           completionCheck
                       fi
                    fi
                    # -- Check if custom QC was specified
                    if [ "$RunQCCustom" == "yes" ]; then
                        runsnr_BOLD
                        for TemplateSceneFile in ${CustomTemplateSceneFiles}; do
                            WorkingSceneFile="${CASE}.${Modality}.${BOLD}.${TemplateSceneFile}"
                            DummyVariable_Check
                            # -- Rsync over template files for a given BOLD
                            Com1="rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/"
                            Com2="cp ${OutPath}/${TemplateSceneFile} ${OutPath}/${WorkingSceneFile} &> /dev/null "
                            ComQueue="$Com1; $Com2"
                            runscene_BOLD
                            CustomRunQUEUE=${ComRunBoldQUEUE}
                            # -- Clean up prior conflicting scripts, generate script and set permissions
                            rm -f ${RunQCLogFolder}/${CASE}_CustomRunQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh &> /dev/null
                            echo "$CustomRunQUEUE" >> ${RunQCLogFolder}/${CASE}_CustomRunQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh
                            chmod 770 ${RunQCLogFolder}/${CASE}_CustomRunQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh
                            # -- Run script
                            ${RunQCLogFolder}/${CASE}_CustomRunQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh |& tee -a ${RunQCLogFolder}/QC_${CASE}_CustomRunQUEUE_${Modality}_${TimeStamp}.log
                            FinalLog="${RunQCLogFolder}/QC_${CASE}_CustomRunQUEUE_${Modality}_${TimeStamp}.log"
                        done
                        completionCheck
                    fi
                    # # -- Check if user specific scene path was provided
                    # if [ ! -z "$UserSceneFile" ]; then
                    #     WorkingSceneFile="${CASE}.${Modality}.${BOLD}.${UserSceneFile}"
                    #     Com1="rsync -aWH ${scenetemplatefolder}/* ${OutPath}/ &> /dev/null"
                    #     Com2="cp ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/${WorkingSceneFile}"
                    #     ComQueue="$Com1; $Com2"
                    #     DummyVariable_Check
                    #     runscene_BOLD
                    #     UserRunQUEUE=${ComRunBoldQUEUE}
                    #     # -- Clean up prior conflicting scripts, generate script and set permissions
                    #     rm -f "$RunQCLogFolder"/${CASE}_UserRunQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh &> /dev/null
                    #     echo "$UserRunQUEUE" >> "$RunQCLogFolder"/${CASE}_UserRunQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh
                    #     chmod 770 "$RunQCLogFolder"/${CASE}_UserRunQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh
                    #     # -- Run script
                    #     "$RunQCLogFolder"/${CASE}_UserRunQUEUE_${Modality}_${BOLD}_${TimeStamp}.sh |& tee -a "$RunQCLogFolder"/QC_"$CASE"_UserRunQUEUE_"$Modality"_"$TimeStamp".log
                    # completionCheck
                    # fi
                fi
            fi
        done
        #
        # End of Code block to run BOLD loop across BOLD runs 
        # ----------------------------------------------------------------------
    fi
    
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # =-=-=-=-=-=- End of BOLD QC Section =-=-=-=-=
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # =-=-= remaining modalities (i.e. T1w, T2w, Myelin or DWI) =-=
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    
    if [ "$Modality" != "BOLD" ]; then
    
    # -- Check if running defaults w/o UserSceneFile
    if [ -z "$UserSceneFile" ] && [ "$OmitDefaults" == 'no' ]; then
        # -- Setup naming conventions before generating scene
        Com1="rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/ &> /dev/null"
        Com2="cp ${OutPath}/${TemplateSceneFile} ${OutPath}/${WorkingSceneFile}"
        Com3="sed -i -e 's|DUMMYPATH|$SubjectsFolder|g' ${OutPath}/${WorkingSceneFile}" 
        Com4="sed -i -e 's|DUMMYCASE|$CASE|g' ${OutPath}/${WorkingSceneFile}"

        # -------------------------------------------
        # -- General QC
        # -------------------------------------------
        
        # -- Perform checks if modality is general
        if [ "$Modality" == "general" ]; then
            GeneralPathCheck="${SubjectsFolder}/${CASE}/${GeneralSceneDataPath}/${GeneralSceneDataFile}"
            # -- Check if Preprocessed T1w files are present
            if [ ! -f ${GeneralPathCheck} ]; then
                echo ""
                reho "--- ERROR: Data requested not found: "
                reho "           --> ${GeneralPathCheck} "
                echo ""
                reho "Check presence of your inputs and re-run!"
                CompletionCheck="fail"
                echo ""
                return 1
            else
                echo ""
                geho "--- Data inputs found: ${GeneralPathCheck}"
                echo ""
                # -- Setup naming conventions for general inputs before generating scene
                Com4a="sed -i -e 's|DUMMYIMAGEPATH|$GeneralSceneDataPath|g' ${OutPath}/${WorkingSceneFile}"
                Com4b="sed -i -e 's|DUMMYIMAGEFILE|$GeneralSceneDataFile|g' ${OutPath}/${WorkingSceneFile}"
                Com4="$Com4; $Com4a; $Com4b"
            fi
        fi
        
        # -------------------------------------------
        # -- T1w QC
        # -------------------------------------------
        
        # -- Perform checks if modality is T1w
        if [ "$Modality" == "T1w" ]; then
            # -- Check if Preprocessed T1w files are present
            if [ -z ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/T1w_restore.nii.gz ]; then
                echo ""
                reho "--- ERROR: Preprocessed T1w data not found: "
                reho "           --> ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/${DWIName}.nii.gz "
                echo ""
                reho "Check presence of your T1w inputs and re-run!"
                CompletionCheck="fail"
                echo ""
                return 1
            else
                echo ""
                geho "--- T1w inputs found: ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/T1w_restore.nii.gz"
                echo ""
            fi
        fi
        
        # -------------------------------------------
        # -- T2w QC
        # -------------------------------------------
        
        # -- Perform checks if modality is T2w
        if [ "$Modality" == "T2w" ]; then
            # -- Check if T2w is found in the subject_hcp.txt mapping file
            T2wCheck=`cat ${SubjectsFolder}/${CASE}/subject_hcp.txt | grep "T2w"`
            if [[ -z $T2wCheck ]]; then
                echo ""
                reho "--- ERROR: T2w QC requested but T2w mapping in ${SubjectsFolder}/${CASE}/subject_hcp.txt not detected. Check your data and re-run if needed."
                CompletionCheck="fail"
                echo ""
                return 1
            else
                echo ""
                geho "--- T2w mapping found: ${SubjectsFolder}/${CASE}/subject_hcp.txt. Checking for T2w data next..."
                echo ""
                # -- If subject_hcp.txt mapping file present check if Preprocessed T2w files are present
                if [ -z ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/T2w_restore.nii.gz ]; then
                    echo ""
                    reho "--- ERROR: Preprocessed T2w data not found: "
                    reho "           --> ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/T2w_restore.nii.gz "
                    echo ""
                    reho "Check presence of your T2w inputs and re-run!"
                    CompletionCheck="fail"
                    echo ""
                    return 1
                else
                    echo ""
                    geho "--- T2w inputs found: ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/T2w_restore.nii.gz"
                    echo ""
                fi
            fi
        fi
        
        # -------------------------------------------
        # -- Myelin QC
        # -------------------------------------------
        
        # -- Perform checks if modality is Myelin
        if [ "$Modality" == "Myelin" ]; then
            # -- Check if Preprocessed Myelin files are present
            if [ -z ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/${CASE}.L.SmoothedMyelinMap.164k_fs_LR.func.gii ] || [ -z ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/${CASE}.R.SmoothedMyelinMap.164k_fs_LR.func.gii ]; then
                echo ""
                reho "--- ERROR: Preprocessed Smoothed Myelin data not found: "
                reho "           --> ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/${CASE}.*.SmoothedMyelinMap.164k_fs_LR.func.gii  "
                echo ""
                reho "---- Check presence of your Myelin inputs and re-run!"
                CompletionCheck="fail"
                echo ""
                return 1
            else
                echo ""
                geho "--- Myelin L hemisphere input found: ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/${CASE}.L.SmoothedMyelinMap.164k_fs_LR.func.gii "
                geho "--- Myelin R hemisphere input found: ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/MNINonLinear/${CASE}.R.SmoothedMyelinMap.164k_fs_LR.func.gii "
                echo ""
            fi
        fi
        
        # -------------------------------------------
        # -- DWI QC
        # -------------------------------------------
        
        # -- Perform checks if modality is DWI
        if [ "$Modality" == "DWI" ]; then
            unset "$DWIName" >/dev/null 2>&1
            # -- Check if legacy setting is YES
            if [ "$DWILegacy" == "yes" ]; then
                DWIName="${CASE}_${DWIData}"
                NoDiffBrainMask=`ls ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/*T1w_brain_mask_downsampled2diff*` &> /dev/null
            else
                DWIName="${DWIData}"
                NoDiffBrainMask="${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/nodif_brain_mask.nii.gz"
            fi
            # -- Check if Preprocessed DWI files are present
            if [ -z ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/${DWIName}.nii.gz ]; then
                echo ""
                reho "--- ERROR: Preprocessed DWI data not found: "
                reho "           --> ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/${DWIName}.nii.gz "
                echo ""
                reho "--- Check presence of your DWI inputs and re-run!"
                echo ""
                exit 1
            else
                echo ""
                geho "--- DWI inputs found: ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/${DWIName}.nii.gz "
                echo ""
                # -- Split the data and setup 1st and 2nd volumes for visualization
                Com4a="fslsplit ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/${DWIName}.nii.gz ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/${DWIName}_split -t"
                Com4b="fslmaths ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/${DWIName}_split0000.nii.gz -mul ${NoDiffBrainMask} ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/data_frame1_brain"
                Com4c="fslmaths ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/${DWIName}_split0010.nii.gz -mul ${NoDiffBrainMask} ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/data_frame10_brain"
                # -- Clean split volumes
                Com4d="rm -f ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/${DWIName}_split* &> /dev/null"
                # -- Setup naming conventions for DWI before generating scene
                Com4e="sed -i -e 's|DUMMYDWIPATH|$DWIPath|g' ${OutPath}/${WorkingSceneFile}"
                Com4="$Com4; $Com4a; $Com4b; $Com4c; $Com4d; $Com4e"
                # --------------------------------------------------
                # -- Check if DTIFIT and BEDPOSTX flags are set
                # --------------------------------------------------
                # -- If dtifit qc is selected then generate dtifit scene
                if [ "$DtiFitQC" == "yes" ]; then
                    if [ ! -z "$UserSceneFile" ]; then
                        WorkingDTISceneFile="${CASE}.${Modality}.dtifit.${UserSceneFile}"
                    else
                        WorkingDTISceneFile="${CASE}.${Modality}.dtifit.QC.wb.scene"
                    fi
                    echo ""
                    geho "--- QC for FSL dtifit requested. Checking if dtifit was completed..."
                    echo ""
                    # -- Check if dtifit is done
                    minimumfilesize=100000
                    if [ -a ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/dti_FA.nii.gz ]; then 
                        actualfilesize=$(wc -c <${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/dti_FA.nii.gz)
                    else
                        actualfilesize="0"
                    fi
                    if [ $(echo "$actualfilesize" | bc) -gt $(echo "$minimumfilesize" | bc) ]; then
                        echo ""
                        geho "    --> FSL dtifit results found here: ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/"
                        echo ""
                        # -- Replace DWI scene specifications with the dtifit results
                        Com4g1="cp ${OutPath}/${WorkingSceneFile} ${OutPath}/${WorkingDTISceneFile}"
                        Com4g2="sed -i -e 's|1st frame|dti FA|g' ${OutPath}/${WorkingDTISceneFile}"
                        Com4g3="sed -i -e 's|10th frame|dti L3|g' ${OutPath}/${WorkingDTISceneFile}"
                        Com4g4="sed -i -e 's|data_frame1_brain.nii.gz|dti_FA.nii.gz|g' ${OutPath}/${WorkingDTISceneFile}"
                        Com4g5="sed -i -e 's|data_frame10_brain.nii.gz|dti_L3.nii.gz|g' ${OutPath}/${WorkingDTISceneFile}"
                        # -- Combine dtifit commands
                        Com4g="$Com4g1; $Com4g2; $Com4g3; $Com4g4; $Com4g5"
                        # -- Combine DWI commands
                        Com4="$Com4; $Com4g"
                    else
                        reho "--- ERROR: FSL dtifit not found for $CASE. Skipping dtifit QC request for upcoming QC calls. Check dtifit results: "
                        reho "           --> ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/${DWIPath}/ "
                    fi
                fi
                # -- If bedpostx qc is selected then generate bedpostx scene
                if [ "$BedpostXQC" == "yes" ]; then
                    if [ ! -z "$UserSceneFile" ]; then
                        WorkingBedpostXSceneFile="${CASE}.${Modality}.bedpostx.${UserSceneFile}"
                    else
                        WorkingBedpostXSceneFile="${CASE}.${Modality}.bedpostx.QC.wb.scene"
                    fi
                    echo ""
                    geho "--- QC for FSL BedpostX requested. Checking if BedpostX was completed..."
                    echo ""
                    # -- Check if the file even exists
                    if [ -f ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/Diffusion.bedpostX/merged_f1samples.nii.gz ]; then
                        # -- Set file sizes to check for completion
                        minimumfilesize=20000000
                        actualfilesize=`wc -c < ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/Diffusion.bedpostX/merged_f1samples.nii.gz` > /dev/null 2>&1          
                        filecount=`ls ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/Diffusion.bedpostX/merged_*nii.gz | wc | awk {'print $1'}`
                        # -- Then check if run is complete based on file count
                        if [ "$filecount" == 9 ]; then
                            # -- Then check if run is complete based on file size
                            if [ $(echo "$actualfilesize" | bc) -ge $(echo "$minimumfilesize" | bc) ]; then > /dev/null 2>&1
                                echo ""
                                geho "    --> BedpostX outputs found and completed here: ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/Diffusion.bedpostX/"
                                echo ""
                                # -- Replace DWI scene specifications with the dtifit results
                                Com4h1="cp ${OutPath}/${WorkingSceneFile} ${OutPath}/${WorkingBedpostXSceneFile}"
                                Com4h2="sed -i -e 's|1st frame|mean d diffusivity|g' ${OutPath}/${WorkingBedpostXSceneFile}"
                                Com4h3="sed -i -e 's|10th frame|mean f anisotropy|g' ${OutPath}/${WorkingBedpostXSceneFile}"
                                Com4h4="sed -i -e 's|$DWIPath/data_frame1_brain.nii.gz|Diffusion.bedpostX/mean_dsamples.nii.gz|g' ${OutPath}/${WorkingBedpostXSceneFile}"
                                Com4h5="sed -i -e 's|$DWIPath/data_frame10_brain.nii.gz|Diffusion.bedpostX/mean_fsumsamples.nii.gz|g' ${OutPath}/${WorkingBedpostXSceneFile}"
                                # -- combine BedpostX commands
                                Com4h="$Com4h1; $Com4h2; $Com4h3; $Com4h4; $Com4h5"
                                # -- Combine BedpostX commands
                                Com4="$Com4; $Com4h"
                            fi
                        fi
                    else 
                        echo ""
                        reho "--- ERROR: FSLBedpostX outputs missing or incomplete for $CASE. Skipping BedpostX QC request for upcoming QC calls. Check BedpostX results: "
                        reho "           --> ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/T1w/Diffusion.bedpostX/ "
                        echo ""
                        BedpostXQC="no"
                    fi
                fi
                # -- If eddy qc is selected then create hard link to eddy qc pdf and print the qc_mot_abs for each subjec to a report
                if [ "$EddyQCStats" == "yes" ]; then
                    echo ""
                    geho "--- QC Stats for FSL EDDY requested. Checking if EDDY QC was completed..."
                    echo ""
                    # -- Then check if eddy qc is completed
                    if [ -f ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/Diffusion/eddy/eddy_unwarped_images.qc/qc.pdf ]; then
                        geho "    --> EDDY QC outputs found and completed here: "; echo ""
                            # -- Regenerate the qc_mot_abs if missing
                            if [ -f ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/Diffusion/eddy/eddy_unwarped_images.qc/${CASE}_qc_mot_abs.txt ]; then
                                echo "        ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/Diffusion/eddy/eddy_unwarped_images.qc/${CASE}_qc_mot_abs.txt"
                            else
                                echo "        ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/Diffusion/eddy/eddy_unwarped_images.qc/${CASE}_qc_mot_abs.txt not found. Regenerating... "
                                more ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/Diffusion/eddy/eddy_unwarped_images.qc/qc.json | grep "qc_mot_abs" | sed -n -e 's/^.*: //p' | tr -d ',' >> ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/Diffusion/eddy/eddy_unwarped_images.qc/${CASE}_qc_mot_abs.txt
                            fi
                        echo ""
                        echo "        ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/Diffusion/eddy/eddy_unwarped_images.qc/qc.pdf"
                        echo ""
                        # -- Run links and printing to reports
                        ln ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/Diffusion/eddy/eddy_unwarped_images.qc/qc.pdf ${OutPath}/${CASE}.${Modality}.eddy.QC.pdf
                        printf "${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/Diffusion/eddy/eddy_unwarped_images.qc/${CASE}_qc_mot_abs.txt\n" >> ${OutPath}/EddyQCReport_qc_mot_abs_${TimeStampRunQC}.txt
                        
                        geho "--- Completed EDDY QC stats for ${CASE}"
                        geho "    Final report can be found here: ${OutPath}/EddyQCReport_qc_mot_abs_${TimeStampRunQC}.txt"; echo ""
                    else
                        echo ""
                        reho "--- ERROR: EDDY QC outputs missing or incomplete for $CASE. Skipping EDDY QC request. Check EDDY results."
                        echo ""
                    fi
                fi
            fi
        fi
    
        # -------------------------------------------
        # -- Additional steps
        # -------------------------------------------
        
        # -- Add timestamp to the scene
        Com5="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingSceneFile}"
        PNGName="${WorkingSceneFile}.png"
        ComRunPngName="sed -i -e 's|DUMMYPNGNAME|$PNGName|g' ${OutPath}/${WorkingSceneFile}"
        Com5="$Com5; $ComRunPngName"
        # -- Output image of the scene
        Com6="wb_command -show-scene ${OutPath}/${WorkingSceneFile} 1 ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png 1194 539"
        echo ""
        echo "$Com6"
        echo ""
        
        # -- Check if dtifit is requested
        if [ "$DtiFitQC" == "yes" ]; then
            Com5a="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingDTISceneFile}"
            PNGNameDtiFit="${WorkingDTISceneFile}.png"
            ComRunPngNameDtiFit="sed -i -e 's|DUMMYPNGNAME|$PNGName|g' ${OutPath}/${WorkingDTISceneFile}"
            Com5b="wb_command -show-scene ${OutPath}/${CASE}.${Modality}.dtifit.QC.wb.scene 1 ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.png 1194 539"
            Com5="$Com5; $ComRunPngNameDtiFit; $Com5a; $Com5b"
        fi
        # -- Check of bedpostx QC is requested
        if [ "$BedpostXQC" == "yes" ]; then
            Com5c="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingBedpostXSceneFile}"
            PNGNameBedpostX="${WorkingDTISceneFile}.png"
            ComRunPngNameBedpostX="sed -i -e 's|DUMMYPNGNAME|$PNGName|g' ${OutPath}/${WorkingDTISceneFile}"
            Com5d="wb_command -show-scene ${OutPath}/${CASE}.${Modality}.bedpostx.QC.wb.scene 1 ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.png 1194 539"
            Com5="$Com5; $ComRunPngNameBedpostX; $Com5c; $Com5d"
        fi
        
        # -- Clean templates and files for next subject
        Com7="rm ${OutPath}/${WorkingSceneFile}-e &> /dev/null"
        Com8="rm ${OutPath}/${TemplateSceneFile} &> /dev/null"
        Com9="rm -f ${OutPath}/data_split*"
        
        # -------------------------------------------
        # -- Zip QC Scenes
        # -------------------------------------------
        
        # -- Generate Scene Zip File if set to YES
        if [ "$SceneZip" == "yes" ]; then
            echo ""
            geho "--- Scene zip set to: $SceneZip. Relevant scene files will be zipped using the following base folder:" 
            geho "    ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
            echo ""
            geho "--- The zip file will be saved to: "
            geho "    ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip "
            echo ""
            if [[ ${Modality} == "general" ]]; then
                 geho "--- ${Modality} scene type requested. Outputs will be set relative to: "
                 geho "    ${SubjectsFolder}/${CASE}"
                 echo ""
                 RemoveScenePath="${SubjectsFolder}/${CASE}"
                 Com10a="cp ${OutPath}/${WorkingSceneFile} ${SubjectsFolder}/${CASE}/"
                 Com10b="rm ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip  &> /dev/null"
                 Com10c="sed -i -e 's|$RemoveScenePath|.|g' ${SubjectsFolder}/${CASE}/${WorkingSceneFile}" 
                 Com10d="cd ${OutPath}; wb_command -zip-scene-file ${SubjectsFolder}/${CASE}/${WorkingSceneFile} ${WorkingSceneFile}.${TimeStamp} ${WorkingSceneFile}.${TimeStamp}.zip"
                 echo ""
                 echo "$Com10d"
                 echo ""
                 Com10e="echo ${SubjectsFolder}/${CASE}/${WorkingSceneFile}"
                 Com10f="mkdir -p ${SubjectsFolder}/${CASE}/qc &> /dev/null"
                 Com10g="cp ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ${SubjectsFolder}/${CASE}/qc/"
                 Com10="$Com10a; $Com10b; $Com10c; $Com10d; $Com10e; $Com10f; $Com10g"

            else
                 geho "--- ${Modality} scene type requested. Outputs will be set relative to: "
                 geho "    ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
                 echo ""
                 RemoveScenePath="${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
                 Com10a="cp ${OutPath}/${WorkingSceneFile} ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/"
                 Com10b="rm ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip  &> /dev/null"
                 Com10c="sed -i -e 's|$RemoveScenePath|.|g' ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile}" 
                 Com10d="cd ${OutPath}; wb_command -zip-scene-file ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile} ${WorkingSceneFile}.${TimeStamp} ${WorkingSceneFile}.${TimeStamp}.zip -base-dir ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
                 Com10e="echo ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile}"
                 Com10f="mkdir -p ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc &> /dev/null"
                 Com10g="cp ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc/"
                 Com10="$Com10a; $Com10b; $Com10c; $Com10d; $Com10e; $Com10f; $Com10g"
            fi
        fi
        # -- Generate Zip files for dtifit scenes if requested
        if [ "$DtiFitQC" == "yes" ] && [ "$SceneZip" == "yes" ]; then
            echo ""
            geho "--- Scene zip set to: $SceneZip. DtiFitQC set to: $DtiFitQC. Relevant scene files will be zipped using the following base folder:" 
            geho "    ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
            echo ""
            geho "--- The zip file will be saved to: "
            geho "    ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.zip"
            echo ""
            RemoveScenePath="${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
            Com11a="cp ${OutPath}/${WorkingDTISceneFile} ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/"
            Com11b="rm ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.zip &> /dev/null"
            Com11c="sed -i -e 's|$RemoveScenePath|.|g' ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingDTISceneFile}" 
            Com11d="cd ${OutPath}; wb_command -zip-scene-file ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingDTISceneFile} ${WorkingDTISceneFile}.${TimeStamp} ${WorkingDTISceneFile}.${TimeStamp}.zip -base-dir ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
            Com11e="rm ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingDTISceneFile}"
            Com11f="mkdir -p ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc &> /dev/null"
            Com11g="cp ${OutPath}/${WorkingDTISceneFile}.${TimeStamp}.zip ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc/"
            Com11="$Com11a; $Com11b; $Com11c; $Com11d; $Com11e; $Com11f; $Com11g"
        fi
        # -- Generate Zip files for bedpostx scenes if requested
        if [ "$BedpostXQC" == "yes" ] && [ "$SceneZip" == "yes" ]; then
            echo ""
            geho "--- Scene zip set to: $SceneZip. BedpostXQC set to: $BedpostXQC. Relevant scene files will be zipped using the following base folder:" 
            geho "    ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
            echo ""
            geho "--- The zip file will be saved to: "
            geho "    ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.zip"
            echo ""
            RemoveScenePath="${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
            Com12a="cp ${OutPath}/${WorkingBedpostXSceneFile} ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/"
            Com12b="rm ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.zip &> /dev/null"
            Com12c="sed -i -e 's|$RemoveScenePath|.|g' ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingBedpostXSceneFile}" 
            Com12d="cd ${OutPath}; wb_command -zip-scene-file ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingBedpostXSceneFile} ${WorkingBedpostXSceneFile}.${TimeStamp} ${WorkingBedpostXSceneFile}.${TimeStamp}.zip -base-dir ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
            Com12e="rm ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingBedpostXSceneFile}"
            Com12f="mkdir -p ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc &> /dev/null"
            Com12g="cp ${OutPath}/${WorkingBedpostXSceneFile}.${TimeStamp}.zip ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc/"
            Com12="$Com12a; $Com12b; $Com12c; $Com12d; $Com12e; $Com12f; $Com12g"
        fi
        # -- Combine all the calls into a single command based on various specifications
        if [ "$SceneZip" == "yes" ]; then
             if [ "$DtiFitQC" == "no" ]; then
                 if [ "$BedpostXQC" == "no" ]; then
                    ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com8; $Com9; $Com10"
                else
                    ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com8; $Com9; $Com10; $Com12"
                fi
            else
                 if [ "$BedpostXQC" == "yes" ]; then
                    ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com8; $Com9; $Com10; $Com11; $Com12"
                else
                    ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $Com6; $Com7; $Com8; $Com9; $Com10; $Com11"
                fi
            fi
        else
            ComQUEUE="$Com1; $Com2; $Com3; $Com4; $Com5; $ComRunBoldPngNameGSMap; $Com6; $Com7; $Com8; $Com9"
        fi
        # -- Clean up prior conflicting scripts, generate script and set permissions
        rm -f "$RunQCLogFolder"/${CASE}_ComQUEUE_${Modality}_${TimeStamp}.sh &> /dev/null
        echo "$ComQUEUE" >> "$RunQCLogFolder"/${CASE}_ComQUEUE_${Modality}_${TimeStamp}.sh
        chmod 770 "$RunQCLogFolder"/${CASE}_ComQUEUE_${Modality}_${TimeStamp}.sh
        # -- Run Job
        "$RunQCLogFolder"/${CASE}_ComQUEUE_${Modality}_${TimeStamp}.sh |& tee -a ${RunQCLogFolder}/QC_${CASE}_ComQUEUE_${Modality}_${TimeStamp}.log
        echo ""
        FinalLog="${RunQCLogFolder}/QC_${CASE}_ComQUEUE_${Modality}_${TimeStamp}.log"
        completionCheck
    fi
    
    # -- Check if custom QC was specified
    if [ "$RunQCCustom" == "yes" ]; then
        echo ""
        reho "====================== Process custom scenes: $RunQCCustom ============================="
        echo ""
        Customscenetemplatefolder="${StudyFolder}/processing/scenes/QC/${Modality}"
        CustomTemplateSceneFiles=`ls ${StudyFolder}/processing/scenes/QC/${Modality}/*.scene | xargs -n 1 basename`
        geho "$CustomTemplateSceneFiles"
        scenetemplatefolder=${Customscenetemplatefolder}
        for TemplateSceneFile in ${CustomTemplateSceneFiles}; do
            DummyVariable_Check
            WorkingSceneFile="${CASE}.${Modality}.${TemplateSceneFile}"
            RunQCCustom1="rsync -aWH ${scenetemplatefolder}/${TemplateSceneFile} ${OutPath}/ &> /dev/null"
            RunQCCustom2="cp ${OutPath}/${TemplateSceneFile} ${OutPath}/${WorkingSceneFile}"
            RunQCCustom3="sed -i -e 's|DUMMYPATH|$SubjectsFolder|g' ${OutPath}/${WorkingSceneFile}" 
            RunQCCustom4="sed -i -e 's|DUMMYCASE|$CASE|g' ${OutPath}/${WorkingSceneFile}"
            # -- Add timestamp to the scene
            RunQCCustom5="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingSceneFile}"
            # -- Add scene name
            PNGName="${WorkingSceneFile}.pzwng"
            ComRunBoldPngNameGSMap="sed -i -e 's|DUMMYPNGNAME|$PNGName|g' ${OutPath}/${WorkingSceneFile}"
            # -- Output image of the scene
            RunQCCustom6="wb_command -show-scene ${OutPath}/${WorkingSceneFile} 1 ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png 1194 539"
            # -- Clean templates and files for next subject
            RunQCCustom7="rm ${OutPath}/${WorkingSceneFile}-e &> /dev/null"
            RunQCCustom8="rm ${OutPath}/${TemplateSceneFile} &> /dev/null"
            RunQCCustom9="rm -f ${OutPath}/data_split*"
            CustomRunQUEUE="$RunQCCustom1; $RunQCCustom2; $RunQCCustom3; $RunQCCustom4; $RunQCCustom5; $ComRunBoldPngNameGSMap; $RunQCCustom6; $RunQCCustom7; $RunQCCustom8; $RunQCCustom9"
            if [ "$SceneZip" == "yes" ]; then
                echo ""
                geho "--- Scene zip set to: $SceneZip. Relevant scene files will be zipped using the following base folder:" 
                geho "    ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
                echo ""
                geho "--- The zip file will be saved to: "
                geho "    ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip "
                echo ""
                RemoveScenePath="${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
                RunQCCustom10="cp ${OutPath}/${WorkingSceneFile} ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/"
                RunQCCustom11="rm ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip  &> /dev/null"
                RunQCCustom12="sed -i -e 's|$RemoveScenePath|.|g' ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile}" 
                RunQCCustom13="cd ${OutPath}; wb_command -zip-scene-file ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile} ${WorkingSceneFile}.${TimeStamp} ${WorkingSceneFile}.${TimeStamp}.zip -base-dir ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
                RunQCCustom14="rm ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile}"
                RunQCCustom15="mkdir -p ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc &> /dev/null"
                RunQCCustom16="cp ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc/"
                CustomRunQUEUE="$RunQCCustom1; $RunQCCustom2; $RunQCCustom3; $RunQCCustom4; $RunQCCustom5; $ComRunBoldPngNameGSMap; $RunQCCustom6; $RunQCCustom7; $RunQCCustom8; $RunQCCustom9; $RunQCCustom10; $RunQCCustom11; $RunQCCustom12; $RunQCCustom13; $RunQCCustom14; $RunQCCustom15; $RunQCCustom16"
            fi
            # -- Clean up prior conflicting scripts, generate script and set permissions
            rm -f "$RunQCLogFolder"/${CASE}_CustomRunQUEUE_${Modality}_${TimeStamp}.sh &> /dev/null
            echo "$CustomRunQUEUE" >> "$RunQCLogFolder"/${CASE}_CustomRunQUEUE_${Modality}_${TimeStamp}.sh
            chmod 770 "$RunQCLogFolder"/${CASE}_CustomRunQUEUE_${Modality}_${TimeStamp}.sh
            # -- Run Job
            "$RunQCLogFolder"/${CASE}_CustomRunQUEUE_${Modality}_${TimeStamp}.sh |& tee -a ${RunQCLogFolder}/QC_${CASE}_CustomRunQUEUE_${Modality}_${TimeStamp}.log
            FinalLog="${RunQCLogFolder}/QC_${CASE}_CustomRunQUEUE_${Modality}_${TimeStamp}.log"
            completionCheck
        done
    fi
    # -- Check if user specific scene path was provided
    if [ ! -z "$UserSceneFile" ]; then
        TemplateSceneFile"${UserSceneFile}"
        DummyVariable_Check
        WorkingSceneFile="${CASE}.${Modality}.${UserSceneFile}"
        RunQCUser1="rsync -aWH ${scenetemplatefolder}/* ${OutPath}/ &> /dev/null"
        RunQCUser2="cp ${OutPath}/${TemplateSceneFile} ${OutPath}/${WorkingSceneFile}"
        RunQCUser3="sed -i -e 's|DUMMYPATH|$SubjectsFolder|g' ${OutPath}/${WorkingSceneFile}" 
        RunQCUser4="sed -i -e 's|DUMMYCASE|$CASE|g' ${OutPath}/${WorkingSceneFile}"
        # -- Add timestamp to the scene
        RunQCUser5="sed -i -e 's|DUMMYTIMESTAMP|$TimeStamp|g' ${OutPath}/${WorkingSceneFile}"
        # -- Add scene name
        PNGName="${WorkingSceneFile}.png"
        ComRunBoldPngNameGSMap="sed -i -e 's|DUMMYPNGNAME|$PNGName|g' ${OutPath}/${WorkingSceneFile}"
        # -- Output image of the scene
        RunQCUser6="wb_command -show-scene ${OutPath}/${WorkingSceneFile} 1 ${OutPath}/${WorkingSceneFile}.${TimeStamp}.png 1194 539"
        # -- Clean templates and files for next subject
        RunQCUser7="rm ${OutPath}/${WorkingSceneFile}-e &> /dev/null"
        RunQCUser8="rm ${OutPath}/${TemplateSceneFile} &> /dev/null"
        RunQCUser9="rm -f ${OutPath}/data_split*"
        UserRunQUEUE="$RunQCUser1; $RunQCUser2; $RunQCUser3; $RunQCUser4; $RunQCUser5; $ComRunBoldPngNameGSMap; $RunQCUser6; $RunQCUser7; $RunQCUser8; $RunQCUser9"
        if [ "$SceneZip" == "yes" ]; then
            geho "--- Scene zip set to: $SceneZip. Relevant scene files will be zipped using the following base folder:" 
            geho "    ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
            echo ""
            geho "--- The zip file will be saved to: "
            geho "    ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip "
            echo ""
            RemoveScenePath="${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
            RunQCUser10="cp ${OutPath}/${WorkingSceneFile} ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/"
            RunQCUser11="rm ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip  &> /dev/null"
            RunQCUser12="sed -i -e 's|$RemoveScenePath|.|g' ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile}" 
            RunQCUser13="cd ${OutPath}; wb_command -zip-scene-file ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile} ${WorkingSceneFile}.${TimeStamp} ${WorkingSceneFile}.${TimeStamp}.zip -base-dir ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}"
            RunQCUser14="rm ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/${WorkingSceneFile}"
            RunQCUser15="mkdir -p ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc &> /dev/null"
            RunQCUser16="cp ${OutPath}/${WorkingSceneFile}.${TimeStamp}.zip ${SubjectsFolder}/${CASE}/hcp/${CASE}${SetHCPSuffix}/qc/"
            UserRunQUEUE="$RunQCCustom1; $RunQCCustom2; $RunQCCustom3; $RunQCCustom4; $RunQCCustom5; $ComRunBoldPngNameGSMap; $RunQCCustom6; $RunQCCustom7; $RunQCCustom8; $RunQCCustom9; $RunQCCustom10; $RunQCCustom11; $RunQCCustom12; $RunQCCustom13; $RunQCCustom14; $RunQCCustom15; $RunQCCustom16"
        fi
        # -- Clean up prior conflicting scripts, generate script and set permissions
        rm -f "$RunQCLogFolder"/${CASE}_UserRunQUEUE_${Modality}_${TimeStamp}.sh &> /dev/null
        echo "$UserRunQUEUE" >> "$RunQCLogFolder"/${CASE}_UserRunQUEUE_${Modality}_${TimeStamp}.sh
        chmod 770 "$RunQCLogFolder"/${CASE}_UserRunQUEUE_${Modality}_${TimeStamp}.sh
        # -- Run Job
        "$RunQCLogFolder"/${CASE}_UserRunQUEUE_${Modality}_${TimeStamp}.sh |& tee -a ${RunQCLogFolder}/QC_${CASE}_UserRunQUEUE_${Modality}_${TimeStamp}.log
        FinalLog="${RunQCLogFolder}/QC_${CASE}_UserRunQUEUE_${Modality}_${TimeStamp}.log"
        completionCheck
    fi
    fi
    
fi

done

finalReport

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@


