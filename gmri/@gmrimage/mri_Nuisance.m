function [out, done] = mri_Nuisance(img, do, mask)

%function [out, done] = mri_Nuisance(img, do, mask)
%
%	Computes the specified statistics across voxels specified in mask
%
%   do          - the statistics to compute
%       n       - non-nan voxels
%       m       - mean
%       me      - median
%       max     - max
%       min     - min
%       sum     - sum
%       sd      - standard deviation
%       var     - variability
%       dvars   - RMS of BOLD derivative across voxels
%
%   mask - mask of voxels to be included in the statistics
%
%   Output
%       out  - structure with results in named fields
%       done - a cell array of executed commands
%
%
%    (c) Grega Repovs, 2011-07-09
%
%   2011-10-24, Grega Repovš
%       - checks what was actually executed instead of just returning the do cell array
%
%   To do
%       - add possibility of comma separated do list
%


if nargin < 3
    mask = [];
    if nargin < 2
        do = [];
    end
end

if isempty(do)
    do = {'n', 'm', 'me', 'max', 'min', 'sum', 'sd', 'var', 'dvars'};
end

if ~iscell(do)
    do = {do};
end

% --- mask image

if ~isempty(mask)
    img = img.maskimg(mask);
end

% --- ensure we have 3d representation

img.data = img.image2D;

% --- prepare output timeseries

nstats = length(do);

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
for d = do
    c = c + 1;

    switch char(d)

    case 'n'
        if isempty(n), n = sum(~isnan(img.data), 1); end
        out.n = n;
        done{c} = char(d);

    case 'm'
        if isempty(sm), sm = nansum(img.data, 1); end
        if isempty(m), m = sm./n; end
        out.mean = m;
        done{c} = char(d);

    case 'me'
        out.median = nanmedian(img.data, 1);
        done{c} = char(d);

    case 'max'
        out.max = nanmax(img.data, [], 1);
        done{c} = char(d);

    case 'min'
        out.min = nanmin(img.data, [], 1);
        done{c} = char(d);

    case 'sum'
        if isempty(sm), sm = nansum(img.data, 1); end
        out.sum = sm;
        done{c} = char(d);

    case 'sd'
        if isempty(sd), sd = nanstd(img.data, 0, 1); end
        out.sd = sd;
        done{c} = char(d);

    case 'var'
        if isempty(v), v = nanvar(img.data, 1, 1); end
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




%
%  ----- Support functions
%

function [V, WB, WM] = asegNuisanceROI(file);

    fsimg = gmrimage(file.segmask);
    bmimg = gmrimage(file.boldmask);
    V     = fsimg.zeroframes(1);
    WB    = fsimg.zeroframes(1);
    WM    = fsimg.zeroframes(1);

    bmimg.data = (bmimg.data > 0) & (fsimg.data > 0);

    WM.data = (fsimg.data == 2 | fsimg.data == 41) & (bmimg.data > 0);
    WM      = WM.mri_ShrinkROI();
    WM.data = WM.image2D;

    V.data  = ismember(fsimg.data, [4 5 14 15 24 43 44 72]) & (bmimg.data > 0);
    WB.data = (bmimg.data > 0) & (WM.data ~=1) & ~V.data;

    V       = V.mri_ShrinkROI('surface', 6);
    WB      = WB.mri_ShrinkROI('edge', 10); %'edge', 10
    WM      = WM.mri_ShrinkROI();
    WM      = WM.mri_ShrinkROI();

return