#!/opt/local/bin/python2.7
# encoding: utf-8
"""
This file holds code for running PALM second level analyses, CIFTI map masking
and concatenation. The specific commands implemented here are:

* runPALM  ... for running PALM resampling
* maskMap  ... for masking results
* joinMaps ... for joining individual cifti maps into named concatencated maps

The functions are to be run using the gmri terminal command.

Created by Grega Repovs on 2016-08-30.
Copyright (c) Grega Repovs. All rights reserved.
"""

import os
import os.path
import subprocess
import gzip
import shutil
import glob
import niutilities
import re


def runPALM(image, design=None, args=None, root=None, cores=None):
    '''
    runPALM image=<image file> [design=<design string>] [args=<arguments string>] [root=<root name for the output>] [cores=<number of cores to use in parallel>]

    USE
    ===

    Runs second level analysis using PALM permutation resampling. It provides a
    simplifed interface, especially when running the analyses on grayordinate,
    CIFTI images. In this case the .dtseries.nii file will be split up into left
    and right surface and volume files, PALM will be run on each of them
    independently and in parallel, and all the resulting images will be then
    stitched back together in a single .dscalar.nii image file.


    REQUIREMENTS
    ============

    For the PALM processing to run successfully, the input image and the design
    files need to be prepared and match. Specifically, the input image file
    should hold first level results (e.g. GLM beta estimates or functional
    connectivity seed-maps) for all the subjects and conditions. For activation
    analyses a simple way to generate such a file is to use g_ExtractGLMVolumes
    matlab function.

    Design files
    ------------

    When only a t-test against zero is run across all the volumes in the image,
    no design files are needed, in all other cases some or all of the design
    files need to be prepared:

    * design matrix file (d)
    * exchangibility blocks file (eb)
    * t-contrasts file (t)
    * f-contrast file (f)

    The files should be named using the following convention. All the files
    should start with the same root, the design name, followed by an underscore
    then a tail that specifies the content of the file and the '.csv' extension.
    The files are expected to be matrices in the comma separated values format.


    PARAMETERS
    ==========

    Design string
    -------------

    The design name and the specififc tails (if the defaults are not used) are
    specified by a design string. Design string is a pipe separated list of
    key:value pairs that specify the following (with the defaults in the
    brackets):

    * name : the root name of the design files [palm]
    * d    : the design matrix file tail [d]
    * t    : the t-contrasts file tail [t]
    * f    : the f-contrasts file tail [f]
    * eb   : the exchange blocks file tail [eb]

    If "none" is given as value, that file is not to be specified and used.

    Example design string and files
    -------------------------------

    design='name:sustained|t:taov'

    In this case the following files would be expected:

    * sustained_d.csv      (design matrix file)
    * sustained_eb.csv     (exchangebility blocks file)
    * sustained_taov.csv   (t-contrasts file)
    * sustained_f.csv      (f-contrasts file)

    Additional arguments to PALM
    ----------------------------

    Additional arguments to palm can be specified using the arguments string.
    The arguments string is a pipe separated list of arguments and optional
    values. The format of the string is:

    "<arg 1>|<arg 2>|<arg 3>:<value 1>:<value 2>|<arg 4>:<value>".

    The default arguments and values are: "n:100|zstats", which specify that
    100 permutations should be run and the statistics of interest expressed in
    z values. To exclude a default argument, specify "<arg>:remove", e.g.:
    "zstats:remove" if the statistics are not to be converted to z values.

    For full list of possible arguments and values, please consult PALM user
    guide. Some relevant arguments to consider:

    accel   : methods to accelerate analysis. Possible values are:
              - noperm  : do not do any permutations (works with fdr correction only)
              - tail    : estimates tail of the permuted distribution, needs at least 100 resamples
              - negbin  : runs as many permutations an needed (works with fdr correction only)
              - gamma   : computes the moment of permutation distribution and fits a gamma function
              - lowrank : runs as many permutations as needed to complete matrix (fdr, fwer only)
    twotail : run two-tailed test for all the contrasts
    fonly   : run only f-contrasts and not the individual t-contrasts
    fdr     : compute a fdr correction for multiple comparisons
    T       : Enable TFCE inference
    C <z>   : Enable cluster inference for univariate tests with z cutoff

    Example additional arguments
    ----------------------------

    args="n:500|accel:tail|T|fonly"

    In this case PALM would run 500 permutations and the p-values would be
    estimated by a help of the tail estimation acceleration method, TFCE
    inference would be used, and only f-contrasts would be computed.

    Additional optional parameters
    ------------------------------

    * root  : optional root name for the result images, design name is used if
              the optional parameter is not specified
    * cores : number of cores to use in parallel for grayordinate decomposition,
              all available cores (3 max for left surface, right surface and
              volume files) will be used if not specified

    Example use
    -----------

    gmri runPALM design="name:sustained|t:taov" args="n:500|accel:tail|T|fonly" \\
         root=sustained_aov

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-06 Grega Repovš
             - Updated documentation.

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
    cnum = re.compile('.*_c([0-9]+).nii')

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
            print " --> setting up PALM for CIFTI input"
            calls = []

            print "     ... Volume"
            inargs  = ['-i', root + '_volume.nii', '-m', os.path.join(atlas, 'masks', 'volume.cifti.mask.nii')]
            command = ['palm'] + inargs + dargs + sargs + ['-o', root + '_volume']
            calls.append({'name': 'PALM Volume', 'args': command, 'sout': root + '_volume.log'})

            print "     ... Left Surface"
            inargs  = ['-i', root + '_left.func.gii', '-m', os.path.join(atlas, 'masks', 'surface.cifti.L.mask.32k_fs_LR.func.gii'), '-s', os.path.join(atlas, 'Q1-Q6_R440.L.midthickness.32k_fs_LR.surf.gii')]
            command = ['palm'] + inargs + dargs + sargs + ['-o', root + '_L']
            if '-T' in command:
                command += ['-tfce2D']
            calls.append({'name': 'PALM Left Surface', 'args': command, 'sout': root + '_left_surface.log'})

            print "     ... Right Surface"
            inargs  = ['-i', root + '_right.func.gii', '-m', os.path.join(atlas, 'masks', 'surface.cifti.R.mask.32k_fs_LR.func.gii'), '-s', os.path.join(atlas, 'Q1-Q6_R440.R.midthickness.32k_fs_LR.surf.gii')]
            command = ['palm'] + inargs + dargs + sargs + ['-o', root + '_R']
            if '-T' in command:
                command += ['-tfce2D']
            calls.append({'name': 'PALM Right Surface', 'args': command, 'sout': root + '_right_surface.log'})

            print " --> running PALM for CIFTI input"

            done = niutilities.g_core.runExternalParallel(calls, cores=cores, prepend='     ... ')

        # --- process output

        if iformat == 'nifti':
            pass
        else:
            print " --> reconstructing results into CIFTI files"

            for pval in ['_fdrp', '_fwep', '_uncp', '']:
                for stat in ['tstat', 'fstat', 'ztstat', 'zfstat']:
                    for volumeUnit, surfaceUnit, unitKind in [('vox', 'dpv', 'reg'), ('tfce', 'tfce', 'tfce'), ('clustere', 'clustere', 'clustere'), ('clusterm', 'clusterm', 'clusterm')]:
                        rvolumes       = glob.glob("%s_volume_%s_%s%s*.nii" % (root, volumeUnit, stat, pval))
                        rleftsurfaces  = glob.glob("%s_L_%s_%s%s*.gii" % (root, surfaceUnit, stat, pval))
                        rrightsurfaces = glob.glob("%s_R_%s_%s%s*.gii" % (root, surfaceUnit, stat, pval))

                        rvolumes.sort()
                        rleftsurfaces.sort()
                        rrightsurfaces.sort()

                        while rvolumes:
                            rvolume       = rvolumes.pop(0)
                            rleftsurface  = rleftsurfaces.pop(0)
                            rrightsurface = rrightsurfaces.pop(0)

                            # --- get the contrast number
                            C = cnum.match(rvolume)
                            if C is None:
                                C = '0'
                            else:
                                C = C.group(1)

                            # --- compile target name
                            targetfile     = "%s_%s_%s%s_C%s.dscalar.nii" % (root, unitKind, stat, pval, C)
                            print "     ... creating", targetfile,

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



def maskMap(image=None, masks=None, output=None, minv=None, maxv=None, join='OR'):
    '''
    maskMap image=<image file> masks=<list of masks to use> [output=<output image name>] [minv=<list of thresholds>] [maxv=<list of thresholds>] [join=<OR or AND>]

    USE
    ===

    maskMap is a wb_command wrapper that enables easy masking of CIFTI images
    (e.g. ztstat image from PALM), using the provided list of mask files (e.g.
    p-values imaages from PALM) and thresholds. More than one mask can be used
    in which case they can be combined using a logical OR or AND operator.

    PARAMETERS
    ==========

    --image   ... The image file to be masked.
    --masks   ... A comma separated list of masks to be used.
    --output  ... An optional image name for the resulting masked image, if
                  none is provided the original image name will be used with
                  tail "_masked" appended.
    --minv    ... The minimum threshold value.
    --maxv    ... The maximum threshold value.
    --join    ... Whether multiple masks should be joined using logical OR or
                  logical AND operator. [OR]

    Join operation
    --------------

    If more than one mask is provided, the final mask used can be either the
    intersection of all the individual masks (logical AND) or a union of all
    the individual masks (logical OR).

    Thresholds
    ----------

    At least minv or maxv needs to be specified.

    If only minv is given, images will be masked with:  mask >= minv.
    If only maxv is given, images will be masked with:  mask <= maxv.
    If both are given, images will be masked with:      minv <= mask <= maxv

    If there is just one minv or maxv value, all the masks will be thresholded using the same value. If more values are
    provided as comma separated list, they should match the number of masks.

    EXAMPLE USE
    ===========

    gmri maskMap image=sustained_anova_reg_zfstat_C0.dscalar.nii \\
         masks="FU3s_sustained_anova_tfce_zfstat_fwep_C0.dscalar.nii" \\
         maxv=0.017

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-06 Grega Repovš
             - Updated documentation.
    '''

    # --- process the arguments

    if image is None:
        raise ValueError("ERROR: No image file was specified!")
    elif not os.path.exists(image):
        raise ValueError("ERROR: The specified image file does not exist! [%s]" % (image))

    if masks is None:
        raise ValueError("ERROR: No mask file was specified!")
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
            ex.append("(m%d <= %.3f)" % (n, maxv[n]))
        elif maxv is None:
            ex.append("(m%d >= %.3f)" % (n, minv[n]))
        else:
            ex.append("((m%d >= %.3f) * (m%d <= %.3f))" % (n, minv[n], maxv[n]))

    if join == 'OR':
        ex = ["((%s) > 0) * img" % (" + ".join(ex))]
    elif join == 'AND':
        ex = ["((%s) > 0) * img" % (" * ".join(ex))]

    files = ['-var', 'img', image]
    for n in range(nmasks):
        files += ['-var', "m%d" % (n), masks[n]]

    command = ['wb_command', '-cifti-math'] + ex + [output] + files

    if subprocess.call(command):
        raise ValueError("ERROR: Running wb_command failed! Call: %s" % (" ".join(command)))



def joinMaps(images=None, output=None, names=None, originals=None):
    '''
    joinMaps images=<image file list> output=<output file name> [names=<volume names list>] [originals=<remove or keep>]

    USE
    ===

    joinMaps is a wb_command wrapper that concatenates the listed cifti images
    and names the individual volumes, if names are provided.

    PARAMETERS
    ==========

    --images     ... A comma separated list of images to be concatenated
    --output     ... The name of the resulting file.
    --names      ... A comma separated list of image names.
    --originals  ... Whether to keep or remove the original images after the
                     concatenation. [keep]

    EXAMPLE USE
    ===========

    gmri joinMaps images="sustained_AvsB.dscalar_p.017.nii, \\
                          sustained_BvsC.dscalar_p.017.nii, \\
                          sustained_AvsC.dscalar_p.017.nii, \\
                          sustained_aov.dscalar_p.017.nii" \\
                  names="A > B, B > C, A > C, ANOVA" \\
                  output="sustained_results.dscalar.nii" \\
                  originals=remove

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-06 Grega Repovš
             - Updated documentation.
    '''

    # --- process the arguments

    if images is None:
        raise ValueError("ERROR: No input image file was specified!")
    images = [e.strip() for e in images.split(',')]
    for image in images:
        if not os.path.exists(image):
            raise ValueError("ERROR: The specified image file does not exist! [%s]" % (image))
    nimages = len(images)

    if output is None:
        raise ValueError("ERROR: No output image file was specified!")

    if names is not None:
        names = [e.strip() for e in names.split(',')]
        if len(names) != nimages:
            raise ValueError("ERROR: List of map names (%d names) does not match the number of maps (%d)! " % (len(names), nimages))

    # --- build the expression and merge files

    command = ['wb_command', '-cifti-merge', output]

    for image in images:
        command += ['-cifti', image]

    print " --> Merging maps"
    if subprocess.call(command):
        raise ValueError("ERROR: Running wb_command failed! Call: %s" % (" ".join(command)))

    # --- build the expression and name maps

    if names is not None:
        command = ['wb_command', '-set-map-names', output]
        m = 0
        for name in names:
            m += 1
            command += ['-map', str(m), name]

        print " --> Naming maps"
        if subprocess.call(command):
            raise ValueError("ERROR: Running wb_command failed! Call: %s" % (" ".join(command)))

    # --- remove originals

    if (originals is not None) and (originals == "remove"):
        print " --> Removing originals"
        for image in images:
            os.remove(image)

