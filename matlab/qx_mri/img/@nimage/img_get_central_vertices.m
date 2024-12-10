function central_vertices = general_get_central_vertices(fin, fout, params)

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 3 || isempty(params), params = []; end
if nargin < 2 || isempty(fout),   fout   = ''; end

if isempty(params)
    load('cifti_brainmodel');
    params.cifti = cifti;
    params.components = components;
    params.projection = 'midthickness';
    params.weigh_by_distance = true;
end

if ischar(fin)
    img = nimage(fin);
else
    img = fin;
end

for fr=1:img.frames
    for cmp=1:2
        params.surfaceComponent = cifti.shortnames{cmp};
        params.cmp = cmp;
        
        indexedData = zeros(32492,1);
        D = img.data(img.cifti.start(params.cmp):img.cifti.end(params.cmp),fr);
        indexedData(params.cifti.(params.surfaceComponent).mask) = D;
        
        regions = unique(indexedData);
        n_regions = length(regions);
        
        central_vertices(fr).(cifti.shortnames{cmp}) = cell(n_regions,3);
        
        for r=1:n_regions
            [central_idx, central_xyz] = get_most_central_vertex(params, indexedData, regions(r));
            central_vertices(fr).(params.surfaceComponent){r,1} = regions(r);
            central_vertices(fr).(params.surfaceComponent){r,1} = central_idx;
            central_vertices(fr).(params.surfaceComponent){r,2} = central_xyz;
        end
    end
end

if ~ismepty(fout)
    repf = fopen(fout, 'w');
    
    fprintf(repf, '#source: %s', obj.filenamepath);
    
    for fr=1:img.frames
        if img.frames > 1
            fprintf(repf, '\n\nFrame #%d:\n', j);
        else
            fprintf(repf, '\n');
        end
        
        fprintf(repf, '\nRegion\tCentral_index\tCentral_x\tCentral_y\tCentral_z');
        
        for cmp=1:2
            n_regions = size(central_vertices(fr).(cifti.shortnames{cmp}),1);
            for r=1:n_regions
                fprintf('\n%d\t%0.3\t%0.3f\t%0.3f\t%0.3f');
            end
        end
    end
    
    fclose(repf)
end

end

function [central_idx, central_xyz] = get_most_central_vertex(fp_param, indexedData, label)
s = find(indexedData == label);
n = numel(s);
AdjacencyMatrix = zeros(n,n);
xyz = zeros(n,3);

for i=1:1:n
    nodeId = s(i);
    if indexedData(nodeId) == label
        VneighbourCount = fp_param.cifti.(fp_param.surfaceComponent).adj_list.n_count(nodeId);
        VadjNodes = fp_param.cifti.(fp_param.surfaceComponent).adj_list.neighbours{nodeId};
        xyz(i,:) = fp_param.cifti.(fp_param.surfaceComponent).(fp_param.projection).vertices(nodeId,:);
        for j=1:1:VneighbourCount
            neighbour = VadjNodes(j);
            if (indexedData(neighbour) == label)
                AdjacencyMatrix(i,find(s == neighbour)) = 1;
                AdjacencyMatrix(find(s == neighbour),i) = 1;
            end
        end
    end
end

if param.weigh_by_distance
    for i=1:1:n
        for j=1:1:n
            if AdjacencyMatrix(i,j)
                AdjacencyMatrix(i,j) = sqrt(sum((xyz(i,:)-xyz(j,:)).^2));
            end
        end
    end
end

G = graph(AdjacencyMatrix);

C = centrality(G,'betweenness');

[~, central_idx] = max(C);
central_xyz = xyz(central_idx);

end