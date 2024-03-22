function [indeces, weights] = img_get_roi(img, roi)

%``img_get_roi(img, roi)``
%
%   Returns the ROI indeces and associated weights.
%
%   Parameters:
%       --img (nimage)
%           An ROI nimage object that holds integer codes in volume 1 and 
%           optionally weights in volume 2.
%       --roi (str, cell array or integer array)
%           A comma separated list or ROI indeces or ROI names or an integer
%           array of numeric codes or a cell array of ROI names [].
%
%   Output:
%       indeces 
%           An array of roi indeces, specifying members of ROI.
%       weights
%           An array of weights for the identified ROI members.
%
%   Notes:
%       Use this method to get a list of indeces that match the provided roi
%       names or codes. If the image has a second volume, that one will be used
%       to extract weights for the ROI.
%
%       If no roi is provided, then all 
%   voxels with non-zero codes.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

img.data = img.image2D;

if nargin < 2 || isempty(roi)
    mask = sum(img.data, 2) > 0
    return
end

if isa(img.data, 'logical')
    mask = img.data;
    return
end

multiframe = size(img.data, 2) > 1;
if ~isa(roi, 'numeric') & ~isa(roi, 'logical')
    roi = find(ismember(img.roi.roinames, roi));
end

% ----> Do the deed

if multiframe
    mask = sum(img.data(:,roi),2) > 0;
else
    mask = ismember(img.data, roi);
end
