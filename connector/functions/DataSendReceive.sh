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
#  DataSendReceive.sh
#
# ## LICENSE
#
# * The DataSendReceive.sh = the "Software"
# * This Software conforms to the license outlined in the QuNex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# --> Add functionality to take in all data types into the XNAT database
#
# ## DESCRIPTION 
#   
# This script, DataSendReceive.sh, implements management of uploads and downloads of imaging data
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * DAX:
#        https://xnat.vanderbilt.edu/index.php/Vanderbilt_XNAT_Tools
#        https://github.com/VUIIS/dax/wiki/XNAT-tools
# 
# * FileLocker: http://filelocker2.sourceforge.net/
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./DataSendReceive.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are data stored in the following format
# * These data are stored in: "$SessionsFolder/$CASE/
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
 echo ""
 echo "DataSendReceive"
 echo ""
 echo "This function implements validation of DICOMs and BIDS datasets for uploads and"
 echo "downloads via several functions."
 echo ""
 echo "The function supports use of DAX (https://github.com/VUIIS/dax/wiki/XNAT-tools) "
 echo "and supports uploads/downloads with an XNAT system."
 echo ""
 echo "The function supports downloads via the FileLocker "
 echo "(http://filelocker2.sourceforge.net/). This allows downloads via the "
 echo "FileLocker tool onto a local file system."
 echo ""
 echo "Note: If using filelocker to invoke this function you will need a credential "
 echo "file in your home folder from filelocker_cli.conf. " 
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "--filelockercliconf   Specify filelocker_cli.conf credential file name."
 echo "--filelockerid        Specify filelocker user name."
 echo "--runtype             Specify from available --runtype options: "
 echo "" 
 echo "                      daxupload"
 echo "                         Runs upload to XNAT via DAX functions"
 echo "                      daxdownload"
 echo "                         Runs download from XNAT via DAX functions"
 echo "                      filelockerdo"
 echo "                         Runs download from FileLocker"
 echo "                      datavalidate"
 echo "                         Runs data validation for downloaded file"
 echo "" 
 echo "--datadropfolder      Path to data drop on local file system"
 echo "--inputpackages       List of files to run that are run-specific and "
 echo "                      correspond to the provided ZIPs"
 echo "--xnatdaxcsv          Specify absolute path of your DAX Project CSV file"
 echo "--xnatchecklogin      Specify 'yes' to run XnatCheckLogin script and setup " 
 echo "                      extra hosts. If omitted, defaults are used."
 echo "--xnathost            Specify the XNAT site hostname URL to push data to. "
 echo "                      (optional)"
 echo ""
 echo "EXAMPLE USE"
 echo "==========="
 echo ""
 echo "::"
 echo ""
 echo " DataSendReceive.sh \ "
 echo " --runtype='<specify_run_type>' \ "
 echo " --filelockerid='<file_locker_user_id>' \ "
 echo " --datadropfolder='<data_drop_folder>' \ "
 echo " --inputpackages='<list_of_files_to_process>' \ "
 echo " --filelockercliconf='~/filelocker_cli.conf' \ "
 echo " --xnatdaxcsv='<xnat_dax_project_csv>' \ "
 echo " --xnatchecklogin='no' "
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
unset RUN_TYPES
unset XnatCheckLoginStep
unset XNAT_DAX_PROJECT_CSV
unset FileLockerUserID

# -- Parse arguments
DataDropFolder=`opts_GetOpt "--datadropfolder" $@`
InputPackages=`opts_GetOpt "--inputpackages" "$@" | sed 's/,/ /g;s/|/ /g'`; InputPackages=`echo "$InputPackages" | sed 's/,/ /g;s/|/ /g'`
RUN_TYPES=`opts_GetOpt "--runtype" "$@" | sed 's/,/ /g;s/|/ /g'`; RUN_TYPES=`echo "$RUN_TYPES" | sed 's/,/ /g;s/|/ /g'`
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

## -- Check run type
if [[ -z ${RUN_TYPES} ]]; then
    usage
    reho "ERROR: --runtype flag not specified. Specify --runtype='upload' or --runtype='download'."
    echo ""
    exit 1
fi

## -- Check XNAT_DAX_PROJECT_CSV folder
if [[ -z ${XNAT_DAX_PROJECT_CSV} ]] && [[ ${RUN_TYPE} == 'upload' ]]; then
    usage
    reho "ERROR: --xnatdaxcsv file not specified."
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

## -- Check for XnatCheckLoginStep variables
if [[ -z ${XnatCheckLoginStep} ]]; then
    usage
    reho "Note: --xnatchecklogin flag not specified. Setting to 'no' and using DAX specified defaults."
    XnatCheckLoginStep="no"
fi

## -- Check for RUN_TYPE variables
if [[ ${RUN_TYPE} == "daxdownload" ]] || [[ ${RUN_TYPE} == "daxupload" ]]; then
    ## -- Check XNAT_HOST_NAME
    if [[ -z ${XNAT_HOST_NAME} ]]; then
        usage
        reho "ERROR: --xnathost not specified."
        echo ""
        exit 1
    fi
fi

## -- Set  credentials file name to default if not provided
if [[ -z ${FILELOCKER_CREDENTIALS} ]]; then
    FILELOCKER_CREDENTIALS="$HOME/filelocker_cli.conf"
    ## -- Check for valid FILELOCKER_CREDENTIALS credential file
    if [[ -f ${FILELOCKER_CREDENTIALS} ]]; then
        echo ""
        ceho " -- FileLocker credentials in ${FILELOCKER_CREDENTIALS} found. Performing credential checks... "
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

# -- Steps validation
SUPPORTED_RUN_TYPES="filelockerdownload datavalidate daxupload daxdownload"
echo ""
geho "--> Checking that requested ${RUN_TYPES} are supported..."
echo ""

unset FoundSupported
RUN_TYPES_CHECKS="${RUN_TYPES}"
unset TEST_RUN_STEPS
for TEST_RUN_STEP in ${RUN_TYPES_CHECKS}; do
   if [ ! -z "${SUPPORTED_RUN_TYPES##*${TEST_RUN_STEP}*}" ]; then
       echo ""
       reho "--> ${TEST_RUN_STEP} is not supported. Will remove from requested list."
       echo ""
   else
       echo ""
       geho "--> ${TEST_RUN_STEP} is supported."
       echo ""
       FoundSupported="yes"
       TEST_RUN_STEPS="${TEST_RUN_STEPS} ${TEST_RUN_STEP}"
   fi
done
if [[ -z ${FoundSupported} ]]; then 
    usage
    echo ""
    reho "ERROR: None of the requested acceptance tests are currently supported."; echo "";
    reho "Supported: ${SUPPORTED_RUN_TYPES}"; echo "";
    exit 1
else
    RUN_TYPES="${TEST_RUN_STEPS}"
    echo ""
    geho "--> Verified list of supported Turnkey steps to be run: ${RUN_TYPES}"
    echo ""
fi

# -- Report all requested options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   Run Types: ${RUN_TYPES}"
echo "   DataDrop folder: ${DataDropFolder}"
echo "   Files to process: ${InputPackages}"

for RUN_TYPE in ${RUN_TYPES}; do
    if [[ ${RUN_TYPE} == "daxdownload" ]]; then
        echo "   Download path: ${DownloadPath}"
    fi
    if [[ ${RUN_TYPE} == "flockerdownload" ]]; then
        echo "   FileLocker User ID: ${FileLockerUserID}"
    fi
    if [[ ${RUN_TYPE} == "daxdownload" ]] || [[ ${RUN_TYPE} == "daxupload" ]]; then
        echo "   XNAT Check Login: ${XnatCheckLoginStep}"
        echo "   XNAT DAX Project CSV File: ${XNAT_DAX_PROJECT_CSV}"    
        echo "   XNAT Host name: ${XNAT_HOST_NAME}"    

    fi
done

echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""

############################# DO WORK ##########################################

main() {

############################ START OF CODE #####################################

for RUN_TYPE in ${RUN_TYPES}; do

    echo ""
    echo " -- Starting work on $RUN_TYPE"
    echo ""
    
    # -- Check if flockerdownload call requested
    if [[ ${RUN_TYPE} == 'filelockerdownload' ]]; then
        # Getting requested packages from file locker
        echo ""
        echo "  -- Downloading requested packages ${InputPackages}..."
        echo ""
        if [[ ! -d  ${DataDropFolder}/FileLockerDownload ]]; then mkdir ${DataDropFolder}/FileLockerDownload; fi
        cd ${DataDropFolder}/FileLockerDownload
        rm filelocker_cli.log &> /dev/null
        unset DirName FileName
        for InputPackage in ${InputPackages}; do
            unset DirName FileName
            FileLockerCommand="python ${TOOLS}/${QUNEXREPO}/qx_library/bin/filelocker.py -c ${FILELOCKER_CREDENTIALS} -a download -i ${InputPackage} -d ${DataDropFolder}/FileLockerDownload -u ${FileLockerUserID}"
            geho " -- Running FileLocker download:"
            geho "    ------------------------------- "
            echo ""
            geho "${FileLockerCommand}"
            geho "    ------------------------------- "
            echo ""
            echo ${FileLockerCommand} >> filelocker_cli.log
            eval ${FileLockerCommand}
            mv filelocker_cli.log filelocker_cli_${InputPackage}.log
            
            FileName=`more filelocker_cli_${InputPackage}.log | grep "Downloaded succeeded for file" | tail -1 | awk 'NF{ print $NF }'`
            if [[ -z ${FileName} ]]; then
                echo ""
                reho "  ERROR: Cannot parse zip file name correctly from log."; echo ""
                exit 1
            else
                echo ""
                geho "  -- Proceeding to unzip ${FileName}..."; echo ""
            fi
            
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
    fi
    
    # -- Check if datavalidation call requested
    if [[ ${RUN_TYPE} == 'datavalidate' ]]; then
        # -- Run validation
        echo ""
        echo " -- Validating requested packages..."
        echo ""
    fi
    
    # -- Check if daxupload or daxdownload calls requested
    if [[ ${RUN_TYPE} == 'daxupload' ]] || [[ ${RUN_Function} == 'daxdownload' ]]; then
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
        fi
        if [[ ! -z `conda list dax` ]]; then
            geho " -- DAX Installation OK. Checking for all requirements..."; echo ""
            ## -- Install Dax in your local environment
            if [[ `pip check dax | grep "No broken requirements found"` ]]; then
               echo ""
               geho " -- DAX installation requirements OK"; echo ""
            else
               ## -- Define dax environment
               reho " -- DAX installation requirements not satisfied"
               echo ""
               echo "  -- Activating DAX Environment"
               echo ""
               source activate ${TOOLS}/env/dax
               if [[ `pip check dax | grep "No broken requirements found"` ]]; then
                   echo ""
                   geho " -- DAX installation requirements OK"; echo ""
               else
                   reho "  ERROR: DAX missing requirements. Re-install and run 'pip check dax' to install additional requirements."; echo ""
                   exit 1
               fi
            fi
        else
            reho "  ERROR: DAX missing requirements. Re-install and run 'pip check dax' to install additional requirements."; echo ""
            exit 1
        fi
        ## -- Configure XNAT initial setup of host
        if [[ ${XnatCheckLoginStep} == 'yes' ]]; then
            XnatCheckLogin
        fi
        ## -- Check DAX upload
        if [[ ${RUN_TYPE} == 'daxupload' ]]; then
            
            # -- Check that data is unzipped
            echo ""
            echo " -- Checking if data is zipped and unzipping ..."
            echo ""
            cd ${DataDropFolder}; find . -name *dcm.gz -exec gunzip {} \;
            
            # -- Upload of files to XNAT
            echo ""
            echo " -- Running DAX upload to XNAT: ${XNAT_HOST_NAME} .."
            echo ""
            if [[ {XNAT_UPLOAD_DAX_REPORT} == 'yes' ]]; then
                echo ""; echo " -- Setting --report flag"; echo ""
                DAXUploadCommand="Xnatupload --host ${XNAT_HOST_NAME} -c ${XNAT_DAX_PROJECT_CSV} --report"
            else
                echo ""; echo " -- Omitting --report flag"; echo ""
                DAXUploadCommand="Xnatupload --host ${XNAT_HOST_NAME} -c ${XNAT_DAX_PROJECT_CSV}"
            fi
            echo ""
            geho " -- Running DAX upload:"
            geho "    ------------------------------- "
            geho " ${DAXUploadCommand}"
            geho "    ------------------------------- "
            echo ""
            eval ${DAXUploadCommand}
        
        fi
        if [[ ${RUN_TYPE} == 'daxdownload' ]]; then
            # -- Download files out of  XNAT
            echo ""
            echo " -- Running DAX download from XNAT: ${XNAT_HOST_NAME} .."
            echo ""
            # if [[ {XNAT_UPLOAD_DAX_REPORT} == 'yes' ]]; then
            #     echo ""; echo " -- Setting --report flag"; echo ""
            #     DAXDownloadCommand="Xnatupload --host ${XNAT_HOST_NAME} -c ${XNAT_DAX_PROJECT_CSV} --report"
            # else
            #     echo ""; echo " -- Omitting --report flag"; echo ""
            #     DAXDownloadCommand="Xnatupload --host ${XNAT_HOST_NAME} -c ${XNAT_DAX_PROJECT_CSV}"
            # fi
            # echo ""
            # geho " -- Running DAX download:"
            # geho "    ------------------------------- "
            # geho "${DAXDownloadCommand}"
            # geho "    ------------------------------- "
            # echo ""
        fi
    fi
done

}

############################ END OF CODE #######################################


# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@