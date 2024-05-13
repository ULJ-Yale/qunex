#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``ge_HCP.py``

Functions for exporting HCP style data out of the QuNex suite:

--export_hcp         Maps HCP style data to QuNex structure.

The commands are accessible from the terminal using the gmri utility.
"""

"""
Copyright (c) Grega Repovs and Jure Demsar.
All rights reserved.
"""

import glob
import os.path
import os
import time
import shutil
import general.core as gc
import general.exceptions as ge
import re

def export_hcp(sessionsfolder=".", sessions=None, filter=None, sessionids=None, mapaction="link", mapto=None, overwrite="no", mapexclude=None, hcp_suffix="", verbose="no"):

    """
    ``export_hcp [sessionsfolder="."] [sessions=None] [filter=None] [sessionids=None] [mapaction=<how to map>] [mapto=None|<location to map to>] [overwrite="no"] [mapexclude=None] [hcp_suffix=""] [verbose="no"]`` 

    Maps HCP style data out of QuNex Suite file strucutre.

    INPUTS
    ======

    --sessionsfolder  Specifies the base study sessions folder within the QuNex
                      folder structure to or from which the data are to be 
                      mapped. If not specified explicitly, the current working 
                      folder will be taken as the location of the
                      sessionsfolder. [.]
    
    --batchfile       A path to a batch.txt file.

    --sessions        Either a string with pipe `|` or comma separatedlist of
                      sessions (sessions ids) to be processed (use of grep
                      patterns is possible), e.g. `"OP128,OP139,ER*"` or `*list`
                      file with a list of session ids.

    --filter          And optional parameter used in combination with a 
                      batch.txt file used to filter sessions to include in the 
                      mapping. It is specified as a string in format:
    
                      ``"<key>:<value>|<key>:<value>"``

                      The keys and values refer to information provided by the
                      batch.txt file referenced in the `sessions` parameter. 
                      Only the sessions for which all the specified keys match
                      the specified values will be mapped. []

    --mapaction       How to map the data. ['link'] The following actions are 
                      supported:

                      - 'copy' (the data is copied from source to target)
                      - 'link' (if possible, hard links are created for the 
                        files, if not, the data is copied)
                      - 'move' (the data is moved from source to target 
                        location)

    --mapto           The external target of the mapping when starting with the 
                      QuNex. This flag is optional and only has to be specified 
                      when mapping out of the QuNex folder structure. []

    --overwrite       Whether existing files at the target location should be
                      overwritten.['no'] Possible options are:

                      - yes (any existing files should be replaced)
                      - no (no existing files should be replaced and the
                        mapping should be aborted if any are found)
                      - skip (skip files that already exist, process others)

    --mapexclude      A comma separated list of regular expression patterns that
                      specify, which files should be excluded from mapping. The
                      regular expression patterns are matched against the full
                      path of the source files. []

    --hcp_suffix      An optional suffix to append to session id when mapping  
                      data from a hcp session folder. The path from which the 
                      data will be mapped from each session will be:
                      ``<sessionsfolder>/<session id>/hcp/<session id><hcp_suffix>``.
                      []

    --verbose         Report details while running function ['no']

    USE
    ===

    The function maps HCP style data out of QuNex data structure. How to do the 
    mapping (move, copy, link) is specified by the `mapaction` parameter. The
    `overwrite` parameter specifies whether to replace any existing data at the
    target location if it already exist. The target location has to be provided
    by the `mapto` parameter.

    The function first prepares the mapping. Next it checks that the mapping can
    be conducted as specified by the parameters given. If the check identifies 
    any potential issues, no mapping is conducted to avoid an incomplete 
    mapping. Do note that the check only investigates the presence of source 
    and target files, it does not check, whether the user has permission on the 
    file system to execute the actions.

    This mapping supports the data preprocessed using the HCP Pipelines
    following the Life Span (LS) convention. The processed derivatives from the 
    HCP pipelines are mapped into the specified target location on the file 
    system to comply with the HCPLS output expectations. The mapping expects 
    that HCPLS folder structure was used for the processing. The function will 
    map all the content of the session's hcp directory to a corresponding 
    session directory in the indicated target location. If any part of the 
    unprocessed data or the results are not to be mapped, they can be specified 
    using the `mapexclude` parameter.

    EXAMPLE CALLS
    =============

    We will assume the following:
    
    - data to be mapped is located in the folder 
      ``/data/studies/myStudy/sessions``
    - a batch file exists in the location 
      ``/data/studies/myStudy/processing/batch.txt``
    - we would like to map the data to location 
      ``/data/outbox/hcp_formatted/myStudy``
    
    given the above assumptions the following example commands can be run::
    
        qunex export_hcp \\
            --sessionsfolder=/data/studies/myStudy/sessions \\
            --batchfile=/data/studies/myStudy/processing/batch.txt \\
            --mapto=/data/outbox/hcp_formatted/myStudy \\
            --mapexclude=unprocessed \\
            --mapaction=link \\
            --overwrite=skip

    Using the above commands the data found in the 
    ``/data/studies/myStudy/sessions/<session id>/hcp/<session id>`` folders, 
    excluding the `unprocessed` folder would be mapped to the 
    ``/data/outbox/hcp_formatted/myStudy/<session id>`` folder for all the 
    sessions listed in the batch.txt file. Specifically, folders would be 
    recreated as needed and hard-links would be created for all the files to be 
    mapped. If any target files already exist, they would be skipped, but 
    the processing of other files would take place anyway.
    
    ::

        qunex export_hcp \\
            --sessionsfolder=/data/studies/myStudy/sessions \\
            --batchfile=/data/studies/myStudy/processing/batch.txt \\
            --mapto=/data/outbox/hcp_formatted/myStudy \\
            --filter="group:controls|institution:Yale" \\
            --mapaction="copy" \\
            --overwrite=no

    Using the above commands, only data from the sessions that are marked in the
    batch.txt file to be from the control group and acquired at Yale would be 
    mapped. In this case, the files would be copied and if any files would 
    already exist in the target location, the mapping would be aborted 
    altogether.
    
    ::

        qunex export_hcp \\
            --sessionsfolder=/data/studies/myStudy/sessions \\
            --batchfile=/data/studies/myStudy/processing/batch.txt \\
            --mapto=/data/outbox/hcp_formatted/myStudy \\
            --sessionids="AP*,HQ*" \\
            --mapaction="move" \\
            --overwrite=yes
    

    Using the above commands, only the sessions that start with either "AP" or 
    "HQ" would be mapped, the files would be moved and any existing files at the 
    target location would be overwritten.
    
    ::

        qunex export_hcp \\
            --sessionsfolder=/data/studies/myStudy/sessions \\
            --batchfile=/data/studies/myStudy/processing/batch.txt \\
            --mapto=/data/outbox/hcp_formatted/myStudy \\
            --mapaction="link" \\
            --mapexclude="unprocessed,MotionMatrices,MotionCorrection" \\
            --overwrite=skip
    
    Using the above commands, all the sessions specified in the batch.txt would 
    be processed, files would be linked, files that already exist would be 
    skipped, and any files for which the path include 'unprocessed', '
    MotionMatrices' or 'MotionCorrection' would be excluded from the mapping.
    """

    # load gu
    import general.utilities as gu

    verbose   = verbose.lower() == 'yes'

    # -- export prep
    sessionsfolder, mapto, mapexclude = gu.exportPrep("export_hcp", sessionsfolder, mapto, mapaction, mapexclude)

    # -- prepare sessions
    sessions, _ = gc.get_sessions_list(sessions, filter=filter, sessionids=sessionids, sessionsfolder=sessionsfolder, verbose=False)
    if not sessions:
        raise ge.CommandFailed("export_hcp", "No session found" , "No sessions found to map based on the provided criteria!", "Please check your data!")

    # -- open logfile
    logfilename, logfile = gc.getLogFile(folders={'sessionsfolder': sessionsfolder}, tags=['export_hcp'])

    # -- start
    gc.printAndLog(gc.underscore("Running export_hcp"), file=logfile)
    
    # -- prepare mapping
    gc.printAndLog("---> Preparing mapping", file=logfile)

    # -- map
    toMap = []

    for session in sessions:
        hcpfolder = os.path.join(sessionsfolder, session['id'], 'hcp', session['id'] + hcp_suffix)
        hcpfolders = glob.glob(os.path.join(hcpfolder, '*')) 
        targetfolder = os.path.join(mapto, session['id'])

        for datafolder in hcpfolders:
            for dirpath, _, filenames in os.walk(datafolder):
                for filename in filenames:
                        toMap.append((os.path.join(datafolder, dirpath, filename), os.path.join(targetfolder, os.path.relpath(dirpath, hcpfolder), filename)))

    if not toMap:
        gc.printAndLog("ERROR: Found nothing to map!", file=logfile, silent=True)
        endlog = gc.closeLogFile(logfile, logfilename, status="error")
        raise ge.CommandFailed("export_hcp", "Nothing to map" , "No files were found to map!", "Please check your data!")

    # -- check mapping
    missing   = []
    existing  = []
    failed    = []
    process   = []
    toexclude = []

    for sfile, tfile in toMap:
        if not os.path.exists(sfile):
            missing.append((sfile, tfile))
        elif os.path.isfile(tfile):
            existing.append((sfile, tfile))
        else:
            if mapexclude:
                if any([e.search(sfile) is not None for e in mapexclude]):
                    toexclude.append((sfile, tfile))
                    continue
            process.append((sfile, tfile))

    if missing:
        gc.printAndLog("---> ERROR: A number of source files are missing", file=logfile, silent=not verbose)
        for sfile, tfile in missing:
            gc.printAndLog("           ---> " + sfile, file=logfile)
        gc.printAndLog("\nMapping Aborted!", file=logfile)
        endlog = gc.closeLogFile(logfile, logfilename, status="error")
        raise ge.CommandFailed("export_hcp", "Source files missing" , "Mapping could not be run as some source files were missing!", "Please check your data and log [%s!" % (endlog))
    
    if existing:
        s = 'Some files already exist'
        if overwrite.lower() == 'yes':
            s = "---> WARNING: " + s + " and will be overwritten"
            pre = "             "
            process += existing
        if overwrite.lower() == 'skip':
            s = "---> WARNING: " + s + " and will be skipped"
            pre = "             "
        else:
            s = "---> ERROR: " + s 
            pre = "           "
        gc.printAndLog(s, file=logfile)

        for sfile, tfile in existing:
            gc.printAndLog(pre + "---> " + sfile, file=logfile, silent=not verbose)

        if overwrite.lower() == 'no':
            gc.printAndLog("---> Mapping Aborted!", file=logfile)
            endlog = gc.closeLogFile(logfile, logfilename, status="error")
            raise ge.CommandFailed("export_hcp", "Target files exist" , "Mapping could not be run as some target file already exist!", "Please check your data and log [%s]!" % (endlog))

    if toexclude:
        gc.printAndLog("---> WARNING: Some files will be excluded from mapping", file=logfile)

        for sfile, tfile in toexclude:
            gc.printAndLog("             ---> " + sfile, file=logfile, silent=not verbose)

    if not process:
        gc.printAndLog("---> Nothing left to map!", file=logfile, silent=True)
        endlog = gc.closeLogFile(logfile, logfilename, status="done")
        raise ge.CommandNull("export_hcp", "Nothing left to map" , "After skipping and exclusion, no files were left to map!", "Please check your data!")

    # -- execute mapping
    # -> clean destination
    if overwrite.lower() == 'yes':
        for tfile in existing:
            os.remove(tfile)

    # -> map
    mapactions = {'copy': shutil.copy2, 'move': shutil.move, 'link': gc.link_or_copy}
    descriptions = {'copy': 'copying', 'move': 'moving', 'link': 'linking'}
    
    do   = mapactions[mapaction]
    desc = descriptions[mapaction]

    gc.printAndLog("---> Mapping files", file=logfile)

    failed = []

    # variable for storing folders that need their timestamps amended
    timemapping = []

    for sfile, tfile in process:

        # split to file and folder
        tfolder, _ = os.path.split(tfile)
        sfolder, _ = os.path.split(sfile)

        # create each fodler in the structure independenlty
        # get all folders in the structure
        tparentfolders = tfolder.split("/")
        sparentfolders = sfolder.split("/")

        # go over all folders
        tpath = ""
        for f in tparentfolders:
            tpath = tpath + f + "/"

            # does not exist yet
            if not os.path.exists(tpath):
                try:
                    # makedir
                    os.makedirs(tpath)

                    # is folder also in source file's folder structure
                    if f in sparentfolders:
                        # create paths
                        spath = "/".join(sparentfolders[0:sparentfolders.index(f)+1])
                        # get source timestamp
                        stime = os.path.getctime(spath)

                        # store folder and timestamp
                        timemapping.append([tpath, stime])

                except:
                    failed.append((sfile, tfile))
                    continue
                gc.printAndLog("    ---> creating folder: %s" % (tfolder), file=logfile, silent=not verbose)

        try:
            do(sfile, tfile)
        except:
            raise

        gc.printAndLog("    ---> %s: %s ---> %s" % (desc, sfile, tfile), file=logfile, silent=not verbose)

    # -- once files are copied set timestamps
    for mapping in timemapping:
        try:
            # set target subfolder timestamp
            os.utime(mapping[0], (mapping[1], mapping[1]))
        except:
            gc.printAndLog("    ---> Setting time stamp of folder %s to %s failed" % (mapping[0], time.ctime(mapping[1])), file=logfile)
            continue

    # -- check
    if failed:
        gc.printAndLog("\n" + gc.underscore("ERROR: The following files could not be mapped"), file=logfile)
        for sfile, tfile in failed:
            gc.printAndLog("---> %s ---> %s" % (sfile, tfile), file=logfile)

        endlog = gc.closeLogFile(logfile, logfilename, status="error")
        raise ge.CommandFailed("export_hcp", "Some files not mapped" , "Some files could not be mapped!", "Please see log and check your data [%s]!" % (endlog))

    gc.printAndLog("---> Mapping completed", file=logfile)
    endlog = gc.closeLogFile(logfile, logfilename, status="done")
