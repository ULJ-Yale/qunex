function mask = img_join_masks(obj, mask_a, mask_b, options)
%function mask = img_join_masks(obj, mask_a, mask_b, options)
%
%   Joins two masks into a new, combined mask
%
%   Parameters:
%       --mask_a (nimage, array):
%           A nimage object, a numeric array mask, an indices vector, or an ROI 
%           structure defining the first mask or a set of masks.
%       --mask_b (nimage, array):
%           A nimage object, a numeric array mask, an indices vector, or an ROI
%           structure defining the first mask or a set of masks.
%       --options (str, default 'volumes:1|join:union|standardize:no'):
%           A string with pipe separated <key>:<value> pairs that define 
%           additional options. The current options are:
%
%           - volumes: '1' (number, 'all')
%               How many volumes from both masks to join. The relevant number
%               has to match between the two masks.
%           - join: 'union' ('union'/'intersection')
%               Whether the resulting mask is a union (any voxels from any mask
%               results in a voxel in the final mask) or intersection (voxels 
%               from both masks have to be "on" to be in the final mask) of the
%               source masks.
%           - standardize: 'no' ('no'/'within'/'across')
%               In case of an ROI structure, if weights exist, are they to be
%               standardized to 1 within each ROI or across all ROI.
%           - threshold: '0' (number)
%               If set different from 0, it is used to threshold the images 
%               before combining masks. The exact behavior will depend on the 
%               prefix or suffix.
%               If provided without a prefix or suffix, all voxels with absolute 
%               value equal to or higher than threshold will be kept in the mask.
%               If the value is preceeded with '<', only voxels with values lower
%               than the threshold will be kept in the mask.
%               If the value is followed with '<', only voxels with values
%               higher than the threshold will be kept in the mask.
%               Note: due to use of '>' in parsing of options, it can not be 
%               used to define the type of threshold.
%
%   Output:
%       mask
%           The resulting mask of the same type as the inputs.

if nargin < 4, options = ''; end
if nargin < 3, error('ERROR: in img_join_masks, both masks need to be provided as input!'); end

defaults = 'volumes:1|join:union|standardize:no|threshold:0';
options = general_parse_options([], options, defaults);
can_standardize = false;

if ischar(options.volumes) 
    if strcmp(options.volumes, 'all')
        options.volumes = [];
    else
        error(sprintf('ERROR (img_join_masks): Invalid specification of volumes option [%s]. Please check your inputs!', options.volumes));
    end
end

% --- identify input type

class_a = class(mask_a);
class_b = class(mask_b);

if ~strcmp(class_a, class_b)
    error(sprintf('ERROR (img_join_mask): The two inputs are not of the same class! mask_a is %s, and mask_b is %s. Please, check your inputs!', class_a, class_b));
end

if strcmp(class_a, 'nimage')
    if isempty(mask_a.roi) && isempty(mask_b.roi)
        if isempty(options.volumes)
            if mask_a.frames ~= mask_b.frames
                error(sprintf('ERROR (img_join_mask): The two images have different number of volumes. mask_a has %d and mask_b %d volumes!', mask_a.frames, mask_b.frames));
            else
                options.volumes = mask_a.frames;
            end
        end
        if mask_a.frames < options.volumes
            error(sprintf('ERROR (img_join_mask): The two images have less volumes [%d] than specified to join [%d]!', mask_a.frames, options.volumes));
        end
        mask_a.data = threshold(mask_a.image2D, options);
        mask_b.data = threshold(mask_b.image2D, options);
        mask = mask_a.zeroframes(options.volumes);
        if strcmp(options.join, 'union')
            mask.data = mask_a.data(:,1:options.volumes) ~= 0 | mask_b.data(:,1:options.volumes) ~= 0;
        else
            mask.data = mask_a.data(:,1:options.volumes) ~= 0 & mask_b.data(:,1:options.volumes) ~= 0;
        end
    elseif ~isempty(mask_a.roi) && ~isempty(mask_b.roi)
        if isempty(options.volumes)
            if length(mask_a.roi) ~= length(mask_b.roi)
                error(sprintf('ERROR (img_join_mask): The ROI structures in the two images are of different lengths. mask_a has %d and mask_b %d ROIs defined!', length(mask_a.roi), length(mask_b.roi)));
            else
                options.volumes = length(mask_a.roi);
            end
        end
        if length(mask_a.roi) < options.volumes
            error(sprintf('ERROR (img_join_mask): The two images have less ROI specified [%d] than specified to join [%d]!', length(mask_a.roi), options.volumes));
        end
        mask = mask_a.zeroframes(options.volumes);
        mask.roi = mask_a.roi(1:options.volumes);
        for r = 1:options.volumes
            if strcmp(options.join, 'union')
                mask.roi(r).indeces = union(mask_a.roi(r).indeces, mask_b.roi(r).indeces);
            else
                mask.roi(r).indeces = intersect(mask_a.roi(r).indeces, mask_b.roi(r).indeces);
            end
            mask.data(mask.roi(r).indeces, r) = r;
            mask.roi(r).weights = [];
            mask.roi(r).nvox = length(mask.roi(r).indeces);
        end
        can_standardize = true;
    else
        error('ERROR (img_join_mask): one of the masks has and the other does not have a ROI structure. Please, check your input!');
    end
elseif strcmp(class_a, 'struct')
    if isempty(options.volumes)
        if length(mask_a) ~= length(mask_b)
            error(sprintf('ERROR (img_join_mask): The ROI structures in the two images are of different lengths. mask_a has %d and mask_b %d ROIs defined!', length(mask_a), length(mask_b)));
        else
            options.volumes = length(mask_a);
        end
    end
    if length(mask_a) < options.volumes
        error(sprintf('ERROR (img_join_mask): The two images have less ROI specified [%d] than specified to join [%d]!', length(mask_a), options.volumes));
    end
    mask = mask(1:options.volumes);
    for r = 1:options.volumes
        if strcmp(options.join, 'union')
            mask(r).indeces = union(mask_a(r).indeces, mask_b(r).indeces);
        else
            mask(r).indeces = intersect(mask_a(r).indeces, mask_b(r).indeces);
        end
        mask(r).weights = [];
        mask(r).nvox = length(mask(r).indeces);
    end
    can_standardize = true;
else
    % ---> do we have indeces
    if size(mask_a, 1) < obj.voxels && size(mask_b, 1) < obj.voxels && size(mask_a, 2) == 1 && size(mask_b, 2) == 1 && sum(mask_a - floor(mask_a)) == 0 && sum(mask_b - floor(mask_b)) == 0 && length(mask_a) == length(unique(mask_a)) && length(mask_b) == length(unique(mask_b))
        if max(mask_a) > obj.voxels || max(mask_b) > obj.voxsels || min(mask_a) < 1 || min(mask_b) < 1
            error('ERROR (img_join_masks): The provided indeces are invalid (higher than the number of image voxels or smaller than 1)!');
        end
        if strcmp(options.join, 'union')
            mask = union(mask_a, mask_b);
        else
            mask = intersect(mask_a, mask_b);
        end

    % ---> we have masks
    else
        if size(mask_a, 1) ~= obj.voxels || size(mask_b, 1) ~= obj.voxels
            error('ERROR (img_join_masks): The size of the masks does not match the size of the image!');
        end
        if isempty(options.volumes)
            if size(mask_a, 2) ~= size(mask_b, 2)
                error(sprintf('ERROR (img_join_masks): All masks specified but sizes of mask_a [%d] and mask_b [%d] do not match!', size(mask_a, 2), size(mask_b, 2)));
            end
            options.volumes = size(mask_a, 2);
        end
        if options.volumes > size(mask_a, 2) || options.volumes > size(mask_b,2)
            error(sprintf('ERROR (img_join_masks): The specified number of mask volumes to join [%d] is heigher of the number of volumes in mask_a [%d] and/or mask_b [%d]!', options.volumes, size(mask_a, 2), size(mask_b, 2)));
        end
        mask_a = threshold(mask_a, options);
        mask_b = threshold(mask_b, options);
        if strcmp(options.join, 'union')
            mask = mask_a(:, 1:options.volumes) ~= 0 | mask_b(:, 1:options.volumes) ~= 0;
        else
            mask = mask_a(:, 1:options.volumes) ~= 0 & mask_b(:, 1:options.volumes) ~= 0;
        end
    end
end


% --- support function for masking

function mask = threshold(mask, options)

    if ischar(options.threshold)
        idx = strfind(options.threshold, "<");
        if isempty(idx)
            error(sprintf('ERROR (img_join_masks): The threshold specification is invalid: %s!', options.threshold));
        elseif idx == 1
            t = str2num(options.threshold(2:end));
            mask = mask .* (mask < t);
        else
            t = str2num(options.threshold(1:idx-1));
            mask = mask .* (mask > t);
        end
    else
        mask = mask .* (abs(mask) > options.threshold);
    end


