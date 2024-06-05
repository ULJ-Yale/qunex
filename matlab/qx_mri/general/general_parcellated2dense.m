function [img] = general_parcellated2dense(inimg, outimg, verbose, missingvalues)

%``general_parcellated2dense(inimg, outimg, verbose, missingvalues)``
%
%   Expands the parcelated file to a dense file
%
%   Parameters:
%       --inimg (str):
%           A path to the image to expand.
%
%       --outimg (str, default inimg):
%           An optional path where the expanded image is to be saved. If not
%           provided, the specified inimg path is used.
%
%       --verbose (bool, default false):
%           Should it report the details.
%
%       --missingvalues (str, default '0'):
%           What value should be used in case of missing values (numeric or NaN)
%           provided as a string.
%
%   Returns:
%       img
%           A dense cifti nimage image object.
%
%   Notes:
%       This method is used to expand a parcellated cifti data file to a cifti
%       dense data file based on the information stored in cifti metatada.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% ---> process variables

if nargin < 4 || isempty(missingvalues), missingvalues = '0'; end
if nargin < 3 || isempty(verbose),       verbose  = false;    end
if nargin < 2,                           outimg   = [];       end

missingvalues = str2num(missingvalues);

% ---> check that input is present

general_check_file(inimg, 'input file');

if isempty(outimg)
    [filepath, filename, ext] = fileparts(inimg);
else
    [filepath, filename, ext] = fileparts(outimg);
    general_check_file(filepath, 'output folder');
end


if verbose, fprintf('\n---> Loading %s', inimg), end
img = nimage(inimg);
img = img.img_parcellated2dense(verbose, missingvalues);

% ---> save
if isempty(outimg)
    outimg = [img.rootfilename '.' img.filetype '.nii'];
end

if verbose, fprintf('\n---> saving %s', outimg), end
img.img_saveimage(outimg);

if verbose, fprintf('\n---> done\n'), end

