function [snr, sd, slicesnr] = general_compute_snr(filename, imask, fmask, target, slice, fname)

%``general_compute_snr(filename, imask, fmask, target, slice, fname)``
%
%   Computes Signal-to-noise ratio for the given image.
%
%   Parameters:
%       --filename (str):
%           The filename of the image.
%
%       --imask (str | matrix | cell array | nimage | bool, default false):
%           Mask that defines voxels to compute snr over.
%
%       --fmask (int | vector | bool, default false):
%           Which frames to use / skip.
%
%       --target (str, default ''):
%           Path to target folder for the figure.
%
%       --slice (vector, default ''):
%           Vector of the two dimensions that define a slice.
%
%       --fname (str, default filename):
%           The name to use when saving file. The filename parameter is used if
%           fname is not given.
%
%   Returns:
%       snr
%           Mean slice snr.
%       sd
%           Std of mean whole brain volume signal over the run.
%       slicesnr
%           Array of snr values for each slice.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

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
                    if nargin < 1
                      error('ERROR: Please specify filename of the image!');
                    end
                end
            end
        end
    end
end

if isempty(fname)
    fname = filename;
end

%  ---- loading data

img = nimage(filename);
img.data = img.image2D;
[path, fname] = fileparts(fname);

%  ---- masking

if fmask
    img = img.sliceframes(fmask);
end

if imask
    mask = nimage(imask);
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

m.img_saveimage(fullfile(target, [fname '_mean']));
sd.img_saveimage(fullfile(target, [fname '_sd']));
msd.img_saveimage(fullfile(target, [fname '_msd']));
mask.img_saveimage(fullfile(target, [fname '_mask']));

slicesnr = snr;
snr = mean(snr(~isnan(snr)));

m = mean(img.image2D,1);
sd = std(m, 0, 2);






