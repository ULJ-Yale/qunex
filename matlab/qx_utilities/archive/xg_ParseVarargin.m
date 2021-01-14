function [options] = g_ParseVarargin(options, vars, fields)

%function [options] = g_ParseVarargin(options, vars, fields)
%
%   Function for parsing variable number of input variables
%
%   Input
%       - options   : a starting structure to work with - everything will be added to it / changed in it
%       - vars      : a cell array of values
%       - fields    : a comma separated string of field names in the order of cell array
%
%   Output
%       - options   : a structure with the embedded values
%
%
%   Written by Grega Repovs, 2014-07-22

if nargin < 3, error('ERROR: Not enough arguments passed to g_ParseVarargin!'); end

fields  = regexp(fields, ',', 'split');
nfields = length(fields);
nvars   = length(vars);

if nfields < nvars
    error('ERROR: More variables than fields! (g_ParseVarargin)!');
end

for n = 1:nfields
    k = strtrim(fields{n});
    if n > nvars
        options = setfield(options, k, []);
    else
        options = setfield(options, k, vars{n});
    end
end

