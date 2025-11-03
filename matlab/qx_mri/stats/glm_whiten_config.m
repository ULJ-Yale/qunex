function opts = glm_whiten_config(opts)
%``function opts = glm_whiten_config(opts)``
%
%   Fill defaults, normalize types, and validate options for the GLM
%   prewhitening engine. Safe for MATLAB and Octave.
%
%   Inputs:
%       opts_in (struct or empty)
%           Partial options structure. Missing fields are filled with defaults.
%
%   Outputs:
%       opts (struct)
%           Completed and validated options. Key fields include:
%             - method: 'none'|'ar1'|'arp'|'arma11'|'film'|'film_strong'|'spm'
%             - pool:   'global'|'parcel'
%             - iterate (bool), min_seg_* (ints), order/arp_pmax/shrink_k,
%               FILM controls (fast_lambda, film_maxlag, film_eps, etc.).
%
%   Notes:
%       - Accepts empty input; string booleans ('true'/'false') coerced.
%       - Normalizes categorical strings to lowercase and trims spaces.
%       - Applies permutation-safe adjustments when opts.permutation_safe is true.
%       - Sets robust defaults for AR/ARP/ARMA/FILM.
%

% SPDX-FileCopyrightText: 2025 QuNex development team
%
% SPDX-License-Identifier: GPL-3.0-or-later

    if nargin < 1 || isempty(opts)
        opts = struct();
    end

    % ----------------------------
    % Helper: fetch or set default
    % ----------------------------
    function v = getd(field, def)

        if isfield(opts, field) && ~isempty(opts.(field))
            v = opts.(field);
        else
            v = def;
        end

    end

    % ----------------------------
    % Defaults (tuned)
    % ----------------------------
    opts.method = getd('method', 'none'); % 'none' | 'ar1' | 'arp' | 'arma11' | 'film' | 'spm'
    opts.order = getd('order', 3); % AR(p) default p
    opts.pool = getd('pool', 'global'); % 'global' | 'parcel'

    % FILM
    opts.film_maxlag = getd('film_maxlag', []); % [] → auto
    opts.film_alpha = getd('film_alpha', 0.5);
    opts.film_eps = getd('film_eps', 1e-6);
    opts.fast_lambda = getd('fast_lambda', 0.25);
    opts.fast_win = getd('fast_win', 9);
    opts.fast_log = getd('fast_log', true);
    opts.film_lowbins_unity = getd('film_lowbins_unity', 2); % protect DC + 1 low bin
    opts.film_padlen = getd('film_padlen', 0);

    % Iteration / REML-like
    opts.iterate = getd('iterate', false);

    % Segment length rules
    opts.min_seg_skip = getd('min_seg_skip', 20);
    opts.min_seg_ar1 = getd('min_seg_ar1', 50); % was 40; 50 is more stable for AR1

    % AR(p) tuning
    opts.shrink_k = getd('shrink_k', 150); % parcel shrinkage strength
    opts.arp_pmax = getd('arp_pmax', 6);
    opts.arp_auto = getd('arp_auto', true);

    % Drift protection
    opts.protect_drifts = getd('protect_drifts', false);
    opts.drift_cols = getd('drift_cols', []);
    opts.drift_autodetect = getd('drift_autodetect', true);
    opts.drift_detect_tol = getd('drift_detect_tol', 0.9995);
    opts.drift_detect_maxperseg = getd('drift_detect_maxperseg', 2);

    % Diagnostics / behavior
    opts.debug_mode = getd('debug_mode', false);
    opts.permutation_safe = getd('permutation_safe', false);

    % FILM autotune
    opts.film_autotune = getd('film_autotune', true);
    opts.film_target_ac = getd('film_target_ac', 0.04); % mean |AC| at lags 1..L target
    opts.film_max_ac = getd('film_max_ac', 0.12);
    opts.film_tune_lags = getd('film_tune_lags', 5);
    opts.film_lambda_grid = getd('film_lambda_grid', [0.02 0.05 0.08 0.10 0.15 0.20 0.25]);
    opts.film_lag_grid = getd('film_lag_grid', [30 40 60 80 100]);
    opts.film_autotune_runs = getd('film_autotune_runs', 1);

    % ----------------------------
    % Coerce types / normalize
    % ----------------------------
    coerce_bool = @(x) ((ischar(x) && strcmpi(x, 'true')) || (islogical(x) && x == true));
    coerce_bool_false_ok = @(x, def) (isempty(x) * def) || coerce_bool(x); %#ok<NASGU>

    % logicals from strings if needed
    if ischar(opts.fast_log), opts.fast_log = strcmpi(opts.fast_log, 'true'); end
    if ischar(opts.iterate), opts.iterate = strcmpi(opts.iterate, 'true'); end
    if ischar(opts.arp_auto), opts.arp_auto = strcmpi(opts.arp_auto, 'true'); end
    if ischar(opts.debug_mode), opts.debug_mode = strcmpi(opts.debug_mode, 'true'); end
    if ischar(opts.permutation_safe), opts.permutation_safe = strcmpi(opts.permutation_safe, 'true'); end
    if ischar(opts.protect_drifts), opts.protect_drifts = strcmpi(opts.protect_drifts, 'true'); end
    if ischar(opts.drift_autodetect), opts.drift_autodetect = strcmpi(opts.drift_autodetect, 'true'); end
    if ischar(opts.film_autotune), opts.film_autotune = strcmpi(opts.film_autotune, 'true'); end

    % numeric coercions commonly seen as strings
    numfields = {'film_eps', 'film_alpha', 'fast_lambda', 'fast_win', 'min_seg_skip', 'min_seg_ar1', ...
                     'order', 'arp_pmax', 'shrink_k', 'film_target_ac', 'film_max_ac', 'film_tune_lags', ...
                 'film_padlen'};

    for i = 1:numel(numfields)
        f = numfields{i};
        if ischar(opts.(f)), opts.(f) = str2double(opts.(f)); end
    end

    % string normalization
    if ischar(opts.method), opts.method = lower(strtrim(opts.method)); end
    if ischar(opts.pool), opts.pool = lower(strtrim(opts.pool)); end

    % allow [] for film_maxlag, otherwise coerce numeric
    if ~isempty(opts.film_maxlag) && ischar(opts.film_maxlag)
        t = str2double(opts.film_maxlag);
        if ~isnan(t), opts.film_maxlag = t; else, opts.film_maxlag = []; end
    end

    % ----------------------------
    % Validate categorical fields
    % ----------------------------
    valid_methods = {'none', 'ar1', 'arp', 'arma11', 'film', 'film_strong', 'spm'};

    if ~any(strcmp(opts.method, valid_methods))
        error('glm_whiten_config: invalid method "%s". Must be one of %s.', ...
            char(opts.method), strjoin(valid_methods, ', '));
    end

    valid_pool = {'global', 'parcel'};

    if ~any(strcmp(opts.pool, valid_pool))
        error('glm_whiten_config: invalid pool "%s". Must be "global" or "parcel".', char(opts.pool));
    end

    valid_modes = {'conservative', 'aggressive', 'fallback'};

    if ~isfield(opts, 'film_whiten_mode') || ~any(strcmp(opts.film_whiten_mode, valid_modes))
        opts.film_whiten_mode = 'conservative';
    end

    % ----------------------------
    % Permutation-safe adjustments
    % ----------------------------
    if opts.permutation_safe
        % Freeze whitening: no iterative re-estimation
        opts.iterate = false;

        % Avoid high-variance models under permutation; prefer AR(1) or stable FILM
        if any(strcmp(opts.method, {'arp', 'arma11'}))
            % If user asked for FILM, keep it (stable); otherwise AR1
            if ~strcmp(opts.method, 'film')
                opts.method = 'ar1';
            end

        end

        % Make FILM slightly more conservative
        if strcmp(opts.method, 'film')
            opts.fast_lambda = max(0.20, opts.fast_lambda);
            opts.film_eps = max(1e-6, opts.film_eps);
        end

    end

    % ----------------------------
    % Hard safety clamps
    % ----------------------------
    opts.fast_win = max(3, round(opts.fast_win));
    if mod(opts.fast_win, 2) == 0, opts.fast_win = opts.fast_win + 1; end

    opts.min_seg_skip = max(1, round(opts.min_seg_skip));
    opts.min_seg_ar1 = max(opts.min_seg_skip + 1, round(opts.min_seg_ar1));

    opts.order = max(1, round(opts.order));
    opts.arp_pmax = max(1, round(opts.arp_pmax));
    opts.shrink_k = max(1, round(opts.shrink_k));

    opts.film_lowbins_unity = max(0, round(opts.film_lowbins_unity));
    opts.film_padlen = max(0, round(opts.film_padlen));

    % Grid sanity
    if isempty(opts.film_lambda_grid) || ~isvector(opts.film_lambda_grid)
        opts.film_lambda_grid = [0.02 0.05 0.08 0.10 0.15 0.20 0.25];
    end

    if isempty(opts.film_lag_grid) || ~isvector(opts.film_lag_grid)
        opts.film_lag_grid = [30 40 60 80 100];
    end

    % Clamp ranges
    opts.fast_lambda = max(0, min(1, opts.fast_lambda));
    opts.film_alpha = max(0, min(1, opts.film_alpha));

    % ----------------------------
    % Method-specific post-fixes
    % ----------------------------

    % Short segments → never allow ARMA(1,1)
    opts.min_seg_arma = 80; % used by apply layer to coerce arma11→ar1

    % If method is 'spm' (future), ensure compatible settings exist
    if strcmp(opts.method, 'spm')
        % Placeholder for SPM AR∞ defaults; actual implementation lives elsewhere
        % Keep as no-op here.
    end

end
