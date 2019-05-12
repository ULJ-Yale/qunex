#!/usr/bin/env python2.7
# encoding: utf-8
"""
Created by Grega Repovs on 2013-10-07.
Adapted from previous joinFidl.py script
Copyright (c) Grega Repovs. All rights reserved.
"""

import niutilities.g_img as g
import niutilities.g_exceptions as ge
import re
import os
import os.path
import glob
import subprocess


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
    s = [[float(e[0])] + e[1:] for e in s if len(e) > 1]

    return {'header': header, 'TR': TR, 'events': s, 'source': fidlf}


def readConc(concf, TR):
    s = readLines(concf)
    nfiles = int(s[0].split(":")[1])
    print " ... %d bolds:" % (nfiles),
    s = [e for e in s if "file:" in e]

    if len(s) != nfiles:
        print "===> ERROR: number of bolds does not match the declaration! [%d vs %d]" % (len(s), nfiles)
        return []

    boldfiles = [e.split(":")[1].strip() for e in s]

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
        length = boldInfo(boldfile).frames * TR
        bolds.append([boldname, start, length, boldfile])
        start += length

    print
    return bolds


def joinFidl(concfile, fidlroot, outfolder=None, fidlname=None):
    '''
    joinFidl concfile=<reference_conc_file> fidlroot=<fidl_files_root_pattern> [fidlname=<optional fidl name>]

    Combines all the fild files matching root based on the information in conc file.
    - concfile:  the conc file to use as reference
    - fidlroot:  the root to use to find fild files
    - outfolder: the folder in which to save the results

    example: mnap joinFidl concfile=OP33-WM.conc fidlroot=OP33-WM
    '''

    # ---> find all fidl files, sort them, read them, get TR info

    if fidlname is None:
        fidlname = ""

    fidlf = glob.glob(fidlroot + '*.fidl')
    fidlf.sort()
    fidldata = [readFidl(f) for f in fidlf]
    try:
        TR = fidldata[0]['TR']
    except:
        if len(fidldata) == 0:
            raise ge.CommandFailed("joinFidl", "No fidl files", "No fidl files correspond to concfile: %s, fidlroot: %s!" % (concfile, fidlroot))
        else:
            raise ge.CommandFailed("joinFidl", "Error processing files", "Error in processing concfile: %s, fidlroot: %s!" % (concfile, fidlroot))

    # ---> read the conc file, check if the number matches

    print "\n===> reading %s" % (os.path.basename(concfile))
    bolddata = readConc(concfile, TR)

    if len(fidldata) != len(bolddata):
        print "\n========= ERROR ==========\nNumber of fidl files: \n - %s \nand bold runs: \n - %s \ndo not match!\n===========================\n" % ("\n - ".join(fidlf), "\n - ".join([e[3] for e in bolddata]))
        raise ge.CommandFailed("joinFidl", "File number mismatch", "Number of fidl [%d] and bold [%d] files do not match!" % (len(fidldata), len(bolddata)), "Please check report!")

    # ---> start the matching loop

    print "---> Matching bold and fidl files\n     \tBOLD file\tfidl file\tbold [s]\tfidl [s]\tdiff [s]\t "
    tfidl = []
    c = 0
    for bold in bolddata:

        w = ""
        sfidl = fidldata[c]

        if len(sfidl['events']) > 0:
            if len(sfidl['events'][-1]) > 2:
                levent = sfidl['events'][-1][0] + float(sfidl['events'][-1][2])
            else:
                levent = sfidl['events'][-1][0] - float(sfidl['events'][-1][1]) * TR
        else:
            levent = 0
            w = "WARNING: Empty fidl file [%s]!" % (sfidl['source'])

        dlen = bold[2] - levent

        if dlen >= 0:
            # print "last event in %s %.1fs [at: %.1f] before end of bold %d [%s length: %.1fs]" % (os.path.basename(fidlf[c]), dlen, sfidl['events'][-1][0], c+1, os.path.basename(bold[3]), bold[2])
            pass
        else:
            # print "WARNING: last event in %s %.1fs [at: %.1f] after end of bold %d [%s length: %.1fs]" % (os.path.basename(fidlf[c]), -dlen, sfidl['events'][-1][0], c+1, os.path.basename(bold[3]), bold[2])
            w = "WARNING: fidl too long for bold!"

        print "     \t%s\t%s\t%.1f\t%.1f\t%.1f\t%s" % (os.path.basename(bold[3]), os.path.basename(fidlf[c]), bold[2], levent, dlen, w)

        tfidl = tfidl + [[e[0] + bold[1]] + e[1:] for e in sfidl['events'] if e[0] < bold[2]]
        c += 1

    jointfile = fidlroot + fidlname + '.fidl'
    if outfolder is not None:
        if not os.path.exists(outfolder):
            print "--> Creating output folder:", outfolder
            os.makedirs(outfolder)
        jointfile = os.path.join(outfolder, os.path.basename(jointfile))

    out = open(jointfile, 'w')
    print >> out, sfidl['header']

    for l in tfidl:
        print >> out, "%g\t%s" % (l[0], "\t".join(l[1:]))

    out.close()
    return 


def joinFidlFolder(concfolder, fidlfolder=None, outfolder=None, fidlname=None):
    '''
    joinFidlFolder concfolder=<folder_with_conc_files> [fidlfolder=<folder_with_fidl_files>] [outfolder=<folder in which to save joint files>]

    Uses joinFidl to join all the fidl files that match the name of each conc file in the concfolder.
    - concfolder:  the folder with conc files
    - fidlfolder:  the folder with fidl files - defaults to concfolder if not provided
    - outfolder:   the folder in which the joint files should be saved, defauts to fidlfolder if not provided

    Example
    ------- 

    mnap joinFidlFolder concfolder=concs fidlfolder=fidls

    ----------------
    Written by Grega Repovš 
    
    Change log

    2019-05-12 Grega Repovš
             - Reports an error if no conc file is found to process
    '''

    if fidlfolder is None:
        fidlfolder = concfolder

    if outfolder is None:
        outfolder = fidlfolder

    concfiles = glob.glob(concfolder + '/*.conc')

    if not concfiles:
        raise ge.CommandFailed("joinFidlFolder", "No conc files founr", "No conc files found to process!", "Please check your data!")

    failed = []
    for concfile in concfiles:
        root = os.path.join(fidlfolder, os.path.basename(concfile).replace('.conc', ""))
        try:
            joinFidl(concfile, root, outfolder, fidlname)
        except ge.CommandFailed as e:
            failed.append([concfolder, e.error])

    if failed:
        print "ERROR: Joining fidls failed for the following conc files:"
        for concfile, error in failed:
            print "       - %s [%s]" % (concfile, error)

        raise ge.CommandFailed("joinFidlFolder", "Processing of %d subject(s) failed" % (len(failed)), "Please check report!")


def splitFidl(concfile, fidlfile, outfolder=None):
    """
    splitFidl concfile=<reference_conc_file> fidlfile=<fidl_file_to_split> [outfolder=<folder_to_save_results>]

    Splits a multi-bold fidl file into run specific bold files based on the sequence of bold files in conc file and their lengths.

    - concfile:  the path to the conc file
    - fidlfile:  the path to the fidl file
    - outfolder: the path to the folder to put split fidls in
    """

    # ---> read the fidl and conc info

    fidldata = readFidl(fidlfile)
    try:
        TR = fidldata['TR']
    except:
        if len(fidldata) == 0:
            raise ge.CommandFailed("splitFidl", "No fidl file", "No fidl files correspond to %s!" % (concfile))
        else:
            raise ge.CommandFailed("splitFidl", "Processing error", "Error in processing concfile: %s, fidlfile: %s!" % (concfile, fidlfile))

    bolddata = readConc(concfile, TR)

    # ---> start the split loop

    bstart = 0
    for bold in bolddata:
        # [boldname, start, length, boldfile]

        bend = bstart + bold[2]

        # ---> open fidl file

        ffile = fidlfile.replace(".fidl", "_%s.fidl" % (bold[0]))
        if outfolder is not None:
            ffile = os.path.join(outfolder, ffile)
        ffile = open(ffile, 'w')

        # ---> print header

        print >> ffile, fidldata['header']

        # return {'header': header, 'TR':TR, 'events':s, 'source': fidlf}

        # ---> print contents

        for l in fidldata['events']:
            if l[0] >= bstart and l[0] < bend:
                print >> ffile, "%.2f\t%s" % (l[0] - bstart, "\t".join(l[1:]))

        # ---> close fidl file

        ffile.close()

        bstart = bend

    return


def checkFidl(fidlfile=None, fidlfolder=".", plotfile=None, allcodes=None):
    '''
    checkFidl [fidlfile=] [fidlfolder=.] [plotfile=] [allcodes=false] [verbose=true]

    Prints figures showing fidl events and their duration.

    - fidlfile:   The path to the fidl file to plot. All the fidl files in the folder if none specified.
    - fidlfolder: The folder from which to plot the fidl files.
    - plotfile:   The name of the file to save the plot to. Only makes sense if fidlfile is specified.
    - allcodes:   Whether to plot line for all fidl codes even if no event has a particular code.
    - verbose:    Whether to report progress

    Example
    -------

    mnap checkFidl fidlfolder=jfidls

    ----------------
    Written by Grega Repovš 
    
    Change log

    2019-05-12 Grega Repovš
             - Reports an error if no fidl file is found to process
    '''

    if fidlfile:
        if not os.path.exists(fidlfile):
            raise ge.CommandFailed("checkFidl", "Fidl file does not exist", "The specified fidl file does not exist [%s]" % (fidlfile), "Please check your data!")
    else:
        if not glob.glob(os.path.join(os.path.abspath(fidlfolder), "*.fidl")):
            raise ge.CommandFailed("checkFidl", "No fidl files found", "No fidl files found to process in the specified folder [%s]" % (fidlfolder), "Please check your data!")   

    command = ['Rscript', os.path.join(os.environ['MNAPPATH'], 'niutilities', 'g_CheckFidl.R')]
    command.append('-fidlfolder=%s' % (fidlfolder))

    if fidlfile is not None:
        command.append("-fidlfile=" + fidlfile)
    if plotfile is not None:
        command.append("-plotfile=" + plotfile)
    if allcodes is not None:
        command.append("-allcodes")

    if subprocess.call(command):
        raise ge.CommandFailed("checkFidl", "Running checkFidl.R failed", "Call: %s" % (" ".join(command)))

    return


