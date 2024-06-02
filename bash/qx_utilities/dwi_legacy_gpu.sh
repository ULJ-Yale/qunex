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

Parameters:
    --sessionsfolder (str, default '.'):
        Path to study data folder.

    --sessions (str):
        Comma separated list of sessions to run.

    --echospacing (str):
        EPI Echo Spacing for data [in ms]; e.g. 0.69.

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
        <session>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR. If you
        provide multiple suffixes, QuNex will merge the images along with their
        bvals and bvecs and run processing on the merged image.

    --overwrite (str):
        Delete prior run for a given session ('yes' | 'no').

    --te (float):
        This is the echo time difference of the fieldmap sequence - find this
        out form the operator - defaults are *usually* 2.46ms on SIEMENS.

    --nogpu (flag, default 'no'):
        If set, this command will be processed useing a CPU instead of a GPU.

Output files:
    - difffolder=${sessionsfolder}/${session}/hcp/${session}/Diffusion
    - t1wdifffolder=${sessionsfolder}/${session}/hcp/${session}/T1w/Diffusion

    ::

        $difffolder/rawdata
        $difffolder/eddy
        $difffolder/data
        $difffolder/reg
        $t1wdifffolder

Notes:
    Apptainer (Singularity) and GPU support:
        If nogpu is not provided, this command will facilitate GPUs to speed
        up processing. Since the command uses CUDA binaries, an NVIDIA GPU
        is required. To give access to CUDA drivers to the system inside the
        Apptainer (Singularity) container, you need to use the --nv flag
        of the qunex_container script.

Examples:
    NOTE: CUDA libraries need to be loaded for this command to work, to do this
    you usually need to load the appropriate module on HPC systems. When
    scheduling for example, add the bash parameter to the command call, e.g.:

    ``--bash="module load CUDA/11.3.1"``

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
            --overwrite='yes' \\
            --bash="module load CUDA//11.3.1" \\
            --scheduler='<name_of_scheduler_and_options>'

    Example with disabled GPU processing:

    ::

        qunex dwi_legacy_gpu \\
            --sessionsfolder='<folder_with_sessions>' \\
            --sessions='<comma_separarated_list_of_cases>' \\
            --diffdatasuffix='DWI_dir91_LR' \\
            --usefieldmap='no' \\
            --pedir='1' \\
            --echospacing='0.69' \\
            --unwarpdir='x-' \\
            --overwrite='yes' \\
            --nogpu='yes'

EOF
exit 0
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
    unset usefieldmap
    unset nogpu
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
            --usefieldmap=*)
                usefieldmap=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --nogpu=*)
                nogpu=${argument/*=/""}
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
    echo "   No GPU: ${nogpu}"
    echo "-- ${script_name}: Specified Command-Line Options - End --"
    echo ""
    echo "------------------------- Start of work --------------------------------"
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
    echospacing="$echospacing" #EPI Echo Spacing for data (in ms); e.g. 0.69
    pedir="$pedir" #Use 1 for Left-Right Phase Encoding, 2 for Anterior-Posterior
    te="$te" #delta te in ms for field map or "NONE" if not used
    unwarpdir="$unwarpdir" # direction along which to unwarp
    dwelltime="$echospacing" #same variable as echospacing - if you have in-plane acceleration then this value needs to be divided by the GRAPPA or SENSE factor (miliseconds)
    dwelltimesec=`echo "scale=6; $dwelltime/1000" | bc` # set the dwell time to seconds

    # -- Establish global directory paths
    echo "--- Establishing paths for all input and output folders:"
    echo ""

    # -- Establish global directory paths
    t1wfolder="$sessionsfolder"/"$session"/hcp/"$session"/T1w
    difffolder="$sessionsfolder"/"$session"/hcp/"$session"/Diffusion
    t1wdifffolder="$t1wfolder"/Diffusion

    echo "T1w folder:           $t1wfolder"
    echo "Diffusion folder:     $difffolder"
    echo "T1w diffusion folder: $t1wdifffolder"
    echo ""

    # -- Prepare diff data
    # if there is a commma in the diffdata suffix we have multiple images and we need to merge
    if [[ $diffdatasuffix == *,* ]]; then

        # remove previous
        if [[ "$overwrite" == "no" ]]; then
            if [[ -f "${difffolder}/${session}_merged.nii.gz" ]]; then
                echo "ERROR: merged DWI data already exists and overwrite is not set to yes"
                exit 1
            elif [[ -f "${difffolder}/${session}_merged.bval" ]]; then
                echo "ERROR: merged DWI data already exists and overwrite is not set to yes"
                exit 1
            elif [[ -f "${difffolder}/${session}_merged.bvec" ]]; then
                echo "ERROR: merged DWI data already exists and overwrite is not set to yes"
                exit 1
            fi
        else
            rm "${difffolder}/${session}_merged.nii.gz"  > /dev/null 2>&1
            rm "${difffolder}/${session}_merged.bval"  > /dev/null 2>&1
            rm "${difffolder}/${session}_merged.bvec"  > /dev/null 2>&1
        fi

        # storage
        difffiles=""
        bvals=""
        bvecs=""

        # merge data
        IFS=","
        for image in $diffdatasuffix; do
            difffiles="${difffiles} ${difffolder}/${session}_${image}.nii.gz"
        done
        eval "fslmerge -t ${difffolder}/${session}_merged.nii.gz ${difffiles}"

        # bvals
        for ((i=1; ; i++))
        do
            merged_row_bval=""

            for image in $diffdatasuffix; do
                row_bval=$(awk "NR==$i" "${difffolder}/${session}_${image}.bval")
                merged_row_bval+="$row_bval "
            done

            # Trim leading/trailing whitespaces
            merged_row_bval=$(echo "$merged_row_bval" | awk '{$1=$1};1')

            # Print or store the merged row
            echo "$merged_row_bval" >> ${difffolder}/${session}_merged.bval

            # Exit the loop if any file reaches end-of-file
            [ -z "$row_bval" ] && break
        done

        # bvecs
        for ((i=1; ; i++))
        do
            merged_row_bvec=""

            for image in $diffdatasuffix; do
                row_bvec=$(awk "NR==$i" "${difffolder}/${session}_${image}.bvec")
                merged_row_bvec+="$row_bvec "
            done

            # Trim leading/trailing whitespaces
            merged_row_bvec=$(echo "$merged_row_bvec" | awk '{$1=$1};1')

            # Print or store the merged row
            echo "$merged_row_bvec" >> ${difffolder}/${session}_merged.bvec

            # Exit the loop if any file reaches end-of-file
            [ -z "$row_bvec" ] && break
        done

        # set the suffix
        diffdatasuffix="merged"
    fi

    diffdata="$session"_"$diffdatasuffix" # Diffusion data suffix name - e.g. if the data is called <sessionID>_DWI_dir91_LR.nii.gz - you would enter DWI_dir91_LR

    # -- Delete any existing output sub-directories
    if [ "$overwrite" == "yes" ]; then
        echo "--- Deleting prior runs for $diffdata ..."
        echo ""
        rm -rf "$difffolder"/rawdata/"$diffdata"* > /dev/null 2>&1
        rm -rf "$difffolder"/eddy/"$diffdata"* > /dev/null 2>&1
        rm -rf "$difffolder"/reg/"$diffdata"* > /dev/null 2>&1
        rm -rf "$difffolder"/fieldmap > /dev/null 2>&1
        rm -rf "$difffolder"/acqparams/"$diffdata" > /dev/null 2>&1
        rm -rf "$t1wdifffolder"/* > /dev/null 2>&1
    else
        timestamp=`date +%Y-%m-%d_%H.%M.%S.%6N`
        if [ -d $difffolder ]; then
            echo "--- Backing up previous ${difffolder} as $difffolder_${timestamp} ..."
            echo ""
            cp $difffolder $difffolder_${timestamp}
        fi
        if [ -d $t1wdifffolder ]; then
            echo "--- Backing up previous ${t1wdifffolder} as $t1wdifffolder_${timestamp} ..."
            echo ""
            cp $t1wdifffolder $t1wdifffolder_${timestamp}
        fi
    fi

    # -- Make sure output directories exist
    mkdir -p "$t1wdifffolder" 2> /dev/null
    mkdir -p "$difffolder"/rawdata 2> /dev/null
    mkdir -p "$difffolder"/eddy 2> /dev/null
    mkdir -p "$difffolder"/reg 2> /dev/null
    mkdir -p "$difffolder"/fieldmap 2> /dev/null
    mkdir -p "$difffolder"/acqparams 2> /dev/null

    #########################################
    # STEP 0 - move the unprocessed data
    #########################################

    echo "--- Copying unprocesed data into the Diffusion folder"
    echo ""
    unproc_file="${sessionsfolder}/${session}/hcp/${session}/unprocessed/Diffusion/${session}_${diffdatasuffix}"
    if [ -f "${unproc_file}.bval" ]; then
        echo "Copying ${unproc_file}.bval"
        cp "${unproc_file}.bval" "${difffolder}/"
    fi
    if [ -f "${unproc_file}.bvec" ]; then
        echo "Copying ${unproc_file}.bvec"
        cp "${unproc_file}.bvec" "${difffolder}/"
    fi
    if [ -f "${unproc_file}.nii.gz" ]; then
        echo "Copying ${unproc_file}.nii.gz"
        cp "${unproc_file}.nii.gz" "${difffolder}/"
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

    echo "--- Setting up acquisition parameters:"
    echo ""
    # -- Make session-specific and acquisition-specific parameter folder
    mkdir "$difffolder"/acqparams/"$diffdata" > /dev/null 2>&1

    # -- Create index file - parameter file for number of frames in the DWI image
    sesdimt=`fslval "$difffolder"/"$diffdata" dim4` #Number of datapoints per Pos series
    rm "$difffolder"/acqparams/"$diffdata"/index.txt > /dev/null 2>&1
    for (( j=0; j<${sesdimt}; j++ )); do echo "1" >> "$difffolder"/acqparams/"$diffdata"/index.txt; done

    # -- Create phase encoding and dwelltime parameter file
    rm "$difffolder"/acqparams/"$diffdata"/acqparams.txt > /dev/null 2>&1
    if [ "$pedir" == "1" ]; then
        voxel_number=`fslval "$difffolder"/"$diffdata" dim1`
        readout_time=`echo "scale=6; $dwelltimesec*($voxel_number-1)" | bc`
            echo "1 0 0 $readout_time" >> "$difffolder"/acqparams/"$diffdata"/acqparams.txt
    else
        voxel_number=`fslval "$difffolder"/"$diffdata" dim2`
        readout_time=`echo "scale=6; $dwelltimesec*($voxel_number-1)" | bc`
            echo "0 1 0 $readout_time" >> "$difffolder"/acqparams/"$diffdata"/acqparams.txt
    fi

    echo "Check acquisition parameter files:"
    echo ""
    echo "`ls $difffolder/acqparams/$diffdata/`"
    echo ""

    ############################################
    # STEP 2 - Prepare FieldMaps and T1w Images
    ############################################

    if [ ${usefieldmap} == "yes" ]; then
        echo "--- Preparing FieldMaps and T1w images..."
        echo ""
        echo "Running conservative BET on the FieldMap Magnitude image..."
        echo ""
        bet "$difffolder"/"$session"_FieldMap_Magnitude.nii.gz "$difffolder"/fieldmap/"$session"_FieldMap_Magnitude_brain -m -f 0.65 -v
        echo ""
        echo "Running fsl_prepare_fieldmap assuming SIEMENS data..."
        echo ""
        fsl_prepare_fieldmap SIEMENS "$difffolder"/"$session"_FieldMap_Phase.nii.gz "$difffolder"/fieldmap/"$session"_FieldMap_Magnitude_brain.nii.gz "$difffolder"/fieldmap/"$session"_fmap_rads "$te"
        echo ""
    else 
        echo ""
        echo "--- Omitting FieldMap step..."
        echo ""
    fi

    # -- Run BET on the DWI data
    echo "Getting the first volume of each DWI image..."
    echo ""
    fslroi "$difffolder"/"$diffdata" "$difffolder"/rawdata/"$diffdata"_nodif 0 1
    echo "Run BET on the B0 EPI image to create masks..."
    echo ""
    bet "$difffolder"/rawdata/"$diffdata"_nodif "$difffolder"/rawdata/"$diffdata"_nodif_brain -m -f 0.35 -v
    echo ""

    # -- Check if PreFreeSurfer was completed to use existing inputs and avoid re-running BET
    echo "--- Checking if PreFreeSurfer was completed to obtain inputs for epi_reg..."
    echo ""

    if [ -f "$t1wfolder"/T1w_acpc_dc_restore_brain.nii.gz ]; then
        echo "PreFreeSurfer data found: "
        echo ""
        echo "$t1wfolder/T1w_acpc_dc_restore_brain.nii.gz"
        echo ""
        if [ -f "$t1wfolder"/T1w_acpc_dc_restore_brain_pve_2.nii.gz ]; then
            echo "FAST already completed."
            echo ""
        else
            echo "Running FAST for the $t1wfolder/T1w_acpc_dc_restore_brain.nii.gz image..."
            echo ""
            fast -v -b -B "$t1wfolder"/T1w_acpc_dc_restore_brain
        fi
        # -- Set all the input image variables for epi_reg
        echo "Setting inputs for epi_reg:"
        t1wimage="$t1wfolder"/T1w_acpc_dc_restore
        t1wbrainimage="$t1wfolder"/T1w_acpc_dc_restore_brain
        wmsegimage="$t1wfolder"/T1w_acpc_dc_restore_brain_pve_2
        t1wimagemask="$t1wfolder"/T1w_acpc_brain_mask
        echo ""
        echo "---> T1w Data:             $t1wimage"
        echo "---> T1w BET+FAST Data:    $t1wbrainimage"
        echo "---> WM Segment FAST Data: $wmsegimage"
        echo "---> T1w Brain Mask Data:  $t1wimagemask"
        echo ""
    else
        echo "PreFreeSurfer data not found. Using raw ${session}_strc_T1w_MPR1.nii.gz as input..."
        echo ""
        if [ -f "$t1wdifffolder"/"$session"_strc_T1w_MPR1_brain_pve_2.nii.gz ]; then
            echo "BET & FAST already completed."
            echo ""
        else
            echo "Running BET for ${t1wfolder}/${session}_strc_T1w_MPR1.nii.gz image..."
            echo ""
            bet "$t1wfolder"/"$session"_strc_T1w_MPR1 "$t1wdifffolder"/"$session"_strc_T1w_MPR1_brain -m -B -f 0.3 -v
            echo ""
            echo "Running FAST for the T1w image..."
            echo ""
            fast -v -b -B "$t1wdifffolder"/"$session"_strc_T1w_MPR1_brain
            echo ""
        fi
        # -- Set all the input image variables for epi_reg
        echo "Setting inputs for epi_reg:"
        t1wimage="$t1wfolder"/"$session"_strc_T1w_MPR1
        t1wbrainimage="$t1wdifffolder"/"$session"_strc_T1w_MPR1_brain_restore
        wmsegimage="$t1wdifffolder"/"$session"_strc_T1w_MPR1_brain_pve_2
        t1wimagemask="$t1wfolder"/"$session"_strc_T1w_MPR1_brain_mask
        echo ""
        echo "---> T1w data:             $t1wimage"
        echo "---> T1w BET+FAST data:    $t1wbrainimage"
        echo "---> WM segment FAST data: $wmsegimage"
        echo "---> T1w brain mask data:  $t1wimagemask"
        echo ""
    fi

    ############################################
    # STEP 3 - Run eddy
    ############################################    

    # -- Performs eddy call with --fwhm=10,0,0,0,0  --ff=10 -- this performs an initial FWHM smoothing for the first step of registration, then re-run with 4 more iterations without smoothing; the --ff flag adds a fat factor for angular smoothing. 
    # -- For best possible results you want opposing diff directions but in practice we distribute directions on the sphere. Instead we look at 'cones'. This does not smooth the data but rather the predictions to allow best possible estimation via EDDY.
    echo "--- Running eddy..."    
    echo ""

    if [[ ${nogpu} == "yes" ]]; then
        eddy_bin=${FSLBINDIR}/eddy_cpu
    else
        eddy_bin=${FSLBINDIR}/eddy_cuda${DEFAULT_CUDA_VERSION}
    fi

    echo "Using the following eddy binary: ${eddy_bin}"
    echo ""

    # -- Eddy call with cuda with extra QC options
    echo "Running command:"
    echo ""
    echo "${eddy_bin} --imain=${difffolder}/${diffdata} --mask=${difffolder}/rawdata/${diffdata}_nodif_brain_mask --acqp=${difffolder}/acqparams/${diffdata}/acqparams.txt --index=${difffolder}/acqparams/${diffdata}/index.txt --bvecs=${difffolder}/${diffdata}.bvec --bvals=${difffolder}/${diffdata}.bval --fwhm=10,0,0,0,0 --ff=10 --nvoxhp=2000 --flm=quadratic --out=${difffolder}/eddy/${diffdata}_eddy_corrected --data_is_shelled --repol -v"
    echo ""
    ${eddy_bin} --imain=${difffolder}/${diffdata} --mask=${difffolder}/rawdata/${diffdata}_nodif_brain_mask --acqp=${difffolder}/acqparams/${diffdata}/acqparams.txt --index=${difffolder}/acqparams/${diffdata}/index.txt --bvecs=${difffolder}/${diffdata}.bvec --bvals=${difffolder}/${diffdata}.bval --fwhm=10,0,0,0,0 --ff=10 --nvoxhp=2000 --flm=quadratic --out=${difffolder}/eddy/${diffdata}_eddy_corrected --data_is_shelled --repol -v --cnr_maps

    ############################################
    # STEP 4 - Run epi_reg w/fieldmap correction
    ############################################

    # -- Performs registration on the DWI EPI raw B0 image to T1w while using the Fieldmap. 
    # -- This gives the EPI ---> T1 transformation given the FieldMap. 
    # -- This yields a transformation matrix that can then be applied to the DWI data. 

    if [ ${usefieldmap} == "yes" ]; then
        echo ""
        echo "--- Running epi_reg for EPI--T1 data with fieldmap specification..." 
        echo ""
        epi_reg --epi="$difffolder"/rawdata/"$diffdata"_nodif_brain --t1="$t1wimage" --t1brain="$t1wbrainimage" --out="$difffolder"/reg/"$diffdata"_nodif2T1 --fmap="$difffolder"/fieldmap/"$session"_fmap_rads --wmseg="$wmsegimage" --fmapmag="$difffolder"/"$session"_FieldMap_Magnitude --fmapmagbrain="$difffolder"/fieldmap/"$session"_FieldMap_Magnitude_brain --echospacing="$dwelltimesec" --pedir="$unwarpdir" -v
    else
        echo ""
        echo "--- Running epi_reg for EPI--T1 data without fieldmap specification..." 
        echo ""
        epi_reg --epi="$difffolder"/rawdata/"$diffdata"_nodif_brain --t1="$t1wimage" --t1brain="$t1wbrainimage" --out="$difffolder"/reg/"$diffdata"_nodif2T1 --wmseg="$wmsegimage" --echospacing="$dwelltimesec" --pedir="$unwarpdir" -v
    fi

    ################################################################################################
    # STEP 5 - Apply the epi_reg warp field (fieldmap correction + BBR to T1) to all diffusion data
    ################################################################################################    

    # -- Registers the eddy_corrected DWI data to T1w space
    echo ""
    echo "--- Registering the eddy_corrected DWI data to T1w space..."
    echo ""
    # -- First create a downsampled T1w image to use a target
    diffres=`fslval "$difffolder"/"$diffdata" pixdim1`
    diffresext=`echo $diffres | cut -c1-3`
    echo "Downsampling the $t1wimage, $t1wbrainimage and $t1wimagemask to $diffdata resolution: $diffresext mm ..."
    echo ""
    flirt -in "$t1wimage" -ref "$t1wimage" -applyisoxfm "$diffres" -interp spline -out "$t1wdifffolder"/T1w_downsampled2diff_"$diffresext" -v
    flirt -in "$t1wbrainimage" -ref "$t1wimage" -applyisoxfm "$diffres" -interp spline -out "$t1wdifffolder"/T1w_brain_downsampled2diff_"$diffresext" -v
    flirt -in "$t1wimagemask" -ref "$t1wimage" -applyisoxfm "$diffres" -interp nearestneighbour -out "$t1wdifffolder"/"T1w_brain_mask_downsampled2diff_${diffresext}" -v
    flirt -in "$wmsegimage" -ref "$t1wimage" -applyisoxfm "$diffres" -interp spline -out "$t1wdifffolder"/T1w_wmsegimage_"$diffresext" -v
    fslmaths "$t1wdifffolder"/"T1w_brain_mask_downsampled2diff_${diffresext}" -fillh "$t1wdifffolder"/"T1w_brain_mask_downsampled2diff_${diffresext}"
    echo ""

    # -- Registers the DWI data to T1w space
    if [ ${usefieldmap} == "yes" ]; then
        echo "Applying the warp for $diffdata to T1w space with fieldmap specification..."; echo ""
        applywarp -i "$difffolder"/eddy/"$diffdata"_eddy_corrected -r "$t1wdifffolder"/T1w_downsampled2diff_"$diffresext" -o "$t1wdifffolder"/data -w "$difffolder"/reg/"$diffdata"_nodif2T1_warp --interp=spline --rel -v
    else
        echo "Applying the warp for $diffdata to T1w space without fieldmap specification via epi_reg..."; echo ""
        epi_reg --epi="$difffolder"/eddy/"$diffdata"_eddy_corrected --t1="$t1wdifffolder"/T1w_downsampled2diff_"$diffresext" --t1brain="$t1wdifffolder"/T1w_brain_downsampled2diff_"$diffresext" --out="$t1wdifffolder"/data --wmseg="$t1wdifffolder"/T1w_wmsegimage_"$diffresext" --echospacing="$dwelltimesec" --pedir="$unwarpdir" -v
    fi
    echo ""

    echo "Getting the first volume of the registered DWI image..."
    echo ""
    fslroi "$t1wdifffolder"/data "$t1wdifffolder"/data_1stframe 0 1
    echo "Running BET for final DWI data: $t1wdifffolder/$diffdata_data"
    echo ""
    bet "$t1wdifffolder"/data_1stframe "$t1wdifffolder"/data_1stframe -m -f 0.35 -v

    echo ""
    echo "Running fslmaths to brain-mask $diffdata using the down-sampled $t1wimagemask..."
    fslmaths "$t1wdifffolder"/"T1w_brain_mask_downsampled2diff_${diffresext}" -mul "$t1wdifffolder"/data_1stframe_mask "$t1wdifffolder"/"T1w_brain_mask_downsampled2diff_${diffresext}"_masked_with_DWI1stframe
    fslmaths "$t1wdifffolder"/data.nii.gz -mul "$t1wdifffolder"/"T1w_brain_mask_downsampled2diff_${diffresext}" "$t1wdifffolder"/data_brain_masked_with_T1.nii.gz 
    fslmaths "$t1wdifffolder"/data.nii.gz -mul "$t1wdifffolder"/data_1stframe_mask "$t1wdifffolder"/data_brain_masked_with_DWI.nii.gz 
    fslmaths "$t1wdifffolder"/data.nii.gz -mul "$t1wdifffolder"/"T1w_brain_mask_downsampled2diff_${diffresext}"_masked_with_DWI1stframe "$t1wdifffolder"/data_brain_masked_with_T1orDWI.nii.gz 

    echo ""
    # -- Aligns the BVECS and BVALS using HCP 
    echo "--- Aligning BVECS to T1 space using HCP code"
    echo ""
    $HCPPIPEDIR_Global/Rotate_bvecs.sh "$difffolder"/"$diffdata".bvec "$difffolder"/reg/"$diffdata"_nodif2T1.mat "$t1wdifffolder"/bvecs
    cp "$difffolder"/"$diffdata".bval "$t1wdifffolder"/bvals
    echo ""

    # copy the T1w brain mask
    cp "${t1wdifffolder}/T1w_brain_mask_downsampled2diff_${diffresext}.nii.gz" $t1wdifffolder/nodif_brain_mask.nii.gz

    # -- Perform completion checks
    unset run_error
    echo "--- Checking outputs..."
    echo ""
    if [ -f "$t1wdifffolder"/T1w_downsampled2diff_"$diffresext".nii.gz ]; then
        OutFile="$t1wdifffolder"/T1w_downsampled2diff_"$diffresext".nii.gz
        echo "T1w data in DWI resolution:   $OutFile"
        echo ""
    else
        echo "T1w data in DWI resolution missing. Something went wrong."
        echo ""
        run_error="yes"
    fi
    if [ -f "$t1wdifffolder"/data.nii.gz ]; then
        OutFile="$t1wdifffolder"/data.nii.gz
        echo "DWI final processed data:     $OutFile"
        echo ""
    else
        echo "DWI final processed data missing. Something went wrong."
        echo ""
        run_error="yes"
    fi
    if [ -f  "$t1wdifffolder"/data_brain_masked_with_T1orDWI.nii.gz ]; then
        OutFile="$t1wdifffolder"/data_brain_masked_with_T1orDWI.nii.gz 
        echo "DWI brain-masked data:        $OutFile"
        echo ""
    else
        echo "DWI brain-masked data missing. Something went wrong."
        echo ""
        run_error="yes"
    fi
    if [ -f  "$t1wdifffolder"/bvecs ]; then
        OutFile="$t1wdifffolder"/bvecs
        echo "DWI bvecs:                    $OutFile"
        echo ""
    else
        echo "BVECS in $t1wdifffolder missing. Something went wrong."
        echo ""
        run_error="yes"
    fi
    if [ -f  "$t1wdifffolder"/bvals ]; then
        OutFile="$t1wdifffolder"/bvals
        echo "DWI bvals:                    $OutFile"
        echo ""
    else
        echo "BVALS in $t1wdifffolder missing. Something went wrong."
        echo ""
        run_error="yes"
    fi
    if [[ -z ${run_error} ]]; then 
        echo ""
        echo "--- DWI preprocessing successfully completed"
        echo ""
        echo "------------------------- Successful completion of work -------------------------"
        echo ""
    else
        echo ""
        echo "--- Results missing. Something went wrong with calculation."
        echo ""
        exit 1
    fi
}

######################################### END OF WORK ##########################################

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
