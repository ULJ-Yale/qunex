function [roi] = mri_MaskROI(img, roi2)

%function [img] = mri_MaskROI(img, roi2)
%
%		Mask the ROI file based on the second ROI.
%
%       img    - the original ROI image
%       roi2   - the additiona ROI image
%
%    (c) Grega Repovs, 2015-12-09
%

if nargin < 2
    error('\nERROR: Please provide information on second ROI file to mask the original one!\n');
end

% ----> Load ROI2 if necessary

roi2 = gmrimage(roi2);

% ----> Process ROI

nroi = length(img.roi.roinames);
roi  = img.zeroframes(nroi);

for n = 1:nroi

    % if length(img.roi.roicodes{n}) == 0
    %   rmask = roi2.mri_ROIMask(img.roi.roicodes2{n});
    if length(img.roi.roicodes2{n}) == 0
        rmask = img.mri_ROIMask(img.roi.roicodes(n));
    else
        rmask = img.mri_ROIMask(img.roi.roicodes(n)) & roi2.mri_ROIMask(img.roi.roicodes2{n});
    end

    roi.data(rmask==1, n) = n;
    roi.roi.nvox(n) = sum(rmask==1);
end

% ----> Collapse to a single volume when there is no overlap between ROI

if max(sum(roi.data > 0, 2)) == 1
    roi.data   = sum(roi.data, 2);
    roi.frames = 1;
end


% ----> Encode metadata

img.roi.roifile2  = roi2.filename;

