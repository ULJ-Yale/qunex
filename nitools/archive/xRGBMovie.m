function [img] = RGBMovie(img, filename)

%
%		saves 3D matrix as a movie
%

dim = size(img);
frames = dim(3);
imgdim = [dim(1), dim(2)];

% --- normalize

img(img<0) = 0;
img = img ./ max(max(max(img)));


wOb = VideoWriter(filename, 'Archival');
wOb.FrameRate = 1;

open(wOb);

for f = 1:frames
    t = zeros(imgdim);
    t(:,:,1) = img(:,:,f);
    t(:,:,2) = img(:,:,f);
    t(:,:,3) = img(:,:,f);
    writeVideo(wOb, im2frame(t));
end

close(wOb);
