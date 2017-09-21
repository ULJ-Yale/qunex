#!/bin/sh

Study="" # Anticevic.DP5 BlackThorn Longitudinal.R01
CASES=""
App="Mindstrong"
#today=`date +%Y-%m-%d.%H:%M`

# Transfer first to data drop, then rsync to subject's dir

for CASE in ${CASES}; do
	mkdir /gpfs/project/fas/n3/${Study}/Anticevic.DP5/subjects/{CASES}/digpheno/
	mkdir /gpfs/project/fas/n3/${Study}/Anticevic.DP5/subjects/{CASES}/digpheno/${App}
	# Have session folder (for each day), date stamp MM-DD-YYYY... but will want this to be date collected not date transfer files created. 
	# mkdir /gpfs/project/fas/n3/${Study}/Anticevic.DP5/subjects/{CASES}/digpheno/${App}/${today}
done


# Push to REDCap