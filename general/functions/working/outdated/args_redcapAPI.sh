#!/bin/sh


# RedCap data will be exported to into a csv file in $outpath
outpath=/gpfs/project/fas/n3/software/MNAP/general/functions/working
mkdir ${outpath}/RedCapExport
outpath=${outpath}/RedCapExport

# if desired, append a suffix to output filename (automatically named 'RedCapExport_<content>_$suffix.csv')
suffix=''        
if [ ! -z ${suffix} ]; then 
	suffix="_${suffix}"
fi
	                
# check if user-specific API token exists.
## API token must be initially created through RedCap web client (https://poa-redcap.med.yale.edu/redcap_v6.17.2/) 
token_api=$(cat ~/.redcapAPI/APItoken)	
if [ -z ${token_api} ]; then
	echo "ERROR: API token not found in ~/.redcapAPI/APItoken "
	echo ""
	exit 1
fi

# set up function to call run_redcapAPI.php with arguments. writes output to ${outpath}/${outfile}
APIRequest(){ 
	if [ $rawOrLabel_api = 'label' ] && [ $content_api = 'record' ]; then
		label='_labels'
	else 
		label=''
	fi
	outfile="RedCapExport_all_${content_api}${label}${suffix}.csv"
	php -f export_redcapAPI.php ${token_api} ${content_api} ${format_api} ${type_api} ${rawOrLabel_api} ${rawOrLabelHeaders_api} > ${outpath}/${outfile}
}

# basic arguments for data request
format_api='csv'              # csv (default), json, xml
type_api='null'               # 'null' defaults to 'flat' for record exports (one record per row). 'eav' outputs one item per row
rawOrLabelHeaders_api='raw'   # chose 'raw' ('labels' may interfere with subsequent parsing of output)

# export all records (raw data)
content_api='record'
rawOrLabel_api='raw'
APIRequest

# export all records (data labels)
content_api='record'
rawOrLabel_api='label'
APIRequest

# export data dictionary (to more easily match fields to forms)
content_api='metadata'
rawOrLabel_api='null'
APIRequest

# export event mapping (to match forms to events)
content_api='formEventMapping'
rawOrLabel_api='null'
APIRequest


