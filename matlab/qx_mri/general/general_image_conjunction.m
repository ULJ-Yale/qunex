% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [] = general_image_conjunction(imgf, maskf, method, effect, q, data)

%``function [] = general_image_conjunction(imgf, maskf, method, effect, q, data)``
%
%	INPUTS
%	======
%
%	Reads image file, computes conjunction using g_conjunction and saves results.
%
%	--imgf 		input file, a z-score image file of concatenated individual files
%	--maskf		optional mask image
%
%				- missing or empty -> takes all non-zero voxels
%				- nonzero -> takes all non-zero voxels
%				- all -> takes all voxels
%
%	For the rest of arguments see g_conjunction.m
%
%	RESULTS
%	=======
%
%	Saves
%
%	'_Conj_p'
%		conjunction results, zscores for u = 1 to u = n
%
%	'_Conj_FDR'
%		above thresholded with FDR
%
%	'_Conj_c'
%		image of frequency of passing threshold
%

% parsing arguments

if nargin < 6, data = []; end
if nargin < 5, q = 0.05; end
if nargin < 4, effect = []; end
if nargin < 3, method = []; end
if nargin < 2 || isempty(maskf), maskf = 'nonzero'; end

%  ---- initializing

qs = num2str(q, '%1.3f');
fraw = strrep(imgf, '.4dfp.img', '');
fraw = strrep(fraw, '.gz', '');
fraw = strrep(fraw, '.nii', '');
fraw = strrep(fraw, '.conc', '');
fraw = strrep(fraw, '.dtseries', '');
fraw = strrep(fraw, '.dscalar', '');
imgpf = [fraw '_Conj_p'];
imgtf = [fraw '_Conj_FDR' qs ];
imgcf = [fraw '_Conj_c'];

fprintf('\n\nComputing conjunction with file %s, thresholding with FDR q=%.4f\n', imgf, q);

%  ---- reading image, computing conjunction

fprintf('... reading image ');
img = nimage(imgf);
nim = img.frames;
fprintf(' volumes: %d ', nim);
fprintf('... done\n');


%  ---- Creating image mask and masking image

if ~strcmp(maskf, 'all')
	fprintf('... masking image ');

	if strcmp(maskf, 'nonzero')
		img.data = img.image2D;
		mask = sum(img.data, 2) ~= 0;
	else
		mask = nimage(maskf);
		mask = mask.image2D > 0;
	end

else
	mask = ones(img.voxels, 1) == 1;
end

%  ---- Coing conjunction

fprintf('... starting conjunction analysis\n');
[mzp, mzt, mzc] = general_conjunction(img.data(mask, :), method, effect, q, data);
fprintf('... done\n');

%  ---- saving results

fprintf('... saving results ');

out = img.zeroframes(nim);
out.data(mask,:) = mzp;
out.img_saveimage(imgpf);       fprintf('.');

out = img.zeroframes(nim);
out.data(mask,:) = mzt;
out.img_saveimage(imgtf);       fprintf('.');

out = img.zeroframes(1);
out.data(mask) = mzc;
out.img_saveimage(imgcf);       fprintf('.');

fprintf(' done.\n\n');


