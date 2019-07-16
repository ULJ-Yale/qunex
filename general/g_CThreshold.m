function [] = g_CThreshold(fname, tname, csize, t)

%function [] = g_CThreshold(fname, tname, csize, t)
%
%   Thresholding using cluster size for volume images.
%
%   INPUT
%       fname ... A path to a Z image.
%       tname ... The name for the new, thresholded image.
%       csize ... Minimal cluster size threshold.
%       t     ... Z magnitude threshold (allways does positive and negative). [3]
%
%   USE
%   The functions first applies the specified Z threshold zeroing all voxels
%   between -t and +t. It then identifies all contiguous clusters of voxels
%   with non-zero values, voxels that share at least an edge (neighboorhood 18).
%   Next, it identifies all clusters smaller than csize and zeros them so that
%   only voxels with Z magnitude more than t, that are part of clusters of at
%   least csize voxels remain.
%
%   EXAMPLE USE
%
%   >>> g_CThreshold('encoding_Z.nii.gz', 'encoding_Z_3_72.nii.gz', 72, 3);
%
%   ---
%   Written by Grega Repovs, 2016-04-06
%
%   Changelog
%   2017-03-12 Grega Repovs
%            - Updated documentation.
%


if nargin < 4 || isempty(t), t = 3; end
if isempty(tname), tname = fname; end


img = gmrimage(fname);
img.data(abs(img.data) < t) = 0;


mp = img;
mp.data = mp.data > 0.0001;

mn = img;
mn.data = mn.data < 0.0001;

mp.data = mp.image4D;
cp = bwconncomp(mp.data, 18);    % vs 26
img = zerosmaller(img, cp, csize);

mn.data = mn.image4D;
cn = bwconncomp(mn.data, 18);    % vs 26
img = zerosmaller(img, cn, csize);

img.mri_saveimage(tname);




function [img] = zerosmaller(img, cc, csize)

    ncomp = length(cc.PixelIdxList);
    for n = 1:ncomp
        if length(cc.PixelIdxList{n}) < csize
            img.data(cc.PixelIdxList{n}) = 0;
        end
    end
