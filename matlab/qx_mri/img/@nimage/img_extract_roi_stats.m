function stats = img_extract_roi_stats(obj, roi, rcodes, selection, frames, weight, criterium)

%``function stats = img_extract_roi_stats(obj, roi, rcodes, selection, frames, weight, criterium)``
%
%    Computes satistics for each of the specified ROI for each of the frames.
%   Uses specified method of selecting voxels within ROI.
%
%   INPUTS
%   ======
%
%    --obj         current image
%   --roi         roi image file
%   --rcodes      roi values to use [all but 0]
%   --selection   selection method name [all]
%
%                  - 'all'        ... compute stats across all ROI voxels
%                 - 'threshold'  ... average of all voxels above threshold
%                 - 'maxn'       ... average of highest n voxels
%                 - 'weighted'   ... weighted average across ROI voxels
%
%   --frames      mask or indeces of frames to be used [all]
%   --weight      image file with weights to use for either selection of 
%                 weighted mean computation []
%   --criterium   threshold or number of voxels to extract []
%
%   OUTPUT
%   ======
%
%   stats
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 7; criterium = [];  end
if nargin < 6; weight = [];     end
if nargin < 5; frames = [];     end
if nargin < 4 || isempty(selection); selection = 'all';     end
if nargin < 3; rcodes = [];     end

selection = lower(selection);

% ---- check selection

if ~ismember(selection, {'all', 'threshold', 'maxn', 'weighted'})
    error('ERROR: Unrecognized method of ROI voxel selection!')
end

% ---- check data dependencies

if ismember(selection, {'threshold', 'maxn', 'weighted'})
    if isempty(weight)
        error('ERROR: weight image needed to extract ROI using %s selection method!', selection);
    end
end

if ismember(selection, {'threshold', 'maxn'})
    if isempty(criterium)
        error('ERROR: Criterium needed to extract ROI using %s selection method!', selection);
    end
end

% ---- select frames

if ~isempty(frames)
    obj = obj.sliceframes(obj, frames);
end
target = obj.image2D;

% ---- check ROI data

% --> is it a an old roi object

if isfield(roi.roi, 'roicodes')
    roi = nimage.img_prep_roi(roi);
end

% --> is it a new roi object

if ~isfield(roi.roi, 'roiname')
    roi = nimage.img_prep_roi(roi);
end

if obj.voxels ~= roi.voxels;
    error('ERROR: ROI image does not match target in dimensions!');
end

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

% ---- check weight data

if ~isempty(weight)
    if isa(weight, 'nimage')
        if ~obj.issize(weight);
            error('ERROR: ROI image does not match target in dimensions!');
        end
        weight = weight.image2D;
    else
        weight = reshape(weight, [], 1);
        if size(weight, 1) ~= obj.voxels
            error('ERROR: weight image does not match target in size!');
        end
    end
else
    weight = ones(size(target, 1), 1);
end


% ---- start the loop

nrois = length(rindeces);
nfrms = size(target, 2);

for r = 1:nrois

    stats(r).roiname = roi.roi(rindeces(r)).roiname;
    stats(r).roicode = roi.roi(rindeces(r)).roicode;

    msk = roi.roi(rindeces(r)).indeces;
    tmp = target(msk, :);
    twg = weight(msk, :);
    div = [];

    switch selection

        case 'threshold'
            msk = msk(twg >= criterium);
            tmp = tmp(msk, :);

        case 'maxn'
            twgr = sort(twg, 'descend');
            twgt = twgr(criterium);
            msk  = msk(twg >= twgt);
            tmp  = tmp(msk, :);
    end

    stats(r).N = size(tmp, 1);
    if stats(r).N == 0
        stats(r).median = zeros(1, nfrms);
        stats(r).max    = zeros(1, nfrms);
        stats(r).min    = zeros(1, nfrms);
        stats(r).mean   = zeros(1, nfrms);
        stats(r).sd     = zeros(1, nfrms);
        stats(r).se     = zeros(1, nfrms);
        continue
    elseif stats(r).N == 1
        stats(r).median = tmp;
        stats(r).max    = tmp;
        stats(r).min    = tmp;
        stats(r).mean   = tmp;
        stats(r).sd     = zeros(1, nfrms);
        stats(r).se     = zeros(1, nfrms);
        continue
    end

    stats(r).median = median(tmp);
    stats(r).max = max(tmp);
    stats(r).min = min(tmp);

    if strcmp(selection, 'weighted')
        stats(r).mean = sum(bsxfun(@times, tmp, twg)) ./ sum(twg);
        stats(r).sd   = std(tmp, twg);
        % see: http://www.cs.tufts.edu/~nr/cs257/archive/donald-gatz/weighted-standard-error.pdf
        stats(r).se   = [];
    else
        stats(r).mean = mean(tmp);
        stats(r).sd   = std(tmp);
        stats(r).se   = stats(r).sd ./ sqrt(stats(r).N);
    end

end

