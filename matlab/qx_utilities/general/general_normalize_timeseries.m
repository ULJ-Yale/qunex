function [ts] = general_normalize_timeseries(ts)

%``function [ts] = general_normalize_timeseries(ts)``
%
%   This function normalizes timeseries to range 1, mean 0.
%   It works along columns.
%
%   INPUT
%   =====
%
%	--ts 	timeseries (time x regions/voxels)
%
%	OUTPUT
%	======
%
%	ts
%		normalized timeseries matrix
%

tsize = size(ts);
tsize(1) = 1;

ts = (ts - repmat(min(ts), tsize))./repmat(max(ts)-min(ts), tsize);
ts = ts - repmat(mean(ts), tsize);

