function [elements] = general_filename_split(filename, delim)

%``general_filename_split(filename, delim)``
%
%   Splits the filename into elements separated by delim.
%
%   Parameters:
%       --filename (str):
%           The filename to be split.
%
%       --delim (str, default '_'):
%           The delimiter to be used.
%
%   Returns:
%       elements
%           Cell array of file elements excluding extension.
%
%   Example:
%       Example below will result in `elements = {'bold3', 's', 'hpss'}`::
%
%           elements = general_filename_split('bold3_s_hpss.nii.gz');
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2, delim = '_'; end

[t, r] = strtok(filename, '.');

items = sum(ismember(t, delim));

for n = 1:items
    [elements{n}, r] = strtok(t, delim);
    t = r(2:end);
end
elements{items+1} = t;

