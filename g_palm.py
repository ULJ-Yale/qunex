#!/opt/local/bin/python2.7
# encoding: utf-8
"""
Created by Grega Repovs on 2016-08-30.
Copyright (c) Grega Repovs. All rights reserved.
"""

import os
import os.path
import subprocess
import gzip
import shutil
import glob

def runPALM(image, design=None, args=None, root=None):
    '''
    runPALM image=<image file> design=<design string> [args=<list of arguments>]

    Runs PALM on the provided image using the provided design files. The image can be either
    a volume NIfTI file or a CIFT .dtseries.nii file. In the latter case the file will be
    split up into left and right surface and volume files and then stitched back together
    in a sigle .dtseries file.

    The design string specifies the design files to use. It should be a pipe separated list of
    key:value pairs. That specify:
    - name : the root name of the design files [palm]
    - d    : the suffix specifying the design file [d]
    - t    : the suffix specifying the t contrasts file [t]
    - f    : the suffix specifying the f contrasts file [f]
    - eb   : the suffix specifying the exchange blocks file [eb]

    If "none" is given as value, that file is not specified.

    All design files need to be provided with the design name root:
    - design_d.csv for the design matrix
    - design_t.csv for the t contrast file
    - design_f.csv for the f contrast file (if it does not exist, it will be skipped)
    - design_eb.csv for the exchangibility block file

    args is a string specifying what additional arguments to pass to palm. The format of the string is:
    "arg1|arg2|arg3:value:value|arg4:value".

    The default arguments and values are: "n:100|zstats".

    To exclude a default argument, specify "arg:remove".

    Relevant arguments to consider:

    accel   : methods to accelerate analysis. Possible values are:
              - noperm  : do not do any permutations (works with fdr correction only)
              - tail    : estimates tail of the permuted distribution, needs at least 100 resamples
              - negbin  : runs as many permutations an needed (works with fdr correction only)
              - gamma   : computes the moment of permutation distribution and fits a gamma function
              - lowrank : runs as many permutations as needed to complete matrix (fdr, fwer only)
    twotail : run two-tailed test for all the contrasts
    fdr     : compute a fdr correction for multiple comparisons
    T       : Enable TFCE inference
    C <z>   : Enable cluster inference for univariate tests with z cutoff
    '''

    print "\n Running PALM"
    print " --> checking input and environment"

    if not os.path.exists(image):
        print "ERROR: The image file is missing: %s. Aborting PALM!" % (image)
        exit(1)

    # missing = []
    # for check in [image, design + '_d.csv', design + '_t.csv', design + '_eb.csv']:
    #     if not os.path.exists(check):
    #         missing.append(check)
    # if missing:
    #     print "WARNING: The following design files are missing and will be omitted: %s." % (", ".join(missing))
    #     return

    if not "HCPATLAS" in os.environ:
        print "ERROR: HCPATLAS environment variable not set. Can not find HCP Template files!"
        return
    atlas = os.environ['HCPATLAS']


    # --- parse design options

    print " --> parsing design options"

    doptions = {'name': 'palm', 'd': 'd', 't': 't', 'f': 'f', 'eb': 'eb'}

    if design is not None:
        design = [e.split(':') for e in design.split('|')]
        for k, v in design:
            doptions[k.strip()] = v.strip()

    if root is None:
        root = doptions['name']

    # --- parse argument options

    print " --> parsing arguments"

    arguments = {'n': ['100'], 'zstat': None}

    if args is not None:
        args = [e.strip() for e in args.split('|')]
        for a in args:
            a = [e.strip() for e in a.split(':')]
            if len(a) == 1:
                arguments[a[0]] = None
            else:
                if a[1] == 'remove':
                    arguments.pop(a[0], None)
                else:
                    arguments[a[0]] = a[1:]

    # --- setup and run

    toclean   = [];

    try:

        # --- prepare input files and arguments

        if '.nii.gz' in image:
            simage = root + '_volume.nii'

            print " --> ungzipping %s" % (image)
            with gzip.open(image, 'rb') as fin, open(simage, 'wb') as fout:
                shutil.copyfileobj(f_in, f_out)
            toclean.append(simage)
            iformat = 'nifti'

        elif '.dtseries.nii' in image:
            print " --> decomposing %s" % (image)
            command = ['wb_command', '-cifti-separate', image, 'COLUMN',
                '-volume-all', root + '_volume.nii',                     # , '-roi', 'cifti_volume_mask.nii'
                '-metric', 'CORTEX_LEFT', root + '_left.func.gii',
                '-metric', 'CORTEX_RIGHT', root + '_right.func.gii']

            print " --> running:", " ".join(command)
            if subprocess.call(command):
                print "ERROR: Command failed: %s" % (" ".join(command))
                raise ValueError("ERROR: Command failed: %s" % (" ".join(command)))
            toclean += [root + e for e in ['_volume.nii', '_left.func.gii', '_right.func.gii']]
            iformat = 'cifti'

        else:
            print "ERROR: Unknown format of the input file [%s]!" % (image)
            return

        # --- compile PALM command

        print " --> compiling PALM commands"

        # --- put together design related arguments

        dargs = []

        for f in ['d', 't', 'f', 'eb']:
            if doptions[f] is not "none":
                tfile = "%s_%s.csv" % (doptions['name'], doptions[f])
                if os.path.exists(tfile):
                    dargs += ['-' + f, tfile]

        # --- put together statistics and other related arguments

        sargs = []
        for k, v in arguments.iteritems():
            sargs += ['-' + k]
            if v is not None:
                sargs += v

        # --- run PALM

        if iformat == 'nifti':
            print " --> running PALM for NIfTI input"
            inargs  = ['-i', root + '_volume.nii', '-m', os.path.join(atlas, 'MNITemplates', 'MNI152_T1_2mm_brain_mask_dil.nii')]
            command = ['palm'] + inargs + dargs + sargs + ['-o', root + '_volume']
            if subprocess.call(command):
                print "ERROR: Command failed: %s" % (" ".join(command))
                raise ValueError("ERROR: Command failed: %s" % (" ".join(command)))

        else:
            print " --> running PALM for CIFTI input"

            print "     ... Volume"
            inargs  = ['-i', root + '_volume.nii', '-m', os.path.join(atlas, 'masks', 'volume.cifti.mask.nii')]
            command = ['palm'] + inargs + dargs + sargs + ['-o', root + '_volume']
            if subprocess.call(command):
                print "ERROR: Command failed: %s" % (" ".join(command))
                raise ValueError("ERROR: Command failed: %s" % (" ".join(command)))

            print "     ... Left Surface"
            inargs  = ['-i', root + '_left.func.gii', '-m', os.path.join(atlas, 'masks', 'surface.cifti.L.mask.32k_fs_LR.func.gii'), '-s', os.path.join(atlas, 'Q1-Q6_R440.L.midthickness.32k_fs_LR.surf.gii')]
            command = ['palm'] + inargs + dargs + sargs + ['-o', root + '_L']
            if '-T' in command:
                command += ['-tfce2D']
            if subprocess.call(command):
                print "ERROR: Command failed: %s" % (" ".join(command))
                raise ValueError("ERROR: Command failed: %s" % (" ".join(command)))

            print "     ... Left Surface"
            inargs  = ['-i', root + '_right.func.gii', '-m', os.path.join(atlas, 'masks', 'surface.cifti.R.mask.32k_fs_LR.func.gii'), '-s', os.path.join(atlas, 'Q1-Q6_R440.R.midthickness.32k_fs_LR.surf.gii')]
            command = ['palm'] + inargs + dargs + sargs + ['-o', root + '_R']
            if '-T' in command:
                command += ['-tfce2D']
            if subprocess.call(command):
                print "ERROR: Command failed: %s" % (" ".join(command))
                raise ValueError("ERROR: Command failed: %s" % (" ".join(command)))

        # --- process output

        if iformat == 'nifti':
            pass
        else:
            print " --> reconstructing results into CIFTI files"

            for pval in ['_fdrp', '_fwep', '_uncp', '']:
                for stat in ['tstat', 'fstat', 'ztstat', 'zfstat']:
                    for volumeUnit, surfaceUnit, unitKind in [('vox', 'dpv', 'reg'), ('tfce', 'tfce', 'tfce')]:
                        rvolumes       = glob.glob("%s_volume_%s_%s%s*.nii" % (root, volumeUnit, stat, pval))
                        rleftsurfaces  = glob.glob("%s_L_%s_%s%s*.gii" % (root, surfaceUnit, stat, pval))
                        rrightsurfaces = glob.glob("%s_R_%s_%s%s*.gii" % (root, surfaceUnit, stat, pval))

                        C = 0
                        while rvolumes:
                            C += 1
                            targetfile     = "%s_%s_%s%s_C%d.dscalar.nii" % (root, unitKind, stat, pval, C)
                            print "     ... creating", targetfile,

                            rvolume       = rvolumes.pop(0)
                            rleftsurface  = rleftsurfaces.pop(0)
                            rrightsurface = rrightsurfaces.pop(0)

                            # --- and func to gii
                            os.rename(rleftsurface, rleftsurface.replace('.gii', '.func.gii'))
                            os.rename(rrightsurface, rrightsurface.replace('.gii', '.func.gii'))
                            rleftsurface = rleftsurface.replace('.gii', '.func.gii')
                            rrightsurface = rrightsurface.replace('.gii', '.func.gii')

                            command = ['wb_command', '-cifti-create-dense-scalar', targetfile,
                                       '-volume', rvolume, os.path.join(atlas, 'standard_mesh_atlases', 'Atlas_ROIs.2.nii.gz'),
                                       '-left-metric', rleftsurface, '-roi-left', os.path.join(atlas, 'standard_mesh_atlases', 'L.atlasroi.32k_fs_LR.shape.gii'),
                                       '-right-metric', rrightsurface, '-roi-right', os.path.join(atlas, 'standard_mesh_atlases', 'R.atlasroi.32k_fs_LR.shape.gii')]
                            if subprocess.call(command):
                                print "ERROR: Command failed: %s" % (" ".join(command))
                                raise ValueError("ERROR: Command failed: %s" % (" ".join(command)))

                            if os.path.exists(targetfile):
                                print "... done!"
                                os.remove(rvolume)
                                os.remove(rleftsurface)
                                os.remove(rrightsurface)
                            else:
                                print "... ops! File was not created!"


    except:
        for f in toclean:
            if os.path.exists(f):
                os.remove(f)
        raise

    # ---- cleanup

    for f in toclean:
        if os.path.exists(f):
            os.remove(f)



def maskMap(image=None, masks=None, output=None, minv=None, maxv=None):
    '''
    maskMap image=<image file> masks=<list of masks to use> [output=<output image name>] [minv=<list of thresholds>] [maxv=<list of thresholds>]

    Wrapper for wb_command that takes the provided image (e.g. ztstat image from PALM) and masks it using the listes masks.
    There can be more than one mask, they should be in a comma separated string. At least minv or maxv needs to be specified.
    If there is just one value, all the masks will be thresholded using the same value. If more values are provided as comma separated list,
    they should match the number of masks. If both minv and maxv are provided, both will be used.

    The result will be saved in "output". If none is provided it will saved as the original image with "masked" appended.
    '''

    # --- process the arguments

    if image is None:
        raise ValueError("ERROR: No image file was specified!")
    elif not os.path.exists(image):
        raise ValueError("ERROR: The specified image file does not exist! [%s]" % (image))

    if masks is None:
        raise ValueError("ERROR: No msk file was specified!")
    masks = [e.strip() for e in masks.split(',')]
    for mask in masks:
        if not os.path.exists(mask):
            raise ValueError("ERROR: The specified mask file does not exist! [%s]" % (mask))
    nmasks = len(masks)

    if output is None:
        output = 'Masked_' + image

    if minv is None and maxv is None:
        raise ValueError("ERROR: At least minv or maxv need to be specified!")

    if minv is not None:
        minv = [float(e) for e in minv.split(',')]
        if len(minv) == 1:
            minv = [minv[0] for e in range(nmasks)]
        elif len(minv) != nmasks:
            raise ValueError("ERROR: Number of provided minimum values does not match number of masks!")

    if maxv is not None:
        maxv = [float(e) for e in maxv.split(',')]
        if len(maxv) == 1:
            maxv = [maxv[0] for e in range(nmasks)]
        elif len(maxv) != nmasks:
            raise ValueError("ERROR: Number of provided maximum values does not match number of masks!")


    # --- build the expression

    ex = []

    for n in range(nmasks):
        if minv is None:
            ex.append("(m%d < %.3f)" % (n, maxv[n]))
        elif maxv is None:
            ex.append("(m%d > %.3f)" % (n, minv[n]))
        else:
            ex.append("((m%d > %.3f) * (m%d < %.3f))" % (n, minv[n], maxv[n]))

    ex = ["((%s) > 0) * img" % (" + ".join(ex))]

    files = ['-var', 'img', image]
    for n in range(nmasks):
        files += ['-var', "m%d" % (n), masks[n]]

    command = ['wb_command', '-cifti-math'] + ex + [output] + files

    if subprocess.call(command):
        raise ValueError("ERROR: Running wb_command failed! Call: %s" % (" ".join(command)))

