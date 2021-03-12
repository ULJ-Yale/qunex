function [s] = strjoin(list, delim)

%``function [s] = strjoin(list, delim)``
%
%   Joins array of string cells into a single string using the provided
%   delimiter.
%
%   INPUTS
%	======
%
%   --list  	a cell array of strings to be joined
%   --delim 	delimiter between strings
%
%   OUTPUT
%	======
%
%   s
%		joined string
%

if nargin < 2 || isempty(delim), delim = ' '; end

s = list{1};
slength = length(list);
if slength > 1
    for n = 2:slength
        s = [s delim list{n}];
    end
end
