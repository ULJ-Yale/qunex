function opts = glm_film_autotune_params(X, y, residuals0, seg_id, opts, w_parc)
%``function opts = glm_film_autotune_params(X, y, residuals0, seg_id, opts, w_parc)``
%
%   Grid-search autotuning for FILM whitening parameters:
%     - fast_lambda  (spectral smoothing blend)
%     - film_maxlag  (ACF truncation for PSD)
%
%   Inputs:
%       X (matrix [T x p])
%           Design matrix
%
%       y (matrix [T x V])
%           Data matrix
%
%       residuals0 (matrix [T x V])
%           Initial residuals (OLS)
%
%       seg_id (vector [T x 1])
%           Segment IDs
%
%       opts (struct)
%           Options from glm_whiten_config (method should be 'film')
%
%       w_parc (vector [V x 1], default ones)
%           Pooling weights
%
%   Outputs:
%       opts (struct)
%           Same struct with tuned fast_lambda and film_maxlag
%
%   Notes:
%       - Scoring rule: score = 0.5*|AR1| + 0.5*mean|AC| over first L lags
%         (penalizes short-lag correlation, more robust than AC mean alone).
%

% SPDX-FileCopyrightText: 2025 QuNex development team
%
% SPDX-License-Identifier: GPL-3.0-or-later

    if ~isfield(opts, 'method') || ~strcmp(opts.method, 'film') || ...
            ~isfield(opts, 'film_autotune') || ~opts.film_autotune
        return;
    end

    if nargin < 6 || isempty(w_parc)
        w_parc = ones(size(y, 2), 1);
    end

    if ~isfield(opts, 'film_tune_lags') || isempty(opts.film_tune_lags)
        opts.film_tune_lags = 5;
    end

    if ~isfield(opts, 'film_target_ac') || isempty(opts.film_target_ac)
        opts.film_target_ac = 0.04; % historical default, not used in new score
    end

    if ~isfield(opts, 'film_lambda_grid') || isempty(opts.film_lambda_grid)
        opts.film_lambda_grid = [0.02 0.05 0.08 0.10 0.15 0.20 0.25];
    end

    if ~isfield(opts, 'film_lag_grid') || isempty(opts.film_lag_grid)
        opts.film_lag_grid = [30 40 60 80 100];
    end

    % working copy
    base = opts;
    base.iterate = false;
    base.film_autotune = false;
    base.method = 'film';
    base.fast_lambda = getfield_def(base, 'fast_lambda', 0.25);

    segs = unique(seg_id(:)); segs(isnan(segs)) = [];

    if isempty(segs)
        segs = 1;
        seg_id = ones(size(X, 1), 1);
    end

    use_drift = isfield(opts, 'protect_drifts') && opts.protect_drifts && ...
        isfield(opts, 'drift_cols') && ~isempty(opts.drift_cols);

    best_score = Inf;
    best_lambda = base.fast_lambda;
    best_maxlag = getfield_def(base, 'film_maxlag', []);

    for li = 1:numel(opts.film_lambda_grid)
        lam = opts.film_lambda_grid(li);

        for gi = 1:numel(opts.film_lag_grid)
            L = opts.film_lag_grid(gi);

            base.fast_lambda = lam;
            base.film_maxlag = L;

            Xw_all = [];
            Yw_all = [];

            for s = segs.'
                idx = (seg_id == s);
                Xseg = X(idx, :);
                Yseg = y(idx, :);
                Rseg = residuals0(idx, :);

                % drift-protected residuals
                Rseg_est = Rseg;

                if use_drift
                    dc = opts.drift_cols(:);
                    dc = dc(dc >= 1 & dc <= size(X, 2));

                    if ~isempty(dc)
                        Sseg = Xseg(:, dc);

                        if ~isempty(Sseg)
                            StS = Sseg' * Sseg;
                            Rseg_est = Rseg - Sseg * (pinv_safe(StS) * (Sseg' * Rseg));
                        end

                    end

                end

                [Yws, Xws] = glm_whiten_film(Xseg, Yseg, Rseg_est, base, w_parc); %#ok<ASGLU>
                Yw_all = [Yw_all; Yws]; %#ok<AGROW>
                Xw_all = [Xw_all; Xws]; %#ok<AGROW>
            end

            % GLS on whitened data
            XtXw = Xw_all' * Xw_all;
            beta_hat = (XtXw \ (Xw_all' * Yw_all));
            resid_w = Yw_all - Xw_all * beta_hat;

            % ---- NEW SCORING ----
            % 1) mean |AC| across lags 1..L
            acm = ac_mean_abs(resid_w, opts.film_tune_lags);

            % 2) pooled AR(1)
            e = resid_w - mean(resid_w, 1);
            num = sum(sum(e(2:end, :) .* e(1:end - 1, :)));
            den = sum(sum(e(1:end - 1, :) .^ 2));
            ac1 = num / max(den, eps); % AR1 estimate

            score = 0.5 * abs(ac1) + 0.5 * abs(acm);
            % ----------------------

            if score < best_score
                best_score = score;
                best_lambda = lam;
                best_maxlag = L;
            end

        end

    end

    % update opts
    opts.fast_lambda = best_lambda;
    opts.film_maxlag = best_maxlag;

    if isfield(opts, 'debug_mode') && opts.debug_mode
        fprintf('[FILM autotune] λ=%.3f, maxlag=%d, score=%.4f\n', ...
            best_lambda, best_maxlag, best_score);
    end

end

% -------- helpers ----------
function val = getfield_def(S, f, def)
    if isfield(S, f) && ~isempty(S.(f)), val = S.(f); else, val = def; end
end

function Ainv = pinv_safe(A)
    [U, S, V] = svd(A, 'econ'); s = diag(S);
    thr = max(size(A)) * eps(max(s));
    s(s < thr) = 0; s(s > 0) = 1 ./ s(s > 0);
    Ainv = V * diag(s) * U';
end

function acm = ac_mean_abs(R, L)
    if nargin < 2 || isempty(L), L = 5; end
    T = size(R, 1); V = size(R, 2); L = min(L, T - 1);
    vals = nan(1, V);

    for v = 1:V
        e = R(:, v) - mean(R(:, v));
        d = sum(e .^ 2);
        if d <= 0 || T < 3, continue; end
        acc = 0;

        for k = 1:L
            num = sum(e(1 + k:end) .* e(1:end - k));
            acc = acc + abs(num / d);
        end

        vals(v) = acc / L;
    end

    acm = mean(vals(~isnan(vals)));
    if isempty(acm) || ~isfinite(acm), acm = NaN; end
end
