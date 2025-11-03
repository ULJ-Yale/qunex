function [Xw, yw, state] = glm_whiten_apply(X, y, R, state)
%``function [Xw, yw, state] = glm_whiten_apply(X, y, R, state)``
%
%   Apply the selected prewhitening method segment-by-segment, concatenate
%   the whitened design and data, and populate state for downstream solve.
%   This is orchestration only; AR / FILM math lives in dedicated modules.
%
%   Inputs:
%       X (matrix [T x p])
%           Design matrix.
%
%       y (matrix [T x V])
%           Data; columns are voxels or parcels.
%
%       R (matrix [T x V])
%           Residuals from OLS (same shape as y).
%
%       state (struct)
%           Fields expected:
%             .opts        options (from glm_whiten_config)
%             .seg_id      [T x 1] segment IDs (integers)
%             .w_parc      [V x 1] pooling weights (e.g., parcel sizes)
%             .iteration   pass index (1 for first pass, 2+ for REML)
%             .film_cache  (optional) per-segment cached FILM info (.W, .padlen)
%
%   Outputs:
%       Xw, yw (matrices or arrays)
%           Whitened design/data stacked across segments.
%           - Global whitening:      Xw [Ttot x p],   yw [Ttot x V]
%           - Parcel-wise whitening: Xw [Ttot x p x V], yw [Ttot x V]
%
%       state (struct)
%           Updated state (debug info, film cache, etc.).
%
%   Notes:
%       - This function does not solve for beta. Use glm_whiten_solve.
%       - Method-specific implementations are delegated to:
%           glm_whiten_ar.m (AR1/ARP/ARMA), glm_whiten_film.m (FILM PSD+FFT),
%           glm_whiten_film_strong.m (stronger FILM variant).
%       - Drift-protected noise estimation is handled here (projection applies
%         only to R for estimating noise; never to X or y).
%

% SPDX-FileCopyrightText: 2025 QuNex development team
%
% SPDX-License-Identifier: GPL-3.0-or-later

    opts = state.opts;
    seg_id = state.seg_id(:);
    w_parc = state.w_parc(:);

    % Init accumulators
    Xw = [];
    yw = [];

    % Debug bookkeeping
    dbg.enabled = isfield(opts, 'debug_mode') && opts.debug_mode;
    dbg.segment = [];
    dbg.length = [];
    dbg.method = {};
    dbg.iter = [];
    dbg.arpord = [];

    % Ensure cache exists
    if ~isfield(state, 'film_cache') || isempty(state.film_cache)
        state.film_cache = struct('seg_id', {}, 'W', {}, 'padlen', {}, 'len', {}, 'method', {});
    end

    % Determine if we should lock (reuse) FILM filter this pass
    is_iter = isfield(state, 'iteration') && state.iteration >= 2;
    want_lock = is_iter && isfield(opts, 'film_lock_filter') && opts.film_lock_filter ...
        && (strcmp(opts.method, 'film') || strcmp(opts.method, 'film_strong'));

    segs = unique(seg_id(~isnan(seg_id)));

    if isempty(segs)
        error('glm_whiten_apply: seg_id has no valid segments.');
    end

    for s = segs.'
        idx = (seg_id == s);
        Xseg = X(idx, :);
        Yseg = y(idx, :);
        Rseg = R(idx, :);
        Tseg = size(Xseg, 1);

        % ---------- Drift-protected noise estimation ----------
        Rseg_est = Rseg;

        if opts.protect_drifts
            drift_cols = [];

            if ~isempty(get_opt(opts, 'drift_cols'))
                drift_cols = opts.drift_cols(:);
            elseif isfield(state, 'drift_cols') && ~isempty(state.drift_cols)
                drift_cols = state.drift_cols(:);
            end

            if ~isempty(drift_cols)
                drift_cols = drift_cols(drift_cols >= 1 & drift_cols <= size(X, 2));

                if ~isempty(drift_cols)
                    Sseg = Xseg(:, drift_cols);

                    if ~isempty(Sseg)
                        StS = Sseg' * Sseg;
                        StS_inv = local_pinv_safe(StS);
                        Rseg_est = Rseg - Sseg * (StS_inv * (Sseg' * Rseg));

                        if dbg.enabled
                            fprintf('[DriftProtect] seg %d: drift_cols %s\n', s, mat2str(drift_cols(:)'));
                        end

                    end

                end

            end

        end

        % ---------- Method coercion by segment length ----------
        eff_method = opts.method;

        if Tseg < opts.min_seg_skip
            eff_method = 'identity';
        elseif Tseg < opts.min_seg_ar1
            eff_method = 'ar1';
        else

            if strcmp(eff_method, 'arma11') && isfield(opts, 'min_seg_arma') && Tseg < opts.min_seg_arma
                eff_method = 'ar1';
            end

        end

        if strcmp(eff_method, 'none')
            eff_method = 'identity';
        end

        % ---------- Dispatch ----------
        meta = struct('arp_order', NaN);

        switch eff_method
            case 'identity'
                Yws = Yseg;
                Xws = Xseg;

            case {'ar1', 'arp', 'arma11'}
                [Yws, Xws, meta] = glm_whiten_ar(eff_method, Xseg, Yseg, Rseg_est, opts, w_parc);

            case {'film', 'film_strong'}
                % Try lock-reuse if requested and cache exists; otherwise do fresh FILM
                if want_lock
                    hit = film_cache_hit(state.film_cache, s, eff_method, Tseg);

                    if hit.found
                        % Reuse cached FFT-domain weights (W) + padlen
                        [Yws, Xws] = local_apply_film_W(Yseg, Xseg, hit.W, hit.padlen, opts);
                        meta.W = hit.W;
                        meta.padlen = hit.padlen;
                    else
                        % No cache for this segment → fresh FILM
                        [Yws, Xws, meta] = call_film_by_name(eff_method, Xseg, Yseg, Rseg_est, opts, w_parc);
                        % Cache if available
                        if isfield(meta, 'W') && ~isempty(meta.W)
                            state.film_cache = film_cache_store(state.film_cache, s, meta.W, getfield_def(meta, 'padlen', 0), Tseg, eff_method);
                        end

                    end

                else
                    % First pass (or unlocked) → fresh FILM
                    [Yws, Xws, meta] = call_film_by_name(eff_method, Xseg, Yseg, Rseg_est, opts, w_parc);
                    % Cache W for possible REML reuse
                    if isfield(meta, 'W') && ~isempty(meta.W)
                        state.film_cache = film_cache_store(state.film_cache, s, meta.W, getfield_def(meta, 'padlen', 0), Tseg, eff_method);
                    end

                end

            otherwise
                error('glm_whiten_apply: unknown method "%s".', eff_method);
        end

        % ---------- Concatenate ----------
        yw = [yw; Yws];

        if ndims(Xws) == 2
            Xw = [Xw; Xws];
        else
            % 3-D: stack along time (dim 1), keep predictors (2), parcels (3)
            if isempty(Xw)
                Xw = Xws;
            else
                Xw = cat(1, Xw, Xws);
            end

        end

        % ---------- Debug record ----------
        if ~isfield(meta, 'arp_order'); meta.arp_order = NaN; end

        if dbg.enabled
            dbg.segment(end + 1, 1) = s;
            dbg.length(end + 1, 1) = Tseg;
            dbg.method{end + 1, 1} = eff_method;
            dbg.iter(end + 1, 1) = opts.iterate;
            dbg.arpord(end + 1, 1) = meta.arp_order;
        end

    end

    % ---------- Debug print ----------
    if dbg.enabled
        fprintf('\n[GLM Whitening Debug]\n');
        fprintf('%-6s %-8s %-14s %-6s %-6s\n', 'Seg', 'Frames', 'Method', 'Iter', 'AR_p');
        fprintf('%s\n', repmat('-', 1, 50));

        for i = 1:numel(dbg.segment)
            seg = dbg.segment(i);
            nfr = dbg.length(i);
            meth = dbg.method{i};
            iterf = dbg.iter(i);
            po = dbg.arpord(i);
            if isnan(po), po_str = '-'; else, po_str = sprintf('%d', po); end
            fprintf('%-6d %-8d %-14s %-6d %-6s\n', seg, nfr, meth, iterf, po_str);
        end

        methods = dbg.method;
            fprintf('\nSegments summary:\n');
            fprintf('  identity skip (<%d frames): %d\n', opts.min_seg_skip, sum(strcmp(methods, 'identity')));
            fprintf('  forced AR1 (<%d frames):    %d\n', opts.min_seg_ar1, sum(strcmp(methods, 'ar1')));
            fprintf('  AR1 user:                   %d\n', sum(strcmp(methods, 'ar1')) - sum(strcmp(methods, 'identity')));
            fprintf('  AR(p):                      %d\n', sum(strcmp(methods, 'arp')));
            fprintf('  ARMA(1,1):                  %d\n', sum(strcmp(methods, 'arma11')));
            fprintf('  FILM:                       %d\n', sum(strcmp(methods, 'film')) + sum(strcmp(methods, 'film_strong')));

            if any(~isnan(dbg.arpord))
                uo = unique(dbg.arpord(~isnan(dbg.arpord)));
                fprintf('  AR auto-orders used:        %s\n', mat2str(uo(:)'));
            end

            fprintf('\n');
        end

        % ---------- Update state ----------
        state.debug = dbg;
        % Parcel mode flag is implicit in Xw dimensionality and used by solver.

    end

    % ======================================================================
    % Helpers
    % ======================================================================

    function v = get_opt(opts, f)
        if isfield(opts, f), v = opts.(f); else, v = []; end
    end

    function Ainv = local_pinv_safe(A)
        % Small helper to avoid warnings in Octave/MATLAB
        [U, S, V] = svd(A, 'econ');
        s = diag(S);
        thr = max(size(A)) * eps(max(s));
        s(s < thr) = 0;
        s(s > 0) = 1 ./ s(s > 0);
        Ainv = V * diag(s) * U';
    end

    function val = getfield_def(S, f, def)
        if isfield(S, f) && ~isempty(S.(f)), val = S.(f); else, val = def; end
    end

    % ---- FILM dispatch allowing both variants ----
    function [Yws, Xws, meta] = call_film_by_name(name, Xseg, Yseg, Rseg_est, opts, w_parc)

        switch name
            case 'film'
                [Yws, Xws, meta] = glm_whiten_film(Xseg, Yseg, Rseg_est, opts, w_parc);
            case 'film_strong'
                [Yws, Xws, meta] = glm_whiten_film_strong(Xseg, Yseg, Rseg_est, opts, w_parc);
            otherwise
                error('call_film_by_name: unknown film variant "%s"', name);
        end

        % Normalize: ensure meta has padlen if the implementation provides it
        if ~isfield(meta, 'padlen'), meta.padlen = 0; end
    end

    % ---- Cache lookup/store ----
    function hit = film_cache_hit(cache, seg, method, Tseg)
        hit.found = false;
        hit.W = [];
        hit.padlen = 0;
        if isempty(cache), return; end
        % last-write-wins lookup
        for k = numel(cache):-1:1

            if cache(k).seg_id == seg && strcmp(cache(k).method, method) && cache(k).len == Tseg
                hit.found = true;
                hit.W = cache(k).W;
                hit.padlen = cache(k).padlen;
                return;
            end

        end

    end

    function cache = film_cache_store(cache, seg, W, padlen, Tseg, method)
        rec.seg_id = seg;
        rec.W = W;
        rec.padlen = getfield_def(struct('padlen', padlen), 'padlen', 0);
        rec.len = Tseg;
        rec.method = method;
        cache(end + 1) = rec; %#ok<AGROW>
    end

    % ---- Re-apply stored FFT-domain whitening operator ----
    % W:    vector of length T or T+2*pad (same as used when stored)
    % padlen: scalar pad used when W was created
    function [Yw, Xw] = local_apply_film_W(Yseg, Xseg, W, padlen, opts)
        Tseg = size(Yseg, 1);

        if nargin < 4 || isempty(padlen), padlen = 0; end

        if padlen > 0
            % reflect pad
            Ypad = [flipud(Yseg(1:padlen, :)); Yseg; flipud(Yseg(end - padlen + 1:end, :))];
            Xpad = zeros(size(Ypad, 1), size(Xseg, 2));

            for j = 1:size(Xseg, 2)
                xj = Xseg(:, j);
                Xpad(:, j) = [flipud(xj(1:padlen)); xj; flipud(xj(end - padlen + 1:end))];
            end

            % apply in frequency domain
            FY = fft(Ypad, [], 1); FY = bsxfun(@times, FY, W);
            Ywp = real(ifft(FY, [], 1));
            Yw = Ywp(1 + padlen:padlen + Tseg, :);

            FX = fft(Xpad, [], 1); FX = bsxfun(@times, FX, W);
            Xwp = real(ifft(FX, [], 1));
            Xw = Xwp(1 + padlen:padlen + Tseg, :);
        else
            % no padding
            FY = fft(Yseg, [], 1); FY = bsxfun(@times, FY, W);
            Yw = real(ifft(FY, [], 1));
            FX = fft(Xseg, [], 1); FX = bsxfun(@times, FX, W);
            Xw = real(ifft(FX, [], 1));
        end

        % optional protection of low bins (should already be baked into W);
        % kept here as a no-op placeholder for consistency
        %#ok<NASGU>
    end
