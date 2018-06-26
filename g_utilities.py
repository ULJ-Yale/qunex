#!/usr/bin/env python
# encoding: utf-8
"""
Miscellaneous utilities for file processing.

Created by Grega Repovs on 2017-09-17.
Copyright (c) Grega Repovs. All rights reserved.
"""

import os.path
import os
import glob
import datetime
import shutil
import niutilities.g_process as gp
import niutilities.g_core as gc
import getpass
import re


parameterTemplateHeader = '''#  Batch parameters file
#  =====================
#
#  This file is used to specify the default parameters used by various MNAP commands for
#  HCP minimal preprocessing pipeline, additional bold preprocessing commands,
#  and other analytic functions. The content of this file should be prepended to the list
#  that contains all the subjects that is passed to the commands. It can added manually or
#  automatically when making use of the compileLists MNAP command.
#
#  This template file should be edited to include the parameters relevant for
#  a given study/analysis and provide the appropriate values. For detailed description of
#  parameters and their valid values, please consult the MNAP documentation
*  (e.g. Running HCP minimal preprocessing pipelines, Additional BOLD
#  preprocessing) and online help for the relevant MNAP commands.
#
#
#  File format
#  -----------
#
#  Each parameter is specified in a separate line as a
#  "_<parameter_key>: <parameter_value>" pair. For example:
#
#  _hcp_brainsize:  170
#
#  Empty lines and lines that start with a hash (#) are ignored.
#
#
#  Parameters
#  ==========
#
#  The following is a list of parameters organized by the commands they relate
#  to. To specify parameters, uncomment the line (it should start with the
#  underscore before the parameter name) and provide the desired value. In some
#  cases default values are provided. Do take care to remove the descriptors
#  (... <description>) after the values for the parameters to be used.'''



def createStudy(studyfolder=None):
    '''
    createStudy studyfolder=<path to study base folder>

    Creates the base folder at the provided path location and the key standard
    study subfolders. Specifically:

    <studyfolder>
    ├── analysis
    │   └── scripts
    ├── processing
    │   ├── logs
    │   ├── lists
    │   └── scripts
    ├── info
    │   ├── demographics
    │   ├── tasks
    │   └── stimuli
    └── subjects
        ├── inbox
        │   ├── MR
        │   ├── EEG
        │   ├── behavior
        │   └── events
        ├── archive
        │   ├── MR
        │   ├── EEG
        │   └── behavior
        ├── specs
        └── QC

    Do note that the command will create all the missing subfolders in which the
    specified study is to reside. The command also prepares template
    batch_parameters_example.txt and hcp_mapping_example.txt files in
    <studyfolder>/subjects/specs folder. Finally, it creates a .mnapstudy file in
    the <studyfolder> to identify it as a study basefolder.

    Example:

    gmri createStudy studyfolder=/Volumes/data/studies/WM.v4

    ----------------
    Written by Grega Repovš

    Changelog
    2017-12-26 Grega Repovš
             - Added copying of parameters and hcpmap templates.
    2018-03-31 Grega Repovs
             - Added creation of .mnapstudy file.
    2018-06-02 Grega Repovs
             - Changed templates to *_example.txt.
    '''

    if studyfolder is None:
        raise ValueError("ERROR: studyfolder parameter has to be provided!")

    folders = [['analysis'], ['analysis', 'scripts'], ['processing'], ['processing', 'logs'], ['processing', 'lists'], ['processing', 'scripts'],
               ['info'], ['info', 'demographics'], ['info', 'tasks'], ['info', 'stimuli'],
               ['subjects'], ['subjects', 'inbox'], ['subjects', 'inbox', 'MR'], ['subjects', 'inbox', 'EEG'], ['subjects', 'inbox', 'behavior'], ['subjects', 'inbox', 'events'],
               ['subjects', 'archive'], ['subjects', 'archive', 'MR'], ['subjects', 'archive', 'EEG'], ['subjects', 'archive', 'behavior'], ['subjects', 'specs'], ['subjects', 'QC']]

    print "\nCreating study folder structure:"
    for folder in folders:
        tfolder = os.path.join(*[studyfolder] + folder)

        if os.path.exists(tfolder):
            print " ... folder exists:", tfolder
        else:
            print " ... creating:", tfolder
            os.makedirs(tfolder)

    TemplateFolder = os.environ['TemplateFolder']
    print "\nPreparing template files:"

    paramFile = os.path.join(studyfolder, 'subjects', 'specs', 'batch_parameters_example.txt')
    if not os.path.exists(paramFile):
        print " ... batch_parameters_example.txt"
        pfile = open(paramFile, 'w')
        print >> pfile, parameterTemplateHeader
        for line in gp.arglist:
            if len(line) == 4:
                print >> pfile, "# _%-24s : %-15s ... %s" % (line[0], line[1], line[3])
            elif len(line) > 0:
                print >> pfile, "#\n# " + line[0] + '\n#'
        pfile.close()
    else:
        print " ... batch_parameters_example.txt file already exists"

    mapFile = os.path.join(studyfolder, 'subjects', 'specs', 'hcp_mapping_example.txt')
    if os.path.exists(mapFile):
        print " ... hcp_mapping_example.txt file already exists"
    else:
        print " ... hcp_mapping_example.txt"
        shutil.copyfile(os.path.join(TemplateFolder, 'templates', 'hcp_mapping_example.txt'), mapFile)

    markFile = os.path.join(studyfolder, '.mnapstudy')
    if os.path.exists(markFile):
        print " ... .mnapstudy file already exists"
    else:
        mark = open(markFile, 'w')
        try:
            username = getpass.getuser()
        except:
            username = "unknown user"
        print >> mark, "%s study folder created on %s by %s." % (os.path.basename(studyfolder), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username)
        mark.close()

    print "\nDone.\n"


def compileBatch(subjectsfolder=".", sfile="subject_hcp.txt", tfile=None, subjects=None, sfilter=None, overwrite="ask", paramfile=None):
    '''
    compileBatch [subjectsfolder=.] [sfile=subject_hcp.txt] [tfile=processing/batch.txt] [subjects=None] [sfilter=None] [overwrite=ask] [paramfile=<subjectsfolder>/specs/batch_parameters.txt]

    Combines all the sfile in all subject folders in subjectsfolder to
    generate a joint batch file and save it as tfile. If only specific subjects
    are to be added or appended, "subjects" parameter can be used. This can be
    a pipe, comma or space separated list of subject ids, another batch file or
    a list file. If a string is provided, grob patterns can be used (e.g.
    subjects="AP*|OR*") and all matching subjects will be processed.

    If no tfile is specified, it will save the file as batch.txt in a
    processing folder parallel to the subjectsfolder. If the folder does not yet
    exist, it will create it.

    If tfile already exists, depending on "overwrite" parameter it will:

    - ask:    ask interactively
    - yes:    overwrite the existing file
    - no:     abort creating the file
    - append: append subjects to the existing file

    If overwrite is set to "append", the parameters will not be changed, however,
    any subjects that are not yet present in the batch file will be appended at
    the end of the batch file.

    The command will also look for a parameter file. If it exists, it will
    prepend its content at the beginning of the batch.txt file. If no paramfile
    is specified and the default template does not exist, the command will print
    a warning and create an empty template (subjects/spec/batch_parameters.txt)
    with all the available parameters. Do note that this file will need to be edited
    with correct parameter values for your study.

    Alternatively, if you don't have a parameter file prepared, you can use or
    copy and modify one of the following templates:

    legacy data template: $TemplateFolder/templates/batch_legacy_parameters.txt
    multiband data template: $TemplateFolder/templates/batch_multiband_parameters.txt

    Example:

    gmri compileBatch sfile="subject.txt" tfile="fcMRI/subjects_fcMRI.txt"

    ----------------
    Written by Grega Repovš

    Changelog
    2017-12-26 Grega Repovš
             - Renamed to compileBatch and batch.txt.
    2018-01-01 Grega Repovš
             - Added append option and changed parameter names.
             - Added the option to specify subjects to add explicitly.
    '''

    if subjects in ['None', 'none', 'NONE']:
        subjects = None

    if sfilter in ['None', 'none', 'NONE']:
        sfilter = None

    # --- prepare target file name and folder

    if tfile is None:
        tfile = os.path.join(os.path.dirname(os.path.abspath(subjectsfolder)), 'processing', 'batch.txt')

    if os.path.exists(tfile):
        print "WARNING: target file %s already exists!" % (os.path.abspath(tfile))
        if overwrite == 'ask':
            s = raw_input("         Do you want to overwrite it (o), cancel command (c), or append to the file (a)? [o/c/a]: ")
            if s == 'o':
                print "         Overwriting exisiting file."
                overwrite = 'yes'
            elif s == 'a':
                print "         Appending to exisiting file."
                overwrite = 'append'
            else:
                print "         Aborting."
                return
        elif overwrite == 'yes':
            print "         Overwriting exisiting file."
        elif overwrite == 'append':
            print "         Appending to exisiting file."
        elif overwrite == 'no':
            print "         Aborting."
            return
    else:
        overwrite = 'yes'

    targetFolder = os.path.dirname(tfile)
    if not os.path.exists(targetFolder):
        print "---> Creating target folder %s" % (targetFolder)
        os.makedirs(targetFolder)

    # --- open target file

    if overwrite == 'yes':
        print "---> Creating file %s" % (os.path.basename(tfile))
        jfile = open(tfile, 'w')
        print >> jfile, "# File generated automatically on %s" % (datetime.datetime.today())
        print >> jfile, "# Subjects folder: %s" % (os.path.abspath(subjectsfolder))
        print >> jfile, "# Source files: %s" % (sfile)
        slist   = []

    elif overwrite == 'append':
        slist, parameters = gc.getSubjectList(tfile)
        slist = [e['id'] for e in slist]
        print "---> Appending to file %s" % (os.path.basename(tfile))
        jfile = open(tfile, 'a')

    # --- check for param file

    if overwrite == 'yes':
        if paramfile is None:
            paramfile = os.path.join(subjectsfolder, 'specs', 'batch_parameters.txt')
            if not os.path.exists(paramfile):
                print "---> WARNING: Creating empty parameter file!"
                pfile = open(paramfile, 'w')
                print >> pfile, parameterTemplateHeader
                for line in gp.arglist:
                    if len(line) == 4:
                        print >> pfile, "# _%-24s : %-15s ... %s" % (line[0], line[1], line[3])
                    elif len(line) > 0:
                        print >> pfile, "#\n# " + line[0] + '\n#'
                pfile.close()

            if os.path.exists(paramfile):
                print "---> appending parameter file [%s]." % (paramfile)
                print >> jfile, "# Parameter file: %s\n#" % (paramfile)
                with open(paramfile) as f:
                    for line in f:
                        print >> jfile, line,
            else:
                print "---> parameter files does not exist, skipping [%s]." % (paramfile)

    # -- get list of subject folders

    if subjects is not None:
        subjects, gopts = gc.getSubjectList(subjects, sfilter=sfilter, verbose=False)
        files = []
        for subject in subjects:
            files += glob.glob(os.path.join(subjectsfolder, subject['id'], sfile))
    else:
        files = glob.glob(os.path.join(os.path.abspath(subjectsfolder), '*', sfile))

    # --- loop trough subject files

    files.sort()
    for file in files:
        subjectid = os.path.basename(os.path.dirname(file))
        if subjectid in slist:
            print "---> Skipping: %s" % (subjectid)
        else:
            print "---> Adding: %s" % (subjectid)
            print >> jfile, "\n---"
            with open(file) as f:
                for line in f:
                    print >> jfile, line,

    # --- close file

    print "===> Done"
    jfile.close()



def createList(subjectsfolder=".", subjects=None, sfilter=None, listfile=None, bolds=None, conc=None, fidl=None, glm=None, roi=None, boldname="bold", boldtail=".nii.gz", overwrite='no', check='yes'):
    """
    createList [subjectsfolder="."] [subjects=None] [sfilter=None] [listfile=None] [bolds=None] [conc=None] [fidl=None] [glm=None] [roi=None] [boldname="bold"] [boldtail=".nii.gz"] [overwrite='no'] [check='yes']

    The function creates a .list formated file that can be used as input to a
    number of processing and analysis functions. The function is fairly flexible,
    its output defined using a number of parameters.

    The location of the file
    ------------------------

    The file is created at the path specified in `listfile` parameter. If no
    parameter is provided, the resulting list is saved in:

    <studyfolder>/processing/lists/subjects.list

    If a file already exists, depending on the `overwrite` parameter the
    function will:

    - ask:    ask interactively, what to do
    - yes:    overwrite the existing file
    - no:     abort creating the file
    - append: append subjects to the existing file

    The subjects to list
    --------------------

    Subjects to include in the list are specified using `subjects` parameter.
    This can be a pipe, comma or space separated list of subject ids, a batch
    file or another list file. If a string is provided, grob patterns can be
    used (e.g. subjects="AP*|OR*") and all matching subjects will be included.

    If a batch file is provided, subjects can be filtered using the `sfilter`
    parameter. The parameter should be provided as a string in the format:

    "<key>:<value>|<key>:<value>"

    Only the subjects for which all the specified keys match the specified values
    will be included in the list.

    If no subjects are specified, the function will inspect the `subjectsfolder`
    and include all the subjects for which an `images` folder exists as a
    subfolder in the subject's folder.

    The files to include
    --------------------

    The function enables inclusion of bold, conc, fidl, glm and roi files.

    *bold files*
    To include bold files, specify them using the `bolds` parameter. Provide a
    string that lists bold numbers or bold task names in a space, comma or pipe
    separated string. The numeric values in the string will be interpreted as
    bold numbers to include, strings will be interpreted as bold task names as
    they are provided in the batch file. All the bolds that match any of the
    tasks listed will be included. If `all` is specified, all the bolds listed
    in the batch file will be included.

    Two other parameters are cruical for generation of bold file entries in the
    list: `boldname` and `boldtail`.

    The bolds will be listed in the list file as:

    file:<subjectsfolder>/<subject>/images/functional/<boldname><boldnumber><boldtail>

    *conc files*
    To include conc files, provide a `conc` parameter. In the parameter list the
    name of the conc file to be include. Conc files will be listed as:

    conc:<subjectsfolder>/<subject>/images/functional/concs/<conc>

    *fidl files*
    To include fidl files, provide a `fidl` parameter. In the parameter list the
    name of the fidl file to include. Fidl files will be listed as:

    fidl:<subjectsfolder>/<subject>/images/functional/events/<fidl>

    *GLM files*
    To include GLM files, provide a `glm` parameter. In the parameter list the
    name of the GLM file to include. GLM files will be listed as:

    glm:<subjectsfolder>/<subject>/images/functional/<glm>

    *ROI files*
    To include ROI files, provide a `roi` parameter. In the parameter list the
    name of the ROI file to include. ROI files will be listed as:

    roi:<subjectsfolder>/<subject>/images/<roi>

    Note that for all the files the function expects the files to be present in
    the correct places within the MNAP subjects folder structure. For ROI files
    provide the relative path from the `images` folder.

    Checking for presence of files
    ------------------------------

    By default the function checks if the files listed indeed exist. If a file
    is missing, the function will abort and no list will be created or appended.
    The behavior is specified using the `check` parameter that can take the
    following values:

    - yes  ... check for presence and abort if the file to be listed is not found
    - no   ... do not check whether files are present or not
    - warn ... check for presence and warn if the file to be listed is not found

    Examples
    --------

    > gmri createList bolds="1,2,3"

    The command will create a list file in `../processing/list/subjects.txt` that
    will list for all the subjects found in the current folder BOLD files 1, 2, 3
    listed as:

      file:<current path>/<subject>/images/functional/bold[n].nii.gz

    > gmri createList subjectsfolder="/studies/myStudy/subjects" subjects="batch.txt" \\
           bolds="rest" listfile="lists/rest.list" boldtail="_Atlas_g7_hpss_res-mVWMWB1d.dtseries"

    The command will create a `lists/rest.list` list file in which for all the
    subjects specified in the `batch.txt` it will list all the BOLD files tagged
    as rest runs and include them as:

      file:<subjectsfolder>/<subject>/images/functional/bold[n]_Atlas_g7_hpss_res-mVWMWB1d.dtseries

    > gmri createList subjectsfolder="/studies/myStudy/subjects" subjects="batch.txt" \\
           sfilter="EC:use" listfile="lists/EC.list" \\
           conc="bold_Atlas_dtseries_EC_g7_hpss_res-mVWMWB1de.conc" \\
           fidl="EC.fidl" glm="bold_conc_EC_g7_hpss_res-mVWMWB1de_Bcoeff.nii.gz" \\
           roi="segmentation/hcp/fsaverage_LR32k/aparc.32k_fs_LR.dlabel.nii"

    The command will create a list file in `lists/EC.list" that will list for
    all the subject in the conc file, that have the key:value pair "EC:use" the
    following files:

      conc:<subjectsfolder>/<subject>/images/functional/concs/bold_Atlas_dtseries_EC_g7_hpss_res-mVWMWB1de.conc
      fidl:<subjectsfolder>/<subject>/images/functional/events/EC.fidl
      glm:<subjectsfolder>/<subject>/images/functional/bold_conc_EC_g7_hpss_res-mVWMWB1de_Bcoeff.nii.gz
      roi:<subjectsfolder>/<subject>/images/segmentation/hcp/fsaverage_LR32k/aparc.32k_fs_LR.dlabel.nii

    ----------------
    Written by Grega Repovš 2018-06-26

    """

    def checkFile(fileName):
        if check == 'no':
            pass
        elif not os.path.exists(fileName):
            if check == 'warn':
                print "WARNING: File does not exist [%s]!" % (fileName)
            else:
                print "ERROR: File does not exist [%s]!" % (fileName)
                print "       Aborting."
                exit()

    print "Running createList\n=================="

    # --- check subjects

    if subjects in ['None', 'none', 'NONE']:
        subjects = None

    if sfilter in ['None', 'none', 'NONE']:
        sfilter = None

    # --- prepare parameters

    boldtags, boldnums = None, None

    if bolds:
        bolds = [e.strip() for e in re.split(' *, *| *\| *| +', bolds)]
        boldtags = [e for e in bolds if not e.isdigit()]
        boldnums = [e for e in bolds if e.isdigit()]

    bsearch  = re.compile('bold([0-9]+)')

    # --- prepare target file name and folder

    if listfile is None:
        listfile = os.path.join(os.path.dirname(os.path.abspath(subjectsfolder)), 'processing', 'lists', 'subjects.list')
        print "WARNING: No target list file name specified.\n         The list will be created as: %s!" % (listfile)

    if os.path.exists(listfile):
        print "WARNING: Target list file %s already exists!" % (os.path.abspath(listfile))
        if overwrite == 'ask':
            s = raw_input("         Do you want to overwrite it (o), cancel command (c), or append to the file (a)? [o/c/a]: ")
            if s == 'o':
                print "         Overwriting exisiting file."
                overwrite = 'yes'
            elif s == 'a':
                print "         Appending to exisiting file."
                overwrite = 'append'
            else:
                print "         Aborting."
                return
        elif overwrite == 'yes':
            print "         Overwriting the exisiting file."
        elif overwrite == 'append':
            print "         Appending to the exisiting file."
        elif overwrite == 'no':
            print "         Aborting."
            return
    else:
        overwrite = 'yes'

    targetFolder = os.path.dirname(listfile)
    if not os.path.exists(targetFolder):
        print "---> Creating target folder %s" % (targetFolder)
        os.makedirs(targetFolder)

    # --- check subjects

    if subjects is None:
        print "WARNING: No subjects specified. The list will be generated for all subjects in the subjects folder!"
        subjects = glob.glob(os.path.join(subjectsfolder, '*', 'images'))
        subjects = [os.path.basename(os.path.dirname(e)) for e in subjects]
        subjects = "|".join(subjects)

    subjects, gopts = gc.getSubjectList(subjects, sfilter=sfilter, verbose=False)

    # --- generate list entries

    lines = []

    for subject in subjects:
        lines.append("subject id: %s" % (subject['id']))

        if boldnums:
            for boldnum in boldnums:
                tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', 'functional', boldname + boldnum + boldtail)
                checkFile(tfile)
                lines.append("    file:" + tfile)

        if boldtags:
            try:
                bolds = [(bsearch.match(v['name']).group(1), v['name'], v['task']) for (k, v) in subject.iteritems() if k.isdigit() and bsearch.match(v['name'])]
                if "all" not in boldtags:
                    bolds = [n for n, b, t in bolds if t in boldtags]
                else:
                    bolds = [n for n, b, t in bolds]
                bolds.sort()
            except:
                pass
            for boldnum in bolds:
                tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', 'functional', boldname + boldnum + boldtail)
                checkFile(tfile)
                lines.append("    file:" + tfile)

        if roi:
            tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', roi)
            checkFile(tfile)
            lines.append("    roi:" + tfile)

        if glm:
            tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', 'functional', glm)
            checkFile(tfile)
            lines.append("    glm:" + tfile)

        if conc:
            tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', 'functional', 'concs', conc)
            checkFile(tfile)
            lines.append("    conc:" + tfile)

        if fidl:
            tfile = os.path.join(os.path.abspath(subjectsfolder), subject['id'], 'images', 'functional', 'events', fidl)
            checkFile(tfile)
            lines.append("    fidl:" + tfile)

    # --- write to target file

    if overwrite == 'yes':
        print "---> Creating file %s" % (os.path.basename(listfile))
        lfile = open(listfile, 'w')
        print >> lfile, "# File generated automatically on %s" % (datetime.datetime.today())

    elif overwrite == 'append':
        print "---> Appending to file %s" % (os.path.basename(listfile))
        lfile = open(listfile, 'a')
        print >> lfile, "# Appended to file on %s" % (datetime.datetime.today())

    for line in lines:
        print >> lfile, line

    lfile.close()
    print "===> Done"