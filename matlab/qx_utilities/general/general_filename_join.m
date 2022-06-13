function [filename] = general_filename_join(elements, delim)

%``function [filename] = general_filename_join(elements, delim)``
%
%   Joins all the elements of a file with the specified delimiter.
%
%   Parameters:
%       --elements (cell array):
%           Cell array of file name elements.
%       --delim (str, default '_'):
%           Delimiter to use for concatenation.
%
%   Returns:
%       filename
%           The generated filename.
%
%   Example:
%       The example below will result in 'bold1_s_hpss'::
%
%           filename = general_filename_join({'bold1', 's', 'hpss'});
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2, delim = '_'; end

items = length(elements);

filename = elements{1};
for n = 2:items
    filename = [filename delim elements{n}];
end
