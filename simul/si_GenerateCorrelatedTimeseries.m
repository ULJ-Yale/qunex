function [ts, er, dr] = si_GenerateCorrelatedTimeseries(r, len, md)

%	function [ts, er, dr] = si_GenerateCorrelatedTimeseries(r, len, md)
%	
%   Function that generates multi normal timeseries with specified correlations
%
%   Inputs
%       - r     correlation matrix
%       - l     desired timeseries length
%       - md    maximal allowed difference between desired and actual correlation
%
%   Outputs
%       - ts    generated timeseries
%       - r     actual correlations
%       - dr    maximal difference between desired and actual correlation
%	
% 	Created by Grega Repovš on 2010-10-09.
%	

if nargin < 3
    md = [];
    if nargin < 2
        error('ERROR: Not enough parameters to generate timeseries!');
    end
end

er = [];

% --- generate timeseries

nVar = size(r, 1);
ts   = randn(len, nVar);
C    = chol(r);
ts   = ts * C;

if ~isempty(md)
    er = corr(ts);
    dr = max(abs(changeform(er) - changeform(r)));
    if dr > md;
        [ts, er, dr] = si_GenerateCorrelatedTimeseries(r, len, md);
    end
end

if nargout > 1 & ~er
    er = corr(ts);
    if nargout > 2
        dr = max(abs(changeform(er) - changeform(r)));
    end
end

