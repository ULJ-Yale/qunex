function [TS] = fc_PreprocessConc2(subjectf, bolds, do, TR, omit, rgss, task, efile, eventstring, variant, overwrite, tail, scrub, ignores, options)

%function [TS] = fc_PreprocessConc2(subjectf, bolds, do, TR, omit, rgss, task, efile, eventstring, variant, overwrite, tail, scrub, ignores, options)
%   (c) Copyright Grega Repovš, 2011-01-24
%
%   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
%
%   Inputs
%       subjectf    - the folder with subjects images and data
%       bolds       - vector of bold runs in the order of the conc file
%       do          - which steps to perform and what order
%           s - 3D spatial smoothing
%           h - highpass temporal filter
%           r - regresses out nuisance, optional parameter:
%               0 - separate nuisance, joint task regressors across runs [default]
%               1 - separate nuisance, separate task regressors for each run
%               2 - joint nuisance, joint task regressors across all runs
%           c - save coefficients in _coeff file
%           p - saves png image files of nusance ROI mask
%           l - lowpass temporal filter
%           m - motion scrubbing
%
%       TR          - TR of the data [2.5]
%       omit        - the number of frames to omit at the start of each bold [5]
%       rgss        - what to regress in the regression step
%           m  - motion
%           V  - ventricles
%           WM - white matter
%           WB - whole brain
%           1d - first derivative
%           t  - task
%           e  - events
%
%       task        - matrix of custom regressors to be entered in GLM
%       efile       - event (fild) file to be used for removing task structure [none]
%       eventstring - a string specifying the events to regress and the regressors to use [none]
%       variant     - a string to be prepended to files [none]
%       overwrite   - whether old files should be overwritten [false]
%       tail        - what file extension to expect and use for images [.4dfp.img]
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
%   Does the preprocesing for the files from subjectf folder.
%   Saves images in ftarget folder
%   Saves new conc files in the ctarget folder
%   Omits "omit" number of start frames from bandpassing and GLM
%   Does the steps specified in "do":
%
%   In regression it uses the regressors specified in "regress":
%
%   It includes task matrix to GLM regression
%   It reads event data from efile fidl event file
%   - these should be placed in the /images/functional/events/ and named boldX_efile
%
%   It takes eventstring to describe which events to model and for how many frames
%
%   To Do
%   - make movement reading more flexible (n of columns and possibly other formats)
%
%
%   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
%
%   2013-10-20 Grega Repovs (v0.9.3)
%              - Added option for ignoring the frames marked as not to be used.
%
%   2014-07-20 Grega Repovs (v0.9.5)
%              - Rewrote with separate nuisance signal extraction and parallel processing.
%
%   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if nargin < 15, options = '';                               end
if nargin < 14, ignores = '';                               end
if nargin < 13, scrub = '';                                 end
if nargin < 12 || isempty(tail), tail = '.4dfp.img';        end
if nargin < 11 || isempty(overwrite), overwrite = false;    end
if nargin < 10, variant = '';                               end
if nargin < 9,  eventstring = '';                           end
if nargin < 8,  efile = '';                                 end
if nargin < 7,  task = [];                                  end
if nargin < 6,  rgss = '';                                  end
if nargin < 5 || isempty(omit), omit = [];                  end
if nargin < 4 || isempty(TR), TR = 2.5;                     end

default = 'surface_smooth=6|volume_smooth=6|voxel_smooth=2|lopass_filter=0.08|hipass_filter=0.009|framework_path=|wb_command_path=|omp_threads=0';
options = g_ParseOptions([], options, default);



fprintf('\nRunning preproces conc 2 script v0.9.5 [%s]\n', tail);


% ======================================================
%                          ----> prepare basic variables

nbolds = length(bolds);

ignore.hipass  = 'keep';
ignore.regress = 'keep';
ignore.lopass  = 'keep';

ignores = regexp(ignores, ',|;|:|\|', 'split');
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
rtype = 0;


% ======================================================
%                                     ---> prepare paths

for b = 1:nbolds

    % ---> general paths

    bnum = int2str(bolds(b));
    file(b).froot       = strcat(subjectf, ['/images/functional/bold' bnum]);

    file(b).movdata     = strcat(subjectf, ['/images/functional/movement/bold' bnum '_mov.dat']);
    file(b).oscrub      = strcat(subjectf, ['/images/functional/movement/bold' bnum '.scrub']);
    file(b).tscrub      = strcat(subjectf, ['/images/functional/movement/bold' bnum variant '.scrub']);
    file(b).bstats      = strcat(subjectf, ['/images/functional/movement/bold' bnum '.bstats']);
    file(b).nuisance    = strcat(subjectf, ['/images/functional/movement/bold' bnum '.nuisance']);
    file(b).fidlfile    = strcat(subjectf, ['/images/functional/events/' efile]);

    eroot               = strrep(efile, '.fidl', '');
    file(b).croot       = strcat(subjectf, ['/images/functional/conc_' eroot]);
    file(b).cfroot      = strcat(subjectf, ['/images/functional/concs/' eroot]);

    file(b).lsurf       = strcat(subjectf, ['/images/segmentation/hcp/fsaverage_LR32k/L.midthickness.32k_fs_LR.surf.gii']);
    file(b).rsurf       = strcat(subjectf, ['/images/segmentation/hcp/fsaverage_LR32k/R.midthickness.32k_fs_LR.surf.gii']);

end


% ======================================================
%                       ----> are we doing coefficients?

docoeff = false;
if strfind(do, 'c')
    docoeff = true;
    do = strrep(do, 'c', '');
end


% ======================================================
%                  ---> deal with nuisance and scrubbing

allframes = 0;
frames    = zeros(1, nbolds);

for b = 1:nbolds

    %   ----> read data

    [nuisance(b).fstats nuisance(b).fstats_hdr] = g_ReadTable(file(b).bstats);
    [nuisance(b).scrub  nuisance(b).scrub_hdr]  = g_ReadTable(file(b).oscrub);
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

    if strfind(do, 'm')
        timg = gmrimage;
        timg.fstats     = nuisance.fstats;
        timg.fstats_hdr = nuisance.fstats_hdr;
        timg.mov        = nuisance.mov;
        timg.mov_hdr    = nuisance.mov_hdr;

        timg = timg.mri_ComputeScrub(scrub);

        nuisance(b).scrub     = timg.scrub;
        nuisance(b).scrub_hdr = timg.scrub_hdr;

        g_WriteTable(file(b).tscrub, [timg.scrub timg.use'], [timg.scrub_hdr, 'use'], 'sum|%', '%-8s|%-8d|%-8d|%-7s', ' ');
    end

    %  ----> what are the frames to be used

    nuisance(b).use = nuisance(b).scrub(:,ismember(nuisance(b).scrub_hdr, {'use'}))';

    %   ----> lets setup nuisances!

    if strfind(do, 'r')

        % ---> signal nuisance

        [nuisance(b).signal nuisance(b).signal_hdr] = g_ReadTable(file(b).nuisance);
        nuisance(b).nsignal = size(nuisance(b).signal,2);

    end

end


%   ----> task and event nuisance

if strfind(do, 'r')

    if ~isempty(eventstring)
        runs = g_CreateTaskRegressors(file(1).fidlfile, frames, eventstring);
    else
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
            nuisance(b).task  = task(bstart:bend,:);
            nuisance(b).ntask = size(task,2);
        end

        nuisance(b).events  = runs(b).matrix;
        nuisance(b).nevents = size(nuisance(b).events,2);

        bstart = bstart + nuisance(b).nframes;
    end

    % ---> regression type

    if strfind(do, 'r1'), rtype = 1; end
    if strfind(do, 'r2'), rtype = 2; end
end





% ======================================================
%                               ---> run processing loop

tasklist = ['shrl'];
exts     = {'_g7','_hpss',['_res-' rgsse],'_lpss'};
info     = {'Smoothing','High-pass filtering','Removing residual','Low-pass filtering'};
ext      = '';

for b = 1:nbolds
    img(b) = gmrimage();
end

dor      = true;

for current = do

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

    fprintf('\n%s\n', info{c});

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
                        else
                            img(b) = readIfEmpty(img(b), file(b).sfile, omit);
                            img(b) = img(b).mri_Smooth3D(options.voxel_smooth, true);
                        end
                    case 'h'
                        img(b) = readIfEmpty(img(b), file(b).sfile, omit);
                        hpsigma = ((1/TR)/options.hipass_filter)/2;
                        img(b) = img(b).mri_Filter(hpsigma, 0, omit, true, ignore.hipass);
                    case 'l'
                        img(b) = readIfEmpty(img(b), file(b).sfile, omit);
                        lpsigma = ((1/TR)/options.lopass_filter)/2;
                        img(b) = img(b).mri_Filter(0, lpsigma, omit, true, ignore.lopass);
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
        if exist(file(b).tfile, 'file') && ~overwrite
            fprintf('... already completed!');
            img(b).empty = true;
        else
            for b = 1:nbolds
                img(b) = readIfEmpty(img(b), file(b).sfile, omit);
            end
            fprintf('\n---> running regression ');
            [img coeff] = regressNuisance(img, omit, nuisance, rgss, rtype, ignore.regress);
            fprintf('... done!');
            for b = 1:nbolds
                fprintf('\n---> saving %s ', file(b).tfile);
                img(b).mri_saveimage(file(b).tfile);
                fprintf('... done!');
            end

            if docoeff
                cname = [file(b).croot ext '_coeff' tail];
                fprintf('\n---> saving %s ', cname);
                coeff.mri_saveimage(cname);
                fprintf('... done!');
            end
        end
        dor = false;
    end

    if exist(file(b).tconc, 'file') && ~overwrite
        fprintf('\n---> conc file already saved!');
    else
        fprintf('\n---> saving conc file ');
        gmrimage.mri_SaveConcFile(file(b).tconc, {file.tfile});
        fprintf('... done!');
    end

end

return


% ======================================================
%   ----> do GLM removal of nuisance regressors
%


function [img coeff] = regressNuisance(img, omit, nuisance, rgss, rtype, ignore)

    % ---> basic settings

    nbolds = length(img);
    frames = zeros(1, nbolds);

    derivatives = ismember('1d', rgss);
    movement    = ismember('m', rgss);
    task        = ismember('t', rgss);
    event       = ismember('e', rgss);
    rgss        = rgss(~ismember(rgss, {'1d', 'e', 't', 'm'}));

    % ---> bold starts, frames

    st = 1;
    smask = ismember(nuisance(1).signal_hdr, rgss);
    for b = 1:nbolds
        bS(b)     = st;
        frames(b) = nuisance(b).nframes;
        bE(b)     = st + frames(b) - 1;
        st        = st + frames(b);

        nuisance(b).signal  = nuisance(b).signal(:,smask);
        nuisance(b).nsignal = sum(smask);
    end

    % ---> X size and init

    nB = 2;
    nS = nuisance(1).nsignal;
    if task,     nT = nuisance(1).ntask;   else nT = 0; end
    if movement, nM = nuisance(1).nmov;    else nM = 0; end
    if event,    nE = nuisance(1).nevents; else nE = 0; end
    nBj = nB*nbolds;
    nTj = nT;

    switch rtype
        case 0
            joinn = false;
            joine = true;
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

    if derivatives
        nX = nBj + nTj + nMj*2 + nSj*2 + nEj;
    else
        nX = nBj + nTj + nMj + nSj + nEj;
    end

    X = zeros(sum(frames), nX);

    %   ----> baseline and linear trend

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
    end


    %   ----> movement

    if movement
        for b = 1:nbolds
            xE = xS + nM - 1;
            X(bS(b):bE(b), xS:xE) = nuisance(b).mov;
            if ~joinn
                xS = xS+nM;
            end
        end
        xS = xS+nM;
    end


    %   ----> signal

    for b = 1:nbolds
        xE = xS + nS - 1;
        X(bS(b):bE(b), xS:xE) = nuisance(b).signal;
        if ~joinn
            xS = xS+nS;
        end
    end
    xS = xS+nS;


    %   ----> movement & signal derivatives

    if derivatives

        %   ----> movement

        if movement
            for b = 1:nbolds
                xE = xS + nM - 1;
                X(bS(b):bE(b), xS:xE) = [zeros(1,nuisance(b).nmov); diff(nuisance(b).mov)];
                if ~joinn
                    xS = xS+nM;
                end
            end
            xS = xS+nM;
        end

        %   ----> signal

        for b = 1:nbolds
            xE = xS + nS - 1;
            X(bS(b):bE(b), xS:xE) = [zeros(omit+1, nuisance(b).nsignal); diff(nuisance(b).signal(omit+1:end,:))];
            if ~joinn
                xS = xS+nS;
            end
        end
        xS = xS+nS;
    end


    %   ----> events

    if event
        for b = 1:nbolds
            xE = xS + nE - 1;
            X(bS(b):bE(b), xS:xE) = nuisance(b).events;
            if ~joine
                xS = xS+nE;
            end
        end
        xS = xS+nE;
    end


    %   ----> task

    if task
        xE = xS + nT - 1;
        for b = 1:nbolds
            X(bS(b):bE(b), xS:xE) = nuisance(b).task;
        end
        xS = xS+nT;
    end

    %   ----> combine data in a single image
    fprintf('.');

    %   ---> first create per bold masks

    masks   = {};
    mframes = zeros(1,nbolds);
    nmask   = [];
    if strcmp(ignore, 'ignore'), fprintf(' ignoring'); end
    for b = 1:nbolds
        if strcmp(ignore, 'ignore')
            fprintf(' %d', sum(img(b).use == 0));
            mask = img(b).use;
        else
            mask = true(1, img(b).frames);
        end
        mask(1:omit) = false;
        masks{b}     = mask;
        mframes(b)   = sum(mask);
        nmask        = [nmask mask];
    end
    if strcmp(ignore, 'ignore'), fprintf(' frames '); end

    %   ---> create and fill placeholder image

    Y = img(1).zeroframes(sum(mframes));

    for b = 1:nbolds
        fstart = sum(mframes(1:b-1)) + 1;
        fend   = sum(mframes(1:b));
        Y.data(:, fstart:fend) = img(b).data(:,masks{b});
    end

    %   ----> mask nuisance and do GLM
    fprintf('.');

    X = X(nmask==1, :);
    [coeff res] = Y.mri_GLMFit(X);

    %   ----> put data back into images
    fprintf('.');

    for b = 1:nbolds
        fstart = sum(mframes(1:b-1)) + 1;
        fend   = sum(mframes(1:b));
        img(b).data(:,masks{b}) = res.data(:,fstart:fend);
    end

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

    % --- set up variables

    tmpf = strrep(tfile, 'g7', 'g7flipped');

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
    comm = sprintf('wb_command -cifti-smoothing %s %f %f COLUMN %s -left-surface %s -right-surface %s', sfile, options.surface_smooth, options.volume_smooth, tmpf, file.lsurf, file.rsurf);
    [status out] = system(comm);

    if status
        fprintf('\nERROR: wb_command finished with error!\n       ran: %s\n', comm);
        fprintf('\n --- wb_command output ---\n%s\n --- end wb_command output ---\n', out);
        error('\nAborting processing!');
    else
        fprintf(' ... done!');
    end

    fprintf('\n     ... transposing');
    comm = sprintf('wb_command -cifti-transpose %s %s', tmpf, tfile);
    [status out] = system(comm);

    if status
        fprintf('\nERROR: wb_command finished with error!\n       ran: %s\n', comm);
        fprintf('\n --- wb_command output ---\n%s\n --- end wb_command output ---\n', out);
        error('\nAborting processing!');
    else
        fprintf(' ... done!');
    end


    fprintf('\n     ... removing temporary flipped file');
    delete(tmpf);

    fprintf(' ... done!');
