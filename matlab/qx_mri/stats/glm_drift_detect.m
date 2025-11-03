function drift_cols = glm_drift_detect(X, seg_id, tol, maxperseg)
%``function drift_cols = glm_drift_detect(X, seg_id, tol, maxperseg)``
%
%   Detect columns in design matrix X that behave like drift regressors
%   (per-run baseline + linear trend). Intended to protect such drifts from
%   whitening filters.
%
%   Inputs:
%       X (matrix [T x p])
%           Design matrix
%
%       seg_id (vector [T x 1])
%           Integer segment IDs (one per time point)
%
%       tol (scalar, default 0.9995)
%           R^2 threshold to classify as drift
%
%       maxperseg (scalar, default 2)
%           Max drift regressors per segment
%
%   Outputs:
%       drift_cols (vector [k x 1])
%           Column indices in X likely to be drift terms
%
%   Method:
%       A column x is classified as drift if it is well explained by a drift
%       basis of (per-run intercept + linear trend). We build a block-diagonal
%       drift basis per segment, then test each column's R^2 against that basis.
%
%   Notes:
%       - MATLAB + GNU Octave compatible
%       - Conservative defaults
%

% SPDX-FileCopyrightText: 2025 QuNex development team
%
% SPDX-License-Identifier: GPL-3.0-or-later

    if nargin < 3 || isempty(tol)
        tol = 0.9995;
    end

    if nargin < 4 || isempty(maxperseg)
        maxperseg = 2;
    end

    segs = unique(seg_id(:));
    segs(isnan(segs)) = [];

    T = size(X, 1);
    P = size(X, 2);

    % --------------------------------------------------------
    % Build per-segment drift basis S:
    %   segment intercept + segment linear trend
    % --------------------------------------------------------
    S = [];

    for s = segs'
        idx = find(seg_id == s);
        t = (0:numel(idx) - 1)'; % 0..(len-1)
        Sseg = [ones(numel(idx), 1), detrend(t, 'constant')]; % intercept + centered slope
        S = blkdiag(S, Sseg);
    end

    % Precompute projection matrix onto orthogonal residual space
    StS = S' * S;
    StS_inv = pinv_safe(StS);
    Pperp = @(v) v - S * (StS_inv * (S' * v)); % residual after removing drift subspace

    drift_cols = [];

    % --------------------------------------------------------
    % Score each X-column by R^2 using drift basis
    % --------------------------------------------------------
    for j = 1:P
        xj = X(:, j);
        r = Pperp(xj);
        R2 = 1 - (r' * r) / max((xj - mean(xj))' * (xj - mean(xj)), eps);

        if R2 >= tol
            drift_cols(end + 1) = j; %#ok<AGROW>
        end

    end

    % --------------------------------------------------------
    % Limit number of drift columns (safety cap)
    % --------------------------------------------------------
    maxcols = maxperseg * numel(segs);

    if numel(drift_cols) > maxcols
        R2s = zeros(size(drift_cols));

        for k = 1:numel(drift_cols)
            xj = X(:, drift_cols(k));
            r = Pperp(xj);
            R2s(k) = 1 - (r' * r) / max((xj - mean(xj))' * (xj - mean(xj)), eps);
        end

        % keep top maxcols in terms of R2
        [~, order] = sort(R2s, 'descend');
        drift_cols = drift_cols(order(1:maxcols));
    end

    drift_cols = unique(drift_cols);
end

% ================== Helpers ==================
function Ainv = pinv_safe(A)
    % Safe pseudoinverse (no warnings)
    [U, S, V] = svd(A, 'econ');
    s = diag(S);
    thr = max(size(A)) * eps(max(s));
    s(s < thr) = 0;
    s(s > 0) = 1 ./ s(s > 0);
    Ainv = V * diag(s) * U';
end
