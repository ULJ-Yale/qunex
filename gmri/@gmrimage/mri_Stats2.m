function [out, do] = mri_Stats2(img1, img2, do, exclude)

%function [out, do] = mri_Stats2(img1, img2, do, exclude)
%
%	Computes the specified statistics across frames excluding values specified in exclude
%   
%   do       - the statistics to compute
%       dm   - difference in mean values
%       dme  - difference in median values
%       dsum - difference in sum values
%       dsd  - difference in standard deviation
%       dvar - difference in variability
%       f    - f-test for difference in variability
%       fp   - p values of f-test for difference in variability
%       t    - t value of dependent t-test
%       tp   - p values of dependent t-test
%       tz   - z values of dependent t-test
%       t2   - t value of independent t-test
%       t2p  - p values of independent t-test
%       t2z  - z values of independent t-test
%
%   exclude - values to be omitted from computing the statistics
%
%    (c) Grega Repovs, 2011-03-18

if nargin < 4
    exclude = [];
    if nargin < 3
        do = 'dm';
    end
end

if ~iscell(do)
    do = {do};
end

% --- NaN the exclude values

img1.data = img1.image2D;
img1.data(isinf(img1.data)) = NaN;
if ~isempty(exclude)
    img1.data(ismember(img1.data, exclude)) = NaN;
end

img2.data = img2.image2D;
img2.data(isinf(img2.data)) = NaN;
if ~isempty(exclude)
    img2.data(ismember(img2.data, exclude)) = NaN;
end

% --- prepare output image

nstats = length(do);
out = img1.zeroframes(nstats);

% --- run the stats loop

n1  = [];
m1  = [];
sd1 = [];
v1  = [];
s1  = [];
n2  = [];
m2  = [];
sd2 = [];
v2  = [];
s2  = [];
dn   = [];
dm   = [];
dme  = [];
dsum = [];
dsd  = [];
dvar = [];
t   = [];
tp  = [];
tz  = [];
t2  = [];
t2p = [];
t2z = [];
t2df = [];
f   = [];
fp  = [];
fz  = [];


c = 0;
for d = do
    c = c + 1;
    
    switch char(d)
    
    case 'dn'
        if isempty(n1), n1 = sum(~isnan(img1.data), 2); end
        if isempty(n2), n2 = sum(~isnan(img2.data), 2); end
        if isempty(dn), dn = n1-n2; end
        out.data(:,c) = dn;
    
    case 'dm'
        if isempty(s1), s1 = nansum(img1.data, 2); end
        if isempty(n1), n1 = sum(~isnan(img1.data), 2); end
        if isempty(m1), m1 = s1./n1; end
        if isempty(s2), s2 = nansum(img2.data, 2); end
        if isempty(n2), n2 = sum(~isnan(img2.data), 2); end
        if isempty(m2), m2 = s2./n2; end
        if isempty(dm), dm = m1-m2; end
        out.data(:,c) = dm;
        
    case 'dme'
        out.data(:,c) = nanmedian(img1.data, 2) - nanmedian(img2.data, 2) ;
        
    case 'dmax'
        out.data(:,c) = nanmax(img1.data, 2) - nanmax(img2.data, 2);
        
    case 'dmin'
        out.data(:,c) = nanmin(img1.data, 2) - nanmin(img2.data, 2);
        
    case 'dsum'
        if isempty(s1), s1 = nansum(img1.data, 2); end
        if isempty(s2), s2 = nansum(img2.data, 2); end
        if isempty(ds), ds = s1-s2; end
        out.data(:,c) = ds;

    case 'sd'
        if isempty(sd1), sd1 = nanstd(img1.data, 0, 2); end
        if isempty(sd2), sd1 = nanstd(img2.data, 0, 2); end
        if isempty(dsd), dsd = sd1-sd2; end
        out.data(:,c) = dsd;
    
    case 'var'
        if isempty(v1), v1 = nanvar(img1.data, 1, 2); end
        if isempty(v2), v2 = nanvar(img2.data, 1, 2); end
        if isempty(dvar), dvar = v1-v2; end
        out.data(:,c) = dvar;
    
    case 't2'
        if isempty(s1), s1 = nansum(img1.data, 2); end
        if isempty(n1), n1 = sum(~isnan(img1.data), 2); end
        if isempty(m1), m1 = s1./n1; end
        if isempty(s2), s2 = nansum(img2.data, 2); end
        if isempty(n2), n2 = sum(~isnan(img2.data), 2); end
        if isempty(m2), m2 = s2./n2; end
        if isempty(dm), dm = m1-m2; end
        if isempty(v1), v1 = nanvar(img1.data, 1, 2); end
        if isempty(v2), v2 = nanvar(img2.data, 1, 2); end
        if isempty(v2), v2 = nanvar(img2.data, 1, 2); end
        if isempty(t2df), t2df = (n1+n2-2); end
        if isempty(t2), t2 = dm ./ sqrt(((n1-1).*v1 + (n2-1).*v2)./t2df); end
        out.data(:,c) = t2;
    
    case 't2p'
        if isempty(s1), s1 = nansum(img1.data, 2); end
        if isempty(n1), n1 = sum(~isnan(img1.data), 2); end
        if isempty(m1), m1 = s1./n1; end
        if isempty(s2), s2 = nansum(img2.data, 2); end
        if isempty(n2), n2 = sum(~isnan(img2.data), 2); end
        if isempty(m2), m2 = s2./n2; end
        if isempty(dm), dm = m1-m2; end
        if isempty(v1), v1 = nanvar(img1.data, 1, 2); end
        if isempty(v2), v2 = nanvar(img2.data, 1, 2); end
        if isempty(v2), v2 = nanvar(img2.data, 1, 2); end
        if isempty(t2df), t2df = (n1+n2-2); end
        if isempty(t2), t2 = dm ./ sqrt(((n1-1).*v1 + (n2-1).*v2)./t2df); end
        if isempty(t2p), t2p = cdf('t', -abs(t2), t2df).*2; end
        out.data(:,c) = t2p;
        
    case 't2z'
        if isempty(s1), s1 = nansum(img1.data, 2); end
        if isempty(n1), n1 = sum(~isnan(img1.data), 2); end
        if isempty(m1), m1 = s1./n1; end
        if isempty(s2), s2 = nansum(img2.data, 2); end
        if isempty(n2), n2 = sum(~isnan(img2.data), 2); end
        if isempty(m2), m2 = s2./n2; end
        if isempty(dm), dm = m1-m2; end
        if isempty(v1), v1 = nanvar(img1.data, 1, 2); end
        if isempty(v2), v2 = nanvar(img2.data, 1, 2); end
        if isempty(v2), v2 = nanvar(img2.data, 1, 2); end
        if isempty(t2df), t2df = (n1+n2-2); end
        if isempty(t2), t2 = dm ./ sqrt(((n1-1).*v1 + (n2-1).*v2)./t2df); end
        if isempty(t2p), t2p = cdf('t', -abs(t2), t2df).*2; end
        t2p(t2p<0.00000000000001)=0.00000000000001;
        if isempty(t2z), t2z = icdf('Normal', (1-(double(t2p)/2)), 0, 1) .* sign(dm); end
        out.data(:,c) = t2z;
    end
end


