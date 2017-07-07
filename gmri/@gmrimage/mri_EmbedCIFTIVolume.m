function [img] = mri_EmbedCIFTIVolume(img, vol_img)

%function [img] = mri_EmbedCIFTIVolume(img, vol_img)
%
%   Overwrites the CIFTI-2 gmrimage with a modified/analyzed NIfTY model.
%
%   INPUT
%       vol_img  - gmrimage in a NIfTI format.
%
%   USE EXAMPLE
%       img = img.mri_EmbedCIFTIVolume(vol_img);
%
%   ---
%   Written by Aleksij Kraljic, 23-06-2017

% import CIFTI-2 components from the .mat file
load('CIFTI_BrainModel.mat');

% convert the NIfTI format to 2D
vol_img.data = vol_img.image2D;

% remap the values from the NIfTI to CIFTI-2 gmrimage
for i = 1:1:numel(img.cifti.shortnames)
    if strcmp(cifti.(lower(img.cifti.shortnames{i})).type, 'Volume')
        img.data(img.cifti.start(i):img.cifti.end(i),:) = vol_img.data(components.indexMask == i,:);
    end
end

end

