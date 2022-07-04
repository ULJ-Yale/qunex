function [img] = img_cifti_embed(img, structures, data)
%``img_cifti_embed(img, structures, data)``
%
%    Embeds given data in the listed CIFTI structures.
%
%   INPUTS
%   ======
%
%   --img          A CIFTI image.
%   --structures   Either a single string or a cell array of strings, specifying 
%                  the CIFTI structures for which data is to be embedded in.
%   --data         Either a single matrix or a cell array of matrices, that hold 
%                  the data that is to be embedded for the given structure.
%
%   OUTPUT
%   ======
%
%   img
%       An image with the specified data embedded.
%
%   USE
%   ===
%
%   The method assumes that the image provided is a standard 32k CIFTI image and
%   enables embedding data into a desired structure or structures. The stuctures
%   can be specified either using their short (e.g. CORTEX_LEFT) or long (e.g.
%   CIFTI_STRUCTURE_CORTEX_LEFT) names. For successfull embedding, first, the
%   structures listed in the structures variable have to be in the same order as
%   matrices passed in the data variable. Second, the dimensions of the data
%   matrice(s) have to match the structure dimensions in both number of rows
%   (the number of vertices or voxels in the structure) and number of columns
%   (the number of) dataframes in the original image. List of structure names is
%   listed in img.cifti.longnames and img.cifti.shortnames.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%
%       img = img.img_cifti_embed({'CORTEX_LEFT', 'CORTEX_RIGHT'}, ...
%           {cortex_left_data, cortex_right_data});
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 3
    error('ERROR: Not enough parameters provided to embed data into CIFTI!');
end

if ~isa(structures, 'cell')
    structures = {structures};
end

if ~isa(data, 'cell')
    data = {data};
end

nstruct = length(structures);
if nstruct ~= length(data)
    error('ERROR: The number of provided structures does not match with provided data!');
end

img.data = img.image2D;

% --- loop through structures

for n = 1:nstruct

    % --- get the structure

    s = find(ismember(img.cifti.longnames, upper(structures{n})));
    if isempty(s)
        s = find(ismember(img.cifti.shortnames, upper(structures{n})));
        if isempty(s)
            fprintf('\nWARNING: Could not match %s with any CIFTI structure. Data not embedded!\n', structures{n});
        end
    end

    % --- embed data

    d = data{n};
    dim = prod(size(d));
    if dim == 1
        img.data(img.cifti.start(s):img.cifti.end(s),:) = d;
    elseif dim == img.frames
        img.data(img.cifti.start(s):img.cifti.end(s),:) = repmat(reshape(d, 1, img.frames), img.cifti.length(s), 1);
    elseif dim == img.cifti.length(s)
        img.data(img.cifti.start(s):img.cifti.end(s),:) = repmat(reshape(d, img.cifti.length(s), 1), 1, img.frames);
    elseif dim == img.frames * img.cifti.length(s)
        img.data(img.cifti.start(s):img.cifti.end(s),:) = d;
    else
        fprintf('\nWARNING: Data dimensions do not match structure / frame length. Data could not be embedded for %s!\n', structures{n});
    end
end
