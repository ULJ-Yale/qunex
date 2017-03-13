function [data, hdr, meta] = g_ReadTable(instr)

%function [data, hdr, meta] = g_ReadTable(instr)
%
%   A general function for reading whitespace separated data tables.
%
%   input
%       - instr     either a path to file or a multiline string to parse
%
%   output
%       - hdr       cell array of strings with column names
%       - data      data matrix
%
%   ---
%   Written by Grega Repovs, 2014-07-18
%
%   Changelog
%   2016-08-18 Grega Repovs - Adapted to work with strings
%


hdr  = {};
data = [];
meta = [];
l    = 0;

instr = instr(:)';
if isempty(regexp(instr, '\n', 'once'))
    instr = fileread(instr);
end

lines = textscan(instr, '%s', 'delimiter', '\n');
lines = lines{1};

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