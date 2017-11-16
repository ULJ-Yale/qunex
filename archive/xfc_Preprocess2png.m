function [TS] = fc_Preprocess2(subjectf, bold, omit, doIt, regress, task, efile, TR)

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
% 	----> do GLM removal of nuisance regressors
%

if strfind(doIt, 'r')

	fprintf('\nRunning nuisance signal removal (%s)\n', hfile);

	%	----> create regressors

	ifh = g_ReadIFH(strrep(ofile, '.img', '.ifh'));
	nf = ifh.frames; 

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
        
    nroi = zeros(size(wbroi));
    nroi(wbroi>0) = 1;
    nroi(vroi >0) = 2;
    nroi(wmroi>0) = 3;
%    g_Save4DFP(nfile, nroi);
    SaveNuisancePNG(nfilepng, nroi, bold1);
	
end



% ======================================================
% 	----> Save nuisance PNG


function x = SaveNuisancePNG(nfilepng, nroi, bold1);

	O = g_Read4DFPn(bold1, 1);						
	T2 = RGBReshape(O,3);
	
	WB = RGBReshape(nroi==1,3);
	V = RGBReshape(nroi==2,3);
	WM = RGBReshape(nroi==3,3);
	
	img(:,:,1) = T2;
	img(:,:,2) = T2;
	img(:,:,3) = T2;

	img = img/2000 % max(max(max(img))); --- Change due to high values in embedded data!
	img = img * 0.7;
	img(:,:,3) = img(:,:,3)+WB*0.3;
	img(:,:,2) = img(:,:,2)+V*0.3;
	img(:,:,1) = img(:,:,1)+WM*0.3;

	imwrite(img, nfilepng, 'png'); 

return



