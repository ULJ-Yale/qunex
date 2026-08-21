#!/bin/bash
#
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## PRODUCT
#
#  qunex_environment.sh
#
# ## DESCRIPTION:
#
# * This is a general script developed as a front-end environment and path organization for the QuNex infrastructure
#
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * QuNex Suite
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# * This script needs to be sourced in each users .bash_profile like so:
#
#    TOOLS=/<absolute_path_to_software_folder>
#    export TOOLS
#    source $TOOLS/env/qunex_environment.sh
#
# ## PREREQUISITE PRIOR PROCESSING
#
# N/A
#
#~ND~END~

# ------------------------------------------------------------------------------
#  Environment clear and check functions
# ------------------------------------------------------------------------------

ENVVARIABLES='PATH MATLABPATH PYTHONPATH QUNEXVer TOOLS QUNEXREPO QUNEXPATH QUNEXEXTENSIONS QUNEXLIBRARY QUNEXLIBRARYETC TemplateFolder FSL_BINDIR FSL_FIXDIR FREESURFERDIR FREESURFER_HOME FREESURFER_SCHEDULER FreeSurferSchedulerDIR WORKBENCHDIR DCMNIIDIR DICMNIIDIR MATLABDIR MATLABBINDIR OCTAVEDIR OCTAVEPKGDIR OCTAVEBINDIR RDIR HCPWBDIR AFNIDIR PYLIBDIR FSLDIR FSLBINDIR PALMDIR QUNEXMCOMMAND HCPPIPEDIR CARET7DIR GRADUNWARPDIR HCPPIPEDIR_Templates HCPPIPEDIR_Bin HCPPIPEDIR_Config HCPPIPEDIR_PreFS HCPPIPEDIR_FS HCPPIPEDIR_FS_CUSTOM HCPPIPEDIR_PostFS HCPPIPEDIR_fMRISurf HCPPIPEDIR_fMRIVol HCPPIPEDIR_tfMRI HCPPIPEDIR_dMRI HCPPIPEDIR_dMRITract HCPPIPEDIR_Global HCPPIPEDIR_tfMRIAnalysis HCPCIFTIRWDIR MSMBin HCPPIPEDIR_dMRITractFull HCPPIPEDIR_dMRILegacy AutoPtxFolder USEOCTAVE QUNEXENV MAMBADIR MSMBINDIR MSMCONFIGDIR R_LIBS FSL_FIX_CIFTIRW FSFAST_HOME SUBJECTS_DIR MINC_BIN_DIR MNI_DIR MINC_LIB_DIR MNI_DATAPATH FSF_OUTPUT_FORMAT ANTSDIR CUDIMOT'
export ENVVARIABLES

# -- Check if inside the container and reset the environment on first setup
if [[ -e /opt/.container ]]; then
    # -- Allow only one sourcing in the container
    if [[ "$QUNEX_SOURCED" != "TRUE" ]]; then
        export QUNEX_SOURCED="TRUE"
    else
        # -- Already sourced outside, so exit
        return 0 2>/dev/null || exit 0
    fi

    # -- First unset all conflicting variables in the environment
    unset $ENVVARIABLES

    # -- Set PATH
    export PATH=/usr/local/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

    if [ -z ${TOOLS+x} ]; then TOOLS="/opt"; fi
    if [ -z ${USEOCTAVE+x} ]; then USEOCTAVE="TRUE"; fi

    PATH=${TOOLS}:${PATH}
    export TOOLS PATH USEOCTAVE

# -- Use Octave outside of container, inside this is auto set to TRUE
elif [[ -e ~/.qunexuseoctave ]]; then
    export USEOCTAVE="TRUE"
fi


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= CODE START =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=

# ------------------------------------------------------------------------------
# -- Setup privileges and environment disclaimer
# ------------------------------------------------------------------------------

umask 002

# ------------------------------------------------------------------------------
# -- Check Operating System (needed for some apps like Workbench)
# ------------------------------------------------------------------------------
OperatingSystem=`uname -sv`
if [[ `gcc --version | grep 'darwin'` != "" ]]; then OSInfo="Darwin"; else
    if [[ `cat /etc/*-release | grep 'Red Hat'` != "" ]] || [[ `cat /etc/*-release | grep 'rhel'` != "" ]]; then OSInfo="RedHat";
        elif [[ `cat /etc/*-release| grep 'ubuntu'` != "" ]]; then OSInfo="Ubuntu";
            elif [[ `cat /etc/*-release | grep 'debian'` != "" ]]; then OSInfo="Debian";
    fi
fi
export OperatingSystem OSInfo

# ------------------------------------------------------------------------------
# -- Check for and setup master software folder
# ------------------------------------------------------------------------------

if [ -z ${TOOLS} ]; then
    echo ""
    echo " -- ERROR: TOOLS environment variable not setup on this system."
    echo "    Please add to your environment profile (e.g. .bash_profile):"
    echo ""
    echo "    TOOLS=/<absolute_path_to_software_folder>/"
    echo 1
    echo ""
else
    export TOOLS
fi

# ------------------------------------------------------------------------------
# -- Set up prompt
# ------------------------------------------------------------------------------

PS1="\[\e[0;36m\][QuNex \W]\$\[\e[0m\] "
PROMPT_COMMAND='echo -ne "\033]0;QuNex: ${PWD}\007"'

# ------------------------------------------------------------------------------
# -- QuNex - General Code
# ------------------------------------------------------------------------------

if [ -z ${QUNEXREPO} ]; then
    QUNEXREPO="qunex"
fi

# ---- changed to work with new clone/branches setup

if [ -e ~/qunexinit.sh ]; then
    source ~/qunexinit.sh
fi

QUNEXPATH=${TOOLS}/${QUNEXREPO}
QuNexVer=`cat ${QUNEXPATH}/VERSION.md`
export QUNEXPATH QUNEXREPO QuNexVer

if [ -e ~/qunexinit.sh ]; then
    echo ""
    echo " --- NOTE: QuNex is set by your ~/qunexinit.sh file! ----"
    echo ""
    echo " ---> QuNex path is set to: ${QUNEXPATH} "
    echo ""
fi

# ------------------------------------------------------------------------------
# -- Load dependent software
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# -- Set default folder names for dependencies if undefined by user environment:
# ------------------------------------------------------------------------------

# -- Check if folders for dependencies are set in the global path
if [[ -z ${FSLDIR} ]]; then FSLDIR="${TOOLS}/fsl/fsl"; export FSLDIR; fi
if [[ -z ${FSLCONFDIR} ]]; then FSLCONFDIR="${FSLDIR}/config"; export FSLCONFDIR; fi
if [[ -z ${FSL_BINDIR} ]]; then FSL_BINDIR="${TOOLS}/fsl/fsl/bin"; fi
if [[ -z ${FSL_FIXDIR} ]]; then FSL_FIXDIR="${TOOLS}/fsl/fsl/bin"; fi
if [[ -z ${FREESURFERDIR} ]]; then FREESURFERDIR="${TOOLS}/freesurfer/freesurfer"; export FREESURFERDIR; fi
if [[ -z ${FreeSurferSchedulerDIR} ]]; then FreeSurferSchedulerDIR="${TOOLS}/freesurfer/FreeSurferScheduler"; export FreeSurferSchedulerDIR; fi
if [[ -z ${HCPWBDIR} ]]; then HCPWBDIR="${TOOLS}/workbench/workbench"; export HCPWBDIR; fi
if [[ -z ${AFNIDIR} ]]; then AFNIDIR="${TOOLS}/AFNI/AFNI"; export AFNIDIR; fi
if [[ -z ${ANTSDIR} ]]; then ANTSDIR="${TOOLS}/ANTs/ANTs/bin"; export ANTSDIR; fi
if [[ -z ${DCMNIIDIR} ]]; then DCMNIIDIR="${TOOLS}/dcm2niix/dcm2niix"; export DCMNIIDIR; fi
if [[ -z ${OCTAVEDIR} ]]; then OCTAVEDIR="${TOOLS}/octave/octave"; export OCTAVEDIR; fi
if [[ -z ${PYLIBDIR} ]]; then PYLIBDIR="${TOOLS}/pylib"; export PYLIBDIR; fi
if [[ -z ${FMRIPREPDIR} ]]; then FMRIPREPDIR="${TOOLS}/fmriprep/fmriprep"; export FMRIPREPDIR; fi
if [[ -z ${MATLABDIR} ]]; then MATLABDIR="${TOOLS}/matlab"; export MATLABDIR; fi
if [[ -z ${GRADUNWARPDIR} ]]; then GRADUNWARPDIR="${TOOLS}/gradunwarp/gradunwarp"; export GRADUNWARPDIR; fi
if [[ -z ${QUNEXENV} ]]; then QUNEXENV="${TOOLS}/env/qunex"; export QUNEXENV; fi
if [[ -z ${MAMBADIR} ]]; then MAMBADIR="${TOOLS}/miniconda"; export MAMBADIR; fi
if [[ -z ${RDIR} ]]; then RDIR="${TOOLS}/R/R"; export RDIR; fi
if [[ -z ${R_LIBS} ]]; then R_LIBS="${TOOLS}/R/packages"; export R_LIBS; fi
if [[ -z ${USEOCTAVE} ]]; then USEOCTAVE="FALSE"; export USEOCTAVE; fi
if [[ -z ${MSMBINDIR} ]]; then MSMBINDIR="$TOOLS/MSM_HOCR_v3"; export MSMBINDIR; fi
if [[ -z ${HCPPIPEDIR} ]]; then HCPPIPEDIR="${TOOLS}/HCP/HCPpipelines"; export HCPPIPEDIR; fi
if [[ -z ${MSMCONFIGDIR} ]]; then MSMCONFIGDIR=${HCPPIPEDIR}/MSMConfig; export MSMCONFIGDIR; fi
if [[ -z ${ASLDIR} ]]; then ASLDIR="${TOOLS}/HCP/hcp-asl"; export ASLDIR; fi
if [[ -z ${PALMDIR} ]]; then PALMDIR="${TOOLS}/palm"; fi

# only outside of the container
if [ ! -f /opt/.container ]; then
    if [[ -z ${DICMNIIDIR} ]]; then DICMNIIDIR="${TOOLS}/dicm2nii/dicm2nii"; export DICMNIIDIR; fi

    # -- dicm2nii path
    export DICMNIIDIR
    MATLABPATH=$DICMNIIDIR:$MATLABPATH
    export MATLABPATH
fi

# ------------------------------------------------------------------------------
# -- QuNex bin paths
# ------------------------------------------------------------------------------
PATH=$QUNEXPATH/bin:$PATH
# -- Make sure gmri is executable and accessible
chmod ugo+x $QUNEXPATH/python/qx_utilities/gmri &> /dev/null
PATH=$QUNEXPATH/python/qx_utilities:$PATH

# ------------------------------------------------------------------------------
# -- License and version disclaimer
# ------------------------------------------------------------------------------

QuNexVer=`cat ${QUNEXPATH}/VERSION.md`

# ------------------------------------------------------------------------------
# -- Splash
# ------------------------------------------------------------------------------
qunex_splash

# ------------------------------------------------------------------------------
# -- Running matlab vs. octave
# ------------------------------------------------------------------------------

if [ "$USEOCTAVE" == "TRUE" ]; then
    # Octave needs this for some reason
    if [[ ! -e ~/.local/share ]]; then
        mkdir -p ~/.local/share
    fi
    echo "---> Setting up Octave "; echo ""
    QUNEXMCOMMAND='octave -q --eval'
    if [ ! -e ~/.octaverc ]; then
        cp ${QUNEXPATH}/qx_library/etc/.octaverc ~/.octaverc
    fi
    export LD_LIBRARY_PATH=/usr/lib64/hdf5/:${LD_LIBRARY_PATH} > /dev/null 2>&1
else
    echo "---> Setting up Matlab "; echo ""
    QUNEXMCOMMAND='matlab -nodisplay -nosplash -r'
fi
# -- Use the following command to run .m code in Matlab
export QUNEXMCOMMAND

# ------------------------------------------------------------------------------
#  path to additional libraries
# ------------------------------------------------------------------------------

LD_LIBRARY_PATH=$TOOLS/lib:$TOOLS/lib/lib:$LD_LIBRARY_PATH
LD_LIBRARY_PATH=/usr/lib64/hdf5:$LD_LIBRARY_PATH
LD_LIBRARY_PATH=$TOOLS/olib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH

PKG_CONFIG_PATH=$TOOLS/lib/lib/pkgconfig:$PKG_CONFIG_PATH
export PKG_CONFIG_PATH

PATH=$TOOLS/olib:$PATH
PATH=$TOOLS/bin:$TOOLS/lib/bin:$TOOLS/lib/lib/:$PATH
PATH=$PATH:/usr/local/bin
PATH=$PATH:/bin
export PATH

# -- add qx python to PYTHONPATH
export PYTHONPATH=$QUNEXPATH/python

# -- FSL bin dir
FSLBINDIR=${FSLDIR}/bin
FSLDIRMATLAB=${FSLDIR}/etc/matlab
FSLLIBDIR=${FSLDIR}/lib
PATH=${PATH}:${FSLBINDIR}:${FSLDIRMATLAB}:${FSLLIBDIR}
export FSLBINDIR FSLDIRMATLAB PATH
MATLABPATH=$FSLBINDIR:$FSLDIRMATLAB:$MATLABPATH
export MATLABPATH

# -- FreeSurfer path
unset FSL_DIR FSL_BIN
FREESURFER_HOME=${FREESURFERDIR}
FREESURFER_BIN=${FREESURFER_HOME}/bin
FREESURFER_MNI=${FREESURFER_HOME}/mni/bin
PATH=${FREESURFER_HOME}:${FREESURFER_BIN}:${FREESURFER_MNI}:${PATH}
LD_LIBRARY_PATH=${FREESURFER_HOME}/freesurfer/lib/tktools:${FREESURFER_HOME}/freesurfer/lib/vtk:${LD_LIBRARY_PATH}
export FREESURFER_HOME PATH LD_LIBRARY_PATH
. ${FREESURFER_HOME}/SetUpFreeSurfer.sh > /dev/null 2>&1


# -- FSL path
# -- Note: Always run after FreeSurfer for correct environment specification
#          because SetUpFreeSurfer.sh can mis-specify the $FSLDIR path

source ${FSLDIR}/etc/fslconf/fsl.sh > /dev/null 2>&1
export FSLDIR PATH
MATLABPATH=$FSLDIR:$MATLABPATH
export MATLABPATH

# -- FreeSurfer Scheduler for GPU acceleration path
FREESURFER_SCHEDULER=${FreeSurferSchedulerDIR}
PATH=${FREESURFER_SCHEDULER}:${PATH}
export FREESURFER_SCHEDULER PATH

# -- Workbench path (set OS)
if [ "$OSInfo" == "Darwin" ]; then
    WORKBENCHDIR=${HCPWBDIR}/bin_macosx64
elif [ "$OSInfo" == "Ubuntu" ] || [ "$OSInfo" == "Debian" ]; then
    WORKBENCHDIR=${HCPWBDIR}/bin_linux64
elif [ "$OSInfo" == "RedHat" ]; then
    WORKBENCHDIR=${HCPWBDIR}/bin_rh_linux64
fi
PATH=${WORKBENCHDIR}:${PATH}

# WBDIR is required for ASL pipelines
WBDIR=$WORKBENCHDIR

export WBDIR WORKBENCHDIR PATH
MATLABPATH=$WORKBENCHDIR:$MATLABPATH
export MATLABPATH

# -- PALM path
PATH=${PALMDIR}:${PATH}
export PALMDIR PATH
MATLABPATH=$PALMDIR:$MATLABPATH
export MATLABPATH

# -- AFNI path
PATH=${AFNIDIR}:${PATH}
export AFNIDIR PATH
#MATLABPATH=$AFNIDIR:$MATLABPATH
#export MATLABPATH

# -- ANTS path
PATH=${ANTSDIR}:${PATH}
export ANTSDIR PATH

# -- dcm2niix path
DCMNIIBINDIR=${DCMNIIDIR}/bin
PATH=${DCMNIIDIR}:${DCMNIIBINDIR}:${PATH}
export DCMNIIDIR PATH

# -- Octave path
OCTAVEBINDIR=${OCTAVEDIR}/bin
PATH=${OCTAVEBINDIR}:${PATH}
export OCTAVEBINDIR PATH

# -- Matlab path
MATLABBINDIR=${MATLABDIR}/bin
PATH=${MATLABBINDIR}:${PATH}
export MATLABBINDIR PATH

# -- R path
PATH=${RDIR}:${PATH}
export RDIR PATH

# QX matlablib packages
MATLABPATH=$TOOLS/matlablib/cifti-matlab.qx:$MATLABPATH
export MATLABPATH

# ------------------------------------------------------------------------------
# -- Setup overall QuNex paths
# ------------------------------------------------------------------------------

export QUNEXLIBRARY=$QUNEXPATH/qx_library
export QUNEXLIBRARYETC=$QUNEXLIBRARY/etc

HCPATLAS=$QUNEXPATH/qx_library/data/atlases/hcp
PATH=${HCPATLAS}:${PATH}
export HCPATLAS PATH
MATLABPATH=$HCPATLAS:$MATLABPATH
export MATLABPATH

TemplateFolder=$QUNEXPATH/qx_library/data/
PATH=${TemplateFolder}:${PATH}
export TemplateFolder PATH

MATLABPATH=$TemplateFolder:$MATLABPATH
export MATLABPATH

NIUTemplateFolder=$QUNEXPATH/python/qx_utilities/templates/
PATH=${NIUTemplateFolder}:${PATH}
export NIUTemplateFolder PATH

# -- useful aliases
alias qunex_env_source='source ${QUNEXPATH}/env/qunex_environment.sh'
alias qx_env_source='source ${QUNEXPATH}/env/qunex_environment.sh'

alias qunex_env_help='bash ${QUNEXPATH}/env/qunex_environment.sh --help'
alias qx_env_help='bash ${QUNEXPATH}/env/qunex_environment.sh --help'

alias qunex_env_status='source ${QUNEXPATH}/env/qunex_env_status.sh --envstatus'
alias qx_env_status='source ${QUNEXPATH}/env/qunex_env_status.sh --envstatus'

alias qunex_container_env_status=`qunex_container --env_status`

alias qunex_env_reset='source ${QUNEXPATH}/env/qunex_env_status.sh --envclear'
alias qx_env_reset='source ${QUNEXPATH}/env/qunex_env_status.sh --envclear'

# -- easy swapping between matlab and octave
qx_env_matlab() {
    # copy over precompiled matlab mex
    cp ${QUNEXPATH}/qx_library/etc/matlab_mex/img_read_nifti_mx.mex ${QUNEXPATH}/matlab/qx_mri/img/@nimage/
    cp ${QUNEXPATH}/qx_library/etc/matlab_mex/img_read_nifti_mx.mexa64 ${QUNEXPATH}/matlab/qx_mri/img/@nimage/
    cp ${QUNEXPATH}/qx_library/etc/matlab_mex/img_read_nifti_mx.mexmaci64 ${QUNEXPATH}/matlab/qx_mri/img/@nimage/
    cp ${QUNEXPATH}/qx_library/etc/matlab_mex/img_save_nifti_mx.mex ${QUNEXPATH}/matlab/qx_mri/img/@nimage/
    cp ${QUNEXPATH}/qx_library/etc/matlab_mex/img_save_nifti_mx.mexa64 ${QUNEXPATH}/matlab/qx_mri/img/@nimage/
    cp ${QUNEXPATH}/qx_library/etc/matlab_mex/img_save_nifti_mx.mexmaci64 ${QUNEXPATH}/matlab/qx_mri/img/@nimage/

    # source env
    export USEOCTAVE="FALSE"
    source ${QUNEXPATH}/env/qunex_environment.sh
}

qx_env_octave() {
    # compile octave's mex
    pushd ${QUNEXPATH}/matlab/qx_mri/img/@nimage > /dev/null
    rm *.mex*
    cp img_read_nifti_mx_octave.cpp img_read_nifti_mx.cpp
    cp img_save_nifti_mx_octave.cpp img_save_nifti_mx.cpp
    mkoctfile --mex -lz img_read_nifti_mx.cpp qx_nifti.c znzlib.c
    mkoctfile --mex -lz img_save_nifti_mx.cpp qx_nifti.c znzlib.c
    rm img_read_nifti_mx.cpp
    rm img_save_nifti_mx.cpp

    # source env
    export USEOCTAVE="TRUE"
    source ${QUNEXPATH}/env/qunex_environment.sh
    popd > /dev/null
}


# ------------------------------------------------------------------------------
# -- QuNex Extensions processing
# ------------------------------------------------------------------------------

extensions_notice_printed=FALSE
QUNEXEXTENSIONS=""
QXEXTENSIONSPY=""

# -- covert $QUNEXEXTENSIONSFOLDERS from colon separated to space
QUNEXEXTENSIONSFOLDERS=`echo $QUNEXEXTENSIONSFOLDERS | tr ':' ' '`

# -- QUNEXEXTENSIONFOLDERS is the spelling the python half used to read on its
#    own, which left a folder named in only one of them half registered. It is
#    still accepted so that an installation setting it keeps working
QUNEXEXTENSIONFOLDERS=`echo $QUNEXEXTENSIONFOLDERS | tr ':' ' '`
if [ -n "$QUNEXEXTENSIONFOLDERS" ]
then
    echo "WARNING: QUNEXEXTENSIONFOLDERS is deprecated and will be removed in a future release. Please name the extension folders in QUNEXEXTENSIONSFOLDERS instead." >&2
fi

# -- the folders named in the environment, de-duplicated so that one named in
#    both variables -- which is how an installation migrates from the old
#    spelling -- is registered once and not twice. A folder somebody named and
#    QuNex can not use is worth a line; the two fixed roots are absent on most
#    installations and are passed over in silence
QUNEXEXTENSIONSNAMED=""
for extensions_folder in $QUNEXEXTENSIONSFOLDERS $QUNEXEXTENSIONFOLDERS
do
    case " $QUNEXEXTENSIONSNAMED " in *" $extensions_folder "*) continue ;; esac

    if [ ! -d "$extensions_folder" ]
    then
        echo "WARNING: extensions folder '$extensions_folder' does not exist or is not a folder, skipping it." >&2
        continue
    fi

    QUNEXEXTENSIONSNAMED="$QUNEXEXTENSIONSNAMED $extensions_folder"
done

# -- loop through plugin folders
for extensions_folder in "$QUNEXPATH/qx_extensions" "$TOOLS/qx_extensions" $QUNEXEXTENSIONSNAMED
do
    # -- identify extensions and loop through them
    for extension in `ls -d $extensions_folder/qx_* 2> /dev/null`
    do
        # -- Notify processing
        if [ $extensions_notice_printed == 'FALSE' ]
        then
            echo "QuNex extensions identified"
            extensions_notice_printed=TRUE
        fi

        # -- Process plugin
        extension_name=`basename $extension`
        echo "---> Registering extension $extension_name"

        QUNEXEXTENSIONS="$QUNEXEXTENSIONS:$extensions_folder/$extension_name"

        # -- Register paths
        extension_root=`echo $extension_name | tr -d "_" | tr '[:lower:]' '[:upper:]'`
        echo "    ... setting ${extension_root}PATH to '$extensions_folder/$extension_name'"
        export ${extension_root}PATH="$extensions_folder/$extension_name"

        if [ -e "$extensions_folder/$extension_name/lib" ]
        then
            echo "    ... setting ${extension_root}LIB to '$extensions_folder/$extension_name/lib'"
            export ${extension_root}LIB="$extensions_folder/$extension_name/lib"
        fi

        # -- Add bin folder to PATH
        if [ -e "$extensions_folder/$extension_name/bin" ]
        then
            echo "    ... setting ${extension_root}BIN to '$extensions_folder/$extension_name/bin'"
            export ${extension_root}BIN="$extensions_folder/$extension_name/bin"
            PATH="$extensions_folder/$extension_name/bin":$PATH
            echo "    ... added $extensions_folder/$extension_name/bin to PATH"
        fi

        # -- Add python folder to QXEXTENSIONSPY
        if [ -e "$extensions_folder/$extension_name/python/qx_modules" ]
        then
            QXEXTENSIONSPY="$extensions_folder/$extension_name/python":$QXEXTENSIONSPY
            echo "    ... added $extensions_folder/$extension_name/python to QXEXTENSIONSPY"
        fi

        # -- Add matlab folder and content to MATLABPATH
        if [ -e "$extensions_folder/$extension_name/matlab" ]
        then
            MATLABPATH="$extensions_folder/$extension_name/matlab":$MATLABPATH
            echo "    ... added $extensions_folder/$extension_name/matlab to MATLABPATH"

            # -- Add subfolders if listed
            if [ -f "$extensions_folder/$extension_name/matlab/matlabpaths" ]
            then
                for matlab_folder in `cat $extensions_folder/$extension_name/matlab/matlabpaths`
                do
                    if [ -e "$extensions_folder/$extension_name/matlab/$matlab_folder" ]
                    then
                        MATLABPATH="$extensions_folder/$extension_name/matlab/$matlab_folder":$MATLABPATH
                        echo "    ... added $extensions_folder/$extension_name/matlab/$matlab_folder to MATLABPATH"
                    fi
                done
            fi
        fi
        echo ""
    done
done

export PATH MATLABPATH QUNEXEXTENSIONS QXEXTENSIONSPY

# ------------------------------------------------------------------------------
# -- Setup HCP Pipeline paths
# ------------------------------------------------------------------------------

# -- Re-Set HCP Pipeline path to different version if needed
if [ -e ~/.qxdevshare ] || [ -e ~/.qxdevind ]; then
    echo ""
    echo " ---> NOTE: You are in QuNex dev mode. Setting HCP debugging settings"
    echo ""
    # -- HCPpipelines Debugging Settings
    export HCP_DEBUG_COLOR=TRUE
    export HCP_VERBOSE=TRUE
    echo ""
fi

# -- Export HCP Pipeline and relevant variables
export PATH=${HCPPIPEDIR}:${MSMCONFIGDIR}:${PATH}; export PATH
export CARET7DIR=$WORKBENCHDIR; PATH=${CARET7DIR}:${PATH}; export PATH
export GRADUNWARPBIN=$GRADUNWARPDIR/gradunwarp/core; PATH=${GRADUNWARPBIN}:${PATH}; export PATH
export HCPPIPEDIR_Templates=${HCPPIPEDIR}/global/templates; PATH=${HCPPIPEDIR_Templates}:${PATH}; export PATH
export HCPPIPEDIR_Bin=${HCPPIPEDIR}/global/binaries; PATH=${HCPPIPEDIR_Bin}:${PATH}; export PATH
export HCPPIPEDIR_Config=${HCPPIPEDIR}/global/config; PATH=${HCPPIPEDIR_Config}:${PATH}; export PATH
export HCPPIPEDIR_PreFS=${HCPPIPEDIR}/PreFreeSurfer/scripts; PATH=${HCPPIPEDIR_PreFS}:${PATH}; export PATH
export HCPPIPEDIR_FS=${HCPPIPEDIR}/FreeSurfer/scripts; PATH=${HCPPIPEDIR_FS}:${PATH}; export PATH
export HCPPIPEDIR_FS_CUSTOM=${HCPPIPEDIR}/FreeSurfer/custom; PATH=${HCPPIPEDIR_FS_CUSTOM}:${PATH}; export PATH
export HCPPIPEDIR_PostFS=${HCPPIPEDIR}/PostFreeSurfer/scripts; PATH=${HCPPIPEDIR_PostFS}:${PATH}; export PATH
export HCPPIPEDIR_fMRISurf=${HCPPIPEDIR}/fMRISurface/scripts; PATH=${HCPPIPEDIR_fMRISurf}:${PATH}; export PATH
export HCPPIPEDIR_fMRIVol=${HCPPIPEDIR}/fMRIVolume/scripts; PATH=${HCPPIPEDIR_fMRIVol}:${PATH}; export PATH
export HCPPIPEDIR_tfMRI=${HCPPIPEDIR}/tfMRI/scripts; PATH=${HCPPIPEDIR_tfMRI}:${PATH}; export PATH
export HCPPIPEDIR_dMRI=${HCPPIPEDIR}/DiffusionPreprocessing/scripts; PATH=${HCPPIPEDIR_dMRI}:${PATH}; export PATH
export HCPPIPEDIR_Global=${HCPPIPEDIR}/global/scripts; PATH=${HCPPIPEDIR_Global}:${PATH}; export PATH
export HCPPIPEDIR_tfMRIAnalysis=${HCPPIPEDIR}/TaskfMRIAnalysis/scripts; PATH=${HCPPIPEDIR_tfMRIAnalysis}:${PATH}; export PATH
export HCPPIPEDIR_dMRITract=${QUNEXPATH}/bash/qx_utilities/diffusion_tractography/scripts; PATH=${HCPPIPEDIR_dMRITract}:${PATH}; export PATH
export HCPPIPEDIR_dMRITractFull=${QUNEXPATH}/bash/qx_utilities/diffusion_tractography_dense; PATH=${HCPPIPEDIR_dMRITractFull}:${PATH}; export PATH
export HCPPIPEDIR_dMRILegacy=${QUNEXPATH}/bash/qx_utilities; PATH=${HCPPIPEDIR_dMRILegacy}:${PATH}; export PATH
export AutoPtxFolder=${HCPPIPEDIR_dMRITractFull}/autoptx_hcp_extended; PATH=${AutoPtxFolder}:${PATH}; export PATH
export CUDIMOT_CUDA_VERSION="11.3";

# ------------------------------------------------------------------------------
# -- Setup ICA FIX paths and variables
# ------------------------------------------------------------------------------

# -- ICA FIX path
PATH=${FSL_BINDIR}:${PATH}
export FSL_BINDIR PATH
MATLABPATH=$FSL_BINDIR:$MATLABPATH
export MATLABPATH
if [ ! -z `which matlab 2>/dev/null` ]; then
    MATLABBIN=$(dirname `which matlab 2>/dev/null`)
fi
export MATLABBIN
MATLABROOT=`cd $MATLABBIN; cd ..; pwd`
export MATLABROOT

# -- Setup HCP Pipelines global matlab path relevant for FIX ICA
HCPDIRMATLAB=${HCPPIPEDIR}/global/matlab
export HCPDIRMATLAB
PATH=${HCPDIRMATLAB}:${PATH}
MATLABPATH=$HCPDIRMATLAB:$MATLABPATH
export MATLABPATH
export PATH

# -- Setup HCP Pipelines global matlab path relevant for temporal ICA
NETS_SPECTRA=${HCPDIRMATLAB}/nets_spectra
MATLABPATH=$NETS_SPECTRA:$MATLABPATH
ICA_DIM=${HCPDIRMATLAB}/icaDim
MATLABPATH=$ICA_DIM:$MATLABPATH
export MATLABPATH

# -- ciftirw
if [[ -z ${FSL_FIX_CIFTIRW} ]]; then FSL_FIX_CIFTIRW=${HCPPIPEDIR}/global/matlab; export FSL_FIX_CIFTIRW; fi
if [[ -z ${HCPCIFTIRWDIR} ]]; then HCPCIFTIRWDIR=${HCPPIPEDIR}/global/matlab/cifti-matlab; export HCPCIFTIRWDIR; fi
MATLABPATH=$FSL_FIX_CIFTIRW:$HCPCIFTIRWDIR:$MATLABPATH
export MATLABPATH

# default is interpreted MATLAB
export FSL_FIX_MATLAB_MODE=1

# if in container set compiled matlab and CUDA path
if [[ -e /opt/.container ]]; then
    # matlab runtime
    export MATLAB_COMPILER_RUNTIME=${MATLABDIR}/R2022b
    export FSL_FIX_MCRROOT=${MATLABDIR}
    export FSL_FIX_MCR=${MATLAB_COMPILER_RUNTIME}

    # use compiled inside the container
    export FSL_FIX_MATLAB_MODE=0

    # add CUDA stuff to PATH and LD_LIBRARY_PATH
    export PATH=/usr/local/cuda/bin:$PATH
    export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
fi

# -- Set and export Matlab paths
MATLABPATH=$QUNEXPATH/matlab/qx_mri/fc:$MATLABPATH
MATLABPATH=$QUNEXPATH/matlab/qx_mri/general:$MATLABPATH
MATLABPATH=$QUNEXPATH/matlab/qx_mri/img:$MATLABPATH
MATLABPATH=$QUNEXPATH/matlab/qx_mri/stats:$MATLABPATH
MATLABPATH=$QUNEXPATH/matlab/qx_utilities/general:$MATLABPATH
MATLABPATH=$QUNEXPATH/matlab/qx_mice:$MATLABPATH

# -- cudimot
export CUDIMOT=$QUNEXLIBRARY/etc/cudimot/cuda_${CUDIMOT_CUDA_VERSION}

# -- mamba management
# deactivate current
source deactivate 2> /dev/null

# set paths
MAMBADIR=${MAMBADIR}/bin
PATH=${MAMBADIR}:${PATH}
export MAMBADIR PATH

# activate
if [[ -e /opt/.container ]]; then
    eval "$(micromamba shell hook --shell bash 2>/dev/null)"
    micromamba activate /opt/env/qunex 2>/dev/null
elif [[ -d ${QUNEXENV} ]]; then
    conda activate ${QUNEXENV} 2>/dev/null
fi

# -- Set up prompt via PROMPT_COMMAND to ensure it displays in all contexts (especially Singularity)
# This is more reliable than PS1 alone for non-interactive edge cases
PROMPT_COMMAND='
if [[ -e /opt/.container ]]; then
    if [[ -n "${CONDA_DEFAULT_ENV}" ]] && [[ $(basename ${CONDA_DEFAULT_ENV}) == "qunex" ]]; then
        PS1="($(basename ${CONDA_DEFAULT_ENV}_container)) \[\e[0;36m\][\W]\$\[\e[0m\] "
    elif [[ -n "${CONDA_DEFAULT_ENV}" ]]; then
        PS1="($(basename ${CONDA_DEFAULT_ENV})) \[\e[0;36m\][\W]\$\[\e[0m\] "
    else
        PS1="\[\e[0;36m\][QuNex \W]\$\[\e[0m\] "
    fi
else
    if [[ -n "${CONDA_DEFAULT_ENV}" ]]; then
        PS1="($(basename ${CONDA_DEFAULT_ENV})) \[\e[0;36m\][${HOSTNAME%%.*} \W]\$\[\e[0m\] "
    else
        PS1="\[\e[0;36m\][QuNex \W]\$\[\e[0m\] "
    fi
fi
history -a
'

export PS1="\[\e[0;36m\][QuNex \W]\$\[\e[0m\] "
export PROMPT_COMMAND
