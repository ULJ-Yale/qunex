function [files] = g_ReadConcFile(file)

%function [files] = g_ReadConcFile(file)
%
%	Reads a conc file and returns a list of files
%
%	files - list of paths
%
%   ----
%   Written by Grega Repovš

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
		f = strrep(f{1}, 'file:', '');
		files{c} = f;
		c = c + 1;
	end
end

fclose(fin);