#!/bin/bash
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
# * Grega Repovs, MBLab, University of Ljubljana
# * Alan Anticevic, N3 Division, Yale University
# * Zailyn Tamayo, N3 Division, Yale University 
#
# ## PRODUCT
#
#  MNAPHCPScript.sh
#
# ## LICENSE
#
# * The MNAPHCPScript.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ### TODO
#
# --> hcp2 through hcp5 + hcpd 
#
# ## Description 
#   
# This script, MNAPHCPScript.sh runs MNAP HCP workflows within Singularity container
# 
# ## Prerequisite Installed Software
#
# * MNAP Suite Singularity Container
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. bash MNAPHCPScript.sh --help
#
# ### Expected Previous Processing
# 
#
#~ND~END~

# ------------------------------------------------------------------------------
#  Setup color outputs
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
# -- General usage
# ------------------------------------------------------------------------------

usage() {
    echo ""
    echo "  -- DESCRIPTION:"
    echo ""
    echo "  This function implements MNAP Suite HCP workflows for Singularity container use."
    echo ""
    echo ""
    echo "  --studyfolder=<study folder path>           The location of the study where results will be generated. The files will be hard-linked or copied to it."
    echo "  --subjects=<subjects to run>                List of subjects to run (comma, space or pipe separated)"
    echo "  --hcpdatapath=<data location>               Data location. It can be a folder that holds the zip or tar.gz files or the root folder where all the session folders are."
    echo "  --parameterfile=<parameter file>            The file with the parameters for the study"
    echo "  --overwrite=<overwrite hcp step>            Set to yes or no. Default is no"
    echo "  --fsldir=<path to fsl version>              Default points to FSL v5.0.9."
    echo " "
    echo "   -- Command to execute the shell script locally via MNAP:"
    echo " "
    echo "   <path to this script>/MNAPHCPScript.sh --path=<Path of the study folder> --hcpdatapath=<data location> --paramfile=<parameter file> --overwrite=<overwrite hcp step> --fsldir=<path to fsl version>"
    echo " "
    echo " " 
    exit 0
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]] || [[ $1 == "help" ]] || [[ $1 == "usage" ]]; then
    usage
fi

# ------------------------------------------------------------------------------
# -- Check for options
# ------------------------------------------------------------------------------

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

# ------------------------------------------------------------------------------
# -- Setup variables
# ------------------------------------------------------------------------------

# -- Clear variables
unset StudyFolder
unset InputDataLocation
unset ParametersFile

echo "" 
echo " -- Reading inputs... "
echo ""

# -- Define script name
scriptName=$(basename ${0})

# =-=-=-=-=-= GENERAL OPTIONS =-=-=-=-=-=
#
# -- key variables to set
StudyFolder=`opts_GetOpt "--studyfolder" $@`
CASES=`opts_GetOpt "--subjects" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "${CASES}" | sed 's/,/ /g;s/|/ /g'`
InputDataLocation=`opts_GetOpt "--hcpdatapath" $@`
ParametersFile=`opts_GetOpt "--parameterfile" $@`
Overwrite=`opts_GetOpt "--overwrite" $@`
FSLDIR=`opts_GetOpt "--fsldir" $@`


if [[ -z ${StudyFolder} ]]; then reho "  --> Error: The location of the study is missing."; exit 1; echo ''; fi
if [[ -z ${CASES} ]]; then reho "  --> Error: Subjects to run pipeline on is missing."; exit 1; echo ''; fi
if [[ -z ${InputDataLocation} ]]; then reho "  --> Error: The location of the input data is missing."; exit 1; echo ''; fi
if [[ -z ${ParametersFile} ]]; then reho "  --> Error: The parameter file input is missing."; exit 1; echo ''; fi
if [[ -z ${Overwrite} ]]; then Overwrite="no"; fi

TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
mkdir -p $StudyFolder/processing/logs &> /dev/null
LogFile="$StudyFolder/processing/logs/${scriptName}_${TimeStamp}.log"

# -- Report environment
source ${TOOLS}/${MNAPREPO}/library/environment/mnap_envStatus.sh --envstatus  >> ${LogFile}

cores=1      # the number of subjects to process in parallel
threads=5    # the number of bold files to process in parallel

# -- Derivative variables
SubjectsFolder="${StudyFolder}/subjects"
BatchFile="${StudyFolder}/processing/batch.txt"

# -- Report options
echo "-- ${scriptName}: Specified Command-Line Options - Start --"                2>&1 | tee -a ${LogFile}
echo "   "                                                                        2>&1 | tee -a ${LogFile}
echo "   "                                                                        2>&1 | tee -a ${LogFile}
echo "   MNAP Study           : $StudyFolder"                                     2>&1 | tee -a ${LogFile}
echo "   Input data location  : $InputDataLocation"                               2>&1 | tee -a ${LogFile}
echo "   Parameter file       : $ParametersFile"                                  2>&1 | tee -a ${LogFile}
echo "   Cores to use         : $cores"                                           2>&1 | tee -a ${LogFile}
echo "   Threads to use       : $threads"                                         2>&1 | tee -a ${LogFile}
echo "   MNAP subjects folder : $SubjectsFolder"                                  2>&1 | tee -a ${LogFile}
echo "   MNAP batch file      : $BatchFile"                                       2>&1 | tee -a ${LogFile}
echo "   Overwrite HCP step   : $Overwrite"                                       2>&1 | tee -a ${LogFile}
echo "   Subjects to run      : $CASES"                                           2>&1 | tee -a ${LogFile}
echo "   Log file output      : $LogFile"                                         2>&1 | tee -a ${LogFile}
echo "   MNAP software path   : $TOOLS"                                           2>&1 | tee -a ${LogFile}
echo "   MNAP path            : $TOOLS/$MNAPREPO"                                 2>&1 | tee -a ${LogFile}
echo "   FSL path             : $FSLDIR"                                          2>&1 | tee -a ${LogFile}
echo ""                                                                           2>&1 | tee -a ${LogFile}
echo "-- ${scriptName}: Specified Command-Line Options - End --"                  2>&1 | tee -a ${LogFile}
echo ""                                                                           2>&1 | tee -a ${LogFile}
echo "----------------- Start of ${scriptName} -----------------------"           2>&1 | tee -a ${LogFile}
echo "   "                                                                        2>&1 | tee -a ${LogFile}

# -- Define MNAP command
MNAPCOMMAND="bash $TOOLS/$MNAPREPO/connector/mnap.sh"

######################################### DO WORK ##########################################

main() {

    # ------------------------------------------------------------------------------
    # -- Processing steps
    # ------------------------------------------------------------------------------
    
    # -> Create a study
    ${MNAPCOMMAND} createStudy ${StudyFolder} 2>&1 | tee -a ${LogFile}
    cd ${SubjectsFolder}
    
    # -> Copy in the parameter file
    echo -e " -- Copy paramater file: ${ParametersFile} --> ${StudyFolder}/subjects/specs/batch_parameters.txt \n" 2>&1 | tee -a ${LogFile}
    cp ${ParametersFile} ${StudyFolder}/subjects/specs/batch_parameters.txt  2>&1 | tee -a ${LogFile}
    cp ${StudyFolder}/subjects/specs/batch_parameters.txt ${BatchFile}  2>&1 | tee -a ${LogFile}
    
    for CASE in ${CASES}; do
        
        # -> Import data for a specific subject
        echo -e " -- Importing data into ${StudyFolder} for ${CASE} \n" 2>&1 | tee -a ${LogFile}
        ${MNAPCOMMAND} HCPLSImport --subjectsfolder="${SubjectsFolder}" --inbox="${InputDataLocation}/${CASE}" --action="link" --overwrite="no" --archive="leave" 2>&1 | tee -a ${LogFile}
        
        # -> Get full session folder name
        SessionNames=`ls ${SubjectsFolder} | grep "${CASE}"`
        echo -e " -- Identified the following session(s) for subject ${CASE}: ${SessionNames} \n" 2>&1 | tee -a ${LogFile}

        for SessionName in ${SessionNames}; do
        
            # -> Map data to be ready for HCP processing
            echo -e " -- Running setupHCP for session ${SessionName}... \n" 2>&1 | tee -a ${LogFile}
            ${MNAPCOMMAND} setupHCP --subjectsfolder="${SubjectsFolder}" --subjects="${SessionName}" 2>&1 | tee -a ${LogFile}
            
            # -> Create a batch file with the parameters and subject's information
            echo -e " -- Running createBatch for session ${SessionName}... \n" 2>&1 | tee -a ${LogFile}
            echo "  ${MNAPCOMMAND} createBatch --subjectsfolder="${SubjectsFolder}" --subjects="${SessionName}" --overwrite="append" --tfile="${BatchFile}"   "
            ${MNAPCOMMAND} createBatch --subjectsfolder="${SubjectsFolder}" --subjects="${SessionName}" --overwrite="append" --tfile="${BatchFile}" 2>&1 | tee -a ${LogFile}
            
            # -> Run HCP proccessing on a single case
            echo -e " -- Running PreFreeSurfer on session ${SessionName}... \n" 2>&1 | tee -a ${LogFile}
            ${MNAPCOMMAND} hcp1 --subjectsfolder="${SubjectsFolder}" --subjects="${BatchFile}" --subjid="${SessionName}" --overwrite="${Overwrite}" --nprocess="0" --cores="${cores}" 2>&1 | tee -a ${LogFile}
            
            # -- Not acceptance tested
            # ${MNAPCOMMAND} hcp2 --subjectsfolder="${SubjectsFolder}" --subjects="${BatchFile}" --subjid="${SessionName}" --overwrite="${Overwrite}" --nprocess="0" --cores="${cores}" 2>&1 | tee -a ${LogFile}
            # ${MNAPCOMMAND} hcp3 --subjectsfolder="${SubjectsFolder}" --subjects="${BatchFile}" --subjid="${SessionName}" --overwrite="${Overwrite}" --nprocess="0" --cores="${cores}" 2>&1 | tee -a ${LogFile}
            # ${MNAPCOMMAND} hcp4 --subjectsfolder="${SubjectsFolder}" --subjects="${BatchFile}" --subjid="${SessionName}" --overwrite="${Overwrite}" --nprocess="0" --cores="${cores}" 2>&1 | tee -a ${LogFile}
            # ${MNAPCOMMAND} hcp5 --subjectsfolder="${SubjectsFolder}" --subjects="${BatchFile}" --subjid="${SessionName}" --overwrite="${Overwrite}" --nprocess="0" --cores="${cores}" 2>&1 | tee -a ${LogFile}
        done

    done
}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@

echo ""                                                                       2>&1 | tee -a ${LogFile}
echo "   Check log file for final outputs --> $LogFile"                       2>&1 | tee -a ${LogFile}
echo ""                                                                       2>&1 | tee -a ${LogFile}
echo "----------------- End of ${scriptName} -----------------------"         2>&1 | tee -a ${LogFile}