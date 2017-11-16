function [s] = g_WriteTable(filename, data, hdr, extra, sform, sep, pre, post)

%function [s] = g_WriteTable(filename, data, hdr, extra, sform, sep, pre, post)
%
%   A general function for writing data tables.
%
%   INPUT
%       - filename  : The path to the file ['']
%       - data      : The data matrix to be saved.
%       - hdr       : Optional header (cell array of strings or a list of columns) [].
%       - extra     : Optional summary rows to be added at the end (e.g. 'mean|sd|min|max|%|sum') [].
%       - sform     : Format string for the header, first data column, rest of the data columns and extra row names ['%s|%d|%.5f|%s'].
%       - sep       : Separator (default '\t').
%       - pre       : Optional text to prepend before the header.
%       - post      : Optional text to append at the end of the file.
%
%   OUTPUT
%       - s         : a formated text string
%
%   USE
%   The function is used to save the data to a text file (if a path / filename
%   is provided) and/or generate a formulated string. The data should be a
%   matrix of values, the header either a cell array of strings or a comma,
%   semicolon, space or pipe separated string. If '#" commented summary rows
%   should be added at the end of the file, the specific summaries should be
%   specified in the extra parameter as a pipe separated list.
%
%   To specify how values are to be formated, an optional sform string can be
%   provided. How the data is separated is specified in the sep parameter.
%   Optional strings to be prepended or appended to the file can be specified
%   as the pre and post parameters.
%
%   EXAMPLE USE
%   g_WriteTable('mov.dat', movdata, 'frame,X,Y,Z', 'mean,sd,min,max');
%
%
%   ---
%   Written by Grega Repovs, 2014-07-18
%
%   Changelog
%   2016-02-05 Grega Repovs ... Added pre and post options
%   2016-08-18 Grega Repovs ... Added printing to string
%   2017-03-19 Grega Repovs ... Updated documentation
%

if nargin < 8                    post  = [];                end
if nargin < 7                    pre   = [];                end
if nargin < 6 || isempty(sep),   sep   = '\t';              end
if nargin < 5 || isempty(sform), sform = '%s|%d|%.5g|%s';   end
if nargin < 4,                   extra = [];                end
if nargin < 3,                   hdr   = {};                end

sform = regexp(sform, '|,|;| |\|', 'split');

if ~isempty(extra)
    extra = regexp(extra, '|,|;| |\|', 'split');
end

if ~isempty(hdr) && isa(hdr, 'char')
    hdr = regexp(sform, '|,|;| |\|', 'split');
end

s = '';
sep = sprintf(sep);
nl  = sprintf('\n');

% --- is there a pre

if ~isempty(pre)
    s = [s pre nl];
end


% --- write header

if ~isempty(hdr)
    for n = 1:length(hdr)
        if n > 1
            s = [s sep];
        end
        s = [s sprintf(sform{1}, hdr{n})];
    end
end

% --- write data
if ~isempty(data)
    for n = 1:size(data, 1)
        s = [s sprintf(['\n' sform{2}], data(n,1))];
        s = [s sprintf([sep sform{3}], data(n,2:end))];
    end
end

% --- write optional summary

for ex = extra
    ex = ex{1};
    sf = strrep(sform{3}, 'd', 'g');

    s = [s sprintf(['\n#' sform{4}], ex)];
    switch ex
    case 'mean'
        s = [s sprintf([sep sf], mean(data(:,2:end)))];
    case 'min'
        s = [s sprintf([sep sform{3}], min(data(:,2:end)))];
    case 'max'
        s = [s sprintf([sep sform{3}], max(data(:,2:end)))];
    case 'sd'
        s = [s sprintf([sep sf], std(data(:,2:end)))];
    case 'sum'
        s = [s sprintf([sep sform{3}], sum(data(:,2:end)))];
    case '%'
        s = [s sprintf([sep sf], sum(data(:,2:end))./size(data,1).*100)];
    end
end

% --- is there a post

if ~isempty(post)
    s = [s nl, post];
end


% --- are we writing to file

if ~isempty(filename)
    fout = fopen(filename, 'w');
    fprintf(fout, s);
    fclose(fout);
end
