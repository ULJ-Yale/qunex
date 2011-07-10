function [out, do] = mri_StatsTime(img, do, mask)

%function [out, do] = mri_StatsTime(img, do, mask)
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
%    (c) Grega Repovs, 2011-07-09

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


c = 0;
for d = do
    c = c + 1;
    
    switch char(d)
    
    case 'n'
        if isempty(n), n = sum(~isnan(img.data), 1); end
        out.n = n;
    
    case 'm'
        if isempty(sm), sm = nansum(img.data, 1); end
        if isempty(m), m = sm./n; end
        out.mean = m;
        
    case 'me'
        out.median = nanmedian(img.data, 1);
        
    case 'max'
        out.max = nanmax(img.data, [], 1);
        
    case 'min'
        out.min = nanmin(img.data, [], 1);
        
    case 'sum'
        if isempty(sm), sm = nansum(img.data, 1); end
        out.sum = sm;

    case 'sd'
        if isempty(sd), sd = nanstd(img.data, 0, 1); end
        out.sd = sd;
    
    case 'var'
        if isempty(v), v = nanvar(img.data, 1, 1); end
        out.var = v;
    
    case 'dvars'
        if isempty(sm), sm = nansum(img.data, 1); end
        if isempty(n), n = sum(~isnan(img.data), 1); end
        if isempty(m), m = sm./n; end
        dv = diff(img.data, 1, 2);
        dv = [0 sqrt(mean(dv.^2, 1))];
        out.dvars   = dv;
        out.dvarsm  = dv ./ m .* 100;
        out.dvarsme = out.dvarsm ./ median(out.dvarsm);
    end
end


