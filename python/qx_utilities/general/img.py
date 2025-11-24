#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``img.py``

Some basic functions to be used for work with nifti and 4dfp images.
"""

import struct
import re
import gzip
import os.path

import general.exceptions as ge

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
    file = open(filename, 'r')
    s = file.read()
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
        if ".".join(p[-2:])  == 'dscalar.nii':
            return '.dscalar.nii'
        elif ".".join(p[-2:])  == 'pscalar.nii':
            return '.pscalar.nii'
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

    m = re.compile(r".*?([0-9]+).*")

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
    print("   number_of_files:  %d" % (nfiles), file=f)
    for c in conc:
        print("      file:%s" % (c[0]), file=f)
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
    print(hdr)


def print_nifti_metadata(filename, info='list'):
    """
    ``print_nifti_metadata <image_filename> [info=list]``

    Prints metadata extension blocks from a NIfTI file.

    NIfTI files can contain metadata extension blocks after the header.
    This function inspects and displays the content of these blocks.

    INPUTS
    ======

    filename  Path to the NIfTI file (.nii or .nii.gz)
    info      Which metadata to print:
              - 'list': List metadata blocks without content (default)
              - 'all': Print all metadata blocks with full content
              - 'cifti': Print CIFTI metadata (ecode 32)
              - 'qunex' or 'qx': Print QuNex metadata (ecode 64)
              - Numeric code (e.g., 32, 64, 2, etc.): Print metadata with that code

    METADATA CODES
    ==============

    Common NIfTI extension codes:
    - 0: Unknown private format
    - 2: DICOM format
    - 4: AFNI group format
    - 6: Comment
    - 8: XCEDE format
    - 10: Jiffy XML format
    - 12: Unused
    - 14: Unused
    - 16: Unused
    - 18: MIND_IDENT format
    - 20: B_VALUE extension
    - 22: SPHERICAL_DIRECTION extension
    - 24: DT_COMPONENT extension
    - 26: SHC_DEGREEORDER extension
    - 28: VOXBO extension
    - 30: CARET extension
    - 32: CIFTI extension (XML format)
    - 34: VARIABLE_FRAME_TIMING extension
    - 36: MATLAB workspace extension
    - 38: QUANTIPHYSE extension
    - 40: MRS extension
    - 42: PYTHON pickle extension
    - 64: QuNex extension

    EXAMPLE USE
    ===========

    ::

        # List metadata blocks (default)
        print_nifti_metadata('bold1.dtseries.nii')

        # Print all metadata with full content
        print_nifti_metadata('bold1.dtseries.nii', info='all')

        # Print only CIFTI metadata
        print_nifti_metadata('bold1.dtseries.nii', info='cifti')

        # Print only QuNex metadata
        print_nifti_metadata('bold1.nii', info='qunex')

        # Print metadata with specific numeric code
        print_nifti_metadata('bold1.nii', info=32)  # CIFTI
        print_nifti_metadata('bold1.nii', info=6)   # Comment
    """

    # Parse the info parameter
    info_str = str(info).lower()
    list_only = False

    # Map info strings to extension codes
    code_filter = None

    if info_str == 'list':
        list_only = True
        code_filter = None
        info_label = "List"
    elif info_str == 'all':
        code_filter = None
        info_label = "All"
    elif info_str == 'cifti':
        code_filter = [32]
        info_label = "CIFTI"
    elif info_str in ['qunex', 'qx']:
        code_filter = [64]
        info_label = "QuNex"
    else:
        # Try to parse as numeric code
        try:
            numeric_code = int(info)
            code_filter = [numeric_code]
            info_label = "Code %d" % numeric_code
        except ValueError:
            print("Warning: Unknown info parameter '%s', using 'list'" % info)
            list_only = True
            code_filter = None
            info_label = "List"

    # Extension code names for display
    ecode_names = {
        0: "Unknown private",
        2: "DICOM",
        4: "AFNI group",
        6: "Comment",
        8: "XCEDE",
        10: "Jiffy XML",
        18: "MIND_IDENT",
        20: "B_VALUE",
        22: "SPHERICAL_DIRECTION",
        24: "DT_COMPONENT",
        26: "SHC_DEGREEORDER",
        28: "VOXBO",
        30: "CARET",
        32: "CIFTI",
        34: "VARIABLE_FRAME_TIMING",
        36: "MATLAB workspace",
        38: "QUANTIPHYSE",
        40: "MRS",
        42: "PYTHON pickle",
        64: "QuNex"
    }

    # Read the NIfTI header and metadata
    hdr = niftihdr(filename)

    # print("-" * 70)
    print("NIfTI Metadata for: %s" % filename)
    print("NIfTI Version: %d" % hdr.nifti_version)
    if list_only:
        print("Mode: List metadata blocks")
    else:
        print("Filter: %s metadata" % info_label)
    print()

    if not hasattr(hdr, 'meta') or len(hdr.meta) == 0:
        print("No metadata extensions found in this file.")
        return

    # If list mode, just show summary
    if list_only:
        print("Found %d metadata block(s):" % len(hdr.meta))
        print()
        for idx, (msize, mcode, mdata) in enumerate(hdr.meta, 1):
            # Extract the actual code value
            if isinstance(mcode, tuple):
                mcode = mcode[0]

            # Get the extension name
            ecode_name = ecode_names.get(mcode, "Unknown")

            print("  Block #%d: Code %d (%s), Size %d bytes" % (idx, mcode, ecode_name, msize))

        print()
        print("Use info='all' to see full content, or info=<code> for specific block")
        print("-" * 70)
        return

    # Filter and display metadata with full content
    found_count = 0
    total_count = len(hdr.meta)

    for idx, (msize, mcode, mdata) in enumerate(hdr.meta, 1):
        # Extract the actual code value (it's returned as a tuple)
        if isinstance(mcode, tuple):
            mcode = mcode[0]

        # Check if this metadata should be displayed
        if code_filter is None or mcode in code_filter:
            found_count += 1

            # Get the extension name
            ecode_name = ecode_names.get(mcode, "Unknown")

            print("--------------------------------")
            print("Metadata Block #%d (of %d total)" % (idx, total_count))
            print("Extension Code: %d (%s)" % (mcode, ecode_name))
            print("Block Size: %d bytes" % msize)
            print()

            # Try to decode and display the metadata content
            try:
                # For CIFTI (32) and many XML-based formats, try UTF-8 decoding
                if mcode in [32, 8, 10, 30]:  # XML-based formats
                    if isinstance(mdata, bytes):
                        content = mdata.decode('utf-8', errors='replace')
                    else:
                        content = ''.join([chr(ord(c)) if ord(c) < 128 else '?' for c in mdata])

                    # Clean up null terminators
                    content = content.rstrip('\x00')

                    print("Content (XML):\n----- START -----")
                    print(content)
                    print("------ END ------")

                # For QuNex (64) and text-based formats
                elif mcode in [64, 6]:  # QuNex or Comment
                    if isinstance(mdata, bytes):
                        content = mdata.decode('utf-8', errors='replace')
                    else:
                        content = ''.join([chr(ord(c)) if ord(c) < 128 else '?' for c in mdata])

                    # Clean up null terminators
                    content = content.rstrip('\x00')

                    print("Content (Text):\n----- START -----")
                    print(content)
                    print("------ END ------")

                # For binary formats, show hex dump of first 256 bytes
                else:
                    if isinstance(mdata, bytes):
                        data_bytes = mdata
                    else:
                        data_bytes = bytes([ord(c) if isinstance(c, str) else c for c in mdata])

                    print("Content (Binary, first 256 bytes):")
                    display_bytes = data_bytes[:256]

                    # Print hex dump in groups of 16 bytes
                    for i in range(0, len(display_bytes), 16):
                        chunk = display_bytes[i:i+16]
                        hex_str = ' '.join(['%02x' % b for b in chunk])
                        ascii_str = ''.join([chr(b) if 32 <= b < 127 else '.' for b in chunk])
                        print("  %04x: %-48s  %s" % (i, hex_str, ascii_str))

                    if len(data_bytes) > 256:
                        print("  ... (%d more bytes not shown)" % (len(data_bytes) - 256))

            except Exception as e:
                print("Error decoding metadata: %s" % str(e))
                print("Raw data length: %d bytes" % len(mdata))

            print()

    if code_filter is None:
        print("Found %d metadata block(s)" % found_count)
    else:
        print("Found %d matching metadata block(s) out of %d total" % (found_count, total_count))
    # print("-" * 70)


def remove_qunex_metadata(infile, outfile=None):
    """
    ``remove_qunex_metadata <infile> [outfile=None]``

    Removes QuNex metadata (extension code 64) from a NIfTI file.

    This function inspects a NIfTI file for QuNex metadata extensions.
    If found, it removes them and saves the file. All other metadata
    blocks (e.g., CIFTI) are preserved.

    INPUTS
    ======

    infile   Path to the input NIfTI file (.nii or .nii.gz)
    outfile  Path to the output file (optional)
             If not provided, the input file is replaced.

    OUTPUTS
    =======

    Returns True if QuNex metadata was found and removed, False otherwise.

    EXAMPLE USE
    ===========

    ::

        # Remove QuNex metadata from file (replace original)
        remove_qunex_metadata('bold1.nii')

        # Remove QuNex metadata and save to new file
        remove_qunex_metadata('bold1.nii', 'bold1_clean.nii')
    """

    # Read the header and metadata
    hdr = niftihdr(infile)
    print("Removing QuNex Metadata\n\n-> Inspecting file for QuNex metadata: %s" % infile)

    # Check if there's any metadata
    if not hasattr(hdr, 'meta') or len(hdr.meta) == 0:
        print("   -> No metadata extensions found in file.")
        return False

    # Find QuNex metadata blocks (code 64)
    original_count = len(hdr.meta)
    qunex_indices = []

    for idx, (msize, mcode, mdata) in enumerate(hdr.meta):
        # Extract the actual code value
        if isinstance(mcode, tuple):
            mcode = mcode[0]

        if mcode == 64:
            qunex_indices.append(idx)

    # Check if any QuNex metadata was found
    if len(qunex_indices) == 0:
        print("   No QuNex metadata (code 64) found in file.")
        return False

    print("   Found %d QuNex metadata block(s) in file." % (len(qunex_indices), ))

    # Remove QuNex metadata blocks (in reverse order to maintain indices)
    for idx in reversed(qunex_indices):
        removed_block = hdr.meta.pop(idx)
        print("-> Removed block #%d: Size %d bytes" % (idx + 1, removed_block[0]))

    # If no metadata remains, clear the extension flag
    if len(hdr.meta) == 0:
        hdr.ext = chr(0) * 4
        print("   All metadata removed, clearing extension flag")
    else:
        print("   %d metadata block(s) remain" % len(hdr.meta))

    # Recalculate vox_offset based on remaining metadata
    if hdr.nifti_version == 2:
        hdr.vox_offset = 544.0 + sum([float(m[0]) for m in hdr.meta])
    else:
        hdr.vox_offset = 352.0 + sum([float(m[0]) for m in hdr.meta])

    # Determine output file
    if outfile is None:
        outfile = infile
        print("-> Updating original file: %s" % infile)
    else:
        print("-> Writing to new file: %s" % outfile)

    # Read the image data from the input file
    sform = getImgFormat(infile)
    if sform == '.nii.gz':
        inf = gzip.open(infile, 'rb')
    else:
        inf = open(infile, 'rb')

    # Read the old header to skip it
    old_hdr = niftihdr()
    old_hdr.unpackHdr(inf)

    # The unpackHdr function already reads the header, extension flag, and all extensions
    # The file pointer is now at vox_offset, ready to read image data
    # No need to skip anything else

    # Read the actual image data
    image_data = inf.read()
    inf.close()

    # Write the new file
    tform = getImgFormat(outfile)
    if tform == '.nii.gz':
        outf = gzip.open(outfile, 'wb')
    else:
        outf = open(outfile, 'wb')

    # Write new header (with updated metadata)
    # Note: packHdr() includes the extension flag at the end
    # For NIfTI-1: 348 bytes header + 4 bytes extension flag = 352 bytes
    # For NIfTI-2: 540 bytes header + 4 bytes extension flag = 544 bytes
    header_bytes = hdr.packHdr()
    outf.write(header_bytes)

    # Write metadata blocks (if any)
    for msize, mcode, mdata in getattr(hdr, 'meta', []):
        outf.write(struct.pack(hdr.e + 'I', msize))   # 4 bytes: size
        outf.write(struct.pack(hdr.e + 'I', mcode))   # 4 bytes: code
        outf.write(mdata)                             # msize-8 bytes: data

    # Write image data
    outf.write(image_data)

    outf.flush()
    os.fsync(outf.fileno())
    outf.close()

    print("-> Successfully removed QuNex metadata")
    print("   Original metadata blocks: %d" % original_count)
    print("   Remaining metadata blocks: %d" % len(hdr.meta))

    return True


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
        print("%.2f %s" % (self.TR, " ".join(self.codes)), file=fout)

        for event in self.events:
            event[1] = int(event[1])
            print("\t".join([str(e) for e in event]), file=fout)

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
        for k, v in d.items():
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
        file = open(filename, 'r')
        s = file.read()
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
        self.nifti_version = 1           # NIfTI version (1 or 2)
        self.dim_info    = chr(0)        # char      - MRI slice ordering ---- information not available in IFH
        self.ndimensions = 4             # short/int64 - number of dimensions used
        self.sizex       = 48            # short/int64 - size in dimension x
        self.sizey       = 64            # short/int64 - size in dimension y
        self.sizez       = 48            # short/int64 - size in dimension z
        self.frames      = 1             # short/int64 - number of frames (4th dimension))
        self.size_5      = 0             # short/int64 - size of 5th dimension
        self.size_6      = 0             # short/int64 - size of 6th dimension
        self.size_7      = 0             # short/int64 - size of 7th dimension
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
        self.srow_x      = [-1, 0, 0, 0]  # float[4]/double[4] - affine transform row x
        self.srow_y      =  [0, 1, 0, 0]  # float[4]/double[4] - affine transform row y
        self.srow_z      =  [0, 0, 1, 0]  # float[4]/double[4] - affine transform row z
        self.intent_name = ""             # char[16]  - intent name
        self.magic       = "n+1" + chr(0)  # char[4]/char[8] - magic word and zero char
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

    def is_cifti(self):
        """Check if this is a CIFTI file based on metadata or filename."""
        # Check for CIFTI extension (code 32)
        for msize, mcode, mdata in self.meta:
            if mcode == 32:
                return True

        # Check filename if available
        if self.filename:
            cifti_extensions = ['.dtseries.nii', '.ptseries.nii', '.dscalar.nii', '.pscalar.nii']
            for ext in cifti_extensions:
                if self.filename.endswith(ext):
                    return True

        return False

    @property
    def volumes(self):
        """
        Get the number of volumes in the file.
        For CIFTI files, this is stored in size_5 (5th dimension).
        For regular NIfTI files, this is stored in frames (4th dimension).
        """
        if self.is_cifti():
            return self.size_5
        else:
            return self.frames

    def packHdr(self):

        if self.nifti_version == 2:
            return self._packHdrV2()
        else:
            return self._packHdrV1()

    def _packHdrV1(self):

        self.vox_offset = 352.0
        for m in self.meta:
            self.vox_offset += float(m[0])

        s = struct.pack(self.e + "i", 348)                            # int       - must be 348
        for n in range(0, 10):                                        # char[10]  - unused
            s += struct.pack(self.e + "c", bytes(" ", "utf-8"))
        for n in range(0, 18):                                        # char[18]  - unused
            s += struct.pack(self.e + "c", bytes(" ", "utf-8"))
        s += struct.pack(self.e + "i", 0)                             # int       - unused
        s += struct.pack(self.e + "h", 0)                             # short     - unused
        s += struct.pack(self.e + "c", bytes(" ", "utf-8"))           # char      - unused
        s += struct.pack(self.e + "c", bytes(self.dim_info, "utf-8")) # char      - MRI slice ordering ---- information not available in IFH
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
        s += bytes((self.descrip + "12345678901234567890123456789012345678901234567890123456789012345678901234567890")[0:80], "utf-8") # char[80]  - data description
        s += bytes((self.aux_file + "123456789012345678901234")[0:24], "utf-8") # char[24]  - auxilary filename
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
        s += bytes((self.intent_name + "1234567890123456")[0:16], "utf-8") # char[16]  - intent name
        s += bytes(self.magic[0:3] + chr(0), "utf-8")                 # char[4]   - magic word and zero char
        s += bytes((self.ext + chr(0) * 4)[0:4], "utf-8")             # char[4]   - extension

        return s

    def _packHdrV2(self):
        """Pack NIfTI-2 header (540 bytes base)"""

        # NIfTI-2 header is 540 bytes, see https://nifti.nimh.nih.gov/pub/dist/src/nifti2.h
        # Calculate vox_offset based on current metadata
        self.vox_offset = 544  # 540 header + 4 extension flag
        for m in self.meta:
            self.vox_offset += m[0]

        # Pack header fields in order, matching nifti2.h
        s = b''
        s += struct.pack(self.e + 'i', 540)  # sizeof_hdr
        s += bytes("n+2" + chr(0) + chr(13) + chr(10) + chr(26) + chr(10), "utf-8")  # magic
        s += struct.pack(self.e + 'h', self.data_type)
        s += struct.pack(self.e + 'h', self.bitpix)
        s += struct.pack(self.e + 'q', self.ndimensions)
        s += struct.pack(self.e + 'q', self.sizex)
        s += struct.pack(self.e + 'q', self.sizey)
        s += struct.pack(self.e + 'q', self.sizez)
        s += struct.pack(self.e + 'q', self.frames)
        s += struct.pack(self.e + 'q', self.size_5)
        s += struct.pack(self.e + 'q', self.size_6)
        s += struct.pack(self.e + 'q', self.size_7)
        s += struct.pack(self.e + 'd', self.intention1)
        s += struct.pack(self.e + 'd', self.intention2)
        s += struct.pack(self.e + 'd', self.intention3)
        s += struct.pack(self.e + 'd', self.pixdim_0)
        s += struct.pack(self.e + 'd', self.pixdim_x)
        s += struct.pack(self.e + 'd', self.pixdim_y)
        s += struct.pack(self.e + 'd', self.pixdim_z)
        s += struct.pack(self.e + 'd', self.pixdim_t)
        s += struct.pack(self.e + 'd', self.pixdim_5)
        s += struct.pack(self.e + 'd', self.pixdim_6)
        s += struct.pack(self.e + 'd', self.pixdim_7)
        s += struct.pack(self.e + 'q', int(self.vox_offset))
        s += struct.pack(self.e + 'd', self.scl_slope)
        s += struct.pack(self.e + 'd', self.scl_inter)
        s += struct.pack(self.e + 'd', self.cal_max)
        s += struct.pack(self.e + 'd', self.cal_min)
        s += struct.pack(self.e + 'd', self.slice_duration)
        s += struct.pack(self.e + 'd', self.toffset)
        s += struct.pack(self.e + 'q', self.slice_start)
        s += struct.pack(self.e + 'q', self.slice_end)
        s += bytes((self.descrip + ' ' * 80)[0:80], 'utf-8')
        s += bytes((self.aux_file + ' ' * 24)[0:24], 'utf-8')
        s += struct.pack(self.e + 'i', self.qform_code)
        s += struct.pack(self.e + 'i', self.sform_code)
        s += struct.pack(self.e + 'd', self.quatern_b)
        s += struct.pack(self.e + 'd', self.quatern_c)
        s += struct.pack(self.e + 'd', self.quatern_d)
        s += struct.pack(self.e + 'd', self.qoffset_x)
        s += struct.pack(self.e + 'd', self.qoffset_y)
        s += struct.pack(self.e + 'd', self.qoffset_z)
        s += struct.pack(self.e + 'dddd', *self.srow_x)
        s += struct.pack(self.e + 'dddd', *self.srow_y)
        s += struct.pack(self.e + 'dddd', *self.srow_z)
        s += struct.pack(self.e + 'i', self.slice_code)
        s += struct.pack(self.e + 'i', self.xyz_unit + self.t_unit)
        s += struct.pack(self.e + 'i', self.intent_code)
        s += bytes((self.intent_name + ' ' * 16)[0:16], 'utf-8')
        s += struct.pack(self.e + 'c', bytes(self.dim_info, 'utf-8'))
        s += bytes(chr(0) * 15, 'utf-8')

        # Pad to 540 bytes if needed
        if len(s) < 540:
            s += bytes(540 - len(s))
        elif len(s) > 540:
            s = s[:540]

        # Add extension flag (4 bytes) - part of the header structure
        if isinstance(self.ext, str):
            s += bytes(self.ext, 'utf-8')
        else:
            s += self.ext

        return s

    def unpackHdr(self, s):

        si = struct.calcsize('i')
        sc = struct.calcsize('c')
        sh = struct.calcsize('h')
        sf = struct.calcsize('f')
        sq = struct.calcsize('q')
        sd = struct.calcsize('d')

        # Detect NIfTI version by reading the first 4 bytes
        header_size, = struct.unpack(">i", s.read(si))

        if header_size == 348:
            # NIfTI-1
            self.nifti_version = 1
            s.seek(0)  # Reset to beginning
            return self._unpackHdrV1(s)
        elif header_size == 540:
            # NIfTI-2
            self.nifti_version = 2
            s.seek(0)  # Reset to beginning
            return self._unpackHdrV2(s)
        else:
            # Try little endian
            s.seek(0)
            header_size, = struct.unpack("<i", s.read(si))
            if header_size == 348:
                self.nifti_version = 1
                s.seek(0)
                return self._unpackHdrV1(s)
            elif header_size == 540:
                self.nifti_version = 2
                s.seek(0)
                return self._unpackHdrV2(s)
            else:
                raise ValueError(f"Invalid NIfTI header size: {header_size}")

    def _unpackHdrV1(self, s):

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
        self.dim_info        = self.dim_info.decode("utf-8", errors="ignore")
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
        t = s.read(si)                                                 # int       - unused
        t = s.read(si)                                                 # int       - unused

        self.descrip         = s.read(sc * 80).decode("utf-8")         # char[80]  - data description
        self.aux_file        = s.read(sc * 24).decode("utf-8")         # char[24]  - auxilary filename
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
        self.intent_name     = s.read(sc * 16).decode("utf-8")         # char[16]  - intent name
        self.magic           = s.read(sc * 4).decode("utf-8")          # char[4]   - magic word and zero char
        self.ext             = s.read(sc * 4).decode("utf-8")          # char[4]   - extension

        self.dType           = niftiDataTypes[self.data_type]

        t = self.xyzt_units
        self.xyz_unit = t % 8
        t = t - (t % 8)
        self.t_unit = t % 64


        # --- Read extensions

        self.meta = []
        pointer = 352

        # Check if extension flag is set (first byte should be 1)
        ext_flag = ord(self.ext[0]) if isinstance(self.ext, str) else self.ext[0]
        if ext_flag == 1:
            while pointer < self.vox_offset:
                msize = struct.unpack(e + "I", s.read(si))
                mcode = struct.unpack(e + "I", s.read(si))
                if pointer + msize[0] <= self.vox_offset:
                    mdata = s.read(msize[0] - 8)
                    pointer += msize[0]
                    self.meta.append([msize[0], mcode[0], mdata])
                else:
                    break
        return

    def _unpackHdrV2(self, s):
        """Unpack NIfTI-2 header (540 bytes)"""

        si = struct.calcsize('i')
        sc = struct.calcsize('c')
        sh = struct.calcsize('h')
        sf = struct.calcsize('f')
        sq = struct.calcsize('q')
        sd = struct.calcsize('d')

        # Determine endianness
        header_size, = struct.unpack(">i", s.read(si))
        if header_size == 540:
            e = ">"
        else:
            e = "<"
        self.e = e

        # Read magic string and verify NIfTI-2 format
        magic = s.read(sc * 8).decode("utf-8", errors="ignore")  # char[8]
        if not magic.startswith("ni2") and not magic.startswith("n+2"):
            raise ValueError("Invalid NIfTI-2 magic string")

        self.data_type,      = struct.unpack(e + "h", s.read(sh))      # short     - datatype
        self.bitpix,         = struct.unpack(e + "h", s.read(sh))      # short     - bits per voxel
        self.ndimensions,    = struct.unpack(e + "q", s.read(sq))      # int64     - number of dimensions used
        self.sizex,          = struct.unpack(e + "q", s.read(sq))      # int64     - size in dimension x
        self.sizey,          = struct.unpack(e + "q", s.read(sq))      # int64     - size in dimension y
        self.sizez,          = struct.unpack(e + "q", s.read(sq))      # int64     - size in dimension z
        self.frames,         = struct.unpack(e + "q", s.read(sq))      # int64     - number of frames (4th dimension)
        self.size_5,         = struct.unpack(e + "q", s.read(sq))      # int64     - size of 5th dimension
        self.size_6,         = struct.unpack(e + "q", s.read(sq))      # int64     - size of 6th dimension
        self.size_7,         = struct.unpack(e + "q", s.read(sq))      # int64     - size of 7th dimension
        self.intention1,     = struct.unpack(e + "d", s.read(sd))      # double    - intention 1 parameter
        self.intention2,     = struct.unpack(e + "d", s.read(sd))      # double    - intention 2 parameter
        self.intention3,     = struct.unpack(e + "d", s.read(sd))      # double    - intention 3 parameter
        self.pixdim_0,       = struct.unpack(e + "d", s.read(sd))      # double    - zero dimension size
        self.pixdim_x,       = struct.unpack(e + "d", s.read(sd))      # double    - x dimension size
        self.pixdim_y,       = struct.unpack(e + "d", s.read(sd))      # double    - y dimension size
        self.pixdim_z,       = struct.unpack(e + "d", s.read(sd))      # double    - z dimension size
        self.pixdim_t,       = struct.unpack(e + "d", s.read(sd))      # double    - t dimension size
        self.pixdim_5,       = struct.unpack(e + "d", s.read(sd))      # double    - 5 dimension size
        self.pixdim_6,       = struct.unpack(e + "d", s.read(sd))      # double    - 6 dimension size
        self.pixdim_7,       = struct.unpack(e + "d", s.read(sd))      # double    - 7 dimension size
        self.vox_offset,     = struct.unpack(e + "q", s.read(sq))      # int64     - offset of data
        self.scl_slope,      = struct.unpack(e + "d", s.read(sd))      # double    - slope of data scaling
        self.scl_inter,      = struct.unpack(e + "d", s.read(sd))      # double    - intersect of data scaling
        self.cal_max,        = struct.unpack(e + "d", s.read(sd))      # double    - maximum value
        self.cal_min,        = struct.unpack(e + "d", s.read(sd))      # double    - minimum value
        self.slice_duration, = struct.unpack(e + "d", s.read(sd))      # double    - slice duration
        self.toffset,        = struct.unpack(e + "d", s.read(sd))      # double    - time offset
        self.slice_start,    = struct.unpack(e + "q", s.read(sq))      # int64     - First slice index
        self.slice_end,      = struct.unpack(e + "q", s.read(sq))      # int64     - Last slice index

        self.descrip         = s.read(sc * 80).decode("utf-8")         # char[80]  - data description
        self.aux_file        = s.read(sc * 24).decode("utf-8")         # char[24]  - auxilary filename
        self.qform_code,     = struct.unpack(e + "i", s.read(si))      # int       - qform code
        self.sform_code,     = struct.unpack(e + "i", s.read(si))      # int       - sform code
        self.quatern_b,      = struct.unpack(e + "d", s.read(sd))      # double    - Quaternion b param
        self.quatern_c,      = struct.unpack(e + "d", s.read(sd))      # double    - Quaternion c param
        self.quatern_d,      = struct.unpack(e + "d", s.read(sd))      # double    - Quaternion d param
        self.qoffset_x,      = struct.unpack(e + "d", s.read(sd))      # double    - Quaternion x shift
        self.qoffset_y,      = struct.unpack(e + "d", s.read(sd))      # double    - Quaternion y shift
        self.qoffset_z,      = struct.unpack(e + "d", s.read(sd))      # double    - Quaternion z shift
        self.srow_x          = list(struct.unpack(e + "dddd", s.read(sd * 4)))     # double[4]  - affine transform row x
        self.srow_y          = list(struct.unpack(e + "dddd", s.read(sd * 4)))     # double[4]  - affine transform row y
        self.srow_z          = list(struct.unpack(e + "dddd", s.read(sd * 4)))     # double[4]  - affine transform row z
        self.slice_code,     = struct.unpack(e + "i", s.read(si))      # int       - slice order code
        self.xyzt_units,     = struct.unpack(e + "i", s.read(si))      # int       - codes for units used
        self.intent_code,    = struct.unpack(e + "i", s.read(si))      # int       - intent code
        self.intent_name     = s.read(sc * 16).decode("utf-8")         # char[16]  - intent name
        self.dim_info,       = struct.unpack(e + "c", s.read(sc))      # char      - MRI slice ordering
        self.dim_info        = self.dim_info.decode("utf-8", errors="ignore")

        t = s.read(sc * 15)                                            # char[15]  - unused (padding)
        self.ext             = s.read(sc * 4).decode("utf-8")          # char[4]   - extension

        # Set magic for NIfTI-2
        self.magic = magic
        self.dType = niftiDataTypes[self.data_type]

        t = self.xyzt_units
        self.xyz_unit = t % 8
        t = t - (t % 8)
        self.t_unit = t % 64

        # --- Read extensions
        self.meta = []
        pointer = 544  # NIfTI-2 header is 540 + 4

        # Check if extension flag is set (first byte should be 1)
        ext_flag = ord(self.ext[0]) if isinstance(self.ext, str) else self.ext[0]
        if ext_flag == 1:
            while pointer < self.vox_offset:
                msize = struct.unpack(e + "I", s.read(si))
                mcode = struct.unpack(e + "I", s.read(si))
                if pointer + msize[0] <= self.vox_offset:
                    mdata = s.read(msize[0] - 8)
                    pointer += msize[0]
                    self.meta.append([msize[0], mcode[0], mdata])
                else:
                    break
        return

    def readHeader(self, filename):

        sform = getImgFormat(filename)
        if sform == '.nii.gz':
            h = gzip.open(filename, 'rb')
        else:
            h = open(filename, 'rb')

        self.unpackHdr(h)
        h.close()

        return

    def writeHeader(self, filename):

        h = open(filename, "wb")
        s = self.packHdr()
        h.write(s)
        h.close()

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

    def convertToV1(self):
        """Convert NIfTI-2 header to NIfTI-1 format (if possible)"""
        if self.nifti_version == 1:
            return  # Already V1

        # Check if dimensions fit in int16
        max_dim = max(self.sizex, self.sizey, self.sizez, self.frames,
                     self.size_5, self.size_6, self.size_7)
        if max_dim > 32767:
            raise ValueError("Dimensions too large for NIfTI-1 (max 32767)")

        self.nifti_version = 1
        self.magic = "n+1" + chr(0)
        self.vox_offset = 352.0  # NIfTI-1 default offset

    def convertToV2(self):
        """Convert NIfTI-1 header to NIfTI-2 format"""
        if self.nifti_version == 2:
            return  # Already V2

        self.nifti_version = 2
        self.magic = "n+2" + chr(0) + chr(0x0D) + chr(0x0A) + chr(0x0D) + chr(0x0A)
        self.vox_offset = 544  # NIfTI-2 default offset

    def __str__(self):
        s = "# ----------------------------------\n# NIfTI Header (Version %d)\n\n" % self.nifti_version
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
                print("WARNING: %s not a valid key for NIfTI header" % (k))


def slice_image(sourcefile, targetfile, frames=1):
    """
    ``slice_image sourcefile=<source image> targetfile=<target image> [frames=1]``

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

        qunex slice_image sourcefile=bold1.nii.gz targetfile=bold1_f10.nii.gz frames=10
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

    sf = open(sourcefile, 'rb')
    df = open(targetfile, 'wb')

    df.write(sf.read(voxels * frames * 4))

    df.flush()
    os.fsync(df.fileno())
    sf.close
    df.close


def sliceNIfTI(sourcefile, targetfile, frames=1):
    sform = getImgFormat(sourcefile)
    tform = getImgFormat(targetfile)

    if sform == '.nii.gz':
        sf = gzip.open(sourcefile, 'rb')
    else:
        sf = open(sourcefile, 'rb')

    if tform == '.nii.gz':
        tf = gzip.open(targetfile, 'wb')
    else:
        tf = open(targetfile, 'wb')

    hdr = niftihdr()
    hdr.unpackHdr(sf)
    nvox = hdr.sizex * hdr.sizey * hdr.sizez
    hdr.frames = frames

    # Calculate offset based on NIfTI version
    header_base_size = 540 if hdr.nifti_version == 2 else 352
    tocopy = int(hdr.vox_offset - header_base_size + nvox * (hdr.bitpix / 8) * frames)

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

