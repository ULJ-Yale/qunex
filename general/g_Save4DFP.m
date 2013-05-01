function [res] = g_Save4DFP(file, data, extra)

%
%	Writes out a 4dfp image 
%	Saves ifh data for 333 file along with possble extra data in key - value string pairs
%

if nargin < 3
	extra = [];
end


root = strrep(file, '.img', '');

[fim message] = fopen(file,'w','b');
if fim == -1
    error('\n\nERROR: Could not open %s for saving. Please check your paths!\n\nMatlab message: %s', file, message);
end


res = fwrite(fim, data, 'float32');
fclose(fim);

hdrf = strcat(root, '.hdr');
ifhf = strcat(root, '.ifh');

if (exist(hdrf))
	delete(hdrf);
end
if (exist(ifhf))
	delete(ifhf);
end

voxels = 48*64*48;
frames = prod(size(data))/voxels;
[fifh message] = fopen(ifhf,'w');
if fifh == -1
    error('\n\nERROR: Could not open %s for saving. Please check your paths!\n\nMatlab message: %s', file, message);
end

fprintf(fifh, 'INTERFILE	:=\n');
fprintf(fifh, 'version of keys	:= 3.3\n');
fprintf(fifh, 'number format	:= float\n');
fprintf(fifh, 'number of bytes per pixel	:= 4\n');
fprintf(fifh, 'imagedata byte order	:= bigendian\n');
fprintf(fifh, 'orientation		:= 2\n');
fprintf(fifh, 'number of dimensions	:= 4\n');
fprintf(fifh, 'matrix size [1]	:= 48\n');
fprintf(fifh, 'matrix size [2]	:= 64\n');
fprintf(fifh, 'matrix size [3]	:= 48\n');
fprintf(fifh, 'matrix size [4]	:= %d\n', frames);
fprintf(fifh, 'scaling factor (mm/pixel) [1]	:= 3.000000\n');
fprintf(fifh, 'scaling factor (mm/pixel) [2]	:= 3.000000\n');
fprintf(fifh, 'scaling factor (mm/pixel) [3]	:= 3.000000\n');
fprintf(fifh, 'mmppix	:=   3.000000 -3.000000 -3.000000\n');
fprintf(fifh, 'center	:=    73.5000  -87.0000  -84.0000\n');

for n = 1:length(extra)
	fprintf(fifh, '%s	:= %s\n', char(extra(n).key), char(extra(n).value));
end

fclose(fifh);
