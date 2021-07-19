#!/bin/sh
#
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
#	Modified by Alan Anticevic
# Originally developed by University of Oxford
#
# last 2 parameters are subjdir and bindir

parameters=""
while [ ! -z "$2" ]
do
    if [[ $1 =~ "--nf=" ]]; then
            numfib=`echo $1 | cut -d '=' -f2`
    fi
     all=$all" "$1
    subjdir=$1
    shift
done
bindir=$1
merge_parts_gpu $all

fib=1
while [ $fib -le $numfib ]
do
    ${FSLDIR}/bin/fslmaths ${subjdir}.bedpostX/merged_th${fib}samples -Tmean ${subjdir}.bedpostX/mean_th${fib}samples
    ${FSLDIR}/bin/fslmaths ${subjdir}.bedpostX/merged_ph${fib}samples -Tmean ${subjdir}.bedpostX/mean_ph${fib}samples
    ${FSLDIR}/bin/fslmaths ${subjdir}.bedpostX/merged_f${fib}samples -Tmean ${subjdir}.bedpostX/mean_f${fib}samples

    ${FSLDIR}/bin/make_dyadic_vectors ${subjdir}.bedpostX/merged_th${fib}samples ${subjdir}.bedpostX/merged_ph${fib}samples ${subjdir}/nodif_brain_mask ${subjdir}.bedpostX/dyads${fib}
    if [ $fib -ge 2 ];then
    ${FSLDIR}/bin/maskdyads ${subjdir}.bedpostX/dyads${fib} ${subjdir}.bedpostX/mean_f${fib}samples
    ${FSLDIR}/bin/fslmaths ${subjdir}.bedpostX/mean_f${fib}samples -div ${subjdir}.bedpostX/mean_f1samples ${subjdir}.bedpostX/mean_f${fib}_f1samples
    ${FSLDIR}/bin/fslmaths ${subjdir}.bedpostX/dyads${fib}_thr0.05 -mul ${subjdir}.bedpostX/mean_f${fib}_f1samples ${subjdir}.bedpostX/dyads${fib}_thr0.05_modf${fib}
    ${FSLDIR}/bin/imrm ${subjdir}.bedpostX/mean_f${fib}_f1samples
    fi

    fib=$(($fib + 1))

done

if [ `${FSLDIR}/bin/imtest ${subjdir}.bedpostX/mean_f1samples` -eq 1 ];then
    ${FSLDIR}/bin/fslmaths ${subjdir}.bedpostX/mean_f1samples -mul 0 ${subjdir}.bedpostX/mean_fsumsamples
    fib=1
    while [ $fib -le $numfib ]
    do
    ${FSLDIR}/bin/fslmaths ${subjdir}.bedpostX/mean_fsumsamples -add ${subjdir}.bedpostX/mean_f${fib}samples ${subjdir}.bedpostX/mean_fsumsamples
    fib=$(($fib + 1))
    done    
fi


echo Removing intermediate files

if [ `${FSLDIR}/bin/imtest ${subjdir}.bedpostX/merged_th1samples` -eq 1 ];then
  if [ `${FSLDIR}/bin/imtest ${subjdir}.bedpostX/merged_ph1samples` -eq 1 ];then
    if [ `${FSLDIR}/bin/imtest ${subjdir}.bedpostX/merged_f1samples` -eq 1 ];then
      rm -rf ${subjdir}.bedpostX/diff_parts
      rm -rf ${subjdir}.bedpostX/data*
      rm -rf ${subjdir}.bedpostX/grad_dev*      
    fi
  fi
fi

echo Creating identity xfm

xfmdir=${subjdir}.bedpostX/xfms
echo 1 0 0 0 > ${xfmdir}/eye.mat
echo 0 1 0 0 >> ${xfmdir}/eye.mat
echo 0 0 1 0 >> ${xfmdir}/eye.mat
echo 0 0 0 1 >> ${xfmdir}/eye.mat

echo Done
