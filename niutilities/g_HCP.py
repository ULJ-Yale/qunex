#!/usr/bin/env python2.7
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
import shutil
import niutilities
import collections
import niutilities.g_exceptions as ge
import os.path
import g_core


def setupHCP(sfolder=".", tfolder="hcp", sfile="subject_hcp.txt", check="yes", existing="add"):
    '''
    setupHCP [sfolder=.] [tfolder=hcp] [sfile=subject_hcp.txt] [check=yes] [existing=add]

    USE
    ===

    The command maps images from the subject's nii folder into a folder
    structure that conforms to the naming conventions used in the HCP
    minimal preprocessing workflow. For the mapping to be correct, the
    command expects the source subject.txt file (sfile) to hold the relevant
    information on images. To save space, the images are not copied into the new
    folder structure but rather hard-links are created if possible.

    PARAMETERS
    ==========

    --sfolder   The base subject folder that contains the nifti images and
                subject.txt file. [.]
    --tfolder   The folder (within the base folder) to which the data is to be
                mapped. [hcp]
    --sfile     The name of the source subject.txt file. [subject_hcp.txt]
    --check     Whether to check if subject is marked ready for setting up
                hcp folder [yes].
    --existing  What to do if the hcp folder already exists? Options are:
                abort -> abort setting up hcp folder
                add   -> leave existing files and add new ones (default)
                clear -> remove any exisiting files and redo hcp mapping

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

    
    In addition to these parameters, it is also possible to optionally specify, 
    which spin-echo image to use for distortion correction, by adding 
    `:se(<number of se image>)` to the line, as well as frequency encoding
    direction by adding `:fenc(<direction>)` to the line. In case of 
    spin-echo images themselves, the number denotes the number of the
    image itself.
    
    If these information are not provided the spin-echo image to use will be
    deduced based on the order of images, and frequency encoding direction 
    will be taken as default from the relevant HCP processing parameters
    (e.g `--hcp_bold_unwarpdir='y'`). 

    Do note that if you provide `se` information for the spin-echo image,
    you have to also provide it for all the images that are to use the
    spin-echo pair and vice-versa. If not, the matching algorithm will have
    incomplete information and might fail.


    Example definition
    ------------------

    hcpready: true
    01:                 :Survey
    02: T1w             :T1w 0.7mm N1             : se(1)
    03: T2w             :T2w 0.7mm N1             : se(1)
    04:                 :Survey
    05: SE-FM-AP        :C-BOLD 3mm 48 2.5s FS-P  : se(1)
    06: SE-FM-PA        :C-BOLD 3mm 48 2.5s FS-A  : se(1)
    07: bold1:WM        :BOLD 3mm 48 2.5s         : se(1) :fenc(AP)
    08: bold2:WM        :BOLD 3mm 48 2.5s         : se(1) :fenc(AP)
    09: bold3:WM        :BOLD 3mm 48 2.5s         : se(1) :fenc(AP)    
    10: bold4:WM        :BOLD 3mm 48 2.5s         : se(1) :fenc(AP)
    11: SE-FM-AP        :C-BOLD 3mm 48 2.5s FS-P  : se(2)
    12: SE-FM-PA        :C-BOLD 3mm 48 2.5s FS-A  : se(2)
    13: bold5:WM        :BOLD 3mm 48 2.5s         : se(2) :fenc(AP)
    14: bold6:WM        :BOLD 3mm 48 2.5s         : se(2) :fenc(AP)
    15: bold7:rest      :RSBOLD 3mm 48 2.5s       : se(2) :fenc(AP)
    16: bold8:rest      :RSBOLD 3mm 48 2.5s       : se(2) :fenc(PA)


    MULTIPLE SUBJECTS AND SCHEDULING
    ================================

    The command can be run for multiple subjects by specifying `subjects` and
    optionally `subjectsfolder` and `cores` parameters. In this case the command
    will be run for each of the specified subjects in the subjectsfolder
    (current directory by default). Optional `filter` and `subjid` parameters
    can be used to filter subjects or limit them to just specified id codes.
    (for more information see online documentation). `sfolder` will be filled in
    automatically as each subject's folder. Commands will run in parallel by
    utilizing the specified number of cores (1 by default).

    If `scheduler` parameter is set, the command will be run using the specified
    scheduler settings (see `mnap ?schedule` for more information). If set in
    combination with `subjects` parameter, subjects will be processed over
    multiple nodes, `core` parameter specifying how many subjects to run per
    node. Optional `scheduler_environment`, `scheduler_workdir`,
    `scheduler_sleep`, and `nprocess` parameters can be set.

    Set optional `logfolder` parameter to specify where the processing logs
    should be stored. Otherwise the processor will make best guess, where the
    logs should go.


    EXAMPLE USE
    ===========

    gmri setupHCP sfolder=OP316 sfile=subject.txt

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-07 Grega Repovš
             - Updated documentation
    2017-08-17 Grega Repovš
             - Added mapping of GE Field Map images
    2018-01-01 Grega Repovš
             - Changed parameter names
    2018-04-01 Grega Repovš
             - Added options for checking whether the subject is
               hcp ready and what to do with existing files
    '''

    print "Running setupHCP\n================"

    inf   = niutilities.g_core.readSubjectData(os.path.join(sfolder, sfile))[0][0]
    basef = os.path.join(sfolder, tfolder, inf['id'])
    rawf  = inf.get('raw_data', None)
    sid   = inf['id']
    bolds = collections.defaultdict(dict)
    nT1w  = 0
    nT2w  = 0

    # --- Check subject

    # -> is it HCP ready

    if inf.get('hcpready', 'no') != 'true':
        if check == 'yes':
            raise ge.CommandFailed("setupHCP", "Subject not ready", "Subject %s is not marked ready for HCP" % (sid), "Please check or run with check=no!")
        else:
            print "WARNING: Subject %s is not marked ready for HCP. Processing anyway." % (sid)

    # -> does raw data exist

    if rawf is None or not os.path.exists(rawf):
        raise ge.CommandFailed("setupHCP", "Data folder does not exist", "raw_data folder for %s does not exist!" % (sid), "Please check specified path [%s]" % (rawf))

    print "===> Setting up HCP folder structure for %s\n" % (sid)

    # -> does hcp folder already exist?

    if os.path.exists(basef):
        if existing == 'clear':
            print " ---> Base folder %s already exist! Clearing existing files and folders! " % (basef)
            shutil.rmtree(basef)
            os.makedirs(basef)
        elif existing == 'add':
            print " ---> Base folder %s already exist! Adding any new files specified! " % (basef)
        else:
            raise ge.CommandFailed("setupHCP", "Base folder exists", "Base folder %s already exist!" % (basef), "Please check or specify `exisiting` as `add` or `clear` for desired action!")
    else:
        print " ---> Creating base folder %s " % (basef)
        os.makedirs(basef)

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
            if 'se' in v:
                senum = v['se']
            else:
                senum = boldn
            tfold = "SpinEchoFieldMap" + senum + "_fncb"
        elif v['name'] == "SE-FM-PA":
            sfile = k + ".nii.gz"
            tfile = sid + "_fncb_BOLD_PA_SB_SE.nii.gz"
            if 'se' in v:
                senum = v['se']
            else:
                senum = boldn
            tfold = "SpinEchoFieldMap" + senum + "_fncb"
        elif v['name'] == "SE-FM-LR":
            sfile = k + ".nii.gz"
            tfile = sid + "_fncb_BOLD_LR_SB_SE.nii.gz"
            if 'se' in v:
                senum = v['se']
            else:
                senum = boldn
            tfold = "SpinEchoFieldMap" + senum + "_fncb"
        elif v['name'] == "SE-FM-RL":
            sfile = k + ".nii.gz"
            tfile = sid + "_fncb_BOLD_RL_SB_SE.nii.gz"
            if 'se' in v:
                senum = v['se']
            else:
                senum = boldn
            tfold = "SpinEchoFieldMap" + senum + "_fncb"
        elif v['name'] == "DWI":
            sfile = [k + e for e in ['.nii.gz', '.bval', '.bvec']]
            tbase = "_".join([sid, 'DWI', v['task']])
            tfile = [tbase + e for e in ['.nii.gz', '.bval', '.bvec']]
            tfold = "Diffusion"
        else:
            print "  ... skipping %s %s [unknown sequence label, please check]" % (v['ima'], v['name'])
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
                print "  ... %s subfolder already exists" % (tfold)

            if not os.path.exists(os.path.join(basef, tfold, tfile)):
                print " ---> linking %s to %s" % (sfile, tfile)
                os.link(os.path.join(rawf, sfile), os.path.join(basef, tfold, tfile))
            else:
                print "  ... %s already exists" % (tfile)
                # print " ---> %s already exists, replacing it with %s " % (tfile, sfile)
                # os.remove(os.path.join(basef,tfold,tfile))
                # os.link(os.path.join(rawf, sfile), os.path.join(basef,tfold,tfile))
    
    return


def setupHCPFolder(subjectsfolder=".", tfolder="hcp", sfile="subject_hcp.txt", check="interactive"):
    '''
    setupHCPFolder [subjectsfolder=.] [tfolder=hcp] [sfile=subject_hcp.txt] [check=interactive]

    USE
    ===

    The command is used to map MR images into a HCP prepocessing folder
    structure for all the subject folders it finds within the specified
    origin folder (subjectsfolder).

    Specifically, the command looks for source subject.txt files (sfile) in all
    the subfolders of the origin folder (subjectsfolder). For each found source
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

    --subjectsfolder  The origin folder that holds the subjects' folders (usually
                      "subjects"). [.]
    --tfolder         The target HCP folder in which to set up data for HCP
                      preprocessing (usually "hcp"). [hcp]
    --sfile           The source subject.txt file to use for mapping to a target
                      HCP folder. [subject_hcp.txt]
    --check           Whether to check if the subject is safe to run (yes), run
                      in any case (no) or ask the user (interactive) if in doubt.

    EXAMPLE USE
    ===========

    gmri setupHCPFolder subjectsfolder=subjects check=no

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-07 Grega Repovš
             - Updated documentation.
    2018-01-01 Grega Repovš
             - Changed input parameters
    '''

    # list all possible sbjfiles and check them
    
    print "Running setupHCPFolder\n======================"

    sbjf   = sfile
    sfiles = glob.glob(os.path.join(subjectsfolder, "*", sbjf))
    flist  = []

    print "---> checking %s files and %s folders in %s" % (sbjf, tfolder, subjectsfolder)

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
            setupHCP(sfolder=os.path.dirname(sfile), tfolder=tfolder, sfile=sbjf)

    print "\n\n===> done processing %s\n" % (subjectsfolder)


def getHCPReady(subjects, subjectsfolder=".", sfile="subject.txt", tfile="subject_hcp.txt", mapping=None, sfilter=None, overwrite="no"):
    '''
    getHCPReady subjects=<subjects specification> [subjectsfolder=.] [sfile=subject.txt] [tfile=subject_hcp.txt] [mapping=specs/hcp_mapping.txt] [sfilter=None] [overwrite=no]

    USE
    ===

    The command is used to prepare subject.txt files so that they hold the
    information necessary for correct mapping to a fodler structure supporting
    HCP preprocessing.

    For all the subjects specified, the command checks for the presence of
    specified source file (sfile). If the source file is found, each sequence
    name is checked against the source specified in the mapping file (mapping),
    and the specified label is aded. The results are then saved to the specified
    target file (tfile). The resulting subject infomation files will have
    "hcpready: true" key-value pair added.

    PARAMETERS
    ==========

    --subjects       Either an explicit list (space, comma or pipe separated) of
                     subjects to process or the path to a batch or list file with
                     subjects to process.
    --subjectsfolder The directory that holds subjects' folders. [.]
    --sfile          The "source" subject.txt file. [subject.txt]
    --tfile          The "target" subject.txt file. [subject_hcp.txt]
    --mapping        The path to the text file describing the mapping.
                     [specs/hcp_mapping.txt]
    --sfilter        An optional "key:value|key:value" string used as a filter
                     if a batch file is used. Only subjects for which all the
                     key:value pairs are true will be processed. All the
                     subjects will be processed if no filter is provided.
    --overwrite      Whether to overwrite target files that already exist (yes)
                     or not (no). [no]

    If an explicit list is provided, each element is treated as a glob pattern
    and the command will process all matching subject ids.

    Mapping specification
    ---------------------

    The mapping file specifies the mapping between original sequence names and
    the desired HCP labels. There are no limits to the number of mappings
    specified. Each mapping is to be specified in a single line in a form:

    <original_sequence_name>  => <user_specified_label>

    or

    <sequence number> => <user_specified_label>

    BOLD files should be given a compound label after the => separator:

    <original_sequence_name>  => bold:<user_specified_label>

    as this allows for flexible labeling of distinct BOLD runs based on their
    content. Here the 'bold' part denotes that it is a bold file and the
    <user_speficied_label> allows for flexibility in naming. getHCPReady will
    automatically number bold images in a sequential order, starting with 1.

    Any empty lines, lines starting with #, and lines without the "map to" =>
    characters in the mapping file will be ingored. In the target file, images
    with names that do not match any of the specified mappings will be given
    empty labels. When both sequence number and sequence name match, sequence
    number will have priority

    Example
    -------

    Example lines in a mapping file:

    C-BOLD 3mm 48 2.5s FS-P => SE-FM-AP
    C-BOLD 3mm 48 2.5s FS-A => SE-FM-PA

    T1w 0.7mm N1 => T1w
    T1w 0.7mm N2 => T1w
    T2w 0.7mm N1 => T2w
    T2w 0.7mm N2 => T2w

    RSBOLD 3mm 48 2.5s  => bold:rest
    BOLD 3mm 48 2.5s    => bold:WM

    5 => bold:sleep

    Example lines in a source subject.txt file:

    01: Scout
    02: T1w 0.7mm N1
    03: T2w 0.7mm N1
    04: RSBOLD 3mm 48 2.5s
    05: RSBOLD 3mm 48 2.5s

    Resulting lines in target subject_hcp.txt file:

    01:                  :Scout
    02: T1w              :T1w 0.7mm N1
    03: T2w              :T2w 0.7mm N1
    04: bold1:rest       :RSBOLD 3mm 48 2.5s
    05: bold2:sleep      :RSBOLD 3mm 48 2.5s

    Note, that the old sequence names are perserved.


    EXAMPLE USE
    ===========

    gmri getHCPReady subjects="OP*|AP*" subjectsfolder=subjects mapping=subjects/hcp_mapping.txt

    gmri getHCPReady subjects="processing/batch_new.txt" subjectsfolder=subjects mapping=subjects/hcp_mapping.txt

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-07 Grega Repovš
             - Updated documentation.
    2017-12-26 Grega Repovš
             - Set to ignore lines that start with # in mapping file.
    2017-12-30 Grega Repovš
             - Added the option to explicitly specify the subjects to process.
             - Adjusted and expanded help string.
             - Added the option to map sequence names.
    '''

    print "Running getHCPReady\n==================="

    if mapping is None:
        mapping = os.path.join(subjectsfolder, 'specs', 'hcp_mapping.txt')

    # -- get mapping ready

    if not os.path.exists(mapping):
        raise ge.CommandFailed("getHCPReady", "No HCP mapping file", "The expected HCP mapping file does not exist!", "Please check the specified path [%s]" % (mapping))

    print " ... Reading HCP mapping from %s" % (mapping)

    mapping = [line.strip() for line in open(mapping) if line[0] != "#"]
    mapping = [e.split('=>') for e in mapping]
    mapping = [[f.strip() for f in e] for e in mapping if len(e) == 2]
    mappingNumber = dict([[int(e[0]), e[1]] for e in mapping if e[0].isdigit()])
    mappingName   = dict([e for e in mapping if not e[0].isdigit()])

    if not mapping:
        raise ge.CommandFailed("getHCPReady", "No mapping defined", "No valid mappings were found in the mapping file!", "Please check the specified file [%s]" % (mapping))

    # -- get list of subject folders

    subjects, gopts = g_core.getSubjectList(subjects, sfilter=sfilter, verbose=False)

    sfolders = []
    for subject in subjects:
        newSet = glob.glob(os.path.join(subjectsfolder, subject['id']))
        if not newSet:
            print "WARNING: No folders found that match %s. Please check your data!" % (os.path.join(subjectsfolder, subject['id']))
        sfolders += newSet

    # -- loop through subject folders

    for sfolder in sfolders:

        ssfile = os.path.join(sfolder, sfile)
        stfile = os.path.join(sfolder, tfile)

        if not os.path.exists(ssfile):
            continue
        print " ... Processing folder %s" % (sfolder)

        if os.path.exists(stfile) and overwrite != "yes":
            print "     ... Target file already exists, skipping! [%s]" % (stfile)
            continue

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

                    onum = int(e[0].strip())
                    oimg = e[1].strip()
                    if onum in mappingNumber:
                        repl  = mappingNumber[onum]
                    elif oimg in mappingName:
                        repl  = mappingName[oimg]
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
    
    return

