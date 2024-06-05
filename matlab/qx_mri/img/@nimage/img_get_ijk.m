function [ijk] = img_get_ijk(img, xyz)

%``img_get_ijk(img, xyz)``
%
%    Returns the IJK voxel indices of a given world coordinates matrix.
%
%   INPUTS
%    ======
%
%    --img
%   --xyz     A matrix of world coordinates x, y, z
%
%   OUTPUT
%    ======
%
%   ijk
%        A matrix of voxel indeces or a weight matrix, weight image.
%
%   NOTES
%    =====
%
%   - The coordinates are computed based on the 1-based indeces x = 1 .. N, not
%     0-based indeces!
%   - The coordinates are computed based on the nifti header affine transform
%     matrix (srow_x/y/z).
%
%   EXAMPLE USE
%    ===========
%
%   To get vertex indices for specific world coordinates::
%
%       ijk = img.img_get_ijk([34, 60, 24; 25, 52, 18]);
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2, xyz = []; end

img.data = img.image4D;

% =================================================================================================
% ---                                                                               The main switch

% ---> if we have no input matrix, assume and check we have an ROI image
if size(xyz, 2) >= 3
    ijk = getIJK(img, xyz);
% ---> nothing matches
else
    error('\nERROR img_get_ijk: Invalid input. Please check the use of the function and the provided input!\n');
end


% =================================================================================================
% ---                                                                             Support functions


% ---> computing the XYZ from IJK

function [ijk] = getIJK(img, xyz)

    ijk = xyz;
    af  = [img.hdrnifti.srow_x'; img.hdrnifti.srow_y'; img.hdrnifti.srow_z'];
    if ~isempty(xyz)
        ijk(:, end-2:end) = (xyz(:, end-2:end) - repmat(af(:,4)', size(xyz, 1), 1)) * inv(af(1:3,1:3)) + 1;
    end

