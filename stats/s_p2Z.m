function [img] = s_p2Z(img, out, tail)

%function [img] = s_p2Z(img, out, tail)
%
%	Converts p to Z values considering one or two tails.
%
%   INPUTS
%       img  ... A gmrimage object or a path to an image file.
%       out  ... A path to the file to save the image to [''].
%       tail ... Should one ('one') or two ('two') tails be considered ['two'].
%
%   OUTPUTS
%       Z    ... A gmrimage object with results
%
%   USE
%   Use the function to convert p-values to Z-values. If not filename is
%   provided, no file is saved.
%
%   EXAMPLE USE
%   s_p2Z('WM_p.nii.gz', 'WM_Z.nii.gz');
%
%   ---
%   Written by Grega Repovs
%
%   Changelog
%   2017-03-19 Grega Repovs
%            - Updated to use gmrimage objects
%            - Updated documentation


if nargin < 3 || isempty(tail), tail = 'two'; end
if nargin < 2 out = ''; end

% ======================================================
% 	----> read files

if ~isobject(img)
    img = gmrimage(img);
end

% ======================================================
% 	----> convert

img.data = icdf('Normal', (1-(img.data/2)), 0, 1);

% ======================================================
% 	----> save results

if ~isempty(out)
    img.mri_saveimage(out);
end
