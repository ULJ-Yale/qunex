function [out, do] = mri_Stats(img, do, exclude)

%function [out, do] = mri_Stats(img, do, exclude)
%
%	Computes the specified statistics across frames excluding values specified in exclude
%
%   INPUT
%       img ... A gmrimage object
%       do  ... A comma separated string or a cell array of the statistics to
%               compute ['m']:
%           'n'   ... number of values
%           'm'   ... mean
%           'me'  ... median
%           'max' ... max
%           'min' ... min
%           'sum' ... sum
%           'sd'  ... standard deviation
%           'var' ... variability
%           't'   ... t value of t-test against zero
%           'tp'  ... p values of t-test against zero
%           'tz'  ... z values of t-test against zero
%       exclude - values to be omitted from computing the statistics
%
%   OUTPUT
%       out ... a gmrimage object with one frame for each statistic computed
%       do  ... the command executed
%
%   USE
%   The method is used to compute the specified statistics across all frames for
%   each voxel of the image. All the voxels with values specified in exclude are
%   set to NaN, and all the statistics are computed excluding NaN values.
%
%   EXAMPLE USE
%   >>> msdimg = img.mri_Stats({'m', 'sd'});
%
%   ---
%   Written by Grega Repovs, 2011-03-18
%
%   Changelog
%   2017-03-11 Grega Repovs
%            - Updated documentation.
%            - Now accepts string with a comma separated commands.
%            - Made loop more robust.


if nargin < 3, exclude = [];            end
if nargin < 2 || isempty(do), do = 'm'; end

if ~iscell(do)
    do = strtrim(regexp(do, ',', 'split'));
end

% --- NaN the exclude values

img.data = img.image2D;
img.data(isinf(img.data)) = NaN;
if ~isempty(exclude)
    img.data(ismember(img.data, exclude)) = NaN;
end

% --- prepare output image

nstats = length(do);
out = img.zeroframes(nstats);

% --- run the stats loop

n  = [];
m  = [];
sd = [];
v  = [];
s  = [];
t  = [];
p  = [];
z  = [];

c = 0;
for d = do(:)'
    c = c + 1;

    switch char(d)

    case 'n'
        if isempty(n), n = sum(~isnan(img.data), 2); end
        out.data(:,c) = n;

    case 'm'
        if isempty(s), s = nansum(img.data, 2); end
        if isempty(n), n = sum(~isnan(img.data), 2); end
        if isempty(m), m = s./n; end
        out.data(:,c) = m;

    case 'me'
        out.data(:,c) = nanmedian(img.data, 2);

    case 'max'
        out.data(:,c) = nanmax(img.data, 2);

    case 'min'
        out.data(:,c) = nanmin(img.data, 2);

    case 'sum'
        if isempty(s), s = nansum(img.data, 2); end
        out.data(:,c) = s;

    case 'sd'
        if isempty(sd), sd = nanstd(img.data, 0, 2); end
        out.data(:,c) = sd;

    case 'var'
        if isempty(v), v = nanvar(img.data, 1, 2); end
        out.data(:,c) = v;

    case 't'
        if isempty(s), s = nansum(img.data, 2); end
        if isempty(n), n = sum(~isnan(img.data), 2); end
        if isempty(m), m = s./n; end
        if isempty(v), v = nanvar(img.data, 1, 2); end
        if isempty(t), t = m./(sqrt(v./n)); end
        out.data(:,c) = t;

    case 'tp'
        if isempty(s), s = nansum(img.data, 2); end
        if isempty(n), n = sum(~isnan(img.data), 2); end
        if isempty(m), m = s./n; end
        if isempty(v), v = nanvar(img.data, 1, 2); end
        if isempty(t), t = m./(sqrt(v./n)); end
        if isempty(p), p = cdf('t', -abs(t), n-1).*2; end
        out.data(:,c) = p;

    case 'tz'
        if isempty(s), s = nansum(img.data, 2); end
        if isempty(n), n = sum(~isnan(img.data), 2); end
        if isempty(m), m = s./n; end
        if isempty(v), v = nanvar(img.data, 1, 2); end
        if isempty(t), t = m./(sqrt(v./n)); end
        if isempty(p), p = cdf('t', -abs(t), n-1).*2; end
        p(p<0.00000000000001)=0.00000000000001;
        if isempty(z), z = icdf('Normal', (1-(double(p)/2)), 0, 1) .* sign(m); end
        out.data(:,c) = z;
    end
end


