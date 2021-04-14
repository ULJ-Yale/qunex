% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [img] = stats_p2z(img, out, tail)

%``function [img] = stats_p2z(img, out, tail)``
%
%	Converts p to Z values considering one or two tails.
%
%   INPUTS
%	======
%
%   --img  		A nimage object or a path to an image file.
%   --out  		A path to the file to save the image to [''].
%   --tail 		Should one ('one') or two ('two') tails be considered ['two'].
%
%   OUTPUT
%	======
%
%   Z
%		A nimage object with results
%
%   USE
%	===
%
%   Use the function to convert p-values to Z-values. If not filename is
%   provided, no file is saved.
%
%   EXAMPLE USE
%	===========
%
%	::
%   
%		stats_p2z('WM_p.nii.gz', 'WM_Z.nii.gz');
%

if nargin < 3 || isempty(tail), tail = 'two'; end
if nargin < 2 out = ''; end

% ======================================================
% 	----> read files

if ~isobject(img)
    img = nimage(img);
end

% ======================================================
% 	----> convert

img.data = norminv((1-(img.data/2)), 0, 1);

% ======================================================
% 	----> save results

if ~isempty(out)
    img.img_saveimage(out);
end
