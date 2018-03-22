#!/bin/sh
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
# * Alan Anticevic, N3 Division, Yale University
#
# ## Product
#
#  Subjects batch parameter file generation script
#
# ## License
#
# * The SubjectsBatch.sh = the "Software"
# * This Software is distributed "AS IS" without warranty of any kind, either 
# * expressed or implied, including, but not limited to, the implied warranties
# * of merchantability and fitness for a particular purpose.
#
# ### TODO
#
# ## Prerequisite Installed Software
#
#
# ## Prerequisite Environment Variables
#
#
# ### Expected Previous Processing
# 
# * The necessary input files are subject-specific subject.txt param files
#
#~ND~END~

# -------------------------------------------------
# ------------ Set ListPath variable --------------
# -------------------------------------------------
		
	
	if [ -z "$ListPath" ]; then 
		unset ListPath
		mkdir -p "$StudyFolder"/processing/lists &> /dev/null
		cd ${StudyFolder}/processing/lists
		ListPath=`pwd`
		reho "Setting default path for list folder --> $ListPath"
	fi

# -------------------------------------------------
# --- Code for generating batch files -------------
# -------------------------------------------------
		
	# -- test if subject_hcp.txt is absent
	if (test ! -f ${SubjectsFolder}/${CASE}/subject_hcp.txt); then
		# -- test if subject_hcp.txt is present		
		if (test -f ${SubjectsFolder}/${CASE}/subject.txt); then
			# -- if yes then copy it to subject_hcp.txt
			cp ${SubjectsFolder}/${CASE}/subject.txt ${SubjectsFolder}/${CASE}/subject_hcp.txt
		else
			# -- report error and exit
			echo ""
			reho "${SubjectsFolder}/${CASE}/subject_hcp.txt and subject.txt is missing."
			reho "Make sure you have sorted the dicoms and setup subject-specific files."
			reho "Note: These files are used to populate the subjects.preprocessing.${ListName}.list"
			echo ""
			exit 1
		fi
	fi
	
	echo "List path is currently set to $ListPath"
	
	echo "---" >> ${ListPath}/batch."$ListName".txt
	cat ${SubjectsFolder}/${CASE}/subject_hcp.txt >> ${ListPath}/batch."$ListName".txt
	echo "" >> ${ListPath}/batch."$ListName".txt
	
	# -- Fix paths stale or outdated paths
	DATATYPES="dicom 4dfp hcp nii"
  	for DATATYPE in $DATATYPES; do
  		CorrectPath="${SubjectsFolder}/${CASE}/${DATATYPE}"
  		GrepInput="/${CASE}/${DATATYPE}"		
  		ReplacePath=`more ${ListPath}/batch.${ListName}.txt | grep "$GrepInput" | awk '{print $2}'`
		sed -i "s@$ReplacePath@$CorrectPath@" ${ListPath}/batch.${ListName}.txt
	done
	
	echo " --> Appending $CASE Done"
	echo ""
	
