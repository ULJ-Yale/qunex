function varargout = glm_whiten_solve(Xw, yw, varargin)
%``function varargout = glm_whiten_solve(Xw, yw, varargin)``
%
%   Dual-interface GLS solver for whitened data.
%
%   Inputs:
%       Xw (matrix or 3-D)
%           Whitened design.
%
%       yw (matrix)
%           Whitened data.
%
%       state (struct, optional)
%           Legacy/stateful interface. On input, may contain options and method.
%
%   Outputs:
%       New/simple interface:
%           [beta, residuals, XtXw, parcel_mode] = glm_whiten_solve(Xw, yw)
%
%       Legacy/state interface:
%           [beta, state] = glm_whiten_solve(Xw, yw, state)
%           state fields populated:
%             .residuals [T x V], .parcel_mode logical, .XtXw []|[p x p],
%             .film_score (if method == 'film')
%
%   Notes:
%       - Handles both global whitening (Xw [T x p], yw [T x V]) and parcel mode
%         (Xw [T x p x P], yw [T x P]).
%       - MATLAB + Octave compatible.

% SPDX-FileCopyrightText: 2025 QuNex development team
%
% SPDX-License-Identifier: GPL-3.0-or-later

    have_state = (nargin >= 3);

    if have_state
        state = varargin{1};
    else
        state = struct();
        state.options = struct();
    end

    % -------- Solve GLS --------
    parcel_mode = (ndims(Xw) == 3);

    if ~parcel_mode
        % Global whitening
        XtXw = Xw' * Xw;
        beta = (XtXw \ (Xw' * yw)); % [p x V]
        residuals = yw - Xw * beta; % [T x V]
    else
        % Parcel-wise whitening
        [~, npred, nparc] = size(Xw);
        beta = zeros(npred, nparc);
        residuals = zeros(size(yw)); % [T x P]
        XtXw = []; % not defined in parcel mode

        for p = 1:nparc
            Xp = Xw(:, :, p);
            yp = yw(:, p);
            bp = (Xp' * Xp) \ (Xp' * yp);
            beta(:, p) = bp;
            residuals(:, p) = yp - Xp * bp;
        end

    end

    % -------- Optional: compute film_score if requested --------
    film_score = [];

    try

        if isfield(state, 'options') && isfield(state.options, 'method') && ...
                strcmp(state.options.method, 'film')

            % Use configured tune lags if available; else default to 5
            if isfield(state.options, 'film_tune_lags') && ~isempty(state.options.film_tune_lags)
                L = state.options.film_tune_lags;
            else
                L = 5;
            end

            % Prefer shared scorer if available
            if exist('glm_ac_score', 'file') == 2
                film_score = glm_ac_score(residuals, L);
            else
                film_score = local_ac_mean_abs(residuals, L);
            end

        end

    catch
        % Never break solve on scoring failure
        film_score = [];
    end

    % -------- Outputs (dual interface) --------
    if have_state
        state.residuals = residuals;
        state.parcel_mode = parcel_mode;
        state.XtXw = XtXw;
        if ~isempty(film_score), state.film_score = film_score; end
        varargout = {beta, state};
    else
        varargout = {beta, residuals, XtXw, parcel_mode};
    end

end

% ================= local helpers =================

function acm = local_ac_mean_abs(R, L)
    % Mean absolute autocorrelation over first L lags, averaged across columns.
    % R: [T x V], L: scalar
    if nargin < 2 || isempty(L), L = 5; end
    [T, V] = size(R);
    L = min(L, max(1, T - 1));
    vals = nan(1, V);

    for v = 1:V
        e = R(:, v);
        e = e - mean(e);
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
