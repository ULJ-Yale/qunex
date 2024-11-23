function [options] = general_parse_options(options, s, default)

%``general_parse_options(options, s, default)``
%
%   Function for compact passing of values between functions.
%
%   Parameters:
%       --options (struct):
%           A starting structure to work with - everything will be added to 
%           it / changed in it.
%
%       --s (str):
%           A 'key:value|key:value' string that defines what values to be 
%           injected into the structure.
%
%       --default (str, default ''):
%           An optional 'key:value|key:value' string with the default
%           values to be used.
%
%   Returns:
%       options
%           A structure with the embedded values.
%
%   Notes:
%       Use the function for easy creation and modification of structures
%       that can enable passing of options from function to function.
%
%       Starting structure:
%           The starting structure can hold the initial values. Any
%           value not changed by the string will remain as is. Any
%           field name not yet existing will becreated. If an empty
%           array is passed, the structure will be created anew.
%
%       String format:
%           The string defines key:value pairs that will be embedded in
%           the structure. Keys will be the field names and values will
%           be assigned to them. So::
%
%               a = general_parse_options([], 'id:66|name:Tom');
%
%           will result in a structure::
%
%               a.id   = 66
%               a.name = 'Tom'
%
%           Notice that strings are not embedded in quotes.
%
%       Structure arrays:
%           The function can generate or edit arrays of structures. To
%           specify key-value pairs for multiple sets, separate them
%           using semicolon::
%
%               a = general_parse_options([], ...
%               'id:66|name:Tom;id=33|name=Mary');
%
%           will result in a structure::
%
%               a(1).id   = 66
%               a(1).name = 'Tom'
%               a(2).id   = 33
%               a(2).name = 'Mary'
%
%           Notice that key-value pairs can be separate either using
%           colon or equal so 'id:66' works the same as 'id=66'.
%
%       Creation of substructures:
%           It is also possible to populate fields with structures. In
%           this case, use greater than sign to specify that the filed
%           contains a substructure and use a comma to separate
%           key-value pairs of the substructure::
%
%               a = general_parse_options([], ...
%               'id:66|name:Tom|demographics>age:37,sex:male');
%
%           will result in a structure::
%
%               a.id    = 66
%               a.name  = 'Tom'
%               a.demographics.age = 37
%               a.demographics.sex = 'male'
%
%       Default structure:
%           It is possible to define a default structure. In this case
%           the default strucutre will be generated first and then
%           overwritten by the specification string::
%
%               a = general_parse_options([], ...
%               'id:66|name:Tom;id=33|name=Mary', 'status:ok|id=0');
%
%           will result in a structure::
%
%               a(1).status = 'ok'
%               a(1).id     = 66
%               a(1).name   = 'Tom'
%               a(2).status = 'ok'
%               a(2).id     = 33
%               a(2).name   = 'Mary'
%
%       Valid values:
%           Values can be numbers, strings or any other valid
%           expression, also arrays and cell arrays, just be aware that
%           strings for the cell array need to be specifed using
%           regular double quotes::
%
%               a = general_parse_options([], ...
%               'id:66|name=Tom|vars={"a", "b", "c"}|values=[1, 2, 3]');
%
%           will result in a structure::
%
%               a.id     = 66
%               a.name   = 'Tom'
%               a.vars   = {'a', 'b', 'c'}
%               a.values = [1, 2, 3]
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 3, default = ''; end
if nargin < 2, error('ERROR: Not enough arguments passed to general_parse_options!'); end

if ~isempty(default)
    if ischar(default)
        options = matchLength(options, default);
    elseif isstruct(default)
        options = matchLengthStruct(options, default);
    else
        error('ERROR: Default is neither a string or a struct!')
    end
end

if ~isempty(s)
    if ischar(s)
        options = matchLength(options, s);
    elseif isstruct(s)
        options = matchLengthStruct(options, s);
    else
        error('ERROR: Default is neither a string or a struct!')
    end     
end

% --- Support functions for struct inputs

function [options] = matchLengthStruct(options, s)
    if length(options) == length(s)
        for n = 1:length(s)
            options = parseStruct(options, s(n), n);
        end
    elseif isempty(options)
        options = s;
    elseif length(options) == 1;
        for n = 1:length(s)
            options = parseStruct(options, s(n), n);
        end
    elseif length(s) == 1
        for n = 1:length(options)
            options = parseStruct(options, s, n);
        end
    else
        error('ERROR: Length of existing structure [%d] and given structure [%s] do not match!', length(options), length(s));
    end


function [options] = parseStruct(options, s, fn)
    fields = fieldnames(s);
    for n = 1:length(fields)
        if isfield(options(fn), fields{n}) && isstruct(s.(fields{n})) && isstruct(options(fn).(fields{n}))
            options(fn).(fields{n}) = matchLengthStruct(options(fn).(fields{n}), s.(fields{n}));            
        else
            options(fn).(fields{n}) = s.(fields{n});
        end
    end

% --- Support functions for string inputs

function [options] = matchLength(options, s)
    s = strtrim(regexp(s, ';', 'split'));
    if length(options) == length(s)
        for n = 1:length(s)
            options = parseString(options, s{n}, n);
        end
    elseif isempty(options)
        for n = 1:length(s)
            options = parseString(options, s{n}, n);
        end
    elseif length(options) == 1;
        for n = 1:length(s)
            options = parseString(options, s{n}, n);
        end
    elseif length(s) == 1
        for n = 1:length(options)
            options = parseString(options, s{1}, n);
        end
    else
        error('ERROR: Length of existing structure and given specification do not match: %d vs. %d!', length(options), length(s));
    end


function [options] = parseString(options, s, fn)

    s = strrep(s, '"', '''');
    t = regexp(s, '\|', 'split');

    for n = 1:length(t)
        if isempty(strfind(t{n}, '>'))
            f = strtrim(regexp(t{n}, '=|:', 'split'));
            if length(f) ~= 2
                error('ERROR: Could not parse token! [%s]', t{n});
            end
            options(fn).(f{1}) = getValue(f{2});
        else
            f = strtrim(regexp(t{n}, '>', 'split'));
            for k = 2:length(f)
                it = strtrim(regexp(f{k}, ',', 'split'));
                for ni = 1:length(it)
                    et = strtrim(regexp(it{ni}, '=|:', 'split'));
                    if length(et) ~= 2
                        error('ERROR: Could not parse token! [%s]', t{n});
                    end
                    ft(k-1).(et{1}) = getValue(et{2});
                end
            end
            options(fn).(f{1}) = ft;
        end
    end



function [v] = getValue(v)

    if isempty(regexp(v, '^-?[\d\.]+$'))
        if length(v)>1 && ismember(v(1), {'{', '['})
            v = eval(v);
        end
    else
        v = str2num(v);
    end
