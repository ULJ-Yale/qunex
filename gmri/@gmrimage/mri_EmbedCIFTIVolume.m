function [img] = mri_EmbedCIFTIVolume(img, vol_img)

%function [img] = mri_EmbedCIFTIVolume(img, vol_img)
%
%   Overwrites the CIFTI-2 gmrimage with a modified/analyzed NIfTY model.
%
%   INPUT
%       vol_img  - gmrimage in a NIfTI format.
%
%   USE EXAMPLE
%   >>> img.mri_volume2CIFTI(vol_img);
%
%   ---
%   Written by Aleksij Kraljic, 23-06-2017

% import CIFTI-2 components from the .mat file
load('CIFTI_BrainModel.mat');

% remap the values from the NIfTI to CIFTI-2 gmrimage
for i = 1:1:numel(img.cifti.shortnames)
    if strcmp(cifti.(lower(img.cifti.shortnames{i})).type, 'Volume')
        A = cifti.(lower(img.cifti.shortnames{i})).indices;
        j=1;
        for k = img.cifti.start(i):1:img.cifti.end(i)
            img.data(k) = vol_img.data(A(j,1)+1,A(j,2)+1,A(j,3)+1);
            j=j+1;
        end
    end
end

end

