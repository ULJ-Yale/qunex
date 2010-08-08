function [obj, commands] = mri_fcMRISegment(obj, smask, tmask, options, verbose)

%function [obj, commands] = mri_fcMRISegment(obj, ssmask, tmask, options, verbose)
%	
%	Computes WTA segmentation of source mask voxels based on target mask ROI
%	
%	obj     - bold image to use for segmentation
%   smask   - source mask defining voxels to be segmented
%   tmask   - target mask defining ROI to correlate source voxels with
%   options - should we use absolute or raw correlations for WTA [raw]
%   verbose - should it talk a lot [no]
%
%   Returns WTA results and correlations with each target ROI.
%   Returned image is masked!
%
%   Grega Repovš, 2010-08-07
%

if nargin < 5
    verbose = false;
    if nargin < 4;
        options = 'raw';
        if nargin < 3
            error('ERROR: Both source and target mask need to be specified to carry out mri_fcMRISegment!')
        end
    end
end

% ---- Checks sizes

if (obj.dim ~= smask.dim) | (obj.dim ~= tmask.dim)
    error('ERROR: Image data and both masks have to be the same size!')
end

% ---- Start

if verbose, fprintf('\n\nStarting fcMRISegment on %s', obj.filename), end

% ---- prepare target data

if verbose, fprintf('\n... setting up target data'), end

obj.data = obj.image2D;
tmask.data = tmask.image2D;

ntargets = length(tmask.roi.roinames);
tdata = zeros(ntargets, obj.frames);

for n = 1:ntargets
    tdata(n,:) = mean(obj.data(ismember(tmask.data, n),:),1);
end

tdata = zscore(tdata, 0, 2);
tdata = tdata ./ sqrt(obj.frames -1);
tdata = tdata';

% ---- prepare source and results data

if verbose, fprintf('\n... setting up source data'), end

if ~obj.masked
    if ~isempty(smask)
        obj = obj.maskimg(smask);
    end
end

if ~obj.correlized    
    obj = obj.correlize;
end

results = zeros(obj.voxels, ntargets+1);


% ---- compute correlations

data = obj.data;

if verbose, fprintf('\n... %d source voxels, %d target ROI over %d frames to process ', obj.voxels, ntargets, obj.frames), end

results(:,2:ntargets+1) = obj.data * tdata;

if strcmp(options, 'absolute')
    results = abs(results);
end

[C, results(:,1)] = max(results(:,2:ntargets+1),[],2);

obj.data = results;
obj.frames = ntargets+1;
obj.roi = tmask.roi;


if verbose, fprintf('\n... done!'), end

