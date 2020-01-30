function [filename] = g_FilenameJoin(elements, delim)

%function [filename] = g_FilenameJoin(elements, delim)
%
%   Joins all the elements of a file with the specified delimiter.
%
%   INPUT
%       - elements ... Cell array of file name elements.
%       - delim    ... Delimiter to use for concatenation. ['_']
%
%   OUTPUT
%       - filename ... The generated filename
%
%   EXAMPLE
%
%   filename = g_FilenameJoin({'bold1', 's', 'hpss'});
%
%   will result in 'bold1_s_hpss'
%
%   ---
%   Written by Grega Repovš
%
%   Changelog
%             2017-02-11 Grega Repovš - Updated documentation


if nargin < 2, delim = '_'; end

items = length(elements);

filename = elements{1};
for n = 2:items
	filename = [filename delim elements{n}];
end
