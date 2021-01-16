function [ts] = g_NormalizeTimeseries(ts)

%``function [ts] = g_NormalizeTimeseries(ts)``
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

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
%   2008-07-16 Grega Repovs
%			   Initial version.
%

tsize = size(ts);
tsize(1) = 1;

ts = (ts - repmat(min(ts), tsize))./repmat(max(ts)-min(ts), tsize);
ts = ts - repmat(mean(ts), tsize);

