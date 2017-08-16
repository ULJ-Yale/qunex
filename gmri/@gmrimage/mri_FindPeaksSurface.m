function [roi peak] = mri_FindPeaksSurface(img, surfaceComponent, projection, minarea, maxarea, val, t, options, verbose)

%function [roi peak] = mri_FindPeaksSurface(img, surfaceComponent, projection, minarea, maxarea, val, t, verbose)
%
%       Find peaks and uses watershed algorithm to grow regions from them on the brain
%       model components constructed with surface elements (ex. left and right cortex).
%
%   INPUT
%       img              - input gmrimage object
%       surfaceComponent - brain component of type surface to perform ROI operation on ('cortex_left', 'cortex_right') ['cortex_left']
%       projection       - type of surface component projection ('midthickness', 'inflated',...)
%                          or a path to the surface file (.surf.gii) of the left or right cortex:
%                                a) for a default projection: 'midthickness' ['midthickness']
%                                b) for a specific projection:
%                                        'CL_projection.surf.gii'
%       minarea          - minimal size of the resulting ROI  [0]
%       maxarea          - maximum size of the resulting ROI  [inf]
%       val              - whether to find positive, negative or both peaks ('n', 'p', 'b') ['b']
%       t                - threshold value [0]
%       options          - list of options separated with a pipe symbol ("|"):
%                                a) for the number of frames to be analized:
%                                           - []                        ... analyze only the first frame
%                                           - 'frames:[LIST OF FRAMES]' ... analyze the list of frames
%                                           - 'frames:all'              ... analyze all the frames
%                                b) for the type of ROI boundary:
%                                           - []                        ... boundary left unmodified
%                                           - 'boundary:remove'         ... remove the boundary regions
%                                           - 'boundary:highlight'      ... highlight boundaries with a value of -100
%                                           - 'boundary:wire'           ... remove ROI data and return only ROI boundaries
%       verbose          - whether to report the peaks (1) and also be verbose (2) [false]
%
%   OUTPUT
%       roi              - A gmrimage with the created ROI.
%       peak             - A datastructure with information about the extracted peaks.
%
%   USE
%   The method is used to identify positive and/or negative peaks in the image,
%   and then generate ROI around them using a watershed algorithm. Specifically,
%   the method first zeros all the values below the specified threshold (t), it
%   then finds all the peaks, voxels that have the value higher than the
%   immediate neighbors. It then uses a wathershed algorithm to flood the peaks,
%   so that all the peaks that result in regions smaller than the specified
%   minsize get either removed or flooded in from the adjoining heigher peak (if
%   if one exists). If final peaks are too large, they get reflooded to the
%   specified maxsize only.
%   This method is used specifically for the surface type brain models,
%   such as the cortex in CIFTI-2 image format. It performs the operations
%   on a triangular surface mesh.
%
%   EXAMPLE USE 1
%   To get a roi image (dscalar) of both positive and negative peak regions
%   with miminum z value of (-)3 and surface peak regions of areas between
%   50 mm^2 and 250 mm^2 on a cortex_left with midthickness projection use:
%
%   roi = img.mri_FindPeaksSurface('cortex_left', 'midthickness', 50, 250, 'b', 3);
%
%   EXAMPLE USE 2
%   To perform an operation on a time series (dtseries) image with similar
%   parameters as in the first example on frames 1, 3, 7 with verbose
%   output use:
%
%   roi = img.mri_FindPeaksSurface('cortex_left', 'midthickness', 50, 250, 'b', 3, 'frames:[1 3 7]', 2);
%
%   ---
%   Written by Aleksij Kraljic, July 5, 2017
%
%   ToDo
%   - add statistics calculations for the peak data structure
%

if nargin < 9 || isempty(verbose), verbose = false;       end
if nargin < 8 || isempty(options), options = '';          end
if nargin < 7 || isempty(t),       t       = 0;           end
if nargin < 6 || isempty(val),     val     = 'b';         end
if nargin < 5 || isempty(maxarea), maxarea = inf;         end
if nargin < 4 || isempty(minarea), minarea = 1;           end
if nargin < 3 || isempty(projection), projection = 'midthickness';            end
if nargin < 2 || isempty(surfaceComponent), surfaceComponent = 'cortex_left'; end

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

% --- parse options argument
options_parsed = g_ParseOptions([],options);
if ~isfield(options_parsed,'frames')
    options_parsed.frames = 1;
end
if ~isfield(options_parsed,'boundary')
    options_parsed.boundary = '';
end
frames = options_parsed.frames;
boundary = options_parsed.boundary;

% --- Check for the number of frames in the image
if img.frames > 1
    if verbose, fprintf('\n---> more than 1 frame detected'); end
    % if more than 1 frame, perform mri_FindPeaks() on each frame recursivelly
    img_temp = img; img_temp.frames = 1;
    roi = img;
    peak = cell(1,img.frames);
    for fr = frames
        if verbose, fprintf('\n---> performing ROI on frame %d', fr); end
        img_temp.data = img.data(:,fr);
        [img_temp, p_temp] = ...
            img_temp.mri_FindPeaksSurface(surfaceComponent, projection, minarea, maxarea, val, t, 1, verbose_pass);
        roi.data(:,fr)=img_temp.image2D();
        peak{fr} = p_temp;
    end
    return;
end

% --- Load CIFTI brain model data
load('CIFTI_BrainModel.mat');

% -- Check the type of projection passed and weather it is a file
if ~sum(strcmp(projection,{'midthickness','inflated','very_inflated','sphere'}))
    subject_projection = gifti(projection);
    projection = 'subject';
    cifti.(lower(surfaceComponent)).subject.vertices = subject_projection.vertices;
    cifti.(lower(surfaceComponent)).subject.area_vector = getProjectionArea(subject_projection.vertices, surfaceComponent, cifti);
end

if strcmp(surfaceComponent, 'cortex_left')
    cmp = 1;
elseif strcmp(surfaceComponent, 'cortex_right')
    cmp = 2;
else
    error('Wrong component inserted!');
end

% --- Create an empty matrix to store the data globally for each hemisphere
data.(lower(img.cifti.shortnames{cmp})) = zeros(32492,1);
if strcmp(cifti.(lower(img.cifti.shortnames{cmp})).type,'Surface')
    data.(lower(img.cifti.shortnames{cmp}))(cifti.(lower(img.cifti.shortnames{cmp})).mask) = img.data(img.cifti.start(cmp):img.cifti.end(cmp));
end

% --- Flip to focus on the relevant value(s)
if strcmp(cifti.(lower(img.cifti.shortnames{cmp})).type,'Surface')
    if strcmp(val, 'b')
        data.(lower(img.cifti.shortnames{cmp})) = abs(data.(lower(img.cifti.shortnames{cmp})));
    elseif strcmp(val, 'p')
        data.(lower(img.cifti.shortnames{cmp}))(data.(lower(img.cifti.shortnames{cmp})) < 0) = 0;
    elseif strcmp(val, 'n')
        data.(lower(img.cifti.shortnames{cmp}))(data.(lower(img.cifti.shortnames{cmp})) > 0) = 0;
        data.(lower(img.cifti.shortnames{cmp})) = data.(lower(img.cifti.shortnames{cmp})) * -1;
    else
        error('No value specified!');
    end
    
    data.(lower(img.cifti.shortnames{cmp}))(data.(lower(img.cifti.shortnames{cmp})) < t) = 0;
end

% --- perform ROI opearions
if strcmp(cifti.(lower(img.cifti.shortnames{cmp})).type,'Surface')
    
    % --- Find all the relevant maxima
    if verbose, fprintf('\n---> identifying intial set of peaks'); end
    
    % --- Find peaks in the regions
    p = 0;
    peak = [];
    ctn_peaks = 0;
    for i=1:1:numel(cifti.(lower(img.cifti.shortnames{cmp})).adj_list.neighbours)
        if (data.(lower(img.cifti.shortnames{cmp}))(i)) > 0 &&...
                (data.(lower(img.cifti.shortnames{cmp}))(i) >= max(data.(lower(img.cifti.shortnames{cmp}))(cifti.(lower(img.cifti.shortnames{cmp})).adj_list.neighbours{i})))
            ctn_peaks = ctn_peaks + 1;
            peak(ctn_peaks).index = i;
            peak(ctn_peaks).value = data.(lower(img.cifti.shortnames{cmp}))(i);
            peak(ctn_peaks).x = cifti.(lower(img.cifti.shortnames{cmp})).(projection).vertices(i,1);
            peak(ctn_peaks).y = cifti.(lower(img.cifti.shortnames{cmp})).(projection).vertices(i,2);
            peak(ctn_peaks).z = cifti.(lower(img.cifti.shortnames{cmp})).(projection).vertices(i,3);
        end
    end
    
    % --- Preapare the data to store the non-zero data to vval and corresponding sorted indices to s
    [vind, ~, vval] = find(data.(lower(img.cifti.shortnames{cmp})));
    [~, s] = sort(vval, 1, 'descend');
    
    % allocate the global vector to store region ID at indices corresponding to the data
    seg = zeros(size(data.(lower(img.cifti.shortnames{cmp}))));
    boundaries = zeros(size(data.(lower(img.cifti.shortnames{cmp}))));
    
    % --- First flooding
    if verbose, fprintf('\n---> flooding %d peaks', length(peak)); end
    
    % assign IDs to the peaks in the seg variable
    for n = 1:length(peak)
        seg(peak(n).index) = n;
        peak(n).size = 1;
        peak(n).area = 0;
    end
    
    % flood the data starting from the highest value.
    for n = 1:numel(vval)
        % if not a peak check around which peak the vertex or ROI lies next to
        if ~any(seg(vind(s(n))) == 1:length(peak))
            % assign vertex neighbour seg ids to id
            [~, ~, id] = find(seg(cifti.(lower(img.cifti.shortnames{cmp})).adj_list.neighbours{vind(s(n))}));
            % remove duplicate ids
            u_id = unique(id);
            if isscalar(u_id)
                % if only one neighbour belongs to a ROI assign it to that one
                seg(vind(s(n))) = u_id;
                peak(u_id).size = peak(u_id).size + 1;
            elseif numel(u_id) > 1
                % if some neighbours belong to other ROIs, assign it to the largest ROI
                [~, ~, nROIs] = mode(id);
                nROIs = nROIs{1};
                if numel(nROIs) > 1
                    % if the same number of neighbours belong to multiple ROIs assign it to the one with the higher peak
                    seg(vind(s(n))) = nROIs(1);
                    maxVal = data.(lower(img.cifti.shortnames{cmp}))(peak(nROIs(1)).index);
                    maxID = nROIs(1);
                    for m=2:numel(nROIs)
                        if data.(lower(img.cifti.shortnames{cmp}))(peak(nROIs(m)).index) >= maxVal
                            maxVal = data.(lower(img.cifti.shortnames{cmp}))(peak(nROIs(m)).index);
                            maxID = nROIs(m);
                        end
                    end
                else
                    maxID = nROIs;
                end
                seg(vind(s(n))) = maxID;
                peak(maxID).size = peak(maxID).size + 1;
            end
        end
    end
    
    % --- Calculate areas of regions
    for i=1:1:length(peak)
        peak(i).area = getRegionArea(i, seg,...
            cifti.(lower(img.cifti.shortnames{cmp})).faces,...
            cifti.(lower(img.cifti.shortnames{cmp})).(lower(projection)).area_vector);
    end
    
    % --- Combine ROIs smaller then the min with the neighbouring ones
    if ~isempty(peak)
        small = peak([peak.area] < minarea);
    else
        small = [];
    end
    
    % loop until the small array is not empty
    while ~isempty(small)
        
        % size of the smallest region
        rsize = min([small.area]);
        % indices of the smallest region
        rtgts = find([peak.area]==rsize);
        
        if verbose, fprintf('\n---> %d regions too small, refilling %d regions of size %d', length(small), length(rtgts), rsize); end
        
        % loop through the smallest regions and refill them up to first contact with another region and combine them
        for rtgt = rtgts(:)'
            [vind, ~, vval] = find(seg(:) == rtgt);
            [~, s]    = sort(vval, 1, 'descend');
            % flood the data
            done = false;
            for n = 1:numel(vval)
                % assign vertex neighbour seg ids to id
                [~, ~, id] = find(seg(cifti.(lower(img.cifti.shortnames{cmp})).adj_list.neighbours{vind(n)}));
                id = id(id ~= rtgt);
                % remove duplicate ids
                u_id = unique(id);
                newId = u_id;
                if isscalar(u_id)
                    % if only one neighbour belongs to another ROI assign it to that one
                    seg(seg == rtgt) = u_id;
                    peak(u_id).size = peak(rtgt).size + peak(u_id).size;
                    done = true;
                    break;
                elseif numel(u_id) > 1
                    % if some neighbours belong to other ROIs, assign it to the largest ROI
                    [~, ~, nROIs] = mode(id);
                    nROIs = nROIs{1};
                    if numel(nROIs) > 1
                        % if the same number of neighbours belong to multiple ROIs assign it to the one with the higher peak
                        seg(vind(s(n))) = nROIs(1);
                        maxVal = data.(lower(img.cifti.shortnames{cmp}))(peak(nROIs(1)).index);
                        maxID = nROIs(1);
                        for m=2:numel(nROIs)
                            if data.(lower(img.cifti.shortnames{cmp}))(peak(nROIs(m)).index) >= maxVal
                                maxVal = data.(lower(img.cifti.shortnames{cmp}))(peak(nROIs(m)).index);
                                maxID = nROIs(m);
                            end
                        end
                    else
                        maxID = nROIs;
                    end
                    seg(seg == rtgt) = maxID;
                    peak(maxID).size = peak(rtgt).size + peak(maxID).size;
                    done = true;
                    newId = maxID;
                    break;
                end
            end
            if ~done
                seg(seg == rtgt) = 0;
            end
            peak(rtgt).size = 0;
            peak(rtgt).area = 0;
        end
        % --- Calculate areas of regions
        if ~isempty(newId)
            peak(newId).area = getRegionArea(newId, seg,...
                cifti.(lower(img.cifti.shortnames{cmp})).faces,...
                cifti.(lower(img.cifti.shortnames{cmp})).(lower(projection)).area_vector);
        end
        % remove the smallest region for the small array
        small = peak([peak.area] > rsize & [peak.area] < minarea);
    end
    
    % --- Trim regions that are too large
    if ~isempty(peak)
        big = find([peak.area] > maxarea);
    else
        big = [];
    end
    
    if ~isempty(big) && verbose, fprintf('\n\n---> found %d ROI that are too large', length(big)); end
    
    for b  = big(:)'
        
        % store the non-zero data to vval and corresponding sorted indices to s
        bigROI_data = data.(lower(img.cifti.shortnames{cmp}));
        bigROI_data(seg ~= b) = 0;
        [vind, ~, vval] = find(bigROI_data);
        [~, s] = sort(vval, 1, 'descend');
        
        seg(seg==(b)) = -1;
        
        if verbose, fprintf('\n---> reflooding region %d', b); end
        
        peak(b).size = 1;
        peak(b).area = 0;
        
        seg(vind(s(1))) = b;
        
        % refill the region around the peak by checking if every consecutive value in the sorted values list neighbours the primary region
        for n=2:1:numel(vval)
            if any(seg(cifti.(lower(img.cifti.shortnames{cmp})).adj_list.neighbours{vind(s(n))}) == b)
                seg(vind(s(n))) = b;
                peak(b).size = peak(b).size + 1;
                % --- Calculate areas of regions
                peak(b).area = getRegionArea(b, seg,...
                    cifti.(lower(img.cifti.shortnames{cmp})).faces,...
                    cifti.(lower(img.cifti.shortnames{cmp})).(lower(projection)).area_vector);
            end
            if peak(b).area >= maxarea
                break;
            end
        end
        
    end
    seg(seg<1) = 0;
    
    % --- remove empty peaks
    if ~isempty(peak)
        peak = peak([peak.area]>0);
    end
    
    % --- relable the ROI labels, starting from 1 up to the last ROI
    for i=1:1:length(peak)
        v = seg(peak(i).index);
        seg(seg == v) = i;
        peak(i).index = i;
    end

% --- define borders between ROIs as desired by the user
boundary_map = zeros(size(seg));
for n=1:1:numel(seg)
    cs = seg(n);
    if cs > 0
        ni = seg(cifti.(lower(img.cifti.shortnames{cmp})).adj_list.neighbours{n});
        boundary_map(cifti.(lower(img.cifti.shortnames{cmp})).adj_list.neighbours{n}(ni~=cs)) = -1;
    end
end

% --- remap the data back from global to CIFTI data format for export
roi = img;
switch (boundary)
    case 'remove'
        seg(boundary_map == -1) = 0;
        data.(lower(img.cifti.shortnames{cmp})) = seg;
        % --- embed data to ROI image
        roi.data(img.cifti.start(cmp):img.cifti.end(cmp)) = data.(lower(img.cifti.shortnames{cmp}))(cifti.(lower(img.cifti.shortnames{cmp})).mask);
    case 'highlight'
        seg(boundary_map == -1) = -100;
        data.(lower(img.cifti.shortnames{cmp})) = seg;
        % --- embed data to ROI image
        roi.data(img.cifti.start(cmp):img.cifti.end(cmp)) = data.(lower(img.cifti.shortnames{cmp}))(cifti.(lower(img.cifti.shortnames{cmp})).mask);
    case 'wire'
        data.(lower(img.cifti.shortnames{cmp})) = boundary_map.*(-1);
        % --- embed data to ROI image
        roi.data(img.cifti.start(cmp):img.cifti.end(cmp)) = data.(lower(img.cifti.shortnames{cmp}))(cifti.(lower(img.cifti.shortnames{cmp})).mask);
    otherwise
        data.(lower(img.cifti.shortnames{cmp})) = seg;
        % --- embed data to ROI image
        roi.data(img.cifti.start(cmp):img.cifti.end(cmp)) = data.(lower(img.cifti.shortnames{cmp}))(cifti.(lower(img.cifti.shortnames{cmp})).mask);
end

% --- the end
if verbose, fprintf('\n===> DONE\n'); end

end

if isempty(peak)
    if report, fprintf('\n===> No peaks to report on!\n'); end
else
    if report, fprintf('\n===> peak report - %s\n',(lower(img.cifti.shortnames{cmp}))); end
    for p = 1:length(peak)
        if report, fprintf('\nROI:%3d  index: %3d  value: %5.1f  size: %3d  area: %3d', p, peak(p).index, peak(p).value, peak(p).size, peak(p).area); end
    end
    if report, fprintf('\n'); end
end

end

% --- SUPPORT FUNCTIONS

function [area] = getRegionArea(i, seg, face_matrix, area_vector)

% --- modify faces matrix to find the corresponding faces
F = face_matrix;
% --- calculate vertex indices of the region
region_indices = find(seg == i);
% --- compute the logical array of the faces that contain existing vertices
F = ismember(F,region_indices);
% --- sum the rows of the logical faces matrix in order to see which face consists of all existing 3 vertices
F = sum(F,2);
% --- calculate the area of the region
area = (1/3) * sum(area_vector(F > 0));

end

function [projection_area_vector] = getProjectionArea(projection_vertices, surface_component, cifti)

%projection_area_vector = zeros(length(cifti.surface_component.faces),1);
ab = projection_vertices(cifti.(surface_component).faces(:,2),:) - ...
    projection_vertices(cifti.(surface_component).faces(:,1),:);
ac = projection_vertices(cifti.(surface_component).faces(:,3),:) - ...
    projection_vertices(cifti.(surface_component).faces(:,1),:);
projection_area_vector = 0.5.*sqrt(sum(cross(ab,ac).^2,2));

end
