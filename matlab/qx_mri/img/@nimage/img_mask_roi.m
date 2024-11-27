function [roi] = img_mask_roi(img, roi2)

%``img_mask_roi(img, roi2)``
%
%   Mask the ROI file based on the second ROI.
%   NOTE: This method is being deprecated.  
%
%   Parameters:
%       --img (nimage object):
%           The original nimage ROI image object.
%       --roi2 (str or nimage object):
%           The additional ROI image passed either as a gmriimage or a path 
%           to the image. Of note, only the first frame of the image will be 
%           used to mask the original ROI.
%
%   Output:
%       roi 
%           A new image with the original ROI masked with the ROI in the second
%           ROI file.
%
%   Notes:
%       The most frequent use case is to generate a subject specific ROI file in
%       which the group defined ROI provided in the original image are masked by 
%       the second image that provides subjects specific information on brain
%       segmentation (e.g. aseg+aparc image).
%
%       For the method to work, the ROI had to be read using the img_prep_roi 
%       method, called on a .names file, so that it has the information on both 
%       group level and subject specific ROI codes. The method loops through all 
%       the original ROI and if subject specific codes are specified for that 
%       group level ROI, it masks the ROI using the specified codes for the 
%       subject specific ROI.
%
%   Example:
%
%   ::
%
%       roi = nimage.img_prep_roi('CCN.names');
%       sroi = roi.img_mask_roi('OP338.aseg+aparc.nii.gz');
%
%       Note that the above can be simplified by the use of img_prep_roi itself,
%       which internaly calls img_mask_roi if the name of the second ROI image 
%       file is provided::
%
%       sroi = nimage.img_prep_roi('CCN.names', 'OP338.aseg+aparc.nii.gz');
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2
    error('\nERROR: Please provide information on second ROI file to mask the original one!\n');
end

% ---> Load ROI2 if necessary

roi2 = nimage(roi2);
roi2.data = roi2.image2D;
roi2 = roi2.selectframes(1);

% ---> Process ROI

nroi = length(img.roi.roinames);
roi  = img.zeroframes(nroi);

for r = 1:nroi

    if length(img.roi(r).roicodes1) == 0
        roi.roi(r).indeces = find(ismember(roi2.data, img.roi(r).roicodes2));
    elseif length(img.roi(r).roicodes2) ~= 0
        roi.roi(r).indeces = intersect(roi.roi(r).indeces, find(ismember(roi2.data, img.roi(r).roicodes2)));
    end

    roi.data(roi.roi(r).indeces, r) = r;
    roi.roi(r).nvox = length(roi.roi(r).indeces);
end

% ---> Collapse to a single volume when there is no overlap between ROI

if max(sum(roi.data > 0, 2)) == 1
    roi.data   = sum(roi.data, 2);
    roi.frames = 1;
end


% ---> Encode metadata

img.roi.roifile2  = fullfile(roi2.filepath, roi2.filename);

