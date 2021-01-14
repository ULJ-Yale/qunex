function [out] = fc_MostActiveVoxels(imgf, percent)

img = fc_Read4DFP(imgf);

imgs = sort(img, 'descend');

nvoxels = size(img,1);
nactive = ceil(nvoxels*percent);
t = imgs(nactive);
out = (img >= t);


