function [vol_img] = img_extract_cifti_volume(img, data_format)

%``img_CIFTI2volume(img, data_format)``
%
%   Transforms a CIFTI nimage into a NIfTI volume nimage in order to allow the
%   usage of the existing methods for volume model analysis.
%
%   INPUTS
%    ======
%
%    --img
%    --data_format  - '2D' for NIfTY data format in 2D (default)
%                  - '4D' for NIfTY data foramt in 4D
%
%   OUTPUT
%    ======
%
%   vol_img
%        nimage in a NIfTI format.
%
%   EXAMPLE USE
%    ===========
%
%    ::
%
%       vol_img = img.img_extract_cifti_volume();
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% set Image2D as the default data format (if data_format is not passed)
if nargin < 2
    data_format = '2D';
end

% import CIFTI-2 components from the .mat file
load('cifti_brainmodel');

% create an empty NIfTI file
vol_img = nimage(zeros(91,109,91,img.frames));
vol_img.data = vol_img.image2D();

% remap the values from the imported CIFTI to the new NIfTI file
for i = 1:1:numel(img.cifti.shortnames)
    if strcmp(cifti.(lower(img.cifti.shortnames{i})).type, 'Volume')
        vol_img.data(components.indexMask == i,:) = img.data(img.cifti.start{i}:img.cifti.end{i},:);
    end
end

if strcmp(data_format,'4D')
    vol_img.data = vol_img.image4D;
end

end

