#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``export_hcp.py``

Functions for exporting HCP style data out of the QuNex suite:

--export_hcp         Maps HCP style data to QuNex structure.

The commands are accessible from the terminal using the gmri utility.
"""

# Copyright (c) Grega Repovs and Jure Demsar.
# All rights reserved.

import glob
import os.path
import os
import time
import shutil
import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl


def export_hcp(sessionsfolder=".", batchfile=None, sessions=None, filter=None, mapaction="link", mapto=None, overwrite="no", mapexclude=None, hcp_suffix="", verbose="no"):

    """
    ``export_hcp [sessionsfolder="."] [batchfile=None] [sessions=None] [filter=None] [mapaction=<how to map>] [mapto=None|<location to map to>] [overwrite="no"] [mapexclude=None] [hcp_suffix=""] [verbose="no"]``

    Export HCP style data out of the QuNex Suite file structure.

    ..  qx_command:
        type: utility

    Parameters:
        --sessionsfolder (str, default '.'):
            The base study sessions folder within the QuNex
            folder structure to or from which the data are to be
            mapped. If not specified explicitly, the current working
            folder will be taken as the location of the
            sessionsfolder.

        --batchfile (str, default ''):
            A path to a batch.txt file.

        --sessions (str, default ''):
            A list of sessions to map (comma/pipe-separated, patterns allowed).
            When a batch file is given, it selects within it.

        --filter (str, default ''):
            An optional string of `<key>:<value>` pairs joined by `|` (OR) or
            by `&` (AND) — one operator at a time, used to select sessions
            within the given batch file. Values may be glob patterns.

        --mapaction (str, default 'link'):
            How to map the data: copy, link, or move.

        --mapto (str, default ''):
            Target location to map to when exporting.

        --overwrite (str, default 'no'):
            Whether to overwrite existing files at the target, skip them, or abort.

        --mapexclude (str, default ''):
            Comma separated list of regex patterns that match files to exclude from mapping.

        --hcp_suffix (str, default ''):
            Optional suffix appended to session id under the hcp folder.

        --verbose (str, default 'no'):
            Report details while running.



    Notes:
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

    Examples:

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
                --sessions="AP*,HQ*" \\
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
    import qx_utilities.general.utilities as gu

    verbose   = verbose.lower() == 'yes'

    # -- export prep
    sessionsfolder, mapto, mapexclude = gu.export_prep("export_hcp", sessionsfolder, mapto, mapaction, mapexclude)

    # -- prepare sessions
    sessions, _ = gc.resolve_sessions(batchfile=batchfile, sessions=sessions, filter=filter, sessionsfolder=sessionsfolder, command="export_hcp", verbose=False)
    if not sessions:
        raise ge.CommandFailed("export_hcp", "No session found" , "No sessions found to map based on the provided criteria!", "Please check your data!")

    # -- open logfile
    logfolder = gc.deduce_folders({'sessionsfolder': sessionsfolder})['logfolder']
    comlog = gl.ComContext(gl.comlog_folder(logfolder), 'export_hcp').open()
    logfile = comlog.file

    # -- start
    gc.print_and_log(gc.underscore("Running export_hcp"), file=logfile)

    # -- prepare mapping
    gc.print_and_log("---> Preparing mapping", file=logfile)

    # -- map
    to_map = []

    for session in sessions:
        hcpfolder = os.path.join(sessionsfolder, session['id'], 'hcp', session['id'] + hcp_suffix)
        hcpfolders = glob.glob(os.path.join(hcpfolder, '*'))
        targetfolder = os.path.join(mapto, session['id'])

        for datafolder in hcpfolders:
            for dirpath, _, filenames in os.walk(datafolder):
                for filename in filenames:
                        to_map.append((os.path.join(datafolder, dirpath, filename), os.path.join(targetfolder, os.path.relpath(dirpath, hcpfolder), filename)))

    if not to_map:
        gc.print_and_log("ERROR: Found nothing to map!", file=logfile, silent=True)
        endlog = comlog.close(status="error")
        raise ge.CommandFailed("export_hcp", "Nothing to map" , "No files were found to map!", "Please check your data!")

    # -- check mapping
    missing   = []
    existing  = []
    failed    = []
    process   = []
    toexclude = []

    for sfile, tfile in to_map:
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
        gc.print_and_log("---> ERROR: A number of source files are missing", file=logfile, silent=not verbose)
        for sfile, tfile in missing:
            gc.print_and_log("           ---> " + sfile, file=logfile)
        gc.print_and_log("\nMapping Aborted!", file=logfile)
        endlog = comlog.close(status="error")
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
        gc.print_and_log(s, file=logfile)

        for sfile, tfile in existing:
            gc.print_and_log(pre + "---> " + sfile, file=logfile, silent=not verbose)

        if overwrite.lower() == 'no':
            gc.print_and_log("---> Mapping Aborted!", file=logfile)
            endlog = comlog.close(status="error")
            raise ge.CommandFailed("export_hcp", "Target files exist" , "Mapping could not be run as some target file already exist!", "Please check your data and log [%s]!" % (endlog))

    if toexclude:
        gc.print_and_log("---> WARNING: Some files will be excluded from mapping", file=logfile)

        for sfile, tfile in toexclude:
            gc.print_and_log("             ---> " + sfile, file=logfile, silent=not verbose)

    if not process:
        gc.print_and_log("---> Nothing left to map!", file=logfile, silent=True)
        endlog = comlog.close(status="done")
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

    gc.print_and_log("---> Mapping files", file=logfile)

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

                except Exception:
                    failed.append((sfile, tfile))
                    continue
                gc.print_and_log("    ---> creating folder: %s" % (tfolder), file=logfile, silent=not verbose)

        try:
            do(sfile, tfile)
        except Exception:
            raise

        gc.print_and_log("    ---> %s: %s ---> %s" % (desc, sfile, tfile), file=logfile, silent=not verbose)

    # -- once files are copied set timestamps
    for mapping in timemapping:
        try:
            # set target subfolder timestamp
            os.utime(mapping[0], (mapping[1], mapping[1]))
        except Exception:
            gc.print_and_log("    ---> Setting time stamp of folder %s to %s failed" % (mapping[0], time.ctime(mapping[1])), file=logfile)
            continue

    # -- check
    if failed:
        gc.print_and_log("\n" + gc.underscore("ERROR: The following files could not be mapped"), file=logfile)
        for sfile, tfile in failed:
            gc.print_and_log("---> %s ---> %s" % (sfile, tfile), file=logfile)

        endlog = comlog.close(status="error")
        raise ge.CommandFailed("export_hcp", "Some files not mapped" , "Some files could not be mapped!", "Please see log and check your data [%s]!" % (endlog))

    gc.print_and_log("---> Mapping completed", file=logfile)
    endlog = comlog.close(status="done")
