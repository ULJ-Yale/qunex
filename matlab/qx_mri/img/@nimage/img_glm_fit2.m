function [B, rss, p] = img_glm_fit2(obj, X)

%`function [B, rss, p] = img_glm_fit2(obj, X)``
%
%	Computes GLM fit to whole brain, optimized for ANOVA.
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
%   rss
%		residual sum of squares
%   p
%		number of parameters
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
%   frame holding the beta value for each of the columns of the X matrix. rss is
%   an image holding the residual sum of squares and p is the number of data
%   points
%
%   EXAMPLE USE
%	===========
%
%   ::
%
%		[B, rss, p] = img.img_glm_fit2(behmatrix);
%

% ---- check input

if nargin < 2
    error('ERROR: Not enough parameters to compute GLM!');
end

if obj.frames ~= size(X, 1)
    error('ERROR: predictor and data number of frames do not match!');
end

% ---- compute GLM

B = obj.zeroframes(size(X,2));
obj.data = obj.image2D';
B.data = (inv(X'*X)*X')*obj.data;

if nargout > 1
    res = (obj.data - X*B.data);

    if nargout > 2
        p = size(X,1);
        rss = obj.zeroframes(1);
        rss.data = sum(res.^2,1)';
    end
end

B.data = B.data';
