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
 		echo "		--path=<study_folder>						Path to study data folder"
		echo "		--mastersubjectid=<list_of_cases>			Overall database subject ID within XNAT"
		echo "		--subject=<list_of_cases>					List of subjects to run that are study-specific (may be unique from --mastersubjectid)"
		echo "		--project=<name_of_xnat_project>			Specify the XNAT cloud project name"
		echo "		--hostname=<xnat_hostname>					Specify the XNAT hostname"
		echo "		--niftiupload=<specify_nifti_upload>		Specify <yes> or <no> for NIFTI upload. Default is [yes]"
		echo "		--overwrite=<specify_level_of_overwrite>	Specify <yes> or <no> for cleanup of prior upload. Default is [yes]"
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
## -- Overwrite="whether to delete existing XNAT upload prior to upload
## -- NIFTIUPLOAD="whether to upload NIFTIs
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
    unset NIFTIUPLOAD
    unset MASTERSUBID
    unset Overwrite

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
            --mastersubjectid=*)
                MASTERSUBIDS=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --niftiupload=*)
                NIFTIUPLOAD=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --overwrite=*)
                Overwrite=${argument/*=/""}
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
    
    if [ -z ${NIFTIUPLOAD} ]; then
		NIFTIUPLOAD="yes"

    fi
    
    if [ -z ${MASTERSUBIDS} ]; then
		MASTERSUBIDS=$CASES
        echo ""
        reho "Note: --mastersubjectid flag omitted. Assuming --subject flag matches --mastersubjectid in XNAT"
        echo ""
    fi
    
     if [ -z ${Overwrite} ]; then
		Overwrite="yes"
    fi
    
    # -- report options
    echo ""
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo "   StudyFolder: ${StudyFolder}"
    echo "   Subjects to process: ${CASES}"
    echo "   Master XNAT IDs for subjects (in order): ${MASTERSUBID}"
    echo "   NIFTI upload: ${NIFTIUPLOAD}"
    echo "	 Overwrite set to: ${Overwrite}"
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
ceho "       ********************************************"
ceho "       ****** Setting up XNAT cloud upload ********"
ceho "       ********************************************"
echo ""

# ------------------------------------------------------------------------------
#  first check if .xnat credentials exist:
# ------------------------------------------------------------------------------
	
if [ -f ${HOME}/.xnat ]; then
	echo ""
	ceho "       XNAT credentials found. Proceeding with upload.        "
	echo ""
else
	reho "-- XNAT credentials NOT found. Please generate them now."
	echo ""
	reho "--> Enter your XNAT HOST username:"
	if read -s answer; then
		XNATUser=$answer
	fi
	reho "--> Enter your XNAT HOST password:"
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
	geho "-- Transfer node confirmed: $TRANSFERNODE. Proceeding"
	echo ""
else
	reho "-- Transfer to the XNAT server from $TRANSFERNODE is not supported."
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
curl -X POST -u "$CRED" "$HOST/data/JSESSION" -i > ${StudyFolder}/JSESSION.txt

#`date +%Y-%m-%d-%H-%M`
#JSESSIONLOG=`ls ${StudyFolder}/JSESSION-*.txt`

JSESSION=`grep "JSESSIONID" ${StudyFolder}/JSESSION.txt`
JSESSION=${JSESSION:23:32}
echo ""
geho "-- JSESSION created: $JSESSION"

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
	DICOMSERIES=`ls -vd */ | cut -f1 -d'/'`
	#DICOMSERIES="1"

	## -- iterate over DICOM SERIES
	DICOMCOUNTER=0
	for SERIES in $DICOMSERIES; do
		DICOMCOUNTER=$((DICOMCOUNTER+1))
		geho "-- Working on SERIES: $SERIES"
		echo ""
		mkdir ${StudyFolder}/xnatupload/temp/working/ &> /dev/null
		## -- unzip files for upload
		geho "-- Unzipping DICOMs and linking into temp location --> ${StudyFolder}/xnatupload/temp/working/"
		echo ""
		gunzip -f ${StudyFolder}/${CASE}/dicom/${SERIES}/*.gz &> /dev/null
		geho "-- Uploading individual DICOMs ... "
			cd ${StudyFolder}/${CASE}/dicom/${SERIES}/
			UPLOADDICOMS=`ls ./*dcm | cut -f2 -d'/'`
			echo ""
			echo "--------------------- DICOMs Staged for XNAT Upload: -------------------"
			echo ""
			echo $UPLOADDICOMS
			echo ""
			echo "------------------------------------------------------------------------"
			echo ""
			for DCM in $UPLOADDICOMS; do
				cd ${StudyFolder}/xnatupload/temp/working/
				ln ${StudyFolder}/${CASE}/dicom/${SERIES}/${DCM} ${StudyFolder}/xnatupload/temp/working/
				if [ -d "${StudyFolder}/xnatupload/temp/working/${DCM}" ]; then
					reho "--> ERROR: Unexpected directory ${StudyFolder}/${CASE}/dicom/${SERIES}/${DCM}"
					exit 1
				fi
				## -- upload individual dicom files
				echo curl -b "JSESSIONID=$JSESSION" -X POST "$HOST/data/services/import?import-handler=gradual-DICOM&inbody=true&PROJECT_ID=$PROJ&SUBJECT_ID=$CASE&EXPT_LABEL=$CASE" --data-binary "@${DCM}"
				PREARCPATH=$(curl -b "JSESSIONID=$JSESSION" -X POST "$HOST/data/services/import?import-handler=gradual-DICOM&inbody=true&PROJECT_ID=$PROJ&SUBJECT_ID=$CASE&EXPT_LABEL=$CASE" --data-binary "@${DCM}")
			done	
				
		echo ""
		geho "-- PREARCHIVE XNAT PATH: ${PREARCPATH}"				
		echo ""
		
		## -- Check timestamp format matches the inputs
		TIMESTAMP=$(echo ${PREARCPATH} | cut -d'/' -f 6 | tr -d '/')
		PATTERN="[0-9]_[0-9]"
		if [[ ${TIMESTAMP} =~ ${PATTERN} ]]; then
     		PREARCPATHFINAL="/data/prearchive/projects/${PROJ}/${TIMESTAMP}/${CASE}"
     		geho "-- Debug PAF is ${PREARCPATHFINAL}"
		else
      		reho `date` "- Debug TS doesn't pass! ${TIMESTAMP}"
		fi
		
		## - clean up and gzip data
		rm -rf ${StudyFolder}/xnatupload/temp/working/ &> /dev/null
		gzip ${StudyFolder}/${CASE}/dicom/${SERIES}/* &> /dev/null
		clear UPLOADDICOMS
		echo ""
		geho "-- DICOM SERIES $SERIES upload completed"
		geho "------------------------------------------"
		echo ""
	done
 
	## -- commit session (builds prearchive xml)
	geho "-- Committing XNAT session to prearchive..."
	echo ""
	curl -b "JSESSIONID=$JSESSION" -X POST "${HOST}${PREARCPATHFINAL}?action=build" &> /dev/null
	
	## -- archive session
	curl -b "JSESSIONID=$JSESSION" -X POST -H "Content-Type: application/x-www-form-urlencoded" "${HOST}/data/services/archive?src=${PREARCPATHFINAL}&overwrite=delete"
	echo ""

	echo ""
	geho "-- DICOM archiving completed completed for a total of $DICOMCOUNTER series"
	geho "--------------------------------------------------------------------------------"
	echo ""
	
	## ------------------------------------------------------------------
	## -- code for uploading extra directories, such as NIFTI, HCP ect.
	## ------------------------------------------------------------------
		
	if [ "$NIFTIUPLOAD" == "yes" ]; then
		geho "-- Uploading individual NIFTIs ... "
		echo ""
		cd ${StudyFolder}/${CASE}/nii/
		NIFTISERIES=`ls | cut -f1 -d"." | uniq`
		#NIFTISERIES="01"
		
		## -- iterate over individual nifti files
		SCANCOUNTER=0
		for NIFTIFILE in $NIFTISERIES; do
			SCANCOUNTER=$((SCANCOUNTER+1))
			MULTIFILES=`ls ./$NIFTIFILE.*`
			FILESTOUPLOAD=`echo $MULTIFILES | sed -e 's,./,,g'`
			for NIFTIFILEUPLOAD in $FILESTOUPLOAD; do
				geho "-- Uploading NIFTI $NIFTIFILEUPLOAD"
				echo ""
				## -- clean existing nii session if requested
				if [ "$Overwrite" == "yes" ]; then
					curl -b "JSESSIONID=$JSESSION" -X DELETE "${HOST}/data/projects/${PROJ}/subjects/${CASE}/experiments/${CASE}/scans/${SCANCOUNTER}/resources/nii"
				fi
				## -- create a folder for nii scans
				curl -b "JSESSIONID=$JSESSION" -X PUT "${HOST}/data/projects/${PROJ}/subjects/${CASE}/experiments/${CASE}/scans/${SCANCOUNTER}/resources/nii"
				## -- upload a specific nii session
				curl -b "JSESSIONID=$JSESSION" -X POST "${HOST}/data/projects/${PROJ}/subjects/${CASE}/experiments/${CASE}/scans/${SCANCOUNTER}/resources/nii/files/${NIFTIFILEUPLOAD}?inbody=true&overwrite=delete" --data-binary "@${NIFTIFILEUPLOAD}"
			done
			geho "-- NIFTI series $NIFTIFILE upload completed"
		done
		
		echo ""
		geho "-- NIFTI upload completed with a total of $SCANCOUNTER scans"
		geho "--------------------------------------------------------------------------------"
		echo ""	
	fi
done
	
## -- close JSESSION	
curl -X DELETE -b "JSESSIONID=${JSESSION}" "$HOST/data/JSESSION"	

## -- Log completion message

echo ""
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
