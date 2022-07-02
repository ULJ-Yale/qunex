function [] = fc_preprocess(sessionf, bold, omit, doIt, rgss, task, efile, TR, eventstring, variant, overwrite, tail, scrub, ignores, options)

%``function [] = fc_preprocess(sessionf, bold, omit, doIt, rgss, task, efile, TR, eventstring, variant, overwrite, tail, scrub, ignores, options)``
%
%   A command for running single BOLD file based functional connectivity 
%   preprocessing.
%
%   Parameters:
%       --sessionf (str):
%           The session’s folder with images and data.
%       --bold (int):
%           The number of the bold file to process.
%       --omit (int, default []):
%           The number of frames to omit at the start of each bold.
%       --doIt (str, default 's,h,r,c,l'):
%           A string specifying, which steps to perform and in what order:
%
%           - s - spatial smoothing
%           - h - highpass temporal filter
%           - r - regression of nuisance signal
%           - c - save coefficients in _coeff file
%           - l - lowpass temporal filtering
%           - m - motion scrubbing.
%
%       --rgss (str, default 'm,V,WM,WB,1d'):
%           What to regress in the regression step, a comma separated list of
%           possibilities:
%
%           - m     - motion
%           - m1d   - first derivate for movement regressors
%           - mSq   - squared motion parameters
%           - m1dSq - squared  motion derivatives
%           - V     - ventricles
%           - WM    - white matter
%           - WB    - whole brain
%           - mWB   - masked whole brain
%           - n1d   - first derivative for nuisance signal regressors
%           - 1d    - first derivatives of nuisance signal and movement
%           - t     - task
%           - e     - event.
%
%       --task (matrix, default []):
%           A matrix of custom regressors to be entered in GLM.
%       --efile (str, default ''):
%           An event (fidl) file to be used for removing task structure.
%       --TR (float, default 2.5):
%           TR of the data, in seconds.
%       --eventstring (str, default ''):
%           A string specifying the events to regress and the regressors to use.
%       --variant (str, default ''):
%           A string to be prepended to files.
%       --overwrite (bool, default false):
%           Whether old files should be overwritten.
%       --tail (str, default '.nii.gz'):
%           What file extension to expect and use for images.
%       --scrub (str, default Existing scrubbing data):
%           The description of how to compute scrubbing - a string in
%           `'param:value|param:value'` format.
%
%           Parameters:
%
%           - radius
%               head radius in mm (default 50)
%           - fdt
%               frame displacement threshold
%           - dvarsmt
%               dvarsm threshold
%           - dvarsmet
%               dvarsme threshold
%           - after
%               how many frames after the bad one to reject
%           - before
%               how many frames before the bad one to reject
%           - reject
%               which criteria to use for rejection (mov, dvars, dvarsme,
%               idvars, udvars ...)
%
%           If empty, the existing scrubbing data is used.
%
%       --ignores (str, default 'hipass꞉keep|regress꞉keep|lopass꞉keep'):
%           How to deal with the frames marked as not used in filering and
%           regression steps specified in a single string, separated with pipes:
%
%           - hipass  - keep / linear / spline
%           - regress - keep / ignore / mark / linear / spline
%           - lopass  - keep / linear /spline.
%
%           NOTE
%
%           The colon symbols used above to denote::
%
%               'hipass꞉keep|regress꞉keep|lopass꞉keep'
%
%           are of the Unicode modifier colon variety (U+A789) and are not
%           equivalent to the usual colon (U+003A) that should be used when
%           running the command. Copying the above line containing modifier
%           colons will result in an error - use normal colons with the command
%           instead.
%       --options (str, default ''):
%           Additional options that can be set using the
%           'key=value|key=value' string:
%
%           - surface_smooth  : 6
%           - volume_smooth   : 6
%           - voxel_smooth    : 2
%           - lopass_filter   : 0.08
%           - hipass_filter   : 0.009
%           - framework_path  :
%           - wb_command_path :
%           - omp_threads     : 0
%           - smooth_mask     : false
%           - dilate_mask     : false
%           - boldname        : bold
%           - bold_tail       :
%           - bold_variant    :
%           - img_suffix      :
%           - glm_matrix      : none  ('none' / 'text' / 'image' / 'both')
%           - glm_residuals   : save
%           - glm_name        :
%
%   Notes:
%       fc_preprocess is a complex function initially used to prepare BOLD files
%       for further functional connectivity analysis. The function enables the
%       following actions:
%
%       - spatial smoothing (3D or 2D for cifti files)
%       - temporal filtering (high-pass, low-pass)
%       - removal of nuisance signal and task structure.
%
%       Basics:
%           Basics specify the files to use for processing and what to do. The
%           relevant parameters are:
%
%           - sessionf
%               Specifies the sessions’s base folder in which the function will
%               look for all the other relevant files.
%
%           - bold
%               The number of the bold file to process
%
%           - doIt
%               The actions to be performed.
%
%           - overwrite
%               Whether to overwrite the existing data or not.
%
%           - variant
%               A string to prepend to the list of steps done in the resulting
%               files saved.
%
%           - tail
%               The file (format) extension (e.g. '.nii.gz').
%
%           - efile
%               The event (fidl) filename.
%
%           Important are also the following optional keys in the options
%           parameter:
%
%           - boldname
%               Specifies, how the BOLD files are named in the images/functional
%               folder.
%
%           - bold_tail
%               Specifies the additional tail that the bold name might have (see
%               below).
%
%           - bold_variant
%               Specifies a possible extension for the images/functional and
%               images/segmentation/boldmasks folders.
%
%           - img_suffix
%               Specifies a possible extension for the images folder name
%               enabling processing of multiple parallel workflows.
%
%           The actions performed are denoted by a single letter, and they
%           will be executed in the sequence listed. The possible actions are:
%
%           - m
%               Motion scrubbing.
%
%           - s
%               Spatial smooting.
%
%           - h
%               High-pass filtering.
%
%           - r
%               Regression (nuisance and/or task) with an optional number 0, 1,
%               or 2 specifying the type of regression to use (see REGRESSION
%               below).
%
%           - c
%               Saving of resulting beta coefficients (always to follow 'r').
%
%           - l
%               Low-pass filtering.
%
%           So the default 's,h,r,c,l' do input parameter would lead to the
%           files first being smoothed, then high-pass filtered. Next a
%           regression step would follow in which nuisance signal and/or task
%           related signal would be estimated and regressed out, then the
%           related beta estimates would be saved. Lastly the BOLDs would be
%           also low-pass filtered.
%
%       Scrubbing:
%           The command either makes use of scrubbing information or performs
%           scrubbing comuputation on its own (when 'm' is part of the command).
%           In the latter case, all the scrubbing parameters need to be
%           specified in the scrub string:
%
%           - radius
%               Estimated head radius (in mm) for computing frame displacement
%               statistics. Defaults to 50.
%
%           - fd
%               Frame displacement threshold (in mm) to use for identifying bad
%               frames. Defaults to 0.5.
%
%           - dvarsmt
%               The (mean normalized) dvars threshold to use for identifying bad
%               frames. Defaults to 3.0.
%
%           - dvarsmet
%               The (median normalized) dvarsm threshold to use for identifying
%               bad frames. Defaults to 1.5.
%
%           - after
%               How many frames after each frame identified as bad to also
%               exclude from further processing and analysis. Defaults to 0.
%
%           - before
%               How many frames before each frame identified as bad to also
%               exclude from further processing and analysis. Defaults to 0.
%
%           - reject
%               Which criteria to use for identification of bad frames. Defaults
%               to 'udvarsme'.
%
%           In any case, if scrubbing was done beforehand or as a part of this
%           commmand, one can specify, how the scrubbing information is used in
%           ignores string::
%
%               'hipass:<filtering opt.>|regress:<regression opt.>|lopass:<filtering opt.>'
%
%           Filtering options are:
%
%           - keep
%               Keep all the bad frames unchanged.
%
%           - linear
%               Replace bad frames with linear interpolated values based on
%               neighbouring good frames.
%
%           - spline
%               Replace bad frames with spline interpolated values based on
%               neighouring good frames
%
%           To prevent artefacts present in bad frames to be temporaly spread,
%           use either 'linear' or 'spline' options.
%
%           Regression options are:
%
%           - keep
%               Keep the bad frames and use them in the regression.
%
%           - ignore
%               Exclude bad frames from regression and keep the original values
%               in their place.
%
%           - mark
%               Exclude bad frames from regression and mark the bad frames as
%               NaN.
%
%           - linear
%               Exclude bad frames from regression and replace them with linear
%               interpolation after regression.
%
%           - spline
%               Exclude bad frames from regression and replace them with spline
%               interpolation after regression.
%
%           Please note that when the bad frames are ignored, the original
%           values will be retained in the residual signal. In this case they
%           have to be excluded or ignored also in all following analyses,
%           otherwise they can be a significant source of artefacts.
%
%       Spatial smoothing:
%           Volume smoothing:
%               For volume formats the images will be smoothed using the
%               img_smooth_3d nimage method. For cifti format the smooting will
%               be done by calling the relevant wb_command command. The
%               smoothing specific parameters can be set in the options string:
%
%               - voxel_smooth
%                   Gaussian smoothing FWHM in voxels. Defaults to 2.
%
%               - smooth_mask
%                   Whether to smooth only within a mask, and what mask to use
%                   (nonzero/brainsignal/brainmask/<filename>). Defaults to
%                   false.
%
%               - dilate_mask
%                   Whether to dilate the image after masked smoothing and what
%                   mask to use (nonzero/brainsignal/brainmask/same/<filename>).
%                   Defaults to false.
%
%               If a smoothing mask is set, only the signal within the specified
%               mask will be used in the smoothing. If a dilation mask is set,
%               after smoothing within a mask, the resulting signal will be
%               constrained / dilated to the specified dilation mask.
%
%               For both optional string values the possibilities are:
%
%               - nonzero
%                   Mask will consist of all the nonzero voxels of the first
%                   BOLD frame.
%
%               - brainsignal
%                   Mask will consist of all the voxels that are of value 300 or
%                   higher in the first BOLD frame (this gave a good coarse
%                   brain mask for images intensity normalized to mode 1000 in
%                   the NIL preprocessing stream).
%
%               - brainmask
%                   Mask will be the actual bet extracted brain mask based on
%                   the first BOLD frame (generated using the
%                   create_bold_brain_masks command).
%
%               - <filename>
%                   All the non-zero voxels in a specified volume file will be
%                   used as a mask.
%
%               - false
%                   No mask will be used.
%
%               - same
%                   Only for dilate_mask, the mask used will be the same as
%                   smooting mask.
%
%           Cifti smoothing:
%               For cifti format images, smoothing will be run using wb_command.
%               The following parameters can be set in the options parameter:
%
%               - surface_smooth
%                   FWHM for gaussian surface smooting in mm. Defaults to 6.0.
%
%               - volume_smooth
%                   FWHM for gaussian volume smooting in mm. Defaults to 6.0.
%
%               - omp_threads
%                   Number of cores to be used by wb_command. 0 for no change of
%                   system settings. Defaults to 0.
%
%               - framework_path
%                   The path to framework libraries on the Mac system. No need
%                   to use it currently if installed correctly.
%
%               - wb_command_path
%                   The path to the wb_command executive. No need to use it
%                   currently if installed correctly.
%
%               Results:
%                   The resulting smoothed files are saved with '_s' added to
%                   the BOLD root filename.
%
%       Temporal filtering:
%           Temporal filtering is accomplished using img_filter nimage method.
%           The code is adopted from the FSL C++ code enabling appropriate
%           handling of bad frames (as described above - see SCRUBBING). The
%           filtering settings can be set in the options parameter:
%
%           - hipass_filter
%               The frequency for high-pass filtering in Hz. Defaults to 0.008.
%
%           - lopass_filter
%               The frequency for low-pass filtering in Hz Defaults to 0.09.
%
%           Please note that the values finaly passed to img_filter method are
%           the respective sigma values computed from the specified frequencies
%           and TR.
%
%           Results:
%               The resulting filtered files are saved with '_hpss' or '_bpss'
%               added to the BOLD root filename for high-pass and low-pass
%               filtering, respectively.
%
%       Regression:
%           Regression is a complex step in which GLM is used to estimate the
%           beta weights for the specified nuisance regressors and events. The
%           resulting beta weights are then stored in a GLM file (a regular file
%           with additional information on the design used) and residuals are
%           stored in a separate file. This step can therefore be used for two
%           puposes:
%
%           (1) to remove nuisance signal and event structure from BOLD
%               files, removing unwanted potential sources of correlation for
%               further functional connectivity analyses, and
%
%           (2) to get task beta estimates for further activational analyses.
%               The following parameters are used in this step:
%
%               - rgss
%                   A comma separated list of regressors to include in GLM.
%                   Possible values are:
%
%                   - m
%                       motion parameters
%                   - m1d
%                       first derivative for movement regressors
%                   - mSq
%                       squared motion parameters
%                   - m1dSq
%                       squared  motion derivatives
%                   - V
%                       ventricles signal
%                   - WM
%                       white matter signal
%                   - WB
%                       whole brain signal
%                   - n1d
%                       first derivative of requested above nuisance signals
%                       (V, WM, WB)
%                   - 1d
%                       first derivative of both movement regressors and
%                       specified nuisance signals (V, WM, WB)
%                   - e
%                       events listed in the provided fidl files (see above),
%                       modeled as specified in the event_string parameter.
%
%                   Defaults to 'm,V,WM,WB,1d'.
%
%               - eventstring
%                   A string describing, how to model the events listed in the
%                   provided fidl files. Defaults to [].
%
%               Additionally, the following options can be set using the options
%               string:
%
%               - glm_matrix
%                   Whether to save the GLM matrix as a text file ('text'), a
%                   png image file ('image'), both ('both') or not ('none').
%                   Defaults to 'none'.
%
%               - glm_residuals
%                   Whether to save the residuals after GLM regression ('save')
%                   or not ('none'). Defaults to 'save'.
%
%               - glm_name
%                   An additional name to add to the residuals and GLM files to
%                   distinguish between different possible models used.
%
%           GLM modeling:
%               The exact GLM model used to estimate nuisance and task beta
%               coefficients and regress them from the signal is defined by the
%               event string provided by the eventstring parameter. The event
%               string is a pipe ('|') separated list of regressor
%               specifications. The possibilities are:
%
%               Unassumed Modelling:
%                   ::
%
%                       <fidl code>:<length in frames>
%
%                   where `<fidl code>` is the code for the event used in the
%                   fidl file, and `<length in frames>` specifies, for how many
%                   frames ofthe bold run (since the onset of the event) the
%                   event should be modeled.
%
%               Assumed Modelling:
%                   ::
%
%                       <fidl code>:<hrf>[-<normalize>][:<length>]
%
%                   where <fidl code> is the same as above, <hrf> is the type of
%                   the hemodynamic response function to use, and <normalize>
%                   and <length> are optional parameters, with their values
%                   dependent on the model used. The allowed <hrf> are:
%
%                   - boynton ... uses the Boynton HRF
%                   - SPM     ... uses the SPM double gaussian HRF
%                   - u       ... unassumed (see above)
%                   - block   ... block response
%
%                   For the first two, <normalize> can be either 'run' or 'uni'.
%                   'run' (e.g. 'SPM-run' or abbreviated 'SPM-r') specifies that
%                   the assumed regressor should be scaled to amplitude of 1
%                   within each BOLD run, and 'uni' (e.g. 'SPM-uni' or
%                   abbreviated 'SPM-u') specifies that the regresor should be
%                   universaly scaled to HRF area-under-the-curve = 1. If no
%                   <normalize> parameter is specified, 'uni' is assumed by
%                   default. The default behavior has changed with QuNex version
%                   0.93.4, which can result in different assumed HRF regressor
%                   scaling and the resulting GLM beta estimates.
%
%                   Parameter <length> is also optional in case of 'SPM' and
%                   'boynton' assumed HRF modelling, and it overrides the event
%                   duration information provided in the fidl file. For 'u' the
%                   length is the same as in previous section: the number of
%                   frames to model. For 'block' length should be two numbers
%                   separated by a colon (e.g. 2:9) that specify the start and
%                   end offset (from the event onset) to model as a block.
%
%               Naming And Behavioral Regressors:
%                   Each of the above (unassumed and assumed modelling
%                   specification) can be followed by a ">" (greater-than
%                   character), which signifies additional information in the
%                   form::
%
%                       <name>[:<column>[:<normalization span>[:<normalization method>]]]
%
%                   - name
%                       The name of the resulting regressor.
%
%                   - column
%                       The number of the additional behavioral regressor column
%                       in the fidl file (1-based) to use as a weight for the
%                       regressor.
%
%                   - normalization span
%                       Whether to normalize the behavioral weight within a
%                       specific event type ('within') or across all events
%                       ('across'). Defaults to 'within'.
%
%                   - normalization method
%                       The method to use for normalization. Options are:
%
%                       - z    ... compute Z-score
%                       - 01   ... normalize to fixed range 0 to 1
%                       - -11  ... normalize to fixed range -1 to 1
%                       - none ... do bot normalize, use weights as provided in
%                         fidl file.
%
%                   Example string::
%
%                       'block:boynton|target:9|target:9>target_rt:1:within:z'
%
%                   This would result in three sets of task regressors: one
%                   assumed task regressor for the sustained activity across the
%                   block, one unassumed task regressor set spanning 9 frames
%                   that would model the presentation of the target, and one
%                   behaviorally weighted unassumed regressor that would for
%                   each frame estimate the variability in response as explained
%                   by the reaction time to the target.
%
%                   Results:
%                       This step results in the following files (if requested):
%
%                       - residual image:
%                           <root>_res-<regressors>.<ext>
%
%                       - GLM coefficient image:
%                           <root>_res-<regressors>_coeff.<ext>
%
%                       If you want more specific GLM results and information,
%                       please use preprocess_conc command.
%
%   Examples:
%       ::
%
%           qunex fc_preprocess \
%               --sessionf='sessions/OP234' \
%               --bold=3 \
%               --omit=4 \
%               --doIt='s,h,r' \
%               --rgss='m,V,WM,WB,1d' \
%               --TR=2.5 \
%               --overwrite=true \
%               --scrub='udvarsme' \
%               --ignores='hipass:linear|regress=ignore|lopass=linear'
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 15, options = '';       end
if nargin < 14, ignores = '';       end
if nargin < 13, scrub = '';         end
if nargin < 12, tail = '.nii.gz';   end
if nargin < 11, overwrite = false;  end
if nargin < 10, variant = '';       end
if nargin < 9,  eventstring = '';   end
if nargin < 8 || isempty(TR), TR = 2.5;                     end
if nargin < 7,  efile = '';                                 end
if nargin < 6,  task = [];                                  end
if nargin < 5 || isempty(rgss), rgss = 'm,V,WM,WB,1d';      end
if nargin < 4 || isempty(doIt),   doIt = 'shrcl';           end
if nargin < 3, omit = [];                                   end
if nargin < 2, error('ERROR: At least session folder and BOLD number need to be specified for the function to run!'); end


fprintf('\nRunning preproces script v0.9.17 [%s]\n--------------------------------\n', tail);
fprintf('\nParameters:\n---------------');
fprintf('\n       sessionf: %s', sessionf);
fprintf('\n           bold: %s', num2str(bold));
fprintf('\n           omit: %s', num2str(omit));
fprintf('\n           doIt: %s', doIt);
fprintf('\n           rgss: %s', rgss);
fprintf('\n           task: [%s]', num2str(size(task)));
fprintf('\n          efile: %s', efile);
fprintf('\n             TR: %.2f', TR);
fprintf('\n   eventrstring: %s', eventstring);
fprintf('\n        variant: %s', variant);
fprintf('\n      overwrite: %s', num2str(overwrite));
fprintf('\n           tail: %s', tail);
fprintf('\n          scrub: %s', scrub);
fprintf('\n        ignores: %s', ignores);
fprintf('\n        options: %s', options);
fprintf('\n');


default = 'boldname=bold|surface_smooth=6|volume_smooth=6|voxel_smooth=2|lopass_filter=0.08|hipass_filter=0.009|framework_path=|wb_command_path=|omp_threads=0|smooth_mask=false|dilate_mask=false|glm_matrix=none|glm_residuals=save|glm_name=|bold_tail=|ref_bold_tail=|bold_variant=|img_suffix=';
options = general_parse_options([], options, default);

general_print_struct(options, 'Options used');

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

rgsse = strrep(strrep(strrep(strrep(rgss, ',', ''), ' ', ''), ';', ''), '|', '');
rgss  = regexp(rgss, ',|;| |\|', 'split');

doIt = strrep(doIt, ',', '');
doIt = strrep(doIt, ' ', '');


% ======================================================
%   ----> prepare paths

froot = strcat(sessionf, ['/images' options.img_suffix '/functional' options.bold_variant '/' options.boldname int2str(bold) options.bold_tail]);

file.movdata   = strcat(sessionf, ['/images' options.img_suffix '/functional' options.bold_variant '/movement/' options.boldname int2str(bold) '_mov.dat']);
file.oscrub    = strcat(sessionf, ['/images' options.img_suffix '/functional' options.bold_variant '/movement/' options.boldname int2str(bold) options.ref_bold_tail '.scrub']);
file.tscrub    = strcat(sessionf, ['/images' options.img_suffix '/functional' options.bold_variant '/movement/' options.boldname int2str(bold) options.bold_tail variant '.scrub']);
file.bstats    = strcat(sessionf, ['/images' options.img_suffix '/functional' options.bold_variant '/movement/' options.boldname int2str(bold) options.ref_bold_tail '.bstats']);
file.fidlfile  = strcat(sessionf, ['/images' options.img_suffix '/functional' options.bold_variant '/events/'   options.boldname int2str(bold) efile]);
file.bmask     = strcat(sessionf, ['/images' options.img_suffix '/segmentation/boldmasks' options.bold_variant '/' options.boldname int2str(bold) options.ref_bold_tail '_frame1_brain_mask' tail]);

eroot          = strrep(efile, '.fidl', '');
if eroot
    eroot = ['_' eroot];
end
file.nuisance  = strcat(sessionf, ['/images' options.img_suffix '/functional' options.bold_variant '/movement/' options.boldname int2str(bold) options.ref_bold_tail '.nuisance']);
file.Xroot     = strcat(sessionf, ['/images' options.img_suffix '/functional' options.bold_variant '/glm/' options.boldname int2str(bold) options.bold_tail '_GLM-X' eroot]);

file.lsurf     = strcat(sessionf, ['/images' options.img_suffix '/segmentation/hcp/fsaverage_LR32k/L.midthickness.32k_fs_LR.surf.gii']);
file.rsurf     = strcat(sessionf, ['/images' options.img_suffix '/segmentation/hcp/fsaverage_LR32k/R.midthickness.32k_fs_LR.surf.gii']);


% ======================================================
%   ----> are we doing coefficients?

docoeff = false;
if strfind(doIt, 'c')
    docoeff = true;
    doIt = strrep(doIt, 'c', '');
end


% ======================================================
%   ----> deal with nuisance and scrubbing

%   ----> read data

[nuisance.fstats nuisance.fstats_hdr] = general_read_table(file.bstats);
[nuisance.scrub  nuisance.scrub_hdr]  = general_read_table(file.oscrub);
[nuisance.mov    nuisance.mov_hdr]    = general_read_table(file.movdata);

nuisance.nframes = size(nuisance.mov,1);

%   ----> exclude extra data from mov

me               = {'frame', 'scale'};
nuisance.mov     = nuisance.mov(:,~ismember(nuisance.mov_hdr, me));
nuisance.mov_hdr = nuisance.mov_hdr(~ismember(nuisance.mov_hdr, me));
nuisance.nmov    = size(nuisance.mov,2);

%   ----> do scrubbing anew if needed!

if strfind(doIt, 'm')
    timg = nimage;
    timg.frames     = size(nuisance.mov,1);
    timg.fstats     = nuisance.fstats;
    timg.fstats_hdr = nuisance.fstats_hdr;
    timg.mov        = nuisance.mov;
    timg.mov_hdr    = nuisance.mov_hdr;

    timg = timg.img_compute_scrub(scrub);

    nuisance.scrub     = timg.scrub;
    nuisance.scrub_hdr = timg.scrub_hdr;

    nuisance.scrub_hdr{end+1} = 'use';
    nuisance.scrub(:, end+1)  = timg.use';

    % generate header
    version = general_get_qunex_version();
    header = sprintf('# Generated by QuNex %s on %s\n#', version, datestr(now,'YYYY-mm-dd_HH.MM.SS'));

    general_write_table(file.tscrub, [timg.scrub timg.use'], [timg.scrub_hdr, 'use'], 'sum|%', '%-8s|%-8d|%-8d|%-7s', ' ', header);
end

%  ----> what are the frames to be used

nuisance.use = nuisance.scrub(:,ismember(nuisance.scrub_hdr, {'use'}))';

%   ----> lets setup nuisances!

if strfind(doIt, 'r')

    % ---> signal nuisance

    [nuisance.signal nuisance.signal_hdr] = general_read_table(file.nuisance);
    nuisance.nsignal = size(nuisance.signal,2);

    % ---> task matrix

    nuisance.task  = task;
    nuisance.ntask = size(task,2);

    % ---> event file

    if ~isempty(eventstring)
        rmodel          = general_create_task_regressors(file.fidlfile, nuisance.nframes, eventstring);
        runs            = rmodel.run;
        nuisance.events = runs(1).matrix;
        nuisance.effects     = {rmodel.regressor.name};
        nuisance.nevents     = size(nuisance(1).events, 2);
        nuisance.eventnamesr = runs(1).regressors;
        nuisance.eventnames  = rmodel.columns.event;
        nuisance.eventframes = rmodel.columns.frame;
    else
        rmodel.fidl.fidl     = 'None';
        rmodel.description   = 'None';
        rmodel.ignore        = 'None';
        nuisance.effects     = [];
        nuisance.events      = [];
        nuisance.nevents     = [];
        nuisance.eventnamesr = [];
        nuisance.eventnames  = [];
        nuisance.eventframes = [];
    end
    nuisance.nevents = size(nuisance.events,2);

end



% ======================================================
%   ----> run processing loop

task = ['shrl'];
exts = {'_s','_hpss',['_res-' rgsse options.glm_name],'_lpss'};
info = {'Smoothing','High-pass filtering','Removing residual','Low-pass filtering'};

% ---> clear existing data

if overwrite
    ext  = '';
    first = true;

    for current = doIt
        c = ismember(task, current);
        if any(c)
            sfile = [froot ext tail];
            if isempty(ext)
                ext = variant;
            end
            ext   = [ext exts{c}];
            tfile = [froot ext tail];
            if exist(tfile, 'file')
                if first
                    fprintf('\n---> removing old files:');
                    first = false;
                end
                fprintf('\n     ... %s', tfile);
                delete(tfile);
            end
        end
    end
end

% ---> start the loop

ext  = '';
img = nimage();


for current = char(doIt)

    % --- set the source and target filename

    c = ismember(task, current);
    sfile = [froot ext tail];
    if isempty(ext)
        ext = variant;
    end
    ext   = [ext exts{c}];
    tfile = [froot ext tail];

    % --- print info

    fprintf('\n\n%s %s ', info{c}, sfile);


    % --- run it on image

    if exist(tfile, 'file') & ~overwrite
        fprintf(' ... already completed!');
    else

        switch current
            case 's'
                if strcmp(tail, '.dtseries.nii')
                    wbSmooth(sfile, tfile, file, options);
                    img = nimage();
                elseif strcmp(tail, '.ptseries.nii')
                    fprintf(' WARNING: No spatial smoothing will be performed on ptseries images!');
                else
                    img = readIfEmpty(img, sfile, omit);
                    img.data = img.image2D;
                    if strcmp(options.smooth_mask, 'false')
                        img = img.img_smooth_3d(options.voxel_smooth, true);
                    else

                        % --- set up the smoothing mask

                        if strcmp(options.smooth_mask, 'nonzero')
                            bmask = img.zeroframes(1);
                            bmask.data = img.data(:,1) > 0;
                        elseif strcmp(options.smooth_mask, 'brainsignal')
                            bmask = img.zeroframes(1);
                            bmask.data = img.data(:,1) > 300;
                        elseif strcmp(options.smooth_mask, 'brainmask')
                            bmask = nimage(file.bmask);
                        else
                            bmask = options.smooth_mask;
                        end

                        % --- set up the dilation mask

                        if strcmp(options.dilate_mask, 'nonzero')
                            dmask = img.zeroframes(1);
                            dmask.data = img.data(:,1) > 0;
                        elseif strcmp(options.dilate_mask, 'brainsignal')
                            dmask = img.zeroframes(1);
                            dmask.data = img.data(:,1) > 300;
                        elseif strcmp(options.dilate_mask, 'brainmask')
                            dmask = nimage(file.bmask);
                        else
                            dmask = options.dilate_mask;
                        end

                        img = img.img_smooth_3d_masked(bmask, options.voxel_smooth, dmask, true);
                    end
                end
            case 'h'
                img = readIfEmpty(img, sfile, omit);
                hpsigma = ((1/TR)/options.hipass_filter)/2;
                img = img.img_filter(hpsigma, 0, omit, true, ignore.hipass);
            case 'l'
                img = readIfEmpty(img, sfile, omit);
                lpsigma = ((1/TR)/options.lopass_filter)/2;
                img = img.img_filter(0, lpsigma, omit, true, ignore.lopass);
            case 'r'
                img = readIfEmpty(img, sfile, omit);
                [img coeff] = regressNuisance(img, omit, nuisance, rgss, ignore.regress, options, [file.Xroot ext], rmodel);
                if docoeff
                    coeff.img_saveimage([froot ext '_coeff' tail]);
                end
        end

        if ~img.empty
            img.img_saveimage(tfile);
            fprintf(' ... saved!');
        end
    end


    % --- filter nuisance if needed

    switch current
        case 'h'
            hpsigma = ((1/TR)/options.hipass_filter)/2;
            tnimg = tmpimg(nuisance.signal', nuisance.use);
            tnimg = tnimg.img_filter(hpsigma, 0, omit, false, ignore.hipass);
            nuisance.signal = tnimg.data';

        case 'l'
            lpsigma = ((1/TR)/options.lopass_filter)/2;
            tnimg = tmpimg([nuisance.signal nuisance.task nuisance.events nuisance.mov]', nuisance.use);
            tnimg = tnimg.img_filter(0, lpsigma, omit, false, ignore.lopass);
            nuisance.signal = tnimg.data(1:nuisance.nsignal,:)';
            nuisance.task   = tnimg.data((nuisance.nsignal+1):(nuisance.nsignal+nuisance.ntask),:)';
            nuisance.events = tnimg.data((nuisance.nsignal+nuisance.ntask+1):(nuisance.nsignal+nuisance.ntask+nuisance.nevents),:)';
            nuisance.mov    = tnimg.data(end-nuisance.nmov:end,:)';
    end

end

fprintf('\n==> preproces BOLD finished successfully\n');

return




% ======================================================
%   ----> do GLM removal of nuisance regressors
%


function [img coeff] = regressNuisance(img, omit, nuisance, rgss, ignore, options, Xroot, rmodel)


    img.data = img.image2D;

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

    smask = ismember(nuisance.signal_hdr, rgss);
    nuisance.signal  = nuisance.signal(:,smask);
    nuisance.signal  = zscore(nuisance.signal);
    nuisance.nsignal = sum(smask);
    nuisance.signal_hdr = nuisance.signal_hdr(smask);

    %   ----> baseline and linear trend

    na = img.frames-omit;
    pl = zeros(na,1);
    for n = 1:na
        pl(n)= (n-1)/(na-1);
    end
    pl = pl-0.5;

    X = [ones(na,1) pl];

    effects     = {'Baseline', 'Trend'};
    hdr{end+1}  = sprintf('baseline');
    hdr{end+1}  = sprintf('trend');
    hdre{end+1} = sprintf('baseline');
    hdre{end+1} = sprintf('trend');
    hdrf(end+1:end+2) = [1 1];
    effect(end+1:end+2) = [1 2];
    eindex(end+1:end+2) = [1 1];


    %   ----> movement


    if movement
        X = [X nuisance.mov(omit+1:end,:)];
        for mi = 1:nuisance.nmov
            ts = sprintf('mov_%s', nuisance.mov_hdr{mi});
            effects{end+1}  = ts;
            hdr{end+1}      = ts;
            hdre{end+1}     = ts;
            hdrf(end+1)     = 1;
            effect(end+1)   = find(ismember(effects, ts));
            eindex(end+1)   = 1;
        end
    end
    
    if movementDer
        if omit
            X = [X diff(nuisance.mov(omit:end,:))];
        else
            X = [X [zeros(1,nuisance.nmov); diff(nuisance.mov)]];
        end
        for mi = 1:nuisance.nmov
            ts = sprintf('mov_%s_1d', nuisance.mov_hdr{mi});
            effects{end+1} = ts;
            hdr{end+1}     = ts;
            hdre{end+1}    = ts;
            hdrf(end+1)    = 1;
            effect(end+1)  = find(ismember(effects, ts));
            eindex(end+1)  = 1;
        end
    end
    
    if movementSQ
        X = [X nuisance.mov(omit+1:end,:).^2];
        for mi = 1:nuisance.nmov
            ts = sprintf('mov_%s_Sq', nuisance.mov_hdr{mi});
            effects{end+1}  = ts;
            hdr{end+1}      = ts;
            hdre{end+1}     = ts;
            hdrf(end+1)     = 1;
            effect(end+1)   = find(ismember(effects, ts));
            eindex(end+1)   = 1;
        end
    end
    
    if movementDerSQ
         if omit
            X = [X diff(nuisance.mov(omit:end,:)).^2];
        else
            X = [X [zeros(1,nuisance.nmov); diff(nuisance.mov).^2]];
        end
        for mi = 1:nuisance.nmov
            ts = sprintf('mov_%s_1dSq', nuisance.mov_hdr{mi});
            effects{end+1} = ts;
            hdr{end+1}     = ts;
            hdre{end+1}    = ts;
            hdrf(end+1)    = 1;
            effect(end+1)  = find(ismember(effects, ts));
            eindex(end+1)  = 1;
        end
    end

    %   ----> signal

    if sum(smask)
        X = [X zscore(nuisance.signal(omit+1:end,:))];
        for mi = 1:nuisance.nsignal
            ts             = sprintf('%s', nuisance.signal_hdr{mi});
            effects{end+1} = ts;
            hdr{end+1}     = ts;
            hdre{end+1}    = ts;
            hdrf(end+1)    = 1;
            effect(end+1)  = find(ismember(effects, nuisance.signal_hdr{mi}));
            eindex(end+1)  = 1;
        end

        if nuisanceDer
            X = [X [zeros(1, nuisance.nsignal); diff(nuisance.signal(omit+1:end,:))]];
            for mi = 1:nuisance.nsignal
                ts             = sprintf('%s_1d', nuisance.signal_hdr{mi});
                effects{end+1} = ts;
                hdr{end+1}     = ts;
                hdre{end+1}    = ts;
                hdrf(end+1)    = 1;
                effect(end+1)  = find(ismember(effects, nuisance.signal_hdr{mi}));
                eindex(end+1)  = 1;
            end
        end
    end


    %   ----> task

    if task && nuisance.ntask
        X = [X nuisance.task(omit+1:end,:)];
        for mi = 1:nuisance.ntask
            ts             = sprintf('task_%d', mi);
            effects{end+1} = ts;
            hdr{end+1}     = ts;
            hdre{end+1}    = ts;
            hdrf(end+1)    = 1;
            effect(end+1)  = find(ismember(effects, ts));
            eindex(end+1)  = 1;
        end
    end


    %   ----> events

    if event && nuisance.nevents
        X = [X nuisance.events(omit+1:end,:)];
        for mi = 1:nuisance.nevents
            ts             = nuisance.eventnames{mi};
            effects{end+1} = ts;
            hdr{end+1}     = ts;
            hdre{end+1}    = ts;
            hdrf(end+1)    = 1;
            effect(end+1)  = find(ismember(effects, nuisance.eventnames{mi}));
            eindex(end+1)  = 1;
        end
    end


    %   ----> do GLM

    if ~strcmp(ignore, 'keep')
        fprintf(' excluding %d bad frames', sum(img.use == 0));
        mask = img.use == 1;
        X = X(mask(omit+1:end),:);
    else
        mask = true(1, img.frames);
    end
    mask(1:omit) = false;

    Y = img.sliceframes(mask);

    [coeff res] = Y.img_glm_fit(X);
    img.data(:,mask) = res.image2D;
    coeff = [coeff Y.img_stats({'m', 'sd'})];

    if min(mask) == 0
        if strcmp(ignore, 'mark')
            fprintf(' marking %d bad frames ', sum(~mask));
            img.data(:, ~mask) = NaN;
        elseif ismember({ignore}, {'linear', 'spline'})
            fprintf(' %s interpolating %d bad frames ', ignore, sum(~mask));
            x  = [1:length(mask)]';
            xi = x;
            x  = x(mask);
            img.data = interp1(x, img.data(:, mask)', xi, ignore, 'extrap')';
        end
    end

    % --- header info

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

    % generate header
    version = general_get_qunex_version();
    header = sprintf('# Generated by QuNex %s on %s\n#', version, datestr(now, 'YYYY-mm-dd_HH.MM.SS'));

    pre      = sprintf('%s# fidl: %s\n# model: %s\n# bolds: %d\n# effects: %s\n# effect: %s\n# eindex: %s\n# ignore: %s\n# event: %s\n# frame: %s', header, rmodel.fidl.fidl, rmodel.description, 1, xeffects, xeffect, xeindex, rmodel.ignore, xevents, xframes(1:end-1));
    xtable   = general_write_table(xfile, [X zeros(sum(mask==1), 2)], hdr, 'sd|mean|min|max', [], [], pre);

    if ismember(options.glm_matrix, {'image', 'both'})
        mimg = X;
        mimg = mimg / (max(max(abs(mimg))) * 2);
        mimg = mimg + 0.5;
        try
            imwrite(mimg, [Xroot '.png']);
        catch
            fprintf('\n---> WARNING: Could not save GLM PNG image! Check supported image formats!');
        end
    end

    coeff = coeff.img_embed_meta(xtable, 64, 'GLM');

return


% ======================================================
%                           ----> create temporary image
%

function [img] = tmpimg(data, use)

    img = nimage();
    img.data = data;
    img.use  = use;
    [img.voxels img.frames] = size(data);


% ======================================================
%                                    ----> read if empty
%

function [img] = readIfEmpty(img, src, omit)

    if isempty(img) || img.empty
        fprintf('\n---> reading %s ', src);
        img = nimage(src);
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
        s  = getenv('DYDL_FRAMEWORK_PATH');
        sl = getenv('DYLD_LIBRARY_PATH');
        ll = getenv('LD_LIBRARY_PATH');
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


