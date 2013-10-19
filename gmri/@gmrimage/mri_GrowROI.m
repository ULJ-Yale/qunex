function [img] = mri_GrowROI(img, voxels)

%function [img] = mri_GrowROI(img, voxels)
%
%	Grows regions by radius of specified voxels
%
%   voxels - radius by which to grow in voxels [1]
%
%    (c) Grega Repovs, 2010-05-10
%
%   ---- Changelog ----
%   Grega Repovs, 2013-07-24 ... Adjusted to use multiframe ROI images
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

