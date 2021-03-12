function [elements] = general_filename_split(filename, delim)

%``function [elements] = general_filename_split(filename, delim)``
%
%   Splits the filename into elements separated by delim.
%
%   INPUTS
%	======
%   
%	--filename  	The filename to be split.
%   --delim     	The delimiter to be used.
%
%   OUTPUT
%	======
%   
%	elements
%		Cell array of file elements excluding extension.
%
%   EXAMPLE
%	=======
%
%	::
%
%   	elements = general_filename_split('bold3_s_hpss.nii.gz');
%
%   will result in `elements = {'bold3', 's', 'hpss'}`.
%

if nargin < 2, delim = '_'; end

[t, r] = strtok(filename, '.');

items = sum(ismember(t, delim));

for n = 1:items
	[elements{n}, r] = strtok(t, delim);
	t = r(2:end);
end
elements{items+1} = t;

