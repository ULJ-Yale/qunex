function [out] = NROI_ShrinkROI(in, method, crit)

%
%		Peels a layer off region to reduce its size at the borders
%       in - single volume to be shrinked
%       method - what is considered as neighbour
%           surface - sharing a surface (default) [ 7]
%           edge    - sharing at least an edge    [19]
%           corner  - sharing at least a corner   [27]
%       crit - how many of the neighbouring voxels need to be present to survive - default is all
%

if nargin < 2
    method = 'surface';
end

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

oldsize = size(in);
in = reshape(in, [48,64,48]);
out = in;

for x = 2:47
	for y = 2:63
		for z = 2:47
			if(in(x,y,z))
				focus = in(x-1:x+1,y-1:y+1,z-1:z+1) & nearest;
				if (sum(sum(sum(focus))) < crit)
					out(x,y,z) = 0;
				end					
			end
		end
	end
end

out([1 48],:,:) = 0;
out(:,[1 64],:) = 0;
out(:,:,[1 48]) = 0;
out = reshape(out, oldsize);
