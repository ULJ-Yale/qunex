function [] = g_FDR4dfp(imgif, q, imgof, maskf, options)

%
%	g_FDR4dfp
%
%	Computes FDR thresholded image and saves the original image masked with the thresholded one.
%
%	imgif	- input file (4dfp z-score image)
%	q		- threshold
%	imgof	- optional output file name 
%	maskf	- optional mask image (4dfp image) 
%		: missing or empty -> takes Avi 333 brain mask
%		: 0 -> takes all non-zero voxels
%		: 1 -> takes all voxels 
%
%	options	- optional flag to define which z values to look at 
%		: 'all' -> both positive and negative (default)
%		: 'pos' -> ony positive
%		: 'neg' -> only negative
%	
%	Grega Repovš
%	v1.1  24.2.2008

%  ---- initializing

if (nargin < 3)
	imgof = [];
end

if isempty(imgof)
	qs = num2str(q, '%1.3f');
	imgof = strrep(imgif, '.4dfp.img', ['_FDR_q' qs '.4dfp.img']);
end

if (nargin < 4)
	maskf = [];
end

if (nargin < 5)
	options = 'all';
end

fprintf('\n\nThresholding image %s with FDR q=%.4f ...', imgif, q);


%  ---- reading input image, creating map

img = g_Read4DFP(imgif);

if isempty(maskf)
	maskf = '/data/iac12/space13/ccp/Matlab/Masks/BrainMask.4dfp.img';
end

if max(size(maskf)) == 1
	if maskf == 1
		mask = ones(size(img));
		mask = mask == 1;
	elseif maskf == 0
		mask = img ~= 0;
	end
else	
	mask = g_Read4DFP(maskf);
	mask = mask > 0;
end

mask(isnan(mask)) = 0;


%  ---- preparing p image

pimg = img(mask);
tail = 1;

switch options
	case 'all'
		pimg = abs(pimg);
		tail = 2;
	case 'pos'
		pimg(pimg < 0) = 0;
	case 'neg'
		pimg = pimg * -1;
		pimg(pimg < 0) = 0;
end
		
pimg = (1-cdf('Normal', pimg, 0, 1))*tail;

nvox = size(pimg,1);

%  ---- finding FDR threshold

vrank = [1:nvox]';
vcrit = (vrank./nvox).*q;
ps = sort(pimg);
vrank(ps>vcrit)=0;
vrank = max(vrank);
vcrit = (vrank./nvox).*q;

%  ---- making FDR mask

fdrmask = zeros(size(pimg));
fdrmask(pimg<= vcrit) = 1;

mask(mask) = fdrmask;

%  ---- saving image

img(mask == 0) = 0;

fprintf('done.\nSaving thresholded image as %s ...', imgof);

g_Save4DFP(imgof, img);

fprintf('done.\n\n');





