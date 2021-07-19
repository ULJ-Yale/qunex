% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [] = general_print_struct(info, ftitle);

%``function [] = general_print_struct(info, ftitle)``
%
%   Function for printing the content of a struct field
%
%   INPUTS
%   ======
%
%   --info      a structure to print
%   --ftitle    a title to print above the report
%

if nargin < 2 || isempty(ftitle), ftitle = ''; end

if ~isstruct(info)
    error('\nERROR: The variable passed to general_print_struct is not a structure!');
end

nrecords = length(info);
names    = fieldnames(info);
nfields  = length(names);

% --- get the maximum field name length

nameLength = 0;
for name = names'
    nameLength = max([nameLength length(name{1})]);
end
nameLength = nameLength + 1;
nameStr = sprintf('%%+%ds', nameLength);

% --- loop through records

fprintf('\n%s:', ftitle);

for r = 1:nrecords
    fprintf('\n%s', repmat('-', 1, max(nameLength, length(ftitle))));
    for name = names'
        name = name{1};
        lineStr = sprintf(nameStr, name);
        value = getfield(info(r), name);

        switch class(value)
        case 'char'
            valueStr = value;
        case {'single', 'double'}
            valueStr = num2str(value);
        case 'logical'
            if value
                valueStr = 'true';
            else
                valueStr = 'false';
            end
        case 'struct'
            vnames = fieldnames(value);
            valueStr = sprintf('[a struct with fields: %s]', strjoin(vnames, ', '));
        case 'cell'
            if iscellstr(value)
                valueStr = sprintf('{%s}', strjoin(value, ', '));
            else
                valueStr = '[a cell array]';
            end
        otherwise
            valueStr = '[non-supported value type]'
        end
        fprintf('\n%s: %s', lineStr, valueStr);
    end
end
fprintf('\n');







