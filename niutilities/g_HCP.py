#!/usr/bin/env python2.7
# encoding: utf-8
"""
g_HCP.py

Functions for preparing information and mapping images to a HCP preprocessing
compliant folder structure:

* setupHCP        ... maps the data to a hcp folder
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
import re

def setupHCP(sfolder=".", tfolder="hcp", sfile="subject_hcp.txt", check="yes", existing="add", filename='standard', folderstructure='hcpls', hcpsuffix=""):
    '''
    setupHCP [sfolder=.] [tfolder=hcp] [sfile=subject_hcp.txt] [check=yes] [existing=add] [filename='standard'] [folderstructure='hcpls'] [hcpsuffix=""]

    USE
    ===

    The command maps images from the sessions's nii folder into a folder
    structure that conforms to the naming conventions used in the HCP
    minimal preprocessing workflow. For the mapping to be correct, the
    command expects the source subject.txt file (sfile) to hold the relevant
    information on images. To save space, the images are not copied into the new
    folder structure but rather hard-links are created if possible.

    PARAMETERS
    ==========

    --sfolder           The base subject folder that contains the nifti images 
                        and subject.txt file. [.]
    --tfolder           The folder (within the base folder) to which the data is
                        to be mapped. [hcp]
    --sfile             The name of the source subject.txt file. 
                        [subject_hcp.txt]
    --check             Whether to check if session is marked ready for setting 
                        up hcp folder [yes].
    --existing          What to do if the hcp folder already exists? Options 
                        are:
                        abort -> abort setting up hcp folder
                        add   -> leave existing files and add new ones (default)
                        clear -> remove any exisiting files and redo hcp mapping
    --filename          How to name the bold files in the hcp structure. The 
                        default is to name them by their bold number ('standard') 
                        (e.g. BOLD_1), the alternative is to use their actual 
                        names ('original') (e.g. rfMRI_REST1_AP). ['standard']
    --folderstructure   Which HCP folder structure to use 'initial' or 'hcpls'. 
                        See below for details. ['hcpls'] 
    --hcpsuffix         Optional suffix to append to session id when creating 
                        session folder within the hcp folder. The final path
                        to HCP session is then: <tfolder>/<session id><hcpsuffix>.
                        []

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
                        phase encoding direction
    SE-FM-PA        ... Spin-echo fieldmap image recorded using the P-to-A
                        phase encoding direction
    SE-FM-LR        ... Spin-echo fieldmap image recorded using the L-to-R
                        phase encoding direction
    SE-FM-RL        ... Spin-echo fieldmap image recorded using the R-to-L
                        phase encoding direction
    DWI             ... Diffusion weighted image

    
    In addition to these parameters, it is also possible to optionally specify, 
    which spin-echo image to use for distortion correction, by adding 
    `:se(<number of se image>)` to the line, as well as phase encoding
    direction by adding `:phenc(<direction>)` to the line. In case of 
    spin-echo images themselves, the number denotes the number of the
    image itself.
    
    If these information are not provided the spin-echo image to use will be
    deduced based on the order of images, and phase encoding direction 
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
    07: bold1:WM        :BOLD 3mm 48 2.5s         : se(1) :phenc(AP)
    08: bold2:WM        :BOLD 3mm 48 2.5s         : se(1) :phenc(AP)
    09: bold3:WM        :BOLD 3mm 48 2.5s         : se(1) :phenc(AP)    
    10: bold4:WM        :BOLD 3mm 48 2.5s         : se(1) :phenc(AP)
    11: SE-FM-AP        :C-BOLD 3mm 48 2.5s FS-P  : se(2)
    12: SE-FM-PA        :C-BOLD 3mm 48 2.5s FS-A  : se(2)
    13: bold5:WM        :BOLD 3mm 48 2.5s         : se(2) :phenc(AP)
    14: bold6:WM        :BOLD 3mm 48 2.5s         : se(2) :phenc(AP)
    15: bold7:rest      :RSBOLD 3mm 48 2.5s       : se(2) :phenc(AP)
    16: bold8:rest      :RSBOLD 3mm 48 2.5s       : se(2) :phenc(PA)


    HCP folder structure version
    ----------------------------

    `version` parameter determines the HCP folder structure to use:

    * 'v1'  ... Unprocessed data is parallel to processed data, functional data
                folders have '_fncb' suffix and field map data folders have
                '_strc' tail.
    * 'v2'  ... Unprocessed data is a subfolder in the HCP session folder, 
                functional data folders and field map data folders do not have 
                the '_fncb' and '_strc' extensions, respectively.


    MULTIPLE SUBJECTS AND SCHEDULING
    ================================

    The command can be run for multiple sessions by specifying `sessions` and
    optionally `subjectsfolder` and `cores` parameters. In this case the command
    will be run for each of the specified sessions in the subjectsfolder
    (current directory by default). Optional `filter` and `subjid` parameters
    can be used to filter sessions or limit them to just specified id codes.
    (for more information see online documentation). `sfolder` will be filled in
    automatically as each sessions's folder. Commands will run in parallel by
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


    EXAMPLE USE
    ===========
    
    ```
    qunex setupHCP sfolder=OP316 sfile=subject.txt
    ```

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
    2019-04-25 Grega Repovš
             - Changed subjects to sessions
    2019-05-12 Grega Repovš
             - Reports an error if no file is found to be mapped
    2019-05-21 Grega Repovš
             - Added the 'boldnamekey' option
    2019-05-24 Grega Repovš
             - Added HCP folder structure specification
    2019-06-18 Grega Repovš
             - Updated documentation with multiple subject runs
    2020-04-08  Grega Repovš
             - Added hcpsuffix parameter
    '''

    print "Running setupHCP\n================"

    inf   = niutilities.g_core.readSubjectData(os.path.join(sfolder, sfile))[0][0]
    rawf  = inf.get('raw_data', None)
    sid   = inf['id']
    bolds = collections.defaultdict(dict)
    nT1w  = 0
    nT2w  = 0

    filename = filename == 'original'

    if folderstructure not in ['initial', 'hcpls']:
        raise ge.CommandFailed("setupHCP", "Unknown HCP folder structure", "The specified HCP folder structure is unknown: %s" % (folderstructure), "Please check the command!")

    if folderstructure == 'initial':
        fctail = '_fncb'
        fmtail = '_strc'
        basef = os.path.join(sfolder, tfolder, inf['id'] + hcpsuffix)
    else:
        fctail = ""
        fmtail = ""
        basef = os.path.join(sfolder, tfolder, inf['id'] + hcpsuffix, 'unprocessed')

    # --- Check session

    # -> is it HCP ready

    if inf.get('hcpready', 'no') != 'true':
        if check == 'yes':
            raise ge.CommandFailed("setupHCP", "Session not ready", "Session %s is not marked ready for HCP" % (sid), "Please check or run with check=no!")
        else:
            print "WARNING: Session %s is not marked ready for HCP. Processing anyway." % (sid)

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
    mapped = False

    for k in i:
        v = inf[k]
        if 'o' in v:
            orient = "_" + v['o']
        elif 'phenc' in v:
            orient = "_" + v['phenc']
        else:
            orient = ""
        if v['name'] == 'T1w':
            nT1w += 1
            if os.path.exists(os.path.join(rawf, k + ".nii.gz")):
                sfile = k + ".nii.gz"
            else:
                sfile = k + "-o.nii.gz"

            if filename and 'filename' in v:
                tfile = sid + "_" + v['filename'] + ".nii.gz"
            else:
                tfile = sid + "_T1w_MPR%d.nii.gz" % (nT1w)
            
            tfold = "T1w"

        elif v['name'] == "T2w":
            nT2w += 1
            if os.path.exists(os.path.join(rawf, k + ".nii.gz")):
                sfile = k + ".nii.gz"
            else:
                sfile = k + "-o.nii.gz"

            if filename and 'filename' in v:
                tfile = sid + "_" + v['filename'] + ".nii.gz"
            else:
                tfile = sid + "_T2w_SPC%d.nii.gz" % (nT2w)
            
            tfold = "T2w"

        elif v['name'] == "FM-GE":
            if 'fm' in v:
                fmnum = v['fm']
            else:
                fmnum = boldn
            sfile = k + ".nii.gz"

            if filename and 'filename' in v:
                tfile = sid + "_" + v['filename'] + ".nii.gz"
                tfold = v['filename'] + fmnum + fmtail
            else:
                tfile = sid + "_FieldMap_GE.nii.gz"
                tfold = "FieldMap" + fmnum + fmtail

        elif v['name'] == "FM-Magnitude":
            if 'fm' in v:
                fmnum = v['fm']
            else:
                fmnum = boldn
            sfile = k + ".nii.gz"

            if filename and 'filename' in v:
                tfile = sid + "_" + v['filename'] + ".nii.gz"
                tfold = v['filename'] + fmnum + fmtail
            else:
                tfile = sid + "_FieldMap_Magnitude.nii.gz"
                tfold = "FieldMap" + fmnum + fmtail

        elif v['name'] == "FM-Phase":
            if 'fm' in v:
                fmnum = v['fm']
            else:
                fmnum = boldn
            sfile = k + ".nii.gz"

            if filename and 'filename' in v:
                tfile = sid + "_" + v['filename'] + ".nii.gz"
                tfold = v['filename'] + fmnum + fmtail
            else:
                tfile = sid + "_FieldMap_Phase.nii.gz"
                tfold = "FieldMap" + fmnum + fmtail

        elif "boldref" in v['name']:
            boldn = v['name'][7:]
            sfile = k + ".nii.gz"

            if filename and 'filename' in v:
                tfile = sid + "_" + v['filename'] + ".nii.gz"
                tfold = v['filename'] + fctail
            else:
                tfile = sid + "_BOLD_" + boldn + orient + "_SBRef.nii.gz"
                tfold = "BOLD_" + boldn + orient + "_SBRef" + fctail
            bolds[boldn]["ref"] = sfile

        elif "bold" in v['name']:
            boldn = v['name'][4:]
            sfile = k + ".nii.gz"
            if filename and 'filename' in v:
                tfile = sid + "_" + v['filename'] + ".nii.gz"
                tfold = v['filename'] + fctail
            else:
                tfile = sid + "_BOLD_" + boldn + orient + ".nii.gz"
                tfold = "BOLD_" + boldn + orient + fctail
            bolds[boldn]["bold"] = sfile

        elif v['name'] == "SE-FM-AP":
            sfile = k + ".nii.gz"
            if 'se' in v:
                senum = v['se']
            else:
                senum = boldn

            if filename and 'filename' in v:
                tfile = sid + "_" + v['filename'] + ".nii.gz"
            else:
                tfile = sid + "_BOLD_AP_SB_SE.nii.gz"
            
            tfold = "SpinEchoFieldMap" + senum + fctail

        elif v['name'] == "SE-FM-PA":
            sfile = k + ".nii.gz"

            if 'se' in v:
                senum = v['se']
            else:
                senum = boldn

            if filename and 'filename' in v:
                tfile = sid + "_" + v['filename'] + ".nii.gz"
            else:
                tfile = sid + "_BOLD_PA_SB_SE.nii.gz"

            tfold = "SpinEchoFieldMap" + senum + fctail

        elif v['name'] == "SE-FM-LR":
            sfile = k + ".nii.gz"
            
            if 'se' in v:
                senum = v['se']
            else:
                senum = boldn

            if filename and 'filename' in v:
                tfile = sid + "_" + v['filename'] + ".nii.gz"
            else:
                tfile = sid + "_BOLD_LR_SB_SE.nii.gz"

            tfold = "SpinEchoFieldMap" + senum + fctail


        elif v['name'] == "SE-FM-RL":
            sfile = k + ".nii.gz"
            
            if 'se' in v:
                senum = v['se']
            else:
                senum = boldn

            if filename and 'filename' in v:
                tfile = sid + "_" + v['filename'] + ".nii.gz"
            else:
                tfile = sid + "_BOLD_RL_SB_SE.nii.gz"
            
            tfold = "SpinEchoFieldMap" + senum + fctail

        elif v['name'] == "DWI":
            sfile = [k + e for e in ['.nii.gz', '.bval', '.bvec']]

            if filename and 'filename' in v:
                tbase = "_".join([sid, v['filename'], v['task']])
            else:
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

            mapped = True

            if not os.path.exists(os.path.join(basef, tfold, tfile)):
                print " ---> linking %s to %s" % (sfile, tfile)
                os.link(os.path.join(rawf, sfile), os.path.join(basef, tfold, tfile))                
            else:
                print "  ... %s already exists" % (tfile)
                # print " ---> %s already exists, replacing it with %s " % (tfile, sfile)
                # os.remove(os.path.join(basef,tfold,tfile))
                # os.link(os.path.join(rawf, sfile), os.path.join(basef,tfold,tfile))
    
    if not mapped:
        raise ge.CommandFailed("setupHCP", "No files mapped", "No files were found to be mapped to the hcp folder [%s]!" % (sfolder), "Please check your data!")     

    return


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
    information necessary for correct mapping to a folder structure supporting
    HCP preprocessing.

    For all the sessions specified, the command checks for the presence of
    specified source file (sfile). If the source file is found, each sequence
    name is checked against the source specified in the mapping file (mapping),
    and the specified label is added. The results are then saved to the specified
    target file (tfile). The resulting session information files will have
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

    Note, that the old sequence names are preserved.


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

        images    = False
        hcpok     = False
        bold      = 0
        nlines    = []
        hasref    = False
        index     = 0
        se, fm    = 0, 0
        imgtrack  = {}
        setrack   = {}
        fmtrack   = {}
        pp_repl, p_repl = "", ""
        sepairs   = ['SE-FM-PA', 'SE-FM-AP', 'SE-FM-LR', 'SE-FM-RL']
        fmpairs   = ['FM-Magnitude', 'FM-Phase']
        sepattern = re.compile(r'SE-FM-PA|SE-FM-AP|SE-FM-LR|SE-FM-RL')
        fmpattern = re.compile(r'FM-Magnitude|FM-Phase') 
        for line in lines:
            e = line.split(':')
            sestr, fmstr = "", ""
            if len(e) > 1:
                if e[0].strip() == 'hcpready' and e[1].strip() == 'true':
                    hcpok = True
                if e[0].strip().isdigit():
                    if not images:
                        nlines.append('hcpready: true')
                        index += 1
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
                    elif sepattern.search(repl):
                        if sepattern.search(p_repl) is None:
                            se += 1
                            setrack.update({index: {'num': se}})
                        repl = repl.replace(repl, '%s' % (repl))
                    elif fmpattern.search(repl):
                        if fmpattern.search(p_repl) is None:
                            fm += 1
                            fmtrack.update({index: {'num': fm}})
                        repl = repl.replace(repl, '%s' % (repl))
                    elif repl in ['FM-GE']:
                        fm += 1
                        repl = repl.replace(repl, '%s' % (repl))
                    
                    explDef = any([re.search(r'se\(\d{1,2}\)|fm\(\d{1,2}\)',element) for element in e])
                    if re.search(r'(DWI:)', repl) is None and explDef is False:
                        if (se > 0) and (re.search(r'(?<!SE-)(FM-)', repl) is None):
                            sestr = ": se(%d)" % (se)
                        if (fm > 0) and (re.search(r'(SE-FM)', repl) is None):
                            fmstr = ": fm(%d)" % (fm)
                        imgtrack.update({index: {'type': repl, 'se': se, 'fm': fm}})

                    if (repl not in sepairs) and pp_repl not in sepairs and p_repl in sepairs:
                        print "WARNING: Spin-echo field map correction requires 2 files: SE-FM-PA and SE-FM-AP or SE-FM-LR and SE-FM-RL"
                    
                    if (repl not in fmpairs) and pp_repl not in fmpairs and p_repl in fmpairs:
                        print "WARNING: Field map correction (Siemens/Philips) requires 2 files: FM-Magnitude and FM-Phase"

                    pp_repl = p_repl
                    p_repl = repl

                    e[1] = " %-16s:%s%s%s" % (repl, oimg, sestr, fmstr)

                    nlines.append(":".join(e))
                else:
                    nlines.append(line)
            else:
                nlines.append(line)
            index += 1

        for item in imgtrack:
            if imgtrack[item]['fm'] == 0 and fmtrack and re.search(r'(SE-FM)', nlines[item]) is None:
                fmdist = [abs(ln-item) for ln in fmtrack.keys()]
                crspfm = min(fmdist)+item
                nlines[item] = nlines[item] + ": fm(%d)" % (fmtrack[crspfm]['num'])
            if imgtrack[item]['se'] == 0 and setrack and re.search(r'(?<!SE-)(FM-)', nlines[item]) is None:
                sedist = [abs(ln-item) for ln in setrack.keys()]
                crspse = min(sedist)+item
                nlines[item] = nlines[item] + ": se(%d)" % (setrack[crspse]['num'])    

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

