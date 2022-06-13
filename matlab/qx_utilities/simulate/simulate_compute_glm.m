function [B, res rvar, Xdof] = simulate_compute_glm(y, X)

%``function [B, res rvar, Xdof] = simulate_compute_glm(y, X)``
%   
%   Function for task structure removal.
%
%   Parameters:
%       --y (timeseries):
%           Timeseries (timepoints x voxels).
%       --X (matrix):
%           Regressor.
%
%   Returns:
%       B
%           Beta coefficients.
%
%       res
%           Residual data.
%
%       rvar
%           Residual variance.
%
%       Xdof
%           Model degrees of freedom.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2
    error('ERROR: Not enough parameters to run task removal!');
end

if size(y,1) ~= size(X,1)
    error('ERROR: timeseries and predictors do not match in length!');
end


% check if we need to add baseline

if(~min(std(X)))
    X = [ones(size(X,1),1) X];
end


% do GLM

B = (inv(X'*X)*X')*y;

if nargout > 1
    res = (y - X*B);
    
    if nargout > 2
        Xdof = size(X,1) - size(X,2);
        rvar = sum(res.^2,2)/Xdof;
    end
end
