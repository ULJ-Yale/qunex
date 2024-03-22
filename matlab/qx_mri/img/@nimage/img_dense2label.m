function [img] = img_dense2label(img, map_names)

%``img_dense2label(img, map_names)``
%
%    Expands a parcelated image to a dense image
%
%   INPUTS
%   ======
%
%   --img               a parcelated cifti nimage image object to convert
%   --map_names         a cell array of map names (number of maps must
%                       equal the number of frames in the input image
%
%   OUTPUT
%   ======
%
%   img
%       a resulting dense cifti nimage object
%
%   USE
%   ===
%
%   This method is used to convert a dense cifti image to a label cifti
%   image.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2 || isempty(map_names), map_names = {};  end

% --- test whether the input image contains only integer values
if any(any(floor(img.data) ~= img.data))
    error('Input image contains non-integer data values -> only integer values supported to convert a "labeled" dense input image to label!');
end

img.filetype = 'dlabel';
num_maps = img.frames;

% --- populate img.cifti.maps -> here go just map names {'Map 1'} {'Map 2'} ... {'Map N'}
if isempty(map_names)
    map_names = cell(1,num_maps);
    for i=1:num_maps
        map_names{i} = sprintf('Map %0.0f',i);
    end
end

% --- create maps array of structs
max_regions_per_map = 0;
for i=1:num_maps
    regions_per_map = length(unique(img.data(:,i)));
    if regions_per_map > max_regions_per_map
        max_regions_per_map = regions_per_map;
    end
end

% --- populate img.cifti.labels -> cell array with as many elements as there are maps
%     each cell elements is a struct with fields name, key, rgba
cmap = jet;
color_matrix = cmap(round(linspace(1, size(cmap, 1), max_regions_per_map)), :);
color_matrix = color_matrix(randperm(max_regions_per_map), :);
color_matrix(:, 4) = 1;
color_matrix = color_matrix';

maps = [];
labels = cell(1, num_maps);
img.cifti.maps = cell(1,num_maps);
for i=1:num_maps
    img.cifti.maps{i} = map_names{i};

    labels{i} = [];

    regions = unique(img.data(:,i));

    label = [];
    for j=1:length(regions)
        label(j).name = sprintf('Region %0.04f', j);
        label(j).key = regions(j);
        label(j).rgba = color_matrix(:,j);
    end
    labels{i} = label;

    maps(i).name = map_names{i};
    maps(i).metadata = struct('key', {}, 'value', {});
    maps(i).table = labels{i};
end
img.cifti.labels = labels;

% --- fill out cifti.metadata temporal information (.diminfo{2})
img.cifti.metadata.diminfo{2} = [];
img.cifti.metadata.diminfo{2}.type = 'labels';
img.cifti.metadata.diminfo{2}.length = num_maps;
img.cifti.metadata.diminfo{2}.maps = maps;

end