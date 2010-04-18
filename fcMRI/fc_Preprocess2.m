function [TS] = fc_Preprocess2(subjectf, bold, omit, do, regress, task, efile, TR)

%	Written by Grega Repovš, 29.10.2007
%
%	Regression of events - 15.11.07
%   Adapted for new fcMRI workflow - 19.1.2009
%
%
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
%

if nargin < 8
	TR = 2.5;
end


fprintf('\nRunning preproces script v0.8.3\n');

% ======================================================
% 	----> prepare paths


ofile = strcat(subjectf, ['/images/functional/bold' int2str(bold) '.4dfp.img']);
sfile = strrep(ofile, '.4dfp.img', '_g7.4dfp.img');
hfile = strrep(sfile, '.4dfp.img', '_hpss.4dfp.img');
rfile = strrep(hfile, '.4dfp.img', strcat('_res-', regress, '.4dfp.img'));
cfile = strrep(hfile, '.4dfp.img', strcat('_coeff-', regress, '.4dfp.img'));
lfile = strrep(rfile, '.4dfp.img', strcat('_bpss', '.4dfp.img'));

boldmask = strcat(subjectf, ['/images/segmentation/boldmasks/bold' int2str(bold) '_frame1_brain_mask.4dfp.img']);
bold1 = strcat(subjectf, ['/images/segmentation/boldmasks/bold' int2str(bold) '_frame1.4dfp.img']);
segmask = strcat(subjectf, ['/images/segmentation/freesurfer/mri/aseg_333.4dfp.img']);
wmmask = '/data/ccpmac1/drobo1/fcConte2/baseimages/WM.4dfp.img';

nfile = strcat(subjectf, ['/images/ROI/nuisance/bold' int2str(bold) '_nuisance.4dfp.img']);
nfilepng = strcat(subjectf, ['/images/ROI/nuisance/bold' int2str(bold) '_nuisance.png']);
movdata = strcat(subjectf, ['/images/functional/movement/bold' int2str(bold) '_mov.dat']);

% ======================================================
% 	----> smooth images

if strfind(do, 's')
    fprintf('... Running g_Smooth3D on %s ', ofile);
    img = g_Read4DFP(ofile, 'single');
    img = g_Smooth3D(img, 2);
    fprintf(' ... saving');
    g_Save4DFP(sfile, img);
    fprintf(' ... done!\n');
    img = reshape(img, 48*48*64,[]);
end

% ======================================================
% 	----> highpass filter images

if strfind(do, 'h')
    hpsigma = ((1/TR)/0.009)/2;
    fprintf('... Running highpass filtering with %s ', sfile);   
    if ~strfind(do, 's') 
        img = g_Read4DFP(sfile, 'single');
    end
    img = reshape(img, 48*48*64, []);
    img = g_Filter(img, hpsigma, 0);
    fprintf(' ... saving');
    g_Save4DFP(hfile, img);
    img = reshape(img, 48*48*64,[]);
end


% ======================================================
% 	----> do GLM removal of nuisance regressors
%

if strfind(do, 'r')

	fprintf('\nRunning nuisance signal removal (%s)\n', hfile);

	%	----> create regressors

	ifh = g_ReadIFH(strrep(ofile, '.img', '.ifh'));
	nf = ifh.frames; 

	% 	----> read image file

    if ~strfind(do, 'h') 
        img = [];
	    Y = g_Read4DFPn(hfile, nf);			fprintf('read');
	else
	    Y = img;
	    img = [];
	end

	% 	----> Extract nuisance timeseries
    
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
    g_Save4DFP(nfile, nroi);
    SaveNuisancePNG(nfilepng, nroi, bold1);

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
	
	if strfind(do, 'c')
		pKX   = spm_sp('x-',xKXs); 		fprintf(', inverted');
		coeff  = pKX*yY; 				fprintf(', coeff');
	end
	
	res = spm_sp('r', xKXs, yY)';		fprintf(', residuals');
	Y(:,omit+1:nf) = res;
	
	if strfind(do, 'c')
		g_Save4DFP(cfile, coeff');
	end
	g_Save4DFP(rfile, Y);	            fprintf(', saved\n');
	Y = reshape(Y, 48*48*64,[]);
	
end

% ======================================================
% 	----> lowpass filter images


if strfind(do, 'l')

    fprintf('... Running lowpass filtering with %s ', rfile);
    lpsigma = ((1/TR)/0.08)/2;
    
    if ~strfind(do, 'r') 
	    img = g_Read4DFP(rfile, 'single');			fprintf('read');
	else
	    img = Y;
	end
    img = reshape(img, 48*48*64, []);
    img = g_Filter(img, 0, lpsigma);
    fprintf(' ... saving');
    g_Save4DFP(lfile, img);
    img = [];
end

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

function x = SaveNuisancePNG(nfilepng, nroi, bold1);

if ftarget 

	O = g_Read4DFPn(bold1, 1);						
	T2 = RGBReshape(O,3);
	
	WB = RGBReshape(nroi==1,3);
	V = RGBReshape(nroi==2,3);
	WM = RGBReshape(nroi==3,3);
    WB = RGBReshape(TS.WB,3);
	
	img(:,:,1) = T2;
	img(:,:,2) = T2;
	img(:,:,3) = T2;

	img = img/max(max(max(img)));
	img = img * 0.7;
	img(:,:,3) = img(:,:,3)+TS.WB*0.3;
	img(:,:,2) = img(:,:,2)+TS.V*0.3;
	img(:,:,1) = img(:,:,1)+TS.WM*0.3;

	imwrite(img, nfilepng, 'png');  	fprintf(' png');
end

return



