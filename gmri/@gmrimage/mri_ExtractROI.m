function ts = mri_ExtractROI(obj, roi, rcodes, method, weights, criterium)

%function ts = mri_ExtractROI(obj, roi, rcodes, method, weights, criterium)
%
%	Extracts roi data for all specified ROI in the ROI image
%   Uses specified method of averaging data
%
%	obj    - current image
%   roi    - roi image file
%   rcodes - roi values to use [all but 0]
%   method - method name [mean]
%      'mean'       - average value of the ROI
%	   'median'     - median value across the ROI
%      'pca'        - first eigenvariate of the ROI
%      'threshold'  - average of all voxels above threshold
%      'maxn'       - average of highest n voxels
%      'weighted'   - weighted average across ROI voxels
%   weights         - image file with weights to use []
%   criterium       - threshold or number of voxels to extract []
%
%
%   Grega Repovš, 2009-11-08
%
%   ---- Changelog ----
%
%   Grega Repovs, 2013-07-24 ... Adjusted to use multivolume ROI objects
%   Grega Repovs, 2018-03-18 ... Added 'median' as an option for extraction method

if nargin < 6; criterium = [];  end
if nargin < 5; weights = [];    end
if nargin < 4; method = [];     end
if nargin < 3; rcodes = [];     end

if isempty (method) method = 'mean'; end

method = lower(method);

% ---- check method

if ~ismember(method, {'mean', 'pca', 'threshold', 'maxn', 'weighted', 'median'})
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
    if obj.voxels ~= roi.voxels;
        error('ERROR: ROI image does not match target in dimensions!');
    end
else
    roi = reshape(roi, [], 1);
    if size(roi, 1) ~= obj.voxels
        error('ERROR: ROI mask does not match target in size!');
    end
    roi = gmrimage(roi);
end

if isempty (rcodes)
    if isfield(roi.roi, 'roicodes') && ~isempty(roi.roi.roicodes)
        rcodes = roi.roi.roicodes;
    else
        rcodes = unique(roi.data);
        rcodes = rcodes(rcodes ~= 0);
    end
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
            error('ERROR: Weights image does not match target in size!');
        end
    end
end

% ---- start the loop


nrois = length(rcodes);
target = obj.image2D;
ts = zeros(nrois, obj.frames);

for r = 1:nrois

    tmp = target(roi.mri_ROIMask(rcodes(r)), :);

    if isempty(tmp)
        ts(r, :) = 0;
        continue
    end

    switch method

        case 'mean'
            ts(r, :) = mean(tmp, 1);

        case 'median'
            ts(r, :) = median(tmp, 1);

        case 'weighted'
            tmpw = weights(roi.mri_ROIMask(rcodes(r)), :);
            if size(tmpw, 2) == 1
                tmpw = repmat(tmpw, 1, obj.frames);
            end
            ts(r, :) = mean(tmp .* tmpw, 1);

        case 'threshold'
            tmpw = weights(roi.mri_ROIMask(rcodes(r)), :);
            tmpm = tmpw >= criterium;
            ts(r, :) = mean(tmp(tmpm, :), 1);

        case 'maxn'
            tmpw = weights(roi.mri_ROIMask(rcodes(r)), :);
            tmpr = sort(tmpw, 'descend');
            tmpt = tmpr(criterium);
            tmpm = tmpw >= tmpt;
            ts(r, :) = mean(tmp(tmpm, :), 1);

        case 'pca'
            [coeff, score] = princomp(tmp');
            ts(r, :) = score(:,1)';
    end
end

