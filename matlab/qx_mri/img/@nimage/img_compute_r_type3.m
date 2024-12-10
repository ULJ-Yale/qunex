function [B, Z] = img_compute_r_type3(obj, bdata, verbose)

%``img_compute_r_type3(obj, bdata, verbose)``
%
%   Computes whole brain regression and significances using Type III Sum of
%   squares.
%
%   INPUTS
%   ======
%
%   --obj       nimage image object
%   --bdata     Data matrix to compute linear regression with and estimate 
%               significances.
%   --verbose   Should it talk a lot [no]
%
%   OUTPUTS
%   =======
%
%   B
%       Beta values image for each of the regressors
%
%   Z
%       Z converted p-values for each of the regressors
%
%   USE
%   ===
%
%   The method performs a linear regression of each column of the bdata and
%   returns Type III SS based significance for each regressor. Specifically, it
%   adds an intercept and first computes a regression and the resulting sum of
%   squares for the full model. Then it computes regression of models for which
%   it takes out one of the regressors and using an F-test compares the
%   resulting sums of squares. In essence it provides an estimate of statistical
%   significance of improvement of fit of the model due to each of regressors by
%   controlling for all the other regressors
%
%   It returns a beta image (B) with beta values for each of the regressors for
%   the full model, and Z, a significance map of significances of adding the
%   regressor.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 3
    verbose = false;
    if nargin < 2
        error('ERROR: No data provided to compute GLM!')
    end
end

if obj.frames ~= size(bdata,1)
    error('ERROR: data matrix file does not match number of image frames!')
end

nX = size(bdata, 2);
if verbose, fprintf('\n\nComputing GLM on %s with %d regressors, using Type III SS', obj.filenamepath, nX), end

% ---- prepare data

if verbose, fprintf('\n... setting up data'), end

B = zeroframes(obj, nX);
Z = zeroframes(obj, nX);

% ---- do the loop

X = [ones(size(bdata,1)), bdata];
data = obj.data;

[Ball RSSall Pall] = img_glm_fit2(obj, X);
B.data = Ball.data(:,2:end);
for n = 1:nX
    mask = ones(1, nX+1);
    mask(n+1) = 0;
    [Bthis RSSthis Pthis] = img_glm_fit2(obj, X(:,mask==1));
    F = ((RSSthis.data - RSSall.data)./(Pall-Pthis)) ./ (RSSall.data ./(obj.frames-Pall));
    Z.data(:,n) = norminv(fcdf(F, Pall-Pthis, obj.frames-Pall), 0, 1);
end

if verbose, fprintf('\n... done!'), end


