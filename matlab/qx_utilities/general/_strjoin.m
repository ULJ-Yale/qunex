function [s] = _strjoin(list, delim)

%``_strjoin(list, delim)``
%
%   Joins array of string cells into a single string using the provided
%   delimiter.
%
%   Parameters:
%       --list (cell):
%           A cell array of strings to be joined.
%
%       --delim (str, default ' '):
%           Delimiter between strings.
%
%   Returns:
%       s
%           Joined string.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2 || isempty(delim), delim = ' '; end

if isempty(list)
    s = '';
else
    s = list{1};
    slength = length(list);
    if slength > 1
        for n = 2:slength
            s = [s delim list{n}];
        end
    end
end
