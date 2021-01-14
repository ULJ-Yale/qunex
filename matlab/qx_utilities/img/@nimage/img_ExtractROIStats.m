function stats = img_ExtractROIStats(obj, roi, rcodes, selection, frames, weight, criterium)

%``function stats = img_ExtractROIStats(obj, roi, rcodes, selection, frames, weight, criterium)``
%
%	Computes satistics for each of the specified ROI for each of the frames.
%   Uses specified method of selecting voxels within ROI.
%
%   INPUTS
%   ======
%
%	--obj         current image
%   --roi         roi image file
%   --rcodes      roi values to use [all but 0]
%   --selection   selection method name [all]
%
%	              - 'all'        ... compute stats across all ROI voxels
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

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
%   2015-12-09 Grega Repovs
%              Adapted from existing img_ExtractROI method.
%
%   ToDo
%   — computation of weighted mean SE
%   — extraction of peak value
%   — extraction of ROI coordinates (min, max, peak, geometric mean)
%

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

nrois = length(rcodes);
nfrms = size(target, 2);

for r = 1:nrois

    stats(r).roiname = roi.roi.roinames{ismember(roi.roi.roicodes, rcodes(r))};
    stats(r).roicode = rcodes(r);

    msk = roi.img_ROIMask(rcodes(r));
    tmp = target(msk, :);
    twg = weight(msk, :);
    div = [];

    switch selection

        case 'threshold'
            msk = twg >= criterium;
            tmp = tmp(msk, :);

        case 'maxn'
            twgr = sort(twg, 'descend');
            twgt = twgr(criterium);
            msk  = twg >= twgt;
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

