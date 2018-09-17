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
import glob
import datetime

bids = {
    'modalities': ['anat', 'func', 'dwi', 'fmap'],
    'optional': ['code', 'derivatives', 'stimuli', 'sourcedata'],
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

    else:
        if r is None:
            return False
        else:
            return (False, "%s%sERROR: %s could not be %sed, source file does not exist [%s]! " % (r, prefix, name, action, source))


def mapToMNAPBids(file, subjectsfolder, bidsname, sessions, existing, prefix):
    '''
    Identifies and returns the intended location of the file based on its name.
    '''

    folder   = os.path.join(os.path.dirname(subjectsfolder), 'info', 'bids', bidsname)
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
        else:
            sessions['map'].append(session)
        
    tfile = os.path.join(folder, optional, modality, os.path.basename(file))

    if os.path.exists(tfile):
        if session in sessions['append']:
            return False
        else:
            os.remove(tfile)
    elif not os.path.exists(os.path.dirname(tfile)):
        os.makedirs(os.path.dirname(tfile))

    return tfile



def BIDSImport(subjectsfolder=None, inbox=None, action='link', existing='skip', archive='move', bidsname=None):
    '''
    BIDSImport [subjectsfolder=.] [inbox=<subjectsfolder>/inbox/BIDS] [action=link] [existing=skip] [archive=move] [bidsname=<inbox folder name>]
    
    USE
    ===

    The command is used to map BIDS dataset to MNAP file structure. The command
    consists of two steps:

    First, the path as specified in the `inbox` parameter is inspected for a 
    BIDS compliant dataset. The path can point to either a folder with extracted
    BIDS dataset, a `.zip` or `.tar.gz` archive or a folder containing one or 
    more `.zip` or `.tar.gz` archives. In the initial step, each file found will
    be assigned either to a specific session or the overall study. 

    The files assigned to the study will be saved in the following location:

    <study folder>/info/bids/<bids dataset name>

    <bids dataset name> can be provided as a `bidsname` parameter to the command
    call. If not provided, the name will set to the name of the parent folder or
    the name of the compressed archive.

    The files identified as belonging to a specific subject will be mapped to: 
    
    <subjectsfolder>/<subject>_<session>/bids

    folder. The `<subject>_<session>` string will be used as the identifier for
    the session in all the following steps. If no session is specified in bids,
    `session` will be the same as `session`. If the folder for the session does
    not exist, it will be created.
    
    When the files are mapped, their filenames will be perserved and the correct
    folder structure will be reconstructed if it was previously flattened.

    Second, for each session separately, images from the `bids` folder are 
    mapped to the `nii` folder and appropriate `subject.txt` file is created.

    The second step is achieved by running mapBIDS2nii on each session folder.
    For detailed information about this step, please review its inline help.

    PARAMETERS
    ==========

    --subjectsfolder    The subjects folder where all the sessions are to be 
                        mapped to. It should be a folder within the 
                        <study folder>. [.]
    --inbox             The location of the BIDS dataset. It can be the dataset
                        top folder, a folder that contains the dataset, a 
                        compressed `.zip` or `.tar.gz` package or a folder that
                        contains a compressed package. 
                        [<subjectsfolder>/inbox/BIDS]
    --action            How to map the files to MNAP structure. One of :
                        - link: The files will be mapped by creating hard links
                                if possible, otherwise they will be copied.
                        - copy: The files will be copied.                    
                        - move: The files will be moved.
                        The default is 'link'
    --existing          The parameter specifies what should be done with 
                        data that already exists in the locations to which bids
                        data would be mapped to. Options are:
                        skip    - skip processing of the session
                        clean   - remove exising files in `nii` folder and redo 
                                  the mapping
                        append  - do not overwrite the existing files, just add 
                                  new files that would be generated
                        replace - leave the existing files in place and 
                                  overwrite those that would be generated anew
        
                        The default option is 'skip'. The use of options other 
                        than 'skip' and 'clean' is discouraged as with new data 
                        mapping can change and the results might be inconsistent!
    --archive           What to do with the files after they were mapped. 
                        Options are:
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
    --bidsname          The optional name of the BIDS dataset. Id not provided
                        it will be set to the inbox folder or compressed package
                        name.
    
    RESULTS
    =======

    After running the command the BIDS dataset will be mapped to the MNAP 
    structure with original session data in:

    <subjectsfolder>/<subject_session>/bids

    image files mapped to new names in:

    <subjectsfolder>/<subject_session>/nii

    description of the mapped files in:

    <subjectsfolder>/<subject_session>/subject.txt

    log of mapping in 

    <subjectsfolder>/<subject_session>/bids/bids2nii.log

    and study level bids files in:

    <study folder>/<info>/bids/<bidsname>

    CAVEATS AND MISSING FUNCTIONALITY
    =================================

    Please see mapBIDS2nii inline documentation!

    EXAMPLE USE
    ===========

    gmri BIDSImport subjectsfolder=myStudy existing=clean bidsname=swga

    ----------------
    Written by Grega Repovš

    Changelog
    2018-09-17 Grega Repovš
             - Initial version

    '''

    print "Running BIDSImport\n=================="

    if action not in ['link', 'copy', 'move']:
        ge.CommandError("BIDSImport", "Invalid action specified", "%s is not a valid action!" % (action), "Please specify one of: copy, link, move!")

    if existing not in ['skip', 'clean', 'append', 'replace']:
        ge.CommandError("BIDSImport", "Invalid option for existing files specified", "%s is not a valid option for existing files!" % (existing), "Please specify one of: skip, clean, append, replace!")

    if archive not in ['move', 'copy', 'delete']:
        ge.CommandError("BIDSImport", "Invalid dataset archive option", "%s is not a valid option for dataset archive option!" % (archive), "Please specify one of: move, copy, delete!")

    if subjectsfolder is None:
        subjectsfolder = os.path.abspath(".")

    if inbox is None:
        inbox = os.path.join(subjectsfolder, 'inbox', 'BIDS')
        bidsname = ""
    else:
        bidsname = os.path.basename(inbox)
        bidsname = re.sub('.zip$|.gz$', '', bidsname)
        bidsname = re.sub('.tar$', '', bidsname)

    sessions = {'list': [], 'clean': [], 'skip': [], 'replace': [], 'append': [], 'map': []}
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

    # ---> mapping data to subjects' folders

    print "--> mapping files to MNAP bids folders"

    for file in sourceFiles:
        if file.endswith('.zip'):
            print "    --> processing zip package [%s]" % (file)

            z = zipfile.ZipFile(file, 'r')
            for sf in z.infolist():
                if sf.file_size > 0:
                    tfile = mapToMNAPBids(sf.filename, subjectsfolder, bidsname, sessions, existing, "        ")
                    if tfile:
                        fdata = z.read(sf)
                        fout = open(tfile, 'wb')
                        fout.write(fdata)
                        fout.close()
            z.close()
            print "        -> done!"

        elif '.tar' in file:
            print "   --> processing tar package [%s]" % (file)

            tar = tarfile.open(file)
            for member in tar.getmembers():
                if member.isfile():
                    tfile = mapToMNAPBids(member.name, subjectsfolder, bidsname, sessions, existing, "        ")
                    if tfile:
                        fobj  = tar.extractfile(member)
                        fdata = fobj.read()
                        fobj.close()
                        fout = open(tfile, 'wb')
                        fout.write(fdata)
                        fout.close()
            tar.close()
            print "        -> done!"

        else:
            tfile = mapToMNAPBids(file, subjectsfolder, bidsname, sessions, existing, "    ")
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

    # ---> mapping data to MNAP nii folder

    report = []
    for execute in ['map', 'clean', 'replace', 'append']:
        for session in sessions[execute]:
            if session != 'bids':
                if execute == 'map':
                    do = 'skip'
                else:
                    do = execute
                print
                try:
                    mapBIDS2nii(os.path.join(subjectsfolder, session), do)
                    report.append('session %s completed ok' % (session))
                except ge.CommandFailed as e:
                    print "===> WARNING:\n     %s\n" % ("\n     ".join(e.report))
                    report.append('session %s failed' % (session))
                    allOk = False

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
    
        subject = [e.split('-')[1] for e in parts if 'sub-' in e] + ['']
        session = [e.split('-')[1] for e in parts if 'ses-' in e] + ['']
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
            info.update(dict([(i, part.split('-')[1]) for part in parts for i in bids[modality]['info'] if i in part]))
    
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
        


def mapBIDS2nii(sfolder='.', existing='skip'):
    '''
    mapBIDS2nii [sfolder='.'] [existing='skip']

    USE
    ===

    The command is used to map data organized according to BIDS specification,
    residing in `bids` session subfolder to `nii` folder as expected by MNAP
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

    --sfolder    The base subject folder in which bids folder with data and
                 files for the session is present. [.]
    --existing   Parameter that specifes what should be done in cases where
                 there are existing data stored in `nii` folder. The options
                 are:

                 skip    - skip processing
                 clean   - remove exising files in `nii` folder and redo the
                           mapping
                 append  - do not overwrite the existing files, just add new
                           files that would be generated
                 replace - leave the existing files in place and overwrite
                           those that would be generated anew

                 The default option is 'skip'. The use of options other than
                 'skip' and 'clean' is discouraged as with new data mapping
                 can change and the results might be inconsistent!

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
    This can be problematic for further HCP processing when different fieldmap
    files are used for different BOLD and structural files. In the a future 
    version the files will be organized so that fieldmaps will precede the 
    files to which they correspond, according to HCP processing expectations.

    Existing files
    --------------

    Due to their inherent problems, `append` and `replace` flags will most 
    probably be deprecated.

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

    gmri mapBIDS2nii folder=. existing=clean

    ----------------
    Written by Grega Repovš

    Changelog
    2018-09-17 Grega Repovš
             - Initial version

    '''

    sfolder = os.path.abspath(sfolder)
    bfolder = os.path.join(sfolder, 'bids')
    nfolder = os.path.join(sfolder, 'nii')

    session = os.path.basename(sfolder)
    subject = session.split('_')[0]

    splash = "Running mapBIDS2nii for session %s" % (session)
    print splash
    print "".join(['=' for e in range(len(splash))])

    if existing not in ['skip', 'clean', 'append', 'replace']:
        ge.CommandError("mapBIDS2nii", "Invalid option for existing files specified", "%s is not a valid option for existing files!" % (existing), "Please specify one of: skip, clean, append, replace!")

    # --- process bids folder

    bidsData = processBIDS(bfolder)
    bidsData = bidsData[session]

    if not bidsData['images']['list']:
        raise ge.CommandFailed("mapBIDS2nii", "No image files in bids folder!", "There are no image files in the bids folder [%s]" % (bfolder), "Please check your data!")

    # --- check for presence of nifti files

    if os.path.exists(nfolder):
        nfiles = glob.glob(os.path.join(nfolder, '*.nii*'))
        if nfiles > 0:
            if existing == 'skip':
                raise ge.CommandFailed("mapBIDS2nii", "Existing files present!", "There are existing files in the nii folder [%s]" % (nfolder), "Please check or set parameter 'existing' to clean, replace or append!")
            elif existing == 'clean':
                shutil.rmtree(nfolder)
                os.makedirs(nfolder)
                print "--> cleaned nii folder, removed existing files"
    else:
        os.makedirs(nfolder)

    # --- open subject.txt file

    sfile = os.path.join(sfolder, 'subject.txt')
    if os.path.exists(sfile):
        if existing in ['clean', 'append', 'replace']:
            os.remove(sfile)
            print "--> removed existing subject.txt file"
        else:
            raise ge.CommandFailed("mapBIDS2nii", "subject.txt file already present!", "A subject.txt file alredy exists [%s]" % (sfile), "Please check or set parameter 'existing' to clean, replace or append to rebuild it!")

    sout = open(sfile, 'w')
    print >> sout, 'id:', session
    print >> sout, 'subject:', subject
    print >> sout, 'bids:', bfolder
    print >> sout, 'hcp:', os.path.join(sfolder, 'hcp')
    print >> sout

    # --- open bids2nii log file

    if existing == 'clean':
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
        
        if os.path.exists(tfile):
            if existing == 'append':
                print >> sout, "%02d: %s" % (imgn, bidsData['images']['info'][image]['tag'])
                print >> bout, "%s => %s [file already existed, not mapped again]" % (bidsData['images']['info'][image]['filepath'], tfile)
                print "--> %02d.nii.gz already exists, skipping %s" % (imgn, bidsData['images']['info'][image]['filename'])
                continue
            elif existing == 'replace':
                os.remove(tfile)
                print "--> removed %02d.nii.gz " % (imgn)

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
            status = moveLinkOrCopy(bidsData['images']['info'][image]['filepath'].replace('.nii.gz', '.bvec'), tfile.replace('.nii.gz', '.bvec'), action='link')
            status = moveLinkOrCopy(bidsData['images']['info'][image]['filepath'].replace('.nii.gz', '.bval'), tfile.replace('.nii.gz', '.bval'), action='link', status=status)
            if not status:
                print "==> WARNING: bval/bvec files were not found and were not mapped for %02d.nii.gz!" % (imgn)
                print "==> ERROR: bval/bvec files were not found and were not mapped: %02d.bval/.bvec <-- %s" % (imgn, bidsData['images']['info'][image]['filename'].replace('.nii.gz', '.bval/.bvec'))
                allOk = False
    
    sout.close()
    bout.close()

    if not allOk:
        raise ge.CommandFailed("mapBIDS2nii", "Not all actions completed successfully!", "Some files for session %s were not mapped successfully!" % (session), "Please check logs and data!")

