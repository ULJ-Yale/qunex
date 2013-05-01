function [img] = g_Read4DFPn(file, n, dtype)

%
%		Reads in n frames of a 4dfp image and returns a voxels by frames matrix.
%

if nargin < 3
	dtype = 'double';
end

[fim message] = fopen(file, 'r', 'b');
if fim == -1
    error('\n\nERROR: Could not open %s for reading. Please check your paths!\n\nMatlab message: %s', file, message);
end
img = fread(fim, [147456, n], ['float32=>' dtype]);
fclose(fim);

