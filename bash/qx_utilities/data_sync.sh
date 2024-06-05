#!/bin/bash

# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= CODE START =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
 echo ""
 echo "This function runs rsync across the entire folder structure based on user "
 echo "specifications. It is used for syncing and backing up folders and data onto "
 echo "local or remote servers." 
 echo ""
 echo "INPUTS"
 echo "======"
 echo ""
 echo "--syncfolders        Set path for folders that contains studies for syncing"
 echo "--syncserver         Set sync server <UserName@some.server.address> or 'local' "
 echo "					    to sync locally"
 echo "--syncdestination    Set sync destination path"
 echo "--synclogfolder      Set log folder"
 echo "--sessions           Comma separated list of sessions for sync. (optional) "
 echo "                     If set, then '--syncfolders' path has to contain sessions' "
 echo "				        folders."
 echo ""
 echo ""
 exit 0
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]]; then
	usage
fi

# ------------------------------------------------------------------------------
# -- Check if command line arguments are passed for single user setup
# ------------------------------------------------------------------------------

# -- Initialize global output variables
unset SyncFolders
unset SyncLogFolder
unset SyncServer
unset CASES
unset SyncDestination

opts_GetOpt() {
sopt="$1"
shift 1
for fn in "$@" ; do
	if [ `echo $fn | grep -- "^${sopt}=" | wc -w` -gt 0 ] ; then
		echo $fn | sed "s/^${sopt}=//"
		return 0
	fi
done
local scriptName=$(basename ${0})
}


######################################### DO WORK ##########################################

main() {

echo ""
echo "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
echo "=-=-=-=  Starting QuNex Data Rsync Script  =-=-=-="
echo "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
echo ""

# -- Check if command line options are requested and return to default run if not
if [ -z "$1" ]; then
	echo "ERROR: No inputs provided!"
	usage
else
	# -- First check if single or double flags are set
	doubleflag=`echo $1 | cut -c1-2`
	singleflag=`echo $1 | cut -c1`
	
	if [ "$doubleflag" == "--" ]; then
		setflag="$doubleflag"
	else
		if [ "$singleflag" == "-" ]; then
			setflag="$singleflag"
		fi
	fi
	# -- Parse inputs
	if [[ "$setflag" =~ .*-.* ]]; then
		SyncFolders=`opts_GetOpt "${setflag}syncfolders" "$@" | sed 's/,/ /g;s/|/ /g'`; StudyFolders=`echo "$StudyFolders" | sed 's/,/ /g;s/|/ /g'` # list of inputs; removing comma or pipes
		CASES=`opts_GetOpt "${setflag}sessions" "$@" | sed 's/,/ /g;s/|/ /g'`; CASES=`echo "$StudyFolders" | sed 's/,/ /g;s/|/ /g'` # list of inputs; removing comma or pipes
		SyncServer=`opts_GetOpt "${setflag}syncserver" $@` # server to Sync to
		SyncDestination=`opts_GetOpt "${setflag}syncdestination" $@` # server to Sync to
		SyncLogFolder=`opts_GetOpt "${setflag}synclogfolder" $@`       # Log folder
		if [ -z "$SyncFolders" ]; then echo "ERROR -- Sync folders flag missing. Backing up $SyncFolders"; exit 0; fi
		if [ -z "$SyncServer" ]; then echo "ERROR -- Sync server flag missing"; show_usage; exit 0; fi
		if [ -z "$SyncDestination" ]; then echo "ERROR -- Sync server path flag missing"; show_usage; exit 0; fi
		if [ -z "$SyncLogFolder" ]; then echo "ERROR -- Log folder flag missing"; show_usage; exit 0; fi
		if [ -z "$CASES" ]; then echo "NOTE -- Individual cases flag missing. Not working on specific sessions."; fi
	fi
fi

# -- Setup new logfile, move old to outdated_logs
mkdir $SyncLogFolder  &> /dev/null
now=`date +%Y-%m-%d_%H.%M.%S.%6N`
TimeStamp=${now}

# -- Report options
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo ""
echo " Folders to Sync: $SyncFolders"
echo " Sesssions to Sync: $CASES"
echo " Server address to Sync to: $SyncServer"
echo " Path to Sync to: $SyncDestination"
echo " Log Folder: $SyncLogFolder"
echo " Time stamp: $TimeStamp"
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
echo "------------------------- Start of work --------------------------------"
echo ""

# -- Setup logging
echo "" > "$SyncLogFolder"/sync_log_"$now".txt
echo "######## Sync Log  $(date) ########" > "$SyncLogFolder"/sync_log_"$now".txt
echo "" >> "$SyncLogFolder"/sync_log_"$now".txt
echo "" >> "$SyncLogFolder"/sync_log_"$now".txt
echo "Backing up folders: $SyncFolders" >> "$SyncLogFolder"/sync_log_"$now".txt
echo "Backing up folders: $SyncFolders"; echo ""

# -- Sync studies loop
for SyncFolder in ${SyncFolders}
do
	if [[ ${SyncServer} == "local" ]]; then
		SyncServerName=`hostname`
		CheckSyncPath=`if [[ -d ${SyncDestination} ]]; then echo "YES"; fi` &> /dev/null
	else
		CheckSyncPath=`ssh -t ${SyncServer} "if [[ -d ${SyncDestination} ]]; then echo "YES"; fi"` &> /dev/null
		SyncServerName=${SyncServer}
	fi
	echo ""
	if [[ `echo ${CheckSyncPath} | grep "YES"` == "" ]]; then
		echo ""
		echo "   * ERROR -- The specified ${SyncDestination} is missing on ${SyncServerName}. Make sure the folder is present on ${SyncServerName} and re-run"
		echo ""
		exit 1
	else
		echo "   * Found ${SyncDestination} on ${SyncServerName}. Starting Sync ..."
		echo ""
		# -- Define command and initiate log
		if [ -z "$CASES" ]; then
			if [[ ${SyncServer} == "local" ]]; then
				cmd="rsync -aHW --progress ${SyncFolder}/* ${SyncDestination}"
			else
				cmd="rsync -aHW --progress ${SyncFolder}/* ${SyncServer}:${SyncDestination}"
			fi
			echo '' >> "$SyncLogFolder"/sync_log_"$now".txt
			echo '----------' >> "$SyncLogFolder"/sync_log_"$now".txt
			echo "Running command: ${cmd}" >> "$SyncLogFolder"/sync_log_"$now".txt
			echo '' >> "$SyncLogFolder"/sync_log_"$now".txt
			# -- Echo which study is being backed up
			echo "Backing up: ${SyncFolder} ---> ${SyncServerName}:${SyncDestination}" >> "$SyncLogFolder"/sync_log_"$now".txt
			echo '----------' >> "$SyncLogFolder"/sync_log_"$now".txt
			# -- Run rsync command
			echo "Running -- $cmd"; echo ""
			${cmd};
			# -- Finish logging
			echo 'DONE' >> "$SyncLogFolder"/sync_log_"$now".txt
			echo '----------' >> "$SyncLogFolder"/sync_log_"$now".txt
			echo '' >> "$SyncLogFolder"/sync_log_"$now".txt
		else
			for CASE in ${CASES}; do
				if [[ -d ${SyncFolder}/${CASE} ]]; then 
					echo "   * Found ${SyncFolder}/${CASE}. Proceeding."
				else
					echo "   ${SyncFolder}/${CASE} missing. Skipping."
					return 1
				fi
				if [[ ${SyncServer} == "local" ]]; then
					cmd="rsync -aHW --progress ${SyncFolder}/${CASE} ${SyncDestination}"
				else
					cmd="rsync -aHW --progress ${SyncFolder}/${CASE} ${SyncServer}:${SyncDestination}"
				fi
				echo '' >> "$SyncLogFolder"/sync_log_"$now".txt
				echo '----------' >> "$SyncLogFolder"/sync_log_"$now".txt
				echo "Running command: ${cmd}" >> "$SyncLogFolder"/sync_log_"$now".txt
				echo '' >> "$SyncLogFolder"/sync_log_"$now".txt
				# -- Echo which study is being backed up
				echo "Backing up: ${SyncFolder}/${CASE} ---> ${SyncServerName}:${SyncDestination}" >> "$SyncLogFolder"/sync_log_"$now".txt
				echo '----------' >> "$SyncLogFolder"/sync_log_"$now".txt
				# -- Run rsync command
				echo "Running -- $cmd"; echo ""
				${cmd};
				# -- Finish logging
				echo 'DONE' >> "$SyncLogFolder"/sync_log_"$now".txt
				echo '----------' >> "$SyncLogFolder"/sync_log_"$now".txt
				echo '' >> "$SyncLogFolder"/sync_log_"$now".txt
			done
		fi
	fi
done

echo '----------' >> "$SyncLogFolder"/sync_log_"$now".txt

echo "--- Data sync completed. Check outputs and logs for errors."
echo ""
echo "--- Check output logs here: ${SyncLogFolder}/sync_log_${now}.txt}"
echo ""
echo "------------------------- Successful completion of work --------------------------------"
echo ""
}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@