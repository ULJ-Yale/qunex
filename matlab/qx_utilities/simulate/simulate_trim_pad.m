function [ts] = simulate_trim_pad(ts, l)

%``simulate_trim_pad(ts, l)``
%    
%   Function that trims or pads timeseries to specified length.
%
%   Parameters:
%       --ts (timeseries):
%           Timeseries (timepoints x voxels).
%
%       --l (int):
%           Desired length.
%
%   Returns:
%       ts
%           Trimmed / padded timeseries.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2
    error('ERROR: not enough parameters to trim or pad the timeseries!');
end

tlen = size(ts,1);

if tlen > l
    ts = ts(1:l,:);
elseif tlen < l
    ts = [ts; zeros(l-tlen, size(ts,2))];
end

