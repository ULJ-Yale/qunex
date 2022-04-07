function [ts] = general_normalize_timeseries(ts)

%``function [ts] = general_normalize_timeseries(ts)``
%
%   This function normalizes timeseries to range 1, mean 0.
%   It works along columns.
%
%   Parameters:
%       --ts (timeseries):
%           Timeseries (time x regions/voxels).
%
%   Returns:
%       ts
%           Normalized timeseries matrix.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

tsize = size(ts);
tsize(1) = 1;

ts = (ts - repmat(min(ts), tsize))./repmat(max(ts)-min(ts), tsize);
ts = ts - repmat(mean(ts), tsize);

