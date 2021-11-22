#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``bids.py``

Functions for importing and exporting BIDS data to QuNex file structure.

--import_bids          Maps BIDS data to QuNex structure.
--BIDSExport          Exports QuNex data to BIDS structured folder.

The commands are accessible from the terminal using qunex command.
"""

"""
Copyright (c) Grega Repovs. All rights reserved.
"""

import os
import os.path
import re
import shutil
import zipfile
import tarfile
import glob
import datetime
import gzip
import ast

import general.exceptions as ge
import general.core as gc
import general.filelock as fl


def mapToQUNEXBids(file, sessionsfolder, bidsfolder, sessionsList, overwrite, prefix, select=False):
    '''
    Identifies and returns the intended location of the file based on its name.
    '''
    try:
        if sessionsfolder[-1] == '/':
            sessionsfolder = sessionsfolder[:-1]
    except:
        pass

    folder     = bidsfolder
    subject    = ""
    session    = ""
    optional   = ""
    modality   = ""
    isoptional = False

    # --- load BIDS structure
    # template folder
    niuTemplateFolder = os.environ["NIUTemplateFolder"]
    bidsStructure = os.path.join(niuTemplateFolder, "import_bids.txt")

    if not os.path.exists(bidsStructure):
        raise ge.CommandFailed("mapToQUNEXBids", "No BIDS structure file present!", "There is no BIDS structure file %s" % (bidsStructure), "Please check your QuNex installation")

    bids_file = open(bidsStructure)
    content = bids_file.read()
    bids = ast.literal_eval(content)

    # -> extract file meta information

    for part in re.split("_|/|\.", file):
        if part.startswith('sub-'):
            subject = part.split('-')[1]            
        elif part.startswith('ses-'):
            session = part.split('-')[1]
        elif part in bids['optional']:
            optional = part
            isoptional = True
        elif part in bids['modalities']:
            modality = part
        else:
            for targetModality in bids['modalities']:
                if part in bids[targetModality]['label']:
                    modality = targetModality 

    # -> check whether we have a session specific or study general file

    session = "_".join([e for e in [subject, session] if e])
    if session:
        folder = os.path.join(sessionsfolder, session, 'bids')
        if select:
            if session not in select:
                sessionsList['skip'].append(session)
    else:
        session = 'bids'

    # --> session marked to skip
    if session in sessionsList['skip']:
        return False, False

    # --> processing a new session
    elif session not in sessionsList['list']:

        sessionsList['list'].append(session)

        # --> processing study level data
        if session == 'bids':
            io = fl.makedirs(bidsfolder)
            if io and io != 'File exists':
                raise ge.CommandFailed("import_bids", "I/O error: %s" % (io), "Could not create BIDS info folder [%s]!" % (bidsfolder), "Please check paths and permissions!")

            io = fl.open_status(os.path.join(bidsfolder, 'bids_info_status'), "Processing started on %s.\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")))

            # --> status created
            if io is None:
                print(prefix + "--> processing BIDS info folder")
                sessionsList['bids'] = 'open'

            # --> status exists
            elif io == 'File exists' and not overwrite == 'yes':
                print(prefix + "--> skipping processing of BIDS info folder")
                sessionsList['skip'].append('bids')
                sessionsList['bids'] = 'locked'
                return False, False

            # --> an error
            elif io != 'File exists':
                raise ge.CommandFailed("import_bids", "I/O error: %s" % (io), "Could not create BIDS info status file [%s]!" % (os.path.join(bidsfolder, 'bids_info_status')), "Please check paths and permissions!")

        # --> session folder exists
        elif os.path.exists(folder):
            if overwrite == 'yes':
                print(prefix + "--> bids for session %s already exists: cleaning session" % (session))
                shutil.rmtree(folder)
                sessionsList['clean'].append(session)
            elif not os.path.exists(os.path.join(folder, 'bids2nii.log')):
                print(prefix + "--> incomplete bids for session %s already exists: cleaning session" % (session))
                shutil.rmtree(folder)
                sessionsList['clean'].append(session)
            else:
                sessionsList['skip'].append(session)
                print(prefix + "--> bids for session %s already exists: skipping session" % (session))
                print(prefix + "    files previously mapped:")
                with open(os.path.join(folder, 'bids2nii.log')) as bidsLog:
                    for logline in bidsLog:
                        if 'BIDS to nii mapping report' in logline:
                            continue
                        elif '=>' in logline:                            
                            mappedFile = logline.split('=>')[0].strip()
                            print(prefix + "    ... %s" % (os.path.basename(mappedFile)))
                return False, False
        
        # --> session folder does not exist and is not 'bids'
        else:
            print(prefix + "--> creating bids session %s" % (session))
            sessionsList['map'].append(session)
    
    # --> compile target filename
    if isoptional:
        oparts = file.split(os.sep)
        fparts = [folder] + oparts[oparts.index(optional):]
        tfile  = os.path.join(*fparts)
    else:
        tfile = os.path.join(folder, optional, modality, os.path.basename(file))

    # --> check folder
    io = fl.makedirs(os.path.dirname(tfile))

    if io and io != 'File exists':
        raise ge.CommandFailed("import_bids", "I/O error: %s" % (io), "Could not create folder for file [%s]!" % (tfile), "Please check paths and permissions!")

    # --> return file and locking info
    return tfile, session == 'bids'



def import_bids(sessionsfolder=None, inbox=None, sessions=None, action='link', overwrite='no', archive='move', bidsname=None, fileinfo=None):
    """
    ``import_bids [sessionsfolder=.] [inbox=<sessionsfolder>/inbox/BIDS] [sessions="*"] [action=link] [overwrite=no] [archive=move] [bidsname=<inbox folder name>] [fileinfo=short]``
    
    Maps a BIDS dataset to the QuNex Suite file structure.

    INPUTS
    ======

    --sessionsfolder      The sessions folder where all the sessions are to be 
                          mapped to. It should be a folder within the 
                          <study folder>. [.]

    --inbox               The location of the BIDS dataset. It can be any of the
                          following: the BIDS dataset top folder, a folder that 
                          contains the BIDS dataset, a path to the compressed 
                          `.zip` or `.tar.gz` package that can contain a single 
                          session or a multi-session dataset, or a folder that 
                          contains a compressed package. For instance the user 
                          can specify "<path>/<bids_file>.zip" or "<path>" to
                          a folder that contains multiple packages. The default 
                          location where the command will look for a BIDS 
                          dataset is [<sessionsfolder>/inbox/BIDS].

    --sessions            An optional parameter that specifies a comma or pipe
                          separated list of sessions from the inbox folder to be 
                          processed. Glob patterns can be used. If provided, 
                          only packets or folders within the inbox that match 
                          the list of sessions will be processed. If `inbox` is 
                          a file `sessions` has to be a list of session 
                          specifications, only those sessions that match the 
                          list will be processed. If `inbox` is a valid bids 
                          datastructure folder or archive, then the sessions can
                          be specified either in `<subject id>[_<session name>]`
                          format or as explicit 
                          `sub-<subject id>[/ses-<session name>]` names.

    --action              How to map the files to QuNex structure. ['link']
                          These are the options:
                        
                          - link (the files will be mapped by creating hard 
                            links if possible, otherwise they will be copied)
                          - copy (the files will be copied)       
                          - move (the files will be moved)

    --overwrite           The parameter specifies what should be done with 
                          data that already exists in the locations to which 
                          bids data would be mapped to. ['no'] Options are:

                          - no (do not overwrite the data and skip processing of
                            the session)
                          - yes (remove existing files in `nii` folder and redo 
                            the mapping)

    --archive             What to do with the files after they were mapped. 
                          ['move'] Options are:

                          - leave (leave the specified archive where it is)
                          - move (move the specified archive to 
                            `<sessionsfolder>/archive/BIDS)`
                          - copy (copy the specified archive to 
                            `<sessionsfolder>/archive/BIDS)`
                          - delete (delete the archive after processing if no 
                            errors were identified)

                         Please note that there can be an interaction with the 
                         `action` parameter. If files are moved during action, 
                         they will be missing if `archive` is set to 'move' or 
                         'copy'.

    --bidsname           The optional name of the BIDS dataset. If not provided
                         it will be set to the name of the inbox folder or the 
                         name of the compressed package.

    --fileinfo           What file information to include in the session.txt 
                         file. Options are:
                        
                         - short (only provide the short description based on 
                           the identified BIDS tags)
                         - full (list the full file name excluding the 
                           participant id, session name and extension)

    OUTPUTS
    =======

    After running the `import_bids` command the BIDS dataset will be mapped 
    to the QuNex folder structure and image files will be prepared for further
    processing along with required metadata.

    Files pertaining to the study and not specific subject / session are
    stored in::

        <study folder>/info/bids/<bids bame>
    
    The original BIDS session-level data is stored in::

        <sessionsfolder>/<session>/bids

    Image files mapped to new names for QuNex are stored in::

        <sessionsfolder>/<session>/nii

    The full description of the mapped files is in::

        <sessionsfolder>/<session>/session.txt

    The output log of BIDS mapping is in::

        <sessionsfolder>/<session>/bids/bids2nii.log

    The study-level BIDS files are in::

        <study_folder>/<info>/bids/<bidsname>

    USE
    ===
    
    The import_bids command consists of two steps:
    
    Step 1 - Mapping BIDS dataset to QuNex Suite folder structure
    --------------------------------------------------------------
    
    The `inbox` parameter specifies the location of the BIDS dataset. This path 
    is inspected for a BIDS compliant dataset. The path can point to a folder 
    with extracted BIDS dataset, a `.zip` or `.tar.gz` archive or a folder 
    containing one or more `.zip` or `.tar.gz` archives. In the initial step, 
    each file found will be assigned either to a specific session or the 
    overall study. 

    The BIDS files assigned to the study will be saved in the following 
    location::

        <study_folder>/info/bids/<bids_dataset_name>

    <bids_dataset_name> can be provided as a `bidsname` parameter to the command
    call. If `bidsname` is not provided, the name will be set to the name of the 
    parent folder or the name of the compressed archive.

    The files identified as belonging to a specific session will be mapped to 
    folder::
    
        <sessions_folder>/<subject>_<session>/bids

    The `<subject>_<session>` string will be used as the identifier for the 
    session in all the following steps. If no session is specified in BIDS,
    `session` will be the same as `subject`. If the folder for the `session` 
    does not exist, it will be created.
    
    When the files are mapped, their filenames will be preserved and the correct
    folder structure will be reconstructed if it was previously flattened.

    Behavioral data
    ~~~~~~~~~~~~~~~
     
    In this step the subject specific and behavioral data that is present in 
    `<bids_study>/participants.tsv` and `phenotype/*.tsv` files, will be parsed
    and split so that data belonging to a specific participant will be mapped to 
    that participant's sessions 'behavior' folder (e.g. 
    `<QuNex study folder>/sessions/s14_01/behavior/masq01.tsv`). In this way 
    the session folder contains all the behavioral data relevant for that 
    participant.

    Step 2 - Mapping image files to QuNex Suite `nii` folder
    ---------------------------------------------------------
    
    For each session separately, images from the `bids` folder are 
    mapped to the `nii` folder and appropriate `session.txt` file is created per
    standard QuNex specification.

    The second step is achieved by running `map_bids2nii` on each session folder.
    This step is run automatically, but can be invoked indepdendently if mapping 
    of bids dataset to QuNex Suite folder structure was already completed. For 
    detailed information about this step, please review `map_bids2nii` inline 
    help.

    Notes
    -----

    Please see `map_bids2nii` inline documentation!

    EXAMPLE USE
    ===========
    
    ::

        qunex import_bids sessionsfolder=myStudy overwrite=yes bidsname=swga
    """

    print("Running import_bids\n==================")

    if action not in ['link', 'copy', 'move']:
        raise ge.CommandError("import_bids", "Invalid action specified", "%s is not a valid action!" % (action), "Please specify one of: copy, link, move!")

    if overwrite not in ['yes', 'no']:
        raise ge.CommandError("import_bids", "Invalid option for overwrite", "%s is not a valid option for overwrite parameter!" % (overwrite), "Please specify one of: yes, no!")

    if archive not in ['leave', 'move', 'copy', 'delete']:
        raise ge.CommandError("import_bids", "Invalid dataset archive option", "%s is not a valid option for dataset archive option!" % (archive), "Please specify one of: move, copy, delete!")

    if fileinfo not in ['short', 'full', None]:
        raise ge.CommandError("import_bids", "Invalid fileinfo option", "%s is not a valid option for fileinfo parameer!" % (fileinfo), "Please specify one of: short, full!")        

    if sessionsfolder is None:
        sessionsfolder = os.path.abspath(".")

    qxfolders = gc.deduceFolders({'sessionsfolder': sessionsfolder})

    if inbox is None:
        inbox = os.path.join(sessionsfolder, 'inbox', 'BIDS')    
    
    sessionsList = {'list': [], 'clean': [], 'skip': [], 'map': [], 'append': [], 'bids': False}
    allOk        = True
    errors       = ""

    inbox = os.path.abspath(inbox)

    # ---> Check for folders

    BIDSInbox = os.path.join(sessionsfolder, 'inbox', 'BIDS')
    if not os.path.exists(BIDSInbox):
        io = fl.makedirs(BIDSInbox)
        if not io:
            print("--> created inbox BIDS folder")
        elif io != 'File exists':
            raise ge.CommandFailed("import_bids", "I/O error: %s" % (io), "Could not create BIDS inbox [%s]!" % (BIDSInbox), "Please check paths and permissions!")

    BIDSArchive = os.path.join(sessionsfolder, 'archive', 'BIDS')
    if not os.path.exists(BIDSArchive):
        io = fl.makedirs(BIDSArchive)
        if not io:
            print("--> created BIDS archive folder")
        elif io != 'File exists':
            raise ge.CommandFailed("import_bids", "I/O error: %s" % (io), "Could not create BIDS archive [%s]!" % (BIDSArchive), "Please check paths and permissions!")

    # --- load BIDS structure
    # template folder
    niuTemplateFolder = os.environ["NIUTemplateFolder"]
    bidsStructure = os.path.join(niuTemplateFolder, "import_bids.txt")

    if not os.path.exists(bidsStructure):
        raise ge.CommandFailed("import_bids", "No BIDS structure file present!", "There is no BIDS structure file %s" % (bidsStructure), "Please check your QuNex installation")

    bids_file = open(bidsStructure)
    content = bids_file.read()
    bids = ast.literal_eval(content)

    # ---> identification of files

    print("--> identifying files in %s" % (inbox))

    sourceFiles = []
    processAll  = True
    select = None

    if os.path.exists(inbox):
        if os.path.isfile(inbox):
            sourceFiles = [inbox]
            folderType = 'file'
            if sessions:
                select = [e.strip().replace('sub-', '').replace('ses-', '').replace('/', '_') for e in re.split(' +|\| *|, *', sessions)]

        elif os.path.isdir(inbox):

            # -- figure out, where we are
            basename = os.path.basename(inbox)            
            if 'sub-' in basename:
                folderType = 'subject'
            elif 'ses-' in basename:
                folderType = 'session'
            elif glob.glob(os.path.join(inbox, 'sub-*')):
                folderType = 'bids_study'
            else:
                folderType = 'inbox'

            print("--> Inbox type:", folderType)

            # -- process sessions

            globfor = {'subject': '*', 'session': '*', 'bids_study': 'sub-*', 'inbox': '*'}

            if sessions:
                processAll = False
                sessions = [e.strip() for e in re.split(' +|\| *|, *', sessions)]
                if folderType == 'bids_study':
                    nsessions = []
                    for session in sessions:
                        if 'sub-' in session:
                            nsessions.append(session.replace('_', '/'))
                        elif '_' in session:
                            nsessions.append("sub-%s/ses-%s" % tuple(session.split("_")))
                        else:
                            nsessions.append('sub-' + session)
                    sessions = nsessions
                elif folderType == 'subject':
                    nsessions = []
                    for session in sessions:
                        if 'ses-' in session:
                            nsessions.append(session)
                        elif '_' in session:
                            nsessions.append("ses-%s" % (session.split("_")[1]))
                        else:
                            nsessions.append('ses-' + session)
                    sessions = nsessions                    
            else:
                sessions = [globfor[folderType]]

            # --- check for metadata

            studyat = {'subject': -1, 'session': -2}
            metadata = ['dataset_description.json', 'README', 'CHANGES', 'participants.*']
            metadata += ["%s/*" % (e) for e in bids['optional']]

            if folderType in studyat:
                metadataPath = os.path.join('/', *inbox.split(os.path.sep)[:studyat[folderType]])
            else:
                metadataPath = inbox
            
            mcandidates = []
            for m in metadata:
                mcandidates += glob.glob(os.path.join(metadataPath, m))

            for mcandidate in mcandidates:
                if os.path.isfile(mcandidate):
                    sourceFiles.append(mcandidate)
                elif os.path.isdir(mcandidate):
                    for path, dirs, files in os.walk(mcandidate):
                        for file in files:
                            sourceFiles.append(os.path.join(path, file))

            # --- compile candidates

            candidates = []
            for e in sessions:
                candidates += glob.glob(os.path.join(inbox, e))
            for candidate in candidates:
                if os.path.isfile(candidate):
                    sourceFiles.append(candidate)
                elif os.path.isdir(candidate):
                    for path, dirs, files in os.walk(candidate):
                        for file in files:
                            sourceFiles.append(os.path.join(path, file))
        else:
            raise ge.CommandFailed("import_bids", "Invalid inbox", "%s is neither a file or a folder!" % (inbox), "Please check your path!")
    else:
        raise ge.CommandFailed("import_bids", "Inbox does not exist", "The specified inbox [%s] does not exist!" % (inbox), "Please check your path!")

    if not sourceFiles:
        raise ge.CommandFailed("import_bids", "No files found", "No files were found to be processed at the specified inbox [%s]!" % (inbox), "Please check your path!")        


    # ---> definition of paths

    if bidsname is None:
        if os.path.samefile(inbox, os.path.join(sessionsfolder, 'inbox', 'BIDS')):
            bidsname = ""
            BIDSInfo = os.path.join(qxfolders['basefolder'], 'info', 'bids')
        else:
            if folderType == 'file':
                bidsname = os.path.basename(inbox)
                bidsname = re.sub('.zip$|.gz$|.tgz$', '', bidsname)
                bidsname = re.sub('.tar$', '', bidsname)
            elif folderType in ['inbox', 'bids_study']:
                bidsname = os.path.basename(inbox)
            elif folderType in ['subject', 'session']:
                bidsname = inbox.split(os.path.sep)[studyat[folderType]-1]
            BIDSInfo = os.path.join(qxfolders['basefolder'], 'info', 'bids', bidsname)
    
    print("==> Paths:")
    print("    BIDSInfo    ->", BIDSInfo)
    print("    BIDSInbox   ->", BIDSInbox)
    print("    BIDSArchive ->", BIDSArchive)

    # ---> mapping data to sessions' folders

    print("--> mapping files to QuNex bids folders")
    
    for file in sourceFiles:
        if file.endswith('.zip'):
            print("    --> processing zip package [%s]" % (file))

            try:
                z = zipfile.ZipFile(file, 'r')
                for sf in z.infolist():
                    if sf.filename[-1] != '/':
                        tfile, lock = mapToQUNEXBids(sf.filename, sessionsfolder, BIDSInfo, sessionsList, overwrite, "        ", select)
                        if tfile:
                            if lock:
                                fl.lock(tfile)
                            fdata = z.read(sf)
                            if tfile.endswith('.nii'):
                                tfile += ".gz"
                                fout = gzip.open(tfile, 'wb')
                            else:
                                fout = open(tfile, 'wb')                            
                            fout.write(fdata)
                            fout.close()
                            if lock:
                                fl.unlock(tfile)
                z.close()
                print("        -> done!")
            except:
                print("        => Error: Processing of zip package failed. Please check the package!")
                errors += "\n    .. Processing of package %s failed!" % (file)
                raise

        elif '.tar' in file or '.tgz' in file:
            print("   --> processing tar package [%s]" % (file))

            try:
                tar = tarfile.open(file)
                for member in tar.getmembers():
                    if member.isfile():
                        tfile, lock = mapToQUNEXBids(member.name, sessionsfolder, BIDSInfo, sessionsList, overwrite, "        ", select)
                        if tfile:
                            if lock:
                                fl.lock(tfile)
                            fobj  = tar.extractfile(member)
                            fdata = fobj.read()
                            fobj.close()
                            if tfile.endswith('.nii'):
                                tfile += ".gz"
                                fout = gzip.open(tfile, 'wb')
                            else:
                                fout = open(tfile, 'wb')
                            fout.write(fdata)
                            fout.close()
                            if lock:
                                fl.unlock(tfile)
                tar.close()
                print("        -> done!")
            except:
                print("        => Error: Processing of tar package failed. Please check the package!")
                errors += "\n    .. Processing of package %s failed!" % (file)

        else:
            tfile, lock = mapToQUNEXBids(file, sessionsfolder, BIDSInfo, sessionsList, overwrite, "    ")
            if tfile:
                if tfile.endswith('.nii'):
                    tfile += ".gz"
                    status, msg = gc.moveLinkOrCopy(file, tfile, 'gzip', r="", prefix='    .. ', lock=lock)
                else:
                    feedback = gc.moveLinkOrCopy(file, tfile, action, r="", prefix='    .. ', lock=lock)
                    status, msg = feedback

                allOk = allOk and status
                if not status:
                    errors += msg

    # ---> close status file

    if sessionsList['bids'] == 'open':
        fl.write_status(os.path.join(BIDSInfo, 'bids_info_status'), 'Processing done on %s.' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")), 'a')

    # ---> archiving the dataset
    
    if errors:
        print("   ==> The following errors were encountered when mapping the files:")
        print(errors)
    else:
        archiveList = []

        # --> review what to archive

        # -> we're archiving a file
        if os.path.isfile(inbox):
            archiveList = [inbox]
            folderType  = 'file'

        # -> we're archiving fully processed inbox folder
        elif processAll:

            # -> from BIDSInbox
            if os.path.samefile(inbox, BIDSInbox):
                archiveList = glob.glob(os.path.join(inbox, '*'))

            # -> from external inbox location
            else:
                archiveList = [inbox]

        # -> we're archiving partially processed inbox folder
        else:   
            archiveList = candidates

        # --> archive

        if archive in ['move', 'copy', 'delete']:
            print("--> Archiving: %sing items" % (archive.replace('y', 'yy')[:-1]))

        # -> prepare target folder
        if archive in ['move', 'copy']:
            if folderType == 'file':
                archiveFolder = BIDSArchive
            elif folderType in ['inbox', 'bids_study']:
                if os.path.samefile(inbox, BIDSInbox):
                    archiveFolder = BIDSArchive
                else:
                    archiveFolder = os.path.join(BIDSArchive, os.path.basename(inbox))
            else:
                if os.path.samefile(inbox, BIDSInbox):
                    archiveFolder = os.path.join(BIDSArchive, *inbox.split(os.path.sep)[studyat[folderType]:])
                else:
                    archiveFolder = os.path.join(BIDSArchive, *inbox.split(os.path.sep)[studyat[folderType]-1:])

        # -> loop through items
        for archiveItem in archiveList:

            # -> delete items
            if archive == 'delete':
                if os.path.isfile(archiveItem):
                    io = fl.remove(archiveItem)
                else:
                    io = fl.rmtree(archiveItem)
                if io and io != "No such file or directory":
                    print("    WARNING: Could not remove %s. Please check permissions!" % (archiveItem))

            # -> move or copy items
           
            if archive in ['move', 'copy']:
                targetItem = archiveItem.replace(inbox, '')
                targetItem = re.sub(r'^%s+' % (os.path.sep), '', targetItem)
                archiveTarget = os.path.join(archiveFolder, targetItem)
                archiveTargetFolder = os.path.dirname(archiveTarget)

                # print("==> Archive folder:", archiveFolder)
                # print("==> Archive item:", targetItem)
                # print("==> Archive target:", archiveTarget)

                io = fl.makedirs(archiveTargetFolder)
                if io and io != "File exists":
                    print("    WARNING: Could not create archive folder %s. Skipping archiving. Please check permissions!" % (archiveTargetFolder))
                    archiveTargetFolder = None

                fl.lock(archiveTarget)
                try:
                    if archive == 'move':
                        shutil.move(archiveItem, archiveTargetFolder)
                    else:
                        if os.path.isfile(archiveItem):
                            shutil.copy2(archiveItem, archiveTargetFolder)
                        else:
                            if os.path.exists(archiveTarget):
                                shutil.rmtree(archiveTarget)
                            shutil.copytree(archiveItem, archiveTarget)
                except:
                    print("    WARNING: Could not %s %s. Please check permissions!" % (archive, archiveItem))
                fl.unlock(archiveTarget)

    # ---> mapping data to QuNex nii and behavioral folder

    # -> check study level data

    if sessionsList['bids'] == 'locked':
        BIDSInfoStatus = fl.wait_status(os.path.join(BIDSInfo, 'bids_info_status'), 'done')
        if BIDSInfoStatus != "done":
            print("===> WARNING: Status of behavioral files is unknown! Please check the data!")

    # --> get a list of behavioral data:

    behavior = []
    behavior += glob.glob(os.path.join(BIDSInfo, 'participants.tsv'))
    behavior += glob.glob(os.path.join(BIDSInfo, 'phenotype/*.tsv'))

    # --> run the mapping

    report = []
    for execute in ['map', 'clean']:
        for session in sessionsList[execute]:
            if session != 'bids':
                
                subject   = session.split('_')[0]
                sessionid = (session.split('_') + [''])[1]
                info      = 'subject ' + subject
                if sessionid:
                    info += ", session " + sessionid

                print

                # -- do image mapping
                try:
                    map_bids2nii(os.path.join(sessionsfolder, session), overwrite=overwrite, fileinfo=fileinfo)
                    nmapping = True
                except ge.CommandFailed as e:
                    print("===> WARNING:\n     %s\n" % ("\n     ".join(e.report)))
                    nmapping = False                    

                # -- do behavioral mapping

                try:
                    bmapping = mapBIDS2behavior(os.path.join(sessionsfolder, session), behavior, overwrite)
                except ge.CommandFailed as e:
                    print("===> WARNING:\n     %s\n" % ("\n     ".join(e.report)))
                    bmapping = False                

                # -- compile report

                if nmapping:
                    minfo = info + " image mapping completed"
                else:
                    minfo = info + " image mapping failed"
                    allOk = False

                if bmapping:
                    minfo += ", behavioral files: "
                    binfo = []
                    if bmapping['mapped']:
                        binfo.append("%d files mapped" % (len(bmapping['mapped'])))
                    else:
                        binfo.append("no files mapped")
                        
                    if bmapping['invalid']:
                        binfo.append("%d files invalid" % (len(bmapping['invalid'])))
                        # allOk = False
                    minfo += ", ".join(binfo)
                else:
                    minfo += ", behavior file mapping failed"
                    # allOk = False

                report.append(minfo)

    print("\nFinal report\n============")
        
    for line in report:
        print(line)

    if not allOk:
        raise ge.CommandFailed("import_bids", "Some actions failed", "Please check report!")

    if not report:
        raise ge.CommandNull("import_bids", "No sessions were mapped in this call. Please check report!")


def processBIDS(bfolder):
    '''
    '''

    bidsData = {}
    sourceFiles = []
    
    if os.path.exists(bfolder):
        for path, dirs, files in os.walk(bfolder):
            for file in files:
                sourceFiles.append(os.path.join(path, file))
    else:
        raise ge.CommandFailed("processBIDS", "No bids folder present!", "There is no bids data in session folder %s" % (bfolder), "Please import BIDS data first!")
    
    # --- load BIDS structure
    # template folder
    niuTemplateFolder = os.environ["NIUTemplateFolder"]
    bidsStructure = os.path.join(niuTemplateFolder, "import_bids.txt")

    if not os.path.exists(bidsStructure):
        raise ge.CommandFailed("processBIDS", "No BIDS structure file present!", "There is no BIDS structure file %s" % (bidsStructure), "Please check your QuNex installation")

    bids_file = open(bidsStructure)
    content = bids_file.read()
    bids = ast.literal_eval(content)

    # -> map all the files
    
    for sfile in sourceFiles:
        parts = re.split("_|/|\.", sfile)
    
        # --> is it optional content
    
        optional = [e for e in parts if e in bids['optional']]
        if optional:
            optional = optional[0]
    
        # --> get session ID
    
        subject = [e.split('-')[1] for e in parts if e.startswith('sub-')] + ['']
        session = [e.split('-')[1] for e in parts if e.startswith('ses-')] + ['']
        session = "_".join([e for e in [subject[0], session[0]] if e])
        if not session:
            session = 'study'
    
        if session not in bidsData:
            bidsData[session] = {}
    
        # --> get modality
    
        modality = [e for e in parts if e in bids['modalities']]
        if modality:
            modality = modality[0]
            if modality not in bidsData[session]:
                bidsData[session][modality] = []
    
            info = dict(zip(bids[modality]['info'], [None for e in range(len(bids[modality]['info']))]))
            info.update(dict([(i, part.split('-')[1]) for part in parts for i in bids[modality]['info'] if '-' in part and i == part.split('-')[0]]))
            info['filepath'] = sfile
            info['filename'] = os.path.basename(sfile)
    
            info['label'] = ([None] + [part for part in parts if part in bids[modality]['label']])[-1]
    
            bidsData[session][modality].append(info)
        else:
            bidsData[session]['files'] = {'filepath': sfile, 'filename': os.path.basename(sfile)}

    # --> sort within modalities

    for session in bidsData:
        for modality in bids['modalities']:
            if modality in bidsData[session]:
                for key in bids[modality]['sort']:
                    bidsData[session][modality].sort(key=lambda x: x[key] or "")

    # --> prepare and sort images

    for session in bidsData:
        bidsData[session]['images'] = {'list': [], 'info': {}}
        for modality in ['anat', 'fmap', 'func', 'dwi']:
            if modality in bidsData[session]:
                for element in bidsData[session][modality]:
                    if '.nii' in element['filename']:
                        bidsData[session]['images']['list'].append(element['filename'])
                        element['tag'] = ' '.join(["%s-%s" % (e, element[e]) for e in bids[modality]['tag'] if element[e]])
                        element['tag'] = element['tag'].replace('label-', '')
                        element['tag'] = element['tag'].replace('task-', '')
                        bidsData[session]['images']['info'][element['filename']] = element

    return bidsData
        


def map_bids2nii(sourcefolder='.', overwrite='no', fileinfo=None):
    """
    ``map_bids2nii [sourcefolder='.'] [overwrite='no'] [fileinfo='short']``

    Maps data organized according to BIDS specification to `nii` folder 
    structure as expected by QuNex commands.

    INPUTS
    ======

    --sourcefolder      The base session folder in which bids folder with data 
                        and files for the session is present. [.]

    --overwrite         Parameter that specifies what should be done in cases 
                        where there are existing data stored in `nii` folder. 
                        ['no'] The options are:

                        - no (do not overwrite the data, skip session)
                        - yes (remove existing files in `nii` folder and redo 
                          the mapping)


    --fileinfo          What file information to include in the session.txt 
                        file. Options are:

                        - short (only provide the short description based on the
                          identified BIDS tags)
                        - full (list the full file name excluding the 
                          participant id, session name and extension)

    OUTPUTS
    =======

    After running the mapped nifti files will be in the `nii` subfolder, 
    named with sequential image number. `session.txt` will be in the base 
    session folder and `bids2nii.log` will be in the `bids` folder.
    
    session.txt file
    ----------------

    The session.txt will be placed in the session base folder. It will contain
    the information about the session id, subject id location of folders and a 
    list of created NIfTI images with their description.

    An example session.txt file would be:

    id: 06_retest
    subject: 06
    bids: /Volumes/tigr/MBLab/fMRI/bidsTest/sessions/06_retest/bids
    raw_data: /Volumes/tigr/MBLab/fMRI/bidsTest/sessions/06_retest/nii
    hcp: /Volumes/tigr/MBLab/fMRI/bidsTest/sessions/06_retest/hcp
    
    01: T1w
    02: bold covertverbgeneration
    03: bold fingerfootlips
    04: bold linebisection
    05: bold overtverbgeneration
    06: bold overtwordrepetition
    07: dwi

    For each of the listed images there will be a corresponding NIfTI file in
    the nii subfolder (e.g. 04.nii.gz for the line bisection BOLD sequence). 
    The generated session.txt files form the basis for the following HCP and 
    other processing steps. `id` field will be set to the full session name,
    `subject` will be set to the text preceeding the underscore (`_`) 
    character.

    bids2nii.log file
    -----------------

    The `bids2nii.log` provides the information about the date and time the
    files were mapped and the exact information about which specific file 
    from the `bids` folder was mapped to which file in the `nii` folder.

    USE
    ===

    The command is used to map data organized according to BIDS specification,
    residing in `bids` session subfolder to `nii` folder as expected by QuNex
    functions. The command checks the imaging data and compiles a list in the
    following order:

    - anatomical images
    - fieldmap images
    - functional images
    - diffusion weighted images

    Once the list is compiled, the files are mapped to `nii` folder to files
    named by ordinal number of the image in the list. To save space, files are 
    not copied but rather hard links are created. Only image, bvec and bval 
    files are mapped from the `bids` to `nii` folder. The exact mapping is
    noted in file `bids2nii.log` that is saved to the `bids` folder. The 
    information on images is also compiled in `session.txt` file that is 
    generated in the main session folder. For every image all the information
    present in the bids filename is listed.

    Multiple sessions and scheduling
    --------------------------------

    The command can be run for multiple sessions by specifying `sessions` and
    optionally `sessionsfolder` and `parsessions` parameters. In this case the
    command will be run for each of the specified sessions in the sessionsfolder
    (current directory by default). Optional `filter` and `sessionids` 
    parameters can be used to filter sessions or limit them to just specified 
    id codes. (for more information see online documentation). `sourcefolder` 
    will be filled in automatically as each session's folder. Commands will run 
    in parallel where the degree of parallelism is determined by `parsessions` 
    (1 by default).

    If `scheduler` parameter is set, the command will be run using the specified
    scheduler settings (see `qunex ?schedule` for more information). If set in
    combination with `sessions` parameter, sessions will be processed over
    multiple nodes, `core` parameter specifying how many sessions to run per
    node. Optional `scheduler_environment`, `scheduler_workdir`,
    `scheduler_sleep`, and `nprocess` parameters can be set.

    Set optional `logfolder` parameter to specify where the processing logs
    should be stored. Otherwise the processor will make best guess, where the
    logs should go.

    Do note that as this command only performs file mapping and no image or 
    file processing, the best performance might be achieved by running on a 
    single node and a single core.

    Caveats and missing functionality
    ---------------------------------

    File order
    ----------

    The files are ordered according to best guess sorted primarily by modality. 
    This can be problematic for further HCP processing when different fieldmap
    files are used for different BOLD and structural files. In the a future 
    version the files will be organized so that fieldmaps will precede the 
    files to which they correspond, according to HCP processing expectations.

    .bvec and .bval files
    ~~~~~~~~~~~~~~~~~~~~~

    `.bvec` and `.bval` files are expected to be present along with dwi files
    in each session folder. If they are only present in the main folder, they
    are currently not mapped to the `.nii` folder.

    Image format
    ~~~~~~~~~~~~

    The function assumes that all the images are saved as `.nii.gz` files!

    EXAMPLE USE
    ===========
    
    ::

        qunex map_bids2nii folder=. overwrite=yes
    """

    if fileinfo is None:
        fileinfo = 'short'

    if fileinfo not in ['short', 'full']:
        raise ge.CommandError("map_bids2nii", "Invalid fileinfo option", "%s is not a valid option for fileinfo parameer!" % (fileinfo), "Please specify one of: short, full!")        


    sfolder = os.path.abspath(sourcefolder)
    bfolder = os.path.join(sfolder, 'bids')
    nfolder = os.path.join(sfolder, 'nii')

    session = os.path.basename(sfolder)
    subject = session.split('_')[0]
    sessionid = (session.split('_') + [''])[1]

    info = 'subject ' + subject
    if sessionid:
        info += ", session " + sessionid

    print
    splash = "Running map_bids2nii for %s" % (info)
    print(splash)
    print("".join(['=' for e in range(len(splash))]))

    if overwrite not in ['yes', 'no']:
        raise ge.CommandError("map_bids2nii", "Invalid option for overwrite specified", "%s is not a valid option for the overwrite parameter!" % (overwrite), "Please specify one of: yes, no!")

    # --- process bids folder

    bidsData = processBIDS(bfolder)

    if session not in bidsData:
        raise ge.CommandFailed("map_bids2nii", "Unrecognized session!", "This folder [%s] does not have a valid matching BIDS session!" % (sfolder), "Please check your data!")

    bidsData = bidsData[session]

    if not bidsData['images']['list']:
        raise ge.CommandFailed("map_bids2nii", "No image files in bids folder!", "There are no image files in the bids folder [%s]" % (bfolder), "Please check your data!")

    # --- check for presence of nifti files

    if os.path.exists(nfolder):
        nfiles = len(glob.glob(os.path.join(nfolder, '*.nii*')))
        if nfiles > 0:
            if overwrite == 'no':
                raise ge.CommandFailed("map_bids2nii", "Existing files present!", "There are existing files in the nii folder [%s]" % (nfolder), "Please check or set parameter 'overwrite' to yes!")
            else:
                shutil.rmtree(nfolder)
                os.makedirs(nfolder)
                print("--> cleaned nii folder, removed existing files")
    else:
        os.makedirs(nfolder)

    # --- create session.txt file
    sout = gc.createSessionFile("map_bids2nii", sfolder, session, subject, overwrite)

    # --- open bids2nii log file
    if overwrite == 'yes':
        mode = 'w'
    else:
        mode = 'a'

    bout  = open(os.path.join(bfolder, 'bids2nii.log'), mode)
    print("BIDS to nii mapping report, executed on %s" % (datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")), file=bout)

    # --- map files

    allOk = True

    imgn = 0
    for image in bidsData['images']['list']:
        imgn += 1

        tfile = os.path.join(nfolder, "%02d.nii.gz" % (imgn))
        
        status = gc.moveLinkOrCopy(bidsData['images']['info'][image]['filepath'], tfile, action='link')
        if status:
            print("--> linked %02d.nii.gz <-- %s" % (imgn, bidsData['images']['info'][image]['filename']))
            if fileinfo == 'short':
                print("%02d: %s" % (imgn, bidsData['images']['info'][image]['tag']), file=sout)
            elif fileinfo == 'full':
                fullinfo = bidsData['images']['info'][image]['filename'].replace('.nii.gz', '').replace('sub-%s_' % (subject), '').replace('ses-%s_' % (sessionid), '')
                print("%02d: %s" % (imgn, fullinfo), file=sout)

            print("%s => %s" % (bidsData['images']['info'][image]['filepath'], tfile), file=bout)
        else:
            allOk = False
            print("==> ERROR: Linking failed: %02d.nii.gz <-- %s" % (imgn, bidsData['images']['info'][image]['filename']))
            print("FAILED: %s => %s" % (bidsData['images']['info'][image]['filepath'], tfile), file=bout)

        status = True
        if bidsData['images']['info'][image]['label'] == 'dwi':
            sbvec = bidsData['images']['info'][image]['filepath'].replace('.nii.gz', '.bvec')
            tbvec = tfile.replace('.nii.gz', '.bvec')
            if gc.moveLinkOrCopy(sbvec, tbvec, action='link'):
                print("%s => %s" % (sbvec, tbvec), file=bout)
            else:
                status = False

            sbval = bidsData['images']['info'][image]['filepath'].replace('.nii.gz', '.bval')
            tbval = tfile.replace('.nii.gz', '.bval')
            if gc.moveLinkOrCopy(sbval, tbval, action='link', status=status):
                print("%s => %s" % (sbval, tbval), file=bout)
            else:
                status = False

            if not status:
                print("==> WARNING: bval/bvec files were not found and were not mapped for %02d.nii.gz [%s]!" % (imgn, bidsData['images']['info'][image]['filename'].replace('.nii.gz', '.bval/.bvec')), file=bout)
                print("==> ERROR: bval/bvec files were not found and were not mapped: %02d.bval/.bvec <-- %s" % (imgn, bidsData['images']['info'][image]['filename'].replace('.nii.gz', '.bval/.bvec')))
                allOk = False
    
    sout.close()
    bout.close()

    if not allOk:
        raise ge.CommandFailed("map_bids2nii", "Not all actions completed successfully!", "Some files for session %s were not mapped successfully!" % (session), "Please check logs and data!")



def mapBIDS2behavior(sfolder='.', behavior=[], overwrite='no'):
    '''
    '''

    # -- set up variables

    sfolder = os.path.abspath(sfolder)
    bfolder = os.path.join(sfolder, 'behavior')

    session = os.path.basename(sfolder)
    subject = session.split('_')[0]
    sessionid = (session.split('_') + [''])[1]

    # -- print splash

    info = 'subject ' + subject
    if sessionid:
        info += ", session " + sessionid

    print
    splash = "Running mapBIDS2behavior for %s" % (info)
    print(splash)
    print("".join(['=' for e in range(len(splash))]))

    # -- map data

    report = {'mapped': [], 'invalid': []}

    subjectid = "sub-" + subject
    if not os.path.exists(bfolder):
        print("--> created behavior subfolder")
        os.makedirs(bfolder)    

    for bfile in behavior:
        outlines = []
        error = "Data for %s not found in file." % (subjectid)
        with open(bfile, 'r') as f:
            first = True
            for line in f:
                line = line.strip()
                if first:
                    first = False       
                    fields = line.split('\t')
                    if 'participant_id' in fields:
                        sidcol = fields.index('participant_id')
                        outlines.append(line)
                    else:
                        error = "No 'participant_id' field in file."
                        break
                else:
                    values = line.split('\t')
                    if values[sidcol] == subjectid:
                        outlines.append(line)

        bfilename = os.path.basename(bfile)
        if len(outlines) >= 2:                     
            with open(os.path.join(bfolder, bfilename), 'w') as ofile:
                for oline in outlines:
                    print(oline, file=ofile)
            print("--> mapped:", bfilename)
            report['mapped'].append(bfilename)
        elif len(outlines) < 2:
            print("==> WARNING: Could not map %s! %s Please inspect file for validity!" % (bfilename, error))
            report['invalid'].append(bfilename)
        else:
            print("==> WARNING: Could not map %s! More than one line matching %s! Please inspect file for validity!" % (bfilename, subjectid))
            report['invalid'].append(bfilename)

    return report
