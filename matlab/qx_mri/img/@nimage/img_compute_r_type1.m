function [B, Z] = img_compute_r_type1(obj, bdata, verbose)

%``img_compute_r_type1(obj, bdata, verbose)``
%
%   Computes whole brain regression and significances using Type I Sum of
%   squares.
%
%   INPUTS
%   =====
%
%    --obj
%       nimage image object
%   --bdata   
%       Data matrix to compute linear regression with and estimate significances.
%   --verbose 
%       Should it talk a lot [no]
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
%   returns Type I Sum of squares based significance for each regressor.
%   Specifically, it first computes intercept and then adds each regressor,
%   comparing each residual SS with the previous one using an F-test. In essence
%   it provides an estimate of statistical significance of improvement of fit by
%   adding each of the regressors in order.
%
%   It returns a beta image (B) with beta values for each of the regressors when
%   they were first added to the regression, and Z, a significance map for
%   addition of each of the regressors in order.
%
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
if verbose, fprintf('\n\nComputing GLM on %s with %d regressors, using Type I SS', fullfile(obj.filepath, obj.filename), nX), end

% ---- prepare data

if verbose, fprintf('\n... setting up data'), end

B = zeroframes(obj, nX);
Z = zeroframes(obj, nX);

% ---- do the loop

X = [ones(size(bdata,1)), bdata];
data = obj.data;

[Blast RSSlast Plast] = img_glm_fit2(obj, X(:,1));
for n = 1:nX
    [Bthis RSSthis Pthis] = img_glm_fit2(obj, X(:,1:n+1));
    F = ((RSSlast.data - RSSthis.data)./(Pthis-Plast)) ./ (RSSthis.data ./(obj.frames-Pthis));
    Z.data(:,n) = norminv(fcdf(F, Pthis-Plast, obj.frames-Plast), 0, 1);
    B.data(:,n) = Bthis.data(:,n+1);
    Blast   = Bthis;
    RSSlast = RSSthis;
    Plast   = Pthis;
end

if verbose, fprintf('\n... done!'), end


