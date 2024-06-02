function [img] = img_convert_cifti(img, output_format, parcel_img, parcel_method, map_names, verbose)
%``img_convert_cifti(img, output_format, parcel_img, parcel_method, map_names, verbose)``
%
%    Converts a CIfTI nimage to a different format.
%
%   INPUTS
%   ======
%
%   --img               an input cifti image to be converted
%   --output_format     a desired output format:
%                           'dense'     - dense cifti image
%                           'parcellated' - parcellated cifti image
%                           'label'     - label cifti image
%   --parcel_img        a parcellated reference image (required for dense
%                       to parcellated conversion)
%   --parcel_method     a method for converting to parcellated format
%   --map_names         a cell array of map names (number of maps must
%                       equal the number of frames in the input image
%   --verbose           a boolean indicating whether the function is verbose
%                       [false]
%
%   OUTPUT
%   ======
%
%   img
%       a resulting converted cifti nimage object
%
%   USE
%   ===
%
%   This method is used to convert a cifti image another cifti format.
%
%   NOTES
%   =====
%
%   Supported conversions:
% 
%   DENSE TO PARCELLATED (requires a parcel reference input image)
%       a) dscalar -> pscalar
%       b) dtseries -> ptseries
% 
%   PARCELLATED TO DENSE
%       c) pscalar -> dscalar
%       d) ptseries -> dtseries
%
%   PARCELLATED TO LABEL
%       e) pscalar -> dlabel
%       f) ptseries -> dlabel
% 
%   DENSE TO LABEL (optional input is map names)
%       g) dscalar -> dlabel
%       h) dtseries -> dlabel
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 6 || isempty(verbose),       verbose = false;        end
if nargin < 5 || isempty(map_names),     map_names = {};         end
if nargin < 4 || isempty(parcel_method), parcel_method = 'mean'; end
if nargin < 3 || isempty(parcel_img),    parcel_img = [];        end

input_format = lower(img.filetype);
output_format = lower(output_format);

% --- convert input format to general format description
if strcmpi(input_format, 'dscalar') || strcmpi(input_format, 'dtseries')
    input_format = 'dense';
elseif strcmpi(input_format, 'pscalar') || strcmpi(input_format, 'ptseries')
    input_format = 'parcellated';
elseif strcmpi(input_format, 'dlabel')
    input_format = 'label';
end

% --- convert the image to the desired format
if strcmpi(input_format, 'dense') && strcmpi(output_format, 'parcellated')
    % --- convert dense to parcellated
    if verbose, fprintf('---> converting dense to parcellated\n'); end
    if isempty(parcel_img)
        error('A parcellated reference image is required for dense to parcellated conversion');
    end
    img = img.img_extract_roi(parcel_img, [], parcel_method, [], [], true);

elseif strcmpi(input_format, 'parcellated') && strcmpi(output_format, 'dense')
    % --- convert parcellated to dense
    if verbose, fprintf('---> converting parcellated to dense\n'); end
    img = img.img_parcellated2dense();

elseif strcmpi(input_format, 'parcellated') && strcmpi(output_format, 'label')
    % --- convert parcellated to label
    if verbose, fprintf('---> converting parcellated to label\n'); end
    img_d = img.img_parcellated2dense();
    img_d_single_frame = img_d;
    img_d_single_frame.data = img_d_single_frame.data(:,1);
    img_d_single_frame.frames = 1;
    img_d_single_frame.runframes = 1;
    parcel_data = unique(img_d_single_frame.data);
    for i = 1:length(parcel_data)
        img_d_single_frame.data(img_d_single_frame.data == parcel_data(i)) = i;
    end
    img = img_d_single_frame.img_dense2label({});

elseif strcmpi(input_format, 'dense') && strcmpi(output_format, 'label')
    % --- convert dense to label
    if verbose, fprintf('---> converting dense to label\n'); end
    img = img.img_dense2label(map_names);

end

img.cifti.metadata.metadata = [];

end