#!/bin/bassh

# Registration to F99 macaque atlas
# S. Jbabdi

if [ "$2" == "" ];then
    echo ""
    echo " do_reg_F99.sh <brain> <outputBase> [F99Dir]"
    echo ""
    echo " <brain>      : FA or T1 image or similar contrast"
    echo " <outputBase> : Prefix for output image and warps"
    echo " [F99Dir]     : Default is $FSLDIR/etc/xtract_data/standard/F99"
    echo ""
    exit 1
fi

f99dir=$3
if [ "$f99dir" == "" ];then
    f99dir=$FSLDIR/etc/xtract_data/standard/F99
fi

# Parse args
anat=$1
atl=$f99dir/mri/struct_brain
conf=$f99dir/config
out=$2


# REGISTRATION TO F99 ATLAS 

echo ""
echo "  ---> Remove Bias Field"

fast -n 1 -b -B -l 10 -o ${out}_struct_brain $anat 

echo ""
echo "  ---> Initial affine registration"
flirt -in $anat -ref $atl -omat ${out}_anat_to_F99.mat -out ${out}_anat_to_F99

echo ""
echo "  ---> FNIRT with custom config file"
fnirt --in=$anat --ref=$atl --aff=${out}_anat_to_F99.mat --iout=${out}_anat_to_F99_nonlin --cout=${out}_anat_to_F99_warp  --config=${conf}
invwarp -w ${out}_anat_to_F99_warp -r $anat -o ${out}_F99_to_anat_warp

echo ""
echo "  ---> Check registration"
applywarp -i $atl -o ${out}_F99_to_anat_nonlin -r $anat -w ${out}_F99_to_anat_warp
slicesdir -o $atl ${out}_anat_to_F99_nonlin $anat ${out}_F99_to_anat_nonlin

echo "In order to check registration, open the following file onto a web browser:"
echo "`pwd`/slicesdir/index.html"

echo ""
echo "Done."
