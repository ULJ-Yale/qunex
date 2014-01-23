function [TS] = fc_SaveNuisancePNG(subjectf, bold)

%function [TS] = fc_SaveNuisancePNG(subjectf, bold)
%
%	Saves nuisance PNG file for the specified subject and bold
%
%   (c) Grega Repovs - 2014-01-08
%


% ======================================================
% 	----> prepare paths


nfile    = strcat(subjectf, ['/images/ROI/nuisance/bold' int2str(bold) '_nuisance.4dfp.img']);
nfilepng = strcat(subjectf, ['/images/ROI/nuisance/bold' int2str(bold) '_nuisance.png']);

nimg = gmrimage(nfile);
nimg.data = nimg.image2D;

O  = nimg.sliceframes([1 0 0 0 0]);
WB = nimg.sliceframes([0 1 0 0 0]);
V  = nimg.sliceframes([0 0 1 0 0]);
WM = nimg.sliceframes([0 0 0 1 0]);

O  = RGBReshape(O ,3);
WB = RGBReshape(WB,3);
V  = RGBReshape(V ,3);
WM = RGBReshape(WM,3);

img(:,:,1) = O;
img(:,:,2) = O;
img(:,:,3) = O;

img = img/2000 % max(max(max(img))); --- Change due to high values in embedded data!
img = img * 0.7;

img(:,:,3) = img(:,:,3)+WB*0.3;
img(:,:,2) = img(:,:,2)+V*0.3;
img(:,:,1) = img(:,:,1)+WM*0.3;

imwrite(img, nfilepng, 'png');
