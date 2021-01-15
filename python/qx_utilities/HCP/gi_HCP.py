#!/usr/bin/env python2.7
# encoding: utf-8
"""
``gi_HCP.py``

Functions for importing HCP style data into QuNex:

--importHCP      Maps HCP style data to QuNex structure.

The commands are accessible from the terminal using the gmri utility.
"""

"""
Copyright (c) Grega Repovs and Jure Demsar.
All rights reserved.
"""

import os
import os.path
import re
import shutil
import qx_utilities.g_exceptions as ge
import qx_utilities.g_core as gc
import zipfile
import tarfile
import glob
import datetime
import json
import ast


unwarp = {None: "Unknown", 'i': 'x', 'j': 'y', 'k': 'z', 'i-': 'x-', 'j-': 'y-', 'k-': 'z-'}
PEDir  = {None: "Unknown", "LR": 1, "RL": 1, "AP": 2, "PA": 2}
PEDirMap  = {'AP': 'j-', 'j-': 'AP', 'PA': 'j', 'j': 'PA', 'RL': 'i', 'i': 'RL', 'LR': 'i-', 'i-': 'LR'}


def mapToQUNEXcpls(file, sessionsfolder, hcplsname, sessions, overwrite, prefix, nameformat):
    '''
    Identifies and returns the intended location of the file based on its name.
    '''

    try:
        if sessionsfolder[-1] == '/':
            sessionsfolder = sessionsfolder[:-1]
    except:
        pass

    if '\\' in file:
        pathsep = "\\"
    else:
        pathsep = "/"

    # -- extract file info

    m = re.search(nameformat, file)
    try:
        subjid  = m.group('subject_id')
        session = m.group('session_name')
        data    = m.group('data').split(pathsep)
    except:
        print "ERROR: Could not parse file:", file
        return False

    if any([e[0] == '.' for e in [subjid, session] + data]):
        return False

    sessionid = subjid + "_" + session

    tfolder = os.path.join(sessionsfolder, sessionid, 'hcpls')
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
            elif not os.path.exists(os.path.join(tfolder, 'hcpfs2nii.log')):
                print prefix + "--> incomplete hcpls for session %s already exists: cleaning session" % (session)
                shutil.rmtree(tfolder)                    
                sessions['clean'].append(session)
            else:
                sessions['skip'].append(session)
                print prefix + "--> hcpls for session %s already exists: skipping session" % (session)
                print prefix + "    files previously mapped:"
                with open(os.path.join(tfolder, 'hcpfs2nii.log')) as hcplsLog:
                    for logline in hcplsLog:
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



def importHCP(sessionsfolder=None, inbox=None, sessions=None, action='link', overwrite='no', archive='move', hcplsname=None, nameformat=None, filesort=None):
    """
    ``importHCP [sessionsfolder=.] [inbox=<sessionsfolder>/inbox/HCPLS] [sessions=""] [action=link] [overwrite=no] [archive=move] [hcplsname=<inbox folder name>] [nameformat='(?P<subject_id>[^/]+?)_(?P<session_name>[^/]+?)/unprocessed/(?P<data>.*)'] [filesort=<file sorting option>]``
    
    Maps HCPLS data to the QuNex Suite file structure. 

    INPUTS
    ======

    --sessionsfolder    The sessions folder where all the sessions are to be 
                        mapped to. It should be a folder within the 
                        <study folder>. [.]

    --inbox             The location of the HCPLS dataset. It can be any of the
                        following: the HCPLS dataset top folder, a folder that 
                        contains the HCPLS dataset, a path to the compressed 
                        `.zip` or `.tar.gz` package that can contain a single 
                        session or a multi-session dataset, or a folder that 
                        contains a compressed package. For instance the user 
                        can specify "<path>/<hcpfs_file>.zip" or "<path>" to
                        a folder that contains multiple packages. The default 
                        location where the command will look for a HCPLS dataset
                        is [<sessionsfolder>/inbox/HCPLS]

    --sessions          An optional parameter that specifies a comma or pipe
                        separated list of sessions from the inbox folder to be 
                        processed. Regular expression patterns can be used. 
                        If provided, only packets or folders within the inbox 
                        that match the list of sessions will be processed. If 
                        `inbox` is a file `sessions` will not be applied. 
                        If `inbox` is a valid HCPLS datastructure folder, then 
                        the sessions will be matched against the 
                        `<subject id>[_<session name>]`.
                        Note: the session will match if the string is found
                        within the package name or the session id. So 
                        'HCPA' with match any zip file that contains string
                        'HCPA' or any session id that contains 'HCPA'!

    --action            How to map the files to QuNex structure. ['link']
                        The following actions are supported:
                        
                        - link (files will be mapped by creating hard links if 
                          possible, otherwise they will be copied)
                        - copy (files will be copied)                  
                        - move (files will be moved)

    --overwrite         The parameter specifies what should be done with 
                        data that already exists in the locations to which HCPLS
                        data would be mapped to. ['no'] Options are:

                        - no (do not overwrite the data and skip processing of 
                          the session)
                        - yes (remove exising files in `nii` folder and redo the
                          mapping) 

    --archive           What to do with the files after they were mapped. 
                        ['move'] Options are:

                        - leave (leave the specified archive where it is)
                        - move (move the specified archive to 
                          `<sessionsfolder>/archive/HCPLS`)
                        - copy (copy the specified archive to 
                          `<sessionsfolder>/archive/HCPLS`)
                        - delete (delete the archive after processing if no 
                          errors were identified)

                        Please note that there can be an
                        interaction with the `action` parameter. If files are
                        moved during action, they will be missing if `archive` 
                        is set to 'move' or 'copy'.

    --hcplsname         The optional name of the HCPLS dataset. If not provided
                        it will be set to the name of the inbox folder or the 
                        name of the compressed package.

    --nameformat        An optional parameter that contains a regular expression 
                        pattern with named fields used to extract the subject
                        and session information based on the file paths and 
                        names. The pattern has to return the groups named:

                        - subject_id (the id of the subject)
                        - session_name (the name of the session) 
                        - data (the rest of the path with the sequence related 
                          files)

                        The default is:
                        ``'(?P<subject_id>[^/]+?)_(?P<session_name>[^/]+?)/unprocessed/(?P<data>.*)'``

    --filesort          An optional parameter that specifies how the files should
                        be sorted before mapping to `nii` folder and inclusion 
                        in `session_hcp.txt`. The sorting is specified by a 
                        string of sort keys separated by '_'. [`name_type_se`] 
                        The available sort keys are:
       
                        - name (sort by the name of the file)
                        - type (sort by the type of the file (T1w, T2w, rfMRI, 
                          tfMRI, Diffusion))
                        - se (sort by the number of the related pair of the SE 
                          fieldmap images)
       
                        The files will be sorted in the order of the listed 
                        keys.

                        NOTE:

                        1. SE field map pair will always come before the first 
                           image in the sorted list that references it. 
                        2. Diffusion images will always be listed jointly in a 
                           fixed order.
    
    OUTPUTS
    =======

    After running the `importHCP` command the HCPLS dataset will be mapped 
    to the QuNex folder structure and image files will be prepared for further
    processing along with required metadata.

    - The original HCPL session-level data is stored in:

        ``<sessionsfolder>/<session>/hcpls``

    - Image files mapped to new names for QuNex are stored in:

        ``<sessionsfolder>/<session>/nii``

    - The full description of the mapped files is in:

        ``<sessionsfolder>/<session>/session.txt``

    - The output log of HCPLS mapping is in: 

        ``<sessionsfolder>/<session>/hcpls/hcpls2nii.log``

    USE
    ===
    
    The importHCP command consists of two steps:
    
    1. Mapping HCPLS dataset to QuNex Suite folder structure
    
        The `inbox` parameter specifies the location of the HCPLS dataset. This
        path is inspected for a HCPLS compliant dataset. The path can point to a
        folder with extracted HCPLS dataset, a `.zip` or `.tar.gz` archive or a 
        folder containing one or more `.zip` or `.tar.gz` archives. In the
        initial step, each file found will be assigned either to a specific 
        session. 

        <hcpls_dataset_name> can be provided as a `hcplsname` parameter to the
        command call. If `hcplsname` is not provided, the name will be set to
        the name of the parent folder or the name of the compressed archive.

        The files identified as belonging to a specific session will be mapped to 
        folder::
        
            <sessions_folder>/<subject>_<session>/hcpls

        The `<subject>_<session>` string will be used as the identifier for the 
        session in all the following steps. If the folder for the `session` 
        does not exist, it will be created.
        
        When the files are mapped, their filenames will be preserved.

    2. Mapping image files to QuNex Suite `nii` folder
    
        For each session separately, images from the `hcpls` folder are 
        mapped to the `nii` folder and appropriate `session.txt` file is created per
        standard QuNex specification.

        The second step is achieved by running `mapHCPLS2nii` on each session folder.
        This step is run automatically, but can be invoked independently if mapping 
        of HCPLS dataset to QuNex Suite folder structure was already completed. For 
        detailed information about this step, please review `mapHCPLS2nii` inline 
        help.

    Please see `mapHCPLS2nii` inline documentation!

    EXAMPLE CALL
    ============
    
    ::

        qunex importHCP sessionsfolder=myStudy/sessions inbox=HCPLS overwrite=yes hcplsname=hcpls
    """

    """
    ~~~~~~~~~~~~~~~~~~

    Change log

    2019-01-19 Grega Repovš
               Initial version adopted from importBIDS
    2019-01-19 Grega Repovš
               Initial version adopted from importBIDS
    2019-05-22 Grega Repovš
               Added nameformat as input
    2019-08-06 Grega Repovš
               Added sessions option
               Expanded documentation
    2020-03-24 Grega Repovš
               Addded file sorting parameter
    """

    print "Running importHCP\n=================="

    if action not in ['link', 'copy', 'move']:
        raise ge.CommandError("importHCP", "Invalid action specified", "%s is not a valid action!" % (action), "Please specify one of: copy, link, move!")

    if overwrite not in ['yes', 'no']:
        raise ge.CommandError("importHCP", "Invalid option for overwrite", "%s is not a valid option for overwrite parameter!" % (overwrite), "Please specify one of: yes, no!")

    if archive not in ['leave', 'move', 'copy', 'delete']:
        raise ge.CommandError("importHCP", "Invalid dataset archive option", "%s is not a valid option for dataset archive option!" % (archive), "Please specify one of: move, copy, delete!")

    if not filesort:
        filesort = "name_type_se"

    if any([e not in ['name', 'type', 'se'] for e in filesort.split("_")]):
        raise ge.CommandError("importHCP", "invalid filesort option", "%s is not a valid option for filesort parameter!" % (filesort), "Please only use keys: name, type, se!")

    if sessionsfolder is None:
        sessionsfolder = os.path.abspath(".")

    if inbox is None:
        inbox = os.path.join(sessionsfolder, 'inbox', 'HCPLS')
        hcplsname = ""
    else:
        hcplsname = os.path.basename(inbox)
        hcplsname = re.sub('.zip$|.gz$', '', hcplsname)
        hcplsname = re.sub('.tar$', '', hcplsname)

    if not nameformat:
        nameformat = r"(?P<subject_id>[^/]+?)_(?P<session_name>[^/]+?)/unprocessed/(?P<data>.*)"

    sessionsList = {'list': [], 'clean': [], 'skip': [], 'map': []}
    allOk        = True
    errors       = ""

    # ---> Check for folders
    if not os.path.exists(os.path.join(sessionsfolder, 'inbox', 'HCPLS')):
        os.makedirs(os.path.join(sessionsfolder, 'inbox', 'HCPLS'))
        print "--> creating inbox HCPLS folder"

    if not os.path.exists(os.path.join(sessionsfolder, 'archive', 'HCPLS')):
        os.makedirs(os.path.join(sessionsfolder, 'archive', 'HCPLS'))
        print "--> creating archive HCPLS folder"

    # ---> identification of files
    if sessions:
        sessions = [e.strip() for e in re.split(r' +|\| *|, *', sessions)]

    print "--> identifying files in %s" % (inbox)

    sourceFiles = []

    if os.path.exists(inbox):
        if os.path.isfile(inbox):
            sourceFiles = [inbox]
        elif os.path.isdir(inbox):
            for path, _, files in os.walk(inbox):
                for file in files:
                    filepath = os.path.join(path, file)
                    if sessions:
                        if any([file.endswith(e) for e in ['.zip', '.tar', '.tar.gz', '.tar.bz', '.tarz', '.tar.bzip2']]):
                            for session in sessions:
                                if re.search(session, file):
                                    sourceFiles.append(filepath)
                                    break
                        else:
                            m = re.search(nameformat, filepath)
                            try:
                                file_subjid  = m.group('subject_id')
                                file_session = m.group('session_name')
                                file_sessionid = "%s_%s" % (file_subjid, file_session)
                                for session in sessions:
                                    if re.search(session, file_sessionid):
                                        sourceFiles.append(filepath)
                                        break
                            except:
                                pass
                    else:
                        sourceFiles.append(filepath)
        else:
            raise ge.CommandFailed("importHCP", "Invalid inbox", "%s is neither a file or a folder!" % (inbox), "Please check your path!")
    else:
        raise ge.CommandFailed("importHCP", "Inbox does not exist", "The specified inbox [%s] does not exist!" % (inbox), "Please check your path!")

    if not sourceFiles:
        raise ge.CommandFailed("importHCP", "No files found", "No files were found to be processed at the specified inbox [%s]!" % (inbox), "Please check your path!")

    # ---> mapping data to sessions' folders
    print "--> mapping files to QuNex hcpls folders"

    for file in sourceFiles:
        if file.endswith('.zip'):
            print "    --> processing zip package [%s]" % (file)

            try:
                z = zipfile.ZipFile(file, 'r')
                for sf in z.infolist():
                    if sf.filename[-1] != '/':
                        tfile = mapToQUNEXcpls(sf.filename, sessionsfolder, hcplsname, sessionsList, overwrite, "        ", nameformat)
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
                allOk = False
                raise

        elif '.tar' in file:
            print "   --> processing tar package [%s]" % (file)

            try:
                tar = tarfile.open(file)
                for member in tar.getmembers():
                    if member.isfile():
                        tfile = mapToQUNEXcpls(member.name, sessionsfolder, hcplsname, sessionsList, overwrite, "        ", nameformat)
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
                allOk = False

        else:
            tfile = mapToQUNEXcpls(file, sessionsfolder, hcplsname, sessionsList, overwrite, "    ", nameformat)
            if tfile:
                status, msg = gc.moveLinkOrCopy(file, tfile, action, r="", prefix='    .. ')
                allOk = allOk and status
                if not status:
                    errors += msg

    # ---> archiving the dataset
    if errors:
        print "   ==> The following errors were encountered when mapping the files:"
        print errors
    else:
        if os.path.isfile(inbox) or not os.path.samefile(inbox, os.path.join(sessionsfolder, 'inbox', 'HCPLS')):
            try:
                if archive == 'move':
                    print "--> moving dataset to archive" 
                    shutil.move(inbox, os.path.join(sessionsfolder, 'archive', 'HCPLS'))
                elif archive == 'copy':
                    print "--> copying dataset to archive"
                    shutil.copy2(inbox, os.path.join(sessionsfolder, 'archive', 'HCPLS'))
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
                        shutil.move(file, os.path.join(sessionsfolder, 'archive', 'HCPLS'))
                    elif archive == 'copy':
                        print "--> copying dataset to archive"
                        shutil.copy2(file, os.path.join(sessionsfolder, 'archive', 'HCPLS'))
                    elif archive == 'delete':
                        print "--> deleting dataset"
                        if os.path.isfile(file):
                            os.remove(file)
                        else:
                            shutil.rmtree(file)
                except:
                    print "==> %s of %s failed!" % (archive, file)

    # ---> check status
    if not allOk:
        print "\nFinal report\n============"
        raise ge.CommandFailed("importHCP", "Processing of some packages failed", "Mapping of image files aborted.", "Please check report!")

    # ---> mapping data to QuNex nii folder
    report = []
    for execute in ['map', 'clean']:
        for session in sessionsList[execute]:
            if session != 'hcpls':
                
                sparts    = session.split('_')
                subjectid = sparts.pop(0)
                sessionid = "_".join([e for e in sparts + [""] if e])
                info      = 'subject ' + subjectid
                if sessionid:
                    info += ", session " + sessionid

                try:
                    print
                    nimg, nmapped = mapHCPLS2nii(os.path.join(sessionsfolder, session), overwrite, filesort=filesort)
                    if nimg == 0:
                        report.append('%s had no images found to be mapped' % (info))
                        allOk = False
                    elif nimg == nmapped:
                        report.append('%s completed ok. %d images mapped' % (info, nmapped))
                    else:
                        report.append('%s mapped incompletely [%d images, %d mapped]' % (info, nimg, nmapped))
                        allOk = False
                except ge.CommandFailed as e:
                    print "===> WARNING:\n     %s\n" % ("\n     ".join(e.report))
                    report.append('%s failed' % (info))
                    allOk = False

    print "\nFinal report\n============"
    for line in report:
        print line

    if not allOk:
        raise ge.CommandFailed("importHCP", "Some actions failed", "Please check report!")



def processHCPLS(sessionfolder, filesort):
    '''
    '''

    if not os.path.exists(sessionfolder):
        raise ge.CommandFailed("processHCPLS", "No hcpls folder present!", "There is no hcpls data in session folder %s" % (sessionfolder), "Please import HCPLS data first!")

    session   = os.path.basename(os.path.dirname(sessionfolder))
    #sparts    = session.split('_')
    #subjectid = sparts.pop(0)
    #sessionid = "_".join([e for e in sparts + [""] if e])

    # --- load HCPLS structure
    # template folder
    niuTemplateFolder = os.environ["NIUTemplateFolder"]
    hcplsStructure = os.path.join(niuTemplateFolder, "importHCP.txt")

    if not os.path.exists(hcplsStructure):
        raise ge.CommandFailed("processHCPLS", "No HCPLS structure file present!", "There is no HCPLS structure file %s" % (hcplsStructure), "Please check your QuNex installation")

    hcpls_file = open(hcplsStructure)
    content = hcpls_file.read()
    hcpls = ast.literal_eval(content)

    # --- get a list of folders and process them

    dfolders = glob.glob(os.path.join(sessionfolder, '*'))

    # -- data: SE number, label, fodlerInfo, folderFiles, status
    checkedFolders = []

    for dfolder in dfolders:
        folderInfo   = {}
        folderFiles  = []
        senum        = 0
        fmnum        = 0
        missingFiles = []

        # --- get folder information

        folderName  = os.path.basename(dfolder)
        folderTags  = folderName.split('_')
        folderLabel = folderTags.pop(0)
        if folderLabel not in hcpls['folders']:
            continue

        for info in hcpls['folders'][folderLabel]['info']:
            if folderTags:
                folderInfo[info] = folderTags.pop(0)

        # --- Get files list

        files = sorted(glob.glob(os.path.join(dfolder, '*')))
        files = [e for e in files if e.endswith('.nii.gz')]

        # --- Exclude files

        toExclude = ['InitialFrames']
        for exclude in toExclude:
            files = [e for e in files if exclude not in e] 

        # --- Proces spin echo files

        sefile = [e for e in files if 'SpinEchoFieldMap' in e]
        if sefile:
            senum = [e for e in sefile[0].split('_') if 'SpinEchoFieldMap' in e][0].replace('SpinEchoFieldMap', "")
            if senum:
                senum = int(senum)
            else:
                senum = 1

        # --- Proces fieldmap files

        fmfile = [e for e in files if 'FieldMap_Magnitude' in e]
        if fmfile:
            fmnum = [e for e in fmfile[0].split('_') if 'Magnitude' in e][0].replace('Magnitude', "").replace('.nii.gz', "")
            if fmnum:
                fmnum = int(fmnum)
            else:
                fmnum = 1

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
                missingFiles.append([dfolder, os.path.basename(jfile)])
                file['json'] = {}
            else:
                with open(jfile, 'r') as f:
                    jinf = json.load(f)
                file['json'] = jinf

        # --- finish up folder

        checkedFolders.append({'senum': senum, 'fmnum': fmnum, 'name': folderName, 'label': folderLabel, 'folderInfo': folderInfo, 'folderFiles': folderFiles, 'extraFiles': extraFiles, 'missingFiles': missingFiles})

    # sort folders

    print "--> filesort:", filesort

    for sortkey in filesort.split('_'):
        if sortkey == 'name':
            checkedFolders.sort(key=lambda x: x['name'])

        if sortkey == 'type':
            checkedFolders.sort(key=lambda x: hcpls['folders']['order'][x['label']])

        if sortkey == 'se':
            checkedFolders.sort(key=lambda x: x['senum'])
                
    return checkedFolders
        


def mapHCPLS2nii(sourcefolder='.', overwrite='no', report=None, filesort=None):
    """
    ``mapHCPLS2nii [sourcefolder='.'] [overwrite='no'] [report=<study>/info/hcpls/parameters.txt] [filesort=<file sorting option>]``

    Maps data organized according to HCPLS specification to `nii` folder
    structure as expected by QuNex functions.

    INPUTS
    ======

    --sourcefolder  The base session folder in which bids folder with data and
                    files for the session are present. [.]
    
    --overwrite     Parameter that specifes what should be done in cases where
                    there are existing data stored in `nii` folder. ['no'] The 
                    options are:

                    - no (do not overwrite the data, skip session)
                    - yes (remove exising files in `nii` folder and redo the
                      mapping)

    --report        The path to the file that will hold the information about the
                    images that are relevant for HCP Pipelines. If not provided
                    it will default to 

    --filesort      An optional parameter that specifies how the files should
                    be sorted before mapping to `nii` folder and inclusion in 
                    `session_hcp.txt`. The sorting is specified by a string of
                    sort keys separated by '_'. The available sort keys are:
   
                    - name (sort by the name of the file)
                    - type (sort by the type of the file (T1w, T2w, rfMRI, 
                      tfMRI, Diffusion)
                    - se (sort by the number of the related pair of the SE 
                      fieldmap images)
   
                    The files will be sorted in the order of the listed keys.
                    The default is: "name_type_se".
   
                    NOTE: 
                    
                    - SE field map pair will allways come before the first image
                      in the sorted list that references it. 
                    - Diffusion images will always be listed jointly in a fixed 
                      order.

    OUTPUTS
    =======

    After running the mapped nifti files will be in the `nii` subfolder, 
    named with sequential image number. `session.txt` will be in the base 
    session folder and `hcpls2nii.log` will be in the `hcpls` folder.
    
    session.txt file
    ----------------

    The session.txt will be placed in the session base folder. It will contain
    the information about the session id, subject id location of folders and a 
    list of created NIfTI images with their description.

    An example session.txt file would be::

        id: 06_retest
        subject: 06
        hcpls: /Volumes/tigr/MBLab/fMRI/bidsTest/sessions/06_retest/hcpls
        raw_data: /Volumes/tigr/MBLab/fMRI/bidsTest/sessions/06_retest/nii
        hcp: /Volumes/tigr/MBLab/fMRI/bidsTest/sessions/06_retest/hcp
        
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
    The generated session.txt files form the basis for the following HCP and 
    other processing steps. `id` field will be set to the full session name,
    `subject` will be set to the text preceeding the first underscore (`_`) 
    character.

    hcpls2nii.log file
    ------------------

    The `hcpls2nii.log` provides the information about the date and time the
    files were mapped and the exact information about which specific file 
    from the `hcpls` folder was mapped to which file in the `nii` folder.

    USE
    ===

    The command is used to map data organized according to HCPLS specification,
    residing in `hcpls` session subfolder to `nii` folder as expected by QuNex
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
    information on images is also compiled in `session.txt` file that is 
    generated in the main session folder. For every image all the information
    present in the hcpls filename is listed.

    Multiple sessions and scheduling
    --------------------------------

    The command can be run for multiple sessions by specifying `sessions` and
    optionally `sessionsfolder` and `parsessions` parameters. In this case the
    command will be run for each of the specified sessions in the sessionsfolder
    (current directory by default). Optional `filter` and `sessionids` parameters
    can be used to filter sessions or limit them to just specified id codes.
    (for more information see online documentation). `sourcefolder` will be filled
    in automatically as each sessions's folder. Commands will run in parallel, where
    the degree of parallelism is determined by `parsessions` (1 by default).

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

    .bvec and .bval files
    ~~~~~~~~~~~~~~~~~~~~~

    `.bvec` and `.bval` files are expected to be present along with dMRI files
    in each session folder. If they are present in another folder, they are 
    currently not mapped to the `.nii` folder.

    Image format
    ~~~~~~~~~~~~

    The function assumes that all the images are saved as `.nii.gz` files!

    EXAMPLE USE
    ===========
    
    ::

        qunex mapHCPLS2nii folder=. overwrite=yes

    ::

        qunex mapHCPLS2nii \\
          --sessionsfolder="/data/my_study/sessions" \\
          --sessions="AP*" \\
          --overwrite=yes
    """

    """
    ~~~~~~~~~~~~~~~~~~

    Change log

    2019-01-19 Grega Repovš
               Initial version based on mapBIDS2nii
    2019-04-25 Grega Repovš
               Changed subjects to sessions
    2019-05-22 Grega Repovš
               Added boldname to output
    2019-06-01 Grega Repovš
               Returns statistics
    2019-06-22 Grega Repovš
               Added multiple sessions example
    2019-09-21 Jure Demšar
               Filename (previously boldname) is now used in all sequences
    2020-03-24 Grega Repovš
               Addded file sorting parameter
    """

    if not filesort:
        filesort = "name_type_se"

    if any([e not in ['name', 'type', 'se'] for e in filesort.split("_")]):
        raise ge.CommandError("importHCP", "invalid filesort option", "%s is not a valid option for filesort parameter!" % (filesort), "Please only use keys: name, type, se!")

    sfolder = os.path.abspath(sourcefolder)
    hfolder = os.path.join(sourcefolder, 'hcpls')
    nfolder = os.path.join(sourcefolder, 'nii')

    # --- report file

    if report is None:
        study = gc.deduceFolders({'sourcefolder': sfolder})
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

    hcplsData = processHCPLS(hfolder, filesort)
       
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

    # --- create session.txt file
    sout = gc.createSessionFile("mapHCPLS2nii", sfolder, session, subjectid, overwrite)

    # --- create session_hcp.txt file
    sfile = os.path.join(sfolder, 'session_hcp.txt')
    if os.path.exists(sfile):
        if overwrite == 'yes':
            os.remove(sfile)
            print "--> removed existing session_hcp.txt file"
        else:
            raise ge.CommandFailed("mapHCPLS2nii", "session_hcp.txt file already present!", "A session_hcp.txt file alredy exists [%s]" % (sfile), "Please check or set parameter 'overwrite' to 'yes' to rebuild it!")

    sout_hcp = open(sfile, 'w')
    print >> sout_hcp, 'id:', session
    print >> sout_hcp, 'subject:', subjectid
    print >> sout_hcp, 'hcpfs:', hfolder
    print >> sout_hcp, 'raw_data:', nfolder
    print >> sout_hcp, 'hcp:', os.path.join(sfolder, 'hcp')
    print >> sout_hcp
    print >> sout_hcp, 'hcpready: true'

    # --- open hcpfs2nii log file

    if overwrite == 'yes':
        mode = 'w'
    else:
        mode = 'a'

    bout  = open(os.path.join(hfolder, 'hcpls2nii.log'), mode)
    print >> bout, "HCPLS to nii mapping report, executed on %s" % (datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))

    # --- map files

    allOk = True

    # hcplsData   = [{'senum':senum, 'label': folderLabel, 'folderInfo': folderInfo, 'folderFiles': folderFiles, 'extraFiles': extraFiles, 'missingFiles': missingFiles}]
    # folderFiles = [{'rank': 0, 'path': file, 'name': fileName, 'parts': fileParts, 'json': None}]

    mapped  = []
    imgn    = 0 
    boldn   = 0
    nmapped = 0
    firstImage = True


    for folder in hcplsData:
        if folder['label'] in ['rfMRI', 'tfMRI']:
            boldn += 1

        for fileInfo in folder['folderFiles']:
            if fileInfo['name'] in mapped:
                continue            
            mapped.append(fileInfo['name'])

            imgn += 1
            tfile = os.path.join(nfolder, "%02d.nii.gz" % (imgn))
            status = gc.moveLinkOrCopy(fileInfo['path'], tfile, action='link')

            if status:
                nmapped += 1
                print "--> linked %02d.nii.gz <-- %s" % (imgn, fileInfo['name'])

                # -- Institution and device information

                if firstImage:
                    deviceInfo  = "%s|%s|%s" % (fileInfo['json'].get('Manufacturer', "NA"), fileInfo['json'].get('ManufacturersModelName', "NA"), fileInfo['json'].get('DeviceSerialNumber', "NA"))
                    institution = fileInfo['json'].get('InstitutionName', "NA")
                    out = "\ninstitution: %s\ndevice: %s\n" % (institution, deviceInfo)
                    print >> sout, out
                    print >> sout_hcp, out
                    firstImage = False

                # --T1w and T2w
                if fileInfo['parts'][0] in ['T1w', 'T2w']:
                    # -29s fol alignment purposes (output generation is slightly different with T1w and T2w)
                    out = "%02d: %-20s: %-29s" % (imgn, fileInfo['parts'][0], "_".join(fileInfo['parts']))
                    print >> sout, out,
                    print >> sout_hcp, out,
                    if folder['senum']:
                        out = ": se(%d)" % (folder['senum'])
                        print >> sout, out,
                        print >> sout_hcp, out,
                    if folder['fmnum']:
                        out = ": fm(%d)" % (folder['fmnum'])
                        print >> sout, out,
                        print >> sout_hcp, out,
                    echospacing = 0
                    if fileInfo['json'].get('DwellTime', None):
                        echospacing = fileInfo['json'].get('DwellTime')
                        out = ": DwellTime(%.10f)" % (echospacing)
                        print >> sout, out,
                        print >> sout_hcp, out,
                    elif fileInfo['json'].get('EchoSpacing', None):
                        echospacing = fileInfo['json'].get('EchoSpacing')
                        out = ": EchoSpacing(%.10f)" % (echospacing)
                        print >> sout, out,
                        print >> sout_hcp, out,
                    if fileInfo['json'].get('ReadoutDirection', None):
                        out = ": UnwarpDir(%s)" % (unwarp[fileInfo['json'].get('ReadoutDirection')])
                        print >> sout, out,
                        print >> sout_hcp, out,

                    # add filename
                    out = ": filename(%s)" % "_".join(fileInfo['parts'])
                    print >> sout, out
                    print >> sout_hcp, out

                    print >> rout, "\n" + fileInfo['parts'][0]
                    print >> rout, "".join(['-' for e in range(len(fileInfo['parts'][0]))])
                    print >> rout, "%-25s : %.8f" % ("_hcp_%ssamplespacing" % (fileInfo['parts'][0][:2]), echospacing)
                    print >> rout, "%-25s : %s" % ("_hcp_unwarpdir", unwarp[fileInfo['json'].get('ReadoutDirection', None)])

                # -- BOLDS
                elif fileInfo['parts'][0] in ['tfMRI', 'rfMRI']:

                    phenc = fileInfo['json'].get('PhaseEncodingDirection', None)
                    if phenc:
                        phenc = PEDirMap.get(phenc, 'NA')
                    else:
                        phenc = fileInfo['parts'][2]

                    fmstr = ""
                    if folder['fmnum']:
                        fmstr += ": fm(%d)" % (folder['fmnum'])
                    if folder['senum']:
                        fmstr += ": se(%d)" % (folder['senum'])

                    if 'SBRef' in fileInfo['parts']:
                        out = "%02d: %-20s: %-30s%s : phenc(%s)" % (imgn, "boldref%d:%s" % (boldn, fileInfo['parts'][1]), "_".join(fileInfo['parts']), fmstr, phenc)
                        print >> sout, out,
                        print >> sout_hcp, out,
                    else:
                        out = "%02d: %-20s: %-30s%s : phenc(%s)" % (imgn, "bold%d:%s" % (boldn, fileInfo['parts'][1]), "_".join(fileInfo['parts']), fmstr, phenc)
                        print >> sout, out,
                        print >> sout_hcp, out,

                    if fileInfo['json'].get('EffectiveEchoSpacing', None):
                        out = ": EchoSpacing(%.10f)" % (fileInfo['json'].get('EffectiveEchoSpacing'))
                        print >> sout, out,
                        print >> sout_hcp, out,

                    # add filename
                    out = ": filename(%s)" % "_".join(fileInfo['parts'])
                    print >> sout, out
                    print >> sout_hcp, out

                    print >> rout, "\n" + "_".join(fileInfo['parts'])
                    print >> rout, "".join(['-' for e in range(len("_".join(fileInfo['parts'])))])
                    print >> rout, "%-25s : %.8f" % ("_hcp_bold_echospacing", fileInfo['json'].get('EffectiveEchoSpacing', -9.))
                    print >> rout, "%-25s : '%s=%s'" % ("_hcp_bold_unwarpdir", phenc, unwarp[fileInfo['json'].get('PhaseEncodingDirection', None)])

                # -- SE
                elif fileInfo['parts'][0] == 'SpinEchoFieldMap':
                    phenc = fileInfo['json'].get('PhaseEncodingDirection', None)
                    if phenc:
                        phenc = PEDirMap.get(phenc, 'NA')
                    else:
                        phenc = [e for e in ['LR', 'RL', 'AP', 'PA'] if e in fileInfo['parts']] + ['NA']
                        phenc = phenc[0]                        
                    
                    if phenc == 'NA':                          
                        print "==> WARNING: Could not identify phase encoding direction for %d.nii.gz [%s]!" % (imgn, fileInfo['name'])
                        phencstr = ""
                    else:
                        phencstr = ": phenc(%s) " % (phenc)

                    if fileInfo['json'].get('EffectiveEchoSpacing', None):
                        echospstr = ": EchoSpacing(%.10f) " % (fileInfo['json'].get('EffectiveEchoSpacing'))
                    else:
                        echospstr = ""

                    out = "%02d: %-20s: %-30s: se(%d) %s%s: filename(%s)" % (imgn, "SE-FM-%s" % (fileInfo['parts'][1]), "_".join(fileInfo['parts']), folder['senum'], phencstr, echospstr, "_".join(fileInfo['parts']))
                    print >> sout, out
                    print >> sout_hcp, out

                    print >> rout, "\n" + "_".join(fileInfo['parts'])
                    print >> rout, "".join(['-' for e in range(len("_".join(fileInfo['parts'])))])
                    print >> rout, "%-25s : %.8f" % ("_hcp_seechospacing", fileInfo['json'].get('EffectiveEchoSpacing', -9.))
                    print >> rout, "%-25s : '%s=%s'" % ("_hcp_seunwarpdir", phenc, unwarp[fileInfo['json'].get('PhaseEncodingDirection', None)])

                # -- Siemens fieldmap
                elif fileInfo['parts'][0] == 'FieldMap':
                    out = "%02d: %-20s: %-30s: fm(%d) : filename(%s)" % (imgn, "FM-%s" % (fileInfo['parts'][1]), "_".join(fileInfo['parts']), folder['fmnum'], "_".join(fileInfo['parts']))
                    print >> sout, out
                    print >> sout_hcp, out

                    print >> rout, "\n" + "_".join(fileInfo['parts'])
                    print >> rout, "".join(['-' for e in range(len("_".join(fileInfo['parts'])))])

                # -- dMRI
                elif fileInfo['parts'][0] in ['dMRI', 'DWI']:
                    phenc = fileInfo['json'].get('PhaseEncodingDirection', None)
                    if phenc:
                        phenc = PEDirMap.get(phenc, 'NA')
                    else:
                        phenc = [e for e in ['LR', 'RL', 'AP', 'PA'] if e in fileInfo['parts']] + ['NA']
                        phenc = phenc[0]
                    
                    if phenc == 'NA':                          
                        print "==> WARNING: Could not identify phase encoding direction for %d.nii.gz [%s]!" % (imgn, fileInfo['name'])
                        phencstr = ""
                    else:
                        phencstr = ": phenc(%s)" % (phenc)

                    if 'SBRef' in fileInfo['parts']:
                        out = "%02d: %-20s: %-30s%s" % (imgn, "DWIref:%s_%s" % (fileInfo['parts'][1], phenc), "_".join(fileInfo['parts']), phencstr)
                        print >> sout, out,
                        print >> sout_hcp, out,
                        if fileInfo['json'].get('EffectiveEchoSpacing', None):
                            print >> sout_hcp, ": EchoSpacing(%.10f)" % (fileInfo['json'].get('EffectiveEchoSpacing', -0.009) * 1000.),

                    else:
                        out = "%02d: %-20s: %-30s: phenc(%s)" % (imgn, "DWI:%s_%s" % (fileInfo['parts'][1], phenc), "_".join(fileInfo['parts']), phenc)
                        print >> sout, out,
                        print >> sout_hcp, out,
                        if fileInfo['json'].get('EffectiveEchoSpacing', None):
                            out = ": EchoSpacing(%.10f)" % (fileInfo['json'].get('EffectiveEchoSpacing', -0.009) * 1000.)
                            print >> sout, out,
                            print >> sout_hcp, out,

                        print >> rout, "\n" + "_".join(fileInfo['parts'])
                        print >> rout, "".join(['-' for e in range(len("_".join(fileInfo['parts'])))])
                        print >> rout, "%-25s : %.8f" % ("_hcp_dwi_echospacing", fileInfo['json'].get('EffectiveEchoSpacing', -0.009) * 1000.)

                    # add filename
                    out = ": filename(%s)" % "_".join(fileInfo['parts'])
                    print >> sout, out
                    print >> sout_hcp, out

                print >> bout, "%s => %s" % (fileInfo['path'], tfile)
            else:
                allOk = False
                print "==> ERROR: Linking failed: %02d.nii.gz <-- %s" % (imgn, fileInfo['name'])
                print >> bout, "FAILED: %s => %s" % (fileInfo['path'], tfile)

            status = True
            if ('dMRI' in fileInfo['parts'] or 'DWI' in fileInfo['parts']) and not 'SBRef' in fileInfo['parts']:
                statusA = gc.moveLinkOrCopy(fileInfo['path'].replace('.nii.gz', '.bvec'), tfile.replace('.nii.gz', '.bvec'), action='link')
                if statusA:
                    print >> bout, "%s => %s" % (fileInfo['path'].replace('.nii.gz', '.bvec'), tfile.replace('.nii.gz', '.bvec'))                    

                statusB = gc.moveLinkOrCopy(fileInfo['path'].replace('.nii.gz', '.bval'), tfile.replace('.nii.gz', '.bval'), action='link')
                if statusB:
                    print >> bout, "%s => %s" % (fileInfo['path'].replace('.nii.gz', '.bval'), tfile.replace('.nii.gz', '.bval'))                    

                if not all([statusA, statusB]):
                    print "==> WARNING: bval/bvec files were not found and were not mapped for %02d.nii.gz!" % (imgn)
                    print "==> ERROR: bval/bvec files were not found and were not mapped: %02d.bval/.bvec <-- %s" % (imgn, fileInfo['name'].replace('.nii.gz', '.bval/.bvec'))
                    allOk = False

    sout.close()
    sout_hcp.close()
    bout.close()

    if not allOk:
        raise ge.CommandFailed("mapHCPLS2nii", "Not all actions completed successfully!", "Some files for session %s were not mapped successfully!" % (session), "Please check logs and data!")

    return imgn, nmapped
