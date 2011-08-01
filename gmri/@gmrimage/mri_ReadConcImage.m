function [img] = mri_ReadConcImage(img, file, dtype, frames)

%       function [img] = mri_ReadConcImage(img, file, dtype, frames)
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
%

if nargin < 4
	frames = [];
	if nargin < 3 
	    dtype = 'single';
    end
end

files = img.mri_ReadConcFile(file);
nfiles = length(files);

img = gmrimage(char(files{1}), dtype, frames); 
img.runframes = img.frames;
for n = 2:nfiles
    nimg = gmrimage(char(files{n}), dtype, frames);
	img = [img nimg];
end