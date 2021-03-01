function [filename] = general_filename_join(elements, delim)

%``function [filename] = general_filename_join(elements, delim)`
%
%   Joins all the elements of a file with the specified delimiter.
%
%   INPUTS
%	======
%
%   --elements 	Cell array of file name elements.
%   --delim    	Delimiter to use for concatenation. ['_']
%
%   OUTPUT
%	======
%
%   filename
%		The generated filename
%
%   EXAMPLE
%	=======
%
%   ::
%
%		filename = general_filename_join({'bold1', 's', 'hpss'});
%
%   will result in 'bold1_s_hpss'
%

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
%   2017-02-11 Grega Repovš - Updated documentation


if nargin < 2, delim = '_'; end

items = length(elements);

filename = elements{1};
for n = 2:items
	filename = [filename delim elements{n}];
end
