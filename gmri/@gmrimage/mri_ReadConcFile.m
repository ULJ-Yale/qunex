function [files] = mri_ReadConcFile(file)

%function [files] = mri_ReadConcFile(file)
%
%	Reads a .conc file and returns a list of files.
%
%   INPUT
%       file  ... a path to the conc file
%
%   OUTPUT
%       files ... a cell array of file paths specified in the .conc file.
%
%   USE
%   Use the method to get the list of files specified in the conc file.
%
%   EXAMPLE USE
%	>>> files = gmrimage.mri_ReadConcFile('OP236-WM.conc');
%
%   ---
%	Written by Grega Repovs
%
%   Changelog
%   2017-03-11 Grega Repovs
%            - Updated documentation.

file = strtrim(file);

[fin message] = fopen(file);
if fin == -1
    error('\n\nERROR: Could not open %s for reading. Please check your paths!\n\nMatlab message: %s', file, message);
end
s = fgetl(fin);

files 	= {};
c = 1;
while feof(fin) == 0
	s = fgetl(fin);
	if findstr(s, 'file:')
		[f] = strread(s, '%s');
		f = strtrim(strrep(f{1}, 'file:', ''));
		files{c} = f;
		c = c + 1;
	end
end

fclose(fin);