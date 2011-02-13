function [B, res, rvar, Xdof] = mri_GLMFit(obj, X)

%   function [B, rvar, Xdof, res] = mri_GLMFit(obj, X)
%	
%	Computes GLM fit to whole brain
%	
%   Input parameters
%	    obj     - image
%       X       - predictor matrix (frames x predictors)
%
%   Outputs
%       B       - beta weights image
%       rvar    - variance of the residual
%       Xdof    - model degrees of freedom
%       res     - residual image
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
