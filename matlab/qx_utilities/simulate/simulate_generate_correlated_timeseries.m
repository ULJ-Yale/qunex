function [ts, er, dr] = simulate_generate_correlated_timeseries(r, len, md)

%``function [ts, er, dr] = simulate_generate_correlated_timeseries(r, len, md)``
%    
%   Function that generates multi normal timeseries with specified
%   correlations.
%
%   Parameters:
%       --r (matrix):
%           Correlation matrix.
%       --len (int):
%           Desired timeseries length.
%       --md (float, default []):
%           Maximal allowed difference between desired and actual
%           correlation.
%
%   Returns:
%       ts
%           Generated timeseries.
%       r
%           Actual correlations.
%       dr
%           Maximal difference between desired and actual correlation.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 3
    md = [];
    if nargin < 2
        error('ERROR: Not enough parameters to generate timeseries!');
    end
end

er = [];

% --- generate timeseries

doIt   = true;
nVar = size(r, 1);
c    = 0;

while doIt 
    c    = c+1;
    ts   = randn(len, nVar);
    C    = chol(r);
    ts   = ts * C;
    doIt   = false;
    
    if ~isempty(md)
        er = corr(ts);
        dr = max(abs(changeform(er) - changeform(r)));
        if dr > md;
            doIt = true;
            if c > 10000
                error('ERROR: Could not generate timeseries even after 10000 atempts. Consider increasing acceptability threshold.');
            end
        end
    end
end

if nargout > 1 & ~er
    er = corr(ts);
    if nargout > 2
        dr = max(abs(changeform(er) - changeform(r)));
    end
end
