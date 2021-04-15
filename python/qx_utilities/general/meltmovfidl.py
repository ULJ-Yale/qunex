#!/usr/bin/env python2.7
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``meltmovfidl``
"""

"""
Created by Grega Repovs on 2011-07-30
Copyright (c) Grega Repovs. All rights reserved.
"""

import sys
import getopt
import re
import os
import os.path
import glob
import img

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def meltmovfidl(cfile, ifile, iffile, offile):
    """
    ``meltmovfidl <concfile> <ignore_fidl_pattern> <input_fidl_file> <output_fidl_file>``

    Checks movement folder for each bold file specified in 
    <concfile> for corresponding scrub fidl file matching <ignore_fild_pattern>
    It then melts information on frames to be ignored into the <input_fidl_file> 
    and saves it to <output_fidl_file>.

    Take into account that it expects bold runs and ignore .fidl files to both
    match b.*[1-9] pattern.
    """

    # ---> read the original fidl file
    
    ofidl = img.fidl(iffile)
    
    # ---> create list of bolds with their offset times in conc
    
    bolds = img.readConc(cfile)
    c = 0
    for bold in bolds:
        
        # ---> add matching fidl ignore file
        
        ifidl = glob.glob(os.path.join(os.path.dirname(bold[0]), 'movement', "*"+ifile))
        m = re.compile(".*b.*?%s[^0-9].*" % bold[1])
        ifidl = [e for e in ifidl if m.match(os.path.basename(e))]

        if len(ifidl) != 1:
            raise Usage("ERROR: Can not match ignore fidl file to: %s (%s)" % (bold[0], bold[1]))
        
        ifidl = img.fidl(ifidl[0])
        ifidl.adjustTime(c)
        ofidl.merge(ifidl, addcodes=False)
        
        # ---> read and add information on length
        info = img.readBasicInfo(bold[0])
        c += ofidl.TR * info['frames']    
        
    ofidl.save(offile)
        


def main(argv=None):
    options = {"TR": 2.5, 'verbose':False}
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hv", ["help", "verbose"])
        except getopt.error, msg:
            raise Usage(msg)
    
        # option processing
        for option, _ in opts:
            if option == "-v":
                options['verbose'] = True

    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "for help use --help"
        return 2
    
    cfile  = args[0]
    ifile  = args[1]
    iffile = args[2]
    offile = args[3]
    
    try:
        meltmovfidl(cfile, ifile, iffile, offile)
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "for help use --help"
        return 2
    
    


if __name__ == "__main__":
    sys.exit(main())
