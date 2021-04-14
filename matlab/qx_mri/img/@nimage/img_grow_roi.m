% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [img] = img_grow_roi(img, voxels)

%``function [img] = img_grow_roi(img, voxels)``
%
%	Grows regions by radius of specified voxels.
%
%   INPUTS
%   ======
%
%   --img
%   --voxels    The radius in voxels by which to the ROI. [1]
%
%   OUTPUT
%   ======
%
%   img
%       The resulting image with grown ROI.
%
%   NOTICE
%   ======
%
%   The function works with volume representation only. If ROI are too close,
%   the one grown second can grow into the neighbouring ROI.
%
%   EXAMPLE USE
%   ===========
%
%   To grow all regions by two voxels::
%
%       grownroi = roi.img_grow_roi(2);
%

if nargin < 2
    voxels = 1;
end

pad  = ceil(voxels);
edge = pad*2+1;
nudge = edge-1;
cent = [pad+1, pad+1, pad+1];

% --- create a grow mask

mask = zeros([edge, edge, edge]);
for x = 1:edge
    for y = 1:edge
        for z = 1:edge
            mask(x, y, z) = sqrt(([x, y, z]-cent)*([x,y,z]-cent)') <= voxels;
        end
    end
end

% --- create a padded target

img.data = img.image4D;
out = zeros([img.dim(1)+2*pad, img.dim(2)+2*pad, img.dim(3)+2*pad, img.frames]);

% --- grow

for f = 1:img.frames
    for x = 1:img.dim(1)
        for y = 1:img.dim(2)
            for z = 1:img.dim(3)
                if img.data(x, y, z, 1) > 0
                    target = img.data(x, y, z, f);
                    focus = out(x:x+nudge,y:y+nudge,z:z+nudge);
                    focus(mask==1) = target;
                    out(x:x+nudge,y:y+nudge,z:z+nudge, f) = focus;
                end
            end
        end
    end
end

img.data = out(pad+1:img.dim(1)+pad, pad+1:img.dim(2)+pad, pad+1:img.dim(3)+pad, :);

