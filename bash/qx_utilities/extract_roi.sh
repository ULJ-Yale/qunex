#!/bin/bash -eu

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
``extract_roi``

This function calls img_roi_extract.m and extracts data from an input file for
every ROI in a given template file. The function needs a matching file type for
the ROI input and the data input (i.e. both NIFTI or CIFTI). It assumes that
the template ROI file indicates each ROI in a single volume via unique scalar
values.

Parameters:
    --roifile (str):
        Path ROI file (either a NIFTI or a CIFTI with distinct scalar values per
        ROI).

    --inputfile (str):
        Path to input file to be read that is of the same type as --roifile
        (i.e. CIFTI or NIFTI).

    --outpath (str):
        New or existing directory to save outputs in.

    --outname (str):
        Output file base-name (to be appended with 'ROIn').

Output files:
    <output_name>.csv
       Matrix with one ROI per row and one column per frame in
       singleinputfile.

Examples:
    ::

        qunex roi_extract \\
            --roifile='<path_to_roifile>' \\
            --inputfile='<path_to_inputfile>' \\
            --outdir='<path_to_outdir>' \\
            --outname='<output_name>'

EOF
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
echo "   ROI file: ${roifile}"
echo "   Input file: ${inputfile}"
echo "   Output path: ${outpath}"
echo "   Output name: ${outname}"
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

# -- Run img_extract_roi.m --> img_extract_roi(obj, roi, rcodes, method, weights, criterium)
cmd="imgf=nimage('$inputfile'); roif=nimage('$roifile'); csvwrite(strcat('$outpath','/','$outname','.csv'), imgf.img_extract_roi(roif)); quit"
echo ${QUNEXMCOMMAND}
echo $cmd
${QUNEXMCOMMAND} "imgf=nimage('$inputfile'); roif=nimage('$roifile'); csvwrite(strcat('$outpath','/','$outname','.csv'), imgf.img_extract_roi(roif)); quit"

# -- Completion check
if [[ -f ${outpath}/${outname}.csv ]]; then
   echo ""
   geho "------------------------- Successful completion of work --------------------------------"
   echo ""
else
    reho "------------------------- ERROR --------------------------------"
    echo ""
    reho "   roi_extract generation did not complete correctly."
    echo ""
    reho "----------------------------------------------------------------"
fi

}

# ---------------------------------------------------------
# -- Invoke the main function to get things started -------
# ---------------------------------------------------------

main $@
