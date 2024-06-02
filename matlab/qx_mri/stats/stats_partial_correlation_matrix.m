function [p] = stats_partial_correlation_matrix(X, Z, verbose)

%function [p] = stats_partial_correlation_matrix(X, Z)
%
%   Computes partial correlation for each column in X with each column in Z,
%   partialing out other columns in Z.
%
%   INPUTS
%   ======
%
%   --X
%   --Z
%   --verbose   should it talk a lot [false]
%   
%   OUTPUT
%   ======
%
%   p
%       matrix n x m where n is number of column in X and m number of vars in Z
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 3
    verbose = false;
    if nargin < 2
        error('\nERROR: Two matrices are needed to run stats_partial_correlation_matrix!\n');
    end
end

% ======================================================
% -------------- Setting up variables

nvar = size(Z,2);
nsam = size(Z,1);
ncor = size(X,2);
p = zeros(ncor,nvar);

% ======================================================
% -------------- Starting up main loop

if verbose, fprintf('\nStarting computation of partial correlations '), end

for n = 1:nvar
    mask = zeros(1, nvar);
    mask(n) = 1;
    
    x = resid([X Z(:,mask==1)],[ones(nsam,1) Z(:,mask==0)]);
    x = zscore(x, 0, 1) ./ sqrt(nsam-1);
    z = x(:,ncor+1);
    x = x(:,1:ncor);
    
    p(:,n) = x' * z;
    if verbose, fprintf('.'), end
end

if verbose, fprintf(' done.\n'), end



% ======================================================
%                     ---> helper - compute GLM residuals


function [r] = resid(X, Z)

r = X - Z * ((inv(Z'*Z)*Z')*X);


