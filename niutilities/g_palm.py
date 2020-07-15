#!/usr/bin/env python2.7
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
import niutilities.g_exceptions as ge
import re

def runPALM(image, design=None, args=None, root=None, options=None, parelements=None, overwrite='no', cleanup='yes'):
    '''
    runPALM image=<image file(s)> [design=<design string>] [args=<arguments string>] [root=<root name for the output>] [options=<options string>] [parelements=<number of elements to run in parallel>] [overwite=no] [cleanup=yes]

    USE
    ===

    Runs second level analysis using PALM permutation resampling. It provides a
    simplifed interface, especially when running the analyses on grayordinate,
    CIFTI images. In this case the .dtseries.nii file will be split up into left
    and right surface and volume files, PALM will be run on each of them
    independently and in parallel, and all the resulting images will be then
    stitched back together in a single .dscalar.nii image file.

    For volume images a standard MNI brain mask will be used. For CIFTI dtseries
    images, a standard atlas 32k midthickness will be used for surface data and
    the appropriate mask for volume data. In case of ptseries no mask or surface
    will be used. In the latter case no surface or volume based statistics (e.g.
    TFCE or clustering extent/mass) should be specified.

    For ptseries it might be necessary to specify transposedata in argument
    string for the data to be interpreted correctly.


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

    --image: Image file(s) 
    ----------------------

    One or multiple files can be specified as input. If multiple files are
    specified, they will be all passed to PALM. If they are cifti files, they
    will be split into separate structures and run in parallel. To specify
    multiple files, separate them with pipe ("|") character and take care to
    put the whole string with files in quotes. Also, if specifying multiple
    files, do take care, that they are of the same format (nifti, cifti) and
    do specify the relevant additional parameters (see below) that are relevant
    for multimodal testing.

    Example string for multiple files:

    image="rs_connectivity.dtseries.nii|task_activation.dtseries.nii"

    --design: Design string
    -----------------------

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

    Do take into account that the design files are looked for from the location
    in which you are running the command from. If they are in a different
    location, then "name" has to specify the full path!

    Example design string and files
    -------------------------------

    design='name:sustained|t:taov'

    In this case the following files would be expected:

    * sustained_d.csv      (design matrix file)
    * sustained_eb.csv     (exchangebility blocks file)
    * sustained_taov.csv   (t-contrasts file)
    * sustained_f.csv      (f-contrasts file)

    design='name:designs/transient|t:faov|f:fmain'

    In this case the following files would be expected:

    * designs/transient_d.csv      (design matrix file)
    * designs/transient_eb.csv     (exchangebility blocks file)
    * designs/transient_taov.csv   (t-contrasts file)
    * designs/transient_fmain.csv  (f-contrasts file)


    --arg: Additional arguments to PALM
    -----------------------------------

    Additional arguments to palm can be specified using the arguments string.
    The arguments string is a pipe separated list of arguments and optional
    values. The format of the string is:

    "<arg 1>|<arg 2>|<arg 3>:<value 1>:<value 2>|<arg 4>:<value>".

    The default arguments and values are: "n:100|zstat", which specify that
    100 permutations should be run and the statistics of interest expressed in
    z values. To exclude a default argument, specify "<arg>:remove", e.g.:
    "zstat:remove" if the statistics are not to be converted to z values.

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

    TFCE specific additional arguments
    ----------------------------------

    Sometimes it is desired to specify TFCE parameters that differ from the
    default values. As the function allows combined surface/volume processing
    of cifti files, it is useful to be able to set them separately for 2D and
    3D analysis. runPALM therefore provides two additional optional parameters
    that are separately expanded to TFCE 2D and 3D settings:

    T2DHEC  : sets H, E and C parameters for 2D part of analysis
    T3DHEC  : sets H, E and C parameters for 3D part of analysis

    All three values need to be provided when the parameter is specified, for
    example:

    args="T2HEC:2:0.5:26|T3DHEC:4:1:6"

    If these two parameters are not specified, the default values specified by
    PALM are used, specifically, H=2, E=1, C=26 for 2D analysis and H=2, E=0.5
    for 3D analysis (C value is not listed in PALM documentation).

    Example additional arguments
    ----------------------------

    args="n:500|accel:tail|T|fonly"

    In this case PALM would run 500 permutations and the p-values would be
    estimated by a help of the tail estimation acceleration method, TFCE
    inference would be used, and only f-contrasts would be computed.

    Additional optional parameters
    ------------------------------
    
    --options       : a | separate string of additional options to be passed to the
                      command, e.g. specify 'surface' if only left and right surfaces
                      from dtseries or dscalar files are to be analysed
    --root          : optional root name for the result images, design name is used
                      if the optional parameter is not specified
    --parelements   : number of elements to run in parallel for grayordinate
                      decomposition, all available elements (3 max for left surface,
                      right surface and volume files) will be used if not specified.
    --overwrite     : whether to remove preexisting image files, if they exists, the
                      command will exit with a warning if there are preexiting files
                      and overwrite is set to 'no' (the default)
    --cleanup       : should the command clean all the temporary generated files or
                      not before the command exits [yes]

    Example use
    -----------
    
    ```
    qunex runPALM design="name:sustained|t:taov" args="n:500|accel:tail|T|fonly" \\
         root=sustained_aov
    ```

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-06 Grega Repovš
             - Updated documentation.
    2017-05-01 Grega Repovš
             - Added custom 2D/3D specification of TFCE parameters
    2017-05-09 Grega Repovš
             - Added ability to specify multiple image files for multimodal
               analysis.
    2017-07-21 Grega Repovš
             - Added ability to run ptseries CIFTI images.
    2017-09-28 Grega Repovš
             - Updated documentation regarding location of design files.
    2017-10-20 Grega Repovš
             - Added cleaning of preexisting image files.
    2018-03-06 Grega Repovš
            - Correction to documentation
    2018-07-26 Grega Repovš
            - Corrected for new locations of templates
    2018-09-10 Grega Repovš
            - Added additional options and surface only processing
    2019-01-25 Grega Repovš
            - Added cleanup option
    '''

    print "Running PALM\n============"
    print " --> checking environment"

    if not "QUNEXPATH" in os.environ:
        raise ge.CommandError("runPALM", "QUNEXPATH environment variable not set.", "Can not find HCP Template files!")
    atlas = os.path.join(os.environ['QUNEXPATH'], 'library', 'data', 'atlases')

    # --- check for number of input files

    images  = [e.strip() for e in image.split('|')]
    nimages = len(images)

    # --- parse design options

    print " --> parsing design options"

    doptions = {'name': 'palm', 'd': 'd', 't': 't', 'f': 'f', 'eb': 'eb'}

    if design is not None:
        design = [e.split(':') for e in design.split('|')]
        for k, v in design:
            doptions[k.strip()] = v.strip()

    if root is None:
        root = doptions['name']

    # --- check for preexisting files

    files = glob.glob(root + '*.nii') + glob.glob(root + '*.nii.gz') + glob.glob(root + '*.gii')
    if len(files) > 0:
        if overwrite == 'yes':
            print " --> cleaning up preexisiting image files"
            for file in files:
                print "     ... removing %s" % file
                os.remove(file)
        else:
            raise ge.CommandFailed("runPALM", "Preexisting image files", "There are preexisting image files with the specified root.", "Please inspect and remove them to prevent conflicts or specify 'overwrite=yes'!")

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

    print " --> checking input"

    for image in images:
        if not os.path.exists(image):
            raise ge.CommandFailed("runPALM", "Missing file", "The image file is missing: %s" % (image), "Please check your paths!")

    rfolder = os.path.dirname(root)
    if (rfolder != '') and (not os.path.exists(rfolder)):
        print "     ... creating target folder [%s]" % (rfolder)
        os.makedirs(rfolder)

    # missing = []
    # for check in [image, design + '_d.csv', design + '_t.csv', design + '_eb.csv']:
    #     if not os.path.exists(check):
    #         missing.append(check)
    # if missing:
    #     print "WARNING: The following design files are missing and will be omitted: %s." % (", ".join(missing))
    #     return

    if options is None:
        options = []
    else:
        options = [e.strip() for e in options.split('|')]


    # --- setup and run

    toclean   = [];
    cnum = re.compile('.*_c([0-9]+).gii')
    mnum = re.compile('.*_m([0-9]+)_')

    try:

        # --- prepare input files and arguments

        c = 0
        for image in images:
            c += 1
            troot = "%s_i%d" % (root, c)

            if '.nii.gz' in image:
                simage = troot + '_volume.nii'

                print " --> ungzipping %s" % (image)
                with gzip.open(image, 'rb') as f_in, open(simage, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                toclean.append(simage)
                iformat = 'nifti'

            elif '.ptseries.nii' in image:
                simage = troot + '_cifti.ptseries.nii'
                shutil.copy(image, simage)
                toclean.append(simage)
                iformat = 'ptseries'

            elif '.dtseries.nii' in image or '.dscalar.nii' in image:
                print " --> decomposing %s" % (image)
                if 'surface' in options:
                    command = ['wb_command', '-cifti-separate', image, 'COLUMN',
                        '-metric', 'CORTEX_LEFT', troot + '_left.func.gii',
                        '-metric', 'CORTEX_RIGHT', troot + '_right.func.gii']
                else:
                    command = ['wb_command', '-cifti-separate', image, 'COLUMN',
                        '-volume-all', troot + '_volume.nii',                     # , '-roi', 'cifti_volume_mask.nii'
                        '-metric', 'CORTEX_LEFT', troot + '_left.func.gii',
                        '-metric', 'CORTEX_RIGHT', troot + '_right.func.gii']

                print " --> running:", " ".join(command)
                if subprocess.call(command):
                    print "ERROR: Command failed: %s" % (" ".join(command))
                    raise ValueError("ERROR: Command failed: %s" % (" ".join(command)))
                if 'surface' in options:
                    toclean += [troot + e for e in ['_left.func.gii', '_right.func.gii']]
                else:
                    toclean += [troot + e for e in ['_volume.nii', '_left.func.gii', '_right.func.gii']]
                iformat = 'dtseries'

            elif '.nii' in image:
                simage = troot + '_volume.nii'
                shutil.copy(image, simage)
                toclean.append(simage)
                iformat = 'nifti'

            else:
                raise ge.CommandFailed("runPALM", "Unsuported file format", "Unknown format of the input file [%s]!" % (image), "Please check your data!")

        # --- compile PALM command

        print " --> compiling PALM commands"

        # --- put together design related arguments

        dargs = []

        for f in ['d', 't', 'f', 'eb']:
            if doptions[f] is not "none":
                tfile = "%s_%s.csv" % (doptions['name'], doptions[f])
                if os.path.exists(tfile):
                    dargs += ['-' + f, tfile]
                    print "     ... %s file set to %s" % (f, tfile)
                else:
                    print "     ... %s file not found and won't be used [%s]" % (f, os.path.abspath(tfile))


        # --- check for additional parameters

        # -- custom 2D TFCE settings

        if 'T2DHEC' in arguments:
            t2hec = arguments.pop('T2DHEC')
            t2set = "-tfce_H %s -tfce_E %s -tfce_C %s" % (t2hec[0], t2hec[1], t2hec[2])
        else:
            t2set = "-tfce2D"

        # -- custom 3D TFCE settings

        if 'T3DHEC' in arguments:
            t3hec = arguments.pop('T3DHEC')
            t3set = "-tfce_H %s -tfce_E %s -tfce_C %s" % (t3hec[0], t3hec[1], t3hec[2])
        else:
            t3set = None

        # --- put together statistics and other related arguments

        sargs = []
        for k, v in arguments.iteritems():
            sargs += ['-' + k]
            if v is not None:
                sargs += v

        # --- run PALM

        if iformat == 'nifti':
            print " --> running PALM for NIfTI input"
            infiles = setInFiles(root, 'volume.nii', nimages)
            inargs  = ['-m', os.path.join(atlas, 'MNITemplates', 'MNI152_T1_2mm_brain_mask_dil.nii')]
            command = ['palm'] + infiles + inargs + dargs + sargs + ['-o', root + '_volume']
            if subprocess.call(command):
                raise ge.CommandFailed("runPALM", "PALM failed", "The PALM command failed to run: %s" % (" ".join(command)), "Please check your settings!")

        elif iformat == 'ptseries':
            print " --> running PALM for ptseries CIFTI input"
            infiles = setInFiles(root, 'cifti.ptseries.nii', nimages)
            command = ['palm'] + infiles + dargs + sargs + ['-o', root]
            if subprocess.call(command):
                raise ge.CommandFailed("runPALM", "PALM failed", "The PALM command failed to run: %s" % (" ".join(command)), "Please check your settings!")

        else:
            print " --> setting up PALM for dtseries/dscalar CIFTI input"
            calls = []

            if not 'surface' in options:
                print "     ... Volume"
                infiles = setInFiles(root, 'volume.nii', nimages)
                inargs  = ['-m', os.path.join(atlas, 'HCP', 'masks', 'volume.cifti.mask.nii')]
                command = ['palm'] + infiles + inargs + dargs + sargs + ['-o', root + '_volume']
                calls.append({'name': 'PALM Volume', 'args': command, 'sout': root + '_volume.log'})
                if '-T' in command and t3set is not None:
                    command += [t3set]

            print "     ... Left Surface"
            infiles = setInFiles(root, 'left.func.gii', nimages)
            inargs  = ['-m', os.path.join(atlas, 'HCP', 'masks', 'surface.cifti.L.mask.32k_fs_LR.func.gii'), '-s', os.path.join(atlas, 'HCP', 'Q1-Q6_R440.L.midthickness.32k_fs_LR.surf.gii')]
            command = ['palm'] + infiles + inargs + dargs + sargs + ['-o', root + '_L']
            if '-T' in command:
                command += [t2set]
            calls.append({'name': 'PALM Left Surface', 'args': command, 'sout': root + '_left_surface.log'})

            print "     ... Right Surface"
            infiles = setInFiles(root, 'right.func.gii', nimages)
            inargs  = ['-m', os.path.join(atlas, 'HCP', 'masks', 'surface.cifti.R.mask.32k_fs_LR.func.gii'), '-s', os.path.join(atlas, 'HCP', 'Q1-Q6_R440.R.midthickness.32k_fs_LR.surf.gii')]
            command = ['palm'] + infiles + inargs + dargs + sargs + ['-o', root + '_R']
            if '-T' in command:
                command += [t2set]
            calls.append({'name': 'PALM Right Surface', 'args': command, 'sout': root + '_right_surface.log'})

            print " --> running PALM for CIFTI input"

            completed = niutilities.g_core.runExternalParallel(calls, cores=parelements, prepend='     ... ')

            errors = []
            for complete in completed:
                if complete['exit']:
                    errors.append(complete)

            if errors:
                report = ["PALM failed", "The following PALM calls failed:"]
                for error in errors:
                    report.append("- %s [%s]" % (error['name'], error['log']))
                report.append("Aborting further processing, please check files and logs!")
                raise ge.CommandFailed("runPALM", *report)

        # --- process output

        if iformat in ['nifti', 'ptseries']:
            pass
        else:
            print " --> reconstructing results into CIFTI files"

            for pval in ['_fdrp', '_cfdrp', '_mfdrp', '_mcfdrp', '_fwep', '_uncp', '_mfwep', '_cfwep', '_mcfwep', 'uncparap', 'fdrparap', '']:
                for stat in ['tstat', 'fstat', 'vstat', 'gstat', 'rstat', 'rsqstat',
                             'mv_tstat', 'mv_fstat', 'mv_vstat', 'mv_gstat', 'mv_rstat', 'mv_rsqstat', 'mv_tsqstat', 'mv_hotellingtsq',
                             'ztstat', 'zfstat', 'zvstat', 'zgstat', 'zrstat', 'zrsqstat',
                             'zmv_tstat', 'zmv_fstat', 'zmv_vstat', 'zmv_gstat', 'zmv_rstat', 'zmv_rsqstat', 'zmv_tsqstat', 'zmv_hotellingtsq']:
                    for volumeUnit, surfaceUnit, unitKind in [('vox', 'dpv', 'reg'), ('tfce', 'tfce', 'tfce'), ('clustere', 'clustere', 'clustere'), ('clusterm', 'clusterm', 'clusterm')]:
                        rvolumes       = glob.glob("%s_volume_%s_%s%s*.nii" % (root, volumeUnit, stat, pval))
                        rleftsurfaces  = glob.glob("%s_L_%s_%s%s*.gii" % (root, surfaceUnit, stat, pval))
                        rrightsurfaces = glob.glob("%s_R_%s_%s%s*.gii" % (root, surfaceUnit, stat, pval))
                        # print " ... testing for: ", "%s_volume_%s_%s%s*.nii" % (root, volumeUnit, stat, pval), "found:", len(rvolumes)

                        rvolumes.sort()
                        rleftsurfaces.sort()
                        rrightsurfaces.sort()

                        if 'surface' in options:
                            if rleftsurfaces:
                                if len(rleftsurfaces) != len(rrightsurfaces):
                                    print "     ... WARNING: Nonmatching number of resulting surface files, please check PALM log for errors!"
                                    continue    
                        else:
                            if rvolumes:
                                if len(rvolumes) != len(rleftsurfaces) or len(rvolumes) != len(rrightsurfaces):
                                    print "     ... WARNING: Nonmatching number of resulting volume and surface files, please check PALM log for errors!"
                                    continue

                        while rleftsurfaces:
                            if 'surface' not in options:
                                rvolume       = rvolumes.pop(0)
                            rleftsurface  = rleftsurfaces.pop(0)
                            rrightsurface = rrightsurfaces.pop(0)

                            # --- get the contrast number
                            C = cnum.match(rleftsurface)
                            if C is None:
                                C = '0'
                            else:
                                C = C.group(1)

                            # --- get the modality number
                            M = mnum.match(rleftsurface)
                            if M is None:
                                M = ''
                            else:
                                M = '_M%s' % (M.group(1))

                            # --- compile target name
                            targetfile     = "%s_%s_%s%s%s_C%s.dscalar.nii" % (root, unitKind, stat, pval, M, C)
                            print "     ... creating", targetfile,

                            # --- and func to gii
                            os.rename(rleftsurface, rleftsurface.replace('.gii', '.func.gii'))
                            os.rename(rrightsurface, rrightsurface.replace('.gii', '.func.gii'))
                            rleftsurface = rleftsurface.replace('.gii', '.func.gii')
                            rrightsurface = rrightsurface.replace('.gii', '.func.gii')

                            if 'surface' in options:
                                command = ['wb_command', '-cifti-create-dense-scalar', targetfile,
                                           '-left-metric', rleftsurface, '-roi-left', os.path.join(atlas, 'HCP', 'standard_mesh_atlases', 'L.atlasroi.32k_fs_LR.shape.gii'),
                                           '-right-metric', rrightsurface, '-roi-right', os.path.join(atlas, 'HCP', 'standard_mesh_atlases', 'R.atlasroi.32k_fs_LR.shape.gii')]
                            else:
                                command = ['wb_command', '-cifti-create-dense-scalar', targetfile,
                                           '-volume', rvolume, os.path.join(atlas, 'HCP', 'standard_mesh_atlases', 'Atlas_ROIs.2.nii.gz'),
                                           '-left-metric', rleftsurface, '-roi-left', os.path.join(atlas, 'HCP', 'standard_mesh_atlases', 'L.atlasroi.32k_fs_LR.shape.gii'),
                                           '-right-metric', rrightsurface, '-roi-right', os.path.join(atlas, 'HCP', 'standard_mesh_atlases', 'R.atlasroi.32k_fs_LR.shape.gii')]
                            if subprocess.call(command):
                                raise ge.CommandFailed("runPALM", "Create cifti failed", "wb_command creating cifti file failed", "The command ran: %s" % (" ".join(command)))

                            if os.path.exists(targetfile):
                                print "... done!"
                                if not 'surface' in options:
                                    os.remove(rvolume)
                                os.remove(rleftsurface)
                                os.remove(rrightsurface)
                            else:
                                print "... ops! File was not created!"

    except:
        if cleanup == "yes":
            for f in toclean:
                if os.path.exists(f):
                    os.remove(f)
        raise

    # ---- cleanup

    if cleanup == "yes":
        for f in toclean:
            if os.path.exists(f):
                os.remove(f)


def setInFiles(root, tail, nimages):
    out = []
    for n in range(nimages):
        out += ['-i', "%s_i%d_%s" % (root, n + 1, tail)]
    return out


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
    
    ```
    qunex maskMap image=sustained_anova_reg_zfstat_C0.dscalar.nii \\
        masks="FU3s_sustained_anova_tfce_zfstat_fwep_C0.dscalar.nii" \\
        maxv=0.017
    ```

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-06 Grega Repovš
             - Updated documentation.
    '''

    print "Running maskMap\n==============="

    # --- process the arguments

    if image is None:
        raise ge.CommandError("maskMap", "No image file specified", "Please provide path to input image for masking!")
    elif not os.path.exists(image):
        raise ge.CommandFailed("maskMap", "Image file not found", "Input image file for masking was not found!", "Please check path [%s]" % (image))

    if masks is None:
        raise ge.CommandError("maskMap", "No mask file specified", "Please provide path to file(s) used as mask(s)!")
    masks = [e.strip() for e in masks.split(',')]
    for mask in masks:
        if not os.path.exists(mask):
            raise ge.CommandFailed("maskMap", "Mask file not found", "Mask file for masking was not found!", "Please check path [%s]" % (mask))
    nmasks = len(masks)

    if output is None:
        output = 'Masked_' + image

    if minv is None and maxv is None:
        raise ge.CommandError("maskMap", "Missing parameters", "At least `minv` or `maxv` need to be specified!")

    if minv is not None:
        minv = [float(e) for e in minv.split(',')]
        if len(minv) == 1:
            minv = [minv[0] for e in range(nmasks)]
        elif len(minv) != nmasks:
            raise ge.CommandError("maskMap", "Missmatch in input", "Number of provided minimum values does not match number of masks!", "Please check your parameters!")

    if maxv is not None:
        maxv = [float(e) for e in maxv.split(',')]
        if len(maxv) == 1:
            maxv = [maxv[0] for e in range(nmasks)]
        elif len(maxv) != nmasks:
            raise ge.CommandError("maskMap", "Missmatch in input", "Number of provided maximum values does not match number of masks!", "Please check your parameters!")


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
        raise ge.CommandFailed("maskMap", "Running wb_command failed", "Call: %s" % (" ".join(command)))


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
    
    ```
    qunex joinMaps images="sustained_AvsB_p.017.dscalar.nii, \\
                          sustained_BvsC_p.017.dscalar.nii, \\
                          sustained_AvsC_p.017.dscalar.nii, \\
                          sustained_aov_p.017.dscalar.nii" \\
                  names="A > B, B > C, A > C, ANOVA" \\
                  output="sustained_results.dscalar.nii" \\
                  originals=remove
    ```

    ----------------
    Written by Grega Repovš

    Changelog
    2017-02-06 Grega Repovš
             - Updated documentation.
    '''

    print "Running joinMaps\n================"

    # --- process the arguments

    if images is None:
        raise ge.CommandError("joinMaps", "No image files specified", "Please provide path to input images for joining!")
    images = [e.strip() for e in images.split(',')]
    for image in images:
        if not os.path.exists(image):
            raise ge.CommandFailed("joinMaps", "Image file not found", "The specified image file was not found!", "Please check path [%s]" % (image))
    nimages = len(images)

    if output is None:
        raise ge.CommandError("joinMaps", "No output file specified", "Please provide path to desired output image file!")

    if names is not None:
        names = [e.strip() for e in names.split(',')]
        if len(names) != nimages:
            raise ge.CommandError("joinMaps", "Mismatch in input", "List of map names (%d names) does not match the number of maps (%d)! " % (len(names), nimages))

    # --- build the expression and merge files

    command = ['wb_command', '-cifti-merge', output]

    for image in images:
        command += ['-cifti', image]

    print " --> Merging maps"
    if subprocess.call(command):
        raise ge.CommandFailed("joinMaps", "Merging maps failed", "Running wb_command failed", "Call: %s" % (" ".join(command)))

    # --- build the expression and name maps

    if names is not None:
        command = ['wb_command', '-set-map-names', output]
        m = 0
        for name in names:
            m += 1
            command += ['-map', str(m), name]

        print " --> Naming maps"
        if subprocess.call(command):
            raise ge.CommandFailed("joinMaps", "Naming maps failed", "Running wb_command failed", "Call: %s" % (" ".join(command)))

    # --- remove originals

    if (originals is not None) and (originals == "remove"):
        print " --> Removing originals"
        for image in images:
            os.remove(image)



#
def fNuissance(n):
    '''Support function for createWSPALMDesign function.'''
    ndummy = n - 1
    block  = []
    for e in range(n):
        if e == 0:
            block.append([-1 for j in range(ndummy)])
        else:
            t = [0 for j in range(ndummy)]
            t[e - 1] = 1
            block.append(t)
    return block


def createWSPALMDesign(factors=None, nsubjects=None, root=None):
    '''
    createWSPALMDesign factors=<factor string> nsubjects=<number of subjects> root=<design root name>

    USE
    ===

    createWSPALMDesign prepares design file, t-contrasts, f-contrasts and
    exchangebility block files for a single group within-subject PALM designs.
    It supports full factorial designs with up to three factors.

    The function assumes the data to be organized by subject and the first
    specified factor to be the slowest varying one. The factors, their
    interactions and subject intercepts will be specified in the following
    order in the design matrix:

    1 factor design:
    F1, subjects

    2 factor design:
    F1, F2, F1*F2, subjects

    3 factor design:
    F1, F2, F3, F1*F2, F1*F3, F2*F3, F1*F2*F3, subjects

    4 factor design:
    F1, F2, F3, F4, F1*F2, F1*F3, F1*F4, F2*F3, F2*F4, F3*F4, F1*F2*F3, F1*F2*F4, F2*F3*F4, F1*F2*F3*F4, subjects

    t-tests will be specified in order and f-tests will be specified in the same
    order as above.

    PARAMETERS
    ==========

    --factors    ... A comma separated list of number of factor levels.
    --nsubjects  ... Number of subjects.
    --root       ... Root name for the created files ['wspalm'].

    EXAMPLE USE
    ===========
    
    ```
    qunex createWSPALMDesign factors="2,3" nsubjects=33 root=WM.type_by_load
    ```

    ----------------
    Written by Grega Repovš, 2017-07-14'''

    if factors is None:
        raise ge.CommandError("createWSPALMDesign", "Missing parameter", "No factors specified!", "Please, check your command!")
    factors = [int(e) for e in factors.split(',')]

    if nsubjects is None:
        raise ge.CommandError("createWSPALMDesign", "Missing parameter", "Number of subjects not specified!", "Please, check your command!")
    nsubjects = int(nsubjects)

    if root is None:
        root = 'wspalm'

    dvars    = [e - 1 for e in factors]
    nfactors = len(factors)
    blocks   = []
    nlevels  = reduce(lambda x, y: x * y, factors)

    for n in factors:
        blocks.append(fNuissance(n))

    # -------------------------------------------------------------
    #                                            create design file

    df = open(root + '_d.csv', 'w')

    for s in range(nsubjects):
        sline = [0 for e in range(nsubjects)]
        sline[s] = 1

        # ---- 1 factor within design

        if nfactors == 1:
            for f1l in blocks[0]:
                line = f1l + sline
                print >> df, ",".join([str(e) for e in line])

        # ---- 2 factor within design

        if nfactors == 2:
            for f1l in blocks[0]:
                for f2l in blocks[1]:
                    line = f1l + f2l

                    # --- compute and add interactions
                    i12 = [i * j for i in f1l for j in f2l]

                    line += i12

                    # --- add subject intercepts

                    line += sline

                    # --- print it out

                    print >> df, ",".join([str(e) for e in line])


        # ---- 3 factor within design

        elif nfactors == 3:

            for f1l in blocks[0]:
                for f2l in blocks[1]:
                    for f3l in blocks[2]:

                        # --- join main effects
                        line = f1l + f2l + f3l

                        # --- compute and add interactions
                        i12 = [i * j for i in f1l for j in f2l]
                        i13 = [i * j for i in f1l for j in f3l]
                        i23 = [i * j for i in f2l for j in f3l]
                        i123 = [i * j * k for i in f1l for j in f2l for k in f3l]

                        line += i12 + i13 + i23 + i123

                        # --- add subject intercepts

                        line += sline

                        # --- print it out

                        print >> df, ",".join([str(e) for e in line])


        # ---- 4 factor within design

        elif nfactors == 4:

            for f1l in blocks[0]:
                for f2l in blocks[1]:
                    for f3l in blocks[2]:
                        for f4l in blocks[3]:

                            # --- join main effects
                            line = f1l + f2l + f3l + f4l

                            # --- compute and add interactions
                            i12 = [i * j for i in f1l for j in f2l]
                            i13 = [i * j for i in f1l for j in f3l]
                            i14 = [i * j for i in f1l for j in f4l]

                            i23 = [i * j for i in f2l for j in f3l]
                            i24 = [i * j for i in f2l for j in f4l]

                            i34 = [i * j for i in f3l for j in f4l]

                            i123 = [i * j * k for i in f1l for j in f2l for k in f3l]
                            i124 = [i * j * k for i in f1l for j in f2l for k in f4l]
                            i234 = [i * j * k for i in f2l for j in f3l for k in f4l]

                            i1234 = [i * j * k * l for i in f1l for j in f2l for k in f3l for l in f3l]

                            line += i12 + i13 + i14 + i23 + i24 + i34 + i123 + i124 + i234 + i1234

                            # --- add subject intercepts

                            line += sline

                            # --- print it out

                            print >> df, ",".join([str(e) for e in line])

    df.close()


    # -------------------------------------------------------------
    #                              create exchangibility block file

    ebf = open(root + '_eb.csv', 'w')
    for s in range(nsubjects):
        for l in range(nlevels):
            print >> ebf, s + 1


    # -------------------------------------------------------------
    #                                       create t-contrasts file

    # --- calculate number of factor variables

    if nfactors == 1:
        tlen = dvars

    elif nfactors == 2:
        tlen = dvars + [dvars[0] * dvars[1]]

    elif nfactors == 3:
        tlen = dvars + [dvars[0] * dvars[1], dvars[0] * dvars[2], dvars[1] * dvars[2], dvars[0] * dvars[1] * dvars[2]]

    elif nfactors == 4:
        tlen = dvars + [dvars[0] * dvars[1], dvars[0] * dvars[2], dvars[0] * dvars[3], dvars[1] * dvars[2], dvars[1] * dvars[3], dvars[2] * dvars[3],
                        dvars[0] * dvars[1] * dvars[2], dvars[0] * dvars[1] * dvars[3], dvars[1] * dvars[2] * dvars[2],
                        dvars[0] * dvars[1] * dvars[2] * dvars[3]]

    ndvars = sum(tlen)

    # --- open and save t-contralst file

    tf = open(root + '_t.csv', 'w')

    for l in range(ndvars):
        line = [0 for e in range(ndvars + nsubjects)]
        line[l] = 1
        print >> tf, ",".join([str(e) for e in line])
    tf.close()

    # -------------------------------------------------------------
    #                                       create f-contrasts file

    fperd = {1: 1, 2: 3, 3: 7, 4: 14}
    nfac  = fperd[nfactors]
    code  = {True: 1, False: 0}

    ff = open(root + '_f.csv', 'w')
    for l in range(nfac):
        line = [code[l == e] for e in range(nfac) for i in range(tlen[e])]
        print >> ff, ",".join([str(e) for e in line])
    ff.close()

