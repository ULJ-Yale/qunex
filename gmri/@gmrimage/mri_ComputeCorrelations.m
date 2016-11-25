function [correlations, significances] = mri_ComputeCorrelations(obj, bdata, verbose, cv)

%function [correlations, significances] = mri_ComputeCorrelations(obj, bdata, verbose, cv)
%
%	For each voxel, computes correlation with the provided (behavioral or other) data.
%
%   INPUT
%	obj     - gmrimage object
%   bdata   - data matrix to compute correlations with
%   verbose - should it talk a lot [no]
%   cv      - should it compute covariances instead of correlations
%
%   OUTPUT
%   correlations  - a gmrimage object with computed correlations.
%   significances - a gmrimage of p-values for each of the correlation.
%
%   USE
%   The method computes correlations of each voxel with each column of the bdata matrix.
%   the bdata matrix can have any number of columns, but has to have the same number of
%   rows as there are frames in the original image. The first frame of the resulting images
%   will hold for each voxel the correlation / p-value of its original dataseries across
%   frames, with the first column of the bdata. In a possible use scenario, each frame of the
%   original image can hold an activation or functional connectivity seed-map for one subject
%   while each row of the bdata can hold that person's behavioral data, age, diagnostic values
%   etc. Each frame of the resulting image will hold a map of correlations between activation
%   maps and behavioral variables across subjects.
%
%   If cv is set to true (or non-zero) the computed and reported values will be covariances
%   instead of correlations.
%
%   EXAMPLE USE
%   [rimg, pimg] = img.mri_ComputeCorrelations(behdata);
%
%   (c) Grega Repovš, 2010-03-18
%
%   Change log
%   2014-09-03 - Grega Repovs - Added covariance option.
%   2016-11-25 - Grega Repovs - Updated documentation.
%

if nargin < 4 || isempty(cv),      cv      = false; end
if nargin < 3 || isempty(verbose), verbose = false; end
if nargin < 2 error('ERROR: No data provided to compute correlations!'); end

if obj.frames ~= size(bdata,1)
    error('ERROR: data matrix file does not match number of image frames!')
end

ncorrelations = size(bdata, 2);
if verbose, fprintf('\n\nComputing %d correlations with %s', ncorrelations, obj.filename), end

% ---- prepare data

if verbose, fprintf('\n... setting up data'), end

if cv
    if verbose, fprintf('\n... setting up for covariances instead of correlations '), end
    obj.data = obj.data';
    obj.data = bsxfun(@minus, obj.data, mean(obj.data)) ./ sqrt(obj.voxels-1);
    obj.data = obj.data';
elseif ~obj.correlized && ~cv
    obj = obj.correlize;
end

if cv
    bdata = bdata';
    bdata = bsxfun(@minus, bdata, mean(bdata)) ./ sqrt(obj.voxels-1);
    bdata = bdata';
else
    bdata = zscore(bdata, 0, 1);
    bdata = bdata ./ sqrt(obj.frames -1);
end

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
    if cv
        significances.data(:) = 1;
    else
        significances.data = fc_Fisher(correlations.data);
        significances.data = significances.data/(1/sqrt(obj.frames-3));
    end
end

if verbose, fprintf('\n... done!'), end

end

