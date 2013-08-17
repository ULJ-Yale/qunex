#!/opt/local/bin/python2.7

import os
import g_mri
import collections
import g_mri.g_gimg as g

def setupHCP(folder=".", tfolder="hcp", sbjf="subject.txt"):
    inf = g_mri.g_core.readSubjectData(os.path.join(folder, sbjf))[0][0]

    basef    = os.path.join(folder, tfolder, inf['id'])
    rawf     = inf['raw_data']
    sid      = inf['id']
    bolds    = collections.defaultdict(dict)

    print " ---===== Setting up HCP folder structure for %s =====---\n" % (sid)

    if not os.path.exists(basef):
        print " ---> Creating base folder %s " % (basef)
        os.makedirs(basef)
    else:
        print " ...  Base folder %s already exists " % (basef)

    for k, v in inf.iteritems():
        if k.isdigit():
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
                tfile = sid + "_fncb_BOLD_"+boldn+"_SBRef.nii.gz"
                tfold = "BOLD_"+boldn+"_SBRef_fncb"
                bolds[boldn]["ref"] = sfile
            elif "bold" in v['name']:
                boldn = v['name'][4:]
                sfile = k+".nii.gz"
                tfile = sid + "_fncb_BOLD_"+boldn+".nii.gz"
                tfold = "BOLD_"+boldn+"_fncb"
                bolds[boldn]["bold"] = sfile
            elif v['name'] == "SE-FM-AP":
                sfile = k+".nii.gz"
                tfile = sid + "_fncb_BOLD_AP_SB_SE.nii.gz"
                tfold = "SpinEchoFieldMap1_fncb"
            elif v['name'] == "SE-FM-PA":
                sfile = k+".nii.gz"
                tfile = sid + "_fncb_BOLD_PA_SB_SE.nii.gz"
                tfold = "SpinEchoFieldMap1_fncb"
            elif v['name'] == "DWI":
                sfile = [k+e for e in ['.nii.gz', '.bval', '.bvec']]
                tbase = "_".join([sid, 'DWI', v['task']])
                tfile = [tbase+e for e in ['.nii.gz', '.bval', '.bvec']]
                tfold = "Diffusion"
            else:
                print " ... skipping %s %s" % (v['ima'], v['name'])
                continue

            for sfile, tfile in zip(list(sfile), list(tfile)):
                if not os.path.exists(os.path.join(rawf, sfile)):
                    print " ---> WARNING: Can not locate %s - skipping the file" % (os.path.join(rawf, sfile))
                    continue

                if not os.path.exists(os.path.join(basef,tfold)):
                    print " ---> creating subfolder", tfold
                    os.makedirs(os.path.join(basef,tfold))
                else:
                    print " ...  %s subfolder already exists", tfold

                if not os.path.exists(os.path.join(basef,tfold,tfile)):
                    print " ---> linking %s to %s" % (sfile, tfile)
                    os.link(os.path.join(rawf, sfile), os.path.join(basef,tfold,tfile))
                else:
                    print " ...  %s already exists" % (tfile)

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
