#!/usr/bin/env python2.7
# encoding: utf-8
"""
This file holds code for support functions for image preprocessing and analysis.
It consists of functions:

* createBoldList   ... creates a list with paths to each session's BOLD files
* createConcList   ... creates a list with paths to each session's conc files
* listSessionInfo  ... lists session data stored in batch.txt file

All the functions are part of the processing suite. They should be called
from the command line using `qunex` command. Help is available through:

`qunex ?<command>` for command specific help
`qunex -o` for a list of relevant arguments and options

Created by Grega Repovs on 2016-12-17.
Code split from dofcMRIp_core gCodeP/preprocess codebase.
Copyright (c) Grega Repovs. All rights reserved.
"""


from gp_core import *
from g_img import *
import os
import re
from datetime import datetime


def createBoldList(sinfo, options, overwrite=False, thread=0):
    """
    createBoldList - documentation not yet available.
    """
    bfile = open(os.path.join(options['sessionsfolder'], 'boldlist' + options['bold_prefix'] + '.list'), 'w')
    bsearch = re.compile('bold([0-9]+)')

    for session in sinfo:
        bolds = []
        for (k, v) in session.iteritems():
            if k.isdigit():
                bnum = bsearch.match(v['name'])
                if bnum:
                    if v['task'] in options['bolds'].split("|"):
                        bolds.append(v['name'])
        if len(bolds) > 0:
            f = getFileNames(session, options)
            print >> bfile, "    session id:%s" % (session['id'])
            print >> bfile, "    roi:%s" % (os.path.abspath(f['fs_aparc_bold']))
            for bold in bolds:
                f = getBOLDFileNames(session, boldname=bold, options=options)
                print >> bfile, "    file:%s" % (os.path.abspath(f['bold_final']))

    bfile.close()


def createConcList(sinfo, options, overwrite=False, thread=0):
    """
    createConcList - documentation not yet available.
    """

    bfile = open(os.path.join(options['sessionsfolder'], 'conclist' + options['bold_prefix'] + '.list'), 'w')

    concs = options['bolds'].split("|")
    fidls = options['event_file'].split("|")

    if len(concs) != len(fidls):
        print "\nWARNING: Number of conc files (%d) does not match number of event files (%d), processing aborted!" % (len(concs), len(fidls))

    else:
        for session in sinfo:
            try:
                f = getFileNames(session, options)
                d = getSessionFolders(session, options)

                print >> bfile, "session id:%s" % (session['id'])
                print >> bfile, "    roi:%s" % (f['fs_aparc_bold'])

                tfidl  = fidls[0].strip().replace(".fidl", "")

                f_conc = os.path.join(d['s_bold_concs'], f['conc_final'])
                f_fidl = os.path.join(d['s_bold_events'], tfidl + ".fidl")

                print >> bfile, "    fidl:%s" % (f_fidl)
                print >> bfile, "    file:%s" % (f_conc)

            except:
                print "ERROR processing session %s!" % (session['id'])
                raise

    bfile.close()



def listSessionInfo(sinfo, options, overwrite=False, thread=0):
    """
    listSessionInfo - documentation not yet available.
    """
    bfile = open(os.path.join(options['sessionsfolder'], 'SessionInfo.txt'), 'w')

    for session in sinfo:
        print >> bfile, "session: %s, group: %s" % (session['id'], session['group'])

    bfile.close()



def runShellScript(sinfo, options, overwrite=False, thread=0):
    """
    runShellScript [... processing options]

    USE
    ===

    runShellScript runs the specified script on every selected session from
    batch.txt file. It places the specified session specific information
    before running the script. The information to be added is to be referenced
    in the script using double curly braces: {{<key>}}. Specifically, the
    function loops through all the session specific information as well as all
    the processing parameters and places them into the script. If the
    information is not provided, the {{<key>}} will remain as is.

    EXAMPLE
    =======

    If batch.txt contains among others:

    ---
    id: OP578
    subject: OP578
    dicom: /gpfs/project/fas/n3/Studies/MBLab/WM.v3/sessions/OP578/dicom
    raw_data: /gpfs/project/fas/n3/Studies/MBLab/WM.v3/sessions/OP578/nii
    hcp: /gpfs/project/fas/n3/Studies/MBLab/WM.v3/sessions/OP578/hcp
    group: control

    If script.sh contains among others:

    ls -l {{hcp}}/{{id}}/MNINonLinear
    if [ "{{group}}" = "control" ]; then
        mkdir /gpfs/project/fas/n3/Studies/tmp/{{id}}
        cp {{raw_data}}/*.nii.gz /gpfs/project/fas/n3/Studies/tmp/{{id}}
    fi
    echo "{{nothing}}"

    Before running the function will change that part of the script to:

    ls -l /gpfs/project/fas/n3/Studies/MBLab/WM.v3/sessions/OP578/hcp/OP578/MNINonLinear
    if [ "control" = "control" ]; then
        mkdir /gpfs/project/fas/n3/Studies/tmp/OP578
        cp /gpfs/project/fas/n3/Studies/MBLab/WM.v3/sessions/OP578/nii/*.nii.gz /gpfs/project/fas/n3/Studies/tmp/OP578
    fi
    echo "{{nothing}}"


    RELEVANT PARAMETERS
    ===================

    The relevant processing parameters are:

    --script          ... Tha path to the script to be executed.
    --sessions        ... The batch.txt file with all the session information
                          [batch.txt].
    --parsessions     ... How many sessions to run in parallel [1].

    The parameters can be specified in command call or batch.txt file.

    EXAMPLE USE
    ===========
    
    ```
    qunex runShellScript sessions=fcMRI/session_hcp.txt sessionsfolder=sessions \\
          overwrite=no script=fcMRI/processdata.sh
    ````
    
    ----------------
    Written by Grega Repovš 2017-06-24

    Change log
    2019-04-25 Grega Repovš
             - Changed subjects to sessions

    """

    r = "\n---------------------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r += "\nRunning script %s" % (options['script'])
    r += "\n........................................................\n"

    try:
        assert (options['script'] is not None), "ERROR: No script was referenced!"
        assert (os.path.exists(options['script'])), "ERROR: The referenced script does not exist in the path provided!"

        script = file(options['script']).read()

        # --- place session specific data

        for key, value in sinfo.iteritems():
            if not key.isdigit():
                script = script.replace("{{%s}}" % (key), str(value))

        # --- place options

        for key, value in options.iteritems():
            if not key.isdigit():
                script = script.replace("{{%s}}" % (key), str(value))

        # --- check for nonplaced

        nonplaced = re.findall("{{.*?}}", script)

        if nonplaced:
            r += "\nWARNING: the following tags were not filled:"
            for n in nonplaced:
                r += "\n ... " + n

        # --- execute script

        description = "runShellScript: %s" % (options['script'])
        task = "runShellScript-%s" % (options['script'])

        r += runScriptThroughShell(script, description, thread=sinfo['id'], remove=options['log'] == 'remove', task=task, logfolder=options['comlogs'])

    except AssertionError, message:
        r += str(message) + "\n---------------------------------------------------------"
        print r
        return (r, (sinfo['id'], message, 1))

    except ExternalFailed, errormessage:
        r += str(errormessage) + "\n---------------------------------------------------------"
        print r
        return (r, (sinfo['id'], "Failed: " + str(message), 1))

    except:
        message = 'ERROR: Error in parsing or executing script %s' % (options['script'])
        r += "\n" + message + "\n---------------------------------------------------------"
        print r
        raise
        return (r, (sinfo['id'], message, 1))

    r += "\n\nrunShellScript %s completed on %s\n---------------------------------------------------------" % (options['script'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    print r
    return (r, (sinfo['id'], "Ran %s without errors" % (options['script']), 0))
