function [roi peak] = img_find_peaks_surface(img, surfaceComponent, projection, minarea, maxarea, val, t, options, verbose)

%``img_find_peaks_surface(img, surfaceComponent, projection, minarea, maxarea, val, t, options, verbose)``
%
%   Find peaks and uses watershed algorithm to grow regions from them on the
%   brain model components constructed with surface elements (ex. left and right
%   cortex).
%
%   INPUTS
%   ======
%
%   --img                input nimage object
%   --surfaceComponent   brain component of type surface to perform ROI 
%                        operation on ('cortex_left', 'cortex_right') 
%                        ['cortex_left']
%   --projection         type of surface component projection ('midthickness', 
%                        'inflated', ...) or a path to the surface file 
%                        (.surf.gii) of the left or right cortex:
%
%                        a. for a default projection: 'midthickness' ['midthickness']
%                        b. for a specific projection: 'CL_projection.surf.gii'
%
%   --minarea            minimal size of the resulting ROI [0]
%   --maxarea            maximum size of the resulting ROI [inf]
%   --val                whether to find positive, negative or both peaks 
%                        ('n', 'p', 'b') ['b']
%   --t                  threshold value [0]
%   --options            list of options separated with a pipe symbol ("|"):
%
%                        - for the number of frames to be analized:
%
%                           []
%                               analyze only the first frame
%                           'frames:[LIST OF FRAMES]'
%                               analyze the list of frames
%                           'frames:all'
%                               analyze all the frames
%
%                        - for the type of ROI boundary:
%
%                           []
%                               boundary left unmodified
%                           'boundary:remove'
%                               remove the boundary regions
%                           'boundary:highlight'
%                               highlight boundaries with a value of -100
%                           'boundary:wire'
%                               remove ROI data and return only ROI boundaries
%
%    --verbose           whether to report the peaks (1) and also be verbose (2) 
%                        [false]
%
%   OUTPUTS
%   =======
%
%   roi
%       A nimage with the created ROI.
%   peak
%       A datastructure with information about the extracted peaks.
%
%   USE
%   ===
%
%   The method is used to identify positive and/or negative peaks in the image,
%   and then generate ROI around them using a watershed algorithm. Specifically,
%   the method first zeros all the values below the specified threshold (t), it
%   then finds all the peaks, voxels that have the value higher than the
%   immediate neighbors. It then uses a wathershed algorithm to flood the peaks,
%   so that all the peaks that result in regions smaller than the specified
%   minsize get either removed or flooded in from the adjoining heigher peak (if
%   if one exists). If final peaks are too large, they get reflooded to the
%   specified maxsize only.
%
%   This method is used specifically for the surface type brain models, such as
%   the cortex in CIFTI-2 image format. It performs the operations on a
%   triangular surface mesh.
%
%   EXAMPLE USE 1
%   =============
%
%   To get a roi image (dscalar) of both positive and negative peak regions with
%   miminum z value of (-)3 and surface peak regions of areas between 50 mm^2
%   and 250 mm^2 on a cortex_left with midthickness projection use::
%
%       roi = img.img_find_peaks_surface('cortex_left', 'midthickness', 50, ...
%               250, 'b', 3);
%
%   EXAMPLE USE 2
%   =============
%
%   To perform an operation on a time series (dtseries) image with similar
%   parameters as in the first example on frames 1, 3, 7 with fp_param.verbose
%   output use::
%
%       roi = img.img_find_peaks_surface('cortex_left', 'midthickness', 50, ...
%           250, 'b', 3, 'frames:[1 3 7]', 2);
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

%% - I - import section
if nargin < 9 || isempty(verbose), fp_param.verbose = false;       end
if nargin < 8 || isempty(options), options = '';          end
if nargin < 7 || isempty(t),       t       = 0;           end
if nargin < 6 || isempty(val),     val     = 'b';         end
if nargin < 5 || isempty(maxarea), maxarea = inf;         end
if nargin < 4 || isempty(minarea), minarea = 1;           end
if nargin < 3 || isempty(projection), projection = 'midthickness';            end
if nargin < 2 || isempty(surfaceComponent), surfaceComponent = 'cortex_left'; end

% --- Find Peaks Parameters
fp_param.surfaceComponent = surfaceComponent;
fp_param.projection = projection;
fp_param.val = val;
fp_param.threshold = t;
fp_param.minarea = minarea;
fp_param.maxarea = maxarea;

% --- Script verbosity
verbose_pass = verbose;
report = false;
if verbose == 1
    verbose = false;
    report  = true;
elseif verbose == 2
    verbose = true;
    report  = true;
end
fp_param.verbose = verbose;
fp_param.report = report;

% --- parse options argument
options_parsed = general_parse_options([],options);
if ~isfield(options_parsed,'frames')
    options_parsed.frames = 1;
end
if ~isfield(options_parsed,'boundary')
    options_parsed.boundary = '';
end
frames = options_parsed.frames;
boundary = options_parsed.boundary;
fp_param.frames = frames;
fp_param.boundary = boundary;

% --- If multiple frame image, perform FindPeaks recursevely for each frame
if img.frames > 1
    if fp_param.fp_param.verbose, fprintf('\n---> more than 1 frame detected'); end
    % if more than 1 frame, perform img_find_peaks() on each frame recursivelly
    img_temp = img; img_temp.frames = 1;
    roi = img;
    peak = cell(1,img.frames);
    for fr = fp_param.frames
        if fp_param.fp_param.verbose, fprintf('\n---> performing ROI on frame %d', fr); end
        img_temp.data = img.data(:,fr);
        [img_temp, p_temp] = ...
            img_temp.img_find_peaks_surface(surfaceComponent, projection, minarea, maxarea, val, t, 1, fp_param.verbose_pass);
        roi.data(:,fr)=img_temp.image2D();
        peak{fr} = p_temp;
    end
    return;
end

% --- Load CIFTI brain model data
cifti = [];
load('cifti_brainmodel');
fp_param.cifti = cifti;

% -- Check the type of projection passed and weather it is a file
fp_param = determineSurfaceProjection(fp_param);

% --- Create an empty matrix to store the data globally for each hemisphere
roiDataRaw = zeros(32492,1);
%fp_param.surfaceComponent = lower(img.cifti.shortnames{fp_param.cmp});
roiDataRaw(fp_param.cifti.(fp_param.surfaceComponent).mask) = img.data(img.cifti.start{fp_param.cmp}:img.cifti.end{fp_param.cmp});

% --- Flip to focus on the relevant value(s)
roiData = thresholdData(roiDataRaw, fp_param);

% --- Preallocate peak structure
peak = [];

% --- preallocate the global vector to store region ID at indices corresponding to the data
indexedData = zeros(size(roiData));

% --- store begining and end of the vertices
fp_param.start = img.cifti.start{fp_param.cmp};
fp_param.end = img.cifti.end{fp_param.cmp};

%% - II - flooding - initial flooding
[peak, indexedData] = performInitialFlooding(roiData, roiDataRaw, peak, indexedData, fp_param);

%% - III - flooding - remove the smallest ROIs
[peak, indexedData] = removeTooSmallROIs(roiData, peak, indexedData, fp_param);

%% - IV - flooding - remove the biggest ROIs
[peak, indexedData] = removeTooLargeROIs(roiData, peak, indexedData, fp_param);

%% - V - export section

peak = removeEmptyPeaks(peak);

[peak, indexedData] = relableROIs(peak, indexedData);

peak = getRegionAverage(peak,roiDataRaw,indexedData);

% --- define borders between ROIs as desired by the user
boundary_map = zeros(size(indexedData));
for n=1:1:numel(indexedData)
    cs = indexedData(n);
    if cs > 0
        ni = indexedData(fp_param.cifti.(fp_param.surfaceComponent).adj_list.neighbours{n});
        boundary_map(fp_param.cifti.(fp_param.surfaceComponent).adj_list.neighbours{n}(ni~=cs)) = -1;
    end
end

% --- remap the data back from global to CIFTI data format for export
roi = img;
switch (fp_param.boundary)
    case 'remove'
        indexedData(boundary_map == -1) = 0;
        roiData = indexedData;
        % --- embed data to ROI image
        roi.data(img.cifti.start{fp_param.cmp}:img.cifti.end{fp_param.cmp}) = roiData(fp_param.cifti.(fp_param.surfaceComponent).mask);
    case 'highlight'
        indexedData(boundary_map == -1) = -100;
        roiData = indexedData;
        % --- embed data to ROI image
        roi.data(img.cifti.start{fp_param.cmp}:img.cifti.end{fp_param.cmp}) = roiData(fp_param.cifti.(fp_param.surfaceComponent).mask);
    case 'wire'
        roiData = boundary_map.*(-1);
        % --- embed data to ROI image
        roi.data(img.cifti.start{fp_param.cmp}:img.cifti.end{fp_param.cmp}) = roiData(fp_param.cifti.(fp_param.surfaceComponent).mask);
    otherwise
        roiData = indexedData;
        % --- embed data to ROI image
        roi.data(img.cifti.start{fp_param.cmp}:img.cifti.end{fp_param.cmp}) = roiData(cifti.(fp_param.surfaceComponent).mask);
end

% --- the end
if fp_param.verbose, fprintf('\n---> DONE\n'); end

if isempty(peak)
    if report, fprintf('\n---> No peaks to report on!\n'); end
else
    if report, fprintf('\n---> peak report - %s\n',(fp_param.surfaceComponent)); end
    for p = 1:length(peak)
        if report, fprintf('\nROI:%3d  index: %3d  value: %5.1f  size: %3d  area: %3d', p, peak(p).index, peak(p).value, peak(p).size, peak(p).area); end
    end
    if report, fprintf('\n'); end
end

end






%% VI - SUPPORT FUNCTIONS

function [area] = getRegionArea(i, indexedData, fp_param)

face_matrix = fp_param.cifti.(fp_param.surfaceComponent).faces;
area_vector = fp_param.cifti.(fp_param.surfaceComponent).(lower(fp_param.projection)).area_vector;

% --- modify faces matrix to find the corresponding faces
F = face_matrix;
% --- calculate vertex indices of the region
region_indices = find(indexedData == i);
% --- compute the logical array of the faces that contain existing vertices
F = ismember(F,region_indices);
% --- sum the rows of the logical faces matrix in order to see which face consists of all existing 3 vertices
F = sum(F,2);
% --- calculate the area of the region
area = (1/3) * sum(area_vector(F > 0));

end

function [projection_area_vector] = getProjectionArea(projection_vertices, fp_param)

ab = projection_vertices(fp_param.cifti.(fp_param.surface_component).faces(:,2),:) - ...
    projection_vertices(fp_param.cifti.(fp_param.surface_component).faces(:,1),:);
ac = projection_vertices(fp_param.cifti.(fp_param.surface_component).faces(:,3),:) - ...
    projection_vertices(fp_param.cifti.(fp_param.surface_component).faces(:,1),:);
projection_area_vector = 0.5.*sqrt(sum(cross(ab,ac).^2,2));

end

function [fp_param] = determineSurfaceProjection(fp_param)
if ~sum(strcmp(fp_param.projection,{'midthickness','inflated','very_inflated','sphere'}))
    subject_projection = gifti(fp_param.projection);
    fp_param.projection = 'subject';
    fp_param.cifti.(lower(surfaceComponent)).subject.vertices = subject_projection.vertices;
    fp_param.cifti.(lower(surfaceComponent)).subject.area_vector = getProjectionArea(subject_projection.vertices, fp_param);
end

if strcmp(fp_param.surfaceComponent, 'cortex_left')
    fp_param.cmp = 1;
elseif strcmp(fp_param.surfaceComponent, 'cortex_right')
    fp_param.cmp = 2;
else
    error('Wrong component inserted!');
end
end

function [roiData] = thresholdData(roiData, fp_param)
if strcmp(fp_param.val, 'b')
    roiData = abs(roiData);
elseif strcmp(fp_param.val, 'p')
    roiData(roiData < 0) = 0;
elseif strcmp(fp_param.val, 'n')
    roiData(roiData > 0) = 0;
    roiData = roiData * -1;
else
    error('No value specified!');
end

roiData(roiData < fp_param.threshold) = 0;
end

function [peak] = removeEmptyPeaks(peak)
% remove empty peaks
if ~isempty(peak)
    peak = peak([peak.area]>0);
end
end

function [peak, indexedData] = relableROIs(peak, indexedData)
% relable the ROI labels, starting from 1 up to the last ROI
for i=1:1:length(peak)
    v = indexedData(peak(i).index);
    if v==0
        error('Labeling messed up!');
    end
    indexedData(indexedData == v) = i;
    peak(i).index = i;
end
end

function [peak, indexedData] = performInitialFlooding(roiData, roiDataRaw, peak, indexedData, fp_param)
% --- Find all the relevant maxima
if fp_param.verbose, fprintf('\n---> identifying intial set of peaks'); end

% --- Find peaks in the regions
p = 0;
ctn_peaks = 0;
for i=1:1:numel(fp_param.cifti.(fp_param.surfaceComponent).adj_list.neighbours)
    if (roiData(i)) > 0 &&...
            (roiData(i) >= max(roiData(fp_param.cifti.(fp_param.surfaceComponent).adj_list.neighbours{i})))
        ctn_peaks = ctn_peaks + 1;
        peak(ctn_peaks).index = i;
        peak(ctn_peaks).grayord = i;
        peak(ctn_peaks).value = roiDataRaw(i);
        peak(ctn_peaks).x = fp_param.cifti.(fp_param.surfaceComponent).(fp_param.projection).vertices(i,1);
        peak(ctn_peaks).y = fp_param.cifti.(fp_param.surfaceComponent).(fp_param.projection).vertices(i,2);
        peak(ctn_peaks).z = fp_param.cifti.(fp_param.surfaceComponent).(fp_param.projection).vertices(i,3);
    end
end

% --- Prepare the data to store the non-zero data to vval and corresponding sorted indices to s
[vind, ~, vval] = find(roiData);
[~, s] = sort(vval, 1, 'descend');

% --- First flooding
if fp_param.verbose, fprintf('\n---> flooding %d peaks', length(peak)); end

% assign IDs to the peaks in the indexedData variable
for n = 1:length(peak)
    indexedData(peak(n).index) = n;
    peak(n).size  = 1;
    peak(n).area  = 0; 
end

% flood the data starting from the highest value.
for n = 1:numel(vval)
    % if not a peak check around which peak the vertex or ROI lies next to
    if ~any(indexedData(vind(s(n))) == 1:length(peak))
        % assign vertex neighbour indexedData ids to id
        [~, ~, id] = find(indexedData(fp_param.cifti.(fp_param.surfaceComponent).adj_list.neighbours{vind(s(n))}));
        % remove duplicate ids
        u_id = unique(id);
        if isscalar(u_id)
            % if only one neighbour belongs to a ROI assign it to that one
            indexedData(vind(s(n))) = u_id;
            peak(u_id).size = peak(u_id).size + 1;
            
            % update peak info to the higher peak
            if abs(peak(u_id).value) < abs(vval(s(n)))
                peak(u_id).grayord = vind(s(n));
                peak(u_id).value   = vval(s(n));
                peak(u_id).x       = fp_param.cifti.(fp_param.surfaceComponent).(fp_param.projection).vertices(vind(s(n)),1);
                peak(u_id).y       = fp_param.cifti.(fp_param.surfaceComponent).(fp_param.projection).vertices(vind(s(n)),2);
                peak(u_id).z       = fp_param.cifti.(fp_param.surfaceComponent).(fp_param.projection).vertices(vind(s(n)),3);
            end
            
        elseif numel(u_id) > 1
            % if some neighbours belong to other ROIs, assign it to the largest ROI
            [~, ~, nROIs] = mode(id);
            nROIs = nROIs{1};
            if numel(nROIs) > 1
                % if the same number of neighbours belong to multiple ROIs assign it to the one with the higher peak
                indexedData(vind(s(n))) = nROIs(1);
                maxVal = roiData(peak(nROIs(1)).index);
                maxID = nROIs(1);
                for m=2:numel(nROIs)
                    if roiData(peak(nROIs(m)).index) >= maxVal
                        maxVal = roiData(peak(nROIs(m)).index);
                        maxID = nROIs(m);
                    end
                end
            else
                maxID = nROIs;
            end
            indexedData(vind(s(n))) = maxID;
            peak(maxID).size = peak(maxID).size + 1;
            
            % update peak info to the higher peak
            if abs(peak(maxID).value) < abs(roiData(vind(s(n))))
                peak(maxID).grayord = vind(s(n));
                peak(maxID).value   = roiData(vind(s(n)));
                peak(maxID).x       = fp_param.cifti.(fp_param.surfaceComponent).(fp_param.projection).vertices(vind(s(n)),1);
                peak(maxID).y       = fp_param.cifti.(fp_param.surfaceComponent).(fp_param.projection).vertices(vind(s(n)),2);
                peak(maxID).z       = fp_param.cifti.(fp_param.surfaceComponent).(fp_param.projection).vertices(vind(s(n)),3);
            end
            
        end
    end
end

% --- Calculate areas of regions
for i=1:1:length(peak)
    peak(i).area = getRegionArea(i, indexedData, fp_param);   
end
end

function [peak, indexedData] = removeTooSmallROIs(roiData, peak, indexedData, fp_param)
% --- Combine ROIs smaller then the min with the neighbouring ones
if ~isempty(peak)
    small = peak([peak.area] < fp_param.minarea);
else
    small = [];
end

% loop until the small array is not empty
while ~isempty(small)
    
    % size of the smallest region
    rsize = min([small.area]);
    % indices of the smallest region(s)
    rtgts = find([peak.area]==rsize);
    
    newId = [];
    
    if fp_param.verbose, fprintf('\n---> %d regions too small, refilling %d regions of size %d', length(small), length(rtgts), rsize); end
    
    % loop through the smallest regions and refill them up to first contact with another region and combine them
    for rtgt = rtgts(:)'
        [vind, ~, vval] = find(indexedData(:) == rtgt);
        [~, s]    = sort(vval, 1, 'descend');
        
        % flood the data
        done = false;
        for n = 1:numel(vval)
            % assign vertex neighbour indexedData ids to id
            [~, ~, id] = find(indexedData(fp_param.cifti.(fp_param.surfaceComponent).adj_list.neighbours{vind(n)}));
            id = id(id ~= rtgt);
            % remove duplicate ids
            u_id = unique(id);
            newId = u_id;
            if isscalar(u_id)
                % if only one neighbour belongs to another ROI assign it to that one
                if ~isempty(u_id)
                    peak(u_id).area = getRegionArea(u_id, indexedData, fp_param);
                    if (peak(u_id).area < fp_param.maxarea)
                        indexedData(indexedData == rtgt) = u_id;
                        peak(u_id).size = peak(rtgt).size + peak(u_id).size;
                        
                        % update peak info to the higher peak
                        if abs(peak(u_id).value) < abs(peak(rtgt).value)
                            peak(u_id).value   = peak(rtgt).value;
                            peak(u_id).grayord = peak(rtgt).grayord;
                            peak(u_id).x       = peak(rtgt).x;
                            peak(u_id).y       = peak(rtgt).y;
                            peak(u_id).z       = peak(rtgt).z;
                        end
                        
                        done = true;
                        break;
                    end
                end
            elseif numel(u_id) > 1
                % if some neighbours belong to other ROIs, assign it to the largest ROI
                [~, ~, nROIs] = mode(id);
                nROIs = nROIs{1};
                if numel(nROIs) > 1
                    % if the same number of neighbours belong to multiple ROIs assign it to the one with the higher peak
                    indexedData(vind(s(n))) = nROIs(1);
                    maxVal = roiData(peak(nROIs(1)).index);
                    maxId = nROIs(1);
                    for m=2:numel(nROIs)
                        if roiData(peak(nROIs(m)).index) >= maxVal
                            maxVal = roiData(peak(nROIs(m)).index);
                            maxId = nROIs(m);
                        end
                    end
                else
                    maxId = nROIs;
                end
                indexedData(indexedData == rtgt) = maxId;
                peak(maxId).size = peak(rtgt).size + peak(maxId).size;
                
                % update peak info to the higher peak
                if abs(peak(maxId).value) < abs(peak(rtgt).value)
                    peak(maxId).value  = peak(rtgt).value;
                    peak(maxId).grayord = peak(rtgt).grayord;
                    peak(maxId).x      = peak(rtgt).x;
                    peak(maxId).y      = peak(rtgt).y;
                    peak(maxId).z      = peak(rtgt).z;
                end
                
                done = true;
                newId = maxId;
                break;
            end
            
        end
        if ~done
            indexedData(indexedData == rtgt) = 0;
        end
        peak(rtgt).size = 0;
        peak(rtgt).area = 0;
        
    end
    % --- Calculate areas of regions
    if ~isempty(newId)
        peak(newId).area = getRegionArea(newId, indexedData, fp_param);
    end
    % remove the smallest region for the small array
    small = peak([peak.area] > rsize & [peak.area] < fp_param.minarea);
end
end

function [peak, indexedData] = removeTooLargeROIs(roiData, peak, indexedData, fp_param)
% --- Trim regions that are too large
if ~isempty(peak)
    big = find([peak.area] > fp_param.maxarea);
else
    big = [];
end

if ~isempty(big) && fp_param.verbose, fprintf('\n\n---> found %d ROI that are too large', length(big)); end

for b  = big(:)'
    % --- store the non-zero data to vval and corresponding sorted indices to s
    bigROI_data = roiData;
    bigROI_data(indexedData ~= b) = 0;
    
    indexedData(indexedData == b) = -1;
    
    [vind, ~, vval] = find(bigROI_data);
    [~, s_ind] = sort(vval, 1, 'descend');
    
    s = vind(s_ind);
    
    % --- if peak.index does not represent the highest value (peak) reassign the new index
    if roiData(peak(b).index) ~= vval(s_ind(1))
        peak(b).index = vind(s_ind(1));
    end
    
    if fp_param.verbose, fprintf('\n---> reflooding region %d', b); end
    
    peak(b).size = 1;
    peak(b).area = 0;
    indexedData(s(1)) = b;
    
    loop_ctn = 1;
    done = false;
    previousArea = peak(b).area;
    
    %% Body of the new algorithm
    while (peak(b).area < fp_param.maxarea && ~done)
        % flood the region from the peak "upwards"
        for n=1:numel(s)
            if (indexedData(s(n)) ~= b && indexedData(s(n)) ~= -2)
                indexedData(s(n)) = b;
                peak(b).size = peak(b).size + 1;
                peak(b).area = getRegionArea(b, indexedData, fp_param);
                AdjacencyMatrix = updateEdges(fp_param, indexedData, s, b, numel(s), false);
            end
            if (peak(b).area >= fp_param.maxarea)
                break;
            end
        end
        
        % relable isolated nodes that were flooded in the previous step
        flooded = find(indexedData == b);
        for i=1:1:numel(flooded)
            m = flooded(i);
            if (~pathExists(AdjacencyMatrix, s, peak(b).index,m))
                indexedData(m) = -2;
                peak(b).size = peak(b).size - 1;
                peak(b).area = getRegionArea(b, indexedData, fp_param);
                AdjacencyMatrix = updateEdges(fp_param, indexedData, s, b, numel(s), false);
            end
        end
        
        % flood the nodes that border the primary region around the peak or became connected after further flooding
        isolatedInd = find(indexedData == -2);
        isolatedVal = bigROI_data(isolatedInd);
        [~, sortingVector] = sort(isolatedVal, 1, 'descend');
        isolatedSorted = isolatedInd(sortingVector);
        for i=1:1:numel(isolatedSorted)
            m = isolatedSorted(i);
            if (pathExists(AdjacencyMatrix, s, peak(b).index,m) && peak(b).area < fp_param.maxarea)
                indexedData(m) = b;
                peak(b).size = peak(b).size + 1;
                peak(b).area = getRegionArea(b, indexedData, fp_param);
                AdjacencyMatrix = updateEdges(fp_param, indexedData, s, b, numel(s), false);
            end
        end
        
        % finally relable isolated regions that were flooded in the previous step
        flooded = find(indexedData == b);
        AdjacencyMatrix = updateEdges(fp_param, indexedData, s, b, numel(s), true);
        for i=1:1:numel(flooded)
            m = flooded(i);
            if (~pathExists(AdjacencyMatrix, s, peak(b).index,m))
                indexedData(m) = -2;
                peak(b).size = peak(b).size - 1;
                peak(b).area = getRegionArea(b, indexedData, fp_param);
                AdjacencyMatrix = updateEdges(fp_param, indexedData, s, b, numel(s), true);
            end
        end
        
        % exit the loop if regions areas converged before reaching the maxarea
        newArea = peak(b).area;
        loop_ctn = loop_ctn + 1;
        if ((loop_ctn > 5) && (previousArea == newArea))
            done = true;
        end
        previousArea = peak(b).area;
        
    end
    indexedData(indexedData < 0) = 0;
end
end

function AdjacencyMatrix = updateEdges(fp_param, indexedData, s, b, n, finalCheck)
% finalCheck does not connect regions that were labeled isolated and border the region around the peak
AdjacencyMatrix = zeros(n,n);
if finalCheck
    for i=1:1:n
        nodeId = s(i);
        if indexedData(nodeId) == b
            VneighbourCount = fp_param.cifti.(fp_param.surfaceComponent).adj_list.n_count(nodeId);
            VadjNodes = fp_param.cifti.(fp_param.surfaceComponent).adj_list.neighbours{nodeId};
            for j=1:1:VneighbourCount
                neighbour = VadjNodes(j);
                if (indexedData(neighbour) == b)
                    AdjacencyMatrix(i,find(s == neighbour)) = 1;
                    AdjacencyMatrix(find(s == neighbour),i) = 1;
                else
                    AdjacencyMatrix(i,find(s == neighbour)) = 0;
                    AdjacencyMatrix(find(s == neighbour),i) = 0;
                end
            end
        end
    end
else
    for i=1:1:n
        nodeId = s(i);
        if indexedData(nodeId) == b
            VneighbourCount = fp_param.cifti.(fp_param.surfaceComponent).adj_list.n_count(nodeId);
            VadjNodes = fp_param.cifti.(fp_param.surfaceComponent).adj_list.neighbours{nodeId};
            for j=1:1:VneighbourCount
                neighbour = VadjNodes(j);
                if (indexedData(neighbour) == b)
                    AdjacencyMatrix(i,find(s == neighbour)) = 1;
                    AdjacencyMatrix(find(s == neighbour),i) = 1;
                elseif (indexedData(neighbour) == -2)
                    AdjacencyMatrix(i,find(s == neighbour)) = 1;
                    AdjacencyMatrix(find(s == neighbour),i) = 1;
                else
                    AdjacencyMatrix(i,find(s == neighbour)) = 0;
                    AdjacencyMatrix(find(s == neighbour),i) = 0;
                end
            end
        end
    end
end
end

function PE = pathExists(AdjacencyMatrix, s, source, destination)
PE = false;

v = dfs(AdjacencyMatrix,find(s == source));

if ~isempty(find(v == find(s == destination)))
    PE = true;
end
end

function [d] = dfs(A,u)

full = 0;
target = 0;

% [rp, ci]=sparse_matrix(A);

n = size(A,1); nz = nnz(A);
[nzi, nzj] = find(A);
ci = zeros(nz,1);
rp = zeros(n+1,1);
for i=1:nz
    rp(nzi(i)+1)=rp(nzi(i)+1)+1;
end
rp=cumsum(rp);
for i=1:nz
    ci(rp(nzi(i))+1)=nzj(i);
    rp(nzi(i))=rp(nzi(i))+1;
end
for i=n:-1:1
    rp(i+1)=rp(i);
end
rp(1)=0;
rp=rp+1;

n=length(rp)-1;
d=-1*ones(n,1); dt=-1*ones(n,1); ft=-1*ones(n,1); pred=zeros(1,n);
rs=zeros(2*n,1); rss=0; % recursion stack holds two nums (v,ri)

% start dfs at u
t=0; targethit=0;
for i=1:n
    if i==1, v=u;
    else v=mod(u+i-1,n)+1; if d(v)>0, continue; end, end
    d(v)=0; dt(v)=t; t=t+1; ri=rp(v);
    rss=rss+1; rs(2*rss-1)=v; rs(2*rss)=ri; % add v to the stack
    while rss>0
        v=rs(2*rss-1); ri=rs(2*rss); rss=rss-1; % pop v from the stack
        if v==target || targethit
            ri=rp(v+1); targethit=1; % end the algorithm if v is the target
        end
        while ri<rp(v+1)
            w=ci(ri); ri=ri+1;
            if d(w)<0
                d(w)=d(v)+1; pred(w)=v;
                rss=rss+1; rs(2*rss-1)=v; rs(2*rss)=ri; % add v to the stack
                v=w; ri=rp(w);
                dt(v)=t; t=t+1; continue; % discover a new vertex!
            end
        end
        ft(v)=t; t=t+1; % finish with v
    end
    if ~full, break; end
end
d = find(d >= 0);
end


% --- Functions intended for debugging
function [] = plotRegionAreas(peak, fp_param)
figure();
j = 1;
for i = 1:1:length(peak)
    if peak(i).size > 0
        stem(j,peak(i).area);
        if j == 1
            hold on; grid on;
        end
        j = j + 1;
    end
end
line([0 j],[fp_param.minarea fp_param.minarea]);
line([0 j],[fp_param.maxarea fp_param.maxarea]);
end

function peakOut = getRegionAverage(peak,roiData,indexedData)
peakOut = peak;
for i=1:1:length(peak)
    regionValues = roiData(indexedData == peak(i).index);
    peakOut(i).averageValue = mean(regionValues);
end
end

function [] = plotDebugBrain(fp_param, indexedData, peak, b)
F = fp_param.cifti.(fp_param.surfaceComponent).faces;
X = fp_param.cifti.(fp_param.surfaceComponent).very_inflated.vertices(:,1);
Y = fp_param.cifti.(fp_param.surfaceComponent).very_inflated.vertices(:,2);
Z = fp_param.cifti.(fp_param.surfaceComponent).very_inflated.vertices(:,3);
area_string = sprintf('Area: %0.5f\n',peak(b).area);
DEBUG_indexedData = indexedData;
DEBUG_indexedData(DEBUG_indexedData ~= -1 & DEBUG_indexedData ~= -2 & DEBUG_indexedData ~= b) = 0;
DEBUG_indexedData(DEBUG_indexedData == b) = 1;
figure(4);
trimesh(F,X,Y,Z,DEBUG_indexedData);
axis equal;
colorbar;
title(area_string);
end
