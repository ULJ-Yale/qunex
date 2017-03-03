function [img] = RGBReshape(in, v, slices)

%
%		reshapes image and returns composite of axial, sagital and transversal slices in a 2D matrix
%

if nargin < 3
	slices = [];
	if nargin < 2
		v = 3;
	end
end

data = squeeze(in.image4D);
dim  = size(data);
x    = dim(1);
y    = dim(2);
z    = dim(3);

if isempty(slices)
	slices = [1:dim(v)];
end
slices = slices(slices > 0);
slices = slices(slices <= dim(v));

nslices = length(slices);
side = ceil(sqrt(nslices));

switch v
	 case 1
        img  = zeros(side*y, side*z);
		c = 1;
		for j = 1:side
			for i = 1:side
			    if c <= nslices
				    t = reshape(data(slices(c),:,:), y, z);
				    img((i-1)*y+1:(i)*y,(j-1)*z+1:(j)*z) = t;
				end
				c = c+1;
			end
		end
		img = imrotate(img,90);

	 case 2
        img  = zeros(side*x, side*z);
		c = 1;
		for j = 1:side
			for i = 1:side
			    if c <= nslices
				    t = reshape(data(:,slices(c),:), x, z);
				    img((i-1)*x+1:(i)*x,(j-1)*z+1:(j)*z) = t;
				end
				c = c+1;
			end
		end
		img = imrotate(img,90);

	 case 3
        img  = zeros(side*x, side*y);
		c = 1;
		for j = side:-1:1
			for i = side:-1:1
			    if c <= nslices
				    t = reshape(data(:,:,slices(c)), x, y);
				    img((i-1)*x+1:(i)*x,(j-1)*y+1:(j)*y) = t;
				end
				c = c+1;
			end
		end
		img = imrotate(img,-90);
end