function [TS] = fc_Preprocess5(subjectf, bold, omit, do, rgss, task, efile, TR, eventstring, variant, wbmask, sbjroi, overwrite)

%	Written by Grega Repovš, 2007-10-29
%
%	Regression of events - 2007-11-15
%   Adapted for new fcMRI workflow - 2009-01-19
%   Changed processing of filenames to alow arbitrary combination of steps - 2009-05-18
%
%   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
%	
%	Does the preprocesing for the conc bold runs
%	Saves images in ftarget folder
%	Saves new conc files in the ctarget folder
%	Omits "omit" number of start frames from bandpassing and GLM
%	Does the steps specified in "do":
%		s - smooth
%		h - highpass
%		r - regresses out nuisance
%		c - save coefficients in _coeff file
%		p - saves png image files of nusance ROI mask
%       l - lowpass
%
%	In regression it uses the regressors specified in "regress":
%		m - motion
%		v - ventricles
%		wm - white matter
%		wb - whole brain
%		d - first derivative
%		t - task 
%		e - events
%
%	It prepends task matrix to GLM regression 
%	It reads event data from efile fidl event file 
%   - these should be placed in the /images/functional/events/ and named boldX_efile
%
%   It takes eventstring to describe which events to model and for how many frames
%   
%   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 


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


fprintf('\nRunning preproces script 5 v0.9.0\n');

% ======================================================
% 	----> prepare paths

froot = strcat(subjectf, ['/images/functional/bold' int2str(bold)]);

file.boldmask  = strcat(subjectf, ['/images/segmentation/boldmasks/bold' int2str(bold) '_frame1_brain_mask.4dfp.img']);
file.bold1     = strcat(subjectf, ['/images/segmentation/boldmasks/bold' int2str(bold) '_frame1.4dfp.img']);
file.segmask  = strcat(subjectf, ['/images/segmentation/freesurfer/mri/aseg_333.4dfp.img']);
file.wmmask    = 'WM.4dfp.img';
file.ventricleseed = 'V.4dfp.img';
file.eyeseed   = 'E.4dfp.img';

file.nfile     = strcat(subjectf, ['/images/ROI/nuisance/bold' int2str(bold) variant '_nuisance.4dfp.img']);
file.nfilepng  = strcat(subjectf, ['/images/ROI/nuisance/bold' int2str(bold) variant '_nuisance.png']);

file.movdata  = strcat(subjectf, ['/images/functional/movement/bold' int2str(bold) '_mov.dat']);
file.fidlfile = strcat(subjectf, ['/images/functional/events/bold' int2str(bold) efile]);

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
% 	----> are we doing coefficients?

docoeff = false;
if strfind(do, 'c')
    docoeff = true;
    do = strrep(do, 'c', '');
end



% ======================================================
% 	----> run processing loop

task = ['shrl'];
exts = {'_g7','_hpss',['_res-' rgss],'_lpss'};
info = {'Smoothing','High-pass filtering','Removing residual','Low-pass filtering'};
tail = '.4dfp.img';
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
                img.mri_Smooth3D(2, true);
            case 'h'
                hpsigma = ((1/TR)/0.009)/2;
                img.mri_Filter(hpsigma, 0, omit, true);
            case 'l'
                lpsigma = ((1/TR)/0.08)/2;
                img.mri_Filter(0, lpsigma, omit, true);
            case 'r'
                [img coeff] = regressNuisance(img, omit, file, glm);
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
% 	----> do GLM removal of nuisance regressors
%


function [img coeff] = regressNuisance(img, omit, file, glm)

    img.data = img.image2D;
    
	% 	----> Create nuisance ROI
	
	if strfind(glm.rgss, '1b')
	    [V, WB, WM] = firstBoldNuisanceROI(file, glm);
	else
	    [V, WB, WM] = asegNuisanceROI(file, glm);
    end
	
	%   ----> mask if necessary
	
	if ~isempty(file.wbmask)
	    wbmask = gmrimage.mri_ReadROI(file.wbmask, file.sbjroi);
	    wbmask = wbmask.mri_GrowROI(2);
        WB.data = WB.image2D;
        WB.data(wbmask.image2D > 0) = 0;
    end
	
	%   ----> save nuisance masks
	
	SaveNuisanceMasks(file, WB, V, WM);
	
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
	
    % 	----> if requested, get first derivatives

	if strfind(glm.rgss, 'd')
		d = [zeros(1,size(nuisance,2));diff(nuisance)];
		nuisance = [nuisance d];
	end
	
	% 	----> add event data from fidl file
	
	if strfind(glm.rgss, 'e')
	    events = g_CreateUnassumedResponseTaskRegressors(file.fidlfile, file.eventstring, img.frames);
	    nuisance = [nuisance events];
	end
	
	% 	----> prepare trend parameters

	na = img.frames-omit;
	pl = zeros(na,1);
	for n = 1:na
		pl(n)= (n-1)/(na-1);
	end
	pl = pl-0.5;
    
	% 	----> put all regressors together

	if strfind(glm.rgss, 't')
		X = [task(omit+1:nf,:) ones(na,1) pl nuisance(omit+1:img.frames,:)];
	else
		X = [ones(na,1) pl nuisance(omit+1:img.frames,:)];
	end

	% 	----> do GLM
	
	Y = img.sliceframes(omit);
	
	[coeff res] = Y.mri_GLMFit(X);
	img.data(:,omit+1:img.frames) = res.image2D;

return


% ======================================================
% 	   ----> define nuisance ROI based on 1st bold frame
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
    
        % 	----> compute WB and V masks
        
        V = gmrimage(file.ventricleseed); 
    	E = gmrimage(file.eyeseed);
    	[V.data WB.data] = NROI_CreateROI(O.data, V.data, E.data);
    	
    	% 	----> shrink WB
    	
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
% 	   ----> define nuisance ROI based on FreeSurfer segmentation
%


function [V, WB, WM] = asegNuisanceROI(file, glm);
        
    fsimg = gmrimage(file.segmask);
    bmimg = gmrimage(file.boldmask);
    WM    = gmrimage(file.wmmask);
    V     = WM.zeroframes(1);
    WB    = WM.zeroframes(1);

    bmimg.data = (bmimg.data > 0) & (fsimg.data > 0);

    WM.data = (WM.data > 0) & (fsimg.data == 2 | fsimg.data == 41) & (bmimg.data > 0);
    V.data  = ismember(fsimg.data, [4 5 14 15 24 43 44 72]) & (bmimg.data > 0);
    WB.data = (bmimg.data > 0) & ~WM.data & ~V.data;

    %WM = WM.mri_ShrinkROI();
    V  = V.mri_ShrinkROI('surface', 6);
    WB = WB.mri_ShrinkROI('edge', 10);

return


% ======================================================
% 	----> read movement files

function x = ReadMovFile(file, nf)

    x = zeros(nf,6);

    fin = fopen(file, 'r');
    s = fgetl(fin);
    for n = 1:nf
    	s = fgetl(fin);
    	line = strread(s);
    	x(n,:) = line(2:7);
    end
    fclose(fin);

return

% ======================================================
% 	----> save nuisance images 
%   --- needs to be changed

function [] = SaveNuisanceMasks(file, WB, V, WM);
    
    O = gmrimage(file.bold1);						
    
    nimg = WB.zeroframes(5);
    nimg.data = nimg.image2D();
    nimg.data(:,1) = O.image2D();
    nimg.data(:,2) = WB.image2D();
    nimg.data(:,3) = V.image2D();
    nimg.data(:,4) = WM.image2D();
    nimg.data(:,5) = (WB.image2D()>0)*1 + (V.image2D()>0)*2 + (WM.image2D()>0)*3;
    
    nimg.mri_saveimage(file.nfile);
    
    O  = RGBReshape(O.data ,3);
    WB = RGBReshape(WB.data,3);
    V  = RGBReshape(V.data ,3);
    WM = RGBReshape(WM.data,3);

    img(:,:,1) = O;
    img(:,:,2) = O;
    img(:,:,3) = O;

    img = img/max(max(max(img)));
    img = img * 0.7;
    img(:,:,3) = img(:,:,3)+WB*0.3;
    img(:,:,2) = img(:,:,2)+V*0.3;
    img(:,:,1) = img(:,:,1)+WM*0.3;

    imwrite(img, file.nfilepng, 'png');

return
