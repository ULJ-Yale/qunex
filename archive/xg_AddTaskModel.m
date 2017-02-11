function [m] = g_AddTaskModel(m, code, hrf_type, len)

%   
%   Adds settings to an array of model structures
%   
%   INPUT
%     - m - an existing model structure or an empty array
%     - code - event codes (used in fidl file) [0] default
%     - hrf_type 
%       -> 'boynton' (assumed response) 
%       -> 'SPM' (assumed response) [default]
%       -> 'u' (unassumed response)
%     - len
%       - number of frames to model (for unasumed response)
%       - length of event in s (for assumed response - if empty, duration is taken from event file) [default]
%
%   OUTPUT
%   - m - new model array
%
%   Grega Repovš - 2008.7.16
%

if nargin < 4
    len = [];
    if nargin < 3
        hrf_type = 'SPM';
        if nargin < 2
            code = 0;
            if nargin < 1
                m = [];
            end
        end
    end
end

n = length(m)+1;

m(n).code = code;
m(n).hrf_type = hrf_type;
m(n).length = len;


