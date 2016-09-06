function [img] = mri_EmbedMeta(img, data, code, name, verbose)

%function [img] = mri_EmbedMeta(img, data, code, name, verbose)
%
%   Aligns the data to mulitipe of 16 bytes and prepares to save as a metadata block in NIfTI file.
%
%   Input:
%       - data   : data to be embedded
%       - code   : metadata code to be used  [64]
%       - name   : if nonempty a name of the metadata block to be prepended []
%
%   (c) Grega Repovs
%   Grega Repovs - 2016-08-20 - Initial version
%

if nargin < 5 || isempty(verbose), verbose = false; end
if nargin < 4,                     name = []; end
if nargin < 3 || isempty(code),    code = 64; end
if nargin < 2, error('\n==> ERROR: Missing data to be embedded!'); end

if ~isempty(name)
    data = ['# meta: ' name 10 data];
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

