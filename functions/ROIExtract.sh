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
# * Charles Scheleifer, Department of Psychiatry, Yale University
#
# ## PRODUCT
#
# Wrapper to run MATLAB function to extract ROIs from input file based on template file (extractROIsFromTemplate.m)
#
# ## LICENCE
#
# * The ROIExtract.sh = the "Software"
# * This Software conforms to the license outlined in the MNAP Suite:
# * https://bitbucket.org/hidradev/mnaptools/src/master/LICENSE.md
#
# ## TODO
#
# ## DESCRIPTION 
#   
# This script, ROIExtract.sh, implements ROI extraction
# using a pre-specified ROI file in NIFTI or CIFTI format
# 
# ## PREREQUISITE INSTALLED SOFTWARE
#
# * MNAP Suite
#
# ## PREREQUISITE ENVIRONMENT VARIABLES
#
# See output of usage function: e.g. $./ROIExtract.sh --help
#
# ## PREREQUISITE PRIOR PROCESSING
# 
# * The necessary input files are imaging data from previous processing and ROI file
#
#~ND~END~

# ------------------------------------------------------------------------------
# -- General help usage function
# ------------------------------------------------------------------------------

usage() {
   echo ""
   echo " -- DESCRIPTION:"
   echo ""
   echo " This function calls mri_ROIExtract.m and extracts data from an input file for every ROI in a given template file."
   echo " The function needs a matching file type for the ROI input and the data input (i.e. both NIFTI or CIFTI)."
   echo " It assumes that the template ROI file indicates each ROI in a single volume via unique scalar values."
   echo ""
   echo ""
   echo " -- REQUIRED PARMETERS:"
   echo ""
   echo "    --roifile=<filepath>      Path ROI file (either a NIFTI or a CIFTI with distinct scalar values per ROI)"
   echo "    --inputfile=<filepath>    Path to input file to be read that is of the same type as --roifile (i.e. CIFTI or NIFTI)"
   echo "    --outpath=<path>          New or existing directory to save outputs in"
   echo "    --outname=<basename>      Output file base-name (to be appended with 'ROIn')"
   echo ""
   echo "-- OUTPUT FORMAT:"
   echo ""
   echo "<output_name>.csv      --> matrix with one ROI per row and one column per frame in singleinputfile "
   echo ""
   echo " -- Example:"
   echo ""
   echo " ROIExtract.sh "
   echo "--roifile='<path_to_roifile>' "
   echo "--inputfile='<path_to_inputfile>' "
   echo "--outdir='<path_to_outdir>' "
   echo "--outname='<output_name>'"
   echo ""
   exit 0
}

# ------------------------------------------------------------------------------
# -- Setup color outputs
# ------------------------------------------------------------------------------

reho() { echo -e "\033[31m $1 \033[0m"; }
geho() { echo -e "\033[32m $1 \033[0m"; }

# ------------------------------------------------------------------------------
# -- Check for help
# ------------------------------------------------------------------------------

if [[ $1 == "" ]] || [[ $1 == "--help" ]] || [[ $1 == "-help" ]] || [[ $1 == "--usage" ]] || [[ $1 == "-usage" ]]; then
	usage
fi
# ------------------------------------------------------------------------------
# -- Parse arguments
# ------------------------------------------------------------------------------

# -- Get flagged arguments
get_options() {

local scriptName=$(basename ${0})
local arguments=($@)

# -- Initialize global output variables
unset roifile
unset inputfile
unset outpath
unset outname
runcmd=""

# -- parse arguments
local index=0
local numArgs=${#arguments[@]}
local argument
while [ ${index} -lt ${numArgs} ]; do
	argument=${arguments[index]}
	case ${argument} in
		--help)
			usage
			;;
		--roifile=*)
			roifile=${argument/*=/""};   index=$(( index + 1 ))
			;;
		--inputfile=*)
			inputfile=${argument/*=/""}; index=$(( index + 1 ))
			;;
		--outpath=*)
			outpath=${argument/*=/""};    index=$(( index + 1 ))
			;;
		--outname=*)
			outname=${argument/*=/""};   index=$(( index + 1 ))
			;;
		*)
			usage; echo ""; reho "ERROR: Unrecognized Option: ${argument}"; echo ""
			exit 1
			;;
	esac
done

# -- Check required parameters and set defaults
if [ -z ${roifile} ]; then
	usage; echo ""; reho "ERROR: --roifile=<path to roi file> not specified>"; echo ""
	exit 1
fi
if [ -z ${inputfile} ]; then
	usage; echo ""; reho "ERROR: --inputfile=<path to file to be extracted> not specified>"; echo ""
	exit 1
fi
if [ -z ${outpath} ]; then
	usage; echo ""; reho "ERROR: --outdir=<path to output directory> not specified>"; echo ""
	exit 1
fi
if [ -z ${outname} ]; then
	usage; echo ""; reho "ERROR: --outname=<output file basename> not specified>"; echo ""
	exit 1
fi

# -- Report options
echo ""
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - Start --"
echo ""
echo "   roifile: ${roifile}"
echo "   inputfile: ${inputfile}"
echo "   outpath: ${outpath}"
echo "   outname: ${outname}"
echo ""
echo "-- ${scriptName}: Specified Command-Line Options - End --"
echo ""
geho "------------------------- Start of work --------------------------------"
echo ""

}

######################################### DO WORK #############################################

main() {

# -- Get Command Line Options
get_options $@

# -- Run mri_ExtractROI.m --> mri_ExtractROI(obj, roi, rcodes, method, weights, criterium)
${MNAPMCOMMAND} "imgf=gmrimage('$inputfile'); roif=gmrimage('$roifile'); csvwrite(strcat('$outpath','/','$outname','.csv'), imgf.mri_ExtractROI(roif)); quit"

geho "-- ROIExtract successfully completed "
echo ""
geho "------------------------- Successful completion of work --------------------------------"
echo ""

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
