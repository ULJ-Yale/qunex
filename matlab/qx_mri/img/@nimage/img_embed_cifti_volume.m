function [img] = img_embed_cifti_volume(img, vol_img)

%``img_embed_cifti_volume(img, vol_img)``
%
%   Overwrites the CIFTI-2 nimage with a modified/analyzed NIfTY model.
%
%   INPUTS
%    ======
%
%    --img
%   --vol_img    nimage in a NIfTI format.
%
%    OUTPUT
%    ======
%
%    img
%
%   EXAMPLE USE
%    ===========
%
%    ::
%       img = img.img_embed_cifti_volume(vol_img);
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% import CIFTI-2 components from the .mat file
load('cifti_brainmodel');

% convert the NIfTI format to 2D
vol_img.data = vol_img.image2D;

% remap the values from the NIfTI to CIFTI-2 nimage
for i = 1:1:numel(img.cifti.shortnames)
    if strcmp(cifti.(lower(img.cifti.shortnames{i})).type, 'Volume')
        img.data(img.cifti.start{i}:img.cifti.end{i},:) = vol_img.data(components.indexMask == i,:);
    end
end

end

