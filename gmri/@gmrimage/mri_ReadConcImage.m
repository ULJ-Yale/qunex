function [img] = mri_ReadConcImage(file, dtype, frames, verbose)

%function [img] = mri_ReadConcImage(file, dtype, frames, verbose)
%
%   Reads and concatenates all image file specified in a .conc image.
%
%   INPUT
%
%   required:
%       file  - filename (can be an .ifh or .img file)
%
%   optional:
%       dtype - number format to use ['single']
%       frames - number of frames to read [all]
%       verbose - whether to talk a lot [false]
%
%   OUTPUT
%       img  - a concatenated gmrimage object.
%
%   USE
%   The method is used to read and concatenate all the image files specified in
%   a .conc file int one gmrimage object. The method can be used either directly
%   or indirectly through gmrimage constructor call.
%
%   EXAMPLE USE
%   >>> concimage = gmrimage.mri_ReadConcImage('OP234-WM.conc');
%
%   Indirect use:
%   >>> concimage = gmrimage('OP234-WM.conc');
%
%   ---
%   Written by Grega Repovs - 2011-02-11
%
%   Changelog
%       2013-10-20 Grega Repovs
%                - Added verbose option
%       2017-03-11 Grega Repovs
%                - Change to static method
%

if nargin < 4, verbose = false; end
if nargin < 3, frames = []; end
if nargin < 2 || isempty(dtype), dtype = 'single'; end

file = strtrim(file);
files = gmrimage.mri_ReadConcFile(file);
nfiles = length(files);

if verbose, fprintf('---> Reading %d files as specified in %s', nfiles, file), end

img = gmrimage(char(files{1}), dtype, frames, verbose);
img.runframes = img.frames;
for n = 2:nfiles
    nimg = gmrimage(char(files{n}), dtype, frames, verbose);
	img = [img nimg];
end