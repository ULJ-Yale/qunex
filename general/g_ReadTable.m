function [data, hdr] = g_ReadTable(filename)

%function [data, hdr] = g_ReadTable(filename)
%
%   A general function for reading whitespace separated data tables.
%
%   input
%       - filename  the path to the file
%
%   output
%       - hdr       cell array of strings with column names
%       - data      data matrix
%
%    Whipped together by Grega Repovs, 2014-07-18

hdr  = {};
data = [];

fin = fopen(filename, 'r');
while ~feof(fin)

    s = strtrim(fgetl(fin));

    % --- if empty get the next line
    if length(s) == 0, continue, end

    % --- if characters in line and no data yet, read header, remove first #
    if max(isstrprop(s, 'alpha')) && isempty(data)
        if s(1) == '#', s = s(2:end); end
        hdr = strread(s, '%s');

    % --- otherwise, if not a hashed line, read values
    elseif s(1) ~= '#'
        data = [data; strread(s)];
    end
end

fclose(fin);
