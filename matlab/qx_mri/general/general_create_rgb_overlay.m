function [img] = general_create_rgb_overlay(img, roi, R, G, B, filename, slices)

%``function [img] = general_create_rgb_overlay(img, roi, R, G, B, filename, slices)``
%
%   Creates an RGB image of img with overlay in R, G and B for specified ROI
%   values. Filename is optional. If specified image is saved as a PNG file. img
%   and roi are expected to be nimage objects. If they are strings, they are
%   expected to be paths to the files to be loaded.
%
%   INPUTS
%   ======
%
%   --img
%   --roi
%   --R
%   --G
%   --B
%   --filename
%   --slices
%
%
%   OUTPUT
%   ======
%
%   img
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

savepng = true;
if nargin < 7
    slices = [];
    if nargin < 6
        savepng = false;
        if nargin < 5
            B = [];
            if nargin < 4
                G = [];
                if nargin < 3
                    error('ERROR: Not enough parameters specified!');
                end
            end
        end
    end
end

if ischar(img)
    img = nimage(img);
end
if ischar(roi)
    roi = nimage(roi);
end

if min(size(img.data) == size(roi.data)) ~= 1
    error('ERROR: The specified images are not of the same dimensions!');
end

img = img.img_slice_matrix(3, slices);
img(:,:,2) = img;
img(:,:,3) = img(:,:,1);
img = img/max(max(max(img)));
img = img * 0.7;

roi = roi.img_slice_matrix(3, slices);

img(:,:,1) = img(:,:,1) + ismember(roi, R) * 0.3;
img(:,:,2) = img(:,:,2) + ismember(roi, G) * 0.3;
img(:,:,3) = img(:,:,3) + ismember(roi, B) * 0.3;

if savepng
    imwrite(img, filename, 'png');
end
