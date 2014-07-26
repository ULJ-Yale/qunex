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

if nargin < 3, default = ''; end
if nargin < 2, error('ERROR: Not enough arguments passed to g_ParseOptions!'); end

if ~isempty(default)
    options = parseString(options, default);
end
if ~isempty(s)
    options = parseString(options, s);
end


function [options] = parseString(options, s)

    s = strrep(s, '"', '''');
    s = regexp(s, '=|\|', 'split');

    if mod(length(s),2)
        error('ERROR: Options string content not divisible by 2!');
    end

    if length(s)>=2
        s = reshape(s, 2, [])';
        for p = 1:size(s, 1)
            k = strtrim(s{p,1});
            v = strtrim(s{p,2});
            if isempty(regexp(v, '^-?[\d\.]+$'))
                if length(v)>1 && ismember(v(1), {'{', '['})
                    options = setfield(options, k, eval(v));
                else
                    options = setfield(options, k, v);
                end
            else
                options = setfield(options, k, str2num(v));
            end
        end
    end