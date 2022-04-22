function [] = general_image_conjunction(imgf, maskf, method, effect, q, data, psign)

%``function [] = general_image_conjunction(imgf, maskf, method, effect, q, data, psign)``
%
%   Reads image file, computes conjunction using general_conjunction and
%   saves results. Accepts image of significance estimates and computes
%   conjunction for 1 <= u <= n. Results at each step are thresholded using
%   FDR q.
%
%   Based on Heller et al. (2017). NeuroImage 37, 1178–1185.
%   (https://doi.org/10.1016/j.neuroimage.2007.05.051).
%
%   Parameters:
%       --imgf (str):
%           Input file, a z-score image file of concatenated individual files.
%       --maskf (str, default 'nonzero'):
%           Optional mask image
%
%           - missing or empty ... takes all non-zero voxels
%           - 'nonzero'        ... takes all non-zero voxels
%           - 'all'            ... takes all voxels.
%
%       --method (str, default 'Fisher'):
%           Method of calculating conjunction p:
%
%           - 'Simes'    ... pooling dependent p-values (eq. 5)
%           - 'Stouffer' ... pooling independent p-values (eq. 6)
%           - 'Fisher'   ... pooling independent p-values (eq. 7).
%
%       --effects (str, default 'all'):
%           The effect of interest:
%
%           - 'pos'    ... positive effect only (one tailed test)
%           - 'neg'    ... negative effect only (one tailed test)
%           - 'all'    ... both effects (two tailed test).
%
%       --q (float, default 0.05)
%           The FDR q value at which to threshold.
%       --data (str, default 'z'):
%           The values in image
%
%           - 'z' ... z-values
%           - 'p' ... p-values.
%
%       --psign (str | matrix | cell array | nimage, default []):
%           In case of two-tailed test for p-values input, an image that
%           includes signs for the effect direction if p-values are not signed.
%           It can be signed z-scores image.
%
%   Notes:
%       For the rest of arguments see general_conjunction.m
%
%       Resulting files:
%           '_Conj_p'
%               Conjunction results, p-values for u = 1 to u = n.
%
%           '_Conj_z'
%               Conjunction results, z-scores for u = 1 to u = n.
%
%           '_Conj_FDR_p_<q>'
%               p-values thresholded with FDR.
%
%           '_Conj_FDR_z_<q>'
%               Z-scores thresholded with FDR.
%
%           '_Conj_FDR_c_<q>'
%               Image of frequency of passing threshold.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% parsing arguments

if nargin < 7, psign = []; end
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

imgpf  = [fraw '_Conj_p'];
imgzf  = [fraw '_Conj_z'];
imgptf = [fraw '_Conj_FDR_p_' qs];
imgztf = [fraw '_Conj_FDR_z_' qs];
imgcf  = [fraw '_Conj_FDR_c_' qs];

fprintf('\n\nComputing conjunction with file %s, thresholding with FDR q=%.4f\n', imgf, q);

%  ---- reading image, computing conjunction

fprintf('... reading image ');
img = nimage(imgf);
nim = img.frames;
fprintf(' volumes: %d ', nim);
fprintf('... done\n');

%  ---- Creating image mask and masking image

if ~strcmp(maskf, 'all')
    fprintf('... masking image\n');

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

if ~isempty(psign)
    psign = nimage(psign);
    psign = psign.data(mask);
end

%  ---- Coing conjunction

fprintf('... starting conjunction analysis\n');
[mp, mpt, mc, mz, mzt] = general_conjunction(img.data(mask, :), method, effect, q, data, psign);
fprintf('... done\n');

%  ---- saving results

fprintf('... saving results ');

out = img.zeroframes(nim);
out.data(mask,:) = mp;
out.img_saveimage(imgpf);       fprintf('.');

out = img.zeroframes(nim);
out.data(mask,:) = mpt;
out.img_saveimage(imgptf);       fprintf('.');

out = img.zeroframes(nim);
out.data(mask,:) = mz;
out.img_saveimage(imgzf);       fprintf('.');

out = img.zeroframes(nim);
out.data(mask,:) = mzt;
out.img_saveimage(imgztf);       fprintf('.');

out = img.zeroframes(1);
out.data(mask) = mc;
out.img_saveimage(imgcf);       fprintf('.');

fprintf(' done.\n\n');


