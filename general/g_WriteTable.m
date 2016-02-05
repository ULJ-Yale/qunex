function [] = g_WriteTable(filename, data, hdr, extra, sform, sep, pre, post)

%function [] = g_WriteTable(filename, data, hdr, extra, sform, sep, pre, post)
%
%   A general function for writing data tables.
%
%   input
%       - filename  : the path to the file
%       - data      : data matrix to be saved
%       - hdr       : optional header (cell array of strings or a list of columns)
%       - extra     : optional summary rows to be added at the end (e.g. 'mean|sd|min|max|%|sum')
%       - sform     : optional format string for header, first data column, rest of the data columns and extra row names (e.g. '%s|%d|%.5f|%s')
%       - sep       : optional separator (default '\t')
%       - pre       : optional text to prepend before the header
%       - post      : optional text to append at the end of the file
%
%    Whipped together by Grega Repovs, 2014-07-18
%
%    2016.02.05 Grega Repovs ... Added pre and post options
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

% --- start writing!

fout = fopen(filename, 'w');

% --- is there a pre

if ~isempty(pre)
    fprintf(fout, '%s\n', pre);
end


% --- write header

if ~isempty(hdr)
    for n = 1:length(hdr)
        if n > 1
            fprintf(fout, sep);
        end
        fprintf(fout, sform{1}, hdr{n});
    end
end

% --- write data

for n = 1:size(data, 1)
    fprintf(fout, ['\n' sform{2}], data(n,1));
    fprintf(fout, [sep sform{3}], data(n,2:end));
end

% --- write optional summary

for ex = extra
    ex = ex{1};
    sf = strrep(sform{3}, 'd', 'g');

    fprintf(fout, ['\n#' sform{4}], ex);
    switch ex
    case 'mean'
        fprintf(fout, [sep sf], mean(data(:,2:end)));
    case 'min'
        fprintf(fout, [sep sform{3}], min(data(:,2:end)));
    case 'max'
        fprintf(fout, [sep sform{3}], max(data(:,2:end)));
    case 'sd'
        fprintf(fout, [sep sf], std(data(:,2:end)));
    case 'sum'
        fprintf(fout, [sep sform{3}], sum(data(:,2:end)));
    case '%'
        fprintf(fout, [sep sf], sum(data(:,2:end))./size(data,1).*100);
    end
end

% --- is there a post

if ~isempty(post)
    fprintf(fout, '\n%s', post);
end




fclose(fout);
