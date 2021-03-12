function [roi] = img_mask_roi(img, roi2)

%``function [img] = img_mask_roi(img, roi2)``
%
%	Mask the ROI file based on the second ROI.
%
%   INPUTS
%   ======
%
%   --img       The original nimage ROI image object.
%   --roi2      The additional ROI image passed either as a gmriimage or a path 
%               to the image.
%
%   OUTPUT
%   ======
%   
%   roi 
%       A new image with the original ROI masked with the ROI in the second ROI 
%       file.
%
%   USE
%   ===
%
%   The most frequent use case is to generate a subject specific ROI file in
%   which the group defined ROI provided in the original image are masked by the
%   second image that provides subjects specific information on brain
%   segmentation (e.g. aseg+aparc image).
%
%   For method to work, the ROI had to be read using the img_read_roi method,
%   called on a .names file, so that it has the information on both group level
%   and subject specific ROI codes. The method loops through all the original
%   ROI and if subject specific codes are specified for that group level ROI, it
%   masks the ROI using the specified codes for the subject specific ROI.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%
%       roi = nimage.img_read_roi('CCN.names');
%       sroi = roi.img_mask_roi('OP338.aseg+aparc.nii.gz');
%
%   Note that the above can be simplified by the use of img_read_roi itself,
%   which internaly calls img_mask_roi if the name of the second ROI image file
%   is provided::
%
%       sroi = nimage.img_read_roi('CCN.names', 'OP338.aseg+aparc.nii.gz');
%

if nargin < 2
    error('\nERROR: Please provide information on second ROI file to mask the original one!\n');
end

% ----> Load ROI2 if necessary

roi2 = nimage(roi2);

% ----> Process ROI

nroi = length(img.roi.roinames);
roi  = img.zeroframes(nroi);

for n = 1:nroi

    % if length(img.roi.roicodes{n}) == 0
    %   rmask = roi2.img_roi_mask(img.roi.roicodes2{n});
    if length(img.roi.roicodes2{n}) == 0
        rmask = img.img_roi_mask(img.roi.roicodes(n));
    else
        rmask = img.img_roi_mask(img.roi.roicodes(n)) & roi2.img_roi_mask(img.roi.roicodes2{n});
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

