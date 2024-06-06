function ts = img_extract_roi(obj, roi, rcodes, method, weights, criterium, return_img)

%``function ts = img_extract_roi(obj, roi, rcodes, method, weights, criterium, return_img)``
%
%   Extracts roi data for all specified ROI in the ROI image. Uses specified
%   method of averaging data.
%
%   Parameters:
%       --obj (nimage):
%           Current image.
%       --roi (nimage):
%           ROI image file.
%       --rcodes (array):
%           ROI values to use, default is all ROI present in roi but 0.
%       --method (str, default 'mean'):
%           The method to use to obtain an ROI representative value.
%
%           - 'mean'           ... average value of the ROI
%           - 'median'         ... median value across the ROI
%	        - 'max'            ... maximum value across the ROI
%	        - 'min'            ... minimum value across the ROI
%           - 'pca'            ... first eigenvariate of the ROI
%           - 'threshold'      ... average of all voxels above threshold  
%           - 'maxn'           ... average of highest n voxels
%           - 'weighted_mean'  ... weighted average across ROI voxels
%           - 'weighted_sum'   ... weighted average across ROI voxels
%           - 'all'            ... all voxels within a ROI 
%
%       --weights (nimage, matrix):
%           If ROI is a regular nimage object or a matrix used as a mask, then 
%           weights should be either a nimage file with weights to use or a 
%           matrix with weights to use. In both cases it has to be of the same
%           size as obj.
%           If roi is an ROI image specification object that includes weights
%           for each roi, those weights will be used.
%       --criterium (float, default []):
%           Additional parameter needed for extraction using 'threshold' (a 
%           threshold value) or 'maxn' (number of voxels) methods.
%       --return_img (boolean, default false):  
%           Whether to return a parcellated nimage.
%
%   Output:
%       ts
%           A time series of the ROI data or a parcellated nimage.
%           If rcodes are provided, the rows are in the order of the rcodes.
%   
%   Notes:
%       If weights parameter is provided, the 'threshold', 'maxn', and 'weighted'
%       methods will use the weights profided in the weights parameter. 
%       If weights parameter is empty, then the weights provided in the roi
%       structure of the roi object will be used.

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 7; return_img = false; end
if nargin < 6; criterium  = [];    end
if nargin < 5; weights    = [];    end
if nargin < 4; method     = [];    end
if nargin < 3; rcodes     = [];    end

if isempty (method), method = 'mean'; end

method = lower(method);

% ---- check method
if ~ismember(method, {'mean', 'pca', 'max', 'min', 'threshold', 'maxn', 'weighted_sum', 'weighted_mean', 'median', 'all'})
    error('ERROR: Unrecognized method of computing ROI mean!')
end

% ---- check data dependencies
if ismember(method, {'threshold', 'maxn'})
    if isempty(criterium)
        error('ERROR: Criterium needed to extract ROI using %s method!', method);
    end
end

% ---- check ROI data

% --> is it a ptseries

if isa(roi, 'char') || isa(roi, 'string')

    if starts_with(roi, 'parcels:')

        if ~isfield(obj.cifti, 'parcels') || isempty(obj.cifti.parcels)
            error('ERROR: The file lacks parcel specification!');
        end

        parcels = strtrim(regexp(roi(9:end), ',', 'split'));

        if length(parcels) == 1 && strcmp(parcels{1}, 'all')
            parcels = obj.cifti.parcels;
        end

        if isempty(rcodes)
            rcodes = parcels;
        else
            if isa(rcodes, 'char')
                rcodes = strtrim(regexp(rcodes, ',', 'split'));
            else
                error('ERROR: When parcels are requested, rcodes has to be a character array!');
            end
        end

        [tf, rows] = ismember(rcodes, obj.cifti.parcels);
        ts = obj.data(rows, :);
        return
    else
        error('ERROR: Unknown ROI specification [%s]!', roi);
    end

end

% --> is it a numeric mask

if ~isa(roi, 'nimage')
    roi = reshape(roi, [], 1);

    if size(roi, 1) ~= obj.voxels
        error('ERROR: ROI mask does not match target in size!');
    end

    roi = nimage(roi);
end

% --> do the sizes match

if obj.voxels ~= roi.voxels;
    error('ERROR: ROI image does not match target in dimensions!');
end

% --> is it a an old roi object

if isfield(roi.roi, 'roicodes')
    roi = nimage.img_prep_roi(roi);    
end

% --> is it a new roi object

if ~isfield(roi.roi, 'roiname')
    roi = nimage.img_prep_roi(roi);
end

% --> do we have weights

if ~isempty(weights)
    if isa(weights, 'nimage')
        weights = weights.image2D;
        weights = weights(:,1);
    else
        weights = reshape(weights, [], 1);
    end
    wvox = size(weights, 1);            
    if wvox ~= roi.voxels
        error('ERROR: Weights mask does not match target in dimensions!');
    end
    for r = 1:length(roi.roi)
        roi.roi(r).weights = weights(roi.roi(r).indeces);
    end
end

% --> process rcodes

if isempty(rcodes)
    rindeces = 1:length(roi.roi);
else
    % --- Check whether we have ROI names or ROI codes
    if iscell(rcodes) && all(cellfun(@ischar, rcodes))
        % rindeces = find(ismember({roi.roi.roiname}, rcodes));
        [~, rindeces] = ismember(rcodes, {roi.roi.roiname});
    elseif isnumeric(rcodes)
        % rindeces = find(ismember([roi.roi.roicode], rcodes));
        [~, rindeces] = ismember(rcodes, [roi.roi.roicode]);
    else
        error('ERROR (img_extract_roi) invalid specification of roi to extract!');
    end
end
rnames = {roi.roi(rindeces).roiname};

% --> check weights
if ismember(method, {'threshold', 'maxn', 'weighted_sum', 'weighted_mean'})
    if any(arrayfun(@(x) isempty(x.weights), roi.roi))
        error('ERROR: Weights have to be provided either in roi structure or separately to extract ROI using %s method!', method);
    end
end

% ---- start the loop
nrois = length(rindeces);
target = obj.image2D;

if strcmp(method, 'all')
    ts = {};
else
    ts = zeros(nrois, obj.frames);
end

for r = 1:nrois

    % -> extract the relevant timeseries

    tmp = target(roi.roi(rindeces(r)).indeces, :);    

    if isempty(tmp) && not(strcmp(method, 'all'))
        ts(r, :) = 0;
        continue
    end

    % -> prepare weights if needed

    if ismember(method, {'weighted_sum', 'weighted_mean', 'threshold', 'maxn'})
        tmpw = roi.roi(rindeces(r)).weights;
        if isempty(tmpw)
            tmpw = ones(size(tmp, 1));
        end
        tmpw = reshape(tmpw, [],1);
    end

    % -> compute requested values

    switch method

        case 'mean'
            ts(r, :) = mean(tmp, 1);

        case 'median'
            ts(r, :) = median(tmp, 1);
        
        case 'max'
            ts(r, :) = max(tmp, [], 1);

        case 'min'
            ts(r, :) = max(tmp, [], 1);

        case 'weighted_sum'
            ts(r, :) = sum(bsxfun(@times, tmp, tmpw), 1);

        case 'weighted_mean'
            ts(r, :) = mean(bsxfun(@times, tmp, tmpw), 1);

        case 'threshold'
            tmpm = tmpw >= criterium;
            ts(r, :) = mean(tmp(tmpm, :), 1);

        case 'maxn'
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

% ---- return nimage if requested
if return_img
    img = obj.img_create_parcellated_metadata(roi, rnames);
    img.data = ts;
    ts = img;
end
    
end