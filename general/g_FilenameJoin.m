function [filename] = g_FilenameJoin(elements, delim)

%
%		reads in a 4dfp image and returns a vector with all the voxels
%

if nargin < 2
	delim = '_';
end

items = length(elements);

filename = elements{1};
for n = 2:items
	filename = [filename delim elements{n}];
end
