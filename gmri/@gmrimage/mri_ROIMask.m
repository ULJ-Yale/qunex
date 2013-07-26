function [mask] = mri_ROIMask(img, roi)

%function [mask] = mri_ROIMask(img, roi)
%
%		Checks which voxels have roi codes and returns a binary mask.
%
%       roi - a list of ROI numberic codes or a cell array of ROI names
%
%    (c) Grega Repovs, 2013-07-24
%
%

if nargin < 2
    mask = zeros(img.voxels, 1) == 1;
    return
end

multiframe = size(img.image2D,2) > 1;
if ~isa(roi, 'numeric')
    roi = find(ismember(img.roi.roinames, roi));
end

% ----> Do the deed

if multiframe
    mask = sum(img.image2D(:,roi)) > 0
else
    mask = ismember(img.image2D, roi);
end
