#!/bin/sh
#
#~ND~FORMAT~MARKDOWN~
#~ND~START~
#
# ## Copyright Notice
#
# Copyright (C)
#
# * Yale University
#
# ## Author(s)
#
# * Charles Scheleifer, N3 Division, Yale University
# * Alan Anticevic, N3 Division, Yale University
#
# ## Product
#
# Wrapper to run MATLAB function to extract ROIs from input file based on template file (extractROIsFromTemplate.m)
#
# ## License
#
# * The ROIExtract.sh = the "Software"
# * This Software is distributed "AS IS" without warranty of any kind, either 
# * expressed or implied, including, but not limited to, the implied warranties
# * of merchantability and fitness for a particular purpose.
#
# ### TODO
#
# ## Description 
#   
# This script, ROIExtract.sh, implements ROI extraction
# using a pre-specified ROI file in NIFTI or CIFTI format
# 
# ## Prerequisite Installed Software
#
# * MNAP
#
# ## Prerequisite Environment Variables
#
# See output of usage function: e.g. $./ROIExtract.sh --help
#
# ### Expected Previous Processing
# 
# * The necessary input files are data from previous processing and ROI file
#
#~ND~END~

# Usage function
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
	echo "    --roifile=<filepath>		Path ROI file (either a NIFTI or a CIFTI with distinct scalar values per ROI)"
	echo "    --inputfile=<filepath>	Path to input file to be read that is of the same type as --roifile (i.e. CIFTI or NIFTI)"
	echo "    --outdir=<path>			New or existing directory to save outputs in"
	echo "    --outname=<basename>		Output file base-name (to be appended with 'ROIn')"
	echo ""
	echo "-- OUTPUT FORMAT:"
	echo ""
	echo "<output_name>_ROI#.csv		-- Value for each voxel or gray-ordinate in the ROI."
	echo "<output_name>_ROI#_mean.csv	-- Average across the entire ROI."
	echo "Note: if the data have multiple volumes / frames (e.g. >1 subject or >1 time point)"
	echo "		then each subsequent volume is written as a column in the csv files."
	echo ""
	echo " -- Example:"
	echo ""
	echo " ROIExtract.sh "
	echo "    --roifile='<path_to_roifile>' "
	echo "    --inputfile='<path_to_inputfile>' "
	echo "    --outdir='<path_to_outdir>' "
	echo "    --outname='<output_name>'"
	echo ""
			
}

# Setup color outputs
reho() { echo -e "\033[31m $1 \033[0m"; }
geho() { echo -e "\033[32m $1 \033[0m"; }

# Get flagged arguments
get_options() {
    local scriptName=$(basename ${0})
    local arguments=($@)

    # initialize global output variables
    unset roifile
	unset inputfile
	unset outdir
	unset outname
	runcmd=""

    # parse arguments
    local index=0
    local numArgs=${#arguments[@]}
    local argument
    while [ ${index} -lt ${numArgs} ]; do
        argument=${arguments[index]}

        case ${argument} in
            --help)
                usage
                exit 1
                ;;
            --roifile=*)
                roifile=${argument/*=/""};   index=$(( index + 1 ))
                ;;
            --inputfile=*)
                inputfile=${argument/*=/""}; index=$(( index + 1 ))
                ;;
			--outdir=*)
				outdir=${argument/*=/""};    index=$(( index + 1 ))
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

    #======= check required parameters and set defaults =======
    if [ -z ${roifile} ]; then
        usage; echo ""; reho "ERROR: --roifile=<path to roi file> not specified>"; echo ""
        exit 1
    fi
	if [ -z ${inputfile} ]; then
		usage; echo ""; reho "ERROR: --inputfile=<path to file to be extracted> not specified>"; echo ""
        exit 1
	fi
	if [ -z ${outdir} ]; then
		usage; echo ""; reho "ERROR: --outdir=<path to output directory> not specified>"; echo ""
        exit 1
	fi
	if [ -z ${outname} ]; then
		usage; echo ""; reho "ERROR: --outname=<output file basename> not specified>"; echo ""
        exit 1
	fi
    
    # report options
    echo ""
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - Start --"
    echo ""
    echo "   roifile: ${roifile}"
    echo "   inputfile: ${inputfile}"
    echo "   outdir: ${outdir}"
    echo "   outname: ${outname}"
    echo ""
    echo "-- ${scriptName}: Specified Command-Line Options - End --"
    echo ""
    geho "------------------------- Start of work --------------------------------"
    echo ""
}


######################################### DO WORK #############################################



main() {

# Get Command Line Options
get_options $@

# run ROIExtract.m

#matlab -nodisplay -nojvm -r "try; addpath(genpath('$TOOLS/MNAP/matlab')); mri_ROIExtract('$roifile','$inputfile','$outdir','$outname'); catch; end; quit"


matlab -nodisplay -nojvm -r "imgf=gmrimage('$inputfile'); roif=gmrimage('$roifile'); csvwrite(strcat('$outdir','/','$outname','.csv'), imgf.mri_ExtractROI(roif)); quit"


}
main $@
