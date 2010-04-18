function [img] = RGBReshape(in, v)

%
%		reshapes 4dfp image and returns composite of axial, sagital and transversal slices in a 2D matrix
%

in = reshape(in,48, 64, 48);
img = zeros(384, 384);

switch v
	 case 1
	 	c = 1;
		for j = 8:-1:1
			for i = 1:8
				t = reshape(in(:,c,:),48,48);
				img((i-1)*48+1:(i)*48,(j-1)*48+1:(j)*48) = t;
				c = c+1;
			end
		end
		img = imrotate(img,90);
		
	 case 2
		c = 48;
		for j = 8:-1:1
			for i = 1:6
				t = reshape(in(c,:,:),64,48);
				img((i-1)*64+1:(i)*64,(j-1)*48+1:(j)*48) = t;
				c = c-1;
			end
		end
		img = imrotate(img,90);

	 case 3
		c = 1;
		for j = 6:-1:1
			for i = 1:8
				t = reshape(in(:,:,c),48,64);
				img((i-1)*48+1:(i)*48,(j-1)*64+1:(j)*64) = t;
				c = c+1;
			end
		end

		img = imrotate(img,270);
end