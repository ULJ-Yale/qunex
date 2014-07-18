function [] = g_WriteTable(filename, data, hdr, extra, sform, sep)

%function [] = g_WriteTable(filename, data, hdr, extra, sform, sep)
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
%
%    Whipped together by Grega Repovs, 2014-07-18

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

fclose(fout);
