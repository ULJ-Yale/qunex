function [img] = img_prep_roi(roi, mask, options)

%``img_prep_roi(roi, mask, options)``
%
%   Reads in an ROI file, if a second file is provided, it uses it to mask the
%   first one.
%
%   Parameters:
%       --roi (str or nimage object):
%           A path to a file or an nimage object that specifies the ROI
%           to be generated. In case of a pipe separated string, the first
%           item will be considered a path, and all others as <key>:<value>
%           pairs of optional information. For details see Notes section.
%
%       --mask (str, integer, or nimage object, default ''):
%           A path to a file or a nimage object to be used as a mask, an
%           index or indeces of the frame(s), or the name or names of
%           the maps to be used. For more details see Notes section.
%
%       --options (str, default ``'check:warning|volumes:|maps:|rois:|roinames:|standardize:no|threshold:'``)
%           A pipe separated '<key>:<value>|<key>:<value>' string 
%           specifying further options. The possible options are:
%           
%           - check : warning ('ignore' / 'warning' / 'error')
%               How to handle unknown integer codes from the .names file:
%               - 'ignore' (don't do anything)
%               - 'warning' (throw a warning)
%               - 'error' (throw an error)
%           - volumes : a comma separated list
%               Which volumes to use – list of indeces of the volumes to
%               use to define ROI.
%           - maps : a comma separated list 
%               Which maps to use - a list of map names refering to the
%               maps to use to define ROI.
%           - rois : a comma separated list
%               Which ROI to use - a list of ROI indices or ROI names to 
%               retain and use. The specification will reorder the roi in the
%               structure in the order listed in rois parameter.
%           - roinames: a comma separated list
%               ROI names - a list of names for the ROI that are created. 
%               They should  be listed in the order the roi are set in the 
%               roi structure. This is the order of the sorted ROI integer
%               codes, the order of the volumes to be used as ROI masks, or the
%               order specified in the 'rois' parameter.
%               See Notes section for details.
%           - standardize : no ('no' / 'within' / 'across')
%               Whether and how to standardize ROI weights:
%               - no     :  do not change the weights
%               - within :  standardize the weights to the sum of 1 within 
%                           each ROI independently
%               - across :  standardize the weight to the sum of 1 across 
%                           all weights for all ROI    
%           - threshold : one or two comma separated numbers
%               A threshold to be used when creating ROI from scalar maps.
%               A positive number indicates that only values equal or higher 
%               than the provided threshold are to be used. A negative 
%               number indicates that only values equal or lower than the
%               provided threshold are to be used. If both positive and
%               negative threshold are provided then both the values equal
%               and higher to the positive threshold and the values equal
%               od lower than the negative threshold will be used.
%           - target : a string
%               The target image format. The value should be one of the
%               following: 'CIFTI', 'MNI2', 'MNI1', or a path to a volume
%               image file. The default is 'CIFTI'.
%               This is a necessary parameter when creating a new ROI file based 
%               on a provided ROI file. 
%           - limit_roi : yes ('no' / 'yes')
%               When creating ROI based on an .roi file for a cifti image, 
%               Whether to limit the ROI to the structure of the ROI center e.g. 
%               limit the ROI to thalamus only or to allow the ROI to spread 
%               across multiple structures, e.g., thalamus and pallidum.   
%           - surface_roi : closest_sphere_sphere ('absolute_sphere', 'closest_sphere_midthickness', 'closest_sphere_sphere')
%               How to define the ROI on the surface. The options are:  
%               - absolute_sphere : 
%                       include in the ROI all the vertices within the sphere
%                       defined by the provided coordinates and radius
%               - closest_sphere_midthickness : 
%                       include in the ROI all the vertices within the sphere
%                       defined by the location of the vertice closest to the 
%                       provided coordinate, and the radius, computed on the 
%                       midthickness surface representation.
%               - closest_sphere_sphere : 
%                       include in the ROI all the vertices within the sphere
%                       defined by the location of the vertice closest to the
%                       provided coordinate, and the radius, computed on the
%                       spherical surface representation.
%
%   Output:
%
%       img
%           A nimage object with an `roi` structure array defining the ROI. 
%           The structure has the following fields:
%       
%           roiname   - the name of the ROI
%           roicode   - the integer code for the ROI, its index in the array
%           roicodes1 - an array of codes used to define the primary ROI as
%                       provided in the '.names' file, the original integer
%                       code in a label or volume image file, or the index
%                       of the original map with the ROI mask
%           roicodes2 - an array of codes used to mask the primary ROI as
%                       provided in the '.names' file
%           map       - in case of 'label' or 'scalar' CIFTI files in which
%                       multiple ROI were defined in a single volume, the 
%                       name of the map in which the ROI was defined, 
%                       otherwise the name of the file
%           indeces   - a vector of indeces of voxels/grayordinates in the 
%                       2D representation of the image
%           weights   - a vector of weights matching the indeces
%           nvox      - number of voxels in ROI
%
%   Notes:
%       The method is used to generate an ROI object, which holds information on 
%       ROIs that can be used to process other images. The decoding of ROIs 
%       depends on the specific input and provided options.
%
%       Names file:
%           If a '.names' file is provided (see specification below), then ROIs 
%           will be created based on the specification provided in the .names 
%           file. In this case, masking of the original image is also supported 
%           in which the original image (usually a group ROI file) is masked 
%           with the second ROI image (usually a subject specific segmentation
%           file.).
%
%           If no file is specified as the second ROI, then no masking is 
%           performed. If a second file exists, it will be used to mask the 
%           original data based on the specified values in the third column of 
%           the .names file. 
%
%           The function supports the specification of region codes in the 
%           .names file using either numeric vaues (e.g. 3,8,9) or names. The 
%           names are based on aseg+aparc segmentation. They are:
%
%           - lcgray  (left cortex gray matter)
%           - rcgray  (right cortex gray matter)
%           - cgray   (cortical gray matter)
%           - lsubc   (left subcortical gray matter)
%           - rsubc   (right subcortical gray matter)
%           - subc    (subcortical gray matter)
%           - lcerc   (left cerebellar gray matter)
%           - rcerc   (right cerelebbar gray matter)
%           - cerc    (cereberal gray matter)
%           - lgray   (left hemisphere gray matter)
%           - rgray   (right hemisphere gray matter)
%           - gray    (whole brain gray matter)
%
%           The use of the names assumes that the second image, specified in 
%           the `mask` parameter uses integer codes as defined for the 
%           freesurfer aseg+aparc segmentation. 
%
%       ROI file:
%           If an '.roi' file is provided (see specification below), then ROIs
%           will be created based on the specification provided in the .roi
%           file. In this case, masking of the original image is also supported
%           in which the created ROI are masked with a mask provided in an image
%           file. In this case the mask has to be either a path to the image file
%           or an nimage object. The generated ROI will only be defined for the 
%           voxels/grayordinates with non-zero values in the mask.
%
%           Take note of the following:
%           - If ROI overlap, each ROI will include all the voxels/grayordinates
%             that are part of the ROI. To avoid the overlap of the image masks
%             each ROI will be represented in a separate volume. In a dlabel 
%             file each ROI will be represented in a separate map.
%           - If the ROI are assigned the same value, they will still be 
%             represented as separate ROIs in the ROI structure, however, if 
%             there is no overlap between any ROI, they will be merged into a 
%             single ROI in the image. In the case of overlap, each ROI will be
%             represented in a separate volume.   
%
%       CIFTI label image:
%           If a path to a CIFTI label image or a nimage object with a label
%           image is provided then the labels defined in the file will be used
%           to specify ROIs. If the file have multiple maps/volumes, then only
%           the maps with the names or indeces provided will be used. If no
%           maps or indeces are specified, then ROIs from all the maps will
%           be used.
%
%       CIFTI parcelated image:
%           If a CIFTI parcelated image is provided, then the information on 
%           parcels in the image will be extracted and used to define ROIs.
%           The ROIs will be adjusted to match a full, 'standard' dense CIFTI 
%           image. If maps or rois options are specified then only the parcels
%           matching them will be retained as ROIs.
%
%       CIFTI dense or volume image:
%           If dense CIFTI image or a volume image is provided, the result 
%           depends on the number of volumes in the image or the number of
%           volumes specified to be retained by the optional volumes or maps
%           parameter.
%
%           One volume with integer values:
%               All the unique integer values in the volume will be used to 
%               specify ROIs. If roinames optional parameter is provided, the
%               ROIs will be named as specified.
%
%           One or more volumes with scalar (non-integer) values:
%               Each volume will be used to define an ROI. The extent of the
%               ROI will be defined by all non-zero values in the map. If
%               an optional threshold or thresholds are provided, then they
%               will be applied before ROI is defined. The scalar values will 
%               be stored as weights. If the optional `roinames` parameter is
%               provided, the ROI will be named as specified. If the file is
%               a CIFTI scalar with named maps, then the map names will be 
%               used to name ROI. `roinames` has priority.
%
%           One or more volumes with binary values:
%               Each volume will be used as a mas to define an ROI. If the 
%               optional `roinames` parameter is provided, the ROI will be 
%               named as specified. If the file is a CIFTI scalar with 
%               named maps, then the map names will be used to name ROI. 
%               `roinames` has priority.
%
%           Two volumes, first with integers and the second with scalars:
%               The first volume will be used to define ROIs, each integer
%               code will be used as a mask for an ROI. The second volume
%               will be used to define the weights for the ROIs. If the 
%               optional `roinames` parameter is provided, the ROI will be 
%               named as specified.
%               
%       Specification of optional parameters:
%           Optional parameters can be specified in three ways. First, as
%           <key>:<value> pairs in the `options` parameter. Second, as <key>:
%           <value> pairs following the path provided in the `roi` parameter. 
%           Finally, as the content of the `mask` parameter. In the last case
%           comma separated string will be treated as options -> maps, whereas
%           a numeric array will be treated as options -> volumes. The priority 
%           will be in the order: `mask`, `roi`, `options` with `mask` having 
%           the highest priority.       
%
%       Names file specification:
%           Names file is a regular text file with .names ending. It specifies
%           how to generate a ROI structure. It has the following example form:
%
%           /path-to-resources/CCN_ROI.nii.gz
%           RDLPFC|1|rcgray
%           LDLPFC|2|lcgray
%           ACC|3,4|cgray
%
%           This file specifies three cognitive cotrol regions. The original 
%           ROI file is referenced by the first line of the .names file. If the 
%           path starts with a forward slash ('/'), it is assumed to be an 
%           absolute path, otherwise it is assumed to be a path relative to the 
%           location of the roiinfo '.names' file. If the line is empty or 
%           references "none", it is assumed that all the ROI are defined by the 
%           roi2 codes only.
%
%           The following lines specify the ROI to be generated with a pipe (|)
%           separated columns. The first column specifies the name of the ROI. 
%           The second column specifies the integer codes that represent the 
%           desired region. There can be more than one code used and the ROI 
%           will be a union of all the specified, comma separated codes. The 
%           third column specifies the codes to be used to mask the ROI 
%           generated from the original file. If either the third or the second 
%           column is empty, the specified ROI from the original or secondary 
%           image file will be used. Again, If the first line is empty or set
%           to 'none', only the third column will be used to generate ROI.
%
%       ROI file specification:
%           ROI file is a regular text file with .roi ending. It specifies how 
%           to create spheric (or circular on surface) ROI. The ROI should be 
%           specified one per line with the following information separated by 
%           whitespace:
%
%           <ROI name> <x coordinate> <y coordinate> <z coordinate> <radius> <value>
%
%           The file should start with the line:
%
%           # ROI specification
%
%           Any following empty line or line that starts with # is ignored.
%           Example:
%
%           # ROI specification
%           # ROI    x  y  z r v
%           LDLPFC -40 40 30 3 1
%           RDLPFC  40 40 30 3 1
%           LIFG   -45 25 10 3 3
%           RIFG    45 25 10 3 1
%           LACC    -5 40  5 3 1
%           RACC     5 40  5 3 1
%
%
%
%   Examples:
%       To create a group level roi file::
%
%           roi = nimage.img_prep_roi('resources/CCN.names')
%
%       To create a subject specific file::
%
%           roi = nimage.img_prep_roi('resources/CCN.names', 'AP3345.aseg+aparc.nii.gz')
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

%   ---- Named region codes

rcodes.lcgray = [3 415 417 419 421:422 424 427 429 431 433 435 438 1000:1035 1100:1104 1200:1202 1205:1207 1210:1212 1105:1181 9000:9006 11100:11175];
rcodes.rcgray = [42 416 418 420 423 425:426 428 430 432 434 436 439 2000:2035 2100:2104 2105:2181 2200:2202 2205:2207 2210:2212 9500:9506 12100:12175 ];
rcodes.cgray  = [rcodes.lcgray rcodes.rcgray 220 222 225 226 400:414 437 ];

rcodes.lsubc  = [9:13 17:20 26:28 96 136 163 169 193:196 550 552:557];
rcodes.rsubc  = [48:56 58:60 97 137 164 176 197:200 500 502:507];
rcodes.subc   = [rcodes.lsubc rcodes.rsubc 16 170:175 203:209 212 214:218 226 7001:7020 7100:7101 8001:8014 ];

rcodes.lcerc  = [8 601 603 605 608 611 614 617 620 623 626 660:679];
rcodes.rcerc  = [47 602 604 607 610 613 616 619 622 625 628 640:659];
rcodes.cerc   = [rcodes.lcerc rcodes.rcerc 606 609 612 615 618 621 624 627];

rcodes.lgray  = [rcodes.lcgray rcodes.lsubc rcodes.lcerc];
rcodes.rgray  = [rcodes.rcgray rcodes.rsubc rcodes.rcerc];
rcodes.gray   = [rcodes.cgray rcodes.subc rcodes.cerc 702];

% rcodes.lcgray = [3 415 417 419 421:422 424 427 429 431 433 435 438 11100:11175 1000:1035 1100:1104 1200:1202 1205:1207 1210:1212 1105:1181];
% rcodes.rcgray = [42 416 418 420 423 425:426 428 430 432 434 436 439 12100:12175 2000:2035 2100:2104 2105:2181 2200:2202 2205:2207 2210:2212];
% rcodes.cgray  = [rcodes.lcgray rcodes.rcgray 220 222 225 400:414 437];
%
% rcodes.lsubc  = [9:13 17:20 26 27 96 193 195:196 9000:9006 550 552:557];
% rcodes.rsubc  = [48:56 58:59 97 197 199:200 9500:9506 500 502:507];
% rcodes.subc   = [rcodes.lsubc rcodes.rsubc 16 170:175 203:209 212 214:218 226 7001:7020 7100:7101 8001:8014];
%
% rcodes.lcerc  = [8 601 603 605 608 611 614 617 620 623 626 660:679];
% rcodes.rcerc  = [47 602 604 607 610 613 616 619 622 625 628 640:659];
% rcodes.cerc   = [rcodes.lcerc rcodes.rcerc 606 609 612 615 618 621 624 627];
%
% rcodes.lgray  = [rcodes.lcgray rcodes.lsubc rcodes.lcerc];
% rcodes.rgray  = [rcodes.rcgray rcodes.rsubc rcodes.rcerc];
% rcodes.gray   = [rcodes.cgray rcodes.subc rcodes.cerc];


% ---> process input

if nargin < 1, error('\nERROR: img_prep_roi: At least one input variable has to be provided!\n'); end
if nargin < 2, mask    = []; end
if nargin < 3, options = []; end

img = [];

% ---> process options

default = 'check:warning|volumes:|maps:|rois:|roinames:|standardize:no|threshold:|target:CIFTI|limit_roi:yes|surface_roi:closest_sphere_sphere';
options = general_parse_options([], options, default);

% ---> are there options in roi variable

if ischar(roi) && ~isempty(strfind(roi, '|'))
    [roi, noptions] = strtok(roi, '|');
    roi = strtrim(roi);
    noptions = noptions(2:end);
    options = general_parse_options(options, noptions);
end

% ---> check options and expand the relevant ones to lists

if ~isempty(options.volumes)
    if ischar(options.volumes)
        try
            options.volumes = str2double(strsplit(options.volumes, ','));
        catch
            error('\nERROR: Invalid list of volumes provided to img_prep_roi: %s!', options.volumes);
        end
    end
end

if ~isempty(options.maps)
    options.maps = strtrim(strsplit(options.maps, ','));
end

if ~isempty(options.rois)
    t = str2num(options.rois);
    if isempty(t)
        options.rois = strtrim(strsplit(options.rois, ','));
    else
        options.rois = t;
    end
end

if ~isempty(options.roinames)
    options.roinames = strtrim(strsplit(options.roinames, ','));
end

if ~isempty(options.threshold)
    if ischar(options.threshold)
        try
            options.threshold = str2double(strsplit(options.threshold, ','));
        catch
            error('\nERROR: Invalid thresholds provided to img_prep_roi: %s!', options.threshold);
        end
    end
    if length(options.threshold) > 2 || any(isnan(options.threshold))
        error('\nERROR: Invalid threshold(s) provided to img_prep_rois! [%s]', num2str(options.threshold));
    end
    if (length(options.threshold) == 2) && sum(sign(options.threshold)) ~= 0
        error('\nERROR: Invalid threshold(s) provided to img_prep_rois - both are of the same sign! [%s]', num2str(options.threshold));
    end
    options.threshold = sort(options.threshold, 'descend');
end

if isempty(options.check) || ~any(strcmpi(options.check, {'warning', 'ignore', 'error'}))
    error('\nERROR: Invalid check option provided to img_prep_roi: %s!', options.check);
end

if isempty(options.standardize) || ~any(strcmpi(options.standardize, {'no', 'within', 'across'}))
    error('\nERROR: Invalid standardize option provided to img_prep_roi: %s!', options.standardize);
end

% ---> check content of mask variable

if ~isempty(mask)
    if ischar(mask)
        file_info = general_check_image_file(mask);
        if file_info.is_image && file_info.exists
            mask = nimage(mask);
        elseif file_info.is_image && ~file_info.exists
            error('\nERROR: Provided mask image file does not exist [%s]. Check your paths!\n', mask);
        elseif file_info.exists && ~file_info.is_image
            error('\nERROR: The provided mask file is not a valid image file [%s]!\n', mask);
        else
            options.maps = strtrim(strsplit(mask, ','));
            mask = [];
        end
    elseif isnumeric(mask)
        options.volumes = mask;
        mask = [];
    elseif ~isa(mask, 'nimage')
        error('\nERROR: Invalid value provided for mask parameter to img_prep_roi!\n');
    end
end

% ---> process ROI

if isa(roi, 'char')

    if ends_with(roi, '.names')
        img = process_names(roi, mask, options, rcodes);
    elseif ends_with(roi, '.roi')
        img = process_roi(roi, mask, options, rcodes);
    else 
        file_info = general_check_image_file(roi);

        if file_info.is_image && file_info.exists
            roi = nimage(roi);
        elseif ~file_info.is_image
            error('\nERROR: The provided roi file is not a valid image file [%s]!\n', roi);
        elseif ~file_info.exists
            error('\nERROR: Provided roi image file does not exist [%s]. Check your paths!\n', roi);
        end
    end

elseif ~isa(roi, 'nimage')    
    error('\nERROR: Invalid value provided for roi parameter to img_prep_roi!\n');    
elseif isfield(roi.roi, 'roinames')
    img = process_old_roi(roi);
elseif isfield(roi.roi, 'roiname') && ~isempty({roi.roi.roiname})
    img = roi;
end

if isempty(img)
    if strcmpi(roi.filetype , 'dlabel')
        img = process_label(roi, options);

    elseif any(strcmpi(roi.filetype, {'ptseries', 'pscalar'}))
        img = process_parcel(roi, options);

    elseif any(strcmpi(roi.filetype, {'dscalar', 'dtseries', 'NIfTI'}))
        img = process_mask(roi, options);

    else
        error('\nERROR: The specified ROI is not of known type that could be processed as a region file.');

    end
end

% ---> select ROI

if ~isempty(options.rois)
    if isnumeric(options.rois)
        [~, keep_roi] = ismember(options.rois, [1:length(img.roi)]);
    else
        [~, keep_roi] = ismember(options.rois, {img.roi.roiname});
    end
    img.roi = img.roi(keep_roi);

    if img.frames > 1
        img = img.selectframes(keep_roi);
    end
    
    if isempty(img.roi)
        error('\nERROR: In img_prep_roi no ROI present after processing and selection of ROI.');
    end
end

% ---> name ROI
if ~isempty(options.roinames) 
    if length(options.roinames) ~= length(img.roi)
        error('\nERROR: In img_prep_roi number of identified ROIs [%d] does not match the number of provided ROI names [%d]!', length(img.roi), length(options.roinames));
    end
    for r = 1:length(img.roi)
        img.roi(r).roiname = options.roinames{r};
    end
end

% ---> standardize weights

if ~isempty(img.roi(1).weights)
    if strcmpi(options.standardize, 'within')
        for r = 1:length(img.roi)
            img.roi(r).weights = img.roi(r).weights ./ sum(img.roi(r).weights);
        end
    elseif strcmpi(options.standardize, 'across')
        scale_by = 1 / sum(vertcat(img.roi.weights));
        for r = 1:length(img.roi)
            img.roi(r).weights = img.roi(r).weights .* scale_by;
        end
    end
end

% ---> prepare metadata for cifti

if strcmp(img.imageformat, 'CIFTI-2')
    if img.frames == 1
        img.cifti.maps{1} = 'ROI';
        labels = struct('name', '???', 'key', 0, 'rgba', [0; 0; 0; 0]);
        f = 1;
        colors = jet(length(img.roi));
        for r = 1:length(img.roi)
            labels(f).name = img.roi(r).roiname;
            labels(f).key  = img.roi(r).roicode;
            labels(f).rgba = [colors(r, :) 0.7]';
            f = f + 1;
        end
        img.cifti.labels{1} = labels;
    else
        colors = jet(length(img.roi));
        for r = 1:length(img.roi)
            img.cifti.maps{r} = img.roi(r).roiname;
            labels = struct('name', '???', 'key', 0, 'rgba', [0; 0; 0; 0]);
            labels(2) = struct('name', img.roi(r).roiname, 'key', img.roi(r).roicode, 'rgba', [colors(r, :) 0.7]');
            img.cifti.labels{r} = labels;
        end
    end
end


% ============================================================================================
%                                                                            Support functions

% --------------------------------------------------------------------------------------------
%                                                                                process_names

function [img] = process_names(names_filename, mask, options, rcodes)
    
    % ---> process information from the .names file

    [names_path, map_name, ~] = fileparts(names_filename);

    names_file   = fopen(names_filename);
    roi_filename = fgetl(names_file);

    if strcmp('none', roi_filename) || isempty(roi_filename)
        roi = [];
    else
        file_info = general_check_image_file(roi_filename);
        if ~file_info.exists
            file_info = general_check_image_file(fullfile(names_path, roi_filename));
        end

        if file_info.is_image && file_info.exists
            roi = nimage(file_info.filename);
        elseif ~file_info.is_image
            error('\nERROR: The roi file [%s] specified in the .names file [%s] is not a valid image file!\n', file_info.filename, names_filename);
        elseif ~file_info.exists
            error('\nERROR: The roi file [%s] specified in the .names file [%s] does not exist! Check your paths!\n', file_info.filename, names_filename);
        end
    end

    c = 0;

    while feof(names_file) == 0
        line = fgetl(names_file);

        if length(line) < 3 || line(1) == '#'
            continue
        end

        c = c + 1;

        relements = regexp(line, '\|', 'split');

        if length(relements) == 3
            roinames{c} = relements{1};
            roicodes1{c} = getCodes(relements{2}, rcodes);
            roicodes2{c} = getCodes(relements{3}, rcodes);
        else
            fprintf('\n WARNING: Not all fields present in ROI definition: ''%s'' skipping ROI.', line);
        end

    end

    nroi = c;
    fclose(names_file);

    % ---> set final ROI image

    if isempty(roi) && isempty(mask)
        error('\nERROR: In img_prep_roi at least a primary ROI file or a mask has to be provided!\n');
    elseif isempty(roi)
        img = mask.zeroframes(nroi);
    else
        img = roi.zeroframes(nroi);
    end

    % ---> Check whether ROI codes from .names file exist in images

    if isa(roi, 'nimage')
        for i = 1:length(roicodes1)
            for j = 1:length(roicodes1{i})
                if ~any(roi.data == roicodes1{i}(j))
                    switch lower(options.check)
                        case 'warning'
                            warning('\nWARNING: img_prep_roi – code [%d] does not exist in primary roi file [%s]!\n', roicodes1{i}(j), roi.filename);
                        case 'error'
                            error('\nERROR: img_prep_roi - code [%d] does not exist in primary roi file %s!\n', roicodes1{i}(j), roi.filename);
                    end
                end
            end
        end
    end

    if isa(mask, 'nimage')
        for i = 1:length(roicodes2)
            for j = 1:length(roicodes2{i})
                if ~any(mask.data == roicodes2{i}(j))
                    switch lower(options.check)
                        case 'warning'
                            warning('\nWARNING: img_prep_roi – code [%d] does not exist in mask roi file [%s]!\n', roicodes2{i}(j), mask.filename);
                        case 'error'
                            error('\nERROR: img_prep_roi - code [%d] does not exist in mask roi file %s!\n', roicodes2{i}(j), mask.filename);
                    end
                end
            end
        end
    end

    % ---> Process ROI

    for n = 1:nroi

        img.roi(n).roiname   = roinames{n};
        img.roi(n).roicode   = n;
        img.roi(n).roicodes1 = roicodes1{n};
        img.roi(n).roicodes2 = roicodes2{n};
        img.roi(n).map       = map_name;        

        if ((length(roicodes1{n}) == 0 || isempty(roi)) & (~isempty(mask)))
            img.roi(n).indeces = get_roi_for_codes(mask, roicodes2{n});
        elseif ((length(roicodes2{n}) == 0 || isempty(mask)) & (~isempty(roi)))
            img.roi(n).indeces = get_roi_for_codes(roi, roicodes1{n});
        elseif ((~isempty(mask)) & (~isempty(roi)));
            img.roi(n).indeces = intersect(get_roi_for_codes(roi, roicodes1{n}), get_roi_for_codes(mask, roicodes2{n}));
        else
            img.roi(n).indeces = [];
        end

        img.roi(n).weights = [];
        img.roi(n).nvox = length(img.roi(n).indeces);
        img.data(img.roi(n).indeces,n) = n;

    end

    % ---> Collapse volumes if possible

    if max(sum(img.data > 0, 2)) == 1
        img.data(:,1) = sum(img.data, 2);
        img = img.selectframes(1);
    end

% --------------------------------------------------------------------------------------------
%                                                                                process_label

function [roi] = process_label(roi, options)
    
    roi.data = roi.image2D;

    % ---> check options

    if ~isempty(options.volumes)
        roi = roi.selectframes(options.volumes);
    elseif ~isempty(options.maps)
        roi = roi.sliceframes(ismember(roi.cifti.maps, options.maps));
    end

    if roi.frames == 0;
        error('ERROR: In img_prep_roi there are no volumes/maps left to define ROI. Please check your ROI file and options!');
    end

    % ---> process and check for overlapping labels
    c = 0;
    labels = {};
    overlap = {};
    for m = 1:roi.frames
        keys = unique(roi.data(:,m));
        keys = keys(keys > 0);
        lnew = {roi.cifti.labels{m}(ismember([roi.cifti.labels{m}.key], keys)).name};
        if m > 1
            overlap = [overlap intersect(labels, lnew)];
        end
        labels = unique([labels, lnew]);

        map_name = roi.cifti.maps{m};
        for key = keys(:)'
            c = c + 1;
            if ~isempty(options.roinames)
                roi.roi(c).roiname = options.roinames{c};
            else
                roi.roi(c).roiname = roi.cifti.labels{m}([roi.cifti.labels{m}.key] == key).name;
            end
            roi.roi(c).roicode   = c;
            roi.roi(c).roicodes1 = {key};
            roi.roi(c).roicodes2 = {};
            roi.roi(c).map       = map_name;
            roi.roi(c).indeces   = find(roi.data(:,m) == key);
            roi.roi(c).weights   = [];
            roi.roi(c).nvox      = length(roi.roi(c).indeces);
        end
    end

% --------------------------------------------------------------------------------------------
%                                                                                process_parcel

function [img] = process_parcel(roi, options)

    roi = roi.selectframes(1);
    nparcels = length(roi.cifti.parcels);
    roi.data = [1:nparcels]';

    error('ERROR: Processing parcel images is not yet implemented!');

    img = nimage('dscalar:1');

    for p = 1:length(roi.cifti.parcels)
        
        % ---> set basic info
        img.roi(p).roiname   = roi.cifti.metadata.diminfo{1}.parcels(p).name;
        img.roi(p).roicode   = p;
        img.roi(p).roicodes1 = {p};
        img.roi(p).roicodes2 = {};
        img.roi(p).map       = roi.rootfilename;
        img.roi(p).indeces   = [];
        img.roi(p).weights   = [];

        nmodels = length(img.cifti.metadata.diminfo{1}.models);

        % ---> process surfs
        for s = 1:length(roi.cifti.metadata.diminfo{1}.parcels(p).surfs)
            sname    = roi.cifti.metadata.diminfo{1}.parcels(p).surfs(s).struct;
            sindeces = roi.cifti.metadata.diminfo{1}.parcels(p).surfs(s).vertlist;
            for tm = 1:nmodels
                if strcmpi(sname, img.cifti.metadata.diminfo{1}.models{tm}.struct)
                    img.roi(p).indeces = [img.roi(p).indeces sindeces + img.cifti.metadata.diminfo{1}.models{tm}.start];                    
                end
            end
        end
        % ---> process vols

        img.data(img.roi(p).indeces) = p;
    end



% --------------------------------------------------------------------------------------------
%                                                                                 process_mask

function [roi] = process_mask(roi, options)

    roi.data = roi.image2D;

    % ---> filter volumes if specified

    if ~isempty(options.volumes)
        roi = roi.selectframes(options.volumes);
    elseif ~isempty(options.maps) && strcmpi(roi.filetype, 'dscalar')
        roi = roi.sliceframes(ismember(roi.cifti.maps, options.maps));
    end

    % ---> check type of volumes
    
    nozeros = double(roi.data);
    nozeros(nozeros == 0) = NaN;
    is_binary  = var(nozeros, 'omitnan') == 0;
    is_scalar  = sum(roi.data - floor(roi.data)) ~= 0;
    is_integer = (is_binary + is_scalar) == 0;
    
    % ---> scalar and binary images

    if ~any(is_integer)

        % ---> threshold scalar maps

        if ~isempty(options.threshold)
            for f = 1:roi.frames
                if is_scalar(f)
                    if length(options.threshold) == 2
                        roi.data(roi.data(:, f) < options.threshold(1) & roi.data(:, f) > options.threshold(2), f) = 0;
                    else
                        if options.threshold > 0
                            roi.data(roi.data(:,f) < options.threshold, f) = 0;
                        else
                            roi.data(roi.data(:,f) > options.threshold, f) = 0;
                        end
                    end
                end
            end
        end

        % ---> check for empty maps

        empty = sum(roi.data) == 0;
        if any(empty)
            if isempty(roi.cifti.maps)
                empty_volumes = [1:roi.frames];
                empty_volumes = ['volumes: [' num2str(empty_volumes(empty)) ']'];
            else
                empty_volumes = ['maps: [' strjoin(roi.cifti.maps(empty), ', '), ']'];
            end
            fprintf('\nWARNING: In img_prep_roi the following %s are without ROI!', empty_volumes);
        end

        % ---> identify ROIs

        for f = 1:roi.frames
            if isfield(roi.cifti, 'maps') && ~isempty(roi.cifti.maps)
                roi.roi(f).roiname = roi.cifti.maps{f};                
            else
                if roi.frames < 10
                    roi.roi(f).roiname = sprintf('ROI_%d', f);
                elseif roi.frames < 100
                    roi.roi(f).roiname = sprintf('ROI_%02d', f);
                elseif roi.frames < 1000
                    roi.roi(f).roiname = sprintf('ROI_%03d', f);
                else
                    roi.roi(f).roiname = sprintf('ROI_%04d', f);
                end
            end

            roi.roi(f).roicode   = f;
            roi.roi(f).roicodes1 = {f};
            roi.roi(f).roicodes2 = {};
            roi.roi(f).map       = roi.rootfilename;
            roi.roi(f).indeces   = find(roi.data(:,f) ~= 0);
            if is_binary(f)                
                roi.roi(f).weights = [];
            else                
                roi.roi(f).weights = roi.data(roi.roi(f).indeces, f);
            end            
            roi.roi(f).nvox = length(roi.roi(f).indeces);
        end
    
    elseif all(is_integer) || (any(is_integer) && ~any(is_scalar))

        % ---> identify unique

        unique_in_frame = {};
        nunique_in_frame = [];
        for f = 1:roi.frames
            unique_in_frame{f} = unique(roi.data(:,f));
            unique_in_frame{f} = unique_in_frame{f}(unique_in_frame{f} ~= 0);
            nunique_in_frame = length(unique_in_frame{f});
        end
        nunique_all = sum(nunique_in_frame);
        
        % ---> process ROIs

        c = 0;
        for f = 1:roi.frames
            keys = unique_in_frame{f};
            for key = keys(:)'
                c = c + 1;

                if nunique_all < 10
                    roi.roi(c).roiname = sprintf('ROI_%d', c);
                elseif nunique_all < 100
                    roi.roi(c).roiname = sprintf('ROI_%02d', c);
                elseif nunique_all < 1000
                    roi.roi(c).roiname = sprintf('ROI_%03d', c);
                else
                    roi.roi(c).roiname = sprintf('ROI_%04d', c);
                end

                roi.roi(c).roicode   = c;
                roi.roi(c).roicodes1 = {key};
                roi.roi(c).roicodes2 = {};
                
                if strcmpi(roi.filetype, 'dscalar')
                    roi.roi(c).map = roi.cifti.maps{f};
                else
                    roi.roi(c).map = roi.rootfilename;
                    if roi.frames > 1
                        roi.roi(c).map = [roi.roi(c).map sprintf('-map_%d', f)];
                    end
                end

                roi.roi(c).indeces = find(roi.data(:,f) == key);
                roi.roi(c).weights = [];
                roi.roi(c).nvox = length(roi.roi(c).indeces);
            end
        end

    elseif roi.frames == 2 && is_integer(1) && is_scalar(2)

        keys = unique(roi.data(:,1));
        keys = keys(keys ~= 0);
        nkeys = length(keys);
        
        c = 0;
        for key = keys(:)'
            c = c + 1;

            if nkeys < 10
                roi.roi(c).roiname = sprintf('ROI_%d', c);
            elseif nkeys < 100
                roi.roi(c).roiname = sprintf('ROI_%02d', c);
            elseif nkeys < 1000
                roi.roi(c).roiname = sprintf('ROI_%03d', c);
            else
                roi.roi(c).roiname = sprintf('ROI_%04d', c);
            end

            roi.roi(c).roicode = c;
            roi.roi(c).roicodes1 = {key};
            roi.roi(c).roicodes2 = {};

            if strcmpi(roi.filetype, 'dscalar')
                roi.roi(c).map = roi.cifti.maps{1};
            else
                roi.roi(c).map = roi.rootfilename;
            end

            roi.roi(c).indeces = find(roi.data(:,1) == key);
            roi.roi(c).weights = roi.data(roi.roi(c).indeces,2);
            roi.roi(c).nvox    = length(roi.roi(c).indeces);
        end
    else 
        error('\nERROR: In img_prep_roi could not deduce how to process ROIs. Please review inline help! [%s]', roi.filename);
    end


% --------------------------------------------------------------------------------------------
%                                                                                     getCodes

function [codes] = getCodes(s, rcodes)

    codes = [];
    s = strtrim(regexp(s, ',', 'split'));
    for n = 1:length(s)
        if ~isempty(s{n})
            if min(isstrprop(s{n}, 'digit'))
                codes = [codes str2num(s{n})];
            elseif isfield(rcodes, s{n})
                codes = [codes rcodes.(s{n})];
            else
                fprintf('\n WARNING: Ignoring unknown region code name: ''%s''!', s{n});
            end
        end
    end

% --------------------------------------------------------------------------------------------
%                                                                            get_roi_for_codes

function [indeces, weights] = get_roi_for_codes(img, roi)
    %
    %   Returns indeces and optionaly weights from img that match roi.
    %   
    %   Parameters:
    %       img - a nimage object with roi codes and one or two volumes
    %       roi - an array of roi codes
    %
    %   Output:
    %       indeces - a list of indeces that belong to ROI
    %       weights - a list of weights associated with ROI

    img.data = img.image2D;
    weights = [];

    if nargin < 2 || isempty(roi)
        if isa(img.data, 'logical')
            indeces = find(img.data(:,1));
            return
        else
            indeces = find(img.data(:,1) > 0);            
        end
    else
        indeces = find(ismember(img.data(:,1), roi));
    end
    if img.frames > 1
        weights = img.data(indeces, 2);
    end

% --------------------------------------------------------------------------------------------
%                                                                              process_old_roi

function [roi] = process_old_roi(roi, options)

    roi.data = roi.image2D;
    oldroi = roi.roi;
    roi.roi = [];
    nroi = length(oldroi.roinames)

    for r = 1:nroi
        roi.roi(r).roiname   = oldroi.roinames{r};
        roi.roi(r).roicode   = r;
        roi.roi(r).roicodes1 = oldroi.roicodes1{r};
        roi.roi(r).roicodes2 = oldroi.roicodes2{r};
        roi.roi(r).nvox      = oldroi.nvox(r);
        roi.roi(r).weights   = [];
        roi.roi(r).map       = oldroi.roifile1;

        if roi.frames > 1
            v = r;
        else
            v = 1;
        end

        roi.roi(r).indeces   = find(roi.data(:, v) == r);
    end



% --------------------------------------------------------------------------------------------
%                                                                                  process_roi

function [roi] = process_roi(roi, mask, options, rcodes)

    roi_list = read_roi_spec(roi);
    mpath = mfilename('fullpath');
    [mpath, ~, ~] = fileparts(mpath);
    mpath = strsplit(mpath, filesep);
    lpath = fullfile(strjoin(mpath(1:end-4), filesep), 'qx_library', 'data', 'atlases', 'mni_templates');

    switch options.target
        case 'CIFTI'
            image_type = 'cifti';
            bm = load('cifti_brainmodel');
            roi = nimage('dscalar:1');
        case 'MNI2'
            image_type = 'volume';
            roi = nimage(fullfile(lpath, 'MNI152_T1_2mm_brain.nii.gz'));
        case 'MNI1'
            image_type = 'volume';
            roi = nimage(fullfile(lpath, 'MNI152_T1_1mm_brain.nii.gz'));
        otherwise            
            roi = nimage(options.target);
            if strcmp(roi.filetype, 'NIfTI')
                image_type = 'volume';
            else
                image_type = 'cifti';                
            end           
    end

    if strcmp(image_type, 'volume')
        roi = process_roi_volume(roi_list, roi, mask, options, rcodes);
    else
        roi = process_roi_cifti(roi_list, roi, mask, options, rcodes, bm);
    end


function [roi] = process_roi_cifti(roi_list, template, mask, options, rcodes, bm)

    roi = template.zeroframes(length(roi_list));

    % compute distances
    distances = pdist2(bm.mapping.mni, horzcat([roi_list.x]', [roi_list.y]', [roi_list.z]'));
    [min_d, min_i] = min(distances);
    min_s_type = bm.mapping.structure_type(min_i);
    min_s_id   = bm.mapping.structure_id(min_i);

    % identify target structure
    for r = 1:length(roi_list)
        
        % volume targets
        if bm.mapping.structure_type(min_i(r)) == 3
            if strcmp(options.limit_roi, 'yes')
                roi.data(distances(:, r) <= roi_list(r).radius & bm.mapping.structure_id == min_s_id(r), r) = roi_list(r).value;
            else
                roi.data(distances(:, r) <= roi_list(r).radius & bm.mapping.structure_type == 3, r) = roi_list(r).value;
            end
        
        % surface targets
        else
            switch options.surface_roi
                case 'absolute_sphere'
                    roi.data(distances(:, r) <= roi_list(r).radius & bm.mapping.structure_id == min_s_id(r), r) = roi_list(r).value;
                
                case 'closest_sphere_midthickness'
                    closest_xyz = bm.mapping.mni(min_i(r), :);
                    new_distances = pdist2(bm.mapping.mni, closest_xyz);
                    roi.data(new_distances <= roi_list(r).radius & bm.mapping.structure_id == min_s_id(r), r) = roi_list(r).value;

                case 'closest_sphere_sphere'
                    shortname = bm.cifti.shortnames{min_s_id(r)};
                    closest_xyz = bm.mapping.mni_sphere(min_i(r), :);
                    % new_distances = pdist2(bm.cifti.(shortname).sphere.vertices(bm.cifti.(shortname).indices + 1, :), closest_xyz);
                    %mask = zeros(size(new_distances));
                    %mask(new_distances <= roi_list(r).radius) = roi_list(r).value;
                    %roi.data(bm.mapping.structure_id == min_s_id(r), r) = mask;
                    new_distances = pdist2(bm.mapping.mni_sphere, closest_xyz);
                    roi.data(new_distances <= roi_list(r).radius & bm.mapping.structure_id == min_s_id(r), r) = roi_list(r).value;

                otherwise
                    error('ERROR: Unknown surface_roi option provided to img_prep_roi: %s!', options.surface_roi);
            end
            
        end

        roi.roi(r).roiname = roi_list(r).name;
        roi.roi(r).roicode = roi_list(r).value;
        roi.roi(r).roicodes1 = roi_list(r).value;
        roi.roi(r).roicodes2 = [];
        roi.roi(r).map = roi_list(r).name;
        roi.roi(r).indeces = find(roi.data(:, r));
        roi.roi(r).weights = [];
        roi.roi(r).nvox = length(roi.roi(r).indeces);
    end

    % ---> Collapse volumes if possible

    if max(sum(roi.data > 0, 2)) == 1
        roi.data(:, 1) = sum(roi.data, 2);
        roi = roi.selectframes(1);
    end



function [roi] = process_roi_volume(roi_list, template, mask, options, rcodes)
    % process a list of rois and return a nimage object with the rois

    % extract transformation matrix from the template image
    roi = template.zeroframes(length(roi_list));
    t = [roi.hdrnifti.srow_x'; roi.hdrnifti.srow_y'; roi.hdrnifti.srow_z'; 0 0 0 1];

    % create a matrix of indeces for each voxel
    dim_i = roi.hdrnifti.dim(2);
    dim_j = roi.hdrnifti.dim(3);
    dim_k = roi.hdrnifti.dim(4);
    ijk = zeros(dim_i * dim_j * dim_k, 4);
    c = 0;
    for k = 0:(dim_k-1)
        for j = 0:(dim_j-1)
            for i = 0:(dim_i-1)
                c = c + 1;
                ijk(c, :) = [i j k 1];
            end
        end
    end

    % transform the indeces to the template space
    xyz = (t * ijk')';
    xyz = xyz(:, 1:3);

    % compile matrix of roi locations
    roi_locations = zeros(length(roi_list), 3);
    for r = 1:length(roi_list)
        roi_locations(r, :) = [roi_list(r).x roi_list(r).y roi_list(r).z];
    end

    % compute distances of each voxel to each roi
    distances = pdist2(xyz, roi_locations);

    % prepare mask
    if ~isempty(mask)
        mask.data = mask.image2D;
        mask.data = mask.data(:, 1);        
    end

    % find voxels within radius of each roi
    for r = 1:length(roi_list)
        roi.data(distances(:, r) <= roi_list(r).radius, r) = roi_list(r).value;
        if ~isempty(mask)
            roi.data(mask.data == 0, r) = 0;
        end
        roi.roi(r).roiname = roi_list(r).name;
        roi.roi(r).roicode = roi_list(r).value;
        roi.roi(r).roicodes1 = roi_list(r).value;
        roi.roi(r).roicodes2 = [];
        roi.roi(r).map = roi_list(r).name;
        roi.roi(r).indeces = find(roi.data(:, r));
        roi.roi(r).weights = [];
        roi.roi(r).nvox = length(roi.roi(r).indeces);
    end

    % ---> Collapse volumes if possible

    if max(sum(roi.data > 0, 2)) == 1
        roi.data(:, 1) = sum(roi.data, 2);
        roi = roi.selectframes(1);
    end


function [roi_list] = read_roi_spec(roi)

    % read a roi specification file and return a list of rois and the format
    % of the file

    % open roi file, read line by line, for each line split line by whitespace
    % and create a new roi structure with the information in the following
    % order: roi name, x, y, z, radius, value

    fid = fopen(roi, 'r');

    if fid == -1
        error('Cannot open the file: %s', filename);
    end

    % Initialize an empty structure array
    roi_list = struct('name', {}, 'x', {}, 'y', {}, 'z', {}, 'radius', {}, 'value', {});

    % Read the file line by line
    line_num = 0;

    while ~feof(fid)
        % Read a line from the file
        line = fgetl(fid);

        % - process first line
        if line_num == 0            
            if starts_with(line, '# ROI specification')
                line_num = 1;
            else
                error('The first line of the ROI file should specify the format of the ROI file');
            end
        end

        if isempty(strtrim(line)) || starts_with(line, '#')
            continue
        end

        tokens = strsplit(line);

        if length(tokens) ~= 6
            error('Each line in the ROI file should have 6 elements');
        end

        roi_list(line_num).name = tokens{1};
        roi_list(line_num).x = str2double(tokens{2});
        roi_list(line_num).y = str2double(tokens{3});
        roi_list(line_num).z = str2double(tokens{4});
        roi_list(line_num).radius = str2double(tokens{5});
        roi_list(line_num).value = str2double(tokens{6});

        line_num = line_num + 1;
    end

    fclose(fid);
