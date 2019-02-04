#!/usr/bin/env python2.7
# encoding: utf-8
"""
g_hcplifespan.py

Functions for importing HCP Lifespan data to MNAP file structure.

* HCPLSImport      ... maps HCP Lifespan data to MNAP structure

The commands are accessible from the terminal using gmri utility.

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
import json

hcpls = {
    'files': {
        'label': ['T1w', 'T2w', 'rfMRI', 'tfMRI', 'dMRI', 'SpinEchoFieldMap'],        
        'T1w': {
            'info':  [],
        },
        'T2w': {
            'info':  [],
        },
        'rfMRI': {
            'info':  ['task', 'fenc', 'ref'],
        },
        'tfMRI': {
            'info':  ['task', 'fenc', 'ref']
        },
        'dMRI': {
            'info':  ['dir', 'fenc', 'ref']
        },
        'SpinEchoFieldMap': {
            'info':  ['fenc']
        }
    },
    'folders': {
        'order': {'T1w': 1, 'T2w': 2, 'rfMRI': 3, 'tfMRI': 4, 'Diffusion': 4},
        'label': ['T1w', 'T2w', 'rfMRI', 'tfMRI', 'Diffusion'],
        'T1w': {
            'info':  [],
            'check': [
                        ['T1w'],
                        ['SpinEchoFieldMap', 'AP'],
                        ['SpinEchoFieldMap', 'PA']
                      ]
        },
        'T2w': {
            'info':  [],
            'check': [                        
                        ['T2w'],
                        ['SpinEchoFieldMap', 'AP'],
                        ['SpinEchoFieldMap', 'PA']
                     ]
        },
        'rfMRI': {
            'info':  ['task', 'fenc'],
            'check': [
                        ['SpinEchoFieldMap', 'AP'],
                        ['SpinEchoFieldMap', 'PA'],
                        ['rfMRI', 'SBRef'],
                        ['rfMRI', '-SBRef']
                     ]
        },
        'tfMRI': {
            'info':  ['task', 'fenc'],
            'check': [
                        ['SpinEchoFieldMap', 'AP'],
                        ['SpinEchoFieldMap', 'PA'],
                        ['tfMRI', 'SBRef'],
                        ['tfMRI', '-SBRef']
                     ]
        },
        'Diffusion': {
            'info':  [],
            'check': [
                        ['dMRI', 'dir98', 'AP', 'SBRef'],
                        ['dMRI', 'dir98', 'AP', '-SBRef'],
                        ['dMRI', 'dir98', 'PA', 'SBRef'],
                        ['dMRI', 'dir98', 'PA', '-SBRef'],
                        ['dMRI', 'dir99', 'AP', 'SBRef'],
                        ['dMRI', 'dir99', 'AP', '-SBRef'],
                        ['dMRI', 'dir99', 'PA', 'SBRef'],
                        ['dMRI', 'dir99', 'PA', '-SBRef']
                    ]
        }
    }    
}

unwarp = {None: "Unknown", 'i': 'x', 'j': 'y', 'k': 'z', 'i-': 'x-', 'j-': 'y-', 'k-': 'z-'}
PEDir  = {None: "Unknown", "LR": 1, "RL": 1, "AP": 2, "PA": 2}


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


def mapToMNAPHcpls(file, subjectsfolder, hcplsname, sessions, overwrite, prefix):
    '''
    Identifies and returns the intended location of the file based on its name.
    '''
    try:
        if subjectsfolder[-1] == '/':
            subjectsfolder = subjectsfolder[:-1]
    except:
        pass

    folder   = os.path.join(os.path.dirname(subjectsfolder), 'info', 'hcpls', hcplsname)

    if '\\' in file:
        pathsep = "\\"
    else:
        pathsep = "/"

    # -- extract file info

    extra = ""
    parts = file.split(pathsep)

    if 'unprocessed' not in parts:
        return False

    u = parts.index('unprocessed')
    subjid  = parts[u - 1]
    session = parts[u + 1]
    data    = parts[u + 2:]

    if session[0] == '.':
        return False

    sessionid = subjid + "_" + session

    tfolder = os.path.join(subjectsfolder, sessionid, 'hcpls')
    tfile = os.path.join(tfolder, os.sep.join(data))

    if sessionid in sessions['skip']:
        return False        
    elif sessionid not in sessions['list']:
        sessions['list'].append(sessionid)
        if os.path.exists(tfolder):
            if overwrite == 'yes':
                print prefix + "--> hcpls for session %s already exists: cleaning session" % (sessionid)
                shutil.rmtree(tfolder)                    
                sessions['clean'].append(sessionid)
            elif not os.path.exists(os.path.join(folder, 'hcpfs2nii.log')):
                print prefix + "--> incomplete hcpls for session %s already exists: cleaning session" % (session)
                shutil.rmtree(folder)                    
                sessions['clean'].append(session)
            else:
                sessions['skip'].append(session)
                print prefix + "--> hcpls for session %s already exists: skipping session" % (session)
                print prefix + "    files previously mapped:"
                with open(os.path.join(folder, 'hcpfs2nii.log')) as bidsLog:
                    for logline in bidsLog:
                        if 'HCPFS to nii mapping report' in logline:
                            continue
                        elif '=>' in logline:                            
                            mappedFile = logline.split('=>')[0].strip()
                            print prefix + "    ... %s" % (os.path.basename(mappedFile))
        else:
            print prefix + "--> creating hcpl session %s" % (sessionid)
            sessions['map'].append(sessionid)
        
    if os.path.exists(tfile):
        if sessionid in sessions['skip']:
            return False
        else:
            os.remove(tfile)
    elif not os.path.exists(os.path.dirname(tfile)):
        os.makedirs(os.path.dirname(tfile))

    if session in sessions['skip']:
        return False

    return tfile



def HCPLSImport(subjectsfolder=None, inbox=None, action='link', overwrite='no', archive='move', hcplsname=None):
    '''
    HCPLSImport [subjectsfolder=.] [inbox=<subjectsfolder>/inbox/HCPLS] [action=link] [overwrite=no] [archive=move] [hcplsname=<inbox folder name>]
    
    USE
    ===

    The command is used to map a HCPLS dataset to the MNAP Suite file structure. 

    PARAMETERS
    ==========

    --subjectsfolder    The subjects folder where all the sessions are to be 
                        mapped to. It should be a folder within the 
                        <study folder>. [.]

    --inbox             The location of the HCPLS dataset. It can be any of the
                        following: the HCPLS dataset top folder, a folder that 
                        contains the HCPLS dataset, a path to the compressed 
                        `.zip` or `.tar.gz` package that can contain a single 
                        subject or a multi-subject dataset, or a folder that 
                        contains a compressed package. For instance the user 
                        can specify "<path>/<hcpfs_file>.zip" or "<path>" to
                        a folder that contains multiple packages. The default 
                        location where the command will look for a HCPLS dataset
                        is [<subjectsfolder>/inbox/HCPLS]

    --action            How to map the files to MNAP structure. One of:
                        
                        - link: The files will be mapped by creating hard links
                                if possible, otherwise they will be copied.
                        - copy: The files will be copied.                    
                        - move: The files will be moved.

                        The default is 'link'

    --overwrite         The parameter specifies what should be done with 
                        data that already exists in the locations to which HCPLS
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
                                  <subjectsfolder>/archive/HCPLS
                        copy    - copy the specified archive to 
                                  <subjectsfolder>/archive/HCPLS
                        delete  - delete the archive after processing if no 
                                  errors were identified

                        The default is 'move'. Please note that there can be an
                        interaction with the `action` parameter. If files are
                        moved during action, they will be missing if `archive` 
                        is set to 'move' or 'copy'.

    --hcplsname         The optional name of the HCPLS dataset. If not provided
                        it will be set to the name of the inbox folder or the 
                        name of the compressed package.

    PROCESS OF HCPLS MAPPING
    ========================
    
    The HCPLSImport command consists of two steps:
    
    ==> Step 1 -- Mapping HCPLS dataset to MNAP Suite folder structure
    
    The `inbox` parameter specifies the location of the HCPLS dataset. This path 
    is inspected for a HCPLS compliant dataset. The path can point to a folder 
    with extracted HCPLS dataset, a `.zip` or `.tar.gz` archive or a folder 
    containing one or more `.zip` or `.tar.gz` archives. In the initial step, 
    each file found will be assigned either to a specific session. 

    <hcpls_dataset_name> can be provided as a `hcplsname` parameter to the command
    call. If `hcplsname` is not provided, the name will be set to the name of the 
    parent folder or the name of the compressed archive.

    The files identified as belonging to a specific subject will be mapped to 
    folder: 
    
        <subjects_folder>/<subject>_<session>/hcpls

    The `<subject>_<session>` string will be used as the identifier for the 
    session in all the following steps. If the folder for the `session` 
    does not exist, it will be created.
    
    When the files are mapped, their filenames will be perserved.

    ==> Step 2 -- Mapping image files to MNAP Suite `nii` folder
    
    For each session separately, images from the `hcpls` folder are 
    mapped to the `nii` folder and appropriate `subject.txt` file is created per
    standard MNAP specification.

    The second step is achieved by running `mapHCPLS2nii` on each session folder.
    This step is run automatically, but can be invoked indepdendently if mapping 
    of HCPLS dataset to MNAP Suite folder structure was already completed. For 
    detailed information about this step, please review `mapHCPLS2nii` inline 
    help.
    
    
    RESULTS
    =======

    After running the `HCPLSImport` command the HCPLS dataset will be mapped 
    to the MNAP folder structure and image files will be prepared for further
    processing along with required metadata.

    * The original HCPL session-level data is stored in:

        <subjectsfolder>/<subject_session>/hcpls

    * Image files mapped to new names for MNAP are stored in:

        <subjects_folder>/<subject_session>/nii

    * The full description of the mapped files is in:

        <subjects_folder>/<subject_session>/subject.txt

    * The output log of HCPLS mapping is in: 

        <subjects_folder>/<subject_session>/hcpls/hcpls2nii.log


    NOTES
    =====

    Please see `mapHCPLS2nii` inline documentation!

    EXAMPLE USE
    ===========

    gmri HCPLSImport subjectsfolder=myStudy/subjects inbox=HCPLS overwrite=yes hcplsname=hcpls

    ----------------
    Written by Grega Repovš

    Changelog
    2019-01-19 Grega Repovš
             - Initial version adopted from BIDSImport
    '''

    print "Running HCPLSImport\n=================="

    if action not in ['link', 'copy', 'move']:
        raise ge.CommandError("HCPLSImport", "Invalid action specified", "%s is not a valid action!" % (action), "Please specify one of: copy, link, move!")

    if overwrite not in ['yes', 'no']:
        raise ge.CommandError("HCPLSImport", "Invalid option for overwrite", "%s is not a valid option for overwrite parameter!" % (overwrite), "Please specify one of: yes, no!")

    if archive not in ['leave', 'move', 'copy', 'delete']:
        raise ge.CommandError("HCPLSImport", "Invalid dataset archive option", "%s is not a valid option for dataset archive option!" % (archive), "Please specify one of: move, copy, delete!")

    if subjectsfolder is None:
        subjectsfolder = os.path.abspath(".")

    if inbox is None:
        inbox = os.path.join(subjectsfolder, 'inbox', 'HCPLS')
        hcplsname = ""
    else:
        hcplsname = os.path.basename(inbox)
        hcplsname = re.sub('.zip$|.gz$', '', hcplsname)
        hcplsname = re.sub('.tar$', '', hcplsname)

    sessions = {'list': [], 'clean': [], 'skip': [], 'map': []}
    allOk    = True
    errors   = ""

    # ---> Check for folders

    if not os.path.exists(os.path.join(subjectsfolder, 'inbox', 'HCPLS')):
        os.makedirs(os.path.join(subjectsfolder, 'inbox', 'HCPLS'))
        print "--> creating inbox HCPLS folder"

    if not os.path.exists(os.path.join(subjectsfolder, 'archive', 'HCPLS')):
        os.makedirs(os.path.join(subjectsfolder, 'archive', 'HCPLS'))
        print "--> creating archive HCPLS folder"

    # ---> identification of files

    print "--> identifying files in %s" % (inbox)

    sourceFiles = []

    if os.path.exists(inbox):
        if os.path.isfile(inbox):
            sourceFiles = [inbox]
        elif os.path.isdir(inbox):
            for path, dirs, files in os.walk(inbox):
                for file in files:
                    sourceFiles.append(os.path.join(path, file))
        else:
            raise ge.CommandFailed("HCPLSImport", "Invalid inbox", "%s is neither a file or a folder!" % (inbox), "Please check your path!")
    else:
        raise ge.CommandFailed("HCPLSImport", "Inbox does not exist", "The specified inbox [%s] does not exist!" % (inbox), "Please check your path!")


    # ---> mapping data to subjects' folders

    print "--> mapping files to MNAP hcpls folders"

    for file in sourceFiles:
        if file.endswith('.zip'):
            print "    --> processing zip package [%s]" % (file)

            try:
                z = zipfile.ZipFile(file, 'r')
                for sf in z.infolist():
                    if sf.filename[-1] != '/':
                        tfile = mapToMNAPHcpls(sf.filename, subjectsfolder, hcplsname, sessions, overwrite, "        ")
                        if tfile:
                            fdata = z.read(sf)
                            fout = open(tfile, 'wb')
                            fout.write(fdata)
                            fout.close()
                z.close()
                print "        -> done!"
            except:
                print "        => Error: Processing of zip package failed. Please check the package!"
                errors += "\n    .. Processing of package %s failed!" % (file)

        elif '.tar' in file:
            print "   --> processing tar package [%s]" % (file)

            try:
                tar = tarfile.open(file)
                for member in tar.getmembers():
                    if member.isfile():
                        tfile = mapToMNAPHcpls(member.name, subjectsfolder, hcplsname, sessions, overwrite, "        ")
                        if tfile:
                            fobj  = tar.extractfile(member)
                            fdata = fobj.read()
                            fobj.close()
                            fout = open(tfile, 'wb')
                            fout.write(fdata)
                            fout.close()
                tar.close()
                print "        -> done!"
            except:
                print "        => Error: Processing of tar package failed. Please check the package!"
                errors += "\n    .. Processing of package %s failed!" % (file)

        else:
            tfile = mapToMNAPHcpls(file, subjectsfolder, hcplsname, sessions, overwrite, "    ")
            if tfile:
                status, msg = moveLinkOrCopy(file, tfile, action, r="", prefix='    .. ')
                allOk = allOk and status
                if not status:
                    errors += msg

    # ---> archiving the dataset
    
    if errors:
        print "   ==> The following errors were encountered when mapping the files:"
        print errors
    else:
        if os.path.isfile(inbox) or not os.path.samefile(inbox, os.path.join(subjectsfolder, 'inbox', 'HCPLS')):
            try:
                if archive == 'move':
                    print "--> moving dataset to archive" 
                    shutil.move(inbox, os.path.join(subjectsfolder, 'archive', 'HCPLS'))
                elif archive == 'copy':
                    print "--> copying dataset to archive"
                    shutil.copy2(inbox, os.path.join(subjectsfolder, 'archive', 'HCPLS'))
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
                        shutil.move(file, os.path.join(subjectsfolder, 'archive', 'HCPLS'))
                    elif archive == 'copy':
                        print "--> copying dataset to archive"
                        shutil.copy2(file, os.path.join(subjectsfolder, 'archive', 'HCPLS'))
                    elif archive == 'delete':
                        print "--> deleting dataset"
                        if os.path.isfile(file):
                            os.remove(file)
                        else:
                            shutil.rmtree(file)
                except:
                    print "==> %s of %s failed!" % (archive, file)

    # ---> mapping data to MNAP nii folder

    report = []
    for execute in ['map', 'clean']:
        for session in sessions[execute]:
            if session != 'hcpls':
                
                sparts    = session.split('_')
                subjectid = sparts.pop(0)
                sessionid = "_".join([e for e in sparts + [""] if e])
                info      = 'subject ' + subjectid
                if sessionid:
                    info += ", session " + sessionid

                try:
                    print
                    mapHCPLS2nii(os.path.join(subjectsfolder, session), overwrite)
                    report.append('%s completed ok' % (info))
                except ge.CommandFailed as e:
                    print "===> WARNING:\n     %s\n" % ("\n     ".join(e.report))
                    report.append('%s failed' % (info))
                    allOk = False

    print "\nFinal report\n============"
    for line in report:
        print line

    if not allOk:
        raise ge.CommandFailed("HCPLSImport", "Some actions failed", "Please check report!")



def processHCPLS(sfolder):
    '''
    '''

    if not os.path.exists(sfolder):
        raise ge.CommandFailed("processHCPLS", "No hcpls folder present!", "There is no hcpls data in session folder %s" % (sfolder), "Please import HCPLS data first!")

    session   = os.path.basename(os.path.dirname(sfolder))
    sparts    = session.split('_')
    subjectid = sparts.pop(0)
    sessionid = "_".join([e for e in sparts + [""] if e])

    # --- get a list of folders and process them

    dfolders = glob.glob(os.path.join(sfolder, '*'))

    # -- data: SE number, label, fodlerInfo, folderFiles, status
    checkedFolders = []

    for dfolder in dfolders:
        folderInfo   = {}
        folderFiles  = []
        senum        = 99
        missingFiles = []

        # --- get folder information

        folderTags  = os.path.basename(dfolder).split('_')
        folderLabel = folderTags.pop(0)
        for info in hcpls['folders'][folderLabel]['info']:
            if folderTags:
                folderInfo[info] = folderTags.pop(0)

        # --- Get files list

        files = glob.glob(os.path.join(dfolder, '*'))
        files = [e for e in files if e.endswith('.nii.gz')]

        sefile = [e for e in files if 'SpinEchoFieldMap' in e]
        if sefile:
            senum = int([e for e in sefile[0].split('_') if 'SpinEchoFieldMap' in e][0].replace('SpinEchoFieldMap', ""))

        for file in files:
            fileName = os.path.basename(file)
            fileParts = fileName.replace(session + "_", "").replace('.nii.gz', '').split('_')
            fileParts = ['SpinEchoFieldMap' if 'SpinEchoFieldMap' in e else e for e in fileParts]
            folderFiles.append({'rank': 0, 'path': file, 'name': fileName, 'parts': fileParts, 'json': None})

        # --- Check files

        check = list(hcpls['folders'][folderLabel]['check'])
        rank = 0
        for fcheck in check:
            rank += 1
            found = False
            for file in folderFiles:
                match = True
                for citem in fcheck:
                    if citem[0] == '-':
                        if citem[1:] in file['parts']:
                            match = False
                    else:
                        if citem not in file['parts']:
                            match = False
                if match:
                    file['rank'] = rank
                    found = True
                    break
            if not found:
                missingFiles.append([dfolder, fcheck])

        # --- Order files

        folderFiles.sort(key=lambda x: x['rank'])
        extraFiles = [e for e in folderFiles if e['rank'] == 0]
        folderFiles = [e for e in folderFiles if e['rank'] > 0]

        # --- Get json info

        for file in folderFiles:
            jfile = file['path'].replace('.nii.gz', '.json')
            if not os.path.exists(jfile):
                missingFiles.append([dfolder, os.path.basepath(jfile)])
            else:
                with open(jfile, 'r') as f:
                    jinf = json.load(f)
                file['json'] = jinf

        # --- finish up folder

        checkedFolders.append({'senum': senum, 'label': folderLabel, 'folderInfo': folderInfo, 'folderFiles': folderFiles, 'extraFiles': extraFiles, 'missingFiles': missingFiles})

    # sort folders

    checkedFolders.sort(key=lambda x: hcpls['folders']['order'][x['label']])
    checkedFolders.sort(key=lambda x: x['senum'])
                
    return checkedFolders
        


def mapHCPLS2nii(sfolder='.', overwrite='no', report=None):
    '''
    mapHCPLS2nii [sfolder='.'] [overwrite='no'] [report=<study>/info/hcpls/parameters.txt]

    USE
    ===

    The command is used to map data organized according to HCPLS specification,
    residing in `hcpls` session subfolder to `nii` folder as expected by MNAP
    functions. The command checks the imaging data and compiles a list in the
    following order:

    - anatomical images
    - fieldmap images
    - functional images
    - diffusion weighted images

    Once the list is compiled, the files are mapped to `nii` folder to files
    named by ordinal number of the image in the list. To save space, files are 
    not copied but rather hard links are created. Only image, bvec and bval 
    files are mapped from the `hcpls` to `nii` folder. The exact mapping is
    noted in file `hcpls2nii.log` that is saved to the `hcpls` folder. The 
    information on images is also compiled in `subject.txt` file that is 
    generated in the main session folder. For every image all the information
    present in the hcpls filename is listed.

    PARAMETERS
    ==========

    --sfolder    The base subject folder in which bids folder with data and
                 files for the session is present. [.]
    
    --overwrite  Parameter that specifes what should be done in cases where
                 there are existing data stored in `nii` folder. The options
                 are:

                 no      - do not overwrite the data, skip session
                 yes     - remove exising files in `nii` folder and redo the
                           mapping

                 The default option is 'no'. 

    --report     The path to the file that will hold the information about the
                 images that are relevant for HCP Pipelines. If not provided
                 it will default to 

    RESULTS
    =======

    After running the mapped nifti files will be in the `nii` subfolder, 
    named with sequential image number. `subject.txt` will be in the base 
    session folder and `hcpls2nii.log` will be in the `hcpls` folder.
    
    subject.txt file
    ----------------

    The subject.txt will be placed in the subject base folder. It will contain
    the information about the session id, subject id location of folders and a 
    list of created NIfTI images with their description.

    An example subject.txt file would be:

    id: 06_retest
    subject: 06
    hcpls: /Volumes/tigr/MBLab/fMRI/bidsTest/subjects/06_retest/hcpls
    raw_data: /Volumes/tigr/MBLab/fMRI/bidsTest/subjects/06_retest/nii
    hcp: /Volumes/tigr/MBLab/fMRI/bidsTest/subjects/06_retest/hcp
    
    01: T1w
    02: bold1:rest1
    03: bold2:rest1
    04: bold3:rest2
    05: bold4:rest2
    06: bold5:CARIT
    07: bold6:FACENAME
    08: bold7:VISMOTOR
    09: dwi

    For each of the listed images there will be a corresponding NIfTI file in
    the nii subfolder (e.g. 04.nii.gz for resting state 2 PA). 
    The generated subject.txt files form the basis for the following HCP and 
    other processing steps. `id` field will be set to the full session name,
    `subject` will be set to the text preceeding the first underscore (`_`) 
    character.

    hcpls2nii.log file
    -----------------

    The `hcpls2nii.log` provides the information about the date and time the
    files were mapped and the exact information about which specific file 
    from the `hcpls` folder was mapped to which file in the `nii` folder.

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

    Do note that as this command only performs file mapping and no image or 
    file processing, the best performance might be achieved by running on a 
    single node and a single core.

    CAVEATS AND MISSING FUNCTIONALITY
    =================================

    File order
    ----------

    The files are ordered according to best guess sorted primarily by modality. 
    This can be problematic for further HCP processing when information on the
    specific order is important.

    .bvec and .bval files
    ---------------------

    `.bvec` and `.bval` files are expected to be present along with dMRI files
    in each session folder. If they are present in another folder, they are 
    currently not mapped to the `.nii` folder.

    Image format
    ------------

    The function assumes that all the images are saved as `.nii.gz` files!


    EXAMPLE USE
    ===========

    gmri mapHCPLS2nii folder=. overwrite=yes

    ----------------
    Written by Grega Repovš

    Changelog
    2019-01-19 Grega Repovš
             - Initial version based on mapBIDS2nii
    '''

    sfolder = os.path.abspath(sfolder)
    hfolder = os.path.join(sfolder, 'hcpls')
    nfolder = os.path.join(sfolder, 'nii')

    # --- report file

    if report is None:
        study = gc.deduceFolders({'sfolder': sfolder})
        basefolder = study.get('basefolder')
        if basefolder:
            report = os.path.join(basefolder, 'info', 'hcpls', 'parameters.txt')
    
    if report:
        rout = open(report, 'a')
    else:
        rout = open(os.devnull, 'w')

    # --- session info

    session = os.path.basename(sfolder)
    sparts    = session.split('_')
    subjectid = sparts.pop(0)
    sessionid = "_".join([e for e in sparts + [""] if e])

    info = 'subject ' + subjectid
    if sessionid:
        info += ", session " + sessionid

    print 'info:', info

    splash = "Running mapHCPLS2nii for %s" % (info)
    print splash
    print "".join(['=' for e in range(len(splash))])


    splash = "\n\nParameters for " + info
    print >> rout, splash
    print >> rout, "".join(['=' for e in range(len(splash))])

    if overwrite not in ['yes', 'no']:
        raise ge.CommandError("mapHCPLS2nii", "Invalid option for overwrite specified", "%s is not a valid option for the overwrite parameter!" % (overwrite), "Please specify one of: yes, no!")

    # --- process hcpls folder

    hcplsData = processHCPLS(hfolder)
       
    if not hcplsData:
        raise ge.CommandFailed("mapHCPLS2nii", "No image files in hcpls folder!", "There are no image files in the hcpls folder [%s]" % (hfolder), "Please check your data!")

    # --- check for presence of nifti files

    if os.path.exists(nfolder):
        nfiles = glob.glob(os.path.join(nfolder, '*.nii*'))
        if nfiles > 0:
            if overwrite == 'no':
                raise ge.CommandFailed("mapHCPLS2nii", "Existing files present!", "There are existing files in the nii folder [%s]" % (nfolder), "Please check or set parameter 'overwrite' to yes!")
            else:
                shutil.rmtree(nfolder)
                os.makedirs(nfolder)
                print "--> cleaned nii folder, removed existing files"
    else:
        os.makedirs(nfolder)

    # --- open subject.txt file

    sfile = os.path.join(sfolder, 'subject_hcp.txt')
    if os.path.exists(sfile):
        if overwrite == 'yes':
            os.remove(sfile)
            print "--> removed existing subject.txt file"
        else:
            raise ge.CommandFailed("mapHCPLS2nii", "subject.txt file already present!", "A subject.txt file alredy exists [%s]" % (sfile), "Please check or set parameter 'overwrite' to 'yes' to rebuild it!")

    sout = open(sfile, 'w')
    print >> sout, 'id:', session
    print >> sout, 'subject:', subjectid
    print >> sout, 'hcpfs:', hfolder
    print >> sout, 'raw_data:', nfolder
    print >> sout, 'hcp:', os.path.join(sfolder, 'hcp')
    print >> sout
    print >> sout, 'hcpready: true'

    # --- open hcpfs2nii log file

    if overwrite == 'yes':
        mode = 'w'
    else:
        mode = 'a'

    bout  = open(os.path.join(hfolder, 'hcpfs2nii.log'), mode)
    print >> bout, "HCPFS to nii mapping report, executed on %s" % (datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))

    # --- map files

    allOk = True

    # hcplsData   = [{'senum':senum, 'label': folderLabel, 'folderInfo': folderInfo, 'folderFiles': folderFiles, 'extraFiles': extraFiles, 'missingFiles': missingFiles}]
    # folderFiles = [{'rank': 0, 'path': file, 'name': fileName, 'parts': fileParts, 'json': None}]

    mapped = []
    imgn   = 0 
    boldn  = 0    
    for folder in hcplsData:
        if folder['label'] in ['rfMRI', 'tfMRI']:
            boldn += 1

        for fileInfo in folder['folderFiles']:
            if fileInfo['name'] in mapped:
                continue            
            mapped.append(fileInfo['name'])

            imgn += 1
            tfile = os.path.join(nfolder, "%02d.nii.gz" % (imgn))
            status = moveLinkOrCopy(fileInfo['path'], tfile, action='link')

            if status:
                print "--> linked %02d.nii.gz <-- %s" % (imgn, fileInfo['name'])

                # --T1w and T2w
                if fileInfo['parts'][0] in ['T1w', 'T2w']:
                    print >> sout, "%02d: %-20s: %-30s: se(%d): DwellTime(%.10f)" % (imgn, fileInfo['parts'][0], "_".join(fileInfo['parts']), folder['senum'], fileInfo['json'].get('DwellTime', -9.))

                    print >> rout, "\n" + fileInfo['parts'][0]
                    print >> rout, "".join(['-' for e in range(len(fileInfo['parts'][0]))])
                    print >> rout, "%-25s : %.8f" % ("_hcp_%ssamplespacing" % (fileInfo['parts'][0][:2]), fileInfo['json'].get('DwellTime', 0))
                    print >> rout, "%-25s : %s" % ("_hcp_unwarpdir", unwarp[fileInfo['json'].get('ReadoutDirection', None)])

                # -- BOLDS
                elif fileInfo['parts'][0] in ['tfMRI', 'rfMRI']:
                    if 'SBRef' in fileInfo['parts']:
                        print >> sout, "%02d: %-20s: %-30s: se(%d): fenc(%s): EchoSpacing(%.10f)" % (imgn, "boldref%d:%s" % (boldn, fileInfo['parts'][1]), "_".join(fileInfo['parts']), folder['senum'], fileInfo['parts'][2], fileInfo['json'].get('EffectiveEchoSpacing', -9.))
                    else:
                        print >> sout, "%02d: %-20s: %-30s: se(%d): fenc(%s): EchoSpacing(%.10f)" % (imgn, "bold%d:%s" % (boldn, fileInfo['parts'][1]), "_".join(fileInfo['parts']), folder['senum'], fileInfo['parts'][2], fileInfo['json'].get('EffectiveEchoSpacing', -9.))

                    print >> rout, "\n" + "_".join(fileInfo['parts'])
                    print >> rout, "".join(['-' for e in range(len("_".join(fileInfo['parts'])))])
                    print >> rout, "%-25s : %.8f" % ("_hcp_bold_echospacing", fileInfo['json'].get('EffectiveEchoSpacing', -9.))
                    print >> rout, "%-25s : '%s=%s'" % ("_hcp_bold_unwarpdir", fileInfo['parts'][2], unwarp[fileInfo['json'].get('PhaseEncodingDirection', None)])

                # -- SE
                elif fileInfo['parts'][0] == 'SpinEchoFieldMap':
                    print >> sout, "%02d: %-20s: %-30s: se(%d): fenc(%s): EchoSpacing(%.10f)" % (imgn, "SE-FM-%s" % (fileInfo['parts'][1]), "_".join(fileInfo['parts']), folder['senum'], fileInfo['parts'][1], fileInfo['json'].get('EffectiveEchoSpacing', -9.))

                    print >> rout, "\n" + "_".join(fileInfo['parts'])
                    print >> rout, "".join(['-' for e in range(len("_".join(fileInfo['parts'])))])
                    print >> rout, "%-25s : %.8f" % ("_hcp_dwelltime", fileInfo['json'].get('EffectiveEchoSpacing', -9.))
                    print >> rout, "%-25s : '%s=%s'" % ("_hcp_seunwarpdir", fileInfo['parts'][1], unwarp[fileInfo['json'].get('PhaseEncodingDirection', None)])


                # -- dMRI
                elif fileInfo['parts'][0] == 'dMRI':
                    if 'SBRef' in fileInfo['parts']:
                        print >> sout, "%02d: %-20s: %-30s: fenc(%s): EchoSpacing(%.10f)" % (imgn, "DWIref:%s_%s" % (fileInfo['parts'][1], fileInfo['parts'][2]), "_".join(fileInfo['parts']), fileInfo['parts'][2], fileInfo['json'].get('EffectiveEchoSpacing', -0.009) * 1000.)
                    else:    
                        print >> sout, "%02d: %-20s: %-30s: fenc(%s): EchoSpacing(%.10f)" % (imgn, "DWI:%s_%s" % (fileInfo['parts'][1], fileInfo['parts'][2]), "_".join(fileInfo['parts']), fileInfo['parts'][2], fileInfo['json'].get('EffectiveEchoSpacing', -0.009) * 1000.)

                        print >> rout, "\n" + "_".join(fileInfo['parts'])
                        print >> rout, "".join(['-' for e in range(len("_".join(fileInfo['parts'])))])
                        print >> rout, "%-25s : %.8f" % ("_hcp_dwi_dwelltime", fileInfo['json'].get('EffectiveEchoSpacing', -0.009) * 1000.)
                        print >> rout, "%-25s : %d" % ("_hcp_dwi_PEdir", PEDir[fileInfo['parts'][2]])

                print >> bout, "%s => %s" % (fileInfo['path'], tfile)
            else:
                allOk = False
                print "==> ERROR: Linking failed: %02d.nii.gz <-- %s" % (imgn, fileInfo['name'])
                print >> bout, "FAILED: %s => %s" % (fileInfo['path'], tfile)

            status = True
            if 'dMRI' in fileInfo['parts'] and not 'SBRef' in fileInfo['parts']:
                status = moveLinkOrCopy(fileInfo['path'].replace('.nii.gz', '.bvec'), tfile.replace('.nii.gz', '.bvec'), action='link')
                status = moveLinkOrCopy(fileInfo['path'].replace('.nii.gz', '.bval'), tfile.replace('.nii.gz', '.bval'), action='link', status=status)
                if not status:
                    print "==> WARNING: bval/bvec files were not found and were not mapped for %02d.nii.gz!" % (imgn)
                    print "==> ERROR: bval/bvec files were not found and were not mapped: %02d.bval/.bvec <-- %s" % (imgn, fileInfo['name'].replace('.nii.gz', '.bval/.bvec'))
                    allOk = False
        
    sout.close()
    bout.close()

    if not allOk:
        raise ge.CommandFailed("mapHCPLS2nii", "Not all actions completed successfully!", "Some files for session %s were not mapped successfully!" % (session), "Please check logs and data!")

