function pimg = img_create_parcellated_metadata(obj, roi, rcodes)

%``function md = img_create_parcellated_metadata(obj, roi, rcodes)``
%
%  Create metadata for parcellated image from the provided regions of
%  interest (ROI) image.
%
%   INPUTS
%   ======
%
%   --obj         current image
%   --roi         roi image file
%   --rcodes      roi values to use [all but 0] 
%
%   OUTPUT
%   ======
%
%   pimg - empty parcellated image (pscalar or ptseries)
%   

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 3; rcodes = []; end
    
model = load('cifti_brainmodel');

pimg = obj.zeroframes(obj.frames);
pimg.TR = obj.TR;

if isempty(rcodes)
    roi_idx = 1:length(roi.roi);
else
    % --- Check whether we have ROI names or ROI codes
    if iscell(rcodes) && all(cellfun(@ischar, rcodes))
        [~, roi_idx] = ismember(rcodes, {roi.roi.roiname});
    elseif isnumeric(rcodes)
        [~, roi_idx] = ismember(rcodes, [roi.roi.roicode]);
    else
        error('ERROR (img_extract_roi) invalid specification of roi to extract!');
    end
end

nrois = length(roi_idx);

pimg.data = zeros(nrois, obj.frames);
pimg.dim = nrois;
pimg.voxels = nrois;

if any(strcmpi(obj.filetype, {'dscalar', 'pscalar'}))
    pimg.filetype = 'pscalar';
else
    pimg.filetype = 'ptseries';
end

pimg.cifti.longnames  = {};
pimg.cifti.shortnames = {};
pimg.cifti.start      = [];
pimg.cifti.end        = [];
pimg.cifti.length     = [];
pimg.cifti.maps       = {};
pimg.cifti.parcels    = {};

% ---> the source is already parcellated
%
% The rest of this function builds a parcellation out of a dense image, by
% mapping each ROI's grayordinates back onto surface vertices and volume
% voxels. There is nothing to work out when the source is parcellated
% already: an ROI over its rows covers whole parcels of its own
% parcellation, so the parcels of the result are those parcels, merged per
% ROI. Reading `models` off a parcels dimension, which is what the dense
% path does below, fails outright.

if strcmp(obj.cifti.metadata.diminfo{1}.type, 'parcels')
    pimg = merge_source_parcels(obj, pimg, roi, roi_idx, nrois);
    return
end

global_data = zeros(size(roi.data,1),1);
for p = 1:length(roi_idx)
    pimg.cifti.parcels{p} = roi.roi(roi_idx(p)).roiname;
    global_data(roi.roi(roi_idx(p)).indeces) = roi.roi(roi_idx(p)).roicode;
end

roi.data = global_data;
tmp_frames = roi.frames;
roi.frames = 1;
vol_sections = roi.img_extract_cifti_volume();
roi.frames = tmp_frames;
vol_4D_data = vol_sections.image4D;

n_structures = length(roi.cifti.shortnames);
parcels = struct([]);
for p = 1:nrois
    parcels(p).name = roi.roi(roi_idx(p)).roiname;
    key = roi.roi(roi_idx(p)).roicode;
    parcels(p).surfs = struct([]);
    parcels(p).voxlist = [];

    ctn_surf = 0;
    ctn_vol = 0;
    for s = 1:n_structures
        s_name = roi.cifti.shortnames{s};
        structure = model.cifti.(lower(s_name));

        if strcmpi(structure.type, 'surface')
            data = global_data(roi.cifti.start{s}:roi.cifti.end{s},:);
            component_data = zeros(32492, size(data,2));
            component_data(structure.mask,:) = data;
            vertlist = (find(component_data == key)-1)';
            if numel(vertlist) > 0
                ctn_surf = ctn_surf + 1;
                parcels(p).surfs(ctn_surf).vertlist = vertlist;
                parcels(p).surfs(ctn_surf).struct = s_name;
            end
        else
            ctn_vol = ctn_vol + 1;
            [i, j, k] = ind2sub(size(vol_4D_data),find(vol_4D_data == key));
            i = i - 1;
            j = j - 1;
            k = k - 1;
            parcels(p).voxlist = [i'; j'; k'];
        end
    end
end

nmodels = length(obj.cifti.metadata.diminfo{1}.models);
surflist = [];
for n = 1:nmodels
    if strcmp(obj.cifti.metadata.diminfo{1}.models{n}.type, 'surf')
        surflist = [surflist,...
                    struct('struct', obj.cifti.metadata.diminfo{1}.models{n}.struct,...
                           'numvert', obj.cifti.metadata.diminfo{1}.models{n}.numvert)];
    end
end

vol = obj.cifti.metadata.diminfo{1}.vol;

pimg.cifti.metadata.diminfo{1} = struct('type', 'parcels',...
                                        'vol', vol,...
                                        'surflist', surflist,...
                                        'parcels', parcels,...
                                        'length', nrois);

pimg.cifti.metadata.diminfo{2}.length = obj.frames;
pimg.cifti.maps = obj.cifti.maps;


% --------------------------------------------------------------------------------------------
%                                                                         merge_source_parcels

function [pimg] = merge_source_parcels(obj, pimg, roi, roi_idx, nrois)

    % One output parcel per ROI, built from the source parcels it covers.
    % An ROI is usually a single parcel, but need not be: a parcellated
    % label file that labels parcels by network gives one ROI per network,
    % and its parcel is then the union of every parcel in that network.

    source  = obj.cifti.metadata.diminfo{1};
    parcels = struct([]);

    for p = 1:nrois
        region = roi.roi(roi_idx(p));

        parcels(p).name    = region.roiname;
        parcels(p).surfs   = struct([]);
        parcels(p).voxlist = [];

        surf_names = {};
        for sp = region.indeces(:)'
            covered = source.parcels(sp);
            for s = 1:length(covered.surfs)
                at = find(strcmp(surf_names, covered.surfs(s).struct), 1);
                if isempty(at)
                    surf_names{end+1} = covered.surfs(s).struct;
                    at = length(surf_names);
                    parcels(p).surfs(at).struct   = covered.surfs(s).struct;
                    parcels(p).surfs(at).vertlist = covered.surfs(s).vertlist(:)';
                else
                    parcels(p).surfs(at).vertlist = [parcels(p).surfs(at).vertlist covered.surfs(s).vertlist(:)'];
                end
            end
            parcels(p).voxlist = [parcels(p).voxlist covered.voxlist];
        end

        for s = 1:length(parcels(p).surfs)
            parcels(p).surfs(s).vertlist = unique(parcels(p).surfs(s).vertlist);
        end
        if ~isempty(parcels(p).voxlist)
            parcels(p).voxlist = unique(parcels(p).voxlist', 'rows')';
        end
    end

    % everything but the parcels themselves - the volume space, the surface
    % list - carries over from the source unchanged
    diminfo         = source;
    diminfo.parcels = parcels;
    diminfo.length  = nrois;

    pimg.cifti.parcels             = {parcels.name};
    pimg.cifti.metadata.diminfo{1} = diminfo;
    pimg.cifti.metadata.diminfo{2}.length = obj.frames;
    pimg.cifti.maps                = obj.cifti.maps;
