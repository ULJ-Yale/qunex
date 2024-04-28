function [p Z M SE t] = img_ttest_zero(obj, verbose)

%``img_ttest_zero(obj, verbose)``
%
%    Computes t-test against zero across all the volumes in the image.
%
%   INPUTS
%   ======
%
%    --obj       the images to work on
%   --verbose   should it talk a lot [false]
%
%   OUTPUTS
%   =======
%
%   p
%       an image with p-values
%
%   t
%       an image with t-values
%
%   Z
%       an image with Z-scores converted from p-values
%
%   M
%       an image with means across all volumes
%
%   SE
%       an image with standard errors of means across all volumes
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2
    verbose = false;
end


% ---- prepare data

if verbose, fprintf('\nSetting up data'), end

obj.data = obj.image2D;
obj = obj.sliceframes(~isnan(mean(obj.data)));

M = obj.zeroframes(1);
p = obj.zeroframes(1);

% ---- compute t-test

if verbose, fprintf('\nComputing t-test'), end

if nargout > 3
    [h, p.data, c, s] = ttest(obj.data, 0, 'Alpha', 0.05, 'Tail', 'both', 'Dim', 2);
else
    [h, p.data] = ttest(obj.data, 0, 'Alpha', 0.05, 'Tail', 'both', 'Dim', 2);
end

M.data = mean(obj.data, 2, "omitnan");

% ---- compute Z scores

if nargout > 1
    if verbose, fprintf('\nComputing Z-scores'), end
    Z = obj.zeroframes(1);
    Z.data = norminv((1-(p.data./2)), 0, 1) .* sign(M.data);
end

% ---- compute SE

if nargout > 3
    if verbose, fprintf('\nComputing standard error'), end
    SE = obj.zeroframes(1);
    SE.data = s.sd ./ sqrt(obj.frames);
end

% ---- extract t-values

if nargout > 4
    if verbose, fprintf('\nExtracting t-values'), end
    t = obj.zeroframes(1);
    t.data = s.tstat;
end

% ---- done

if verbose, fprintf('\n... done!\n'), end

