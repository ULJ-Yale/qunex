function [img] = mri_CIFTIEmbedd(img, structures, data)

%function [img] = mri_CIFTIEmbedd(img, structures, data)
%
%	Embedds given data in the listed structures. The data must be either a single string and a matrix
%   or a cell array of strings and matrices.
%
%
%   (c) Grega Repovs, 2014-08-01
%

if nargin < 3
    error('ERROR: Not enough parameters provided to embedd data into CIFTI!');
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

    % --- embedd data

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
