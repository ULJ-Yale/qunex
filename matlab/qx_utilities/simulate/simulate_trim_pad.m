% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [ts] = simulate_trim_pad(ts,l)

%``function [ts] = simulate_trim_pad(ts,l)``
%	
%   Function that trimms or pads timeseries to specified length.
%
%   INPUTS
%	======
%
%   --ts	timeseries (timepoints x voxels)
%   --l  	desired length
%
%   OUTPUT
%	======
%
%   ts
%		trimmed / padded timeseries
%

if nargin < 2
    error('ERROR: not enough parameters to trim or pad the timeseries!');
end

tlen = size(ts,1);

if tlen > l
    ts = ts(1:l,:);
elseif tlen < l
    ts = [ts; zeros(l-tlen, size(ts,2))];
end

