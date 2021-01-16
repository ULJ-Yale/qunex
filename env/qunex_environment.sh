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
# * Alan Anticevic, Department of Psychiatry, Yale University
# * Jure Demsar, University of Ljubljana
#
# ## PRODUCT
#
#  qunex_environment.sh
#
# ## LICENSE
#
# * The qunex_environment.sh = the "Software"
# * This Software conforms to the license outlined in the QuNex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ## TODO
#
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
#    source $TOOLS/qx_library/environment/qunex_environment.sh
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
 echo " source <path_to_folder_with_qunex_software>/qx_library/environment/qunex_environment.sh "
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
 echo "  TOOLS                               --> The base folder for the dependency "
 echo "  |                                       installation "
 echo "  │ "
 echo "  ├── qunex                           --> Env. Variable => QUNEXREPO -- "
 echo "  │                                       All QuNex Suite repositories "
 echo "  │                                       (https://bitbucket.org/hidradev/qunextools) "
 echo "  │ "
 echo "  ├── env                             --> conda environments with python "
 echo "  │   │                                   packages"
 echo "  │   └── qunex                       --> Env. Variable => QUNEXENV (python2.7 "
 echo "  │                                       versions of the required packages)"
 echo "  │ "
 echo "  ├── HCP                             --> Human Connectome Tools Folder "
 echo "  │   ├── Pipelines                   --> Human Connectome Pipelines Folder "
 echo "  │   │                                   (https://github.com/Washington-University/HCPpipelines)"
 echo "  │   │                                   Env. Variable => HCPPIPEDIR "
 echo "  │   ├── Pipelines-<VERSION>         --> Point any other desired version point "
 echo "  │   │                                   to HCPPIPEDIR "
 echo "  │   └── RunUtils                    --> Env. Variable => HCPPIPERUNUTILS "
 echo "  │ "
 echo "  ├── fmriprep                        --> fMRIPrep Pipelines "
 echo "  │   │                                   (https://github.com/poldracklab/fmriprep) "
 echo "  │   ├── fmriprep                    --> Env. Variable => FMRIPREPDIR "
 echo "  │   └── fmriprep-<VERSION>          --> Set any other version to FMRIPREPDIR "
 echo "  │ "
 echo "  ├── afni                            --> AFNI: Analysis of Functional"
 echo "  │   │                                   NeuroImages "
 echo "  │   │                                   (https://github.com/afni/afni) "
 echo "  │   ├── afni                        --> Env. Variable => AFNIDIR "
 echo "  │   └── afni-<VERSION>              --> Set any other version to AFNIDIR "
 echo "  │ "
 echo "  ├── dcm2niix                        --> dcm2niix conversion tool "
 echo "  │   │                                   (https://github.com/rordenlab/dcm2niix) "
 echo "  │   ├── dcm2niix                    --> Env. Variable => DCMNIIDIR "
 echo "  │   └── dcm2niix-<VERSION>          --> Set any other version to DCMNIIDIR "
 echo "  │ "
 echo "  ├── dicm2nii                        --> dicm2nii conversion tool "
 echo "  │   │                                   (https://github.com/xiangruili/dicm2nii) "
 echo "  │   ├── dicm2nii                    --> Env. Variable => DICMNIIDIR "
 echo "  │   └── dicm2nii-<VERSION>          --> Set any other version to DICMNIIDIR "
 echo "  │ "
 echo "  ├── freesurfer                      --> FreeSurfer "
 echo "  │   │                                   (http://ftp.nmr.mgh.harvard.edu/pub/dist/freesurfer/5.3.0-HCP/) "
 echo "  │   ├── freesurfer-5.3-HCP          --> Env. Variable => FREESURFER_HOME "
 echo "  │   │                                   (v5.3-HCP version for HCP-compatible "
 echo "  │   │                                   data) "
 echo "  │   ├── freesurfer-<VERSION>        --> Env. Variable => FREESURFER_HOME "
 echo "  │   │                                   (v6.0 or later stable for all other "
 echo "  │   │                                   data) "
 echo "  │   └── FreeSurferScheduler         --> Env. Variable => FreeSurferSchedulerDIR "
 echo "  │ "
 echo "  ├── fsl                             --> FSL (v5.0.9 or above with GPU-enabled "
 echo "  │   │                                   DWI tools; "
 echo "  │   │                                   https://fsl.fmrib.ox.ac.uk/fsl/fslwiki) "
 echo "  │   ├── fsl                         --> Env. Variable => FSLDIR "
 echo "  │   ├── fsl-<VERSION>               --> Set any other version to FSLDIR "
 echo "  │   ├── fix                         --> Env. Variable => FSL_FIXDIR - ICA FIX "
 echo "  │   └── fix-<VERSION>               --> Set any other version to FSL_FIXDIR "
 echo "  │                                       (https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIX/UserGuide) "
 echo "  │ "
 echo "  ├── matlab                          --> Env. Variable => MATLABDIR "
 echo "  │   │                                   Matlab vR2017b or higher. If Matlab "
 echo "  │   │                                   is installed system-wide then a "
 echo "  │   │                                   symlink is created here "
 echo "  │   └── bin                         --> Env. Variable => MATLABBINDIR "
 echo "  │ "
 echo "  ├── miniconda                       --> Env. Variable => CONDADIR "
 echo "  │                                       miniconda2 for python environment "
 echo "  │                                       management and package installation "
 echo "  │                                       (https://conda.io/projects/conda/en/latest/user-guide/install/) "
 echo "  │ "
 echo "  ├── octave                          --> Octave v.4.4.1 or higher. If Octave "
 echo "  │   │                                   is installed system-wide then a "
 echo "  │   │                                   symlink is created here "
 echo "  │   ├── octave                      --> Env. Variable => OCTAVEDIR "
 echo "  │   ├── octave/bin                  --> Env. Variable => OCTAVEBINDIR "
 echo "  │   └── octavepkg                   --> Env. Variable => OCTAVEPKGDIR -- If "
 echo "  │                                       Octave packages need manual deployment "
 echo "  │                                       then the installed packages go here "
 echo "  │ "
 echo "  ├── palm                            --> PALM: Permutation Analysis of Linear "
 echo "  │   │                                   Models "
 echo "  │   │                                   (https://github.com/andersonwinkler/PALM) "
 echo "  │   ├── palm-o                      --> Env. Variable => PALMDIR (If using "
 echo "  │   │                                   Octave) "
 echo "  │   ├── palm-m                      --> Env. Variable => PALMDIR (If using "
 echo "  │   │                                   Matlab) "
 echo "  │   └── palm-<VERSION>              --> Set any other version to PALMDIR " 
 echo "  │ "
 echo "  ├── R                               --> R Statistical computing environment"
 echo "  │   ├── packages                    --> Env. Variable => R_LIBS "
 echo "  │   └── R                           --> Env. Variable => RDIR "
 echo "  │ "
 echo "  ├── pylib                           --> Env. Variable => PYLIBDIR "
 echo "  │                                       All QuNex python libraries and tools "
 echo "  │ "
 echo "  ├── gradunwarp                      --> HCP version of gradunwarp "
 echo "  │   │                                   (https://github.com/Washington-University/gradunwarp) "
 echo "  │   ├── gradunwarp                  --> Env. Variable => GRADUNWARPDIR "
 echo "  │   └── gradunwarp-<VERSION>        --> Set any other version to GRADUNWARPDIR " 
 echo "  │ "
 echo "  └── workbench/workbench-<VERSION>   --> Connectome Workbench (v1.0 or above; "
 echo "      │                                   https://www.humanconnectome.org/software/connectome-workbench) "
 echo "      ├── workbench                   --> Env. Variable => HCPWBDIR "
 echo "      └── workbench-<VERSION>         --> Set any other version to HCPWBDIR " 
 echo ""
 echo "These defaults can be redefined if the above paths are declared as global "
 echo "variables in the .bash_profile profile after loading the QuNex environment."
 echo ""
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

ENVVARIABLES='PATH MATLABPATH PYTHONPATH QUNEXVer TOOLS QUNEXREPO QUNEXPATH TemplateFolder FSL_FIXDIR FREESURFERDIR FREESURFER_HOME FREESURFER_SCHEDULER FreeSurferSchedulerDIR WORKBENCHDIR DCMNIIDIR DICMNIIDIR MATLABDIR MATLABBINDIR OCTAVEDIR OCTAVEPKGDIR OCTAVEBINDIR RDIR HCPWBDIR AFNIDIR PYLIBDIR FSLDIR FSLGPUDIR PALMDIR QUNEXMCOMMAND HCPPIPEDIR CARET7DIR GRADUNWARPDIR HCPPIPEDIR_Templates HCPPIPEDIR_Bin HCPPIPEDIR_Config HCPPIPEDIR_PreFS HCPPIPEDIR_FS HCPPIPEDIR_PostFS HCPPIPEDIR_fMRISurf HCPPIPEDIR_fMRIVol HCPPIPEDIR_tfMRI HCPPIPEDIR_dMRI HCPPIPEDIR_dMRITract HCPPIPEDIR_Global HCPPIPEDIR_tfMRIAnalysis MSMBin HCPPIPEDIR_dMRITracFull HCPPIPEDIR_dMRILegacy AutoPtxFolder FSLGPUBinary EDDYCUDADIR USEOCTAVE QUNEXENV CONDADIR MSMBINDIR MSMCONFIGDIR R_LIBS FSL_FIX_CIFTIRW'
export ENVVARIABLES

# -- Check if inside the container and reset the environment on first setup
if [[ -e /opt/.container ]]; then
    # -- Perform initial reset for the environment in the container
    if [[ "$FIRSTRUNDONE" != "TRUE" ]]; then

        # -- First unset all conflicting variables in the environment
        echo "--> unsetting all environment variables: $ENVVARIABLES"
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
# -- Setup server login messages
# ------------------------------------------------------------------------------

HOST=`hostname`
MyID=`whoami`

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
if [[ -z ${FSL_FIXDIR} ]]; then FSL_FIXDIR="${TOOLS}/fsl/fix"; fi
if [[ -z ${FREESURFERDIR} ]]; then FREESURFERDIR="${TOOLS}/freesurfer/freesurfer-6.0"; export FREESURFERDIR; fi
if [[ -z ${FreeSurferSchedulerDIR} ]]; then FreeSurferSchedulerDIR="${TOOLS}/freesurfer/FreeSurferScheduler"; export FreeSurferSchedulerDIR; fi
if [[ -z ${HCPWBDIR} ]]; then HCPWBDIR="${TOOLS}/workbench/workbench"; export HCPWBDIR; fi
if [[ -z ${AFNIDIR} ]]; then AFNIDIR="${TOOLS}/afni/afni"; export AFNIDIR; fi
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
if [[ -z ${MSMBINDIR} ]]; then MSMBINDIR="$TOOLS/MSM_HOCR_v3/Centos"; export MSMBINDIR; fi
if [[ -z ${HCPPIPEDIR} ]]; then HCPPIPEDIR="${TOOLS}/HCP/HCPpipelines"; export HCPPIPEDIR; fi
if [[ -z ${MSMCONFIGDIR} ]]; then MSMCONFIGDIR=${HCPPIPEDIR}/MSMConfig; export MSMCONFIGDIR; fi

# -- The line below points to the environment expectation if using the 'dev' extended version of HCP Pipelines directly from QuNex repo
#if [[ -z ${HCPPIPEDIR} ]]; then HCPPIPEDIR="${TOOLS}/qunex/hcp"; export HCPPIPEDIR; fi

# -- conda management
CONDABIN=${CONDADIR}/bin
PATH=${CONDABIN}:${PATH}
export CONDABIN PATH
source deactivate 2> /dev/null

# Activate conda environment
source activate $QUNEXENV 2> /dev/null


# -- Checks for version
showVersion() {
    QuNexVer=`cat ${TOOLS}/${QUNEXREPO}/VERSION.md`
    echo ""
    geho " Loading Quantitative Neuroimaging Environment & ToolboX (QuNex) Version: v${QuNexVer}"
}

# ------------------------------------------------------------------------------
# -- License and version disclaimer
# ------------------------------------------------------------------------------

showVersion
geho ""
geho "Logged in as User: $MyID                                                    "
geho "Node info: `hostname`                                                       "
geho "OS: $OSInfo $OperatingSystem                                                "
geho ""
geho ""
geho "        ██████\                  ║      ██\   ██\                    "
geho "       ██  __██\                 ║      ███\  ██ |                   "
geho "       ██ /  ██ |██\   ██\       ║      ████\ ██ | ██████\ ██\   ██\ "
geho "       ██ |  ██ |██ |  ██ |      ║      ██ ██\██ |██  __██\\\\\██\ ██  |"
geho "       ██ |  ██ |██ |  ██ |      ║      ██ \████ |████████ |\████  / "
geho "       ██ ██\██ |██ |  ██ |      ║      ██ |\███ |██   ____|██  ██\  "
geho "       \██████ / \██████  |      ║      ██ | \██ |\███████\██  /\██\ "
geho "        \___███\  \______/       ║      \__|  \__| \_______\__/  \__|"
geho "            \___|                ║                                   "
geho ""
geho "                       DEVELOPED & MAINTAINED BY: "
geho ""                                
geho "                            Anticevic Lab                                    " 
geho "                       MBLab led by Grega Repovs                             "
geho ""
geho "                      COPYRIGHT & LICENSE NOTICE:                            "
geho ""
geho "Use of this software is subject to the terms and conditions defined by the Yale  "
geho "University Copyright Policies:"
geho "http://ocr.yale.edu/faculty/policies/yale-university-copyright-policy    "
geho "and the terms and conditions defined in the file 'LICENSE.md' which is a part of "
geho "the QuNex Suite source code package:"
geho "https://bitbucket.org/hidradev/qunextools/src/master/LICENSE.md"
geho ""

# ------------------------------------------------------------------------------
#  Check for Lmod and Load software modules -- deprecated to ensure container compatibility
# ------------------------------------------------------------------------------

# -- Check if Lmod is installed and if Matlab is available https://lmod.readthedocs.io/en/latest/index.html
#    Lmod is a Lua based module system that easily handles the MODULEPATH Hierarchical problem.
# if [[ `module -t --redirect help | grep 'Lua'` = *"Lua"* ]]; then LMODPRESENT="yes"; else LMODPRESENT="no"; fi > /dev/null 2>&1
# if [[ ${LMODPRESENT} == "yes" ]]; then
#     module load StdEnv &> /dev/null
#     # -- Check for presence of system install via Lmod
#     if [[ `module -t --redirect avail /Matlab` = *"matlab"* ]] || [[ `module -t --redirect avail /Matlab` = *"Matlab"* ]]; then LMODMATLAB="yes"; else LMODMATLAB="no"; fi > /dev/null 2>&1
#     if [[ `module -t --redirect avail /Matlab` = *"octave"* ]] || [[ `module -t --redirect avail /Octave` = *"Octave"* ]]; then LMODOCTAVE="yes"; else LMODOCTAVE="no"; fi > /dev/null 2>&1
#     # --- Matlab vs Octave
#     if [ -f ~/.qunexuseoctave ] && [[ ${LMODOCTAVE} == "yes" ]]; then
#         module load Libs/netlib &> /dev/null
#         module load Apps/Octave/4.2.1 &> /dev/null
#         echo ""; cyaneho " ---> Selected to use Octave instead of Matlab! "
#         OctaveTest="pass"
#     fi
#     if [ -f ~/.qunexuseoctave ] && [[ ${LMODOCTAVE} == "no" ]]; then
#         echo ""; reho " ===> ERROR: .qunexuseoctave set but no Octave module is present on the system."; echo ""
#         OctaveTest="fail"
#     fi
#     if [ ! -f ~/.qunexuseoctave ] && [[ ${LMODMATLAB} == "yes" ]]; then
#         module load Apps/Matlab/R2018a &> /dev/null
#         echo ""; cyaneho " ---> Selected to use Matlab!"
#         MatlabTest="pass"
#     fi
#     if [ ! -f ~/.qunexuseoctave ] && [[ ${LMODMATLAB} == "no" ]]; then
#         echo ""; reho " ===> ERROR: Matlab selected and Lmod found but Matlab module missing. Alert your SysAdmin"; echo ""
#         MatlabTest="fail"
#     fi
# fi

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
             cp ${QUNEXPATH}/qx_library/.octaverc ~/.octaverc
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
export WORKBENCHDIR PATH
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

#QUNEXCONNPATH=$QUNEXPATH/bash/qx_utilities
#PATH=${QUNEXCONNPATH}:${PATH}
#export QUNEXCONNPATH PATH
#PATH=$QUNEXPATH/bash/qx_utilities/functions:$PATH
#export QUNEXFUNCTIONS=${QUNEXCONNPATH}/functions
#MATLABPATH=$QUNEXPATH/bash/qx_utilities:$MATLABPATH
#export MATLABPATH

HCPATLAS=$QUNEXPATH/qx_library/data/atlases/HCP
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
unset QuNexSubModules
QuNexSubModules=`cd $QUNEXPATH; git submodule status | awk '{ print $2 }' | sed 's/hcpextendedpull//' | sed '/^\s*$/d'`

#alias qunex='bash ${TOOLS}/${QUNEXREPO}/bin/qunex.sh'
alias qunex_envset='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_environment.sh'
alias qunex_environment_set='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_environment.sh'

alias qunex_envhelp='bash ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_environment.sh --help'
alias qunex_environment_help='bash ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_environment.sh --help'

alias qunex_envcheck='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_envStatus.sh --envstatus'
alias qunex_envstatus='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_envStatus.sh --envstatus'
alias qunex_envreport='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_envStatus.sh --envstatus'
alias qunex_environment_check='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_envStatus.sh --envstatus'
alias qunex_environment_status='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_envStatus.sh --envstatus'
alias qunex_environment_report='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_envStatus.sh --envstatus'

alias qunex_envreset='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_envStatus.sh --envclear'
alias qunex_envclear='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_envStatus.sh --envclear'
alias qunex_envpurge='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_envStatus.sh --envclear'
alias qunex_environment_reset='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_envStatus.sh --envclear'
alias qunex_environment_clear='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_envStatus.sh --envclear'
alias qunex_environment_purge='source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_envStatus.sh --envclear'

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
export HCPPIPEDIR_dMRITract=${TOOLS}/${QUNEXREPO}/bash/qx_utilities/functions/diffusion_tractography/scripts; PATH=${HCPPIPEDIR_dMRITract}:${PATH}; export PATH
export HCPPIPEDIR_dMRITracFull=${TOOLS}/${QUNEXREPO}/bash/qx_utilities/functions/diffusion_tractography_dense; PATH=${HCPPIPEDIR_dMRITracFull}:${PATH}; export PATH
export HCPPIPEDIR_dMRILegacy=${TOOLS}/${QUNEXREPO}/bash/qx_utilities/functions; PATH=${HCPPIPEDIR_dMRILegacy}:${PATH}; export PATH
export AutoPtxFolder=${HCPPIPEDIR_dMRITracFull}/autoPtx_HCP_extended; PATH=${AutoPtxFolder}:${PATH}; export PATH
export FSLGPUBinary=${HCPPIPEDIR_dMRITracFull}/fsl_gpu_binaries; PATH=${FSLGPUBinary}:${PATH}; export PATH
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
HCPDIRMATLAB=${HCPPIPEDIR}/global/matlab/
export HCPDIRMATLAB
PATH=${HCPDIRMATLAB}:${PATH}
MATLABPATH=$HCPDIRMATLAB:$MATLABPATH
export MATLABPATH
export PATH

# -- ciftirw
if [[ -z ${FSL_FIX_CIFTIRW} ]]; then FSL_FIX_CIFTIRW=${HCPPIPEDIR}/global/matlab; export FSL_FIX_CIFTIRW; fi

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

# -- FIX ICA Dependencies Folder
# FIXDIR_DEPEND=${QUNEXPATH}/qx_library/etc/ICAFIXDependencies
# export FIXDIR_DEPEND
# PATH=${FIXDIR_DEPEND}:${PATH}
# MATLABPATH=$FIXDIR_DEPEND:$MATLABPATH
# export MATLABPATH

# -- Setup MATLAB_GIFTI_LIB relevant for FIX ICA
#MATLAB_GIFTI_LIB=$FIXDIR_DEPEND/gifti/
#export MATLAB_GIFTI_LIB
#PATH=${MATLAB_GIFTI_LIB}:${PATH}
#MATLABPATH=$MATLAB_GIFTI_LIB:$MATLABPATH
#export MATLABPATH
#export PATH
#. ${FIXDIR_DEPEND}/ICAFIX_settings.sh > /dev/null 2>&1 

# -- POST FIX ICA path
# POSTFIXICADIR=${TOOLS}/${QUNEXREPO}/hcpmodified/PostFix
# PATH=${POSTFIXICADIR}:${PATH}
# export POSTFIXICADIR PATH
# MATLABPATH=$POSTFIXICADIR:$MATLABPATH
# export MATLABPATH

# ------------------------------------------------------------------------------
# -- QuNex - python and MATLAB Paths
# ------------------------------------------------------------------------------
# --- setup PYTHONPATH and PATH When not conda

#if [ ! -e /opt/.hcppipelines ]; then 
#    PYTHONPATH=$TOOLS:$PYTHONPATH
#    PYTHONPATH=$TOOLS/pylib:$PYTHONPATH
#    PYTHONPATH=/usr/local/bin:$PYTHONPATH
#    PYTHONPATH=$TOOLS/env/qunex/bin:$PYTHONPATH
#    PYTHONPATH=$TOOLS/miniconda/pkgs:$PYTHONPATH
#    PYTHONPATH=$TOOLS/env/qunex/lib/python2.7/site-packages:$PYTHONPATH
#    PYTHONPATH=$TOOLS/env/qunex/lib/python2.7/site-packages/nibabel/xmlutils.py:$PYTHONPATH
#    PYTHONPATH=$TOOLS/env/qunex/lib/python2.7/site-packages/pydicom:$PYTHONPATH
#    PYTHONPATH=$TOOLS/env/qunex/lib/python2.7/site-packages/gradunwarp:$PYTHONPATH
#    PYTHONPATH=$TOOLS/env/qunex/lib/python2.7/site-packages/gradunwarp/core:$PYTHONPATH
#    PYTHONPATH=$QUNEXPATH:$PYTHONPATH
#    PYTHONPATH=$QUNEXPATH/bash/qx_utilities:$PYTHONPATH
#    PYTHONPATH=$QUNEXPATH/pyton/qx_utilities:$PYTHONPATH
#    PYTHONPATH=$QUNEXPATH/matlab/qx_utilities:$PYTHONPATH
#    PYTHONPATH=$PYLIBDIR/bin:$PYTHONPATH
#    PYTHONPATH=$PYLIBDIR/lib/python2.7/site-packages:$PYTHONPATH
#    PYTHONPATH=$PYLIBDIR/lib64/python2.7/site-packages:$PYTHONPATH
#    PYTHONPATH=$PYLIBDIR:$PYTHONPATH
#    PATH=$TOOLS/env/qunex/bin:$PATH
#fi

#export PATH
#export PYTHONPATH


# -- Export Python paths (before change to conda)
# PYTHONPATH=$TOOLS:$PYTHONPATH
# PYTHONPATH=$TOOLS/pylib:$PYTHONPATH
# PYTHONPATH=/usr/local/bin:$PYTHONPATH
# PYTHONPATH=/usr/local/bin/python2.7:$PYTHONPATH
# PYTHONPATH=/usr/lib/python2.7/site-packages:$PYTHONPATH
# PYTHONPATH=/usr/lib64/python2.7/site-packages:$PYTHONPATH
# PYTHONPATH=$QUNEXPATH:$PYTHONPATH
# PYTHONPATH=$QUNEXPATH/bash/qx_utilities:$PYTHONPATH
# PYTHONPATH=$QUNEXPATH/python/qx_utilities:$PYTHONPATH
# PYTHONPATH=$QUNEXPA$TH/matlab/qx_utilities:$PYTHONPATH
# PYTHONPATH=$PYLIBDIR/pydicom:$PYTHONPATH
# PYTHONPATH=$PYLIBDIR/gradunwarp:$PYTHONPATH
# PYTHONPATH=$PYLIBDIR/gradunwarp/core:$PYTHONPATH
# PYTHONPATH=$PYLIBDIR/xmlutils.py:$PYTHONPATH
# PYTHONPATH=$PYLIBDIR/bin:$PYTHONPATH
# PYTHONPATH=$PYLIBDIR/lib/python2.7/site-packages:$PYTHONPATH
# PYTHONPATH=$PYLIBDIR/lib64/python2.7/site-packages:$PYTHONPATH
# PYTHONPATH=$PYLIBDIR:$PYTHONPATH
# PYTHONPATH=$TOOLS/MeshNet:$PYTHONPATH
# export PATH
# export PYTHONPATH

# -- Set and export Matlab paths
MATLABPATH=$QUNEXPATH/matlab/qx_utilities/fcMRI:$MATLABPATH
MATLABPATH=$QUNEXPATH/matlab/qx_utilities/general:$MATLABPATH
MATLABPATH=$QUNEXPATH/matlab/qx_utilities/img:$MATLABPATH
MATLABPATH=$QUNEXPATH/matlab/qx_utilities/stats:$MATLABPATH

# ------------------------------------------------------------------------------
# -- Path to additional dependencies
# ------------------------------------------------------------------------------

# -- Define additional paths here as needed

# ------------------------------------------------------------------------------
#  QuNex Functions and git aliases for BitBucket commit and pull requests
# ------------------------------------------------------------------------------

# -- gitqunex_usage function help

gitqunex_usage() {
 echo ""
 echo "gitqunex"
 echo ""
 echo "The QuNex Suite provides functionality for users with repo privileges to "
 echo "easily pull or commit & push changes via git. This is done via two aliases that "
 echo "are setup as general environment variables: "
 echo ""
 echo "gitqunex"
 echo "     Alias for the QuNex function that updates the QuNex Suite via git from "
 echo "     the origin repo or pushes changes to origin repo."
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "--command        Specify git command: push or pull."
 echo "--add            Specify file to add with absolute path when 'push' is selected. "
 echo "                 Default []. "
 echo ""
 echo "                 Note: If 'all' is specified then will run git add on entire "
 echo "                 repo."
 echo ""
 echo "                 e.g. $TOOLS/$QUNEXREPO/bin/qunex.sh "
 echo "--branch         Specify the branch name you want to pull or commit."
 echo "--branchpath     Absolute path to folder containing QuNex suite. This folder "
 echo "                 has to have the selected branch checked out."
 echo "--message        Specify commit message if running commitqunex"
 echo "--submodules     Comma, space or pipe separated list of submodules to work on."
 echo "                 OR:"
 echo ""
 echo "                 - 'all'  ...  Update both the main repo and all submodules"
 echo "                 - 'main' ...  Update only the main repo"
 echo ""
 geho "QuNex Submodules:"
 echo ""
 geho "${QuNexSubModules}"
 echo ""
 echo ""
 echo "EXAMPLE USE"
 echo "==========="
 echo ""
 echo "::"
 echo ""
 echo " gitqunex \ "
 echo " --command='pull' \ "
 echo " --branch='master' \ "
 echo " --branchpath='$TOOLS/$QUNEXREPO' \ "
 echo " --submodules='all' "
 echo ""
 echo ""
 echo " gitqunex \ "
 echo " --command='push' \ "
 echo " --branch='master' \ "
 echo " --branchpath='$TOOLS/$QUNEXREPO' \ "
 echo " --submodules='all' \ "
 echo " --add='files_to_add' \ "
 echo " --message='Committing change' "
 echo ""
}

function_gitqunexbranch() {
    # -- Check path
    if [[ -z ${QuNexBranchPath} ]]; then
        cd $TOOLS/$QUNEXREPO
    else
        cd ${QuNexBranchPath}
    fi
    if [[ ! -z ${QuNexSubModule} ]]; then
        cd ${QuNexBranchPath}/${QuNexSubModule}
    fi
    # -- Update origin
    git remote update > /dev/null 2>&1
    QuNexDirBranchTest=`pwd`
    QuNexDirBranchCurrent=`git branch | grep '*'`
    QuNexSubModuleRepoURL=`more $TOOLS/$QUNEXREPO/.git/config | grep "url" | grep "${QuNexSubModule}" `
    echo ""
    geho "==> Running git status checks in ${QuNexDirBranchTest} \n"
    geho "        Active branch ${QuNexDirBranchCurrent}"
    geho " ${QuNexSubModuleRepoURL}"
    # -- Set git variables
    unset UPSTREAM; unset ORIGIN; unset WORKINGREPO; unset BASE
    #UPSTREAM=${1:-'@{u}'}
    ORIGIN=$(git rev-parse origin)
    WORKINGREPO=$(git rev-parse HEAD)
    BASE=$(git merge-base "$ORIGIN" "$WORKINGREPO")
    HostName=`hostname`
    if [[ `echo ${#HostName}` -lt 40 ]]; then
        SetLength=$(expr 40 - ${#HostName})
        #echo ${SetLength}
        HostName=`printf ${HostName}%+${SetLength}s`
        #echo ${#HostName}
    fi
    echo ""
    geho "    -----------------------------------------------------------------------------------------------"
    echo ""
    geho "     - Commit for origin on Bitbucket                      ${ORIGIN}"
    geho "     - Commit for ${HostName} ${WORKINGREPO}"
    geho "     - Base common ancestor commit                         ${BASE}"
    echo ""
    # -- Run a few git tests to verify WORKINGREPO, ORIGIN and BASE tips
    if [[ $ORIGIN == $WORKINGREPO ]]; then
        cyaneho "     ==> STATUS OK: ORIGIN equals `hostname` commit \n         Repo path: ${QuNexDirBranchTest}"; echo ""
    elif [[ $ORIGIN == $BASE ]] && [[ $WORKINGREPO != $BASE ]]; then
        reho "     ==> ACTION NEEDED: ORIGIN mismatches `hostname` \n         Repo path: ${QuNexDirBranchTest} \n         You need to push."; echo ""
    elif [[ $WORKINGREPO == $BASE ]] && [[ $ORIGIN != $BASE ]]; then
        reho "     ==> ACTION NEEDED: `hostname` equals BASE in ${QuNexDirBranchTest} \n         You need to pull."; echo ""
    else
        reho "     ==> ERROR: ORIGIN, BASE and `hostname` tips have diverged in ${QuNexDirBranchTest}"
        echo ""
        reho "    -----------------------------------------------------------------------------------------------"
        reho "     - Commit for origin on Bitbucket                      ${ORIGIN}"
        reho "     - Commit for ${HostName} ${WORKINGREPO}"
        reho "     - Base common ancestor commit                         ${BASE}"
        reho "    -----------------------------------------------------------------------------------------------"
        echo ""
        reho "    ==> Check 'git status -uno' to inspect and re-run after cleaning things up."
        echo ""
    fi
}
alias gitqunexbranch=function_gitqunexbranch

function_gitqunexstatus() {
    
    # -- Function for reporting git status
    function_gitstatusreport() { 
                        #GitStatusReport="$(git status -uno --porcelain | sed 's/M/Modified:/')"
                        GitStatusReport="$(git status --porcelain | sed 's/^/    /' | sed 's/M/    Modified:/' | sed 's/??/     Untracked:/' | sed 's/D/    Deleted:/')"
                        #GitStatusReport="$(echo ${GitStatusReport} | sed 's/M/-> Modified:/' | sed 's/^/    /')"
                        #GitStatusReport="$(echo ${GitStatusReport} | sed 's/??/\n    -> Untracked:/')"
                        if [[ ! -z ${GitStatusReport} ]]; then
                            echo ""
                            reho "     ==> ACTION NEEDED: The following changes need to be committed and pushed: \n"
                            reho "${GitStatusReport} \n"
                        fi
                        geho "    ----------------------------------------------------------------------------------------------"
                        echo ""; echo ""
    }

    echo ""
    geho " ================ Running QuNex Suite Repository Status Check ================"
    geho ""
    unset QuNexBranchPath; unset QuNexSubModules; unset QuNexSubModule
    
    # -- Run it for the main module
    cd ${TOOLS}/${QUNEXREPO}
    geho "  QuNex repo location: ${TOOLS}/${QUNEXREPO}"
    echo ""
    geho " =============================================================================="
    echo ""
    function_gitqunexbranch
    function_gitstatusreport
    
    # -- Then iterate over submodules
    QuNexSubModules=`cd ${TOOLS}/${QUNEXREPO}; git submodule status | awk '{ print $2 }' | sed 's/hcpextendedpull//' | sed '/^\s*$/d'`
    QuNexBranchPath="${QUNEXPATH}"
    for QuNexSubModule in ${QuNexSubModules}; do
        cd ${QuNexBranchPath}/${QuNexSubModule}
        function_gitqunexbranch
        function_gitstatusreport
    done
    cd ${TOOLS}/${QuNexREPO}
    echo ""
    geho " ================ Completed QuNex Suite Repository Status Check ================"
    echo ""
}
alias gitqunexstatus=function_gitqunexstatus

# -- function_gitqunex start

function_gitqunex() {
    unset QuNexSubModules
    QuNexSubModules=`cd $QUNEXPATH; git submodule status | awk '{ print $2 }' | sed 's/hcpextendedpull//' | sed '/^\s*$/d'`
    # -- Inputs
    unset QuNexBranch
    unset QuNexAddFiles
    unset QuNexGitCommand
    unset QuNexBranchPath
    unset CommitMessage
    unset GitStatus
    unset QuNexSubModulesList
    QuNexGitCommand=`opts_GetOpt "--command" $@`
    QuNexAddFiles=`opts_GetOpt "--add" "$@" | sed 's/,/ /g;s/|/ /g'`; QuNexSubModulesList=`echo "$QuNexSubModulesList" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes
    QuNexBranch=`opts_GetOpt "--branch" $@`
    QuNexBranchPath=`opts_GetOpt "--branchpath" $@`
    CommitMessage=`opts_GetOpt "--message" "${@}"`
    QuNexSubModulesList=`opts_GetOpt "--submodules" "$@" | sed 's/,/ /g;s/|/ /g'`; QuNexSubModulesList=`echo "$QuNexSubModulesList" | sed 's/,/ /g;s/|/ /g'` # list of input cases; removing comma or pipes

    # -- Check for help calls
    if [[ ${1} == "help" ]] || [[ ${1} == "-help" ]] || [[ ${1} == "--help" ]] || [[ ${1} == "?help" ]] || [[ -z ${1} ]]; then
        gitqunex_usage
        return 0
    fi
    if [[ ${1} == "usage" ]] || [[ ${1} == "-usage" ]] || [[ ${1} == "--usage" ]] || [[ ${1} == "?usage" ]] || [[ -z ${1} ]]; then
        gitqunex_usage
        return 0
    fi

    # -- Start execution
    echo ""
    geho "=============== Executing QuNex $QuNexGitCommand function ============== "
    # -- Performing flag checks
    echo ""
    geho "--- Checking inputs ... "
    echo ""
    if [[ -z ${QuNexGitCommand} ]]; then reho ""; reho "   Error: --command flag not defined. Specify 'pull' or 'push' option."; echo ""; gitqunex_usage; return 1; fi
    if [[ -z ${QuNexBranch} ]]; then reho ""; reho "   Error: --branch flag not defined."; echo ""; gitqunex_usage; return 1; fi
    if [[ -z ${QuNexBranchPath} ]]; then reho ""; reho "   Error: --branchpath flag for specified branch not defined. Specify absolute path of the relevant QuNex repo."; echo ""; gitqunex_usage; return 1; fi
    if [[ -z ${QuNexSubModulesList} ]]; then reho ""; reho "   Error: --submodules flag not not defined. Specify 'main', 'all' or specific submodule to commit."; echo ""; gitqunex_usage; return 1; fi
    if [[ ${QuNexSubModulesList} == "all" ]]; then reho ""; geho "   Note: --submodules flag set to all. Setting update for all submodules."; echo ""; fi
    if [[ ${QuNexSubModulesList} == "main" ]]; then reho ""; geho "   Note: --submodules flag set to main QuNex repo only in $QuNexBranchPath"; echo ""; fi
    if [[ ${QuNexGitCommand} == "push" ]]; then
        if [[ -z ${CommitMessage} ]]; then reho ""; reho "   Error: --message flag missing. Please specify commit message."; echo ""; gitqunex_usage; return 1; else CommitMessage="${CommitMessage}"; fi
        if [[ -z ${QuNexAddFiles} ]]; then reho ""; reho "   Error: --add flag not defined. Run 'gitqunexstatus' and specify which files to add."; echo ""; gitqunex_usage; return 1; fi
    fi

    # -- Perform checks that QuNex contains requested branch and that it is actively checked out
    cd ${QuNexBranchPath}
    echo ""
    mageho "  * Checking active branch for main QuNex repo in $QuNexBranchPath..."
    echo ""
    if [[ -z `git branch | grep "${QuNexBranch}"` ]]; then reho "Error: Branch $QuNexBranch does not exist in $QuNexBranchPath. Check your repo."; echo ""; gitqunex_usage; return 1; else geho "   --> $QuNexBranch found in $QuNexBranchPath"; echo ""; fi
    if [[ -z `git branch | grep "* ${QuNexBranch}"` ]]; then reho "Error: Branch $QuNexBranch is not checked out and active in $QuNexBranchPath. Check your repo."; echo ""; gitqunex_usage; return 1; else geho "   --> $QuNexBranch is active in $QuNexBranchPath"; echo ""; fi
    mageho "  * All checks for main QuNex repo passed."
    echo ""

    # -- Not perform further checks
    if [ "${QuNexSubModulesList}" == "main" ]; then
        echo ""
        geho "   Note: --submodules flag set to main QuNex repo only. Omitting individual submodules."
        echo ""
        # -- Check git command
        echo ""
        geho "--- Running QuNex git ${QuNexGitCommand} for ${QuNexBranch} on QuNex main repo in ${QuNexBranchPath}."
        echo
        cd ${QuNexBranchPath}
        # -- Run a few git tests to verify WORKINGREPO, ORIGIN and BASE tips
        function_gitqunexbranch > /dev/null 2>&1
        # -- Check git command request
        if [[ ${QuNexGitCommand} == "pull" ]]; then
            cd ${QuNexBranchPath}; git pull origin ${QuNexBranch}
        fi
        if [[ ${QuNexGitCommand} == "push" ]]; then
            cd ${QuNexBranchPath}
            if [[ $WORKINGREPO == $BASE ]] && [[ $WORKINGREPO != $ORIGIN ]]; then
                echo ""
                reho " --- ERROR: Local working repo [ $WORKINGREPO ] equals base [ $BASE ] but mismatches origin [ $ORIGIN ]. You need to pull your changes first. Run 'gitqunexstatus' and inspect changes."
                echo ""
                return 1
            else
                if [[ ${QuNexAddFiles} == "all" ]]; then
                    git add ./*
                else
                    git add ${QuNexAddFiles}
                fi
                git commit . --message="${CommitMessage}"
                git push origin ${QuNexBranch}
            fi
        fi
        function_gitqunexbranch
        echo ""
        geho "--- Completed QuNex git ${QuNexGitCommand} for ${QuNexBranch} on QuNex main repo in ${QuNexBranchPath}."; echo ""
        return 1
    fi

    # -- Check if all submodules are requested or only specific ones
    if [ ${QuNexSubModulesList} == "all" ]; then
        # -- Reset submodules variable to all
        unset QuNexSubModulesList
        QuNexSubModulesList=`cd $QUNEXPATH; git submodule status | awk '{ print $2 }' | sed 's/hcpextendedpull//' | sed '/^\s*$/d'`
        QuNexSubModules=${QuNexSubModulesList}
        if [[ ${QuNexAddFiles} != "all" ]] && [[ ${QuNexGitCommand} == "push" ]]; then
            reho "ERROR: Cannot specify all submodules and select files. Specify specific files for a given submodule or specify -add='all' "
            return 1
            gitqunex_usage
        else
            GitAddCommand="git add ./*"
        fi
    elif [ ${QuNexSubModulesList} == "main" ]; then
        echo ""
        geho "Note: --submodules flag set to the main QuNex repo."
        echo ""
        QuNexSubModules="main"
        if [[ ${QuNexAddFiles} == "all" ]] && [[ ${QuNexGitCommand} == "push" ]]; then
            GitAddCommand="git add ./*"
        else
            GitAddCommand="git add ${QuNexAddFiles}"
        fi
    elif [[ ${QuNexSubModulesList} != "main*" ]] && [[ ${QuNexSubModulesList} != "all*" ]]; then
        QuNexSubModules=${QuNexSubModulesList}
        echo ""
        geho "Note: --submodules flag set to selected QuNex repos: $QuNexSubModules"
        echo ""
        if [[ ${QuNexAddFiles} != "all" ]] && [[ ${QuNexGitCommand} == "push" ]]; then
            if [[ `echo ${QuNexSubModules} | wc -w` != 1 ]]; then 
                reho "Note: More than one submodule requested"
                reho "ERROR: Cannot specify several submodules and select specific files. Specify specific files for a given submodule or specify -add='all' "
                return 1
            fi 
            GitAddCommand="git add ${QuNexAddFiles}"
        else
            GitAddCommand="git add ./*"
        fi
    fi

    # -- Continue with specific submodules
    echo ""
    mageho "  * Checking active branch ${QuNexBranch} for specified submodules in ${QuNexBranchPath}... "
    echo ""
    for QuNexSubModule in ${QuNexSubModules}; do
        cd ${QuNexBranchPath}/${QuNexSubModule}
        if [[ -z `git branch | grep "${QuNexBranch}"` ]]; then reho "Error: Branch $QuNexBranch does not exist in $QuNexBranchPath/$QuNexSubModule. Check your repo."; echo ""; gitqunex_usage; return 1; else geho "   --> $QuNexBranch found in $QuNexBranchPath/$QuNexSubModule"; echo ""; fi
        if [[ -z `git branch | grep "* ${QuNexBranch}"` ]]; then reho "Error: Branch $QuNexBranch is not checked out and active in $QuNexBranchPath/$QuNexSubModule. Check your repo."; echo ""; gitqunex_usage; return 1; else geho "   --> $QuNexBranch is active in $QuNexBranchPath/$QuNexSubModule"; echo ""; fi
    done
    mageho "  * All checks passed for specified submodules... "
    echo ""
    # -- First run over specific modules
    for QuNexSubModule in ${QuNexSubModules}; do
        echo ""
        geho "--- Running QuNex git ${QuNexGitCommand} for ${QuNexBranch} on QuNex submodule ${QuNexBranchPath}/${QuNexSubModule}."
        echo
        cd ${QuNexBranchPath}/${QuNexSubModule}
        # -- Run a few git tests to verify WORKINGREPO, ORIGIN and BASE tips
        function_gitqunexbranch > /dev/null 2>&1
        # -- Check git command requests
        if [[ ${QuNexGitCommand} == "pull" ]]; then
            cd ${QuNexBranchPath}/${QuNexSubModule}; git pull origin ${QuNexBranch}
        fi
        if [[ ${QuNexGitCommand} == "push" ]]; then
            if [[ $WORKINGREPO == $BASE ]] && [[ $WORKINGREPO != $ORIGIN ]]; then
                echo ""
                reho " --- ERROR: Local working repo [ $WORKINGREPO ] equals BASE [ $BASE ] but mismatches origin [ $ORIGIN ]. You need to pull your changes first. Run 'gitqunexstatus' and inspect changes."
                echo ""
                return 1
            else
                cd ${QuNexBranchPath}/${QuNexSubModule}
                eval ${GitAddCommand}
                git commit . --message="${CommitMessage}"
                git push origin ${QuNexBranch}
            fi
        fi
        function_gitqunexbranch
        echo ""
        geho "--- Completed QuNex git ${QuNexGitCommand} for ${QuNexBranch} on QuNex submodule ${QuNexBranchPath}/${QuNexSubModule}."; echo ""; echo ""
    done
    unset QuNexSubModule

    # -- Finish up with the main submodule after individual modules are committed
    echo ""
    geho "--- Running QuNex git ${QuNexGitCommand} for ${QuNexBranch} on QuNex main repo in ${QuNexBranchPath}."
    echo
    cd ${QuNexBranchPath}
    function_gitqunexbranch > /dev/null 2>&1
    # -- Check git command request
    if [[ ${QuNexGitCommand} == "pull" ]]; then
        cd ${QuNexBranchPath}; git pull origin ${QuNexBranch}
    fi
    if [[ ${QuNexGitCommand} == "push" ]]; then
        cd ${QuNexBranchPath}
            if [[ $WORKINGREPO == $BASE ]] && [[ $WORKINGREPO != $ORIGIN ]]; then
            echo ""
                reho " --- ERROR: Local working repo [ $WORKINGREPO ] equals base [ $BASE ] but mismatches origin [ $ORIGIN ]. You need to pull your changes first. Run 'gitqunexstatus' and inspect changes."
            echo ""
            return 1
        else
            git add ./*
            git commit . --message="${CommitMessage}"
            git push origin ${QuNexBranch}
        fi
    fi
    function_gitqunexbranch
    echo ""
    geho "--- Completed QuNex git ${QuNexGitCommand} for ${QuNexBranch} on QuNex main repo in ${QuNexBranchPath}."; echo ""

    # -- Report final completion
    echo ""
    geho "=============== Completed QuNex $QuNexGitCommand function ============== "
    echo ""

    # -- Reset submodules variable
    unset QuNexSubModules
    QuNexSubModules=`cd $QUNEXPATH; git submodule status | awk '{ print $2 }' | sed 's/hcpextendedpull//' | sed '/^\s*$/d'`
    unset QuNexBranch
    unset QuNexGitCommand
    unset QuNexBranchPath
    unset CommitMessage
    unset GitStatus
    unset QuNexSubModulesList
    unset QuNexSubModule
}

# -- define function_gitqunex alias
alias gitqunex=function_gitqunex

# ------------------------------------------------------------------------------
# -- Module setup if using a cluster
# ------------------------------------------------------------------------------

# # -- Load additional needed modules
# if [[ ${LMODPRESENT} == "yes" ]]; then
#     LoadModules="Libs/netlib Libs/QT/5.6.2 Apps/R Rpkgs/RCURL/1.95 Langs/Python/2.7.14 Tools/GIT/2.6.2 Tools/Mercurial/3.6 GPU/Cuda/7.5 Rpkgs/GGPLOT2 Libs/SCIPY/0.13.3 Libs/PYDICOM/0.9.9 Libs/NIBABEL/2.0.1 Libs/MATPLOTLIB/1.4.3 Libs/AWS/1.11.66 Libs/NetCDF/4.3.3.1-parallel-intel2013 Libs/NUMPY/1.9.2 Langs/Lua/5.3.3"
#     echo ""; cyaneho " ---> LMOD present. Loading Modules..."
#     for LoadModule in ${LoadModules}; do
#         module load ${LoadModule} &> /dev/null
#     done
#     echo ""; cyaneho " ---> Loaded Modules:  ${LoadModules}"; echo ""
# fi

# ------------------------------------------------------------------------------
# -- Setup CUDA
# ------------------------------------------------------------------------------

# set default version to 9.1
NVCCVer="9.1"

# check other versions
if [[ ! -z `command -v nvcc` ]]; then
    if [[ `nvcc --version | grep "release"` == *"7.5"* ]]; then NVCCVer="7.5"; fi
    if [[ `nvcc --version | grep "release"` == *"8.0"* ]]; then NVCCVer="8.0"; fi
fi

# set variables
BedpostXGPUDir="bedpostx_gpu_cuda_${NVCCVer}" 
ProbTrackXDIR="${FSLGPUBinary}/probtrackx_gpu_cuda_${NVCCVer}"
bindir=${FSLGPUBinary}/${BedpostXGPUDir}/bedpostx_gpu
export BedpostXGPUDir; export ProbTrackXDIR; export bindir; PATH=${bindir}:${PATH}; PATH=${bindir}/lib:${PATH}; PATH=${bindir}/bin:${PATH}; PATH=${ProbTrackXDIR}:${PATH}; export PATH
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${bindir}/lib


QuNexEnvCheck=`source ${TOOLS}/${QUNEXREPO}/qx_library/environment/qunex_envStatus.sh --envstatus | grep "ERROR"` > /dev/null 2>&1
if [[ -z ${QuNexEnvCheck} ]]; then
    geho " ---> QuNex environment set successfully!"
    echo ""
else
    reho "   --> ERROR in QuNex environment. Run 'qunex_envstatus' to check missing variables!"
    echo ""
fi

# ------------------------------------------------------------------------------
# -- QuNex Source & Docker Pull and Build Function Aliases 
# ------------------------------------------------------------------------------

# -- Build and push Docker container to Docker.io: $1 ==> build,push $2 ==> tag (e.g. qunex/qunex_suite:0_45_07
qxdocker_function_build_push() { 
    cd $TOOLS/qunexcontainer
    ./containerRegistryWorkflow.sh --commands="$1" --versiontag="$2" --registry="docker.io" --localcontainerfile="$TOOLS/qunexcontainer/Dockerfile_qunex_suite"
}
alias qxdocker_build_push='qxdocker_function_build_push'

# -- Run Docker container with a given tag
qxdocker_function_run() { 
    docker container run -it --rm qunex/qunex_suite:$1 bash 
}
alias qxdocker_run='qxdocker_function_run'

# -- Pull Docker container with a given tag
qxdocker_function_pull() { 
    docker pull qunex/qunex_suite:"$1"
}
alias qxdocker_pull='qxdocker_function_pull'

# -- Pull all QuNex source across all submodules
qxsource_function_pull_all() {
    gitqunex --command="pull" --branch="master" --branchpath="$TOOLS/qunex" --submodules="all"
}
alias qxsource_pull_all='qxsource_function_pull_all'

# -- Commit-Push all QuNex source across all submodules with any message passed as string
qxsource_function_commit_push_all() {
    gitqunex --command='push' --add='all' --branch='master' --branchpath="$TOOLS/qunex" --submodules='all' --message="$*"
}
alias qxsource_commit_push_all='qxsource_function_commit_push_all'

