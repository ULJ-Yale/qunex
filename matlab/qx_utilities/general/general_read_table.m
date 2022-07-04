function [data, hdr, meta] = general_read_table(instr)

%``general_read_table(instr)``
%
%   A general function for reading whitespace separated data tables.
%
%   Parameters:
%       --instr (str):
%           Either a path to file or a multiline string to parse.
%
%   Returns:
%       data
%           A data matrix with file contents.
%       hdr
%           Cell array of strings with column names.
%       meta
%           A structure with metadata specified in the string.
%
%   Notes:
%       The function is used to read a text file or convert a text string
%       into a data matrix. All the # commented lines are excluded from
%       reading the data. Comment lines in the form of '# key: value' are
%       added to the meta structure that has fields with key names and
%       values ascribed to them. The last commented line that is not a
%       '# key: value' line is considered a white-character separated
%       header.
%
%   Example:
%       ::
%
%           [data, hdr, meta] = general_read_table('movement.dat');
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

hdr  = {};
data = [];
meta = [];

instr = instr(:)';
if isempty(regexp(instr, '\n', 'once'))
    instr = fileread(instr);
end

lines = strsplit(instr, '\n', 'CollapseDelimiters', false);

header = true;
l = 0;
while header && length(lines) > l
    l = l + 1;
    s = lines{l};

    % --- if empty get the next line
    if length(s) == 0, continue, end

    % --- if characters excluding "e" in line and no data yet, read header, remove first #
    if max(isstrprop(strrep(s, 'e', ''), 'alpha')) && isempty(data)
        if s(1) == '#', s = s(2:end); end
        if strfind(s, ':')
            [fname, fdata] = strtok(s, ':');
            meta.(validName(fname)) = strtrim(fdata(2:end));
        else
            hdr = strread(s, '%s')';
        end

    % --- otherwise, if not a hashed line, read values
    elseif s(1) ~= '#'
        nc = length(strread(s, '%s'));
        header = false;
    end
end

if ~header
    data = textscan(instr, '%f', 'CommentStyle', '#', 'HeaderLines', l-1);
    data = data{1};
    data = reshape(data, nc, [])';

    if nc == 1 + length(hdr)
        hdr = ['id', hdr];
    end
else
    data = [];
end


% ----- function for making valid field names

function [s] = validName(s)

    s = strtrim(s);
    s = s(isstrprop(s, 'alphanum'));
    s = s(find(~isstrprop(s, 'digit'), 1, 'first'):end);
