function [roi peak] = img_find_peaks_volume(img, minsize, maxsize, val, t, options, verbose)

%function [roi peak] = img_find_peaks_volume(img, minsize, maxsize, val, t, options, verbose)
%
%   Find peaks and uses watershed algorithm to grow regions from them on the
%   brain model components modeled in 3D space (voxels).
%
%   INPUTS
%   ======
%
%   --image       input nimage object
%   --minsize     minimal size of the resulting ROI  [0]
%   --maxize      maximum size of the resulting ROI  [inf]
%   --val         whether to find positive, negative or both peaks ('n', 'p', 'b') ['b']
%   --t           threshold value [0]
%   --options     list of options separated with a pipe symbol ("|"):
%
%                 - for the number of frames to be analyzed:
%
%                    []
%                       analyze only the first frame
%                    'frames:[LIST OF FRAMES]'
%                       analyze the list of frames
%                    'frames:all'
%                       analyze all the frames
%
%                 - for the type of ROI boundary:
%
%                     []
%                       boundary left unmodified
%                     'boundary:remove'
%                       remove the boundary regions
%                     'boundary:highlight'
%                       highlight boundaries with a value of -100
%                     'boundary:wire'
%                       remove ROI data and return only ROI boundaries
%
%                 - to limit the growth of regions to subcortical structures:
%
%                     []
%                       growth not limited
%                     'limitvol:1'
%                       limit growth of regions to subcortical structures
%                     'limitvol:0'
%                       growth not limited
%
%    --verbose     whether to report the peaks (1) and also be verbose (2) [false]
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
%   immediate neighbors. It then uses a watershed algorithm to flood the peaks,
%   so that all the peaks that result in regions smaller than the specified
%   minsize get either removed or flooded in from the adjoining higher peak (if
%   if one exists). If final peaks are too large, they get re-flooded to the
%   specified maxsize only.
%
%   This method is used specifically for the brain models constructed from
%   voxels in 3D space.
%
%   EXAMPLE USE 1
%   =============
%
%   To get a roi image (dscalar) of both positive and negative peak regions with
%   miminum z value of (-)3 and 72 contiguous voxels in size, but no larger than
%   300 voxels, use::
%
%       roi = img.img_find_peaks_volume(72, 300, 'b', 3);
%
%   EXAMPLE USE 2
%   =============
%
%   To perform an operation on a time series (dtseries) image with similar
%   parameters as in the first example on frames 1, 3, 7 with verbose output
%   use::
%
%       roi = img.img_find_peaks_volume([72 50], [300 250], 'b', 3, ...
%           'frames:[1 3 7]', 2);
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 7 || isempty(verbose), verbose = false;            end
if nargin < 6 || isempty(options), options = '';               end
if nargin < 5 || isempty(t),       t       = 0;                end
if nargin < 4 || isempty(val),     val     = 'b';              end
if nargin < 3 || isempty(maxsize), maxsize = inf;              end
if nargin < 2 || isempty(minsize), minsize = 1;                end

% --- load CIFTI brain model data
load('cifti_brainmodel');

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
options_parsed = general_parse_options([], options);
if ~isfield(options_parsed,'frames')
    options_parsed.frames = 1;
end
if ~isfield(options_parsed,'boundary')
    options_parsed.boundary = '';
end
if ~isfield(options_parsed,'limitvol')
    options_parsed.limitvol = false;
end
frames = options_parsed.frames;
boundary = options_parsed.boundary;
limit_growth = options_parsed.limitvol;

% --- Set up data
% check for the number of frames in the image
if img.frames == 1
    img.data  = img.image4D;
    data  = zeros(size(img.data)+2);
    data(2:(img.dim(1)+1),2:(img.dim(2)+1),2:(img.dim(3)+1)) = img.data;
else
    if verbose, fprintf('\n---> more than 1 frame detected'); end
    % if more than 1 frame, perform img_find_peaks() on each frame recursivelly
    img_temp = img; img_temp.frames = 1;
    roi = img;
    peak = cell(1,img.frames);
    for fr = frames
        if verbose, fprintf('\n---> performing ROI on frame %d', fr); end
        img_temp.data = img.data(:,fr);
        [img_temp, p_temp] = img_temp.img_find_peaks_volume(minsize, maxsize, val, t, options, verbose_pass);
        roi.data(:,fr)=img_temp.image2D();
        peak{fr} = p_temp;
    end
    return;
end

% --- Flip to focus on the relevant value(s)

if strcmp(val, 'b')
    data = abs(data);
elseif strcmp(val, 'p')
    data(data < 0) = 0;
elseif strcmp(val, 'n')
    data(data > 0) = 0;
    data = data * -1;
else
    error('No value specified!');
end

data(data < t) = 0;

% --- Find all the relevant maxima

if verbose, fprintf('\n---> identifying initial set of peaks'); end

p    = 0;
peak = [];

for x = 2:img.dim(1)+1
    for y = 2:img.dim(2)+1
        for z = 2:img.dim(3)+1
            if data(x, y, z) > 0 && data(x, y, z) == max(max(max(data((x-1):(x+1), (y-1):(y+1), (z-1):(z+1)))))
                p = p + 1;
                peak(p).xyz   = [x, y, z];
                peak(p).value = data(x, y, z);
                % in img.data this value is at (x-1, y-1, z-1)
            end
        end
    end
end


% --- prepare voxel data

% reshape data to a vector and get indices and corresponding values of
% nonzero elements
[vind, ~, vval] = find(reshape(data, [], 1));

% sort the indices with respect to values
[~, s] = sort(vval, 1, 'descend');

% get sorted xyz subscripts of the 3D array
[x, y, z] = ind2sub(size(data), vind(s));

% number of nonzero voxels in thresholded data matrix
nvox = length(vval);

seg = zeros(size(data));
bpx = zeros(size(data));
assigned_vox = zeros(nvox, 1);

% --- First flooding

if verbose, fprintf('\n---> flooding %d peaks', length(peak)); end

% loop over all detected maxima and label the roi data matrix
for n = 1:length(peak)
    seg(peak(n).xyz(1), peak(n).xyz(2), peak(n).xyz(3)) = n;
    peak(n).size = 1;
end

% label all voxels with assigned peaks
for n = 1:nvox
    if seg(x(n), y(n), z(n)) > 0
        assigned_vox(n) = 1;
    end
end

% loop until all nonzero voxels have been assigned a peak or _____
while min(assigned_vox) == 0
    bpx(:) = 0;
    for n = 1:nvox
        
        if assigned_vox(n) > 0
            continue
        end
        
        % check the neighborhood
        neighborhood = seg((x(n)-1):(x(n)+1), (y(n)-1):(y(n)+1), (z(n)-1):(z(n)+1));
        
        if limit_growth
            vox_a = [x(n),y(n),z(n)];
            neigb_list = combvec((x(n)-1):(x(n)+1), (y(n)-1):(y(n)+1), (z(n)-1):(z(n)+1))';
            neigb_list = neigb_list(~any(min(neigb_list,2)<=1,2),:);
            for neibg=1:size(neigb_list,1)
                if (~isSameStructure(vox_a-1, neigb_list(neibg,:)-1, img, components))
                    neighborhood(neibg) = 0;
                end
            end
            
            if ~any(neighborhood)
                assigned_vox(n) = 1;
            end
        end
        
        u = unique(neighborhood);
        u = u(u>0);
        
        if length(u) == 1 % assign the single value
            seg(x(n), y(n), z(n)) = u;
            peak(u).size = peak(u).size + 1;
            assigned_vox(n) = 1;
            
            % update peak info to the higher peak
            peak = update_peak_information(peak, u, [x(n), y(n), z(n)], data);
%             if abs(peak(u).value) < abs(data(x(n), y(n), z(n)))
%                 peak(u).value = data(x(n), y(n), z(n));
%                 peak(u).xyz   = [x(n), y(n), z(n)];
%             end
            
        elseif length(u) > 1 % put it to the closest peak
            curr_dist = inf;
            % loop across neighboring peaks and assign the closer one
            for k = u(:)'
                dist_peak = sqrt(sum(([x(n) y(n) z(n)] - peak(k).xyz).^2));
                if dist_peak < curr_dist
                    curr_dist = dist_peak;
                    closer_peak = k;
                end
            end
            bpx(x(n), y(n), z(n)) = closer_peak;
            peak(closer_peak).size = peak(closer_peak).size + 1;
            assigned_vox(n) = 1;
            
            % update peak info to the higher peak
            peak = update_peak_information(peak, closer_peak, [x(n), y(n), z(n)], data);
%             if abs(peak(closer_peak).value) < abs(data(x(n), y(n), z(n)))
%                 peak(closer_peak).value = data(x(n), y(n), z(n));
%                 peak(closer_peak).xyz   = [x(n), y(n), z(n)];
%             end
            
        end
    end
    seg = seg + bpx;
end

% --- reassign ROI too small

if ~isempty(peak)
    small = peak([peak.size] < minsize);
else
    small = [];
end

while ~isempty(small)
    
    % start with the smallest roi remaining
    rsize = min([small.size]);
    rtgts = find([peak.size]==rsize);
    
    if verbose, fprintf('\n---> %d regions too small, refilling %d regions of size %d', length(small), length(rtgts), rsize); end
    
    for rtgt = rtgts(:)'
        
        [vind, ~, vval] = find(seg(:) == rtgt);
        [~, s]    = sort(vval, 1, 'descend');
        [x, y, z] = ind2sub(size(data), vind(s));
        nvox      = length(vval);
        
        done = false;
        for n = 1:nvox
            
            % check the neighborhood
            neighborhood = seg((x(n)-1):(x(n)+1), (y(n)-1):(y(n)+1), (z(n)-1):(z(n)+1));
            
            % filter neighboring voxels for regions
            if limit_growth
                vox_a = [x(n),y(n),z(n)];
                neigb_list = combvec((x(n)-1):(x(n)+1), (y(n)-1):(y(n)+1), (z(n)-1):(z(n)+1))';
                neigb_list = neigb_list(~any(min(neigb_list,2)<=1,2),:);
                for neibg=1:size(neigb_list,1)
                    if (~isSameStructure(vox_a-1, neigb_list(neibg,:)-1, img, components))
                        neighborhood(neibg) = 0;
                    end
                end
            end
            
            % get all the neighboring regions of each voxel of a the small region
            u = unique(neighborhood);
            u = u(u > 0 & u ~= rtgt);
            
            % if only one region neighbors the small ROI assign it to that one
            if length(u) == 1
                
                seg(seg==rtgt) = u;
                peak(u).size = peak(u).size + peak(rtgt).size;
                
                % update peak info to the higher peak
                peak = update_peak_information(peak, u, rtgt);
%                 if abs(peak(u).value) < abs(peak(rtgt).value)
%                     peak(u).value = peak(rtgt).value;
%                     peak(u).xyz   = peak(rtgt).xyz;
%                 end
                
                done = true;
                break
                % if more than one region neighbors the small ROI assign each
                % voxel of the small region to a closes neighboring region
            elseif length(u) > 1
                for m = 1:nvox
                    closer_peak = 0;
                    curr_dist = inf;
                    for k = u(:)'
                        dist_peak = sqrt(sum(([x(m) y(m) z(m)] - peak(k).xyz).^2));
                        if dist_peak < curr_dist
                            curr_dist = dist_peak;
                            closer_peak = k;
                        end
                    end
                    seg(x(m), y(m), z(m)) = closer_peak;
                    peak(closer_peak).size = peak(closer_peak).size + 1;
                    
                    % update peak info to the higher peak
                    peak = update_peak_information(peak, closer_peak, [x(m), y(m), z(m)], data);
%                     if abs(peak(closer_peak).value) < abs(data(x(m), y(m), z(m)))
%                         peak(closer_peak).value = data(x(m), y(m), z(m));
%                         peak(closer_peak).xyz = [x(m), y(m), z(m)];
%                     end
                    
                end
                done = true;
                break
            end
        end
        if ~done
            seg(seg==rtgt) = 0;
        end
        peak(rtgt).size = 0;
    end
    small = peak([peak.size] > rsize & [peak.size] < minsize);
end



% --- Trim regions that are too large

if ~isempty(peak)
    big = find([peak.size] > maxsize);
else
    big = [];
end

if ~isempty(big) && verbose, fprintf('\n\n---> found %d ROI that are too large', length(big)); end

for b  = big(:)'
    
    np = 0;
    seg(seg==(b)) = -1;
    plist = zeros(peak(b).size, 4);
    
    if verbose, fprintf('\n---> reflooding region %d', b); end
    
    x = peak(b).xyz(1);
    y = peak(b).xyz(2);
    z = peak(b).xyz(3);
    
    peak(b).size = 1;
    seg(x, y, z) = b;
    [seg, plist, np] = addPriority(data, seg, plist, x, y, z, np);
    
    while np > 0
        
        x = plist(1,1);
        y = plist(1,2);
        z = plist(1,3);
        
        plist(1:np,:) = plist(2:(np+1),:);
        np = np - 1;
        
        seg(x, y, z) = b ;
        peak(b).size = peak(b).size + 1;
        % update peak info to the higher peak
        peak = update_peak_information(peak, b, [x, y, z], data);
        [seg, plist, np] = addPriority(data, seg, plist, x, y, z, np);
        
        if peak(b).size >= maxsize
            break
        end
    end
end
seg(seg<1) = 0;

% --- relabel to consecutive labels

c = 1;
for p = 1:length(peak)
    if peak(p).size > 0
        seg(seg == p) = c;
        peak(p).label = c;
        c = c + 1;
    end
end

% --- remove empty peaks

if ~isempty(peak)
    peak = peak([peak.size]>0);
end

% --- embed ROI
roi = img.zeroframes(1);
roi.data = seg(2:(img.dim(1)+1),2:(img.dim(2)+1),2:(img.dim(3)+1));

% --- define borders between ROIs as desired by the user
nonZseg = find(seg>0)';
seg_size = size(seg);
boundary_map = zeros(size(seg));
for n=nonZseg
    [x, y, z] = ind2sub(size(seg), n);
    cs = seg(x,y,z);
    for l=[-1 1]
        if (x > 1 && x < seg_size(1))
            if seg(x+l,y,z) ~= cs, boundary_map(x+l,y,z) = -1; end
        end
        if (y > 1 && y < seg_size(2))
            if seg(x,y+l,z) ~= cs, boundary_map(x,y+l,z) = -1; end
        end
        if (z > 1 && z < seg_size(3))
            if seg(x,y,z+l) ~= cs, boundary_map(x,y,z+l) = -1; end
        end
    end
end

roi_out = img.zeroframes(1);
switch (boundary)
    case 'remove'
        seg(boundary_map == -1) = 0;
        roi_out.data = seg(2:(img.dim(1)+1),2:(img.dim(2)+1),2:(img.dim(3)+1));
    case 'highlight'
        seg(boundary_map == -1) = -100;
        roi_out.data = seg(2:(img.dim(1)+1),2:(img.dim(2)+1),2:(img.dim(3)+1));
    case 'wire'
        roi_out.data = boundary_map(2:(img.dim(1)+1),2:(img.dim(2)+1),2:(img.dim(3)+1)).*(-1);
    otherwise
        roi_out.data = roi.data;
end

% --- gather statistics

if isempty(peak)
    if report, fprintf('\n---> No peaks to report on!\n'); end
else
    
    roiinfo     = roi.img_get_xyz(img);
    roiinfo.ijk = [reshape([peak.label], [],1) reshape([peak.xyz], 3, [])' - 1];
    roiinfo.xyz = roi.img_get_xyz(roiinfo.ijk);
    
    if report, fprintf('\n---> peak report - volume structures\n'); end
    
    for p = 1:length(peak)
        peak(p).ijk = peak(p).xyz - 1;
        peak(p).xyz = roiinfo.xyz(p, end-2:end);
        peak(p).value = img.data(peak(p).ijk(1), peak(p).ijk(2), peak(p).ijk(3));
        peak(p).Centroid = roiinfo.cxyz(p, end-2:end);
        peak(p).WeightedCentroid = roiinfo.wcxyz(p, end-2:end);
        peak(p).averageValue = mean(img.data(roi.data == peak(p).label));
        
        if limit_growth
            peak(p).component = cifti.shortnames{components.volumeMask(peak(p).ijk(1),peak(p).ijk(2),peak(p).ijk(3))};
        else
            peak(p).component = 'volume';
        end
        
        if report, fprintf('\nROI:%3d  label: %3d  value: %5.1f  voxels: %3d  peak indices: %3d %3d %3d  peak: %5.1f %5.1f %5.1f  centroid: %5.1f %5.1f %5.1f  wcentroid: %4.1f %4.1f %4.1f', p, peak(p).label, peak(p).value, peak(p).size, peak(p).ijk, peak(p).xyz, peak(p).Centroid, peak(p).WeightedCentroid); end
    end
    
    if report, fprintf('\n'); end
end

roi = roi_out;

% --- the end

if verbose, fprintf('\n---> DONE\n'); end




% --- SUPPORT FUNCTIONS

end

function [seg, plist, np] = addPriority(data, seg, plist, x, y, z, np)
for xi = x-1:x+1
    for yi = y-1:y+1
        for zi = z-1:z+1
            if seg(xi, yi, zi) == -1
                seg(xi, yi, zi) = -2;
                np = np + 1;
                v  = data(xi, yi, zi);
                for n = 1:np
                    if v > plist(n, 4)
                        plist(n+1:np+1,:) = plist(n:np,:);
                        plist(n,:) = [xi, yi, zi, v];
                        break
                    end
                end
            end
        end
    end
end
end

function status = isSameStructure(vox_a, vox_b, img, components)
if (components.volumeMask(vox_a(1),vox_a(2),vox_a(3)) == components.volumeMask(vox_b(1),vox_b(2),vox_b(3)))
    status = true;
else
    status = false;
end
end

function peak = update_peak_information(peak, current_peak, appended_index, data)
update_from_peak = false;
if nargin < 4 || isempty(data), update_from_peak = true; end

if ~update_from_peak && length(appended_index) ~= 3
    error('If updating from the data matrix, appended_index should be an (x,y,z) vector!\n');
end

if update_from_peak
    if abs(peak(current_peak).value) < abs(peak(appended_index).value)
        peak(current_peak).value = peak(appended_index).value;
        peak(current_peak).xyz   = peak(appended_index).xyz;
    end
else
    x = appended_index(1);
    y = appended_index(2);
    z = appended_index(3);
    if abs(peak(current_peak).value) < abs(data(x, y, z))
        peak(current_peak).value = data(x, y, z);
        peak(current_peak).xyz   = appended_index;
    end
end


end

