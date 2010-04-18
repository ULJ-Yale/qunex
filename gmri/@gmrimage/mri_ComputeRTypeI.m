function [B, Z] = mri_ComputeRTypeI(obj, bdata, verbose)

%   function [B, Z] = mri_ComputeRTypeI(obj, bdata, verbose)
%	
%	Computes whole brain regression and significances using Type I SS
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
if verbose, fprintf('\n\nComputing GLM on %s with %d regressors, using Type I SS', obj.filename, nX), end

% ---- prepare data

if verbose, fprintf('\n... setting up data'), end

B = zeroframes(obj, nX);
Z = zeroframes(obj, nX);

% ---- do the loop

X = [ones(size(bdata,1)), bdata];
data = obj.data;

[Blast RSSlast Plast] = mri_GLMFit2(obj, X(:,1));
for n = 1:nX
    [Bthis RSSthis Pthis] = mri_GLMFit2(obj, X(:,1:n+1));
    F = ((RSSlast.data - RSSthis.data)./(Pthis-Plast)) ./ (RSSthis.data ./(obj.frames-Pthis));
    Z.data(:,n) = icdf('normal', cdf('F', F, Pthis-Plast, obj.frames-Plast), 0, 1);
    B.data(:,n) = Bthis.data(:,n+1);
    Blast   = Bthis;
    RSSlast = RSSthis;
    Plast   = Pthis;
end

if verbose, fprintf('\n... done!'), end

     
