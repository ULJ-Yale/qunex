#!/usr/bin/env python2.7
# encoding: utf-8
"""
``img.py``

Some basic functions to be used for work with nifti and 4dfp images.
"""

"""
~~~~~~~~~~~~~~~~~~

Change log

2011-03-05 Grega Repovš
           Initial version
2011-07-30 Grega Repovš
           Added function for reporting basic information

Copyright (c) Grega Repovs and Jure Demsar.
All rights reserved.
"""

import struct
import re
import gzip
import os.path
import exceptions as ge

niftiDataTypes = {1: 'b', 2: 'u1', 4: 'i2', 8: 'i4', 16: 'f4', 32: 'c8', 64: 'f8', 128: 'u1,u1,u1', 256: 'i1', 512: 'u2', 768: 'u4', 1025: 'i8', 1280: 'u8', 1536: 'f16', 2304: 'u1,u1,u1,u1'}
niftiBytesPerVoxel = {1: 1, 2: 1, 4: 2, 8: 4, 16: 4, 32: 8, 64: 8, 128: 3, 256: 1, 512: 2, 768: 4, 1025: 8, 1280: 8, 1536: 16, 2304: 4}


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0


def readTextFileToLines(filename):
    s = file(filename).read()
    s = s.replace('\r', '\n')
    s = s.replace('\n\n', '\n')
    s = s.split('\n')
    return s


def getImgFormat(filename):
    p = filename.split('.')
    if p[-1] == 'nii':
        if ".".join(p[-2:])  == 'dtseries.nii':
            return '.dtseries.nii'
        elif ".".join(p[-2:])  == 'ptseries.nii':
            return '.ptseries.nii'
        else:
            return '.nii'
    elif ".".join(p[-2:]) == '4dfp.img':
        return '.4dfp.img'
    elif ".".join(p[-2:]) == '4dfp.ifh':
        return '.4dfp.img'
    elif ".".join(p[-2:])  == 'nii.gz':
        return '.nii.gz'
    return 'unknown'


def readConc(filename, boldname=None, check=False):
    if os.path.exists(filename):
        s = readTextFileToLines(filename)
    else:
        raise ge.CommandFailed("readConc", "File does not exist", "The specified conc file does not exist:", "[%s]" % (filename), "Please check your data!")

    if boldname is None:
        boldname = 'bold'

    try:
        f = []
        nfiles = int(s[0].split(":")[1])
        boldfiles = [e.split(":")[1].strip() for e in s[1:nfiles + 1]]
    except:
        raise ge.CommandFailed("readConc", "Conc file error", "The conc file is misspecified!", "Conc file: %s" % (filename), "Please check your data!")

    if check:
        missing = []
        for boldfile in boldfiles:
            if not os.path.exists(boldfile):
                missing.append(boldfile)
    
        if missing:
            raise ge.CommandFailed("readConc", "File does not exist", "%d bold files specified in conc file do not exist!" % (len(missing)), "Conc file: %s" % (filename), "Please check your data!", "Missing bold files:", *missing)

    m = re.compile(".*?([0-9]+).*")

    try:
        for boldfile in boldfiles:
            bnum = m.match(boldfile.split('/')[-1]).group(1)
            f.append((boldfile, bnum))
    except:
        raise ge.CommandFailed("readConc", "Conc file error", "The conc file is misspecified!", "Conc file: %s" % (filename), "Please check your data!")

    return f


def writeConc(filename, conc):
    f = open(filename, 'w')
    nfiles = len(conc)
    print >> f, "   number_of_files:  %d" % (nfiles)
    for c in conc:
        print >> f, "      file:%s" % (c[0])
    f.close()


def readBasicInfo(filename):
    if getImgFormat(filename) == '.4dfp.img':
        ifht = ifhhdr()
        ifht.readHeader(filename)
        hdr = ifht.toNIfTI()
    else:
        hdr = niftihdr(filename)

    info = {
            'sizex': hdr.sizex,
            'sizey': hdr.sizey,
            'sizez': hdr.sizez,
            'frames': hdr.frames
    }

    return info


def printniftihdr(filename=None):
    """
    ``printniftihdr <image_filename>``

    Prints the header contents of the NIfTI file.
    """

    hdr = niftihdr(filename)
    print hdr



class fidl:
    def __init__(self, filename=False):
        self.filename = False
        self.TR = False
        self.codes = []
        self.events = []

        if filename:
            self.read(filename)

    def read(self, filename):
        self.filename = filename
        s = readTextFileToLines(filename)
        hdr         = s[0].split()
        self.TR     = float(hdr[0])
        self.codes  = hdr[1:]
        self.events = [e.split() for e in s[1:]]
        self.events = [[float(e) for e in l] for l in self.events if len(l) > 1]

    # ---> adjust times for delta

    def adjustTime(self, delta):
        for event in self.events:
            event[0] += delta

    # ---> merge data from another fidl file

    def merge(self, other, addcodes=True):

        if self.TR != other.TR:
            raise Usage("ERROR: TR of the two fidl files does not match!")

        nevents = list(other.events)

        if addcodes:
            for e in nevents:
                if e[1] > 0:
                    e[1] += nevents
            self.codes += other.codes

        self.events += nevents
        self.events.sort()

    # ---> save to output fidl

    def save(self, filename=False):
        if not filename:
            filename = self.filename
            if not filename:
                raise Usage("ERROR: No filename provided to save fidl file")

        fout = open(filename, 'w')
        print >> fout, "%.2f %s" % (self.TR, " ".join(self.codes))

        for event in self.events:
            event[1] = int(event[1])
            print >> fout, "\t".join([str(e) for e in event])

        fout.close()




class ifhhdr:

    def __init__(self, filename=False):
        self.ifh = {
            "INTERFILE": "",
            "version of keys": "3.3",
            "number format": "float",
            "number of bytes per pixel": "4",
            "orientation": "2",
            "number of dimensions": "4",
            "matrix size [1]": "48",
            "matrix size [2]": "64",
            "matrix size [3]": "48",
            "matrix size [4]": "1",
            "scaling factor (mm/pixel) [1]": "3.000",
            "scaling factor (mm/pixel) [2]": "3.000",
            "scaling factor (mm/pixel) [3]": "3.000",
            "center": "73.500000 -87.000000 -84.000000",
            "mmppix": "3.000000 -3.000000 -3.000000"
        }
        self.vlist = ["INTERFILE", "version of keys", "number format", "number of bytes per pixel", "orientation", "number of dimensions", "matrix size [1]", "matrix size [2]", "matrix size [3]", "matrix size [4]", "scaling factor (mm/pixel) [1]", "scaling factor (mm/pixel) [2]", "scaling factor (mm/pixel) [3]", "center", "mmppix"]

        if filename:
            self.readHeader(filename)
        else:
            self.hdr = self.packHdr()


    def packHdr(self):
        d = dict(self.ifh)
        s = ""
        for k in self.vlist:
            s += "%s %s:= %s\n" % (k, " " * (35 - len(k)), d[k])
            del d[k]
        for k, v in d.iteritems():
            s += "%s %s:= %s\n" % (k, " " * (35 - len(k)), v)

        return s

    def unpackHdr(self, s):
        s = s.replace('\r', '\n')
        s = s.replace('\n\n', '\n')
        s = s.split('\n')
        self.ifh = {}
        self.vlist = []

        for l in s:
            l = l.split(":=")
            if len(l) == 2:
                k = l[0].strip()
                v = l[1].strip()
                self.ifh[k] = v
                self.vlist.append(k)

        return

    def readHeader(self, filename):
        filename = filename.replace('.img', '.ifh')
        s = file(filename).read()
        self.unpackHdr(s)
        self.hdr = s

        return

    def writeHeader(self, filename):
        h = open(filename, 'w')
        s = self.packHdr()
        h.write(s)
        h.close()

        return

    def toNIfTI(self):
        nihdr = niftihdr()
        if "center" in self.ifh:
            c  = tuple([float(e) for e in self.ifh["center"].split()])
        else:
            c = (0, 0, 0)
        if "mmppix" in self.ifh:
            mm = tuple([abs(float(e)) for e in self.ifh["mmppix"].split()])
        else:
            mm = (0, 0, 0)

        nihdr.sizex  = int(self.ifh["matrix size [1]"])
        nihdr.sizey  = int(self.ifh["matrix size [2]"])
        nihdr.sizez  = int(self.ifh["matrix size [3]"])
        nihdr.frames = int(self.ifh["matrix size [4]"])

        if nihdr.frames == 1:
            nihdr.ndimensions = 3

        if "imagedata byte order" in self.ifh:
            if self.ifh["imagedata byte order"] == "littleendian":
                nihdr.e = "<"
            else:
                nihdr.e = ">"
        else:
            nihdr.e = ">"

        nihdr.pixdim_x, nihdr.pixdim_y, nihdr.pixdim_z = mm
        x = (mm[0] / 2 - c[0]) * nihdr.pixdim_0
        y = -c[1] + mm[1] / 2 - mm[1] * nihdr.sizey
        z = -c[2] + mm[2] / 2 - mm[2] * nihdr.sizez

        nihdr.qoffset_x, nihdr.qoffset_y, nihdr.qoffset_z = x, y, z
        nihdr.srow_x[0] = mm[0] * nihdr.srow_x[0]
        nihdr.srow_x[3] = x
        nihdr.srow_y[1] = mm[1] * nihdr.srow_y[1]
        nihdr.srow_y[3] = y
        nihdr.srow_z[2] = mm[2] * nihdr.srow_z[2]
        nihdr.srow_z[3] = z

        return nihdr


class niftihdr:

    def __init__(self, filename=False):
        self.dim_info    = chr(0)        # char      - MRI slice ordering ---- information not available in IFH
        self.ndimensions = 4             # short     - number of dimensions used
        self.sizex       = 48            # short     - size in dimension x
        self.sizey       = 64            # short     - size in dimension y
        self.sizez       = 48            # short     - size in dimension z
        self.frames      = 1             # short     - number of frames (4th dimension))
        self.size_5      = 0             # short     - size of 5th dimension
        self.size_6      = 0             # short     - size of 6th dimension
        self.size_7      = 0             # short     - size of 7th dimension
        self.intention1  = 0.0           # float     - intention 1 parameter
        self.intention2  = 0.0           # float     - intention 2 parameter
        self.intention3  = 0.0           # float     - intention 3 parameter
        self.intent_code = 0             # short     - intent code
        self.data_type   = 16            # short     - datatype  [16 = 32bit float]
        self.bitpix      = 32            # short     - bits per voxel [4 = 4 byte / 32 bit float]
        self.slice_start = 0             # short     - First slice index
        self.pixdim_0    = -1.0          # float     - zero dimension size (important for orientation))
        self.pixdim_x    = 3.0           # float     - x dimension size (important for orientation))
        self.pixdim_y    = 3.0           # float     - y dimension size (important for orientation))
        self.pixdim_z    = 3.0           # float     - z dimension size (important for orientation))
        self.pixdim_t    = 3.0           # float     - t dimension size (important for orientation))
        self.pixdim_5    = 0.0           # float     - 5 dimension size (important for orientation))
        self.pixdim_6    = 0.0           # float     - 6 dimension size (important for orientation))
        self.pixdim_7    = 0.0           # float     - 7 dimension size (important for orientation))
        self.vox_offset  = 352.0         # float     - offset of data when within the same file
        self.scl_slope   = 1.0           # float     - slope of data scaling
        self.scl_inter   = 0.0           # float     - intersect of data scaling
        self.slice_end   = 0             # short     - Last slice index
        self.slice_code  = 0             # char      - slice order code
        self.xyzt_units  = 10            # char      - codes for units used
        self.cal_max     = 2000.0        # float     - maximum value in the dataset to be displayed (white))
        self.cal_min     = 0.0           # float     - minimum value in the dataset to be displayed (black))
        self.slice_duration = 0.0        # float     - slice duration if slice_dim is not zero
        self.toffset     = 0.0           # float     - time offset for first datapoint
        self.descrip     = ""            # char[80]  - data description
        self.aux_file    = ""            # char[24]  - auxilary filename
        self.qform_code  = 3             # short     - for which space is qform information in (3 - Coordinates aligned to Talairach-Tournoux Atlas)
        self.sform_code  = 3             # short     - niftixform code
        self.quatern_b   = 0.0           # float     - Quaternion b param
        self.quatern_c   = 1.0           # float     - Quaternion c param
        self.quatern_d   = 0.0           # float     - Quaternion d param
        self.qoffset_x   = 70.5          # float     - Quaternion x shift
        self.qoffset_y   = 84.0          # float     - Quaternion y shift
        self.qoffset_z   = -60.0         # float     - Quaternion z shift
        self.srow_x      = [-1, 0, 0, 0]  # float[4]  - affine transform row x
        self.srow_y      =  [0, 1, 0, 0]  # float[4]  - affine transform row y
        self.srow_z      =  [0, 0, 1, 0]  # float[4]  - affine transform row z
        self.intent_name = ""             # char[16]  - intent name
        self.magic       = "n+1" + chr(0)  # char[4]     - magic word and zero char
        self.ext         = chr(0) * 4      # extension code

        self.xyz_unit    = 2             # used units for xyz dimension (0-unspecified, 1-m, 2-mm, 3-micronm)
        self.t_unit      = 8             # used units for t dimension (0-unspecified, 8-seconds, 16-milliseconds, 24-microseconds)
        self.s_unit      = 0             # used units for spectral data (0-unspecified, 32-hertz, 40-ppm, 48-radians per s)

        self.e           = ">"           # endiannes
        self.hdr         = False
        self.filename    = False

        self.dType      = niftiDataTypes[self.data_type]
        self.meta       = []

        if filename:
            self.readHeader(filename)
        else:
            self.hdr = self.packHdr()

    def packHdr(self):

        self.vox_offset = 352
        for m in self.meta:
            self.vox_offset += m[0]

        s = struct.pack(self.e + "i", 348)                            # int       - must be 348
        for n in range(0, 10):                                        # char[10]  - unused
            s += struct.pack(self.e + "c", " ")
        for n in range(0, 18):                                        # char[18]  - unused
            s += struct.pack(self.e + "c", " ")
        s += struct.pack(self.e + "i", 0)                             # int       - unused
        s += struct.pack(self.e + "h", 0)                             # short     - unused
        s += struct.pack(self.e + "c", " ")                           # char      - unused
        s += struct.pack(self.e + "c", self.dim_info)                 # char      - MRI slice ordering ---- information not available in IFH
        s += struct.pack(self.e + "h", self.ndimensions)              # short     - number of dimensions used
        s += struct.pack(self.e + "h", self.sizex)                    # short     - size in dimension x
        s += struct.pack(self.e + "h", self.sizey)                    # short     - size in dimension y
        s += struct.pack(self.e + "h", self.sizez)                    # short     - size in dimension z
        s += struct.pack(self.e + "h", self.frames)                   # short     - number of frames (4th dimension)
        s += struct.pack(self.e + "h", self.size_5)                   # short     - size of 5th dimension
        s += struct.pack(self.e + "h", self.size_6)                   # short     - size of 6th dimension
        s += struct.pack(self.e + "h", self.size_7)                   # short     - size of 7th dimension
        s += struct.pack(self.e + "f", self.intention1)               # float     - intention 1 parameter
        s += struct.pack(self.e + "f", self.intention2)               # float     - intention 2 parameter
        s += struct.pack(self.e + "f", self.intention3)               # float     - intention 3 parameter
        s += struct.pack(self.e + "h", self.intent_code)              # short     - intent code
        s += struct.pack(self.e + "h", self.data_type)                # short     - datatype
        s += struct.pack(self.e + "h", self.bitpix)                   # short     - bits per voxel
        s += struct.pack(self.e + "h", self.slice_start)              # short     - First slice index
        s += struct.pack(self.e + "f", self.pixdim_0)                 # float     - zero dimension size (important for orientation)
        s += struct.pack(self.e + "f", self.pixdim_x)                 # float     - x dimension size (important for orientation)
        s += struct.pack(self.e + "f", self.pixdim_y)                 # float     - y dimension size (important for orientation)
        s += struct.pack(self.e + "f", self.pixdim_z)                 # float     - z dimension size (important for orientation)
        s += struct.pack(self.e + "f", self.pixdim_t)                 # float     - t dimension size (important for orientation)
        s += struct.pack(self.e + "f", self.pixdim_5)                 # float     - 5 dimension size (important for orientation)
        s += struct.pack(self.e + "f", self.pixdim_6)                 # float     - 6 dimension size (important for orientation)
        s += struct.pack(self.e + "f", self.pixdim_7)                 # float     - 7 dimension size (important for orientation)
        s += struct.pack(self.e + "f", self.vox_offset)               # float     - offset of data when within the same file
        s += struct.pack(self.e + "f", self.scl_slope)                # float     - slope of data scaling
        s += struct.pack(self.e + "f", self.scl_inter)                # float     - intersect of data scaling
        s += struct.pack(self.e + "h", self.slice_end)                # short     - Last slice index
        s += struct.pack(self.e + "b", self.slice_code)               # char      - slice order code
        s += struct.pack(self.e + "b", self.xyz_unit + self.t_unit)   # char      - codes for units used
        s += struct.pack(self.e + "f", self.cal_max)                  # float     - maximum value in the dataset to be displayed (white)
        s += struct.pack(self.e + "f", self.cal_min)                  # float     - minimum value in the dataset to be displayed (black)
        s += struct.pack(self.e + "f", self.slice_duration)           # float     - minimum value in the dataset to be displayed (black)
        s += struct.pack(self.e + "f", self.toffset)                  # float     - time offset for first datapoint
        s += struct.pack(self.e + "i", 0)                             # int       - unused
        s += struct.pack(self.e + "i", 0)                             # int       - unused
        s += (self.descrip + "12345678901234567890123456789012345678901234567890123456789012345678901234567890")[0:80]  # char[80]  - data description
        s += (self.aux_file + "123456789012345678901234")[0:24]       # char[24]  - auxilary filename
        s += struct.pack(self.e + "h", self.qform_code)               # short     - niftixform code
        s += struct.pack(self.e + "h", self.sform_code)               # short     - niftixform code
        s += struct.pack(self.e + "f", self.quatern_b)                # float     - Quaternion b param
        s += struct.pack(self.e + "f", self.quatern_c)                # float     - Quaternion c param
        s += struct.pack(self.e + "f", self.quatern_d)                # float     - Quaternion d param
        s += struct.pack(self.e + "f", self.qoffset_x)                # float     - Quaternion x shift
        s += struct.pack(self.e + "f", self.qoffset_y)                # float     - Quaternion y shift
        s += struct.pack(self.e + "f", self.qoffset_z)                # float     - Quaternion z shift
        s += struct.pack(self.e + "ffff", self.srow_x[0], self.srow_x[1], self.srow_x[2], self.srow_x[3])  # float[4]  - affine transform data - row x
        s += struct.pack(self.e + "ffff", self.srow_y[0], self.srow_y[1], self.srow_y[2], self.srow_y[3])  # float[4]  - affine transform data - row y
        s += struct.pack(self.e + "ffff", self.srow_z[0], self.srow_z[1], self.srow_z[2], self.srow_z[3])  # float[4]  - affine transform data - row z
        s += (self.intent_name + "1234567890123456")[0:16]            # char[16]  - intent name
        s += self.magic[0:3] + chr(0)                                 # char[4]   - magic word and zero char
        s += (self.ext + chr(0) * 4)[0:4]                             # char[4]   - extension

        for msize, mcode, mdata in self.meta:
            s += struct.pack(self.e + "I", msize)                     # int       - length
            s += struct.pack(self.e + "I", mcode)                     # int       - code
            s += mdata                                                # data

        return s

    def unpackHdr(self, s):

        si = struct.calcsize('i')
        sc = struct.calcsize('c')
        sh = struct.calcsize('h')
        sf = struct.calcsize('f')

        e, = struct.unpack(">i", s.read(si))                        # int       - must be 348
        if e == 348:
            e = ">"
        else:
            e = "<"
        self.e = e

        t = s.read(10 * sc)                                           # char[10]  - unused
        t = s.read(18 * sc)                                           # char[18]  - unused
        t = s.read(si)                                                # int       - unused
        t = s.read(sh)                                                # short     - unused
        t = s.read(sc)                                                # char      - unused

        self.dim_info,       = struct.unpack(e + "c", s.read(sc))      # char      - MRI slice ordering ---- information not available in IFH

        self.ndimensions,    = struct.unpack(e + "h", s.read(sh))      # short     - number of dimensions used
        self.sizex,          = struct.unpack(e + "h", s.read(sh))      # short     - size in dimension x
        self.sizey,          = struct.unpack(e + "h", s.read(sh))      # short     - size in dimension y
        self.sizez,          = struct.unpack(e + "h", s.read(sh))      # short     - size in dimension z
        self.frames,         = struct.unpack(e + "h", s.read(sh))      # short     - number of frames (4th dimension))
        self.size_5,         = struct.unpack(e + "h", s.read(sh))      # short     - size of 5th dimension
        self.size_6,         = struct.unpack(e + "h", s.read(sh))      # short     - size of 6th dimension
        self.size_7,         = struct.unpack(e + "h", s.read(sh))      # short     - size of 7th dimension
        self.intention1,     = struct.unpack(e + "f", s.read(sf))      # float     - intention 1 parameter
        self.intention2,     = struct.unpack(e + "f", s.read(sf))      # float     - intention 2 parameter
        self.intention3,     = struct.unpack(e + "f", s.read(sf))      # float     - intention 3 parameter
        self.intent_code,    = struct.unpack(e + "h", s.read(sh))      # short     - intent code
        self.data_type,      = struct.unpack(e + "h", s.read(sh))      # short     - datatype
        self.bitpix,         = struct.unpack(e + "h", s.read(sh))      # short     - bits per voxel
        self.slice_start,    = struct.unpack(e + "h", s.read(sh))      # short     - First slice index
        self.pixdim_0,       = struct.unpack(e + "f", s.read(sf))      # float     - zero dimension size (important for orientation))
        self.pixdim_x,       = struct.unpack(e + "f", s.read(sf))      # float     - x dimension size (important for orientation))
        self.pixdim_y,       = struct.unpack(e + "f", s.read(sf))      # float     - y dimension size (important for orientation))
        self.pixdim_z,       = struct.unpack(e + "f", s.read(sf))      # float     - z dimension size (important for orientation))
        self.pixdim_t,       = struct.unpack(e + "f", s.read(sf))      # float     - t dimension size (important for orientation))
        self.pixdim_5,       = struct.unpack(e + "f", s.read(sf))      # float     - 5 dimension size (important for orientation))
        self.pixdim_6,       = struct.unpack(e + "f", s.read(sf))      # float     - 6 dimension size (important for orientation))
        self.pixdim_7,       = struct.unpack(e + "f", s.read(sf))      # float     - 7 dimension size (important for orientation))
        self.vox_offset,     = struct.unpack(e + "f", s.read(sf))      # float     - offset of data when within the same file
        self.scl_slope,      = struct.unpack(e + "f", s.read(sf))      # float     - slope of data scaling
        self.scl_inter,      = struct.unpack(e + "f", s.read(sf))      # float     - intersect of data scaling
        self.slice_end,      = struct.unpack(e + "h", s.read(sh))      # short     - Last slice index
        self.slice_code,     = struct.unpack(e + "b", s.read(sc))      # char      - slice order code
        self.xyzt_units,     = struct.unpack(e + "b", s.read(sc))      # char      - codes for units used
        self.cal_max,        = struct.unpack(e + "f", s.read(sf))      # float     - maximum value in the dataset to be displayed (white))
        self.cal_min,        = struct.unpack(e + "f", s.read(sf))      # float     - minimum value in the dataset to be displayed (black))
        self.slice_duration, = struct.unpack(e + "f", s.read(sf))      # float     - minimum value in the dataset to be displayed (black))
        self.toffset,        = struct.unpack(e + "f", s.read(sf))      # float     - time offset for first datapoint
        t = s.read(si)                                              # int       - unused
        t = s.read(si)                                              # int       - unused

        self.descrip         = s.read(sc * 80)                         # char[80]  - data description
        self.aux_file        = s.read(sc * 24)                         # char[24]  - auxilary filename
        self.qform_code,     = struct.unpack(e + "h", s.read(sh))      # short     - niftixform code
        self.sform_code,     = struct.unpack(e + "h", s.read(sh))      # short     - niftixform code
        self.quatern_b,      = struct.unpack(e + "f", s.read(sf))      # float     - Quaternion b param
        self.quatern_c,      = struct.unpack(e + "f", s.read(sf))      # float     - Quaternion c param
        self.quatern_d,      = struct.unpack(e + "f", s.read(sf))      # float     - Quaternion d param
        self.qoffset_x,      = struct.unpack(e + "f", s.read(sf))      # float     - Quaternion x shift
        self.qoffset_y,      = struct.unpack(e + "f", s.read(sf))      # float     - Quaternion y shift
        self.qoffset_z,      = struct.unpack(e + "f", s.read(sf))      # float     - Quaternion z shift
        self.srow_x          = list(struct.unpack(e + "ffff", s.read(sf * 4)))     # float[4]  - affine transform row x
        self.srow_y          = list(struct.unpack(e + "ffff", s.read(sf * 4)))     # float[4]  - affine transform row y
        self.srow_z          = list(struct.unpack(e + "ffff", s.read(sf * 4)))     # float[4]  - affine transform row z
        self.intent_name     = s.read(sc * 16)                         # char[16]  - intent name
        self.magic           = s.read(sc * 4)                          # char[4]   - magic word and zero char
        self.ext             = s.read(sc * 4)                          # char[4]   - extension

        self.dType           = niftiDataTypes[self.data_type]

        t = self.xyzt_units
        self.xyz_unit = t % 8
        t = t - (t % 8)
        self.t_unit = t % 64


        # --- Read extensions

        self.meta = []
        pointer = 352

        if self.ext == [1, 0, 0, 0]:
            while pointer < self.vox_offset:
                msize = struct.unpack(e + "I", s.read(si))
                mcode = struct.unpack(e + "I", s.read(si))
                if pointer + msize <= self.vox_offset:
                    mdata = s.read(sc * msize - 8)
                    pointer += msize
                self.meta.append([msize, mcode, mdata])
        return

    def readHeader(self, filename):

        sform = getImgFormat(filename)
        if sform == '.nii.gz':
            h = gzip.open(filename, 'r')
        else:
            h = open(filename, 'r')

        self.unpackHdr(h)
        h.close()

        return

    def writeHeader(self, filename):

        h = open(filename, "w")
        s = self.packHdr()
        h.write(s)
        h.close

        return

    def toIFH(self):

        ifhdr = ifhhdr()
        ifhdr.ifh = {
            "INTERFILE": "",
            "version of keys": "3.3",
            "number format": "float",
            "number of bytes per pixel": "4",
            "orientation": "2",
            "number of dimensions": "4",
            "matrix size [1]": str(self.sizex),
            "matrix size [2]": str(self.sizey),
            "matrix size [3]": str(self.sizez),
            "matrix size [4]": str(self.frames),
            "scaling factor (mm/pixel) [1]": str(self.pixdim_x),
            "scaling factor (mm/pixel) [2]": str(self.pixdim_y),
            "scaling factor (mm/pixel) [3]": str(self.pixdim_z)
            # "center": "73.500000 -87.000000 -84.000000",
            # "mmppix": "3.000000 -3.000000 -3.000000"
        }
        if self.e == '<':
            ifhdr.ifh["imagedata byte order"] = 'littleendian'
        else:
            ifhdr.ifh["imagedata byte order"] = 'bigendian'
        ifhdr.vlist = ["INTERFILE", "version of keys", "number format", "number of bytes per pixel", "imagedata byte order", "orientation", "number of dimensions", "matrix size [1]", "matrix size [2]", "matrix size [3]", "matrix size [4]", "scaling factor (mm/pixel) [1]", "scaling factor (mm/pixel) [2]", "scaling factor (mm/pixel) [3]", "center", "mmppix"]

        if self.sform_code > 0:

            if self.srow_x[3] < 0:
                self.srow_x[3] = abs(self.srow_x[3]) - (self.sizex - 1) * abs(self.srow_x[2])
            else:
                self.srow_x[3] = abs(self.srow_x[3])

            if self.srow_y[3] < 0:
                self.srow_y[3] = abs(self.srow_y[3]) - (self.sizey - 1) * abs(self.srow_y[1])
            else:
                self.srow_y[3] = -abs(self.srow_y[3])

            if self.srow_z[3] < 0:
                self.srow_z[3] = abs(self.srow_z[3]) - (self.sizez - 1) * abs(self.srow_z[2])
            else:
                self.srow_z[3] = -abs(self.srow_z[3])

            x = self.srow_x[3] + abs(self.srow_x[0]) / 2
            y = self.srow_y[3] - abs(self.srow_y[1]) / 2
            z = self.srow_z[3] - abs(self.srow_z[2]) / 2

            ifhdr.ifh["center"] = "%.6f %.6f %.6f" % (x, y, z)
            ifhdr.ifh["mmppix"] = "%.6f %.6f %.6f" % (self.pixdim_x * sign(x), self.pixdim_y * sign(y), self.pixdim_z * sign(z))

#        elif self.qform_code > 0:
#            x = -self.qoffset_x*self.pixdim_0 + self.pixdim_x/2
#            y = -self.qoffset_y + self.pixdim_y/2 - self.sizey*self.pixdim_y
#            z = -self.qoffset_z + self.pixdim_z/2 - self.sizez*self.pixdim_z
#            ifhdr.ifh["center"] = "%.6f %.6f %.6f" % (x, y, z)
#            ifhdr.ifh["mmppix"] = "%.6f %.6f %.6f" % (self.pixdim_x*sign(x), self.pixdim_y*sign(y), self.pixdim_z*sign(z))

        return ifhdr

    def __str__(self):
        s = "# ----------------------------------\n# NIfTI Header\n\n"
        d = self.__dict__
        fields = ["dim_info", "ndimensions", "sizex", "sizey", "sizez", "frames", "size_5", "size_6", "size_7", "intention1", "intention2", "intention3", "intent_code", "data_type", "bitpix", "slice_start", "pixdim_0", "pixdim_x", "pixdim_y", "pixdim_z", "pixdim_t", "pixdim_5", "pixdim_6", "pixdim_7", "vox_offset", "scl_slope", "scl_inter", "slice_end", "slice_code", "xyzt_units", "cal_max", "cal_min", "slice_duration", "toffset", "descrip", "aux_file", "qform_code", "sform_code", "quatern_b", "quatern_c", "quatern_d", "qoffset_x", "qoffset_y", "qoffset_z", "srow_x", "srow_y", "srow_z", "intent_name", "magic"]
        for f in fields:
            s += "%s%s: %s\n" % (f, " " * (15 - len(f)), str(d[f]))
        if len(self.meta) > 0:
            s += "\nMetadata:"
            mi = 0
            for msize, mcode, mdata in self.meta:
                mi += 1
                s += "\n- metadata chunk %d, size: %d bytes, code: %d" % (mi, msize, mcode)

        return s + "\n# ----------------------------------"

    def modifyHeader(self, s):
        decodef = {"dim_info":        int,
                   "ndimensions":    int,
                   "sizex":          int,
                   "sizey":          int,
                   "sizez":          int,
                   "frames":         int,
                   "size_5":         int,
                   "size_6":         int,
                   "size_7":         int,
                   "intention1":     float,
                   "intention2":     float,
                   "intention3":     float,
                   "intent_code":    int,
                   "data_type":      int,
                   "bitpix":         int,
                   "slice_start":    int,
                   "pixdim_0":       float,
                   "pixdim_x":       float,
                   "pixdim_y":       float,
                   "pixdim_z":       float,
                   "pixdim_t":       float,
                   "pixdim_5":       float,
                   "pixdim_6":       float,
                   "pixdim_7":       float,
                   "vox_offset":     float,
                   "scl_slope":      float,
                   "scl_inter":      float,
                   "slice_end":      int,
                   "slice_code":     int,
                   "xyzt_units":     int,
                   "cal_max":        float,
                   "cal_min":        float,
                   "slice_duration": float,
                   "toffset":        float,
                   "descrip":        str,
                   "aux_file":       str,
                   "qform_code":     int,
                   "sform_code":     int,
                   "quatern_b":      float,
                   "quatern_c":      float,
                   "quatern_d":      float,
                   "qoffset_x":      float,
                   "qoffset_y":      float,
                   "qoffset_z":      float,
                   "srow_x": lambda x: [float(e) for e in x.replace("[", "").replace("]", "").split(',')],
                   "srow_y": lambda x: [float(e) for e in x.replace("[", "").replace("]", "").split(',')],
                   "srow_z": lambda x: [float(e) for e in x.replace("[", "").replace("]", "").split(',')],
                   "intent_name":    str,
                   "magic":          str,
                   "ext":            str,
                   "xyz_unit":       int,
                   "t_unit":         int,
                   "s_unit":         int,
                   "e":              str,
                   "filename":       str}
        s = s.replace("\r", "\n")
        s = s.replace("\n\n", "\n")
        s = s.replace("\n", ";")
        s = s.split(";")
        s = [e.split(":") for e in s]
        s = [[f.strip() for f in e] for e in s if len(e) == 2]

        for k, v in s:
            if k in decodef:
                self.__dict__[k] = decodef[k](v)
            else:
                print "WARNING: %s not a valid key for NIfTI header" % (k)




def sliceImage(sourcefile, targetfile, frames=1):
    """
    ``sliceImage sourcefile=<source image> targetfile=<target image> [frames=1]``

    Takes the source volume image file, removes all but the first N frames, and
    saves the resulting image to target volume image file.

    INPUTS
    ======

    --sourcefile  Source volume file (.4dfp, .nii, or .nii.gz).
    --targetfile  Target volume file of the same format.
    --frames      Optional number of initial frames to retain. [1]

    EXAMPLE USE
    ===========

    ::

        qunex sliceImage sourcefile=bold1.nii.gz targetfile=bold1_f10.nii.gz frames=10
    """

    """
    ~~~~~~~~~~~~~~~~~~

    Change log

    2016-12-25 Grega Repovš
               Initial version
    2016-12-25 Grega Repovš
               Adopted from a selfstanding command in the dofcMRIp package,
               added documentation.
    """
    frames = int(frames)
    if 'nii' in getImgFormat(sourcefile):
        sliceNIfTI(sourcefile, targetfile, frames)
    else:
        slice4dfp(sourcefile, targetfile, frames)



def slice4dfp(sourcefile, targetfile, frames=1):
    hdr = ifhhdr(sourcefile.replace('.img', '.ifh'))
    x = int(hdr.ifh['matrix size [1]'])
    y = int(hdr.ifh['matrix size [2]'])
    z = int(hdr.ifh['matrix size [3]'])
    t = int(hdr.ifh['matrix size [4]'])
    voxels = x * y * z

    hdr.ifh['matrix size [4]'] = str(frames)
    hdr.writeHeader(targetfile.replace('.img', '.ifh'))

    sf = open(sourcefile, 'r')
    df = open(targetfile, 'w')

    df.write(sf.read(voxels * frames * 4))

    df.flush()
    os.fsync(df.fileno())
    sf.close
    df.close


def sliceNIfTI(sourcefile, targetfile, frames=1):
    sform = getImgFormat(sourcefile)
    tform = getImgFormat(targetfile)

    if sform == '.nii.gz':
        sf = gzip.open(sourcefile, 'r')
    else:
        sf = open(sourcefile, 'r')

    if tform == '.nii.gz':
        tf = gzip.open(targetfile, 'w')
    else:
        tf = open(targetfile, 'w')

    hdr = niftihdr()
    hdr.unpackHdr(sf)
    nvox = hdr.sizex * hdr.sizey * hdr.sizez
    hdr.frames = frames
    tocopy = int(hdr.vox_offset - 352 + nvox * (hdr.bitpix / 8) * frames)

    tf.write(hdr.packHdr())
    tf.write(sf.read(tocopy))

    tf.flush()
    os.fsync(tf.fileno())
    tf.close
    sf.close


def main():
    pass


if __name__ == '__main__':
    main()

