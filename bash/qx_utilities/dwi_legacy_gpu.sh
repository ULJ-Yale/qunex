#!/bin/bash

# Copyright (C)
# Copyright Notice
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Load Function Libraries
source ${HCPPIPEDIR}/global/scripts/log.shlib     # log_ functions
source ${HCPPIPEDIR}/global/scripts/version.shlib # version_ functions

usage() {
    cat << EOF
``dwi_legacy_gpu``

This function runs the DWI preprocessing using the FUGUE method for legacy data
that are not TOPUP compatible.

It explicitly assumes the the Human Connectome Project folder structure for
preprocessing.

DWI data needs to be in the following folder::

    <study_folder>/<session>/hcp/<session>/unprocessed/Diffusion

T1w data needs to be in the following folder::

    <study_folder>/<session>/hcp/<session>/T1w

Warning:
    - If PreFreeSurfer component of the HCP Pipelines was run the function will
      make use of the T1w data [Results will be better due to superior brain
      stripping].
    - If PreFreeSurfer component of the HCP Pipelines was NOT run the
      function will start from raw T1w data [Results may be less optimal]. -
      If you are this function interactively you need to be on a GPU-enabled
      node or send it to a GPU-enabled queue.

Parameters:
    --sessionsfolder (str, default '.'):
        Path to study data folder.
    --sessions (str):
        Comma separated list of sessions to run.
    --scanner (str):
        Name of scanner manufacturer ('siemens' or 'ge' supported).
    --echospacing (str):
        EPI Echo Spacing for data [in msec]; e.g. 0.69
    --pedir (int):
        Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior.
    --unwarpdir (str):
        Direction for EPI image unwarping; e.g. 'x' or 'x-' for LR/RL, 'y' or
        'y-' for AP/PA; may been to try out both -/+ combinations.
    --usefieldmap (str):
        Whether to use the standard field map ('yes' | 'no'). If set to <yes>
        then the parameter --te becomes mandatory.
    --diffdatasuffix (str):
        Name of the DWI image; e.g. if the data is called
        <session>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR.
    --overwrite (str):
        Delete prior run for a given session ('yes' | 'no').

Specific parameters:
    --te (float):
        This is the echo time difference of the fieldmap sequence - find this
        out form the operator - defaults are *usually* 2.46ms on SIEMENS.

Output files:
     - difffolder=${sessionsfolder}/${session}/Diffusion
     - t1wdifffolder=${sessionsfolder}/${session}/hcp/${session}/T1w/Diffusion_"$diffdatasuffix"

     ::

         $difffolder/$diffdatasuffix/rawdata
         $difffolder/$diffdatasuffix/eddy
         $difffolder/$diffdatasuffix/data
         $difffolder/$diffdatasuffix/reg
         $t1wdifffolder

Examples:
    Examples using Siemens FieldMap (needs GPU-enabled node).

    Run directly via::

        ${TOOLS}/${QUNEXREPO}/bash/qx_utilities/DWIPreprocPipelineLegacy.sh \\
            --<parameter1> \\
            --<parameter2> \\
            --<parameter3> ... \\
            --<parameterN>

    NOTE: --scheduler is not available via direct script call.

    Run via::

        qunex dwi_legacy_gpu \\
            --<parameter1> \\
            --<parameter2> ... \\
            --<parameterN>

    NOTE: scheduler is available via qunex call.

    --scheduler
        A string for the cluster scheduler (e.g. LSF, PBS or SLURM) followed by
        relevant options.

    For SLURM scheduler the string would look like this via the qunex call::

         --scheduler='SLURM,jobname=<name_of_job>,time=<job_duration>,ntasks=<number_of_tasks>,cpus-per-task=<cpu_number>,mem-per-cpu=<memory>,partition=<queue_to_send_job_to>'

    NOTE: CUDA libraries need to be loaded for this command to work, to do this
    you usually need to execute module load CUDA/9.1.85. When scheduling add the
    bash parameter to the command call, e.g.:

        --bash="module load CUDA/9.1.85"

    ::

        qunex dwi_legacy_gpu \\
            --sessionsfolder='<folder_with_sessions>' \\
            --sessions='<comma_separarated_list_of_cases>' \\
            --pedir='1' \\
            --echospacing='0.69' \\
            --te='2.46' \\
            --unwarpdir='x-' \\
            --diffdatasuffix='DWI_dir91_LR' \\
            --usefieldmap='yes' \\
            --scanner='siemens' \\
            --overwrite='yes'

    Example with flagged parameters for submission to the scheduler using
    Siemens FieldMap (needs GPU-enabled queue):

    ::

        qunex dwi_legacy_gpu \\
            --sessionsfolder='<folder_with_sessions>' \\
            --sessions='<comma_separarated_list_of_cases>' \\
            --pedir='1' \\
            --echospacing='0.69' \\
            --te='2.46' \\
            --unwarpdir='x-' \\
            --diffdatasuffix='DWI_dir91_LR' \\
            --usefieldmap='yes' \\
            --scanner='siemens' \\
            --overwrite='yes' \\
            --bash="module load CUDA/9.1.85" \\
            --scheduler='<name_of_scheduler_and_options>'

    Example with flagged parameters for submission to the scheduler using GE data
    without FieldMap (needs GPU-enabled queue):

    ::

        qunex dwi_legacy_gpu \\
            --sessionsfolder='<folder_with_sessions>' \\
            --sessions='<comma_separarated_list_of_cases>' \\
            --diffdatasuffix='DWI_dir91_LR' \\
            --scheduler='<name_of_scheduler_and_options>' \\
            --usefieldmap='no' \\
            --pedir='1' \\
            --echospacing='0.69' \\
            --unwarpdir='x-' \\
            --scanner='ge' \\
            --overwrite='yes'

EOF
exit 0
}

# ------------------------------------------------------------------------------
#  Setup color outputs
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

# -- Get the command line options for this script
get_options() {
    local script_name=$(basename ${0})
    local arguments=($@)
    
    # -- initialize global output variables
    unset sessionsfolder
    unset session
    unset pedir
    unset echospacing
    unset te
    unset unwarpdir
    unset diffdatasuffix
    unset overwrite
    unset scanner
    unset usefieldmap
    runcmd=""
    # -- parse arguments
    local index=0
    local numArgs=${#arguments[@]}
    local argument
    while [ ${index} -lt ${numArgs} ]; do
        argument=${arguments[index]}

        case ${argument} in
            --help)
                usage
                exit 1
                ;;
            --version)
                version_show $@
                exit 0
                ;;
            --sessionsfolder=*)
                sessionsfolder=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --session=*)
                session=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --pedir=*)
                pedir=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --echospacing=*)
                echospacing=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --te=*)
                te=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --unwarpdir=*)
                unwarpdir=${argument/*=/""}
                index=$(( index + 1 ))
                ;;  
            --diffdatasuffix=*)
                diffdatasuffix=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --overwrite=*)
                overwrite=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
             --scanner=*)
                scanner=${argument/*=/""}
                index=$(( index + 1 ))
                ;;    
            --usefieldmap=*)
                usefieldmap=${argument/*=/""}
                index=$(( index + 1 ))
                ;;        
            *)
                echo "ERROR: Unrecognized Option: ${argument}"
                exit 1
                ;;
        esac
    done
    # -- check required parameters
    if [ -z ${sessionsfolder} ]; then
        echo "ERROR: <study-path> not specified"
        exit 1
    fi
    if [ -z ${session} ]; then
        echo "ERROR: <session-id> not specified"
        exit 1
    fi
    if [ -z ${scanner} ]; then
        echo "Note: <scanner> specification not set"
        exit 1
    fi
    if [ -z ${pedir} ]; then
        echo "ERROR: <phase-encoding-dir> not specified"
        exit 1
    fi
    if [ -z ${echospacing} ]; then
        echo "ERROR: <echo-spacing> not specified"
        exit 1
    fi
    if [ -z ${unwarpdir} ]; then
        echo "ERROR: <unwarp-direction> not specified"
        exit 1
    fi
    if [ -z ${usefieldmap} ]; then
        echo "Note: <fieldmap> specification not set"
        exit 1
    fi    
    if [ ${usefieldmap} == "yes" ]; then
        if [ -z ${te} ]; then
            echo "ERROR: <te> not specified"
            exit 1
        fi
    fi
    if [ -z ${diffdatasuffix} ]; then
        echo "ERROR: <diffusion-data-suffix> not specified"
        exit 1
    fi
    # -- report options
    echo ""
    echo ""
    echo "-- ${script_name}: Specified Command-Line Options - Start --"
    echo "   Sessionsfolder: ${sessionsfolder}"
    echo "   Session: ${session}"
    echo "   Scanner: ${scanner}"
    if [ ${usefieldmap} == "yes" ]; then
        echo "   Using fieldmap: ${usefieldmap}"
        echo "   PEdir: ${pedir}"
        echo "   Echospacing: ${echospacing}"
        echo "   TE: ${te}"
        echo "   Unwarpdir: ${unwarpdir}"
    else
        echo "   Using fieldmap: ${usefieldmap}"
    fi
    echo "   Diffusion data sufix: ${diffdatasuffix}"
    echo "   Overwrite: ${overwrite}"
    echo "-- ${script_name}: Specified Command-Line Options - End --"
    echo ""
    geho "------------------------- Start of work --------------------------------"
    echo ""
}

######################################### DO WORK ##########################################

main() {
    # -- Get Command Line Options
    get_options $@

    ##############################
    # Setup folders and variables
    #############################

    # -- Parse all Parameters
    echospacing="$echospacing" #EPI Echo Spacing for data (in msec); e.g. 0.69
    pedir="$pedir" #Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior
    te="$te" #delta te in ms for field map or "NONE" if not used
    unwarpdir="$unwarpdir" # direction along which to unwarp
    diffdata="$session"_"$diffdatasuffix" # Diffusion data suffix name - e.g. if the data is called <sessionID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR
    dwelltime="$echospacing" #same variable as echospacing - if you have in-plane acceleration then this value needs to be divided by the GRAPPA or SENSE factor (miliseconds)
    dwelltimesec=`echo "scale=6; $dwelltime/1000" | bc` # set the dwell time to seconds

    # -- Establish global directory paths
    geho "--- Establishing paths for all input and output folders:"
    echo ""

    # -- Establish global directory paths
    t1wfolder="$sessionsfolder"/"$session"/hcp/"$session"/T1w
    difffolder="$sessionsfolder"/"$session"/hcp/"$session"/Diffusion
    t1wdifffolder="$sessionsfolder"/"$session"/hcp/"$session"/T1w/T1wDiffusion_"$diffdatasuffix"
    difffolderout="$sessionsfolder"/"$session"/hcp/"$session"/T1w/Diffusion_"$diffdatasuffix"

    echo "T1w folder:           $t1wfolder"
    echo "Diffusion folder:     $difffolder"
    echo "T1w diffusion folder: $t1wdifffolder"
    echo ""

    # -- Delete any existing output sub-directories        
    if [ "$overwrite" == "yes" ]; then
        reho "--- Deleting prior runs for $diffdata..."
        echo ""
        rm -rf "$difffolder"/"$diffdatasuffix"/rawdata/"$diffdata"* > /dev/null 2>&1
        rm -rf "$difffolder"/"$diffdatasuffix"/eddy/"$diffdata"* > /dev/null 2>&1
        rm -rf "$difffolder"/"$diffdatasuffix"/reg/"$diffdata"* > /dev/null 2>&1
        rm -rf "$difffolder"/"$diffdatasuffix"/fieldmap > /dev/null 2>&1
        rm -rf "$difffolder"/"$diffdatasuffix"/acqparams/"$diffdata" > /dev/null 2>&1
        rm -rf "$difffolderout"/"$diffdata"* > /dev/null 2>&1
        rm -rf "$t1wdifffolder"/*"$diffdatasuffix"* > /dev/null 2>&1
    fi

    # -- Make sure output directories exist
    mkdir -p "$t1wdifffolder" 2> /dev/null
    mkdir -p "$difffolderout" 2> /dev/null
    mkdir -p "$difffolder"/"$diffdatasuffix"/rawdata 2> /dev/null
    mkdir -p "$difffolder"/"$diffdatasuffix"/eddy 2> /dev/null
    mkdir -p "$difffolder"/"$diffdatasuffix"/reg 2> /dev/null
    mkdir -p "$difffolder"/"$diffdatasuffix"/fieldmap 2> /dev/null
    mkdir -p "$difffolder"/"$diffdatasuffix"/acqparams 2> /dev/null

    #########################################
    # STEP 0 - move the unprocessed data
    #########################################

    geho "--- Moving or copying unprocesed data into the Diffusion folder"
    echo ""
    unproc_file="${sessionsfolder}/${session}/hcp/${session}/unprocessed/Diffusion/${session}_${diffdatasuffix}"
    if [ -f "${unproc_file}.bval" ]; then
        echo "Moving ${unproc_file}.bval"
        mv "${unproc_file}.bval" "${difffolder}/"
    fi
    if [ -f "${unproc_file}.bvec" ]; then
        echo "Moving ${unproc_file}.bvec"
        mv "${unproc_file}.bvec" "${difffolder}/"
    fi
    if [ -f "${unproc_file}.nii.gz" ]; then
        echo "Moving ${unproc_file}.nii.gz"
        mv "${unproc_file}.nii.gz" "${difffolder}/"
    fi

    if [ ${usefieldmap} == "yes" ]; then
        unproc_fm="${sessionsfolder}/${session}/hcp/${session}/unprocessed/FieldMap1/${session}"
        if [ -f "${unproc_fm}_FieldMap_Magnitude.nii.gz" ]; then
            echo "Copying ${unproc_fm}_FieldMap_Magnitude.nii.gz"
            cp "${unproc_fm}_FieldMap_Magnitude.nii.gz" "${difffolder}/"
        fi
        if [ -f "${unproc_fm}_FieldMap_Phase.nii.gz" ]; then
            echo "Copying ${unproc_fm}_FieldMap_Phase.nii.gz"
            cp "${unproc_fm}_FieldMap_Phase.nii.gz" "${difffolder}/"
        fi
    fi

    #########################################
    # STEP 1 - setup acquisition parameters
    #########################################

    geho "--- Setting up acquisition parameters:"
    echo ""
    # -- Make session-specific and acquisition-specific parameter folder
    mkdir "$difffolder"/"$diffdatasuffix"/acqparams/"$diffdata" > /dev/null 2>&1

    # -- Create index file - parameter file for number of frames in the DWI image
    sesdimt=`fslval "$difffolder"/"$diffdata" dim4` #Number of datapoints per Pos series
    rm "$difffolder"/"$diffdatasuffix"/acqparams/"$diffdata"/index.txt > /dev/null 2>&1
    for (( j=0; j<${sesdimt}; j++ )); do echo "1" >> "$difffolder"/"$diffdatasuffix"/acqparams/"$diffdata"/index.txt; done

    # -- Create phase encoding and dwelltime parameter file
    rm "$difffolder"/"$diffdatasuffix"/acqparams/"$diffdata"/acqparams.txt > /dev/null 2>&1
    if [ "$pedir" == "1" ]; then
        voxel_number=`fslval "$difffolder"/"$diffdata" dim1`
        readout_time=`echo "scale=6; $dwelltimesec*($voxel_number-1)" | bc`
            echo "1 0 0 $readout_time" >> "$difffolder"/"$diffdatasuffix"/acqparams/"$diffdata"/acqparams.txt
    else
        voxel_number=`fslval "$difffolder"/"$diffdata" dim2`
        readout_time=`echo "scale=6; $dwelltimesec*($voxel_number-1)" | bc`
            echo "0 1 0 $readout_time" >> "$difffolder"/"$diffdatasuffix"/acqparams/"$diffdata"/acqparams.txt
    fi

    echo "Check acquisition parameter files:"
    echo ""
    echo "`ls $difffolder/$diffdatasuffix/acqparams/$diffdata/`"
    echo ""

    ############################################
    # STEP 2 - Prepare FieldMaps and T1w Images
    ############################################

    if [ ${usefieldmap} == "yes" ]; then
        geho "--- Preparing FieldMaps and T1w images..."
        echo ""
        geho "Running conservative BET on the FieldMap Magnitude image..."
        echo ""
        bet "$difffolder"/"$session"_FieldMap_Magnitude.nii.gz "$difffolder"/"$diffdatasuffix"/fieldmap/"$session"_FieldMap_Magnitude_brain -m -f 0.65 -v
        echo ""
        geho "Running fsl_prepare_fieldmap assuming SIEMENS data..."
        echo ""
        fsl_prepare_fieldmap SIEMENS "$difffolder"/"$session"_FieldMap_Phase.nii.gz "$difffolder"/"$diffdatasuffix"/fieldmap/"$session"_FieldMap_Magnitude_brain.nii.gz "$difffolder"/"$diffdatasuffix"/fieldmap/"$session"_fmap_rads "$te"
        echo ""
    else 
        echo ""
        geho "--- Omitting FieldMap step..."
        echo ""
    fi

    # -- Run BET on the DWI data
    geho "Getting the first volume of each DWI image..."
    echo ""
    fslroi "$difffolder"/"$diffdata" "$difffolder"/"$diffdatasuffix"/rawdata/"$diffdata"_nodif 0 1
    geho "Run BET on the B0 EPI image to create masks..."
    echo ""
    bet "$difffolder"/"$diffdatasuffix"/rawdata/"$diffdata"_nodif "$difffolder"/"$diffdatasuffix"/rawdata/"$diffdata"_nodif_brain -m -f 0.35 -v
    echo ""

    # -- Check if PreFreeSurfer was completed to use existing inputs and avoid re-running BET
    geho "--- Checking if PreFreeSurfer was completed to obtain inputs for epi_reg..."
    echo ""

    if [ -f "$t1wfolder"/T1w_acpc_dc_restore_brain.nii.gz ]; then
        geho "PreFreeSurfer data found: "
        echo ""
        echo "$t1wfolder/T1w_acpc_dc_restore_brain.nii.gz"
        echo ""
        if [ -f "$t1wfolder"/T1w_acpc_dc_restore_brain_pve_2.nii.gz ]; then
            geho "FAST already completed."
            echo ""
        else
            geho "Running FAST for the $t1wfolder/T1w_acpc_dc_restore_brain.nii.gz image..."
            echo ""
            fast -v -b -B "$t1wfolder"/T1w_acpc_dc_restore_brain
        fi
        # -- Set all the input image variables for epi_reg
        geho "Setting inputs for epi_reg:"
        t1wimage="$t1wfolder"/T1w_acpc_dc_restore
        t1wbrainimage="$t1wfolder"/T1w_acpc_dc_restore_brain
        wmsegimage="$t1wfolder"/T1w_acpc_dc_restore_brain_pve_2
        t1wimageMask="$t1wfolder"/T1w_acpc_brain_mask
        geho ""
        geho "--> T1w Data:             $t1wimage"
        geho "--> T1w BET+FAST Data:    $t1wbrainimage"
        geho "--> WM Segment FAST Data: $wmsegimage"
        geho "--> T1w Brain Mask Data:  $t1wimageMask"
        echo ""
    else
        geho "PreFreeSurfer data not found. Using raw ${session}_strc_T1w_MPR1.nii.gz as input..."
        echo ""
        if [ -f "$t1wdifffolder"/"$session"_strc_T1w_MPR1_brain_pve_2.nii.gz ]; then
            geho "BET & FAST already completed."
            echo ""
        else
            geho "Running BET for ${t1wfolder}/${session}_strc_T1w_MPR1.nii.gz image..."
            echo ""
            bet "$t1wfolder"/"$session"_strc_T1w_MPR1 "$t1wdifffolder"/"$session"_strc_T1w_MPR1_brain -m -B -f 0.3 -v
            echo ""
            geho "Running FAST for the T1w image..."
            echo ""
            fast -v -b -B "$t1wdifffolder"/"$session"_strc_T1w_MPR1_brain
            echo ""
        fi
        # -- Set all the input image variables for epi_reg
        geho "Setting inputs for epi_reg:"
        t1wimage="$t1wfolder"/"$session"_strc_T1w_MPR1
        t1wbrainimage="$t1wdifffolder"/"$session"_strc_T1w_MPR1_brain_restore
        wmsegimage="$t1wdifffolder"/"$session"_strc_T1w_MPR1_brain_pve_2
        t1wimageMask="$t1wfolder"/"$session"_strc_T1w_MPR1_brain_mask
        geho ""
        geho "--> T1w data:             $t1wimage"
        geho "--> T1w BET+FAST data:    $t1wbrainimage"
        geho "--> WM segment FAST data: $wmsegimage"
        geho "--> T1w brain mask data:  $t1wimageMask"
        echo ""
    fi

    ############################################
    # STEP 3 - Run eddy_cuda
    ############################################    

    # -- Performs eddy call with --fwhm=10,0,0,0,0  --ff=10 -- this performs an initial FWHM smoothing for the first step of registration, then re-run with 4 more iterations without smoothing; the --ff flag adds a fat factor for angular smoothing. 
    # -- For best possible results you want opposing diff directions but in practice we distribute directions on the sphere. Instead we look at 'cones'. This does not smooth the data but rather the predictions to allow best possible estimation via EDDY.
    geho "--- Running eddy_cuda..."    
    echo ""
    eddy_cuda=${FSLGPUDIR}/eddy_cuda${DEFAULT_CUDA_VERSION}
    geho "Using the following eddy_cuda binary: ${eddy_cuda}"
    echo ""

    # -- Eddy call with cuda with extra QC options
    echo "Running command:"
    echo ""
    geho "${eddy_cuda} --imain=${difffolder}/${diffdata} --mask=${difffolder}/${diffdatasuffix}/rawdata/${diffdata}_nodif_brain_mask --acqp=${difffolder}/${diffdatasuffix}/acqparams/${diffdata}/acqparams.txt --index=${difffolder}/${diffdatasuffix}/acqparams/${diffdata}/index.txt --bvecs=${difffolder}/${diffdata}.bvec --bvals=${difffolder}/${diffdata}.bval --fwhm=10,0,0,0,0 --ff=10 --nvoxhp=2000 --flm=quadratic --out=${difffolder}/${diffdatasuffix}/eddy/${diffdata}_eddy_corrected --data_is_shelled --repol -v"
    echo ""
    ${eddy_cuda} --imain=${difffolder}/${diffdata} --mask=${difffolder}/${diffdatasuffix}/rawdata/${diffdata}_nodif_brain_mask --acqp=${difffolder}/${diffdatasuffix}/acqparams/${diffdata}/acqparams.txt --index=${difffolder}/${diffdatasuffix}/acqparams/${diffdata}/index.txt --bvecs=${difffolder}/${diffdata}.bvec --bvals=${difffolder}/${diffdata}.bval --fwhm=10,0,0,0,0 --ff=10 --nvoxhp=2000 --flm=quadratic --out=${difffolder}/${diffdatasuffix}/eddy/${diffdata}_eddy_corrected --data_is_shelled --repol -v --cnr_maps

    # copy nodif_brain_mask to outputs folder
    cp "${difffolder}/${diffdatasuffix}/rawdata/${diffdata}_nodif_brain_mask.nii.gz" "${difffolderout}/nodif_brain_mask.nii.gz"

    ############################################
    # STEP 4 - Run epi_reg w/fieldmap correction
    ############################################

    # -- Performs registration on the DWI EPI raw B0 image to T1w while using the Fieldmap. 
    # -- This gives the EPI --> T1 transformation given the FieldMap. 
    # -- This yields a transformation matrix that can then be applied to the DWI data. 

    if [ ${usefieldmap} == "yes" ]; then
        echo ""
        geho "--- Running epi_reg for EPI--T1 data with fieldmap specification..." 
        echo ""
        epi_reg --epi="$difffolder"/"$diffdatasuffix"/rawdata/"$diffdata"_nodif_brain --t1="$t1wimage" --t1brain="$t1wbrainimage" --out="$difffolder"/"$diffdatasuffix"/reg/"$diffdata"_nodif2T1 --fmap="$difffolder"/"$diffdatasuffix"/fieldmap/"$session"_fmap_rads --wmseg="$wmsegimage" --fmapmag="$difffolder"/"$session"_FieldMap_Magnitude --fmapmagbrain="$difffolder"/"$diffdatasuffix"/fieldmap/"$session"_FieldMap_Magnitude_brain --echospacing="$dwelltimesec" --pedir="$unwarpdir" -v
    else
        echo ""
        geho "--- Running epi_reg for EPI--T1 data without fieldmap specification..." 
        echo ""
        epi_reg --epi="$difffolder"/"$diffdatasuffix"/rawdata/"$diffdata"_nodif_brain --t1="$t1wimage" --t1brain="$t1wbrainimage" --out="$difffolder"/"$diffdatasuffix"/reg/"$diffdata"_nodif2T1 --wmseg="$wmsegimage" --echospacing="$dwelltimesec" --pedir="$unwarpdir" -v
    fi

    ################################################################################################
    # STEP 5 - Apply the epi_reg warp field (fieldmap correction + BBR to T1) to all diffusion data
    ################################################################################################    

    # -- Registers the eddy_corrected DWI data to T1w space
    echo ""
    geho "--- Registering the eddy_corrected DWI data to T1w space..."
    echo ""
    # -- First create a downsampled T1w image to use a target
    diffres=`fslval "$difffolder"/"$diffdata" pixdim1`
    diffresext=`echo $diffres | cut -c1-3`
    geho "Downsampling the $t1wimage, $t1wbrainimage and $t1wimageMask to $diffdata resolution: $diffresext mm ..."
    echo ""
    flirt -in "$t1wimage" -ref "$t1wimage" -applyisoxfm "$diffres" -interp spline -out "$t1wdifffolder"/"$session"_T1w_downsampled2diff_"$diffdatasuffix"_"$diffresext" -v
    flirt -in "$t1wbrainimage" -ref "$t1wimage" -applyisoxfm "$diffres" -interp spline -out "$t1wdifffolder"/"$session"_T1w_brain_downsampled2diff_"$diffdatasuffix"_"$diffresext" -v
    flirt -in "$t1wimageMask" -ref "$t1wimage" -applyisoxfm "$diffres" -interp nearestneighbour -out "$t1wdifffolder"/"brain_mask_downsampled2diff_${diffdatasuffix}_${diffresext}" -v
    flirt -in "$wmsegimage" -ref "$t1wimage" -applyisoxfm "$diffres" -interp spline -out "$t1wdifffolder"/"$session"_T1w_wmsegimage_"$diffdatasuffix"_"$diffresext" -v    
    fslmaths "$t1wdifffolder"/"brain_mask_downsampled2diff_${diffdatasuffix}_${diffresext}" -fillh "$t1wdifffolder"/"brain_mask_downsampled2diff_${diffdatasuffix}_${diffresext}"
    echo ""

    # -- Registers the DWI data to T1w space
    if [ ${usefieldmap} == "yes" ]; then
        geho "Applying the warp for $diffdata to T1w space with fieldmap specification..."; echo ""
        applywarp -i "$difffolder"/"$diffdatasuffix"/eddy/"$diffdata"_eddy_corrected -r "$t1wdifffolder"/"$session"_T1w_downsampled2diff_"$diffdatasuffix"_"$diffresext" -o "$difffolderout"/data -w "$difffolder"/"$diffdatasuffix"/reg/"$diffdata"_nodif2T1_warp --interp=spline --rel -v
    else
        geho "Applying the warp for $diffdata to T1w space without fieldmap specification via epi_reg..."; echo ""
        epi_reg --epi="$difffolder"/"$diffdatasuffix"/eddy/"$diffdata"_eddy_corrected --t1="$t1wdifffolder"/"$session"_T1w_downsampled2diff_"$diffdatasuffix"_"$diffresext" --t1brain="$t1wdifffolder"/"$session"_T1w_brain_downsampled2diff_"$diffdatasuffix"_"$diffresext" --out="$difffolderout"/data --wmseg="$t1wdifffolder"/"$session"_T1w_wmsegimage_"$diffdatasuffix"_"$diffresext" --echospacing="$dwelltimesec" --pedir="$unwarpdir" -v
    fi
    echo ""

    # -- Alan edited on 1/16/17 due to poor BET performance
    geho "Getting the first volume of the registered DWI image..."
    echo ""
    fslroi "$difffolderout"/data "$difffolderout"/data_1stframe 0 1
    geho "Running BET for final DWI data: $difffolderout/$diffdata_data"
    echo ""
    bet "$difffolderout"/data_1stframe "$difffolderout"/data_1stframe -m -f 0.35 -v

    echo ""
    geho "Running fslmaths to brain-mask $diffdata using the down-sampled $t1wimageMask..."
    fslmaths "$t1wdifffolder"/"brain_mask_downsampled2diff_${diffdatasuffix}_${diffresext}" -mul "$difffolderout"/data_1stframe_mask "$difffolderout"/"brain_mask_downsampled2diff_${diffdatasuffix}_${diffresext}"_masked_with_DWI1stframe
    fslmaths "$difffolderout"/data.nii.gz -mul "$t1wdifffolder"/"brain_mask_downsampled2diff_${diffdatasuffix}_${diffresext}" "$difffolderout"/data_brain_masked_with_T1.nii.gz 
    fslmaths "$difffolderout"/data.nii.gz -mul "$difffolderout"/data_1stframe_mask "$difffolderout"/data_brain_masked_with_DWI.nii.gz 
    fslmaths "$difffolderout"/data.nii.gz -mul "$difffolderout"/"brain_mask_downsampled2diff_${diffdatasuffix}_${diffresext}"_masked_with_DWI1stframe "$difffolderout"/data_brain_masked_with_T1orDWI.nii.gz 

    echo ""
    # -- Aligns the BVECS and BVALS using HCP 
    geho "--- Aligning BVECS to T1 space using HCP code"
    echo ""
    $HCPPIPEDIR_GLOBAL/Rotate_bvecs.sh "$difffolder"/"$diffdata".bvec "$difffolder"/"$diffdatasuffix"/reg/"$diffdata"_nodif2T1.mat "$difffolderout"/bvecs
    cp "$difffolder"/"$diffdata".bval "$difffolderout"/bvals
    echo ""

    # -- Perform completion checks
    unset run_error
    geho "--- Checking outputs..."
    echo ""
    if [ -f "$t1wdifffolder"/"$session"_T1w_downsampled2diff_"$diffdatasuffix"_"$diffresext".nii.gz ]; then
        OutFile="$t1wdifffolder"/"$session"_T1w_downsampled2diff_"$diffdatasuffix"_"$diffresext".nii.gz
        geho "T1w data in DWI resolution:   $OutFile"
        echo ""
    else
        reho "T1w data in DWI resolution missing. Something went wrong."
        echo ""
        run_error="yes"
    fi
    if [ -f "$difffolderout"/data.nii.gz ]; then
        OutFile="$difffolderout"/data.nii.gz
        geho "DWI final processed data:     $OutFile"
        echo ""
    else
        reho "DWI final processed data missing. Something went wrong."
        echo ""
        run_error="yes"
    fi
    if [ -f  "$difffolderout"/data_brain_masked_with_T1orDWI.nii.gz ]; then
        OutFile="$difffolderout"/data_brain_masked_with_T1orDWI.nii.gz 
        geho "DWI brain-masked data:        $OutFile"
        echo ""
    else
        reho "DWI brain-masked data missing. Something went wrong."
        echo ""
        run_error="yes"
    fi
    if [ -f  "$difffolderout"/bvecs ]; then
        OutFile="$difffolderout"/_bvecs
        geho "DWI bvecs:                    $OutFile"
        echo ""
    else
        reho "BVECS in $difffolderout missing. Something went wrong."
        echo ""
        run_error="yes"
    fi
    if [ -f  "$difffolderout"/bvals ]; then
        OutFile="$difffolderout"/bvals
        geho "DWI bvals:                    $OutFile"
        echo ""
    else
        reho "BVALS in $difffolderout missing. Something went wrong."
        echo ""
        run_error="yes"
    fi
    if [ -f  "$difffolderout"/nodif_brain_mask.nii.gz ]; then
        OutFile="$difffolderout"/nodif_brain_mask.nii.gz
        geho "nodif_brain_mask:              $OutFile"
        echo ""
    else
        reho "nodif_brain_mask in $difffolderout missing. Something went wrong."
        echo ""
        run_error="yes"
    fi

    if [[ -z ${run_error} ]]; then 
        echo ""
        geho "--- DWI preprocessing successfully completed"
        echo ""
        geho "------------------------- Successful completion of work -------------------------"
        echo ""
    else
        echo ""
        reho "--- Results missing. Something went wrong with calculation."
        echo ""
        exit 1
    fi

}

######################################### END OF WORK ##########################################

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
