function [img] = img_filter(img, hp_sigma, lp_sigma, omit, verbose, ignore)

%``img_filter(img, hp_sigma, lp_sigma, omit, verbose, ignore)``
%
%   INPUTS
%   ======
%
%   --img        image to be filtered
%   --hp_sigma   sigma for high-pass filter
%   --lp_sigma   sigma for low-pass filter
%   --omit       how many frames to omit at the start of the run
%   --verbose    should we talk much
%   --ignore     what to do with frames marked as "do not use"
%
%                - keep   ... do nothing
%                - linear ... do linear interpolation
%                - spline ... do spline interpolation
%
%   OUTPUT
%   ======
%   
%   img
%       filtered image
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

%------- Check input

if nargin < 6, ignore = []; end
if nargin < 5, verbose = false; end
if nargin < 4, omit = 0; end
if nargin < 3, lp_sigma = 0; end

if isempty(ignore), ignore = 'keep'; end
img.data = img.image2D;

use = ones(1, img.frames);
if omit > 0
    use(1:omit) = 0;
end
if ~strcmp(ignore, 'keep')
    use = img.use & (use > 0);
end
ffirst = find(use, 1, 'first');
flast  = find(use, 1, 'last');

%------- Prepare data

len      = flast - ffirst + 1;
data     = img.data(:,ffirst:flast);
use      = use(ffirst:flast);
mask     = var(data(:, use==1), 1, 2) > 0;
data     = data(mask, :);
nvox     = size(data, 1);

if nvox == 0
    return
end

%------- Interpolate?
if verbose, fprintf('\n---> Temporal filtering (15/10/22)'); end
if verbose, fprintf('\n---> triming: %d on start, %d on end', ffirst-1, img.frames-flast); end
if verbose, fprintf('\n---> remaining bad frames: %d, action: %s', sum(use==0), ignore); end

if sum(use==0) > 0 & (~strcmp(ignore, 'keep'))
    if verbose, fprintf('\n---> interpolating %d frames', sum(use==0)); end
    x  = [1:len]';
    xi = x;
    x  = x(use==1);
    Y  = data(:, use==1)';
    data = interp1(x, Y, xi, ignore)';
end

%------- Create mask, window, and tmp

if hp_sigma
    hp_mask = ceil(hp_sigma*3);
    hp_exp = zeros(1, hp_mask*2+1);
    for n = 1:hp_mask*2+1
        t = n-hp_mask-1;
        hp_exp(n) = exp(-0.5*t^2/hp_sigma^2);
    end
end

if lp_sigma
    lp_mask = ceil(lp_sigma*5)+2;
    lp_exp = zeros(1, lp_mask*2+1);
    for n = 1:lp_mask*2+1
        t = n-lp_mask-1;
        lp_exp(n) = exp(-0.5*t^2/lp_sigma^2);
    end
    lp_exp = lp_exp./sum(lp_exp);
else
    lp_mask = 0;
end

tmp = zeros(nvox, len+lp_mask*2);

%------- Do hi-pass


if hp_sigma
    dt = [-hp_mask:hp_mask];
    A = hp_exp .* dt;
    C = hp_exp .* dt .* dt;
    sAf = sum(A);
    sCf = sum(C);
    denom = sCf*sum(hp_exp) - sAf^2;

    if verbose, fprintf('\n---> hipass frame     '), end
    first = true;
    c0 = zeros(nvox,1);
    for t = 1:len
        if verbose && mod(t, 20) == 0, fprintf('%5d',t), end

        bot = max([t-hp_mask, 1]);
        top = min([t+hp_mask, len]);

        wbot = bot-t+hp_mask+1;
        wtop = top-t+hp_mask+1;

        if wtop-wbot == length(A)
            sA = sAf;
            sC = sCf;
            tempdenom = denom;
        else
            sC = sum(C(wbot:wtop));
            sA = sum(A(wbot:wtop));
            tmpdenom = sC*sum(hp_exp(wbot:wtop)) - sA^2;
        end

        if tmpdenom
            tc = (sum(data(:,bot:top).*repmat(hp_exp(wbot:wtop),nvox,1),2).*sC - sum(data(:,bot:top).*repmat(A(wbot:wtop),nvox,1),2) .* sA) ./ tmpdenom;
            if first
                c0 = tc;
                first = false;
            end
            tmp(:,t+lp_mask) =  c0 + data(:,t) - tc;
        else
            tmp(:,t+lp_mask) = data(:,t);
        end
    end
    if verbose, fprintf('\n'), end
else
    tmp(:,lp_mask+1:len+lp_mask) = data;
end

%------- Do low-pass

out = zeros(size(data));

if lp_sigma
    % --- pad
    for n = 1:lp_mask
        tmp(:,n) = tmp(:,lp_mask+1);
        tmp(:,len+lp_mask+n) = tmp(:,len+lp_mask);
    end

    w = repmat(lp_exp, nvox,1);
    if verbose, fprintf('\n---> lopass frame      '), end
    for t = 1:len
        if verbose && mod(t, 20) == 0, fprintf('%5d',t); end
        out(:,t) = sum(tmp(:,t:t+2*lp_mask).*w,2);
    end
    if verbose, fprintf('\n'), end
else
    out = tmp;
end

img.data(mask,ffirst:flast) = out;
