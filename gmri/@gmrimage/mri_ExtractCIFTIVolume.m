function [vol_img] = mri_ExtractCIFTIVolume(img, data_format)

%function [vol_img] = mri_CIFTI2volume(img, data_format)
%
%   Transforms a CIFTI gmrimage into a NIfTI volume gmrimage in order to
%   allow the usage of the existing methods for volume model analysis.
%
%   INPUT
%       data_format  - '2D' for NIfTY data format in 2D (default)
%                      '4D' for NIfTY data foramt in 4D
%
%   OUTPUT
%       vol_img  - gmrimage in a NIfTI format.
%
%   USE EXAMPLE
%       vol_img = img.mri_ExtractCIFTIVolume();
%
%   ---
%   Written by Aleksij Kraljic, 23-06-2017

% set Image2D as the default data format (if data_format is not passed)
if nargin<2
    data_format = '2D';
end

% import CIFTI-2 components from the .mat file
load('CIFTI_BrainModel.mat');

% create an empty NIfTI file
vol_img = gmrimage(zeros(91,109,91,img.frames));
vol_img.data = vol_img.image2D();

% remap the values from the imported CIFTI to the new NIfTI file
for i = 1:1:numel(img.cifti.shortnames)
    if strcmp(cifti.(lower(img.cifti.shortnames{i})).type, 'Volume')
        vol_img.data(components.data2D == i,:) = img.data(img.cifti.start(i):img.cifti.end(i),:);
    end
end

if strcmp(data_format,'4D')
    vol_img.data = vol_img.image4D;
end

end

