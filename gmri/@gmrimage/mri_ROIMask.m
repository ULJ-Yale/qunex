function [mask] = mri_ROIMask(obj, roi)

%function [mask] = mri_ROIMask(obj, roi)
%
%		Checks which voxels have roi codes and returns a binary mask.
%
%       roi - a list of ROI numberic codes or a cell array of ROI names
%
%    (c) Grega Repovs, 2013-07-24
%
%

if nargin < 2
    mask = zeros(obj.voxels, 1) == 1;
    return
end

% ----> Do the deed

if isa(roi, 'numeric')
    mask = sum(ismember(obj.image2D, roi), 2) > 0;
else
    mask = sum(ismember(obj.image2D, find(ismember(obj.roi.roinames, roi))), 2) > 0;
end

