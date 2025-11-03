function [Yws, Xws, meta] = glm_whiten_ar(method, Xseg, Yseg, Rseg_est, opts, w_parc)
%``function [Yws, Xws, meta] = glm_whiten_ar(method, Xseg, Yseg, Rseg_est, opts, w_parc)``
%
%   Implement AR-based whitening methods:
%     - 'ar1'    : AR(1) pooled (global) or per-parcel with shrinkage
%     - 'arp'    : AR(p) pooled (global) or per-parcel with shrinkage (+ auto-p)
%     - 'arma11' : ARMA(1,1) pooled globally (per-voxel ARMA not implemented)
%
%   Inputs:
%       method (char)
%           'ar1' | 'arp' | 'arma11'
%
%       Xseg (matrix [T x p])
%           Design segment
%
%       Yseg (matrix [T x V])
%           Data segment (voxels/parcels in columns)
%
%       Rseg_est (matrix [T x V])
%           Residuals for noise estimation (drift-protected)
%
%       opts (struct)
%           Options (glm_whiten_config)
%
%       w_parc (vector [V x 1])
%           Pooling weights (e.g., parcel sizes)
%
%   Outputs:
%       Yws (matrix [T x V])
%           Whitened Y segment
%
%       Xws (matrix or 3-D)
%           Whitened X segment; global [T x p], parcel [T x p x V]
%
%       meta (struct)
%           Fields include .arp_order (NaN for ar1/arma11)
%

% SPDX-FileCopyrightText: 2025 QuNex development team
%
% SPDX-License-Identifier: GPL-3.0-or-later

    V = size(Yseg, 2);
    T = size(Yseg, 1);
    p = size(Xseg, 2);

    if nargin < 6 || isempty(w_parc)
        w_parc = ones(V, 1);
    end

    w_parc = w_parc(:);

    meta = struct('arp_order', NaN);

    switch method

            % ------------------------------------------------------------
            % AR(1)
            % ------------------------------------------------------------
        case 'ar1'

            if strcmp(opts.pool, 'global')
                rho = ar1_weighted_from_residuals(Rseg_est, w_parc);
                [Yws, Xws] = whiten_ar1(Yseg, Xseg, rho);

            elseif strcmp(opts.pool, 'parcel')
                rho_pool = ar1_weighted_from_residuals(Rseg_est, w_parc);
                k = opts.shrink_k;
                [Yws, Xws] = whiten_perparcel_ar1(Yseg, Xseg, Rseg_est, w_parc, rho_pool, k);

            else
                error('glm_whiten_ar: unknown pool mode "%s".', opts.pool);
            end

            % ------------------------------------------------------------
            % AR(p)  (pooled or per-parcel with shrinkage)
            % ------------------------------------------------------------
        case 'arp'
            % Choose order
            if isfield(opts, 'arp_auto') && opts.arp_auto
                psel = min(opts.arp_pmax, max(1, floor(T / 8))); % crude cap vs length
                pord = select_arp_order_AIC(Rseg_est, w_parc, psel);
                meta.arp_order = pord;
            else
                pord = max(1, round(opts.order));
                meta.arp_order = pord;
            end

            a_pool = arp_weighted_from_residuals(Rseg_est, pord, w_parc);

            if strcmp(opts.pool, 'global')
                [Yws, Xws] = whiten_arp(Yseg, Xseg, a_pool);

            elseif strcmp(opts.pool, 'parcel')
                k = opts.shrink_k;
                [Yws, Xws] = whiten_perparcel_arp(Yseg, Xseg, Rseg_est, w_parc, a_pool, k);

            else
                error('glm_whiten_ar: unknown pool mode "%s".', opts.pool);
            end

            % ------------------------------------------------------------
            % ARMA(1,1)  (global only)
            % ------------------------------------------------------------
        case 'arma11'

            if ~strcmp(opts.pool, 'global')
                error('glm_whiten_ar: ARMA(1,1) voxelwise/parcel mode not implemented.');
            end

            [phi, theta] = arma11_weighted_from_residuals(Rseg_est, w_parc);
            [Yws, Xws] = whiten_arma11(Yseg, Xseg, phi, theta);

        otherwise
            error('glm_whiten_ar: unknown method "%s".', method);
    end

end

% ============================================================
%                    Pooled parameter estimation
% ============================================================

function rho = ar1_weighted_from_residuals(Rseg, w)
    % Weighted lag-1 autocorrelation across columns
    w = w(:) / max(sum(w), eps);
    r1 = 0; r0 = 0;

    for v = 1:size(Rseg, 2)
        e = Rseg(:, v) - mean(Rseg(:, v), 'omitnan');
        r1 = r1 + w(v) * sum(e(2:end) .* e(1:end - 1));
        r0 = r0 + w(v) * sum(e(1:end - 1) .^ 2);
    end

    rho = r1 / (r0 + eps);
    % stability clamp
    rho = sign(rho) * min(abs(rho), 0.90);
end

function a = arp_weighted_from_residuals(Rseg, pord, w)
    % Weighted Yule–Walker solve for pooled AR(p)
    w = w(:) / max(sum(w), eps);
    g = zeros(pord + 1, 1);

    for v = 1:size(Rseg, 2)
        e = Rseg(:, v) - mean(Rseg(:, v), 'omitnan');

        for k = 0:pord
            g(k + 1) = g(k + 1) + w(v) * sum(e(1 + k:end) .* e(1:end - k));
        end

    end

    % unbiased-ish
    Tseg = size(Rseg, 1);

    for k = 0:pord
        g(k + 1) = g(k + 1) / max(Tseg - k, 1);
    end

    Gamma = toeplitz(g(1:pord));
    gamma = g(2:pord + 1);
    a = Gamma \ gamma;
    % stabilize if needed
    r = roots([1; -a]);
    rmax = max(abs(r));

    if any(abs(r) >= 1)
        a = 0.90 * a / max(rmax, 1e-6);
    end

end

function p_best = select_arp_order_AIC(Rseg, w, pmax)
    % Weighted pooled AIC selection for AR(p)
    best = inf; p_best = 1;
    T = size(Rseg, 1);
    V = size(Rseg, 2);
    w = w(:) / max(sum(w), eps);

    for p = 1:pmax
        a = arp_weighted_from_residuals(Rseg, p, w);
        % Innovation variance via one-step-ahead residuals
        nll = 0; kpar = p;

        for v = 1:V
            e = Rseg(:, v) - mean(Rseg(:, v), 'omitnan');
            vhat = zeros(T, 1);

            for t = p + 1:T
                vhat(t) = e(t) - a' * e(t - 1:-1:t - p);
            end

            sig2 = mean(vhat(p + 1:end) .^ 2);
            nll = nll + w(v) * (0.5 * (T - p) * log(sig2) + 0.5 * sum(vhat(p + 1:end) .^ 2) / sig2);
        end

        AIC = 2 * kpar + 2 * nll;

        if AIC < best
            best = AIC; p_best = p;
        end

    end

end

function [phi, theta] = arma11_weighted_from_residuals(Rseg, w)
    % Simple weighted Gaussian likelihood fit for ARMA(1,1)
    w = w(:) / max(sum(w), eps);

    % initial from AR(1)
    rho0 = ar1_weighted_from_residuals(Rseg, w);
    x0 = [rho0; 0]; % [phi; theta]

    % map (-0.99,0.99) <-> R
    invlogit = @(z) (1.98 * (exp(z) ./ (1 + exp(z))) - 0.99);
    logit = @(x) log((x + 0.99) ./ (0.99 - x));

    z0 = logit(x0);

    obj = @(z) arma11_negloglik(invlogit(z), Rseg, w);

    opts = optimset('Display', 'off', 'TolX', 1e-6, 'TolFun', 1e-6, 'MaxIter', 200);
    zopt = fminsearch(obj, z0, opts);
    xopt = invlogit(zopt);

    phi = xopt(1);
    theta = xopt(2);

    % stability gentle clamp
    phi = sign(phi) * min(abs(phi), 0.90);
    theta = sign(theta) * min(abs(theta), 0.90);
end

function nll = arma11_negloglik(x, Rseg, w)
    phi = x(1);
    theta = x(2);

    [T, V] = size(Rseg);
    w = w(:) / max(sum(w), eps);
    nll = 0;

    for v = 1:V
        e = Rseg(:, v) - mean(Rseg(:, v), 'omitnan');
        epshat = zeros(T, 1);

        for t = 2:T
            epshat(t) = e(t) - phi * e(t - 1) - theta * epshat(t - 1);
        end

        sig2 = mean(epshat .^ 2);
        nll = nll + w(v) * (0.5 * T * log(sig2) + 0.5 * sum(epshat .^ 2) / sig2);
    end

end

% ============================================================
%                      Whitening filters
% ============================================================

function [Yw, Xw] = whiten_ar1(Y, X, rho)
    % Filter: (1 - rho L)
    b = [1, -rho];
    a = 1;
    Yw = filter(b, a, Y); % vectorized across columns
    Xw = filter(b, a, X); % vectorized across columns
end

function [Yw, Xw] = whiten_arp(Y, X, a)
    % Filter: A(L) = 1 - a1 L - ... - ap L^p
    b = [1; -a(:)].';
    a_tf = 1;
    Yw = filter(b, a_tf, Y);
    Xw = filter(b, a_tf, X);
end

function [Yw, Xw] = whiten_arma11(Y, X, phi, theta)
    % Filter: (1 - phi L) / (1 + theta L)
    b = [1, -phi];
    a = [1, theta];
    Yw = filter(b, a, Y);
    Xw = filter(b, a, X);
end

% ============================================================
%                Parcel-wise (per-voxel) whitening
% ============================================================

function [Yw_all, Xw_all] = whiten_perparcel_ar1(Yseg, Xseg, Rseg, w_parc, rho_pool, k)
    % Per-voxel AR(1) with shrinkage toward pooled rho
    [T, p] = size(Xseg);
    V = size(Yseg, 2);
    Yw_all = zeros(T, V);
    Xw_all = zeros(T, p, V);

    for v = 1:V
        e = Rseg(:, v) - mean(Rseg(:, v), 'omitnan');
        % raw AR(1)
        r0 = e(1:end - 1)' * e(1:end - 1);
        r1 = e(2:end)' * e(1:end - 1);
        rho_raw = r1 / (r0 + eps);
        rho_raw = sign(rho_raw) * min(abs(rho_raw), 0.90);

        m = max(1, w_parc(v));
        lambda = m / (m + k);
        rho = lambda * rho_raw + (1 - lambda) * rho_pool;

        [Yw_v, Xw_v] = whiten_ar1(Yseg(:, v), Xseg, rho);
        Yw_all(:, v) = Yw_v;
        Xw_all(:, :, v) = Xw_v;
    end

end

function [Yw_all, Xw_all] = whiten_perparcel_arp(Yseg, Xseg, Rseg, w_parc, a_pool, k)
    % Per-voxel AR(p) with shrinkage toward pooled a_pool
    [T, p] = size(Xseg);
    V = size(Yseg, 2);
    Yw_all = zeros(T, V);
    Xw_all = zeros(T, p, V);

    pord = numel(a_pool);

    for v = 1:V
        e = Rseg(:, v) - mean(Rseg(:, v), 'omitnan');
        a_raw = local_arp_from_e(e, pord);

        m = max(1, w_parc(v));
        lambda = m / (m + k);
        a = lambda * a_raw + (1 - lambda) * a_pool;

        [Yw_v, Xw_v] = whiten_arp(Yseg(:, v), Xseg, a);
        Yw_all(:, v) = Yw_v;
        Xw_all(:, :, v) = Xw_v;
    end

end

% ============================================================
%                 AR(p) from a single vector e
% ============================================================
function a = local_arp_from_e(e, pord)
    e = e - mean(e, 'omitnan');
    L = numel(e);
    g = zeros(pord + 1, 1);

    for k = 0:pord
        g(k + 1) = sum(e(1 + k:end) .* e(1:end - k)) / max(L - k, 1);
    end

    Gamma = toeplitz(g(1:pord));
    gamma = g(2:pord + 1);
    a = Gamma \ gamma;

    % stabilize if roots outside unit circle
    r = roots([1; -a]);
    rmax = max(abs(r));

    if any(abs(r) >= 1)
        a = 0.90 * a / max(rmax, 1e-6);
    end

end
