#!/bin/sh
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
# -- Setup color outputs
# ------------------------------------------------------------------------------

BLACK_F="\033[30m"; BLACK_B="\033[40m"
RED_F="\033[31m"; RED_B="\033[41m"
GREEN_F="\033[32m"; GREEN_B="\033[42m"
YELLOW_F="\033[33m"; YELLOW_B="\033[43m"
BLUE_F="\033[34m"; BLUE_B="\033[44m"
MAGENTA_F="\033[35m"; MAGENTA_B="\033[45m"
CYAN_F="\033[36m"; CYAN_B="\033[46m"
WHITE_F="\033[37m"; WHITE_B="\033[47m"

reho() {
    echo -e "$RED_F$1 \033[0m"
}
geho() {
    echo -e "$GREEN_F$1 \033[0m"
}
yeho() {
    echo -e "$YELLOW_F$1 \033[0m"
}
beho() {
    echo -e "$BLUE_F$1 \033[0m"
}
mageho() {
    echo -e "$MAGENTA_F$1 \033[0m"
}
cyaneho() {
    echo -e "$CYAN_F$1 \033[0m"
}
weho() {
    echo -e "$WHITE_F$1 \033[0m"
}

# -- Set general options functions
opts_GetOpt() {
sopt="$1"
shift 1
for fn in "$@" ; do
    if [ `echo ${fn} | grep -- "^${sopt}=" | wc -w` -gt 0 ]; then
        echo "${fn}" | sed "s/^${sopt}=//"
        return 0
    fi
done
}

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
 echo ""
 echo "This script implements the global environment setup for the QuNex Suite."
 echo ""
 echo "Configure the environment script by adding the following lines to the "
 echo ".bash_profile::"
 echo ""
 echo " TOOLS=<path_to_folder_with_qunex_software> "
 echo " export TOOLS "
 echo " source <path_to_folder_with_qunex_software>/env/qunex_environment.sh "
 echo ""
 echo "Permissions of this file need to be set to 770."
 echo ""
 echo "REQUIRED DEPENDENCIES"
 echo "====================="
 echo ""
 echo "The QuNex Suite assumes a set default folder names for dependencies if "
 echo "undefined by user environment. These are defined relative to the "
 echo "${TOOLS} folder which should be set as a global system variable."
 echo ""
 echo "For details about required dependencies consult the QuNex documentation."
 geho "**For full environment report run 'qunex environment'.**"
 echo ""
 exit 0
}

if [ "$1" == "--help" ] || [ "$1" == "-help" ] || [ "$1" == "help" ] || [ "$1" == "?help" ] || [ "$1" == "--usage" ] || [ "$1" == "-usage" ] || [ "$1" == "usage" ] || [ "$1" == "?usage" ]; then
    usage
fi

# ------------------------------------------------------------------------------
#  Environment clear and check functions
# ------------------------------------------------------------------------------

ENVVARIABLES='PATH MATLABPATH PYTHONPATH QUNEXVer TOOLS QUNEXREPO QUNEXPATH QUNEXLIBRARY QUNEXLIBRARYETC TemplateFolder FSL_FIXDIR FREESURFERDIR FREESURFER_HOME FREESURFER_SCHEDULER FreeSurferSchedulerDIR WORKBENCHDIR DCMNIIDIR DICMNIIDIR MATLABDIR MATLABBINDIR OCTAVEDIR OCTAVEPKGDIR OCTAVEBINDIR RDIR HCPWBDIR AFNIDIR PYLIBDIR FSLDIR FSLGPUDIR PALMDIR QUNEXMCOMMAND HCPPIPEDIR CARET7DIR GRADUNWARPDIR HCPPIPEDIR_Templates HCPPIPEDIR_Bin HCPPIPEDIR_Config HCPPIPEDIR_PreFS HCPPIPEDIR_FS HCPPIPEDIR_PostFS HCPPIPEDIR_fMRISurf HCPPIPEDIR_fMRIVol HCPPIPEDIR_tfMRI HCPPIPEDIR_dMRI HCPPIPEDIR_dMRITract HCPPIPEDIR_Global HCPPIPEDIR_tfMRIAnalysis HCPCIFTIRWDIR MSMBin HCPPIPEDIR_dMRITractFull HCPPIPEDIR_dMRILegacy AutoPtxFolder FSLGPUScripts FSLGPUBinary EDDYCUDADIR USEOCTAVE QUNEXENV CONDADIR MSMBINDIR MSMCONFIGDIR R_LIBS FSL_FIX_CIFTIRW FSFAST_HOME SUBJECTS_DIR MINC_BIN_DIR MNI_DIR MINC_LIB_DIR MNI_DATAPATH FSF_OUTPUT_FORMAT'
export ENVVARIABLES

# -- Check if inside the container and reset the environment on first setup
if [[ -e /opt/.container ]]; then
    # -- Perform initial reset for the environment in the container
    if [[ "$FIRSTRUNDONE" != "TRUE" ]]; then

        # -- First unset all conflicting variables in the environment
        echo "--> unsetting the following environment variables: $ENVVARIABLES"
        unset $ENVVARIABLES

        # -- Set PATH
        export PATH=/usr/local/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

        # -- Check for specific settings a user might want:

        # --- This is a file that should reside in a user's home folder and it should contain the settings the user wants to make that are different from the defaults.
        if [ -f ~/.qunex_container.rc ]; then
            echo "--> sourcing  ~/.qunex_container.rc"
            . ~/.qunex_container.rc
        fi

        # --- This is an environmental variable that if set should hold a path to a bash script that contains the settings the user wants to make that are different from the defaults.
        if [[ ! -z "$QUNEXCONTAINERENV" ]]; then    
            echo "--> QUNEXCONTAINERENV set: sourcing $QUNEXCONTAINERENV"
            . $QUNEXCONTAINERENV
        fi

        # --- Check for presence of set con_<VariableName>. If present <VariableName> is set to con_<VariableName>

        for ENVVAR in $ENVVARIABLES
        do
            if [[ ! -z $(eval echo "\${con_$ENVVAR+x}") ]]; then
                echo "--> setting $ENVVAR to value of con_$ENVVAR [$(eval echo \"\$con_$ENVVAR\")]"
                export $ENVVAR="$(eval echo \"\$con_$ENVVAR\")"
            fi
        done

        if [ -z ${TOOLS+x} ]; then TOOLS="/opt"; fi
        if [ -z ${USEOCTAVE+x} ]; then USEOCTAVE="TRUE"; fi

        PATH=${TOOLS}:${PATH}
        export TOOLS PATH USEOCTAVE
        export FIRSTRUNDONE="TRUE"
    fi

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
    reho " -- ERROR: TOOLS environment variable not setup on this system."
    reho "    Please add to your environment profile (e.g. .bash_profile):"
    echo ""
    echo "    TOOLS=/<absolute_path_to_software_folder>/"
    reho 1
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
QuNexVer=`cat ${TOOLS}/${QUNEXREPO}/VERSION.md`
export QUNEXPATH QUNEXREPO QuNexVer

if [ -e ~/qunexinit.sh ]; then
    echo ""
    reho " --- NOTE: QuNex is set by your ~/qunexinit.sh file! ----"
    echo ""
    reho " ---> QuNex path is set to: ${QUNEXPATH} "
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
if [[ -z ${FSL_FIXDIR} ]]; then FSL_FIXDIR="${TOOLS}/fsl/fix"; fi
if [[ -z ${FREESURFERDIR} ]]; then FREESURFERDIR="${TOOLS}/freesurfer/freesurfer-6.0"; export FREESURFERDIR; fi
if [[ -z ${FreeSurferSchedulerDIR} ]]; then FreeSurferSchedulerDIR="${TOOLS}/freesurfer/FreeSurferScheduler"; export FreeSurferSchedulerDIR; fi
if [[ -z ${HCPWBDIR} ]]; then HCPWBDIR="${TOOLS}/workbench/workbench"; export HCPWBDIR; fi
if [[ -z ${AFNIDIR} ]]; then AFNIDIR="${TOOLS}/AFNI/AFNI"; export AFNIDIR; fi
if [[ -z ${ANTSDIR} ]]; then ANTSDIR="${TOOLS}/ANTs/ANTs/bin"; export ANTSDIR; fi
if [[ -z ${DCMNIIDIR} ]]; then DCMNIIDIR="${TOOLS}/dcm2niix/dcm2niix"; export DCMNIIDIR; fi
if [[ -z ${DICMNIIDIR} ]]; then DICMNIIDIR="${TOOLS}/dicm2nii/dicm2nii"; export DICMNIIDIR; fi
if [[ -z ${OCTAVEDIR} ]]; then OCTAVEDIR="${TOOLS}/octave/octave"; export OCTAVEDIR; fi
if [[ -z ${OCTAVEPKGDIR} ]]; then OCTAVEPKGDIR="${TOOLS}/octave/octavepkg"; export OCTAVEPKGDIR; fi
if [[ -z ${PYLIBDIR} ]]; then PYLIBDIR="${TOOLS}/pylib"; export PYLIBDIR; fi
if [[ -z ${FMRIPREPDIR} ]]; then FMRIPREPDIR="${TOOLS}/fmriprep/fmriprep"; export FMRIPREPDIR; fi
if [[ -z ${MATLABDIR} ]]; then MATLABDIR="${TOOLS}/matlab"; export MATLABDIR; fi
if [[ -z ${GRADUNWARPDIR} ]]; then GRADUNWARPDIR="${TOOLS}/gradunwarp/gradunwarp"; export GRADUNWARPDIR; fi
if [[ -z ${QUNEXENV} ]]; then QUNEXENV="${TOOLS}/env/qunex"; export QUNEXENV; fi
if [[ -z ${CONDADIR} ]]; then CONDADIR="${TOOLS}/miniconda"; export CONDADIR; fi
if [[ -z ${RDIR} ]]; then RDIR="${TOOLS}/R/R"; export RDIR; fi
if [[ -z ${R_LIBS} ]]; then R_LIBS="${TOOLS}/R/packages"; export R_LIBS; fi
if [[ -z ${USEOCTAVE} ]]; then USEOCTAVE="FALSE"; export USEOCTAVE; fi
if [[ -z ${MSMBINDIR} ]]; then MSMBINDIR="$TOOLS/MSM_HOCR_v3"; export MSMBINDIR; fi
if [[ -z ${HCPPIPEDIR} ]]; then HCPPIPEDIR="${TOOLS}/HCP/HCPpipelines"; export HCPPIPEDIR; fi
if [[ -z ${MSMCONFIGDIR} ]]; then MSMCONFIGDIR=${HCPPIPEDIR}/MSMConfig; export MSMCONFIGDIR; fi
if [[ -z ${ASLDIR} ]]; then ASLDIR="${HCPPIPEDIR}/hcp-asl"; export ASLDIR; fi

# -- The line below points to the environment expectation if using the 'dev' extended version of HCP Pipelines directly from QuNex repo
#if [[ -z ${HCPPIPEDIR} ]]; then HCPPIPEDIR="${TOOLS}/qunex/hcp"; export HCPPIPEDIR; fi

# -- conda management
CONDABIN=${CONDADIR}/bin
PATH=${CONDABIN}:${PATH}
export CONDABIN PATH
source deactivate 2> /dev/null

# Activate conda environment
source activate $QUNEXENV 2> /dev/null

# ------------------------------------------------------------------------------
# -- License and version disclaimer
# ------------------------------------------------------------------------------

QuNexVer=`cat ${TOOLS}/${QUNEXREPO}/VERSION.md`

# ------------------------------------------------------------------------------
# -- Setup server login messages
# ------------------------------------------------------------------------------
geho ""
geho "Generated by QuNex"
geho "------------------------------------------------------------------------"
geho "Version: $QuNexVer"
geho "User: `whoami`"
geho "System: `hostname`"
geho "OS: $OSInfo $OperatingSystem"
geho "------------------------------------------------------------------------"
geho ""
geho "        ██████\                  ║      ██\   ██\                       "
geho "       ██  __██\                 ║      ███\  ██ |                      "
geho "       ██ /  ██ |██\   ██\       ║      ████\ ██ | ██████\ ██\   ██\    "
geho "       ██ |  ██ |██ |  ██ |      ║      ██ ██\██ |██  __██\\\\\██\ ██  |"
geho "       ██ |  ██ |██ |  ██ |      ║      ██ \████ |████████ |\████  /    "
geho "       ██ ██\██ |██ |  ██ |      ║      ██ |\███ |██   ____|██  ██\     "
geho "       \██████ / \██████  |      ║      ██ | \██ |\███████\██  /\██\    "
geho "        \___███\  \______/       ║      \__|  \__| \_______\__/  \__|   "
geho "            \___|                ║                                      "
geho ""
geho ""
geho "                       DEVELOPED & MAINTAINED BY:"
geho ""
geho "                    Anticevic Lab, Yale University"
geho "               Mind & Brain Lab, University of Ljubljana"
geho "                     Murray Lab, Yale University"
geho ""
geho "                      COPYRIGHT & LICENSE NOTICE:"
geho ""
geho "Use of this software is subject to the terms and conditions defined in"
geho "'LICENSE.md' which is a part of the QuNex Suite source code package:"
geho "https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md"
geho ""

# ------------------------------------------------------------------------------
# -- Running matlab vs. octave
# ------------------------------------------------------------------------------

if [ "$USEOCTAVE" == "TRUE" ]; then
    if [[ ${OctaveTest} == "fail" ]]; then 
        reho " ===> ERROR: Cannot setup Octave because module test failed."
    else
         ln -s `which octave` ${OCTAVEDIR}/octave > /dev/null 2>&1
         export OCTAVEPKGDIR
         export OCTAVEDIR
         export OCTAVEBINDIR
         cyaneho " ---> Setting up Octave "; echo ""
         QUNEXMCOMMAND='octave -q --no-init-file --eval'
         if [ ! -e ~/.octaverc ]; then
             cp ${QUNEXPATH}/qx_library/etc/.octaverc ~/.octaverc
         fi
         export LD_LIBRARY_PATH=/usr/lib64/hdf5/:${LD_LIBRARY_PATH} > /dev/null 2>&1
         if [[ -z ${PALMDIR} ]]; then PALMDIR="${TOOLS}/palm/palm-o"; fi
    fi
else
    # if [[ ${MatlabTest} == "fail" ]]; then
    #     reho " ===> ERROR: Cannot setup Matlab because module test failed."
    # else
         
         cyaneho " ---> Setting up Matlab "; echo ""
         QUNEXMCOMMAND='matlab -nodisplay -nosplash -r'
         if [[ -z ${PALMDIR} ]]; then PALMDIR="${TOOLS}/palm/palm-m"; fi
    # fi
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

# -- Make sure gmri is executable and accessible
chmod ugo+x $QUNEXPATH/python/qx_utilities/gmri &> /dev/null
PATH=$QUNEXPATH/python/qx_utilities:$PATH

PATH=$TOOLS/olib:$PATH
PATH=$TOOLS/bin:$TOOLS/lib/bin:$TOOLS/lib/lib/:$PATH
PATH=$QUNEXPATH/bin:$PATH
PATH=$QUNEXPATH/lib:$PATH
PATH=/usr/local/bin:$PATH
PATH=$PATH:/bin
#PATH=$QUNEXPATH/qx_library/bin:$PATH
#PATH=$QUNEXPATH/bash/qx_utilities:$PATH
#PATH=$QUNEXPATH/matlab/qx_utilities:$PATH
#PATH=$PYLIBDIR/gradunwarp:$PATH
#PATH=$PYLIBDIR/gradunwarp/core:$PATH
#PATH=$PYLIBDIR/xmlutils.py:$PATH
#PATH=$PYLIBDIR:$PATH
#PATH=$PYLIBDIR/bin:$PATH
#PATH=$TOOLS/MeshNet:$PATH
export PATH

# -- FSL probtrackx2_gpu command path
FSLGPUDIR=${FSLDIR}/bin
PATH=${FSLGPUDIR}:${PATH}
export FSLGPUDIR PATH
MATLABPATH=$FSLGPUDIR:$MATLABPATH
export MATLABPATH

# -- FreeSurfer path
unset FSL_DIR
FREESURFER_HOME=${FREESURFERDIR}
PATH=${FREESURFER_HOME}:${PATH}
export FREESURFER_HOME PATH
. ${FREESURFER_HOME}/SetUpFreeSurfer.sh > /dev/null 2>&1

# -- FSL path
# -- Note: Always run after FreeSurfer for correct environment specification
#          because SetUpFreeSurfer.sh can mis-specify the $FSLDIR path

PATH=${FSLDIR}/bin:${PATH}
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
DCMNIIBINDIR=${DCMNIIDIR}/build/bin
PATH=${DCMNIIDIR}:${DCMNIIBINDIR}:${PATH}
export DCMNIIDIR PATH

# -- dicm2nii path
export DICMNIIDIR PATH
MATLABPATH=$DICMNIIDIR:$MATLABPATH
export MATLABPATH

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

# -- Define submodules, but omit hcpextendedpull to avoid conflicts
alias qunex_envset='source ${TOOLS}/${QUNEXREPO}/env/qunex_environment.sh'
alias qx_envset='source ${TOOLS}/${QUNEXREPO}/env/qunex_environment.sh'
alias qunex_environment_set='source ${TOOLS}/${QUNEXREPO}/env/qunex_environment.sh'
alias qx_environment_set='source ${TOOLS}/${QUNEXREPO}/env/qunex_environment.sh'

alias qunex_envhelp='bash ${TOOLS}/${QUNEXREPO}/env/qunex_environment.sh --help'
alias qx_envhelp='bash ${TOOLS}/${QUNEXREPO}/env/qunex_environment.sh --help'
alias qunex_environment_help='bash ${TOOLS}/${QUNEXREPO}/env/qunex_environment.sh --help'
alias qx_environment_help='bash ${TOOLS}/${QUNEXREPO}/env/qunex_environment.sh --help'

alias qunex_env_status='source ${TOOLS}/${QUNEXREPO}/env/qunex_env_status.sh --envstatus'
alias qx_env_status='source ${TOOLS}/${QUNEXREPO}/env/qunex_env_status.sh --envstatus'
alias qunex_envstatus='source ${TOOLS}/${QUNEXREPO}/env/qunex_env_status.sh --envstatus'
alias qx_envstatus='source ${TOOLS}/${QUNEXREPO}/env/qunex_env_status.sh --envstatus'
alias qunex_environment_status='source ${TOOLS}/${QUNEXREPO}/env/qunex_env_status.sh --envstatus'
alias qx_environment_status='source ${TOOLS}/${QUNEXREPO}/env/qunex_env_status.sh'

alias qunex_container_env_status=`qunex_container --env_status`
alias qunex_container_envstatus=`qunex_container --env_status`

alias qunex_envreset='source ${TOOLS}/${QUNEXREPO}/env/qunex_env_status.sh --envclear'
alias qx_envreset='source ${TOOLS}/${QUNEXREPO}/env/qunex_env_status.sh --envclear'
alias qunex_environment_reset='source ${TOOLS}/${QUNEXREPO}/env/qunex_env_status.sh --envclear'
alias qx_environment_reset='source ${TOOLS}/${QUNEXREPO}/env/qunex_env_status.sh --envclear'

# ------------------------------------------------------------------------------
# -- Setup HCP Pipeline paths
# ------------------------------------------------------------------------------

# -- Re-Set HCP Pipeline path to different version if needed 
if [ -e ~/.qxdevshare ] || [ -e ~/.qxdevind ]; then
    echo ""
    geho " ==> NOTE: You are in QuNex dev mode. Setting HCP debugging settings"
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
export HCPPIPEDIR_PostFS=${HCPPIPEDIR}/PostFreeSurfer/scripts; PATH=${HCPPIPEDIR_PostFS}:${PATH}; export PATH
export HCPPIPEDIR_fMRISurf=${HCPPIPEDIR}/fMRISurface/scripts; PATH=${HCPPIPEDIR_fMRISurf}:${PATH}; export PATH
export HCPPIPEDIR_fMRIVol=${HCPPIPEDIR}/fMRIVolume/scripts; PATH=${HCPPIPEDIR_fMRIVol}:${PATH}; export PATH
export HCPPIPEDIR_tfMRI=${HCPPIPEDIR}/tfMRI/scripts; PATH=${HCPPIPEDIR_tfMRI}:${PATH}; export PATH
export HCPPIPEDIR_dMRI=${HCPPIPEDIR}/DiffusionPreprocessing/scripts; PATH=${HCPPIPEDIR_dMRI}:${PATH}; export PATH
export HCPPIPEDIR_Global=${HCPPIPEDIR}/global/scripts; PATH=${HCPPIPEDIR_Global}:${PATH}; export PATH
export HCPPIPEDIR_tfMRIAnalysis=${HCPPIPEDIR}/TaskfMRIAnalysis/scripts; PATH=${HCPPIPEDIR_tfMRIAnalysis}:${PATH}; export PATH
export HCPPIPEDIR_dMRITract=${TOOLS}/${QUNEXREPO}/bash/qx_utilities/diffusion_tractography/scripts; PATH=${HCPPIPEDIR_dMRITract}:${PATH}; export PATH
export HCPPIPEDIR_dMRITractFull=${TOOLS}/${QUNEXREPO}/bash/qx_utilities/diffusion_tractography_dense; PATH=${HCPPIPEDIR_dMRITractFull}:${PATH}; export PATH
export HCPPIPEDIR_dMRILegacy=${TOOLS}/${QUNEXREPO}/bash/qx_utilities; PATH=${HCPPIPEDIR_dMRILegacy}:${PATH}; export PATH
export AutoPtxFolder=${HCPPIPEDIR_dMRITractFull}/autoptx_hcp_extended; PATH=${AutoPtxFolder}:${PATH}; export PATH
export FSLGPUScripts=${HCPPIPEDIR_dMRITractFull}/fsl_gpu; PATH=${FSLGPUScripts}:${PATH}; export PATH
export FSLGPUBinary=${QUNEXLIBRARYETC}/fsl_gpu_binaries; PATH=${FSLGPUBinary}:${PATH}; export PATH
export DefaultCUDAVersion="9.1";
export EDDYCUDADIR=${FSLGPUBinary}/eddy_cuda; PATH=${EDDYCUDADIR}:${PATH}; export PATH; eddy_cuda="eddy_cuda_wQC"; export eddy_cuda


# ------------------------------------------------------------------------------
# -- Setup ICA FIX paths and variables
# ------------------------------------------------------------------------------

# -- ICA FIX path
PATH=${FSL_FIXDIR}:${PATH}
export FSL_FIXDIR PATH
MATLABPATH=$FSL_FIXDIR:$MATLABPATH
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

# if in container set compiled matlab and CUDA path
if [[ -e /opt/.container ]]; then
    # matlab runtime
    export MATLAB_COMPILER_RUNTIME=${MATLABDIR}/v93
    export FSL_FIX_MCRROOT=${MATLABDIR}
    export LD_LIBRARY_PATH=/opt/matlab/v93/runtime/glnxa64:/opt/matlab/v93/bin/glnxa64:/opt/matlab/v93/sys/os/glnxa64:${LD_LIBRARY_PATH}

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
