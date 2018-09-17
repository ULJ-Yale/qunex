#!/usr/bin/env python
# encoding: utf-8
"""
g_bids.py

Functions for importing and exporting BIDS data to MNAP file structure.

* BIDSImport      ... maps BIDS data to MNAP structure
* BIDSExport      ... exports MNAP data to BIDS structured folder

The commands are accessible from the terminal using gmri utility.

Copyright (c) Grega Repovs. All rights reserved.
"""

import os
import os.path
import re
import shutil
import niutilities.g_exceptions as ge
import zipfile
import tarfile

bids = {
    'modalities': ['anat', 'func', 'dwi', 'fmap'],
    'optional': ['code', 'derivatives', 'stimuli', 'sourcedata'],
    'anat': {
        'label': ['T1w', 'T2w', 'T1rho', 'T1map', 'T2map', 'T2star', 'FLAIR', 'FLASH', 'PD', 'PDMap', 'PDT2', 'inplaneT1', 'inplaneT2', 'angio', 'defacemask'],
        'info':  ['acq', 'run', 'ce', 'rec', 'mod', 'ses'],
        'sort':  ['label', 'acq', 'run', 'ce', 'rec', 'mod'],
        'tag':   ['label', 'acq', 'ce', 'rec', 'mod'],
    },
    'func': {
        'label': ['bold', 'sbref'],
        'info':  ['task', 'acq', 'rec', 'run', 'echo', 'ses'],
        'sort':  ['task', 'run', 'acq', 'echo', 'rec'],
        'tag':   ['label', 'task', 'acq', 'echo', 'rec']
    },
    'dwi': {
        'label': ['bold', 'sbref'],
        'info':  ['acq', 'run', 'ses'],
        'sort':  ['acq', 'run'],
        'tag':   ['label', 'acq']
    },
    'fmap': {
        'label': ['phasediff', 'magnitude', 'magnitude1', 'magnitude2', 'phase1', 'phase2', 'epi'],
        'info':  ['acq', 'run', 'ses', 'dir'],
        'sort':  ['acq', 'dir', 'run'],
        'tag':   ['label', 'dir', 'acq']
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

    else:
        if r is None:
            return False
        else:
            return (False, "%s%sERROR: %s could not be %sed, source file does not exist [%s]! " % (r, prefix, name, action, source))


def mapToMNAPBids(file, subjectsfolder, bidsName, sessions, existing, prefix):
    '''
    Identifies and returns the intended location of the file based on its name.
    '''

    folder   = os.path.join(os.path.dirname(subjectsfolder), 'info', 'bids', bidsName)
    subject  = ""
    session  = ""
    optional = ""
    modality = ""

    for part in re.split("_|/|\.", file):
        if 'sub-' in part:
            subject = part.split('-')[1]            
        elif 'ses' in part:
            session = part.split('-')[1]
        elif part in bids['optional']:
            optional = part
        elif part in bids['modalities']:
            modality = part

    session = "_".join([e for e in [subject, session] if e])
    if session:
        folder = os.path.join(subjectsfolder, session, 'bids')
    else:
        session = 'bids'

    if session in sessions['skip']:
        return False        
    elif session not in sessions['list']:
        sessions['list'].append(session)
        if os.path.exists(folder):
            if existing == 'clean':
                print prefix + "--> bids for session %s already exists: cleaning session" % (session)
                shutil.rmtree(folder)                    
                sessions['clean'].append(session)
            elif existing == 'skip':
                sessions['skip'].append(session)
                print prefix + "--> bids for session %s already exists: skipping session" % (session)
            elif existing == 'append':
                sessions['append'].append(session)
                print prefix + "--> bids for session %s already exists: appending files" % (session)
            elif existing == 'replace':
                sessions['replace'].append(session)
                print prefix + "--> bids for session %s already exists: replacing files" % (session)
        
    tfile = os.path.join(folder, optional, modality, os.path.basename(file))

    if os.path.exists(tfile):
        if session in sessions['append']:
            return False
        else:
            os.remove(tfile)
    elif not os.path.exists(os.path.dirname(tfile)):
        os.makedirs(os.path.dirname(tfile))

    return tfile


def BIDSImport(subjectsfolder=None, inbox=None, action='link', existing='skip', archive='move', bidsName=None):
    '''
    BIDSImport [subjectsfolder=.] [inbox=<subjectsfolder>/inbox/MR] [action=link] [existing=skip] [archive=move] [bidsName=<inbox folder name>]

    existing:
    - skip    .. skip if a session already exists
    - clean   .. clean and replace
    - append  .. append only new files
    - replace .. replace any preexisting files

    # Operation:
    # - process the files in the package (archive or folder)
    #   - check / create subject folder(s) (multiple if there are multiple session data)
    #   - copy / map subject specific files to their 'bids' folder
    # - process by subject
    #   - build dictionary from file info
    #   - figure out the order of the files for the nii folder
    #   - map the files in the nii folder
    #   - create subject.txt file
    #   - create bids2mnap.log in subjects 'bids' folder
    
    ----------------
    Written by Grega Repovš

    Changelog
    2018-09-16 Grega Repovš
             - Initial version
    '''

    print "Running BIDSImport\n=================="

    if action not in ['link', 'copy', 'move']:
        ge.CommandError("BIDSImport", "Invalid action specified", "%s is not a valid action!" % (action), "Please specify one of: copy, link, move!")

    if existing not in ['skip', 'clean', 'append', 'replace']:
        ge.CommandError("BIDSImport", "Invalid option for existing files specified", "%s is not a valid option for existing files!" % (existing), "Please specify one of: skip, clean, append, replace!")

    if subjectsfolder is None:
        subjectsfolder = os.path.abspath(".")

    if inbox is None:
        inbox = os.path.join(subjectsfolder, 'inbox', 'MR')
        bidsName = ""
    else:
        bidsName = os.path.basename(inbox)
        bidsName = re.sub('.zip$|.gz$', '', bidsName)
        bidsName = re.sub('.tar$', '', bidsName)

    sessions = {'list': [], 'clean': [], 'skip': [], 'replace': [], 'append': []}
    allOk    = True
    errors   = ""

    # ---> identification of files

    print "--> identifying files in %s" % (inbox)

    sourceFiles = []

    if os.path.isfile(inbox):
        sourceFiles = [inbox]
    elif os.path.isdir(inbox):
        for path, dirs, files in os.walk(inbox):
            for file in files:
                sourceFiles.append(os.path.join(path, file))
    else:
        ge.CommandError("BIDSImport", "Invalid inbox", "%s is neither a file or a folder!" % (inbox), "Please check your path!")

    # ---> extraction of archives

    print "--> mapping files to MNAP bids folders"

    toArchive = []

    for file in sourceFiles:
        if file.endswith('.zip'):
            print "    --> processing zip package [%s]" % (file)

            z = zipfile.ZipFile(file, 'r')
            for sf in z.infolist():
                if sf.file_size > 0:
                    tfile = mapToMNAPBids(sf.filename, subjectsfolder, bidsName, sessions, existing, "        ")
                    if tfile:
                        fdata = z.read(sf)
                        fout = open(tfile, 'wb')
                        fout.write(fdata)
                        fout.close()
            z.close()
            print "        -> done!"
            toArchive.append(file)

        elif '.tar' in file:
            print "   --> processing tar package [%s]" % (file)

            tar = tarfile.open(file)
            for member in tar.getmembers():
                if member.isfile():
                    tfile = mapToMNAPBids(member.name, subjectsfolder, bidsName, sessions, existing, "        ")
                    if tfile:
                        fobj  = tar.extractfile(member)
                        fdata = fobj.read()
                        fobj.close()
                        fout = open(tfile, 'wb')
                        fout.write(fdata)
                        fout.close()
            tar.close()
            print "        -> done!"
            toArchive.append(file)

        else:
            tfile = mapToMNAPBids(file, subjectsfolder, bidsName, sessions, existing, "    ")
            if tfile:
                status, msg = moveLinkOrCopy(file, tfile, action, r="", prefix='    .. ')
                allOk = allOk and status
                if not status:
                    errors += msg

    if toArchive:
        for package in toArchive:
            if archive == 'move':
                print "--> moving package %s to archive" % (package)
                shutil.move(package, os.path.join(subjectsfolder, 'archive', 'MR'))
            if archive == 'copy':
                print "--> copying package %s to archive" % (package)
                shutil.copy2(package, os.path.join(subjectsfolder, 'archive', 'MR'))
            if archive == 'delete':
                print "--> deleting package %s" % (package)
                os.remove(package)

    if errors:
        print "   ==> The following errors were encountered when mapping the files:"
        print errors

    if not allOk:
        raise ge.CommandFailed("BIDSImport", "Some actions failed", "Please check report!")

