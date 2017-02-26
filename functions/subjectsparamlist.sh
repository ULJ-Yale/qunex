#!/bin/sh

# -------------------------------------------------
# --- Code for generating parameter files ---------
# -------------------------------------------------
		
	# -- test if subject_hcp.txt is absent
	if (test ! -f ${StudyFolder}/${CASE}/subject_hcp.txt); then
		# -- test if subject_hcp.txt is present		
		if (test -f ${StudyFolder}/${CASE}/subject.txt); then
			# -- if yes then copy it to subject_hcp.txt
			cp ${StudyFolder}/${CASE}/subject.txt ${StudyFolder}/${CASE}/subject_hcp.txt
		else
			# -- report error and exit
			echo ""
			reho "${StudyFolder}/${CASE}/subject_hcp.txt and subject.txt is missing."
			reho "Make sure you have sorted the dicoms and setup subject-specific files."
			reho "Note: These files are used to populate the subjects.preprocessing.${ListName}.list"
			echo ""
			exit 1
		fi
	fi
	
	echo "---" >> ${StudyFolder}/lists/subjects.preprocessing.${ListName}.param
	cat ${StudyFolder}/${CASE}/subject_hcp.txt >> ${StudyFolder}/lists/subjects.preprocessing.${ListName}.param
	echo "" >> ${StudyFolder}/lists/subjects.preprocessing.${ListName}.param
	
	# -- Fix paths stale or outdated paths
	DATATYPES="dicom 4dfp hcp nii"
  	for DATATYPE in $DATATYPES; do
  		CorrectPath="${StudyFolder}/${CASE}/${DATATYPE}"
  		GrepInput="/${CASE}/${DATATYPE}"		
  		ReplacePath=`more ${StudyFolder}/lists/subjects.preprocessing.${ListName}.param | grep "$GrepInput" | awk '{print $2}'`
		sed -i "s@$ReplacePath@$CorrectPath@" ${StudyFolder}/lists/subjects.preprocessing.${ListName}.param
	done
	
	echo " --> Appending $CASE Done"
	echo ""
	
