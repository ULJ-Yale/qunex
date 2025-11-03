function [Yws, Xws, meta] = glm_whiten_film_strong(Xseg, Yseg, Rseg_est, opts, w_parc)
%``function [Yws, Xws, meta] = glm_whiten_film_strong(Xseg, Yseg, Rseg_est, opts, w_parc)``
%
%   FILM-style (frequency-domain) whitening for a single segment (STRONG).
%   This variant follows the same pipeline as `glm_whiten_film` but applies
%   more aggressive defaults to better suppress temporal autocorrelation:
%     - Longer ACF truncation (film_maxlag) unless user-specified
%     - Stronger FAST-style spectral smoothing (lambda, window, log-domain)
%     - Optional reflect padding to mitigate circular FFT artifacts
%     - Fewer low-frequency "unity" bins (can be tuned)
%
%   Inputs:
%       Xseg (matrix [T x p])
%           Design segment.
%
%       Yseg (matrix [T x V])
%           Data segment (voxels/parcels in columns).
%
%       Rseg_est (matrix [T x V])
%           Residuals for noise estimation (drift-protected upstream, if used).
%
%       opts (struct)
%           Options (see `glm_whiten_config`). Relevant fields include:
%             - film_maxlag, film_alpha, film_eps
%             - fast_lambda, fast_win, fast_log
%             - film_lowbins_unity, film_padlen
%
%       w_parc (vector [V x 1], default ones)
%           Pooling weights (e.g., parcel sizes) for PSD estimation.
%
%   Outputs:
%       Yws (matrix [T x V])
%           Whitened data (same size as Yseg).
%
%       Xws (matrix [T x p])
%           Whitened design (global filter).
%
%       meta (struct)
%           FILM details:
%           .psd_len, .film_maxlag, .fast_lambda, .lowbins_unity, .padlen, .W, .kind
%
%   Notes:
%       - Use when `glm_whiten_film` leaves residual short-lag AC. This trades
%         mild bias risk for stronger AC suppression.
%       - MATLAB/Octave compatible; relies on local helpers shared with FILM.
%

% SPDX-FileCopyrightText: 2025 QuNex development team
%
% SPDX-License-Identifier: GPL-3.0-or-later

    T = size(Xseg, 1);
    if nargin < 5 || isempty(w_parc), w_parc = ones(size(Yseg, 2), 1); end
    w_parc = w_parc(:);

    % --------- STRONG defaults (soft) ----------
    eff = struct();
    eff.film_alpha = getfield_def(opts, 'film_alpha', 0.7);
    eff.film_eps = getfield_def(opts, 'film_eps', 1e-6);
    eff.fast_lambda = getfield_def(opts, 'fast_lambda', 0.10);
    eff.fast_win = getfield_def(opts, 'fast_win', 11);
    eff.fast_log = getfield_def(opts, 'fast_log', true);
    eff.film_lowbins_unity = getfield_def(opts, 'film_lowbins_unity', 1);
    eff.film_padlen = getfield_def(opts, 'film_padlen', min(30, max(0, floor(T / 10))));

    % maxlag — longer than classic FILM unless user-specified
    if isfield(opts, 'film_maxlag') && ~isempty(opts.film_maxlag)
        eff.film_maxlag = max(1, min(T - 2, round(opts.film_maxlag)));
    else
        eff.film_maxlag = max(40, min(min(180, T - 2), round(0.4 * T)));
    end

    % merge into copy of opts
    loc = opts;
    fn = fieldnames(eff);

    for i = 1:numel(fn)
        loc.(fn{i}) = eff.(fn{i});
    end

    % --------- PSD estimation ---------
    [psd, eff_maxlag] = local_film_psd_weighted(Rseg_est, w_parc, loc);

    % --------- Whiten via FFT ---------
    [Yws, Xws, W, pad] = local_film_whiten_fft(Yseg, Xseg, psd, loc);

    % --------- meta info ---------
    meta = struct();
    meta.kind = 'film_strong';
    meta.psd_len = numel(psd);
    meta.film_maxlag = eff_maxlag;
    meta.fast_lambda = loc.fast_lambda;
    meta.lowbins_unity = loc.film_lowbins_unity;
    meta.padlen = pad; % real pad used
    meta.W = W; % whitening filter used
end

% ======================================================================
% PSD estimation (pooled)
% ======================================================================
function [psd, eff_maxlag] = local_film_psd_weighted(Rseg, w, opts)
    T = size(Rseg, 1);

    if ~isfield(opts, 'film_maxlag') || isempty(opts.film_maxlag)
        L = min(100, floor(T / 3));
    else
        L = min(max(1, round(opts.film_maxlag)), T - 2);
    end

    eff_maxlag = L;

    alpha = getfield_def(opts, 'film_alpha', 0.5);
    epsf = getfield_def(opts, 'film_eps', 1e-6);

    w = w(:); w = w / max(sum(w), eps);
    E = Rseg - mean(Rseg, 1, 'omitnan');

    g = zeros(L + 1, 1);

    for v = 1:size(E, 2)
        e = E(:, v);

        for k = 0:L
            g(k + 1) = g(k + 1) + w(v) * (e(1 + k:end)' * e(1:end - k));
        end

    end

    for k = 0:L, g(k + 1) = g(k + 1) / max(T - k, 1); end

    tw = local_tukey(L + 1, alpha);
    gtp = g .* tw(:);

    c = zeros(T, 1);
    c(1) = gtp(1);

    for k = 1:L
        c(k + 1) = gtp(k + 1);
        c(T - k + 1) = gtp(k + 1);
    end

    psd = real(fft(c));
    psd = max(psd, epsf);

    lam = max(0, min(1, getfield_def(opts, 'fast_lambda', 0.1)));

    if lam > 0
        s = psd(:);
        if getfield_def(opts, 'fast_log', true), s = log(s); end

        win = max(3, round(getfield_def(opts, 'fast_win', 11)));
        if mod(win, 2) == 0, win = win + 1; end

        half = floor(win / 2);
        s_pad = [s(half + 1:-1:2); s; s(end - 1:-1:end - half)];
        s_smooth = conv(s_pad, ones(win, 1) / win, 'valid');
        s_smooth = s_smooth(1:numel(s));

        if getfield_def(opts, 'fast_log', true)
            psd_s = exp(s_smooth);
        else
            psd_s = s_smooth;
        end

        psd = max((1 - lam) * psd + lam * psd_s, getfield_def(opts, 'film_eps', 1e-6));
    end

end

% ======================================================================
% FFT-domain whitening
% ======================================================================
function [Yw, Xw, W, pad] = local_film_whiten_fft(Yseg, Xseg, psd, opts)
    T = size(Yseg, 1);
    pad = max(0, round(getfield_def(opts, 'film_padlen', 0)));
    pad = min(pad, max(0, T - 2));

    % ---------- Padding path ----------
    if pad > 0
        Ypad = [flipud(Yseg(1:pad, :)); Yseg; flipud(Yseg(end - pad + 1:end, :))];
        Xpad = zeros(size(Ypad, 1), size(Xseg, 2));

        for j = 1:size(Xseg, 2)
            xj = Xseg(:, j);
            Xpad(:, j) = [flipud(xj(1:pad)); xj; flipud(xj(end - pad + 1:end))];
        end

        c = real(ifft(psd)); % ACF
        Np = size(Ypad, 1);
        cpad = zeros(Np, 1);
        cpad(1:numel(c)) = c;
        psd_p = real(fft(cpad));
        psd_p = max(psd_p, getfield_def(opts, 'film_eps', 1e-6));

        W = 1 ./ sqrt(psd_p);
        K = max(0, round(getfield_def(opts, 'film_lowbins_unity', 1)));

        if K > 0
            W(1:K) = 1;
            for k = 1:K - 1, W(end - k + 1) = 1; end
        end

        FY = fft(Ypad); FY = FY .* W;
        Ywp = real(ifft(FY));
        Yw = Ywp(1 + pad:pad + T, :);

        FX = fft(Xpad); FX = FX .* W;
        Xwp = real(ifft(FX));
        Xw = Xwp(1 + pad:pad + T, :);

        % ---------- No-pad path ----------
    else
        W = 1 ./ sqrt(psd);
        K = max(0, round(getfield_def(opts, 'film_lowbins_unity', 1)));

        if K > 0
            W(1:K) = 1;
            for k = 1:K - 1, W(end - k + 1) = 1; end
        end

        FY = fft(Yseg); FY = FY .* W;
        Yw = real(ifft(FY));

        FX = fft(Xseg); FX = FX .* W;
        Xw = real(ifft(FX));
    end

end

% ======================================================================
% Utilities
% ======================================================================
function val = getfield_def(s, f, def)

    if isfield(s, f) && ~isempty(s.(f)), val = s.(f);
    else , val = def;
    end

end

function w = local_tukey(N, alpha)

    if alpha <= 0
        w = ones(N, 1); return;
    elseif alpha >= 1
        n = (0:N - 1)'; w = 0.5 * (1 - cos(2 * pi * n / (N - 1))); return;
    end

    n = (0:N - 1)';
    w = ones(N, 1);
    a = floor(alpha * (N - 1) / 2);
    idx = n <= a;
    w(idx) = 0.5 * (1 + cos(pi * (2 * n(idx) / (alpha * (N - 1)) - 1)));
    idx = n >= (N - 1 - a);
    w(idx) = 0.5 * (1 + cos(pi * (2 * (n(idx) - (N - 1)) / (alpha * (N - 1)) + 1)));
end
