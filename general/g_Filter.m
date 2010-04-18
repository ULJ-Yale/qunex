function [out] = g_Filter(in, hp_sigma, lp_sigma)



%------- Check input

if nargin < 3
    lp_sigma = 0;
end

[nvox, len] = size(in);


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
    
    fprintf('hipass frame    ');
    first = true;
    c0 = zeros(nvox,1);
    for t = 1:len
        fprintf('\b\b\b%3d',t);
        
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
            tc = (sum(in(:,bot:top).*repmat(hp_exp(wbot:wtop),nvox,1),2).*sC - sum(in(:,bot:top).*repmat(A(wbot:wtop),nvox,1),2) .* sA) ./ tmpdenom;
            if first
                c0 = tc;
                first = false;
            end
            tmp(:,t+lp_mask) =  c0 + in(:,t) - tc;
        else
            tmp(:,t+lp_mask) = in(:,t);
        end
    end
    fprintf('\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b')
else
    tmp(:,lp_mask+1:len+lp_mask) = in;
end

%------- Do low-pass

out = zeros(size(in));

if lp_sigma
    % --- pad
    for n = 1:lp_mask
        tmp(:,n) = tmp(:,lp_mask+1);
        tmp(:,len+lp_mask+n) = tmp(:,len+lp_mask);
    end
    
    w = repmat(lp_exp, nvox,1);
    fprintf('lopass frame    ');
    for t = 1:len
        fprintf('\b\b\b%3d',t);
        out(:,t) = sum(tmp(:,t:t+2*lp_mask).*w,2);
    end
    fprintf('\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b')
else
    out = tmp;
end


