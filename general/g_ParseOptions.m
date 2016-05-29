function [options] = g_ParseOptions(options, s, default)

%function [options] = g_ParseOptions(options, s, default)
%
%   Function for parsing compact passing of values between functions.
%
%   Input
%       - options   : a starting structure to work with - everythng will be added to it / changed in it
%       - s         : the input string to be injected into the structure
%       - default   : the string with the default values to be used
%
%   Output
%       - options   : a structure with the embedded values
%
%
%   Written by Grega Repovs, 2014-07-22
%
%   ====== Change Log ======
%
%   Grega Repovs, 2015-10-17
%   - updated to enable structure arrays and specification of single layer depth structures
%


if nargin < 3, default = ''; end
if nargin < 2, error('ERROR: Not enough arguments passed to g_ParseOptions!'); end

if ~isempty(default)
    options = matchLength(options, default);
end

if ~isempty(s)
    options = matchLength(options, s);
end


function [options] = matchLength(options, s)
    s = regexp(s, ';', 'split');
    if length(options) == length(s)
        for n = 1:length(s)
            options(n) = parseString(options, s{n});
        end
    elseif isempty(options)
        for n = 1:length(s)
            options(n) = parseString(options, s{n});
        end
    elseif length(options) == 1;
        t = options;
        for n = 1:length(s)
            options(n) = g_ParseOptions(t, s{n});
        end
    elseif length(s) == 1
        for n = 1:length(options)
            options(n) = parseString(options, s{1});
        end
    else
        error('ERROR: Length of existing structure and given specification do not match: %d vs. %d!', length(options), length(s));
    end


function [options] = parseString(options, s)

    s = strrep(s, '"', '''');
    t = regexp(s, '\|', 'split');

    for n = 1:length(t)
        if isempty(strfind(t{n}, '>'))
            f = regexp(t{n}, '=', 'split');
            if length(f) ~= 2
                error('ERROR: Could not parse token! [%s]', t{n});
            end
            options = setfield(options, f{1}, getValue(f{2}));
        else
            f = regexp(t{n}, '>', 'split');
            for k = 2:length(f)
                it = regexp(f{k}, ',', 'split');
                for ni = 1:length(it)
                    et = regexp(it{ni}, '=', 'split');
                    if length(et) ~= 2
                        error('ERROR: Could not parse token! [%s]', t{n});
                    end
                    ft(k-1).(et{1}) = getValue(et{2});
                end
            end
            options = setfield(options, f{1}, ft);
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