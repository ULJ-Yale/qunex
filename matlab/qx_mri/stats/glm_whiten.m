function [Xw, yw, state] = glm_whiten(X, y, R, seg_id, opts, w_parc)
%``function [Xw, yw, state] = glm_whiten(X, y, R, seg_id, opts, w_parc)``
%
%   Unified entry point for GLM prewhitening. Orchestrates whitening across
%   segments and methods; method-specific math is delegated to dedicated helpers.
%
%   Inputs:
%       X (matrix [T x p])
%           Design matrix.
%
%       y (matrix [T x V])
%           Data matrix; columns are voxels or parcels.
%
%       R (matrix [T x V])
%           Residuals from OLS (used for noise estimation).
%
%       seg_id (vector [T x 1])
%           Integer segment IDs labeling contiguous keep-runs.
%
%       opts (struct)
%           Whitening options; see `glm_whiten_config` for fields and defaults.
%
%       w_parc (vector [V x 1], default ones)
%           Pooling weights (e.g., parcel sizes) for weighted estimates.
%
%   Outputs:
%       Xw (matrix or 3-D array)
%           Whitened design. Global whitening yields [T x p]; parcel-wise
%           whitening yields [T x p x V].
%
%       yw (matrix [T x V])
%           Whitened data.
%
%       state (struct)
%           Bookkeeping and diagnostics (options used, segment info, optional
%           FILM cache and scores). Intended for downstream use by solvers.
%
%   Notes:
%       - Supported methods: 'none', 'ar1', 'arp', 'arma11', 'film', 'film_strong' (future: 'spm').
%       - Iterative (REML-like) refinement is optional via opts.iterate.
%       - Method-specific implementations live in:
%           glm_whiten_config.m, glm_whiten_apply.m, glm_whiten_solve.m,
%           glm_whiten_ar.m, glm_whiten_film.m
%

% SPDX-FileCopyrightText: 2025 QuNex development team
%
% SPDX-License-Identifier: GPL-3.0-or-later

    % ---- 1) initialize state ----
    state = struct();
    state.opts = glm_whiten_config(opts); % fill missing defaults & grids
    state.seg_id = seg_id;
    state.w_parc = w_parc;
    state.first_pass = struct(); % for REML guard
    state.method = state.opts.method;

    % ---- 2) pre-whitening stage (first pass) ----
    [Xw, yw, state] = glm_whiten_apply(X, y, R, state);

    % ---- 3) optional REML iteration ----
    if state.opts.iterate && ~strcmp(state.method, 'none')
        % compute original-domain residuals
        beta = glm_whiten_solve(Xw, yw, state);
        R2 = y - X * beta;

        % second pass whitening
        [Xw2, yw2, state2] = glm_whiten_apply(X, y, R2, state);
        beta2 = glm_whiten_solve(Xw2, yw2, state2);

        % check whiteness guard (FILM)
        if isfield(state, 'film_score') && isfield(state2, 'film_score')

            if state2.film_score > state.film_score + 0.01
                % revert
                Xw = Xw;
                yw = yw;
                state = state;
            else
                Xw = Xw2;
                yw = yw2;
                state = state2;
            end

        else
            % no FILM guard — accept second pass
            Xw = Xw2;
            yw = yw2;
            state = state2;
        end

    end

end
