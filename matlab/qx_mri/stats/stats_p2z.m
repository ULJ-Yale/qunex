function [img] = stats_p2z(img, out, tail)
%``stats_p2z(img, out, tail)``
%
%   Converts p to Z values considering one or two tails.
%
%   Parameters:
%       --img (nimage | str):
%           A nimage object or a path to an image file.
%
%       --out (str, default ''):
%           A path to the file to save the image to.
%
%       --tail (str, default 'two'):
%           Should one ('one') or two ('two') tails be considered.
%
%   Returns:
%       Z
%           A nimage object with results.
%
%   Notes:
%       Use the function to convert p-values to Z-values. If not filename is
%       provided, no file is saved.
%
%   Examples:
%       ::
%
%           qunex stats_p2z \
%               --img='WM_p.nii.gz' \
%               --out='WM_Z.nii.gz'
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 3 || isempty(tail), tail = 'two'; end
if nargin < 2 out = ''; end

% ======================================================
%     ---> read files

if ~isobject(img)
    img = nimage(img);
end


% ======================================================
%     ---> adjust small p values to not trigger inf

img.data(abs(img.data) < 0.0000001) = sign(img.data(abs(img.data) < 0.0000001)) .* 0.0000001;


% ======================================================
%     ---> convert

if strcmp(tail, 'two')
    img.data = norminv((1-(img.data/2)), 0, 1);    
else
    img.data = norminv((1-img.data), 0, 1);
end



% ======================================================
%     ---> save results

if ~isempty(out)
    img.img_saveimage(out);
end