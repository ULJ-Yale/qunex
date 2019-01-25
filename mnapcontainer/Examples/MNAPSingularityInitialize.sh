#!/bin/bash
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
# * Grega Repovs, MBLab, University of Ljubljana
# * Alan Anticevic, N3 Division, Yale University
# * Zailyn Tamayo, N3 Division, Yale University 
#
# ## PRODUCT
#
#  MNAPSingularityExecute.sh
#
# ## LICENSE
#
# * The MNAPSingularityInitialize.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ### TODO
#
#
# ## Description 
#   
# This script, MNAPSingularityInitialize.sh runs MNAP Singularity container 
#  pointing to code that executes the environment and calls the final code 
#  that should be executed inside the container
# 
# ## Prerequisite Installed Software
#
# * MNAP Suite Singularity Container
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. bash MNAPSingularityInitialize.sh --help
#
# ### Expected Previous Processing
# 
#
#~ND~END~

usage() {
    echo ""
    echo "  -- DESCRIPTION:"
    echo ""
    echo "  This function implements the initialization of the MNAP Singularity container execution."
    echo ""
    echo ""
    echo "  --containerpath=<Path to container image>                      The location for the container image."
    echo "  --mnapexecscript=<MNAP container execute script location>      Location of the MNAP execute script."
    echo " "
    echo "   -- Command to execute the shell script locally via MNAP:"
    echo " "
    echo "   <path to this script>/MNAPSingularityInitialize.sh --containerpath=<Path of the study folder> --scriptpath=<data location> "
    echo " "    
    exit 0
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]] || [[ $1 == "help" ]] || [[ $1 == "usage" ]]; then
    usage
fi

# ------------------------------------------------------------------------------
# -- Check for options
# ------------------------------------------------------------------------------

opts_GetOpt() {
sopt="$1"
shift 1
for fn in "$@" ; do
    if [ `echo $fn | grep -- "^${sopt}=" | wc -w` -gt 0 ]; then
        echo $fn | sed "s/^${sopt}=//"
        return 0
    fi
done
}

# =-=-=-=-=-= GENERAL OPTIONS =-=-=-=-=-=
#
# -- key variables to set
#
MNAPContainerPath=`opts_GetOpt "--containerpath" $@`
MNAPScriptPath=`opts_GetOpt "--mnapexecscript" $@`

# -- Setup paths for scripts folder and container

if [[ -z ${MNAPScriptPath} ]]; then reho "  --> Error: The location of the MNAP execute script path is missing."; exit 1; echo ''; fi
if [[ -z ${MNAPContainerPath} ]]; then reho "  --> Error: The location of the MNAP Singularity image input is missing."; exit 1; echo ''; fi

PATH=${MNAPContainerPath}:${MnapScriptPath}:${PATH}
export MnapScriptPath MNAPContainerPath PATH

# -- Execute container with /MNAP_Singularity.sh, which points to code to run inside container
echo ""
echo " -- Executing container image ${MNAPContainerPath} with script: ${MNAPScriptPath}"
echo ""
singularity exec ${MNAPContainerPath} bash ${MNAPScriptPath}

