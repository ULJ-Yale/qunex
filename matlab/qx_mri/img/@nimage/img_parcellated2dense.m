function [img] = img_parcellated2dense(img, defineMissing)

%``img_parcellated2dense(img, defineMissing)``
%
%    Expands a parcelated image to a dense image
%
%   INPUTS
%   ======
%
%   --img               a parcelated cifti nimage image object to convert
%   --defineMissing     what value should be used in case of missing values
%                       (number or 'NaN') [0]
%
%   OUTPUT
%   ======
%
%   img
%       a resulting dense cifti nimage image object
%
%   USE
%   ===
%
%   This method is used to expand a parcellated cifti image to a dense cifti
%   image based on the information stored in cifti metadata.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% ---> process variables

if nargin < 2 || isempty(defineMissing),  defineMissing = 0; end

% ---> load cifti templates
load('cifti_templates.mat');

% the new cifti_brainmodel should replace the old one in QuNex
model = load('cifti_brainmodel');

% ------------------------------------------------------------------------
% The following steps were used to obtain a volume to grayordinates
% mapping, which was stored in the cifti_brainmodel_v2.mat data:
%
% wb_command -cifti-export-dense-mapping template.dtseries.nii COLUMN -volume-all vol.txt
% T = readtable('vol.txt');
% vol2gray = T{:,:}+1;
% vol2gray_mask = zeros(size(model.components.volumeMask));
% for i=1:size(vol2gray,1)
%     vol2gray_mask(vol2gray(i,2),vol2gray(i,3),vol2gray(i,4)) = vol2gray(i,1);
% end
% ------------------------------------------------------------------------

% --- create the output image
output_img = nimage();
output_img = output_img.zeroframes(img.frames);

if strcmpi(img.filetype, 'ptseries')
    output_img.filetype = 'dtseries';
    output_img.cifti = cifti_templates.dtseries;
    output_img.TR = img.cifti.metadata.diminfo{2}.seriesStep;
elseif strcmpi(img.filetype, 'pscalar')
    output_img.filetype = 'dscalar';
    output_img.cifti = cifti_templates.dscalar;
else
    error('ERROR: The image provided to img_parcellated2dense is neither ptseries nor pscalar! Aborting');
end

output_img.dim = output_img.cifti.metadata.diminfo{1}.length;
output_img.voxels = output_img.cifti.metadata.diminfo{1}.length;
output_img.cifti.metadata.diminfo{2} = img.cifti.metadata.diminfo{2};
output_img.cifti.maps = img.cifti.maps;
output_img.data = zeros([output_img.dim, output_img.frames]);

if defineMissing, output_img.data(:) = defineMissing; end

% --- extract parcels from the input image
parcels = img.cifti.metadata.diminfo{1,1}.parcels;

% --- loop over parcels for surface structures to expand parcel data
data = zeros(size(output_img.data));

all_surfs = {};
for i=1:length(parcels)
    for j=1:length(parcels(i).surfs)
        all_surfs{end+1} = parcels(i).surfs(j).struct;
    end
end
surfaces = lower(unique(all_surfs));

surf_data = [];
for i=1:length(surfaces)
    surf_data.(surfaces{i}) = zeros(size(model.cifti.(surfaces{i}).mask));
end

for f=1:output_img.frames

    for p=1:length(parcels)

        % --- expand parcellated surface data
        parcel = parcels(p);
        parcel_surfaces = lower({parcel.surfs.struct});
        for s=1:length(parcel_surfaces)
            surf_label = parcel_surfaces{s};
            surf_id = model.cifti.(surf_label).id;
            % surf_data = zeros(size(model.cifti.(surf_label).mask));
            if any(strcmp(surf_label, parcel_surfaces))
                surf_data.(surf_label)(parcel.surfs(s).vertlist+1) = img.data(p,f);
                data(model.cifti.start(surf_id):model.cifti.end(surf_id),f) = surf_data.(surf_label)(model.cifti.(surf_label).mask);
            end
        end

        % --- expand parcellated volume data
        n = size(parcel.voxlist,2);
        for v=1:n
            cifti_idx = model.mapping.vol2gray(parcel.voxlist(1,v)+1,parcel.voxlist(2,v)+1,parcel.voxlist(3,v)+1);
            if cifti_idx > 0
                data(cifti_idx,f) = img.data(p,f);
            end
        end

    end

end

% --- prepare output img data structure
output_img.data = data;
output_img.imageformat = 'CIFTI-2';
output_img.cifti.metadata.cdata = output_img.data;

img = output_img;

end
