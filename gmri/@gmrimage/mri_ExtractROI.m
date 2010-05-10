function ts = mri_ExtractROI(obj, roi, rcodes, method, weights, criterium)

%function ts = mri_ExtractROI(obj, roi, rcodes, method, weights, criterium)
%	
%	Extracts roi data for all specified ROI in the ROI image
%   Uses specified method of averaging data
%	
%	obj    - current image
%   roi    - roi image file
%   rcodes - roi values to use [all but 0]
%   method - method name [average]
%	   'mean'       - average value of the ROI
%      'pca'        - first eigenvariate of the ROI
%      'threshold'  - average of all voxels above threshold
%      'maxn'       - average of highest n voxels
%      'weighted'   - weighted average across ROI voxels
%   weights         - image file with weights to use
%   criterium       - threshold of number of voxels to extract
%
%
%   Grega Repovš, 2009-11-08
%


if nargin < 6;
    criterium = [];
    if nargin < 5
        weights = [];
        if nargin < 4
            method = 'mean';
            if nargin < 3
                rcodes = [];
            end
        end
    end
end

method = lower(method);

% ---- check method

if ~ismember(method, {'mean', 'pca', 'threshold', 'maxn', 'weighted'})
    error('ERROR: Unrecognized method of computing ROI mean!')
end

% ---- check data dependencies

if ismember(method, {'threshold', 'maxn', 'weighted'})
    if isempty(weights)
        error('ERROR: Weights image needed to extract ROI using %s method!', method);
    end    
end

if ismember(method, {'threshold', 'maxn'})
    if isempty(criterium)
        error('ERROR: Criterium needed to extract ROI using %s method!', method);
    end    
end


% ---- check ROI data

if isa(roi, 'gmrimage')
    if ~obj.issize(roi);
        error('ERROR: ROI image does not match target in dimensions!');
    end
    roi = roi.image2D;
else
    roi = reshape(roi, [], 1);
    if size(roi, 1) ~= obj.voxels
        error('ERROR: ROI mask does not match target in size!');
    end    
end

if isempty (rcodes)
    rcodes = unique(roi);
    rcodes = rcodes(rcodes ~= 0);
end

% ---- check weights data

if ~isempty(weights)
    if isa(weights, 'gmrimage')
        if ~obj.issize(weights);
            error('ERROR: ROI image does not match target in dimensions!');
        end
        weights = weights.image2D;
    else
        weights = reshape(weights, [], 1);
        if size(weights, 1) ~= obj.voxels
            error('ERROR: ROI mask does not match target in size!');
        end    
    end
end

% ---- start the loop


nrois = length(rcodes);
target = obj.image2D;
ts = zeros(nrois, obj.frames);

for r = 1:nrois
    
    tmp = target(roi == rcodes(r), :);
    
    switch method
    
        case 'mean'
            ts(r, :) = mean(tmp, 1);
            
        case 'weighted'
            tmpw = weights(roi == rcodes(r), :);
            if size(tmpw, 2) == 1
                tmpw = repmat(tmpw, 1, obj.frames);
            end            
            ts(r, :) = mean(tmp .* tmpw, 1);
            
        case 'threshold'
            tmpw = weights(roi == rcodes(r), :);
            tmpm = tmpw >= criterium;
            ts(r, :) = mean(tmp(tmpm, :), 1);
            
        case 'maxn'
            tmpw = weights(roi == rcodes(r), :);
            tmpr = sort(tmpw, 'descend');
            tmpt = tmpr(criterium);
            tmpm = tmpw >= tmpt;
            ts(r, :) = mean(tmp(tmpm, :), 1);
            
        case 'pca'
            [coeff, score] = princomp(tmp');
            ts(r, :) = score(:,1)';
    end
end
        
