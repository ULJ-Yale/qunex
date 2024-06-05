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

nrois = length(rcodes);

pimg.data = zeros(nrois, obj.frames);
pimg.dim = nrois;
pimg.voxels = nrois;

if strcmpi(obj.filetype, 'dscalar')
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
