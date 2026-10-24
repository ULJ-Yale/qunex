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

Run quality control on diffusion MRI (dMRI) datasets based on FSL's eddy.

Warning:
    The command  assumes that eddy has been run and that EDDY QC by Matteo Bastiani,
    FMRIB has been installed.

    For full documentation of the EDDY QC please examine the README file.

    The function assumes that eddy outputs are saved in the following folder::

        <sessionsfolder>/<session>/hcp/<session>/Diffusion/eddy/

    This can be changed with the --eddypath argument, in this case eddypath should
    point to the folder that holds the eddy outputs.

..  qx_command:
    type: processing.session
    language: bash    

Parameters:
    --studyfolder (str):
        The path to the study folder. The sessions are in its ``sessions``
        folder, unless --sessionsfolder names another one.

    --sessionsfolder (str, default '<studyfolder>/sessions'):
        The path to the folder with the sessions. Set it only when the
        sessions are not in the ``sessions`` folder of the study. One of
        --studyfolder and --sessionsfolder has to be given.

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

    --report (str):
        The type of report to generate ('individual' or 'group').

    --overwrite (str, default 'no'):
        Whether to overwrite existing data (yes) or not (no). Note that
        previous data is deleted before the run, so in the case of a failed
        command run, previous results are lost.

    --eddypath (str, default '<sessionsfolder>/<session>/hcp/<session>/Diffusion/eddy/'):
        Specify the path of the eddy folder you want to use for inputs. A
        relative path is taken relative to the session's
        ``<sessionsfolder>/<session>/hcp/<session>`` folder.

    --bvecsfile (str):
        If specified, the tool will create a bvals_no_outliers.txt and a
        bvecs_no_outliers.txt file that contain the bvals and bvecs of the
        non-outlier volumes, based on the MSR estimates,

    --list (str):
        Text file listing the single session QC folders (the output folders
        of the individual runs), one per line. If --report='group', then this
        argument needs to be specified.

    --groupvar (str):
        Text file containing extra grouping variable. Extra optional input if
        --report='group'.

    --outputdir (str, default '<eddypath>/<eddybase>.qc'):
        Output directory. Required for a group run: the default is the folder
        of the session's individual run.

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

    - group_qc.pdf   ... group QC report
    - group_db.json  ... database

Notes:
    -  Input: requires hcp_diffusion runs (eddy outputs here:
       ``<sessionsfolder>/<session>/hcp/<session>/Diffusion/eddy``) and
       hcp_pre_freesurfer-hcp_post_freesurfer to have run successfully
    -  Output for individual run:
       ``<sessionsfolder>/<session>/hcp/<session>/Diffusion/eddy/<eddybase>.qc``

       -  qc.pdf: single session QC report
       -  qc.json: single session QC and data info
       -  vols_no_outliers.txt: text file that contains the list of the
          non-outlier volumes (based on eddy residuals)

    -  Output for group run: the folder given with ``--outputdir``

       -  group_qc.pdf: group QC report
       -  group_db.json: database

    -  Log Location: logs are created in the study's ``logs`` folder,
       ``<studyfolder>/logs/<timestamp>_dwi_eddy_qc``

       -  Run progress and error information will be logged in this folder

Examples:
    ::

        qunex dwi_eddy_qc \\
            --studyfolder='<path_to_study_folder>' \\
            --session='<session_id>' \\
            --eddybase='<eddy_base_name>' \\
            --report='individual' \\
            --bvalsfile='<bvals_file>' \\
            --mask='<mask_file>' \\
            --eddyidx='<eddy_index_file>' \\
            --eddyparams='<eddy_param_file>' \\
            --bvecsfile='<bvecs_file>' \\
            --overwrite='yes'

    Individual run example (this command runs QC on dMRI eddy outputs)::

        qunex dwi_eddy_qc \\
            --studyfolder='<path_to_study_folder>' \\
            --session='<session_id>' \\
            --eddybase='<eddy_base_name>' \\
            --report='individual' \\
            --bvalsfile='<bvals_file>' \\
            --mask='<mask_file>' \\
            --eddyidx='<eddy_index_file>' \\
            --eddyparams='<eddy_param_file>' \\
            --bvecsfile='<bvecs_file>' \\
            --overwrite='yes' \\
            --scheduler='<name_of_scheduler_and_options>'

    Group run example (this command runs QC on dMRI eddy outputs)::

        qunex dwi_eddy_qc \\
            --studyfolder='<path_to_study_folder>' \\
            --list='<group_list_input>' \\
            --report='group' \\
            --outputdir='<group_output_folder>' \\
            --scheduler='<name_of_scheduler_and_options>'


EOF
exit 0
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

if [ -z "${EddySquadCheck}" ] || [ -z "${EddyQuadCheck}" ]; then
    echo ""
    echo " -- ERROR: EDDY QC does not seem to be installed on this system."
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
unset StudyFolder
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
        --studyfolder=*)
            StudyFolder=${argument/*=/""}
            index=$(( index + 1 ))
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
            echo "ERROR: Unrecognized Option: ${argument}"
            echo ""
            exit 1
            ;;
    esac
done

# the sessions are in the sessions folder of the study, unless --sessionsfolder
# names another one
if [ -z "${SessionsFolder}" ] && [ -n "${StudyFolder}" ]; then
    SessionsFolder="${StudyFolder}/sessions"
fi

# -- Check required parameters
if [ -z "${SessionsFolder}" ]; then
    echo "ERROR: Neither --studyfolder nor --sessionsfolder specified"
    echo ""
    exit 1
fi
if [ -z ${Report} ]; then
    echo "ERROR: <report> type not specified"
    echo ""
    exit 1
fi
if [ ${Report} != "individual" ] && [ ${Report} != "group" ]; then
    echo "ERROR: Unknown <report> type ${Report}, use 'individual' or 'group'"
    echo ""
    exit 1
fi
if [ ${Report} == "individual" ]; then
    # -- Check each individual parameter
    if [ -z ${CASE} ]; then
        echo "ERROR: <session-id> not specified"
        echo ""
        exit 1
    fi
    if [ -z ${EddyBase} ]; then
        echo "ERROR: <eddy_base_name> not specified"
        echo ""
        exit 1
    fi
    if [ -z ${BvalsFile} ]; then
        echo "ERROR: <bvals_file> not specified"
        echo ""
        exit 1
    fi
    if [ -z ${EddyIdx} ]; then
        echo "ERROR: <eddy_index> file not specified"
        echo ""
        exit 1
    fi
    if [ -z ${EddyParams} ]; then
        echo "ERROR: <eddy_params> file not specified"
        echo ""
        exit 1
    fi
    if [ -z ${Mask} ]; then
        echo "ERROR: <mask> file not specified"
        echo ""
        exit 1
    fi
fi
if [ ${Report} == "group" ]; then
    if [ -z ${List} ]; then
        echo "ERROR: <group_list_input> not specified"
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
else
    # --eddypath is documented as the relative path of the eddy folder, and
    # this is where it is relative to; the shell front end resolved it here
    case ${EddyPath} in
        /*) ;;
        *) EddyPath="${SessionsFolder}/${CASE}/hcp/${CASE}/${EddyPath}" ;;
    esac
fi
if [ -z ${GroupVar} ]; then
    GroupVar=""
fi
# the default is the folder of an individual run, which a group run would
# either stop at or, with --overwrite, delete
if [ -z "${OutputDir}" ] && [ ${Report} == "group" ]; then
    echo "ERROR: <outputdir> not specified, a group run needs one"
    echo ""
    exit 1
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
echo "   Mask: ${Mask}"
echo "   BVALS file: ${BvalsFile}"
echo "   Eddy Index file: ${EddyIdx}"
echo "   Eddy parameter file: ${EddyParams}"
fi
# -- Report optional parameters
echo "   BvecsFile: ${BvecsFile}"
echo "   Overwrite: ${Overwrite}"
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
echo "------------------------- Start of work --------------------------------"
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
    echo "--- Deleting prior QC runs for $CASE..."
    echo ""
    rm -rf ${EddyQCOut}> /dev/null 2>&1
fi

# -- Check if prior run exists
echo "--- Checking if QC was completed..."
echo ""
if [ -d ${EddyQCOut} ]; then
    echo "   ---> DWI EDDY QC folder found: ${EddyQCOut}"
    echo ""
    echo "   Use --overwrite='yes' if you want to re-run"
    echo ""
    exit 1
else
    echo "DWI EDDY QC folder not found."
    echo ""
    echo "Computing DWI EDDY QC using specified parameters..."
    echo ""
    # -- Check if individual run was selected
    if [ ${Report} == "individual" ]; then
        echo "Computing individual QC run on ${EddyQCIn} "
        EddyCommand="eddy_quad ${EddyQCIn}/${EddyBase} -idx ${EddyIdx} -par ${EddyParams} -m ${Mask} -b ${BvalsFile}"
        # the bvecs are optional, and an empty -g would take -o for its value
        if [ -n "${BvecsFile}" ]; then
            EddyCommand="${EddyCommand} -g ${BvecsFile}"
        fi
        EddyCommand="${EddyCommand} -o ${EddyQCOut}"
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
        echo "Computing group QC run on ${List} "
        # eddy_squad takes the list of single session qc folders as its
        # argument, the grouping variable and the update request are optional
        EddyCommand="eddy_squad ${List}"
        if [ -n "${GroupVar}" ]; then
            EddyCommand="${EddyCommand} -g ${GroupVar}"
        fi
        if [ "${Update}" == "true" ] || [ "${Update}" == "yes" ]; then
            EddyCommand="${EddyCommand} -u"
        fi
        EddyCommand="${EddyCommand} -o ${EddyQCOut}"
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
if [ ${Report} == "group" ]; then
    # a group run writes the group report, not the single session files
    if [ -f ${EddyQCOut}/group_qc.pdf ]; then
        OutFile="${EddyQCOut}/group_qc.pdf"
        echo "Group QC report found:           $OutFile"
        echo ""
    else
        echo "Group QC report ${EddyQCOut}/group_qc.pdf missing. Something went wrong."
        echo ""
        exit 1
    fi
else
    if [ -f ${EddyQCOut}/qc.json ]; then
        OutFile="${EddyQCOut}/qc.json"
        echo "QC output file found:           $OutFile"
        echo ""
    else
        echo "QC output file ${EddyQCOut}/qc.json missing. Something went wrong."
        echo ""
        exit 1
    fi

    if [ -f ${EddyQCOut}/${CASE}_qc_mot_abs.txt ]; then
        OutFile="${EddyQCOut}/${CASE}_qc_mot_abs.txt"
        echo "QC absolute motion value file found:           $OutFile"
        echo ""
    else
        echo "QC absolute motion value file ${EddyQCOut}/${CASE}_qc_mot_abs.txt is missing. Something went wrong."
        echo ""
        exit 1
    fi
fi

echo "--- DWI EDDY QC successfully completed"
echo ""
echo "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
