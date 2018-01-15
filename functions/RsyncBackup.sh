#!/bin/bash
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# # setup_acls_n3_user.sh
#
# ## Copyright Notice
#
# Copyright (C) 2015 Anticevic Lab 
#
# * Yale University
#
# ## Author(s)
#
# * Alan Anticevic, Department of Psychiatry, Yale University
#
# ## Product
#
# * Wrapper for backup of studies on HPC clusters to N3 servers
#
# ## License
#
# Standard Yale OCR License
#
# ## Description:
#
# * This is a HPCBackup.sh wrapper developed for backup from a cluster to local
#   storage
#
# ### Installed Software (Prerequisites):
#
# * * NONE
#
#~ND~END~

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= CODE START =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

show_usage() {

echo ""
echo "---------------------------------------------------------------------------"
echo "------------ General Usage for Backing up HPC Studies ---------------------"
echo "---------------------------------------------------------------------------"
echo ""
echo "  This code runs rsync across the entire N3 folder structure based on user and"
echo "  group specifications. If no flags are specified it will use hard-coded settings"
echo "  that are in the code."
echo ""
echo "  If using flags to explicitly specify user/folder then usage is as follows for terminal input: "
echo ""
echo "  HPCBackup.sh --studiespath='<path_to_studies>' --studies='<lists_studies_folders>' --backupserver='<select_backup_server>' --logfolder='<path_to_log_folder>' "
echo ""
echo "  * Mandatory Inputs:"
echo ""
echo "   --studiespath=<path_to_studies>     Set path for studies folder for backup"
echo "   --studies=<lists_studies_folders>     Set input studies for backup"
echo "   --backupserver=<select_backup_server>     Set backup server <UserName@some.server.address>"
echo "   --logfolder=<path_to_log_folder>     Set log folder"
echo ""
echo ""
echo ""

}

# ------------------------------------------------------------------------------
#  -- Setup color outputs
# ------------------------------------------------------------------------------

reho() {
    echo -e "\033[31m $1 \033[0m"
}

geho() {
    echo -e "\033[32m $1 \033[0m"
}

# ------------------------------------------------------------------------------
#  -- Check if command line arguments are passed for single user setup
# ------------------------------------------------------------------------------

opts_GetOpt() {
sopt="$1"
shift 1
for fn in "$@" ; do
	if [ `echo $fn | grep -- "^${sopt}=" | wc -w` -gt 0 ] ; then
		echo $fn | sed "s/^${sopt}=//"
		return 0
	fi
done
}

# ------------------------------------------------------------------------------
#  -- Parse help calls
# ------------------------------------------------------------------------------


opts_CheckForHelpRequest() {
for fn in "$@" ; do
	if [ "$fn" = "--help" ]; then
		return 0
	fi
done
return 1
}

if opts_CheckForHelpRequest $@; then
	show_usage
	exit 0
fi

# ------------------------------------------------------------------------------
#  -- Check if command line arguments are specified
# ------------------------------------------------------------------------------

reho ""
reho "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
reho "=-=-=-= Starting syncing script for local N3 servers and NAS -=-=-=-="
reho "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
echo ""

# -- Check if command line options are requested and return to default run if not
if [ -z "$1" ]; then
	# -- Define overall studies folder	
	StudiesFolder="/gpfs/project/fas/n3/Studies"
	cd ${StudiesFolder}
	# -- Studies to backup
	StudyFolders=`ls`
	# -- Select backup server
	BackupServer="aa353@nmda.yale.internal"
	# -- Log folder paths
	LogFolder="/gpfs/project/fas/n3/admin/StudyBackupLogs"
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
		StudiesFolder=`opts_GetOpt "${setflag}studiespath" $@` # study folder to work on
		StudyFolders=`opts_GetOpt "${setflag}studies" "$@" | sed 's/,/ /g;s/|/ /g'`; StudyFolders=`echo "$StudyFolders" | sed 's/,/ /g;s/|/ /g'` 	# list of inputs; removing comma or pipes
		BackupServer=`opts_GetOpt "${setflag}backupserver" $@` # server to backup to
		LogFolder=`opts_GetOpt "${setflag}logfolder" $@`       # Log folder
		
		if [ -z "$StudiesFolder" ]; then reho "ERROR -- Studies folder flag missing"; show_usage; exit 0; fi
		if [ -z "$StudyFolders" ]; then reho "ERROR -- Individual folders flag missing"; show_usage; exit 0; fi
		if [ -z "$BackupServer" ]; then reho "ERROR -- Backup server flag missing"; show_usage; exit 0; fi
		if [ -z "$LogFolder" ]; then reho "ERROR -- Log folder flag missing"; show_usage; exit 0; fi
	fi
fi

# -- Setup new logfile, move old to outdated_logs
mkdir $LogFolder  &> /dev/null
mkdir $LogFolder/outdated_logs  &> /dev/null

mv "$LogFolder"/backup_log* "$LogFolder"/outdated_logs/  &> /dev/null
now=$(date +"%Y-%m-%d-%H-%M-%S")

echo "" > "$LogFolder"/backup_log_"$now".txt
echo "######## Study Backup Log  $(date) ########" > "$LogFolder"/backup_log_"$now".txt
echo "" >> "$LogFolder"/backup_log_"$now".txt
echo "" >> "$LogFolder"/backup_log_"$now".txt
echo "Backing up folders: $StudyFolders" >> "$LogFolder"/backup_log_"$now".txt
echo "Backing up folders: $StudyFolders"; echo ""

# -- Backup studies loop
for StudyFolder in $StudyFolders
do
	CheckStudy=`ssh -t ${BackupServer} "if [[ -d /n3/Studies/${StudyFolder} ]]; then echo "YES"; fi"` &> /dev/null
	echo ""	
	if [[ `echo ${CheckStudy} | grep "YES"` == "" ]]; then
		echo ""
		reho "   ERROR -- The specified $StudiesFolder/$StudyFolder is missing a link on ${BackupServer}:/n3/$StudyFolder. Setup link first and re-run"
		echo ""
	else
		geho "Found ${BackupServer}:/n3/$StudyFolder Starting backup ..."
		echo ""
		# -- Check if DataDrop is the study for rsync command
		if [ $StudyFolder == "DataDrop" ]; then
			cmd="rsync -aHW --progress $StudiesFolder/$StudyFolder/* ${BackupServer}:/n3/$StudyFolder/"
		fi
		# -- Define command and initiate log
		cmd="rsync -aHW --progress $StudiesFolder/$StudyFolder/* ${BackupServer}:/n3/Studies/$StudyFolder/"
		echo '' >> "$LogFolder"/backup_log_"$now".txt
		echo '----------' >> "$LogFolder"/backup_log_"$now".txt
		echo "Running command: ${cmd}" >> "$LogFolder"/backup_log_"$now".txt
		echo '' >> "$LogFolder"/backup_log_"$now".txt
		# -- Check if DataDrop is the study for logging
		if [ $StudyFolder == "DataDrop" ]; then
			echo "Backing up $StudiesFolder/$StudyFolder --> ${BackupServer}:/n3/$StudyFolder" >> "$LogFolder"/backup_log_"$now".txt
		fi
		# -- Echo which study is being backed up
		echo "Backing up $StudyFolder: $StudiesFolder/$StudyFolder --> ${BackupServer}:/n3/Studies/$StudyFolder" >> "$LogFolder"/backup_log_"$now".txt
		echo '----------' >> "$LogFolder"/backup_log_"$now".txt
		# -- Run rsync command
		echo "Running -- $cmd"; echo ""
		${cmd};
		# -- Finish logging
		echo 'DONE' >> "$LogFolder"/backup_log_"$now".txt
		echo '----------' >> "$LogFolder"/backup_log_"$now".txt
		echo '' >> "$LogFolder"/backup_log_"$now".txt
	fi
done

echo '----------' >> "$LogFolder"/backup_log_"$now".txt

exit 0
