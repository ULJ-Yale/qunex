function [img] = g_Read4DFP(file, dtype)

%   [img] = g_Read4DFP(file, dtype)
%
%
%	Reads in a 4dfp image (.img or .conc) and returns a vector with all the voxels
%
%   Required:
%       file - filename
%
%   Optional:
%       dtype - datatype to use [single]
%
%   Grega Repovš - a long, long time ago
%

if ~g_CheckFile(file, '', 'nothing');
	fprintf('\nERROR: Could not open %s, file does not exist. Please check your paths!\n\n', file);
	img = false;
	return
end


if nargin < 2
	dtype = 'double';
end

if FileType(file)

	files = g_ReadConcFile(file);
	nfiles = length(files);

	img = [];
	for n = 1:nfiles
		img = [img; g_Read4DFP(char(files{n}), dtype)]; 
	end
else

    ifh = g_ReadIFH(file);
    mformat = 'b';
    if (~isempty(ifh))
	    if ismember('littleendian', ifh.value)
    	    mformat = 'l';
    	end
    end
    
	[fim message] = fopen(file, 'r', mformat);
	if fim == -1
        error('\n\nERROR: Could not open %s for reading. Please check your paths!\n\nMatlab message: %s', file, message);
    end
	img = fread(fim, ['float32=>' dtype]);
	fclose(fim);
end


function [ftype] = FileType(filename)

if filename(length(filename)-4:end) == '.conc'
	ftype = 1;
elseif filename(length(filename)-3:end) == '.img'
	ftype = 0;
else
	error('\n%s is neither a conc nor an image file! Aborting', filename);
end


% if strfind(filename, '.conc')
% 	ftype = true;
% elseif strfind(filename, '.img')
% 	ftype = false;
% else
% 	error('\n%s is neither a conc nor an image file! Aborting', filename);
% end
