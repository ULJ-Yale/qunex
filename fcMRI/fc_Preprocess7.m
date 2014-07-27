function [] = fc_Preprocess7(subjectf, bold, omit, do, rgss, task, efile, TR, eventstring, variant, overwrite, tail, scrub, ignores, options)

%function [] = fc_Preprocess7(subjectf, bold, omit, do, rgss, task, efile, TR, eventstring, variant, overwrite, tail, scrub, ignores, options)
%
%  Inputs
%       subjectf    - the folder with subjects images and data
%       bold        - the number of bold file to process
%       omit        - the number of frames to omit at the start of each bold [5]
%       do          - which steps to perform and in what order
%           s - 3D spatial smoothing
%           h - highpass temporal filter
%           r - regresses out nuisance, optional parameter:
%           c - save coefficients in _coeff file
%           l - lowpass temporal filter
%           m - motion scrubbing
%       rgss        - what to regress in the regression step, comma separated list
%           m   - motion
%           V   - ventricles
%           WM  - white matter
%           WB  - whole brain
%           mWB - masked whole brain
%           1d  - first derivatives of nuisance signal and movement
%           t   - task
%           e   - event
%       task        - matrix of custom regressors to be entered in GLM
%       efile       - event (fild) file to be used for removing task structure [none]
%       TR          - TR of the data [2.5]
%       eventstring - a string specifying the events to regress and the regressors to use [none]
%       variant     - a string to be prepended to files [none]
%       overwrite   - whether old files should be overwritten [false]
%       tail        - what file extension to expect and use for images [.4dfp.img]
%       scrub       - the description of how to compute scrubbing - a string in 'param:value|param:value' format
%                     parameters:
%                     - radius   : head radius in mm [50]
%                     - fdt      : frame displacement threshold
%                     - dvarsmt  : dvarsm threshold
%                     - dvarsmet : dvarsme threshold
%                     - after    : how many frames after the bad one to reject
%                     - before   : how many frames before the bad one to reject
%                     - reject   : which criteria to use for rejection (mov, dvars, dvarsme, idvars, udvars ...)
%                     if empty, the existing scrubbing data is used
%       ignores     - how to deal with the frames marked as not used in filering and regression steps
%                     specified in a single string, separated with pipes
%                     hipass  - keep / linear / spline
%                     regress - keep / ignore
%                     lopass  - keep / linear /spline
%                     example: 'hipass:linear|regress:ignore|lopass:spline'
%       options     - additional options that can be set using the 'key=value|key=value' string:
%                     surface_smooth: 6
%                     volume_smooth:  6
%                     voxel_smooth:   2
%                     lopass_filter:  0.08
%                     hipass_filter:  0.009
%                     framework_path:
%                     wb_command_path:
%                     omp_threads:    0
%
%   Additional notes
%   - Taks matrix is prepended to the GLM regression
%   - Event data is read from efile fidl event file
%   - fidl files should be placed in the /images/functional/events/ and named boldX_efile
%
%   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
%
%   2007-10-29  Written by Grega Repovš
%
%   2007-11-15  Grega Repovs
%               - Added regression of events
%
%   2009-01-19  Grega Repovs
%               - Adapted for new fcMRI workflow
%
%   2009-05-18  Grega Repovs
%               - Changed processing of filenames to alow arbitrary combination of steps
%
%   2012-09-08  Grega Repovs
%               - Implemented the option of specifying arbitrary ROI to be used for
%                 definition of nuisance signal
%               - Cleaned up help text
%
%   2013-10-20 Grega Repovs (v0.9.3)
%              - Added option for ignoring the frames marked as not to be used
%
%   2014-07-17 Grega Repovs (v0.9.4)
%              - Moved to using external nuisance file and preprocessing nuisance in parallel
%              - Scrubbing can now be re-defined here and a scrubbing file is saved (separately for variant if set)
%
%   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if nargin < 15, options = '';       end
if nargin < 14, ignores = '';       end
if nargin < 13, scrub = '';         end
if nargin < 12, tail = '.4dfp.img'; end
if nargin < 11, overwrite = false;  end
if nargin < 10, variant = '';       end
if nargin < 9,  eventstring = '';   end
if nargin < 8,  TR = 2.5;           end

default = 'surface_smooth=6|volume_smooth=6|voxel_smooth=2|lopass_filter=0.08|hipass_filter=0.009|framework_path=|wb_command_path=|omp_threads=0';
options = g_ParseOptions([], options, default);

fprintf('\nRunning preproces script 7 v0.9.4 [%s]\n', tail);

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
rgss  = regexp(rgss, '|,|;| |\|', 'split');



% ======================================================
%   ----> prepare paths

froot = strcat(subjectf, ['/images/functional/bold' int2str(bold)]);

file.movdata   = strcat(subjectf, ['/images/functional/movement/bold' int2str(bold) '_mov.dat']);
file.oscrub    = strcat(subjectf, ['/images/functional/movement/bold' int2str(bold) '.scrub']);
file.tscrub    = strcat(subjectf, ['/images/functional/movement/bold' int2str(bold) variant '.scrub']);
file.bstats    = strcat(subjectf, ['/images/functional/movement/bold' int2str(bold) '.bstats']);
file.fidlfile  = strcat(subjectf, ['/images/functional/events/bold'   int2str(bold) efile]);

file.nuisance  = strcat(subjectf, ['/images/functional/movement/bold' int2str(bold) '.nuisance']);

file.lsurf     = strcat(subjectf, ['/images/segmentation/hcp/fsaverage_LR32k/L.midthickness.32k_fs_LR.surf.gii']);
file.rsurf     = strcat(subjectf, ['/images/segmentation/hcp/fsaverage_LR32k/R.midthickness.32k_fs_LR.surf.gii']);


% ======================================================
%   ----> are we doing coefficients?

docoeff = false;
if strfind(do, 'c')
    docoeff = true;
    do = strrep(do, 'c', '');
end


% ======================================================
%   ----> deal with nuisance and scrubbing

%   ----> read data

[nuisance.fstats nuisance.fstats_hdr] = g_ReadTable(file.bstats);
[nuisance.scrub  nuisance.scrub_hdr]  = g_ReadTable(file.oscrub);
[nuisance.mov    nuisance.mov_hdr]    = g_ReadTable(file.movdata);

nuisance.nframes = size(nuisance.mov,1);

%   ----> exclude extra data from mov

me               = {'frame', 'scale'};
nuisance.mov     = nuisance.mov(:,~ismember(nuisance.mov_hdr, me));
nuisance.mov_hdr = nuisance.mov_hdr(~ismember(nuisance.mov_hdr, me));
nuisance.nmov    = size(nuisance.mov,2);

%   ----> do scrubbing anew if needed!

if strfind(do, 'm')
    timg = gmrimage;
    timg.fstats     = nuisance.fstats;
    timg.fstats_hdr = nuisance.fstats_hdr;
    timg.mov        = nuisance.mov;
    timg.mov_hdr    = nuisance.mov_hdr;

    timg = timg.mri_ComputeScrub(scrub);

    nuisance.scrub     = timg.scrub;
    nuisance.scrub_hdr = timg.scrub_hdr;

    g_WriteTable(file.tscrub, [timg.scrub timg.use'], [timg.scrub_hdr, 'use'], 'sum|%', '%-8s|%-8d|%-8d|%-7s', ' ');
end

%  ----> what are the frames to be used

nuisance.use = nuisance.scrub(:,ismember(nuisance.scrub_hdr, {'use'}))';

%   ----> lets setup nuisances!

if strfind(do, 'r')

    % ---> signal nuisance

    [nuisance.signal nuisance.signal_hdr] = g_ReadTable(file.nuisance);
    nuisance.nsignal = size(nuisance.signal,2);

    % ---> task matrix

    nuisance.task  = task;
    nuisance.ntask = size(task,2);

    % ---> event file

    if ~isempty(eventstring)
        runs            = g_CreateTaskRegressors(file.fidlfile, nuisance.nframes, eventstring);
        nuisance.events = runs(1).matrix;
    else
        nuisance.events = [];
    end
    nuisance.nevents = size(nuisance.events,2);

end



% ======================================================
%   ----> run processing loop

task = ['shrl'];
exts = {'_g7','_hpss',['_res-' rgsse],'_lpss'};
info = {'Smoothing','High-pass filtering','Removing residual','Low-pass filtering'};
ext  = '';

img = gmrimage();

for current = do

    % --- set the source and target filename

    c = ismember(task, current);
    sfile = [froot ext tail];
    if isempty(ext)
        ext = variant;
    end
    ext   = [ext exts{c}];
    tfile = [froot ext tail];

    % --- print info

    fprintf('\n%s %s ', info{c}, sfile);


    % --- run it on image

    if exist(tfile, 'file') & ~overwrite
        fprintf(' ... already completed!');
    else

        switch current
            case 's'
                if strcmp(tail, '.dtseries.nii')
                    wbSmooth(sfile, tfile, file, options);
                    img = gmrimage();
                else
                    img = readIfEmpty(img, sfile, omit);
                    img = img.mri_Smooth3D(options.voxel_smooth, true);
                end
            case 'h'
                img = readIfEmpty(img, sfile, omit);
                hpsigma = ((1/TR)/options.hipass_filter)/2;
                img = img.mri_Filter(hpsigma, 0, omit, true, ignore.hipass);
            case 'l'
                img = readIfEmpty(img, sfile, omit);
                lpsigma = ((1/TR)/options.lopass_filter)/2;
                img = img.mri_Filter(0, lpsigma, omit, true, ignore.lopass);
            case 'r'
                img = readIfEmpty(img, sfile, omit);
                [img coeff] = regressNuisance(img, omit, nuisance, rgss, ignore.regress);
                if docoeff
                    coeff.mri_saveimage([froot ext '_coeff' tail]);
                end
        end

        if ~img.empty
            img.mri_saveimage(tfile);
            fprintf(' ... saved!');
        end
    end


    % --- filter nuisance if needed

    switch current
        case 'h'
            hpsigma = ((1/TR)/options.hipass_filter)/2;
            tnimg = tmpimg(nuisance.signal', nuisance.use);
            tnimg = tnimg.mri_Filter(hpsigma, 0, omit, false, ignore.hipass);
            nuisance.signal = tnimg.data';

        case 'l'
            lpsigma = ((1/TR)/options.lopass_filter)/2;
            tnimg = tmpimg([nuisance.signal nuisance.task nuisance.events nuisance.mov]', nuisance.use);
            tnimg = tnimg.mri_Filter(0, lpsigma, omit, false, ignore.lopass);
            nuisance.signal = tnimg.data(1:nuisance.nsignal,:)';
            nuisance.task   = tnimg.data((nuisance.nsignal+1):(nuisance.nsignal+nuisance.ntask),:)';
            nuisance.events = tnimg.data((nuisance.nsignal+nuisance.ntask+1):(nuisance.nsignal+nuisance.ntask+nuisance.nevents),:)';
            nuisance.mov    = tnimg.data(end-nuisance.nmov:end,:)';
    end

end

return




% ======================================================
%   ----> do GLM removal of nuisance regressors
%


function [img coeff] = regressNuisance(img, omit, nuisance, rgss, ignore)


    img.data = img.image2D;

    derivatives = ismember('1d', rgss);
    movement    = ismember('m', rgss);
    task        = ismember('t', rgss);
    event       = ismember('e', rgss);
    rgss        = rgss(~ismember(rgss, {'1d', 'e', 't', 'm'}));

    %   ----> baseline and linear trend

    na = img.frames-omit;
    pl = zeros(na,1);
    for n = 1:na
        pl(n)= (n-1)/(na-1);
    end
    pl = pl-0.5;

    X = [ones(na,1) pl];


    %   ----> movement

    if movement
        X = [X nuisance.mov(omit+1:end,:)];
        if derivatives
            if omit, z = []; else z = zeros(1,nuisance.nmov); end
            X = [X [z; diff(nuisance.mov(omit:end,:))]];
        end
    end


    %   ----> signal

    smask = ismember(nuisance.signal_hdr,rgss);
    if sum(smask)
        X = [X nuisance.signal(omit+1:end,smask)];
        if derivatives
            X = [X [zeros(1,sum(smask)); diff(nuisance.signal(omit+1:end,smask))]];
        end
    end


    %   ----> task

    if task && nuisance.ntask
        X = [X nuisance.task(omit+1:end,:)];
    end


    %   ----> events

    if event && nuisance.nevents
        X = [X nuisance.events(omit+1:end,:)];
    end


    %   ----> do GLM

    if strcmp(ignore, 'ignore')
        fprintf(' ignoring %d bad frames', sum(img.use == 0));
        mask = img.use;
        X = X(mask(omit+1:end),:);
    else
        mask = true(1, img.frames);
    end
    mask(1:omit) = false;

    Y = img.sliceframes(mask);

    [coeff res] = Y.mri_GLMFit(X);
    img.data(:,mask) = res.image2D;

return


% ======================================================
%                           ----> create temporary image
%

function [img] = tmpimg(data, use)

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
        s = getenv('DYDL_FRAMEWORK_PATH');
        if isempty(strfind(s, options.framework_path))
            fprintf('\n     ... setting DYDL_FRAMEWORK_PATH to %s', options.framework_path);
            setenv('DYDL_FRAMEWORK_PATH', [options.framework_path ':' s]);
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

