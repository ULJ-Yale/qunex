function x = g_ReadMovData(file)

%    Reads movement correction data
%
%
%    Created by Grega Repovs, November 1st 2009


x = [];

fin = fopen(file, 'r');
s = fgetl(fin);
s = fgetl(fin);

while isempty(strfind(s, '#mean'))
	line = strread(s);
	x = [x; line(2:7)];
	s = fgetl(fin);
end
fclose(fin);
