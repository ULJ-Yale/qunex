function [] = cthreshold(fname, tname, csize, t)

%function [] = cthreshold(fname, tname, csize, t)
%
%   Thresholds for cluster size
%
%   input
%       fname = exisiting Z image name
%       tname = new, thresholded Z image name
%       csize = cluster size threshold
%       t     = Z magnitude threshold (allways does positive and negative)
%
%   What
%       The functions first applies Z threshold, then finds all 
%       contiguous (shared voxel side - neighboorhood 18) custers and
%       zeros all that are smaller than csize.
%
%   (c) Grega Repovs, 2016-04-06
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
