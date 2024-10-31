function [roi] = general_create_roi(targetf, roi, mask, options)

% `img_prep_roi(targetf, roi, mask, options)``
%
% Creates an image file with regions of interest masks(s) based on the provided
% ROI specification. This is a wrapper function that calls nimage.img_prep_roi
% method. Please refer to the documentation of the latter for more details.
% 
%   Parameters:
%       -- targetf: (str)
%           Path to the target image file that should be created. The path can
%           include the full file name including the extension. If the extension
%           is not provided or does not match the file format, the function will 
%           create the appropriate extension. The default extension for volume
%           images is '.nii.gz' and for cifti images '.dlabel.nii'.  
%
%       -- roi: (str or nimage onject)
%           See nimage.img_prep_roi documentation for details.
%
%       --mask (str, integer, or nimage object, default ''):
%           See nimage.img_prep_roi documentation for details.
%
%       --options (str, default 'check:warning|volumes:|maps:|rois:|roinames:|standardize:no|threshold:')
%           See nimage.img_prep_roi documentation for details.
%
%   Output:
%       img
%           A nimage object with an `roi` structure array defining the ROI.
%           See nimage.img_prep_roi documentation for details.

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% ---> process input

if nargin < 2, error('\nERROR: general_create_roi: At least target file and roi specification have to be provided!\n'); end
if nargin < 3, mask = []; end
if nargin < 4, options = []; end

if isempty(targetf)
    error('\nERROR: general_create_roi: Target file has to be provided!\nI you only need the roi nimage object, please use nimage.img_prep_roi method instead!\n');
end

% ---> call nimage.img_prep_roi

roi = nimage.img_prep_roi(roi, mask, options);

% ---> detect the extension of the target file

file_info  = general_check_image_file(targetf);

% ---> save the nimage object

if strcmp(roi.imageformat, 'CIFTI-2')
    if ~file_info.is_image 
        targetf = [targetf '.dlabel.nii'];
    elseif strcmp(file_info.image_type, 'NIfTI')
        targetf = fullfile(file_info.path, [file_info.rootname '.dlabel.nii']);
    end
else
    if ~file_info.is_image 
        targetf = [targetf '.nii.gz'];
    elseif strcmp(file_info.image_type, 'CIFTI')
        targetf = fullfile(file_info.path, [file_info.rootname '.nii.gz']);
    end
end

roi.img_saveimage(targetf);
