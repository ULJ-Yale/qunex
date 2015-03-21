#!/opt/local/bin/python2.7

import os
import glob
import g_mri
import collections
import g_mri.g_gimg as g
import os.path


def setupHCP(folder=".", tfolder="hcp", sbjf="subject_hcp.txt"):
    '''
    setupHCP [folder=.] [tfolder=hcp] [sbjf=subject_hcp.txt]

    - folder:  the base subject folder that contains the nifti images and subject.txt file
    - tfolder: the folder (within the base folder) where to put the HCP data
    - sbjf:    the alternative name of the subject.txt file

    example: gmri setupHCP folder=data tfolder=hcp2 sbjf=subject1.txt
    '''

    inf = g_mri.g_core.readSubjectData(os.path.join(folder, sbjf))[0][0]

    basef    = os.path.join(folder, tfolder, inf['id'])
    rawf     = inf['raw_data']
    sid      = inf['id']
    bolds    = collections.defaultdict(dict)

    if not os.path.exists(rawf):
        print "ERROR: raw_data folder for %s does not exist! Check your paths [%s]! Aborting setupHCP.\n" % (sid, rawf)
        return

    print " ---===== Setting up HCP folder structure for %s =====---\n" % (sid)

    if not os.path.exists(basef):
        print " ---> Creating base folder %s " % (basef)
        os.makedirs(basef)
    else:
        print " ...  Base folder %s already exists " % (basef)

    i = [k for k, v in inf.iteritems() if k.isdigit()]
    i.sort(key=int, reverse=True)

    for k in i:
        v = inf[k]
        if 'o' in v:
            orient = "_"+v['o']
        else:
            orient = ""
        if v['name'] == 'T1w':
            sfile = k+"-o.nii.gz"
            tfile = sid + "_strc_T1w_MPR1.nii.gz"
            tfold = "T1w"
        elif v['name'] == "T2w":
            sfile = k+"-o.nii.gz"
            tfile = sid + "_strc_T2w_SPC1.nii.gz"
            tfold = "T2w"
        elif v['name'] == "FM-Magnitude":
            sfile = k+".nii.gz"
            tfile = sid + "_strc_FieldMap_Magnitude.nii.gz"
            tfold = "FieldMap_strc"
        elif v['name'] == "FM-Phase":
            sfile = k+".nii.gz"
            tfile = sid + "_strc_FieldMap_Phase.nii.gz"
            tfold = "FieldMap_strc"
        elif "boldref" in v['name']:
            boldn = v['name'][7:]
            sfile = k+".nii.gz"
            tfile = sid + "_fncb_BOLD_"+boldn+orient+"_SBRef.nii.gz"
            tfold = "BOLD_"+boldn+orient+"_SBRef_fncb"
            bolds[boldn]["ref"] = sfile
        elif "bold" in v['name']:
            boldn = v['name'][4:]
            sfile = k+".nii.gz"
            tfile = sid + "_fncb_BOLD_"+boldn+orient+".nii.gz"
            tfold = "BOLD_"+boldn+orient+"_fncb"
            bolds[boldn]["bold"] = sfile
        elif v['name'] == "SE-FM-AP":
            sfile = k+".nii.gz"
            tfile = sid + "_fncb_BOLD_AP_SB_SE.nii.gz"
            tfold = "SpinEchoFieldMap"+boldn+"_fncb"
        elif v['name'] == "SE-FM-PA":
            sfile = k+".nii.gz"
            tfile = sid + "_fncb_BOLD_PA_SB_SE.nii.gz"
            tfold = "SpinEchoFieldMap"+boldn+"_fncb"
        elif v['name'] == "SE-FM-LR":
            sfile = k+".nii.gz"
            tfile = sid + "_fncb_BOLD_LR_SB_SE.nii.gz"
            tfold = "SpinEchoFieldMap"+boldn+"_fncb"
        elif v['name'] == "SE-FM-RL":
            sfile = k+".nii.gz"
            tfile = sid + "_fncb_BOLD_RL_SB_SE.nii.gz"
            tfold = "SpinEchoFieldMap"+boldn+"_fncb"
        elif v['name'] == "DWI":
            sfile = [k+e for e in ['.nii.gz', '.bval', '.bvec']]
            tbase = "_".join([sid, 'DWI', v['task']])
            tfile = [tbase+e for e in ['.nii.gz', '.bval', '.bvec']]
            tfold = "Diffusion"
        else:
            print " ... skipping %s %s" % (v['ima'], v['name'])
            continue

        if type(sfile) is not list:
            sfile = [sfile]
        if type(tfile) is not list:
            tfile = [tfile]

        for sfile, tfile in zip(list(sfile), list(tfile)):
            if not os.path.exists(os.path.join(rawf, sfile)):
                print " ---> WARNING: Can not locate %s - skipping the file" % (os.path.join(rawf, sfile))
                continue

            if not os.path.exists(os.path.join(basef,tfold)):
                print " ---> creating subfolder", tfold
                os.makedirs(os.path.join(basef,tfold))
            else:
                print " ...  %s subfolder already exists", (tfold)

            if not os.path.exists(os.path.join(basef,tfold,tfile)):
                print " ---> linking %s to %s" % (sfile, tfile)
                os.link(os.path.join(rawf, sfile), os.path.join(basef,tfold,tfile))
            else:
                print " ---> %s already exists" % (tfile)
                # print " ---> %s already exists, replacing it with %s " % (tfile, sfile)
                # os.remove(os.path.join(basef,tfold,tfile))
                # os.link(os.path.join(rawf, sfile), os.path.join(basef,tfold,tfile))

    # --- checking if all bolds have refs

    # for k, v in bolds.iteritems():
    #     if "ref" not in v:
    #         tfold = "BOLD_"+k+"_SBRef_fncb"
    #         tfile = sid + "_fncb_BOLD_"+boldn+"_SBRef.nii.gz"
    #
    #         if not os.path.exists(os.path.join(rawf, v["bold"])):
    #             print " ---> WARNING: Can not locate %s - skipping extraction of first frame" % (os.path.join(rawf, v["bold"]))
    #             continue
    #
    #         if not os.path.exists(os.path.join(basef,tfold)):
    #             print " ---> creating subfolder", tfold
    #             os.makedirs(os.path.join(basef,tfold))
    #         else:
    #             print " ...  %s subfolder already exists", tfold
    #
    #         if not os.path.exists(os.path.join(basef,tfold,tfile)):
    #             print " ---> extracting first frame of %s to %s" % (v["bold"], tfile)
    #             img = g.gimg(os.path.join(rawf, v["bold"]), 1)
    #             img.saveimage(os.path.join(basef,tfold,tfile))
    #
    #         else:
    #             print " ...  %s already exists" % (tfile)


    print "\n ---=====         DONE          =====---\n"




def setupHCPFolder(folder=".", tfolder="hcp", sbjf="subject_hcp.txt", check="interactive"):
    '''
    setupHCPFolder [folder=.] [tfolder=hcp] [sbjf=subject_hcp.txt] [check=interactive]

    The command looks for sbjf files in all the subfolders of folder and check whether the sbjf are hcp ready
    and if tfolder exists. If the file is ready and folder does not yet exist, it automatically calls setupHCP
    on that folder. If the sbjf does not seem to be ready or if the tfolder exists, the action depends on check.
    If check is "yes", the subject is not processed, if check is "no" the subject is processed. If check is
    "interactive" the user is asked whether the subject should be processed or not.

    - folder:  the directory that holds the subjects' folders (usually "subjects")
    - tfolder: the folder in which to set up data for HCP preprocessing
    - sbjf:    the subject.txt file to use for mapping to HCP folder
    - check:   whether to check if the subject is safe to run (yes), run in in any case (no) or
               ask the user (interactive)
    '''

    # list all possible sbjfiles and check them

    sfiles = glob.glob(os.path.join(folder, "*", sbjf))
    flist  = []

    print "---> checking %s files and %s folders in %s" % (sbjf, tfolder, folder)

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
            print status, " => processing the subject"
        elif check == "yes":
            print status, " => skipping this subject"
        elif check == "interactive":
            print status
            s = raw_input("     ---> do you want to process this subject [y/n]: ")
            if s != 'y':
                process = False

        flist.append((sfile, ready, fex, ok, process))

    for sfile, ready, fex, ok, process in flist:
        if process:
            setupHCP(folder=os.path.dirname(sfile), tfolder=tfolder, sbjf=sbjf)

    print "\n\n===> done processing %s\n" % (folder)


def getHCPReady(folder=".", sfile="subject.txt", tfile="subject_hcp.txt", pattern=None, mapping=None):
    '''
    getHCPReady [folder=.] [sfile=subject.txt] [tfile=subject_hcp.txt] [pattern="*"] [mapping=specs/hcpmap.txt]

    The command checks all the directories in the folder that match the pattern checking for the presence of sfile.
    If sfile is found, each sequence name is checked against the source specified in hcpmap.txt file and replaced
    with the provided text. The resulting file is saved to tfile. In hcpmap.txt the mapping is specified line by line
    in the form of "source text => replacement text". All lines not matching the pattern are ignored.

    - folder:   the directory that holds subjects' folders (usually "subjects")
    - sfile:    the "source" subject.txt file
    - tfile:    the replacement subject.txt file
    - pattern:  glob pattern to use in identifying subject folders
    - mapping:  the path to the text file describing the mapping
    '''

    if pattern == None:
        pattern = "*"
    if mapping == None:
        mapping = os.path.join(folder, 'specs', 'hcpmap.txt')

    # -- get mapping ready

    if not os.path.exists(mapping):
        print "ERROR: No HCP mapping file found. Aborting."
        return

    print " ... Reading HCP mapping from %s" % (mapping)

    mapping = [line.strip() for line in open(mapping)]
    mapping = [e.split('=>') for e in mapping]
    mapping = [[f.strip() for f in e] for e in mapping if len(e) == 2]
    mapping = dict(mapping)

    # -- get list of subject folders

    sfolders = glob.glob(os.path.join(folder, pattern))

    # -- loop through subject folders

    for sfolder in sfolders:

        ssfile = os.path.join(sfolder, sfile)
        stfile = os.path.join(sfolder, tfile)

        if not os.path.exists(ssfile):
            continue
        print " ... Processing folder %s" % (sfolder)


        lines = [line.strip() for line in open(ssfile)]

        images = False
        hcpok  = False
        bold   = 0
        nlines = []
        hasref = False
        for line in lines:
            e = line.split(':')
            if len(e) > 1:
                if e[0].strip() == 'hcpready' and e[1].strip() == 'true':
                    hcpok = True
                if e[0].strip().isdigit():
                    if not images:
                        nlines.append('hcpready: true')
                        images = True

                    oimg = e[1].strip()
                    if oimg in mapping:
                        repl  = mapping[oimg]
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

                    e[1] = " %-16s:%s" % (repl, oimg)
                    nlines.append(":".join(e))
                else:
                    nlines.append(line)
            else:
                nlines.append(line)

        if hcpok:
            print "     ... %s already HCP ready" % (sfile)
        else:
            print "     ... writing %s" % (tfile)
            fout = open(stfile, 'w')
            for line in nlines:
                print >> fout, line


