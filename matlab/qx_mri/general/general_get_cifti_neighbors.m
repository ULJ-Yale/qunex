function [neighbors, meta] = general_get_cifti_neighbors(varargin)
% general_get_cifti_neighbors
%   Loads precomputed grayordinate-level neighbors for dense CIFTI or
%   computes them if missing, returning a cell array where neighbors{i}
%   lists the grayordinate indices adjacent to i.
%
%   Usage:
%       neighbors = general_get_cifti_neighbors();
%       neighbors = general_get_cifti_neighbors('File','cifti_neighbors_all.mat');
%       [neighbors, meta] = general_get_cifti_neighbors('ComputeIfMissing',true);
%
%   Name-Value parameters:
%       'File'             - MAT file to load/save (default: 'cifti_neighbors_all.mat')
%       'ComputeIfMissing' - If true, compute neighbors when file is missing (default: true)
%       'SaveComputed'     - If true, save computed neighbors to 'File' (default: true)
%       'Verbose'          - If true, print progress (default: true)
%
%   Returns:
%       neighbors  - cell array (typically 91282x1 for 32k LR dense)
%       meta       - struct with optional fields if loaded/saved from MAT
%
%   Requirements to compute:
%       - 'cifti_brainmodel.mat' must be on the MATLAB path. This file is
%         created by general_create_cifti_mat.m and must provide variables
%         'cifti' (with cortex adjacency and volume indices) and
%         'components' (with .volumeMask).
%
% SPDX-FileCopyrightText: 2025 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

    % Defaults
    params.File = 'cifti_neighbors_all.mat';
    params.ComputeIfMissing = true;
    params.SaveComputed = true;
    params.Verbose = true;

    % Parse name-value args
    if mod(numel(varargin),2) ~= 0
        error('general_get_cifti_neighbors: Name-value pairs expected.');
    end
    for k = 1:2:numel(varargin)
        key = varargin{k}; val = varargin{k+1};
        switch lower(key)
            case 'file', params.File = val;
            case 'computeifmissing', params.computeifmissing = logical(val); params.ComputeIfMissing = params.computeifmissing; %#ok<NASGU>
            case 'savecomputed', params.SaveComputed = logical(val);
            case 'verbose', params.Verbose = logical(val);
            otherwise
                error('general_get_cifti_neighbors: unknown parameter "%s".', key);
        end
    end

    neighbors = [];
    meta = struct();

    % Try loading existing neighbors
    if exist(params.File, 'file') == 2
        try
            S = load(params.File, 'neighbors', 'meta');
            if isfield(S, 'neighbors') && iscell(S.neighbors)
                neighbors = S.neighbors; %#ok<NASGU>
                if isfield(S, 'meta'), meta = S.meta; end
                if params.Verbose
                    fprintf('[general_get_cifti_neighbors] Loaded neighbors from %s\n', params.File);
                end
                neighbors = S.neighbors;
                return;
            end
        catch ME
            if params.Verbose
                fprintf('[general_get_cifti_neighbors] Failed loading %s (%s). Will try to compute.\n', params.File, ME.message);
            end
        end
    end

    if ~params.ComputeIfMissing
        error('general_get_cifti_neighbors: file "%s" not found and ComputeIfMissing=false.', params.File);
    end

    % Compute neighbors either by invoking precompute (preferred, saves) or inline
    computed = false;
    if params.SaveComputed
        % Use the precompute utility which saves a MAT file for reuse
        try
            if params.Verbose
                fprintf('[general_get_cifti_neighbors] Computing neighbors and saving to %s ...\n', params.File);
            end
            precompute_cifti_neighbors(params.File);
            computed = true;
        catch ME
            if params.Verbose
                fprintf('[general_get_cifti_neighbors] precompute_cifti_neighbors failed: %s\nFalling back to in-memory computation.\n', ME.message);
            end
        end
    end

    if computed && exist(params.File,'file')==2
        S = load(params.File, 'neighbors', 'meta');
        neighbors = S.neighbors;
        if isfield(S,'meta'), meta = S.meta; end
        return;
    end

    % Inline compute without saving
    if params.Verbose
        fprintf('[general_get_cifti_neighbors] Computing neighbors in memory (no save) ...\n');
    end
    [neighbors, meta] = local_build_neighbors_from_brainmodel(params);

    % Optionally save
    if params.SaveComputed
        % Save in MATLAB v7 format for cross-compatibility
        try
            if params.Verbose
                fprintf('[general_get_cifti_neighbors] Saving computed neighbors to %s ...\n', params.File);
            end
            save(params.File, 'neighbors', 'meta', '-v7');
        catch ME
            % Last resort: default save
            try
                save(params.File, 'neighbors', 'meta');
            catch
                if params.Verbose
                    fprintf('[general_get_cifti_neighbors] Failed to save neighbors after fallback: %s\n', ME.message);
                end
            end
        end
    end
end

function [neighbors, meta] = local_build_neighbors_from_brainmodel(params)
    % Load cifti brain model
    try
        S = load('cifti_brainmodel');
    catch
        error(['general_get_cifti_neighbors: missing cifti_brainmodel.mat on path. ', ...
               'Generate it with general_create_cifti_mat.m']);
    end
    if ~isfield(S,'cifti') || ~isfield(S,'components')
        error('general_get_cifti_neighbors: cifti_brainmodel.mat must contain variables "cifti" and "components".');
    end
    cifti = S.cifti; components = S.components;

    % Infer total grayordinates (default to 91282 for 32k LR dense)
    totalGray = 0;
    if isfield(cifti,'start') && isfield(cifti,'end')
        totalGray = max(cifti.end);
    end
    if isempty(totalGray) || totalGray <= 0
        totalGray = 91282;
    end
    neighbors = cell(totalGray,1);

    % Find cortex components
    idxL = find(strcmp(cifti.shortnames, 'cortex_left'), 1);
    idxR = find(strcmp(cifti.shortnames, 'cortex_right'), 1);

    % Cortex left
    if ~isempty(idxL) && isfield(cifti,'cortex_left') && isfield(cifti.cortex_left,'adj_list')
        if params.Verbose, fprintf('  - building cortex_left neighbors ...\n'); end
        left_gidx = cifti.start(idxL):cifti.end(idxL);
        left_mask_pos = find(cifti.cortex_left.mask);
        inv_left = zeros(max(left_mask_pos),1);
        inv_left(left_mask_pos) = 1:numel(left_mask_pos);
        for ii = 1:numel(left_gidx)
            vtx = left_mask_pos(ii);
            neigh_vtx = cifti.cortex_left.adj_list.neighbours{vtx};
            neigh_vtx = neigh_vtx(neigh_vtx > 0 & neigh_vtx <= numel(inv_left));
            pos = inv_left(neigh_vtx);
            pos = pos(pos>0 & pos<=numel(left_gidx));
            neighbors{left_gidx(ii)} = left_gidx(pos(:)');
        end
    end

    % Cortex right
    if ~isempty(idxR) && isfield(cifti,'cortex_right') && isfield(cifti.cortex_right,'adj_list')
        if params.Verbose, fprintf('  - building cortex_right neighbors ...\n'); end
        right_gidx = cifti.start(idxR):cifti.end(idxR);
        right_mask_pos = find(cifti.cortex_right.mask);
        inv_right = zeros(max(right_mask_pos),1);
        inv_right(right_mask_pos) = 1:numel(right_mask_pos);
        for ii = 1:numel(right_gidx)
            vtx = right_mask_pos(ii);
            neigh_vtx = cifti.cortex_right.adj_list.neighbours{vtx};
            neigh_vtx = neigh_vtx(neigh_vtx > 0 & neigh_vtx <= numel(inv_right));
            pos = inv_right(neigh_vtx);
            pos = pos(pos>0 & pos<=numel(right_gidx));
            neighbors{right_gidx(ii)} = right_gidx(pos(:)');
        end
    end

    % Volume/subcortex 26-connectivity
    if params.Verbose, fprintf('  - building subcortex/volume neighbors (26-conn) ...\n'); end
    if ~isfield(components,'volumeMask')
        warning('general_get_cifti_neighbors: components.volumeMask missing, skipping volume adjacency.');
        meta = struct('version','1.0', 'date', datestr(now,'yyyy-mm-dd HH:MM:SS'), ...
                      'notes','Cortex adjacency only; volume mask missing');
        return;
    end

    volSize = size(components.volumeMask);
    volGray = zeros(volSize, 'uint32');

    % Map volume coordinates to grayordinates
    for i = 1:numel(cifti.shortnames)
        name = cifti.shortnames{i};
        if ~isfield(cifti, name), continue; end
        if ~isfield(cifti.(name), 'type'), continue; end
        if ~strcmp(cifti.(name).type, 'Volume'), continue; end
        A = cifti.(name).indices; % [N x 3], 0-based indices
        if isempty(A), continue; end
        start_idx = cifti.start(i);
        for j = 1:size(A,1)
            x = A(j,1)+1; y = A(j,2)+1; z = A(j,3)+1;
            volGray(x,y,z) = uint32(start_idx + (j-1));
        end
    end

    % 26-neighborhood offsets
    offs = int32([]);
    idx = 0;
    for dx=-1:1
        for dy=-1:1
            for dz=-1:1
                if dx==0 && dy==0 && dz==0, continue; end
                idx = idx + 1; offs(idx,:) = [dx dy dz]; %#ok<AGROW>
            end
        end
    end

    [X,Y,Z] = ind2sub(volSize, find(volGray>0));
    for ii = 1:numel(X)
        x = X(ii); y = Y(ii); z = Z(ii);
        go = volGray(x,y,z);
        ng = [];
        for o = 1:size(offs,1)
            xx = x + offs(o,1); yy = y + offs(o,2); zz = z + offs(o,3);
            if xx<1 || yy<1 || zz<1 || xx>volSize(1) || yy>volSize(2) || zz>volSize(3)
                continue;
            end
            go2 = volGray(xx,yy,zz);
            if go2>0, ng(end+1) = double(go2); end %#ok<AGROW>
        end
        if ~isempty(ng)
            neighbors{double(go)} = unique(ng);
        end
    end

    meta = struct('version','1.0', 'date', datestr(now,'yyyy-mm-dd HH:MM:SS'), ...
                  'notes','CIFTI cortex one-ring and subcortical 26-connectivity (in-memory)');
end
