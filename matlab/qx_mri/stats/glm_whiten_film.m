function [Yws, Xws, meta] = glm_whiten_film(Xseg, Yseg, Rseg_est, opts, w_parc)
%``function [Yws, Xws, meta] = glm_whiten_film(Xseg, Yseg, Rseg_est, opts, w_parc)``
%
%   FILM-style (frequency-domain) whitening for a single segment.
%   - Pooled, weighted PSD estimate from residuals (with optional drift protection upstream)
%   - Tukey-tapered ACF → circulant embedding → FFT PSD
%   - Optional FAST-like spectral smoothing (lambda, window, log-domain)
%   - Optional reflect padding to mitigate circular FFT artifacts
%   - Optional low-frequency unity bins to protect DC/ultra-low frequencies
%
%   Inputs:
%       Xseg (matrix [T x p])
%           Design segment.
%
%       Yseg (matrix [T x V])
%           Data segment (voxels/parcels in columns).
%
%       Rseg_est (matrix [T x V])
%           Residuals for noise estimation (drift-protected upstream).
%
%       opts (struct)
%           Options from glm_whiten_config.
%
%       w_parc (vector [V x 1], default ones)
%           Pooling weights (e.g., parcel sizes).
%
%   Outputs:
%       Yws (matrix [T x V])
%           Whitened data.
%
%       Xws (matrix [T x p])
%           Whitened design (global filter).
%
%       meta (struct)
%           FILM details:
%           .psd_len, .film_maxlag, .fast_lambda, .lowbins_unity, .padlen, .W, .kind
%

% SPDX-FileCopyrightText: 2025 QuNex development team
%
% SPDX-License-Identifier: GPL-3.0-or-later

    T = size(Xseg, 1);

    if nargin < 5 || isempty(w_parc)
        w_parc = ones(size(Yseg, 2), 1);
    end

    w_parc = w_parc(:);

    % --------- 1) PSD estimate from residuals ----------
    [psd, eff_maxlag] = local_film_psd_weighted(Rseg_est, w_parc, opts);

    % --------- 2) FFT-domain whitening (optional padding + low-freq unity) ----------
    [Yws, Xws, W, pad] = local_film_whiten_fft(Yseg, Xseg, psd, opts);

    % --------- 3) Meta ----------
    meta = struct();
    meta.psd_len = numel(psd);
    meta.film_maxlag = eff_maxlag;
    meta.fast_lambda = getfield_def(opts, 'fast_lambda', 0.25);
    meta.lowbins_unity = getfield_def(opts, 'film_lowbins_unity', 2);
    meta.padlen = pad;
    meta.W = W(:);
    meta.kind = 'film';
end

% ======================================================================
%                      PSD estimation (pooled)
% ======================================================================
function [psd, eff_maxlag] = local_film_psd_weighted(Rseg, w, opts)
    % Weighted pooled ACF, Tukey-tapered, circulant-embedded, PSD via FFT
    T = size(Rseg, 1);

    if ~isfield(opts, 'film_maxlag') || isempty(opts.film_maxlag)
        L = min(100, floor(T / 3));
    else
        L = min(max(1, round(opts.film_maxlag)), T - 2);
    end

    eff_maxlag = L;

    alpha = getfield_def(opts, 'film_alpha', 0.5);
    epsf = getfield_def(opts, 'film_eps', 1e-6);

    % Normalize weights and demean residuals per column
    w = w(:);
    w = w / max(sum(w), eps);
    E = Rseg - mean(Rseg, 1, 'omitnan'); % [T x V]

    % Weighted autocovariances g(0..L)
    g = zeros(L + 1, 1);

    for v = 1:size(E, 2)
        e = E(:, v);

        for k = 0:L
            g(k + 1) = g(k + 1) + w(v) * (e(1 + k:end)' * e(1:end - k));
        end

    end

    % --- Biased normalization (divide by T) for better PSD stability
    g = g / max(T, 1);

    % Tukey-taper on ACF
    tw = local_tukey(L + 1, alpha);
    gtp = g .* tw(:);

    % Circulant ACF of length T: c(1)=g0, c(k+1)=gk, c(T-k+1)=gk
    c = zeros(T, 1);
    c(1) = gtp(1);

    for k = 1:L
        c(k + 1) = gtp(k + 1);
        c(T - k + 1) = gtp(k + 1);
    end

    % PSD via FFT (real, non-negative, floored)
    psd = real(fft(c));
    psd = max(psd, epsf);

    % FAST-like spectral smoothing (optional)
    lam = max(0, min(1, getfield_def(opts, 'fast_lambda', 0.25)));

    if lam > 0
        s = psd(:);
        if getfield_def(opts, 'fast_log', true), s = log(s); end

        win = max(3, round(getfield_def(opts, 'fast_win', 9)));
        if mod(win, 2) == 0, win = win + 1; end
        half = floor(win / 2);

        % reflect-pad and uniform moving average
        s_pad = [s(half + 1:-1:2); s; s(end - 1:-1:end - half)];
        s_smooth = conv(s_pad, ones(win, 1) / win, 'valid');
        s_smooth = s_smooth(1:numel(s));

        if getfield_def(opts, 'fast_log', true)
            psd_s = exp(s_smooth);
        else
            psd_s = s_smooth;
        end

        psd = max((1 - lam) * psd + lam * psd_s, epsf);
    end

    % --- Rescale PSD so mean(psd) matches tapered variance gtp(1)
    mpsd = mean(psd);

    if mpsd > 0
        target = gtp(1); % variance after tapering
        psd = psd * (target / mpsd);
        psd = max(psd, epsf);
    end

end

% ======================================================================
%                    FFT-domain whitening filter
% ======================================================================
function [Yw, Xw, W, pad] = local_film_whiten_fft(Yseg, Xseg, psd, opts)
    T = size(Yseg, 1);

    pad = max(0, round(getfield_def(opts, 'film_padlen', 0)));
    pad = min(pad, max(0, T - 2)); % keep at least 2 unpadded points

    if pad > 0
        % ---- reflect pad data/design ----
        Ypad = [flipud(Yseg(1:pad, :)); Yseg; flipud(Yseg(end - pad + 1:end, :))];

        Xw = zeros(T, size(Xseg, 2)); % allocate output (un-padded)
        Xpad = zeros(size(Ypad, 1), size(Xseg, 2));

        for j = 1:size(Xseg, 2)
            xj = Xseg(:, j);
            Xpad(:, j) = [flipud(xj(1:pad)); xj; flipud(xj(end - pad + 1:end))];
        end

        % ---- expand PSD length to padded length via zero-padded ACF ----
        c = real(ifft(psd, [], 1)); % back to ACF of len T (circulant)
        Np = size(Ypad, 1);
        cpad = zeros(Np, 1);
        cpad(1:numel(c)) = c;
        psd_pad = real(fft(cpad));
        psd_pad = max(psd_pad, getfield_def(opts, 'film_eps', 1e-6));

        W = 1 ./ sqrt(psd_pad);

        % low-frequency unity bins
        K = max(0, round(getfield_def(opts, 'film_lowbins_unity', 2)));

        if K > 0
            W(1:K) = 1;
            for k = 1:K - 1, W(end - k + 1) = 1; end
        else
            % DC guard even when lowbins_unity==0 (prevent amplification)
            if W(1) > 1, W(1) = 1; end
            if numel(W) >= 2 && W(2) > 1, W(2) = 1; end
        end

        % ---- apply in frequency domain ----
        FY = fft(Ypad, [], 1); FY = bsxfun(@times, FY, W);
        Ywp = real(ifft(FY, [], 1));
        Yw = Ywp(1 + pad:pad + T, :);

        FX = fft(Xpad, [], 1); FX = bsxfun(@times, FX, W);
        Xwp = real(ifft(FX, [], 1));
        Xw = Xwp(1 + pad:pad + T, :);

    else
        % ---- no padding ----
        W = 1 ./ sqrt(psd);

        K = max(0, round(getfield_def(opts, 'film_lowbins_unity', 2)));

        if K > 0
            W(1:K) = 1;
            for k = 1:K - 1, W(end - k + 1) = 1; end
        else
            % DC guard even when lowbins_unity==0 (prevent amplification)
            if W(1) > 1, W(1) = 1; end
            if numel(W) >= 2 && W(2) > 1, W(2) = 1; end
        end

        FY = fft(Yseg, [], 1); FY = bsxfun(@times, FY, W);
        Yw = real(ifft(FY, [], 1));

        FX = fft(Xseg, [], 1); FX = bsxfun(@times, FX, W);
        Xw = real(ifft(FX, [], 1));
    end

end

% ======================================================================
%                           Utilities
% ======================================================================
function val = getfield_def(s, f, def)
    if isfield(s, f) && ~isempty(s.(f)), val = s.(f); else, val = def; end
end

function w = local_tukey(N, alpha)
    % Minimal Tukey window (toolbox-free)
    if alpha <= 0
        w = ones(N, 1);
        return;
    elseif alpha >= 1
        n = (0:N - 1)';
        w = 0.5 * (1 - cos(2 * pi * n / (N - 1)));
        return;
    end

    w = ones(N, 1);
    a = floor(alpha * (N - 1) / 2);
    n = (0:N - 1)';
    idx = n <= a;
    w(idx) = 0.5 * (1 + cos(pi * (2 * n(idx) / (alpha * (N - 1)) - 1)));
    idx = n >= (N - 1 - a);
    w(idx) = 0.5 * (1 + cos(pi * (2 * (n(idx) - (N - 1)) / (alpha * (N - 1)) + 1)));
end
