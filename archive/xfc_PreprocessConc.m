function [TS] = fc_PreprocessConc(subjectf, bolds, doIt, TR, omit, rgss, task, efile, eventstring, variant, wbmask, sbjroi, overwrite, tail, nroi, ignores)

%function [TS] = fc_PreprocessConc(subjectf, bolds, doIt, TR, omit, rgss, task, efile, eventstring, variant, wbmask, sbjroi, overwrite, tail, nroi, ignores)
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
%
%       TR          - TR of the data [2.5]
%       omit        - the number of frames to omit at the start of each bold [5]
%       rgss        - what to regress in the regression step
%           m  - motion
%           v  - ventricles
%           wm - white matter
%           wb - whole brain
%           d  - first derivative
%           t  - task
%           e  - events
%
%       task        - matrix of custom regressors to be entered in GLM
%       efile       - event (fild) file to be used for removing task structure [none]
%       eventstring - a string specifying the events to regress and the regressors to use [none]
%       variant     - a string to be prepended to files [none]
%       wbmask      - a mask used to exclude ROI from the whole-brain nuisance regressor [none]
%       sbjroi      - a mask used to create subject specific wbmask [none]
%       overwrite   - whether old files should be overwritten [false]
%       tail        - what file extension to expect and use for images [.4dfp.img]
%       nroi        - ROI.names file to use to define additional nuisance ROI to regress out
%                     when additionally provided a list of ROI, those will not be masked by
%                     bold brain mask (e.g. 'nroi.names|eyes,scull')
%       ignores     - how to deal with the frames marked as not used in filering and regression steps
%                     specified in a single string, separated with pipes
%                     hipass  - keep / linear / spline
%                     regress - keep / ignore
%                     lopass  - keep / linear /spline
%                     example: 'hipass:linear|regress:ignore|lopass:spline'

%   Does the preprocesing for the files from subjectf folder.
%   Saves images in ftarget folder
%   Saves new conc files in the ctarget folder
%   Omits "omit" number of start frames from bandpassing and GLM
%   Does the steps specified in "do":
%
%   In regression it uses the regressors specified in "regress":
%
%   It prepends task matrix to GLM regression
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
%              - Added option for ignoring the frames marked as not to be used
%
%   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if nargin < 16, ignores = [];                               end
if nargin < 15, nroi = [];                                  end
if nargin < 14 || isempty(tail), tail = '.4dfp.img';        end
if nargin < 13 || isempty(overwrite), overwrite = false;    end
if nargin < 12, sbjroi = '';                                end
if nargin < 11, wbmask = '';                                end
if nargin < 10, variant = '';                               end
if nargin < 9,  eventstring = '';                           end
if nargin < 8,  efile = '';                                 end
if nargin < 7,  task = [];                                  end
if nargin < 6,  rgss = '';                                  end
if nargin < 5 || isempty(omit), omit = [];                  end
if nargin < 4 || isempty(TR), TR = 2.5;                     end

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

fprintf('\nRunning preproces conc script v0.9.4\n');

% ======================================================
%   ----> prepare paths and glm variables

%   ----> paths

for b = 1:nbolds

    % ---> general paths

    file(b).segmask       = strcat(subjectf, ['/images/segmentation/freesurfer/mri/aseg_bold' tail]);
    file(b).wmmask        = ['WM' tail];
    file(b).ventricleseed = ['V'  tail];
    file(b).eyeseed       = ['E'  tail];
    file(b).wbmask        = wbmask;
    file(b).fidlfile      = strcat(subjectf, ['/images/functional/events/' efile]);

    bnum = int2str(bolds(b));
    file(b).froot       = strcat(subjectf, ['/images/functional/bold' bnum]);
    file(b).boldmask    = strcat(subjectf, ['/images/segmentation/boldmasks/bold' bnum '_frame1_brain_mask' tail]);
    file(b).bold1       = strcat(subjectf, ['/images/segmentation/boldmasks/bold' bnum '_frame1' tail]);

    eroot               = strrep(efile, '.fidl', '');
    file(b).croot       = strcat(subjectf, ['/images/functional/conc_' eroot]);
    file(b).cfroot      = strcat(subjectf, ['/images/functional/concs/' eroot]);

    file(b).nfile       = strcat(subjectf, ['/images/ROI/nuisance/bold' bnum variant '_nuisance' tail]);
    file(b).nfilepng    = strcat(subjectf, ['/images/ROI/nuisance/bold' bnum variant '_nuisance.png']);

    file(b).movdata     = strcat(subjectf, ['/images/functional/movement/bold' bnum '_mov.dat']);

    file(b).nroi        = [];
    if ~isempty(nroi)
        file(b).nroi    = nroi;
    end

    % --- read and write nuisance data

    if ~isempty(variant), nvar = ['_' variant]; else nvar = ''; end
    file(b).writenuisance = strcat(subjectf, ['/images/functional/movement/nuisance_' int2str(bold) nvar '.dat']);

    if strcmp(tail, '.dtseries.nii')
        if ~isempty(variant), nvar = ['_' variant]; else nvar = ''; end
        file(b).readnuisance = strcat(subjectf, ['/images/functional/movement/nuisance_' int2str(bold) nvar '.dat']);
    else
        file(b).readnuisance = [];
    end

    % --- aseg stuff

    if strcmp(sbjroi, 'aseg')
        file(b).sbjroi = file.segmask;
    elseif strcmp(sbjroi, 'wb')
        file(b).sbjroi = file.boldmask;
    else
        file(b).sbjroi = sbjroi;
    end
end

%   ----> GLM variables

glm.rgss    = rgss;
glm.task    = task;
glm.eventstring = eventstring;


% ======================================================
%   ----> are we doing coefficients?

docoeff = false;
if strfind(doIt, 'c')
    docoeff = true;
    doIt = strrep(doIt, 'c', '');
end


% ======================================================
%   ----> run processing loop

tasklist = ['shrl'];
exts     = {'_g7','_hpss',['_res-' rgss],'_lpss'};
info     = {'Smoothing','High-pass filtering','Removing residual','Low-pass filtering'};
ext      = '';

for b = 1:nbolds
    img(b) = gmrimage();
end

for current = doIt

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
            fprintf('---> %s ', file(b).sfile)

            if exist(file(b).tfile, 'file') && ~overwrite
                fprintf('... already completed!\n');
                img(b).empty = true;
            else
                if img(b).empty
                    img(b) = img(b).mri_readimage(file(b).sfile);
                    if ~isempty(omit)
                        img(b).use(1:omit) = 0;
                    end
                end

                switch current
                    case 's'
                        img(b) = img(b).mri_Smooth3D(2, true);
                    case 'h'
                        hpsigma = ((1/TR)/0.009)/2;
                        img(b) = img(b).mri_Filter(hpsigma, 0, omit, true, ignore.hipass);
                    case 'l'
                        lpsigma = ((1/TR)/0.08)/2;
                        img(b) = img(b).mri_Filter(0, lpsigma, omit, true, ignore.lopass);
                end

                img(b).mri_saveimage(file(b).tfile);
                fprintf('... saved!\n');
            end
        end

    end

    % --- run tasks that are run on the joint bolds

    if current == 'r'
        if exist(file(b).tfile, 'file') && ~overwrite
            fprintf('... already completed!\n');
            img(b).empty = true;
        else
            for b = 1:nbolds
                if img(b).empty
                    fprintf('---> reading %s ', file(b).sfile);
                    img(b) = img(b).mri_readimage(file(b).sfile);
                    fprintf('... done!\n');
                end
            end
            fprintf('---> running regression ');
            [img coeff] = regressNuisance(img, omit, file, eventstring, glm, ignore.regress);
            fprintf('... done!\n');
            for b = 1:nbolds
                fprintf('---> saving %s ', file(b).tfile);
                img(b).mri_saveimage(file(b).tfile);
                fprintf('... done!\n');
            end

            if docoeff
                cname = [file(b).croot ext '_coeff' tail];
                fprintf('---> saving %s ', cname);
                coeff.mri_saveimage(cname);
                fprintf('... done!\n');
            end
        end
    end

    if exist(file(b).tconc, 'file') && ~overwrite
        fprintf('---> conc file already saved!\n');
    else
        fprintf('---> saving conc file ');
        gmrimage.mri_SaveConcFile(file(b).tconc, {file.tfile});
        fprintf('... done!\n');
    end

end

return


% ======================================================
%   ----> do GLM removal of nuisance regressors
%


function [img coeff] = regressNuisance(img, omit, file, eventstring, glm, ignore)

    nbolds = length(img);
    frames = zeros(1, nbolds);

    %   ----> extract per bold regressors

    for b = 1:nbolds

        img(b).data = img(b).image2D;
        frames(b)   = img(b).frames;


        % --- should we read nuisance

        if ~isempty(file(b).readnuisance)

            nuisance = dlmread(file.readnuisance);

        % --- compute generate nuisance data

        else

            %   ----> Create nuisance ROI
            fprintf(' .');

            if strfind(glm.rgss, '1b')
                [V, WB, WM] = firstBoldNuisanceROI(file(b), glm);
            else
                [V, WB, WM] = asegNuisanceROI(file(b), glm);
            end

            eROI = [];
            if ~isempty(file(b).nroi)
                [fnroi nomask] = processeROI(file(b).nroi);
                eROI      = gmrimage.mri_ReadROI(fnroi, file(b).sbjroi);
                bmimg     = gmrimage(file(b).boldmask);
                eROI.data = eROI.image2D;

                maskcodes = find(~ismember(eROI.roi.roinames, nomask));

                if ~isempty(maskcodes)
                    bmimg.data = bmimg.image2D;
                    for mc = maskcodes
                        eROI.data(bmimg.data == 0 & eROI.data == mc) = 0;
                    end
                end
            end

            %   ----> mask if necessary
            fprintf('.');

            if ~isempty(file(b).wbmask)
                wbmask = gmrimage.mri_ReadROI(file(b).wbmask, file(b).sbjroi);
                wbmask = wbmask.mri_GrowROI(2);
                WB.data = WB.image2D;
                WB.data(wbmask.image2D > 0) = 0;
            end

            %   ----> save nuisance masks
            fprintf('.');

            SaveNuisanceMasks(file(b), WB, V, WM, eROI, glm);

            %   ----> combine nuisances
            fprintf('.');

            bold(b).nuisance = [];

            trgss = glm.rgss;

            if strfind(glm.rgss, 'wm')
                bold(b).nuisance = [bold(b).nuisance img(b).mri_ExtractROI(WM)'];
                trgss = strrep(trgss, 'wm', '');
            end

            if strfind(trgss, 'wb')
                bold(b).nuisance = [bold(b).nuisance img(b).mri_ExtractROI(WB)'];
                trgss = strrep(trgss, 'wb', '');
            end

            if strfind(trgss, 'm')
                bold(b).nuisance = [bold(b).nuisance ReadMovFile(file(b).movdata, img(b).frames)];
                trgss = strrep(trgss, 'm', '');
            end

            if strfind(trgss, 'v')
                bold(b).nuisance = [bold(b).nuisance img(b).mri_ExtractROI(V)'];
                trgss = strrep(trgss, 'v', '');
            end

            if ~isempty(eROI)
               bold(b).nuisance = [bold(b).nuisance img(b).mri_ExtractROI(eROI)'];
            end

            %   ----> Save nuisance

            dlmwrite(file(b).writenuisance, nuisance, 'delimiter', '\t');

        end

        %   ----> if requested, get first derivatives
        fprintf('.');

        if strfind(trgss, 'd')
            d = [zeros(1,size(bold(b).nuisance,2));diff(bold(b).nuisance)];
            bold(b).nuisance = [bold(b).nuisance d];
        end

        %   ----> prepare baseline and trend parameters
        fprintf('.');

        na = img(b).frames-omit;
        pl = zeros(na,1);
        for n = 1:na
            pl(n) = (n-1)/(na-1);
        end
        pl = pl-0.5;
        bs = ones(na,1);
        bold(b).base = [bs, pl];
        bold(b).base = [zeros(omit, 2); bold(b).base];

    end

    %   ----> create overall task regressors
    fprintf(' .');

    if strfind(glm.rgss, 'e')
        rmodel = g_CreateTaskRegressors(file(b).fidlfile, frames, eventstring);
        runs   = rmodel.run;
    else
        for r = 1:nbolds
            runs(r).matrix = [];
        end
    end

    %   ----> join base, task and nuisance regressors
    fprintf('.');

    bregs   = size(bold(1).base, 2);
    nregs   = size(bold(1).nuisance, 2);
    tregs   = size(runs(1).matrix, 2);
    nframes = sum(frames);

    %   --> case of separate nuisance and task regressors
    fprintf('.');

    if strfind(glm.rgss, 'r1')
        sregs = bregs + nregs + tregs;          % separate regressors for each run
        regs  = nbolds * sregs;                 % all regressors
        X = zeros(nframes, regs);
        for b = 1:nbolds
            fstart = sum(frames(1:b-1)) + 1;
            fend   = sum(frames(1:b));
            rstart = sregs * (b-1) + 1;
            rend   = sregs * b;
            X(fstart:fend,rstart:rend) = [bold(b).base bold(b).nuisance runs(b).matrix];
        end

    %   --> case of joint nuisance and task regressors

    elseif strfind(glm.rgss, 'r2')
        sregs = bregs;                          % separate regressors for each run
        jregs = nregs + tregs;                  % joint regressors for all runs
        regs  = jregs + nbolds * sregs;         % all regressors
        X = zeros(nframes, regs);
        for b = 1:nbolds
            fstart = sum(frames(1:b-1)) + 1;
            fend   = sum(frames(1:b));
            rstart = jregs + sregs * (b-1) + 1;
            rend   = jregs + sregs * b;
            X(fstart:fend,1:jregs) = [bold(b).nuisance runs(b).matrix];
            X(fstart:fend,rstart:rend) = bold(b).base;
        end

    %   --> case of joint task separate nuisance regressors

    else
        sregs = bregs + nregs;                  % separate regressors for each run
        jregs = tregs;                          % joint regressors for all runs
        regs  = jregs + nbolds * sregs;         % all regressors
        X = zeros(nframes, regs);
        for b = 1:nbolds
            fstart = sum(frames(1:b-1)) + 1;
            fend   = sum(frames(1:b));
            rstart = jregs + sregs * (b-1) + 1;
            rend   = jregs + sregs * b;
            X(fstart:fend,1:jregs) = runs(b).matrix;
            X(fstart:fend,rstart:rend) = [bold(b).base bold(b).nuisance];
        end
    end

    %   ----> add the additional regressor matrix if present
    fprintf('.');

    if strfind(glm.rgss, 't')
        X = [X task];
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
%      ----> define nuisance ROI based on 1st bold frame
%


function [V, WB, WM] = firstBoldNuisanceROI(file, glm);

    % set up masks to be used

    O  = gmrimage(file.bold1, 'single', 1);
    V  = O.zeroframes(1);
    WB = O.zeroframes(1);
    WM = O.zeroframes(1);

    %   ----> White matter

    if strfind(glm.rgss, 'wm')
        WM = gmrimage(file.wmmask);
    end

    %   ----> Ventricle and Whole Brain

    if (~isempty(strfind(glm.rgss, 'wb')) | ~isempty(strfind(glm.rgss, 'v')))

        %   ----> compute WB and V masks

        V = gmrimage(file.ventricleseed);
        E = gmrimage(file.eyeseed);
        [V.data WB.data] = NROI_CreateROI(O.data, V.data, E.data);

        %   ----> shrink WB

        if strfind(glm.rgss, 'wb')
            WB = WB.mri_ShrinkROI();
            WB = WB.mri_ShrinkROI();
        end

        %   ----> shrink V

        if strfind(glm.rgss, 'v')
            V = V.mri_ShrinkROI();
        end

    end
return



% ======================================================
%      ----> define nuisance ROI based on FreeSurfer segmentation
%


function [V, WB, WM] = asegNuisanceROI(file, glm);

    fsimg = gmrimage(file.segmask);
    bmimg = gmrimage(file.boldmask);
%   WM    = gmrimage(file.wmmask);
    V     = fsimg.zeroframes(1);
    WB    = fsimg.zeroframes(1);
    WM    = fsimg.zeroframes(1);

    bmimg.data = (bmimg.data > 0) & (fsimg.data > 0);

    WM.data = (fsimg.data == 2 | fsimg.data == 41) & (bmimg.data > 0);
    WM      = WM.mri_ShrinkROI();
    WM.data = WM.image2D;

    V.data  = ismember(fsimg.data, [4 5 14 15 24 43 44 72]) & (bmimg.data > 0);
    WB.data = (bmimg.data > 0) & (WM.data ~=1) & ~V.data;

    V  		= V.mri_ShrinkROI('surface', 6);
    WB 		= WB.mri_ShrinkROI('edge', 10); %'edge', 10
    WM      = WM.mri_ShrinkROI();
    WM      = WM.mri_ShrinkROI();

return


% ======================================================
%   ----> read movement files

function x = ReadMovFile(file, nf)

    x = zeros(nf,6);

    fin = fopen(file, 'r');
    c = 0;
    while c < nf
    	s = fgetl(fin);
    	if s(1) ~= '#'
    		line = strread(s);
    		l = length(line);
    		c = c+1;
    		x(c,:) = line(l-5:l);
    	end
    end
    fclose(fin);

return



% ======================================================
%   ----> save nuisance imagesimg = img/2000 % max(max(max(img))); --- Change due to high values in embedded data!
%   --- needs to be changed

function [] = SaveNuisanceMasks(file, WB, V, WM, eROI, glm);

    O = gmrimage(file.bold1);

    nimg = WB.zeroframes(5);
    nimg.data = nimg.image2D();
    nimg.data(:,1) = O.image2D();
    nimg.data(:,2) = WB.image2D();
    nimg.data(:,3) = V.image2D();
    nimg.data(:,4) = WM.image2D();
    nimg.data(:,5) = (WB.image2D()>0)*1 + (V.image2D()>0)*2 + (WM.image2D()>0)*3;

    if ~isempty(eROI)
        nimg = [nimg eROI];
    end

    nimg.mri_saveimage(file.nfile);

    O  = RGBReshape(O ,3);
    WB = RGBReshape(WB,3);
    V  = RGBReshape(V ,3);
    WM = RGBReshape(WM,3);

    img(:,:,1) = O;
    img(:,:,2) = O;
    img(:,:,3) = O;

    img = img/2000 % max(max(max(img))); --- Change due to high values in embedded data!
    img = img * 0.7;

    if strfind(glm.rgss, 'wb')
        img(:,:,3) = img(:,:,3)+WB*0.3;
    end
    if strfind(glm.rgss, 'v')
        img(:,:,2) = img(:,:,2)+V*0.3;
    end
    if strfind(glm.rgss, 'wm')
        img(:,:,1) = img(:,:,1)+WM*0.3;
    end

    if ~isempty(eROI)
        eROI   = RGBReshape(eROI, 3);
        rcodes = unique(eROI);
        rcodes = rcodes(rcodes > 0);
        cmap   = hsv(length(rcodes));

        isize  = size(eROI);
        eROI   = reshape(eROI, prod(isize), 1);
        cROI   = repmat(eROI, 1, 3);

        for rc = 1:length(rcodes)
            tm = eROI==rcodes(rc);
            cROI(tm,1) = cmap(rc,1);
            cROI(tm,2) = cmap(rc,2);
            cROI(tm,3) = cmap(rc,3);
        end
        cROI = cROI .*3;
        cROI = reshape(cROI, [isize 3]);
        img  = img + cROI;
    end

    imwrite(img, file.nfilepng, 'png');

return



% ======================================================
%   ----> process extra ROI name
%

function [filename nomask] = processeROI(s);

    [filename, s] = strtok(s, '|');
    nomask = {};
    while ~isempty(s)
        s = strrep(s, '|', '');
        [r, s] = strtok(s, ',');
        if ~isempty(r)
            nomask(end+1) = {r};
        end
    end

return
