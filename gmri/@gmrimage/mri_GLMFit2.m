function [B, rss, p] = mri_GLMFit2(obj, X)

%   function [B, rss, p] = mri_GLMFit2(obj, X)
%	
%	Computes GLM fit to whole brain, optimized for ANOVA
%	
%   Input parameters
%	    obj     - image
%       X       - predictor matrix (frames x predictors)
%
%   Outputs
%       B       - beta weights image
%       rss     - residual sum of squares
%       p       - number of parameters
%   
%   Grega Repovš, 2010-03-18
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
