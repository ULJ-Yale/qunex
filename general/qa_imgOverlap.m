function [] = imgOverlap(af, bf, tf, v)

%function [] = imgOverlap(af, bf, tf, v)
%
%	Function that prints the overlap of two images, one in red, another in green.
%
%	Input:
%		af - the first image file
%		bf - the second image file
%		tf - the file to save the overlap to 
%		v  - which slice view (1, 2, 3)

if nargin < 4
	v = 3;
	if nargin < 3
		help imgOverlap;
		error('ERROR: At least three parameters are required!');
	end
end

if isobject(af)
	a =	af;
else 
	a = gmrimage(af);
end
	
if isobject(bf)
	b =	bf;
else 
	b = gmrimage(bf);
end

am = RGBReshape(a, v);
bm = RGBReshape(b, v);

am = normalize(am);
bm = normalize(bm);

rgb = zeros([size(am) 3]);
rgb(:,:,1) = am;
rgb(:,:,2) = bm;

imwrite(rgb, tf);


function [im] = normalize(im)
	
	os = size(im);
	im = reshape(im, [], 1);
	m  = mean(im);
	s  = std(im);
	mv = m+3*s;
	im(im > mv) = mv;
	im(im < 0) = 0;
	im = im./mv;
	im = reshape(im, os);