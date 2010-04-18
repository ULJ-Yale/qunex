function [p] = fc_ttest(x, tail)

if nargin < 2
	tail = 0;
end

m = 0;
dim = 1;

nans = isnan(x);
if any(nans(:))
    samplesize = sum(~nans,dim);
else
    samplesize = size(x,dim); % a scalar, => a scalar call to tinv
end
df = max(samplesize - 1,0);
xmean = nanmean(x);
sdpop = nanstd(x);
ser = sdpop ./ sqrt(samplesize);
tval = (xmean - m) ./ ser;


% Compute the correct p-value for the test, and confidence intervals
% if requested.
if tail == 0 % two-tailed test
    p = 2 * tcdf(-abs(tval), df);
elseif tail == 1 % right one-tailed test
    p = tcdf(-tval, df);
elseif tail == -1 % left one-tailed test
    p = tcdf(tval, df);
else
    error('stats:ttest:BadTail',...
          'TAIL must be ''both'', ''right'', or ''left'', or 0, 1, or -1.');
end

