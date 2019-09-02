#!/usr/bin/env python2.7
# encoding: utf-8
"""
g_bids.py

Functions for importing and exporting BIDS data to Qu|Nex file structure.

* BIDSImport      ... maps BIDS data to Qu|Nex structure
* BIDSExport      ... exports Qu|Nex data to BIDS structured folder

The commands are accessible from the terminal using qunex command.

Copyright (c) Grega Repovs. All rights reserved.
"""

import os
import os.path
import re
import shutil
import niutilities.g_exceptions as ge
import niutilities.g_core as gc
import zipfile
import tarfile
import glob
import datetime
import gzip
import sys

bids = {
    'modalities': ['anat', 'func', 'dwi', 'fmap'],
    'optional': ['code', 'derivatives', 'stimuli', 'sourcedata', 'phenotype'],
    'anat': {
        'label': ['T1w', 'T2w', 'T1rho', 'T1map', 'T2map', 'T2star', 'FLAIR', 'FLASH', 'PD', 'PDMap', 'PDT2', 'inplaneT1', 'inplaneT2', 'angio', 'defacemask'],
        'info':  ['acq', 'run', 'ce', 'rec', 'echo', 'mod', 'ses'],
        'sort':  ['mod', 'rec', 'ce', 'echo','run', 'acq', 'label'],
        'tag':   ['label', 'acq', 'ce', 'rec', 'mod', 'echo', 'run'],
    },
    'func': {
        'label': ['bold', 'sbref'],
        'info':  ['task', 'acq', 'rec', 'run', 'echo', 'ses'],
        'sort':  ['rec', 'echo', 'acq', 'run', 'task'],
        'tag':   ['label', 'task', 'acq', 'echo', 'rec', 'run']
    },
    'dwi': {
        'label': ['dwi'],
        'info':  ['acq', 'run', 'ses'],
        'sort':  ['run', 'acq'],
        'tag':   ['label', 'acq', 'run']
    },
    'fmap': {
        'label': ['phasediff', 'magnitude', 'magnitude1', 'magnitude2', 'phase1', 'phase2', 'epi'],
        'info':  ['acq', 'run', 'ses', 'dir'],
        'sort':  ['run', 'dir', 'acq' ],
        'tag':   ['label', 'dir', 'acq', 'run']
    }
}



def moveLinkOrCopy(source, target, action=None, r=None, status=None, name=None, prefix=None):
    """
    moveLinkOrCopy - documentation not yet available.
    """
    if action is None:
        action = 'link'
    if status is None:
        status = True
    if name is None:
        name = source
    if prefix is None:
        prefix = ""

    if os.path.exists(source):

        if not os.path.exists(os.path.dirname(target)):
            try:
                os.makedirs(os.path.dirname(target))
            except:
                if r is None:
                    return False
                else:
                    return (False, "%s%sERROR: %s could not be %sed, target folder could not be created, check permissions! " % (r, prefix, name, action))

        if action == 'link':
            try:
                if os.path.exists(target):
                    if os.path.samefile(source, target):
                        if r is None:
                            return status
                        else:
                            return (status, "%s%s%s already mapped" % (r, prefix, name))
                    else:
                        os.remove(target)
                os.link(source, target)
                if r is None:
                    return status
                else:
                    return (status, "%s%s%s mapped" % (r, prefix, name))
            except:
                action = 'copy'

        if action == 'copy':
            try:
                shutil.copy2(source, target)
                if r is None:
                    return status
                else:
                    return (status, "%s%s%s copied" % (r, prefix, name))
            except:
                if r is None:
                    return False
                else:
                    return (False, "%s%sERROR: %s could not be copied, check permissions! " % (r, prefix, name))

        if action == 'move':
            try:
                shutil.move(source, target)
                if r is None:
                    return status
                else:
                    return (status, "%s%s%s moved" % (r, prefix, name))
            except:
                if r is None:
                    return False
                else:
                    return (False, "%s%sERROR: %s could not be moved, check permissions! " % (r, prefix, name))

        if action == 'gzip':
            try:
                with open(source, 'rb') as f_in, gzip.open(target, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                if r is None:
                    return status
                else:
                    return (status, "%s%s%s copied and gzipped" % (r, prefix, name))
            except:
                if r is None:
                    return False
                else:
                    return (False, "%s%sERROR: %s could not be copied and gzipped, check permissions! " % (r, prefix, name))

    else:
        if r is None:
            return False
        else:
            return (False, "%s%sERROR: %s could not be %sed, source file does not exist [%s]! " % (r, prefix, name, action, source))


def mapToQUNEXBids(file, subjectsfolder, bidsname, sessionsList, overwrite, prefix):
    '''
    Identifies and returns the intended location of the file based on its name.
    '''
    try:
        if subjectsfolder[-1] == '/':
            subjectsfolder = subjectsfolder[:-1]
    except:
        pass

    folder   = os.path.join(os.path.dirname(subjectsfolder), 'info', 'bids', bidsname)
    subject  = ""
    session  = ""
    optional = ""
    modality = ""

    for part in re.split("_|/|\.", file):
        if part.startswith('sub-'):
            subject = part.split('-')[1]            
        elif part.startswith('ses-'):
            session = part.split('-')[1]
        elif part in bids['optional']:
            optional = part
        elif part in bids['modalities']:
            modality = part
        else:
            for targetModality in bids['modalities']:
                if part in bids[targetModality]['label']:
                    modality = targetModality 

    session = "_".join([e for e in [subject, session] if e])
    if session:
        folder = os.path.join(subjectsfolder, session, 'bids')
    else:
        session = 'bids'

    if session in sessionsList['skip']:
        return False        
    elif session not in sessionsList['list']:
        sessionsList['list'].append(session)
        if os.path.exists(folder):
            if overwrite == 'yes':
                print prefix + "--> bids for session %s already exists: cleaning session" % (session)
                shutil.rmtree(folder)                    
                sessionsList['clean'].append(session)
            elif not os.path.exists(os.path.join(folder, 'bids2nii.log')):
                print prefix + "--> incomplete bids for session %s already exists: cleaning session" % (session)
                shutil.rmtree(folder)                    
                sessionsList['clean'].append(session)
            else:
                sessionsList['skip'].append(session)
                print prefix + "--> bids for session %s already exists: skipping session" % (session)
                print prefix + "    files previously mapped:"
                with open(os.path.join(folder, 'bids2nii.log')) as bidsLog:
                    for logline in bidsLog:
                        if 'BIDS to nii mapping report' in logline:
                            continue
                        elif '=>' in logline:                            
                            mappedFile = logline.split('=>')[0].strip()
                            print prefix + "    ... %s" % (os.path.basename(mappedFile))
        else:
            print prefix + "--> creating bids session %s" % (session)
            sessionsList['map'].append(session)
        
    tfile = os.path.join(folder, optional, modality, os.path.basename(file))

    if os.path.exists(tfile):
        if session in sessionsList['skip']:
            return False
        else:
            os.remove(tfile)
    elif not os.path.exists(os.path.dirname(tfile)):
        os.makedirs(os.path.dirname(tfile))

    if session in sessionsList['skip']:
        return False

    return tfile



def BIDSImport(subjectsfolder=None, inbox=None, sessions=None, action='link', overwrite='no', archive='move', bidsname=None):
    '''
    BIDSImport [subjectsfolder=.] [inbox=<subjectsfolder>/inbox/BIDS] [sessions="*"] [action=link] [overwrite=no] [archive=move] [bidsname=<inbox folder name>]
    
    USE
    ===

    The command is used to map a BIDS dataset to the Qu|Nex Suite file structure. 

    PARAMETERS
    ==========

    --subjectsfolder    The subjects folder where all the sessions are to be 
                        mapped to. It should be a folder within the 
                        <study folder>. [.]

    --inbox             The location of the BIDS dataset. It can be any of the
                        following: the BIDS dataset top folder, a folder that 
                        contains the BIDS dataset, a path to the compressed 
                        `.zip` or `.tar.gz` package that can contain a single 
                        subject or a multi-subject dataset, or a folder that 
                        contains a compressed package. For instance the user 
                        can specify "<path>/<bids_file>.zip" or "<path>" to
                        a folder that contains multiple packages. The default 
                        location where the command will look for a BIDS dataset
                        is [<subjectsfolder>/inbox/BIDS]

    --sessions          An optional parameter that specifies a comma or pipe
                        separated list of sessions from the inbox folder to be 
                        processed. Glob patterns can be used. If provided, only
                        packets or folders within the inbox that match the list
                        of sessions will be processed. If `inbox` is a file 
                        `sessions` will not be applied. If `inbox` is a valid 
                        bids datastructure folder, then the sessions can be 
                        specified either in `<subject id>[_<session name>]`
                        format or as explicit `sub-<subject id>` names.

    --action            How to map the files to Qu|Nex structure. One of:
                        
                        - link: The files will be mapped by creating hard links
                                if possible, otherwise they will be copied.
                        - copy: The files will be copied.                    
                        - move: The files will be moved.

                        The default is 'link'

    --overwrite         The parameter specifies what should be done with 
                        data that already exists in the locations to which bids
                        data would be mapped to. Options are:

                        no   - do not overwrite the data and skip processing of
                               the session
                        yes  - remove exising files in `nii` folder and redo 
                               the mapping
        
                        The default option is 'no'. 

    --archive           What to do with the files after they were mapped. 
                        Options are:

                        leave   - leave the specified archive where it is
                        move    - move the specified archive to 
                                  <subjectsfolder>/archive/BIDS
                        copy    - copy the specified archive to 
                                  <subjectsfolder>/archive/BIDS
                        delete  - delete the archive after processing if no 
                                  errors were identified

                        The default is 'move'. Please note that there can be an
                        interactio with the `action` parameter. If files are
                        moved during action, they will be missing if `archive` 
                        is set to 'move' or 'copy'.

    --bidsname          The optional name of the BIDS dataset. If not provided
                        it will be set to the name of the inbox folder or the 
                        name of the compressed package.

    PROCESS OF BIDS MAPPING
    =======================
    
    The BIDSImport command consists of two steps:
    
    ==> Step 1 -- Mapping BIDS dataset to Qu|Nex Suite folder structure
    
    The `inbox` parameter specifies the location of the BIDS dataset. This path 
    is inspected for a BIDS compliant dataset. The path can point to a folder 
    with extracted BIDS dataset, a `.zip` or `.tar.gz` archive or a folder 
    containing one or more `.zip` or `.tar.gz` archives. In the initial step, 
    each file found will be assigned either to a specific session or the 
    overall study. 

    The BIDS files assigned to the study will be saved in the following 
    location:

        <study_folder>/info/bids/<bids_dataset_name>

    <bids_dataset_name> can be provided as a `bidsname` parameter to the command
    call. If `bidsname` is not provided, the name will be set to the name of the 
    parent folder or the name of the compressed archive.

    The files identified as belonging to a specific session will be mapped to 
    folder: 
    
        <subjects_folder>/<subject>_<session>/bids

    The `<subject>_<session>` string will be used as the identifier for the 
    session in all the following steps. If no session is specified in BIDS,
    `session` will be the same as `subject`. If the folder for the `session` 
    does not exist, it will be created.
    
    When the files are mapped, their filenames will be perserved and the correct
    folder structure will be reconstructed if it was previously flattened.

    **Behavioral data**  
    In this step the subject specific and behavioral data that is present in 
    '<bids_study>/participants.tsv' and 'phenotype/*.tsv' files, will be parsed
    and split so that data belonging to a specific participant will be mapped to 
    that participant's sessions 'behavior' folder (e.g. 
    <Qu|Nex study folder>/subjects/s14_01/behavior/masq01.tsv'). In this way the
    session folder contains all the behavioral data relevant fror that 
    participant.

    ==> Step 2 -- Mapping image files to Qu|Nex Suite `nii` folder
    
    For each session separately, images from the `bids` folder are 
    mapped to the `nii` folder and appropriate `subject.txt` file is created per
    standard Qu|Nex specification.

    The second step is achieved by running `mapBIDS2nii` on each session folder.
    This step is run automatically, but can be invoked indepdendently if mapping 
    of bids dataset to Qu|Nex Suite folder structure was already completed. For 
    detailed information about this step, please review `mapBIDS2nii` inline 
    help.
    
    
    RESULTS
    =======

    After running the `BIDSImport` command the BIDS dataset will be mapped 
    to the Qu|Nex folder structure and image files will be prepared for further
    processing along with required metadata.

    * Files pertaining to the study and not specific subject / session are
      stored in:
        <study folder>/info/bids/<bids bame>
    
    * The original BIDS session-level data is stored in:

        <subjectsfolder>/<subject_session>/bids

    * Image files mapped to new names for Qu|Nex are stored in:

        <subjects_folder>/<subject_session>/nii

    * The full description of the mapped files is in:

        <subjects_folder>/<subject_session>/subject.txt

    * The output log of BIDS mapping is in: 

        <subjects_folder>/<subject_session>/bids/bids2nii.log

    * The study-level BIDS files are in:

        <study_folder>/<info>/bids/<bidsname>

    NOTES
    =====

    Please see `mapBIDS2nii` inline documentation!

    EXAMPLE USE
    ===========
    
    ```
    qunex BIDSImport subjectsfolder=myStudy overwrite=yes bidsname=swga
    ```

    ----------------
    Written by Grega Repovš

    Changelog
    2018-09-17 Grega Repovš
             - Initial version
    2018-09-19 Grega Repovš, Alan Anticevic
             - Updated documentation, changed handling of previous data
    2019-04-13 Grega Repovš, Alan Anticevic
             - Added the option to specify subjects
    2019-04-25 Grega Repovs
             - Changed subjects to sessions
    2019-05-12 Grega Repovš
             - Reports an error if no file is found
    2019-07-18 Grega Repovs
             - Added parsing of behavioral data
    2019-07-23 Grega Repovs
             - Changed behavioral data parsing to allow mulitple measurments
               per participant
    2019-08-29 Grega Repovs
             - Updated documentation
    '''

    print "Running BIDSImport\n=================="

    if action not in ['link', 'copy', 'move']:
        raise ge.CommandError("BIDSImport", "Invalid action specified", "%s is not a valid action!" % (action), "Please specify one of: copy, link, move!")

    if overwrite not in ['yes', 'no']:
        raise ge.CommandError("BIDSImport", "Invalid option for overwrite", "%s is not a valid option for overwrite parameter!" % (overwrite), "Please specify one of: yes, no!")

    if archive not in ['leave', 'move', 'copy', 'delete']:
        raise ge.CommandError("BIDSImport", "Invalid dataset archive option", "%s is not a valid option for dataset archive option!" % (archive), "Please specify one of: move, copy, delete!")

    if subjectsfolder is None:
        subjectsfolder = os.path.abspath(".")

    qxfolders = gc.deduceFolders({'subjectsfolder': subjectsfolder})

    if inbox is None:
        inbox = os.path.join(subjectsfolder, 'inbox', 'BIDS')
        bidsname = ""
    else:
        bidsname = os.path.basename(inbox)
        bidsname = re.sub('.zip$|.gz$', '', bidsname)
        bidsname = re.sub('.tar$', '', bidsname)
    
    sessionsList = {'list': [], 'clean': [], 'skip': [], 'map': [], 'append': []}
    allOk        = True
    errors       = ""

    inbox = os.path.abspath(inbox)

    # ---> Check for folders

    if not os.path.exists(os.path.join(subjectsfolder, 'inbox', 'BIDS')):
        os.makedirs(os.path.join(subjectsfolder, 'inbox', 'BIDS'))
        print "--> creating inbox BIDS folder"

    if not os.path.exists(os.path.join(subjectsfolder, 'archive', 'BIDS')):
        os.makedirs(os.path.join(subjectsfolder, 'archive', 'BIDS'))
        print "--> creating archive BIDS folder"

    # ---> identification of files

    print "--> identifying files in %s" % (inbox)

    sourceFiles = []

    if os.path.exists(inbox):
        if os.path.isfile(inbox):
            sourceFiles = [inbox]
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

            print "--> Inbox type:", folderType

            # -- process sessions

            globfor = {'subject': '*', 'session': '*', 'bids_study': 'sub-*', 'inbox': '*'}

            if sessions:
                sessions = [e.strip() for e in re.split(' +|\| *|, *', sessions)]
                if folderType == 'bids_study':
                    nsessions = []
                    for session in sessions:
                        if 'sub-' in session:
                            nsessions.append(session)
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
                metadataPath = os.path.join('/', *inbox.split('/')[:studyat[folderType]])
            else:
                metadataPath = inbox
            
            for m in metadata:
                sourceFiles += glob.glob(os.path.join(metadataPath, m))

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
            raise ge.CommandFailed("BIDSImport", "Invalid inbox", "%s is neither a file or a folder!" % (inbox), "Please check your path!")
    else:
        raise ge.CommandFailed("BIDSImport", "Inbox does not exist", "The specified inbox [%s] does not exist!" % (inbox), "Please check your path!")

    if not sourceFiles:
        raise ge.CommandFailed("BIDSImport", "No files found", "No files were found to be processed at the specified inbox [%s]!" % (inbox), "Please check your path!")        

    # ---> mapping data to sessions' folders

    print "--> mapping files to Qu|Nex bids folders"

    for file in sourceFiles:
        if file.endswith('.zip'):
            print "    --> processing zip package [%s]" % (file)

            try:
                z = zipfile.ZipFile(file, 'r')
                for sf in z.infolist():
                    if sf.filename[-1] != '/':
                        tfile = mapToQUNEXBids(sf.filename, subjectsfolder, bidsname, sessionsList, overwrite, "        ")
                        if tfile:
                            fdata = z.read(sf)
                            if tfile.endswith('.nii'):
                                tfile += ".gz"
                                fout = gzip.open(tfile, 'wb')
                            else:
                                fout = open(tfile, 'wb')                            
                            fout.write(fdata)
                            fout.close()
                z.close()
                print "        -> done!"
            except:
                print "        => Error: Processing of zip package failed. Please check the package!"
                errors += "\n    .. Processing of package %s failed!" % (file)
                raise

        elif '.tar' in file:
            print "   --> processing tar package [%s]" % (file)

            try:
                tar = tarfile.open(file)
                for member in tar.getmembers():
                    if member.isfile():
                        tfile = mapToQUNEXBids(member.name, subjectsfolder, bidsname, sessionsList, overwrite, "        ")
                        if tfile:
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
                tar.close()
                print "        -> done!"
            except:
                print "        => Error: Processing of tar package failed. Please check the package!"
                errors += "\n    .. Processing of package %s failed!" % (file)


        else:
            tfile = mapToQUNEXBids(file, subjectsfolder, bidsname, sessionsList, overwrite, "    ")
            if tfile:
                if tfile.endswith('.nii'):
                    tfile += ".gz"
                    status, msg = moveLinkOrCopy(file, tfile, 'gzip', r="", prefix='    .. ')
                else:
                    status, msg = moveLinkOrCopy(file, tfile, action, r="", prefix='    .. ')                    

                allOk = allOk and status
                if not status:
                    errors += msg

    # ---> archiving the dataset
    
    if errors:
        print "   ==> The following errors were encountered when mapping the files:"
        print errors
    else:
        if os.path.isfile(inbox) or not os.path.samefile(inbox, os.path.join(subjectsfolder, 'inbox', 'BIDS')):
            try:
                if archive == 'move':
                    print "--> moving dataset to archive" 
                    shutil.move(inbox, os.path.join(subjectsfolder, 'archive', 'BIDS'))
                elif archive == 'copy':
                    print "--> copying dataset to archive"
                    shutil.copy2(inbox, os.path.join(subjectsfolder, 'archive', 'BIDS'))
                elif archive == 'delete':
                    print "--> deleting dataset"
                    if os.path.isfile(inbox):
                        os.remove(inbox)
                    else:
                        shutil.rmtree(inbox)
            except:
                print "==> %s failed!" % (archive)
        else:
            files = glob.glob(os.path.join(inbox, '*'))
            for file in files:
                try:
                    if archive == 'move':
                        print "--> moving dataset to archive" 
                        shutil.move(file, os.path.join(subjectsfolder, 'archive', 'BIDS'))
                    elif archive == 'copy':
                        print "--> copying dataset to archive"
                        shutil.copy2(file, os.path.join(subjectsfolder, 'archive', 'BIDS'))
                    elif archive == 'delete':
                        print "--> deleting dataset"
                        if os.path.isfile(file):
                            os.remove(file)
                        else:
                            shutil.rmtree(file)
                except:
                    print "==> %s of %s failed!" % (archive, file)

    # ---> mapping data to Qu|Nex nii and behavioral folder

    # --> get a list of behavioral data:

    bids_folder = os.path.join(qxfolders['basefolder'], 'info', 'bids', bidsname)
    behavior = []
    behavior += glob.glob(os.path.join(bids_folder, 'participants.tsv'))
    behavior += glob.glob(os.path.join(bids_folder, 'phenotype/*.tsv'))

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
                    mapBIDS2nii(os.path.join(subjectsfolder, session), overwrite)
                    nmapping = True
                except ge.CommandFailed as e:
                    print "===> WARNING:\n     %s\n" % ("\n     ".join(e.report))
                    nmapping = False                    

                # -- do behavioral mapping

                try:
                    bmapping = mapBIDS2behavior(os.path.join(subjectsfolder, session), behavior, overwrite)
                except ge.CommandFailed as e:
                    print "===> WARNING:\n     %s\n" % ("\n     ".join(e.report))
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

    print "\nFinal report\n============"
    for line in report:
        print line

    if not allOk:
        raise ge.CommandFailed("BIDSImport", "Some actions failed", "Please check report!")



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
                    bidsData[session][modality].sort(key=lambda x: x[key])

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
        


def mapBIDS2nii(sfolder='.', overwrite='no'):
    '''
    mapBIDS2nii [sfolder='.'] [overwrite='no']

    USE
    ===

    The command is used to map data organized according to BIDS specification,
    residing in `bids` session subfolder to `nii` folder as expected by Qu|Nex
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
    information on images is also compiled in `subject.txt` file that is 
    generated in the main session folder. For every image all the information
    present in the bids filename is listed.

    PARAMETERS
    ==========

    --sfolder    The base session folder in which bids folder with data and
                 files for the session is present. [.]
    
    --overwrite  Parameter that specifes what should be done in cases where
                 there are existing data stored in `nii` folder. The options
                 are:

                 no      - do not overwrite the data, skip session
                 yes     - remove exising files in `nii` folder and redo the
                           mapping

                 The default option is 'no'. 

    RESULTS
    =======

    After running the mapped nifti files will be in the `nii` subfolder, 
    named with sequential image number. `subject.txt` will be in the base 
    session folder and `bids2nii.log` will be in the `bids` folder.
    
    subject.txt file
    ----------------

    The subject.txt will be placed in the subject base folder. It will contain
    the information about the session id, subject id location of folders and a 
    list of created NIfTI images with their description.

    An example subject.txt file would be:

    id: 06_retest
    subject: 06
    bids: /Volumes/tigr/MBLab/fMRI/bidsTest/subjects/06_retest/bids
    raw_data: /Volumes/tigr/MBLab/fMRI/bidsTest/subjects/06_retest/nii
    hcp: /Volumes/tigr/MBLab/fMRI/bidsTest/subjects/06_retest/hcp
    
    01: T1w
    02: bold covertverbgeneration
    03: bold fingerfootlips
    04: bold linebisection
    05: bold overtverbgeneration
    06: bold overtwordrepetition
    07: dwi

    For each of the listed images there will be a corresponding NIfTI file in
    the nii subfolder (e.g. 04.nii.gz for the line bisection BOLD sequence). 
    The generated subject.txt files form the basis for the following HCP and 
    other processing steps. `id` field will be set to the full session name,
    `subject` will be set to the text preceeding the underscore (`_`) 
    character.

    bids2nii.log file
    -----------------

    The `bids2nii.log` provides the information about the date and time the
    files were mapped and the exact information about which specific file 
    from the `bids` folder was mapped to which file in the `nii` folder.

    MULTIPLE SESSIONS AND SCHEDULING
    ================================

    The command can be run for multiple sessions by specifying `sessions` and
    optionally `subjectsfolder` and `cores` parameters. In this case the command
    will be run for each of the specified sessions in the subjectsfolder
    (current directory by default). Optional `filter` and `subjid` parameters
    can be used to filter sessions or limit them to just specified id codes.
    (for more information see online documentation). `sfolder` will be filled in
    automatically as each subject's folder. Commands will run in parallel by
    utilizing the specified number of cores (1 by default).

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

    CAVEATS AND MISSING FUNCTIONALITY
    =================================

    File order
    ----------

    The files are ordered according to best guess sorted primarily by modality. 
    This can be problematic for further HCP processing when different fieldmap
    files are used for different BOLD and structural files. In the a future 
    version the files will be organized so that fieldmaps will precede the 
    files to which they correspond, according to HCP processing expectations.

    .bvec and .bval files
    ---------------------

    `.bvec` and `.bval` files are expected to be present along with dwi files
    in each session folder. If they are only present in the main folder, they
    are currently not mapped to the `.nii` folder.

    Image format
    ------------

    The function assumes that all the images are saved as `.nii.gz` files!


    EXAMPLE USE
    ===========
    
    ```
    qunex mapBIDS2nii folder=. overwrite=yes
    ```

    ----------------
    Written by Grega Repovš

    Changelog
    2018-09-17 Grega Repovš
             - Initial version
    2018-09-19 Grega Repovš
             - Simplified dealing with preexisting data
    2019-04-25
             - Changed subjects to sessions

    '''

    sfolder = os.path.abspath(sfolder)
    bfolder = os.path.join(sfolder, 'bids')
    nfolder = os.path.join(sfolder, 'nii')

    session = os.path.basename(sfolder)
    subject = session.split('_')[0]
    sessionid = (session.split('_') + [''])[1]

    info = 'subject ' + subject
    if sessionid:
        info += ", session " + sessionid

    print
    splash = "Running mapBIDS2nii for %s" % (info)
    print splash
    print "".join(['=' for e in range(len(splash))])

    if overwrite not in ['yes', 'no']:
        raise ge.CommandError("mapBIDS2nii", "Invalid option for overwrite specified", "%s is not a valid option for the overwrite parameter!" % (overwrite), "Please specify one of: yes, no!")

    # --- process bids folder

    bidsData = processBIDS(bfolder)
    bidsData = bidsData[session]

    if not bidsData['images']['list']:
        raise ge.CommandFailed("mapBIDS2nii", "No image files in bids folder!", "There are no image files in the bids folder [%s]" % (bfolder), "Please check your data!")

    # --- check for presence of nifti files

    if os.path.exists(nfolder):
        nfiles = glob.glob(os.path.join(nfolder, '*.nii*'))
        if nfiles > 0:
            if overwrite == 'no':
                raise ge.CommandFailed("mapBIDS2nii", "Existing files present!", "There are existing files in the nii folder [%s]" % (nfolder), "Please check or set parameter 'overwrite' to yes!")
            else:
                shutil.rmtree(nfolder)
                os.makedirs(nfolder)
                print "--> cleaned nii folder, removed existing files"
    else:
        os.makedirs(nfolder)

    # --- open subject.txt file

    sfile = os.path.join(sfolder, 'subject.txt')
    if os.path.exists(sfile):
        if overwrite == 'yes':
            os.remove(sfile)
            print "--> removed existing subject.txt file"
        else:
            raise ge.CommandFailed("mapBIDS2nii", "subject.txt file already present!", "A subject.txt file alredy exists [%s]" % (sfile), "Please check or set parameter 'overwrite' to 'yes' to rebuild it!")

    sout = open(sfile, 'w')
    print >> sout, 'id:', session
    print >> sout, 'subject:', subject
    print >> sout, 'bids:', bfolder
    print >> sout, 'raw_data:', nfolder
    print >> sout, 'hcp:', os.path.join(sfolder, 'hcp')
    print >> sout

    # --- open bids2nii log file

    if overwrite == 'yes':
        mode = 'w'
    else:
        mode = 'a'

    bout  = open(os.path.join(bfolder, 'bids2nii.log'), mode)
    print >> bout, "BIDS to nii mapping report, executed on %s" % (datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))

    # --- map files

    allOk = True

    imgn = 0
    for image in bidsData['images']['list']:
        imgn += 1

        tfile = os.path.join(nfolder, "%02d.nii.gz" % (imgn))
        
        status = moveLinkOrCopy(bidsData['images']['info'][image]['filepath'], tfile, action='link')
        if status:
            print "--> linked %02d.nii.gz <-- %s" % (imgn, bidsData['images']['info'][image]['filename'])
            print >> sout, "%02d: %s" % (imgn, bidsData['images']['info'][image]['tag'])
            print >> bout, "%s => %s" % (bidsData['images']['info'][image]['filepath'], tfile)
        else:
            allOk = False
            print "==> ERROR: Linking failed: %02d.nii.gz <-- %s" % (imgn, bidsData['images']['info'][image]['filename'])
            print >> bout, "FAILED: %s => %s" % (bidsData['images']['info'][image]['filepath'], tfile)

        status = True
        if bidsData['images']['info'][image]['label'] == 'dwi':
            sbvec = bidsData['images']['info'][image]['filepath'].replace('.nii.gz', '.bvec')
            tbvec = tfile.replace('.nii.gz', '.bvec')
            if moveLinkOrCopy(sbvec, tbvec, action='link'):
                print >> bout, "%s => %s" % (sbvec, tbvec)
            else:
                status = False

            sbval = bidsData['images']['info'][image]['filepath'].replace('.nii.gz', '.bval')
            tbval = tfile.replace('.nii.gz', '.bval')
            if moveLinkOrCopy(sbval, tbval, action='link', status=status):
                print >> bout, "%s => %s" % (sbval, tbval)
            else:
                status = False

            if not status:
                print >> bout, "==> WARNING: bval/bvec files were not found and were not mapped for %02d.nii.gz [%s]!" % (imgn, bidsData['images']['info'][image]['filename'].replace('.nii.gz', '.bval/.bvec'))
                print "==> ERROR: bval/bvec files were not found and were not mapped: %02d.bval/.bvec <-- %s" % (imgn, bidsData['images']['info'][image]['filename'].replace('.nii.gz', '.bval/.bvec'))
                allOk = False
    
    sout.close()
    bout.close()

    if not allOk:
        raise ge.CommandFailed("mapBIDS2nii", "Not all actions completed successfully!", "Some files for session %s were not mapped successfully!" % (session), "Please check logs and data!")



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
    print splash
    print "".join(['=' for e in range(len(splash))])

    # -- map data

    report = {'mapped': [], 'invalid': []}

    subjectid = "sub-" + subject
    if not os.path.exists(bfolder):
        print "--> created behavior subfolder"
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
                    print >> ofile, oline
            print "--> mapped:", bfilename
            report['mapped'].append(bfilename)
        elif len(outlines) < 2:
            print "==> WARNING: Could not map %s! %s Please inspect file for validity!" % (bfilename, error)
            report['invalid'].append(bfilename)
        else:
            print "==> WARNING: Could not map %s! More than one line matching %s! Please inspect file for validity!" % (bfilename, subjectid)
            report['invalid'].append(bfilename)

    return report

                    

