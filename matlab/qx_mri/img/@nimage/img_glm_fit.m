function [B, res, rvar, Xdof, B_se, B_z, B_pval] = img_glm_fit(obj, X)

%``img_glm_fit(obj, X)``.
%
%    Computes GLM fit to whole brain
%
%   INPUTS
%    ======
%
%    --obj   nimage image object
%    --X     predictor matrix (frames x predictors)
%
%   OUTPUTS
%    =======
%
%   B
%        beta weights image
%   res
%        residual image
%   rvar
%        variance of the residual
%   Xdof
%        model degrees of freedom
%   B_se
%        standard error of beta weights
%   B_z
%        z scores of beta weights
%   B_pval
%        P-values of beta weights
%
%   USE
%    ===
%
%   The method computes a linear regression between dataseries of each voxel and
%   all the columns of the X regressor matrix. The image can be a series of
%   activation values for a set of sessions, and columns of X behavioral,
%   demographic or other variables. X can have whatever number of columns, but
%   the number of rows need to match the number of frames in the image.
%
%   The results in an image of beta values for each voxel of the image, each
%   frame holding the beta value for each of the columns of the X matrix. res is
%   an image holding the residual remaining after regression. Xdof holds the
%   model's degrees of freedom (ncols - nrows). rvar holds the variance image,
%   the sum of squares of the residuals divided by the model degrees of freedom.
%
%   EXAMPLE USE
%    ===========
%
%   ::
%
%        [B, res, rvar, Xdof] = img.img_glm_fit2(behmatrix);
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% ---- check input

if nargin < 2
    error('ERROR: Not enough parameters to compute GLM!');
end

if obj.frames ~= size(X, 1)
    error('ERROR: predictor and data number of frames do not match!');
end

% ---- zero sd regressors

good = std(X) ~= 0;
good(find(~good & mean(X)==1,1)) = true;

% ---- compute GLM

% ---- image of beta coefficients
B = obj.zeroframes(size(X,2));
B.data = reshape(B.data,B.frames,B.voxels);

% --- extract data from the input image
obj.data = obj.image2D';
y = obj.data;
X = X(:,good);

% ---- estimate beta coefficients
beta = ((X'*X)\X')*y; % was (INV(X'*X)*X')*y;

% ---- embed beta weights to output
B.data(good,:) = beta;

if nargout > 1
    % ---- compute the residuals
    res = obj;
    residuals = (y - X*beta);
    res.data = residuals';

    if nargout > 2
        % ---- compute the degrees of freedom
        Xdof = size(X,1) - size(X,2);

        % ---- compute the mean squared error (MSE)
        MSE = sum(residuals.^2,1) / Xdof;
        rvar = obj.zeroframes(1);
        rvar.data = MSE';
        
        if nargout > 4
            B_se = obj.zeroframes(size(X,2));
            B_se.data = reshape(B_se.data,B_se.frames,B_se.voxels);

            B_z = obj.zeroframes(size(X,2));
            B_z.data = reshape(B_z.data,B_z.frames,B_z.voxels);

            B_pval = obj.zeroframes(size(X,2));
            B_pval.data = reshape(B_pval.data,B_pval.frames,B_pval.voxels);

            % ---- compute the standard error of beta estimates
            var_beta = diag(inv(X'*X));
            SE_beta = sqrt(MSE' * var_beta')';

            % ---- compute the z-scores and p-values for beta estimates
            z_beta = beta  .* (1./SE_beta);
            p_beta = 2 .* (1 - normcdf(abs(z_beta)));

            % ---- embed data to output images
            B_se.data(good,:) = SE_beta;
            B_se.data = B_se.data';
            B_z.data(good,:) = z_beta;
            B_z.data = B_z.data';
            B_pval.data(good,:) = p_beta;
            B_pval.data = B_pval.data';
        end
    end
end

B.data = B.data';
