function [snr, sd, slicesnr] = g_ComputeSNR(filename, imask, fmask, target, slice, fname)

%function [snr, sd, slicesnr] = g_ComputeSNR(filename, imask, fmask, target, slice, fname)
%	
%   Computes SNR for the given image.
%
%   Input
%       - filename	: the filename of the image
%		- imask		: mask that defines voxels to compute snr over 
%		- fmask		: which frames to use / skip
%		- target	: target folder for the figure
%       - slice		: vector of the two dimensions that define a slice
%		- fname		: the name to use when saving file
%
%	Output
%		- snr		: mean slice snr
%		- sd		: std of mean whole brain volume signal over the run
%		- slicesnr	: array of snr values for each slice
%
%	Created by Grega Repovs 2010-11-21
%	Modified by Grega Repovs 2010-11-22
%
% 	Copyright (c) 2010 Grega Repovs. All rights reserved.
%

	if nargin < 6
		fname = [];
		if nargin < 5
			slice = [];
			if nargin < 4
				target = '';
				if nargin < 3
					fmask = false;
					if nargin < 2
						imask = false;
					end
				end
			end
		end
	end		

if isempty(fname)
	fname = filename;
end

%  ---- loading data

img = gmrimage(filename);
img.data = img.image2D;
[path, fname] = fileparts(fname);

%  ---- masking

if fmask
	img = img.sliceframes(fmask);
end

if imask
	mask = gmrimage(imask);
	mask.data = mask.image4D > 0;
else
	tm = zeros(img.frames,1);
	tm(1) = 1;
	mask = img.sliceframes(tm);
	mask.data = mask.image4D > 500;
end

nslices = img.dim(3);
m = zeros(nslices, img.frames);
smask = mask;
smask.data(:,:,:) = 0;

for n = 1:nslices
	tmask = smask;
	tmask.data(:,:,n) = 1;
	tmask.data = tmask.data & mask.data;
	tmask = tmask.image2D;
	m(n,:) = mean(img.data(tmask,:),1);
end
	
sd = std(m,0,2);
m = mean(m,2);
snr = m./sd;

f = figure('visible','off');
subplot(1,2,1);
plot(snr);
subplot(1,2,2);
boxplot(snr);
print(f, '-noui', '-dpng', fullfile(target, [fname '_SNR.png']));
close(f);

img = img.maskimg(mask);
mask = mask.maskimg(mask);

m = mask;
m.data = mean(img.image2D,2);

sd = mask;
sd.data = std(img.image2D,0,2);

msd = mask;
msd.data = m.data./sd.data;

m.mri_saveimage(fullfile(target, [fname '_mean']));
sd.mri_saveimage(fullfile(target, [fname '_sd']));
msd.mri_saveimage(fullfile(target, [fname '_msd']));
mask.mri_saveimage(fullfile(target, [fname '_mask']));

slicesnr = snr;
snr = mean(snr(~isnan(snr)));

m = mean(img.image2D,1);
sd = std(m, 0, 2);






