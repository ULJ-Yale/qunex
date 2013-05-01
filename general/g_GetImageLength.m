function [frames] = g_GetImageLength(file)

%	
%	Reads number of frames from IFH file for a given file or set of files listed in conc file
%	Return column row with lengths in frames
%
%
%	Grega Repovš - 2008.7.11
%

if strfind(file, '.conc')
	files = g_ReadConcFile(file);
else
	files = {file};
end

nfiles = length(files);
frames = zeros(nfiles,1);

for n = 1:nfiles
	ifh = g_ReadIFH(files{n});
	frames(n,1) = ifh.frames;
end

