#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``qximg.py``

This file holds code for an image reading and manipulation object. The code is
for internal use and not called directly. It also implements the modniftihdr
command.
"""

"""
Created by Grega Repovs on 2013-04-13.
Copyright (c) Grega Repovs. All rights reserved.
"""

import numpy as np
import gzip
import os.path

import general.img as gi

def removeExt(s, ext):
    if type(ext) not in (tuple, list):
        ext = [ext]
    for e in ext:
        s = s[:-len(e)] if s.endswith(e) else s
    return s


class qximg(object):
    """A general class for loading, saving and manipulating MR images."""

    def __init__(self, varone=None, frames=None):
        super(qximg, self).__init__()

        self.data         = False
        self.imageformat  = False
        self.hdrnifti     = False
        self.hdr4dfp      = False
        self.dim          = False
        self.voxels       = False
        self.vsize        = False
        self.TR           = False
        self.frames       = False
        self.runframes    = []
        self.filename     = ""
        self.rootfilename = ""
        self.mask         = False
        self.masked       = False
        self.empty        = True
        self.standardized = False
        self.correlized   = False
        self.info         = False
        self.roi          = False

        self.mov          = False
        self.mov_hdr      = False
        self.fstats       = False
        self.fstats_hdr   = False
        self.scrub        = False
        self.scrub_hdr    = False

        basestring = (str, bytes)
        if isinstance(varone, basestring):
            self = self.readimage(varone, frames)

        # --- Add option for taking a numpty array

    def readimage(self, filename, frames=None):
        """Calls the appropriate read function based on the image format."""
        if ".4dfp.img" in filename:
            self = self.read4DFP(filename, frames)
        elif ".nii" in filename:
            self = self.readNIfTI(filename, frames)
        elif ".conc" in filename:
            self = self.readConcImage(filename, frames)
        else:
            raise Exception("Read Image: Filename not of a known type!")

    def saveimage(self, filename=None, frames=None, extra=None):
        """Calls the appropriate save function based on the image format."""

        if filename == None:
            filename = self.filename

        if self.imageformat == ".4dfp.img":
            self.save4DFP(filename, frames, extra)
        elif self.imageformat in ['.nii', '.nii.gz']:
            self.saveNIfTI(filename, frames, extra)

    def readConcImage(self, filename, frames=None):
        pass

    def read4DFP(self, filename, frames=None):
        pass

    def readNIfTI(self, filename, frames=None):
        """Reads a NIfTI file."""

        # ---> check data format

        sform = gi.getImgFormat(filename)
        if sform == '.nii.gz':
            sf = gzip.open(filename, 'r')
        else:
            sf = open(filename,'r')

        # ---> read the header info

        nihdr = gi.niftihdr()
        nihdr.unpackHdr(sf)
        dataType = np.dtype(nihdr.e + nihdr.dType)

        if frames != None:
            nihdr.frames = frames

        self.hdrnifti    = nihdr
        self.imageformat = sform
        self.dim         = [nihdr.sizex, nihdr.sizey, nihdr.sizez, nihdr.frames]
        self.voxels      = np.product(self.dim)
        self.vsize       = np.product(self.dim[0:3])
        self.mformat     = 'l'
        self.frames      = nihdr.frames
        self.runframes   = [self.frames]
        self.empty       = False

        self.filename    = filename

        # ---> read the data

        sf.seek(int(nihdr.vox_offset))
        # self.data = np.fromstring(sf.read(self.voxels*nihdr.bitpix/8), dtype=dataType)
        self.data = np.fromstring(sf.read(), dtype=dataType)
        sf.close()
        self.data.shape  = (nihdr.frames, nihdr.sizez, nihdr.sizey, nihdr.sizex)


    def save4DFP(self, filename=None, frames=None, extra=None):
        """Saves a 4dfp file."""

        # ... check filename

        path, fname = ".", self.filename

        if filename is not None:
            path, fname = os.path.split(filename)
            self.filename = fname

        # ... see if we need to transform from NIfTI

        if self.imageformat in ['.nii', '.nii.gz']:
            self.hdr4dfp = self.hdrnifti.toIFH()
            self.data = self.data[:,:,::-1,...]
            self.imageformat = '.4dfp.img'
            self.filename = removeExt(self.filename, ['.gz', '.nii'])
            self.filename += '.4dfp.img'

        fname = removeExt(self.filename, ['.img', '.4dfp'])

        # ... save IFH header

        self.hdr4dfp.writeHeader(os.path.join(path, fname + '.4dfp.ifh'))

        # ... save data

        if 'imagedata byte order' in self.hdr4dfp.ifh:
            if self.hdr4dfp.ifh['imagedata byte order'] == 'littleendian':
                dataType = np.dtype('<f4')
            else:
                dataType = np.dtype('>f4')
        else:
            self.hdr4dfp.ifh['imagedata byte order'] = 'littleendian'
            dataType = np.dtype('<f4')

        tf = open(os.path.join(path, fname + '.4dfp.img'), 'w')
        tf.write(self.data.astype(dataType).tostring())
        tf.close



    def saveNIfTI(self, filename=None, frames=None, extra=None):

        if filename == None:
            filename = self.filename

        tform = gi.getImgFormat(filename)
        if tform == '.nii.gz':
            tf = gzip.open(filename, 'w')
        else:
            tf = open(filename,'w')

        # ---> check if image has to be trimmed

        if frames == None:
            data = self.data
        else:
            data = self.data[0:frames,:,:,:]
            self.hdrnifti.frames = frames

        # ---> save image data

        dataType = np.dtype(self.hdrnifti.e + self.hdrnifti.dType)

        tf.write(self.hdrnifti.packHdr())
        tf.write(data.astype(dataType).tostring())
        tf.close


def modniftihdr(filename, s):
    """
    ``modniftihdr <image_filename> <modification string>``

    Modifies the NIfTI header in place. It reads the header, changes according
    to information in the modification string and writes the header back.

    EXAMPLE USE
    ===========

    ::

        gmri modniftihdr img.nii.gz "srow_x:[0.7,0.0,0.0,-84.0];srow_y:[0.0,0.7,0.0,-112.0];srow_z:[0.0,0.0,0.7,-126]"
    """

    image = qximg(filename)
    image.hdrnifti.modifyHeader(s)
    image.saveimage()
