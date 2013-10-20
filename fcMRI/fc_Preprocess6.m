function [] = fc_Preprocess6(subjectf, bold, omit, do, rgss, task, efile, TR, eventstring, variant, wbmask, sbjroi, overwrite, tail, nroi, ignores)

%function [] = fc_Preprocess6(subjectf, bold, omit, do, rgss, task, efile, TR, eventstring, variant, wbmask, sbjroi, overwrite, tail, nroi, ignores)
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
%           p - saves png image files of nusance ROI mask
%           l - lowpass temporal filter
%       rgss        - what to regress in the regression step
%           m  - motion
%           v  - ventricles
%           wm - white matter
%           wb - whole brain
%           d  - first derivative
%           t  - task
%           e  - events
%           1b - use the first bold run to define whole brain and ventricle mask
%       task        - matrix of custom regressors to be entered in GLM
%       efile       - event (fild) file to be used for removing task structure [none]
%       TR          - TR of the data [2.5]
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
%   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if nargin < 15
    ignores = [];
    if nargin < 15
        nroi = [];
        if nargin < 14
            tail = '.4dfp.img';
            if nargin < 13
                overwrite = false;
                if nargin < 12
                    sbjroi = '';
                    if nargin < 11
                        wbmask = '';
                        if nargin < 10
                            variant = '';
                            if nargin < 9
                                eventstring = '';
                                if nargin < 8
                                    TR = 2.5;
                                end
                            end
                        end
                    end
                end
            end
        end
    end
end

fprintf('\nRunning preproces script 6 v0.9.3\n');

ignore.hipass  = 'keep';
ignore.regress = 'keep';
ignore.lopass  = 'keep';

ignores = regexp(ignores, ',|;|:|\|', 'split');
if length(ignores)>=2
    ignores = reshape(ignores, 2, [])';
    for p = size(ignores, 1)
        val = str2num(ignores{p,2});
        if isempty(val)
            setfield(ignore, ignores{p,1}, ignores{p,2});
        else
            setfield(ignore, ignores{p,1}, val);
        end
    end
end


% ======================================================
%   ----> prepare paths

froot = strcat(subjectf, ['/images/functional/bold' int2str(bold)]);

file.boldmask  = strcat(subjectf, ['/images/segmentation/boldmasks/bold' int2str(bold) '_frame1_brain_mask' tail]);
file.bold1     = strcat(subjectf, ['/images/segmentation/boldmasks/bold' int2str(bold) '_frame1' tail]);
file.segmask   = strcat(subjectf, ['/images/segmentation/freesurfer/mri/aseg_bold' tail]);
file.wmmask    = ['WM' tail];
file.ventricleseed = ['V' tail];
file.eyeseed   = ['E' tail];

file.nfile     = strcat(subjectf, ['/images/ROI/nuisance/bold' int2str(bold) variant '_nuisance' tail]);
file.nfilepng  = strcat(subjectf, ['/images/ROI/nuisance/bold' int2str(bold) variant '_nuisance.png']);

file.movdata  = strcat(subjectf, ['/images/functional/movement/bold' int2str(bold) '_mov.dat']);
file.fidlfile = strcat(subjectf, ['/images/functional/events/bold' int2str(bold) efile]);

file.nroi     = [];
if ~isempty(nroi)
    file.nroi = nroi;
end

file.wbmask = wbmask;
if strcmp(sbjroi, 'aseg')
    file.sbjroi = file.segmask;
elseif strcmp(sbjroi, 'wb')
    file.sbjroi = file.boldmask;
else
    file.sbjroi = sbjroi;
end

glm.rgss = rgss;
glm.task    = task;
glm.efile   = efile;
glm.eventstring = eventstring;



% ======================================================
%   ----> are we doing coefficients?

docoeff = false;
if strfind(do, 'c')
    docoeff = true;
    do = strrep(do, 'c', '');
end



% ======================================================
%   ----> run processing loop

task = ['shrl'];
exts = {'_g7','_hpss',['_res-' rgss],'_lpss'};
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

    fprintf('%s %s ', info{c}, sfile);

    % --- run it

    if exist(tfile, 'file') & ~overwrite
        fprintf(' ... already completed!\n');
    else
        if img.empty
            img = img.mri_readimage(sfile);
        end

        switch current
            case 's'
                img = img.mri_Smooth3D(2, true);
            case 'h'
                hpsigma = ((1/TR)/0.009)/2;
                img = img.mri_Filter(hpsigma, 0, omit, true, ignore.hipass);
            case 'l'
                lpsigma = ((1/TR)/0.08)/2;
                img = img.mri_Filter(0, lpsigma, omit, true, ignore.lopass);
            case 'r'
                [img coeff] = regressNuisance(img, omit, file, glm, ignore.regress);
                if docoeff
                    coeff.mri_saveimage([froot ext '_coeff' tail]);
                end
        end

        img.mri_saveimage(tfile);
        fprintf(' ... saved!\n');
    end

end

return


% ======================================================
%   ----> do GLM removal of nuisance regressors
%


function [img coeff] = regressNuisance(img, omit, file, glm, ignore)


    img.data = img.image2D;

    %   ----> Create nuisance ROI

    if strfind(glm.rgss, '1b')
        [V, WB, WM] = firstBoldNuisanceROI(file, glm);
    else
        [V, WB, WM] = asegNuisanceROI(file, glm);
    end

    %   ----> add extra ROI based nuisance

    eROI = [];
    if ~isempty(file.nroi)
        [fnroi nomask] = processeROI(file.nroi);
        eROI      = gmrimage.mri_ReadROI(fnroi, file.sbjroi);
        bmimg     = gmrimage(file.boldmask);
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

    if ~isempty(file.wbmask)
        wbmask = gmrimage.mri_ReadROI(file.wbmask, file.sbjroi);
        wbmask = wbmask.mri_GrowROI(2);
        WB.data = WB.image2D;
        WB.data(wbmask.image2D > 0) = 0;
    end

    %   ----> save nuisance masks

    SaveNuisanceMasks(file, WB, V, WM, eROI, glm);

    %   ----> combine nuisances

    nuisance = [];

    if strfind(glm.rgss, 'm')
        nuisance = [nuisance ReadMovFile(file.movdata, img.frames)];
    end

    if strfind(glm.rgss, 'v')
        nuisance = [nuisance img.mri_ExtractROI(V)'];
    end

    if strfind(glm.rgss, 'wm')
        nuisance = [nuisance img.mri_ExtractROI(WM)'];
    end

    if strfind(glm.rgss, 'wb')
        nuisance = [nuisance img.mri_ExtractROI(WB)'];
    end

    if ~isempty(eROI)
       nuisance = [nuisance img.mri_ExtractROI(eROI)'];
    end

    %   ----> if requested, get first derivatives

    if strfind(glm.rgss, 'd')
        d = [zeros(1,size(nuisance,2));diff(nuisance)];
        nuisance = [nuisance d];
    end

    %   ----> add event data from fidl file

    if strfind(glm.rgss, 'e')
        events = g_CreateUnassumedResponseTaskRegressors(file.fidlfile, file.eventstring, img.frames);
        nuisance = [nuisance events];
    end

    %   ----> prepare trend parameters

    na = img.frames-omit;
    pl = zeros(na,1);
    for n = 1:na
        pl(n)= (n-1)/(na-1);
    end
    pl = pl-0.5;

    %   ----> put all regressors together

    if strfind(glm.rgss, 't')
        X = [task(omit+1:nf,:) ones(na,1) pl nuisance(omit+1:img.frames,:)];
    else
        X = [ones(na,1) pl nuisance(omit+1:img.frames,:)];
    end

    %   ----> do GLM

    if strcmp(ignore, 'ignore')
        mask = img.use;
    else
        mask = true(1, img.frames);
    end
    mask(1:omit) = false;

    Y = img.sliceframes(mask);

    [coeff res] = Y.mri_GLMFit(X);
    img.data(:,mask) = res.image2D;


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

    V       = V.mri_ShrinkROI('surface', 6);
    WB      = WB.mri_ShrinkROI('edge', 10); %'edge', 10
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
%   ----> save nuisance images
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

    img = img/max(max(max(img)));
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

