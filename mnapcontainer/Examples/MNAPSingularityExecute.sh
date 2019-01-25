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
# * The MNAPSingularityExecute.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ### TODO
#
#
# ## Description 
#   
# This script, MNAPSingularityExecute.sh runs the script that MNAP Singularity 
#  then executes inside the container
# 
# ## Prerequisite Installed Software
#
# * MNAP Suite Singularity Container
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. bash MNAPSingularityExecute.sh --help
#
# ### Expected Previous Processing
# 
#
#~ND~END~

usage() {
    echo ""
    echo "  -- DESCRIPTION:"
    echo ""
    echo "  This function implements the execution of the code to be executed inside the MNAP Singularity container."
    echo "  To run this the user would edit the code inside this script, which gets passed to the MNAP Singularity container."
    echo ""
    exit 0
}

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]] || [[ $1 == "help" ]] || [[ $1 == "usage" ]]; then
    usage
fi

# ------------------------------------------------------------------------------
# -- Ensure MNAP environment is sourced upon container execution
# ------------------------------------------------------------------------------

# -- Paths to MNAP environment script inside the container
source /opt/mnaptools/library/environment/mnap_environment.sh

# ------------------------------------------------------------------------------
# -- User can adjust the code below ==> 
# ------------------------------------------------------------------------------

# ~~~~ Users adjust as needed to point to code for MNAP Singularity to run ~~~~~
#

export FSLDIR="/opt/fsl/fsl-5.0.9"
export PATH=${FSLDIR}:${FSLDIR}/bin:${PATH}
TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
ScriptFolder="/gpfs/project/fas/n3/software/mnaptools/mnapcontainer/Examples/"
StudyFolder="/gpfs/project/fas/n3/Studies/HCPLSOutput_$TimeStamp"
InputFolder="/gpfs/project/fas/n3/Studies/HCPLSImport/input"
export PATH=${InputFolder}:${StudyFolder}:${ScriptFolder}:${PATH}

bash ${ScriptFolder}/MNAPHCPScript.sh \
--studyfolder="${StudyFolder}" \
--subjects="HCA1234567,HCA7654321" \
--hcpdatapath="${InputFolder}" \
--parameterfile="${InputFolder}/batch_parameters.txt" \
--fsldir="${FSLDIR}" \
--overwrite="yes"

#
# ~~~~ Users adjust as needed to point to code for MNAP Singularity to run ~~~~~
