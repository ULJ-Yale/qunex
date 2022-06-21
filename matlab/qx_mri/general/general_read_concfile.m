function [files] = general_read_concfile(file)

%``function [files] = general_read_concfile(file)``
%
%	Reads a conc file and returns a list of files.
%
%	INPUT
%	=====
%
%	--file 	a conc file
%
%	OUTPUT
%	======
%
%	files
%		list of paths
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

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
