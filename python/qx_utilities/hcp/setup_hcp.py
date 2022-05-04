#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``setup_hcp.py``

Functions for preparing information and mapping images to a HCP preprocessing
compliant folder structure:

--setup_hcp      Maps the data to an hcp folder.

The commands are accessible from the terminal using the gmri utility.
"""

"""
Copyright (c) Grega Repovs and Jure Demsar.
All rights reserved.
"""

import os
import shutil
import collections
import general.exceptions as ge
import os.path
import general.core as gc

def setup_hcp(sourcefolder=".", targetfolder="hcp", sourcefile="session_hcp.txt", check="yes", existing="add", hcp_filename="automated", hcp_folderstructure="hcpls", hcp_suffix=""):
    """
    ``setup_hcp [sourcefolder=.] [targetfolder=hcp] [sourcefile=session_hcp.txt] [check=yes] [existing=add] [hcp_filename=automated] [hcp_folderstructure=hcpls] [hcp_suffix=""]``

    The command maps images from the sessions's nii folder into a folder
    structure that conforms to the naming conventions used in the HCP minimal
    preprocessing workflow.

    Parameters:
        --sourcefolder (str, default '.'):
            The base session folder that contains the nifti images and
            session.txt file.
        --targetfolder (str, default 'hcp'):
            The folder (within the base folder) to which the data is to be
            mapped.
        --sourcefile (str, default 'session_hcp.txt'):
            The name of the source session.txt file.
        --check (str, default 'yes'):
            Whether to check if session is marked ready for setting up hcp
            folder.
        --existing (str, default 'add'):
            What to do if the hcp folder already exists.
            Options are:

            - 'abort' ... abort setting up hcp folder
            - 'add'   ... leave existing files and add new ones
            - 'clear' ... remove any existing files and redo hcp mapping.

        --hcp_filename (str, default 'automated'):
            How to name the BOLD files once mapped into the hcp input folder
            structure. The default ('automated') will automatically name each
            file by their number (e.g. `BOLD_1`). The alternative ('userdefined')
            is to use the file names, which can be defined by the user prior to
            mapping (e.g. `rfMRI_REST1_AP`).
        --hcp_folderstructure (str, default 'hcpls'):
            Which HCP folder structure to use 'hcpya' or 'hcpls'.
        --hcp_suffix (str, default ''):
            Optional suffix to append to session id when creating session folder
            within the hcp folder. The final path to HCP session is then:
            `<targetfolder>/<session id><hcp_suffix>`.

    Notes:
        The command maps images from the sessions's nii folder into a folder
        structure that conforms to the naming conventions used in the HCP
        minimal preprocessing workflow. For the mapping to be correct, the
        command expects the source session.txt file (sourcefile) to hold the
        relevant information on images. To save space, the images are not
        copied into the new folder structure but rather hard-links are created
        if possible.

        Image definition:
            For the mapping to work, each MR to be mapped has to be marked with
            the appropriate image type in the source.txt file. The following
            file types are recognized and will be mapped correctly:

            --T1w
                T1 weighted high resolution structural image
            --T2w
                T2 weighted high resolution structural image
            --FM-GE
                Gradient echo field map image used for distortion correction
            --FM-Magnitude
                Field mapping magnitude image used for distortion correction
            --FM-Phase
                Field mapping phase image used for distortion correction
            --boldref
                Reference image for the following BOLD image, N should be added
                to the end of the boldref (boldref<N>)
            --bold
                BOLD image, N should be added to the end of bold (bold<N>)
            --SE-FM-AP
                Spin-echo fieldmap image recorded using the A-to-P phase
                encoding direction
            --SE-FM-PA
                Spin-echo fieldmap image recorded using the P-to-A phase
                encoding direction
            --SE-FM-LR
                Spin-echo fieldmap image recorded using the L-to-R phase
                encoding direction
            --SE-FM-RL
                Spin-echo fieldmap image recorded using the R-to-L phase
                encoding direction
            --DWI
                Diffusion weighted image.

            In addition to these parameters, it is also possible to optionally
            specify, which spin-echo image to use for distortion correction, by
            adding `:se(<number of se image>)` to the line, as well as phase
            encoding direction by adding `:phenc(<direction>)` to the line. In
            case of spin-echo images themselves, the number denotes the number
            of the image itself.

            If this information is not provided the spin-echo image to use
            will be deduced based on the order of images, and phase encoding
            direction will be taken as default from the relevant HCP processing
            parameters (e.g `--hcp_bold_unwarpdir='y'`).

            Do note that if you provide `se` information for the spin-echo
            image, you have to also provide it for all the images that are to
            use the spin-echo pair and vice-versa. If not, the matching
            algorithm will have incomplete information and might fail.

            Example definition::

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

            HCP folder structure version:
                `version` parameter determines the HCP folder structure to use:

                --'v1'
                    Unprocessed data is parallel to processed data, functional
                    data folders have `_fncb` suffix and field map data folders
                    have `_strc` tail.
                --'v2'
                    Unprocessed data is a subfolder in the HCP session folder,
                    functional data folders and field map data folders do not
                    have the `_fncb` and `_strc` extensions, respectively.

        Multiple sessions and scheduling:
            The command can be run for multiple sessions by specifying
            `sessions` and optionally `sessionsfolder` and `parsessions`
            parameters. In this case the command will be run for each of the
            specified sessions in the sessionsfolder (current directory by
            default). Optional `filter` and `sessionids` parameters can be used
            to filter sessions or limit them to just specified id codes. (for
            more information see online documentation). `sourcefolder` will be
            filled in automatically as each sessions's folder. Commands will
            run in parallel, where the degree of parallelism is determined by
            `parsessions` (1 by default).

            If `scheduler` parameter is set, the command will be run using the
            specified scheduler settings (see `qunex ?schedule` for more
            information). If set in combination with `sessions` parameter,
            sessions will be processed over multiple nodes, `parsessions`
            parameter specifying how many sessions to run per node. Optional
            `scheduler_environment`, `scheduler_workdir`, `scheduler_sleep`,
            and `nprocess` parameters can be set.

            Set optional `logfolder` parameter to specify where the processing
            logs should be stored. Otherwise the processor will make best
            guess, where the logs should go.

    Examples:
        >>> qunex setup_hcp sourcefolder=OP316 sourcefile=session.txt
    """

    print("Running setup_hcp\n================")

    inf   = gc.readSessionData(os.path.join(sourcefolder, sourcefile))[0][0]
    rawf  = inf.get('raw_data', None)
    sid   = inf['id']
    bolds = collections.defaultdict(dict)
    nT1w  = 0
    nT2w  = 0

    filename = hcp_filename == 'userdefined'

    if hcp_folderstructure not in ['hcpya', 'hcpls']:
        raise ge.CommandFailed("setup_hcp", "Unknown HCP folder structure", "The specified HCP folder structure is unknown: %s" % (hcp_folderstructure), "Please check the command!")

    if hcp_folderstructure == 'hcpya':
        fctail = '_fncb'
        fmtail = '_strc'
        basef = os.path.join(sourcefolder, targetfolder, inf['id'] + hcp_suffix)
    else:
        fctail = ""
        fmtail = ""
        basef = os.path.join(sourcefolder, targetfolder, inf['id'] + hcp_suffix, 'unprocessed')

    # --- Check session

    # -> is it HCP ready

    if inf.get('hcpready', 'no') != 'true':
        if check == 'yes':
            raise ge.CommandFailed("setup_hcp", "Session not ready", "Session %s is not marked ready for HCP" % (sid), "Please check or run with check=no!")
        else:
            print("WARNING: Session %s is not marked ready for HCP. Processing anyway." % (sid))

    # -> does raw data exist

    if rawf is None or not os.path.exists(rawf):
        raise ge.CommandFailed("setup_hcp", "Data folder does not exist", "raw_data folder for %s does not exist!" % (sid), "Please check specified path [%s]" % (rawf))

    print("===> Setting up HCP folder structure for %s\n" % (sid))

    # -> does hcp folder already exist?

    if os.path.exists(basef):
        if existing == 'clear':
            print(" ---> Base folder %s already exist! Clearing existing files and folders! " % (basef))
            shutil.rmtree(basef)
            os.makedirs(basef)
        elif existing == 'add':
            print(" ---> Base folder %s already exist! Adding any new files specified! " % (basef))
        else:
            raise ge.CommandFailed("setup_hcp", "Base folder exists", "Base folder %s already exist!" % (basef), "Please check or specify `exisiting` as `add` or `clear` for desired action!")
    else:
        print(" ---> Creating base folder %s " % (basef))
        os.makedirs(basef)

    i = [k for k, v in inf.items() if k.isdigit()]
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

        elif v['name'] in ["mbPCASLhr", "PCASLhr"]:
            sfile = [k + e for e in ['.nii.gz']]

            tbase = "_".join([sid, v['filename']])

            tfile = [tbase + e for e in ['.nii.gz']]
            tfold = "mbPCASLhr"

        else:
            print("  ... skipping %s %s [unknown sequence label, please check]" % (v['ima'], v['name']))
            continue

        if type(sfile) is not list:
            sfile = [sfile]
        if type(tfile) is not list:
            tfile = [tfile]

        for sfile, tfile in zip(list(sfile), list(tfile)):
            if not os.path.exists(os.path.join(rawf, sfile)):
                print(" ---> WARNING: Can not locate %s - skipping the file" % (os.path.join(rawf, sfile)))
                continue

            if not os.path.exists(os.path.join(basef, tfold)):
                print(" ---> creating subfolder", tfold)
                os.makedirs(os.path.join(basef, tfold))
            else:
                print("  ... %s subfolder already exists" % (tfold))

            mapped = True

            if not os.path.exists(os.path.join(basef, tfold, tfile)):
                # link the file
                print(" ---> linking %s to %s" % (sfile, tfile))
                gc.linkOrCopy(os.path.join(rawf, sfile), os.path.join(basef, tfold, tfile))

                # check if json exists
                sfile_json = sfile.split('.')[0] + '.json'
                tfile_json = tfile.split('.')[0] + '.json'
                json_path = os.path.join(rawf, sfile_json)
                # link or copy if it exists
                if os.path.exists(json_path):
                    gc.linkOrCopy(json_path, os.path.join(basef, tfold, tfile_json))
            else:
                print("  ... %s already exists" % (tfile))
    
    if not mapped:
        raise ge.CommandFailed("setup_hcp", "No files mapped", "No files were found to be mapped to the hcp folder [%s]!" % (sourcefolder), "Please check your data!")     

    return
