function [B, res, rvar, Xdof] = img_glm_fit(obj, X)

%``function [B, res, rvar, Xdof] = img_glm_fit(obj, X)``.
%
%	Computes GLM fit to whole brain
%
%   INPUTS
%	======
%
%	--obj   nimage image object
%   --X     predictor matrix (frames x predictors)
%
%   OUTPUTS
%	=======
%
%   B
%		beta weights image
%   rvar
%		variance of the residual
%   Xdof
%		model degrees of freedom
%   res
%		residual image
%
%   USE
%	===
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
%	===========
%
%   ::
%	
%		[B, res, rvar, Xdof] = img.img_glm_fit2(behmatrix);
%

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

B = obj.zeroframes(size(X,2));
B.data = reshape(B.data,B.frames,B.voxels);
obj.data = obj.image2D';
X = X(:,good);
B.data(good,:) = ((X'*X)\X')*obj.data; % was (INV(X'*X)*X')*obj.data;

if nargout > 1
    res  = obj;
    res.data = (obj.data - X*B.data(good,:))';

    if nargout > 2
        Xdof = size(X,1) - size(X,2);
        rvar = obj.zeroframes(1);
        rvar.data = sum(res.data.^2,2)/Xdof;
    end
end

B.data = B.data';
