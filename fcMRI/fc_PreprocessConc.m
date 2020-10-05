function [] = fc_PreprocessConc(subjectf, bolds, doIt, TR, omit, rgss, task, efile, eventstring, variant, overwrite, tail, scrub, ignores, options, done)

%function [] = fc_PreprocessConc(subjectf, bolds, doIt, TR, omit, rgss, task, efile, eventstring, variant, overwrite, tail, scrub, ignores, options, done)
%
%   Function for fcMRI preprocessing and GLM analysis a set of BOLD files.
%
%   INPUTS
%       subjectf ... A path to the subject's folder with images and data.
%       bolds    ... A vector of bold runs in the order of the conc file.
%       doIt     ... Which steps to perform and in what order ['s,h,r,c,l']:
%           s - spatial smoothing
%           h - highpass temporal filter
%           r - GLM estimation and regression of nuisance signals, with an
%               optional parameter (e.g. r0):
%               0 - separate nuisance, joint task regressors across runs [default]
%               1 - separate nuisance, separate task regressors for each run
%               2 - joint nuisance, joint task regressors across all runs
%           c - save coefficients in _Bcoeff file
%           p - save png image files of nusance ROI mask
%           l - lowpass temporal filter
%           m - motion scrubbing
%
%       TR        ... TR of the data [2.5]
%       omit      ... The number of frames to omit at the start of each bold []
%       rgss      ... A comma separated string specifying what to regress in the
%                     regression step ['m,V,WM,WB,1d']
%                       m   - motion
%                       V   - ventricles
%                       WM  - white matter
%                       WB  - whole brain
%                       1d  - first derivative for movement and nuisance signal regressors
%                       m1d - first derivative for movement regressors
%                       n1d - first derivative for nuisance signal regressors
%                       t   - task
%                       e   - events        
%       task        ... Matrix of custom regressors to be entered in GLM.
%       efile       ... Event (fild) file to be used for estimation of task regressors ['']
%       eventstring ... A string specifying the events to regress and the regressors to use ['']
%       variant     ... A string to be prepended to files ['']
%       overwrite   ... Whether old files should be overwritten [false]
%       tail        ... what file extension to expect and use for images ['.nii.gz']
%       scrub       ... the description of how to compute scrubbing - a string in 'param:value|param:value' format
%                       parameters:
%                       - radius   : head radius in mm [50]
%                       - fdt      : frame displacement threshold [0.5]
%                       - dvarsmt  : dvarsm threshold [3.0]
%                       - dvarsmet : dvarsme threshold [1.6]
%                       - after    : how many frames after the bad one to reject [0]
%                       - before   : how many frames before the bad one to reject [0]
%                       - reject   : which criteria to use for rejection (mov, dvars, dvarsme, idvars, udvars ...) [udvarsme]
%                       if empty, the defaults from mri_ComputeScrub are used.
%       ignores     - How to deal with the frames marked as not used in filering and regression steps
%                     specified in a single string, separated with pipes
%                     hipass  : keep / linear / spline
%                     regress : keep / ignore / mark / linear / spline
%                     lopass  : keep / linear /spline
%                     ['hipass:keep|regress:keep|lopass:keep']
%       options     - Additional options that can be set using the 'key=value|key=value' string:
%           boldname        : ['bold']
%           surface_smooth  : [6]
%           volume_smooth   : [6]
%           voxel_smooth    : [2]
%           lopass_filter   : [0.08]
%           hipass_filter   : [0.009]
%           framework_path  : ['']
%           wb_command_path : ['']
%           omp_threads     : [0]
%           smooth_mask     : ['false']
%           dilate_mask     : ['false']
%           glm_matrix      : ['none']  ('none' / 'text' / 'image' / 'both')
%           glm_residuals   : ['save']
%           glm_name        : ['']
%           bold_tail       : ['']
%           bold_variant    : ['']
%
%       done        - A path to a file to save to confirm all is a-ok. ['']
%
%
%   USE
%   ===
%
%   fc_PreprocessConc is a complex command initially used to prepare BOLD files
%   for further functional connectivity analysis. While it still accomplishes
%   that it can now also be used for complex activation modeling that creates
%   GLM files for further second-level analyses. The function enables the
%   following actions:
%
%   * spatial smoothing (3D or 2D for cifti files)
%   * temporal filtering (high-pass, low-pass)
%   * removal of nuisance signal
%   * complex modeling of events
%
%   The function makes use of a number of files and accepts a long list of
%   arguments that make it very powerfull and flexible but also require care in
%   its use. What follows is a detailed documentation of its actions and
%   parameters organised by actions in the order they would be most commonly
%   done. Use and parameter description will be intertwined.
%
%   BASICS
%   ======
%
%   Basics specify the files to use for processing and what to do. The relevant
%   parameters are:
%
%   - subjectf  ... Specifies the subject's base folder in which the function
%                   will look for all the other relevant files.
%   - bolds     ... Lists the numbers of the bold files to be processed. These
%                   have to match the order in which the bolds are specified in
%                   the .conc file and they have to match the order in which
%                   events follow in the .fidl file.
%   - do        ... The actions to be performed.
%   - overwrite ... Whether to overwrite the existing data or not.
%   - variant   ... A string to prepend to the list of steps done in the
%                   resulting files saved.
%   - tail      ... The file (format) extension (e.g. '.nii.gz').
%   - efile     ... The event (fidl) filename.
%
%   Important are also the following optional keys in the options parameter:
%
%   - boldname     ... Specifies, how the BOLD files are named in the
%                      images/functional folder.
%   - bold_tail    ... Specifies the additional tail that the bold name might
%                      have (see below).
%   - bold_variant ... Specifies a possible extension for the images/functional
%                      and images/segmentation/boldmasks folders
%
%   The files that will be processed / used are:
%
%   bolds           : <subjectf>/images/functional<bold_variant>/<boldname>[N]<bold_tail><tail>
%   movement data   : <subjectf>/images/functional<bold_variant>/movement/<boldname>_mov.dat
%   scrubbing data  : <subjectf>/images/functional<bold_variant>/movement/<boldname>.scrub
%   bold stats data : <subjectf>/images/functional<bold_variant>/movement/<boldname>.bstats
%   nuisance signal : <subjectf>/images/functional<bold_variant>/movement/<boldname>.nuisance
%   bold brain mask : <subjectf>/images/segmentation/boldmasks<bold_variant>/<boldname>[N]_frame1_brain_mask<tail>
%   event file      : <subjectf>/images/functional<bold_variant>/events/<efile>
%
%   The actions that can be performed are denoted by a single letter, and they
%   will be executed in the sequence listed:
%
%   m ... Motion scrubbing.
%   s ... Spatial smooting.
%   h ... High-pass filtering.
%   r ... Regression (nuisance and/or task) with an optional number 0, 1, or 2
%         specifying the type of regression to use (see REGRESSION below).
%   c ... Saving of resulting beta coefficients (allways to follow 'r').
%   l ... Low-pass filtering.
%
%   So the default 's,h,r,c,l' do parameter would lead to the image files
%   first being smoothed, then high-pass filtered. Next a regression step
%   would follow in which nuisance signal and/or task related signal would
%   be estimated and regressed out, then the related beta estimates would
%   be saved. Lastly the BOLDs would be also low-pass filtered.
%
%   SCRUBBING
%   =========
%
%   The function either makes use of scrubbing information or performs scrubbing
%   comuputation on its own (when 'm' is part of the command). In the latter
%   case, the scrubbing parameters need to be specified in the scrub string:
%
%   - radius  ... Estimated head radius (in mm) for computing frame
%                 displacement statistics [50].
%   - fd      ... Frame displacement threshold (in mm) to use for
%                 identifying bad frames [0.5]
%   - dvars   ... The (mean normalized) dvars threshold to use for
%                 identifying bad frames [3.0].
%   - dvarsme ... The (median normalized) dvarsm threshold to use for
%                 identifying bad frames [1.6].
%   - after   ... How many frames after each frame identified as bad
%                 to also exclude from further processing and analysis [0].
%   - before  ... How many frames before each frame identified as bad
%                 to also exclude from further processing and analysis [0].
%   - bad     ... Which criteria to use for identification of bad frames
%                 [udvarsme].
%
%   In any case, if scrubbing was done beforehand or as a part of this commmand,
%   one has to specify, how the scrubbing information is used by specifying it
%   in the ignores parameter string. The string has the following format:
%
%   'hipass:<filtering opt.>|regress:<regression opt.>|lopass:<filtering opt.>'
%
%   Filtering options are:
%
%   * keep   ... Keep all the bad frames unchanged.
%   * linear ... Replace bad frames with linear interpolated values based on
%                neighbouring good frames.
%   * spline ... Replace bad frames with spline interpolated values based on
%                neighouring good frames
%
%   To prevent artefacts present in bad frames to be temporaly spread, use
%   either 'linear' or 'spline' options.
%
%   Regression options are:
%
%   * keep   ... Keep the bad frames and use them in the regression.
%   * ignore ... Exclude bad frames from regression and keep the original
%                values in their place.
%   * mark   ... Exclude bad frames from regression and mark the bad frames
%                as NaN.
%   * linear ... Exclude bad frames from regression and replace them with
%                linear interpolation after regression.
%   * spline ... Exclude bad frames from regression and replace them with
%                spline interpolation after regression.
%
%   Please note that when the bad frames are ignored, the original values will
%   be retained in the residual signal. In this case they have to be excluded
%   or ignored also in all following analyses, otherwise they can be a
%   significant source of artefacts.
%
%   SPATIAL SMOOTHING
%   =================
%
%   Volume smoothing
%   ----------------
%
%   For volume formats the images will be smoothed using the mri_Smooth3D
%   gmrimage method. For cifti format the smooting will be done by calling the
%   relevant wb_command command. The smoothing specific parameters can be
%   set in the options string:
%
%   * voxel_smooth  ... Gaussian smoothing FWHM in voxels [2]
%   * smooth_mask   ... Whether to smooth only within a mask, and what mask to
%                       use (nonzero/brainsignal/brainmask/<filename>)[false].
%   * dilate_mask   ... Whether to dilate the image after masked smoothing and
%                       what mask to use (nonzero/brainsignal/brainmask/
%                       same/<filename>)[false].
%
%   If a smoothing mask is set, only the signal within the specified mask will
%   be used in the smoothing. If a dilation mask is set, after smoothing within
%   a mask, the resulting signal will be constrained / dilated to the specified
%   dilation mask.
%
%   For both optional string values the possibilities are:
%
%   * nonzero      ... Mask will consist of all the nonzero voxels of the first
%                      BOLD frame.
%   * brainsignal  ... Mask will consist of all the voxels that are of value
%                      300 or higher in the first BOLD frame (this gave a good
%                      coarse brain mask for images intensity normalized to
%                      mode 1000 in the NIL preprocessing stream).
%   * brainmask    ... Mask will be the actual bet extracted brain mask based
%                      on the first BOLD frame (generated using in the
%                      creatBOLDBrainMasks command).
%   * <filename>   ... All the non-zero voxels in a specified volume file will
%                      be used as a mask.
%   * false        ... No mask will be used.
%   * same         ... Only for dilate_mask, the mask used will be the same as
%                      smooting mask.
%
%   Cifti smoothing
%   ---------------
%
%   For cifti format images, smoothing will be run using wb_command. The
%   following parameters can be set in the options parameter:
%
%   * surface_smooth  ... FWHM for gaussian surface smooting in mm [6.0].
%   * volume_smooth   ... FWHM for gaussian volume smooting in mm [6.0].
%   * omp_threads     ... Number of cores to be used by wb_command. 0 for no
%                         change of system settings [0].
%   * framework_path  ... The path to framework libraries on the Mac system.
%                         No need to use it currently if installed correctly.
%   * wb_command_path ... The path to the wb_command executive. No need to
%                         use it currently if installed correctly.
%
%   Results
%   -------
%
%   The resulting smoothed files are saved with '_s' added to the BOLD root
%   filename.
%
%
%   TEMPORAL FILTERING
%   ==================
%
%   Temporal filtering is accomplished using mri_Filter gmrimage method. The
%   code is adopted from the FSL C++ code enabling appropriate handling of
%   bad frames (as described above - see SCRUBBING). The filtering settings
%   can be set in the options parameter:
%
%   * hipass_filter  ... The frequency for high-pass filtering in Hz [0.008].
%   * lopass_filter  ... The frequency for low-pass filtering in Hz [0.09].
%
%   Please note that the values finaly passed to mri_Filter method are the
%   respective sigma values computed from the specified frequencies and TR.
%
%   Results
%   -------
%
%   The resulting filtered files are saved with '_hpss' or '_bpss' added to the
%   BOLD root filename for high-pass and low-pass filtering, respectively.
%
%
%   REGRESSION
%   ==========
%
%   Regression is a complex step in which GLM is used to estimate the beta
%   weights for the specified nuisance regressors and events. The resulting
%   beta weights are then stored in a GLM file (a regular file with additional
%   information on the design used) and residuals are stored in a separate file.
%   This step can therefore be used for two puposes: (1) to remove nuisance
%   signal and event structure from BOLD files, removing unwanted potential
%   sources of correlation for further functional connectivity analyses, and
%   (2) to get task beta estimates for further activational analyses. The
%   following parameters are used in this step:
%
%   * rgss       ...  A comma separated list of regressors to include in GLM.
%                     Possible values are:
%                     * m  - motion parameters
%                     * m1d - motion derivatives
%                     * mSq  - squared motion parameters
%                     * m1dSq - squared motion derivatives
%                     * V  - ventricles signal
%                     * WM - white matter signal
%                     * WB - whole brain signal
%                     * n1d - first derivative of requested above nuisance
%                             signals (V, WM, WB)
%                     * 1d - first derivative of both movement regressors 
%                            and specified nuisance signal regressors
%                            (V, WM, WB)
%                     * e  - events listed in the provided fidl files (see
%                            above), modeled as specified in the event_string
%                            parameter.
%                     [m,V,WM,WB,1d]
%                     Note: `1d` implies `n1d` and `m1d`
%   * eventstring ... A string describing, how to model the events listed in
%                     the provided fidl files [].
%
%   Additionally, the following options can be set using the options string:
%
%   * glm_matrix     ... Whether to save the GLM matrix as a text file ('text'),
%                        a png image file ('image'), both ('both') or not
%                        ('none') [none].
%   * glm_residuals  ... Whether to save the residuals after GLM regression
%                        ('save') or not ('none') [save].
%   * glm_name       ... An additional name to add to the residuals and GLM
%                        files to distinguish between different possible models
%                        used.
%
%   GLM modeling
%   ------------
%
%   The exact GLM model used to estimate nuisance and task beta coefficients
%   and regress them from the signal is defined by the event string provided
%   by the eventstring parameter. The event string is a pipe ('|') separated
%   list of regressor specifications. The possibilities are:
%
%   __Unassumed Modelling__
%   <fidl code>:<length in frames>
%   where <fidl code> is the code for the event used in the fidl file, and
%   <length in frames> specifies, for how many frames of the bold run (since
%   the onset of the event) the event should be modeled.
%
%   __Assumed Modelling__
%   <fidl code>:<hrf>[:<length>]
%   where <fidl code> is the same as above, <hrf> is the type of the hemodynamic
%   response function to use, and <length> is an optional parameter, with its
%   value dependent on the model used. The allowed <hrf> are:
%
%   boynton ... uses the Boynton HRF
%   SPM     ... uses the SPM double gaussian HRF
%   u       ... unassumed (see above)
%   block   ... block response
%
%   For the first two, the <length> parameter is optional and would override the
%   event duration information provided in the fidl file. For 'u' the length is
%   the same as in previous section: the number of frames to model. For 'block'
%   length should be two numbers separated by a colon (e.g. 2:9) that specify
%   the start and end offset (from the event onset) to model as a block.
%
%   __Naming And Behavioral Regressors__
%   Each of the above (unassumed and assumed modelling specification) can be
%   followed by a ">" (greater-than character), which signifies additional
%   information in the form:
%
%   <name>[:<column>[:<normalization span>[:<normalization method>]]]
%
%   name   ... The name of the resulting regressor.
%   column ... The number of the additional behavioral regressor column in the
%              fidl file (1-based) to use as a weight for the regressor.
%   normalization span   ... Whether to normalize the behavioral weight within
%                            a specific event type ('within') or across all
%                            events ('across') [within].
%   normalization method ... The method to use for normalization. Options are
%                            z   ... compute Z-score
%                            01  ... normalize to fixed range 0 to 1
%                            -11 ... normalize to fixed range -1 to 1
%
%   Example string:
%   'block:boynton|target:9|target:9>target_rt:1:within:z'
%
%   This would result in three sets of task regressors: one assumed task
%   regressor for the sustained activity across the block, one unassumed
%   task regressor set spanning 9 frames that would model the presentation of
%   the target, and one behaviorally weighted unassumed regressor that would
%   for each frame estimate the variability in response as explained by the
%   reaction time to the target.
%
%   Results
%   -------
%
%   This step results in the following files (if requested):
%
%   * residual image:
%     <root>_res-<regressors><glm name>.<ext>
%   * GLM image:
%     <bold name><bold tail>_conc_<event root>_res-<regressors><glm name>_Bcoeff.<ext>
%   * text GLM regressor matrix:
%     glm/<bold name><bold tail>_GLM-X_<event root>_res-<regressors><glm name>.txt
%   * image of a regressor matrix:
%     glm/<bold name><bold tail>_GLM-X_<event root>_res-<regressors><glm name>.png
%
%   EXAMPLE USE
%   ===========
%
%   Activation analysis
%
%   >>> fc_PreprocessConc(subjects/OP234', [1 2 4 5], 's,r,c', 2.5, 0, 'e', [], 'flanker.fidl', 'block:boynton|target:9|target:9>target_rt:1:within:z', '', false, '.nii.gz', '', 'hipass=keep|regress=keep|lopass=keep', 'glm_name:M1');
%
%   Functional connectivity preprocessing
%
%   >>> fc_PreprocessConc(subjects/OP234', [1 2 4 5], 's,h,r', 2.5, 0, 'm,V,WM,WB,1d,e', [], 'flanker.fidl', 'block:boynton|target:9|target:9>target_rt:1:within:z', '', false, '.nii.gz', '', 'hipass=linear|regress=ignore|lopass=linear');
%
%   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
%   Written by Grega Repovs
%
%   Changelog
%   2011-01-24 Grega Repovs
%              - Created based on fc_Preprocess.m and other previous code
%
%   2013-10-20 Grega Repovs (v0.9.3)
%              - Added option for ignoring the frames marked as not to be used.
%
%   2014-07-20 Grega Repovs (v0.9.5)
%              - Rewrote with separate nuisance signal extraction and parallel processing.
%
%   2014-09-15 Grega Repovs (v0.9.6)
%              - Added the option to smooth within a mask and use a dilation mask
%
%   2015-05-26 Grega Repovs (v0.9.6)
%              - Added the option to provide alternative root names of bolds (boldname)
%
%   2016-02-02 Grega Repovs (v0.9.8)
%              - Added additional GLM options
%
%   2017-01-07 Grega Repovs (v0.9.9)
%              - Renamed from fc_PreprocessConc2 to fc_PreprocessConc.
%
%   2017-03-11 Grega Repovs (v0.9.10)
%              - Updated documentation.
%
%   2017-04-22 Grega Repovs (v0.9.11)
%              - Added the option for interpolation of bad frames after regression.
%
%   2018-06-17 Grega Repovs (v0.9.12)
%              - Changes for Octave compatibility.
%
%   2018-06-20 Grega Repovs (v0.9.12)
%              - Added more detailed reporting of parameters used.
%
%   2018-06-26 Grega Repovs (v0.9.13)
%              - Changed to pretty struct printing.
%              - Added option to support hcp_bold variant processing.
%
%   2018-09-22 Grega Repovs (v0.9.14)
%              - Fixed an issue with conversion of doIt from char to string
%
%   2020-10-05 Grega Repovs (v0.9.15)
%              - Enabled additional movement and nuisance regressor computation
%   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if nargin < 16, done = [];                                  end
if nargin < 15, options = '';                               end
if nargin < 14, ignores = '';                               end
if nargin < 13, scrub = '';                                 end
if nargin < 12 || isempty(tail), tail = '.nii.gz';          end
if nargin < 11 || isempty(overwrite), overwrite = false;    end
if nargin < 10, variant = '';                               end
if nargin < 9,  eventstring = '';                           end
if nargin < 8,  efile = '';                                 end
if nargin < 7,  task = [];                                  end
if nargin < 6 || isempty(rgss), rgss = 'm,V,WM,WB,1d';      end
if nargin < 5 || isempty(omit), omit = [];                  end
if nargin < 4 || isempty(TR), TR = 2.5;                     end

fprintf('\nRunning preproces conc script v0.9.15 [%s]\n-------------------------------------\n', tail);
fprintf('\nParameters:\n---------------');
fprintf('\n       subjectf: %s', subjectf);
fprintf('\n          bolds: [%s]', num2str(bolds));
fprintf('\n           doIt: %s', doIt);
fprintf('\n             TR: %.2f', TR);
fprintf('\n           omit: %s', num2str(omit));
fprintf('\n           rgss: %s', rgss);
fprintf('\n           task: [%s]', num2str(size(task)));
fprintf('\n          efile: %s', efile);
fprintf('\n   eventrstring: %s', eventstring);
fprintf('\n        variant: %s', variant);
fprintf('\n      overwrite: %s', num2str(overwrite));
fprintf('\n           tail: %s', tail);
fprintf('\n          scrub: %s', scrub);
fprintf('\n        ignores: %s', ignores);
fprintf('\n           done: %s', done);
fprintf('\n        options: %s', options);
fprintf('\n');

default = 'boldname=bold|surface_smooth=6|volume_smooth=6|voxel_smooth=2|lopass_filter=0.08|hipass_filter=0.009|framework_path=|wb_command_path=|omp_threads=0|smooth_mask=false|dilate_mask=false|glm_matrix=none|glm_residuals=save|glm_name=|bold_tail=|bold_variant=';
options = g_ParseOptions([], options, default);

g_PrintStruct(options, 'Options used');

TS = [];
doIt = strrep(doIt, ',', '');
doIt = strrep(doIt, ' ', '');


% ======================================================
%                          ----> prepare basic variables

nbolds = length(bolds);

ignore.hipass  = 'keep';
ignore.regress = 'keep';
ignore.lopass  = 'keep';

ignores = regexp(ignores, '=|,|;|:|\|', 'split');
if length(ignores)>=2
    ignores = reshape(ignores, 2, [])';
    for p = 1:size(ignores, 1)
        if isempty(regexp(ignores{p,2}, '^-?[\d\.]+$'))
            ignore = setfield(ignore, ignores{p,1}, ignores{p,2});
        else
            ignore = setfield(ignore, ignores{p,1}, str2num(ignores{p,2}));
        end
    end
end

doscrubbing = ~any(ismember({ignore.hipass, ignore.regress, ignore.lopass}, {'keep'}));

rgsse = strrep(strrep(strrep(strrep(rgss, ',', ''), ' ', ''), ';', ''), '|', '');
rgss  = regexp(rgss, ',|;| |\|', 'split');
rtype = 0;

switch tail
case '.4dfp.img'
    fformat = '4dfp';
case '.nii'
    fformat = 'nifti';
case '.nii.gz'
    fformat = 'nifti';
case '.dtseries.nii'
    fformat = 'dtseries';
case '.ptseries.nii'
    fformat = 'ptseries';
end


% ======================================================
%                                     ---> prepare paths

for b = 1:nbolds

    % ---> general paths

    bnum = int2str(bolds(b));
    file(b).froot       = strcat(subjectf, ['/images/functional' options.bold_variant '/' options.boldname bnum options.bold_tail]);

    file(b).movdata     = strcat(subjectf, ['/images/functional' options.bold_variant '/movement/' options.boldname bnum '_mov.dat']);
    file(b).oscrub      = strcat(subjectf, ['/images/functional' options.bold_variant '/movement/' options.boldname bnum '.scrub']);
    file(b).tscrub      = strcat(subjectf, ['/images/functional' options.bold_variant '/movement/' options.boldname bnum options.bold_tail variant '.scrub']);
    file(b).bstats      = strcat(subjectf, ['/images/functional' options.bold_variant '/movement/' options.boldname bnum '.bstats']);
    file(b).nuisance    = strcat(subjectf, ['/images/functional' options.bold_variant '/movement/' options.boldname bnum '.nuisance']);
    file(b).fidlfile    = strcat(subjectf, ['/images/functional' options.bold_variant '/events/' efile]);
    file(b).bmask       = strcat(subjectf, ['/images/segmentation/boldmasks' options.bold_variant '/' options.boldname bnum '_frame1_brain_mask' tail]);

    eroot               = strrep(efile, '.fidl', '');
    file(b).croot       = strcat(subjectf, ['/images/functional' options.bold_variant '/' options.boldname options.bold_tail '_conc_' eroot]);
    file(b).cfroot      = strcat(subjectf, ['/images/functional' options.bold_variant '/concs/' options.boldname options.bold_tail '_' fformat '_' eroot]);

    file(b).Xroot       = strcat(subjectf, ['/images/functional' options.bold_variant '/glm/' options.boldname options.bold_tail '_GLM-X_' eroot]);

    file(b).lsurf       = strcat(subjectf, ['/images/segmentation/hcp/fsaverage_LR32k/L.midthickness.32k_fs_LR.surf.gii']);
    file(b).rsurf       = strcat(subjectf, ['/images/segmentation/hcp/fsaverage_LR32k/R.midthickness.32k_fs_LR.surf.gii']);

end


% ======================================================
%                       ----> are we doing coefficients?

docoeff = false;
if strfind(doIt, 'c')
    docoeff = true;
    doIt = strrep(doIt, 'c', '');
end


% ======================================================
%                  ---> deal with nuisance and scrubbing

allframes = 0;
frames    = zeros(1, nbolds);

for b = 1:nbolds

    %   ----> read data

    if doscrubbing
        [nuisance(b).scrub  nuisance(b).scrub_hdr]  = g_ReadTable(file(b).oscrub);
    end

    [nuisance(b).mov    nuisance(b).mov_hdr]    = g_ReadTable(file(b).movdata);

    nuisance(b).nframes = size(nuisance(b).mov,1);
    frames(b) = nuisance(b).nframes;
    allframes = allframes + nuisance(b).nframes;

    %   ----> exclude extra data from mov

    me = {'frame', 'scale'};
    nuisance(b).mov     = nuisance(b).mov(:,~ismember(nuisance(b).mov_hdr, me));
    nuisance(b).mov_hdr = nuisance(b).mov_hdr(~ismember(nuisance(b).mov_hdr, me));
    nuisance(b).nmov    = size(nuisance(b).mov,2);

    %   ----> do scrubbing anew if needed!

    if strfind(doIt, 'm')
        [nuisance(b).fstats nuisance(b).fstats_hdr] = g_ReadTable(file(b).bstats);

        timg = gmrimage;
        timg.frames     = size(nuisance(b).mov, 1);
        timg.fstats     = nuisance(b).fstats;
        timg.fstats_hdr = nuisance(b).fstats_hdr;
        timg.mov        = nuisance(b).mov;
        timg.mov_hdr    = nuisance(b).mov_hdr;

        timg = timg.mri_ComputeScrub(scrub);

        nuisance(b).scrub     = timg.scrub;
        nuisance(b).scrub_hdr = timg.scrub_hdr;

        nuisance(b).scrub_hdr{end+1} = 'use';
        nuisance(b).scrub(:, end+1)  = timg.use';

        g_WriteTable(file(b).tscrub, [timg.scrub timg.use'], [timg.scrub_hdr, 'use'], 'sum|%', '%-8s|%-8d|%-8d|%-7s', ' ');
    end

    %  ----> what are the frames to be used

    if doscrubbing
        nuisance(b).use = nuisance(b).scrub(:,ismember(nuisance(b).scrub_hdr, {'use'}))';
    else
        nuisance(b).use = ones(1, nuisance(b).nframes);
    end

    %   ----> lets setup nuisances!

    if strfind(doIt, 'r') && any(~ismember(rgss, {'1d', 'e', 't', 'm'}));

        % ---> signal nuisance

        [nuisance(b).signal nuisance(b).signal_hdr] = g_ReadTable(file(b).nuisance);
        nuisance(b).nsignal = size(nuisance(b).signal,2);
    else
        nuisance(b).signal = [];
        nuisance(b).signal_hdr = {};
        nuisance(b).nsignal = 0;
    end

end


%   ----> task and event nuisance

if strfind(doIt, 'r')

    if ~isempty(eventstring)
        rmodel = g_CreateTaskRegressors(file(1).fidlfile, frames, eventstring);
        runs   = rmodel.run;
    else
        rmodel.fidl.fidl   = 'None';
        rmodel.description = 'None';
        rmodel.ignore      = 'None';

        for b = 1:nbolds
            runs(b).matrix = [];
        end
    end

    bstart = 1;
    for b = 1:nbolds
        bend = bstart + nuisance(b).nframes - 1;

        if isempty(task)
            nuisance(b).task  = [];
        else
            nuisance(b).task  = task(bstart:bend, :);
            nuisance(b).ntask = size(task, 2);
        end

        if strcmp(rmodel.fidl.fidl, 'None')
            nuisance(b).effects     = [];
            nuisance(b).events      = [];
            nuisance(b).nevents     = [];
            nuisance(b).eventnamesr = [];
            nuisance(b).eventnames  = [];
            nuisance(b).eventframes = [];
        else
            nuisance(b).effects     = {rmodel.regressor.name};
            nuisance(b).events      = runs(b).matrix;
            nuisance(b).nevents     = size(nuisance(b).events, 2);
            nuisance(b).eventnamesr = runs(b).regressors;
            nuisance(b).eventnames  = rmodel.columns.event;
            nuisance(b).eventframes = rmodel.columns.frame;
        end

        bstart = bstart + nuisance(b).nframes;
    end

    % ---> regression type

    if strfind(doIt, 'r1'), rtype = 1; end
    if strfind(doIt, 'r2'), rtype = 2; end
end



% ======================================================
%                               ---> run processing loop

tasklist = ['shrl'];
exts     = {'_s','_hpss',['_res-' rgsse options.glm_name],'_lpss'};
info     = {'Smoothing','High-pass filtering','Computing GLM','Low-pass filtering'};


% ---> clean old files

if overwrite
    ext   = '';
    first = true;

    for current = doIt

        c = ismember(tasklist, current);

        if any(c)
            for b = 1:nbolds
                file(b).sfile = [file(b).froot ext tail];
            end
            if isempty(ext)
                ext = variant;
            end
            ext   = [ext exts{c}];
            for b = 1:nbolds
                file(b).tfile = [file(b).froot ext tail];
                file(b).tconc = [file(b).cfroot ext '.conc'];
            end
    
            if exist(file(b).tfile, 'file')
                if first
                    fprintf('\n---> removing old files:');
                    first = false;
                end
                fprintf('\n     ... %s', file(b).tfile);
                delete(file(b).tfile);
            end

            if exist(file(b).tconc, 'file')
                if first
                    fprintf('\n---> removing old files:');
                    first = false;
                end
                fprintf('\n     ... %s', file(b).tconc);
                delete(file(b).tconc);
            end
        end
    end
end


% ---> start the loop

ext      = '';

for b = 1:nbolds
    img(b) = gmrimage();
end

dor      = true;
fprintf('--> starting the loop\n')

for current = char(doIt)

    saveconc = true;

    % --- set the source and target filenames

    c = ismember(tasklist, current);

    for b = 1:nbolds
        file(b).sfile = [file(b).froot ext tail];
    end
    if isempty(ext)
        ext = variant;
    end
    ext   = [ext exts{c}];
    for b = 1:nbolds
        file(b).tfile = [file(b).froot ext tail];
        file(b).tconc = [file(b).cfroot ext '.conc'];
    end


    % --- print info

    fprintf('\n\n%s\n', info{c});

    % --- run tasks that are run on individual bolds

    if ismember(current, 'shl')
        for b = 1:nbolds
            fprintf('\n---> %s ', file(b).sfile)

            if exist(file(b).tfile, 'file') && ~overwrite
                fprintf('... already completed!');
                img(b).empty = true;
            else

                switch current
                    case 's'
                        if strcmp(tail, '.dtseries.nii')
                            wbSmooth(file(b).sfile, file(b).tfile, file(b), options);
                            img(b) = gmrimage();
                        elseif strcmp(tail, '.ptseries.nii')
                            fprintf(' WARNING: No spatial smoothing will be performed on ptseries images!')
                        else
                            tmpi = readIfEmpty(img(b), file(b).sfile, omit);
                            tmpi.data = tmpi.image2D;
                            if strcmp(options.smooth_mask, 'false')
                                tmpi = tmpi.mri_Smooth3D(options.voxel_smooth, true);
                            else

                                % --- set up the smoothing mask

                                if strcmp(options.smooth_mask, 'nonzero')
                                    bmask = tmpi.zeroframes(1);
                                    bmask.data = tmpi.data(:,1) > 0;
                                elseif strcmp(options.smooth_mask, 'brainsignal')
                                    bmask = tmpi.zeroframes(1);
                                    bmask.data = tmpi.data(:,1) > 300;
                                elseif strcmp(options.smooth_mask, 'brainmask')
                                    bmask = gmrimage(file(b).bmask);
                                else
                                    bmask = options.smooth_mask;
                                end

                                % --- set up the dilation mask

                                if strcmp(options.dilate_mask, 'nonzero')
                                    dmask = tmpi.zeroframes(1);
                                    dmask.data = tmpi.data(:,1) > 0;
                                elseif strcmp(options.dilate_mask, 'brainsignal')
                                    dmask = tmpi.zeroframes(1);
                                    dmask.data = tmpi.data(:,1) > 300;
                                elseif strcmp(options.dilate_mask, 'brainmask')
                                    dmask = gmrimage(file(b).bmask);
                                else
                                    dmask = options.dilate_mask;
                                end

                                tmpi = tmpi.mri_Smooth3DMasked(bmask, options.voxel_smooth, dmask, true);
                            end
                            img(b) = tmpi;

                        end
                    case 'h'
                        tmpi = readIfEmpty(img(b), file(b).sfile, omit);
                        hpsigma = ((1/TR)/options.hipass_filter)/2;
                        tmpi = tmpi.mri_Filter(hpsigma, 0, omit, true, ignore.hipass);
                        img(b) = tmpi;
                    case 'l'
                        tmpi = readIfEmpty(tmpi, file(b).sfile, omit);
                        lpsigma = ((1/TR)/options.lopass_filter)/2;
                        tmpi = tmpi.mri_Filter(0, lpsigma, omit, true, ignore.lopass);
                        img(b) = tmpi;
                end

                if ~img(b).empty
                    img(b).mri_saveimage(file(b).tfile);
                    fprintf(' ... saved!');
                end
            end

            % --- filter nuisance if needed

            if dor
                switch current
                    case 'h'
                        hpsigma = ((1/TR)/options.hipass_filter)/2;
                        tnimg = tmpimg(nuisance(b).signal', nuisance(b).use);
                        tnimg = tnimg.mri_Filter(hpsigma, 0, omit, false, ignore.hipass);
                        nuisance(b).signal = tnimg.data';

                    case 'l'
                        lpsigma = ((1/TR)/options.lopass_filter)/2;
                        tnimg = tmpimg([nuisance(b).signal nuisance(b).task nuisance(b).events nuisance(b).mov]', nuisance(b).use);
                        tnimg = tnimg.mri_Filter(0, lpsigma, omit, false, ignore.lopass);
                        nuisance(b).signal = tnimg.data(1:nuisance(b).nsignal,:)';
                        nuisance(b).task   = tnimg.data((nuisance(b).nsignal+1):(nuisance(b).nsignal+nuisance(b).ntask),:)';
                        nuisance(b).events = tnimg.data((nuisance(b).nsignal+nuisance(b).ntask+1):(nuisance(b).nsignal+nuisance(b).ntask+nuisance(b).nevents),:)';
                        nuisance(b).mov    = tnimg.data(end-nuisance(b).nmov:end,:)';
                end
            end
        end
    end

    % --- run tasks that are run on the joint bolds

    if current == 'r'

        for b = 1:nbolds
            file(b).tfile = [file(b).froot ext tail];
            file(b).tconc = [file(b).cfroot ext '.conc'];
        end

        if exist(file(b).tfile, 'file') && ~overwrite
            fprintf('... already completed!');
            img(b).empty = true;
        else
            for b = 1:nbolds
                img(b) = readIfEmpty(img(b), file(b).sfile, omit);
            end
            fprintf('\n---> running GLM ');
            [img coeff] = regressNuisance(img, omit, nuisance, rgss, rtype, ignore.regress, options, [file(b).Xroot ext], rmodel);
            fprintf('... done!');

            if strcmp(options.glm_residuals, 'save')
                for b = 1:nbolds
                    fprintf('\n---> saving %s ', file(b).tfile);
                    img(b).mri_saveimage(file(b).tfile);
                    fprintf('... done!');
                end
                saveconc = true;
            else
                fprintf('\n---> not saving residuals (glm_residuals set to %s)', options.glm_residuals);
                saveconc = false;
            end

            if docoeff
                cname = [file(b).croot ext '_Bcoeff' tail];
                fprintf('\n---> saving %s ', cname);
                coeff.mri_saveimage(cname);
                fprintf('... done!');
            end
        end
        dor = false;
    end

    if saveconc
        if exist(file(b).tconc, 'file') && ~overwrite
            fprintf('\n---> conc file already saved!');
        else
            fprintf('\n---> saving conc file ');
            gmrimage.mri_SaveConcFile(file(b).tconc, {file.tfile});
            fprintf('... done!');
        end
    end

end

if ~isempty(done)
    fout = fopen(done, 'w');
    fprintf(fout, 'OK');
    fclose(fout);
end
fprintf('\n==> preproces conc finished successfully\n');

return


% ======================================================
%   ----> do GLM removal of nuisance regressors
%


function [img coeff] = regressNuisance(img, omit, nuisance, rgss, rtype, ignore, options, Xroot, rmodel)

    % ---> basic settings

    nbolds = length(img);
    frames = zeros(1, nbolds);

    nuisanceDer = ismember('1d', rgss) || ismember('n1d', rgss);
    movement    = ismember('m', rgss);
    movementDer = ismember('1d', rgss) || ismember('m1d', rgss);
    movementSQ  = ismember('mSq', rgss);
    movementDerSQ = ismember('m1dSq', rgss);
    task        = ismember('t', rgss);
    event       = ismember('e', rgss);
    rgss        = rgss(~ismember(rgss, {'1d', 'n1d', 'e', 't', 'm','m1d','mSq','m1dSq'}));
    hdr         = {};
    hdre        = {};
    hdrf        = [];
    effects     = {};
    effect      = [];
    eindex      = [];

    % ---> bold starts, ends, frames, selection of nuisance

    st = 1;
    smask = ismember(nuisance(1).signal_hdr, rgss);
    for b = 1:nbolds
        bS(b)     = st;
        frames(b) = nuisance(b).nframes;
        bE(b)     = st + frames(b) - 1;
        st        = st + frames(b);

        nuisance(b).signal  = nuisance(b).signal(:,smask);
        nuisance(b).signal  = zscore(nuisance(b).signal);
        nuisance(b).nsignal = sum(smask);
        nuisance(b).signal_hdr = nuisance(b).signal_hdr(smask);
    end

    % ---> X size and init

    nB = 2;
    nS = nuisance(1).nsignal;
    if task,     nT = nuisance(1).ntask;   else nT = 0; end
    if movement, nM = nuisance(1).nmov;    else nM = 0; end
    if movementDer, nM = nM + nuisance(1).nmov;    end
    if movementSQ, nM = nM + nuisance(1).nmov;    end
    if movementDerSQ, nM = nM + nuisance(1).nmov;    end
    if event,    nE = nuisance(1).nevents; else nE = 0; end
    nBj = nB*nbolds;
    nTj = nT;

    switch rtype
        case 0
            joinn = false;          % joinn - whether to have the same nuisance regressors across bolds
            joine = true;           % joine - whether to have the same event regressors across bolds
        case 1
            joinn = false;
            joine = false;
        case 2
            joinn = true;
            joine = true;
    end

    if joine, nEj = nE; else nEj = nE * nbolds; end
    if joinn, nMj = nM; else nMj = nM * nbolds; end
    if joinn, nSj = nS; else nSj = nS * nbolds; end

    if nuisanceDer
        nX = nBj + nTj + nMj + nSj*2 + nEj;   %movement derivatives are already included
    else
        nX = nBj + nTj + nMj + nSj + nEj;
    end

    X = zeros(sum(frames), nX);

    %   ----> baseline and linear trend

    effects = {'Baseline', 'Trend'};

    xS = 1;
    for b = 1:nbolds
        xE = xS + nB - 1;
        nf = frames(b) - omit;
        pl = zeros(nf,1);
        for n = 1:nf
            pl(n)= (n-1)/(nf-1);
        end
        pl = pl-0.5;

        X(bS(b):bE(b), xS:xE) = [ones(frames(b),1) [zeros(omit,1); pl]];
        xS = xS+2;
        hdr{end+1}  = sprintf('baseline_b%d', b);
        hdr{end+1}  = sprintf('trend_b%d', b);
        hdre{end+1} = sprintf('baseline.b%d', b);
        hdre{end+1} = sprintf('trend.b%d', b);
        hdrf(end+1:end+2) = [1 1];
        effect(end+1:end+2) = [1 2];
        eindex(end+1:end+2) = [b b];
    end


    %   ----> movement

    for mi = 1:nM
        effects{end+1}  = sprintf('mov_%s', nuisance(1).mov_hdr{mi});
    end

    if movement
        for b = 1:nbolds
            xE = xS + nM - 1;
            X(bS(b):bE(b), xS:xE) = nuisance(b).mov;
            if ~joinn
                xS = xS+nM;
                for mi = 1:nM
                    ts = sprintf('mov_%s', nuisance(1).mov_hdr{mi});
                    hdr{end+1}  = sprintf('%s_b%d', ts, b);
                    hdre{end+1} = sprintf('%s.b%d', ts, b);
                    hdrf(end+1) = 1;
                    effect(end+1) = find(ismember(effects, ts));
                    eindex(end+1) = b;
                end
            end
        end
        if joinn
            xS = xS+nM;
            for mi = 1:nM
                ts = sprintf('mov_%s', nuisance(1).mov_hdr{mi});
                hdr{end+1}  = ts;
                hdre{end+1} = ts;
                hdrf(end+1) = 1;
                effect(end+1) = find(ismember(effects, ts));
                eindex(end+1) = 1;
            end
        end
    end

 %----- movement derivatives

    for mi = 1:nM
        effects{end+1}  = sprintf('mov_%s_1d', nuisance(1).mov_hdr{mi});
    end

    if movementDer
        for b = 1:nbolds
            xE = xS + nM - 1;
            X(bS(b):bE(b), xS:xE) = [zeros(1,nuisance(b).nmov); diff(nuisance(b).mov)];
            if ~joinn
                xS = xS+nM;
                for mi = 1:nM
                    ts = sprintf('mov_%s_1d', nuisance(1).mov_hdr{mi});
                    hdr{end+1}  = sprintf('%s.b%d', ts, b);
                    hdre{end+1} = sprintf('%s.b%d', ts, b);
                    hdrf(end+1) = 1;
                    effect(end+1) = find(ismember(effects, ts));
                    eindex(end+1) = b;
                end
            end
        end
        if joinn
            xS = xS+nM;
            for mi = 1:nM
                ts = sprintf('mov_%s_1d', nuisance(1).mov_hdr{mi});
                hdr{end+1}  = ts;
                hdre{end+1} = ts;
                hdrf(end+1) = 1;
                effect(end+1) = find(ismember(effects, ts));
                eindex(end+1) = 1;
            end
        end
    end
    
    %------ Squared motion parameters
    
    for mi = 1:nM
        effects{end+1}  = sprintf('mov_%s_Sq', nuisance(1).mov_hdr{mi});
    end
    
    if movementSQ
        for b = 1:nbolds
            xE = xS + nM - 1;
            X(bS(b):bE(b), xS:xE) = nuisance(b).mov.^2;
            if ~joinn
                xS = xS+nM;
                for mi = 1:nM
                    ts = sprintf('mov_%s_Sq', nuisance(1).mov_hdr{mi});
                    hdr{end+1}  = sprintf('%s_b%d', ts, b);
                    hdre{end+1} = sprintf('%s.b%d', ts, b);
                    hdrf(end+1) = 1;
                    effect(end+1) = find(ismember(effects, ts));
                    eindex(end+1) = b;
                end
            end
        end
        if joinn
            xS = xS+nM;
            for mi = 1:nM
                ts = sprintf('mov_%s_Sq', nuisance(1).mov_hdr{mi});
                hdr{end+1}  = ts;
                hdre{end+1} = ts;
                hdrf(end+1) = 1;
                effect(end+1) = find(ismember(effects, ts));
                eindex(end+1) = 1;
            end
        end
    end
    
    % ------ Squared motion derivatives
    
    for mi = 1:nM
        effects{end+1}  = sprintf('mov_%s_1dSq', nuisance(1).mov_hdr{mi});
    end

    if movementDerSQ
        for b = 1:nbolds
            xE = xS + nM - 1;
            X(bS(b):bE(b), xS:xE) = [zeros(1,nuisance(b).nmov); diff(nuisance(b).mov).^2];
            if ~joinn
                xS = xS+nM;
                for mi = 1:nM
                    ts = sprintf('mov_%s_1dSq', nuisance(1).mov_hdr{mi});
                    hdr{end+1}  = sprintf('%s.b%d', ts, b);
                    hdre{end+1} = sprintf('%s.b%d', ts, b);
                    hdrf(end+1) = 1;
                    effect(end+1) = find(ismember(effects, ts));
                    eindex(end+1) = b;
                end
            end
        end
        if joinn
            xS = xS+nM;
            for mi = 1:nM
                ts = sprintf('mov_%s_1dSq', nuisance(1).mov_hdr{mi});
                hdr{end+1}  = ts;
                hdre{end+1} = ts;
                hdrf(end+1) = 1;
                effect(end+1) = find(ismember(effects, ts));
                eindex(end+1) = 1;
            end
        end
    end

    
    %   ----> signal

    for mi = 1:nS
        effects{end+1}  = nuisance(1).signal_hdr{mi};
    end

    for b = 1:nbolds
        xE = xS + nS - 1;
        X(bS(b):bE(b), xS:xE) = nuisance(b).signal;
        if ~joinn
            xS = xS+nS;
            for mi = 1:nS
                hdr{end+1}  = sprintf('%s_b%d', nuisance(1).signal_hdr{mi}, b);
                hdre{end+1} = sprintf('%s.b%d', nuisance(1).signal_hdr{mi}, b);
                hdrf(end+1) = 1;
                effect(end+1) = find(ismember(effects, nuisance(1).signal_hdr{mi}));
                eindex(end+1) = b;
            end
        end
    end
    if joinn
        xS = xS+nS;
        for mi = 1:nS
            ts = nuisance(1).signal_hdr{mi};
            hdr{end+1}  = ts;
            hdre{end+1} = ts;
            hdrf(end+1) = 1;
            effect(end+1) = find(ismember(effects, ts));
            eindex(end+1) = 1;
        end
    end


    %   ----> signal derivatives

    if nuisanceDer

        %   ----> signal

        for mi = 1:nS
            effects{end+1}  = sprintf('%s_1d', nuisance(1).signal_hdr{mi});
        end

        for b = 1:nbolds
            xE = xS + nS - 1;
            X(bS(b):bE(b), xS:xE) = [zeros(omit+1, nuisance(b).nsignal); diff(nuisance(b).signal(omit+1:end,:))];
            if ~joinn
                xS = xS+nS;
                for mi = 1:nS
                    ts = sprintf('%s_1d', nuisance(1).signal_hdr{mi});
                    hdr{end+1}  = sprintf('%s.b%d', ts, b);
                    hdre{end+1} = sprintf('%s.b%d', ts, b);
                    hdrf(end+1) = 1;
                    effect(end+1) = find(ismember(effects, ts));
                    eindex(end+1) = b;
                end
            end
        end
        if joinn
            xS = xS+nS;
            for mi = 1:nS
                ts = sprintf('%s_1d', nuisance(1).signal_hdr{mi});
                hdr{end+1}  = sprintf('%s_1d', nuisance(1).signal_hdr{mi});
                hdre{end+1} = sprintf('%s_1d', nuisance(1).signal_hdr{mi});
                hdrf(end+1) = 1;
                effect(end+1) = find(ismember(effects, ts));
                eindex(end+1) = 1;
            end
        end
    end


    %   ----> events

    % for mi = 1:nE
    %     effects{end+1}  = nuisance(b).eventnamesr{mi};
    % end

    effects = [effects nuisance(1).effects];

    if event
        for b = 1:nbolds
            xE = xS + nE - 1;
            X(bS(b):bE(b), xS:xE) = nuisance(b).events;
            % fprintf('\n---> events run %d %d %d %d %d', b, bS(b), bE(b), xS, xE);
            if ~joine
                xS = xS+nE;
                for mi = 1:nE
                    hdr{end+1}  = sprintf('%s_b%d', nuisance(b).eventnamesr{mi}, b);
                    hdre{end+1} = sprintf('%s.b%d', nuisance(b).eventnames{mi}, b);
                    hdrf(end+1) = nuisance(b).eventframes(mi);
                    effect(end+1) = find(ismember(effects, nuisance(b).eventnames{mi}));
                    eindex(end+1) = b;
                end
            end
        end
        if joine
            xS = xS+nE;
            for mi = 1:nE
                hdr{end+1}  = sprintf('%s', nuisance(1).eventnamesr{mi});
                hdre{end+1} = sprintf('%s', nuisance(1).eventnames{mi});
                hdrf(end+1) = nuisance(1).eventframes(mi);
                effect(end+1) = find(ismember(effects, nuisance(b).eventnames{mi}));
                eindex(end+1) = 1;
            end
        end
    end


    %   ----> task

    for mi = 1:nT
        effects{end+1}  = sprintf('task%d', mi);
    end

    if task
        xE = xS + nT - 1;
        for b = 1:nbolds
            X(bS(b):bE(b), xS:xE) = nuisance(b).task;
        end
        xS = xS+nT;
        for mi = 1:nT
            ts = sprintf('task%d', mi);
            hdr{end+1}  = ts;
            hdre{end+1} = ts;
            hdrf(end+1) = 1;
            effect(end+1) = find(ismember(effects, ts));
            eindex(end+1) = 1;
        end
    end

    %   ----> combine data in a single image
    fprintf('.');

    %   ---> first create per bold masks

    masks   = {};
    mframes = zeros(1, nbolds);
    nmask   = [];
    if ~strcmp(ignore, 'keep'), fprintf(' excluding'); end
    for b = 1:nbolds
        if ~strcmp(ignore, 'keep')
            fprintf(' %d', sum(img(b).use == 0));
            mask = img(b).use == 1;
        else
            mask = true(1, img(b).frames);
        end
        mask(1:omit) = false;
        masks{b}     = mask;
        mframes(b)   = sum(mask);
        nmask        = [nmask mask];
    end
    if ~strcmp(ignore, 'keep'), fprintf(' frames '); end

    %   ---> create and fill placeholder image

    Y = img(1).zeroframes(sum(mframes));

    for b = 1:nbolds
        fstart = sum(mframes(1:b-1)) + 1;
        fend   = sum(mframes(1:b));
        Y.data(:, fstart:fend) = img(b).data(:,masks{b});
    end

    %   ----> save GLM matrix data
    %   ----> Header not written right yet ... need to change columns according to the regression type (per run matrices)

    % ---- add gmean and sd image info

    hdr  = [hdr  {'gmean', 'sd'}];
    hdre = [hdre {'gmean', 'sd'}];
    hdrf = [hdrf 1 1];
    effects = [effects {'gmean', 'sd'}];
    effect  = [effect find(ismember(effects, 'gmean')), find(ismember(effects, 'sd'))];
    eindex  = [eindex 1 1];

    if ismember(options.glm_matrix, {'text', 'both'})
        xfile = [Xroot '.txt'];
    else
        xfile = [];
    end
    xevents  = sprintf(strjoin(hdre, '\t'));
    xframes  = sprintf('%d\t', hdrf);
    xeffects = sprintf(strjoin(effects, '\t'));
    xeffect  = sprintf('%d\t', effect);
    xeindex  = sprintf('%d\t', eindex);
    pre      = sprintf('# fidl: %s\n# model: %s\n# bolds: %d\n# effects: %s\n# effect: %s\n# eindex: %s\n# ignore: %s\n# event: %s\n# frame: %s', rmodel.fidl.fidl, rmodel.description, nbolds, xeffects, xeffect, xeindex, rmodel.ignore, xevents, xframes(1:end-1));
    xtable   = g_WriteTable(xfile, [X(nmask==1, :) zeros(sum(nmask==1), 2)], hdr, 'sd|mean|min|max', [], [], pre);

    if ismember(options.glm_matrix, {'image', 'both'})
        mimg = X(nmask==1, :);
        mimg = mimg / (max(max(abs(mimg))) * 2);
        mimg = mimg + 0.5;
        try
            imwrite(mimg, [Xroot '.png']);
        catch
            fprintf('\n---> WARNING: Could not save GLM PNG image! Check supported image formats!');
        end
    end

    %   ----> mask nuisance and do GLM
    fprintf('.');
    % fprintf('\n -> X\n'); fprintf('%.2f ', sum(X));
    % fprintf('\n -> X\n'); fprintf('%.2f ', sum(X(nmask==1, :)));
    % fprintf('\n -> mask %d', sum(nmask==1));
    % fprintf(xevents);
    X = X(nmask==1, :);
    [coeff res] = Y.mri_GLMFit(X);
    coeff = [coeff Y.mri_Stats({'m', 'sd'})];

    %   ----> put data back into images
    fprintf('.');

    for b = 1:nbolds
        fstart = sum(mframes(1:b-1)) + 1;
        fend   = sum(mframes(1:b));
        % img(b).data(:,masks{b}) = res.data(:,fstart:fend);    % --- led to strange error in Octave, had to give it off to a temporary image
        tmpi   = img(b);
        tmpi.data(:,masks{b}) = res.data(:,fstart:fend);
        if min(masks{b}) == 0
            if strcmp(ignore, 'mark')
                fprintf(' marking %d bad frames ', sum(~masks{b}));
                tmpi.data(:, ~masks{b}) = NaN;
            elseif ismember({ignore}, {'linear', 'spline'})
                fprintf(' %s interpolating %d bad frames ', ignore, sum(~masks{b}));
                x  = [1:length(masks{b})]';
                xi = x;
                x  = x(masks{b});
                tmpi.data = interp1(x, tmpi.data(:, masks{b})', xi, ignore, 'extrap')';
            end
        end
        img(b) = tmpi;
    end

    coeff = coeff.mri_EmbedMeta(xtable, 64, 'GLM');

return





% ======================================================
%                           ----> create temporary image
%

function [img] = tmpimg(data, use);

    img = gmrimage();
    img.data = data;
    img.use  = use;
    [img.voxels img.frames] = size(data);


% ======================================================
%                                    ----> read if empty
%

function [img] = readIfEmpty(img, src, omit)

    if isempty(img) || img.empty
        fprintf('\n---> reading %s ', src);
        img = gmrimage(src);
        if ~isempty(omit)
            img.use(1:omit) = 0;
        end
        fprintf('... done!');
    end



% ======================================================
%                                         ----> wbSmooth
%

function [] = wbSmooth(sfile, tfile, file, options)

    % --- convert FWHM to sd

    options.surface_smooth = options.surface_smooth / 2.35482004503; % (sqrt(8*log(2)))
    options.volume_smooth  = options.volume_smooth / 2.35482004503;


    fprintf('\n---> running wb_command -cifti-smoothing');

    if ~isempty(options.framework_path)
        if strcmp(options.framework_path, 'NULL')
            setenv('LD_LIBRARY_PATH');
            setenv('DYLD_LIBRARY_PATH');
            setenv('DYLD_FRAMEWORK_PATH');
        else
            if isempty(strfind(s, options.framework_path))
                fprintf('\n     ... setting DYDL_FRAMEWORK_PATH to %s', options.framework_path);
                setenv('DYLD_FRAMEWORK_PATH');
            end
            if isempty(strfind(sl, options.framework_path))
                fprintf('\n     ... setting DYLD_LIBRARY_PATH to %s', options.framework_path);
                setenv('DYLD_LIBRARY_PATH', [options.framework_path ':' sl]);
            end
            if isempty(strfind(ll, options.framework_path))
                fprintf('\n     ... setting LD_LIBRARY_PATH to %s', options.framework_path);
                setenv('LD_LIBRARY_PATH', [options.framework_path ':' ll]);
            end
        end
    end

    if ~isempty(options.wb_command_path)
        s = getenv('PATH');
        if isempty(strfind(s, options.wb_command_path))
            fprintf('\n     ... setting PATH to %s', options.wb_command_path);
            setenv('PATH', [options.wb_command_path ':' s]);
        end
    end
    if options.omp_threads > 0
        setenv('OMP_NUM_THREADS', num2str(options.omp_threads));
    end

    fprintf('\n     ... smoothing');
    comm = sprintf('wb_command -cifti-smoothing %s %f %f COLUMN %s -left-surface %s -right-surface %s', sfile, options.surface_smooth, options.volume_smooth, tfile, file.lsurf, file.rsurf);
    [status out] = system(comm);

    if status
        fprintf('\nERROR: wb_command finished with error!\n       ran: %s\n', comm);
        fprintf('\n --- wb_command output ---\n%s\n --- end wb_command output ---\n', out);
        error('\nAborting processing!');
    else
        fprintf(' ... done!');
    end



