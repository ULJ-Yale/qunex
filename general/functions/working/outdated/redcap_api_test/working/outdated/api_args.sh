#!/bin/sh

set -x

#set all output to placeholder 'NULL'
token_api=NULL
content_api=NULL
format_api=NULL
type_api=NULL
records_api=NULL
fields_api=NULL
forms_api=NULL
events_api=NULL
rawOrLabel_api=NULL
rawOrLabelHeaders_api=NULL
exportCheckboxLabel_api=NULL
returnFormat_api=NULL
exportSurveyFields_api=NULL
exportDataAccessGroups_api=NULL
filterLogic_api=NULL

#populate variables
token_api=$(cat redcap_api_token)
content_api='record'
format_api='csv'
type_api='flat'
records_api=NULL
fields_api=NULL
forms_api='blackthorn_fmri'
events_api='4_blackthorn_arm_1'
rawOrLabel_api='raw'
rawOrLabelHeaders_api='raw'
exportCheckboxLabel_api=NULL
returnFormat_api=NULL
exportSurveyFields_api=NULL
exportDataAccessGroups_api=NULL
filterLogic_api=NULL

if [ -z ${token_api} ]; then
        usage
        reho "ERROR: ~/.redcap_api_token not specified>"
        echo ""
        exit 1
fi

# export redcap data with options
php redcap_api_test.php ${token_api} ${content_api} ${format_api} ${type_api} ${records_api} ${fields_api} ${forms_api} ${events_api} ${rawOrLabel_api} ${rawOrLabelHeaders_api} ${exportCheckboxLabel_api} ${returnFormat_api} ${exportSurveyFields_api} ${exportDataAccessGroups_api} ${filterLogic_api}

