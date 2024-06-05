function [xyz] = img_get_xyz(img, ijk)

%``img_get_xyz(img, ijk)``
%
%    Returns the XYZ world coordinates for given image indeces or ROI.
%
%   INPUTS
%   ======
%
%   --img
%   --ijk     A matrix of voxel indeces or a weight matrix, weight image.
%
%   OUTPUT
%   ======
%   
%   xyz
%       Depending on the ijk input:
%       
%           A matrix of voxel indeces
%               a matrix of x, y, z coordinates for each specified index    
%           An ROI image
%               A structure including matrices reporting centroids for each ROI 
%               in XYZ (world) and IJK (indeces) cordinates.
%           A weight image
%                A structure including matrices reporting centroids for each ROI 
%                as defined in the img image in XYZ (world) and IJK (indices) 
%                coordinates, and matrices reporting weighted centroids for each 
%                ROI in XYZ and IJK.
%
%   NOTES
%   =====
%
%   - The coordinates are computed based on the 1-based indeces x = 1 .. N, not
%     0-based indeces!
%   - The coordinates are computed based on the nifti header affine transform
%     matrix (srow_x/y/z)
%
%   EXAMPLE USE
%   ===========
%
%   To get centroids of all the ROI::
%
%       centroids = roi.img_get_xyz();
%
%   To get world coordinates for specific indeces::
%
%       xyz = img.img_get_xyz([34, 60, 24; 25, 52, 18]);
%
%   To get weighted ROI centroids::
%
%       wcentroids = roi.img_get_xyz(zimg);
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2, ijk = []; end

img.data = img.image4D;

% =================================================================================================
% ---                                                                               The main switch

% ---> if we have no input matrix, assume and check we have an ROI image
if isempty(ijk)
    if isroi(img.data)
        xyz.cijk = getROICentroids(img.data);
        xyz.cxyz = getXYZ(img, xyz.cijk);
    else
        error('\nERROR img_XYZ: The image is not an ROI mask. Can not compute ROI coordinates!\n');
    end

% ---> is ijk an image or a 3D matrix?

elseif isa(ijk, 'nimage') || (length(size(ijk)) == 3)

    % - extract ijk data matrix

    if isa(ijk, 'nimage')
        ijk = ijk.image4D;
    end

    % - check size matching

    if size(ijk) ~= size(img.data)
        error('\nERROR img_XYZ: The sizes of provided images do not match!\n');
    end

    % - check which one is an ROI and which one a weight image

    if isroi(img.data) && ~isroi(ijk)
        roi  = img.data;
        wimg = ijk;
    elseif ~isroi(img.data) && isroi(ijk)
        roi  = ijk;
        wimg = img.data;
    else
        error('\nERROR img_XYZ: Of the two images one has to be and ROI and the other a weight image!\n');
    end

    xyz.cijk  = getROICentroids(roi);
    xyz.wcijk = getROIWeightedCentroids(roi, wimg);
    xyz.cxyz  = getXYZ(img, xyz.cijk);
    xyz.wcxyz = getXYZ(img, xyz.wcijk);

% ---> is ijk a 2D matrix

elseif size(ijk, 2) >= 3
    xyz = getXYZ(img, ijk);

% ---> nothing matches

else
    error('\nERROR img_XYZ: Invalid input. Please check the use of the function and the provided input!\n');
end


% =================================================================================================
% ---                                                                             Support functions


% ---> computing the XYZ from IJK

function [xyz] = getXYZ(img, ijk)

    xyz = ijk;
    af  = [img.hdrnifti.srow_x'; img.hdrnifti.srow_y'; img.hdrnifti.srow_z'];
    if ~isempty(xyz)
        xyz(:, end-2:end) = (ijk(:, end-2:end) - 1) * af(1:3,1:3) + repmat(af(:,4)', size(ijk, 1), 1);
    end


% ---> getting ROI Centroids

function [xyz] = getROICentroids(roi)

    stats = regionprops(roi, 'Centroid');
    rois  = sort(unique(roi));
    rois  = rois(rois>0);
    xyz   = [];
    if ~isempty(rois)
        xyz = [rois reshape([stats(rois).Centroid], 3, [])'];
        xyz = xyz(:, [1 3 2 4]);
    end


% ---> getting Weighted ROI Centroids

function [xyz] = getROIWeightedCentroids(roi, W)

    stats = regionprops(roi, W, 'WeightedCentroid');
    rois  = sort(unique(roi));
    rois  = rois(rois>0);
    xyz   = [];
    if ~isempty(rois)
        xyz = [rois reshape([stats(rois).WeightedCentroid], 3, [])'];
        xyz = xyz(:, [1 3 2 4]);
    end


% ---> checking if we have an ROI image

function [isr] = isroi(img)

    isr = sum(sum(sum(img - round(img)))) == 0 & min(min(min(img))) >= 0 & length(unique(img)) < 1000;

