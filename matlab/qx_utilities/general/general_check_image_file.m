function [file_info] = general_check_image_file(filename)

%``function [image_type, file_exists] = general_check_image_file(filename)``
%
%   Checks whether the file is a valid image file, and returns information
%   about the file.
%
%   Parameters:
%       --filename (str):
%           The path to the file to check for.
%
%   Returns:
%       file_info
%           A structure with the following information:
%           - filename   ... the provided filename
%           - path       ... the path to the file
%           - basename   ... the basename of the file
%           - rootname   ... the root name without the extension
%           - extension  ... the image file extension
%           - image_type ... the kind of image file
%           - exists     ... whether the file exists in the filesystem
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 1, filename = ''; end

[filepath, name, ext] = fileparts(filename);

file_info = struct('filename', filename, 'path', filepath, 'basename', [name ext], 'rootname', name, 'extension', ext, 'is_image', false, 'image_type', '', 'exists', exist(filename, 'file') == 2);

image_type = regexp([name ext], '(\.4dfp\.img|\.4dfp\.ifh|.4dfp\.hdr|\.dconn\.nii|\.dtseries\.nii|\.dscalar\.nii|\.dlabel\.nii|\.dpconn\.nii|\.pconnseries\.nii|\.pconnscalar\.nii|\.pconn\.nii|\.ptseries\.nii|\.pscalar\.nii|\.pdconn\.nii|\.dfan\.nii|\.fiberTemp\.nii|\.nii\.gz|\.nii)$', 'tokens');
if ~isempty(image_type)
    image_type = image_type{1}{1};
    file_info.is_image = true;
    file_info.extension = image_type;
    file_info.rootname = strrep(file_info.basename, image_type, '');
    if strcmp(image_type, '.nii') || strcmp(image_type, '.nii.gz')
        file_info.image_type = 'nifti';
    else
        image_type = strrep(image_type, '.nii', '');
        file_info.image_type = image_type(2:end);
    end
end
