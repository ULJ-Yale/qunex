function [mask] = img_ROIMask(img, roi)

%function [mask] = img_ROIMask(img, roi)
%
%   Checks which voxels have roi codes and returns a binary mask.
%
%   INPUT
%       img - An ROI nimage object.
%       roi - A list of ROI numeric codes or a cell array of ROI names [].
%
%   OUTPUT
%       mask - A binary mask marking voxels with specified roi codes.
%
%   USE
%   Use this method to get a binary mask of specified ROI. If no ROI codes are
%   provided or an empty matrix is passed, the mask has true values for all the
%   voxels with non-zero codes.
%
%   ---
%   Written by Grega Repovs, 2013-07-24
%
%   Changelog
%   2017-03-21 Grega Repovs
%            - With empty roi it now retuns mask of all nonzero voxels
%

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
