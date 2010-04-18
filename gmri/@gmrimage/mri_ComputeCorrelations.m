function [correlations, significances] = mri_ComputeCorrelations(obj, bdata, verbose)

%   function [correlations, significances] = mri_ComputeCorrelations(obj, bdata, verbose)
%	
%	Computes whole brain GBC based on specified mask and command string
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
        error('ERROR: No data provided to compute correlations!')
    end
end

if obj.frames ~= size(bdata,1)
    error('ERROR: data matrix file does not match number of image frames!')
end

ncorrelations = size(bdata, 2);
if verbose, fprintf('\n\nComputing %d correlations with %s', ncorrelations, obj.filename), end

% ---- prepare data

if verbose, fprintf('\n... setting up data'), end

if ~obj.correlized    
    obj = obj.correlize;
end

bdata = zscore(bdata, 0, 1);
bdata = bdata ./ sqrt(obj.frames -1);

correlations = zeroframes(obj, ncorrelations);

% ---- do the loop

voxels = obj.voxels;
data = obj.data;

if verbose, fprintf('\n... computing correlations'), end

for n = 1:ncorrelations
    x = data(n,:)';
    correlations.data(:,n) = data * bdata(:,n);
end

if nargout > 1
    significances = zeroframes(obj, ncorrelations);
    significances.data = fc_Fisher(correlations.data);
    significances.data = significances.data/(1/sqrt(obj.frames-3));
end

if verbose, fprintf('\n... done!'), end

end
     
