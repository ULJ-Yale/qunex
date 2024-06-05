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
#  qunex_container.sh
#
# ## Description 
#   
# This script, qunex_container.sh runs QuNex  container 
#  pointing to code that executes the environment and calls the final code 
#  that should be executed inside the container
# 
# ## Prerequisite Installed Software
#
# * QuNex Suite Docker or Apptainer Container
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. bash qunex_container.sh --help
#
# ### Expected Previous Processing
# 
#
#~ND~END~

usage() {
 echo ""
 echo "This function implements the initialization of the QuNex container execution for "
 echo "Docker or Apptainer."
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "--container   Specifies either the path to the Apptainer container image or"
 echo "              the full specification of the Docker container to be used (e.g. "
 echo "              qunex/qunex_suite:0_45_07). This parameter can be omitted if the "
 echo "              value is specified in the `QUNEXCONIMAGE` environmental variable. "
 echo "--script      If a script is to be run agains the Apptainer container rather "
 echo "              than a single command, the path to the script to be run is "
 echo "              specified here. [''] "
 echo "--string      String to execute the QuNex call."
 echo ""
 echo "PARAMETERS FOR I/O"
 echo "------------------"
 echo ""
 echo "--inputfolder    Path to study folder"
 echo "--outputfolder   Path to output folder"
 echo "--specfolder     Path to folder with spec files (parameters.txt and hcp_mapping.txt). "
 echo "                 Not required if spec files are inside inputfolder or "
 echo "                 outputfolder. "
 echo ""
 echo ""
 echo "EXAMPLE USE"
 echo "==========="
 echo ""
 echo "Command to execute the shell script::"
 echo ""
 echo " <path to this script>/qunex_container.sh \ " 
 echo "   --container=<Type of container image> \ "
 echo "   --script=<Path of the container folder> \ "
 echo "   --inputfolder=<input_folder> \ "
 echo "   --outputfolder=<output_folder> \ "
 echo "   --specfolder=<spec_folder> "
 echo ""
 exit 0
}

reho() {
    echo -e "$RED_F$1 \033[0m"
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


# =-=-=-=-=-= GENERAL OPTIONS =-=-=-=-=-=
#
# -- key variables to set
#

echo "---> Parameters $@"

for i in "$@"; do
  case "$i" in
    --container=* ) ConImage="${i#*=}"; shift 2;;
    --script=* ) QUNEXscript="${i#*=}"; shift 2;;
    --string=* ) QUNEXstring="${i#*=}"; shift 2;;
    --inputfolder=* ) InputFolder="${i#*=}"; shift 2;;
    --outputfolder=* ) OutputFolder="${i#*=}"; shift 2;;
    --specfolder=* ) SpecFolder="${i#*=}"; shift 2;;
    --containername=* ) ContainerName="${i#*=}"; shift 2;;
    * ) break ;;
  esac
done


echo ""
echo "Running qunex_container.sh"
echo "========================="
echo ""
echo "ConImage      : ${ConImage}"
echo "QUNEXscript   : ${QUNEXscript}"
echo "QUNEXstring   : ${QUNEXstring}"
echo "InputFolder   : ${InputFolder}"
echo "OutputFolder  : ${OutputFolder}"
echo "SpecFolder    : ${SpecFolder}"
echo "ContainerName : ${ContainerName}"
echo ""


# -- Setup paths for scripts folder and container
if [[ -z ${QUNEXscript} ]] && [[ -z ${QUNEXstring} ]]; then echo "  ---> Error: QuNex execute call or script is missing."; exit 1; echo ''; fi
if [[ -z ${ConImage} ]]; then echo "  ---> Error: QuNex Container image input is missing."; exit 1; echo ''; fi
if [[ -z ${InputFolder} ]]; then echo "  ---> Error: QuNex Input folder input is missing."; exit 1; echo ''; fi
if [[ -z ${OutputFolder} ]]; then echo "  ---> Error: QuNex Output folder input is missing."; exit 1; echo ''; fi

if [[ `echo ${ConImage} | grep '.simg' ` ]] || [[ `echo ${ConImage} | grep '.sif' ` ]]; then 
    Apptainer="yes"
else
    Docker="yes"
fi

# -- Execute Apptainer container
#
#   -- Not yet finished -> needs to differentiate between script and call

#if [[ ${Apptainer} == 'yes' ]] ; then 
#   echo ""
#   echo " -- Executing container image ${QUNEXCONIMAGEPath}"
#   echo ""
#   singularity exec ${ConImage} bash ${QUNEXRunCall}
#fi

# -- Execute Docker container
if [[ ${Docker} == 'yes' ]] ; then 
   
   echo ""
   echo "---> Executing Docker container image"
   
   # -- If script then parse folder name
   if [[ ! -z ${QUNEXscript} ]]; then
       ScriptsDir=$(dirname "${QUNEXscript}")
   fi
   echo "    -- Creating output folder $OutputFolder"
   
   mkdir -p ${OutputFolder}
   docker rm -f ${ContainerName}
   
   # -- Check for String or Script
   if [[ ! -z ${QUNEXscript} ]]; then
        echo "    ---> Running script ${QUNEXscript}"
        docker container run \
            --name ${ContainerName} -d \
            -v ${ScriptsDir}/:/data/scripts \
            -v ${InputFolder}/:/data/input \
            -v ${OutputFolder}:/data/output \
            -v ${SpecFolder}:/data/spec \
            ${ConImage} bash -c "/data/scripts/${QUNEXscript}"
   fi
   if [[ ! -z ${QUNEXstring} ]]; then
        echo "    ---> Running command string ${QUNEXstring}"
        docker container run \
            --name ${ContainerName} -d \
            -v ${InputFolder}/:/data/input \
            -v ${OutputFolder}:/data/output \
            -v ${SpecFolder}/:/data/spec \
             ${ConImage} bash -c "/opt/qunex/bin/qunex_api_wrapper.sh ${QUNEXstring}"
   fi
fi
