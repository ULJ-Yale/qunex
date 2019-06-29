#!/bin/sh
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## COPYRIGHT NOTICE
#
# Copyright (C) 2015 Anticevic Lab, Yale University
#
# ## AUTHORS(s)
#
# * Alan Anticevic, Department of Psychiatry, Yale University
# * Zailyn Tamayo, Department of Psychiatry, Yale University

#
# ## PRODUCT
#
#  BIDS_DICOM_Validate_XNATUpload.sh.sh
#
# ## LICENSE
#
# * The BIDS_DICOM_Validate_XNATUpload.sh = the "Software"
# * This Software conforms to the license outlined in the Qu|Nex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ## TODO
#
# --> Add functionality to take in all data types into the XNAT database
#
# ## DESCRIPTION 
#   
# This script, BIDS_DICOM_Validate_XNATUpload.sh, implements upload of the data to the XNAT host
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * BIDS_DICOM_Validate_XNATUpload.sh
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./BIDS_DICOM_Validate_XNATUpload.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are data stored in the following format
# * These data are stored in: "$SubjectsFolder/$CASE/
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
    echo ""
    echo "-- DESCRIPTION:"
    echo ""
    echo "This function implements validation of DICOMs and BIDS datasets for XNAT server upload via DAX code."
    echo ""
    echo "   Note: To invoke this function you will need a credential file in your home folder from filelocker_cli.conf " 
    echo ""
    echo "-- REQUIRED PARMETERS:"
    echo ""
    echo "   --filelockercliconf=<cli_credential_file_name>    Specify filelocker_cli.conf credential file name."
    echo "   --filelockerid=<file_locker_user_id>              Specify filelocker user name."
    echo "   --runtype=<specify_upload_or_download>            Select --runtype='upload' or --runtype='download' "
    echo "   --datadropfolder=<data_drop_folder>               Path to data drop on local file system"
    echo "   --inputpackages=<list_of_files_to_process>        List of files to run that are run-specific and correspond to the provided ZIPs"
    echo "   --xnatdaxcsv=<xnat_dax_project_csv>               Specify absolute path of your DAX Project CSV file"
    echo ""
    echo "-- XNAT Host Optional Parameters"
    echo ""
    echo "    --xnatchecklogin=<check_xnat_dax_login>       Specify 'yes' to run XnatCheckLogin script and setup extra hosts. If omitted, defaults are used."
    echo ""
    echo " -- Example Command:"
    echo ""
    echo "    BIDS_DICOM_Validate_XNATUpload.sh \ "
    echo "    --runtype='download' \ "
    echo "    --filelockerid='<file_locker_user_id>' \ "
    echo "    --datadropfolder='<data_drop_folder>' \ "
    echo "    --inputpackages='<list_of_files_to_process>' \ "
    echo "    --filelockercliconf='~/filelocker_cli.conf' \ "
    echo "    --xnatdaxcsv='<xnat_dax_project_csv>' \ "
    echo "    --xnatchecklogin='no' "
    echo ""
    echo ""
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

ceho() {
    echo -e "\033[36m $1 \033[0m"
}

# ------------------------------------------------------------------------------
# -- Parse and check all arguments
# ------------------------------------------------------------------------------

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

opts_CheckForHelpRequest() {
for fn in "$@" ; do
    if [ "$fn" = "--help" ]; then
        return 0
    fi
done
}

if [ $(opts_CheckForHelpRequest $@) ]; then
    showVersion
    show_usage
    exit 0
fi

# -- Initialize global output variables
unset InputPackages
unset DataDropFolder
unset XNAT_HOST_NAME
unset FILELOCKER_CREDENTIALS
unset XNAT_PROJECT_ID
unset RUN_TYPE
unset XnatCheckLoginStep
unset XNAT_DAX_PROJECT_CSV
unset FileLockerUserID

# -- Parse arguments
DataDropFolder=`opts_GetOpt "--datadropfolder" $@`
InputPackages=`opts_GetOpt "--inputpackages" "$@" | sed 's/,/ /g;s/|/ /g'`; InputPackages=`echo "$InputPackages" | sed 's/,/ /g;s/|/ /g'`
FILELOCKER_CREDENTIALS=`opts_GetOpt "--filelockercliconf" $@`
XNAT_HOST_NAME=`opts_GetOpt "--xnathost" $@`
XNAT_PROJECT_ID=`opts_GetOpt "--xnatprojectid" $@`
RUN_TYPE=`opts_GetOpt "--runtype" $@`
DownloadPath=`opts_GetOpt "--downloadpath" $@`
XnatCheckLoginStep=`opts_GetOpt "--xnatchecklogin" $@`
XNAT_DAX_PROJECT_CSV=`opts_GetOpt "--xnatdaxcsv" $@`
FileLockerUserID=`opts_GetOpt "--filelockerid" $@`

## -- Check DataDrop folder
if [[ -z ${DataDropFolder} ]]; then
    usage
    reho "ERROR: --datadropfolder flag not specified."
    echo ""
    exit 1
fi

## -- Check XNAT_DAX_PROJECT_CSV folder
if [[ -z ${XNAT_DAX_PROJECT_CSV} ]]; then
    usage
    reho "ERROR: --xnatdaxcsv file not specified."
    echo ""
    exit 1
fi

## -- Check run type
if [[ -z ${RUN_TYPE} ]]; then
    usage
    reho "ERROR: --runtype flag not specified. Specify --runtype='upload' or --runtype='download'."
    echo ""
    exit 1
fi

# -- Check for provided ZIP files
if [[ -z ${InputPackages} ]]; then
    usage
    reho "ERROR: --inputpackages flag not specified. No cases to work with. Please specify either."
    echo ""
    exit 1
fi

## -- Check for UploadPackages variables
if [[ -z ${XnatCheckLoginStep} ]]; then
    usage
    reho "Note: --xnatchecklogin flag not specified. Setting to 'no' and using DAX specified defaults."
    XnatCheckLoginStep="no"
fi

## -- Set  credentials file name to default if not provided
if [[ -z ${FILELOCKER_CREDENTIALS} ]]; then
    FILELOCKER_CREDENTIALS="~/filelocker_cli.conf"
## -- Check for valid FILELOCKER_CREDENTIALS credential file
if [ -f ${HOME}/${FILELOCKER_CREDENTIALS} ]; then
    echo ""
    ceho " -- FileLocker credentials in ${FILELOCKER_CREDENTIALS} found. Performing credential checks... "
    echo ""
    if [[ `more ${FILELOCKER_CREDENTIALS} | grep 'server_url'` ]] && [[ `more ${FILELOCKER_CREDENTIALS} | grep 'cli_key'` ]]; then
        echo ""
        ceho " -- FileLocker credentials present in ${FILELOCKER_CREDENTIALS} " 
        echo ""
        ceho " -- Proceeding with script..."
        echo ""
    fi
else
    echo ""
    reho " -- XNAT credentials in ${FILELOCKER_CREDENTIALS} NOT found. Please generate provide them using --filelockercliconf flag and re-run."
    echo ""
    exit 1
fi
fi

# -- Report all requested options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo "   DataDrop folder: ${DataDropFolder}"
    echo "   Files to process: ${InputPackages}"
    echo "   XNAT Check Login: ${XnatCheckLoginStep}"
    echo "   XNAT Run Type: ${RUN_TYPE}"
    echo "   XNAT DAX Project CSV File: ${XNAT_DAX_PROJECT_CSV}"
    echo "   FileLocker User ID: ${FileLockerUserID}"
    if [[ ${RUN_TYPE} == "download" ]]; then
        echo "   Download path: ${DownloadPath}"
    fi
    echo "-- ${scriptName}: Specified Command-Line Options - End --"
    echo ""
    geho "------------------------- Start of work --------------------------------"
echo ""

######################################### DO WORK ##########################################

main() {

############################ START OF CODE ############################

## -- Information for DAX code
##    https://xnat.vanderbilt.edu/index.php/Vanderbilt_XNAT_Tools
##    https://github.com/VUIIS/dax/wiki/XNAT-tools

## -- Setup environment for DAX
echo ""
echo " -- Checking DAX Installation"
echo ""
if [[ -z `conda list dax` ]]; then
   reho " -- DAX Installation not found. Running now..."; echo ""
   ## -- Setup conda environment
   if [[ ! -d  ~/miniconda ]]; then mkdir ~/miniconda; fi
   cd ~/miniconda/
   wget --progress=bar:force -O ~/miniconda.sh https://repo.anaconda.com/miniconda/Miniconda2-latest-Linux-x86_64.sh
   export PATH=~/miniconda/miniconda2/bin:${PATH}
   bash ~/miniconda.sh -b -p ~/miniconda/miniconda2
   if [[ ! -d  ~/env ]]; then mkdir ~/env; fi
   cd ~/env
   conda create -p ~/env/dax python=2.7
   pip install dax
   ## -- Define dax environment
   echo ""
   echo "  -- Activating DAX Environment"
   echo ""
   source activate ~/env/dax
else
    geho " -- DAX Installation OK. Checking for all requirements..."; echo ""
    ## -- Install Dax in your local environment
   if [[ `pip check dax | grep "No broken requirements found"` ]]; then
      echo ""
      geho " -- DAX installation requirements OK"; echo ""
   else 
      reho "  ERROR: DAX missing requirements. Run 'pip check dax' to install additional requirements."; echo ""
      exit 1
   fi
fi

## -- Configure XNAT initial setup of host
if [[ ${XnatCheckLoginStep} == 'yes' ]]; then
    XnatCheckLogin
fi

# Getting requested packages from file locker
echo ""
echo "  -- Unzipping requested packages..."
echo ""
if [[ ! -d  ${DataDropFolder}/FileLockerDownload ]]; then mkdir ${DataDropFolder}/FileLockerDownload; fi
cd ${DataDropFolder}/FileLockerDownload
rm filelocker_cli.log &> /dev/null
unset DirName FileName
for InputPackage in ${InputPackages}; do
    unset DirName FileName
    FileLockerCommand="python ${DataDropFolder}/filelocker.py -c ${FILELOCKER_CREDENTIALS} -a ${RUN_TYPE} -i ${InputPackage} -d ${DataDropFolder}/FileLockerDownload -u ${FileLockerUserID}"
    geho " -- Running FileLocker download:"
    geho "    ------------------------------- "
    geho "${FileLockerCommand}"
    geho "    ------------------------------- "
    echo ""
    echo ${FileLockerCommand} >> filelocker_cli.log
    eval ${FileLockerCommand}
    mv filelocker_cli.log filelocker_cli_${InputPackage}.log
    FileName=`more filelocker_cli_${InputPackage}.log | grep "Downloaded succeeded for file" | tail -1 | awk 'NF{ print $NF }'`
    # -- Unzip files
    if [[ -f ${DataDropFolder}/FileLockerDownload/${FileName} ]]; then
        echo ""
        geho "  -- File ${DataDropFolder}/FileLockerDownload/${FileName} found. Testing if valid zip..."
        echo ""
        if [[ `unzip -t ${DataDropFolder}/FileLockerDownload/${FileName} | grep "No errors detected"` ]]; then
             echo ""
             geho "  -- File ${DataDropFolder}/FileLockerDownload/${FileName} is a valid ZIP archive."
             echo ""
             echo ""
             echo " -- Unzipping requested packages..."
             echo ""
             DirName=`echo "${FileName}" | cut -d'.' -f1`
             unzip ${DataDropFolder}/FileLockerDownload/${FileName} -d ${DataDropFolder}/UnzippedData/${DirName}/
        else
             echo ""
             reho "  ERROR: File ${DataDropFolder}/FileLockerDownload/${FileName} is a NOT valid ZIP archive."
             reho "         Downloaded file ${DataDropFolder}/FileLockerDownload/*.zip does not meet upload validation criteria."
             reho "         Convention --> LastName_FirstName_Initials.zip"
             echo ""
        fi
    fi
done

# -- Run validation
echo ""
echo " -- Validating requested packages..."
echo ""

# -- To check a file to upload to XNAT
# Xnatupload -c ${XNAT_DAX_PROJECT_CSV} --report

# -- Simple upload of files to XNAT
echo ""
echo " -- Uploading requested packages to XNAT..."
echo ""
# Xnatupload -c ${XNAT_DAX_PROJECT_CSV}

}


# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@