function [mask] = mri_ROIMask(img, roi)

%function [mask] = mri_ROIMask(img, roi)
%
%		Checks which voxels have roi codes and returns a binary mask.
%
%       roi - a list of ROI numeric codes or a cell array of ROI names
%
%    (c) Grega Repovs, 2013-07-24
%
%

if nargin < 2
    mask = zeros(img.voxels, 1) == 1;
    return
end

if isa(img.data, 'logical')
    mask = img.data;
    return
end

multiframe = size(img.image2D,2) > 1;
if ~isa(roi, 'numeric') & ~isa(roi, 'logical')
    roi = find(ismember(img.roi.roinames, roi));
end

% ----> Do the deed

if multiframe
    img.data = img.image2D;
    mask = sum(img.data(:,roi),2) > 0;
else
    mask = ismember(img.image2D, roi);
end
