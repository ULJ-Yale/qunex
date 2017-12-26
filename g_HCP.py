#!/usr/bin/env python
# encoding: utf-8
"""
g_HCP.py

Functions for preparing information and mapping images to a HCP preprocessing
compliant folder structure:

* setupHCP        ... maps the data to a hcp folder
* setupHCPFolder  ... runs setupHCP for all subject folders
* getHCPReady     ... prepares subject.txt files for HCP mapping

The commands are accessible from the terminal wusing gmri utility.

Copyright (c) Grega Repovs. All rights reserved.
"""

import os
import glob
import niutilities
import collections
import niutilities.g_gimg as g
import os.path


def setupHCP(folder=".", tfolder="hcp", sbjf="subject_hcp.txt"):
    '''
    setupHCP [folder=.] [tfolder=hcp] [sbjf=subject_hcp.txt]

    USE
    ===

    The command maps images from the subject's nii folder into a folder
    structure that conforms to the naming conventions used in the HCP
    minimal preprocessing workflow. For the mapping to be correct, the
    command expects the source subject.txt file (sbjf) to hold the relevant
    information on images. To save space, the images are not copied into the new
    folder structure but rather hard-links are created if possible.

    PARAMETERS
    ==========

    --folder   The base subject folder that contains the nifti images and
               subject.txt file. [.]
    --tfolder  The folder (within the base folder) to which the data is to be
               mapped. [hcp]
    --sbjf     The name of the source subject.txt file. [subject_hcp.txt]

    IMAGE DEFINITION
    ================

    For the mapping to work, each MR to be mapped has to be marked with the
    appropriate image type in the source.txt file. The following file types
    are recognized and will be mapped correctly:

    T1w             ... T1 weighted high resolution structural image
    T2w             ... T2 weighted high resolution structural image
    FM-GE           ... Gradient echo field map image used for distortion
                        correction
    FM-Magnitude    ... Field mapping magnitude image used for distortion
                        correction
    FM-Phase        ... Field mapping phase image used for distortion
                        correction
    boldref[N]      ... Reference image for the following BOLD image
    bold[N]         ... BOLD image
    SE-FM-AP        ... Spin-echo fieldmap image recorded using the A-to-P
                        frequency readout direction
    SE-FM-PA        ... Spin-echo fieldmap image recorded using the P-to-A
                        frequency readout direction
    SE-FM-LR        ... Spin-echo fieldmap image recorded using the L-to-R
                        frequency readout direction
    SE-FM-RL        ... Spin-echo fieldmap image recorded using the R-to-L
                        frequency readout direction
    DWI             ... Diffusion weighted image

    Example definition
    ------------------

    hcpready: true
    01:                 :Survey
    02: T1w             :T1w 0.7mm N1
    03: T2w             :T2w 0.7mm N1
    04:                 :Survey
    05: SE-FM-AP        :C-BOLD 3mm 48 2.5s FS-P
    06: SE-FM-PA        :C-BOLD 3mm 48 2.5s FS-A
    07: bold1:WM        :BOLD 3mm 48 2.5s
    08: bold2:WM        :BOLD 3mm 48 2.5s
    09: bold3:WM        :BOLD 3mm 48 2.5s
    10: bold4:WM        :BOLD 3mm 48 2.5s
    11: bold5:WM        :BOLD 3mm 48 2.5s
    12: bold6:WM        :BOLD 3mm 48 2.5s
    13: bold7:rest      :RSBOLD 3mm 48 2.5s
    14: bold8:rest      :RSBOLD 3mm 48 2.5s

    EXAMPLE USE
    ===========

    gmri setupHCP folder=OP316 sbjf=subject.txt

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-07 Grega Repovš
             - Updated documentation
    2017-08-17 Grega Repovš
             - Added mapping of GE Field Map images

    '''

    inf = niutilities.g_core.readSubjectData(os.path.join(folder, sbjf))[0][0]

    basef    = os.path.join(folder, tfolder, inf['id'])
    rawf     = inf['raw_data']
    sid      = inf['id']
    bolds    = collections.defaultdict(dict)
    nT1w     = 0
    nT2w     = 0

    if not os.path.exists(rawf):
        print "ERROR: raw_data folder for %s does not exist! Check your paths [%s]! Aborting setupHCP.\n" % (sid, rawf)
        return

    print " ---===== Setting up HCP folder structure for %s =====---\n" % (sid)

    if not os.path.exists(basef):
        print " ---> Creating base folder %s " % (basef)
        os.makedirs(basef)
    else:
        print " ...  Base folder %s already exists " % (basef)

    i = [k for k, v in inf.iteritems() if k.isdigit()]
    i.sort(key=int, reverse=True)
    boldn = '99'

    for k in i:
        v = inf[k]
        if 'o' in v:
            orient = "_" + v['o']
        else:
            orient = ""
        if v['name'] == 'T1w':
            nT1w += 1
            if os.path.exists(os.path.join(rawf, k + ".nii.gz")):
                sfile = k + ".nii.gz"
            else:
                sfile = k + "-o.nii.gz"
            tfile = sid + "_strc_T1w_MPR%d.nii.gz" % (nT1w)
            tfold = "T1w"
        elif v['name'] == "T2w":
            nT2w += 1
            if os.path.exists(os.path.join(rawf, k + ".nii.gz")):
                sfile = k + ".nii.gz"
            else:
                sfile = k + "-o.nii.gz"
            tfile = sid + "_strc_T2w_SPC%d.nii.gz" % (nT2w)
            tfold = "T2w"
        elif v['name'] == "FM-GE":
            sfile = k + ".nii.gz"
            tfile = sid + "_strc_FieldMap_GE.nii.gz"
            tfold = "FieldMap_strc"
        elif v['name'] == "FM-Magnitude":
            sfile = k + ".nii.gz"
            tfile = sid + "_strc_FieldMap_Magnitude.nii.gz"
            tfold = "FieldMap_strc"
        elif v['name'] == "FM-Phase":
            sfile = k + ".nii.gz"
            tfile = sid + "_strc_FieldMap_Phase.nii.gz"
            tfold = "FieldMap_strc"
        elif "boldref" in v['name']:
            boldn = v['name'][7:]
            sfile = k + ".nii.gz"
            tfile = sid + "_fncb_BOLD_" + boldn + orient + "_SBRef.nii.gz"
            tfold = "BOLD_" + boldn + orient + "_SBRef_fncb"
            bolds[boldn]["ref"] = sfile
        elif "bold" in v['name']:
            boldn = v['name'][4:]
            sfile = k + ".nii.gz"
            tfile = sid + "_fncb_BOLD_" + boldn + orient + ".nii.gz"
            tfold = "BOLD_" + boldn + orient + "_fncb"
            bolds[boldn]["bold"] = sfile
        elif v['name'] == "SE-FM-AP":
            sfile = k + ".nii.gz"
            tfile = sid + "_fncb_BOLD_AP_SB_SE.nii.gz"
            tfold = "SpinEchoFieldMap" + boldn + "_fncb"
        elif v['name'] == "SE-FM-PA":
            sfile = k + ".nii.gz"
            tfile = sid + "_fncb_BOLD_PA_SB_SE.nii.gz"
            tfold = "SpinEchoFieldMap" + boldn + "_fncb"
        elif v['name'] == "SE-FM-LR":
            sfile = k + ".nii.gz"
            tfile = sid + "_fncb_BOLD_LR_SB_SE.nii.gz"
            tfold = "SpinEchoFieldMap" + boldn + "_fncb"
        elif v['name'] == "SE-FM-RL":
            sfile = k + ".nii.gz"
            tfile = sid + "_fncb_BOLD_RL_SB_SE.nii.gz"
            tfold = "SpinEchoFieldMap" + boldn + "_fncb"
        elif v['name'] == "DWI":
            sfile = [k + e for e in ['.nii.gz', '.bval', '.bvec']]
            tbase = "_".join([sid, 'DWI', v['task']])
            tfile = [tbase + e for e in ['.nii.gz', '.bval', '.bvec']]
            tfold = "Diffusion"
        else:
            print " ... skipping %s %s" % (v['ima'], v['name'])
            continue

        if type(sfile) is not list:
            sfile = [sfile]
        if type(tfile) is not list:
            tfile = [tfile]

        for sfile, tfile in zip(list(sfile), list(tfile)):
            if not os.path.exists(os.path.join(rawf, sfile)):
                print " ---> WARNING: Can not locate %s - skipping the file" % (os.path.join(rawf, sfile))
                continue

            if not os.path.exists(os.path.join(basef, tfold)):
                print " ---> creating subfolder", tfold
                os.makedirs(os.path.join(basef, tfold))
            else:
                print " ...  %s subfolder already exists", (tfold)

            if not os.path.exists(os.path.join(basef, tfold, tfile)):
                print " ---> linking %s to %s" % (sfile, tfile)
                os.link(os.path.join(rawf, sfile), os.path.join(basef, tfold, tfile))
            else:
                print " ---> %s already exists" % (tfile)
                # print " ---> %s already exists, replacing it with %s " % (tfile, sfile)
                # os.remove(os.path.join(basef,tfold,tfile))
                # os.link(os.path.join(rawf, sfile), os.path.join(basef,tfold,tfile))

    # --- checking if all bolds have refs

    # for k, v in bolds.iteritems():
    #     if "ref" not in v:
    #         tfold = "BOLD_"+k+"_SBRef_fncb"
    #         tfile = sid + "_fncb_BOLD_"+boldn+"_SBRef.nii.gz"
    #
    #         if not os.path.exists(os.path.join(rawf, v["bold"])):
    #             print " ---> WARNING: Can not locate %s - skipping extraction of first frame" % (os.path.join(rawf, v["bold"]))
    #             continue
    #
    #         if not os.path.exists(os.path.join(basef,tfold)):
    #             print " ---> creating subfolder", tfold
    #             os.makedirs(os.path.join(basef,tfold))
    #         else:
    #             print " ...  %s subfolder already exists", tfold
    #
    #         if not os.path.exists(os.path.join(basef,tfold,tfile)):
    #             print " ---> extracting first frame of %s to %s" % (v["bold"], tfile)
    #             img = g.gimg(os.path.join(rawf, v["bold"]), 1)
    #             img.saveimage(os.path.join(basef,tfold,tfile))
    #
    #         else:
    #             print " ...  %s already exists" % (tfile)


    print "\n ---=====         DONE          =====---\n"




def setupHCPFolder(folder=".", tfolder="hcp", sbjf="subject_hcp.txt", check="interactive"):
    '''
    setupHCPFolder [folder=.] [tfolder=hcp] [sbjf=subject_hcp.txt] [check=interactive]

    USE
    ===

    The command is used to map MR images into a HCP prepocessing folder
    structure for all the subject folders it finds within the specified
    origin folder (folder).

    Specifically, the command looks for source subject.txt files (sbjf) in all
    the subfolders of the origin folder (folder). For each found source
    subject.txt file it checks whether the file is hcp ready and if the target
    folder (tfolder) exists. If the file is ready and if the target folder
    does not yet exists, it runs setupHCP command mapping the files to the
    target folder as specified in the source subject.txt file.

    If the source subject.txt file does not seem to be ready or if the target
    folder exists, the action depends on check parameter. If check is "yes",
    the subject is not processed, if check is set to "no" the subject is
    processed. If check is set to "interactive" the user is asked whether the
    subject should be processed or not.

    PARAMETERS
    ==========

    --folder   The origin folder that holds the subjects' folders (usually
               "subjects"). [.]
    --tfolder  The target HCP folder in which to set up data for HCP
               preprocessing (usually "hcp"). [hcp]
    --sbjf     The source subject.txt file to use for mapping to a target HCP
               folder. [subject_hcp.txt]
    --check    Whether to check if the subject is safe to run (yes), run in any
               case (no) or ask the user (interactive) if in doubt.

    EXAMPLE USE
    ===========

    gmri setupHCPFolder folder=subjects check=no

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-07 Grega Repovš
             - Updated documentation.
    '''

    # list all possible sbjfiles and check them

    sfiles = glob.glob(os.path.join(folder, "*", sbjf))
    flist  = []

    print "---> checking %s files and %s folders in %s" % (sbjf, tfolder, folder)

    for sfile in sfiles:

        ok = True
        status = "     ... %s: " % (os.path.basename(os.path.dirname(sfile)))

        # --- check if sbjf is hcp ready

        lines = [line.split(":") for line in open(sfile)]
        lines = [[e.strip() for e in line] for line in lines if len(line) == 2]
        lines = dict(lines)

        ready = False
        if "hcpready" in lines:
            if lines["hcpready"].lower() == "true":
                ready = True

        if ready:
            status += "%s is hcp ready" % (sbjf)
        else:
            status += "%s does not appear to be hcp ready" % (sbjf)
            ok = False

        # --- check if tfolder exists

        if os.path.exists(os.path.join(os.path.dirname(sfile), tfolder)):
            fex = True
            status += ", %s folder allready exist" % (tfolder)
            ok = False
        else:
            fex = False
            status += ", %s folder does not yet exist" % (tfolder)

        process = True
        if ok or check == "no":
            print status, " => processing the subject"
        elif check == "yes":
            print status, " => skipping this subject"
        elif check == "interactive":
            print status
            s = raw_input("     ---> do you want to process this subject [y/n]: ")
            if s != 'y':
                process = False

        flist.append((sfile, ready, fex, ok, process))

    for sfile, ready, fex, ok, process in flist:
        if process:
            setupHCP(folder=os.path.dirname(sfile), tfolder=tfolder, sbjf=sbjf)

    print "\n\n===> done processing %s\n" % (folder)


def getHCPReady(folder=".", sfile="subject.txt", tfile="subject_hcp.txt", pattern=None, mapping=None):
    '''
    getHCPReady [folder=.] [sfile=subject.txt] [tfile=subject_hcp.txt] [pattern="*"] [mapping=specs/hcpmap.txt]

    USE
    ===

    The command is used to prepare subject.txt files so that they hold the
    information necessary for correct mapping to a fodler structure supporting
    HCP preprocessing.

    The command checks all the directories in the folder that match the pattern,
    looking for the presence of specified source file (sfile). If the source
    file is found, each sequence name is checked against the source specified in
    the mapping file (mapping), and replaced with the provided text. The results
    are then saved to the specified target file (tfile). The resulting files will
    have "hcpready: true" key-value pair added.

    PARAMETERS
    ==========

    --folder   the directory that holds subjects' folders (usually "subjects") [.]
    --sfile    the "source" subject.txt file [subject.txt]
    --tfile    the "target' subject.txt file [subject_hcp.txt]
    --pattern  glob pattern to use in identifying subject folders ["*"]
    --mapping  the path to the text file describing the mapping [specs/hcpmap.txt]

    Mapping specification
    ---------------------

    The mapping file specifies what source text is to be replaced with what
    target text. There are no limits to the number of mappings. Mappings that
    are not found in the source file will not be used. All lines not matching
    the pattern are ignored, as well as lines that start with #. Each mapping
    is to be specified in a single line in a form:

    "<source text> => <replacement text>"

    Example lines in a mapping file:

    C-BOLD 3mm 48 2.5s FS-P => SE-FM-AP
    C-BOLD 3mm 48 2.5s FS-A => SE-FM-PA

    T1w 0.7mm N1 => T1w
    T1w 0.7mm N2 => T1w
    T2w 0.7mm N1 => T2w
    T2w 0.7mm N2 => T2w

    RSBOLD 3mm 48 2.5s  => bold:rest
    BOLD 3mm 48 2.5s    => bold:WM

    EXAMPLE USE
    ===========

    gmri getHCPReady folder=subjects pattern="OP*" mapping=subjects/maphcp.txt

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-07 Grega Repovš
             - Updated documentation.
    2017-12-26 Grega Repovš
             - Set to ignore lines that start with # in mapping file.
    '''

    if pattern is None:
        pattern = "*"
    if mapping is None:
        mapping = os.path.join(folder, 'specs', 'hcpmap.txt')

    # -- get mapping ready

    if not os.path.exists(mapping):
        print "ERROR: No HCP mapping file found. Aborting."
        return

    print " ... Reading HCP mapping from %s" % (mapping)

    mapping = [line.strip() for line in open(mapping) if line[0] != "#"]
    mapping = [e.split('=>') for e in mapping]
    mapping = [[f.strip() for f in e] for e in mapping if len(e) == 2]
    mapping = dict(mapping)

    # -- get list of subject folders

    sfolders = glob.glob(os.path.join(folder, pattern))

    # -- loop through subject folders

    for sfolder in sfolders:

        ssfile = os.path.join(sfolder, sfile)
        stfile = os.path.join(sfolder, tfile)

        if not os.path.exists(ssfile):
            continue
        print " ... Processing folder %s" % (sfolder)


        lines = [line.strip() for line in open(ssfile)]

        images = False
        hcpok  = False
        bold   = 0
        nlines = []
        hasref = False
        for line in lines:
            e = line.split(':')
            if len(e) > 1:
                if e[0].strip() == 'hcpready' and e[1].strip() == 'true':
                    hcpok = True
                if e[0].strip().isdigit():
                    if not images:
                        nlines.append('hcpready: true')
                        images = True

                    oimg = e[1].strip()
                    if oimg in mapping:
                        repl  = mapping[oimg]
                    else:
                        repl  = " "

                    if 'boldref' in repl:
                        bold += 1
                        repl = repl.replace('boldref', 'boldref%d' % (bold))
                        hasref = True
                    elif 'bold' in repl:
                        if hasref:
                            hasref = False
                        else:
                            bold += 1
                        repl = repl.replace('bold', 'bold%d' % (bold))

                    e[1] = " %-16s:%s" % (repl, oimg)
                    nlines.append(":".join(e))
                else:
                    nlines.append(line)
            else:
                nlines.append(line)

        if hcpok:
            print "     ... %s already HCP ready" % (sfile)
        else:
            print "     ... writing %s" % (tfile)
            fout = open(stfile, 'w')
            for line in nlines:
                print >> fout, line


