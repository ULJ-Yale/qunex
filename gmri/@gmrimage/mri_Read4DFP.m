function [img] = mri_Read4DFP(img, file, dtype, frames)

%       function [img] = mri_Read4DFP(img, file, dtype)
%
%		Reads in a 4dfp image into an image object
%
%       required:
%		    img   - mrimage object
%           file  - filename (can be a .conc., .ifh or .img file)
%
%		optional:
%           dtype - number format to use ['single']
%           frames - number of frames to read [all]
%
%       Grega Repovs - 2009-11-19
%

if nargin < 4
	frames = [];
	if nargin < 3 
	    dtype = 'single';
    end
end


if FileType(file)

	files = img.mri_ReadConcFile(file);
	nfiles = length(files);

    img = img.mri_Read4DFP(char(files{1}), dtype);
	for n = 2:nfiles
		img = [img img.mri_Read4DFP(char(files{n}), dtype)]; 
	end
else
    root = strrep(file, '.img', '');
    root = strrep(root, '.4dfp', '');
    root = strrep(root, '.ifh', '');

    img.rootfilename = root;
    
    img.hdr4dfp = img.mri_ReadIFH([root '.4dfp.ifh']);
    
    img.imageformat = '4dfp';
    img.filename = [root '.4dfp.img'];
    img.TR = [];

    x = str2num(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'matrix size [1]'}))));
    y = str2num(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'matrix size [2]'}))));
    z = str2num(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'matrix size [3]'}))));
    img.dim = [x y z];
    img.voxels = x*y*z;
    
    mformat = 'b';
    if ismember('littleendian', img.hdr4dfp.value)
        mformat = 'l';
    end

	[fim message] = fopen([root '.4dfp.img'], 'r', mformat);
	if fim == -1
        error('\n\nERROR: Could not open %s for reading. Please check your paths!\n\nMatlab message: %s', file, message);
    end
    if isempty(frames)
	    img.data = fread(fim, ['float32=>' dtype]);
	else
	    img.data = fread(fim, img.voxels*frames, ['float32=>' dtype]);
    end
	fclose(fim);

    img.frames = length(img.data)/sum(img.voxels);
    img.runframes = img.frames;
    img.hdr4dfp.value{ismember(img.hdr4dfp.key, {'matrix size [4]'})} = num2str(img.frames);

    xmm = str2num(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'scaling factor (mm/pixel) [1]'}))));
    ymm = str2num(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'scaling factor (mm/pixel) [2]'}))));
    zmm = str2num(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'scaling factor (mm/pixel) [3]'}))));
    img.vsizes = [xmm ymm zmm];
end


function [ftype] = FileType(filename)

if strcmp(filename(length(filename)-4:end), '.conc')
	ftype = 1;
elseif strcmp(filename(length(filename)-3:end), '.img')
	ftype = 0;
else
	error('\n%s is neither a conc nor an image file! Aborting', filename);
end

