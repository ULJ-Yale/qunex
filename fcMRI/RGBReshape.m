function [img] = RGBReshape(in, v)

%
%		reshapes image and returns composite of axial, sagital and transversal slices in a 2D matrix
%

data = squeeze(in.image4D);
dim  = size(data);
x    = dim(1);
y    = dim(2);
z    = dim(3);

switch v
	 case 1
	    side = ceil(sqrt(x));
        img  = zeros(side*y, side*z);
		c = 1;
		for j = 1:side
			for i = 1:side
			    if c <= x
				    t = reshape(data(c,:,:), y, z);
				    img((i-1)*y+1:(i)*y,(j-1)*z+1:(j)*z) = t;
				end
				c = c+1;
			end
		end
		img = imrotate(img,90);
		
	 case 2
	    side = ceil(sqrt(y));
        img  = zeros(side*x, side*z);
		c = 1;
		for j = 1:side
			for i = 1:side
			    if c <= y
				    t = reshape(data(:,c,:), x, z);
				    img((i-1)*x+1:(i)*x,(j-1)*z+1:(j)*z) = t;
				end
				c = c+1;
			end
		end
		img = imrotate(img,90);

	 case 3
	    side = ceil(sqrt(z));
        img  = zeros(side*x, side*y);
		c = 1;
		for j = 1:side
			for i = 1:side
			    if c <= z
				    t = reshape(data(:,:,c), x, y);
				    img((i-1)*x+1:(i)*x,(j-1)*y+1:(j)*y) = t;
				end
				c = c+1;
			end
		end
		img = imrotate(img,270);
end