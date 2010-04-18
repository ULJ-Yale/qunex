function [B, Z] = mri_ComputeRTypeIII(obj, bdata, verbose)

%   function [B, Z] = mri_ComputeRTypeIII(obj, bdata, verbose)
%	
%	Computes whole brain regression and significances using Type III SS
%	
%	obj     - image
%   bdata   - data matrix to compute correlations with
%   verbose - should it talk a lot [no]
%
%   Grega Repovš, 2010-03-18
%

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
if verbose, fprintf('\n\nComputing GLM on %s with %d regressors, using Type III SS', obj.filename, nX), end

% ---- prepare data

if verbose, fprintf('\n... setting up data'), end

B = zeroframes(obj, nX);
Z = zeroframes(obj, nX);

% ---- do the loop

X = [ones(size(bdata,1)), bdata];
data = obj.data;

[Ball RSSall Pall] = mri_GLMFit2(obj, X);
B.data = Ball.data(:,2:end);
for n = 1:nX
    mask = ones(1, nX+1);
    mask(n+1) = 0;
    [Bthis RSSthis Pthis] = mri_GLMFit2(obj, X(:,mask==1));
    F = ((RSSthis.data - RSSall.data)./(Pall-Pthis)) ./ (RSSall.data ./(obj.frames-Pall));
    Z.data(:,n) = icdf('normal', cdf('F', F, Pall-Pthis, obj.frames-Pall), 0, 1);
end

if verbose, fprintf('\n... done!'), end

     
