#!/usr/bin/env python
# encoding: utf-8
"""
Created by Grega Repovs on 2013-10-07.
Adapted from previous joinFidl.py script
Copyright (c) Grega Repovs. All rights reserved.
"""

import g_mri.g_img as g
import sys
import getopt
import re
import os
import os.path
import glob


ifh2info = {'matrix size [1]': 'xlen', 'matrix size [2]': 'ylen', 'matrix size [3]': 'zlen', 'matrix size [4]': 'frames', 'scaling factor (mm/pixel) [1]': 'xsize', 'scaling factor (mm/pixel) [2]': 'ysize', 'scaling factor (mm/pixel) [3]': 'zsize'}

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def readLines(filename):
    s = file(filename).read()
    s = s.replace("\r", "\n")
    s = s.replace("\n\n", "\n")
    s = s.split("\n")
    return s

def boldInfo(boldfile):
    if ".4dfp.img" in boldfile:
        ifhfile = boldfile.replace('.img', '.ifh')
        ifh = g.ifhhdr(ifhfile)
        hdr = ifh.toNIfTI()
    elif ".nii" in boldfile:
        hdr = g.niftihdr(boldfile)
    else:
        hdr = None

    return hdr

def readFidl(fidlf):
    s = readLines(fidlf)

    header = s.pop(0)
    TR = float(header.split()[0])

    s = [e.split() for e in s]
    s = [[float(e[0])]+e[1:] for e in s if len(e) > 1]

    return {'header': header, 'TR':TR, 'events':s, 'source': fidlf}

def readConc(concf, TR):
    s = readLines(concf)
    nfiles = int(s[0].split(":")[1])
    print " ... %d bolds:" % (nfiles),
    boldfiles = [e.split(":")[1].strip() for e in s[1:nfiles+1]]

    for boldfile in boldfiles:
        if not os.path.exists(boldfile):
            print
            print "===> ERROR: image does not exist! (%s)" % (boldfile)
            return []

    # m = re.compile('_b.*?([0-9]+)')
    m = re.compile(".*/.*?[bold]*?([0-9]+)(/|\.).*")
    bolds = []
    start = 0
    for boldfile in boldfiles:
        boldname = m.match(boldfile).group(1)
        print boldname,
        length   = boldInfo(boldfile).frames * TR
        bolds.append([boldname, start, length, boldfile])
        start += length

    print
    return bolds


def joinFidl(concfile, fidlroot, outfolder=None):
    """
    Joins fidl files matching root pattern based on the sequence of bold files in conc file and their lengths.
    concfile - the path to the conc file
    root  - root pattern of the fidl files
    """

    # ---> find all fidl files, sort them, read them, get TR info

    fidlf = glob.glob(fidlroot+'*.fidl')
    fidlf.sort()
    fidldata = [readFidl(f) for f in fidlf]
    try:
        TR = fidldata[0]['TR']
    except:
        if len(fidldata) == 0:
            print "===> WARNING: No fidl files correspond to %s!" % (concfile)
        else:
            print "===> WARNING: Error in processing concfile: %s, fidlroot: %s!" % (concfile, fidlrrot)
        return

    # ---> read the conc file, check if the number matches

    bolddata = readConc(concfile, TR)

    if len(fidldata) != len(bolddata):
    	print "\n========= ERROR ==========\nNumber of fidl files: \n - %s \nand bold runs: \n - %s \ndo not match!\n===========================\n" % ("\n - ".join(fidlf), "\n - ".join([e[3] for e in bolddata]))
    	return False

    # ---> start the matching loop

    print "---> Matching bold and fidl files\n     \tBOLD file\tfidl file\tbold [s]\tfidl [s]\tdiff [s]\t "
    tfidl = []
    c = 0
    for bold in bolddata:
        sfidl = fidldata[c]
       	dlen = bold[2] - sfidl['events'][-1][0]

       	w = ""
        if dlen >=0:
            # print "last event in %s %.1fs [at: %.1f] before end of bold %d [%s length: %.1fs]" % (os.path.basename(fidlf[c]), dlen, sfidl['events'][-1][0], c+1, os.path.basename(bold[3]), bold[2])
            pass
        else:
            # print "WARNING: last event in %s %.1fs [at: %.1f] after end of bold %d [%s length: %.1fs]" % (os.path.basename(fidlf[c]), -dlen, sfidl['events'][-1][0], c+1, os.path.basename(bold[3]), bold[2])
            w = "WARNING: fidl too long for bold!"

        print "     \t%s\t%s\t%.1f\t%.1f\t%.1f\t%s" % (os.path.basename(bold[3]), os.path.basename(fidlf[c]), bold[2], sfidl['events'][-1][0], dlen, w)

        tfidl = tfidl + [[e[0]+bold[1]]+e[1:] for e in sfidl['events'] if e[0] < bold[2]]
        c += 1

    jointfile = fidlroot + '.fidl'
    if outfolder is not None:
        jointfile = os.path.join(outfolder, os.path.basename(jointfile))

    out = open(jointfile, 'w')
    print >> out, sfidl['header']

    for l in tfidl:
        print >> out, "%g\t%s" % (l[0], "\t".join(l[1:]))

    out.close()
    return True


def joinFidlFolder(concfolder, fidlfolder=None, outfolder=None):
    """
    Looks up all conc files in a conc folder and tries to match them up with fidl files in the fidl folder.
    It expects fidl files to have the same root as the conc file.
    concfolder - folder with conc files
    fidlfolder - folder with fidl files (same as concfolder is none)
    """
    if fidlfolder is None:
        fidlfolder = concfolder

    if outfolder is None:
        outfolder = fidlfolder

    concfiles = glob.glob(concfolder+'/*.conc')

    for concfile in concfiles:
        root = os.path.join(fidlfolder, os.path.basename(concfile).replace('.conc', ''))
        joinFidl(concfile, root, outfolder)


def splitFidl(concfile, fidlfile, outfolder=None):
    """
    Split a multi-bold fidl file into run specific bold files based on the sequence of bold files in conc file and their lengths.
    concfile - the path to the conc file
    fidlfile - the path to the fidl file
    root  - root pattern of the fidl files
    """

    # ---> read the fidl and conc info

    fidldata = readFidl(fidlfile)
    try:
        TR = fidldata['TR']
    except:
        if len(fidldata) == 0:
            print "===> WARNING: No fidl files correspond to %s!" % (concfile)
        else:
            print "===> WARNING: Error in processing concfile: %s, fidlfile: %s!" % (concfile, fidlfile)
        return

    bolddata = readConc(concfile, TR)

    # ---> start the split loop

    bstart = 0
    for bold in bolddata:
        # [boldname, start, length, boldfile]

        bend = bstart + bold[2]

        # ---> open fidl file

        ffile = fidlfile.replace(".fidl", "_%s.fidl" % (bold[0]))
        if outfolder != None:
            ffile = os.path.join(outfolder, ffile)
        ffile = open(ffile, 'w')

        # ---> print header

        print >> ffile, fidldata['header']

        # return {'header': header, 'TR':TR, 'events':s, 'source': fidlf}

        # ---> print contents

        for l in fidldata['events']:
            if l[0] >= bstart and l[0] < bend:
                print >> ffile, "%.2f\t%s" % (l[0]-bstart, "\t".join(l[1:]))

        # ---> close fidl file

        ffile.close()

        bstart = bend

    return True