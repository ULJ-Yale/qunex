#!/bin/sh

# define global variables
StudyFolder=/gpfs/project/fas/n3/Studies/BlackThorn/subjects
datadrop=/gpfs/project/fas/n3/Studies/DataDrop
#redcap=${datadrop}/RedCap_sync/BlackThornfMRI_redcap.txt #TODO 2/24
boxsync=${datadrop}/BoxSync_backup

# note: code depends on proper scan notes in RedCap

##### Alan's comment ----> This line does not work	
cat " " > ${StudyFolder}/subjects.all.blackthorn.txt 

# read scan IDs from the acquisition log
CASES=$(cat ${redcap} | grep "BT-"| cut -d "," -f 2 )

for CASE in ${CASES}; do 

	# get ID number, task version, and errors from acquisition log
	ID=$(cat ${redcap} | grep ",${CASE}," | cut -d "," -f 3 )
	N=$(echo $ID | sed 's/[^0-9]//g') # strip non-numbers from ID
	version=$(cat ${redcap} | grep ${ID} | cut -d "," -f 4)
	errors=$(cat ${redcap} | grep ${ID} | cut -d "," -f 21)
	eyelink=$(cat ${redcap} | grep ${ID} | cut -d "," -f 22)
	physio=$(cat ${redcap} | grep ${ID} | cut -d "," -f 23)
	
	
	# sync dicoms from DataDrop for cases that haven't been dicomsorted yet 
	if (test ! -f ${StudyFolder}/${CASE}/dicom/DICOM-Report.txt); then
		mkdir -p ${StudyFolder}/${CASE}/inbox
		rsync -aWH ${datadrop}/MRRC_transfers/${CASE}/prismab*/ ${StudyFolder}/${CASE}/inbox/
		/gpfs/project/fas/n3/software/MNAP/general/AnalysisPipeline.sh --path="${StudyFolder}" --function="dicomsort"  --subjects="${CASE}" --runmethod="2" --queue="anticevic" --scheduler="lsf" --overwrite="no"
	fi
	
	#sync behavior 
	mkdir ${StudyFolder}/${CASE}/behavior
	find ${boxsync}/BlackThorn-fMRI/ -maxdepth 2 -type f -name "*BT*${N}*" -exec rsync -aWH {} ${StudyFolder}/${CASE}/behavior/ \;
	#sync physio
	if [ ${physio} == 1 ];then
		mkdir ${StudyFolder}/${CASE}/physio 
		find ${boxsync}/BlackThorn-physio/ -maxdepth 1 -type f -name "*${N}*" -exec rsync -aWH {} ${StudyFolder}/${CASE}/physio/ \;
	fi
	#sync eyelink 
	if [ ${eyelink} == 1 ];then
		mkdir -p ${StudyFolder}/${CASE}/eyetracking
		find ${boxsync}/BlackThorn-fMRI/ -maxdepth 2 -type d -name "*${N}eyelinkData" -exec rsync -aWH --exclude='*bmp' {} ${StudyFolder}/${CASE}/behavior/ \;
	fi
	
	#create subject_hcp.txt files
	if [ ${errors} == 0 ];then
		if (test ! -f ${StudyFolder}/${CASE}/subject_hcp.txt); then
			echo "id: ${CASE}" > ${StudyFolder}/${CASE}/subject_hcp.txt
			echo "subject: ${CASE}" >> ${StudyFolder}/${CASE}/subject_hcp.txt
			echo "dicom: /gpfs/project2/fas/n3/Studies/BlackThorn/subjects/${CASE}/dicom" >> ${StudyFolder}/${CASE}/subject_hcp.txt
			echo "raw_data: /gpfs/project2/fas/n3/Studies/BlackThorn/subjects/${CASE}/nii" >> ${StudyFolder}/${CASE}/subject_hcp.txt
			echo "data: /gpfs/project2/fas/n3/Studies/BlackThorn/subjects/${CASE}/4dfp" >> ${StudyFolder}/${CASE}/subject_hcp.txt
			echo "hcp: /gpfs/project2/fas/n3/Studies/BlackThorn/subjects/${CASE}/hcp" >> ${StudyFolder}/${CASE}/subject_hcp.txt
			echo "" >> ${StudyFolder}/${CASE}/subject_hcp.txt
			cat ${StudyFolder}/inbox/examples/${version}_task.txt >> ${StudyFolder}/${CASE}/subject_hcp.txt
			
			echo "---" >> ${StudyFolder}/subjects.all.blackthorn.txt
			cat ${StudyFolder}/${CASE}/subject_hcp.txt >> ${StudyFolder}/subjects.all.blackthorn.txt
			echo "" >> ${StudyFolder}/subjects.all.blackthorn.txt	
		fi
	fi

	##### Alan's comment ----> Note that this code won't work as it relies on HCP being finished... 
	####                       You really just want to check results from DICOM Sorting and/or NIFTI

	# create conc and fidl files in $StudyFolder/inbox
	if (test -d ${StudyFolder}/${CASE}/hcp/${CASE}/MNINonLinear/Results); then
		#conc 
		echo "number_of_files: 6" > ${StudyFolder}/inbox/${CASE}_BT.CIFTI.conc
		echo "file:/gpfs/project/fas/n3/Studies/BlackThorn/subjects/${CASE}/images/bold2.dtseries.nii >> ${StudyFolder}/inbox/${CASE}_BT.CIFTI.conc
		echo "file:/gpfs/project/fas/n3/Studies/BlackThorn/subjects/${CASE}/images/bold3.dtseries.nii >> ${StudyFolder}/inbox/${CASE}_BT.CIFTI.conc
		echo "file:/gpfs/project/fas/n3/Studies/BlackThorn/subjects/${CASE}/images/bold4.dtseries.nii >> ${StudyFolder}/inbox/${CASE}_BT.CIFTI.conc
		echo "file:/gpfs/project/fas/n3/Studies/BlackThorn/subjects/${CASE}/images/bold5.dtseries.nii >> ${StudyFolder}/inbox/${CASE}_BT.CIFTI.conc
		echo "file:/gpfs/project/fas/n3/Studies/BlackThorn/subjects/${CASE}/images/bold6.dtseries.nii >> ${StudyFolder}/inbox/${CASE}_BT.CIFTI.conc
		echo "file:/gpfs/project/fas/n3/Studies/BlackThorn/subjects/${CASE}/images/bold7.dtseries.nii >> ${StudyFolder}/inbox/${CASE}_BT.CIFTI.conc
	
		#fidl
		cp ${StudyFolder}/inbox/examples/${version}_AR_fidl.txt ${StudyFolder}/inbox/${CASE}_BT_AR.fidl
		cp ${StudyFolder}/inbox/examples/${version}_UR_fidl.txt ${StudyFolder}/inbox/${CASE}_BT_UR.fidl
	fi

done


