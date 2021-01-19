function [out] = img_shrink_roi(img, method, crit)

%``function [out] = img_shrink_roi(img, method, crit)``
%
%	Peels a layer off all regions to reduce their size.
%
%   INPUTS
%   ======
%
%   --in        A nimage object with ROI volume data.
%   --method    What is considered as neighbour ['surface']
%
%               - surface ... sharing a surface (default) (N=7)
%               - edge    ... sharing at least an edge    (N=19)
%               - corner  ... sharing at least a corner   (N=27)
%
%   --crit      how many of the neighbouring voxels need to be present to 
%               survive - default is all
%
%   OUTPUT
%   ======
%
%   out
%       A nimage object with shrunk regions
%
%   USE
%   ===
%
%   The method inspects all the voxels in the image for presence of neighbours.
%   If a voxel has all the specified neighbors (or a crit number of them), then
%   it is left as it is. If it does not have the required number of neighbours,
%   then it is considered a part of the border layer and it is peeled off, set
%   to zero. Neighbors can be specified as all those voxels that share a
%   surface, those that share at least an edge or those that share at least a
%   corner.
%
%   EXAMPLE USE
%   ===========
%
%   To cunt as neighbors voxels that share at least an edge and take out those
%   that have less than 17 neighbors use::
%
%       shrunkimg = img.img_shrink_roi('edge', 17);
%

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
%   2010-05-10 Grega Repovs
%              Initial version.
%   2013-07-24 Grega Repovs
%              Adjusted for multivolume ROI files
%   2017-03-11 Grega Repovs
%              Updated documentation
%

if nargin < 2,  method = 'surface';  end

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

for f = 1:img.frames
    for x = 2:img.dim(1)-1
    	for y = 2:img.dim(2)-1
    		for z = 2:img.dim(3)-1
    			if(img.data(x,y,z,f))
    				focus = img.data(x-1:x+1,y-1:y+1,z-1:z+1,f) & nearest;
    				if (sum(sum(sum(focus))) < crit)
    					out.data(x,y,z,f) = 0;
    				end
    			end
    		end
    	end
    end
    out.data([1 out.dim(1)],:,:,f) = 0;
    out.data(:,[1 out.dim(2)],:,f) = 0;
    out.data(:,:,[1 out.dim(3)],f) = 0;
end


