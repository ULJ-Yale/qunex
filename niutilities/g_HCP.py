#!/usr/bin/env python2.7
# encoding: utf-8
"""
g_HCP.py

Functions for preparing information and mapping images to a HCP preprocessing
compliant folder structure:

* setupHCPFolder  ... runs setupHCP for all session folders
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

def setupHCPFolder(subjectsfolder=".", tfolder="hcp", sfile="subject_hcp.txt", check="interactive"):
    '''
    setupHCPFolder [subjectsfolder=.] [tfolder=hcp] [sfile=subject_hcp.txt] [check=interactive]

    USE
    ===

    The command is used to map MR images into a HCP prepocessing folder
    structure for all the session folders it finds within the specified
    origin folder (subjectsfolder).

    Specifically, the command looks for source subject.txt files (sfile) in all
    the subfolders of the origin folder (subjectsfolder). For each found source
    subject.txt file it checks whether the file is hcp ready and if the target
    folder (tfolder) exists. If the file is ready and if the target folder
    does not yet exists, it runs setupHCP command mapping the files to the
    target folder as specified in the source subject.txt file.

    If the source subject.txt file does not seem to be ready or if the target
    folder exists, the action depends on check parameter. If check is "yes",
    the session is not processed, if check is set to "no" the session is
    processed. If check is set to "interactive" the user is asked whether the
    session should be processed or not.

    PARAMETERS
    ==========

    --subjectsfolder  The origin folder that holds the sessions' folders (usually
                      "subjects"). [.]
    --tfolder         The target HCP folder in which to set up data for HCP
                      preprocessing (usually "hcp"). [hcp]
    --sfile           The source subject.txt file to use for mapping to a target
                      HCP folder. [subject_hcp.txt]
    --check           Whether to check if the session is safe to run (yes), run
                      in any case (no) or ask the user (interactive) if in doubt.

    EXAMPLE USE
    ===========
    
    ```
    qunex setupHCPFolder subjectsfolder=subjects check=no
    ```

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-07 Grega Repovš
             - Updated documentation.
    2018-01-01 Grega Repovš
             - Changed input parameters
    2019-04-25 Grega Repovš
             - Changed subjects to sessions
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
            print status, " => processing session"
        elif check == "yes":
            print status, " => skipping this session"
        elif check == "interactive":
            print status
            s = raw_input("     ---> do you want to process this session [y/n]: ")
            if s != 'y':
                process = False

        flist.append((sfile, ready, fex, ok, process))

    for sfile, ready, fex, ok, process in flist:
        if process:
            setupHCP(sfolder=os.path.dirname(sfile), tfolder=tfolder, sfile=sbjf)

    print "\n\n===> done processing %s\n" % (subjectsfolder)


def getHCPReady(sessions=None, subjectsfolder=".", sfile="subject.txt", tfile="subject_hcp.txt", mapping=None, sfilter=None, overwrite="no"):
    '''
    getHCPReady sessions=<sessions specification> [subjectsfolder=.] [sfile=subject.txt] [tfile=subject_hcp.txt] [mapping=specs/hcp_mapping.txt] [sfilter=None] [overwrite=no]

    USE
    ===

    The command is used to prepare subject.txt files so that they hold the
    information necessary for correct mapping to a fodler structure supporting
    HCP preprocessing.

    For all the sessions specified, the command checks for the presence of
    specified source file (sfile). If the source file is found, each sequence
    name is checked against the source specified in the mapping file (mapping),
    and the specified label is aded. The results are then saved to the specified
    target file (tfile). The resulting session infomation files will have
    "hcpready: true" key-value pair added.

    PARAMETERS
    ==========

    --sessions       Either an explicit list (space, comma or pipe separated) of
                     sessions to process or the path to a batch or list file with
                     sessions to process. If left unspecified, "*" will be used 
                     and all folders within subjectfolder will be processed.
    --subjectsfolder The directory that holds sessions' folders. [.]
    --sfile          The "source" subject.txt file. [subject.txt]
    --tfile          The "target" subject.txt file. [subject_hcp.txt]
    --mapping        The path to the text file describing the mapping.
                     [specs/hcp_mapping.txt]
    --sfilter        An optional "key:value|key:value" string used as a filter
                     if a batch file is used. Only sessions for which all the
                     key:value pairs are true will be processed. All the
                     sessions will be processed if no filter is provided.
    --overwrite      Whether to overwrite target files that already exist (yes)
                     or not (no). [no]

    If an explicit list is provided, each element is treated as a glob pattern
    and the command will process all matching session ids.

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
    
    ```
    qunex getHCPReady sessions="OP*|AP*" subjectsfolder=subjects mapping=subjects/hcp_mapping.txt
    ```
    
    ```
    qunex getHCPReady sessions="processing/batch_new.txt" subjectsfolder=subjects mapping=subjects/hcp_mapping.txt
    ```

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
    2019-04-07 Grega Repovš
             - Added more detailed report with explicit failure in case of missing source files.
    2019-04-25 Grega Repovš
             - Changed subjects to sessions
    '''

    print "Running getHCPReady\n==================="

    if sessions is None:
        sessions = "*"

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

    # -- get list of session folders

    sessions, gopts = g_core.getSubjectList(sessions, sfilter=sfilter, verbose=False)

    sfolders = []
    for session in sessions:
        newSet = glob.glob(os.path.join(subjectsfolder, session['id']))
        if not newSet:
            print "WARNING: No folders found that match %s. Please check your data!" % (os.path.join(subjectsfolder, session['id']))
        sfolders += newSet

    # -- check if we have any

    if not sfolders:
        raise ge.CommandFailed("getHCPReady", "No sessions found to process", "No sessions were found to process!", "Please check the data and sessions parameter!")

    # -- loop through sessions folders

    report = {'missing source': [], 'pre-existing target': [], 'pre-processed source': [], 'processed': []}
    
    for sfolder in sfolders:

        ssfile = os.path.join(sfolder, sfile)
        stfile = os.path.join(sfolder, tfile)

        if not os.path.exists(ssfile):
            report['missing source'].append(sfolder)
            continue
        print " ... Processing folder %s" % (sfolder)

        if os.path.exists(stfile) and overwrite != "yes":
            print "     ... Target file already exists, skipping! [%s]" % (stfile)
            report['pre-existing target'].append(sfolder)
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
            if sfile != tfile:
                shutil.copyfile(sfile, tfile)
            report['pre-processed source'].append(sfolder)
        else:
            print "     ... writing %s" % (tfile)
            fout = open(stfile, 'w')
            for line in nlines:
                print >> fout, line
            report['processed'].append(sfolder)
    
    print "\n===> Final report"

    for status in ['pre-existing target', 'pre-processed source', 'processed', 'missing source']:
        if report[status]:
            print "---> sessions with %s file:" % (status)
            for session in report[status]:
                print "     -> %s " % (os.path.basename(session))

    if report['missing source']:
        raise ge.CommandFailed("getHCPReady", "Unprocessed sessions", "Some sessions were missing source files [%s]!" % (sfile), "Please check the data and parameters!")

    return

