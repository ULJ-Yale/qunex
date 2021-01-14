function [panel] = img_SliceMatrix(img, sdim, slices)

%``function [panel] = img_SliceMatrix(img, sdim, slices)``
%
%	Takes the first volume and generates a panel / matrix of slices in selected
%	dimension.
%
%	INPUTS
%	======
%
%	--img    	A nimage object.
%	--sdim   	The dimension across which to make the slices. What slices are 
%				generated (axial, saggital or coronal) depends on the geometry 
%				of the image. [3]
%	--slices 	Which slices to include. If empty, all the slices will be
%				included. []
%
%	OUTPUT
%	======
%
%	panel
%		A 2D matrix consisting of optimal collage of slices.
%
%	EXAMPLE USE
%	===========
%
%	::
%	
%		panel = img.img_SliceMatrix(2);
%

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
%	2010-04-18 Grega Repovs - Entry into repository (as RGBReshape)
%	2017-03-03 Grega Repovs - Moved to nimage method, renamed, adjusted
%                             and updated documentation

if nargin < 3,	slices = []; end
if nargin < 2   sdim   = 3;  end

mask = zeros(1, img.frames);
mask(1) = 1;
mask = mask == 1;

img  = img.sliceframes(mask);
data = squeeze(img.image4D);
dim  = size(data);
x    = dim(1);
y    = dim(2);
z    = dim(3);

if isempty(slices)
	slices = [1:dim(sdim)];
end
slices = slices(slices > 0);
slices = slices(slices <= dim(sdim));

nslices = length(slices);
side = ceil(sqrt(nslices));

switch sdim
	 case 1
        panel  = zeros(side*y, side*z);
		c = 1;
		for j = 1:side
			for i = 1:side
			    if c <= nslices
				    t = reshape(data(slices(c),:,:), y, z);
				    panel((i-1)*y+1:(i)*y,(j-1)*z+1:(j)*z) = t;
				end
				c = c+1;
			end
		end
		panel = imrotate(panel,90);

	 case 2
        panel  = zeros(side*x, side*z);
		c = 1;
		for j = 1:side
			for i = 1:side
			    if c <= nslices
				    t = reshape(data(:,slices(c),:), x, z);
				    panel((i-1)*x+1:(i)*x,(j-1)*z+1:(j)*z) = t;
				end
				c = c+1;
			end
		end
		panel = imrotate(panel,90);

	 case 3
        panel  = zeros(side*x, side*y);
		c = 1;
		for j = side:-1:1
			for i = side:-1:1
			    if c <= nslices
				    t = reshape(data(:,:,slices(c)), x, y);
				    panel((i-1)*x+1:(i)*x,(j-1)*y+1:(j)*y) = t;
				end
				c = c+1;
			end
		end
		panel = imrotate(panel,-90);
end
