function [img m] = fc_FDRThreshold(img, mask, q)

%	
%	Takes in an image of p values, mask and fdr target and returns FDR threshholded image.
%	
% 	Created by  on 2008-02-10.
% 	Copyright (c) 2008 . All rights reserved.
%	

s_img = size(img);

if (isempty(mask))
	mask = ones(s_img);
end

img = reshape(img, [],1);
mask = reshape(mask, [],1);

nvox = sum(mask);

target = img(mask==1);

%  ---- thresholding with FDR

vrank = [1:nvox]';
vcrit = (vrank./nvox).*q;
ps = sort(target);
vrank(ps>vcrit)=0;
vrank = max(vrank);
vcrit = (vrank./nvox).*q;
vcrit = repmat(vcrit, nvox,1);

target(target>vcrit) = 0.9;

img(mask ~= 1) = 0.9;
img(mask == 1) = target;

m = zeros(s_img);
tm = zeros(size(target));

tm(target <= vcrit) = 1;
m(mask==1) = tm;

img = reshape(img, s_img);
m = reshape(m, s_img);

