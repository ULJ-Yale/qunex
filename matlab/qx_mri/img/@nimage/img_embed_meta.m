function [img] = img_embed_meta(img, data, code, name, verbose)

%``img_embed_meta(img, data, code, name, verbose)``
%
%   Method for embedding meta-data in a format ready to save in the extension
%   part of the NIfTI files.
%
%   INPUTS
%    ======
%
%   --img         a nimage image object
%   --data        data to be embedded
%   --code        metadata code to be used  [64]
%   --name        if nonempty a name of the metadata block []
%   --verbose     whether to be talkative
%
%   OUTPUT
%   ======
%
%    img
%        a nimage image object with added meta data
%
%   USE
%    ===
%
%   The method is used to prepare meta-data to be added to the extension part of
%   the NIfTI image file. If name is specified, the method assumes that the data
%   is a string and prepends a line::
%
%       # meta: <name>
%
%   which helps interpreting data present in the NIfTI file. The method adds as
%   many spaces (ASCII value 32) at the end, as needed for the data to be a
%   multiple of 16 bytes long, as required by NIfTI specification. It adds a
%   newline ASCII code at the end if one is not yet present. "code" is a code
%   specified as part of the extension data description. If not provided the
%   code has value 64, which is not yet used / defined in the NIfTI
%   specification.
%
%   EXAMPLE USE
%    ===========
%
%    ::
%   
%        img = img.img_embed_meta(datatable, [], 'Behavioral results');
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 5 || isempty(verbose), verbose = false; end
if nargin < 4,                     name = []; end
if nargin < 3 || isempty(code),    code = 64; end
if nargin < 2, error('\n---> ERROR: Missing data to be embedded!'); end

if ~isempty(name)
    data = ['# meta: ' name char(10) data];
end

% -- embed data
if verbose, fprintf('\n ---> Embedding meta %s [code %d]', name, code); end

img.meta(end+1).code = code;
img.meta(end).size   = ceil((length(data)+8)/16)*16;
img.meta(end).data   = ones(1, img.meta(end).size-8, 'uint8') * 32;
img.meta(end).data(1:length(data)) = data;

% -- add newline at the end of the original data if not yet present

if (img.meta(end).size - 8) > length(data) && data(end) ~= 10
    img.meta(end).data(length(data)+1) = 10;
end

