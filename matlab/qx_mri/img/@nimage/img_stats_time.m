function [out, done] = img_stats_time(img, doIt, mask)

%``img_stats_time(img, doIt, mask)``
%
%    Computes the specified statistics across all voxels of each frame specified
%   by the mask.
%
%   INPUTS
%   ======
%
%   --img   A nimage object to compute statistics on.
%   --do    A comma separated string or a cell array of strings specifying the 
%           statistics to compute ['n, m, me, max, min, sum, sd, var, dvars']
%
%           - 'n'       ...  number of non-nan voxels
%           - 'm'       ...  mean
%           - 'me'      ...  median
%           - 'max'     ...  max
%           - 'min'     ...  min
%           - 'sum'     ...  sum
%           - 'sd'      ...  standard deviation
%           - 'var'     ...  variability
%           - 'dvars'   ...  RMS of BOLD derivative across voxels
%
%   --mask  A mask of voxels to be included in the statistics
%
%   OUTPUTS
%   =======
%
%   out
%       Structure with results in named fields.
%
%   done
%       A cell array of the executed commands.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 3, mask = []; end
if nargin < 2, doIt = []; end

if isempty(doIt)
    doIt = {'n', 'm', 'me', 'max', 'min', 'sum', 'sd', 'var', 'dvars'};
end

if ~iscell(doIt)
    doIt = strtrim(regexp(doIt, ',', 'split'));
end

% --- mask image

if ~isempty(mask)
    img = img.maskimg(mask);
end

% --- ensure we have 2D representation

img.data = img.image2D;

% --- prepare output timeseries

nstats = length(doIt);

% --- run the stats loop

n   = [];
m   = [];
me  = [];
mx  = [];
mn  = [];
sm  = [];
sd  = [];
v   = [];
dv  = [];
done = {};

c = 0;
for d = doIt
    c = c + 1;

    switch char(d)

    case 'n'
        if isempty(n), n = sum(~isnan(img.data), 1); end
        out.n = n;
        done{c} = char(d);

    case 'm'
        if isempty(n), n = sum(~isnan(img.data), 1); end
        if isempty(sm), sm = nansum(img.data, 1); end
        if isempty(m), m = sm./n; end
        out.mean = m;
        done{c} = char(d);

    case 'me'
        out.median = median(img.data, 1, "omitnan");
        done{c} = char(d);

    case 'max'
        out.max = max(img.data, [], 1);
        done{c} = char(d);

    case 'min'
        out.min = min(img.data, [], 1);
        done{c} = char(d);

    case 'sum'
        if isempty(sm), sm = nansum(img.data, 1); end
        out.sum = sm;
        done{c} = char(d);

    case 'sd'
        if isempty(sd), sd = std(img.data, 0, 1, "omitnan"); end
        out.sd = sd;
        done{c} = char(d);

    case 'var'
        if isempty(v), v = var(img.data, 1, 1, "omitnan"); end
        out.var = v;
        done{c} = char(d);

    case 'dvars'
        if isempty(sm), sm = nansum(img.data, 1); end
        if isempty(n), n = sum(~isnan(img.data), 1); end
        if isempty(m), m = sm./n; end
        dv = diff(img.data, 1, 2);
        dv = [0 sqrt(mean(dv.^2, 1))];
        out.dvars   = dv;
        out.dvarsm  = dv ./ m .* 100;
        out.dvarsme = out.dvarsm ./ median(out.dvarsm);
        done{c} = char(d);
    end
end
