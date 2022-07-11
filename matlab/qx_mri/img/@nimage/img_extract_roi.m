function ts = img_extract_roi(obj, roi, rcodes, method, weights, criterium)

%``function ts = img_extract_roi(obj, roi, rcodes, method, weights, criterium)``
%
%   Extracts roi data for all specified ROI in the ROI image. Uses specified
%   method of averaging data.
%
%   INPUTS
%   ======
%
%    --obj         current image
%   --roi         roi image file
%   --rcodes      roi values to use [all but 0]
%   --method      method name [mean]
%
%                 - 'mean'      ... average value of the ROI
%                  - 'median'    ... median value across the ROI
%                 - 'pca'       ... first eigenvariate of the ROI
%                 - 'threshold' ... average of all voxels above threshold
%                 - 'maxn'      ... average of highest n voxels
%                 - 'weighted'  ... weighted average across ROI voxels
%                 - 'all'       ... all voxels within a ROI 
%
%   --weights     image file with weights to use []
%   --criterium   threshold or number of voxels to extract []
%
%   OUTPUT
%   ======
%
%   ts
%   

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 6; criterium = [];  end
if nargin < 5; weights = [];    end
if nargin < 4; method = [];     end
if nargin < 3; rcodes = [];     end

if isempty (method) method = 'mean'; end

method = lower(method);

% ---- check method

if ~ismember(method, {'mean', 'pca', 'threshold', 'maxn', 'weighted', 'median', 'all'})
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

if isa(roi, 'nimage')
    if obj.voxels ~= roi.voxels;
        error('ERROR: ROI image does not match target in dimensions!');
    end
else
    roi = reshape(roi, [], 1);
    if size(roi, 1) ~= obj.voxels
        error('ERROR: ROI mask does not match target in size!');
    end
    roi = nimage(roi);
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
    if isa(weights, 'nimage')
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

if strcmp(method, 'all')
    ts = {};
else
    ts = zeros(nrois, obj.frames);
end

for r = 1:nrois

    tmp = target(roi.img_roi_mask(rcodes(r)), :);

    if isempty(tmp) && not(strcmp(method, 'all'))
        ts(r, :) = 0;
        continue
    end

    switch method

        case 'mean'
            ts(r, :) = mean(tmp, 1);

        case 'median'
            ts(r, :) = median(tmp, 1);

        case 'weighted'
            tmpw = weights(roi.img_roi_mask(rcodes(r)), :);
            if size(tmpw, 2) == 1
                tmpw = repmat(tmpw, 1, obj.frames);
            end
            ts(r, :) = mean(tmp .* tmpw, 1);

        case 'threshold'
            tmpw = weights(roi.img_roi_mask(rcodes(r)), :);
            tmpm = tmpw >= criterium;
            ts(r, :) = mean(tmp(tmpm, :), 1);

        case 'maxn'
            tmpw = weights(roi.img_roi_mask(rcodes(r)), :);
            tmpr = sort(tmpw, 'descend');
            tmpt = tmpr(criterium);
            tmpm = tmpw >= tmpt;
            ts(r, :) = mean(tmp(tmpm, :), 1);

        case 'pca'
            [coeff, score] = pca(tmp');
            ts(r, :) = score(:,1)';

        case 'all'
            ts{r} = tmp;
    end
end

