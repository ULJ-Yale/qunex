function [B, res, rvar, Xdof, B_se, B_t, B_z, B_pval] = img_glm_fit(obj, X, options)

%``img_glm_fit(obj, X)``.
%
%    Computes GLM fit to whole brain
%
%   INPUTS
%    ======
%
%    --obj     nimage image object
%    --X       predictor matrix (frames x predictors)
%    --options (optional) <key>:<value> string or struct with options:
%               - method: none (defaut) | ar1 | arp | arma11 | film
%               - order: p (for arp) (default 3)
%               - pool: global (default) | parcel
%               - film_maxlag: max lag for FILM (default: empty, auto)
%               - film_alpha: alpha for FILM (default: 0.5)
%               - film_eps: epsilon for FILM (default: 1e-6)
%               - iterate: true | false (default false)
%               - min_seg_skip: min segment length to apply whitening (default 20)
%               - min_seg_ar1: min segment length to fit AR(1) (default 40)
%               - fast_lambda: shrinkage for FILM (default 0.25)
%               - fast_win: moving-average window for FILM (default 9)
%               - fast_log: true | false (default true)
%               - permutation_safe: true | false (default false)
%               - shrink_k: shrinkage parameter for ARP (default 200)
%               - arp_pmax: max AR order for ARP (default 6)
%               - arp_auto: true | false (default true)
%               - debug_mode: true | false (default false)
%
%   OUTPUTS
%    =======
%
%   B
%        beta weights image
%   res
%        residual image
%   rvar
%        variance of the residual
%   Xdof
%        model degrees of freedom
%   B_se
%        standard error of beta weights
%   B_t
%        t-statistics of beta weights
%   B_z
%        z-scores of beta weights (signed; derived from two-sided p-values)
%   B_pval
%        P-values of beta weights
%
%   USE
%    ===
%
%   The method computes a linear regression between dataseries of each voxel and
%   all the columns of the X regressor matrix. The image can be a series of
%   activation values for a set of sessions, and columns of X behavioral,
%   demographic or other variables. X can have whatever number of columns, but
%   the number of rows need to match the number of frames in the image.
%
%   The results in an image of beta values for each voxel of the image, each
%   frame holding the beta value for each of the columns of the X matrix. res is
%   an image holding the residual remaining after regression. Xdof holds the
%   model's degrees of freedom (ncols - nrows). rvar holds the variance image,
%   the sum of squares of the residuals divided by the model degrees of freedom.
%
%   EXAMPLE USE
%    ===========
%
%   ::
%
%        [B, res, rvar, Xdof] = img.img_glm_fit2(behmatrix);
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% ---- check input

    if nargin < 2, error('ERROR: Not enough parameters to compute GLM!'); end
    if nargin < 3, options = ''; end

    default = 'method:none|order:3|pool:global|film_maxlag:|film_alpha:0.5|film_eps:1e-6|iterate:false|min_seg_skip:20|min_seg_ar1:40|fast_lambda:0.25|fast_win:9|fast_log:true|permutation_safe:false|shrink_k:200|arp_pmax:6|arp_auto:true|debug_mode:false|protect_drifts:false|drift_cols:|drift_autodetect:true|drift_detect_tol:0.9995|drift_detect_maxperseg:2';
    options = general_parse_options([], options, default);

    options.debug_mode       = strcmp(options.debug_mode, 'true');
    options.permutation_safe = strcmp(options.permutation_safe, 'true');
    options.iterate          = strcmp(options.iterate, 'true');
    options.fast_log         = strcmp(options.fast_log, 'true');
    options.arp_auto         = strcmp(options.arp_auto, 'true');
    options.film_eps         = str2double(options.film_eps);
    options.protect_drifts   = strcmp(options.protect_drifts, 'true');
    options.drift_autodetect = strcmp(options.drift_autodetect, 'true');

    if options.debug_mode
        fprintf('\n');
        general_print_struct(options, 'Fit GLM - prewhitening options used');
        fprintf('\n');
    end

    % --- Permutation-safe adjustments:
    if options.permutation_safe
        % Avoid iterative re-estimation (keeps transformation fixed/simple)
        options.iterate = false;

        % If user requested high-order model, coerce to safer options
        if any(strcmp(options.method, {'arp', 'arma11'}))
            % Prefer FILM (stable) else AR(1)
            if ~strcmp(options.method, 'film')
                options.method = 'ar1';
            end
        end

        % Make FILM shrinkage modest and PSD floor conservative
        if strcmp(options.method, 'film')
            if ~isfield(options, 'fast_lambda') || isempty(options.fast_lambda)
                options.fast_lambda = 0.25;
            end
            options.film_eps = max(options.film_eps, 1e-6);
        end
    end

    % --- check dimensions
    if obj.frames ~= size(X, 1)
        error('ERROR: predictor and data number of frames do not match!');
    end

    % ---- prewhitening pooling weights and segments

    seg_id = obj.use(:); % integer per frame for segments
    w_parc = parcel_weights(obj, options);

    % ---- zero sd regressors

    good = std(X) ~= 0;
    good(find(~good & mean(X)==1,1)) = true;

    % ---- compute GLM

    % ---- image of beta coefficients
    B = obj.zeroframes(size(X,2));
    B.data = reshape(B.data,B.frames,B.voxels);

    % --- extract data from the input image
    obj.data = obj.image2D';
    y = obj.data;
    X = X(:,good);

    %% ---------------- INITIAL OLS ----------------
    XtX = X' * X;
    beta0 = (XtX \ X') * y;
    residuals0 = y - X * beta0;

    %% ---------------- APPLY PREWHITENING IF REQUESTED ----------------
    if ~strcmp(options.method, 'none')
        if options.debug_mode
            fprintf('--> Applying prewhitening method: %s\n', options.method);
        end

        % ---- Protect drift regressors if requested
        if options.protect_drifts && isempty(options.drift_cols) && options.drift_autodetect
            options.drift_cols = detect_drift_cols_from_X(X, obj.use, options.drift_detect_tol, options.drift_detect_maxperseg);
            if isfield(options, 'debug') && options.debug
                fprintf('[DriftProtect] auto-detected %d drift cols\n', numel(options.drift_cols));
            end
        end

        % ---- 1st whiten – GLS
        [Xw, yw] = apply_whitening(X, y, residuals0, seg_id, options, w_parc);

        if ndims(Xw) == 2
            % === Global whitening case ===
            XtXw = Xw' * Xw;
            beta = (XtXw \ Xw') * yw;
            residuals = yw - Xw * beta;

        else
            % === Parcel-wise whitening case ===
            % Xw: T × predictors × parcels
            % yw: T × parcels
            [T, npred, nparc] = size(Xw);
            beta = zeros(npred, nparc);
            residuals = zeros(size(yw));

            for p = 1:nparc
                Xp = Xw(:, :, p);
                yp = yw(:, p);
                betap = (Xp' * Xp) \ (Xp' * yp);
                beta(:, p) = betap;
                residuals(:, p) = yp - Xp * betap;
            end

            % XtX equivalent for SE computation will be per parcel,
            % but we will track final XtX in XtX_current below.
            XtXw = []; % marker: handled later
        end

        % ---- Optional REML iteration ---
        if options.iterate
            residuals_gls = y - X * beta;

            [Xw2, yw2] = apply_whitening(X, y, residuals_gls, seg_id, options, w_parc);

            if ndims(Xw2) == 2
                XtXw2 = Xw2' * Xw2;
                beta = (XtXw2 \ Xw2') * yw2;
                residuals = yw2 - Xw2 * beta;
                XtXw = XtXw2;
            else
                [T, npred, nparc] = size(Xw2);
                beta = zeros(npred, nparc);
                residuals = zeros(size(yw2));

                for p = 1:nparc
                    Xp = Xw2(:, :, p);
                    yp = yw2(:, p);
                    betap = (Xp' * Xp) \ (Xp' * yp);
                    beta(:, p) = betap;
                    residuals(:, p) = yp - Xp * betap;
                end

                XtXw = []; % parcel mode, handled later
            end
        end

        XtX_current = XtXw;
    else
        if options.debug_mode
            fprintf('--> No prewhitening applied (OLS)\n');
        end
        beta = beta0;
        residuals = residuals0;
        XtX_current = XtX;
    end

    % ---- embed beta weights to output
    B.data(good,:) = beta;
    B.data = B.data';

    if nargout > 1
        % ---- compute the residuals
        res = obj;
        res.data = residuals';

        if nargout > 2
            % ---- compute the degrees of freedom
            Xdof = size(X,1) - size(X,2);

            % ---- compute the mean squared error (MSE)
            MSE = sum(residuals.^2,1) / Xdof;
            rvar = obj.zeroframes(1);
            rvar.data = MSE';

            if nargout > 4
                B_se = obj.zeroframes(size(X,2));
                B_se.data = reshape(B_se.data,B_se.frames,B_se.voxels);

                B_t = obj.zeroframes(size(X,2));
                B_t.data = reshape(B_t.data,B_t.frames,B_t.voxels);

                B_z = obj.zeroframes(size(X,2));
                B_z.data = reshape(B_z.data,B_z.frames,B_z.voxels);

                B_pval = obj.zeroframes(size(X,2));
                B_pval.data = reshape(B_pval.data,B_pval.frames,B_pval.voxels);

                % ---- compute the standard error of beta estimates
                if size(MSE, 2) > 1
                    MSE = MSE'; % ensure column
                end
                % var_beta = diag(inv(X'*X));
                if ndims(Xw) == 2
                    % global whitening case
                    var_beta = diag(inv(XtX_current)); % [nPred × 1]
                    SE_beta  = sqrt(var_beta * MSE'); % [nPred × nVox]
                else
                    % parcel-wise case: compute SE per parcel
                    npred = size(Xw, 2);
                    nvox = size(MSE, 1);

                    SE_beta = zeros(npred, nvox);

                    for p = 1:nvox
                        Xp = Xw(:, :, p);
                        XtX = Xp' * Xp;
                        var_b = diag(inv(XtX)); % [nPred × 1]
                        SE_beta(:, p) = sqrt(var_b * MSE(p)); % [nPred × 1]
                    end
                end

                % ---- compute the t-statistics and p-values for beta estimates
                t_beta = beta ./ SE_beta;
                p_beta = 2 .* (1 - tcdf(abs(t_beta), Xdof));

                % ---- compute signed z-scores from two-sided p-values
                % z = sign(t) * norminv(1 - p/2)
                % Guard against p=0 due to underflow by flooring at realmin
                p_safe = max(min(p_beta, 1-1e-16), realmin);
                z_beta = sign(t_beta) .* norminv(1 - p_safe/2, 0, 1);

                % ---- embed data to output images
                B_se.data(good, :)   = SE_beta;  B_se.data   = B_se.data';
                B_t.data(good, :)    = t_beta;   B_t.data    = B_t.data';
                B_z.data(good, :)    = z_beta;   B_z.data    = B_z.data';
                B_pval.data(good, :) = p_beta;   B_pval.data = B_pval.data';
            end
        end
    end
end



%% --------- APPLY WHITENING OVER SEGMENTS ----------
function [Xw, Yw] = apply_whitening(X, Y, R, seg_id, opts, w_parc)

    Xw = [];
    Yw = [];

    segs = unique(seg_id(:)); segs(isnan(segs)) = [];

    debug_mode         = isfield(opts, 'debug_mode') && opts.debug_mode;
    debug_info         = struct;
    debug_info.segment = [];
    debug_info.length  = [];
    debug_info.method  = {};
    debug_info.iter    = [];
    debug_info.p_order = [];

    for s = segs'
        idx = (seg_id == s);
        Rseg = R(idx, :);
        Yseg = Y(idx, :);
        Xseg = X(idx, :);

        % ---- Drift-protected estimation (projection only for estimating noise) ----
        if isfield(opts, 'protect_drifts') && opts.protect_drifts && ~isempty(opts.drift_cols)
            dc = opts.drift_cols(:);
            dc = dc(dc >= 1 & dc <= size(X, 2));
            Sseg = Xseg(:, dc);
            if debug_mode
                fprintf('[DriftProtect] seg %d: drift_cols %s\n', s, mat2str(find(~all(Sseg == 0, 1))));
            end
            % Build projector P = I - S(S'S)^{-1}S'
            % Guard for rank deficiency
            if ~isempty(Sseg)
                [~, Ssv, Vsv] = svd(Sseg, 'econ'); %#ok<ASGLU>
                rS = sum(diag(Ssv) > 1e-8);
                if rS > 0
                    % Faster/robust projector via normal equations
                    Pseg = eye(size(Sseg, 1)) - Sseg * ((Sseg' * Sseg) \ Sseg');
                    Rseg_est = Pseg * Rseg; % use projected residuals for noise estimation
                else
                    Rseg_est = Rseg;
                end
            else
                Rseg_est = Rseg;
            end
        else
            Rseg_est = Rseg;
        end

        Tseg = size(Rseg, 1);

        % --- debug info START

        % determine effective method selected
        if Tseg < opts.min_seg_skip
            eff_method = 'identity';
        elseif Tseg < opts.min_seg_ar1
            eff_method = 'ar1(forced)';
        else
            eff_method = opts.method;
        end

        % if AR auto-select, note it later; placeholder
        eff_p = NaN;

        if strcmp(eff_method, 'arp') && isfield(opts, 'arp_auto') && opts.arp_auto
            % AR order will be chosen inside selector; we capture after
        end

        % store debug info
        if debug_mode
            debug_info.segment(end + 1, 1) = s;
            debug_info.length(end + 1, 1) = Tseg;
            debug_info.method{end + 1, 1} = eff_method;
            debug_info.iter(end + 1, 1) = opts.iterate; % if REML iteration enabled
            debug_info.p_order(end + 1, 1) = eff_p; % ~ filled post-hoc below
        end

        % --- debug info END

        % --- Short-segment rules:
        if Tseg < opts.min_seg_skip
            % Skip whitening: identity (pass-through)
            Yws = Yseg; Xws = Xseg;
            Yw = [Yw; Yws]; Xw = [Xw; Xws];
            continue
        elseif Tseg < opts.min_seg_ar1
            forced_method = 'ar1';
        else
            forced_method = opts.method;
        end

        switch forced_method
            case 'ar1'

                if strcmp(opts.pool, 'global')
                    rho = ar1_weighted_from_residuals(Rseg_est, w_parc);
                    [Yws, Xws] = whiten_ar1(Yseg, Xseg, rho);
                elseif strcmp(opts.pool, 'parcel')
                    % pooled first
                    rho_pool = ar1_weighted_from_residuals(Rseg_est, w_parc);
                    % per-parcel shrinkage & whitening (fit per parcel independently)
                    [Yws, Xws] = whiten_perparcel_ar1(Yseg, Xseg, Rseg_est, w_parc, rho_pool, opts.shrink_k);
                else
                    error('Unknown pool mode %s', opts.pool);
                end

            case 'arp'

                if strcmp(opts.pool, 'global') || strcmp(opts.pool, 'parcel')
                    if isfield(opts, 'arp_auto') && opts.arp_auto
                        psel = min(opts.arp_pmax, max(1, floor(Tseg / 8))); % cap by segment length
                        p_best = select_arp_order_AIC(Rseg_est, w_parc, psel);
                        debug_info.p_order(debug_info.segment == s) = p_best;
                        a_pool = arp_weighted_from_residuals(Rseg_est, p_best, w_parc);
                    else
                        a_pool = arp_weighted_from_residuals(Rseg_est, opts.order, w_parc);
                    end

                    if strcmp(opts.pool, 'global')
                        [Yws, Xws] = whiten_arp(Yseg, Xseg, a_pool);
                    elseif strcmp(opts.pool, 'parcel')
                        [Yws, Xws] = whiten_perparcel_arp(Yseg, Xseg, Rseg_est, w_parc, a_pool, opts.shrink_k);
                    end
                else
                    error('Unknown pool mode %s', opts.pool);
                end

            case 'arma11'

                if strcmp(opts.pool, 'global')
                    [phi, theta] = arma11_weighted_from_residuals(Rseg_est, w_parc);
                else
                    error('voxelwise ARMA not implemented yet');
                end

                [Yws, Xws] = whiten_arma11(Yseg, Xseg, phi, theta);

            case 'film'
                % PSD from pooled, weighted residuals in this segment
                psd = film_psd_weighted_from_residuals(Rseg_est, w_parc, opts);
                [Yws, Xws] = film_whiten_fft(Yseg, Xseg, psd, opts);

            otherwise
                error('Unknown whitening method %s', opts.method);
        end

        Yw = [Yw; Yws];
        Xw = [Xw; Xws];
    end

    if debug_mode
        fprintf('\n[GLM Whitening Debug]\n');

        fprintf('%-6s %-8s %-14s %-6s %-6s\n', 'Seg', 'Frames', 'Method', 'Iter', 'AR_p');
        fprintf('%s\n', repmat('-', 1, 50));

        for ii = 1:length(debug_info.segment)
            seg  = debug_info.segment(ii);
            nfr  = debug_info.length(ii);
            meth = debug_info.method{ii};
            iter = debug_info.iter(ii);
            arp  = debug_info.p_order(ii);

            if isnan(arp), arp_str = '-'; else, arp_str = sprintf('%d', arp); end

            fprintf('%-6d %-8d %-14s %-6d %-6s\n', seg, nfr, meth, iter, arp_str);
        end

        % summary counts
        methods = debug_info.method;
        fprintf('\nSegments summary:\n');
        fprintf('  identity skip (<%d frames): %d\n', opts.min_seg_skip, sum(strcmp(methods, 'identity')));
        fprintf('  forced AR1 (<%d frames):    %d\n', opts.min_seg_ar1, sum(strcmp(methods, 'ar1(forced)')));
        fprintf('  AR1 user:                   %d\n', sum(strcmp(methods, 'ar1')));
        fprintf('  AR(p):                      %d\n', sum(strcmp(methods, 'arp')));
        fprintf('  ARMA(1,1):                  %d\n', sum(strcmp(methods, 'arma11')));
        fprintf('  FILM:                       %d\n', sum(strcmp(methods, 'film')));

        if any(~isnan(debug_info.p_order))
            unique_orders = unique(debug_info.p_order(~isnan(debug_info.p_order)));
            fprintf('  AR auto-orders used:        %s\n', mat2str(unique_orders'));
        end
        fprintf('\n');
    end
end

%% --------- AR(1) weighted pooled ----------
function rho = ar1_weighted_from_residuals(Rseg, w)
    w = w(:) / sum(w);
    r1 = 0; r0 = 0;

    for p = 1:size(Rseg, 2)
        e = Rseg(:, p) - mean(Rseg(:, p), 'omitnan');
        r1 = r1 + w(p) * sum(e(2:end) .* e(1:end - 1));
        r0 = r0 + w(p) * sum(e(1:end - 1) .^ 2);
    end

    rho = r1 / (r0 + eps);
    rho = max(min(rho, 0.95), -0.95);
end

%% --------- AR(p) weighted pooled ----------
function a = arp_weighted_from_residuals(Rseg, p, w)
    w = w(:) / sum(w);
    g = zeros(p + 1, 1);

    for idx = 1:size(Rseg, 2)
        e = Rseg(:, idx) - mean(Rseg(:, idx), 'omitnan');

        for k = 0:p
            g(k + 1) = g(k + 1) + w(idx) * sum(e(1 + k:end) .* e(1:end - k));
        end

    end

    Gamma = toeplitz(g(1:p));
    gamma = g(2:p + 1);
    a = Gamma \ gamma;

    if any(abs(roots([1; -a])) >= 1)
        a = 0.99 * a / max(abs(roots([1; -a])));
    end

end

%% --------- Whitening filters ----------
function [Yw, Xw] = whiten_ar1(Y, X, rho)
    b = [1 -rho];
    Yw = filter(b, 1, Y);
    Xw = zeros(size(X));
    for j = 1:size(X, 2), Xw(:, j) = filter(b, 1, X(:, j)); end
end

function [Yw, Xw] = whiten_arp(Y, X, a)
    b = [1; -a(:)];
    Yw = filter(b, 1, Y);
    Xw = zeros(size(X));
    for j = 1:size(X, 2), Xw(:, j) = filter(b, 1, X(:, j)); end
end


%% ------- establishing parcel weights for pooling ----------
function w_parc = parcel_weights(obj, options)
    w_parc = ones(obj.voxels, 1);

    % -- check if we have parcel information

    if ~isempty(obj.cifti) && isfield(obj.cifti, 'metadata') && ...
            isfield(obj.cifti.metadata, 'diminfo') && ...
            length(obj.cifti.metadata.diminfo) >= 1 && ...
            isfield(obj.cifti.metadata.diminfo{1}, 'parcels') && ...
            isfield(obj.cifti.metadata.diminfo{1}.parcels, 'voxlist')

        if obj.voxels ~= length(obj.cifti.metadata.diminfo{1}.parcels)
            error('ERROR: Number of parcels does not match number of rows in the data!');
        end

        if options.debug_mode
            fprintf('--> Using parcel size as weights for prewhitening pooling\n');
        end
        for p = 1:obj.voxels
            w_parc(p) = size(obj.cifti.metadata.diminfo{1}.parcels(p).voxlist, 1);
            for s = 1:length(obj.cifti.metadata.diminfo{1}.parcels(p).surfs)
                w_parc(p) = w_parc(p) + length(obj.cifti.metadata.diminfo{1}.parcels(p).surfs(s).vertlist);
            end
        end
    end
end


%% --------- ARMA(1,1) weighted pooled ----------
function [phi, theta] = arma11_weighted_from_residuals(Rseg, w)

    % Normalize weights
    w = w(:) / sum(w);

    % Initial guess via AR(1)
    phi0 = ar1_weighted_from_residuals(Rseg, w);
    theta0 = 0;

    x0 = [phi0; theta0];

    % Bound transform: we optimize unbounded u, map to (-0.99,0.99)
    function x = invlogit(z)
        x = 1.98 * (exp(z) ./ (1 + exp(z))) - 0.99;
    end

    function z = logit(x)
        z = log((x + 0.99) ./ (0.99 - x));
    end

    z0 = logit([phi0; theta0]);

    opts = optimset('Display', 'off', 'TolX', 1e-6, 'TolFun', 1e-6, 'MaxIter', 200);

    zopt = fminsearch(@(z) arma11_negloglik(invlogit(z), Rseg, w), z0, opts);
    xopt = invlogit(zopt);

    phi = xopt(1);
    theta = xopt(2);

end


function nll = arma11_negloglik(x, Rseg, w)
    phi = x(1);
    theta = x(2);

    T = size(Rseg, 1);
    P = size(Rseg, 2);

    nll = 0;

    for p = 1:P
        e = Rseg(:, p) - mean(Rseg(:, p), 'omitnan');

        % ARMA(1,1) innovation recursion
        eps = zeros(size(e));

        for t = 2:length(e)
            eps(t) = e(t) - phi * e(t - 1) - theta * eps(t - 1);
        end

        var_eps = mean(eps .^ 2);

        % Gaussian negative log-likelihood weighted
        nll = nll + w(p) * (0.5 * T * log(var_eps) + 0.5 * sum(eps .^ 2) / var_eps);
    end

end


%% --------- ARMA(1,1) whitening filter ----------
function [Yw, Xw] = whiten_arma11(Y, X, phi, theta)

    % ARMA whitening filter: (1 - phi L) / (1 + theta L)
    b = [1 -phi];
    a = [1 theta];

    Yw = filter(b, a, Y);

    Xw = zeros(size(X));

    for j = 1:size(X, 2)
        Xw(:, j) = filter(b, a, X(:, j));
    end

end


%% --------- FILM-style PSD from residuals (weighted pooled) ----------
function psd = film_psd_weighted_from_residuals(Rseg, w, opts)
    % Rseg: [Tseg × P] residuals for this segment (demeaned per parcel here)
    % w:    [P×1] parcel weights (e.g., n_vox), will be normalized
    % opts: expects fields (with fallbacks inside)
    %   .film_maxlag (default: min(100, floor(Tseg/3)))
    %   .film_alpha  (default: 0.5)  % Tukey taper fraction
    %   .film_eps    (default: 1e-6) % PSD floor
    % Returns psd: [Tseg×1] nonnegative spectrum for circulant whitening

    Tseg = size(Rseg, 1);

    if ~isfield(opts, 'film_maxlag') || isempty(opts.film_maxlag)
        L = min(100, floor(Tseg / 3));
    else
        L = min(opts.film_maxlag, Tseg - 2);
    end

    if ~isfield(opts, 'film_alpha') || isempty(opts.film_alpha), opts.film_alpha = 0.5; end
    if ~isfield(opts, 'film_eps') || isempty(opts.film_eps), opts.film_eps = 1e-6; end

    % Normalize weights, demean residuals parcelwise
    w = w(:); w = w / max(sum(w), eps);
    E = Rseg - mean(Rseg, 1, 'omitnan'); % Tseg × P

    % Weighted unbiased autocovariances γ(k), k=0..L
    g = zeros(L + 1, 1);

    for p = 1:size(E, 2)
        e = E(:, p);

        for k = 0:L
            g(k + 1) = g(k + 1) + w(p) * (e(1 + k:end)' * e(1:end - k));
        end

    end

    % (optional) unbiased -> divide by (Tseg - k); stabilizes at high lag
    for k = 0:L
        g(k + 1) = g(k + 1) / max(Tseg - k, 1);
    end

    % Tukey (taper) window on ACF to reduce estimation noise
    tw = local_tukey(L + 1, opts.film_alpha); % length L+1
    g_tap = g .* tw(:);

    % Build symmetric ACF c of length Tseg for circulant embedding:
    % c(1)=γ(0); c(k+1)=γ(k); c(Tseg-k+1)=γ(k), k=1..L; the rest zero.
    c = zeros(Tseg, 1);
    c(1) = g_tap(1);

    for k = 1:L
        c(k + 1) = g_tap(k + 1);
        c(Tseg - k + 1) = g_tap(k + 1);
    end

    % PSD is FFT of the circulant ACF; force real & nonnegative
    psd = real(fft(c));
    psd = max(psd, opts.film_eps);

    % --- FAST-like spectral shrinkage (optional)
    lam = max(0, min(1, opts.fast_lambda));

    if lam > 0
        s = psd(:);

        if opts.fast_log
            s = log(s);
        end

        % simple centered moving-average smoother
        w = max(1, opts.fast_win);
        if mod(w, 2) == 0, w = w + 1; end
        half = floor(w / 2);
        s_pad = [s(half + 1:-1:2); s; s(end - 1:-1:end - half)]; % reflect-padding
        s_smooth = conv(s_pad, ones(w, 1) / w, 'valid'); % length matches s
        s_smooth = s_smooth(1:numel(s));

        if opts.fast_log
            psd_smooth = exp(s_smooth);
        else
            psd_smooth = s_smooth;
        end

        psd = max((1 - lam) * psd + lam * psd_smooth, opts.film_eps);
    end
end

%% --------- FILM whitening by FFT ----------
function [Yw, Xw] = film_whiten_fft(Yseg, Xseg, psd, opts)
    % Applies 1/sqrt(PSD) in frequency domain to Y and each column of X
    Tseg = size(Yseg, 1);
    W = 1 ./ sqrt(psd); % Tseg×1
    W = W(:);

    % FFT along time; multiply; IFFT back (real part)
    FY = fft(Yseg, [], 1);
    FY = bsxfun(@times, FY, W);
    Yw = real(ifft(FY, [], 1));

    Xw = zeros(size(Xseg));
    FX = fft(Xseg, [], 1);
    FX = bsxfun(@times, FX, W);
    Xw = real(ifft(FX, [], 1));
end

%% --------- Minimal Tukey window (toolbox-free) ----------
function w = local_tukey(N, alpha)
    % N: length, alpha in [0,1]. alpha=0 -> rectangular, alpha=1 -> Hann
    if alpha <= 0
        w = ones(N, 1);
        return;
    elseif alpha >= 1
        n = (0:N - 1)';
        w = 0.5 * (1 - cos(2 * pi * n / (N - 1)));
        return;
    end

    w = ones(N, 1);
    % cosine tapers on both ends of length a = floor(alpha*(N-1)/2)
    a = floor(alpha * (N - 1) / 2);
    n = (0:N - 1)';
    % left taper
    idx = n <= a;
    w(idx) = 0.5 * (1 + cos(pi * (2 * n(idx) / (alpha * (N - 1)) - 1)));
    % right taper
    idx = n >= (N - 1 - a);
    w(idx) = 0.5 * (1 + cos(pi * (2 * (n(idx) - (N - 1)) / (alpha * (N - 1)) + 1)));
end


function [Yw_all, Xw_all] = whiten_perparcel_ar1(Yseg, Xseg, Rseg, w_parc, rho_pool, k)
    % Fit/whiten per parcel; shrink AR(1) toward pooled
    P = size(Yseg, 2);
    Yw_all = zeros(size(Yseg));
    Xw_all = zeros(size(Xseg, 1), size(Xseg, 2), P); % each parcel needs its own X after filtering

    for p = 1:P
        e = Rseg(:, p) - mean(Rseg(:, p), 'omitnan');
        rho_raw = (e(2:end)' * e(1:end - 1)) / (e(1:end - 1)' * e(1:end - 1) + eps);
        rho_raw = max(min(rho_raw, 0.95), -0.95);

        m = max(1, w_parc(p));
        lambda = m / (m + k);
        rho = lambda * rho_raw + (1 - lambda) * rho_pool;

        [Yw_p, Xw_p] = whiten_ar1(Yseg(:, p), Xseg, rho); % note: Xseg filtered separately for this parcel
        Yw_all(:, p) = Yw_p;
        Xw_all(:, :, p) = Xw_p;
    end
end



function [Yw_all, Xw_all] = whiten_perparcel_arp(Yseg, Xseg, Rseg, w_parc, a_pool, k)

    P = size(Yseg, 2); % number of voxels/parcel components
    T = size(Yseg, 1); % time points
    npred = size(Xseg, 2);

    Yw_all = zeros(T, P);
    Xw_all = zeros(T, npred, P);

    pord = length(a_pool); % pooled AR order

    for p = 1:P
        e = Rseg(:, p) - mean(Rseg(:, p), 'omitnan');

        % estimate AR coeffs for this parcel, same order as pooled
        a_raw = local_arp_from_e(e, pord);

        % shrink toward pooled AR coeffs
        m = max(1, w_parc(p));
        lambda = m / (m + k);
        a = lambda * a_raw + (1 - lambda) * a_pool;

        % whiten this parcel's time series and design
        [Yw_p, Xw_p] = whiten_arp(Yseg(:, p), Xseg, a);

        Yw_all(:, p) = Yw_p;
        Xw_all(:, :, p) = Xw_p;
    end
end



function a = local_arp_from_e(e, p)
    e = e - mean(e, 'omitnan'); L = numel(e);
    g = zeros(p + 1, 1);
    for k = 0:p, g(k + 1) = sum(e(1 + k:end) .* e(1:end - k)) / max(L - k, 1); end
    Gamma = toeplitz(g(1:p)); gamma = g(2:p + 1);
    a = Gamma \ gamma;
    % stabilize if needed
    if any(abs(roots([1; -a])) >= 1)
        a = 0.99 * a / max(1e-6, max(abs(roots([1; -a]))));
    end

end



function p_best = select_arp_order_AIC(Rseg, w, pmax)
    % Weighted pooled AIC selection for AR(p)
    best = inf; p_best = 1;

    for p = 1:pmax
        a = arp_weighted_from_residuals(Rseg, p, w);
        % Innovation variance via one-step ahead residuals
        T = size(Rseg, 1); P = size(Rseg, 2);
        nll = 0; kpar = p; % number of parameters

        for j = 1:P
            e = Rseg(:, j) - mean(Rseg(:, j), 'omitnan');
            v = zeros(T, 1);

            for t = p + 1:T
                v(t) = e(t) - a' * e(t - 1:-1:t - p);
            end

            sig2 = mean(v(p + 1:end) .^ 2);
            nll = nll + w(j) * (0.5 * (T - p) * log(sig2) + 0.5 * sum(v(p + 1:end) .^ 2) / sig2);
        end

        AIC = 2 * kpar + 2 * nll;
        if AIC < best, best = AIC; p_best = p; end
    end

end


function drift_cols = detect_drift_cols_from_X(X, seg_id, tol, maxperseg)
    % Conservative detector: a column is "drift" if it is (almost) explainable
    % by per-segment intercept and (optionally) linear trend: R^2 >= tol.
    % At most maxperseg*#segments columns are flagged.
    if nargin < 3 || isempty(tol), tol = 0.9995; end
    if nargin < 4 || isempty(maxperseg), maxperseg = 2; end

    segs = unique(seg_id(:)); segs(isnan(segs)) = [];
    T = size(X, 1); P = size(X, 2);

    % Build block design for segment-wise intercept + slope
    S = [];

    for s = segs'
        idx = find(seg_id == s);
        t = (0:numel(idx) - 1)'; % 0..(len-1) within-segment
        Ss = [ones(numel(idx), 1), detrend(t, 'constant')]; % intercept + centered slope
        S = blkdiag(S, Ss);
    end

    % Fast pseudo-inverse once
    StS = S' * S; StS_inv = pinv_safe(StS);
    Pperp = @(v) v - S * (StS_inv * (S' * v)); % projection residuals

    drift_cols = [];

    for j = 1:P
        xj = X(:, j);
        r = Pperp(xj);
        R2 = 1 - (r' * r) / max((xj - mean(xj))' * (xj - mean(xj)), eps);

        if R2 >= tol
            drift_cols(end + 1) = j; %#ok<AGROW>
        end

    end

    % Limit number (safety guard)
    maxcols = maxperseg * numel(segs);

    if numel(drift_cols) > maxcols
        % Keep the best-fitting ones (highest R^2)
        R2s = zeros(numel(drift_cols), 1);

        for k = 1:numel(drift_cols)
            xj = X(:, drift_cols(k));
            r = Pperp(xj);
            R2s(k) = 1 - (r' * r) / max((xj - mean(xj))' * (xj - mean(xj)), eps);
        end

        [~, ord] = sort(R2s, 'descend');
        drift_cols = drift_cols(ord(1:maxcols));
    end

    drift_cols = unique(drift_cols);
end

function Ainv = pinv_safe(A)
    % Small helper to avoid warnings in Octave/MATLAB
    [U, S, V] = svd(A, 'econ');
    s = diag(S);
    thr = max(size(A)) * eps(max(s));
    s(s < thr) = 0;
    s(s > 0) = 1 ./ s(s > 0);
    Ainv = V * diag(s) * U';
end
