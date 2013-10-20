function [img] = mri_Filter(img, hp_sigma, lp_sigma, omit, verbose, ignore)

%function [img] = mri_Filter(img, hp_sigma, lp_sigma, omit, verbose, ignore)
%
%   input
%       img      - image to be filtered
%       hp_sigma - sigma for high-pass filter
%       lp_sigma - sigma for low-pass filter
%       omit     - how many frames to omit at the start of the run
%       verbose  - should we talk much
%       ignore   - what to do with frames marked as "do not use"
%                   - keep   : do nothing
%                   - linear : do linear interpolation
%                   - spline : do spline interpolation
%
% Grega Repovš - 2013-10-20
%              - added the ignore / interpolate option
%



%------- Check input

if nargin < 6
    ignore = [];
    if nargin < 5
        verbose = false;
        if nargin < 4
            omit = 0;
            if nargin < 3
                lp_sigma = 0;
            end
        end
    end
end

if isempty(ignore), ignore = 'keep'; end
img.data = img.image2D;

%------- Interpolate?

if sum(img.use==0) > 0 & (~strcmp(ignore, 'keep'))
    x  = [1:img.frames]';
    xi = x;
    x  = x(img.use);
    Y  = img.data(:, img.use)';
    img.data = interp1(x, Y, xi, ignore)';
end

%------- Prepare data

nvox     = img.voxels;
len      = img.frames - omit;
data     = img.data(:,omit+1:img.frames);

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

    if verbose, fprintf('hipass frame    '), end
    first = true;
    c0 = zeros(nvox,1);
    for t = 1:len
        if verbose, fprintf('\b\b\b\b%4d',t), end

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
    if verbose, fprintf('\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b'), end
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
    if verbose, fprintf('lopass frame     '), end
    for t = 1:len
        fprintf('\b\b\b\b%4d',t);
        out(:,t) = sum(tmp(:,t:t+2*lp_mask).*w,2);
    end
    if verbose, fprintf('\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b'), end
else
    out = tmp;
end

img.data(:,omit+1:img.frames) = out;
