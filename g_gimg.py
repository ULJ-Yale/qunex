#!/opt/local/bin/python2.7
# encoding: utf-8
"""
Created by Grega Repovs on 2013-04-13.
Copyright (c) Grega Repovs. All rights reserved.
"""

import g_mri.g_img as g
import numpy as np
import gzip


class gimg(object):
    """A general class for loading, saving and manipulating MR images."""

    def __init__(self, varone=None, frames=None):
        super(gimg, self).__init__()

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

        sform = g.getImgFormat(filename)
        if sform == '.nii.gz':
            sf = gzip.open(filename, 'r')
        else:
            sf = open(filename,'r')

        # ---> read the header info

        nihdr = g.niftihdr()
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
        self.data = np.fromstring(sf.read(self.voxels*nihdr.bitpix/8), dtype=dataType)
        sf.close()
        self.data.shape  = (nihdr.frames, nihdr.sizez, nihdr.sizey, nihdr.sizex)


    def save4DFP(self, filename=None, frames=None, extra=None):
        pass

    def saveNIfTI(self, filename=None, frames=None, extra=None):

        if filename == None:
            filename = self.filename

        tform = g.getImgFormat(filename)
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


def modifyNIfTIHeader(filename, s):

    img = gimg(filename)
    img.hdrnifti.modifyHeader(s)
    img.saveimage()
