#!/bin/sh
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## Copyright Notice
#
# Copyright (C)
#
# * Radiologics
# * Yale University
#
# ## Author(s)
#
# * Tim Olsen <tim@radiologics.com>
# * Alan Anticevic, N3 Division, Yale University
#
# ## Product
#
#  XNAT upload wrapper for DICOMs and other data
#
# ## License
#
# * The XNATCloudUpload.sh = the "Software"
# * This Software is distributed "AS IS" without warranty of any kind, either 
# * expressed or implied, including, but not limited to, the implied warranties
# * of merchantability and fitness for a particular purpose.
#
# ### TODO
#
# --> Add functionality to take in all data types into the XNAT database
#
# ## Description 
#   
# This script, XNATCloudUpload.sh, implements upload of the data to the XNAT host via the curl API 
# 
# ## Prerequisite Installed Software
#
# * curl
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. $./XNATCloudUpload.sh --help
#
# ### Expected Previous Processing
# 
# * The necessary input files are data stored in the following format
# * These data are stored in: "$StudyFolder/subjects/$CASE/
#
# Last Modified: 07/24/2017
#
#~ND~END~

usage() {
		echo ""
		echo "-- DESCRIPTION:"
		echo ""
		echo "This function implements syncing to the XNAT cloud HOST via the CURL REST API."
		echo ""
		echo ""
		echo "-- REQUIRED PARMETERS:"
		echo ""
 		echo "		--path=<study_folder>					Path to study data folder"
		echo "		--subject=<list_of_cases>				List of subjects to run"
		echo "		--project=<name_of_xnat_project>		Specify the XNAT cloud project name"
		echo "		--hostname=<xnat_hostname>				Specify the XNAT hostname"
		echo ""
		echo "-- OPTIONAL PARMETERS:"
		echo "" 
 		echo " N/A"
 		echo ""
 		echo "-- Example:"
		echo ""
		echo "XNATCloudUpload.sh --path='/gpfs/project/fas/n3/Studies/BlackThorn/subjects' \ "
		echo "--subject='100206' \ "
		echo "--project='bt-yale' \ "
		echo "--hostname='https://blackthornrx-sandbox.dev.radiologics.com' "
		echo ""	
}

# ------------------------------------------------------------------------------
#  Load Core Functions
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

## -- Input variables for this script:
## -----------------------------------------------------------------------------
## -- HOST=https://somewhere.xnat.org
## -- CRED="username:password"
## -- PROJ="XNAT PROJECT ID to push data to"
## -- StudyFolder="Master directory containing folders to push"
## -- CASES="List of FOLDERS to push that have a specific subject name
## -----------------------------------------------------------------------------

get_options() {
    local scriptName=$(basename ${0})
    local arguments=($@)
    
    # -- initialize global output variables
    unset StudyFolder
    unset HOST
    unset CRED
    unset PROJ
    unset CASES

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
            --path=*)
                StudyFolder=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --subject=*)
                CASES=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --hostname=*)
                HOST=${argument/*=/""}
                index=$(( index + 1 ))
                ;;      
            --project=*)
                PROJ=${argument/*=/""}
                index=$(( index + 1 ))
                ;;      
            *)
                usage
                reho "ERROR: Unrecognized Option: ${argument}"
        		echo ""
                exit 1
                ;;
        esac
    done

    # -- check required parameters
    
    if [ -z ${StudyFolder} ]; then
        usage
        reho "ERROR: <study-path> not specified"
        echo ""
        exit 1
    fi
	
    if [ -z ${CASES} ]; then
        usage
        reho "ERROR: <Subject-IDs> not specified"
        echo ""
        exit 1
    fi
	
    if [ -z ${HOST} ]; then
        usage
        reho "ERROR: XNAT hostname not specified"
        echo ""
        exit 1
    fi
    
    if [ -z ${PROJ} ]; then
        usage
        reho "ERROR: XNAT project id not specified"
        echo ""
        exit 1
    fi
    
    # -- report options
    echo ""
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo "   StudyFolder: ${StudyFolder}"
    echo "   Subjects to process: ${CASES}"
    echo "   XNAT Hostname: ${HOST}"
    echo "   XNAT Project ID: ${PROJ}"
    echo "-- ${scriptName}: Specified Command-Line Options - End --"
    echo ""
    geho "------------------------- Start of work --------------------------------"
    echo ""
}

######################################### DO WORK ##########################################

main() {

# -- Get Command Line Options
get_options $@

echo ""
reho "********************************************"
reho "****** Setting up XNAT cloud upload ********"
reho "********************************************"
echo ""

# ------------------------------------------------------------------------------
#  first check if .xnat credentials exist:
# ------------------------------------------------------------------------------
	
if [ -f ${HOME}/.xnat ]; then
	echo ""
	ceho "XNAT credentials found. Proceeding with upload."
	echo ""
else
	reho "XNAT credentials NOT found. Please generate them now."
	echo ""
	reho "Enter your XNAT HOST username:"
	if read -s answer; then
		XNATUser=$answer
	fi
	reho "Enter your XNAT HOST password:"
	if read -s answer; then
		XNATPass=$answer
	fi
	echo $XNATUser:$XNATPass >> ${HOME}/.xnat
	chmod 400 ${HOME}/.xnat
	unset XNATUser
	unset XNATPass
fi

# ------------------------------------------------------------------------------
#   check if you are on the transfer node:
# ------------------------------------------------------------------------------

TRANSFERNODE=`hostname` 
if [ $TRANSFERNODE == "transfer-grace.hpc.yale.edu" ]; then 
	echo ""
	geho "Transfer node confirmed: $TRANSFERNODE. Proceeding"
	echo ""
else
	reho "Transfer to the XNAT server from $TRANSFERNODE is not supported."
	echo ""
	exit 1
fi

# ------------------------------------------------------------------------------
#  Setup the JSESSION and clean up prior temp folders:
# ------------------------------------------------------------------------------

START=$(date +"%s")

## -- get credentials
CRED=`more ${HOME}/.xnat`

## -- open JSESSION
curl -X POST -u "$CRED" "$HOST/data/JSESSION" -i > $ARC-JSESSION.txt
JSESSION=`grep "JSESSIONID" ./$ARC-JSESSION.txt`
JSESSION=${JSESSION:23:32}
echo "JSESSION created: $JSESSION"

COUNTER=1

rm -r ${StudyFolder}/xnatupload/temp/working &> /dev/null

# ------------------------------------------------------------------------------
#  Iterate over CASES:
# ------------------------------------------------------------------------------

cd ${StudyFolder}	
for CASE in ${CASES}; do	
	## -- first check if data drop is present or if inbox is populated
	cd ${StudyFolder}/${CASE}/dicom
	echo ""
	geho "-- Working on subject: ${CASE}"
	cd ${StudyFolder}/${CASE}/dicom/
	echo ""
	DICOMSESSIONS=`ls -vd */ | cut -f1 -d'/'`
	## -- iterate over DICOM sessions
	for SESSION in $DICOMSESSIONS; do
		geho "-- Working on SESSION: $SESSION"
		echo ""
		mkdir ${StudyFolder}/xnatupload/temp/working &> /dev/null
		## -- unzip files for upload
		geho "-- Unzipping DICOMs into temp location --> ${StudyFolder}/xnatupload/temp/working/"
		echo ""
		gunzip -f ${StudyFolder}/${CASE}/dicom/${SESSION}/*.gz
		ln ${StudyFolder}/${CASE}/dicom/${SESSION}/*dcm ${StudyFolder}/xnatupload/temp/working/
		geho "Uploading DICOMs"
		echo ""
			UPLOADDICOMS=`ls ${StudyFolder}/xnatupload/temp/working/* | cut -f2 -d'/'`
			for DCM in $UPLOADDICOMS; do
				if [ -d "$DCM" ]; then
					echo "ERROR: Unexpected directory ${StudyFolder}/${CASE}/dicom/${SESSION}/$DCM"
					exit 1
				fi
				## -- upload individual dicom files
				echo curl -b "JSESSIONID=$JSESSION" -X POST "$HOST/data/services/import?import-handler=gradual-DICOM&inbody=true&PROJECT_ID=$PROJ&SUBJECT_ID=$CASE&EXPT_LABEL=$SESSION" --data-binary "@$DCM"
				PREARCPATH=$(curl -b "JSESSIONID=$JSESSION" -X POST "$HOST/data/services/import?import-handler=gradual-DICOM&inbody=true&PROJECT_ID=$PROJ&SUBJECT_ID=$CASE&EXPT_LABEL=$SESSION" --data-binary "@$DCM")
			done	
		TIMESTAMP=${PREARCPATH:31:18}
		PREARCPATH="/data/prearchive/projects/$PROJ/$TIMESTAMP/$SESSION"
		echo "PREARCHIVE PATH: '$PREARCPATH'"
		## - clean up and gzip data
		rm -rf ${StudyFolder}/xnatupload/temp/working/ &> /dev/null
		gzip ${StudyFolder}/${CASE}/dicom/${SESSION}/* &> /dev/null
	done
 
	## -- commit session (builds prearchive xml)
	curl -b "JSESSIONID=$JSESSION" -X POST "${HOST}${PREARCPATH}?action=build"
	## -- archive session
	curl -b "JSESSIONID=$JSESSION" -X POST -H "Content-Type: application/x-www-form-urlencoded"  "${HOST}/data/services/archive?src=${PREARCPATH}" &

	## --> Add more code for uploading extra directories, such as NIFTI, HCP ect.
done
	
## -- close JSESSION	
curl -X DELETE -b "JSESSIONID=${JSESSION}" "$HOST/data/JSESSION"	

## -- Log completion message

geho "--- XNAT upload completed. Check output log for outputs and errors."
echo ""
geho "------------------------- End of work --------------------------------"
echo ""

exit 1

}	

#
# -- Invoke the main function to get things started
#

main $@
