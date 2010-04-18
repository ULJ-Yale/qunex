function [elements] = g_FilenameSplit(t, delim)

%
%		reads in a 4dfp image and returns a vector with all the voxels
%

if nargin < 2
	delim = '_';
end

[t, r] = strtok(t, '.');

items = sum(ismember(t, delim));

for n = 1:items
	[elements{n}, r] = strtok(t, delim);
	t = r(2:end);
end
elements{items+1} = t;

