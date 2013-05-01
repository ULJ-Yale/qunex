function [out] = mri_ShrinkROI(img, method, crit)

%function [out] = mri_ShrinkROI(img, method, crit)
%
%		Peels a layer off region to reduce its size at the borders
%       in - single volume to be shrinked
%       method - what is considered as neighbour
%           surface - sharing a surface (default) [ 7]
%           edge    - sharing at least an edge    [19]
%           corner  - sharing at least a corner   [27]
%       crit - how many of the neighbouring voxels need to be present to survive - default is all
%
%    (c) Grega Repovs, 2010-05-10

if nargin < 2
    method = 'surface';
end

img.data = img.image4D;
out = img;

if strcmp(method, 'surface')
    nearest = cat(3,[0 0 0; 0 1 0; 0 0 0], [0 1 0; 1 1 1; 0 1 0], [0 0 0; 0 1 0; 0 0 0]);
elseif strcmp(method, 'edge')
    nearest = cat(3,[0 1 0; 1 1 1; 0 1 0], [1 1 1; 1 1 1; 1 1 1], [0 1 0; 1 1 1; 0 1 0]);
elseif strcmp(method, 'corner')
    nearest = ones(3, 3, 3);
else
    error ('ERROR: %s is not a valid method for defining neighbours to a voxel!\n       Valid options are: surface - sharing a surface (default) [ 7]\n                          edge    - sharing at least an edge    [19]\n                          corner  - sharing at least a corner   [27]\n\n', method);
end

if nargin < 3
    crit = sum(sum(sum(nearest)));
end

for x = 2:img.dim(1)-1
	for y = 2:img.dim(2)-1
		for z = 2:img.dim(3)-1
			if(img.data(x,y,z,1))
				focus = img.data(x-1:x+1,y-1:y+1,z-1:z+1,1) & nearest;
				if (sum(sum(sum(focus))) < crit)
					out.data(x,y,z,1) = 0;
				end					
			end
		end
	end
end

out.data([1 out.dim(1)],:,:,1) = 0;
out.data(:,[1 out.dim(2)],:,1) = 0;
out.data(:,:,[1 out.dim(3)],1) = 0;
