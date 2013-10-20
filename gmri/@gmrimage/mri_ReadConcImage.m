function [img] = mri_ReadConcImage(img, file, dtype, frames, verbose)

%function [img] = mri_ReadConcImage(img, file, dtype, frames, verbose)
%
%		Reads in a 4dfp image into an image object
%
%       required:
%		    img   - mrimage object
%           file  - filename (can be an .ifh or .img file)
%
%		optional:
%           dtype - number format to use ['single']
%           frames - number of frames to read [all]
%
%       Grega Repovs - 2011-02-11
%       Grega Repovs - 2013-10-20 - Added verbose option
%

if nargin < 5
    verbose = false;
    if nargin < 4
    	frames = [];
    	if nargin < 3
    	    dtype = 'single';
        end
    end
end

file = strtrim(file);
files = img.mri_ReadConcFile(file);
nfiles = length(files);

if verbose, fprintf('---> Reading %d files as specified in %s', nfiles, file), end

img = gmrimage(char(files{1}), dtype, frames, verbose);
img.runframes = img.frames;
for n = 2:nfiles
    nimg = gmrimage(char(files{n}), dtype, frames, verbose);
	img = [img nimg];
end