function [elements] = g_FilenameSplit(filename, delim)

%function [elements] = g_FilenameSplit(filename, delim)
%
%   Splits the filename into elements separated by delim
%
%   INPUT
%       - filename  ... The filename to be split.
%       - delim     ... The delimiter to be used.
%
%   OUTPUT
%       - elements  ... Cell array of file elements excluding extension.
%
%   EXAMPLE
%
%   elements = g_FilenameSplit('bold3_s_hpss.nii.gz');
%
%   will result in elements = {'bold3', 's', 'hpss'}
%
%   ---
%   Written by Grega Repovš
%
%   Changelog
%             2017-02-11 Grega Repovš - Updated documentation

if nargin < 2, delim = '_'; end

[t, r] = strtok(filename, '.');

items = sum(ismember(t, delim));

for n = 1:items
	[elements{n}, r] = strtok(t, delim);
	t = r(2:end);
end
elements{items+1} = t;

