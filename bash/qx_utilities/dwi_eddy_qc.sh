#!/bin/bash

# Copyright (C) 2015 Anticevic Lab, Yale University
# Copyright (C) 2015 MBLAB, University of Ljubljana
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
    cat << EOF
``dwi_eddy_qc``

This function is based on FSL's eddy to perform quality control on diffusion MRI
(dMRI) datasets. It explicitly assumes the that eddy has been run and that EDDY
QC by Matteo Bastiani, FMRIB has been installed.

For full documentation of the EDDY QC please examine the README file.

The function assumes that eddy outputs are saved in the following folder::

    <folder_with_sessions>/<session>/hcp/<session>/Diffusion/eddy/

Parameters:
    --sessionsfolder (str):
        Path to study folder that contains sessions.

    --session (str):
        Session ID to run EDDY QC on.

    --eddybase (str):
        This is the basename specified when running EDDY (e.g.
        eddy_unwarped_images)

    --eddyidx (str):
        EDDY index file.

    --eddyparams (str):
        EDDY parameters file.

    --mask (str):
        Binary mask file (most qc measures will be averaged across voxels
        labeled in the mask).

    --bvalsfile (str):
        bvals input file.

    --report (str, default 'individual'):
        If you want to generate a group report ('individual' or 'group').

    --overwrite (str):
        Delete prior run for a given session.

    --eddypath (str, default '<study_folder>/<session>/hcp/<session>/Diffusion/eddy/'):
        Specify the relative path of the eddy folder you want to use for inputs.

    --bvecsfile (str):
        If specified, the tool will create a bvals_no_outliers.txt and a
        bvecs_no_outliers.txt file that contain the bvals and bvecs of the
        non-outlier volumes, based on the MSR estimates,

    --list (str):
        Text file containing a list of qc.json files obtained from SQUAD. If
        --report='group', then this argument needs to be specified.

    --groupvar (str):
        Text file containing extra grouping variable. Extra optional input if
        --report='group'.

    --outputdir (str, default '<eddyBase>.qc'):
          Output directory. Extra optional input if --report='group'.

    --update (str):
        Applies only if --report='group' - set to <true> to update existing
        single session qc reports.

Output files:
    Outputs for individual run:

    - qc.pdf               ... single session QC report
    - qc.json              ... single session QC and data info
    - vols_no_outliers.txt ... text file that contains the list of the
      non-outlier volumes (based on eddy residuals)

    Outputs for group run:

    - group_qc.pdf ... single session QC report
    - group_qc.db  ... database

Examples:
    ::

        qunex dwi_eddy_qc \\
            --sessionsfolder='<path_to_study_folder_with_session_directories>' \\
            --session='<session_id>' \\
            --eddybase='<eddy_base_name>' \\
            --report='individual' \\
            --bvalsfile='<bvals_file>' \\
            --mask='<mask_file>' \\
            --eddyidx='<eddy_index_file>' \\
            --eddyparams='<eddy_param_file>' \\
            --bvecsfile='<bvecs_file>' \\
            --overwrite='yes'

EOF
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

################# CHECK eddy_squad and eddy_squad INSTALL ################################

# -- Check if eddy_squad and eddy_quad exist in user path
EddySquadCheck=`which eddy_squad`
EddyQuadCheck=`which eddy_quad`

if [ -z ${EddySquadCheck} ] || [ -z ${EddySquadCheck} ]; then
	echo ""
    reho " -- ERROR: EDDY QC does not seem to be installed on this system."
    echo ""
    exit 1
fi

# ------------------------------------------------------------------------------
#  -- Check if command line arguments are specified
# ------------------------------------------------------------------------------

########################################## INPUTS ########################################## 

# -- eddy-cleaned DWI Data

########################################## OUTPUTS #########################################

# -- Outputs will be located in <eddyBase>.qc per EDDY QC specification

# -- Get the command line options for this script
get_options() {

local scriptName=$(basename ${0})
local arguments=($@)

# -- Initialize global output variables
unset SessionsFolder
unset Session
unset Report
unset EddyBase
unset List
unset EddyIdx
unset EddyParams
unset Mask
unset BvalsFile

# -- Optional parameters
unset Overwrite
unset EddyPath
unset GroupVar
unset OutputDir
unset Update
unset BvecsFile

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
        --session=*)
            CASE=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --report=*)
            Report=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --eddybase=*)
            EddyBase=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --list=*)
            List=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
         --eddyidx=*)
            EddyIdx=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
         --eddyparams=*)
            EddyParams=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
         --mask=*)
            Mask=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
         --bvalsfile=*)
            BvalsFile=${argument/*=/""}
            index=$(( index + 1 ))
            ;; 
        --outputdir=*)
            OutputDir=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --eddypath=*)
            EddyPath=${argument/*=/""}
            index=$(( index + 1 ))
            ;;
        --update=*)
            Update=${argument/*=/""}
            index=$(( index + 1 ))
            ;;                
        --groupvar=*)
            GroupVar=${argument/*=/""}
            index=$(( index + 1 ))
            ;; 
        --overwrite=*)
            Overwrite=${argument/*=/""}
            index=$(( index + 1 ))
            ;;      
        --bvecsfile=*)
            BvecsFile=${argument/*=/""}
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

# -- Check required parameters
if [ -z ${SessionsFolder} ]; then
    usage
    reho "ERROR: <sessions-folder-path> not specified>"
    echo ""
    exit 1
fi
if [ -z ${Report} ]; then
    usage
    reho "ERROR: <report> type specified>"
    echo ""
    exit 1
fi
if [ ${Report} == "individual" ]; then
	# -- Check each individual parameter
	if [ -z ${CASE} ]; then
		usage
		reho "ERROR: <session-id> not specified>"
		echo ""
		exit 1
	fi
	if [ -z ${EddyBase} ]; then
		usage
		reho "ERROR: <eddy_base_name> not specified>"
		echo ""
		exit 1
	fi
	if [ -z ${BvalsFile} ]; then
		usage
		reho "ERROR: <bvals_file> not specified>"
		echo ""
		exit 1
	fi
	if [ -z ${EddyIdx} ]; then
		usage
		reho "ERROR: <eddy_index> file not specified>"
		echo ""
		exit 1
	fi
	if [ -z ${EddyParams} ]; then
		usage
		reho "ERROR: <eddy_params> file not specified>"
		echo ""
		exit 1
	fi
	if [ -z ${Mask} ]; then
		usage
		reho "ERROR: <mask> file not specified>"
		echo ""
		exit 1
	fi
fi
if [ ${Report} == "group" ]; then
	if [ -z ${List} ]; then
    	usage
    	reho "ERROR: <group_list_input> no specified>"
    	echo ""
    	exit 1
	fi
fi

# -- Check optional parameters
if [ -z ${Overwrite} ]; then
    Overwrite="no"
fi
if [ -z ${EddyPath} ]; then
    EddyPath="${SessionsFolder}/${CASE}/hcp/${CASE}/Diffusion/eddy"
    echo $EddyPath
fi
if [ -z ${GroupVar} ]; then
	GroupVar=""
fi
if [ -z ${OutputDir} ]; then
    OutputDir="${EddyPath}/${EddyBase}.qc"
fi
if [ -z ${Update} ]; then
    Update="false"
fi
if [ -z ${BvecsFile} ]; then
    BvecsFile=""
fi

# -- Set StudyFolder
cd $SessionsFolder/../ &> /dev/null
StudyFolder=`pwd` &> /dev/null

# -- Report parameters
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo "   SessionsFolder: ${SessionsFolder}"
echo "   Session: ${CASE}"
echo "   Report Type: ${Report}"
echo "   Eddy QC Input Path: ${EddyPath}"
echo "   Eddy QC Output Path: ${OutputDir}"
# -- Report group parameters
if [ ${Report} == "group" ]; then
echo "   List: ${List}"
echo "   Grouping Variable: ${GroupVar}"
echo "   Update single sessions: ${Update}"
echo ""
fi
# -- Report individual parameters
if [ ${Report} == "individual" ]; then
echo "   Eddy Inputs Base Name: ${EddyBase}"
echo "   Mask: ${EddyPath}/${Mask}"
echo "   BVALS file: ${EddyPath}/${BvalsFile}"
echo "   Eddy Index file: ${EddyPath}/${EddyIdx}"
echo "   Eddy parameter file: ${EddyPath}/${EddyParams}"
fi
# -- Report optional parameters
echo "   BvecsFile: ${EddyPath}/${BvecsFile}"
echo "   Overwrite: ${EddyPath}/${Overwrite}"
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""
}

######################################### DO WORK ##########################################

main() {

# -- Get Command Line Options
get_options $@

# -- Define inputs and output
echo "--- Establishing paths for all input and output folders:"
echo ""

# -- Define input path
EddyQCIn="$EddyPath"
# -- Define output path
EddyQCOut="$OutputDir"

echo "   DWI Eddy QC Input Path:              ${EddyQCIn}"
echo "   DWI Eddy QC Output Path:              ${EddyQCOut}"
echo ""

# -- Delete any existing output sub-directories
if [ "$Overwrite" == "yes" ]; then
	reho "--- Deleting prior QC runs for $CASE..."
	echo ""
	rm -rf ${EddyQCOut}> /dev/null 2>&1
fi

# -- Check if prior run exists
echo "--- Checking if QC was completed..."
echo ""
if [ -d ${EddyQCOut} ]; then
	geho "   ===> DWI EDDY QC folder found: ${EddyQCOut}"
	echo ""
	echo "   Use --overwrite='yes' if you want to re-run"
	echo ""
	exit 1
else
	reho "DWI EDDY QC folder not found."
	echo ""
	geho "Computing DWI EDDY QC using specified parameters..."
	echo ""
	# -- Check if individual run was selected
	if [ ${Report} == "individual" ]; then
		geho "Computing individual QC run on ${EddyQCIn} "
		EddyCommand="eddy_quad ${EddyQCIn}/${EddyBase} -idx ${EddyIdx} -par ${EddyParams} -m ${Mask} -b ${BvalsFile} -g ${BvecsFile} -o ${EddyQCOut}"
		echo ""
		echo $EddyCommand
		echo ""
		eval $EddyCommand
		echo ""
		cat ${EddyQCOut}/qc.json | grep "qc_mot_abs" | sed -n -e 's/^.*: //p' | tr -d ',' >> ${EddyQCOut}/${CASE}_qc_mot_abs.txt
	fi
	echo ""
	# -- Check if group run was selected
	if [ ${Report} == "group" ]; then
		geho "Computing group QC run on ${EddyQCIn} "
		EddyCommand="eddy_squad ${EddyQCIn}/${EddyBase} -list ${List} -var ${GroupVar} -upd ${Update} -o {$EddyQCOut}"
		echo ""
		echo $EddyCommand
		echo ""
		eval $EddyCommand
		echo ""
	fi
	echo ""
fi

# -- Perform completion checks
echo "--- Checking DWI EDDY QC outputs..."
echo ""
if [ -f ${EddyQCOut}/qc.json ]; then
	OutFile="${EddyQCOut}/qc.json"
	geho "QC output file found:           $OutFile"
	echo ""
else
	reho "QC output file ${EddyQCOut}/qc.json missing. Something went wrong."
	echo ""
	exit 1
fi

if [ -f ${EddyQCOut}/${CASE}_qc_mot_abs.txt ]; then
	OutFile="${EddyQCOut}/${CASE}_qc_mot_abs.txt"
	geho "QC absolute motion value file found:           $OutFile"
	echo ""
else
	reho "QC absolute motion value file ${EddyQCOut}/${CASE}_qc_mot_abs.txt is missing. Something went wrong."
	echo ""
	exit 1
fi

geho "--- DWI EDDY QC successfully completed"
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
