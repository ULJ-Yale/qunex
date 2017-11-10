function [TS] = fc_Preprocess4(subjectf, bold, omit, doIt, regress, task, efile, TR, eventstring)

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
%		r - regress out nuisance
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


if nargin < 8
	TR = 2.5;
end


fprintf('\nRunning preproces script v0.8.3\n');

% ======================================================
% 	----> prepare paths

ofile = strcat(subjectf, ['/images/functional/bold' int2str(bold) '.4dfp.img']);
tfile = ofile;

boldmask = strcat(subjectf, ['/images/segmentation/boldmasks/bold' int2str(bold) '_frame1_brain_mask.4dfp.img']);
bold1    = strcat(subjectf, ['/images/segmentation/boldmasks/bold' int2str(bold) '_frame1.4dfp.img']);
segmask  = strcat(subjectf, ['/images/segmentation/freesurfer/mri/aseg_333.4dfp.img']);
wmmask   = 'WM.4dfp.img';
ventricleseed = 'V.4dfp.img';
eyeseed  = 'E.4dfp.img';

nfile_1b     = strcat(subjectf, ['/images/ROI/nuisance/bold' int2str(bold) '_nuisance_1b.4dfp.img']);
nfilepng_1b  = strcat(subjectf, ['/images/ROI/nuisance/bold' int2str(bold) '_nuisance_1b.png']);

nfile_fsf    = strcat(subjectf, ['/images/ROI/nuisance/bold' int2str(bold) '_nuisance_fsf.4dfp.img']);
nfilepng_fsf = strcat(subjectf, ['/images/ROI/nuisance/bold' int2str(bold) '_nuisance_fsf.png']);

movdata  = strcat(subjectf, ['/images/functional/movement/bold' int2str(bold) '_mov.dat']);
fidlfile = strcat(subjectf, ['/images/functional/events/bold' int2str(bold) efile]);

img =[];

% ======================================================
% 	----> smooth images

if strfind(doIt, 's')
    fprintf('... Running g_Smooth3D on %s ', tfile);
    img = g_Read4DFP(tfile, 'single');
    img = g_Smooth3D(img, 2);
    fprintf(' ... saving');
    tfile = strrep(tfile, '.4dfp.img', '_g7.4dfp.img');
    g_Save4DFP(tfile, img);
    fprintf(' ... done!\n');
    img = reshape(img, 48*48*64,[]);
end

% ======================================================
% 	----> highpass filter images

if strfind(doIt, 'h')
    hpsigma = ((1/TR)/0.009)/2;
    fprintf('... Running highpass filtering with %s ', tfile);   
    if isempty(img)
        img = g_Read4DFP(tfile, 'single');
    end
    img = reshape(img, 48*48*64, []);
    img(:,omit+1:end) = g_Filter(img(:,omit+1:end), hpsigma, 0);
    fprintf(' ... saving');
    tfile = strrep(tfile, '.4dfp.img', '_hpss.4dfp.img');
    g_Save4DFP(tfile, img);
    img = reshape(img, 48*48*64,[]);
end


% ======================================================
% 	----> do GLM removal of nuisance regressors
%

if strfind(doIt, 'r')

	fprintf('\nRunning nuisance signal removal (%s)\n', tfile);

	%	----> create regressors

	ifh = g_ReadIFH(strrep(ofile, '.img', '.ifh'));
	nf = ifh.frames; 

	% 	----> read image file
		
    if isempty(img)
	    Y = g_Read4DFPn(tfile, nf);			fprintf('read');
	else
	    Y = img;
	    img = [];
	end
	
	% 	----> Extract nuisance timeseries
    
    
    if strfind(regress, '1b')    %    ----> use first bold frame
    
    	fprintf(', bold1 (');
    
        % set up masks to be used
        
        O = g_Read4DFPn(bold1, 1);
        V = zeros(size(O));
        WB = zeros(size(O));
        WM = zeros(size(O));

        %   ----> White matter
        
        if strfind(regress, 'wm')
        	fprintf('WM');
        	WM = g_Read4DFP(wmmask, 'single'); fprintf('.');
        	TS.WM = mean(Y(WM==1,:),1)';  fprintf('.');
        end
        
        %   ----> Ventricle and Whole Brain
        
        if (~isempty(strfind(regress, 'wb')) | ~isempty(strfind(regress, 'v')))
        
            % 	----> compute WB and V masks
            
            V = g_Read4DFP(ventricleseed, 'single');  fprintf('.');
        	E = g_Read4DFP(eyeseed, 'single');         fprintf('.');
        	fprintf(' ... creating ROI ');
        	[V WB] = NROI_CreateROI(O, V, E);
        	
        	if strfind(regress, 'wb')
        		fprintf('... WB ');
        		WB = NROI_ShrinkROI(WB);					   
        		WB = NROI_ShrinkROI(WB);					   
        		WB = reshape(WB, 147456, 1);				   
        		TS.WB = mean(Y(WB==1,:),1)';
            end

        	if strfind(regress, 'v')
        		fprintf('... V');
        		V = NROI_ShrinkROI(V);						   
        		V = reshape(V, 147456, 1);					   
        		TS.V = mean(Y(V==1,:),1)';		
        	end

        end
        
        %   ----> Save mask
        
        nroi = zeros(size(O));
        nroi(WB>0) = 1;
        nroi(V >0) = 2;
        nroi(WM>0) = 3;
        
        g_Save4DFP(nfile_1b, nroi);
        SaveNuisancePNG(nfilepng_1b, nroi, bold1);
        
        fprintf(')');

    else    % ... use freesurfer segmentation
        
        fsimg = g_Read4DFP(segmask, 'single');
        bmimg = g_Read4DFP(boldmask, 'single');
        wmimg = g_Read4DFP(wmmask, 'single');
    
        bmimg = (bmimg > 0) & (fsimg > 0);
    
        wmroi = (wmimg > 0) & (fsimg == 2 | fsimg == 41) & (bmimg > 0);
        vroi = ismember(fsimg, [4 5 14 15 24 43 44 72]) & (bmimg > 0);
        wbroi = (bmimg > 0) & ~wmroi & ~vroi;
    
        wmroi = reshape(wmroi, [48 64 48]);
        vroi  = reshape(vroi,  [48 64 48]);
        wbroi = reshape(wbroi, [48 64 48]);
    
        %wmroi = NROI_ShrinkROI(wmroi);
        vroi  = NROI_ShrinkROI(vroi,'surface', 6);
        wbroi = NROI_ShrinkROI(wbroi,'edge', 10);
    
        wmroi = reshape(wmroi, [], 1);
        vroi  = reshape(vroi,  [], 1);
        wbroi = reshape(wbroi, [], 1);
    
        TS.V  = mean(Y(vroi >0,:), 1)';
        TS.WM = mean(Y(wmroi>0,:), 1)';
        TS.WB = mean(Y(wbroi>0,:), 1)';
    
        nroi = zeros(size(wbroi));
        nroi(wbroi>0) = 1;
        nroi(vroi >0) = 2;
        nroi(wmroi>0) = 3;
        
        g_Save4DFP(nfile_fsf, nroi);
        SaveNuisancePNG(nfilepng_fsf, nroi, bold1);
    end

	% 	----> prepare trend parameters

	na = nf-omit;
	pl = zeros(na,1);
	for n = 1:na
		pl(n)= (n-1)/(na-1);
	end
	pl = pl-0.5;

	% 	----> get movement data

	if strfind(regress, 'm')
		md = ReadMovFile(movdata, nf);
	end

	% 	----> put together nuisances

	nuisance = [];

	if strfind(regress, 'm')
		nuisance = [nuisance md];
	end

	if strfind(regress, 'v')
		nuisance = [nuisance TS.V];
	end

	if strfind(regress, 'wm')
		nuisance = [nuisance TS.WM];
	end

	if strfind(regress, 'wb')
		nuisance = [nuisance TS.WB];
	end

	% 	----> if requested, get first derivatives

	if strfind(regress, 'd')
		d = [zeros(1,size(nuisance,2));diff(nuisance)];
		nuisance = [nuisance d];
	end
	
	% 	----> add event data from fidl file
	
	if strfind(regress, 'e')
	    events = g_CreateUnassumedResponseTaskRegressors(fidlfile, eventstring, nf);
	    nuisance = [nuisance events];
	end

	% 	----> put all regressors together

	if strfind(regress, 't')
		X = [task(omit+1:nf,:) ones(na,1) pl nuisance(omit+1:nf,:)];
	else
		X = [ones(na,1) pl nuisance(omit+1:nf,:)];
	end

	% 	----> do GLM

	fprintf(', GLM: ');

	yY = Y(:,omit+1:nf)';				fprintf('data');

	xKXs   = spm_sp('Set', X); 			fprintf(', space');
	xKXs.X = full(xKXs.X);
	
	if strfind(doIt, 'c')
		pKX   = spm_sp('x-',xKXs); 		fprintf(', inverted');
		coeff  = pKX*yY; 				fprintf(', coeff');
	end
	
	res = spm_sp('r', xKXs, yY)';		fprintf(', residuals');
	Y(:,omit+1:nf) = res;
	
	
	%    ----> Save results
	
	
    if strfind(doIt, 'c')
	    cfile = strrep(tfile, '.4dfp.img', strcat('_coeff-', regress, '.4dfp.img'));
		g_Save4DFP(cfile, coeff');
	end
	tfile = strrep(tfile, '.4dfp.img', strcat('_res-', regress, '.4dfp.img'));
	g_Save4DFP(tfile, Y);	            fprintf(', saved\n');
	img = Y;
	Y = [];
end

% ======================================================
% 	----> lowpass filter images


if strfind(doIt, 'l')

    fprintf('... Running lowpass filtering with %s ', tfile);
    lpsigma = ((1/TR)/0.08)/2;
    
    if isempty(img)
	    img = g_Read4DFP(tfile, 'single');			fprintf('read');
	end
	img = reshape(img, 48*48*64, []);
    img(:,omit+1:end) = g_Filter(img(:,omit+1:end), 0, lpsigma);
    fprintf(' ... saving');
    tfile = strrep(tfile, '.4dfp.img', strcat('_bpss', '.4dfp.img'));
    g_Save4DFP(tfile, img);
    img = [];
end

return



% ======================================================
% 	----> read movement files

function x = ReadMovFile(file, nf)

x = zeros(nf,6);

fin = fopen(file, 'r');
c = 0;
while c < nf
	s = fgetl(fin);
	if s(1) ~= '#'
		line = strread(s);
		c = c+1;
		x(c,:) = line(2:7);
	end
end
fclose(fin);

return

function x = SaveNuisancePNG(nfilepng, nroi, bold1);

O = g_Read4DFPn(bold1, 1);						
T2 = RGBReshape(O,3);

WB = RGBReshape(nroi==1,3);
V = RGBReshape(nroi==2,3);
WM = RGBReshape(nroi==3,3);

img(:,:,1) = T2;
img(:,:,2) = T2;
img(:,:,3) = T2;

img = img/max(max(max(img)));
img = img * 0.7;
img(:,:,3) = img(:,:,3)+WB*0.3;
img(:,:,2) = img(:,:,2)+V*0.3;
img(:,:,1) = img(:,:,1)+WM*0.3;

imwrite(img, nfilepng, 'png');  	fprintf(' png');

return



