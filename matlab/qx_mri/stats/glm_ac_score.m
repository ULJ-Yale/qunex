function [acm_mean, acm_vec, ac1_mean, ac1_vec] = glm_ac_score(resid, L)
%``function [acm_mean, acm_vec, ac1_mean, ac1_vec] = glm_ac_score(resid, L)``
%
%   Compute whiteness diagnostics for residuals:
%     - Mean absolute autocorrelation across the first L lags (per column)
%     - AC at lag-1 (per column)
%     - Aggregate scores (mean across columns, ignoring NaNs)
%
%   Inputs:
%       resid (matrix [T x V])
%           Residuals (whitened or not), columns = voxels/parcels
%
%       L (scalar, default 5)
%           Number of lags for AC-mean
%
%   Outputs:
%       acm_mean (scalar)
%           Mean over columns of mean |AC| at lags 1..L
%
%       acm_vec  ([1 x V])
%           Per-column mean |AC| at lags 1..L
%
%       ac1_mean (scalar)
%           Mean over columns of |AC1|
%
%       ac1_vec  ([1 x V])
%           Per-column |AC1|
%
%   Notes:
%       - Uses denominator sum(e.^2) for AC; ignores low-variance columns.
%       - MATLAB/Octave compatible; no toolbox dependencies.
%

% SPDX-FileCopyrightText: 2025 QuNex development team
%
% SPDX-License-Identifier: GPL-3.0-or-later

    if nargin < 2 || isempty(L)
        L = 5;
    end

    [T, V] = size(resid);
    L = min(L, max(1, T - 1));

    acm_vec = nan(1, V);
    ac1_vec = nan(1, V);

    for v = 1:V
        e = resid(:, v);
        e = e - mean(e);

        denom = sum(e .^ 2);

        if ~isfinite(denom) || denom <= 0 || T < 3
            continue; % leave NaN
        end

        % lag-1
        num1 = sum(e(2:end) .* e(1:end - 1));
        ac1 = num1 / denom;
        ac1_vec(v) = abs(ac1);

        % mean |AC| over lags 1..L
        acc = 0;

        for k = 1:L
            numk = sum(e(1 + k:end) .* e(1:end - k));
            acc = acc + abs(numk / denom);
        end

        acm_vec(v) = acc / L;
    end

    acm_mean = mean(acm_vec(~isnan(acm_vec)));
    ac1_mean = mean(ac1_vec(~isnan(ac1_vec)));

    if isempty(acm_mean) || ~isfinite(acm_mean)
        acm_mean = NaN;
    end

    if isempty(ac1_mean) || ~isfinite(ac1_mean)
        ac1_mean = NaN;
    end

end
