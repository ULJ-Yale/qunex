function glm_print_ar1_debug(label, R)
%``function glm_print_ar1_debug(label, R)``
%
%   Compute and print a quick pooled AR(1) estimate for residuals matrix R,
%   skipping an initial burn-in portion to avoid transient effects.
%
%   Inputs:
%       label (char)
%           Label to include in the diagnostic line
%
%       R (matrix [T x V])
%           Residuals (time x voxels/parcels)
%
%   Outputs:
%       (none)  Prints a diagnostic line to stdout
%
%   Notes:
%       - Burns ~1%% of the beginning (min 5, max 10 frames) before computing.
%       - Prints: [AR1 <label>]  rho = <value>  (T=?, Vox=?)
%

% SPDX-FileCopyrightText: 2025 QuNex development team
%
% SPDX-License-Identifier: GPL-3.0-or-later

    if isempty(R), return; end
    burn = min(10, max(5, round(size(R, 1) * 0.01))); % e.g., first 1 % or at least 5, capped 10

    if size(R, 1) > burn
        R = R(1 + burn:end, :);
    end

    T = size(R, 1); P = size(R, 2);
    num = 0; den = 0;

    for v = 1:P
        e = R(:, v) - mean(R(:, v));
        num = num + sum(e(2:end) .* e(1:end - 1));
        den = den + sum(e(1:end - 1) .^ 2);
    end

    rho = num / max(den, eps);
    fprintf('[AR1 %s]  ρ = %+0.4f  (T=%d, Vox=%d)\n', label, rho, T, P);
end
