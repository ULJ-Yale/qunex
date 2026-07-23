#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``nifti.py``

This file holds code for NIfTI file manipulation utilities. The functions
implemented here are:

--fz2zf        Reordering of time and z dimension.
--reslice      Reslicing of images.
--reorder      Reordering of slices in images.

These functions are primarily intended for internal use by other gmri commands.
"""

"""
Created by Grega Repovs on 2013-04-08.
Copyright (c) Grega Repovs. All rights reserved.
"""

import numpy as np
import gzip

import qx_utilities.general.img as gi
import qx_utilities.general.qximg as qxi


def fz2zf(inf, outf=None):
    """
    ``fz2zf inf=<input_image> [outf=<output_image>]``

    Convert the xyfz order of data to xyzf.

    ..  qx_command:
        type: utility

    Parameters:
        --inf (str):
            Input image filename to be shuffled.

        --outf (str):
            Output image filename. If not provided, it replaces the original file.

    """

    # ---> check data format

    sform = gi.get_img_format(inf)
    if sform == '.nii.gz':
        sf = gzip.open(inf, 'r')
    else:
        sf = open(inf,'r')

    # ---> read the header info

    nihdr = gi.niftihdr()
    nihdr.unpack_hdr(sf)
    data_type = np.dtype(nihdr.e + nihdr.dType)

    # ---> read and reshuffle the data

    sf.seek(int(nihdr.vox_offset))
    image = np.fromstring(sf.read(), dtype=data_type)
    sf.close()
    image.shape = (nihdr.sizez, nihdr.frames, nihdr.sizey, nihdr.sizex)

    out = image.swapaxes(0, 1)

    # ---> check data format

    if outf is None:
        outf = inf

    tform = gi.get_img_format(outf)
    if tform == '.nii.gz':
        tf = gzip.open(outf, 'w')
    else:
        tf = open(outf,'w')

    # ---> save image data

    tf.write(nihdr.pack_hdr())
    tf.write(out.astype(data_type).tostring())
    tf.close


def reslice(inf, slices, outf=None):
    """
    ``reslice inf=<input_image> slices=<slices_per_volume> [outf=<output_image>]``

    Remove extra slices for interrupted BOLD sequences.

    ..  qx_command:
        type: utility

    Parameters:
        --inf (str):
            Input image filename to be reordered.

        --slices (int):
            Number of slices per volume.

        --outf (str):
            Output image filename. If not provided, it replaces the original file.

    Notes:

        Removes extra slices for interrupted BOLD sequences and creates an image with good
        frames with data in xyzf order.

    Warning:
        It assumes ascending interpolated acquisition of slices!

    Examples:

        ::

            qunex reslice 07.nii.gz 48
    """

    slices = int(slices)

    # ---> check data format

    sform = gi.get_img_format(inf)
    if sform == '.nii.gz':
        sf = gzip.open(inf, 'r')
    else:
        sf = open(inf,'r')

    # ---> read the header info

    nihdr = gi.niftihdr()
    nihdr.unpack_hdr(sf)
    data_type = np.dtype(nihdr.e + nihdr.dType)

    # ---> read and reshuffle the data

    sf.seek(int(nihdr.vox_offset))
    image = np.fromstring(sf.read(), dtype=data_type)
    sf.close()
    image.shape = (nihdr.sizez, nihdr.frames, nihdr.sizey, nihdr.sizex)

    # ---> compute number of frames and take extra slices out

    gframes = int(nihdr.sizez / slices)
    eslices = nihdr.sizez % slices

    sdelete = list(range(0,slices,2)) + list(range(1,slices,2))
    sdelete = sdelete[0:eslices]
    indeces = [gframes+1 if n in sdelete else gframes for n in range(slices)]
    indeces = [sum(indeces[0:n+1])-1 for n in range(slices)]
    indeces = [indeces[n] for n in range(slices) if n in sdelete]

    mask = np.ones(nihdr.sizez, dtype=bool)
    mask[indeces] = False

    image = image[mask,...]

    # image = np.delete(image, indeces, 0)

    # ---> recompute the size

    nihdr.sizez  = slices
    nihdr.frames = gframes
    nihdr.ndimensions = 4
    image.shape = (nihdr.sizez, nihdr.frames, nihdr.sizey, nihdr.sizex)

    # ---> swap Z and F

    out = image.swapaxes(0, 1)

    # ---> check data format

    if outf is None:
        outf = inf

    tform = gi.get_img_format(outf)
    if tform == '.nii.gz':
        tf = gzip.open(outf, 'w')
    else:
        tf = open(outf,'w')

    # ---> save image data

    tf.write(nihdr.pack_hdr())
    tf.write(out.astype(data_type).tostring())
    tf.close


def reorder(inf, outf=None):
    """
    ``reorder inf=<input_image> [outf=<output_image>]``

    Reorder the slices (y dimension) for images that are upside down.

    ..  qx_command:
        type: utility

    Parameters:
        --inf (str):
            Input image filename to be reordered.

        --outf (str):
            Output image filename. If not provided, it replaces the original file.
    """

    # ---> check data format

    sform = gi.get_img_format(inf)
    if sform == '.nii.gz':
        sf = gzip.open(inf, 'r')
    else:
        sf = open(inf,'r')

    # ---> read the header info

    nihdr = gi.niftihdr()
    nihdr.unpack_hdr(sf)
    data_type = np.dtype(nihdr.e + nihdr.dType)

    # ---> read and reshuffle the data

    sf.seek(int(nihdr.vox_offset))
    image = np.fromstring(sf.read(), dtype=data_type)
    sf.close()
    image.shape = (nihdr.frames, nihdr.sizez, nihdr.sizey, nihdr.sizex)

    out = image[:,::-1,...]

    # ---> check data format

    if outf is None:
        outf = inf

    tform = gi.get_img_format(outf)
    if tform == '.nii.gz':
        tf = gzip.open(outf, 'w')
    else:
        tf = open(outf,'w')

    # ---> save image data

    tf.write(nihdr.pack_hdr())
    tf.write(out.astype(data_type).tostring())
    tf.close


def nifti24dfp(inf, outf=None):
    """
    ``nifti24dfp inf=<input_image> [outf=<output_image>]``

    Convert a NIfTI file to a 4dfp file.

    ..  qx_command:
        type: utility

    Parameters:
        --inf (str):
            Input image filename to be converted.

        --outf (str):
            Output image filename. If not provided, it replaces the original file.
    """

    if outf is None:
        outf = inf

    # ---> read image

    image = qxi.qximg(inf)
    image.save_4dfp(outf)
