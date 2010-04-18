function [ts] = g_NormalizeTimeseries(ts)

%
%    It normalizes timeseries to range 1, mean 0
%    It works along columns
%
%    Grega Repovs - created: 2008.7.16
%

tsize = size(ts);
tsize(1) = 1;

ts = (ts - repmat(min(ts), tsize))./repmat(max(ts)-min(ts), tsize);
ts = ts - repmat(mean(ts), tsize);

