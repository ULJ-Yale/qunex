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
#  qunex_env_status.sh
#
# ## DESCRIPTION:
#
# * This a script designed to check QuNex suite environment setup
#
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * QuNex Suite
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
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

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
 echo ""
 echo "This a script designed to report status or clear the QuNex suite environment "
 echo "variables."
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "--envstatus   Reports the status of all environment variables (also supports "
 echo "              --envreport or --environment)"
 echo "--envclear    Clears all environment variables (also supports --envreset or "
 echo "              --envpurge)"
 echo ""
}

######################################### DO WORK ##########################################

main() {

# -- Clear QuNex environment

# -- Hard reset for the environment in the container manually
     #
     #   Useful links on how to rename variables to be passe back to parent shell: 
     #   --> https://unix.stackexchange.com/questions/129084/in-bash-how-can-i-echo-the-variable-name-not-the-variable-value
     #   --> https://stackoverflow.com/questions/23564995/how-to-modify-a-global-variable-within-a-function-in-bash
     #

if [[ "$1" == "--envreset" ]] || [[ "$1" == "--envclear" ]] || [[ "$1" == "--envpurge" ]]; then
    unset $ENVVARIABLES
    echo ""
    reho " ---> Requested a hard reset of the QuNex environment! "
    echo ""
    for ENVVARIABLE in ${ENVVARIABLES}; do 
        reho " --> Unsetting ${ENVVARIABLE}"
        EnvVarName=(${!ENVVARIABLE@})
        unset $EnvVarName
        if [ -z ${ENVVARIABLE+x} ]; then 
            geho "     --> Unset successful: $ENVVARIABLE"; 
        else 
            reho "     --> $ENVVARIABLE is still set!"; 
        fi
    done
    echo ""
fi

# -- Check QuNex environment

if [[ "$1" == "--envstatus" ]] || [[ "$1" == "--envreport" ]] || [[ "$1" == "--env" ]] || [[ "$1" == "--environment" ]]; then
    echo ""
    geho "--------------------------------------------------------------"
    geho " QuNex Environment Status Report"
    geho "--------------------------------------------------------------"
    unset EnvErrorReport
    unset EnvError
    echo ""
    echo ""
    echo ""
    geho "   OS Version"
    geho "----------------------------------------------"
    echo ""
    OSVersion=$(cat /etc/os-release)
    OSVersion="${OSVersion//$'\n'/$'\n'               }"
    echo "               $OSVersion";
    echo ""
    geho "   QuNex General Environment Variables"
    geho "----------------------------------------------"
    echo ""
    echo "                 QuNexVer : $QuNexVer";             if [[ -z $QuNexVer ]]; then EnvError="yes"; EnvErrorReport="QuNexVer"; fi
    echo "                    TOOLS : $TOOLS";                if [[ -z $TOOLS ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport TOOLS"; fi
    echo "                QUNEXREPO : $QUNEXREPO";            if [[ -z $QUNEXREPO ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport QUNEXREPO"; fi
    echo "                QUNEXPATH : $QUNEXPATH";            if [[ -z $QUNEXPATH ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport QUNEXPATH"; fi
    echo "                 QUNEXENV : $QUNEXENV";             if [[ -z $QUNEXENV ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport QUNEXENV"; fi
    echo "           TemplateFolder : $TemplateFolder";       if [[ -z $TemplateFolder ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport TemplateFolder"; fi
    echo "            QUNEXMCOMMAND : $QUNEXMCOMMAND";        if [[ -z $QUNEXMCOMMAND ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport QUNEXMCOMMAND"; fi
    echo ""
    geho "   Core Dependencies Environment Variables"
    geho "----------------------------------------------"
    echo ""
    echo "                 CONDADIR : $CONDADIR";             if [[ -z $CONDADIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport CONDADIR"; fi
    echo "                   FSLDIR : $FSLDIR";               if [[ -z $FSLDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport FSLDIR"; fi
    echo "               FSLCONFDIR : $FSLCONFDIR";           if [[ -z $FSLCONFDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport FSLCONFDIR"; fi
    echo "                FSLGPUDIR : $FSLGPUDIR";            if [[ -z $FSLGPUDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport FSLGPUDIR"; fi
    echo "          FSL_GPU_SCRIPTS : $FSL_GPU_SCRIPTS";      if [[ -z $FSL_GPU_SCRIPTS ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport FSL_GPU_SCRIPTS"; fi
    echo "             FSLGPUBinary : $FSLGPUBinary";         if [[ -z $FSLGPUBinary ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport FSLGPUBinary"; fi
    echo "               FSL_FIXDIR : $FSL_FIXDIR";           if [[ -z $FSL_FIXDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport FSL_FIXDIR"; fi
    # echo "            POSTFIXICADIR : $POSTFIXICADIR";        if [[ -z $POSTFIXICADIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport POSTFIXICADIR"; fi
    echo "          FREESURFER_HOME : $FREESURFER_HOME";      if [[ -z $FREESURFER_HOME ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport FREESURFER_HOME"; fi
    echo "     FREESURFER_SCHEDULER : $FREESURFER_SCHEDULER"; if [[ -z $FREESURFER_SCHEDULER ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport FREESURFER_SCHEDULER"; fi
    echo "             WORKBENCHDIR : $WORKBENCHDIR";         if [[ -z $WORKBENCHDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport WORKBENCHDIR"; fi
    echo "                CARET7DIR : $CARET7DIR";            if [[ -z $CARET7DIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport CARET7DIR"; fi
    echo "                  AFNIDIR : $AFNIDIR";              if [[ -z $AFNIDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport AFNIDIR"; fi
    echo "                  ANTSDIR : $ANTSDIR";              if [[ -z $ANTSDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport ANTSDIR"; fi
    echo "                DCMNIIDIR : $DCMNIIDIR";            if [[ -z $DCMNIIDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport DCMNIIDIR"; fi
    echo "               DICMNIIDIR : $DICMNIIDIR";           if [[ -z $DICMNIIDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport DICMNIIDIR"; fi
    if [ "$USEOCTAVE" == "TRUE" ]; then
    echo "                OCTAVEDIR : $OCTAVEDIR";            if [[ -z $OCTAVEDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport OCTAVEDIR"; fi
    echo "             OCTAVEPKGDIR : $OCTAVEPKGDIR";         if [[ -z $OCTAVEPKGDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport OCTAVEPKGDIR"; fi
    echo "             OCTAVEBINDIR : $OCTAVEBINDIR";         if [[ -z $OCTAVEBINDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport OCTAVEBINDIR"; fi
    else
    echo "                MATLABDIR : $MATLABDIR";            if [[ -z $MATLABDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport MATLABDIR"; fi
    echo "             MATLABBINDIR : $MATLABBINDIR";         if [[ -z $MATLABBINDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport MATLABBINDIR"; fi
    fi
    echo "                     RDIR : $RDIR";                 if [[ -z $RDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport RDIR"; fi
    echo "                  PALMDIR : $PALMDIR";              if [[ -z $PALMDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport PALMDIR"; fi
    echo ""
    geho "   HCP Pipelines"
    geho "----------------------------------------------"
    echo ""
    echo "               HCPPIPEDIR : $HCPPIPEDIR";               if [[ -z $HCPPIPEDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR"; fi
    echo "            GRADUNWARPDIR : $GRADUNWARPDIR";            if [[ -z $GRADUNWARPDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport GRADUNWARPDIR"; fi
    echo "     HCPPIPEDIR_Templates : $HCPPIPEDIR_Templates";     if [[ -z $HCPPIPEDIR_Templates ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_Templates"; fi
    echo "           HCPPIPEDIR_Bin : $HCPPIPEDIR_Bin";           if [[ -z $HCPPIPEDIR_Bin ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_Bin"; fi
    echo "        HCPPIPEDIR_Config : $HCPPIPEDIR_Config";        if [[ -z $HCPPIPEDIR_Config ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_Config"; fi
    echo "         HCPPIPEDIR_PreFS : $HCPPIPEDIR_PreFS";         if [[ -z $HCPPIPEDIR_PreFS ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_PreFS"; fi
    echo "            HCPPIPEDIR_FS : $HCPPIPEDIR_FS";            if [[ -z $HCPPIPEDIR_FS ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_FS"; fi
    echo "        HCPPIPEDIR_PostFS : $HCPPIPEDIR_PostFS";        if [[ -z $HCPPIPEDIR_PostFS ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_PostFS"; fi
    echo "      HCPPIPEDIR_fMRISurf : $HCPPIPEDIR_fMRISurf";      if [[ -z $HCPPIPEDIR_fMRISurf ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_fMRISurf"; fi
    echo "       HCPPIPEDIR_fMRIVol : $HCPPIPEDIR_fMRIVol";       if [[ -z $HCPPIPEDIR_fMRIVol ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_fMRIVol"; fi
    echo "         HCPPIPEDIR_tfMRI : $HCPPIPEDIR_tfMRI";         if [[ -z $HCPPIPEDIR_tfMRI ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_tfMRI"; fi
    echo "          HCPPIPEDIR_dMRI : $HCPPIPEDIR_dMRI";          if [[ -z $HCPPIPEDIR_dMRI ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_dMRI"; fi
    echo "     HCPPIPEDIR_dMRITract : $HCPPIPEDIR_dMRITract";     if [[ -z $HCPPIPEDIR_dMRITract ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_dMRITract"; fi
    echo "        HCPPIPEDIR_Global : $HCPPIPEDIR_Global";        if [[ -z $HCPPIPEDIR_Global ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_Global"; fi
    echo " HCPPIPEDIR_tfMRIAnalysis : $HCPPIPEDIR_tfMRIAnalysis"; if [[ -z $HCPPIPEDIR_tfMRIAnalysis ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_tfMRIAnalysis"; fi
    echo "                MSMBINDIR : $MSMBINDIR";                if [[ -z $MSMBINDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport MSMBINDIR"; fi
    echo " HCPPIPEDIR_dMRITractFull : $HCPPIPEDIR_dMRITractFull";  if [[ -z $HCPPIPEDIR_dMRITractFull ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_dMRITractFull"; fi
    echo "    HCPPIPEDIR_dMRILegacy : $HCPPIPEDIR_dMRILegacy";    if [[ -z $HCPPIPEDIR_dMRILegacy ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport HCPPIPEDIR_dMRILegacy"; fi
    echo "            AutoPtxFolder : $AutoPtxFolder";            if [[ -z $AutoPtxFolder ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport AutoPtxFolder"; fi
    echo "              EDDYCUDADIR : $EDDYCUDADIR";              if [[ -z $EDDYCUDADIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport EDDYCUDADIR"; fi
    echo "                   ASLDIR : $ASLDIR";                   if [[ -z $ASLDIR ]]; then EnvError="yes"; EnvErrorReport="$EnvErrorReport ASLDIR"; fi
    echo ""
    echo ""
    geho "   Binary / Executable Locations and Versions"
    geho "----------------------------------------------"
    echo ""
    
    unset BinaryErrorReport
    unset BinaryError

    ## -- Check for HCPpipedir
    if [[ -e $HCPPIPEDIR/global/scripts/versioning/base.txt ]]; then
        # add specific TAG and commit hash
        echo "    HCPpipelines TAG : $(cat $HCPPIPEDIR/global/scripts/versioning/base.txt)"
        echo " HCPpipelines commit : $(git --git-dir ${HCPPIPEDIR}/.git log -1 --pretty=format:"%H")"
    elif [[ -e $HCPPIPEDIR/version.txt ]]; then
        # add specific TAG and commit hash
        echo "    HCPpipelines TAG : $(cat $HCPPIPEDIR/version.txt)"
        echo " HCPpipelines commit : $(git --git-dir ${HCPPIPEDIR}/.git log -1 --pretty=format:"%H")"
    else
        BinaryError="yes"; BinaryErrorReport="HCPPipelines"
        reho "        HCPpipelines : Version not found!"
        if [[ -L "$HCPPIPEDIR"  && ! -e "$HCPPIPEDIR" ]]; then
            reho "                     : $HCPPIPEDIR is a link to a nonexisiting folder!"
        fi
    fi
    echo ""

    ## -- Check for FSL
    echo "         FSL Binary  : $(which fsl 2>&1 | grep -v 'no fsl')"
    if [[ -z $(which fsl 2>&1 | grep -v 'no fsl') ]]; then 
        BinaryError="yes"; BinaryErrorReport="fsl"
        reho "         FSL Version : Binary not found!"
        if [[ -L "$FSLDIR"  && ! -e "$FSLDIR" ]]; then
            reho "                     : $FSLDIR is a link to a nonexisiting folder!"
        fi
    else
        echo "         FSL Version : $(cat $FSLDIR/etc/fslversion)"
    fi
    echo ""

    ## -- Check for FreeSurfer
    echo "  FreeSurfer Binary  : $(which freesurfer 2>&1 | grep -v 'no freesurfer')"
    if [[ -z $(which freesurfer 2>&1 | grep -v 'no freesurfer') ]]; then 
        BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport freesurfer"
        reho "  FreeSurfer Version : Binary not found!"
        if [[ -L "$FREESURFER_HOME"  && ! -e "$FREESURFER_HOME" ]]; then
            reho "                     : $FREESURFER_HOME is a link to a nonexisiting folder!"
        fi
    else
        echo "  FreeSurfer Version : $(freesurfer | tail -n 2)"
    fi
    echo ""

    ## -- Check for AFNI
    echo "        AFNI Binary  : $(which afni 2>&1 | grep -v 'no afni')"
    if [[ -z $(which afni 2>&1 | grep -v 'no afni') ]]; then 
        BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport afni"
        reho "        AFNI Version : Binary not found!"
        if [[ -L "$AFNIDIR"  && ! -e "$AFNIDIR" ]]; then
            reho "                     : $AFNIDIR is a link to a nonexisiting folder!"
        fi
    else
        echo "        AFNI Version : $(afni --version)"
    fi
    echo ""

    ## -- Check for ANTs (only very few ANTs commands support --version flag)
    echo "        ANTs Binary  : $(which antsJointFusion 2>&1 | grep -v 'no antsJointFusion')"
    if [[ -z $(which antsJointFusion 2>&1 | grep -v 'no antsJointFusion') ]]; then 
        BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport ants"
        reho "        ANTs Version : Binary not found!"
        if [[ -L "$ANTSDIR"  && ! -e "$ANTSDIR" ]]; then
            reho "                     : $ANTSDIR is a link to a nonexisiting folder!"
        fi
    else
        echo "        ANTs Version : $(antsJointFusion --version | head -1)"
    fi
    echo ""

    ## -- Check for dcm2niix
    echo "    dcm2niix Binary  : $(which dcm2niix 2>&1 | grep -v 'no dcm2niix')"
    if [[ -z $(which dcm2niix 2>&1 | grep -v 'no dcm2niix') ]]; then 
        BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport dcm2niix"
        reho "    dcm2niix Version : Binary not found!"
        if [[ -L "$DCMNIIDIR"  && ! -e "$DCMNIIDIR" ]]; then
            reho "                     : $DCMNIIDIR is a link to a nonexisiting folder!"
        fi
    else
        echo "    dcm2niix Version : $(dcm2niix -v | head -1)"
    fi
    echo ""

    ## -- Check for dicm2nii only if outside the container
    if [ ! -f /opt/.container ]; then
        echo "    dicm2nii Binary  : $DICMNIIDIR/dicm2nii.m"
        if [[ -z `ls $DICMNIIDIR/dicm2nii.m 2> /dev/null` ]]; then 
            BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport dicm2nii"
            reho "    dicm2nii Version : Executable not found!"
            if [[ -L "$DICMNIIDIR"  && ! -e "$DICMNIIDIR" ]]; then
                reho "                     : $DICMNIIDIR is a link to a nonexisiting folder!"
            fi
        else    
            echo "    dicm2nii Version : $(cat $DICMNIIDIR/README.md | grep "(version" )"
        fi
        echo ""
    fi

    ## -- Check for fix
    if [ ! -f /opt/.container ]; then
        echo "         FIX Binary  : $(which fix 2>&1 | grep -v 'no fix')"
        if [[ -z $(which fix 2>&1 | grep -v 'no fix') ]]; then 
            BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport fix"
            reho "         FIX Version : Binary not found!"
            if [[ -L "$FSL_FIXDIR"  && ! -e "$FSL_FIXDIR" ]]; then
                reho "                     : $FSL_FIXDIR is a link to a nonexisiting folder!"
            fi
        else
            echo "         FIX Version : $(fix -v | grep FMRIB)"
        fi
        echo ""
    fi

    ## -- Check for gradient_unwarp.py
    if [ ! -f /opt/.container ]; then
        echo "  Gradunwarp Binary  : $(which gradient_unwarp.py)"
        if [[ -z $(which gradient_unwarp.py) ]]; then 
            BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport gradient_unwarp.py"
            reho "  Gradunwarp Version : Binary not found!"
            if [[ -L "$GRADUNWARPDIR"  && ! -e "$GRADUNWARPDIR" ]]; then
                reho "                     : $GRADUNWARPDIR is a link to a nonexisiting folder!"
            fi
        else
            GradunwarpVersion=$((gradient_unwarp.py -v) 2>&1)
            echo "  Gradunwarp Version : $GradunwarpVersion"
        fi
        echo ""
    fi

    ## -- Check for msm
    if [ ! -f /opt/.container ]; then
        echo "         MSM Binary  : ${MSMBINDIR}/msm"
        if [[ ! -f ${MSMBINDIR}/msm ]]; then 
            BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport msm"
            reho "         MSM Version : Binary not found!"
            if [[ -L "$MSMBINDIR"  && ! -e "$MSMBINDIR" ]]; then
                reho "                     : $MSMBINDIR is a link to a nonexisiting folder!"
            fi
        else
            MSMVersion=`${MSMBINDIR}/msm 2>&1 | grep "Part"`
            echo "         MSM Version : $MSMVersion"
        fi
        echo ""
    fi

    ## -- Check for Octave
    if [ "$USEOCTAVE" == "TRUE" ]; then
        echo "      Octave Binary  : $(which octave 2>&1 | grep -v 'no octave')"
        if [[ -z $(which octave 2>&1 | grep -v 'no octave') ]]; then 
            BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport octave"
            reho "      Octave Version : Binary not found!"
            if [[ -L "$OCTAVEBINDIR"  && ! -e "$OCTAVEBINDIR" ]]; then
                reho "                     : $OCTAVEBINDIR is a link to a nonexisiting folder!"
            fi
        else
            echo "      Octave Version : $(octave -q --eval "v=version;fprintf('%s', v);")"
        fi
    else
        echo "      Matlab Binary  : $(which matlab 2>&1 | grep -v 'no matlab')"
        if [[ -z $(which matlab 2>&1 | grep -v 'no matlab') ]]; then
            BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport matlab"
            reho "      Matlab Version : Binary not found!"
            if [[ -L "$MATLABDIR"  && ! -e "$MATLABDIR" ]]; then
                reho "                     : $MATLABDIR is a link to a nonexisiting folder!"
            fi
        else
            echo "      Matlab Version : $(which matlab 2>&1 | grep -v 'no matlab')"
        fi
        # echo "     matlab : $(matlab -nodisplay -nojvm -nosplash -r "v=version;fprintf('%s', v);" | tail -1)"  
    fi
    echo ""

    ## -- Check for R
    echo "           R Binary  : $(which R 2>&1 | grep -v 'no R')"
        if [[ -z $(which R 2>&1 | grep -v 'no R') ]]; then
        BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport R"
        reho "  R Version : Binary not found!"
        if [[ -L "$RDIR"  && ! -e "$RDIR" ]]; then
            reho "                     : $RDIR is a link to a nonexisiting folder!"
        fi
    else
        echo "           R Version : $(R --version | head -1)"
    fi
    echo ""
    
    ## -- Check for R packages that are required
    unset RPackageTest RPackage
    RPackages="ggplot2"   # <-- Add R packages here
    echo " R required packages : ${RPackages}"
    for RPackage in ${RPackages}; do
        RPackageTest=`R --slave -e "tpkg <- '$RPackage'; if (is.element(tpkg, installed.packages()[,1])) {packageVersion(tpkg)} else {print('package not installed')}" | sed 's/\[1\]//g'`
        if [[ `echo ${RPackageTest} | grep 'not installed'` ]]; then 
                reho "  R Package : ${RPackage} not installed!"
        else
                echo "           R Package : ${RPackage} ${RPackageTest}"
        fi
    done
    echo ""

    ## -- Check for python
    echo "      python binary  : $(which python 2>&1 | grep -v 'no python')"
        if [[ -z $(which python 2>&1 | grep -v 'no python') ]]; then
        BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport python"
        reho "     python : Binary not found!"
    else
        echo "     python Version : $(python --version | head -1)"
    fi
    echo ""
        
    ## -- Check for PALM
    echo "        PALM Binary  : $PALMDIR/palm.m"
    if [[ -z `ls $PALMDIR/palm.m 2> /dev/null` ]]; then 
        BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport palm"
        reho "        PALM Version : Executable not found!"
        if [[ -L "$PALMDIR"  && ! -e "$PALMDIR" ]]; then
            reho "                     : $PALMDIR is a link to a nonexisiting folder!"
        fi
    else
        echo "        PALM Version : $(cat $PALMDIR/palm_version.txt)"
    fi
    echo ""

    ## -- Check for Workbench
    echo "  wb_command Binary  : $(which wb_command 2>&1 | grep -v 'no wb_command')"
        if [[ -z $(which wb_command 2>&1 | grep -v 'no wb_command') ]]; then
        BinaryError="yes"; BinaryErrorReport="$BinaryErrorReport wb_command"
        reho "  wb_command Version : Binary not found!"
        if [[ -L "$WORKBENCHDIR"  && ! -e "$WORKBENCHDIR" ]]; then
            reho "                     : $WORKBENCHDIR is a link to a nonexisiting folder!"
        fi
    else
        echo "  wb_command Version : $(wb_command | head -1)"
    fi
    echo ""

    geho "  Full Environment Paths"
    geho "----------------------------------------------"
    echo ""
    echo "  PATH : $PATH"
    echo ""
    #echo "  PYTHONPATH : $PYTHONPATH"
    #echo ""
    echo "  MATLABPATH : $MATLABPATH"
    echo ""
    
    if [[ ${EnvError} == "yes" ]]; then
        echo ""
        reho "  ERROR: The following environment variable(s) are missing: ${EnvErrorReport}"
        echo ""
    elif [[ ${BinaryError} == "yes" ]]; then
        echo ""
        reho "  ERROR: The following binaries / executables are not found: ${BinaryErrorReport}"
        echo ""
    else
        echo ""
        geho "=================== QuNex environment set successfully! ===================="
        echo ""
    fi
fi

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
