function [out, doIt] = img_stats(img, doIt, exclude)

%``img_stats(img, doIt, exclude)``
%
%   Computes the specified statistics across frames excluding values specified
%   in exclude.
%
%   INPUTS
%   ======
%       
%   --img       A nimage object
%   --do        A comma separated string or a cell array of the statistics to
%               compute ['m']:
%   
%               _ 'n'     ... number of values
%               _ 'm'     ... mean
%               _ 'me'    ... median
%               _ 'max'   ... max
%               _ 'min'   ... min
%               _ 'sum'   ... sum
%               _ 'sd'    ... standard deviation
%               _ 'var'   ... variability
%               _ 'rmsd'  ... root mean squared difference across time
%               _ 'nrmsd' ... mean normalized root mean squared difference across time
%               _ 't'     ... t value of t-test against zero
%               _ 'tp'    ... p values of t-test against zero
%               _ 'tz'    ... z values of t-test against zero
%
%   --exclude   values to be omitted from computing the statistics
%
%   OUTPUT
%   ======
%
%   out
%       a nimage object with one frame for each statistic computed
%   do
%       the command executed
%
%   USE
%   ===
%
%   The method is used to compute the specified statistics across all frames for
%   each voxel of the image. All the voxels with values specified in exclude are
%   set to NaN, and all the statistics are computed excluding NaN values.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%
%       msdimg = img.img_stats({'m', 'sd'});
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 3, exclude = [];            end
if nargin < 2 || isempty(doIt), doIt = 'm'; end

if ~iscell(doIt)
    doIt = strtrim(regexp(doIt, ',', 'split'));
end

% --- NaN the exclude values

img.data = img.image2D;
img.data(isinf(img.data)) = NaN;
if ~isempty(exclude)
    img.data(ismember(img.data, exclude)) = NaN;
end

% --- prepare output image

nstats = length(doIt);
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
r  = [];
nr = [];

c = 0;
for d = doIt(:)'
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
        out.data(:,c) = median(img.data, 2, "omitnan");

    case 'max'
        out.data(:,c) = max(img.data, 2);

    case 'min'
        out.data(:,c) = min(img.data, 2);

    case 'sum'
        if isempty(s), s = nansum(img.data, 2); end
        out.data(:,c) = s;

    case 'sd'
        if isempty(sd), sd = std(img.data, 0, 2, "omitnan"); end
        out.data(:,c) = sd;

    case 'var'
        if isempty(v), v = var(img.data, 1, 2, "omitnan"); end
        out.data(:,c) = v;

    case 't'
        if isempty(s), s = nansum(img.data, 2); end
        if isempty(n), n = sum(~isnan(img.data), 2); end
        if isempty(m), m = s./n; end
        if isempty(v), v = var(img.data, 1, 2, "omitnan"); end
        if isempty(t), t = m./(sqrt(v./n)); end
        out.data(:,c) = t;

    case 'tp'
        if isempty(s), s = nansum(img.data, 2); end
        if isempty(n), n = sum(~isnan(img.data), 2); end
        if isempty(m), m = s./n; end
        if isempty(v), v = var(img.data, 1, 2, "omitnan"); end
        if isempty(t), t = m./(sqrt(v./n)); end
        if isempty(p), p = tcdf(-abs(t), n-1).*2; end
        out.data(:,c) = p;

    case 'tz'
        if isempty(s), s = nansum(img.data, 2); end
        if isempty(n), n = sum(~isnan(img.data), 2); end
        if isempty(m), m = s./n; end
        if isempty(v), v = var(img.data, 1, 2, "omitnan"); end
        if isempty(t), t = m./(sqrt(v./n)); end
        if isempty(p), p = tcdf(-abs(t), n-1).*2; end
        p(p<0.00000000000001)=0.00000000000001;
        if isempty(z), z = norminv((1-(double(p)/2)), 0, 1) .* sign(m); end
        out.data(:,c) = z;

    case 'rmsd'
        if isempty(r), r = sqrt(mean(diff(img.data, 1, 2) .^ 2, 2)); end
        out.data(:,c) = r;

    case 'nrmsd'
        if isempty(s), s = nansum(img.data, 2); end
        if isempty(n), n = sum(~isnan(img.data), 2); end
        if isempty(m), m = s./n; end
        if isempty(r), r = sqrt(mean(diff(img.data, 1, 2) .^ 2, 2)); end
        if isempty(nr), nr = r ./ m; end
        out.data(:,c) = nr;

    end
end


