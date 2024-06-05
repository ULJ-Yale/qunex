function [roi vol_peak peak] = img_find_peaks(img, mindim, maxdim, val, t, projection_type, options, verbose)

%``img_find_peaks(img, mindim, maxdim, val, t, projection_type, options, verbose)``
%
%   Find peaks and uses watershed algorithm to grow regions from them.
%
%   INPUTS
%   ======
%
%   --img               input nimage object
%   --mindim            [minimum size, minimum area] of the resulting ROI  
%                       [0, 0]
%   --maxdim            [maximum size, maximum area] of the resulting ROI  
%                       [inf, inf]
%   --val               whether to find positive, negative or both peaks 
%                       ('n', 'p', 'b') ['b']
%   --t                 threshold value [0]
%   --projection_type   type of surface component projection ('midthickness', 
%                       'inflated', ...) or a string containing the path to the 
%                       surface files (.surf.gii) for both, left and right
%                       cortex separated by a pipe:
%
%                       - for a default projection: 'type: midthickness' 
%                         ['type:midthickness']
%                       - for a specific projection:
%                         'cortex_left: CL_projection.surf.gii|cortex_right: CR_projection.surf.gii'
%
%   --options           list of options separated with a pipe symbol ("|"):
%                       
%                       - for the number of frames to be analized:
%
%                          []                        
%                               analyze only the first frame
%                          'frames:[LIST OF FRAMES]' 
%                               analyze the list of frames
%                          'frames:all'              
%                               analyze all the frames
%
%                       - for the type of ROI boundary:
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
%                       - to limit the growth of regions to subcortical structures:
%    
%                           []
%                               growth not limited
%                           'limitvol:1'
%                               limit growth of regions to subcortical structures
%                           'limitvol:0'
%                               growth not limited
%
%   --verbose           whether to report the peaks (1) and also be verbose:
%
%                       a) on the first level (2)
%                       b) on all the levels  (3) [false]
%
%   OUTPUTS
%   =======
%
%   roi 
%       A nimage with the created ROI.
%
%   vol_peak
%       A datastructure with information about the extracted peaks from volume components.
%
%   peak
%       A datastructure with information about the extracted peaks from surface components.
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
%   one exists). If final peaks are too large, they get reflooded to the
%   specified maxsize only.
%
%   This method supports both NIfTY and CIFTI-2 image types. If the file is
%   NIfTY, the function performs the operations by calling the function
%   img_find_peaks_volume, if the file is CIFTI-2, it extracts the volume
%   components from the image and performs the operations by calling
%   img_find_peaks_volume on extracted volume components and img_find_peaks_surface
%   on surface components (cortex).
%
%   EXAMPLE USE 1 (CIFTI-2 image)
%   =============================
%
%   To get a roi image (dscalar) of both positive and negative peak regions with
%   miminum z value of (-)3 and 72 contiguous voxels in size, but no larger than
%   300 voxels, and surface peak regions of areas between 50 mm^2 and 250 mm^2
%   on a cortex midthickness projection use::
%
%       roi = img.img_find_peaks([72 50], [300 250], 'b', 3, 'type:midthickness');
%
%   EXAMPLE USE 2 (CIFTI-2 image)
%   =============================
%
%   To perform an operation on a time series (dtseries) image with similar
%   parameters as in the first example on frames 1, 3, 7 with verbose output and
%   highlighted ROI boundaries use::
%
%       roi = img.img_find_peaks([72 50], [300 250], 'b', 3, ...
%           'type:midthickness', 'frames:[1 3 7]|boundary:highlight', 2);
%
%   EXAMPLE USE 3 (NIfTI image)
%   ===========================
%
%   To get a roi image of both positive and negative peak regions with miminum z
%   value of (-)1 and 50 contiguous voxels in size, but no larger than 250
%   voxels use::
%
%       roi = img.img_find_peaks(50, 250, 'b', 1);
%
%   EXAMPLE USE 4 (CIFTI-2 image)
%   =============================
%
%   To get a roi image of both positive and negative peak regions with miminum z
%   value of (-)3 and 72 contiguous voxels in size, but no larger than 300
%   voxels on a projection defined with a specific surface file and boundaries
%   removed use::
%
%       [roi vol_peaks peaks] = img.img_find_peaks([72 80], [300 350], 'b', 3, ...
%       'cortex_left:CL_projection.surf.gii|cortex_right:CR_projection.surf.gii',...
%       'boundary:remove', 1);
%
%   COMPLETE FLOW EXAMPLE
%   =====================
%
%   ::
%
%       %% import dscalar CIFTI-2 image
%       img = nimage('example_image.dscalar.nii');
%       
%       %% FindPeaks input arguments
%       % mindim: [min. size of the vol. ROIs (voxels), min. area of the surf. ROIs (mm^2)]
%       mindim = [30 30];
%       % maxdim: [max. size of the vol. ROIs (voxels), max. area of the surf. ROIs (mm^2)]
%       maxdim = [300 300];
%       % val: find both positive and negative peaks
%       val = 'b';
%       % t: threshold value
%       t = 3;
%       % projection: type of the projection (required for the max/min surface area arguments)
%       projection = 'midthickness';
%       % frames: which frames to consider [1 5 7,...] (can be [] for dscalar)
%       frames = [];
%       % verbose: - whether to report the peaks (1) and also be verbose: 
%       %                  a) on the first level (2)
%       %                  b) on all the levels  (3)
%       verbose = 2;
%       
%       %% perform ROI operation
%       [roi vol_peak peak] = img.img_find_peaks(mindim, maxdim, val, t, ...
%                           projection, frames, verbose);
%       
%       %% export the modified image
%       img_save_nifti(roi,'example_image_ROI.dscalar.nii');
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 8 || isempty(verbose),    verbose = false;                            end
if nargin < 7 || isempty(options),    options = '';                               end
if nargin < 6 || isempty(projection_type), projection_type = 'type:midthickness'; end
if nargin < 5 || isempty(t),          t       = 0;                                end
if nargin < 4 || isempty(val),        val     = 'b';                              end
if nargin < 3
    maxdim = [inf, inf];
elseif isempty(maxdim)
    maxdim = [inf, inf];
elseif isscalar(maxdim)
    maxdim = [maxdim, inf];
end
if nargin < 2
    mindim = [0, 0];
elseif isempty(mindim)
    mindim = [0, 0];
elseif isscalar(mindim)
    mindim = [mindim, 0];
end

minsize = mindim(1);
minarea = mindim(2);
maxsize = maxdim(1);
maxarea = maxdim(2);

default_options = 'frames:1|boundary:|limitvol:0';

% --- Script verbosity
report = false;
verbose_pass = false;
if verbose == 1
    verbose = false;
    report  = true;
    verbose_pass = 1;
elseif verbose == 2
    report  = true;
    verbose_pass = false;
elseif verbose == 3
    verbose = true;
    report  = true;
    verbose_pass = 2;
end

% --- assign proper projection type format
projection_raw = projection_type;
projection_type = general_parse_options([],projection_type);
if isfield(projection_type,'cortex_left') && isfield(projection_type,'cortex_right')
    projection.cortex_left = projection_type.cortex_left;
    projection.cortex_right = projection_type.cortex_right;
else
    projection.cortex_left = projection_type.type;
    projection.cortex_right = projection_type.type;
end

% --- parse options argument
options_parsed = general_parse_options([], options, default_options);

if img.frames > 1 && options_parsed.frames == 1 
    warning(['img_find_peaks(): image contains multiple frames however ',...
        'options->frames is set to 1. As a result, only the ',...
        'first frame will be processed.']);
end

frames = options_parsed.frames;
if strcmp(frames,'all')
    frames = 1:1:img.frames;
end
options_single_frame = strcat('boundary:',options_parsed.boundary,...
                              '|limitvol:',num2str(options_parsed.limitvol));

% --- Check for the number of frames in the image
if img.frames > 1
    if verbose, fprintf('\nMAIN FIND PEAKS---> more than 1 frame detected\n'); end
    % if more than 1 frame, perform img_find_peaks() on each frame recursivelly
    img_temp = img; img_temp.frames = 1;
    roi = img;
    peak = cell(1,img.frames);
    vol_peak = cell(1,img.frames);
    for fr = frames
        if verbose, fprintf('\nMAIN FIND PEAKS---> performing ROI ops on frame %d', fr); end
        img_temp.data = img.data(:,fr);
        [img_temp, p_temp_vol, p_temp] = img_temp.img_find_peaks(mindim, maxdim, val, t, projection_raw, options_single_frame, verbose);
        roi.data(:,fr)=img_temp.image2D();
        vol_peak{fr} = p_temp_vol;
        peak{fr} = p_temp;
    end
    return;
end

% --- Load CIFTI brain model data
load('cifti_brainmodel');

if strcmpi(img.imageformat, 'CIFTI-2')
    % --- Extract volume components
    if verbose, fprintf('\nMAIN FIND PEAKS---> extracting volume components'); end
    vol_sections = img.img_extract_cifti_volume();
    
    % --- Find peaks for volume components
    if verbose, fprintf('\nMAIN FIND PEAKS---> finding peaks for volume components'); end
    [vol_roi vol_peak] = vol_sections.img_find_peaks_volume(minsize, maxsize, val, t, options, verbose_pass);
    
    % --- Embed volume components
    if verbose, fprintf('\nMAIN FIND PEAKS---> embedding volume components'); end
    roi = img.img_embed_cifti_volume(vol_roi);
    
    % --- Find peaks for surface components
    if verbose, fprintf('\nMAIN FIND PEAKS---> finding peaks for surface components'); end
    for i=1:1:numel(img.cifti.shortnames)
        if strcmp(cifti.(lower(img.cifti.shortnames{i})).type,'Surface')
            [roi peak.(lower(img.cifti.shortnames{i}))] = roi.img_find_peaks_surface(lower(img.cifti.shortnames{i}),...
                projection.(lower(img.cifti.shortnames{i})), minarea, maxarea, val, t, options, verbose_pass);
        end
    end
    % --- Relable the peaks to have unique IDs
    if ~isempty(vol_peak)
        offsetID = vol_peak(end).label;
    else
        offsetID = 0;
    end
    for i=1:1:numel(img.cifti.shortnames)
        if strcmp(cifti.(lower(img.cifti.shortnames{i})).type,'Surface')
            t_data = roi.data(img.cifti.start{i}:img.cifti.end{i});
            for j=1:1:length(peak.(lower(img.cifti.shortnames{i})))
                peak.(lower(img.cifti.shortnames{i}))(j).index = offsetID + j;
            end
            t_data(t_data ~= 0) = t_data(t_data ~= 0) + offsetID;
            roi.data(img.cifti.start{i}:img.cifti.end{i}) = t_data;
            if ~isempty(peak.(lower(img.cifti.shortnames{i})))
                offsetID = peak.(lower(img.cifti.shortnames{i}))(end).index;
            else
                offsetID = 0;
            end
        end
    end
    
    % --- compute grayordinates of every peak
    for i=1:1:length(vol_peak)
       idx = find(roi.data == vol_peak(i).label);
       roi_values = img.data(idx);
       
       if strcmpi(val, 'b')
           [~, peak_ind] = max(abs(roi_values));
       elseif strcmpi(val, 'p')
           [~, peak_ind] = max(roi_values);
       elseif strcmpi(val, 'n')
           [~, peak_ind] = min(roi_values);
       end
       
       roi_val = roi_values(peak_ind);
       vol_peak(i).grayord = idx(peak_ind);
       
       % assert(vol_peak(i).value == roi_val, 'ROI peak does not match the maximum/minimum value in that region!\n');
       if isempty(options_parsed.boundary) && ~(vol_peak(i).value == roi_val)
           fprintf('\n');
           warning('ROI volume peak does not match the maximum/minimum value in region %d!\n', vol_peak(i).label);
       end
    end
    
    for i=1:1:numel(img.cifti.shortnames)
        if strcmp(cifti.(lower(img.cifti.shortnames{i})).type,'Surface')
            for j=1:1:length(peak.(lower(img.cifti.shortnames{i})))
                idx = find(roi.data == peak.(lower(img.cifti.shortnames{i}))(j).index);
                roi_values = img.data(idx);
                
                if strcmpi(val, 'b')
                    [~, peak_ind] = max(abs(roi_values));
                elseif strcmpi(val, 'p')
                    [~, peak_ind] = max(roi_values);
                elseif strcmpi(val, 'n')
                    [~, peak_ind] = min(roi_values);
                end
                
                roi_val = roi_values(peak_ind);
                peak.(lower(img.cifti.shortnames{i}))(j).grayord = idx(peak_ind);
                
                % assert(vol_peak(i).value == roi_val, 'ROI peak does not match the maximum/minimum value in that region!\n');
                if isempty(options_parsed.boundary) && ~(peak.(lower(img.cifti.shortnames{i}))(j).value == roi_val)
                    fprintf('\n');
                    warning('ROI surface peak does not match the maximum/minimum value in region %d!\n', peak.(lower(img.cifti.shortnames{i}))(j).index);
                end
            end
        end
    end
    
elseif strcmpi(img.imageformat, 'NIFTI')
    if verbose, fprintf('\nMAIN FIND PEAKS---> finding peaks for volume components'); end
    [roi vol_peak] = img.img_find_peaks_volume(minsize, maxsize, val, t, options, verbose_pass);
    peak = [];
end

if verbose, fprintf('\nMAIN FIND PEAKS---> DONE\n'); end
