function central_vertices = general_get_central_vertices(fin, fout, projection)

%``function central_vertices = general_get_central_vertices(fin, fout, params)``
%
%   Computes the vertex with the highest betweenness centrality in every
%   region (parcel) of the input image. This function does not work with
%   GNU Octave.
%
%   INPUTS
%   ======
%
%   --fin                input nimage object or path to the .nii file
%   --fout               output .txt filename (include the extension)
%                        [if empty, no output file is generated]
%   --projection         type of surface projection ['midthickness']
%
%   OUTPUTS
%   =======
%
%   --central_vertices   An array of structs with information about the
%                        most central region vertices. The output is
%                        structured as ::
%
%                        `central_vertices(<frame #>).(<surface structure>).{<region id>,:}`
%
%                        The first element corresponds to the region label
%                        (index), the second element is the index of the
%                        most central vertex in the surface structure
%                        coordinates, the third element is an array with
%                        XYZ coordinates of the most central vertex.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%
%       central_vertices = general_get_central_vertices('inputImage.dscalar.nii','outputFile.txt','very_inflated');
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 3 || isempty(projection), projection = 'midthickness'; end
if nargin < 2 || isempty(fout),       fout       = '';             end

is_octave = exist('OCTAVE_VERSION', 'builtin') ~= 0;

if ~is_octave
    
    load('cifti_brainmodel');
    
    params.cifti = cifti;
    params.components = components;
    params.projection = projection;
    params.weigh_by_distance = true;
    
    if ischar(fin)
        img = nimage(fin);
    else
        img = fin;
    end
    
    for fr=1:img.frames
        for cmp=1:2
            params.surfaceComponent = params.cifti.shortnames{cmp};
            params.cmp = cmp;
            
            indexedData = zeros(32492,1);
            D = img.data(img.cifti.start(params.cmp):img.cifti.end(params.cmp),fr);
            indexedData(params.cifti.(params.surfaceComponent).mask) = D;
            
            regions = unique(indexedData(indexedData ~= 0));
            n_regions = length(regions);
            
            central_vertices(fr).(params.cifti.shortnames{cmp}) = cell(n_regions,3);
            
            for r=1:n_regions
                [central_idx, central_xyz] = get_most_central_vertex(params, indexedData, regions(r));
                central_vertices(fr).(params.surfaceComponent){r,1} = regions(r);
                central_vertices(fr).(params.surfaceComponent){r,2} = central_idx;
                central_vertices(fr).(params.surfaceComponent){r,3} = central_xyz;
            end
        end
    end
    
    if ~isempty(fout)
        repf = fopen(fout, 'w');
        
        fprintf(repf, '#source: %s', img.filenamepath);
        fprintf(repf, '\n#projection: %s', params.projection);
        
        for fr=1:img.frames
            if img.frames > 1
                fprintf(repf, '\n\nFrame #%d:\n', fr);
            else
                fprintf(repf, '\n');
            end
            
            fprintf(repf, '\nRegion\tCentral_index\tCentral_x\tCentral_y\tCentral_z');
            
            for cmp=1:2
                n_regions = size(central_vertices(fr).(params.cifti.shortnames{cmp}),1);
                for r=1:n_regions
                    fprintf(repf, '\n%d\t%0.3f\t%0.3f\t%0.3f\t%0.3f',...
                        central_vertices(fr).(params.cifti.shortnames{cmp}){r,1},...
                        central_vertices(fr).(params.cifti.shortnames{cmp}){r,2},...
                        central_vertices(fr).(params.cifti.shortnames{cmp}){r,3}(1),...
                        central_vertices(fr).(params.cifti.shortnames{cmp}){r,3}(2),...
                        central_vertices(fr).(params.cifti.shortnames{cmp}){r,3}(3));
                end
            end
        end
        
        fclose(repf);
    end
    
else
    fprintf('\n---> ERROR: Function general_get_central_vertices is currently not supported when running Qu|Nex with Octave - EXITING! \n');
end

end

function [central_idx, central_xyz] = get_most_central_vertex(params, indexedData, label)
s = find(indexedData == label);
n = numel(s);
AdjacencyMatrix = zeros(n,n);
xyz = zeros(n,3);

for i=1:1:n
    nodeId = s(i);
    if indexedData(nodeId) == label
        VneighbourCount = params.cifti.(params.surfaceComponent).adj_list.n_count(nodeId);
        VadjNodes = params.cifti.(params.surfaceComponent).adj_list.neighbours{nodeId};
        xyz(i,:) = params.cifti.(params.surfaceComponent).(params.projection).vertices(nodeId,:);
        for j=1:1:VneighbourCount
            neighbour = VadjNodes(j);
            if (indexedData(neighbour) == label)
                AdjacencyMatrix(i,find(s == neighbour)) = 1;
                AdjacencyMatrix(find(s == neighbour),i) = 1;
            end
        end
    end
end

if params.weigh_by_distance
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
central_xyz = xyz(central_idx,:);


end