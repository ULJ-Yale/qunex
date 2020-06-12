#!/bin/sh
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## COPYRIGHT NOTICE
#
# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
#
# ## AUTHORS(s)
#
# * Alan Anticevic, Department of Psychiatry, Yale University
#
# ## PRODUCT
#
# * SubjectsBatch.sh
#
# ## LICENSE
#
# * The SubjectsBatch.sh = the "Software"
# * This Software conforms to the license outlined in the Qu|Nex Suite:
# * https://bitbucket.org/oriadev/qunex/src/master/LICENSE.md
#
# ## TODO
#
# ## DESCRIPTION 
#
# Script to generate batch files
#
# ## PREREQUISITE INSTALLED SOFTWARE
#
# Qu|Nex Suite
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# N/A
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are subject-specific subject.txt param files
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
     echo ""
     echo "-- DESCRIPTION for SubjectsBatch"
     echo ""
     echo "This function generates a batch file for processing for a given subject."
     echo "It is designed to be invoked directly via Qu|Nex call:"
     echo ""
     echo "   > qunex createLists"
     echo ""
     echo "This script accepts the following mandatory paramaters:"
     echo ""
     echo "   --sessionsfolder=<folder_with_subjects>        Path to study folder that contains subjects"
     echo "   --subjects=<comma_separated_list_of_cases>  Subject to run"
     echo "   --outname=<output_name_of_the_batch>        Output name of the batch file to generate. "
     echo "   --outpath=<absolute_path_to_list_folder>    Path for the batch file"
     echo ""
     exit 0
}

# ------------------------------------------------------------------------------
# -- Setup color outputs
# ------------------------------------------------------------------------------

reho() {
    echo -e "\033[31m $1 \033[0m"
}

geho() {
    echo -e "\033[32m $1 \033[0m"
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]]; then
	usage
fi

# ------------------------------------------------------------------------------
# -- Parse and check all arguments
# ------------------------------------------------------------------------------

########### INPUTS ###############

	# -- Subject-specific subject_hcp.txt file 

########## OUTPUTS ###############

	# -- Info appended to the specified batch

# -- Get the command line options for this script

get_options() {

local scriptName=$(basename ${0})
local arguments=($@)

# -- Initialize global variables
unset SessionsFolder # --sessionsfolder=
unset CASE           # --subjects=
unset ListPath       # --outpath=
unset ListName       # --outname=
unset Overwrite      # --outname=
runcmd=""

# -- Parse arguments
local index=0
local numArgs=${#arguments[@]}
local argument
while [ ${index} -lt ${numArgs} ]; do
        argument=${arguments[index]}
        case ${argument} in
            --help)
                usage
                ;;
            --version)
                version_show $@
                exit 0
                ;;
            --sessionsfolder=*)
                SessionsFolder=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --subjects=*)
                CASE=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --outpath=*)
                ListPath=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --outname=*)
                ListName=${argument/*=/""}
                index=$(( index + 1 ))
                ;;
            --overwrite=*)
                Overwrite=${argument/*=/""}
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
echo ""

# -- Check general required parameters
if [ -z ${CASE} ]; then
    usage
    reho "ERROR: <subject_id> not specified."; echo ""
    exit 1
fi
if [ -z ${SessionsFolder} ]; then
    usage
    reho "ERROR: <subjects_folder> not specified."; echo ""
    exit 1
fi
if [ -z ${Overwrite} ]; then
    Overwrite="no"
    echo "Overwrite value not explicitly specified. Using default: ${Overwrite}"; echo ""
fi
if [ -z ${ListPath} ]; then
    ListPath="${SessionsFolder}/../processing/lists/"
    echo "Output folder path value not explicitly specified. Using default: ${ListPath}"; echo ""
fi
if [ -z ${ListName} ]; then 
    TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
    ListName="$TimeStamp"
    echo "Output name value not explicitly specified. Using default: ${ListName}"; echo ""
fi

# -- Set StudyFolder
cd $SessionsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null

# -- Report options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   SessionsFolder: ${SessionsFolder}"
echo "   Subject: ${CASE}"
echo "   Batch file name: ${ListName}"
echo "   Path to save output: ${ListPath}"
echo "   Overwrite: ${Overwrite}"
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""

}

######################################### DO WORK ##########################################

main() {

# -- Get Command Line Options
get_options $@

# -------------------------------------------------
# -- Set ListPath variable 
# -------------------------------------------------

# -- Check if path for the batch list is set
if [ -z "$ListPath" ]; then 
	unset ListPath
	mkdir -p "$StudyFolder"/processing/lists &> /dev/null
	cd ${StudyFolder}/processing/lists
	ListPath=`pwd`
	reho "Setting default path for list folder --> $ListPath"
fi

# -------------------------------------------------
# -- Code for generating batch files
# -------------------------------------------------
		
# -- Test if subject_hcp.txt is absent
if (test ! -f ${SessionsFolder}/${CASE}/subject_hcp.txt); then
	# -- Test if subject_hcp.txt is present
	if (test -f ${SessionsFolder}/${CASE}/subject.txt); then
		# -- If yes then copy it to subject_hcp.txt
		cp ${SessionsFolder}/${CASE}/subject.txt ${SessionsFolder}/${CASE}/subject_hcp.txt
	else
		# -- Report error and exit
		echo ""
		reho "${SessionsFolder}/${CASE}/subject_hcp.txt and subject.txt is missing."
		reho "Make sure you have sorted the dicoms and setup subject-specific files."
		reho "Note: These files are used to populate the batch.${ListName}.list"
		echo ""
		exit 1
	fi
fi
echo "List path is currently set to $ListPath"
echo "---" >> ${ListPath}/batch."$ListName".txt
cat ${SessionsFolder}/${CASE}/subject_hcp.txt >> ${ListPath}/batch."$ListName".txt
echo "" >> ${ListPath}/batch."$ListName".txt
# -- Fix paths stale or outdated paths
DATATYPES="dicom 4dfp hcp nii"
for DATATYPE in $DATATYPES; do
	CorrectPath="${SessionsFolder}/${CASE}/${DATATYPE}"
	GrepInput="/${CASE}/${DATATYPE}"
	ReplacePath=`more ${ListPath}/batch.${ListName}.txt | grep "$GrepInput" | awk '{print $2}'`
	sed -i "s@$ReplacePath@$CorrectPath@" ${ListPath}/batch.${ListName}.txt
done

echo " --> Appending $CASE to ${ListPath}/batch.${ListName}.txt completed."
echo ""

geho "--- Batch file appending successfully completed"
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
