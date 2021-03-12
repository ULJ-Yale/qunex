function [img] = img_read_concimage(file, dtype, frames, verbose)

%``function [img] = img_read_concimage(file, dtype, frames, verbose)``
%
%   Reads and concatenates all image file specified in a .conc image.
%
%   INPUTS
%	======
%
%   --file  	filename (can be an .ifh or .img file)
%   --dtype 	number format to use ['single']
%   --frames 	number of frames to read [all]
%   --verbose 	whether to talk a lot [false]
%
%   OUTPUT
%	======
%
%   img 
%		a concatenated nimage object.
%
%   USE
%	===
%
%   The method is used to read and concatenate all the image files specified in
%   a .conc file int one nimage object. The method can be used either directly
%   or indirectly through nimage constructor call.
%
%   EXAMPLE USE
%	===========
%
%	::
%
%   	concimage = nimage.img_read_concimage('OP234-WM.conc');
%
%   Indirect use::
%
%   	concimage = nimage('OP234-WM.conc');
%

if nargin < 4, verbose = false; end
if nargin < 3, frames = []; end
if nargin < 2 || isempty(dtype), dtype = 'single'; end

file = strtrim(file);
files = nimage.img_read_concfile(file);
nfiles = length(files);

if verbose, fprintf('---> Reading %d files as specified in %s', nfiles, file), end

img = nimage(char(files{1}), dtype, frames, verbose);
img.runframes = img.frames;
for n = 2:nfiles
    nimg = nimage(char(files{n}), dtype, frames, verbose);
	img = [img nimg];
end
