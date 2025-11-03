function [B, res, rvar, Xdof, B_se, B_t, B_z, B_pval] = img_glm_fit_w(obj, X, options)
%``function [B, res, rvar, Xdof, B_se, B_t, B_z, B_pval] = img_glm_fit_w(obj, X, options)``
%
%   Whole-brain GLM fitting with optional prewhitening and REML-like iteration.
%   Supports multiple whitening methods and parcel-weighted pooling for robust
%   noise estimation. Designed for MATLAB and GNU Octave.
%
%   Whitening methods:
%     - 'none'   : OLS (no prewhitening)
%     - 'ar1'    : AR(1) pooled (global) or per-parcel with shrinkage
%     - 'arp'    : AR(p) pooled or per-parcel with shrinkage (auto p-select)
%     - 'arma11' : ARMA(1,1) pooled
%     - 'film'   : Frequency-domain (FILM) whitening; optional autotune
%     - 'film_strong'   : FILM version with stronger AC suppression
%
%   Inputs:
%       obj (nimage)
%           Image object; time in rows (frames), voxels/scalars in columns.
%
%       X (matrix [T x p])
%           Design matrix. Columns with zero variance are excluded.
%
%       options (char or struct)
%           - When char: option string parsed via general_parse_options
%           - When struct: fields are normalized by glm_whiten_config
%           Key fields include: method, pool, iterate, arp_auto/arp_pmax,
%           shrink_k, film_* controls, debug_mode, protect_drifts and
%           drift_* settings. See glm_whiten_config.m for defaults.
%
%   Outputs:
%       B (nimage)
%           Beta coefficients (one frame per predictor in X after filtering).
%
%       res (nimage)
%           Residuals from the final (whitened) fit, in the original domain.
%
%        rvar (nimage)
%           Residual variance image (one frame), based on whitened residuals.
%
%       Xdof (double)
%           Effective degrees of freedom: size(X,1) - size(X,2).
%
%       B_se (nimage), B_t (nimage), B_z (nimage), B_pval (nimage)
%           Standard errors, t-statistics, z-scores, and two-sided p-values.
%
%   Notes:
%       - Drift protection: when enabled, drift-like design columns are detected
%         per segment and excluded from noise estimation prior to whitening.
%       - FILM autotune (if on) adjusts fast_lambda and film_maxlag using
%         a residual whiteness score (see glm_film_autotune_params).
%       - REML-like iteration: if iterate=true, a second pass refines whitening
%         using residuals from the first GLS fit.
%       - Parcel weights: when CIFTI parcel metadata is present, parcel sizes
%         (voxels + surface vertices) are used as pooling weights.
%
%   Options (cheatsheet):
%       Core
%         - method: 'none'|'ar1'|'arp'|'arma11'|'film'|'film_strong'   % prewhitening
%         - pool: 'global'|'parcel'                                    % AC pooling mode
%         - iterate: true|false                                        % REML-like second pass
%
%       Segment thresholds (coercions by length)
%         - min_seg_skip: int  % < this → identity (no whitening)
%         - min_seg_ar1:  int  % < this (but ≥skip) → force AR(1)
%         - min_seg_arma: int  % < this → arma11 coerced to ar1 (from config)
%
%       AR/ARP/ARMA
%         - order: int             % AR(p) order when arp_auto=false
%         - arp_auto: true|false   % auto-select p up to arp_pmax (AIC pooled)
%         - arp_pmax: int          % max AR order when auto-selecting
%         - shrink_k: int          % parcel shrink strength toward pooled params
%
%       FILM (frequency-domain)
%         - film_autotune: true|false         % grid-search fast_lambda & film_maxlag
%         - film_lambda_grid: [..]            % lambda values to try in autotune
%         - film_lag_grid: [..]               % maxlag values to try in autotune
%         - film_tune_lags: int               % lags used in whiteness score
%         - film_target_ac: scalar            % legacy target AC (kept for compat)
%         - film_maxlag: int|[]               % []→auto; ACF truncation
%         - fast_lambda: [0..1]               % spectral smoothing blend
%         - fast_win: odd int ≥3              % smoothing window length
%         - fast_log: true|false              % smooth in log domain
%         - film_alpha: [0..1]                % Tukey taper parameter
%         - film_eps: small+                  % PSD floor
%         - film_lowbins_unity: int≥0         % force low freq bins to unity
%         - film_padlen: int≥0                % reflect padding to reduce wrap
%         - film_whiten_mode: 'conservative'|'aggressive'|'fallback'  % behavior token
%         - film_lock_filter: true|false      % reuse FILM filter on iteration
%
%       Drift protection
%         - protect_drifts: true|false        % exclude drift-like cols from noise est.
%         - drift_cols: [idx]                 % explicit drift columns in X
%         - drift_autodetect: true|false      % auto-detect drift columns per segment
%         - drift_detect_tol: (0,1)           % similarity tolerance for detection
%         - drift_detect_maxperseg: int       % cap per-segment drift columns
%
%       Diagnostics / behavior
%         - debug_mode: true|false            % verbose per-segment diagnostics
%         - permutation_safe: true|false      % stabilize settings under permutation
%
%       Notes on defaults
%         - String/struct options are normalized by glm_whiten_config.m; its
%           defaults may slightly differ from the initial string defaults here.
%         - Effective values (after normalization) are printed when debug_mode=true.
%
%   Examples (option strings):
%       % 1) OLS (no whitening)
%       'method:none'
%
%       % 2) Global AR(1) with iteration
%       'method:ar1|pool:global|iterate:true'
%
%       % 3) Parcel AR(p) with auto order up to 6 and stronger shrinkage
%       'method:arp|pool:parcel|arp_auto:true|arp_pmax:6|shrink_k:200'
%
%       % 4) Global ARMA(1,1) (short segments auto-coerce to AR1)
%       'method:arma11|pool:global'
%
%       % 5) FILM with autotune and mild padding, conservative mode
%       'method:film|film_autotune:true|film_padlen:10|film_lowbins_unity:2'
%
%       % 6) Strong FILM with REML-like iteration and filter lock
%       'method:film_strong|iterate:true|film_lock_filter:true|film_autotune:true'
%
%       % 7) Drift protection with autodetect (up to 2 per segment)
%       'protect_drifts:true|drift_autodetect:true|drift_detect_tol:0.9995|drift_detect_maxperseg:2'
%
%       % 8) Permutation-safe adjustments (coerces to stable configs)
%       'permutation_safe:true|method:arp'   % may coerce ARP→AR1 if not FILM
%

% SPDX-FileCopyrightText: 2025 QuNex development team
%
% SPDX-License-Identifier: GPL-3.0-or-later

    % -------------------------------------------------------------------------
    % 0) Parse options
    % -------------------------------------------------------------------------
    if nargin < 2, error('img_glm_fit: requires obj, X'); end
    if nargin < 3, options = ''; end

    default = [ ...
                   'method:none|order:3|pool:global|' ...
                   'iterate:false|min_seg_skip:20|min_seg_ar1:40|' ...
                   'shrink_k:200|arp_pmax:6|arp_auto:true|film_lock_filter:true|' ...
                   'film_autotune:true|film_target_ac:0.02|film_whiten_mode:conservative|' ...
                   'film_tune_lags:5|film_lambda_grid:[0.02 0.05 0.08 0.1 0.15 0.2 0.25]|' ...
                   'film_lag_grid:[30 40 60 80 100]|film_autotune_runs:1|' ...
                   'debug_mode:false|protect_drifts:false|drift_cols:|' ...
                   'drift_autodetect:true|drift_detect_tol:0.9995|drift_detect_maxperseg:2' ...
               ];
    options = general_parse_options([], options, default);

    bool = @(x) (ischar(x) && strcmpi(x, 'true')) || isequal(x, true);
    options.iterate = bool(options.iterate);
    options.arp_auto = bool(options.arp_auto);
    options.film_autotune = bool(options.film_autotune);
    options.debug_mode = bool(options.debug_mode);
    options.protect_drifts = bool(options.protect_drifts);
    options.drift_autodetect = bool(options.drift_autodetect);

    % Keep glm_whiten_config in the loop if you want it to normalize fields
    options = glm_whiten_config(options);

    % --- debug printout ---
    if options.debug_mode
        fprintf('\n-------------------------------------------------------------------------\n');
        fprintf('Running GLM fit with optional prewhitening\n');
        general_print_struct(options, 'GLM fitting options in use');
        fprintf('\n');
    end

    % -------------------------------------------------------------------------
    % 1) Dimensions, data, good regressors
    % -------------------------------------------------------------------------
    if obj.frames ~= size(X, 1)
        error('predictor and data number of frames do not match');
    end

    seg_id = obj.use(:);
    w_parc = parcel_weights(obj, options);

    obj.data = obj.image2D'; % [T x Vox]
    y = obj.data;

    good = std(X) ~= 0;
    X = X(:, good);

    % -------------------------------------------------------------------------
    % 2) Initial OLS
    % -------------------------------------------------------------------------
    XtX = X' * X;
    beta0 = (XtX \ X') * y;
    res0 = y - X * beta0;

    if options.debug_mode
        glm_print_ar1_debug('raw', res0);
        fprintf('          |AC|1..5 = %.3f\n', glm_ac_score(res0, 5));
    end

    % -------------------------------------------------------------------------
    % 3) (optional) drift detection
    % -------------------------------------------------------------------------
    if options.protect_drifts && isempty(options.drift_cols) && options.drift_autodetect
        options.drift_cols = glm_drift_detect(X, seg_id, ...
            options.drift_detect_tol, options.drift_detect_maxperseg);

        if options.debug_mode
            fprintf('[DriftProtect] auto-detected %d drift regressors\n', numel(options.drift_cols));
        end

    end

    % -------------------------------------------------------------------------
    % 4) Prewhitening (state-based -> stateless solve)
    % -------------------------------------------------------------------------
    if strcmp(options.method, 'none')
        beta = beta0;
        resW = res0;
        XtX_current = XtX;
        Xw = X; yw = y;
        parcel_mode = false;

    else
        % Build whitening state (since glm_whiten_config does not build it)
        state = struct();
        state.opts = options;
        state.seg_id = seg_id;
        state.w_parc = w_parc;

        % Optional FILM autotune using your current signature
        if strcmp(state.opts.method, 'film') && state.opts.film_autotune
            tuned = glm_film_autotune_params(X, y, res0, seg_id, state.opts, w_parc);
            if ~isempty(tuned), state.opts = tuned; end
        end

        % Pass 1 whitening + GLS
        [Xw, yw, state] = glm_whiten_apply(X, y, res0, state);
        [beta, resW, XtX_current, parcel_mode] = glm_whiten_solve(Xw, yw);

        if options.debug_mode
            glm_print_ar1_debug('pass1', resW);
            fprintf('          |AC|1..5 = %.3f\n', glm_ac_score(resW, 5));
        end

        % Optional REML-style iteration
        if state.opts.iterate
            res_gls = y - X * beta; % residuals in the ORIGINAL domain
            state.iteration = 2;
            [Xw, yw, state] = glm_whiten_apply(X, y, res_gls, state);
            [beta, resW, XtX_current, parcel_mode] = glm_whiten_solve(Xw, yw);

            if options.debug_mode
                glm_print_ar1_debug('iter', resW);
                fprintf('          |AC|1..5 = %.3f\n', glm_ac_score(resW, 5));
            end

        end

    end

    % Use whitened residuals from the solver for downstream outputs
    res = resW;

    % -------------------------------------------------------------------------
    % 5) embed Betas
    % -------------------------------------------------------------------------
    B = obj.zeroframes(size(X, 2));
    B.data = reshape(B.data, B.frames, B.voxels);
    B.data(good, :) = beta;
    B.data = B.data';

    % -------------------------------------------------------------------------
    % 6) Residual image
    % -------------------------------------------------------------------------
    if nargout > 1
        res_img = obj;
        res_img.data = res';
        res = res_img;
    end

    % -------------------------------------------------------------------------
    % 7) Variance, DOF
    % -------------------------------------------------------------------------
    if nargout > 2
        Xdof = size(X, 1) - size(X, 2);
        % mse = sum((y - X * beta) .^ 2, 1) / Xdof;
        mse = sum(resW .^ 2, 1) / Xdof;
        rvar = obj.zeroframes(1);
        rvar.data = mse';
    end

    % -------------------------------------------------------------------------
    % 8) SE / t / z / p
    % -------------------------------------------------------------------------
    if nargout > 4
        B_se = obj.zeroframes(size(X, 2)); B_se.data = reshape(B_se.data, B_se.frames, B_se.voxels);
        B_t = obj.zeroframes(size(X, 2)); B_t.data = reshape(B_t.data, B_t.frames, B_t.voxels);
        B_z = obj.zeroframes(size(X, 2)); B_z.data = reshape(B_z.data, B_z.frames, B_z.voxels);
        B_pval = obj.zeroframes(size(X, 2)); B_pval.data = reshape(B_pval.data, B_pval.frames, B_pval.voxels);

        % mse_col = sum((y - X * beta) .^ 2, 1)' / Xdof;
        mse_col = sum(resW .^ 2, 1)' / Xdof; % [V × 1]

        if ~parcel_mode
            % Global (single) design after whitening
            if isempty(XtX_current)
                XtX_current = X' * X; % fallback (should not happen in proper global path)
            end

            varb = diag(inv(XtX_current)); % [nPred x 1]
            SE = sqrt(varb * mse_col'); % [nPred x nVox]
        else
            % Parcel-mode: Xw is [T x nPred x nVox], compute per-voxel
            np = size(Xw, 2);
            nv = size(mse_col, 1);
            SE = zeros(np, nv);

            for v = 1:nv
                Xp = Xw(:, :, v);
                varb = diag(inv(Xp' * Xp));
                SE(:, v) = sqrt(varb * mse_col(v));
            end

        end

        t = beta ./ SE;
        p = 2 .* (1 - tcdf(abs(t), Xdof));
        p = max(min(p, 1 -1e-16), realmin);
        z = sign(t) .* norminv(1 - p / 2, 0, 1);

        B_se.data(good, :) = SE; B_se.data = B_se.data';
        B_t.data(good, :) = t; B_t.data = B_t.data';
        B_z.data(good, :) = z; B_z.data = B_z.data';
        B_pval.data(good, :) = p; B_pval.data = B_pval.data';
    end

    if options.debug_mode
        fprintf('\nDone running GLM fit\n');
        fprintf('-------------------------------------------------------------------------\n');
    end
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

        if isfield(options, 'debug_mode') && options.debug_mode
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
