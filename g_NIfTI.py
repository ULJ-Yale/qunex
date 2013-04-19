#!/opt/local/bin/python2.7
# encoding: utf-8
"""
Created by Grega Repovs on 2013-04-08.
Copyright (c) Grega Repovs. All rights reserved.
"""

import g_mri.g_img as g
import numpy as np
import gzip

def fz2zf(inf, outf=None):

    # ---> check data format

    sform = g.getImgFormat(inf)
    if sform == '.nii.gz':
        sf = gzip.open(inf, 'r')
    else:
        sf = open(inf,'r')

    # ---> read the header info

    nihdr = g.niftihdr()
    nihdr.unpackHdr(sf)
    dataType = np.dtype(nihdr.e + nihdr.dType)

    # ---> read and reshuffle the data

    sf.seek(int(nihdr.vox_offset))
    img = np.fromstring(sf.read(), dtype=dataType)
    sf.close()
    img.shape = (nihdr.sizez, nihdr.frames, nihdr.sizey, nihdr.sizex)

    out = img.swapaxes(0, 1)

    # ---> check data format

    if outf is None:
        outf = inf

    tform = g.getImgFormat(outf)
    if tform == '.nii.gz':
        tf = gzip.open(outf, 'w')
    else:
        tf = open(outf,'w')

    # ---> save image data

    tf.write(nihdr.packHdr())
    tf.write(out.astype(dataType).tostring())
    tf.close

