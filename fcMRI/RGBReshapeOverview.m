function [img] = RGBReshapeOverview(in, v, slice)

%
%		reshapes image and returns composite of specified axial, coronal and saggital slice
%

data = squeeze(in.image4D);
dim  = size(data);
x    = dim(1);
y    = dim(2);
z    = dim(3);
f    = dim(4);

img = zeros([x+z, y+z, f]);

for nf = 1:f
    img(1:x,1:y,nf) = data(:,:,slice(3),nf);
    img(x+1:x+z,1:y,nf) = squeeze(data(slice(1),:,:,nf))';
    img(1:x,y+1:y+z,nf) = squeeze(data(:,slice(2),:,nf));
end

img = imrotate(img,90);

