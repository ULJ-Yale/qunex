#!/bin/bash
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## Copyright Notice
#
# Copyright (C)
#
# * Yale University
#
# ## Author(s)
#
# * Charlie Schleifer, N3 Division, Yale University
# * Alan Anticevic, N3 Division, Yale University
#
# ## Product
#
#  Turnkey wrapper for MNAP general pipeline
#
# ## License
#
# * The turnkey.sh = the "Software"
# * This Software is distributed "AS IS" without warranty of any kind, either 
# * expressed or implied, including, but not limited to, the implied warranties
# * of merchantability and fitness for a particular purpose.
#
# ### TODO
#
# ## Description 
#   
# This script, turnkey.sh, implements an automated 'turnkey' processing of multi-modal 
# imaging data via the MNAP general code
# 
# ## Prerequisite Installed Software
#
# * MNAP repositories and all their dependencies
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. $./turnkey.sh --help
#
# ### Expected Previous Processing
# 
# * The necessary input files are "$StudyFolder/subjects/$CASE/inbox/*dicom
#
#~ND~END~

usage() {
	echo ""
	echo " -- DESCRIPTION:"
	echo ""
	echo " This function reads acquisition logs to drive turnkey organization and processing of multimodal data."
	echo ""
	echo " It assumes that the log table has the same header format as RedCapExport_OrganizedDatabase.csv (four-line header: EVENT, FORM, LABEL, FIELD)"
	echo " 		writeACQLogs.R can be used to generate acquisition logs with the correct format from the general database"
	echo ""
	echo ""
	echo " -- REQUIRED PARMETERS:"
	echo ""
	echo "    --path=<study_folder>               Path to study folder"
	echo "    --logfile=<acq_log>                 Path to acquisition log file"
	echo "    --scanfield=<redcap_fieldname>      FIELD (acq_log row 4) header for scan IDs"
	echo "    --subjectfield=<redcap_fieldname>   FIELD header for subject IDs"
	echo "    --errorfield=<redcap_fieldname>     FIELD header for error status (0=no errors, 1=errors)"
	echo "    --dcmpath=<datadrop_dicoms>         Path to DataDrop folder to retrieve dicoms"
	echo ""
	echo " -- OPTIONAL PARMETERS:"
	echo ""
	echo "    --taskfield=<redcap_fieldname>      FIELD header for task version"
	echo "    --bhvpath=<datadrop_bhv>            Path to DataDrop folder to retrieve behavior files"
	echo "    --bhvdepth=<maxdepth>               Max subdir depth to search for behavior in bhvpath. If not specified, default=4"
	echo "    --bhvname=<string>                  string to search for behavior files"
	echo "                                             (NOTE: replace ID number with 'nnn' and variable elements with regex)"
	echo "    --eyefield=<redcap_fieldname>       FIELD header for eyetracking status"
	echo "    --eyepath=<datadrop_eye>            Path to DataDrop folder to retrieve eyetracking files"
	echo "    --eyedepth=<maxdepth>               Max subdir depth to search for eyetracking in eyepath. If not specified, default=4"
	echo "    --eyename=<string>                  string to search for eyetracking files"
	echo "                                             (NOTE: replace ID number with 'nnn' and variable elements with regex)"
	echo "    --physfield=<redcap_fieldname>      FIELD header for physio status"
	echo "    --physpath=<datadrop_phys>          Path to DataDrop folder to retrieve physio files"
	echo "    --physdepth=<maxdepth>              Max subdir depth to search for physio in physpath. If not specified, default=4"
	echo "    --physname=<string>                 string to search for physio files"
	echo "                                             (NOTE: replace ID number with 'nnn' and variable elements with regex)"
	echo ""
	echo ""
	echo " -- Example:"
	echo ""
	echo " turnkey.sh --path=/gpfs/project/fas/n3/Studies/BlackThorn/subjects/ \\"
	echo " --logfile=/gpfs/project/fas/n3/Studies/BlackThorn/subjects/acquisition.log.blackthorn_fmri.csv \\"
	echo " --scanfield=wmr_scan_bt \\"
	echo " --subjectfield=wmr_subject_bt \\"
	echo " --taskfield=wmr_tasks_bt \\"
	echo " --errorfield=wmr_errors_bt \\"
	echo " --eyefield=wmr_eyetrack_bt \\"
	echo " --physfield=wmr_physio_bt \\"
	echo " --dcmpath=/gpfs/project/fas/n3/Studies/DataDrop/MRRC_transfers/ \\"
	echo " --bhvpath=/gpfs/project/fas/n3/Studies/DataDrop/BoxSync_backup/BlackThorn-fMRI/ \\"
	echo " --bhvdepth=2 \\"
	echo " --bhvname=*BT_*nnn* \\"
	echo " --physpath=/gpfs/project/fas/n3/Studies/DataDrop/BoxSync_backup/BlackThorn-physio/ \\"
	echo " --physdepth=1 \\"
	echo " --physname=BT-nnn* \\"
	echo "  --eyepath=/gpfs/project/fas/n3/Studies/DataDrop/BoxSync_backup/BlackThorn-fMRI/ \\"
	echo " --eyedepth=3 \\"
	echo " --eyename=nnneyelinkData"			
}

# Setup color outputs
reho() { echo -e "\033[31m $1 \033[0m"; }
geho() { echo -e "\033[32m $1 \033[0m"; }

# Get flagged arguments
get_options() {
    local scriptName=$(basename ${0})
    local arguments=($@)

    # initialize global output variables
    unset StudyFolder
	unset LogFile
	unset scanField
	unset subjField
	unset taskField
	unset errorField
	unset eyeField
	unset physField
	unset bhvPath
	unset physPath
	unset eyePath
	unset dcmPath
	unset bhvDepth
	unset physDepth
	unset eyeDepth	
	unset bhvName
	unset physName
	unset eyeName
	runcmd=""

    # parse arguments
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
            --path=*)
                StudyFolder=${argument/*=/""}; index=$(( index + 1 ))
                ;;
            --logfile=*)
                LogFile=${argument/*=/""};     index=$(( index + 1 ))
                ;;
			--scanfield=*)
				scanField=${argument/*=/""};   index=$(( index + 1 ))
                ;;
			--subjectfield=*)
				subjField=${argument/*=/""};   index=$(( index + 1 ))
                ;;
			--taskfield=*)
				taskField=${argument/*=/""};   index=$(( index + 1 ))
                ;;
			--errorfield=*)
				errorField=${argument/*=/""};  index=$(( index + 1 ))
                ;;
			--eyefield=*)
				eyeField=${argument/*=/""};    index=$(( index + 1 ))
                ;;
			--physfield=*)
				physField=${argument/*=/""};   index=$(( index + 1 ))
                ;;
			--bhvpath=*)
				bhvPath=${argument/*=/""};     index=$(( index + 1 ))
                ;;
			--physpath=*)
				physPath=${argument/*=/""};    index=$(( index + 1 ))
                ;;
			--eyepath=*)
				eyePath=${argument/*=/""};     index=$(( index + 1 ))
                ;;
			--dcmpath=*)
				dcmPath=${argument/*=/""};     index=$(( index + 1 ))
                ;;
			--bhvdepth=*)
				bhvDepth=${argument/*=/""};    index=$(( index + 1 ))
                ;;
			--physdepth=*)
				physDepth=${argument/*=/""};   index=$(( index + 1 ))
                ;;
			--eyedepth=*)
				eyeDepth=${argument/*=/""};    index=$(( index + 1 ))
                ;;	
			--bhvname=*)
				bhvName=${argument/*=/""};     index=$(( index + 1 ))
                ;;
			--physname=*)
				physName=${argument/*=/""};    index=$(( index + 1 ))
                ;;
			--eyename=*)
				eyeName=${argument/*=/""};     index=$(( index + 1 ))
                ;;	
            *)
                usage; echo ""; reho "ERROR: Unrecognized Option: ${argument}"; echo ""
                exit 1
                ;;
        esac
    done

    #======= check required parameters and set defaults =======
    if [ -z ${StudyFolder} ]; then
        usage; echo ""; reho "ERROR: --path=<study-path> not specified>"; echo ""
        exit 1
    fi
	if [ -z ${LogFile} ]; then
		usage; echo ""; reho "ERROR: --logfile=<acquisition-log> not specified>"; echo ""
        exit 1
	fi
	if [ -z ${scanField} ]; then
		usage; echo ""; reho "ERROR: --scanfield=<scanID-redcap-fieldname> not specified>"; echo ""
        exit 1
	fi
	if [ -z ${subjField} ]; then
		usage; echo ""; reho "ERROR: --subjectfield=<subjectID-redcap-fieldname> not specified>"; echo ""
        exit 1
	fi
	if [ -z ${errorField} ]; then
		usage; echo ""; reho "ERROR: --errorfield=<errors-redcap-fieldname> not specified>"; echo ""
        exit 1
	fi
	if [ -z ${dcmPath} ]; then
		usage; echo ""; reho "ERROR: -dcmpath=<dicom-datadrop-path> not specified>"; echo ""
        exit 1
	fi
	if [ -z ${eyeField} ]; then
		reho "WARNING: --eyefield=<eyetracking-redcap-fieldname> not specified. Skipping eyetracking"; echo ""
		eyeField="none", eyePath="none", eyeName="none"
	fi
	if [ -z ${eyePath} ]; then
		reho "WARNING: --eyepath=<eyetracking-search path> not specified>. Skipping eyetracking"; echo ""
		eyeField="none"; eyePath="none"; eyeName="none"
	fi
	if [ -z ${eyeName} ]; then
		reho "WARNING: --eyename=<eyetracking-search-string> not specified>. Skipping eyetracking"; echo ""
		eyeField="none"; eyePath="none"; eyeName="none"
	fi
	if [ -z ${physField} ]; then
		reho "WARNING: --physfield=<physio-redcap-fieldname> not specified. Skipping physio"; echo ""
		physField="none", physPath="none", physName="none"
	fi
	if [ -z ${physPath} ]; then
		reho "WARNING: --physpath=<physio-search-path> not specified>. Skipping physio"; echo ""
		physField="none"; physPath="none"; physName="none"
	fi
	if [ -z ${physName} ]; then
		reho "WARNING: --physname=<physio-search-string> not specified>. Skipping physio"; echo ""
		physField="none"; physPath="none"; physName="none"
	fi
	if [ -z ${bhvPath} ]; then
		reho "WARNING: --bhvpath=<behavior-search path> not specified>. Skipping behavior"; echo ""
		bhvPath="none", bhvName="none"
	fi
	if [ -z ${taskField} ]; then
		reho "WARNING: --taskfield=<task-version-redcap-fieldname> not specified>"; echo ""
		taskField="none"
	fi
	if [ -z ${bhvName} ]; then
		reho "WARNING: --bhvname=<behavior-search-string> not specified>. Skipping behavior"; echo ""
		bhvPath="none", bhvName="none"
	fi
	if [ -z ${bhvDepth} ]; then
		reho "WARNING: --bhvdepth=<behavior-search-depth> not specified. Defaulting to 4 subdirs"; echo ""
		bhvDepth=4
	fi
	if [ -z ${physDepth} ]; then
		reho "WARNING: --physdepth=<physio-search-depth> not specified. Defaulting to 4 subdirs"; echo ""
		physDepth=4
	fi
	if [ -z ${eyeDepth} ]; then
		reho "WARNING: --eyedepth=<eyetracking-search-depth> not specified. Defaulting to 4 subdirs"; echo ""
		eyeDepth=4
	fi
    
    # report options
    echo ""
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo ""
    echo "   StudyFolder: ${StudyFolder}"
    echo "   LogFile:     ${LogFile}"
    echo "   scanField:   ${scanField}"
    echo "   subjField:   ${subjField}"
    echo "   taskField:   ${taskField}"
    echo "   errorField:  ${errorField}"
    echo "   eyeField:    ${eyeField}"
    echo "   physField:   ${physField}"
    echo "   bhvPath:     ${bhvPath}"
    echo "   physPath:    ${physPath}"
    echo "   eyePath:     ${eyePath}"
    echo "   dcmPath:     ${dcmPath}"
    echo "   bhvDepth:    ${bhvDepth}"
    echo "   physDepth:   ${physDepth}"
    echo "   eyeDepth:    ${eyeDepth}"
    echo "   bhvName:     ${bhvName}"
    echo "   physName:    ${physName}"
    echo "   eyeName:     ${eyeName}"
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - End --"
    echo ""
    geho "------------------------- Start of work --------------------------------"
    echo ""
}


######################################### DO WORK #############################################

main() {

# Get Command Line Options
get_options $@

#=============================================================================================
#===>  Read Acquisition Log 
#=============================================================================================

# retrieve field names from acquisition log header (row 4)
fieldHeader=$(head -4 ${LogFile} | tail -1)

# read scan IDs
	field=$scanField
    # get column index of chosen field 
    fieldIndex=$(echo $fieldHeader | tr ',' '\n' | tr -d '\"'  | grep -n ${field} | cut -d ':' -f 1)
    # retrieve chosen column as single string 
    str=$(cat ${LogFile} | awk -F ',' '{print $'$fieldIndex'}' | sed s/'NA'/'"NA"'/g)
    # substrings in single quotes, comma-delimited  
    str=$(echo $str | sed s/'" "'/'","'/g | tr \" \')
    # save default field separator
    OIFS=$IFS
    # set field separator to commas, then read string into array (each acquisition log row is one element) 
    IFS=',' read -ra scanIDs <<< "$str"
    # reset IFS
    IFS=$OIFS
	echo "${scanIDs[@]}"

# read subject IDs
	field=$subjField
    fieldIndex=$(echo $fieldHeader | tr ',' '\n' | tr -d '\"'  | grep -n ${field} | cut -d ':' -f 1)
    str=$(cat ${LogFile} | awk -F ',' '{print $'$fieldIndex'}' | sed s/'NA'/'"NA"'/g)
    str=$(echo $str | sed s/'" "'/'","'/g | tr \" \')
    OIFS=$IFS
    IFS=',' read -ra subjIDs <<< "$str"
    IFS=$OIFS
    echo "${subjIDs[@]}"

# read error status
	field=$errorField
    fieldIndex=$(echo $fieldHeader | tr ',' '\n' | tr -d '\"'  | grep -n ${field} | cut -d ':' -f 1)
    str=$(cat ${LogFile} | awk -F ',' '{print $'$fieldIndex'}' | sed s/'NA'/'"NA"'/g)
    str=$(echo $str | sed s/'" "'/'","'/g | tr \" \')
    OIFS=$IFS
    IFS=',' read -ra errors <<< "$str"
    IFS=$OIFS
    echo "${errors[@]}"

# read task versions
if [ "${taskField}" != "none" ]; then
	field=$taskField
    fieldIndex=$(echo $fieldHeader | tr ',' '\n' | tr -d '\"'  | grep -n ${field} | cut -d ':' -f 1)
    str=$(cat ${LogFile} | awk -F ',' '{print $'$fieldIndex'}' | sed s/'NA'/'"NA"'/g)
    str=$(echo $str | sed s/'" "'/'","'/g | tr \" \')
    OIFS=$IFS
    IFS=',' read -ra taskVersions <<< "$str"
    IFS=$OIFS
    echo "${taskVersions[@]}"
fi

# read eyetracking status
if [ "${eyeField}" != "none" ]; then
	field=$eyeField
	fieldIndex=$(echo $fieldHeader | tr ',' '\n' | tr -d '\"'  | grep -n ${field} | cut -d ':' -f 1)
	str=$(cat ${LogFile} | awk -F ',' '{print $'$fieldIndex'}' | sed s/'NA'/'"NA"'/g)
	str=$(echo $str | sed s/'" "'/'","'/g | tr \" \')
	OIFS=$IFS
	IFS=',' read -ra eyetracking <<< "$str"
	IFS=$OIFS
	echo "${eyetracking[@]}"
fi

# read physio status
if [ "${physField}" != "none" ]; then
	field=$physField
    fieldIndex=$(echo $fieldHeader | tr ',' '\n' | tr -d '\"'  | grep -n ${field} | cut -d ':' -f 1)
    str=$(cat ${LogFile} | awk -F ',' '{print $'$fieldIndex'}' | sed s/'NA'/'"NA"'/g)
    str=$(echo $str | sed s/'" "'/'","'/g | tr \" \')
    OIFS=$IFS
    IFS=',' read -ra physio <<< "$str"
    IFS=$OIFS
    echo "${physio[@]}"
fi
	
# get array length
length="${#scanIDs[@]}"
# beginning of subject info (after four line header)
indFirst=4
# end of subject info (last index)
((indLast = length - 1))

#======= check arrays ========
if [ "${#subjIDs[@]}" != "${length}" ]; then
	reho "ERROR parsing acquisition log: subject ID column"
	exit 1
fi
if [ "${#errors[@]}" != "${length}" ];then 
	reho "ERROR parsing acquisition log: errors column"
	exit 1
fi
if [ "${#eyetracking[@]}" != "${length}" ] && [ "${eyeField}" != "none" ];then
	reho "ERROR parsing acquisition log: eyetracking column"
	exit 1
fi
if [ "${#physio[@]}" != "${length}" ] && [ "${physField}" != "none" ]; then
	reho "ERROR parsing acquisition log: physio column"
	exit 1
fi
if [ "${#taskVersions[@]}" != "${length}" ] && [ "${taskField}" != "none" ]; then 
	reho "ERROR parsing acquisition log: task version column"
	exit 1
fi

#=============================================================================================
#===> Begin Turnkey Processing
#=============================================================================================

echo " "
echo "============================================================================="
echo "Begin Turnkey Processing"
echo "============================================================================="
echo " "

# loop through all scans in log 
i=3; while [ "${i}" -lt "${indLast}" ]; do (( i = ${i} +1 ))
	
	# set subject info (removing quotes and whitespace)
	scanID=$(echo "${scanIDs[$i]}"    | tr -d \' | tr -d \ )
	subjID=$(echo "${subjIDs[$i]}"    | tr -d \' | tr -d \ )
	task=$(echo "${taskVersions[$i]}" | tr -d \' | tr -d \ )
	errorYN=$(echo "${errors[$i]}"    | tr -d \' | tr -d \ )
	eyeYN=$(echo "${eyetracking[$i]}" | tr -d \' | tr -d \ )
	physYN=$(echo "${physio[$i]}"     | tr -d \' | tr -d \ )
	# strip non-numbers from subjID
	numID=$(echo $subjID | sed 's/[^0-9]//g')   
	
	
	#======= check subject info ========
	
	# skip if no scan ID
	if [ "${scanID}" == "NA" ] || [ -z "${scanID}" ]; then
		reho "ERROR: scan ID missing at row: ${i}"
		continue
	fi
	
	# skip if no subject ID
	if [ "${subjID}" == "NA" ] || [ -z "${subjID}" ]; then
		reho "ERROR: subect ID missing at row: ${i}"
		continue
	fi
	
	# skip if num ID less than two digits
	if [ "${#numID}" -lt "2" ]; then
		reho "ERROR: subject ID ${subjID} formatted incorrectly --> must be at least two integers"
		continue
	fi
	
	
	#======= SYNC DATA ========
	
	# sync MRI
	if [ -d ${dcmPath}/${scanID} ]; then
		mkdir -p ${StudyFolder}/${scanID}/inbox
		dcmReport=$(cat ${StudyFolder}/${scanID}/dicom/DICOM-Report.txt)
		# check if DICOM-Report contains text. If dicomsort is not complete then sync raw dicoms to inbox
		if [ "${#dcmReport}" == "0" ]; then
			echo "...syncing dicoms for ${scanID}"
			echo "${dcmPath}/${scanID}/... ---> ${StudyFolder}/${scanID}/inbox/"
			rsync -rWH  ${dcmPath}/${scanID}/*_*/ ${StudyFolder}/${scanID}/inbox/
			geho "${scanID} sync complete"; echo "" 
		else
			geho "${scanID} dicoms already sorted -- not syncing"; echo ""
		fi
	else
		reho "ERROR ${dcmPath}/${scanID} not found"; echo ""
		continue  
	fi 
	
	# sync behavior
	if [ "${bhvPath}" != "none" ]; then
		echo "...syncing behavior data for ${subjID}"
		echo "${bhvPath}... ---> ${StudyFolder}/${scanID}/bhvavior/"
		mkdir -p ${StudyFolder}/${scanID}/behavior
		bhvFile=$(echo $bhvName | sed s/'nnn'/${numID}/g)
		find ${bhvPath} -maxdepth ${bhvDepth} -type f -name ${bhvFile} -exec rsync -rWH {} ${StudyFolder}/${scanID}/behavior/ \;
		geho "${subjID} behavior sync complete"; echo "" 
	fi
	
	# sync physio
	if [ "${physPath}" != "none" ] && [ "${physYN}" == "1" ];then
		echo "...syncing physio data for ${subjID}" 
		echo "${physPath}... ---> ${StudyFolder}/${scanID}/physio/"
		mkdir -p ${StudyFolder}/${scanID}/physio 
		physFile=$(echo $physName | sed s/'nnn'/${numID}/g)
		find ${physPath} -maxdepth ${physDepth} -type f -name ${physFile} -exec rsync -rWH {} ${StudyFolder}/${scanID}/physio/ \;
		geho "${subjID} physio sync complete"; echo "" 
	fi
	
	# sync eyelink 
	if [ "${eyePath}" != "none" ] && [ "${eyeYN}" == "1" ];then
		echo "...syncing eyelink data for ${subjID}"
		echo "${eyePath}... ---> ${StudyFolder}/${scanID}/eyetracking/"
		mkdir -p ${StudyFolder}/${scanID}/eyetracking
		eyeFile=$(echo $eyeName | sed s/'nnn'/${numID}/g)
		find ${eyePath} -maxdepth ${eyeDepth} -type d -name ${eyeFile} -exec rsync -rWH {} ${StudyFolder}/${scanID}/eyetracking/ \;
		geho "${subjID} eyelink sync complete"; echo ""
	fi
			
done
}

main $@
