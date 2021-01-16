#!/bin/bash
#   Automated probabilistic tractography plugin for FSL; visualisation script.


Usage() {
cat << EOF

Usage: Prepare_for_Display <AutoPtx_ResultsDir> <threshold> <binarise_flag>

    If binarise_flag is 1, then generates binary masks for each structure, and prepares a
    call to display the tracts in FSLView.

    <threshold> is used to binarise the normalised tract density images. As a
    first test try e.g. 0.005.

    if binarise_flag is 0, then prepare a call to display thresholded tracts in FSLview.

EOF
    exit 1
}

[ "$3" = "" ] && Usage

ResultsDir=$1
thresh=$2
bin_flag=$3
MNI_brain="\$FSLDIR/data/standard/MNI152_T1_1mm_brain.nii.gz"

execPath=`dirname $0`
structures=$execPath/autoPtxDir/structureList
dest=$ResultsDir

if [ "${bin_flag}" -eq "1" ]; then 
    command=$dest/viewAll_3D_${thresh}
else
    command=$dest/viewAll_${thresh}
fi

# function based on fsledithd script
setIntentCode() {
    tmpbase=`${FSLDIR}/bin/tmpnam`;
    tmpbase2=`${FSLDIR}/bin/tmpnam`;

    # generate the xml-style header with fslhd
    ${FSLDIR}/bin/fslhd -x $1 | grep -v '/>' | grep -v 'intent_code' | grep -v '_filename' | grep -v '[^t]_name' | grep -v 'nvox' | grep -v 'to_ijk' | grep -v 'form_.*orientation' | grep -v 'qto_' > ${tmpbase}
    # exit if the above didn't generate a decent file
    if [ `cat ${tmpbase} | wc -l` -le 1 ] ; then
    echo "==ERROR== Header not recognized. Exiting..."
    exit 0;
    fi

    # append intent_code to header
    echo "  intent_code = '"$2"'  " >> ${tmpbase}
    # close the xml-style part
    echo "/>" >> ${tmpbase}

    cat ${tmpbase} | grep -v '^[ 	]*#' | grep -v '^[ 	]*$' > ${tmpbase2}
    ${FSLDIR}/bin/fslcreatehd ${tmpbase2} $1

    \rm -f ${tmpbase} ${tmpbase2}
}

# the individual luts for each tract, combined with the intentcode in the nifti
# header allow each tract to be displayed in FSLView with some spatial smoothing
cd $dest
echo "#!/bin/bash" > $command
chmod +x $command
Lut_list="Cool Cool Blue-Lightblue Blue-Lightblue Green Green Green Green Copper Copper Yellow Yellow Pink Pink Red Red Blue Copper Copper Blue-Lightblue Blue-Lightblue Red Red Red Red Red Red Red Red Blue-Lightblue Blue-Lightblue Hot Hot"
arr=($Lut_list)
comIt=0
viewstr="fslview ${MNI_brain}"
while read line; do
        struct=`echo $line | awk '{print $1}'`
        comIt=$(( $comIt + 1 ))
        #tracts=$tractSrc/$struct/tracts/tractsNorm.nii.gz
        tracts=$struct.nii.gz
        if [ "${bin_flag}" -eq "1" ]; then 
	    tracts_thr=${struct}_bin
	    $FSLDIR/bin/fslmaths $tracts -thr $thresh -bin -mul $comIt -range $tracts_thr
            setIntentCode $tracts_thr 3
            viewstr=$viewstr\ $tracts_thr\ -b\ 0.1,${comIt}.01\ -l\ $execPath/autoPtxDir/luts/c${comIt}.lut
	else
            comIt=$(( $comIt - 1 ))
	    tracts_thr=${struct}_thr
	    imcp $tracts $tracts_thr
            setIntentCode $tracts_thr 3
            viewstr=$viewstr\ $tracts_thr\ -b\ ${thresh},0.01\ -l\ `echo ${arr[$comIt]}`
            comIt=$(( $comIt + 1 ))
	fi
done < $structures
echo $viewstr >> $command
